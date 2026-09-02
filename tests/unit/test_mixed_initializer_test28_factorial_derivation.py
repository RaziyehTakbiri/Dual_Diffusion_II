"""Independent and hostile tests for the CP54 cap-two factorial oracle."""

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

from heterodiff.evaluation import (
    mixed_initializer_test28_factorial_derivation as derivation,
)


_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_ACTIVITY = Fraction(1, 1)
_RATIONAL_WEIGHTS = (Fraction(2, 5), Fraction(3, 5))
_BINARY64_WEIGHTS = (
    Fraction(3602879701896397, 9007199254740992),
    Fraction(5404319552844595, 9007199254740992),
)
_SUPPORT_LABELS = ("empty", "a", "b", "aa", "ab", "bb")
_M2_SUPPORT_LABELS = (
    "empty",
    "one-type-1d",
    "one-type-2d",
    "two-type-1d",
    "one-each",
    "two-type-2d",
)
_COUNT_VECTORS = ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2))


def _enumerate_cap_support(type_count: int, cap: int) -> tuple[tuple[int, ...], ...]:
    """Independent complete enumeration; it does not consume oracle support."""

    values = tuple(
        counts
        for counts in product(range(cap + 1), repeat=type_count)
        if sum(counts) <= cap
    )
    return tuple(
        sorted(values, key=lambda counts: (sum(counts), tuple(-x for x in counts)))
    )


def _direct_factorial_reference(
    activity: Fraction,
    weights: tuple[Fraction, ...],
    cap: int,
) -> tuple[
    tuple[tuple[int, ...], ...],
    tuple[int, ...],
    tuple[Fraction, ...],
    Fraction,
    tuple[Fraction, ...],
]:
    support = _enumerate_cap_support(len(weights), cap)
    denominators = tuple(
        __import__("math").prod(factorial(value) for value in counts)
        for counts in support
    )
    raw = tuple(
        activity ** sum(counts)
        * __import__("math").prod(
            weight**count for weight, count in zip(weights, counts)
        )
        / denominator
        for counts, denominator in zip(support, denominators)
    )
    normalizer = sum(raw, _ZERO)
    return (
        support,
        denominators,
        raw,
        normalizer,
        tuple(value / normalizer for value in raw),
    )


def _count_multinomial_reference(
    activity: Fraction,
    weights: tuple[Fraction, ...],
    cap: int,
) -> tuple[tuple[Fraction, ...], tuple[Fraction, ...], tuple[Fraction, ...]]:
    """Independent count-law times conditional-multinomial derivation."""

    count_raw = tuple(activity**count / factorial(count) for count in range(cap + 1))
    normalizer = sum(count_raw, _ZERO)
    count_probabilities = tuple(value / normalizer for value in count_raw)
    conditional = []
    joint = []
    for counts in _enumerate_cap_support(len(weights), cap):
        total = sum(counts)
        multinomial = Fraction(factorial(total), 1)
        for weight, multiplicity in zip(weights, counts):
            multinomial *= weight**multiplicity / factorial(multiplicity)
        conditional.append(multinomial)
        joint.append(count_probabilities[total] * multinomial)
    return count_probabilities, tuple(conditional), tuple(joint)


def _builder_arguments(
    fixture_id: str = "T28-A0-H",
    parameter_layer: str = "ideal_rational",
    activity: object = _ACTIVITY,
    type_labels: object = ("a", "b"),
    type_weights: object = _RATIONAL_WEIGHTS,
    event_dimensions: object = (0, 0),
    support_labels: object = _SUPPORT_LABELS,
    count_vectors: object = _COUNT_VECTORS,
    total_cap: object = 2,
) -> dict[str, object]:
    return {
        "fixture_id": fixture_id,
        "parameter_layer": parameter_layer,
        "activity": activity,
        "type_labels": type_labels,
        "type_weights": type_weights,
        "event_dimensions": event_dimensions,
        "support_labels": support_labels,
        "count_vectors": count_vectors,
        "total_cap": total_cap,
    }


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


