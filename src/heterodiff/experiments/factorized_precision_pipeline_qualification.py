"""Bounded CPU-only qualification of explicit BASE precision propagation.

Invented fixtures, two BASE and two conditional updates per fresh run, four
domain/method cases and one exact replay each. Never accepts device/run settings,
loads data, installs packages, writes results or launches remote computation.
Full-path here means these tiny finite numerical paths, not a scientific release.
"""
from fractions import Fraction
import hashlib
import json
import math
import time

import numpy as np
import torch

from heterodiff.data.two_domain_factorized_state import (
    FactoredEvent, FactorizedMetadataReference, PhysioStateKey, RetailStateKey,
    TrainInformedMetadataReference,
)
from heterodiff.experiments.factorized_base_precision import PRECISION_POLICY
from heterodiff.experiments.factorized_conditional_pipeline import (
    FactorizedPopulationContext, _parameter_digest,
)
from heterodiff.experiments.factorized_conditional_training import FactorizedConditionalModel, FactorizedObservation
from heterodiff.experiments.factorized_device_qualification import (
    DeviceQualificationRequest, TOLERANCES, POLICY_ID, _Budget, _compare,
    _error_diagnostics, _need, _numerical_policy, _optimizer, _rss,
)
from heterodiff.experiments.factorized_device_training import (
    DeviceFactorizedBasePopulation, DeviceFactorizedConditionalModel, DeviceFactorizedPhysicalPotential,
    device_sample_conditional, device_train_base_step, device_train_conditional_step,
)
from heterodiff.models.factorized_configuration_energy_torch import (
    BoundedFactorizedConfigurationEnergy, FactorizedEnergyArchitecture, FactorizedEnergyLimits,
)
from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy
from heterodiff.processes.factorized_hybrid_sampler import (
    ExactFactorizedReference, FactorizedSamplerLimits, FactorizedSchedule, LearnedFactorizedSampler,
    canonical, heun_step,
)
from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide
from heterodiff.theory.factorized_smooth_amendment import AmendmentParameters, FactorizedSmoothOracle


DOMAINS = ('R3-PHYS', 'R4-RETAIL')
METHODS = ('association-aware-guide-plus-residual', 'unified-direct-conditioner')
CASE_ROSTER = tuple((domain, method) for domain in DOMAINS for method in METHODS)
GRID = (0., .25, .5, .75, 1.)
FIXTURE_ID = 'factorized-precision-pipeline-tiny-cpu-v1'


def _fixture(domain, method):
    _need(domain in DOMAINS and method in METHODS, 'unknown fixed fixture')
    if domain == 'R3-PHYS':
        atomic = FactoredEvent(PhysioStateKey(3, 'MechVent', 'ATOMIC', Fraction(1)))
        continuous = FactoredEvent(PhysioStateKey(3, 'HR', 'POSITIVE'), .2)
    else:
        def key(branch):
            return RetailStateKey('C123456', 'sku', 'name', -1, (2010, 1, 2, 3, 4, 5, 6), 'UK', branch)
        atomic, continuous = FactoredEvent(key('ZERO')), FactoredEvent(key('NEGATIVE'), .2)
    source = (atomic, continuous, continuous)
    q = TrainInformedMetadataReference(FactorizedMetadataReference(domain), source, beta=Fraction(1, 4))
    oracle = FactorizedSmoothOracle(q, AmendmentParameters(.5, 4, 4, .2, .1, .25, .25, 1.))
    schedule = FactorizedSchedule(1., .25, .5, 1.)
    reference = ExactFactorizedReference(oracle, schedule,
        FactorizedSamplerLimits(maximum_jump_candidates=20000, maximum_initialization_trials=256))
    arch = FactorizedEnergyArchitecture('SYNTHETIC_PRECISION_PIPELINE:' + domain, 4, 1., .25, 1., 1.,
                                      FactorizedEnergyLimits(4, 16, 2048, 16384))
    base = DeviceFactorizedEnergy.from_cpu(BoundedFactorizedConfigurationEnergy(arch, initialization_seed=41), 'cpu')
    prototype = FactorizedConditionalModel(BoundedFactorizedConfigurationEnergy(arch, initialization_seed=42),
        guide=FactorizedAssociationGuide(oracle), method_id=method, clean_hold=.25,
        remaining_clocks=schedule.remaining_clocks, observation_seed=43, nuisance_seed=44)
    model = DeviceFactorizedConditionalModel.from_cpu(prototype, 'cpu')
    context = FactorizedPopulationContext(domain, 'SYNTHETIC_PRECISION_PIPELINE', b'fixed-fixture-context', (0.,)*64)
    return source, reference, base, model, context


