"""Independent hostile tests for the CP58 bounded/SIR diagnostics."""

from __future__ import annotations

import ast
import builtins
from dataclasses import FrozenInstanceError
from fractions import Fraction
from itertools import combinations, product
import os
from pathlib import Path
import pickle
import subprocess
import sys

import pytest

from heterodiff.evaluation import (
    mixed_initializer_test28_bounded_sir_diagnostics as diagnostics,
)


_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_HALF = Fraction(1, 2)

_PROJECTIONS = {
    "T28-M1-Q": {
        1: (("axis0", (_ONE,)),),
    },
    "T28-M2-Q": {
        0: (("axis0", (_ONE,)),),
        1: (
            ("axis0", (_ONE, _ZERO)),
            ("axis1", (_ZERO, _ONE)),
            ("diag-plus-3-4", (Fraction(3, 5), Fraction(4, 5))),
            ("diag-minus-3-4", (Fraction(3, 5), Fraction(-4, 5))),
        ),
    },
}

_M1_FEATURE_IDS = (
    "count/eq/0",
    "count/eq/1",
    "type/0/occupancy",
    "type/1/occupancy",
    "coordinate/1/axis0/odd",
    "coordinate/1/axis0/even",
)

_M2_FEATURE_IDS = (
    "count/eq/0",
    "count/eq/1",
    "count/eq/2",
    "type/0/occupancy",
    "type/1/occupancy",
    "coordinate/0/axis0/odd",
    "coordinate/0/axis0/even",
    "coordinate/1/axis0/odd",
    "coordinate/1/axis0/even",
    "coordinate/1/axis1/odd",
    "coordinate/1/axis1/even",
    "coordinate/1/diag-plus-3-4/odd",
    "coordinate/1/diag-plus-3-4/even",
    "coordinate/1/diag-minus-3-4/odd",
    "coordinate/1/diag-minus-3-4/even",
    "pair-type/0/0",
    "pair-type/0/1",
    "pair-type/1/1",
    "pair-projection/0/axis0/0/axis0",
    "pair-projection/0/axis0/1/axis0",
    "pair-projection/0/axis0/1/axis1",
    "pair-projection/0/axis0/1/diag-plus-3-4",
    "pair-projection/0/axis0/1/diag-minus-3-4",
    "pair-projection/1/axis0/1/axis0",
    "pair-projection/1/axis0/1/axis1",
    "pair-projection/1/axis0/1/diag-plus-3-4",
    "pair-projection/1/axis0/1/diag-minus-3-4",
    "pair-projection/1/axis1/1/axis1",
    "pair-projection/1/axis1/1/diag-plus-3-4",
    "pair-projection/1/axis1/1/diag-minus-3-4",
    "pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
    "pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
    "pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
)

_M1_LEFT = (
    (),
    ((0, ()),),
    ((1, (1.0,)),),
    ((1, (-1.0,)),),
)
_M1_RIGHT = (
    (),
    ((0, ()),),
    ((1, (0.0,)),),
    ((1, (0.0,)),),
)

_M2_LEFT = (
    (),
    ((0, (0.5,)),),
    ((1, (0.0, 0.5)),),
    ((0, (-0.5,)), (1, (0.5, -0.5))),
)
_M2_RIGHT = (
    (),
    ((0, (0.0,)),),
    ((1, (0.5, 0.0)),),
    ((1, (-0.5, 0.5)), (1, (0.5, 0.5))),
)

_M1_EXPECTED_MEANS = {
    "count/eq/0": (Fraction(1, 4), Fraction(1, 4)),
    "count/eq/1": (Fraction(3, 4), Fraction(3, 4)),
    "type/0/occupancy": (Fraction(1, 4), Fraction(1, 4)),
    "type/1/occupancy": (Fraction(1, 2), Fraction(1, 2)),
    "coordinate/1/axis0/odd": (_ZERO, _ZERO),
    "coordinate/1/axis0/even": (Fraction(1, 2), _ZERO),
}

_M2_EXPECTED_MEANS = dict(
    zip(
        _M2_FEATURE_IDS,
        (
            (Fraction(1, 4), Fraction(1, 4)),
            (Fraction(1, 2), Fraction(1, 2)),
            (Fraction(1, 4), Fraction(1, 4)),
            (Fraction(1, 4), Fraction(1, 8)),
            (Fraction(1, 4), Fraction(3, 8)),
            (_ZERO, _ZERO),
            (Fraction(1, 16), _ZERO),
            (Fraction(1, 16), Fraction(1, 16)),
            (Fraction(1, 32), Fraction(3, 32)),
            (_ZERO, Fraction(1, 8)),
            (Fraction(1, 16), Fraction(1, 16)),
            (Fraction(3, 80), Fraction(11, 80)),
            (Fraction(17, 800), Fraction(59, 800)),
            (Fraction(3, 80), Fraction(-1, 16)),
            (Fraction(13, 160), Fraction(59, 800)),
            (_ZERO, _ZERO),
            (Fraction(1, 4), _ZERO),
            (_ZERO, Fraction(1, 4)),
            (_ZERO, _ZERO),
            (Fraction(-1, 16), _ZERO),
            (Fraction(1, 16), _ZERO),
            (Fraction(1, 80), _ZERO),
            (Fraction(-7, 80), _ZERO),
            (_ZERO, Fraction(-1, 16)),
            (_ZERO, _ZERO),
            (_ZERO, Fraction(-3, 80)),
            (_ZERO, Fraction(-3, 80)),
            (_ZERO, Fraction(1, 16)),
            (_ZERO, Fraction(1, 20)),
            (_ZERO, Fraction(-1, 20)),
            (_ZERO, Fraction(7, 400)),
            (_ZERO, Fraction(-1, 16)),
            (_ZERO, Fraction(7, 400)),
        ),
    )
)

_AESS_STATE_INDICES = (0, 1, 2, 3, 4, 5, 0, 1)
_AESS_NORMALIZED_SLOT_WEIGHTS = (
    Fraction(1, 1031),
    Fraction(1, 1031),
    Fraction(1, 1031),
    Fraction(1, 1031),
    Fraction(1, 1031),
    Fraction(1024, 1031),
    Fraction(1, 1031),
    Fraction(1, 1031),
)
_AESS_EXPECTED_UNIQUE = Fraction(
    1345749996474790269638727,
    1276642570773512871925441,
)
_AESS_EXPECTED_UNIQUE_FRACTION = Fraction(
    1345749996474790269638727,
    10213140566188102975403528,
)
_AESS_EXPECTED_DUPLICATES = Fraction(
    8867390569713312705764801,
    1276642570773512871925441,
)
_AESS_UNIQUE_VARIANCE = Fraction(
    87034990809236068846433935516957609713720879466,
    1629816253511203822084273856281083691558663044481,
)
_AESS_WRONG_COLLAPSED_EXPECTED_UNIQUE = Fraction(
    1345616262302436436017923,
    1276642570773512871925441,
)
_AESS_SLOT_VERSUS_VALUE_EXPECTATION_GAP = Fraction(
    133734172353833620804,
    1276642570773512871925441,
)


