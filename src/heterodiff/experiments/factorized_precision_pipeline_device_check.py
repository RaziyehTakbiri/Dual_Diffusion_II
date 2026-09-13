"""Fixed synthetic integrated precision check; no remote execution or data I/O.

Generated populations have device/weight-dependent law identities. Their CPU
and CUDA paths are therefore never presented as common-noise parity controls.
Separate, explicit common-input computations test numerical parity; complete
own-route replay binds generated paths, diagnostics and all optimizer tensors.
"""
from copy import deepcopy
import hashlib
import json
import math
import re
import time

import numpy as np
import torch

from heterodiff.experiments.factorized_base_precision import PRECISION_POLICY
from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest
from heterodiff.experiments.factorized_conditional_training import (
    FactorizedConditionalModel, FactorizedObservation, FactorizedTrainingBatch,
)
from heterodiff.experiments.factorized_device_qualification import (
    DeviceQualificationRequest, MAXIMUM_MEMORY_BYTES, POLICY_ID, TOLERANCES,
    _Budget, _compare, _error_diagnostics, _host_payload, _need, _numerical_policy,
    _optimizer, _rss,
)
from heterodiff.experiments.factorized_device_training import (
    DeviceFactorizedBasePopulation, DeviceFactorizedConditionalModel,
    DeviceFactorizedPhysicalPotential, device_sample_conditional,
    device_train_base_step, device_train_conditional_step,
)
from heterodiff.experiments.factorized_precision_pipeline_qualification import (
    _digest, _fixture as _cpu_fixture, _path_summary, _state_record,
)
from heterodiff.models.factorized_configuration_energy_torch import BoundedFactorizedConfigurationEnergy
from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy
from heterodiff.processes.factorized_hybrid_sampler import canonical, heun_step


DOMAINS = ('R3-PHYS', 'R4-RETAIL')
METHODS = ('association-aware-guide-plus-residual', 'unified-direct-conditioner')
CASE_ROSTER = tuple((domain, method) for domain in DOMAINS for method in METHODS)
ROLES = ('candidate_cpu', 'candidate_target', 'candidate_target_replay')
GATING_COMPARISONS = ('common_base_cpu_vs_target', 'common_conditional_cpu_vs_target',
                      'shared_weight_physical_cpu_vs_target', 'candidate_target_exact_replay')
COMPARISONS = GATING_COMPARISONS + ('legacy_shared_weight_physical_drift',)
COMPARISON_CATEGORIES = {
    'common_base_cpu_vs_target': {'exact', 'loss', 'parameter_gradient', 'updated_parameter', 'optimizer_moment'},
    'common_conditional_cpu_vs_target': {'exact', 'forward', 'loss', 'parameter_gradient', 'updated_parameter', 'optimizer_moment'},
    'shared_weight_physical_cpu_vs_target': {'physical'},
    'candidate_target_exact_replay': {'exact', 'forward', 'loss', 'parameter_gradient', 'updated_parameter', 'optimizer_moment', 'physical'},
    'legacy_shared_weight_physical_drift': {'physical'},
}
GRID = (0., .25, .5, .75, 1.)
FIXTURE_ID = 'factorized-integrated-precision-device-fixed-v1'
MAXIMUM_REPORT_BYTES = 55 * 1024
STEP_KINDS = ('base_updates', 'conditional_updates', 'conditional_control_updates')


def _fixture(domain, method, device):
    """Reuse frozen local fixture and CPU initialization seeds without moving it."""
    source, reference, cpu_base, cpu_model, context = _cpu_fixture(domain, method)
    if device == 'cpu':
        return source, reference, cpu_base, cpu_model, context
    arch = cpu_base.architecture
    base = DeviceFactorizedEnergy.from_cpu(
        BoundedFactorizedConfigurationEnergy(arch, initialization_seed=41), device)
    prototype = FactorizedConditionalModel(
        BoundedFactorizedConfigurationEnergy(arch, initialization_seed=42),
        guide=cpu_model.guide, method_id=method, clean_hold=.25,
        remaining_clocks=reference.schedule.remaining_clocks, observation_seed=43, nuisance_seed=44)
    model = DeviceFactorizedConditionalModel.from_cpu(prototype, device)
    _need(_parameter_digest(base) == _parameter_digest(cpu_base)
          and _parameter_digest(model) == _parameter_digest(cpu_model),
          'CPU prototypes and selected-device initial weights differ')
    return source, reference, base, model, context


def _model_contract(model, device, *, base=False):
    parameters = dict(model.named_parameters())
    _need(parameters and str(model.device) == device, 'model does not own requested device')
    if base:
        _need(sum(p.numel() for p in parameters.values()) == 96705, 'BASE parameter count changed')
    else:
        _need(all(any(name.startswith(prefix) for name in parameters)
                  for prefix in ('conditioner.', 'encoder.', 'nuisance.')),
              'conditional component parameter roster incomplete')
    for p in parameters.values():
        _need(p.dtype == torch.float32 and str(p.device) == device
              and bool(torch.isfinite(p).all()), 'trainable dtype/device/finite mismatch')
    return {name: tuple(p.shape) for name, p in parameters.items()}