@pytest.mark.parametrize(
    "builder,fixture_id,type_labels,event_dimensions,support_labels",
    (
        (
            derivation.t28_a0_h_factorial_derivations,
            "T28-A0-H",
            ("a", "b"),
            (0, 0),
            _SUPPORT_LABELS,
        ),
        (
            derivation.t28_m2_q_factorial_derivations,
            "T28-M2-Q",
            ("type-1d", "type-2d"),
            (1, 2),
            _M2_SUPPORT_LABELS,
        ),
    ),
)
def test_both_fixtures_and_parameter_layers_match_two_independent_derivations(
    builder,
    fixture_id,
    type_labels,
    event_dimensions,
    support_labels,
) -> None:
    pair = builder()

    assert pair.fixture_id == fixture_id
    assert pair.ideal_rational.parameter_layer == "ideal_rational"
    assert pair.binary64_parameter.parameter_layer == "binary64_parameter"
    assert pair.common_support_sha256 == pair.ideal_rational.support_sha256
    assert pair.common_support_sha256 == pair.binary64_parameter.support_sha256

    for record, weights in (
        (pair.ideal_rational, _RATIONAL_WEIGHTS),
        (pair.binary64_parameter, _BINARY64_WEIGHTS),
    ):
        (
            support,
            denominators,
            raw,
            normalizer,
            probabilities,
        ) = _direct_factorial_reference(_ACTIVITY, weights, 2)
        count_probabilities, conditional, joint = _count_multinomial_reference(
            _ACTIVITY, weights, 2
        )

        assert support == _COUNT_VECTORS
        assert record.fixture_id == fixture_id
        assert record.activity == _ACTIVITY
        assert record.total_cap == 2
        assert record.type_labels == type_labels
        assert record.type_weights == weights
        assert record.event_dimensions == event_dimensions
        assert record.support_labels == support_labels
        assert record.count_vectors == support
        assert record.raw_normalizer_by_support_sum == normalizer == Fraction(5, 2)
        assert record.raw_normalizer_by_capped_count_series == normalizer
        assert record.base_masses == probabilities == joint
        assert record.count_raw_masses == (_ONE, _ONE, Fraction(1, 2))
        assert (
            record.count_marginal_probabilities
            == count_probabilities
            == (
                Fraction(2, 5),
                Fraction(2, 5),
                Fraction(1, 5),
            )
        )
        assert sum(record.base_masses, _ZERO) == _ONE
        assert sum(record.count_marginal_probabilities, _ZERO) == _ONE

        for index, state in enumerate(record.states):
            assert state.support_index == index
            assert state.support_label == support_labels[index]
            assert state.count_vector == support[index]
            assert state.total_count == sum(support[index])
            assert state.multiplicity_factorial_product == denominators[index]
            assert state.raw_mass_from_product_formula == raw[index]
            assert state.raw_mass_via_count_multinomial == raw[index]
            assert state.conditional_multinomial_probability == conditional[index]
            assert state.normalized_base_mass == probabilities[index]
            assert state.normalized_base_mass_via_count_multinomial == joint[index]

        for count in range(3):
            assert (
                sum(
                    (
                        state.conditional_multinomial_probability
                        for state in record.states
                        if state.total_count == count
                    ),
                    _ZERO,
                )
                == _ONE
            )
            assert (
                sum(
                    (
                        state.normalized_base_mass
                        for state in record.states
                        if state.total_count == count
                    ),
                    _ZERO,
                )
                == record.count_marginal_probabilities[count]
            )


def test_ideal_rational_vector_is_frozen_and_binary64_vector_differs_exactly() -> None:
    expected_rational = (
        Fraction(2, 5),
        Fraction(4, 25),
        Fraction(6, 25),
        Fraction(4, 125),
        Fraction(12, 125),
        Fraction(9, 125),
    )
    t, complement = _BINARY64_WEIGHTS
    expected_binary64 = (
        Fraction(2, 5),
        Fraction(2, 5) * t,
        Fraction(2, 5) * complement,
        Fraction(1, 5) * t * t,
        Fraction(2, 5) * t * complement,
        Fraction(1, 5) * complement * complement,
    )

    assert t + complement == _ONE
    assert t != Fraction(2, 5)
    for pair in (
        derivation.t28_a0_h_factorial_derivations(),
        derivation.t28_m2_q_factorial_derivations(),
    ):
        assert pair.ideal_rational.base_masses == expected_rational
        assert pair.binary64_parameter.base_masses == expected_binary64
        assert pair.ideal_rational.base_masses != pair.binary64_parameter.base_masses
        assert sum(pair.binary64_parameter.base_masses, _ZERO) == _ONE
        assert pair.parameter_records_distinct is True
        assert pair.base_mass_vectors_distinct is True


