from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = (
    ROOT / "databricks" / "notebooks" / "b08_conventional_runtime_integration.py"
)


@pytest.fixture(scope="module")
def workflow():
    specification = importlib.util.spec_from_file_location(
        "b08_conventional_runtime_integration_test_target", NOTEBOOK
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def test_notebook_is_gitless_two_pass_data_free_route(workflow) -> None:
    source = NOTEBOOK.read_text(encoding="utf-8")
    assert source.startswith("# Databricks notebook source\n")
    assert "dbutils" in source
    assert "restartPython" in source
    assert "--require-hashes" in source
    assert "--no-build-isolation" in source
    assert "run_nonconfirmatory_test28_30_route_v2" in source
    assert "_stage_source_snapshot" in source
    assert "runtime_manifest_sha256" in source
    assert '"git"' not in source.lower()
    assert "git_state" not in source.lower()
    assert "project_revision" not in source
    assert "/local_disk0/heterodiff-b08" not in source
    assert "b08_n1_uc_native_overlay_lock_candidate" not in source
    assert "b08_n1_candidate_003_flat_namespace_forensics" not in source
    assert '"selected_route"' not in source
    assert '"gpu_enabled": False' not in source
    assert workflow.DURABLE_OUTPUT_DIRECTORY == Path(
        "/Volumes/development/team_eds_supplychain/b08_runtime_output"
    )


def test_exact_lock_manifest_and_targeted_test_roster_are_present(
    workflow,
) -> None:
    controller_anchor = workflow._load_controller_anchor(ROOT)
    assert controller_anchor["file_sha256"] == (
        "6fe5be57c560a32933e12515edfde53db7e409ccc963d5b0794b799c06a63a2a"
    )
    assert controller_anchor["record_sha256"] == (
        "18eed8c81d786270f0538fdf592a4b505df36299bcc1e48d40389c46046414dc"
    )
    assert controller_anchor["controller"]["sha256"] == workflow._sha256_file(
        NOTEBOOK
    )
    assert controller_anchor["controller"]["size_bytes"] == NOTEBOOK.stat().st_size

    lock = ROOT / workflow.LOCK_RELATIVE_PATH
    assert workflow._sha256_file(lock) == workflow.EXPECTED_LOCK_SHA256
    versions = workflow._lock_versions(lock)
    assert len(versions) == 21
    assert versions["numpy"] == "2.4.6"
    assert versions["scipy"] == "1.17.1"
    assert versions["threadpoolctl"] == "3.6.0"
    assert versions["torch"] == "2.12.1+cpu"
    assert versions["pytest"] == "9.1.1"
    assert versions["packaging"] == "25.0"
    assert all(
        (ROOT / relative).is_file() for relative in workflow.TARGETED_TEST_FILES
    )
    assert len(workflow.TARGETED_TEST_FILES) == 7
    assert len(workflow.WHOLE_METHOD_RUNTIME_NEUTRAL_TEST_NAMES) == 17
    assert len(workflow.WHOLE_METHOD_HISTORICAL_VALIDATOR_TEST_NAMES) == 8
    assert len(workflow.TARGETED_PYTEST_SELECTORS) == 23
    assert workflow.WHOLE_METHOD_TEST_FILE not in workflow.TARGETED_PYTEST_SELECTORS
    assert all(
        selector.startswith(workflow.WHOLE_METHOD_TEST_FILE + "::")
        for selector in workflow.TARGETED_PYTEST_SELECTORS[6:]
    )
    assert not any(
        name in selector
        for name in workflow.WHOLE_METHOD_HISTORICAL_VALIDATOR_TEST_NAMES
        for selector in workflow.TARGETED_PYTEST_SELECTORS
    )

    source_manifest = workflow._load_source_manifest(ROOT)
    assert source_manifest["file_sha256"] == (
        workflow.EXPECTED_SOURCE_MANIFEST_FILE_SHA256
    )
    assert source_manifest["record_sha256"] == (
        "59d2814a79f3dd79e3fd5d352897eeaea1d35cca5c7e3ce36b5b5ce22f269e60"
    )
    assert source_manifest["file_count"] == 321
    assert source_manifest["total_size_bytes"] == 26369620
    verification = workflow._verify_source_snapshot(ROOT, source_manifest)
    assert verification["file_count"] == 321


def _write_bound_manifest(workflow, root: Path) -> dict:
    selected_payloads = {
        "README.md": b"# bounded source fixture\n",
        "pyproject.toml": b"[project]\nname='heterodiff'\n",
        "src/heterodiff/__init__.py": b"__version__ = '0.1.0'\n",
        **{
            relative: (f"# {relative}\n").encode("ascii")
            for relative in workflow.TARGETED_TEST_FILES
        },
    }
    records = []
    for relative, payload in sorted(selected_payloads.items()):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        records.append(
            {
                "relative_path": relative,
                "sha256": workflow._sha256_bytes(payload),
                "size_bytes": len(payload),
                "mode_octal": "0644",
            }
        )
    unsigned = {
        "schema_version": workflow.SOURCE_MANIFEST_SCHEMA_VERSION,
        "selection": {"fixture": "BOUNDED_SELECTED_FILES_ONLY"},
        "files": records,
        "file_count": len(records),
        "total_size_bytes": sum(record["size_bytes"] for record in records),
    }
    manifest = {
        **unsigned,
        "record_sha256": workflow._source_manifest_record_sha256(unsigned),
    }
    manifest_path = root / workflow.SOURCE_MANIFEST_RELATIVE_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    raw = workflow._canonical_json_bytes(manifest) + b"\n"
    manifest_path.write_bytes(raw)
    return {
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_file_sha256": workflow._sha256_bytes(raw),
    }


def test_project_root_override_is_bounded_to_expected_markers(
    workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    candidate = tmp_path / "repo"
    (candidate / "src" / "heterodiff").mkdir(parents=True)
    lock = candidate / workflow.LOCK_RELATIVE_PATH
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("# placeholder\n", encoding="utf-8")
    (candidate / workflow.SOURCE_MANIFEST_RELATIVE_PATH).write_text(
        "{}\n", encoding="ascii"
    )
    (candidate / workflow.CONTROLLER_ANCHOR_RELATIVE_PATH).write_text(
        "{}\n", encoding="ascii"
    )
    (candidate / "pyproject.toml").write_text(
        "[project]\nname='heterodiff'\n", encoding="utf-8"
    )
    monkeypatch.setenv("HETERODIFF_PROJECT_ROOT", str(candidate))
    monkeypatch.chdir(tmp_path)
    assert workflow._find_project_root() == candidate.resolve()


def test_manifest_validation_and_staging_are_content_addressed_and_bounded(
    workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    live = tmp_path / "live"
    fixture = _write_bound_manifest(workflow, live)
    unselected = live / "not-selected.txt"
    unselected.write_text("must not be staged\n", encoding="utf-8")
    monkeypatch.setattr(
        workflow,
        "EXPECTED_SOURCE_MANIFEST_FILE_SHA256",
        fixture["manifest_file_sha256"],
    )
    source_manifest = workflow._load_source_manifest(live)
    staging = tmp_path / "staging"
    staging.mkdir()
    staged = workflow._stage_source_snapshot(live, source_manifest, staging)
    assert not (staged / "not-selected.txt").exists()
    assert workflow._verify_source_snapshot(
        live, source_manifest
    )["verification_sha256"] == workflow._verify_source_snapshot(
        staged, source_manifest
    )["verification_sha256"]

    (live / "README.md").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(
        workflow.B08ConventionalRuntimeError,
        match="SOURCE_SNAPSHOT_FILE_BINDING_MISMATCH",
    ):
        workflow._verify_source_snapshot(live, source_manifest)


def _marker_fixture(workflow, tmp_path: Path) -> tuple[Path, dict]:
    staging = tmp_path / "stage"
    wheel_root = staging / "wheel"
    source_root = staging / "source"
    wheel_root.mkdir(parents=True)
    source_root.mkdir(parents=True)
    wheel = wheel_root / "heterodiff-0.1.0-py3-none-any.whl"
    wheel.write_bytes(b"bounded-wheel-fixture")
    payload = b"bounded staged payload\n"
    (source_root / "payload.py").write_bytes(payload)
    source_manifest = {
        "manifest": {
            "files": [
                {
                    "relative_path": "payload.py",
                    "sha256": workflow._sha256_bytes(payload),
                    "size_bytes": len(payload),
                    "mode_octal": "0644",
                }
            ]
        },
        "relative_path": workflow.SOURCE_MANIFEST_RELATIVE_PATH,
        "file_sha256": "d" * 64,
        "record_sha256": "c" * 64,
    }
    controller_anchor = {
        "relative_path": workflow.CONTROLLER_ANCHOR_RELATIVE_PATH,
        "file_sha256": "a" * 64,
        "record_sha256": "b" * 64,
        "controller": {
            "relative_path": workflow.CONTROLLER_RELATIVE_PATH,
            "sha256": "e" * 64,
            "size_bytes": 123,
        },
    }
    preflight = {
        "controller_anchor": controller_anchor,
        "lock_sha256": workflow.EXPECTED_LOCK_SHA256,
        "source_manifest": source_manifest,
    }
    marker = {
        "schema_version": workflow.SCHEMA_VERSION,
        "state": "INSTALL_COMPLETE_RESTART_REQUIRED",
        "controller_anchor": controller_anchor,
        "source_manifest_relative_path": source_manifest["relative_path"],
        "source_manifest_file_sha256": source_manifest["file_sha256"],
        "source_manifest_record_sha256": source_manifest["record_sha256"],
        "lock_sha256": preflight["lock_sha256"],
        "project_wheel_name": wheel.name,
        "project_wheel_sha256": workflow._sha256_file(wheel),
        "python_prefix": sys.prefix,
        "pre_restart_pid": os.getpid() + 1,
        "staging_root": str(staging),
    }
    path = tmp_path / "marker.json"
    path.write_bytes(workflow._canonical_json_bytes(marker) + b"\n")
    return path, preflight


def test_controller_anchor_rejects_controller_byte_drift(
    workflow, tmp_path: Path
) -> None:
    controller_path = tmp_path / workflow.CONTROLLER_RELATIVE_PATH
    controller_path.parent.mkdir(parents=True)
    controller_path.write_bytes(b"# reviewed controller\n")
    unsigned = {
        "schema_version": workflow.CONTROLLER_ANCHOR_SCHEMA_VERSION,
        "identity_scope": "EXACT_CONTROLLER_BYTES",
        "controller": {
            "relative_path": workflow.CONTROLLER_RELATIVE_PATH,
            "sha256": workflow._sha256_file(controller_path),
            "size_bytes": controller_path.stat().st_size,
        },
    }
    anchor = {
        **unsigned,
        "record_sha256": workflow._controller_anchor_record_sha256(unsigned),
    }
    anchor_path = tmp_path / workflow.CONTROLLER_ANCHOR_RELATIVE_PATH
    anchor_path.parent.mkdir(parents=True, exist_ok=True)
    anchor_path.write_bytes(workflow._canonical_json_bytes(anchor) + b"\n")
    assert workflow._load_controller_anchor(tmp_path)["controller"] == anchor[
        "controller"
    ]

    controller_path.write_bytes(b"# changed controller!\n")
    with pytest.raises(
        workflow.B08ConventionalRuntimeError,
        match="CONTROLLER_ANCHOR_CONTROLLER_BINDING_MISMATCH",
    ):
        workflow._load_controller_anchor(tmp_path)


def test_restart_marker_binds_manifest_lock_wheel_prefix_and_new_pid(
    workflow, tmp_path: Path
) -> None:
    path, preflight = _marker_fixture(workflow, tmp_path)
    marker = workflow._validated_marker(path, preflight)
    assert marker["source_manifest_record_sha256"] == "c" * 64

    same_pid = json.loads(path.read_text(encoding="utf-8"))
    same_pid["pre_restart_pid"] = os.getpid()
    path.write_bytes(workflow._canonical_json_bytes(same_pid) + b"\n")
    with pytest.raises(
        workflow.B08ConventionalRuntimeError, match="PYTHON_WAS_NOT_RESTARTED"
    ):
        workflow._validated_marker(path, preflight)


def test_all_locked_distribution_roots_must_be_under_active_prefix(
    workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prefix = tmp_path / "python-prefix"
    distribution_root = prefix / "lib" / "python3.12" / "site-packages"
    distribution_root.mkdir(parents=True)
    module_file = distribution_root / "module.py"
    module_file.write_text("# origin\n", encoding="utf-8")
    versions = {f"package-{ordinal}": "1.0" for ordinal in range(21)}

    class FakeDistribution:
        version = "1.0"

        @staticmethod
        def locate_file(relative: str) -> Path:
            assert relative == ""
            return distribution_root

    monkeypatch.setattr(workflow.sys, "prefix", str(prefix))
    monkeypatch.setattr(
        workflow.importlib.metadata,
        "distribution",
        lambda name: FakeDistribution(),
    )
    monkeypatch.setattr(
        workflow.importlib.metadata,
        "version",
        lambda name: "0.1.0" if name == "heterodiff" else "1.0",
    )
    monkeypatch.setattr(
        workflow.importlib.util,
        "find_spec",
        lambda name: SimpleNamespace(origin=str(module_file)),
    )
    monkeypatch.setattr(
        workflow,
        "_run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout="No broken requirements found.\n", stderr=""
        ),
    )
    observed = workflow._installed_environment(tmp_path, versions)
    assert observed["lock_pin_count"] == 21
    assert len(observed["locked_distribution_roots"]) == 21
    assert observed[
        "all_locked_distributions_under_active_python_prefix"
    ] is True
    assert all(
        item["under_active_python_prefix"] is True
        for item in observed["locked_distribution_roots"].values()
    )


def test_final_receipt_file_and_printable_object_are_identical(
    workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(workflow, "DURABLE_OUTPUT_DIRECTORY", tmp_path)
    receipt = {
        "schema_version": workflow.SCHEMA_VERSION,
        "decision": "PASS_CONVENTIONAL_RUNTIME_AND_SYNTHETIC_INTEGRATION",
        "project": {"source_manifest_record_sha256": "b" * 64},
        "safety": {"study_or_test_data_accessed": False},
    }
    completed, path = workflow._write_final_receipt(receipt)
    assert path.is_file()
    assert completed == json.loads(path.read_text(encoding="utf-8"))
    assert completed["durable_write_verified"] is True
    assert ("b08-conventional-runtime-integration-" + "b" * 12) in path.name
    unsigned = {
        key: value
        for key, value in completed.items()
        if key not in {"record_sha256", "durable_receipt_path"}
    }
    assert (
        workflow._sha256_bytes(workflow._canonical_json_bytes(unsigned))
        == completed["record_sha256"]
    )


def test_expected_synthetic_receipts_are_recursive_values(workflow) -> None:
    value = {
        "route": workflow.EXPECTED_ROUTE_RECEIPT_SHA256,
        "nested": [{"receipt": workflow.EXPECTED_WHOLE_METHOD_RECEIPT_SHA256}],
    }
    assert workflow._contains_string(
        value, workflow.EXPECTED_ROUTE_RECEIPT_SHA256
    )
    assert workflow._contains_string(
        value, workflow.EXPECTED_WHOLE_METHOD_RECEIPT_SHA256
    )
    assert not workflow._contains_string(value, "0" * 64)