def _parameters(model, prefix, category):
    return {prefix + '/' + name: (category, p.detach().clone()) for name, p in model.named_parameters()}


def _snapshot(model, optimizer, contract, device, prefix):
    """Complete FP32 leaf/gradient/moment roster, including legitimate None grads."""
    _need({name: tuple(p.shape) for name, p in model.named_parameters()} == contract,
          'optimizer parameter roster changed')
    expected_ids = {id(p) for p in model.parameters()}
    optimizer_ids = [id(p) for group in optimizer.param_groups for p in group['params']]
    _need(len(optimizer_ids) == len(set(optimizer_ids)) and set(optimizer_ids) == expected_ids
          and all(id(p) in expected_ids for p in optimizer.state),
          'AdamW parameter ownership roster mismatch')
    payload, active = {}, 0
    for name, p in model.named_parameters():
        _need(p.dtype == torch.float32 and str(p.device) == device
              and bool(torch.isfinite(p).all()), 'nonfinite or misplaced updated parameter')
        grad, state = p.grad, optimizer.state.get(p, {})
        if grad is None:
            _need(not state, 'unused parameter gained AdamW state')
        else:
            active += 1
            _need(grad.shape == p.shape and grad.dtype == torch.float32 and grad.device == p.device
                  and bool(torch.isfinite(grad).all()), 'nonfinite or misplaced parameter gradient')
            _need(set(state) == {'step', 'exp_avg', 'exp_avg_sq'}, 'incomplete AdamW state')
            _need(state['step'].numel() == 1 and float(state['step']) == 1.,
                  'AdamW must take exactly one step for each present gradient')
            for field in ('exp_avg', 'exp_avg_sq'):
                value = state[field]
                _need(value.shape == p.shape and value.dtype == torch.float32 and value.device == p.device
                      and bool(torch.isfinite(value).all()), 'nonfinite or misplaced AdamW moment')
        payload[prefix + '/gradients/' + name] = ('parameter_gradient', None if grad is None else grad.detach().clone())
        payload[prefix + '/updated/' + name] = ('updated_parameter', p.detach().clone())
        for field in ('step', 'exp_avg', 'exp_avg_sq'):
            value = state.get(field)
            payload[prefix + '/optimizer/' + name + '/' + field] = (
                'exact' if field == 'step' else 'optimizer_moment',
                None if value is None else value.detach().clone())
    _need(active > 0, 'optimizer update had no present gradients')
    expected = {prefix + '/gradients/' + name for name in contract}
    expected |= {prefix + '/updated/' + name for name in contract}
    expected |= {prefix + '/optimizer/' + name + '/' + field
                 for name in contract for field in ('step', 'exp_avg', 'exp_avg_sq')}
    _need(payload.keys() == expected, 'optimizer payload roster incomplete')
    return payload


def _payload_digest(payload):
    rows = []
    for name, (kind, value) in sorted(payload.items()):
        if value is None:
            rows.append([name, kind, None])
        else:
            _need(type(value) is torch.Tensor and bool(torch.isfinite(value).all()),
                  'nonfinite or non-tensor replay payload')
            host = value.detach().cpu().contiguous()
            rows.append([name, kind, str(host.dtype), list(host.shape),
                         hashlib.sha256(host.numpy().tobytes()).hexdigest()])
    return _digest(rows)


def _step(progress, kind, device, operation):
    progress[kind + '_begun'] += 1
    progress['optimizer_steps_begun'] += 1
    progress['gpu_optimizer_steps_begun' if device.startswith('cuda:') else 'cpu_optimizer_steps_begun'] += 1
    result = operation()
    progress[kind + '_completed'] += 1
    progress['optimizer_steps_completed'] += 1
    return result


