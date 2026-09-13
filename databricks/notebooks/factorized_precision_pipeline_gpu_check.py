# Databricks notebook source
# MAGIC %md
# MAGIC # Bounded integrated precision-pipeline check
# MAGIC This is a **new, separate check**. The legacy parity notebook stays unchanged.
# MAGIC **Run all first:** the default INSPECT_ONLY reads metadata without importing
# MAGIC Torch, querying CUDA, starting a child process, or changing the environment.
# MAGIC
# MAGIC After the separately authorized check is agreed, use the fields below the
# MAGIC toolbar: mode = CPU_REFERENCE and device = cpu, or mode = CUDA and device =
# MAGIC cuda:0 (an explicit visible GPU index). Enter
# MAGIC **RUN BOUNDED PRECISION PIPELINE CHECK** in acknowledgement, then Run all once.
# MAGIC Put the absolute pulled project folder in repo_root if detection needs help.
# MAGIC The fixed workload covers both domains and conditional methods, learned-BASE
# MAGIC populations, conditional updates and tiny retained/overflow sampling paths.
# MAGIC Common-input CPU/device comparisons are separate from device-specific path
# MAGIC replay: equal seeds do not couple different population law identities.
# MAGIC This is one four-case synthetic check, not training on real data.
# MAGIC Exactly 36 small optimizer updates and 48 tiny paths; no iteration widget.
# MAGIC The child has a 300-second deadline, a 2 GiB soft harness memory bound, and
# MAGIC five seconds to confirm termination after a stop. Output is bounded while read.
# MAGIC
# MAGIC No package install, restart, Docker, network request, or cluster creation is
# MAGIC performed. CUDA runs use already attached authorized compute. Missing cuBLAS
# MAGIC configuration is supplied only to the child; conflicting values stop before
# MAGIC launch. CUDA_VISIBLE_DEVICES is never changed. A candidate pass does not turn
# MAGIC the legacy failure into a pass or establish production readiness.

# COMMAND ----------

from pathlib import Path
import importlib.metadata
import json
import math
import os
import re
import selectors
import subprocess
import sys
import time


SCOPE = "SOURCE_ONLY_PRECISION_PIPELINE_CHECK_NOT_INSTALLED_RELEASE"
WRAPPER_REVISION = "factorized-precision-pipeline-gpu-wrapper-v1"
HARNESS_RELATIVE = Path("src/heterodiff/experiments/factorized_precision_pipeline_device_check.py")
MAXIMUM_SECONDS = 300
TERMINATION_GRACE_SECONDS = 5
MAXIMUM_STDOUT_BYTES = 65536
MAXIMUM_STDERR_BYTES = 16384
READ_CHUNK_BYTES = 4096
ACKNOWLEDGEMENT = "RUN BOUNDED PRECISION PIPELINE CHECK"
DEFAULTS = {"mode": "INSPECT_ONLY", "device": "", "repo_root": "", "acknowledgement": ""}
RESULT_DECISIONS = {
    "PASS_CPU_PRECISION_PIPELINE_CONTROLS_CUDA_NOT_EXECUTED",
    "PASS_SELECTED_CUDA_PRECISION_PIPELINE_CANDIDATE_ONLY",
    "FAIL_PRECISION_PIPELINE_CANDIDATE",
    "STOP_PRECISION_PIPELINE_CHECK_INCOMPLETE",
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
            None, "Pull the new files; repo_root must contain pyproject.toml and the new integrated precision-pipeline harness.")
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
        from heterodiff.experiments import factorized_precision_pipeline_device_check as harness
        expected = source / "heterodiff/experiments/factorized_precision_pipeline_device_check.py"
        if Path(harness.__file__).resolve() != expected:
            raise RuntimeError("Selected source harness required, not an installed release.")
        for name, module in tuple(sys.modules.items()):
            filename = getattr(module, "__file__", None)
            if (name == "heterodiff" or name.startswith("heterodiff.")) and filename:
                if not Path(filename).resolve().is_relative_to(source):
                    raise RuntimeError("A project import came from outside the selected source folder.")
        result = harness.run_precision_pipeline_check(**request)
        for name, module in tuple(sys.modules.items()):
            filename = getattr(module, "__file__", None)
            if (name == "heterodiff" or name.startswith("heterodiff.")) and filename:
                if not Path(filename).resolve().is_relative_to(source):
                    raise RuntimeError("A late project import came from outside the selected source folder.")
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


