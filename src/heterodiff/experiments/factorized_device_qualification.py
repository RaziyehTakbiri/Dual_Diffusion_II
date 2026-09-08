"""Fixed, bounded synthetic CPU/device parity; never launches remote work.

This module imports Torch. The notebook's INSPECT mode must not import it.
CPU_REFERENCE requests only CPU tensor computation; ordinary Torch AdamW may
internally probe accelerator availability. The harness does not explicitly
discover/synchronize CUDA in that mode. CUDA requires an explicit
ordinal and preconfigured deterministic runtime; no environment is repaired.
"""

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import os
import re
import resource
import sys
import time

import torch


POLICY_ID = 'factorized-device-parity-fixed-tolerances-v1'
FIXTURE_ID = 'factorized-device-four-cases-synthetic-v1'
# Prospective numerical policy, frozen before any CUDA result. No caller override.
TOLERANCES = {
    'forward': (2e-6, 2e-5),
    'coordinate_gradient': (2e-5, 2e-4),
    'coordinate_hessian': (1e-4, 1e-3),
    'parameter_gradient': (2e-5, 2e-4),
    'loss': (2e-6, 2e-5),
    'updated_parameter': (2e-6, 2e-5),
    'optimizer_moment': (2e-6, 2e-4),
    'physical': (2e-5, 2e-4),
}
MAXIMUM_MEMORY_BYTES = 2 * 1024**3


class DeviceQualificationError(ValueError):
    pass


def _need(condition, detail):
    if not condition:
        raise DeviceQualificationError(detail)


@dataclass(frozen=True)
class DeviceQualificationRequest:
    mode: str = 'CPU_REFERENCE'
    device: str = 'cpu'
    iterations: int = 1
    maximum_seconds: int = 120

    def __post_init__(self):
        _need(self.mode in ('CPU_REFERENCE', 'CUDA'), 'explicit CPU_REFERENCE or CUDA mode required')
        _need(type(self.device) is str and (
            self.device == 'cpu' if self.mode == 'CPU_REFERENCE' else
            re.fullmatch(r'cuda:(0|[1-9][0-9]*)', self.device) is not None),
            'mode and explicit device must agree')
        _need(type(self.iterations) is int and 1 <= self.iterations <= 3, 'iterations must be 1..3')
        _need(type(self.maximum_seconds) is int and 5 <= self.maximum_seconds <= 300,
              'maximum_seconds must be 5..300')


def _rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == 'darwin' else value * 1024)


class _Budget:
    def __init__(self, request):
        self.request, self.started = request, time.perf_counter()
        self.explicit_synchronizations = 0

    def sync(self, device):
        if device.startswith('cuda:'):
            torch.cuda.synchronize(torch.device(device))
            self.explicit_synchronizations += 1

    def check(self):
        _need(time.perf_counter() - self.started <= self.request.maximum_seconds,
              'soft wall-clock bound exceeded; no partial qualification')
        _need(_rss() <= MAXIMUM_MEMORY_BYTES, 'process peak RSS exceeded fixed memory bound')
        if self.request.mode == 'CUDA':
            _need(torch.cuda.max_memory_reserved(self.request.device) <= MAXIMUM_MEMORY_BYTES,
                  'CUDA reserved memory exceeded fixed bound')

    def timed(self, device, function):
        self.check()
        self.sync(device)
        started = time.perf_counter()
        result = function()
        self.sync(device)
        elapsed = time.perf_counter() - started
        self.check()
        return result, elapsed


def _cuda_precision_family(version):
    version = str(version)
    match = re.fullmatch(r'2\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:\+[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*)?', version)
    _need(match is not None and int(match.group(1)) >= 7,
          'supported stable Torch 2.7+ version required; ambiguous/prerelease version refused')
    return 'legacy_allow_tf32_only' if int(match.group(1)) <= 8 else 'new_fp32_precision_only'


