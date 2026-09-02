"""Canonical records for the dormant A1 R1 activation-preparation v2 package.

This module is stdlib-only and has no filesystem, entropy, launch, or scientific
execution entry point.  It defines closed, type-strict JSON record contracts.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Mapping, Tuple


REGISTRATION_SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-activation-preparation-" "implementation-freeze-v2"
)
QUALIFICATION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-implementation-qualification-v2"
)
ATTEMPT_MARKER_SCHEMA = "heterodiff-a1-r1-activation-preparation-attempt-marker-v2"
LEDGER_GENESIS_SCHEMA = "heterodiff-a1-r1-preparation-ledger-genesis-v2"
LEDGER_EVENT_SCHEMA = "heterodiff-a1-r1-preparation-ledger-event-v2"
OPERATION_NONCE_CLAIM_SCHEMA = "heterodiff-a1-r1-preparation-operation-nonce-claim-v2"
SOURCE_CAPSULE_MANIFEST_SCHEMA = "heterodiff-a1-r1-source-capsule-manifest-v2"
SOURCE_CAPSULE_ADMISSION_SCHEMA = "heterodiff-a1-r1-source-capsule-admission-v2"
RUNTIME_REQUEST_SCHEMA = "heterodiff-a1-r1-runtime-double-capture-request-v2"
RUNTIME_ENVELOPE_BINDING_SCHEMA = (
    "heterodiff-a1-r1-runtime-double-capture-envelope-binding-v2"
)
RUNTIME_CANDIDATE_SCHEMA = "heterodiff-a1-r1-runtime-candidate-v2"

MILESTONE_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_IMPLEMENTATION_V2_FROZEN_"
    "AWAITING_EXPLICIT_MARKER_AUTHORIZATION_ZERO_EXECUTION_NOT_EXECUTABLE"
)

SHA256_HEX_LENGTH = 64
MAXIMUM_RECORD_BYTES = 16 * 1024 * 1024


class ContractError(ValueError):
    """Raised when a v2 preparation record is not exact and canonical."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def require_sha256(value: Any, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != SHA256_HEX_LENGTH
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ContractError(name + " is not a lowercase SHA-256 digest")
    return value


def _field(kind: str, argument: Any = None) -> Tuple[str, Any]:
    return (kind, argument)


MARKER_FIELDS = {
    "schema": _field("literal", ATTEMPT_MARKER_SCHEMA),
    "registration_raw_sha256": _field("sha256"),
    "registration_record_sha256": _field("sha256"),
    "predecessor_registration_raw_sha256": _field("sha256"),
    "predecessor_registration_record_sha256": _field("sha256"),
    "predecessor_qualification_snapshot_sha256": _field("sha256"),
    "human_sha256": _field("sha256"),
    "contracts_sha256": _field("sha256"),
    "authority_sha256": _field("sha256"),
    "runtime_sha256": _field("sha256"),
    "test_sha256": _field("sha256"),
    "path_roster_sha256": _field("sha256"),
    "d1_quarantine_roster_sha256": _field("sha256"),
    "operator_authorization_context": _field("string"),
    "operator_authorization_sha256": _field("sha256"),
    "preparation_instance_nonce_sha256": _field("sha256"),
    "entropy_source": _field("literal", "secrets.token_bytes"),
    "entropy_byte_count": _field("literal", 32),
    "raw_entropy_persisted": _field("literal", False),
    "exclusive_inode_reserved_before_entropy": _field("literal", True),
    "all_dormant_v1_paths_absent_after_reservation": _field("literal", True),
    "v2_root_absent_after_reservation": _field("literal", True),
    "scientific_campaign_nonce_minted": _field("literal", False),
    "attempt_state": _field(
        "literal", "PREPARATION_ATTEMPT_SPENT_TERMINAL_MARKER_CREATED_NO_RETRY"
    ),
    "marker_sha256": _field("sha256"),
}

