# Databricks notebook source
# MAGIC %md
# MAGIC # Factorized CPU/GPU parity and small performance check
# MAGIC **First run: choose Run all. The default is INSPECT_ONLY.** No package
# MAGIC installation, Python restart, network request, or GPU query is performed.
# MAGIC This notebook uses the pulled source, not the frozen installed release.
# MAGIC
# MAGIC After inspection, use the fields directly below the notebook toolbar:
# MAGIC `mode`: CPU_REFERENCE or CUDA; `device`: cpu or a specific cuda:N;
# MAGIC `iterations`: 1 initially; `maximum_seconds`: 120 initially;
# MAGIC `acknowledgement`: RUN BOUNDED LOCAL TEST. Then choose Run all again.
# MAGIC CUDA must already be available in the attached environment; no cluster
# MAGIC is created or started by this notebook. Do not run CUDA without permission
# MAGIC to use that attached compute. No dataset is needed or read.
# MAGIC CUDA also requires the inherited `CUBLAS_WORKSPACE_CONFIG` setting to be
# MAGIC `:4096:8` or `:16:8` before launching the child. Inspection reports this
# MAGIC prerequisite; it never changes the setting. See the accompanying guide.
# MAGIC
# MAGIC If source detection fails, put the absolute pulled Git-folder path
# MAGIC (the folder containing pyproject.toml and src) in `repo_root` and rerun.
# MAGIC No Docker, ECR, credentials, Git command, or environment rebuild is needed.

# COMMAND ----------

from pathlib import Path
import importlib.metadata
import json
import os
import re
import subprocess
import sys


SCOPE = "SOURCE_ONLY_FACTORIZED_LOCAL_QUALIFICATION_NOT_INSTALLED_RELEASE"
HARNESS_RELATIVE = Path("src/heterodiff/experiments/factorized_device_qualification.py")
MAXIMUM_PARENT_LEVELS = 8
MAXIMUM_OUTPUT_BYTES = 262144
DEFAULTS = {
    "mode": "INSPECT_ONLY", "device": "", "iterations": "1",
    "maximum_seconds": "120", "acknowledgement": "", "repo_root": "",
}


def read_settings(dbutils_object=None):
    """All controls are ordinary string widgets; preserve an existing selection."""
    if dbutils_object is None:
        return dict(DEFAULTS)
    widgets = dbutils_object.widgets
    widgets.dropdown("mode", DEFAULTS["mode"], ["INSPECT_ONLY", "CPU_REFERENCE", "CUDA"],
                     "1. Mode (inspection is read-only)")
    widgets.text("device", "", "2. Device: cpu or explicit cuda:N")
    widgets.text("iterations", "1", "3. Iterations (1-3; each runs all four cases)")
    widgets.text("maximum_seconds", "120", "4. Wall-time limit seconds (5-300)")
    widgets.text("acknowledgement", "", "5. To run: RUN BOUNDED LOCAL TEST")
    widgets.text("repo_root", "", "Optional: absolute source Git-folder path")
    return {name: widgets.get(name).strip() for name in DEFAULTS}


def detect_repo_root(explicit, *, notebook_file=None, cwd=None):
    """Only explicit path or bounded notebook/CWD ancestors; never invokes Git."""
    def valid(path):
        return (path / "pyproject.toml").is_file() and (path / HARNESS_RELATIVE).is_file()
    if explicit:
        supplied = Path(explicit)
        if not supplied.is_absolute():
            return None, "repo_root must be an absolute path, not a repository URL."
        supplied = supplied.resolve()
        return (supplied, None) if valid(supplied) else (
            None, "repo_root must contain pyproject.toml and the new parity/performance source module; pull all new files.")
    candidates = []
    if notebook_file:
        candidate = Path(notebook_file)
        if candidate.is_absolute():
            candidates.append(candidate.resolve().parent)
    candidates.append(Path.cwd().resolve() if cwd is None else Path(cwd).resolve())
    seen = set()
    for start in candidates:
        for candidate in (start, *tuple(start.parents)[:MAXIMUM_PARENT_LEVELS]):
            if candidate in seen:
                continue
            seen.add(candidate)
            if valid(candidate):
                return candidate, None
    return None, "Set repo_root above to the absolute pulled Git folder containing pyproject.toml and src, then Run all."


