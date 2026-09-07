from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ROOT / "databricks/notebooks/b08_conventional_runtime_support.py"
HISTORICAL_FILE = (
    "tests/unit/test_configuration_totalized_jump_potential_composer_torch.py"
)
HISTORICAL_FUNCTION = (
    "test_checkpoint17_module_keeps_checkpoint14_source_and_api_isolated"
)
HISTORICAL_NODEID = HISTORICAL_FILE + "::" + HISTORICAL_FUNCTION
ORIGINAL_HISTORICAL_TEST_SHA256 = (
    "513bcbe2103f30974cb73ed37a8c499d090178fe2e3c4f6f8d97c34f0255c1f2"
)


@pytest.fixture()
def workflow():
    specification = importlib.util.spec_from_file_location(
        "b08_historical_deferral_test_target", SUPPORT
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop(specification.name, None)


def _real_pytest_child(
    workflow,
    tmp_path: Path,
    payload: str,
    *,
    duplicate_collection: bool = False,
):
    project_root = tmp_path / "source"
    path = project_root / HISTORICAL_FILE
    path.parent.mkdir(parents=True)
    path.write_text(payload, encoding="utf-8")
    config = tmp_path / "pytest.ini"
    config.write_text("[pytest]\n", encoding="utf-8")
    selection_report = tmp_path / "selection.json"
    junit_report = tmp_path / "report.xml"
    environment = dict(os.environ)
    for key in ("PYTHONPATH", "PYTEST_ADDOPTS", "FORCE_COLOR"):
        environment.pop(key, None)
    environment.update({
        "PYTHONSAFEPATH": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "NO_COLOR": "1",
    })
    selectors = [HISTORICAL_FILE]
    if duplicate_collection:
        selectors.extend(("--keep-duplicates", HISTORICAL_FILE))
    command = (
        sys.executable,
        "-c",
        workflow._pytest_entrypoint(False, (HISTORICAL_NODEID,)),
        str(project_root),
        str(selection_report),
        "-q",
        "--color=no",
        "--tb=short",
        "-p", "no:cacheprovider",
        "-c", str(config),
        "--rootdir", str(project_root),
        "--junitxml", str(junit_report),
        *selectors,
    )
    completed = subprocess.run(
        command,
        cwd=project_root,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    selection = (
        json.loads(selection_report.read_text("utf-8"))
        if selection_report.is_file() else None
    )
    return completed, selection, workflow._read_pytest_report(junit_report)


def test_historical_deferral_preserves_original_test_bytes(workflow) -> None:
    assert workflow.HISTORICAL_DEFERRED_NODEID == HISTORICAL_NODEID
    assert hashlib.sha256((ROOT / HISTORICAL_FILE).read_bytes()).hexdigest() == (
        ORIGINAL_HISTORICAL_TEST_SHA256
    )


def test_exact_deferral_keeps_similarly_prefixed_sibling(workflow, tmp_path) -> None:
    completed, selection, summary = _real_pytest_child(
        workflow,
        tmp_path,
        f"def {HISTORICAL_FUNCTION}():\n"
        "    raise AssertionError('historical obligation must not execute')\n\n"
        f"def {HISTORICAL_FUNCTION}_current_model_sibling():\n"
        "    assert True\n",
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert selection["deferred_nodeids"] == [HISTORICAL_NODEID]
    assert selection["selected_nodeids"] == [
        HISTORICAL_NODEID + "_current_model_sibling"
    ]
    assert summary["passed"] == 1
    assert summary["failed"] == summary["errors"] == summary["skipped"] == 0


def test_missing_exact_deferred_node_stops_before_tests(workflow, tmp_path) -> None:
    completed, selection, summary = _real_pytest_child(
        workflow,
        tmp_path,
        f"def {HISTORICAL_FUNCTION}_similarly_prefixed_only():\n"
        "    raise AssertionError('collection guard must stop before execution')\n",
    )
    assert completed.returncode == pytest.ExitCode.USAGE_ERROR
    assert summary["passed"] == 0
    assert selection is None or selection["deferred_nodeids"] != [HISTORICAL_NODEID]


def test_duplicate_exact_deferred_node_stops_before_tests(workflow, tmp_path) -> None:
    completed, selection, summary = _real_pytest_child(
        workflow,
        tmp_path,
        f"def {HISTORICAL_FUNCTION}():\n"
        "    raise AssertionError('duplicate collection must not execute')\n\n"
        "def test_current_model():\n"
        "    raise AssertionError('collection guard must stop before execution')\n",
        duplicate_collection=True,
    )
    assert completed.returncode == pytest.ExitCode.USAGE_ERROR
    assert summary["passed"] == 0
    assert selection is None or selection["deferred_nodeids"] != [HISTORICAL_NODEID]


def test_unrelated_failure_still_fails_after_exact_deferral(workflow, tmp_path) -> None:
    completed, selection, summary = _real_pytest_child(
        workflow,
        tmp_path,
        f"def {HISTORICAL_FUNCTION}():\n"
        "    raise AssertionError('historical obligation must not execute')\n\n"
        "def test_current_model_failure():\n"
        "    raise AssertionError('unrelated model failure remains mandatory')\n",
    )
    assert completed.returncode == pytest.ExitCode.TESTS_FAILED
    assert selection["deferred_nodeids"] == [HISTORICAL_NODEID]
    assert selection["selected_nodeids"] == [
        HISTORICAL_FILE + "::test_current_model_failure"
    ]
    assert summary["failed"] == 1
    assert summary["passed"] == summary["errors"] == summary["skipped"] == 0


@pytest.mark.parametrize(
    "use_root_alias", (False, True), ids=("physical-root", "symlink-root-alias")
)
def test_deferral_does_not_leak_staged_source_into_installed_cohort(
    workflow, monkeypatch, tmp_path, use_root_alias
) -> None:
    if not hasattr(sys.flags, "safe_path"):
        pytest.skip("requires Python 3.11+ PYTHONSAFEPATH enforcement")
    project_root = tmp_path / "source"
    unit_root = project_root / "tests/unit"
    unit_root.mkdir(parents=True)
    for relative in workflow.TEST_PACKAGE_MARKERS:
        (project_root / relative).write_bytes((ROOT / relative).read_bytes())
    poison = project_root / "src/heterodiff"
    poison.mkdir(parents=True)
    (poison / "__init__.py").write_text(
        "raise RuntimeError('staged source must not be imported')\n",
        encoding="utf-8",
    )
    (project_root / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\npythonpath = ["src"]\n', encoding="utf-8"
    )
    (project_root / HISTORICAL_FILE).write_text(
        "from pathlib import Path\nimport importlib.util\nimport sys\n\n"
        f"def {HISTORICAL_FUNCTION}():\n"
        "    raise AssertionError('historical obligation must not execute')\n\n"
        "def test_installed_cohort_never_exposes_staged_source():\n"
        "    root = Path(__file__).resolve().parents[2]\n"
        "    assert sys.flags.safe_path is True\n"
        "    assert str(root / 'src') not in {str(Path(p).resolve()) for p in sys.path if p}\n"
        "    spec = importlib.util.find_spec('heterodiff')\n"
        "    if spec is not None and spec.origin is not None:\n"
        "        assert Path(spec.origin).resolve() != root / 'src/heterodiff/__init__.py'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONSAFEPATH", "1")
    monkeypatch.setenv("PYTHONPATH", str(project_root / "src"))
    monkeypatch.setenv("PYTEST_ADDOPTS", "--import-mode=importlib")
    monkeypatch.setattr(workflow, "TARGETED_TEST_FILES", (HISTORICAL_FILE,))
    monkeypatch.setattr(workflow, "TARGETED_PYTEST_SELECTORS", (HISTORICAL_FILE,))
    caller_root = project_root
    if use_root_alias:
        caller_root = tmp_path / "source-alias"
        caller_root.symlink_to(project_root, target_is_directory=True)
    result = workflow._run_targeted_tests(caller_root)
    assert result["passed"] == 1
    assert result["returncode"] == 0
    assert len(result["cohorts"]) == 1
    assert result["cohorts"][0]["name"] == "installed_wheel"
    selection = json.loads(
        Path(result["cohorts"][0]["selection_report_path"]).read_text("utf-8")
    )
    assert selection["deferred_nodeids"] == [HISTORICAL_NODEID]
    assert selection["selected_nodeids"] == [
        HISTORICAL_FILE + "::test_installed_cohort_never_exposes_staged_source"
    ]



def test_generated_success_receipt_keeps_historical_obligation_open(
    workflow, monkeypatch, tmp_path
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    staging_root = tmp_path / "staging"
    (staging_root / "source").mkdir(parents=True)
    source_manifest = {
        "relative_path": workflow.SOURCE_MANIFEST_RELATIVE_PATH,
        "file_sha256": "a" * 64,
        "record_sha256": "b" * 64,
        "file_count": 1,
        "total_size_bytes": 1,
    }
    anchor = {"record_sha256": "c" * 64}
    preflight = {
        "source_manifest": source_manifest,
        "controller_anchor": anchor,
        "lock_versions": {},
        "lock_sha256": "d" * 64,
        "environment": {"exact": True},
    }
    marker = {
        "staging_root": str(staging_root),
        "project_wheel_name": "heterodiff-0.1.0-py3-none-any.whl",
        "project_wheel_sha256": "e" * 64,
        "python_prefix_observations": [{"prefix": sys.prefix}],
    }
    # Isolate receipt assembly from runtime and tensor work. The actual receipt
    # construction and serialization run unchanged, with no Databricks access.
    monkeypatch.setattr(
        workflow, "_verify_source_snapshot",
        lambda *args: {"verification_sha256": "f" * 64},
    )
    monkeypatch.setattr(workflow, "_installed_environment", lambda *args: {})
    monkeypatch.setattr(workflow, "_configure_and_verify_cpu_runtime", lambda: {})
    monkeypatch.setattr(
        workflow, "_run_targeted_tests",
        lambda *args: {
            "passed": 2, "deselected_count": 1,
            "open_deferred_obligations": workflow._historical_deferred_obligations(),
            "full_historical_suite_passed": False,
        },
    )
    monkeypatch.setattr(
        workflow, "_run_synthetic_smoke",
        lambda *args: {"formal_test_states": ["OPEN", "OPEN", "PENDING"]},
    )
    monkeypatch.setattr(workflow, "_load_controller_anchor", lambda *args: anchor)
    monkeypatch.setattr(workflow, "_load_source_manifest", lambda *args: source_manifest)
    monkeypatch.setattr(workflow, "_runtime_manifest", lambda *args: {})
    monkeypatch.setattr(workflow, "DURABLE_OUTPUT_DIRECTORY", tmp_path)

    receipt = workflow._verify_and_integrate(project_root, preflight, marker)

    assert receipt["decision"] == "PASS_CURRENT_SCOPE_WITH_DEFERRED_HISTORICAL_CHECK"
    assert receipt["current_scope_passed"] is True
    assert receipt["full_historical_suite_passed"] is False
    assert len(receipt["open_deferred_obligations"]) == 1
    obligation = receipt["open_deferred_obligations"][0]
    assert obligation["test_nodeid"] == HISTORICAL_NODEID
    assert obligation["state"] == "OPEN_DEFERRED"
    assert obligation["passed"] is obligation["closed"] is False
    assert obligation["test_or_expected_hash_modified"] is False
    assert "HISTORICAL_CHECKPOINT14_COMPATIBILITY" in receipt["not_proven_by_this_run"]
    assert "FULL_HISTORICAL_TEST_SUITE_PASS" in receipt["not_proven_by_this_run"]
    assert receipt["project_delta"]["b08_closed"] is False
    assert receipt["project_delta"]["timetable_or_ledger_edited"] is False
    assert all(
        receipt["project_delta"][name] == 0
        for name in ("fields_closed", "blockers_closed", "formal_tests_closed", "result_slots_filled")
    )
    assert receipt["safety"]["training_executed"] is False
    assert receipt["safety"]["study_or_test_data_accessed"] is False
    saved = json.loads(Path(receipt["durable_receipt_path"]).read_text("utf-8"))
    assert saved == receipt
