"""Bounded local candidate qualification; no GPU is exercised by these tests."""
from copy import deepcopy
import json

import pytest
import torch

from heterodiff.experiments import factorized_precision_candidate_qualification as q
from heterodiff.experiments import factorized_device_qualification as legacy


@pytest.fixture(scope='module')
def cpu_report():
    return q.run_precision_candidate_check()


def test_actual_cpu_report_has_all_controls_and_no_cuda_claim(cpu_report):
    assert cpu_report['decision'] == 'PASS_CPU_BASE_PRECISION_CONTROLS_CUDA_NOT_EXECUTED'
    assert cpu_report['completed_case_count'] == 4
    assert cpu_report['execution_progress']['optimizer_steps_completed'] == 24
    assert cpu_report['execution_progress']['gpu_optimizer_steps_begun'] == 0
    assert cpu_report['execution_progress']['cpu_optimizer_steps_begun'] == 24
    assert cpu_report['explicit_cuda_synchronize_calls'] == 0
    assert len(json.dumps(cpu_report, allow_nan=False).encode()) < 32768
    assert tuple((c['domain_id'], c['method_id']) for c in cpu_report['cases']) == q.CASE_ROSTER
    for case in cpu_report['cases']:
        assert set(case['comparisons']) == set(q.COMPARISONS)
        assert set(case['timing_seconds_including_fixture_copy_and_readback']) == set(q.ROLES)
        comparisons = case['comparisons']
        for name in ('candidate_cpu_vs_target', 'candidate_target_exact_replay', 'legacy_target_exact_replay'):
            assert comparisons[name]['passed']
        categories = comparisons['candidate_cpu_vs_target']['categories']
        assert categories['updated_parameter']['scalars'] == 96705
        assert categories['parameter_gradient']['scalars'] == 2*96705
        assert categories['optimizer_moment']['scalars'] == 2*96705
        assert categories['coordinate_hessian']['scalars'] > 0
        assert not comparisons['legacy_cpu_vs_candidate_cpu_drift']['passed']
    assert not cpu_report['scope']['old_legacy_parity_relabelled']
    assert not cpu_report['scope']['production_qualification']
    assert not cpu_report['scope']['conditional_training_or_sampling_executed']
    assert cpu_report['bounds']['unique_base_fixtures'] == 2


def test_existing_acceptance_and_optimizer_are_reused_unchanged(cpu_report):
    assert q._optimizer is legacy._optimizer
    assert q.TOLERANCES is legacy.TOLERANCES
    assert cpu_report['acceptance_tolerances_unchanged'] == {
        'forward': (2e-6, 2e-5), 'coordinate_gradient': (2e-5, 2e-4),
        'coordinate_hessian': (1e-4, 1e-3), 'parameter_gradient': (2e-5, 2e-4),
        'loss': (2e-6, 2e-5), 'updated_parameter': (2e-6, 2e-5),
        'optimizer_moment': (2e-6, 2e-4), 'physical': (2e-5, 2e-4)}


@pytest.mark.parametrize('kwargs', [
    {'mode': 'INSPECT_ONLY'}, {'mode': 'CUDA', 'device': 'cpu'},
    {'mode': 'CPU_REFERENCE', 'device': 'cuda:0'}, {'mode': 'CUDA', 'device': 'cuda'},
    {'mode': 'CUDA', 'device': 'cuda:-1'}, {'mode': 'CUDA', 'device': 'cuda:00'},
    {'maximum_seconds': 119}, {'maximum_seconds': 121}, {'maximum_seconds': 120.},
    {'maximum_seconds': True}, {'iterations': 2}, {'tolerances': {}},
    {'precision_policy': 'LEGACY_FP32'},
])
def test_request_cannot_expand_scope_or_change_acceptance(kwargs):
    with pytest.raises((ValueError, TypeError)):
        q.run_precision_candidate_check(**kwargs)


