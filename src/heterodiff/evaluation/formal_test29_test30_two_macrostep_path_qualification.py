"""Bounded supplied-input two-macrostep Test-29/Test-30 path precursor.

The earlier single-macrostep precursor proves one left-Heun / one finite edit /
one right-Heun composition from a fixed two-occurrence state.  This additive
module closes the next *development* integration gap: it carries coordinates,
active and retired serials, and the next fresh serial through exactly two such
macrosteps.  Both complete CP23-shaped increment rosters and both CP24-shaped
words are validated before the first Heun operation.

Every numerical value and uint64 word is caller supplied.  The frozen
qualification exhausts the 32 x 32 low-word pair space of the dynamic
rank-one fixtures.  No entropy, clock, retry loop, filesystem operation,
network operation, production source, or protected data is used.  The finite
normal-cell midpoint is a representative, not a continuous Gaussian draw.
This is not an arbitrary-length or production Strang path and closes no
formal test, blocker, result, field, or tracker task.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
import json
import math
from types import ModuleType
from typing import Dict, Mapping, Optional, Tuple


SCHEMA_VERSION = "heterodiff-test29-test30-two-macrostep-path-v1"
PREDICATE = (
    "SYNTHETIC_SUPPLIED_INPUT_TWO_MACROSTEP_ROLLING_LINEAGE_PATH_VALIDATED"
)
QUALIFICATION_SCOPE = (
    "TWO_LEFT_JUMP_RIGHT_MACROSTEPS;SUPPLIED_CP23_SHAPED_PHYSICAL_"
    "INCREMENTS;TWO_SUPPLIED_CP24_SHAPED_WORDS;ROLLING_COORDINATE_AND_"
    "FRESH_RETIRED_LINEAGE_CONTINUITY;COMPLETE_32_BY_32_LOW_WORD_PAIRS"
)
STRICT_NONCLAIMS = (
    "NO_TEST28_INITIALIZER_OR_ADMISSION;NO_LIVE_CP23_OR_CP24_STREAM;"
    "NO_BROWNIAN_GAUSSIAN_INDEPENDENCE_OR_WORD_LAW;NO_CONTINUOUS_"
    "GAUSSIAN_DESTINATION;NO_WAITING_CLOCK_ACCEPTANCE_OR_THINNING;"
    "NO_ZERO_OR_MULTIPLE_EDIT_JUMP_SUBSTEP;NO_ARBITRARY_LENGTH_GENERAL_"
    "OR_PRODUCTION_STRANG_PATH;NO_STEP_HALVING_OR_ENDPOINT_LAW;"
    "NO_PARENT_CUSTODY_AUTHENTICATION;NO_FORMAL_TEST_BLOCKER_RESULT_"
    "FIELD_OR_TRACKER_CLOSURE;NO_SCIENTIFIC_EXECUTION"
)
FAILURE_POLICY = "FAIL_CLOSED_COMPLETE_TWO_STEP_PREFLIGHT_NO_RETRY_NO_FALLBACK"
EXPECTED_SINGLE_SCHEMA = "heterodiff-test29-test30-single-macrostep-integration-v1"
EXPECTED_TEST29_SCHEMA = "formal-test29-finite-acyclic-route-oracle-v1"
EXPECTED_TEST30_SCHEMA = "heterodiff-formal-test30-synthetic-coupled-path-v1"

FROZEN_RUN_ID = 29_032
FROZEN_MACROSTEP_WIDTH = 0.25
FROZEN_STEP_COUNT = 2
FROZEN_LOW_WORD_COUNT = 32


class SyntheticTwoMacrostepPathError(ValueError):
    """Raised when a supplied path or its reconstruction is invalid."""


def _exact_uint64(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact built-in integer")
    if value < 0 or value >= 1 << 64:
        raise ValueError(name + " lies outside its uint64 range")
    return value


def _finite_float(value: object, *, name: str, positive: bool = False) -> float:
    if type(value) is not float:
        raise TypeError(name + " must be an exact built-in float")
    if not math.isfinite(value):
        raise ValueError(name + " must be finite")
    if positive and value <= 0.0:
        raise ValueError(name + " must be positive")
    return value


def _exact_text(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if not value or not value.isascii():
        raise ValueError(name + " must be nonempty ASCII text")
    return value


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(name + " must be an exact boolean")
    return value


def _exact_optional_uint64(value: object, *, name: str) -> Optional[int]:
    if value is None:
        return None
    return _exact_uint64(value, name=name)


def _exact_sha256(value: object, *, name: str) -> str:
    text = _exact_text(value, name=name)
    if len(text) != 64 or any(c not in "0123456789abcdef" for c in text):
        raise ValueError(name + " must be lowercase SHA-256 hex")
    return text


def _canonical_digest(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def _require_parent_modules(
    single_api: object, test29_api: object, test30_api: object
) -> None:
    if any(type(api) is not ModuleType for api in (single_api, test29_api, test30_api)):
        raise TypeError("all parent APIs must be exact module objects")
    if getattr(single_api, "SCHEMA_VERSION", None) != EXPECTED_SINGLE_SCHEMA:
        raise SyntheticTwoMacrostepPathError("single-macrostep schema differs")
    if (
        getattr(test29_api, "FORMAL_TEST29_FINITE_ACYCLIC_SCHEMA_VERSION", None)
        != EXPECTED_TEST29_SCHEMA
    ):
        raise SyntheticTwoMacrostepPathError("Test-29 schema differs")
    if getattr(test30_api, "SCHEMA_VERSION", None) != EXPECTED_TEST30_SCHEMA:
        raise SyntheticTwoMacrostepPathError("Test-30 schema differs")
    required_single = (
        "_addressed_increment",
        "_validate_increment_roster",
        "_validate_central_word",
        "_strict_compare_dataclass_fields",
    )
    required_test29 = (
        "FAMILY_BIRTH",
        "FAMILY_DEATH",
        "FAMILY_REPLACEMENT",
        "GaussianDestination",
        "WordLayout",
        "RouteSpec",
        "StateSpec",
        "FixtureSpec",
        "CP24CompatibleAddress",
        "AddressedUint64Word",
        "LineageState",
        "select_one_step",
        "run_addressed_acyclic_fixture",
        "validate_addressed_acyclic_run_result",
        "qualify_finite_acyclic_fixture",
        "_advance_lineage",
    )
    required_test30 = (
        "TAG_BROWNIAN_LEFT",
        "TAG_BROWNIAN_RIGHT",
        "AddressedBrownianIncrement",
        "SyntheticOccurrence",
        "frozen_synthetic_design",
        "_heun_half",
    )
    if any(not hasattr(single_api, name) for name in required_single):
        raise SyntheticTwoMacrostepPathError(
            "single-macrostep parent is missing a required symbol"
        )
    if any(not hasattr(test29_api, name) for name in required_test29):
        raise SyntheticTwoMacrostepPathError(
            "Test-29 parent is missing a required symbol"
        )
    if any(not hasattr(test30_api, name) for name in required_test30):
        raise SyntheticTwoMacrostepPathError(
            "Test-30 parent is missing a required symbol"
        )


def _source_masses(cardinality: int) -> Tuple[Fraction, ...]:
    cardinality = _exact_uint64(cardinality, name="cardinality")
    if cardinality == 1:
        return (Fraction(1),)
    if cardinality == 2:
        return (Fraction(1, 2), Fraction(1, 2))
    if cardinality == 3:
        return (Fraction(1, 2), Fraction(1, 4), Fraction(1, 4))
    raise SyntheticTwoMacrostepPathError(
        "the frozen two-step fixture only admits active cardinality one through three"
    )


def dynamic_central_jump_fixture(test29_api: ModuleType, cardinality: int):
    """Build one rank-one fixture for the current rolling cardinality."""

    if type(test29_api) is not ModuleType:
        raise TypeError("test29_api must be an exact module")
    cardinality = _exact_uint64(cardinality, name="cardinality")
    masses = _source_masses(cardinality)
    gaussian_birth = test29_api.GaussianDestination(
        (Fraction(1, 4),), (Fraction(1, 4),)
    )
    gaussian_replacement = test29_api.GaussianDestination(
        (Fraction(-1, 4),), (Fraction(1, 1),)
    )
    root = test29_api.StateSpec(
        "two-step-root",
        1,
        cardinality,
        (
            test29_api.RouteSpec(
                "two-step-birth",
                test29_api.FAMILY_BIRTH,
                "two-step-birth-terminal",
                Fraction(1),
                Fraction(2),
                (),
                gaussian_birth,
            ),
            test29_api.RouteSpec(
                "two-step-replacement",
                test29_api.FAMILY_REPLACEMENT,
                "two-step-replacement-terminal",
                Fraction(1),
                Fraction(1),
                masses,
                gaussian_replacement,
            ),
            test29_api.RouteSpec(
                "two-step-death",
                test29_api.FAMILY_DEATH,
                "two-step-death-terminal",
                Fraction(1),
                Fraction(1),
                masses,
                None,
            ),
        ),
    )
    terminals = (
        test29_api.StateSpec(
            "two-step-birth-terminal", 0, cardinality + 1, ()
        ),
        test29_api.StateSpec(
            "two-step-replacement-terminal", 0, cardinality, ()
        ),
        test29_api.StateSpec(
            "two-step-death-terminal", 0, cardinality - 1, ()
        ),
    )
    return test29_api.FixtureSpec(
        "test29-test30-two-macrostep-cardinality-%d" % cardinality,
        (root,) + terminals,
        "two-step-root",
        test29_api.WordLayout(2, 2, 1, 1),
    )


@dataclass(frozen=True)
class SuppliedPathStep:
    step_index: int
    left_increments: Tuple[object, ...]
    central_word: object
    right_increments: Tuple[object, ...]

    def __post_init__(self) -> None:
        _exact_uint64(self.step_index, name="step.step_index")
        if type(self.left_increments) is not tuple:
            raise TypeError("step.left_increments must be an exact tuple")
        if type(self.right_increments) is not tuple:
            raise TypeError("step.right_increments must be an exact tuple")


@dataclass(frozen=True)
class SuppliedTwoMacrostepPathInput:
    run_id: int
    macrostep_width: float
    steps: Tuple[SuppliedPathStep, ...]

    def __post_init__(self) -> None:
        _exact_uint64(self.run_id, name="path.run_id")
        _finite_float(self.macrostep_width, name="path.macrostep_width", positive=True)
        if type(self.steps) is not tuple:
            raise TypeError("path.steps must be an exact tuple")


@dataclass(frozen=True)
class TwoMacrostepStepResult:
    step_index: int
    raw64_word: int
    route_id: str
    family: str
    source_index: Optional[int]
    source_serial: Optional[int]
    created_serial: Optional[int]
    normal_cell_indices: Tuple[int, ...]
    active_serials_before: Tuple[int, ...]
    retired_serials_before: Tuple[int, ...]
    active_serials_after: Tuple[int, ...]
    retired_serials_after: Tuple[int, ...]
    next_serial_before: int
    next_serial_after: int
    state_before: Tuple[Tuple[int, str, float], ...]
    state_after_left: Tuple[Tuple[int, str, float], ...]
    state_after_jump: Tuple[Tuple[int, str, float], ...]
    state_after_right: Tuple[Tuple[int, str, float], ...]
    left_heun_application_count: int
    central_jump_count: int
    right_heun_application_count: int
    address_count: int


@dataclass(frozen=True)
class TwoMacrostepPathResult:
    schema_version: str
    predicate: str
    scope: str
    strict_nonclaims: str
    failure_policy: str
    run_id: int
    macrostep_width: float
    input_sha256: str
    report_sha256: str
    steps: Tuple[TwoMacrostepStepResult, ...]
    total_left_heun_applications: int
    total_central_jumps: int
    total_right_heun_applications: int
    total_address_count: int
    complete_input_preflight_before_first_arithmetic: bool
    global_address_identities_unique: bool
    boundary_state_continuity: bool
    rolling_test29_fresh_retired_lineage_preserved: bool
    bounded_two_macrostep_path_integrated: bool
    arbitrary_length_general_strang_path_integrated: bool
    parent_custody_authenticated: bool
    test28_initializer_admissible: bool
    live_cp23_stream_consumed: bool
    live_cp24_stream_consumed: bool
    continuous_gaussian_destination_sampled: bool
    waiting_clock_or_acceptance_thinning_executed: bool
    step_halving_or_endpoint_law_qualified: bool
    formal_test28_closed: bool
    formal_test29_closed: bool
    formal_test30_closed: bool
    fields_closed: int
    blockers_closed: int
    result_slots_filled: int
    tracker_files_edited: int
    passed: bool


@dataclass(frozen=True)
class FrozenTwoMacrostepQualification:
    schema_version: str
    predicate: str
    scope: str
    strict_nonclaims: str
    failure_policy: str
    ordered_word_pair_cases_checked: int
    route_pair_counts: Tuple[Tuple[str, int], ...]
    boundary_cardinality_counts: Tuple[Tuple[int, int], ...]
    final_cardinality_counts: Tuple[Tuple[int, int], ...]
    distinct_input_sha256_count: int
    distinct_report_sha256_count: int
    ordered_case_commitment_sha256: str
    all_nine_route_family_pairs_covered: bool
    every_case_boundary_continuous: bool
    every_case_global_addresses_unique: bool
    every_case_rolling_lineage_preserved: bool
    every_case_complete_preflight_before_arithmetic: bool
    arbitrary_length_general_strang_path_integrated: bool
    parent_custody_authenticated: bool
    formal_tests_closed: int
    fields_closed: int
    blockers_closed: int
    result_slots_filled: int
    tracker_files_edited: int
    passed: bool
    report_sha256: str


@dataclass(frozen=True)
class _PreflightStep:
    supplied: SuppliedPathStep
    fixture: object
    selection: object
    lineage_before: object
    lineage_after: object
    source_serial: Optional[int]
    created_serial: Optional[int]
    left_values: Mapping[int, float]
    right_values: Mapping[int, float]


def _frozen_increment(
    *, serial: int, low_word: int, step_index: int, right: bool
) -> float:
    if right:
        numerator = ((7 * serial + 3 * low_word + 5 * step_index) % 13) - 6
    else:
        numerator = ((5 * serial + 2 * low_word + 3 * step_index) % 11) - 5
    return float(numerator) / 64.0


def _advance_lineage(test29_api: ModuleType, lineage, selection):
    advanced, source_serial, created_serial = test29_api._advance_lineage(
        lineage, selection
    )
    if type(advanced) is not test29_api.LineageState:
        raise SyntheticTwoMacrostepPathError("Test-29 lineage result type differs")
    return advanced, source_serial, created_serial


def build_frozen_two_macrostep_path_input(
    single_api: ModuleType,
    test29_api: ModuleType,
    test30_api: ModuleType,
    first_word: int = 2,
    second_word: int = 27,
) -> SuppliedTwoMacrostepPathInput:
    """Build deterministic two-step supplied data without asserting any law."""

    _require_parent_modules(single_api, test29_api, test30_api)
    words = (
        _exact_uint64(first_word, name="first_word"),
        _exact_uint64(second_word, name="second_word"),
    )
    design = test30_api.frozen_synthetic_design()
    active = tuple(item.serial for item in design.initial_occurrences)
    lineage = test29_api.LineageState(active, (), max(active) + 1)
    steps = []
    for step_index, word in enumerate(words):
        fixture = dynamic_central_jump_fixture(test29_api, len(lineage.active_serials))
        selection = test29_api.select_one_step(
            fixture, fixture.initial_state_id, word
        )
        next_lineage, _, _ = _advance_lineage(test29_api, lineage, selection)
        low_word = word & (FROZEN_LOW_WORD_COUNT - 1)
        left = tuple(
            single_api._addressed_increment(
                test30_api,
                run_id=FROZEN_RUN_ID,
                step_index=step_index,
                serial=serial,
                tag=test30_api.TAG_BROWNIAN_LEFT,
                increment=_frozen_increment(
                    serial=serial,
                    low_word=low_word,
                    step_index=step_index,
                    right=False,
                ),
            )
            for serial in lineage.active_serials
        )
        central = test29_api.AddressedUint64Word(
            test29_api.CP24CompatibleAddress(FROZEN_RUN_ID, step_index, 0),
            word,
        )
        right = tuple(
            single_api._addressed_increment(
                test30_api,
                run_id=FROZEN_RUN_ID,
                step_index=step_index,
                serial=serial,
                tag=test30_api.TAG_BROWNIAN_RIGHT,
                increment=_frozen_increment(
                    serial=serial,
                    low_word=low_word,
                    step_index=step_index,
                    right=True,
                ),
            )
            for serial in next_lineage.active_serials
        )
        steps.append(SuppliedPathStep(step_index, left, central, right))
        lineage = next_lineage
    return SuppliedTwoMacrostepPathInput(
        FROZEN_RUN_ID, FROZEN_MACROSTEP_WIDTH, tuple(steps)
    )


def _increment_payload(items: Tuple[object, ...]):
    return [
        {
            "domain": item.address.domain,
            "domain_tag": item.address.domain_tag,
            "run_id": item.address.run_id,
            "step_index": item.address.step_index,
            "occurrence_serial": item.address.occurrence_serial,
            "proposal_index": item.address.proposal_index,
            "philox_key": list(item.address.philox_key),
            "philox_counter": list(item.address.philox_counter),
            "increment_hex": item.increment.hex(),
        }
        for item in items
    ]


def _input_payload(value: SuppliedTwoMacrostepPathInput) -> Mapping[str, object]:
    if type(value) is not SuppliedTwoMacrostepPathInput:
        raise TypeError("value must be an exact SuppliedTwoMacrostepPathInput")
    return {
        "run_id": value.run_id,
        "macrostep_width_hex": value.macrostep_width.hex(),
        "steps": [
            {
                "step_index": step.step_index,
                "left_increments": _increment_payload(step.left_increments),
                "central_word": {
                    "key": list(step.central_word.address.key),
                    "counter": list(step.central_word.address.counter),
                    "raw64_word": step.central_word.raw64_word,
                },
                "right_increments": _increment_payload(step.right_increments),
            }
            for step in value.steps
        ],
    }


def _state_snapshot(occurrences: Mapping[int, object]):
    return tuple(
        (serial, occurrences[serial].kind, occurrences[serial].coordinate)
        for serial in sorted(occurrences)
    )


def _checked_serial_tuple(value: object, *, name: str) -> Tuple[int, ...]:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    checked = tuple(_exact_uint64(item, name=name + " item") for item in value)
    if any(item == 0 for item in checked) or tuple(sorted(set(checked))) != checked:
        raise ValueError(name + " must contain increasing unique positive serials")
    return checked


def _checked_snapshot(value: object, *, name: str):
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    rows = []
    for row in value:
        if type(row) is not tuple or len(row) != 3:
            raise TypeError(name + " rows must be exact length-three tuples")
        serial = _exact_uint64(row[0], name=name + " serial")
        kind = _exact_text(row[1], name=name + " kind")
        coordinate = _finite_float(row[2], name=name + " coordinate")
        if serial == 0 or kind not in ("A", "B"):
            raise ValueError(name + " row is invalid")
        rows.append(
            {"serial": serial, "kind": kind, "coordinate_hex": coordinate.hex()}
        )
    if tuple(row["serial"] for row in rows) != tuple(
        sorted(row["serial"] for row in rows)
    ) or len({row["serial"] for row in rows}) != len(rows):
        raise ValueError(name + " serial roster is invalid")
    return rows


def _step_result_payload(result: TwoMacrostepStepResult) -> Mapping[str, object]:
    if type(result) is not TwoMacrostepStepResult:
        raise TypeError("step result must have the exact result type")
    if type(result.normal_cell_indices) is not tuple:
        raise TypeError("normal cells must be an exact tuple")
    cells = tuple(
        _exact_uint64(cell, name="normal cell")
        for cell in result.normal_cell_indices
    )
    if any(cell not in (0, 1) for cell in cells):
        raise ValueError("normal cell lies outside the frozen layout")
    return {
        "step_index": _exact_uint64(result.step_index, name="step.step_index"),
        "raw64_word": _exact_uint64(result.raw64_word, name="step.raw64_word"),
        "route_id": _exact_text(result.route_id, name="step.route_id"),
        "family": _exact_text(result.family, name="step.family"),
        "source_index": _exact_optional_uint64(
            result.source_index, name="step.source_index"
        ),
        "source_serial": _exact_optional_uint64(
            result.source_serial, name="step.source_serial"
        ),
        "created_serial": _exact_optional_uint64(
            result.created_serial, name="step.created_serial"
        ),
        "normal_cell_indices": list(cells),
        "active_serials_before": list(
            _checked_serial_tuple(
                result.active_serials_before, name="step.active_serials_before"
            )
        ),
        "retired_serials_before": list(
            _checked_serial_tuple(
                result.retired_serials_before, name="step.retired_serials_before"
            )
        ),
        "active_serials_after": list(
            _checked_serial_tuple(
                result.active_serials_after, name="step.active_serials_after"
            )
        ),
        "retired_serials_after": list(
            _checked_serial_tuple(
                result.retired_serials_after, name="step.retired_serials_after"
            )
        ),
        "next_serial_before": _exact_uint64(
            result.next_serial_before, name="step.next_serial_before"
        ),
        "next_serial_after": _exact_uint64(
            result.next_serial_after, name="step.next_serial_after"
        ),
        "state_before": _checked_snapshot(result.state_before, name="step.state_before"),
        "state_after_left": _checked_snapshot(
            result.state_after_left, name="step.state_after_left"
        ),
        "state_after_jump": _checked_snapshot(
            result.state_after_jump, name="step.state_after_jump"
        ),
        "state_after_right": _checked_snapshot(
            result.state_after_right, name="step.state_after_right"
        ),
        "left_heun_application_count": _exact_uint64(
            result.left_heun_application_count,
            name="step.left_heun_application_count",
        ),
        "central_jump_count": _exact_uint64(
            result.central_jump_count, name="step.central_jump_count"
        ),
        "right_heun_application_count": _exact_uint64(
            result.right_heun_application_count,
            name="step.right_heun_application_count",
        ),
        "address_count": _exact_uint64(
            result.address_count, name="step.address_count"
        ),
    }


def _path_report_payload(result: TwoMacrostepPathResult) -> Mapping[str, object]:
    if type(result) is not TwoMacrostepPathResult:
        raise TypeError("result must be an exact TwoMacrostepPathResult")
    if type(result.steps) is not tuple:
        raise TypeError("result.steps must be an exact tuple")
    return {
        "schema_version": _exact_text(
            result.schema_version, name="result.schema_version"
        ),
        "predicate": _exact_text(result.predicate, name="result.predicate"),
        "scope": _exact_text(result.scope, name="result.scope"),
        "strict_nonclaims": _exact_text(
            result.strict_nonclaims, name="result.strict_nonclaims"
        ),
        "failure_policy": _exact_text(
            result.failure_policy, name="result.failure_policy"
        ),
        "run_id": _exact_uint64(result.run_id, name="result.run_id"),
        "macrostep_width_hex": _finite_float(
            result.macrostep_width,
            name="result.macrostep_width",
            positive=True,
        ).hex(),
        "input_sha256": _exact_sha256(
            result.input_sha256, name="result.input_sha256"
        ),
        "steps": [_step_result_payload(step) for step in result.steps],
        "total_left_heun_applications": _exact_uint64(
            result.total_left_heun_applications,
            name="result.total_left_heun_applications",
        ),
        "total_central_jumps": _exact_uint64(
            result.total_central_jumps, name="result.total_central_jumps"
        ),
        "total_right_heun_applications": _exact_uint64(
            result.total_right_heun_applications,
            name="result.total_right_heun_applications",
        ),
        "total_address_count": _exact_uint64(
            result.total_address_count, name="result.total_address_count"
        ),
        "complete_input_preflight_before_first_arithmetic": _exact_bool(
            result.complete_input_preflight_before_first_arithmetic,
            name="result.complete_input_preflight_before_first_arithmetic",
        ),
        "global_address_identities_unique": _exact_bool(
            result.global_address_identities_unique,
            name="result.global_address_identities_unique",
        ),
        "boundary_state_continuity": _exact_bool(
            result.boundary_state_continuity,
            name="result.boundary_state_continuity",
        ),
        "rolling_test29_fresh_retired_lineage_preserved": _exact_bool(
            result.rolling_test29_fresh_retired_lineage_preserved,
            name="result.rolling_test29_fresh_retired_lineage_preserved",
        ),
        "bounded_two_macrostep_path_integrated": _exact_bool(
            result.bounded_two_macrostep_path_integrated,
            name="result.bounded_two_macrostep_path_integrated",
        ),
        "arbitrary_length_general_strang_path_integrated": _exact_bool(
            result.arbitrary_length_general_strang_path_integrated,
            name="result.arbitrary_length_general_strang_path_integrated",
        ),
        "parent_custody_authenticated": _exact_bool(
            result.parent_custody_authenticated,
            name="result.parent_custody_authenticated",
        ),
        "test28_initializer_admissible": _exact_bool(
            result.test28_initializer_admissible,
            name="result.test28_initializer_admissible",
        ),
        "live_cp23_stream_consumed": _exact_bool(
            result.live_cp23_stream_consumed,
            name="result.live_cp23_stream_consumed",
        ),
        "live_cp24_stream_consumed": _exact_bool(
            result.live_cp24_stream_consumed,
            name="result.live_cp24_stream_consumed",
        ),
        "continuous_gaussian_destination_sampled": _exact_bool(
            result.continuous_gaussian_destination_sampled,
            name="result.continuous_gaussian_destination_sampled",
        ),
        "waiting_clock_or_acceptance_thinning_executed": _exact_bool(
            result.waiting_clock_or_acceptance_thinning_executed,
            name="result.waiting_clock_or_acceptance_thinning_executed",
        ),
        "step_halving_or_endpoint_law_qualified": _exact_bool(
            result.step_halving_or_endpoint_law_qualified,
            name="result.step_halving_or_endpoint_law_qualified",
        ),
        "formal_test28_closed": _exact_bool(
            result.formal_test28_closed, name="result.formal_test28_closed"
        ),
        "formal_test29_closed": _exact_bool(
            result.formal_test29_closed, name="result.formal_test29_closed"
        ),
        "formal_test30_closed": _exact_bool(
            result.formal_test30_closed, name="result.formal_test30_closed"
        ),
        "fields_closed": _exact_uint64(
            result.fields_closed, name="result.fields_closed"
        ),
        "blockers_closed": _exact_uint64(
            result.blockers_closed, name="result.blockers_closed"
        ),
        "result_slots_filled": _exact_uint64(
            result.result_slots_filled, name="result.result_slots_filled"
        ),
        "tracker_files_edited": _exact_uint64(
            result.tracker_files_edited, name="result.tracker_files_edited"
        ),
        "passed": _exact_bool(result.passed, name="result.passed"),
    }


def recompute_two_macrostep_path_report_sha256(
    result: TwoMacrostepPathResult,
) -> str:
    return _canonical_digest(_path_report_payload(result))


def _validate_path_result_structure(
    result: TwoMacrostepPathResult,
) -> TwoMacrostepPathResult:
    _path_report_payload(result)
    if (
        result.schema_version != SCHEMA_VERSION
        or result.predicate != PREDICATE
        or result.scope != QUALIFICATION_SCOPE
        or result.strict_nonclaims != STRICT_NONCLAIMS
        or result.failure_policy != FAILURE_POLICY
    ):
        raise SyntheticTwoMacrostepPathError("result contract identity differs")
    if result.run_id != FROZEN_RUN_ID or (
        result.macrostep_width.hex() != FROZEN_MACROSTEP_WIDTH.hex()
    ):
        raise SyntheticTwoMacrostepPathError("result frozen identity differs")
    if len(result.steps) != 2 or tuple(step.step_index for step in result.steps) != (
        0,
        1,
    ):
        raise SyntheticTwoMacrostepPathError("result step roster differs")
    if result.steps[0].state_before != ((1, "A", 0.75), (2, "B", -0.4)):
        raise SyntheticTwoMacrostepPathError("result initial state differs")
    if result.steps[0].state_after_right != result.steps[1].state_before:
        raise SyntheticTwoMacrostepPathError("step boundary state is discontinuous")
    if (
        result.steps[0].active_serials_after
        != result.steps[1].active_serials_before
        or result.steps[0].retired_serials_after
        != result.steps[1].retired_serials_before
        or result.steps[0].next_serial_after != result.steps[1].next_serial_before
    ):
        raise SyntheticTwoMacrostepPathError("step boundary lineage is discontinuous")
    for step in result.steps:
        if step.family not in ("birth", "death", "replacement"):
            raise SyntheticTwoMacrostepPathError("step family differs")
        if tuple(row[0] for row in step.state_before) != step.active_serials_before:
            raise SyntheticTwoMacrostepPathError("step initial coordinate roster differs")
        if tuple(row[0] for row in step.state_after_right) != step.active_serials_after:
            raise SyntheticTwoMacrostepPathError("step final coordinate roster differs")
        if (
            step.left_heun_application_count != len(step.active_serials_before)
            or step.central_jump_count != 1
            or step.right_heun_application_count != len(step.active_serials_after)
            or step.address_count
            != len(step.active_serials_before) + 1 + len(step.active_serials_after)
        ):
            raise SyntheticTwoMacrostepPathError("step application counts differ")
    if result.total_left_heun_applications != sum(
        step.left_heun_application_count for step in result.steps
    ) or result.total_central_jumps != 2 or result.total_right_heun_applications != sum(
        step.right_heun_application_count for step in result.steps
    ) or result.total_address_count != sum(step.address_count for step in result.steps):
        raise SyntheticTwoMacrostepPathError("aggregate application counts differ")
    expected_true = (
        result.complete_input_preflight_before_first_arithmetic,
        result.global_address_identities_unique,
        result.boundary_state_continuity,
        result.rolling_test29_fresh_retired_lineage_preserved,
        result.bounded_two_macrostep_path_integrated,
        result.passed,
    )
    expected_false = (
        result.arbitrary_length_general_strang_path_integrated,
        result.parent_custody_authenticated,
        result.test28_initializer_admissible,
        result.live_cp23_stream_consumed,
        result.live_cp24_stream_consumed,
        result.continuous_gaussian_destination_sampled,
        result.waiting_clock_or_acceptance_thinning_executed,
        result.step_halving_or_endpoint_law_qualified,
        result.formal_test28_closed,
        result.formal_test29_closed,
        result.formal_test30_closed,
    )
    if not all(value is True for value in expected_true) or not all(
        value is False for value in expected_false
    ):
        raise SyntheticTwoMacrostepPathError("result positive or negative flag differs")
    if any(
        value != 0
        for value in (
            result.fields_closed,
            result.blockers_closed,
            result.result_slots_filled,
            result.tracker_files_edited,
        )
    ):
        raise SyntheticTwoMacrostepPathError("result project delta differs")
    _exact_sha256(result.report_sha256, name="result.report_sha256")
    if result.report_sha256 != recompute_two_macrostep_path_report_sha256(result):
        raise SyntheticTwoMacrostepPathError("result report digest differs")
    return result


def _preflight_path(
    single_api: ModuleType,
    test29_api: ModuleType,
    test30_api: ModuleType,
    supplied: SuppliedTwoMacrostepPathInput,
):
    _require_parent_modules(single_api, test29_api, test30_api)
    if type(supplied) is not SuppliedTwoMacrostepPathInput:
        raise TypeError("supplied must be an exact SuppliedTwoMacrostepPathInput")
    run_id = _exact_uint64(supplied.run_id, name="supplied.run_id")
    width = _finite_float(
        supplied.macrostep_width,
        name="supplied.macrostep_width",
        positive=True,
    )
    if run_id != FROZEN_RUN_ID or width.hex() != FROZEN_MACROSTEP_WIDTH.hex():
        raise SyntheticTwoMacrostepPathError("supplied frozen identity differs")
    if type(supplied.steps) is not tuple or len(supplied.steps) != 2:
        raise SyntheticTwoMacrostepPathError("supplied must contain exactly two steps")
    design = test30_api.frozen_synthetic_design()
    active = tuple(item.serial for item in design.initial_occurrences)
    lineage = test29_api.LineageState(active, (), max(active) + 1)
    plans = []
    identities = []
    for step_index, step in enumerate(supplied.steps):
        if type(step) is not SuppliedPathStep:
            raise TypeError("supplied steps must have the exact SuppliedPathStep type")
        actual_step = _exact_uint64(step.step_index, name="step.step_index")
        if actual_step != step_index:
            raise SyntheticTwoMacrostepPathError("step index roster differs")
        fixture = dynamic_central_jump_fixture(
            test29_api, len(lineage.active_serials)
        )
        parent_qualification = test29_api.qualify_finite_acyclic_fixture(fixture)
        if (
            not parent_qualification.cp24_compatible_address_consumption_defined
            or not parent_qualification.unconditional_bounded_fixture_completion_proved
            or parent_qualification.formal_test29_closed
        ):
            raise SyntheticTwoMacrostepPathError("Test-29 qualification differs")
        central = single_api._validate_central_word(
            test29_api,
            step.central_word,
            run_id=run_id,
            step_index=step_index,
        )
        jump_run = test29_api.run_addressed_acyclic_fixture(
            fixture, (central,), run_id=run_id, step_index=step_index
        )
        test29_api.validate_addressed_acyclic_run_result(
            fixture, (central,), jump_run
        )
        if jump_run.consumed_word_count != 1 or len(jump_run.transitions) != 1:
            raise AssertionError("rank-one fixture did not consume one word")
        selection = jump_run.transitions[0].selection
        lineage_after, source_serial, created_serial = _advance_lineage(
            test29_api, lineage, selection
        )
        left_values = single_api._validate_increment_roster(
            test30_api,
            step.left_increments,
            expected_serials=lineage.active_serials,
            run_id=run_id,
            step_index=step_index,
            tag=test30_api.TAG_BROWNIAN_LEFT,
            label="step-%d-left" % step_index,
        )
        right_values = single_api._validate_increment_roster(
            test30_api,
            step.right_increments,
            expected_serials=lineage_after.active_serials,
            run_id=run_id,
            step_index=step_index,
            tag=test30_api.TAG_BROWNIAN_RIGHT,
            label="step-%d-right" % step_index,
        )
        identities.extend(
            (item.address.philox_key, item.address.philox_counter)
            for item in step.left_increments + step.right_increments
        )
        identities.append((central.address.key, central.address.counter))
        plans.append(
            _PreflightStep(
                supplied=step,
                fixture=fixture,
                selection=selection,
                lineage_before=lineage,
                lineage_after=lineage_after,
                source_serial=source_serial,
                created_serial=created_serial,
                left_values=left_values,
                right_values=right_values,
            )
        )
        lineage = lineage_after
    if len(set(identities)) != len(identities):
        raise SyntheticTwoMacrostepPathError("path reused an address identity")
    input_sha256 = _canonical_digest(_input_payload(supplied))
    return design, tuple(plans), len(identities), input_sha256


def _route_for_selection(fixture, selection):
    for route in fixture.initial_state.routes:
        if route.route_id == selection.route_id:
            return route
    raise AssertionError("selected route is absent from its fixture")


def _created_occurrence(test29_api: ModuleType, test30_api: ModuleType, plan):
    route = _route_for_selection(plan.fixture, plan.selection)
    if route.gaussian_destination is None or plan.created_serial is None:
        raise AssertionError("destination-bearing route omitted its destination")
    if len(plan.selection.normal_cells) != 1:
        raise AssertionError("frozen destination must be one-dimensional")
    cell = plan.selection.normal_cells[0]
    mean = float(route.gaussian_destination.mean[0])
    standard_deviation = math.sqrt(float(route.gaussian_destination.variance[0]))
    coordinate = mean + standard_deviation * cell.midpoint_representative()
    if not math.isfinite(coordinate):
        raise ArithmeticError("normal-cell midpoint became non-finite")
    kind = "A" if plan.selection.family == test29_api.FAMILY_BIRTH else "B"
    return test30_api.SyntheticOccurrence(plan.created_serial, kind, coordinate)


def _execute_two_macrostep_path_core(
    single_api: ModuleType,
    test29_api: ModuleType,
    test30_api: ModuleType,
    supplied: SuppliedTwoMacrostepPathInput,
) -> TwoMacrostepPathResult:
    design, plans, total_addresses, input_sha256 = _preflight_path(
        single_api, test29_api, test30_api, supplied
    )
    current = {item.serial: item for item in design.initial_occurrences}
    step_results = []
    half = 0.5 * supplied.macrostep_width
    for plan in plans:
        before = _state_snapshot(current)
        after_left: Dict[int, object] = {}
        for serial in plan.lineage_before.active_serials:
            item = current[serial]
            target = (
                design.long_run_mean_a if item.kind == "A" else design.long_run_mean_b
            )
            coordinate = test30_api._heun_half(
                item.coordinate,
                duration=half,
                increment=plan.left_values[serial],
                theta=design.mean_reversion,
                diffusion=design.diffusion,
                long_run_mean=target,
            )
            after_left[serial] = test30_api.SyntheticOccurrence(
                serial, item.kind, coordinate
            )
        after_jump = dict(after_left)
        if plan.source_serial is not None:
            if plan.source_serial not in after_jump:
                raise AssertionError("selected source is not live")
            del after_jump[plan.source_serial]
        if plan.created_serial is not None:
            created = _created_occurrence(test29_api, test30_api, plan)
            if created.serial in after_jump:
                raise AssertionError("fresh serial collides with a live occurrence")
            after_jump[created.serial] = created
        if tuple(sorted(after_jump)) != plan.lineage_after.active_serials:
            raise AssertionError("coordinate and Test-29 lineage rosters differ")
        after_right: Dict[int, object] = {}
        for serial in plan.lineage_after.active_serials:
            item = after_jump[serial]
            target = (
                design.long_run_mean_a if item.kind == "A" else design.long_run_mean_b
            )
            coordinate = test30_api._heun_half(
                item.coordinate,
                duration=half,
                increment=plan.right_values[serial],
                theta=design.mean_reversion,
                diffusion=design.diffusion,
                long_run_mean=target,
            )
            after_right[serial] = test30_api.SyntheticOccurrence(
                serial, item.kind, coordinate
            )
        step_results.append(
            TwoMacrostepStepResult(
                step_index=plan.supplied.step_index,
                raw64_word=plan.supplied.central_word.raw64_word,
                route_id=plan.selection.route_id,
                family=plan.selection.family,
                source_index=plan.selection.source_index,
                source_serial=plan.source_serial,
                created_serial=plan.created_serial,
                normal_cell_indices=tuple(
                    cell.index for cell in plan.selection.normal_cells
                ),
                active_serials_before=plan.lineage_before.active_serials,
                retired_serials_before=plan.lineage_before.retired_serials,
                active_serials_after=plan.lineage_after.active_serials,
                retired_serials_after=plan.lineage_after.retired_serials,
                next_serial_before=plan.lineage_before.next_serial,
                next_serial_after=plan.lineage_after.next_serial,
                state_before=before,
                state_after_left=_state_snapshot(after_left),
                state_after_jump=_state_snapshot(after_jump),
                state_after_right=_state_snapshot(after_right),
                left_heun_application_count=len(plan.lineage_before.active_serials),
                central_jump_count=1,
                right_heun_application_count=len(plan.lineage_after.active_serials),
                address_count=(
                    len(plan.lineage_before.active_serials)
                    + 1
                    + len(plan.lineage_after.active_serials)
                ),
            )
        )
        current = after_right
    steps = tuple(step_results)
    provisional = TwoMacrostepPathResult(
        schema_version=SCHEMA_VERSION,
        predicate=PREDICATE,
        scope=QUALIFICATION_SCOPE,
        strict_nonclaims=STRICT_NONCLAIMS,
        failure_policy=FAILURE_POLICY,
        run_id=supplied.run_id,
        macrostep_width=supplied.macrostep_width,
        input_sha256=input_sha256,
        report_sha256="0" * 64,
        steps=steps,
        total_left_heun_applications=sum(
            step.left_heun_application_count for step in steps
        ),
        total_central_jumps=2,
        total_right_heun_applications=sum(
            step.right_heun_application_count for step in steps
        ),
        total_address_count=total_addresses,
        complete_input_preflight_before_first_arithmetic=True,
        global_address_identities_unique=True,
        boundary_state_continuity=steps[0].state_after_right == steps[1].state_before,
        rolling_test29_fresh_retired_lineage_preserved=True,
        bounded_two_macrostep_path_integrated=True,
        arbitrary_length_general_strang_path_integrated=False,
        parent_custody_authenticated=False,
        test28_initializer_admissible=False,
        live_cp23_stream_consumed=False,
        live_cp24_stream_consumed=False,
        continuous_gaussian_destination_sampled=False,
        waiting_clock_or_acceptance_thinning_executed=False,
        step_halving_or_endpoint_law_qualified=False,
        formal_test28_closed=False,
        formal_test29_closed=False,
        formal_test30_closed=False,
        fields_closed=0,
        blockers_closed=0,
        result_slots_filled=0,
        tracker_files_edited=0,
        passed=True,
    )
    result = replace(
        provisional,
        report_sha256=recompute_two_macrostep_path_report_sha256(provisional),
    )
    return _validate_path_result_structure(result)


def validate_two_macrostep_path_result(
    single_api: ModuleType,
    test29_api: ModuleType,
    test30_api: ModuleType,
    supplied: SuppliedTwoMacrostepPathInput,
    result: TwoMacrostepPathResult,
) -> TwoMacrostepPathResult:
    """Reconstruct the exact supplied path and compare every result field."""

    _validate_path_result_structure(result)
    expected = _execute_two_macrostep_path_core(
        single_api, test29_api, test30_api, supplied
    )
    single_api._strict_compare_dataclass_fields(
        result,
        expected,
        expected_type=TwoMacrostepPathResult,
        name="two_macrostep_result",
    )
    return result


def run_supplied_two_macrostep_path(
    single_api: ModuleType,
    test29_api: ModuleType,
    test30_api: ModuleType,
    supplied: SuppliedTwoMacrostepPathInput,
) -> TwoMacrostepPathResult:
    result = _execute_two_macrostep_path_core(
        single_api, test29_api, test30_api, supplied
    )
    return validate_two_macrostep_path_result(
        single_api, test29_api, test30_api, supplied, result
    )


def _checked_pair_counts(rows: object, *, name: str):
    if type(rows) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    checked = []
    previous = None
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise TypeError(name + " rows must be exact pairs")
        key = row[0]
        if type(key) is str:
            key = _exact_text(key, name=name + " key")
        else:
            key = _exact_uint64(key, name=name + " key")
        count = _exact_uint64(row[1], name=name + " count")
        if count == 0 or (previous is not None and key <= previous):
            raise ValueError(name + " must be sorted with positive counts")
        previous = key
        checked.append((key, count))
    return tuple(checked)


def _qualification_payload(result: FrozenTwoMacrostepQualification):
    if type(result) is not FrozenTwoMacrostepQualification:
        raise TypeError("result must be an exact FrozenTwoMacrostepQualification")
    return {
        "schema_version": _exact_text(result.schema_version, name="q.schema_version"),
        "predicate": _exact_text(result.predicate, name="q.predicate"),
        "scope": _exact_text(result.scope, name="q.scope"),
        "strict_nonclaims": _exact_text(
            result.strict_nonclaims, name="q.strict_nonclaims"
        ),
        "failure_policy": _exact_text(
            result.failure_policy, name="q.failure_policy"
        ),
        "ordered_word_pair_cases_checked": _exact_uint64(
            result.ordered_word_pair_cases_checked,
            name="q.ordered_word_pair_cases_checked",
        ),
        "route_pair_counts": [
            list(row)
            for row in _checked_pair_counts(
                result.route_pair_counts, name="q.route_pair_counts"
            )
        ],
        "boundary_cardinality_counts": [
            list(row)
            for row in _checked_pair_counts(
                result.boundary_cardinality_counts,
                name="q.boundary_cardinality_counts",
            )
        ],
        "final_cardinality_counts": [
            list(row)
            for row in _checked_pair_counts(
                result.final_cardinality_counts,
                name="q.final_cardinality_counts",
            )
        ],
        "distinct_input_sha256_count": _exact_uint64(
            result.distinct_input_sha256_count,
            name="q.distinct_input_sha256_count",
        ),
        "distinct_report_sha256_count": _exact_uint64(
            result.distinct_report_sha256_count,
            name="q.distinct_report_sha256_count",
        ),
        "ordered_case_commitment_sha256": _exact_sha256(
            result.ordered_case_commitment_sha256,
            name="q.ordered_case_commitment_sha256",
        ),
        "all_nine_route_family_pairs_covered": _exact_bool(
            result.all_nine_route_family_pairs_covered,
            name="q.all_nine_route_family_pairs_covered",
        ),
        "every_case_boundary_continuous": _exact_bool(
            result.every_case_boundary_continuous,
            name="q.every_case_boundary_continuous",
        ),
        "every_case_global_addresses_unique": _exact_bool(
            result.every_case_global_addresses_unique,
            name="q.every_case_global_addresses_unique",
        ),
        "every_case_rolling_lineage_preserved": _exact_bool(
            result.every_case_rolling_lineage_preserved,
            name="q.every_case_rolling_lineage_preserved",
        ),
        "every_case_complete_preflight_before_arithmetic": _exact_bool(
            result.every_case_complete_preflight_before_arithmetic,
            name="q.every_case_complete_preflight_before_arithmetic",
        ),
        "arbitrary_length_general_strang_path_integrated": _exact_bool(
            result.arbitrary_length_general_strang_path_integrated,
            name="q.arbitrary_length_general_strang_path_integrated",
        ),
        "parent_custody_authenticated": _exact_bool(
            result.parent_custody_authenticated,
            name="q.parent_custody_authenticated",
        ),
        "formal_tests_closed": _exact_uint64(
            result.formal_tests_closed, name="q.formal_tests_closed"
        ),
        "fields_closed": _exact_uint64(result.fields_closed, name="q.fields_closed"),
        "blockers_closed": _exact_uint64(
            result.blockers_closed, name="q.blockers_closed"
        ),
        "result_slots_filled": _exact_uint64(
            result.result_slots_filled, name="q.result_slots_filled"
        ),
        "tracker_files_edited": _exact_uint64(
            result.tracker_files_edited, name="q.tracker_files_edited"
        ),
        "passed": _exact_bool(result.passed, name="q.passed"),
    }


def recompute_frozen_two_macrostep_qualification_report_sha256(
    result: FrozenTwoMacrostepQualification,
) -> str:
    return _canonical_digest(_qualification_payload(result))


def _validate_qualification_structure(result: FrozenTwoMacrostepQualification):
    _qualification_payload(result)
    if (
        result.schema_version != SCHEMA_VERSION
        or result.predicate != PREDICATE
        or result.scope != QUALIFICATION_SCOPE
        or result.strict_nonclaims != STRICT_NONCLAIMS
        or result.failure_policy != FAILURE_POLICY
    ):
        raise SyntheticTwoMacrostepPathError("qualification identity differs")
    expected = {
        "ordered_word_pair_cases_checked": 1024,
        "route_pair_counts": (
            ("birth->birth", 256),
            ("birth->death", 128),
            ("birth->replacement", 128),
            ("death->birth", 128),
            ("death->death", 64),
            ("death->replacement", 64),
            ("replacement->birth", 128),
            ("replacement->death", 64),
            ("replacement->replacement", 64),
        ),
        "boundary_cardinality_counts": ((1, 256), (2, 256), (3, 512)),
        "final_cardinality_counts": (
            (0, 64),
            (1, 128),
            (2, 320),
            (3, 256),
            (4, 256),
        ),
        "distinct_input_sha256_count": 1024,
        "distinct_report_sha256_count": 1024,
    }
    if any(getattr(result, key) != value for key, value in expected.items()):
        raise SyntheticTwoMacrostepPathError("qualification exact counts differ")
    expected_true = (
        result.all_nine_route_family_pairs_covered,
        result.every_case_boundary_continuous,
        result.every_case_global_addresses_unique,
        result.every_case_rolling_lineage_preserved,
        result.every_case_complete_preflight_before_arithmetic,
        result.passed,
    )
    expected_false = (
        result.arbitrary_length_general_strang_path_integrated,
        result.parent_custody_authenticated,
    )
    if not all(value is True for value in expected_true) or not all(
        value is False for value in expected_false
    ):
        raise SyntheticTwoMacrostepPathError(
            "qualification positive or negative flag differs"
        )
    if any(
        value != 0
        for value in (
            result.formal_tests_closed,
            result.fields_closed,
            result.blockers_closed,
            result.result_slots_filled,
            result.tracker_files_edited,
        )
    ):
        raise SyntheticTwoMacrostepPathError("qualification project delta differs")
    _exact_sha256(result.report_sha256, name="q.report_sha256")
    if result.report_sha256 != (
        recompute_frozen_two_macrostep_qualification_report_sha256(result)
    ):
        raise SyntheticTwoMacrostepPathError("qualification report digest differs")
    return result


def _execute_frozen_two_macrostep_qualification_core(
    single_api: ModuleType, test29_api: ModuleType, test30_api: ModuleType
) -> FrozenTwoMacrostepQualification:
    _require_parent_modules(single_api, test29_api, test30_api)
    results = []
    route_pairs: Dict[str, int] = {}
    boundary_cardinalities: Dict[int, int] = {}
    final_cardinalities: Dict[int, int] = {}
    for first in range(FROZEN_LOW_WORD_COUNT):
        for second in range(FROZEN_LOW_WORD_COUNT):
            supplied = build_frozen_two_macrostep_path_input(
                single_api, test29_api, test30_api, first, second
            )
            result = _execute_two_macrostep_path_core(
                single_api, test29_api, test30_api, supplied
            )
            results.append(result)
            pair = result.steps[0].family + "->" + result.steps[1].family
            route_pairs[pair] = route_pairs.get(pair, 0) + 1
            boundary = len(result.steps[0].active_serials_after)
            final = len(result.steps[1].active_serials_after)
            boundary_cardinalities[boundary] = (
                boundary_cardinalities.get(boundary, 0) + 1
            )
            final_cardinalities[final] = final_cardinalities.get(final, 0) + 1
    ordered_commitment = _canonical_digest(
        [
            {
                "ordinal": ordinal,
                "input_sha256": result.input_sha256,
                "report_sha256": result.report_sha256,
            }
            for ordinal, result in enumerate(results)
        ]
    )
    every_boundary = all(result.boundary_state_continuity for result in results)
    every_address = all(result.global_address_identities_unique for result in results)
    every_lineage = all(
        result.rolling_test29_fresh_retired_lineage_preserved for result in results
    )
    every_preflight = all(
        result.complete_input_preflight_before_first_arithmetic for result in results
    )
    all_pairs = len(route_pairs) == 9
    provisional = FrozenTwoMacrostepQualification(
        schema_version=SCHEMA_VERSION,
        predicate=PREDICATE,
        scope=QUALIFICATION_SCOPE,
        strict_nonclaims=STRICT_NONCLAIMS,
        failure_policy=FAILURE_POLICY,
        ordered_word_pair_cases_checked=len(results),
        route_pair_counts=tuple(sorted(route_pairs.items())),
        boundary_cardinality_counts=tuple(sorted(boundary_cardinalities.items())),
        final_cardinality_counts=tuple(sorted(final_cardinalities.items())),
        distinct_input_sha256_count=len({r.input_sha256 for r in results}),
        distinct_report_sha256_count=len({r.report_sha256 for r in results}),
        ordered_case_commitment_sha256=ordered_commitment,
        all_nine_route_family_pairs_covered=all_pairs,
        every_case_boundary_continuous=every_boundary,
        every_case_global_addresses_unique=every_address,
        every_case_rolling_lineage_preserved=every_lineage,
        every_case_complete_preflight_before_arithmetic=every_preflight,
        arbitrary_length_general_strang_path_integrated=False,
        parent_custody_authenticated=False,
        formal_tests_closed=0,
        fields_closed=0,
        blockers_closed=0,
        result_slots_filled=0,
        tracker_files_edited=0,
        passed=(
            len(results) == 1024
            and all_pairs
            and every_boundary
            and every_address
            and every_lineage
            and every_preflight
        ),
        report_sha256="0" * 64,
    )
    result = replace(
        provisional,
        report_sha256=(
            recompute_frozen_two_macrostep_qualification_report_sha256(provisional)
        ),
    )
    return _validate_qualification_structure(result)


def validate_frozen_two_macrostep_qualification(
    single_api: ModuleType,
    test29_api: ModuleType,
    test30_api: ModuleType,
    result: FrozenTwoMacrostepQualification,
) -> FrozenTwoMacrostepQualification:
    _validate_qualification_structure(result)
    expected = _execute_frozen_two_macrostep_qualification_core(
        single_api, test29_api, test30_api
    )
    single_api._strict_compare_dataclass_fields(
        result,
        expected,
        expected_type=FrozenTwoMacrostepQualification,
        name="two_macrostep_qualification",
    )
    return result


def run_frozen_two_macrostep_qualification(
    single_api: ModuleType, test29_api: ModuleType, test30_api: ModuleType
) -> FrozenTwoMacrostepQualification:
    result = _execute_frozen_two_macrostep_qualification_core(
        single_api, test29_api, test30_api
    )
    return validate_frozen_two_macrostep_qualification(
        single_api, test29_api, test30_api, result
    )


__all__ = [
    "SCHEMA_VERSION",
    "PREDICATE",
    "QUALIFICATION_SCOPE",
    "STRICT_NONCLAIMS",
    "FAILURE_POLICY",
    "FROZEN_RUN_ID",
    "FROZEN_MACROSTEP_WIDTH",
    "FROZEN_STEP_COUNT",
    "FROZEN_LOW_WORD_COUNT",
    "SyntheticTwoMacrostepPathError",
    "SuppliedPathStep",
    "SuppliedTwoMacrostepPathInput",
    "TwoMacrostepStepResult",
    "TwoMacrostepPathResult",
    "FrozenTwoMacrostepQualification",
    "dynamic_central_jump_fixture",
    "build_frozen_two_macrostep_path_input",
    "recompute_two_macrostep_path_report_sha256",
    "validate_two_macrostep_path_result",
    "run_supplied_two_macrostep_path",
    "recompute_frozen_two_macrostep_qualification_report_sha256",
    "validate_frozen_two_macrostep_qualification",
    "run_frozen_two_macrostep_qualification",
]
