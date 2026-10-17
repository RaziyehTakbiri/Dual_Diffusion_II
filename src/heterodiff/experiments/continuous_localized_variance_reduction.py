"""Prospective paired forward-label Rao--Blackwell comparison; no learner change.

The computational match is the identical marked jump skeleton at each fixed
suffix budget, not equal FLOPs or wall time. Both label arms are generated in
one paired pass. All fits freeze before independent target evaluation.
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
    ForwardSpec, GRID, design_states, baseline_rows,
)
from heterodiff.experiments.continuous_rao_blackwell_labels import paired_rollout_labels
from heterodiff.experiments.continuous_localized_learnability import (
    SCENARIOS, METHODS, SEEDS, BUDGETS, VALIDATION_SIZE, TOLERANCES,
    payload, digest, write_new, array_digest, unpenalized_risk, paired_risk_change,
    evaluate_frozen,
)
from heterodiff.models.localized_likelihood_learner import (
    training_design, roughness_matrix, fit_likelihood, risk_value_gradient,
    SMOOTHNESS, RIDGE,
)

SCHEMA = 'continuous-localized-rao-blackwell-comparison-v1'
ARMS = ('RAW', 'RAO_BLACKWELL')
MAXIMUM_SECONDS = 1200
FAMILY_FAILURE_PROBABILITY = .05
UNIQUE_NOISE_COMPARISONS = 96


def specification():
    return {'schema_version': SCHEMA,
        'scenarios': [dict(id=s[0], process=asdict(ForwardSpec(*s[1:]))) for s in SCENARIOS],
        'methods': METHODS, 'seeds': SEEDS, 'nested_budgets': BUDGETS,
        'arms': ARMS, 'grid': GRID, 'validation_size': VALIDATION_SIZE,
        'route_count': 48, 'fit_count': 384, 'dataset_pair_count': 48,
        'unique_training_skeletons': 393216, 'unique_validation_skeletons': 196608,
        'unique_total_skeletons': 589824, 'evaluation_coordinates': np.linspace(-4.,4.,256).tolist(),
        'design': 'BALANCED_E_O_C_C_WITH_C_UNIFORM_MINUS_4_POINT_5_TO_4_POINT_5',
        'design_rng_namespace': '[20260913,scenario,seed,node,split,0] (unchanged coordinates)',
        'skeleton_rng_namespace': '[20260913,731,scenario,seed,node,split,0]',
        'gaussian_rng_namespace': '[20260913,731,scenario,seed,node,split,1]',
        'raw_arm_is_new_paired_control_not_old_archive': True,
        'label_estimator': 'CONDITIONAL_EXPECTATION_OVER_GAUSSIAN_NOISE_GIVEN_MARKED_JUMP_SKELETON',
        'target': 'UNCHANGED_ZERO_BASE_CAP_ONE_HEUN_HALF_FULL_CTMC_HEUN_HALF_GRID',
        'fit': {'family_cells':32, 'coefficients':35, 'smoothness':SMOOTHNESS, 'ridge':RIDGE,
            'physical_box':'2*log(M/c)', 'initial':'ZERO', 'optimizer':'UNCHANGED_fit_likelihood_L_BFGS_B',
            'maxiter':200, 'maxls':30, 'ftol':1e-12, 'gtol':1e-7},
        'work_match': 'EXACT_SAME_SUFFIXES_MARKED_JUMP_PROPOSALS_ACCEPTANCES_AND_HEUN_UPDATE_ROSTER',
        'equal_flops_random_draws_wall_time_or_actual_optimizer_evaluations_claimed': False,
        'paired_generation_cost_reported_once_not_standalone_arm_timings': True,
        'primary_validation_labels': 'SHARED_INDEPENDENT_RAO_BLACKWELL',
        'secondary_validation_labels': 'SHARED_INDEPENDENT_RAW',
        'all_fits_frozen_before_backward_oracle': True,
        'primary_comparisons': ['PAIRED_ROUTE_VALUE_SCORE_HESSIAN_RMS', 'PAIRED_VALIDATION_RISK',
            'REALIZED_LABEL_MSE_AND_EMPIRICAL_GRADIENT_NOISE', 'EXPECTED_REMOVED_GRADIENT_COVARIANCE_ESTIMATE'],
        'uncertainty': {'paired_training_seeds':3, 'seed_summaries':'DESCRIPTIVE_NOT_SUPERIORITY_INFERENCE',
            'derivative_bound':'RIDGE_STRONG_CONVEXITY_AND_COORDINATE_HOEFFDING_UNION_BOUND',
            'family_failure_probability':FAMILY_FAILURE_PROBABILITY,
            'unique_noise_comparisons':UNIQUE_NOISE_COMPARISONS,
            'same_noise_event_covers_both_methods':True,
            'bound_not_total_bias_or_floating_point_certificate':True},
        'tolerances':TOLERANCES, 'tolerances_changed':False,
        'retries':0, 'maximum_seconds':MAXIMUM_SECONDS, 'threads':1,
        'oracle_or_validation_selects_settings_or_stopping':False,
        'learner_sampler_real_data_GPU_cloud_network_or_release_changed':False}


def derivative_noise_bound(features, maximum, minimum, derivative_features):
    """Real-arithmetic theorem evaluated in floats, NOT an interval certificate.

    Conditional on fixed design, simultaneous over 96 noise problems and both
    arms: coordinate Hoeffding + union bound, then ridge strong convexity. Label
