"""Bounded CPU replays of captured BASE gradients; never a parity waiver.

This helper performs no forward/backward pass and does not request CUDA work.
Ordinary PyTorch AdamW may internally probe accelerator availability. The two
optimizer steps act only on fresh CPU clones, never on the measured models.
"""
from collections.abc import Mapping
import json
import math

import torch


SCHEMA_VERSION = 'factorized-base-update-diagnostics-v1'
MAXIMUM_COORDINATE_SAMPLES = 8
MAXIMUM_MOMENT_ANOMALY_NAMES = 4
MAXIMUM_PARAMETER_TENSORS = 64
MAXIMUM_PARAMETER_SCALARS = 262144
MAXIMUM_REPORT_BYTES = 16384
_ROUNDING_UNITS = 8
_SETTINGS = {
    'lr': .001, 'betas': (.9, .999), 'eps': 1e-8, 'weight_decay': 0.0,
    'foreach': False, 'fused': False, 'amsgrad': False, 'maximize': False,
    'capturable': False, 'differentiable': False,
}
_PREFIXES = ('initial/base/', 'base/objective_parameter_gradients/',
             'base/updated_parameters/', 'base/optimizer/')


class BaseUpdateDiagnosticError(RuntimeError):
    """Captured inputs do not support an unambiguous first-step replay."""


def _need(condition, detail):
    if not condition:
        raise BaseUpdateDiagnosticError(detail)


def _tensor(value, *, name, shape=None):
    _need(type(value) is torch.Tensor, name + ': expected a tensor')
    _need(value.device.type == 'cpu', name + ': captured payload must be CPU-only')
    _need(value.layout == torch.strided and value.dtype == torch.float32,
          name + ': expected dense FP32')
    _need(value.ndim <= 4 and 0 < value.numel() <= MAXIMUM_PARAMETER_SCALARS,
          name + ': tensor size/rank outside diagnostic bound')
    _need(shape is None or value.shape == shape, name + ': shape mismatch')
    _need(bool(torch.isfinite(value).all()), name + ': nonfinite tensor')
    return value.detach()


def _roundoff_mask(left, right):
    left, right = left.double(), right.double()
    scale = torch.maximum(left.abs(), right.abs()).clamp(min=torch.finfo(torch.float32).tiny)
    return (left - right).abs() <= _ROUNDING_UNITS * torch.finfo(torch.float32).eps * scale


def _read(payload, names, label):
    expected = set()
    result = {}
    for name in names:
        keys = {'initial': 'initial/base/' + name,
                'gradient': 'base/objective_parameter_gradients/' + name,
                'updated': 'base/updated_parameters/' + name}
        keys.update({field: 'base/optimizer/' + name + '/' + field
                     for field in ('step', 'exp_avg', 'exp_avg_sq')})
        expected.update(keys.values())
        row = {}
        for field, key in keys.items():
            _need(key in payload, label + ': missing BASE payload entry ' + key)
            entry = payload[key]
            _need(type(entry) in (tuple, list) and len(entry) == 2,
                  label + ': malformed payload entry ' + key)
            expected_kind = {'initial': 'exact', 'gradient': 'parameter_gradient',
                             'updated': 'updated_parameter', 'step': 'exact',
                             'exp_avg': 'optimizer_moment', 'exp_avg_sq': 'optimizer_moment'}[field]
            _need(entry[0] == expected_kind, label + ': payload category mismatch ' + key)
            row[field] = entry[1]
        initial = _tensor(row['initial'], name=label + '/' + name + '/initial')
        row['initial'] = initial
        row['updated'] = _tensor(row['updated'], name=label + '/' + name + '/updated', shape=initial.shape)
        if row['gradient'] is None:
            _need(all(row[field] is None for field in ('step', 'exp_avg', 'exp_avg_sq')),
                  label + '/' + name + ': absent gradient must have absent fresh state')
            _need(torch.equal(initial, row['updated']),
                  label + '/' + name + ': absent gradient changed a parameter')
        else:
            for field in ('gradient', 'exp_avg', 'exp_avg_sq'):
                row[field] = _tensor(row[field], name=label + '/' + name + '/' + field,
                                     shape=initial.shape)
            row['step'] = _tensor(row['step'], name=label + '/' + name + '/step')
            _need(row['step'].ndim == 0 and float(row['step']) == 1.0,
                  label + '/' + name + ': fresh first-step state must have scalar step=1')
        result[name] = row
    observed = {key for key in payload if isinstance(key, str) and key.startswith(_PREFIXES)}
    _need(observed == expected, label + ': BASE gradient/parameter/state roster mismatch')
    return result


