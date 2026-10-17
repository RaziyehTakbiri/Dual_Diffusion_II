"""Analytic, finite-difference and immutability checks for compact residuals."""

from dataclasses import FrozenInstanceError
import ast
import inspect
import math

import numpy as np
from numpy.polynomial import Chebyshev
import pytest

from heterodiff.models.compact_fiber_residual import CompactFiberResidual, MAXIMUM_DEGREE, design


@pytest.mark.parametrize('shape', [(), (7,), (2, 3), (2, 1, 3), (0,)])
def test_design_and_evaluation_preserve_coordinate_shape(shape):
    z = np.linspace(-2., 2., math.prod(shape) if shape else 1).reshape(shape)
    residual = CompactFiberResidual((.4, -.2, .1, .3), .7)
    matrices = design(z, residual.degree, residual.remaining_time, residual.coordinate_scale)
    assert all(matrix.shape == shape + (4,) for matrix in matrices)
    values = residual.evaluate(z)
    assert set(values) == {'value', 'gradient', 'hessian'}
    assert all(type(value) is np.ndarray and value.shape == shape and value.dtype == np.float64 for value in values.values())
    for key, matrix in zip(('value', 'gradient', 'hessian'), matrices):
        assert np.array_equal(values[key], matrix @ np.asarray(residual.coefficients))


@pytest.mark.parametrize('degree', [0, 1, 2, 3, 8, 32, MAXIMUM_DEGREE])
@pytest.mark.parametrize('scale', [.7, 2., 5.])
def test_basis_matches_independent_chebyshev_derivative_polynomials(degree, scale):
    z = np.array([-20., -3., -.7, 0., .4, 2., 20.])
    compact = np.tanh(z / scale)
    ds = (1 - compact ** 2) / scale
    d2s = -2 * compact * (1 - compact ** 2) / scale ** 2
    tau = .625
    value, gradient, hessian = design(z, degree, tau, scale)
    # Chebyshev.deriv transforms polynomial coefficients; it does not use
    # the module's differentiated recurrence or residual evaluator.
    for k in range(degree + 1):
        polynomial = Chebyshev.basis(k)
        assert np.allclose(value[:, k], tau * polynomial(compact), rtol=2e-12, atol=2e-13)
        assert np.allclose(gradient[:, k], tau * polynomial.deriv(1)(compact) * ds, rtol=2e-11, atol=2e-11)
        expected_second = tau * (polynomial.deriv(2)(compact) * ds ** 2 + polynomial.deriv(1)(compact) * d2s)
        assert np.allclose(hessian[:, k], expected_second, rtol=3e-11, atol=3e-9)


def test_low_degree_values_have_explicit_closed_forms():
    z = np.array([-1., 0., .6])
    s = np.tanh(z / 2)
    value, _, _ = design(z, 3)
    expected = np.stack((np.ones_like(z), s, 2 * s ** 2 - 1, 4 * s ** 3 - 3 * s), axis=-1)
    assert np.allclose(value, expected, rtol=0., atol=2e-16)


def test_residual_gradient_and_hessian_match_finite_differences():
    residual = CompactFiberResidual((.3, -.15, .025, .06, -.01, .006, -.003), .75, 1.7)
    z = np.linspace(-2., 2., 17)
    step = 2e-5
    middle = residual.evaluate(z)
    plus, minus = residual.evaluate(z + step), residual.evaluate(z - step)
    numerical_gradient = (plus['value'] - minus['value']) / (2 * step)
    numerical_hessian = (plus['value'] - 2 * middle['value'] + minus['value']) / step ** 2
    assert np.allclose(middle['gradient'], numerical_gradient, rtol=3e-8, atol=1e-9)
    assert np.allclose(middle['hessian'], numerical_hessian, rtol=2e-4, atol=8e-7)


def test_residual_linearity_and_terminal_gate_scale_all_three_quantities():
    a, b = (.2, -.1, .03), (-.4, .25, .7)
    z = np.array([-2., -.5, 0., 1.])
    left, right = CompactFiberResidual(a, 1.), CompactFiberResidual(b, 1.)
    combined = CompactFiberResidual(tuple(x + y for x, y in zip(a, b)), 1.)
    scaled = CompactFiberResidual(combined.coefficients, .375)
    for key in ('value', 'gradient', 'hessian'):
        assert np.allclose(combined.evaluate(z)[key], left.evaluate(z)[key] + right.evaluate(z)[key], atol=2e-16)
        assert np.allclose(scaled.evaluate(z)[key], .375 * combined.evaluate(z)[key], atol=2e-16)


def test_atomic_degree_zero_residual_is_coordinate_independent():
    residual = CompactFiberResidual((-.6,), .4)
    result = residual.evaluate(np.array([-1e300, -3., 0., 2., 1e300]))
    assert np.array_equal(result['value'], np.full(5, -.24))
    assert np.array_equal(result['gradient'], np.zeros(5))
    assert np.array_equal(result['hessian'], np.zeros(5))
    assert residual.real_arithmetic_bound == .24


def test_terminal_is_exact_zero_even_with_extreme_finite_coefficients_and_coordinates():
    residual = CompactFiberResidual((1e308, -1e308, 1e308), 0., 1e-320)
    assert residual.real_arithmetic_bound == 0.
    for array in residual.evaluate(np.array([-1e308, 0., 1e308])).values():
        assert np.array_equal(array, np.zeros(3))
        assert not np.signbit(array).any()
    for array in design(np.array([-1e308, 0., 1e308]), MAXIMUM_DEGREE, 0., 1e-320):
        assert np.array_equal(array, np.zeros((3, MAXIMUM_DEGREE + 1)))


