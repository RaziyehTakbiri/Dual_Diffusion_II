"""Pure validation for the additive B08 Databricks Jobs-lifecycle successor.

This module validates caller-supplied canonical records only.  It performs no
I/O, network access, Databricks operation, environment capture, subprocess
launch, entropy draw, calibration, data access, authentication, reservation,
or project-state edit.

``ELIGIBLE_FOR_DATA_FREE_JOB_LIFECYCLE_REVIEW_ONLY`` means that a supplied
record satisfies this successor's structural contract.  It is not evidence
authentication, Stage-C acceptance, calibration authority, B08 closure, or
authority to access study or test data.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Dict, Iterable


SCHEMA_VERSION = "heterodiff-b08-databricks-aws-job-lifecycle-v1"
LIFECYCLE_POLICY_ID = "B08_CLASSIC_JOB_COMPUTE_SINGLE_AUTHORIZED_RUN_LIFECYCLE_V1"
MAXIMUM_JOB_TIMEOUT_SECONDS = 86_400
MAXIMUM_TASK_TIMEOUT_SECONDS = 86_400

HOLD_INCOMPLETE = "HOLD_INCOMPLETE"
ELIGIBLE_FOR_DATA_FREE_JOB_LIFECYCLE_REVIEW_ONLY = (
    "ELIGIBLE_FOR_DATA_FREE_JOB_LIFECYCLE_REVIEW_ONLY"
)
SEMANTIC_DISPOSITIONS = (
    HOLD_INCOMPLETE,
    ELIGIBLE_FOR_DATA_FREE_JOB_LIFECYCLE_REVIEW_ONLY,
)

_HEX_DIGITS = frozenset("0123456789abcdef")
_IDENTIFIER_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:/+-"
)

_TOP_LEVEL_KEYS = (
    "schema_version",
    "record_sha256",
    "semantic_disposition",
    "job_definition",
    "run_observation",
    "durable_handoff",
    "authority_boundary",
    "project_effects",
)

_JOB_DEFINITION_KEYS = (
    "policy_id",
    "cloud_provider",
    "service",
    "compute_kind",
    "access_mode",
    "new_cluster_per_run",
    "existing_cluster_id_present",
    "manual_trigger_only",
    "authorized_manual_run_budget",
    "schedule_present",
    "continuous_trigger_present",
    "event_trigger_present",
    "queue_enabled",
    "max_concurrent_runs",
    "task_count",
    "synchronous_task",
    "detached_or_background_process_allowed",
    "job_max_retries",
    "task_max_retries",
    "retry_on_timeout",
    "job_timeout_seconds",
    "task_timeout_seconds",
    "repair_runs_allowed",
    "partial_reruns_allowed",
    "restarts_allowed",
    "replacement_attempts_allowed",
    "autotermination_minutes",
    "autotermination_zero_required",
    "autotermination_is_continuity_evidence",
    "canonical_job_definition_sha256",
    "canonical_cluster_spec_sha256",
    "cluster_policy_sha256",
    "source_manifest_sha256",
    "digest_addressed_container_image",
    "job_definition_contains_secrets",
)

_RUN_OBSERVATION_KEYS = (
    "authorization_receipt_sha256",
    "observed_authorized_run_count",
    "run_id",
    "attempt_number",
    "original_attempt_run_id_present",
    "repair_history_count",
    "restart_count",
    "replacement_compute_count",
    "observed_compute_id_count",
    "observed_task_run_count",
    "queued_state_observed",
    "provider_interruption_or_timeout_observed",
    "definition_match_verified",
    "source_match_verified",
    "terminal_life_cycle_state",
    "terminal_result_state",
    "termination_after_task_verified",
    "no_automatic_successor_run_verified",
    "started_attempt_charged",
    "terminal_run_record_sha256",
    "lifecycle_event_log_sha256",
    "job_compute_termination_receipt_sha256",
)

_DURABLE_HANDOFF_KEYS = (
    "transient_stage_kind",
    "transient_stage_is_durable_evidence",
    "local_receipt_validated_before_handoff",
    "exclusive_no_clobber_handoff",
    "approved_private_durable_channel",
    "approved_private_durable_destination_binding_sha256",
    "durable_copy_reopened_and_rehashed",
    "local_receipt_byte_count",
    "durable_copy_byte_count",
    "local_receipt_sha256",
    "durable_copy_sha256",
    "commit_manifest_written_last",
    "durable_commit_manifest_sha256",
    "job_task_returned_after_durable_commit",
    "workspace_or_git_used_as_durable_evidence",
    "notebook_or_job_output_used_as_durable_evidence",
    "transient_stage_counted_as_storage_reservation",
    "lifecycle_logs_delivered_to_durable_sink",
    "post_termination_external_review_required",
)

_AUTHORITY_BOUNDARY_KEYS = (
    "module_performs_io",
    "module_performs_network_or_databricks_calls",
    "module_authenticates_external_evidence",
    "study_data_access_authorized",
    "test_data_access_authorized",
    "scientific_execution_authorized",
    "data_free_calibration_authorized",
    "training_or_inference_authorized",
    "lifecycle_record_alone_closes_b08",
    "later_independent_review_required",
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


class JobLifecycleError(ValueError):
    """The supplied Jobs-lifecycle record is malformed or ineligible."""


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
                raise JobLifecycleError(name + " contains a non-string key")
            _require_json_native(item, name=name + "." + key)
        return
    raise JobLifecycleError(name + " contains a non-exact JSON-native type")


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
        raise JobLifecycleError("value is not canonical JSON") from error
    return encoded.encode("ascii")


def _exact_object(value: object, keys: Iterable[str], *, name: str) -> dict:
    if type(value) is not dict:
        raise JobLifecycleError(name + " must be an exact object")
    expected = frozenset(keys)
    if frozenset(value) != expected or any(type(key) is not str for key in value):
        raise JobLifecycleError(name + " has missing or unknown keys")
    return value


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise JobLifecycleError(name + " must be an exact boolean")
    return value


def _exact_nonnegative_int(value: object, *, name: str) -> int:
    if type(value) is not int or value < 0:
        raise JobLifecycleError(name + " must be an exact nonnegative integer")
    return value


def _exact_positive_int(value: object, *, name: str) -> int:
    result = _exact_nonnegative_int(value, name=name)
    if result == 0:
        raise JobLifecycleError(name + " must be positive")
    return result


def _exact_identifier(value: object, *, name: str, maximum: int = 256) -> str:
    if (
        type(value) is not str
        or not value
        or len(value) > maximum
        or any(character not in _IDENTIFIER_CHARACTERS for character in value)
    ):
        raise JobLifecycleError(name + " must be a bounded exact identifier")
    return value


def _exact_sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX_DIGITS for character in value)
    ):
        raise JobLifecycleError(name + " must be a lowercase SHA-256 digest")
    return value


def _exact_digest_addressed_image(value: object, *, name: str) -> str:
    if type(value) is not str or not value or len(value) > 1024:
        raise JobLifecycleError(name + " must be a bounded image reference")
    if any(ord(character) < 0x21 or ord(character) > 0x7E for character in value):
        raise JobLifecycleError(name + " contains forbidden characters")
    marker = "@sha256:"
    if value.count(marker) != 1:
        raise JobLifecycleError(name + " must contain one digest address")
    repository, digest = value.rsplit(marker, 1)
    if not repository or "@" in repository:
        raise JobLifecycleError(name + " has an invalid repository component")
    _exact_sha256(digest, name=name + ".digest")
    return value


def _nullable_bool(value: object, *, name: str) -> None:
    if value is not None:
        _exact_bool(value, name=name)


def _nullable_nonnegative_int(value: object, *, name: str) -> None:
    if value is not None:
        _exact_nonnegative_int(value, name=name)


def _nullable_positive_int(value: object, *, name: str) -> None:
    if value is not None:
        _exact_positive_int(value, name=name)


def _nullable_identifier(value: object, *, name: str) -> None:
    if value is not None:
        _exact_identifier(value, name=name)


def _nullable_sha256(value: object, *, name: str) -> None:
    if value is not None:
        _exact_sha256(value, name=name)


def _nullable_digest_addressed_image(value: object, *, name: str) -> None:
    if value is not None:
        _exact_digest_addressed_image(value, name=name)


def _contains_none(value: object) -> bool:
    if value is None:
        return True
    if type(value) is list:
        return any(_contains_none(item) for item in value)
    if type(value) is dict:
        return any(_contains_none(item) for item in value.values())
    return False


def _authority_boundary() -> Dict[str, object]:
    return {
        "module_performs_io": False,
        "module_performs_network_or_databricks_calls": False,
        "module_authenticates_external_evidence": False,
        "study_data_access_authorized": False,
        "test_data_access_authorized": False,
        "scientific_execution_authorized": False,
        "data_free_calibration_authorized": False,
        "training_or_inference_authorized": False,
        "lifecycle_record_alone_closes_b08": False,
        "later_independent_review_required": True,
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


def semantic_projection(record: object) -> Dict[str, object]:
    """Return the exact record projection covered by ``record_sha256``."""

    value = _exact_object(record, _TOP_LEVEL_KEYS, name="record")
    result = deepcopy(value)
    result.pop("record_sha256")
    return result


def semantic_sha256(record: object) -> str:
    """Hash the canonical semantic projection of a lifecycle record."""

    return hashlib.sha256(canonical_json_bytes(semantic_projection(record))).hexdigest()


def with_semantic_digest(record: object) -> Dict[str, object]:
    """Return an exact copy with its semantic digest carrier populated."""

    value = _exact_object(record, _TOP_LEVEL_KEYS, name="record")
    result = deepcopy(value)
    result["record_sha256"] = semantic_sha256(result)
    return result


def build_empty_template() -> Dict[str, object]:
    """Return the zero-effect HOLD template for this additive successor."""

    record: Dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "record_sha256": "0" * 64,
        "semantic_disposition": HOLD_INCOMPLETE,
        "job_definition": {
            "policy_id": LIFECYCLE_POLICY_ID,
            "cloud_provider": "AWS",
            "service": "DATABRICKS",
            "compute_kind": None,
            "access_mode": None,
            "new_cluster_per_run": False,
            "existing_cluster_id_present": None,
            "manual_trigger_only": False,
            "authorized_manual_run_budget": None,
            "schedule_present": None,
            "continuous_trigger_present": None,
            "event_trigger_present": None,
            "queue_enabled": None,
            "max_concurrent_runs": None,
            "task_count": None,
            "synchronous_task": False,
            "detached_or_background_process_allowed": False,
            "job_max_retries": None,
            "task_max_retries": None,
            "retry_on_timeout": None,
            "job_timeout_seconds": None,
            "task_timeout_seconds": None,
            "repair_runs_allowed": False,
            "partial_reruns_allowed": False,
            "restarts_allowed": False,
            "replacement_attempts_allowed": False,
            "autotermination_minutes": None,
            "autotermination_zero_required": False,
            "autotermination_is_continuity_evidence": False,
            "canonical_job_definition_sha256": None,
            "canonical_cluster_spec_sha256": None,
            "cluster_policy_sha256": None,
            "source_manifest_sha256": None,
            "digest_addressed_container_image": None,
            "job_definition_contains_secrets": None,
        },
        "run_observation": {
            "authorization_receipt_sha256": None,
            "observed_authorized_run_count": None,
            "run_id": None,
            "attempt_number": None,
            "original_attempt_run_id_present": None,
            "repair_history_count": None,
            "restart_count": None,
            "replacement_compute_count": None,
            "observed_compute_id_count": None,
            "observed_task_run_count": None,
            "queued_state_observed": None,
            "provider_interruption_or_timeout_observed": None,
            "definition_match_verified": False,
            "source_match_verified": False,
            "terminal_life_cycle_state": None,
            "terminal_result_state": None,
            "termination_after_task_verified": False,
            "no_automatic_successor_run_verified": False,
            "started_attempt_charged": False,
            "terminal_run_record_sha256": None,
            "lifecycle_event_log_sha256": None,
            "job_compute_termination_receipt_sha256": None,
        },
        "durable_handoff": {
            "transient_stage_kind": "PRIVATE_LOCAL_DRIVER_ONLY",
            "transient_stage_is_durable_evidence": False,
            "local_receipt_validated_before_handoff": False,
            "exclusive_no_clobber_handoff": False,
            "approved_private_durable_channel": False,
            "approved_private_durable_destination_binding_sha256": None,
            "durable_copy_reopened_and_rehashed": False,
            "local_receipt_byte_count": None,
            "durable_copy_byte_count": None,
            "local_receipt_sha256": None,
            "durable_copy_sha256": None,
            "commit_manifest_written_last": False,
            "durable_commit_manifest_sha256": None,
            "job_task_returned_after_durable_commit": False,
            "workspace_or_git_used_as_durable_evidence": False,
            "notebook_or_job_output_used_as_durable_evidence": False,
            "transient_stage_counted_as_storage_reservation": False,
            "lifecycle_logs_delivered_to_durable_sink": False,
            "post_termination_external_review_required": True,
        },
        "authority_boundary": _authority_boundary(),
        "project_effects": _project_effects(),
    }
    return with_semantic_digest(record)


def _validate_job_definition(value: object, *, eligible: bool) -> None:
    item = _exact_object(value, _JOB_DEFINITION_KEYS, name="job_definition")
    if (
        item["policy_id"] != LIFECYCLE_POLICY_ID
        or item["cloud_provider"] != "AWS"
        or item["service"] != "DATABRICKS"
    ):
        raise JobLifecycleError("job lifecycle policy identity differs")
    for key in ("compute_kind", "access_mode"):
        _nullable_identifier(item[key], name="job_definition." + key)
    for key in (
        "new_cluster_per_run",
        "existing_cluster_id_present",
        "manual_trigger_only",
        "schedule_present",
        "continuous_trigger_present",
        "event_trigger_present",
        "queue_enabled",
        "synchronous_task",
        "detached_or_background_process_allowed",
        "retry_on_timeout",
        "repair_runs_allowed",
        "partial_reruns_allowed",
        "restarts_allowed",
        "replacement_attempts_allowed",
        "job_definition_contains_secrets",
    ):
        _nullable_bool(item[key], name="job_definition." + key)
    for key in (
        "max_concurrent_runs",
        "task_count",
        "authorized_manual_run_budget",
        "job_max_retries",
        "task_max_retries",
        "autotermination_minutes",
    ):
        _nullable_nonnegative_int(item[key], name="job_definition." + key)
    for key in ("job_timeout_seconds", "task_timeout_seconds"):
        _nullable_positive_int(item[key], name="job_definition." + key)
    for key in (
        "autotermination_zero_required",
        "autotermination_is_continuity_evidence",
    ):
        if _exact_bool(item[key], name="job_definition." + key) is not False:
            raise JobLifecycleError(key + " must remain false")
    for key in (
        "canonical_job_definition_sha256",
        "canonical_cluster_spec_sha256",
        "cluster_policy_sha256",
        "source_manifest_sha256",
    ):
        _nullable_sha256(item[key], name="job_definition." + key)
    _nullable_digest_addressed_image(
        item["digest_addressed_container_image"],
        name="job_definition.digest_addressed_container_image",
    )

    if eligible:
        expected = {
            "compute_kind": "CLASSIC_JOB_COMPUTE",
            "access_mode": "DEDICATED",
            "new_cluster_per_run": True,
            "existing_cluster_id_present": False,
            "manual_trigger_only": True,
            "authorized_manual_run_budget": 1,
            "schedule_present": False,
            "continuous_trigger_present": False,
            "event_trigger_present": False,
            "queue_enabled": False,
            "max_concurrent_runs": 1,
            "task_count": 1,
            "synchronous_task": True,
            "detached_or_background_process_allowed": False,
            "job_max_retries": 0,
            "task_max_retries": 0,
            "retry_on_timeout": False,
            "repair_runs_allowed": False,
            "partial_reruns_allowed": False,
            "restarts_allowed": False,
            "replacement_attempts_allowed": False,
            "job_definition_contains_secrets": False,
        }
        for key, required in expected.items():
            if item[key] != required or type(item[key]) is not type(required):
                raise JobLifecycleError("eligible job definition differs: " + key)
        _exact_nonnegative_int(
            item["autotermination_minutes"],
            name="job_definition.autotermination_minutes",
        )
        job_timeout = _exact_positive_int(
            item["job_timeout_seconds"],
            name="job_definition.job_timeout_seconds",
        )
        task_timeout = _exact_positive_int(
            item["task_timeout_seconds"],
            name="job_definition.task_timeout_seconds",
        )
        if task_timeout > job_timeout:
            raise JobLifecycleError("task timeout exceeds job timeout")
        if job_timeout > MAXIMUM_JOB_TIMEOUT_SECONDS:
            raise JobLifecycleError("job timeout exceeds the policy bound")
        if task_timeout > MAXIMUM_TASK_TIMEOUT_SECONDS:
            raise JobLifecycleError("task timeout exceeds the policy bound")
        for key in (
            "canonical_job_definition_sha256",
            "canonical_cluster_spec_sha256",
            "cluster_policy_sha256",
            "source_manifest_sha256",
        ):
            _exact_sha256(item[key], name="job_definition." + key)
        _exact_digest_addressed_image(
            item["digest_addressed_container_image"],
            name="job_definition.digest_addressed_container_image",
        )


def _validate_run_observation(value: object, *, eligible: bool) -> None:
    item = _exact_object(value, _RUN_OBSERVATION_KEYS, name="run_observation")
    for key in (
        "authorization_receipt_sha256",
        "terminal_run_record_sha256",
        "lifecycle_event_log_sha256",
        "job_compute_termination_receipt_sha256",
    ):
        _nullable_sha256(item[key], name="run_observation." + key)
    _nullable_positive_int(item["run_id"], name="run_observation.run_id")
    for key in (
        "attempt_number",
        "observed_authorized_run_count",
        "repair_history_count",
        "restart_count",
        "replacement_compute_count",
        "observed_compute_id_count",
        "observed_task_run_count",
    ):
        _nullable_nonnegative_int(item[key], name="run_observation." + key)
    for key in (
        "original_attempt_run_id_present",
        "queued_state_observed",
        "provider_interruption_or_timeout_observed",
        "definition_match_verified",
        "source_match_verified",
        "termination_after_task_verified",
        "no_automatic_successor_run_verified",
        "started_attempt_charged",
    ):
        _nullable_bool(item[key], name="run_observation." + key)
    for key in ("terminal_life_cycle_state", "terminal_result_state"):
        _nullable_identifier(item[key], name="run_observation." + key)

    if eligible:
        expected = {
            "attempt_number": 0,
            "observed_authorized_run_count": 1,
            "original_attempt_run_id_present": False,
            "repair_history_count": 0,
            "restart_count": 0,
            "replacement_compute_count": 0,
            "observed_compute_id_count": 1,
            "observed_task_run_count": 1,
            "queued_state_observed": False,
            "provider_interruption_or_timeout_observed": False,
            "definition_match_verified": True,
            "source_match_verified": True,
            "terminal_life_cycle_state": "TERMINATED",
            "terminal_result_state": "SUCCESS",
            "termination_after_task_verified": True,
            "no_automatic_successor_run_verified": True,
            "started_attempt_charged": True,
        }
        for key, required in expected.items():
            if item[key] != required or type(item[key]) is not type(required):
                raise JobLifecycleError("eligible run observation differs: " + key)
        _exact_positive_int(item["run_id"], name="run_observation.run_id")
        for key in (
            "authorization_receipt_sha256",
            "terminal_run_record_sha256",
            "lifecycle_event_log_sha256",
            "job_compute_termination_receipt_sha256",
        ):
            _exact_sha256(item[key], name="run_observation." + key)


def _validate_durable_handoff(value: object, *, eligible: bool) -> None:
    item = _exact_object(value, _DURABLE_HANDOFF_KEYS, name="durable_handoff")
    if item["transient_stage_kind"] != "PRIVATE_LOCAL_DRIVER_ONLY":
        raise JobLifecycleError("transient stage kind differs")
    fixed_false = (
        "transient_stage_is_durable_evidence",
        "workspace_or_git_used_as_durable_evidence",
        "notebook_or_job_output_used_as_durable_evidence",
        "transient_stage_counted_as_storage_reservation",
    )
    for key in fixed_false:
        if _exact_bool(item[key], name="durable_handoff." + key) is not False:
            raise JobLifecycleError(key + " must remain false")
    if (
        _exact_bool(
            item["post_termination_external_review_required"],
            name="durable_handoff.post_termination_external_review_required",
        )
        is not True
    ):
        raise JobLifecycleError("post-termination external review must remain required")
    for key in (
        "local_receipt_validated_before_handoff",
        "exclusive_no_clobber_handoff",
        "approved_private_durable_channel",
        "durable_copy_reopened_and_rehashed",
        "commit_manifest_written_last",
        "job_task_returned_after_durable_commit",
        "lifecycle_logs_delivered_to_durable_sink",
    ):
        _exact_bool(item[key], name="durable_handoff." + key)
    for key in ("local_receipt_byte_count", "durable_copy_byte_count"):
        _nullable_positive_int(item[key], name="durable_handoff." + key)
    for key in (
        "approved_private_durable_destination_binding_sha256",
        "local_receipt_sha256",
        "durable_copy_sha256",
        "durable_commit_manifest_sha256",
    ):
        _nullable_sha256(item[key], name="durable_handoff." + key)

    if eligible:
        for key in (
            "local_receipt_validated_before_handoff",
            "exclusive_no_clobber_handoff",
            "approved_private_durable_channel",
            "durable_copy_reopened_and_rehashed",
            "commit_manifest_written_last",
            "job_task_returned_after_durable_commit",
            "lifecycle_logs_delivered_to_durable_sink",
        ):
            if item[key] is not True:
                raise JobLifecycleError("eligible durable handoff differs: " + key)
        local_bytes = _exact_positive_int(
            item["local_receipt_byte_count"],
            name="durable_handoff.local_receipt_byte_count",
        )
        durable_bytes = _exact_positive_int(
            item["durable_copy_byte_count"],
            name="durable_handoff.durable_copy_byte_count",
        )
        if local_bytes != durable_bytes:
            raise JobLifecycleError("durable handoff byte counts differ")
        local_digest = _exact_sha256(
            item["local_receipt_sha256"],
            name="durable_handoff.local_receipt_sha256",
        )
        durable_digest = _exact_sha256(
            item["durable_copy_sha256"],
            name="durable_handoff.durable_copy_sha256",
        )
        if local_digest != durable_digest:
            raise JobLifecycleError("durable handoff digests differ")
        _exact_sha256(
            item["approved_private_durable_destination_binding_sha256"],
            name=(
                "durable_handoff." "approved_private_durable_destination_binding_sha256"
            ),
        )
        _exact_sha256(
            item["durable_commit_manifest_sha256"],
            name="durable_handoff.durable_commit_manifest_sha256",
        )


def validate_record(record: object) -> Dict[str, object]:
    """Validate and return an exact deep copy of a lifecycle record."""

    value = _exact_object(record, _TOP_LEVEL_KEYS, name="record")
    _require_json_native(value, name="record")
    if value["schema_version"] != SCHEMA_VERSION:
        raise JobLifecycleError("schema_version differs")
    if (
        type(value["semantic_disposition"]) is not str
        or value["semantic_disposition"] not in SEMANTIC_DISPOSITIONS
    ):
        raise JobLifecycleError("semantic disposition differs")
    _exact_sha256(value["record_sha256"], name="record.record_sha256")
    if value["record_sha256"] != semantic_sha256(value):
        raise JobLifecycleError("semantic digest differs")

    eligible = (
        value["semantic_disposition"]
        == ELIGIBLE_FOR_DATA_FREE_JOB_LIFECYCLE_REVIEW_ONLY
    )
    _validate_job_definition(value["job_definition"], eligible=eligible)
    _validate_run_observation(value["run_observation"], eligible=eligible)
    _validate_durable_handoff(value["durable_handoff"], eligible=eligible)
    if value["authority_boundary"] != _authority_boundary():
        raise JobLifecycleError("authority boundary differs")
    if value["project_effects"] != _project_effects():
        raise JobLifecycleError("project effects must remain exactly zero")
    _exact_object(
        value["authority_boundary"],
        _AUTHORITY_BOUNDARY_KEYS,
        name="authority_boundary",
    )
    _exact_object(
        value["project_effects"],
        _PROJECT_EFFECT_KEYS,
        name="project_effects",
    )
    if eligible and _contains_none(value):
        raise JobLifecycleError("eligible record contains an unknown value")
    return deepcopy(value)


__all__ = (
    "ELIGIBLE_FOR_DATA_FREE_JOB_LIFECYCLE_REVIEW_ONLY",
    "HOLD_INCOMPLETE",
    "JobLifecycleError",
    "LIFECYCLE_POLICY_ID",
    "MAXIMUM_JOB_TIMEOUT_SECONDS",
    "MAXIMUM_TASK_TIMEOUT_SECONDS",
    "SCHEMA_VERSION",
    "SEMANTIC_DISPOSITIONS",
    "build_empty_template",
    "canonical_json_bytes",
    "semantic_projection",
    "semantic_sha256",
    "validate_record",
    "with_semantic_digest",
)
