"""Independent hostile tests for the development-only CP69 interchange."""

from __future__ import annotations

import ast
import builtins
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, is_dataclass
from fractions import Fraction
from functools import lru_cache
import hashlib
import inspect
import json
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

import heterodiff.evaluation.mixed_initializer_test28_compact_projection_aggregation_qualification as cp68
import heterodiff.evaluation.mixed_initializer_test28_compact_projection_interchange_qualification as cp69
import heterodiff.evaluation.mixed_initializer_test28_independent_recomputation as cp63i
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_compact_projection_interchange_qualification.py"
)
_V19_PROTOCOL = _ROOT / "research/preregistrations/cp50_test28_mixed_initializer_v19.md"
_V19_MANIFEST = _ROOT / "research/fixtures/cp50_test28_mixed_initializer_v19.json"

_SCHEMA = "cp69-test28-compact-projection-interchange-qualification-v1"
_CP63_SCHEMA = "cp63-test28-independent-compact-recomputation-v1"
_CP68_SCHEMA = "cp68-test28-compact-projection-aggregation-qualification-v1"
_ZERO_SHA256 = "0" * 64
_N = 2_048
_ROW_COUNT = 16
_REQUEST_COUNT = 32_768
_OBSERVABLE_COUNT = 72
_FIRST_ATTEMPT_COUNT = 170
_FEATURE_COUNT = 312
_ESTIMAND_COUNT = 554
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
_ROW_SHAPES = tuple(
    (fixture, strategy, budget)
    for fixture in ("T28-M1-Q", "T28-M2-Q")
    for strategy, budgets in (
        ("bounded-rejection", (1, 4, 16, 64)),
        ("fixed-budget-sir", (8, 32, 128, 512)),
    )
    for budget in budgets
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
    "T28-M1-Q": (
        (),
        ((0, ()),),
        ((1, (Fraction(1),)),),
    ),
    "T28-M2-Q": (
        (),
        ((0, (Fraction(1, 2),)),),
        ((1, (Fraction(0), Fraction(1, 2))),),
        (
            (0, (Fraction(-1, 2),)),
            (1, (Fraction(1, 2), Fraction(-1, 2))),
        ),
    ),
}
_V19_PROTOCOL_SHA256 = (
    "38558ba7f67f56fb21aa6974ee9a932350ffb703d47fc6b972e22b322a444d08"
)
_V19_MANIFEST_SHA256 = (
    "3649c90d3d1ddffa9edae27625246c0f97399c7c60319a5c09d7fa20b365b1ae"
)
_CP68_FIRST_PROJECTION_SHA256 = (
    "b40854463d8f441614621319f2e7a774059cd757d75284750906f84222744796"
)
_CP68_ORDERED_PROJECTION_SHA256 = (
    "f898741b035d59116f6e096a1deab6c642f83dd3ad0417b7995e182584731f42"
)
_CP68_OUTPUT_SHA256 = "f9e1bf93354af057d08ca722d2cffe1a8188d2f1e823a0173f9b6a937ddc42c3"
_CP68_FIXTURE_SET_SHA256 = (
    "6b8d7db706b94c32ee53efe9969e16560997e0f7b2345960e44ad4f18feb49ce"
)
_CP69_FIXTURE_SET_SHA256 = (
    "95a388b634e208b8d7b578a18657289390fe9306e23a4e5ecb3ed084771a8303"
)
_CP69_FIRST_INPUT_SHA256 = (
    "de2237dfb851b4370d25cfa9b72698a73d6ea4c1c4f70b654f509999ecec34b8"
)
_CP69_ORDERED_INPUT_SHA256 = (
    "754b058697dc9324611152b4987925a414520fc98dd764571321c3135d0ecc8d"
)
_DEVELOPMENT_RUNTIME_LOCK_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
)
_SEED_FREE_REQUEST_SHA256S = (
    "a99bafb93499e89d054dd8e0df8c9a04acff29142620a7da374aa88dae53215a",
    "f9f2d4f1d8aad14bbe5075b4febd763af4652fb4dda337e7a8d295b3a6045ec2",
    "4413d707c0165dbf18e88df043edd760a75d4eed44d039a611402e06de9c4eb8",
    "29f1f28fb222d258746cb7956a9ca0d65a6e97d398eddb1612720a9339eed338",
    "71701768f889fee219b854217de255f3d034202a3a66875ceade1cd55955896a",
    "bd7c4fd661bda70f29b8582c0db52d91d68fc703ae8838295a21cf9e6e55f23a",
    "801f600536240a2f6f3de0dcac8d4092c2121fd17dc14fb0ca0bfc3b0260acb8",
    "8e5458a8dfca1e49875cad53deff7447274ce3055960a0031cc07c4ec4de33e0",
    "7d32b4e85d39504864268b7ba39189f17c3171d11079638e37a6614b97a543bf",
    "17f11b448585709ef35a172e86665c83b2ea50a907caacdd400dbd8ce625771b",
    "57937405e7302fcd9b9935050050a74e4b2c2818e17d720cde1ee2a56352bcf3",
    "878797b61ec628ae5db0e882d6f3c34531468fbbc35fd92325063a3b017c1bd8",
    "bc7b374f072aa402264634bcf520834a71609af5f6705b9b8ac3079884cd0376",
    "1b60b917c4fba30085678101276fe2a210aaa82f34deb6ad4f9440a38cc3b074",
    "a88491906e47ec4f5483b638ce411b8afd4ce7b5d73f19e372ab68a405f6d81c",
    "0667c6c19a9b54db91f2167f685abdcaafcab73cbc4bcfaebcb420511ecc89c8",
)
_INPUT_KEYS = (
    "schema_version",
    "source_semantic_schema_version",
    "seed_ordinal",
    "row_ordinal",
    "logical_request_ordinal",
    "row_key",
    "fixture_id",
    "strategy",
    "budget",
    "plan_seed_hex",
    "seed_free_request_sha256",
    "request_instance_sha256",
    "runtime_lock_sha256",
    "stable_trace_sha256",
    "observable_cell_label",
    "observable_contribution_ordinal",
    "first_selected_attempt_one_based",
    "selected",
    "selected_feature_ids",
    "selected_feature_values",
    "record_sha256",
)
_VIEW_KEYS = (
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
    "CP69PredecessorCustodyV1": b"cp69-test28-predecessor-custody-v1",
    "CP69CompactInterchangeContractV1": (
        b"cp69-test28-compact-interchange-contract-v1"
    ),
    "CP69CompactInterchangeObservationV1": (
        b"cp69-test28-compact-interchange-observation-v1"
    ),
    "CP69CP68ProjectionViewV1": b"cp68-test28-synthetic-compact-projection-v1",
    "CP69FullStreamExpectationV1": b"cp69-test28-full-stream-expectation-v1",
    "CP69CompactProjectionInterchangeQualificationV1": (
        b"cp69-test28-compact-projection-interchange-qualification-v1"
    ),
    "CP69CompactProjectionInterchangeQualificationBundleV1": (
        b"cp69-test28-compact-projection-interchange-qualification-bundle-v1"
    ),
}


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is Fraction:
        return {"$fraction": [str(value.numerator), str(value.denominator)]}
    if type(value) is tuple:
        return [_canonical(item) for item in value]
    if type(value) is list:
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


def _expected_status(seed_ordinal: int, row_ordinal: int) -> tuple[str, object, bool]:
    _fixture, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
    selected_count = _SELECTED_COUNTS[row_ordinal - 1]
    if seed_ordinal <= selected_count:
        if strategy == "bounded-rejection":
            return (
                _REJECTION_CELLS[0],
                (seed_ordinal - 1) % budget + 1,
                True,
            )
        return _SIR_CELLS[0], None, True
    offset = seed_ordinal - selected_count - 1
    if strategy == "bounded-rejection":
        return _REJECTION_CELLS[1 + offset % 4], None, False
    return _SIR_CELLS[1 + offset % 3], None, False


def _observable_contribution_ordinal(row_ordinal: int, cell: str) -> int:
    prior = 0
    for candidate in range(1, row_ordinal):
        strategy = _ROW_SHAPES[candidate - 1][1]
        prior += len(
            _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
        )
    strategy = _ROW_SHAPES[row_ordinal - 1][1]
    cells = _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
    return prior + cells.index(cell) + 1


