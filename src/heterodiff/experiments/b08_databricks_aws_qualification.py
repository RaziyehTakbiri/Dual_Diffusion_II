"""Pure AWS Databricks Wave-2 qualification-receipt validation.

This module defines a fail-closed, standard-library-only schema.  It performs
no I/O, network access, subprocess launch, entropy draw, environment capture,
calibration, data access, reservation, authentication, or project-state edit.

``ELIGIBLE_FOR_DATA_FREE_CALIBRATION_ONLY`` means only that caller-supplied
evidence satisfies the frozen structural prerequisites for a later separately
authorized data-free calibration.  It never closes a field or blocker and does
not authorize study or test-data access.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Dict, Iterable


SCHEMA_VERSION = "heterodiff-b08-databricks-aws-qualification-v1"

HOLD_INCOMPLETE = "HOLD_INCOMPLETE"
ELIGIBLE_FOR_DATA_FREE_CALIBRATION_ONLY = (
    "ELIGIBLE_FOR_DATA_FREE_CALIBRATION_ONLY"
)
SEMANTIC_DISPOSITIONS = (
    HOLD_INCOMPLETE,
    ELIGIBLE_FOR_DATA_FREE_CALIBRATION_ONLY,
)

DESTINATION_RESERVATION_BYTES = 1_099_511_627_776
AUXILIARY_RESERVATION_BYTES = 34_359_738_368
COMBINED_RESERVATION_BYTES = 1_133_871_366_144
MINIMUM_AVAILABLE_INODES_AFTER_RESERVATION = 4_096

F104_EVENT_IDS = (
    "BASE_FORWARD",
    "BASE_BACKWARD",
    "CONDITIONER_FORWARD",
    "CONDITIONER_BACKWARD",
    "GUIDE_EVALUATION",
    "RESAMPLING_STEP",
    "ODE_OR_SDE_STEP",
    "DATA_ADAPTER_RECORD",
    "METRIC_DRAW_EVALUATION",
    "OTHER_DECLARED_OPERATION",
)

HARD_AXIS_IDS = (
    "WALL_TIME",
    "ACCELERATOR_TIME",
    "PEAK_DEVICE_MEMORY",
    "PEAK_HOST_MEMORY",
    "MODEL_EVALUATION_COUNT",
    "PERSISTENT_BYTES",
    "FAILURE_COUNT",
    "PARAMETER_COUNT",
)

DETERMINISTIC_ENVIRONMENT_CONTROLS = {
    "BLIS_NUM_THREADS": "1",
    "CUDA_VISIBLE_DEVICES": "",
    "LANG": "C",
    "LC_ALL": "C",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONSAFEPATH": "1",
    "PYTHONUTF8": "1",
    "TZ": "UTC",
    "VECLIB_MAXIMUM_THREADS": "1",
}

_HEX_DIGITS = frozenset("0123456789abcdef")
_IDENTIFIER_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:/+-"
)

_TOP_LEVEL_KEYS = (
    "schema_version",
    "record_sha256",
    "semantic_disposition",
    "infrastructure",
    "deterministic_policy",
    "storage_reservation",
    "calibration_boundary",
    "authority_boundary",
    "project_effects",
)

_INFRASTRUCTURE_KEYS = (
    "cloud_provider",
    "service",
    "compute_mode",
    "dedicated_compute",
    "worker_count",
    "fixed_instance_topology_verified",
    "autoscaling_enabled",
    "dynamic_allocation_enabled",
    "spot_instances_enabled",
    "preemptible_instances_enabled",
    "on_demand_only",
    "automatic_job_retry_enabled",
    "spark_speculation_enabled",
    "cpu_only",
    "gpu_enabled",
    "photon_enabled",
    "databricks_runtime_version",
    "databricks_runtime_sha256",
    "immutable_container_digest",
    "cluster_policy_sha256",
    "canonical_secret_free_cluster_config_sha256",
    "cluster_config_canonicalization_verified",
    "cluster_config_contains_secrets",
    "complete_runtime_dependency_manifest_sha256",
    "runtime_dependency_manifest_complete",
    "availability_reservation_receipt_sha256",
    "output_location_binding_sha256",
    "log_location_binding_sha256",
    "output_and_log_locations_fixed",
)

_DETERMINISTIC_POLICY_KEYS = (
    "policy_id",
    "accelerator_policy",
    "single_thread_required",
    "unsupported_or_nondeterministic_operation_disposition",
    "environment",
    "torch_deterministic_algorithms",
    "torch_warn_only",
    "torch_intraop_threads",
    "torch_interop_threads",
    "cudnn_benchmark",
)

_STORAGE_KEYS = (
    "admin_record_schema",
    "admin_record_sha256",
    "admin_principal_id",
    "externally_verified",
    "verification_method_id",
    "destination_reservation_bytes",
    "auxiliary_reservation_bytes",
    "combined_reservation_bytes",
    "available_inodes_after_reservation",
    "same_qualified_storage_root_verified",
    "destination_and_auxiliary_exclusive_verified",
    "destination_and_auxiliary_disjoint_verified",
    "non_sparse_allocation_verified",
    "enforced_quota_verified",
    "reservation_durable_verified",
    "no_double_count_verified",
    "retained_through_commit_verified",
)

_CALIBRATION_BOUNDARY_KEYS = (
    "f104_event_ids",
    "hard_axis_ids",
    "data_free_calibration_performed",
    "f104_weights_created",
    "scalar_ceiling_created",
    "hard_axis_ceilings_created",
    "later_separate_authority_required",
)

_AUTHORITY_BOUNDARY_KEYS = (
    "study_data_access_authorized",
    "test_data_access_authorized",
    "scientific_execution_authorized",
    "training_or_inference_authorized",
    "external_contact_performed_by_module",
    "network_access_performed_by_module",
    "reservation_performed_by_module",
    "environment_capture_performed_by_module",
    "admin_receipt_authenticity_asserted_by_caller_not_module",
)

_PROJECT_EFFECT_KEYS = (
    "field_ids_closed",
    "field_count_delta",
    "blocker_ids_closed",
    "blocker_count_delta",
    "timetable_tasks_closed",
    "timetable_checkbox_delta",
    "formal_test_delta",
    "result_slot_delta",
    "b08_closed",
    "tracker_or_evidence_ledger_edited",
)


class QualificationError(ValueError):
    """The supplied qualification record is malformed or ineligible."""


def canonical_json_bytes(value: object) -> bytes:
    """Return exact canonical ASCII JSON bytes without a terminal newline."""

    _require_json_native(value, name="value")
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise QualificationError("value is not canonical JSON") from error
    return encoded.encode("ascii")


def semantic_projection(record: object) -> Dict[str, object]:
    """Return the record projection covered by ``record_sha256``."""

    value = _exact_object(record, _TOP_LEVEL_KEYS, name="record")
    projection = deepcopy(value)
    projection.pop("record_sha256")
    return projection


def semantic_sha256(record: object) -> str:
    """Hash the canonical semantic projection of a qualification record."""

    return hashlib.sha256(canonical_json_bytes(semantic_projection(record))).hexdigest()


def with_semantic_digest(record: object) -> Dict[str, object]:
    """Return an exact copy with its semantic digest carrier populated."""

    value = _exact_object(record, _TOP_LEVEL_KEYS, name="record")
    result = deepcopy(value)
    result["record_sha256"] = semantic_sha256(result)
    return result


def _require_json_native(value: object, *, name: str) -> None:
    value_type = type(value)
    if value is None or value_type in (str, int, bool):
        return
    if value_type is list:
        for ordinal, item in enumerate(value):
            _require_json_native(item, name=f"{name}[{ordinal}]")
        return
    if value_type is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise QualificationError(name + " contains a non-string key")
            _require_json_native(item, name=name + "." + key)
        return
    raise QualificationError(name + " contains a non-exact JSON-native type")


def _exact_object(value: object, keys: Iterable[str], *, name: str) -> dict:
    if type(value) is not dict:
        raise QualificationError(name + " must be an exact object")
    expected = frozenset(keys)
    if frozenset(value) != expected or any(type(key) is not str for key in value):
        raise QualificationError(name + " has missing or unknown keys")
    return value


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise QualificationError(name + " must be an exact boolean")
    return value


def _exact_nonnegative_int(value: object, *, name: str) -> int:
    if type(value) is not int or value < 0:
        raise QualificationError(name + " must be an exact nonnegative integer")
    return value


def _exact_positive_int(value: object, *, name: str) -> int:
    result = _exact_nonnegative_int(value, name=name)
    if result == 0:
        raise QualificationError(name + " must be positive")
    return result


def _exact_identifier(value: object, *, name: str, maximum: int = 256) -> str:
    if (
        type(value) is not str
        or not value
        or len(value) > maximum
        or any(character not in _IDENTIFIER_CHARACTERS for character in value)
    ):
        raise QualificationError(name + " must be a bounded exact identifier")
    return value


def _exact_sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX_DIGITS for character in value)
    ):
        raise QualificationError(name + " must be a lowercase SHA-256 digest")
    return value


def _nullable_identifier(value: object, *, name: str) -> None:
    if value is not None:
        _exact_identifier(value, name=name)


def _nullable_sha256(value: object, *, name: str) -> None:
    if value is not None:
        _exact_sha256(value, name=name)


def _nullable_positive_int(value: object, *, name: str) -> None:
    if value is not None:
        _exact_positive_int(value, name=name)


def _contains_none(value: object) -> bool:
    if value is None:
        return True
    if type(value) is list:
        return any(_contains_none(item) for item in value)
    if type(value) is dict:
        return any(_contains_none(item) for item in value.values())
    return False


def _deterministic_policy() -> Dict[str, object]:
    return {
        "policy_id": "B08_CPU_SINGLE_THREAD_FAIL_CLOSED_DETERMINISM_V1",
        "accelerator_policy": "CPU_ONLY_CUDA_AND_MPS_DISABLED",
        "single_thread_required": True,
        "unsupported_or_nondeterministic_operation_disposition": (
            "TERMINAL_PREEXECUTION_NO_GO_NO_FALLBACK"
        ),
        "environment": dict(DETERMINISTIC_ENVIRONMENT_CONTROLS),
        "torch_deterministic_algorithms": True,
        "torch_warn_only": False,
        "torch_intraop_threads": 1,
        "torch_interop_threads": 1,
        "cudnn_benchmark": False,
    }


def _calibration_boundary() -> Dict[str, object]:
    return {
        "f104_event_ids": list(F104_EVENT_IDS),
        "hard_axis_ids": list(HARD_AXIS_IDS),
        "data_free_calibration_performed": False,
        "f104_weights_created": False,
        "scalar_ceiling_created": False,
        "hard_axis_ceilings_created": False,
        "later_separate_authority_required": True,
    }


def _authority_boundary() -> Dict[str, object]:
    return {
        "study_data_access_authorized": False,
        "test_data_access_authorized": False,
        "scientific_execution_authorized": False,
        "training_or_inference_authorized": False,
        "external_contact_performed_by_module": False,
        "network_access_performed_by_module": False,
        "reservation_performed_by_module": False,
        "environment_capture_performed_by_module": False,
        "admin_receipt_authenticity_asserted_by_caller_not_module": True,
    }


def _project_effects() -> Dict[str, object]:
    return {
        "field_ids_closed": [],
        "field_count_delta": 0,
        "blocker_ids_closed": [],
        "blocker_count_delta": 0,
        "timetable_tasks_closed": [],
        "timetable_checkbox_delta": 0,
        "formal_test_delta": 0,
        "result_slot_delta": 0,
        "b08_closed": False,
        "tracker_or_evidence_ledger_edited": False,
    }


def build_empty_template() -> Dict[str, object]:
    """Return a sealed HOLD template with every external fact unpopulated."""

    record: Dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "record_sha256": "0" * 64,
        "semantic_disposition": HOLD_INCOMPLETE,
        "infrastructure": {
            "cloud_provider": "AWS",
            "service": "DATABRICKS",
            "compute_mode": None,
            "dedicated_compute": False,
            "worker_count": None,
            "fixed_instance_topology_verified": False,
            "autoscaling_enabled": None,
            "dynamic_allocation_enabled": None,
            "spot_instances_enabled": None,
            "preemptible_instances_enabled": None,
            "on_demand_only": None,
            "automatic_job_retry_enabled": None,
            "spark_speculation_enabled": None,
            "cpu_only": None,
            "gpu_enabled": None,
            "photon_enabled": None,
            "databricks_runtime_version": None,
            "databricks_runtime_sha256": None,
            "immutable_container_digest": None,
            "cluster_policy_sha256": None,
            "canonical_secret_free_cluster_config_sha256": None,
            "cluster_config_canonicalization_verified": False,
            "cluster_config_contains_secrets": None,
            "complete_runtime_dependency_manifest_sha256": None,
            "runtime_dependency_manifest_complete": False,
            "availability_reservation_receipt_sha256": None,
            "output_location_binding_sha256": None,
            "log_location_binding_sha256": None,
            "output_and_log_locations_fixed": False,
        },
        "deterministic_policy": _deterministic_policy(),
        "storage_reservation": {
            "admin_record_schema": None,
            "admin_record_sha256": None,
            "admin_principal_id": None,
            "externally_verified": False,
            "verification_method_id": None,
            "destination_reservation_bytes": None,
            "auxiliary_reservation_bytes": None,
            "combined_reservation_bytes": None,
            "available_inodes_after_reservation": None,
            "same_qualified_storage_root_verified": False,
            "destination_and_auxiliary_exclusive_verified": False,
            "destination_and_auxiliary_disjoint_verified": False,
            "non_sparse_allocation_verified": False,
            "enforced_quota_verified": False,
            "reservation_durable_verified": False,
            "no_double_count_verified": False,
            "retained_through_commit_verified": False,
        },
        "calibration_boundary": _calibration_boundary(),
        "authority_boundary": _authority_boundary(),
        "project_effects": _project_effects(),
    }
    return with_semantic_digest(record)


def _validate_infrastructure(value: object, *, eligible: bool) -> None:
    item = _exact_object(value, _INFRASTRUCTURE_KEYS, name="infrastructure")
    if item["cloud_provider"] != "AWS" or item["service"] != "DATABRICKS":
        raise QualificationError("AWS Databricks identity differs")
    _nullable_identifier(item["compute_mode"], name="infrastructure.compute_mode")
    _exact_bool(item["dedicated_compute"], name="infrastructure.dedicated_compute")
    if item["worker_count"] is not None:
        _exact_nonnegative_int(
            item["worker_count"], name="infrastructure.worker_count"
        )
    for key in (
        "fixed_instance_topology_verified",
        "autoscaling_enabled",
        "dynamic_allocation_enabled",
        "spot_instances_enabled",
        "preemptible_instances_enabled",
        "on_demand_only",
        "automatic_job_retry_enabled",
        "spark_speculation_enabled",
        "cpu_only",
        "gpu_enabled",
        "photon_enabled",
        "cluster_config_canonicalization_verified",
        "cluster_config_contains_secrets",
        "runtime_dependency_manifest_complete",
        "output_and_log_locations_fixed",
    ):
        if item[key] is not None:
            _exact_bool(item[key], name="infrastructure." + key)
    for key in ("databricks_runtime_version",):
        _nullable_identifier(item[key], name="infrastructure." + key)
    for key in (
        "databricks_runtime_sha256",
        "immutable_container_digest",
        "cluster_policy_sha256",
        "canonical_secret_free_cluster_config_sha256",
        "complete_runtime_dependency_manifest_sha256",
        "availability_reservation_receipt_sha256",
        "output_location_binding_sha256",
        "log_location_binding_sha256",
    ):
        _nullable_sha256(item[key], name="infrastructure." + key)

    if eligible:
        expected = {
            "compute_mode": "CLASSIC_DEDICATED",
            "dedicated_compute": True,
            "fixed_instance_topology_verified": True,
            "autoscaling_enabled": False,
            "dynamic_allocation_enabled": False,
            "spot_instances_enabled": False,
            "preemptible_instances_enabled": False,
            "on_demand_only": True,
            "automatic_job_retry_enabled": False,
            "spark_speculation_enabled": False,
            "cpu_only": True,
            "gpu_enabled": False,
            "photon_enabled": False,
            "cluster_config_canonicalization_verified": True,
            "cluster_config_contains_secrets": False,
            "runtime_dependency_manifest_complete": True,
            "output_and_log_locations_fixed": True,
        }
        for key, required in expected.items():
            if item[key] != required:
                raise QualificationError("eligible infrastructure differs: " + key)
        _exact_nonnegative_int(
            item["worker_count"], name="infrastructure.worker_count"
        )
        _exact_identifier(
            item["databricks_runtime_version"],
            name="infrastructure.databricks_runtime_version",
        )
        for key in (
            "databricks_runtime_sha256",
            "immutable_container_digest",
            "cluster_policy_sha256",
            "canonical_secret_free_cluster_config_sha256",
            "complete_runtime_dependency_manifest_sha256",
            "availability_reservation_receipt_sha256",
            "output_location_binding_sha256",
            "log_location_binding_sha256",
        ):
            _exact_sha256(item[key], name="infrastructure." + key)


def _validate_deterministic_policy(value: object) -> None:
    item = _exact_object(
        value, _DETERMINISTIC_POLICY_KEYS, name="deterministic_policy"
    )
    if item != _deterministic_policy():
        raise QualificationError("deterministic policy differs from frozen policy")


def _validate_storage(value: object, *, eligible: bool) -> None:
    item = _exact_object(value, _STORAGE_KEYS, name="storage_reservation")
    for key in (
        "admin_record_schema", "admin_principal_id", "verification_method_id"
    ):
        _nullable_identifier(item[key], name="storage_reservation." + key)
    _nullable_sha256(
        item["admin_record_sha256"], name="storage_reservation.admin_record_sha256"
    )
    for key in (
        "destination_reservation_bytes",
        "auxiliary_reservation_bytes",
        "combined_reservation_bytes",
        "available_inodes_after_reservation",
    ):
        _nullable_positive_int(item[key], name="storage_reservation." + key)
    for key in (
        "externally_verified",
        "same_qualified_storage_root_verified",
        "destination_and_auxiliary_exclusive_verified",
        "destination_and_auxiliary_disjoint_verified",
        "non_sparse_allocation_verified",
        "enforced_quota_verified",
        "reservation_durable_verified",
        "no_double_count_verified",
        "retained_through_commit_verified",
    ):
        _exact_bool(item[key], name="storage_reservation." + key)

    if eligible:
        _exact_identifier(
            item["admin_record_schema"], name="storage_reservation.admin_record_schema"
        )
        _exact_sha256(
            item["admin_record_sha256"], name="storage_reservation.admin_record_sha256"
        )
        _exact_identifier(
            item["admin_principal_id"], name="storage_reservation.admin_principal_id"
        )
        _exact_identifier(
            item["verification_method_id"],
            name="storage_reservation.verification_method_id",
        )
        minimum_values = {
            "destination_reservation_bytes": DESTINATION_RESERVATION_BYTES,
            "auxiliary_reservation_bytes": AUXILIARY_RESERVATION_BYTES,
            "combined_reservation_bytes": COMBINED_RESERVATION_BYTES,
        }
        for key, minimum in minimum_values.items():
            if type(item[key]) is not int or item[key] < minimum:
                raise QualificationError("eligible storage floor differs: " + key)
        if (
            item["destination_reservation_bytes"]
            + item["auxiliary_reservation_bytes"]
            != item["combined_reservation_bytes"]
        ):
            raise QualificationError("eligible storage components do not sum")
        if (
            type(item["available_inodes_after_reservation"]) is not int
            or item["available_inodes_after_reservation"]
            < MINIMUM_AVAILABLE_INODES_AFTER_RESERVATION
        ):
            raise QualificationError("eligible inode floor is not satisfied")
        for key in (
            "externally_verified",
            "same_qualified_storage_root_verified",
            "destination_and_auxiliary_exclusive_verified",
            "destination_and_auxiliary_disjoint_verified",
            "non_sparse_allocation_verified",
            "enforced_quota_verified",
            "reservation_durable_verified",
            "no_double_count_verified",
            "retained_through_commit_verified",
        ):
            if item[key] is not True:
                raise QualificationError("eligible storage proof differs: " + key)


def _validate_calibration_boundary(value: object) -> None:
    item = _exact_object(
        value, _CALIBRATION_BOUNDARY_KEYS, name="calibration_boundary"
    )
    if item != _calibration_boundary():
        raise QualificationError("calibration boundary differs")


def _validate_authority_boundary(value: object) -> None:
    item = _exact_object(value, _AUTHORITY_BOUNDARY_KEYS, name="authority_boundary")
    if item != _authority_boundary():
        raise QualificationError("authority boundary differs")


def _validate_project_effects(value: object) -> None:
    item = _exact_object(value, _PROJECT_EFFECT_KEYS, name="project_effects")
    if item != _project_effects():
        raise QualificationError("project effects must remain exactly zero")


def validate_record(record: object) -> Dict[str, object]:
    """Validate and return an exact deep copy of a qualification record.

    Both accepted dispositions preserve zero project closure.  Eligibility is
    fail-closed and requires complete caller-supplied infrastructure and
    externally verified storage evidence; this module does not authenticate
    those external facts.
    """

    value = _exact_object(record, _TOP_LEVEL_KEYS, name="record")
    _require_json_native(value, name="record")
    if value["schema_version"] != SCHEMA_VERSION:
        raise QualificationError("schema_version differs")
    if value["semantic_disposition"] not in SEMANTIC_DISPOSITIONS or type(
        value["semantic_disposition"]
    ) is not str:
        raise QualificationError("semantic_disposition differs")
    _exact_sha256(value["record_sha256"], name="record.record_sha256")
    if value["record_sha256"] != semantic_sha256(value):
        raise QualificationError("semantic digest differs")

    eligible = (
        value["semantic_disposition"]
        == ELIGIBLE_FOR_DATA_FREE_CALIBRATION_ONLY
    )
    _validate_infrastructure(value["infrastructure"], eligible=eligible)
    _validate_deterministic_policy(value["deterministic_policy"])
    _validate_storage(value["storage_reservation"], eligible=eligible)
    _validate_calibration_boundary(value["calibration_boundary"])
    _validate_authority_boundary(value["authority_boundary"])
    _validate_project_effects(value["project_effects"])

    if eligible and _contains_none(value):
        raise QualificationError("eligible record contains an unknown value")
    return deepcopy(value)


__all__ = (
    "AUXILIARY_RESERVATION_BYTES",
    "COMBINED_RESERVATION_BYTES",
    "DESTINATION_RESERVATION_BYTES",
    "DETERMINISTIC_ENVIRONMENT_CONTROLS",
    "ELIGIBLE_FOR_DATA_FREE_CALIBRATION_ONLY",
    "F104_EVENT_IDS",
    "HARD_AXIS_IDS",
    "HOLD_INCOMPLETE",
    "MINIMUM_AVAILABLE_INODES_AFTER_RESERVATION",
    "QualificationError",
    "SCHEMA_VERSION",
    "SEMANTIC_DISPOSITIONS",
    "build_empty_template",
    "canonical_json_bytes",
    "semantic_projection",
    "semantic_sha256",
    "validate_record",
    "with_semantic_digest",
)
