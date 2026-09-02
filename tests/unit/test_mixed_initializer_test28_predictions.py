"""Independent and hostile tests for the CP53 analytic prediction oracle."""

from __future__ import annotations

import ast
import inspect
import json
import os
import pickle
import subprocess
import sys
from dataclasses import fields, is_dataclass, replace
from fractions import Fraction
from itertools import product
from math import factorial
from pathlib import Path

import pytest

from heterodiff.evaluation import mixed_initializer_test28_predictions as predictions


_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_INDEPENDENT_BITS = 384
_INDEPENDENT_DENOMINATOR = 1 << _INDEPENDENT_BITS
_INDEPENDENT_WIDTH = Fraction(1, _INDEPENDENT_DENOMINATOR)


def _point(value: Fraction) -> tuple[Fraction, Fraction]:
    return value, value


def _add(
    left: tuple[Fraction, Fraction],
    right: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction]:
    return left[0] + right[0], left[1] + right[1]


def _sum(
    values: tuple[tuple[Fraction, Fraction], ...],
) -> tuple[Fraction, Fraction]:
    result = _point(_ZERO)
    for value in values:
        result = _add(result, value)
    return result


def _multiply(
    left: tuple[Fraction, Fraction],
    right: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction]:
    assert left[0] >= 0 and right[0] >= 0
    return left[0] * right[0], left[1] * right[1]


def _divide(
    numerator: tuple[Fraction, Fraction],
    denominator: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction]:
    assert numerator[0] >= 0 and denominator[0] > 0
    return numerator[0] / denominator[1], numerator[1] / denominator[0]


def _subtract(
    left: tuple[Fraction, Fraction],
    right: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction]:
    return left[0] - right[1], left[1] - right[0]


def _sqrt_bracket(value: Fraction) -> tuple[Fraction, Fraction]:
    """Independent integer-inequality bracket at a different precision."""

    assert value >= 0
    scaled = (value.numerator << (2 * _INDEPENDENT_BITS)) // value.denominator
    low_integer = __import__("math").isqrt(scaled)
    lower = Fraction(low_integer, _INDEPENDENT_DENOMINATOR)
    if low_integer * low_integer * value.denominator == (
        value.numerator << (2 * _INDEPENDENT_BITS)
    ):
        return lower, lower
    return lower, Fraction(low_integer + 1, _INDEPENDENT_DENOMINATOR)


def _sqrt_interval(
    value: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction]:
    return _sqrt_bracket(value[0])[0], _sqrt_bracket(value[1])[1]


def _exp_negative_bracket(value: Fraction) -> tuple[Fraction, Fraction]:
    """Independent alternating-series enclosure for exp(-value)."""

    assert 0 < value <= 1
    term = _ONE
    partial = _ONE
    lower = _ZERO
    upper = _ONE
    for index in range(1, 4097):
        term = term * value / index
        if index % 2:
            partial -= term
            lower = partial
        else:
            partial += term
            upper = partial
        if upper - lower <= _INDEPENDENT_WIDTH:
            return lower, upper
    raise AssertionError("independent exponential series did not terminate")


def _normalizer_variance_and_sir(
    normalizer: tuple[Fraction, Fraction],
    second_moment: tuple[Fraction, Fraction],
) -> tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]:
    raw_variance = _subtract(second_moment, _multiply(normalizer, normalizer))
    variance = max(_ZERO, raw_variance[0]), raw_variance[1]
    coefficient = _divide(
        _sqrt_interval(variance),
        _multiply(_point(Fraction(2, 1)), normalizer),
    )
    return variance, coefficient