def _base_update(base, reference, source, context, device, progress):
    """Record actual CPU corruption/proposal inputs without replacing the draws."""
    contract = _model_contract(base, device, base=True)
    payload = _parameters(base, 'base/initial', 'exact')
    optimizer = _optimizer(base)
    forward_records, proposal_records = [], []
    forward, proposal = reference.sample_forward, reference.proposal
    def observed_forward(initial, s, rng):
        result = forward(initial, s, rng)
        forward_records.append({'initial': _state_record(initial), 'time': s.hex(),
                                'corrupted': _state_record(result)})
        return result
    def observed_proposal(state, rng):
        result = proposal(state, rng)
        proposal_records.append(None if result is None else {
            'state': _state_record(state), 'destination': _state_record(result[0]),
            'rate': float(result[1]).hex(), 'kind': result[2]})
        return result
    reference.sample_forward, reference.proposal = observed_forward, observed_proposal
    try:
        update = _step(progress, 'base_updates', device, lambda: device_train_base_step(
            base, reference, (source,), context=torch.tensor(context.base_context, dtype=torch.float32, device=device),
            rng=np.random.default_rng(7), optimizer=optimizer, sample_count=2,
            jump_weight=1., precision_policy=PRECISION_POLICY))
    finally:
        # Restore normal class method lookup before copying reference into the law.
        del reference.sample_forward
        del reference.proposal
    _need(len(forward_records) == len(proposal_records) == 2, 'BASE corruption input count changed')
    _need(update['base_precision_policy'] == PRECISION_POLICY and update['device'] == device
          and update['changed_parameter_elements'] > 0, 'actual candidate BASE update incomplete')
    for field in ('loss', 'continuous_loss', 'jump_loss'):
        payload['base/' + field] = ('loss', torch.tensor(update[field], dtype=torch.float64, device='cpu'))
    payload.update(_snapshot(base, optimizer, contract, device, 'base'))
    inputs = {'forward': forward_records, 'proposal': proposal_records,
              'continuous_rate': reference.schedule.continuous_rate,
              'jump_rate': reference.schedule.jump_rate,
              'context': context.base_context, 'sample_count': 2, 'jump_weight': 1.}
    return update, _digest(inputs), _host_payload(payload)


def _observation_record(observation):
    return {'observed': None if observation.observed is None else _state_record(observation.observed),
            'context_identity': observation.canonical_context_bytes.hex()}


def _compact_path(summary):
    # The two full-content hashes retain the complete numerical trajectory and
    # diagnostics. Do not repeat grids/cardinalities already bound by those hashes.
    return {key: summary[key] for key in ('state_grid_sha256', 'full_diagnostics_sha256',
            'stream_binding_sha256', 'accepted_births', 'accepted_deaths', 'jump_candidates')}


def _compact_update(update):
    return {'record_sha256': _digest(update), 'loss': update['loss'],
            'changed_parameter_elements': update['changed_parameter_elements']}


def _common_batches(source, context):
    state = canonical(source)
    atomic = next(event for event in source if not event.key.dimension)
    states, times = (state, (atomic,), ()), (.375, .75, 1.)
    def observation(value):
        return FactorizedObservation(value, context.domain_id, context.task_id, context.context_bytes)
    observations = (observation((source[-1],)), observation(()), observation(None))
    products = (observation(None), observation((source[-1],)), observation(()))
    law = 'EXPLICIT_SHARED_INPUT_DIAGNOSTIC_NOT_GENERATED_POPULATION:' + context.domain_id
    joint = FactorizedTrainingBatch(states, times, observations, law)
    product = FactorizedTrainingBatch(states, times, products, law)
    record = {'states': [_state_record(x) for x in states], 'times': times,
              'joint_observations': [_observation_record(x) for x in observations],
              'product_observations': [_observation_record(x) for x in products],
              'law': law, 'unit_weights': [[1, 1]] * 3}
    _need(len(state) == 3 and state.count(source[-1]) == 2 and sum(e.key.dimension for e in state) == 2,
          'atomic/continuous/duplicate shared-input fixture changed')
    return joint, product, _digest(record)


def _conditional_control(model, source, context, device, progress):
    contract = _model_contract(model, device)
    joint, product, input_digest = _common_batches(source, context)
    payload = _parameters(model, 'conditional/initial', 'exact')
    for name, tensor in (
        ('joint_logits', model.logits(joint)), ('product_logits', model.logits(product)),
        ('observation_encoder', model.encoder(joint.observations)),
        ('nuisance', model.nuisance(joint.observations)),
    ):
        payload['conditional/' + name] = ('forward', tensor.detach().clone())
    loss = model.paired_loss(joint, product)
    _need(loss.dtype == torch.float64 and loss.device.type == 'cpu' and bool(torch.isfinite(loss)),
          'conditional objective reduction changed')
    payload['conditional/loss'] = ('loss', loss.detach().clone())
    optimizer = _optimizer(model)
    loss.backward()
    _step(progress, 'conditional_control_updates', device, optimizer.step)
    payload.update(_snapshot(model, optimizer, contract, device, 'conditional'))
    _need(any(not torch.equal(payload['conditional/initial/' + name][1], p.detach())
              for name, p in model.named_parameters()), 'common-input conditional update changed no weights')
    _need(payload['conditional/observation_encoder'][1].dtype == torch.float32
          and payload['conditional/nuisance'][1].dtype == torch.float32,
          'FP32 conditional components changed precision')
    expected = {'conditional/' + name for name in
                ('joint_logits', 'product_logits', 'observation_encoder', 'nuisance', 'loss')}
    expected |= {'conditional/initial/' + name for name in contract}
    expected |= {'conditional/' + prefix + '/' + name for name in contract for prefix in ('gradients', 'updated')}
    expected |= {'conditional/optimizer/' + name + '/' + field for name in contract
                 for field in ('step', 'exp_avg', 'exp_avg_sq')}
    _need(payload.keys() == expected, 'common-input conditional payload roster incomplete')
    return _host_payload(payload), input_digest


