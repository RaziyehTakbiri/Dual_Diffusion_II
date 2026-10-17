"""Fixed simulator-supervised localized likelihood comparison, CPU only.

All fits freeze before the independent backward target is imported/queried.
The new fixed-observation Poisson quasi-risk is not the old amortized BCE risk.
"""
from dataclasses import asdict
import argparse
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

from heterodiff.experiments.continuous_forward_labels import (
    ForwardSpec, GRID, design_states, rollout_labels, baseline_rows,
)
from heterodiff.models.localized_likelihood_learner import (
    LearnedLocalizedResidual, training_design, roughness_matrix, fit_likelihood,
    CELLS, SMOOTHNESS, RIDGE, MAXIMUM_ITERATIONS,
)

SCHEMA = 'continuous-localized-forward-learnability-v1'
SCENARIOS = (('reference-pressure', .8, .7), ('higher-pressure-shifted-observation', 2.5, 1.4))
METHODS = ('association-aware-guide-plus-residual', 'unified-direct-conditioner')
SEEDS = (11, 29, 47)
BUDGETS = (1024, 8192)
VALIDATION_SIZE = 4096
MAXIMUM_SECONDS = 1200
TOLERANCES = {'value': (2e-6, 2e-5), 'gradient': (2e-5, 2e-4), 'hessian': (1e-4, 1e-3)}


def payload(record):
    return json.dumps(record, sort_keys=True, indent=2, allow_nan=False).encode()+b'\n'


def digest(record):
    return hashlib.sha256(payload(record)).hexdigest()


def write_new(path, record):
    encoded = payload(record)
    with path.open('xb') as handle:
        handle.write(encoded)


def array_digest(*arrays):
    result = hashlib.sha256()
    for array in arrays:
        a = np.ascontiguousarray(array)
        result.update(str(a.shape).encode()+a.dtype.str.encode()+a.tobytes())
    return result.hexdigest()


def specification():
    return {'schema_version': SCHEMA, 'scenarios': [{'id': name, 'process': asdict(ForwardSpec(theta,y))} for name,theta,y in SCENARIOS],
        'methods': METHODS, 'seeds': SEEDS, 'nested_train_budgets_per_node': BUDGETS,
        'independent_validation_labels_per_node': VALIDATION_SIZE, 'grid': GRID,
        'design_probabilities': {'EMPTY': .25, 'OTHER': .25, 'CONTINUOUS': .5},
        'continuous_design': 'UNIFORM_MINUS_4_POINT_5_TO_4_POINT_5',
        'evaluation_coordinates': np.linspace(-4.,4.,256).tolist(),
        'family': 'QUINTIC_B_SPLINE_32_CELLS_TIED_THREE_EDGE_CONTROLS_C2_CONSTANT_TAILS',
        'continuous_cells': CELLS, 'continuous_free_coefficients': 33, 'atom_free_coefficients': 2,
        'physical_coefficient_bound': '2*log(known_maximum_label/known_contamination_density)',
        'quotient_coefficient_bound': 'physical_bound/(1-u)',
        'objective': 'mean((exp(b+Phi*a)-Y*(b+Phi*a))/known_maximum_label)+0.5*smoothness*aR*a+0.5*ridge*a*a',
        'smoothness': SMOOTHNESS, 'ridge': RIDGE, 'optimizer': 'SCIPY_L_BFGS_B_PHYSICAL_COEFFICIENTS',
        'optimizer_max_iterations': MAXIMUM_ITERATIONS, 'optimizer_ftol': 1e-12, 'optimizer_gtol': 1e-7,
        'optimizer_max_line_search': 30, 'initial_coefficients': 'ALL_ZERO_EACH_FIT',
        'label_source': 'FORWARD_HEUN_HALF_FULL_UNIFORMIZED_CTMC_HEUN_HALF_SUFFIX_AND_KNOWN_TERMINAL_G',
        'training_labels_include_backward_likelihood_or_derivatives': False,
        'paired_inputs_and_labels_across_methods': True, 'nested_samples_across_budgets': True,
        'validation_or_oracle_selects_settings_or_stopping': False,
        'oracle_import_and_queries_after_all_fits_frozen': True,
        'route_count': 24, 'fit_count': 192, 'unique_training_suffixes': 393216,
        'unique_validation_suffixes': 196608, 'unique_forward_suffixes': 589824,
        'approximation_tolerances': TOLERANCES, 'tolerances_are_statistical_success_guarantees': False,
        'sampler_integration': False, 'old_BCE_model_replaced': False,
        'maximum_seconds': MAXIMUM_SECONDS, 'numerical_threads': 1, 'retries': 0}