@contextmanager
def _cuda_precision_policy(torch_api, environment):
    """Version-selected documented FP32 family, with no cross-family fallback.

    Torch 2.7/2.8 uses allow_tf32; stable 2.9+ within major 2 uses
    fp32_precision. Fake backend objects exercise this policy without CUDA.
    """
    version = str(torch_api.__version__)
    family = _cuda_precision_family(version)
    # These overrides can defeat or ambiguously change the selected policy.
    # Do not mutate inherited environment to make a failing check pass.
    for name in ('TORCH_ALLOW_TF32_CUBLAS_OVERRIDE', 'NVIDIA_TF32_OVERRIDE'):
        _need(environment.get(name) in (None, '0'),
              name + ' must be absent or 0 for the fixed IEEE policy')
    backends = torch_api.backends
    saved = []
    settings = {}
    def set_and_check(owner, attribute, value, label):
        _need(hasattr(owner, attribute), family + ' missing required ' + label)
        previous = getattr(owner, attribute)
        _need(type(previous) is type(value), family + ' ambiguous existing ' + label)
        saved.append((owner, attribute, previous))
        setattr(owner, attribute, value)
        _need(getattr(owner, attribute) == value, family + ' setting did not take effect: ' + label)
        settings[label] = value
    try:
        if family == 'legacy_allow_tf32_only':
            set_and_check(backends.cuda.matmul, 'allow_tf32', False, 'cuda.matmul.allow_tf32')
            set_and_check(backends.cudnn, 'allow_tf32', False, 'cudnn.allow_tf32')
        else:
            set_and_check(backends, 'fp32_precision', 'ieee', 'global.fp32_precision')
            set_and_check(backends.cuda.matmul, 'fp32_precision', 'ieee', 'cuda.matmul.fp32_precision')
            set_and_check(backends.cudnn, 'fp32_precision', 'ieee', 'cudnn.fp32_precision')
        set_and_check(backends.cudnn, 'benchmark', False, 'cudnn.benchmark')
        yield {'family': family, 'torch_version': version, 'settings': settings,
               'TF32_environment_overrides_absent_or_disabled': True}
    finally:
        failures = []
        for owner, attribute, previous in reversed(saved):
            try:
                setattr(owner, attribute, previous)
                if getattr(owner, attribute) != previous:
                    failures.append(attribute)
            except (AttributeError, TypeError, ValueError, RuntimeError):
                failures.append(attribute)
        _need(not failures, 'FP32 policy restoration failed: ' + ','.join(failures))


@contextmanager
def _numerical_policy(request):
    """Restore flags; never mix the legacy and new TF32 control families."""
    saved_threads = torch.get_num_threads()
    saved_deterministic = torch.are_deterministic_algorithms_enabled()
    saved_warn = torch.is_deterministic_algorithms_warn_only_enabled()
    try:
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True, warn_only=False)
        with ExitStack() as stack:
            precision = {'family': 'NOT_ACCESSED', 'settings': {}}
            if request.mode == 'CUDA':
                _need(torch.version.cuda is not None, 'CUDA build required; no install attempted')
                _need(os.environ.get('CUDA_VISIBLE_DEVICES') not in ('', '-1'),
                      'CUDA visibility is disabled; not changed by qualification')
                _need(os.environ.get('CUBLAS_WORKSPACE_CONFIG') in (':4096:8', ':16:8'),
                      'deterministic CUBLAS_WORKSPACE_CONFIG required before launch')
                precision = stack.enter_context(_cuda_precision_policy(torch, os.environ))
                _need(torch.cuda.is_available(), 'selected CUDA runtime unavailable')
                ordinal = int(request.device.split(':')[1])
                _need(ordinal < torch.cuda.device_count(), 'selected CUDA ordinal unavailable')
                torch.cuda.reset_peak_memory_stats(request.device)
            yield precision
    finally:
        torch.use_deterministic_algorithms(saved_deterministic, warn_only=saved_warn)
        torch.set_num_threads(saved_threads)


