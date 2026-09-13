"""Synthetic CPU tensor qualification; no CUDA tensor computation requested."""
import json
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

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


class _FakePrecisionOwner:
    """Wrong-family access is a test error, not a simulated compatibility path."""
    def __init__(self, allowed, **values):
        object.__setattr__(self, '_allowed', set(allowed))
        object.__setattr__(self, 'writes', [])
        for name, value in values.items():
            object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        if name in ('fp32_precision', 'allow_tf32') and name not in object.__getattribute__(self, '_allowed'):
            raise AssertionError('precision families were mixed on read: ' + name)
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name in ('fp32_precision', 'allow_tf32') and name not in self._allowed:
            raise AssertionError('precision families were mixed on write: ' + name)
        self.writes.append((name, value))
        object.__setattr__(self, name, value)


def _fake_torch(version, modern):
    attribute, initial = ('fp32_precision', 'tf32') if modern else ('allow_tf32', True)
    matmul = _FakePrecisionOwner((attribute,), **{attribute: initial})
    cudnn = _FakePrecisionOwner((attribute,), **{attribute: initial, 'benchmark': True})
    backends = _FakePrecisionOwner(('fp32_precision',) if modern else (),
        **({'fp32_precision': 'tf32'} if modern else {}))
    backends.cuda, backends.cudnn = SimpleNamespace(matmul=matmul), cudnn
    return SimpleNamespace(__version__=version, backends=backends)


@pytest.mark.parametrize('version,modern', [('2.7.0', False), ('2.8.1+cu128', False),
                                         ('2.9.0', True), ('2.12.1+cpu', True)])
def test_version_selected_precision_policy_uses_one_family_and_restores_every_flag(version, modern):
    fake = _fake_torch(version, modern)
    attribute, desired, initial = ('fp32_precision', 'ieee', 'tf32') if modern else ('allow_tf32', False, True)
    with q._cuda_precision_policy(fake, {}) as observed:
        expected_family = 'new_fp32_precision_only' if modern else 'legacy_allow_tf32_only'
        assert observed['family'] == expected_family
        assert observed['torch_version'] == version
        assert getattr(fake.backends.cuda.matmul, attribute) == desired
        assert getattr(fake.backends.cudnn, attribute) == desired
        assert fake.backends.cudnn.benchmark is False
        assert observed['settings']['cuda.matmul.'+attribute] == desired
        assert observed['settings']['cudnn.'+attribute] == desired
        assert observed['settings']['cudnn.benchmark'] is False
    assert getattr(fake.backends.cuda.matmul, attribute) == initial
    assert getattr(fake.backends.cudnn, attribute) == initial
    assert fake.backends.cudnn.benchmark is True
    if modern:
        assert fake.backends.fp32_precision == 'tf32'


@pytest.mark.parametrize('version', ['2.6.0', '1.13.1', '3.0.0', '2.7', '2.9.0rc1',
                                    '2.10.0.dev20260101', '2.9.0a0+gitabc', 'unknown', '2.07.0'])
def test_unsupported_or_ambiguous_versions_refuse_before_any_backend_access(version):
    fake = SimpleNamespace(__version__=version)
    with pytest.raises(q.DeviceQualificationError, match='stable Torch'):
        with q._cuda_precision_policy(fake, {}):
            raise AssertionError('Unsupported version entered precision context')


@pytest.mark.parametrize('name,value', [('TORCH_ALLOW_TF32_CUBLAS_OVERRIDE', '1'),
                                      ('TORCH_ALLOW_TF32_CUBLAS_OVERRIDE', ''),
                                      ('NVIDIA_TF32_OVERRIDE', '1'),
                                      ('NVIDIA_TF32_OVERRIDE', 'invalid')])
def test_forced_or_ambiguous_tf32_override_refuses_without_modifying_environment(name, value):
    environment = {name: value}
    with pytest.raises(q.DeviceQualificationError, match=name):
        with q._cuda_precision_policy(SimpleNamespace(__version__='2.7.0'), environment):
            raise AssertionError('Forced TF32 entered precision context')
    assert environment == {name: value}


