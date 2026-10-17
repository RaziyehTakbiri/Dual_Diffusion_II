"""Manufactured weighted-risk checks; no prior scientific labels or outcomes."""
from copy import deepcopy
import json
import math
from types import SimpleNamespace

import numpy as np
import pytest

from heterodiff.experiments import localized_population_risk as population
from heterodiff.models.localized_likelihood_learner import training_design


def manufactured_problem():
    X = np.tile(np.eye(35),(2,1))
    Y = np.tile(.2+.05*np.sin(np.arange(35)),2)
    b = np.full(len(Y),math.log(.2))
    w = np.full(len(Y),1/len(Y))
    return X,Y,b,w,1.,np.zeros((35,35))


def test_weighted_terms_match_direct_scalar_sums_and_analytic_derivatives():
    X,Y,b,w,M,P = manufactured_problem()
    P = np.diag(np.linspace(0.,.2,35))
    c = np.linspace(-.2,.3,35)
    objective,g,H = population.weighted_risk_terms(c,X,Y,b,w,M,P)
    f = b+X@c
    direct = sum(float(wi)*(math.exp(float(fi))-float(yi)*float(fi))/M for wi,fi,yi in zip(w,f,Y))+.5*sum(float(pi)*float(ci)**2 for pi,ci in zip(np.diag(P),c))
    assert objective == pytest.approx(direct,abs=2e-16)
    assert np.allclose(g,X.T@(w*(np.exp(f)-Y))/M+P@c,atol=1e-15,rtol=1e-14)
    assert np.allclose(H,X.T@np.diag(w*np.exp(f)/M)@X+P,atol=1e-15,rtol=1e-14)
    direction = np.cos(np.arange(35))
    step = 1e-5
    plus = population.weighted_risk_terms(c+step*direction,X,Y,b,w,M,P)
    minus = population.weighted_risk_terms(c-step*direction,X,Y,b,w,M,P)
    assert (plus[0]-minus[0])/(2*step) == pytest.approx(g@direction,abs=2e-11)
    assert np.allclose((plus[1]-minus[1])/(2*step),H@direction,atol=2e-11,rtol=1e-8)
    assert np.linalg.eigvalsh(H)[0] > 0


def test_manufactured_unpenalized_fit_recovers_known_log_mean():
    X,Y,b,w,M,P = manufactured_problem()
    before = deepcopy((X,Y,b,w,P))
    c,report = population.fit_weighted_risk(X,Y,b,w,M,3.,P,.1)
    expected = np.log(Y[:35]/.2)
    assert np.allclose(c,expected,atol=2e-7,rtol=1e-6)
    assert report['projected_gradient_max_abs'] < 1e-9
    assert report['box_first_order_gap'] < 1e-7
    assert report['final_objective'] < report['initial_objective']
    assert report['optimizer_options'] == {'maxiter':2000,'maxls':50,'ftol':1e-15,'gtol':1e-11}
    assert report['weighted_gram_minimum_eigenvalue'] == pytest.approx(1/35,rel=1e-14)
    assert report['local_hessian_is_global_strong_convexity_certificate'] is False
    assert report['computed_eigenvalues_are_interval_certified'] is False
    assert report['newton_polish_performed'] is False and report['retries'] == 0
    for actual,previous in zip((X,Y,b,w,P),before):
        assert np.array_equal(actual,previous)
    assert json.loads(json.dumps(report,allow_nan=False)) == report
    c[:] = 0.
    assert report['physical_coefficients'] != c.tolist()


def test_manufactured_box_optimum_has_zero_normal_cone_residual_and_gap():
    X,Y,b,w,M,P = manufactured_problem()
    Y[:] = .8
    b[:] = math.log(.1)
    c,report = population.fit_weighted_risk(X,Y,b,w,M,.5,P,.1)
    assert np.array_equal(c,np.full(35,.5))
    assert all(x < 0 for x in report['gradient'])
    assert report['projected_gradient'] == [0.]*35
    assert report['box_first_order_gap'] == 0.
    assert report['exact_boundary_count'] == 35