def _strict_json(payload):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON field')
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError('Nonfinite JSON value')
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('Nonfinite JSON value')
        return number
    return json.loads(payload, object_pairs_hook=unique_object,
                      parse_constant=invalid_constant, parse_float=finite_float)


EXPECTED_CASES = tuple((domain, method) for domain in ('R3-PHYS', 'R4-RETAIL') for method in
    ('association-aware-guide-plus-residual', 'unified-direct-conditioner'))
GATING_COMPARISONS = ('common_base_cpu_vs_target', 'common_conditional_cpu_vs_target',
                     'shared_weight_physical_cpu_vs_target', 'candidate_target_exact_replay')
EXPECTED_TOLERANCES = {
    'forward': [2e-6, 2e-5], 'coordinate_gradient': [2e-5, 2e-4],
    'coordinate_hessian': [1e-4, 1e-3], 'parameter_gradient': [2e-5, 2e-4],
    'loss': [2e-6, 2e-5], 'updated_parameter': [2e-6, 2e-5],
    'optimizer_moment': [2e-6, 2e-4], 'physical': [2e-5, 2e-4],
}
EXPECTED_CATEGORIES = {
    'common_base_cpu_vs_target': {'exact', 'loss', 'parameter_gradient', 'updated_parameter', 'optimizer_moment'},
    'common_conditional_cpu_vs_target': {'exact', 'forward', 'loss', 'parameter_gradient', 'updated_parameter', 'optimizer_moment'},
    'shared_weight_physical_cpu_vs_target': {'physical'},
    'candidate_target_exact_replay': {'exact', 'forward', 'loss', 'parameter_gradient', 'updated_parameter', 'optimizer_moment', 'physical'},
    'legacy_shared_weight_physical_drift': {'physical'},
}


