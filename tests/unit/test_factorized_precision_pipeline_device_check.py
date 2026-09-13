"""CPU-only verification of the bounded integrated precision GPU-check harness.

No CUDA run is authorized by these tests. GPU-labelled acceptance tests inspect
pure report decisions only; the one actual workload uses CPU_REFERENCE/cpu.
"""
from copy import deepcopy
import json
import math

import pytest
import torch

from heterodiff.experiments import factorized_precision_pipeline_device_check as q
from heterodiff.experiments.factorized_base_precision import PRECISION_POLICY


EXPECTED_CASES = (
    ('R3-PHYS', 'association-aware-guide-plus-residual'),
    ('R3-PHYS', 'unified-direct-conditioner'),
    ('R4-RETAIL', 'association-aware-guide-plus-residual'),
    ('R4-RETAIL', 'unified-direct-conditioner'),
)
EXPECTED_TOLERANCES = {
    'forward': (2e-6, 2e-5), 'coordinate_gradient': (2e-5, 2e-4),
    'coordinate_hessian': (1e-4, 1e-3), 'parameter_gradient': (2e-5, 2e-4),
    'loss': (2e-6, 2e-5), 'updated_parameter': (2e-6, 2e-5),
    'optimizer_moment': (2e-6, 2e-4), 'physical': (2e-5, 2e-4),
}


@pytest.mark.parametrize('settings', (
    {'mode': 'AUTO'}, {'mode': None}, {'mode': 'CPU_REFERENCE', 'device': 'cuda:0'},
    {'mode': 'CUDA', 'device': 'cpu'}, {'mode': 'CUDA', 'device': 'cuda'},
    {'mode': 'CUDA', 'device': 'cuda:-1'}, {'mode': 'CPU_REFERENCE', 'device': None},
    {'maximum_seconds': 120}, {'maximum_seconds': 301}, {'maximum_seconds': 300.},
    {'maximum_seconds': True}, {'maximum_seconds': '300'},
    {'iterations': 2}, {'precision_policy': 'LEGACY_FP32'}, {'tolerances': {}},
))
def test_invalid_or_expanded_request_rejected_before_numerical_work(monkeypatch, settings):
    def forbidden(*_args, **_kwargs):
        pytest.fail('invalid or expanded request reached numerical work')
    monkeypatch.setattr(q, '_case', forbidden)
    monkeypatch.setattr(q, '_numerical_policy', forbidden)
    with pytest.raises((TypeError, ValueError)):
        q.run_precision_pipeline_check(**settings)


def test_acceptance_tolerances_are_the_existing_frozen_values():
    assert q.TOLERANCES == EXPECTED_TOLERANCES


@pytest.fixture(scope='module')
def actual_report():
    before_threads = torch.get_num_threads()
    before_determinism = torch.are_deterministic_algorithms_enabled()
    before_warn = torch.is_deterministic_algorithms_warn_only_enabled()
    before_rng = torch.random.get_rng_state().clone()
    def forbidden(*_args, **_kwargs):
        pytest.fail('CPU_REFERENCE made an explicit CUDA discovery/allocation/synchronization call')
    # Ordinary library-internal availability health probes remain possible;
    # these are the explicit device APIs the harness must not request on CPU.
    with pytest.MonkeyPatch.context() as patches:
        for name in ('get_device_properties', 'device_count', 'synchronize',
                     'reset_peak_memory_stats', 'max_memory_allocated', 'max_memory_reserved'):
            patches.setattr(torch.cuda, name, forbidden)
        report = q.run_precision_pipeline_check(mode='CPU_REFERENCE', device='cpu', maximum_seconds=300)
    assert torch.get_num_threads() == before_threads
    assert torch.are_deterministic_algorithms_enabled() == before_determinism
    assert torch.is_deterministic_algorithms_warn_only_enabled() == before_warn
    assert torch.equal(before_rng, torch.random.get_rng_state())
    return report