class _EqualityBomb:
    def __eq__(self, other):
        del other
        raise AssertionError("hostile equality was touched")

    def __ne__(self, other):
        del other
        raise AssertionError("hostile inequality was touched")


def _odd(value: Fraction) -> Fraction:
    return max(-_ONE, min(_ONE, value))


def _even(value: Fraction) -> Fraction:
    return min(value * value, _ONE)


def _dot(coefficients, coordinates):
    return sum(
        (
            coefficient * Fraction.from_float(coordinate)
            for coefficient, coordinate in zip(coefficients, coordinates)
        ),
        _ZERO,
    )


def _independent_feature_vector(fixture_id, configuration):
    cap = 1 if fixture_id == "T28-M1-Q" else 2
    type_ids = (0, 1)
    values = {}
    for count in range(cap + 1):
        values["count/eq/%d" % count] = Fraction(len(configuration) == count)
    for type_index in type_ids:
        values["type/%d/occupancy" % type_index] = Fraction(
            sum(event[0] == type_index for event in configuration), cap
        )
    for type_index, projections in _PROJECTIONS[fixture_id].items():
        coordinates = tuple(
            event[1] for event in configuration if event[0] == type_index
        )
        for projection_id, coefficients in projections:
            projected = tuple(_dot(coefficients, point) for point in coordinates)
            values["coordinate/%d/%s/odd" % (type_index, projection_id)] = (
                sum((_odd(value) for value in projected), _ZERO) / cap
            )
            values["coordinate/%d/%s/even" % (type_index, projection_id)] = (
                sum((_even(value) for value in projected), _ZERO) / cap
            )
    if cap == 1:
        return values

    for left_type in type_ids:
        for right_type in range(left_type, 2):
            values["pair-type/%d/%d" % (left_type, right_type)] = Fraction(
                sum(
                    tuple(sorted((left[0], right[0]))) == (left_type, right_type)
                    for left, right in combinations(configuration, 2)
                )
            )
    for left_type in type_ids:
        for left_index, (left_id, left_projection) in enumerate(
            _PROJECTIONS[fixture_id][left_type]
        ):
            for right_type in range(left_type, 2):
                for right_index, (right_id, right_projection) in enumerate(
                    _PROJECTIONS[fixture_id][right_type]
                ):
                    if left_type == right_type and left_index > right_index:
                        continue
                    total = _ZERO
                    for left, right in combinations(configuration, 2):
                        if tuple(sorted((left[0], right[0]))) != (
                            left_type,
                            right_type,
                        ):
                            continue
                        if left_type != right_type:
                            left_event = left if left[0] == left_type else right
                            right_event = right if left[0] == left_type else left
                            total += _odd(_dot(left_projection, left_event[1])) * _odd(
                                _dot(right_projection, right_event[1])
                            )
                        elif left_id == right_id:
                            total += _odd(_dot(left_projection, left[1])) * _odd(
                                _dot(right_projection, right[1])
                            )
                        else:
                            total += (
                                _odd(_dot(left_projection, left[1]))
                                * _odd(_dot(right_projection, right[1]))
                                + _odd(_dot(right_projection, left[1]))
                                * _odd(_dot(left_projection, right[1]))
                            ) / 2
                    values[
                        "pair-projection/%d/%s/%d/%s"
                        % (left_type, left_id, right_type, right_id)
                    ] = total
    return values


def _independent_means(fixture_id, configurations):
    vectors = tuple(
        _independent_feature_vector(fixture_id, configuration)
        for configuration in configurations
    )
    return {
        feature_id: sum((vector[feature_id] for vector in vectors), _ZERO)
        / len(vectors)
        for feature_id in vectors[0]
    }


def _independent_expected_occupancy(weights, draws):
    expected = sum((1 - (1 - weight) ** draws for weight in weights), _ZERO)
    variance = sum(
        ((1 - (1 - weight) ** draws) * (1 - weight) ** draws for weight in weights),
        _ZERO,
    )
    for left in range(len(weights)):
        for right in range(left + 1, len(weights)):
            variance += 2 * (
                (1 - weights[left] - weights[right]) ** draws
                - (1 - weights[left]) ** draws * (1 - weights[right]) ** draws
            )
    return expected, variance


def _forge(instance, **changes):
    forged = object.__new__(type(instance))
    for name in instance.__annotations__:
        object.__setattr__(
            forged,
            name,
            changes[name] if name in changes else getattr(instance, name),
        )
    return forged


def _redigest(instance, domain):
    zeroed = _forge(instance, record_sha256="0" * 64)
    return _forge(
        zeroed,
        record_sha256=diagnostics._digest(domain, zeroed),
    )


@pytest.mark.parametrize(
    ("fixture_id", "expected_ids", "expected_cap", "expected_dimensions"),
    (
        ("T28-M1-Q", _M1_FEATURE_IDS, 1, (0, 1)),
        ("T28-M2-Q", _M2_FEATURE_IDS, 2, (1, 2)),
    ),
)
def test_registry_exact_feature_order_bounds_and_sign_closure(
    fixture_id, expected_ids, expected_cap, expected_dimensions
) -> None:
    registry = diagnostics.cp58_feature_registry(fixture_id)

    assert registry.fixture_id == fixture_id
    assert registry.count_cap == expected_cap
    assert registry.event_dimensions == expected_dimensions
    assert tuple(feature.feature_id for feature in registry.features) == expected_ids
    assert len(registry.features) <= diagnostics.CP58_TEST28_MAX_FEATURES
    assert registry.odd_transform_formula == (
        "odd_sat(z)=max(-1,min(1,z)) over exact Q"
    )
    assert registry.even_transform_formula == ("even_sat(z)=min(1,z*z) over exact Q")
    assert "max over sign" in registry.ipm_formula
    assert "lexicographically-smallest" in registry.witness_tie_rule
    assert registry.source_law_verified is False
    assert registry.target_law_verified is False
    assert all(feature.sign_closed is True for feature in registry.features)
    assert all(
        -_ONE <= feature.lower_bound <= feature.upper_bound <= _ONE
        for feature in registry.features
    )
    assert diagnostics.validate_cp58_feature_registry(registry) is registry


