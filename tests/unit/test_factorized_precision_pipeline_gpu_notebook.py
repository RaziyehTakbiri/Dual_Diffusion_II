"""Integrated precision notebook controls; all CUDA execution is simulated.

Real child processes below run only tiny standard-library fixtures. The actual
source-only CPU harness integration is added only after that harness is ready.
"""
import builtins
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest


NOTEBOOK = Path(__file__).resolve().parents[2] / "databricks/notebooks/factorized_precision_pipeline_gpu_check.py"
HARNESS = Path("src/heterodiff/experiments/factorized_precision_pipeline_device_check.py")
ACK = "RUN BOUNDED PRECISION PIPELINE CHECK"


@pytest.fixture
def notebook():
    spec = importlib.util.spec_from_file_location("precision_pipeline_gpu_notebook_test", NOTEBOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def source_root(tmp_path, notebook):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='synthetic-test-fixture'\n")
    harness = tmp_path / notebook.HARNESS_RELATIVE
    harness.parent.mkdir(parents=True)
    harness.write_text("def run_precision_pipeline_check(**request):\n"
                       "    raise RuntimeError('synthetic child failure')\n")
    return tmp_path


def settings(notebook, root, **changes):
    return {**notebook.DEFAULTS, "repo_root": str(root), **changes}


def request(notebook, mode="CPU_REFERENCE", device="cpu"):
    return notebook.validated_request({**notebook.DEFAULTS, "mode": mode,
        "device": device, "acknowledgement": ACK})


def test_new_contract_is_distinct_and_fixed(notebook):
    assert notebook.HARNESS_RELATIVE == HARNESS
    assert notebook.ACKNOWLEDGEMENT == ACK
    assert notebook.MAXIMUM_SECONDS == 300
    assert notebook.TERMINATION_GRACE_SECONDS == 5
    assert notebook.MAXIMUM_STDOUT_BYTES == 65536
    assert notebook.MAXIMUM_STDERR_BYTES == 16384
    assert notebook.DEFAULTS == {"mode": "INSPECT_ONLY", "device": "",
                                 "repo_root": "", "acknowledgement": ""}


def test_inspection_imports_no_torch_and_never_launches_child(notebook, source_root, monkeypatch):
    real_import = builtins.__import__
    def guard(name, *args, **kwargs):
        if name == "torch" or name.startswith("torch."):
            pytest.fail("inspection imported Torch")
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guard)
    monkeypatch.setattr(notebook.subprocess, "Popen", lambda *a, **k: pytest.fail("inspection launched a child"))
    environment = {"CUDA_VISIBLE_DEVICES": "", "CUBLAS_WORKSPACE_CONFIG": "bad-for-CUDA"}
    before = dict(environment)
    result = notebook.run_notebook(settings(notebook, source_root), environ=environment)
    assert result["decision"] == "INSPECT_ONLY_COMPLETE"
    assert not result["GPU_queried_by_inspection"] and not result["Torch_imported_by_inspection"]
    assert not result["parent_or_cluster_environment_modified"]
    assert not result["network_or_cloud_operation_requested"]
    assert environment == before


def test_widget_labels_locations_and_retained_settings(notebook):
    values = {"mode": "CUDA", "device": "cuda:0", "repo_root": "/synthetic/project",
              "acknowledgement": ACK}
    class Widgets:
        def __init__(self): self.labels = {}
        def dropdown(self, name, default, choices, label):
            assert default == "INSPECT_ONLY"
            assert choices == ["INSPECT_ONLY", "CPU_REFERENCE", "CUDA"]
            self.labels[name] = label
        def text(self, name, default, label): self.labels[name] = label
        def get(self, name): return "  " + values[name] + "  "
    class DB:
        widgets = Widgets()
    assert notebook.read_settings(DB()) == values
    assert set(DB.widgets.labels) == set(values)
    assert ACK in DB.widgets.labels["acknowledgement"]
    assert notebook.read_settings() == notebook.DEFAULTS


