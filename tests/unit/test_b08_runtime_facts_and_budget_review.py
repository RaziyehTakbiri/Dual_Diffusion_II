import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("runtime_facts_review", ROOT / "databricks/notebooks/b08_runtime_facts_and_budget_review.py")
facts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(facts)


def fake_spark():
    values = {
        facts.CONFIG_KEYS["node_type_id"]: "m6i.8xlarge",
        facts.CONFIG_KEYS["driver_node_type_id"]: "m6i.8xlarge",
        facts.CONFIG_KEYS["data_security_mode"]: "DEDICATED",
        facts.CONFIG_KEYS["cluster_profile"]: "singleNode",
    }
    status = SimpleNamespace(size=lambda: 1)
    sc = SimpleNamespace(getExecutorMemoryStatus=lambda: status)
    context = SimpleNamespace(master="local[*, 4]", _jsc=SimpleNamespace(sc=lambda: sc))
    return SimpleNamespace(conf=SimpleNamespace(get=lambda k, default: values.get(k, default)), version="4.0.0", sparkContext=context)


def test_explicit_spark_session_populates_separate_module():
    result, missing = facts.collect_spark_facts(fake_spark())
    assert result["node_type_id"] == "m6i.8xlarge"
    assert result["spark_version"] == "4.0.0"
    assert result["executor_process_count_including_driver"] == 1
    assert result["spark_master_kind"] == "local"
    assert not missing


def test_metadata_absence_does_not_trigger_installs_or_fallback():
    result, missing = facts.collect_spark_facts(None)
    assert all(v is None for v in result.values())
    assert missing == ["live_spark_session"]


def test_export_only_retains_allowlisted_nonprivate_fields():
    value = {"node_type_id": "m6i.8xlarge", "is_single_node": True, "num_workers": 0,
             "spark_version": "17.3.x-scala2.13", "single_user_name": "private@example.org",
             "cluster_id": "private-id", "secret": "private-secret", "custom_tags": {"owner": "private"}}
    result = facts.sanitize_cluster_export(json.dumps(value))
    assert set(result) == {"node_type_id", "is_single_node", "num_workers", "spark_version"}
    assert "private" not in json.dumps(result)


@pytest.mark.parametrize("raw", ['[]', '{"num_workers":true}', '{"is_single_node":"true"}',
                                  '{"is_single_node":true,"num_workers":2}',
                                  '{"num_workers":0,"num_workers":1}',
                                  '{"node_type_id":"host/path?token=secret"}'])
def test_invalid_export_is_rejected(raw):
    with pytest.raises(ValueError):
        facts.sanitize_cluster_export(raw)


def test_remote_master_hostname_is_not_disclosed():
    spark = fake_spark()
    spark.sparkContext.master = "spark://private-host:7077"
    result, _ = facts.collect_spark_facts(spark)
    assert result["spark_master_kind"] == "standalone"
    assert "private-host" not in json.dumps(result)


def test_real_frozen_budget_conflict_is_reproduced_without_mutation():
    paths = [ROOT / facts.BUDGET_PATH, ROOT / facts.TRAINING_PATH]
    before = [p.read_bytes() for p in paths]
    result = facts.audit_frozen_validation_budget(ROOT)
    assert result["decision"] == "PREOUTCOME_BUDGET_RECONCILIATION_REQUIRED"
    assert len(result["rows"]) == 4
    for row in result["rows"]:
        assert row["checkpoint_count"] == 16
        assert row["validation_draws_per_seed"] == 131072
        assert row["validation_only_reverse_step_events"] == 8589934592
        assert row["final_training_ode_event_ceiling"] == 4194304
        assert row["validation_only_reverse_step_shortfall"] == 8585740288
        assert row["final_training_metric_draw_event_ceiling"] == 0
        assert row["conflict"] is True
    assert [p.read_bytes() for p in paths] == before


def test_report_never_merges_prior_notebook_identity_or_closes_fields(monkeypatch):
    monkeypatch.setattr(facts.shutil, "which", lambda name: None)
    report = facts.build_report(ROOT, fake_spark(), '{"node_type_id":"m6i.4xlarge"}')
    assert report["observed_vs_export_conflicts"] == ["node_type_id"]
    assert report["current_notebook_runtime"]["same_installed_environment_as_previous_success_claimed"] is False
    assert report["safety"]["field_or_blocker_closed"] is False
    assert not report["safety"]["files_written"]
    assert not report["safety"]["spark_data_job_requested"]
    assert not report["safety"]["training_or_inference"]
    assert not report["safety"]["local_gpu_metadata_query_attempted"]
    assert not report["safety"]["gpu_computation_requested"]
    assert not report["safety"]["cuda_visible_devices_environment_changed"]
    assert report["budget_review"]["existing_cpu_reference_policy_accelerator_hours_per_run"] == 0
    assert report["budget_review"]["gpu_successor_accelerator_hours_per_run"] is None
    assert "proposed_cpu_policy_accelerator_hours_per_run" not in report["budget_review"]


