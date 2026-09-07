# Databricks notebook source
# MAGIC %md
# MAGIC # Runtime facts and prospective budget review
# MAGIC Attach the existing cluster and choose **Run all**. No installation,
# MAGIC restart, model execution, data read, or configuration change is performed.
# MAGIC The report collects only an allowlist of cluster facts and checks the
# MAGIC arithmetic of the existing frozen plans. It does **not** approve training.
# MAGIC
# MAGIC The optional `CLUSTER_JSON` box accepts an exported cluster configuration
# MAGIC if automatic node/topology fields are unavailable. Only six configuration
# MAGIC fields are retained; names, IDs, emails, credentials and tags are omitted.
# MAGIC Do not change the previously successful installation notebook.
# MAGIC A bounded optional local `nvidia-smi` query reads GPU model, per-device
# MAGIC memory and driver version only. It performs no GPU computation and does
# MAGIC not change CPU-reference settings or approve GPU training/spending.

# COMMAND ----------

from datetime import datetime, timezone
import csv
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import selectors
import shutil
import subprocess
import time


BUDGET_PATH = "research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json"
TRAINING_PATH = "research/fixtures/manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.json"
CONFIG_KEYS = {
    "node_type_id": "spark.databricks.clusterUsageTags.clusterNodeType",
    "driver_node_type_id": "spark.databricks.clusterUsageTags.driverNodeType",
    "data_security_mode": "spark.databricks.clusterUsageTags.dataSecurityMode",
    "cluster_profile": "spark.databricks.cluster.profile",
}
GPU_QUERY_ARGUMENTS = (
    "--query-gpu=name,memory.total,driver_version",
    "--format=csv,noheader,nounits",
)
GPU_QUERY_TIMEOUT_SECONDS = 5
GPU_QUERY_MAXIMUM_BYTES = 16384
GPU_QUERY_MAXIMUM_DEVICES = 64


def _bounded_metadata_query(argv, timeout_seconds, maximum_bytes):
    """Read bounded local command output; discard stderr and never use a shell."""
    deadline = time.monotonic() + timeout_seconds
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               shell=False)
    payload = bytearray()
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise subprocess.TimeoutExpired(argv, timeout_seconds)
                chunk = os.read(process.stdout.fileno(), min(4096, maximum_bytes + 1 - len(payload)))
                if not chunk:
                    break
                payload.extend(chunk)
                if len(payload) > maximum_bytes:
                    raise ValueError("GPU_QUERY_OUTPUT_LIMIT_EXCEEDED")
        returncode = process.wait(timeout=max(0, deadline - time.monotonic()))
        return returncode, bytes(payload)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=1)
        process.stdout.close()


