"""Independent and hostile tests for the CP55 ``T28-A0-Q`` oracle."""

from __future__ import annotations

import ast
import inspect
import json
import os
import pickle
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from fractions import Fraction
from itertools import product
from math import factorial
from pathlib import Path

import pytest

from heterodiff.evaluation import mixed_initializer_test28_atomic_q_oracle as oracle


_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_ACTIVITY = Fraction(1, 1)
_RATIONAL_WEIGHTS = (Fraction(2, 5), Fraction(3, 5))
_BINARY64_WEIGHTS = (
    Fraction(3602879701896397, 9007199254740992),
    Fraction(5404319552844595, 9007199254740992),
)
_SUPPORT_LABELS = ("empty", "a", "b", "aa", "ab", "bb")
_COUNT_VECTORS = ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2))
_RUNTIME_COUNT_VECTORS = ((0, 0), (0, 1), (1, 0), (0, 2), (1, 1), (2, 0))
_RUNTIME_TO_PROTOCOL = (0, 2, 1, 5, 4, 3)
_SCORES = (
    Fraction(0, 1),
    Fraction(1, 2),
    Fraction(-1, 2),
    Fraction(1, 1),
    Fraction(1, 2),
    Fraction(-1, 1),
)
_INDEPENDENT_BITS = 512
_INDEPENDENT_WIDTH = Fraction(1, 1 << _INDEPENDENT_BITS)


def _enumerate_cap_support(type_count: int, cap: int) -> tuple[tuple[int, ...], ...]:
    """Complete enumeration independent of the implementation's support."""

    values = tuple(
        counts
        for counts in product(range(cap + 1), repeat=type_count)
        if sum(counts) <= cap
    )
    return tuple(
        sorted(values, key=lambda counts: (sum(counts), tuple(-x for x in counts)))
    )


def _base_probabilities(
    weights: tuple[Fraction, Fraction],
) -> tuple[Fraction, ...]:
    """Reconstruct the base law; no serialized mass vector is consumed."""

    raw = []
    for counts in _enumerate_cap_support(2, 2):
        value = _ACTIVITY ** sum(counts)
        for weight, multiplicity in zip(weights, counts):
            value *= weight**multiplicity / factorial(multiplicity)
        raw.append(value)
    normalizer = sum(raw, _ZERO)
    assert normalizer == Fraction(5, 2)
    return tuple(value / normalizer for value in raw)


def _raw_base_weights(
    weights: tuple[Fraction, Fraction],
) -> tuple[Fraction, ...]:
    return tuple(
        probability * Fraction(5, 2) for probability in _base_probabilities(weights)
    )


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


def _scale_nonnegative(
    scalar: Fraction,
    interval: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction]:
    assert scalar >= 0 and interval[0] >= 0
    return scalar * interval[0], scalar * interval[1]


def _multiply_nonnegative(
    left: tuple[Fraction, Fraction],
    right: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction]:
    assert left[0] >= 0 and right[0] >= 0
    return left[0] * right[0], left[1] * right[1]


def _subtract(
    left: tuple[Fraction, Fraction],
    right: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction]:
    return left[0] - right[1], left[1] - right[0]


def _absolute(
    interval: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction]:
    lower, upper = interval
    if lower <= _ZERO <= upper:
        return _ZERO, max(-lower, upper)
    if lower > _ZERO:
        return lower, upper
    return -upper, -lower


def _divide_positive(
    numerator: tuple[Fraction, Fraction],
    denominator: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction]:
    assert numerator[0] >= 0 and denominator[0] > 0
    return numerator[0] / denominator[1], numerator[1] / denominator[0]


def _positive_exp_bracket(value: Fraction) -> tuple[Fraction, Fraction]:
    """Rigorous positive-series bracket using an exact geometric tail bound.

    The implementation under test uses its own frozen interval construction.
    This checker deliberately uses a different proof: after the partial Taylor
    sum, every ratio in the remaining positive tail is bounded by the first
    remaining ratio.
    """

    assert _ZERO < value <= Fraction(2, 1)
    term = _ONE
    partial = _ONE
    for index in range(1, 8193):
        term = term * value / index
        partial += term
        next_term = term * value / (index + 1)
        tail_ratio = value / (index + 2)
        upper = partial + next_term / (_ONE - tail_ratio)
        if upper - partial <= _INDEPENDENT_WIDTH:
            return partial, upper
    raise AssertionError("independent positive exponential series did not terminate")


def _exp_bracket(value: Fraction) -> tuple[Fraction, Fraction]:
    if value == _ZERO:
        return _point(_ONE)
    if value > _ZERO:
        return _positive_exp_bracket(value)
    positive_lower, positive_upper = _positive_exp_bracket(-value)
    return _ONE / positive_upper, _ONE / positive_lower


def _independent_layer(
    weights: tuple[Fraction, Fraction],
) -> dict[str, tuple[object, ...] | tuple[Fraction, Fraction]]:
    base = _base_probabilities(weights)
    exponential = tuple(_exp_bracket(score) for score in _SCORES)
    masses = tuple(
        _scale_nonnegative(probability, exp_interval)
        for probability, exp_interval in zip(base, exponential)
    )
    normalizer = _sum(masses)
    probabilities = tuple(_divide_positive(mass, normalizer) for mass in masses)
    envelope = max(_SCORES)
    shifted_exponential = tuple(_exp_bracket(score - envelope) for score in _SCORES)
    shifted_masses = tuple(
        _scale_nonnegative(probability, exp_interval)
        for probability, exp_interval in zip(base, shifted_exponential)
    )
    shifted_normalizer = _sum(shifted_masses)
    shifted_probabilities = tuple(
        _divide_positive(mass, shifted_normalizer) for mass in shifted_masses
    )
    return {
        "base": base,
        "exponential": exponential,
        "masses": masses,
        "normalizer": normalizer,
        "probabilities": probabilities,
        "shifted_exponential": shifted_exponential,
        "shifted_masses": shifted_masses,
        "shifted_normalizer": shifted_normalizer,
        "shifted_probabilities": shifted_probabilities,
    }