def test_actual_cpu_workload_complete_exact_roster_and_fixed_budgets(actual_report):
    report = actual_report
    assert report['decision'].startswith('PASS_CPU_'), report
    assert report['completed_case_count'] == 4
    assert tuple((row['domain_id'], row['method_id']) for row in report['cases']) == EXPECTED_CASES
    assert report['mode'] == 'CPU_REFERENCE' and report['device'] == 'cpu'
    bounds = report['bounds']
    for name, expected in (('required_cases', 4), ('routes_per_case', 3), ('base_steps', 12),
                           ('generated_conditional_steps', 12), ('common_input_conditional_steps', 12),
                           ('total_optimizer_steps', 36), ('generated_paths', 48)):
        assert bounds[name] == expected
    assert bounds['maximum_seconds_soft'] == 300
    assert bounds['maximum_memory_bytes_soft'] == 2 * 1024**3
    progress = report['execution_progress']
    for stem in ('base_updates', 'conditional_updates', 'conditional_control_updates'):
        assert progress[stem + '_begun'] == progress[stem + '_completed'] == 12
    assert progress['optimizer_steps_begun'] == progress['optimizer_steps_completed'] == 36
    assert progress['cpu_optimizer_steps_begun'] == 36 and progress['gpu_optimizer_steps_begun'] == 0
    assert report['explicit_cuda_synchronize_calls'] == 0
    assert math.isfinite(report['elapsed_seconds']) and report['elapsed_seconds'] <= 300
    assert len(json.dumps(report, allow_nan=False).encode()) <= q.MAXIMUM_REPORT_BYTES


def test_actual_cases_include_all_required_common_input_contrasts_and_exact_replay(actual_report):
    expected_comparisons = {
        'common_base_cpu_vs_target', 'common_conditional_cpu_vs_target',
        'shared_weight_physical_cpu_vs_target', 'candidate_target_exact_replay',
        'legacy_shared_weight_physical_drift',
    }
    for case in actual_report['cases']:
        assert case['completed_base_steps'] == case['completed_generated_conditional_steps'] == 3
        assert case['completed_common_input_conditional_steps'] == 3
        assert case['generated_path_count'] == 12
        for name in ('initial_weights_exact_across_routes', 'common_base_inputs_exact_across_routes',
                     'common_conditional_inputs_exact_across_routes', 'shared_physical_weights_exact_across_routes'):
            assert case[name] is True
        assert set(case['comparisons']) == expected_comparisons
        for name in expected_comparisons - {'legacy_shared_weight_physical_drift'}:
            comparison = case['comparisons'][name]
            assert comparison['passed'] is True and comparison['failure_count'] == 0


def require_no_pass(cases, mode='CPU_REFERENCE'):
    try:
        decision = q._decision(cases, mode)
    except (ValueError, TypeError, KeyError):
        return
    assert not decision.startswith('PASS'), decision


@pytest.mark.parametrize('shape', ('missing', 'duplicate', 'reordered'))
def test_incomplete_duplicate_or_reordered_case_roster_cannot_pass(actual_report, shape):
    cases = deepcopy(actual_report['cases'])
    if shape == 'missing':
        cases.pop()
    elif shape == 'duplicate':
        cases[-1] = deepcopy(cases[0])
    else:
        cases.reverse()
    require_no_pass(cases)


@pytest.mark.parametrize('name', (
    'common_base_cpu_vs_target', 'common_conditional_cpu_vs_target',
    'shared_weight_physical_cpu_vs_target', 'candidate_target_exact_replay',
    'legacy_shared_weight_physical_drift',
))
def test_missing_required_contrast_cannot_pass(actual_report, name):
    cases = deepcopy(actual_report['cases'])
    cases[0]['comparisons'].pop(name)
    require_no_pass(cases)


@pytest.mark.parametrize('name', (
    'common_base_cpu_vs_target', 'common_conditional_cpu_vs_target',
    'shared_weight_physical_cpu_vs_target', 'candidate_target_exact_replay',
))
def test_failure_of_any_gating_contrast_cannot_pass(actual_report, name):
    cases = deepcopy(actual_report['cases'])
    cases[0]['comparisons'][name]['passed'] = False
    require_no_pass(cases)