def _independent_prediction(
    fixture_id: str,
    weights: tuple[Fraction, Fraction],
) -> dict[str, object]:
    w0, w1 = (_point(value) for value in weights)
    mu0 = _sqrt_bracket(Fraction(2, 3))
    if fixture_id == "T28-M1-Q":
        p0 = p1 = _point(Fraction(1, 2))
        category_masses = (
            p0,
            _multiply(p1, w0),
            _multiply(_multiply(p1, w1), mu0),
        )
        normalizer = _sum(category_masses)
        second_moment = _sum(
            (
                p0,
                _multiply(p1, w0),
                _multiply(
                    _multiply(p1, w1),
                    _sqrt_bracket(Fraction(1, 2)),
                ),
            )
        )
        variance, coefficient = _normalizer_variance_and_sir(normalizer, second_moment)
        return {
            "normalizer": normalizer,
            "second_moment": second_moment,
            "variance": variance,
            "sir_coefficient": coefficient,
            "configuration-category": (
                category_masses,
                tuple(_divide(mass, normalizer) for mass in category_masses),
                normalizer,
            ),
        }

    p0 = _point(Fraction(2, 5))
    p1 = _point(Fraction(2, 5))
    p2 = _point(Fraction(1, 5))
    mu1 = _sqrt_bracket(Fraction(3, 5))
    penalty = _exp_negative_bracket(Fraction(1, 4))
    tilted0 = _multiply(w0, mu0)
    tilted1 = _multiply(w1, mu1)
    mean = _add(tilted0, tilted1)
    category_masses = (
        p0,
        _multiply(p1, tilted0),
        _multiply(p1, tilted1),
        _multiply(_multiply(_multiply(p2, penalty), tilted0), tilted0),
        _multiply(
            _multiply(
                _multiply(_multiply(p2, penalty), _point(Fraction(2, 1))),
                tilted0,
            ),
            tilted1,
        ),
        _multiply(_multiply(_multiply(p2, penalty), tilted1), tilted1),
    )
    normalizer = _sum(category_masses)
    count_masses = (
        p0,
        _multiply(p1, mean),
        _multiply(_multiply(_multiply(p2, penalty), mean), mean),
    )
    second_mean = _add(
        _multiply(w0, _sqrt_bracket(Fraction(1, 2))),
        _multiply(w1, _sqrt_bracket(Fraction(2, 5))),
    )
    second_moment = _sum(
        (
            p0,
            _multiply(p1, second_mean),
            _multiply(
                _multiply(
                    _multiply(
                        p2,
                        _exp_negative_bracket(Fraction(1, 2)),
                    ),
                    second_mean,
                ),
                second_mean,
            ),
        )
    )
    variance, coefficient = _normalizer_variance_and_sir(normalizer, second_moment)
    return {
        "normalizer": normalizer,
        "second_moment": second_moment,
        "variance": variance,
        "sir_coefficient": coefficient,
        "configuration-category": (
            category_masses,
            tuple(_divide(mass, normalizer) for mass in category_masses),
            normalizer,
        ),
        "count": (
            count_masses,
            tuple(_divide(mass, normalizer) for mass in count_masses),
            normalizer,
        ),
        "event-type": (
            (tilted0, tilted1),
            (_divide(tilted0, mean), _divide(tilted1, mean)),
            mean,
        ),
    }


def _assert_contains(
    actual: predictions.ClosedRationalInterval,
    independent: tuple[Fraction, Fraction],
) -> None:
    assert actual.lower <= independent[0] <= independent[1] <= actual.upper


def _tables(
    layer: predictions.AnalyticReferencePrediction,
) -> tuple[predictions.ProbabilityTablePrediction, ...]:
    result = [layer.category_table]
    if layer.count_table is not None:
        result.append(layer.count_table)
    if layer.event_type_table is not None:
        result.append(layer.event_type_table)
    return tuple(result)


@pytest.mark.parametrize(
    "builder,fixture_id",
    [
        (predictions.t28_m1_analytic_predictions, "T28-M1-Q"),
        (predictions.t28_m2_analytic_predictions, "T28-M2-Q"),
    ],
)
def test_exact_rational_predictions_enclose_independent_384_bit_derivations(
    builder: object,
    fixture_id: str,
) -> None:
    pair = builder()
    predictions.validate_t28_analytic_predictions(pair)
    assert pair.fixture_id == fixture_id
    assert "exact-rational-interval" in pair.rational_interval_method
    assert "no Decimal or libm" in pair.rational_proof_statement
    layers = (
        (
            pair.ideal_rational,
            (Fraction(2, 5), Fraction(3, 5)),
        ),
        (
            pair.binary64_parameter,
            (Fraction.from_float(0.4), Fraction.from_float(0.6)),
        ),
    )
    for layer, weights in layers:
        independent = _independent_prediction(fixture_id, weights)
        _assert_contains(layer.normalizer, independent["normalizer"])
        _assert_contains(layer.second_weight_moment, independent["second_moment"])
        _assert_contains(layer.weight_variance, independent["variance"])
        _assert_contains(
            layer.exact_iid_sir_tv_coefficient,
            independent["sir_coefficient"],
        )
        assert layer.normalizer == layer.ideal_rejection_acceptance_probability
        for table in _tables(layer):
            expected_masses, expected_probabilities, expected_normalizer = independent[
                table.table_id
            ]
            _assert_contains(table.normalizer, expected_normalizer)
            for actual, expected in zip(table.unnormalized_masses, expected_masses):
                _assert_contains(actual, expected)
            for actual, expected in zip(table.probabilities, expected_probabilities):
                _assert_contains(actual, expected)


def _walk_records(value: object) -> tuple[object, ...]:
    result = [value]
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            result.extend(_walk_records(getattr(value, field.name)))
    elif type(value) is tuple:
        for item in value:
            result.extend(_walk_records(item))
    return tuple(result)


def test_all_authoritative_analytic_intervals_are_tighter_than_2_to_minus_192() -> None:
    ceiling = Fraction(1, 1 << 192)
    for pair in (
        predictions.t28_m1_analytic_predictions(),
        predictions.t28_m2_analytic_predictions(),
    ):
        intervals = tuple(
            value
            for value in _walk_records(pair)
            if type(value) is predictions.ClosedRationalInterval
        )
        assert intervals
        assert all(value.upper - value.lower < ceiling for value in intervals)
        assert all(
            value.enclosure_bits == predictions.CP53_TEST28_RATIONAL_ENCLOSURE_BITS
            for value in intervals
        )


