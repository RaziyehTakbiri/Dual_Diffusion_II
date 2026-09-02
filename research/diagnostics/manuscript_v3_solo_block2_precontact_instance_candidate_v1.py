"""Read-only validator for the Solo Block 2 precontact-instance candidate.

The validator reopens only a fixed fourteen-file roster: this four-file
candidate package and ten immutable predecessor files.  Historical drafting
snapshots are hash receipts only and are never reopened.  There is no network,
subprocess, connector, entropy, data, protocol, authority/runtime, scientific,
or writer route.  Guarantees are procedural on an honest host, not resistance
to a malicious host.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-solo-block2-precontact-instance-candidate-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = (
    "PRECONTACT_INSTANCE_LOCAL_CANDIDATE_COMPLETE_AWAITING_PRECONTACT_"
    "PREREQUISITES_AND_INDEPENDENT_REVIEW"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
PACKAGE_KIND = "STATIC_LOCAL_CANDIDATE_AND_GAP_AUDIT_NOT_POPULATED_INSTANCE"
REPORTED_DATE = "2026-08-30"

HUMAN_PATH = "PROJECT_SOLO_BLOCK2_PRECONTACT_INSTANCE_CANDIDATE.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_solo_block2_precontact_instance_candidate_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_solo_block2_precontact_instance_candidate_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_solo_block2_precontact_instance_candidate_v1.py"
)

PREREGISTRATION_PATH = (
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
)
CLOSURE_PATH = (
    "research/fixtures/"
    "manuscript_v3_execution_preregistration_preexecution_closure_v2.json"
)
SEAL_HUMAN_PATH = "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md"
SEAL_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json"
)
SEAL_VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py"
)
SEAL_TEST_PATH = (
    "tests/unit/test_manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py"
)
STATIC_HUMAN_PATH = "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md"
STATIC_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json"
)
STATIC_VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_solo_block2_static_selection_freeze_v1.py"
)
STATIC_TEST_PATH = (
    "tests/unit/test_manuscript_v3_solo_block2_static_selection_freeze_v1.py"
)

NORMALIZED_AUTHORITY_TEXT = (
    "Okay, go ahead to the next step then.\n"
    "And dont forget to mark the steps carried out in the project plan."
)
AUTHORITY_TEXT_SHA256 = (
    "d5d42ebe4def8e706729637627e2497f7b62f1b239a4f49e74e40f488f8b166a"
)
CONTROL_PREDICATE = (
    "SOLO_BLOCK2_PRECONTACT_INSTANCE_LOCAL_CANDIDATE_AND_GAP_AUDIT_VALIDATED"
)
PHYSIONET_URL = "https://physionet.org/content/challenge-2012/1.0.0/"
RETAIL_URL = "https://archive.ics.uci.edu/dataset/502/online+retail+ii"


class ValidationError(ValueError):
    """Raised when candidate custody or semantics fail closed."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload))