def _generated_conditional(base, model, reference, source, context, device, budget, progress):
    contract = _model_contract(model, device)
    before = _parameter_digest(base)
    population = DeviceFactorizedBasePopulation(base, reference, GRID, context, precision_policy=PRECISION_POLICY)
    legacy = DeviceFactorizedBasePopulation(base, reference, GRID, context)
    _need(population.law_id != legacy.law_id
          and population.precision_policy == population.physical.precision_policy == PRECISION_POLICY,
          'candidate population precision law binding missing')
    training_paths, pairs = [], []
    original = population.sample_pair
    def observed_pair(**kwargs):
        joint, product, paths = original(**kwargs)
        training_paths.extend(_path_summary(path, context.domain_id) for path in paths)
        pairs.append({'states': [_state_record(x) for x in joint.states], 'times': joint.reverse_times,
                      'joint_observations': [_observation_record(x) for x in joint.observations],
                      'product_observations': [_observation_record(x) for x in product.observations],
                      'joint_law': joint.law_id, 'product_law': product.law_id})
        return joint, product, paths
    population.sample_pair = observed_pair
    optimizer = _optimizer(model)
    update = _step(progress, 'conditional_updates', device, lambda: device_train_conditional_step(
        model, population, optimizer=optimizer, reverse_time=None, run_seed=501,
        record_id=b'conditional-step-0', sample_count=1))
    _need(update['base_paths_generated'] == 2 and len(training_paths) == 2 and len(pairs) == 1
          and update['changed_parameter_elements'] > 0 and update['device'] == device
          and update['base_precision_policy'] == PRECISION_POLICY
          and update['time_policy'] == 'UNIFORM_FULL_REVERSE_INTERVAL',
          'actual generated-population conditional update incomplete')
    _need(all(p['reference_initializer'] and p['base_precision_policy'] == PRECISION_POLICY
              for p in training_paths), 'conditional source paths lost candidate reference binding')
    _need(training_paths[0]['stream_binding_sha256'] != training_paths[1]['stream_binding_sha256'],
          'joint/product source streams are not separated')
    payload = _snapshot(model, optimizer, contract, device, 'generated_conditional')
    payload['generated_conditional/loss'] = ('loss', torch.tensor(update['loss'], dtype=torch.float64, device='cpu'))
    _need(_parameter_digest(base) == _parameter_digest(population.physical.base) == before,
          'conditional learner mutated frozen BASE weights')
    model_before = _parameter_digest(model)
    paths = {}
    for name, observed in (('retained', (source[-1],)), ('overflow', None)):
        budget.check()
        path = device_sample_conditional(base, model, reference, GRID, context, observed,
            run_seed=502, record_id=('draw-' + name).encode(), precision_policy=PRECISION_POLICY)
        paths[name] = _path_summary(path, context.domain_id)
        _need(not paths[name]['reference_initializer'] and paths[name]['base_precision_policy'] == PRECISION_POLICY
              and path.diagnostics['conditioner_precision_policy'] == 'LEGACY_FP32',
              'full conditional path lost precision or initializer binding')
    _need(_parameter_digest(base) == before and _parameter_digest(model) == model_before,
          'conditional sampler mutated learned weights')
    return {'update': _compact_update(update), 'candidate_population_law_id': population.law_id,
            'legacy_population_law_id': legacy.law_id,
            'actual_conditional_inputs_sha256': _digest(pairs),
            'conditional_source_paths': [_compact_path(path) for path in training_paths],
            'conditional_paths': {name: _compact_path(path) for name, path in paths.items()},
            'frozen_BASE_preserved': True, 'sampler_weights_unchanged': True,
            'cross_device_generated_draws_are_common_inputs': False}, _host_payload(payload)


