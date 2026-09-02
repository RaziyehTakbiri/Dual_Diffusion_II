"""Hostile tests for the final locked-route manuscript successor."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = (
    ROOT
    / "research"
    / "diagnostics"
    / "manuscript_v3_locked_route_successor_v1.py"
)


def _load_validator():
    specification = importlib.util.spec_from_file_location(
        "locked_route_successor_validator", VALIDATOR_PATH
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


validator = _load_validator()


def _copy_workspace_inputs(tmp_path: Path) -> Path:
    required = set(validator.SUCCESSOR_PATHS)
    required.update(path for path, _size, _digest in validator.HISTORICAL)
    required.update(path for path, *_rest in validator.SETTLED_INPUTS)
    required.update(path for path, *_rest in validator.B05_INPUTS)
    for relative in sorted(required):
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return tmp_path


def _rewrite_record(workspace: Path, mutator) -> None:
    path = workspace / validator.MACHINE_PATH
    record = json.loads(path.read_text(encoding="utf-8"))
    mutator(record)
    record["record_sha256"] = validator.record_sha256(record)
    path.write_text(
        json.dumps(record, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def test_live_final_validation_closes_only_manuscript_sync() -> None:
    receipt = validator.validate(ROOT)
    assert receipt["validation"] == "PASS"
    assert receipt["binding_status"] == validator.BINDING_STATUS
    assert receipt["target_predicate_id"] == validator.TARGET_PREDICATE
    assert receipt["target_predicate_value"] is True
    assert receipt["b05_control_predicate_value"] is True
    assert receipt["effective_pre_execution_open"] == 146
    assert receipt["effective_closed_field_count"] == 20
    assert receipt["B05_closed"] is False
    assert receipt["scientific_effect"] == 0
    assert receipt["tracker_effect"] == 0


def test_historical_predecessor_byte_change_fails_closed(tmp_path: Path) -> None:
    workspace = _copy_workspace_inputs(tmp_path)
    path = workspace / "manuscript_v3" / "manuscript_v3.md"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(validator.ValidationError, match="historical bytes changed"):
        validator.validate(workspace)


def test_settled_machine_input_byte_change_fails_closed(tmp_path: Path) -> None:
    workspace = _copy_workspace_inputs(tmp_path)
    path = (
        workspace
        / "research"
        / "fixtures"
        / "manuscript_v3_c17_po13_initializer_kl_proof_v1.json"
    )
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(validator.ValidationError, match="settled bytes changed"):
        validator.validate(workspace)


def test_b05_stopped_input_byte_change_fails_closed(tmp_path: Path) -> None:
    workspace = _copy_workspace_inputs(tmp_path)
    path = workspace / "PROJECT_GATE_A_B05_KNOWN_LAW_DESIGN_FREEZE.md"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(validator.ValidationError, match="B05 stopped bytes changed"):
        validator.validate(workspace)


def test_affirmative_stale_route_marker_fails_closed(tmp_path: Path) -> None:
    workspace = _copy_workspace_inputs(tmp_path)
    path = (
        workspace
        / "manuscript_v3"
        / "manuscript_v3_locked_route_successor_v1.md"
    )
    path.write_text(
        path.read_text(encoding="utf-8") + "\nCURRENT_ROUTE_USES_R5_ASAP\n",
        encoding="utf-8",
    )
    with pytest.raises(validator.ValidationError, match="forbidden current-route marker"):
        validator.validate(workspace)


def test_fixed_or_atomic_event_time_reintroduction_fails_closed(
    tmp_path: Path,
) -> None:
    workspace = _copy_workspace_inputs(tmp_path)
    path = (
        workspace
        / "manuscript_v3"
        / "manuscript_v3_locked_route_successor_v1.md"
    )
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\nThe current mixed gate uses fixed or atomic event times.\n",
        encoding="utf-8",
    )
    with pytest.raises(validator.ValidationError, match="fixed/atomic event-time"):
        validator.validate(workspace)


def test_missing_corrected_cks_formula_fails_closed(tmp_path: Path) -> None:
    workspace = _copy_workspace_inputs(tmp_path)
    path = (
        workspace
        / "manuscript_v3"
        / "manuscript_v3_locked_route_successor_v1.md"
    )
    text = path.read_text(encoding="utf-8").replace("\\Phi(x)=", "PHI_REMOVED=", 1)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(validator.ValidationError, match="lacks synchronized token"):
        validator.validate(workspace)


def test_raw_unnormalized_cks_formula_reintroduction_fails_closed(
    tmp_path: Path,
) -> None:
    workspace = _copy_workspace_inputs(tmp_path)
    path = (
        workspace
        / "manuscript_v3"
        / "manuscript_v3_locked_route_successor_v1.tex"
    )
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\n\\[\\mu_x=\\int k_{\\mathcal E}(e,\\cdot)x(de)\\]\n",
        encoding="utf-8",
    )
    with pytest.raises(validator.ValidationError, match="raw unnormalized CKS"):
        validator.validate(workspace)


def test_coherently_redigested_b05_overclosure_fails_closed(tmp_path: Path) -> None:
    workspace = _copy_workspace_inputs(tmp_path)

    def mutate(record):
        record["b05_binding"]["cannot_close"].remove("B05")

    _rewrite_record(workspace, mutate)
    with pytest.raises(validator.ValidationError, match="B05 binding boundary changed"):
        validator.validate(workspace)


def test_coherently_redigested_extra_machine_key_fails_closed(tmp_path: Path) -> None:
    workspace = _copy_workspace_inputs(tmp_path)
    _rewrite_record(workspace, lambda record: record.__setitem__("unexpected", True))
    with pytest.raises(validator.ValidationError, match="top-level roster"):
        validator.validate(workspace)


def test_machine_semantic_self_digest_change_fails_closed(tmp_path: Path) -> None:
    workspace = _copy_workspace_inputs(tmp_path)
    path = workspace / validator.MACHINE_PATH
    record = json.loads(path.read_text(encoding="utf-8"))
    record["record_sha256"] = "0" * 64
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(validator.ValidationError, match="semantic self-digest"):
        validator.validate(workspace)


def test_successor_byte_change_fails_exact_binding(tmp_path: Path) -> None:
    workspace = _copy_workspace_inputs(tmp_path)
    path = (
        workspace
        / "manuscript_v3"
        / "manuscript_v3_locked_route_successor_v1.md"
    )
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(validator.ValidationError, match="successor binding changed"):
        validator.validate(workspace)


def test_symlinked_successor_fails_closed(tmp_path: Path) -> None:
    workspace = _copy_workspace_inputs(tmp_path)
    path = (
        workspace
        / "manuscript_v3"
        / "manuscript_v3_locked_route_successor_v1.md"
    )
    target = workspace / "detached-successor.md"
    path.replace(target)
    path.symlink_to(target)
    with pytest.raises(validator.ValidationError, match="non-symlink"):
        validator.validate(workspace)