def _projection_specs(
    fixture_id: str,
) -> tuple[tuple[int, str, tuple[Fraction, ...]], ...]:
    if fixture_id == "T28-M1-Q":
        return ((1, "axis0", (Fraction(1),)),)
    return (
        (0, "axis0", (Fraction(1),)),
        (1, "axis0", (Fraction(1), Fraction(0))),
        (1, "axis1", (Fraction(0), Fraction(1))),
        (1, "diag-plus-3-4", (Fraction(3, 5), Fraction(4, 5))),
        (1, "diag-minus-3-4", (Fraction(3, 5), Fraction(-4, 5))),
    )


def _feature_ids(fixture_id: str) -> tuple[str, ...]:
    cap = 1 if fixture_id == "T28-M1-Q" else 2
    dimensions = (0, 1) if fixture_id == "T28-M1-Q" else (1, 2)
    projections = tuple(
        (event_type, projection_id)
        for event_type, projection_id, _coefficients in _projection_specs(fixture_id)
    )
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


def _odd(value: Fraction) -> Fraction:
    return max(Fraction(-1), min(Fraction(1), value))


def _even(value: Fraction) -> Fraction:
    return Fraction(1) if abs(value) >= 1 else value * value


def _project(
    event: tuple[int, tuple[Fraction, ...]], coefficients: tuple[Fraction, ...]
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
    cap = 1 if fixture_id == "T28-M1-Q" else 2
    dimensions = (0, 1) if fixture_id == "T28-M1-Q" else (1, 2)
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
            Fraction(sum(1 for event in configuration if event[0] == event_type), cap)
        )
    for event_type, _projection_id, coefficients in projections:
        projected = tuple(
            _project(event, coefficients)
            for event in configuration
            if event[0] == event_type
        )
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
    assert len(feature_ids) == len(values)
    return tuple(zip(feature_ids, values))


@lru_cache(maxsize=32)
def _expected_features(
    row_ordinal: int, selected: bool
) -> tuple[tuple[str, Fraction], ...]:
    if not selected:
        return ()
    fixture = _ROW_SHAPES[row_ordinal - 1][0]
    configuration = _SELECTED_CONFIGURATION_ROSTERS[fixture][
        _SELECTED_CONFIGURATION_INDEX_BY_ROW[row_ordinal - 1]
    ]
    return _exact_feature_vector(fixture, configuration)


def _independent_fixture_set_sha256() -> str:
    payload = {
        "schema_version": _SCHEMA,
        "source_semantic_schema_version": _CP63_SCHEMA,
        "target_projection_schema_version": _CP68_SCHEMA,
        "seed_count": _N,
        "row_count": _ROW_COUNT,
        "request_count": _REQUEST_COUNT,
        "row_shapes": _ROW_SHAPES,
        "rejection_observable_cells": _REJECTION_CELLS,
        "sir_observable_cells": _SIR_CELLS,
        "selected_counts_by_row": _SELECTED_COUNTS,
        "selected_configuration_index_by_row": (_SELECTED_CONFIGURATION_INDEX_BY_ROW),
        "m1_selected_configuration_roster": _SELECTED_CONFIGURATION_ROSTERS["T28-M1-Q"],
        "m2_selected_configuration_roster": _SELECTED_CONFIGURATION_ROSTERS["T28-M2-Q"],
        "m1_feature_ids": _feature_ids("T28-M1-Q"),
        "m2_feature_ids": _feature_ids("T28-M2-Q"),
        "interchange_keys": _INPUT_KEYS,
        "target_projection_keys": _VIEW_KEYS,
        "seed_free_request_sha256s": _SEED_FREE_REQUEST_SHA256S,
        "development_runtime_lock_sha256": _DEVELOPMENT_RUNTIME_LOCK_SHA256,
        "closed_fixture_plan_seed_formula": "lowercase-16-hex(seed_ordinal-1)",
        "request_custody_is_synthetic_sentinel": True,
        "stable_trace_custody_is_synthetic_no-trace-sentinel": True,
        "provenance_authenticated": False,
        "cp68_fixture_set_sha256": _CP68_FIXTURE_SET_SHA256,
        "cp68_ordered_projection_sha256": _CP68_ORDERED_PROJECTION_SHA256,
    }
    return _sha256(
        b"cp69-test28-compact-interchange-fixture-set-v1\0"
        + _canonical_json_bytes(payload)
    )


class _ProtocolBomb:
    def __getattribute__(self, name: str) -> object:
        raise AssertionError("alien protocol accessed: %s" % name)


class _IntSubclass(int):
    pass


class _StrSubclass(str):
    pass


class _IterableBomb:
    def __iter__(self) -> object:
        raise RuntimeError("iterator bomb")


class _BoundaryFailureSource:
    def __init__(self, boundary: str, failure: BaseException, first: bytes) -> None:
        self.boundary = boundary
        self.failure = failure
        self.first = first
        self.iter_calls = 0
        self.next_calls = 0

    def __iter__(self) -> object:
        self.iter_calls += 1
        if self.boundary == "iter":
            raise self.failure
        return self

    def __next__(self) -> bytes:
        self.next_calls += 1
        if self.boundary == "item":
            raise self.failure
        if self.boundary == "terminal":
            if self.next_calls == 1:
                return self.first
            raise self.failure
        raise AssertionError("unknown iterator failure boundary")


def _decode_exact(payload: bytes) -> dict:
    return json.loads(payload.decode("ascii"))


def _retag_input(body: dict) -> bytes:
    mutable = dict(body)
    mutable["record_sha256"] = _ZERO_SHA256
    mutable["record_sha256"] = _sha256(
        b"cp69-test28-compact-interchange-observation-v1\0"
        + _canonical_json_bytes(mutable)
    )
    return _canonical_json_bytes(mutable)


def _mutated_closed_payload(
    base_seed_ordinal: int = 1,
    base_row_ordinal: int = 1,
    *,
    changes: object = None,
    retag: bool = True,
) -> bytes:
    raw = _decode_exact(
        cp69._closed_interchange_bytes(base_seed_ordinal, base_row_ordinal)
    )
    if changes is not None:
        raw.update(changes)
    return _retag_input(raw) if retag else _canonical_json_bytes(raw)


def _parse_error_code(payload: object) -> str:
    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69.cp69_parse_compact_interchange_bytes(payload)
    return caught.value.code


def _independent_record_sha256(record: object) -> str:
    digest_field = (
        "projection_sha256"
        if type(record).__name__ == "CP69CP68ProjectionViewV1"
        else "record_sha256"
    )
    if type(record).__name__ == "CP69CP68ProjectionViewV1":
        body = {
            item.name: getattr(record, item.name)
            for item in fields(type(record))
            if item.name != digest_field
        }
    else:
        body = {
            item.name: (
                _ZERO_SHA256
                if item.name == digest_field
                else getattr(record, item.name)
            )
            for item in fields(type(record))
        }
    return _sha256(
        _RECORD_DOMAINS[type(record).__name__] + b"\0" + _canonical_json_bytes(body)
    )


def _forge(record: object, **changes: object) -> object:
    forged = object.__new__(type(record))
    for item in fields(type(record)):
        object.__setattr__(
            forged,
            item.name,
            changes.get(item.name, getattr(record, item.name)),
        )
    return forged


def _assert_sha256(value: object) -> None:
    assert type(value) is str
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def _issued_registry_snapshot() -> tuple[tuple[int, str, bytes], ...]:
    with cp69._ISSUED_RECORD_LOCK:
        return tuple(
            sorted(
                (id(record), type(record).__name__, snapshot)
                for record, snapshot in cp69._ISSUED_RECORD_SNAPSHOTS.items()
            )
        )


def _cache_population_snapshot() -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (info.maxsize, info.currsize, info.misses)
        for info in (
            cp69.cp69_compact_interchange_fixture_set_sha256.cache_info(),
            cp69._row_feature_items.cache_info(),
        )
    )


@lru_cache(maxsize=1)
def _bundle() -> object:
    return cp69.cp69_compact_projection_interchange_qualification_bundle()


@lru_cache(maxsize=1)
def _qualification() -> object:
    return cp69.cp69_run_compact_projection_interchange_qualification()


