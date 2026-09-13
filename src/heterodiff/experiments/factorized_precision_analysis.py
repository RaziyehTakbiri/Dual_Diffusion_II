"""Fixed CPU-only precision experiment; prints bounded JSON, never writes files.

No CUDA query, cloud operation, package installation, real data or tuning search.
This compares arithmetic implementations on the existing four-case fixture.
Passing here never relabels legacy CPU/CUDA parity or GPU qualification.
"""
from dataclasses import replace
import json
import platform
import time

import torch

from heterodiff.experiments.factorized_base_precision import _precision_objective, PRECISION_POLICY
from heterodiff.experiments.factorized_device_qualification import (
    _fixture, _optimizer, _numerical_policy, DeviceQualificationRequest, TOLERANCES, FIXTURE_ID, POLICY_ID,
)
from heterodiff.experiments.factorized_device_training import device_base_objective_on_corrupted_states
from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy, device_configuration_batch


VARIANTS = ('legacy_fp32', 'functional_fp32', 'rowwise_fp32', 'shared_fp64',
            'rowwise_shared_fp64', 'separate_cast_fp64', 'replay_shared_fp64')
DOMAINS = ('R3-PHYS', 'R4-RETAIL')
METHODS = ('association-aware-guide-plus-residual', 'unified-direct-conditioner')


def _compare(a, b, kind):
    if a.keys() != b.keys():
        raise ValueError('precision comparison parameter roster mismatch')
    atol, rtol = TOLERANCES[kind]
    failures = count = 0
    maximum = 0.
    exact = True
    for name in a:
        left, right = a[name], b[name]
        if (left is None) != (right is None):
            raise ValueError('precision comparison gradient presence mismatch')
        if left is None:
            continue
        if left.shape != right.shape or not bool(torch.isfinite(left).all() & torch.isfinite(right).all()):
            raise ValueError('precision comparison shape/nonfinite failure')
        residual = (left.double() - right.double()).abs()
        count += residual.numel()
        failures += int((residual > atol + rtol * left.double().abs()).sum())
        maximum = max(maximum, float(residual.max()) if residual.numel() else 0.)
        exact = exact and torch.equal(left, right)
    return {'exact': exact, 'within_existing_tolerance': failures == 0,
            'failing_scalar_count': failures, 'scalar_count': count,
            'maximum_absolute_difference': maximum, 'atol': atol, 'rtol': rtol}


def _evaluate(domain, method, variant):
    base, _, joint, _, destinations, _ = _fixture(domain, method)
    model = DeviceFactorizedEnergy.from_cpu(base, 'cpu')
    times, cr, jr = (.625, .125, 0.), (1., 1., 0.), (2., 1., .5)
    if variant == 'legacy_fp32':
        objective = device_base_objective_on_corrupted_states(model, joint.states, destinations,
            times, torch.zeros(64, dtype=torch.float32, device='cpu'), cr, jr, jump_weight=1.)
    else:
        context = torch.zeros(3, 64, dtype=torch.float32, device='cpu')
        src = device_configuration_batch(joint.states, joint.reverse_times, context, model.architecture,
                                          device='cpu', coordinate_gradients=True)
        dst = device_configuration_batch(destinations, joint.reverse_times, context, model.architecture, device='cpu')
        t = torch.tensor(times, dtype=torch.float32, device='cpu')
        src, dst = replace(src, forward_time=t), replace(dst, forward_time=t)
        objective = _precision_objective(model, src, dst, cr, jr, 1.,
            dtype=torch.float32 if variant.endswith('fp32') else torch.float64,
            rowwise=variant.startswith('rowwise'), shared_parameters=variant != 'separate_cast_fp64')
    loss = {name: float(getattr(objective, name).detach()) for name in ('total', 'continuous', 'jump')}
    optimizer = _optimizer(model)
    objective.total.backward()
    gradients = {name: None if p.grad is None else p.grad.detach().clone() for name, p in model.named_parameters()}
    optimizer.step()
    parameters = {name: p.detach().clone() for name, p in model.named_parameters()}
    for p in model.parameters():
        if p.dtype != torch.float32 or p.device.type != 'cpu':
            raise ValueError('FP32 CPU parameter ownership changed')
        for name in ('exp_avg', 'exp_avg_sq'):
            value = optimizer.state.get(p, {}).get(name)
            if value is not None and (value.dtype != torch.float32 or value.device.type != 'cpu'):
                raise ValueError('FP32 CPU optimizer state changed')
    return loss, gradients, parameters


