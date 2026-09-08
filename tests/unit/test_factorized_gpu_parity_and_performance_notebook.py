"""Notebook wrapper qualification only; fake CUDA metadata never queries a GPU."""

import json
from pathlib import Path
import runpy
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "databricks/notebooks/factorized_gpu_parity_and_performance.py"


@pytest.fixture
def notebook():
    return runpy.run_path(str(NOTEBOOK), run_name="source_notebook_under_test")


def fake_repo(tmp_path, *, cuda_build=False, harness_body=None):
    root = tmp_path / "Git folder with spaces"
    experiments = root / "src/heterodiff/experiments"
    experiments.mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='notebook-wrapper-test'\nversion='0.0.0'\n")
    (root / "src/heterodiff/__init__.py").write_text("")
    (experiments / "__init__.py").write_text("")
    (root / "src/torch.py").write_text(
        "from types import SimpleNamespace\nversion=SimpleNamespace(cuda="
        + repr("synthetic-metadata-not-a-GPU" if cuda_build else None) + ")\n")
    (experiments / "factorized_device_qualification.py").write_text(harness_body or (
        "def run_qualification(**request):\n"
        "    print('harmless fixture log, not the JSON result')\n"
        "    return {'request': request, 'fixture_only': True}\n"))
    return root


def settings(notebook, **updates):
    return {**notebook["DEFAULTS"], **updates}


def forbidden(*args, **kwargs):
    raise AssertionError("inspection or invalid input attempted execution")


def test_default_inspection_launches_no_child_and_does_not_import_torch(notebook, tmp_path, monkeypatch):
    root = fake_repo(tmp_path)
    function = notebook["run_notebook"]
    monkeypatch.setitem(function.__globals__, "launch_child", forbidden)
    before = "torch" in sys.modules
    report = function(settings(notebook), cwd=root / "src", environ={})
    assert report["decision"] == "INSPECT_ONLY_COMPLETE"
    assert report["scope"] == "SOURCE_ONLY_FACTORIZED_LOCAL_QUALIFICATION_NOT_INSTALLED_RELEASE"
    assert report["repo_root"] == str(root)
    assert ("torch" in sys.modules) is before
    for field in ("gpu_queried_by_notebook_inspection", "package_install_or_restart_requested",
                  "network_or_cloud_operation_requested", "real_data_requested", "old_installed_release_replaced"):
        assert report[field] is False


def test_inspection_works_in_bare_python_without_site_packages_or_torch(tmp_path):
    root = fake_repo(tmp_path)
    script = r'''
import builtins, json, runpy, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'numpy'):
        raise RuntimeError('NUMERICAL_LIBRARY_IMPORT_DURING_INSPECTION')
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
namespace = runpy.run_path(sys.argv[1], run_name='notebook_test')
result = namespace['run_notebook'](namespace['DEFAULTS'], cwd=sys.argv[2], environ={})
assert result['decision'] == 'INSPECT_ONLY_COMPLETE'
assert 'torch' not in sys.modules
print(json.dumps(result))
'''
    result = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", script, str(NOTEBOOK), str(root)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["package_metadata"] == {"numpy": None, "torch": None}


def test_bounded_root_lookup_uses_file_cwd_or_explicit_widget_without_git(notebook, tmp_path):
    root = fake_repo(tmp_path)
    detect = notebook["detect_repo_root"]
    assert detect("", notebook_file=str(root / "databricks/notebooks/example.py"), cwd=tmp_path) == (root, None)
    assert detect("", cwd=root / "src/heterodiff/experiments") == (root, None)
    assert detect(str(root), cwd=tmp_path) == (root, None)
    assert detect("https://example.com/repo", cwd=tmp_path)[0] is None
    assert detect(str(tmp_path / "absent"), cwd=root)[0] is None
    too_deep = root.joinpath(*[f"d{i}" for i in range(11)])
    too_deep.mkdir(parents=True)
    assert detect("", cwd=too_deep)[0] is None


def test_missing_source_folder_gives_exact_widget_action(notebook, tmp_path):
    report = notebook["run_notebook"](settings(notebook), cwd=tmp_path, environ={})
    assert report["decision"] == "SOURCE_FOLDER_REQUIRED"
    assert "repo_root" in report["next_action"] and "pyproject.toml" in report["next_action"]


