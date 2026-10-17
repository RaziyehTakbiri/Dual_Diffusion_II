"""Manufactured checks of exact FD7 weights and floating-point evaluation."""
from fractions import Fraction
import math

import numpy as np
from numpy.polynomial import Polynomial
import pytest

from heterodiff.models.localized_score_curvature import estimate_hessians_from_scores_fd7, fd7_weights


@pytest.mark.parametrize('position', range(7))
def test_exact_fraction_weights_differentiate_all_degree_six_monomials(position):
    weights = fd7_weights(position)
    assert type(weights) is tuple and all(type(w) is Fraction for w in weights)
    for degree in range(7):
        actual = sum((w*j**degree for j, w in enumerate(weights)), Fraction(0))
        expected = 0 if degree == 0 else degree*position**(degree-1)
        assert actual == expected


def test_centered_stencil_and_boundary_mirror_identities_are_exact():
    assert fd7_weights(3) == tuple(Fraction(w, 60) for w in (-1, 9, -45, 0, 45, -9, 1))
    assert fd7_weights(0) == tuple(Fraction(w, 60) for w in (-147, 360, -450, 400, -225, 72, -10))
    for position in range(7):
        assert fd7_weights(6-position) == tuple(-w for w in reversed(fd7_weights(position)))


@pytest.mark.parametrize('degree', range(7))
@pytest.mark.parametrize('count', [7, 17, 257])
def test_seven_point_rules_differentiate_degree_six_scores_at_all_boundary_nodes(degree, count):
    knots = np.linspace(-2., 2., count)
    score = Polynomial(tuple((-1)**k/(k+1) for k in range(degree+1)))
    result = estimate_hessians_from_scores_fd7(tuple(knots), tuple(score(knots)))
    assert type(result) is tuple
    assert np.allclose(result, score.deriv(1)(knots), atol=5e-12, rtol=5e-12)


def test_scores_only_rule_has_sixth_order_truncation_under_smooth_exact_inputs():
    errors = []
    for cells in (12, 24, 48):
        knots = np.linspace(-1., 1., cells+1)
        result = estimate_hessians_from_scores_fd7(tuple(knots), tuple(np.sin(knots)))
        errors.append(float(np.max(np.abs(np.array(result)-np.cos(knots)))))
    assert all(40 < coarse/fine < 90 for coarse, fine in zip(errors, errors[1:]))
    assert errors[-1] < 2e-9


def test_subtracting_reference_score_preserves_constant_scores_exactly():
    knots = tuple(float(i) for i in range(13))
    result = estimate_hessians_from_scores_fd7(knots, (1e300,)*13)
    assert result == (0.,)*13


def test_large_coordinate_spacing_does_not_overflow_scaled_stencil_denominator():
    width = 2e307
    knots = tuple(i*width for i in range(7))
    result = estimate_hessians_from_scores_fd7(knots, tuple(float(i) for i in range(7)))
    assert all(value > 0 for value in result)
    assert np.allclose(np.asarray(result)/(1/width), 1., rtol=2e-14, atol=0.)


@pytest.mark.parametrize('position', [-1, 7, True, 3., np.int64(3)])
def test_invalid_stencil_position_is_refused(position):
    with pytest.raises(ValueError):
        fd7_weights(position)


@pytest.mark.parametrize('case', ['list', 'short', 'large', 'shape', 'nonuniform', 'reversed', 'bool', 'complex', 'nan', 'inf'])
def test_invalid_knot_and_score_inputs_are_refused(case):
    knots, scores = tuple(float(i) for i in range(7)), (0.,)*7
    if case == 'list': knots = list(knots)
    elif case == 'short': knots, scores = knots[:6], scores[:6]
    elif case == 'large': knots, scores = tuple(float(i) for i in range(1026)), (0.,)*1026
    elif case == 'shape': scores = scores[:6]
    elif case == 'nonuniform': knots = (0., 1., 2., 3.1, 4., 5., 6.)
    elif case == 'reversed': knots = tuple(reversed(knots))
    elif case == 'bool': scores = (True,)+scores[1:]
    elif case == 'complex': scores = (1j,)+scores[1:]
    elif case == 'nan': scores = (math.nan,)+scores[1:]
    else: knots = (math.inf,)+knots[1:]
    with pytest.raises(ValueError):
        estimate_hessians_from_scores_fd7(knots, scores)


def test_unrepresentable_curvature_fails_without_silent_clipping():
    with pytest.raises(ArithmeticError):
        estimate_hessians_from_scores_fd7(tuple(i*1e-308 for i in range(7)), tuple((-1)**i*1e308 for i in range(7)))
