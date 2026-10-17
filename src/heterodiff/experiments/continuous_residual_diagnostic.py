"""Fixed, post-outcome CPU diagnosis of the twelve archived residual fits.

No endpoint sampler, hyperparameter selection, model repair, or cloud interface.
Exact replay bindings make this a diagnosis of old fits, not a replacement run.
The query errors are finite-roster summaries, never posterior accuracy bounds.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

from heterodiff.experiments import continuous_multiseed_benchmark as original

SCHEMA = 'continuous-residual-likelihood-score-diagnosis-v1'
ARCHIVED_REPORT_SHA256 = '5cc83ec15fb3600ae975887c53d1a7b4c50e91ef3ea1e193a7670b8df355510e'
VERIFICATION_SHA256 = 'ebfca4c9aad509023576b2e8d4a546574ed3fbda8d0e652a42180c381b47784b'
ARCHIVED_REPORT = 'research/fixtures/continuous_multiseed_completion_cpu_2026_09_13/report.json'
PROTOCOL = 'docs/RESIDUAL_LIKELIHOOD_SCORE_DIAGNOSTIC_PROTOCOL.md'
COORDINATES = (-3., -1.5, 0., 1.5, 3.)
CHECKPOINTS = (0, 8, 16, 32)
MAXIMUM_SECONDS = 1200


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _payload(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _digest(value):
    return hashlib.sha256(_payload(value)).hexdigest()


def capacity_summary(targets, baseline, bound, gate):
    """Necessary finite-query condition, invariant to a state-independent gauge."""
    _need(len(targets) == len(baseline) and len(targets) >= 2, 'aligned query rosters required')
    _need(all(math.isfinite(x) for x in (*targets, *baseline, bound, gate))
          and bound > 0 and 0 <= gate <= 1, 'finite values and valid amplitude/gate required')
    correction = [a-b for a, b in zip(targets, baseline)]
    diameter = max(correction)-min(correction)
    available = 2*bound*gate
    excess = max(0., diameter-available)
    return {'required_correction_diameter': diameter, 'available_residual_diameter': available,
            'excess_diameter': excess, 'uniform_log_potential_error_lower_bound_any_gauge': excess/2,
            'scope': 'FINITE_QUERY_NECESSARY_CONDITION_NOT_GLOBAL_ERROR_OR_SCORE_BOUND'}


def error_summary(errors):
    _need(bool(errors) and all(math.isfinite(x) for x in errors), 'nonempty finite errors required')
    return {'count': len(errors), 'max_abs': max(abs(x) for x in errors),
            'rms': math.sqrt(math.fsum(x*x for x in errors)/len(errors))}


def query_roster(key):
    from heterodiff.data.two_domain_factorized_state import FactoredEvent, PhysioStateKey
    atomic = PhysioStateKey(3, 'HR', 'ZERO')
    other = PhysioStateKey(4, 'HR', 'POSITIVE')
    return [('EMPTY', None, ()), ('OTHER_ATOM', None, (FactoredEvent(atomic, None),))] + [
        (label, z, (FactoredEvent(selected, z),)) for label, selected in (
            ('CONTINUOUS', key), ('OTHER_CONTINUOUS', other)) for z in COORDINATES]


class ObservationCoverage:
    """Read-only projections, no RNG calls and no scientific sample selection."""
    def __init__(self, key, observation_value, half_width=.5):
        self.key, self.y, self.half_width = key, observation_value, half_width
        self.phase = 'validation'
        self.records = []

    def record(self, joint, product):
        for side, batch in (('joint', joint), ('product', product)):
            for state, u, observed in zip(batch.states, batch.reverse_times, batch.observations):
                value = observed.observed
                if value is None:
                    kind, z = 'OVERFLOW', None
                elif not value:
                    kind, z = 'EMPTY', None
                elif len(value) == 1 and value[0].key == self.key:
                    kind, z = 'SELECTED_CONTINUOUS', value[0].coordinate
                else:
                    kind, z = 'OTHER', None
                self.records.append({'phase': self.phase, 'side': side, 'reverse_time': u,
                    'latent_category': original.category(state, self.key), 'observation_kind': kind,
                    'selected_observation_coordinate': z,
                    'within_fixed_observation_band': z is not None and abs(z-self.y) <= self.half_width})

    def report(self):
        rows = []
        for phase in ('validation', 'training'):
            for side in ('joint', 'product'):
                selected = [r for r in self.records if r['phase'] == phase and r['side'] == side]
                rows.append({'phase': phase, 'side': side, 'count': len(selected),
                    'observation_kinds': dict(sorted(Counter(r['observation_kind'] for r in selected).items())),
                    'time_counts': {str(u): sum(r['reverse_time'] == u for r in selected) for u in original.GRID[:-1]},
                    'selected_within_fixed_band_count': sum(r['within_fixed_observation_band'] for r in selected)})
        return {'half_width': self.half_width, 'record_sha256': _digest(self.records),
                'record_count': len(self.records), 'groups': rows, 'records': self.records}


def _coordinate_derivatives(values, coordinates):
    import torch
    active = [i for i, c in enumerate(coordinates) if c.numel()]
    answer = {i: (0., 0.) for i in range(len(coordinates))}
    if not active or not values.requires_grad:
        return answer
    gradients = torch.autograd.grad(values.sum(), tuple(coordinates[i] for i in active),
                                    create_graph=True, retain_graph=True, allow_unused=True)
    for i, gradient in zip(active, gradients):
        if gradient is None:
            continue
        second = (torch.autograd.grad(gradient.sum(), coordinates[i], retain_graph=True,
                                      allow_unused=True)[0] if gradient.requires_grad else None)
        answer[i] = (float(gradient.detach().sum()), 0. if second is None else float(second.detach().sum()))
    return answer


def inspect_model(model, context, observed, key, check=lambda: None):
    """Actual native baseline/residual derivatives, without parameter mutation."""
    import torch
    from heterodiff.experiments.factorized_conditional_training import FactorizedObservation
    from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest
    before = _parameter_digest(model)
    observation = FactorizedObservation(observed, context.domain_id, context.task_id, context.context_bytes)
    with torch.no_grad():
        nuisance = float(model.nuisance((observation,))[0])
    roster = query_roster(key)
    rows = []
    for u in original.GRID:
        for start in range(0, len(roster), 4):
            check()
            batch = roster[start:start+4]
            states = tuple(row[2] for row in batch)
            times, observations = (u,)*len(batch), (observation,)*len(batch)
            coordinates = tuple(torch.tensor([] if event.coordinate is None else [event.coordinate],
                dtype=torch.float64, device='cpu', requires_grad=True) for state in states for event in state)
            baseline = model.baseline(states, times, observations, coordinates=coordinates)
            residual = model.residual(states, times, observations, coordinates=coordinates)
            bg = _coordinate_derivatives(baseline, coordinates)
            rg = _coordinate_derivatives(residual, coordinates)
            cursor = 0
            for i, (label, z, state) in enumerate(batch):
                bder, rder = (bg[cursor], rg[cursor]) if state else ((0., 0.), (0., 0.))
                cursor += len(state)
                b, r = float(baseline[i].detach()), float(residual[i].detach())
                rows.append({'time': u, 'state': label, 'coordinate': z,
                    'baseline_rn_log_likelihood': b, 'residual': r,
                    'physical_rn_log_likelihood': b+r, 'classifier_logit': b+r+nuisance,
                    'baseline_gradient': bder[0], 'baseline_hessian': bder[1],
                    'residual_gradient': rder[0], 'residual_hessian': rder[1],
                    'physical_gradient': bder[0]+rder[0], 'physical_hessian': bder[1]+rder[1]})
    _need(_parameter_digest(model) == before, 'diagnostic query mutated model parameters')
    return {'nuisance': nuisance, 'rows': rows, 'parameter_sha256': before}


def target_rows(oracle, key):
    from heterodiff.evaluation.continuous_fiber_grid_target import ContinuousFiberGridTarget
    numerical = ContinuousFiberGridTarget(oracle.spec, original.GRID)
    log_reference = math.log(oracle.observation_reference_density)
    rows = []
    for u in original.GRID:
        for label, z, _ in query_roster(key):
            category = 'OTHER' if label.startswith('OTHER') else label
            values = {}
            for name, source in (('continuous', oracle), ('numerical_grid', numerical)):
                value = source.log_likelihood_derivatives(u, category, z if category == 'CONTINUOUS' else None)
                values[name] = {**value, 'rn_log_likelihood': value['log_likelihood']-log_reference,
                               'classifier_logit': value['log_likelihood']-math.log(source.evidence())}
            rows.append({'time': u, 'state': label, 'coordinate': z, **values})
    return {'rows': rows, 'evidence': {'continuous': oracle.evidence(), 'numerical_grid': numerical.evidence()},
            'observation_reference_density': oracle.observation_reference_density,
            'numerical_target_scope': 'IDEAL_ZERO_BASE_MACRO_NODE_KERNEL_NOT_FINITE_RNG_OR_RESOURCE_REFUSAL'}


def summarize_queries(inspection, targets, value_bound):
    rows, exact = inspection['rows'], targets['rows']
    _need([(r['time'], r['state'], r['coordinate']) for r in rows] ==
          [(r['time'], r['state'], r['coordinate']) for r in exact], 'query/target roster mismatch')
    per_time = []
    for u in original.GRID:
        indices = [i for i, r in enumerate(rows) if r['time'] == u]
        empty = next(i for i in indices if rows[i]['state'] == 'EMPTY')
        sources = {}
        for name in ('continuous', 'numerical_grid'):
            errors = {}
            for prefix in ('baseline', 'physical'):
                errors[prefix] = {
                    'empty_centered_log_likelihood': error_summary([
                        (rows[i][prefix+'_rn_log_likelihood']-rows[empty][prefix+'_rn_log_likelihood'])-
                        (exact[i][name]['rn_log_likelihood']-exact[empty][name]['rn_log_likelihood'])
                        for i in indices if i != empty]),
                    'selected_coordinate_score': error_summary([rows[i][prefix+'_gradient']-exact[i][name]['gradient']
                        for i in indices if rows[i]['state'] == 'CONTINUOUS']),
                    'selected_coordinate_hessian': error_summary([rows[i][prefix+'_hessian']-exact[i][name]['hessian']
                        for i in indices if rows[i]['state'] == 'CONTINUOUS']),
                    'other_continuous_spurious_score': error_summary([rows[i][prefix+'_gradient']
                        for i in indices if rows[i]['state'] == 'OTHER_CONTINUOUS'])}
            errors['classifier_logit'] = error_summary([rows[i]['classifier_logit']-exact[i][name]['classifier_logit']
                                                       for i in indices])
            errors['capacity'] = capacity_summary([exact[i][name]['rn_log_likelihood'] for i in indices],
                [rows[i]['baseline_rn_log_likelihood'] for i in indices], value_bound, 1.-u)
            sources[name] = errors
        per_time.append({'time': u, 'gate': 1.-u, 'targets': sources,
            'residual_diameter': max(rows[i]['residual'] for i in indices)-min(rows[i]['residual'] for i in indices),
            'maximum_abs_residual': max(abs(rows[i]['residual']) for i in indices)})
    return {'scope': 'UNWEIGHTED_FIXED_QUERY_ERRORS_NOT_POSTERIOR_RISK_OR_ENDPOINT_BOUND', 'per_time': per_time}


def require_original_replay(archived, initial, final, population, updates, losses):
    comparisons = {'initial_parameter_sha256': initial == archived['initial_parameter_sha256'],
        'final_parameter_sha256': final == archived['final_parameter_sha256'],
        'population_law_id': population == archived['population_law_id'],
        'every_update_record': json.loads(_payload(updates)) == archived['updates'],
        'every_held_out_loss_record': losses == archived['held_out_paired_loss_curve']}
    _need(all(comparisons.values()), 'original fit replay mismatch: '+','.join(k for k,v in comparisons.items() if not v))
    return comparisons


def replay_route(archived, scenario, targets, check=lambda: None):
    from heterodiff.experiments.factorized_common_grid_pipeline import (
        CommonGridDeviceFactorizedBasePopulation, common_grid_train_conditional_step)
    from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest
    from heterodiff.experiments.factorized_device_qualification import _optimizer
    seed, method = archived['training_seed'], archived['route']
    ref, _, key, base, model, context, observed = original.fixture(scenario, seed, method)
    initial = _parameter_digest(model)
    population = CommonGridDeviceFactorizedBasePopulation(base, ref, original.GRID, context)
    coverage = ObservationCoverage(key, scenario[2])
    delegate = population.sample_pair
    def recording_pair(**kwargs):
        result = delegate(**kwargs)
        coverage.record(result[0], result[1])
        return result
    population.sample_pair = recording_pair
    validation = original.validation_pairs(population, seed, 32, check)
    coverage.phase = 'training'
    optimizer = _optimizer(model)
    losses, updates, inspections = [], [], []
    for step in range(33):
        check()
        if step:
            updates.append(common_grid_train_conditional_step(model, population, optimizer=optimizer,
                run_seed=original.seed_for(seed, 'training-paths'), record_id=f'update-{step}'.encode(), sample_count=2))
        if step in CHECKPOINTS:
            losses.append({'update': step, 'held_out_paired_loss': original.validation_loss(model, validation)})
            inspection = inspect_model(model, context, observed, key, check)
            inspection['summary'] = summarize_queries(inspection, targets, model.conditioner.architecture.value_bound)
            inspection['update'] = step
            inspections.append(inspection)
    final = _parameter_digest(model)
    binding = require_original_replay(archived, initial, final, population.law_id, updates, losses)
    _need(len(coverage.records) == 192, 'unexpected replay sample count')
    return {'scenario': scenario[0], 'method': method, 'training_seed': seed,
        'original_replay_checks': binding, 'initial_parameter_sha256': initial, 'final_parameter_sha256': final,
        'population_law_id': population.law_id, 'held_out_paired_loss_curve': losses,
        'observation_coverage': coverage.report(), 'checkpoints': inspections,
        'conditioner_value_bound': model.conditioner.architecture.value_bound,
        'residual_gate_policy': model.residual_gate_policy, 'new_endpoint_draws': 0}


def _write(path, record):
    with Path(path).open('xb') as stream:
        stream.write(json.dumps(record, sort_keys=True, indent=2, allow_nan=False).encode()+b'\n')


def run(archive, output, protocol, maximum_seconds=MAXIMUM_SECONDS):
    import numpy as np
    import scipy
    import torch
    from heterodiff.experiments.finite_conditional_learning_benchmark import _cpu_policy
    _need(type(maximum_seconds) is int and 1 <= maximum_seconds <= MAXIMUM_SECONDS, 'bounded CPU deadline required')
    payload = Path(archive).read_bytes()
    _need(hashlib.sha256(payload).hexdigest() == ARCHIVED_REPORT_SHA256, 'original report bytes differ')
    old = json.loads(payload)
    versions = {'python': platform.python_version(), 'torch': torch.__version__, 'numpy': np.__version__, 'scipy': scipy.__version__}
    verification_path = Path(archive).parent.parent/'continuous_multiseed_verification_2026_09_13.json'
    verification_bytes = verification_path.read_bytes()
    _need(hashlib.sha256(verification_bytes).hexdigest() == VERIFICATION_SHA256,
          'original environment verification bytes differ')
    expected_versions = json.loads(verification_bytes)['tests']['development_regression']['versions']
    _need(versions == expected_versions and all(old['environment'][k] == versions[k]
          for k in ('python', 'torch', 'numpy')), 'original replay environment differs')
    roster = [(s[0], seed, method) for s in original.SCENARIOS for seed in original.SEEDS for method in original.METHODS]
    fitted = [r for r in old['routes'] if r['kind'] == 'neural']
    _need([(r['scenario'], r['training_seed'], r['route']) for r in fitted] == roster, 'archived fit roster differs')
    protocol_hash = hashlib.sha256(Path(protocol).read_bytes()).hexdigest()
    source_hashes = {name: hashlib.sha256(Path(importlib.util.find_spec(name).origin).read_bytes()).hexdigest()
        for name in ('heterodiff.experiments.continuous_residual_diagnostic',
                     'heterodiff.evaluation.continuous_fiber_grid_target',
                     'heterodiff.evaluation.continuous_fiber_conditional_benchmark',
                     'heterodiff.experiments.continuous_multiseed_benchmark',
                     'heterodiff.experiments.factorized_common_grid_pipeline',
                     'heterodiff.experiments.factorized_device_training')}
    output = Path(output)
    _need(not output.exists() and output.parent.is_dir(), 'new output directory beneath existing parent required')
    output.mkdir()
    started = time.monotonic()
    def check():
        if time.monotonic()-started > maximum_seconds:
            raise TimeoutError('diagnostic CPU deadline exceeded')
    _write(output/'protocol.json', {'schema_version': SCHEMA, 'archive_sha256': ARCHIVED_REPORT_SHA256,
        'protocol_sha256': protocol_hash, 'maximum_seconds': maximum_seconds, 'roster': roster,
        'original_environment_verification_sha256': VERIFICATION_SHA256,
        'selected_source_sha256': source_hashes,
        'coordinates': COORDINATES, 'times': original.GRID, 'checkpoints': CHECKPOINTS})
    completed, targets = [], {}
    try:
        with _cpu_policy(torch):
            for scenario in original.SCENARIOS:
                _, oracle, key, _, _, _, _ = original.fixture(scenario, original.SEEDS[0], original.METHODS[0])
                targets[scenario[0]] = target_rows(oracle, key)
                for archived in (r for r in fitted if r['scenario'] == scenario[0]):
                    check()
                    route_started = time.monotonic()
                    record = replay_route(archived, scenario, targets[scenario[0]], check)
                    record['elapsed_seconds'] = time.monotonic()-route_started
                    completed.append(record)
                    _write(output/f'route-{len(completed):02d}.json', record)
                    print(json.dumps({'completed': len(completed), 'required': 12, 'scenario': scenario[0],
                        'seed': archived['training_seed'], 'method': archived['route'],
                        'replay_exact': True, 'elapsed_seconds': record['elapsed_seconds']}), flush=True)
        check()
        report = {'schema_version': SCHEMA, 'decision': 'COMPLETE_ORIGINAL_FIT_RESIDUAL_DIAGNOSIS',
            'archive_sha256': ARCHIVED_REPORT_SHA256, 'protocol_sha256': protocol_hash,
            'original_environment_verification_sha256': VERIFICATION_SHA256,
            'selected_source_sha256': source_hashes,
            'environment': versions, 'targets': targets, 'routes': completed,
            'elapsed_seconds': time.monotonic()-started, 'query_row_count': 5184,
            'replayed_optimizer_updates': 384, 'replayed_base_paths': 2304,
            'scope': {'diagnostic_only': True, 'post_outcome_explanatory_not_confirmatory': True,
                'original_fit_hashes_and_losses_reproduced': True, 'new_endpoint_draws': 0,
                'objective_model_capacity_gate_tolerances_changed': False, 'GPU_or_cloud_requested': False,
                'real_data_accessed': False, 'model_selection': False, 'retries': 0,
                'global_score_or_sampling_error_bound_claimed': False}}
        _write(output/'report.json', report)
        return report
    except Exception as error:
        _write(output/'failure.json', {'decision': 'DIAGNOSIS_INCOMPLETE', 'completed_routes': len(completed),
            'error_type': type(error).__name__, 'detail': str(error)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--child', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        run(args.archive, args.output, args.protocol)
    else:
        command = [sys.executable, '-m', __name__ if __name__ != '__main__' else
            'heterodiff.experiments.continuous_residual_diagnostic', '--archive', str(args.archive),
            '--output', str(args.output), '--protocol', str(args.protocol), '--child']
        try:
            result = subprocess.run(command, timeout=MAXIMUM_SECONDS, check=False)
        except subprocess.TimeoutExpired:
            print('DIAGNOSIS_INCOMPLETE: child deadline reached; partial files preserved', file=sys.stderr)
            raise SystemExit(2)
        raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