def _enumerate_capped_reference_pmf(
    cap: int,
    type_weights: tuple[Fraction, Fraction],
) -> dict[tuple[int, int], Fraction]:
    count_terms = tuple(Fraction(1, factorial(count)) for count in range(cap + 1))
    count_normalizer = sum(count_terms, _ZERO)
    result: dict[tuple[int, int], Fraction] = {}
    for count, count_term in enumerate(count_terms):
        count_probability = count_term / count_normalizer
        for ordered_types in product((0, 1), repeat=count):
            type_probability = _ONE
            for event_type in ordered_types:
                type_probability *= type_weights[event_type]
            key = (ordered_types.count(0), ordered_types.count(1))
            result[key] = result.get(key, _ZERO) + (
                count_probability * type_probability
            )
    assert sum(result.values(), _ZERO) == _ONE
    return result


def _finite_half_l1(
    left: dict[tuple[int, int], Fraction],
    right: dict[tuple[int, int], Fraction],
) -> Fraction:
    support = set(left) | set(right)
    return (
        sum(
            (abs(left.get(key, _ZERO) - right.get(key, _ZERO)) for key in support),
            _ZERO,
        )
        / 2
    )


def test_m1_and_m2_exact_reference_parameter_perturbations_and_proposal_tv() -> None:
    epsilon = Fraction(1, 5 * (1 << 53))
    m1 = predictions.t28_m1_parameter_perturbation()
    m2 = predictions.t28_m2_parameter_perturbation()
    for value in (m1, m2):
        predictions.validate_t28_parameter_perturbation(value)
        assert value.binary64_minus_ideal_activity == 0
        assert value.binary64_minus_ideal_type_weights == (epsilon, -epsilon)
        assert value.exact_type_weight_l1_distance == 2 * epsilon
        assert value.exact_type_weight_total_variation_distance == epsilon
        assert value.exact_reference_parameter_epsilon == epsilon
        assert value.normalizer_difference.signed_difference.lower > 0
        assert value.normalizer_relative_absolute_difference.lower > 0
        assert (
            value.analytic_target_law_total_variation_distance
            == value.table_perturbations[0].total_variation_distance
        )
        assert value.analytic_target_tv_equals_configuration_category_tv is True
        assert "conditional selected-fiber laws are identical" in (
            value.analytic_target_tv_identity_statement
        )
        assert value.analytic_references_only is True
        assert value.operational_sampler_perturbation_bounded is False
    ideal_weights = (Fraction(2, 5), Fraction(3, 5))
    binary64_weights = (Fraction.from_float(0.4), Fraction.from_float(0.6))
    m1_enumerated_tv = _finite_half_l1(
        _enumerate_capped_reference_pmf(1, ideal_weights),
        _enumerate_capped_reference_pmf(1, binary64_weights),
    )
    m2_enumerated_tv = _finite_half_l1(
        _enumerate_capped_reference_pmf(2, ideal_weights),
        _enumerate_capped_reference_pmf(2, binary64_weights),
    )
    assert m1.exact_proposal_measure_total_variation_distance == m1_enumerated_tv
    assert m1.proposal_tv_formula_id == "m1-proposal-tv-epsilon-over-2-v1"
    assert m2.exact_proposal_measure_total_variation_distance == m2_enumerated_tv
    assert "16-epsilon-over-25" in m2.proposal_tv_formula_id


def test_target_table_perturbations_enclose_independent_probability_deltas() -> None:
    for pair, report in (
        (
            predictions.t28_m1_analytic_predictions(),
            predictions.t28_m1_parameter_perturbation(),
        ),
        (
            predictions.t28_m2_analytic_predictions(),
            predictions.t28_m2_parameter_perturbation(),
        ),
    ):
        ideal = _independent_prediction(
            pair.fixture_id, (Fraction(2, 5), Fraction(3, 5))
        )
        binary64 = _independent_prediction(
            pair.fixture_id,
            (Fraction.from_float(0.4), Fraction.from_float(0.6)),
        )
        for table_report in report.table_perturbations:
            ideal_probabilities = ideal[table_report.table_id][1]
            binary_probabilities = binary64[table_report.table_id][1]
            independent_differences = tuple(
                _subtract(right, left)
                for left, right in zip(ideal_probabilities, binary_probabilities)
            )
            for actual, expected in zip(
                table_report.probability_differences,
                independent_differences,
            ):
                _assert_contains(actual.signed_difference, expected)
            independent_tv = _multiply(
                _point(Fraction(1, 2)),
                _sum(
                    tuple(
                        (
                            _ZERO
                            if lower <= 0 <= upper
                            else min(abs(lower), abs(upper)),
                            max(abs(lower), abs(upper)),
                        )
                        for lower, upper in independent_differences
                    )
                ),
            )
            _assert_contains(table_report.total_variation_distance, independent_tv)