def _independent_layer_difference() -> dict[str, tuple[Fraction, Fraction]]:
    rational = _independent_layer(_RATIONAL_WEIGHTS)
    binary64 = _independent_layer(_BINARY64_WEIGHTS)
    normalizer = _subtract(binary64["normalizer"], rational["normalizer"])
    probability_differences = tuple(
        _subtract(right, left)
        for left, right in zip(rational["probabilities"], binary64["probabilities"])
    )
    total_variation = _scale_nonnegative(
        Fraction(1, 2),
        _sum(tuple(_absolute(value) for value in probability_differences)),
    )
    return {
        "normalizer": normalizer,
        "shifted_acceptance": _subtract(
            binary64["shifted_normalizer"], rational["shifted_normalizer"]
        ),
        "total_variation": total_variation,
    }


def _assert_contains(actual: object, expected: tuple[Fraction, Fraction]) -> None:
    assert type(actual) is oracle.ClosedRationalInterval
    assert actual.lower <= expected[0] <= expected[1] <= actual.upper


class _TouchBomb:
    def __eq__(self, other: object) -> bool:
        del other
        raise AssertionError("hostile equality executed")

    def __ne__(self, other: object) -> bool:
        del other
        raise AssertionError("hostile inequality executed")

    def __len__(self) -> int:
        raise AssertionError("hostile length executed")

    def __iter__(self):
        raise AssertionError("hostile iteration executed")

    def __hash__(self) -> int:
        raise AssertionError("hostile hash executed")


class _TupleAlias(tuple):
    pass


class _TextAlias(str):
    pass


class _IntegerAlias(int):
    pass


class _FractionAlias(Fraction):
    pass


def _builder_arguments(
    *,
    fixture_id: object = "T28-A0-Q",
    state_labels: object = _SUPPORT_LABELS,
    count_vectors: object = _COUNT_VECTORS,
    activity: object = _ACTIVITY,
    ideal_type_weights: object = _RATIONAL_WEIGHTS,
    binary64_type_weights: object = _BINARY64_WEIGHTS,
    type_labels: object = ("a", "b"),
    event_dimensions: object = (0, 0),
    total_cap: object = 2,
    exact_scores: object = _SCORES,
    precision_schedule: object = (64, 128, 192, 256),
) -> dict[str, object]:
    return {
        "fixture_id": fixture_id,
        "state_labels": state_labels,
        "count_vectors": count_vectors,
        "activity": activity,
        "ideal_type_weights": ideal_type_weights,
        "binary64_type_weights": binary64_type_weights,
        "type_labels": type_labels,
        "event_dimensions": event_dimensions,
        "total_cap": total_cap,
        "exact_scores": exact_scores,
        "precision_schedule": precision_schedule,
    }


def test_frozen_score_table_is_count_keyed_and_runtime_order_is_explicit() -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    provider = pair.score_provider

    assert provider.fixture_id == "T28-A0-Q"
    assert provider.state_labels == _SUPPORT_LABELS
    assert provider.count_vectors == _COUNT_VECTORS
    assert provider.exact_scores == _SCORES
    assert provider.lower_score_bound == Fraction(-1, 1)
    assert provider.upper_score_bound == Fraction(1, 1)
    assert provider.runtime_count_vectors == _RUNTIME_COUNT_VECTORS
    assert provider.runtime_to_protocol_permutation == _RUNTIME_TO_PROTOCOL
    assert provider.count_keyed_lookup_required is True

    by_count = {}
    for index, count_vector in enumerate(_COUNT_VECTORS):
        evaluation = provider.evaluate(count_vector)
        assert type(evaluation) is oracle.AtomicQScoreEvaluation
        assert evaluation.protocol_index == index
        assert evaluation.state_label == _SUPPORT_LABELS[index]
        assert evaluation.count_vector == count_vector
        assert evaluation.exact_score == _SCORES[index]
        by_count[count_vector] = evaluation.exact_score

    expected_runtime_scores = tuple(by_count[value] for value in _RUNTIME_COUNT_VECTORS)
    assert expected_runtime_scores == tuple(
        _SCORES[index] for index in _RUNTIME_TO_PROTOCOL
    )
    assert provider.scores_in_runtime_order() == expected_runtime_scores
    assert expected_runtime_scores != _SCORES


def test_real_runtime_counting_space_confirms_nonpositional_permutation() -> None:
    from heterodiff.theory.finite_atomic_counting import FiniteAtomicCountingSpace

    runtime = FiniteAtomicCountingSpace(("a", "b"), 2)
    assert runtime.states == _RUNTIME_COUNT_VECTORS
    protocol_index = {value: index for index, value in enumerate(_COUNT_VECTORS)}
    assert tuple(protocol_index[value] for value in runtime.states) == (
        _RUNTIME_TO_PROTOCOL
    )

    pair = oracle.t28_a0_q_oracle_pair()
    correct = pair.score_provider.scores_in_runtime_order()
    positional = pair.score_provider.exact_scores
    assert correct != positional
    assert correct[1] == Fraction(-1, 2) != positional[1]
    assert correct[3] == Fraction(-1, 1) != positional[3]
    assert correct[5] == Fraction(1, 1) != positional[5]


