"""Separate precision notebook tests; CUDA is always mocked, never queried."""
import builtins
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest


NOTEBOOK = Path(__file__).resolve().parents[2] / "databricks/notebooks/factorized_base_precision_candidate_check.py"


@pytest.fixture
def notebook():
    spec = importlib.util.spec_from_file_location("precision_candidate_notebook_test", NOTEBOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def source_root(tmp_path, notebook):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='fixture'\n")
    harness = tmp_path / notebook.HARNESS_RELATIVE
    harness.parent.mkdir(parents=True)
    harness.write_text("def run_precision_candidate_check(**request):\n"
                       "    return {'decision': 'PASS_CPU_BASE_PRECISION_CONTROLS_CUDA_NOT_EXECUTED', "
                       "'source_fixture': True}\n")
    return tmp_path


def settings(notebook, root, **changes):
    return {**notebook.DEFAULTS, "repo_root": str(root), **changes}


def request(notebook, mode="CPU_REFERENCE", device="cpu"):
    return notebook.validated_request({**notebook.DEFAULTS, "mode": mode, "device": device,
                                      "acknowledgement": notebook.ACKNOWLEDGEMENT})


def test_default_inspection_is_metadata_only_no_torch_or_process(notebook, source_root, monkeypatch):
    real_import = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name == "torch" or name.startswith("torch."):
            raise AssertionError("Torch imported during inspection")
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)
    monkeypatch.setattr(notebook.subprocess, "Popen", lambda *a, **k: pytest.fail("Child launched during inspection"))
    report = notebook.run_notebook(settings(notebook, source_root), environ={})
    assert report["decision"] == "INSPECT_ONLY_COMPLETE"
    assert not report["GPU_queried_by_inspection"]
    assert not report["Torch_imported_by_inspection"]
    assert not report["parent_or_cluster_environment_modified"]
    assert not report["network_or_cloud_operation_requested"]


def test_widgets_are_clear_and_existing_selections_preserved(notebook):
    values = {"mode": "CUDA", "device": "cuda:0", "repo_root": "/project",
              "acknowledgement": notebook.ACKNOWLEDGEMENT}
    class Widgets:
        def __init__(self): self.labels = {}
        def text(self, name, default, label): self.labels[name] = label
        def dropdown(self, name, default, choices, label):
            assert default == "INSPECT_ONLY"
            assert choices == ["INSPECT_ONLY", "CPU_REFERENCE", "CUDA"]
            self.labels[name] = label
        def get(self, name): return "  " + values[name] + "  "
    class DB:
        widgets = Widgets()
    assert notebook.read_settings(DB()) == values
    assert set(DB.widgets.labels) == set(values)
    assert notebook.read_settings() == notebook.DEFAULTS


@pytest.mark.parametrize("changes", [
    {"mode": "AUTO"},
    {"mode": "CUDA", "device": "cuda:0", "acknowledgement": "RUN BOUNDED LOCAL TEST"},
    {"mode": "CPU_REFERENCE", "device": "cuda:0"},
    {"mode": "CUDA", "device": "cuda"},
    {"mode": "CUDA", "device": "cuda:-1"},
    {"mode": "CUDA", "device": "cuda:01"},
    {"mode": "CUDA", "device": "cuda:1000"},
])
def test_invalid_request_never_starts_child(notebook, source_root, changes, monkeypatch):
    monkeypatch.setattr(notebook, "launch_child", lambda *a, **k: pytest.fail("invalid request launched"))
    supplied = settings(notebook, source_root, acknowledgement=notebook.ACKNOWLEDGEMENT)
    supplied.update(changes)
    assert notebook.run_notebook(supplied)["decision"] == "INPUT_REQUIRED"


@pytest.mark.parametrize("mode,device", [("CPU_REFERENCE", "cpu"), ("CUDA", "cuda:0"), ("CUDA", "cuda:23")])
def test_fixed_one_pass_request_has_no_iterations_control(notebook, mode, device):
    assert request(notebook, mode, device) == {"mode": mode, "device": device, "maximum_seconds": 120}
    assert "iterations" not in notebook.DEFAULTS and "maximum_seconds" not in notebook.DEFAULTS


def test_source_detection_is_bounded_and_requires_new_harness(notebook, source_root, tmp_path):
    nested = source_root / "a/b"
    nested.mkdir(parents=True)
    assert notebook.detect_repo_root("", cwd=nested)[0] == source_root
    assert notebook.detect_repo_root("relative/path")[0] is None
    assert notebook.detect_repo_root(str(tmp_path / "missing"))[0] is None


