from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SUPPORT = (
    ROOT / "databricks" / "notebooks" / "b08_conventional_runtime_support.py"
)


@pytest.fixture()
def workflow():
    specification = importlib.util.spec_from_file_location(
        "b08_test_cohort_test_target", SUPPORT
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


def _project_fixture(workflow, tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "staged-source"
    (project_root / "src").mkdir(parents=True)
    for relative in workflow.TARGETED_TEST_FILES:
        path = project_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# cohort test fixture\n", encoding="utf-8")
    report_root = tmp_path / "pytest-reports"
    report_root.mkdir()
    return project_root, report_root


def _junit_payload(
    *,
    passed: int = 0,
    failures: tuple[str, ...] = (),
    errors: tuple[str, ...] = (),
    skipped: int = 0,
) -> str:
    cases = [
        f'<testcase classname="cohort" name="pass-{ordinal}" />'
        for ordinal in range(passed)
    ]
    cases.extend(
        '<testcase classname="cohort" name="failure-%d">'
        '<failure message="%s">failure detail</failure></testcase>'
        % (ordinal, message)
        for ordinal, message in enumerate(failures)
    )
    cases.extend(
        '<testcase classname="cohort" name="error-%d">'
        '<error message="%s">error detail</error></testcase>'
        % (ordinal, message)
        for ordinal, message in enumerate(errors)
    )
    cases.extend(
        '<testcase classname="cohort" name="skip-%d">'
        '<skipped message="bounded skip" /></testcase>' % ordinal
        for ordinal in range(skipped)
    )
    return "<testsuites><testsuite>%s</testsuite></testsuites>" % "".join(cases)


def _report_path(argv: tuple[str, ...]) -> Path:
    index = argv.index("--junitxml")
    return Path(argv[index + 1])


def _write_selection(command, count, deferred=()):
    Path(command[4]).write_text(json.dumps({
        "selected_nodeids": [f"tests/unit/test_fixture.py::test_{i}" for i in range(count)],
        "deferred_nodeids": list(deferred),
    }), encoding="utf-8")


def test_targeted_tests_partition_source_and_installed_cohorts_exactly_once(
    workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project_root, report_root = _project_fixture(workflow, tmp_path)
    monkeypatch.setattr(
        workflow.tempfile,
        "mkdtemp",
        lambda *, prefix, dir: str(report_root),
    )
    monkeypatch.setenv("PYTHONPATH", "/poisoned/source")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--maxfail=1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    calls: list[dict[str, object]] = []

    def fake_run(argv, **kwargs):
        command = tuple(argv)
        calls.append({"argv": command, **kwargs})
        source_bound = "source_bound = True\n" in command[2]
        _write_selection(command, 2 if source_bound else 3,
                         () if source_bound else (workflow.HISTORICAL_DEFERRED_NODEID,))
        _report_path(command).write_text(
            _junit_payload(passed=2 if source_bound else 3),
            encoding="utf-8",
        )
        label = "source" if source_bound else "installed"
        return subprocess.CompletedProcess(
            command,
            0,
            f"\x1b[32m{label} stdout\x1b[0m\n",
            f"{label} stderr\n",
        )

    monkeypatch.setattr(workflow, "_run", fake_run)
    result = workflow._run_targeted_tests(project_root)

    assert result["returncode"] == 0
    assert result["passed"] == 5
    assert result["deselected_count"] == 1
    assert result["full_historical_suite_passed"] is False
    obligation, = result["open_deferred_obligations"]
    assert obligation["state"] == "OPEN_DEFERRED"
    assert obligation["passed"] is False and obligation["closed"] is False
    assert result["test_file_count"] == len(workflow.TARGETED_TEST_FILES)
    assert result["test_files"] == list(workflow.TARGETED_TEST_FILES)
    assert result["pytest_selector_count"] == len(
        workflow.TARGETED_PYTEST_SELECTORS
    )
    assert result["pytest_selectors"] == list(workflow.TARGETED_PYTEST_SELECTORS)

    cohorts = result["cohorts"]
    assert [cohort["name"] for cohort in cohorts] == [
        "source_bound_checkout",
        "installed_wheel",
    ]
    assert [cohort["scope"] for cohort in cohorts] == [
        "STAGED_SOURCE_CONTRACT_TESTS_NOT_INSTALLED_WHEEL",
        "INSTALLED_PACKAGE_TEST_PROCESS",
    ]
    assert [cohort["passed"] for cohort in cohorts] == [2, 3]
    assert all(
        cohort["report_available"]
        and cohort["failed"] == 0
        and cohort["errors"] == 0
        and cohort["skipped"] == 0
        and Path(cohort["log_path"]).is_file()
        for cohort in cohorts
    )

    selected = [
        selector for cohort in cohorts for selector in cohort["selectors"]
    ]
    assert Counter(selected) == Counter(workflow.TARGETED_PYTEST_SELECTORS)
    assert len(selected) == len(set(selected))
    assert cohorts[0]["selectors"] == list(workflow.SOURCE_BOUND_TEST_FILES)
    assert all(
        selector.split("::", 1)[0] not in workflow.SOURCE_BOUND_TEST_FILES
        for selector in cohorts[1]["selectors"]
    )

    assert len(calls) == 2
    source_call, installed_call = calls
    source_command = source_call["argv"]
    installed_command = installed_call["argv"]
    assert source_call["check"] is False and installed_call["check"] is False
    assert source_call["cwd"] == project_root
    assert installed_call["cwd"] == project_root

    assert source_command[:2] == (sys.executable, "-c")
    assert source_command[3] == str(project_root)
    assert "b12_integration_stack" in source_command[2]
    assert "b12_independent_component_recomputation" in source_command[2]
    assert "pytest.main" in source_command[2]
    assert installed_command[:2] == (sys.executable, "-c")
    assert "source_bound = False\n" in installed_command[2]
    assert "source_bound = True\n" in source_command[2]
    assert workflow.HISTORICAL_DEFERRED_NODEID in installed_command[2]
    assert workflow.HISTORICAL_DEFERRED_NODEID not in source_command[2]

    for call, cohort in zip(calls, cohorts):
        command = call["argv"]
        report_index = command.index("--junitxml")
        assert command[report_index + 2 :] == tuple(cohort["selectors"])
        assert "--color=no" in command
        assert command[command.index("--rootdir") + 1] == str(project_root)
        environment = call["environment"]
        assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
        assert environment["NO_COLOR"] == "1"
        assert environment["PYTHONSAFEPATH"] == "1"
        assert "PYTEST_ADDOPTS" not in environment
        assert "FORCE_COLOR" not in environment
    assert source_call["environment"]["PYTHONPATH"] == str(
        project_root / "src"
    )
    assert "PYTHONPATH" not in installed_call["environment"]

    assert "\x1b" not in Path(cohorts[0]["log_path"]).read_text("utf-8")
    assert "source stdout\nsource stderr" in Path(
        cohorts[0]["log_path"]
    ).read_text("utf-8")
    assert "\x1b" not in Path(cohorts[1]["log_path"]).read_text("utf-8")


def test_targeted_test_failure_keeps_structured_counts_and_complete_log(
    workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project_root, report_root = _project_fixture(workflow, tmp_path)
    monkeypatch.setattr(
        workflow.tempfile,
        "mkdtemp",
        lambda *, prefix, dir: str(report_root),
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(argv, **kwargs):
        command = tuple(argv)
        calls.append(command)
        if len(calls) == 1:
            _write_selection(command, 4)
            _report_path(command).write_text(
                _junit_payload(passed=4), encoding="utf-8"
            )
            return subprocess.CompletedProcess(command, 0, "source complete\n", "")

        _write_selection(command, 42, (workflow.HISTORICAL_DEFERRED_NODEID,))
        _report_path(command).write_text(
            _junit_payload(
                passed=1,
                failures=("independent failure",),
                errors=("shared fixture cause",) * 40,
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(
            command,
            1,
            "complete stdout first line\n",
            "\x1b[31mshared fixture cause\x1b[0m\ncomplete stderr last line\n",
        )

    monkeypatch.setattr(workflow, "_run", fake_run)
    with pytest.raises(
        workflow.B08ConventionalRuntimeError,
        match="TARGETED_INTEGRATION_TESTS_FAILED:installed_wheel",
    ) as caught:
        workflow._run_targeted_tests(project_root)

    diagnostics = caught.value.diagnostics
    assert diagnostics is not None
    assert [cohort["name"] for cohort in diagnostics["cohorts"]] == [
        "source_bound_checkout",
        "installed_wheel",
    ]
    failed = diagnostics["cohorts"][-1]
    assert failed["report_available"] is True
    assert (failed["passed"], failed["failed"], failed["errors"], failed["skipped"]) == (
        1,
        1,
        40,
        0,
    )
    assert len(failed["failures"]) == 32
    assert failed["failures"][0]["kind"] == "failed"
    assert all(item["kind"] == "errors" for item in failed["failures"][1:])
    assert sum(
        item["message"] == "shared fixture cause"
        for item in failed["failures"]
    ) == 31
    assert "shared fixture cause" in diagnostics["output_excerpt"]

    log_path = Path(failed["log_path"])
    assert log_path.is_file()
    assert log_path.read_text("utf-8") == (
        "complete stdout first line\n"
        "shared fixture cause\n"
        "complete stderr last line\n"
    )
    assert len(calls) == 2