@lru_cache(maxsize=1)
def _live_cp63_compact_anchors() -> tuple[object, ...]:
    """Execute one fresh CP63 row set without consuming its imported counters."""

    runner_path = (
        _ROOT
        / "src"
        / "heterodiff"
        / "evaluation"
        / "mixed_initializer_test28_runner_recomputation_rehearsal.py"
    )
    module_name = "heterodiff.evaluation._cp69_fresh_cp63_anchor_runner"
    module = types.ModuleType(module_name)
    module.__file__ = str(runner_path)
    module.__package__ = "heterodiff.evaluation"
    sys.modules[module_name] = module
    try:
        exec(
            compile(runner_path.read_bytes(), str(runner_path), "exec"), module.__dict__
        )
        cases = module.cp63_runner_recomputation_rehearsal_bundle().rehearsal_cases
        result = []
        for case in cases:
            raw_payload = module.cp63_run_rehearsal_case(case.case_id)
            stable = module.cp63_project_stable_trace(raw_payload)
            stable_payload = module.cp63_stable_trace_canonical_json_bytes(stable)
            result.append(cp63i.cp63_compact_observation(stable_payload))
        return tuple(result)
    finally:
        del sys.modules[module_name]


def _cp69_values_from_cp63(observation: object) -> dict:
    return {
        "schema_version": _SCHEMA,
        "source_semantic_schema_version": observation.schema_version,
        "seed_ordinal": observation.seed_ordinal,
        "row_ordinal": observation.row_ordinal,
        "logical_request_ordinal": observation.logical_request_ordinal,
        "row_key": observation.row_key,
        "fixture_id": observation.fixture_id,
        "strategy": observation.strategy,
        "budget": observation.budget,
        "plan_seed_hex": observation.plan_seed_hex,
        "seed_free_request_sha256": observation.seed_free_request_sha256,
        "request_instance_sha256": observation.request_instance_sha256,
        "runtime_lock_sha256": observation.runtime_lock_sha256,
        "stable_trace_sha256": observation.stable_trace_sha256,
        "observable_cell_label": observation.observable_cell_label,
        "observable_contribution_ordinal": (
            observation.observable_contribution_ordinal
        ),
        "first_selected_attempt_one_based": (
            observation.first_selected_attempt_one_based
        ),
        "selected": observation.selected,
        "selected_feature_ids": observation.selected_feature_ids,
        "selected_feature_values": observation.selected_feature_values,
    }


@lru_cache(maxsize=1)
def _full_stream_oracle() -> dict:
    ordered_input = hashlib.sha256(
        b"cp69-test28-ordered-interchange-record-digests-v1\0"
    )
    statuses = Counter()
    selected_by_row = [0] * 16
    first_attempt_count = 0
    feature_count = 0
    first_input_digest = None
    total_bytes = 0

    def projection_stream() -> object:
        nonlocal first_attempt_count, feature_count, first_input_digest, total_bytes
        for seed_ordinal in range(1, _N + 1):
            for row_ordinal in range(1, _ROW_COUNT + 1):
                logical = (seed_ordinal - 1) * _ROW_COUNT + row_ordinal
                payload = cp69._closed_interchange_bytes(seed_ordinal, row_ordinal)
                assert type(payload) is bytes
                assert 0 < len(payload) <= cp69.CP69_TEST28_MAXIMUM_INTERCHANGE_BYTES
                total_bytes += len(payload)
                assert total_bytes <= cp69.CP69_TEST28_MAXIMUM_STREAM_BYTES
                raw = _decode_exact(payload)
                assert tuple(raw) == tuple(sorted(raw))
                assert tuple(sorted(raw)) == tuple(sorted(_INPUT_KEYS))
                assert payload == _canonical_json_bytes(raw)
                fixture, strategy, budget = _ROW_SHAPES[row_ordinal - 1]
                status, first_attempt, selected = _expected_status(
                    seed_ordinal, row_ordinal
                )
                feature_items = _expected_features(row_ordinal, selected)
                exact_expected = {
                    "schema_version": _SCHEMA,
                    "source_semantic_schema_version": _CP63_SCHEMA,
                    "seed_ordinal": seed_ordinal,
                    "row_ordinal": row_ordinal,
                    "logical_request_ordinal": logical,
                    "row_key": _row_key(row_ordinal),
                    "fixture_id": fixture,
                    "strategy": strategy,
                    "budget": budget,
                    "plan_seed_hex": "%016x" % (seed_ordinal - 1),
                    "observable_cell_label": status,
                    "observable_contribution_ordinal": (
                        _observable_contribution_ordinal(row_ordinal, status)
                    ),
                    "first_selected_attempt_one_based": first_attempt,
                    "selected": selected,
                    "selected_feature_ids": [item[0] for item in feature_items],
                    "selected_feature_values": _canonical(
                        tuple(item[1] for item in feature_items)
                    ),
                }
                for name, expected in exact_expected.items():
                    assert raw[name] == expected, (logical, name)
                for name in (
                    "seed_free_request_sha256",
                    "request_instance_sha256",
                    "runtime_lock_sha256",
                    "stable_trace_sha256",
                    "record_sha256",
                ):
                    _assert_sha256(raw[name])
                assert raw["seed_free_request_sha256"] == (
                    _SEED_FREE_REQUEST_SHA256S[row_ordinal - 1]
                )
                assert raw["runtime_lock_sha256"] == (_DEVELOPMENT_RUNTIME_LOCK_SHA256)
                request_identity = {
                    "purpose": (
                        "cp69-synthetic-transport-request-custody-sentinel-only"
                    ),
                    "seed_ordinal": seed_ordinal,
                    "row_ordinal": row_ordinal,
                    "logical_request_ordinal": logical,
                    "plan_seed_hex": "%016x" % (seed_ordinal - 1),
                    "seed_free_request_sha256": (
                        _SEED_FREE_REQUEST_SHA256S[row_ordinal - 1]
                    ),
                }
                assert raw["request_instance_sha256"] == _sha256(
                    b"cp69-test28-synthetic-request-instance-custody-sentinel-v1\0"
                    + _canonical_json_bytes(request_identity)
                )
                assert raw["stable_trace_sha256"] == _sha256(
                    b"cp69-test28-no-stable-trace-synthetic-custody-sentinel-v1\0"
                    + _canonical_json_bytes(
                        {
                            "purpose": "no-stable-trace-present-or-claimed",
                            "request_instance_sha256": raw["request_instance_sha256"],
                            "observable_cell_label": status,
                            "first_selected_attempt_one_based": first_attempt,
                        }
                    )
                )
                assert raw["record_sha256"] == _sha256(
                    b"cp69-test28-compact-interchange-observation-v1\0"
                    + _canonical_json_bytes({**raw, "record_sha256": _ZERO_SHA256})
                )
                observation = cp69.cp69_parse_compact_interchange_bytes(payload)
                assert observation.record_sha256 == raw["record_sha256"]
                assert cp69.cp69_canonical_json_bytes(observation) == payload
                view = cp69.cp69_to_cp68_projection_view(observation)
                assert tuple(item.name for item in fields(type(view))) == _VIEW_KEYS
                assert view.schema_version == _CP68_SCHEMA
                assert view.projection_sha256 == _independent_record_sha256(view)
                copied = (
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
                )
                for name in copied:
                    assert getattr(view, name) == getattr(observation, name), (
                        logical,
                        name,
                    )
                if logical == 1:
                    first_input_digest = observation.record_sha256
                    assert view.projection_sha256 == _CP68_FIRST_PROJECTION_SHA256
                ordered_input.update(bytes.fromhex(observation.record_sha256))
                statuses[status] += 1
                if selected:
                    selected_by_row[row_ordinal - 1] += 1
                    feature_count += len(feature_items)
                if first_attempt is not None:
                    first_attempt_count += 1
                yield {
                    item.name: getattr(view, item.name) for item in fields(type(view))
                }

    outputs, cp68_metrics = cp68._aggregate_closed_fixture_details(projection_stream())
    assert len(outputs) == _ESTIMAND_COUNT
    return {
        "first_input_digest": first_input_digest,
        "ordered_input_digest": ordered_input.hexdigest(),
        "statuses": statuses,
        "selected_by_row": tuple(selected_by_row),
        "first_attempt_count": first_attempt_count,
        "feature_count": feature_count,
        "total_bytes": total_bytes,
        "cp68_metrics": cp68_metrics,
    }


