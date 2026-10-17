"""One fixed FD7 score-only curvature comparison; no learner/sampler integration."""
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

from heterodiff.experiments import continuous_localized_residual as localized
from heterodiff.models.localized_fiber_residual import LocalizedFiberResidual
from heterodiff.models.localized_score_curvature import estimate_hessians_from_scores_fd7, fd7_weights


previous = localized.previous
SCHEMA = 'continuous-localized-fd7-curvature-comparison-v1'
ARM = 'VS_FD7_SIXTH_ORDER_SCORE_DIFFERENCES'
CORE, CORE_CELLS, COLLAR_WIDTH = (-4.5, 4.5), 256, 1.
MAXIMUM_SECONDS = 300
SCENARIOS, METHODS, GRID, TOLERANCES = previous.SCENARIOS, previous.METHODS, previous.GRID, previous.TOLERANCES
ARCHIVE_SHA256 = '5cfc1a95284ce1149dd3211799666988b8b0422807affec2961c26264ab4c099'
ARCHIVE_PROTOCOL_SHA256 = 'de45c892a45e67ccee208bb59077c58fe55e5bed9993fd5f876729db00ccc20e'
ARCHIVE_ARMS = ('VS_FINITE_DIFFERENCE', 'ORACLE_JET_VSH')
ARCHIVE_TARGET_MATCH_ATOL, ARCHIVE_TARGET_MATCH_RTOL = 2e-13, 2e-13
payload, digest = previous.payload, previous.digest


def construction_rosters():
    knots = np.linspace(*CORE, CORE_CELLS+1)
    evaluation = previous.collocation_rosters()[1]
    if np.min(np.abs(knots[:, None]-evaluation[None, :])) <= 1e-12:
        raise ArithmeticError('construction and evaluation locations overlap')
    return knots, evaluation


def specification():
    knots, evaluation = construction_rosters()
    return {'schema_version': SCHEMA, 'scenarios': previous.specification()['scenarios'],
        'methods': METHODS, 'arm': ARM, 'core_cells': CORE_CELLS,
        'core_knots': knots.tolist(), 'evaluation_coordinates': evaluation.tolist(), 'grid': GRID,
        'collar_width': COLLAR_WIDTH, 'tail_policy': 'C2_COLLARS_TO_SAME_ENDPOINT_VALUES_THEN_CONSTANT',
        'curvature_rule': 'DEGREE_SIX_SCORE_INTERPOLANT_DERIVATIVE_ON_SEVEN_KNOTS',
        'stencil_fraction_weights': {str(i): [[w.numerator, w.denominator] for w in fd7_weights(i)] for i in range(7)},
        'score_centering_before_weighted_sum': True,
        'oracle_hessian_labels_consumed': False, 'tolerances_changed': False,
        'approximation_tolerances': TOLERANCES, 'active_profile_count': 32,
        'terminal_zero_profile_count': 4, 'route_count': 4, 'maximum_seconds': MAXIMUM_SECONDS,
        'numerical_threads': 1, 'retries': 0, 'resolution_selection': False,
        'atomic_corrections': 'EXACT_ORACLE_CONSTANTS_NOT_LEARNED',
        'archive': {'report_sha256': ARCHIVE_SHA256, 'protocol_sha256': ARCHIVE_PROTOCOL_SHA256,
            'arms': ARCHIVE_ARMS, 'core_cells': 256, 'refit': False,
            'target_identity_check_atol': ARCHIVE_TARGET_MATCH_ATOL,
            'target_identity_check_rtol': ARCHIVE_TARGET_MATCH_RTOL,
            'target_identity_check_is_not_new_acceptance_tolerance': True},
        'same_knots_values_scores_target_baseline_as_archived_FD5': True,
        'VSH_archive_is_extra_supervision_not_primary': True,
        'collar_or_tail_target_accuracy_claimed': False,
        'time_interpolation': False, 'sampler_integration': False,
        'scientific_target': 'INDEPENDENT_ZERO_BASE_NUMERICAL_MACRO_GRID_LIKELIHOOD'}