def collect_local_gpu_facts():
    """Only local nvidia-smi visibility, not allocation or CUDA qualification."""
    result = {
        "status": "UNAVAILABLE_TOOL_NOT_FOUND", "query_attempted": False,
        "observation_source": "LOCAL_NVIDIA_SMI_METADATA_QUERY",
        "scope": "LOCAL_PROCESS_VISIBLE_DEVICES_NOT_WHOLE_CLUSTER_ALLOCATION",
        "devices": [], "device_count": None,
        "query_timeout_seconds": GPU_QUERY_TIMEOUT_SECONDS,
        "maximum_output_bytes": GPU_QUERY_MAXIMUM_BYTES,
        "maximum_device_rows": GPU_QUERY_MAXIMUM_DEVICES,
        "cuda_visible_devices_environment_changed": False,
        "cuda_visibility_note": "CUDA_VISIBLE_DEVICES can mask Torch visibility; this query does not establish Torch accessibility or alter that setting.",
        "torch_imported_or_gpu_computation_requested": False,
        "gpu_training_or_spend_authorized": False,
        "reported_host_ram_is_gpu_memory": False,
    }
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return result
    result["query_attempted"] = True
    try:
        returncode, payload = _bounded_metadata_query(
            [executable, *GPU_QUERY_ARGUMENTS], GPU_QUERY_TIMEOUT_SECONDS,
            GPU_QUERY_MAXIMUM_BYTES,
        )
        if returncode != 0:
            result["status"] = "QUERY_FAILED"
            return result
        if len(payload) > GPU_QUERY_MAXIMUM_BYTES:
            raise ValueError("GPU_QUERY_OUTPUT_LIMIT_EXCEEDED")
        rows = list(csv.reader(payload.decode("ascii").splitlines(), strict=True))
        if len(rows) > GPU_QUERY_MAXIMUM_DEVICES:
            raise ValueError("GPU_QUERY_DEVICE_LIMIT_EXCEEDED")
        devices = []
        for row in rows:
            if len(row) != 3:
                raise ValueError("GPU_QUERY_MALFORMED_OUTPUT")
            name, memory, driver = (part.strip() for part in row)
            if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _./()+-]{0,127}", name)
                    or not re.fullmatch(r"[0-9]{1,8}", memory)
                    or not 0 < int(memory) <= 16777216
                    or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,4}", driver)
                    or len(driver) > 64):
                raise ValueError("GPU_QUERY_MALFORMED_OUTPUT")
            devices.append({"name": name, "memory_total_mib": int(memory),
                            "driver_version": driver})
        result.update(status="OBSERVED" if devices else "NO_DEVICES_REPORTED",
                      devices=devices, device_count=len(devices))
    except subprocess.TimeoutExpired:
        result["status"] = "QUERY_TIMED_OUT"
    except OSError:
        result["status"] = "QUERY_UNAVAILABLE"
    except (ValueError, UnicodeError, csv.Error) as error:
        result["status"] = (
            "OUTPUT_LIMIT_EXCEEDED" if str(error) == "GPU_QUERY_OUTPUT_LIMIT_EXCEEDED" else
            "DEVICE_LIMIT_EXCEEDED" if str(error) == "GPU_QUERY_DEVICE_LIMIT_EXCEEDED" else
            "MALFORMED_OUTPUT"
        )
    return result


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _token(value):
    if value is None:
        return None
    text = str(value)
    return text if re.fullmatch(r"[A-Za-z0-9_.+:-]{1,128}", text) else None


def sanitize_cluster_export(raw):
    """Retain configuration, never identity, credentials, tags or free text."""
    if not raw.strip():
        return {}
    if len(raw.encode("utf-8")) > 131072:
        raise ValueError("CLUSTER_JSON exceeds 128 KiB")
    value = json.loads(raw, object_pairs_hook=_json_object)
    if type(value) is not dict:
        raise ValueError("CLUSTER_JSON must be an object")
    result = {}
    for name in ("node_type_id", "driver_node_type_id", "spark_version", "data_security_mode"):
        if name in value:
            if type(value[name]) is not str or _token(value[name]) is None:
                raise ValueError("Invalid configuration field: " + name)
            result[name] = value[name]
    if "num_workers" in value:
        count = value["num_workers"]
        if type(count) is not int or not 0 <= count <= 10000:
            raise ValueError("num_workers must be a nonnegative integer")
        result["num_workers"] = count
    if "is_single_node" in value:
        if type(value["is_single_node"]) is not bool:
            raise ValueError("is_single_node must be boolean")
        result["is_single_node"] = value["is_single_node"]
    if result.get("is_single_node") and result.get("num_workers", 0) != 0:
        raise ValueError("Single-node export conflicts with num_workers")
    return result


