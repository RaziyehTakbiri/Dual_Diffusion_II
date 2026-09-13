# Databricks notebook source
# MAGIC %md
# MAGIC # Bounded BASE precision-candidate check
# MAGIC This is a **new, separate check**. The legacy parity notebook stays unchanged.
# MAGIC **Run all first:** the default INSPECT_ONLY reads metadata without importing
# MAGIC Torch, querying CUDA, starting a child process, or changing the environment.
# MAGIC
# MAGIC After the separately authorized check is agreed, use the fields below the
# MAGIC toolbar: mode = CPU_REFERENCE and device = cpu, or mode = CUDA and device =
# MAGIC cuda:0 (an explicit visible GPU index). Enter
# MAGIC **RUN BOUNDED BASE PRECISION CHECK** in acknowledgement, then Run all once.
# MAGIC Put the absolute pulled project folder in repo_root if detection needs help.
# MAGIC The fixed workload is one four-case synthetic pass, not training on real data.
# MAGIC The child has a 120-second deadline, a 2 GiB soft harness memory bound, and
# MAGIC five seconds to confirm termination after a stop. Output is bounded while read.
# MAGIC
# MAGIC No package install, restart, Docker, network request, or cluster creation is
# MAGIC performed. CUDA runs use already attached authorized compute. Missing cuBLAS
# MAGIC configuration is supplied only to the child; conflicting values stop before
# MAGIC launch. CUDA_VISIBLE_DEVICES is never changed. A candidate pass does not turn
# MAGIC the legacy failure into a pass or establish production/whole-pipeline readiness.

# COMMAND ----------

from pathlib import Path
import importlib.metadata
import json
import os
import re
import selectors
import subprocess
import sys
import time


SCOPE = "SOURCE_ONLY_BASE_PRECISION_CANDIDATE_NOT_INSTALLED_RELEASE"
WRAPPER_REVISION = "factorized-base-precision-candidate-wrapper-v1"
HARNESS_RELATIVE = Path("src/heterodiff/experiments/factorized_precision_candidate_qualification.py")
MAXIMUM_SECONDS = 120
TERMINATION_GRACE_SECONDS = 5
MAXIMUM_STDOUT_BYTES = 65536
MAXIMUM_STDERR_BYTES = 16384
READ_CHUNK_BYTES = 4096
ACKNOWLEDGEMENT = "RUN BOUNDED BASE PRECISION CHECK"
DEFAULTS = {"mode": "INSPECT_ONLY", "device": "", "repo_root": "", "acknowledgement": ""}
RESULT_DECISIONS = {
    "PASS_CPU_BASE_PRECISION_CONTROLS_CUDA_NOT_EXECUTED",
    "PASS_SELECTED_CUDA_BASE_PRECISION_CANDIDATE_ONLY",
    "FAIL_BASE_PRECISION_CANDIDATE",
    "STOP_BASE_PRECISION_CHECK_INCOMPLETE",
}


def read_settings(dbutils_object=None):
    if dbutils_object is None:
        return dict(DEFAULTS)
    widgets = dbutils_object.widgets
    widgets.dropdown("mode", "INSPECT_ONLY", ["INSPECT_ONLY", "CPU_REFERENCE", "CUDA"],
                     "1. Mode: inspection is read-only")
    widgets.text("device", "", "2. Device: cpu or explicit cuda:N")
    widgets.text("repo_root", "", "3. Optional: absolute pulled project folder")
    widgets.text("acknowledgement", "", "4. To run: " + ACKNOWLEDGEMENT)
    return {name: widgets.get(name).strip() for name in DEFAULTS}


def detect_repo_root(explicit, *, notebook_file=None, cwd=None):
    def valid(path):
        return (path / "pyproject.toml").is_file() and (path / HARNESS_RELATIVE).is_file()
    if explicit:
        supplied = Path(explicit)
        if not supplied.is_absolute():
            return None, "repo_root must be an absolute local project-folder path."
        supplied = supplied.resolve()
        return (supplied, None) if valid(supplied) else (
            None, "Pull the new files; repo_root must contain pyproject.toml and the new precision-candidate harness.")
    starts = []
    if notebook_file and Path(notebook_file).is_absolute():
        starts.append(Path(notebook_file).resolve().parent)
    starts.append(Path.cwd().resolve() if cwd is None else Path(cwd).resolve())
    seen = set()
    for start in starts:
        for candidate in (start, *tuple(start.parents)[:8]):
            if candidate not in seen and valid(candidate):
                return candidate, None
            seen.add(candidate)
    return None, "Set repo_root to the absolute pulled project folder containing pyproject.toml and src."


def package_metadata():
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
        raise ValueError("Choose INSPECT_ONLY, CPU_REFERENCE, or CUDA.")
    if mode == "INSPECT_ONLY":
        return {"mode": mode}
    if settings.get("acknowledgement") != ACKNOWLEDGEMENT:
        raise ValueError("Enter " + ACKNOWLEDGEMENT + " to run this separate bounded check.")
    device = settings.get("device", "")
    if mode == "CPU_REFERENCE" and device != "cpu":
        raise ValueError("CPU_REFERENCE requires device=cpu; no fallback is performed.")
    if mode == "CUDA" and (type(device) is not str or re.fullmatch(r"cuda:(0|[1-9][0-9]{0,2})", device) is None):
        raise ValueError("CUDA requires an explicit visible process-local device such as cuda:0.")
    return {"mode": mode, "device": device, "maximum_seconds": MAXIMUM_SECONDS}


