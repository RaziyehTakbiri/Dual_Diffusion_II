"""Read-only validator and pure policy checker for the additive F145 freeze.

The checker qualifies the exact no-validation-early-stopping policy against a
caller-certified future F143 bound.  It has no writer, network, connector,
subprocess, entropy, project-science, data, training, checkpoint, runtime, or
result route.
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

SCHEMA = "heterodiff-manuscript-v3-f145-validation-early-stopping-freeze-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "F145_VALIDATION_EARLY_STOPPING_DISABLED_F143_BOUND_ONLY_PREOUTCOME"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
REPORTED_DATE = "2026-09-01"
PACKAGE_KIND = "ADDITIVE_PREOUTCOME_EXACT_F145_FIELD_CLOSURE"
CONTROL_PREDICATE = STATE

HUMAN_PATH = "PROJECT_F145_VALIDATION_EARLY_STOPPING_FREEZE.md"
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_f145_validation_early_stopping_freeze_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_f145_validation_early_stopping_freeze_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_f145_validation_early_stopping_freeze_v1.py"
)
PACKAGE_ROSTER = (HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)

F145_POINTER = "/training_and_checkpoint_plan/early_stopping_patience"
FIELD_VALUE = "DISABLED_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY"
POLICY_ID = "F145_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY_V1"
REFUSAL = "F145_POLICY_REFUSAL_NO_EXECUTABLE_TRAINING_PLAN"
F143_BOUND_DOMAIN = b"heterodiff-f145-certified-f143-bound-v1\0"
SHA256_RE = re.compile(r"[0-9a-f]{64}")

COORDINATOR_INSTRUCTION = (
    "Begin F145 package construction after F146 independent acceptance, receipt "
    "binding, and registration; close only F145 to the exact disabled-validation-"
    "early-stopping sentinel, bind the verified lineage plus Gate-A/F148 and the "
    "final F146 five-file group, and do not edit tracker or evidence ledger."
)

EVIDENCE_READY_REGISTRATION = (
    "Upon independent acceptance, register only this delta: F145 "
    "(`/training_and_checkpoint_plan/early_stopping_patience`) is closed to the "
    "exact sentinel `DISABLED_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY` "
    "under policy `F145_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY_V1`. "
    "There is no validation early stopping and no patience counter, monitor, "
    "direction, minimum delta, warmup, cadence, reset, smoothing, best-so-far "
    "selection, adaptive extension, top-up, resume, restart, or retry. COMPLETE "
    "is admissible only at a separately final-frozen, caller-certified positive "
    "exact F143 completed-update or epoch bound with its exact unit. Earlier "
    "termination is limited to the existing four failure statuses; F148 forbids "
    "infrastructure rerun, and F146 checkpoint choice cannot change duration. "
    "Effective PRE moves from 143 open / 23 closed to 142 open / 24 closed; POST "
    "remains 3 open / 3 closed; total moves from 146 open / 26 closed to 145 "
    "open / 27 closed; method/runtime/compute moves from 63/2 to 62/3. F139--"
    "F144, F147, F150--F162, B12, all 12 blockers, Formal Tests, results, "
    "runtime, data, science, claims, and submission remain open or absent."
)

POLICY_INPUT_KEYS = (
    "certificate",
    "observation",
    "policy_value",
)
POLICY_CERTIFICATE_KEYS = (
    "f143_bound_final_and_frozen_certified",
    "f143_bound_sha256",
    "f143_bound_unit",
    "f143_bound_value",
    "policy_id",
    "production_history_authenticated_by_helper",
    "training_run_unit_sha256",
)
POLICY_OBSERVATION_KEYS = (
    "completed_units",
    "event_kind",
    "scheduled_run_status",
    "training_run_unit_sha256",
)
SUCCESS_OUTPUT_KEYS = (
    "action",
    "caller_certifications_structurally_accepted",
    "completed_units",
    "f143_bound_sha256",
    "f143_bound_unit",
    "f143_bound_value",
    "policy_id",
    "policy_value",
    "production_history_authenticated",
    "scheduled_run_status",
    "training_run_unit_sha256",
    "validation_early_stopping_used",
)
REFUSAL_OUTPUT_KEYS = (
    "disposition",
    "executable_training_plan_produced",
    "policy_id",
    "reason_code",
)
REFUSAL_REASON_CODES = (
    "BOUND_NOT_FINAL_OR_FROZEN",
    "BOUND_SCHEMA_NONCANONICAL",
    "BOUND_UNIT_NONCANONICAL",
    "CERTIFICATE_SCHEMA_NONCANONICAL",
    "DIGEST_NONCANONICAL",
    "EVENT_SCHEMA_NONCANONICAL",
    "F143_BOUND_OVERSHOOT",
    "F143_BOUND_DIGEST_MISMATCH",
    "HISTORY_AUTHENTICATION_CLAIM_NONCANONICAL",
    "OBSERVATION_SCHEMA_NONCANONICAL",
    "POLICY_INPUT_SCHEMA_NONCANONICAL",
    "POLICY_SENTINEL_NONCANONICAL",
    "PROGRESS_AT_BOUND_REQUIRES_COMPLETE_STATUS",
    "STATUS_BOUNDARY_MISMATCH",
    "TERMINAL_STATUS_NONCANONICAL",
    "TRAINING_RUN_UNIT_MISMATCH",
)
BOUND_UNITS = ("COMPLETED_OPTIMIZER_UPDATES", "COMPLETED_EPOCHS")
EVENT_KINDS = ("PROGRESS", "TERMINAL_STATUS")
SCHEDULED_RUN_STATUSES = (
    "COMPLETE",
    "ALGORITHMIC_FAILURE",
    "NONFINITE",
    "OOM_OR_TIMEOUT",
    "INFRA_ABORT",
)
FAILURE_STATUSES = SCHEDULED_RUN_STATUSES[1:]

POLICY_CONTRACT: Mapping[str, Any] = {
    "exact_field_value": FIELD_VALUE,
    "policy_id": POLICY_ID,
    "refusal_disposition": REFUSAL,
    "f143_bound_final_and_frozen_certification_required": True,
    "f143_bound_must_be_positive_exact_builtin_int": True,
    "f143_bound_units": list(BOUND_UNITS),
    "f143_bound_digest_domain_ascii": "heterodiff-f145-certified-f143-bound-v1",
    "f143_bound_digest_domain_suffix_hex": "00",
    "f143_bound_digest_payload_key_order": [
        "f143_bound_unit",
        "f143_bound_value",
    ],
    "complete_status_only_at_exact_f143_bound": True,
    "earlier_terminal_statuses": list(FAILURE_STATUSES),
    "existing_scheduled_run_terminal_status_roster": list(SCHEDULED_RUN_STATUSES),
    "refusal_is_not_a_scheduled_run_terminal_status": True,
    "validation_early_stopping_enabled": False,
    "patience_counter_exists": False,
    "validation_monitor_direction_min_delta_or_stop_signal_exists": False,
    "validation_warmup_cadence_reset_smoothing_or_best_so_far_exists": False,
    "validation_shadow_stopping_field_exists": False,
    "validation_driven_stop_extend_resume_retry_or_duration_change_permitted": False,
    "adaptive_extension_topup_or_extra_units_permitted": False,
    "resume_restart_retry_rerun_or_replacement_permitted_by_f145": False,
    "f148_infrastructure_rerun_permitted": False,
    "f146_checkpoint_choice_may_change_training_duration": False,
    "f143_value_unit_cadence_capacity_or_runtime_selected_here": False,
    "project_executable_after_this_freeze": False,
    "pure_helper_authenticates_production_history_or_f143_finality": False,
    "shadow_fields_forbidden": [
        "best_so_far",
        "check_cadence",
        "grace_period",
        "minimum_delta",
        "monitor",
        "monitor_direction",
        "patience",
        "plateau_counter",
        "reset_rule",
        "smoothing",
        "validation_stop_signal",
        "warmup",
    ],
    "top_level_key_order": list(POLICY_INPUT_KEYS),
    "certificate_key_order": list(POLICY_CERTIFICATE_KEYS),
    "observation_key_order": list(POLICY_OBSERVATION_KEYS),
    "success_output_key_order": list(SUCCESS_OUTPUT_KEYS),
    "refusal_output_key_order": list(REFUSAL_OUTPUT_KEYS),
    "refusal_reason_codes": list(REFUSAL_REASON_CODES),
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
    "F146",
    "F148",
)
CLOSED_AFTER = tuple(sorted(CLOSED_BEFORE + ("F145",)))
OPEN_BEFORE = tuple(field for field in PRE_FIELDS if field not in CLOSED_BEFORE)
OPEN_AFTER = tuple(field for field in PRE_FIELDS if field not in CLOSED_AFTER)


class ValidationError(ValueError):
    """Package custody, schema, or semantic validation failed."""


class PolicyRefusal(ValidationError):
    """The F145 checker refused without producing an executable plan."""

    disposition = REFUSAL

    def __init__(self, reason_code: str) -> None:
        if reason_code not in REFUSAL_REASON_CODES:
            raise RuntimeError("unknown F145 refusal reason code")
        self.reason_code = reason_code
        super().__init__(REFUSAL + ": " + reason_code)

    def as_record(self) -> Dict[str, Any]:
        record = {
            "disposition": REFUSAL,
            "executable_training_plan_produced": False,
            "policy_id": POLICY_ID,
            "reason_code": self.reason_code,
        }
        if tuple(record) != REFUSAL_OUTPUT_KEYS:
            raise RuntimeError("refusal output key-order drift")
        return record


def _refuse(reason_code: str) -> None:
    raise PolicyRefusal(reason_code)


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


def _policy_digest(value: Any) -> str:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        _refuse("DIGEST_NONCANONICAL")
    return value


def _positive_f143_bound(value: Any) -> int:
    if type(value) is not int or value <= 0:
        _refuse("BOUND_SCHEMA_NONCANONICAL")
    return value


def _nonnegative_completed_units(value: Any) -> int:
    if type(value) is not int or value < 0:
        _refuse("EVENT_SCHEMA_NONCANONICAL")
    return value


def canonical_f143_bound_sha256(bound_unit: Any, bound_value: Any) -> str:
    """Bind the exact future F143 unit/value without selecting either one."""

    if type(bound_unit) is not str or bound_unit not in BOUND_UNITS:
        _refuse("BOUND_UNIT_NONCANONICAL")
    bound = _positive_f143_bound(bound_value)
    payload = {
        "f143_bound_unit": bound_unit,
        "f143_bound_value": bound,
    }
    return _sha256(F143_BOUND_DOMAIN + _canonical_payload_bytes(payload))


def evaluate_no_validation_early_stopping(value: Any) -> Dict[str, Any]:
    """Qualify one synthetic F143-bound observation under the frozen policy.

    The checker accepts no validation value and authenticates neither the
    caller's future F143 certificate nor production history.  Every invalid
    input raises :class:`PolicyRefusal`; no executable plan is returned.
    """

    if type(value) is not dict or tuple(value) != POLICY_INPUT_KEYS:
        _refuse("POLICY_INPUT_SCHEMA_NONCANONICAL")
    if type(value["policy_value"]) is not str or value["policy_value"] != FIELD_VALUE:
        _refuse("POLICY_SENTINEL_NONCANONICAL")
    certificate = value["certificate"]
    if (
        type(certificate) is not dict
        or tuple(certificate) != POLICY_CERTIFICATE_KEYS
    ):
        _refuse("CERTIFICATE_SCHEMA_NONCANONICAL")
    if certificate["f143_bound_final_and_frozen_certified"] is not True:
        _refuse("BOUND_NOT_FINAL_OR_FROZEN")
    unit_label = certificate["f143_bound_unit"]
    if type(unit_label) is not str or unit_label not in BOUND_UNITS:
        _refuse("BOUND_UNIT_NONCANONICAL")
    bound = _positive_f143_bound(certificate["f143_bound_value"])
    claimed_bound_digest = _policy_digest(certificate["f143_bound_sha256"])
    observed_bound_digest = canonical_f143_bound_sha256(unit_label, bound)
    if claimed_bound_digest != observed_bound_digest:
        _refuse("F143_BOUND_DIGEST_MISMATCH")
    if type(certificate["policy_id"]) is not str or certificate["policy_id"] != POLICY_ID:
        _refuse("POLICY_SENTINEL_NONCANONICAL")
    if certificate["production_history_authenticated_by_helper"] is not False:
        _refuse("HISTORY_AUTHENTICATION_CLAIM_NONCANONICAL")
    run_unit = _policy_digest(certificate["training_run_unit_sha256"])

    observation = value["observation"]
    if (
        type(observation) is not dict
        or tuple(observation) != POLICY_OBSERVATION_KEYS
    ):
        _refuse("OBSERVATION_SCHEMA_NONCANONICAL")
    completed = _nonnegative_completed_units(observation["completed_units"])
    event_kind = observation["event_kind"]
    if type(event_kind) is not str or event_kind not in EVENT_KINDS:
        _refuse("EVENT_SCHEMA_NONCANONICAL")
    status = observation["scheduled_run_status"]
    observed_run_unit = _policy_digest(observation["training_run_unit_sha256"])
    if observed_run_unit != run_unit:
        _refuse("TRAINING_RUN_UNIT_MISMATCH")
    if completed > bound:
        _refuse("F143_BOUND_OVERSHOOT")

    if event_kind == "PROGRESS":
        if status is not None:
            _refuse("EVENT_SCHEMA_NONCANONICAL")
        if completed == bound:
            _refuse("PROGRESS_AT_BOUND_REQUIRES_COMPLETE_STATUS")
        action = "CONTINUE_TO_F143_BOUND"
    else:
        if type(status) is not str or status not in SCHEDULED_RUN_STATUSES:
            _refuse("TERMINAL_STATUS_NONCANONICAL")
        if status == "COMPLETE":
            if completed != bound:
                _refuse("STATUS_BOUNDARY_MISMATCH")
            action = "TERMINAL_COMPLETE_AT_EXACT_F143_BOUND"
        else:
            action = "TERMINAL_EXISTING_FAILURE_STATUS"

    result = {
        "action": action,
        "caller_certifications_structurally_accepted": True,
        "completed_units": completed,
        "f143_bound_sha256": observed_bound_digest,
        "f143_bound_unit": unit_label,
        "f143_bound_value": bound,
        "policy_id": POLICY_ID,
        "policy_value": FIELD_VALUE,
        "production_history_authenticated": False,
        "scheduled_run_status": status,
        "training_run_unit_sha256": run_unit,
        "validation_early_stopping_used": False,
    }
    if tuple(result) != SUCCESS_OUTPUT_KEYS:
        raise RuntimeError("success output key-order drift")
    return result


def synthetic_policy_input(
    f143_bound_value: int,
    f143_bound_unit: str,
    completed_units: int,
    event_kind: str,
    scheduled_run_status: Optional[str],
    training_run_unit_sha256: str,
) -> Dict[str, Any]:
    """Build one exact synthetic policy-check input, never runtime evidence."""

    return {
        "certificate": {
            "f143_bound_final_and_frozen_certified": True,
            "f143_bound_sha256": canonical_f143_bound_sha256(
                f143_bound_unit, f143_bound_value
            ),
            "f143_bound_unit": f143_bound_unit,
            "f143_bound_value": f143_bound_value,
            "policy_id": POLICY_ID,
            "production_history_authenticated_by_helper": False,
            "training_run_unit_sha256": training_run_unit_sha256,
        },
        "observation": {
            "completed_units": completed_units,
            "event_kind": event_kind,
            "scheduled_run_status": scheduled_run_status,
            "training_run_unit_sha256": training_run_unit_sha256,
        },
        "policy_value": FIELD_VALUE,
    }


SYNTHETIC_TRAINING_RUN_UNIT_SHA256 = _sha256(b"synthetic-f145-training-run-unit")
SYNTHETIC_INPUT = synthetic_policy_input(
    8,
    "COMPLETED_OPTIMIZER_UPDATES",
    3,
    "PROGRESS",
    None,
    SYNTHETIC_TRAINING_RUN_UNIT_SHA256,
)
SYNTHETIC_QUALIFICATION = evaluate_no_validation_early_stopping(SYNTHETIC_INPUT)


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
    (
        "GATE_A_F148_BASELINE",
        "human",
        "PROJECT_GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISION_FREEZE.md",
        8073,
        "ca9a593c54a9d3587f58a3d414defd5cf81a3765395d5ebb8494e6effa6dd44d",
        None,
    ),
    (
        "GATE_A_F148_BASELINE",
        "machine",
        "research/fixtures/"
        "manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json",
        8455,
        "b8a74f1131f85aa1b7497f2f43bd34a0e30bc471953c935d4362a5a8dea1446a",
        "aa3fe845190d6c74472706749598ba245de1925ce03a5702d1d2eed81a88bffa",
    ),
    (
        "GATE_A_F148_BASELINE",
        "validator",
        "research/diagnostics/"
        "manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.py",
        22410,
        "3769017b9d6e2b1d2e1f876a84d5cfb49ccb9160e2505338ce5095b03bf790c5",
        None,
    ),
    (
        "GATE_A_F148_BASELINE",
        "test",
        "tests/unit/"
        "test_manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.py",
        28454,
        "82955f1d0cfefeef439e63ebf1cc8d478225b6529485257ccdb7a5d402d245e7",
        None,
    ),
    (
        "ACCEPTED_F146_BASELINE",
        "human",
        "PROJECT_F146_CHECKPOINT_TIE_RULE_FREEZE.md",
        18409,
        "403858d0a1afe5c4498973b568ca2e528cb0cde54a02dde52f74123eb0b4c249",
        None,
    ),
    (
        "ACCEPTED_F146_BASELINE",
        "machine",
        "research/fixtures/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.json",
        20813,
        "21dcfd76f4701f3be033f6ab70a7c93fd9b9b3475ab773d8709d5d027dcbf447",
        "33ae0137e1c41da0553b78d7790f4556ddf7d993bbf635fe9dd6abd46ec9c131",
    ),
    (
        "ACCEPTED_F146_BASELINE",
        "validator",
        "research/diagnostics/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.py",
        55293,
        "f260cf4cb34cf05a6ddbf55c9690207f10b8758c06a23f3afd28f6ad76670ab5",
        None,
    ),
    (
        "ACCEPTED_F146_BASELINE",
        "test",
        "tests/unit/test_manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.py",
        36317,
        "cfe4bd7689b6d40abd28b363e553172ecdbb1dc0bc1a759d61abb124e5332bbd",
        None,
    ),
    (
        "ACCEPTED_F146_BASELINE",
        "independent_review",
        "PROJECT_F146_CHECKPOINT_TIE_RULE_FREEZE_INDEPENDENT_REVIEW.md",
        14443,
        "9c2858279242dc1005e792ce827e9d95a27b70a62baf6b605e2c21f25724b089",
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
    "GATE_A_F148_BASELINE": 4,
    "ACCEPTED_F146_BASELINE": 5,
}
NONTERMINAL_LF_PREDECESSOR_PATHS = {
    "research/fixtures/"
    "manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration_v1.json"
}

# Installed only after the human and hostile-test bytes were internally stable.
EXPECTED_HUMAN_BYTES = 14003
EXPECTED_HUMAN_SHA256 = "ef31cab9d4d8a245d8e88b47590d90a335b31f230a499893629d3a46e9a8eee4"
EXPECTED_TEST_BYTES = 39441
EXPECTED_TEST_SHA256 = "c8c796f331224f101d54af8f61c9c8d4f0d26e4478afe70ef8187b385da0bfe0"


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
        POLICY_ID,
        FIELD_VALUE,
        REFUSAL,
        F145_POINTER,
        "143 open / 23 closed",
        "142 open / 24 closed",
        "146 open / 26 closed",
        "145 open / 27 closed",
        "B12 remains open",
        "second consecutive B12 package",
        "any third consecutive B12 package requires explicit scope review",
        "NEVER_TRUE_NO_INFRASTRUCTURE_RERUN",
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

    gate_a = _parse_json(
        _stable_read(
            root,
            "research/fixtures/"
            "manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json",
        ),
        "Gate-A local machine",
    )
    f148_rows = [
        row for row in gate_a.get("field_closures", [])
        if type(row) is dict and row.get("field_id") == "F148"
    ]
    expected_f148_row = {
        "field_id": "F148",
        "json_pointer": (
            "/stopping_failure_and_exclusion_plan/infrastructure_rerun_predicate"
        ),
        "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_FREEZE",
        "value": "NEVER_TRUE_NO_INFRASTRUCTURE_RERUN",
    }
    _strict_equal(f148_rows, [expected_f148_row], "Gate-A F148 closure")
    gate_downstream = gate_a.get("downstream_contract")
    if (
        type(gate_downstream) is not dict
        or gate_downstream.get("infrastructure_rerun_predicate")
        != "NEVER_TRUE_NO_INFRASTRUCTURE_RERUN"
        or gate_downstream.get(
            "retry_resume_replacement_topup_threshold_seed_config_or_route_change_permitted"
        ) is not False
    ):
        raise ValidationError("Gate-A F148 no-rerun semantic drift")

    f146 = _parse_json(
        _stable_read(
            root,
            "research/fixtures/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.json",
        ),
        "F146 machine",
    )
    expected_f146_after = {
        "post_execution_closed": 3,
        "post_execution_open": 3,
        "pre_execution_closed": 23,
        "pre_execution_open": 143,
        "total_closed": 26,
        "total_open": 146,
    }
    _strict_equal(
        f146.get("count_transition", {}).get("after"),
        expected_f146_after,
        "F146 count anchor",
    )
    f146_closures = f146.get("field_closures")
    if (
        type(f146_closures) is not list
        or len(f146_closures) != 1
        or f146_closures[0].get("field_id") != "F146"
        or f146_closures[0].get("json_pointer")
        != "/training_and_checkpoint_plan/checkpoint_tie_rule"
    ):
        raise ValidationError("F146 sole-field closure projection drift")
    f146_contract = f146.get("rule_contract")
    if (
        type(f146_contract) is not dict
        or f146_contract.get("existing_scheduled_run_terminal_status_roster")
        != list(SCHEDULED_RUN_STATUSES)
        or f146_contract.get("refusal_is_not_a_scheduled_run_terminal_status")
        is not True
    ):
        raise ValidationError("F146 five-status projection drift")
    f146_effects = f146.get("project_effects_and_nonclaims")
    if (
        type(f146_effects) is not dict
        or f146_effects.get("only_fields_closed") != ["F146"]
        or f146_effects.get("B12_remains_open") is not True
        or f146_effects.get("F139_F145_and_F147_remain_open") is not True
        or f146_effects.get("checkpoint_selection_or_training_performed") is not False
    ):
        raise ValidationError("F146 nonclosure projection drift")

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
    _required_utf8_text(
        root,
        "PROJECT_F146_CHECKPOINT_TIE_RULE_FREEZE_INDEPENDENT_REVIEW.md",
        (
            "INDEPENDENT_REVIEW_GO",
            "`GO` for the exact four-file F146 package",
            "143 open / 23 closed",
            "146 open / 26 closed",
            "F145 early-stopping patience",
        ),
    )
    return {
        "anti_drift_requires_named_direct_count_reduction": True,
        "base_F143_F144_F145_values_null": True,
        "base_validation_early_stopping_allowed_only_if_frozen": True,
        "base_experiment_optional_stopping_forbidden": True,
        "b11_after_pre_145_21_post_3_3_total_148_24": True,
        "b11_only_F168_F170_F171_closed_and_F169_open": True,
        "development_final_update_only_no_selection_or_early_stopping": True,
        "d1_checkpoint_ineligible_and_not_selected": True,
        "f148_never_true_no_infrastructure_rerun": True,
        "f137_after_pre_144_22_post_3_3_total_147_25": True,
        "f137_independent_review_go_and_only_F137_closed": True,
        "f146_after_pre_143_23_post_3_3_total_146_26": True,
        "f146_independent_review_go_and_only_F146_closed": True,
        "f146_preserves_existing_five_scheduled_statuses": True,
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
                "pre_execution_closed": 23,
                "pre_execution_open": 143,
                "total_closed": 26,
                "total_open": 146,
            },
            "delta": {
                "closed": 1,
                "closed_fields": ["F145"],
                "open": -1,
            },
            "after": {
                "post_execution_closed": 3,
                "post_execution_open": 3,
                "pre_execution_closed": 24,
                "pre_execution_open": 142,
                "total_closed": 27,
                "total_open": 145,
            },
        },
        "development_evidence_exclusion": {
            "d1_checkpoint_metric_or_training_duration_eligible_for_f145": False,
            "d1_checkpoint_selection_performed": False,
            "development_checkpoint_rule": "FINAL_UPDATE_ONLY",
            "development_checkpoint_tie_rule": "NOT_APPLICABLE_NO_SELECTION",
            "development_early_stopping": False,
            "development_evidence_reinterpreted_as_production": False,
            "validation_checkpoint_selection_in_development_permitted": False,
        },
        "evidence_ready_registration": {
            "conditional_on_independent_acceptance": True,
            "permitted_blocker_delta": [],
            "permitted_field_delta": ["F145"],
            "permitted_formal_test_delta": [],
            "permitted_result_delta": [],
            "proposed_text": EVIDENCE_READY_REGISTRATION,
            "registration_performed_by_this_package": False,
        },
        "field_closures": [
            {
                "field_id": "F145",
                "json_pointer": F145_POINTER,
                "owner_role": "OWNER_B_METHOD_RUNTIME_AND_COMPUTE",
                "value": FIELD_VALUE,
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
            "F139_F144_and_F147_remain_open": True,
            "F143_bound_value_and_unit_remain_open": True,
            "F144_metric_direction_representation_equality_tolerance_remain_null": True,
            "F146_prior_checkpoint_tie_rule_closure_preserved": True,
            "F148_never_true_no_infrastructure_rerun_preserved": True,
            "F150_F162_compute_fields_remain_open": True,
            "all_12_blockers_remain_open": True,
            "checkpoint_choice_may_change_training_duration": False,
            "checkpoint_cadence_or_maximum_horizon_selected": False,
            "checkpoint_storage_retention_or_cadence_selected": False,
            "checkpoint_selection_or_training_performed": False,
            "data_entropy_runtime_or_scientific_execution_performed": False,
            "formal_test_28_status": "OPEN",
            "formal_test_29_status": "OPEN",
            "formal_test_30_status": "PENDING",
            "only_fields_closed": ["F145"],
            "result_claim_or_submission_promoted": False,
            "results_filled": 0,
            "third_consecutive_B12_package_authorized_without_scope_review": False,
            "tracker_or_evidence_ledger_edited": False,
            "validation_early_stopping_patience_counter_or_shadow_field_created": False,
        },
        "qualification_boundary": {
            "canonical_duplicate_free_ascii_json_required": True,
            "hostile_mutations_use_disposable_test_replicas_only": True,
            "independent_review_required_before_registration": True,
            "machine_generated_only_after_final_f146_review": True,
            "pure_helper_authenticates_f143_finality_or_production_history": False,
            "pure_synthetic_policy_checker_only": True,
            "read_only_stable_no_follow_validator": True,
            "second_consecutive_B12_package": True,
            "self_validation_is_independent_acceptance": False,
        },
        "policy_contract": dict(POLICY_CONTRACT),
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
            "validation_patience_monitor_or_stop_signal_accepted": False,
        },
        "state": STATE,
        "synthetic_qualification": dict(SYNTHETIC_QUALIFICATION),
        "workstream_transition": {
            "after": {
                "data_governance_reproduction": {"closed": 4, "open": 48},
                "final_sealed_freeze": {"closed": 0, "open": 1},
                "method_runtime_compute": {"closed": 3, "open": 62},
                "theory_statistics": {"closed": 20, "open": 34},
            },
            "before": {
                "data_governance_reproduction": {"closed": 4, "open": 48},
                "final_sealed_freeze": {"closed": 0, "open": 1},
                "method_runtime_compute": {"closed": 2, "open": 63},
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
    if len(CLOSED_BEFORE) != 23 or len(CLOSED_AFTER) != 24:
        raise ValidationError("closed-field cardinality drift")
    if len(OPEN_BEFORE) != 143 or len(OPEN_AFTER) != 142:
        raise ValidationError("open-field cardinality drift")
    if tuple(field for field in CLOSED_AFTER if field not in CLOSED_BEFORE) != (
        "F145",
    ):
        raise ValidationError("field delta is not exactly F145")
    return {
        "B12_open": True,
        "F145_closed": True,
        "control_predicate": CONTROL_PREDICATE,
        "effective_open_blocker_count": 12,
        "effective_post_execution_closed": 3,
        "effective_post_execution_open": 3,
        "effective_pre_execution_closed": 24,
        "effective_pre_execution_open": 142,
        "formal_tests_closed": 0,
        "global_state": GLOBAL_STATE,
        "record_sha256": machine["record_sha256"],
        "results_filled": 0,
        "runtime_or_scientific_execution": False,
        "schema_version": SCHEMA,
        "training_or_early_stopping_performed": False,
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