def collect_spark_facts(spark_session):
    """Pass the live session explicitly; a loaded helper has no implicit spark."""
    facts = {key: None for key in CONFIG_KEYS}
    facts.update(spark_version=None, spark_master_kind=None, executor_process_count_including_driver=None)
    unavailable = []
    if spark_session is None:
        return facts, ["live_spark_session"]
    for name, key in CONFIG_KEYS.items():
        try:
            facts[name] = _token(spark_session.conf.get(key, None))
        except Exception:
            unavailable.append(name)
    try:
        facts["spark_version"] = _token(spark_session.version)
    except Exception:
        unavailable.append("spark_version")
    try:
        # Do not expose hostnames in spark:// or other remote master URLs.
        master = str(spark_session.sparkContext.master)
        facts["spark_master_kind"] = (
            "local" if master == "local" or master.startswith("local[") else
            "yarn" if master == "yarn" else
            "standalone" if master.startswith("spark://") else
            "kubernetes" if master.startswith("k8s://") else "other"
        )
    except Exception:
        unavailable.append("spark_master_kind")
    try:
        count = int(spark_session.sparkContext._jsc.sc().getExecutorMemoryStatus().size())
        if count >= 0:
            facts["executor_process_count_including_driver"] = count
    except Exception:
        unavailable.append("executor_process_count_including_driver")
    return facts, sorted(set(unavailable + [k for k, v in facts.items() if v is None]))


def audit_frozen_validation_budget(root):
    """Arithmetic only: no benchmark, fitted weight, model or data operation."""
    payloads = {name: (root / name).read_bytes() for name in (BUDGET_PATH, TRAINING_PATH)}
    budget = json.loads(payloads[BUDGET_PATH])
    training = json.loads(payloads[TRAINING_PATH])
    fields = {row["field_id"]: row["value"] for row in training["plan_semantics"]["field_closures"]}
    budget_fields = {row["field_id"]: row["value"] for row in budget["field_closures"]}
    validation = fields["F144"]
    steps = fields["F143"]
    cadence = validation["checkpoint_cadence"]["every_completed_optimizer_updates"]
    if any(type(v) is not int or v <= 0 for v in (steps, cadence, validation["f134_validation_group_count"], validation["draw_count_per_group"])):
        raise ValueError("Invalid frozen workload integers")
    if not validation["checkpoint_cadence"]["terminal_f143_bound_included"]:
        raise ValueError("Unsupported checkpoint schedule; review its semantics")
    checkpoints = (steps + cadence - 1) // cadence
    rows = []
    for method, field in zip(budget["registry"]["primary_pair"], ("F066", "F072")):
        for domain in budget["registry"]["domain_ids"]:
            envelope = budget_fields[field][domain]
            if envelope["scope"] != "PER_METHOD_PER_DOMAIN_COMPLETE_256_SEED_ROSTER":
                raise ValueError("Budget scope changed; review seed interpretation")
            reverse_steps = method["config"]["domain_configs"][domain]["base"]["reverse_steps"]
            if type(reverse_steps) is not int or reverse_steps <= 0:
                raise ValueError("Invalid frozen reverse-step count")
            draws_per_seed = checkpoints * validation["f134_validation_group_count"] * validation["draw_count_per_group"]
            required_steps = draws_per_seed * reverse_steps * 256
            caps = envelope["phase_event_count_ceilings"]["FINAL_TRAINING"]
            ode_cap = caps["ODE_OR_SDE_STEP"]
            rows.append({
                "method_id": method["method_id"], "domain_id": domain, "budget_field": field,
                "checkpoint_count": checkpoints, "validation_draws_per_seed": draws_per_seed,
                "reverse_steps_per_draw": reverse_steps, "seed_roster_count": 256,
                "validation_only_reverse_step_events": required_steps,
                "final_training_ode_event_ceiling": ode_cap,
                "validation_only_reverse_step_shortfall": max(0, required_steps - ode_cap),
                "final_training_metric_draw_event_ceiling": caps["METRIC_DRAW_EVALUATION"],
                "conflict": required_steps > ode_cap or caps["METRIC_DRAW_EVALUATION"] == 0,
            })
    if len(rows) != 4:
        raise ValueError("Expected the two primary methods across two domains")
    return {
        "decision": "PREOUTCOME_BUDGET_RECONCILIATION_REQUIRED" if any(r["conflict"] for r in rows) else "NO_PRIMARY_VALIDATION_CONFLICT_FOUND",
        "scope": "PRIMARY_PAIR_CHECKPOINT_VALIDATION_ONLY_NOT_TOTAL_RUN_COST",
        "source_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in payloads.items()},
        "rows": rows,
        "policies_or_budgets_changed": False,
        "existing_cpu_reference_policy_accelerator_hours_per_run": 0,
        "cpu_reference_basis": "HISTORICAL_F153_AND_F141_CPU_REFERENCE_ONLY_NOT_GPU_SUCCESSOR_BUDGET",
        "gpu_successor_accelerator_hours_per_run": None,
        "gpu_successor_training_or_spend_authorized": False,
        "scalar_weights_time_memory_storage_or_spend_invented": False,
    }