def test_cp69_live_v19_and_predecessor_pins_are_exact() -> None:
    for path, expected_sha, expected_bytes, expected_lf in (
        (_V19_PROTOCOL, _V19_PROTOCOL_SHA256, 174_492, 3_019),
        (_V19_MANIFEST, _V19_MANIFEST_SHA256, 6_059_388, 119_095),
    ):
        payload = path.read_bytes()
        assert _sha256(payload) == expected_sha
        assert len(payload) == expected_bytes
        assert payload.count(b"\n") == expected_lf
        assert payload.endswith(b"\n")

    custody = _bundle().predecessor_custody
    assert custody.v19_protocol_sha256 == _V19_PROTOCOL_SHA256
    assert custody.v19_manifest_sha256 == _V19_MANIFEST_SHA256
    assert custody.cp63_independent_source_sha256 == (
        "5df076a008d8fe6848dc72083e2563e622c136ce0159441dd69db04c3b1cb9dc"
    )
    assert custody.cp63_independent_bundle_record_sha256 == (
        "b219de24a17af7c06b503af07110ed863c339bca19c7457c163412ae0e76ddb9"
    )
    assert custody.cp63_schedule_contract_record_sha256 == (
        "7ca5555de1aa852021c6b7fd181417a629dcec461455650ecafc495f5e6fb607"
    )
    assert custody.cp68_source_sha256 == (
        "15afd7e4a8fb99c137faea8d57ef2bd2dc3ab3c193481883da4e205b75c16555"
    )
    assert custody.cp68_test_sha256 == (
        "5587785ad8c5fc3ac526758ce87ad91acbb5b4e1532563ceacc2e1c8d64f32e4"
    )
    assert custody.cp68_bundle_record_sha256 == (
        "b301ea4cadb8a67fa238dfa5872c874b4689a08b7baec04f1133bef7191a2a83"
    )
    assert custody.cp68_ordered_projection_sha256 == _CP68_ORDERED_PROJECTION_SHA256
    assert custody.cp68_output_canonical_json_sha256 == _CP68_OUTPUT_SHA256


def test_cp69_frozen_counts_caps_and_public_signatures_are_exact() -> None:
    assert cp69.CP69_TEST28_SCHEMA_VERSION == _SCHEMA
    assert cp69.CP69_TEST28_FORMAL_TEST_28_STATUS == "OPEN"
    assert (
        cp69.CP69_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID
        == "whole_seed_cp63_compact_semantics_to_cp68_projection_interchange_qualification"
    )
    assert (
        cp69.CP69_TEST28_SEED_COUNT,
        cp69.CP69_TEST28_ROW_COUNT,
        cp69.CP69_TEST28_REQUEST_COUNT,
    ) == (_N, _ROW_COUNT, _REQUEST_COUNT)
    assert (
        cp69.CP69_TEST28_OBSERVABLE_ESTIMAND_COUNT,
        cp69.CP69_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT,
        cp69.CP69_TEST28_FEATURE_ESTIMAND_COUNT,
        cp69.CP69_TEST28_ESTIMAND_COUNT,
    ) == (_OBSERVABLE_COUNT, _FIRST_ATTEMPT_COUNT, _FEATURE_COUNT, _ESTIMAND_COUNT)
    assert cp69.CP69_TEST28_SELECTED_COUNTS_BY_ROW == _SELECTED_COUNTS
    assert (
        cp69.CP69_TEST28_MAXIMUM_INTERCHANGE_BYTES,
        cp69.CP69_TEST28_MAXIMUM_CANONICAL_DEPTH,
        cp69.CP69_TEST28_MAXIMUM_CANONICAL_NODES,
        cp69.CP69_TEST28_MAXIMUM_TEXT_BYTES,
        cp69.CP69_TEST28_MAXIMUM_INTEGER_BITS,
        cp69.CP69_TEST28_MAXIMUM_STREAM_BYTES,
    ) == (65_536, 16, 512, 4_096, 256, 2_147_483_648)
    assert tuple(
        inspect.signature(cp69.cp69_parse_compact_interchange_bytes).parameters
    ) == ("payload",)
    assert tuple(inspect.signature(cp69.cp69_to_cp68_projection_view).parameters) == (
        "observation",
    )
    assert tuple(inspect.signature(cp69.cp69_canonical_json_bytes).parameters) == (
        "value",
    )
    assert tuple(inspect.signature(cp69.cp69_sha256).parameters) == ("value",)
    assert not inspect.signature(
        cp69.cp69_compact_projection_interchange_qualification_bundle
    ).parameters
    assert not inspect.signature(
        cp69.cp69_run_compact_projection_interchange_qualification
    ).parameters


def test_cp69_public_export_surface_is_exact() -> None:
    assert cp69.__all__ == (
        "CP69_TEST28_SCHEMA_VERSION",
        "CP69_TEST28_SCOPE",
        "CP69_TEST28_FORMAL_TEST_28_STATUS",
        "CP69_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID",
        "CP69_TEST28_SEED_COUNT",
        "CP69_TEST28_ROW_COUNT",
        "CP69_TEST28_REQUEST_COUNT",
        "CP69_TEST28_OBSERVABLE_ESTIMAND_COUNT",
        "CP69_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT",
        "CP69_TEST28_FEATURE_ESTIMAND_COUNT",
        "CP69_TEST28_ESTIMAND_COUNT",
        "CP69_TEST28_MAXIMUM_INTERCHANGE_BYTES",
        "CP69_TEST28_MAXIMUM_CANONICAL_DEPTH",
        "CP69_TEST28_MAXIMUM_CANONICAL_NODES",
        "CP69_TEST28_MAXIMUM_TEXT_BYTES",
        "CP69_TEST28_MAXIMUM_INTEGER_BITS",
        "CP69_TEST28_MAXIMUM_STREAM_BYTES",
        "CP69_TEST28_SELECTED_COUNTS_BY_ROW",
        "CP69CompactProjectionInterchangeQualificationError",
        "CP69PredecessorCustodyV1",
        "CP69CompactInterchangeContractV1",
        "CP69CompactInterchangeObservationV1",
        "CP69CP68ProjectionViewV1",
        "CP69FullStreamExpectationV1",
        "CP69CompactProjectionInterchangeQualificationV1",
        "CP69CompactProjectionInterchangeQualificationBundleV1",
        "cp69_parse_compact_interchange_bytes",
        "cp69_to_cp68_projection_view",
        "cp69_canonical_json_bytes",
        "cp69_sha256",
        "cp69_compact_interchange_fixture_set_sha256",
        "cp69_compact_projection_interchange_qualification_bundle",
        "cp69_run_compact_projection_interchange_qualification",
    )


def test_cp69_record_field_orders_are_exact_and_custody_is_preserved() -> None:
    expected = {
        cp69.CP69CompactInterchangeObservationV1: (
            "schema_version",
            "source_semantic_schema_version",
            "seed_ordinal",
            "row_ordinal",
            "logical_request_ordinal",
            "row_key",
            "fixture_id",
            "strategy",
            "budget",
            "plan_seed_hex",
            "seed_free_request_sha256",
            "request_instance_sha256",
            "runtime_lock_sha256",
            "stable_trace_sha256",
            "observable_cell_label",
            "observable_contribution_ordinal",
            "first_selected_attempt_one_based",
            "selected",
            "selected_feature_ids",
            "selected_feature_values",
            "record_sha256",
        ),
        cp69.CP69CP68ProjectionViewV1: (
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
        ),
    }
    for cls, field_names in expected.items():
        assert tuple(item.name for item in fields(cls)) == field_names
        assert cls.__dataclass_params__.frozen is True
        with pytest.raises(TypeError):
            cls()

    contract = _bundle().interchange_contract
    assert (
        contract.exact_input_keys == expected[cp69.CP69CompactInterchangeObservationV1]
    )
    assert contract.exact_target_keys == expected[cp69.CP69CP68ProjectionViewV1]
    assert contract.cp63_provenance_fields_transported is True
    assert contract.provenance_authenticated is False
    assert contract.transport_adds_scientific_semantics is False


