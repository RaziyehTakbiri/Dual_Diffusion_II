"""Fixed CPU-only multi-step/checkpoint continuity check on invented fixtures.

Four BASE and four generated-population conditional updates, uninterrupted
versus disk-roundtripped fresh objects. This is not convergence, process-restart,
production checkpointing, cross-version/device resume, or real-data evidence.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys
import tempfile
import time

import numpy as np
import torch

from heterodiff.experiments.factorized_base_precision import PRECISION_POLICY
from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest, _reference_identity
from heterodiff.experiments.factorized_device_qualification import (
    DeviceQualificationRequest, POLICY_ID, TOLERANCES, _Budget, _error_diagnostics,
    _need, _numerical_policy, _optimizer, _rss,
)
from heterodiff.experiments.factorized_device_training import (
    DeviceFactorizedBasePopulation, device_train_base_step,
    device_train_conditional_step, device_sample_conditional,
)
from heterodiff.experiments.factorized_precision_pipeline_device_check import _payload_digest
from heterodiff.experiments.factorized_precision_pipeline_qualification import (
    CASE_ROSTER, GRID, _digest, _fixture, _optimizer_snapshot, _path_summary, _state_record,
)
from heterodiff.experiments.factorized_training_checkpoint import encode_checkpoint, restore_checkpoint

BASE_STEPS = 4
CONDITIONAL_STEPS = 4
MAXIMUM_REPORT_BYTES = 48 * 1024
MAXIMUM_SECONDS = 300
MAXIMUM_CHECKPOINT_BYTES = 16 * 1024**2
ROUTES = ('uninterrupted', 'resumed')
PHASE_ORDER = ('BASE',) * BASE_STEPS + ('CONDITIONAL',) * CONDITIONAL_STEPS


def _new_state(domain, method):
    source, reference, base, conditional, context = _fixture(domain, method)
    cursor = {
        'phase': 'BASE', 'completed_base_steps': 0, 'completed_conditional_steps': 0,
        'base_gradient_steps': {n: 0 for n, _ in base.named_parameters()},
        'conditional_gradient_steps': {n: 0 for n, _ in conditional.named_parameters()},
        'conditional_run_seed': 501, 'conditional_record_prefix': 'multistep-conditional-v1',
        'population_law_id': None,
    }
    return {'source': source, 'reference': reference, 'base': base, 'conditional': conditional,
            'context': context, 'base_optimizer': _optimizer(base),
            'conditional_optimizer': _optimizer(conditional), 'base_rng': np.random.default_rng(7),
            'cursor': cursor, 'population': None}


def _binding(state):
    base, conditional = state['base'], state['conditional']
    return {
        'schema_version': 'factorized-multistep-local-binding-v1',
        'precision_policy': PRECISION_POLICY, 'device': 'cpu',
        'base_architecture_sha256': base.architecture.architecture_sha256,
        'conditional_architecture_sha256': conditional.conditioner.architecture.architecture_sha256,
        'domain_id': state['context'].domain_id, 'method_id': conditional.method_id,
        'reference_sha256': _reference_identity(state['reference']),
        'context_sha256': hashlib.sha256(state['context'].binding()).hexdigest(),
        'source_fixture_sha256': _digest(_state_record(state['source'])),
        'torch_version': str(torch.__version__), 'numpy_version': str(np.__version__),
        'python_version': sys.version.split()[0],
        'optimizer_policy': {'class': 'AdamW', 'lr': .001, 'betas': [.9, .999], 'eps': 1e-8,
            'weight_decay': 0., 'foreach': False, 'fused': False, 'amsgrad': False,
            'maximize': False, 'capturable': False, 'differentiable': False},
        'training_schedule': {'base_steps': BASE_STEPS, 'conditional_steps': CONDITIONAL_STEPS,
            'base_samples': 2, 'conditional_samples': 1, 'jump_weight': 1.,
            'reverse_grid': list(GRID), 'schedule': dict(state['reference'].schedule.__dict__),
            'time_policy': 'UNIFORM_FULL_REVERSE_INTERVAL'},
        'conditional_seed': 501, 'conditional_record_prefix': 'multistep-conditional-v1',
    }


def _snapshot(state):
    """Finite complete post-step state, including previous moments for unused grads."""
    tensors, groups, modes, trainability = {}, {}, {}, {}
    for label in ('base', 'conditional'):
        model, optimizer = state[label], state[label + '_optimizer']
        counters = state['cursor'][label + '_gradient_steps']
        _need(set(counters) == dict(model.named_parameters()).keys(), 'gradient counter roster changed')
        _optimizer_snapshot(model, optimizer, counters)
        expected = list(model.parameters())
        actual = [p for group in optimizer.param_groups for p in group['params']]
        _need(len(expected) == len(actual) and all(a is b for a, b in zip(expected, actual))
              and all(any(p is q for q in expected) for p in optimizer.state),
              'optimizer ownership/order changed')
        groups[label] = [{k: v for k, v in group.items() if k != 'params'}
                         for group in optimizer.param_groups]
        modes[label] = {n: m.training for n, m in model.named_modules()}
        trainability[label] = {n: p.requires_grad for n, p in model.named_parameters()}
        _need(all(trainability[label].values()), 'trainable parameter unexpectedly frozen')
        for name, value in model.state_dict().items():
            tensors[label + '/state/' + name] = ('exact', value)
        for name, parameter in model.named_parameters():
            grad = parameter.grad
            if grad is not None:
                _need(grad.dtype == torch.float32 and grad.device.type == 'cpu'
                      and grad.shape == parameter.shape and bool(torch.isfinite(grad).all()),
                      'gradient finite/dtype/shape mismatch')
            tensors[label + '/gradient/' + name] = ('exact', grad)
            for key in ('step', 'exp_avg', 'exp_avg_sq'):
                tensors[label + '/adamw/' + name + '/' + key] = (
                    'exact', optimizer.state.get(parameter, {}).get(key))
    record = {'cursor': deepcopy(state['cursor']), 'rng': deepcopy(state['base_rng'].bit_generator.state),
              'tensors_sha256': _payload_digest(tensors), 'optimizer_groups': groups,
              'module_modes': modes, 'trainability': trainability}
    return _digest(record)


def _count_gradients(state, label):
    for name, parameter in state[label].named_parameters():
        state['cursor'][label + '_gradient_steps'][name] += int(parameter.grad is not None)


def _population(state):
    result = DeviceFactorizedBasePopulation(state['base'], state['reference'], GRID, state['context'],
                                           precision_policy=PRECISION_POLICY)
    _need(result.law_id == state['cursor']['population_law_id'], 'restored population law changed')
    return result


def _advance_base(state):
    cursor = state['cursor']
    _need(cursor['phase'] == 'BASE' and cursor['completed_base_steps'] < BASE_STEPS,
          'BASE cursor is not executable')
    update = device_train_base_step(state['base'], state['reference'], (state['source'],),
        context=torch.tensor(state['context'].base_context, dtype=torch.float32, device='cpu'),
        rng=state['base_rng'], optimizer=state['base_optimizer'], sample_count=2,
        jump_weight=1., precision_policy=PRECISION_POLICY)
    _count_gradients(state, 'base')
    cursor['completed_base_steps'] += 1
    if cursor['completed_base_steps'] == BASE_STEPS:
        cursor['phase'] = 'CONDITIONAL'
        state['population'] = DeviceFactorizedBasePopulation(
            state['base'], state['reference'], GRID, state['context'], precision_policy=PRECISION_POLICY)
        cursor['population_law_id'] = state['population'].law_id
    return update, []


def _advance_conditional(state, budget):
    cursor, population = state['cursor'], state['population']
    _need(cursor['phase'] == 'CONDITIONAL' and cursor['completed_base_steps'] == BASE_STEPS
          and cursor['completed_conditional_steps'] < CONDITIONAL_STEPS, 'conditional cursor is not executable')
    _need(population is not None and population.law_id == cursor['population_law_id'],
          'conditional learner has wrong frozen population')
    before = _parameter_digest(state['base'])
    _need(before == _parameter_digest(population.physical.base), 'population BASE snapshot changed')
    source_paths = []
    original = population.sample_pair
    def observed_pair(**kwargs):
        budget.check()
        joint, product, paths = original(**kwargs)
        source_paths.extend(_path_summary(path, state['context'].domain_id) for path in paths)
        budget.check()
        return joint, product, paths
    population.sample_pair = observed_pair
    try:
        update = device_train_conditional_step(state['conditional'], population,
            optimizer=state['conditional_optimizer'], reverse_time=None,
            run_seed=cursor['conditional_run_seed'],
            record_id=cursor['conditional_record_prefix'].encode('ascii') +
                cursor['completed_conditional_steps'].to_bytes(8, 'big'),
            sample_count=1)
    finally:
        del population.sample_pair
    _need(len(source_paths) == update['base_paths_generated'] == 2,
          'generated conditional source path count changed')
    _need(all(p['base_precision_policy'] == PRECISION_POLICY and p['reference_initializer'] is True
              for p in source_paths), 'conditional source path precision/initializer changed')
    _need(_parameter_digest(state['base']) == before == _parameter_digest(population.physical.base),
          'conditional update mutated frozen BASE')
    _count_gradients(state, 'conditional')
    cursor['completed_conditional_steps'] += 1
    return update, source_paths


def _roundtrip(state, scratch, name, progress):
    before, binding = _snapshot(state), _binding(state)
    payload = encode_checkpoint(binding=binding, cursor=state['cursor'],
        **{k: state[k] for k in ('base', 'conditional', 'base_optimizer', 'conditional_optimizer', 'base_rng')})
    _need(0 < len(payload) <= MAXIMUM_CHECKPOINT_BYTES, 'checkpoint byte bound exceeded')
    path = scratch / name
    with path.open('xb') as handle:
        _need(handle.write(payload) == len(payload), 'checkpoint write incomplete')
    progress['checkpoint_files_written'] += 1
    progress['checkpoint_bytes_written'] += len(payload)
    loaded = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    _need(hashlib.sha256(loaded).hexdigest() == digest, 'disk checkpoint readback changed')
    fresh = _new_state(state['context'].domain_id, state['conditional'].method_id)
    _need(_binding(fresh) == binding, 'fresh construction binding differs')
    fresh['cursor'] = restore_checkpoint(loaded, expected_sha256=digest, expected_binding=binding,
        **{k: fresh[k] for k in ('base', 'conditional', 'base_optimizer', 'conditional_optimizer', 'base_rng')})
    if fresh['cursor']['phase'] == 'CONDITIONAL':
        fresh['population'] = _population(fresh)
    after = _snapshot(fresh)
    _need(before == after, 'post-load model/gradient/AdamW/RNG/cursor state differs')
    progress['checkpoint_restores_completed'] += 1
    return fresh, {'phase': state['cursor']['phase'], 'base_steps': state['cursor']['completed_base_steps'],
        'conditional_steps': state['cursor']['completed_conditional_steps'],
        'bytes': len(payload), 'disk_sha256': digest, 'state_sha256_before': before,
        'state_sha256_after': after, 'exact': True, 'fresh_objects': True,
        'population_law_reconstructed_exactly': fresh['cursor']['phase'] == 'CONDITIONAL'}


def _run_route(domain, method, resumed, scratch, case_index, budget, progress):
    state = _new_state(domain, method)
    initial = _snapshot(state)
    records, checkpoints, path_rows = [], [], []
    for phase in PHASE_ORDER:
        budget.check()
        progress['stage'] = phase
        index = state['cursor']['completed_base_steps' if phase == 'BASE' else 'completed_conditional_steps']
        progress['optimizer_steps_begun'] += 1
        update, paths = (_advance_base(state) if phase == 'BASE' else _advance_conditional(state, budget))
        progress['optimizer_steps_completed'] += 1
        progress['base_updates_completed' if phase == 'BASE' else 'conditional_updates_completed'] += 1
        progress['generated_paths_completed'] += len(paths)
        path_rows.extend(paths)
        _need(type(update['loss']) is float and math.isfinite(update['loss'])
              and update['base_precision_policy'] == PRECISION_POLICY
              and type(update['changed_parameter_elements']) is int
              and update['changed_parameter_elements'] > 0, 'step absent, nonfinite or wrong precision')
        records.append({'phase': phase, 'index': index, 'loss': update['loss'],
            'changed_parameter_elements': update['changed_parameter_elements'],
            'update_sha256': _digest(update), 'source_paths_sha256': _digest(paths),
            'state_sha256': _snapshot(state)})
        if resumed and ((phase == 'BASE' and index == 1) or (phase == 'CONDITIONAL' and index == 1)):
            progress['stage'] = 'CHECKPOINT_ROUNDTRIP'
            state, receipt = _roundtrip(state, scratch, f'case-{case_index}-{phase.lower()}-2.pt', progress)
            checkpoints.append(receipt)
            budget.check()
    _need(state['cursor']['completed_base_steps'] == BASE_STEPS
          and state['cursor']['completed_conditional_steps'] == CONDITIONAL_STEPS, 'route incomplete')
    before = _snapshot(state)
    draws = {}
    for label, observation in (('retained', (state['source'][-1],)), ('overflow', None)):
        budget.check()
        path = device_sample_conditional(state['base'], state['conditional'], state['reference'], GRID,
            state['context'], observation, run_seed=502, record_id=('multistep-final-' + label).encode(),
            precision_policy=PRECISION_POLICY)
        draws[label] = _path_summary(path, domain)
        _need(draws[label]['base_precision_policy'] == PRECISION_POLICY
              and draws[label]['reference_initializer'] is False,
              'final conditional path precision/initializer changed')
        progress['generated_paths_completed'] += 1
    _need(before == _snapshot(state), 'final sampling mutated training state')
    return {'initial_state_sha256': initial, 'step_records': records,
        'final_state_sha256': before, 'population_law_id': state['cursor']['population_law_id'],
        'final_paths': draws, 'source_paths_sha256': _digest(path_rows),
        'source_path_count': len(path_rows), 'generated_path_count': len(path_rows) + len(draws),
        'optimizer_steps': len(records), 'checkpoints': checkpoints,
        'base_loss_history': [r['loss'] for r in records if r['phase'] == 'BASE'],
        'conditional_loss_history': [r['loss'] for r in records if r['phase'] == 'CONDITIONAL'],
        'frozen_BASE_preserved': True, 'sampling_state_unchanged': True,
        'all_parameters_gradients_and_moments_finite_FP32': True}


def _case(domain, method, scratch, case_index, budget, progress):
    routes = {}
    for role in ROUTES:
        progress.update(domain_id=domain, method_id=method, route=role)
        routes[role] = _run_route(domain, method, role == 'resumed', scratch, case_index, budget, progress)
    left, right = (routes[k] for k in ROUTES)
    checks = {key: left[key] == right[key] for key in ('initial_state_sha256', 'step_records',
        'final_state_sha256', 'population_law_id', 'final_paths', 'source_paths_sha256')}
    checks['checkpoint_roundtrips'] = len(right['checkpoints']) == 2 and all(c['exact'] for c in right['checkpoints'])
    return {'domain_id': domain, 'method_id': method, 'routes': routes,
            'checks': checks, 'passed': all(checks.values())}


def _decision(cases):
    def digest(value):
        return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None
    _need(tuple((r['domain_id'], r['method_id']) for r in cases) == CASE_ROSTER, 'four-case roster incomplete')
    expected_checks = {'initial_state_sha256', 'step_records', 'final_state_sha256',
                       'population_law_id', 'final_paths', 'source_paths_sha256', 'checkpoint_roundtrips'}
    for case in cases:
        _need(set(case['routes']) == set(ROUTES) and set(case['checks']) == expected_checks,
              'route or check roster incomplete')
        for role, route in case['routes'].items():
            _need(all(type(route[k]) is int and route[k] == v for k, v in
                      (('optimizer_steps', 8), ('source_path_count', 8), ('generated_path_count', 10))),
                  'route count incomplete')
            _need(all(digest(route[k]) for k in ('initial_state_sha256', 'final_state_sha256',
                      'source_paths_sha256')) and type(route['population_law_id']) is str
                  and re.fullmatch('device-factorized-base-precision-v1-[0-9a-f]{64}',
                                   route['population_law_id']) is not None, 'route identity evidence invalid')
            rows = route['step_records']
            _need(len(rows) == 8 and tuple(r['phase'] for r in rows) == PHASE_ORDER
                  and all(type(r['index']) is int for r in rows)
                  and [r['index'] for r in rows] == list(range(4)) * 2, 'training cursor order changed')
            _need(all(type(r['loss']) is float and math.isfinite(r['loss']) and
                type(r['changed_parameter_elements']) is int and r['changed_parameter_elements'] > 0 and
                all(digest(r[key]) for key in ('state_sha256', 'update_sha256', 'source_paths_sha256'))
                for r in rows),
                'step evidence incomplete or nonfinite')
            _need(route['final_state_sha256'] == rows[-1]['state_sha256']
                  and route['base_loss_history'] == [r['loss'] for r in rows[:4]]
                  and route['conditional_loss_history'] == [r['loss'] for r in rows[4:]],
                  'final state or loss history contradicts step evidence')
            _need(set(route['final_paths']) == {'retained', 'overflow'}, 'final path roster incomplete')
            _need(all(p['base_precision_policy'] == PRECISION_POLICY and p['reference_initializer'] is False
                      and p['exact_continuous_time_law_claimed'] is False and tuple(p['grid']) == GRID
                      and all(digest(p[k]) for k in ('state_grid_sha256', 'full_diagnostics_sha256',
                                                    'stream_binding_sha256'))
                      for p in route['final_paths'].values()), 'final path evidence invalid')
            _need(all(route[k] is True for k in ('frozen_BASE_preserved', 'sampling_state_unchanged',
                'all_parameters_gradients_and_moments_finite_FP32')), 'state ownership or finite evidence missing')
            _need(len(route['checkpoints']) == (2 if role == 'resumed' else 0), 'checkpoint count changed')
        left, right = (case['routes'][k] for k in ROUTES)
        for key in expected_checks - {'checkpoint_roundtrips'}:
            _need(type(case['checks'][key]) is bool and case['checks'][key] == (left[key] == right[key]),
                  'reported comparison contradicts route evidence')
        receipts = right['checkpoints']
        _need([(r['phase'], r['base_steps'], r['conditional_steps']) for r in receipts]
              == [('BASE', 2, 0), ('CONDITIONAL', 4, 2)], 'checkpoint cursor positions changed')
        _need(all(type(r['base_steps']) is int and type(r['conditional_steps']) is int
                  and type(r['bytes']) is int and 0 < r['bytes'] <= MAXIMUM_CHECKPOINT_BYTES
                  and all(digest(r[k]) for k in ('disk_sha256', 'state_sha256_before', 'state_sha256_after'))
                  and r['state_sha256_before'] == right['step_records'][i]['state_sha256']
                  and r['population_law_reconstructed_exactly'] is (r['phase'] == 'CONDITIONAL')
                  for r, i in zip(receipts, (1, 5))), 'checkpoint binding evidence invalid')
        exact = all(r['exact'] is True and r['fresh_objects'] is True and
                    r['state_sha256_before'] == r['state_sha256_after'] for r in receipts)
        _need(type(case['checks']['checkpoint_roundtrips']) is bool
              and case['checks']['checkpoint_roundtrips'] == exact, 'checkpoint evidence contradiction')
        _need(type(case['passed']) is bool and case['passed'] == all(case['checks'].values()),
              'case pass contradicts checks')
    return ('PASS_LOCAL_CPU_MULTISTEP_CHECKPOINT_RESUME_ONLY' if all(c['passed'] for c in cases)
            else 'FAIL_LOCAL_CPU_MULTISTEP_CHECKPOINT_RESUME')


def _global_random_state():
    n = np.random.get_state()
    return _digest({'torch_cpu': torch.random.get_rng_state().numpy().tobytes().hex(),
        'numpy': [n[0], n[1].tolist(), n[2], n[3], n[4]], 'python': random.getstate()})


def run_multistep_checkpoint_check():
    """One fixed local CPU run; no device, seed, iteration or tolerance overrides."""
    request = DeviceQualificationRequest(mode='CPU_REFERENCE', device='cpu', maximum_seconds=MAXIMUM_SECONDS)
    budget = _Budget(request)
    initial_random = _global_random_state()
    progress = {key: 0 for key in ('optimizer_steps_begun', 'optimizer_steps_completed',
        'base_updates_completed', 'conditional_updates_completed', 'generated_paths_completed',
        'checkpoint_files_written', 'checkpoint_restores_completed', 'checkpoint_bytes_written')}
    progress['stage'] = 'START'
    report = {'schema_version': 'factorized-multistep-checkpoint-qualification-v1',
        'precision_policy': PRECISION_POLICY, 'mode': 'CPU_REFERENCE', 'device': 'cpu',
        'torch_version': str(torch.__version__), 'numpy_version': str(np.__version__),
        'python_version': sys.version.split()[0], 'cases': [], 'execution_progress': progress,
        'tolerance_policy_id': POLICY_ID, 'acceptance_tolerances_unchanged': TOLERANCES,
        'bounds': {'required_cases': 4, 'routes_per_case': 2, 'base_steps_per_route': 4,
            'conditional_steps_per_route': 4, 'total_optimizer_steps': 64,
            'base_updates': 32, 'conditional_updates': 32, 'generated_paths': 80,
            'checkpoint_files': 8, 'maximum_checkpoint_bytes': MAXIMUM_CHECKPOINT_BYTES,
            'maximum_seconds_soft': MAXIMUM_SECONDS, 'maximum_memory_bytes_soft': 2 * 1024**3,
            'retries': 0, 'hyperparameter_searches': 0},
        'scope': {'synthetic_only': True, 'same_runtime_CPU_resume_only': True,
            'fresh_objects_after_local_disk_roundtrip': True, 'fresh_OS_process_restart_tested': False,
            'global_RNG_or_dataloader_checkpointing_claimed': False,
            'explicit_PCG64_and_conditional_counter_keys_restored': True,
            'GPU_execution': False, 'explicit_CUDA_discovery_requested': False,
            'library_internal_availability_probes_possible': True,
            'cloud_or_paid_jobs_launched': False, 'real_data_accessed': False, 'F105_executed': False,
            'packages_installed': False, 'production_checkpoint_or_resume': False,
            'convergence_or_long_run_stability_claimed': False, 'legacy_default_changed': False,
            'scientific_objective_or_tolerance_changed': False,
            'checkpoint_bytes_equal_across_independent_saves_claimed': False,
            'untrusted_checkpoint_loading_supported': False}}
    scratch = None
    try:
        with _numerical_policy(request):
            with tempfile.TemporaryDirectory(prefix='heterodiff-multistep-checkpoint-') as directory:
                scratch = Path(directory)
                for ordinal, (domain, method) in enumerate(CASE_ROSTER):
                    budget.check()
                    report['cases'].append(_case(domain, method, scratch, ordinal, budget, progress))
                _need(progress['optimizer_steps_begun'] == progress['optimizer_steps_completed'] == 64
                      and progress['base_updates_completed'] == progress['conditional_updates_completed'] == 32
                      and progress['generated_paths_completed'] == 80
                      and progress['checkpoint_files_written'] == progress['checkpoint_restores_completed'] == 8,
                      'bounded multistep workload incomplete')
                report['decision'] = _decision(report['cases'])
                budget.check()
        _need(_global_random_state() == initial_random, 'global random state changed')
        progress['stage'] = 'COMPLETE'
    except Exception as error:
        report['decision'] = 'STOP_LOCAL_CPU_MULTISTEP_CHECKPOINT_INCOMPLETE'
        report['error_type'] = type(error).__name__
        report['error_diagnostics'] = _error_diagnostics(error)
    report['scratch_checkpoint_files_cleaned'] = scratch is None or not scratch.exists()
    report['global_random_state_preserved'] = _global_random_state() == initial_random
    report['completed_case_count'] = len(report['cases'])
    report['elapsed_seconds'] = time.perf_counter() - budget.started
    report['process_lifetime_peak_rss_bytes'] = _rss()
    report['explicit_cuda_synchronize_calls'] = budget.explicit_synchronizations
    if not report['scratch_checkpoint_files_cleaned'] or not report['global_random_state_preserved']:
        report['decision'] = 'STOP_LOCAL_CPU_MULTISTEP_CHECKPOINT_INCOMPLETE'
    _need(len(json.dumps(report, allow_nan=False).encode()) <= MAXIMUM_REPORT_BYTES, 'local report byte bound exceeded')
    return report
