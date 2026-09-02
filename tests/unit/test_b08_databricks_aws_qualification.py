from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from heterodiff.experiments import b08_databricks_aws_qualification as q


ROOT = Path(__file__).resolve().parents[2]
MACHINE = (
    ROOT
    / "research/fixtures/manuscript_v3_b08_databricks_aws_qualification_template_v1.json"
)
SOURCE = ROOT / "src/heterodiff/experiments/b08_databricks_aws_qualification.py"


def eligible_record():
    record = q.build_empty_template()
    record["semantic_disposition"] = q.ELIGIBLE_FOR_DATA_FREE_CALIBRATION_ONLY
    infrastructure = record["infrastructure"]
    infrastructure.update(
        {
            "compute_mode": "CLASSIC_DEDICATED",
            "dedicated_compute": True,
            "worker_count": 0,
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
            "databricks_runtime_version": "16.4.x-scala2.12",
            "databricks_runtime_sha256": "1" * 64,
            "immutable_container_digest": "2" * 64,
            "cluster_policy_sha256": "3" * 64,
            "canonical_secret_free_cluster_config_sha256": "4" * 64,
            "cluster_config_canonicalization_verified": True,
            "cluster_config_contains_secrets": False,
            "complete_runtime_dependency_manifest_sha256": "5" * 64,
            "runtime_dependency_manifest_complete": True,
            "availability_reservation_receipt_sha256": "6" * 64,
            "output_location_binding_sha256": "7" * 64,
            "log_location_binding_sha256": "8" * 64,
            "output_and_log_locations_fixed": True,
        }
    )
    destination = q.DESTINATION_RESERVATION_BYTES + 4_096
    auxiliary = q.AUXILIARY_RESERVATION_BYTES + 8_192
    record["storage_reservation"].update(
        {
            "admin_record_schema": "b08-aws-admin-storage-reservation-v1",
            "admin_record_sha256": "9" * 64,
            "admin_principal_id": "opaque-admin-01",
            "externally_verified": True,
            "verification_method_id": "external-admin-signed-record-v1",
            "destination_reservation_bytes": destination,
            "auxiliary_reservation_bytes": auxiliary,
            "combined_reservation_bytes": destination + auxiliary,
            "available_inodes_after_reservation": 8_192,
            "same_qualified_storage_root_verified": True,
            "destination_and_auxiliary_exclusive_verified": True,
            "destination_and_auxiliary_disjoint_verified": True,
            "non_sparse_allocation_verified": True,
            "enforced_quota_verified": True,
            "reservation_durable_verified": True,
            "no_double_count_verified": True,
            "retained_through_commit_verified": True,
        }
    )
    return q.with_semantic_digest(record)


def test_canonical_hold_template_is_exact_and_zero_delta():
    record = json.loads(MACHINE.read_text(encoding="ascii"))
    assert record == q.build_empty_template()
    assert q.validate_record(record) == record
    assert MACHINE.read_bytes() == q.canonical_json_bytes(record) + b"\n"
    assert record["semantic_disposition"] == q.HOLD_INCOMPLETE
    assert record["project_effects"]["field_count_delta"] == 0
    assert record["project_effects"]["b08_closed"] is False


def test_exact_floors_event_roster_hard_axes_and_determinism():
    assert q.DESTINATION_RESERVATION_BYTES == 1_099_511_627_776
    assert q.AUXILIARY_RESERVATION_BYTES == 34_359_738_368
    assert q.COMBINED_RESERVATION_BYTES == 1_133_871_366_144
    assert q.DESTINATION_RESERVATION_BYTES + q.AUXILIARY_RESERVATION_BYTES == q.COMBINED_RESERVATION_BYTES
    assert q.MINIMUM_AVAILABLE_INODES_AFTER_RESERVATION == 4_096
    assert len(q.F104_EVENT_IDS) == 10
    assert len(q.HARD_AXIS_IDS) == 8
    assert set(q.DETERMINISTIC_ENVIRONMENT_CONTROLS.values()) <= {"", "0", "1", "C", "UTC"}


def test_fully_populated_record_reaches_calibration_eligibility_only():
    record = eligible_record()
    assert q.validate_record(record) == record
    assert record["semantic_disposition"] == q.ELIGIBLE_FOR_DATA_FREE_CALIBRATION_ONLY
    assert record["infrastructure"]["worker_count"] == 0
    assert record["storage_reservation"]["combined_reservation_bytes"] > q.COMBINED_RESERVATION_BYTES
    assert record["calibration_boundary"]["data_free_calibration_performed"] is False
    assert record["authority_boundary"]["study_data_access_authorized"] is False
    assert record["project_effects"]["field_ids_closed"] == []
    assert record["project_effects"]["b08_closed"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["infrastructure"].__setitem__("compute_mode", "SERVERLESS"),
        lambda r: r["infrastructure"].__setitem__("dedicated_compute", False),
        lambda r: r["infrastructure"].__setitem__("autoscaling_enabled", True),
        lambda r: r["infrastructure"].__setitem__("dynamic_allocation_enabled", True),
        lambda r: r["infrastructure"].__setitem__("spot_instances_enabled", True),
        lambda r: r["infrastructure"].__setitem__("on_demand_only", False),
        lambda r: r["infrastructure"].__setitem__("automatic_job_retry_enabled", True),
        lambda r: r["infrastructure"].__setitem__("spark_speculation_enabled", True),
        lambda r: r["infrastructure"].__setitem__("gpu_enabled", True),
        lambda r: r["infrastructure"].__setitem__("photon_enabled", True),
        lambda r: r["infrastructure"].__setitem__("immutable_container_digest", None),
        lambda r: r["infrastructure"].__setitem__("runtime_dependency_manifest_complete", False),
        lambda r: r["storage_reservation"].__setitem__("destination_reservation_bytes", q.DESTINATION_RESERVATION_BYTES - 1),
        lambda r: r["storage_reservation"].__setitem__("available_inodes_after_reservation", 4_095),
        lambda r: r["storage_reservation"].__setitem__("non_sparse_allocation_verified", False),
        lambda r: r["storage_reservation"].__setitem__("enforced_quota_verified", False),
        lambda r: r["calibration_boundary"].__setitem__("data_free_calibration_performed", True),
        lambda r: r["authority_boundary"].__setitem__("study_data_access_authorized", True),
        lambda r: r["project_effects"]["field_ids_closed"].append("F150"),
        lambda r: r.__setitem__("extra", False),
    ],
)
def test_hostile_eligibility_mutations_fail(mutation):
    record = eligible_record()
    mutation(record)
    record = q.with_semantic_digest(record) if set(record) == {
        "schema_version",
        "record_sha256",
        "semantic_disposition",
        "infrastructure",
        "deterministic_policy",
        "storage_reservation",
        "calibration_boundary",
        "authority_boundary",
        "project_effects",
    } else record
    with pytest.raises(q.QualificationError):
        q.validate_record(record)


def test_boolean_integer_aliases_and_component_sum_fail():
    record = eligible_record()
    record["infrastructure"]["worker_count"] = False
    record = q.with_semantic_digest(record)
    with pytest.raises(q.QualificationError):
        q.validate_record(record)

    record = eligible_record()
    record["storage_reservation"]["combined_reservation_bytes"] += 1
    record = q.with_semantic_digest(record)
    with pytest.raises(q.QualificationError):
        q.validate_record(record)


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
        {"os", "pathlib", "socket", "subprocess", "requests", "urllib", "http", "random", "secrets"}
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called_names.isdisjoint({"open", "exec", "eval", "compile", "__import__"})