GENESIS_FIELDS = {
    "schema": _field("literal", LEDGER_GENESIS_SCHEMA),
    "marker_raw_sha256": _field("sha256"),
    "marker_sha256": _field("sha256"),
    "registration_raw_sha256": _field("sha256"),
    "registration_record_sha256": _field("sha256"),
    "predecessor_registration_record_sha256": _field("sha256"),
    "predecessor_qualification_snapshot_sha256": _field("sha256"),
    "preparation_instance_nonce_sha256": _field("sha256"),
    "path_roster_sha256": _field("sha256"),
    "source_capsule_plan_sha256": _field("sha256"),
    "registry_semantic_sha256": _field("sha256"),
    "d1_quarantine_roster_sha256": _field("sha256"),
    "preparation_event_protocol_sha256": _field("sha256"),
    "scientific_event_protocol_sha256": _field("sha256"),
    "writer_lock_relative_path": _field("string"),
    "next_preparation_event_ordinal": _field("literal", 0),
    "scientific_authority_ledger_created": _field("literal", False),
    "scientific_campaign_nonce_minted": _field("literal", False),
    "genesis_sha256": _field("sha256"),
}

OPERATION_NONCE_CLAIM_FIELDS = {
    "schema": _field("literal", OPERATION_NONCE_CLAIM_SCHEMA),
    "marker_sha256": _field("sha256"),
    "genesis_sha256": _field("sha256"),
    "preparation_instance_nonce_sha256": _field("sha256"),
    "claim_scope": _field("enum", ("PREPARATION_EVENT", "RUNTIME_CAPTURE_LAUNCH")),
    "preparation_event_ordinal": _field("int_or_none"),
    "operation_kind": _field("string"),
    "operation_nonce_sha256": _field("sha256"),
    "previous_head_sha256": _field("sha256"),
    "recovery_policy": _field(
        "enum",
        (
            "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
            "LAUNCH_SPENT_NO_RECAPTURE",
            "TERMINAL_NO_RETRY",
        ),
    ),
    "claim_state": _field("literal", "OPERATION_NONCE_SPENT"),
    "claim_sha256": _field("sha256"),
}

LEDGER_EVENT_FIELDS = {
    "schema": _field("literal", LEDGER_EVENT_SCHEMA),
    "marker_sha256": _field("sha256"),
    "genesis_sha256": _field("sha256"),
    "preparation_instance_nonce_sha256": _field("sha256"),
    "preparation_event_ordinal": _field("int"),
    "preparation_event_kind": _field("string"),
    "previous_head_sha256": _field("sha256"),
    "operation_nonce_sha256": _field("sha256"),
    "nonce_claim_sha256": _field("sha256"),
    "payload_schema": _field("string"),
    "payload_relative_path": _field("string"),
    "payload_raw_sha256": _field("sha256"),
    "payload_record_sha256": _field("sha256"),
    "event_outcome": _field("string"),
    "scientific_authority_event_ordinal": _field("literal", None),
    "rank_execution_performed": _field("literal", False),
    "training_execution_performed": _field("literal", False),
    "scientific_execution_performed": _field("literal", False),
    "event_sha256": _field("sha256"),
}

SOURCE_CAPSULE_MANIFEST_FIELDS = {
    "schema": _field("literal", SOURCE_CAPSULE_MANIFEST_SCHEMA),
    "marker_sha256": _field("sha256"),
    "genesis_sha256": _field("sha256"),
    "capsule_root_relative_path": _field("string"),
    "predecessor_source_manifest_sha256": _field("sha256"),
    "registry_semantic_sha256": _field("sha256"),
    "row_count": _field("literal", 53),
    "directory_count": _field("int"),
    "rows": _field("list"),
    "protocol_copy_count": _field("literal", 3),
    "local_package_source_count": _field("literal", 47),
    "nonpackage_input_count": _field("literal", 3),
    "parent_authority_in_child_import_path": _field("literal", False),
    "source_capsule_execution_admissible": _field("literal", False),
    "manifest_sha256": _field("sha256"),
}

