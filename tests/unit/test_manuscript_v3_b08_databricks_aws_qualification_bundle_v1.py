from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (
    ROOT
    / "research/diagnostics/manuscript_v3_b08_databricks_aws_qualification_bundle_v1.py"
)
SPEC = importlib.util.spec_from_file_location("b08_databricks_bundle_validator", VALIDATOR)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def test_hash_first_bundle_validator_passes_with_zero_delta():
    result = validator.validate()
    assert result["decision"] == (
        "PASS_DATABRICKS_AWS_QUALIFICATION_BUNDLE_HOLD_NO_CLOSURE"
    )
    assert result["b08"] == "OPEN"
    assert result["calibration_authorized"] is False
    assert result["field_delta"] == 0
    assert result["blocker_delta"] == 0
    assert result["timetable_delta"] == 0
    assert result["marked_tasks"] == {"checked": 62, "open": 101, "total": 163}
    assert result["formal_tests"] == ["OPEN", "OPEN", "PENDING"]


def test_validator_loads_bound_core_bytes_without_project_import():
    tree = ast.parse(VALIDATOR.read_text(encoding="utf-8"))
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    imports.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert all(not name.startswith("heterodiff") for name in imports)
    assert "load_hash_first_core" in {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }


def test_validator_rejects_byte_correct_world_writable_candidate(tmp_path):
    copied_root = tmp_path / "project"
    copied_validator = copied_root / VALIDATOR.relative_to(ROOT)
    copied_validator.parent.mkdir(parents=True)
    shutil.copyfile(VALIDATOR, copied_validator)

    for relative_path in validator.EXPECTED:
        source = ROOT / relative_path
        destination = copied_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    for relative_path in ("PROJECT_COMPLETION_TIMETABLE.md", "PROJECT_EVIDENCE_LEDGER.md"):
        source = ROOT / relative_path
        destination = copied_root / relative_path
        shutil.copyfile(source, destination)

    exposed = copied_root / next(iter(validator.EXPECTED))
    exposed.chmod(0o666)

    copied_spec = importlib.util.spec_from_file_location(
        "copied_b08_databricks_bundle_validator", copied_validator
    )
    assert copied_spec is not None and copied_spec.loader is not None
    copied_module = importlib.util.module_from_spec(copied_spec)
    copied_spec.loader.exec_module(copied_module)
    with pytest.raises(copied_module.ValidationError, match="custody"):
        copied_module.validate()