@pytest.mark.parametrize("change", [
    {"mode": "TRAIN"}, {"mode": "CPU_REFERENCE"},
    {"mode": "CPU_REFERENCE", "device": "cuda:0"},
    {"mode": "CUDA", "device": "cuda"}, {"mode": "CUDA", "device": "cuda:-1"},
    {"iterations": "0"}, {"iterations": "4"}, {"iterations": "1.0"},
    {"maximum_seconds": "4"}, {"maximum_seconds": "301"},
])
def test_invalid_execution_controls_never_launch(notebook, tmp_path, monkeypatch, change):
    root = fake_repo(tmp_path)
    function = notebook["run_notebook"]
    monkeypatch.setitem(function.__globals__, "launch_child", forbidden)
    values = settings(notebook, mode="CPU_REFERENCE", device="cpu", acknowledgement="RUN BOUNDED LOCAL TEST")
    values.update(change)
    if change == {"mode": "CPU_REFERENCE"}:
        values["acknowledgement"] = ""
    report = function(values, cwd=root, environ={})
    assert report["decision"] == "INPUT_REQUIRED"


@pytest.mark.parametrize("mask", ["", "-1", "   "])
def test_existing_cpu_visibility_mask_is_explained_never_mutated(notebook, tmp_path, monkeypatch, mask):
    root = fake_repo(tmp_path)
    function = notebook["run_notebook"]
    monkeypatch.setitem(function.__globals__, "launch_child", forbidden)
    environment = {"CUDA_VISIBLE_DEVICES": mask}
    inspect = function(settings(notebook), cwd=root, environ=environment)
    assert "hides GPUs" in inspect["next_action"]
    report = function(settings(notebook, mode="CUDA", device="cuda:0", acknowledgement="RUN BOUNDED LOCAL TEST"),
                      cwd=root, environ=environment)
    assert report["decision"] == "CUDA_HIDDEN_BY_EXISTING_ENVIRONMENT"
    assert environment == {"CUDA_VISIBLE_DEVICES": mask}


def test_widget_creation_and_values_use_plain_visible_controls(notebook):
    class Widgets:
        values = {"mode": "CPU_REFERENCE", "device": "cpu"}
        created = []
        def dropdown(self, name, default, choices, label):
            self.created.append((name, label))
            self.values.setdefault(name, default)
        def text(self, name, default, label):
            self.created.append((name, label))
            self.values.setdefault(name, default)
        def get(self, name):
            return self.values[name]
    class Utilities:
        widgets = Widgets()
    values = notebook["read_settings"](Utilities())
    assert values["mode"] == "CPU_REFERENCE" and values["device"] == "cpu"
    assert len(Utilities.widgets.created) == 6
    assert values["acknowledgement"] == ""


@pytest.mark.parametrize("value", ["", ":4096:2", "other"])
def test_cublas_prelaunch_status_is_visible_and_cuda_stops_before_launch(notebook, tmp_path, monkeypatch, value):
    root = fake_repo(tmp_path)
    function = notebook["run_notebook"]
    monkeypatch.setitem(function.__globals__, "launch_child", forbidden)
    environment = {} if value is None else {"CUBLAS_WORKSPACE_CONFIG": value}
    before = dict(environment)
    inspection = function(settings(notebook), cwd=root, environ=environment)
    assert inspection["cublas_workspace_config_setting"] == value
    assert inspection["cublas_prelaunch_value_ready"] is False
    assert "CUBLAS_WORKSPACE_CONFIG" in inspection["next_action"]
    report = function(settings(notebook, mode="CUDA", device="cuda:0", acknowledgement="RUN BOUNDED LOCAL TEST"),
                      cwd=root, environ=environment)
    assert report["decision"] == "CUDA_PRELAUNCH_CONFIG_REQUIRED"
    assert ":4096:8" in report["next_action"] and ":16:8" in report["next_action"]
    assert environment == before


@pytest.mark.parametrize("value", [":4096:8", ":16:8"])
def test_valid_cublas_setting_is_reported_without_cuda_query(notebook, tmp_path, monkeypatch, value):
    root = fake_repo(tmp_path)
    function = notebook["run_notebook"]
    monkeypatch.setitem(function.__globals__, "launch_child", forbidden)
    report = function(settings(notebook), cwd=root, environ={"CUBLAS_WORKSPACE_CONFIG": value})
    assert report["decision"] == "INSPECT_ONLY_COMPLETE"
    assert report["cublas_prelaunch_value_ready"] is True
    assert report["gpu_queried_by_notebook_inspection"] is False


def test_complete_cuda_controls_forward_exact_index_without_fallback(notebook, tmp_path, monkeypatch):
    root = fake_repo(tmp_path)
    function = notebook["run_notebook"]
    received = []
    def record_request(root_path, request, *, environ):
        received.append((root_path, request, dict(environ)))
        return {"decision": "FIXTURE_NO_EXECUTION"}
    monkeypatch.setitem(function.__globals__, "launch_child", record_request)
    environment = {"CUDA_VISIBLE_DEVICES": "3", "CUBLAS_WORKSPACE_CONFIG": ":4096:8"}
    values = settings(notebook, mode="CUDA", device="cuda:0", iterations="3",
                      maximum_seconds="300", acknowledgement="RUN BOUNDED LOCAL TEST")
    report = function(values, cwd=root, environ=environment)
    assert report["decision"] == "FIXTURE_NO_EXECUTION"
    assert received == [(root, {"mode": "CUDA", "device": "cuda:0", "iterations": 3, "maximum_seconds": 300}, environment)]
    assert environment == {"CUDA_VISIBLE_DEVICES": "3", "CUBLAS_WORKSPACE_CONFIG": ":4096:8"}