@pytest.mark.parametrize("attempts", [1, 4, 16, 64])
def test_conditional_uint64_bounds_preserve_strict_endpoint_semantics(
    attempts: int,
) -> None:
    epsilon = Fraction(1, 1 << 64)
    for pair in (
        predictions.t28_m1_analytic_predictions(),
        predictions.t28_m2_analytic_predictions(),
    ):
        for layer in (pair.ideal_rational, pair.binary64_parameter):
            result = predictions.conditional_uint64_rejection_bounds(layer, attempts)
            predictions.validate_conditional_uint64_rejection_bounds(result)
            assert result.alpha64_bound.lower == layer.normalizer.lower - epsilon
            assert result.alpha64_bound.upper == layer.normalizer.upper
            assert result.alpha64_bound.lower_inclusive is False
            assert result.alpha64_bound.upper_inclusive is True
            exact_lower = (1 - layer.normalizer.upper) ** attempts
            exact_strict_upper = (1 - (layer.normalizer.lower - epsilon)) ** attempts
            assert result.exhaustion_probability_bound.lower <= exact_lower
            assert result.exhaustion_probability_bound.upper >= exact_strict_upper
            assert result.exhaustion_probability_bound.lower_inclusive is True
            assert result.exhaustion_probability_bound.upper_inclusive is False
            assert result.selected_total_variation_bound.lower == 0
            assert result.selected_total_variation_bound.upper == epsilon / (
                layer.normalizer.lower
            )
            assert result.selected_total_variation_bound.upper_inclusive is False
            assert result.conditional_theorem_derived is True
            assert result.alpha64_positive_precondition_met is True
            assert result.iid_proposals_verified is False
            assert result.independent_uniform_uint64_words_verified is False
            assert result.operational_mu_fp_identified is False
            assert result.numerical_mu_fp_prediction is False
            assert result.operational_predictions_satisfied is False


def test_conditional_uint64_attempt_budget_is_bounded_and_preflighted() -> None:
    layer = predictions.t28_m1_analytic_predictions().ideal_rational
    maximum = predictions.MAX_CP53_TEST28_REJECTION_ATTEMPTS
    result = predictions.conditional_uint64_rejection_bounds(layer, maximum)
    assert result.attempts == maximum
    assert (
        result.exhaustion_probability_bound.lower.denominator.bit_length()
        <= predictions.MAX_CP53_TEST28_EXACT_INTEGER_BITS
    )
    for invalid in (True, 1.0, Fraction(1, 1), "1"):
        with pytest.raises(TypeError, match="exact non-boolean integer"):
            predictions.conditional_uint64_rejection_bounds(layer, invalid)
    for invalid in (0, maximum + 1):
        with pytest.raises(ValueError, match="resource bound"):
            predictions.conditional_uint64_rejection_bounds(layer, invalid)


@pytest.mark.parametrize("particles", [8, 32, 128, 512])
def test_conditional_exact_iid_sir_bounds_are_bounds_not_distributions(
    particles: int,
) -> None:
    for pair in (
        predictions.t28_m1_analytic_predictions(),
        predictions.t28_m2_analytic_predictions(),
    ):
        for layer in (pair.ideal_rational, pair.binary64_parameter):
            result = predictions.conditional_exact_iid_sir_bounds(layer, particles)
            predictions.validate_conditional_exact_iid_sir_bounds(result)
            assert result.particles == particles
            assert result.sir_tv_coefficient == layer.exact_iid_sir_tv_coefficient
            assert result.marginal_total_variation_bound.lower == 0
            assert result.marginal_total_variation_bound.lower_inclusive is True
            assert result.marginal_total_variation_bound.upper_inclusive is True
            independent_sqrt_lower = _sqrt_bracket(Fraction(particles, 1))[0]
            assert (
                result.marginal_total_variation_bound.upper * independent_sqrt_lower
                >= layer.exact_iid_sir_tv_coefficient.upper
            )
            assert result.conditional_theorem_derived is True
            assert result.iid_analytic_proposals_verified is False
            assert result.operational_exact_weights_verified is False
            assert result.exact_categorical_resampling_verified is False
            assert result.operational_mu_fp_identified is False
            assert result.exact_finite_j_distribution_derived is False
            assert result.operational_predictions_satisfied is False


def test_conditional_sir_particle_budget_is_exact_and_bounded() -> None:
    layer = predictions.t28_m1_analytic_predictions().binary64_parameter
    maximum = predictions.MAX_CP53_TEST28_SIR_PARTICLES
    edge = predictions.conditional_exact_iid_sir_bounds(layer, 1)
    assert edge.particles == 1
    result = predictions.conditional_exact_iid_sir_bounds(layer, maximum)
    assert result.particles == maximum
    for invalid in (True, 1.0, Fraction(1, 1), "1"):
        with pytest.raises(TypeError, match="exact non-boolean integer"):
            predictions.conditional_exact_iid_sir_bounds(layer, invalid)
    for invalid in (0, maximum + 1):
        with pytest.raises(ValueError, match="resource bound"):
            predictions.conditional_exact_iid_sir_bounds(layer, invalid)