def test_declared_real_arithmetic_bound_and_sampled_values():
    coefficients = tuple((-1) ** k / (k + 1) for k in range(25))
    residual = CompactFiberResidual(coefficients, .375)
    assert residual.real_arithmetic_bound == pytest.approx(.375 * sum(abs(c) for c in coefficients), rel=2e-15)
    # This sample-grid check is not a replacement for the mathematical
    # |T_k|<=1 argument or an outward-rounded floating-point certificate.
    values = residual.evaluate(np.linspace(-100., 100., 2001))['value']
    assert np.max(np.abs(values)) <= residual.real_arithmetic_bound * (1 + 3e-15)
    assert 'NOT an FP-safe' in type(residual).real_arithmetic_bound.__doc__


def test_saturated_compactification_has_finite_limits_and_zero_computed_derivatives():
    coefficients = (.3, -.4, .2, .1)
    residual = CompactFiberResidual(coefficients, .7, 2.)
    result = residual.evaluate(np.array([-1e308, 1e308]))
    expected = [.7 * sum(c * (-1) ** k for k, c in enumerate(coefficients)), .7 * sum(coefficients)]
    assert np.allclose(result['value'], expected, rtol=0., atol=2e-16)
    assert np.array_equal(result['gradient'], np.zeros(2))
    assert np.array_equal(result['hessian'], np.zeros(2))
    # Division z/scale overflows, but its tanh is safely saturated.  This is
    # finite-precision behavior and not exact mathematical zero derivatives.
    extreme = CompactFiberResidual(coefficients, .7, 1e-308).evaluate(np.array([-1e308, 1e308]))
    for key in result:
        assert np.array_equal(extreme[key], result[key])


def test_coefficients_and_settings_are_immutable_and_output_arrays_do_not_alias():
    residual = CompactFiberResidual((.2, -.4), .7)
    with pytest.raises(FrozenInstanceError):
        residual.remaining_time = .2
    with pytest.raises(FrozenInstanceError):
        residual.coefficients = (3.,)
    assert type(residual.coefficients) is tuple
    output = residual.evaluate(np.array([.3]))
    original = float(output['value'][0])
    output['value'][0] = 100.
    assert float(residual.evaluate(np.array([.3]))['value'][0]) == original
    assert hash(residual) == hash(CompactFiberResidual((.2, -.4), .7))


def test_design_can_recover_predeclared_finite_coefficients_without_module_fitting():
    coefficients = np.array([.3, -.2, .1, .04, -.07, .02, .01])
    values, _, _ = design(np.linspace(-5., 5., 81), 6, .6)
    # Only a small deterministic test of the design matrix, not a model fit
    # or a scientific experiment.  The module exposes no fitting operation.
    recovered, _, rank, _ = np.linalg.lstsq(values, values @ coefficients, rcond=None)
    assert rank == 7
    roundoff_scale = 32 * np.finfo(np.float64).eps * np.linalg.cond(values) * np.linalg.norm(coefficients)
    assert np.allclose(recovered, coefficients, rtol=0., atol=roundoff_scale)


@pytest.mark.parametrize('coefficients', [[], (), (1.,) * 130, (math.inf,), (math.nan,), (True,), ('1',), (1 + 0j,)])
def test_invalid_coefficient_declarations_are_refused(coefficients):
    with pytest.raises(ValueError):
        CompactFiberResidual(coefficients, 1.)


@pytest.mark.parametrize('remaining_time', [-1., True, math.inf, math.nan, '1'])
def test_invalid_remaining_time_is_refused(remaining_time):
    with pytest.raises(ValueError):
        CompactFiberResidual((1.,), remaining_time)
    with pytest.raises(ValueError):
        design(np.array([0.]), 1, remaining_time)


@pytest.mark.parametrize('scale', [0., -2., True, math.inf, math.nan, '2'])
def test_invalid_coordinate_scale_is_refused(scale):
    with pytest.raises(ValueError):
        CompactFiberResidual((1.,), 1., scale)
    with pytest.raises(ValueError):
        design(np.array([0.]), 1, coordinate_scale=scale)


@pytest.mark.parametrize('degree', [-1, MAXIMUM_DEGREE + 1, True, 2., np.int64(2)])
def test_invalid_degree_is_refused_without_truncation(degree):
    with pytest.raises(ValueError):
        design([0.], degree)


@pytest.mark.parametrize('z', [math.inf, math.nan, [0., math.inf], [True], [1j], ['1'],
                             np.array([1.], dtype=object), np.ma.array([1.], mask=[True])])
def test_invalid_coordinates_are_refused_even_at_terminal(z):
    for remaining in (0., 1.):
        with pytest.raises(ValueError):
            design(z, 2, remaining)
        with pytest.raises(ValueError):
            CompactFiberResidual((1., .2), remaining).evaluate(z)


def test_unrepresentable_bound_or_derivatives_fail_explicitly():
    with pytest.raises(ArithmeticError, match='bound'):
        CompactFiberResidual((1e308, 1e308), 2.)
    with pytest.raises(ArithmeticError, match='derivatives'):
        design([0.], 2, coordinate_scale=1e-308)
    # Multiplication by tau before summing avoids an unnecessary overflow
    # when the declared scaled bound itself is representable.
    assert CompactFiberResidual((1e308, 1e308), 1e-308).real_arithmetic_bound == pytest.approx(2.)


def test_module_has_no_sampler_training_or_optional_framework_dependency():
    module = inspect.getmodule(CompactFiberResidual)
    tree = ast.parse(inspect.getsource(module))
    names = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    names.extend(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert not any(name and any(token in name for token in ('torch', 'sampler', 'training', 'guide')) for name in names)
    assert not hasattr(module, 'fit')