def test_cp69_fixture_set_and_frozen_stream_pins_are_independently_derived() -> None:
    assert _independent_fixture_set_sha256() == _CP69_FIXTURE_SET_SHA256
    assert cp69.cp69_compact_interchange_fixture_set_sha256() == (
        _CP69_FIXTURE_SET_SHA256
    )
    expectation = _bundle().full_stream_expectation
    assert expectation.fixture_set_sha256 == _CP69_FIXTURE_SET_SHA256
    assert expectation.first_interchange_record_sha256 == _CP69_FIRST_INPUT_SHA256
    assert expectation.ordered_interchange_record_sha256 == (_CP69_ORDERED_INPUT_SHA256)


def test_cp69_crosswalk_preserves_all_sixteen_live_cp63_compact_anchors() -> None:
    anchors = _live_cp63_compact_anchors()
    assert len(anchors) == 16
    assert tuple(item.row_ordinal for item in anchors) == tuple(range(1, 17))
    assert all(item.schema_version == _CP63_SCHEMA for item in anchors)
    for source in anchors:
        values = _cp69_values_from_cp63(source)
        payload = cp69._interchange_bytes_from_values(values)
        assert type(payload) is bytes
        assert payload == _canonical_json_bytes(_decode_exact(payload))
        parsed = cp69.cp69_parse_compact_interchange_bytes(payload)
        for name, expected in values.items():
            assert getattr(parsed, name) == expected, (source.row_ordinal, name)
        assert parsed.record_sha256 == _independent_record_sha256(parsed)
        view = cp69.cp69_to_cp68_projection_view(parsed)
        assert view.schema_version == _CP68_SCHEMA
        copied = (
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
        )
        for name in copied:
            assert getattr(view, name) == getattr(source, name), (
                source.row_ordinal,
                name,
            )
        assert not any(
            hasattr(view, name)
            for name in (
                "source_semantic_schema_version",
                "observable_contribution_ordinal",
                "seed_free_request_sha256",
                "request_instance_sha256",
                "runtime_lock_sha256",
                "stable_trace_sha256",
                "record_sha256",
            )
        )
        assert view.projection_sha256 == _independent_record_sha256(view)


def test_cp69_all_32768_records_match_independent_semantics_and_cp68_output() -> None:
    summary = _full_stream_oracle()
    assert summary["selected_by_row"] == _SELECTED_COUNTS
    assert summary["statuses"] == Counter(
        {
            "returned-rejection-selected-before-deadline": 8_254,
            "returned-rejection-exhausted-before-deadline": 2_034,
            "returned-sir-selected-before-deadline": 8_254,
            "preexecution-refusal-before-deadline": 4_744,
            "execution-failure-before-deadline": 4_742,
            "timeout-censored-at-deadline": 4_740,
        }
    )
    assert summary["first_attempt_count"] == 8_254
    assert summary["feature_count"] == 321_906
    metrics = summary["cp68_metrics"]
    assert metrics["ordered_projection_sha256"] == _CP68_ORDERED_PROJECTION_SHA256
    assert metrics["output_canonical_json_sha256"] == _CP68_OUTPUT_SHA256
    bundle = _bundle()
    expectation = bundle.full_stream_expectation
    assert expectation.request_count == _REQUEST_COUNT
    assert expectation.selected_counts_by_row == _SELECTED_COUNTS
    assert expectation.first_interchange_record_sha256 == summary["first_input_digest"]
    assert (
        expectation.ordered_interchange_record_sha256 == summary["ordered_input_digest"]
    )
    assert expectation.first_target_projection_sha256 == (_CP68_FIRST_PROJECTION_SHA256)
    assert expectation.ordered_target_projection_sha256 == (
        _CP68_ORDERED_PROJECTION_SHA256
    )
    assert expectation.cp68_output_canonical_json_sha256 == _CP68_OUTPUT_SHA256
    qualification = _qualification()
    assert qualification.request_count == _REQUEST_COUNT
    assert qualification.logical_ordinals_complete is True
    assert qualification.streaming_peak_input_payload_count == 1
    assert qualification.streaming_peak_parsed_observation_count == 1
    assert qualification.streaming_peak_projection_view_count == 1
    assert qualification.interchange_corpus_retained is False
    assert qualification.canonical_bytes_verified is True
    assert qualification.record_digests_verified is True
    assert qualification.row_identity_verified is True
    assert qualification.observable_contribution_ordinals_verified is True
    assert qualification.outcome_and_attempt_semantics_verified is True
    assert qualification.selected_feature_semantics_verified is True
    assert qualification.selected_counts_by_row == _SELECTED_COUNTS
    assert qualification.first_attempt_contribution_count == 8_254
    assert qualification.feature_contribution_count == 321_906
    assert (
        qualification.first_interchange_record_sha256 == summary["first_input_digest"]
    )
    assert (
        qualification.ordered_interchange_record_sha256
        == summary["ordered_input_digest"]
    )
    assert qualification.first_target_projection_sha256 == (
        _CP68_FIRST_PROJECTION_SHA256
    )
    assert qualification.ordered_target_projection_sha256 == (
        _CP68_ORDERED_PROJECTION_SHA256
    )
    assert qualification.target_projection_matches_cp68_expectation is True


@pytest.mark.parametrize(
    "alien",
    (None, True, 1, "{}", bytearray(b"{}"), memoryview(b"{}")),
)
def test_cp69_parser_requires_exact_bytes(alien: object) -> None:
    assert _parse_error_code(alien) == "CP69_INPUT_TYPE_MISMATCH"


def test_cp69_parser_does_not_consult_alien_protocols() -> None:
    assert _parse_error_code(_ProtocolBomb()) == "CP69_INPUT_TYPE_MISMATCH"


@pytest.mark.parametrize(
    "payload,code",
    (
        (b"", "CP69_INPUT_BYTE_LIMIT"),
        (b"x" * 65_537, "CP69_INPUT_BYTE_LIMIT"),
        (b"\xef\xbb\xbf{}", "CP69_INPUT_ENCODING_INVALID"),
        (b'{"x":"\xff"}', "CP69_INPUT_ENCODING_INVALID"),
        (b"{", "CP69_INPUT_JSON_INVALID"),
        (b"null", "CP69_INPUT_FIELD_TYPE_MISMATCH"),
        (b'{"budget":1,"budget":1}', "CP69_INPUT_JSON_INVALID"),
        (b'{"x":1.0}', "CP69_INPUT_JSON_INVALID"),
        (b'{"x":1e0}', "CP69_INPUT_JSON_INVALID"),
        (b'{"x":NaN}', "CP69_INPUT_JSON_INVALID"),
        (b'{"x":Infinity}', "CP69_INPUT_JSON_INVALID"),
        (
            b'{"x":' + str(1 << 257).encode("ascii") + b"}",
            "CP69_INPUT_RESOURCE_LIMIT",
        ),
        (
            _canonical_json_bytes({"x": "a" * 4_097}),
            "CP69_INPUT_RESOURCE_LIMIT",
        ),
        (
            b"[" * 18 + b"0" + b"]" * 18,
            "CP69_INPUT_RESOURCE_LIMIT",
        ),
        (
            _canonical_json_bytes({"x": [0] * 513}),
            "CP69_INPUT_RESOURCE_LIMIT",
        ),
    ),
    ids=(
        "empty",
        "oversize",
        "bom",
        "nonascii",
        "malformed",
        "null-root",
        "duplicate-key",
        "float",
        "exponent",
        "nan",
        "infinity",
        "integer-bits",
        "text-bytes",
        "depth",
        "nodes",
    ),
)
def test_cp69_parser_rejects_encoding_json_and_resource_hostiles(
    payload: bytes, code: str
) -> None:
    assert _parse_error_code(payload) == code