def _self_digest(record: Mapping[str, Any]) -> str:
    schema = record.get("schema_version")
    if type(schema) is not str or not schema.isascii():
        raise ValidationError("self-digest schema invalid")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(
        (schema + "\0").encode("ascii") + _canonical_payload_bytes(payload)
    )


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for ordinal, (item, wanted) in enumerate(zip(actual, expected)):
            _strict_equal(item, wanted, label + "[" + str(ordinal) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def _safe_relative_path(root: Path, relative_path: str) -> Path:
    if type(relative_path) is not str:
        raise ValidationError("path type invalid")
    rel = Path(relative_path)
    if rel.is_absolute() or not rel.parts or ".." in rel.parts:
        raise ValidationError("unsafe path")
    return root.joinpath(*rel.parts)


def _ancestor_snapshot(root: Path, path: Path) -> Tuple[Tuple[Any, ...], ...]:
    rows: List[Tuple[Any, ...]] = []
    current = path.parent
    while True:
        status = current.lstat()
        if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
            raise ValidationError("unsafe ancestor")
        rows.append(
            (
                str(current),
                status.st_dev,
                status.st_ino,
                stat.S_IFMT(status.st_mode),
                stat.S_IMODE(status.st_mode),
                status.st_uid,
                status.st_gid,
            )
        )
        if current == root:
            break
        if root not in current.parents:
            raise ValidationError("path escaped root")
        current = current.parent
    return tuple(reversed(rows))


def _leaf_fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode),
        status.st_uid,
        status.st_gid,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _stable_read(root: Path, relative_path: str) -> bytes:
    path = _safe_relative_path(root, relative_path)
    ancestors = _ancestor_snapshot(root, path)
    before_path = path.lstat()
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != 0o644
        or before_path.st_nlink != 1
    ):
        raise ValidationError("file custody invalid: " + relative_path)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before_fd = os.fstat(descriptor)
        chunks: List[bytes] = []
        while True:
            chunk = os.read(descriptor, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    raw = b"".join(chunks)
    fingerprint = _leaf_fingerprint(before_path)
    if not (
        fingerprint
        == _leaf_fingerprint(before_fd)
        == _leaf_fingerprint(after_fd)
        == _leaf_fingerprint(after_path)
    ):
        raise ValidationError("file changed during read: " + relative_path)
    if len(raw) != before_fd.st_size:
        raise ValidationError("short read: " + relative_path)
    if ancestors != _ancestor_snapshot(root, path):
        raise ValidationError("ancestor changed during read")
    return raw


def _binding(
    ordinal: int,
    role: str,
    path: str,
    raw: bytes,
    *,
    self_digest: Optional[str] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "ordinal": ordinal,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": raw.endswith(b"\n"),
    }
    if self_digest is not None:
        row["record_sha256"] = self_digest
    return row


LIVE_IMMUTABLE_BINDINGS: Tuple[Mapping[str, Any], ...] = (
    {
        "ordinal": 0,
        "role": "EXECUTION_PREREGISTRATION",
        "path": PREREGISTRATION_PATH,
        "bytes": 39771,
        "raw_sha256": "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": True,
    },
    {
        "ordinal": 1,
        "role": "PREEXECUTION_CLOSURE",
        "path": CLOSURE_PATH,
        "bytes": 24571,
        "raw_sha256": "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": True,
        "record_sha256": "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4",
    },
    {
        "ordinal": 2,
        "role": "PROSPECTIVE_SEAL_HUMAN",
        "path": SEAL_HUMAN_PATH,
        "bytes": 7078,
        "raw_sha256": "ad58c5fcb9d47531a7af041eb59f71386fd42a81b1fe31701df167f064f951c2",
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": True,
    },
    {
        "ordinal": 3,
        "role": "PROSPECTIVE_SEAL_MACHINE",
        "path": SEAL_MACHINE_PATH,
        "bytes": 8461,
        "raw_sha256": "0357fc48394d5888632e3e2d7f5c9180e683141ebc10bef3dec9879a58cdf0e8",
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": True,
        "record_sha256": "d11d5336f1ede024ab56f92bc64e620681e53fc406fd954aa3da36b7861485a6",
    },
    {
        "ordinal": 4,
        "role": "PROSPECTIVE_SEAL_VALIDATOR",
        "path": SEAL_VALIDATOR_PATH,
        "bytes": 32156,
        "raw_sha256": "3647c367506519149d5df60dc2dcfb07a8f5dc976526b88700321b0de89a2258",
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": True,
    },
    {
        "ordinal": 5,
        "role": "PROSPECTIVE_SEAL_HOSTILE_TEST",
        "path": SEAL_TEST_PATH,
        "bytes": 16698,
        "raw_sha256": "2285525223f42154553a0302bb46a8f04f0ff7ff35233906a37f4f1a9bf47403",
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": True,
    },
    {
        "ordinal": 6,
        "role": "STATIC_SELECTION_HUMAN",
        "path": STATIC_HUMAN_PATH,
        "bytes": 23012,
        "raw_sha256": "ab80a009f3d83be4186d3d2da13e3efd5939362e4215477dd2b1a89b870b3126",
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": True,
    },
    {
        "ordinal": 7,
        "role": "STATIC_SELECTION_MACHINE",
        "path": STATIC_MACHINE_PATH,
        "bytes": 33638,
        "raw_sha256": "7ff0bf3bb5d9a03e2212f2f7f1853cde2283694b33e072931d258d98e1882590",
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": True,
        "record_sha256": "1f02200d524749d6708695072dfbc8b785a6f03d5be908b3563f121d7fcd5b53",
    },
    {
        "ordinal": 8,
        "role": "STATIC_SELECTION_VALIDATOR",
        "path": STATIC_VALIDATOR_PATH,
        "bytes": 56344,
        "raw_sha256": "8843cef229c24cbd25cd00e55697755c8fc7a1247f20044dfe110e182e558ec0",
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": True,
    },
    {
        "ordinal": 9,
        "role": "STATIC_SELECTION_HOSTILE_TEST",
        "path": STATIC_TEST_PATH,
        "bytes": 48158,
        "raw_sha256": "801fc7c87f57eb72da6cdfa7b2be93c6edd66b974fefe47dabbe5b91eaa0f005",
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": True,
    },
)


HISTORICAL_SNAPSHOT_INPUTS: Tuple[Mapping[str, Any], ...] = (
    {
        "ordinal": 0,
        "role": "METHOD_SPEC_HISTORICAL_SNAPSHOT",
        "path": "manuscript_v3/executable_method_spec.md",
        "bytes": 442123,
        "raw_sha256": "58bdfd689caa1698a07e415074e98bd3a80e9d69467d9ddec8f8471aba36c34d",
        "mode_octal_at_snapshot": "0644",
        "live_reopen_required": False,
        "official_source_or_contact_evidence": False,
    },
    {
        "ordinal": 1,
        "role": "METHOD_AUDIT_HISTORICAL_SNAPSHOT",
        "path": "manuscript_v3/executable_method_audit.md",
        "bytes": 186715,
        "raw_sha256": "4dbfe7ec57973dcac1dcaae4a03f46e60f66d828d6b75d1c77dd1b8776d35da0",
        "mode_octal_at_snapshot": "0644",
        "live_reopen_required": False,
        "official_source_or_contact_evidence": False,
    },
    {
        "ordinal": 2,
        "role": "PHYSIONET_RAW_CODE_HISTORICAL_SNAPSHOT",
        "path": "src/heterodiff/data/physionet_2012_raw.py",
        "bytes": 25231,
        "raw_sha256": "ff869134bfd696964c23bf7a2dbd0b2b428811b0fb3058cd7f3bd688dd48968c",
        "mode_octal_at_snapshot": "0644",
        "live_reopen_required": False,
        "official_source_or_contact_evidence": False,
    },
    {
        "ordinal": 3,
        "role": "PHYSIONET_ADAPTER_CODE_HISTORICAL_SNAPSHOT",
        "path": "src/heterodiff/data/physionet_2012_adapter.py",
        "bytes": 34377,
        "raw_sha256": "4429d826115bd520d2d3dacecb68fed3dc53d72c99acec9095068f44aa5582da",
        "mode_octal_at_snapshot": "0644",
        "live_reopen_required": False,
        "official_source_or_contact_evidence": False,
    },
    {
        "ordinal": 4,
        "role": "PHYSIONET_INVENTORY_CODE_HISTORICAL_SNAPSHOT",
        "path": "src/heterodiff/data/physionet_2012_inventory.py",
        "bytes": 26000,
        "raw_sha256": "50f3eb80ba284400c4dea76a04a162b72be090bc62628b692dca548c3a203985",
        "mode_octal_at_snapshot": "0644",
        "live_reopen_required": False,
        "official_source_or_contact_evidence": False,
    },
    {
        "ordinal": 5,
        "role": "RETAIL_FIXTURE_CODE_HISTORICAL_SNAPSHOT",
        "path": "src/heterodiff/data/generated_transaction_fixture.py",
        "bytes": 42657,
        "raw_sha256": "0f3a67f863c7adedf2ff443f80864f39e5b958ecfce584403414905b67e54a7d",
        "mode_octal_at_snapshot": "0644",
        "live_reopen_required": False,
        "official_source_or_contact_evidence": False,
    },
)


EXPECTED_AUTHORITY: Mapping[str, Any] = {
    "normalized_visible_text": NORMALIZED_AUTHORITY_TEXT,
    "normalized_visible_text_sha256": AUTHORITY_TEXT_SHA256,
    "normalized_visible_text_utf8_bytes": 104,
    "normalization": "TRAILING_HTML_SPACE_ENTITY_AND_TRANSPORT_WHITESPACE_REMOVED_ONLY",
    "raw_transport_bytes_bound": False,
    "conversation_envelope_bound": False,
    "account_identity_bound": False,
    "timestamp_bound": False,
    "cryptographic_user_authentication_claimed": False,
    "additive_static_candidate_package_authorized": True,
    "later_one_way_tracker_maintenance_after_independent_go_authorized": True,
    "tracker_edit_authorized_before_independent_go": False,
    "external_contact_authorized": False,
    "dataset_page_browsing_authorized": False,
    "documentation_license_or_governance_browsing_authorized": False,
    "data_access_or_download_authorized": False,
    "approval_creation_authorized": False,
    "credential_use_authorized": False,
    "protocol_operation_authorized": False,
    "scientific_execution_authorized": False,
    "scientific_entropy_authorized": False,
    "user_selected_paths_schema_or_file_count": False,
    "user_selected_roster_split_or_role_tokens": False,
    "agent_selected_bounded_implementation_details": True,
}


EXPECTED_IDENTITY: Mapping[str, Any] = {
    "candidate_id": "SOLO_BLOCK2_PRECONTACT_INSTANCE_CANDIDATE_V1",
    "candidate_present": True,
    "candidate_complete_as_gap_audit": True,
    "populated_instance_present": False,
    "populated_instance_admitted": False,
    "independent_review_present": False,
    "administrative_contact_authority_present": False,
    "data_access_authority_present": False,
    "durable_contact_intent_present": False,
    "source_contact_performed_by_this_package": False,
    "documentation_or_license_contact_performed_by_this_package": False,
    "governance_or_approval_contact_performed_by_this_package": False,
    "data_access_performed_by_this_package": False,
    "snapshot_observed": False,
    "split_performed": False,
    "escrow_activated": False,
    "science_performed": False,
    "result_produced": False,
    "precontact_population_blocked": True,
    "candidate_operation_roster_complete_for_admission": False,
    "approval_contact_target_roster_complete": False,
    "retail_exact_temporal_rule_populated": False,
}


EXPECTED_SOURCES: Sequence[Mapping[str, Any]] = (
    {
        "ordinal": 0,
        "domain_id": "physionet-challenge-2012",
        "registered_source_url": PHYSIONET_URL,
        "target_status": "SOLE_REGISTERED_UNVERIFIED_TARGET",
        "resolved_or_contacted_by_this_package": False,
        "redirect_permitted": False,
        "mirror_or_fallback_permitted": False,
        "target_mismatch_disposition": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
    },
    {
        "ordinal": 1,
        "domain_id": "online-retail-ii",
        "registered_source_url": RETAIL_URL,
        "target_status": "SOLE_REGISTERED_UNVERIFIED_TARGET",
        "resolved_or_contacted_by_this_package": False,
        "redirect_permitted": False,
        "mirror_or_fallback_permitted": False,
        "target_mismatch_disposition": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
    },
)


ADMIN_SUCCESS = (
    "EXACT_REGISTERED_TARGET_NO_REDIRECT_AND_ONE_CANONICAL_VERSION_REVISION_AND_"
    "EXACTLY_ONE_IMMUTABLE_ARCHIVE_LOCATOR_SHA256_BYTE_COUNT_AND_COMPLETE_"
    "LICENSE_GOVERNANCE_ACCESS_SCHEMA_TIMEZONE_REQUIREMENTS_RECEIPT"
)
DATA_SUCCESS = (
    "EXACT_PRIOR_ADMIN_RECEIPT_AND_ALL_REQUIRED_APPROVAL_RECEIPTS_AND_SEPARATELY_"
    "REVIEWED_ACCESS_INSTANCE_AND_FRESH_DATA_AUTHORITY_AND_DURABLE_INTENT_AND_"
    "ONE_CONTENT_ADDRESSED_ARCHIVE_MATCHING_VERSION_LOCATOR_SHA256_AND_BYTE_COUNT"
)


EXPECTED_OPERATION_ROWS: Sequence[Mapping[str, Any]] = (
    {
        "global_ordinal": 0,
        "operation_id": "PHYSIONET_ADMIN_METADATA_LICENSE_GOVERNANCE",
        "domain_id": "physionet-challenge-2012",
        "phase": "ADMIN",
        "exact_target": PHYSIONET_URL,
        "exact_target_derivation": "LITERAL_REGISTERED_SOURCE_URL",
        "exact_permitted_request_kind": "ADMIN_METADATA_LICENSE_GOVERNANCE_ONLY_NO_AUTH_NO_DOWNLOAD",
        "maximum_attempt_count": 1,
        "authorized_retry_count": 0,
        "required_prior_receipts": ["POPULATED_INSTANCE_REVIEW", "FRESH_ADMIN_CONTACT_AUTHORITY", "DURABLE_INTENT"],
        "exact_machine_evaluable_success_predicate": ADMIN_SUCCESS,
        "failure_disposition_resolution_order": ["PROTOCOL_VIOLATION", "INTENT_WITHOUT_OUTCOME", "NAMED_FAILURE_DISPOSITION_MAP", "RESIDUAL_PHASE_NON_SUCCESS"],
        "residual_terminal_disposition_after_protocol_violation_and_named_failure_map": "ADMIN_CONTACT_TERMINAL_NO_GO",
        "current_intent_receipt": None,
        "current_outcome_receipt": None,
        "currently_eligible": False,
    },
    {
        "global_ordinal": 1,
        "operation_id": "RETAIL_ADMIN_METADATA_LICENSE_GOVERNANCE",
        "domain_id": "online-retail-ii",
        "phase": "ADMIN",
        "exact_target": RETAIL_URL,
        "exact_target_derivation": "LITERAL_REGISTERED_SOURCE_URL",
        "exact_permitted_request_kind": "ADMIN_METADATA_LICENSE_GOVERNANCE_ONLY_NO_AUTH_NO_DOWNLOAD",
        "maximum_attempt_count": 1,
        "authorized_retry_count": 0,
        "required_prior_receipts": ["POPULATED_INSTANCE_REVIEW", "FRESH_ADMIN_CONTACT_AUTHORITY", "DURABLE_INTENT"],
        "exact_machine_evaluable_success_predicate": ADMIN_SUCCESS,
        "failure_disposition_resolution_order": ["PROTOCOL_VIOLATION", "INTENT_WITHOUT_OUTCOME", "NAMED_FAILURE_DISPOSITION_MAP", "RESIDUAL_PHASE_NON_SUCCESS"],
        "residual_terminal_disposition_after_protocol_violation_and_named_failure_map": "ADMIN_CONTACT_TERMINAL_NO_GO",
        "current_intent_receipt": None,
        "current_outcome_receipt": None,
        "currently_eligible": False,
    },
    {
        "global_ordinal": 2,
        "operation_id": "PHYSIONET_DATA_AUTHENTICATION_OR_DOWNLOAD",
        "domain_id": "physionet-challenge-2012",
        "phase": "DATA",
        "exact_target": "ROW_0_EXACT_SUCCESS_SINGLE_CONTENT_ADDRESSED_ARCHIVE",
        "exact_target_derivation": "DETERMINISTIC_FROM_ACCEPTED_ROW_0_RECEIPT_ONLY",
        "exact_permitted_request_kind": "DATA_AUTHENTICATION_OR_DOWNLOAD_ONLY_AFTER_ALL_GATES",
        "maximum_attempt_count": 1,
        "authorized_retry_count": 0,
        "required_prior_receipts": ["ROW_0_EXACT_SUCCESS", "ALL_REQUIRED_APPROVAL_RECEIPTS", "SEPARATELY_REVIEWED_DATA_ACCESS_INSTANCE", "FRESH_DATA_ACCESS_AUTHORITY", "DURABLE_INTENT"],
        "exact_machine_evaluable_success_predicate": DATA_SUCCESS,
        "failure_disposition_resolution_order": ["PROTOCOL_VIOLATION", "INTENT_WITHOUT_OUTCOME", "NAMED_FAILURE_DISPOSITION_MAP", "RESIDUAL_PHASE_NON_SUCCESS"],
        "residual_terminal_disposition_after_protocol_violation_and_named_failure_map": "DATA_ACCESS_TERMINAL_NO_GO",
        "current_intent_receipt": None,
        "current_outcome_receipt": None,
        "currently_eligible": False,
    },
    {
        "global_ordinal": 3,
        "operation_id": "RETAIL_DATA_AUTHENTICATION_OR_DOWNLOAD",
        "domain_id": "online-retail-ii",
        "phase": "DATA",
        "exact_target": "ROW_1_EXACT_SUCCESS_SINGLE_CONTENT_ADDRESSED_ARCHIVE",
        "exact_target_derivation": "DETERMINISTIC_FROM_ACCEPTED_ROW_1_RECEIPT_ONLY",
        "exact_permitted_request_kind": "DATA_AUTHENTICATION_OR_DOWNLOAD_ONLY_AFTER_ALL_GATES",
        "maximum_attempt_count": 1,
        "authorized_retry_count": 0,
        "required_prior_receipts": ["ROW_1_EXACT_SUCCESS", "ALL_REQUIRED_APPROVAL_RECEIPTS", "SEPARATELY_REVIEWED_DATA_ACCESS_INSTANCE", "FRESH_DATA_ACCESS_AUTHORITY", "DURABLE_INTENT"],
        "exact_machine_evaluable_success_predicate": DATA_SUCCESS,
        "failure_disposition_resolution_order": ["PROTOCOL_VIOLATION", "INTENT_WITHOUT_OUTCOME", "NAMED_FAILURE_DISPOSITION_MAP", "RESIDUAL_PHASE_NON_SUCCESS"],
        "residual_terminal_disposition_after_protocol_violation_and_named_failure_map": "DATA_ACCESS_TERMINAL_NO_GO",
        "current_intent_receipt": None,
        "current_outcome_receipt": None,
        "currently_eligible": False,
    },
)


EXPECTED_SELECTORS: Mapping[str, Any] = {
    "physionet": {
        "domain_id": "physionet-challenge-2012",
        "agent_selected_expected_version_token": "1.0.0",
        "exact_registered_url": PHYSIONET_URL,
        "expected_identity_verified_by_this_package": False,
        "required_admin_result_cardinality": 1,
        "required_archive_fields": ["IMMUTABLE_ARCHIVE_LOCATOR", "VERSION_OR_REVISION", "SHA256", "BYTE_COUNT"],
        "observed_archive_locator": None,
        "observed_version": None,
        "observed_sha256": None,
        "observed_byte_count": None,
        "redirect_fallback_or_substitution_permitted": False,
    },
    "retail": {
        "domain_id": "online-retail-ii",
        "agent_selected_expected_dataset_id_token": "502",
        "agent_selected_expected_title_token": "online-retail-ii",
        "exact_registered_url": RETAIL_URL,
        "expected_identity_verified_by_this_package": False,
        "required_admin_result_cardinality": 1,
        "required_archive_fields": ["IMMUTABLE_ARCHIVE_LOCATOR", "VERSION_OR_REVISION", "SHA256", "BYTE_COUNT"],
        "observed_archive_locator": None,
        "observed_version": None,
        "observed_sha256": None,
        "observed_byte_count": None,
        "redirect_fallback_or_substitution_permitted": False,
    },
    "zero_or_multiple_candidates_disposition": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
    "mismatch_or_unavailability_disposition": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
    "reconnaissance_or_target_amendment_permitted": False,
}


EXPECTED_ADMIN_QUESTIONS: Sequence[str] = (
    "CANONICAL_DATASET_IDENTIFIER_AND_CURRENT_IMMUTABLE_VERSION_OR_REVISION",
    "EXACTLY_ONE_IMMUTABLE_ARCHIVE_LOCATOR_SHA256_AND_BYTE_COUNT",
    "GOVERNING_LICENSE_OR_TERMS_FOR_ACCESS_STORAGE_ANALYSIS_PUBLICATION_REDISTRIBUTION_RETENTION",
    "ACCOUNT_AUTHENTICATION_OR_DATA_USE_AGREEMENT_REQUIREMENTS",
    "GOVERNANCE_ETHICS_PRIVACY_CLINICAL_OR_INSTITUTIONAL_APPROVAL_REQUIREMENTS",
    "STORAGE_DELETION_RETENTION_DISCLOSURE_AND_PUBLICATION_CONTROLS",
    "SCHEMA_AND_TIMEZONE_METADATA_REQUIRED_FOR_DETERMINISTIC_SELECTOR_AND_SPLIT",
)


EXPECTED_SPLIT: Mapping[str, Any] = {
    "candidate_only": True,
    "agent_selected": True,
    "power_justified": False,
    "proportions": {"train_numerator": 70, "validation_numerator": 15, "test_numerator": 15, "denominator": 100},
    "allocation_rule": "HAMILTON_LARGEST_REMAINDER_OVER_NATURAL_GROUPS",
    "minimum_group_count": 5,
    "remainder_tie_priority": ["TRAIN", "VALIDATION", "TEST"],
    "ordering_rule": "CANDIDATE_PUBLIC_DOMAIN_SEPARATED_SHA256_RULE_NOT_FULLY_SPECIFIED",
    "exact_split_algorithm_populated": False,
    "seed_or_entropy_required": False,
    "snapshot_fixed_and_hash_bound_before_split_required": True,
    "physionet": {
        "natural_group": "NONEMPTY_CANONICAL_PATIENT_ID",
        "all_patient_records_in_one_split_required": True,
        "patient_overlap_permitted": False,
        "exact_rule_populated": False,
        "literal_hash_domain_separator": None,
        "canonical_patient_id_byte_encoding_and_normalization": None,
        "hash_collision_tie_break_rule": None,
    },
    "retail": {
        "natural_group": "NONEMPTY_CUSTOMER_ID",
        "invoice_time_requirement": "UNAMBIGUOUS_UTC_AFTER_ADMIN_TIMEZONE_RECEIPT",
        "customer_interval": "FULL_CLOSED_INTERVAL_MIN_TO_MAX_INVOICE_TIME",
        "required_policy": "CUSTOMER_DISJOINT_AND_TEMPORAL",
        "test_set_exclusion_permitted": False,
        "customer_invoice_or_row_censoring_permitted": False,
        "boundary_spanning_customer_exclusion_permitted": False,
        "candidate_feasibility_idea": "DETERMINISTIC_BOUNDARY_PAIR_SEARCH_WITH_EVERY_FULL_CUSTOMER_INTERVAL_IN_EXACTLY_ONE_ORDERED_WINDOW_AND_EXACT_HAMILTON_COUNTS",
        "zero_feasible_pair_disposition": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
        "exact_temporal_rule_populated": False,
        "independent_consistency_review_complete": False,
    },
    "duplicate_group_overlap_near_duplicate_and_temporal_audits_required": True,
    "actual_cutoffs_counts_and_manifest_sha256": None,
    "split_performed": False,
}


EXPECTED_APPROVALS: Mapping[str, Any] = {
    "required_receipt_classes": [
        "SOURCE_LICENSE_AND_ACCESS_TERMS",
        "PHYSIONET_CLINICAL_ETHICS_GOVERNANCE_DETERMINATION",
        "RETAIL_PRIVACY_PSEUDONYMOUS_CUSTOMER_DUPLICATE_AND_MEMBERSHIP_INFERENCE_DETERMINATION",
        "DATA_SECURITY_STORAGE_RETENTION_DELETION_REDISTRIBUTION_AND_PUBLICATION_CONTROLS",
        "EXACT_SOURCE_MANIFEST_VERSION_RECEIPT",
        "INDEPENDENT_PROTOCOL_REVIEW",
        "SEPARATE_DATA_ACCESS_INSTANCE_REVIEW",
    ],
    "receipt_values": [None, None, None, None, None, None, None],
    "concrete_approval_target_identities_present": False,
    "approval_contact_target_roster_complete": False,
    "undeclared_approval_contact_permitted": False,
    "missing_required_contact_disposition": "PRECONTACT_POPULATION_BLOCKED_BEFORE_ANY_CONTACT_NEW_EXPLICIT_SCOPE_REVIEW_REQUIRED",
    "scope_review_may_complete_roster_only_before_any_contact": True,
    "post_contact_or_terminal_scope_review_may_repair_resume_insert_or_replace": False,
    "administrative_response_creates_approval": False,
    "all_required_approvals_complete": False,
}


EXPECTED_ESCROW: Mapping[str, Any] = {
    "candidate_role_tokens": [
        "RAW_SNAPSHOT_CUSTODIAN_ROLE",
        "DETERMINISTIC_SPLIT_OPERATOR_ROLE",
        "INDEPENDENT_HELD_OUT_ESCROW_CUSTODIAN_ROLE",
        "INDEPENDENT_FINAL_OPENING_APPROVER_ROLE",
    ],
    "role_tokens_are_real_identities": False,
    "real_principal_identity_binding_present": False,
    "key_identity_binding_present": False,
    "acl_acceptance_receipt_present": False,
    "final_opening_authority_present": False,
    "independent_escrow_ready": False,
    "solo_worker_self_escrow_called_independent": False,
    "credentials_tokens_or_key_material_present": False,
    "test_inputs_or_outcomes_opened": False,
}


EXPECTED_FUTURE_SLOTS: Mapping[str, Any] = {
    "administrative_contact_outcomes": None,
    "data_access_outcomes": None,
    "observed_snapshot_versions": None,
    "raw_snapshot_sha256_by_domain": None,
    "snapshot_byte_counts_by_domain": None,
    "etag_or_equivalent_by_domain": None,
    "license_text_receipts": None,
    "governance_approval_receipts": None,
    "ethics_approval_receipts": None,
    "split_counts": None,
    "split_manifest_sha256": None,
    "escrow_receipts": None,
    "access_log_head_sha256": None,
}


FAILURE_MAP: Mapping[str, str] = {
    "ADMIN_DENIED": "ADMIN_CONTACT_TERMINAL_NO_GO",
    "ADMIN_FAILED": "ADMIN_CONTACT_TERMINAL_NO_GO",
    "ADMIN_CANCELLED": "ADMIN_CONTACT_TERMINAL_NO_GO",
    "REQUIRED_APPROVALS_INCOMPLETE": "APPROVALS_INCOMPLETE_TERMINAL_NO_GO",
    "SELECTED_VERSION_UNAVAILABLE": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
    "ACQUISITION_SELECTOR_MISMATCH": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
    "SNAPSHOT_IDENTITY_OR_HASH_MISMATCH": "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
    "DATA_ACCESS_DENIED": "DATA_ACCESS_TERMINAL_NO_GO",
    "DATA_ACCESS_FAILED": "DATA_ACCESS_TERMINAL_NO_GO",
    "DATA_ACCESS_CANCELLED": "DATA_ACCESS_TERMINAL_NO_GO",
}


EXPECTED_FAILURE: Mapping[str, Any] = {
    "intent_claim_method": "O_EXCL_0600_FILE_FSYNC_PARENT_FSYNC",
    "outcome_append_only_hash_link_required": True,
    "intent_without_outcome_disposition": "TERMINAL_SPENT_INCOMPLETE_NO_RETRY",
    "protocol_violation_precedence": 0,
    "intent_without_outcome_precedence": 1,
    "named_failure_mapping_precedence": 2,
    "residual_phase_non_success_precedence": 3,
    "named_failure_disposition_map": dict(FAILURE_MAP),
    "unknown_or_missing_outcome_may_count_as_success": False,
    "failure_mapping_total_nonoverlapping_and_precedence_ordered_required": True,
    "terminal_no_go_permits_retry_repair_replacement_fallback_deletion_reacquisition_or_amendment": False,
    "protocol_violation_terminal_state": "SOLO_BLOCK2_PRECONTACT_PROTOCOL_VIOLATION_TERMINAL",
    "contact_from_current_candidate_state_is_protocol_violation": True,
}


EXPECTED_GAPS: Mapping[str, Any] = {
    "local_or_user_resolvable_precontact_prerequisites": [
        "SPLIT_POWER_JUSTIFICATION_ABSENT",
        "REAL_ESCROW_PRINCIPALS_KEYS_AND_ACL_ACCEPTANCE_ABSENT",
        "CONCRETE_APPROVAL_REVIEWER_TARGET_IDENTITIES_AND_VALIDATORS_ABSENT",
        "PHYSIONET_EXACT_HASH_ALGORITHM_AND_COLLISION_RULE_NOT_POPULATED",
        "RETAIL_EXACT_TEMPORAL_NO_EXCLUSION_RULE_NOT_INDEPENDENTLY_REVIEWED",
    ],
    "future_admin_observations_not_precontact_reconnaissance_authority": [
        "CURRENT_OFFICIAL_SOURCE_VERSION_ARCHIVE_LICENSE_AND_GOVERNANCE_FACTS_UNOBSERVED",
        "CONCRETE_RETAIL_IMMUTABLE_VERSION_AND_ARCHIVE_UNOBSERVED",
        "PHYSIONET_SINGLE_ARCHIVE_LOCATOR_HASH_AND_BYTES_UNOBSERVED",
    ],
    "precontact_population_blocked": True,
    "external_fact_needed_to_define_first_contact_target_or_rule_means_population_blocked": True,
    "documentation_license_governance_reconnaissance_exception_permitted": False,
    "registered_urls_are_unverified_sole_targets": True,
    "target_mismatch_permits_amendment_or_reconnaissance": False,
    "four_row_core_complete_for_admission": False,
    "approval_contact_roster_incomplete": True,
    "physionet_exact_split_rule_complete": False,
    "retail_temporal_rule_complete": False,
    "role_tokens_are_real_escrow_identities": False,
}


EXPECTED_CHECKLIST: Mapping[str, Any] = {
    "candidate_control_predicate": CONTROL_PREDICATE,
    "candidate_control_predicate_value_after_validation": True,
    "original_populated_instance_checkbox_closed": False,
    "theory_selection_changed": False,
    "metric_route_selection_changed": False,
    "method_inventory_changed": False,
    "static_protocol_design_changed": False,
    "unresolved_fields_closed": 0,
    "blockers_closed": 0,
    "formal_tests_closed": 0,
    "results_filled": 0,
    "effective_unresolved_field_count": 172,
    "effective_preexecution_unresolved_field_count": 166,
    "effective_deferred_postexecution_unresolved_field_count": 6,
    "effective_open_blocker_count": 12,
    "effective_open_execution_blocker_count": 10,
    "effective_open_submission_blocker_count": 2,
    "f172_open_and_null": True,
    "domain_admission_complete": False,
    "power_review_complete": False,
    "c17_proved": False,
    "cks_characteristicness_proved": False,
    "primary_metric_selected": False,
    "runner_or_science_authorized": False,
    "external_requests_opened_by_this_package": False,
    "protected_data_or_outcomes_accessed_by_this_package": False,
    "tracker_edit_performed_by_this_package": False,
}


EXPECTED_SCOPE: Mapping[str, Any] = {
    "preparatory_package_ordinal_for_precontact": 2,
    "second_and_last_preparatory_package_under_current_scope": True,
    "third_micro_layer_permitted_without_explicit_new_scope_review": False,
    "four_physical_files_form_one_candidate_validation_package": True,
    "targeted_blocker_count": 0,
    "field_or_blocker_closure_claimed": False,
    "tracker_may_consume_after_independent_go_one_way": True,
    "tracker_digest_bound_by_this_package": False,
    "existing_file_modified": False,
    "future_instance_path_absence_is_permanent_gate": False,
}


EXPECTED_ANONYMITY: Mapping[str, Any] = {
    "package_internal_only": True,
    "anonymous_or_public_supplement": False,
    "publication_safe_derivative_required": True,
    "local_absolute_paths_present": False,
    "credentials_tokens_cookies_or_key_material_present": False,
    "person_or_account_identity_present": False,
    "protected_data_or_outcome_present": False,
    "scientific_result_present": False,
    "future_receipt_raw_bytes_present": False,
}


EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "state",
    "global_state",
    "package_kind",
    "reported_date",
    "authority_provenance",
    "live_immutable_input_bindings",
    "historical_snapshot_inputs",
    "candidate_identity",
    "registered_sources",
    "candidate_operation_roster",
    "candidate_selectors",
    "candidate_administrative_questions",
    "candidate_split_and_leakage_rules",
    "candidate_approval_gates",
    "candidate_escrow_controls",
    "future_observed_slots",
    "failure_and_state_contract",
    "gap_inventory",
    "checklist_effects",
    "scope_review",
    "publication_anonymity_boundary",
    "package_bindings",
    "record_sha256",
}