def test_missing_multiplicity_factorials_and_extra_cardinality_factorial_are_detected() -> None:
    _, denominators, correct_raw, _, correct = _direct_factorial_reference(
        _ACTIVITY, _RATIONAL_WEIGHTS, 2
    )
    support = _enumerate_cap_support(2, 2)

    missing_multiplicity_raw = tuple(
        _ACTIVITY ** sum(counts)
        * __import__("math").prod(
            weight**count for weight, count in zip(_RATIONAL_WEIGHTS, counts)
        )
        for counts in support
    )
    missing_normalizer = sum(missing_multiplicity_raw, _ZERO)
    missing_multiplicity = tuple(
        value / missing_normalizer for value in missing_multiplicity_raw
    )

    extra_cardinality_raw = tuple(
        value / factorial(sum(counts)) for value, counts in zip(correct_raw, support)
    )
    extra_normalizer = sum(extra_cardinality_raw, _ZERO)
    extra_cardinality = tuple(
        value / extra_normalizer for value in extra_cardinality_raw
    )

    assert denominators == (1, 1, 1, 2, 1, 2)
    assert missing_normalizer == Fraction(69, 25)
    assert extra_normalizer == Fraction(9, 4)
    assert missing_multiplicity != correct
    assert extra_cardinality != correct
    assert missing_multiplicity[3] != correct[3]
    assert missing_multiplicity[5] != correct[5]
    assert extra_cardinality[3:] != correct[3:]
    record = derivation.t28_a0_h_factorial_derivations().ideal_rational
    assert record.base_masses == correct
    assert record.multiplicity_factorials_used_exactly_once is True
    assert record.extra_total_count_factorial_used is False


def test_public_builder_has_no_mass_normalizer_target_or_runtime_injection() -> None:
    expected = (
        "fixture_id",
        "parameter_layer",
        "activity",
        "type_labels",
        "type_weights",
        "event_dimensions",
        "support_labels",
        "count_vectors",
        "total_cap",
    )
    signature = inspect.signature(derivation.derive_cap_two_factorial_reference)
    assert tuple(signature.parameters) == expected
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert (
        tuple(inspect.signature(derivation.t28_a0_h_factorial_derivations).parameters)
        == ()
    )
    assert (
        tuple(inspect.signature(derivation.t28_m2_q_factorial_derivations).parameters)
        == ()
    )
    assert not any(
        forbidden in name
        for name in signature.parameters
        for forbidden in ("mass", "normalizer", "probability", "target", "runtime")
    )
    with pytest.raises(TypeError, match="unexpected keyword"):
        derivation.derive_cap_two_factorial_reference(
            **_builder_arguments(),
            base_masses=(Fraction(1, 6),) * 6,
        )


def test_generic_builder_reproduces_both_canonical_zero_argument_builders() -> None:
    a0 = derivation.derive_cap_two_factorial_reference(**_builder_arguments())
    assert a0 == derivation.t28_a0_h_factorial_derivations().ideal_rational

    m2_arguments = _builder_arguments(
        fixture_id="T28-M2-Q",
        type_labels=("type-1d", "type-2d"),
        event_dimensions=(1, 2),
        support_labels=_M2_SUPPORT_LABELS,
    )
    m2 = derivation.derive_cap_two_factorial_reference(**m2_arguments)
    assert m2 == derivation.t28_m2_q_factorial_derivations().ideal_rational

    m2_binary_arguments = dict(m2_arguments)
    m2_binary_arguments.update(
        parameter_layer="binary64_parameter",
        type_weights=_BINARY64_WEIGHTS,
    )
    m2_binary = derivation.derive_cap_two_factorial_reference(**m2_binary_arguments)
    assert m2_binary == derivation.t28_m2_q_factorial_derivations().binary64_parameter