def build_profile(knots, values, gradients, remaining_time, *, oracle_hessians=None):
    """Consume residual values and scores only; the gate is applied exactly once."""
    if oracle_hessians is not None:
        raise ValueError('FD7 primary must not consume oracle Hessian labels')
    if isinstance(remaining_time, bool) or not isinstance(remaining_time, (int, float)) or not math.isfinite(remaining_time) or not 0 < remaining_time <= 1:
        raise ValueError('active remaining time must lie in (0,1]')
    arrays = []
    for name, source in (('knots', knots), ('values', values), ('gradients', gradients)):
        raw = np.asarray(source)
        if np.ma.isMaskedArray(source) or raw.dtype.kind not in 'fiu' or raw.ndim != 1 or raw.size < 7:
            raise ValueError(f'{name} must be a real one-dimensional array with at least seven entries')
        array = np.asarray(raw, dtype=np.float64)
        if not np.isfinite(array).all():
            raise ValueError('finite representable inputs required')
        arrays.append(array)
    z, value, gradient = arrays
    if z.shape != value.shape or z.shape != gradient.shape:
        raise ValueError('aligned knot values and scores required')
    curvature = np.asarray(estimate_hessians_from_scores_fd7(tuple(z), tuple(gradient)))
    tau = float(remaining_time)
    model = LocalizedFiberResidual.from_jets(tuple(float(x) for x in z),
        tuple(float(x/tau) for x in value), tuple(float(x/tau) for x in gradient),
        tuple(float(x/tau) for x in curvature), tau, COLLAR_WIDTH)
    at_knots = model.evaluate(z)
    return model, {'arm': ARM, 'oracle_hessian_labels_consumed': False,
        'knots': z.tolist(), 'residual_values': value.tolist(), 'residual_scores': gradient.tolist(),
        'residual_curvatures_used': curvature.tolist(), 'remaining_time': tau,
        'full_knots_including_collars': list(model.knots), 'collar_width': COLLAR_WIDTH,
        'core_cell_count': len(z)-1, 'quotient_bezier_controls': [list(row) for row in model.controls],
        'knot_value_interpolation_max_abs': float(np.max(np.abs(at_knots['value']-value))),
        'knot_score_interpolation_max_abs': float(np.max(np.abs(at_knots['gradient']-gradient))),
        'knot_curvature_interpolation_max_abs': float(np.max(np.abs(at_knots['hessian']-curvature))),
        'coefficient_sha256': digest([list(row) for row in model.controls])}


def load_archive(path):
    """Read only the predeclared previous report; retain no alternative archive."""
    with Path(path).open('rb') as handle:
        raw = handle.read(64*1024*1024+1)
    if len(raw) > 64*1024*1024 or hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('previous report must match the predeclared archive SHA256')
    report = json.loads(raw)
    if (report.get('schema_version') != localized.SCHEMA
            or report.get('protocol_sha256') != ARCHIVE_PROTOCOL_SHA256
            or digest(report['protocol']) != ARCHIVE_PROTOCOL_SHA256):
        raise ValueError('previous protocol binding mismatch')
    controls = {}
    for route in report['routes']:
        if route['core_cells'] == CORE_CELLS and route['arm'] in ARCHIVE_ARMS:
            key = route['scenario'], route['method'], route['arm']
            if key in controls:
                raise ValueError('duplicate archived control route')
            controls[key] = route
    if set(controls) != {(s[0], m, a) for s in SCENARIOS for m in METHODS for a in ARCHIVE_ARMS}:
        raise ValueError('incomplete archived control roster')
    references = {row['scenario']: row for row in report['references']}
    return {'report_sha256': ARCHIVE_SHA256, 'size_bytes': len(raw), 'protocol_sha256': ARCHIVE_PROTOCOL_SHA256,
            'controls': controls, 'references': references}


def compare_archival_control(route, targets):
    """Reevaluate preserved physical arrays against the same current target; never refit."""
    if len(route['nodes']) != len(GRID) or tuple(row['u'] for row in route['nodes']) != GRID:
        raise ValueError('archived control node roster mismatch')
    nodes = []
    for row in route['nodes']:
        errors = previous.compare_arrays(row['physical'], targets[row['u']]['evaluation'])
        nodes.append({'u': row['u'], 'candidate_errors': errors,
            'archived_physical_arrays_sha256': digest(row['physical']),
            'archived_coefficient_sha256': row['construction'].get('coefficient_sha256')})
    return {'arm': route['arm'], 'core_cells': route['core_cells'],
        'source_route_ordinal': route['ordinal'], 'source_route_sha256': digest(route),
        'refit_performed': False, 'oracle_hessians_consumed_by_current_construction': False,
        'archived_control_used_extra_hessian_supervision': route['arm'] == 'ORACLE_JET_VSH',
        'nodes': nodes, 'active_probe_errors': aggregate_errors(nodes),
        'largest_whole_projection_real_absolute_bound': route['largest_whole_projection_real_absolute_bound']}


def aggregate_errors(nodes):
    result = {}
    for name in TOLERANCES:
        active = [row['candidate_errors'][name] for row in nodes[:-1]]
        result[name] = {'max_abs': max(row['max_abs'] for row in active),
            'rms': math.sqrt(sum(row['rms']**2 for row in active)/len(active)),
            'failure_count': sum(row['failure_count'] for row in active),
            'probe_count': sum(row['count'] for row in active)}
    return result