covariance reduction is a separate theorem; this worst-case bound is shared.
"""
    if np.ma.isMaskedArray(features):
        raise ValueError('unmasked finite feature matrix required')
    x = np.asarray(features)
    if (x.ndim != 2 or x.shape[1] != 35 or not len(x) or x.dtype.kind not in 'fiu'
            or not np.isfinite(x).all()):
        raise ValueError('finite n by 35 feature matrix required')
    if (any(isinstance(v,(bool,np.bool_,str,bytes)) or not np.isscalar(v) or not np.isrealobj(v)
            or not math.isfinite(float(v)) for v in (maximum,minimum))
            or not 0 < minimum < maximum):
        raise ValueError('positive ordered label bounds required')
    maximum, minimum = float(maximum), float(minimum)
    with np.errstate(over='ignore',invalid='ignore'):
        x = x.astype(np.float64)
    if not np.isfinite(x).all():
        raise ValueError('float64 representable features required')
    # 2 signs * 35 coordinates * 96 problems * 2 label arms.
    logarithm = math.log(2*35*UNIQUE_NOISE_COMPARISONS*len(ARMS)/FAMILY_FAILURE_PROBABILITY)
    with np.errstate(over='ignore',invalid='ignore'):
        eps = ((maximum-minimum)/maximum/len(x))*np.sqrt(.5*np.sum(x*x,axis=0)*logarithm)
        radius = float(np.linalg.norm(eps)/RIDGE)
    if not np.isfinite(eps).all() or not math.isfinite(radius):
        raise ValueError('representable concentration bound required')
    box = 2*(math.log(maximum)-math.log(minimum))
    radius = min(radius,2*box*math.sqrt(35))
    responses = {}
    if set(derivative_features) != set(TOLERANCES):
        raise ValueError('three derivative feature matrices required')
    for name, design in derivative_features.items():
        if np.ma.isMaskedArray(design):
            raise ValueError('finite derivative matrix required')
        d = np.asarray(design)
        if d.ndim != 2 or d.shape[1] != 35 or not len(d) or d.dtype.kind not in 'fiu' or not np.isfinite(d).all():
            raise ValueError('finite derivative matrix required')
        with np.errstate(over='ignore',invalid='ignore'):
            d = d.astype(np.float64)
        if not np.isfinite(d).all():
            raise ValueError('float64 representable derivative matrix required')
        responses[name] = {'maximum_probe_error_bound':float(np.max(np.linalg.norm(d,axis=1))*radius),
            'rms_probe_error_bound':float(np.linalg.norm(d,ord=2)/math.sqrt(len(d))*radius)}
        if not all(math.isfinite(v) for v in responses[name].values()):
            raise ValueError('representable derivative response required')
    return {'family_failure_probability':FAMILY_FAILURE_PROBABILITY,
        'gradient_noise_l2_bound':float(np.linalg.norm(eps)), 'ridge_curvature_lower_bound':RIDGE,
        'coefficient_distance_bound_with_box_cap':radius, 'derivative_responses':responses,
        'scope':'EXACT_EMPIRICAL_LABEL_OPTIMUM_VS_SAME_DESIGN_CONDITIONAL_MEAN_OPTIMUM',
        'optimizer_error_bias_and_floating_point_not_included':True,
        'raw_and_rb_share_conservative_bound':True, 'floating_point_interval_certificate':False}


def make_dataset(spec, scenario_index, seed, node, split):
    size = max(BUDGETS) if split == 0 else VALIDATION_SIZE
    states, coordinates = design_states(size,np.random.default_rng(
        np.random.SeedSequence([20260913,scenario_index,seed,node,split,0])))
    namespace = [20260913,731,scenario_index,seed,node,split]
    start = time.monotonic()
    raw, rb, work = paired_rollout_labels(spec,GRID[node],states,coordinates,
        np.random.default_rng(np.random.SeedSequence(namespace+[0])),
        np.random.default_rng(np.random.SeedSequence(namespace+[1])))
    duration = time.monotonic()-start
    conditional_variance = np.asarray(work.pop('conditional_raw_label_variance'),dtype=np.float64)
    counts = work.pop('per_suffix_counts')
    terminal_gaussian_state = work.pop('terminal_gaussian_state')
    return {'states':states.tolist(), 'coordinates':coordinates.tolist(),
        'RAW':raw.tolist(), 'RAO_BLACKWELL':rb.tolist(),
        'conditional_raw_label_variance':conditional_variance.tolist(),
        'per_suffix_counts':counts, 'work':work, 'terminal_gaussian_state':terminal_gaussian_state,
        'paired_generation_seconds':duration,
        'rng_namespace':namespace, 'design_sha256':array_digest(states,coordinates),
        'payload_sha256':array_digest(states,coordinates,raw,rb,conditional_variance)}


def train_all(check=lambda:None,on_dataset=lambda r:None,on_frozen=lambda r:None):
    routes, records = [], []
    roughness = roughness_matrix()
    for si, (name,theta,y) in enumerate(SCENARIOS):
        spec = ForwardSpec(theta,y)
        for seed in SEEDS:
            datasets = []
            for ni,u in enumerate(GRID[:-1]):
                check()
                splits = [make_dataset(spec,si,seed,ni,split) for split in (0,1)]
                record = {'ordinal':len(records)+1,'scenario':name,'seed':seed,'u':u,'splits':splits}
                on_dataset(record)
                records.append(record)
                datasets.append(splits)
            for method in METHODS:
                features = [[training_design(d['states'],d['coordinates']) for d in pair] for pair in datasets]
                baselines = [[baseline_rows(spec,u,d['states'],d['coordinates'],method)['value'] for d in pair]
                    for u,pair in zip(GRID[:-1],datasets)]
                for budget in BUDGETS:
                    for arm in ARMS:
                        nodes = []
                        for ni,u in enumerate(GRID[:-1]):
                            check()
                            train,valid = datasets[ni]
                            x,xv = features[ni]
                            b,bv = baselines[ni]
                            labels = np.asarray(train[arm])[:budget]
                            started = time.monotonic()
                            model,fit = fit_likelihood(x[:budget],labels,b[:budget],1-u,
                                spec.maximum_label,spec.contamination_density,roughness)
                            fit_seconds = time.monotonic()-started
                            a = np.asarray(fit['physical_coefficients'])
                            predicted = bv+xv@a
                            val_rb,val_raw = np.asarray(valid['RAO_BLACKWELL']),np.asarray(valid['RAW'])
                            _,gradient = risk_value_gradient(a,x[:budget],labels,b[:budget],1.,spec.maximum_label,roughness)
                            box = fit['physical_coefficient_bound']
                            box_gap = max(0.,float(gradient@a+box*np.sum(abs(gradient))))
                            nodes.append({'u':u,'fit':fit,'fit_seconds':fit_seconds,
                                'train_budget':budget,'design_prefix_sha256':array_digest(
                                    np.asarray(train['states'],dtype=np.int64)[:budget],np.asarray(train['coordinates'])[:budget]),
                                'training_labels_sha256':array_digest(labels),
                                'paired_dataset_payload_sha256':train['payload_sha256'],
                                'matched_skeleton_prefix_work':{k:int(np.sum(v[:budget])) for k,v in train['per_suffix_counts'].items()},
                                'validation_paired_change':paired_risk_change(predicted,bv,val_rb,spec.maximum_label,valid['states']),
                                'raw_validation_paired_change':paired_risk_change(predicted,bv,val_raw,spec.maximum_label,valid['states']),
                                'validation_risk':unpenalized_risk(predicted,val_rb,spec.maximum_label),
                                'optimizer_box_gap_upper_bound':box_gap,
                                'optimizer_coefficient_distance_bound':min(2*box*math.sqrt(35),math.sqrt(2*box_gap/RIDGE)),
                                'optimizer_bound_is_floating_point_estimate':True,
                                'model_real_absolute_bound':model.real_absolute_bound})
                        route = {'ordinal':len(routes)+1,'scenario':name,'seed':seed,'method':method,
                            'train_budget':budget,'arm':arm,'process':asdict(spec),'nodes':nodes,
                            'all_models_frozen_before_backward_oracle':True}
                        on_frozen(route)
                        routes.append(route)
    return routes,records


def postfit_label_diagnostics(records,check=lambda:None):
    from heterodiff.experiments.continuous_residual_capacity import target_bundle
    targets = {s[0]:target_bundle(s)[0] for s in SCENARIOS}
    probes = np.linspace(-4.,4.,256)
    derivative_features = {k:training_design(np.full(256,2),probes,i) for i,k in enumerate(TOLERANCES)}
    results = []
    for record in records:
        check()
        spec = ForwardSpec(*next(s[1:] for s in SCENARIOS if s[0]==record['scenario']))
        data = record['splits'][0]
        states,z = np.asarray(data['states']),np.asarray(data['coordinates'])
        target = targets[record['scenario']]
        h = np.array([math.exp(target.log_likelihood_derivatives(record['u'],('EMPTY','OTHER','CONTINUOUS')[int(s)],
            float(v) if s==2 else None)['log_likelihood']) for s,v in zip(states,z)])
        x = training_design(states,z)
        v = np.asarray(data['conditional_raw_label_variance'])
        for budget in BUDGETS:
            xi,hi = x[:budget],h[:budget]
            removed = xi.T@(v[:budget,None]*xi)/(budget*spec.maximum_label)**2
            arm_metrics = {}
            for arm in ARMS:
                error = np.asarray(data[arm])[:budget]-hi
                noise = xi.T@error/(budget*spec.maximum_label)
                arm_metrics[arm] = {'label_mse_against_independent_mean':float(np.mean(error**2)),
                    'label_bias_realized_mean':float(np.mean(error)),
                    'empirical_gradient_noise':noise.tolist(),'empirical_gradient_noise_l2':float(np.linalg.norm(noise))}
            results.append({'scenario':record['scenario'],'seed':record['seed'],'u':record['u'],'budget':budget,
                'arms':arm_metrics,'mean_removed_conditional_label_variance':float(np.mean(v[:budget])),
                'removed_gradient_covariance_estimate':removed.tolist(),
                'removed_gradient_covariance_trace':float(np.trace(removed)),
                'covariance_estimate_not_confidence_certificate':True,
                'noise_bound':derivative_noise_bound(xi,spec.maximum_label,spec.contamination_density,derivative_features)})
    return results


def summarize_pairs(routes):
    index = {(r['scenario'],r['method'],r['seed'],r['train_budget'],r['arm']):r for r in routes}
    if len(index) != len(routes) or any(k[-1] not in ARMS for k in index):
        raise ValueError('unique known route arms required')
    pairs = []
    for key in index:
        if key[-1] != 'RAW':
            continue
        if key[:-1]+('RAO_BLACKWELL',) not in index:
            raise ValueError('both paired arms required')
        raw,rb = index[key],index[key[:-1]+('RAO_BLACKWELL',)]
        pairs.append({'scenario':key[0],'method':key[1],'seed':key[2],'budget':key[3],
            'errors':{k:{'raw_rms':raw['active_errors'][k]['continuous_errors']['rms'],
                'rb_rms':rb['active_errors'][k]['continuous_errors']['rms'],
                'rb_over_raw_rms':(rb['active_errors'][k]['continuous_errors']['rms']/raw['active_errors'][k]['continuous_errors']['rms']
                    if raw['active_errors'][k]['continuous_errors']['rms'] else None)}
                for k in TOLERANCES},
            'validation_risk_rb_minus_raw':float(np.mean([b['validation_risk']-a['validation_risk'] for a,b in zip(raw['nodes'],rb['nodes'])])),
            'exact_shared_design_and_skeleton':all(a['design_prefix_sha256']==b['design_prefix_sha256']
                and a['paired_dataset_payload_sha256']==b['paired_dataset_payload_sha256']
                and a['matched_skeleton_prefix_work']==b['matched_skeleton_prefix_work'] for a,b in zip(raw['nodes'],rb['nodes']))})
    if len(pairs)*2 != len(routes):
        raise ValueError('both paired arms required')
    return pairs


def run_comparison(check=lambda:None,on_dataset=lambda r:None,on_frozen=lambda r:None,
        on_barrier=lambda r:None,on_route=lambda r:None):
    start = time.monotonic()
    with threadpool_limits(limits=1):
        frozen,records = train_all(check,on_dataset,on_frozen)
        barrier = {'frozen_routes':len(frozen),'frozen_models':sum(len(r['nodes']) for r in frozen),
            'frozen_records_sha256':digest(frozen),'backward_target_queried_during_training':False}
        on_barrier(barrier)
        routes = evaluate_frozen(frozen,check,on_route)
        diagnostics = postfit_label_diagnostics(records,check)
        pairs = summarize_pairs(routes)
    return {'schema_version':SCHEMA,'decision':'MATCHED_SKELETON_VARIANCE_REDUCTION_COMPARISON_COMPLETE_REVIEW_ERRORS',
        'protocol':specification(),'freeze_barrier':barrier,'routes':routes,'paired_comparisons':pairs,
        'label_diagnostics':diagnostics,
        'datasets':[{'ordinal':r['ordinal'],'scenario':r['scenario'],'seed':r['seed'],'u':r['u'],
            'record_sha256':digest(r),'splits':[{k:d[k] for k in ('design_sha256','payload_sha256','work','paired_generation_seconds')} for d in r['splits']]}
            for r in records],
        'completed_routes':len(routes),'completed_fits':sum(len(r['nodes']) for r in routes),
        'elapsed_seconds':time.monotonic()-start,
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
        'scope':{'local_cpu_synthetic_only':True,'unchanged_learner_penalties_family_and_tolerances':True,
            'no_sampler_or_real_data_or_GPU_or_cloud':True,'same_skeleton_not_equal_flop_or_walltime':True,
            'neural_BASE_generalization_or_statistical_superiority_claimed':False}}


def source_bindings():
    root = Path(__file__).resolve().parents[1]
    paths = ('experiments/continuous_localized_variance_reduction.py','experiments/continuous_rao_blackwell_labels.py',
        'experiments/continuous_forward_labels.py','experiments/continuous_localized_learnability.py',
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
        parser.error('new output directory required')
    out = args.output.absolute()
    if not args.worker:
        if out.exists() or not out.parent.is_dir():
            parser.error('new directory beneath existing parent required')
        out.mkdir()
        write_new(out/'protocol.json',specification())
        try:
            child = subprocess.run([sys.executable,'-m',__spec__.name,'--worker','--output',str(out)],
                timeout=MAXIMUM_SECONDS,check=False)
        except subprocess.TimeoutExpired:
            write_new(out/'failure.json',{'decision':'INCOMPLETE_DEADLINE','seconds':MAXIMUM_SECONDS})
            raise SystemExit(1)
        if child.returncode:
            write_new(out/'failure.json',{'decision':'INCOMPLETE_CHILD_FAILURE','returncode':child.returncode})
        raise SystemExit(child.returncode)
    if json.loads((out/'protocol.json').read_bytes()) != json.loads(payload(specification())):
        raise RuntimeError('prospective protocol mismatch')
    start = time.monotonic()
    def check():
        if time.monotonic()-start > MAXIMUM_SECONDS:
            raise TimeoutError('comparison soft deadline')
    def freeze(r):
        write_new(out/f"frozen-{r['ordinal']:02d}.json",r)
        print(json.dumps({'phase':'fit_frozen','route':r['ordinal']}),flush=True)
    bindings = source_bindings()
    write_new(out/'execution.json',{'source_sha256':bindings,'protocol_sha256':digest(specification()),'before_training':True})
    report = run_comparison(check,lambda r:write_new(out/f"dataset-{r['ordinal']:02d}.json",r),freeze,
        lambda r:write_new(out/'freeze-barrier.json',r),lambda r:write_new(out/f"route-{r['ordinal']:02d}.json",r))
    if source_bindings() != bindings:
        raise RuntimeError('source changed during comparison')
    report.update(source_sha256=bindings,protocol_sha256=digest(specification()))
    write_new(out/'report.json',report)
    print(json.dumps({k:report[k] for k in ('decision','completed_routes','completed_fits','elapsed_seconds')}))


if __name__ == '__main__':
    main()