def test_exact_two_point_sir_exhaustively_verifies_augmented_tv_identity() -> None:
    proposal = (Fraction(1, 3), Fraction(2, 3))
    weights = (Fraction(1, 4), Fraction(3, 4))
    normalizer = sum(
        (probability * weight for probability, weight in zip(proposal, weights)),
        _ZERO,
    )
    target = tuple(
        probability * weight / normalizer
        for probability, weight in zip(proposal, weights)
    )
    variance = sum(
        (
            probability * (weight - normalizer) * (weight - normalizer)
            for probability, weight in zip(proposal, weights)
        ),
        _ZERO,
    )
    for particles in (1, 2, 3):
        selected = [_ZERO, _ZERO]
        augmented_tv = _ZERO
        absolute_sum_identity = _ZERO
        for cloud in product((0, 1), repeat=particles):
            cloud_probability = _ONE
            cloud_weight_sum = _ZERO
            for state in cloud:
                cloud_probability *= proposal[state]
                cloud_weight_sum += weights[state]
            conditional_joint_l1 = _ZERO
            for state in cloud:
                actual_index_mass = weights[state] / cloud_weight_sum
                ideal_extended_mass = weights[state] / (particles * normalizer)
                conditional_joint_l1 += abs(actual_index_mass - ideal_extended_mass)
                selected[state] += cloud_probability * actual_index_mass
            augmented_tv += cloud_probability * conditional_joint_l1 / 2
            absolute_sum_identity += (
                cloud_probability
                * abs(cloud_weight_sum - particles * normalizer)
                / (2 * particles * normalizer)
            )
        selected_tv = (
            sum(
                (abs(actual - expected) for actual, expected in zip(selected, target)),
                _ZERO,
            )
            / 2
        )
        theorem_bound_squared = variance / (4 * normalizer * normalizer * particles)
        assert augmented_tv == absolute_sum_identity
        assert selected_tv <= augmented_tv
        assert augmented_tv * augmented_tv <= theorem_bound_squared


def test_small_word_floor_quantization_exhaustively_verifies_generic_bounds() -> None:
    proposal = (Fraction(1, 3), Fraction(2, 3))
    weights = (Fraction(2, 3), Fraction(1, 5))
    word_bits = 4
    word_count = 1 << word_bits
    epsilon = Fraction(1, word_count)
    quotas = tuple(
        (word_count * weight.numerator) // weight.denominator for weight in weights
    )
    quantized = tuple(Fraction(quota, word_count) for quota in quotas)
    for weight, approximation in zip(weights, quantized):
        assert 0 <= weight - approximation < epsilon
    normalizer = sum(
        (probability * weight for probability, weight in zip(proposal, weights)),
        _ZERO,
    )
    accepted_state_mass = []
    for state in (0, 1):
        accepted_words = sum(1 for word in range(word_count) if word < quotas[state])
        accepted_state_mass.append(
            proposal[state] * Fraction(accepted_words, word_count)
        )
    alpha = sum(accepted_state_mass, _ZERO)
    assert normalizer - epsilon < alpha <= normalizer
    exact_target = tuple(
        probability * weight / normalizer
        for probability, weight in zip(proposal, weights)
    )
    selected_quantized = tuple(mass / alpha for mass in accepted_state_mass)
    selected_tv = (
        sum(
            (
                abs(left - right)
                for left, right in zip(selected_quantized, exact_target)
            ),
            _ZERO,
        )
        / 2
    )
    assert selected_tv < epsilon / normalizer
    for attempts in (1, 4, 16):
        exhaustion = (1 - alpha) ** attempts
        assert (1 - normalizer) ** attempts <= exhaustion
        assert exhaustion < (1 - (normalizer - epsilon)) ** attempts


def test_formula_identifiers_and_nonclaims_keep_analytic_and_runtime_laws_separate() -> None:
    assert "mu_fp" in " ".join(predictions.CP53_TEST28_PREDICTION_NONCLAIMS)
    assert (
        "not a numerical mu_fp"
        in predictions.CP53_TEST28_CONDITIONAL_UINT64_BOUND_STATEMENT
    )
    assert "neither derives Q_J" in (
        predictions.CP53_TEST28_CONDITIONAL_EXACT_IID_SIR_BOUND_STATEMENT
    )
    for pair in (
        predictions.t28_m1_analytic_predictions(),
        predictions.t28_m2_analytic_predictions(),
    ):
        for layer in (pair.ideal_rational, pair.binary64_parameter):
            assert "capped-poisson-gaussian-integral" in layer.formula_id
            assert "-z=" in layer.normalizer_formula_id
            assert "-ew2=" in layer.second_weight_moment_formula_id
            assert layer.ideal_gaussian_fibers_retained is True
            assert layer.operational_sampler_law_verified is False
            assert layer.runtime_sampler_imported is False
            assert layer.source_or_rng_law_verified is False
            assert layer.represented_measure_identified is False
            assert layer.exact_iid_sir_premises_verified is False
            assert layer.confirmatory_evidence is False
            assert layer.manuscript_claim is False


