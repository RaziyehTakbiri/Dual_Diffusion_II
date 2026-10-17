"""Manufactured C2 interpolation and score-only finite-difference checks."""

from dataclasses import FrozenInstanceError
import ast
import inspect
import math

import numpy as np
from numpy.polynomial import Polynomial
import pytest

from heterodiff.models.localized_fiber_residual import (
    LocalizedFiberResidual, MAXIMUM_CORE_CELLS, estimate_hessians_from_scores,
)


def _polynomial_model(polynomial, knots=(-2., -.3, .8, 2.), remaining_time=.6, collar_width=1.):
    x = np.asarray(knots)
    return LocalizedFiberResidual.from_jets(knots, tuple(polynomial(x)), tuple(polynomial.deriv(1)(x)),
        tuple(polynomial.deriv(2)(x)), remaining_time, collar_width)


def _bernstein(controls, parameter):
    # Direct Bernstein sum independently checks de Casteljau evaluation.
    degree = len(controls) - 1
    return sum(math.comb(degree, k) * parameter ** k * (1 - parameter) ** (degree - k) * value
               for k, value in enumerate(controls))


@pytest.mark.parametrize('degree', range(6))
def test_quintic_hermite_reproduces_manufactured_polynomials_in_core(degree):
    polynomial = Polynomial(tuple((-1) ** k / (k + 1) for k in range(degree + 1)))
    residual = _polynomial_model(polynomial)
    x = np.linspace(-2., 2., 101)
    result = residual.evaluate(x)
    assert np.allclose(result['value'], .6 * polynomial(x), rtol=3e-13, atol=3e-13)
    assert np.allclose(result['gradient'], .6 * polynomial.deriv(1)(x), rtol=3e-12, atol=3e-12)
    assert np.allclose(result['hessian'], .6 * polynomial.deriv(2)(x), rtol=3e-11, atol=3e-11)


def test_controls_match_endpoint_value_gradient_and_hessian_formulas():
    core = (-1., .7, 2.)
    values, gradients, hessians = (.5, -.3, .9), (.7, -.2, .4), (-.1, .3, -.6)
    residual = LocalizedFiberResidual.from_jets(core, values, gradients, hessians, 1., .8)
    full_values = (values[0],) + values + (values[-1],)
    full_gradients = (0.,) + gradients + (0.,)
    full_hessians = (0.,) + hessians + (0.,)
    assert residual.core_knots == core
    assert residual.knots == (-1.8, -1., .7, 2., 2.8)
    assert len(residual.controls) == len(core) + 1
    assert all(type(row) is tuple and len(row) == 6 for row in residual.controls)
    for i, (left, right) in enumerate(zip(residual.knots, residual.knots[1:])):
        b = residual.controls[i]
        width = right - left
        observed = (b[0], b[5], 5 * (b[1] - b[0]) / width, 5 * (b[5] - b[4]) / width,
                    20 * (b[2] - 2 * b[1] + b[0]) / width ** 2,
                    20 * (b[5] - 2 * b[4] + b[3]) / width ** 2)
        wanted = (full_values[i], full_values[i + 1], full_gradients[i], full_gradients[i + 1],
                  full_hessians[i], full_hessians[i + 1])
        assert observed == pytest.approx(wanted, abs=5e-14)


@pytest.mark.parametrize('cells', [64, 128, 256, MAXIMUM_CORE_CELLS])
def test_all_core_knots_share_the_declared_c2_jets(cells):
    x = np.linspace(-4.5, 4.5, cells + 1)
    residual = LocalizedFiberResidual.from_jets(tuple(x), tuple(np.sin(x)), tuple(np.cos(x)), tuple(-np.sin(x)), .375)
    at_knots = residual.evaluate(x)
    assert np.allclose(at_knots['value'], .375 * np.sin(x), atol=2e-15, rtol=0.)
    assert np.allclose(at_knots['gradient'], .375 * np.cos(x), atol=2e-13, rtol=0.)
    assert np.allclose(at_knots['hessian'], -.375 * np.sin(x), atol=2e-10, rtol=0.)
    # Independently compare the Bernstein endpoint derivatives from both
    # incident cells, including each core/collar join.
    for i in range(1, len(residual.knots) - 1):
        before, after = residual.controls[i - 1], residual.controls[i]
        left_width = residual.knots[i] - residual.knots[i - 1]
        right_width = residual.knots[i + 1] - residual.knots[i]
        assert before[-1] == after[0]
        assert 5 * (before[-1] - before[-2]) / left_width == pytest.approx(
            5 * (after[1] - after[0]) / right_width, abs=2e-12)
        assert 20 * (before[-1] - 2 * before[-2] + before[-3]) / left_width ** 2 == pytest.approx(
            20 * (after[2] - 2 * after[1] + after[0]) / right_width ** 2, abs=9e-10)


