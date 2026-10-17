"""Fixed oracle-control diagnosis of archived localized likelihood fits.

No learner amendment: separate realized optimizer, label, design, penalty and
likelihood-projection contrasts, preserving cross terms and numerical limits.
"""
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

from heterodiff.experiments.continuous_forward_labels import ForwardSpec, GRID, baseline_rows
from heterodiff.experiments.continuous_localized_learnability import (
    SCENARIOS, METHODS, SEEDS, BUDGETS, TOLERANCES, array_digest, digest, payload, write_new,
)
from heterodiff.models.localized_likelihood_learner import training_design, roughness_matrix, SMOOTHNESS, RIDGE
from heterodiff.experiments.localized_population_risk import (
    fit_weighted_risk, population_quadrature, weighted_risk_terms, global_bound_diagnostics,
)

SCHEMA = 'continuous-localized-error-decomposition-v1'
ARCHIVE_SHA256 = 'd8db24c1c4f2d22069da8ec15640cd9b553dfec5f3ecf87b5f0530069289a692'
ARCHIVE_PROTOCOL_SHA256 = 'c99b27fbd042359f65f54cd7c191a4bdd28e98f62303ad341fcdb8287ee8036e'
QUADRATURE_LEVELS = (16, 32)
PRIMARY_QUADRATURE = 32
MAXIMUM_SECONDS = 1200
TERMS = ('optimizer_stopping', 'realized_label_noise', 'realized_design_variation',
         'combined_regularization', 'fixed_family_risk_projection')
STAGES = ('A', 'N', 'M', 'P', 'U', 'T')


def specification():
    return {'schema_version': SCHEMA, 'archive_report_sha256': ARCHIVE_SHA256,
        'archive_protocol_sha256': ARCHIVE_PROTOCOL_SHA256,
        'scenarios': SCENARIOS, 'methods': METHODS, 'seeds': SEEDS, 'budgets': BUDGETS,
        'grid': GRID, 'evaluation_coordinates': np.linspace(-4., 4., 256).tolist(),
        'representation_and_box': 'UNCHANGED_35_PHYSICAL_COEFFICIENTS_32_CELL_QUINTIC_2_LOG_M_OVER_C_BOX',
        'stages': {'A': 'ARCHIVED_NOISY_EMPIRICAL_FIT', 'N': 'STRICT_SAME_NOISY_OBJECTIVE_CONTROL',
            'M': 'STRICT_SAME_DESIGN_EXACT_CONDITIONAL_MEAN_LABEL_CONTROL',
            'P': 'QUADRATURE_POPULATION_PENALIZED_CONTROL',
            'U': 'QUADRATURE_POPULATION_UNPENALIZED_CONTROL', 'T': 'INDEPENDENT_NUMERICAL_GRID_LOG_LIKELIHOOD'},
        'ordered_terms': TERMS, 'all_ten_cross_inner_products_retained': True,
        'quadrature_points_per_cell': QUADRATURE_LEVELS, 'primary_quadrature': PRIMARY_QUADRATURE,
        'quadrature_weights': {'EMPTY': .25, 'OTHER': .25, 'CONTINUOUS_UNIFORM_CORE': .5},
        'population_fits_shared_across_seeds_and_budgets': True,
        'same_data_control_fits': 384, 'population_control_fits': 128, 'total_new_diagnostic_fits': 512,
        'empirical_control_routes': 24, 'population_control_profiles': 128,
        'optimizer': {'method': 'L-BFGS-B', 'start': 'ZERO', 'maxiter': 2000,
            'maxls': 50, 'ftol': 1e-15, 'gtol': 1e-11, 'Newton_polishing': False},
        'penalty_P': {'roughness': SMOOTHNESS, 'ridge': RIDGE},
        'penalty_U': {'roughness': 0., 'ridge': 0.},
        'approximation_tolerances': TOLERANCES,
        'oracle_labels_are_diagnostic_not_learned_results': True,
        'new_forward_simulations': 0, 'validation_labels_used_for_fitting_or_selection': False,
        'hyperparameter_or_family_change_selected': False, 'numerical_threads': 1,
        'maximum_seconds': MAXIMUM_SECONDS, 'retries': 0}