def _risk_vectors(maximum, *vectors):
    if isinstance(maximum, (bool, np.bool_)) or not np.isscalar(maximum) or not np.isrealobj(maximum):
        raise ValueError('positive finite maximum required')
    maximum = float(maximum)
    if not math.isfinite(maximum) or maximum <= 0:
        raise ValueError('positive finite maximum required')
    checked = []
    for vector in vectors:
        if np.ma.isMaskedArray(vector):
            raise ValueError('unmasked aligned finite vectors required')
        array = np.asarray(vector)
        if array.ndim != 1 or not array.size or array.dtype.kind not in 'iuf':
            raise ValueError('nonempty aligned real vectors required')
        array = np.asarray(array, dtype=np.float64)
        if not np.isfinite(array).all() or (checked and array.shape != checked[0].shape):
            raise ValueError('aligned finite vectors required')
        checked.append(array)
    return maximum, checked


def unpenalized_risk(potential, labels, maximum):
    maximum, (potential, labels) = _risk_vectors(maximum, potential, labels)
    value = float(np.mean(np.exp(potential)-labels*potential)/maximum)
    if not math.isfinite(value):
        raise ValueError('nonfinite risk')
    return value


def paired_risk_change(potential, baseline, labels, maximum, states):
    maximum, (potential, baseline, labels, states) = _risk_vectors(maximum, potential, baseline, labels, states)
    if not np.isin(states, (0,1,2)).all() or any(np.sum(states == state) < 2 for state in (0,1,2)):
        raise ValueError('valid states and two observations per stratum required')
    change = (np.exp(potential)-np.exp(baseline)-labels*(potential-baseline))/maximum
    if not np.isfinite(change).all():
        raise ValueError('nonfinite paired risk change')
    variance = sum((np.mean(states==state)**2)*change[states==state].var(ddof=1)/np.sum(states==state)
        for state in (0,1,2))
    return {'mean': float(change.mean()),
        'stratified_standard_error_descriptive': float(math.sqrt(variance)),
        'negative_means_improved': True, 'confidence_interval_or_multiple_testing_claim': False}


def make_dataset(spec, scenario_index, seed, node, split):
    size = max(BUDGETS) if split == 0 else VALIDATION_SIZE
    design_rng = np.random.default_rng(np.random.SeedSequence([20260913, scenario_index, seed, node, split, 0]))
    label_rng = np.random.default_rng(np.random.SeedSequence([20260913, scenario_index, seed, node, split, 1]))
    states, coordinates = design_states(size, design_rng)
    labels, work = rollout_labels(spec, GRID[node], states, coordinates, label_rng)
    return {'states': states, 'coordinates': coordinates, 'labels': labels,
        'sha256': array_digest(states, coordinates, labels), 'work': work,
        'rng_namespace': [20260913, scenario_index, seed, node, split]}


def train_all(check=lambda: None, on_dataset=lambda r: None, on_frozen=lambda r: None):
    """No evaluation-module import; validation loss is reporting only."""
    routes, dataset_records = [], []
    roughness = roughness_matrix()
    for scenario_index, (name, theta, y) in enumerate(SCENARIOS):
        spec = ForwardSpec(theta, y)
        for seed in SEEDS:
            datasets = []
            for node, u in enumerate(GRID[:-1]):
                check()
                pair = [make_dataset(spec, scenario_index, seed, node, split) for split in (0,1)]
                row = {'ordinal': len(dataset_records)+1, 'scenario': name, 'seed': seed, 'u': u,
                    'splits': [{**{k:v for k,v in data.items() if k not in ('states','coordinates','labels')},
                        **{k:data[k].tolist() for k in ('states','coordinates','labels')}} for data in pair]}
                on_dataset(row)
                dataset_records.append({k:v for k,v in row.items() if k != 'splits'} | {
                    'record_sha256': digest(row), 'split_sha256': [x['sha256'] for x in pair],
                    'work': [x['work'] for x in pair]})
                datasets.append(pair)
            for method in METHODS:
                # Fixed model offset only; no backward numerical target or its
                # derivatives/evidence are available in this training phase.
                offsets = [[baseline_rows(spec,u,d['states'],d['coordinates'],method)['value'] for d in pair]
                    for u,pair in zip(GRID[:-1],datasets)]
                features = [[training_design(d['states'],d['coordinates']) for d in pair] for pair in datasets]
                for budget in BUDGETS:
                    nodes = []
                    for node,u in enumerate(GRID[:-1]):
                        check()
                        train, validation = datasets[node]
                        b_train,b_validation = offsets[node]
                        x_train,x_validation = features[node]
                        model, fit = fit_likelihood(x_train[:budget],train['labels'][:budget],b_train[:budget],
                            1-u,spec.maximum_label,spec.contamination_density,roughness)
                        train_potential = b_train[:budget]+x_train[:budget]@fit['physical_coefficients']
                        validation_potential = b_validation+x_validation@fit['physical_coefficients']
                        nodes.append({'u': u, 'fit': fit, 'train_budget': budget,
                            'training_prefix_sha256': array_digest(train['states'][:budget],train['coordinates'][:budget],train['labels'][:budget]),
                            'training_full_dataset_sha256': train['sha256'], 'validation_dataset_sha256': validation['sha256'],
                            'training_risk': unpenalized_risk(train_potential,train['labels'][:budget],spec.maximum_label),
                            'training_baseline_risk': unpenalized_risk(b_train[:budget],train['labels'][:budget],spec.maximum_label),
                            'validation_risk': unpenalized_risk(validation_potential,validation['labels'],spec.maximum_label),
                            'validation_baseline_risk': unpenalized_risk(b_validation,validation['labels'],spec.maximum_label),
                            'validation_paired_change': paired_risk_change(validation_potential,b_validation,validation['labels'],spec.maximum_label,validation['states']),
                            'model_real_absolute_bound': model.real_absolute_bound})
                    route = {'ordinal':len(routes)+1,'scenario':name,'seed':seed,'method':method,'train_budget':budget,
                        'process':asdict(spec),'nodes':nodes,'all_models_frozen_before_backward_oracle':True}
                    on_frozen(route)
                    routes.append(route)
    return routes,dataset_records


