"""Fixed oracle-supervised residual capacity comparison; no native learner repair.

Independent numerical-grid likelihood labels, disjoint deterministic probes,
all declared degrees/objectives, no endpoint sampler or data/cloud interface.
"""
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

from heterodiff.evaluation.continuous_fiber_conditional_benchmark import (
    ContinuousFiberSpec, ContinuousFiberConditionalBenchmark,
)
from heterodiff.evaluation.continuous_fiber_grid_target import ContinuousFiberGridTarget
from heterodiff.evaluation.continuous_fiber_initialization_diagnostic import ContinuousFiberInitializationDiagnostic
from heterodiff.models.compact_fiber_residual import CompactFiberResidual, design

SCHEMA = 'continuous-residual-capacity-comparison-v1'
SCENARIOS = (('reference-pressure', .8, .7), ('higher-pressure-shifted-observation', 2.5, 1.4))
METHODS = ('association-aware-guide-plus-residual', 'unified-direct-conditioner')
OBJECTIVES = ('VALUE_ONLY', 'VALUE_AND_SCORE')
DEGREES = (16, 32, 64)
GRID = tuple(i/8. for i in range(9))
SCALE = 2.
RCOND = 1e-12
MAXIMUM_SECONDS = 300
TOLERANCES = {'value': (2e-6, 2e-5), 'gradient': (2e-5, 2e-4), 'hessian': (1e-4, 1e-3)}


def payload(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False).encode()+b'\n'


def digest(value):
    return hashlib.sha256(payload(value)).hexdigest()


def collocation_rosters():
    k = np.arange(129, dtype=np.float64)
    train = SCALE*np.arctanh(np.tanh(4./SCALE)*np.cos(np.pi*(k+.5)/129))
    evaluation = np.linspace(-4., 4., 256)
    if np.min(np.abs(train[:, None]-evaluation[None, :])) <= 1e-12:
        raise ArithmeticError('training and evaluation coordinates overlap')
    return train, evaluation


def specification():
    train, evaluation = collocation_rosters()
    rho = 393217/524288
    specs = [asdict(ContinuousFiberSpec(theta=theta, observation_value=y,
        type_probabilities=(1-rho, rho))) for _, theta, y in SCENARIOS]
    return {'schema_version': SCHEMA, 'scenarios': [
        {'id': s[0], 'process': p} for s, p in zip(SCENARIOS, specs)],
        'methods': METHODS, 'objectives': OBJECTIVES, 'degrees': DEGREES,
        'grid': GRID, 'train_coordinates': train.tolist(),
        'evaluation_coordinates': evaluation.tolist(), 'coordinate_scale': SCALE,
        'coordinate_units': 'BENCHMARK_STANDARDIZED_LATENT_COORDINATE',
        'score_objective_weight': 1., 'hessian_supervised': False,
        'solver': 'FLOAT64_COLUMN_EQUILIBRATED_NUMPY_LSTSQ', 'rcond': RCOND,
        'ridge_regularization': 0., 'route_count': 24, 'continuous_fit_count': 192,
        'maximum_seconds': MAXIMUM_SECONDS, 'numerical_threads': 1,
        'approximation_tolerances': TOLERANCES,
        'tolerances_are_not_parity_or_endpoint_acceptance': True,
        'old_amplitude_lower_bound': .25, 'terminal_residual': 0.,
        'atomic_corrections': 'EXACT_ORACLE_CONSTANTS_NOT_LEARNED',
        'target': 'INDEPENDENT_ZERO_BASE_NUMERICAL_MACRO_GRID_LIKELIHOOD',
        'degree_selection_from_evaluation': False, 'sampler_integration': False}