def _digest(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _state_record(state):
    return [[event.key.canonical_bytes().hex(), None if event.coordinate is None else event.coordinate.hex()]
            for event in state]


def _path_summary(path, domain):
    _need(path.reverse_grid[0] == 0. and path.reverse_grid[-1] == 1., 'incomplete numerical path')
    _need(len(path.states) == len(path.reverse_grid) and path.states[-1] is path.states[-2], 'clean hold not retained')
    for state in path.states:
        _need(len(state) <= 4, 'state cap exceeded')
        for event in state:
            _need(event.key.domain_id == domain and (event.coordinate is None or math.isfinite(event.coordinate)),
                  'nonfinite or cross-domain generated event')
    d = path.diagnostics
    return {'state_grid_sha256': _digest({'states': [_state_record(x) for x in path.states], 'grid': path.reverse_grid}),
        'full_diagnostics_sha256': _digest(d),
        'grid': path.reverse_grid, 'cardinalities': [len(x) for x in path.states],
        'accepted_births': d['accepted_birth'], 'accepted_deaths': d['accepted_death'],
        'jump_candidates': d['jump_candidates'], 'reference_initializer': d['reference_pi_n_initializer'],
        'stream_binding_sha256': d['stream_binding_sha256'],
        'base_precision_policy': d.get('base_precision_policy'),
        'exact_continuous_time_law_claimed': False}


def _gradient_steps(model, counts):
    for name, p in model.named_parameters():
        counts[name] += int(p.grad is not None)


def _optimizer_snapshot(model, optimizer, expected_steps):
    record = []
    histogram = {}
    for name, p in model.named_parameters():
        _need(p.dtype == torch.float32 and p.device.type == 'cpu', 'non-FP32 CPU trainable parameter')
        _need(bool(torch.isfinite(p).all()), 'nonfinite trainable parameter')
        state = optimizer.state.get(p, {})
        row = [name, hashlib.sha256(p.detach().numpy().tobytes()).hexdigest()]
        count = expected_steps[name]
        histogram[str(count)] = histogram.get(str(count), 0) + 1
        if count == 0:
            _need(not state, 'unused parameter gained optimizer state')
            record.append(row + [0])
            continue
        _need(set(state) == {'step', 'exp_avg', 'exp_avg_sq'}, 'optimizer state incomplete')
        _need(float(state['step']) == count, 'optimizer step count changed')
        row.append(count)
        for field in ('exp_avg', 'exp_avg_sq'):
            tensor = state[field]
            _need(tensor.dtype == torch.float32 and tensor.device.type == 'cpu'
                  and bool(torch.isfinite(tensor).all()), 'nonfinite or misplaced moment')
            row.append(hashlib.sha256(tensor.detach().numpy().tobytes()).hexdigest())
        record.append(row)
    return {'parameters_moments_and_steps_sha256': _digest(record),
            'parameter_tensor_step_histogram': histogram,
            'steps_match_actual_non_none_gradients': True, 'parameters_and_moments_dtype': 'FP32'}


def _fixed_input_controls(base, model, source, context):
    """One common state and Brownian increment, not same-seed law coupling."""
    observation = FactorizedObservation((source[-1],), context.domain_id, context.task_id, context.context_bytes)
    source = canonical(source)
    kwargs = dict(base_context=context.base_context, conditional_model=model, observation=observation, clean_hold=.25)
    candidate = DeviceFactorizedPhysicalPotential(base, **kwargs, precision_policy=PRECISION_POLICY)
    replay = DeviceFactorizedPhysicalPotential(base, **kwargs, precision_policy=PRECISION_POLICY)
    legacy = DeviceFactorizedPhysicalPotential(base, **kwargs)
    def payload(physical):
        result = {}
        for u in (0., .375, .75, .875, 1.):
            v, g = physical.value_grad(u, source)
            _need(v == physical.value(u, source), 'physical value and value_grad disagree')
            result['value/' + u.hex()] = ('physical', torch.tensor(v, dtype=torch.float64, device='cpu'))
            result['gradient/' + u.hex()] = ('physical', torch.tensor([a for row in g for a in row], dtype=torch.float64, device='cpu'))
        increments = tuple((.01,) if event.key.dimension else () for event in source)
        stepped = heun_step(source, .375, .0625, physical, .5, increments)
        _need(tuple(e.key for e in stepped) == tuple(e.key for e in source), 'continuous step altered exact metadata')
        _need(any(a.coordinate != b.coordinate for a, b in zip(source, stepped) if a.key.dimension),
              'fixed continuous diagnostic did not move')
        result['heun_coordinates'] = ('physical', torch.tensor([e.coordinate for e in stepped if e.key.dimension],
                                                               dtype=torch.float64, device='cpu'))
        _need(physical.value(.75, source) == physical.value(.875, source) == physical.value(1., source),
              'clean hold changes physical value')
        return result
    left, right, old = payload(candidate), payload(replay), payload(legacy)
    exact = _compare(left, right, exact=True)
    drift = _compare(old, left)
    return {'candidate_snapshot_exact_replay': exact['passed'],
        'candidate_snapshot_maximum_difference': max(x['maximum_absolute_difference'] for x in exact['categories'].values()),
        'legacy_same_weights_fixed_input_drift': {'passed_existing_physical_tolerance': drift['passed'],
            'maximum_absolute_difference': max(x['maximum_absolute_difference'] for x in drift['categories'].values()),
            'failure_count': drift['failure_count'], 'gates_candidate_completion': False},
        'common_inputs': 'EXPLICIT_STATE_AND_FIXED_BROWNIAN_INCREMENT_NOT_POPULATION_RUN_SEED',
        'continuous_coordinate_motion_exercised': True, 'duplicate_occurrences_preserved': True}


def _fixed_jump_controls(base, reference, source, context):
    """Scripted diagnostic streams exercise both routes; not draws from a law."""
    class ConstantUniform:
        def __init__(self, value):
            self.value = value
        def random(self):
            return self.value
    class DiagnosticStreams:
        def rng(self, purpose, step, ordinal):
            if purpose == 'jump-wait':
                return ConstantUniform(1. - 1e-12 if ordinal == 0 else 1e-300)
            if purpose == 'jump-accept':
                return ConstantUniform(1e-300)
            _need(purpose == 'jump-route', 'unexpected diagnostic stream')
            return np.random.default_rng(887 + ordinal)
    physical = DeviceFactorizedPhysicalPotential(base, base_context=context.base_context,
                                                 clean_hold=.25, precision_policy=PRECISION_POLICY)
    sampler = LearnedFactorizedSampler(reference, physical, GRID)
    record = {}
    # Empty forces a birth proposal; full cap forces a death proposal. Neither
    # the proposal nor acceptance calculation is mocked or replaced.
    for kind, state in (('birth', ()), ('death', canonical((source[-1],) * 4))):
        counts = dict(jump_candidates=0, accepted_jumps=0, accepted_birth=0, accepted_death=0)
        journal = []
        dest = sampler._jumps(state, .375, .01, 0, DiagnosticStreams(), counts, journal)
        _need(counts['jump_candidates'] == counts['accepted_jumps'] == counts['accepted_' + kind] == 1,
              'fixed birth/death diagnostic incomplete')
        _need(len(dest) == len(state) + (1 if kind == 'birth' else -1), 'diagnostic count change incorrect')
        record[kind] = {'counts': counts, 'source_count': len(state), 'destination_count': len(dest),
                        'state_and_journal_sha256': _digest({'state': _state_record(dest), 'journal': journal})}
    return {'controls': record, 'scripted_streams_not_scientific_draws': True,
            'scope': 'BASE_ONLY_ACCEPTED_JUMP_CONTROL_NOT_CONDITIONAL_PATH_FREQUENCY'}


def _run(domain, method, budget, progress):
    source, reference, base, model, context = _fixture(domain, method)
    rng = np.random.default_rng(7)
    base_optimizer = _optimizer(base)
    base_counts = {name: 0 for name, _ in base.named_parameters()}
    base_updates = []
    for _ in range(2):
        budget.check()
        progress['base_updates_begun'] += 1
        update = device_train_base_step(base, reference, (source,), context=torch.zeros(64, device='cpu'),
            rng=rng, optimizer=base_optimizer, sample_count=2, jump_weight=1., precision_policy=PRECISION_POLICY)
        _need(update['base_precision_policy'] == PRECISION_POLICY and update['changed_parameter_elements'] > 0,
              'candidate BASE update absent')
        base_updates.append(update)
        _gradient_steps(base, base_counts)
        progress['base_updates_completed'] += 1
    base_state = _optimizer_snapshot(base, base_optimizer, base_counts)
    base_weights = _parameter_digest(base)
    population = DeviceFactorizedBasePopulation(base, reference, GRID, context, precision_policy=PRECISION_POLICY)
    legacy = DeviceFactorizedBasePopulation(base, reference, GRID, context)
    _need(population.precision_policy == population.physical.precision_policy == PRECISION_POLICY,
          'candidate policy not propagated to frozen population')
    _need(population.law_id != legacy.law_id, 'candidate and legacy population identities collide')
    joint, product, paths = population.sample_pair(reverse_time=.375, run_seed=501, record_id=b'paired-control')
    _need(joint.states == product.states == (paths[0].at_time(.375),), 'paired first-state binding changed')
    _need(joint.law_id == product.law_id and joint.law_id.startswith(population.law_id), 'paired law binding changed')
    _need(joint.observations[0].context_identity == product.observations[0].context_identity,
          'paired observation context changed')
    paired = [_path_summary(path, domain) for path in paths]
    _need(paired[0]['stream_binding_sha256'] != paired[1]['stream_binding_sha256'], 'joint/product streams not separated')
    _need(all(p['base_precision_policy'] == PRECISION_POLICY and p['reference_initializer'] for p in paired),
          'paired BASE paths lost precision policy or reference initializer')
    optimizer = _optimizer(model)
    conditional_counts = {name: 0 for name, _ in model.named_parameters()}
    conditional_updates = []
    training_paths = []
    original_sample_pair = population.sample_pair
    def recorded_sample_pair(**kwargs):
        result = original_sample_pair(**kwargs)
        training_paths.extend(_path_summary(path, domain) for path in result[2])
        return result
    # Observe the exact paths used by the learner; no replacement law or draws.
    population.sample_pair = recorded_sample_pair
    for i in range(2):
        budget.check()
        progress['conditional_updates_begun'] += 1
        update = device_train_conditional_step(model, population, optimizer=optimizer, reverse_time=None,
            run_seed=501, record_id=('conditional-step-' + str(i)).encode(), sample_count=1)
        _need(update['changed_parameter_elements'] > 0 and update['base_paths_generated'] == 2
              and update['base_precision_policy'] == PRECISION_POLICY,
              'conditional update or candidate source population absent')
        _need(update['time_policy'] == 'UNIFORM_FULL_REVERSE_INTERVAL' and 0 < update['reverse_times'][0] < 1,
              'full-interval conditional time missing')
        conditional_updates.append(update)
        _gradient_steps(model, conditional_counts)
        progress['conditional_updates_completed'] += 1
    conditional_state = _optimizer_snapshot(model, optimizer, conditional_counts)
    _need(len(training_paths) == 4, 'conditional source path count changed')
    _need(_parameter_digest(base) == _parameter_digest(population.physical.base) == base_weights,
          'conditional updates mutated learned BASE snapshot')
    results = {}
    conditional_weights = _parameter_digest(model)
    for name, observed in (('retained', (source[-1],)), ('overflow', None)):
        budget.check()
        path = device_sample_conditional(base, model, reference, GRID, context, observed,
            run_seed=502, record_id=('draw-' + name).encode(), precision_policy=PRECISION_POLICY)
        summary = _path_summary(path, domain)
        _need(summary['base_precision_policy'] == PRECISION_POLICY and not summary['reference_initializer'],
              'conditional sampler lost policy or used unconditioned initializer')
        results[name] = summary
    _need(_parameter_digest(model) == conditional_weights and _parameter_digest(base) == base_weights,
          'conditional sampling mutated trainable models')
    budget.check()
    controls = _fixed_input_controls(base, model, source, context)
    _need(controls['candidate_snapshot_exact_replay'], 'fixed-input candidate replay failed')
    jumps = _fixed_jump_controls(base, reference, source, context)
    budget.check()
    return {'base_updates': base_updates, 'conditional_updates': conditional_updates,
        'base_optimizer_snapshot': base_state,
        'conditional_optimizer_snapshot': conditional_state,
        'candidate_population_law_id': population.law_id, 'legacy_population_law_id': legacy.law_id,
        'paired_paths': paired, 'conditional_source_paths': training_paths,
        'conditional_paths': results, 'fixed_input_controls': controls, 'fixed_jump_controls': jumps,
        'base_frozen_during_conditional_work': True, 'sampler_did_not_mutate_models': True}


def run_local_precision_pipeline_check():
    """Fixed CPU workload; soft120s/2GiB bounds, no hard process quota claimed."""
    request = DeviceQualificationRequest()
    budget = _Budget(request)
    progress = dict(stage='START', base_updates_begun=0, base_updates_completed=0,
                    conditional_updates_begun=0, conditional_updates_completed=0)
    report = {'schema_version': 'factorized-precision-pipeline-local-check-v1',
        'fixture_id': FIXTURE_ID, 'precision_policy': PRECISION_POLICY, 'device': 'cpu',
        'torch_version': str(torch.__version__), 'tolerance_policy_id': POLICY_ID,
        'unchanged_physical_tolerance': TOLERANCES['physical'], 'cases': [], 'progress': progress,
        'bounds': {'cases': 4, 'fresh_runs_per_case': 2, 'base_updates': 16, 'conditional_updates': 16,
            'paired_base_paths': 48, 'conditional_paths': 16, 'state_cap': 4,
            'scripted_single_jump_diagnostic_operations': 16,
            'per_path_jump_candidate_limit': 20000, 'per_initialization_trial_limit': 256,
            'maximum_seconds_soft': 120, 'maximum_memory_bytes_soft': 2*1024**3,
            'hard_deadline_or_memory_quota_claimed': False},
        'scope': {'local_cpu_only': True, 'synthetic_only': True, 'real_data_accessed': False,
            'explicit_CUDA_query_or_execution_requested': False,
            'library_internal_accelerator_availability_probes_possible': True,
            'cloud_jobs_launched': False, 'files_written': False, 'packages_installed': False,
            'scientific_training_or_convergence_claimed': False, 'F105_executed': False,
            'installed_release_qualified': False, 'full_pipeline_GPU_qualified': False,
            'legacy_default_or_acceptance_tolerances_changed': False,
            'equal_seeds_across_different_population_laws_claimed_as_coupling': False}}
    try:
        _need(CASE_ROSTER == tuple((domain, method) for domain in DOMAINS for method in METHODS)
              and len(CASE_ROSTER) == len(set(CASE_ROSTER)) == 4, 'invalid fixed four-case roster')
        with _numerical_policy(request):
            for domain, method in CASE_ROSTER:
                progress.update(stage='CASE', domain_id=domain, method_id=method)
                budget.check()
                first = _run(domain, method, budget, progress)
                replay = _run(domain, method, budget, progress)
                _need(first == replay, 'fresh CPU full-pipeline replay differs')
                report['cases'].append({'domain_id': domain, 'method_id': method,
                    'fresh_full_run_exact_replay': True, 'full_run_sha256': _digest(first), 'run': first})
            _need(progress['base_updates_completed'] == progress['base_updates_begun'] == 16
                  and progress['conditional_updates_completed'] == progress['conditional_updates_begun'] == 16,
                  'incomplete local training step count')
            _need(tuple((c['domain_id'], c['method_id']) for c in report['cases']) == CASE_ROSTER,
                  'incomplete four-case roster')
            visible_paths = [path for case in report['cases'] for path in
                case['run']['paired_paths'] + case['run']['conditional_source_paths'] +
                list(case['run']['conditional_paths'].values())]
            _need(len(visible_paths) == 32, 'incomplete full-path record count')
            report['path_activity_first_runs_only'] = {
                'recorded_paths': len(visible_paths),
                'accepted_births': sum(p['accepted_births'] for p in visible_paths),
                'accepted_deaths': sum(p['accepted_deaths'] for p in visible_paths),
                'jump_candidates': sum(p['jump_candidates'] for p in visible_paths)}
            _need(report['path_activity_first_runs_only']['accepted_births'] +
                  report['path_activity_first_runs_only']['accepted_deaths'] > 0,
                  'generated paths did not exercise any accepted jumps')
            budget.check()
            report['decision'] = 'PASS_LOCAL_CPU_PRECISION_PIPELINE_ONLY'
        progress['stage'] = 'COMPLETE'
    except Exception as error:
        report['decision'] = 'STOP_LOCAL_PRECISION_PIPELINE_INCOMPLETE'
        report['error_type'] = type(error).__name__
        report['error_diagnostics'] = _error_diagnostics(error)
    report['completed_case_count'] = len(report['cases'])
    report['elapsed_seconds'] = time.perf_counter()-budget.started
    report['process_lifetime_peak_rss_bytes'] = _rss()
    return report