def test_exact_projection_registry_and_feature_family_coverage() -> None:
    m1 = diagnostics.cp58_feature_registry("T28-M1-Q")
    m2 = diagnostics.cp58_feature_registry("T28-M2-Q")
    assert tuple(
        (item.type_index, item.projection_id, item.coefficients)
        for item in m1.projections
    ) == (
        (1, "axis0", (_ONE,)),
    )
    assert tuple(
        (item.type_index, item.projection_id, item.coefficients)
        for item in m2.projections
    ) == (
        (0, "axis0", (_ONE,)),
        (1, "axis0", (_ONE, _ZERO)),
        (1, "axis1", (_ZERO, _ONE)),
        (1, "diag-plus-3-4", (Fraction(3, 5), Fraction(4, 5))),
        (1, "diag-minus-3-4", (Fraction(3, 5), Fraction(-4, 5))),
    )
    assert tuple(feature.family for feature in m1.features).count("count-one-hot") == 2
    assert tuple(feature.family for feature in m1.features).count("type-occupancy") == 2
    assert tuple(feature.family for feature in m1.features).count("coordinate-odd") == 1
    assert (
        tuple(feature.family for feature in m1.features).count("coordinate-even") == 1
    )
    families = tuple(feature.family for feature in m2.features)
    assert families.count("count-one-hot") == 3
    assert families.count("type-occupancy") == 2
    assert families.count("coordinate-odd") == 5
    assert families.count("coordinate-even") == 5
    assert families.count("pair-type-occupancy") == 3
    assert families.count("pair-projected-product") == 15


@pytest.mark.parametrize(
    ("fixture_id", "samples", "expected_ids"),
    (
        ("T28-M1-Q", _M1_LEFT + _M1_RIGHT, _M1_FEATURE_IDS),
        ("T28-M2-Q", _M2_LEFT + _M2_RIGHT, _M2_FEATURE_IDS),
    ),
)
def test_every_frozen_feature_matches_independent_exact_evaluation(
    fixture_id, samples, expected_ids
) -> None:
    for configuration in samples:
        expected = _independent_feature_vector(fixture_id, configuration)
        observed = diagnostics.cp58_bounded_feature_vector(fixture_id, configuration)
        assert tuple(expected) == expected_ids
        assert observed == tuple(expected[feature_id] for feature_id in expected_ids)
        assert all(type(value) is Fraction for value in observed)
        assert all(-_ONE <= value <= _ONE for value in observed)


@pytest.mark.parametrize(
    ("fixture_id", "left", "right", "expected_means", "ipm", "witness"),
    (
        (
            "T28-M1-Q",
            _M1_LEFT,
            _M1_RIGHT,
            _M1_EXPECTED_MEANS,
            Fraction(1, 2),
            ("coordinate/1/axis0/even", 1),
        ),
        (
            "T28-M2-Q",
            _M2_LEFT,
            _M2_RIGHT,
            _M2_EXPECTED_MEANS,
            Fraction(1, 4),
            ("pair-type/0/1", 1),
        ),
    ),
)
def test_calibration_ipm_means_discrepancies_and_witness_are_independent(
    fixture_id, left, right, expected_means, ipm, witness
) -> None:
    independent_left = _independent_means(fixture_id, left)
    independent_right = _independent_means(fixture_id, right)
    assert {
        feature_id: (independent_left[feature_id], independent_right[feature_id])
        for feature_id in independent_left
    } == expected_means

    result = diagnostics.cp58_bounded_feature_ipm(fixture_id, left, right)
    assert result.sample_a_feature_means == tuple(independent_left.values())
    assert result.sample_b_feature_means == tuple(independent_right.values())
    expected_differences = tuple(
        independent_left[name] - independent_right[name] for name in independent_left
    )
    assert result.signed_base_discrepancies == expected_differences
    assert result.absolute_base_discrepancies == tuple(
        abs(value) for value in expected_differences
    )
    assert result.ipm == ipm
    assert (result.witness_feature_id, result.witness_sign) == witness
    assert result.input_is_predeclared_calibration is False
    assert result.input_sample_digest_provenance_verified is False
    assert diagnostics.validate_cp58_bounded_feature_ipm(result) is result


def test_ipm_swap_sign_and_all_zero_lexicographic_tie_rule() -> None:
    forward = diagnostics.cp58_bounded_feature_ipm("T28-M2-Q", _M2_LEFT, _M2_RIGHT)
    reverse = diagnostics.cp58_bounded_feature_ipm("T28-M2-Q", _M2_RIGHT, _M2_LEFT)
    assert reverse.ipm == forward.ipm == Fraction(1, 4)
    assert reverse.signed_base_discrepancies == tuple(
        -value for value in forward.signed_base_discrepancies
    )
    assert (reverse.witness_feature_id, reverse.witness_sign) == (
        "pair-type/0/1",
        -1,
    )

    zero = diagnostics.cp58_bounded_feature_ipm("T28-M1-Q", _M1_LEFT, _M1_LEFT)
    assert zero.ipm == 0
    assert zero.witness_feature_id == min(_M1_FEATURE_IDS)
    assert zero.witness_sign == 1


def test_exact_saturation_at_boundaries_and_all_finite_binary64_magnitudes() -> None:
    positions = {name: index for index, name in enumerate(_M1_FEATURE_IDS)}
    for coordinate, odd, even in (
        (-2.0, Fraction(-1), Fraction(1)),
        (-1.0, Fraction(-1), Fraction(1)),
        (1.0, Fraction(1), Fraction(1)),
        (2.0, Fraction(1), Fraction(1)),
        (sys.float_info.max, Fraction(1), Fraction(1)),
        (-sys.float_info.max, Fraction(-1), Fraction(1)),
    ):
        vector = diagnostics.cp58_bounded_feature_vector(
            "T28-M1-Q", ((1, (coordinate,)),)
        )
        assert vector[positions["coordinate/1/axis0/odd"]] == odd
        assert vector[positions["coordinate/1/axis0/even"]] == even

    smallest = float.fromhex("0x0.0000000000001p-1022")
    vector = diagnostics.cp58_bounded_feature_vector("T28-M1-Q", ((1, (smallest,)),))
    exact = Fraction.from_float(smallest)
    assert vector[positions["coordinate/1/axis0/odd"]] == exact
    assert vector[positions["coordinate/1/axis0/even"]] == exact * exact


