"""CPU-only diagnostic replays; no GPU or scientific data requested."""
import copy
import json

import pytest
import torch

from heterodiff.experiments import factorized_update_diagnostics as d
from heterodiff.experiments.factorized_device_qualification import _optimizer


def _payload(gradients, initials=None):
    initials = initials or {name: torch.full_like(gradient, .05) if gradient is not None
                            else torch.tensor([.05], dtype=torch.float32)
                            for name, gradient in gradients.items()}
    model = torch.nn.Module()
    model.weights = torch.nn.ParameterList([torch.nn.Parameter(initials[name].clone()) for name in gradients])
    optimizer = _optimizer(model)
    result = {}
    for name, parameter in zip(gradients, model.weights):
        gradient = gradients[name]
        result['initial/base/' + name] = ('exact', parameter.detach().clone())
        result['base/objective_parameter_gradients/' + name] = (
            'parameter_gradient', None if gradient is None else gradient.detach().clone())
        # Deliberately unrelated forward gradients must not be used for replay.
        result['base/forward_parameter_gradients/' + name] = ('parameter_gradient', torch.full_like(parameter, 99.))
        parameter.grad = None if gradient is None else gradient.detach().clone()
    optimizer.step()
    for name, parameter in zip(gradients, model.weights):
        result['base/updated_parameters/' + name] = ('updated_parameter', parameter.detach().clone())
        for field in ('step', 'exp_avg', 'exp_avg_sq'):
            value = optimizer.state.get(parameter, {}).get(field)
            result['base/optimizer/' + name + '/' + field] = (
                'exact' if field == 'step' else 'optimizer_moment', None if value is None else value.clone())
    return result


def _report(cpu, target, factory=_optimizer):
    return d.build_base_update_diagnostics(cpu, target, optimizer_factory=factory, atol=2e-6, rtol=2e-5)


def _assert_payload_unchanged(before, after):
    assert before.keys() == after.keys()
    for key in before:
        assert before[key][0] == after[key][0]
        left, right = before[key][1], after[key][1]
        if left is None:
            assert right is None
        else:
            assert torch.equal(left, right)


def test_exact_capture_has_genuine_two_step_cpu_control_and_no_disagreement(monkeypatch):
    payload = _payload({'weight': torch.tensor([.1, -.2, 0.], dtype=torch.float32)})
    real_step = torch.optim.AdamW.step
    steps = []
    def checked_step(optimizer, *args, **kwargs):
        assert not optimizer.state
        assert all(parameter.device.type == 'cpu' for group in optimizer.param_groups for parameter in group['params'])
        steps.append(id(optimizer))
        return real_step(optimizer, *args, **kwargs)
    monkeypatch.setattr(torch.optim.AdamW, 'step', checked_step)
    report = _report(payload, payload)
    assert len(steps) == 2
    assert report['cpu_optimizer_replay_steps'] == 2
    assert report['additional_cuda_optimizer_steps'] == 0
    assert report['forward_or_backward_passes'] == 0
    assert report['changes_parity_acceptance'] is False
    assert report['interpretation'] == 'NO_BASE_UPDATED_PARAMETER_FAILURE_AT_EXISTING_TOLERANCES'
    assert not report['coordinate_samples']
    for replay in report['all_parameter_comparison'].values():
        assert all(summary['exact'] for summary in replay.values())
        assert all(summary['maximum_absolute_residual'] == 0 for summary in replay.values())