def load_archive(directory):
    directory = Path(directory)
    raw = (directory/'report.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('wrong archived learnability report')
    report = json.loads(raw)
    if (report['protocol_sha256'] != ARCHIVE_PROTOCOL_SHA256
            or report['completed_routes'] != 24 or report['completed_fits'] != 192):
        raise ValueError('archive protocol or coverage mismatch')
    protocol = json.loads((directory/'protocol.json').read_bytes())
    if digest(protocol) != ARCHIVE_PROTOCOL_SHA256 or protocol != report['protocol']:
        raise ValueError('archive protocol payload mismatch')
    root = Path(__file__).resolve().parents[1]
    for relative, expected in report['source_sha256'].items():
        if hashlib.sha256((root/relative).read_bytes()).hexdigest() != expected:
            raise ValueError('archived learner or target source changed')
    frozen_rows = []
    frozen_keys = {'all_models_frozen_before_backward_oracle','method','nodes','ordinal',
        'process','scenario','seed','train_budget'}
    for row in report['routes']:
        frozen = json.loads((directory/f"frozen-{row['ordinal']:02d}.json").read_bytes())
        if set(frozen) != frozen_keys or any(row[k] != v for k, v in frozen.items()):
            raise ValueError('archive frozen route mismatch')
        frozen_rows.append(frozen)
    barrier = json.loads((directory/'freeze-barrier.json').read_bytes())
    if barrier != report['freeze_barrier'] or digest(frozen_rows) != barrier['frozen_records_sha256']:
        raise ValueError('archive freeze barrier mismatch')
    # Validate every required file and every original fit before spending any
    # work on a new control. This performs no optimization or oracle queries.
    data = {(r['scenario'],r['seed'],r['u']):archived_training(directory,r) for r in report['datasets']}
    if len(data) != 48:
        raise ValueError('archive dataset roster mismatch')
    states = np.r_[np.array((0,1)),np.full(256,2)].astype(np.int64)
    coordinates = np.r_[0.,0.,np.linspace(-4.,4.,256)]
    features = {key:training_design(states,coordinates,i) for i,key in enumerate(TOLERANCES)}
    penalty = SMOOTHNESS*roughness_matrix()+RIDGE*np.eye(35)
    for row in report['routes']:
        spec = ForwardSpec(**row['process'])
        n = row['train_budget']
        for node, saved in zip(row['nodes'],row['evaluation_nodes'][:-1]):
            s,z,y = data[row['scenario'],row['seed'],node['u']]
            if array_digest(s[:n],z[:n],y[:n]) != node['training_prefix_sha256']:
                raise ValueError('archive original training prefix mismatch')
            c = np.asarray(node['fit']['physical_coefficients'])
            X = training_design(s[:n],z[:n])
            baseline = baseline_rows(spec,node['u'],s[:n],z[:n],row['method'])['value']
            risk = weighted_risk_terms(c,X,y[:n],baseline,np.full(n,1/n),spec.maximum_label,penalty)[0]
            if not math.isclose(risk,node['fit']['final_penalized_risk'],rel_tol=1e-12,abs_tol=1e-12):
                raise ValueError('archive original risk reconstruction mismatch')
            physical = _physical(spec,node['u'],row['method'],c,states,coordinates,features)
            if any(not np.allclose(physical[k],saved['physical'][k],rtol=1e-12,atol=1e-12) for k in TOLERANCES):
                raise ValueError('archive original physical reconstruction mismatch')
    return report


def archived_training(directory, record):
    raw = (Path(directory)/f"dataset-{record['ordinal']:02d}.json").read_bytes()
    row = json.loads(raw)
    if digest(row) != record['record_sha256']:
        raise ValueError('archived paired dataset binding mismatch')
    # Validation fields remain preserved in the original file but are not used
    # in any fitting, selection or diagnostic risk below.
    train = row['splits'][0]
    s = np.asarray(train['states'], dtype=np.int64)
    z, y = (np.asarray(train[k], dtype=np.float64) for k in ('coordinates', 'labels'))
    if (s.shape != (8192,) or z.shape != s.shape or y.shape != s.shape
            or array_digest(s,z,y) != train['sha256']
            or train['sha256'] != record['split_sha256'][0]):
        raise ValueError('archived training array binding mismatch')
    return s,z,y


def target_rows(oracle, u, states, coordinates):
    atoms = [oracle.log_likelihood_derivatives(u,k) for k in ('EMPTY','OTHER')]
    rows = [oracle.log_likelihood_derivatives(u,'CONTINUOUS',float(z)) if s == 2 else atoms[s]
        for s,z in zip(states,coordinates)]
    return {key:np.asarray([r[source] for r in rows]) for key,source in
        (('value','log_likelihood'),('gradient','gradient'),('hessian','hessian'))}


def _population_key(scenario, method, level, penalized, u):
    return (scenario, method, level, bool(penalized), u)


def fit_controls(directory, archive, oracles, check=lambda:None, on_population=lambda r:None, on_empirical=lambda r:None):
    """All controls use the predeclared risk; no evaluation probes select fits."""
    penalty = SMOOTHNESS*roughness_matrix()+RIDGE*np.eye(35)
    populations = []
    quad = {level:population_quadrature(level) for level in QUADRATURE_LEVELS}
    for name,theta,y in SCENARIOS:
        spec = ForwardSpec(theta,y)
        for u in GRID[:-1]:
            for level in QUADRATURE_LEVELS:
                q = quad[level]
                labels = np.exp(target_rows(oracles[name],u,q['states'],q['coordinates'])['value'])
                for method in METHODS:
                    b = baseline_rows(spec,u,q['states'],q['coordinates'],method)['value']
                    for regularized in (True,False):
                        check()
                        c,fit = fit_weighted_risk(q['features'],labels,b,q['weights'],spec.maximum_label,
                            2*math.log(spec.maximum_label/spec.contamination_density),
                            penalty if regularized else np.zeros((35,35)),spec.contamination_density)
                        fit['global_bounds'] = global_bound_diagnostics(fit)
                        row = {'ordinal':len(populations)+1,'scenario':name,'method':method,'u':u,
                            'quadrature':level,'regularized':regularized,'coefficients':c.tolist(),'fit':fit,
                            'target_label_sha256':array_digest(labels),'quadrature_input_sha256':array_digest(q['states'],q['coordinates'],q['weights']),
                            'oracle_supervised_diagnostic_control':True}
                        on_population(row)
                        populations.append(row)
    datasets = {(r['scenario'],r['seed'],r['u']):r for r in archive['datasets']}
    empirical = []
    for name,theta,y in SCENARIOS:
        spec = ForwardSpec(theta,y)
        for seed in SEEDS:
            cache = []
            for u in GRID[:-1]:
                check()
                s,z,labels = archived_training(directory,datasets[name,seed,u])
                means = np.exp(target_rows(oracles[name],u,s,z)['value'])
                cache.append((s,z,labels,means,training_design(s,z)))
            for method in METHODS:
                for budget in BUDGETS:
                    old = next(r for r in archive['routes'] if (r['scenario'],r['seed'],r['method'],r['train_budget'])==(name,seed,method,budget))
                    nodes = []
                    for i,u in enumerate(GRID[:-1]):
                        s,z,labels,means,x = cache[i]
                        b = baseline_rows(spec,u,s[:budget],z[:budget],method)['value']
                        weights = np.full(budget,1/budget)
                        fits = {}
                        for stage,ys in (('N',labels),('M',means)):
                            check()
                            c,fit = fit_weighted_risk(x[:budget],ys[:budget],b,weights,spec.maximum_label,
                                2*math.log(spec.maximum_label/spec.contamination_density),penalty,spec.contamination_density)
                            fit['global_bounds'] = global_bound_diagnostics(fit)
                            fits[stage] = {'coefficients':c.tolist(),'fit':fit,'labels_sha256':array_digest(ys[:budget])}
                        if array_digest(s[:budget],z[:budget],labels[:budget]) != old['nodes'][i]['training_prefix_sha256']:
                            raise ValueError('paired prefix differs from archived fit')
                        perturbation = x[:budget].T@(labels[:budget]-means[:budget])/(budget*spec.maximum_label)
                        nodes.append({'u':u,'A_coefficients':old['nodes'][i]['fit']['physical_coefficients'],
                            'realized_label_gradient_perturbation':perturbation.tolist(),
                            'realized_label_gradient_perturbation_l2':float(np.linalg.norm(perturbation)),
                            'training_prefix_sha256':old['nodes'][i]['training_prefix_sha256'], 'controls':fits})
                    row = {'ordinal':len(empirical)+1,'scenario':name,'seed':seed,'method':method,
                        'train_budget':budget,'archived_route_ordinal':old['ordinal'],'nodes':nodes}
                    on_empirical(row)
                    empirical.append(row)
    return populations,empirical


def contrast_summary(stage_arrays):
    """Exact ordered identity and Gram/cross terms; no variance apportionment."""
    if set(stage_arrays) != set(STAGES):
        raise ValueError('all six ordered stages required')
    if any(np.ma.isMaskedArray(stage_arrays[k]) or np.asarray(stage_arrays[k]).dtype.kind not in 'fiu' for k in STAGES):
        raise ValueError('unmasked real stage vectors required')
    xs = [np.asarray(stage_arrays[k],dtype=np.float64) for k in STAGES]
    if any(x.ndim != 1 or not x.size or x.shape != xs[0].shape or not np.isfinite(x).all() for x in xs):
        raise ValueError('aligned finite nonempty stage vectors required')
    components = np.asarray([a-b for a,b in zip(xs,xs[1:])])
    total = xs[0]-xs[-1]
    gram = components@components.T/len(total)
    return {'probe_count':len(total),'term_order':TERMS,
        'term_rms':np.sqrt(np.diag(gram)).tolist(),'term_max_abs':np.max(abs(components),axis=1).tolist(),
        'term_mean':np.mean(components,axis=1).tolist(),'gram_mean_inner_products':gram.tolist(),
        'cross_terms_twice_inner_product':[{'left':TERMS[i],'right':TERMS[j],'value':float(2*gram[i,j])}
            for i in range(5) for j in range(i+1,5)],
        'total_error_rms':float(np.sqrt(np.mean(total*total))),
        'squared_error_sum_diagonal':float(np.trace(gram)),
        'squared_error_sum_including_cross_terms':float(gram.sum()),
        'pointwise_identity_max_abs':float(np.max(abs(components.sum(axis=0)-total))),
        'squared_error_identity_abs':float(abs(gram.sum()-np.mean(total*total))),
        'components_are_independent_variances':False}


def accuracy(values,target):
    answer = {}
    for key,(atol,rtol) in TOLERANCES.items():
        error = values[key]-target[key]
        answer[key] = {'max_abs':float(np.max(abs(error))),'rms':float(np.sqrt(np.mean(error*error))),
            'failure_count':int(np.sum(abs(error)>atol+rtol*abs(target[key]))),'probe_count':len(error)}
    return answer


def _physical(spec,u,method,coefficients,states,coordinates,features):
    baseline = baseline_rows(spec,u,states,coordinates,method)
    return {k:baseline[k]+features[k]@coefficients for k in TOLERANCES}


def evaluate_controls(populations,empirical,oracles,check=lambda:None,on_route=lambda r:None):
    s = np.r_[np.array((0,1)),np.full(256,2)].astype(np.int64)
    z = np.r_[0.,0.,np.linspace(-4.,4.,256)]
    features = {k:training_design(s,z,i) for i,k in enumerate(TOLERANCES)}
    feature_norms = {k:{'max_row_l2':float(np.max(np.linalg.norm(x,axis=1))),
        'continuous_spectral_norm_div_sqrt_n':float(np.linalg.norm(x[2:],2)/16)} for k,x in features.items()}
    popmap = {_population_key(r['scenario'],r['method'],r['quadrature'],r['regularized'],r['u']):r for r in populations}
    processes = {name:ForwardSpec(theta,y) for name,theta,y in SCENARIOS}
    target = {(name,u):target_rows(oracles[name],u,s,z) for name,_,_ in SCENARIOS for u in GRID}
    q = population_quadrature(PRIMARY_QUADRATURE)
    common_risk_cache = {}
    for name,_,_ in SCENARIOS:
        for u in GRID[:-1]:
            tq = target_rows(oracles[name],u,q['states'],q['coordinates'])['value']
            common_risk_cache[name,u] = (tq,np.exp(tq))
    for r in populations:
        r['evaluation'] = {k:v.tolist() for k,v in _physical(processes[r['scenario']],r['u'],r['method'],
            np.asarray(r['coefficients']),s,z,features).items()}
    penalty = SMOOTHNESS*roughness_matrix()+RIDGE*np.eye(35)
    quad = {level:population_quadrature(level) for level in QUADRATURE_LEVELS}
    cross_cache = {}
    for name,_,_ in SCENARIOS:
        for u in GRID[:-1]:
            for level,qlevel in quad.items():
                cross_cache[name,u,level] = np.exp(target_rows(oracles[name],u,qlevel['states'],qlevel['coordinates'])['value'])
    for r in populations:
        spec = processes[r['scenario']]
        qlevel = quad[r['quadrature']]
        other_level = 48-r['quadrature']
        other = popmap[_population_key(r['scenario'],r['method'],other_level,r['regularized'],r['u'])]
        c,other_c = np.asarray(r['coefficients']),np.asarray(other['coefficients'])
        b = baseline_rows(spec,r['u'],qlevel['states'],qlevel['coordinates'],r['method'])['value']
        P = penalty if r['regularized'] else np.zeros((35,35))
        value,gradient,_ = weighted_risk_terms(other_c,qlevel['features'],cross_cache[r['scenario'],r['u'],r['quadrature']],
            b,qlevel['weights'],spec.maximum_label,P)
        r['cross_quadrature_control'] = {'other_profile_ordinal':other['ordinal'],
            'other_coefficients_on_this_quadrature_objective':value,
            'other_coefficients_on_this_quadrature_gradient':gradient.tolist(),
            'other_coefficients_on_this_quadrature_gradient_max_abs':float(np.max(abs(gradient))),
            'coefficient_difference_max_abs':float(np.max(abs(c-other_c))),
            'coefficient_difference_l2':float(np.linalg.norm(c-other_c)),
            'pure_quadrature_error_claimed':False}
    def readback_bounds(fit):
        distance = fit['global_bounds']['coefficient_distance_upper_bound_estimate']
        return {k:{'max_abs_upper_bound_estimate':None if distance is None else distance*norm['max_row_l2'],
            'continuous_rms_upper_bound_estimate':None if distance is None else distance*norm['continuous_spectral_norm_div_sqrt_n'],
            'interval_certified':False} for k,norm in feature_norms.items()}
    for r in populations:
        r['solve_readback_bounds'] = readback_bounds(r['fit'])
    routes = []
    for row in empirical:
        spec = processes[row['scenario']]
        nodes = []
        pooled = {level:{k:{stage:[] for stage in STAGES} for k in TOLERANCES} for level in QUADRATURE_LEVELS}
        for i,u in enumerate(GRID):
            check()
            t = target[row['scenario'],u]
            cs = {'A':np.asarray(row['nodes'][i]['A_coefficients']),
                **{stage:np.asarray(row['nodes'][i]['controls'][stage]['coefficients']) for stage in ('N','M')}} if u<1 else {stage:np.zeros(35) for stage in ('A','N','M')}
            actual = {stage:_physical(spec,u,row['method'],c,s,z,features) for stage,c in cs.items()}
            nr = {'u':u,'stages':{stage:{k:v.tolist() for k,v in vals.items()} for stage,vals in actual.items()},
                'target':{k:v.tolist() for k,v in t.items()},'chains':{}}
            for level in QUADRATURE_LEVELS:
                if u<1:
                    ps = {stage:popmap[_population_key(row['scenario'],row['method'],level,regular,u)] for stage,regular in (('P',True),('U',False))}
                    pv = {stage:{k:np.asarray(v) for k,v in p['evaluation'].items()} for stage,p in ps.items()}
                else:
                    ps = {}
                    pv = {stage:_physical(spec,u,row['method'],np.zeros(35),s,z,features) for stage in ('P','U')}
                stages = {**actual,**pv,'T':t}
                nr['chains'][str(level)] = {'population_profile_ordinals':{stage:p['ordinal'] for stage,p in ps.items()},
                    'continuous':{k:contrast_summary({stage:v[k][2:] for stage,v in stages.items()}) for k in TOLERANCES},
                    'atomic_value':contrast_summary({stage:v['value'][:2] for stage,v in stages.items()}),
                    'stage_accuracy':{stage:accuracy({k:v[2:] for k,v in vals.items()},{k:v[2:] for k,v in t.items()}) for stage,vals in stages.items() if stage!='T'}}
                if u<1:
                    for k in TOLERANCES:
                        for stage,vals in stages.items():
                            pooled[level][k][stage].extend(vals[k][2:].tolist())
            if u<1:
                bq = baseline_rows(spec,u,q['states'],q['coordinates'],row['method'])['value']
                tq,hq = common_risk_cache[row['scenario'],u]
                qcs = {**cs,**{stage:np.asarray(popmap[_population_key(row['scenario'],row['method'],PRIMARY_QUADRATURE,regular,u)]['coefficients']) for stage,regular in (('P',True),('U',False))}}
                nr['common_primary_population_excess_risk'] = {}
                for stage,c in qcs.items():
                    difference = bq+q['features']@c-tq
                    nr['common_primary_population_excess_risk'][stage] = float(np.dot(q['weights'],hq*(np.expm1(difference)-difference))/spec.maximum_label)
                nr['quadrature_plus_solver_response'] = {}
                for stage,regular in (('P',True),('U',False)):
                    lo,hi = (popmap[_population_key(row['scenario'],row['method'],level,regular,u)] for level in QUADRATURE_LEVELS)
                    nr['quadrature_plus_solver_response'][stage] = {k:{'max_abs':float(np.max(abs(np.asarray(lo['evaluation'][k])-hi['evaluation'][k]))),
                        'rms':float(np.sqrt(np.mean((np.asarray(lo['evaluation'][k])[2:]-hi['evaluation'][k][2:])**2)))} for k in TOLERANCES}
            nodes.append(nr)
        result = {**row,'evaluation_nodes':nodes,
            'solve_readback_bounds':[{stage:readback_bounds(control['fit']) for stage,control in n['controls'].items()} for n in row['nodes']],
            'active_decomposition':{str(level):{k:contrast_summary(stages) for k,stages in bykey.items()} for level,bykey in pooled.items()}}
        on_route(result)
        routes.append(result)
    return populations,routes,feature_norms


def run_comparison(directory,check=lambda:None,on_population=lambda r:None,on_empirical=lambda r:None,on_barrier=lambda r:None,on_route=lambda r:None):
    from heterodiff.experiments.continuous_residual_capacity import target_bundle
    start = time.monotonic()
    with threadpool_limits(limits=1):
        archive = load_archive(directory)
        oracles = {scenario[0]:target_bundle(scenario)[0] for scenario in SCENARIOS}
        populations,empirical = fit_controls(directory,archive,oracles,check,on_population,on_empirical)
        barrier = {'population_profiles':len(populations),'empirical_routes':len(empirical),
            'new_fits':len(populations)+sum(2*len(r['nodes']) for r in empirical),
            'frozen_record_sha256':digest({'population':populations,'empirical':empirical}),
            'before_evaluation_probe_comparisons':True,'oracle_likelihood_labels_used_for_controls':True}
        on_barrier(barrier)
        populations,routes,norms = evaluate_controls(populations,empirical,oracles,check,on_route)
    return {'schema_version':SCHEMA,'decision':'CONTROLLED_ERROR_DECOMPOSITION_COMPLETE_REVIEW_NUMERICS',
        'protocol':specification(),'freeze_barrier':barrier,'population_controls':populations,'routes':routes,
        'evaluation_feature_norms':norms,'elapsed_seconds':time.monotonic()-start,
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
        'scope':{'learner_changed':False,'new_forward_labels_simulated':False,'sampler_integrated':False,
            'oracle_controls_are_learned_results':False,'population_or_optimization_exactness_certified':False,
            'real_data_GPU_cloud_network_or_paid_jobs':False,'variance_components_identified':False}}


def source_bindings():
    root = Path(__file__).resolve().parents[1]
    names = ('experiments/continuous_localized_error_decomposition.py','experiments/localized_population_risk.py',
        'experiments/continuous_localized_learnability.py','experiments/continuous_forward_labels.py',
        'models/localized_likelihood_learner.py','experiments/continuous_residual_capacity.py',
        'evaluation/continuous_fiber_grid_target.py','evaluation/continuous_fiber_conditional_benchmark.py',
        'evaluation/continuous_fiber_initialization_diagnostic.py')
    return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in names}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect',action='store_true')
    parser.add_argument('--archive',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.inspect:
        print(payload(specification()).decode(),end='')
        return
    if args.archive is None or args.output is None:
        parser.error('--archive directory and new --output required')
    out,archive = args.output.absolute(),args.archive.absolute()
    if not args.worker:
        with threadpool_limits(limits=1):
            load_archive(archive)
        if out.exists() or not out.parent.is_dir():
            parser.error('new output directory beneath existing parent required')
        out.mkdir()
        write_new(out/'protocol.json',specification())
        try:
            result = subprocess.run([sys.executable,'-m','heterodiff.experiments.continuous_localized_error_decomposition',
                '--archive',str(archive),'--output',str(out),'--worker'],timeout=MAXIMUM_SECONDS,check=False)
        except subprocess.TimeoutExpired:
            write_new(out/'failure.json',{'decision':'INCOMPLETE_DEADLINE','maximum_seconds':MAXIMUM_SECONDS})
            raise SystemExit(1)
        if result.returncode:
            write_new(out/'failure.json',{'decision':'INCOMPLETE_CHILD_FAILURE','returncode':result.returncode})
        raise SystemExit(result.returncode)
    start = time.monotonic()
    def check():
        if time.monotonic()-start>MAXIMUM_SECONDS:
            raise TimeoutError('soft diagnostic deadline')
    def frozen(row):
        write_new(out/f"empirical-{row['ordinal']:02d}.json",row)
        print(json.dumps({'phase':'empirical_controls_frozen','route':row['ordinal']}),flush=True)
    bindings = source_bindings()
    write_new(out/'execution.json',{'sources':bindings,'protocol_sha256':digest(specification()),'recorded_before_fits':True})
    report = run_comparison(archive,check,lambda r:write_new(out/f"population-{r['ordinal']:03d}.json",r),frozen,
        lambda r:write_new(out/'freeze-barrier.json',r),lambda r:write_new(out/f"route-{r['ordinal']:02d}.json",r))
    if source_bindings()!=bindings:
        raise RuntimeError('source changed during diagnosis')
    report['source_sha256'],report['protocol_sha256'] = bindings,digest(specification())
    write_new(out/'report.json',report)
    print(json.dumps({'decision':report['decision'],'new_fits':report['freeze_barrier']['new_fits'],'elapsed_seconds':report['elapsed_seconds']}))


if __name__ == '__main__':
    main()
