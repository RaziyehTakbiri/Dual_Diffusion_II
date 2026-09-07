from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "databricks/notebooks/b08_conventional_restart_diagnostics.py"


@pytest.fixture
def diagnostic():
    spec = importlib.util.spec_from_file_location("b08_restart_diagnostic_test", NOTEBOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture(diagnostic, tmp_path):
    root = tmp_path / "project"
    def write_json(relative, value):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        path.write_bytes(raw)
        return raw
    anchor = {
        "record_sha256": "a" * 64,
        "identity_scope": "CONTROLLER_BYTES_IGNORING_ONE_OPTIONAL_TERMINAL_LF",
        "controller": {"sha256": "b" * 64, "size_bytes": 5, "relative_path": "controller.py"},
    }
    anchor_raw = write_json(diagnostic._B08_DIAG_ANCHOR_PATH, anchor)
    manifest_raw = write_json(diagnostic._B08_DIAG_MANIFEST_PATH, {"record_sha256": "c" * 64})
    lock = b"numpy==2.4.6 \\\n    --hash=sha256:example\n"
    (root / diagnostic._B08_DIAG_LOCK_PATH).write_bytes(lock)
    marker = {
        "schema_version": diagnostic._B08_DIAG_CONTROLLER_SCHEMA,
        "state": "INSTALL_COMPLETE_RESTART_REQUIRED",
        "controller_anchor": {
            "relative_path": diagnostic._B08_DIAG_ANCHOR_PATH,
            "file_sha256": diagnostic._b08_diag_sha(anchor_raw),
            "record_sha256": anchor["record_sha256"],
            "identity_scope": anchor["identity_scope"],
            "controller": anchor["controller"],
        },
        "source_manifest_relative_path": diagnostic._B08_DIAG_MANIFEST_PATH,
        "source_manifest_file_sha256": diagnostic._b08_diag_sha(manifest_raw),
        "source_manifest_record_sha256": "c" * 64,
        "lock_sha256": diagnostic._b08_diag_sha(lock),
        "python_prefix": sys.prefix,
        "pre_restart_pid": 123456,
        "project_wheel_sha256": "d" * 64,
    }
    marker_path = tmp_path / "marker.json"
    marker_path.write_text(json.dumps(marker))
    return root, marker_path, marker


def _fake_packages(monkeypatch, diagnostic):
    def distribution(name):
        return SimpleNamespace(
            version="2.4.6" if name == "numpy" else "0.1.0",
            locate_file=lambda relative: Path(sys.prefix) / "lib/site-packages",
        )
    monkeypatch.setattr(diagnostic.importlib.metadata, "distribution", distribution)


@pytest.mark.parametrize("field", [
    "schema_version", "state", "source_manifest_relative_path",
    "source_manifest_file_sha256", "source_manifest_record_sha256",
    "lock_sha256", "python_prefix",
])
def test_reports_the_specific_binding_difference(diagnostic, monkeypatch, tmp_path, field):
    root, path, marker = _fixture(diagnostic, tmp_path)
    marker[field] = "different"
    path.write_text(json.dumps(marker))
    _fake_packages(monkeypatch, diagnostic)
    before = path.read_bytes()
    report = diagnostic._b08_restart_diagnostic_report(root, path)
    assert report["mismatched_fields"] == [field]
    assert report["mismatches"][field]["stored"] == "different"
    assert path.read_bytes() == before


def test_reports_nested_controller_difference(diagnostic, monkeypatch, tmp_path):
    root, path, marker = _fixture(diagnostic, tmp_path)
    marker["controller_anchor"]["controller"]["sha256"] = "e" * 64
    path.write_text(json.dumps(marker))
    _fake_packages(monkeypatch, diagnostic)
    report = diagnostic._b08_restart_diagnostic_report(root, path)
    assert report["mismatched_fields"] == ["controller_anchor.controller.sha256"]


def test_reports_missing_anchor_key_and_present_extra_key(diagnostic):
    differences = diagnostic._b08_diag_differences(
        {"controller_anchor": {"old": "x"}},
        {"controller_anchor": {"identity_scope": "y"}},
    )
    assert differences["controller_anchor.old"]["current_field_absent"]
    assert differences["controller_anchor.identity_scope"]["stored_field_absent"]


def test_same_session_entrypoint_is_read_only(diagnostic, monkeypatch, tmp_path, capsys):
    root, marker_path, _ = _fixture(diagnostic, tmp_path)
    _fake_packages(monkeypatch, diagnostic)
    monkeypatch.chdir(root)
    monkeypatch.setattr(diagnostic, "_B08_DIAG_MARKER_PATH", marker_path)
    before = {str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    diagnostic.run_b08_restart_diagnostics()
    report = json.loads(capsys.readouterr().out)
    assert report["decision"] == "NO_BINDING_DIFFERENCE_IN_THIS_SESSION"
    assert report["python_session"]["prefix"] == sys.prefix
    assert report["installed_packages"]["missing"] == []
    assert report["installed_packages"]["version_mismatches"] == {}
    assert not report["continuation_authorized_by_this_report"]
    after = {str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert before == after


def test_missing_marker_prints_read_error(diagnostic, monkeypatch, tmp_path, capsys):
    root, _, _ = _fixture(diagnostic, tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setattr(diagnostic, "_B08_DIAG_MARKER_PATH", tmp_path / "absent.json")
    diagnostic.run_b08_restart_diagnostics()
    report = json.loads(capsys.readouterr().out)
    assert report["decision"] == "RESTART_DIAGNOSTIC_READ_FAILED"
    assert report["error_type"] == "FileNotFoundError"
    assert not report["files_written"]
