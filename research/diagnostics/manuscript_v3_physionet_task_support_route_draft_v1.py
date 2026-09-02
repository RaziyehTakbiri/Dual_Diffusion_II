"""Read-only validator for the PhysioNet task/support-route draft.

The module treats all bound project sources as inert bytes.  It imports no
scientific package, opens no data, uses no network or subprocess API, draws no
entropy, and writes nothing.  The only public operation is :func:`validate`.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-physionet-task-support-route-draft-v1"
STATE = (
    "PHYSIONET_TASK_SUPPORT_ROUTE_DRAFT_FROZEN_AWAITING_SNAPSHOT_GOVERNANCE_"
    "SEMANTIC_POPULATION_AND_ADMISSION"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
PACKAGE_KIND = "STATIC_PHYSIONET_TASK_SUPPORT_ROUTE_DRAFT_NO_SCIENTIFIC_EFFECT"
CONTROL_PREDICATE = "PHYSIONET_TASK_SUPPORT_ROUTE_DRAFT_VALIDATED"
REPORTED_DATE = "2026-08-30"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")

HUMAN_PATH = "PROJECT_PHYSIONET_TASK_SUPPORT_ROUTE_DRAFT.md"
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_physionet_task_support_route_draft_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_physionet_task_support_route_draft_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_physionet_task_support_route_draft_v1.py"
)

PREREG_HUMAN_PATH = "manuscript_v3/execution_preregistration.md"
PREREG_MACHINE_PATH = "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
CLOSURE_HUMAN_PATH = "manuscript_v3/execution_preregistration_preexecution_closure_v2.md"
CLOSURE_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json"
)
SEAL_HUMAN_PATH = "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md"
SEAL_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json"
)
STATIC_HUMAN_PATH = "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md"
STATIC_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json"
)
RAW_SOURCE_PATH = "src/heterodiff/data/physionet_2012_raw.py"
INVENTORY_SOURCE_PATH = "src/heterodiff/data/physionet_2012_inventory.py"
ADAPTER_SOURCE_PATH = "src/heterodiff/data/physionet_2012_adapter.py"

NORMALIZED_AUTHORITY_TEXT = (
    "Sounds great. Go ahead and finish them in parallel. "
    "Mark all the completed tasks as the end."
)
AUTHORITY_TEXT_SHA256 = (
    "465aa47a0714b7914e33b6b6772afbfad3a56959cb6eb9f10b8e98f39c0f8d38"
)
SOURCE_URL = "https://physionet.org/content/challenge-2012/1.0.0/"


class ValidationError(ValueError):
    """Raised when custody, schema, or semantic validation fails."""


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


def record_sha256(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload))


def _object_without_duplicate_keys(
    pairs: Sequence[Tuple[str, Any]],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _strict_json(raw: bytes, label: str) -> Dict[str, Any]:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValidationError(label + " must be ASCII JSON") from exc
    try:
        value = json.loads(text, object_pairs_hook=_object_without_duplicate_keys)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValidationError(label + " is invalid strict JSON") from exc
    if type(value) is not dict:
        raise ValidationError(label + " top level must be an object")
    return value


def _ancestor_snapshot(root: Path, leaf: Path) -> Tuple[Tuple[int, int, int], ...]:
    snapshots = []
    current = leaf.parent
    while True:
        status = current.lstat()
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise ValidationError("unsafe ancestor: " + str(current))
        snapshots.append((status.st_dev, status.st_ino, stat.S_IFMT(status.st_mode)))
        if current == root:
            return tuple(snapshots)
        if root not in current.parents:
            raise ValidationError("path escaped workspace")
        current = current.parent


def _stable_read(root: Path, relative_path: str) -> bytes:
    if type(relative_path) is not str or not relative_path:
        raise ValidationError("binding path must be a nonempty string")
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValidationError("binding path must be canonical and relative")
    path = root / candidate
    ancestors = _ancestor_snapshot(root, path)
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValidationError("binding must be a regular non-symlink file")
    if before.st_nlink != 1:
        raise ValidationError("binding must have exactly one hard link")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        chunks = []
        while True:
            chunk = os.read(descriptor, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_opened = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    fingerprint = lambda item: (
        item.st_dev,
        item.st_ino,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
        stat.S_IFMT(item.st_mode),
        item.st_nlink,
    )
    if not (
        fingerprint(before)
        == fingerprint(opened)
        == fingerprint(after_opened)
        == fingerprint(after)
    ):
        raise ValidationError("file changed during read: " + relative_path)
    raw = b"".join(chunks)
    if len(raw) != before.st_size:
        raise ValidationError("short read: " + relative_path)
    if ancestors != _ancestor_snapshot(root, path):
        raise ValidationError("ancestor changed during read")
    return raw


EVIDENCE_SPECS: Tuple[Tuple[str, str], ...] = (
    ("EXECUTION_PREREGISTRATION_HUMAN", PREREG_HUMAN_PATH),
    ("EXECUTION_PREREGISTRATION_MACHINE", PREREG_MACHINE_PATH),
    ("PREEXECUTION_CLOSURE_HUMAN", CLOSURE_HUMAN_PATH),
    ("PREEXECUTION_CLOSURE_MACHINE", CLOSURE_MACHINE_PATH),
    ("PROSPECTIVE_NO_ACQUISITION_SEAL_HUMAN", SEAL_HUMAN_PATH),
    ("PROSPECTIVE_NO_ACQUISITION_SEAL_MACHINE", SEAL_MACHINE_PATH),
    ("SOLO_BLOCK2_STATIC_SELECTION_HUMAN", STATIC_HUMAN_PATH),
    ("SOLO_BLOCK2_STATIC_SELECTION_MACHINE", STATIC_MACHINE_PATH),
    ("PHYSIONET_LOSSLESS_RAW_SOURCE_RECEIPT", RAW_SOURCE_PATH),
    ("PHYSIONET_POLICY_FREE_INVENTORY_SOURCE_RECEIPT", INVENTORY_SOURCE_PATH),
    ("PHYSIONET_EXPLICIT_ADAPTER_SOURCE_RECEIPT", ADAPTER_SOURCE_PATH),
)

PACKAGE_SPECS: Tuple[Tuple[str, str], ...] = (
    ("HUMAN_DRAFT", HUMAN_PATH),
    ("READ_ONLY_VALIDATOR", VALIDATOR_PATH),
    ("HOSTILE_UNIT_TEST", TEST_PATH),
)


def _binding(ordinal: int, role: str, path: str, raw: bytes) -> Dict[str, Any]:
    return {
        "ordinal": ordinal,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "terminal_lf": raw.endswith(b"\n"),
    }


def _expected_bindings(
    root: Path, specs: Sequence[Tuple[str, str]]
) -> List[Dict[str, Any]]:
    return [
        _binding(ordinal, role, path, _stable_read(root, path))
        for ordinal, (role, path) in enumerate(specs)
    ]


EXPECTED_AUTHORITY: Mapping[str, Any] = {
    "normalized_visible_text": NORMALIZED_AUTHORITY_TEXT,
    "normalized_visible_text_utf8_bytes": 92,
    "normalized_visible_text_sha256": AUTHORITY_TEXT_SHA256,
    "normalization": "TRAILING_HTML_SPACE_ENTITY_AND_TRANSPORT_WHITESPACE_REMOVED_ONLY",
    "raw_transport_bytes_bound": False,
    "conversation_envelope_bound": False,
    "account_identity_bound": False,
    "timestamp_bound": False,
    "cryptographic_user_authentication_claimed": False,
    "parallel_block2_block3_draft_work_authorized": True,
    "tracker_edit_authorized_only_after_independent_validation": True,
    "external_contact_or_browsing_authorized": False,
    "data_access_or_opening_authorized": False,
    "split_or_escrow_operation_authorized": False,
    "scientific_execution_or_entropy_authorized": False,
    "runtime_approval_or_claim_promotion_authorized": False,
}

EXPECTED_DRAFT_IDENTITY: Mapping[str, Any] = {
    "route_id": "PHYSIONET_PATIENT_CONFIGURATION_TASK_SUPPORT_ROUTE_DRAFT_V1",
    "control_predicate": CONTROL_PREDICATE,
    "control_predicate_value_after_validation": True,
    "target_domain_id": "physionet-challenge-2012",
    "target_slot_id": "R3-PHYS",
    "registered_source_identifier": SOURCE_URL,
    "registered_source_identifier_verified_current": False,
    "draft_complete": True,
    "scientific_task_populated": False,
    "domain_admitted": False,
    "scientific_effect": 0,
}

EXPECTED_REPRESENTATION: Mapping[str, Any] = {
    "unit_of_analysis": "PATIENT_RECORD",
    "natural_group": "CANONICAL_RECORD_ID_PATIENT",
    "context_z_route": "STATIC_ADMISSION_DESCRIPTORS_AND_NONMODELING_CUSTODY_IDENTITY",
    "generated_endpoint_Y_route": "COMPLETE_ADMITTED_TIME_SERIES_MEASUREMENT_EVENT_CONFIGURATION",
    "observation_A_route": "UNORDERED_PARTIAL_OBSERVATION_FROM_FUTURE_APPLICATION_JUSTIFIED_KERNEL",
    "raw_row_contract": "EXACT_TIME_PARAMETER_VALUE_THREE_COLUMN_ROWS",
    "candidate_horizon_minutes_from_local_code_receipt": 2880,
    "physical_time_route": "ATOMIC_ELAPSED_MINUTE_GRID_PRESERVE_SIMULTANEOUS_EVENTS",
    "current_local_admission_descriptor_names": [
        "Age", "Gender", "Height", "ICUType", "RecordID", "Weight"
    ],
    "current_local_dual_role_parameter_names": ["Weight"],
    "static_descriptors_generated_as_events": False,
    "one_admitted_observation_row_per_event_or_fail": True,
    "missing_value_imputation_permitted": False,
    "sorting_row_collapse_deduplication_or_timestamp_jitter_permitted": False,
    "source_schema_or_clinical_meaning_verified_by_code_receipt": False,
    "event_vocabulary_support_units_sentinels_and_type_ids_populated": False,
}

EXPECTED_PIPELINE: Mapping[str, Any] = {
    "stage_order": [
        "BIND_OFFICIAL_ARCHIVE_LICENSE_GOVERNANCE_AND_USE_CONTROLS",
        "EXPLICIT_ALLOWLIST_POLICY_FREE_STRUCTURAL_INVENTORY",
        "VERIFY_PATIENT_IDENTITY_AND_SOURCE_PARTITION_DISJOINTNESS",
        "CONSUME_SEPARATELY_REVIEWED_PATIENT_SPLIT_PACKAGE",
        "FIT_TRAINING_ONLY_VOCABULARY_SUPPORT_TRANSFORMS_AND_CAPS",
        "FREEZE_COMPLETE_VERSIONED_ADAPTER_POLICY",
        "RUN_METHOD_BLIND_TRAINING_ONLY_ADMISSION_AUDIT",
        "INDEPENDENTLY_ADMIT_OR_TERMINATE_DOMAIN",
    ],
    "broad_glob_discovery_permitted": False,
    "outcome_table_joined_by_structural_inventory": False,
    "modeling_roles_assigned_by_structural_inventory": False,
    "all_data_dependent_semantics_fit_on_training_patients_only": True,
    "row_or_patient_quarantine_exclusion_resplit_or_postoutcome_repair_permitted": False,
    "failure_disposition": "DOMAIN_NO_GO_NEW_PREOUTCOME_VERSION_REQUIRED",
}

EXPECTED_SUPPORT: Mapping[str, Any] = {
    "selected_development_policy": (
        "ACQUISITION_JUSTIFIED_POSITIVE_DOMINATED_MIXTURE_WITH_SHARED_BASE_"
        "STRUCTURAL_ZEROS_AND_FAIL_CLOSED_NONADMISSION"
    ),
    "clean_kernel_kept_separate": True,
    "noise_or_clipping_for_theorem_convenience_permitted": False,
    "normalized_observation_reference_required_if_route_used": True,
    "positive_mixture_weight_frozen_before_test_access_required_if_justified": True,
    "shared_frozen_unconditional_base_required": True,
    "shared_base_structural_zeros_required": True,
    "finite_positive_information_and_normalizers_required": True,
    "target_positive_occupied_edges_candidate_positive_required": True,
    "observation_reference_populated": False,
    "positive_mixture_weight_populated": False,
    "common_support_proved_for_physionet": False,
    "failure_disposition": "PHYSIONET_DOMAIN_NOT_ADMITTED",
}

EXPECTED_ADMISSION: Mapping[str, Any] = {
    "scope": "METHOD_BLIND_TRAINING_PATIENTS_ONLY",
    "required_components": [
        "RAW_FORMAT_AND_IDENTITY_FAILURES",
        "UNKNOWN_OR_UNBOUND_PARAMETER_ROWS",
        "UNRESOLVED_MISSING_SENTINEL_SEMANTICS",
        "EVENT_STATE_COLLISIONS",
        "HORIZON_SUPPORT_CAP_AND_OVERFLOW_VIOLATIONS",
        "ROW_OR_PATIENT_EXCLUSION_COUNT",
        "PATIENT_PARTITION_OVERLAP",
        "KERNEL_NORMALIZATION_AND_COMMON_SUPPORT_FAILURES",
        "EXACT_NUMERATORS_AND_DENOMINATORS",
    ],
    "hard_integrity_components_must_equal_zero": True,
    "statistic_selected": False,
    "threshold_selected": False,
    "validation_or_test_feedback_permitted": False,
    "failed_rule_repair_topup_resplit_or_exclusion_permitted": False,
}

EXPECTED_SPLIT_SEAM: Mapping[str, Any] = {
    "patient_grouping_policy": "ALL_ROWS_FOR_CANONICAL_RECORD_ID_IN_EXACTLY_ONE_SPLIT",
    "patient_disjoint_manifest_required": True,
    "split_before_development_exposure_required": True,
    "split_design_implemented_by_this_package": False,
    "patient_hash_domain_selected_by_this_package": False,
    "canonical_patient_id_encoding_selected_by_this_package": False,
    "collision_rule_selected_by_this_package": False,
    "allocation_selected_by_this_package": False,
    "real_split_manifest_present": False,
    "separate_split_package_must_be_consumed_before_population": True,
}

OPEN_FIELD_IDS = tuple(
    ["F{:03d}".format(index) for index in range(19, 38)]
    + ["F058", "F061", "F163", "F166"]
)

EXPECTED_NONCLOSURE: Mapping[str, Any] = {
    "blocker_status": {"B02": "OPEN", "B09": "OPEN"},
    "open_field_values": {field_id: None for field_id in OPEN_FIELD_IDS},
    "open_field_count_in_this_dependency_view": 23,
    "effective_project_unresolved_field_count": 172,
    "effective_project_open_blocker_count": 12,
    "unresolved_fields_closed": 0,
    "blockers_closed": 0,
    "formal_scientific_tests_closed": 0,
    "scientific_results_produced": 0,
    "physionet_task_field_written_to_preregistration": False,
    "physionet_split_field_written_to_preregistration": False,
    "original_block2_populated_precontact_checkbox_closed": False,
}

EXPECTED_SCOPE: Mapping[str, Any] = {
    "static_draft_only": True,
    "web_network_connector_or_external_contact_used": False,
    "dataset_documentation_license_or_governance_contacted": False,
    "data_acquired_opened_parsed_inventoried_or_split": False,
    "protected_or_test_outcome_accessed": False,
    "project_science_imported_or_invoked": False,
    "scientific_execution_training_pilot_or_entropy_performed": False,
    "runtime_approved": False,
    "claim_or_domain_promoted": False,
    "tracker_edited_by_package": False,
    "existing_predecessor_modified": False,
    "package_internal_only": True,
    "publication_safe_derivative_required": True,
}

EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "state",
    "global_state",
    "package_kind",
    "reported_date",
    "authority_provenance",
    "draft_identity",
    "representation_route",
    "population_pipeline",
    "common_support_route",
    "admission_route",
    "split_package_seam",
    "nonclosure",
    "scope_and_nonclaims",
    "evidence_bindings",
    "package_bindings",
    "record_sha256",
}


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
    elif type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for ordinal, (left, right) in enumerate(zip(actual, expected)):
            _strict_equal(left, right, label + "[" + str(ordinal) + "]")
    elif actual != expected:
        raise ValidationError(label + " value mismatch")


def _defined_top_level_symbols(raw: bytes, label: str) -> set[str]:
    try:
        tree = ast.parse(raw.decode("utf-8"), filename=label)
    except (UnicodeDecodeError, SyntaxError) as exc:
        raise ValidationError(label + " is not valid UTF-8 Python") from exc
    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    symbols.add(target.id)
    return symbols


EXPECTED_SOURCE_SYMBOLS: Mapping[str, set[str]] = {
    RAW_SOURCE_PATH: {
        "DEFAULT_PHYSIONET_2012_ADMISSION_DESCRIPTORS",
        "DEFAULT_PHYSIONET_2012_DUAL_ROLE_PARAMETERS",
        "PhysioNet2012IngestionConfig",
        "PhysioNet2012Row",
        "PhysioNet2012Record",
        "parse_physionet_2012_record",
        "load_physionet_2012_record",
    },
    INVENTORY_SOURCE_PATH: {
        "PhysioNet2012PartitionInput",
        "PhysioNet2012ArchiveInventory",
        "PhysioNet2012InventoryLimits",
        "inventory_physionet_2012_partitions",
    },
    ADAPTER_SOURCE_PATH: {
        "PHYSIONET_2012_HORIZON_MINUTES",
        "PhysioNet2012TimePolicy",
        "PhysioNet2012DuplicatePolicy",
        "PhysioNet2012SplitIdentityPolicy",
        "PhysioNet2012AdapterPolicy",
        "PhysioNet2012AdaptedRecord",
        "adapt_physionet_2012_record",
    },
}


def _validate_bound_predecessors(root: Path, raws: Mapping[str, bytes]) -> None:
    prereg = _strict_json(raws[PREREG_MACHINE_PATH], "preregistration")
    if prereg.get("state") != GLOBAL_STATE:
        raise ValidationError("preregistration state changed")
    if prereg.get("confirmatory_execution_authorized") is not False:
        raise ValidationError("preregistration execution authority changed")
    domains = prereg.get("domains")
    if type(domains) is not list or len(domains) < 1 or type(domains[0]) is not dict:
        raise ValidationError("preregistration PhysioNet domain missing")
    domain = domains[0]
    if (
        domain.get("domain_id") != "physionet-challenge-2012"
        or domain.get("slot_id") != "R3-PHYS"
        or domain.get("source_url") != SOURCE_URL
        or domain.get("natural_group") != "patient"
        or domain.get("split_policy") != "PATIENT_DISJOINT"
    ):
        raise ValidationError("preregistration PhysioNet fixed identity changed")
    for field in (
        "snapshot_version",
        "raw_snapshot_sha256",
        "license_and_access_record",
        "governance_approval_record",
        "generated_endpoint_semantics",
        "context_semantics",
        "observation_semantics",
        "event_type_and_mark_schema",
        "physical_time_semantics",
        "horizon",
        "cap",
        "segmentation_rule",
        "overflow_and_exclusion_rule",
        "clean_observation_kernel",
        "observation_reference",
        "positive_or_common_support_route",
        "detection_noise_confusion_clutter_rule",
        "method_blind_training_only_admission_statistic",
        "method_blind_training_only_admission_threshold",
    ):
        if domain.get(field) is not None:
            raise ValidationError("PhysioNet field no longer open: " + field)
    split = prereg.get("split_and_leakage_plan")
    if type(split) is not dict:
        raise ValidationError("split plan missing")
    if (
        split.get("physionet_split_manifest_path") is not None
        or split.get("train_validation_test_proportions_or_counts") is not None
        or split.get("preprocessing_fit_scope") != "TRAIN_ONLY"
        or split.get("vocabulary_fit_scope") != "TRAIN_ONLY"
        or split.get("normalization_fit_scope") != "TRAIN_ONLY"
        or split.get("task_noise_model_fit_scope") != "TRAIN_ONLY"
        or split.get("test_access_before_full_freeze_permitted") is not False
        or split.get("test_set_exclusion_permitted") is not False
    ):
        raise ValidationError("split nonclosure or training-only boundary changed")
    ethics = prereg.get("ethics_release_and_review_plan")
    if type(ethics) is not dict:
        raise ValidationError("ethics plan missing")
    for field in (
        "data_license_compliance_plan",
        "physionet_clinical_governance_and_interpretation_plan",
    ):
        if ethics.get(field) is not None:
            raise ValidationError("governance field no longer open: " + field)

    closure = _strict_json(raws[CLOSURE_MACHINE_PATH], "closure")
    if closure.get("global_state") != GLOBAL_STATE:
        raise ValidationError("closure global state changed")
    projection = closure.get("blocker_projection")
    if type(projection) is not dict or projection.get("blockers_closed_by_closure") != 0:
        raise ValidationError("closure blocker projection changed")

    seal = _strict_json(raws[SEAL_MACHINE_PATH], "prospective seal")
    if seal.get("state") != "NO_TEST_DATA_ACQUIRED_USER_REPORTED_PROSPECTIVE_SEAL_ACTIVE":
        raise ValidationError("prospective no-acquisition state changed")
    boundary = seal.get("authority_boundary")
    if (
        type(boundary) is not dict
        or boundary.get("network_access_authorized") is not False
        or boundary.get("test_data_opening_authorized") is not False
        or boundary.get("scientific_execution_authorized") is not False
    ):
        raise ValidationError("prospective seal authority changed")

    static = _strict_json(raws[STATIC_MACHINE_PATH], "static route selection")
    support = static.get("common_support_selection")
    if (
        type(support) is not dict
        or support.get("policy") != EXPECTED_SUPPORT["selected_development_policy"]
        or support.get("physionet_route_verified") is not False
        or support.get("domain_admission_promoted") is not False
    ):
        raise ValidationError("static common-support selection changed")

    for path, required in EXPECTED_SOURCE_SYMBOLS.items():
        observed = _defined_top_level_symbols(raws[path], path)
        missing = required - observed
        if missing:
            raise ValidationError(
                "source symbol receipt missing from {}: {}".format(
                    path, ", ".join(sorted(missing))
                )
            )


def _validate_semantics(record: Mapping[str, Any]) -> None:
    if set(record) != EXPECTED_TOP_LEVEL_KEYS:
        raise ValidationError("machine record top-level key roster mismatch")
    if record["schema_version"] != SCHEMA:
        raise ValidationError("schema mismatch")
    if record["state"] != STATE or record["global_state"] != GLOBAL_STATE:
        raise ValidationError("state mismatch")
    if record["package_kind"] != PACKAGE_KIND or record["reported_date"] != REPORTED_DATE:
        raise ValidationError("package identity mismatch")
    for key, expected in (
        ("authority_provenance", EXPECTED_AUTHORITY),
        ("draft_identity", EXPECTED_DRAFT_IDENTITY),
        ("representation_route", EXPECTED_REPRESENTATION),
        ("population_pipeline", EXPECTED_PIPELINE),
        ("common_support_route", EXPECTED_SUPPORT),
        ("admission_route", EXPECTED_ADMISSION),
        ("split_package_seam", EXPECTED_SPLIT_SEAM),
        ("nonclosure", EXPECTED_NONCLOSURE),
        ("scope_and_nonclaims", EXPECTED_SCOPE),
    ):
        _strict_equal(record[key], dict(expected), key)
    if list(record["nonclosure"]["open_field_values"]) != list(OPEN_FIELD_IDS):
        raise ValidationError("open field order changed")
    if record["draft_identity"]["scientific_effect"] != 0:
        raise ValidationError("scientific effect must be zero")


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate the exact package and return a non-scientific status."""

    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    raw = _stable_read(workspace, MACHINE_PATH)
    record = _strict_json(raw, "PhysioNet task/support machine record")
    if type(record.get("record_sha256")) is not str:
        raise ValidationError("record self-digest must be a string")
    if record["record_sha256"] != record_sha256(record):
        raise ValidationError("record self-digest mismatch")
    _validate_semantics(record)

    expected_evidence = _expected_bindings(workspace, EVIDENCE_SPECS)
    expected_package = _expected_bindings(workspace, PACKAGE_SPECS)
    _strict_equal(record["evidence_bindings"], expected_evidence, "evidence bindings")
    _strict_equal(record["package_bindings"], expected_package, "package bindings")
    raw_map = {
        row["path"]: _stable_read(workspace, row["path"])
        for row in record["evidence_bindings"]
    }
    _validate_bound_predecessors(workspace, raw_map)

    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "control_predicate_value": True,
        "draft_complete": True,
        "B02_open": True,
        "B09_open": True,
        "dependency_open_field_count": 23,
        "patient_split_seam_open": True,
        "domain_admitted": False,
        "scientific_effect": 0,
        "validation": "PASS",
    }


__all__ = ["ValidationError", "record_sha256", "validate"]