def _physical_control(base, model, source, context, *, policy):
    """CPU64 roots pass through unchanged FP32 encoding/FP64 candidate graph."""
    state = canonical(source)
    observation = FactorizedObservation((source[-1],), context.domain_id, context.task_id, context.context_bytes)
    result = {}
    for label, kwargs in (
        ('base', {}), ('conditional', {'conditional_model': model, 'observation': observation}),
    ):
        potential = DeviceFactorizedPhysicalPotential(base, base_context=context.base_context,
            clean_hold=.25, precision_policy=policy, **kwargs)
        values = []
        for u in (0., .375, .75, .875, 1.):
            value, gradients = potential.value_grad(u, state)
            _need(value == potential.value(u, state), 'physical value/value_grad disagreement')
            values.append(value)
            result[label + '/value/' + u.hex()] = ('physical', torch.tensor(value, dtype=torch.float64, device='cpu'))
            result[label + '/gradient/' + u.hex()] = ('physical', torch.tensor(
                [x for row in gradients for x in row], dtype=torch.float64, device='cpu'))
        _need(values[-3] == values[-2] == values[-1], 'physical clean hold changed')
        increments = tuple((.01,) if event.key.dimension else () for event in state)
        path = heun_step(state, .375, .0625, potential, .5, increments)
        _need(tuple(e.key for e in path) == tuple(e.key for e in state), 'Heun altered exact metadata')
        _need(any(a.coordinate != b.coordinate for a, b in zip(state, path) if a.key.dimension),
              'fixed-noise Heun control did not exercise continuous motion')
        result[label + '/fixed_noise_heun_coordinates'] = ('physical', torch.tensor(
            [e.coordinate for e in path if e.key.dimension], dtype=torch.float64, device='cpu'))
        result[label + '/initial_residual_tilt'] = ('physical', torch.tensor(
            potential.initialization_residual_log_tilt(state), dtype=torch.float64, device='cpu'))
    expected = {label + '/' + kind + '/' + u.hex() for label in ('base', 'conditional')
                for kind in ('value', 'gradient') for u in (0., .375, .75, .875, 1.)}
    expected |= {label + '/' + kind for label in ('base', 'conditional')
                 for kind in ('fixed_noise_heun_coordinates', 'initial_residual_tilt')}
    _need(result.keys() == expected and all(kind == 'physical' and tensor.dtype == torch.float64
          and bool(torch.isfinite(tensor).all()) for kind, tensor in result.values()),
          'physical common-input payload incomplete or nonfinite')
    return result


def _weights(base, model):
    return {'base': {k: v.detach().cpu().clone() for k, v in base.state_dict().items()},
            'conditional': {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}}


def _shared_physical(base, model, source, context, weights):
    copied_base, copied_model = deepcopy(base), deepcopy(model)
    copied_base.load_state_dict(weights['base'], strict=True)
    copied_model.load_state_dict(weights['conditional'], strict=True)
    selected = {'base': copied_base, 'conditional': copied_model}
    for label, module in selected.items():
        _need(module.state_dict().keys() == weights[label].keys() and all(
            torch.equal(tensor.detach().cpu(), weights[label][name]) for name, tensor in module.state_dict().items()),
            'shared CPU-trained physical weights were not copied exactly')
    binding = _payload_digest({label + '/' + name: ('exact', value)
                               for label, rows in weights.items() for name, value in rows.items()})
    payload = _physical_control(copied_base, copied_model, source, context, policy=PRECISION_POLICY)
    return payload, binding, copied_base, copied_model


def _run_route(domain, method, device, budget, progress, *, shared_physical_weights=None):
    source, reference, base, model, context = _fixture(domain, method, device)
    _model_contract(base, device, base=True)
    _model_contract(model, device)
    control_model = deepcopy(model)  # Fresh identical initial weights; never the generated conditional update.
    initial = _host_payload({**_parameters(base, 'initial/base', 'exact'),
                             **_parameters(model, 'initial/conditional', 'exact')})
    budget.check()
    base_update, base_input_digest, base_payload = _base_update(base, reference, source, context, device, progress)
    budget.check()
    generated, generated_payload = _generated_conditional(
        base, model, reference, source, context, device, budget, progress)
    budget.check()
    common_payload, common_input_digest = _conditional_control(control_model, source, context, device, progress)
    budget.check()
    weights = _weights(base, model) if shared_physical_weights is None else shared_physical_weights
    physical, weight_digest, copied_base, copied_model = _shared_physical(base, model, source, context, weights)
    legacy = (_physical_control(copied_base, copied_model, source, context, policy='LEGACY_FP32')
              if shared_physical_weights is None else None)
    payloads = {'initial': initial, 'base': base_payload, 'generated_conditional': generated_payload,
                'common_conditional': common_payload, 'physical': _host_payload(physical)}
    record = {'device': device, 'precision_policy': PRECISION_POLICY,
              'base_update': _compact_update(base_update), 'generated_conditional': generated,
              'base_inputs_sha256': base_input_digest, 'common_conditional_inputs_sha256': common_input_digest,
              'shared_physical_weights_sha256': weight_digest,
              'all_payload_sha256': _digest({key: _payload_digest(value) for key, value in payloads.items()}),
              'generated_path_count': 4, 'optimizer_steps': 3,
              'full_path_diagnostics_bound': True, 'trainable_parameters_and_moments_FP32': True,
              'conditioner_precision_policy': 'LEGACY_FP32'}
    _digest(record)  # Reject nonfinite scalar reports before declaring a route complete.
    budget.check()
    return record, payloads, weights, legacy


def _compact_comparison(left, right, *, exact=False):
    comparison = _compare(left, right, exact=exact)
    return {'passed': comparison['passed'], 'failure_count': comparison['failure_count'],
            'first_failure_names': comparison['failure_names'][:4],
            'tensor_roster_sha256': comparison['all_tensor_names_sha256'],
            'categories': {key: {'passed': row['passed'], 'tensors': row['tensor_count'],
                'scalars': row['scalar_count'], 'max_abs': row['maximum_absolute_difference']}
                for key, row in comparison['categories'].items()}}