def _validate_result(result, request):
    """Check the completion contract without importing Torch in the parent.

    This rejects incomplete/misrouted output, not an authentication mechanism
    for a malicious source tree or a reconstruction of unreported tensors.
    """
    def require(ok):
        if not ok:
            raise ValueError('Invalid integrated-pipeline result contract')
    require(type(result) is dict and result.get('decision') in RESULT_DECISIONS)
    require(result.get('schema_version') == 'factorized-precision-pipeline-device-check-v1')
    require(result.get('mode') == request['mode'] and result.get('device') == request['device'])
    require(result.get('precision_policy') == 'BASE_GRAPH_FP64_SHARED_V1')
    bounds = result.get('bounds', {})
    expected_bounds = {'required_cases': 4, 'routes_per_case': 3, 'base_steps': 12,
        'generated_conditional_steps': 12, 'common_input_conditional_steps': 12,
        'total_optimizer_steps': 36, 'generated_paths': 48, 'maximum_seconds_soft': 300,
        'maximum_memory_bytes_soft': 2147483648,
        'gpu_steps': 24 if request['mode'] == 'CUDA' else 0,
        'cpu_steps': 12 if request['mode'] == 'CUDA' else 36}
    require(type(bounds) is dict and all(type(bounds.get(k)) is int and bounds[k] == v
                                        for k, v in expected_bounds.items()))
    if not result['decision'].startswith('PASS_'):
        return
    expected_pass = ('PASS_CPU_PRECISION_PIPELINE_CONTROLS_CUDA_NOT_EXECUTED'
        if request['mode'] == 'CPU_REFERENCE' else 'PASS_SELECTED_CUDA_PRECISION_PIPELINE_CANDIDATE_ONLY')
    require(result['decision'] == expected_pass)
    require(result.get('tolerance_policy_id') == 'factorized-device-parity-fixed-tolerances-v1')
    require(result.get('acceptance_tolerances_unchanged') == EXPECTED_TOLERANCES)
    require(type(result.get('completed_case_count')) is int and result['completed_case_count'] == 4)
    progress = result.get('execution_progress', {})
    require(type(progress) is dict and progress.get('stage') == 'COMPLETE')
    expected_progress = {'optimizer_steps_begun': 36, 'optimizer_steps_completed': 36,
        'base_updates_begun': 12, 'base_updates_completed': 12,
        'conditional_updates_begun': 12, 'conditional_updates_completed': 12,
        'conditional_control_updates_begun': 12, 'conditional_control_updates_completed': 12,
        'gpu_optimizer_steps_begun': expected_bounds['gpu_steps'],
        'cpu_optimizer_steps_begun': expected_bounds['cpu_steps']}
    require(all(type(progress.get(k)) is int and progress[k] == v for k, v in expected_progress.items()))
    cases = result.get('cases')
    require(type(cases) is list and len(cases) == 4)
    require(all(type(c) is dict for c in cases))
    require(tuple((c.get('domain_id'), c.get('method_id')) for c in cases) == EXPECTED_CASES)
    for case in cases:
        for key, value in (('completed_base_steps', 3), ('completed_generated_conditional_steps', 3),
                           ('completed_common_input_conditional_steps', 3), ('generated_path_count', 12)):
            require(type(case.get(key)) is int and case[key] == value)
        for key in ('initial_weights_exact_across_routes', 'common_base_inputs_exact_across_routes',
                    'common_conditional_inputs_exact_across_routes', 'shared_physical_weights_exact_across_routes'):
            require(case.get(key) is True)
        comparisons = case.get('comparisons', {})
        require(type(comparisons) is dict and set(comparisons) ==
                set(GATING_COMPARISONS) | {'legacy_shared_weight_physical_drift'})
        for name, row in comparisons.items():
            require(type(row) is dict and type(row.get('passed')) is bool)
            require(type(row.get('failure_count')) is int and row['failure_count'] >= 0)
            require(row['passed'] == (row['failure_count'] == 0))
            require(type(row.get('tensor_roster_sha256')) is str and
                    re.fullmatch(r'[0-9a-f]{64}', row['tensor_roster_sha256']) is not None)
            categories = row.get('categories')
            require(type(categories) is dict and set(categories) == EXPECTED_CATEGORIES[name])
            for category in categories.values():
                require(type(category) is dict and type(category.get('passed')) is bool)
                require(all(type(category.get(k)) is int and category[k] > 0 for k in ('tensors', 'scalars')))
                require(type(category.get('max_abs')) in (int, float) and
                        math.isfinite(category['max_abs']) and category['max_abs'] >= 0)
                if row['passed']:
                    require(category['passed'] is True)
                if name == 'candidate_target_exact_replay':
                    require(category['max_abs'] == 0)
            if name in GATING_COMPARISONS:
                require(row['passed'] is True and row['failure_count'] == 0)
            if name == 'candidate_target_exact_replay':
                require(row.get('full_route_records_equal') is True)
            if name == 'legacy_shared_weight_physical_drift':
                require(row.get('gates_candidate_completion') is False)
    require(type(result.get('elapsed_seconds')) in (int, float)
            and 0 <= result['elapsed_seconds'] <= MAXIMUM_SECONDS)
    require(type(result.get('process_lifetime_peak_rss_bytes')) is int
            and 0 < result['process_lifetime_peak_rss_bytes'] <= 2147483648)


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
        payload = _strict_json(output["stdout"])
        if type(payload) is not dict or type(payload.get("child_completed")) is not bool:
            raise ValueError("Invalid child envelope")
    except (ValueError, TypeError, UnicodeDecodeError):
        return {**base, "decision": "STOP_CHILD_OUTPUT_INVALID", "error_tail": _error_tail(output["stderr"])}
    if process.returncode != 0 or not payload["child_completed"]:
        return {**base, "decision": "STOP_PRECISION_PIPELINE_CHECK_INCOMPLETE",
                "error_type": payload.get("error_type"), "error": str(payload.get("error", "Child failed"))[:2048],
                "error_tail": _error_tail(output["stderr"])}
    result = payload.get("result")
    try:
        _validate_result(result, request)
    except (ValueError, TypeError, KeyError):
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
                    + ACKNOWLEDGEMENT + ", and Run all once. The fixed four-case pass has a 300-second child deadline; no iteration setting."}
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
