"""One actual bounded CPU continuity workload plus report/failure contracts."""
from copy import deepcopy
import json
import math
from pathlib import Path

import pytest
import torch

from heterodiff.experiments import factorized_multistep_checkpoint_qualification as q
from heterodiff.experiments.factorized_base_precision import PRECISION_POLICY


CASES = tuple((domain, method) for domain in ('R3-PHYS', 'R4-RETAIL') for method in (
    'association-aware-guide-plus-residual', 'unified-direct-conditioner'))


@pytest.mark.parametrize('settings', (
    {'mode': 'CUDA'}, {'device': 'cuda:0'}, {'iterations': 2}, {'maximum_seconds': 600},
    {'seed': 123}, {'precision_policy': 'LEGACY_FP32'}, {'tolerances': {}},
))
def test_fixed_cpu_workload_accepts_no_execution_overrides(monkeypatch, settings):
    def forbidden(*_args, **_kwargs):
        pytest.fail('unsupported override reached numerical work')
    monkeypatch.setattr(q, '_case', forbidden)
    with pytest.raises(TypeError):
        q.run_multistep_checkpoint_check(**settings)


@pytest.fixture(scope='module')
def actual_report():
    before_random = q._global_random_state()
    before_threads = torch.get_num_threads()
    before_determinism = torch.are_deterministic_algorithms_enabled()
    before_warn = torch.is_deterministic_algorithms_warn_only_enabled()
    directories = []
    original_temp = q.tempfile.TemporaryDirectory
    def tracked_directory(*args, **kwargs):
        result = original_temp(*args, **kwargs)
        directories.append(Path(result.name))
        return result
    def forbidden(*_args, **_kwargs):
        pytest.fail('CPU checkpoint check explicitly touched CUDA')
    with pytest.MonkeyPatch.context() as patches:
        patches.setattr(q.tempfile, 'TemporaryDirectory', tracked_directory)
        for name in ('get_device_properties', 'device_count', 'synchronize',
                     'reset_peak_memory_stats', 'max_memory_allocated', 'max_memory_reserved'):
            patches.setattr(torch.cuda, name, forbidden)
        report = q.run_multistep_checkpoint_check()
    assert q._global_random_state() == before_random
    assert torch.get_num_threads() == before_threads
    assert torch.are_deterministic_algorithms_enabled() == before_determinism
    assert torch.is_deterministic_algorithms_warn_only_enabled() == before_warn
    assert len(directories) == 1 and all(not directory.exists() for directory in directories)
    return report


def test_actual_four_cases_complete_fixed_64_updates_80_paths_eight_roundtrips(actual_report):
    r = actual_report
    assert r['decision'] == 'PASS_LOCAL_CPU_MULTISTEP_CHECKPOINT_RESUME_ONLY', r
    assert r['mode'] == 'CPU_REFERENCE' and r['device'] == 'cpu'
    assert r['precision_policy'] == PRECISION_POLICY
    assert r['completed_case_count'] == 4
    assert tuple((c['domain_id'], c['method_id']) for c in r['cases']) == CASES
    bounds = r['bounds']
    for name, value in {'required_cases': 4, 'routes_per_case': 2, 'base_steps_per_route': 4,
        'conditional_steps_per_route': 4, 'total_optimizer_steps': 64, 'base_updates': 32,
        'conditional_updates': 32, 'generated_paths': 80, 'checkpoint_files': 8,
        'maximum_checkpoint_bytes': 16 * 1024**2, 'maximum_seconds_soft': 300,
        'maximum_memory_bytes_soft': 2 * 1024**3, 'retries': 0, 'hyperparameter_searches': 0}.items():
        assert bounds[name] == value
    p = r['execution_progress']
    assert p['optimizer_steps_begun'] == p['optimizer_steps_completed'] == 64
    assert p['base_updates_completed'] == p['conditional_updates_completed'] == 32
    assert p['generated_paths_completed'] == 80
    assert p['checkpoint_files_written'] == p['checkpoint_restores_completed'] == 8
    assert 0 < p['checkpoint_bytes_written'] <= 8 * 16 * 1024**2
    assert p['stage'] == 'COMPLETE'
    assert r['scratch_checkpoint_files_cleaned'] and r['global_random_state_preserved']
    assert r['explicit_cuda_synchronize_calls'] == 0
    assert math.isfinite(r['elapsed_seconds']) and 0 < r['elapsed_seconds'] <= 300
    assert len(json.dumps(r, allow_nan=False).encode()) <= q.MAXIMUM_REPORT_BYTES


