"""Hostile tests for the bounded B12 whole-method qualification runner."""

from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest

from heterodiff.evaluation import b12_external_author_extension_components as external
from heterodiff.evaluation import b12_whole_method_nonconfirmatory_recomputation as independent
from heterodiff.evaluation import b12_whole_method_nonconfirmatory_runner as runner


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_RECEIPT_SHA256 = (
    "677aedeac9fe02a3bac9a14316c2c1f1a0047d6839e9c7492063d344b5e93220"
)
EXPECTED_EXTERNAL_SOURCE_SHA256 = (
    "859d719c1782a9964cd7219af29faeac696f1bd1d8029efa8f176dc8b4f93807"
)
EXTERNAL_IDS = tuple(
    f"CSDI_AUTHOR_EXTENSION_{ordinal}" for ordinal in range(1, 5)
) + tuple(f"EDITPP_AUTHOR_EXTENSION_{ordinal}" for ordinal in range(1, 5))
VALIDATOR_PATH = ROOT / (
    "research/diagnostics/"
    "manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.py"
)
MACHINE_PATH = ROOT / (
    "research/fixtures/"
    "manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.json"
)


@pytest.fixture(scope="module")
def execution():
    supplied = runner.build_frozen_nonconfirmatory_input()
    core_bundle = runner._core_output(str(ROOT), supplied)
    original = runner._core_output
    try:
        # The core was already executed above.  Reuse those exact objects so the
        # public runner still exercises recomputation, ledger, and open runner
        # without redundantly repeating the primary numerical path.
        runner._core_output = lambda project_root, supplied_input: core_bundle
        receipt = runner.run_supplied_nonconfirmatory_whole_method(
            str(ROOT), supplied
        )
    finally:
        runner._core_output = original
    return supplied, core_bundle[0], receipt


def test_public_entrypoint_yields_exact_stable_receipt(execution) -> None:
    supplied, core, receipt = execution
    assert runner.validate_whole_method_nonconfirmatory_receipt(receipt) is receipt
    assert receipt.receipt_sha256 == EXPECTED_RECEIPT_SHA256
    assert receipt.supplied_input_sha256 == supplied.input_sha256
    assert receipt.core_output_sha256 == receipt.independent_output_sha256
    assert receipt.core_output_sha256 == hashlib.sha256(
        runner._canonical(core) + b"\n"
    ).hexdigest()
    document = json.loads(runner.receipt_canonical_json_bytes(receipt))
    assert document["receipt_sha256"] == EXPECTED_RECEIPT_SHA256
    assert document["schema_version"] == runner.RECEIPT_SCHEMA


def test_exact_50_real_residuals_remain_open(execution) -> None:
    _, core, receipt = execution
    states = core["real_residual_receipt_states"]
    assert len(states) == len(receipt.open_residual_predicate_ids) == 50
    assert len(set(receipt.open_residual_predicate_ids)) == 50
    assert tuple(row["predicate_id"] for row in states) == runner.REAL_RESIDUAL_IDS
    assert {row["state"] for row in states} == {"OPEN_RECEIPT_ABSENT"}


def test_initializer_sampler_and_two_macrostep_path_are_composed(execution) -> None:
    _, core, _ = execution
    initializer = core["initializer_and_sampler"]
    assert initializer["fixture_id"] == "T28-M1-Q"
    assert initializer["strategy"] == "fixed-budget-sir"
    assert initializer["budget"] == len(initializer["particles"]) == 8
    assert initializer["plan_seed_hex"] == "12a5228200019dae"
    assert initializer["selected_index"] == 1
    assert initializer["adaptive_fallback_permitted"] is False
    assert initializer["formal_test_28_closed"] is False

    path = core["two_macrostep_continuous_jump_path"]
    assert [(row["raw64_word"], row["family"]) for row in path["steps"]] == [
        (2, "replacement"),
        (27, "death"),
    ]
    assert path["total_central_jumps"] == 2
    assert path["total_left_heun_applications"] == 4
    assert path["total_right_heun_applications"] == 3
    assert path["boundary_state_continuity"] is True
    assert path["rolling_lineage_preserved"] is True
    assert path["bounded_two_macrostep_path_integrated"] is True


def test_corrected_adapter_stack_and_64d_contexts_are_bound(execution) -> None:
    _, core, receipt = execution
    adapter = core["adapter_and_capsule"]
    assert adapter["adapter_receipt_count"] == 22
    assert adapter["adapter_manifest_sha256"] == receipt.adapter_manifest_sha256
    assert adapter["capsule_receipt_manifest_sha256"] == (
        receipt.capsule_manifest_sha256
    )
    assert adapter["legacy_adapter_mismatch_ordinals"] == list(range(12, 20))
    contexts = core["context_encoders"]
    assert {row["domain_id"] for row in contexts} == {
        "online-retail-ii",
        "physionet-challenge-2012",
    }
    assert {row["context_dimension"] for row in contexts} == {64}