def test_near_zero_gradient_sensitivity_is_reproduced_on_cpu_and_only_supported():
    cpu = _payload({'weight': torch.tensor([0.], dtype=torch.float32)})
    target = _payload({'weight': torch.tensor([1e-9], dtype=torch.float32)})
    report = _report(cpu, target)
    assert report['interpretation'] == 'CAPTURED_GRADIENT_SENSITIVITY_SUPPORTED_NOT_PROVEN'
    row = report['coordinate_samples'][0]
    assert row['tensor_name'] == 'weight' and row['index'] == [0]
    assert row['cpu_reference']['objective_gradient'] == 0
    assert row['target']['objective_gradient'] == pytest.approx(1e-9)
    assert row['target']['step'] == 1
    assert row['target']['exp_avg'] == pytest.approx(1e-10)
    assert row['target']['exp_avg_sq'] == pytest.approx(1e-21)
    assert row['target']['cpu_replay_updated_residual'] == 0
    assert row['actual_updated_gap_target_minus_cpu'] == pytest.approx(-9.0908e-5, abs=1e-9)
    assert row['ideal_fp64_updated_gap_target_minus_cpu'] == pytest.approx(-9.090909e-5, abs=1e-11)
    assert row['cpu_replay_updated_gap_target_gradient_minus_cpu_gradient'] == row['actual_updated_gap_target_minus_cpu']
    assert report['all_parameter_comparison']['captured_target_gradient_cpu_replay']['updated_parameters']['exact']
    assert report['gradient_source'].startswith('base/objective_parameter_gradients/')


def test_update_only_perturbation_requires_optimizer_review_not_gradient_explanation():
    cpu = _payload({'weight': torch.tensor([.1], dtype=torch.float32)})
    target = copy.deepcopy(cpu)
    target['base/updated_parameters/weight'][1].add_(1e-4)
    report = _report(cpu, target)
    assert report['interpretation'] == 'SAME_GRADIENT_OPTIMIZER_RESIDUAL_REQUIRES_REVIEW'
    comparisons = report['all_parameter_comparison']['captured_target_gradient_cpu_replay']
    assert comparisons['optimizer_moments']['exact']
    assert not comparisons['updated_parameters']['exact']
    assert not comparisons['updated_parameters']['fp32_roundoff_close']
    assert comparisons['updated_parameters']['maximum_absolute_residual'] == pytest.approx(1e-4, abs=2e-9)
    assert report['coordinate_samples'][0]['ideal_fp64_updated_gap_target_minus_cpu'] == 0


def test_descriptive_update_tolerance_does_not_claim_exact_optimizer_arithmetic():
    cpu = _payload({'weight': torch.tensor([0.], dtype=torch.float32)})
    target = _payload({'weight': torch.tensor([1e-9], dtype=torch.float32)})
    target['base/updated_parameters/weight'][1].add_(1e-6)
    report = _report(cpu, target)
    summary = report['all_parameter_comparison']['captured_target_gradient_cpu_replay']['updated_parameters']
    assert summary['within_existing_update_tolerance']
    assert not summary['exact'] and not summary['fp32_roundoff_close']
    assert report['interpretation'] == 'SAME_GRADIENT_OPTIMIZER_RESIDUAL_REQUIRES_REVIEW'


def test_cpu_control_failure_is_reported_without_reinterpreting_original_parity():
    cpu = _payload({'weight': torch.tensor([.1], dtype=torch.float32)})
    target = copy.deepcopy(cpu)
    cpu['base/updated_parameters/weight'][1].add_(1e-4)
    report = _report(cpu, target)
    assert report['interpretation'] == 'CPU_REPLAY_CONTROL_MISMATCH_REVIEW_REQUIRED'
    assert not report['all_parameter_comparison']['cpu_gradient_control']['updated_parameters']['exact']
    assert report['changes_parity_acceptance'] is False


def test_inconsistent_first_step_is_rejected_before_replay():
    cpu = _payload({'weight': torch.tensor([.1], dtype=torch.float32)})
    target = copy.deepcopy(cpu)
    target['base/optimizer/weight/step'][1].fill_(2)
    def forbidden(_):
        raise AssertionError('optimizer must not be constructed before captured state is valid')
    with pytest.raises(d.BaseUpdateDiagnosticError, match='step=1'):
        _report(cpu, target, forbidden)