def test_explicit_source_only_child_supervisor_returns_json_fixture_result(notebook, tmp_path):
    root = fake_repo(tmp_path)
    request = {"mode": "CPU_REFERENCE", "device": "cpu", "iterations": 1, "maximum_seconds": 10}
    result = notebook["launch_child"](root, request)
    assert result["decision"] == "LOCAL_HARNESS_COMPLETED_REVIEW_RESULT"
    assert result["result"] == {"request": request, "fixture_only": True}
    assert result["child_returncode"] == 0


def test_cpu_only_torch_metadata_stops_cuda_without_fallback_or_query(notebook, tmp_path):
    root = fake_repo(tmp_path, harness_body="raise AssertionError('harness must not import on CPU-only CUDA request')\n")
    result = notebook["launch_child"](root, {"mode": "CUDA", "device": "cuda:0", "iterations": 1, "maximum_seconds": 10})
    assert result["decision"] == "STOP_LOCAL_QUALIFICATION"
    assert "CPU-only PyTorch" in result["error"] and "No installation" in result["error"]


def test_wall_deadline_terminates_local_child_and_never_returns_pass(notebook, tmp_path):
    root = fake_repo(tmp_path, harness_body="import time\ndef run_qualification(**request):\n    time.sleep(10)\n")
    # Direct supervisor seam uses a short bound; the visible widget requires>=5s.
    result = notebook["launch_child"](root, {"mode": "CPU_REFERENCE", "device": "cpu", "iterations": 1, "maximum_seconds": .05})
    assert result["decision"] == "STOP_LOCAL_WALL_TIME_LIMIT"
    assert result["child_termination_confirmed"] is True
    assert "result" not in result


def test_notebook_interruption_requests_child_termination_before_propagating(notebook, tmp_path, monkeypatch):
    class InterruptedChild:
        calls = 0
        killed = False
        def communicate(self, timeout):
            self.calls += 1
            if self.calls == 1:
                raise KeyboardInterrupt()
            return "", ""
        def kill(self):
            self.killed = True
    child = InterruptedChild()
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: child)
    with pytest.raises(KeyboardInterrupt):
        notebook["launch_child"](tmp_path, {"mode": "CPU_REFERENCE", "maximum_seconds": 5})
    assert child.killed and child.calls == 2


def test_actual_four_case_cpu_harness_through_isolated_source_supervisor(notebook):
    pytest.importorskip("torch")
    values = settings(notebook, mode="CPU_REFERENCE", device="cpu", iterations="1",
                      maximum_seconds="120", acknowledgement="RUN BOUNDED LOCAL TEST")
    report = notebook["run_notebook"](values, cwd=ROOT, environ={})
    assert report["decision"] == "LOCAL_HARNESS_COMPLETED_REVIEW_RESULT", report
    result = report["result"]
    assert result["decision"] == "PASS_CPU_REFERENCE_CUDA_NOT_EXECUTED", result
    assert result["cuda_execution"] == "CUDA_NOT_EXECUTED"
    assert result["completed_case_count"] == result["required_case_count"] == 4
    assert all(case["passed"] and case["same_device_repeatability"]["passed"] for case in result["cases"])
    assert result["timing_scope"]["explicit_cuda_synchronize_calls"] == 0
    assert result["scope"]["F105_factory_or_checkpoint_validation_executed"] is False
    assert result["scope"]["production_qualification"] is False
    assert result["scope"]["paid_or_remote_jobs_launched"] is False


def test_missing_cublas_is_ready_as_planned_child_only_default_not_cluster_repair(notebook, tmp_path, monkeypatch):
    root = fake_repo(tmp_path)
    function = notebook["run_notebook"]
    monkeypatch.setitem(function.__globals__, "launch_child", forbidden)
    environment = {}
    report = function(settings(notebook), cwd=root, environ=environment)
    assert report["decision"] == "INSPECT_ONLY_COMPLETE"
    assert report["wrapper_revision"] == "factorized-gpu-wrapper-v2-child-environment"
    assert report["cublas_workspace_config_setting"] is None
    assert report["cublas_inherited_value_ready"] is False
    assert report["cublas_prelaunch_value_ready"] is True
    assert report["cublas_cuda_child_value_planned"] == ":4096:8"
    assert report["cublas_missing_default_is_child_only"] is True
    assert report["parent_or_cluster_environment_modified"] is False
    assert "No cluster setting or restart" in report["next_action"]
    assert report["cuda_visible_devices_setting"] is None and environment == {}