@pytest.mark.parametrize("changes", [
    {"mode": "AUTO"}, {"mode": "CUDA", "device": "cuda:0", "acknowledgement": "RUN BOUNDED BASE PRECISION CHECK"},
    {"mode": "CPU_REFERENCE", "device": "cuda:0"}, {"mode": "CPU_REFERENCE", "device": ""},
    {"mode": "CUDA", "device": "cuda"}, {"mode": "CUDA", "device": "cuda:-1"},
    {"mode": "CUDA", "device": "cuda:01"}, {"mode": "CUDA", "device": "cuda:1000"},
    {"mode": "CUDA", "device": True},
])
def test_bad_settings_stop_before_child(notebook, source_root, changes, monkeypatch):
    monkeypatch.setattr(notebook, "launch_child", lambda *a, **k: pytest.fail("bad request launched"))
    supplied = settings(notebook, source_root, acknowledgement=ACK)
    supplied.update(changes)
    assert notebook.run_notebook(supplied)["decision"] == "INPUT_REQUIRED"


@pytest.mark.parametrize("mode,device", [("CPU_REFERENCE", "cpu"), ("CUDA", "cuda:0"), ("CUDA", "cuda:23")])
def test_mode_request_has_fixed_deadline_and_no_campaign_controls(notebook, mode, device):
    assert request(notebook, mode, device) == {"mode": mode, "device": device, "maximum_seconds": 300}
    assert not {"iterations", "maximum_seconds", "batch_size", "seeds"} & notebook.DEFAULTS.keys()


def test_source_detection_requires_the_new_harness(notebook, source_root, tmp_path):
    nested = source_root / "a/b"
    nested.mkdir(parents=True)
    assert notebook.detect_repo_root("", cwd=nested)[0] == source_root
    assert notebook.detect_repo_root("relative/path")[0] is None
    assert notebook.detect_repo_root(str(tmp_path / "absent"))[0] is None
    (source_root / notebook.HARNESS_RELATIVE).unlink()
    legacy = source_root / "src/heterodiff/experiments/factorized_precision_candidate_qualification.py"
    legacy.write_text("# unrelated old harness\n")
    assert notebook.detect_repo_root(str(source_root))[0] is None


@pytest.mark.parametrize("inherited", [None, ":4096:8", ":16:8"])
def test_cuda_environment_copy_is_child_only(notebook, inherited):
    environment = {"CUDA_VISIBLE_DEVICES": "2,3", "UNRELATED": "keep"}
    if inherited is not None:
        environment["CUBLAS_WORKSPACE_CONFIG"] = inherited
    before = dict(environment)
    child, result = notebook.prepare_child_environment(request(notebook, "CUDA", "cuda:0"), environment)
    assert environment == before and child is not environment
    assert child["CUDA_VISIBLE_DEVICES"] == "2,3"
    assert child["UNRELATED"] == "keep"
    assert child["CUBLAS_WORKSPACE_CONFIG"] == (inherited or ":4096:8")
    assert result["cublas_default_inserted_for_child_only"] == (inherited is None)
    assert not result["parent_or_cluster_environment_modified"]
    assert not result["cuda_visible_devices_modified"]


def test_absent_cuda_mask_is_not_treated_as_disabled_or_created(notebook):
    child, result = notebook.prepare_child_environment(request(notebook, "CUDA", "cuda:0"), {})
    assert "CUDA_VISIBLE_DEVICES" not in child
    assert child["CUBLAS_WORKSPACE_CONFIG"] == ":4096:8"
    assert not result["cuda_visible_devices_modified"]


@pytest.mark.parametrize("environment", [
    {"CUBLAS_WORKSPACE_CONFIG": ""}, {"CUBLAS_WORKSPACE_CONFIG": "bad"},
    {"CUDA_VISIBLE_DEVICES": ""}, {"CUDA_VISIBLE_DEVICES": "-1"}, {"CUDA_VISIBLE_DEVICES": "  "},
    {"TORCH_ALLOW_TF32_CUBLAS_OVERRIDE": "1"}, {"NVIDIA_TF32_OVERRIDE": "1"},
])
def test_cuda_environment_conflicts_stop_before_process_creation(notebook, source_root, environment, monkeypatch):
    monkeypatch.setattr(notebook.subprocess, "Popen", lambda *a, **k: pytest.fail("conflicting environment launched"))
    before = dict(environment)
    result = notebook.run_notebook(settings(notebook, source_root, mode="CUDA", device="cuda:0",
        acknowledgement=ACK), environ=environment)
    assert result["decision"] == "PRELAUNCH_INPUT_REQUIRED"
    assert environment == before


