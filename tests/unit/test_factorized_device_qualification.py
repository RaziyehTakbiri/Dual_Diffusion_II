"""Synthetic CPU tensor qualification; no CUDA tensor computation requested."""
import json
from dataclasses import FrozenInstanceError

import pytest
import torch

from heterodiff.experiments import factorized_device_qualification as q


@pytest.mark.parametrize('kwargs', [
    {'mode': 'AUTO'}, {'mode': 'CUDA', 'device': 'cpu'}, {'device': 'cuda:0'},
    {'mode': 'CUDA', 'device': 'cuda'}, {'mode': 'CUDA', 'device': 'cuda:-1'},
    {'mode': 'CUDA', 'device': 'cuda:01'}, {'mode': 'CUDA', 'device': 'cuda:0;cmd'},
    {'iterations': 0}, {'iterations': 4}, {'iterations': True},
    {'maximum_seconds': 4}, {'maximum_seconds': 301}, {'maximum_seconds': 5.0},
])
def test_request_rejects_ambiguous_or_unbounded_controls_before_work(kwargs):
    with pytest.raises(q.DeviceQualificationError):
        q.DeviceQualificationRequest(**kwargs)


def test_request_immutable_and_only_explicit_cuda_ordinal_is_accepted_without_query(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('CUDA must not be queried by request validation')
    monkeypatch.setattr(torch.cuda, 'is_available', forbidden)
    request = q.DeviceQualificationRequest(mode='CUDA', device='cuda:3')
    assert request.device == 'cuda:3'
    with pytest.raises(FrozenInstanceError):
        request.device = 'cpu'


def test_fixed_tolerances_use_elementwise_reference_scale_and_exact_replay():
    reference = {'x': ('forward', torch.tensor([0., 1.], dtype=torch.float32))}
    close = {'x': ('forward', torch.tensor([1e-6, 1.00001], dtype=torch.float32))}
    distant = {'x': ('forward', torch.tensor([1e-4, 1.], dtype=torch.float32))}
    assert q._compare(reference, close)['passed']
    assert not q._compare(reference, close, exact=True)['passed']
    result = q._compare(reference, distant)
    assert not result['passed'] and result['failure_names'] == ['x']
    assert q.TOLERANCES['coordinate_hessian'] == (1e-4, 1e-3)
    assert q.POLICY_ID == 'factorized-device-parity-fixed-tolerances-v1'


@pytest.mark.parametrize('bad', [
    {'y': ('loss', torch.tensor(1., dtype=torch.float64))},
    {'x': ('forward', torch.tensor(1., dtype=torch.float64))},
    {'x': ('loss', torch.tensor([1.], dtype=torch.float64))},
    {'x': ('loss', torch.tensor(1., dtype=torch.float32))},
    {'x': ('loss', torch.tensor(float('nan'), dtype=torch.float64))},
])
def test_tampered_tensor_roster_shape_dtype_or_nonfinite_never_passes(bad):
    good = {'x': ('loss', torch.tensor(1., dtype=torch.float64))}
    with pytest.raises(q.DeviceQualificationError):
        q._compare(good, bad)


def test_missing_gradient_or_optimizer_state_is_a_failure_not_a_skip():
    good = {'x': ('parameter_gradient', torch.tensor([0.]))}
    result = q._compare(good, {'x': ('parameter_gradient', None)})
    assert not result['passed'] and result['failure_count'] == 1


def test_unmodified_adamw_has_cpu_parameters_gradients_and_moments():
    model = torch.nn.Linear(1, 1, device='cpu')
    optimizer = q._optimizer(model)
    assert type(optimizer) is torch.optim.AdamW
    model(torch.ones(1, 1, device='cpu')).sum().backward()
    before = model.weight.detach().clone()
    optimizer.step()
    assert not torch.equal(model.weight, before)
    assert set(optimizer.state[model.weight]) == {'step', 'exp_avg', 'exp_avg_sq'}
    assert all(p.device.type == 'cpu' and p.grad.device.type == 'cpu' for p in model.parameters())
    assert all(v.device.type == 'cpu' for v in optimizer.state[model.weight].values())
    assert not any(name in optimizer.__dict__ for name in (
        '_accelerator_graph_capture_health_check', '_cuda_graph_capture_health_check'))


def test_cpu_full_roster_graph_optimizer_physical_parity_without_explicit_cuda_work(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('CPU qualification attempted CUDA query')
    # Ordinary AdamW may internally call is_available; its safety guard is not overridden.
    for name in ('device_count', 'get_device_properties', 'synchronize',
                 'reset_peak_memory_stats', 'max_memory_allocated', 'max_memory_reserved'):
        monkeypatch.setattr(torch.cuda, name, forbidden)
    random_before = torch.random.get_rng_state().clone()
    threads = torch.get_num_threads()
    deterministic = torch.are_deterministic_algorithms_enabled()
    warn = torch.is_deterministic_algorithms_warn_only_enabled()
    report = q.run_qualification(mode='CPU_REFERENCE', device='cpu', iterations=1, maximum_seconds=120)
    assert report['decision'] == 'PASS_CPU_REFERENCE_CUDA_NOT_EXECUTED', report
    assert report['cuda_execution'] == 'CUDA_NOT_EXECUTED'
    assert report['completed_case_count'] == report['required_case_count'] == 4
    assert len({(c['domain_id'], c['method_id']) for c in report['cases']}) == 4
    assert report['timing_scope']['explicit_cuda_synchronize_calls'] == 0
    assert report['scope']['F105_factory_or_checkpoint_validation_executed'] is False
    assert report['scope']['production_qualification'] is False
    assert report['scope']['speedup_claimed'] is False
    for case in report['cases']:
        assert case['unique_parameters_including_base'] == 297923
        assert case['passed'] and case['same_device_repeatability']['passed']
        assert set(case['comparison']['categories']) == set(q.TOLERANCES) | {'exact'}
        assert all(v['maximum_absolute_difference'] == 0. for v in case['comparison']['categories'].values())
    assert torch.equal(random_before, torch.random.get_rng_state())
    assert torch.get_num_threads() == threads
    assert torch.are_deterministic_algorithms_enabled() is deterministic
    assert torch.is_deterministic_algorithms_warn_only_enabled() is warn
    json.dumps(report, allow_nan=False)


def test_partial_roster_exception_returns_stop_and_restores_flags(monkeypatch):
    previous = torch.are_deterministic_algorithms_enabled()
    def broken(*args):
        raise RuntimeError('/secret/runtime/path must not be exported')
    monkeypatch.setattr(q, '_case', broken)
    report = q.run_qualification()
    assert report['decision'] == 'STOP_DEVICE_QUALIFICATION_INCOMPLETE'
    assert report['completed_case_count'] == 0 and report['required_case_count'] == 4
    assert '/secret' not in json.dumps(report)
    assert torch.are_deterministic_algorithms_enabled() is previous


def test_numeric_failure_does_not_drop_remaining_cases_or_return_pass(monkeypatch):
    calls = []
    def failure(domain, method, device, budget):
        calls.append((domain, method))
        return {'domain_id': domain, 'method_id': method, 'passed': False}
    monkeypatch.setattr(q, '_case', failure)
    report = q.run_qualification(iterations=2)
    assert report['decision'] == 'FAIL_DEVICE_PARITY'
    assert report['completed_case_count'] == report['required_case_count'] == len(calls) == 8


def test_soft_deadline_and_memory_checks_refuse_without_deleting_or_retrying(monkeypatch):
    request = q.DeviceQualificationRequest(maximum_seconds=5)
    budget = q._Budget(request)
    monkeypatch.setattr(q.time, 'perf_counter', lambda: budget.started+6)
    with pytest.raises(q.DeviceQualificationError, match='wall-clock'):
        budget.check()
    monkeypatch.setattr(q.time, 'perf_counter', lambda: budget.started)
    monkeypatch.setattr(q, '_rss', lambda: q.MAXIMUM_MEMORY_BYTES+1)
    with pytest.raises(q.DeviceQualificationError, match='RSS'):
        budget.check()


def test_cuda_build_failure_refuses_before_discovery_no_install_fallback(monkeypatch):
    monkeypatch.setattr(torch.version, 'cuda', None)
    def forbidden(*args, **kwargs):
        raise AssertionError('No CUDA discovery allowed for CPU-only build')
    monkeypatch.setattr(torch.cuda, 'is_available', forbidden)
    report = q.run_qualification(mode='CUDA', device='cuda:0')
    assert report['decision'] == 'STOP_DEVICE_QUALIFICATION_INCOMPLETE'
    assert report['cuda_execution'] == 'CUDA_REQUESTED'
    assert 'CUDA build required' in report['error_detail']
    assert report['completed_case_count'] == 0


def test_cuda_hidden_or_missing_cublas_policy_refuses_before_discovery(monkeypatch):
    monkeypatch.setattr(torch.version, 'cuda', 'synthetic-not-a-runtime')
    def forbidden(*args, **kwargs):
        raise AssertionError('No actual CUDA work authorized by unit test')
    monkeypatch.setattr(torch.cuda, 'is_available', forbidden)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    report = q.run_qualification(mode='CUDA', device='cuda:0')
    assert report['decision'] == 'STOP_DEVICE_QUALIFICATION_INCOMPLETE'
    assert 'visibility' in report['error_detail']
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '0')
    monkeypatch.delenv('CUBLAS_WORKSPACE_CONFIG', raising=False)
    report = q.run_qualification(mode='CUDA', device='cuda:0')
    assert 'CUBLAS_WORKSPACE_CONFIG' in report['error_detail']
