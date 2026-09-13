"""One bounded, synthetic BASE precision-candidate comparison, never remote work.

The candidate is compared to its own CPU implementation. Legacy FP32 controls
and candidate-versus-legacy drift remain visible; they are not relabelled PASS.
Four domain/method routing labels cover two unique BASE fixtures, not conditional
training, sampling, an installed release, or production qualification.
"""
import hashlib
import json
import time

import torch

from heterodiff.experiments.factorized_base_precision import (
    PRECISION_POLICY, _functional_energy, _promote_batch,
)
from heterodiff.experiments.factorized_device_qualification import (
    DeviceQualificationRequest, FIXTURE_ID, MAXIMUM_MEMORY_BYTES, POLICY_ID,
    TOLERANCES, _Budget, _compare, _coordinate_derivatives, _error_diagnostics,
    _fixture, _host_payload, _need, _numerical_policy, _optimizer,
    _optimizer_state, _rss, _store_parameters,
)
from heterodiff.experiments.factorized_base_training import base_objective_on_corrupted_states
from heterodiff.experiments.factorized_conditional_training import factorized_configuration_batch
from heterodiff.experiments.factorized_device_training import device_base_objective_on_corrupted_states
from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy, device_configuration_batch


DOMAINS = ('R3-PHYS', 'R4-RETAIL')
METHODS = ('association-aware-guide-plus-residual', 'unified-direct-conditioner')
CASE_ROSTER = tuple((domain, method) for domain in DOMAINS for method in METHODS)
ROLES = ('legacy_cpu', 'candidate_cpu', 'legacy_target', 'legacy_target_replay',
         'candidate_target', 'candidate_target_replay')
COMPARISONS = ('candidate_cpu_vs_target', 'candidate_target_exact_replay',
               'legacy_cpu_vs_target', 'legacy_target_exact_replay',
               'legacy_cpu_vs_candidate_cpu_drift')
MAXIMUM_REPORT_BYTES = 40960


def _owned(model, optimizer=None, *, gradients=False):
    parameters = tuple(model.parameters())
    _need(sum(p.numel() for p in parameters) == 96705, 'BASE parameter count changed')
    expected_device = parameters[0].device
    for p in parameters:
        _need(p.dtype == torch.float32 and p.device == expected_device
              and bool(torch.isfinite(p).all()), 'BASE parameter dtype/device/finite mismatch')
        if gradients:
            _need(p.grad is not None and p.grad.dtype == torch.float32
                  and p.grad.device == p.device and bool(torch.isfinite(p.grad).all()),
                  'BASE gradient missing or dtype/device/finite mismatch')
        if optimizer is not None:
            state = optimizer.state.get(p, {})
            _need(set(state) == {'step', 'exp_avg', 'exp_avg_sq'}, 'incomplete AdamW state')
            step = state['step']
            _need(step.numel() == 1 and float(step) == 1., 'AdamW did not take exactly one step')
            for name in ('exp_avg', 'exp_avg_sq'):
                value = state[name]
                _need(value.shape == p.shape and value.dtype == torch.float32
                      and value.device == p.device and bool(torch.isfinite(value).all()),
                      'AdamW moment dtype/device/shape/finite mismatch')


def _validate_payload(payload, names, coordinates, *, candidate):
    """Reject missing data even if both paired controls lose the same tensor."""
    expected = {'base/forward': 'forward'}
    for prefix, kind in (
        ('initial/base', 'exact'), ('base/forward_parameter_gradients', 'parameter_gradient'),
        ('base/objective_parameter_gradients', 'parameter_gradient'),
        ('base/updated_parameters', 'updated_parameter'),
    ):
        expected.update({prefix + '/' + name: kind for name in names})
    for name in names:
        for field in ('step', 'exp_avg', 'exp_avg_sq'):
            expected['base/optimizer/' + name + '/' + field] = (
                'exact' if field == 'step' else 'optimizer_moment')
    for ordinal, coordinate in enumerate(coordinates):
        if coordinate.numel() == 0:
            expected['base/coordinates/' + str(ordinal)] = 'exact'
        else:
            for field in ('gradient', 'hessian'):
                expected['base/coordinates/' + field + '/' + str(ordinal)] = 'coordinate_' + field
    expected.update({'base/loss/' + name: 'loss' for name in ('total', 'continuous', 'jump')})
    _need(payload.keys() == expected.keys(), 'BASE payload roster incomplete or unexpected')
    graph_dtype = torch.float64 if candidate else torch.float32
    for name, (kind, tensor) in payload.items():
        _need(kind == expected[name] and type(tensor) is torch.Tensor,
              'BASE payload missing tensor or wrong category')
        _need(bool(torch.isfinite(tensor).all()), 'BASE payload contains nonfinite tensor')
        if name == 'base/forward' or name.startswith('base/coordinates/'):
            _need(tensor.dtype == graph_dtype, 'BASE forward/coordinate graph precision mismatch')
        elif kind in ('parameter_gradient', 'updated_parameter', 'optimizer_moment') or name.startswith('initial/'):
            _need(tensor.dtype == torch.float32, 'BASE trainable/state precision changed')
        if name.startswith('base/loss/'):
            _need(tensor.numel() == 1 and tensor.dtype == torch.float64, 'BASE scalar objective precision changed')