def _validate_no_absolute_paths(value: Any, key: str = "") -> None:
    if type(value) is dict:
        for child_key, child in value.items():
            _validate_no_absolute_paths(child, child_key)
    elif type(value) is list:
        for child in value:
            _validate_no_absolute_paths(child, key)
    elif type(value) is str and (key == "path" or key.endswith("_path")):
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValidationError("absolute or unsafe local path")


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for ordinal, role, path in (
        (0, "HUMAN_CANDIDATE_AND_GAP_AUDIT", HUMAN_PATH),
        (1, "READ_ONLY_VALIDATOR", VALIDATOR_PATH),
        (2, "HOSTILE_TEST", TEST_PATH),
    ):
        result.append(_binding(ordinal, role, path, _stable_read(root, path)))
    return result


def expected_record(root: Optional[Path] = None) -> Dict[str, Any]:
    """Construct the exact acyclic candidate record for local publication."""

    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": PACKAGE_KIND,
        "reported_date": REPORTED_DATE,
        "authority_provenance": dict(EXPECTED_AUTHORITY),
        "live_immutable_input_bindings": [dict(row) for row in LIVE_IMMUTABLE_BINDINGS],
        "historical_snapshot_inputs": [dict(row) for row in HISTORICAL_SNAPSHOT_INPUTS],
        "candidate_identity": dict(EXPECTED_IDENTITY),
        "registered_sources": [dict(row) for row in EXPECTED_SOURCES],
        "candidate_operation_roster": [dict(row) for row in EXPECTED_OPERATION_ROWS],
        "candidate_selectors": dict(EXPECTED_SELECTORS),
        "candidate_administrative_questions": list(EXPECTED_ADMIN_QUESTIONS),
        "candidate_split_and_leakage_rules": dict(EXPECTED_SPLIT),
        "candidate_approval_gates": dict(EXPECTED_APPROVALS),
        "candidate_escrow_controls": dict(EXPECTED_ESCROW),
        "future_observed_slots": dict(EXPECTED_FUTURE_SLOTS),
        "failure_and_state_contract": dict(EXPECTED_FAILURE),
        "gap_inventory": dict(EXPECTED_GAPS),
        "checklist_effects": dict(EXPECTED_CHECKLIST),
        "scope_review": dict(EXPECTED_SCOPE),
        "publication_anonymity_boundary": dict(EXPECTED_ANONYMITY),
        "package_bindings": _package_bindings(workspace),
        "record_sha256": "",
    }
    record["record_sha256"] = record_sha256(record)
    return record