def test_actual_continuation_matches_every_step_and_final_retained_overflow_path(actual_report):
    for case in actual_report['cases']:
        assert case['passed'] is True and all(case['checks'].values())
        left, right = (case['routes'][name] for name in ('uninterrupted', 'resumed'))
        for field in ('initial_state_sha256', 'step_records', 'final_state_sha256',
                      'population_law_id', 'final_paths', 'source_paths_sha256',
                      'base_loss_history', 'conditional_loss_history'):
            assert left[field] == right[field]
        assert left['population_law_id'].startswith('device-factorized-base-precision-v1-')
        for route in (left, right):
            assert route['optimizer_steps'] == 8 and route['source_path_count'] == 8
            assert route['generated_path_count'] == 10
            rows = route['step_records']
            assert [row['phase'] for row in rows] == ['BASE'] * 4 + ['CONDITIONAL'] * 4
            assert [row['index'] for row in rows] == list(range(4)) * 2
            assert all(math.isfinite(row['loss']) for row in rows)
            assert route['frozen_BASE_preserved'] is True
            assert route['sampling_state_unchanged'] is True
            assert route['all_parameters_gradients_and_moments_finite_FP32'] is True
            assert set(route['final_paths']) == {'retained', 'overflow'}
            for path in route['final_paths'].values():
                assert path['base_precision_policy'] == PRECISION_POLICY
                assert path['reference_initializer'] is False
                assert path['exact_continuous_time_law_claimed'] is False
                assert tuple(path['grid']) == q.GRID
                assert path['cardinalities'][-1] == path['cardinalities'][-2]


def test_actual_checkpoints_restore_exact_fresh_objects_at_both_midpoints(actual_report):
    all_receipts = []
    for case in actual_report['cases']:
        assert case['routes']['uninterrupted']['checkpoints'] == []
        receipts = case['routes']['resumed']['checkpoints']
        assert [(r['phase'], r['base_steps'], r['conditional_steps']) for r in receipts] == [
            ('BASE', 2, 0), ('CONDITIONAL', 4, 2)]
        for receipt in receipts:
            assert receipt['exact'] is True and receipt['fresh_objects'] is True
            assert receipt['state_sha256_before'] == receipt['state_sha256_after']
            assert len(receipt['disk_sha256']) == 64
            assert 0 < receipt['bytes'] <= 16 * 1024**2
            assert receipt['population_law_reconstructed_exactly'] is (receipt['phase'] == 'CONDITIONAL')
        all_receipts.extend(receipts)
    assert len(all_receipts) == 8
    assert sum(r['bytes'] for r in all_receipts) == actual_report['execution_progress']['checkpoint_bytes_written']


def no_pass(cases):
    try:
        decision = q._decision(cases)
    except (ValueError, TypeError, KeyError):
        return
    assert not decision.startswith('PASS'), decision


@pytest.mark.parametrize('defect', ('missing', 'duplicate', 'reordered'))
def test_fixed_case_roster_cannot_be_changed(actual_report, defect):
    cases = deepcopy(actual_report['cases'])
    if defect == 'missing':
        cases.pop()
    elif defect == 'duplicate':
        cases[-1] = deepcopy(cases[0])
    else:
        cases.reverse()
    no_pass(cases)