def test_cp69_parser_rejects_noncanonical_whitespace_order_and_escaping() -> None:
    payload = cp69._closed_interchange_bytes(1, 1)
    assert _parse_error_code(payload + b" ") == "CP69_INPUT_CANONICAL_MISMATCH"
    raw = _decode_exact(payload)
    reverse = json.dumps(
        {key: raw[key] for key in reversed(tuple(raw))},
        sort_keys=False,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    assert _parse_error_code(reverse) == "CP69_INPUT_CANONICAL_MISMATCH"
    escaped = payload.replace(b"T28-M1-Q", b"T28-M1-\\u0051")
    assert escaped != payload
    assert _parse_error_code(escaped) == "CP69_INPUT_CANONICAL_MISMATCH"


def test_cp69_parser_rejects_missing_extra_and_duplicate_semantic_fields() -> None:
    raw = _decode_exact(cp69._closed_interchange_bytes(1, 1))
    missing = dict(raw)
    del missing["stable_trace_sha256"]
    extra = {**raw, "alien": None}
    assert _parse_error_code(_canonical_json_bytes(missing)) == (
        "CP69_INPUT_FIELD_SET_MISMATCH"
    )
    assert _parse_error_code(_canonical_json_bytes(extra)) == (
        "CP69_INPUT_FIELD_SET_MISMATCH"
    )
    duplicate = b'{"budget":1,' + cp69._closed_interchange_bytes(1, 1)[1:]
    assert _parse_error_code(duplicate) == "CP69_INPUT_JSON_INVALID"


@pytest.mark.parametrize(
    "changes,code",
    (
        ({"schema_version": "cp69-alien"}, "CP69_INPUT_SCHEMA_MISMATCH"),
        (
            {"source_semantic_schema_version": "cp63-alien"},
            "CP69_INPUT_SCHEMA_MISMATCH",
        ),
        ({"seed_ordinal": True}, "CP69_INPUT_FIELD_TYPE_MISMATCH"),
        ({"seed_ordinal": 0}, "CP69_INPUT_ORDINAL_MISMATCH"),
        ({"seed_ordinal": 2_049}, "CP69_INPUT_ORDINAL_MISMATCH"),
        ({"row_ordinal": 0}, "CP69_INPUT_ORDINAL_MISMATCH"),
        ({"row_ordinal": 17}, "CP69_INPUT_ORDINAL_MISMATCH"),
        ({"logical_request_ordinal": 2}, "CP69_INPUT_ORDINAL_MISMATCH"),
        ({"row_key": "row-01/alien"}, "CP69_INPUT_ROW_MISMATCH"),
        ({"fixture_id": "T28-M2-Q"}, "CP69_INPUT_ROW_MISMATCH"),
        ({"strategy": "fixed-budget-sir"}, "CP69_INPUT_ROW_MISMATCH"),
        ({"budget": 4}, "CP69_INPUT_ROW_MISMATCH"),
        ({"plan_seed_hex": "0" * 15}, "CP69_INPUT_FIELD_TYPE_MISMATCH"),
        ({"plan_seed_hex": "G" * 16}, "CP69_INPUT_FIELD_TYPE_MISMATCH"),
        ({"seed_free_request_sha256": "0" * 63}, "CP69_INPUT_FIELD_TYPE_MISMATCH"),
        ({"request_instance_sha256": "A" * 64}, "CP69_INPUT_FIELD_TYPE_MISMATCH"),
        ({"runtime_lock_sha256": None}, "CP69_INPUT_FIELD_TYPE_MISMATCH"),
        ({"stable_trace_sha256": "z" * 64}, "CP69_INPUT_FIELD_TYPE_MISMATCH"),
        (
            {"observable_cell_label": "returned-sir-selected-before-deadline"},
            "CP69_INPUT_OUTCOME_MISMATCH",
        ),
        ({"selected": False}, "CP69_INPUT_OUTCOME_MISMATCH"),
        ({"first_selected_attempt_one_based": None}, "CP69_INPUT_OUTCOME_MISMATCH"),
        ({"first_selected_attempt_one_based": 0}, "CP69_INPUT_OUTCOME_MISMATCH"),
        ({"first_selected_attempt_one_based": 2}, "CP69_INPUT_OUTCOME_MISMATCH"),
        (
            {"observable_contribution_ordinal": 2},
            "CP69_INPUT_CONTRIBUTION_ORDINAL_MISMATCH",
        ),
    ),
)
def test_cp69_parser_rejects_scalar_identity_and_outcome_corruption(
    changes: dict, code: str
) -> None:
    assert _parse_error_code(_mutated_closed_payload(changes=changes)) == code


def test_cp69_parser_rejects_sir_attempt_and_nonselected_feature_smuggling() -> None:
    assert (
        _parse_error_code(
            _mutated_closed_payload(
                base_row_ordinal=5,
                changes={"first_selected_attempt_one_based": 1},
            )
        )
        == "CP69_INPUT_OUTCOME_MISMATCH"
    )
    raw = _decode_exact(cp69._closed_interchange_bytes(1, 4))
    raw["selected_feature_ids"] = ["count/eq/0"]
    raw["selected_feature_values"] = [{"$fraction": ["1", "1"]}]
    assert _parse_error_code(_retag_input(raw)) == "CP69_INPUT_FEATURE_MISMATCH"


def test_cp69_parser_rejects_feature_inventory_value_and_fraction_corruption() -> None:
    raw = _decode_exact(cp69._closed_interchange_bytes(1, 1))
    cases = []
    for changed_ids in (
        raw["selected_feature_ids"][:-1],
        list(reversed(raw["selected_feature_ids"])),
        [*raw["selected_feature_ids"][:-1], "alien"],
        [raw["selected_feature_ids"][0], *raw["selected_feature_ids"]],
    ):
        cases.append({**raw, "selected_feature_ids": changed_ids})
    cases.append(
        {**raw, "selected_feature_values": raw["selected_feature_values"][:-1]}
    )
    cases.append(
        {
            **raw,
            "selected_feature_values": [
                {"$fraction": ["2", "1"]},
                *raw["selected_feature_values"][1:],
            ],
        }
    )
    malformed = (
        None,
        1,
        {"fraction": ["0", "1"]},
        {"$fraction": ["0"]},
        {"$fraction": [0, "1"]},
        {"$fraction": ["00", "1"]},
        {"$fraction": ["-0", "1"]},
        {"$fraction": ["1", "0"]},
        {"$fraction": ["1", "-1"]},
        {"$fraction": ["2", "2"]},
    )
    for value in malformed:
        changed_values = list(raw["selected_feature_values"])
        changed_values[0] = value
        cases.append({**raw, "selected_feature_values": changed_values})
    for case in cases:
        assert _parse_error_code(_retag_input(case)) in {
            "CP69_INPUT_FEATURE_MISMATCH",
            "CP69_INPUT_FIELD_TYPE_MISMATCH",
        }


def test_cp69_parser_detects_digest_tamper_and_body_transplant() -> None:
    raw = _decode_exact(cp69._closed_interchange_bytes(1, 1))
    changed_digest = {**raw, "record_sha256": "f" * 64}
    assert _parse_error_code(_canonical_json_bytes(changed_digest)) == (
        "CP69_INPUT_DIGEST_MISMATCH"
    )
    transplanted = dict(raw)
    transplanted["plan_seed_hex"] = "1234567890abcdef"
    assert _parse_error_code(_canonical_json_bytes(transplanted)) == (
        "CP69_INPUT_DIGEST_MISMATCH"
    )


def test_cp69_stream_rejects_noniterable_empty_failed_reordered_and_duplicate() -> None:
    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69._reduce_interchange_stream_details(_IterableBomb())
    assert caught.value.code == "CP69_STREAM_ITERABLE_INVALID"

    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69._reduce_interchange_stream_details(())
    assert caught.value.code == "CP69_STREAM_COUNT_MISMATCH"

    def failed() -> object:
        raise RuntimeError("stream failure")
        yield b"unreachable"

    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69._reduce_interchange_stream_details(failed())
    assert caught.value.code == "CP69_STREAM_ITERATION_FAILED"

    first = cp69._closed_interchange_bytes(1, 1)
    second = cp69._closed_interchange_bytes(1, 2)
    for stream in ((second,), (first, first)):
        with pytest.raises(
            cp69.CP69CompactProjectionInterchangeQualificationError
        ) as caught:
            cp69._reduce_interchange_stream_details(stream)
        assert caught.value.code == "CP69_STREAM_CONTENT_MISMATCH"


def test_cp69_stream_terminal_probe_is_bounded_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = cp69._closed_interchange_bytes(1, 1)
    monkeypatch.setattr(cp69, "CP69_TEST28_REQUEST_COUNT", 1)

    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69._reduce_interchange_stream_details((first, None))
    assert caught.value.code == "CP69_STREAM_COUNT_MISMATCH"

    class Infinite:
        def __init__(self) -> None:
            self.calls = 0

        def __iter__(self) -> object:
            return self

        def __next__(self) -> bytes:
            self.calls += 1
            if self.calls > 2:
                raise AssertionError("terminal probe consumed more than one extra")
            return first

    infinite = Infinite()
    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69._reduce_interchange_stream_details(infinite)
    assert caught.value.code == "CP69_STREAM_COUNT_MISMATCH"
    assert infinite.calls == 2

    class TailBomb:
        def __init__(self) -> None:
            self.calls = 0

        def __iter__(self) -> object:
            return self

        def __next__(self) -> bytes:
            self.calls += 1
            if self.calls == 1:
                return first
            raise RuntimeError("terminal failure")

    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69._reduce_interchange_stream_details(TailBomb())
    assert caught.value.code == "CP69_STREAM_ITERATION_FAILED"


@pytest.mark.parametrize(
    "boundary,expected_calls",
    (
        ("iter", (1, 0)),
        ("item", (1, 1)),
        ("terminal", (1, 2)),
    ),
)
def test_cp69_public_runner_normalizes_memory_failure_at_every_stream_boundary(
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    expected_calls: tuple[int, int],
) -> None:
    first = cp69._closed_interchange_bytes(1, 1)
    cp69._closed_interchange_values(1, 1)
    cp69.cp69_compact_interchange_fixture_set_sha256()
    bundle = cp69.cp69_compact_projection_interchange_qualification_bundle()
    bundle_bytes = cp69.cp69_canonical_json_bytes(bundle)
    bundle_sha256 = cp69.cp69_sha256(bundle)
    registry_before = _issued_registry_snapshot()
    caches_before = _cache_population_snapshot()
    memory_message = "memory exhausted at %s boundary" % boundary
    source = _BoundaryFailureSource(boundary, MemoryError(memory_message), first)
    monkeypatch.setattr(cp69, "CP69_TEST28_REQUEST_COUNT", 1)
    monkeypatch.setattr(cp69, "_iter_closed_interchange_bytes", lambda: source)

    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69.cp69_run_compact_projection_interchange_qualification()

    error = caught.value
    assert type(error) is cp69.CP69CompactProjectionInterchangeQualificationError
    assert error.code == "CP69_RESOURCE_EXHAUSTED"
    assert error.args == ("the closed CP69 qualification exceeded its memory boundary",)
    assert str(error) == "the closed CP69 qualification exceeded its memory boundary"
    assert type(error.__cause__) is MemoryError
    assert error.__cause__.args == (memory_message,)
    assert error.__context__ is error.__cause__
    assert error.__suppress_context__ is True
    assert (source.iter_calls, source.next_calls) == expected_calls
    assert cp69._BUNDLE_CACHE is bundle
    assert cp69.cp69_canonical_json_bytes(bundle) == bundle_bytes
    assert cp69.cp69_sha256(bundle) == bundle_sha256
    assert _issued_registry_snapshot() == registry_before
    assert _cache_population_snapshot() == caches_before


@pytest.mark.parametrize(
    "boundary,expected_code,expected_message,expected_calls",
    (
        (
            "iter",
            "CP69_STREAM_ITERABLE_INVALID",
            "the private interchange source is not iterable",
            (1, 0),
        ),
        (
            "item",
            "CP69_STREAM_ITERATION_FAILED",
            "the interchange iterator failed during reduction",
            (1, 1),
        ),
        (
            "terminal",
            "CP69_STREAM_ITERATION_FAILED",
            "the interchange iterator failed at its terminal boundary",
            (1, 2),
        ),
    ),
)
def test_cp69_public_runner_preserves_ordinary_stream_failure_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    expected_code: str,
    expected_message: str,
    expected_calls: tuple[int, int],
) -> None:
    first = cp69._closed_interchange_bytes(1, 1)
    cp69._closed_interchange_values(1, 1)
    cp69.cp69_compact_interchange_fixture_set_sha256()
    bundle = cp69.cp69_compact_projection_interchange_qualification_bundle()
    bundle_bytes = cp69.cp69_canonical_json_bytes(bundle)
    bundle_sha256 = cp69.cp69_sha256(bundle)
    registry_before = _issued_registry_snapshot()
    caches_before = _cache_population_snapshot()
    failure_message = "ordinary failure at %s boundary" % boundary
    source = _BoundaryFailureSource(boundary, RuntimeError(failure_message), first)
    monkeypatch.setattr(cp69, "CP69_TEST28_REQUEST_COUNT", 1)
    monkeypatch.setattr(cp69, "_iter_closed_interchange_bytes", lambda: source)

    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69.cp69_run_compact_projection_interchange_qualification()

    error = caught.value
    assert type(error) is cp69.CP69CompactProjectionInterchangeQualificationError
    assert error.code == expected_code
    assert error.args == (expected_message,)
    assert str(error) == expected_message
    assert type(error.__cause__) is RuntimeError
    assert error.__cause__.args == (failure_message,)
    assert error.__context__ is error.__cause__
    assert error.__suppress_context__ is True
    assert (source.iter_calls, source.next_calls) == expected_calls
    assert cp69._BUNDLE_CACHE is bundle
    assert cp69.cp69_canonical_json_bytes(bundle) == bundle_bytes
    assert cp69.cp69_sha256(bundle) == bundle_sha256
    assert _issued_registry_snapshot() == registry_before
    assert _cache_population_snapshot() == caches_before