def fit_residual(z, target_value, target_gradient, remaining_time, degree, objective):
    """Fit one fiber/node without access to any evaluation target."""
    if objective not in OBJECTIVES or degree not in DEGREES:
        raise ValueError('a declared objective and degree are required')
    if not math.isfinite(remaining_time) or not 0 < remaining_time <= 1:
        raise ValueError('an active remaining time in (0,1] is required')
    z, value, gradient = (np.asarray(x, dtype=np.float64) for x in (z, target_value, target_gradient))
    if z.ndim != 1 or len(z) <= degree or value.shape != z.shape or gradient.shape != z.shape:
        raise ValueError('aligned overdetermined one-dimensional collocation arrays required')
    if not all(np.isfinite(x).all() for x in (z, value, gradient)):
        raise ValueError('finite collocation inputs required')
    v, d, _ = design(z, degree, remaining_time=remaining_time, coordinate_scale=SCALE)
    matrix = v if objective == 'VALUE_ONLY' else np.vstack((v, d))
    rhs = value if objective == 'VALUE_ONLY' else np.concatenate((value, gradient))
    norms = np.linalg.norm(matrix, axis=0)
    if not np.isfinite(norms).all() or (norms == 0).any():
        raise ArithmeticError('invalid column normalization')
    scaled, _, rank, singular = np.linalg.lstsq(matrix/norms, rhs, rcond=RCOND)
    coefficients = scaled/norms
    model = CompactFiberResidual(tuple(float(c) for c in coefficients), remaining_time, SCALE)
    fitted = model.evaluate(z)
    value_mse = float(np.mean((fitted['value']-value)**2))
    gradient_mse = float(np.mean((fitted['gradient']-gradient)**2))
    return model, {'degree': degree, 'objective': objective, 'rank': int(rank),
        'column_count': degree+1, 'full_column_rank': bool(rank == degree+1),
        'equilibrated_singular_values': singular.tolist(),
        'equilibrated_condition_number': float(singular[0]/singular[-1]) if singular[-1] else None,
        'column_norms': norms.tolist(), 'rcond': RCOND,
        'train_value_mse': value_mse, 'train_score_mse': gradient_mse,
        'train_objective': value_mse+(gradient_mse if objective == 'VALUE_AND_SCORE' else 0.),
        'coefficients': coefficients.tolist(), 'coefficient_sha256': digest(coefficients.tolist()),
        'real_arithmetic_residual_envelope': model.real_arithmetic_bound,
        'floating_point_sampling_envelope_certified': False}


def compare_arrays(approximation, target):
    answer = {}
    for name, (atol, rtol) in TOLERANCES.items():
        a, t = np.asarray(approximation[name]), np.asarray(target[name])
        if a.shape != t.shape or not a.size or not np.isfinite(a).all() or not np.isfinite(t).all():
            raise ValueError('aligned nonempty finite comparison arrays required')
        error = a-t
        threshold = atol+rtol*np.abs(t)
        failures = np.abs(error) > threshold
        answer[name] = {'count': int(t.size), 'max_abs': float(np.max(np.abs(error))),
            'rms': float(np.sqrt(np.mean(error**2))), 'failure_count': int(failures.sum()),
            'passed_pointwise_approximation_tolerance': not bool(failures.any()),
            'atol': atol, 'rtol': rtol,
            'maximum_error_over_threshold': float(np.max(np.abs(error)/threshold))}
    return answer


def _rows(oracle, u, coordinates, *, baseline=False):
    function = oracle.uncapped_log_likelihood_derivatives if baseline else oracle.log_likelihood_derivatives
    values = [function(u, 'CONTINUOUS', float(z)) for z in coordinates]
    return {name: np.array([row[source] for row in values], dtype=np.float64)
        for name, source in (('value', 'log_likelihood'), ('gradient', 'gradient'), ('hessian', 'hessian'))}


def _serialize_arrays(arrays):
    return {name: values.tolist() for name, values in arrays.items()}


def target_bundle(scenario):
    if scenario not in SCENARIOS:
        raise ValueError('declared scenario required')
    rho = 393217/524288
    spec = ContinuousFiberSpec(theta=scenario[1], observation_value=scenario[2], type_probabilities=(1-rho, rho))
    return ContinuousFiberGridTarget(spec, GRID), ContinuousFiberInitializationDiagnostic(spec), ContinuousFiberConditionalBenchmark(spec)


def _capacity_floor(target, baseline, tau):
    correction = np.asarray(target)-np.asarray(baseline)
    diameter = float(np.max(correction)-np.min(correction))
    return {'required_correction_diameter': diameter, 'old_allowed_diameter': .5*tau,
        'old_class_uniform_error_lower_bound_any_gauge': max(0., diameter-.5*tau)/2}


