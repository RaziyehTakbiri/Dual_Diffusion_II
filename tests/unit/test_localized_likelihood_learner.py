"""Manufactured convex-learner and spline checks, with no backward labels."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import math
import json

import numpy as np
import pytest

from heterodiff.models import localized_likelihood_learner as learner


def test_spline_partition_nonnegativity_and_tied_endpoint_derivatives():
    z = np.r_[-1e100, np.linspace(-4.5, 4.5, 129), 1e100]
    value = learner.spline_features(z)
    assert value.shape == (len(z), 33)
    assert value.min() >= -1e-15
    np.testing.assert_allclose(value.sum(axis=1), 1., atol=2e-15, rtol=0.)
    np.testing.assert_array_equal(value[0], np.eye(33)[0])
    np.testing.assert_array_equal(value[-1], np.eye(33)[-1])
    for order in (1, 2):
        derivative = learner.spline_features(z, order)
        np.testing.assert_allclose(derivative.sum(axis=1), 0., atol=2e-12, rtol=0.)
        np.testing.assert_array_equal(derivative[[0, 1, -2, -1]], np.zeros((4, 33)))
    value[:] = 100.
    assert learner.spline_features(np.array([0.])).max() <= 1.


def test_analytic_spline_derivatives_match_independent_centered_differences():
    z = np.array([-4.1, -3.17, -.83, .17, 2.39, 4.1])
    epsilon = 1e-5
    value_derivative = (learner.spline_features(z+epsilon)-learner.spline_features(z-epsilon))/(2*epsilon)
    score_derivative = (learner.spline_features(z+epsilon, 1)-learner.spline_features(z-epsilon, 1))/(2*epsilon)
    np.testing.assert_allclose(learner.spline_features(z, 1), value_derivative, atol=2e-8, rtol=2e-8)
    np.testing.assert_allclose(learner.spline_features(z, 2), score_derivative, atol=2e-7, rtol=2e-8)


def test_state_design_keeps_atoms_separate_and_their_scores_zero():
    states, z = np.array([0, 1, 2, 2]), np.array([0., 0., -.5, .5])
    features = learner.training_design(states, z)
    assert features.shape == (4, 35)
    np.testing.assert_array_equal(features[0], np.eye(35)[-2])
    np.testing.assert_array_equal(features[1], np.eye(35)[-1])
    np.testing.assert_array_equal(features[2:, -2:], np.zeros((2, 2)))
    for order in (1, 2):
        derivative = learner.training_design(states, z, order)
        np.testing.assert_array_equal(derivative[:2], np.zeros((2, 35)))
        np.testing.assert_array_equal(derivative[:, -2:], np.zeros((4, 2)))


def test_roughness_is_symmetric_psd_and_independently_integrates_core_curvature():
    actual = learner.roughness_matrix()
    np.testing.assert_allclose(actual, actual.T, atol=2e-12, rtol=0.)
    assert np.linalg.eigvalsh(actual).min() >= -1e-8
    roots, weights = np.polynomial.legendre.leggauss(7)
    nodes = np.linspace(-4.5, 4.5, 33)
    independent = np.zeros((35, 35))
    for left, right in zip(nodes, nodes[1:]):
        half = (right-left)/2
        features = learner.spline_features((right+left)/2+half*roots, 2)
        independent[:33, :33] += features.T@((weights*half/9)[:, None]*features)
    np.testing.assert_allclose(actual, independent, atol=2e-10, rtol=2e-13)
    np.testing.assert_array_equal(actual[-2:], np.zeros((2, 35)))
    np.testing.assert_allclose(actual@np.ones(35), 0., atol=2e-11, rtol=0.)


@pytest.mark.parametrize('tau', [1., .125])
def test_likelihood_risk_gradient_and_physical_reparameterization(tau):
    rng = np.random.default_rng(31)
    features = rng.uniform(size=(17, 35))
    features /= features.sum(axis=1, keepdims=True)
    labels = rng.uniform(.01, .4, size=17)
    baseline = rng.uniform(-3., -1., size=17)
    coefficients = rng.normal(0., .1, size=35)
    roughness = learner.roughness_matrix()
    value, gradient = learner.risk_value_gradient(coefficients, features, labels, baseline,
        tau, .5, roughness)
    physical_value, physical_gradient = learner.risk_value_gradient(tau*coefficients,
        features, labels, baseline, 1., .5, roughness)
    assert value == pytest.approx(physical_value, abs=1e-14)
    np.testing.assert_allclose(gradient, tau*physical_gradient, atol=2e-15, rtol=2e-15)
    potential = baseline+tau*(features@coefficients)
    expected_value = np.mean(np.exp(potential)-labels*potential)/.5
    expected_value += .5*learner.SMOOTHNESS*tau**2*(coefficients@roughness@coefficients)
    expected_value += .5*learner.RIDGE*tau**2*(coefficients@coefficients)
    assert value == pytest.approx(expected_value, abs=1e-15)
    epsilon = 2e-6
    numerical = []
    for axis in np.eye(35):
        plus = learner.risk_value_gradient(coefficients+epsilon*axis, features, labels,
            baseline, tau, .5, roughness)[0]
        minus = learner.risk_value_gradient(coefficients-epsilon*axis, features, labels,
            baseline, tau, .5, roughness)[0]
        numerical.append((plus-minus)/(2*epsilon))
    np.testing.assert_allclose(gradient, numerical, atol=1e-10, rtol=1e-7)


def test_convex_objective_has_positive_semidefinite_independent_hessian():
    rng = np.random.default_rng(20)
    features = rng.uniform(size=(9, 35))
    coefficients, other = rng.normal(0., .01, size=(2, 35))
    labels, baseline, tau, maximum = np.full(9, .1), np.full(9, -2.), .5, .5
    roughness = learner.roughness_matrix()
    def risk(c):
        return learner.risk_value_gradient(c, features, labels, baseline, tau, maximum, roughness)[0]
    assert risk((coefficients+other)/2) <= (risk(coefficients)+risk(other))/2+1e-15
    predicted = np.exp(baseline+tau*features@coefficients)
    hessian = tau**2*(features.T@(predicted[:, None]*features))/(len(labels)*maximum)
    hessian += learner.SMOOTHNESS*tau**2*roughness+learner.RIDGE*tau**2*np.eye(35)
    assert np.linalg.eigvalsh(hessian).min() > 0


@pytest.mark.parametrize('tau', [1., .125])
def test_manufactured_constant_likelihood_fit_improves_risk_and_reports_fixed_box(tau):
    features, labels, baseline = np.eye(35), np.full(35, .2), np.full(35, math.log(.1))
    before = deepcopy((features, labels, baseline))
    model, record = learner.fit_likelihood(features, labels, baseline, tau, .5, .01,
        roughness=np.zeros((35, 35)))
    bound = 2*math.log(.5/.01)
    assert record['physical_coefficient_bound'] == bound
    assert model.coefficient_bound == record['quotient_coefficient_bound'] == bound/tau
    assert record['solver_success'] is True
    assert record['final_penalized_risk'] < record['initial_penalized_risk']
    assert record['projected_gradient_max_abs'] < 2e-7
    assert record['coefficient_boundary_count'] == 0
    np.testing.assert_allclose(np.exp(baseline+tau*features@model.coefficients), labels,
        atol=2e-5, rtol=0.)
    np.testing.assert_allclose(record['physical_coefficients'], tau*np.asarray(model.coefficients), atol=0., rtol=0.)
    assert model.real_absolute_bound <= bound
    assert record['hessian_score_or_exact_likelihood_labels_consumed'] is False
    assert record['regularization_selected_from_validation_or_oracle'] is False
    json.dumps(record, allow_nan=False)
    for actual, expected in zip((features, labels, baseline), before):
        np.testing.assert_array_equal(actual, expected)
    with pytest.raises(FrozenInstanceError):
        model.remaining_time = 1.


def test_frozen_model_bound_includes_atoms_and_constant_tails():
    coefficients = tuple(np.linspace(-2., 2., 35))
    model = learner.LearnedLocalizedResidual(coefficients, .125, 2.)
    states = np.r_[0, 1, np.full(257, 2)]
    z = np.r_[0., 0., np.linspace(-10., 10., 257)]
    output = model.evaluate(states, z)
    assert np.max(abs(output['value'])) <= model.real_absolute_bound*(1+1e-14)
    assert model.real_absolute_bound == .25
    assert output['value'][0] == .125*coefficients[-2]
    assert output['value'][1] == .125*coefficients[-1]
    for key in ('gradient', 'hessian'):
        assert output[key][0] == output[key][1] == 0.
        assert output[key][2] == output[key][-1] == 0.
    terminal = learner.LearnedLocalizedResidual(coefficients, 0., 2.)
    for value in terminal.evaluate(states, z).values():
        np.testing.assert_array_equal(value, np.zeros(len(states)))


@pytest.mark.parametrize('case', ['masked', 'boolean', 'complex', 'shape', 'nan',
    'below_floor', 'above_maximum', 'empty', 'zero_tau', 'bool_tau', 'nan_max',
    'invalid_bounds', 'roughness_shape', 'roughness_asymmetric', 'roughness_negative'])
def test_bad_fit_inputs_are_refused_before_optimizer(monkeypatch, case):
    features, labels, baseline = np.eye(35), np.full(35, .2), np.full(35, -2.)
    tau, maximum, minimum, roughness = 1., .5, .01, np.zeros((35, 35))
    if case == 'masked': labels = np.ma.array(labels, mask=False)
    elif case == 'boolean': features = features > 0
    elif case == 'complex': baseline = baseline.astype(complex)
    elif case == 'shape': labels = labels[:, None]
    elif case == 'nan': labels[0] = math.nan
    elif case == 'below_floor': labels[0] = .001
    elif case == 'above_maximum': labels[0] = .6
    elif case == 'empty': features, labels, baseline = features[:0], labels[:0], baseline[:0]
    elif case == 'zero_tau': tau = 0.
    elif case == 'bool_tau': tau = True
    elif case == 'nan_max': maximum = math.nan
    elif case == 'invalid_bounds': minimum = 1.
    elif case == 'roughness_shape': roughness = np.zeros((34, 34))
    elif case == 'roughness_asymmetric': roughness[0, 1] = 1.
    else: roughness[0, 0] = -1.
    def forbidden(*args, **kwargs):
        raise AssertionError('optimizer must not be entered')
    monkeypatch.setattr(learner, 'minimize', forbidden)
    with pytest.raises(ValueError):
        learner.fit_likelihood(features, labels, baseline, tau, maximum, minimum, roughness)


@pytest.mark.parametrize('derivative', [True, -1, 3, 1.5])
def test_bad_derivative_queries_are_refused_even_for_all_atomic_rows(derivative):
    with pytest.raises(ValueError):
        learner.training_design(np.array([0, 1]), np.array([0., 0.]), derivative)