def _fixture(domain, method):
    from heterodiff.data.two_domain_factorized_state import (
        FactoredEvent, FactorizedMetadataReference, PhysioStateKey, RetailStateKey,
        TrainInformedMetadataReference,
    )
    from heterodiff.evaluation.two_domain_count_normalized_event_cks import PHYSIONET_DOMAIN_ID
    from heterodiff.experiments.factorized_conditional_training import (
        FactorizedConditionalModel, FactorizedObservation, FactorizedTrainingBatch,
    )
    from heterodiff.models.factorized_configuration_energy_torch import (
        BoundedFactorizedConfigurationEnergy, FactorizedEnergyArchitecture, FactorizedEnergyLimits,
    )
    from heterodiff.processes.factorized_hybrid_sampler import FactorizedSchedule, canonical
    from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide
    from heterodiff.theory.factorized_smooth_amendment import AmendmentParameters, FactorizedSmoothOracle
    if domain == PHYSIONET_DOMAIN_ID:
        atomic = FactoredEvent(PhysioStateKey(7, 'GCS', 'ATOMIC', Fraction(4)))
        continuous = FactoredEvent(PhysioStateKey(7, 'HR', 'POSITIVE'), .25)
    else:
        def key(branch):
            return RetailStateKey('C000007', 'code', '', -2, (2010, 1, 1, 0, 0, 0, 0), None, branch)
        atomic, continuous = FactoredEvent(key('ZERO')), FactoredEvent(key('NEGATIVE'), .25)
    state = canonical((atomic, continuous, continuous))  # Duplicate occurrences are retained.
    reference = TrainInformedMetadataReference(FactorizedMetadataReference(domain), state, beta=Fraction(1, 4))
    parameters = AmendmentParameters(.5, 4, 4, .25, .01, .25, .1, .25)
    guide = FactorizedAssociationGuide(FactorizedSmoothOracle(reference, parameters))
    schedule = FactorizedSchedule(1.0, .125, 1.0, 1.0)
    architecture = FactorizedEnergyArchitecture('SYNTHETIC_DEVICE_QUALIFICATION:' + domain,
        4, 1.0, 2.0, 1.0, 1.0, FactorizedEnergyLimits(4, 16, 2048, 32768))
    base = BoundedFactorizedConfigurationEnergy(architecture, initialization_seed=11)
    conditioner = BoundedFactorizedConfigurationEnergy(architecture, initialization_seed=12)
    model = FactorizedConditionalModel(conditioner, guide=guide, method_id=method, clean_hold=.125,
        remaining_clocks=schedule.remaining_clocks, observation_seed=13, nuisance_seed=14)
    def observation(value):
        return FactorizedObservation(value, domain, 'SYNTHETIC-parity', b'fixed-visible-context')
    # Full-interval coverage includes active, clean-hold endpoint and terminal rows.
    states, times = (state, (atomic,), ()), (.375, .875, 1.0)
    joint = FactorizedTrainingBatch(states, times, (observation(state), observation(()), observation(None)), FIXTURE_ID)
    product = FactorizedTrainingBatch(states, times, (observation(()), observation(None), observation(state)), FIXTURE_ID)
    return base, model, joint, product, ((), state, (atomic,)), schedule


def _optimizer(model):
    return torch.optim.AdamW(model.parameters(), lr=.001, betas=(.9, .999), eps=1e-8,
        weight_decay=0.0, foreach=False, fused=False, amsgrad=False, maximize=False,
        capturable=False, differentiable=False)


def _store_parameters(result, prefix, model, kind, gradient=False):
    for name, parameter in model.named_parameters():
        value = parameter.grad if gradient else parameter
        if value is not None:
            _need(value.device == parameter.device, 'parameter or gradient device mismatch')
        result[prefix + '/' + name] = (kind, None if value is None else value.detach().clone())


def _optimizer_state(result, prefix, model, optimizer):
    for name, parameter in model.named_parameters():
        state = optimizer.state.get(parameter, {})
        _need(set(state) in (set(), {'step', 'exp_avg', 'exp_avg_sq'}), 'unexpected AdamW state roster')
        for field in ('step', 'exp_avg', 'exp_avg_sq'):
            value = state.get(field)
            if value is not None and field != 'step':
                _need(value.device == parameter.device, 'AdamW moment device mismatch')
            result[prefix + '/' + name + '/' + field] = (
                'exact' if field == 'step' else 'optimizer_moment',
                None if value is None else value.detach().clone())


def _coordinate_derivatives(result, prefix, values, coordinates):
    for ordinal, coordinate in enumerate(coordinates):
        if coordinate.numel() == 0:
            result[prefix + '/' + str(ordinal)] = ('exact', coordinate.detach().clone())
            continue
        grad = torch.autograd.grad(values.sum(), coordinate, retain_graph=True, create_graph=True)[0]
        second = torch.autograd.grad(grad.sum(), coordinate, retain_graph=True)[0]
        result[prefix + '/gradient/' + str(ordinal)] = ('coordinate_gradient', grad.detach().clone())
        result[prefix + '/hessian/' + str(ordinal)] = ('coordinate_hessian', second.detach().clone())