@pytest.mark.parametrize(
    ("fixture_id", "configuration", "exception", "message"),
    (
        ("T28-M1-Q", [], TypeError, "exact tuple"),
        ("T28-M1-Q", ([0, ()],), TypeError, "exact tuple"),
        ("T28-M1-Q", ((True, ()),), TypeError, "exact integer"),
        ("T28-M1-Q", ((2, ()),), ValueError, "frozen bound"),
        ("T28-M1-Q", ((0, []),), TypeError, "exact tuple"),
        ("T28-M1-Q", ((0, (0.0,)),), ValueError, "bounded length"),
        ("T28-M1-Q", ((1, ()),), ValueError, "bounded length"),
        ("T28-M1-Q", ((1, (1,)),), TypeError, "built-in float"),
        ("T28-M1-Q", ((1, (float("nan"),)),), ValueError, "finite"),
        ("T28-M1-Q", ((1, (float("inf"),)),), ValueError, "finite"),
        ("T28-M1-Q", ((1, (-0.0,)),), ValueError, "positive zero"),
        (
            "T28-M2-Q",
            ((1, (0.0, 0.0)), (0, (0.0,))),
            ValueError,
            "canonical nondecreasing order",
        ),
        (
            "T28-M2-Q",
            ((1, (1.0, 0.0)), (1, (-1.0, 0.0))),
            ValueError,
            "canonical nondecreasing order",
        ),
        (
            "T28-M2-Q",
            ((0, (0.0,)), (0, (0.0,)), (0, (0.0,))),
            ValueError,
            "bounded length",
        ),
    ),
)
def test_noncanonical_configuration_inputs_fail_closed(
    fixture_id, configuration, exception, message
) -> None:
    with pytest.raises(exception, match=message):
        diagnostics.cp58_bounded_feature_vector(fixture_id, configuration)


def test_hostile_fixture_types_fail_before_equality_or_membership() -> None:
    hostile = _EqualityBomb()
    for function, args in (
        (diagnostics.cp58_feature_registry, (hostile,)),
        (diagnostics.cp58_bounded_feature_vector, (hostile, ())),
        (
            diagnostics.cp58_proposal_configuration_uniqueness,
            (hostile, "cloud", ((0, 0),)),
        ),
    ):
        with pytest.raises(TypeError, match="exact text"):
            function(*args)


def test_sample_shape_size_and_public_calibration_claim_fail_closed() -> None:
    with pytest.raises(ValueError, match="bounded length"):
        diagnostics.cp58_bounded_feature_ipm("T28-M1-Q", (), ((),))
    with pytest.raises(TypeError, match="exact tuple"):
        diagnostics.cp58_bounded_feature_ipm("T28-M1-Q", [()], ((),))
    oversized = ((),) * (diagnostics.CP58_TEST28_MAX_SAMPLE_SIZE + 1)
    with pytest.raises(ValueError, match="bounded length"):
        diagnostics.cp58_bounded_feature_ipm("T28-M1-Q", oversized, ((),))
    with pytest.raises(TypeError):
        diagnostics.cp58_bounded_feature_ipm(
            "T28-M1-Q",
            _M1_LEFT,
            _M1_RIGHT,
            input_is_predeclared_calibration=True,
        )


def test_ipm_validator_rejects_bool_witness_and_exact_arithmetic_overflow() -> None:
    result = diagnostics.cp58_bounded_feature_ipm("T28-M1-Q", _M1_LEFT, _M1_RIGHT)
    with pytest.raises(TypeError, match="exact integer"):
        diagnostics.validate_cp58_bounded_feature_ipm(_forge(result, witness_sign=True))
    huge = Fraction(1, 1 << (diagnostics.CP58_TEST28_MAX_FRACTION_BITS + 1))
    hostile_means = (huge,) + result.sample_a_feature_means[1:]
    with pytest.raises(ValueError, match="exact arithmetic bit bound"):
        diagnostics.validate_cp58_bounded_feature_ipm(
            _forge(result, sample_a_feature_means=hostile_means)
        )


def test_registry_rejects_redigested_feature_semantic_forgery() -> None:
    registry = diagnostics.cp58_feature_registry("T28-M2-Q")
    original = registry.features[0]
    forged_feature = _redigest(
        _forge(original, formula_id="hostile-near-match-formula"),
        b"cp58-feature-v1\x00",
    )
    forged_registry = _redigest(
        _forge(registry, features=(forged_feature,) + registry.features[1:]),
        b"cp58-feature-registry-v1\x00",
    )
    with pytest.raises(ValueError, match="frozen feature definitions"):
        diagnostics.validate_cp58_feature_registry(forged_registry)


def test_registry_rejects_wrong_feature_container_and_child_digest_reuse() -> None:
    registry = diagnostics.cp58_feature_registry("T28-M1-Q")
    with pytest.raises(TypeError, match="exact tuple|unsupported CP58 canonical value"):
        diagnostics.validate_cp58_feature_registry(
            _forge(registry, features=list(registry.features))
        )
    forged_child = _forge(
        registry.features[0],
        family="coordinate-even",
    )
    forged_registry = _redigest(
        _forge(registry, features=(forged_child,) + registry.features[1:]),
        b"cp58-feature-registry-v1\x00",
    )
    with pytest.raises(ValueError, match="feature-definition digest"):
        diagnostics.validate_cp58_feature_registry(forged_registry)


def test_proposal_value_uniqueness_is_separate_from_particle_slots() -> None:
    result = diagnostics.cp58_proposal_configuration_uniqueness(
        "T28-AESS",
        "T28-AESS-predeclared-j8-cloud",
        (
            (0, 0),
            (1, 0),
            (0, 1),
            (2, 0),
            (1, 1),
            (0, 2),
            (0, 0),
            (1, 0),
        ),
    )
    assert result.particle_slot_count == 8
    assert result.canonical_configurations_or_state_vectors == (
        (0, 0),
        (1, 0),
        (0, 1),
        (2, 0),
        (1, 1),
        (0, 2),
        (0, 0),
        (1, 0),
    )
    assert result.value_multiplicities == (2, 2, 1, 1, 1, 1)
    assert result.unique_configuration_value_count == 6
    assert result.repeated_value_excess == 2
    assert result.maximum_value_multiplicity == 2
    assert result.configuration_value_uniqueness_is_ancestor_occupancy is False
    assert result.particle_slots_remain_distinct_when_values_equal is True
    assert result.supplied_configuration_values_only is True
    assert result.production_behavior_observed is False
    assert diagnostics.validate_cp58_proposal_configuration_uniqueness(result) is result