@pytest.mark.parametrize(
    "layer_name,weights",
    (
        ("ideal_rational", _RATIONAL_WEIGHTS),
        ("binary64_parameter", _BINARY64_WEIGHTS),
    ),
)
def test_each_layer_contains_independent_factorial_and_exponential_derivation(
    layer_name: str,
    weights: tuple[Fraction, Fraction],
) -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    layer = getattr(pair, layer_name)
    expected = _independent_layer(weights)
    base = expected["base"]
    raw = _raw_base_weights(weights)

    assert layer.fixture_id == "T28-A0-Q"
    assert layer.parameter_layer == layer_name
    assert layer.activity == _ACTIVITY
    assert layer.total_cap == 2
    assert layer.type_labels == ("a", "b")
    assert layer.event_dimensions == (0, 0)
    assert layer.type_weights == weights
    assert layer.support_labels == _SUPPORT_LABELS
    assert layer.count_vectors == _COUNT_VECTORS
    assert layer.exact_scores == _SCORES
    assert layer.score_lower_bound == Fraction(-1, 1)
    assert layer.score_upper_bound == Fraction(1, 1)
    assert layer.raw_base_normalizer_by_support == Fraction(5, 2)
    assert layer.raw_base_normalizer_by_count_series == Fraction(5, 2)
    assert layer.normalized_base_masses == base
    assert sum(layer.normalized_base_masses, _ZERO) == _ONE
    assert layer.precision_schedule == (64, 128, 192, 256)

    _assert_contains(layer.target_normalizer_interval, expected["normalizer"])
    _assert_contains(layer.shifted_acceptance_interval, expected["shifted_normalizer"])
    assert layer.probability_sum_interval.lower <= _ONE
    assert layer.probability_sum_interval.upper >= _ONE

    for index, state in enumerate(layer.states):
        assert state.protocol_index == index
        assert state.state_label == _SUPPORT_LABELS[index]
        assert state.count_vector == _COUNT_VECTORS[index]
        assert state.multiplicity_factorials == tuple(
            factorial(value) for value in _COUNT_VECTORS[index]
        )
        assert state.raw_base_weight == raw[index]
        assert state.normalized_base_mass == base[index]
        assert state.exact_score == _SCORES[index]
        assert state.exact_shifted_score == _SCORES[index] - Fraction(1, 1)
        _assert_contains(state.exp_score_interval, expected["exponential"][index])
        _assert_contains(
            state.exp_shifted_score_interval,
            expected["shifted_exponential"][index],
        )
        _assert_contains(state.direct_target_mass_interval, expected["masses"][index])
        _assert_contains(
            state.shifted_target_mass_interval, expected["shifted_masses"][index]
        )
        _assert_contains(
            state.target_probability_interval, expected["probabilities"][index]
        )
        _assert_contains(
            state.target_probability_interval,
            expected["shifted_probabilities"][index],
        )
        assert state.direct_target_mass_interval == oracle.ClosedRationalInterval(
            state.normalized_base_mass * state.exp_score_interval.lower,
            state.normalized_base_mass * state.exp_score_interval.upper,
        )
        assert state.shifted_target_mass_interval == oracle.ClosedRationalInterval(
            state.normalized_base_mass * state.exp_shifted_score_interval.lower,
            state.normalized_base_mass * state.exp_shifted_score_interval.upper,
        )

    assert tuple(state.target_probability_interval for state in layer.states) == (
        layer.target_probability_intervals
    )


@pytest.mark.parametrize(
    "layer_name,weights",
    (
        ("ideal_rational", _RATIONAL_WEIGHTS),
        ("binary64_parameter", _BINARY64_WEIGHTS),
    ),
)
def test_precision_schedule_certifies_direct_and_shifted_routes_at_every_stage(
    layer_name: str,
    weights: tuple[Fraction, Fraction],
) -> None:
    layer = getattr(oracle.t28_a0_q_oracle_pair(), layer_name)
    expected = _independent_layer(weights)
    prior = None
    for bits, stage in zip(layer.precision_schedule, layer.precision_stages):
        assert stage.precision_bits == bits
        assert 1 <= stage.taylor_terms <= oracle.MAX_CP55_TAYLOR_TERMS
        assert stage.exp_minus_half_interval.width <= Fraction(1, 1 << bits)
        _assert_contains(stage.exp_minus_half_interval, _exp_bracket(Fraction(-1, 2)))
        _assert_contains(stage.direct_normalizer_interval, expected["normalizer"])
        _assert_contains(
            stage.shifted_recovered_normalizer_interval, expected["normalizer"]
        )
        _assert_contains(stage.normalizer_interval, expected["normalizer"])
        _assert_contains(
            stage.shifted_acceptance_interval, expected["shifted_normalizer"]
        )
        assert stage.probability_sum_interval.lower <= _ONE
        assert stage.probability_sum_interval.upper >= _ONE

        for index in range(6):
            _assert_contains(
                stage.exp_score_intervals[index], expected["exponential"][index]
            )
            _assert_contains(
                stage.exp_shifted_score_intervals[index],
                expected["shifted_exponential"][index],
            )
            _assert_contains(
                stage.direct_target_mass_intervals[index],
                expected["masses"][index],
            )
            _assert_contains(
                stage.shifted_target_mass_intervals[index],
                expected["shifted_masses"][index],
            )
            _assert_contains(
                stage.direct_probability_intervals[index],
                expected["probabilities"][index],
            )
            _assert_contains(
                stage.shifted_probability_intervals[index],
                expected["shifted_probabilities"][index],
            )
            _assert_contains(
                stage.probability_intervals[index],
                expected["probabilities"][index],
            )

        if prior is not None:
            assert stage.normalizer_interval.lower >= prior.normalizer_interval.lower
            assert stage.normalizer_interval.upper <= prior.normalizer_interval.upper
            assert stage.normalizer_interval.width < prior.normalizer_interval.width
            for current, previous in zip(
                stage.probability_intervals, prior.probability_intervals
            ):
                assert current.lower >= previous.lower
                assert current.upper <= previous.upper
        prior = stage


