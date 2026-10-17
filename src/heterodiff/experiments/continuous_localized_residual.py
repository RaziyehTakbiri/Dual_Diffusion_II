"""Fixed localized C2 residual comparison, not neural or sampler integration."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import scipy
from threadpoolctl import threadpool_limits

from heterodiff.experiments import continuous_residual_capacity as previous
from heterodiff.models.localized_fiber_residual import (
    LocalizedFiberResidual, estimate_hessians_from_scores,
)

SCHEMA = 'continuous-localized-residual-comparison-v1'
ARMS = ('VS_FINITE_DIFFERENCE', 'ORACLE_JET_VSH')
CELLS = (64, 128, 256)
CORE = (-4.5, 4.5)
COLLAR_WIDTH = 1.
MAXIMUM_SECONDS = 300
SCENARIOS, METHODS, GRID = previous.SCENARIOS, previous.METHODS, previous.GRID
TOLERANCES = previous.TOLERANCES
payload, digest = previous.payload, previous.digest


def construction_rosters():
    evaluation = previous.collocation_rosters()[1]
    knots = {n: np.linspace(*CORE, n+1) for n in CELLS}
    for values in knots.values():
        if np.min(np.abs(values[:, None]-evaluation[None, :])) <= 1e-12:
            raise ArithmeticError('construction and evaluation locations overlap')
    return knots, evaluation


def specification():
    knots, evaluation = construction_rosters()
    return {'schema_version': SCHEMA,
        'scenarios': previous.specification()['scenarios'], 'methods': METHODS,
        'arms': ARMS, 'primary_arm': ARMS[0], 'cells': CELLS,
        'core_knots': {str(n): z.tolist() for n, z in knots.items()},
        'evaluation_coordinates': evaluation.tolist(), 'grid': GRID,
        'coordinate_units': 'BENCHMARK_STANDARDIZED_LATENT_COORDINATE',
        'coordinate_compactification': None, 'collar_width': COLLAR_WIDTH,
        'tail_policy': 'C2_COLLARS_TO_SAME_ENDPOINT_VALUES_THEN_CONSTANT',
        'VS_curvature': 'FOURTH_ORDER_FIVE_POINT_SCORE_DIFFERENCES_SHARED_AT_KNOTS',
        'VSH_curvature': 'EXACT_ORACLE_HESSIAN_EXTRA_SUPERVISION',
        'continuous_profile_count': 192, 'terminal_zero_profiles': 24, 'route_count': 24,
        'approximation_tolerances': TOLERANCES, 'tolerances_changed': False,
        'collars_and_tails_oracle_accuracy_claimed': False,
        'atomic_corrections': 'EXACT_ORACLE_CONSTANTS_NOT_LEARNED',
        'time_interpolation': False, 'sampler_integration': False,
        'evaluation_selected_resolution': False, 'maximum_seconds': MAXIMUM_SECONDS,
        'numerical_threads': 1, 'basis_only_causal_comparison_claimed': False,
        'matched_label_or_compute_budget_claimed': False}


def build_profile(knots, values, gradients, remaining_time, *, arm, oracle_hessians=None):
    """Consume values/scores only for the primary; reject accidental Hessian labels.

    Input jets describe d, not d/tau. The quotient is formed exactly once here.
    Evaluation coordinates and target Hessians are not arguments to this routine.
    """
    if arm not in ARMS:
        raise ValueError('a declared arm is required')
    if isinstance(remaining_time, bool) or not isinstance(remaining_time, (int, float)) or not math.isfinite(remaining_time) or not 0 < remaining_time <= 1:
        raise ValueError('an active remaining time in (0,1] is required')
    arrays = []
    for name, source in (('knots', knots), ('values', values), ('gradients', gradients)):
        raw = np.asarray(source)
        if np.ma.isMaskedArray(source) or raw.dtype.kind not in 'fiu' or raw.ndim != 1 or raw.size < 5:
            raise ValueError(f'{name} must be a real one-dimensional array with at least five entries')
        array = np.asarray(raw, dtype=np.float64)
        if not np.isfinite(array).all():
            raise ValueError('finite representable inputs required')
        arrays.append(array)
    z, value, gradient = arrays
    if value.shape != z.shape or gradient.shape != z.shape:
        raise ValueError('aligned knot jets required')
    if arm == ARMS[0]:
        if oracle_hessians is not None:
            raise ValueError('primary arm must not consume oracle Hessian labels')
        curvature = np.array(estimate_hessians_from_scores(tuple(z), tuple(gradient)))
    else:
        if oracle_hessians is None:
            raise ValueError('oracle-jet control requires explicit Hessian labels')
        raw = np.asarray(oracle_hessians)
        if np.ma.isMaskedArray(oracle_hessians) or raw.dtype.kind not in 'fiu' or raw.shape != z.shape:
            raise ValueError('aligned real oracle Hessian labels required')
        curvature = np.asarray(raw, dtype=np.float64)
        if not np.isfinite(curvature).all():
            raise ValueError('finite oracle Hessian labels required')
    tau = float(remaining_time)
    model = LocalizedFiberResidual.from_jets(tuple(float(x) for x in z),
        tuple(float(x/tau) for x in value), tuple(float(x/tau) for x in gradient),
        tuple(float(x/tau) for x in curvature), tau, COLLAR_WIDTH)
    evaluated = model.evaluate(z)
    return model, {'arm': arm, 'oracle_hessian_labels_consumed': arm == ARMS[1],
        'knots': z.tolist(), 'residual_values': value.tolist(),
        'residual_scores': gradient.tolist(), 'residual_curvatures_used': curvature.tolist(),
        'remaining_time': tau, 'full_knots_including_collars': list(model.knots),
        'quotient_bezier_controls': [list(row) for row in model.controls],
        'collar_width': COLLAR_WIDTH, 'core_cell_count': len(z)-1,
        'knot_value_interpolation_max_abs': float(np.max(np.abs(evaluated['value']-value))),
        'knot_score_interpolation_max_abs': float(np.max(np.abs(evaluated['gradient']-gradient))),
        'knot_curvature_interpolation_max_abs': float(np.max(np.abs(evaluated['hessian']-curvature))),
        'coefficient_sha256': digest([list(row) for row in model.controls])}


def profile_bounds(model, atomic_residuals):
    """Whole projected roster bounds, all collars/tails included; real arithmetic."""
    controls = np.asarray(model.controls, dtype=np.float64)*model.remaining_time
    widths = np.diff(model.knots)
    lower, upper = float(np.min(controls)), float(np.max(controls))
    first = 5*np.diff(controls, axis=1)/widths[:, None]
    second = 20*np.diff(controls, n=2, axis=1)/widths[:, None]**2
    atoms = [float(v) for v in atomic_residuals.values()]
    if not all(math.isfinite(v) for v in atoms) or not np.isfinite(first).all() or not np.isfinite(second).all():
        raise ArithmeticError('nonfinite profile bound')
    mixed_lower, mixed_upper = min([lower, *atoms]), max([upper, *atoms])
    return {'continuous_real_absolute_bound': model.real_arithmetic_bound,
        'continuous_real_range': [lower, upper], 'mixed_real_range': [mixed_lower, mixed_upper],
        'whole_projection_real_absolute_bound': max(abs(mixed_lower), abs(mixed_upper)),
        'whole_projection_real_oscillation_bound': mixed_upper-mixed_lower,
        'continuous_real_score_absolute_bound': float(np.max(np.abs(first))),
        'continuous_real_hessian_absolute_bound': float(np.max(np.abs(second))),
        'includes_core_collars_tails_and_atomic_values': True,
        'floating_point_outward_certificate': False, 'used_by_sampler': False}


def run_comparison(check=lambda: None, on_route=lambda route: None):
    start = time.monotonic()
    knots, evaluation = construction_rosters()
    routes, references = [], []
    with threadpool_limits(limits=1):
        for scenario in SCENARIOS:
            grid, uncapped, continuous = previous.target_bundle(scenario)
            targets = {u: {'evaluation': previous._rows(grid, u, evaluation),
                'knots': {n: previous._rows(grid, u, z) for n, z in knots.items()},
                'atoms': {s: grid.log_likelihood_derivatives(u, s)['log_likelihood'] for s in ('EMPTY', 'OTHER')}} for u in GRID}
            references.append({'scenario': scenario[0], 'process': asdict(grid.spec),
                'grid_evidence': grid.evidence(), 'continuous_evidence': continuous.evidence(),
                'target_rows': [{'u': u, 'evaluation': previous._serialize_arrays(targets[u]['evaluation']),
                    'atoms': targets[u]['atoms']} for u in GRID],
                'continuous_vs_grid': [{'u': u, 'comparison': previous.compare_arrays(
                    previous._rows(continuous, u, evaluation), targets[u]['evaluation'])} for u in GRID]})
            for method in METHODS:
                baseline = {u: {'evaluation': previous._rows(uncapped, u if method == METHODS[0] else 1., evaluation, baseline=True),
                    'knots': {n: previous._rows(uncapped, u if method == METHODS[0] else 1., z, baseline=True) for n, z in knots.items()},
                    'atoms': {s: uncapped.uncapped_log_likelihood_derivatives(u if method == METHODS[0] else 1., s)['log_likelihood'] for s in ('EMPTY', 'OTHER')}} for u in GRID}
                for arm in ARMS:
                    for n in CELLS:
                        node_records = []
                        for u in GRID:
                            check()
                            tau = 1-u
                            t, b = targets[u], baseline[u]
                            atoms = {s: t['atoms'][s]-b['atoms'][s] for s in ('EMPTY', 'OTHER')}
                            if tau:
                                correction = {key: t['knots'][n][key]-b['knots'][n][key] for key in TOLERANCES}
                                model, construction = build_profile(knots[n], correction['value'], correction['gradient'], tau,
                                    arm=arm, oracle_hessians=correction['hessian'] if arm == ARMS[1] else None)
                            else:
                                model = LocalizedFiberResidual.from_jets(CORE, (0., 0.), (0., 0.), (0., 0.), 0., COLLAR_WIDTH)
                                construction = {'terminal_zero_no_oracle_labels_consumed': True,
                                    'remaining_time': 0., 'full_knots_including_collars': list(model.knots),
                                    'quotient_bezier_controls': [list(row) for row in model.controls]}
                                if any(abs(v) > 1e-12 for v in atoms.values()):
                                    raise ArithmeticError('terminal atomic baseline/target mismatch')
                                atoms = {s: 0. for s in atoms}
                            residual = model.evaluate(evaluation)
                            physical = {name: b['evaluation'][name]+residual[name] for name in TOLERANCES}
                            error = previous.compare_arrays(physical, t['evaluation'])
                            log_error = physical['value']-t['evaluation']['value']
                            contrast_error = (physical['value']-b['atoms']['EMPTY']-atoms['EMPTY'])-(t['evaluation']['value']-t['atoms']['EMPTY'])
                            node_records.append({'u': u, 'construction': construction,
                                'atomic_residuals_exact_oracle_not_learned': atoms, 'baseline_atoms': b['atoms'],
                                'baseline': previous._serialize_arrays(b['evaluation']),
                                'residual': previous._serialize_arrays(residual), 'physical': previous._serialize_arrays(physical),
                                'baseline_errors': previous.compare_arrays(b['evaluation'], t['evaluation']),
                                'candidate_errors': error, 'coefficient_and_derivative_bounds': profile_bounds(model, atoms),
                                'relative_likelihood_error_max_abs': float(np.max(np.abs(np.expm1(log_error)))),
                                'empty_centered_log_potential_error_max_abs': float(np.max(np.abs(contrast_error))),
                                'E_to_C_log_rate_ratio_error_max_abs': float(np.max(np.abs(contrast_error))),
                                'E_to_C_relative_rate_ratio_error_max_abs': float(np.max(np.abs(np.expm1(contrast_error))))})
                        aggregate = {}
                        for name in TOLERANCES:
                            active = [row['candidate_errors'][name] for row in node_records[:-1]]
                            aggregate[name] = {'max_abs': max(r['max_abs'] for r in active),
                                'rms': math.sqrt(sum(r['rms']**2 for r in active)/len(active)),
                                'failure_count': sum(r['failure_count'] for r in active),
                                'probe_count': sum(r['count'] for r in active)}
                        route = {'ordinal': len(routes)+1, 'scenario': scenario[0], 'method': method,
                            'arm': arm, 'core_cells': n, 'nodes': node_records, 'active_probe_errors': aggregate,
                            'all_active_value_score_hessian_checks_passed': all(r['failure_count'] == 0 for r in aggregate.values()),
                            'largest_continuous_real_absolute_bound': max(r['coefficient_and_derivative_bounds']['continuous_real_absolute_bound'] for r in node_records),
                            'largest_whole_projection_real_absolute_bound': max(r['coefficient_and_derivative_bounds']['whole_projection_real_absolute_bound'] for r in node_records),
                            'largest_whole_projection_real_oscillation_bound': max(r['coefficient_and_derivative_bounds']['whole_projection_real_oscillation_bound'] for r in node_records)}
                        on_route(route)
                        routes.append(route)
    check()
    return {'schema_version': SCHEMA, 'decision': 'LOCALIZED_RESIDUAL_COMPARISON_COMPLETE_REVIEW_ACCURACY',
        'protocol': specification(), 'completed_routes': len(routes), 'completed_active_profiles': len(routes)*8,
        'completed_terminal_zero_profiles': len(routes), 'elapsed_seconds': time.monotonic()-start,
        'references': references, 'routes': routes,
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
        'scope': {'synthetic_local_cpu_only': True, 'old_model_or_tolerances_changed': False,
            'primary_consumed_oracle_hessian_labels': False, 'control_consumed_oracle_hessian_labels': True,
            'native_BCE_learner_repaired_or_qualified': False, 'sampler_or_endpoint_law_qualified': False,
            'time_interpolation_selected': False, 'sampling_envelope_FP_certified': False,
            'real_data_gpu_cloud_or_network_requested': False, 'basis_only_causal_claim': False,
            'knots_or_arm_selected_from_evaluation': False}}


def source_bindings():
    result = previous.source_bindings()
    for path in (__file__, sys.modules[LocalizedFiberResidual.__module__].__file__):
        result[Path(path).name] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.inspect:
        print(payload(specification()).decode(), end='')
        return
    if args.output is None:
        parser.error('--output is required unless --inspect is selected')
    destination = args.output.absolute()
    if not args.worker:
        if destination.exists() or not destination.parent.is_dir():
            parser.error('new output directory beneath an existing parent required')
        destination.mkdir()
        previous._write_new(destination/'protocol.json', specification())
        try:
            child = subprocess.run([sys.executable, '-m', 'heterodiff.experiments.continuous_localized_residual',
                '--worker', '--output', str(destination)], timeout=MAXIMUM_SECONDS, check=False)
        except subprocess.TimeoutExpired:
            previous._write_new(destination/'failure.json', {'decision': 'INCOMPLETE_DEADLINE', 'maximum_seconds': MAXIMUM_SECONDS})
            raise SystemExit(1)
        if child.returncode:
            previous._write_new(destination/'failure.json', {'decision': 'INCOMPLETE_CHILD_FAILURE', 'returncode': child.returncode})
        raise SystemExit(child.returncode)
    start = time.monotonic()
    def check():
        if time.monotonic()-start > MAXIMUM_SECONDS:
            raise TimeoutError('soft comparison deadline')
    def save(route):
        previous._write_new(destination/f"route-{route['ordinal']:02d}.json", route)
    bindings = source_bindings()
    previous._write_new(destination/'execution.json', {'source_sha256': bindings,
        'protocol_sha256': digest(specification()), 'recorded_before_constructions': True})
    report = run_comparison(check, save)
    if bindings != source_bindings():
        raise RuntimeError('source changed during comparison')
    report['source_sha256'] = bindings
    report['protocol_sha256'] = digest(report['protocol'])
    previous._write_new(destination/'report.json', report)
    print(json.dumps({name: report[name] for name in ('decision', 'completed_routes', 'completed_active_profiles', 'elapsed_seconds')}))


if __name__ == '__main__':
    main()
