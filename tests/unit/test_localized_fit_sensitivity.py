"""Post-result sensitivity theorem arithmetic on manufactured saved records."""
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[2]/'scripts/analyze_localized_fit_sensitivity.py'
SPEC = importlib.util.spec_from_file_location('localized_fit_sensitivity_script',SOURCE)
sensitivity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sensitivity)


@pytest.mark.parametrize('mean',[.8,.1,1e-6])
def test_scalar_exponential_example_is_sharp_without_any_fit(mean):
    result = sensitivity.sensitivity_estimate([1-mean],1.,1.)
    expected = -math.log(mean)
    assert result['coefficient_distance_upper_bound_estimate'] == pytest.approx(expected,rel=1e-10,abs=1e-14)
    assert result['raw_gradient_not_infinity_or_projected_norm'] is True
    assert result['floating_point_interval_certificate'] is False
    assert result['predeclared_acceptance_outcome'] is False


def test_constrained_optimum_is_covered_by_raw_gradient_bound():
    # F(x)=exp(x)-.1*x on [-.2,.2]; its optimum is the lower boundary.
    observed,optimum = .1,-.2
    gradient,hessian = math.exp(observed)-.1,math.exp(observed)
    result = sensitivity.sensitivity_estimate([gradient],hessian,1.)
    assert abs(observed-optimum) <= result['coefficient_distance_upper_bound_estimate']
    # At a constrained optimum the raw gradient need not vanish. Retaining it
    # produces a possibly loose but still valid nonnegative radius.
    at_optimum = sensitivity.sensitivity_estimate([math.exp(-.2)-.1],math.exp(-.2),1.)
    assert at_optimum['coefficient_distance_upper_bound_estimate'] > 0.


def test_zero_feature_quadratic_limit_and_zero_gradient():
    result = sensitivity.sensitivity_estimate([.06],.3,0.)
    assert result['coefficient_distance_upper_bound_estimate'] == pytest.approx(.2)
    assert result['reason'] == 'L_ZERO_QUADRATIC_LIMIT_UNVALIDATED'
    zero = sensitivity.sensitivity_estimate([0.,0.],1.,2.)
    assert zero['coefficient_distance_upper_bound_estimate'] == 0.


def test_raw_euclidean_gradient_is_not_infinity_norm():
    result = sensitivity.sensitivity_estimate([.03,.04],1.,1.)
    assert result['raw_gradient_l2'] == .05
    assert result['coefficient_distance_upper_bound_estimate'] == pytest.approx(-math.log1p(-.05))


@pytest.mark.parametrize('gradient',[1.,1.5])
def test_ratio_at_least_one_is_vacuous_not_forced_to_finite_radius(gradient):
    result = sensitivity.sensitivity_estimate([gradient],1.,1.)
    assert result['vacuous'] is True
    assert result['coefficient_distance_upper_bound_estimate'] is None
    assert result['reason'] == 'SENSITIVITY_RATIO_AT_LEAST_ONE'


@pytest.mark.parametrize('eigenvalue',[0.,-1.])
def test_nonpositive_curvature_is_vacuous(eigenvalue):
    result = sensitivity.sensitivity_estimate([.01],eigenvalue,1.)
    assert result['vacuous'] is True
    assert result['reason'] == 'NONPOSITIVE_LOCAL_HESSIAN_EIGENVALUE'


def test_tiny_feature_norm_does_not_underflow_radius_to_zero():
    result = sensitivity.sensitivity_estimate([1e-10],1.,5e-324)
    assert result['L_times_gradient_to_curvature_ratio'] == 0.
    assert result['coefficient_distance_upper_bound_estimate'] == 1e-10


def test_unrepresentable_norm_is_vacuous_and_strict_json():
    result = sensitivity.sensitivity_estimate([1e308]*4,1.,1.)
    assert result['raw_gradient_l2'] is None and result['vacuous'] is True
    assert json.loads(sensitivity.payload(result)) == result


@pytest.mark.parametrize('g,lam,L',[
    ([],1.,1.),([True],1.,1.),([complex(1)],1.,1.),([float('nan')],1.,1.),
    ([1.],True,1.),([1.],float('inf'),1.),([1.],1.,-1.),([1.],1.,True)])