def evaluate_frozen(routes, check=lambda: None, on_route=lambda r: None):
    """Independent numerical likelihood is first accessed here, after fitting."""
    from heterodiff.experiments.continuous_residual_capacity import target_bundle, compare_arrays
    evaluation = np.linspace(-4.,4.,256)
    states = np.r_[np.array((0,1)),np.full(256,2)].astype(np.int64)
    coordinates = np.r_[0.,0.,evaluation]
    targets = {}
    for scenario in SCENARIOS:
        oracle,_,_ = target_bundle(scenario)
        targets[scenario[0]] = {}
        for u in GRID:
            rows = [oracle.log_likelihood_derivatives(u,('EMPTY','OTHER','CONTINUOUS')[s],float(z) if s==2 else None) for s,z in zip(states,coordinates)]
            targets[scenario[0]][u] = {key:np.array([r[source] for r in rows]) for key,source in
                (('value','log_likelihood'),('gradient','gradient'),('hessian','hessian'))}
    evaluated = []
    for route in routes:
        spec = ForwardSpec(**route['process'])
        nodes = []
        for index,u in enumerate(GRID):
            check()
            if u < 1:
                fit = route['nodes'][index]['fit']
                model = LearnedLocalizedResidual(tuple(fit['coefficients']),1-u,fit['quotient_coefficient_bound'])
            else:
                model = LearnedLocalizedResidual((0.,)*35,0.,1.)
            baseline = baseline_rows(spec,u,states,coordinates,route['method'])
            residual = model.evaluate(states,coordinates)
            physical = {k:baseline[k]+residual[k] for k in TOLERANCES}
            target = targets[route['scenario']][u]
            errors = compare_arrays({k:v[2:] for k,v in physical.items()},{k:v[2:] for k,v in target.items()})
            base_errors = compare_arrays({k:v[2:] for k,v in baseline.items()},{k:v[2:] for k,v in target.items()})
            nodes.append({'u':u,'baseline':{k:v.tolist() for k,v in baseline.items()},
                'residual':{k:v.tolist() for k,v in residual.items()},'physical':{k:v.tolist() for k,v in physical.items()},
                'target':{k:v.tolist() for k,v in target.items()},'continuous_errors':errors,'continuous_baseline_errors':base_errors,
                'atomic_log_value_errors':(physical['value'][:2]-target['value'][:2]).tolist(),
                'empty_centered_log_potential_error_max_abs':float(np.max(abs((physical['value']-physical['value'][0])-(target['value']-target['value'][0])))),
                'model_real_absolute_bound':model.real_absolute_bound})
        aggregate = {}
        for key in TOLERANCES:
            aggregate[key] = {kind:{'max_abs':max(n[kind][key]['max_abs'] for n in nodes[:-1]),
                'rms':math.sqrt(sum(n[kind][key]['rms']**2 for n in nodes[:-1])/8),
                'failure_count':sum(n[kind][key]['failure_count'] for n in nodes[:-1]),'probe_count':2048}
                for kind in ('continuous_errors','continuous_baseline_errors')}
        record = {**route,'evaluation_nodes':nodes,'active_errors':aggregate,
            'mean_validation_risk_change':float(np.mean([n['validation_paired_change']['mean'] for n in route['nodes']])),
            'solver_success_count':sum(n['fit']['solver_success'] for n in route['nodes']),
            'maximum_projected_gradient':max(n['fit']['projected_gradient_max_abs'] for n in route['nodes']),
            'all_continuous_tolerances_passed':all(v['continuous_errors']['failure_count']==0 for v in aggregate.values())}
        on_route(record)
        evaluated.append(record)
    return evaluated