def test_cp69_stream_enforces_cumulative_byte_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = cp69._closed_interchange_bytes(1, 1)
    monkeypatch.setattr(cp69, "CP69_TEST28_MAXIMUM_STREAM_BYTES", len(first) - 1)
    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69._reduce_interchange_stream_details((first,))
    assert caught.value.code == "CP69_STREAM_RESOURCE_LIMIT"


def test_cp69_duplicate_plan_seed_values_are_transportable_at_distinct_ordinals() -> None:
    first = _decode_exact(cp69._closed_interchange_bytes(1, 1))
    second = _decode_exact(cp69._closed_interchange_bytes(2, 1))
    second["plan_seed_hex"] = first["plan_seed_hex"]
    payload = _retag_input(second)
    parsed = cp69.cp69_parse_compact_interchange_bytes(payload)
    assert parsed.seed_ordinal == 2
    assert parsed.plan_seed_hex == first["plan_seed_hex"]
    assert parsed.plan_seed_hex != "%016x" % (parsed.seed_ordinal - 1)


def test_cp69_mapper_rejects_wrong_forged_and_tampered_observations() -> None:
    for alien in (None, True, 1, {}, b"x", _ProtocolBomb()):
        with pytest.raises(
            cp69.CP69CompactProjectionInterchangeQualificationError
        ) as caught:
            cp69.cp69_to_cp68_projection_view(alien)
        assert caught.value.code == "CP69_OBSERVATION_TYPE_MISMATCH"
    issued = cp69.cp69_parse_compact_interchange_bytes(
        cp69._closed_interchange_bytes(1, 1)
    )
    forged = _forge(issued)
    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69.cp69_to_cp68_projection_view(forged)
    assert caught.value.code == "CP69_OBSERVATION_NOT_ISSUED"
    tampered = cp69.cp69_parse_compact_interchange_bytes(
        cp69._closed_interchange_bytes(1, 1)
    )
    object.__setattr__(tampered, "plan_seed_hex", "f" * 16)
    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69.cp69_to_cp68_projection_view(tampered)
    assert caught.value.code == "CP69_OBSERVATION_TAMPERED"