@pytest.mark.parametrize('modern', [False, True])
def test_policy_restores_flags_when_body_raises_and_accepts_disabled_overrides(modern):
    fake = _fake_torch('2.9.0' if modern else '2.7.0', modern)
    environment = {'TORCH_ALLOW_TF32_CUBLAS_OVERRIDE': '0', 'NVIDIA_TF32_OVERRIDE': '0'}
    with pytest.raises(RuntimeError, match='synthetic body failure'):
        with q._cuda_precision_policy(fake, environment):
            raise RuntimeError('synthetic body failure')
    attribute, initial = ('fp32_precision', 'tf32') if modern else ('allow_tf32', True)
    assert getattr(fake.backends.cuda.matmul, attribute) == initial
    assert getattr(fake.backends.cudnn, attribute) == initial
    assert fake.backends.cudnn.benchmark is True
    assert environment == {'TORCH_ALLOW_TF32_CUBLAS_OVERRIDE': '0', 'NVIDIA_TF32_OVERRIDE': '0'}


def test_missing_modern_api_never_falls_back_to_legacy_and_restores_prior_changes():
    fake = _fake_torch('2.9.0', True)
    del fake.backends.cudnn.fp32_precision
    with pytest.raises(q.DeviceQualificationError, match='missing required cudnn.fp32_precision'):
        with q._cuda_precision_policy(fake, {}):
            raise AssertionError('Missing API entered context')
    assert fake.backends.fp32_precision == fake.backends.cuda.matmul.fp32_precision == 'tf32'
    assert fake.backends.cudnn.benchmark is True


def test_setting_failure_restores_all_previously_touched_legacy_flags():
    class FailingOwner(_FakePrecisionOwner):
        def __setattr__(self, name, value):
            if name == 'allow_tf32' and value is False:
                raise RuntimeError('synthetic setter failure')
            super().__setattr__(name, value)
    fake = _fake_torch('2.7.0', False)
    fake.backends.cudnn = FailingOwner(('allow_tf32',), allow_tf32=True, benchmark=True)
    with pytest.raises(RuntimeError, match='synthetic setter failure'):
        with q._cuda_precision_policy(fake, {}):
            raise AssertionError('Failed setter entered context')
    assert fake.backends.cuda.matmul.allow_tf32 is True
    assert fake.backends.cudnn.allow_tf32 is True
    assert fake.backends.cudnn.benchmark is True


def test_one_restore_failure_still_attempts_all_other_settings_and_cannot_pass():
    class RestoreFailure(_FakePrecisionOwner):
        def __setattr__(self, name, value):
            if name == 'fp32_precision' and value == 'tf32':
                raise RuntimeError('synthetic restoration failure')
            super().__setattr__(name, value)
    fake = _fake_torch('2.9.0', True)
    fake.backends.cudnn = RestoreFailure(('fp32_precision',), fp32_precision='tf32', benchmark=True)
    with pytest.raises(q.DeviceQualificationError, match='restoration failed'):
        with q._cuda_precision_policy(fake, {}):
            assert fake.backends.cudnn.fp32_precision == 'ieee'
    assert fake.backends.fp32_precision == fake.backends.cuda.matmul.fp32_precision == 'tf32'
    assert fake.backends.cudnn.benchmark is True