def test_binary64_minus_ideal_perturbation_is_directional_and_nonzero() -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    perturbation = pair.perturbation
    expected = _independent_layer_difference()
    rational = _independent_layer(_RATIONAL_WEIGHTS)
    binary64 = _independent_layer(_BINARY64_WEIGHTS)

    exact_base_tv = (
        sum(
            (
                abs(right - left)
                for left, right in zip(rational["base"], binary64["base"])
            ),
            _ZERO,
        )
        / 2
    )
    assert perturbation.direction == "binary64_parameter-minus-ideal_rational"
    assert perturbation.exact_base_proposal_total_variation == exact_base_tv
    _assert_contains(
        perturbation.binary64_minus_ideal_normalizer_difference,
        expected["normalizer"],
    )
    _assert_contains(
        perturbation.binary64_minus_ideal_shifted_acceptance_difference,
        expected["shifted_acceptance"],
    )
    assert perturbation.binary64_minus_ideal_normalizer_difference.lower > 0
    for actual, left, right in zip(
        perturbation.binary64_minus_ideal_probability_differences,
        rational["probabilities"],
        binary64["probabilities"],
    ):
        _assert_contains(actual, _subtract(right, left))
    _assert_contains(
        perturbation.target_total_variation_interval,
        expected["total_variation"],
    )
    assert perturbation.target_total_variation_interval.lower > 0
    assert pair.ideal_rational.record_sha256 != pair.binary64_parameter.record_sha256
    assert (
        pair.ideal_rational.target_probability_intervals
        != pair.binary64_parameter.target_probability_intervals
    )


def test_published_final_intervals_have_a_strict_high_precision_width_cap() -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    width_cap = Fraction(1, 1 << 250)
    intervals = []
    for layer in (pair.ideal_rational, pair.binary64_parameter):
        final = layer.precision_stages[-1]
        intervals.extend(
            (
                layer.target_normalizer_interval,
                layer.shifted_acceptance_interval,
                layer.probability_sum_interval,
                final.exp_minus_half_interval,
                final.direct_normalizer_interval,
                final.shifted_recovered_normalizer_interval,
                final.normalizer_interval,
            )
        )
        for name in (
            "exp_score_intervals",
            "exp_shifted_score_intervals",
            "direct_target_mass_intervals",
            "shifted_target_mass_intervals",
            "direct_probability_intervals",
            "shifted_probability_intervals",
            "probability_intervals",
        ):
            intervals.extend(getattr(final, name))
    intervals.extend(
        (
            pair.perturbation.binary64_minus_ideal_normalizer_difference,
            pair.perturbation.binary64_minus_ideal_shifted_acceptance_difference,
            pair.perturbation.target_total_variation_interval,
        )
    )
    intervals.extend(pair.perturbation.binary64_minus_ideal_probability_differences)
    assert intervals
    assert all(value.width < width_cap for value in intervals)


def test_wrong_factorials_and_a0_h_factors_are_detected_as_different_targets() -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    support = _enumerate_cap_support(2, 2)
    correct_base = _base_probabilities(_RATIONAL_WEIGHTS)

    missing_raw = tuple(
        __import__("math").prod(
            weight**count for weight, count in zip(_RATIONAL_WEIGHTS, counts)
        )
        for counts in support
    )
    missing_total = sum(missing_raw, _ZERO)
    missing_base = tuple(value / missing_total for value in missing_raw)
    correct_raw = _raw_base_weights(_RATIONAL_WEIGHTS)
    extra_raw = tuple(
        value / factorial(sum(counts)) for value, counts in zip(correct_raw, support)
    )
    extra_total = sum(extra_raw, _ZERO)
    extra_base = tuple(value / extra_total for value in extra_raw)

    assert missing_total == Fraction(69, 25)
    assert extra_total == Fraction(9, 4)
    assert missing_base != correct_base
    assert extra_base != correct_base
    assert pair.ideal_rational.normalized_base_masses == correct_base

    a0_h_factors = (
        Fraction(1, 1),
        Fraction(2, 1),
        Fraction(1, 2),
        Fraction(3, 1),
        Fraction(3, 2),
        Fraction(1, 4),
    )
    a0_h_normalizer = sum(
        (base * factor for base, factor in zip(correct_base, a0_h_factors)),
        _ZERO,
    )
    assert a0_h_normalizer == Fraction(549, 500)
    target_z = pair.ideal_rational.target_normalizer_interval
    assert not target_z.lower <= a0_h_normalizer <= target_z.upper
    assert pair.score_provider.exact_scores != a0_h_factors
    assert pair.score_provider.a0_h_logarithm_claim is False


def test_linearized_exp_and_forgotten_envelope_rescaling_are_counterexamples() -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    base = pair.ideal_rational.normalized_base_masses
    one_plus_q_normalizer = sum(
        (mass * (_ONE + score) for mass, score in zip(base, _SCORES)),
        _ZERO,
    )
    target_z = pair.ideal_rational.target_normalizer_interval
    beta = pair.ideal_rational.shifted_acceptance_interval

    assert one_plus_q_normalizer == Fraction(121, 125)
    assert not target_z.lower <= one_plus_q_normalizer <= target_z.upper
    assert beta.upper < target_z.lower

    final = pair.ideal_rational.precision_stages[-1]
    assert final.shifted_recovered_normalizer_interval.lower <= target_z.upper
    assert final.shifted_recovered_normalizer_interval.upper >= target_z.lower
    assert final.shifted_acceptance_interval == beta
    assert final.shifted_acceptance_interval != final.normalizer_interval