@pytest.mark.parametrize("mode,inherited,effective,inserted", [
    ("CPU_REFERENCE", None, None, False),
    ("CPU_REFERENCE", "explicit-test-value", "explicit-test-value", False),
    ("CUDA", None, ":4096:8", True),
    ("CUDA", ":16:8", ":16:8", False),
    ("CUDA", ":4096:8", ":4096:8", False),
])
def test_child_environment_copy_preserves_parent_and_unrelated_settings(notebook, mode, inherited, effective, inserted):
    environment = {"UNRELATED_TEST_KEY": "retained"}
    if inherited is not None:
        environment["CUBLAS_WORKSPACE_CONFIG"] = inherited
    before = dict(environment)
    child, report = notebook["prepare_child_environment"]({"mode": mode}, environment)
    assert child is not environment and environment == before
    assert child["UNRELATED_TEST_KEY"] == "retained"
    assert "CUDA_VISIBLE_DEVICES" not in child
    assert child.get("CUBLAS_WORKSPACE_CONFIG") == effective
    assert report["cublas_effective_child_value"] == effective
    assert report["cublas_default_inserted_for_child_only"] is inserted
    assert report["parent_or_cluster_environment_modified"] is False
    assert report["cuda_visible_devices_modified"] is False


@pytest.mark.parametrize("value", ["", "other", ":4096:2"])
def test_conflicting_cublas_is_refused_even_at_direct_supervisor_seam(notebook, tmp_path, monkeypatch, value):
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    environment = {"CUBLAS_WORKSPACE_CONFIG": value}
    with pytest.raises(ValueError, match="conflicts"):
        notebook["launch_child"](tmp_path, {"mode": "CUDA"}, environ=environment)
    assert environment == {"CUBLAS_WORKSPACE_CONFIG": value}


@pytest.mark.parametrize("inherited,mask", [(None, None), (":16:8", "3")])
def test_fake_cuda_child_receives_cublas_before_torch_import_without_parent_mutation(notebook, tmp_path, inherited, mask):
    # This fixture is a tiny fake Torch module; no CUDA library is imported.
    effective = inherited or ":4096:8"
    root = fake_repo(tmp_path, cuda_build=True, harness_body=(
        "import os\ndef run_qualification(**request):\n"
        "    return {'fixture_only':True,'cublas':os.environ.get('CUBLAS_WORKSPACE_CONFIG'),"
        "'mask':os.environ.get('CUDA_VISIBLE_DEVICES')}\n"))
    torch_fixture = root / "src/torch.py"
    torch_fixture.write_text(
        "import os\nassert os.environ.get('CUBLAS_WORKSPACE_CONFIG') == " + repr(effective) + "\n"
        + "assert os.environ.get('CUDA_VISIBLE_DEVICES') == " + repr(mask) + "\n"
        + torch_fixture.read_text())
    environment = {}
    if inherited is not None:
        environment["CUBLAS_WORKSPACE_CONFIG"] = inherited
    if mask is not None:
        environment["CUDA_VISIBLE_DEVICES"] = mask
    before = dict(environment)
    values = settings(notebook, mode="CUDA", device="cuda:0", acknowledgement="RUN BOUNDED LOCAL TEST")
    report = notebook["run_notebook"](values, cwd=root, environ=environment)
    assert report["decision"] == "LOCAL_HARNESS_COMPLETED_REVIEW_RESULT", report
    assert report["result"] == {"fixture_only": True, "cublas": effective, "mask": mask}
    assert report["child_environment"]["cublas_default_inserted_for_child_only"] is (inherited is None)
    assert environment == before


@pytest.mark.parametrize("name", ["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE", "NVIDIA_TF32_OVERRIDE"])
@pytest.mark.parametrize("value", ["1", "", "other"])
def test_conflicting_tf32_override_is_visible_before_any_child(notebook, tmp_path, monkeypatch, name, value):
    root = fake_repo(tmp_path)
    function = notebook["run_notebook"]
    monkeypatch.setitem(function.__globals__, "launch_child", forbidden)
    environment = {name: value}
    inspection = function(settings(notebook), cwd=root, environ=environment)
    assert inspection["tf32_environment_overrides"][name] == value
    assert inspection["tf32_environment_policy_ready"] is False
    assert "TF32 override" in inspection["next_action"]
    report = function(settings(notebook, mode="CUDA", device="cuda:0", acknowledgement="RUN BOUNDED LOCAL TEST"),
                      cwd=root, environ=environment)
    assert report["decision"] == "CUDA_TF32_OVERRIDE_CONFLICT"
    assert environment == {name: value}
