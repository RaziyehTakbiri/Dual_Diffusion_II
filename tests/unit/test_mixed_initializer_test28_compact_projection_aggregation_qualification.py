"""Independent hostile tests for the development-only CP68 aggregator."""

from __future__ import annotations

import ast
import builtins
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, is_dataclass
from fractions import Fraction
from functools import lru_cache
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import pickle
import random
import secrets
import socket
import subprocess
import sys
import time
import types
import weakref

import heterodiff.evaluation.mixed_initializer_test28_compact_projection_aggregation_qualification as cp68
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_compact_projection_aggregation_qualification.py"
)
_V18_PROTOCOL = _ROOT / "research/preregistrations/cp50_test28_mixed_initializer_v18.md"
_V18_MANIFEST = _ROOT / "research/fixtures/cp50_test28_mixed_initializer_v18.json"

_ZERO_SHA256 = "0" * 64
_V18_PROTOCOL_SHA256 = (
    "857d6ac7e35c0ba3f7f49d63f18c0f4558fa82528aa4fc3dda0ccf3bbdcea9a0"
)
_V18_PROTOCOL_BYTES = 161_456
_V18_PROTOCOL_LF_COUNT = 2_838
_V18_MANIFEST_SHA256 = (
    "5f4f4bc2cf18f1e8bf10b39fa4bfa7c3e2d942d423c6f134d3e25e7f79df63c3"
)
_V18_MANIFEST_BYTES = 6_035_828
_V18_MANIFEST_LF_COUNT = 118_788
_CP58_SOURCE_SHA256 = "24649278e40c49bb1c7eae0f3b00a3c5694020844b986aa836b98c02c3024822"
_M1_FEATURE_REGISTRY_SHA256 = (
    "314a54638d17f8dcb4b4313a92594306643254ab4a958aeb9d81efd5786a0406"
)
_M2_FEATURE_REGISTRY_SHA256 = (
    "e740e5927d2242aa0d945f4a252a638cae6aa4757f31ed24094c188b715929e8"
)
_CP61_SOURCE_SHA256 = "8ea06f5cfc5cd79842e2984d5f91918463cf887c0efc2fd026490f51e66129cb"
_CP61_BUNDLE_SHA256 = "8c5e23661cc0ef459e700c2af5239d21ee8aafd4d9dca2ed3db6e3ce2e4a0ca0"
_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)
_CP61_PROJECTION_SHA256 = (
    "5b7f733e8cd2a8f3ed16915dc77fdf4c059af77ae31a1c5008a2dba9352e7a6d"
)
_CP61_PRECISION_SHA256 = (
    "5e3be7db774cab9c572c3cdf7e98055192391b5ddf2c8d85dfe1592dc392734e"
)
_CP63_INDEPENDENT_SOURCE_SHA256 = (
    "5df076a008d8fe6848dc72083e2563e622c136ce0159441dd69db04c3b1cb9dc"
)
_CP63_INDEPENDENT_BUNDLE_SHA256 = (
    "b219de24a17af7c06b503af07110ed863c339bca19c7457c163412ae0e76ddb9"
)
_CP63_SCHEDULE_CONTRACT_SHA256 = (
    "7ca5555de1aa852021c6b7fd181417a629dcec461455650ecafc495f5e6fb607"
)
_CP67_SOURCE_SHA256 = "e52e5e7229a46b22983aa7b2c3656d3e27a342de5033b5b9f582523d3d67b1c6"
_CP67_TEST_SHA256 = "698c2d4843f3a9d4234aabfe7eef66f3b796c8d08ee6415277f3db2fbeb49b40"
_CP67_BUNDLE_SHA256 = "12dd4c44682a7db53a65258f146e96f6248755ebf2f2ed1db6aa0f4ad3d99c35"
_CP67_FIXTURE_SET_SHA256 = (
    "e5f48b09da24f6a98d1fb3fa0e903dffb306db56233001c1dc6eaa742a2f2a0c"
)
_CP67_EXPECTATION_SHA256 = (
    "283ebec3c3b1bb4c3a18479fdc66e20525a591d9af1f02007869154cf8d041ea"
)

_SCHEMA_VERSION = "cp68-test28-compact-projection-aggregation-qualification-v1"
_M1 = "T28-M1-Q"
_M2 = "T28-M2-Q"
_N = 2_048
_ROW_COUNT = 16
_REQUEST_COUNT = 32_768
_OBSERVABLE_COUNT = 72
_FIRST_ATTEMPT_COUNT = 170
_FEATURE_COUNT = 312
_ESTIMAND_COUNT = 554
_BINOMIAL_COUNT = 242
_TAIL = Fraction(1, 110_800)
_K_MIN = 1_040
_HALFWIDTH = Fraction(3, 40)
_CP_STEPS = 256
_CP_DENOMINATOR = 1 << _CP_STEPS
_CP_GOLDEN_NUMERATOR_HEX = {
    0: (
        "0000000000000000000000000000000000000000000000000000000000000000",
        "0172a4b315e37bd6bf9bb256559430b052d0441ccd3bc1bfdc6436ce8ea3b820",
    ),
    1: (
        "00000012ed6d5cd87f1eeed39116535afdca9bc259b948a6543d388307e25433",
        "01c9973a298dfdd5a0041396e5e9ebc20d8c8e3bb8ce93a2c95afd818bdeb362",
    ),
    1_024: (
        "73d6c766d8fc0efa9c68dcb8d0d9d02d73ed4994ab6a0cceaa87ba53957ef0e4",
        "8c2938992703f105639723472f262fd28c12b66b5495f331557845ac6a810f1c",
    ),
    1_039: (
        "75b42577f425a0d9dd44dc02f33b7795b2f1f5d3d5c553fec8803ba76a159063",
        "8e05ece44774429bf7675a24080f10a187eff48fdd3005c4fe1834d21418c868",
    ),
    1_040: (
        "75d3fe93a34632652678a4ed7a60308337a5c63967da5ac19fffa3ca18006e27",
        "8e25ae9b80e791796ddac5591ef985eff49121422f134ef2ee7eeb408a6cc4ee",
    ),
    2_047: (
        "fe3668c5d672022a5ffbec691a16143df27371c447316c5d36a5027e74214c9e",
        "ffffffed1292a32780e1112c6ee9aca50235643da646b759abc2c77cf81dabcd",
    ),
    2_048: (
        "fe8d5b4cea1c842940644da9aa6bcf4fad2fbbe332c43e40239bc931715c47e0",
        "10000000000000000000000000000000000000000000000000000000000000000",
    ),
}
_FIRST_PROJECTION_SHA256 = (
    "b40854463d8f441614621319f2e7a774059cd757d75284750906f84222744796"
)
_PROJECTION_FIELDS = (
    "schema_version",
    "seed_ordinal",
    "row_ordinal",
    "logical_request_ordinal",
    "row_key",
    "fixture_id",
    "strategy",
    "budget",
    "plan_seed_hex",
    "observable_cell_label",
    "first_selected_attempt_one_based",
    "selected",
    "selected_feature_ids",
    "selected_feature_values",
    "projection_sha256",
)
_RECORD_DOMAINS = {
    "CP68PredecessorCustodyV1": b"cp68-test28-predecessor-custody-v1",
    "CP68SyntheticCompactProjectionContractV1": (
        b"cp68-test28-synthetic-compact-projection-contract-v1"
    ),
    "CP68EstimateIntervalOutputSchemaV1": (
        b"cp68-test28-estimate-interval-output-schema-v1"
    ),
    "CP68EstimandEstimateIntervalV1": (b"cp68-test28-estimand-estimate-interval-v1"),
    "CP68AggregationExpectationV1": (b"cp68-test28-aggregation-expectation-v1"),
    "CP68CompactProjectionAggregationQualificationV1": (
        b"cp68-test28-compact-projection-aggregation-qualification-v1"
    ),
    "CP68CompactProjectionAggregationQualificationBundleV1": (
        b"cp68-test28-compact-projection-aggregation-qualification-bundle-v1"
    ),
}
_SELECTED_COUNTS = (
    2_048,
    1_040,
    1_039,
    0,
    2_048,
    1_040,
    1_039,
    0,
    0,
    1_039,
    1_040,
    2_048,
    0,
    1_039,
    1_040,
    2_048,
)

_REJECTION_CELLS = (
    "returned-rejection-selected-before-deadline",
    "returned-rejection-exhausted-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_SIR_CELLS = (
    "returned-sir-selected-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_ROW_SHAPES = tuple(
    (fixture, strategy, budget)
    for fixture in (_M1, _M2)
    for strategy, budgets in (
        ("bounded-rejection", (1, 4, 16, 64)),
        ("fixed-budget-sir", (8, 32, 128, 512)),
    )
    for budget in budgets
)
_SELECTED_CONFIGURATION_INDEX_BY_ROW = (
    0,
    1,
    0,
    2,
    0,
    1,
    0,
    2,
    0,
    1,
    0,
    3,
    0,
    1,
    0,
    3,
)
_SELECTED_CONFIGURATION_ROSTERS = {
    _M1: (
        (),
        ((0, ()),),
        ((1, (Fraction(1),)),),
    ),
    _M2: (
        (),
        ((0, (Fraction(1, 2),)),),
        ((1, (Fraction(0), Fraction(1, 2))),),
        (
            (0, (Fraction(-1, 2),)),
            (1, (Fraction(1, 2), Fraction(-1, 2))),
        ),
    ),
}


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _projection_sha256(projection: dict) -> str:
    body = {name: projection[name] for name in _PROJECTION_FIELDS[:-1]}
    return _sha256(
        b"cp68-test28-synthetic-compact-projection-v1\0" + _canonical_json_bytes(body)
    )