def _check_archived_targets(reference, targets):
    if tuple(row['u'] for row in reference['target_rows']) != GRID:
        raise ValueError('archived target node roster mismatch')
    maximum = 0.
    exact = True
    for row in reference['target_rows']:
        current = targets[row['u']]
        for name in TOLERANCES:
            old = np.asarray(row['evaluation'][name], dtype=np.float64)
            new = np.asarray(current['evaluation'][name], dtype=np.float64)
            if old.shape != new.shape or not np.isfinite(old).all() or not np.allclose(
                    old, new, atol=ARCHIVE_TARGET_MATCH_ATOL, rtol=ARCHIVE_TARGET_MATCH_RTOL):
                raise ValueError('archived numerical target differs from current oracle')
            maximum = max(maximum, float(np.max(np.abs(old-new))))
            exact = exact and bool(np.array_equal(old, new))
        for state in ('EMPTY', 'OTHER'):
            if not math.isclose(row['atoms'][state], current['atoms'][state],
                                abs_tol=ARCHIVE_TARGET_MATCH_ATOL, rel_tol=ARCHIVE_TARGET_MATCH_RTOL):
                raise ValueError('archived atomic target differs from current oracle')
    return {'all_continuous_target_arrays_bitwise_equal': exact, 'maximum_target_roundoff_difference': maximum,
            'same_mathematical_numerical_grid_target_checked': True}


def run_comparison(archive_report, check=lambda: None, on_route=lambda route: None):
    """Four fixed new constructions only. CLI supplies the 300-second hard deadline."""
    start = time.monotonic()
    archive = load_archive(archive_report)
    knots, evaluation = construction_rosters()
    routes, references = [], []
    with threadpool_limits(limits=1):
        for scenario in SCENARIOS:
            check()
            grid, uncapped, continuous = previous.target_bundle(scenario)
            targets = {u: {'evaluation': previous._rows(grid, u, evaluation),
                'knots': previous._rows(grid, u, knots),
                'atoms': {s: grid.log_likelihood_derivatives(u, s)['log_likelihood'] for s in ('EMPTY', 'OTHER')}} for u in GRID}
            reference_check = _check_archived_targets(archive['references'][scenario[0]], targets)
            references.append({'scenario': scenario[0], 'process': asdict(grid.spec),
                'grid_evidence': grid.evidence(), 'continuous_evidence': continuous.evidence(),
                'archived_target_identity': reference_check,
                'target_rows': [{'u': u, 'evaluation': previous._serialize_arrays(targets[u]['evaluation']),
                                'atoms': targets[u]['atoms']} for u in GRID],
                'continuous_vs_grid': [{'u': u, 'comparison': previous.compare_arrays(
                    previous._rows(continuous, u, evaluation), targets[u]['evaluation'])} for u in GRID]})
            for method in METHODS:
                nodes = []
                for u in GRID:
                    check()
                    tau, clock = 1-u, u if method == METHODS[0] else 1.
                    t = targets[u]
                    base_eval = previous._rows(uncapped, clock, evaluation, baseline=True)
                    base_atoms = {s: uncapped.uncapped_log_likelihood_derivatives(clock, s)['log_likelihood'] for s in ('EMPTY', 'OTHER')}
                    atoms = {s: t['atoms'][s]-base_atoms[s] for s in ('EMPTY', 'OTHER')}
                    if tau:
                        base_knots = previous._rows(uncapped, clock, knots, baseline=True)
                        model, construction = build_profile(knots, t['knots']['value']-base_knots['value'],
                            t['knots']['gradient']-base_knots['gradient'], tau)
                    else:
                        model = LocalizedFiberResidual.from_jets(CORE, (0., 0.), (0., 0.), (0., 0.), 0., COLLAR_WIDTH)
                        construction = {'terminal_zero_no_oracle_labels_consumed': True, 'remaining_time': 0.,
                            'full_knots_including_collars': list(model.knots), 'quotient_bezier_controls': [list(row) for row in model.controls]}
                        if any(abs(v) > 1e-12 for v in atoms.values()):
                            raise ArithmeticError('terminal atomic baseline/target mismatch')
                        atoms = {s: 0. for s in atoms}
                    residual = model.evaluate(evaluation)
                    physical = {key: base_eval[key]+residual[key] for key in TOLERANCES}
                    contrast = (physical['value']-base_atoms['EMPTY']-atoms['EMPTY'])-(t['evaluation']['value']-t['atoms']['EMPTY'])
                    nodes.append({'u': u, 'construction': construction,
                        'atomic_residuals_exact_oracle_not_learned': atoms, 'baseline_atoms': base_atoms,
                        'baseline': previous._serialize_arrays(base_eval), 'residual': previous._serialize_arrays(residual),
                        'physical': previous._serialize_arrays(physical),
                        'candidate_errors': previous.compare_arrays(physical, t['evaluation']),
                        'baseline_errors': previous.compare_arrays(base_eval, t['evaluation']),
                        'coefficient_and_derivative_bounds': localized.profile_bounds(model, atoms),
                        'relative_likelihood_error_max_abs': float(np.max(np.abs(np.expm1(physical['value']-t['evaluation']['value'])))),
                        'empty_centered_log_potential_error_max_abs': float(np.max(np.abs(contrast))),
                        'E_to_C_log_rate_ratio_error_max_abs': float(np.max(np.abs(contrast))),
                        'E_to_C_relative_rate_ratio_error_max_abs': float(np.max(np.abs(np.expm1(contrast))))})
                errors = aggregate_errors(nodes)
                route = {'ordinal': len(routes)+1, 'scenario': scenario[0], 'method': method, 'arm': ARM,
                    'core_cells': CORE_CELLS, 'nodes': nodes, 'active_probe_errors': errors,
                    'all_active_value_score_hessian_checks_passed': all(row['failure_count'] == 0 for row in errors.values()),
                    'largest_whole_projection_real_absolute_bound': max(row['coefficient_and_derivative_bounds']['whole_projection_real_absolute_bound'] for row in nodes),
                    'archival_controls': [compare_archival_control(archive['controls'][(scenario[0], method, arm)], targets) for arm in ARCHIVE_ARMS]}
                on_route(route)
                routes.append(route)
    check()
    return {'schema_version': SCHEMA, 'decision': 'FD7_CURVATURE_COMPARISON_COMPLETE_REVIEW_ACCURACY',
        'protocol': specification(), 'completed_routes': len(routes), 'completed_active_profiles': len(routes)*8,
        'completed_terminal_zero_profiles': len(routes), 'elapsed_seconds': time.monotonic()-start,
        'references': references, 'routes': routes,
        'archive_binding': {key: archive[key] for key in ('report_sha256', 'size_bytes', 'protocol_sha256')},
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
        'scope': {'synthetic_local_cpu_only': True, 'primary_consumed_oracle_hessian_labels': False,
            'archive_controls_refitted': False, 'old_model_or_tolerances_changed': False,
            'learner_or_sampler_integration': False, 'endpoint_sampling': False,
            'real_data_gpu_cloud_or_network_requested': False, 'time_interpolation_selected': False,
            'sampling_envelope_FP_certified': False, 'settings_selected_from_evaluation': False}}


