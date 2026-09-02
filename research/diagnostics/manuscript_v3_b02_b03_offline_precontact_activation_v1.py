#!/usr/bin/env python3
"""Read-only validator for the B02/B03 offline activation preflight.

The validator reopens only a fixed closed-world roster of ordinary workspace
files.  It has no network, connector, subprocess, entropy, authority,
acquisition, dataset-opening, training, inference, release, or writer route.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any, Dict, Mapping, Tuple


SCHEMA = "heterodiff-b02-b03-offline-precontact-activation-v1"
STATE = "OFFLINE_ACTIVATION_PREFLIGHT_COMPLETE_AWAITING_HUMAN_OWNER_ROSTER"
PREDICATE = "B02_B03_JOINT_OFFLINE_ACTIVATION_PREFLIGHT_IMPLEMENTED_AND_QUALIFIED"
EXPECTED_RECORD_SHA256 = (
    "2a150e0b3037d01e6b311d9ab4c17157f20031f75b644a7c8778007c168b9fec"
)
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_b02_b03_offline_precontact_activation_v1.json"
)
ROOT = Path(__file__).resolve().parents[2]
MAX_FILE_BYTES = 2_000_000
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")

PACKAGE_PATHS = (
    "PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION.md",
    "src/heterodiff/data/two_domain_offline_precontact_activation.py",
    "tests/unit/test_two_domain_offline_precontact_activation.py",
    "src/heterodiff/data/physionet_2012_admission_preflight.py",
    "tests/unit/test_physionet_2012_admission_preflight.py",
    "src/heterodiff/data/online_retail_ii_admission_preflight.py",
    "tests/unit/test_online_retail_ii_admission_preflight.py",
)

FROZEN_PATHS = (
    "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md",
    "research/fixtures/"
    "manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json",
    "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md",
    "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json",
    "PROJECT_SOLO_BLOCK2_PRECONTACT_INSTANCE_CANDIDATE.md",
    "research/fixtures/"
    "manuscript_v3_solo_block2_precontact_instance_candidate_v1.json",
    "PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md",
    "research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json",
    "PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS.md",
    "research/fixtures/"
    "manuscript_v3_two_domain_governance_release_controls_v1.json",
    "PROJECT_REAL_DOMAIN_POWER_ALLOCATION_ROUTE.md",
    "research/fixtures/manuscript_v3_real_domain_power_allocation_route_v1.json",
    "PROJECT_PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN.md",
    "research/fixtures/"
    "manuscript_v3_physionet_patient_disjoint_split_design_v1.json",
    "PROJECT_RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN.md",
    "research/fixtures/"
    "manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json",
)

STAGES = (
    "DESIGN_FROZEN_AWAITING_POPULATED_PRECONTACT_INSTANCE",
    "PRECONTACT_INSTANCE_POPULATED_AWAITING_INDEPENDENT_REVIEW",
    "PRECONTACT_INSTANCE_REVIEWED_AWAITING_FRESH_ADMIN_CONTACT_AUTHORITY",
    "ADMIN_CONTACT_AUTHORIZED_AWAITING_DURABLE_INTENT",
    "ADMIN_CONTACT_INTENT_RESERVED_AWAITING_CONTACT",
    "ADMIN_CONTACT_OUTCOME_RECORDED_AWAITING_REQUIRED_APPROVALS",
    "APPROVALS_COMPLETE_AWAITING_REVIEWED_DATA_ACCESS_INSTANCE",
    "DATA_ACCESS_INSTANCE_REVIEWED_AWAITING_FRESH_DATA_ACCESS_AUTHORITY",
    "DATA_ACCESS_AUTHORIZED_AWAITING_DURABLE_INTENT",
    "DATA_ACCESS_INTENT_RESERVED_AWAITING_ACCESS",
    "SNAPSHOT_OBSERVED_AND_CUSTODIED_AWAITING_DETERMINISTIC_SPLIT",
    "SPLIT_ASSIGNED_AND_HELD_OUT_ESCROW_ACTIVE",
    "FINAL_OPENING_AWAITING_SEPARATE_AUTHORITY",
)

OWNER_ROLES = (
    "accountable_governance_owner",
    "license_privacy_or_institutional_approval_endpoint",
    "raw_snapshot_custodian",
    "deterministic_split_operator",
    "independent_heldout_escrow_custodian",
    "final_opening_approver",
    "key_and_acl_acceptance_authority",
    "retention_and_deletion_owner",
    "incident_response_owner",
)
OWNER_MANIFEST_KEYS = OWNER_ROLES + (
    "conflict_of_interest_determination_sha256",
)
F061_POLICY_NULL_SLOTS = (
    "f061_allocation_id",
    "f061_mode",
    "f061_values",
    "f061_denominator_is_null",
    "f061_denominator",
    "f061_minimum_counts",
    "f061_rounding_rule_id",
    "f061_power_requirement_id",
    "f061_allocation_proposal_sha256",
    "f061_power_review_receipt_sha256",
    "f061_power_review_accepted",
    "f061_allocation_definition_sha256",
)
OTHER_DEFINITION_NULL_SLOTS = (
    "physionet_selector_record_sha256",
    "retail_selector_record_sha256",
    "contact_target_roster_sha256",
    "contact_target_count",
    "approval_requirement_roster_sha256",
    "approval_receipt_validator_roster_sha256",
    "contact_roster_complete",
    "escrow_control_binding_sha256",
    "held_out_material_definition_sha256",
    "final_opening_rule_sha256",
    "append_only_log_schema_sha256",
)
EXTERNAL_REVIEW_NULL_SLOTS = (
    "external_review_receipt_sha256",
    "external_review_decision",
    "external_reviewer_principal_id",
)

FUTURE_OBSERVATIONS = (
    "administrative_contact_outcomes",
    "data_access_outcomes",
    "observed_snapshot_versions",
    "raw_snapshot_sha256_values",
    "snapshot_byte_counts",
    "etags_or_equivalents",
    "license_text_receipts",
    "governance_approval_receipts",
    "ethics_approval_receipts",
    "split_counts",
    "split_manifest_sha256",
    "escrow_receipts",
    "access_log_head_sha256",
)


class ValidationError(RuntimeError):
    """Raised when a package byte, custody rule, or semantic invariant fails."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative_parts(relative: object) -> Tuple[str, ...]:
    if type(relative) is not str:
        raise ValidationError("path must be a built-in string")
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts or str(path) != relative:
        raise ValidationError("path must be canonical, nonempty, and relative")
    if any(part in ("", ".", "..") for part in path.parts):
        raise ValidationError("unsafe path component")
    return path.parts