@pytest.mark.parametrize('field', ['exp_avg', 'exp_avg_sq'])
@pytest.mark.parametrize('side', ['cpu_reference', 'target'])
def test_finite_moment_anomalies_remain_reportable_evidence_not_a_diagnostic_stop(field, side):
    cpu = _payload({'weight': torch.tensor([.1], dtype=torch.float32)})
    target = copy.deepcopy(cpu)
    (cpu if side == 'cpu_reference' else target)['base/optimizer/weight/' + field][1].add_(.01)
    report = _report(cpu, target)
    assert report['interpretation'] == 'CAPTURED_FIRST_STEP_MOMENT_RESIDUAL_REQUIRES_REVIEW'
    assert not report['fresh_first_step_state_consistent']
    summary = report['first_step_moment_consistency'][side]
    assert summary['inconsistent_tensor_names'] == ['weight/' + field]
    assert summary['inconsistent_tensor_count'] == 1
    assert summary['maximum_absolute_residual_from_ideal_fp64'] == pytest.approx(.01, abs=1e-9)
    replay_side = 'cpu_gradient_control' if side == 'cpu_reference' else 'captured_target_gradient_cpu_replay'
    assert not report['all_parameter_comparison'][replay_side]['optimizer_moments']['exact']
    assert report['cpu_optimizer_replay_steps'] == 2
    assert report['changes_parity_acceptance'] is False


def test_initial_value_or_shape_difference_is_rejected_before_replay():
    cpu = _payload({'weight': torch.tensor([.1], dtype=torch.float32)})
    target = copy.deepcopy(cpu)
    target['initial/base/weight'][1].add_(.1)
    with pytest.raises(d.BaseUpdateDiagnosticError, match='initial CPU/target parameters are not exact'):
        _report(cpu, target)


def test_none_gradient_has_no_state_and_is_preserved_by_both_replays():
    cpu = _payload({'used': torch.tensor([.1]), 'unused': None})
    report = _report(cpu, cpu)
    assert report['parameter_tensor_count'] == 2
    assert report['all_parameter_comparison']['cpu_gradient_control']['optimizer_moments']['absent_tensor_count'] == 2
    assert report['all_parameter_comparison']['cpu_gradient_control']['optimizer_steps']['absent_tensor_count'] == 1


@pytest.mark.parametrize('change', ['state', 'updated', 'presence'])
def test_none_gradient_state_update_or_cross_device_presence_ambiguity_rejected(change):
    cpu = _payload({'unused': None})
    target = copy.deepcopy(cpu)
    if change == 'state':
        target['base/optimizer/unused/step'] = ('exact', torch.tensor(1.))
    elif change == 'updated':
        target['base/updated_parameters/unused'][1].add_(.1)
    else:
        target = _payload({'unused': torch.tensor([0.])})
    with pytest.raises(d.BaseUpdateDiagnosticError):
        _report(cpu, target)


def test_tiny_gradients_with_underflowing_second_moments_are_supported():
    cpu = _payload({'weight': torch.tensor([0., 1e-30, -1e-30], dtype=torch.float32)})
    assert cpu['base/optimizer/weight/exp_avg_sq'][1].eq(0).all()
    report = _report(cpu, cpu)
    assert report['all_parameter_comparison']['cpu_gradient_control']['optimizer_moments']['exact']


def test_representable_subnormal_moment_flushed_to_zero_is_retained_as_evidence():
    cpu = _payload({'weight': torch.tensor([1e-19], dtype=torch.float32)})
    target = copy.deepcopy(cpu)
    original = float(cpu['base/optimizer/weight/exp_avg_sq'][1])
    assert 0 < original < torch.finfo(torch.float32).tiny
    target['base/optimizer/weight/exp_avg_sq'][1].zero_()
    report = _report(cpu, target)
    assert report['interpretation'] == 'CAPTURED_FIRST_STEP_MOMENT_RESIDUAL_REQUIRES_REVIEW'
    assert report['first_step_moment_consistency']['target']['inconsistent_tensor_names'] == ['weight/exp_avg_sq']
    residual = report['all_parameter_comparison']['captured_target_gradient_cpu_replay']['optimizer_moments']
    assert not residual['exact']
    assert residual['maximum_absolute_residual'] == original
    assert report['cpu_optimizer_replay_steps'] == 2