def test_projected_gradient_does_not_treat_near_boundary_as_normal_cone():
    c,g = np.zeros(35),np.ones(35)
    c[0],c[1],c[2],c[3] = -1.,-1.+1e-12,1.,1.-1e-12
    g[2:4] = -1.
    result = population.projected_gradient(c,g,1.)
    assert result[0] == result[2] == 0.
    assert result[1] == 1. and result[3] == -1.
    assert np.array_equal(g[4:],result[4:])


def test_solver_failure_is_retained_without_retry_or_polish(monkeypatch):
    X,Y,b,w,M,P = manufactured_problem()
    calls = []
    def solver(fun,initial,**kwargs):
        calls.append(kwargs)
        assert np.array_equal(initial,np.zeros(35))
        assert kwargs['method'] == 'L-BFGS-B' and kwargs['jac'] is True
        value,gradient = fun(initial)
        assert math.isfinite(value) and gradient.shape == (35,)
        return SimpleNamespace(x=initial.copy(),success=False,status=1,message='manufactured limit',nit=2000,nfev=1,njev=1)
    monkeypatch.setattr(population,'minimize',solver)
    c,report = population.fit_weighted_risk(X,Y,b,w,M,2.,P,.1)
    assert len(calls) == 1
    assert report['solver_success'] is False and report['solver_status'] == 1
    assert report['iterations'] == 2000 and report['observed_optimizer_objective_calls'] == 1
    assert report['newton_polish_performed'] is False and report['retries'] == 0
    assert np.array_equal(c,np.zeros(35))


@pytest.mark.parametrize('points',[16,32])
def test_population_quadrature_is_positive_balanced_and_exact_same_feature_family(points):
    rule = population.population_quadrature(points)
    states,z,w,X = (rule[k] for k in ('states','coordinates','weights','features'))
    assert states.shape == z.shape == w.shape == (2+32*points,)
    assert X.shape == (len(states),35)
    assert (w > 0).all() and math.fsum(w) == pytest.approx(1.,abs=3e-16)
    assert w[states==0].sum() == w[states==1].sum() == .25
    assert w[states==2].sum() == pytest.approx(.5,abs=2e-16)
    assert (abs(z[states==2]) < 4.5).all()
    assert np.array_equal(X,training_design(states,z))
    assert np.allclose(X.sum(axis=1),1.,atol=1e-15,rtol=0)
    for power in range(11):
        observed = float(w[states==2]@(z[states==2]**power))
        expected = 0. if power%2 else .5*4.5**power/(power+1)
        assert observed == pytest.approx(expected,abs=3e-10,rel=2e-15)


def test_q16_q32_weighted_grams_agree_but_no_nonlinear_exactness_claim():
    grams = []
    for points in (16,32):
        rule = population.population_quadrature(points)
        X,w = rule['features'],rule['weights']
        grams.append(X.T@(w[:,None]*X))
    assert np.allclose(grams[0],grams[1],atol=3e-17,rtol=5e-14)
    assert np.linalg.eigvalsh(grams[0])[0] > 0


@pytest.mark.parametrize('points',[True,8,24,64,16.,None])
def test_population_quadrature_refuses_nondeclared_order(points):
    with pytest.raises(ValueError):
        population.population_quadrature(points)


@pytest.mark.parametrize('problem',['shape','columns','empty','label_nan','label_zero','label_above_max','baseline_shape',
    'weight_zero','weight_negative','weight_sum','weight_shape','penalty_shape','penalty_asymmetric','penalty_indefinite',
    'masked','complex','boolean','maximum_zero','maximum_bool','minimum_zero','minimum_above_labels','baseline_below_floor','bound_zero'])