def _exercise_base(domain, method, device, *, candidate, original_cpu, progress):
    base, _, joint, _, destinations, _ = _fixture(domain, method)
    if not original_cpu:
        base = DeviceFactorizedEnergy.from_cpu(base, device)
    _need(str(next(base.parameters()).device) == device, 'BASE requested device not owned')
    _owned(base)
    names = tuple(name for name, _ in base.named_parameters())
    result = {}
    _store_parameters(result, 'initial/base', base, 'exact')
    context = torch.zeros(3, 64, dtype=torch.float32, device=device)
    if original_cpu:
        _need(not candidate and device == 'cpu', 'invalid original CPU reference route')
        batch = factorized_configuration_batch(joint.states, joint.reverse_times, context,
                                              base.architecture, coordinate_gradients=True)
    else:
        batch = device_configuration_batch(joint.states, joint.reverse_times, context,
            base.architecture, device=device, coordinate_gradients=True)
    if candidate:
        batch = _promote_batch(batch, torch.float64)
        # This is the actual FP64 functional forward, not base(batch)'s FP32 graph.
        promoted = {name: p.to(torch.float64) for name, p in base.named_parameters()}
        values = _functional_energy(base.architecture, batch, promoted)
    else:
        values = base(batch)
    result['base/forward'] = ('forward', values.detach().clone())
    _coordinate_derivatives(result, 'base/coordinates', values, batch.coordinates)
    values.sum().backward()
    _owned(base, gradients=True)
    _store_parameters(result, 'base/forward_parameter_gradients', base, 'parameter_gradient', True)
    base.zero_grad(set_to_none=True)
    objective_fn = base_objective_on_corrupted_states if original_cpu else device_base_objective_on_corrupted_states
    kwargs = {} if original_cpu else {'precision_policy': PRECISION_POLICY if candidate else 'LEGACY_FP32'}
    objective = objective_fn(base, joint.states, destinations, (.625, .125, .0),
        torch.zeros(64, dtype=torch.float32, device=device), (1., 1., 0.), (2., 1., .5),
        jump_weight=1., **kwargs)
    for name in ('total', 'continuous', 'jump'):
        result['base/loss/' + name] = ('loss', getattr(objective, name).detach().clone())
    optimizer = _optimizer(base)
    objective.total.backward()
    _owned(base, gradients=True)
    _store_parameters(result, 'base/objective_parameter_gradients', base, 'parameter_gradient', True)
    progress['optimizer_steps_begun'] += 1
    progress['gpu_optimizer_steps_begun' if device.startswith('cuda:') else 'cpu_optimizer_steps_begun'] += 1
    optimizer.step()
    _owned(base, optimizer, gradients=True)
    _need(any(not torch.equal(result['initial/base/' + name][1], p.detach())
              for name, p in base.named_parameters()), 'BASE update changed no parameter')
    progress['optimizer_steps_completed'] += 1
    _store_parameters(result, 'base/updated_parameters', base, 'updated_parameter')
    _optimizer_state(result, 'base/optimizer', base, optimizer)
    _validate_payload(result, names, batch.coordinates, candidate=candidate)
    return _host_payload(result)