def test_cuda_failure_is_incomplete_without_any_case_or_gpu_work(monkeypatch):
    monkeypatch.setattr(torch.version, 'cuda', None)
    report = q.run_precision_candidate_check(mode='CUDA', device='cuda:0')
    assert report['decision'] == 'STOP_BASE_PRECISION_CHECK_INCOMPLETE'
    assert report['completed_case_count'] == 0
    assert report['execution_progress']['optimizer_steps_begun'] == 0
    assert report['bounds']['gpu_steps'] == 16 and report['bounds']['cpu_steps'] == 8


@pytest.mark.parametrize('name', ['candidate_cpu_vs_target', 'candidate_target_exact_replay'])
def test_candidate_comparison_or_exact_replay_failure_gates_pass(cpu_report, name):
    cases = deepcopy(cpu_report['cases'])
    cases[2]['comparisons'][name]['passed'] = False
    assert q._decision(cases, 'CUDA') == 'FAIL_BASE_PRECISION_CANDIDATE'


def test_legacy_numeric_failure_remains_visible_but_cannot_veto_candidate(cpu_report):
    cases = deepcopy(cpu_report['cases'])
    cases[0]['comparisons']['legacy_cpu_vs_target']['passed'] = False
    assert q._decision(cases, 'CUDA') == 'PASS_SELECTED_CUDA_BASE_PRECISION_CANDIDATE_ONLY'
    assert not cases[0]['comparisons']['legacy_cpu_vs_target']['passed']


@pytest.mark.parametrize('mutation', ['missing_case', 'duplicate_case', 'missing_control',
                                   'legacy_replay', 'initial_weights', 'step_count'])
def test_incomplete_or_invalid_controls_prevent_completion(cpu_report, mutation):
    cases = deepcopy(cpu_report['cases'])
    if mutation == 'missing_case':
        cases.pop()
    elif mutation == 'duplicate_case':
        cases[1] = deepcopy(cases[0])
    elif mutation == 'missing_control':
        del cases[1]['comparisons']['legacy_cpu_vs_target']
    elif mutation == 'legacy_replay':
        cases[1]['comparisons']['legacy_target_exact_replay']['passed'] = False
    elif mutation == 'initial_weights':
        cases[1]['initial_weights_exact_across_all_six_routes'] = False
    else:
        cases[1]['completed_base_steps'] = 5
    with pytest.raises(ValueError):
        q._decision(cases, 'CUDA')


@pytest.mark.parametrize('category', ['forward', 'coordinate_gradient', 'coordinate_hessian',
                                    'parameter_gradient', 'loss', 'updated_parameter', 'optimizer_moment', 'exact'])
def test_no_comparison_category_can_hide_numeric_failure(category):
    payload = {'tensor': (category, torch.tensor([1.], dtype=torch.float64))}
    changed = {'tensor': (category, torch.tensor([2.], dtype=torch.float64))}
    result = q._compact_comparison(payload, changed)
    assert not result['passed'] and result['failure_count'] == 1
    assert not result['categories'][category]['passed']


def test_cross_precision_is_only_permitted_in_labelled_drift():
    left = {'a': ('forward', torch.tensor([1.], dtype=torch.float32))}
    right = {'a': ('forward', torch.tensor([1.], dtype=torch.float64))}
    with pytest.raises(ValueError, match='dtype'):
        q._compact_comparison(left, right)
    assert q._compact_comparison(left, right, drift=True)['passed']


@pytest.fixture(scope='module')
def actual_payload():
    with q._numerical_policy(q.DeviceQualificationRequest()):
        progress = dict(optimizer_steps_begun=0, optimizer_steps_completed=0,
                        gpu_optimizer_steps_begun=0, cpu_optimizer_steps_begun=0)
        payload = q._exercise_base(*q.CASE_ROSTER[0], 'cpu', candidate=True,
                                  original_cpu=False, progress=progress)
        base, _, joint, _, _, _ = q._fixture(*q.CASE_ROSTER[0])
        batch = q.factorized_configuration_batch(joint.states, joint.reverse_times,
            torch.zeros(3, 64), base.architecture, coordinate_gradients=True)
    return payload, tuple(name for name, _ in base.named_parameters()), batch.coordinates


@pytest.mark.parametrize('mutation', ['missing', 'none', 'nan', 'inf', 'category', 'fp32_forward',
                                   'fp32_hessian', 'fp64_gradient', 'fp64_moment'])