def test_generic_proposal_value_uniqueness_uses_canonical_values_not_ancestry() -> None:
    configurations = (
        (),
        (),
        ((0, ()),),
        ((1, (0.5,)),),
        ((1, (0.5,)),),
    )
    result = diagnostics.cp58_proposal_configuration_uniqueness(
        "T28-M1-Q", "one-supplied-cloud", configurations
    )
    assert result.particle_slot_count == 5
    assert result.unique_configuration_value_count == 3
    assert result.value_multiplicities == (2, 1, 2)
    assert result.repeated_value_excess == 2
    assert result.maximum_value_multiplicity == 2
    assert result.configuration_value_uniqueness_is_ancestor_occupancy is False


@pytest.mark.parametrize(
    ("states", "exception", "message"),
    (
        (((0, 0),), ValueError, "sequence differs"),
        (
            (
                (0, 0),
                (1, 0),
                (0, 1),
                (2, 0),
                (1, 1),
                (0, 2),
                (0, 1),
                (1, 0),
            ),
            ValueError,
            "sequence differs",
        ),
        (
            (
                (0, 0),
                (-1, 0),
                (0, 1),
                (2, 0),
                (1, 1),
                (0, 2),
                (0, 0),
                (1, 0),
            ),
            ValueError,
            "frozen bound",
        ),
        (
            (
                (0, 0),
                (True, 0),
                (0, 1),
                (2, 0),
                (1, 1),
                (0, 2),
                (0, 0),
                (1, 0),
            ),
            TypeError,
            "exact integer",
        ),
        (
            (
                (0, 0),
                (1, 0),
                (0, 1),
                (2, 1),
                (1, 1),
                (0, 2),
                (0, 0),
                (1, 0),
            ),
            ValueError,
            "exceeds cap two",
        ),
    ),
)
def test_aess_proposal_value_fixture_rejects_malformed_or_alternate_states(
    states, exception, message
) -> None:
    with pytest.raises(exception, match=message):
        diagnostics.cp58_proposal_configuration_uniqueness("T28-AESS", "cloud", states)


def test_same_cloud_ancestor_occupancy_exact_arithmetic_and_one_draw_contract() -> None:
    one = diagnostics.cp58_same_cloud_ancestor_occupancy((("one-cloud", 5),), 8)
    assert one.selection_count == 1
    assert one.selected_slot_indices == (5,)
    assert one.slot_multiplicities == (0, 0, 0, 0, 0, 1, 0, 0)
    assert one.unique_selected_ancestor_count == 1
    assert one.duplicate_selection_count == 0
    assert one.selected_unique_fraction == 1
    assert one.particle_slot_occupancy_fraction == Fraction(1, 8)
    assert one.maximum_slot_multiplicity == 1
    assert one.single_kernel_selection_contract is True

    observations = tuple(("same-cloud", index) for index in (0, 0, 2, 5, 5, 5, 7, 7))
    many = diagnostics.cp58_same_cloud_ancestor_occupancy(observations, 8)
    assert many.selection_count == 8
    assert many.slot_multiplicities == (2, 0, 1, 0, 0, 3, 0, 2)
    assert many.unique_selected_ancestor_count == 4
    assert many.duplicate_selection_count == 4
    assert many.selected_unique_fraction == Fraction(1, 2)
    assert many.particle_slot_occupancy_fraction == Fraction(1, 2)
    assert many.maximum_slot_multiplicity == 3
    assert many.single_kernel_selection_contract is False
    for record in (one, many):
        assert record.all_supplied_cloud_labels_equal is True
        assert record.physical_same_cloud_provenance_verified is False
        assert record.cross_cloud_pooling_permitted is False
        assert record.supplied_selection_positions_only is True
        assert record.production_boundary_verified is False
        assert record.production_behavior_observed is False
        assert diagnostics.validate_cp58_same_cloud_ancestor_occupancy(record) is record


@pytest.mark.parametrize(
    ("observations", "slots", "exception", "message"),
    (
        ((("cloud-a", 0), ("cloud-b", 0)), 8, ValueError, "cross-cloud"),
        ((["cloud", 0],), 8, TypeError, "exact tuple"),
        ((("cloud", True),), 8, TypeError, "exact integer"),
        ((("cloud", -1),), 8, ValueError, "frozen bound"),
        ((("cloud", 8),), 8, ValueError, "frozen bound"),
        ((("cloud", 0),), True, TypeError, "exact integer"),
        ((("cloud", 0),), 0, ValueError, "frozen bound"),
        ((("cloud", 0),), 513, ValueError, "frozen bound"),
        ((), 8, ValueError, "bounded length"),
    ),
)
def test_same_cloud_occupancy_rejects_pooling_types_bounds_and_empty_input(
    observations, slots, exception, message
) -> None:
    with pytest.raises(exception, match=message):
        diagnostics.cp58_same_cloud_ancestor_occupancy(observations, slots)


def test_expected_occupancy_formula_matches_bruteforce_small_law() -> None:
    weights = (Fraction(1, 3), Fraction(2, 3))
    draws = 3
    expected = second = _ZERO
    for outcome in product(range(2), repeat=draws):
        probability = _ONE
        for index in outcome:
            probability *= weights[index]
        unique = len(set(outcome))
        expected += probability * unique
        second += probability * unique * unique
    brute_variance = second - expected * expected
    formula_expected, formula_variance = _independent_expected_occupancy(weights, draws)
    assert expected == formula_expected == Fraction(5, 3)
    assert brute_variance == formula_variance == Fraction(2, 9)
    one_draw_expected, one_draw_variance = _independent_expected_occupancy(
        _AESS_NORMALIZED_SLOT_WEIGHTS, 1
    )
    assert one_draw_expected == 1
    assert one_draw_variance == 0


def test_aess_expected_slot_occupancy_exact_values_and_no_draw_scope() -> None:
    record = diagnostics.cp58_aess_expected_ancestor_occupancy()
    independently_expected, independently_variance = _independent_expected_occupancy(
        _AESS_NORMALIZED_SLOT_WEIGHTS, 8
    )
    assert independently_expected == _AESS_EXPECTED_UNIQUE
    assert independently_variance == _AESS_UNIQUE_VARIANCE
    assert record.exact_slot_weights == _AESS_NORMALIZED_SLOT_WEIGHTS
    assert record.slot_inclusion_probabilities == tuple(
        1 - (1 - weight) ** 8 for weight in _AESS_NORMALIZED_SLOT_WEIGHTS
    )
    assert (
        record.conditional_expected_unique_particle_slot_occupancy
        == _AESS_EXPECTED_UNIQUE
    )
    assert (
        record.conditional_expected_particle_slot_occupancy_fraction
        == _AESS_EXPECTED_UNIQUE_FRACTION
    )
    assert record.conditional_particle_slot_occupancy_variance == _AESS_UNIQUE_VARIANCE
    assert record.conditional_expected_duplicate_selections == _AESS_EXPECTED_DUPLICATES
    assert record.conditional_expected_duplicate_selection_fraction == (
        _AESS_EXPECTED_DUPLICATES / 8
    )
    assert record.equal_configuration_values_collapsed is False
    assert record.particle_slots_not_configuration_values is True
    assert record.extra_resampling_draws_executed == 0
    assert record.analytic_report_only is True
    assert record.production_behavior_observed is False
    assert record.categorical_source_law_verified is False
    assert diagnostics.validate_cp58_aess_expected_ancestor_occupancy(record) is record


