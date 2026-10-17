"""Post-result sensitivity of saved fits; no imports of learner or optimizer.

Uses raw gradient L2, recorded row-L1 upper bound for feature L2 norms, and
ordinary computed local Hessian eigenvalues. Results are not interval-certified
error bars, not predeclared acceptance outcomes, and do not alter primary bounds.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from numbers import Real


def payload(record):
    return json.dumps(record,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n'


def digest(record):
    return hashlib.sha256(payload(record)).hexdigest()


def finite(value,name):
    if isinstance(value,bool) or not isinstance(value,Real) or not math.isfinite(float(value)):
        raise ValueError(name+' must be a finite real number')
    return float(value)


def sensitivity_estimate(gradient,minimum_hessian_eigenvalue,feature_norm_bound):
    """Evaluate the exponential-Hessian theorem using noncertified inputs."""
    if not isinstance(gradient,(list,tuple)) or not gradient:
        raise ValueError('nonempty raw gradient vector required')
    g = [finite(v,'gradient') for v in gradient]
    lam = finite(minimum_hessian_eigenvalue,'minimum_hessian_eigenvalue')
    L = finite(feature_norm_bound,'feature_norm_bound')
    if L < 0:
        raise ValueError('feature norm bound must be nonnegative')
    norm = math.hypot(*g)
    ratio = distance = base = None
    if not math.isfinite(norm):
        reason = 'RAW_GRADIENT_NORM_NOT_REPRESENTABLE'
    elif lam <= 0:
        reason = 'NONPOSITIVE_LOCAL_HESSIAN_EIGENVALUE'
    else:
        base = norm/lam
        if not math.isfinite(base):
            base = None
            reason = 'GRADIENT_TO_CURVATURE_RATIO_NOT_REPRESENTABLE'
        elif L == 0:
            ratio,distance = 0.,base
            reason = 'L_ZERO_QUADRATIC_LIMIT_UNVALIDATED'
        else:
            ratio = L*base
            if not math.isfinite(ratio):
                ratio = None
                reason = 'SENSITIVITY_RATIO_NOT_REPRESENTABLE'
            elif ratio >= 1:
                reason = 'SENSITIVITY_RATIO_AT_LEAST_ONE'
            else:
                # Equivalent to -log1p(-ratio)/L; stable also if multiplication
                # L*base underflows to zero while base remains representable.
                factor = -math.log1p(-ratio)/ratio if ratio else 1.
                distance = base*factor
                if not math.isfinite(distance):
                    distance = None
                    reason = 'DISTANCE_ESTIMATE_NOT_REPRESENTABLE'
                else:
                    reason = 'EXPONENTIAL_HESSIAN_UNVALIDATED_ESTIMATE'
    return {'raw_gradient_l2':norm if math.isfinite(norm) else None,
        'local_hessian_minimum_eigenvalue_computed':lam,'feature_norm_upper_bound_used':L,
        'raw_gradient_to_curvature_ratio':base,'L_times_gradient_to_curvature_ratio':ratio,
        'coefficient_distance_upper_bound_estimate':distance,'vacuous':distance is None,'reason':reason,
        'formula':'-log1p(-L*norm(raw_gradient,2)/lambda_min(H(a)))/L; L=0 limit norm(g,2)/lambda',
        'raw_gradient_not_infinity_or_projected_norm':True,
        'local_eigenvalue_assumed_constant_on_box':False,
        'post_result_analytical_sensitivity':True,'predeclared_acceptance_outcome':False,
        'floating_point_interval_certificate':False,
        'scope':'DISTANCE_TO_OPTIMUM_OF_SAME_FINITE_WEIGHTED_PENALIZED_OBJECTIVE_ONLY'}


def fit_sensitivity(fit,identity,feature_norms):
    coefficients = [finite(c,'coefficient') for c in fit['physical_coefficients']]
    A = finite(fit['coefficient_bound'],'coefficient_bound')
    if len(coefficients) != 35 or len(fit['gradient']) != 35 or A <= 0 or any(abs(c) > A for c in coefficients):
        raise ValueError('feasible saved 35-coefficient box fit required')
    active = sum(abs(c) == A for c in coefficients)
    if active != fit['exact_boundary_count']:
        raise ValueError('saved exact-boundary count mismatch')
    estimate = sensitivity_estimate(fit['gradient'],fit['local_hessian_minimum_eigenvalue'],fit['feature_maximum_row_l1_norm'])
    radius = estimate['coefficient_distance_upper_bound_estimate']
    responses = {}
    for name in ('value','gradient','hessian'):
        row = feature_norms[name]
        largest = finite(row['max_row_l2'],'max_row_l2')
        rms = finite(row['continuous_spectral_norm_div_sqrt_n'],'continuous_spectral_norm_div_sqrt_n')
        if min(largest,rms) < 0:
            raise ValueError('nonnegative saved feature operator norms required')
        worst = None if radius is None else largest*radius
        mean = None if radius is None else rms*radius
        if worst is not None and not math.isfinite(worst): worst = None
        if mean is not None and not math.isfinite(mean): mean = None
        responses[name] = {'max_abs_optimum_response_estimate':worst,
            'continuous_rms_optimum_response_estimate':mean,
            'recorded_max_row_l2':largest,'recorded_continuous_spectral_norm_div_sqrt_n':rms,
            'finite_saved_probe_roster_only':True,'interval_certificate':False}
    return {'identity':identity,'fit_record_sha256':digest(fit),'exact_boundary_count':active,
        'all_coefficients_strictly_interior':active == 0,'sensitivity':estimate,
        'finite_probe_responses':responses,'preserved_primary_global_bounds':fit['global_bounds'],
        'primary_global_bounds_sha256':digest(fit['global_bounds'])}


def summarize(rows):
    finite_rows = [r for r in rows if not r['sensitivity']['vacuous']]
    def limits(values):
        values = [v for v in values if v is not None]
        return {'minimum':min(values),'maximum':max(values)} if values else None
    return {'fit_count':len(rows),'nonvacuous_unvalidated_count':len(finite_rows),
        'strictly_interior_count':sum(r['all_coefficients_strictly_interior'] for r in rows),
        'coefficient_distance_estimate_range':limits([r['sensitivity']['coefficient_distance_upper_bound_estimate'] for r in rows]),
        'raw_gradient_to_curvature_ratio_range':limits([r['sensitivity']['raw_gradient_to_curvature_ratio'] for r in rows]),
        'primary_predeclared_distance_estimate_range':limits([r['preserved_primary_global_bounds']['coefficient_distance_upper_bound_estimate'] for r in rows]),
        'finite_probe_response_ranges':{name:{kind:limits([r['finite_probe_responses'][name][kind] for r in rows])
            for kind in ('max_abs_optimum_response_estimate','continuous_rms_optimum_response_estimate')}
            for name in ('value','gradient','hessian')}}


def analyze_report(report,report_sha256):
    if report['schema_version'] != 'continuous-localized-error-decomposition-v1':
        raise ValueError('the saved error-decomposition report is required')
    if digest(report['protocol']) != report['protocol_sha256']:
        raise ValueError('protocol hash mismatch')
    before = digest(report)
    rows = []
    norms = report['evaluation_feature_norms']
    for row in report['population_controls']:
        identity = {key:row[key] for key in ('ordinal','scenario','method','u','quadrature','regularized')}
        identity['kind'] = 'population'
        rows.append(fit_sensitivity(row['fit'],identity,norms))
    population_count = len(rows)
    for route in report['routes']:
        for node in route['nodes']:
            for stage in ('N','M'):
                identity = {key:route[key] for key in ('ordinal','scenario','seed','method','train_budget')}
                identity.update(kind='empirical',u=node['u'],stage=stage)
                rows.append(fit_sensitivity(node['controls'][stage]['fit'],identity,norms))
    if population_count != 128 or len(rows) != 512 or report['freeze_barrier']['new_fits'] != 512:
        raise ValueError('expected complete 128-population/384-empirical fit roster')
    if before != digest(report):
        raise RuntimeError('input report changed during pure sensitivity analysis')
    return {'schema_version':'continuous-localized-post-result-fit-sensitivity-v1',
        'decision':'POST_RESULT_ANALYTICAL_SENSITIVITY_COMPLETE_NOT_CERTIFIED',
        'captured_at_utc':datetime.now(timezone.utc).isoformat(),
        'primary_report_sha256':report_sha256,'primary_report_record_sha256':before,
        'primary_protocol_sha256':report['protocol_sha256'],
        'primary_source_bindings_preserved':report['source_sha256'],
        'analysis_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'summary':summarize(rows),
        'by_group':{name:summarize(group) for name,group in (
            ('population_regularized',[r for r in rows if r['identity']['kind']=='population' and r['identity']['regularized']]),
            ('population_unregularized',[r for r in rows if r['identity']['kind']=='population' and not r['identity']['regularized']]),
            ('empirical_N',[r for r in rows if r['identity']['kind']=='empirical' and r['identity']['stage']=='N']),
            ('empirical_M',[r for r in rows if r['identity']['kind']=='empirical' and r['identity']['stage']=='M']))},
        'evaluation_feature_norms_used':norms,'fits':rows,
        'scope':{'post_result_analysis_not_predeclared_test':True,'primary_loose_global_bounds_preserved':True,
            'new_fits_or_labels_or_oracle_evaluations':False,'learner_or_optimizer_changed':False,
            'learned_sampler_or_GPU_work':False,'interval_certified_numerical_bound':False,
            'population_quadrature_or_statistical_approximation_error_resolved':False,
            'scientific_success_or_new_acceptance_decision_claimed':False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error('new output file beneath an existing parent required')
    raw = args.report.read_bytes()
    if len(raw) > 256*1024*1024:
        raise ValueError('input report exceeds 256 MiB')
    def reject(value):
        raise ValueError('nonfinite JSON constant: '+value)
    report = json.loads(raw,parse_constant=reject)
    result = analyze_report(report,hashlib.sha256(raw).hexdigest())
    if args.report.read_bytes() != raw:
        raise RuntimeError('primary report bytes changed while reading')
    encoded = payload(result)
    with args.output.open('xb') as handle:
        handle.write(encoded)
    print(json.dumps({'decision':result['decision'],'summary':result['summary']},allow_nan=False))


if __name__ == '__main__':
    main()