@pytest.mark.parametrize('defect', (
    'missing_route', 'missing_step', 'wrong_phase', 'wrong_index', 'nonfinite_loss',
    'missing_state_hash', 'changed_state', 'missing_path', 'wrong_path_policy',
    'wrong_count', 'ownership_false', 'missing_receipt', 'wrong_receipt_position',
    'unequal_receipt_state', 'invalid_receipt_hash', 'not_fresh', 'legacy_population',
    'contradictory_loss_history', 'missing_check', 'false_check', 'false_case_pass',
))
def test_incomplete_or_contradictory_continuation_evidence_cannot_pass(actual_report, defect):
    cases = deepcopy(actual_report['cases'])
    case = cases[0]
    route = case['routes']['resumed']
    if defect == 'missing_route':
        case['routes'].pop('uninterrupted')
    elif defect == 'missing_step':
        route['step_records'].pop()
    elif defect == 'wrong_phase':
        route['step_records'][0]['phase'] = 'CONDITIONAL'
    elif defect == 'wrong_index':
        route['step_records'][0]['index'] = 2
    elif defect == 'nonfinite_loss':
        route['step_records'][0]['loss'] = math.nan
    elif defect == 'missing_state_hash':
        route['step_records'][0].pop('state_sha256')
    elif defect == 'changed_state':
        route['step_records'][0]['state_sha256'] = 'f' * 64
    elif defect == 'missing_path':
        route['final_paths'].pop('overflow')
    elif defect == 'wrong_path_policy':
        route['final_paths']['retained']['base_precision_policy'] = 'LEGACY_FP32'
    elif defect == 'wrong_count':
        route['optimizer_steps'] = 7
    elif defect == 'ownership_false':
        route['frozen_BASE_preserved'] = False
    elif defect == 'missing_receipt':
        route['checkpoints'].pop()
    elif defect == 'wrong_receipt_position':
        route['checkpoints'][0]['base_steps'] = 3
    elif defect == 'unequal_receipt_state':
        route['checkpoints'][0]['state_sha256_after'] = 'f' * 64
    elif defect == 'invalid_receipt_hash':
        route['checkpoints'][0]['disk_sha256'] = 'invalid'
    elif defect == 'not_fresh':
        route['checkpoints'][0]['fresh_objects'] = False
    elif defect == 'legacy_population':
        route['population_law_id'] = 'device-factorized-' + 'a' * 64
    elif defect == 'contradictory_loss_history':
        route['base_loss_history'][0] += 1.
    elif defect == 'missing_check':
        case['checks'].pop('step_records')
    elif defect == 'false_check':
        case['checks']['step_records'] = False
    else:
        case['passed'] = False
    no_pass(cases)


def test_scope_does_not_promote_local_continuity_to_production_or_convergence(actual_report):
    scope = actual_report['scope']
    for field in ('fresh_OS_process_restart_tested', 'global_RNG_or_dataloader_checkpointing_claimed',
        'GPU_execution', 'explicit_CUDA_discovery_requested', 'cloud_or_paid_jobs_launched',
        'real_data_accessed', 'F105_executed', 'packages_installed', 'production_checkpoint_or_resume',
        'convergence_or_long_run_stability_claimed', 'legacy_default_changed',
        'scientific_objective_or_tolerance_changed', 'checkpoint_bytes_equal_across_independent_saves_claimed',
        'untrusted_checkpoint_loading_supported'):
        assert scope[field] is False
    assert scope['synthetic_only'] and scope['same_runtime_CPU_resume_only']
    assert scope['fresh_objects_after_local_disk_roundtrip']
    assert scope['explicit_PCG64_and_conditional_counter_keys_restored']


def test_failure_cleans_only_its_temporary_scratch_and_does_not_claim_completion(monkeypatch):
    directories = []
    def failure(_domain, _method, scratch, _case_index, _budget, progress):
        directories.append(scratch)
        with (scratch / 'partial-local-test.pt').open('xb') as stream:
            stream.write(b'bounded synthetic failure fixture')
        progress['checkpoint_files_written'] += 1
        raise RuntimeError('synthetic failed checkpoint attempt')
    monkeypatch.setattr(q, '_case', failure)
    report = q.run_multistep_checkpoint_check()
    assert report['decision'] == 'STOP_LOCAL_CPU_MULTISTEP_CHECKPOINT_INCOMPLETE'
    assert report['completed_case_count'] == 0
    assert report['execution_progress']['checkpoint_files_written'] == 1
    assert report['execution_progress']['checkpoint_restores_completed'] == 0
    assert report['scratch_checkpoint_files_cleaned'] is True
    assert directories and all(not path.exists() for path in directories)