def _exercise(base, model, joint, product, destinations, *, device_path):
    from heterodiff.experiments.factorized_conditional_training import factorized_configuration_batch
    from heterodiff.experiments.factorized_base_training import base_objective_on_corrupted_states
    from heterodiff.models.factorized_device_energy_torch import device_configuration_batch
    from heterodiff.experiments.factorized_device_training import device_base_objective_on_corrupted_states
    device = str(base.device) if device_path else 'cpu'
    results = {}
    _store_parameters(results, 'initial/base', base, 'exact')
    _store_parameters(results, 'initial/conditional', model, 'exact')
    context = torch.zeros(3, 64, dtype=torch.float32, device=device)
    builder = device_configuration_batch if device_path else factorized_configuration_batch
    kwargs = {'device': device} if device_path else {}
    batch = builder(joint.states, joint.reverse_times, context, base.architecture,
                    coordinate_gradients=True, **kwargs)
    values = base(batch)
    results['base/forward'] = ('forward', values.detach().clone())
    _coordinate_derivatives(results, 'base/coordinates', values, batch.coordinates)
    values.sum().backward()
    _store_parameters(results, 'base/forward_parameter_gradients', base, 'parameter_gradient', True)
    base.zero_grad(set_to_none=True)
    objective_fn = device_base_objective_on_corrupted_states if device_path else base_objective_on_corrupted_states
    objective = objective_fn(base, joint.states, destinations, (.625, .125, .0),
        torch.zeros(64, dtype=torch.float32, device=device), (1.0, 1.0, 0.0), (2.0, 1.0, .5), jump_weight=1.0)
    for name in ('total', 'continuous', 'jump'):
        results['base/loss/' + name] = ('loss', getattr(objective, name).detach().clone())
    base_optimizer = _optimizer(base)
    objective.total.backward()
    _store_parameters(results, 'base/objective_parameter_gradients', base, 'parameter_gradient', True)
    base_optimizer.step()
    _need(any(not torch.equal(results['initial/base/' + name][1], parameter.detach())
              for name, parameter in base.named_parameters()), 'BASE AdamW step changed no parameters')
    _store_parameters(results, 'base/updated_parameters', base, 'updated_parameter')
    _optimizer_state(results, 'base/optimizer', base, base_optimizer)
    # Conditional coordinate Hessian includes FP64 guide and observation-conditioned NN.
    coordinates = tuple(torch.tensor([] if event.coordinate is None else [event.coordinate],
        dtype=torch.float64, device='cpu', requires_grad=True) for state in joint.states for event in state)
    conditional = (model.baseline(joint.states, joint.reverse_times, joint.observations, coordinates=coordinates)
                   + model.residual(joint.states, joint.reverse_times, joint.observations, coordinates=coordinates))
    results['conditional/physical_tilt'] = ('forward', conditional.detach().clone())
    _coordinate_derivatives(results, 'conditional/coordinates', conditional, coordinates)
    results['conditional/observation_encoder'] = ('forward', model.encoder(joint.observations).detach().clone())
    results['conditional/nuisance'] = ('forward', model.nuisance(joint.observations).detach().clone())
    results['conditional/joint_logits'] = ('forward', model.logits(joint).detach().clone())
    results['conditional/product_logits'] = ('forward', model.logits(product).detach().clone())
    risk = model.paired_loss(joint, product)
    results['conditional/loss'] = ('loss', risk.detach().clone())
    conditional_optimizer = _optimizer(model)
    risk.backward()
    _store_parameters(results, 'conditional/parameter_gradients', model, 'parameter_gradient', True)
    conditional_optimizer.step()
    for component in ('conditioner.', 'encoder.', 'nuisance.'):
        _need(any(not torch.equal(results['initial/conditional/' + name][1], parameter.detach())
                  for name, parameter in model.named_parameters() if name.startswith(component)),
              'conditional AdamW step did not update ' + component)
    _store_parameters(results, 'conditional/updated_parameters', model, 'updated_parameter')
    _optimizer_state(results, 'conditional/optimizer', model, conditional_optimizer)
    return results