def test_module_import_graph_excludes_runtime_oracle_and_scientific_stacks() -> None:
    source_path = Path(predictions.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    assert roots <= {
        "__future__",
        "dataclasses",
        "fractions",
        "hashlib",
        "json",
        "math",
        "typing",
    }
    assert roots.isdisjoint({"heterodiff", "numpy", "scipy", "torch"})


def test_public_builders_have_no_precision_or_runtime_injection_inputs() -> None:
    for function in (
        predictions.t28_m1_analytic_predictions,
        predictions.t28_m2_analytic_predictions,
        predictions.t28_m1_parameter_perturbation,
        predictions.t28_m2_parameter_perturbation,
    ):
        assert tuple(inspect.signature(function).parameters) == ()
    assert tuple(
        inspect.signature(predictions.conditional_uint64_rejection_bounds).parameters
    ) == ("prediction", "attempts")
    assert tuple(
        inspect.signature(predictions.conditional_exact_iid_sir_bounds).parameters
    ) == ("prediction", "particles")


def test_fraction_records_reject_bool_float_huge_and_reversed_endpoints() -> None:
    bits = predictions.MAX_CP53_TEST28_EXACT_INTEGER_BITS
    huge = Fraction(1 << (bits + 1), 1)
    with pytest.raises(ArithmeticError, match="resource bound"):
        predictions.ClosedRationalInterval(
            huge,
            huge,
            predictions.CP53_TEST28_RATIONAL_ENCLOSURE_BITS,
        )
    for invalid in (False, 0, 0.0, "0"):
        with pytest.raises(TypeError, match="exact Fraction"):
            predictions.ClosedRationalInterval(
                invalid,
                Fraction(1, 1),
                predictions.CP53_TEST28_RATIONAL_ENCLOSURE_BITS,
            )
    with pytest.raises(ValueError, match="reversed"):
        predictions.ClosedRationalInterval(
            Fraction(2, 1),
            Fraction(1, 1),
            predictions.CP53_TEST28_RATIONAL_ENCLOSURE_BITS,
        )
    with pytest.raises(TypeError, match="exact integer"):
        predictions.ClosedRationalInterval(
            Fraction(0, 1),
            Fraction(1, 1),
            True,
        )


def test_perturbation_resource_and_string_preflight_is_bounded() -> None:
    report = predictions.t28_m2_parameter_perturbation()
    table = report.table_perturbations[0]
    difference = table.probability_differences[0]
    with pytest.raises(ValueError, match="frozen bound"):
        replace(table, probability_differences=(difference,) * 17)
    with pytest.raises(ValueError, match="bounded nonempty"):
        replace(table, table_id="x" * 97)
    with pytest.raises(ValueError, match="bounded nonempty"):
        replace(difference, label="x" * 129)
    with pytest.raises(ValueError, match="wrong bounded length"):
        replace(report, table_perturbations=(table,) * 4)
    source_table = (
        predictions.t28_m1_analytic_predictions().ideal_rational.category_table
    )
    with pytest.raises(ValueError, match="bounded nonempty"):
        replace(
            source_table,
            labels=("x" * 97,) + source_table.labels[1:],
        )


class _TouchBomb:
    def __eq__(self, other: object) -> bool:
        del other
        raise AssertionError("hostile equality executed")

    def __ne__(self, other: object) -> bool:
        del other
        raise AssertionError("hostile inequality executed")

    def __len__(self) -> int:
        raise AssertionError("hostile length executed")

    def __hash__(self) -> int:
        raise AssertionError("hostile hash executed")


def test_fixed_text_preflight_rejects_touch_bombs_before_comparison() -> None:
    pair = predictions.t28_m1_analytic_predictions()
    perturbation = predictions.t28_m1_parameter_perturbation()
    uint64_bound = predictions.conditional_uint64_rejection_bounds(
        pair.ideal_rational, 4
    )
    sir_bound = predictions.conditional_exact_iid_sir_bounds(pair.ideal_rational, 8)
    hostile_rewrites = (
        (pair.ideal_rational, "exact_iid_sir_bound_statement"),
        (pair, "schema_version"),
        (perturbation, "proposal_tv_formula_id"),
        (uint64_bound, "bound_statement"),
        (sir_bound, "formula_id"),
    )
    for record, field_name in hostile_rewrites:
        with pytest.raises(TypeError, match="exact text"):
            replace(record, **{field_name: _TouchBomb()})


def _reauthor_prediction(
    original: predictions.FixtureAnalyticPredictions,
    ideal_layer: predictions.AnalyticReferencePrediction,
) -> predictions.FixtureAnalyticPredictions:
    values = {field.name: getattr(original, field.name) for field in fields(original)}
    values["ideal_rational"] = ideal_layer
    values["record_sha256"] = "0" * 64
    provisional = object.__new__(predictions.FixtureAnalyticPredictions)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    values["record_sha256"] = predictions._prediction_digest(provisional)
    return predictions.FixtureAnalyticPredictions(**values)


def test_canonical_validator_accepts_equal_value_reauthoring_but_rejects_redigested_forge() -> None:
    pair = predictions.t28_m1_analytic_predictions()
    equal_probabilities = tuple(
        replace(value) for value in pair.ideal_rational.category_table.probabilities
    )
    equal_table = replace(
        pair.ideal_rational.category_table,
        probabilities=equal_probabilities,
    )
    equal_layer = replace(pair.ideal_rational, category_table=equal_table)
    equal_pair = _reauthor_prediction(pair, equal_layer)
    assert equal_pair == pair
    predictions.validate_t28_analytic_predictions(equal_pair)

    first = equal_probabilities[0]
    widened_first = predictions.ClosedRationalInterval(
        first.lower - Fraction(1, 1 << 300),
        first.upper,
        predictions.CP53_TEST28_RATIONAL_ENCLOSURE_BITS,
    )
    forged_table = replace(
        equal_table,
        probabilities=(widened_first,) + equal_probabilities[1:],
    )
    forged_layer = replace(equal_layer, category_table=forged_table)
    forged_pair = _reauthor_prediction(pair, forged_layer)
    forged_pair.__post_init__()
    with pytest.raises(ValueError, match="canonical derivation"):
        predictions.validate_t28_analytic_predictions(forged_pair)


def test_tamper_wrong_exact_type_subclass_and_pickle_paths_fail_closed() -> None:
    pair = predictions.t28_m2_analytic_predictions()
    object.__setattr__(pair, "record_sha256", "0" * 64)
    with pytest.raises(ValueError, match="digest"):
        predictions.validate_t28_analytic_predictions(pair)
    with pytest.raises(TypeError, match="wrong exact type"):
        predictions.validate_t28_analytic_predictions(object())


def _public_record_examples() -> tuple[object, ...]:
    pair = predictions.t28_m1_analytic_predictions()
    perturbation = predictions.t28_m1_parameter_perturbation()
    uint64_bound = predictions.conditional_uint64_rejection_bounds(
        pair.ideal_rational, 4
    )
    sir_bound = predictions.conditional_exact_iid_sir_bounds(pair.ideal_rational, 8)
    return (
        pair.ideal_rational.normalizer,
        uint64_bound.alpha64_bound,
        pair.ideal_rational.category_table,
        pair.ideal_rational,
        pair,
        perturbation.normalizer_difference,
        perturbation.table_perturbations[0],
        perturbation,
        uint64_bound,
        sir_bound,
    )


@pytest.mark.parametrize(
    "record",
    _public_record_examples(),
    ids=lambda value: type(value).__name__,
)
def test_every_public_record_class_refuses_pickle(record: object) -> None:
    with pytest.raises(TypeError, match="non-pickleable"):
        pickle.dumps(record)


def test_every_public_record_class_refuses_subclassing() -> None:
    classes = tuple(type(value) for value in _public_record_examples())
    assert len(classes) == 10
    assert len(set(classes)) == 10
    for index, record_class in enumerate(classes):
        with pytest.raises(TypeError, match="cannot be subclassed"):
            type("InvalidRecord%d" % index, (record_class,), {})


def test_record_hashes_are_deterministic_and_domain_separated() -> None:
    first = predictions.t28_m1_analytic_predictions()
    second = predictions.t28_m1_analytic_predictions()
    m2 = predictions.t28_m2_analytic_predictions()
    assert first == second
    assert first is not second
    assert first.record_sha256 == second.record_sha256
    assert first.record_sha256 != m2.record_sha256
    perturbation = predictions.t28_m1_parameter_perturbation()
    bound = predictions.conditional_uint64_rejection_bounds(
        first.ideal_rational,
        64,
    )
    sir_bound = predictions.conditional_exact_iid_sir_bounds(
        first.ideal_rational,
        512,
    )
    assert (
        len(
            {
                first.record_sha256,
                perturbation.record_sha256,
                bound.record_sha256,
                sir_bound.record_sha256,
            }
        )
        == 4
    )
    assert all(
        len(value) == 64 and set(value) <= set("0123456789abcdef")
        for value in (
            first.record_sha256,
            perturbation.record_sha256,
            bound.record_sha256,
            sir_bound.record_sha256,
        )
    )
    assert first.record_sha256 == (
        "a5195be1e78547bb8fe8c2ed1b0d813098437c4a820817662d75cc8ec0ac9a31"
    )
    assert m2.record_sha256 == (
        "e4f075724b9af5200a2c70497c6559bb1c3f854fe6a9a716a64c34f403e92324"
    )
    assert perturbation.record_sha256 == (
        "284549111e8baeef91000c2dbd7824c4f1a2a9fb092499a98b41898da7da453e"
    )
    assert predictions.t28_m2_parameter_perturbation().record_sha256 == (
        "cca445cad3453c52123805c122832631083db196338bcc7ec590920530cf04e5"
    )
    assert bound.record_sha256 == (
        "53f6c2b495519b5c2312022851a387d4e340af67377882ebc81bd31b9c39419d"
    )
    assert sir_bound.record_sha256 == (
        "33facfcd633b6331057bbc5cb3810b5d33c8f504efb6f4713cfca6f80e84aa77"
    )


def _run_clean_evaluation_subprocess(code: str) -> str:
    project_root = Path(predictions.__file__).resolve().parents[3]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = "%s:%s" % (
        project_root / "src",
        project_root,
    )
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-W", "error", "-c", code],
        cwd=project_root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.stderr == ""
    return completed.stdout.strip()


def test_record_digests_are_stable_across_clean_python_processes() -> None:
    code = """
import json
import sys
from heterodiff.evaluation import mixed_initializer_test28_predictions as p
assert "numpy" not in sys.modules
assert "scipy" not in sys.modules
m1 = p.t28_m1_analytic_predictions()
m2 = p.t28_m2_analytic_predictions()
values = {
    "m1": m1.record_sha256,
    "m2": m2.record_sha256,
    "m1_perturbation": p.t28_m1_parameter_perturbation().record_sha256,
    "m2_perturbation": p.t28_m2_parameter_perturbation().record_sha256,
    "m1_rat_u64_a64": p.conditional_uint64_rejection_bounds(
        m1.ideal_rational, 64
    ).record_sha256,
    "m2_b64_sir_j512": p.conditional_exact_iid_sir_bounds(
        m2.binary64_parameter, 512
    ).record_sha256,
}
print(json.dumps(values, sort_keys=True, separators=(",", ":")))
"""
    outputs = [_run_clean_evaluation_subprocess(code) for _ in range(2)]
    assert outputs[0] == outputs[1]
    decoded = json.loads(outputs[0])
    assert decoded["m1"] == predictions.t28_m1_analytic_predictions().record_sha256
    assert decoded["m2"] == predictions.t28_m2_analytic_predictions().record_sha256


_LEGACY_EVALUATION_EXPORTS = (
    "BIASED_ENERGY",
    "WASSERSTEIN_1D",
    "GroupMetricFloor",
    "GroupSplitDistance",
    "biased_energy_distance",
    "estimate_group_metric_floor",
    "wasserstein_distance_1d",
)


def test_lazy_evaluation_dir_and_unknown_attribute_do_not_load_scientific_stack() -> None:
    code = """
import sys
import heterodiff.evaluation as evaluation
expected = {
    "BIASED_ENERGY", "WASSERSTEIN_1D", "GroupMetricFloor",
    "GroupSplitDistance", "biased_energy_distance",
    "estimate_group_metric_floor", "wasserstein_distance_1d",
}
assert set(evaluation.__all__) == expected
assert expected <= set(dir(evaluation))
assert "heterodiff.evaluation.metric_floor" not in sys.modules
assert "numpy" not in sys.modules
assert "scipy" not in sys.modules
try:
    getattr(evaluation, "definitely_missing")
except AttributeError as error:
    assert "definitely_missing" in str(error)
else:
    raise AssertionError("unknown package attribute did not fail")
try:
    evaluation.__getattr__(object())
except AttributeError:
    pass
else:
    raise AssertionError("non-text package attribute did not fail")
assert "heterodiff.evaluation.metric_floor" not in sys.modules
assert "numpy" not in sys.modules
assert "scipy" not in sys.modules
"""
    assert _run_clean_evaluation_subprocess(code) == ""


def test_named_legacy_import_loads_all_exports_once_and_caches_identity() -> None:
    code = """
import sys
import heterodiff.evaluation as evaluation
assert "heterodiff.evaluation.metric_floor" not in sys.modules
assert "numpy" not in sys.modules and "scipy" not in sys.modules
from heterodiff.evaluation import (
    BIASED_ENERGY, WASSERSTEIN_1D, GroupMetricFloor, GroupSplitDistance,
    biased_energy_distance, estimate_group_metric_floor,
    wasserstein_distance_1d,
)
from heterodiff.evaluation import metric_floor
objects = {
    "BIASED_ENERGY": BIASED_ENERGY,
    "WASSERSTEIN_1D": WASSERSTEIN_1D,
    "GroupMetricFloor": GroupMetricFloor,
    "GroupSplitDistance": GroupSplitDistance,
    "biased_energy_distance": biased_energy_distance,
    "estimate_group_metric_floor": estimate_group_metric_floor,
    "wasserstein_distance_1d": wasserstein_distance_1d,
}
assert set(objects) == set(evaluation.__all__)
for name, value in objects.items():
    assert evaluation.__dict__[name] is value
    assert getattr(evaluation, name) is value
    assert getattr(metric_floor, name) is value
first = evaluation.BIASED_ENERGY
def bomb(name):
    raise AssertionError("cached attribute invoked __getattr__: %r" % (name,))
evaluation.__getattr__ = bomb
assert evaluation.BIASED_ENERGY is first
assert "heterodiff.evaluation.metric_floor" in sys.modules
assert "numpy" in sys.modules and "scipy" in sys.modules
"""
    assert _run_clean_evaluation_subprocess(code) == ""


def test_star_import_exposes_exact_legacy_surface_and_shared_identity() -> None:
    code = """
import sys
import heterodiff.evaluation as evaluation
assert "numpy" not in sys.modules and "scipy" not in sys.modules
namespace = {}
exec("from heterodiff.evaluation import *", namespace)
exported = set(namespace) - {"__builtins__"}
assert exported == set(evaluation.__all__)
from heterodiff.evaluation import metric_floor
for name in evaluation.__all__:
    assert namespace[name] is getattr(evaluation, name)
    assert namespace[name] is getattr(metric_floor, name)
assert "numpy" in sys.modules and "scipy" in sys.modules
"""
    assert _run_clean_evaluation_subprocess(code) == ""


def test_direct_metric_floor_submodule_import_preserves_lazy_export_cache_contract() -> None:
    code = """
import importlib
import sys
import heterodiff.evaluation as evaluation
assert "numpy" not in sys.modules and "scipy" not in sys.modules
metric_floor = importlib.import_module("heterodiff.evaluation.metric_floor")
assert "numpy" in sys.modules and "scipy" in sys.modules
for name in evaluation.__all__:
    assert name not in evaluation.__dict__
    value = getattr(evaluation, name)
    assert value is getattr(metric_floor, name)
    assert evaluation.__dict__[name] is value
"""
    assert _run_clean_evaluation_subprocess(code) == ""
