"""Canonical, type-strict contracts for the dormant A1 R1 successor protocol.

This module parses and validates supplied custody records.  It has no issuance,
minting, filesystem-write, entropy, network, subprocess, launch, or project-code
import capability.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Mapping, Sequence, Tuple


AUTHORITY_DOMAIN = "A1_FINITE_ASSOCIATION_R1_REGISTRY_AWARE_SUCCESSOR_AUTHORITY_V1"
REGISTRATION_SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-successor-runtime-adapter-authority-"
    "protocol-freeze-v1"
)
QUALIFICATION_SCHEMA = (
    "heterodiff-a1-r1-successor-runtime-adapter-authority-protocol-" "qualification-v1"
)
MILESTONE_STATE = (
    "R1_A1_SUCCESSOR_RUNTIME_ADMISSION_ADAPTER_AUTHORITY_AND_TYPED_CUSTODY_"
    "PROTOCOL_FROZEN_ZERO_EXECUTION_ACTIVATION_DEFERRED_NOT_EXECUTABLE"
)


def _schema(suffix: str) -> str:
    return "heterodiff-a1-r1-registry-aware-" + suffix + "-v1"


RUNTIME_CANDIDATE_SCHEMA = _schema("runtime-candidate")
RUNTIME_REVIEW_SCHEMA = _schema("runtime-review")
RUNTIME_APPROVAL_SCHEMA = _schema("runtime-approval")
SOURCE_CAPSULE_MANIFEST_SCHEMA = _schema("materialized-source-capsule-manifest")
SUCCESSOR_PLAN_SCHEMA = _schema("successor-plan")
SUCCESSOR_ACTIVATION_SCHEMA = _schema("successor-activation")
PHASE_AUTHORIZATION_SCHEMA = _schema("phase-authorization")
RANK_REQUEST_SCHEMA = _schema("rank-request")
RANK_COMPLETION_SCHEMA = _schema("rank-completion")
RANK_ADMISSION_SCHEMA = _schema("rank-admission")
COORDINATE_PERMIT_SCHEMA = _schema("coordinate-permit")
COORDINATE_REQUEST_SCHEMA = _schema("coordinate-request")
COORDINATE_COMPLETION_SCHEMA = _schema("coordinate-completion")
COORDINATE_CONSUMPTION_SCHEMA = _schema("coordinate-consumption")
PHASE_AGGREGATE_ADMISSION_SCHEMA = _schema("phase-aggregate-admission")
PRIMARY_METRICS_REQUEST_SCHEMA = _schema("primary-metrics-request")
PRIMARY_METRICS_COMPLETION_SCHEMA = _schema("primary-metrics-completion")
PRIMARY_METRICS_ADMISSION_SCHEMA = _schema("primary-metrics-admission")
ADAPTER_BOOTSTRAP_SPEC_SCHEMA = _schema("adapter-bootstrap-spec")
PRECREATION_ATTEMPT_MARKER_SCHEMA = _schema("precreation-attempt-marker")
PREREQUISITE_EVIDENCE_SCHEMA = _schema("prerequisite-evidence")
SOURCE_CAPSULE_ADMISSION_SCHEMA = _schema("source-capsule-admission")

PHASE_EVENT_ORDINAL = {
    "RANK": 0,
    "EXACT": 1,
    "PRIMARY": 2,
    "PRIMARY_METRICS": 3,
    "CONTROLS": 4,
}
COORDINATE_PHASES = ("EXACT", "PRIMARY", "CONTROLS")
BOOTSTRAP_INTERPRETER_RELATIVE_PATH = ".venv-m1/bin/python"
BOOTSTRAP_INTERPRETER_FLAGS = ["-P", "-B", "-S", "-X", "utf8"]
BOOTSTRAP_ENVIRONMENT = {
    "BLIS_NUM_THREADS": "1",
    "CUDA_VISIBLE_DEVICES": "",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
}
BOOTSTRAP_FORBIDDEN_INHERITED_ENVIRONMENT_KEYS = ["PYTHONHOME", "PYTHONPATH"]
BOOTSTRAP_SYS_PATH_ORDER = [
    "<content-addressed-capsule-root>/protocol",
    "<content-addressed-capsule-root>/src",
    "<runtime-approved-exact-site-packages>",
]


class ContractError(ValueError):
    """Raised when a supplied custody record is not the exact frozen contract."""


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        raise ContractError("value is not canonical ASCII JSON") from error


def sha256_bytes(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise ContractError("SHA-256 payload must be exact bytes")
    return hashlib.sha256(payload).hexdigest()


def require_sha256(value: Any, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ContractError(name + " must be one lowercase SHA-256")
    return value


def _require_relative_path(value: Any, name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.startswith("/")
        or "\\" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise ContractError(name + " must be one normalized relative path")
    return value


def _require_string(value: Any, name: str) -> str:
    if type(value) is not str or not value:
        raise ContractError(name + " must be one nonempty string")
    return value


def _require_int(value: Any, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ContractError(name + " must be one nonnegative exact integer")
    return value


def _require_bool(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise ContractError(name + " must be one exact Boolean")
    return value


def _require_sha_list(value: Any, name: str) -> Sequence[str]:
    if type(value) is not list:
        raise ContractError(name + " must be one SHA-256 list")
    for ordinal, item in enumerate(value):
        require_sha256(item, "%s[%d]" % (name, ordinal))
    return value


def _require_string_list(value: Any, name: str) -> Sequence[str]:
    if type(value) is not list:
        raise ContractError(name + " must be one string list")
    for ordinal, item in enumerate(value):
        _require_string(item, "%s[%d]" % (name, ordinal))
    return value


def _require_review_checks(value: Any, name: str) -> Mapping[str, bool]:
    fields = {
        "candidate_hashes_recomputed",
        "capsule_hashes_recomputed",
        "complete_installed_file_verification",
        "double_capture_stable",
        "legacy_paths_absent",
        "no_scientific_compute",
    }
    if type(value) is not dict or set(value) != fields:
        raise ContractError(name + " has the wrong exact review-check fields")
    for key in fields:
        _require_bool(value[key], name + "." + key)
    return value


def _require_tagged_coordinate(value: Any, name: str) -> Mapping[str, Any]:
    fields = {
        "accepted_example_budget",
        "coordinate_tag",
        "method",
        "phase",
        "phase_coordinate_ordinal",
        "seed",
        "seed_ordinal",
    }
    if type(value) is not dict or set(value) != fields:
        raise ContractError(name + " has the wrong exact tagged-coordinate fields")
    phase = value["phase"]
    if phase not in COORDINATE_PHASES:
        raise ContractError(name + ".phase is not a coordinate phase")
    _require_int(value["phase_coordinate_ordinal"], name + ".phase_coordinate_ordinal")
    _require_int(value["seed_ordinal"], name + ".seed_ordinal")
    _require_int(value["seed"], name + ".seed")
    _require_string(value["coordinate_tag"], name + ".coordinate_tag")
    _require_string(value["method"], name + ".method")
    budget = value["accepted_example_budget"]
    if phase == "EXACT":
        if budget is not None or value["coordinate_tag"] != "EXACT_SEED_METHOD":
            raise ContractError(name + " exact coordinate is malformed")
    elif (
        type(budget) is not int
        or budget < 0
        or value["coordinate_tag"] != "SAMPLED_SEED_BUDGET_METHOD"
    ):
        raise ContractError(name + " sampled coordinate is malformed")
    return value


def _require_projection(value: Any, name: str) -> Sequence[Any]:
    if type(value) is not list or len(value) not in {2, 3}:
        raise ContractError(name + " must be a two- or three-field list")
    if type(value[0]) is not int or type(value[-1]) is not str:
        raise ContractError(name + " has the wrong exact projection types")
    if len(value) == 3 and type(value[1]) is not int:
        raise ContractError(name + " has the wrong sampled budget type")
    return value


def _require_capsule_rows(value: Any, name: str) -> Sequence[Mapping[str, Any]]:
    fields = {
        "bytes",
        "capsule_relative_path",
        "execution_admissible",
        "ordinal",
        "raw_sha256",
        "source_path",
        "source_role",
    }
    if type(value) is not list:
        raise ContractError(name + " must be one capsule-row list")
    for ordinal, row in enumerate(value):
        if type(row) is not dict or set(row) != fields:
            raise ContractError(name + " has a malformed capsule row")
        if row["ordinal"] != ordinal or type(row["ordinal"]) is not int:
            raise ContractError(name + " capsule ordinals are not exact")
        _require_relative_path(row["source_path"], name + ".source_path")
        _require_relative_path(
            row["capsule_relative_path"], name + ".capsule_relative_path"
        )
        _require_string(row["source_role"], name + ".source_role")
        require_sha256(row["raw_sha256"], name + ".raw_sha256")
        _require_int(row["bytes"], name + ".bytes")
        if row["execution_admissible"] is not False:
            raise ContractError(name + " rows are not execution-admissible yet")
    return value


def _require_json_object(value: Any, name: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        raise ContractError(name + " must be one JSON object")
    canonical_json(value)
    return value


def _validate_kind(kind: str, value: Any, name: str, argument: Any) -> None:
    if kind == "sha256":
        require_sha256(value, name)
    elif kind == "nullable_sha256":
        if value is not None:
            require_sha256(value, name)
    elif kind == "nullable_string":
        if value is not None:
            _require_string(value, name)
    elif kind == "nullable_boolean":
        if value is not None:
            _require_bool(value, name)
    elif kind == "string":
        _require_string(value, name)
    elif kind == "relative_path":
        _require_relative_path(value, name)
    elif kind == "integer":
        _require_int(value, name)
    elif kind == "boolean":
        _require_bool(value, name)
    elif kind == "literal":
        if type(value) is not type(argument) or value != argument:
            raise ContractError(name + " differs from the frozen literal")
    elif kind == "enum":
        if type(value) is not str or value not in argument:
            raise ContractError(name + " is outside the frozen enumeration")
    elif kind == "sha256_list":
        _require_sha_list(value, name)
    elif kind == "string_list":
        _require_string_list(value, name)
    elif kind == "review_checks":
        _require_review_checks(value, name)
    elif kind == "tagged_coordinate":
        _require_tagged_coordinate(value, name)
    elif kind == "projection":
        _require_projection(value, name)
    elif kind == "capsule_rows":
        _require_capsule_rows(value, name)
    elif kind == "json_object":
        _require_json_object(value, name)
    else:  # pragma: no cover - closed catalog construction
        raise ContractError("unknown contract field kind")


Field = Tuple[str, str, Any]


def _field(name: str, kind: str, argument: Any = None) -> Field:
    return name, kind, argument


AUTHORITY_COMMON_FIELDS: Tuple[Field, ...] = (
    _field("schema", "string"),
    _field("authority_domain", "literal", AUTHORITY_DOMAIN),
    _field("plan_sha256", "sha256"),
    _field("campaign_nonce_sha256", "sha256"),
    _field("authority_event_ordinal", "integer"),
    _field("phase_event_ordinal", "integer"),
    _field("previous_head_sha256", "sha256"),
    _field("source_capsule_manifest_sha256", "sha256"),
    _field("runtime_manifest_sha256", "sha256"),
    _field("runtime_approval_sha256", "sha256"),
    _field("contracts_sha256", "sha256"),
    _field("authority_sha256", "sha256"),
    _field("adapter_sha256", "sha256"),
    _field("bootstrap_spec_sha256", "sha256"),
    _field("protocol_registration_raw_sha256", "sha256"),
    _field("protocol_registration_record_sha256", "sha256"),
    _field("protocol_test_sha256", "sha256"),
    _field("prerequisite_evidence_sha256", "sha256"),
    _field("source_capsule_admission_sha256", "sha256"),
)


def _common(*fields: Field) -> Tuple[Field, ...]:
    return AUTHORITY_COMMON_FIELDS + fields


CONTRACT_SPECS: Dict[str, Dict[str, Any]] = {
    "RUNTIME_CANDIDATE": {
        "schema": RUNTIME_CANDIDATE_SCHEMA,
        "digest_key": "candidate_sha256",
        "fields": (
            _field("schema", "literal", RUNTIME_CANDIDATE_SCHEMA),
            _field("target_profile_id", "string"),
            _field("capture_operation", "string"),
            _field("capture_request_sha256", "sha256"),
            _field("capture_envelope_a_sha256", "sha256"),
            _field("capture_envelope_b_sha256", "sha256"),
            _field("runtime_manifest_preview_sha256", "sha256"),
            _field("external_candidate_manifest_raw_sha256", "sha256"),
            _field("external_candidate_manifest_sha256", "sha256"),
            _field("capsule_manifest_sha256", "sha256"),
            _field("installed_files_manifest_sha256", "sha256"),
            _field("double_capture_stable", "boolean"),
            _field("complete_installed_file_verification", "boolean"),
            _field("scientific_compute_executed", "boolean"),
            _field("candidate_sha256", "sha256"),
        ),
    },
    "RUNTIME_REVIEW": {
        "schema": RUNTIME_REVIEW_SCHEMA,
        "digest_key": "review_sha256",
        "fields": (
            _field("schema", "literal", RUNTIME_REVIEW_SCHEMA),
            _field("target_profile_id", "string"),
            _field("candidate_sha256", "sha256"),
            _field("candidate_raw_sha256", "sha256"),
            _field("capsule_manifest_sha256", "sha256"),
            _field("review_checks", "review_checks"),
            _field("decision", "enum", ("APPROVE", "REJECT")),
            _field("operator_confirmation", "boolean"),
            _field("review_sha256", "sha256"),
        ),
    },
    "RUNTIME_APPROVAL": {
        "schema": RUNTIME_APPROVAL_SCHEMA,
        "digest_key": "approval_sha256",
        "fields": (
            _field("schema", "literal", RUNTIME_APPROVAL_SCHEMA),
            _field("target_profile_id", "string"),
            _field("candidate_sha256", "sha256"),
            _field("review_sha256", "sha256"),
            _field("fresh_recapture_envelope_sha256", "sha256"),
            _field("final_runtime_manifest_sha256", "sha256"),
            _field("approved_runtime_manifest_raw_sha256", "sha256"),
            _field("capsule_manifest_sha256", "sha256"),
            _field("contracts_sha256", "sha256"),
            _field("authority_sha256", "sha256"),
            _field("adapter_sha256", "sha256"),
            _field("runtime_identity_source_sha256", "sha256"),
            _field("runtime_identity_loader_api_sha256", "sha256"),
            _field("runtime_capture_source_sha256", "sha256"),
            _field("runtime_capture_api_sha256", "sha256"),
            _field("approved", "boolean"),
            _field("limitations", "string_list"),
            _field("approval_sha256", "sha256"),
        ),
    },
    "PRECREATION_ATTEMPT_MARKER": {
        "schema": PRECREATION_ATTEMPT_MARKER_SCHEMA,
        "digest_key": "marker_sha256",
        "fields": (
            _field("schema", "literal", PRECREATION_ATTEMPT_MARKER_SCHEMA),
            _field("registration_raw_sha256", "sha256"),
            _field("registration_record_sha256", "sha256"),
            _field("predecessor_snapshot_sha256", "sha256"),
            _field("source_capsule_manifest_sha256", "sha256"),
            _field("human_sha256", "sha256"),
            _field("contracts_sha256", "sha256"),
            _field("authority_sha256", "sha256"),
            _field("adapter_sha256", "sha256"),
            _field("test_sha256", "sha256"),
            _field("campaign_nonce_sha256", "sha256"),
            _field("preactivation_source_manifest_sha256", "sha256"),
            _field("registry_semantic_sha256", "sha256"),
            _field("execution_phase_schedule_sha256", "sha256"),
            _field("all_aggregate_manifest_sha256", "sha256"),
            _field("phase_event_schedule_sha256", "sha256"),
            _field("contract_catalog_sha256", "sha256"),
            _field("future_custody_path_roster_sha256", "sha256"),
            _field("precreation_plan_commitment_sha256", "sha256"),
            _field("all_future_roots_pristine_before_marker", "boolean"),
            _field("exclusive_create_completed", "boolean"),
            _field(
                "attempt_state",
                "literal",
                "PRECREATION_ATTEMPT_SPENT_TERMINAL_NO_RETRY",
            ),
            _field("marker_sha256", "sha256"),
        ),
    },
    "PREREQUISITE_EVIDENCE": {
        "schema": PREREQUISITE_EVIDENCE_SCHEMA,
        "digest_key": "evidence_sha256",
        "loader_only": True,
        "fields": (
            _field("schema", "literal", PREREQUISITE_EVIDENCE_SCHEMA),
            _field("authority_domain", "literal", AUTHORITY_DOMAIN),
            _field("predecessor_registration_raw_sha256", "sha256"),
            _field("predecessor_registration_record_sha256", "sha256"),
            _field("predecessor_qualification_snapshot_sha256", "sha256"),
            _field("registry_raw_sha256", "sha256"),
            _field("registry_record_sha256", "sha256"),
            _field("registry_semantic_sha256", "sha256"),
            _field("executable_preregistration_raw_sha256", "sha256"),
            _field("executable_preregistration_record_sha256", "sha256"),
            _field("executable_preregistration_freeze_receipt_sha256", "sha256"),
            _field("executable_preregistration_state", "string"),
            _field("unresolved_null_count", "integer"),
            _field("execution_blocker_count", "integer"),
            _field("submission_blocker_count", "integer"),
            _field("all_execution_blockers_closed", "boolean"),
            _field("all_submission_blockers_closed", "boolean"),
            _field("freeze_predicate_satisfied", "boolean"),
            _field("test_data_unopened_before_freeze", "boolean"),
            _field("r1_a1_slot_identity_sha256", "sha256"),
            _field("d1_human_sha256", "sha256"),
            _field("d1_machine_sha256", "sha256"),
            _field("d1_diagnostic_record_sha256", "sha256"),
            _field("d1_prior_observed", "boolean"),
            _field("d1_execution_admissible", "boolean"),
            _field("source_capsule_admission_sha256", "sha256"),
            _field("runtime_manifest_sha256", "sha256"),
            _field("runtime_approval_sha256", "sha256"),
            _field("contracts_sha256", "sha256"),
            _field("authority_sha256", "sha256"),
            _field("adapter_sha256", "sha256"),
            _field("exact_manifest_sha256", "sha256"),
            _field("primary_manifest_sha256", "sha256"),
            _field("controls_manifest_sha256", "sha256"),
            _field("complete_sampled_manifest_sha256", "sha256"),
            _field("execution_phase_schedule_sha256", "sha256"),
            _field("all_aggregate_manifest_sha256", "sha256"),
            _field("phase_event_schedule_sha256", "sha256"),
            _field("live_absence_roster_sha256", "sha256"),
            _field("evidence_sha256", "sha256"),
        ),
    },
    "SOURCE_CAPSULE_ADMISSION": {
        "schema": SOURCE_CAPSULE_ADMISSION_SCHEMA,
        "digest_key": "admission_sha256",
        "loader_only": True,
        "fields": (
            _field("schema", "literal", SOURCE_CAPSULE_ADMISSION_SCHEMA),
            _field("authority_domain", "literal", AUTHORITY_DOMAIN),
            _field("predecessor_qualification_snapshot_sha256", "sha256"),
            _field("preactivation_source_manifest_sha256", "sha256"),
            _field("materialized_capsule_manifest_sha256", "sha256"),
            _field("canonical_capsule_root_identity_sha256", "sha256"),
            _field("local_package_source_count", "literal", 47),
            _field("local_package_source_roster_sha256", "sha256"),
            _field("nonpackage_input_count", "literal", 3),
            _field("nonpackage_input_roster_sha256", "sha256"),
            _field("protocol_copy_count", "literal", 3),
            _field("protocol_copy_roster_sha256", "sha256"),
            _field("overlay_rule_count", "literal", 5),
            _field("overlay_rule_roster_sha256", "sha256"),
            _field("registry_semantic_sha256", "sha256"),
            _field("all_live_rows_verified", "boolean"),
            _field("regular_files_only", "boolean"),
            _field("no_symlinks", "boolean"),
            _field("no_hardlinks", "boolean"),
            _field("no_extra_files", "boolean"),
            _field("no_pyc", "boolean"),
            _field("planned_workspace_src_adapter_absent", "boolean"),
            _field("dynamic_local_edge_count", "literal", 6),
            _field("dynamic_local_edges_satisfied", "boolean"),
            _field("external_numerical_modules_deferred_to_runtime", "boolean"),
            _field("admission_sha256", "sha256"),
        ),
    },
    "SOURCE_CAPSULE_MANIFEST": {
        "schema": SOURCE_CAPSULE_MANIFEST_SCHEMA,
        "digest_key": "capsule_manifest_sha256",
        "fields": (
            _field("schema", "literal", SOURCE_CAPSULE_MANIFEST_SCHEMA),
            _field("capsule_root_relative_path", "relative_path"),
            _field("source_manifest_sha256", "sha256"),
            _field("registry_semantic_sha256", "sha256"),
            _field("base_module_count", "integer"),
            _field("deferred_runtime_source_count", "integer"),
            _field("nonpackage_input_count", "integer"),
            _field("rows", "capsule_rows"),
            _field("adapter_copy_relative_path", "relative_path"),
            _field("contracts_copy_relative_path", "relative_path"),
            _field("bootstrap_spec_copy_relative_path", "relative_path"),
            _field("adapter_sha256", "sha256"),
            _field("contracts_sha256", "sha256"),
            _field("bootstrap_spec_raw_sha256", "sha256"),
            _field("capsule_src_excludes_adapter_protocol", "boolean"),
            _field("capsule_manifest_sha256", "sha256"),
        ),
    },
    "SUCCESSOR_PLAN": {
        "schema": SUCCESSOR_PLAN_SCHEMA,
        "digest_key": "plan_sha256",
        "fields": (
            _field("schema", "literal", SUCCESSOR_PLAN_SCHEMA),
            _field("authority_domain", "literal", AUTHORITY_DOMAIN),
            _field("campaign_nonce_sha256", "sha256"),
            _field("initial_head_sha256", "sha256"),
            _field("precreation_plan_commitment_sha256", "sha256"),
            _field("precreation_attempt_marker_raw_sha256", "sha256"),
            _field("precreation_attempt_marker_record_sha256", "sha256"),
            _field("predecessor_registration_sha256", "sha256"),
            _field("predecessor_snapshot_sha256", "sha256"),
            _field("source_capsule_manifest_sha256", "sha256"),
            _field("runtime_manifest_sha256", "sha256"),
            _field("runtime_approval_sha256", "sha256"),
            _field("contracts_sha256", "sha256"),
            _field("authority_sha256", "sha256"),
            _field("adapter_sha256", "sha256"),
            _field("bootstrap_spec_sha256", "sha256"),
            _field("protocol_registration_raw_sha256", "sha256"),
            _field("protocol_registration_record_sha256", "sha256"),
            _field("protocol_test_sha256", "sha256"),
            _field("prerequisite_evidence_sha256", "sha256"),
            _field("source_capsule_admission_sha256", "sha256"),
            _field("registry_raw_sha256", "sha256"),
            _field("registry_record_sha256", "sha256"),
            _field("registry_semantic_sha256", "sha256"),
            _field("exact_manifest_sha256", "sha256"),
            _field("primary_manifest_sha256", "sha256"),
            _field("controls_manifest_sha256", "sha256"),
            _field("complete_sampled_manifest_sha256", "sha256"),
            _field("execution_phase_schedule_manifest_sha256", "sha256"),
            _field("all_aggregate_manifest_sha256", "sha256"),
            _field("phase_event_schedule_sha256", "sha256"),
            _field("phase_event_order", "string_list"),
            _field("d1_disclosed_and_seed_1729_quarantined", "boolean"),
            _field("executable_preregistration_verified", "boolean"),
            _field("plan_sha256", "sha256"),
        ),
    },
    "SUCCESSOR_ACTIVATION": {
        "schema": SUCCESSOR_ACTIVATION_SCHEMA,
        "digest_key": "activation_sha256",
        "fields": (
            _field("schema", "literal", SUCCESSOR_ACTIVATION_SCHEMA),
            _field("authority_domain", "literal", AUTHORITY_DOMAIN),
            _field("plan_sha256", "sha256"),
            _field("campaign_nonce_sha256", "sha256"),
            _field("precreation_snapshot_sha256", "sha256"),
            _field("precreation_plan_commitment_sha256", "sha256"),
            _field("precreation_attempt_marker_raw_sha256", "sha256"),
            _field("precreation_attempt_marker_record_sha256", "sha256"),
            _field("source_capsule_manifest_sha256", "sha256"),
            _field("runtime_manifest_sha256", "sha256"),
            _field("runtime_approval_sha256", "sha256"),
            _field("contracts_sha256", "sha256"),
            _field("authority_sha256", "sha256"),
            _field("adapter_sha256", "sha256"),
            _field("bootstrap_spec_sha256", "sha256"),
            _field("protocol_registration_raw_sha256", "sha256"),
            _field("protocol_registration_record_sha256", "sha256"),
            _field("protocol_test_sha256", "sha256"),
            _field("prerequisite_evidence_sha256", "sha256"),
            _field("source_capsule_admission_sha256", "sha256"),
            _field("confirmatory_execution_blockers_remaining", "integer"),
            _field("executable_preregistration_verified", "boolean"),
            _field("d1_disclosure_verified", "boolean"),
            _field("seed_1729_quarantine_verified", "boolean"),
            _field("all_successor_roots_pristine", "boolean"),
            _field("activation_ready", "boolean"),
            _field("activation_sha256", "sha256"),
        ),
    },
    "PHASE_AUTHORIZATION": {
        "schema": PHASE_AUTHORIZATION_SCHEMA,
        "digest_key": "authorization_sha256",
        "fields": _common(
            _field(
                "phase",
                "enum",
                ("RANK", "EXACT", "PRIMARY", "PRIMARY_METRICS", "CONTROLS"),
            ),
            _field("activation_sha256", "sha256"),
            _field("prior_admission_sha256", "nullable_sha256"),
            _field("authorization_nonce_sha256", "sha256"),
            _field("authorization_sha256", "sha256"),
        ),
    },
}


def _api_identity_fields(prefix: str) -> Tuple[Field, ...]:
    return (
        _field(prefix + "_module", "string"),
        _field(prefix + "_qualname", "string"),
        _field(prefix + "_source_sha256", "sha256"),
        _field(prefix + "_api_sha256", "sha256"),
    )


CONTRACT_SPECS.update(
    {
        "RANK_REQUEST": {
            "schema": RANK_REQUEST_SCHEMA,
            "digest_key": "request_sha256",
            "fields": _common(
                _field("phase_authorization_sha256", "sha256"),
                _field("request_nonce_sha256", "sha256"),
                _field("destination_relative_path", "relative_path"),
                _field("raw_result_relative_path", "relative_path"),
                _field("prepared_custody_relative_path", "relative_path"),
                _field("parent_exit_relative_path", "relative_path"),
                *_api_identity_fields("launcher"),
                *_api_identity_fields("loader"),
                *_api_identity_fields("revalidator"),
                _field("request_sha256", "sha256"),
            ),
        },
        "RANK_COMPLETION": {
            "schema": RANK_COMPLETION_SCHEMA,
            "digest_key": "completion_sha256",
            "fields": _common(
                _field("request_sha256", "sha256"),
                _field("phase_authorization_sha256", "sha256"),
                _field("child_exit_code", "integer"),
                _field("raw_result_path_sha256", "sha256"),
                _field("raw_result_sha256", "sha256"),
                _field("prepared_custody_path_sha256", "sha256"),
                _field("prepared_custody_sha256", "sha256"),
                _field("parent_exit_path_sha256", "sha256"),
                _field("parent_exit_sha256", "sha256"),
                _field("serialized_result_sha256", "sha256"),
                _field("loader_receipt_sha256", "sha256"),
                _field("section_nine_gate_passed", "boolean"),
                _field("completion_sha256", "sha256"),
            ),
        },
        "RANK_ADMISSION": {
            "schema": RANK_ADMISSION_SCHEMA,
            "digest_key": "admission_sha256",
            "fields": _common(
                _field("request_sha256", "sha256"),
                _field("completion_sha256", "sha256"),
                _field("phase_authorization_sha256", "sha256"),
                _field("parent_reopened_loader_receipt_sha256", "sha256"),
                _field("prepared_revalidation_passed", "boolean"),
                _field("admission_sha256", "sha256"),
            ),
        },
        "COORDINATE_PERMIT": {
            "schema": COORDINATE_PERMIT_SCHEMA,
            "digest_key": "permit_sha256",
            "fields": _common(
                _field("phase", "enum", COORDINATE_PHASES),
                _field("phase_coordinate_ordinal", "integer"),
                _field("tagged_coordinate", "tagged_coordinate"),
                _field("phase_coordinate_manifest_sha256", "sha256"),
                _field("phase_authorization_sha256", "sha256"),
                _field("permit_nonce_sha256", "sha256"),
                _field("permit_sha256", "sha256"),
            ),
        },
        "COORDINATE_REQUEST": {
            "schema": COORDINATE_REQUEST_SCHEMA,
            "digest_key": "request_sha256",
            "fields": _common(
                _field("phase", "enum", COORDINATE_PHASES),
                _field("phase_coordinate_ordinal", "integer"),
                _field("tagged_coordinate", "tagged_coordinate"),
                _field("phase_coordinate_manifest_sha256", "sha256"),
                _field("phase_authorization_sha256", "sha256"),
                _field("permit_sha256", "sha256"),
                _field("legacy_request_type", "string"),
                _field("legacy_request_projection", "projection"),
                *_api_identity_fields("launcher"),
                _field("child_output_root", "relative_path"),
                _field("request_sha256", "sha256"),
            ),
        },
        "COORDINATE_COMPLETION": {
            "schema": COORDINATE_COMPLETION_SCHEMA,
            "digest_key": "completion_sha256",
            "fields": _common(
                _field("phase", "enum", COORDINATE_PHASES),
                _field("phase_coordinate_ordinal", "integer"),
                _field("tagged_coordinate", "tagged_coordinate"),
                _field("phase_coordinate_manifest_sha256", "sha256"),
                _field("phase_authorization_sha256", "sha256"),
                _field("permit_sha256", "sha256"),
                _field("request_sha256", "sha256"),
                _field("child_exit_code", "integer"),
                _field("legacy_run_key_sha256", "sha256"),
                _field("raw_success_path_sha256", "sha256"),
                _field("raw_checkpoint_sha256", "nullable_sha256"),
                _field("public_member_loader_module", "nullable_string"),
                _field("public_member_loader_qualname", "nullable_string"),
                _field("public_member_loader_source_sha256", "nullable_sha256"),
                _field("public_member_loader_api_sha256", "nullable_sha256"),
                _field("public_member_revalidator_module", "nullable_string"),
                _field("public_member_revalidator_qualname", "nullable_string"),
                _field("public_member_revalidator_source_sha256", "nullable_sha256"),
                _field("public_member_revalidator_api_sha256", "nullable_sha256"),
                _field("member_revalidation_passed", "nullable_boolean"),
                _field("member_completion_provisional", "boolean"),
                _field(
                    "parent_reopened_member_loader_receipt_sha256",
                    "nullable_sha256",
                ),
                _field("reopened_tagged_coordinate_sha256", "nullable_sha256"),
                _field("completion_sha256", "sha256"),
            ),
        },
        "COORDINATE_CONSUMPTION": {
            "schema": COORDINATE_CONSUMPTION_SCHEMA,
            "digest_key": "consumption_sha256",
            "fields": _common(
                _field("phase", "enum", COORDINATE_PHASES),
                _field("phase_coordinate_ordinal", "integer"),
                _field("tagged_coordinate", "tagged_coordinate"),
                _field("phase_coordinate_manifest_sha256", "sha256"),
                _field("phase_authorization_sha256", "sha256"),
                _field("permit_sha256", "sha256"),
                _field("request_sha256", "sha256"),
                _field("typed_output_evidence_sha256", "sha256"),
                _field(
                    "evidence_level",
                    "enum",
                    (
                        "PROVISIONAL_EXACT_MEMBER_COMPLETION",
                        "PROVISIONAL_SAMPLED_MEMBER_LOADER_REVALIDATED",
                    ),
                ),
                _field("consumed_once", "boolean"),
                _field("consumption_sha256", "sha256"),
            ),
        },
        "PHASE_AGGREGATE_ADMISSION": {
            "schema": PHASE_AGGREGATE_ADMISSION_SCHEMA,
            "digest_key": "admission_sha256",
            "fields": _common(
                _field("phase", "enum", COORDINATE_PHASES),
                _field("phase_manifest_sha256", "sha256"),
                _field("expected_count", "integer"),
                _field("ordered_permit_sha256s", "sha256_list"),
                _field("ordered_request_sha256s", "sha256_list"),
                _field("ordered_completion_sha256s", "sha256_list"),
                _field("ordered_consumption_sha256s", "sha256_list"),
                _field("permit_list_sha256", "sha256"),
                _field("request_list_sha256", "sha256"),
                _field("completion_list_sha256", "sha256"),
                _field("consumption_list_sha256", "sha256"),
                _field("coverage_complete", "boolean"),
                _field("no_gaps", "boolean"),
                _field("no_duplicates", "boolean"),
                *_api_identity_fields("aggregate_loader"),
                *_api_identity_fields("aggregate_revalidator"),
                _field("aggregate_receipt_sha256", "sha256"),
                _field("aggregate_campaign_sha256", "sha256"),
                _field("aggregate_result_sha256", "sha256"),
                _field("prior_phase_admission_sha256", "nullable_sha256"),
                _field("primary_metrics_admission_sha256", "nullable_sha256"),
                _field("complete_sampled_manifest_sha256", "nullable_sha256"),
                _field("parent_revalidation_passed", "boolean"),
                _field("admission_sha256", "sha256"),
            ),
        },
        "PRIMARY_METRICS_REQUEST": {
            "schema": PRIMARY_METRICS_REQUEST_SCHEMA,
            "digest_key": "request_sha256",
            "fields": _common(
                _field("primary_aggregate_admission_sha256", "sha256"),
                _field("primary_manifest_sha256", "sha256"),
                _field("primary_success_set_sha256", "sha256"),
                *_api_identity_fields("compute"),
                _field("request_nonce_sha256", "sha256"),
                _field("request_sha256", "sha256"),
            ),
        },
        "PRIMARY_METRICS_COMPLETION": {
            "schema": PRIMARY_METRICS_COMPLETION_SCHEMA,
            "digest_key": "completion_sha256",
            "fields": _common(
                _field("request_sha256", "sha256"),
                _field("child_exit_code", "integer"),
                _field("raw_metrics_receipt_sha256", "sha256"),
                _field("raw_metrics_path_sha256", "sha256"),
                _field("raw_metrics_order_sha256", "sha256"),
                _field("completion_sha256", "sha256"),
            ),
        },
        "PRIMARY_METRICS_ADMISSION": {
            "schema": PRIMARY_METRICS_ADMISSION_SCHEMA,
            "digest_key": "admission_sha256",
            "fields": _common(
                _field("request_sha256", "sha256"),
                _field("completion_sha256", "sha256"),
                *_api_identity_fields("loader"),
                *_api_identity_fields("revalidator"),
                _field("parent_reopened_receipt_sha256", "sha256"),
                _field("primary_success_set_sha256", "sha256"),
                _field("ordered_metric_records_sha256", "sha256"),
                _field("primary_48_coordinate_identity_sha256", "sha256"),
                _field("parent_revalidation_passed", "boolean"),
                _field("admission_sha256", "sha256"),
            ),
        },
        "ADAPTER_BOOTSTRAP_SPEC": {
            "schema": ADAPTER_BOOTSTRAP_SPEC_SCHEMA,
            "digest_key": "bootstrap_spec_sha256",
            "fields": (
                _field("schema", "literal", ADAPTER_BOOTSTRAP_SPEC_SCHEMA),
                _field(
                    "interpreter_relative_path",
                    "literal",
                    BOOTSTRAP_INTERPRETER_RELATIVE_PATH,
                ),
                _field("interpreter_flags", "literal", BOOTSTRAP_INTERPRETER_FLAGS),
                _field("environment", "literal", BOOTSTRAP_ENVIRONMENT),
                _field("environment_mode", "literal", "EXACT_REPLACEMENT_ALLOWLIST"),
                _field("environment_inheritance_permitted", "literal", False),
                _field(
                    "forbidden_inherited_environment_keys",
                    "literal",
                    BOOTSTRAP_FORBIDDEN_INHERITED_ENVIRONMENT_KEYS,
                ),
                _field("sys_path_order", "literal", BOOTSTRAP_SYS_PATH_ORDER),
                _field("pth_processing_permitted", "literal", False),
                _field("verify_every_file_hash", "literal", True),
                _field("verify_imported_module_file", "literal", True),
                _field("legacy_project_import_permitted", "literal", False),
                _field("bootstrap_spec_sha256", "sha256"),
            ),
        },
    }
)


def _semantic_digest(record: Mapping[str, Any], schema: str, digest_key: str) -> str:
    body = dict(record)
    body[digest_key] = None
    return sha256_bytes(schema.encode("ascii") + b"\0" + canonical_json(body))


def _validate_record(record: Any, contract_id: str) -> Dict[str, Any]:
    if contract_id not in CONTRACT_SPECS:
        raise ContractError("contract identifier is not frozen")
    spec = CONTRACT_SPECS[contract_id]
    fields = spec["fields"]
    names = tuple(field[0] for field in fields)
    if (
        type(record) is not dict
        or set(record) != set(names)
        or len(record) != len(names)
    ):
        raise ContractError(contract_id + " has the wrong exact fields")
    if record.get("schema") != spec["schema"]:
        raise ContractError(contract_id + " schema changed")
    for name, kind, argument in fields:
        _validate_kind(kind, record[name], contract_id + "." + name, argument)
    digest_key = spec["digest_key"]
    if record[digest_key] != _semantic_digest(record, spec["schema"], digest_key):
        raise ContractError(contract_id + " terminal digest is inconsistent")
    return record


class StrictCanonicalRecord:
    """Immutable syntax- and digest-validated record; never an authorization."""

    __slots__ = ("_canonical_record",)
    CONTRACT_ID = ""

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise TypeError("records are parsed only from canonical supplied bytes")

    @classmethod
    def parse(cls, payload: bytes) -> "StrictCanonicalRecord":
        if CONTRACT_SPECS[cls.CONTRACT_ID].get("loader_only") is True:
            raise TypeError("this evidence type is constructed only by its live loader")
        return _parse_record_payload(cls, payload)

    def to_record(self) -> Dict[str, Any]:
        value = json.loads(self._canonical_record.decode("ascii"))
        if type(value) is not dict:
            raise ContractError("validated record changed type")
        return value

    @property
    def terminal_sha256(self) -> str:
        spec = CONTRACT_SPECS[self.CONTRACT_ID]
        return self.to_record()[spec["digest_key"]]

    def __setattr__(self, name: str, value: Any) -> None:
        del name, value
        raise AttributeError("validated custody records are immutable")


def _parse_record_payload(cls: type, payload: bytes) -> StrictCanonicalRecord:
    """Internal exact parser used by public syntax parsers and live loaders."""

    if not issubclass(cls, StrictCanonicalRecord):
        raise TypeError("record class is outside the frozen contract hierarchy")
    if type(payload) is not bytes or not payload.endswith(b"\n"):
        raise ContractError("record must be LF-terminated exact bytes")
    try:
        record = json.loads(payload[:-1].decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError("record is not canonical ASCII JSON") from error
    if payload != canonical_json(record) + b"\n":
        raise ContractError("record bytes are not canonical LF-terminated JSON")
    checked = _validate_record(record, cls.CONTRACT_ID)
    instance = object.__new__(cls)
    object.__setattr__(instance, "_canonical_record", canonical_json(checked))
    return instance


def _record_type(name: str, contract_id: str) -> type:
    return type(name, (StrictCanonicalRecord,), {"CONTRACT_ID": contract_id})


RuntimeCandidateV1 = _record_type("RuntimeCandidateV1", "RUNTIME_CANDIDATE")
RuntimeReviewV1 = _record_type("RuntimeReviewV1", "RUNTIME_REVIEW")
RuntimeApprovalV1 = _record_type("RuntimeApprovalV1", "RUNTIME_APPROVAL")
PrecreationAttemptMarkerV1 = _record_type(
    "PrecreationAttemptMarkerV1", "PRECREATION_ATTEMPT_MARKER"
)
PrerequisiteEvidenceV1 = _record_type("PrerequisiteEvidenceV1", "PREREQUISITE_EVIDENCE")
SourceCapsuleAdmissionV1 = _record_type(
    "SourceCapsuleAdmissionV1", "SOURCE_CAPSULE_ADMISSION"
)
MaterializedSourceCapsuleManifestV1 = _record_type(
    "MaterializedSourceCapsuleManifestV1", "SOURCE_CAPSULE_MANIFEST"
)
SuccessorPlanV1 = _record_type("SuccessorPlanV1", "SUCCESSOR_PLAN")
SuccessorActivationV1 = _record_type("SuccessorActivationV1", "SUCCESSOR_ACTIVATION")
PhaseAuthorizationV1 = _record_type("PhaseAuthorizationV1", "PHASE_AUTHORIZATION")
RankRequestV1 = _record_type("RankRequestV1", "RANK_REQUEST")
RankCompletionV1 = _record_type("RankCompletionV1", "RANK_COMPLETION")
RankAdmissionV1 = _record_type("RankAdmissionV1", "RANK_ADMISSION")
CoordinatePermitV1 = _record_type("CoordinatePermitV1", "COORDINATE_PERMIT")
CoordinateRequestV1 = _record_type("CoordinateRequestV1", "COORDINATE_REQUEST")
CoordinateCompletionV1 = _record_type("CoordinateCompletionV1", "COORDINATE_COMPLETION")
CoordinateConsumptionV1 = _record_type(
    "CoordinateConsumptionV1", "COORDINATE_CONSUMPTION"
)
PhaseAggregateAdmissionV1 = _record_type(
    "PhaseAggregateAdmissionV1", "PHASE_AGGREGATE_ADMISSION"
)
PrimaryMetricsRequestV1 = _record_type(
    "PrimaryMetricsRequestV1", "PRIMARY_METRICS_REQUEST"
)
PrimaryMetricsCompletionV1 = _record_type(
    "PrimaryMetricsCompletionV1", "PRIMARY_METRICS_COMPLETION"
)
PrimaryMetricsAdmissionV1 = _record_type(
    "PrimaryMetricsAdmissionV1", "PRIMARY_METRICS_ADMISSION"
)
AdapterBootstrapSpecV1 = _record_type(
    "AdapterBootstrapSpecV1", "ADAPTER_BOOTSTRAP_SPEC"
)


RECORD_TYPES = {
    contract_id: value
    for contract_id, value in (
        ("RUNTIME_CANDIDATE", RuntimeCandidateV1),
        ("RUNTIME_REVIEW", RuntimeReviewV1),
        ("RUNTIME_APPROVAL", RuntimeApprovalV1),
        ("PRECREATION_ATTEMPT_MARKER", PrecreationAttemptMarkerV1),
        ("PREREQUISITE_EVIDENCE", PrerequisiteEvidenceV1),
        ("SOURCE_CAPSULE_ADMISSION", SourceCapsuleAdmissionV1),
        ("SOURCE_CAPSULE_MANIFEST", MaterializedSourceCapsuleManifestV1),
        ("SUCCESSOR_PLAN", SuccessorPlanV1),
        ("SUCCESSOR_ACTIVATION", SuccessorActivationV1),
        ("PHASE_AUTHORIZATION", PhaseAuthorizationV1),
        ("RANK_REQUEST", RankRequestV1),
        ("RANK_COMPLETION", RankCompletionV1),
        ("RANK_ADMISSION", RankAdmissionV1),
        ("COORDINATE_PERMIT", CoordinatePermitV1),
        ("COORDINATE_REQUEST", CoordinateRequestV1),
        ("COORDINATE_COMPLETION", CoordinateCompletionV1),
        ("COORDINATE_CONSUMPTION", CoordinateConsumptionV1),
        ("PHASE_AGGREGATE_ADMISSION", PhaseAggregateAdmissionV1),
        ("PRIMARY_METRICS_REQUEST", PrimaryMetricsRequestV1),
        ("PRIMARY_METRICS_COMPLETION", PrimaryMetricsCompletionV1),
        ("PRIMARY_METRICS_ADMISSION", PrimaryMetricsAdmissionV1),
        ("ADAPTER_BOOTSTRAP_SPEC", AdapterBootstrapSpecV1),
    )
}


def contract_catalog() -> Dict[str, Any]:
    """Return the exact public field/schema registry, without issuing a record."""

    rows = []
    for ordinal, contract_id in enumerate(sorted(CONTRACT_SPECS)):
        spec = CONTRACT_SPECS[contract_id]
        rows.append(
            {
                "ordinal": ordinal,
                "contract_id": contract_id,
                "schema": spec["schema"],
                "digest_key": spec["digest_key"],
                "fields": [field[0] for field in spec["fields"]],
                "record_type": RECORD_TYPES[contract_id].__name__,
                "public_syntax_parser_available": spec.get("loader_only") is not True,
                "live_loader_only": spec.get("loader_only") is True,
                "no_issuance": True,
            }
        )
    body = {
        "authority_domain": AUTHORITY_DOMAIN,
        "registration_schema": REGISTRATION_SCHEMA,
        "qualification_schema": QUALIFICATION_SCHEMA,
        "record_count": len(rows),
        "records": rows,
        "one_terminal_digest_per_schema": True,
        "issued_record_count": 0,
    }
    return {
        **body,
        "catalog_sha256": sha256_bytes(
            b"heterodiff-a1-r1-successor-contract-catalog-v1\0" + canonical_json(body)
        ),
    }


__all__ = [
    "ADAPTER_BOOTSTRAP_SPEC_SCHEMA",
    "AUTHORITY_DOMAIN",
    "AdapterBootstrapSpecV1",
    "BOOTSTRAP_ENVIRONMENT",
    "BOOTSTRAP_FORBIDDEN_INHERITED_ENVIRONMENT_KEYS",
    "BOOTSTRAP_INTERPRETER_FLAGS",
    "BOOTSTRAP_INTERPRETER_RELATIVE_PATH",
    "BOOTSTRAP_SYS_PATH_ORDER",
    "COORDINATE_PHASES",
    "CONTRACT_SPECS",
    "ContractError",
    "CoordinateCompletionV1",
    "CoordinateConsumptionV1",
    "CoordinatePermitV1",
    "CoordinateRequestV1",
    "MILESTONE_STATE",
    "MaterializedSourceCapsuleManifestV1",
    "PHASE_EVENT_ORDINAL",
    "PRECREATION_ATTEMPT_MARKER_SCHEMA",
    "PrecreationAttemptMarkerV1",
    "PhaseAggregateAdmissionV1",
    "PhaseAuthorizationV1",
    "PrimaryMetricsAdmissionV1",
    "PrimaryMetricsCompletionV1",
    "PrimaryMetricsRequestV1",
    "QUALIFICATION_SCHEMA",
    "REGISTRATION_SCHEMA",
    "RECORD_TYPES",
    "RankAdmissionV1",
    "RankCompletionV1",
    "RankRequestV1",
    "RuntimeApprovalV1",
    "RuntimeCandidateV1",
    "RuntimeReviewV1",
    "PrerequisiteEvidenceV1",
    "PREREQUISITE_EVIDENCE_SCHEMA",
    "SourceCapsuleAdmissionV1",
    "SOURCE_CAPSULE_ADMISSION_SCHEMA",
    "StrictCanonicalRecord",
    "SuccessorActivationV1",
    "SuccessorPlanV1",
    "canonical_json",
    "contract_catalog",
    "require_sha256",
    "sha256_bytes",
]