def _compact_comparison(left, right, *, exact=False, drift=False):
    if drift:
        # Lossless promotion is for this explicitly non-gating cross-policy report
        # only. Own-route payload dtype validation has already occurred.
        left = {k: (kind, value.double()) for k, (kind, value) in left.items()}
        right = {k: (kind, value.double()) for k, (kind, value) in right.items()}
    result = _compare(left, right, exact=exact)
    return {'passed': result['passed'], 'failure_count': result['failure_count'],
        'first_failure_names': result['failure_names'][:4],
        'all_tensor_names_sha256': result['all_tensor_names_sha256'],
        'categories': {name: {'passed': row['passed'], 'tensors': row['tensor_count'],
            'scalars': row['scalar_count'], 'max_abs': row['maximum_absolute_difference']}
            for name, row in result['categories'].items()}}


def _case(domain, method, device, budget, progress):
    payloads, timing = {}, {}
    for role in ROLES:
        progress.update(stage='BASE_ROUTE_EXECUTION', role=role)
        target = 'cpu' if role.endswith('_cpu') else device
        payloads[role], timing[role] = budget.timed(target, lambda: _exercise_base(
            domain, method, target, candidate=role.startswith('candidate'),
            original_cpu=role == 'legacy_cpu', progress=progress))
    initial = {k: v for k, v in payloads['legacy_cpu'].items() if k.startswith('initial/')}
    for payload in payloads.values():
        _need(_compare(initial, {k: v for k, v in payload.items() if k.startswith('initial/')},
                       exact=True)['passed'], 'fresh initial FP32 weights differ across routes')
    comparisons = {
        'candidate_cpu_vs_target': _compact_comparison(payloads['candidate_cpu'], payloads['candidate_target']),
        'candidate_target_exact_replay': _compact_comparison(payloads['candidate_target'], payloads['candidate_target_replay'], exact=True),
        'legacy_cpu_vs_target': _compact_comparison(payloads['legacy_cpu'], payloads['legacy_target']),
        'legacy_target_exact_replay': _compact_comparison(payloads['legacy_target'], payloads['legacy_target_replay'], exact=True),
        'legacy_cpu_vs_candidate_cpu_drift': _compact_comparison(payloads['legacy_cpu'], payloads['candidate_cpu'], drift=True),
    }
    budget.check()
    return {'domain_id': domain, 'method_id': method, 'completed_base_steps': 6,
            'initial_weights_exact_across_all_six_routes': True,
            'comparisons': comparisons, 'timing_seconds_including_fixture_copy_and_readback': timing}


def _decision(cases, mode):
    _need(tuple((x['domain_id'], x['method_id']) for x in cases) == CASE_ROSTER,
          'incomplete or changed four-case roster')
    for case in cases:
        _need(case['completed_base_steps'] == 6 and case['initial_weights_exact_across_all_six_routes'],
              'incomplete BASE routes or changed initial weights')
        _need(set(case['comparisons']) == set(COMPARISONS), 'missing comparison control')
        _need(case['comparisons']['legacy_target_exact_replay']['passed'],
              'legacy control replay is not exact; qualification incomplete')
    passed = all(case['comparisons'][name]['passed'] for case in cases
                 for name in ('candidate_cpu_vs_target', 'candidate_target_exact_replay'))
    if not passed:
        return 'FAIL_BASE_PRECISION_CANDIDATE'
    return ('PASS_CPU_BASE_PRECISION_CONTROLS_CUDA_NOT_EXECUTED' if mode == 'CPU_REFERENCE'
            else 'PASS_SELECTED_CUDA_BASE_PRECISION_CANDIDATE_ONLY')


