from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = (
    ROOT / "databricks" / "notebooks" / "b08_conventional_runtime_integration.py"
)
SUPPORT = (
    ROOT / "databricks" / "notebooks" / "b08_conventional_runtime_support.py"
)


@pytest.fixture()
def workflow():
    specification = importlib.util.spec_from_file_location(
        "b08_databricks_managed_flow_test_target", SUPPORT
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


def _managed_fixture(workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    project_root = tmp_path / "project"
    selected_payloads = {
        "pyproject.toml": b"[project]\nname='heterodiff'\nversion='0.1.0'\n",
        "src/heterodiff/__init__.py": b"__version__ = '0.1.0'\n",
    }
    records = []
    for relative, payload in sorted(selected_payloads.items()):
        path = project_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        records.append(
            {
                "relative_path": relative,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
                "mode_octal": "0644",
            }
        )

    lock_path = project_root / workflow.LOCK_RELATIVE_PATH
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_payload = b"# bounded managed-flow lock fixture\n"
    lock_path.write_bytes(lock_payload)
    lock_versions = workflow._lock_versions(ROOT / workflow.LOCK_RELATIVE_PATH)
    source_manifest = {
        "manifest": {"files": records},
        "relative_path": workflow.SOURCE_MANIFEST_RELATIVE_PATH,
        "file_sha256": "a" * 64,
        "record_sha256": "b" * 64,
        "file_count": len(records),
        "total_size_bytes": sum(record["size_bytes"] for record in records),
    }
    preflight = {
        "controller_anchor": {"record_sha256": "c" * 64},
        "lock_sha256": hashlib.sha256(lock_payload).hexdigest(),
        "lock_versions": lock_versions,
        "source_manifest": source_manifest,
    }

    managed_root = tmp_path / "managed"
    staging_root = tmp_path / "staging"
    runtime = {"pid": 101, "prefix": str(tmp_path / "python-1")}
    installed_versions: dict[str, str] = {}
    project_install = {"present": False}

    monkeypatch.setattr(workflow, "MANAGED_RUNTIME_ROOT", managed_root)
    monkeypatch.setattr(workflow, "_find_project_root", lambda: project_root)
    monkeypatch.setattr(workflow, "_runtime_preflight", lambda root: preflight)

    def make_staging_root(*, prefix, dir):
        staging_root.mkdir()
        return str(staging_root)

    monkeypatch.setattr(
        workflow.tempfile,
        "mkdtemp",
        make_staging_root,
    )
    monkeypatch.setattr(workflow.os, "getpid", lambda: runtime["pid"])
    monkeypatch.setattr(workflow.sys, "prefix", runtime["prefix"])

    def installed_version(name: str) -> str:
        try:
            return installed_versions[name]
        except KeyError as error:
            raise workflow.importlib.metadata.PackageNotFoundError(name) from error

    monkeypatch.setattr(workflow.importlib.metadata, "version", installed_version)
    return SimpleNamespace(
        project_root=project_root,
        preflight=preflight,
        managed_root=managed_root,
        staging_root=staging_root,
        runtime=runtime,
        installed_versions=installed_versions,
        project_install=project_install,
    )


def _context(fixture) -> dict:
    return json.loads((fixture.managed_root / "context.json").read_text("ascii"))


def test_controller_has_seven_managed_cells_and_literal_percent_pip_boundaries() -> None:
    cells = CONTROLLER.read_text(encoding="utf-8").split("# COMMAND ----------")
    assert len(cells) == 7
    assert cells[1].strip() == (
        "# MAGIC %pip install --upgrade --force-reinstall --only-binary=:all: "
        "--require-hashes -r "
        "/tmp/heterodiff-b08-managed-current/dependencies.lock"
    )
    assert cells[4].strip() == (
        "# MAGIC %pip install --force-reinstall --no-deps "
        "/tmp/heterodiff-b08-managed-current/heterodiff-0.1.0-py3-none-any.whl"
    )

    action_cells = {
        0: "prepare",
        2: "dependencies_restart",
        3: "build",
        5: "project_restart",
        6: "verify",
    }
    for ordinal, action in action_cells.items():
        cell = cells[ordinal]
        assert f'b08_runtime.managed_action("{action}")' in cell
        assert "exec(compile(_b08_support_bytes" in cell
        assert "B08_SUPPORT_SOURCE_MISMATCH_PULL_THE_COMPLETE_UPDATE" in cell

    for ordinal in (2, 5):
        lines = [line.strip() for line in cells[ordinal].splitlines() if line.strip()]
        assert lines[-1] == "dbutils.library.restartPython()"
        assert cells[ordinal].count("restartPython()") == 1
    assert all(
        "restartPython()" not in cells[ordinal]
        for ordinal in (0, 1, 3, 4, 6)
    )


def test_controller_bootstrap_reloads_only_hash_bound_support_in_fresh_namespaces(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cells = CONTROLLER.read_text(encoding="utf-8").split("# COMMAND ----------")
    fake_root = tmp_path / "pulled-project"
    support_path = (
        fake_root
        / "databricks"
        / "notebooks"
        / "b08_conventional_runtime_support.py"
    )
    support_path.parent.mkdir(parents=True)
    support_payload = (
        b"ACTIONS = []\n"
        b"def managed_action(action):\n"
        b"    ACTIONS.append(action)\n"
        b"    return {'action': action}\n"
    )
    support_path.write_bytes(support_payload)
    anchor_path = (
        fake_root
        / "requirements"
        / "b08-conventional-runtime-controller-anchor-v1.json"
    )
    anchor_path.parent.mkdir(parents=True)
    anchor_path.write_text(
        json.dumps(
            {
                "support_module": {
                    "sha256": hashlib.sha256(support_payload).hexdigest(),
                    "size_bytes": len(support_payload),
                }
            }
        ),
        encoding="ascii",
    )
    monkeypatch.chdir(fake_root)

    expected_actions = {
        0: "prepare",
        2: "dependencies_restart",
        3: "build",
        5: "project_restart",
        6: "verify",
    }
    for ordinal, action in expected_actions.items():
        restarts = []
        namespace = {
            "__name__": f"managed_cell_{ordinal}",
            "dbutils": SimpleNamespace(
                library=SimpleNamespace(restartPython=lambda: restarts.append(True))
            ),
        }
        sys.modules.pop("b08_managed_runtime", None)
        exec(compile(cells[ordinal], f"<managed-cell-{ordinal}>", "exec"), namespace)
        assert namespace["b08_runtime"].ACTIONS == [action]
        assert restarts == ([True] if ordinal in {2, 5} else [])

    support_path.write_bytes(support_payload + b"# drift\n")
    sys.modules.pop("b08_managed_runtime", None)
    with pytest.raises(
        RuntimeError, match="B08_SUPPORT_SOURCE_MISMATCH_PULL_THE_COMPLETE_UPDATE"
    ):
        exec(compile(cells[0], "<managed-cell-drift>", "exec"), {})


def test_percent_pip_state_survives_both_prefix_rotations(
    workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixture = _managed_fixture(workflow, monkeypatch, tmp_path)
    commands: list[tuple[str, ...]] = []

    def build_only(argv, **kwargs):
        command = tuple(argv)
        commands.append(command)
        assert command[1:4] == ("-m", "pip", "wheel")
        assert "install" not in command
        wheel_root = Path(command[command.index("--wheel-dir") + 1])
        (wheel_root / workflow.MANAGED_WHEEL_NAME).write_bytes(
            b"bounded deterministic wheel"
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(workflow, "_run", build_only)

    assert workflow.managed_action("prepare")["phase"] == "PREPARED"
    # This assignment models the first literal %pip cell. Unlike the retired
    # subprocess-install route, the managed environment survives Python restart.
    fixture.installed_versions.update(fixture.preflight["lock_versions"])
    assert workflow.managed_action("dependencies_restart")["phase"] == (
        "DEPENDENCIES_INSTALLED"
    )

    fixture.runtime.update(pid=202, prefix=str(tmp_path / "python-2"))
    monkeypatch.setattr(workflow.sys, "prefix", fixture.runtime["prefix"])
    built = workflow.managed_action("build")
    assert built["decision"] == "READY_FOR_MANAGED_PROJECT_INSTALL"
    assert len(commands) == 1
    assert _context(fixture)["phase"] == "PROJECT_WHEEL_READY"

    # This assignment models the second literal %pip cell.
    fixture.project_install["present"] = True
    assert workflow.managed_action("project_restart")["phase"] == (
        "PROJECT_INSTALLED"
    )
    fixture.runtime.update(pid=303, prefix=str(tmp_path / "python-3"))
    monkeypatch.setattr(workflow.sys, "prefix", fixture.runtime["prefix"])

    captured = {}

    def verify_and_integrate(project_root, preflight, context):
        assert fixture.project_install["present"] is True
        captured.update(context)
        return {"decision": "PASS_BOUNDED_MANAGED_FLOW"}

    monkeypatch.setattr(workflow, "_verify_and_integrate", verify_and_integrate)
    assert workflow.managed_action("verify") == {
        "decision": "PASS_BOUNDED_MANAGED_FLOW"
    }
    assert captured["staging_root"] == str(fixture.staging_root)
    assert captured["project_wheel_name"] == workflow.MANAGED_WHEEL_NAME
    assert len(captured["project_wheel_sha256"]) == 64
    assert [item["prefix"] for item in captured["python_prefix_observations"]] == [
        str(tmp_path / "python-1"),
        str(tmp_path / "python-2"),
    ]


def test_process_local_dependency_install_is_rejected_before_wheel_build(
    workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixture = _managed_fixture(workflow, monkeypatch, tmp_path)
    build_called = False

    def should_not_build(*args, **kwargs):
        nonlocal build_called
        build_called = True
        raise AssertionError("wheel build must not start with missing dependencies")

    monkeypatch.setattr(workflow, "_run", should_not_build)
    workflow.managed_action("prepare")

    # Model packages installed into only the old process-local environment.
    fixture.installed_versions.update(fixture.preflight["lock_versions"])
    workflow.managed_action("dependencies_restart")
    fixture.runtime.update(pid=202, prefix=str(tmp_path / "python-2"))
    monkeypatch.setattr(workflow.sys, "prefix", fixture.runtime["prefix"])
    fixture.installed_versions.clear()

    with pytest.raises(
        workflow.B08ConventionalRuntimeError,
        match="MANAGED_DEPENDENCIES_NOT_AVAILABLE_AFTER_RESTART",
    ) as caught:
        workflow.managed_action("build")
    assert len(caught.value.diagnostics["packages"]) == 21
    assert build_called is False
    assert _context(fixture)["phase"] == "DEPENDENCIES_INSTALLED"


def test_each_restart_boundary_requires_a_new_pid_and_preserves_hashes(
    workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixture = _managed_fixture(workflow, monkeypatch, tmp_path)
    fixture.installed_versions.update(fixture.preflight["lock_versions"])
    workflow.managed_action("prepare")
    workflow.managed_action("dependencies_restart")

    with pytest.raises(
        workflow.B08ConventionalRuntimeError,
        match="MANAGED_PYTHON_RESTART_NOT_OBSERVED",
    ):
        workflow.managed_action("build")

    fixture.runtime.update(pid=202, prefix=str(tmp_path / "python-2"))
    monkeypatch.setattr(workflow.sys, "prefix", fixture.runtime["prefix"])

    def build_wheel(argv, **kwargs):
        command = tuple(argv)
        wheel_root = Path(command[command.index("--wheel-dir") + 1])
        (wheel_root / workflow.MANAGED_WHEEL_NAME).write_bytes(b"bound wheel")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(workflow, "_run", build_wheel)
    workflow.managed_action("build")
    workflow.managed_action("project_restart")

    with pytest.raises(
        workflow.B08ConventionalRuntimeError,
        match="MANAGED_PYTHON_RESTART_NOT_OBSERVED",
    ):
        workflow.managed_action("verify")

    context = _context(fixture)
    install_wheel = fixture.managed_root / workflow.MANAGED_WHEEL_NAME
    install_wheel.write_bytes(b"tampered wheel")
    fixture.runtime.update(pid=303, prefix=str(tmp_path / "python-3"))
    monkeypatch.setattr(workflow.sys, "prefix", fixture.runtime["prefix"])
    monkeypatch.setattr(
        workflow,
        "_verify_and_integrate",
        lambda *args: {"decision": "MUST_NOT_REACH_INTEGRATION"},
    )
    with pytest.raises(
        workflow.B08ConventionalRuntimeError,
        match="MANAGED_PROJECT_WHEEL_BINDING_MISMATCH",
    ):
        workflow.managed_action("verify")
    assert context["project_wheel_sha256"] != hashlib.sha256(
        install_wheel.read_bytes()
    ).hexdigest()
