from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = (
    ROOT
    / "research/diagnostics/manuscript_v3_b02_physionet_public_documentation_gap_v1.py"
)


def load_validator():
    name = "_test_b02_physionet_public_documentation_gap_validator"
    spec = importlib.util.spec_from_file_location(name, VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def machine_record() -> dict:
    return validator.strict_loads((ROOT / validator.MACHINE_PATH).read_bytes())


def copy_package(destination: Path) -> Path:
    for relative in validator.FILE_BINDINGS:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    validator_target = destination / VALIDATOR_PATH.relative_to(ROOT)
    validator_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(VALIDATOR_PATH, validator_target)
    return destination


def rewrite_machine(root: Path, mutator) -> None:
    path = root / validator.MACHINE_PATH
    value = json.loads(path.read_text(encoding="utf-8"))
    mutator(value)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def test_canonical_package_passes() -> None:
    result = validator.validate_package(ROOT)
    assert result == {
        "status": "PASS",
        "schema_version": validator.SCHEMA,
        "record_sha256": validator.EXPECTED_RECORD_SHA256,
        "open_fields": ["F019", "F020", "F022", "F033", "F034", "F058"],
        "checklist_items": 12,
        "field_delta": 0,
        "blocker_delta": 0,
        "b02": "OPEN",
        "b09": "OPEN",
    }


def test_machine_semantic_self_digest_is_exact() -> None:
    value = machine_record()
    assert validator.semantic_sha256(value) == value["record_sha256"]
    assert value["record_sha256"] == validator.EXPECTED_RECORD_SHA256


def test_public_observation_is_documentation_only() -> None:
    value = machine_record()
    observation = value["public_documentation_observation"]
    assert observation["displayed_version"] == "1.0.0"
    assert observation["displayed_set_a_archive_byte_count"] == 6_632_372
    assert observation["observed_page_published_raw_archive_sha256"] is None
    assert observation["dataset_archive_downloaded"] is False
    assert observation["governance_approval_authenticated"] is False
    assert observation["field_closure_supported_by_this_observation"] == []


def test_all_six_real_field_receipts_remain_absent() -> None:
    rows = machine_record()["open_field_evidence_map"]
    assert [row["field_id"] for row in rows] == [
        "F019", "F020", "F022", "F033", "F034", "F058"
    ]
    assert all(row["currently_present"] is False for row in rows)
    assert all(row["public_documentation_alone_sufficient"] is False for row in rows)


def test_every_authority_and_receipt_step_is_required_and_unsatisfied() -> None:
    rows = machine_record()["exact_next_authority_and_receipt_checklist"]
    assert [row["ordinal"] for row in rows] == list(range(12))
    assert all(row["required_before_next"] is True for row in rows)
    assert all(row["currently_satisfied"] is False for row in rows)
    assert all(row["satisfied_by_this_package"] is False for row in rows)


def test_closure_projection_is_exact_zero() -> None:
    closure = machine_record()["closure_projection"]
    assert closure["field_ids_closed"] == []
    assert closure["field_count_delta"] == 0
    assert closure["blocker_ids_closed"] == []
    assert closure["blocker_count_delta"] == 0
    assert closure["operational_tasks_closed"] == []
    assert closure["timetable_checkbox_delta"] == 0
    assert closure["formal_test_delta"] == 0
    assert closure["result_slot_delta"] == 0
    assert closure["b02_status"] == closure["b09_status"] == "OPEN"
    assert closure["physionet_domain_admitted"] is False
    assert closure["wave3_physionet_complete"] is False


def test_strict_json_rejects_duplicate_key() -> None:
    with pytest.raises(validator.ValidationError, match="duplicate"):
        validator.strict_loads(b'{"schema_version":"a","schema_version":"b"}')


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value["scope"].__setitem__("dataset_bytes_downloaded", True),
        lambda value: value["public_documentation_observation"].__setitem__(
            "observed_page_published_raw_archive_sha256", "0" * 64
        ),
        lambda value: value["open_field_evidence_map"][0].__setitem__(
            "currently_present", True
        ),
        lambda value: value["exact_next_authority_and_receipt_checklist"][0].__setitem__(
            "currently_satisfied", True
        ),
        lambda value: value["closure_projection"].__setitem__("b02_status", "CLOSED"),
        lambda value: value["closure_projection"].__setitem__("field_count_delta", True),
    ],
)
def test_semantic_promotions_fail_closed(mutator) -> None:
    value = machine_record()
    mutator(value)
    with pytest.raises(validator.ValidationError):
        validator.validate_record(value)


def test_checklist_reordering_fails_closed() -> None:
    value = machine_record()
    rows = value["exact_next_authority_and_receipt_checklist"]
    rows[0], rows[1] = rows[1], rows[0]
    with pytest.raises(validator.ValidationError):
        validator.validate_record(value)


def test_open_field_requirement_weakening_fails_closed() -> None:
    value = machine_record()
    value["open_field_evidence_map"][1]["required_evidence"] = "A_HASH"
    with pytest.raises(validator.ValidationError):
        validator.validate_record(value)


def test_copied_package_passes_from_unrelated_working_directory(
    tmp_path: Path,
) -> None:
    copied = copy_package(tmp_path / "capsule")
    result = validator.validate_package(copied)
    assert result["status"] == "PASS"
    completed = subprocess.run(
        [
            sys.executable,
            str(copied / VALIDATOR_PATH.relative_to(ROOT)),
            "--root",
            str(copied),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["status"] == "PASS"


def test_copied_package_rejects_mutated_machine_bytes(tmp_path: Path) -> None:
    copied = copy_package(tmp_path / "capsule")
    rewrite_machine(
        copied,
        lambda value: value["closure_projection"].__setitem__("b02_status", "CLOSED"),
    )
    with pytest.raises(validator.ValidationError, match="bound file bytes changed"):
        validator.validate_package(copied)


def test_copied_package_rejects_mutated_preflight_source(tmp_path: Path) -> None:
    copied = copy_package(tmp_path / "capsule")
    source = copied / validator.SOURCE_PATH
    source.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(validator.ValidationError, match="bound file bytes changed"):
        validator.validate_package(copied)


def test_copied_package_rejects_missing_control_binding(tmp_path: Path) -> None:
    copied = copy_package(tmp_path / "capsule")
    path = copied / "research/fixtures/manuscript_v3_f061_guarded_power_review_receipt_v1.json"
    path.unlink()
    with pytest.raises(validator.ValidationError, match="bound file missing"):
        validator.validate_package(copied)


def test_fail_closed_preflight_api_cannot_self_admit() -> None:
    validator._validate_preflight_api(ROOT)


def test_validator_has_no_network_or_dataset_executor_import() -> None:
    source = VALIDATOR_PATH.read_text(encoding="utf-8")
    forbidden = (
        "import socket",
        "import urllib",
        "import requests",
        "import httpx",
        "import aiohttp",
        "subprocess.run(",
        "urlopen(",
        "wget ",
        "curl ",
    )
    assert not any(token in source for token in forbidden)