def _case(domain, method, device, budget, progress):
    records, payloads, timings, weights, legacy = {}, {}, {}, None, None
    for role in ROLES:
        target = 'cpu' if role == 'candidate_cpu' else device
        progress.update(stage='INTEGRATED_ROUTE', role=role)
        result, timings[role] = budget.timed(target, lambda: _run_route(
            domain, method, target, budget, progress, shared_physical_weights=weights))
        record, tensors, returned_weights, old = result
        if role == 'candidate_cpu':
            weights, legacy = returned_weights, old
        records[role], payloads[role] = record, tensors
    cpu, target, replay = (payloads[role] for role in ROLES)
    for role in ROLES:
        _need(_compare(cpu['initial'], payloads[role]['initial'], exact=True)['passed'],
              'initial weights differ across complete routes')
        for key, message in (
            ('base_inputs_sha256', 'actual BASE corruption inputs differ across routes'),
            ('common_conditional_inputs_sha256', 'explicit common conditional inputs differ across routes'),
            ('shared_physical_weights_sha256', 'shared physical weights differ across routes'),
        ):
            _need(records[role][key] == records['candidate_cpu'][key], message)
    # Generated conditional inputs and path realizations are intentionally NOT
    # compared across CPU/CUDA laws. Only exact own-target replay covers them.
    flattened = [{group + '/' + name: item for group, rows in payload.items() for name, item in rows.items()}
                 for payload in (target, replay)]
    exact = _compact_comparison(flattened[0], flattened[1], exact=True)
    record_equal = records['candidate_target'] == records['candidate_target_replay']
    exact['full_route_records_equal'] = record_equal
    exact['passed'] = bool(exact['passed'] and record_equal)
    if not record_equal:
        exact['failure_count'] += 1
        exact['first_failure_names'] = (exact['first_failure_names'] + ['full_route_record'])[:4]
    comparisons = {
        'common_base_cpu_vs_target': _compact_comparison(cpu['base'], target['base']),
        'common_conditional_cpu_vs_target': _compact_comparison(cpu['common_conditional'], target['common_conditional']),
        'shared_weight_physical_cpu_vs_target': _compact_comparison(cpu['physical'], target['physical']),
        'candidate_target_exact_replay': exact,
        'legacy_shared_weight_physical_drift': _compact_comparison(legacy, cpu['physical']),
    }
    comparisons['legacy_shared_weight_physical_drift']['gates_candidate_completion'] = False
    roles = {role: {**record, 'full_route_sha256': _digest(record)} for role, record in records.items()}
    budget.check()
    return {'domain_id': domain, 'method_id': method, 'completed_base_steps': 3,
            'completed_generated_conditional_steps': 3, 'completed_common_input_conditional_steps': 3,
            'generated_path_count': 12, 'initial_weights_exact_across_routes': True,
            'common_base_inputs_exact_across_routes': True, 'common_conditional_inputs_exact_across_routes': True,
            'shared_physical_weights_exact_across_routes': True, 'roles': roles,
            'comparisons': comparisons, 'timing_seconds_including_host_copy_and_readback': timings}


