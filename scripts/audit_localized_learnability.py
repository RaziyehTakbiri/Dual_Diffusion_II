"""Independent saved-artifact audit: no fitting, simulation or production learner.

Rebuilds raw clamped spline controls directly, independently evaluates model
offsets, and uses six-point (rather than construction's four-point) curvature
quadrature. The existing independent grid oracle is accessed after verifying
the complete frozen roster, solely to check saved evaluation targets.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
import scipy
from scipy.interpolate import BSpline
from threadpoolctl import threadpool_limits

GRID = tuple(i/8 for i in range(9))
SCENARIOS = (('reference-pressure', .8, .7), ('higher-pressure-shifted-observation', 2.5, 1.4))
METHODS = ('association-aware-guide-plus-residual', 'unified-direct-conditioner')
SEEDS, BUDGETS = (11, 29, 47), (1024, 8192)
TOLERANCES = {'value': (2e-6, 2e-5), 'gradient': (2e-5, 2e-4), 'hessian': (1e-4, 1e-3)}
PROTOCOL_SHA256 = 'c99b27fbd042359f65f54cd7c191a4bdd28e98f62303ad341fcdb8287ee8036e'
AUDIT_ATOL, AUDIT_RTOL = 5e-10, 5e-9


def payload(record):
    return json.dumps(record, sort_keys=True, indent=2, allow_nan=False).encode()+b'\n'


def digest(record):
    return hashlib.sha256(payload(record)).hexdigest()


def array_digest(*arrays):
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(a)
        h.update(str(a.shape).encode()+a.dtype.str.encode()+a.tobytes())
    return h.hexdigest()


class Audit:
    def __init__(self):
        self.check_count = 0
        self.failures = []
        self.maximum_differences = {}
        self.files = {}

    def require(self, condition, label):
        self.check_count += 1
        if not condition:
            self.failures.append(label)

    def close(self, actual, expected, label, family):
        a, e = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
        valid = a.shape == e.shape and a.size and np.isfinite(a).all() and np.isfinite(e).all()
        self.require(bool(valid), label+':finite_shape')
        if valid:
            self.maximum_differences[family] = max(self.maximum_differences.get(family, 0.), float(np.max(abs(a-e))))
            self.require(bool(np.allclose(a, e, atol=AUDIT_ATOL, rtol=AUDIT_RTOL)), label+':numerical_match')

    def read(self, path):
        raw = path.read_bytes()
        if len(raw) > 256*1024*1024:
            raise ValueError('audit file exceeds 256 MiB')
        def reject(value):
            raise ValueError('nonfinite JSON constant: '+value)
        record = json.loads(raw, parse_constant=reject)
        self.files[path.name] = {'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)}
        return record


def basis(coordinates, order=0):
    """Build all 37 raw basis functions, then sum tied edge columns."""
    edges = np.linspace(-4.5, 4.5, 33)
    knot_vector = np.concatenate((np.full(5, -4.5), edges, np.full(5, 4.5)))
    raw = BSpline(knot_vector, np.eye(37), 5, extrapolate=False)
    z = np.asarray(coordinates)
    values = raw.derivative(order)(np.clip(z, -4.5, 4.5))
    answer = np.column_stack((values[:, :3].sum(axis=1), values[:, 3:34], values[:, 34:].sum(axis=1)))
    if order:
        answer[(z <= -4.5) | (z >= 4.5)] = 0.
    return answer


def features(states, coordinates, order=0):
    matrix = np.zeros((len(states), 35))
    matrix[states == 2, :33] = basis(coordinates[states == 2], order)
    if order == 0:
        matrix[states == 0, 33] = 1.
        matrix[states == 1, 34] = 1.
    return matrix


def roughness():
    roots, weights = np.polynomial.legendre.leggauss(6)
    edges = np.linspace(-4.5, 4.5, 33)
    points, integration_weights = [], []
    for left, right in zip(edges[:-1], edges[1:]):
        points.extend(((left+right)/2+(right-left)*roots/2).tolist())
        integration_weights.extend(((right-left)*weights/18).tolist())
    b = basis(np.asarray(points), 2)
    result = np.zeros((35, 35))
    result[:33, :33] = b.T@(np.asarray(integration_weights)[:, None]*b)
    return result


def constants(process):
    y, sigma = process['observation_value'], process['observation_sd']
    c = process['contamination']*math.exp(-1)*process['selected_probability']*math.exp(-y*y/2)/math.sqrt(2*math.pi)
    maximum = c+(1-process['contamination'])/(2*sigma*math.sqrt(2*math.pi))
    return c, maximum, 2*math.log(maximum/c)


def offset(process, u, states, z, method):
    """Independent raw-density Gaussian calculation, not the forward module."""
    tau = 1-u if method == METHODS[0] else 0.
    rho, theta, y = process['selected_probability'], process['theta'], process['observation_value']
    sigma, epsilon = process['observation_sd'], process['contamination']
    c = constants(process)[0]
    survival = math.exp(-process['death_rate']*tau)
    a = math.exp(-process['continuous_rate']*tau/2)
    variance = sigma*sigma+1-a*a
    retained, immigrants = survival/2, theta*(1-survival)/2
    factor = (1-epsilon)*math.exp(-immigrants)
    stationary = math.exp(-y*y/(2*(1+sigma*sigma)))/math.sqrt(2*math.pi*(1+sigma*sigma))
    h = c+factor*immigrants*rho*stationary*np.where(states == 0, 1., 1-retained)
    first, second = np.zeros(len(states)), np.zeros(len(states))
    active = states == 2
    delta = y-a*z[active]
    signal = factor*retained*np.exp(-delta*delta/(2*variance))/math.sqrt(2*math.pi*variance)
    h[active] += signal
    first[active] = signal*a*delta/variance
    second[active] = signal*((a*delta/variance)**2-a*a/variance)
    return {'value': np.log(h), 'gradient': first/h, 'hessian': second/h-(first/h)**2}


def risk(f, labels, maximum):
    return float(np.mean(np.exp(f)-labels*f)/maximum)


def risk_change(f, b, labels, maximum, states):
    change = (np.exp(f)-np.exp(b)-labels*(f-b))/maximum
    variance = 0.
    for s in (0, 1, 2):
        values = change[states == s]
        n, total = len(values), len(states)
        variance += (n/total)**2*float(np.sum((values-values.mean())**2))/(n-1)/n
    return float(change.mean()), math.sqrt(variance)


def errors(a, t, tolerance):
    atol, rtol = tolerance
    delta = np.asarray(a)-np.asarray(t)
    threshold = atol+rtol*abs(np.asarray(t))
    return {'max_abs': float(np.max(abs(delta))), 'rms': float(np.sqrt(np.mean(delta*delta))),
        'failure_count': int(np.sum(abs(delta) > threshold)), 'count': len(delta),
        'maximum_error_over_threshold': float(np.max(abs(delta)/threshold)),
        'passed_pointwise_approximation_tolerance': not bool(np.any(abs(delta) > threshold))}


def audit_run(directory, repo):
    start = time.monotonic()
    audit = Audit()
    report = audit.read(directory/'report.json')
    protocol = audit.read(directory/'protocol.json')
    execution = audit.read(directory/'execution.json')
    barrier = audit.read(directory/'freeze-barrier.json')
    audit.require(report['schema_version'] == 'continuous-localized-forward-learnability-v1', 'schema')
    audit.require(digest(protocol) == PROTOCOL_SHA256 == report['protocol_sha256'] == execution['protocol_sha256'], 'fixed_protocol_hash')
    audit.require(protocol == report['protocol'], 'protocol_file_report_identity')
    audit.require(report['source_sha256'] == execution['source_sha256'], 'source_before_after_bindings')
    for relative, expected in execution['source_sha256'].items():
        audit.require(hashlib.sha256((repo/'src/heterodiff'/relative).read_bytes()).hexdigest() == expected, 'current_source:'+relative)
    audit.require(protocol['approximation_tolerances'] == {k:list(v) for k,v in TOLERANCES.items()}, 'unchanged_acceptance_tolerances')
    audit.require(report['completed_routes'] == 24 and report['completed_fits'] == 192, 'completed_counts')
    frozen = [audit.read(directory/f'frozen-{i:02d}.json') for i in range(1, 25)]
    audit.require(digest(frozen) == barrier['frozen_records_sha256'], 'global_frozen_roster_hash')
    audit.require(barrier == report['freeze_barrier'], 'barrier_file_report_identity')
    audit.require(barrier['frozen_routes'] == 24 and barrier['frozen_models'] == 192 and not barrier['backward_target_queried_during_training'], 'barrier_fields')
    expected_roster = [(s[0], seed, method, budget) for s in SCENARIOS for seed in SEEDS for method in METHODS for budget in BUDGETS]
    audit.require([(r['scenario'], r['seed'], r['method'], r['train_budget']) for r in frozen] == expected_roster, 'fixed_route_roster')
    datasets = {}
    work_totals = {'training_suffixes': 0, 'validation_suffixes': 0, 'macro_suffix_intervals': 0}
    for i in range(1, 49):
        row = audit.read(directory/f'dataset-{i:02d}.json')
        summary = report['datasets'][i-1]
        audit.require(row['ordinal'] == i and digest(row) == summary['record_sha256'], f'dataset_{i}:record_hash')
        key = row['scenario'], row['seed'], row['u']
        audit.require(key not in datasets, f'dataset_{i}:unique')
        scenario_index = [s[0] for s in SCENARIOS].index(row['scenario'])
        pair = []
        for split, source in enumerate(row['splits']):
            n = 8192 if split == 0 else 4096
            states = np.asarray(source['states'], dtype=np.int64)
            z, labels = np.asarray(source['coordinates']), np.asarray(source['labels'])
            audit.require(states.shape == z.shape == labels.shape == (n,), f'dataset_{i}_{split}:shape')
            audit.require(np.array_equal(states, np.tile((0,1,2,2), n//4)), f'dataset_{i}_{split}:balanced_design')
            audit.require(bool(np.isfinite(z).all() and np.isfinite(labels).all() and (z[states != 2] == 0).all() and (abs(z) <= 4.5).all()), f'dataset_{i}_{split}:finite_design')
            fingerprint = array_digest(states,z,labels)
            audit.require(fingerprint == source['sha256'] == summary['split_sha256'][split], f'dataset_{i}_{split}:arrays_hash')
            audit.require(source['rng_namespace'] == [20260913,scenario_index,row['seed'],GRID.index(row['u']),split], f'dataset_{i}_{split}:namespace')
            work = source['work']
            audit.require(work == summary['work'][split] and work['forward_suffix_count'] == n, f'dataset_{i}_{split}:work_binding')
            audit.require(work['macro_intervals_per_suffix'] == 8-GRID.index(row['u']), f'dataset_{i}_{split}:suffix_length')
            audit.require(sum(work['terminal_state_counts'].values()) == n and not work['backward_likelihood_or_score_queried'] and not work['conditional_endpoint_sampler_used'], f'dataset_{i}_{split}:label_scope')
            work_totals['training_suffixes' if split == 0 else 'validation_suffixes'] += n
            work_totals['macro_suffix_intervals'] += n*work['macro_intervals_per_suffix']
            pair.append((states,z,labels,fingerprint))
        datasets[key] = pair
    audit.require(len(datasets) == 48, 'dataset_count')
    audit.require(work_totals == {'training_suffixes':393216,'validation_suffixes':196608,'macro_suffix_intervals':2654208}, 'total_forward_work')
    # Only now access the independent target. No production fitting/model/label
    # module is imported by this audit, and no simulation is performed.
    sys.path.insert(0, str(repo/'src'))
    from heterodiff.evaluation.continuous_fiber_conditional_benchmark import ContinuousFiberSpec
    from heterodiff.evaluation.continuous_fiber_grid_target import ContinuousFiberGridTarget
    target_cache = {}
    states = np.concatenate((np.array((0,1)),np.full(256,2))).astype(np.int64)
    z = np.concatenate((np.zeros(2),np.linspace(-4.,4.,256)))
    designs = {order:features(states,z,order) for order in (0,1,2)}
    R = roughness()
    audit.close(basis(np.linspace(-4.5,4.5,257)).sum(axis=1), np.ones(257), 'spline_partition_unity', 'spline_self_check')
    for order in (1,2):
        audit.close(basis(np.linspace(-4.5,4.5,257),order).sum(axis=1), np.zeros(257), 'constant_derivative_zero', 'spline_self_check')
    for name, theta, y in SCENARIOS:
        oracle = ContinuousFiberGridTarget(ContinuousFiberSpec(theta=theta,observation_value=y,
            type_probabilities=(1-393217/524288,393217/524288)),GRID)
        for u in GRID:
            records = [oracle.log_likelihood_derivatives(u,('EMPTY','OTHER','CONTINUOUS')[s],float(v) if s==2 else None) for s,v in zip(states,z)]
            target_cache[name,u] = {key:np.asarray([r[field] for r in records]) for key,field in
                (('value','log_likelihood'),('gradient','gradient'),('hessian','hessian'))}
    route_summaries, fit_summaries, pairings = [], [], {}
    for i, original in enumerate(frozen, 1):
        route = audit.read(directory/f'route-{i:02d}.json')
        audit.require(route == report['routes'][i-1], f'route_{i}:report_file_identity')
        audit.require({k:route[k] for k in original} == original, f'route_{i}:frozen_preserved')
        name, seed, method, budget = original['scenario'],original['seed'],original['method'],original['train_budget']
        process = original['process']
        c, maximum, bound = constants(process)
        per_node_errors, baseline_errors, changes = [], [], []
        for j,u in enumerate(GRID):
            label = f'route_{i}_node_{j}'
            if j < 8:
                n, tau = original['nodes'][j], 1-u
                fit = n['fit']
                a, q = np.asarray(fit['physical_coefficients']),np.asarray(fit['coefficients'])
                audit.close(a,tau*q,label+':physical_quotient','coefficient_gate')
                audit.require(a.shape == q.shape == (35,) and bool((abs(a) <= bound).all()), label+':coefficient_box')
                audit.close(fit['physical_coefficient_bound'],bound,label+':physical_bound','bounds')
                audit.close(fit['quotient_coefficient_bound'],bound/tau,label+':quotient_bound','bounds')
                train, validation = datasets[name,seed,u]
                audit.require(n['training_full_dataset_sha256'] == train[3] and n['validation_dataset_sha256'] == validation[3],label+':shared_dataset_binding')
                prefix = array_digest(*(x[:budget] for x in train[:3]))
                audit.require(n['training_prefix_sha256'] == prefix,label+':nested_prefix')
                pairkey = name,seed,u,budget
                audit.require(pairings.setdefault(pairkey,prefix) == prefix,label+':method_pairing')
                audit.require(n['u'] == u and n['train_budget'] == budget and fit['remaining_time'] == tau,label+':node_budget')
                audit.require(not fit['hessian_score_or_exact_likelihood_labels_consumed'] and not fit['regularization_selected_from_validation_or_oracle'],label+':supervision_flags')
                risks = []
                for split,data in enumerate((train,validation)):
                    st,co,labels = (x[:budget] if split == 0 else x for x in data[:3])
                    audit.require(bool((labels >= c).all() and (labels <= maximum).all()),label+':bounded_labels')
                    X = features(st,co)
                    b = offset(process,u,st,co,method)['value']
                    f = b+X@a
                    current, baseline = risk(f,labels,maximum),risk(b,labels,maximum)
                    risks.append((current,baseline))
                    splitname = 'training' if split == 0 else 'validation'
                    audit.close(n[splitname+'_risk'],current,label+':'+splitname+'_risk','risks')
                    audit.close(n[splitname+'_baseline_risk'],baseline,label+':'+splitname+'_baseline_risk','risks')
                    if split == 0:
                        gradient = X.T@(np.exp(f)-labels)/(len(labels)*maximum)+1e-4*(R@a)+1e-6*a
                        projected = gradient.copy()
                        projected[(a <= -bound)&(gradient > 0)] = 0.
                        projected[(a >= bound)&(gradient < 0)] = 0.
                    else:
                        mean,se = risk_change(f,b,labels,maximum,st)
                        audit.close(n['validation_paired_change']['mean'],mean,label+':paired_mean','risks')
                        audit.close(n['validation_paired_change']['stratified_standard_error_descriptive'],se,label+':paired_se','risk_se')
                        changes.append(mean)
                rough = float(a@R@a)
                penalty = .5e-4*rough+.5e-6*float(a@a)
                audit.close(fit['initial_penalized_risk'],risks[0][1],label+':initial_objective','objective')
                audit.close(fit['final_penalized_risk'],risks[0][0]+penalty,label+':final_objective','objective')
                audit.close(fit['projected_gradient_max_abs'],np.max(abs(projected)),label+':projected_gradient','kkt')
                audit.require(fit['coefficient_boundary_count'] == int(np.sum(abs(a) >= bound-1e-10)),label+':active_bounds')
                audit.require(0 <= fit['iterations'] <= 200,label+':iteration_limit')
                audit.close(fit['real_arithmetic_absolute_bound'],max(abs(a)),label+':fit_envelope','bounds')
                audit.close(n['model_real_absolute_bound'],max(abs(a)),label+':node_envelope','bounds')
                fit_summaries.append({'route':i,'u':u,'independent_mean_core_squared_curvature':rough,
                    'independent_projected_gradient_max_abs':float(max(abs(projected))),
                    'solver_success_recorded':fit['solver_success'],'solver_success_independently_rederived':False})
            else:
                a = np.zeros(35)
            row = route['evaluation_nodes'][j]
            audit.require(row['u'] == u,label+':evaluation_node')
            baseline = offset(process,u,states,z,method)
            residual = {key:designs[order]@a for order,key in enumerate(TOLERANCES)}
            physical = {k:baseline[k]+residual[k] for k in TOLERANCES}
            target = target_cache[name,u]
            candidate_stats, baseline_stats = {},{}
            for key,tolerance in TOLERANCES.items():
                for family,computed in (('baseline',baseline),('residual',residual),('physical',physical),('target',target)):
                    audit.close(row[family][key],computed[key],label+':'+family+'_'+key,family+'_arrays')
                candidate_stats[key] = errors(physical[key][2:],target[key][2:],tolerance)
                baseline_stats[key] = errors(baseline[key][2:],target[key][2:],tolerance)
                for field,stats in (('continuous_errors',candidate_stats),('continuous_baseline_errors',baseline_stats)):
                    saved = row[field][key]
                    audit.require((saved['atol'],saved['rtol']) == tolerance,label+':fixed_tolerance_'+key)
                    for metric,value in stats[key].items():
                        if isinstance(value,(bool,int)):
                            audit.require(saved[metric] == value,label+':'+field+'_'+key+'_'+metric)
                        else:
                            audit.close(saved[metric],value,label+':'+field+'_'+key+'_'+metric,'error_statistics')
            per_node_errors.append(candidate_stats)
            baseline_errors.append(baseline_stats)
            audit.close(row['atomic_log_value_errors'],physical['value'][:2]-target['value'][:2],label+':atomic_errors','atomic_errors')
            centered = (physical['value']-physical['value'][0])-(target['value']-target['value'][0])
            audit.close(row['empty_centered_log_potential_error_max_abs'],max(abs(centered)),label+':centered_error','centered_errors')
            audit.close(row['model_real_absolute_bound'],max(abs(a)),label+':evaluation_envelope','bounds')
            if j == 8:
                audit.require(all(np.array_equal(v,np.zeros(258)) for v in residual.values()),label+':terminal_residual_exact_zero')
                audit.close(physical['value'],target['value'],label+':terminal_identity','terminal_identity')
        passed = True
        for key in TOLERANCES:
            for field,stats in (('continuous_errors',per_node_errors),('continuous_baseline_errors',baseline_errors)):
                active = [n[key] for n in stats[:-1]]
                aggregate = {'max_abs':max(n['max_abs'] for n in active),
                    'rms':math.sqrt(sum(n['rms']**2 for n in active)/8),
                    'failure_count':sum(n['failure_count'] for n in active),'probe_count':2048}
                for metric,value in aggregate.items():
                    saved = route['active_errors'][key][field][metric]
                    if isinstance(value,int): audit.require(saved == value,f'route_{i}:aggregate_{key}_{field}_{metric}')
                    else: audit.close(saved,value,f'route_{i}:aggregate_{key}_{field}_{metric}','aggregate_statistics')
                if field == 'continuous_errors': passed = passed and aggregate['failure_count'] == 0
        audit.require(route['all_continuous_tolerances_passed'] == passed,f'route_{i}:overall_diagnostic')
        audit.require(route['solver_success_count'] == sum(n['fit']['solver_success'] for n in original['nodes']),f'route_{i}:solver_count')
        audit.close(route['maximum_projected_gradient'],max(n['fit']['projected_gradient_max_abs'] for n in original['nodes']),f'route_{i}:maximum_kkt','aggregate_statistics')
        audit.close(route['mean_validation_risk_change'],np.mean(changes),f'route_{i}:mean_validation_change','aggregate_statistics')
        route_summaries.append({'ordinal':i,'scenario':name,'seed':seed,'method':method,'train_budget':budget,
            'all_continuous_tolerances_passed':passed,'independent_mean_validation_risk_change':float(np.mean(changes))})
    audit.require(len(fit_summaries) == 192 and len(pairings) == 96,'audited_fit_pairing_counts')
    return {'schema_version':'continuous-localized-learnability-independent-audit-v1',
        'decision':'PASS_SAVED_LEARNABILITY_AUDIT' if not audit.failures else 'FAIL_SAVED_LEARNABILITY_AUDIT',
        'captured_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-start,
        'report_sha256':audit.files['report.json']['sha256'],'protocol_sha256':PROTOCOL_SHA256,
        'audit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'audit_numerical_identity_tolerances':{'atol':AUDIT_ATOL,'rtol':AUDIT_RTOL,'scientific_acceptance_tolerances_changed':False},
        'scientific_acceptance_tolerances':TOLERANCES,'check_count':audit.check_count,
        'failure_count':len(audit.failures),'failures':audit.failures,
        'maximum_absolute_recomputation_differences':audit.maximum_differences,
        'audited_routes':24,'audited_fits':192,'audited_raw_paired_datasets':48,'forward_work':work_totals,
        'files':audit.files,'routes':route_summaries,'fits':fit_summaries,
        'environment':{'numpy':np.__version__,'scipy':scipy.__version__},
        'scope':{'no_refits':True,'no_new_labels_or_random_draws':True,'production_learner_or_optimizer_imported':False,
            'independent_raw_spline_reconstruction':True,'independent_six_point_curvature_quadrature':True,
            'backward_oracle_used_only_for_post_fit_target_verification':True,
            'stored_freeze_barrier_binding_checked_not_historical_execution_authentication':True,
            'recorded_solver_success_not_proof_of_optimality':True,'sampler_or_GPU_or_network_requested':False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-directory',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error('new output file beneath an existing parent required')
    with threadpool_limits(limits=1):
        result = audit_run(args.run_directory,args.repo)
    encoded = payload(result)
    with args.output.open('xb') as handle:
        handle.write(encoded)
    print(json.dumps({k:result[k] for k in ('decision','check_count','failure_count','elapsed_seconds','report_sha256')}))
    raise SystemExit(bool(result['failure_count']))


if __name__ == '__main__':
    main()