def _replay(rows, names, optimizer_factory):
    # ParameterList creates no randomized weights. Every storage and gradient is
    # cloned so optimizer mutations cannot reach either observed payload.
    model = torch.nn.Module()
    model.weights = torch.nn.ParameterList([
        torch.nn.Parameter(rows[name]['initial'].detach().clone()) for name in names])
    optimizer = optimizer_factory(model)
    _need(type(optimizer) is torch.optim.AdamW, 'replay factory must return ordinary torch.optim.AdamW')
    _need(len(optimizer.param_groups) == 1 and not optimizer.state,
          'replay optimizer must have one fresh parameter group and no state')
    group = optimizer.param_groups[0]
    _need(tuple(map(id, group['params'])) == tuple(map(id, model.weights)),
          'replay optimizer parameter identity/order mismatch')
    for field, expected in _SETTINGS.items():
        _need(type(group.get(field)) is type(expected) and group[field] == expected,
              'replay optimizer setting changed: ' + field)
    for name, parameter in zip(names, model.weights):
        gradient = rows[name]['gradient']
        parameter.grad = None if gradient is None else gradient.detach().clone()
    optimizer.step()
    result = {}
    for name, parameter in zip(names, model.weights):
        state = optimizer.state.get(parameter, {})
        _need(set(state) in (set(), {'step', 'exp_avg', 'exp_avg_sq'}),
              'replay produced unexpected optimizer state')
        result[name] = {'updated': parameter.detach().clone()}
        for field in ('step', 'exp_avg', 'exp_avg_sq'):
            result[name][field] = None if field not in state else state[field].detach().clone()
    return result


def _summary(actual, replay, names, fields, *, atol, rtol):
    summary = {'tensor_count': 0, 'scalar_count': 0, 'absent_tensor_count': 0,
               'exact': True, 'fp32_roundoff_close': True,
               'maximum_absolute_residual': 0.0,
               'maximum_fp32_scaled_residual': 0.0}
    if fields == ('updated',):
        summary['within_existing_update_tolerance'] = True
    for name in names:
        for field in fields:
            left, right = actual[name][field], replay[name][field]
            if left is None or right is None:
                _need(left is right, 'replay gradient/state presence mismatch for ' + name + '/' + field)
                summary['absent_tensor_count'] += 1
                continue
            _need(left.shape == right.shape and left.dtype == right.dtype and right.device.type == 'cpu',
                  'replay tensor shape/dtype/device changed')
            _need(bool(torch.isfinite(right).all()), 'replay produced nonfinite values')
            difference = (left.double() - right.double()).abs()
            scale = torch.maximum(left.double().abs(), right.double().abs()).clamp(min=torch.finfo(torch.float32).tiny)
            summary['tensor_count'] += 1
            summary['scalar_count'] += left.numel()
            summary['exact'] &= torch.equal(left, right)
            summary['fp32_roundoff_close'] &= bool(_roundoff_mask(left, right).all())
            summary['maximum_absolute_residual'] = max(summary['maximum_absolute_residual'], float(difference.max()))
            summary['maximum_fp32_scaled_residual'] = max(summary['maximum_fp32_scaled_residual'],
                float((difference / (torch.finfo(torch.float32).eps * scale)).max()))
            if fields == ('updated',):
                summary['within_existing_update_tolerance'] &= bool(
                    (difference <= atol + rtol * left.double().abs()).all())
    return summary


def _moment_consistency(rows, names):
    """Retain finite moment anomalies as evidence, not a diagnostic stop."""
    result = {'consistent_with_fp32_roundoff_envelope': True, 'tensor_count': 0,
              'maximum_absolute_residual_from_ideal_fp64': 0.0,
              'inconsistent_tensor_count': 0, 'inconsistent_tensor_names': []}
    for name in names:
        row = rows[name]
        if row['gradient'] is None:
            continue
        g = row['gradient'].double()
        for field, ideal in (('exp_avg', (1.0 - _SETTINGS['betas'][0]) * g),
                             ('exp_avg_sq', (1.0 - _SETTINGS['betas'][1]) * g.square())):
            close = bool(_roundoff_mask(ideal, row[field]).all())
            result['tensor_count'] += 1
            result['consistent_with_fp32_roundoff_envelope'] &= close
            result['maximum_absolute_residual_from_ideal_fp64'] = max(
                result['maximum_absolute_residual_from_ideal_fp64'],
                float((ideal - row[field].double()).abs().max()))
            if not close:
                result['inconsistent_tensor_count'] += 1
                if len(result['inconsistent_tensor_names']) < MAXIMUM_MOMENT_ANOMALY_NAMES:
                    result['inconsistent_tensor_names'].append(name + '/' + field)
    result['inconsistent_tensor_names_truncated'] = (
        result['inconsistent_tensor_count'] > len(result['inconsistent_tensor_names']))
    return result