def test_all_eight_external_author_extensions_are_exercised_without_outputs(
    execution,
) -> None:
    _, core, receipt = execution
    summary = core["external_author_extensions"]
    assert summary["module_source_sha256"] == EXPECTED_EXTERNAL_SOURCE_SHA256
    assert tuple(summary["predicate_ids"]) == EXTERNAL_IDS
    assert len(summary["implementation_record_sha256s"]) == 8
    assert all(identifier in receipt.implementation_obligations_exercised for identifier in EXTERNAL_IDS)
    assert [row["context_dimension"] for row in summary["adapters"]] == [64, 64]
    assert [row["event_count"] for row in summary["adapters"]] == [3, 3]
    assert [row["retail_structured_mark_head_count"] for row in summary["adapters"]] == [0, 3]
    assert [row["draw_count"] for row in summary["conditioning_interfaces"]] == [64, 64]
    assert [row["generated_output_count"] for row in summary["conditioning_interfaces"]] == [0, 0]
    assert {
        row["pending_draw_status"] for row in summary["conditioning_interfaces"]
    } == {external.DRAW_SLOT_STATUS}
    assert summary["csdi_occurrence_decoder_roundtrip_exact"] is True
    assert summary["upstream_packages_executed"] is False
    assert summary["upstream_native_functionality_claimed"] is False
    assert summary["production_receipts_claimed"] is False


def test_f105_two_domain_metric_and_f144_structural_seams_are_exact(execution) -> None:
    _, core, _ = execution
    bridges = core["f105_checkpoint_bridges"]
    assert [(row["f105_domain_id"], row["b06_domain_id"]) for row in bridges] == [
        ("R4-RETAIL", "online-retail-ii"),
        ("R3-PHYS", "physionet-challenge-2012"),
    ]
    for bridge in bridges:
        assert bridge["f105_score"]["draw_count"] == 64
        assert bridge["factory_and_f144_namespace_subjects_byte_equal"] is False
        assert bridge["actual_f105_factory_integrity_sha256"] != (
            bridge["f144_normalized_factory_subject_sha256"]
        )
        structural = bridge["structural_checkpoint_receipt"]
        assert structural["eligible_under_f144_structure"] is True
        assert structural["completed_optimizer_updates"] == 256
        assert structural["production_history_authenticated"] is False
        assert bridge["production_history_authenticated"] is False


def test_paired_ledger_open_runner_and_recomputation_are_bound(execution) -> None:
    _, _, receipt = execution
    assert len(receipt.ledger_event_sha256s) == 2
    assert len(set(receipt.ledger_event_sha256s)) == 2
    assert receipt.independent_output_sha256 == receipt.core_output_sha256
    independent_raw = Path(
        ROOT / runner.CAPSULE_SOURCE_PATHS[4]
    ).read_bytes()
    assert receipt.independent_implementation_sha256 == hashlib.sha256(
        independent_raw
    ).hexdigest()
    assert len(receipt.open_residual_predicate_ids) == 50


def test_nonconfirmatory_effects_and_formal_test_nonclaims_are_exact(execution) -> None:
    _, core, _ = execution
    assert core["formal_test_states"] == {"28": "OPEN", "29": "OPEN", "30": "PENDING"}
    assert core["effects"] == {
        "authority_created": False,
        "blocker_delta": 0,
        "data_accessed": False,
        "entropy_acquired": False,
        "field_delta": 0,
        "formal_test_delta": 0,
        "network_used": False,
        "production_receipts_minted": False,
        "result_delta": 0,
        "science_executed": False,
        "tracker_edited": False,
        "training_executed": False,
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("initializer_row_ordinal", 4),
        ("initializer_seed", True),
        ("path_first_word", 3),
        ("path_second_word", 26),
        ("checkpoint_step", 255),
        ("schema_version", "wrong"),
    ],
)
def test_supplied_input_tampering_fails_closed(field, value) -> None:
    supplied = runner.build_frozen_nonconfirmatory_input()
    tampered = replace(supplied, **{field: value})
    with pytest.raises(runner.WholeMethodNonconfirmatoryError):
        tampered.payload()


def test_receipt_tampering_and_duck_typing_fail_closed(execution) -> None:
    _, _, receipt = execution
    with pytest.raises(runner.WholeMethodNonconfirmatoryError):
        runner.validate_whole_method_nonconfirmatory_receipt(
            replace(receipt, core_output_sha256="0" * 64)
        )
    with pytest.raises(TypeError):
        runner.validate_whole_method_nonconfirmatory_receipt(object())