@pytest.mark.parametrize(
    "rewrite,match",
    (
        ({"fixture_id": "T28-UNKNOWN"}, "fixture_id"),
        ({"parameter_layer": "runtime"}, "parameter_layer"),
        ({"activity": Fraction(2, 1)}, "activity"),
        ({"total_cap": 1}, "cap"),
        ({"total_cap": 3}, "between|cap"),
        ({"type_labels": ("b", "a")}, "type_labels"),
        ({"type_weights": (Fraction(1, 2), Fraction(1, 2))}, "type_weights"),
        ({"type_weights": (Fraction(2, 5), Fraction(2, 5))}, "normalize"),
        ({"type_weights": (Fraction(0, 1), Fraction(1, 1))}, "positive"),
        ({"event_dimensions": (0, 1)}, "event_dimensions"),
        ({"support_labels": ("empty", "a", "b", "aa", "ab", "ab")}, "duplicate"),
        ({"support_labels": _SUPPORT_LABELS[:-1]}, "bounded length"),
        ({"support_labels": _SUPPORT_LABELS + ("extra",)}, "bounded length"),
        ({"count_vectors": _COUNT_VECTORS[:-1]}, "bounded length"),
        ({"count_vectors": _COUNT_VECTORS + ((0, 0),)}, "bounded length"),
        ({"count_vectors": _COUNT_VECTORS[:-1] + ((0, 0),)}, "duplicate"),
        ({"count_vectors": _COUNT_VECTORS[:-1] + ((3, 0),)}, "between|above"),
        ({"count_vectors": _COUNT_VECTORS[:-1] + ((-1, 0),)}, "between"),
        ({"count_vectors": _COUNT_VECTORS[:-1] + ((0, 1, 1),)}, "arity"),
        (
            {
                "count_vectors": (
                    _COUNT_VECTORS[0],
                    _COUNT_VECTORS[2],
                    _COUNT_VECTORS[1],
                )
                + _COUNT_VECTORS[3:]
            },
            "noncanonical|order",
        ),
        (
            {
                "support_labels": (
                    _SUPPORT_LABELS[0],
                    _SUPPORT_LABELS[2],
                    _SUPPORT_LABELS[1],
                )
                + _SUPPORT_LABELS[3:]
            },
            "support_labels|order",
        ),
    ),
)
def test_wrong_fixture_cap_weights_support_and_counts_fail_closed(
    rewrite, match
) -> None:
    arguments = _builder_arguments()
    arguments.update(rewrite)
    with pytest.raises((TypeError, ValueError), match=match):
        derivation.derive_cap_two_factorial_reference(**arguments)


@pytest.mark.parametrize(
    "rewrite,match",
    (
        ({"fixture_id": _TouchBomb()}, "fixture_id must be exact text"),
        ({"parameter_layer": _TouchBomb()}, "parameter_layer must be exact text"),
        ({"activity": _TouchBomb()}, "activity must be an exact Fraction"),
        ({"type_labels": _TouchBomb()}, "type_labels must be an exact tuple"),
        ({"type_weights": _TouchBomb()}, "type_weights must be an exact tuple"),
        ({"event_dimensions": _TouchBomb()}, "event_dimensions must be an exact tuple"),
        ({"support_labels": _TouchBomb()}, "support_labels must be an exact tuple"),
        ({"count_vectors": _TouchBomb()}, "count_vectors must be an exact tuple"),
        ({"total_cap": _TouchBomb()}, "total_cap must be an exact"),
        ({"type_labels": (_TouchBomb(), "b")}, "entries must be exact text"),
        (
            {"type_weights": (_TouchBomb(), Fraction(3, 5))},
            "entries must be exact Fractions",
        ),
        ({"event_dimensions": (_TouchBomb(), 0)}, "entries must be exact"),
        (
            {"support_labels": (_TouchBomb(),) + _SUPPORT_LABELS[1:]},
            "entries must be exact text",
        ),
        (
            {"count_vectors": (_TouchBomb(),) + _COUNT_VECTORS[1:]},
            "rows must be exact tuples",
        ),
    ),
)
def test_exact_type_preflight_rejects_touch_bombs_before_using_them(
    rewrite, match
) -> None:
    arguments = _builder_arguments()
    arguments.update(rewrite)
    with pytest.raises(TypeError, match=match):
        derivation.derive_cap_two_factorial_reference(**arguments)


