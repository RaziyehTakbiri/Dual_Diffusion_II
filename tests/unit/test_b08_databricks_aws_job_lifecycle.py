from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from heterodiff.experiments import b08_databricks_aws_job_lifecycle as q


ROOT = Path(__file__).resolve().parents[2]
MACHINE = (
    ROOT
    / "research/fixtures/manuscript_v3_b08_databricks_aws_job_lifecycle_template_v1.json"
)
SOURCE = ROOT / "src/heterodiff/experiments/b08_databricks_aws_job_lifecycle.py"


def eligible_record(*, autotermination_minutes: int = 20):
    record = q.build_empty_template()
    record["semantic_disposition"] = q.ELIGIBLE_FOR_DATA_FREE_JOB_LIFECYCLE_REVIEW_ONLY
    record["job_definition"].update(
        {
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
            "job_timeout_seconds": 7_200,
            "task_timeout_seconds": 6_900,
            "repair_runs_allowed": False,
            "partial_reruns_allowed": False,
            "restarts_allowed": False,
            "replacement_attempts_allowed": False,
            "autotermination_minutes": autotermination_minutes,
            "canonical_job_definition_sha256": "1" * 64,
            "canonical_cluster_spec_sha256": "2" * 64,
            "cluster_policy_sha256": "3" * 64,
            "source_manifest_sha256": "4" * 64,
            "digest_addressed_container_image": (
                "123456789012.dkr.ecr.us-west-2.amazonaws.com/heterodiff"
                "@sha256:" + "5" * 64
            ),
            "job_definition_contains_secrets": False,
        }
    )
    record["run_observation"].update(
        {
            "authorization_receipt_sha256": "6" * 64,
            "observed_authorized_run_count": 1,
            "run_id": 123_456,
            "attempt_number": 0,
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
            "terminal_run_record_sha256": "7" * 64,
            "lifecycle_event_log_sha256": "8" * 64,
            "job_compute_termination_receipt_sha256": "9" * 64,
        }
    )
    record["durable_handoff"].update(
        {
            "local_receipt_validated_before_handoff": True,
            "exclusive_no_clobber_handoff": True,
            "approved_private_durable_channel": True,
            "approved_private_durable_destination_binding_sha256": "a" * 64,
            "durable_copy_reopened_and_rehashed": True,
            "local_receipt_byte_count": 4_096,
            "durable_copy_byte_count": 4_096,
            "local_receipt_sha256": "b" * 64,
            "durable_copy_sha256": "b" * 64,
            "commit_manifest_written_last": True,
            "durable_commit_manifest_sha256": "c" * 64,
            "job_task_returned_after_durable_commit": True,
            "lifecycle_logs_delivered_to_durable_sink": True,
        }
    )
    return q.with_semantic_digest(record)


def redigest(record):
    return q.with_semantic_digest(record)


def test_canonical_hold_template_is_exact_and_zero_delta():
    record = json.loads(MACHINE.read_text(encoding="ascii"))
    assert record == q.build_empty_template()
    assert q.validate_record(record) == record
    assert MACHINE.read_bytes() == q.canonical_json_bytes(record) + b"\n"
    assert record["semantic_disposition"] == q.HOLD_INCOMPLETE
    assert record["authority_boundary"]["later_independent_review_required"] is True
    assert record["project_effects"]["field_count_delta"] == 0
    assert record["project_effects"]["b08_closed"] is False
    assert record["project_effects"]["tracker_or_evidence_ledger_edited"] is False