def test_independent_parser_rejects_duplicate_and_noncanonical_json() -> None:
    duplicate = (
        b'{"checkpoint_step":256,"checkpoint_step":256,'
        b'"initializer_row_ordinal":5,"initializer_seed":1343517442647661998,'
        b'"path_first_word":2,"path_second_word":27,'
        b'"schema_version":"heterodiff-b12-whole-method-nonconfirmatory-input-v1"}\n'
    )
    with pytest.raises(independent.WholeMethodIndependentRecomputationError):
        independent.independently_recompute_whole_method(str(ROOT), duplicate)
    supplied = runner.build_frozen_nonconfirmatory_input()
    noncanonical = runner.supplied_input_canonical_json_bytes(supplied).replace(
        b'"checkpoint_step":256', b'"checkpoint_step": 256'
    )
    with pytest.raises(independent.WholeMethodIndependentRecomputationError):
        independent.independently_recompute_whole_method(str(ROOT), noncanonical)


def test_missing_external_implementation_record_fails_closed(monkeypatch) -> None:
    original = external.build_author_extension_implementation_manifest

    def shortened(*, module_source_sha256):
        return original(module_source_sha256=module_source_sha256)[:-1]

    monkeypatch.setattr(
        external, "build_author_extension_implementation_manifest", shortened
    )
    with pytest.raises(runner.WholeMethodNonconfirmatoryError):
        runner._external_author_extension_summary(str(ROOT))


def test_sources_are_offline_and_independent_source_does_not_import_primary() -> None:
    forbidden_roots = {
        "http",
        "requests",
        "secrets",
        "socket",
        "subprocess",
        "torch",
        "urllib",
    }
    paths = [ROOT / runner.CAPSULE_SOURCE_PATHS[3], ROOT / runner.CAPSULE_SOURCE_PATHS[4]]
    for path in paths:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert imported.isdisjoint(forbidden_roots)
        assert "PROJECT_COMPLETION_TIMETABLE.md" not in source
        assert "PROJECT_EVIDENCE_LEDGER.md" not in source
    independent_tree = ast.parse(paths[1].read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(independent_tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_modules.update(
        alias.name
        for node in ast.walk(independent_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert not any(
        name.endswith("b12_whole_method_nonconfirmatory_runner")
        for name in imported_modules
    )


def test_noncanonical_project_root_refuses_before_execution() -> None:
    with pytest.raises(runner.WholeMethodNonconfirmatoryError):
        runner._core_output(
            str(ROOT) + "/", runner.build_frozen_nonconfirmatory_input()
        )


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "b12_whole_method_nonconfirmatory_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hash_first_validator_passes_and_resists_target_module_cache_spoof(
    monkeypatch,
) -> None:
    validator = _load_validator()
    spoof_primary = ModuleType(
        "heterodiff.evaluation.b12_whole_method_nonconfirmatory_runner"
    )
    spoof_independent = ModuleType(
        "heterodiff.evaluation.b12_whole_method_nonconfirmatory_recomputation"
    )
    monkeypatch.setitem(sys.modules, spoof_primary.__name__, spoof_primary)
    monkeypatch.setitem(sys.modules, spoof_independent.__name__, spoof_independent)
    result = validator.validate()
    assert result["decision"] == "PASS_CANDIDATE_PENDING_INDEPENDENT_REVIEW"
    assert result["proposed_timetable_task_closure_count"] == 2
    assert result["stable_receipt_sha256"] == EXPECTED_RECEIPT_SHA256


def test_machine_record_is_canonical_duplicate_free_and_self_digesting() -> None:
    raw = MACHINE_PATH.read_bytes()
    assert raw.endswith(b"\n") and not raw[:-1].endswith(b"\n")

    def pairs_hook(pairs):
        value = {}
        for key, item in pairs:
            assert key not in value
            value[key] = item
        return value

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
        b"heterodiff-b12-whole-method-nonconfirmatory-runner-candidate-v1\0"
        + json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    assert supplied == expected


def test_machine_route_binding_has_exact_eight_consumer_fields() -> None:
    machine = json.loads(MACHINE_PATH.read_text(encoding="ascii"))
    assert machine["route_binding"] == {
        "confirmatory_evidence": False,
        "implementation_obligation_count": 19,
        "open_residual_slot_count": 50,
        "receipt_schema": runner.RECEIPT_SCHEMA,
        "separate_recomputation_bytes_equal": True,
        "separately_executed_and_validated": True,
        "stable_receipt_sha256": EXPECTED_RECEIPT_SHA256,
        "supplied_input_sha256": (
            "f7e213442d073f88df73d2b33c21e43add4269a8a45b07714bfbd60b4b4ff971"
        ),
    }


def test_machine_proposes_only_two_implementation_checkboxes() -> None:
    machine = json.loads(MACHINE_PATH.read_text(encoding="ascii"))
    assert machine["registration_proposal"] == {
        "applied_timetable_task_delta": 0,
        "independent_review_required_before_registration": True,
        "proposed_timetable_task_closure_count": 2,
        "proposed_timetable_task_closures": [
            "Produce whole-method beta: initializer, continuous path, jump/edit law, and sampler integrated.",
            "End-to-end method is feature-complete.",
        ],
    }