def _physical(base, model, observation, state, *, device_path):
    from heterodiff.experiments.factorized_conditional_training import FactorizedPhysicalPotential
    from heterodiff.experiments.factorized_device_training import DeviceFactorizedPhysicalPotential
    from heterodiff.processes.factorized_hybrid_sampler import heun_step
    cls = DeviceFactorizedPhysicalPotential if device_path else FactorizedPhysicalPotential
    potential = cls(base, base_context=(0.0,)*64, conditional_model=model, observation=observation, clean_hold=.125)
    result = {}
    for u in (.375, .875, 1.0):
        value, gradients = potential.value_grad(u, state)
        result['physical/value/' + u.hex()] = ('physical', torch.tensor(value, dtype=torch.float64, device='cpu'))
        result['physical/gradients/' + u.hex()] = ('physical', torch.tensor(
            [x for row in gradients for x in row], dtype=torch.float64, device='cpu'))
        _need(value == potential.value(u, state), 'physical scalar and value_grad value differ')
    path = heun_step(state, .375, .0625, potential, 1.0,
                     tuple((.01,) if e.key.dimension else () for e in state))
    _need(tuple(e.key.canonical_bytes() for e in path) == tuple(e.key.canonical_bytes() for e in state),
          'Heun changed exact metadata roster')
    result['physical/heun_coordinates'] = ('physical', torch.tensor(
        [e.coordinate for e in path if e.coordinate is not None], dtype=torch.float64, device='cpu'))
    result['physical/initial_residual'] = ('physical', torch.tensor(
        potential.initialization_residual_log_tilt(state), dtype=torch.float64, device='cpu'))
    return result


def _host_payload(payload):
    return {key: (kind, None if value is None else value.detach().to('cpu').contiguous())
            for key, (kind, value) in payload.items()}


def _compare(reference, observed, *, exact=False):
    _need(reference.keys() == observed.keys(), 'comparison tensor roster mismatch')
    summary = {}
    failures = []
    for name in reference:
        kind, left = reference[name]
        right_kind, right = observed[name]
        _need(kind == right_kind, 'comparison category changed')
        if left is None or right is None:
            if left is not right:
                failures.append(name + ': gradient/state presence mismatch')
            continue
        _need(left.shape == right.shape and left.dtype == right.dtype, 'comparison shape/dtype mismatch')
        _need(bool(torch.isfinite(left).all()) and bool(torch.isfinite(right).all()), 'nonfinite comparison tensor')
        atol, rtol = (0.0, 0.0) if exact or kind == 'exact' else TOLERANCES[kind]
        difference = (left.double() - right.double()).abs()
        maximum = float(difference.max()) if difference.numel() else 0.0
        relative = difference / left.double().abs().clamp(min=1e-30)
        maximum_relative = float(relative.max()) if relative.numel() else 0.0
        passed = bool((difference <= atol + rtol*left.double().abs()).all())
        entry = summary.setdefault(kind, {'tensor_count': 0, 'scalar_count': 0,
            'maximum_absolute_difference': 0.0, 'maximum_relative_difference': 0.0,
            'absolute_tolerance': atol, 'relative_tolerance': rtol, 'passed': True})
        entry['tensor_count'] += 1
        entry['scalar_count'] += left.numel()
        entry['maximum_absolute_difference'] = max(entry['maximum_absolute_difference'], maximum)
        entry['maximum_relative_difference'] = max(entry['maximum_relative_difference'], maximum_relative)
        entry['passed'] &= passed
        if not passed:
            failures.append(name)
    return {'passed': not failures, 'categories': summary, 'failure_names': failures[:32],
            'failure_count': len(failures), 'all_tensor_names_sha256': hashlib.sha256(
                '\n'.join(reference).encode('utf-8')).hexdigest()}