def _linux_fact(path, key):
    try:
        for line in Path(path).read_text().splitlines():
            if line.split(":", 1)[0].strip() == key:
                return line.split(":", 1)[1].strip()[:256]
    except OSError:
        pass
    return None


def build_report(root, spark_session, cluster_json=""):
    facts, unavailable = collect_spark_facts(spark_session)
    gpu_facts = collect_local_gpu_facts()
    exported = sanitize_cluster_export(cluster_json)
    conflicts = [name for name in ("node_type_id", "driver_node_type_id", "data_security_mode")
                 if facts[name] is not None and name in exported and facts[name] != exported[name]]
    versions = {}
    for name in ("heterodiff", "numpy", "scipy", "torch", "threadpoolctl", "pytest"):
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    disk = shutil.disk_usage("/tmp")
    report = {
        "schema_version": "heterodiff-runtime-facts-and-budget-review-v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "FACTS_COLLECTED_REVIEW_REQUIRED",
        "observed_cluster_facts": facts,
        "local_gpu_metadata": gpu_facts,
        "unavailable_observed_fields": unavailable,
        "operator_supplied_cluster_export": exported,
        "observed_vs_export_conflicts": conflicts,
        "current_notebook_runtime": {
            "databricks_runtime": os.environ.get("DATABRICKS_RUNTIME_VERSION"),
            "python": platform.python_version(), "architecture": platform.machine(),
            "cpu_count": os.cpu_count(), "cpu_model": _linux_fact("/proc/cpuinfo", "model name"),
            "memory_total": _linux_fact("/proc/meminfo", "MemTotal"),
            "package_metadata_versions": versions,
            "same_installed_environment_as_previous_success_claimed": False,
            "note": "Packages are notebook-scoped. This metadata-only report does not replace the accepted installation/import/test receipt.",
        },
        "scratch_observation": {"path": "/tmp", "free_bytes": disk.free, "total_bytes": disk.total, "capacity_assurance": False},
        "budget_review": audit_frozen_validation_budget(root),
        "remaining_inputs": ["actual data locations and applicable approvals", "prospective budget reconciliation decision", "total compute spend/runtime limit", "approved durable storage allocation"],
        "safety": {"files_written": False, "package_install_or_restart": False,
                   "training_or_inference": False, "study_or_test_data_read": False,
                   "spark_metadata_requested": spark_session is not None,
                   "spark_data_job_requested": False, "databricks_rest_requested": False,
                   "local_gpu_metadata_query_attempted": gpu_facts["query_attempted"],
                   "gpu_computation_requested": False,
                   "cuda_visible_devices_environment_changed": False,
                   "field_or_blocker_closed": False},
    }
    report["record_sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return report


def notebook_main(spark_session, dbutils_object=None):
    root = next((p for p in (Path.cwd(), *Path.cwd().parents) if (p / BUDGET_PATH).is_file()), None)
    if root is None:
        raise ValueError("Open this notebook inside the pulled project Git folder")
    cluster_json = ""
    if dbutils_object is not None:
        dbutils_object.widgets.text("CLUSTER_JSON", "", "Optional cluster JSON (not required for first run)")
        cluster_json = dbutils_object.widgets.get("CLUSTER_JSON")
    return build_report(root, spark_session, cluster_json)

# COMMAND ----------

if __name__ == "__main__":
    runtime_facts_and_budget_report = notebook_main(globals().get("spark"), globals().get("dbutils"))
    print(json.dumps(runtime_facts_and_budget_report, indent=2))
