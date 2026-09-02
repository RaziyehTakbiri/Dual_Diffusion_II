"""Pure supplied-input integration of the stopped Test-29 and Test-30 precursors.

This module validates one deliberately narrow Strang-shaped macrostep:

1. one supplied physical Brownian increment advances every initial occurrence
   through a left stochastic-Heun half-step;
2. one supplied CP24-shaped uint64 word selects exactly one finite-acyclic
   Test-29 birth, death, or replacement transition; and
3. one supplied physical Brownian increment advances every surviving or newly
   created occurrence through a right stochastic-Heun half-step.

The parent modules are explicit dependency arguments.  The package custody
validator hard-pins and executes their exact stable-read bytes before passing
the resulting modules here; this source never opens or imports a project path.
The public functions only check exact module type, schema, and the presence of
required symbols.  They do not authenticate arbitrary caller-supplied modules
or constrain effects those arbitrary modules could perform.

Case validation is contextual: it accepts the exact supplied input and parent
APIs, reruns a nonrecursive internal execution core, and strictly compares
every result field and digest.  Frozen aggregate validation reruns all sixteen
ordered canonical cases through the same core and strictly compares the full
aggregate.  Digest recomputation without this reconstruction is not semantic
validation.

The central destination coordinate is the finite normal-quantile-cell midpoint
representative exposed by the Test-29 precursor.  It is not a continuous
Gaussian draw.  The Brownian values are supplied finite data, not random draws.
The initial state is the deterministic Test-30 synthetic fixture, not an
admitted Test-28 initializer.  Under validator-admitted hard-pinned parent
bytes, the construction has no clock, rejection loop, live stream,
stochastic-law, general split-step, scientific, or tracker effect.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
import json
import math
from types import ModuleType
from typing import Dict, Mapping, Optional, Tuple


SCHEMA_VERSION = "heterodiff-test29-test30-single-macrostep-integration-v1"
PREDICATE = (
    "SYNTHETIC_SUPPLIED_INPUT_SINGLE_MACROSTEP_LEFT_JUMP_RIGHT_INTEGRATION_VALIDATED"
)
QUALIFICATION_SCOPE = (
    "DETERMINISTIC_TEST30_INITIAL_STATE;SUPPLIED_CP23_SHAPED_PHYSICAL_HALF_"
    "INCREMENTS;ONE_SUPPLIED_CP24_SHAPED_TEST29_WORD;ONE_FINITE_ACYCLIC_"
    "CENTRAL_EDIT;LEFT_HEUN_THEN_JUMP_THEN_RIGHT_HEUN;LOW_WORD_EXHAUSTION"
)
STRICT_NONCLAIMS = (
    "NO_TEST28_INITIALIZER_OR_ADMISSION;NO_LIVE_CP23_OR_CP24_STREAM;"
    "NO_BROWNIAN_GAUSSIAN_OR_INDEPENDENCE_LAW;NO_CONTINUOUS_GAUSSIAN_"
    "DESTINATION;NO_WAITING_CLOCK_ACCEPTANCE_THINNING_OR_JUMP_SUBSTEP_LAW;"
    "NO_GENERAL_STRANG_PATH_OR_STEP_HALVING;NO_FORMAL_TEST_CLOSURE;"
    "NO_SCIENTIFIC_EXECUTION_OR_TRACKER_EFFECT;"
    "NO_ARBITRARY_PARENT_MODULE_AUTHENTICATION"
)
FAILURE_POLICY = "FAIL_CLOSED_NO_RETRY_NO_FALLBACK_NO_PARTIAL_RESULT"
EXPECTED_TEST29_SCHEMA = "formal-test29-finite-acyclic-route-oracle-v1"
EXPECTED_TEST30_SCHEMA = "heterodiff-formal-test30-synthetic-coupled-path-v1"

FROZEN_RUN_ID = 29_030
FROZEN_STEP_INDEX = 0
FROZEN_MACROSTEP_WIDTH = 0.25
FROZEN_LOW_WORD_COUNT = 16


class SyntheticSingleMacrostepError(ValueError):
    """Raised when the composite input or parent boundary is invalid."""


def _exact_uint64(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError("%s must be an exact built-in integer" % name)
    if value < 0 or value >= 1 << 64:
        raise ValueError("%s lies outside its uint64 range" % name)
    return value


def _finite_float(value: object, *, name: str, positive: bool = False) -> float:
    if type(value) is not float:
        raise TypeError("%s must be an exact built-in float" % name)
    if not math.isfinite(value):
        raise ValueError("%s must be finite" % name)
    if positive and value <= 0.0:
        raise ValueError("%s must be positive" % name)
    return value


def _canonical_digest(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def _require_parent_modules(test29_api: object, test30_api: object) -> None:
    if type(test29_api) is not ModuleType or type(test30_api) is not ModuleType:
        raise TypeError("parent APIs must be exact module objects")
    if (
        getattr(test29_api, "FORMAL_TEST29_FINITE_ACYCLIC_SCHEMA_VERSION", None)
        != EXPECTED_TEST29_SCHEMA
    ):
        raise SyntheticSingleMacrostepError("Test-29 parent schema differs")
    if getattr(test30_api, "SCHEMA_VERSION", None) != EXPECTED_TEST30_SCHEMA:
        raise SyntheticSingleMacrostepError("Test-30 parent schema differs")
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
        "select_one_step",
        "run_addressed_acyclic_fixture",
        "validate_addressed_acyclic_run_result",
        "qualify_finite_acyclic_fixture",
    )
    required_test30 = (
        "DOMAIN_BROWNIAN_LEFT",
        "DOMAIN_BROWNIAN_RIGHT",
        "TAG_BROWNIAN_LEFT",
        "TAG_BROWNIAN_RIGHT",
        "CP23BrownianAddress",
        "AddressedBrownianIncrement",
        "SyntheticOccurrence",
        "frozen_synthetic_design",
        "_heun_half",
    )
    if any(not hasattr(test29_api, name) for name in required_test29):
        raise SyntheticSingleMacrostepError(
            "Test-29 parent is missing a required symbol"
        )
    if any(not hasattr(test30_api, name) for name in required_test30):
        raise SyntheticSingleMacrostepError(
            "Test-30 parent is missing a required symbol"
        )


def frozen_central_jump_fixture(test29_api: ModuleType):
    """Construct the exact rank-one birth/death/replacement parent fixture."""

    if type(test29_api) is not ModuleType:
        raise TypeError("test29_api must be an exact module")
    gaussian_birth = test29_api.GaussianDestination(
        (Fraction(1, 4),), (Fraction(1, 4),)
    )
    gaussian_replacement = test29_api.GaussianDestination(
        (Fraction(-1, 4),), (Fraction(1, 1),)
    )
    root = test29_api.StateSpec(
        "macro-root",
        1,
        2,
        (
            test29_api.RouteSpec(
                "macro-birth",
                test29_api.FAMILY_BIRTH,
                "macro-birth-terminal",
                Fraction(1),
                Fraction(2),
                (),
                gaussian_birth,
            ),
            test29_api.RouteSpec(
                "macro-replacement",
                test29_api.FAMILY_REPLACEMENT,
                "macro-replacement-terminal",
                Fraction(1),
                Fraction(1),
                (Fraction(1, 2), Fraction(1, 2)),
                gaussian_replacement,
            ),
            test29_api.RouteSpec(
                "macro-death",
                test29_api.FAMILY_DEATH,
                "macro-death-terminal",
                Fraction(1),
                Fraction(1),
                (Fraction(1, 2), Fraction(1, 2)),
                None,
            ),
        ),
    )
    terminals = (
        test29_api.StateSpec("macro-birth-terminal", 0, 3, ()),
        test29_api.StateSpec("macro-replacement-terminal", 0, 2, ()),
        test29_api.StateSpec("macro-death-terminal", 0, 1, ()),
    )
    return test29_api.FixtureSpec(
        "test29-test30-single-macrostep-fixture",
        (root,) + terminals,
        "macro-root",
        test29_api.WordLayout(2, 1, 1, 1),
    )


@dataclass(frozen=True)
class SuppliedSingleMacrostepInput:
    """Complete preflightable supplied input for exactly one macrostep."""

    run_id: int
    step_index: int
    macrostep_width: float
    left_increments: Tuple[object, ...]
    central_word: object
    right_increments: Tuple[object, ...]

    def __post_init__(self) -> None:
        _exact_uint64(self.run_id, name="input.run_id")
        _exact_uint64(self.step_index, name="input.step_index")
        _finite_float(self.macrostep_width, name="input.macrostep_width", positive=True)
        if type(self.left_increments) is not tuple:
            raise TypeError("input.left_increments must be an exact tuple")
        if type(self.right_increments) is not tuple:
            raise TypeError("input.right_increments must be an exact tuple")


@dataclass(frozen=True)
class SingleMacrostepResult:
    schema_version: str
    predicate: str
    scope: str
    strict_nonclaims: str
    failure_policy: str
    run_id: int
    step_index: int
    macrostep_width: float
    input_sha256: str
    report_sha256: str
    route_id: str
    family: str
    source_index: Optional[int]
    source_serial: Optional[int]
    created_serial: Optional[int]
    normal_cell_indices: Tuple[int, ...]
    state_before: Tuple[Tuple[int, str, float], ...]
    state_after_left: Tuple[Tuple[int, str, float], ...]
    state_after_jump: Tuple[Tuple[int, str, float], ...]
    state_after_right: Tuple[Tuple[int, str, float], ...]
    left_heun_application_count: int
    central_jump_count: int
    right_heun_application_count: int
    address_count: int
    address_identities_unique: bool
    lineage_matches_test29: bool
    destination_is_normal_cell_midpoint_only: bool
    no_effect_claim_scoped_to_validator_admitted_parents: bool
    arbitrary_parent_modules_authenticated: bool
    test28_initializer_admissible: bool
    live_cp23_stream_consumed: bool
    live_cp24_stream_consumed: bool
    continuous_gaussian_destination_sampled: bool
    waiting_clock_or_acceptance_thinning_executed: bool
    general_strang_path_integrated: bool
    formal_test28_closed: bool
    formal_test29_closed: bool
    formal_test30_closed: bool
    passed: bool


@dataclass(frozen=True)
class FrozenSingleMacrostepQualification:
    schema_version: str
    predicate: str
    scope: str
    strict_nonclaims: str
    failure_policy: str
    low_word_cases_checked: int
    route_family_counts: Tuple[Tuple[str, int], ...]
    final_cardinality_counts: Tuple[Tuple[int, int], ...]
    source_serial_counts: Tuple[Tuple[int, int], ...]
    normal_cell_counts: Tuple[Tuple[int, int], ...]
    distinct_input_sha256_count: int
    distinct_report_sha256_count: int
    case_input_sha256s: Tuple[str, ...]
    case_report_sha256s: Tuple[str, ...]
    every_case_one_left_jump_right_macrostep: bool
    every_case_address_unique: bool
    every_case_lineage_matches_test29: bool
    birth_death_replacement_all_covered: bool
    no_effect_claim_scoped_to_validator_admitted_parents: bool
    arbitrary_parent_modules_authenticated: bool
    test28_initializer_admissible: bool
    live_parent_stream_consumed: bool
    continuous_gaussian_destination_sampled: bool
    general_strang_path_integrated: bool
    formal_tests_closed: int
    fields_closed: int
    blockers_closed: int
    result_slots_filled: int
    tracker_files_edited: int
    passed: bool
    report_sha256: str


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
    if len(text) != 64 or any(
        character not in "0123456789abcdef" for character in text
    ):
        raise ValueError(name + " must be lowercase SHA-256 hex")
    return text


def _checked_snapshot_payload(
    snapshot: object, *, name: str
) -> Tuple[Mapping[str, object], ...]:
    if type(snapshot) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    rows = []
    serials = set()
    for ordinal, row in enumerate(snapshot):
        if type(row) is not tuple or len(row) != 3:
            raise TypeError(name + " row must be an exact length-three tuple")
        serial = _exact_uint64(row[0], name=name + " serial")
        if serial == 0 or serial in serials:
            raise ValueError(name + " serial roster is invalid")
        serials.add(serial)
        kind = _exact_text(row[1], name=name + " kind")
        if kind not in ("A", "B"):
            raise ValueError(name + " kind is invalid")
        coordinate = _finite_float(row[2], name=name + " coordinate")
        rows.append(
            {
                "ordinal": ordinal,
                "serial": serial,
                "kind": kind,
                "coordinate_hex": coordinate.hex(),
            }
        )
    if tuple(sorted(serials)) != tuple(row["serial"] for row in rows):
        raise ValueError(name + " must use increasing serial order")
    return tuple(rows)


def _checked_pair_counts(
    rows: object, *, name: str, text_key: bool
) -> Tuple[Tuple[object, int], ...]:
    if type(rows) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    checked = []
    prior = None
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise TypeError(name + " row must be an exact pair")
        if text_key:
            key: object = _exact_text(row[0], name=name + " key")
        else:
            key = _exact_uint64(row[0], name=name + " key")
        count = _exact_uint64(row[1], name=name + " count")
        if count == 0:
            raise ValueError(name + " counts must be positive")
        if prior is not None and key <= prior:
            raise ValueError(name + " keys must be strictly increasing")
        prior = key
        checked.append((key, count))
    return tuple(checked)


def _single_macrostep_report_payload(
    result: SingleMacrostepResult,
) -> Mapping[str, object]:
    if type(result) is not SingleMacrostepResult:
        raise TypeError("result must be an exact SingleMacrostepResult")
    normal_cells = result.normal_cell_indices
    if type(normal_cells) is not tuple:
        raise TypeError("result.normal_cell_indices must be an exact tuple")
    checked_cells = tuple(
        _exact_uint64(cell, name="result.normal_cell_indices") for cell in normal_cells
    )
    if any(cell not in (0, 1) for cell in checked_cells):
        raise ValueError("result normal-cell index is outside the frozen layout")
    payload = {
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
        "step_index": _exact_uint64(result.step_index, name="result.step_index"),
        "macrostep_width_hex": _finite_float(
            result.macrostep_width,
            name="result.macrostep_width",
            positive=True,
        ).hex(),
        "input_sha256": _exact_sha256(result.input_sha256, name="result.input_sha256"),
        "route_id": _exact_text(result.route_id, name="result.route_id"),
        "family": _exact_text(result.family, name="result.family"),
        "source_index": _exact_optional_uint64(
            result.source_index, name="result.source_index"
        ),
        "source_serial": _exact_optional_uint64(
            result.source_serial, name="result.source_serial"
        ),
        "created_serial": _exact_optional_uint64(
            result.created_serial, name="result.created_serial"
        ),
        "normal_cell_indices": list(checked_cells),
        "state_before": list(
            _checked_snapshot_payload(result.state_before, name="result.state_before")
        ),
        "state_after_left": list(
            _checked_snapshot_payload(
                result.state_after_left, name="result.state_after_left"
            )
        ),
        "state_after_jump": list(
            _checked_snapshot_payload(
                result.state_after_jump, name="result.state_after_jump"
            )
        ),
        "state_after_right": list(
            _checked_snapshot_payload(
                result.state_after_right, name="result.state_after_right"
            )
        ),
        "left_heun_application_count": _exact_uint64(
            result.left_heun_application_count,
            name="result.left_heun_application_count",
        ),
        "central_jump_count": _exact_uint64(
            result.central_jump_count, name="result.central_jump_count"
        ),
        "right_heun_application_count": _exact_uint64(
            result.right_heun_application_count,
            name="result.right_heun_application_count",
        ),
        "address_count": _exact_uint64(
            result.address_count, name="result.address_count"
        ),
        "address_identities_unique": _exact_bool(
            result.address_identities_unique,
            name="result.address_identities_unique",
        ),
        "lineage_matches_test29": _exact_bool(
            result.lineage_matches_test29,
            name="result.lineage_matches_test29",
        ),
        "destination_is_normal_cell_midpoint_only": _exact_bool(
            result.destination_is_normal_cell_midpoint_only,
            name="result.destination_is_normal_cell_midpoint_only",
        ),
        "no_effect_claim_scoped_to_validator_admitted_parents": _exact_bool(
            result.no_effect_claim_scoped_to_validator_admitted_parents,
            name="result.no_effect_claim_scoped_to_validator_admitted_parents",
        ),
        "arbitrary_parent_modules_authenticated": _exact_bool(
            result.arbitrary_parent_modules_authenticated,
            name="result.arbitrary_parent_modules_authenticated",
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
        "general_strang_path_integrated": _exact_bool(
            result.general_strang_path_integrated,
            name="result.general_strang_path_integrated",
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
        "passed": _exact_bool(result.passed, name="result.passed"),
    }
    return payload


def recompute_single_macrostep_report_sha256(result: SingleMacrostepResult) -> str:
    """Recompute the complete material result digest, excluding only itself."""

    return _canonical_digest(_single_macrostep_report_payload(result))


def _validate_single_macrostep_result_structure(
    result: SingleMacrostepResult,
) -> SingleMacrostepResult:
    """Validate exact types, structural invariants, and the complete digest."""

    _single_macrostep_report_payload(result)
    if (
        result.schema_version != SCHEMA_VERSION
        or result.predicate != PREDICATE
        or result.scope != QUALIFICATION_SCOPE
        or result.strict_nonclaims != STRICT_NONCLAIMS
        or result.failure_policy != FAILURE_POLICY
    ):
        raise SyntheticSingleMacrostepError("result contract identity differs")
    if (
        result.run_id != FROZEN_RUN_ID
        or result.step_index != FROZEN_STEP_INDEX
        or result.macrostep_width.hex() != FROZEN_MACROSTEP_WIDTH.hex()
    ):
        raise SyntheticSingleMacrostepError("result frozen run identity differs")
    if result.family not in ("birth", "death", "replacement"):
        raise SyntheticSingleMacrostepError("result edit family differs")
    if result.state_before != ((1, "A", 0.75), (2, "B", -0.4)):
        raise SyntheticSingleMacrostepError("result initial state differs")
    if len(result.state_after_left) != 2:
        raise SyntheticSingleMacrostepError("result left state cardinality differs")
    if len(result.state_after_jump) != len(result.state_after_right):
        raise SyntheticSingleMacrostepError("result terminal cardinality differs")
    if tuple((row[0], row[1]) for row in result.state_after_jump) != tuple(
        (row[0], row[1]) for row in result.state_after_right
    ):
        raise SyntheticSingleMacrostepError("result right lineage roster differs")
    if (
        result.left_heun_application_count != 2
        or result.central_jump_count != 1
        or result.right_heun_application_count != len(result.state_after_right)
        or result.address_count != 3 + len(result.state_after_right)
    ):
        raise SyntheticSingleMacrostepError("result application counts differ")
    expected_true = (
        result.address_identities_unique,
        result.lineage_matches_test29,
        result.destination_is_normal_cell_midpoint_only,
        result.no_effect_claim_scoped_to_validator_admitted_parents,
        result.passed,
    )
    expected_false = (
        result.arbitrary_parent_modules_authenticated,
        result.test28_initializer_admissible,
        result.live_cp23_stream_consumed,
        result.live_cp24_stream_consumed,
        result.continuous_gaussian_destination_sampled,
        result.waiting_clock_or_acceptance_thinning_executed,
        result.general_strang_path_integrated,
        result.formal_test28_closed,
        result.formal_test29_closed,
        result.formal_test30_closed,
    )
    if not all(value is True for value in expected_true) or not all(
        value is False for value in expected_false
    ):
        raise SyntheticSingleMacrostepError("result positive or negative flag differs")
    _exact_sha256(result.report_sha256, name="result.report_sha256")
    if result.report_sha256 != recompute_single_macrostep_report_sha256(result):
        raise SyntheticSingleMacrostepError("result report digest differs")
    return result


def _strict_compare_value(actual: object, expected: object, *, name: str) -> None:
    if type(actual) is not type(expected):
        raise SyntheticSingleMacrostepError(name + " exact type differs")
    if type(expected) is tuple:
        if len(actual) != len(expected):  # type: ignore[arg-type]
            raise SyntheticSingleMacrostepError(name + " tuple length differs")
        for ordinal, (actual_item, expected_item) in enumerate(
            zip(actual, expected)  # type: ignore[arg-type]
        ):
            _strict_compare_value(
                actual_item,
                expected_item,
                name=name + "[" + str(ordinal) + "]",
            )
        return
    if type(expected) is float:
        if actual.hex() != expected.hex():  # type: ignore[union-attr]
            raise SyntheticSingleMacrostepError(name + " exact float differs")
        return
    if actual != expected:
        raise SyntheticSingleMacrostepError(name + " value differs")


def _strict_compare_dataclass_fields(
    actual: object,
    expected: object,
    *,
    expected_type: type,
    name: str,
) -> None:
    if type(actual) is not expected_type or type(expected) is not expected_type:
        raise TypeError(name + " values must have the exact result type")
    field_names = tuple(expected_type.__dataclass_fields__)
    for field_name in field_names:
        _strict_compare_value(
            getattr(actual, field_name),
            getattr(expected, field_name),
            name=name + "." + field_name,
        )


def _qualification_report_payload(
    result: FrozenSingleMacrostepQualification,
) -> Mapping[str, object]:
    if type(result) is not FrozenSingleMacrostepQualification:
        raise TypeError("result must be an exact FrozenSingleMacrostepQualification")
    input_hashes = result.case_input_sha256s
    report_hashes = result.case_report_sha256s
    if type(input_hashes) is not tuple or type(report_hashes) is not tuple:
        raise TypeError("qualification case digests must be exact tuples")
    checked_input_hashes = [
        _exact_sha256(value, name="qualification.case_input_sha256s")
        for value in input_hashes
    ]
    checked_report_hashes = [
        _exact_sha256(value, name="qualification.case_report_sha256s")
        for value in report_hashes
    ]
    return {
        "schema_version": _exact_text(
            result.schema_version, name="qualification.schema_version"
        ),
        "predicate": _exact_text(result.predicate, name="qualification.predicate"),
        "scope": _exact_text(result.scope, name="qualification.scope"),
        "strict_nonclaims": _exact_text(
            result.strict_nonclaims, name="qualification.strict_nonclaims"
        ),
        "failure_policy": _exact_text(
            result.failure_policy, name="qualification.failure_policy"
        ),
        "low_word_cases_checked": _exact_uint64(
            result.low_word_cases_checked,
            name="qualification.low_word_cases_checked",
        ),
        "route_family_counts": [
            list(row)
            for row in _checked_pair_counts(
                result.route_family_counts,
                name="qualification.route_family_counts",
                text_key=True,
            )
        ],
        "final_cardinality_counts": [
            list(row)
            for row in _checked_pair_counts(
                result.final_cardinality_counts,
                name="qualification.final_cardinality_counts",
                text_key=False,
            )
        ],
        "source_serial_counts": [
            list(row)
            for row in _checked_pair_counts(
                result.source_serial_counts,
                name="qualification.source_serial_counts",
                text_key=False,
            )
        ],
        "normal_cell_counts": [
            list(row)
            for row in _checked_pair_counts(
                result.normal_cell_counts,
                name="qualification.normal_cell_counts",
                text_key=False,
            )
        ],
        "distinct_input_sha256_count": _exact_uint64(
            result.distinct_input_sha256_count,
            name="qualification.distinct_input_sha256_count",
        ),
        "distinct_report_sha256_count": _exact_uint64(
            result.distinct_report_sha256_count,
            name="qualification.distinct_report_sha256_count",
        ),
        "case_input_sha256s": checked_input_hashes,
        "case_report_sha256s": checked_report_hashes,
        "every_case_one_left_jump_right_macrostep": _exact_bool(
            result.every_case_one_left_jump_right_macrostep,
            name="qualification.every_case_one_left_jump_right_macrostep",
        ),
        "every_case_address_unique": _exact_bool(
            result.every_case_address_unique,
            name="qualification.every_case_address_unique",
        ),
        "every_case_lineage_matches_test29": _exact_bool(
            result.every_case_lineage_matches_test29,
            name="qualification.every_case_lineage_matches_test29",
        ),
        "birth_death_replacement_all_covered": _exact_bool(
            result.birth_death_replacement_all_covered,
            name="qualification.birth_death_replacement_all_covered",
        ),
        "no_effect_claim_scoped_to_validator_admitted_parents": _exact_bool(
            result.no_effect_claim_scoped_to_validator_admitted_parents,
            name=("qualification.no_effect_claim_scoped_to_validator_admitted_parents"),
        ),
        "arbitrary_parent_modules_authenticated": _exact_bool(
            result.arbitrary_parent_modules_authenticated,
            name="qualification.arbitrary_parent_modules_authenticated",
        ),
        "test28_initializer_admissible": _exact_bool(
            result.test28_initializer_admissible,
            name="qualification.test28_initializer_admissible",
        ),
        "live_parent_stream_consumed": _exact_bool(
            result.live_parent_stream_consumed,
            name="qualification.live_parent_stream_consumed",
        ),
        "continuous_gaussian_destination_sampled": _exact_bool(
            result.continuous_gaussian_destination_sampled,
            name="qualification.continuous_gaussian_destination_sampled",
        ),
        "general_strang_path_integrated": _exact_bool(
            result.general_strang_path_integrated,
            name="qualification.general_strang_path_integrated",
        ),
        "formal_tests_closed": _exact_uint64(
            result.formal_tests_closed, name="qualification.formal_tests_closed"
        ),
        "fields_closed": _exact_uint64(
            result.fields_closed, name="qualification.fields_closed"
        ),
        "blockers_closed": _exact_uint64(
            result.blockers_closed, name="qualification.blockers_closed"
        ),
        "result_slots_filled": _exact_uint64(
            result.result_slots_filled,
            name="qualification.result_slots_filled",
        ),
        "tracker_files_edited": _exact_uint64(
            result.tracker_files_edited,
            name="qualification.tracker_files_edited",
        ),
        "passed": _exact_bool(result.passed, name="qualification.passed"),
    }


def recompute_frozen_single_macrostep_qualification_report_sha256(
    result: FrozenSingleMacrostepQualification,
) -> str:
    """Recompute the complete frozen qualification digest."""

    return _canonical_digest(_qualification_report_payload(result))


def _validate_frozen_single_macrostep_qualification_structure(
    result: FrozenSingleMacrostepQualification,
) -> FrozenSingleMacrostepQualification:
    """Validate exact aggregate structure and its complete report digest."""

    _qualification_report_payload(result)
    if (
        result.schema_version != SCHEMA_VERSION
        or result.predicate != PREDICATE
        or result.scope != QUALIFICATION_SCOPE
        or result.strict_nonclaims != STRICT_NONCLAIMS
        or result.failure_policy != FAILURE_POLICY
    ):
        raise SyntheticSingleMacrostepError("qualification identity differs")
    expected = {
        "low_word_cases_checked": 16,
        "route_family_counts": (("birth", 8), ("death", 4), ("replacement", 4)),
        "final_cardinality_counts": ((1, 4), (2, 4), (3, 8)),
        "source_serial_counts": ((1, 4), (2, 4)),
        "normal_cell_counts": ((0, 6), (1, 6)),
        "distinct_input_sha256_count": 16,
        "distinct_report_sha256_count": 16,
    }
    if any(getattr(result, key) != value for key, value in expected.items()):
        raise SyntheticSingleMacrostepError("qualification exact counts differ")
    if (
        len(result.case_input_sha256s) != 16
        or len(result.case_report_sha256s) != 16
        or len(set(result.case_input_sha256s)) != 16
        or len(set(result.case_report_sha256s)) != 16
    ):
        raise SyntheticSingleMacrostepError("qualification case digests differ")
    expected_true = (
        result.every_case_one_left_jump_right_macrostep,
        result.every_case_address_unique,
        result.every_case_lineage_matches_test29,
        result.birth_death_replacement_all_covered,
        result.no_effect_claim_scoped_to_validator_admitted_parents,
        result.passed,
    )
    expected_false = (
        result.arbitrary_parent_modules_authenticated,
        result.test28_initializer_admissible,
        result.live_parent_stream_consumed,
        result.continuous_gaussian_destination_sampled,
        result.general_strang_path_integrated,
    )
    if not all(value is True for value in expected_true) or not all(
        value is False for value in expected_false
    ):
        raise SyntheticSingleMacrostepError(
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
        raise SyntheticSingleMacrostepError("qualification project delta differs")
    _exact_sha256(result.report_sha256, name="qualification.report_sha256")
    if result.report_sha256 != (
        recompute_frozen_single_macrostep_qualification_report_sha256(result)
    ):
        raise SyntheticSingleMacrostepError("qualification report digest differs")
    return result


def _addressed_increment(
    test30_api: ModuleType,
    *,
    run_id: int,
    step_index: int,
    serial: int,
    tag: int,
    increment: float,
):
    domain = (
        test30_api.DOMAIN_BROWNIAN_LEFT
        if tag == test30_api.TAG_BROWNIAN_LEFT
        else test30_api.DOMAIN_BROWNIAN_RIGHT
    )
    return test30_api.AddressedBrownianIncrement(
        address=test30_api.CP23BrownianAddress(
            domain=domain,
            domain_tag=tag,
            run_id=run_id,
            step_index=step_index,
            occurrence_serial=serial,
            proposal_index=0,
            philox_key=(run_id, tag),
            philox_counter=(0, step_index, serial, 0),
        ),
        increment=increment,
    )


def _frozen_increment(*, serial: int, low_word: int, right: bool) -> float:
    if right:
        numerator = ((5 * serial + 3 * low_word) % 9) - 4
    else:
        numerator = ((3 * serial + 2 * low_word) % 7) - 3
    return float(numerator) / 32.0


def build_frozen_single_macrostep_input(
    test29_api: ModuleType,
    test30_api: ModuleType,
    raw64_word: int = 2,
) -> SuppliedSingleMacrostepInput:
    """Build deterministic supplied data; no word or increment law is asserted."""

    _require_parent_modules(test29_api, test30_api)
    raw64_word = _exact_uint64(raw64_word, name="raw64_word")
    fixture = frozen_central_jump_fixture(test29_api)
    address = test29_api.CP24CompatibleAddress(FROZEN_RUN_ID, FROZEN_STEP_INDEX, 0)
    central_word = test29_api.AddressedUint64Word(address, raw64_word)
    transition = test29_api.run_addressed_acyclic_fixture(
        fixture,
        (central_word,),
        run_id=FROZEN_RUN_ID,
        step_index=FROZEN_STEP_INDEX,
    ).transitions[0]
    initial_serials = transition.lineage_before.active_serials
    final_serials = transition.lineage_after.active_serials
    low_word = raw64_word & (FROZEN_LOW_WORD_COUNT - 1)
    left = tuple(
        _addressed_increment(
            test30_api,
            run_id=FROZEN_RUN_ID,
            step_index=FROZEN_STEP_INDEX,
            serial=serial,
            tag=test30_api.TAG_BROWNIAN_LEFT,
            increment=_frozen_increment(serial=serial, low_word=low_word, right=False),
        )
        for serial in initial_serials
    )
    right = tuple(
        _addressed_increment(
            test30_api,
            run_id=FROZEN_RUN_ID,
            step_index=FROZEN_STEP_INDEX,
            serial=serial,
            tag=test30_api.TAG_BROWNIAN_RIGHT,
            increment=_frozen_increment(serial=serial, low_word=low_word, right=True),
        )
        for serial in final_serials
    )
    return SuppliedSingleMacrostepInput(
        run_id=FROZEN_RUN_ID,
        step_index=FROZEN_STEP_INDEX,
        macrostep_width=FROZEN_MACROSTEP_WIDTH,
        left_increments=left,
        central_word=central_word,
        right_increments=right,
    )


def _validate_increment_roster(
    test30_api: ModuleType,
    supplied: Tuple[object, ...],
    *,
    expected_serials: Tuple[int, ...],
    run_id: int,
    step_index: int,
    tag: int,
    label: str,
) -> Mapping[int, float]:
    if type(supplied) is not tuple:
        raise TypeError(label + " increments must be an exact tuple")
    if len(supplied) != len(expected_serials):
        raise SyntheticSingleMacrostepError(label + " increment count differs")
    values: Dict[int, float] = {}
    checked_run_id = _exact_uint64(run_id, name=label + " run_id")
    checked_step_index = _exact_uint64(step_index, name=label + " step_index")
    checked_tag = _exact_uint64(tag, name=label + " domain_tag")
    domain = (
        test30_api.DOMAIN_BROWNIAN_LEFT
        if checked_tag == test30_api.TAG_BROWNIAN_LEFT
        else test30_api.DOMAIN_BROWNIAN_RIGHT
    )
    checked_domain = _exact_text(domain, name=label + " domain")
    for ordinal, (item, serial) in enumerate(zip(supplied, expected_serials)):
        checked_serial = _exact_uint64(serial, name=label + " expected serial")
        if checked_serial == 0:
            raise ValueError(label + " expected serial must be positive")
        if type(item) is not test30_api.AddressedBrownianIncrement:
            raise TypeError(
                "%s increment %d has the wrong exact type" % (label, ordinal)
            )
        address = item.address
        if type(address) is not test30_api.CP23BrownianAddress:
            raise TypeError(label + " increment address has the wrong exact type")
        actual_domain = _exact_text(address.domain, name=label + " address.domain")
        actual_tag = _exact_uint64(
            address.domain_tag, name=label + " address.domain_tag"
        )
        actual_run = _exact_uint64(address.run_id, name=label + " address.run_id")
        actual_step = _exact_uint64(
            address.step_index, name=label + " address.step_index"
        )
        actual_serial = _exact_uint64(
            address.occurrence_serial,
            name=label + " address.occurrence_serial",
        )
        if actual_serial == 0:
            raise ValueError(label + " address occurrence serial must be positive")
        actual_proposal = _exact_uint64(
            address.proposal_index,
            name=label + " address.proposal_index",
        )
        if type(address.philox_key) is not tuple or len(address.philox_key) != 2:
            raise TypeError(label + " address.philox_key must be an exact pair")
        actual_key = tuple(
            _exact_uint64(word, name=label + " address.philox_key word")
            for word in address.philox_key
        )
        if (
            type(address.philox_counter) is not tuple
            or len(address.philox_counter) != 4
        ):
            raise TypeError(
                label + " address.philox_counter must be an exact length-four tuple"
            )
        actual_counter = tuple(
            _exact_uint64(word, name=label + " address.philox_counter word")
            for word in address.philox_counter
        )
        if (
            actual_domain != checked_domain
            or actual_tag != checked_tag
            or actual_run != checked_run_id
            or actual_step != checked_step_index
            or actual_serial != checked_serial
            or actual_proposal != 0
            or actual_key != (checked_run_id, checked_tag)
            or actual_counter != (0, checked_step_index, checked_serial, 0)
        ):
            raise SyntheticSingleMacrostepError(
                label + " increment address differs from its canonical roster"
            )
        canonical_address = test30_api.CP23BrownianAddress(
            domain=actual_domain,
            domain_tag=actual_tag,
            run_id=actual_run,
            step_index=actual_step,
            occurrence_serial=actual_serial,
            proposal_index=actual_proposal,
            philox_key=actual_key,
            philox_counter=actual_counter,
        )
        expected_address = test30_api.CP23BrownianAddress(
            domain=checked_domain,
            domain_tag=checked_tag,
            run_id=checked_run_id,
            step_index=checked_step_index,
            occurrence_serial=checked_serial,
            proposal_index=0,
            philox_key=(checked_run_id, checked_tag),
            philox_counter=(0, checked_step_index, checked_serial, 0),
        )
        if canonical_address != expected_address:
            raise SyntheticSingleMacrostepError(
                label + " increment address differs from its canonical roster"
            )
        if checked_serial in values:
            raise SyntheticSingleMacrostepError(label + " increment serial repeats")
        values[checked_serial] = _finite_float(
            item.increment, name=label + " increment"
        )
    return values


def _validate_central_word(
    test29_api: ModuleType,
    supplied_word: object,
    *,
    run_id: int,
    step_index: int,
):
    if type(supplied_word) is not test29_api.AddressedUint64Word:
        raise TypeError("central_word has the wrong exact Test-29 type")
    address = supplied_word.address
    if type(address) is not test29_api.CP24CompatibleAddress:
        raise TypeError("central_word address has the wrong exact Test-29 type")
    actual_run = _exact_uint64(address.run_id, name="central address.run_id")
    actual_step = _exact_uint64(address.step_index, name="central address.step_index")
    completed = _exact_uint64(
        address.completed_proposals,
        name="central address.completed_proposals",
    )
    canonical_address = test29_api.CP24CompatibleAddress(
        actual_run, actual_step, completed
    )
    expected_address = test29_api.CP24CompatibleAddress(run_id, step_index, 0)
    if canonical_address != expected_address:
        raise SyntheticSingleMacrostepError("central word address differs")
    raw64_word = _exact_uint64(supplied_word.raw64_word, name="central_word.raw64_word")
    return test29_api.AddressedUint64Word(canonical_address, raw64_word)


def _state_snapshot(
    occurrences: Mapping[int, object]
) -> Tuple[Tuple[int, str, float], ...]:
    return tuple(
        (serial, occurrences[serial].kind, occurrences[serial].coordinate)
        for serial in sorted(occurrences)
    )


def _snapshot_payload(
    snapshot: Tuple[Tuple[int, str, float], ...]
) -> Tuple[Mapping[str, object], ...]:
    return tuple(
        {"serial": serial, "kind": kind, "coordinate_hex": coordinate.hex()}
        for serial, kind, coordinate in snapshot
    )


def _input_payload(value: SuppliedSingleMacrostepInput) -> Mapping[str, object]:
    def increment_rows(items: Tuple[object, ...]):
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

    return {
        "run_id": value.run_id,
        "step_index": value.step_index,
        "macrostep_width_hex": value.macrostep_width.hex(),
        "left_increments": increment_rows(value.left_increments),
        "central_word": {
            "key": list(value.central_word.address.key),
            "counter": list(value.central_word.address.counter),
            "raw64_word": value.central_word.raw64_word,
        },
        "right_increments": increment_rows(value.right_increments),
    }


def _route_by_id(fixture, route_id: str):
    for route in fixture.initial_state.routes:
        if route.route_id == route_id:
            return route
    raise AssertionError("selected route is absent from the frozen fixture")


def _destination_occurrence(
    test29_api: ModuleType,
    test30_api: ModuleType,
    *,
    fixture,
    transition,
):
    route = _route_by_id(fixture, transition.selection.route_id)
    if route.gaussian_destination is None or transition.created_serial is None:
        raise AssertionError("destination route omitted its created lineage")
    if len(transition.selection.normal_cells) != 1:
        raise AssertionError("frozen destination is not one-dimensional")
    cell = transition.selection.normal_cells[0]
    mean = float(route.gaussian_destination.mean[0])
    standard_deviation = math.sqrt(float(route.gaussian_destination.variance[0]))
    coordinate = mean + standard_deviation * cell.midpoint_representative()
    if not math.isfinite(coordinate):
        raise ArithmeticError("normal-cell representative became non-finite")
    kind = "A" if transition.selection.family == test29_api.FAMILY_BIRTH else "B"
    return test30_api.SyntheticOccurrence(transition.created_serial, kind, coordinate)


def _execute_single_macrostep_core(
    test29_api: ModuleType,
    test30_api: ModuleType,
    supplied: SuppliedSingleMacrostepInput,
) -> SingleMacrostepResult:
    """Nonrecursive execution core used by both running and validation."""

    _require_parent_modules(test29_api, test30_api)
    if type(supplied) is not SuppliedSingleMacrostepInput:
        raise TypeError("supplied must be an exact SuppliedSingleMacrostepInput")
    run_id = _exact_uint64(supplied.run_id, name="supplied.run_id")
    step_index = _exact_uint64(supplied.step_index, name="supplied.step_index")
    macrostep_width = _finite_float(
        supplied.macrostep_width,
        name="supplied.macrostep_width",
        positive=True,
    )
    if type(supplied.left_increments) is not tuple:
        raise TypeError("supplied.left_increments must be an exact tuple")
    if type(supplied.right_increments) is not tuple:
        raise TypeError("supplied.right_increments must be an exact tuple")
    if run_id != FROZEN_RUN_ID or step_index != FROZEN_STEP_INDEX:
        raise SyntheticSingleMacrostepError("run or step differs from frozen v1")
    if macrostep_width.hex() != FROZEN_MACROSTEP_WIDTH.hex():
        raise SyntheticSingleMacrostepError("macrostep width differs from frozen v1")
    fixture = frozen_central_jump_fixture(test29_api)
    parent_qualification = test29_api.qualify_finite_acyclic_fixture(fixture)
    if (
        not parent_qualification.cp24_compatible_address_consumption_defined
        or not parent_qualification.unconditional_bounded_fixture_completion_proved
        or parent_qualification.formal_test29_closed
    ):
        raise SyntheticSingleMacrostepError("Test-29 parent qualification differs")
    canonical_central_word = _validate_central_word(
        test29_api,
        supplied.central_word,
        run_id=run_id,
        step_index=step_index,
    )

    # This pure central selection must precede the right-roster preflight because
    # the selected edit determines the terminal lineage.  No Heun/path arithmetic
    # or result is produced until both increment rosters have then been checked.
    jump_run = test29_api.run_addressed_acyclic_fixture(
        fixture,
        (canonical_central_word,),
        run_id=run_id,
        step_index=step_index,
    )
    test29_api.validate_addressed_acyclic_run_result(
        fixture, (canonical_central_word,), jump_run
    )
    if jump_run.consumed_word_count != 1 or len(jump_run.transitions) != 1:
        raise AssertionError("rank-one fixture did not consume exactly one word")
    transition = jump_run.transitions[0]
    initial_serials = transition.lineage_before.active_serials
    final_serials = transition.lineage_after.active_serials
    left_values = _validate_increment_roster(
        test30_api,
        supplied.left_increments,
        expected_serials=initial_serials,
        run_id=run_id,
        step_index=step_index,
        tag=test30_api.TAG_BROWNIAN_LEFT,
        label="left",
    )
    right_values = _validate_increment_roster(
        test30_api,
        supplied.right_increments,
        expected_serials=final_serials,
        run_id=run_id,
        step_index=step_index,
        tag=test30_api.TAG_BROWNIAN_RIGHT,
        label="right",
    )
    address_identities = [
        (item.address.philox_key, item.address.philox_counter)
        for item in supplied.left_increments + supplied.right_increments
    ] + [(canonical_central_word.address.key, canonical_central_word.address.counter)]
    if len(set(address_identities)) != len(address_identities):
        raise SyntheticSingleMacrostepError("macrostep address identity was reused")

    design = test30_api.frozen_synthetic_design()
    if tuple(item.serial for item in design.initial_occurrences) != initial_serials:
        raise AssertionError("Test-30 initial lineage differs from Test-29 fixture")
    initial = {item.serial: item for item in design.initial_occurrences}
    state_before = _state_snapshot(initial)
    half = 0.5 * macrostep_width
    after_left: Dict[int, object] = {}
    for serial in initial_serials:
        item = initial[serial]
        target = design.long_run_mean_a if item.kind == "A" else design.long_run_mean_b
        coordinate = test30_api._heun_half(
            item.coordinate,
            duration=half,
            increment=left_values[serial],
            theta=design.mean_reversion,
            diffusion=design.diffusion,
            long_run_mean=target,
        )
        after_left[serial] = test30_api.SyntheticOccurrence(
            serial, item.kind, coordinate
        )
    state_after_left = _state_snapshot(after_left)

    after_jump = dict(after_left)
    if transition.source_serial is not None:
        if transition.source_serial not in after_jump:
            raise AssertionError("Test-29 selected a nonlive source")
        del after_jump[transition.source_serial]
    if transition.created_serial is not None:
        created = _destination_occurrence(
            test29_api,
            test30_api,
            fixture=fixture,
            transition=transition,
        )
        if created.serial in after_jump:
            raise AssertionError("fresh Test-29 serial collides with a live occurrence")
        after_jump[created.serial] = created
    if tuple(sorted(after_jump)) != final_serials:
        raise AssertionError("coordinate roster differs from Test-29 terminal lineage")
    state_after_jump = _state_snapshot(after_jump)

    after_right: Dict[int, object] = {}
    for serial in final_serials:
        item = after_jump[serial]
        target = design.long_run_mean_a if item.kind == "A" else design.long_run_mean_b
        coordinate = test30_api._heun_half(
            item.coordinate,
            duration=half,
            increment=right_values[serial],
            theta=design.mean_reversion,
            diffusion=design.diffusion,
            long_run_mean=target,
        )
        after_right[serial] = test30_api.SyntheticOccurrence(
            serial, item.kind, coordinate
        )
    state_after_right = _state_snapshot(after_right)
    input_sha256 = _canonical_digest(_input_payload(supplied))
    provisional = SingleMacrostepResult(
        schema_version=SCHEMA_VERSION,
        predicate=PREDICATE,
        scope=QUALIFICATION_SCOPE,
        strict_nonclaims=STRICT_NONCLAIMS,
        failure_policy=FAILURE_POLICY,
        run_id=run_id,
        step_index=step_index,
        macrostep_width=macrostep_width,
        input_sha256=input_sha256,
        report_sha256="0" * 64,
        route_id=transition.selection.route_id,
        family=transition.selection.family,
        source_index=transition.selection.source_index,
        source_serial=transition.source_serial,
        created_serial=transition.created_serial,
        normal_cell_indices=tuple(
            cell.index for cell in transition.selection.normal_cells
        ),
        state_before=state_before,
        state_after_left=state_after_left,
        state_after_jump=state_after_jump,
        state_after_right=state_after_right,
        left_heun_application_count=len(initial_serials),
        central_jump_count=1,
        right_heun_application_count=len(final_serials),
        address_count=len(address_identities),
        address_identities_unique=True,
        lineage_matches_test29=True,
        destination_is_normal_cell_midpoint_only=True,
        no_effect_claim_scoped_to_validator_admitted_parents=True,
        arbitrary_parent_modules_authenticated=False,
        test28_initializer_admissible=False,
        live_cp23_stream_consumed=False,
        live_cp24_stream_consumed=False,
        continuous_gaussian_destination_sampled=False,
        waiting_clock_or_acceptance_thinning_executed=False,
        general_strang_path_integrated=False,
        formal_test28_closed=False,
        formal_test29_closed=False,
        formal_test30_closed=False,
        passed=True,
    )
    result = replace(
        provisional,
        report_sha256=recompute_single_macrostep_report_sha256(provisional),
    )
    return _validate_single_macrostep_result_structure(result)


def validate_single_macrostep_result(
    test29_api: ModuleType,
    test30_api: ModuleType,
    supplied: SuppliedSingleMacrostepInput,
    result: SingleMacrostepResult,
) -> SingleMacrostepResult:
    """Reconstruct one supplied case and strictly compare every result field."""

    _validate_single_macrostep_result_structure(result)
    expected = _execute_single_macrostep_core(test29_api, test30_api, supplied)
    _strict_compare_dataclass_fields(
        result,
        expected,
        expected_type=SingleMacrostepResult,
        name="result",
    )
    return result


def run_supplied_single_macrostep(
    test29_api: ModuleType,
    test30_api: ModuleType,
    supplied: SuppliedSingleMacrostepInput,
) -> SingleMacrostepResult:
    """Select, preflight, execute, then independently reconstruct one case."""

    result = _execute_single_macrostep_core(test29_api, test30_api, supplied)
    return validate_single_macrostep_result(
        test29_api,
        test30_api,
        supplied,
        result,
    )


def _execute_frozen_single_macrostep_qualification_core(
    test29_api: ModuleType, test30_api: ModuleType
) -> FrozenSingleMacrostepQualification:
    """Nonrecursive core that exhausts every frozen low-word case."""

    _require_parent_modules(test29_api, test30_api)
    results = tuple(
        _execute_single_macrostep_core(
            test29_api,
            test30_api,
            build_frozen_single_macrostep_input(test29_api, test30_api, word),
        )
        for word in range(FROZEN_LOW_WORD_COUNT)
    )
    family_counts: Dict[str, int] = {}
    cardinality_counts: Dict[int, int] = {}
    source_counts: Dict[int, int] = {}
    cell_counts: Dict[int, int] = {}
    for result in results:
        family_counts[result.family] = family_counts.get(result.family, 0) + 1
        cardinality = len(result.state_after_right)
        cardinality_counts[cardinality] = cardinality_counts.get(cardinality, 0) + 1
        if result.source_serial is not None:
            source_counts[result.source_serial] = (
                source_counts.get(result.source_serial, 0) + 1
            )
        for cell in result.normal_cell_indices:
            cell_counts[cell] = cell_counts.get(cell, 0) + 1
    every_shape = all(
        result.left_heun_application_count == 2
        and result.central_jump_count == 1
        and result.right_heun_application_count == len(result.state_after_right)
        for result in results
    )
    every_address = all(result.address_identities_unique for result in results)
    every_lineage = all(result.lineage_matches_test29 for result in results)
    all_families = set(family_counts) == {
        test29_api.FAMILY_BIRTH,
        test29_api.FAMILY_DEATH,
        test29_api.FAMILY_REPLACEMENT,
    }
    positive = (
        len(results) == FROZEN_LOW_WORD_COUNT
        and family_counts
        == {
            test29_api.FAMILY_BIRTH: 8,
            test29_api.FAMILY_REPLACEMENT: 4,
            test29_api.FAMILY_DEATH: 4,
        }
        and cardinality_counts == {1: 4, 2: 4, 3: 8}
        and source_counts == {1: 4, 2: 4}
        and cell_counts == {0: 6, 1: 6}
        and len({result.input_sha256 for result in results}) == 16
        and len({result.report_sha256 for result in results}) == 16
        and every_shape
        and every_address
        and every_lineage
        and all_families
    )
    provisional = FrozenSingleMacrostepQualification(
        schema_version=SCHEMA_VERSION,
        predicate=PREDICATE,
        scope=QUALIFICATION_SCOPE,
        strict_nonclaims=STRICT_NONCLAIMS,
        failure_policy=FAILURE_POLICY,
        low_word_cases_checked=len(results),
        route_family_counts=tuple(sorted(family_counts.items())),
        final_cardinality_counts=tuple(sorted(cardinality_counts.items())),
        source_serial_counts=tuple(sorted(source_counts.items())),
        normal_cell_counts=tuple(sorted(cell_counts.items())),
        distinct_input_sha256_count=len({result.input_sha256 for result in results}),
        distinct_report_sha256_count=len({result.report_sha256 for result in results}),
        case_input_sha256s=tuple(result.input_sha256 for result in results),
        case_report_sha256s=tuple(result.report_sha256 for result in results),
        every_case_one_left_jump_right_macrostep=every_shape,
        every_case_address_unique=every_address,
        every_case_lineage_matches_test29=every_lineage,
        birth_death_replacement_all_covered=all_families,
        no_effect_claim_scoped_to_validator_admitted_parents=True,
        arbitrary_parent_modules_authenticated=False,
        test28_initializer_admissible=False,
        live_parent_stream_consumed=False,
        continuous_gaussian_destination_sampled=False,
        general_strang_path_integrated=False,
        formal_tests_closed=0,
        fields_closed=0,
        blockers_closed=0,
        result_slots_filled=0,
        tracker_files_edited=0,
        passed=positive,
        report_sha256="0" * 64,
    )
    result = replace(
        provisional,
        report_sha256=(
            recompute_frozen_single_macrostep_qualification_report_sha256(provisional)
        ),
    )
    return _validate_frozen_single_macrostep_qualification_structure(result)


def validate_frozen_single_macrostep_qualification(
    test29_api: ModuleType,
    test30_api: ModuleType,
    result: FrozenSingleMacrostepQualification,
) -> FrozenSingleMacrostepQualification:
    """Rerun all canonical cases and strictly compare every aggregate field."""

    _validate_frozen_single_macrostep_qualification_structure(result)
    expected = _execute_frozen_single_macrostep_qualification_core(
        test29_api,
        test30_api,
    )
    _strict_compare_dataclass_fields(
        result,
        expected,
        expected_type=FrozenSingleMacrostepQualification,
        name="qualification",
    )
    return result


def run_frozen_single_macrostep_qualification(
    test29_api: ModuleType, test30_api: ModuleType
) -> FrozenSingleMacrostepQualification:
    """Run and independently reconstruct the canonical sixteen-case aggregate."""

    result = _execute_frozen_single_macrostep_qualification_core(
        test29_api,
        test30_api,
    )
    return validate_frozen_single_macrostep_qualification(
        test29_api,
        test30_api,
        result,
    )


__all__ = [
    "SCHEMA_VERSION",
    "PREDICATE",
    "QUALIFICATION_SCOPE",
    "STRICT_NONCLAIMS",
    "FAILURE_POLICY",
    "EXPECTED_TEST29_SCHEMA",
    "EXPECTED_TEST30_SCHEMA",
    "FROZEN_RUN_ID",
    "FROZEN_STEP_INDEX",
    "FROZEN_MACROSTEP_WIDTH",
    "FROZEN_LOW_WORD_COUNT",
    "SyntheticSingleMacrostepError",
    "SuppliedSingleMacrostepInput",
    "SingleMacrostepResult",
    "FrozenSingleMacrostepQualification",
    "recompute_single_macrostep_report_sha256",
    "validate_single_macrostep_result",
    "recompute_frozen_single_macrostep_qualification_report_sha256",
    "validate_frozen_single_macrostep_qualification",
    "frozen_central_jump_fixture",
    "build_frozen_single_macrostep_input",
    "run_supplied_single_macrostep",
    "run_frozen_single_macrostep_qualification",
]
