# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
from pathlib import Path
import hashlib
import json
import os
import platform

EXPECTED_HELPER = "ce16f4c6c797f64b2f101c54ffc0338824e9e7ebf91fca276ca2d50260c8be4d"
EXPECTED_TEMPLATE = "f8a910f8c3d8c9458b7c68de18adcefc439fa2975f8fa83957ad2af1755ec8cf"
EXPECTED_INIT_SCRIPT = "69053bc7e5eb5339ac0e750a47444a99c456196b6bc637a8e78270775685901c"

# Locate the repository without printing its potentially identifying path.
start = Path.cwd().resolve()
repo = next(
    (
        path
        for path in (start, *start.parents)
        if (
            path / "research/diagnostics/b08_databricks_aws_qualification_capture_v1.py"
        ).is_file()
    ),
    None,
)
assert repo is not None, "Run this notebook from inside the cloned repository."

helper = repo / "research/diagnostics/b08_databricks_aws_qualification_capture_v1.py"
template = repo / "research/fixtures/manuscript_v3_b08_databricks_aws_admin_storage_reservation_template_v1.json"
init_script = repo / "databricks/init/set-cuda-empty.sh"

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha256(helper) == EXPECTED_HELPER, "Helper bytes differ from reviewed version."
assert sha256(template) == EXPECTED_TEMPLATE, "Template bytes differ from reviewed version."
assert sha256(init_script) == EXPECTED_INIT_SCRIPT, "Init-script bytes differ from reviewed version."

base = Path("/local_disk0/heterodiff-b08")
base.mkdir(mode=0o700, parents=True, exist_ok=True)
os.chmod(base, 0o700)

stage = base / "successor-preflight-v2"
stage.mkdir(mode=0o700, exist_ok=False)

def copy_exclusive(source, destination):
    raw = source.read_bytes()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(destination, flags, 0o600)
    try:
        offset = 0
        while offset < len(raw):
            offset += os.write(fd, raw[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)
    return hashlib.sha256(raw).hexdigest()

helper_copy = stage / "b08_databricks_aws_qualification_capture_v1.py"
template_copy = stage / "storage-reservation.empty-template.json"
init_script_copy = stage / "set-cuda-empty.sh"

assert copy_exclusive(helper, helper_copy) == EXPECTED_HELPER
assert copy_exclusive(template, template_copy) == EXPECTED_TEMPLATE
assert copy_exclusive(init_script, init_script_copy) == EXPECTED_INIT_SCRIPT

fs = os.statvfs(stage)
env_names = (
    "BLIS_NUM_THREADS",
    "CUDA_VISIBLE_DEVICES",
    "LANG",
    "LC_ALL",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "PYTHONHASHSEED",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONNOUSERSITE",
    "PYTHONSAFEPATH",
    "PYTHONUTF8",
    "TZ",
    "VECLIB_MAXIMUM_THREADS",
)

expected_environment = {
    "BLIS_NUM_THREADS": "1",
    "CUDA_VISIBLE_DEVICES": "",
    "LANG": "C",
    "LC_ALL": "C",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONNOUSERSITE": "1",
    "PYTHONSAFEPATH": "1",
    "PYTHONUTF8": "1",
    "TZ": "UTC",
    "VECLIB_MAXIMUM_THREADS": "1",
}
observed_environment = {name: os.environ.get(name) for name in env_names}
environment_exact = observed_environment == expected_environment
machine = platform.machine()
x86_64 = machine.casefold() in {"x86_64", "amd64"}

report = {
    "decision": (
        "PASS_DATA_FREE_LOCAL_SUCCESSOR_PREFLIGHT_ONLY"
        if environment_exact and x86_64
        else "NO_GO_DATA_FREE_LOCAL_SUCCESSOR_PREFLIGHT"
    ),
    "capture_executed": False,
    "calibration_executed": False,
    "network_or_databricks_rest_accessed": False,
    "spark_accessed": False,
    "study_or_test_data_accessed": False,
    "helper_sha256": sha256(helper_copy),
    "storage_template_sha256": sha256(template_copy),
    "init_script_sha256": sha256(init_script_copy),
    "databricks_runtime_environment": os.environ.get("DATABRICKS_RUNTIME_VERSION"),
    "python_version": platform.python_version(),
    "machine": machine,
    "cpu_count": os.cpu_count(),
    "local_disk0": {
        "total_bytes": fs.f_blocks * fs.f_frsize,
        "available_bytes": fs.f_bavail * fs.f_frsize,
        "available_inodes": fs.f_favail,
    },
    "deterministic_environment": observed_environment,
    "local_checks": {
        "deterministic_environment_exact": environment_exact,
        "machine_x86_64": x86_64,
    },
    "not_proven_by_this_preflight": [
        "ADMIN_AUTHORITY_AND_POLICY_REVISION",
        "AUTOTERMINATION_DISABLED",
        "CUSTOM_CONTAINER_IMMUTABLE_DIGEST",
        "DURABLE_LOG_DELIVERY",
        "FIXED_ON_DEMAND_NO_FALLBACK_TOPOLOGY",
        "PHOTON_DISABLED_EFFECTIVELY",
        "PHYSICAL_STORAGE_RESERVATION",
        "WORKER_ENVIRONMENT_EQUIVALENCE",
    ],
}

print(json.dumps(report, sort_keys=True, indent=2))