def _case(domain, method, device, budget):
    from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy
    from heterodiff.experiments.factorized_device_training import DeviceFactorizedConditionalModel
    base, model, joint, product, destinations, _ = _fixture(domain, method)
    named = tuple(base.parameters()) + tuple(model.parameters())
    _need(len({p.data_ptr() for p in named}) == len(named), 'unexpected shared parameter storage')
    parameter_count = sum(p.numel() for p in named)
    _need(parameter_count == 297923, 'prototype architecture parameter count changed')
    def transfer():
        return DeviceFactorizedEnergy.from_cpu(base, device), DeviceFactorizedConditionalModel.from_cpu(model, device)
    (target_base, target_model), transfer_seconds = budget.timed(device, transfer)
    # The target is snapshotted before any CPU optimizer mutation.
    source, cpu_seconds = budget.timed('cpu', lambda: _exercise(base, model, joint, product, destinations, device_path=False))
    target, target_seconds = budget.timed(device, lambda: _exercise(target_base, target_model, joint, product, destinations, device_path=True))
    physical_cpu, physical_cpu_seconds = budget.timed('cpu', lambda: _physical(base, model, joint.observations[0], joint.states[0], device_path=False))
    physical_target, physical_target_seconds = budget.timed(device, lambda: _physical(target_base, target_model, joint.observations[0], joint.states[0], device_path=True))
    source.update(physical_cpu)
    target.update(physical_target)
    host_target, readback_seconds = budget.timed(device, lambda: _host_payload(target))
    comparison = _compare(_host_payload(source), host_target)
    # A mandatory independent reconstruction/replay, not an optional warmup.
    replay_base, replay_model, replay_joint, replay_product, replay_destinations, _ = _fixture(domain, method)
    replay_base = DeviceFactorizedEnergy.from_cpu(replay_base, device)
    replay_model = DeviceFactorizedConditionalModel.from_cpu(replay_model, device)
    replay, replay_seconds = budget.timed(device, lambda: _exercise(
        replay_base, replay_model, replay_joint, replay_product, replay_destinations, device_path=True))
    replay_physical, _ = budget.timed(device, lambda: _physical(replay_base, replay_model,
        replay_joint.observations[0], replay_joint.states[0], device_path=True))
    replay.update(replay_physical)
    repeatability = _compare(host_target, _host_payload(replay), exact=True)
    return {'domain_id': domain, 'method_id': method, 'passed': comparison['passed'] and repeatability['passed'],
        'comparison': comparison, 'same_device_repeatability': repeatability,
        'unique_parameters_including_base': parameter_count,
        'timing_seconds': {'initial_model_transfer_and_copy': transfer_seconds,
            'cpu_reference_graph_and_updates': cpu_seconds, 'target_graph_and_updates': target_seconds,
            'cpu_physical_heun_seam': physical_cpu_seconds, 'target_physical_heun_seam': physical_target_seconds,
            'target_payload_host_readback': readback_seconds, 'target_replay_graph_and_updates': replay_seconds}}