def test_coordinate_sampling_is_deterministic_lexical_bounded_and_covers_all_comparisons():
    names = ['weight' + str(i).zfill(2) for i in reversed(range(12))]
    cpu = _payload({name: torch.tensor([[0., 0.], [0., 0.]]) for name in names})
    target = _payload({name: torch.tensor([[1e-9, 2e-9], [2e-9, 0.]]) for name in names})
    before_cpu, before_target = copy.deepcopy(cpu), copy.deepcopy(target)
    report = _report(cpu, target)
    assert report == _report(dict(reversed(tuple(cpu.items()))), dict(reversed(tuple(target.items()))))
    assert report['sampling']['sample_count'] == 8
    assert report['sampling']['omitted_failing_tensor_count'] == 4
    assert report['sampling']['omitted_failing_scalar_count'] == 28
    assert report['observed_update_disagreement']['failing_tensor_count'] == 12
    assert report['observed_update_disagreement']['failing_scalar_count'] == 36
    assert [row['tensor_name'] for row in report['coordinate_samples']] == sorted(names)[:8]
    assert all(row['flat_index'] == 1 and row['index'] == [0, 1] for row in report['coordinate_samples'])
    assert report['all_parameter_comparison']['captured_target_gradient_cpu_replay']['updated_parameters']['scalar_count'] == 48
    assert len(json.dumps(report, separators=(',', ':')).encode()) <= d.MAXIMUM_REPORT_BYTES
    _assert_payload_unchanged(before_cpu, cpu)
    _assert_payload_unchanged(before_target, target)


def test_full_name_length_eight_sample_report_fits_byte_limit():
    names = [str(i).zfill(2) + 'x' * 126 for i in range(8)]
    cpu = _payload({name: torch.tensor([0.]) for name in names})
    target = _payload({name: torch.tensor([1e-9]) for name in names})
    report = _report(cpu, target)
    assert len(json.dumps(report, separators=(',', ':')).encode()) <= 16384


def test_eight_sample_report_with_long_names_and_moment_anomalies_remains_bounded():
    names = [str(i).zfill(2) + 'x' * 126 for i in range(8)]
    cpu = _payload({name: torch.tensor([0.]) for name in names})
    target = _payload({name: torch.tensor([1e-9]) for name in names})
    for payload in (cpu, target):
        for name in names:
            for field in ('exp_avg', 'exp_avg_sq'):
                payload['base/optimizer/' + name + '/' + field][1].add_(.01)
    report = _report(cpu, target)
    assert report['first_step_moment_consistency']['target']['inconsistent_tensor_names_truncated']
    assert len(json.dumps(report, separators=(',', ':')).encode()) <= 16384


def test_helper_does_not_touch_input_storage_rng_or_explicit_cuda_operations(monkeypatch):
    cpu = _payload({'weight': torch.tensor([0., .1, -.1])})
    target = _payload({'weight': torch.tensor([1e-9, .1, -.1])})
    before_cpu, before_target = copy.deepcopy(cpu), copy.deepcopy(target)
    rng_before = torch.random.get_rng_state().clone()
    def forbidden(*args, **kwargs):
        raise AssertionError('diagnostic requested CUDA or RNG operation')
    for name in ('device_count', 'get_device_properties', 'synchronize', 'init',
                 'reset_peak_memory_stats', 'max_memory_allocated', 'max_memory_reserved'):
        monkeypatch.setattr(torch.cuda, name, forbidden)
    monkeypatch.setattr(torch, 'manual_seed', forbidden)
    monkeypatch.setattr(torch, 'randn', forbidden)
    monkeypatch.setattr(torch.Tensor, 'backward', forbidden)
    _report(cpu, target)
    assert torch.equal(rng_before, torch.random.get_rng_state())
    _assert_payload_unchanged(before_cpu, cpu)
    _assert_payload_unchanged(before_target, target)


@pytest.mark.parametrize('field,value', [('lr', .002), ('eps', 1e-7), ('weight_decay', .1),
    ('betas', (.8, .999)), ('foreach', True), ('fused', True), ('amsgrad', True),
    ('maximize', True), ('capturable', True), ('differentiable', True)])