SOURCE_CAPSULE_ADMISSION_FIELDS = {
    "schema": _field("literal", SOURCE_CAPSULE_ADMISSION_SCHEMA),
    "marker_sha256": _field("sha256"),
    "genesis_sha256": _field("sha256"),
    "manifest_raw_sha256": _field("sha256"),
    "manifest_sha256": _field("sha256"),
    "capsule_root_relative_path": _field("string"),
    "file_count": _field("literal", 53),
    "directory_count": _field("int"),
    "inventory_sha256": _field("sha256"),
    "all_rows_reopened_twice": _field("literal", True),
    "regular_files_only": _field("literal", True),
    "no_symlinks": _field("literal", True),
    "no_hardlinks": _field("literal", True),
    "no_extra_files": _field("literal", True),
    "no_extra_directories": _field("literal", True),
    "no_pyc": _field("literal", True),
    "owner_only_modes": _field("literal", True),
    "registry_seed_1729_absent": _field("literal", True),
    "scientific_execution_performed": _field("literal", False),
    "execution_admissible": _field("literal", False),
    "admission_sha256": _field("sha256"),
}

RUNTIME_REQUEST_FIELDS = {
    "schema": _field("literal", RUNTIME_REQUEST_SCHEMA),
    "marker_sha256": _field("sha256"),
    "genesis_sha256": _field("sha256"),
    "preparation_instance_nonce_sha256": _field("sha256"),
    "source_capsule_manifest_sha256": _field("sha256"),
    "source_capsule_admission_sha256": _field("sha256"),
    "target_profile_id": _field("string"),
    "capture_operation": _field(
        "literal", "EXACTLY_TWO_CAPTURES_NO_SCIENTIFIC_COMPUTE"
    ),
    "capture_count": _field("literal", 2),
    "capture_ordinals": _field("literal", [0, 1]),
    "python_relative_path": _field("string"),
    "capsule_root_relative_path": _field("string"),
    "site_packages_relative_path": _field("string"),
    "python_flags": _field("literal", ["-I", "-S", "-B", "-X", "utf8"]),
    "environment_policy_sha256": _field("sha256"),
    "launch_binding_preimage_sha256": _field("sha256"),
    "launch_binding_a_sha256": _field("sha256"),
    "launch_binding_b_sha256": _field("sha256"),
    "raw_capture_envelopes_persisted": _field("literal", False),
    "scientific_compute_requested": _field("literal", False),
    "runtime_approval_requested": _field("literal", False),
    "request_sha256": _field("sha256"),
}

RUNTIME_ENVELOPE_BINDING_FIELDS = {
    "schema": _field("literal", RUNTIME_ENVELOPE_BINDING_SCHEMA),
    "request_sha256": _field("sha256"),
    "capture_ordinal": _field("int"),
    "launch_claim_sha256": _field("sha256"),
    "launch_binding_sha256": _field("sha256"),
    "child_process_id": _field("int"),
    "child_exit_code": _field("literal", 0),
    "child_stdout_byte_count": _field("int"),
    "child_stderr_byte_count": _field("literal", 0),
    "child_oracle_raw_sha256": _field("sha256"),
    "child_oracle_api_sha256": _field("sha256"),
    "raw_envelope_sha256": _field("sha256"),
    "raw_envelope_record_sha256": _field("sha256"),
    "raw_envelope_persisted": _field("literal", False),
    "embedded_candidate_raw_sha256": _field("sha256"),
    "embedded_candidate_record_sha256": _field("sha256"),
    "semantic_manifest_sha256": _field("sha256"),
    "installed_files_manifest_sha256": _field("sha256"),
    "source_capsule_manifest_sha256": _field("sha256"),
    "target_profile_id": _field("string"),
    "privacy_safe_projection": _field("dict"),
    "privacy_projection_sha256": _field("sha256"),
    "unclassified_absolute_path_count": _field("literal", 0),
    "complete_installed_file_verification": _field("literal", True),
    "scientific_compute_executed": _field("literal", False),
    "approved": _field("literal", False),
    "binding_sha256": _field("sha256"),
}