def _decision(cases, mode, device='cpu'):
    DeviceQualificationRequest(mode=mode, device=device, maximum_seconds=300)
    _need(tuple((case['domain_id'], case['method_id']) for case in cases) == CASE_ROSTER,
          'incomplete or changed fixed four-case roster')
    for case in cases:
        _need(case['completed_base_steps'] == case['completed_generated_conditional_steps']
              == case['completed_common_input_conditional_steps'] == 3
              and case['generated_path_count'] == 12, 'incomplete integrated route workload')
        _need(all(case[key] is True for key in ('initial_weights_exact_across_routes',
            'common_base_inputs_exact_across_routes', 'common_conditional_inputs_exact_across_routes',
            'shared_physical_weights_exact_across_routes')), 'common-input/weight binding incomplete')
        _need(set(case['comparisons']) == set(COMPARISONS), 'missing or unexpected comparison controls')
        for name, comparison in case['comparisons'].items():
            _need(type(comparison['passed']) is bool
                  and type(comparison['failure_count']) is int and comparison['failure_count'] >= 0
                  and (comparison['failure_count'] == 0) == comparison['passed'],
                  'comparison pass/failure-count contradiction')
            _need(set(comparison['categories']) == COMPARISON_CATEGORIES[name],
                  'comparison category roster incomplete')
            _need(type(comparison['tensor_roster_sha256']) is str
                  and re.fullmatch('[0-9a-f]{64}', comparison['tensor_roster_sha256']) is not None,
                  'comparison tensor roster binding invalid')
            for row in comparison['categories'].values():
                _need(type(row['passed']) is bool and type(row['tensors']) is int and row['tensors'] > 0
                      and type(row['scalars']) is int and row['scalars'] > 0
                      and type(row['max_abs']) in (int, float) and math.isfinite(row['max_abs'])
                      and row['max_abs'] >= 0, 'comparison tensor evidence incomplete or nonfinite')
                _need(not comparison['passed'] or row['passed'], 'comparison hides a failed category')
        replay = case['comparisons']['candidate_target_exact_replay']
        _need(type(replay['full_route_records_equal']) is bool
              and (not replay['passed'] or replay['full_route_records_equal']),
              'target replay hides changed full-route diagnostics')
        _need(set(case['roles']) == set(ROLES), 'missing or unexpected integrated route roles')
        for role, record in case['roles'].items():
            _need(record['device'] == ('cpu' if role == 'candidate_cpu' else device)
                  and record['precision_policy'] == PRECISION_POLICY
                  and record['conditioner_precision_policy'] == 'LEGACY_FP32',
                  'route device or precision-policy ownership mismatch')
            _need(record['optimizer_steps'] == 3 and record['generated_path_count'] == 4
                  and record['full_path_diagnostics_bound'] is True
                  and record['trainable_parameters_and_moments_FP32'] is True,
                  'route replay or optimizer evidence incomplete')
            _need(record['full_route_sha256'] == _digest({k: v for k, v in record.items() if k != 'full_route_sha256'}),
                  'route record digest mismatch')
            for key in ('base_inputs_sha256', 'common_conditional_inputs_sha256', 'shared_physical_weights_sha256'):
                _need(record[key] == case['roles']['candidate_cpu'][key],
                      'declared common-input/weight equality contradicts route bindings')
            generated = record['generated_conditional']
            _need(len(generated['conditional_source_paths']) == 2
                  and set(generated['conditional_paths']) == {'retained', 'overflow'},
                  'full generated path roster incomplete')
        if replay['passed']:
            _need(case['roles']['candidate_target']['full_route_sha256']
                  == case['roles']['candidate_target_replay']['full_route_sha256'],
                  'declared exact replay contradicts full-route hashes')
        _need(case['comparisons']['legacy_shared_weight_physical_drift']['gates_candidate_completion'] is False,
              'legacy drift was relabelled as a candidate gate')
        _need(all(type(case['comparisons'][name]['passed']) is bool for name in COMPARISONS),
              'comparison decision must be boolean')
    if not all(case['comparisons'][name]['passed'] for case in cases for name in GATING_COMPARISONS):
        return 'FAIL_PRECISION_PIPELINE_CANDIDATE'
    return ('PASS_CPU_PRECISION_PIPELINE_CONTROLS_CUDA_NOT_EXECUTED' if mode == 'CPU_REFERENCE'
            else 'PASS_SELECTED_CUDA_PRECISION_PIPELINE_CANDIDATE_ONLY')