@pytest.mark.parametrize('field', (
    'initial_weights_exact_across_routes', 'common_base_inputs_exact_across_routes',
    'common_conditional_inputs_exact_across_routes', 'shared_physical_weights_exact_across_routes',
))
def test_changed_input_or_weight_binding_cannot_pass(actual_report, field):
    cases = deepcopy(actual_report['cases'])
    cases[0][field] = False
    require_no_pass(cases)


@pytest.mark.parametrize('field', (
    'completed_base_steps', 'completed_generated_conditional_steps',
    'completed_common_input_conditional_steps', 'generated_path_count',
))
def test_incomplete_route_step_or_path_count_cannot_pass(actual_report, field):
    cases = deepcopy(actual_report['cases'])
    cases[0][field] -= 1
    require_no_pass(cases)


def test_cpu_complete_evidence_cannot_be_relabelled_cuda(actual_report):
    require_no_pass(deepcopy(actual_report['cases']), mode='CUDA')


def test_legacy_physical_drift_disagreement_is_visible_but_not_candidate_gate(actual_report):
    cases = deepcopy(actual_report['cases'])
    for case in cases:
        comparison = case['comparisons']['legacy_shared_weight_physical_drift']
        comparison['passed'] = False
        comparison['failure_count'] = 1
    assert q._decision(cases, 'CPU_REFERENCE').startswith('PASS_CPU_')


@pytest.mark.parametrize('role', ('candidate_cpu', 'candidate_target', 'candidate_target_replay'))
def test_missing_route_cannot_pass(actual_report, role):
    cases = deepcopy(actual_report['cases'])
    cases[0]['roles'].pop(role)
    require_no_pass(cases)


@pytest.mark.parametrize('field,value', (
    ('device', 'cuda:0'), ('precision_policy', 'LEGACY_FP32'),
    ('generated_path_count', 3), ('optimizer_steps', 2),
    ('trainable_parameters_and_moments_FP32', False), ('full_path_diagnostics_bound', False),
))
def test_incorrect_role_device_policy_ownership_or_completeness_cannot_pass(actual_report, field, value):
    cases = deepcopy(actual_report['cases'])
    cases[0]['roles']['candidate_target'][field] = value
    require_no_pass(cases)


def test_corrupt_replay_route_hash_cannot_hide_behind_pass_flag(actual_report):
    cases = deepcopy(actual_report['cases'])
    cases[0]['roles']['candidate_target_replay']['full_route_sha256'] = 'f' * 64
    require_no_pass(cases)


def test_actual_role_evidence_records_complete_paths_and_fp32_ownership(actual_report):
    for case in actual_report['cases']:
        assert set(case['roles']) == {'candidate_cpu', 'candidate_target', 'candidate_target_replay'}
        for row in case['roles'].values():
            assert row['device'] == 'cpu' and row['precision_policy'] == PRECISION_POLICY
            assert row['generated_path_count'] == 4 and row['optimizer_steps'] == 3
            assert row['trainable_parameters_and_moments_FP32'] is True
            assert row['full_path_diagnostics_bound'] is True
            assert len(row['full_route_sha256']) == 64
        assert case['roles']['candidate_target']['full_route_sha256'] == case['roles']['candidate_target_replay']['full_route_sha256']


@pytest.mark.parametrize('defect', (
    'failure_count', 'empty_categories', 'missing_category', 'category_failure',
    'zero_tensors', 'zero_scalars', 'nonfinite_error', 'negative_error',
    'invalid_roster_digest', 'missing_replay_diagnostics',
))
def test_incomplete_or_contradictory_comparison_evidence_cannot_pass(actual_report, defect):
    cases = deepcopy(actual_report['cases'])
    comparison = cases[0]['comparisons']['candidate_target_exact_replay']
    row = comparison['categories']['updated_parameter']
    if defect == 'failure_count':
        comparison['failure_count'] = 1
    elif defect == 'empty_categories':
        comparison['categories'] = {}
    elif defect == 'missing_category':
        comparison['categories'].pop('updated_parameter')
    elif defect == 'category_failure':
        row['passed'] = False
    elif defect == 'zero_tensors':
        row['tensors'] = 0
    elif defect == 'zero_scalars':
        row['scalars'] = 0
    elif defect == 'nonfinite_error':
        row['max_abs'] = math.nan
    elif defect == 'negative_error':
        row['max_abs'] = -1.
    elif defect == 'invalid_roster_digest':
        comparison['tensor_roster_sha256'] = 'not-a-digest'
    else:
        comparison['full_route_records_equal'] = False
    require_no_pass(cases)