def run_comparison(check=lambda: None, on_route=lambda route: None):
    """All fixed routes; API callback is soft only (CLI provides hard deadline)."""
    start = time.monotonic()
    train, evaluation = collocation_rosters()
    routes, references = [], []
    with threadpool_limits(limits=1):
        for scenario in SCENARIOS:
            grid, uncapped, continuous = target_bundle(scenario)
            targets = {u: {'train': _rows(grid, u, train), 'evaluation': _rows(grid, u, evaluation),
                'atoms': {s: grid.log_likelihood_derivatives(u, s)['log_likelihood'] for s in ('EMPTY', 'OTHER')}} for u in GRID}
            references.append({'scenario': scenario[0], 'process': asdict(grid.spec),
                'grid_evidence': grid.evidence(), 'continuous_evidence': continuous.evidence(),
                'continuous_vs_grid': [{'u': u, 'comparison': compare_arrays(_rows(continuous, u, evaluation), targets[u]['evaluation'])} for u in GRID],
                'target_rows': [{'u': u, 'train': _serialize_arrays(targets[u]['train']),
                    'evaluation': _serialize_arrays(targets[u]['evaluation']), 'atoms': targets[u]['atoms']} for u in GRID]})
            for method in METHODS:
                baseline = {u: {'train': _rows(uncapped, u if method == METHODS[0] else 1., train, baseline=True),
                    'evaluation': _rows(uncapped, u if method == METHODS[0] else 1., evaluation, baseline=True),
                    'atoms': {s: uncapped.uncapped_log_likelihood_derivatives(u if method == METHODS[0] else 1., s)['log_likelihood'] for s in ('EMPTY', 'OTHER')}} for u in GRID}
                for objective in OBJECTIVES:
                    for degree in DEGREES:
                        node_records = []
                        for u in GRID:
                            check()
                            tau = 1-u
                            t, b = targets[u], baseline[u]
                            atoms = {s: t['atoms'][s]-b['atoms'][s] for s in ('EMPTY', 'OTHER')}
                            if tau:
                                fitted, fit = fit_residual(train, t['train']['value']-b['train']['value'],
                                    t['train']['gradient']-b['train']['gradient'], tau, degree, objective)
                            else:
                                fitted = CompactFiberResidual((0.,), 0., SCALE)
                                fit = {'terminal_no_fit': True, 'coefficients': [0.],
                                    'real_arithmetic_residual_envelope': 0.}
                                if any(abs(v) > 1e-12 for v in atoms.values()):
                                    raise ArithmeticError('terminal baseline/target disagreement')
                                atoms = {s: 0. for s in atoms}
                            residual = fitted.evaluate(evaluation)
                            physical = {name: b['evaluation'][name]+residual[name] for name in TOLERANCES}
                            centered = physical['value']-(b['atoms']['EMPTY']+atoms['EMPTY'])
                            target_centered = t['evaluation']['value']-t['atoms']['EMPTY']
                            contrast_error = centered-target_centered
                            errors = compare_arrays(physical, t['evaluation'])
                            relative_h = np.expm1(physical['value']-t['evaluation']['value'])
                            node_records.append({'u': u, 'fit': fit, 'atomic_residuals_exact_oracle': atoms,
                                'baseline_atoms': b['atoms'], 'atomic_residuals_learned': False,
                                'baseline': _serialize_arrays(b['evaluation']),
                                'residual': _serialize_arrays(residual), 'physical': _serialize_arrays(physical),
                                'baseline_errors': compare_arrays(b['evaluation'], t['evaluation']),
                                'candidate_errors': errors,
                                'empty_centered_log_potential_error': {'max_abs': float(np.max(np.abs(contrast_error))),
                                    'rms': float(np.sqrt(np.mean(contrast_error**2)))},
                                'relative_likelihood_error_max_abs': float(np.max(np.abs(relative_h))),
                                'E_to_C_log_rate_ratio_error_max_abs': float(np.max(np.abs(contrast_error))),
                                'E_to_C_relative_rate_ratio_error_max_abs': float(np.max(np.abs(np.expm1(contrast_error)))),
                                'old_amplitude_obstruction': _capacity_floor(
                                    [*t['atoms'].values(), *t['evaluation']['value']],
                                    [*b['atoms'].values(), *b['evaluation']['value']], tau)})
                        aggregate = {}
                        for name in TOLERANCES:
                            active = [row['candidate_errors'][name] for row in node_records[:-1]]
                            aggregate[name] = {'max_abs': max(r['max_abs'] for r in active),
                                'rms': math.sqrt(sum(r['rms']**2 for r in active)/len(active)),
                                'failure_count': sum(r['failure_count'] for r in active),
                                'probe_count': sum(r['count'] for r in active)}
                        route = {'ordinal': len(routes)+1, 'scenario': scenario[0], 'method': method,
                            'objective': objective, 'degree': degree, 'nodes': node_records,
                            'active_probe_errors': aggregate,
                            'all_active_value_score_hessian_checks_passed': all(r['failure_count'] == 0 for r in aggregate.values()),
                            'rank_deficient_node_count': sum(not r['fit'].get('full_column_rank', True) for r in node_records),
                            'largest_real_arithmetic_envelope': max(r['fit']['real_arithmetic_residual_envelope'] for r in node_records)}
                        on_route(route)
                        routes.append(route)
    check()
    return {'schema_version': SCHEMA, 'decision': 'CONTROLLED_ORACLE_APPROXIMATION_COMPARISON_COMPLETE',
        'protocol': specification(), 'completed_routes': len(routes), 'completed_continuous_fits': len(routes)*8,
        'elapsed_seconds': time.monotonic()-start, 'references': references, 'routes': routes,
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
        'scope': {'synthetic_local_cpu_only': True, 'oracle_supervised': True,
            'native_neural_learner_replaced_or_qualified': False, 'old_BCE_learning_gap_closed': False,
            'sampler_or_endpoint_law_qualified': False, 'continuous_time_interpolation_selected': False,
            'real_data_gpu_cloud_or_network_requested': False, 'old_acceptance_tolerances_changed': False,
            'degree_selected_from_evaluation': False, 'sampling_envelope_FP_certified': False}}