def test_collars_smooth_to_same_endpoint_values_with_constant_outer_tails():
    residual = LocalizedFiberResidual.from_jets((-1., 1.), (2., -3.), (1.2, -.8), (.7, .4), .5, 1.)
    output = residual.evaluate(np.array([-1e300, -2., 2., 1e300]))
    assert np.array_equal(output['value'], np.array([1., 1., -1.5, -1.5]))
    assert np.array_equal(output['gradient'], np.zeros(4))
    assert np.array_equal(output['hessian'], np.zeros(4))
    # Inside each collar, values and derivatives are not clamped to the core.
    collar = residual.evaluate(np.array([-1.5, 1.5]))
    assert not np.array_equal(collar['value'], np.array([1., -1.5]))
    assert np.all(np.abs(collar['gradient']) > .001)
    near = residual.evaluate(np.array([-2. + 1e-7, 2. - 1e-7]))
    assert np.max(np.abs(near['gradient'])) < 1e-12
    assert np.max(np.abs(near['hessian'])) < 3e-6


def test_de_casteljau_and_derivative_evaluations_match_separate_bernstein_sums():
    residual = _polynomial_model(Polynomial((.2, -.3, .4, -.1, .03)), collar_width=.7)
    for i, (left, right) in enumerate(zip(residual.knots, residual.knots[1:])):
        b = residual.controls[i]
        width = right - left
        first = tuple(5 * (b[k + 1] - b[k]) / width for k in range(5))
        second = tuple(20 * (b[k + 2] - 2 * b[k + 1] + b[k]) / width ** 2 for k in range(4))
        for t in (0., .2, .5, .8, 1.):
            x = left + width * t
            result = residual.evaluate(x)
            assert float(result['value']) == pytest.approx(.6 * _bernstein(b, t), abs=3e-14)
            assert float(result['gradient']) == pytest.approx(.6 * _bernstein(first, t), abs=4e-14)
            assert float(result['hessian']) == pytest.approx(.6 * _bernstein(second, t), abs=6e-13)


def test_analytic_coordinate_derivatives_match_finite_differences_in_core_and_collars():
    residual = _polynomial_model(Polynomial((.2, -.3, .4, -.1, .03)))
    z = np.array([-2.8, -2.4, -1.6, -.6, .2, 1.4, 2.3, 2.7])
    step = 2e-5
    middle, plus, minus = residual.evaluate(z), residual.evaluate(z + step), residual.evaluate(z - step)
    assert np.allclose(middle['gradient'], (plus['value'] - minus['value']) / (2 * step), rtol=3e-7, atol=2e-8)
    assert np.allclose(middle['hessian'], (plus['value'] - 2 * middle['value'] + minus['value']) / step ** 2,
                       rtol=5e-5, atol=7e-6)


def test_convex_hull_bound_includes_collar_overshoot():
    # Equal zero values at both core knots do not bound the collar values.
    residual = LocalizedFiberResidual.from_jets((-1., 1.), (0., 0.), (5., -4.), (3., -2.), .4)
    max_control = max(abs(value) for row in residual.controls for value in row)
    assert residual.real_arithmetic_bound == .4 * max_control
    assert max(abs(value) for row in (residual.controls[0], residual.controls[-1]) for value in row) > 0.
    for i, (left, right) in enumerate(zip(residual.knots, residual.knots[1:])):
        values = residual.evaluate(np.linspace(left, right, 101))['value']
        assert values.min() >= .4 * min(residual.controls[i]) - 3e-15
        assert values.max() <= .4 * max(residual.controls[i]) + 3e-15
        assert np.max(np.abs(values)) <= residual.real_arithmetic_bound + 3e-15
    assert 'NOT an FP-safe' in type(residual).real_arithmetic_bound.__doc__