def test_aess_equal_values_must_not_be_collapsed_before_slot_occupancy() -> None:
    collapsed = (
        Fraction(2, 1031),
        Fraction(2, 1031),
        Fraction(1, 1031),
        Fraction(1, 1031),
        Fraction(1, 1031),
        Fraction(1024, 1031),
    )
    wrong_expected, _ = _independent_expected_occupancy(collapsed, 8)
    assert wrong_expected == _AESS_WRONG_COLLAPSED_EXPECTED_UNIQUE
    assert _AESS_EXPECTED_UNIQUE - wrong_expected == (
        _AESS_SLOT_VERSUS_VALUE_EXPECTATION_GAP
    )
    record = diagnostics.cp58_aess_expected_ancestor_occupancy()
    assert record.conditional_expected_unique_particle_slot_occupancy != (
        wrong_expected
    )


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        ("schema_version", "hostile-schema", "arithmetic differs"),
        ("expectation_formula_id", "near-match", "formula identifier"),
        ("variance_formula_id", "near-match", "formula identifier"),
        ("equal_configuration_values_collapsed", True, "scope differs"),
        ("particle_slots_not_configuration_values", False, "scope differs"),
        ("extra_resampling_draws_executed", True, "scope differs"),
        ("analytic_report_only", False, "scope differs"),
        ("production_behavior_observed", True, "scope differs"),
        ("categorical_source_law_verified", True, "scope differs"),
    ),
)
def test_aess_validator_rejects_redigested_schema_formula_and_scope_tamper(
    field, replacement, message
) -> None:
    original = diagnostics.cp58_aess_expected_ancestor_occupancy()
    forged = _redigest(
        _forge(original, **{field: replacement}),
        b"cp58-aess-expected-ancestor-occupancy-v1\x00",
    )
    with pytest.raises((TypeError, ValueError), match=message):
        diagnostics.validate_cp58_aess_expected_ancestor_occupancy(forged)


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        ("particle_slot_count", True, "exact integer"),
        ("value_multiplicities", (2.0, 1, 2), "exact integer"),
        ("unique_configuration_value_count", 3.0, "exact integer"),
        ("repeated_value_excess", False, "exact integer"),
        ("maximum_value_multiplicity", 2.0, "exact integer"),
    ),
)
def test_proposal_uniqueness_rejects_redigested_bool_and_float_counts(
    field, replacement, message
) -> None:
    original = diagnostics.cp58_proposal_configuration_uniqueness(
        "T28-M1-Q",
        "cloud",
        ((), (), ((0, ()),), ((1, (0.5,)),), ((1, (0.5,)),)),
    )
    forged = _redigest(
        _forge(original, **{field: replacement}),
        b"cp58-proposal-configuration-uniqueness-v1\x00",
    )
    with pytest.raises(TypeError, match=message):
        diagnostics.validate_cp58_proposal_configuration_uniqueness(forged)


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        ("selection_count", True, "exact integer"),
        (
            "slot_multiplicities",
            (True, 0, 1, 0, 0, 3, 0, 2),
            "exact integer",
        ),
        ("unique_selected_ancestor_count", 4.0, "exact integer"),
        ("duplicate_selection_count", 4.0, "exact integer"),
        ("maximum_slot_multiplicity", 3.0, "exact integer"),
        ("selected_unique_fraction", 0.5, "exact Fraction"),
        ("particle_slot_occupancy_fraction", 0.5, "exact Fraction"),
    ),
)
def test_same_cloud_rejects_redigested_bool_float_and_nonfraction_fields(
    field, replacement, message
) -> None:
    original = diagnostics.cp58_same_cloud_ancestor_occupancy(
        tuple(("cloud", index) for index in (0, 0, 2, 5, 5, 5, 7, 7)),
        8,
    )
    forged = _redigest(
        _forge(original, **{field: replacement}),
        b"cp58-same-cloud-ancestor-occupancy-v1\x00",
    )
    with pytest.raises(TypeError, match=message):
        diagnostics.validate_cp58_same_cloud_ancestor_occupancy(forged)


def test_feature_normalizers_use_frozen_cap_not_observed_event_count() -> None:
    feature_ids = _M2_FEATURE_IDS
    positions = {name: index for index, name in enumerate(feature_ids)}
    vector = diagnostics.cp58_bounded_feature_vector("T28-M2-Q", ((0, (1.0,)),))
    assert vector[positions["type/0/occupancy"]] == Fraction(1, 2)
    assert vector[positions["coordinate/0/axis0/odd"]] == Fraction(1, 2)
    assert vector[positions["coordinate/0/axis0/even"]] == Fraction(1, 2)
    assert vector[positions["pair-type/0/0"]] == 0
    assert all(
        vector[positions[name]] == 0
        for name in feature_ids
        if name.startswith("pair-projection/")
    )
    registry = diagnostics.cp58_feature_registry("T28-M2-Q")
    for feature in registry.features:
        if feature.family in (
            "type-occupancy",
            "coordinate-odd",
            "coordinate-even",
        ):
            assert feature.normalization_denominator == 2
        elif feature.family.startswith("pair-"):
            assert feature.normalization_denominator == 1


def test_same_type_cross_projection_pair_is_event_order_symmetric() -> None:
    registry = diagnostics.cp58_feature_registry("T28-M2-Q")
    feature = next(
        feature
        for feature in registry.features
        if feature.feature_id == "pair-projection/1/axis0/1/axis1"
    )
    canonical = diagnostics._canonical_configuration(
        registry,
        ((1, (-1.0, 0.5)), (1, (0.25, 1.0))),
    )
    forward = diagnostics._feature_value(registry, canonical, feature)
    reverse = diagnostics._feature_value(registry, tuple(reversed(canonical)), feature)
    direct_only = _odd(Fraction(-1)) * _odd(Fraction(1))
    reverse_only = _odd(Fraction(1, 2)) * _odd(Fraction(1, 4))
    assert direct_only != reverse_only
    assert forward == reverse == (direct_only + reverse_only) / 2
    assert forward == Fraction(-7, 16)