def test_weighted_fit_rejects_invalid_inputs_before_optimizer(monkeypatch,problem):
    X,Y,b,w,M,P = manufactured_problem()
    minimum,A = .1,2.
    if problem == 'shape': X = X[:,None,:]
    elif problem == 'columns': X = X[:,:34]
    elif problem == 'empty': X,Y,b,w = X[:0],Y[:0],b[:0],w[:0]
    elif problem == 'label_nan': Y[0] = np.nan
    elif problem == 'label_zero': Y[0] = 0.
    elif problem == 'label_above_max': Y[0] = 2.
    elif problem == 'baseline_shape': b = b[:,None]
    elif problem == 'weight_zero': w[0] = 0.
    elif problem == 'weight_negative': w[0] = -.1
    elif problem == 'weight_sum': w *= 2
    elif problem == 'weight_shape': w = w[:-1]
    elif problem == 'penalty_shape': P = P[:34]
    elif problem == 'penalty_asymmetric': P[0,1] = .1
    elif problem == 'penalty_indefinite': P[0,0] = -.1
    elif problem == 'masked': Y = np.ma.array(Y,mask=False)
    elif problem == 'complex': X = X.astype(complex)
    elif problem == 'boolean': X = X == 0
    elif problem == 'maximum_zero': M = 0.
    elif problem == 'maximum_bool': M = True
    elif problem == 'minimum_zero': minimum = 0.
    elif problem == 'minimum_above_labels': minimum = .5
    elif problem == 'baseline_below_floor': b[0] = math.log(.01)
    else: A = 0.
    def forbidden(*args,**kwargs):
        raise AssertionError('invalid inputs reached optimizer')
    monkeypatch.setattr(population,'minimize',forbidden)
    with pytest.raises(ValueError):
        population.fit_weighted_risk(X,Y,b,w,M,A,P,minimum)


def test_nonrepresentable_objective_is_explicit_and_not_returned_as_success():
    X,Y,b,w,M,P = manufactured_problem()
    with pytest.raises(ArithmeticError,match='not representable'):
        population.weighted_risk_terms(np.full(35,1e308),X,Y,b,w,M,P)


def test_roundoff_spectral_diagnostics_are_not_silently_made_positive(monkeypatch):
    X,Y,b,w,M,P = manufactured_problem()
    P[0,0] = -1e-16
    def solver(fun,initial,**kwargs):
        fun(initial)
        return SimpleNamespace(x=initial,success=False,status=1,message='manufactured',nit=0,nfev=1,njev=1)
    monkeypatch.setattr(population,'minimize',solver)
    _,report = population.fit_weighted_risk(X,Y,b,w,M,2.,P,.1)
    assert report['penalty_minimum_eigenvalue_computed'] == -1e-16
    assert report['negative_roundoff_eigenvalue_projected_away'] is False
    assert report['box_gap_is_outward_rounded_certificate'] is False


def test_conservative_offset_floor_uses_observed_roundoff_lower_value(monkeypatch):
    X,Y,b,w,M,P = manufactured_problem()
    floor = .1
    b[0] = math.log(floor)-5e-13
    def solver(fun,initial,**kwargs):
        fun(initial)
        return SimpleNamespace(x=initial,success=False,status=1,message='manufactured',nit=0,nfev=1,njev=1)
    monkeypatch.setattr(population,'minimize',solver)
    _,report = population.fit_weighted_risk(X,Y,b,w,M,2.,P,floor)
    assert report['conservative_baseline_density_floor_from_supplied_floor_and_observed_offset'] < floor
    assert report['conservative_baseline_density_floor_from_supplied_floor_and_observed_offset'] == math.exp(b.min())


def _manufactured_bound_diagnostics():
    return {'conservative_baseline_density_floor_from_supplied_floor_and_observed_offset':.1,
        'maximum_label':.5,'coefficient_bound':2.,'feature_maximum_row_l1_norm':1.25,
        'weighted_gram_minimum_eigenvalue':.03,'penalty_minimum_eigenvalue_computed':1e-6,
        'box_first_order_gap':2e-8}


