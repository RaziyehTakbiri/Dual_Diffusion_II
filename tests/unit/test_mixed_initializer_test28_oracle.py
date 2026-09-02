"""Independent tests for the CP50 known-law mixed-initializer oracle."""

from fractions import Fraction
import math

import pytest

from heterodiff.evaluation import mixed_initializer_test28_oracle as oracle


def test_atomic_a0_exact_target_and_factorials_are_frozen():
    fixture = oracle.atomic_a0_fixture()

    assert fixture.fixture_id == "T28-A0-H"
    assert fixture.base_probabilities == (
        Fraction(2, 5),
        Fraction(4, 25),
        Fraction(6, 25),
        Fraction(4, 125),
        Fraction(12, 125),
        Fraction(9, 125),
    )
    assert sum(fixture.base_probabilities, Fraction()) == 1
    assert fixture.normalizer == Fraction(549, 500)
    assert fixture.target_probabilities == tuple(
        Fraction(value, 549) for value in (200, 160, 60, 48, 72, 9)
    )
    assert sum(fixture.target_probabilities, Fraction()) == 1
    assert fixture.rejection_acceptance_probability == Fraction(183, 500)


def test_m1_quadratic_target_has_analytic_categories_and_gaussian_fiber():
    fixture = oracle.mixed_m1_fixture()
    integrated = math.sqrt(2.0 / 3.0)
    normalizer = math.fsum((0.5, 0.2, 0.3 * integrated))

    assert fixture.fixture_id == "T28-M1-Q"
    assert fixture.continuous_integrated_weight.hex() == integrated.hex()
    assert fixture.target_normalizer.hex() == normalizer.hex()
    assert fixture.continuous_target_variance == Fraction(2, 3)
    assert fixture.rejection_acceptance_probability.hex() == normalizer.hex()
    assert math.isclose(
        oracle.m1_continuous_target_density(0.0),
        1.0 / math.sqrt(2.0 * math.pi * (2.0 / 3.0)),
        rel_tol=0.0,
        abs_tol=2.0e-16,
    )
    assert oracle.m1_continuous_target_cdf(0.0) == 0.5


def test_m2_quadratic_target_categories_and_moments_are_self_consistent():
    fixture = oracle.mixed_m2_fixture()
    moments = oracle.m2_count_type_moments()
    p0, p1, p2 = fixture.target_count_probabilities
    del p0

    assert fixture.fixture_id == "T28-M2-Q"
    assert math.fsum(
        fixture.target_configuration_category_probabilities
    ) == pytest.approx(1.0, abs=2.0e-16)
    assert math.fsum(fixture.target_count_probabilities) == pytest.approx(
        1.0, abs=2.0e-16
    )
    assert moments.count_mean.hex() == (p1 + 2.0 * p2).hex()
    assert moments.count_second_moment.hex() == (p1 + 4.0 * p2).hex()
    assert math.fsum(moments.expected_type_counts).hex() == moments.count_mean.hex()
    assert fixture.type_coordinate_variances == (
        (Fraction(2, 3),),
        (Fraction(4, 5), Fraction(3, 4)),
    )


@pytest.mark.parametrize(
    "category,coordinates,expected",
    [
        ("empty", (), Fraction(0)),
        ("atomic-a", (), Fraction(0)),
        ("continuous-b", (1.25,), Fraction(-25, 64)),
    ],
)
def test_m1_score_keeps_exact_rational_and_binary64_formula_layers_separate(
    category, coordinates, expected
):
    result = oracle.m1_exact_rational_score(category, coordinates)

    assert result.exact_rational_score == expected
    assert result.exact_rational_score_as_binary64.hex() == float(expected).hex()


def test_m2_score_uses_canonical_types_dimensions_and_count_penalty():
    result = oracle.m2_exact_rational_score(
        (0, 1),
        ((1.0,), (2.0, -0.5)),
    )

    assert result.count_penalty == Fraction(-1, 4)
    assert result.exact_rational_score == Fraction(-25, 24)
    assert (
        result.exact_rational_score_as_binary64.hex() == float(Fraction(-25, 24)).hex()
    )

    with pytest.raises(ValueError, match="canonical"):
        oracle.m2_exact_rational_score((1, 0), ((0.0, 0.0), (0.0,)))
    with pytest.raises(ValueError, match="coordinate"):
        oracle.m2_exact_rational_score((1,), ((0.0,),))


@pytest.mark.parametrize("query", (-3.0, -0.5, 0.0, 0.75, 4.0))
def test_analytic_gaussian_cdfs_agree_with_independent_quadrature(query):
    comparisons = (
        (
            oracle.m1_continuous_target_cdf(query),
            oracle.m1_continuous_target_cdf_quadrature(query),
        ),
        (
            oracle.m2_type1_target_cdf(query),
            oracle.m2_type1_target_cdf_quadrature(query),
        ),
        (
            oracle.m2_type2_coordinate_target_cdf(query, coordinate_index=0),
            oracle.m2_type2_coordinate_target_cdf_quadrature(query, coordinate_index=0),
        ),
        (
            oracle.m2_type2_coordinate_target_cdf(query, coordinate_index=1),
            oracle.m2_type2_coordinate_target_cdf_quadrature(query, coordinate_index=1),
        ),
    )
    for analytic, numerical in comparisons:
        assert numerical.analytic_reference_value.hex() == analytic.hex()
        assert numerical.absolute_discrepancy <= (
            8.0 * numerical.absolute_error_estimate + 2.0e-15
        )