def _resign_role(record):
    record['full_route_sha256'] = q._digest({
        key: value for key, value in record.items() if key != 'full_route_sha256'})


@pytest.mark.parametrize('field', (
    'base_inputs_sha256', 'common_conditional_inputs_sha256', 'shared_physical_weights_sha256',
))
def test_recomputed_role_hash_cannot_hide_common_input_cross_binding(actual_report, field):
    cases = deepcopy(actual_report['cases'])
    # Change both target records equally, preserving exact replay but breaking
    # the declared common-input comparison with the CPU reference.
    for role in ('candidate_target', 'candidate_target_replay'):
        record = cases[0]['roles'][role]
        record[field] = 'f' * 64
        _resign_role(record)
    require_no_pass(cases)


def test_recomputed_replay_hash_cannot_hide_changed_generated_paths(actual_report):
    cases = deepcopy(actual_report['cases'])
    record = cases[0]['roles']['candidate_target_replay']
    record['generated_conditional']['actual_conditional_inputs_sha256'] = 'f' * 64
    _resign_role(record)
    require_no_pass(cases)


def _tiny_updated_model():
    model = torch.nn.Module()
    model.register_parameter('active', torch.nn.Parameter(torch.tensor([.5, -.25], dtype=torch.float32)))
    model.register_parameter('unused', torch.nn.Parameter(torch.tensor([.75], dtype=torch.float32)))
    optimizer = torch.optim.AdamW(model.parameters(), lr=.01, foreach=False, fused=False)
    model.active.square().sum().backward()
    optimizer.step()
    contract = {name: tuple(value.shape) for name, value in model.named_parameters()}
    return model, optimizer, contract


def test_optimizer_snapshot_includes_every_leaf_and_legitimate_unused_state():
    model, optimizer, contract = _tiny_updated_model()
    snapshot = q._snapshot(model, optimizer, contract, 'cpu', 'control')
    assert len(snapshot) == 5 * len(contract)
    assert snapshot['control/gradients/unused'] == ('parameter_gradient', None)
    for field in ('step', 'exp_avg', 'exp_avg_sq'):
        assert snapshot['control/optimizer/unused/' + field][1] is None
    assert snapshot['control/optimizer/active/step'][1].item() == 1
    for name, (_, tensor) in snapshot.items():
        if tensor is not None and not name.endswith('/step'):
            assert tensor.dtype == torch.float32 and tensor.device.type == 'cpu'


@pytest.mark.parametrize('defect', (
    'missing_parameter', 'nonfinite_parameter', 'nonfinite_gradient',
    'missing_moment', 'nonfinite_moment', 'wrong_moment_dtype', 'wrong_moment_shape',
    'wrong_step', 'unexpected_state', 'unused_state', 'no_active_gradients', 'wrong_device',
))
def test_optimizer_snapshot_rejects_incomplete_nonfinite_or_wrong_ownership(defect):
    model, optimizer, contract = _tiny_updated_model()
    state = optimizer.state[model.active]
    device = 'cpu'
    if defect == 'missing_parameter':
        del model.unused
    elif defect == 'nonfinite_parameter':
        with torch.no_grad():
            model.active[0] = math.nan
    elif defect == 'nonfinite_gradient':
        model.active.grad[0] = math.nan
    elif defect == 'missing_moment':
        state.pop('exp_avg')
    elif defect == 'nonfinite_moment':
        state['exp_avg'][0] = math.inf
    elif defect == 'wrong_moment_dtype':
        state['exp_avg'] = state['exp_avg'].double()
    elif defect == 'wrong_moment_shape':
        state['exp_avg'] = torch.zeros(1, dtype=torch.float32)
    elif defect == 'wrong_step':
        state['step'].fill_(2)
    elif defect == 'unexpected_state':
        state['unexpected'] = torch.tensor(1.)
    elif defect == 'unused_state':
        optimizer.state[model.unused]['step'] = torch.tensor(1.)
    elif defect == 'no_active_gradients':
        model.active.grad = None
        optimizer.state.clear()
    else:
        device = 'cuda:0'  # Compare metadata only; never allocate/query CUDA.
    with pytest.raises(ValueError):
        q._snapshot(model, optimizer, contract, device, 'control')