def test_sample_permutation_preserves_ipm_but_changes_order_binding_digest() -> None:
    original = diagnostics.cp58_bounded_feature_ipm("T28-M2-Q", _M2_LEFT, _M2_RIGHT)
    permuted = diagnostics.cp58_bounded_feature_ipm(
        "T28-M2-Q", tuple(reversed(_M2_LEFT)), _M2_RIGHT
    )
    assert permuted.sample_a_feature_means == original.sample_a_feature_means
    assert permuted.sample_b_feature_means == original.sample_b_feature_means
    assert permuted.signed_base_discrepancies == (original.signed_base_discrepancies)
    assert permuted.ipm == original.ipm
    assert permuted.witness_feature_id == original.witness_feature_id
    assert permuted.witness_sign == original.witness_sign
    assert permuted.sample_a_sha256 != original.sample_a_sha256
    assert permuted.record_sha256 != original.record_sha256


def test_bundle_exact_nested_roots_calibrations_and_nonclaims() -> None:
    bundle = diagnostics.cp58_diagnostic_bundle()
    assert diagnostics.validate_cp58_diagnostic_bundle(bundle) is bundle
    assert bundle.schema_version == diagnostics.CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION
    assert bundle.scope == diagnostics.CP58_TEST28_DIAGNOSTIC_SCOPE
    assert bundle.predeclared_calibration_inputs_only is True
    assert bundle.m1_calibration.input_is_predeclared_calibration is True
    assert bundle.m2_calibration.input_is_predeclared_calibration is True
    assert bundle.m1_calibration.sample_a_feature_means == tuple(
        pair[0] for pair in _M1_EXPECTED_MEANS.values()
    )
    assert bundle.m1_calibration.sample_b_feature_means == tuple(
        pair[1] for pair in _M1_EXPECTED_MEANS.values()
    )
    assert bundle.m2_calibration.sample_a_feature_means == tuple(
        pair[0] for pair in _M2_EXPECTED_MEANS.values()
    )
    assert bundle.m2_calibration.sample_b_feature_means == tuple(
        pair[1] for pair in _M2_EXPECTED_MEANS.values()
    )
    assert bundle.m1_calibration.ipm == Fraction(1, 2)
    assert bundle.m2_calibration.ipm == Fraction(1, 4)
    assert bundle.aess_proposal_value_uniqueness.value_multiplicities == (
        2,
        2,
        1,
        1,
        1,
        1,
    )
    assert bundle.one_selection_contract.selection_count == 1
    assert bundle.one_selection_contract.unique_selected_ancestor_count == 1
    assert bundle.aess_expected_occupancy.record_sha256 == (
        diagnostics.cp58_aess_expected_ancestor_occupancy().record_sha256
    )
    assert bundle.operational_predictions is False
    assert bundle.production_runner_evidence is False
    assert bundle.confirmatory_evidence is False
    assert bundle.manuscript_claim is False
    assert bundle.formal_test_28_status == "OPEN"
    assert "no-operational" in bundle.scope
    assert "no-confirmatory" in bundle.scope


def test_all_metric_and_law_claim_boundaries_remain_negative() -> None:
    bundle = diagnostics.cp58_diagnostic_bundle()
    for registry in (bundle.m1_registry, bundle.m2_registry):
        assert registry.finite_sign_closed_class is True
        assert registry.metric_is_finite_class_pseudometric is True
        assert registry.source_law_verified is False
        assert registry.target_law_verified is False
        assert registry.probability_law_equality_certified is False
        assert registry.continuous_total_variation_claim is False
        assert registry.sliced_wasserstein_registry is False
    for result in (bundle.m1_calibration, bundle.m2_calibration):
        assert result.input_sample_digest_provenance_verified is False
        assert result.sampled_output_observed is False
        assert result.source_laws_verified is False
        assert result.target_comparison is False
        assert result.finite_class_pseudometric_only is True
        assert result.probability_law_equality_certified is False
        assert result.finite_categorical_total_variation is False
        assert result.sliced_wasserstein is False
        assert result.confirmatory_evidence is False
        assert result.formal_test_28_status == "OPEN"
    assert bundle.aess_proposal_value_uniqueness.production_behavior_observed is False
    assert bundle.one_selection_contract.production_boundary_verified is False
    assert bundle.one_selection_contract.production_behavior_observed is False
    assert bundle.aess_expected_occupancy.production_behavior_observed is False
    assert bundle.aess_expected_occupancy.categorical_source_law_verified is False


def test_bundle_rejects_full_redigest_alternate_same_summary_children() -> None:
    bundle = diagnostics.cp58_diagnostic_bundle()

    alternate_calibration = diagnostics.cp58_bounded_feature_ipm(
        "T28-M1-Q", _M1_LEFT + _M1_LEFT, _M1_RIGHT + _M1_RIGHT
    )
    assert alternate_calibration.ipm == bundle.m1_calibration.ipm
    assert alternate_calibration.witness_feature_id == (
        bundle.m1_calibration.witness_feature_id
    )
    forged_bundle = _redigest(
        _forge(bundle, m1_calibration=alternate_calibration),
        b"cp58-diagnostic-bundle-v1\x00",
    )
    with pytest.raises(ValueError, match="M1 calibration differs"):
        diagnostics.validate_cp58_diagnostic_bundle(forged_bundle)

    alternate_one = diagnostics.cp58_same_cloud_ancestor_occupancy(
        (("one-kernel-request-local-cloud", 7),), 8
    )
    assert alternate_one.unique_selected_ancestor_count == 1
    forged_bundle = _redigest(
        _forge(bundle, one_selection_contract=alternate_one),
        b"cp58-diagnostic-bundle-v1\x00",
    )
    with pytest.raises(ValueError, match="one-selection contract differs"):
        diagnostics.validate_cp58_diagnostic_bundle(forged_bundle)

    alternate_states = (
        (0, 0),
        (1, 0),
        (0, 1),
        (2, 0),
        (1, 1),
        (0, 2),
        (0, 1),
        (2, 0),
    )
    original_uniqueness = bundle.aess_proposal_value_uniqueness
    hashes = tuple(
        diagnostics._digest(
            b"cp58-proposal-configuration-value-v1\x00",
            {"fixture_id": "T28-AESS", "configuration": item},
        )
        for item in alternate_states
    )
    distinct = tuple(dict.fromkeys(hashes))
    alternate_uniqueness = _redigest(
        _forge(
            original_uniqueness,
            canonical_configurations_or_state_vectors=alternate_states,
            configuration_value_sha256s=hashes,
            distinct_value_sha256s=distinct,
            value_multiplicities=tuple(hashes.count(item) for item in distinct),
            unique_configuration_value_count=6,
            repeated_value_excess=2,
            maximum_value_multiplicity=2,
        ),
        b"cp58-proposal-configuration-uniqueness-v1\x00",
    )
    forged_bundle = _redigest(
        _forge(bundle, aess_proposal_value_uniqueness=alternate_uniqueness),
        b"cp58-diagnostic-bundle-v1\x00",
    )
    with pytest.raises(ValueError, match="retained AESS state vectors differ"):
        diagnostics.validate_cp58_diagnostic_bundle(forged_bundle)