def _validate_live_inputs(root: Path, record: Mapping[str, Any]) -> Dict[str, bytes]:
    _strict_equal(
        record["live_immutable_input_bindings"],
        [dict(row) for row in LIVE_IMMUTABLE_BINDINGS],
        "live immutable binding roster",
    )
    raws: Dict[str, bytes] = {}
    for expected in LIVE_IMMUTABLE_BINDINGS:
        raw = _stable_read(root, expected["path"])
        raws[expected["path"]] = raw
        observed = _binding(
            expected["ordinal"],
            expected["role"],
            expected["path"],
            raw,
            self_digest=expected.get("record_sha256"),
        )
        _strict_equal(observed, dict(expected), "live immutable input")

    prereg = json.loads(raws[PREREGISTRATION_PATH].decode("ascii"))
    if type(prereg) is not dict:
        raise ValidationError("preregistration type invalid")
    if prereg.get("state") != GLOBAL_STATE:
        raise ValidationError("preregistration state changed")
    if prereg.get("confirmatory_execution_authorized") is not False:
        raise ValidationError("preregistration authority changed")
    domains = prereg.get("domains")
    if type(domains) is not list or len(domains) != 2:
        raise ValidationError("domain roster changed")
    if [domain.get("source_url") for domain in domains] != [PHYSIONET_URL, RETAIL_URL]:
        raise ValidationError("registered source targets changed")
    if [domain.get("snapshot_version") for domain in domains] != [None, None]:
        raise ValidationError("snapshot version no longer null")
    if [domain.get("raw_snapshot_sha256") for domain in domains] != [None, None]:
        raise ValidationError("snapshot digest no longer null")
    if [domain.get("split_policy") for domain in domains] != [
        "PATIENT_DISJOINT",
        "CUSTOMER_DISJOINT_AND_TEMPORAL",
    ]:
        raise ValidationError("split policies changed")
    split = prereg.get("split_and_leakage_plan")
    if (
        type(split) is not dict
        or split.get("test_set_exclusion_permitted") is not False
        or split.get("train_validation_test_proportions_or_counts") is not None
        or split.get("retail_temporal_cutoff_and_window_rule") is not None
    ):
        raise ValidationError("preregistration split boundary changed")

    closure = json.loads(raws[CLOSURE_PATH].decode("ascii"))
    if type(closure) is not dict or _self_digest(closure) != closure.get("record_sha256"):
        raise ValidationError("closure self digest invalid")
    nulls = closure.get("null_projection", {})
    blockers = closure.get("blocker_projection", {})
    if (
        type(nulls) is not dict
        or type(blockers) is not dict
        or nulls.get("effective_total_unresolved_null_count") != 172
        or nulls.get("effective_preexecution_unresolved_null_count") != 166
        or nulls.get("effective_deferred_postexecution_unresolved_null_count") != 6
        or blockers.get("effective_unresolved_blocker_count") != 12
        or blockers.get("blockers_closed_by_closure") != 0
    ):
        raise ValidationError("closure projection changed")

    seal = json.loads(raws[SEAL_MACHINE_PATH].decode("ascii"))
    if type(seal) is not dict or _self_digest(seal) != seal.get("record_sha256"):
        raise ValidationError("seal self digest invalid")
    boundary = seal.get("authority_boundary", {})
    if (
        type(boundary) is not dict
        or boundary.get("connector_contact_authorized") is not False
        or boundary.get("network_access_authorized") is not False
        or boundary.get("test_data_acquisition_authorized") is not False
    ):
        raise ValidationError("seal authority boundary changed")

    static = json.loads(raws[STATIC_MACHINE_PATH].decode("ascii"))
    if type(static) is not dict or _self_digest(static) != static.get("record_sha256"):
        raise ValidationError("static selection self digest invalid")
    if static.get("state") != "SOLO_BLOCK2_STATIC_SELECTIONS_FROZEN_NO_EXTERNAL_CONTACT_AUTHORITY":
        raise ValidationError("static selection state changed")
    protocol = static.get("precontact_protocol_design", {})
    if (
        type(protocol) is not dict
        or protocol.get("populated_instance_present") is not False
        or protocol.get("populated_instance_admitted") is not False
        or protocol.get("future_observed_slots") != dict(EXPECTED_FUTURE_SLOTS)
    ):
        raise ValidationError("static protocol nonclaim changed")
    return raws