class _TupleAlias(tuple):
    pass


class _TextAlias(str):
    pass


class _IntegerAlias(int):
    pass


class _FractionAlias(Fraction):
    pass


@pytest.mark.parametrize(
    "rewrite,match",
    (
        ({"fixture_id": _TextAlias("T28-A0-H")}, "exact text"),
        ({"parameter_layer": _TextAlias("ideal_rational")}, "exact text"),
        ({"activity": True}, "exact Fraction"),
        ({"activity": 1.0}, "exact Fraction"),
        ({"activity": _FractionAlias(1, 1)}, "exact Fraction"),
        ({"total_cap": True}, "exact non-boolean integer"),
        ({"total_cap": 2.0}, "exact non-boolean integer"),
        ({"total_cap": _IntegerAlias(2)}, "exact non-boolean integer"),
        ({"type_labels": ["a", "b"]}, "exact tuple"),
        ({"type_labels": _TupleAlias(("a", "b"))}, "exact tuple"),
        ({"type_weights": (0.4, 0.6)}, "exact Fractions"),
        ({"type_weights": (True, Fraction(3, 5))}, "exact Fractions"),
        ({"event_dimensions": (False, 0)}, "exact non-boolean integers"),
        ({"support_labels": list(_SUPPORT_LABELS)}, "exact tuple"),
        ({"count_vectors": list(_COUNT_VECTORS)}, "exact tuple"),
        (
            {"count_vectors": _COUNT_VECTORS[:-1] + ((False, 2),)},
            "exact non-boolean integers",
        ),
        (
            {"count_vectors": _COUNT_VECTORS[:-1] + ((0.0, 2),)},
            "exact non-boolean integers",
        ),
    ),
)
def test_bool_float_mutable_and_subclass_aliases_are_rejected(rewrite, match) -> None:
    arguments = _builder_arguments()
    arguments.update(rewrite)
    with pytest.raises(TypeError, match=match):
        derivation.derive_cap_two_factorial_reference(**arguments)


def test_resource_bounds_precede_parameter_equality_and_derivation() -> None:
    bits = derivation.MAX_CP54_TEST28_EXACT_INTEGER_BITS
    huge = Fraction(1 << (bits + 1), 1)
    with pytest.raises(ValueError, match="bit bound"):
        derivation.derive_cap_two_factorial_reference(
            **_builder_arguments(activity=huge)
        )
    with pytest.raises(ValueError, match="bit bound"):
        derivation.derive_cap_two_factorial_reference(
            **_builder_arguments(type_weights=(huge, _ONE - huge))
        )
    with pytest.raises(ValueError, match="bounded length"):
        derivation.derive_cap_two_factorial_reference(
            **_builder_arguments(fixture_id="x" * 129)
        )
    with pytest.raises(ValueError, match="bounded length"):
        derivation.derive_cap_two_factorial_reference(
            **_builder_arguments(support_labels=("x" * 129,) + _SUPPORT_LABELS[1:])
        )
    with pytest.raises(ValueError, match="between"):
        derivation.derive_cap_two_factorial_reference(
            **_builder_arguments(count_vectors=_COUNT_VECTORS[:-1] + ((1 << 5000, 0),))
        )


def _fully_redigested_record_forge(
    original: derivation.CapTwoFactorialDerivation,
    **changes: object,
) -> derivation.CapTwoFactorialDerivation:
    values = {field.name: getattr(original, field.name) for field in fields(original)}
    values.update(changes)
    values["record_sha256"] = "0" * 64
    provisional = object.__new__(derivation.CapTwoFactorialDerivation)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    values["record_sha256"] = derivation._derivation_digest(provisional)
    forged = object.__new__(derivation.CapTwoFactorialDerivation)
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    return forged


def _fully_redigested_pair_forge(
    original: derivation.FixtureFactorialDerivationPair,
    **changes: object,
) -> derivation.FixtureFactorialDerivationPair:
    values = {field.name: getattr(original, field.name) for field in fields(original)}
    values.update(changes)
    values["record_sha256"] = "0" * 64
    provisional = object.__new__(derivation.FixtureFactorialDerivationPair)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    values["record_sha256"] = derivation._pair_digest(provisional)
    forged = object.__new__(derivation.FixtureFactorialDerivationPair)
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    return forged