def test_payload_integrity_and_actual_graph_precision(actual_payload, mutation):
    original, names, coordinates = actual_payload
    payload = deepcopy(original)
    key = 'base/forward'
    if mutation == 'missing':
        del payload[key]
    elif mutation == 'none':
        payload[key] = ('forward', None)
    elif mutation in ('nan', 'inf'):
        payload[key][1][0] = float(mutation)
    elif mutation == 'category':
        payload[key] = ('loss', payload[key][1])
    else:
        if mutation == 'fp32_hessian':
            key = next(k for k in payload if '/hessian/' in k)
        elif mutation == 'fp64_gradient':
            key = next(k for k in payload if '/objective_parameter_gradients/' in k)
        elif mutation == 'fp64_moment':
            key = next(k for k in payload if k.endswith('/exp_avg'))
        kind, tensor = payload[key]
        payload[key] = (kind, tensor.float() if mutation.startswith('fp32') else tensor.double())
    with pytest.raises(ValueError):
        q._validate_payload(payload, names, coordinates, candidate=True)


def test_actual_candidate_carries_fp64_graph_and_fp32_leaves(actual_payload):
    payload, names, coordinates = actual_payload
    q._validate_payload(payload, names, coordinates, candidate=True)
    assert payload['base/forward'][1].dtype == torch.float64
    assert payload['base/loss/total'][1].dtype == torch.float64
    for name in names:
        assert payload['initial/base/' + name][1].dtype == torch.float32
        assert payload['base/objective_parameter_gradients/' + name][1].dtype == torch.float32
        assert payload['base/optimizer/' + name + '/exp_avg'][1].dtype == torch.float32
        assert payload['base/optimizer/' + name + '/step'][1].item() == 1


def test_failure_restores_policy_and_preserves_partial_progress(monkeypatch):
    before = (torch.get_num_threads(), torch.are_deterministic_algorithms_enabled(),
              torch.is_deterministic_algorithms_warn_only_enabled())
    def fail(*args):
        raise RuntimeError('injected legacy control failure')
    monkeypatch.setattr(q, '_case', fail)
    report = q.run_precision_candidate_check()
    assert report['decision'] == 'STOP_BASE_PRECISION_CHECK_INCOMPLETE'
    assert not report['cases']
    assert (torch.get_num_threads(), torch.are_deterministic_algorithms_enabled(),
            torch.is_deterministic_algorithms_warn_only_enabled()) == before


def test_final_step_crossing_deadline_never_passes(monkeypatch, cpu_report):
    clock = [0.]
    monkeypatch.setattr(q.time, 'perf_counter', lambda: clock[0])
    def case(domain, method, device, budget, progress):
        index = q.CASE_ROSTER.index((domain, method))
        progress['optimizer_steps_completed'] += 6
        progress['optimizer_steps_begun'] += 6
        progress['cpu_optimizer_steps_begun'] += 6
        if index == 3:
            clock[0] = 120.001
        return deepcopy(cpu_report['cases'][index])
    monkeypatch.setattr(q, '_case', case)
    report = q.run_precision_candidate_check()
    assert report['decision'] == 'STOP_BASE_PRECISION_CHECK_INCOMPLETE'
    assert report['completed_case_count'] == 4
    assert 'soft wall-clock' in report['error_diagnostics']['message']


def test_changed_cpu_gpu_accounting_cannot_pass(monkeypatch, cpu_report):
    def case(domain, method, device, budget, progress):
        progress['optimizer_steps_completed'] += 6
        progress['optimizer_steps_begun'] += 6
        progress['cpu_optimizer_steps_begun'] += 5
        progress['gpu_optimizer_steps_begun'] += 1
        return deepcopy(cpu_report['cases'][q.CASE_ROSTER.index((domain, method))])
    monkeypatch.setattr(q, '_case', case)
    report = q.run_precision_candidate_check()
    assert report['decision'] == 'STOP_BASE_PRECISION_CHECK_INCOMPLETE'
    assert 'step split changed' in report['error_diagnostics']['message']