def test_bundle_rejects_redigested_claim_and_nested_scope_mutants() -> None:
    bundle = diagnostics.cp58_diagnostic_bundle()
    for field in (
        "operational_predictions",
        "production_runner_evidence",
        "confirmatory_evidence",
        "manuscript_claim",
    ):
        forged = _redigest(
            _forge(bundle, **{field: True}),
            b"cp58-diagnostic-bundle-v1\x00",
        )
        with pytest.raises(ValueError, match="claim scope differs"):
            diagnostics.validate_cp58_diagnostic_bundle(forged)

    forged_calibration = _redigest(
        _forge(
            bundle.m1_calibration,
            input_is_predeclared_calibration=False,
        ),
        b"cp58-bounded-feature-ipm-v1\x00",
    )
    forged_bundle = _redigest(
        _forge(bundle, m1_calibration=forged_calibration),
        b"cp58-diagnostic-bundle-v1\x00",
    )
    with pytest.raises(ValueError, match="M1 calibration differs"):
        diagnostics.validate_cp58_diagnostic_bundle(forged_bundle)


def test_all_record_types_are_slots_sealed_immutable_and_nonpickleable() -> None:
    bundle = diagnostics.cp58_diagnostic_bundle()
    records = (
        bundle.m1_registry.projections[0],
        bundle.m1_registry.features[0],
        bundle.m1_registry,
        bundle.m1_calibration,
        bundle.aess_proposal_value_uniqueness,
        bundle.one_selection_contract,
        bundle.aess_expected_occupancy,
        bundle,
    )
    for record in records:
        assert not hasattr(record, "__dict__")
        with pytest.raises(TypeError, match="module-created"):
            type(record)()
        with pytest.raises(TypeError, match="pickle"):
            pickle.dumps(record)
        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            record.record_sha256 = "0" * 64
        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            record.hostile_extra_attribute = True
        with pytest.raises(TypeError, match="cannot be subclassed"):
            builtins.__build_class__(lambda: None, "HostileSubclass", type(record))


def test_canonical_bytes_and_semantic_digests_are_deterministic_and_distinct() -> None:
    first = diagnostics.cp58_diagnostic_bundle()
    second = diagnostics.cp58_diagnostic_bundle()
    assert diagnostics.cp58_canonical_json_bytes(first) == (
        diagnostics.cp58_canonical_json_bytes(second)
    )
    assert first.record_sha256 == second.record_sha256
    assert first.record_sha256 == diagnostics._digest(
        b"cp58-diagnostic-bundle-v1\x00",
        _forge(first, record_sha256="0" * 64),
    )
    child_hashes = {
        first.m1_registry.record_sha256,
        first.m2_registry.record_sha256,
        first.m1_calibration.record_sha256,
        first.m2_calibration.record_sha256,
        first.aess_proposal_value_uniqueness.record_sha256,
        first.one_selection_contract.record_sha256,
        first.aess_expected_occupancy.record_sha256,
    }
    assert len(child_hashes) == 7
    assert first.record_sha256 not in child_hashes
    encoded = diagnostics.cp58_canonical_json_bytes(first)
    assert encoded.startswith(b'{"aess_expected_occupancy":')
    assert b'": ' not in encoded
    assert b", " not in encoded
    assert b"\n" not in encoded


def test_bundle_hashes_are_stable_in_a_fresh_pinned_process() -> None:
    bundle = diagnostics.cp58_diagnostic_bundle()
    expected = (
        bundle.m1_registry.record_sha256,
        bundle.m2_registry.record_sha256,
        bundle.m1_calibration.record_sha256,
        bundle.m2_calibration.record_sha256,
        bundle.aess_proposal_value_uniqueness.record_sha256,
        bundle.one_selection_contract.record_sha256,
        bundle.aess_expected_occupancy.record_sha256,
        bundle.record_sha256,
    )
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
from heterodiff.evaluation import mixed_initializer_test28_bounded_sir_diagnostics as d
b = d.cp58_diagnostic_bundle()
for value in (b.m1_registry,b.m2_registry,b.m1_calibration,b.m2_calibration,b.aess_proposal_value_uniqueness,b.one_selection_contract,b.aess_expected_occupancy,b):
    print(value.record_sha256)
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = source_root
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert tuple(completed.stdout.splitlines()) == expected


def test_stdlib_only_import_succeeds_with_scientific_and_runtime_modules_blocked() -> None:
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
import builtins
original = builtins.__import__
def guarded(name, *args, **kwargs):
    forbidden = ("numpy", "scipy", "torch", "random", "heterodiff.processes", "heterodiff.theory")
    if any(name == item or name.startswith(item + ".") for item in forbidden):
        raise AssertionError("forbidden import: " + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from heterodiff.evaluation import mixed_initializer_test28_bounded_sir_diagnostics as d
print(d.cp58_diagnostic_bundle().record_sha256)
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = source_root
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == (
        diagnostics.cp58_diagnostic_bundle().record_sha256
    )


def test_source_ast_is_stdlib_only_rng_free_and_has_no_runtime_dependency() -> None:
    source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "heterodiff"
        / "evaluation"
        / "mixed_initializer_test28_bounded_sir_diagnostics.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "fractions",
        "hashlib",
        "json",
        "math",
        "typing",
    }
    assert not imported_roots & {
        "heterodiff",
        "numpy",
        "scipy",
        "torch",
        "random",
        "secrets",
    }
    assert "default_rng" not in source
    assert "random_raw" not in source
    assert "np." not in source
    assert "finite empirical measure is singular" not in source
    assert "no source-law" in source
    assert "no target-law" in source
    assert "no-operational" in source