def test_state_and_record_validation_rejects_semantic_tampering() -> None:
    pair = derivation.t28_a0_h_factorial_derivations()
    record = pair.ideal_rational
    state = record.states[3]

    with pytest.raises(ValueError, match="multiplicity factorial"):
        replace(state, multiplicity_factorial_product=1)
    with pytest.raises(ValueError, match="product-formula raw mass"):
        replace(
            state, raw_mass_from_product_formula=state.raw_mass_from_product_formula * 2
        )
    with pytest.raises(ValueError, match="independent raw-mass routes"):
        replace(
            state,
            raw_mass_via_count_multinomial=state.raw_mass_via_count_multinomial * 2,
        )
    with pytest.raises(ValueError, match="normalized-mass routes"):
        replace(
            state, normalized_base_mass=state.normalized_base_mass + Fraction(1, 1000)
        )

    changed = (record.base_masses[0] + Fraction(1, 1000),) + record.base_masses[1:]
    with pytest.raises(ValueError, match="base_masses differ|normalize"):
        replace(record, base_masses=changed)
    with pytest.raises(ValueError, match="states has the wrong bounded length"):
        replace(record, states=record.states[:-1])
    with pytest.raises(ValueError, match=r"state\[0\] differs"):
        replace(record, states=(record.states[1], record.states[0]) + record.states[2:])


def test_fully_redigested_record_and_pair_forgeries_fail_canonical_validation() -> None:
    pair = derivation.t28_a0_h_factorial_derivations()
    record = pair.ideal_rational
    changed_masses = (record.base_masses[0] + Fraction(1, 1000),) + record.base_masses[
        1:
    ]
    forged_record = _fully_redigested_record_forge(
        record,
        base_masses=changed_masses,
    )
    assert forged_record.record_sha256 == derivation._derivation_digest(forged_record)
    with pytest.raises(ValueError, match="base_masses differ|normalize"):
        derivation.factorial_derivation_record_sha256(forged_record)

    forged_pair = _fully_redigested_pair_forge(pair, manuscript_claim=True)
    assert forged_pair.record_sha256 == derivation._pair_digest(forged_pair)
    with pytest.raises(ValueError, match="forbidden operational or evidence claim"):
        derivation.factorial_derivation_pair_sha256(forged_pair)


def test_digest_tamper_and_wrong_exact_validator_types_fail_closed() -> None:
    record = derivation.t28_m2_q_factorial_derivations().binary64_parameter
    object.__setattr__(record, "record_sha256", "0" * 64)
    with pytest.raises(ValueError, match="record digest differs"):
        derivation.factorial_derivation_record_sha256(record)

    pair = derivation.t28_m2_q_factorial_derivations()
    object.__setattr__(pair, "record_sha256", "0" * 64)
    with pytest.raises(ValueError, match="pair record digest differs"):
        derivation.factorial_derivation_pair_sha256(pair)

    with pytest.raises(TypeError, match="exact CapTwoFactorialDerivation"):
        derivation.factorial_derivation_record_sha256(object())
    with pytest.raises(TypeError, match="exact FixtureFactorialDerivationPair"):
        derivation.factorial_derivation_pair_sha256(object())


def test_fixed_text_fields_reject_touch_bombs_before_equality() -> None:
    pair = derivation.t28_a0_h_factorial_derivations()
    record = pair.ideal_rational
    with pytest.raises(TypeError, match="exact text"):
        replace(record.states[0], support_label=_TouchBomb())
    with pytest.raises(TypeError, match="exact text"):
        replace(record, formula_statement=_TouchBomb())
    with pytest.raises(TypeError, match="exact text"):
        replace(pair, schema_version=_TouchBomb())


def _public_record_examples() -> tuple[object, ...]:
    pair = derivation.t28_m2_q_factorial_derivations()
    return pair.ideal_rational.states[0], pair.ideal_rational, pair