@pytest.mark.parametrize('shape', [(), (4,), (2, 3), (2, 1, 3), (0,)])
def test_evaluation_preserves_shape_and_returns_fresh_arrays(shape):
    z = np.linspace(-3., 3., math.prod(shape) if shape else 1).reshape(shape)
    residual = _polynomial_model(Polynomial((.3, -.1, .2)))
    output = residual.evaluate(z)
    assert set(output) == {'value', 'gradient', 'hessian'}
    assert all(type(value) is np.ndarray and value.shape == shape and value.dtype == np.float64 for value in output.values())
    saved = output['value'].copy()
    output['value'][...] = 100.
    assert np.array_equal(residual.evaluate(z)['value'], saved)


def test_quotient_jets_are_gated_once_and_terminal_is_exact_zero():
    polynomial = Polynomial((.4, -.2, .3))
    full = _polynomial_model(polynomial, remaining_time=1.)
    part = _polynomial_model(polynomial, remaining_time=.125)
    terminal = _polynomial_model(polynomial, remaining_time=0.)
    z = np.array([-1e300, -2.5, -.3, 1.5, 2.5, 1e300])
    for key in ('value', 'gradient', 'hessian'):
        assert np.array_equal(part.evaluate(z)[key], .125 * full.evaluate(z)[key])
        assert np.array_equal(terminal.evaluate(z)[key], np.zeros_like(z))
        assert not np.signbit(terminal.evaluate(z)[key]).any()
    assert terminal.real_arithmetic_bound == 0.


def test_validated_factory_and_nested_coefficients_are_immutable():
    residual = _polynomial_model(Polynomial((.3, -.1, .2)))
    with pytest.raises(TypeError, match='from_jets'):
        LocalizedFiberResidual()
    with pytest.raises(FrozenInstanceError):
        residual.remaining_time = .2
    with pytest.raises(FrozenInstanceError):
        residual.controls = ()
    assert type(residual.knots) is tuple
    assert type(residual.controls) is tuple
    assert all(type(row) is tuple for row in residual.controls)
    assert hash(residual) == hash(_polynomial_model(Polynomial((.3, -.1, .2))))


@pytest.mark.parametrize('degree', range(5))
def test_score_only_five_point_rules_exactly_differentiate_quartic_polynomials(degree):
    x = np.linspace(-2., 2., 17)
    score = Polynomial(tuple((-1) ** k / (k + 1) for k in range(degree + 1)))
    estimated = estimate_hessians_from_scores(tuple(x), tuple(score(x)))
    assert type(estimated) is tuple
    assert np.allclose(estimated, score.deriv(1)(x), rtol=0., atol=7e-14)


def test_score_only_rules_are_fourth_order_including_one_sided_boundaries():
    errors = []
    for count in (16, 32, 64):
        x = np.linspace(-1., 1., count + 1)
        estimated = np.array(estimate_hessians_from_scores(tuple(x), tuple(np.sin(x))))
        errors.append(np.max(np.abs(estimated - np.cos(x))))
    assert all(12 < coarse / fine < 21 for coarse, fine in zip(errors, errors[1:]))
    assert errors[-1] < 2e-7


def test_score_only_rules_use_correct_mirrored_stencil_signs():
    knots = tuple(float(x) for x in range(5))
    for location in range(5):
        scores = tuple(1. if k == location else 0. for k in range(5))
        result = estimate_hessians_from_scores(knots, scores)
        expected_first = (-25., 48., -36., 16., -3.)[location] / 12
        expected_next = (-3., -10., 18., -6., 1.)[location] / 12
        expected_middle = (1., -8., 0., 8., -1.)[location] / 12
        expected_last = -( -25., 48., -36., 16., -3.)[4 - location] / 12
        expected_penultimate = -(-3., -10., 18., -6., 1.)[4 - location] / 12
        assert result == pytest.approx((expected_first, expected_next, expected_middle, expected_penultimate, expected_last))