def test_cp69_parser_mapper_bundle_and_record_registry_are_thread_safe() -> None:
    payload = cp69._closed_interchange_bytes(1, 1)
    bundle = _bundle()

    def observe(_index: int) -> tuple[bytes, bytes, bytes]:
        parsed = cp69.cp69_parse_compact_interchange_bytes(payload)
        view = cp69.cp69_to_cp68_projection_view(parsed)
        return (
            cp69.cp69_canonical_json_bytes(parsed),
            cp69.cp69_canonical_json_bytes(view),
            cp69.cp69_canonical_json_bytes(
                cp69.cp69_compact_projection_interchange_qualification_bundle()
            ),
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        observed = tuple(executor.map(observe, range(32)))
    expected = (
        payload,
        cp69.cp69_canonical_json_bytes(
            cp69.cp69_to_cp68_projection_view(
                cp69.cp69_parse_compact_interchange_bytes(payload)
            )
        ),
        cp69.cp69_canonical_json_bytes(bundle),
    )
    assert observed == (expected,) * 32


def test_cp69_public_parser_and_runner_normalize_unexpected_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def memory(*_args: object, **_kwargs: object) -> object:
        raise MemoryError("bounded memory failure")

    monkeypatch.setattr(cp69, "_decode_canonical_object", memory)
    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69.cp69_parse_compact_interchange_bytes(b"{}")
    assert caught.value.code == "CP69_RESOURCE_EXHAUSTED"

    def unexpected(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(cp69, "_decode_canonical_object", unexpected)
    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69.cp69_parse_compact_interchange_bytes(b"{}")
    assert caught.value.code == "CP69_INPUT_JSON_INVALID"

    monkeypatch.setattr(
        cp69, "_run_compact_projection_interchange_qualification", memory
    )
    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69.cp69_run_compact_projection_interchange_qualification()
    assert caught.value.code == "CP69_RESOURCE_EXHAUSTED"
    monkeypatch.setattr(
        cp69, "_run_compact_projection_interchange_qualification", unexpected
    )
    with pytest.raises(
        cp69.CP69CompactProjectionInterchangeQualificationError
    ) as caught:
        cp69.cp69_run_compact_projection_interchange_qualification()
    assert caught.value.code == "CP69_QUALIFICATION_FAILURE"


def test_cp69_public_surfaces_are_zero_io_and_do_not_import_predecessors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = cp69._closed_interchange_bytes(1, 1)
    expected_qualification = _qualification()
    original_import = builtins.__import__

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("CP69 attempted forbidden I/O or observation")

    def guarded_import(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        if name.startswith(("heterodiff", "numpy", "scipy")):
            raise AssertionError("CP69 attempted project or numerical import")
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
    parsed = cp69.cp69_parse_compact_interchange_bytes(payload)
    view = cp69.cp69_to_cp68_projection_view(parsed)
    assert view.projection_sha256 == _CP68_FIRST_PROJECTION_SHA256
    assert cp69.cp69_compact_projection_interchange_qualification_bundle() is _bundle()
    monkeypatch.setattr(
        cp69,
        "_run_compact_projection_interchange_qualification",
        lambda: expected_qualification,
    )
    assert cp69.cp69_run_compact_projection_interchange_qualification() is (
        expected_qualification
    )


def test_cp69_public_record_helpers_reject_aliens_forgery_and_mutation() -> None:
    for alien in (None, True, 1, "x", b"x", {}, (), _ProtocolBomb()):
        for function in (cp69.cp69_canonical_json_bytes, cp69.cp69_sha256):
            with pytest.raises(
                cp69.CP69CompactProjectionInterchangeQualificationError
            ) as caught:
                function(alien)
            assert caught.value.code == "CP69_RECORD_TYPE_MISMATCH"
    issued = cp69.cp69_parse_compact_interchange_bytes(
        cp69._closed_interchange_bytes(1, 1)
    )
    forged = _forge(issued)
    for candidate, code in (
        (forged, "CP69_RECORD_NOT_ISSUED"),
        (issued, "CP69_RECORD_TAMPERED"),
    ):
        if candidate is issued:
            object.__setattr__(issued, "record_sha256", "f" * 64)
        for function in (cp69.cp69_canonical_json_bytes, cp69.cp69_sha256):
            with pytest.raises(
                cp69.CP69CompactProjectionInterchangeQualificationError
            ) as caught:
                function(candidate)
            assert caught.value.code == code


def test_cp69_source_is_stdlib_only_zero_io_and_python39_parseable() -> None:
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
    assert "dataclass(slots=True" not in source.replace(" ", "")
    match_node = getattr(ast, "Match", ())
    assert all(not isinstance(node, match_node) for node in ast.walk(tree))
    assert "except*" not in source


def test_cp69_fresh_module_execution_performs_no_host_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    code = compile(source, str(_SOURCE), "exec")
    original_import = builtins.__import__

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("CP69 attempted forbidden host observation")

    def guarded_import(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        if name.startswith(("heterodiff", "numpy", "scipy")):
            raise AssertionError("CP69 attempted project or numerical import")
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
    module_name = "heterodiff.evaluation._cp69_hostile_fresh_import"
    module = types.ModuleType(module_name)
    module.__file__ = str(_SOURCE)
    module.__package__ = "heterodiff.evaluation"
    sys.modules[module_name] = module
    try:
        exec(code, module.__dict__)
    finally:
        del sys.modules[module_name]
    assert module.CP69_TEST28_REQUEST_COUNT == _REQUEST_COUNT


def test_cp69_records_are_sealed_nonconstructible_and_nonpickleable() -> None:
    bundle = _bundle()
    first = cp69.cp69_parse_compact_interchange_bytes(
        cp69._closed_interchange_bytes(1, 1)
    )
    view = cp69.cp69_to_cp68_projection_view(first)
    records = (
        bundle.predecessor_custody,
        bundle.interchange_contract,
        bundle.full_stream_expectation,
        bundle,
        first,
        view,
        _qualification(),
    )
    for record in records:
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(record)
        with pytest.raises((TypeError, AttributeError)):
            setattr(record, fields(type(record))[0].name, "mutated")
        with pytest.raises(TypeError):
            type("Alien", (type(record),), {})
        canonical = _canonical_json_bytes(record)
        assert cp69.cp69_canonical_json_bytes(record) == canonical
        assert cp69.cp69_sha256(record) == _sha256(
            b"cp69-public-record-v1\0"
            + type(record).__name__.encode("ascii")
            + b"\0"
            + canonical
        )
        digest_name = (
            "projection_sha256"
            if type(record) is cp69.CP69CP68ProjectionViewV1
            else "record_sha256"
        )
        assert getattr(record, digest_name) == _independent_record_sha256(record)


def test_cp69_nonclaims_leave_every_production_boundary_fail_closed() -> None:
    bundle = _bundle()
    qualification = _qualification()
    assert bundle.formal_test_28_status == "OPEN"
    assert bundle.ledger_total_count == 24
    assert bundle.ledger_satisfied_count == 20
    assert bundle.ledger_missing_count == 4
    assert bundle.ledger_prerequisite_state == (
        "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_ARTIFACTS"
    )
    assert bundle.zero_argument_builder is True
    assert bundle.builder_parses_or_streams is False
    assert bundle.qualification_runner_zero_argument is True
    assert bundle.bounded_public_byte_parser_exposed is True
    assert bundle.sealed_public_projection_mapper_exposed is True
    assert bundle.closed_module_owned_fixture_only is True
    assert bundle.stdlib_only_import is True
    assert bundle.streaming_interchange is True
    assert bundle.development_qualification_only is True
    for name in (
        "project_modules_imported",
        "full_interchange_corpus_materialized",
        "host_filesystem_probed",
        "clock_read",
        "rng_used",
        "network_used",
        "subprocess_api_exposed",
        "filesystem_path_api_exposed",
        "raw_record_api_exposed",
        "stable_trace_api_exposed",
        "production_campaign_api_exposed",
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
        "formal_test_28_closed",
    ):
        assert getattr(bundle, name) is False, name
    assert bundle.production_gate_13_state == "MISSING"
    assert bundle.production_gate_14_state == "MISSING"
    for name in (
        "raw_record_parsed",
        "stable_trace_parsed",
        "provenance_authenticated",
        "estimate_or_interval_computed",
        "decision_path_qualified",
        "production_evidence",
        "production_execution_authorized",
        "runner_and_recomputation_blocker_closed",
        "formal_test_28_closed",
    ):
        assert getattr(qualification, name) is False, name
    assert qualification.all_development_qualification_checks_passed is True
