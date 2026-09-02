"""Read-only validator and pure selector for the additive F146 rule freeze.

The selector consumes only a synthetic/certified tied-best roster.  It does
not accept validation values and has no writer, network, connector, subprocess,
entropy, project-science, data, training, checkpoint, runtime, or result route.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-f146-checkpoint-tie-rule-freeze-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "F146_EARLIEST_STEP_TIED_BEST_CHECKPOINT_RULE_FROZEN_PREOUTCOME"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
REPORTED_DATE = "2026-09-01"
PACKAGE_KIND = "ADDITIVE_PREOUTCOME_EXACT_F146_FIELD_CLOSURE"
CONTROL_PREDICATE = STATE

HUMAN_PATH = "PROJECT_F146_CHECKPOINT_TIE_RULE_FREEZE.md"
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.py"
)
PACKAGE_ROSTER = (HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)

F146_POINTER = "/training_and_checkpoint_plan/checkpoint_tie_rule"
RULE_ID = "F146_EARLIEST_STEP_TIED_BEST_CANONICAL_CHECKPOINT_RULE_V1"
REFUSAL = "F146_SELECTION_REFUSAL_NO_CHECKPOINT"
STEP_IDENTITY_DOMAIN = b"heterodiff-f146-step-bound-checkpoint-identity-v1\0"
TIED_ROSTER_DOMAIN = b"heterodiff-f146-certified-tied-best-roster-v1\0"
SHA256_RE = re.compile(r"[0-9a-f]{64}")

COORDINATOR_INSTRUCTION = (
    "Begin authoring the direct F146 checkpoint-tie-rule field-closure package "
    "using the approved scope contract; close only F146 and defer the machine "
    "record until the final F137 independent-review receipt can be bound."
)

EVIDENCE_READY_REGISTRATION = (
    "Upon independent acceptance, register only this delta: F146 "
    "(`/training_and_checkpoint_plan/checkpoint_tie_rule`) is closed by "
    "`F146_EARLIEST_STEP_TIED_BEST_CANONICAL_CHECKPOINT_RULE_V1`: within "
    "one future canonical selection unit, the unique smallest nonnegative "
    "completed optimizer-step index is selected from an at-least-two-member "
    "complete tied-best eligible checkpoint roster already certified under "
    "the later-frozen F144 metric semantics. Invalid, incomplete, uncertified, "
    "duplicate, conflicting, aliased, or noncanonical input yields "
    "`F146_SELECTION_REFUSAL_NO_CHECKPOINT` with no output or fallback. "
    "Effective pre-execution counts move from 144 open / 22 closed to 143 "
    "open / 23 closed; post-execution remains 3 open / 3 closed; totals move "
    "from 147 open / 25 closed to 146 open / 26 closed. Method/runtime/compute "
    "moves from 64/1 to 63/2. F139--F145 and F147, F150--F162, B12, all 12 "
    "blockers, Formal Tests, results, runtime, data, science, claims, and "
    "submission remain open or absent."
)

TIE_INPUT_KEYS = (
    "certificate",
    "rows",
    "tied_best_roster_sha256",
)
TIE_CERTIFICATE_KEYS = (
    "all_rows_eligible_under_f144_certified",
    "candidate_set_closed_under_future_freeze_certified",
    "complete_tied_best_roster_certified",
    "f144_semantics_final_and_frozen_certified",
    "f144_semantics_sha256",
    "first_and_only_invocation_certified",
    "prior_tie_break_invocation_count",
    "production_history_authenticated_by_helper",
    "selection_unit_sha256",
)
TIE_ROW_KEYS = (
    "checkpoint_content_sha256",
    "checkpoint_identity_sha256",
    "optimizer_step_index",
    "ordinal",
)
SUCCESS_OUTPUT_KEYS = (
    "caller_certifications_structurally_accepted",
    "checkpoint_content_sha256",
    "checkpoint_identity_sha256",
    "checkpoint_selected",
    "optimizer_step_index",
    "production_history_authenticated",
    "rule_id",
    "selection_disposition",
    "selection_unit_sha256",
    "tied_best_candidate_count",
    "tied_best_roster_sha256",
)
REFUSAL_OUTPUT_KEYS = (
    "checkpoint_selected",
    "disposition",
    "reason_code",
    "rule_id",
)
REFUSAL_REASON_CODES = (
    "CERTIFICATE_SCHEMA_NONCANONICAL",
    "CERTIFICATION_ABSENT_OR_FALSE",
    "DIGEST_NONCANONICAL",
    "DUPLICATE_ROW_AT_ONE_STEP",
    "IDENTITY_ALIASED_ACROSS_STEPS",
    "INVOCATION_HISTORY_SCHEMA_NONCANONICAL",
    "ROSTER_DIGEST_MISMATCH",
    "ROW_CONFLICT_AT_ONE_STEP",
    "ROW_ORDER_NONCANONICAL",
    "ROW_SCHEMA_NONCANONICAL",
    "STEP_BOUND_IDENTITY_MISMATCH",
    "STEP_SCHEMA_NONCANONICAL",
    "SYNTHETIC_PAIR_SCHEMA_NONCANONICAL",
    "TIE_CARDINALITY_BELOW_TWO",
    "TOP_LEVEL_SCHEMA_NONCANONICAL",
)

RULE_VALUE: Mapping[str, Any] = {
    "at_least_two_tied_rows_required_for_invocation": True,
    "candidate_roster_scope": "ONE_FUTURE_CANONICAL_SELECTION_UNIT",
    "checkpoint_identity_rule": (
        "DOMAIN_SEPARATED_SHA256_OF_SELECTION_UNIT_STEP_AND_CONTENT"
    ),
    "complete_tied_best_roster_must_be_f144_certified": True,
    "f144_semantics_final_and_frozen_certification_required": True,
    "fallback_retry_retraining_topup_or_extra_steps_permitted": False,
    "f144_owns_metric_direction_representation_equality_and_tolerance": True,
    "optimizer_step_index_type": (
        "EXACT_NONNEGATIVE_COMPLETED_OPTIMIZER_UPDATE_COUNT_NOT_BOOL"
    ),
    "optimizer_step_decimal_encoding": (
        "PACKAGE_LOCAL_TOTAL_BASE_1E9_CHUNKED_CANONICAL_BASE10"
    ),
    "optimizer_step_index_decimal_encoder_total": True,
    "refusal_disposition": REFUSAL,
    "rule_id": RULE_ID,
    "selection": (
        "UNIQUE_MINIMUM_OPTIMIZER_STEP_INDEX_WITHIN_CERTIFIED_TIED_BEST_ROSTER"
    ),
    "sequential_stopping_permitted": False,
    "caller_final_roster_and_first_invocation_certifications_required": True,
    "pure_helper_authenticates_production_history": False,
    "future_integration_and_invocation_custody_remain_open": True,
    "one_checkpoint_per_step_scope": (
        "ELIGIBLE_ROSTER_WITHIN_ONE_SELECTION_UNIT_NOT_EVERY_TRAINING_STEP"
    ),
    "canonical_ascii_json": {
        "allow_nan": False,
        "ensure_ascii": True,
        "separators": [",", ":"],
        "sort_keys": True,
        "terminal_lf_inside_digest_preimage": False,
    },
    "step_identity_domain_ascii": (
        "heterodiff-f146-step-bound-checkpoint-identity-v1"
    ),
    "step_identity_domain_suffix_hex": "00",
    "step_identity_payload_key_order": [
        "checkpoint_content_sha256",
        "optimizer_step_index",
        "selection_unit_sha256",
    ],
    "tied_roster_domain_ascii": (
        "heterodiff-f146-certified-tied-best-roster-v1"
    ),
    "tied_roster_domain_suffix_hex": "00",
    "tied_roster_payload_key_order": [
        "f144_semantics_sha256",
        "rows",
        "selection_unit_sha256",
    ],
    "top_level_key_order": list(TIE_INPUT_KEYS),
    "certificate_key_order": list(TIE_CERTIFICATE_KEYS),
    "row_key_order": list(TIE_ROW_KEYS),
    "success_output_key_order": list(SUCCESS_OUTPUT_KEYS),
    "refusal_output_key_order": list(REFUSAL_OUTPUT_KEYS),
    "refusal_reason_codes": list(REFUSAL_REASON_CODES),
    "refusal_is_not_a_scheduled_run_terminal_status": True,
    "existing_scheduled_run_terminal_status_roster": [
        "COMPLETE",
        "ALGORITHMIC_FAILURE",
        "NONFINITE",
        "OOM_OR_TIMEOUT",
        "INFRA_ABORT",
    ],
    "repeated_content_digest_at_distinct_steps_permitted": True,
    "checkpoint_identity_reuse_across_steps_permitted": False,
}

POST_FIELDS = ("F164", "F165", "F168", "F169", "F170", "F171")
PRE_FIELDS = tuple(
    "F" + str(index).zfill(3)
    for index in range(1, 173)
    if "F" + str(index).zfill(3) not in POST_FIELDS
)
CLOSED_BEFORE = (
    "F007",
    "F008",
    "F009",
    "F010",
    "F011",
    "F012",
    "F013",
    "F014",
    "F015",
    "F016",
    "F017",
    "F018",
    "F060",
    "F104",
    "F106",
    "F107",
    "F108",
    "F113",
    "F128",
    "F129",
    "F137",
    "F148",
)
CLOSED_AFTER = tuple(sorted(CLOSED_BEFORE + ("F146",)))
OPEN_BEFORE = tuple(field for field in PRE_FIELDS if field not in CLOSED_BEFORE)
OPEN_AFTER = tuple(field for field in PRE_FIELDS if field not in CLOSED_AFTER)


class ValidationError(ValueError):
    """Package custody, schema, or semantic validation failed."""


class SelectionRefusal(ValidationError):
    """The F146 selector refused without producing a checkpoint."""

    disposition = REFUSAL

    def __init__(self, reason_code: str) -> None:
        if reason_code not in REFUSAL_REASON_CODES:
            raise RuntimeError("unknown F146 refusal reason code")
        self.reason_code = reason_code
        super().__init__(REFUSAL + ": " + reason_code)

    def as_record(self) -> Dict[str, Any]:
        record = {
            "checkpoint_selected": False,
            "disposition": REFUSAL,
            "reason_code": self.reason_code,
            "rule_id": RULE_ID,
        }
        if tuple(record) != REFUSAL_OUTPUT_KEYS:
            raise RuntimeError("refusal output key-order drift")
        return record


def _refuse(reason_code: str) -> None:
    raise SelectionRefusal(reason_code)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_integer_ascii(value: int) -> bytes:
    """Encode any exact built-in integer without interpreter digit limits."""

    if type(value) is not int:
        raise ValidationError("canonical JSON integer must be an exact built-in int")
    negative = value < 0
    magnitude = -value if negative else value
    if magnitude == 0:
        return b"0"
    base = 1_000_000_000
    chunks: List[int] = []
    while magnitude:
        magnitude, remainder = divmod(magnitude, base)
        chunks.append(remainder)
    head = str(chunks.pop()).encode("ascii")
    tail = b"".join(("%09d" % chunk).encode("ascii") for chunk in reversed(chunks))
    return (b"-" if negative else b"") + head + tail


def _canonical_json_value_bytes(value: Any) -> bytes:
    value_type = type(value)
    if value is None:
        return b"null"
    if value_type is bool:
        return b"true" if value else b"false"
    if value_type is int:
        return _canonical_integer_ascii(value)
    if value_type is float:
        try:
            return json.dumps(value, allow_nan=False, separators=(",", ":")).encode(
                "ascii"
            )
        except (TypeError, ValueError, UnicodeEncodeError) as error:
            raise ValidationError("value is not canonical ASCII JSON") from error
    if value_type is str:
        try:
            return json.dumps(
                value,
                ensure_ascii=True,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("ascii")
        except (TypeError, ValueError, UnicodeEncodeError) as error:
            raise ValidationError("value is not canonical ASCII JSON") from error
    if value_type in (list, tuple):
        return b"[" + b",".join(
            _canonical_json_value_bytes(item) for item in value
        ) + b"]"
    if value_type is dict:
        if any(type(key) is not str for key in value):
            raise ValidationError("canonical JSON object keys must be exact strings")
        return b"{" + b",".join(
            _canonical_json_value_bytes(key)
            + b":"
            + _canonical_json_value_bytes(value[key])
            for key in sorted(value)
        ) + b"}"
    raise ValidationError("value is not canonical ASCII JSON")


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    if type(value) is not dict:
        raise ValidationError("canonical JSON input must be an exact dictionary")
    return _canonical_json_value_bytes(value)


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        raise ValidationError("record must be an exact dictionary")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload))


def _predecessor_record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict or type(record.get("schema_version")) is not str:
        raise ValidationError("predecessor machine record has no exact schema")
    payload = dict(record)
    payload.pop("record_sha256", None)
    domain = (record["schema_version"] + "\0").encode("ascii")
    return _sha256(domain + _canonical_payload_bytes(payload))


def _object_without_duplicate_keys(
    pairs: Sequence[Tuple[str, Any]],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _parse_json(raw: bytes, label: str) -> Dict[str, Any]:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValidationError(label + " must be ASCII JSON") from error
    try:
        value = json.loads(text, object_pairs_hook=_object_without_duplicate_keys)
    except (json.JSONDecodeError, ValidationError) as error:
        raise ValidationError(label + " is not strict JSON") from error
    if type(value) is not dict:
        raise ValidationError(label + " top level must be an exact object")
    return value


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if any(type(key) is not str for key in actual):
            raise ValidationError(label + " key type mismatch")
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for index, expected_item in enumerate(expected):
            _strict_equal(actual[index], expected_item, label + "[" + str(index) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def _selection_digest(value: Any, label: str) -> str:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        del label
        _refuse("DIGEST_NONCANONICAL")
    return value


def _selection_step(value: Any) -> int:
    if type(value) is not int or value < 0:
        _refuse("STEP_SCHEMA_NONCANONICAL")
    return value


def canonical_step_bound_checkpoint_identity(
    selection_unit_sha256: Any,
    optimizer_step_index: Any,
    checkpoint_content_sha256: Any,
) -> str:
    """Return the exact synthetic step-bound checkpoint identity."""

    unit = _selection_digest(selection_unit_sha256, "selection_unit_sha256")
    step = _selection_step(optimizer_step_index)
    content = _selection_digest(
        checkpoint_content_sha256, "checkpoint_content_sha256"
    )
    payload = {
        "checkpoint_content_sha256": content,
        "optimizer_step_index": step,
        "selection_unit_sha256": unit,
    }
    return _sha256(STEP_IDENTITY_DOMAIN + _canonical_payload_bytes(payload))


def certified_tied_best_roster_sha256(
    selection_unit_sha256: Any,
    f144_semantics_sha256: Any,
    rows: Any,
) -> str:
    """Digest one canonical complete tied-best roster without metric values."""

    unit = _selection_digest(selection_unit_sha256, "selection_unit_sha256")
    semantics = _selection_digest(f144_semantics_sha256, "f144_semantics_sha256")
    if type(rows) is not tuple:
        _refuse("ROW_SCHEMA_NONCANONICAL")
    payload_rows: List[Dict[str, Any]] = []
    for row in rows:
        if type(row) is not dict or tuple(row) != TIE_ROW_KEYS:
            _refuse("ROW_SCHEMA_NONCANONICAL")
        payload_rows.append(dict(row))
    payload = {
        "f144_semantics_sha256": semantics,
        "rows": payload_rows,
        "selection_unit_sha256": unit,
    }
    return _sha256(TIED_ROSTER_DOMAIN + _canonical_payload_bytes(payload))


def select_earliest_step_tied_best(value: Any) -> Dict[str, Any]:
    """Select the earliest member of one certified complete tied-best roster.

    This function does not accept raw validation values.  Every invalid input
    raises :class:`SelectionRefusal`; there is no fallback return.
    """

    if type(value) is not dict or tuple(value) != TIE_INPUT_KEYS:
        _refuse("TOP_LEVEL_SCHEMA_NONCANONICAL")
    certificate = value["certificate"]
    if type(certificate) is not dict or tuple(certificate) != TIE_CERTIFICATE_KEYS:
        _refuse("CERTIFICATE_SCHEMA_NONCANONICAL")
    for name in (
        "all_rows_eligible_under_f144_certified",
        "candidate_set_closed_under_future_freeze_certified",
        "complete_tied_best_roster_certified",
        "f144_semantics_final_and_frozen_certified",
        "first_and_only_invocation_certified",
    ):
        if certificate[name] is not True:
            _refuse("CERTIFICATION_ABSENT_OR_FALSE")
    if (
        type(certificate["prior_tie_break_invocation_count"]) is not int
        or certificate["prior_tie_break_invocation_count"] != 0
        or certificate["production_history_authenticated_by_helper"] is not False
    ):
        _refuse("INVOCATION_HISTORY_SCHEMA_NONCANONICAL")
    unit = _selection_digest(
        certificate["selection_unit_sha256"], "selection_unit_sha256"
    )
    semantics = _selection_digest(
        certificate["f144_semantics_sha256"], "f144_semantics_sha256"
    )
    claimed_roster_digest = _selection_digest(
        value["tied_best_roster_sha256"], "tied_best_roster_sha256"
    )
    rows = value["rows"]
    if type(rows) is not tuple:
        _refuse("ROW_SCHEMA_NONCANONICAL")
    if len(rows) < 2:
        _refuse("TIE_CARDINALITY_BELOW_TWO")

    seen_steps: Dict[int, Tuple[str, str]] = {}
    seen_identities: Dict[str, int] = {}
    checked: List[Dict[str, Any]] = []
    previous_step: Optional[int] = None
    for expected_ordinal, row in enumerate(rows):
        if type(row) is not dict or tuple(row) != TIE_ROW_KEYS:
            _refuse("ROW_SCHEMA_NONCANONICAL")
        step = _selection_step(row["optimizer_step_index"])
        content = _selection_digest(
            row["checkpoint_content_sha256"], "checkpoint_content_sha256"
        )
        identity = _selection_digest(
            row["checkpoint_identity_sha256"], "checkpoint_identity_sha256"
        )
        if step in seen_steps:
            previous_identity, previous_content = seen_steps[step]
            if identity == previous_identity and content == previous_content:
                _refuse("DUPLICATE_ROW_AT_ONE_STEP")
            _refuse("ROW_CONFLICT_AT_ONE_STEP")
        if identity in seen_identities:
            _refuse("IDENTITY_ALIASED_ACROSS_STEPS")
        if type(row["ordinal"]) is not int or row["ordinal"] != expected_ordinal:
            _refuse("ROW_ORDER_NONCANONICAL")
        if previous_step is not None and step <= previous_step:
            _refuse("ROW_ORDER_NONCANONICAL")
        expected_identity = canonical_step_bound_checkpoint_identity(
            unit, step, content
        )
        if identity != expected_identity:
            _refuse("STEP_BOUND_IDENTITY_MISMATCH")
        seen_steps[step] = (identity, content)
        seen_identities[identity] = step
        previous_step = step
        checked.append(
            {
                "checkpoint_content_sha256": content,
                "checkpoint_identity_sha256": identity,
                "optimizer_step_index": step,
                "ordinal": expected_ordinal,
            }
        )

    canonical_rows = tuple(checked)
    observed_roster_digest = certified_tied_best_roster_sha256(
        unit, semantics, canonical_rows
    )
    if claimed_roster_digest != observed_roster_digest:
        _refuse("ROSTER_DIGEST_MISMATCH")

    selected = checked[0]
    result = {
        "caller_certifications_structurally_accepted": True,
        "checkpoint_content_sha256": selected["checkpoint_content_sha256"],
        "checkpoint_identity_sha256": selected["checkpoint_identity_sha256"],
        "checkpoint_selected": True,
        "optimizer_step_index": selected["optimizer_step_index"],
        "production_history_authenticated": False,
        "rule_id": RULE_ID,
        "selection_disposition": "SELECTED_UNIQUE_EARLIEST_TIED_BEST",
        "selection_unit_sha256": unit,
        "tied_best_candidate_count": len(checked),
        "tied_best_roster_sha256": observed_roster_digest,
    }
    if tuple(result) != SUCCESS_OUTPUT_KEYS:
        raise RuntimeError("success output key-order drift")
    return result


def synthetic_tied_best_input(
    selection_unit_sha256: str,
    f144_semantics_sha256: str,
    step_content_pairs: Sequence[Tuple[int, str]],
) -> Dict[str, Any]:
    """Build a canonical synthetic input for tests, never production evidence."""

    if type(step_content_pairs) is not tuple:
        _refuse("SYNTHETIC_PAIR_SCHEMA_NONCANONICAL")
    rows: List[Dict[str, Any]] = []
    for ordinal, pair in enumerate(step_content_pairs):
        if type(pair) is not tuple or len(pair) != 2:
            _refuse("SYNTHETIC_PAIR_SCHEMA_NONCANONICAL")
        step, content = pair
        rows.append(
            {
                "checkpoint_content_sha256": content,
                "checkpoint_identity_sha256": (
                    canonical_step_bound_checkpoint_identity(
                        selection_unit_sha256, step, content
                    )
                ),
                "optimizer_step_index": step,
                "ordinal": ordinal,
            }
        )
    immutable_rows = tuple(rows)
    roster_digest = certified_tied_best_roster_sha256(
        selection_unit_sha256, f144_semantics_sha256, immutable_rows
    )
    return {
        "certificate": {
            "all_rows_eligible_under_f144_certified": True,
            "candidate_set_closed_under_future_freeze_certified": True,
            "complete_tied_best_roster_certified": True,
            "f144_semantics_final_and_frozen_certified": True,
            "f144_semantics_sha256": f144_semantics_sha256,
            "first_and_only_invocation_certified": True,
            "prior_tie_break_invocation_count": 0,
            "production_history_authenticated_by_helper": False,
            "selection_unit_sha256": selection_unit_sha256,
        },
        "rows": immutable_rows,
        "tied_best_roster_sha256": roster_digest,
    }


SYNTHETIC_SELECTION_UNIT_SHA256 = _sha256(b"synthetic-f146-selection-unit")
SYNTHETIC_F144_SEMANTICS_SHA256 = _sha256(b"synthetic-f144-semantics")
SYNTHETIC_CONTENT_SHA256 = (
    _sha256(b"synthetic-checkpoint-step-3"),
    _sha256(b"synthetic-checkpoint-step-7"),
    _sha256(b"synthetic-checkpoint-step-11"),
)
SYNTHETIC_INPUT = synthetic_tied_best_input(
    SYNTHETIC_SELECTION_UNIT_SHA256,
    SYNTHETIC_F144_SEMANTICS_SHA256,
    (
        (3, SYNTHETIC_CONTENT_SHA256[0]),
        (7, SYNTHETIC_CONTENT_SHA256[1]),
        (11, SYNTHETIC_CONTENT_SHA256[2]),
    ),
)
SYNTHETIC_QUALIFICATION = select_earliest_step_tied_best(SYNTHETIC_INPUT)


# group, role, path, byte count, raw SHA-256, optional semantic self-digest
BindingSpec = Tuple[str, str, str, int, str, Optional[str]]
PREDECESSOR_SPECS: Tuple[BindingSpec, ...] = (
    (
        "EXECUTION_PREREGISTRATION_V1",
        "human",
        "manuscript_v3/execution_preregistration.md",
        22491,
        "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
        None,
    ),
    (
        "EXECUTION_PREREGISTRATION_V1",
        "machine",
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        39771,
        "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
        None,
    ),
    (
        "PREEXECUTION_CLOSURE_V2",
        "human",
        "manuscript_v3/execution_preregistration_preexecution_closure_v2.md",
        14938,
        "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d",
        None,
    ),
    (
        "PREEXECUTION_CLOSURE_V2",
        "machine",
        "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
        24571,
        "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
        "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4",
    ),
    (
        "ANTI_DRIFT_POLICY",
        "policy",
        "PROJECT_ANTI_DRIFT_OPERATING_POLICY.md",
        2240,
        "22f1006bfd0b4dde8eb51e6e30abd7b153882a3fd41d6f3a3494ffd98a98bbd3",
        None,
    ),
    (
        "A1_DEVELOPMENT_CHECKPOINT_V2_EXCLUSION",
        "human",
        "manuscript_v3/a1_development_checkpoint_freeze_v2.md",
        12113,
        "6639e0f15592558f03bae98fd7d75a56ec64564132f9631832c360a2be60f953",
        None,
    ),
    (
        "A1_DEVELOPMENT_CHECKPOINT_V2_EXCLUSION",
        "machine",
        "research/fixtures/manuscript_v3_a1_development_checkpoint_freeze_v2.json",
        14948,
        "b0b892db1041267defe664f59d57801e723f0115b8ac5ae9fc8656c3708cd8fc",
        None,
    ),
    (
        "D1_DIAGNOSTIC_EXCLUSION",
        "human",
        "manuscript_v3/a1_trained_checkpoint_diagnostic_evidence_registration.md",
        10795,
        "bd00e6d145a5517ed8ecd34f6547c49d6d8d4eae67aeb8321037bf6ca54b3ba5",
        None,
    ),
    (
        "D1_DIAGNOSTIC_EXCLUSION",
        "machine",
        "research/fixtures/manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration_v1.json",
        16764,
        "b52685e2b61a30c5781f0e75138eaae6410063fa2312a447eeed7a4d1902cac0",
        "d1c52907ba0bbb6b17cb2cb4e930d983623f39c161ad8a116afa43dccbbfa1b9",
    ),
    (
        "ACCEPTED_B11_BASELINE",
        "human",
        "PROJECT_B11_PREOUTCOME_AUDIT_PLAN_FREEZE.md",
        15878,
        "1b9cb20bde42b97967a1cc0ea4ee4e2d91f8be6f42f813271eaab1531ef877e9",
        None,
    ),
    (
        "ACCEPTED_B11_BASELINE",
        "machine",
        "research/fixtures/manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.json",
        23299,
        "d5770caedfd50858040eae696f9c6174f0a34266efa4c685102df7e51f8a01ff",
        "55455c716dfe09284c94ccd465919b5080423e7535e514daeee928081313f9a4",
    ),
    (
        "ACCEPTED_B11_BASELINE",
        "validator",
        "research/diagnostics/manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.py",
        42156,
        "224a1ca34b806e26077ceecd78aa2b57c2189c5e4c5be7447dc82ee6ae256070",
        None,
    ),
    (
        "ACCEPTED_B11_BASELINE",
        "test",
        "tests/unit/test_manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.py",
        37589,
        "790c0cec8f8f5ca565ce0edf7f76441216384b9eb45e6a44bbcc41744db9372f",
        None,
    ),
    (
        "ACCEPTED_B11_BASELINE",
        "independent_review",
        "PROJECT_B11_PREOUTCOME_AUDIT_PLAN_FREEZE_INDEPENDENT_REVIEW.md",
        13072,
        "0491763f2db016e957de0023f0ca92b9d5e1a8f1b02c87320625826f25b372c6",
        None,
    ),
    (
        "ACCEPTED_F137_BASELINE",
        "human",
        "PROJECT_F137_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_FREEZE.md",
        12160,
        "12174a5da4b0c43773a89b4a1c01e97b7a8208e7d849520c5310e2909defb52e",
        None,
    ),
    (
        "ACCEPTED_F137_BASELINE",
        "machine",
        "research/fixtures/manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.json",
        24002,
        "2ce4fc0af580c9b0572496ee932467d185b0710744541342a41ce8715df65a06",
        "6bd2cc0bfd8dead57318775f82f39d8ba22a4919c5eae3628a6fffb584a3d6a8",
    ),
    (
        "ACCEPTED_F137_BASELINE",
        "validator",
        "research/diagnostics/manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.py",
        68065,
        "59f1f294fb6b8878bb89a5759c12242762dd223af06da709de6be4410a88e3e2",
        None,
    ),
    (
        "ACCEPTED_F137_BASELINE",
        "test",
        "tests/unit/test_manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.py",
        40414,
        "59c8a40ffd39632d47eaa63fe4d39baa18886d4b4a0d29c5e124b49820b7b855",
        None,
    ),
    (
        "ACCEPTED_F137_BASELINE",
        "independent_review",
        "PROJECT_F137_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_FREEZE_INDEPENDENT_REVIEW.md",
        14661,
        "0d7c09bd69b8d26405c2c173f0c153510d97929fe5fbc457ec222f075e726533",
        None,
    ),
)

PREDECESSOR_GROUP_COUNTS = {
    "EXECUTION_PREREGISTRATION_V1": 2,
    "PREEXECUTION_CLOSURE_V2": 2,
    "ANTI_DRIFT_POLICY": 1,
    "A1_DEVELOPMENT_CHECKPOINT_V2_EXCLUSION": 2,
    "D1_DIAGNOSTIC_EXCLUSION": 2,
    "ACCEPTED_B11_BASELINE": 5,
    "ACCEPTED_F137_BASELINE": 5,
}
NONTERMINAL_LF_PREDECESSOR_PATHS = {
    "research/fixtures/"
    "manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration_v1.json"
}

# Installed only after the human and hostile-test bytes were internally stable.
EXPECTED_HUMAN_BYTES = 18409
EXPECTED_HUMAN_SHA256 = "403858d0a1afe5c4498973b568ca2e528cb0cde54a02dde52f74123eb0b4c249"
EXPECTED_TEST_BYTES = 36317
EXPECTED_TEST_SHA256 = "cfe4bd7689b6d40abd28b363e553172ecdbb1dc0bc1a759d61abb124e5332bbd"


def _canonical_relative_path(relative: Any) -> Tuple[str, ...]:
    if type(relative) is not str or not relative or "\\" in relative:
        raise ValidationError("binding path must be a nonempty POSIX string")
    path = Path(relative)
    if path.is_absolute() or relative.startswith("/"):
        raise ValidationError("binding path must be relative")
    if "/".join(path.parts) != relative:
        raise ValidationError("binding path must be canonical")
    if any(part in (".", "..") for part in path.parts):
        raise ValidationError("binding path traversal is forbidden")
    return tuple(path.parts)


def _fingerprint(value: os.stat_result) -> Tuple[int, int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        value.st_mode,
        value.st_nlink,
    )


def _validate_leaf_status(value: os.stat_result, label: str) -> None:
    if not stat.S_ISREG(value.st_mode):
        raise ValidationError(label + " must be a regular file")
    if stat.S_IMODE(value.st_mode) != 0o644:
        raise ValidationError(label + " mode must be exactly 0644")
    if value.st_nlink != 1:
        raise ValidationError(label + " must have exactly one hard link")


def _stable_read(root: Path, relative: str) -> bytes:
    if not isinstance(root, Path) or not root.is_absolute():
        raise ValidationError("workspace root must be an absolute Path")
    parts = _canonical_relative_path(relative)
    descriptors: List[int] = []
    namespace_rows: List[Tuple[int, str, Tuple[int, ...]]] = []
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    root_before = root.lstat()
    try:
        root_fd = os.open(str(root), os.O_RDONLY | directory | nofollow | cloexec)
        descriptors.append(root_fd)
        root_open = os.fstat(root_fd)
        if (
            stat.S_ISLNK(root_before.st_mode)
            or not stat.S_ISDIR(root_before.st_mode)
            or _fingerprint(root_before) != _fingerprint(root_open)
        ):
            raise ValidationError("workspace root identity mismatch")
        parent_fd = root_fd
        for component in parts[:-1]:
            entry_before = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            child_fd = os.open(
                component,
                os.O_RDONLY | directory | nofollow | cloexec,
                dir_fd=parent_fd,
            )
            descriptors.append(child_fd)
            child_status = os.fstat(child_fd)
            if (
                stat.S_ISLNK(entry_before.st_mode)
                or not stat.S_ISDIR(entry_before.st_mode)
                or _fingerprint(entry_before) != _fingerprint(child_status)
            ):
                raise ValidationError("unsafe or changed path component")
            namespace_rows.append((parent_fd, component, _fingerprint(entry_before)))
            parent_fd = child_fd

        leaf = parts[-1]
        entry_before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        _validate_leaf_status(entry_before, "before-path binding")
        leaf_fd = os.open(leaf, os.O_RDONLY | nofollow | cloexec, dir_fd=parent_fd)
        descriptors.append(leaf_fd)
        before_fd = os.fstat(leaf_fd)
        _validate_leaf_status(before_fd, "before-descriptor binding")
        if (
            stat.S_ISLNK(entry_before.st_mode)
            or _fingerprint(entry_before) != _fingerprint(before_fd)
        ):
            raise ValidationError("binding must be a stable regular file")
        namespace_rows.append((parent_fd, leaf, _fingerprint(entry_before)))

        chunks: List[bytes] = []
        while True:
            chunk = os.read(leaf_fd, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(leaf_fd)
        _validate_leaf_status(after_fd, "after-descriptor binding")
        if _fingerprint(before_fd) != _fingerprint(after_fd):
            raise ValidationError("binding changed during descriptor read")
        for saved_parent, component, expected in namespace_rows:
            current = os.stat(
                component, dir_fd=saved_parent, follow_symlinks=False
            )
            if component == leaf and saved_parent == parent_fd:
                _validate_leaf_status(current, "after-path binding")
            if _fingerprint(current) != expected:
                raise ValidationError("binding namespace changed during read")
        root_after = root.lstat()
        if _fingerprint(root_before) != _fingerprint(root_after):
            raise ValidationError("workspace root changed during read")
        raw = b"".join(chunks)
        if len(raw) != before_fd.st_size:
            raise ValidationError("short binding read")
        return raw
    except OSError as error:
        raise ValidationError("stable no-follow read failed: " + relative) from error
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _binding(
    ordinal: int,
    group: str,
    role: str,
    path: str,
    raw: bytes,
    semantic_digest: Optional[str] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "bytes": len(raw),
        "group": group,
        "mode_octal": "0644",
        "nlink": 1,
        "ordinal": ordinal,
        "path": path,
        "raw_sha256": _sha256(raw),
        "role": role,
        "terminal_lf": raw.endswith(b"\n"),
    }
    if semantic_digest is not None:
        row["record_sha256"] = semantic_digest
    return row


def _checked_fixed_binding(
    root: Path,
    ordinal: int,
    group: str,
    role: str,
    path: str,
    expected_bytes: int,
    expected_sha256: str,
    semantic_digest: Optional[str] = None,
) -> Dict[str, Any]:
    raw = _stable_read(root, path)
    if len(raw) != expected_bytes or _sha256(raw) != expected_sha256:
        raise ValidationError("fixed binding drift: " + path)
    expected_terminal_lf = path not in NONTERMINAL_LF_PREDECESSOR_PATHS
    if raw.endswith(b"\n") is not expected_terminal_lf:
        raise ValidationError("fixed binding terminal-LF drift: " + path)
    if semantic_digest is not None:
        parsed = _parse_json(raw, path)
        if parsed.get("record_sha256") != semantic_digest:
            raise ValidationError("predecessor semantic digest field drift: " + path)
        if _predecessor_record_sha256(parsed) != semantic_digest:
            raise ValidationError("predecessor semantic digest recomputation failed: " + path)
    return _binding(
        ordinal, group, role, path, raw, semantic_digest=semantic_digest
    )


def _predecessor_bindings(root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for ordinal, spec in enumerate(PREDECESSOR_SPECS):
        rows.append(_checked_fixed_binding(root, ordinal, *spec))
    observed: Dict[str, int] = {}
    for row in rows:
        observed[row["group"]] = observed.get(row["group"], 0) + 1
    if observed != PREDECESSOR_GROUP_COUNTS:
        raise ValidationError("predecessor group-count drift")
    return rows


def _validate_human(raw: bytes) -> None:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError("human record is not UTF-8") from error
    required = (
        STATE,
        RULE_ID,
        REFUSAL,
        F146_POINTER,
        "144 open / 22 closed",
        "143 open / 23 closed",
        "147 open / 25 closed",
        "146 open / 26 closed",
        "B12 remains open",
        "FINAL_UPDATE_ONLY",
        "NOT_APPLICABLE_NO_SELECTION",
        EVIDENCE_READY_REGISTRATION,
    )
    for marker in required:
        if marker not in text:
            raise ValidationError("human record lost required marker: " + marker[:80])


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    if (
        EXPECTED_HUMAN_BYTES <= 0
        or SHA256_RE.fullmatch(EXPECTED_HUMAN_SHA256) is None
        or EXPECTED_TEST_BYTES <= 0
        or SHA256_RE.fullmatch(EXPECTED_TEST_SHA256) is None
    ):
        raise ValidationError("fixed package hashes are not installed")
    human = _checked_fixed_binding(
        root,
        0,
        "CURRENT_PACKAGE",
        "human",
        HUMAN_PATH,
        EXPECTED_HUMAN_BYTES,
        EXPECTED_HUMAN_SHA256,
    )
    _validate_human(_stable_read(root, HUMAN_PATH))
    validator_raw = _stable_read(root, VALIDATOR_PATH)
    test = _checked_fixed_binding(
        root,
        2,
        "CURRENT_PACKAGE",
        "test",
        TEST_PATH,
        EXPECTED_TEST_BYTES,
        EXPECTED_TEST_SHA256,
    )
    validator = _binding(
        1, "CURRENT_PACKAGE", "validator", VALIDATOR_PATH, validator_raw
    )
    return [human, validator, test]


def _required_utf8_text(root: Path, path: str, markers: Sequence[str]) -> None:
    raw = _stable_read(root, path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError("predecessor human record is not UTF-8: " + path) from error
    for marker in markers:
        if marker not in text:
            raise ValidationError(
                "predecessor human semantic marker drift: " + path + ": " + marker
            )


def _validate_predecessor_semantics(root: Path) -> Dict[str, Any]:
    prereg = _parse_json(
        _stable_read(
            root,
            "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        ),
        "execution preregistration machine",
    )
    expected_training_plan = {
        "optimizer": None,
        "learning_rate_schedule": None,
        "precision": None,
        "batch_construction": None,
        "maximum_epochs_or_steps": None,
        "validation_metric": None,
        "early_stopping_patience": None,
        "checkpoint_tie_rule": None,
        "maximum_tuning_trials_per_method": None,
        "validation_early_stopping_allowed_only_if_frozen": True,
        "experiment_level_optional_stopping_permitted": False,
    }
    _strict_equal(
        prereg.get("training_and_checkpoint_plan"),
        expected_training_plan,
        "base preregistration training plan",
    )
    if prereg.get("confirmatory_execution_authorized") is not False:
        raise ValidationError("base preregistration execution boundary drift")

    closure = _parse_json(
        _stable_read(
            root,
            "research/fixtures/"
            "manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
        ),
        "preexecution closure machine",
    )
    if closure.get("global_state") != GLOBAL_STATE:
        raise ValidationError("preexecution closure global-state drift")
    closure_nonclaims = closure.get("nonclaims")
    if type(closure_nonclaims) is not dict:
        raise ValidationError("preexecution closure nonclaims missing")
    for key in (
        "confirmatory_execution_authorized",
        "production_execution_authorized",
        "production_order_admissible",
        "production_phase_consumed",
        "rank_executed",
        "scientific_execution_authorized",
        "scientific_result_eligible",
        "training_executed",
    ):
        if closure_nonclaims.get(key) is not False:
            raise ValidationError("preexecution nonexecution projection drift: " + key)
    d1_prior = closure.get("d1_prior_knowledge_boundary")
    if type(d1_prior) is not dict or d1_prior.get("used_for_checkpoint_selection") is not False:
        raise ValidationError("closure D1 checkpoint-selection boundary drift")

    development = _parse_json(
        _stable_read(
            root,
            "research/fixtures/manuscript_v3_a1_development_checkpoint_freeze_v2.json",
        ),
        "A1 development checkpoint V2 machine",
    )
    training = development.get("training_protocol")
    expected_development_projection = {
        "checkpoint_rule": "FINAL_UPDATE_ONLY",
        "checkpoint_tie_rule": "NOT_APPLICABLE_NO_SELECTION",
        "early_stopping": False,
        "experiment_level_optional_stopping_permitted": False,
        "validation_checkpoint_selection_permitted": False,
    }
    if type(training) is not dict:
        raise ValidationError("development training protocol missing")
    for key, expected in expected_development_projection.items():
        _strict_equal(training.get(key), expected, "development." + key)

    d1 = _parse_json(
        _stable_read(
            root,
            "research/fixtures/"
            "manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration_v1.json",
        ),
        "D1 diagnostic registration machine",
    )
    if d1.get("checkpoint_custody", {}).get("checkpoint_selected_by_diagnostic") is not False:
        raise ValidationError("D1 diagnostic checkpoint-selection drift")
    future = d1.get("future_r1_boundary")
    if type(future) is not dict:
        raise ValidationError("D1 future boundary missing")
    for key in ("may_select_checkpoint_from_d1", "used_for_checkpoint_selection"):
        if future.get(key) is not False:
            raise ValidationError("D1 future checkpoint-selection drift: " + key)
    for section in ("source_nonclaims", "visible_limitations"):
        projection = d1.get(section)
        if type(projection) is not dict:
            raise ValidationError("D1 exclusion projection missing: " + section)
        for key in (
            "checkpoint_selected_by_diagnostic",
            "production_checkpoint",
            "training_performed_by_diagnostic",
        ):
            if projection.get(key) is not False:
                raise ValidationError("D1 exclusion semantic drift: " + section + "." + key)

    b11 = _parse_json(
        _stable_read(
            root,
            "research/fixtures/manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.json",
        ),
        "B11 machine",
    )
    expected_b11_after = {
        "post_execution_closed": 3,
        "post_execution_open": 3,
        "pre_execution_closed": 21,
        "pre_execution_open": 145,
        "total_closed": 24,
        "total_open": 148,
    }
    _strict_equal(
        b11.get("count_transition", {}).get("after"),
        expected_b11_after,
        "B11 count anchor",
    )
    if [row.get("field_id") for row in b11.get("field_closures", [])] != [
        "F168",
        "F170",
        "F171",
    ]:
        raise ValidationError("B11 sole-field closure projection drift")
    b11_sweep = b11.get("comprehensive_field_sweep")
    if (
        type(b11_sweep) is not dict
        or b11_sweep.get("F169_value") is not None
        or b11_sweep.get("open_post_ids") != ["F164", "F165", "F169"]
    ):
        raise ValidationError("B11 F169/open-POST projection drift")
    if b11.get("project_effects_and_nonclaims", {}).get("B11_remains_open") is not True:
        raise ValidationError("B11 blocker nonclosure drift")

    f137 = _parse_json(
        _stable_read(
            root,
            "research/fixtures/"
            "manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.json",
        ),
        "F137 machine",
    )
    expected_f137_after = {
        "post_execution_closed": 3,
        "post_execution_open": 3,
        "pre_execution_closed": 22,
        "pre_execution_open": 144,
        "total_closed": 25,
        "total_open": 147,
    }
    _strict_equal(
        f137.get("count_transition", {}).get("after"),
        expected_f137_after,
        "F137 count anchor",
    )
    if [row.get("field_id") for row in f137.get("field_closures", [])] != ["F137"]:
        raise ValidationError("F137 sole-field closure projection drift")
    f137_effects = f137.get("project_effects_and_nonclaims")
    if (
        type(f137_effects) is not dict
        or f137_effects.get("only_field_closed") != "F137"
        or f137_effects.get("B07_remains_open") is not True
        or f137_effects.get("all_12_blockers_remain_open") is not True
    ):
        raise ValidationError("F137 effect projection drift")

    _required_utf8_text(
        root,
        "PROJECT_ANTI_DRIFT_OPERATING_POLICY.md",
        (
            "Count progress only when a named field, blocker, or gate is closed",
            "new work must close a named item",
        ),
    )
    _required_utf8_text(
        root,
        "PROJECT_B11_PREOUTCOME_AUDIT_PLAN_FREEZE_INDEPENDENT_REVIEW.md",
        ("INDEPENDENT_REVIEW_GO", "F169", "B11"),
    )
    _required_utf8_text(
        root,
        "PROJECT_F137_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_FREEZE_INDEPENDENT_REVIEW.md",
        (
            "INDEPENDENT_REVIEW_GO",
            "`GO` for the exact four-file F137 package",
            "144 open / 22 closed",
            "147 open / 25 closed",
        ),
    )
    return {
        "anti_drift_requires_named_direct_count_reduction": True,
        "base_F139_F147_values_remain_null_including_F144_and_F146": True,
        "base_optional_stopping_forbidden": True,
        "b11_after_pre_145_21_post_3_3_total_148_24": True,
        "b11_only_F168_F170_F171_closed_and_F169_open": True,
        "development_checkpoint_final_update_only_no_selection": True,
        "d1_checkpoint_ineligible_and_not_selected": True,
        "f137_after_pre_144_22_post_3_3_total_147_25": True,
        "f137_independent_review_go_and_only_F137_closed": True,
        "predecessor_execution_or_training_authorized": False,
    }


def expected_record(root: Path) -> Dict[str, Any]:
    if not isinstance(root, Path) or not root.is_absolute():
        raise ValidationError("workspace root must be an absolute Path")
    record: Dict[str, Any] = {
        "authority_provenance": {
            "coordinator_instruction": COORDINATOR_INSTRUCTION,
            "coordinator_instruction_sha256": _sha256(
                COORDINATOR_INSTRUCTION.encode("utf-8")
            ),
            "offline_local_package_construction_authorized": True,
            "network_contact_data_access_or_repository_action_authorized": False,
            "entropy_training_runtime_or_scientific_execution_authorized": False,
            "tracker_ledger_or_predecessor_edit_authorized_by_this_package": False,
        },
        "control_predicate": CONTROL_PREDICATE,
        "count_transition": {
            "before": {
                "post_execution_closed": 3,
                "post_execution_open": 3,
                "pre_execution_closed": 22,
                "pre_execution_open": 144,
                "total_closed": 25,
                "total_open": 147,
            },
            "delta": {
                "closed": 1,
                "closed_fields": ["F146"],
                "open": -1,
            },
            "after": {
                "post_execution_closed": 3,
                "post_execution_open": 3,
                "pre_execution_closed": 23,
                "pre_execution_open": 143,
                "total_closed": 26,
                "total_open": 146,
            },
        },
        "development_evidence_exclusion": {
            "d1_checkpoint_or_metric_eligible_for_f146": False,
            "d1_checkpoint_selection_performed": False,
            "development_checkpoint_rule": "FINAL_UPDATE_ONLY",
            "development_checkpoint_tie_rule": "NOT_APPLICABLE_NO_SELECTION",
            "development_evidence_reinterpreted_as_production": False,
            "validation_checkpoint_selection_in_development_permitted": False,
        },
        "evidence_ready_registration": {
            "conditional_on_independent_acceptance": True,
            "permitted_blocker_delta": [],
            "permitted_field_delta": ["F146"],
            "permitted_formal_test_delta": [],
            "permitted_result_delta": [],
            "proposed_text": EVIDENCE_READY_REGISTRATION,
            "registration_performed_by_this_package": False,
        },
        "field_closures": [
            {
                "field_id": "F146",
                "json_pointer": F146_POINTER,
                "owner_role": "OWNER_B_METHOD_RUNTIME_AND_COMPUTE",
                "value": dict(RULE_VALUE),
            }
        ],
        "global_state": GLOBAL_STATE,
        "machine_self_binding": {
            "path": MACHINE_PATH,
            "raw_self_hash_embedded": False,
            "semantic_self_digest_field": "record_sha256",
        },
        "package_bindings_excluding_machine_self": _package_bindings(root),
        "package_file_roster": list(PACKAGE_ROSTER),
        "package_kind": PACKAGE_KIND,
        "predecessor_bindings": _predecessor_bindings(root),
        "predecessor_group_counts": dict(PREDECESSOR_GROUP_COUNTS),
        "predecessor_semantic_receipt": _validate_predecessor_semantics(root),
        "project_effects_and_nonclaims": {
            "B07_remains_open": True,
            "B12_remains_open": True,
            "F139_F145_and_F147_remain_open": True,
            "F144_metric_direction_representation_equality_tolerance_remain_null": True,
            "F150_F162_compute_fields_remain_open": True,
            "all_12_blockers_remain_open": True,
            "checkpoint_cadence_or_maximum_step_selected": False,
            "checkpoint_storage_retention_or_cadence_selected": False,
            "checkpoint_selection_or_training_performed": False,
            "data_entropy_runtime_or_scientific_execution_performed": False,
            "formal_test_28_status": "OPEN",
            "formal_test_29_status": "OPEN",
            "formal_test_30_status": "PENDING",
            "only_fields_closed": ["F146"],
            "result_claim_or_submission_promoted": False,
            "results_filled": 0,
            "tracker_or_evidence_ledger_edited": False,
        },
        "qualification_boundary": {
            "canonical_duplicate_free_ascii_json_required": True,
            "hostile_mutations_use_disposable_test_replicas_only": True,
            "independent_review_required_before_registration": True,
            "machine_generated_only_after_final_f137_review": True,
            "pure_synthetic_selector_only": True,
            "read_only_stable_no_follow_validator": True,
            "self_validation_is_independent_acceptance": False,
        },
        "rule_contract": dict(RULE_VALUE),
        "schema_version": SCHEMA,
        "source_effect_surface": {
            "checkpoint_file_read_or_write": False,
            "connector_or_subprocess": False,
            "data_reader_or_writer": False,
            "environment_or_project_science_import": False,
            "network": False,
            "rng_or_entropy": False,
            "training_or_optimizer_step": False,
            "validation_metric_value_accepted": False,
        },
        "state": STATE,
        "synthetic_qualification": dict(SYNTHETIC_QUALIFICATION),
        "workstream_transition": {
            "after": {
                "data_governance_reproduction": {"closed": 4, "open": 48},
                "final_sealed_freeze": {"closed": 0, "open": 1},
                "method_runtime_compute": {"closed": 2, "open": 63},
                "theory_statistics": {"closed": 20, "open": 34},
            },
            "before": {
                "data_governance_reproduction": {"closed": 4, "open": 48},
                "final_sealed_freeze": {"closed": 0, "open": 1},
                "method_runtime_compute": {"closed": 1, "open": 64},
                "theory_statistics": {"closed": 20, "open": 34},
            },
        },
        "reported_date": REPORTED_DATE,
    }
    record["record_sha256"] = record_sha256(record)
    return record


def validate(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    if not isinstance(root, Path) or not root.is_absolute():
        raise ValidationError("workspace root must be an absolute Path")
    machine_raw = _stable_read(root, MACHINE_PATH)
    machine = _parse_json(machine_raw, MACHINE_PATH)
    if machine_raw != canonical_machine_bytes(machine):
        raise ValidationError("machine record is not canonical ASCII JSON plus LF")
    expected = expected_record(root)
    _strict_equal(machine, expected, "machine record")
    if machine["record_sha256"] != record_sha256(machine):
        raise ValidationError("machine semantic self-digest mismatch")
    if len(CLOSED_BEFORE) != 22 or len(CLOSED_AFTER) != 23:
        raise ValidationError("closed-field cardinality drift")
    if len(OPEN_BEFORE) != 144 or len(OPEN_AFTER) != 143:
        raise ValidationError("open-field cardinality drift")
    if tuple(field for field in CLOSED_AFTER if field not in CLOSED_BEFORE) != (
        "F146",
    ):
        raise ValidationError("field delta is not exactly F146")
    return {
        "B12_open": True,
        "F146_closed": True,
        "control_predicate": CONTROL_PREDICATE,
        "effective_open_blocker_count": 12,
        "effective_post_execution_closed": 3,
        "effective_post_execution_open": 3,
        "effective_pre_execution_closed": 23,
        "effective_pre_execution_open": 143,
        "formal_tests_closed": 0,
        "global_state": GLOBAL_STATE,
        "record_sha256": machine["record_sha256"],
        "results_filled": 0,
        "runtime_or_scientific_execution": False,
        "schema_version": SCHEMA,
        "selection_performed": False,
        "state": STATE,
        "tracker_edit_performed": False,
        "unresolved_fields_closed": 1,
        "validation": "PASS",
    }


def main() -> None:
    print(
        json.dumps(
            validate(WORKSPACE_ROOT),
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