def _independent_fixture_set_sha256() -> str:
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "seed_count": _N,
        "row_shapes": _ROW_SHAPES,
        "selected_counts_by_row": _SELECTED_COUNTS,
        "selected_configuration_index_by_row": (_SELECTED_CONFIGURATION_INDEX_BY_ROW),
        "m1_selected_configuration_roster_exact": (
            (),
            ((0, ()),),
            ((1, (Fraction(1),)),),
        ),
        "m2_selected_configuration_roster_exact": (
            (),
            ((0, (Fraction(1, 2),)),),
            ((1, (Fraction(0), Fraction(1, 2))),),
            (
                (0, (Fraction(-1, 2),)),
                (1, (Fraction(1, 2), Fraction(-1, 2))),
            ),
        ),
        "logical_request_order": ("seed-major-row-minor;logical=(seed-1)*16+row"),
        "selected_status_formula": ("selected iff seed_ordinal<=selected_count"),
        "rejection_nonselected_status_formula": (
            "(seed-selected_count-1)%4 indexes exhausted,refusal,failure,timeout"
        ),
        "sir_nonselected_status_formula": (
            "(seed-selected_count-1)%3 indexes refusal,failure,timeout"
        ),
        "first_selected_attempt_formula": (
            "(seed_ordinal-1)%budget+1 for selected bounded-rejection"
        ),
        "plan_seed_formula": "lowercase-16-hex(seed_ordinal-1)",
        "feature_value_formula": (
            "complete frozen CP58 registry vector on the row-fixed selected "
            "configuration"
        ),
    }
    return _sha256(
        b"cp68-test28-compact-projection-fixture-set-v1\0"
        + _canonical_json_bytes(payload)
    )


def _independent_record_sha256(record: object) -> str:
    values = {
        item.name: (
            _ZERO_SHA256 if item.name == "record_sha256" else getattr(record, item.name)
        )
        for item in fields(type(record))
    }
    return _sha256(
        _RECORD_DOMAINS[type(record).__name__] + b"\0" + _canonical_json_bytes(values)
    )