def package_metadata():
    """Distribution metadata only: this does not import Torch or initialize CUDA."""
    result = {}
    for name in ("torch", "numpy"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def validated_request(settings):
    mode = settings.get("mode", "INSPECT_ONLY")
    if mode not in ("INSPECT_ONLY", "CPU_REFERENCE", "CUDA"):
        raise ValueError("Choose INSPECT_ONLY, CPU_REFERENCE, or CUDA in mode.")
    if mode == "INSPECT_ONLY":
        return {"mode": mode}
    if settings.get("acknowledgement") != "RUN BOUNDED LOCAL TEST":
        raise ValueError("Enter RUN BOUNDED LOCAL TEST in acknowledgement to authorize this bounded local test.")
    device = settings.get("device", "")
    if mode == "CPU_REFERENCE" and device != "cpu":
        raise ValueError("CPU_REFERENCE requires device=cpu; no device fallback is performed.")
    if mode == "CUDA" and re.fullmatch(r"cuda:(0|[1-9][0-9]{0,2})", device) is None:
        raise ValueError("CUDA requires a specific device such as cuda:0 (the visible process-local index).")
    numbers = {}
    for name, lower, upper in (("iterations", 1, 3), ("maximum_seconds", 5, 300)):
        value = settings.get(name, "")
        if type(value) is not str or re.fullmatch(r"[0-9]{1,3}", value) is None or not lower <= int(value) <= upper:
            raise ValueError(f"Set {name} to an integer from {lower} to {upper}.")
        numbers[name] = int(value)
    return {"mode": mode, "device": device, **numbers}


CHILD_CODE = r'''
from pathlib import Path
import contextlib
import json
import sys

request = json.loads(sys.argv[2])
source = (Path(sys.argv[1]) / 'src').resolve()
if not (sys.flags.isolated and sys.dont_write_bytecode):
    raise RuntimeError('ISOLATED_SOURCE_CHILD_REQUIRED')
sys.path.insert(0, str(source))
try:
    with contextlib.redirect_stdout(sys.stderr):
        try:
            import torch
        except ImportError as error:
            raise RuntimeError('PyTorch is unavailable in this notebook environment. Use an already qualified environment with PyTorch; this notebook does not install packages.') from error
        if request['mode'] == 'CUDA' and torch.version.cuda is None:
            raise RuntimeError('This notebook environment has a CPU-only PyTorch build. Use an existing CUDA-enabled PyTorch environment on the intended GPU compute; do not reuse the prior CPU-only bootstrap. No installation or environment change was attempted.')
        from heterodiff.experiments import factorized_device_qualification as harness
        expected = source / 'heterodiff/experiments/factorized_device_qualification.py'
        if Path(harness.__file__).resolve() != expected:
            raise RuntimeError('Expected explicitly selected source harness, not an installed release.')
        result = harness.run_qualification(**request)
    print(json.dumps({'child_completed': True, 'result': result}, sort_keys=True, allow_nan=False))
except Exception as error:
    print(json.dumps({'child_completed': False, 'error_type': type(error).__name__,
                      'error': str(error)[:4096]}, sort_keys=True))
    raise SystemExit(1)
'''


def launch_child(root, request):
    """Supervise one local process; deadline includes imports, not just kernels."""
    process = subprocess.Popen(
        [sys.executable, "-I", "-B", "-c", CHILD_CODE, str(root), json.dumps(request)],
        cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        stdout, stderr = process.communicate(timeout=request["maximum_seconds"])
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            process.communicate(timeout=5)
            stopped = True
        except subprocess.TimeoutExpired:
            stopped = False
        return {"decision": "STOP_LOCAL_WALL_TIME_LIMIT", "child_termination_confirmed": stopped,
                "next_action": "Review the bounded workload before choosing another run; no result is a pass."
                if stopped else "The local child did not confirm termination. Stop this notebook execution and inspect attached compute before another run.",
                "maximum_seconds": request["maximum_seconds"], "termination_grace_seconds": 5}
    except BaseException:
        # A notebook interruption must not deliberately leave its child running.
        process.kill()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            pass  # Do not suppress the original interruption or claim completion.
        raise
    if len(stdout.encode()) > MAXIMUM_OUTPUT_BYTES:
        return {"decision": "STOP_OUTPUT_LIMIT", "child_returncode": process.returncode}
    try:
        output = json.loads(stdout)
    except (ValueError, TypeError):
        return {"decision": "STOP_CHILD_OUTPUT_INVALID", "child_returncode": process.returncode,
                "error_tail": stderr[-4096:]}
    if process.returncode or not output.get("child_completed"):
        return {"decision": "STOP_LOCAL_QUALIFICATION", "child_returncode": process.returncode,
                "error": output.get("error", "Child did not complete."),
                "error_type": output.get("error_type"), "diagnostic_tail": stderr[-4096:]}
    return {"decision": "LOCAL_HARNESS_COMPLETED_REVIEW_RESULT", "result": output["result"],
            "child_returncode": process.returncode}


def run_notebook(settings, *, notebook_file=None, cwd=None, environ=None):
    environment = os.environ if environ is None else environ
    root, root_error = detect_repo_root(settings.get("repo_root", ""), notebook_file=notebook_file, cwd=cwd)
    mask = environment.get("CUDA_VISIBLE_DEVICES")
    cublas = environment.get("CUBLAS_WORKSPACE_CONFIG")
    cublas_ready = cublas in (":4096:8", ":16:8")
    report = {"scope": SCOPE, "repo_root": None if root is None else str(root),
              "python_version": sys.version.split()[0], "package_metadata": package_metadata(),
              "cuda_visible_devices_setting": mask,
              "cublas_workspace_config_setting": cublas,
              "cublas_prelaunch_value_ready": cublas_ready,
              "gpu_queried_by_notebook_inspection": False, "package_install_or_restart_requested": False,
              "network_or_cloud_operation_requested": False, "real_data_requested": False,
              "old_installed_release_replaced": False}
    try:
        request = validated_request(settings)
    except ValueError as error:
        return {**report, "decision": "INPUT_REQUIRED", "next_action": str(error)}
    report["requested_mode"] = request["mode"]
    if root_error:
        return {**report, "decision": "SOURCE_FOLDER_REQUIRED", "next_action": root_error}
    if request["mode"] == "INSPECT_ONLY":
        action = "Inspection only. To run, select CPU_REFERENCE/cpu or CUDA/cuda:N, set limits and enter the acknowledgement."
        if mask is not None and mask.strip() in ("", "-1"):
            action += " CUDA_VISIBLE_DEVICES currently hides GPUs, possibly from the earlier CPU-only setup. It was not changed; use the intended GPU environment before selecting CUDA."
        if not cublas_ready:
            action += " A CUDA run also requires inherited CUBLAS_WORKSPACE_CONFIG=:4096:8 (or :16:8) before child launch. Arrange that prelaunch setting in the intended environment first; this inspection does not change it. CPU_REFERENCE does not require it."
        return {**report, "decision": "INSPECT_ONLY_COMPLETE", "next_action": action}
    if request["mode"] == "CUDA" and mask is not None and mask.strip() in ("", "-1"):
        return {**report, "decision": "CUDA_HIDDEN_BY_EXISTING_ENVIRONMENT",
                "next_action": "CUDA_VISIBLE_DEVICES hides all GPUs. Do not rerun the CPU-only bootstrap. Use the intended existing GPU-enabled environment and review its visibility setting; this notebook does not change it."}
    if request["mode"] == "CUDA" and not cublas_ready:
        return {**report, "decision": "CUDA_PRELAUNCH_CONFIG_REQUIRED",
                "next_action": "The inherited CUBLAS_WORKSPACE_CONFIG must be :4096:8 or :16:8 before launching the CUDA child. Configure this in the intended execution environment before its Python process starts, then rerun INSPECT_ONLY to confirm. No setting, package, or compute was changed."}
    return {**report, "request": request, **launch_child(root, request)}

# COMMAND ----------

if __name__ == "__main__":
    try:
        _settings = read_settings(globals().get("dbutils"))
        _result = run_notebook(_settings, notebook_file=globals().get("__file__"))
    except Exception as _error:
        _result = {"scope": SCOPE, "decision": "STOP_NOTEBOOK_WRAPPER_ERROR",
                   "error_type": type(_error).__name__, "error": str(_error)[:4096],
                   "next_action": "Review this error before running again; no environment repair or retry was attempted."}
    print(json.dumps(_result, indent=2, sort_keys=True, allow_nan=False))