def test_postfit_global_bound_uses_row_l1_floor_and_gap_without_solver(monkeypatch):
    fit = _manufactured_bound_diagnostics()
    original = deepcopy(fit)
    def forbidden(*args,**kwargs):
        raise AssertionError('post-fit diagnostics must not call optimizer')
    monkeypatch.setattr(population,'minimize',forbidden)
    result = population.global_bound_diagnostics(fit)
    expected = (.1/.5)*math.exp(-2*1.25)*.03+1e-6
    assert result['global_strong_convexity_lower_bound_estimate'] == pytest.approx(expected,rel=1e-15)
    assert result['coefficient_distance_upper_bound_estimate'] == pytest.approx(math.sqrt(4e-8/expected),rel=2e-15)
    assert result['vacuous'] is False
    assert result['floating_point_certificate'] is False
    assert result['local_hessian_eigenvalue_used_as_global_bound'] is False
    assert result['optimizer_or_oracle_called'] is False
    assert result['eigenvalues_baseline_floor_and_gap_are_validated_enclosures'] is False
    assert fit == original
    assert json.loads(json.dumps(result,allow_nan=False)) == result


@pytest.mark.parametrize('gram,penalty',[(0.,0.),(-1e-12,0.),(.03,-1.)])
def test_nonpositive_bound_is_vacuous_and_negative_spectra_remain_visible(gram,penalty):
    fit = _manufactured_bound_diagnostics()
    fit['weighted_gram_minimum_eigenvalue'] = gram
    fit['penalty_minimum_eigenvalue_computed'] = penalty
    result = population.global_bound_diagnostics(fit)
    assert result['vacuous'] is True
    assert result['coefficient_distance_upper_bound_estimate'] is None
    assert result['reason'] == 'NONPOSITIVE_GLOBAL_CURVATURE_ESTIMATE'
    assert result['weighted_gram_minimum_eigenvalue_computed'] == gram
    assert result['penalty_minimum_eigenvalue_computed'] == penalty
    assert result['negative_computed_eigenvalues_clipped'] is False


def test_zero_gap_with_positive_curvature_has_zero_unvalidated_distance():
    fit = _manufactured_bound_diagnostics()
    fit['box_first_order_gap'] = 0.
    result = population.global_bound_diagnostics(fit)
    assert result['coefficient_distance_upper_bound_estimate'] == 0.
    assert result['vacuous'] is False
    assert result['floating_point_certificate'] is False


def test_large_exponent_underflows_explicitly_and_retains_penalty_bound():
    fit = _manufactured_bound_diagnostics()
    fit['coefficient_bound'],fit['feature_maximum_row_l1_norm'] = 1e308,2.
    result = population.global_bound_diagnostics(fit)
    assert result['coefficient_exponent_representable'] is False
    assert result['likelihood_curvature_factor'] == 0.
    assert result['global_strong_convexity_lower_bound_estimate'] == 1e-6
    assert json.loads(json.dumps(result,allow_nan=False)) == result


def test_nonrepresentable_distance_is_vacuous_and_strict_json():
    fit = _manufactured_bound_diagnostics()
    fit['weighted_gram_minimum_eigenvalue'] = 0.
    fit['penalty_minimum_eigenvalue_computed'] = 1e-320
    fit['box_first_order_gap'] = 1e308
    result = population.global_bound_diagnostics(fit)
    assert result['positive_finite_curvature_estimate'] is True
    assert result['vacuous'] is True
    assert result['coefficient_distance_upper_bound_estimate'] is None
    assert result['reason'] == 'COEFFICIENT_DISTANCE_ESTIMATE_NOT_REPRESENTABLE'
    assert json.loads(json.dumps(result,allow_nan=False)) == result


@pytest.mark.parametrize('key,value',[
    ('box_first_order_gap',-1.),('box_first_order_gap',np.nan),
    ('coefficient_bound',0.),('coefficient_bound',True),
    ('feature_maximum_row_l1_norm',-1.),('maximum_label',0.),
    ('conservative_baseline_density_floor_from_supplied_floor_and_observed_offset',1.)])
def test_global_bound_refuses_invalid_diagnostics(key,value):
    fit = _manufactured_bound_diagnostics()
    fit[key] = value
    with pytest.raises(ValueError):
        population.global_bound_diagnostics(fit)


def test_global_bound_refuses_missing_diagnostics():
    with pytest.raises(ValueError,match='missing'):
        population.global_bound_diagnostics({})