def test_gaussian_cdf_endpoints_and_projection_moments_are_exactly_scoped():
    assert oracle.m1_continuous_target_cdf(-math.inf) == 0.0
    assert oracle.m1_continuous_target_cdf(math.inf) == 1.0
    first = oracle.m2_type2_projection_moment((1.0, 0.0))
    diagonal = oracle.m2_type2_projection_moment(
        (1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0))
    )

    assert first.variance == pytest.approx(4.0 / 5.0)
    assert diagonal.variance == pytest.approx(31.0 / 40.0)
    with pytest.raises(ValueError, match="nonzero"):
        oracle.m2_type2_projection_moment((0.0, 0.0))


def test_finite_categorical_tv_bound_matches_the_frozen_union_bound():
    result = oracle.finite_categorical_tv_bound((0.5, 0.5), (60, 40), alpha=0.01)
    radius = math.sqrt(math.log(4.0 / 0.01) / 200.0)

    assert result.empirical_probabilities == (0.6, 0.4)
    assert result.empirical_total_variation == pytest.approx(0.1)
    assert result.simultaneous_linf_radius.hex() == radius.hex()
    assert result.total_variation_upper_bound == pytest.approx(0.1 + radius)

    with pytest.raises(TypeError, match="all Fractions or all floats"):
        oracle.finite_categorical_tv_bound((Fraction(1, 2), 0.5), (1, 1))


def test_ks_dkw_bound_uses_both_empirical_jump_sides():
    result = oracle.ks_dkw_bound((-1.0, 0.0, 1.0), oracle.m1_continuous_target_cdf)

    cdf_values = tuple(
        oracle.m1_continuous_target_cdf(value) for value in (-1.0, 0.0, 1.0)
    )
    expected = max(
        max(cdf - (index - 1) / 3.0, index / 3.0 - cdf)
        for index, cdf in enumerate(cdf_values, start=1)
    )
    assert result.empirical_ks.hex() == expected.hex()
    assert result.cdf_distance_upper_bound >= result.empirical_ks


@pytest.mark.parametrize(
    "successes,trials,expected_boundary",
    [(0, 20, 0.0), (20, 20, 1.0), (7, 20, None)],
)
def test_clopper_pearson_interval_handles_boundaries(
    successes, trials, expected_boundary
):
    interval = oracle.clopper_pearson_interval(successes, trials, alpha=0.01)

    assert interval.lower <= interval.estimate <= interval.upper
    if expected_boundary == 0.0:
        assert interval.lower == 0.0
    elif expected_boundary == 1.0:
        assert interval.upper == 1.0


def test_rejection_exhaustion_is_an_outcome_not_an_exclusion():
    assert oracle.rejection_exhaustion_probability(0.0, 7) == 1.0
    assert oracle.rejection_exhaustion_probability(1.0, 7) == 0.0
    expected = oracle.rejection_exhaustion_probability(0.5, 4)
    assert expected.hex() == (1.0 / 16.0).hex()

    check = oracle.rejection_exhaustion_binomial_check(
        attempt_cap=4,
        request_count=100,
        exhaustion_count=6,
        acceptance_probability=0.5,
        alpha=0.01,
    )
    assert check.expected_exhaustion_probability.hex() == expected.hex()
    assert check.expected_probability_inside_interval is True

    with pytest.raises(ArithmeticError, match="underflowed to zero"):
        oracle.rejection_exhaustion_probability(0.5, 4096)


def test_ess_summary_is_scale_invariant_and_refuses_underflowed_support():
    first = oracle.ess_summary((1.0, 2.0, 3.0))
    scaled = oracle.ess_summary((10.0, 20.0, 30.0))

    assert first.effective_sample_size.hex() == scaled.effective_sample_size.hex()
    assert first.maximum_normalized_weight == pytest.approx(0.5)
    assert 1.0 <= first.effective_sample_size <= 3.0

    with pytest.raises(ValueError, match="strictly positive"):
        oracle.ess_summary((1.0, 0.0))
    with pytest.raises(ArithmeticError, match="underflow"):
        oracle.ess_summary((1.0e308, math.nextafter(0.0, 1.0)))
    with pytest.raises(ArithmeticError, match="normalized SIR probability"):
        oracle.ess_summary((1.0, 1.0, 1.0, math.nextafter(0.0, 1.0)))


def test_oracle_scope_refuses_continuous_tv_and_test28_closure():
    scope = oracle.CP50_TEST28_ORACLE_SCOPE

    assert "not-continuous-tv-or-kl" in scope
    assert "not-test28-closure" in scope
    assert "not-production-initializer" in scope