def test_cpu_keeps_unrelated_cuda_environment_without_repair(notebook):
    environment = {"CUDA_VISIBLE_DEVICES": "", "CUBLAS_WORKSPACE_CONFIG": "not-used-on-CPU"}
    child, result = notebook.prepare_child_environment(request(notebook), environment)
    assert child == environment and child is not environment
    assert not result["cublas_default_inserted_for_child_only"]


def small_process(code):
    return subprocess.Popen([sys.executable, "-I", "-B", "-c", code],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_capture_enforces_byte_limits_during_read_and_stops_child(notebook, monkeypatch, stream):
    monkeypatch.setattr(notebook, "MAXIMUM_STDOUT_BYTES", 1024)
    monkeypatch.setattr(notebook, "MAXIMUM_STDERR_BYTES", 256)
    process = small_process("import sys,time; sys." + stream +
        ".buffer.write(b'x'*20000); sys." + stream + ".flush(); time.sleep(10)")
    output, stop, confirmed = notebook._collect_bounded(process, deadline=time.monotonic() + 5)
    assert stop == "STOP_OUTPUT_LIMIT" and confirmed and process.poll() is not None
    assert len(output["stdout"]) <= 1024 and len(output["stderr"]) <= 256
    assert process.stdout.closed and process.stderr.closed


def test_deadline_stops_real_tiny_child_and_confirms_termination(notebook):
    process = small_process("import time; time.sleep(10)")
    _, stop, confirmed = notebook._collect_bounded(process, deadline=time.monotonic() + .03)
    assert stop == "STOP_LOCAL_WALL_TIME_LIMIT" and confirmed and process.poll() is not None


def test_normal_collection_preserves_both_streams(notebook):
    process = small_process("import sys; print('ok'); print('diagnostic',file=sys.stderr)")
    output, stop, confirmed = notebook._collect_bounded(process, deadline=time.monotonic() + 5)
    assert stop is None and confirmed
    assert output == {"stdout": b"ok\n", "stderr": b"diagnostic\n"}


def test_interrupt_cleanup_does_not_abandon_real_tiny_child(notebook, monkeypatch):
    process = small_process("import time; time.sleep(10)")
    selector_type = notebook.selectors.DefaultSelector
    class InterruptedSelector:
        def __init__(self): self.inner = selector_type()
        def __enter__(self): return self
        def __exit__(self, *args): return self.inner.__exit__(*args)
        def register(self, *args): return self.inner.register(*args)
        def get_map(self): return self.inner.get_map()
        def select(self, **kwargs): raise KeyboardInterrupt()
    monkeypatch.setattr(notebook.selectors, "DefaultSelector", InterruptedSelector)
    with pytest.raises(KeyboardInterrupt):
        notebook._collect_bounded(process, deadline=time.monotonic() + 5)
    assert process.poll() is not None and process.stdout.closed and process.stderr.closed


def test_quiescence_failure_is_not_reported_as_confirmed(notebook):
    class Process:
        def poll(self): return None
        def kill(self): pass
        def wait(self, timeout): raise subprocess.TimeoutExpired("synthetic-child", timeout)
    assert not notebook._stop_and_confirm(Process())


def fake_process_output(notebook, monkeypatch, stdout, *, returncode=0, stop=None, confirmed=True):
    class Process: pass
    process = Process()
    process.returncode = returncode
    calls = []
    def start(argv, **kwargs):
        calls.append((argv, kwargs))
        return process
    monkeypatch.setattr(notebook.subprocess, "Popen", start)
    monkeypatch.setattr(notebook, "_collect_bounded", lambda *a, **k: (
        {"stdout": stdout, "stderr": b""}, stop, confirmed))
    return calls


def test_unconfirmed_quiescence_overrides_any_child_payload(notebook, source_root, monkeypatch):
    fake_process_output(notebook, monkeypatch, b'{"child_completed":true}',
                        returncode=None, stop="STOP_LOCAL_WALL_TIME_LIMIT", confirmed=False)
    result = notebook.launch_child(source_root, request(notebook))
    assert result["decision"] == "STOP_CHILD_QUIESCENCE_UNCONFIRMED"
    assert not result["child_termination_confirmed"]


@pytest.mark.parametrize("stop", ["STOP_LOCAL_WALL_TIME_LIMIT", "STOP_OUTPUT_LIMIT"])
def test_confirmed_collector_stop_overrides_payload(notebook, source_root, monkeypatch, stop):
    fake_process_output(notebook, monkeypatch, b'{"child_completed":true}', stop=stop)
    assert notebook.launch_child(source_root, request(notebook))["decision"] == stop


def test_real_stdlib_child_failure_uses_correct_integration_function(notebook, source_root):
    result = notebook.launch_child(source_root, request(notebook))
    assert result["decision"] == "STOP_PRECISION_PIPELINE_CHECK_INCOMPLETE"
    assert result["child_returncode"] != 0 and result["child_termination_confirmed"]
    assert result["error_type"] == "RuntimeError"
    assert "synthetic child failure" in result["error"]


CASES = tuple((domain, method) for domain in ("R3-PHYS", "R4-RETAIL") for method in
    ("association-aware-guide-plus-residual", "unified-direct-conditioner"))
COMPARISONS = ("common_base_cpu_vs_target", "common_conditional_cpu_vs_target",
              "shared_weight_physical_cpu_vs_target", "candidate_target_exact_replay")
TOLERANCES = {
    "forward": [2e-6, 2e-5], "coordinate_gradient": [2e-5, 2e-4],
    "coordinate_hessian": [1e-4, 1e-3], "parameter_gradient": [2e-5, 2e-4],
    "loss": [2e-6, 2e-5], "updated_parameter": [2e-6, 2e-5],
    "optimizer_moment": [2e-6, 2e-4], "physical": [2e-5, 2e-4],
}


CATEGORY_NAMES = {
    "common_base_cpu_vs_target": {"exact", "loss", "parameter_gradient", "updated_parameter", "optimizer_moment"},
    "common_conditional_cpu_vs_target": {"exact", "forward", "loss", "parameter_gradient", "updated_parameter", "optimizer_moment"},
    "shared_weight_physical_cpu_vs_target": {"physical"},
    "candidate_target_exact_replay": {"exact", "forward", "loss", "parameter_gradient", "updated_parameter", "optimizer_moment", "physical"},
    "legacy_shared_weight_physical_drift": {"physical"},
}


def comparison_record(name):
    categories = {category: {"tensors": 1, "scalars": 1, "max_abs": 0., "passed": True}
                  for category in sorted(CATEGORY_NAMES[name])}
    row = {"passed": True, "failure_count": 0, "first_failure_names": [], "categories": categories,
           "tensor_roster_sha256": "a" * 64}
    if name == "candidate_target_exact_replay":
        row["full_route_records_equal"] = True
    if name == "legacy_shared_weight_physical_drift":
        row["gates_candidate_completion"] = False
    return row


def complete_result(mode="CPU_REFERENCE", device="cpu"):
    """Independent positive envelope; no Torch or production tensors involved."""
    gpu_steps, cpu_steps = (24, 12) if mode == "CUDA" else (0, 36)
    result = {
        "schema_version": "factorized-precision-pipeline-device-check-v1",
        "mode": mode, "device": device, "precision_policy": "BASE_GRAPH_FP64_SHARED_V1",
        "decision": ("PASS_SELECTED_CUDA_PRECISION_PIPELINE_CANDIDATE_ONLY" if mode == "CUDA"
                     else "PASS_CPU_PRECISION_PIPELINE_CONTROLS_CUDA_NOT_EXECUTED"),
        "bounds": {"required_cases": 4, "routes_per_case": 3, "base_steps": 12,
            "generated_conditional_steps": 12, "common_input_conditional_steps": 12,
            "total_optimizer_steps": 36, "generated_paths": 48, "maximum_seconds_soft": 300,
            "maximum_memory_bytes_soft": 2147483648, "gpu_steps": gpu_steps, "cpu_steps": cpu_steps},
        "execution_progress": {"stage": "COMPLETE", "optimizer_steps_begun": 36,
            "optimizer_steps_completed": 36, "base_updates_begun": 12, "base_updates_completed": 12,
            "conditional_updates_begun": 12, "conditional_updates_completed": 12,
            "conditional_control_updates_begun": 12, "conditional_control_updates_completed": 12,
            "gpu_optimizer_steps_begun": gpu_steps, "cpu_optimizer_steps_begun": cpu_steps},
        "tolerance_policy_id": "factorized-device-parity-fixed-tolerances-v1",
        "acceptance_tolerances_unchanged": deepcopy(TOLERANCES), "completed_case_count": 4,
        "elapsed_seconds": 1.25, "process_lifetime_peak_rss_bytes": 123456789, "cases": [],
    }
    for domain, method in CASES:
        comparisons = {name: comparison_record(name) for name in CATEGORY_NAMES}
        result["cases"].append({"domain_id": domain, "method_id": method,
            "completed_base_steps": 3, "completed_generated_conditional_steps": 3,
            "completed_common_input_conditional_steps": 3, "generated_path_count": 12,
            "initial_weights_exact_across_routes": True, "common_base_inputs_exact_across_routes": True,
            "common_conditional_inputs_exact_across_routes": True,
            "shared_physical_weights_exact_across_routes": True, "comparisons": comparisons})
    return result


def envelope(result):
    return json.dumps({"child_completed": True, "result": result}, separators=(",", ":")).encode()


def launch_mock(notebook, source_root, monkeypatch, result, *, mode="CPU_REFERENCE", device="cpu"):
    fake_process_output(notebook, monkeypatch, envelope(result))
    return notebook.launch_child(source_root, request(notebook, mode, device), environ={})


@pytest.mark.parametrize("mode,device", [("CPU_REFERENCE", "cpu"), ("CUDA", "cuda:0"), ("CUDA", "cuda:23")])
def test_complete_positive_report_is_accepted_in_exact_requested_mode(notebook, source_root, monkeypatch, mode, device):
    result = complete_result(mode, device)
    report = launch_mock(notebook, source_root, monkeypatch, result, mode=mode, device=device)
    assert report["decision"] == result["decision"], report
    assert report["result"] == result
    assert report["child_termination_confirmed"] and report["child_returncode"] == 0


def test_parent_launch_is_isolated_with_only_child_environment_copy(notebook, source_root, monkeypatch):
    parent = {"CUBLAS_WORKSPACE_CONFIG": ":16:8", "CUDA_VISIBLE_DEVICES": "2,3"}
    result = complete_result("CUDA", "cuda:0")
    calls = fake_process_output(notebook, monkeypatch, envelope(result))
    report = notebook.launch_child(source_root, request(notebook, "CUDA", "cuda:0"), environ=parent)
    assert report["decision"] == result["decision"]
    assert len(calls) == 1
    argv, options = calls[0]
    assert argv[:4] == [sys.executable, "-I", "-B", "-c"]
    assert options["env"] == parent and options["env"] is not parent
    assert "text" not in options and options["cwd"] == str(source_root)
    assert json.loads(argv[-1]) == {"mode": "CUDA", "device": "cuda:0", "maximum_seconds": 300}
    assert "factorized_precision_pipeline_device_check" in argv[4]
    assert "run_precision_pipeline_check" in argv[4]


@pytest.mark.parametrize("field,value", [
    ("schema_version", "old-schema"), ("mode", "CUDA"), ("device", "cuda:0"),
    ("precision_policy", "LEGACY_FP32"), ("decision", "PASS_SELECTED_CUDA_PRECISION_PIPELINE_CANDIDATE_ONLY"),
    ("decision", "PASS_SELECTED_CUDA_BASE_PRECISION_CANDIDATE_ONLY"),
    ("completed_case_count", 3), ("completed_case_count", 4.0),
    ("tolerance_policy_id", "relaxed-policy"), ("elapsed_seconds", -1.),
    ("elapsed_seconds", 300.01), ("elapsed_seconds", True),
    ("process_lifetime_peak_rss_bytes", 2147483649), ("process_lifetime_peak_rss_bytes", True),
])
def test_wrong_completion_metadata_cannot_pass(notebook, source_root, monkeypatch, field, value):
    result = complete_result()
    result[field] = value
    assert launch_mock(notebook, source_root, monkeypatch, result)["decision"] == "STOP_CHILD_OUTPUT_INVALID"


@pytest.mark.parametrize("field", ["required_cases", "routes_per_case", "base_steps", "generated_conditional_steps",
    "common_input_conditional_steps", "total_optimizer_steps", "generated_paths", "maximum_seconds_soft",
    "maximum_memory_bytes_soft", "gpu_steps", "cpu_steps"])
def test_wrong_fixed_bound_cannot_pass(notebook, source_root, monkeypatch, field):
    result = complete_result()
    result["bounds"][field] += 1
    assert launch_mock(notebook, source_root, monkeypatch, result)["decision"] == "STOP_CHILD_OUTPUT_INVALID"


@pytest.mark.parametrize("field", ["optimizer_steps_begun", "optimizer_steps_completed", "base_updates_begun",
    "base_updates_completed", "conditional_updates_begun", "conditional_updates_completed",
    "conditional_control_updates_begun", "conditional_control_updates_completed",
    "gpu_optimizer_steps_begun", "cpu_optimizer_steps_begun"])
def test_wrong_observed_step_count_cannot_pass(notebook, source_root, monkeypatch, field):
    result = complete_result()
    result["execution_progress"][field] += 1
    assert launch_mock(notebook, source_root, monkeypatch, result)["decision"] == "STOP_CHILD_OUTPUT_INVALID"


@pytest.mark.parametrize("tamper", ["duplicate", "missing", "reordered", "wrong_method", "wrong_case_steps",
    "wrong_case_paths", "bad_exact_flag", "bad_exact_flag_type", "not_complete", "relaxed_tolerance",
    "integer_bool", "missing_comparison", "failed_comparison", "nonzero_failure_count"])
def test_case_controls_and_acceptance_contract_cannot_be_skipped(notebook, source_root, monkeypatch, tamper):
    result = complete_result()
    first = result["cases"][0]
    if tamper == "duplicate": result["cases"][1] = deepcopy(first)
    elif tamper == "missing": result["cases"].pop()
    elif tamper == "reordered": result["cases"].reverse()
    elif tamper == "wrong_method": first["method_id"] = "BASE_ONLY"
    elif tamper == "wrong_case_steps": first["completed_base_steps"] = 2
    elif tamper == "wrong_case_paths": first["generated_path_count"] = 11
    elif tamper == "bad_exact_flag": first["common_conditional_inputs_exact_across_routes"] = False
    elif tamper == "bad_exact_flag_type": first["initial_weights_exact_across_routes"] = 1
    elif tamper == "not_complete": result["execution_progress"]["stage"] = "RUNNING"
    elif tamper == "relaxed_tolerance": result["acceptance_tolerances_unchanged"]["updated_parameter"][0] = .01
    elif tamper == "integer_bool": result["bounds"]["gpu_steps"] = False
    elif tamper == "missing_comparison": del first["comparisons"][COMPARISONS[0]]
    elif tamper == "failed_comparison": first["comparisons"][COMPARISONS[0]]["passed"] = False
    else: first["comparisons"][COMPARISONS[0]]["failure_count"] = 1
    assert launch_mock(notebook, source_root, monkeypatch, result)["decision"] == "STOP_CHILD_OUTPUT_INVALID"


@pytest.mark.parametrize("decision", ["FAIL_PRECISION_PIPELINE_CANDIDATE", "STOP_PRECISION_PIPELINE_CHECK_INCOMPLETE"])
def test_harness_nonpass_stays_nonpass_without_claiming_complete_cases(notebook, source_root, monkeypatch, decision):
    result = complete_result()
    result.update(decision=decision, completed_case_count=0, cases=[])
    result["execution_progress"]["stage"] = "FAILED"
    assert launch_mock(notebook, source_root, monkeypatch, result)["decision"] == decision


def test_legacy_drift_failure_is_visible_but_does_not_gate_candidate(notebook, source_root, monkeypatch):
    result = complete_result()
    row = result["cases"][0]["comparisons"]["legacy_shared_weight_physical_drift"]
    row.update(passed=False, failure_count=1, first_failure_names=["legacy_physical"])
    row["categories"]["physical"].update(passed=False, max_abs=.1)
    report = launch_mock(notebook, source_root, monkeypatch, result)
    assert report["decision"] == result["decision"]
    assert not report["result"]["cases"][0]["comparisons"]["legacy_shared_weight_physical_drift"]["passed"]


@pytest.mark.parametrize("tamper", ["duplicate_top_key", "duplicate_nested_key", "nan", "infinity",
    "negative_infinity", "float_overflow", "negative_float_overflow", "array_envelope", "string_completion",
    "invalid_utf8", "prefix_text", "trailing_json", "null_result"])
def test_strict_json_and_child_envelope_reject_ambiguous_payload(notebook, source_root, monkeypatch, tamper):
    valid = envelope(complete_result())
    if tamper == "duplicate_top_key": payload = valid.replace(b'{"child_completed":true', b'{"child_completed":false,"child_completed":true', 1)
    elif tamper == "duplicate_nested_key": payload = valid.replace(b'"completed_case_count":4', b'"completed_case_count":3,"completed_case_count":4', 1)
    elif tamper in ("nan", "infinity", "negative_infinity", "float_overflow", "negative_float_overflow"):
        token = {"nan": b"NaN", "infinity": b"Infinity", "negative_infinity": b"-Infinity",
                 "float_overflow": b"1e400", "negative_float_overflow": b"-1e400"}[tamper]
        payload = valid[:-1] + b',"unrelated_numeric_field":' + token + b'}'
    elif tamper == "array_envelope": payload = b"[]"
    elif tamper == "string_completion": payload = valid.replace(b'"child_completed":true', b'"child_completed":"true"', 1)
    elif tamper == "invalid_utf8": payload = b"\xff"
    elif tamper == "prefix_text": payload = b"hello\n" + valid
    elif tamper == "trailing_json": payload = valid + b"{}"
    else: payload = b'{"child_completed":true,"result":null}'
    fake_process_output(notebook, monkeypatch, payload)
    assert notebook.launch_child(source_root, request(notebook))["decision"] == "STOP_CHILD_OUTPUT_INVALID"


@pytest.mark.parametrize("returncode,completed", [(1, True), (0, False), (1, False)])
def test_failed_child_cannot_be_relabelled_pass_from_result(notebook, source_root, monkeypatch, returncode, completed):
    payload = json.dumps({"child_completed": completed, "result": complete_result()}).encode()
    fake_process_output(notebook, monkeypatch, payload, returncode=returncode)
    assert notebook.launch_child(source_root, request(notebook))["decision"] == "STOP_PRECISION_PIPELINE_CHECK_INCOMPLETE"


def test_real_stdlib_positive_child_uses_only_selected_source(notebook, source_root):
    result = complete_result()
    (source_root / notebook.HARNESS_RELATIVE).write_text(
        "import json\n_RESULT = json.loads(" + repr(json.dumps(result)) + ")\n"
        "def run_precision_pipeline_check(**request):\n    return _RESULT\n")
    report = notebook.launch_child(source_root, request(notebook))
    assert report["decision"] == result["decision"], report
    assert report["result"] == result and report["child_termination_confirmed"]


def test_child_rejects_harness_file_identity_outside_selected_source(notebook, source_root):
    (source_root / notebook.HARNESS_RELATIVE).write_text(
        "__file__ = '/synthetic/outside-source/harness.py'\n"
        "def run_precision_pipeline_check(**request):\n    raise AssertionError('must not run')\n")
    report = notebook.launch_child(source_root, request(notebook))
    assert report["decision"] == "STOP_PRECISION_PIPELINE_CHECK_INCOMPLETE"
    assert report["error_type"] == "RuntimeError"
    assert "source" in report["error"].lower()


@pytest.mark.parametrize("comparison", tuple(CATEGORY_NAMES))
@pytest.mark.parametrize("tamper", ["missing_categories", "empty_categories", "missing_category",
    "extra_category", "nonpositive_tensors", "nonpositive_scalars", "bool_count", "bad_max_abs",
    "category_failed", "bad_category_type", "bad_digest", "missing_digest"])
def test_every_comparison_requires_real_structured_summary(notebook, source_root, monkeypatch, comparison, tamper):
    result = complete_result()
    row = result["cases"][0]["comparisons"][comparison]
    category_name = next(iter(row["categories"]))
    category = row["categories"][category_name]
    if tamper == "missing_categories": del row["categories"]
    elif tamper == "empty_categories": row["categories"] = {}
    elif tamper == "missing_category": del row["categories"][category_name]
    elif tamper == "extra_category": row["categories"]["unrelated"] = deepcopy(category)
    elif tamper == "nonpositive_tensors": category["tensors"] = 0
    elif tamper == "nonpositive_scalars": category["scalars"] = -1
    elif tamper == "bool_count": category["tensors"] = True
    elif tamper == "bad_max_abs": category["max_abs"] = -1.
    elif tamper == "category_failed": category["passed"] = False
    elif tamper == "bad_category_type": row["categories"][category_name] = None
    elif tamper == "bad_digest": row["tensor_roster_sha256"] = "A" * 64
    else: del row["tensor_roster_sha256"]
    assert launch_mock(notebook, source_root, monkeypatch, result)["decision"] == "STOP_CHILD_OUTPUT_INVALID"


@pytest.mark.parametrize("tamper", ["legacy_null", "legacy_text", "legacy_gate_true", "legacy_gate_absent",
    "replay_records_false", "replay_records_absent", "replay_positive_difference", "comparison_boolean",
    "comparison_bad_count", "legacy_inconsistent_count"])
def test_legacy_and_replay_evidence_cannot_be_replaced_by_labels(notebook, source_root, monkeypatch, tamper):
    result = complete_result()
    rows = result["cases"][0]["comparisons"]
    legacy = rows["legacy_shared_weight_physical_drift"]
    replay = rows["candidate_target_exact_replay"]
    if tamper == "legacy_null": rows["legacy_shared_weight_physical_drift"] = None
    elif tamper == "legacy_text": rows["legacy_shared_weight_physical_drift"] = "not measured"
    elif tamper == "legacy_gate_true": legacy["gates_candidate_completion"] = True
    elif tamper == "legacy_gate_absent": del legacy["gates_candidate_completion"]
    elif tamper == "replay_records_false": replay["full_route_records_equal"] = False
    elif tamper == "replay_records_absent": del replay["full_route_records_equal"]
    elif tamper == "replay_positive_difference": replay["categories"]["physical"]["max_abs"] = 1e-15
    elif tamper == "comparison_boolean": legacy["passed"] = 1
    elif tamper == "comparison_bad_count": legacy["failure_count"] = False
    else: legacy.update(passed=False, failure_count=0)
    assert launch_mock(notebook, source_root, monkeypatch, result)["decision"] == "STOP_CHILD_OUTPUT_INVALID"


def test_child_rechecks_late_import_origins_after_function_returns(notebook, source_root):
    result = complete_result()
    (source_root / notebook.HARNESS_RELATIVE).write_text(
        "import json,sys,types\n_RESULT = json.loads(" + repr(json.dumps(result)) + ")\n"
        "def run_precision_pipeline_check(**request):\n"
        "    late = types.ModuleType('heterodiff.late_wrong_source')\n"
        "    late.__file__ = '/synthetic/outside-source/late.py'\n"
        "    sys.modules[late.__name__] = late\n"
        "    return _RESULT\n")
    report = notebook.launch_child(source_root, request(notebook))
    assert report["decision"] == "STOP_PRECISION_PIPELINE_CHECK_INCOMPLETE"
    assert "source" in report["error"].lower()