def _gpu_query_stub(monkeypatch, payload=b"", returncode=0, error=None):
    monkeypatch.setattr(facts.shutil, "which", lambda name: "/usr/bin/nvidia-smi")
    def query(argv, timeout, bound):
        assert argv == ["/usr/bin/nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"]
        assert timeout == 5
        assert bound == 16384
        if error is not None:
            raise error
        return returncode, payload
    monkeypatch.setattr(facts, "_bounded_metadata_query", query)


def test_missing_gpu_tool_is_not_zero_device_proof(monkeypatch):
    monkeypatch.setattr(facts.shutil, "which", lambda name: None)
    result = facts.collect_local_gpu_facts()
    assert result["status"] == "UNAVAILABLE_TOOL_NOT_FOUND"
    assert result["device_count"] is None
    assert not result["query_attempted"]


def test_multiple_gpus_report_local_per_device_memory_only(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")
    before = dict(os.environ)
    _gpu_query_stub(monkeypatch, b"NVIDIA A100-SXM4-80GB, 81920, 570.86.15\n" * 8)
    result = facts.collect_local_gpu_facts()
    assert result["status"] == "OBSERVED"
    assert result["device_count"] == 8
    assert all(set(row) == {"name", "memory_total_mib", "driver_version"} for row in result["devices"])
    assert result["devices"][0]["memory_total_mib"] == 81920
    assert result["scope"] == "LOCAL_PROCESS_VISIBLE_DEVICES_NOT_WHOLE_CLUSTER_ALLOCATION"
    assert not result["gpu_training_or_spend_authorized"]
    assert not result["reported_host_ram_is_gpu_memory"]
    assert not result["torch_imported_or_gpu_computation_requested"]
    assert dict(os.environ) == before


@pytest.mark.parametrize("payload", [b"GPU, 81920\n", b"GPU, N/A, 570.86\n", b"GPU, -1, 570.86\n", b"GPU, 0, 570.86\n", b"GPU, 81920, private@host\n", b"GPU\x1b, 81920, 570.86\n", b"\xff", b"\"GPU, 81920, 570.86\n"])
def test_malformed_gpu_output_is_not_retained(monkeypatch, payload):
    _gpu_query_stub(monkeypatch, payload)
    result = facts.collect_local_gpu_facts()
    assert result["status"] == "MALFORMED_OUTPUT"
    assert result["device_count"] is None
    assert result["devices"] == []


@pytest.mark.parametrize("error,status", [(subprocess.TimeoutExpired("private-command", 5), "QUERY_TIMED_OUT"), (OSError("private-runtime-path"), "QUERY_UNAVAILABLE"), (ValueError("GPU_QUERY_OUTPUT_LIMIT_EXCEEDED"), "OUTPUT_LIMIT_EXCEEDED")])
def test_gpu_query_errors_are_graceful_and_sanitized(monkeypatch, error, status):
    _gpu_query_stub(monkeypatch, error=error)
    result = facts.collect_local_gpu_facts()
    assert result["status"] == status
    assert result["device_count"] is None
    assert "private" not in json.dumps(result)


def test_gpu_nonzero_exit_discards_output(monkeypatch):
    _gpu_query_stub(monkeypatch, b"private diagnostic", returncode=1)
    result = facts.collect_local_gpu_facts()
    assert result["status"] == "QUERY_FAILED"
    assert "private" not in json.dumps(result)


@pytest.mark.parametrize("payload,status", [(b"x" * 16385, "OUTPUT_LIMIT_EXCEEDED"), (b"GPU, 1, 570.86\n" * 65, "DEVICE_LIMIT_EXCEEDED")])
def test_gpu_output_acceptance_bounds(monkeypatch, payload, status):
    _gpu_query_stub(monkeypatch, payload)
    assert facts.collect_local_gpu_facts()["status"] == status


def test_zero_rows_is_only_no_devices_reported(monkeypatch):
    _gpu_query_stub(monkeypatch)
    result = facts.collect_local_gpu_facts()
    assert result["status"] == "NO_DEVICES_REPORTED"
    assert result["device_count"] == 0


def test_bounded_reader_captures_without_shell_or_stderr():
    result = facts._bounded_metadata_query([sys.executable, "-c", "import sys; print('GPU, 12, 570.86'); print('private', file=sys.stderr)"], 5, 16384)
    assert result == (0, b"GPU, 12, 570.86\n")


def test_bounded_reader_stops_oversized_output():
    with pytest.raises(ValueError, match="GPU_QUERY_OUTPUT_LIMIT_EXCEEDED"):
        facts._bounded_metadata_query([sys.executable, "-c", "print('x'*20000)"], 5, 16384)


def test_bounded_reader_times_out_and_reaps_child():
    with pytest.raises(subprocess.TimeoutExpired):
        facts._bounded_metadata_query([sys.executable, "-c", "import time; time.sleep(3)"], 0.1, 16384)