def _write_new(path, value):
    encoded = payload(value)
    with path.open('xb') as handle:
        handle.write(encoded)


def source_bindings():
    paths = (__file__, sys.modules[CompactFiberResidual.__module__].__file__,
        sys.modules[ContinuousFiberGridTarget.__module__].__file__,
        sys.modules[ContinuousFiberInitializationDiagnostic.__module__].__file__,
        sys.modules[ContinuousFiberSpec.__module__].__file__)
    return {Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths}


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
        _write_new(destination/'protocol.json', specification())
        try:
            child = subprocess.run([sys.executable, '-m', __name__ if __name__ != '__main__' else
                'heterodiff.experiments.continuous_residual_capacity', '--worker', '--output', str(destination)],
                timeout=MAXIMUM_SECONDS, check=False)
        except subprocess.TimeoutExpired:
            _write_new(destination/'failure.json', {'decision': 'INCOMPLETE_DEADLINE', 'maximum_seconds': MAXIMUM_SECONDS})
            raise SystemExit(1)
        if child.returncode:
            _write_new(destination/'failure.json', {'decision': 'INCOMPLETE_CHILD_FAILURE', 'returncode': child.returncode})
        raise SystemExit(child.returncode)
    start = time.monotonic()
    def check():
        if time.monotonic()-start > MAXIMUM_SECONDS:
            raise TimeoutError('soft comparison deadline')
    def save(route):
        _write_new(destination/f"route-{route['ordinal']:02d}.json", route)
    bindings = source_bindings()
    _write_new(destination/'execution.json', {'source_sha256': bindings,
        'protocol_sha256': digest(specification()), 'recorded_before_fits': True})
    report = run_comparison(check, save)
    if bindings != source_bindings():
        raise RuntimeError('source changed during comparison; result not accepted')
    report['source_sha256'] = bindings
    report['protocol_sha256'] = digest(report['protocol'])
    _write_new(destination/'report.json', report)
    print(json.dumps({name: report[name] for name in ('decision', 'completed_routes', 'completed_continuous_fits', 'elapsed_seconds')}))


if __name__ == '__main__':
    main()