def run_precision_candidate_check(*, mode='CPU_REFERENCE', device='cpu', maximum_seconds=120):
    """Exactly 24 BASE steps; pair with the notebook's 120s child supervisor.

Time and 2GiB memory checks here are soft/observational, not hard quotas.
There is no tolerance override, iteration search, retry, or policy selection.
"""
    _need(type(maximum_seconds) is int and maximum_seconds == 120, 'fixed 120-second bound required')
    request = DeviceQualificationRequest(mode=mode, device=device, iterations=1, maximum_seconds=120)
    budget = _Budget(request)
    progress = {'stage': 'START', 'optimizer_steps_begun': 0, 'optimizer_steps_completed': 0,
                'gpu_optimizer_steps_begun': 0, 'cpu_optimizer_steps_begun': 0}
    report = {'schema_version': 'factorized-base-precision-candidate-check-v1',
        'precision_policy': PRECISION_POLICY, 'tolerance_policy_id': POLICY_ID,
        'acceptance_tolerances_unchanged': TOLERANCES, 'fixture_id': FIXTURE_ID,
        'mode': mode, 'device': device, 'torch_version': str(torch.__version__),
        'cuda_build_version': torch.version.cuda, 'cases': [], 'execution_progress': progress,
        'bounds': {'required_cases': 4, 'unique_base_fixtures': 2, 'base_steps': 24,
            'gpu_steps': 16 if mode == 'CUDA' else 0, 'cpu_steps': 8 if mode == 'CUDA' else 24,
            'iterations': 1, 'warmups': 0, 'retries': 0, 'maximum_seconds_soft': 120,
            'maximum_memory_bytes_soft': MAXIMUM_MEMORY_BYTES,
            'hard_child_deadline_requires_notebook_supervisor': True},
        'scope': {'synthetic_only': True, 'source_only_not_installed_release': True,
            'base_only': True, 'method_specific_conditional_computation_executed': False,
            'conditional_training_or_sampling_executed': False, 'F105_executed': False,
            'real_data_accessed': False, 'files_written': False, 'packages_installed': False,
            'cloud_or_paid_jobs_launched': False, 'production_qualification': False,
            'old_legacy_parity_relabelled': False, 'speedup_claimed': False,
            'all_gpu_pipeline_claimed': False,
            'host_work': ['exact metadata and ordering', 'FP64 objective reduction', 'scalar control and validation'],
            'CPU_REFERENCE_explicit_CUDA_discovery_or_allocation_requested': False,
            'CPU_REFERENCE_library_internal_availability_probes_possible': True},
        'comparison_policy': {'candidate_reference': 'SHARED_FP64_CPU_NOT_LEGACY_FP32',
            'legacy_numeric_disagreement_is_gating': False,
            'legacy_control_completeness_finiteness_and_exact_replay_are_gating': True,
            'drift_comparison_uses_lossless_fp64_promotion_only': True,
            'candidate_and_legacy_own_route_dtypes_checked': True,
            'trainable_parameters_gradients_and_adamw_moments': 'FP32',
            'candidate_forward_and_coordinate_derivatives': 'FP64',
            'adamw_factory_unchanged': True}}
    try:
        with _numerical_policy(request, progress=progress) as policy:
            report['numerical_policy'] = {'deterministic_algorithms': True,
                'intraop_threads': 1, 'autocast_used': False,
                'cuda_precision_family': policy['family'], 'cuda_precision_settings': policy['settings']}
            if mode == 'CUDA':
                properties = policy['device_properties']
                report['selected_gpu'] = {'name': properties.name, 'total_memory_bytes': properties.total_memory,
                    'compute_capability': [properties.major, properties.minor]}
            for domain, method in CASE_ROSTER:
                progress.update(domain_id=domain, method_id=method)
                budget.check()
                report['cases'].append(_case(domain, method, device, budget, progress))
            _need(progress['optimizer_steps_completed'] == 24, 'BASE step count incomplete')
            _need(progress['optimizer_steps_begun'] == 24
                  and progress['gpu_optimizer_steps_begun'] == (16 if mode == 'CUDA' else 0)
                  and progress['cpu_optimizer_steps_begun'] == (8 if mode == 'CUDA' else 24),
                  'BASE CPU/GPU step split changed')
            budget.check()
            report['decision'] = _decision(report['cases'], mode)
            if mode == 'CUDA':
                report['cuda_memory'] = {'peak_allocated_bytes': torch.cuda.max_memory_allocated(device),
                                        'peak_reserved_bytes': torch.cuda.max_memory_reserved(device)}
        progress['stage'] = 'COMPLETE'
    except Exception as error:
        report['decision'] = 'STOP_BASE_PRECISION_CHECK_INCOMPLETE'
        report['error_type'] = type(error).__name__
        report['error_diagnostics'] = _error_diagnostics(error)
    report['completed_case_count'] = len(report['cases'])
    report['elapsed_seconds'] = time.perf_counter() - budget.started
    report['process_lifetime_peak_rss_bytes'] = _rss()
    report['explicit_cuda_synchronize_calls'] = budget.explicit_synchronizations
    report['timing_scope'] = 'SYNCHRONIZED_WALL_INCLUDING_HOST_WORK_COPY_READBACK_AND_FIRST_USE_NOT_KERNEL_ONLY'
    report['tolerance_values_sha256'] = hashlib.sha256(json.dumps(TOLERANCES, sort_keys=True).encode()).hexdigest()
    _need(len(json.dumps(report, allow_nan=False).encode()) <= MAXIMUM_REPORT_BYTES,
          'compact report bound exceeded')
    return report
