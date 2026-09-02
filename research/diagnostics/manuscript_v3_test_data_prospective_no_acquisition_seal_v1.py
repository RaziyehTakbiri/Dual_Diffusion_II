"""Read-only validator for the prospective no-test-data-acquisition seal.

The validator opens only a closed roster of governance and registration files.
It has no data-discovery, writer, subprocess, network, connector, entropy,
runtime, training, production, or scientific route.  Its guarantees are
procedural on an honest host, not malicious-host resistance.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, Mapping, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = (
    "heterodiff-manuscript-v3-test-data-prospective-no-acquisition-seal-v1"
)
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "NO_TEST_DATA_ACQUIRED_USER_REPORTED_PROSPECTIVE_SEAL_ACTIVE"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
VIOLATION_STATE = "PROSPECTIVE_TEST_DATA_SEAL_VIOLATION_TERMINAL"

HUMAN_PATH = "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py"
)
TRACKER_PATH = "PROJECT_COMPLETION_TIMETABLE.md"
LEDGER_PATH = "PROJECT_EVIDENCE_LEDGER.md"
PREREGISTRATION_PATH = (
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
)
CLOSURE_PATH = (
    "research/fixtures/"
    "manuscript_v3_execution_preregistration_preexecution_closure_v2.json"
)

NORMALIZED_ITEM_5 = (
    "5- What are the canonical test-data locations, or has test data not yet "
    "been acquired? No test has been acquired. For what purpose de we need it "
    "at all?"
)
NORMALIZED_ANSWER = (
    "No test has been acquired. For what purpose de we need it at all?"
)
RESOLVED_PRE_D1_POINTERS = (
    "/theory_and_known_law_plan/a1_fixture_parameters",
    "/theory_and_known_law_plan/a1_evaluation_grid",
)
DEFERRED_POSTEXECUTION_POINTERS = (
    "/ethics_release_and_review_plan/clean_room_reproduction_audit_plan",
    "/ethics_release_and_review_plan/code_model_and_artifact_release_plan",
    "/ethics_release_and_review_plan/methods_and_statistics_audit_plan",
    "/ethics_release_and_review_plan/proof_and_code_audit_artifact_path",
    "/ethics_release_and_review_plan/proof_and_code_audit_plan",
    "/ethics_release_and_review_plan/submission_anonymization_plan",
)

SOURCE_BINDINGS: Tuple[Mapping[str, Any], ...] = (
    {
        "ordinal": 0,
        "role": "EXECUTION_PREREGISTRATION",
        "path": PREREGISTRATION_PATH,
        "bytes": 39771,
        "lf_count": 909,
        "terminal_lf": True,
        "raw_sha256": (
            "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706"
        ),
    },
    {
        "ordinal": 1,
        "role": "PREEXECUTION_CLOSURE_V2",
        "path": CLOSURE_PATH,
        "bytes": 24571,
        "lf_count": 1,
        "terminal_lf": True,
        "raw_sha256": (
            "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db"
        ),
        "record_sha256": (
            "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4"
        ),
    },
)

HUMAN_BINDING: Mapping[str, Any] = {
    "ordinal": 0,
    "role": "HUMAN_SEAL",
    "path": HUMAN_PATH,
    "bytes": 7078,
    "lf_count": 129,
    "terminal_lf": True,
    "raw_sha256": (
        "ad58c5fcb9d47531a7af041eb59f71386fd42a81b1fe31701df167f064f951c2"
    ),
}
TEST_BINDING: Mapping[str, Any] = {
    "ordinal": 2,
    "role": "HOSTILE_TEST",
    "path": TEST_PATH,
    "bytes": 16698,
    "lf_count": 453,
    "terminal_lf": True,
    "raw_sha256": (
        "2285525223f42154553a0302bb46a8f04f0ff7ff35233906a37f4f1a9bf47403"
    ),
}

CLOSED_FILE_ROSTER: Tuple[str, ...] = (
    HUMAN_PATH,
    MACHINE_PATH,
    VALIDATOR_PATH,
    TEST_PATH,
    PREREGISTRATION_PATH,
    CLOSURE_PATH,
)

EXPECTED_SEMANTICS: Mapping[str, Any] = {
    "schema_version": SCHEMA,
    "state": STATE,
    "global_state": GLOBAL_STATE,
    "seal_kind": "PROSPECTIVE_USER_REPORTED_PROCEDURAL_NONCRYPTOGRAPHIC",
    "reported_date": "2026-08-30",
    "test_data_definition": {
        "scope": (
            "SCIENTIFIC_HELD_OUT_PHYSIONET_AND_RETAIL_MATERIAL_AND_DERIVED_"
            "OUTCOMES"
        ),
        "dataset_roster": ["PHYSIONET", "RETAIL"],
        "unit_test_fixtures_in_scope": False,
        "synthetic_hostile_test_records_in_scope": False,
        "synthetic_pytest_temporary_files_in_scope": False,
        "software_test_material_changes_scientific_custody": False,
    },
    "historical_tracker_provenance": {
        "capture_context": "IMMEDIATELY_BEFORE_SEAL_CONSTRUCTION",
        "historical_provenance_only": True,
        "live_custody_validated": False,
        "future_tracker_mutation_expected": True,
        "trackers_consume_seal_one_way": True,
        "records": [
            {
                "ordinal": 0,
                "role": "COMPLETION_TRACKER_PRESEAL_RECEIPT",
                "path": TRACKER_PATH,
                "bytes": 31794,
                "raw_sha256": (
                    "a7351bdad5d067856bacc673c128cd025e0fcd44870e7d33fdb7f8b2eca4e91c"
                ),
            },
            {
                "ordinal": 1,
                "role": "EVIDENCE_LEDGER_PRESEAL_RECEIPT",
                "path": LEDGER_PATH,
                "bytes": 33723,
                "raw_sha256": (
                    "3a3ba08b8f4c0710e3d38f52132ac8df6ed537ba9a944110be51a859cfd02acb"
                ),
            },
        ],
    },
    "publication_anonymity_boundary": {
        "internal_evidence_only": True,
        "anonymous_or_public_submission_inclusion_permitted": False,
        "publication_safe_derivative_required": True,
        "raw_visible_user_text_in_public_derivative_permitted": False,
        "raw_custody_provenance_in_public_derivative_permitted": False,
        "fresh_anonymity_audit_required": True,
        "excluded_from_public_derivative": [
            "VISIBLE_USER_ITEM_5_QUESTION_AND_ANSWER",
            "VISIBLE_USER_ITEM_5_ANSWER",
            "EXACT_CONVERSATION_PROVENANCE",
            "INTERNAL_SOURCE_AND_PACKAGE_PATHS",
            "RAW_AND_RECORD_SHA256_VALUES",
            "BYTE_AND_LF_COUNTS",
            "HISTORICAL_TRACKER_PROVENANCE",
        ],
        "sanitized_scientific_custody_conclusion_only": True,
        "excluded_provenance_reconstruction_permitted": False,
    },
    "visible_user_item_5": {
        "source": "CONVERSATION_VISIBLE_TEXT",
        "normalization": (
            "ONLY_TRAILING_TRANSPORT_WHITESPACE_OR_ENTITY_UNBOUND"
        ),
        "normalized_question_and_answer": NORMALIZED_ITEM_5,
        "normalized_answer": NORMALIZED_ANSWER,
        "question_and_answer_sha256": (
            "6804008bfe65a88ee33e7ba69824d20d109dd5e2a6c3e203662222885c8a09e9"
        ),
        "answer_sha256": (
            "607374414650d66dc4e3f503911c0eb075c75d026f3359ab4ed2592e0521c917"
        ),
        "raw_transport_bytes_bound": False,
        "user_reported": True,
        "independently_verified": False,
        "cryptographic_user_authentication": False,
    },
    "custody_projection": {
        "historical_preregistration_null_count": 174,
        "projected_resolved_pre_d1_null_count": 2,
        "effective_preexecution_unresolved_null_count": 166,
        "effective_deferred_postexecution_unresolved_null_count": 6,
        "effective_unresolved_null_count": 172,
        "open_confirmatory_execution_blocker_count": 10,
        "open_submission_blocker_count": 2,
        "open_blocker_count": 12,
        "final_test_secrecy_field_id": "F172",
        "final_test_secrecy_json_pointer": (
            "/freeze_predicate/test_data_unopened_before_freeze"
        ),
        "final_test_secrecy_predicate": None,
        "seal_resolves_final_test_secrecy_predicate": False,
        "unresolved_fields_closed_by_seal": 0,
        "blockers_closed_by_seal": 0,
    },
    "observation_boundary": {
        "locations_known": False,
        "canonical_test_data_locations": [],
        "hashes_known": False,
        "canonical_test_data_raw_sha256": [],
        "byte_counts_known": False,
        "canonical_test_data_bytes": [],
        "user_report_only": True,
        "independent_observation_performed": False,
        "workspace_data_scan_performed": False,
        "filesystem_data_scan_performed": False,
        "test_data_acquisition_performed": False,
        "test_data_opening_performed": False,
        "network_access_performed": False,
        "connector_contact_performed": False,
        "global_absence_claimed": False,
        "filesystem_absence_claimed": False,
        "cache_absence_claimed": False,
        "network_absence_claimed": False,
        "account_absence_claimed": False,
        "remote_service_absence_claimed": False,
        "preexisting_local_or_external_state_attested": False,
    },
    "protected_future_test_data": {
        "dataset_roster": ["PHYSIONET", "RETAIL"],
        "partition_scope": "HELD_OUT_TEST_PARTITIONS",
        "protected_material": [
            "HELD_OUT_INPUT_CONTENT",
            "LABELS_TARGETS_AND_EVENT_VALUES",
            "PREDICTIONS_AND_PER_EXAMPLE_LOSSES",
            "AGGREGATE_METRICS_AND_DIAGNOSTICS",
            "DECISION_STATISTICS_AND_OUTCOMES",
        ],
        "development_exposure_before_final_opening_permitted": False,
        "model_selection_exposure_before_final_opening_permitted": False,
        "tuning_exposure_before_final_opening_permitted": False,
        "held_out_outcome_access_before_final_opening_permitted": False,
    },
    "required_precontact_protocol": {
        "operational_protocol_created_by_this_seal": False,
        "contact_or_access_authorized_by_this_seal": False,
        "must_be_frozen_and_authorized_before_any_source_contact": True,
        "content_addressed_review_required": True,
        "required_order": [
            "FREEZE_AND_AUTHORIZE_PROTOCOL",
            "CONTACT_AND_ACQUIRE_AUTHORIZED_SOURCE",
            "FIX_CONTENT_ADDRESSED_SNAPSHOT",
            "DETERMINISTICALLY_ASSIGN_PARTITIONS_BEFORE_DEVELOPMENT_EXPOSURE",
            "ESCROW_HELD_OUT_PARTITIONS_AND_OUTCOMES",
            "RECORD_EVERY_CONTACT_AND_ACCESS_EVENT",
            "OPEN_ONLY_AFTER_FINAL_SEALED_FREEZE_AUTHORIZATION",
        ],
        "required_fields": [
            "CANONICAL_SOURCE_AND_VERSION",
            "LICENSE_AND_GOVERNANCE_APPROVALS",
            "ACQUISITION_IDENTITY_AND_CUSTODY",
            "SNAPSHOT_HASHES_AND_BYTE_COUNTS",
            "DETERMINISTIC_SPLIT_ALGORITHM_AND_ALL_INPUTS",
            "GROUP_AND_LEAKAGE_CONSTRAINTS",
            "ESCROW_IDENTITIES_AND_ACCESS_CONTROLS",
            "APPEND_ONLY_ACCESS_LOG_SCHEMA",
            "TERMINAL_VIOLATION_HANDLING",
        ],
        "deterministic_split_before_development_exposure_required": True,
        "escrow_after_partition_assignment_required": True,
        "access_log_required": True,
        "logged_event_roster": [
            "SOURCE_CONTACT",
            "ATTEMPTED_ACCESS",
            "GRANTED_ACCESS",
            "DENIED_ACCESS",
            "AUTHORIZED_FINAL_OPENING",
        ],
    },
    "violation_rule": {
        "terminal_state": VIOLATION_STATE,
        "conditions": [
            "SOURCE_CONTACT_BEFORE_PROTOCOL_FREEZE_AND_AUTHORIZATION",
            "HELD_OUT_CONTENT_OR_OUTCOME_EXPOSURE_BEFORE_FINAL_OPENING",
            "UNLOGGED_CONTACT_OR_ACCESS_ATTEMPT",
        ],
        "repair_by_deletion_permitted": False,
        "repair_by_resplit_or_reacquisition_permitted": False,
        "repair_or_retry_permitted": False,
        "evidence_admission_permitted": False,
        "claim_promotion_or_submission_permitted": False,
        "separately_authorized_independent_disposition_required": True,
    },
    "authority_boundary": {
        "honest_host_procedural_only": True,
        "malicious_host_resistance_claimed": False,
        "record_self_digest_is_user_authentication": False,
        "data_scan_authorized": False,
        "test_data_acquisition_authorized": False,
        "test_data_opening_authorized": False,
        "network_access_authorized": False,
        "connector_contact_authorized": False,
        "deterministic_split_execution_authorized": False,
        "escrow_operation_authorized": False,
        "runtime_approval_authorized": False,
        "entropy_authorized": False,
        "rank_authorized": False,
        "training_authorized": False,
        "production_authorized": False,
        "scientific_execution_authorized": False,
        "claim_promotion_authorized": False,
        "submission_authorized": False,
        "retry_authorized": False,
        "scientific_project_code_imported_or_invoked": False,
    },
}


class SealValidationError(RuntimeError):
    """Raised when the closed prospective-seal registration does not validate."""


def _reject_duplicate_pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SealValidationError("duplicate-json-key:" + key)
        result[key] = value
    return result


def _parse_json(data: bytes, role: str) -> Dict[str, Any]:
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise SealValidationError(role + ":non-ascii-json") from exc
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (json.JSONDecodeError, SealValidationError) as exc:
        raise SealValidationError(role + ":invalid-json") from exc
    if not isinstance(value, dict):
        raise SealValidationError(role + ":top-level-not-object")
    return value


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def record_sha256(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return hashlib.sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload)).hexdigest()


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


def _safe_relative_path(root: Path, relative_path: str) -> Path:
    rel = Path(relative_path)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise SealValidationError("unsafe-bound-path:" + relative_path)
    return root.joinpath(*rel.parts)


def _directory_identity(path: Path, role: str) -> Tuple[int, int, int, int]:
    try:
        status = os.lstat(path)
    except OSError as exc:
        raise SealValidationError("ancestor-lstat-failed:" + role) from exc
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
        raise SealValidationError("ancestor-not-direct-directory:" + role)
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IMODE(status.st_mode),
        status.st_nlink,
    )


def _ancestor_snapshot(root: Path, relative_path: str) -> Tuple[Tuple[str, Tuple[int, int, int, int]], ...]:
    rel = Path(relative_path)
    current = root
    rows = [(".", _directory_identity(current, "."))]
    for part in rel.parts[:-1]:
        current = current / part
        rows.append((str(current.relative_to(root)), _directory_identity(current, part)))
    return tuple(rows)


def _regular_identity(status: os.stat_result) -> Tuple[int, int, int, int, int, int, int]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IMODE(status.st_mode),
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _require_regular_0644_single_link(status: os.stat_result, role: str) -> None:
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
        raise SealValidationError("not-regular:" + role)
    if stat.S_IMODE(status.st_mode) != 0o644:
        raise SealValidationError("mode-not-0644:" + role)
    if status.st_nlink != 1:
        raise SealValidationError("link-count-not-one:" + role)


def _read_regular_single_link(root: Path, relative_path: str) -> bytes:
    path = _safe_relative_path(root, relative_path)
    ancestors_before = _ancestor_snapshot(root, relative_path)
    try:
        path_before = os.lstat(path)
    except OSError as exc:
        raise SealValidationError("path-lstat-failed:" + relative_path) from exc
    _require_regular_0644_single_link(path_before, relative_path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise SealValidationError("open-failed:" + relative_path) from exc
    try:
        descriptor_before = os.fstat(descriptor)
        _require_regular_0644_single_link(descriptor_before, relative_path)
        if _regular_identity(descriptor_before) != _regular_identity(path_before):
            raise SealValidationError("preopen-path-fd-identity-mismatch:" + relative_path)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        descriptor_after = os.fstat(descriptor)
        _require_regular_0644_single_link(descriptor_after, relative_path)
        try:
            path_after = os.lstat(path)
        except OSError as exc:
            raise SealValidationError("postread-path-lstat-failed:" + relative_path) from exc
        _require_regular_0644_single_link(path_after, relative_path)
        ancestors_after = _ancestor_snapshot(root, relative_path)
    finally:
        os.close(descriptor)
    if ancestors_after != ancestors_before:
        raise SealValidationError("ancestor-path-swap:" + relative_path)
    stable_before = _regular_identity(descriptor_before)
    if _regular_identity(descriptor_after) != stable_before:
        raise SealValidationError("changed-during-read:" + relative_path)
    if _regular_identity(path_after) != stable_before:
        raise SealValidationError("postread-path-fd-identity-mismatch:" + relative_path)
    data = b"".join(chunks)
    if len(data) != descriptor_before.st_size:
        raise SealValidationError("short-read:" + relative_path)
    return data


def _binding_for(data: bytes, template: Mapping[str, Any]) -> Dict[str, Any]:
    binding: Dict[str, Any] = {
        "ordinal": template["ordinal"],
        "role": template["role"],
        "path": template["path"],
        "bytes": len(data),
        "lf_count": data.count(b"\n"),
        "terminal_lf": data.endswith(b"\n"),
        "raw_sha256": hashlib.sha256(data).hexdigest(),
    }
    if "record_sha256" in template:
        binding["record_sha256"] = template["record_sha256"]
    return binding


def _require_exact_binding(
    root: Path, expected: Mapping[str, Any]
) -> bytes:
    data = _read_regular_single_link(root, str(expected["path"]))
    observed = _binding_for(data, expected)
    if observed != dict(expected):
        raise SealValidationError("binding-mismatch:" + str(expected["role"]))
    return data


def _null_json_pointers(value: Any, pointer: str = "") -> Tuple[str, ...]:
    if value is None:
        return (pointer,)
    rows = []
    if isinstance(value, dict):
        for key, child in value.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            rows.extend(_null_json_pointers(child, pointer + "/" + token))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_null_json_pointers(child, pointer + "/" + str(index)))
    return tuple(rows)


def _json_pointer_value(value: Any, pointer: str) -> Any:
    current = value
    if not pointer.startswith("/"):
        raise SealValidationError("invalid-json-pointer:" + pointer)
    for encoded in pointer[1:].split("/"):
        token = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit():
            index = int(token)
            if index >= len(current):
                raise SealValidationError("json-pointer-index-missing:" + pointer)
            current = current[index]
        else:
            raise SealValidationError("json-pointer-missing:" + pointer)
    return current


def derive_projection(
    preregistration: Mapping[str, Any], closure: Mapping[str, Any]
) -> Dict[str, Any]:
    """Derive the effective null and blocker projection from immutable inputs."""

    historical_nulls = set(_null_json_pointers(preregistration))
    if len(historical_nulls) != 174:
        raise SealValidationError("derived-historical-null-count-not-174")

    null_projection = closure.get("null_projection")
    if not isinstance(null_projection, dict):
        raise SealValidationError("closure-null-projection-missing")
    deferred = tuple(null_projection.get("deferred_postexecution_null_paths", []))
    if deferred != DEFERRED_POSTEXECUTION_POINTERS:
        raise SealValidationError("deferred-null-pointer-roster-mismatch")
    if len(set(deferred)) != 6:
        raise SealValidationError("deferred-null-pointer-duplicates")
    for pointer in deferred:
        if pointer not in historical_nulls or _json_pointer_value(
            preregistration, pointer
        ) is not None:
            raise SealValidationError("deferred-pointer-not-historical-null:" + pointer)

    resolved_rows = closure.get("resolved_pre_d1_fields")
    if not isinstance(resolved_rows, list):
        raise SealValidationError("resolved-pre-d1-roster-missing")
    resolved = tuple(
        row.get("source_json_pointer") if isinstance(row, dict) else None
        for row in resolved_rows
    )
    if resolved != RESOLVED_PRE_D1_POINTERS:
        raise SealValidationError("resolved-pre-d1-pointer-roster-mismatch")
    for pointer in resolved:
        if pointer not in historical_nulls or _json_pointer_value(
            preregistration, pointer
        ) is not None:
            raise SealValidationError("resolved-pointer-not-historical-null:" + pointer)
    if set(resolved) & set(deferred):
        raise SealValidationError("resolved-and-deferred-pointer-overlap")

    historical_postexecution = len(deferred)
    historical_preexecution = len(historical_nulls - set(deferred))
    effective_preexecution = historical_preexecution - len(resolved)
    effective_postexecution = historical_postexecution
    effective_total = effective_preexecution + effective_postexecution
    derived_nulls = {
        "historical_total_null_count": len(historical_nulls),
        "historical_preexecution_null_count": historical_preexecution,
        "historical_deferred_postexecution_null_count": historical_postexecution,
        "projected_resolved_pre_d1_null_count": len(resolved),
        "effective_preexecution_unresolved_null_count": effective_preexecution,
        "effective_deferred_postexecution_unresolved_null_count": (
            effective_postexecution
        ),
        "effective_total_unresolved_null_count": effective_total,
    }
    for key, value in derived_nulls.items():
        if null_projection.get(key) != value:
            raise SealValidationError("closure-derived-null-mismatch:" + key)

    blocker_projection = closure.get("blocker_projection")
    if not isinstance(blocker_projection, dict):
        raise SealValidationError("closure-blocker-projection-missing")
    blocker_ids = blocker_projection.get("blocker_ids")
    if not isinstance(blocker_ids, list) or len(blocker_ids) != 12:
        raise SealValidationError("closure-blocker-roster-count-mismatch")
    if len(set(blocker_ids)) != 12:
        raise SealValidationError("closure-blocker-roster-duplicates")
    stages = blocker_projection.get("effective_stage_counts")
    expected_stage_keys = {
        "CONFIRMATORY_EXECUTION",
        "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION",
    }
    if not isinstance(stages, dict) or set(stages) != expected_stage_keys:
        raise SealValidationError("closure-blocker-stage-roster-mismatch")
    execution_blockers = stages["CONFIRMATORY_EXECUTION"]
    submission_blockers = stages[
        "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION"
    ]
    if execution_blockers != 10 or submission_blockers != 2:
        raise SealValidationError("closure-derived-blocker-stage-count-mismatch")
    if execution_blockers + submission_blockers != len(blocker_ids):
        raise SealValidationError("closure-blocker-stage-total-mismatch")
    if blocker_projection.get("effective_unresolved_blocker_count") != len(
        blocker_ids
    ):
        raise SealValidationError("closure-effective-blocker-count-mismatch")

    return {
        **derived_nulls,
        "resolved_pre_d1_pointers": list(resolved),
        "open_confirmatory_execution_blocker_count": execution_blockers,
        "open_submission_blocker_count": submission_blockers,
        "open_blocker_count": len(blocker_ids),
    }


def _validate_source_custody(
    root: Path, record: Mapping[str, Any]
) -> Dict[str, Any]:
    if record["source_bindings"] != list(SOURCE_BINDINGS):
        raise SealValidationError("source-binding-roster-mismatch")
    source_bytes = {}
    for expected in SOURCE_BINDINGS:
        source_bytes[str(expected["path"])] = _require_exact_binding(root, expected)

    preregistration = _parse_json(
        source_bytes[PREREGISTRATION_PATH], "execution-preregistration"
    )
    if preregistration.get("schema_version") != "manuscript-v3-execution-preregistration-v1":
        raise SealValidationError("preregistration-schema-mismatch")
    freeze_predicate = preregistration.get("freeze_predicate")
    if not isinstance(freeze_predicate, dict):
        raise SealValidationError("preregistration-freeze-predicate-missing")
    if freeze_predicate.get("test_data_unopened_before_freeze", object()) is not None:
        raise SealValidationError("preregistration-test-secrecy-not-null")
    if freeze_predicate.get("current_state") != GLOBAL_STATE:
        raise SealValidationError("preregistration-state-mismatch")

    closure = _parse_json(source_bytes[CLOSURE_PATH], "preexecution-closure-v2")
    if closure.get("schema_version") != (
        "heterodiff-manuscript-v3-execution-preregistration-preexecution-closure-v2"
    ):
        raise SealValidationError("closure-schema-mismatch")
    if closure.get("record_sha256") != SOURCE_BINDINGS[1]["record_sha256"]:
        raise SealValidationError("closure-record-digest-mismatch")
    if closure.get("global_state") != GLOBAL_STATE:
        raise SealValidationError("closure-state-mismatch")
    predicate_projection = closure.get("freeze_predicate_projection")
    if not isinstance(predicate_projection, dict):
        raise SealValidationError("closure-freeze-predicate-projection-missing")
    effective = predicate_projection.get("effective_predicate")
    if not isinstance(effective, dict):
        raise SealValidationError("closure-effective-predicate-missing")
    if effective.get("test_data_unopened_before_freeze", object()) is not None:
        raise SealValidationError("closure-test-secrecy-not-null")
    derived = derive_projection(preregistration, closure)
    custody = record["custody_projection"]
    expected_projection = {
        "historical_preregistration_null_count": derived[
            "historical_total_null_count"
        ],
        "projected_resolved_pre_d1_null_count": derived[
            "projected_resolved_pre_d1_null_count"
        ],
        "effective_preexecution_unresolved_null_count": derived[
            "effective_preexecution_unresolved_null_count"
        ],
        "effective_deferred_postexecution_unresolved_null_count": derived[
            "effective_deferred_postexecution_unresolved_null_count"
        ],
        "effective_unresolved_null_count": derived[
            "effective_total_unresolved_null_count"
        ],
        "open_confirmatory_execution_blocker_count": derived[
            "open_confirmatory_execution_blocker_count"
        ],
        "open_submission_blocker_count": derived[
            "open_submission_blocker_count"
        ],
        "open_blocker_count": derived["open_blocker_count"],
    }
    for key, value in expected_projection.items():
        if custody.get(key) != value:
            raise SealValidationError("machine-derived-projection-mismatch:" + key)
    return derived


def _validate_package_custody(
    root: Path, record: Mapping[str, Any]
) -> None:
    rows = record["package_bindings"]
    if not isinstance(rows, list) or len(rows) != 3:
        raise SealValidationError("package-binding-roster-mismatch")
    if rows[0] != dict(HUMAN_BINDING) or rows[2] != dict(TEST_BINDING):
        raise SealValidationError("fixed-package-binding-mismatch")
    expected_validator_shape = {
        "ordinal": 1,
        "role": "READ_ONLY_VALIDATOR",
        "path": VALIDATOR_PATH,
    }
    validator_row = rows[1]
    if not isinstance(validator_row, dict):
        raise SealValidationError("validator-binding-not-object")
    for key, value in expected_validator_shape.items():
        if validator_row.get(key) != value:
            raise SealValidationError("validator-binding-shape-mismatch")
    if set(validator_row) != {
        "ordinal",
        "role",
        "path",
        "bytes",
        "lf_count",
        "terminal_lf",
        "raw_sha256",
    }:
        raise SealValidationError("validator-binding-key-mismatch")
    _require_exact_binding(root, HUMAN_BINDING)
    _require_exact_binding(root, validator_row)
    _require_exact_binding(root, TEST_BINDING)


def _validate_semantics(record: Mapping[str, Any]) -> None:
    expected_keys = set(EXPECTED_SEMANTICS) | {
        "record_sha256",
        "source_bindings",
        "package_bindings",
    }
    if set(record) != expected_keys:
        raise SealValidationError("top-level-key-roster-mismatch")
    for key, expected in EXPECTED_SEMANTICS.items():
        if record.get(key) != expected:
            raise SealValidationError("semantic-mismatch:" + key)
    if not isinstance(record.get("record_sha256"), str):
        raise SealValidationError("record-digest-not-string")
    if record["record_sha256"] != record_sha256(record):
        raise SealValidationError("record-self-digest-mismatch")


def validate(workspace_root: Path | str = WORKSPACE_ROOT) -> Dict[str, Any]:
    """Validate the closed seal package without writing or discovering data."""

    root = Path(os.path.abspath(os.fspath(workspace_root)))
    machine_bytes = _read_regular_single_link(root, MACHINE_PATH)
    record = _parse_json(machine_bytes, "machine-seal")
    if machine_bytes != canonical_machine_bytes(record):
        raise SealValidationError("machine-serialization-not-canonical")
    _validate_semantics(record)
    derived = _validate_source_custody(root, record)
    _validate_package_custody(root, record)
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "effective_unresolved_null_count": derived[
            "effective_total_unresolved_null_count"
        ],
        "open_blocker_count": derived["open_blocker_count"],
        "final_test_secrecy_predicate": None,
        "user_reported": True,
        "independently_verified": False,
        "internal_evidence_only": True,
        "anonymous_or_public_submission_inclusion_permitted": False,
        "publication_safe_derivative_required": True,
        "validation": "PASS",
    }


def main() -> int:
    print(
        json.dumps(
            validate(), ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