def _validate_operation_semantics(rows: Sequence[Mapping[str, Any]]) -> None:
    if [row["global_ordinal"] for row in rows] != [0, 1, 2, 3]:
        raise ValidationError("operation ordinals not contiguous")
    if [row["phase"] for row in rows] != ["ADMIN", "ADMIN", "DATA", "DATA"]:
        raise ValidationError("operation phases changed")
    if any(row["maximum_attempt_count"] != 1 for row in rows):
        raise ValidationError("operation maximum attempt changed")
    if any(row["authorized_retry_count"] != 0 for row in rows):
        raise ValidationError("operation retry changed")
    if any(row["currently_eligible"] is not False for row in rows):
        raise ValidationError("candidate row became eligible")
    if any(row["current_intent_receipt"] is not None for row in rows):
        raise ValidationError("candidate intent fabricated")
    if any(row["current_outcome_receipt"] is not None for row in rows):
        raise ValidationError("candidate outcome fabricated")
    for row in rows:
        target = row["exact_target"]
        if type(target) is not str or "*" in target or "TBD" in target or "AS_NEEDED" in target:
            raise ValidationError("wildcard or placeholder target")


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate exact candidate custody and return a privacy-safe status."""

    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    machine_raw = _stable_read(workspace, MACHINE_PATH)
    record = json.loads(machine_raw.decode("ascii"))
    if type(record) is not dict:
        raise ValidationError("machine record must be exact dict")
    if set(record) != EXPECTED_TOP_LEVEL_KEYS:
        raise ValidationError("top-level field roster mismatch")
    if canonical_machine_bytes(record) != machine_raw:
        raise ValidationError("machine record is not canonical")
    if type(record.get("record_sha256")) is not str:
        raise ValidationError("record self digest type invalid")
    if record["record_sha256"] != record_sha256(record):
        raise ValidationError("record self digest invalid")

    expected = expected_record(workspace)
    _strict_equal(record, expected, "candidate record")
    _validate_no_absolute_paths(record)
    _validate_operation_semantics(record["candidate_operation_roster"])
    _validate_live_inputs(workspace, record)

    if len(record["future_observed_slots"]) != 13:
        raise ValidationError("future slot count changed")
    if any(value is not None for value in record["future_observed_slots"].values()):
        raise ValidationError("future observation fabricated")
    if record["candidate_identity"]["precontact_population_blocked"] is not True:
        raise ValidationError("population blocker erased")
    if record["candidate_split_and_leakage_rules"]["retail"]["exact_temporal_rule_populated"] is not False:
        raise ValidationError("Retail rule overclaimed")
    if record["candidate_approval_gates"]["approval_contact_target_roster_complete"] is not False:
        raise ValidationError("approval contact roster overclaimed")
    if record["candidate_escrow_controls"]["independent_escrow_ready"] is not False:
        raise ValidationError("escrow overclaimed")

    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "candidate_control_predicate": True,
        "candidate_present": True,
        "populated_instance_present": False,
        "populated_instance_admitted": False,
        "precontact_population_blocked": True,
        "four_row_core_complete_for_admission": False,
        "approval_contact_roster_complete": False,
        "retail_exact_temporal_rule_populated": False,
        "future_observed_nonnull_count": 0,
        "external_contact_or_data_access_authorized": False,
        "unresolved_fields_closed": 0,
        "blockers_closed": 0,
        "effective_unresolved_field_count": 172,
        "effective_open_blocker_count": 12,
        "original_populated_instance_checkbox_closed": False,
        "validation": "PASS",
    }


__all__ = [
    "ValidationError",
    "canonical_machine_bytes",
    "expected_record",
    "record_sha256",
    "validate",
]