def _fake_cold_cuda_runtime(monkeypatch, *, fail_at=None):
    """Stateful API-order model only: no real CUDA module call or computation."""
    fake = _fake_torch('2.7.0+cu126', False)
    fake.version = SimpleNamespace(cuda='synthetic-12.6')
    state = {'initialized': False, 'reset': False, 'calls': [],
             'threads': 4, 'deterministic': False, 'warn_only': True}
    def operation(name):
        state['calls'].append(name)
        if name == fail_at:
            raise RuntimeError('synthetic ' + name + ' failure')
    def properties(device):
        assert device == 'cuda:0'
        operation('properties')
        state['initialized'] = True
        return SimpleNamespace(name='FAKE_GPU_NOT_HARDWARE', total_memory=123, major=8, minor=0)
    def reset(device):
        assert device == 'cuda:0'
        operation('reset')
        if not state['initialized']:
            raise RuntimeError('Invalid device argument 0: did you call init?')
        state['reset'] = True
    def available():
        operation('available')
        return True
    def count():
        operation('count')
        return 1
    def memory(device):
        assert device == 'cuda:0' and state['initialized']
        return 0
    fake.cuda = SimpleNamespace(is_available=available, device_count=count,
        get_device_properties=properties, reset_peak_memory_stats=reset,
        max_memory_allocated=memory, max_memory_reserved=memory)
    fake.get_num_threads = lambda: state['threads']
    fake.set_num_threads = lambda value: state.update(threads=value)
    fake.are_deterministic_algorithms_enabled = lambda: state['deterministic']
    fake.is_deterministic_algorithms_warn_only_enabled = lambda: state['warn_only']
    fake.use_deterministic_algorithms = lambda value, warn_only: state.update(
        deterministic=value, warn_only=warn_only)
    monkeypatch.setattr(q, 'torch', fake)
    monkeypatch.setenv('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    for name in ('CUDA_VISIBLE_DEVICES', 'TORCH_ALLOW_TF32_CUBLAS_OVERRIDE', 'NVIDIA_TF32_OVERRIDE'):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(q, '_rss', lambda: 0)
    return fake, state


def test_cold_cuda_properties_initialize_allocator_before_reset_and_cases(monkeypatch):
    fake, state = _fake_cold_cuda_runtime(monkeypatch)
    def case(domain, method, device, budget):
        assert state['initialized'] and state['reset']
        state['calls'].append('case')
        return {'domain_id': domain, 'method_id': method, 'passed': True}
    monkeypatch.setattr(q, '_case', case)
    report = q.run_qualification(mode='CUDA', device='cuda:0')
    assert state['calls'] == ['available', 'count', 'properties', 'reset'] + ['case']*4
    assert report['selected_device']['name'] == 'FAKE_GPU_NOT_HARDWARE'
    assert report['completed_case_count'] == 4
    assert report['execution_progress']['cuda_device_initialization_completed'] is True
    assert report['execution_progress']['cuda_peak_memory_reset_completed'] is True
    assert report['harness_revision'] == 'factorized-device-qualification-v2-initialization-order'
    assert (state['threads'], state['deterministic'], state['warn_only']) == (4, False, True)
    assert fake.backends.cuda.matmul.allow_tf32 is True
    assert fake.backends.cudnn.allow_tf32 is True
    assert fake.backends.cudnn.benchmark is True


@pytest.mark.parametrize('failure,stage,initialized', [
    ('available', 'CUDA_AVAILABILITY', False),
    ('count', 'CUDA_ORDINAL_CHECK', False),
    ('properties', 'CUDA_DEVICE_INITIALIZATION', False),
    ('reset', 'CUDA_PEAK_MEMORY_RESET', True),
])
def test_cuda_startup_error_keeps_stage_message_and_restores_flags(monkeypatch, failure, stage, initialized):
    fake, state = _fake_cold_cuda_runtime(monkeypatch, fail_at=failure)
    def forbidden(*args, **kwargs):
        raise AssertionError('case must not begin after startup failure')
    monkeypatch.setattr(q, '_case', forbidden)
    report = q.run_qualification(mode='CUDA', device='cuda:0')
    assert report['decision'] == 'STOP_DEVICE_QUALIFICATION_INCOMPLETE'
    assert report['completed_case_count'] == 0
    assert report['failed_stage'] == stage
    assert report['error_detail'] == 'synthetic ' + failure + ' failure'
    assert report['error_diagnostics']['frames'][-1]['function'] == 'operation'
    assert 'active_numerical_policy' not in report
    assert state['initialized'] is initialized and state['reset'] is False
    assert (state['threads'], state['deterministic'], state['warn_only']) == (4, False, True)
    assert fake.backends.cuda.matmul.allow_tf32 is True
    assert fake.backends.cudnn.allow_tf32 is True
    assert fake.backends.cudnn.benchmark is True


def test_bounded_diagnostics_retain_allocator_message_not_paths_locals_or_credentials():
    try:
        raise RuntimeError('Invalid device argument 0: did you call init? /secret/runtime/path '
                           'https://private.example/token password=private-value token=hidden-value\x1b[31m')
    except RuntimeError as error:
        diagnostics = q._error_diagnostics(error)
    serialized = json.dumps(diagnostics)
    assert 'did you call init?' in diagnostics['message']
    assert all(value not in serialized for value in ('/secret', 'private.example', 'private-value', 'hidden-value', '\\u001b'))
    assert diagnostics['frame_locals_or_source_text_included'] is False
    assert diagnostics['frames'][-1]['file'] == 'test_factorized_device_qualification.py'
    assert diagnostics['frames'][-1]['line'] > 0


def test_error_message_and_frame_list_are_bounded():
    def nested(depth):
        if depth:
            return nested(depth-1)
        raise RuntimeError('x'*3000)
    try:
        nested(12)
    except RuntimeError as error:
        diagnostics = q._error_diagnostics(error)
    assert len(diagnostics['message']) == 2048
    assert diagnostics['message_truncated'] is True
    assert len(diagnostics['frames']) == 8


@pytest.mark.parametrize('message', [
    'Authorization: Bearer EXAMPLE_TEST_ONLY',
    "password='EXAMPLE TEST ONLY'",
    'token="EXAMPLE TEST ONLY"',
])
def test_diagnostics_redact_authorization_and_quoted_credentials(message):
    diagnostics = q._error_diagnostics(RuntimeError(message))
    assert diagnostics['message'] == '<credential>'
    assert 'EXAMPLE' not in json.dumps(diagnostics)


def test_diagnostic_frame_strings_are_bounded_and_not_absolute_paths():
    def broken():
        raise RuntimeError('synthetic failure')
    broken.__code__ = broken.__code__.replace(co_filename='C:\\private\\'+'f'*300+'.py', co_name='n'*300)
    try:
        broken()
    except RuntimeError as error:
        diagnostics = q._error_diagnostics(error)
    frame = diagnostics['frames'][-1]
    assert frame['file'] == 'f'*160 and frame['function'] == 'n'*160
    assert 'private' not in json.dumps(diagnostics)


def test_deferred_cuda_initialization_exception_is_reported_with_stage(monkeypatch):
    fake, state = _fake_cold_cuda_runtime(monkeypatch)
    class FakeDeferredCudaCallError(Exception):
        pass
    def deferred(device):
        raise FakeDeferredCudaCallError('synthetic deferred CUDA initialization failure')
    fake.cuda.get_device_properties = deferred
    report = q.run_qualification(mode='CUDA', device='cuda:0')
    assert report['decision'] == 'STOP_DEVICE_QUALIFICATION_INCOMPLETE'
    assert report['failed_stage'] == 'CUDA_DEVICE_INITIALIZATION'
    assert report['error_type'] == 'FakeDeferredCudaCallError'
    assert report['completed_case_count'] == 0
    assert (state['threads'], state['deterministic'], state['warn_only']) == (4, False, True)


@pytest.mark.parametrize('error_type', [KeyboardInterrupt, SystemExit])
def test_interrupts_are_not_swallowed_by_failure_reporting(monkeypatch, error_type):
    def interrupted(*args, **kwargs):
        raise error_type('synthetic interruption')
    monkeypatch.setattr(q, '_case', interrupted)
    previous = torch.are_deterministic_algorithms_enabled()
    with pytest.raises(error_type):
        q.run_qualification()
    assert torch.are_deterministic_algorithms_enabled() is previous