def test_score_derivatives_do_not_silently_zero_when_twelve_times_width_overflows():
    width = 3e307
    knots = tuple(index * width for index in range(5))
    result = estimate_hessians_from_scores(knots, (0., 1., 2., 3., 4.))
    expected = 1 / width
    assert expected > 0
    assert all(value > 0 for value in result)
    assert np.allclose(np.asarray(result) / expected, 1., rtol=5e-15, atol=0.)


@pytest.mark.parametrize('knots', [[], (), (0.,), (0., 0.), (1., 0.), (0., math.nan), (False, 1.),
                                  tuple(float(i) for i in range(MAXIMUM_CORE_CELLS + 2))])
def test_invalid_core_knots_are_refused(knots):
    with pytest.raises(ValueError):
        LocalizedFiberResidual.from_jets(knots, (), (), (), 1.)


@pytest.mark.parametrize('field,bad', [('values', [1., 2.]), ('gradients', (.2,)), ('hessians', (0., math.inf)),
                                    ('values', (True, 2.)), ('values', (1j, 2.)), ('hessians', ('0', 0.))])
def test_invalid_or_mutable_jet_inputs_are_refused(field, bad):
    inputs = dict(knots=(0., 1.), values=(1., 2.), gradients=(.2, .3), hessians=(0., 0.), remaining_time=1.)
    inputs[field] = bad
    with pytest.raises(ValueError):
        LocalizedFiberResidual.from_jets(**inputs)


@pytest.mark.parametrize('remaining,collar', [(-1., 1.), (True, 1.), (math.inf, 1.), (math.nan, 1.),
                                           (1., 0.), (1., -1.), (1., True), (1., math.inf), (1., math.nan)])
def test_invalid_gate_or_collar_is_refused(remaining, collar):
    with pytest.raises(ValueError):
        LocalizedFiberResidual.from_jets((0., 1.), (0., 0.), (0., 0.), (0., 0.), remaining, collar)


@pytest.mark.parametrize('coordinates', [math.inf, math.nan, [True], [1j], ['1'], np.array([1.], dtype=object),
                                        np.ma.array([1.], mask=[True])])
def test_invalid_coordinates_are_refused_even_at_terminal(coordinates):
    for time in (0., 1.):
        with pytest.raises(ValueError):
            _polynomial_model(Polynomial((1.,)), remaining_time=time).evaluate(coordinates)


@pytest.mark.parametrize('knots,scores', [((0., 1., 2., 3.), (0.,) * 4), ((0., 1., 2., 3., 4.1), (0.,) * 5),
                                      ((0., 1., 2., 3., 4.), [0.] * 5), ((0., 1., 2., 3., 4.), (0.,) * 4)])
def test_score_only_estimator_refuses_short_nonuniform_or_mismatched_inputs(knots, scores):
    with pytest.raises(ValueError):
        estimate_hessians_from_scores(knots, scores)


def test_unrepresentable_collars_controls_bounds_and_derivatives_are_refused():
    with pytest.raises(ValueError, match='collar'):
        LocalizedFiberResidual.from_jets((1e100, 2e100), (0., 0.), (0., 0.), (0., 0.), 1., 1.)
    with pytest.raises(ArithmeticError):
        LocalizedFiberResidual.from_jets((0., 1.), (0., 0.), (1e308, 1e308), (0., 0.), 1., 100.)
    with pytest.raises(ArithmeticError, match='bound'):
        LocalizedFiberResidual.from_jets((0., 1.), (1e308, 1e308), (0., 0.), (0., 0.), 2.)
    with pytest.raises(ArithmeticError):
        LocalizedFiberResidual.from_jets((0., 1e-308), (0., 1.), (0., 0.), (0., 0.), 1.)


def test_new_module_has_no_sampler_native_model_or_fitting_dependency():
    module = inspect.getmodule(LocalizedFiberResidual)
    tree = ast.parse(inspect.getsource(module))
    names = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    names.extend(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert not any(name and any(token in name for token in ('torch', 'sampler', 'training', 'guide', 'heterodiff')) for name in names)
    assert not hasattr(module, 'fit')