def _coordinate(rows, replay, name, flat_index):
    row = rows[name]
    scalar = lambda field: None if row[field] is None else float(row[field].reshape(-1)[
        0 if field == 'step' else flat_index])
    initial, gradient, updated = scalar('initial'), scalar('gradient'), scalar('updated')
    ideal_delta = 0.0 if gradient is None else -_SETTINGS['lr'] * gradient / (abs(gradient) + _SETTINGS['eps'])
    result = {'initial': initial, 'objective_gradient': gradient, 'step': scalar('step'),
              'exp_avg': scalar('exp_avg'), 'exp_avg_sq': scalar('exp_avg_sq'),
              'updated': updated, 'delta': updated - initial,
              'ideal_fp64_first_step_delta': ideal_delta,
              'ideal_fp64_first_step_updated': initial + ideal_delta}
    for field in ('updated', 'step', 'exp_avg', 'exp_avg_sq'):
        value = replay[name][field]
        result['cpu_replay_' + field] = None if value is None else float(
            value.reshape(-1)[0 if field == 'step' else flat_index])
    result['cpu_replay_updated_residual'] = result['cpu_replay_updated'] - updated
    return result


def build_base_update_diagnostics(reference_payload, target_payload, *, optimizer_factory, atol, rtol):
    """Explain captured first-step disagreements without changing their verdict.

    All BASE tensors are validated and compared. Reporting samples one worst
    violating scalar per failing tensor in lexical name order, at most eight.
    FP32-roundoff comparisons are descriptive, NOT acceptance tolerances.
    """
    _need(isinstance(reference_payload, Mapping) and isinstance(target_payload, Mapping),
          'diagnostics require captured payload mappings')
    _need(all(type(value) in (float, int) and math.isfinite(value) and value >= 0
              for value in (atol, rtol)), 'invalid existing update tolerances')
    names = sorted(key[len('initial/base/'):] for key in reference_payload
                   if isinstance(key, str) and key.startswith('initial/base/'))
    _need(0 < len(names) <= MAXIMUM_PARAMETER_TENSORS and all(
        name and '/' not in name and len(name.encode('utf-8')) <= 128 for name in names),
        'BASE name/tensor roster outside diagnostic bound')
    reference = _read(reference_payload, names, 'cpu_reference')
    target = _read(target_payload, names, 'target')
    scalar_count = sum(reference[name]['initial'].numel() for name in names)
    _need(scalar_count <= MAXIMUM_PARAMETER_SCALARS, 'BASE scalar count outside diagnostic bound')
    for name in names:
        _need(torch.equal(reference[name]['initial'], target[name]['initial'])
              and reference[name]['initial'].shape == target[name]['initial'].shape,
              name + ': initial CPU/target parameters are not exact')
        _need((reference[name]['gradient'] is None) == (target[name]['gradient'] is None),
              name + ': CPU/target objective gradient presence differs')
    cpu_replay = _replay(reference, names, optimizer_factory)
    target_gradient_replay = _replay(target, names, optimizer_factory)
    moment_consistency = {'cpu_reference': _moment_consistency(reference, names),
                          'target': _moment_consistency(target, names)}
    moments_consistent = all(row['consistent_with_fp32_roundoff_envelope']
                             for row in moment_consistency.values())
    comparisons = {}
    for label, actual, replay in (('cpu_gradient_control', reference, cpu_replay),
                                   ('captured_target_gradient_cpu_replay', target, target_gradient_replay)):
        comparisons[label] = {label_: _summary(actual, replay, names, fields, atol=atol, rtol=rtol)
            for label_, fields in (('updated_parameters', ('updated',)),
                                   ('optimizer_moments', ('exp_avg', 'exp_avg_sq')),
                                   ('optimizer_steps', ('step',)))}
    failures, samples, failing_scalar_count = [], [], 0
    for name in names:
        left, right = reference[name]['updated'].double(), target[name]['updated'].double()
        difference = (left - right).abs()
        threshold = atol + rtol * left.abs()
        violations = difference > threshold
        count = int(violations.sum())
        if not count:
            continue
        failures.append(name)
        failing_scalar_count += count
        if len(samples) == MAXIMUM_COORDINATE_SAMPLES:
            continue
        flat = int((difference - threshold).reshape(-1).argmax())
        remainder, index = flat, []
        for size in reversed(left.shape):
            index.insert(0, remainder % size)
            remainder //= size
        cpu_row = _coordinate(reference, cpu_replay, name, flat)
        target_row = _coordinate(target, target_gradient_replay, name, flat)
        samples.append({'tensor_name': name, 'flat_index': flat, 'index': index,
            'cpu_reference': cpu_row, 'target': target_row,
            'actual_updated_gap_target_minus_cpu': target_row['updated'] - cpu_row['updated'],
            'ideal_fp64_updated_gap_target_minus_cpu': (
                target_row['ideal_fp64_first_step_updated'] - cpu_row['ideal_fp64_first_step_updated']),
            'cpu_replay_updated_gap_target_gradient_minus_cpu_gradient': (
                target_row['cpu_replay_updated'] - cpu_row['cpu_replay_updated']),
            'existing_elementwise_update_threshold': float(threshold.reshape(-1)[flat])})
    control_exact = all(value['exact'] for value in comparisons['cpu_gradient_control'].values())
    target_roundoff_close = all(value['fp32_roundoff_close'] for value in
                                comparisons['captured_target_gradient_cpu_replay'].values())
    if not moments_consistent:
        interpretation = 'CAPTURED_FIRST_STEP_MOMENT_RESIDUAL_REQUIRES_REVIEW'
    elif not control_exact:
        interpretation = 'CPU_REPLAY_CONTROL_MISMATCH_REVIEW_REQUIRED'
    elif not failures:
        interpretation = 'NO_BASE_UPDATED_PARAMETER_FAILURE_AT_EXISTING_TOLERANCES'
    elif target_roundoff_close:
        interpretation = 'CAPTURED_GRADIENT_SENSITIVITY_SUPPORTED_NOT_PROVEN'
    else:
        interpretation = 'SAME_GRADIENT_OPTIMIZER_RESIDUAL_REQUIRES_REVIEW'
    result = {'schema_version': SCHEMA_VERSION, 'diagnostic_only': True,
        'changes_parity_acceptance': False, 'interpretation': interpretation,
        'cpu_optimizer_replay_steps': 2, 'additional_cuda_optimizer_steps': 0,
        'forward_or_backward_passes': 0, 'input_mutations_requested': False,
        'optimizer_settings': dict(_SETTINGS),
        'gradient_source': 'base/objective_parameter_gradients/NOT_FORWARD_GRADIENTS',
        'initial_parameters_exact': True, 'observed_steps_and_state_presence_validated': True,
        'fresh_first_step_state_consistent': moments_consistent,
        'first_step_moment_consistency': moment_consistency,
        'ideal_fp64_note': 'REAL_ARITHMETIC_FIRST_STEP_PREDICTION_NOT_AN_EXACT_FP32_BACKEND_PREDICTION',
        'parameter_tensor_count': len(names), 'parameter_scalar_count': scalar_count,
        'all_parameter_comparison': comparisons,
        'roundoff_description': {'fp32_relative_units': _ROUNDING_UNITS,
            'scale': 'max(abs(actual),abs(replay),FP32_minimum_normal)',
            'descriptive_only_not_a_parity_acceptance_rule': True,
            'exact_equality_reported_separately': True},
        'observed_update_disagreement': {'failing_tensor_count': len(failures),
            'failing_scalar_count': failing_scalar_count,
            'existing_absolute_tolerance': float(atol), 'existing_relative_tolerance': float(rtol)},
        'sampling': {'policy': 'ONE_WORST_THRESHOLD_EXCESS_COORDINATE_PER_FAILING_TENSOR_LEXICAL_ORDER',
            'tie_break': 'LOWEST_FLAT_INDEX', 'maximum_coordinate_samples': MAXIMUM_COORDINATE_SAMPLES,
            'sample_count': len(samples), 'omitted_failing_tensor_count': len(failures) - len(samples),
            'omitted_failing_scalar_count': failing_scalar_count - len(samples),
            'all_parameter_tensors_compared_before_sampling': True},
        'coordinate_samples': samples,
        'limits': {'maximum_parameter_tensors': MAXIMUM_PARAMETER_TENSORS,
                   'maximum_parameter_scalars': MAXIMUM_PARAMETER_SCALARS,
                   'maximum_moment_anomaly_names_per_side': MAXIMUM_MOMENT_ANOMALY_NAMES,
                   'maximum_report_bytes': MAXIMUM_REPORT_BYTES}}
    _need(len(json.dumps(result, allow_nan=False, separators=(',', ':')).encode('utf-8')) <= MAXIMUM_REPORT_BYTES,
          'diagnostic JSON exceeds report byte bound')
    return result