def _canonical(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is Fraction:
        return {
            "$fraction": [str(value.numerator), str(value.denominator)],
        }
    if type(value) is tuple:
        return [_canonical(item) for item in value]
    if type(value) is dict:
        assert all(type(key) is str for key in value)
        return {key: _canonical(value[key]) for key in sorted(value)}
    if is_dataclass(value):
        return {
            item.name: _canonical(getattr(value, item.name))
            for item in fields(type(value))
        }
    raise TypeError("unsupported independent canonical value")


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _row_key(row_ordinal: int) -> str:
    fixture, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    return "row-%02d/%s/%s/budget-%d" % (
        row_ordinal,
        fixture,
        strategy,
        budget,
    )


def _projection_specs(
    fixture_id: str,
) -> tuple[tuple[int, str, tuple[Fraction, ...]], ...]:
    if fixture_id == _M1:
        return ((1, "axis0", (Fraction(1),)),)
    return (
        (0, "axis0", (Fraction(1),)),
        (1, "axis0", (Fraction(1), Fraction(0))),
        (1, "axis1", (Fraction(0), Fraction(1))),
        (1, "diag-plus-3-4", (Fraction(3, 5), Fraction(4, 5))),
        (1, "diag-minus-3-4", (Fraction(3, 5), Fraction(-4, 5))),
    )


def _projections(fixture_id: str) -> tuple[tuple[int, str], ...]:
    return tuple(
        (event_type, projection_id)
        for event_type, projection_id, _coefficients in _projection_specs(fixture_id)
    )


def _feature_ids(fixture_id: str) -> tuple[str, ...]:
    cap = 1 if fixture_id == _M1 else 2
    dimensions = (0, 1) if fixture_id == _M1 else (1, 2)
    projections = _projections(fixture_id)
    result = ["count/eq/%d" % count for count in range(cap + 1)]
    result.extend("type/%d/occupancy" % index for index in range(len(dimensions)))
    for type_index, projection_id in projections:
        result.extend(
            (
                "coordinate/%d/%s/odd" % (type_index, projection_id),
                "coordinate/%d/%s/even" % (type_index, projection_id),
            )
        )
    if cap == 2:
        by_type = {
            type_index: tuple(item for item in projections if item[0] == type_index)
            for type_index in range(len(dimensions))
        }
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                result.append("pair-type/%d/%d" % (left_type, right_type))
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                for left_position, left in enumerate(by_type[left_type]):
                    for right_position, right in enumerate(by_type[right_type]):
                        if left_type == right_type and right_position < left_position:
                            continue
                        result.append(
                            "pair-projection/%d/%s/%d/%s"
                            % (left_type, left[1], right_type, right[1])
                        )
    return tuple(result)


def _estimand_ids() -> tuple[str, ...]:
    observable = []
    first = []
    selected = []
    for row_ordinal, (fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        row_key = _row_key(row_ordinal)
        cells = _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
        observable.extend("cp61/observable/%s/%s" % (row_key, cell) for cell in cells)
        if strategy == "bounded-rejection":
            first.extend(
                "cp61/rejection-first-attempt/%s/attempt-%d" % (row_key, attempt)
                for attempt in range(1, budget + 1)
            )
        selected.extend(
            "cp61/selected-feature/%s/%s" % (row_key, feature_id)
            for feature_id in _feature_ids(fixture)
        )
    assert (len(observable), len(first), len(selected)) == (
        _OBSERVABLE_COUNT,
        _FIRST_ATTEMPT_COUNT,
        _FEATURE_COUNT,
    )
    return tuple(observable + first + selected)


def _binomial_cdf(n: int, k: int, p: Fraction) -> Fraction:
    q = 1 - p
    return sum(
        (
            Fraction(math.comb(n, index)) * p**index * q ** (n - index)
            for index in range(k + 1)
        ),
        Fraction(0),
    )


def _feature_interval(
    mean: Fraction,
    lower: Fraction,
    upper: Fraction,
    selected_count: int,
) -> tuple[Fraction, Fraction] | None:
    if selected_count < _K_MIN:
        return None
    halfwidth = (upper - lower) * _HALFWIDTH
    return max(lower, mean - halfwidth), min(upper, mean + halfwidth)


def _cycle_counts(total: int, width: int) -> tuple[int, ...]:
    quotient, remainder = divmod(total, width)
    return tuple(quotient + int(index < remainder) for index in range(width))


def _expected_observable_counts(row_ordinal: int) -> tuple[int, ...]:
    _fixture, strategy, _budget = _ROW_SHAPES[row_ordinal - 1]
    selected = _SELECTED_COUNTS[row_ordinal - 1]
    if strategy == "bounded-rejection":
        return (selected,) + _cycle_counts(_N - selected, 4)
    return (selected,) + _cycle_counts(_N - selected, 3)


def _expected_attempt_counts(selected: int, budget: int) -> tuple[int, ...]:
    quotient, remainder = divmod(selected, budget)
    return tuple(
        quotient + int(attempt <= remainder) for attempt in range(1, budget + 1)
    )


def _expected_projection_status(
    seed_ordinal: int, row_ordinal: int
) -> tuple[str, int | None, bool]:
    _fixture, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    selected_count = _SELECTED_COUNTS[row_ordinal - 1]
    if seed_ordinal <= selected_count:
        if strategy == "bounded-rejection":
            return _REJECTION_CELLS[0], (seed_ordinal - 1) % budget + 1, True
        return _SIR_CELLS[0], None, True
    offset = seed_ordinal - selected_count - 1
    if strategy == "bounded-rejection":
        return _REJECTION_CELLS[1 + offset % 4], None, False
    return _SIR_CELLS[1 + offset % 3], None, False


def _odd(value: Fraction) -> Fraction:
    return max(Fraction(-1), min(Fraction(1), value))


def _even(value: Fraction) -> Fraction:
    return Fraction(1) if abs(value) >= 1 else value * value


def _project(
    event: tuple[int, tuple[Fraction, ...]],
    coefficients: tuple[Fraction, ...],
) -> Fraction:
    return sum(
        (
            coefficient * coordinate
            for coefficient, coordinate in zip(coefficients, event[1])
        ),
        Fraction(0),
    )


def _exact_feature_vector(
    fixture_id: str,
    configuration: tuple[tuple[int, tuple[Fraction, ...]], ...],
) -> tuple[tuple[str, Fraction], ...]:
    """Independently evaluate the frozen CP58 feature definitions."""

    cap = 1 if fixture_id == _M1 else 2
    dimensions = (0, 1) if fixture_id == _M1 else (1, 2)
    projections = _projection_specs(fixture_id)
    projection_map = {
        (event_type, projection_id): coefficients
        for event_type, projection_id, coefficients in projections
    }
    values = []
    for count in range(cap + 1):
        values.append(Fraction(int(len(configuration) == count)))
    for event_type in range(len(dimensions)):
        values.append(
            Fraction(
                sum(1 for event in configuration if event[0] == event_type),
                cap,
            )
        )
    for event_type, _projection_id, coefficients in projections:
        projected = (
            _project(event, coefficients)
            for event in configuration
            if event[0] == event_type
        )
        projected = tuple(projected)
        values.append(sum((_odd(value) for value in projected), Fraction(0)) / cap)
        values.append(sum((_even(value) for value in projected), Fraction(0)) / cap)
    if cap == 2:
        pairs = tuple(
            (configuration[left], configuration[right])
            for left in range(len(configuration))
            for right in range(left + 1, len(configuration))
        )
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                values.append(
                    Fraction(
                        sum(
                            1
                            for left, right in pairs
                            if (left[0], right[0]) == (left_type, right_type)
                        )
                    )
                )
        by_type = {
            event_type: tuple(item for item in projections if item[0] == event_type)
            for event_type in range(len(dimensions))
        }
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                for left_position, left_projection in enumerate(by_type[left_type]):
                    for right_position, right_projection in enumerate(
                        by_type[right_type]
                    ):
                        if left_type == right_type and right_position < left_position:
                            continue
                        total = Fraction(0)
                        for left, right in pairs:
                            if (left[0], right[0]) != (left_type, right_type):
                                continue
                            direct = _odd(
                                _project(
                                    left,
                                    projection_map[(left_type, left_projection[1])],
                                )
                            ) * _odd(
                                _project(
                                    right,
                                    projection_map[(right_type, right_projection[1])],
                                )
                            )
                            if (
                                left_type == right_type
                                and left_projection[1] != right_projection[1]
                            ):
                                reverse = _odd(
                                    _project(
                                        left,
                                        projection_map[
                                            (left_type, right_projection[1])
                                        ],
                                    )
                                ) * _odd(
                                    _project(
                                        right,
                                        projection_map[
                                            (right_type, left_projection[1])
                                        ],
                                    )
                                )
                                direct = (direct + reverse) / 2
                            total += direct
                        values.append(total)
    feature_ids = _feature_ids(fixture_id)
    assert len(values) == len(feature_ids)
    return tuple(zip(feature_ids, values))


class _ProtocolBomb:
    def __getattribute__(self, name: str) -> object:
        raise AssertionError("protocol coercion attempted: " + name)


class _IntSubclass(int):
    pass


class _StrSubclass(str):
    pass


class _TupleSubclass(tuple):
    pass


class _IterableBomb:
    def __iter__(self) -> object:
        raise RuntimeError("iterable infrastructure failed")


def _forge(record: object, **changes: object) -> object:
    forged = object.__new__(type(record))
    for item in fields(type(record)):
        object.__setattr__(
            forged,
            item.name,
            changes.get(item.name, getattr(record, item.name)),
        )
    return forged


def _mutated_projection_stream(logical_ordinal: int, **changes: object) -> object:
    for candidate_ordinal, projection in enumerate(
        cp68._iter_synthetic_projections(), 1
    ):
        if candidate_ordinal == logical_ordinal:
            mutated = dict(projection)
            mutated.update(changes)
            yield mutated
        else:
            yield projection


def _failing_projection_stream() -> object:
    yield next(cp68._iter_synthetic_projections())
    raise RuntimeError("iterator infrastructure failed")


@lru_cache(maxsize=1)
def _actual_output_records() -> tuple[object, ...]:
    """Reach the closed output only through CP68's private test seam."""

    for name in (
        "_development_output",
        "_build_development_output",
        "_aggregate_closed_fixture",
    ):
        candidate = getattr(cp68, name, None)
        if candidate is not None:
            value = candidate()
            if type(value) is tuple and len(value) == _ESTIMAND_COUNT:
                return value
            if type(value) is tuple:
                for item in value:
                    if type(item) is tuple and len(item) == _ESTIMAND_COUNT:
                        return item
    raise AssertionError("CP68 does not expose its closed output to hostile tests")


def _bundle() -> object:
    return cp68.cp68_compact_projection_aggregation_qualification_bundle()


def _qualification() -> object:
    return cp68.cp68_run_compact_projection_aggregation_qualification()


def _cp61_estimands() -> tuple[object, ...]:
    # This predecessor is the independent oracle.  CP68 itself must not import it.
    from heterodiff.evaluation import (
        mixed_initializer_test28_whole_seed_mc_design as cp61,
    )

    bundle = cp61.cp61_whole_seed_mc_design_bundle()
    return (
        bundle.observable_estimands
        + bundle.rejection_first_attempt_estimands
        + bundle.selected_conditional_feature_estimands
    )


def test_cp68_live_v18_and_predecessor_file_pins_are_exact() -> None:
    protocol = _V18_PROTOCOL.read_bytes()
    manifest = _V18_MANIFEST.read_bytes()
    assert (_sha256(protocol), len(protocol), protocol.count(b"\n")) == (
        _V18_PROTOCOL_SHA256,
        _V18_PROTOCOL_BYTES,
        _V18_PROTOCOL_LF_COUNT,
    )
    assert (_sha256(manifest), len(manifest), manifest.count(b"\n")) == (
        _V18_MANIFEST_SHA256,
        _V18_MANIFEST_BYTES,
        _V18_MANIFEST_LF_COUNT,
    )
    assert protocol.endswith(b"\n")
    assert manifest.endswith(b"\n")
    assert (
        _sha256(
            (
                _ROOT / "src/heterodiff/evaluation/"
                "mixed_initializer_test28_whole_seed_mc_design.py"
            ).read_bytes()
        )
        == _CP61_SOURCE_SHA256
    )
    assert (
        _sha256(
            (
                _ROOT / "src/heterodiff/evaluation/"
                "mixed_initializer_test28_independent_recomputation.py"
            ).read_bytes()
        )
        == _CP63_INDEPENDENT_SOURCE_SHA256
    )
    assert (
        _sha256(
            (
                _ROOT / "src/heterodiff/evaluation/"
                "mixed_initializer_test28_full_schedule_materializer_qualification.py"
            ).read_bytes()
        )
        == _CP67_SOURCE_SHA256
    )
    assert (
        _sha256(
            (
                _ROOT / "tests/unit/"
                "test_mixed_initializer_test28_full_schedule_materializer_qualification.py"
            ).read_bytes()
        )
        == _CP67_TEST_SHA256
    )


def test_cp68_frozen_scalar_constants_and_public_signatures_are_closed() -> None:
    assert cp68.CP68_TEST28_SCHEMA_VERSION == _SCHEMA_VERSION
    assert cp68.CP68_TEST28_FORMAL_TEST_28_STATUS == "OPEN"
    assert cp68.CP68_TEST28_SEED_COUNT == _N
    assert cp68.CP68_TEST28_ROW_COUNT == _ROW_COUNT
    assert cp68.CP68_TEST28_REQUEST_COUNT == _REQUEST_COUNT
    assert cp68.CP68_TEST28_ESTIMAND_COUNT == _ESTIMAND_COUNT
    assert cp68.CP68_TEST28_BINOMIAL_ESTIMAND_COUNT == _BINOMIAL_COUNT
    assert cp68.CP68_TEST28_FEATURE_ESTIMAND_COUNT == _FEATURE_COUNT
    assert cp68.CP68_TEST28_CP_BISECTION_STEPS == _CP_STEPS
    assert cp68.CP68_TEST28_MINIMUM_SELECTED_COUNT == _K_MIN
    assert cp68.CP68_TEST28_PER_TAIL_ERROR_BUDGET == _TAIL
    assert cp68.CP68_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER == _HALFWIDTH
    for function in (
        cp68.cp68_compact_projection_fixture_set_sha256,
        cp68.cp68_compact_projection_aggregation_qualification_bundle,
        cp68.cp68_run_compact_projection_aggregation_qualification,
    ):
        assert tuple(inspect.signature(function).parameters) == ()
    assert tuple(
        inspect.signature(cp68.cp68_exact_clopper_pearson_interval_2048).parameters
    ) == ("success_count",)
    assert tuple(inspect.signature(cp68.cp68_canonical_json_bytes).parameters) == (
        "value",
    )
    assert tuple(inspect.signature(cp68.cp68_sha256).parameters) == ("value",)
    fixture_set_sha256 = cp68.cp68_compact_projection_fixture_set_sha256()
    assert fixture_set_sha256 == _independent_fixture_set_sha256()
    assert len(fixture_set_sha256) == 64
    assert all(character in "0123456789abcdef" for character in fixture_set_sha256)


def test_cp68_public_export_surface_is_exact() -> None:
    assert cp68.__all__ == (
        "CP68_TEST28_SCHEMA_VERSION",
        "CP68_TEST28_SCOPE",
        "CP68_TEST28_FORMAL_TEST_28_STATUS",
        "CP68_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID",
        "CP68_TEST28_SEED_COUNT",
        "CP68_TEST28_ROW_COUNT",
        "CP68_TEST28_REQUEST_COUNT",
        "CP68_TEST28_OBSERVABLE_ESTIMAND_COUNT",
        "CP68_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT",
        "CP68_TEST28_FEATURE_ESTIMAND_COUNT",
        "CP68_TEST28_ESTIMAND_COUNT",
        "CP68_TEST28_BINOMIAL_ESTIMAND_COUNT",
        "CP68_TEST28_FAMILYWISE_ERROR_BUDGET",
        "CP68_TEST28_PER_ESTIMATOR_ERROR_BUDGET",
        "CP68_TEST28_PER_TAIL_ERROR_BUDGET",
        "CP68_TEST28_CP_BISECTION_STEPS",
        "CP68_TEST28_MINIMUM_SELECTED_COUNT",
        "CP68_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER",
        "CP68_TEST28_OUTPUT_MAX_BYTES",
        "CP68_TEST28_SELECTED_COUNTS_BY_ROW",
        "CP68CompactProjectionAggregationQualificationError",
        "CP68PredecessorCustodyV1",
        "CP68SyntheticCompactProjectionContractV1",
        "CP68EstimateIntervalOutputSchemaV1",
        "CP68EstimandEstimateIntervalV1",
        "CP68AggregationExpectationV1",
        "CP68CompactProjectionAggregationQualificationV1",
        "CP68CompactProjectionAggregationQualificationBundleV1",
        "cp68_canonical_json_bytes",
        "cp68_sha256",
        "cp68_compact_projection_fixture_set_sha256",
        "cp68_exact_clopper_pearson_interval_2048",
        "cp68_compact_projection_aggregation_qualification_bundle",
        "cp68_run_compact_projection_aggregation_qualification",
    )


def test_cp68_independent_inventory_is_exactly_72_170_312_in_cp61_order() -> None:
    expected_ids = _estimand_ids()
    assert len(expected_ids) == _ESTIMAND_COUNT
    assert len(set(expected_ids)) == _ESTIMAND_COUNT
    cp61_records = _cp61_estimands()
    assert tuple(item.estimand_id for item in cp61_records) == expected_ids
    assert tuple(item.estimand_ordinal for item in cp61_records) == tuple(
        range(1, _ESTIMAND_COUNT + 1)
    )
    assert (
        tuple(item.estimand_family for item in cp61_records[:72])
        == ("observable-cell",) * 72
    )
    assert (
        tuple(item.estimand_family for item in cp61_records[72:242])
        == ("rejection-first-attempt",) * 170
    )
    assert (
        tuple(item.estimand_family for item in cp61_records[242:])
        == ("selected-conditional-feature",) * 312
    )


def test_cp68_bundle_predecessor_custody_and_contract_are_exact() -> None:
    bundle = _bundle()
    custody = bundle.predecessor_custody
    assert tuple(
        getattr(custody, name)
        for name in (
            "v18_protocol_sha256",
            "v18_protocol_bytes",
            "v18_protocol_lf_count",
            "v18_manifest_sha256",
            "v18_manifest_bytes",
            "v18_manifest_lf_count",
        )
    ) == (
        _V18_PROTOCOL_SHA256,
        _V18_PROTOCOL_BYTES,
        _V18_PROTOCOL_LF_COUNT,
        _V18_MANIFEST_SHA256,
        _V18_MANIFEST_BYTES,
        _V18_MANIFEST_LF_COUNT,
    )
    assert custody.cp58_source_sha256 == _CP58_SOURCE_SHA256
    assert custody.m1_feature_registry_sha256 == _M1_FEATURE_REGISTRY_SHA256
    assert custody.m2_feature_registry_sha256 == _M2_FEATURE_REGISTRY_SHA256
    assert custody.cp61_source_sha256 == _CP61_SOURCE_SHA256
    assert custody.cp61_bundle_record_sha256 == _CP61_BUNDLE_SHA256
    assert custody.cp61_stable_design_sha256 == _CP61_STABLE_DESIGN_SHA256
    assert custody.cp61_projection_contract_record_sha256 == _CP61_PROJECTION_SHA256
    assert custody.cp61_multiplicity_precision_record_sha256 == _CP61_PRECISION_SHA256
    assert custody.cp63_independent_source_sha256 == _CP63_INDEPENDENT_SOURCE_SHA256
    assert custody.cp63_independent_bundle_record_sha256 == (
        _CP63_INDEPENDENT_BUNDLE_SHA256
    )
    assert custody.cp63_schedule_contract_record_sha256 == (
        _CP63_SCHEDULE_CONTRACT_SHA256
    )
    assert custody.cp67_source_sha256 == _CP67_SOURCE_SHA256
    assert custody.cp67_test_sha256 == _CP67_TEST_SHA256
    assert custody.cp67_bundle_record_sha256 == _CP67_BUNDLE_SHA256
    assert custody.cp67_qualification_fixture_set_sha256 == _CP67_FIXTURE_SET_SHA256
    assert custody.cp67_schedule_expectation_record_sha256 == (_CP67_EXPECTATION_SHA256)

    contract = bundle.synthetic_projection_contract
    assert (
        contract.seed_count,
        contract.row_count,
        contract.request_count,
    ) == (_N, _ROW_COUNT, _REQUEST_COUNT)
    assert contract.selected_counts_by_row == _SELECTED_COUNTS
    assert contract.selected_configuration_roster_sizes == (3, 4)
    assert contract.all_observable_cells_reached is True
    assert contract.all_rejection_first_attempts_reached is True
    assert contract.streaming_single_projection is True
    assert contract.compact_projection_corpus_retained is False
    assert contract.raw_records_accepted is False
    assert contract.stable_traces_accepted is False
    assert contract.filesystem_paths_accepted is False


def test_cp68_synthetic_projection_iterator_is_one_shot_and_lazy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = cp68._synthetic_projection
    calls = []

    def observed(seed_ordinal: int, row_ordinal: int) -> dict:
        calls.append((seed_ordinal, row_ordinal))
        return original(seed_ordinal, row_ordinal)

    monkeypatch.setattr(cp68, "_synthetic_projection", observed)
    iterator = cp68._iter_synthetic_projections()
    assert iter(iterator) is iterator
    assert calls == []
    assert next(iterator)["logical_request_ordinal"] == 1
    assert calls == [(1, 1)]
    assert next(iterator)["logical_request_ordinal"] == 2
    assert calls == [(1, 1), (1, 2)]
    iterator.close()


def test_cp68_streams_all_32768_projections_against_independent_oracle() -> None:
    iterator = cp68._iter_synthetic_projections()
    seen = 0
    ordered_projection_digest = hashlib.sha256(
        b"cp68-test28-ordered-projection-digests-v1\0"
    )
    for seed_ordinal in range(1, _N + 1):
        for row_ordinal, (fixture_id, strategy, budget) in enumerate(_ROW_SHAPES, 1):
            projection = next(iterator)
            seen += 1
            status, first_attempt, selected = _expected_projection_status(
                seed_ordinal, row_ordinal
            )
            assert type(projection) is dict
            assert tuple(projection) == _PROJECTION_FIELDS
            assert projection["schema_version"] == _SCHEMA_VERSION
            assert type(projection["seed_ordinal"]) is int
            assert projection["seed_ordinal"] == seed_ordinal
            assert type(projection["row_ordinal"]) is int
            assert projection["row_ordinal"] == row_ordinal
            assert type(projection["logical_request_ordinal"]) is int
            assert projection["logical_request_ordinal"] == seen
            assert projection["row_key"] == _row_key(row_ordinal)
            assert projection["fixture_id"] == fixture_id
            assert projection["strategy"] == strategy
            assert type(projection["budget"]) is int
            assert projection["budget"] == budget
            assert projection["plan_seed_hex"] == "%016x" % (seed_ordinal - 1)
            assert projection["observable_cell_label"] == status
            assert projection["first_selected_attempt_one_based"] == first_attempt
            assert type(projection["selected"]) is bool
            assert projection["selected"] is selected
            assert type(projection["selected_feature_ids"]) is tuple
            assert type(projection["selected_feature_values"]) is tuple
            if selected:
                roster = _SELECTED_CONFIGURATION_ROSTERS[fixture_id]
                configuration = roster[
                    _SELECTED_CONFIGURATION_INDEX_BY_ROW[row_ordinal - 1]
                ]
                expected_features = _exact_feature_vector(fixture_id, configuration)
                assert projection["selected_feature_ids"] == tuple(
                    feature_id for feature_id, _value in expected_features
                )
                assert projection["selected_feature_values"] == tuple(
                    value for _feature_id, value in expected_features
                )
            else:
                assert projection["selected_feature_ids"] == ()
                assert projection["selected_feature_values"] == ()
            assert projection["projection_sha256"] == _projection_sha256(projection)
            ordered_projection_digest.update(
                bytes.fromhex(projection["projection_sha256"])
            )
            if seen == 1:
                assert projection["projection_sha256"] == (_FIRST_PROJECTION_SHA256)
    assert seen == _REQUEST_COUNT
    with pytest.raises(StopIteration):
        next(iterator)
    assert ordered_projection_digest.hexdigest() == (
        _bundle().aggregation_expectation.ordered_projection_sha256
    )


@pytest.mark.parametrize(
    ("projections", "code"),
    (
        ((), "CP68_PROJECTION_COUNT_MISMATCH"),
        (
            (cp68._synthetic_projection(1, 2),),
            "CP68_PROJECTION_ORDINAL_MISMATCH",
        ),
        (
            (
                cp68._synthetic_projection(1, 1),
                cp68._synthetic_projection(1, 1),
            ),
            "CP68_PROJECTION_ORDINAL_MISMATCH",
        ),
        (_IterableBomb(), "CP68_PROJECTION_ITERABLE_INVALID"),
        (_failing_projection_stream(), "CP68_PROJECTION_ITERATION_FAILED"),
    ),
)
def test_cp68_rejects_missing_duplicate_out_of_order_and_failed_streams(
    projections: object, code: str
) -> None:
    issued_before = len(cp68._ISSUED_RECORD_SNAPSHOTS)
    with pytest.raises(
        cp68.CP68CompactProjectionAggregationQualificationError
    ) as caught:
        cp68._aggregate_closed_fixture(projections)
    assert caught.value.code == code
    assert len(cp68._ISSUED_RECORD_SNAPSHOTS) == issued_before


@pytest.mark.parametrize(
    ("logical_ordinal", "changes", "code"),
    (
        (1, {"seed_ordinal": True}, "CP68_PROJECTION_FIELD_TYPE_MISMATCH"),
        (1, {"seed_ordinal": 2}, "CP68_PROJECTION_ORDINAL_MISMATCH"),
        (1, {"row_ordinal": 2}, "CP68_PROJECTION_ORDINAL_MISMATCH"),
        (
            1,
            {"logical_request_ordinal": 2},
            "CP68_PROJECTION_ORDINAL_MISMATCH",
        ),
        (
            1,
            {"first_selected_attempt_one_based": None},
            "CP68_PROJECTION_CONTENT_MISMATCH",
        ),
        (
            1,
            {"first_selected_attempt_one_based": 2},
            "CP68_PROJECTION_CONTENT_MISMATCH",
        ),
        (
            5,
            {"first_selected_attempt_one_based": 1},
            "CP68_PROJECTION_CONTENT_MISMATCH",
        ),
        (
            4,
            {
                "selected_feature_ids": ("count/eq/0",),
                "selected_feature_values": (Fraction(1),),
            },
            "CP68_PROJECTION_CONTENT_MISMATCH",
        ),
        (
            1,
            {"selected_feature_ids": _feature_ids(_M1)[:-1]},
            "CP68_PROJECTION_CONTENT_MISMATCH",
        ),
        (
            1,
            {
                "selected_feature_ids": (
                    _feature_ids(_M1)[0],
                    _feature_ids(_M1)[0],
                )
                + _feature_ids(_M1)[2:],
            },
            "CP68_PROJECTION_CONTENT_MISMATCH",
        ),
        (
            1,
            {
                "selected_feature_values": (Fraction(2),)
                + tuple(value for _feature_id, value in _exact_feature_vector(_M1, ()))[
                    1:
                ],
            },
            "CP68_PROJECTION_CONTENT_MISMATCH",
        ),
        (
            1,
            {"projection_sha256": _ZERO_SHA256},
            "CP68_PROJECTION_DIGEST_MISMATCH",
        ),
    ),
)
def test_cp68_rejects_projection_type_ordinal_semantic_and_digest_corruption(
    logical_ordinal: int, changes: dict, code: str
) -> None:
    issued_before = len(cp68._ISSUED_RECORD_SNAPSHOTS)
    with pytest.raises(
        cp68.CP68CompactProjectionAggregationQualificationError
    ) as caught:
        cp68._aggregate_closed_fixture(
            _mutated_projection_stream(logical_ordinal, **changes)
        )
    assert caught.value.code == code
    assert len(cp68._ISSUED_RECORD_SNAPSHOTS) == issued_before


def test_cp68_rejects_nonexact_projection_mapping_and_field_sets() -> None:
    class DictSubclass(dict):
        pass

    first = cp68._synthetic_projection(1, 1)
    missing = dict(first)
    del missing["row_key"]
    extra = dict(first)
    extra["raw_record"] = b"forbidden"
    nonstring = dict(first)
    nonstring[1] = None
    for projection, code in (
        (DictSubclass(first), "CP68_PROJECTION_TYPE_MISMATCH"),
        (missing, "CP68_PROJECTION_FIELD_SET_MISMATCH"),
        (extra, "CP68_PROJECTION_FIELD_SET_MISMATCH"),
        (nonstring, "CP68_PROJECTION_FIELD_SET_MISMATCH"),
    ):
        with pytest.raises(
            cp68.CP68CompactProjectionAggregationQualificationError
        ) as caught:
            cp68._aggregate_closed_fixture((projection,))
        assert caught.value.code == code


def test_cp68_infinite_projection_source_is_bounded_at_one_extra_item() -> None:
    consumed = [0]

    def infinite_source() -> object:
        first = None
        for projection in cp68._iter_synthetic_projections():
            consumed[0] += 1
            if first is None:
                first = projection
            yield projection
        while True:
            consumed[0] += 1
            yield first

    with pytest.raises(
        cp68.CP68CompactProjectionAggregationQualificationError
    ) as caught:
        cp68._aggregate_closed_fixture(infinite_source())
    assert caught.value.code == "CP68_PROJECTION_COUNT_MISMATCH"
    assert consumed == [_REQUEST_COUNT + 1]


@pytest.mark.parametrize("extra", (None, 0))
def test_cp68_rejects_malformed_item_after_exact_full_stream_without_poisoning(
    extra: object,
) -> None:
    def overlong_source() -> object:
        yield from cp68._iter_synthetic_projections()
        yield extra

    bundle = _bundle()
    bundle_snapshot = cp68.cp68_canonical_json_bytes(bundle)
    issued_before = len(cp68._ISSUED_RECORD_SNAPSHOTS)
    interval_cache_before = cp68._exact_clopper_pearson_interval.cache_info()
    numerator_cache_before = cp68._lower_cp_numerator.cache_info()
    with pytest.raises(
        cp68.CP68CompactProjectionAggregationQualificationError
    ) as caught:
        cp68._aggregate_closed_fixture(overlong_source())
    assert caught.value.code == "CP68_PROJECTION_COUNT_MISMATCH"
    assert caught.value.__cause__ is None
    assert len(cp68._ISSUED_RECORD_SNAPSHOTS) == issued_before
    assert cp68._exact_clopper_pearson_interval.cache_info() == (interval_cache_before)
    assert cp68._lower_cp_numerator.cache_info() == numerator_cache_before
    assert _bundle() is bundle
    assert cp68.cp68_canonical_json_bytes(bundle) == bundle_snapshot


def test_cp68_record_field_orders_are_exact_and_closed() -> None:
    bundle = _bundle()
    output = _actual_output_records()
    qualification = _qualification()
    assert tuple(item.name for item in fields(type(bundle.predecessor_custody))) == (
        "schema_version",
        "v18_protocol_sha256",
        "v18_protocol_bytes",
        "v18_protocol_lf_count",
        "v18_manifest_sha256",
        "v18_manifest_bytes",
        "v18_manifest_lf_count",
        "cp58_source_sha256",
        "m1_feature_registry_sha256",
        "m2_feature_registry_sha256",
        "cp61_source_sha256",
        "cp61_bundle_record_sha256",
        "cp61_stable_design_sha256",
        "cp61_projection_contract_record_sha256",
        "cp61_multiplicity_precision_record_sha256",
        "cp63_independent_source_sha256",
        "cp63_independent_bundle_record_sha256",
        "cp63_schedule_contract_record_sha256",
        "cp67_source_sha256",
        "cp67_test_sha256",
        "cp67_bundle_record_sha256",
        "cp67_qualification_fixture_set_sha256",
        "cp67_schedule_expectation_record_sha256",
        "record_sha256",
    )
    assert tuple(
        item.name for item in fields(type(bundle.synthetic_projection_contract))
    ) == (
        "schema_version",
        "contract_id",
        "seed_count",
        "row_count",
        "request_count",
        "logical_request_order",
        "synthetic_plan_seed_formula",
        "selected_counts_by_row",
        "selected_configuration_roster_sizes",
        "all_observable_cells_reached",
        "all_rejection_first_attempts_reached",
        "streaming_single_projection",
        "compact_projection_corpus_retained",
        "raw_records_accepted",
        "stable_traces_accepted",
        "filesystem_paths_accepted",
        "record_sha256",
    )
    assert tuple(
        item.name for item in fields(type(bundle.estimate_interval_output_schema))
    ) == (
        "schema_version",
        "schema_id",
        "estimand_count",
        "binomial_estimand_count",
        "feature_estimand_count",
        "exact_estimand_keys",
        "binomial_interval_method",
        "binomial_trial_count",
        "per_tail_error_budget",
        "cp_bisection_steps",
        "feature_interval_method",
        "minimum_selected_count",
        "feature_halfwidth_range_multiplier",
        "computed_interval_states",
        "strict_discriminated_union",
        "decision_fields_present",
        "maximum_output_bytes",
        "record_sha256",
    )
    assert tuple(item.name for item in fields(type(output[0]))) == (
        "schema_version",
        "estimand_ordinal",
        "estimand_id",
        "cp61_estimand_record_sha256",
        "estimand_family",
        "row_ordinal",
        "fixture_id",
        "strategy",
        "budget",
        "observable_cell_label",
        "first_attempt_one_based",
        "feature_id",
        "feature_lower_bound",
        "feature_upper_bound",
        "denominator_mode",
        "denominator_count",
        "success_count",
        "exact_feature_sum",
        "estimate",
        "interval_method",
        "interval_state",
        "interval_lower",
        "interval_upper",
        "development_fixture_only",
        "record_sha256",
    )
    assert tuple(
        item.name for item in fields(type(bundle.aggregation_expectation))
    ) == (
        "schema_version",
        "fixture_set_sha256",
        "request_count",
        "estimand_count",
        "binomial_interval_count",
        "feature_interval_count",
        "insufficient_selection_count",
        "computed_interval_count",
        "selected_counts_by_row",
        "ordered_projection_sha256",
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
        "record_sha256",
    )
    assert tuple(item.name for item in fields(type(qualification))) == (
        "schema_version",
        "fixture_set_sha256",
        "request_count",
        "logical_ordinals_complete",
        "streaming_peak_projection_count",
        "compact_projection_corpus_retained",
        "observable_row_sums_verified",
        "first_attempt_sums_verified",
        "feature_denominators_verified",
        "estimand_count",
        "binomial_interval_count",
        "feature_interval_count",
        "insufficient_selection_count",
        "computed_interval_count",
        "cp_zero_endpoint_verified",
        "cp_all_endpoint_verified",
        "cp_256_step_dyadic_endpoints_independently_verified",
        "feature_threshold_verified",
        "feature_clipping_verified",
        "ordered_projection_sha256",
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
        "output_matches_frozen_expectation",
        "raw_or_stable_recomputation_performed",
        "decision_path_qualified",
        "production_evidence",
        "production_execution_authorized",
        "runner_and_recomputation_blocker_closed",
        "formal_test_28_closed",
        "all_development_qualification_checks_passed",
        "record_sha256",
    )
    assert tuple(item.name for item in fields(type(bundle))) == (
        "schema_version",
        "scope",
        "predecessor_custody",
        "synthetic_projection_contract",
        "estimate_interval_output_schema",
        "aggregation_expectation",
        "qualification_fixture_set_sha256",
        "zero_argument_builder",
        "builder_streams_or_aggregates",
        "qualification_runner_zero_argument",
        "closed_module_owned_fixture_only",
        "bounded_exact_cp2048_api_exposed",
        "stdlib_only_import",
        "project_modules_imported_by_builder",
        "predecessor_modules_lazy_imported_by_qualification_runner",
        "streaming_aggregation",
        "full_projection_corpus_materialized",
        "host_filesystem_probed",
        "clock_read",
        "rng_used",
        "network_used",
        "subprocess_api_exposed",
        "filesystem_path_api_exposed",
        "generic_projection_api_exposed",
        "raw_record_api_exposed",
        "stable_trace_api_exposed",
        "production_recomputation_api_exposed",
        "production_estimate_or_interval",
        "decision_path_qualified",
        "production_qualification_receipt_present",
        "production_gate_13_evidence_present",
        "production_gate_13_state",
        "production_gate_14_evidence_present",
        "production_gate_14_state",
        "production_execution_authorized",
        "production_execution_observed",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_and_thresholds_blocker_closed",
        "confirmatory_custody_blocker_closed",
        "confirmatory_evidence",
        "manuscript_claim",
        "formal_test_28_status",
        "formal_test_28_closed",
        "ledger_prerequisite_id",
        "ledger_prerequisite_state",
        "ledger_total_count",
        "ledger_satisfied_count",
        "ledger_missing_count",
        "development_qualification_only",
        "record_sha256",
    )


def test_cp68_output_schema_is_exact_and_has_no_decision_fields() -> None:
    schema = _bundle().estimate_interval_output_schema
    assert (
        schema.estimand_count,
        schema.binomial_estimand_count,
        schema.feature_estimand_count,
    ) == (_ESTIMAND_COUNT, _BINOMIAL_COUNT, _FEATURE_COUNT)
    assert schema.binomial_trial_count == _N
    assert schema.binomial_interval_method == (
        "clopper-pearson-exact-rational-certified-equivalent-outward-"
        "endpoint-on-2^-256-grid-n2048"
    )
    assert schema.per_tail_error_budget == _TAIL
    assert schema.cp_bisection_steps == _CP_STEPS
    assert schema.minimum_selected_count == _K_MIN
    assert schema.feature_halfwidth_range_multiplier == _HALFWIDTH
    assert schema.strict_discriminated_union is True
    assert schema.decision_fields_present is False
    assert schema.computed_interval_states == (
        "computed",
        "insufficient-selection",
    )
    output = _actual_output_records()
    assert schema.exact_estimand_keys is True
    assert schema.maximum_output_bytes >= len(_canonical_json_bytes(output))


def test_cp68_closed_output_matches_cp61_inventory_and_exact_record_pins() -> None:
    output = _actual_output_records()
    expected = _cp61_estimands()
    assert len(output) == len(expected) == _ESTIMAND_COUNT
    assert tuple(item.estimand_ordinal for item in output) == tuple(
        range(1, _ESTIMAND_COUNT + 1)
    )
    assert tuple(item.estimand_id for item in output) == _estimand_ids()
    for actual, frozen in zip(output, expected):
        assert actual.cp61_estimand_record_sha256 == frozen.record_sha256
        for name in (
            "estimand_ordinal",
            "estimand_id",
            "estimand_family",
            "row_ordinal",
            "fixture_id",
            "strategy",
            "budget",
            "observable_cell_label",
            "first_attempt_one_based",
            "feature_id",
            "feature_lower_bound",
            "feature_upper_bound",
            "denominator_mode",
        ):
            assert getattr(actual, name) == getattr(frozen, name), name
        assert actual.development_fixture_only is True


def test_cp68_closed_output_digests_match_independent_canonical_recomputation() -> None:
    output = _actual_output_records()
    expectation = _bundle().aggregation_expectation
    ordered_record_sha256 = _sha256(
        b"cp68-test28-ordered-estimand-record-digests-v1\0"
        + b"".join(bytes.fromhex(item.record_sha256) for item in output)
    )
    output_body = {
        "schema_version": _SCHEMA_VERSION,
        "fixture_set_sha256": _independent_fixture_set_sha256(),
        "request_count": _REQUEST_COUNT,
        "estimand_count": _ESTIMAND_COUNT,
        "estimand_estimate_intervals": output,
    }
    output_payload = _canonical_json_bytes(output_body)
    output_body_sha256 = _sha256(
        b"cp68-test28-estimate-interval-output-body-v1\0" + output_payload
    )
    assert expectation.ordered_estimand_record_sha256s_sha256 == (ordered_record_sha256)
    assert expectation.output_body_sha256 == output_body_sha256
    assert expectation.output_canonical_json_bytes == len(output_payload)
    assert expectation.output_canonical_json_sha256 == _sha256(output_payload)
    assert len(output_payload) <= (
        _bundle().estimate_interval_output_schema.maximum_output_bytes
    )


def test_cp68_exact_family_counts_denominators_estimates_and_intervals() -> None:
    output = _actual_output_records()
    selected_counts = _bundle().synthetic_projection_contract.selected_counts_by_row
    observable = output[:_OBSERVABLE_COUNT]
    attempts = output[_OBSERVABLE_COUNT:_BINOMIAL_COUNT]
    features = output[_BINOMIAL_COUNT:]
    assert all(item.denominator_count == _N for item in observable + attempts)
    assert all(
        type(item.success_count) is int and 0 <= item.success_count <= _N
        for item in observable + attempts
    )
    assert all(
        item.estimate == Fraction(item.success_count, _N)
        for item in observable + attempts
    )
    assert all(item.interval_state == "computed" for item in observable + attempts)
    assert all(
        item.interval_method
        == (
            "clopper-pearson-exact-rational-certified-equivalent-outward-"
            "endpoint-on-2^-256-grid-n2048"
        )
        for item in observable + attempts
    )
    assert all(
        (item.interval_lower, item.interval_upper)
        == cp68.cp68_exact_clopper_pearson_interval_2048(item.success_count)
        for item in observable + attempts
    )

    by_row_observable = {row: [] for row in range(1, 17)}
    by_row_attempt = {row: [] for row in range(1, 17)}
    by_row_features = {row: [] for row in range(1, 17)}
    for item in observable:
        by_row_observable[item.row_ordinal].append(item)
    for item in attempts:
        by_row_attempt[item.row_ordinal].append(item)
    for item in features:
        by_row_features[item.row_ordinal].append(item)

    for row, (_fixture, strategy, budget) in enumerate(_ROW_SHAPES, 1):
        row_observable = by_row_observable[row]
        expected_cells = (
            _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
        )
        assert (
            tuple(item.observable_cell_label for item in row_observable)
            == expected_cells
        )
        assert tuple(item.success_count for item in row_observable) == (
            _expected_observable_counts(row)
        )
        assert sum(item.success_count for item in row_observable) == _N
        row_attempts = by_row_attempt[row]
        if strategy == "bounded-rejection":
            assert len(row_attempts) == budget
            assert tuple(item.success_count for item in row_attempts) == (
                _expected_attempt_counts(selected_counts[row - 1], budget)
            )
            assert (
                sum(item.success_count for item in row_attempts)
                == selected_counts[row - 1]
            )
        else:
            assert row_attempts == []
        row_features = by_row_features[row]
        assert len(row_features) == len(_feature_ids(_ROW_SHAPES[row - 1][0]))
        assert {item.denominator_count for item in row_features} == {
            selected_counts[row - 1]
        }
        roster = _SELECTED_CONFIGURATION_ROSTERS[_fixture]
        configuration = roster[_SELECTED_CONFIGURATION_INDEX_BY_ROW[row - 1]]
        expected_features = dict(_exact_feature_vector(_fixture, configuration))
        assert tuple(item.feature_id for item in row_features) == tuple(
            expected_features
        )
        for item in row_features:
            expected_value = expected_features[item.feature_id]
            if selected_counts[row - 1] == 0:
                assert item.exact_feature_sum is None
                assert item.estimate is None
            else:
                assert item.exact_feature_sum == (
                    selected_counts[row - 1] * expected_value
                )
                assert item.estimate == expected_value

    computed_features = []
    insufficient_features = []
    lower_clipped = upper_clipped = False
    for item in features:
        selected_count = selected_counts[item.row_ordinal - 1]
        assert item.denominator_count == selected_count
        assert item.success_count is None
        assert item.interval_method == (
            "bounded-feature-fixed-range-halfwidth-clipped-to-bounds"
        )
        if selected_count == 0:
            assert item.exact_feature_sum is None
            assert item.estimate is None
        else:
            assert type(item.exact_feature_sum) is Fraction
            assert item.estimate == item.exact_feature_sum / selected_count
            assert item.feature_lower_bound <= item.estimate <= item.feature_upper_bound
        if selected_count < _K_MIN:
            insufficient_features.append(item)
            assert item.interval_state == "insufficient-selection"
            assert item.interval_lower is None
            assert item.interval_upper is None
        else:
            computed_features.append(item)
            expected_interval = _feature_interval(
                item.estimate,
                item.feature_lower_bound,
                item.feature_upper_bound,
                selected_count,
            )
            assert expected_interval is not None
            assert (item.interval_lower, item.interval_upper) == expected_interval
            assert item.interval_state == "computed"
            lower_clipped |= item.interval_lower == item.feature_lower_bound
            upper_clipped |= item.interval_upper == item.feature_upper_bound
    assert len(computed_features) == 156
    assert len(insufficient_features) == 156
    assert lower_clipped is True
    assert upper_clipped is True


def test_cp68_qualification_counts_and_compact_digest_expectation_match() -> None:
    qualification = _qualification()
    expectation = _bundle().aggregation_expectation
    assert qualification.request_count == expectation.request_count == _REQUEST_COUNT
    assert qualification.estimand_count == expectation.estimand_count == _ESTIMAND_COUNT
    assert (
        qualification.binomial_interval_count,
        qualification.feature_interval_count,
        qualification.insufficient_selection_count,
        qualification.computed_interval_count,
    ) == (242, 156, 156, 398)
    assert (
        expectation.binomial_interval_count,
        expectation.feature_interval_count,
        expectation.insufficient_selection_count,
        expectation.computed_interval_count,
    ) == (242, 156, 156, 398)
    assert expectation.selected_counts_by_row == _SELECTED_COUNTS
    for name in (
        "fixture_set_sha256",
        "ordered_projection_sha256",
        "ordered_estimand_record_sha256s_sha256",
        "output_body_sha256",
        "output_canonical_json_bytes",
        "output_canonical_json_sha256",
    ):
        assert getattr(qualification, name) == getattr(expectation, name)
    assert qualification.logical_ordinals_complete is True
    assert qualification.streaming_peak_projection_count == 1
    assert qualification.compact_projection_corpus_retained is False
    assert qualification.observable_row_sums_verified is True
    assert qualification.first_attempt_sums_verified is True
    assert qualification.feature_denominators_verified is True
    assert qualification.cp_zero_endpoint_verified is True
    assert qualification.cp_all_endpoint_verified is True
    assert qualification.cp_256_step_dyadic_endpoints_independently_verified is True
    assert qualification.feature_threshold_verified is True
    assert qualification.feature_clipping_verified is True
    assert qualification.output_matches_frozen_expectation is True
    assert qualification.all_development_qualification_checks_passed is True


def test_cp68_n2048_cp_intervals_match_independent_common_grid_goldens() -> None:
    for success_count, (lower_hex, upper_hex) in _CP_GOLDEN_NUMERATOR_HEX.items():
        expected = (
            Fraction(int(lower_hex, 16), _CP_DENOMINATOR),
            Fraction(int(upper_hex, 16), _CP_DENOMINATOR),
        )
        assert cp68.cp68_exact_clopper_pearson_interval_2048(success_count) == expected


def test_cp68_n2048_exact_cp_zero_and_all_endpoints_have_outward_witnesses() -> None:
    zero_lower, zero_upper = cp68.cp68_exact_clopper_pearson_interval_2048(0)
    all_lower, all_upper = cp68.cp68_exact_clopper_pearson_interval_2048(_N)
    step = Fraction(1, 1 << _CP_STEPS)
    assert all(
        type(value) is Fraction
        for value in (zero_lower, zero_upper, all_lower, all_upper)
    )
    assert zero_lower == 0
    assert all_upper == 1
    assert 0 < zero_upper < 1
    assert 0 < all_lower < 1
    assert zero_upper == 1 - all_lower
    # These direct power witnesses are independent of CP68's tail evaluator.
    assert (1 - zero_upper) ** _N <= _TAIL
    assert (1 - (zero_upper - step)) ** _N > _TAIL
    assert all_lower**_N < _TAIL
    assert (all_lower + step) ** _N >= _TAIL


def test_cp68_n2048_cp_intervals_are_monotone_and_contain_estimates() -> None:
    success_counts = (0, 1, 1_039, 1_040, 1_041, 2_047, 2_048)
    intervals = tuple(
        cp68.cp68_exact_clopper_pearson_interval_2048(value) for value in success_counts
    )
    assert tuple(lower for lower, _upper in intervals) == tuple(
        sorted(lower for lower, _upper in intervals)
    )
    assert tuple(upper for _lower, upper in intervals) == tuple(
        sorted(upper for _lower, upper in intervals)
    )
    for successes, (lower, upper) in zip(success_counts, intervals):
        estimate = Fraction(successes, _N)
        assert 0 <= lower <= estimate <= upper <= 1
    for successes in success_counts:
        lower, upper = intervals[success_counts.index(successes)]
        mirror_lower, mirror_upper = cp68.cp68_exact_clopper_pearson_interval_2048(
            _N - successes
        )
        assert lower == 1 - mirror_upper
        assert upper == 1 - mirror_lower


def test_cp68_n2048_cp_public_surface_rejects_type_and_range_hostiles() -> None:
    for value in (
        None,
        True,
        False,
        _IntSubclass(0),
        0.0,
        "0",
        Fraction(0),
        _ProtocolBomb(),
    ):
        with pytest.raises(TypeError):
            cp68.cp68_exact_clopper_pearson_interval_2048(value)
    for value in (-1, _N + 1, -(1 << 1_000), 1 << 1_000):
        with pytest.raises(ValueError):
            cp68.cp68_exact_clopper_pearson_interval_2048(value)


def test_cp68_cp_endpoint_is_independent_of_untrusted_extreme_proposals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cp68._lower_cp_numerator.cache_clear()
    expected = cp68._lower_cp_numerator(1_040)
    original_compare = cp68._upper_tail_compare
    proposals = (
        0,
        cp68._CP_DENOMINATOR,
        -(1 << 1_000),
        1 << 1_000,
        None,
        True,
        _IntSubclass(0),
        _ProtocolBomb(),
    )
    for proposal in proposals:
        comparisons = []

        def compare(success_count: int, probability_numerator: int) -> int:
            comparisons.append((success_count, probability_numerator))
            return original_compare(success_count, probability_numerator)

        monkeypatch.setattr(
            cp68,
            "_approximate_lower_cp_numerator",
            lambda _success_count, value=proposal: value,
        )
        monkeypatch.setattr(cp68, "_upper_tail_compare", compare)
        cp68._lower_cp_numerator.cache_clear()
        assert cp68._lower_cp_numerator(1_040) == expected
        # The independently recomputed guard is within one grid cell, so exact
        # certification needs only the candidate and its adjacent cell.
        assert 1 <= len(comparisons) <= 4
    cp68._lower_cp_numerator.cache_clear()


def test_cp68_n2048_cp_cache_is_deterministic_and_thread_safe() -> None:
    expected = cp68.cp68_exact_clopper_pearson_interval_2048(1_040)
    with ThreadPoolExecutor(max_workers=8) as executor:
        observed = tuple(
            executor.map(
                cp68.cp68_exact_clopper_pearson_interval_2048,
                (1_040,) * 32,
            )
        )
    assert observed == (expected,) * 32
    assert all(value is expected for value in observed)


def test_cp68_feature_threshold_and_exact_clipping_are_not_off_by_one() -> None:
    helper = cp68._feature_interval
    assert helper(Fraction(1, 2), Fraction(0), Fraction(1), 1_039) is None
    assert helper(Fraction(1, 2), Fraction(0), Fraction(1), 1_040) == (
        Fraction(17, 40),
        Fraction(23, 40),
    )
    assert helper(Fraction(-1), Fraction(-1), Fraction(1), 1_040) == (
        Fraction(-1),
        Fraction(-17, 20),
    )
    assert helper(Fraction(1), Fraction(-1), Fraction(1), 1_040) == (
        Fraction(17, 20),
        Fraction(1),
    )
    assert helper(Fraction(0), Fraction(0), Fraction(0), 1_040) == (
        Fraction(0),
        Fraction(0),
    )


def test_cp68_feature_interval_rejects_type_range_and_bound_hostiles() -> None:
    helper = cp68._feature_interval
    for arguments in (
        (0, Fraction(0), Fraction(1), 1_040),
        (Fraction(0), 0, Fraction(1), 1_040),
        (Fraction(0), Fraction(0), 1, 1_040),
        (Fraction(0), Fraction(0), Fraction(1), True),
        (Fraction(0), Fraction(0), Fraction(1), _IntSubclass(1_040)),
    ):
        with pytest.raises(TypeError):
            helper(*arguments)
    for selected_count in (-1, _N + 1):
        with pytest.raises(ValueError):
            helper(Fraction(0), Fraction(0), Fraction(1), selected_count)
    for mean, lower, upper in (
        (Fraction(-1), Fraction(0), Fraction(1)),
        (Fraction(2), Fraction(0), Fraction(1)),
        (Fraction(0), Fraction(1), Fraction(0)),
    ):
        with pytest.raises(ValueError):
            helper(mean, lower, upper, 1_040)


def test_cp68_private_canonicalizer_fails_closed_on_resource_hostiles() -> None:
    cyclic = {}
    cyclic["self"] = cyclic
    too_deep: object = None
    for _ in range(66):
        too_deep = (too_deep,)
    cases = (
        cyclic,
        too_deep,
        1 << 4_097,
        Fraction(1 << 4_097, 3),
        "x" * 131_073,
        {"x" * 257: None},
    )
    for value in cases:
        with pytest.raises(
            cp68.CP68CompactProjectionAggregationQualificationError
        ) as caught:
            cp68._plain_json_bytes(value)
        assert caught.value.code == "CP68_CANONICAL_RESOURCE_VIOLATION"
    with pytest.raises(
        cp68.CP68CompactProjectionAggregationQualificationError
    ) as caught:
        cp68._plain_json_bytes("0123456789", maximum_bytes=4)
    assert caught.value.code == "CP68_CANONICAL_RESOURCE_VIOLATION"


def test_cp68_private_canonicalizer_does_not_coerce_alien_types() -> None:
    for value in (
        _IntSubclass(1),
        _StrSubclass("x"),
        _TupleSubclass((1,)),
        _ProtocolBomb(),
        {1: "non-string-key"},
    ):
        with pytest.raises(TypeError):
            cp68._plain_json_bytes(value)


def test_cp68_public_runner_fails_whole_on_iterator_infrastructure_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cp68,
        "_iter_synthetic_projections",
        lambda: _failing_projection_stream(),
    )
    issued_before = len(cp68._ISSUED_RECORD_SNAPSHOTS)
    with pytest.raises(
        cp68.CP68CompactProjectionAggregationQualificationError
    ) as caught:
        cp68.cp68_run_compact_projection_aggregation_qualification()
    assert caught.value.code == "CP68_PROJECTION_ITERATION_FAILED"
    assert len(cp68._ISSUED_RECORD_SNAPSHOTS) == issued_before


@pytest.mark.parametrize(
    ("failure", "code"),
    (
        (MemoryError("bounded resource failure"), "CP68_RESOURCE_EXHAUSTED"),
        (RuntimeError("unexpected failure"), "CP68_QUALIFICATION_FAILURE"),
    ),
)
def test_cp68_public_runner_normalizes_resource_and_unexpected_failures(
    monkeypatch: pytest.MonkeyPatch, failure: BaseException, code: str
) -> None:
    def fail() -> object:
        raise failure

    monkeypatch.setattr(cp68, "_run_compact_projection_aggregation_qualification", fail)
    with pytest.raises(
        cp68.CP68CompactProjectionAggregationQualificationError
    ) as caught:
        cp68.cp68_run_compact_projection_aggregation_qualification()
    assert caught.value.code == code


def test_cp68_bundle_and_runner_are_zero_io_and_do_not_import_predecessors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("CP68 attempted forbidden I/O or observation")

    original_import = builtins.__import__

    def guarded_import(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        if name.startswith("heterodiff") or name.startswith(("numpy", "scipy")):
            raise AssertionError("CP68 attempted a project or numerical import")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(cp68, "_BUNDLE_CACHE", None)
    if hasattr(cp68, "_QUALIFICATION_CACHE"):
        monkeypatch.setattr(cp68, "_QUALIFICATION_CACHE", None)
    for owner, names in (
        (os, ("open", "stat", "lstat", "listdir", "scandir", "walk", "fork")),
        (random, ("random", "getrandbits", "randrange")),
        (secrets, ("token_bytes", "token_hex", "randbits")),
        (socket, ("socket", "create_connection")),
        (subprocess, ("run", "Popen", "call", "check_call", "check_output")),
        (time, ("time", "time_ns", "monotonic", "perf_counter", "sleep")),
    ):
        for name in names:
            if hasattr(owner, name):
                monkeypatch.setattr(owner, name, forbidden)
    bundle = _bundle()
    qualification = _qualification()
    assert bundle.schema_version == _SCHEMA_VERSION
    assert qualification.schema_version == _SCHEMA_VERSION
    assert qualification.request_count == _REQUEST_COUNT


def test_cp68_source_has_no_hidden_project_numeric_or_io_imports() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, feature_version=(3, 9))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    assert all(
        not name.startswith(("heterodiff", "numpy", "scipy")) for name in imported
    )
    assert not (
        {"os", "pathlib", "random", "secrets", "socket", "subprocess", "time"}
        & set(imported)
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not ({"open", "eval", "exec", "compile", "input"} & called_names)
    assert "__file__" not in source


def test_cp68_fresh_module_execution_performs_no_host_io_or_project_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    code = compile(source, str(_SOURCE), "exec")
    original_import = builtins.__import__

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("CP68 import attempted forbidden host observation")

    def guarded_import(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        if name.startswith(("heterodiff", "numpy", "scipy")):
            raise AssertionError("CP68 import attempted a project/numeric import")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    for owner, names in (
        (os, ("open", "stat", "lstat", "listdir", "scandir", "walk", "fork")),
        (random, ("random", "getrandbits", "randrange")),
        (secrets, ("token_bytes", "token_hex", "randbits")),
        (socket, ("socket", "create_connection")),
        (subprocess, ("run", "Popen", "call", "check_call", "check_output")),
        (time, ("time", "time_ns", "monotonic", "perf_counter", "sleep")),
    ):
        for name in names:
            if hasattr(owner, name):
                monkeypatch.setattr(owner, name, forbidden)
    module_name = "heterodiff.evaluation._cp68_hostile_fresh_import"
    module = types.ModuleType(module_name)
    module.__file__ = str(_SOURCE)
    module.__package__ = "heterodiff.evaluation"
    sys.modules[module_name] = module
    try:
        exec(code, module.__dict__)
    finally:
        del sys.modules[module_name]
    assert module.CP68_TEST28_REQUEST_COUNT == _REQUEST_COUNT


def test_cp68_records_are_sealed_nonconstructible_and_nonpickleable() -> None:
    bundle = _bundle()
    records = (
        bundle.predecessor_custody,
        bundle.synthetic_projection_contract,
        bundle.estimate_interval_output_schema,
        bundle.aggregation_expectation,
        bundle,
        _actual_output_records()[0],
        _qualification(),
    )
    for record in records:
        cls = type(record)
        assert is_dataclass(record)
        with pytest.raises(TypeError):
            cls()
        with pytest.raises(TypeError):
            type("Hostile" + cls.__name__, (cls,), {})
        with pytest.raises(TypeError):
            pickle.dumps(record)
        reference = weakref.ref(record)
        assert reference() is record


def test_cp68_forged_and_tampered_public_records_are_rejected() -> None:
    bundle = _bundle()
    output = _actual_output_records()[0]
    qualification = _qualification()
    cases = (
        _forge(bundle.predecessor_custody, record_sha256=_ZERO_SHA256),
        _forge(bundle.synthetic_projection_contract, request_count=_REQUEST_COUNT - 1),
        _forge(bundle.estimate_interval_output_schema, decision_fields_present=True),
        _forge(bundle.aggregation_expectation, request_count=_REQUEST_COUNT - 1),
        _forge(bundle, record_sha256=_ZERO_SHA256),
        _forge(output, development_fixture_only=False),
        _forge(qualification, production_evidence=True),
    )
    for forged in cases:
        with pytest.raises(
            (
                TypeError,
                ValueError,
                cp68.CP68CompactProjectionAggregationQualificationError,
            )
        ):
            cp68.cp68_canonical_json_bytes(forged)
        with pytest.raises(
            (
                TypeError,
                ValueError,
                cp68.CP68CompactProjectionAggregationQualificationError,
            )
        ):
            cp68.cp68_sha256(forged)


def test_cp68_public_canonical_bytes_and_hashes_are_deterministic() -> None:
    bundle = _bundle()
    qualification = _qualification()
    for record in (bundle, qualification, _actual_output_records()[0]):
        first = cp68.cp68_canonical_json_bytes(record)
        second = cp68.cp68_canonical_json_bytes(record)
        assert first == second == _canonical_json_bytes(record)
        public_sha256 = _sha256(
            b"cp68-public-record-v1\0"
            + type(record).__name__.encode("ascii")
            + b"\0"
            + first
        )
        assert cp68.cp68_sha256(record) == public_sha256
        assert len(public_sha256) == 64
        int(public_sha256, 16)
    for alien in (None, True, 1, "x", {}, (), _ProtocolBomb()):
        with pytest.raises(TypeError):
            cp68.cp68_canonical_json_bytes(alien)
        with pytest.raises(TypeError):
            cp68.cp68_sha256(alien)


def test_cp68_every_issued_record_has_the_independent_domain_digest() -> None:
    bundle = _bundle()
    qualification = _qualification()
    records = (
        bundle.predecessor_custody,
        bundle.synthetic_projection_contract,
        bundle.estimate_interval_output_schema,
        bundle.aggregation_expectation,
        bundle,
        qualification,
    ) + _actual_output_records()
    assert len(records) == _ESTIMAND_COUNT + 6
    for record in records:
        assert record.record_sha256 == _independent_record_sha256(record)


def test_cp68_bundle_and_qualification_are_concurrently_deterministic() -> None:
    bundle = _bundle()
    assert _bundle() is bundle
    expected_bundle = cp68.cp68_canonical_json_bytes(bundle)
    expected_qualification = cp68.cp68_canonical_json_bytes(_qualification())

    def observe(_index: int) -> tuple[bytes, bytes]:
        return (
            cp68.cp68_canonical_json_bytes(_bundle()),
            cp68.cp68_canonical_json_bytes(_qualification()),
        )

    with ThreadPoolExecutor(max_workers=4) as executor:
        observed = tuple(executor.map(observe, range(4)))
    assert observed == ((expected_bundle, expected_qualification),) * 4


def test_cp68_nonclaims_leave_all_production_boundaries_fail_closed() -> None:
    bundle = _bundle()
    qualification = _qualification()
    assert qualification.raw_or_stable_recomputation_performed is False
    assert qualification.decision_path_qualified is False
    assert qualification.production_evidence is False
    assert qualification.production_execution_authorized is False
    assert qualification.runner_and_recomputation_blocker_closed is False
    assert qualification.formal_test_28_closed is False
    assert bundle.formal_test_28_status == "OPEN"
    assert bundle.formal_test_28_closed is False
    assert bundle.ledger_total_count == 23
    assert bundle.ledger_satisfied_count == 19
    assert bundle.ledger_missing_count == 4
    assert bundle.ledger_prerequisite_state == (
        "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_ARTIFACTS"
    )
    assert bundle.zero_argument_builder is True
    assert bundle.builder_streams_or_aggregates is False
    assert bundle.qualification_runner_zero_argument is True
    assert bundle.closed_module_owned_fixture_only is True
    assert bundle.bounded_exact_cp2048_api_exposed is True
    assert bundle.stdlib_only_import is True
    assert bundle.streaming_aggregation is True
    assert bundle.development_qualification_only is True
    for name in (
        "project_modules_imported_by_builder",
        "predecessor_modules_lazy_imported_by_qualification_runner",
        "full_projection_corpus_materialized",
        "host_filesystem_probed",
        "clock_read",
        "rng_used",
        "network_used",
        "subprocess_api_exposed",
        "filesystem_path_api_exposed",
        "generic_projection_api_exposed",
        "raw_record_api_exposed",
        "stable_trace_api_exposed",
        "production_recomputation_api_exposed",
        "production_estimate_or_interval",
        "decision_path_qualified",
        "production_qualification_receipt_present",
        "production_gate_13_evidence_present",
        "production_gate_14_evidence_present",
        "production_execution_authorized",
        "production_execution_observed",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_and_thresholds_blocker_closed",
        "confirmatory_custody_blocker_closed",
        "confirmatory_evidence",
        "manuscript_claim",
    ):
        assert getattr(bundle, name) is False, name
    assert bundle.production_gate_13_state == "MISSING"
    assert bundle.production_gate_14_state == "MISSING"


def test_cp68_source_and_bundle_remain_python39_compatible() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, feature_version=(3, 9))
    assert isinstance(tree, ast.Module)
    assert "dataclass(slots=True" not in source.replace(" ", "")
    match_node = getattr(ast, "Match", ())
    assert all(not isinstance(node, match_node) for node in ast.walk(tree))
    assert "except*" not in source
    assert (
        cp68.cp68_compact_projection_aggregation_qualification_bundle().schema_version
        == _SCHEMA_VERSION
    )