def prepare_child_environment(request, environment):
    child = dict(environment)
    inherited = child.get("CUBLAS_WORKSPACE_CONFIG")
    inserted = False
    if request["mode"] == "CUDA":
        mask = child.get("CUDA_VISIBLE_DEVICES")
        if mask is not None and mask.strip() in ("", "-1"):
            raise ValueError("CUDA_VISIBLE_DEVICES hides GPUs; it was not changed. Review the intended GPU environment.")
        if inherited is None:
            child["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
            inserted = True
        elif inherited not in (":4096:8", ":16:8"):
            raise ValueError("Explicit CUBLAS_WORKSPACE_CONFIG must be :4096:8 or :16:8; no override or child launch.")
        if any(child.get(name) not in (None, "0") for name in (
                "TORCH_ALLOW_TF32_CUBLAS_OVERRIDE", "NVIDIA_TF32_OVERRIDE")):
            raise ValueError("An inherited TF32 override conflicts with the fixed numerical policy; no override or child launch.")
    return child, {
        "cublas_inherited_value": inherited,
        "cublas_effective_child_value": child.get("CUBLAS_WORKSPACE_CONFIG"),
        "cublas_default_inserted_for_child_only": inserted,
        "cuda_visible_devices_modified": False,
        "parent_or_cluster_environment_modified": False,
    }


CHILD_CODE = r'''
from pathlib import Path
import contextlib
import json
import sys

if not (sys.flags.isolated and sys.dont_write_bytecode):
    raise RuntimeError("ISOLATED_SOURCE_CHILD_REQUIRED")
source = (Path(sys.argv[1]) / "src").resolve()
request = json.loads(sys.argv[2])
sys.path.insert(0, str(source))
try:
    with contextlib.redirect_stdout(sys.stderr):
        from heterodiff.experiments import factorized_precision_candidate_qualification as harness
        expected = source / "heterodiff/experiments/factorized_precision_candidate_qualification.py"
        if Path(harness.__file__).resolve() != expected:
            raise RuntimeError("Selected source harness required, not an installed release.")
        for name, module in tuple(sys.modules.items()):
            filename = getattr(module, "__file__", None)
            if (name == "heterodiff" or name.startswith("heterodiff.")) and filename:
                if not Path(filename).resolve().is_relative_to(source):
                    raise RuntimeError("A project import came from outside the selected source folder.")
        result = harness.run_precision_candidate_check(**request)
    print(json.dumps({"child_completed": True, "result": result},
                     sort_keys=True, separators=(",", ":"), allow_nan=False))
except Exception as error:
    print(json.dumps({"child_completed": False, "error_type": type(error).__name__,
                      "error": str(error)[:2048]}, sort_keys=True, allow_nan=False))
    raise SystemExit(1)
'''


def _stop_and_confirm(process):
    """Stop only the one child; never claim quiescence without process exit."""
    try:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=TERMINATION_GRACE_SECONDS)
        return process.poll() is not None
    except (subprocess.TimeoutExpired, OSError):
        return False


def _collect_bounded(process, *, deadline):
    """Read both binary pipes incrementally; limits apply DURING collection."""
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    limits = {"stdout": MAXIMUM_STDOUT_BYTES, "stderr": MAXIMUM_STDERR_BYTES}
    stop_reason = None
    try:
        with selectors.DefaultSelector() as selector:
            for name in buffers:
                selector.register(getattr(process, name), selectors.EVENT_READ, name)
            while selector.get_map() or process.poll() is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    stop_reason = "STOP_LOCAL_WALL_TIME_LIMIT"
                    break
                if not selector.get_map():
                    try:
                        process.wait(timeout=remaining)
                    except subprocess.TimeoutExpired:
                        stop_reason = "STOP_LOCAL_WALL_TIME_LIMIT"
                    break
                for key, _ in selector.select(timeout=min(remaining, .1)):
                    chunk = os.read(key.fileobj.fileno(), READ_CHUNK_BYTES)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    name = key.data
                    available = limits[name] - len(buffers[name])
                    buffers[name].extend(chunk[:available])
                    if len(chunk) > available:
                        stop_reason = "STOP_OUTPUT_LIMIT"
                        break
                if stop_reason:
                    break
        if time.monotonic() > deadline and stop_reason is None:
            stop_reason = "STOP_LOCAL_WALL_TIME_LIMIT"
        confirmed = _stop_and_confirm(process) if stop_reason else process.poll() is not None
        return {name: bytes(value) for name, value in buffers.items()}, stop_reason, confirmed
    except BaseException:
        _stop_and_confirm(process)
        raise
    finally:
        for name in buffers:
            getattr(process, name).close()


def _error_tail(payload):
    text = payload.decode("utf-8", errors="replace")
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    return text[-2048:]