@pytest.mark.parametrize(
    "record",
    _public_record_examples(),
    ids=lambda value: type(value).__name__,
)
def test_every_public_record_is_frozen_and_nonpickleable(record: object) -> None:
    assert is_dataclass(record)
    assert type(record).__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        setattr(record, "invalid_attribute", True)
    with pytest.raises(TypeError, match="non-pickleable"):
        pickle.dumps(record)


def test_every_public_record_class_refuses_subclassing() -> None:
    classes = tuple(type(value) for value in _public_record_examples())
    assert len(classes) == len(set(classes)) == 3
    for index, record_class in enumerate(classes):
        with pytest.raises(TypeError, match="cannot be subclassed"):
            type("HostileSubclass%d" % index, (record_class,), {})


def test_formula_scope_flags_and_nonclaims_keep_base_laws_separate() -> None:
    combined_nonclaims = " ".join(
        derivation.CP54_TEST28_FACTORIAL_DERIVATION_NONCLAIMS
    ).lower()
    for required in (
        "mu_fp",
        "stored-binary64-parameter",
        "floating-point execution",
        "no multiplicative h factor or q-score tilt",
        "source uniformity",
        "formal test 28",
        "manuscript result",
    ):
        assert required in combined_nonclaims
    assert "no additional total-count factorial" in (
        derivation.CP54_TEST28_NO_EXTRA_FACTORIAL_STATEMENT
    )
    assert "conditional(m|n)" in derivation.CP54_TEST28_INDEPENDENT_ROUTE_STATEMENT

    for pair in (
        derivation.t28_a0_h_factorial_derivations(),
        derivation.t28_m2_q_factorial_derivations(),
    ):
        assert pair.analytic_base_measure_only is True
        for flag in (
            pair.operational_reference_sampler_law_claim,
            pair.operational_mu_fp_identified,
            pair.runtime_source_or_rng_law_verified,
            pair.target_tilt_or_score_applied,
            pair.formal_test28_evidence,
            pair.confirmatory_evidence,
            pair.manuscript_claim,
        ):
            assert flag is False
        for record in (pair.ideal_rational, pair.binary64_parameter):
            assert record.complete_support_verified is True
            assert record.type_weights_normalized_exactly is True
            assert record.support_and_count_routes_agree is True
            assert record.analytic_base_measure_only is True
            for flag in (
                record.operational_reference_sampler_law_claim,
                record.operational_mu_fp_identified,
                record.runtime_source_or_rng_law_verified,
                record.target_tilt_or_score_applied,
                record.formal_test28_evidence,
                record.confirmatory_evidence,
                record.manuscript_claim,
            ):
                assert flag is False
        assert pair.ideal_rational.ideal_rational_parameter_reference is True
        assert pair.ideal_rational.stored_binary64_parameter_values_only is False
        assert pair.binary64_parameter.ideal_rational_parameter_reference is False
        assert pair.binary64_parameter.stored_binary64_parameter_values_only is True


def test_event_dimensions_are_metadata_but_fixture_supports_remain_domain_separated() -> None:
    a0 = derivation.t28_a0_h_factorial_derivations()
    m2 = derivation.t28_m2_q_factorial_derivations()
    assert a0.ideal_rational.base_masses == m2.ideal_rational.base_masses
    assert a0.binary64_parameter.base_masses == m2.binary64_parameter.base_masses
    assert a0.common_support_sha256 != m2.common_support_sha256
    assert a0.record_sha256 != m2.record_sha256
    assert a0.ideal_rational.event_dimensions == (0, 0)
    assert m2.ideal_rational.event_dimensions == (1, 2)
    assert "do not enter" in (a0.ideal_rational.event_dimension_scope_statement)