def run_comparison(check=lambda:None,on_dataset=lambda r:None,on_frozen=lambda r:None,on_route=lambda r:None,on_barrier=lambda r:None):
    start = time.monotonic()
    with threadpool_limits(limits=1):
        frozen,datasets = train_all(check,on_dataset,on_frozen)
        barrier = {'frozen_routes':len(frozen),'frozen_models':sum(len(r['nodes']) for r in frozen),
            'frozen_records_sha256':digest(frozen),'backward_target_queried_during_training':False}
        on_barrier(barrier)
        routes = evaluate_frozen(frozen,check,on_route)
    return {'schema_version':SCHEMA,'decision':'CONTROLLED_LEARNABILITY_COMPARISON_COMPLETE_REVIEW_ERRORS',
        'protocol':specification(),'datasets':datasets,'freeze_barrier':barrier,'routes':routes,
        'completed_routes':len(routes),'completed_fits':sum(len(r['nodes']) for r in routes),
        'elapsed_seconds':time.monotonic()-start,'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
        'scope':{'fixed_observation_simulator_supervised':True,'amortized_BCE_learner_repaired':False,
            'independent_backward_target_used_for_training_or_selection':False,'forward_terminal_states_simulated_for_labels':True,
            'learned_conditional_sampler_or_paths_executed':False,'real_data_GPU_cloud_or_network':False,
            'statistical_superiority_or_derivative_guarantee':False,'old_models_targets_and_tolerances_changed':False}}


def source_bindings():
    root = Path(__file__).resolve().parents[1]
    paths = ('experiments/continuous_localized_learnability.py','experiments/continuous_forward_labels.py',
        'models/localized_likelihood_learner.py','experiments/continuous_residual_capacity.py',
        'evaluation/continuous_fiber_grid_target.py','evaluation/continuous_fiber_conditional_benchmark.py',
        'evaluation/continuous_fiber_initialization_diagnostic.py')
    return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect',action='store_true')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.inspect:
        print(payload(specification()).decode(),end='')
        return
    if args.output is None:
        parser.error('new --output directory required')
    out = args.output.absolute()
    if not args.worker:
        if out.exists() or not out.parent.is_dir():
            parser.error('new output beneath an existing parent required')
        out.mkdir()
        write_new(out/'protocol.json',specification())
        try:
            child = subprocess.run([sys.executable,'-m','heterodiff.experiments.continuous_localized_learnability','--worker','--output',str(out)],
                timeout=MAXIMUM_SECONDS,check=False)
        except subprocess.TimeoutExpired:
            write_new(out/'failure.json',{'decision':'INCOMPLETE_DEADLINE','maximum_seconds':MAXIMUM_SECONDS})
            raise SystemExit(1)
        if child.returncode:
            write_new(out/'failure.json',{'decision':'INCOMPLETE_CHILD_FAILURE','returncode':child.returncode})
        raise SystemExit(child.returncode)
    start = time.monotonic()
    def check():
        if time.monotonic()-start > MAXIMUM_SECONDS:
            raise TimeoutError('comparison soft deadline')
    def save_frozen(route):
        write_new(out/f"frozen-{route['ordinal']:02d}.json",route)
        print(json.dumps({'phase':'fit_frozen','route':route['ordinal']}),flush=True)
    bindings = source_bindings()
    write_new(out/'execution.json',{'source_sha256':bindings,'protocol_sha256':digest(specification()),'before_training':True})
    report = run_comparison(check,lambda r:write_new(out/f"dataset-{r['ordinal']:02d}.json",r),save_frozen,
        lambda r:write_new(out/f"route-{r['ordinal']:02d}.json",r),lambda r:write_new(out/'freeze-barrier.json',r))
    if source_bindings()!=bindings:
        raise RuntimeError('source changed during comparison')
    report['source_sha256'],report['protocol_sha256'] = bindings,digest(specification())
    write_new(out/'report.json',report)
    print(json.dumps({k:report[k] for k in ('decision','completed_routes','completed_fits','elapsed_seconds')}))


if __name__ == '__main__':
    main()
