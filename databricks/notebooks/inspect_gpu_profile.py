# Databricks notebook source
# MAGIC %md
# MAGIC # M68 — inspect the proposed test environment only
# MAGIC Attach this notebook only to an already-running intended test cluster.
# MAGIC Run all once and return the JSON output. Do not start or resize a cluster
# MAGIC for this inspection without separate approval. No widgets need changing.
# MAGIC This notebook does not import Torch, query a GPU, install packages,
# MAGIC restart Python, read research data, write files or run training.

# COMMAND ----------
import importlib.metadata
import json
import os
import platform
import shutil
import sys


def inspect_profile():
    versions = {}
    for name in ("torch", "numpy", "scipy"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "schema_version": "m68-profile-inspection-v1",
        "decision": "INSPECTION_ONLY_GPU_PROFILE_NOT_QUALIFIED",
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": {"system": platform.system(), "architecture": platform.machine()},
        "databricks_runtime_environment": os.environ.get("DATABRICKS_RUNTIME_VERSION"),
        "package_metadata_versions": versions,
        "package_inventory_is_import_or_abi_verification": False,
        "settings": {key: os.environ.get(key) for key in (
            "CUDA_VISIBLE_DEVICES", "CUBLAS_WORKSPACE_CONFIG",
            "NVIDIA_TF32_OVERRIDE", "TORCH_ALLOW_TF32_CUBLAS_OVERRIDE")},
        "nvidia_smi_executable_present": shutil.which("nvidia-smi") is not None,
        "torch_already_in_session": "torch" in sys.modules,
        "not_observed": ["GPU_MODEL", "GPU_MEMORY", "DRIVER_VERSION", "CUDA_BUILD",
                         "DEVICE_AVAILABILITY", "CLUSTER_TOPOLOGY", "BILLING_RATE"],
        "next_action": "Return this JSON plus the intended GPU model/node type if known. "
                       "A separate exact-profile protocol and bounded execution approval are still required.",
        "safety": {"torch_import_requested": False, "gpu_query_requested": False,
                   "subprocess_requested": False, "files_written": False,
                   "network_or_cloud_operation_requested": False,
                   "packages_installed": False, "environment_changed": False,
                   "training_or_sampling_requested": False, "execution_authorized": False},
    }


if __name__ == "__main__":
    print(json.dumps(inspect_profile(), indent=2, sort_keys=True, allow_nan=False))
