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

EXPECTED_HELPER = "f1123e302f1f7731570d0649af45ed7fc881c7d4487beda29578a741d0b75642"
EXPECTED_TEMPLATE = "f8a910f8c3d8c9458b7c68de18adcefc439fa2975f8fa83957ad2af1755ec8cf"

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

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha256(helper) == EXPECTED_HELPER, "Helper bytes differ from reviewed version."
assert sha256(template) == EXPECTED_TEMPLATE, "Template bytes differ from reviewed version."

base = Path("/local_disk0/heterodiff-b08")
base.mkdir(mode=0o700, parents=True, exist_ok=True)
os.chmod(base, 0o700)

stage = base / "preflight-v1"
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

assert copy_exclusive(helper, helper_copy) == EXPECTED_HELPER
assert copy_exclusive(template, template_copy) == EXPECTED_TEMPLATE

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

report = {
    "decision": "DATA_FREE_LOCAL_PREFLIGHT_ONLY",
    "capture_executed": False,
    "study_or_test_data_accessed": False,
    "helper_sha256": sha256(helper_copy),
    "storage_template_sha256": sha256(template_copy),
    "databricks_runtime_environment": os.environ.get("DATABRICKS_RUNTIME_VERSION"),
    "python_version": platform.python_version(),
    "machine": platform.machine(),
    "cpu_count": os.cpu_count(),
    "local_disk0": {
        "total_bytes": fs.f_blocks * fs.f_frsize,
        "available_bytes": fs.f_bavail * fs.f_frsize,
        "available_inodes": fs.f_favail,
    },
    "deterministic_environment": {
        name: os.environ.get(name) for name in env_names
    },
}

print(json.dumps(report, sort_keys=True, indent=2))