@pytest.mark.parametrize("inherited", [None, ":4096:8", ":16:8"])
def test_cuda_child_only_cublas_configuration(notebook, inherited):
    parent = {"CUDA_VISIBLE_DEVICES": "2,3", "UNRELATED": "preserved"}
    if inherited is not None:
        parent["CUBLAS_WORKSPACE_CONFIG"] = inherited
    before = dict(parent)
    child, report = notebook.prepare_child_environment(request(notebook, "CUDA", "cuda:0"), parent)
    assert parent == before and child is not parent
    assert child["CUDA_VISIBLE_DEVICES"] == "2,3"
    assert child["CUBLAS_WORKSPACE_CONFIG"] == (inherited or ":4096:8")
    assert report["cublas_default_inserted_for_child_only"] == (inherited is None)
    assert not report["parent_or_cluster_environment_modified"]
    assert not report["cuda_visible_devices_modified"]


@pytest.mark.parametrize("environment", [
    {"CUBLAS_WORKSPACE_CONFIG": ""}, {"CUBLAS_WORKSPACE_CONFIG": "bad"},
    {"CUDA_VISIBLE_DEVICES": ""}, {"CUDA_VISIBLE_DEVICES": "-1"},
    {"TORCH_ALLOW_TF32_CUBLAS_OVERRIDE": "1"}, {"NVIDIA_TF32_OVERRIDE": "1"},
])
def test_conflicting_cuda_environment_stops_before_launch(notebook, source_root, environment, monkeypatch):
    monkeypatch.setattr(notebook.subprocess, "Popen", lambda *a, **k: pytest.fail("invalid CUDA environment launched"))
    before = dict(environment)
    report = notebook.run_notebook(settings(notebook, source_root, mode="CUDA", device="cuda:0",
        acknowledgement=notebook.ACKNOWLEDGEMENT), environ=environment)
    assert report["decision"] == "PRELAUNCH_INPUT_REQUIRED"
    assert environment == before


def test_cpu_preserves_existing_gpu_environment_unchanged(notebook):
    parent = {"CUDA_VISIBLE_DEVICES": "", "CUBLAS_WORKSPACE_CONFIG": "irrelevant-for-CPU"}
    child, report = notebook.prepare_child_environment(request(notebook), parent)
    assert child == parent
    assert not report["cublas_default_inserted_for_child_only"]


def test_one_real_isolated_source_child_with_fake_cpu_harness(notebook, source_root):
    report = notebook.launch_child(source_root, request(notebook))
    assert report["decision"] == "PASS_CPU_BASE_PRECISION_CONTROLS_CUDA_NOT_EXECUTED"
    assert report["result"]["source_fixture"]
    assert report["child_returncode"] == 0 and report["child_termination_confirmed"]
    assert report["captured_stdout_bytes"] < 40000


def test_child_argv_is_isolated_and_parent_environment_is_not_mutated(notebook, source_root, monkeypatch):
    parent = {"CUBLAS_WORKSPACE_CONFIG": ":16:8", "CUDA_VISIBLE_DEVICES": "0"}
    calls = []
    class Process:
        returncode = 0
    def start(argv, **kwargs):
        calls.append((argv, kwargs))
        return Process()
    monkeypatch.setattr(notebook.subprocess, "Popen", start)
    payload = {"child_completed": True, "result": {"decision": "PASS_SELECTED_CUDA_BASE_PRECISION_CANDIDATE_ONLY"}}
    monkeypatch.setattr(notebook, "_collect_bounded", lambda p, **k: (
        {"stdout": json.dumps(payload).encode(), "stderr": b""}, None, True))
    result = notebook.launch_child(source_root, request(notebook, "CUDA", "cuda:0"), environ=parent)
    argv, options = calls[0]
    assert argv[0:4] == [sys.executable, "-I", "-B", "-c"]
    assert options["env"] == parent and options["env"] is not parent
    assert "text" not in options
    assert result["decision"] == payload["result"]["decision"]
    assert len(calls) == 1


@pytest.mark.parametrize("stdout,returncode,expected", [
    (b"not JSON", 0, "STOP_CHILD_OUTPUT_INVALID"),
    (b"[]", 0, "STOP_CHILD_OUTPUT_INVALID"),
    (b'{"child_completed":"true"}', 0, "STOP_CHILD_OUTPUT_INVALID"),
    (b'{"child_completed":false,"error":"failure"}', 1, "STOP_BASE_PRECISION_CHECK_INCOMPLETE"),
    (b'{"child_completed":true,"result":{"decision":"PASS_SELECTED_CUDA_BASE_PRECISION_CANDIDATE_ONLY"}}', 0, "STOP_CHILD_OUTPUT_INVALID"),
    (b'{"child_completed":true,"result":{"decision":"PASS_UNBOUNDED"}}', 0, "STOP_CHILD_OUTPUT_INVALID"),
    (b'{"child_completed":true,"result":{"decision":"FAIL_BASE_PRECISION_CANDIDATE"}}', 0, "FAIL_BASE_PRECISION_CANDIDATE"),
])
def test_child_failure_or_wrong_scope_cannot_be_relabelled_pass(notebook, source_root, monkeypatch, stdout, returncode, expected):
    class Process: pass
    process = Process()
    process.returncode = returncode
    monkeypatch.setattr(notebook.subprocess, "Popen", lambda *a, **k: process)
    monkeypatch.setattr(notebook, "_collect_bounded", lambda *a, **k: (
        {"stdout": stdout, "stderr": b"trace"}, None, True))
    report = notebook.launch_child(source_root, request(notebook))
    assert report["decision"] == expected