RUNTIME_CANDIDATE_FIELDS = {
    "schema": _field("literal", RUNTIME_CANDIDATE_SCHEMA),
    "marker_sha256": _field("sha256"),
    "genesis_sha256": _field("sha256"),
    "preparation_instance_nonce_sha256": _field("sha256"),
    "request_sha256": _field("sha256"),
    "binding_a_raw_sha256": _field("sha256"),
    "binding_a_sha256": _field("sha256"),
    "binding_b_raw_sha256": _field("sha256"),
    "binding_b_sha256": _field("sha256"),
    "raw_envelope_a_sha256": _field("sha256"),
    "raw_envelope_a_record_sha256": _field("sha256"),
    "raw_envelope_b_sha256": _field("sha256"),
    "raw_envelope_b_record_sha256": _field("sha256"),
    "raw_capture_envelopes_persisted": _field("literal", False),
    "semantic_manifest_a_sha256": _field("sha256"),
    "semantic_manifest_b_sha256": _field("sha256"),
    "installed_files_manifest_a_sha256": _field("sha256"),
    "installed_files_manifest_b_sha256": _field("sha256"),
    "double_capture_semantically_stable": _field("bool"),
    "complete_installed_file_verification": _field("bool"),
    "candidate_state": _field(
        "enum", ("UNAPPROVED_PREPARATION_CANDIDATE", "REJECTED_DOUBLE_CAPTURE_MISMATCH")
    ),
    "approved": _field("literal", False),
    "runtime_admitted": _field("literal", False),
    "scientific_compute_executed": _field("literal", False),
    "execution_admissible": _field("literal", False),
    "candidate_not_reusable_as_formal_runtime_approval": _field("literal", True),
    "fresh_approval_recapture_required": _field("literal", True),
    "privacy_projection_sha256": _field("sha256"),
    "unclassified_absolute_path_count": _field("literal", 0),
    "candidate_sha256": _field("sha256"),
}


CONTRACTS = {
    "ATTEMPT_MARKER": (ATTEMPT_MARKER_SCHEMA, "marker_sha256", MARKER_FIELDS),
    "LEDGER_GENESIS": (LEDGER_GENESIS_SCHEMA, "genesis_sha256", GENESIS_FIELDS),
    "LEDGER_EVENT": (LEDGER_EVENT_SCHEMA, "event_sha256", LEDGER_EVENT_FIELDS),
    "OPERATION_NONCE_CLAIM": (
        OPERATION_NONCE_CLAIM_SCHEMA,
        "claim_sha256",
        OPERATION_NONCE_CLAIM_FIELDS,
    ),
    "SOURCE_CAPSULE_MANIFEST": (
        SOURCE_CAPSULE_MANIFEST_SCHEMA,
        "manifest_sha256",
        SOURCE_CAPSULE_MANIFEST_FIELDS,
    ),
    "SOURCE_CAPSULE_ADMISSION": (
        SOURCE_CAPSULE_ADMISSION_SCHEMA,
        "admission_sha256",
        SOURCE_CAPSULE_ADMISSION_FIELDS,
    ),
    "RUNTIME_REQUEST": (
        RUNTIME_REQUEST_SCHEMA,
        "request_sha256",
        RUNTIME_REQUEST_FIELDS,
    ),
    "RUNTIME_ENVELOPE_BINDING": (
        RUNTIME_ENVELOPE_BINDING_SCHEMA,
        "binding_sha256",
        RUNTIME_ENVELOPE_BINDING_FIELDS,
    ),
    "RUNTIME_CANDIDATE": (
        RUNTIME_CANDIDATE_SCHEMA,
        "candidate_sha256",
        RUNTIME_CANDIDATE_FIELDS,
    ),
}


def _validate_field(name: str, value: Any, specification: Tuple[str, Any]) -> None:
    kind, argument = specification
    if kind == "literal":
        if type(value) is not type(argument) or canonical_json(value) != canonical_json(
            argument
        ):
            raise ContractError(name + " changed from its exact literal")
        return
    if kind == "sha256":
        require_sha256(value, name)
        return
    if kind == "string":
        if type(value) is not str or not value:
            raise ContractError(name + " is not a nonempty string")
        return
    if kind == "bool":
        if type(value) is not bool:
            raise ContractError(name + " is not an exact Boolean")
        return
    if kind == "int":
        if type(value) is not int or value < 0:
            raise ContractError(name + " is not a nonnegative exact integer")
        return
    if kind == "int_or_none":
        if value is not None and (type(value) is not int or value < 0):
            raise ContractError(name + " is not null or a nonnegative exact integer")
        return
    if kind == "enum":
        if type(value) is not str or value not in argument:
            raise ContractError(name + " is outside its exact enumeration")
        return
    if kind == "list":
        if type(value) is not list:
            raise ContractError(name + " is not an exact list")
        return
    if kind == "dict":
        if type(value) is not dict:
            raise ContractError(name + " is not an exact object")
        return
    raise ContractError("unknown field kind: " + kind)