def run_local_precision_analysis():
    started, cases = time.perf_counter(), []
    def check_time():
        if time.perf_counter() - started > 120:
            raise TimeoutError('local precision experiment soft 120-second limit exceeded')
    with _numerical_policy(DeviceQualificationRequest()):
        for domain in DOMAINS:
            for method in METHODS:
                variants = {}
                for variant in VARIANTS:
                    check_time()
                    variants[variant] = _evaluate(domain, method, variant)
                    check_time()
                def compare(left, right):
                    a, b = variants[left], variants[right]
                    loss_a = {k: torch.tensor(v, dtype=torch.float64, device='cpu') for k, v in a[0].items()}
                    loss_b = {k: torch.tensor(v, dtype=torch.float64, device='cpu') for k, v in b[0].items()}
                    return {'losses': _compare(loss_a, loss_b, 'loss'),
                            'loss_maximum_absolute_difference': max(abs(a[0][k]-b[0][k]) for k in a[0]),
                            'gradients': _compare(a[1], b[1], 'parameter_gradient'),
                            'updated_parameters': _compare(a[2], b[2], 'updated_parameter')}
                comparisons = {
                    'legacy_vs_functional_fp32': compare('legacy_fp32', 'functional_fp32'),
                    'fp32_batched_vs_rowwise': compare('functional_fp32', 'rowwise_fp32'),
                    'shared_fp64_batched_vs_rowwise': compare('shared_fp64', 'rowwise_shared_fp64'),
                    'shared_fp64_exact_cpu_replay': compare('shared_fp64', 'replay_shared_fp64'),
                    'shared_fp64_vs_separate_cast_fp64': compare('shared_fp64', 'separate_cast_fp64'),
                    'legacy_fp32_vs_shared_fp64_NOT_legacy_GPU_parity': compare('legacy_fp32', 'shared_fp64'),
                }
                index = (93, 167) if domain == 'R3-PHYS' else (5, 64)
                sensitive = {'parameter': 'readout_hidden.weight', 'index': list(index),
                    'gradients': {variant: float(values[1]['readout_hidden.weight'][index])
                                  for variant, values in variants.items()}}
                checks = {
                    'fp32_control_exact': all(comparisons['legacy_vs_functional_fp32'][k]['exact']
                                              for k in ('gradients', 'updated_parameters'))
                        and comparisons['legacy_vs_functional_fp32']['loss_maximum_absolute_difference'] == 0.,
                    'shared_fp64_replay_exact': all(comparisons['shared_fp64_exact_cpu_replay'][k]['exact']
                                                    for k in ('gradients', 'updated_parameters'))
                        and comparisons['shared_fp64_exact_cpu_replay']['loss_maximum_absolute_difference'] == 0.,
                    'shared_fp64_cpu_layout_stress_pass': all(
                        comparisons['shared_fp64_batched_vs_rowwise'][k]['within_existing_tolerance']
                        for k in ('losses', 'gradients', 'updated_parameters')),
                }
                cases.append({'domain': domain, 'method': method, 'checks': checks,
                              'comparisons': comparisons, 'sensitive_coordinate': sensitive,
                              'losses': {k: v[0] for k, v in variants.items()}})
    passed = all(all(row['checks'].values()) for row in cases)
    check_time()
    return {'schema_version': 'factorized-base-local-precision-analysis-v1',
            'decision': 'PASS_LOCAL_PRECISION_CONTROLS_ONLY' if passed else 'FAIL_LOCAL_PRECISION_CONTROLS',
            'candidate_precision_policy': PRECISION_POLICY, 'fixture_id': FIXTURE_ID,
            'unchanged_tolerance_policy_id': POLICY_ID, 'variants': list(VARIANTS), 'cases': cases,
            'case_count': len(cases), 'synthetic_adamw_steps': len(cases) * len(VARIANTS),
            'elapsed_seconds_not_GPU_forecast': time.perf_counter() - started,
            'runtime': {'python': platform.python_version(), 'torch': str(torch.__version__),
                        'device': 'cpu', 'architecture': platform.machine(),
                        'operating_system': platform.system(), 'intraop_threads_during_run': 1,
                        'deterministic_algorithms_during_run': True},
            'scope': {'GPU_execution': False, 'CUDA_queried_explicitly': False,
                      'CPU_layout_stress_is_GPU_emulation': False,
                      'legacy_CPU_GPU_parity_closed': False, 'candidate_GPU_qualified': False,
                      'production_precision_policy_adopted': False, 'real_data_accessed': False,
                      'optimizer_or_scientific_objective_changed': False, 'tolerances_changed': False,
                      'default_precision_route_changed': False, 'files_written': False,
                      'paid_jobs_launched': False, 'packages_installed': False}}


if __name__ == '__main__':
    print(json.dumps(run_local_precision_analysis(), indent=2, sort_keys=True, allow_nan=False))