def test_unconfirmed_quiescence_overrides_child_output(notebook, source_root, monkeypatch):
    class Process: returncode = None
    monkeypatch.setattr(notebook.subprocess, "Popen", lambda *a, **k: Process())
    monkeypatch.setattr(notebook, "_collect_bounded", lambda *a, **k: (
        {"stdout": b"", "stderr": b""}, "STOP_LOCAL_WALL_TIME_LIMIT", False))
    report = notebook.launch_child(source_root, request(notebook))
    assert report["decision"] == "STOP_CHILD_QUIESCENCE_UNCONFIRMED"
    assert not report["child_termination_confirmed"]


def small_process(code):
    return subprocess.Popen([sys.executable, "-I", "-B", "-c", code],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_output_is_bounded_during_collection_and_child_is_stopped(notebook, monkeypatch, stream):
    monkeypatch.setattr(notebook, "MAXIMUM_STDOUT_BYTES", 1024)
    monkeypatch.setattr(notebook, "MAXIMUM_STDERR_BYTES", 256)
    process = small_process("import sys,time; sys." + stream +
        ".buffer.write(b'x'*20000); sys." + stream + ".flush(); time.sleep(10)")
    output, stop, confirmed = notebook._collect_bounded(process, deadline=time.monotonic() + 5)
    assert stop == "STOP_OUTPUT_LIMIT" and confirmed and process.poll() is not None
    assert len(output["stdout"]) <= 1024 and len(output["stderr"]) <= 256
    assert process.stdout.closed and process.stderr.closed


def test_short_deadline_kills_real_child_and_confirms_termination(notebook):
    process = small_process("import time; time.sleep(10)")
    output, stop, confirmed = notebook._collect_bounded(process, deadline=time.monotonic() + .03)
    assert stop == "STOP_LOCAL_WALL_TIME_LIMIT"
    assert confirmed and process.poll() is not None


def test_successful_collection_retains_both_streams(notebook):
    process = small_process("import sys; print('ok'); print('diagnostic',file=sys.stderr)")
    output, stop, confirmed = notebook._collect_bounded(process, deadline=time.monotonic() + 5)
    assert stop is None and confirmed
    assert output == {"stdout": b"ok\n", "stderr": b"diagnostic\n"}


def test_notebook_interruption_does_not_abandon_child(notebook, monkeypatch):
    process = small_process("import time; time.sleep(10)")
    real_selector = notebook.selectors.DefaultSelector
    class InterruptedSelector:
        def __init__(self): self.inner = real_selector()
        def __enter__(self): return self
        def __exit__(self, *args): return self.inner.__exit__(*args)
        def register(self, *args): return self.inner.register(*args)
        def get_map(self): return self.inner.get_map()
        def select(self, **kwargs): raise KeyboardInterrupt()
    monkeypatch.setattr(notebook.selectors, "DefaultSelector", InterruptedSelector)
    with pytest.raises(KeyboardInterrupt):
        notebook._collect_bounded(process, deadline=time.monotonic() + 5)
    assert process.poll() is not None
    assert process.stdout.closed and process.stderr.closed


def test_quiescence_failure_is_not_reported_confirmed(notebook):
    class Process:
        def poll(self): return None
        def kill(self): pass
        def wait(self, timeout): raise subprocess.TimeoutExpired("child", timeout)
    assert not notebook._stop_and_confirm(Process())


def test_actual_cpu_candidate_child_after_harness_is_available(notebook):
    root = NOTEBOOK.parents[2]
    assert (root / notebook.HARNESS_RELATIVE).is_file(), "Candidate harness must accompany this notebook"
    report = notebook.launch_child(root, request(notebook))
    assert report["decision"] == "PASS_CPU_BASE_PRECISION_CONTROLS_CUDA_NOT_EXECUTED", report
    assert report["child_returncode"] == 0 and report["child_termination_confirmed"]
    assert report["captured_stdout_bytes"] < 40000
