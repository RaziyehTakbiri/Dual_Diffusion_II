"""Hash-first package tests for the B12 Gate-B0 integration candidate."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest

import heterodiff.evaluation as evaluation_package
from heterodiff.evaluation import b12_independent_component_recomputation as independent
from heterodiff.evaluation import b12_integration_stack as stack


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = (
    ROOT
    / "research/diagnostics/manuscript_v3_b12_gate_b0_integration_implementation_candidate_v1.py"
)
MACHINE_PATH = (
    ROOT
    / "research/fixtures/manuscript_v3_b12_gate_b0_integration_implementation_candidate_v1.json"
)
TASK_TEXT = (
    "Runtime identity, runner, capsule, ledger, and recomputation implementations exist."
)


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "b12_gate_b0_integration_candidate_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator():
    return _load_validator()


@pytest.fixture(scope="module")
def semantics(validator):
    return validator.derive_semantics()


def test_standalone_validator_passes_exact_candidate(validator, monkeypatch) -> None:
    baseline = validator.derive_semantics()
    spoof = ModuleType("heterodiff.evaluation.b12_integration_stack")
    spoof.__file__ = str(
        ROOT / "src/heterodiff/evaluation/b12_integration_stack.py"
    )
    spoof.RuntimeIdentityBinding = None
    spoof.DEFAULT_CAPSULE_SOURCE_PATHS = ()
    monkeypatch.setitem(
        sys.modules, "heterodiff.evaluation.b12_integration_stack", spoof
    )
    monkeypatch.setattr(evaluation_package, "b12_integration_stack", spoof)
    monkeypatch.setitem(
        sys.modules,
        "heterodiff.evaluation.b12_independent_component_recomputation",
        None,
    )
    monkeypatch.setattr(
        evaluation_package,
        "b12_independent_component_recomputation",
        None,
    )
    assert validator.derive_semantics() == baseline
    result = validator.validate()
    assert result["decision"] == "PASS_CANDIDATE_PENDING_INDEPENDENT_REVIEW"
    assert result["proposed_timetable_task_closure_count"] == 1
    assert result["proposed_timetable_task"] == TASK_TEXT


def test_machine_record_is_canonical_duplicate_free_and_self_digesting() -> None:
    raw = MACHINE_PATH.read_bytes()
    assert raw.endswith(b"\n") and not raw[:-1].endswith(b"\n")

    def pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result
            result[key] = value
        return result

    machine = json.loads(raw[:-1].decode("ascii"), object_pairs_hook=pairs_hook)
    canonical = json.dumps(
        machine,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    assert canonical == raw[:-1]
    unsigned = dict(machine)
    supplied = unsigned.pop("record_sha256")
    expected = hashlib.sha256(
        b"heterodiff-b12-gate-b0-integration-implementation-candidate-v1\0"
        + json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    assert supplied == expected


def test_only_exact_gate_b0_implementation_task_is_proposed(semantics) -> None:
    proposal = semantics["registration_proposal"]
    assert proposal == {
        "applied_timetable_task_delta": 0,
        "independent_review_required_before_registration": True,
        "proposed_timetable_task_closure_count": 1,
        "proposed_timetable_task_closures": [TASK_TEXT],
    }


def test_all_five_named_implementation_surfaces_exist(semantics) -> None:
    surfaces = semantics["implementation_surfaces"]
    assert surfaces == {
        "capsule": "IMPLEMENTED_AND_FOCUSED_TESTED",
        "durable_paired_ledger": "IMPLEMENTED_AND_FOCUSED_TESTED",
        "independent_recomputation": "IMPLEMENTED_AS_SEPARATE_MODULE_AND_FOCUSED_TESTED",
        "runner": "IMPLEMENTED_AND_FOCUSED_TESTED",
        "runtime_identity_binding": "IMPLEMENTED_FUTURE_CALLER_SUPPLIED_SEAM_AND_FOCUSED_TESTED",
    }


def test_capsule_is_self_contained_only_at_component_evidence_scope(semantics) -> None:
    capsule = semantics["capsule_exercise"]
    assert capsule["component_binding_payload_name"] == "component-bindings.json"
    assert capsule["component_source_payload_count"] == 11
    assert capsule["accepted_receipt_payload_digest_count"] == 12
    assert capsule["binding_payload_is_physically_planned"] is True
    assert capsule["binding_payload_is_manifest_bound"] is True
    assert capsule["binding_payload_is_receipt_bound"] is True
    assert capsule["standalone_executable_claimed"] is False
    assert capsule["transitive_dependency_closure_claimed"] is False


def test_real_residual_exercise_is_exact_50_open_slots_without_accepts(semantics) -> None:
    runner = semantics["runner_exercise"]
    assert runner["corrected_adapter_count"] == 22
    assert runner["residual_slot_count"] == 50
    assert runner["residual_receipts_present"] == 0
    assert runner["residual_receipts_missing"] == 50
    assert runner["every_slot_subject_bound"] is True
    assert runner["real_residual_accept_receipts_locally_minted"] is False
    assert runner["embedded_nonproduction_authentication_rejected"] is True


def test_relative_and_absolute_text_aliases_fail_closed(semantics) -> None:
    assert semantics["canonical_path_hostility"] == {
        "absolute_root_double_separator_rejected": True,
        "absolute_root_trailing_separator_rejected": True,
        "relative_dot_segment_rejected": True,
        "relative_double_separator_rejected": True,
        "relative_trailing_separator_rejected": True,
    }
    bindings = stack.build_component_bindings(str(ROOT))
    outputs = stack.run_and_independently_recompute(str(ROOT), bindings)
    with pytest.raises(stack.B12IntegrationError):
        stack.build_component_bindings(str(ROOT) + "/")
    with pytest.raises(independent.IndependentRecomputationError):
        independent.independently_recompute_component_output(
            str(ROOT) + "/", outputs.binding_document_bytes
        )


def test_prohibited_effects_and_external_surfaces_remain_absent(
    semantics,
) -> None:
    assert semantics["effects"] == {
        "authority_created": False,
        "blocker_delta": 0,
        "contact_performed": False,
        "data_accessed": False,
        "field_delta": 0,
        "formal_test_delta": 0,
        "network_used": False,
        "result_delta": 0,
        "runtime_identity_selected": False,
        "science_executed": False,
        "timetable_task_delta_applied": 0,
        "tracker_or_evidence_ledger_edited": False,
    }
    forbidden_import_roots = {
        "http",
        "requests",
        "secrets",
        "socket",
        "subprocess",
        "torch",
        "urllib",
    }
    for relative in (
        "src/heterodiff/evaluation/b12_integration_stack.py",
        "src/heterodiff/evaluation/b12_independent_component_recomputation.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert imported.isdisjoint(forbidden_import_roots)
        assert "PROJECT_COMPLETION_TIMETABLE.md" not in source
        assert "PROJECT_EVIDENCE_LEDGER.md" not in source