def test_record_hashes_are_frozen_deterministic_and_domain_separated() -> None:
    a0_first = derivation.t28_a0_h_factorial_derivations()
    a0_second = derivation.t28_a0_h_factorial_derivations()
    m2 = derivation.t28_m2_q_factorial_derivations()
    assert a0_first == a0_second
    assert a0_first is not a0_second
    assert a0_first.record_sha256 == (
        "630a4827f188319692c8a6b9f8f25439eaf29ee071880f015304f239a2698b1b"
    )
    assert m2.record_sha256 == (
        "3bc9f9ea1602c88f9700940c71bc8d2a0d82a5080c25d8f2ad8102213bd97bba"
    )
    assert a0_first.ideal_rational.record_sha256 == (
        "f2977a3650840cf43e180598a13b74d3008dab2b1c14cc7dfb36c1adfa7e6f2b"
    )
    assert a0_first.binary64_parameter.record_sha256 == (
        "b13b3171e77208a7a5c73357f7a3916d471e793e78d1364cd1077f742fbc5114"
    )
    assert m2.ideal_rational.record_sha256 == (
        "463b66e0586c59e0262027d27ffb915d5466e316c2ce51aaa5c7ce01b8b94071"
    )
    assert m2.binary64_parameter.record_sha256 == (
        "ae9006633a86c46dbe19e1ac56b5c6837b1a4444f6eeec70be7f7dddc218182d"
    )
    assert derivation.CP54_TEST28_FACTORIAL_FORMULA_SHA256 == (
        "eae971c3f4948cd5a7810ef323498e7ab7513347bfa5936241a5ee01d2b02bbc"
    )
    digests = {
        a0_first.record_sha256,
        a0_first.ideal_rational.record_sha256,
        a0_first.binary64_parameter.record_sha256,
        m2.record_sha256,
        m2.ideal_rational.record_sha256,
        m2.binary64_parameter.record_sha256,
        derivation.CP54_TEST28_FACTORIAL_FORMULA_SHA256,
    }
    assert len(digests) == 7
    assert all(
        len(value) == 64 and set(value) <= set("0123456789abcdef") for value in digests
    )
    assert (
        derivation.factorial_derivation_pair_sha256(a0_first) == a0_first.record_sha256
    )
    assert (
        derivation.factorial_derivation_record_sha256(m2.binary64_parameter)
        == m2.binary64_parameter.record_sha256
    )


def _run_clean_subprocess(code: str) -> str:
    project_root = Path(derivation.__file__).resolve().parents[3]
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


def test_module_import_graph_is_stdlib_only_and_excludes_runtime_oracles() -> None:
    tree = ast.parse(Path(derivation.__file__).read_text(encoding="utf-8"))
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


def test_clean_import_and_record_digests_are_stable_across_processes() -> None:
    code = """
import json
import sys
from heterodiff.evaluation import mixed_initializer_test28_factorial_derivation as d
assert "numpy" not in sys.modules
assert "scipy" not in sys.modules
assert "torch" not in sys.modules
assert "heterodiff.evaluation.mixed_initializer_test28_oracle" not in sys.modules
assert "heterodiff.evaluation.mixed_initializer_test28_predictions" not in sys.modules
a0 = d.t28_a0_h_factorial_derivations()
m2 = d.t28_m2_q_factorial_derivations()
assert "numpy" not in sys.modules and "scipy" not in sys.modules
print(json.dumps({
    "a0": a0.record_sha256,
    "a0_rat": a0.ideal_rational.record_sha256,
    "a0_b64": a0.binary64_parameter.record_sha256,
    "m2": m2.record_sha256,
    "m2_rat": m2.ideal_rational.record_sha256,
    "m2_b64": m2.binary64_parameter.record_sha256,
}, sort_keys=True, separators=(",", ":")))
"""
    outputs = tuple(_run_clean_subprocess(code) for _ in range(2))
    assert outputs[0] == outputs[1]
    decoded = json.loads(outputs[0])
    assert decoded == {
        "a0": "630a4827f188319692c8a6b9f8f25439eaf29ee071880f015304f239a2698b1b",
        "a0_b64": "b13b3171e77208a7a5c73357f7a3916d471e793e78d1364cd1077f742fbc5114",
        "a0_rat": "f2977a3650840cf43e180598a13b74d3008dab2b1c14cc7dfb36c1adfa7e6f2b",
        "m2": "3bc9f9ea1602c88f9700940c71bc8d2a0d82a5080c25d8f2ad8102213bd97bba",
        "m2_b64": "ae9006633a86c46dbe19e1ac56b5c6837b1a4444f6eeec70be7f7dddc218182d",
        "m2_rat": "463b66e0586c59e0262027d27ffb915d5466e316c2ce51aaa5c7ce01b8b94071",
    }