def launch_child(root, request, *, environ=None):
    child_environment, environment_report = prepare_child_environment(
        request, os.environ if environ is None else environ)
    started = time.monotonic()
    process = subprocess.Popen(
        [sys.executable, "-I", "-B", "-c", CHILD_CODE, str(root), json.dumps(request)],
        cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=child_environment)
    output, stop_reason, confirmed = _collect_bounded(process, deadline=started + MAXIMUM_SECONDS)
    base = {"child_environment": environment_report, "child_returncode": process.returncode,
            "child_termination_confirmed": confirmed, "maximum_seconds": MAXIMUM_SECONDS,
            "termination_grace_seconds": TERMINATION_GRACE_SECONDS,
            "captured_stdout_bytes": len(output["stdout"]), "captured_stderr_bytes": len(output["stderr"]),
            "stdout_limit_bytes": MAXIMUM_STDOUT_BYTES, "stderr_limit_bytes": MAXIMUM_STDERR_BYTES}
    if not confirmed:
        return {**base, "decision": "STOP_CHILD_QUIESCENCE_UNCONFIRMED",
                "next_action": "Stop this notebook and inspect the attached compute before another run; child termination was not confirmed."}
    if stop_reason:
        return {**base, "decision": stop_reason,
                "next_action": "The bounded check stopped. Review this outcome before another run; it is not a pass."}
    try:
        payload = json.loads(output["stdout"])
        if type(payload) is not dict or type(payload.get("child_completed")) is not bool:
            raise ValueError("Invalid child envelope")
    except (ValueError, TypeError, UnicodeDecodeError):
        return {**base, "decision": "STOP_CHILD_OUTPUT_INVALID", "error_tail": _error_tail(output["stderr"])}
    if process.returncode != 0 or not payload["child_completed"]:
        return {**base, "decision": "STOP_BASE_PRECISION_CHECK_INCOMPLETE",
                "error_type": payload.get("error_type"), "error": str(payload.get("error", "Child failed"))[:2048],
                "error_tail": _error_tail(output["stderr"])}
    result = payload.get("result")
    if type(result) is not dict or result.get("decision") not in RESULT_DECISIONS:
        return {**base, "decision": "STOP_CHILD_OUTPUT_INVALID"}
    impossible = ("PASS_SELECTED_CUDA_BASE_PRECISION_CANDIDATE_ONLY" if request["mode"] == "CPU_REFERENCE"
                  else "PASS_CPU_BASE_PRECISION_CONTROLS_CUDA_NOT_EXECUTED")
    if result["decision"] == impossible:
        return {**base, "decision": "STOP_CHILD_OUTPUT_INVALID"}
    # Expose the scientific check's decision at the top, not just child completion.
    return {**base, "decision": result["decision"], "result": result}


def run_notebook(settings, *, notebook_file=None, cwd=None, environ=None):
    environment = os.environ if environ is None else environ
    report = {"scope": SCOPE, "wrapper_revision": WRAPPER_REVISION,
              "package_metadata": package_metadata(), "python_version": sys.version.split()[0],
              "GPU_queried_by_inspection": False, "Torch_imported_by_inspection": False,
              "parent_or_cluster_environment_modified": False, "real_data_requested": False,
              "package_install_or_restart_requested": False, "network_or_cloud_operation_requested": False,
              "old_notebook_or_installed_release_replaced": False,
              "cuda_visible_devices_setting": environment.get("CUDA_VISIBLE_DEVICES"),
              "cublas_workspace_config_setting": environment.get("CUBLAS_WORKSPACE_CONFIG")}
    try:
        request = validated_request(settings)
    except ValueError as error:
        return {**report, "decision": "INPUT_REQUIRED", "next_action": str(error)}
    root, error = detect_repo_root(settings.get("repo_root", ""), notebook_file=notebook_file, cwd=cwd)
    report.update(requested_mode=request["mode"], repo_root=None if root is None else str(root))
    if error:
        return {**report, "decision": "SOURCE_FOLDER_REQUIRED", "next_action": error}
    if request["mode"] == "INSPECT_ONLY":
        return {**report, "decision": "INSPECT_ONLY_COMPLETE",
                "next_action": "Inspection only. After authorization select CPU_REFERENCE/cpu or CUDA/cuda:N, enter "
                    + ACKNOWLEDGEMENT + ", and Run all once. The fixed four-case pass has a 120-second child deadline; no iteration setting."}
    try:
        return {**report, "request": request, **launch_child(root, request, environ=environment)}
    except ValueError as error:
        return {**report, "decision": "PRELAUNCH_INPUT_REQUIRED", "next_action": str(error)}


# COMMAND ----------

if __name__ == "__main__":
    try:
        _report = run_notebook(read_settings(globals().get("dbutils")),
                               notebook_file=globals().get("__file__"))
    except Exception as _error:
        _report = {"scope": SCOPE, "decision": "STOP_NOTEBOOK_WRAPPER_ERROR",
                   "error_type": type(_error).__name__, "error": str(_error)[:2048]}
    print(json.dumps(_report, sort_keys=True, separators=(",", ":"), allow_nan=False))