def run_precision_pipeline_check(*, mode='CPU_REFERENCE', device='cpu', maximum_seconds=300):
    """One fixed four-case check; pair with a 300s child process supervisor.

No retry, installation, parameter search, warmup, or tolerance override exists.
The 2GiB memory and 300s in-process checks are observations, not hard quotas.
"""
    _need(type(mode) is str and type(maximum_seconds) is int and maximum_seconds == 300,
          'explicit mode and fixed 300-second bound required')
    request = DeviceQualificationRequest(mode=mode, device=device, iterations=1, maximum_seconds=300)
    budget = _Budget(request)
    progress = {'stage': 'START', 'optimizer_steps_begun': 0, 'optimizer_steps_completed': 0,
                'cpu_optimizer_steps_begun': 0, 'gpu_optimizer_steps_begun': 0}
    progress.update({kind + suffix: 0 for kind in STEP_KINDS for suffix in ('_begun', '_completed')})
    report = {'schema_version': 'factorized-precision-pipeline-device-check-v1',
        'fixture_id': FIXTURE_ID, 'mode': mode, 'device': device, 'precision_policy': PRECISION_POLICY,
        'torch_version': str(torch.__version__), 'cuda_build_version': torch.version.cuda,
        'tolerance_policy_id': POLICY_ID, 'acceptance_tolerances_unchanged': TOLERANCES,
        'cases': [], 'execution_progress': progress,
        'bounds': {'required_cases': 4, 'routes_per_case': 3, 'base_steps': 12,
            'generated_conditional_steps': 12, 'common_input_conditional_steps': 12,
            'total_optimizer_steps': 36, 'generated_paths': 48,
            'cpu_steps': 12 if mode == 'CUDA' else 36, 'gpu_steps': 24 if mode == 'CUDA' else 0,
            'base_corruption_rows_per_route': 2, 'common_conditional_rows_per_route': 3,
            'state_cap': 4, 'reverse_grid': GRID, 'per_path_jump_candidate_limit': 20000,
            'per_initialization_trial_limit': 256, 'maximum_seconds_soft': 300,
            'maximum_memory_bytes_soft': MAXIMUM_MEMORY_BYTES, 'iterations': 1, 'retries': 0, 'warmups': 0,
            'hard_deadline_requires_child_supervisor': True, 'hard_memory_quota_claimed': False},
        'scope': {'synthetic_only': True, 'source_only_not_installed_release': True,
            'actual_BASE_and_conditional_training_API_exercise_requested': True,
            'tiny_complete_finite_numerical_paths_not_exact_continuous_time_law': True,
            'real_data_accessed': False, 'files_written': False, 'packages_installed': False,
            'cloud_or_paid_jobs_launched': False, 'F105_executed': False,
            'scientific_training_or_convergence_claimed': False, 'production_qualification': False,
            'all_GPU_pipeline_claimed': False, 'speedup_claimed': False,
            'legacy_failure_relabelled': False, 'default_policy_or_tolerance_changed': False,
            'CPU_REFERENCE_explicit_CUDA_discovery_or_allocation_requested': False,
            'library_internal_availability_probes_possible': True,
            'host_work': ['exact metadata/RNG and reference draws', 'FP64 association guide and loss reductions',
                          'jump/Heun control flow and CPU64 physical interface']},
        'comparison_policy': {'candidate_reference': 'SHARED_FP64_CPU_CANDIDATE_NOT_LEGACY_FP32',
            'generated_CPU_GPU_paths_compared_as_common_noise': False,
            'device_and_weight_bound_population_laws_may_use_different_streams': True,
            'cross_device_generated_conditional_update_parity_claimed': False,
            'BASE_parity_requires_exact_recorded_corruption_inputs': True,
            'conditional_parity_uses_separate_explicit_common_inputs_and_initial_weights': True,
            'physical_parity_uses_exact_CPU_trained_snapshot_weights_on_both_devices': True,
            'physical_gradient_boundary': 'CPU64_ROOT_FP32_ENCODING_FP64_BASE_GRAPH_FP32_CAST_BACK_CPU64',
            'conditional_neural_arithmetic_and_all_trainable_parameters_moments': 'FP32',
            'legacy_fixed_weight_physical_drift_is_gating': False,
            'own_target_replay_includes_generated_paths_complete_diagnostics_gradients_weights_moments': True}}
    try:
        _need(CASE_ROSTER == tuple((domain, method) for domain in DOMAINS for method in METHODS)
              and len(CASE_ROSTER) == len(set(CASE_ROSTER)) == 4, 'invalid fixed four-case roster')
        with _numerical_policy(request, progress=progress) as policy:
            report['numerical_policy'] = {'deterministic_algorithms': True, 'intraop_threads': 1,
                'autocast_used': False, 'cuda_precision_family': policy['family'],
                'cuda_precision_settings': policy['settings']}
            if mode == 'CUDA':
                properties = policy['device_properties']
                report['selected_gpu'] = {'name': properties.name, 'total_memory_bytes': properties.total_memory,
                    'compute_capability': [properties.major, properties.minor]}
            for domain, method in CASE_ROSTER:
                progress.update(domain_id=domain, method_id=method)
                budget.check()
                report['cases'].append(_case(domain, method, device, budget, progress))
            _need(all(progress[kind + suffix] == 12 for kind in STEP_KINDS
                      for suffix in ('_begun', '_completed')), 'integrated update count incomplete')
            _need(progress['optimizer_steps_begun'] == progress['optimizer_steps_completed'] == 36
                  and progress['cpu_optimizer_steps_begun'] == (12 if mode == 'CUDA' else 36)
                  and progress['gpu_optimizer_steps_begun'] == (24 if mode == 'CUDA' else 0),
                  'CPU/GPU optimizer step split changed')
            budget.check()
            report['decision'] = _decision(report['cases'], mode, device)
            if mode == 'CUDA':
                report['cuda_memory'] = {'peak_allocated_bytes': torch.cuda.max_memory_allocated(device),
                                        'peak_reserved_bytes': torch.cuda.max_memory_reserved(device)}
        budget.check()
        progress['stage'] = 'COMPLETE'
    except Exception as error:
        report['decision'] = 'STOP_PRECISION_PIPELINE_CHECK_INCOMPLETE'
        report['error_type'] = type(error).__name__
        report['error_diagnostics'] = _error_diagnostics(error)
    report['completed_case_count'] = len(report['cases'])
    report['elapsed_seconds'] = time.perf_counter() - budget.started
    report['process_lifetime_peak_rss_bytes'] = _rss()
    report['explicit_cuda_synchronize_calls'] = budget.explicit_synchronizations
    report['timing_scope'] = 'SYNCHRONIZED_WALL_INCLUDING_HOST_COPY_READBACK_FIRST_USE_NOT_KERNEL_ONLY'
    report['tolerance_values_sha256'] = hashlib.sha256(json.dumps(TOLERANCES, sort_keys=True).encode()).hexdigest()
    _need(len(json.dumps(report, allow_nan=False).encode()) <= MAXIMUM_REPORT_BYTES, 'compact report bound exceeded')
    return report