def source_bindings():
    answer = localized.source_bindings()
    for path in (__file__, sys.modules[estimate_hessians_from_scores_fd7.__module__].__file__):
        answer[Path(path).name] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return answer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', action='store_true')
    parser.add_argument('--archive-report', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.inspect:
        print(payload(specification()).decode(), end='')
        return
    if args.output is None or args.archive_report is None:
        parser.error('--output and --archive-report are required unless --inspect is selected')
    destination, archive = args.output.absolute(), args.archive_report.absolute()
    if not args.worker:
        load_archive(archive)  # Reject the wrong saved control before creating output.
        if destination.exists() or not destination.parent.is_dir():
            parser.error('new output directory beneath an existing parent required')
        destination.mkdir()
        previous._write_new(destination/'protocol.json', specification())
        try:
            child = subprocess.run([sys.executable, '-m', 'heterodiff.experiments.continuous_localized_curvature',
                '--worker', '--archive-report', str(archive), '--output', str(destination)], timeout=MAXIMUM_SECONDS, check=False)
        except subprocess.TimeoutExpired:
            previous._write_new(destination/'failure.json', {'decision': 'INCOMPLETE_DEADLINE', 'maximum_seconds': MAXIMUM_SECONDS})
            raise SystemExit(1)
        if child.returncode:
            previous._write_new(destination/'failure.json', {'decision': 'INCOMPLETE_CHILD_FAILURE', 'returncode': child.returncode})
        raise SystemExit(child.returncode)
    start = time.monotonic()
    def check():
        if time.monotonic()-start > MAXIMUM_SECONDS:
            raise TimeoutError('soft curvature-comparison deadline')
    def save(route):
        previous._write_new(destination/f"route-{route['ordinal']:02d}.json", route)
    bindings = source_bindings()
    previous._write_new(destination/'execution.json', {'source_sha256': bindings,
        'protocol_sha256': digest(specification()), 'recorded_before_constructions': True})
    report = run_comparison(archive, check, save)
    if bindings != source_bindings():
        raise RuntimeError('source changed during comparison')
    report['source_sha256'], report['protocol_sha256'] = bindings, digest(report['protocol'])
    previous._write_new(destination/'report.json', report)
    print(json.dumps({key: report[key] for key in ('decision', 'completed_routes', 'completed_active_profiles', 'elapsed_seconds')}))


if __name__ == '__main__':
    main()