@pytest.mark.parametrize('value', (math.nan, math.inf, -math.inf))
def test_nonfinite_replay_tensor_is_rejected(value):
    with pytest.raises(ValueError):
        q._payload_digest({'state': ('physical', torch.tensor([value]))})


def test_replay_payload_digest_binds_tensor_values_dtype_shape_and_none_presence():
    payload = {'state': ('physical', torch.tensor([1., 2.], dtype=torch.float32)),
               'unused': ('parameter_gradient', None)}
    original = q._payload_digest(payload)
    alternatives = (
        {'state': ('physical', torch.tensor([1., 3.], dtype=torch.float32)), 'unused': ('parameter_gradient', None)},
        {'state': ('physical', torch.tensor([1., 2.], dtype=torch.float64)), 'unused': ('parameter_gradient', None)},
        {'state': ('physical', torch.tensor([[1., 2.]], dtype=torch.float32)), 'unused': ('parameter_gradient', None)},
        {'state': payload['state']},
        {'state': payload['state'], 'unused': ('parameter_gradient', torch.zeros(1))},
    )
    assert all(q._payload_digest(changed) != original for changed in alternatives)
    assert q._payload_digest(dict(reversed(list(payload.items())))) == original


@pytest.mark.parametrize('defect', ('missing', 'nonfinite', 'dtype', 'category'))
def test_common_input_comparison_rejects_malformed_tensor_payloads(defect):
    left = {'coordinate': ('physical', torch.tensor([1.], dtype=torch.float64))}
    right = deepcopy(left)
    if defect == 'missing':
        right = {}
    elif defect == 'nonfinite':
        right['coordinate'][1].fill_(math.nan)
    elif defect == 'dtype':
        right['coordinate'] = ('physical', torch.tensor([1.], dtype=torch.float32))
    else:
        right['coordinate'] = ('forward', right['coordinate'][1])
    with pytest.raises(ValueError):
        q._compact_comparison(left, right)


def test_exact_replay_uses_zero_tolerance_even_within_numerical_parity_limits():
    left = {'coordinate': ('physical', torch.tensor([1.], dtype=torch.float64))}
    right = {'coordinate': ('physical', torch.tensor([1. + 1e-8], dtype=torch.float64))}
    assert q._compact_comparison(left, right)['passed'] is True
    assert q._compact_comparison(left, right, exact=True)['passed'] is False


def test_failed_optimizer_operation_remains_begun_not_completed():
    progress = {'base_updates_begun': 0, 'base_updates_completed': 0,
                'optimizer_steps_begun': 0, 'optimizer_steps_completed': 0,
                'cpu_optimizer_steps_begun': 0, 'gpu_optimizer_steps_begun': 0}
    def failure():
        raise RuntimeError('synthetic failure')
    with pytest.raises(RuntimeError, match='synthetic failure'):
        q._step(progress, 'base_updates', 'cpu', failure)
    assert progress == {'base_updates_begun': 1, 'base_updates_completed': 0,
                        'optimizer_steps_begun': 1, 'optimizer_steps_completed': 0,
                        'cpu_optimizer_steps_begun': 1, 'gpu_optimizer_steps_begun': 0}