def test_invalid_inputs_are_refused(g,lam,L):
    with pytest.raises(ValueError):
        sensitivity.sensitivity_estimate(g,lam,L)


def manufactured_fit():
    return {'physical_coefficients':[0.]*35,'coefficient_bound':2.,'exact_boundary_count':0,
        'gradient':[.01]+[0.]*34,'local_hessian_minimum_eigenvalue':1.,
        'feature_maximum_row_l1_norm':1.,
        'global_bounds':{'coefficient_distance_upper_bound_estimate':100.,'primary_preserved':True}}


def manufactured_norms():
    return {name:{'max_row_l2':float(i),'continuous_spectral_norm_div_sqrt_n':i/10}
        for i,name in enumerate(('value','gradient','hessian'),1)}


def test_finite_probe_propagation_keeps_primary_bounds_unchanged():
    fit,norms = manufactured_fit(),manufactured_norms()
    before = deepcopy((fit,norms))
    row = sensitivity.fit_sensitivity(fit,{'kind':'manufactured'},norms)
    distance = -math.log1p(-.01)
    for i,name in enumerate(('value','gradient','hessian'),1):
        assert row['finite_probe_responses'][name]['max_abs_optimum_response_estimate'] == pytest.approx(i*distance)
        assert row['finite_probe_responses'][name]['continuous_rms_optimum_response_estimate'] == pytest.approx(i*distance/10)
    assert row['preserved_primary_global_bounds'] == before[0]['global_bounds']
    assert row['primary_global_bounds_sha256'] == sensitivity.digest(before[0]['global_bounds'])
    assert (fit,norms) == before
    assert json.loads(sensitivity.payload(row)) == row


def test_saved_activity_mismatch_is_refused():
    fit = manufactured_fit()
    fit['physical_coefficients'][0] = 2.
    with pytest.raises(ValueError,match='boundary count'):
        sensitivity.fit_sensitivity(fit,{},manufactured_norms())


def manufactured_report():
    report = {'schema_version':'continuous-localized-error-decomposition-v1',
        'protocol':{'manufactured':True},'source_sha256':{'manufactured':'not_source'},
        'freeze_barrier':{'new_fits':512},'evaluation_feature_norms':manufactured_norms(),
        'population_controls':[],'routes':[]}
    report['protocol_sha256'] = sensitivity.digest(report['protocol'])
    for i in range(128):
        report['population_controls'].append({'ordinal':i+1,'scenario':'manufactured','method':'fixed',
            'u':(i%8)/8,'quadrature':16 if i%2 else 32,'regularized':bool(i%2),'fit':manufactured_fit()})
    for i in range(24):
        report['routes'].append({'ordinal':i+1,'scenario':'manufactured','method':'fixed','seed':i,
            'train_budget':1024,'nodes':[{'u':j/8,'controls':{stage:{'fit':manufactured_fit()} for stage in ('N','M')}} for j in range(8)]})
    return report


def test_complete_saved_roster_analysis_is_pure_and_preserves_predeclared_outcome():
    report = manufactured_report()
    before = sensitivity.digest(report)
    result = sensitivity.analyze_report(report,'manufactured-report-bytes-sha')
    assert result['summary']['fit_count'] == result['summary']['nonvacuous_unvalidated_count'] == 512
    assert result['summary']['strictly_interior_count'] == 512
    assert result['summary']['primary_predeclared_distance_estimate_range'] == {'minimum':100.,'maximum':100.}
    assert result['primary_report_record_sha256'] == before == sensitivity.digest(report)
    assert result['scope']['post_result_analysis_not_predeclared_test'] is True
    assert result['scope']['new_fits_or_labels_or_oracle_evaluations'] is False
    assert result['scope']['scientific_success_or_new_acceptance_decision_claimed'] is False
    assert json.loads(sensitivity.payload(result))['summary']['fit_count'] == 512


def test_incomplete_roster_and_bad_protocol_are_refused():
    report = manufactured_report()
    report['population_controls'].pop()
    with pytest.raises(ValueError,match='complete'):
        sensitivity.analyze_report(report,'manufactured')
    report = manufactured_report()
    report['protocol']['mutated'] = True
    with pytest.raises(ValueError,match='protocol hash'):
        sensitivity.analyze_report(report,'manufactured')
