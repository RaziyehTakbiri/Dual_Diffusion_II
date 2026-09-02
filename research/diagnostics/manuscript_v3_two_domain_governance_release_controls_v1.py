"""Read-only validator for the two-domain governance/release controls."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-two-domain-governance-release-controls-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS_FROZEN_PREEXECUTION"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
PACKAGE_KIND = "ADDITIVE_OFFLINE_DATA_GOVERNANCE_AND_POSTEXECUTION_PLAN_FIELD_CLOSURE"
CONTROL_PREDICATE = "TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROL_PLANS_FROZEN_NO_EXTERNAL_COMPLETION"
REPORTED_DATE = "2026-09-01"

SOURCE_PATH = "src/heterodiff/data/two_domain_governance_release_controls.py"
HUMAN_PATH = "PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS.md"
MACHINE_PATH = "research/fixtures/manuscript_v3_two_domain_governance_release_controls_v1.json"
VALIDATOR_PATH = "research/diagnostics/manuscript_v3_two_domain_governance_release_controls_v1.py"
TEST_PATH = "tests/unit/test_manuscript_v3_two_domain_governance_release_controls_v1.py"
PACKAGE_ROSTER = (SOURCE_PATH, HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)
PACKAGE_BINDING_ROLES = ((SOURCE_PATH, "pure_source"), (HUMAN_PATH, "human_contract"),
                         (VALIDATOR_PATH, "validator"), (TEST_PATH, "hostile_tests"))
PREDECESSOR_BINDINGS = (
    ("manuscript_v3/execution_preregistration.md", "accepted_preregistration", 22491, "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e"),
    ("research/fixtures/manuscript_v3_execution_preregistration_v1.json", "accepted_preregistration_machine", 39771, "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706"),
    ("manuscript_v3/execution_preregistration_preexecution_closure_v2.md", "accepted_preregistration_closure", 14938, "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d"),
    ("research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json", "accepted_preregistration_closure_machine", 24571, "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db"),
    ("src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py", "accepted_f105_engine", 25342, "567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881"),
    ("PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md", "accepted_f105_contract", 15242, "5d495ee917357a763e53b73cd40008a02da32918c7cb83503cbd0df851227cef"),
    ("research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json", "accepted_f105_machine", 23899, "560b6275a4e30d188cc35ed8190118ba01ad8fc3bacc9199daf5b6f305cc96c9"),
    ("research/diagnostics/manuscript_v3_f105_two_domain_cks_metric_instance_v1.py", "accepted_f105_validator", 37339, "ca99e505669ca77d632e1cbf1dc5a6a3f5523edc71b7b8e90456b30975d25064"),
    ("tests/unit/test_manuscript_v3_f105_two_domain_cks_metric_instance_v1.py", "accepted_f105_tests", 17542, "f86daa76c8e0492e614107c7f777a914da826356d71edf09d2a59ddcfbbc6a82"),
    ("PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE_INDEPENDENT_REVIEW.md", "accepted_f105_independent_review", 5932, "368fd5444b958c5eef1a62b25ad45062415a6c396863e33864f63a81356171a3"),
)

FIELDS_CLOSED = (
    "F021", "F025", "F032", "F035", "F036", "F037",
    "F040", "F044", "F052", "F055", "F056", "F057",
    "F163", "F164", "F165", "F166", "F167",
)
PRE_FIELDS_CLOSED = tuple(field for field in FIELDS_CLOSED if field not in {"F164", "F165"})
POST_FIELDS_CLOSED = ("F164", "F165")

ADMISSION_COMPONENTS = (
    "raw_format_failures",
    "identity_failures",
    "unknown_or_unbound_event_type_rows",
    "missing_or_invalid_required_value_rows",
    "event_transform_collisions",
    "horizon_violations",
    "cap_or_overflow_violations",
    "row_exclusions",
    "natural_group_exclusions",
    "natural_group_split_overlaps",
    "split_contract_failures",
    "clean_kernel_normalization_failures",
    "observation_subset_failures",
)

REQUIRED_RECEIPTS = (
    "snapshot_hash_verified",
    "license_access_record_verified",
    "governance_approval_verified",
    "complete_split_manifest_verified",
    "duplicate_and_near_duplicate_audit_verified",
    "observation_reference_and_support_receipt_verified",
)

PLAN_IDS = {
    "F163": "TWO_DOMAIN_DATA_LICENSE_COMPLIANCE_PLAN_V1",
    "F164": "CODE_MODEL_ARTIFACT_RELEASE_PLAN_V1",
    "F165": "DOUBLE_BLIND_SUBMISSION_ANONYMIZATION_PLAN_V1",
    "F166": "PHYSIONET_CLINICAL_GOVERNANCE_AND_INTERPRETATION_PLAN_V1",
    "F167": "RETAIL_PRIVACY_DUPLICATE_EXPOSURE_MEMBERSHIP_PLAN_V1",
}


class ValidationError(RuntimeError):
    """Raised on any malformed, drifting, or overclaiming package state."""


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return hashlib.sha256(RECORD_DOMAIN + canonical_json_bytes(payload)).hexdigest()


def _pairs_no_duplicates(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _fingerprint(value: os.stat_result) -> Tuple[int, int, int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink, value.st_size, value.st_mtime_ns)


def _canonical_root(root: Path) -> Path:
    root = Path(root)
    if not root.is_absolute() or root != root.resolve(strict=True) or stat.S_ISLNK(os.lstat(root).st_mode):
        raise ValidationError("root must be an absolute canonical non-symlink directory")
    return root


def _read_regular_no_follow(root: Path, relative: str) -> Tuple[bytes, os.stat_result]:
    root = _canonical_root(root)
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(part in ("", ".", "..") for part in parts):
        raise ValidationError(f"unsafe relative path: {relative}")
    flags_directory = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    flags_file = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptors: List[int] = []
    custody: List[Tuple[Path, os.stat_result, os.stat_result]] = []
    try:
        current = os.open(os.fspath(root), flags_directory)
        descriptors.append(current)
        custody.append((root, os.lstat(root), os.fstat(current)))
        for part in parts[:-1]:
            current = os.open(part, flags_directory, dir_fd=current)
            descriptors.append(current)
            path = root.joinpath(*parts[:len(custody)])
            custody.append((path, os.lstat(path), os.fstat(current)))
        file_descriptor = os.open(parts[-1], flags_file, dir_fd=current)
        descriptors.append(file_descriptor)
        before = os.fstat(file_descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValidationError(f"not a regular file: {relative}")
        chunks: List[bytes] = []
        while True:
            chunk = os.read(file_descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(file_descriptor)
        leaf_path = root / relative
        if _fingerprint(before) != _fingerprint(after) or _fingerprint(after) != _fingerprint(os.lstat(leaf_path)):
            raise ValidationError(f"file changed during read: {relative}")
        for path, path_before, fd_before in custody:
            if _fingerprint(path_before) != _fingerprint(fd_before) or _fingerprint(fd_before) != _fingerprint(os.fstat(descriptors[custody.index((path, path_before, fd_before))])) or _fingerprint(fd_before) != _fingerprint(os.lstat(path)):
                raise ValidationError(f"ancestor changed during read: {relative}")
        return b"".join(chunks), after
    except OSError as exc:
        raise ValidationError(f"cannot safely read {relative}: {exc}") from exc
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _binding(root: Path, relative: str, role: str) -> Dict[str, Any]:
    raw, metadata = _read_regular_no_follow(root, relative)
    if stat.S_IMODE(metadata.st_mode) != 0o644:
        raise ValidationError(f"unexpected mode for {relative}")
    if metadata.st_nlink != 1:
        raise ValidationError(f"unexpected link count for {relative}")
    if not raw.endswith(b"\n"):
        raise ValidationError(f"missing terminal LF: {relative}")
    return {
        "path": relative,
        "role": role,
        "bytes": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": True,
    }


def _binding_from_raw(relative: str, role: str, raw: bytes) -> Dict[str, Any]:
    return {"path": relative, "role": role, "bytes": len(raw),
            "raw_sha256": hashlib.sha256(raw).hexdigest(), "mode_octal": "0644",
            "nlink": 1, "terminal_lf": True}


def _closure(field_id: str, pointer: str, value: object) -> Dict[str, Any]:
    return {
        "field_id": field_id,
        "json_pointer": pointer,
        "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_CONTROL_FREEZE",
        "value": value,
    }


def field_closures() -> List[Dict[str, Any]]:
    observation = {
        "observation_semantics_id": "UNORDERED_OCCURRENCE_SUBCONFIGURATION_WITH_PRIVATE_ORDINAL_IDENTITY_V1",
        "kernel_id": "OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1",
        "per_occurrence_detection_probability": "1/2",
        "exact_subset_mass": "2^(-SOURCE_OCCURRENCE_COUNT)",
        "occurrence_ordinal_rule_by_domain": {
            "physionet-challenge-2012": "ZERO_BASED_ADMITTED_TIME_SERIES_ROW_POSITION_IN_ORIGINAL_RECORD_FILE_ORDER",
            "online-retail-ii": "FROZEN_CONTIGUOUS_SOURCE_WORKBOOK_ROW_ORDINAL",
        },
        "retained_event_map": "IDENTITY_TYPE_TIME_MARK_AND_MULTIPLICITY",
        "confusion": "NONE",
        "clutter": "ZERO",
        "timestamp_jitter": "ZERO",
        "value_noise": "ZERO",
        "imputation_deduplication_or_synthesis": "FORBIDDEN",
    }
    statistic = {
        "statistic_id": "MAX_HARD_TRAIN_ONLY_ADMISSION_VIOLATION_COUNT_V1",
        "ordered_component_counts": list(ADMISSION_COMPONENTS),
        "scope": "METHOD_BLIND_TRAINING_ONLY_AND_CUSTODY_METADATA",
    }
    threshold = {
        "threshold_id": "ALL_COMPONENTS_AND_MAX_EXACTLY_ZERO_V1",
        "required_receipts": list(REQUIRED_RECEIPTS),
        "missing_receipt_or_positive_component": "NO_GO",
        "retry_resplit_topup_or_post_outcome_repair": "FORBIDDEN",
    }
    phys_license = {
        "record_id": "PHYSIONET_CHALLENGE_2012_ODC_BY_1_0_PUBLIC_ACCESS_RECORD_V1",
        "source_url": "https://physionet.org/content/challenge-2012/1.0.0/",
        "license_name": "Open Data Commons Attribution License v1.0",
        "license_short_name": "ODC-By-1.0",
        "license_url": "https://physionet.org/content/challenge-2012/view-license/1.0.0/",
        "access_policy_observation": "ANYONE_MAY_ACCESS_FILES_SUBJECT_TO_SPECIFIED_LICENSE",
        "page_bytes_or_transport_hash_claimed": False,
        "governance_approval_inferred": False,
    }
    retail_license = {
        "record_id": "UCI_ONLINE_RETAIL_II_CC_BY_4_0_ACCESS_RECORD_V1",
        "source_url": "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
        "dataset_id": 502,
        "doi": "10.24432/C5CG6D",
        "file_name": "online_retail_II.xlsx",
        "license_name": "Creative Commons Attribution 4.0 International",
        "license_short_name": "CC-BY-4.0",
        "page_bytes_or_transport_hash_claimed": False,
        "governance_approval_inferred": False,
    }
    plans = {
        "F163": {
            "plan_id": PLAN_IDS["F163"],
            "required_controls": [
                "BIND_OFFICIAL_SOURCE_LICENSE_CITATION_RAW_BYTES_AND_SHA256_BEFORE_USE",
                "OBTAIN_APPLICABLE_GOVERNANCE_DETERMINATION_BEFORE_USE",
                "INTERNAL_RESTRICTED_RAW_NORMALIZED_IDENTIFIER_AND_SPLIT_CUSTODY",
                "PRESERVE_PHYSIONET_ODC_BY_NOTICE_URI_AND_ATTRIBUTION",
                "PRESERVE_UCI_DOI_CC_BY_NOTICE_LINK_AND_ATTRIBUTION",
                "INVENTORY_EVERY_THIRD_PARTY_LICENSE_AND_REDISTRIBUTION_CLASS",
                "MISSING_CONFLICTING_OR_UNAPPROVED_TERM_IS_NO_GO",
            ],
        },
        "F164": {
            "plan_id": PLAN_IDS["F164"],
            "release_classes": [
                "PUBLIC_PROJECT_CODE", "PUBLIC_CONFIG_OR_SCHEMA",
                "PUBLIC_AGGREGATE_RESULT", "PUBLIC_MODEL_CANDIDATE",
                "INTERNAL_RESTRICTED", "NEVER_RELEASE",
            ],
            "required_gates": [
                "LICENSE_ATTRIBUTION_REVIEW", "PRIVACY_REVIEW",
                "MEMBERSHIP_INFERENCE_REVIEW", "ABSOLUTE_PATH_SCAN",
                "SECRET_SCAN", "IDENTITY_SCAN", "VENUE_ANONYMITY_SCAN",
                "FINAL_OWNER_RELEASE_APPROVAL",
            ],
            "release_performed": False,
        },
        "F165": {
            "plan_id": PLAN_IDS["F165"],
            "scan_passes_required": 2,
            "rescan_after_any_change": True,
            "scan_classes": [
                "AUTHOR_AFFILIATION_CONTACT_AND_ACKNOWLEDGEMENT",
                "PATH_USERNAME_HOST_JOB_WORKSPACE_AND_CREDENTIAL",
                "FILENAME_COMMENT_HISTORY_DOCUMENT_IMAGE_AND_ARCHIVE_METADATA",
                "VENUE_SPECIFIC_CITATION_AND_SELF_REFERENCE",
                "SCANNED_TO_UPLOAD_BYTE_IDENTITY",
            ],
            "actual_scan_performed": False,
        },
        "F166": {
            "plan_id": PLAN_IDS["F166"],
            "required_controls": [
                "APPLICABLE_ACCOUNTABLE_INSTITUTION_DETERMINATION_BEFORE_USE",
                "LEAST_PRIVILEGE_RETENTION_DELETION_AND_INCIDENT_ROUTE",
                "NO_REIDENTIFICATION_CONTACT_OR_PATIENT_LEVEL_RELEASE",
                "AGGREGATE_ONLY_AFTER_PRIVACY_AND_CELL_DISCLOSURE_REVIEW",
                "RETROSPECTIVE_NONDIAGNOSTIC_NONTREATMENT_NONDEPLOYMENT_LANGUAGE",
                "NO_UNSUPPORTED_CAUSAL_CLINICAL_UTILITY_TRANSPORTABILITY_OR_EQUITY_CLAIM",
                "CLINICAL_INTERPRETATION_REVIEW_BEFORE_CLAIM_PROMOTION",
            ],
            "actual_determination_or_approval_present": False,
        },
        "F167": {
            "plan_id": PLAN_IDS["F167"],
            "minimum_public_aggregate_natural_groups": 20,
            "required_controls": [
                "NO_RAW_NORMALIZED_IDENTIFIER_TRACE_ROW_OUTPUT_OR_NEAREST_NEIGHBOR_RELEASE",
                "DUPLICATE_NEAR_DUPLICATE_GROUP_TEMPORAL_RARE_PATTERN_AND_TEXT_AUDITS",
                "CROSS_TABLE_DIFFERENCING_AND_COMPOSITION_REVIEW",
                "MODEL_WITHHELD_UNTIL_MEMBERSHIP_ATTRIBUTE_EXTRACTION_AND_CANARY_AUDITS_PASS",
                "MISSING_CUSTOMER_ID_OR_REQUIRED_EXCLUSION_IS_NO_GO",
            ],
            "actual_privacy_or_model_release_audit_present": False,
        },
    }
    return [
        _closure("F021", "/domains/0/license_and_access_record", phys_license),
        _closure("F025", "/domains/0/observation_semantics", observation["observation_semantics_id"]),
        _closure("F032", "/domains/0/clean_observation_kernel", observation),
        _closure("F035", "/domains/0/detection_noise_confusion_clutter_rule", observation),
        _closure("F036", "/domains/0/method_blind_training_only_admission_statistic", statistic),
        _closure("F037", "/domains/0/method_blind_training_only_admission_threshold", threshold),
        _closure("F040", "/domains/1/license_and_access_record", retail_license),
        _closure("F044", "/domains/1/observation_semantics", observation["observation_semantics_id"]),
        _closure("F052", "/domains/1/clean_observation_kernel", observation),
        _closure("F055", "/domains/1/detection_noise_confusion_clutter_rule", observation),
        _closure("F056", "/domains/1/method_blind_training_only_admission_statistic", statistic),
        _closure("F057", "/domains/1/method_blind_training_only_admission_threshold", threshold),
        _closure("F163", "/ethics_release_and_review_plan/data_license_compliance_plan", plans["F163"]),
        _closure("F164", "/ethics_release_and_review_plan/code_model_and_artifact_release_plan", plans["F164"]),
        _closure("F165", "/ethics_release_and_review_plan/submission_anonymization_plan", plans["F165"]),
        _closure("F166", "/ethics_release_and_review_plan/physionet_clinical_governance_and_interpretation_plan", plans["F166"]),
        _closure("F167", "/ethics_release_and_review_plan/retail_privacy_duplicate_exposure_and_membership_inference_plan", plans["F167"]),
    ]


def _expected_record_from_raws(raws: Mapping[str, bytes]) -> Dict[str, Any]:
    bindings = [_binding_from_raw(path, role, raws[path]) for path, role in PACKAGE_BINDING_ROLES]
    predecessor_bindings = [
        {"path": path, "role": role, "bytes": size, "raw_sha256": digest,
         "mode_octal": "0644", "nlink": 1, "terminal_lf": True}
        for path, role, size, digest in PREDECESSOR_BINDINGS
    ]
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": PACKAGE_KIND,
        "control_predicate": CONTROL_PREDICATE,
        "reported_date": REPORTED_DATE,
        "field_closures": field_closures(),
        "field_delta": {
            "field_ids": list(FIELDS_CLOSED),
            "pre_execution": len(PRE_FIELDS_CLOSED),
            "post_execution": len(POST_FIELDS_CLOSED),
            "total": len(FIELDS_CLOSED),
            "blockers_closed": 0,
        },
        "additive_count_transition": {
            "accepted_predecessor": "F105_AND_PREREGISTRATION_ACCEPTED_FROZEN_BYTES",
            "before": {"pre_execution_open": 122, "pre_execution_closed": 44,
                       "post_execution_open": 3, "post_execution_closed": 3,
                       "total_open": 125, "total_closed": 47},
            "after": {"pre_execution_open": 107, "pre_execution_closed": 59,
                      "post_execution_open": 1, "post_execution_closed": 5,
                      "total_open": 108, "total_closed": 64},
            "delta": {"pre_execution_open": -15, "pre_execution_closed": 15,
                      "post_execution_open": -2, "post_execution_closed": 2,
                      "total_open": -17, "total_closed": 17, "blockers_closed": 0},
        },
        "remaining_open_requirements": {
            "B02": ["F019", "F020", "F022", "F033", "F034", "F058", "ACTUAL_DOMAIN_ADMISSION"],
            "B03": ["F038", "F039", "F041", "F053", "F054", "F059", "F061", "ACTUAL_DOMAIN_ADMISSION"],
            "B09": ["ACTUAL_APPLICABLE_APPROVALS_OR_DETERMINATIONS", "ACCOUNTABLE_OWNER_PLAN_ACCEPTANCE"],
            "B10": ["FINAL_VENUE_PACKAGE", "POPULATED_RELEASE_MANIFEST", "ACTUAL_SCANS_FINDINGS_AND_DISPOSITIONS", "ACTUAL_RELEASE_DECISION"],
            "B11": ["F169", "ADMITTED_INDEPENDENT_IDENTITIES_AND_APPOINTMENTS", "FINAL_REPORTS_AND_DISPOSITIONS", "OBSERVED_CLEAN_ROOM_REPRODUCTION"],
        },
        "blocker_assessment": {
            "B02": "OPEN_EVENT_DEPENDENT",
            "B03": "OPEN_EVENT_DEPENDENT",
            "B09": "OPEN_EXTERNAL_DETERMINATION_DEPENDENT",
            "B10": "OPEN_FINAL_PACKAGE_AND_SCAN_DEPENDENT",
            "B11": "OPEN_INDEPENDENT_REPORT_AND_CLEAN_ROOM_DEPENDENT",
            "closable_now_count": 0,
        },
        "project_effects_and_nonclaims": {
            "network_or_person_contact_performed": False,
            "authentication_or_protected_data_access_performed": False,
            "dataset_acquired_opened_parsed_or_split": False,
            "raw_snapshot_hash_created": False,
            "governance_legal_ethics_or_privacy_approval_created": False,
            "scientific_entropy_training_runtime_or_result_inspection_performed": False,
            "release_anonymity_scan_or_submission_performed": False,
            "audit_report_or_clean_room_reproduction_created": False,
            "tracker_or_evidence_ledger_edited": False,
            "formal_test_result_claim_or_blocker_closed": False,
        },
        "qualification_boundary": {
            "official_page_semantics_not_page_byte_or_transport_receipts": True,
            "pure_source_has_no_writer_network_subprocess_entropy_or_release_route": True,
            "self_validation_is_not_independent_acceptance": True,
            "independent_acceptance_required_before_field_registration": True,
        },
        "package_file_roster": list(PACKAGE_ROSTER),
        "package_bindings_excluding_machine_self": bindings,
        "accepted_predecessor_bindings": predecessor_bindings,
        "machine_self_binding": {
            "path": MACHINE_PATH,
            "semantic_self_digest_field": "record_sha256",
            "raw_self_hash_embedded": False,
        },
    }
    record["record_sha256"] = record_sha256(record)
    return record


def expected_record(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    root = _canonical_root(Path(root))
    raws = {path: _read_regular_no_follow(root, path)[0] for path, _ in PACKAGE_BINDING_ROLES}
    for path, _, size, digest in PREDECESSOR_BINDINGS:
        raw, metadata = _read_regular_no_follow(root, path)
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest or stat.S_IMODE(metadata.st_mode) != 0o644 or metadata.st_nlink != 1 or not raw.endswith(b"\n"):
            raise ValidationError(f"accepted predecessor mismatch: {path}")
    return _expected_record_from_raws(raws)


def _load_machine(root: Path) -> Tuple[Dict[str, Any], bytes]:
    raw, _ = _read_regular_no_follow(root, MACHINE_PATH)
    try:
        decoded = json.loads(raw.decode("ascii"), object_pairs_hook=_pairs_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid machine JSON: {exc}") from exc
    if type(decoded) is not dict:
        raise ValidationError("machine record must be an exact object")
    return decoded, raw


def _load_source_namespace(raw: bytes) -> Dict[str, Any]:
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError("pure source is not UTF-8") from exc
    try:
        tree = ast.parse(source, SOURCE_PATH, "exec")
    except SyntaxError as exc:
        raise ValidationError(f"pure source syntax error: {exc}") from exc
    required = {
        "OBSERVATION_KERNEL_ID", "ADMISSION_STATISTIC_ID", "ADMISSION_THRESHOLD_ID",
        "ADMISSION_COMPONENTS", "REQUIRED_ADMISSION_RECEIPTS",
    }
    extracted: Dict[str, Any] = {}
    for node in tree.body:
        name = None
        value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name, value = node.targets[0].id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name, value = node.target.id, node.value
        if name not in required:
            continue
        if name in extracted:
            raise ValidationError(f"duplicate required source assignment: {name}")
        if value is None:
            raise ValidationError(f"missing literal value for source assignment: {name}")
        try:
            extracted[name] = ast.literal_eval(value)
        except (ValueError, TypeError) as exc:
            raise ValidationError(f"nonliteral required source assignment: {name}") from exc
    missing = sorted(required - extracted.keys())
    if missing:
        raise ValidationError(f"missing required source assignments: {missing}")
    return extracted


def validate(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    root = _canonical_root(Path(root))
    machine_raw, machine_metadata = _read_regular_no_follow(root, MACHINE_PATH)
    if stat.S_IMODE(machine_metadata.st_mode) != 0o644 or machine_metadata.st_nlink != 1:
        raise ValidationError("machine custody mode/link mismatch")
    try:
        record = json.loads(machine_raw.decode("ascii"), object_pairs_hook=_pairs_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid machine JSON: {exc}") from exc
    raw = machine_raw
    if raw != canonical_machine_bytes(record):
        raise ValidationError("machine JSON is not canonical one-line ASCII with terminal LF")
    if record.get("record_sha256") != record_sha256(record):
        raise ValidationError("machine semantic self-digest mismatch")
    raws: Dict[str, bytes] = {}
    for path, _ in PACKAGE_BINDING_ROLES:
        content, metadata = _read_regular_no_follow(root, path)
        if stat.S_IMODE(metadata.st_mode) != 0o644 or metadata.st_nlink != 1 or not content.endswith(b"\n"):
            raise ValidationError(f"package custody mismatch: {path}")
        raws[path] = content
    for path, _, size, digest in PREDECESSOR_BINDINGS:
        content, metadata = _read_regular_no_follow(root, path)
        if len(content) != size or hashlib.sha256(content).hexdigest() != digest or stat.S_IMODE(metadata.st_mode) != 0o644 or metadata.st_nlink != 1 or not content.endswith(b"\n"):
            raise ValidationError(f"accepted predecessor mismatch: {path}")
    expected = _expected_record_from_raws(raws)
    if record != expected:
        raise ValidationError("machine record differs from the exact expected contract")
    namespace = _load_source_namespace(raws[SOURCE_PATH])
    for name, expected_value in (
        ("OBSERVATION_KERNEL_ID", "OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1"),
        ("ADMISSION_STATISTIC_ID", "MAX_HARD_TRAIN_ONLY_ADMISSION_VIOLATION_COUNT_V1"),
        ("ADMISSION_THRESHOLD_ID", "ALL_COMPONENTS_AND_MAX_EXACTLY_ZERO_V1"),
    ):
        if namespace.get(name) != expected_value:
            raise ValidationError(f"pure source constant drift: {name}")
    if tuple(namespace.get("ADMISSION_COMPONENTS", ())) != ADMISSION_COMPONENTS:
        raise ValidationError("pure source admission component drift")
    if tuple(namespace.get("REQUIRED_ADMISSION_RECEIPTS", ())) != REQUIRED_RECEIPTS:
        raise ValidationError("pure source receipt roster drift")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "fields_closed": list(FIELDS_CLOSED),
        "pre_execution_fields_closed": len(PRE_FIELDS_CLOSED),
        "post_execution_fields_closed": len(POST_FIELDS_CLOSED),
        "blockers_closed": 0,
        "blockers_remaining_open": ["B02", "B03", "B09", "B10", "B11"],
        "data_or_external_action_performed": False,
        "runtime_or_scientific_execution_performed": False,
        "validation": "PASS",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=True, sort_keys=True, separators=(",", ":")))