def _fingerprint(value: os.stat_result) -> Tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _canonical_root(root: Path) -> Path:
    supplied = Path(root)
    if not supplied.is_absolute():
        raise ValidationError("root must be absolute")
    try:
        lexical = supplied.absolute()
        resolved = supplied.resolve(strict=True)
        metadata = os.lstat(supplied)
    except OSError as exc:
        raise ValidationError("cannot resolve package root") from exc
    if lexical != resolved or stat.S_ISLNK(metadata.st_mode):
        raise ValidationError("root must be canonical and non-symlinked")
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValidationError("root must be a directory")
    return supplied


def _read_regular(
    root: Path,
    relative: object,
    *,
    expected_bytes: int | None = None,
    expected_sha256: str | None = None,
) -> bytes:
    canonical_root = _canonical_root(root)
    parts = _relative_parts(relative)
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    descriptors = []
    custody = []
    try:
        descriptor = os.open(canonical_root, directory_flags)
        descriptors.append(descriptor)
        custody.append(
            (canonical_root, os.lstat(canonical_root), os.fstat(descriptor))
        )
        for index, component in enumerate(parts[:-1], start=1):
            descriptor = os.open(component, directory_flags, dir_fd=descriptor)
            descriptors.append(descriptor)
            path = canonical_root.joinpath(*parts[:index])
            custody.append((path, os.lstat(path), os.fstat(descriptor)))
        file_flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            file_flags |= os.O_NOFOLLOW
        file_descriptor = os.open(parts[-1], file_flags, dir_fd=descriptor)
        descriptors.append(file_descriptor)
        before = os.fstat(file_descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValidationError(f"{relative} is not regular")
        if before.st_nlink != 1 or stat.S_IMODE(before.st_mode) != 0o644:
            raise ValidationError(f"{relative} has unsafe file custody")
        if before.st_size > MAX_FILE_BYTES:
            raise ValidationError(f"{relative} exceeds byte ceiling")
        chunks = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(file_descriptor, min(65536, remaining))
            if not chunk:
                raise ValidationError(f"short read for {relative}")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(file_descriptor, 1):
            raise ValidationError(f"growth during read for {relative}")
        after = os.fstat(file_descriptor)
        if _fingerprint(before) != _fingerprint(after):
            raise ValidationError(f"unstable read for {relative}")
        leaf = canonical_root.joinpath(*parts)
        if _fingerprint(after) != _fingerprint(os.lstat(leaf)):
            raise ValidationError(f"leaf identity changed for {relative}")
        for index, (path, path_before, fd_before) in enumerate(custody):
            if not (
                _fingerprint(path_before)
                == _fingerprint(fd_before)
                == _fingerprint(os.fstat(descriptors[index]))
                == _fingerprint(os.lstat(path))
            ):
                raise ValidationError(f"ancestor changed for {relative}")
    except OSError as exc:
        raise ValidationError(f"cannot safely read {relative}") from exc
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass
    data = b"".join(chunks)
    if expected_bytes is not None and (
        type(expected_bytes) is not int or len(data) != expected_bytes
    ):
        raise ValidationError(f"byte count mismatch for {relative}")
    digest = _sha256(data)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValidationError(f"raw hash mismatch for {relative}")
    if not data.endswith(b"\n"):
        raise ValidationError(f"{relative} lacks terminal LF")
    return data


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(data: bytes) -> Dict[str, Any]:
    try:
        record = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValidationError(f"forbidden JSON constant {value}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError("machine record is not strict UTF-8 JSON") from exc
    if type(record) is not dict:
        raise ValidationError("machine record must be an object")
    return record


def _semantic_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        raise ValidationError("machine record must be a built-in object")
    projection = dict(record)
    projection["record_sha256"] = None
    try:
        canonical = json.dumps(
            projection,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValidationError("machine record is not canonicalizable") from exc
    return _sha256((SCHEMA + "\0").encode("ascii") + canonical)


def _require_keys(
    value: object, expected: Tuple[str, ...], label: str
) -> Mapping[str, Any]:
    if type(value) is not dict or tuple(value) != expected:
        raise ValidationError(f"{label} has an invalid ordered field roster")
    return value


def _exact_value(actual: object, expected: object) -> bool:
    """Compare JSON semantics without Python's bool/int/float coercions."""

    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        actual_dict = actual
        expected_dict = expected
        if len(actual_dict) != len(expected_dict):
            return False
        return all(
            _exact_value(actual_key, expected_key)
            and _exact_value(actual_value, expected_value)
            for (actual_key, actual_value), (expected_key, expected_value)
            in zip(actual_dict.items(), expected_dict.items())
        )
    if type(expected) in (list, tuple):
        actual_sequence = actual
        expected_sequence = expected
        return len(actual_sequence) == len(expected_sequence) and all(
            _exact_value(actual_item, expected_item)
            for actual_item, expected_item in zip(
                actual_sequence, expected_sequence
            )
        )
    return actual == expected


def _validate_binding_roster(
    root: Path,
    bindings: object,
    expected_paths: Tuple[str, ...],
    label: str,
) -> None:
    if type(bindings) is not list or len(bindings) != len(expected_paths):
        raise ValidationError(f"{label} count mismatch")
    seen = []
    for ordinal, raw in enumerate(bindings):
        binding = _require_keys(
            raw,
            ("ordinal", "path", "bytes", "raw_sha256"),
            f"{label}[{ordinal}]",
        )
        if binding["ordinal"] != ordinal or type(binding["ordinal"]) is not int:
            raise ValidationError(f"{label} ordinal mismatch")
        path = binding["path"]
        if path != expected_paths[ordinal] or path in seen:
            raise ValidationError(f"{label} path roster mismatch")
        seen.append(path)
        digest = binding["raw_sha256"]
        if type(digest) is not str or SHA256_RE.fullmatch(digest) is None:
            raise ValidationError(f"{label} digest malformed")
        _read_regular(
            root,
            path,
            expected_bytes=binding["bytes"],
            expected_sha256=digest,
        )


def _expected_operation_roster() -> list[dict[str, Any]]:
    questions = [
        (
            "What is the canonical dataset identifier and current immutable "
            "version or revision for the registered target?"
        ),
        (
            "Is there exactly one immutable archive locator, with SHA-256 and "
            "byte count, for that version?"
        ),
        (
            "What exact license or terms govern access, storage, analysis, "
            "publication, redistribution, and retention?"
        ),
        "What account, authentication, or data-use-agreement requirements apply?",
        (
            "What governance, ethics, privacy, clinical, or institutional "
            "approvals are required before access?"
        ),
        (
            "What storage, deletion, retention, disclosure, and publication "
            "controls are mandatory?"
        ),
        (
            "What schema and timezone metadata are required to evaluate the "
            "frozen selector and split rules deterministically?"
        ),
    ]
    admin_success = (
        "EXACT_REGISTERED_TARGET_NO_REDIRECT_AND_ONE_CANONICAL_VERSION_REVISION_"
        "AND_EXACTLY_ONE_IMMUTABLE_ARCHIVE_LOCATOR_SHA256_BYTE_COUNT_AND_COMPLETE_"
        "LICENSE_GOVERNANCE_ACCESS_SCHEMA_TIMEZONE_REQUIREMENTS_RECEIPT"
    )
    data_success = (
        "EXACT_MATCHING_ADMIN_SUCCESS_AND_ALL_REQUIRED_APPROVAL_RECEIPTS_AND_"
        "SEPARATELY_REVIEWED_DATA_ACCESS_INSTANCE_AND_FRESH_EXACT_DATA_ACCESS_"
        "AUTHORITY_AND_DURABLE_INTENT_AND_ONE_CONTENT_ADDRESSED_ARCHIVE_MATCHING_"
        "VERSION_LOCATOR_SHA256_AND_BYTE_COUNT"
    )
    domains = (
        {
            "domain_id": "physionet-challenge-2012",
            "url": "https://physionet.org/content/challenge-2012/1.0.0/",
            "selector_identity": (
                "PHYSIONET_CHALLENGE_2012_VERSION_1_0_0_"
                "EXACT_REGISTERED_URL_SELECTOR_V1"
            ),
            "admin_operation_id": "PHYSIONET_ADMIN_METADATA_LICENSE_GOVERNANCE",
            "data_operation_id": "PHYSIONET_DATA_AUTHENTICATION_OR_DOWNLOAD",
        },
        {
            "domain_id": "online-retail-ii",
            "url": "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
            "selector_identity": (
                "UCI_DATASET_502_ONLINE_RETAIL_II_EXACT_REGISTERED_URL_SELECTOR_V1"
            ),
            "admin_operation_id": "RETAIL_ADMIN_METADATA_LICENSE_GOVERNANCE",
            "data_operation_id": "RETAIL_DATA_AUTHENTICATION_OR_DOWNLOAD",
        },
    )
    rows = []
    for ordinal, domain in enumerate(domains):
        rows.append(
            {
                "ordinal": ordinal,
                "operation_id": domain["admin_operation_id"],
                "domain_id": domain["domain_id"],
                "phase": "ADMIN",
                "exact_target": domain["url"],
                "target_derivation": "LITERAL_REGISTERED_SOURCE_URL",
                "selector_identity": domain["selector_identity"],
                "permitted_request_kind": (
                    "ADMIN_METADATA_LICENSE_GOVERNANCE_ONLY_NO_AUTH_NO_DOWNLOAD_NO_DATA"
                ),
                "administrative_questions": questions,
                "matching_admin_operation_id": None,
                "required_prior_receipts": [
                    "POPULATED_INSTANCE_REVIEW",
                    "FRESH_EXACT_ADMIN_CONTACT_AUTHORITY",
                    "DURABLE_INTENT",
                ],
                "authentication_permitted": False,
                "download_permitted": False,
                "data_opening_permitted": False,
                "protected_data_permitted": False,
                "maximum_attempt_count": 1,
                "retry_limit": 0,
                "redirect_limit": 0,
                "fallback_limit": 0,
                "current_execution_budget": 0,
                "success_predicate": admin_success,
                "terminal_disposition": "ADMIN_CONTACT_TERMINAL_NO_GO",
            }
        )
    for offset, domain in enumerate(domains, start=2):
        rows.append(
            {
                "ordinal": offset,
                "operation_id": domain["data_operation_id"],
                "domain_id": domain["domain_id"],
                "phase": "DATA",
                "exact_target": None,
                "target_derivation": (
                    "DETERMINISTIC_FROM_MATCHING_ADMIN_EXACT_SUCCESS_ONLY"
                ),
                "selector_identity": domain["selector_identity"],
                "permitted_request_kind": (
                    "DORMANT_DATA_OPERATION_NOT_AUTHORIZED_BY_OFFLINE_PACKAGE"
                ),
                "administrative_questions": [],
                "matching_admin_operation_id": domain["admin_operation_id"],
                "required_prior_receipts": [
                    "MATCHING_ADMIN_EXACT_SUCCESS",
                    "ALL_REQUIRED_APPROVAL_RECEIPTS",
                    "SEPARATELY_REVIEWED_DATA_ACCESS_INSTANCE",
                    "FRESH_EXACT_DATA_ACCESS_AUTHORITY",
                    "DURABLE_INTENT",
                ],
                "authentication_permitted": False,
                "download_permitted": False,
                "data_opening_permitted": False,
                "protected_data_permitted": False,
                "maximum_attempt_count": 1,
                "retry_limit": 0,
                "redirect_limit": 0,
                "fallback_limit": 0,
                "current_execution_budget": 0,
                "success_predicate": data_success,
                "terminal_disposition": "DATA_ACCESS_TERMINAL_NO_GO",
            }
        )
    return rows


def _validate_semantics(record: Mapping[str, Any]) -> None:
    expected_top = (
        "schema_version",
        "state",
        "authority_provenance",
        "package_bindings",
        "frozen_inputs",
        "operation_roster",
        "activation_contract",
        "execution_boundary",
        "shared_f061_policy_boundary",
        "other_unresolved_definition_slots",
        "external_review_slots",
        "domain_split_contract_boundary",
        "domain_readiness",
        "unresolved_owner_manifest",
        "future_observations",
        "closure_effect",
        "qualification_boundary",
        "record_sha256",
    )
    _require_keys(record, expected_top, "machine record")
    if not _exact_value(record["schema_version"], SCHEMA) or not _exact_value(
        record["state"], STATE
    ):
        raise ValidationError("schema/state mismatch")

    authority = _require_keys(
        record["authority_provenance"],
        (
            "normalized_visible_text",
            "normalized_visible_text_sha256",
            "offline_construction_and_review_authorized",
            "external_contact_or_browsing_authorized",
            "authentication_download_or_data_access_authorized",
            "institutional_determination_created",
            "identity_or_time_externally_authenticated",
        ),
        "authority_provenance",
    )
    if not _exact_value(authority, {
        "normalized_visible_text": "Okay, let's move forward then.",
        "normalized_visible_text_sha256": (
            "706de12ea5e317649aa6550fa4c7c53a4b0a19b369a3fe032d80f38f76872138"
        ),
        "offline_construction_and_review_authorized": True,
        "external_contact_or_browsing_authorized": False,
        "authentication_download_or_data_access_authorized": False,
        "institutional_determination_created": False,
        "identity_or_time_externally_authenticated": False,
    }):
        raise ValidationError("authority boundary mismatch")

    if not _exact_value(
        record["operation_roster"], _expected_operation_roster()
    ):
        raise ValidationError("operation roster mismatch")

    activation = _require_keys(
        record["activation_contract"],
        (
            "shared_core_schema_version",
            "forward_only_stages",
            "current_stage",
            "populated_instance_present",
            "independent_operational_admission_present",
            "fresh_admin_authority_present",
            "durable_intent_present",
            "data_rows_dormant",
            "terminal_no_retry",
            "strict_stage_skipping_refusal",
        ),
        "activation_contract",
    )
    if not _exact_value(activation, {
        "shared_core_schema_version": (
            "heterodiff-two-domain-offline-precontact-activation-v2"
        ),
        "forward_only_stages": list(STAGES),
        "current_stage": STAGES[0],
        "populated_instance_present": False,
        "independent_operational_admission_present": False,
        "fresh_admin_authority_present": False,
        "durable_intent_present": False,
        "data_rows_dormant": True,
        "terminal_no_retry": True,
        "strict_stage_skipping_refusal": True,
    }):
        raise ValidationError("activation contract mismatch")

    execution = _require_keys(
        record["execution_boundary"],
        (
            "operational_authority_present",
            "admin_contact_authority_present",
            "data_access_authority_present",
            "durable_intent_present",
            "network_or_contact_authorized",
            "authentication_authorized",
            "download_authorized",
            "data_opening_authorized",
            "split_execution_authorized",
            "escrow_activation_authorized",
            "admin_contact_attempt_budget",
            "data_access_attempt_budget",
            "snapshot_open_budget",
            "split_execution_budget",
            "escrow_activation_budget",
            "scientific_execution_budget",
        ),
        "execution_boundary",
    )
    if not _exact_value(execution, {
        "operational_authority_present": False,
        "admin_contact_authority_present": False,
        "data_access_authority_present": False,
        "durable_intent_present": False,
        "network_or_contact_authorized": False,
        "authentication_authorized": False,
        "download_authorized": False,
        "data_opening_authorized": False,
        "split_execution_authorized": False,
        "escrow_activation_authorized": False,
        "admin_contact_attempt_budget": 0,
        "data_access_attempt_budget": 0,
        "snapshot_open_budget": 0,
        "split_execution_budget": 0,
        "escrow_activation_budget": 0,
        "scientific_execution_budget": 0,
    }):
        raise ValidationError("execution boundary mismatch")

    f061_boundary = _require_keys(
        record["shared_f061_policy_boundary"],
        (
            "schema_version",
            "allowed_method_id",
            "retail_adapter_id",
            "retail_adapter_sha256",
            "physionet_adapter_id",
            "physionet_adapter_sha256",
            "f061_field_status",
            "unresolved_policy_slots",
            "shared_policy_present",
            "shared_policy_external_review_present",
            "shared_policy_is_exact_domain_allocation",
            "retail_native_proposal_requires_shared_policy_definition_binding",
            "retail_native_proposal_present",
            "physionet_natural_group_count_observed",
            "physionet_native_proposal_requires_shared_policy_definition_binding",
            "physionet_native_proposal_present",
            "physionet_resolved_counts_require_separate_external_review",
            "physionet_exact_count_external_review_present",
        ),
        "shared_f061_policy_boundary",
    )
    if not _exact_value(f061_boundary, {
        "schema_version": "heterodiff-two-domain-f061-shared-policy-v1",
        "allowed_method_id": "POWER_REVIEWED_EXACT_PROPORTIONS_HAMILTON_V1",
        "retail_adapter_id": (
            "SHARED_POLICY_TO_RETAIL_F061_PROPOSAL_ADAPTER_V1"
        ),
        "retail_adapter_sha256": (
            "c442a1a7ee95078d07852d600f7ea2c35ec52c309b6f97d9cbdba41374f878ee"
        ),
        "physionet_adapter_id": (
            "SHARED_POLICY_AND_NATURAL_GROUP_COUNT_TO_PHYSIONET_"
            "F061_PROPOSAL_ADAPTER_V1"
        ),
        "physionet_adapter_sha256": (
            "018def4ab7d7f991d4820da612489b5162d91d8c04e4231f3429295cb032a52b"
        ),
        "f061_field_status": "OPEN",
        "unresolved_policy_slots": {
            field: None for field in F061_POLICY_NULL_SLOTS
        },
        "shared_policy_present": False,
        "shared_policy_external_review_present": False,
        "shared_policy_is_exact_domain_allocation": False,
        "retail_native_proposal_requires_shared_policy_definition_binding": True,
        "retail_native_proposal_present": False,
        "physionet_natural_group_count_observed": False,
        "physionet_native_proposal_requires_shared_policy_definition_binding": True,
        "physionet_native_proposal_present": False,
        "physionet_resolved_counts_require_separate_external_review": True,
        "physionet_exact_count_external_review_present": False,
    }):
        raise ValidationError("shared F061 policy boundary mismatch")

    other_definitions = _require_keys(
        record["other_unresolved_definition_slots"],
        OTHER_DEFINITION_NULL_SLOTS,
        "other unresolved definition slots",
    )
    if not _exact_value(
        other_definitions,
        {field: None for field in OTHER_DEFINITION_NULL_SLOTS},
    ):
        raise ValidationError("other definition slots must remain strict null")

    external_review = _require_keys(
        record["external_review_slots"],
        EXTERNAL_REVIEW_NULL_SLOTS,
        "external review slots",
    )
    if not _exact_value(
        external_review,
        {field: None for field in EXTERNAL_REVIEW_NULL_SLOTS},
    ):
        raise ValidationError("external review slots must remain strict null")

    split_boundary = _require_keys(
        record["domain_split_contract_boundary"],
        ("physionet-challenge-2012", "online-retail-ii"),
        "domain_split_contract_boundary",
    )
    if not _exact_value(split_boundary, {
        "physionet-challenge-2012": {
            "active_contract_id": (
                "PHYSIONET_PATIENT_HASH_EXPLICIT_F061_HAMILTON_V1"
            ),
            "active_contract_sha256": (
                "32651b654a1b11ceb256f4f6cc6df1ff567d34538c3c2c6033d9acf1fc020b2d"
            ),
            "active_implementation_sha256": (
                "f9bed4ebcc86e692977ce7a49da1901c15f20a056757ad14fab98e16c81d37a8"
            ),
            "historical_design_id": (
                "PHYSIONET_PATIENT_HASH_HAMILTON_70_15_15_V1"
            ),
            "historical_design_raw_sha256": (
                "a9fc01ae42ba7942e6c61def5120d6497b74fc99c82b0c5b68188f221b4b68a8"
            ),
            "active_contract_runtime_recomputed": True,
        },
        "online-retail-ii": {
            "active_contract_id": (
                "RETAIL_F060_SOURCE_CIVIL_SHARED_F061_INTEGRATED_REPLAY_V3"
            ),
            "active_contract_sha256": (
                "b1a4fef836a50987b5d723e2bd133605bd907b4d7904f7cd6e87ca1d83077659"
            ),
            "historical_design_id": (
                "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_HAMILTON_70_15_15_V1"
            ),
            "historical_design_raw_sha256": (
                "b27086c5979d2f7018b4b8b50b3fffacf03b3fe2691d60567bc42b179d53e98b"
            ),
            "legacy_misbound_f105_semantic_sha256": (
                "14cefa1f0b8e300c26373a9ffdfc01ede99f783a326feb78c68166d187168b52"
            ),
            "legacy_misbound_digest_is_split_contract": False,
            "active_contract_runtime_recomputed": True,
        },
    }):
        raise ValidationError("domain split contract boundary mismatch")

    readiness = _require_keys(
        record["domain_readiness"],
        ("physionet-challenge-2012", "online-retail-ii"),
        "domain_readiness",
    )
    expected_readiness = {
        "physionet-challenge-2012": {
            "implemented_offline_controls": [
                "snapshot_and_archive_receipt_validation",
                "explicit_f061_patient_disjoint_split",
                "duplicate_and_near_duplicate_audit_validation",
                "support_receipt_validation",
                "thirteen_component_six_receipt_admission",
            ],
            "open_field_ids": [
                "F019",
                "F020",
                "F022",
                "F033",
                "F034",
                "F058",
                "F061",
            ],
            "actual_domain_admission_present": False,
        },
        "online-retail-ii": {
            "implemented_offline_controls": [
                "snapshot_and_schema_receipt_validation",
                "source_civil_f060_v2_explicit_f061_customer_temporal_split",
                "duplicate_and_near_duplicate_audit_validation",
                "accepted_positive_dominated_support_policy_receipt_validation",
                "thirteen_component_six_receipt_admission",
            ],
            "open_field_ids": [
                "F038",
                "F039",
                "F041",
                "F053",
                "F054",
                "F059",
                "F061",
            ],
            "actual_domain_admission_present": False,
        },
    }
    if not _exact_value(readiness, expected_readiness):
        raise ValidationError("domain readiness mismatch")

    owners = _require_keys(
        record["unresolved_owner_manifest"],
        OWNER_MANIFEST_KEYS,
        "owner manifest",
    )
    for role in OWNER_ROLES:
        role_binding = _require_keys(
            owners[role],
            ("principal_id", "acceptance_sha256"),
            f"owner manifest {role}",
        )
        if not _exact_value(
            role_binding,
            {"principal_id": None, "acceptance_sha256": None},
        ):
            raise ValidationError("owner role bindings must remain strict null")
    if owners["conflict_of_interest_determination_sha256"] is not None:
        raise ValidationError("owner COI determination must remain strict null")
    observations = _require_keys(
        record["future_observations"], FUTURE_OBSERVATIONS, "future observations"
    )
    if any(value is not None for value in observations.values()):
        raise ValidationError("future observations must remain strict null")

    closure = _require_keys(
        record["closure_effect"],
        (
            "completed_enabling_timetable_item",
            "field_count_delta",
            "blocker_count_delta",
            "b02_closed",
            "b03_closed",
            "seven_operational_tasks_closed_count",
            "formal_test_count_delta",
            "scientific_result_count_delta",
            "tracker_update_permitted_after_independent_go",
        ),
        "closure_effect",
    )
    if not _exact_value(closure, {
        "completed_enabling_timetable_item": PREDICATE,
        "field_count_delta": 0,
        "blocker_count_delta": 0,
        "b02_closed": False,
        "b03_closed": False,
        "seven_operational_tasks_closed_count": 0,
        "formal_test_count_delta": 0,
        "scientific_result_count_delta": 0,
        "tracker_update_permitted_after_independent_go": True,
    }):
        raise ValidationError("closure boundary mismatch")

    qualification = _require_keys(
        record["qualification_boundary"],
        (
            "synthetic_inputs_only",
            "real_dataset_opened_or_parsed",
            "network_connector_or_subprocess_route",
            "credential_or_secret_route",
            "entropy_training_inference_result_or_release_route",
            "validator_and_tests_outside_semantic_self_binding",
        ),
        "qualification_boundary",
    )
    if not _exact_value(qualification, {
        "synthetic_inputs_only": True,
        "real_dataset_opened_or_parsed": False,
        "network_connector_or_subprocess_route": False,
        "credential_or_secret_route": False,
        "entropy_training_inference_result_or_release_route": False,
        "validator_and_tests_outside_semantic_self_binding": True,
    }):
        raise ValidationError("qualification boundary mismatch")


def validate_package(root: Path = ROOT) -> Mapping[str, Any]:
    """Validate fixed bytes and semantics without performing any mutation."""

    canonical_root = _canonical_root(root)
    raw = _read_regular(canonical_root, MACHINE_PATH)
    record = _load_json(raw)
    _validate_semantics(record)
    digest = _semantic_sha256(record)
    if (
        record["record_sha256"] != EXPECTED_RECORD_SHA256
        or digest != EXPECTED_RECORD_SHA256
    ):
        raise ValidationError("machine semantic digest mismatch")
    _validate_binding_roster(
        canonical_root, record["package_bindings"], PACKAGE_PATHS, "package bindings"
    )
    _validate_binding_roster(
        canonical_root, record["frozen_inputs"], FROZEN_PATHS, "frozen inputs"
    )
    return {
        "state": STATE,
        "record_sha256": digest,
        "package_binding_count": len(PACKAGE_PATHS),
        "frozen_input_count": len(FROZEN_PATHS),
        "completed_enabling_timetable_item": PREDICATE,
        "field_count_delta": 0,
        "blocker_count_delta": 0,
        "operational_task_count_delta": 0,
    }


if __name__ == "__main__":
    print(json.dumps(validate_package(), sort_keys=True, separators=(",", ":")))
