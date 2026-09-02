#!/usr/bin/env python3
"""Read-only validation for the B08 three-field capacity-gap package."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = "heterodiff-manuscript-v3-b08-local-host-capacity-gap-v1"
STATE = "B08_LOCAL_HOST_PARTIAL_POLICY_FREEZE_CAPACITY_NO_GO"
CONTROL_PREDICATE = "B08_THREE_LOCALLY_DEFENSIBLE_FIELDS_FROZEN_CAPACITY_HOLD"
PACKAGE_KIND = "ADDITIVE_PREOUTCOME_THREE_FIELD_B08_POLICY_FREEZE_WITH_EXACT_RESIDUAL_GAP"
MACHINE_PATH = "research/fixtures/manuscript_v3_b08_local_host_capacity_gap_freeze_v1.json"
HUMAN_PATH = "PROJECT_B08_LOCAL_HOST_CAPACITY_GAP_FREEZE.md"
SOURCE_PATH = "src/heterodiff/experiments/b08_local_host_capacity_gap.py"
VALIDATOR_PATH = "research/diagnostics/manuscript_v3_b08_local_host_capacity_gap_freeze_v1.py"
TEST_PATH = "tests/unit/test_manuscript_v3_b08_local_host_capacity_gap_freeze_v1.py"
PACKAGE_ROSTER = [HUMAN_PATH, SOURCE_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH]

EXPECTED_HUMAN_SHA256 = "66b0f9796eb2da7038a4aca7cbadfc449fc1af1eae542601007f7a589c6436e0"
EXPECTED_SOURCE_SHA256 = "347f2de3008af8df679faad1b275179e6a6b788977d744919f880c58383af499"
EXPECTED_TEST_SHA256 = "660a70eb5a15c57d8b4ed835c9d670d954b399b450fc50f6abbdc7353ad74da5"
EXPECTED_PROJECTION_SHA256 = "fa9aa9824029a1aa5053de8dd545b6965f56a9d28e3e63920c2f7b7b1778197e"
EXPECTED_HARDWARE_PROFILE_SHA256 = "b3de65a7efc4ba62a7da509ae030515d15d431a090a620f3774cf6d8dc6de041"
EXPECTED_ENVIRONMENT_SHA256 = "84b5b293a5d8378332499aa3ee0641a1ab833549e08f373fad56f7421d54e837"
EXPECTED_SHA_CALIBRATION_SHA256 = "cba6f72870b436c503e5803a1f53f06380653aaac096233a290e995722871a22"
EXPECTED_TORCH_CALIBRATION_SHA256 = "4147a2f835bc687ee8f6a3b16b66ce89320d9ba95275a798f1186e9630be72fb"

EXPECTED_PREDECESSOR_SHA256 = {
    "manuscript_v3/execution_preregistration.md": "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json": "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
    "manuscript_v3/execution_preregistration_preexecution_closure_v2.md": "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d",
    "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json": "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
    "PROJECT_ANTI_DRIFT_OPERATING_POLICY.md": "22f1006bfd0b4dde8eb51e6e30abd7b153882a3fd41d6f3a3494ffd98a98bbd3",
    "PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md": "4d73909714e5227175b8c0f250876ffeddcd25ad9cc4d54b27d02499c562edfb",
    "research/fixtures/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json": "c6275a6fb6941b28c2b0ed89196efdfeeba5530d8cabe47f173452cda364af54",
    "PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE_INDEPENDENT_REVIEW.md": "7694694d7fe2b0c2dd17f79b9e0f9d2f44c14c59c3f0568902e3cad7d75ae402",
    "PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE.md": "6a10a546a70d43aa71cb878e72ba09c24be949cd932e1cdf5becdeb732fa816a",
    "research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json": "b789b4b39aef1cef3134dddee506409f311b79cc70b1d121daa0a2ff22267f21",
    "PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE_INDEPENDENT_REVIEW.md": "a0aa207a0a68545d0af7ba5e252d7c30f1349d799e0e61ebf807c2426ee22209",
    "PROJECT_GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISION_FREEZE.md": "ca9a593c54a9d3587f58a3d414defd5cf81a3765395d5ebb8494e6effa6dd44d",
    "research/fixtures/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json": "b8a74f1131f85aa1b7497f2f43bd34a0e30bc471953c935d4362a5a8dea1446a",
    "PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE.md": "bb4438887f54710b0445e0b713ee086abc2523b2bf34b4a08d42ee586515d721",
    "research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json": "2ff92ac1b4b6df75931791cd16ce7ade461c70b29042a17486bc2804f35295f1",
    "PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE_INDEPENDENT_REVIEW.md": "ede11cff876c96cafe5734cee59ffae347b001dc8e16c3b3b71437d6cb4a0b64",
    "PROJECT_F061_PRESERVATION_FIRST_ALLOCATION_PROPOSAL.md": "2769df9d8da86b054857973b7025c03f6932e88fa683848171dd32af507ec052",
    "research/fixtures/manuscript_v3_f061_preservation_first_allocation_proposal_v1.json": "4a6414b494328a7f7cd4030718af960764bb2ce1946fb7de093985983e725d32",
    "research/fixtures/manuscript_v3_f061_guarded_power_review_receipt_v1.json": "906b12b78400cba6bc2b32527a1410c6d42f154bbad0775591d69ada7485668d",
    "PROJECT_F061_PRESERVATION_FIRST_ALLOCATION_INDEPENDENT_REVIEW.md": "053de959f3fffabf0da21a4c9e997b96e170f1fbc4b9295d71fef8e8347835eb",
}

PREDECESSOR_GROUP_ROLE = {
    "manuscript_v3/execution_preregistration.md": ("EXECUTION_PREREGISTRATION", "human"),
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json": ("EXECUTION_PREREGISTRATION", "machine"),
    "manuscript_v3/execution_preregistration_preexecution_closure_v2.md": ("PREEXECUTION_CLOSURE_V2", "human"),
    "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json": ("PREEXECUTION_CLOSURE_V2", "machine"),
    "PROJECT_ANTI_DRIFT_OPERATING_POLICY.md": ("ANTI_DRIFT_POLICY", "policy"),
    "PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md": ("ACCEPTED_F104", "human"),
    "research/fixtures/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json": ("ACCEPTED_F104", "machine"),
    "PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE_INDEPENDENT_REVIEW.md": ("ACCEPTED_F104", "independent_review"),
    "PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE.md": ("ACCEPTED_B06", "human"),
    "research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json": ("ACCEPTED_B06", "machine"),
    "PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE_INDEPENDENT_REVIEW.md": ("ACCEPTED_B06", "independent_review"),
    "PROJECT_GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISION_FREEZE.md": ("ACCEPTED_GATE_A_LOCAL", "human"),
    "research/fixtures/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json": ("ACCEPTED_GATE_A_LOCAL", "machine"),
    "PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE.md": ("ACCEPTED_THEORY_STATISTICS", "human"),
    "research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json": ("ACCEPTED_THEORY_STATISTICS", "machine"),
    "PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE_INDEPENDENT_REVIEW.md": ("ACCEPTED_THEORY_STATISTICS", "independent_review"),
    "PROJECT_F061_PRESERVATION_FIRST_ALLOCATION_PROPOSAL.md": ("ACCEPTED_F061_COUNT_ANCHOR", "human"),
    "research/fixtures/manuscript_v3_f061_preservation_first_allocation_proposal_v1.json": ("ACCEPTED_F061_COUNT_ANCHOR", "machine"),
    "research/fixtures/manuscript_v3_f061_guarded_power_review_receipt_v1.json": ("ACCEPTED_F061_COUNT_ANCHOR", "guarded_receipt"),
    "PROJECT_F061_PRESERVATION_FIRST_ALLOCATION_INDEPENDENT_REVIEW.md": ("ACCEPTED_F061_COUNT_ANCHOR", "independent_review"),
}

EXPECTED_FIELD_DELTA = {
    "blocker_ids": [],
    "blockers_closed": 0,
    "field_ids": ["F153", "F158", "F161"],
    "post_execution": 0,
    "pre_execution": 3,
    "total": 3,
}
EXPECTED_COUNT_TRANSITION = {
    "after": {
        "post_execution_closed": 5,
        "post_execution_open": 1,
        "pre_execution_closed": 136,
        "pre_execution_open": 30,
        "total_closed": 141,
        "total_open": 31,
    },
    "before": {
        "post_execution_closed": 5,
        "post_execution_open": 1,
        "pre_execution_closed": 133,
        "pre_execution_open": 33,
        "total_closed": 138,
        "total_open": 34,
    },
}
EXPECTED_WORKSTREAM_TRANSITION = {
    "after": {"closed": 48, "open": 17},
    "before": {"closed": 45, "open": 20},
    "workstream": "Method, runtime, and compute",
}
EXPECTED_BLOCKER_TRANSITION = {
    "after": {"closed": 5, "execution_open": 5, "open": 7},
    "before": {"closed": 5, "execution_open": 5, "open": 7},
    "closed_now": [],
    "remaining_open": ["B02", "B03", "B08", "B09", "B10", "B11", "B12"],
}
EXPECTED_GATE_A_TRANSITION = {
    "after": {"closed": 5, "open": 3, "total": 8},
    "before": {"closed": 5, "open": 3, "total": 8},
    "hardware_capacity_item_closed": False,
}
EXPECTED_AUTHORITY_BOUNDARY = {
    "data_test_access_training_inference_or_science_authorized": False,
    "entropy_authorized": False,
    "external_contact_network_or_repository_action_authorized": False,
    "external_execution_or_compute_purchase_authorized": False,
    "hardware_or_storage_reservation_authorized_or_performed": False,
    "offline_local_construction_and_synthetic_qualification_authorized": True,
    "tracker_or_evidence_ledger_edit_authorized_by_package": False,
}
EXPECTED_PROJECT_EFFECTS = {
    "B08_closed": False,
    "B12_closed": False,
    "capacity_reservation_or_resource_receipt_created": False,
    "data_entropy_training_inference_or_science_performed": False,
    "f104_calibration_weight_or_scalar_hard_axis_value_created": False,
    "fields_closed_only_after_independent_acceptance": ["F153", "F158", "F161"],
    "formal_test_28_status": "OPEN",
    "formal_test_29_status": "OPEN",
    "formal_test_30_status": "PENDING",
    "gate_a_capacity_closed": False,
    "hardware_or_production_runtime_selected": False,
    "only_proposed_field_closures": ["F153", "F158", "F161"],
    "result_claim_release_or_submission_created": False,
    "tracker_or_evidence_ledger_edited": False,
}
EXPECTED_QUALIFICATION_BOUNDARY = {
    "candidate_source_executed_by_validator": False,
    "canonical_duplicate_free_ascii_json_required": True,
    "hostile_mutations_use_disposable_copies_only": True,
    "independent_review_required_before_registration": True,
    "production_capacity_or_determinism_inferred_from_synthetic_receipts": False,
    "read_only_stable_no_follow_validator": True,
    "self_review_or_self_acceptance": False,
    "source_is_pure_standard_library_policy": True,
}
EXPECTED_REGISTRATION = {
    "conditional_on_independent_acceptance": True,
    "permitted_blocker_delta": [],
    "permitted_field_delta": ["F153", "F158", "F161"],
    "registration_performed_by_this_package": False,
}
EXPECTED_SEMANTIC_BINDINGS = {
    "b06_semantic_sha256": "aa3ab6c8cb05287304da321f2d5b4892b94d4483860d830a3e724c339b2809bd",
    "f061_guarded_receipt_sha256": "906b12b78400cba6bc2b32527a1410c6d42f154bbad0775591d69ada7485668d",
    "f104_semantic_sha256": "ba1c3a7898c858ec7cf7b3073c869a134cd8a06b93aeb0f7778793c271c96d7b",
    "gate_a_local_semantic_sha256": "aa3fe845190d6c74472706749598ba245de1925ce03a5702d1d2eed81a88bffa",
    "preexecution_closure_v2_semantic_sha256": "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4",
    "theory_statistics_semantic_sha256": "335879da927b14de0f2ab0cb69b531ea51f24d9734777cb33cdf1e90fb81a491",
}

MAXIMUM_FILE_BYTES = 64 * 1024 * 1024
_HEX_DIGITS = frozenset("0123456789abcdef")


class ValidationError(RuntimeError):
    pass


def canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        raise ValidationError("value is not finite canonical JSON") from error


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _reject_duplicate_pairs(pairs: Sequence[Tuple[str, object]]) -> dict:
    result: Dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def decode_canonical_json_file(
    payload: bytes, *, terminal_lf: bool = True, canonical_required: bool = True
) -> dict:
    if type(payload) is not bytes or not payload or len(payload) > MAXIMUM_FILE_BYTES:
        raise ValidationError("invalid JSON file byte length")
    if terminal_lf:
        if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
            raise ValidationError("JSON file must have exactly one terminal LF")
        body = payload[:-1]
    else:
        if payload.endswith(b"\n"):
            raise ValidationError("JSON file must not have a terminal LF")
        body = payload
    try:
        value = json.loads(
            body.decode("ascii"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValidationError("non-finite JSON constant: " + token)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValidationError("invalid canonical JSON") from error
    if type(value) is not dict:
        raise ValidationError("JSON file is not an object")
    if canonical_required and body != canonical_json_bytes(value):
        raise ValidationError("JSON file is not a canonical ASCII object")
    return value


def _relative_path(value: object) -> str:
    if type(value) is not str or not value or len(value) > 8192 or "\x00" in value:
        raise ValidationError("invalid relative path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value or any(part in (".", "..") for part in pure.parts):
        raise ValidationError("path is not a canonical relative POSIX path")
    return value


def _fingerprint(metadata: os.stat_result) -> Tuple[int, int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
        metadata.st_mode,
        metadata.st_nlink,
    )


def stable_read(root: Path, relative_path: str) -> Tuple[bytes, os.stat_result]:
    relative = _relative_path(relative_path)
    base = Path(root)
    if not base.is_absolute():
        raise ValidationError("project root must be absolute")
    root_before = os.lstat(base)
    if not stat.S_ISDIR(root_before.st_mode) or stat.S_ISLNK(root_before.st_mode):
        raise ValidationError("project root must be a real directory")
    current = base
    parts = PurePosixPath(relative).parts
    for part in parts[:-1]:
        current = current / part
        metadata = os.lstat(current)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValidationError("path ancestor is not a real directory")
    path = base / relative
    before = os.lstat(path)
    if (
        not stat.S_ISREG(before.st_mode)
        or stat.S_ISLNK(before.st_mode)
        or before.st_nlink != 1
        or stat.S_IMODE(before.st_mode) != 0o644
        or before.st_size > MAXIMUM_FILE_BYTES
    ):
        raise ValidationError("file custody predicate failed: " + relative)
    descriptor = os.open(os.fspath(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        if _fingerprint(opened) != _fingerprint(before):
            raise ValidationError("file changed while opening: " + relative)
        chunks: List[bytes] = []
        consumed = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, MAXIMUM_FILE_BYTES + 1 - consumed))
            if not chunk:
                break
            chunks.append(chunk)
            consumed += len(chunk)
            if consumed > MAXIMUM_FILE_BYTES:
                raise ValidationError("file exceeds read bound: " + relative)
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = os.lstat(path)
    root_after = os.lstat(base)
    if (
        _fingerprint(before) != _fingerprint(after_descriptor)
        or _fingerprint(before) != _fingerprint(after_path)
        or _fingerprint(root_before) != _fingerprint(root_after)
    ):
        raise ValidationError("file changed during read: " + relative)
    payload = b"".join(chunks)
    if len(payload) != before.st_size:
        raise ValidationError("file read size mismatch: " + relative)
    return payload, before


def file_binding(root: Path, path: str, *, group: str, role: str, ordinal: int) -> dict:
    payload, metadata = stable_read(root, path)
    return {
        "bytes": len(payload),
        "group": group,
        "mode_octal": "%04o" % stat.S_IMODE(metadata.st_mode),
        "nlink": metadata.st_nlink,
        "ordinal": ordinal,
        "path": path,
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "role": role,
        "terminal_lf": payload.endswith(b"\n"),
    }


def predecessor_bindings(root: Path) -> List[dict]:
    rows = []
    for ordinal, path in enumerate(EXPECTED_PREDECESSOR_SHA256):
        group, role = PREDECESSOR_GROUP_ROLE[path]
        row = file_binding(root, path, group=group, role=role, ordinal=ordinal)
        if row["raw_sha256"] != EXPECTED_PREDECESSOR_SHA256[path]:
            raise ValidationError("accepted predecessor hash drift: " + path)
        rows.append(row)
    return rows


def package_bindings(root: Path) -> List[dict]:
    roles = {
        HUMAN_PATH: "human",
        SOURCE_PATH: "source",
        VALIDATOR_PATH: "validator",
        TEST_PATH: "test",
    }
    rows = []
    for ordinal, path in enumerate((HUMAN_PATH, SOURCE_PATH, VALIDATOR_PATH, TEST_PATH)):
        rows.append(file_binding(root, path, group="CURRENT_PACKAGE", role=roles[path], ordinal=ordinal))
    return rows


def package_aggregate_sha256(bindings: object) -> str:
    return hashlib.sha256(
        b"heterodiff-b08-local-host-capacity-gap-package-v1\0"
        + canonical_json_bytes(bindings)
    ).hexdigest()


def _record_digest(record: Mapping[str, object]) -> str:
    body = dict(record)
    body.pop("record_sha256", None)
    return sha256_json(body)


def build_candidate_record(root: Path, supported_projection: object) -> dict:
    projection_digest = sha256_json(supported_projection)
    if projection_digest != EXPECTED_PROJECTION_SHA256:
        raise ValidationError("candidate projection differs from frozen digest")
    bindings = package_bindings(root)
    record = {
        "accepted_predecessor_bindings": predecessor_bindings(root),
        "accepted_semantic_bindings": dict(EXPECTED_SEMANTIC_BINDINGS),
        "authority_boundary": dict(EXPECTED_AUTHORITY_BOUNDARY),
        "blocker_transition": dict(EXPECTED_BLOCKER_TRANSITION),
        "control_predicate": CONTROL_PREDICATE,
        "count_transition": dict(EXPECTED_COUNT_TRANSITION),
        "evidence_ready_registration": dict(EXPECTED_REGISTRATION),
        "field_delta": dict(EXPECTED_FIELD_DELTA),
        "gate_a_transition": dict(EXPECTED_GATE_A_TRANSITION),
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "machine_self_binding": {
            "path": MACHINE_PATH,
            "raw_self_hash_embedded": False,
            "semantic_self_digest_field": "record_sha256",
        },
        "package_aggregate_sha256": package_aggregate_sha256(bindings),
        "package_bindings_excluding_machine_self": bindings,
        "package_file_roster": list(PACKAGE_ROSTER),
        "package_kind": PACKAGE_KIND,
        "project_effects_and_nonclaims": dict(EXPECTED_PROJECT_EFFECTS),
        "qualification_boundary": dict(EXPECTED_QUALIFICATION_BOUNDARY),
        "reported_date": "2026-09-01",
        "schema_version": SCHEMA_VERSION,
        "state": STATE,
        "supported_projection": supported_projection,
        "supported_projection_sha256": projection_digest,
        "workstream_transition": dict(EXPECTED_WORKSTREAM_TRANSITION),
    }
    record["record_sha256"] = _record_digest(record)
    return record


def _validate_exact_receipt_digest(receipt: object, expected: str, *, name: str) -> None:
    if type(receipt) is not dict or type(receipt.get("receipt_sha256")) is not str:
        raise ValidationError(name + " schema is invalid")
    body = dict(receipt)
    digest = body.pop("receipt_sha256")
    if digest != sha256_json(body) or digest != expected:
        raise ValidationError(name + " self digest differs")


def _validate_projection(projection: object) -> None:
    if type(projection) is not dict or sha256_json(projection) != EXPECTED_PROJECTION_SHA256:
        raise ValidationError("supported projection digest differs")
    exact_keys = {
        "capacity_gate",
        "field_closures",
        "hardware_observation",
        "residual_gaps",
        "sha256_calibration_receipt",
        "software_environment_observation",
        "storage_observation",
        "torch_calibration_receipt",
    }
    if set(projection) != exact_keys:
        raise ValidationError("supported projection schema differs")
    closures = projection["field_closures"]
    if type(closures) is not list or [row.get("field_id") for row in closures] != ["F153", "F158", "F161"]:
        raise ValidationError("field closure roster differs")
    residuals = projection["residual_gaps"]
    if type(residuals) is not list or [row.get("field_id") for row in residuals] != [
        "F150", "F151", "F152", "F154", "F155", "F156", "F157", "F159", "F160", "F162"
    ]:
        raise ValidationError("residual field roster differs")
    gate = projection["capacity_gate"]
    if (
        type(gate) is not dict
        or gate.get("B08_close_permitted") is not False
        or [row.get("requirement_id") for row in gate.get("requirements", [])]
        != [
            "HARDWARE_AND_RUNTIME_IDENTITY",
            "CALIBRATION_WEIGHTS",
            "SCALAR_AND_HARD_AXIS_CEILING_VALUES",
            "CAPACITY_RESERVATION_RECEIPT",
        ]
        or any(row.get("satisfied") is not False for row in gate.get("requirements", []))
        or gate.get("terminal_disposition") != "B08_REMAINS_OPEN_CAPACITY_NO_GO"
    ):
        raise ValidationError("capacity gate differs")
    hardware = projection["hardware_observation"]
    if (
        hardware.get("hardware_public_profile_sha256") != EXPECTED_HARDWARE_PROFILE_SHA256
        or hardware.get("production_hardware_selected") is not False
        or hardware.get("production_hardware_reserved") is not False
        or hardware.get("private_identifiers_recorded_in_package") is not False
    ):
        raise ValidationError("hardware observation overclaims")
    environment = projection["software_environment_observation"]
    if (
        environment.get("software_environment_observation_sha256") != EXPECTED_ENVIRONMENT_SHA256
        or environment.get("production_environment_selected") is not False
        or environment.get("complete_b12_runtime_present") is not False
        or environment.get("external_baseline_runtime_dependencies_complete") is not False
    ):
        raise ValidationError("environment observation overclaims")
    storage = projection["storage_observation"]
    if (
        storage.get("reservation_created") is not False
        or storage.get("persistent_bytes_reserved") != 0
        or storage.get("production_capacity_receipt") is not False
    ):
        raise ValidationError("storage observation overclaims")
    _validate_exact_receipt_digest(
        projection["sha256_calibration_receipt"],
        EXPECTED_SHA_CALIBRATION_SHA256,
        name="SHA calibration receipt",
    )
    _validate_exact_receipt_digest(
        projection["torch_calibration_receipt"],
        EXPECTED_TORCH_CALIBRATION_SHA256,
        name="torch calibration receipt",
    )


def _load_json_predecessor(root: Path, path: str, *, terminal_lf: bool = True) -> dict:
    payload, _ = stable_read(root, path)
    return decode_canonical_json_file(
        payload, terminal_lf=terminal_lf, canonical_required=False
    )


def _validate_predecessor_semantics(root: Path) -> None:
    prereg = _load_json_predecessor(root, "research/fixtures/manuscript_v3_execution_preregistration_v1.json")
    plan = prereg.get("compute_and_fairness_plan")
    expected_fields = [
        "hardware", "software_environment_sha256", "container_or_lockfile_sha256", "deterministic_settings",
        "per_run_wall_time_ceiling", "per_run_accelerator_hour_ceiling", "per_run_peak_memory_ceiling",
        "per_run_model_evaluation_ceiling", "pilot_compute_allocation", "tuning_compute_allocation",
        "final_compute_allocation", "failure_reserve", "total_compute_ceiling",
    ]
    if type(plan) is not dict or any(plan.get(name) is not None for name in expected_fields):
        raise ValidationError("base B08 fields are not all null")
    if (
        plan.get("primary_training_and_inference_compute_matched") is not True
        or plan.get("realized_compute_report_required") is not True
        or plan.get("post_result_compute_topup_permitted") is not False
        or prereg.get("cp75_style_external_reviewer_appointment_or_signature_required") is not False
    ):
        raise ValidationError("base compute/fairness policy differs")
    blockers = [row for row in prereg.get("unresolved_blockers", []) if row.get("blocker_id") == "hardware-compute-and-tuning-budget"]
    if len(blockers) != 1 or blockers[0].get("owner") != "USER_RESOURCE_DECISION":
        raise ValidationError("base B08 blocker definition differs")

    closure = _load_json_predecessor(root, "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json")
    if closure.get("record_sha256") != EXPECTED_SEMANTIC_BINDINGS["preexecution_closure_v2_semantic_sha256"]:
        raise ValidationError("preexecution closure semantic digest differs")

    f104 = _load_json_predecessor(root, "research/fixtures/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json")
    if f104.get("record_sha256") != EXPECTED_SEMANTIC_BINDINGS["f104_semantic_sha256"]:
        raise ValidationError("F104 semantic digest differs")
    value = f104.get("field_closures", [{}])[0].get("value", {})
    if (
        value.get("calculator_id") != "EXACT_WEIGHTED_RESOURCE_LEDGER_V1"
        or value.get("hardware_calibration_weights_populated") is not False
        or value.get("scalar_cost_sufficient_without_hard_axis_ceilings") is not False
        or value.get("unused_budget_transfer_or_postresult_topup_permitted") is not False
        or value.get("additional_hard_axes") != [
            "WALL_TIME", "ACCELERATOR_TIME", "PEAK_DEVICE_MEMORY", "PEAK_HOST_MEMORY",
            "MODEL_EVALUATION_COUNT", "PERSISTENT_BYTES", "FAILURE_COUNT", "PARAMETER_COUNT",
        ]
    ):
        raise ValidationError("F104 policy projection differs")

    b06 = _load_json_predecessor(root, "research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json")
    if b06.get("record_sha256") != EXPECTED_SEMANTIC_BINDINGS["b06_semantic_sha256"]:
        raise ValidationError("B06 semantic digest differs")
    if b06.get("remaining_open_requirements", {}).get("B08") != [
        "HARDWARE_AND_RUNTIME_IDENTITY", "CALIBRATION_WEIGHTS",
        "SCALAR_AND_HARD_AXIS_CEILING_VALUES", "CAPACITY_RESERVATION_RECEIPT",
    ]:
        raise ValidationError("B06 B08 residual requirements differ")
    effects = b06.get("project_effects_and_nonclaims", {})
    if effects.get("b08_closed") is not False or effects.get("hardware_selected_or_capacity_reserved") is not False:
        raise ValidationError("B06 B08 nonclosure differs")
    for closure_row in b06.get("field_closures", []):
        if closure_row.get("field_id") not in ("F066", "F067", "F072", "F073"):
            continue
        value_by_domain = closure_row.get("value")
        if type(value_by_domain) is not dict:
            raise ValidationError("B06 compute budget schema differs")
        for budget in value_by_domain.values():
            pilot = budget.get("phase_event_count_ceilings", {}).get("PILOT")
            if type(pilot) is not dict or not pilot or any(type(v) is not int or v != 0 for v in pilot.values()):
                raise ValidationError("B06 PILOT resource event count is nonzero")

    gate_a = _load_json_predecessor(root, "research/fixtures/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json")
    if gate_a.get("record_sha256") != EXPECTED_SEMANTIC_BINDINGS["gate_a_local_semantic_sha256"]:
        raise ValidationError("Gate-A semantic digest differs")
    gate_values = {row.get("field_id"): row.get("value") for row in gate_a.get("field_closures", [])}
    if gate_values.get("F148") != "NEVER_TRUE_NO_INFRASTRUCTURE_RERUN":
        raise ValidationError("F148 no-rerun predicate differs")

    theory = _load_json_predecessor(root, "research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json")
    if theory.get("record_sha256") != EXPECTED_SEMANTIC_BINDINGS["theory_statistics_semantic_sha256"]:
        raise ValidationError("theory/statistics semantic digest differs")
    theory_values = {row.get("field_id"): row.get("value") for row in theory.get("field_closures", [])}
    if theory_values.get("F131") != "NO_EMPIRICAL_PILOT_DISTRIBUTION_FREE_CKS_PAIRED_RANGE_MINUS3_TO3_WIDTH6":
        raise ValidationError("F131 pilot source differs")

    f061_receipt, _ = stable_read(root, "research/fixtures/manuscript_v3_f061_guarded_power_review_receipt_v1.json")
    if hashlib.sha256(f061_receipt).hexdigest() != EXPECTED_SEMANTIC_BINDINGS["f061_guarded_receipt_sha256"]:
        raise ValidationError("F061 count-anchor receipt differs")


def _validate_source_effect_surface(source_payload: bytes) -> None:
    if hashlib.sha256(source_payload).hexdigest() != EXPECTED_SOURCE_SHA256:
        raise ValidationError("candidate source raw hash differs")
    try:
        tree = ast.parse(source_payload.decode("utf-8"), filename=SOURCE_PATH)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("candidate source cannot be parsed") from error
    allowed_imports = {"__future__", "copy", "hashlib", "json", "typing"}
    forbidden_names = {
        "open", "Path", "os", "subprocess", "socket", "urllib", "requests",
        "random", "secrets", "time", "torch", "numpy", "scipy", "pickle",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in allowed_imports:
                    raise ValidationError("candidate source imports forbidden module")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in allowed_imports:
                raise ValidationError("candidate source imports forbidden module")
        elif isinstance(node, ast.Name) and node.id in forbidden_names:
            raise ValidationError("candidate source contains forbidden effect name: " + node.id)
    text = source_payload.decode("utf-8")
    for required in (
        "B08_REMAINS_OPEN_CAPACITY_NO_GO",
        "B08_CPU_SINGLE_THREAD_FAIL_CLOSED_DETERMINISM_V1",
        "B08_ZERO_EMPIRICAL_PILOT_DISTRIBUTION_FREE_B07_V1",
        "B08_ZERO_FAILURE_RESERVE_NO_RERUN_NO_REPLACEMENT_V1",
    ):
        if required not in text:
            raise ValidationError("candidate source omits required exact policy ID")


def validate_package(root: Path) -> dict:
    base = Path(root)
    machine_payload, _ = stable_read(base, MACHINE_PATH)
    machine = decode_canonical_json_file(machine_payload)
    exact_keys = {
        "accepted_predecessor_bindings", "accepted_semantic_bindings", "authority_boundary",
        "blocker_transition", "control_predicate", "count_transition", "evidence_ready_registration",
        "field_delta", "gate_a_transition", "global_state", "machine_self_binding",
        "package_aggregate_sha256", "package_bindings_excluding_machine_self", "package_file_roster",
        "package_kind", "project_effects_and_nonclaims", "qualification_boundary", "record_sha256",
        "reported_date", "schema_version", "state", "supported_projection",
        "supported_projection_sha256", "workstream_transition",
    }
    if type(machine) is not dict or set(machine) != exact_keys:
        raise ValidationError("machine record schema differs")
    if (
        machine.get("schema_version") != SCHEMA_VERSION
        or machine.get("state") != STATE
        or machine.get("control_predicate") != CONTROL_PREDICATE
        or machine.get("package_kind") != PACKAGE_KIND
        or machine.get("global_state") != "DRAFT_NOT_EXECUTABLE"
        or machine.get("reported_date") != "2026-09-01"
    ):
        raise ValidationError("machine record identity differs")
    digest = machine.get("record_sha256")
    if type(digest) is not str or digest != _record_digest(machine):
        raise ValidationError("machine semantic self digest differs")
    if machine.get("supported_projection_sha256") != EXPECTED_PROJECTION_SHA256:
        raise ValidationError("machine projection binding differs")
    _validate_projection(machine.get("supported_projection"))
    exact_mappings = (
        ("accepted_semantic_bindings", EXPECTED_SEMANTIC_BINDINGS),
        ("authority_boundary", EXPECTED_AUTHORITY_BOUNDARY),
        ("field_delta", EXPECTED_FIELD_DELTA),
        ("count_transition", EXPECTED_COUNT_TRANSITION),
        ("workstream_transition", EXPECTED_WORKSTREAM_TRANSITION),
        ("blocker_transition", EXPECTED_BLOCKER_TRANSITION),
        ("gate_a_transition", EXPECTED_GATE_A_TRANSITION),
        ("project_effects_and_nonclaims", EXPECTED_PROJECT_EFFECTS),
        ("qualification_boundary", EXPECTED_QUALIFICATION_BOUNDARY),
        ("evidence_ready_registration", EXPECTED_REGISTRATION),
    )
    for name, expected in exact_mappings:
        if machine.get(name) != expected:
            raise ValidationError(name + " differs")
    if machine.get("package_file_roster") != PACKAGE_ROSTER:
        raise ValidationError("package roster differs")
    if machine.get("machine_self_binding") != {
        "path": MACHINE_PATH,
        "raw_self_hash_embedded": False,
        "semantic_self_digest_field": "record_sha256",
    }:
        raise ValidationError("machine self-binding differs")

    expected_predecessors = predecessor_bindings(base)
    if machine.get("accepted_predecessor_bindings") != expected_predecessors:
        raise ValidationError("accepted predecessor bindings differ")
    expected_package = package_bindings(base)
    if machine.get("package_bindings_excluding_machine_self") != expected_package:
        raise ValidationError("current package bindings differ")
    if machine.get("package_aggregate_sha256") != package_aggregate_sha256(expected_package):
        raise ValidationError("package aggregate differs")
    package_by_path = {row["path"]: row for row in expected_package}
    if package_by_path[HUMAN_PATH]["raw_sha256"] != EXPECTED_HUMAN_SHA256:
        raise ValidationError("human record raw hash differs")
    if package_by_path[TEST_PATH]["raw_sha256"] != EXPECTED_TEST_SHA256:
        raise ValidationError("hostile test raw hash differs")
    source_payload, _ = stable_read(base, SOURCE_PATH)
    _validate_source_effect_surface(source_payload)
    _validate_predecessor_semantics(base)
    return {
        "accepted_predecessor_count": len(expected_predecessors),
        "B08_closed": False,
        "field_ids": ["F153", "F158", "F161"],
        "package_aggregate_sha256": machine["package_aggregate_sha256"],
        "record_sha256": machine["record_sha256"],
        "residual_field_ids": ["F150", "F151", "F152", "F154", "F155", "F156", "F157", "F159", "F160", "F162"],
        "state": machine["state"],
        "supported_projection_sha256": machine["supported_projection_sha256"],
    }


def default_project_root() -> Path:
    return Path(__file__).absolute().parents[2]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=default_project_root())
    arguments = parser.parse_args(argv)
    try:
        result = validate_package(arguments.project_root.absolute())
    except (OSError, ValidationError, ValueError, TypeError) as error:
        print("FAIL_B08_LOCAL_HOST_CAPACITY_GAP: %s" % error, file=sys.stderr)
        return 1
    print("PASS_THREE_FIELDS_ONLY_B08_REMAINS_OPEN")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