def test_public_builder_accepts_primitives_only_and_reproduces_canonical_pair() -> None:
    signature = inspect.signature(oracle.derive_t28_a0_q_oracle_pair)
    assert tuple(signature.parameters) == (
        "fixture_id",
        "state_labels",
        "count_vectors",
        "activity",
        "ideal_type_weights",
        "binary64_type_weights",
        "type_labels",
        "event_dimensions",
        "total_cap",
        "exact_scores",
        "precision_schedule",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert not any(
        forbidden in name
        for name in signature.parameters
        for forbidden in (
            "base_mass",
            "exponential",
            "normalizer",
            "probability",
            "target_mass",
            "runtime",
        )
    )
    pair = oracle.derive_t28_a0_q_oracle_pair(**_builder_arguments())
    assert pair == oracle.t28_a0_q_oracle_pair()
    assert oracle.validate_t28_a0_q_oracle_pair(pair) is pair
    with pytest.raises(TypeError, match="unexpected keyword"):
        oracle.derive_t28_a0_q_oracle_pair(
            **_builder_arguments(),
            normalized_base_masses=(Fraction(1, 6),) * 6,
        )


@pytest.mark.parametrize(
    "rewrite,match",
    (
        ({"fixture_id": "T28-A0-H"}, "frozen|differ"),
        ({"state_labels": _SUPPORT_LABELS[:-1]}, "length"),
        (
            {"state_labels": _SUPPORT_LABELS[:-1] + ("ab",)},
            "frozen|differ",
        ),
        ({"count_vectors": _COUNT_VECTORS[:-1]}, "length"),
        (
            {"count_vectors": _COUNT_VECTORS[:-1] + ((0, 0),)},
            "frozen|differ",
        ),
        ({"count_vectors": _RUNTIME_COUNT_VECTORS}, "frozen|differ"),
        ({"activity": Fraction(2, 1)}, "frozen|differ"),
        (
            {"ideal_type_weights": (Fraction(1, 2), Fraction(1, 2))},
            "frozen|differ",
        ),
        ({"binary64_type_weights": _RATIONAL_WEIGHTS}, "frozen|differ"),
        ({"type_labels": ("b", "a")}, "frozen|differ"),
        ({"event_dimensions": (0, 1)}, "frozen|differ"),
        ({"total_cap": 1}, "frozen|differ"),
        ({"exact_scores": _SCORES[:-1]}, "length"),
        (
            {"exact_scores": (_SCORES[0], _SCORES[2], _SCORES[1]) + _SCORES[3:]},
            "frozen|differ",
        ),
        (
            {
                "exact_scores": (
                    Fraction(1, 1),
                    Fraction(2, 1),
                    Fraction(1, 2),
                    Fraction(3, 1),
                    Fraction(3, 2),
                    Fraction(1, 4),
                )
            },
            "frozen|differ",
        ),
        ({"precision_schedule": (64, 128, 192)}, "length"),
        ({"precision_schedule": (64, 128, 192, 255)}, "frozen|differ"),
    ),
)
def test_wrong_fixture_support_parameters_scores_and_precision_fail_closed(
    rewrite: dict[str, object], match: str
) -> None:
    arguments = _builder_arguments()
    arguments.update(rewrite)
    with pytest.raises((TypeError, ValueError), match=match):
        oracle.derive_t28_a0_q_oracle_pair(**arguments)


@pytest.mark.parametrize(
    "rewrite,match",
    (
        ({"fixture_id": _TouchBomb()}, "fixture_id must be exact text"),
        ({"state_labels": _TouchBomb()}, "state_labels must be an exact tuple"),
        ({"count_vectors": _TouchBomb()}, "count_vectors must be an exact tuple"),
        ({"activity": _TouchBomb()}, "activity must be an exact Fraction"),
        (
            {"ideal_type_weights": _TouchBomb()},
            "ideal_type_weights must be an exact tuple",
        ),
        (
            {"binary64_type_weights": _TouchBomb()},
            "binary64_type_weights must be an exact tuple",
        ),
        ({"type_labels": _TouchBomb()}, "type_labels must be an exact tuple"),
        (
            {"event_dimensions": _TouchBomb()},
            "event_dimensions must be an exact tuple",
        ),
        ({"total_cap": _TouchBomb()}, "total_cap must be an exact"),
        ({"exact_scores": _TouchBomb()}, "exact_scores must be an exact tuple"),
        (
            {"precision_schedule": _TouchBomb()},
            "precision_schedule must be an exact tuple",
        ),
        (
            {"state_labels": (_TouchBomb(),) + _SUPPORT_LABELS[1:]},
            "state label must be exact text",
        ),
        (
            {"count_vectors": (_TouchBomb(),) + _COUNT_VECTORS[1:]},
            "count vector must be an exact tuple",
        ),
        (
            {"ideal_type_weights": (_TouchBomb(), Fraction(3, 5))},
            "entry must be an exact Fraction",
        ),
        (
            {"exact_scores": (_TouchBomb(),) + _SCORES[1:]},
            "exact score must be an exact Fraction",
        ),
    ),
)
def test_exact_type_preflight_rejects_touch_bombs_without_using_them(
    rewrite: dict[str, object], match: str
) -> None:
    arguments = _builder_arguments()
    arguments.update(rewrite)
    with pytest.raises(TypeError, match=match):
        oracle.derive_t28_a0_q_oracle_pair(**arguments)


@pytest.mark.parametrize(
    "rewrite,match",
    (
        ({"fixture_id": _TextAlias("T28-A0-Q")}, "exact text"),
        ({"state_labels": list(_SUPPORT_LABELS)}, "exact tuple"),
        ({"state_labels": _TupleAlias(_SUPPORT_LABELS)}, "exact tuple"),
        ({"activity": True}, "exact Fraction"),
        ({"activity": 1.0}, "exact Fraction"),
        ({"activity": _FractionAlias(1, 1)}, "exact Fraction"),
        ({"ideal_type_weights": (0.4, 0.6)}, "exact Fraction"),
        ({"binary64_type_weights": list(_BINARY64_WEIGHTS)}, "exact tuple"),
        ({"type_labels": ["a", "b"]}, "exact tuple"),
        ({"event_dimensions": (False, 0)}, "exact non-boolean integer"),
        ({"total_cap": True}, "exact non-boolean integer"),
        ({"total_cap": 2.0}, "exact non-boolean integer"),
        ({"total_cap": _IntegerAlias(2)}, "exact non-boolean integer"),
        ({"exact_scores": (0.0,) + _SCORES[1:]}, "exact Fraction"),
        ({"precision_schedule": [64, 128, 192, 256]}, "exact tuple"),
        (
            {"precision_schedule": (64, 128, 192, True)},
            "exact non-boolean integer",
        ),
    ),
)
def test_mutable_float_bool_and_subclass_aliases_fail_closed(
    rewrite: dict[str, object], match: str
) -> None:
    arguments = _builder_arguments()
    arguments.update(rewrite)
    with pytest.raises(TypeError, match=match):
        oracle.derive_t28_a0_q_oracle_pair(**arguments)


def test_builder_resource_bounds_apply_before_frozen_value_comparison() -> None:
    huge = Fraction(1 << (oracle.MAX_CP55_EXACT_INTEGER_BITS + 1), 1)
    with pytest.raises(ValueError, match="bit bound"):
        oracle.derive_t28_a0_q_oracle_pair(**_builder_arguments(activity=huge))
    with pytest.raises(ValueError, match="bit bound"):
        oracle.derive_t28_a0_q_oracle_pair(
            **_builder_arguments(ideal_type_weights=(huge, _ONE - huge))
        )
    with pytest.raises(ValueError, match="bit bound"):
        oracle.derive_t28_a0_q_oracle_pair(
            **_builder_arguments(exact_scores=(huge,) + _SCORES[1:])
        )
    with pytest.raises(ValueError, match="bounded length"):
        oracle.derive_t28_a0_q_oracle_pair(
            **_builder_arguments(fixture_id="x" * (oracle.MAX_CP55_TEXT_LENGTH + 1))
        )
    with pytest.raises(ValueError, match="bounded length"):
        oracle.derive_t28_a0_q_oracle_pair(
            **_builder_arguments(state_labels=("x" * 33,) + _SUPPORT_LABELS[1:])
        )


@pytest.mark.parametrize(
    "value,exception,match",
    (
        ([(0), (0)], TypeError, "exact tuple"),
        (_TupleAlias((0, 0)), TypeError, "exact tuple"),
        ((_TouchBomb(), 0), TypeError, "exact non-boolean integer"),
        ((False, 0), TypeError, "exact non-boolean integer"),
        ((0.0, 0), TypeError, "exact non-boolean integer"),
        ((_IntegerAlias(0), 0), TypeError, "exact non-boolean integer"),
        ((-1, 0), ValueError, "bound|support"),
        ((3, 0), ValueError, "bound|support"),
        ((1 << 100000, 0), ValueError, "bound|support"),
        ((1, 2), ValueError, "bound|support"),
    ),
)
def test_score_provider_evaluate_rejects_hostile_or_out_of_support_counts(
    value: object,
    exception: type[Exception],
    match: str,
) -> None:
    provider = oracle.t28_a0_q_oracle_pair().score_provider
    with pytest.raises(exception, match=match):
        provider.evaluate(value)


def test_interval_constructor_rejects_wrong_types_reversed_and_oversized() -> None:
    with pytest.raises(TypeError, match="exact Fraction"):
        oracle.ClosedRationalInterval(0.0, _ONE)
    with pytest.raises(TypeError, match="exact Fraction"):
        oracle.ClosedRationalInterval(_FractionAlias(0, 1), _ONE)
    with pytest.raises(ValueError, match="reversed"):
        oracle.ClosedRationalInterval(_ONE, _ZERO)
    huge = Fraction(1 << (oracle.MAX_CP55_EXACT_INTEGER_BITS + 1), 1)
    with pytest.raises(ValueError, match="bit bound"):
        oracle.ClosedRationalInterval(_ZERO, huge)


def _record_values(record: object) -> dict[str, object]:
    return {
        field.name: getattr(record, field.name)
        for field in fields(record)
        if field.name != "record_sha256"
    }


def _fully_redigested_forge(
    original: object,
    kind: str,
    **changes: object,
) -> object:
    values = _record_values(original)
    values.update(changes)
    provisional = object.__new__(type(original))
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    object.__setattr__(provisional, "record_sha256", "0" * 64)
    digest = oracle._digest(kind, provisional)
    forged = object.__new__(type(original))
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    object.__setattr__(forged, "record_sha256", digest)
    return forged


def _public_record_examples() -> tuple[object, ...]:
    pair = oracle.t28_a0_q_oracle_pair()
    return (
        pair.ideal_rational.target_normalizer_interval,
        pair.score_provider.evaluate((1, 0)),
        pair.score_provider,
        pair.ideal_rational.states[1],
        pair.ideal_rational.precision_stages[-1],
        pair.ideal_rational,
        pair.perturbation,
        pair,
    )


@pytest.mark.parametrize(
    "record",
    _public_record_examples(),
    ids=lambda value: type(value).__name__,
)
def test_every_public_record_is_frozen_and_nonpickleable(record: object) -> None:
    assert is_dataclass(record)
    assert type(record).__dataclass_params__.frozen is True
    with pytest.raises((FrozenInstanceError, TypeError)):
        setattr(record, "invalid_attribute", True)
    with pytest.raises(TypeError, match="non-pickleable"):
        pickle.dumps(record)


def test_every_public_record_class_refuses_subclassing() -> None:
    record_types = tuple(type(value) for value in _public_record_examples())
    assert len(record_types) == len(set(record_types)) == 8
    for index, record_type in enumerate(record_types):
        with pytest.raises(TypeError, match="cannot be subclassed"):
            type("HostileSubclass%d" % index, (record_type,), {})


def test_stale_digests_and_wrong_validator_types_fail_closed() -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    for record in (
        pair.score_provider.evaluate((1, 0)),
        pair.score_provider,
        pair.ideal_rational.states[1],
        pair.ideal_rational.precision_stages[-1],
        pair.ideal_rational,
        pair.perturbation,
    ):
        with pytest.raises(ValueError, match="digest"):
            replace(record, record_sha256="0" * 64)

    object.__setattr__(pair, "record_sha256", "0" * 64)
    with pytest.raises(ValueError, match="digest"):
        oracle.validate_t28_a0_q_oracle_pair(pair)
    with pytest.raises(TypeError, match="wrong exact type"):
        oracle.validate_t28_a0_q_oracle_pair(object())
    with pytest.raises(TypeError, match="wrong exact type"):
        oracle.atomic_q_oracle_pair_record_sha256(object())


def test_fully_redigested_semantic_forgeries_fail_record_validation() -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    evaluation = pair.score_provider.evaluate((1, 0))
    forged_evaluation = _fully_redigested_forge(
        evaluation,
        "score-evaluation",
        exact_score=Fraction(9, 10),
    )
    with pytest.raises(ValueError, match="value differs"):
        forged_evaluation.__post_init__()

    forged_provider = _fully_redigested_forge(
        pair.score_provider,
        "score-table-provider",
        exact_scores=(_SCORES[0], _SCORES[2], _SCORES[1]) + _SCORES[3:],
    )
    with pytest.raises(ValueError, match="contents differ"):
        forged_provider.__post_init__()

    state = pair.ideal_rational.states[1]
    forged_state = _fully_redigested_forge(
        state,
        "state-oracle",
        normalized_base_mass=state.normalized_base_mass + Fraction(1, 1000),
    )
    with pytest.raises(ValueError, match="factorial mass"):
        forged_state.__post_init__()

    stage = pair.ideal_rational.precision_stages[-1]
    altered_exp = (
        oracle.ClosedRationalInterval(Fraction(9, 10), Fraction(11, 10)),
    ) + stage.exp_score_intervals[1:]
    forged_stage = _fully_redigested_forge(
        stage,
        "precision-stage",
        exp_score_intervals=altered_exp,
    )
    with pytest.raises(ValueError, match="exponential powers"):
        forged_stage.__post_init__()

    perturbation = pair.perturbation
    forged_perturbation = _fully_redigested_forge(
        perturbation,
        "parameter-perturbation",
        exact_base_proposal_total_variation=Fraction(1, 10),
    )
    with pytest.raises(ValueError, match="base proposal TV"):
        forged_perturbation.__post_init__()

    forged_pair = _fully_redigested_forge(
        pair,
        "oracle-pair",
        operational_adapter_implemented=True,
    )
    with pytest.raises(ValueError, match="must be false"):
        forged_pair.__post_init__()


def test_full_redigest_repeated_final_precision_stage_forge_fails() -> None:
    layer = oracle.t28_a0_q_oracle_pair().ideal_rational
    final = layer.precision_stages[-1]
    values = _record_values(layer)
    values["precision_stages"] = (final,) * 4
    with pytest.raises(ValueError, match="schedule entry"):
        oracle._make_record(oracle.AtomicQAnalyticLayer, "analytic-layer", **values)


def test_full_redigest_nested_layer_forge_fails_canonical_pair_validation() -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    forged_layer = _fully_redigested_forge(
        pair.ideal_rational,
        "analytic-layer",
        target_normalizer_interval=oracle.ClosedRationalInterval(
            pair.ideal_rational.target_normalizer_interval.lower,
            pair.ideal_rational.target_normalizer_interval.upper + Fraction(1, 10),
        ),
    )
    forged_pair = _fully_redigested_forge(
        pair,
        "oracle-pair",
        ideal_rational=forged_layer,
    )
    with pytest.raises(ValueError, match="final precision stage|normalizer"):
        forged_pair.__post_init__()
    with pytest.raises(ValueError):
        oracle.validate_t28_a0_q_oracle_pair(forged_pair)


def test_public_record_exact_type_preflight_defuses_touch_bombs() -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    with pytest.raises(TypeError, match="exact text"):
        replace(pair.score_provider, fixture_id=_TouchBomb())
    with pytest.raises(TypeError, match="exact tuple"):
        replace(pair.score_provider, exact_scores=_TouchBomb())
    with pytest.raises(TypeError, match="exact text"):
        replace(pair.ideal_rational, parameter_layer=_TouchBomb())
    with pytest.raises(TypeError, match="exact tuple"):
        replace(pair.ideal_rational, precision_schedule=_TouchBomb())
    with pytest.raises(TypeError, match="exact tuple"):
        replace(pair, nonclaims=_TouchBomb())


def test_scope_flags_and_nonclaims_remain_strictly_nonoperational() -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    combined = " ".join(pair.nonclaims).lower()
    for required in (
        "not log of the t28-a0-h factors",
        "stored-binary64",
        "mu_fp",
        "operational sampler law",
        "score-provider facade",
        "initializer kernel",
        "rng",
        "confirmatory",
        "test-28",
        "manuscript claim",
    ):
        assert required in combined

    assert pair.analytic_parameter_layers_distinct is True
    assert pair.count_keyed_runtime_adapter_required is True
    for flag in (
        pair.operational_adapter_implemented,
        pair.kernel_integration_implemented,
        pair.formal_test28_evidence,
        pair.confirmatory_evidence,
        pair.manuscript_claim,
        pair.score_provider.a0_h_logarithm_claim,
        pair.score_provider.facade_integrated,
        pair.score_provider.kernel_integrated,
    ):
        assert flag is False

    for layer in (pair.ideal_rational, pair.binary64_parameter):
        assert layer.exact_score_table_bound is True
        assert layer.base_factorials_reconstructed is True
        assert layer.high_precision_interval_oracle_derived is True
        for flag in (
            layer.operational_mu_fp_identified,
            layer.runtime_source_or_rng_law_verified,
            layer.facade_integrated,
            layer.kernel_integrated,
            layer.operational_categorical_record_compared,
            layer.formal_test28_evidence,
            layer.confirmatory_evidence,
            layer.manuscript_claim,
        ):
            assert flag is False
    assert pair.ideal_rational.stored_binary64_parameter_values_only is False
    assert pair.binary64_parameter.stored_binary64_parameter_values_only is True


def test_record_digests_are_deterministic_lowercase_and_domain_separated() -> None:
    first = oracle.t28_a0_q_oracle_pair()
    second = oracle.t28_a0_q_oracle_pair()
    assert first == second
    assert first is not second
    records = (
        first,
        first.score_provider,
        first.score_provider.evaluate((1, 0)),
        first.ideal_rational,
        first.binary64_parameter,
        first.ideal_rational.states[0],
        first.ideal_rational.precision_stages[-1],
        first.perturbation,
    )
    digests = tuple(record.record_sha256 for record in records)
    assert len(digests) == len(set(digests))
    assert all(
        len(value) == 64 and set(value) <= set("0123456789abcdef") for value in digests
    )
    assert first.record_sha256 == (
        "3f850f54af75009ab597e0a321a8dc01ea4caa61321b135bf9131973f4c6f94e"
    )
    assert first.score_provider.record_sha256 == (
        "6ef113b98cc34f8c32e3631711c933084bb190fa47e9a42db88dee784ed88c13"
    )
    assert first.ideal_rational.record_sha256 == (
        "53b9f2370092a302ab6e3f836298749f2e8cb3b7ac8e3d948890a50f27a13f50"
    )
    assert first.binary64_parameter.record_sha256 == (
        "c5f35ab310992fc0f4c8f887044736d363d1bc828bea7cf8284f9f1f7ac1ac93"
    )
    assert first.perturbation.record_sha256 == (
        "9cbb98f3e352a9f3ae396a662fab1b95a08d74392c8deee0ffe8ac5398d14937"
    )
    assert first.ideal_rational.support_sha256 == (
        "5ad3cb833e507084cb19f762c67d876d10a7e0de5d99fe4d0b70e8f01cd088ff"
    )
    assert first.ideal_rational.score_table_sha256 == (
        "69e348a19c2dd1c7e52963cd7a0682b71c81b935e0d47267ad7585793bb10ba1"
    )
    assert first.ideal_rational.parameter_sha256 == (
        "8ae9ca51e2733cdf1c1068dd5d2b84f293ec27419699e8b2f41e1c18c8e53a36"
    )
    assert first.binary64_parameter.parameter_sha256 == (
        "1ca7d6e90daa7c0705a4f3ad1605bb12015e7a32ac0f6f8ae1db792f9c2d5d05"
    )
    assert oracle.atomic_q_oracle_pair_record_sha256(first) == first.record_sha256


def _run_clean_subprocess(code: str) -> str:
    project_root = Path(oracle.__file__).resolve().parents[3]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = "%s:%s" % (project_root / "src", project_root)
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


def test_module_import_graph_is_stdlib_only_and_oracle_is_standalone() -> None:
    tree = ast.parse(Path(oracle.__file__).read_text(encoding="utf-8"))
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
    assert roots.isdisjoint({"decimal", "heterodiff", "numpy", "scipy", "torch"})


def test_clean_import_and_pair_digest_are_stable_across_processes() -> None:
    code = """
import json
import sys
from heterodiff.evaluation import mixed_initializer_test28_atomic_q_oracle as q
for forbidden in ("numpy", "scipy", "torch"):
    assert forbidden not in sys.modules
for forbidden in (
    "heterodiff.evaluation.mixed_initializer_test28_oracle",
    "heterodiff.evaluation.mixed_initializer_test28_predictions",
    "heterodiff.evaluation.mixed_initializer_test28_factorial_derivation",
):
    assert forbidden not in sys.modules
pair = q.t28_a0_q_oracle_pair()
print(json.dumps({"record": pair.record_sha256}, sort_keys=True, separators=(",", ":")))
"""
    outputs = tuple(_run_clean_subprocess(code) for _ in range(2))
    assert outputs[0] == outputs[1]
    decoded = json.loads(outputs[0])
    pair = oracle.t28_a0_q_oracle_pair()
    assert decoded == {"record": pair.record_sha256}
    assert oracle.atomic_q_oracle_pair_record_sha256(pair) == pair.record_sha256