def test_actual_report_distinguishes_common_input_controls_from_uncoupled_paths(actual_report):
    scope = actual_report['scope']
    for name in ('real_data_accessed', 'files_written', 'packages_installed',
                 'cloud_or_paid_jobs_launched', 'F105_executed',
                 'scientific_training_or_convergence_claimed', 'production_qualification',
                 'all_GPU_pipeline_claimed', 'speedup_claimed', 'legacy_failure_relabelled',
                 'default_policy_or_tolerance_changed'):
        assert scope[name] is False
    assert scope['synthetic_only'] is True
    assert scope['source_only_not_installed_release'] is True
    comparison = actual_report['comparison_policy']
    assert comparison['generated_CPU_GPU_paths_compared_as_common_noise'] is False
    assert comparison['cross_device_generated_conditional_update_parity_claimed'] is False
    assert comparison['device_and_weight_bound_population_laws_may_use_different_streams'] is True
    assert comparison['physical_parity_uses_exact_CPU_trained_snapshot_weights_on_both_devices'] is True
    assert comparison['conditional_parity_uses_separate_explicit_common_inputs_and_initial_weights'] is True
    assert comparison['legacy_fixed_weight_physical_drift_is_gating'] is False
    for case in actual_report['cases']:
        for role in case['roles'].values():
            generated = role['generated_conditional']
            assert generated['candidate_population_law_id'] != generated['legacy_population_law_id']
            assert generated['cross_device_generated_draws_are_common_inputs'] is False
            assert generated['frozen_BASE_preserved'] is True
            assert generated['sampler_weights_unchanged'] is True


def test_runtime_failure_reports_zero_complete_cases_and_incomplete_begun_step(monkeypatch):
    before = torch.random.get_rng_state().clone()
    def failed_case(_domain, _method, device, _budget, progress):
        def failed_operation():
            raise RuntimeError('synthetic bounded operation failure')
        q._step(progress, 'base_updates', device, failed_operation)
    monkeypatch.setattr(q, '_case', failed_case)
    report = q.run_precision_pipeline_check()
    assert report['decision'] == 'STOP_PRECISION_PIPELINE_CHECK_INCOMPLETE'
    assert report['completed_case_count'] == 0 and report['cases'] == []
    assert report['error_type'] == 'RuntimeError'
    assert report['execution_progress']['optimizer_steps_begun'] == 1
    assert report['execution_progress']['optimizer_steps_completed'] == 0
    assert report['execution_progress']['stage'] != 'COMPLETE'
    assert torch.equal(before, torch.random.get_rng_state())
    assert report['explicit_cuda_synchronize_calls'] == 0


@pytest.mark.parametrize('defect', ('incomplete_count', 'wrong_device_count', 'partial_case_failure'))
def test_public_api_does_not_pass_complete_looking_cases_with_failed_execution_accounting(
        actual_report, monkeypatch, defect):
    rows = deepcopy(actual_report['cases'])
    call_count = 0
    def simulated_case(domain, method, device, _budget, progress):
        nonlocal call_count
        ordinal = call_count
        call_count += 1
        if defect == 'partial_case_failure' and ordinal == 3:
            raise RuntimeError('synthetic failure before last case completed')
        for stem in q.STEP_KINDS:
            progress[stem + '_begun'] += 3
            progress[stem + '_completed'] += 3
        progress['optimizer_steps_begun'] += 9
        progress['optimizer_steps_completed'] += 9
        progress['cpu_optimizer_steps_begun'] += 9
        if ordinal == 3 and defect == 'incomplete_count':
            progress['conditional_control_updates_completed'] -= 1
        if ordinal == 3 and defect == 'wrong_device_count':
            progress['cpu_optimizer_steps_begun'] -= 1
            progress['gpu_optimizer_steps_begun'] += 1
        assert (domain, method) == EXPECTED_CASES[ordinal] and device == 'cpu'
        return rows[ordinal]
    monkeypatch.setattr(q, '_case', simulated_case)
    report = q.run_precision_pipeline_check()
    assert report['decision'] == 'STOP_PRECISION_PIPELINE_CHECK_INCOMPLETE'
    assert report['completed_case_count'] == (3 if defect == 'partial_case_failure' else 4)
    assert report['execution_progress']['stage'] != 'COMPLETE'


def test_changed_fixed_roster_stops_before_any_case_work(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail('changed fixed roster reached case work')
    monkeypatch.setattr(q, '_case', forbidden)
    monkeypatch.setattr(q, 'CASE_ROSTER', q.CASE_ROSTER[:-1])
    report = q.run_precision_pipeline_check()
    assert report['decision'] == 'STOP_PRECISION_PIPELINE_CHECK_INCOMPLETE'
    assert report['completed_case_count'] == 0
    assert report['execution_progress']['optimizer_steps_begun'] == 0