def validate_record(record: Any, contract_id: str) -> Dict[str, Any]:
    if contract_id not in CONTRACTS:
        raise ContractError("unknown contract id")
    schema, digest_key, fields = CONTRACTS[contract_id]
    if type(record) is not dict or set(record) != set(fields):
        raise ContractError(contract_id + " fields changed")
    if record.get("schema") != schema:
        raise ContractError(contract_id + " schema changed")
    for name, specification in fields.items():
        _validate_field(name, record[name], specification)
    body = dict(record)
    claimed = require_sha256(body[digest_key], digest_key)
    body[digest_key] = None
    expected = sha256(schema.encode("ascii") + b"\0" + canonical_json(body))
    if claimed != expected:
        raise ContractError(contract_id + " terminal digest changed")
    return json.loads(canonical_json(record).decode("ascii"))


def parse_record(payload: bytes, contract_id: str) -> Dict[str, Any]:
    if type(payload) is not bytes or not payload or len(payload) > MAXIMUM_RECORD_BYTES:
        raise ContractError("record payload has an invalid size or type")
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError("record payload is not canonical ASCII JSON") from error
    checked = validate_record(record, contract_id)
    if payload != canonical_json(checked) + b"\n":
        raise ContractError("record payload is not canonical LF-terminated JSON")
    return checked


def finish_record(record: Mapping[str, Any], contract_id: str) -> Dict[str, Any]:
    if contract_id not in CONTRACTS:
        raise ContractError("unknown contract id")
    schema, digest_key, fields = CONTRACTS[contract_id]
    value = dict(record)
    if set(value) != set(fields) or value.get("schema") != schema:
        raise ContractError(contract_id + " unfinished fields changed")
    if value.get(digest_key) is not None:
        raise ContractError(contract_id + " terminal digest must begin null")
    value[digest_key] = sha256(schema.encode("ascii") + b"\0" + canonical_json(value))
    return validate_record(value, contract_id)


def contract_catalog() -> Dict[str, Any]:
    rows = []
    for ordinal, (contract_id, (schema, digest_key, fields)) in enumerate(
        CONTRACTS.items()
    ):
        rows.append(
            {
                "ordinal": ordinal,
                "contract_id": contract_id,
                "schema": schema,
                "terminal_digest_key": digest_key,
                "field_names": list(fields),
            }
        )
    body = {
        "registration_schema": REGISTRATION_SCHEMA,
        "qualification_schema": QUALIFICATION_SCHEMA,
        "record_count": len(rows),
        "records": rows,
        "issued_record_count": 0,
    }
    return {
        **body,
        "catalog_sha256": sha256(
            b"heterodiff-a1-r1-activation-preparation-contract-catalog-v2\0"
            + canonical_json(body)
        ),
    }


__all__ = [
    "ATTEMPT_MARKER_SCHEMA",
    "ContractError",
    "LEDGER_EVENT_SCHEMA",
    "LEDGER_GENESIS_SCHEMA",
    "MILESTONE_STATE",
    "OPERATION_NONCE_CLAIM_SCHEMA",
    "QUALIFICATION_SCHEMA",
    "REGISTRATION_SCHEMA",
    "RUNTIME_CANDIDATE_SCHEMA",
    "RUNTIME_ENVELOPE_BINDING_SCHEMA",
    "RUNTIME_REQUEST_SCHEMA",
    "SOURCE_CAPSULE_ADMISSION_SCHEMA",
    "SOURCE_CAPSULE_MANIFEST_SCHEMA",
    "canonical_json",
    "contract_catalog",
    "finish_record",
    "parse_record",
    "require_sha256",
    "sha256",
    "validate_record",
]