def run_qualification(*, mode='CPU_REFERENCE', device='cpu', iterations=1, maximum_seconds=120):
    """Run all four fixed cases; a partial/failed roster never receives PASS.

    The wall/RSS/device-memory checks are observational soft limits, not kernel
    cancellation or hard allocation quotas. Use the notebook's isolated child
    supervisor for a hard process deadline. Each iteration starts fresh weights.
    """
    request = DeviceQualificationRequest(mode, device, iterations, maximum_seconds)
    from heterodiff.evaluation.two_domain_count_normalized_event_cks import PHYSIONET_DOMAIN_ID, RETAIL_DOMAIN_ID
    from heterodiff.experiments.factorized_conditional_training import PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID
    report = {'schema_version': 'factorized-device-qualification-v1', 'fixture_id': FIXTURE_ID,
        'tolerance_policy_id': POLICY_ID, 'mode': mode, 'device': device, 'iterations': iterations,
        'torch_version': torch.__version__, 'cuda_build_version': torch.version.cuda,
        'cuda_execution': 'CUDA_NOT_EXECUTED' if mode == 'CPU_REFERENCE' else 'CUDA_REQUESTED',
        'cases': [], 'required_case_count': 4*iterations,
        'bounds': {'batch_rows': 3, 'state_event_cap': 4, 'metadata_bytes_per_event': 2048,
            'batch_metadata_bytes': 32768, 'maximum_seconds_soft': maximum_seconds,
            'maximum_memory_bytes_soft': MAXIMUM_MEMORY_BYTES, 'warmup_iterations': 0,
            'mandatory_same_device_replays_per_case': 1},
        'scope': {'synthetic_only': True, 'actual_data_accessed': False, 'paid_or_remote_jobs_launched': False,
            'packages_installed': False, 'files_written': False, 'production_qualification': False,
            'whole_cluster_allocation_proven': False, 'all_gpu_pipeline_claimed': False,
            'F105_factory_or_checkpoint_validation_executed': False,
            'physical_seam': 'ONE_FIXED_INCREMENT_HEUN_STEP_NOT_A_COMPLETE_CONDITIONAL_PATH',
            'host_work': ['exact metadata and ordering', 'FP64 association guide', 'Heun control flow'],
            'speedup_claimed': False}}
    report['scope']['CPU_REFERENCE_library_internal_availability_probes_possible'] = True
    report['scope']['CPU_REFERENCE_explicit_CUDA_discovery_or_allocation_requested_by_harness'] = False
    budget = _Budget(request)
    try:
        if mode == 'CUDA':
            report['version_selected_CUDA_precision_family'] = _cuda_precision_family(torch.__version__)
        with _numerical_policy(request) as precision:
            report['active_numerical_policy'] = {
                'intraop_threads': torch.get_num_threads(),
                'deterministic_algorithms': torch.are_deterministic_algorithms_enabled(),
                'deterministic_warn_only': torch.is_deterministic_algorithms_warn_only_enabled(),
                'CUDA_IEEE_precision_family': precision['family'],
                'CUDA_IEEE_precision_settings': precision['settings'],
                'mixed_precision_or_autocast_used': False,
                'CUDA_cudnn_benchmark': False if mode == 'CUDA' else 'NOT_ACCESSED',
                'ordinary_AdamW_health_checks_and_math_unchanged': True,
            }
            if mode == 'CUDA':
                properties = torch.cuda.get_device_properties(device)
                report['selected_device'] = {'name': properties.name, 'total_memory_bytes': properties.total_memory,
                    'compute_capability': [properties.major, properties.minor]}
                report['cuda_execution'] = 'CUDA_CONTEXT_ACCESSED_NEURAL_EXECUTION_NOT_YET_COMPLETED'
            for iteration in range(iterations):
                for domain in (PHYSIONET_DOMAIN_ID, RETAIL_DOMAIN_ID):
                    for method in (PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID):
                        budget.check()
                        result = _case(domain, method, device, budget)
                        result['iteration'] = iteration
                        report['cases'].append(result)
                        if mode == 'CUDA':
                            report['cuda_execution'] = 'CUDA_NEURAL_CASE_EXECUTED_SELECTED_DEVICE_ONLY'
            passed = len(report['cases']) == 4*iterations and all(case['passed'] for case in report['cases'])
            report['decision'] = ('PASS_CPU_REFERENCE_CUDA_NOT_EXECUTED' if mode == 'CPU_REFERENCE'
                                  else 'PASS_SELECTED_CUDA_SYNTHETIC_PARITY_ONLY') if passed else 'FAIL_DEVICE_PARITY'
    except (RuntimeError, ValueError, ImportError, OSError) as error:
        report['decision'] = 'STOP_DEVICE_QUALIFICATION_INCOMPLETE'
        report['error_type'] = type(error).__name__
        # Exclude traceback, runtime paths, identities and arbitrary backend diagnostics.
        report['error_detail'] = str(error)[:240] if isinstance(error, DeviceQualificationError) else 'local operation failed; inspect local traceback separately'
    report['completed_case_count'] = len(report['cases'])
    report['elapsed_seconds'] = time.perf_counter()-budget.started
    report['memory'] = {'process_lifetime_peak_rss_bytes': _rss(), 'exclusive_task_memory_claimed': False}
    if mode == 'CUDA' and 'selected_device' in report:
        try:
            report['memory']['selected_device_peak_allocated_bytes'] = torch.cuda.max_memory_allocated(device)
            report['memory']['selected_device_peak_reserved_bytes'] = torch.cuda.max_memory_reserved(device)
        except (RuntimeError, OSError):
            report['memory']['selected_device_peak_measurement_failed'] = True
            report['decision'] = 'STOP_DEVICE_MEMORY_MEASUREMENT_FAILED'
    report['timing_scope'] = {'synchronized_wall_time': True,
        'explicit_cuda_synchronize_calls': budget.explicit_synchronizations,
        'internal_scalar_synchronization_count': None, 'internal_scalar_synchronizations_included_in_wall_time': True,
        'pure_kernel_active_time_measured': False, 'all_transfers_separately_measured': False,
        'cross_device_analytic_autograd_transfers_included_in_graph_time': True,
        'first_use_overheads_included': True, 'hard_deadline_provided_by_caller_not_harness': True}
    return report