@pytest.mark.parametrize("autotermination_minutes", [0, 20, 120])
def test_eligible_record_captures_autotermination_but_does_not_require_zero(
    autotermination_minutes,
):
    record = eligible_record(autotermination_minutes=autotermination_minutes)
    assert q.validate_record(record) == record
    assert (
        record["job_definition"]["autotermination_minutes"] == autotermination_minutes
    )
    assert record["job_definition"]["autotermination_zero_required"] is False
    assert record["job_definition"]["autotermination_is_continuity_evidence"] is False
    assert record["semantic_disposition"] == (
        q.ELIGIBLE_FOR_DATA_FREE_JOB_LIFECYCLE_REVIEW_ONLY
    )
    assert record["project_effects"]["b08_closed"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["job_definition"].__setitem__(
            "compute_kind", "ALL_PURPOSE_COMPUTE"
        ),
        lambda r: r["job_definition"].__setitem__("access_mode", "SHARED"),
        lambda r: r["job_definition"].__setitem__("new_cluster_per_run", False),
        lambda r: r["job_definition"].__setitem__("existing_cluster_id_present", True),
        lambda r: r["job_definition"].__setitem__("manual_trigger_only", False),
        lambda r: r["job_definition"].__setitem__("authorized_manual_run_budget", 2),
        lambda r: r["job_definition"].__setitem__("schedule_present", True),
        lambda r: r["job_definition"].__setitem__("continuous_trigger_present", True),
        lambda r: r["job_definition"].__setitem__("event_trigger_present", True),
        lambda r: r["job_definition"].__setitem__("queue_enabled", True),
        lambda r: r["job_definition"].__setitem__("max_concurrent_runs", 2),
        lambda r: r["job_definition"].__setitem__("task_count", 2),
        lambda r: r["job_definition"].__setitem__("synchronous_task", False),
        lambda r: r["job_definition"].__setitem__(
            "detached_or_background_process_allowed", True
        ),
        lambda r: r["job_definition"].__setitem__("job_max_retries", 1),
        lambda r: r["job_definition"].__setitem__("task_max_retries", 1),
        lambda r: r["job_definition"].__setitem__("retry_on_timeout", True),
        lambda r: r["job_definition"].__setitem__("job_timeout_seconds", 0),
        lambda r: r["job_definition"].__setitem__(
            "job_timeout_seconds", q.MAXIMUM_JOB_TIMEOUT_SECONDS + 1
        ),
        lambda r: r["job_definition"].__setitem__("task_timeout_seconds", 7_201),
        lambda r: r["job_definition"].__setitem__("repair_runs_allowed", True),
        lambda r: r["job_definition"].__setitem__("partial_reruns_allowed", True),
        lambda r: r["job_definition"].__setitem__("restarts_allowed", True),
        lambda r: r["job_definition"].__setitem__("replacement_attempts_allowed", True),
        lambda r: r["job_definition"].__setitem__(
            "autotermination_zero_required", True
        ),
        lambda r: r["job_definition"].__setitem__(
            "autotermination_is_continuity_evidence", True
        ),
        lambda r: r["job_definition"].__setitem__("source_manifest_sha256", None),
        lambda r: r["job_definition"].__setitem__(
            "digest_addressed_container_image", "heterodiff:latest"
        ),
        lambda r: r["job_definition"].__setitem__(
            "job_definition_contains_secrets", True
        ),
        lambda r: r["run_observation"].__setitem__(
            "authorization_receipt_sha256", None
        ),
        lambda r: r["run_observation"].__setitem__("observed_authorized_run_count", 2),
        lambda r: r["run_observation"].__setitem__("attempt_number", 1),
        lambda r: r["run_observation"].__setitem__(
            "original_attempt_run_id_present", True
        ),
        lambda r: r["run_observation"].__setitem__("repair_history_count", 1),
        lambda r: r["run_observation"].__setitem__("restart_count", 1),
        lambda r: r["run_observation"].__setitem__("replacement_compute_count", 1),
        lambda r: r["run_observation"].__setitem__("observed_compute_id_count", 2),
        lambda r: r["run_observation"].__setitem__("observed_task_run_count", 2),
        lambda r: r["run_observation"].__setitem__("queued_state_observed", True),
        lambda r: r["run_observation"].__setitem__(
            "provider_interruption_or_timeout_observed", True
        ),
        lambda r: r["run_observation"].__setitem__("definition_match_verified", False),
        lambda r: r["run_observation"].__setitem__("source_match_verified", False),
        lambda r: r["run_observation"].__setitem__(
            "terminal_life_cycle_state", "RUNNING"
        ),
        lambda r: r["run_observation"].__setitem__("terminal_result_state", "FAILED"),
        lambda r: r["run_observation"].__setitem__(
            "termination_after_task_verified", False
        ),
        lambda r: r["run_observation"].__setitem__(
            "no_automatic_successor_run_verified", False
        ),
        lambda r: r["run_observation"].__setitem__("started_attempt_charged", False),
        lambda r: r["run_observation"].__setitem__(
            "job_compute_termination_receipt_sha256", None
        ),
        lambda r: r["durable_handoff"].__setitem__(
            "local_receipt_validated_before_handoff", False
        ),
        lambda r: r["durable_handoff"].__setitem__(
            "exclusive_no_clobber_handoff", False
        ),
        lambda r: r["durable_handoff"].__setitem__(
            "approved_private_durable_channel", False
        ),
        lambda r: r["durable_handoff"].__setitem__(
            "approved_private_durable_destination_binding_sha256", None
        ),
        lambda r: r["durable_handoff"].__setitem__(
            "durable_copy_reopened_and_rehashed", False
        ),
        lambda r: r["durable_handoff"].__setitem__("durable_copy_byte_count", 4_095),
        lambda r: r["durable_handoff"].__setitem__("durable_copy_sha256", "d" * 64),
        lambda r: r["durable_handoff"].__setitem__(
            "commit_manifest_written_last", False
        ),
        lambda r: r["durable_handoff"].__setitem__(
            "job_task_returned_after_durable_commit", False
        ),
        lambda r: r["durable_handoff"].__setitem__(
            "workspace_or_git_used_as_durable_evidence", True
        ),
        lambda r: r["durable_handoff"].__setitem__(
            "notebook_or_job_output_used_as_durable_evidence", True
        ),
        lambda r: r["durable_handoff"].__setitem__(
            "transient_stage_counted_as_storage_reservation", True
        ),
        lambda r: r["durable_handoff"].__setitem__(
            "lifecycle_logs_delivered_to_durable_sink", False
        ),
        lambda r: r["durable_handoff"].__setitem__(
            "post_termination_external_review_required", False
        ),
        lambda r: r["authority_boundary"].__setitem__(
            "study_data_access_authorized", True
        ),
        lambda r: r["project_effects"].__setitem__("b08_closed", True),
        lambda r: r["job_definition"].__setitem__("unknown_key", False),
    ],
)
def test_hostile_eligibility_mutations_fail_closed(mutation):
    record = eligible_record()
    mutation(record)
    with pytest.raises(q.JobLifecycleError):
        q.validate_record(redigest(record))


def test_digest_tamper_unknown_top_level_and_boolean_integer_alias_fail():
    record = eligible_record()
    record["job_definition"]["queue_enabled"] = True
    with pytest.raises(q.JobLifecycleError, match="semantic digest"):
        q.validate_record(record)

    record = eligible_record()
    record["unknown_key"] = False
    with pytest.raises(q.JobLifecycleError, match="missing or unknown"):
        q.validate_record(record)

    record = eligible_record()
    record["job_definition"]["authorized_manual_run_budget"] = True
    with pytest.raises(q.JobLifecycleError):
        q.validate_record(redigest(record))


def test_validation_returns_an_independent_copy():
    record = eligible_record()
    validated = q.validate_record(record)
    validated["job_definition"]["queue_enabled"] = True
    assert record["job_definition"]["queue_enabled"] is False


def test_pure_source_has_no_effect_surface():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported_roots.isdisjoint(
        {
            "databricks",
            "http",
            "os",
            "pathlib",
            "pyspark",
            "random",
            "requests",
            "secrets",
            "socket",
            "subprocess",
            "urllib",
        }
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called_names.isdisjoint({"__import__", "compile", "eval", "exec", "open"})