def test_optimizer_settings_cannot_be_changed_for_diagnostics(field, value):
    payload = _payload({'weight': torch.tensor([.1])})
    def changed(model):
        optimizer = _optimizer(model)
        optimizer.param_groups[0][field] = value
        return optimizer
    with pytest.raises(d.BaseUpdateDiagnosticError, match='optimizer setting changed: ' + field):
        _report(payload, payload, changed)


@pytest.mark.parametrize('kind', ['sgd', 'prefilled', 'wrong_parameters'])
def test_ordinary_fresh_adamw_parameter_identity_required(kind):
    payload = _payload({'weight': torch.tensor([.1])})
    def invalid(model):
        if kind == 'sgd':
            return torch.optim.SGD(model.parameters(), lr=.001)
        optimizer = _optimizer(model)
        if kind == 'prefilled':
            optimizer.state[model.weights[0]]['step'] = torch.tensor(1.)
        else:
            optimizer.param_groups[0]['params'] = [torch.nn.Parameter(torch.tensor([.05]))]
        return optimizer
    with pytest.raises(d.BaseUpdateDiagnosticError):
        _report(payload, payload, invalid)


@pytest.mark.parametrize('kind', ['missing', 'extra', 'dtype', 'shape', 'category', 'nan', 'device', 'empty'])
def test_payload_roster_and_dense_finite_cpu_fp32_contract_enforced(kind):
    payload = _payload({'weight': torch.tensor([.1])})
    target = copy.deepcopy(payload)
    key = 'base/objective_parameter_gradients/weight'
    if kind == 'missing':
        del target[key]
    elif kind == 'extra':
        target['base/optimizer/extra/step'] = ('exact', torch.tensor(1.))
    elif kind == 'dtype':
        target[key] = ('parameter_gradient', torch.tensor([.1], dtype=torch.float64))
    elif kind == 'shape':
        target[key] = ('parameter_gradient', torch.tensor([[.1]]))
    elif kind == 'category':
        target[key] = ('forward', target[key][1])
    elif kind == 'nan':
        target[key][1].fill_(float('nan'))
    elif kind == 'device':
        target[key] = ('parameter_gradient', torch.empty((1,), device='meta'))
    else:
        target[key] = ('parameter_gradient', torch.empty((0,)))
    with pytest.raises(d.BaseUpdateDiagnosticError):
        _report(payload, target)


@pytest.mark.parametrize('atol,rtol', [(-1., 0.), (float('nan'), 0.), (0., float('inf')), (True, 0.)])
def test_invalid_descriptive_tolerance_rejected(atol, rtol):
    payload = _payload({'weight': torch.tensor([.1])})
    with pytest.raises(d.BaseUpdateDiagnosticError, match='tolerances'):
        d.build_base_update_diagnostics(payload, payload, optimizer_factory=_optimizer, atol=atol, rtol=rtol)


def test_parameter_roster_count_and_scalar_bounds_checked_before_optimizer(monkeypatch):
    payload = _payload({'weight': torch.tensor([.1, .2])})
    monkeypatch.setattr(d, 'MAXIMUM_PARAMETER_SCALARS', 1)
    with pytest.raises(d.BaseUpdateDiagnosticError, match='bound'):
        _report(payload, payload)


def test_aggregate_parameter_scalar_bound_checked_before_replay(monkeypatch):
    payload = _payload({'a': torch.tensor([.1, .2]), 'b': torch.tensor([.3, .4])})
    monkeypatch.setattr(d, 'MAXIMUM_PARAMETER_SCALARS', 2)
    def forbidden(_):
        raise AssertionError('optimizer must not start above aggregate scalar bound')
    with pytest.raises(d.BaseUpdateDiagnosticError, match='scalar count outside diagnostic bound'):
        _report(payload, payload, forbidden)
    monkeypatch.setattr(d, 'MAXIMUM_PARAMETER_SCALARS', 262144)
    monkeypatch.setattr(d, 'MAXIMUM_PARAMETER_TENSORS', 0)
    with pytest.raises(d.BaseUpdateDiagnosticError, match='bound'):
        _report(payload, payload)
