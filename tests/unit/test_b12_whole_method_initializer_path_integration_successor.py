"""Hostile tests for the bounded initializer-to-path B12 successor."""

from __future__ import annotations

import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import ModuleType

import pytest

from heterodiff.evaluation import (
    b12_whole_method_initializer_path_integration_recomputation as independent,
)
from heterodiff.evaluation import (
    b12_whole_method_initializer_path_integration_successor as successor,
)
from heterodiff.evaluation import (
    b12_whole_method_nonconfirmatory_runner as predecessor_runner,
)
from heterodiff.evaluation import exact_rational_quadratic_initial_tilt as exact_tilt
from heterodiff.evaluation import mixed_initializer_test28_execution_capsule as cp62
from heterodiff.processes import certified_initial_score_provider_v1 as score_facade
from heterodiff.processes import (
    plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as initializer,
)
from heterodiff.theory.configuration_reference import TransformedEvent


ROOT = Path(__file__).resolve().parents[2]
PRIMARY_PATH = ROOT / (
    "src/heterodiff/evaluation/"
    "b12_whole_method_initializer_path_integration_successor.py"
)
INDEPENDENT_PATH = ROOT / successor.INDEPENDENT_RELATIVE_PATH
PREDECESSOR_MACHINE_PATH = ROOT / successor.PREDECESSOR_MACHINE_RELATIVE_PATH
VALIDATOR_PATH = ROOT / (
    "research/diagnostics/"
    "manuscript_v3_b12_whole_method_initializer_path_integration_successor_v1.py"
)

EXPECTED_RECEIPT_SHA256 = (
    "7f3af61499f4c618daa38d72e38570c4759c5e146eeeef61bb182b9b4f20e102"
)
EXPECTED_CORE_SHA256 = (
    "73887c5411e8822942c9c37ddbdfb1a485f96ef1a2fce4c4ff56f503b4b9bc8e"
)
EXPECTED_CUSTODY_SHA256 = (
    "037d50b89289979c8b40bc843f14fd47fc0365792c0b12c4315b4132c6e428ca"
)
EXPECTED_EMPTY_CONFIGURATION_SHA256 = (
    "c9450132be2800eddc7e8e36547c49e8b7839e1e282e32f0736b453267b92b06"
)
EXPECTED_EMPTY_STATE_SHA256 = (
    "2338839b5c7df9c0845063a4053e6ab40d16132f232713ef515d5599d728f05f"
)
EXPECTED_EMPTY_TRANSFORM_SHA256 = (
    "72a27a8f315e4a1fa95933fde4fe8711d08bcd1d00766dea80bf50275ebcb5b4"
)
EXPECTED_SEED14_CONFIGURATION_SHA256 = (
    "d9cd11de541290057aa837a94b05220e9cc8404baf00b76b6cb6848790d71033"
)
EXPECTED_STABLE_INITIALIZER_SHA256 = (
    "5bca3f822a6a526fb0775cc7bf422347df7e65227141b4f2c76a462d3d597f85"
)


@pytest.fixture(scope="module")
def execution():
    core = successor._core(str(ROOT))
    receipt = successor.run_whole_method_beta_successor(str(ROOT))
    return core, receipt


@pytest.fixture(scope="module")
def validator_module():
    name = "_b12_whole_method_initializer_path_successor_validator_test_copy"
    spec = importlib.util.spec_from_file_location(name, VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(name, None)


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(successor._canonical(value) + b"\n").hexdigest()


def _receipt_unsigned_payload(receipt) -> dict:
    return {
        name: getattr(receipt, name)
        for name in receipt.__annotations__
        if name != "receipt_sha256"
    }


def _resign_receipt(receipt, **updates):
    candidate = replace(receipt, **updates, receipt_sha256="f" * 64)
    payload = _receipt_unsigned_payload(candidate)
    return replace(
        candidate,
        receipt_sha256=successor._domain_sha256(
            "heterodiff-b12-whole-method-beta-successor-receipt-v1", payload
        ),
    )


def _execute_initializer_seed(seed: int):
    row = cp62.cp62_execution_capsule_bundle().request_bindings[
        successor.FROZEN_INITIALIZER_ROW_ORDINAL - 1
    ]
    source = exact_tilt.build_t28_m1_q_exact_score_provider()
    provider = score_facade.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
        source, adapter_role_sha256=row.adapter_role_sha256
    )
    plan = initializer.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy=row.strategy,
        residual_context=row.residual_context,
        initializer_role_sha256=row.initializer_role_sha256,
        seed=seed,
        budget=row.budget,
        ess_warning_fraction=0.25,
    )
    owner = initializer.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        provider, plan=plan
    )
    result = owner.execute()
    owner.validate_result(result)
    return result


def test_public_receipt_has_exact_core_and_separate_recomputation_parity(execution) -> None:
    core, receipt = execution
    core_bytes = successor._canonical(core) + b"\n"
    independent_bytes = independent.independently_recompute_beta_successor(str(ROOT))

    assert successor.validate_beta_successor_receipt(receipt) is receipt
    assert receipt.receipt_sha256 == EXPECTED_RECEIPT_SHA256
    assert receipt.core_output_sha256 == EXPECTED_CORE_SHA256
    assert receipt.core_output_sha256 == receipt.independent_output_sha256
    assert receipt.core_output_sha256 == hashlib.sha256(core_bytes).hexdigest()
    assert independent_bytes == core_bytes
    assert receipt.independent_implementation_sha256 == hashlib.sha256(
        INDEPENDENT_PATH.read_bytes()
    ).hexdigest()
    assert receipt.independent_implementation_sha256 == (
        successor.EXPECTED_INDEPENDENT_SOURCE_SHA256
    )
    document = json.loads(successor.receipt_canonical_json_bytes(receipt))
    assert document == dict(
        _receipt_unsigned_payload(receipt), receipt_sha256=receipt.receipt_sha256
    )


def test_core_preserves_every_scope_nonclaim_and_only_proposes_beta(execution) -> None:
    core, receipt = execution
    assert core["formal_test_states"] == {"28": "OPEN", "29": "OPEN", "30": "PENDING"}
    assert core["effects"] == {
        "blocker_delta": 0,
        "data_accessed": False,
        "field_delta": 0,
        "formal_test_delta": 0,
        "network_used": False,
        "result_delta": 0,
        "science_executed": False,
        "tracker_or_ledger_edited": False,
        "training_executed": False,
        "upstream_runtimes_executed": False,
    }
    assert core["nonclaims"] == {
        "arbitrary_length_general_path": False,
        "b12_closed": False,
        "confirmatory_evidence": False,
        "direct_public_api_custody_authenticated": False,
        "gate_b0_feature_complete": False,
        "production_receipt": False,
        "real_residual_receipts_present": 0,
        "upstream_external_runtime": False,
    }
    assert core["proposed_timetable_task_closures"] == [successor.PROPOSED_TASK]
    assert receipt.proposed_timetable_task == successor.PROPOSED_TASK
    assert len(core["open_residual_predicate_ids"]) == 50
    assert tuple(core["open_residual_predicate_ids"]) == successor.REAL_RESIDUAL_IDS
    assert len(set(core["open_residual_predicate_ids"])) == 50
    assert receipt.open_residual_slot_count == 50


def test_receipt_recomputes_custody_and_resigned_substitution_fails(execution) -> None:
    _, receipt = execution
    custody_payload = {
        "derived_initial_state_sha256": receipt.derived_initial_state_sha256,
        "initializer_result_sha256": receipt.stable_initializer_execution_sha256,
        "integrated_path_input_sha256": receipt.integrated_path_input_sha256,
        "integrated_path_report_sha256": receipt.integrated_path_report_sha256,
        "predecessor_receipt_sha256": receipt.predecessor_receipt_sha256,
        "selected_configuration_sha256": receipt.selected_configuration_sha256,
        "supplied_input_sha256": receipt.supplied_input_sha256,
        "transform_policy_id": receipt.transform_policy_id,
        "transform_sha256": receipt.transform_sha256,
    }
    assert receipt.custody_chain_sha256 == EXPECTED_CUSTODY_SHA256
    assert receipt.custody_chain_sha256 == successor._domain_sha256(
        "heterodiff-b12-beta-end-to-end-custody-v1", custody_payload
    )

    for field in (
        "selected_configuration_sha256",
        "stable_initializer_execution_sha256",
        "integrated_path_input_sha256",
        "integrated_path_report_sha256",
        "derived_initial_state_sha256",
        "supplied_input_sha256",
    ):
        tampered = _resign_receipt(receipt, **{field: "1" * 64})
        with pytest.raises(successor.WholeMethodInitializerPathError):
            successor.validate_beta_successor_receipt(tampered)

    tampered_custody = _resign_receipt(receipt, custody_chain_sha256="2" * 64)
    with pytest.raises(successor.WholeMethodInitializerPathError):
        successor.validate_beta_successor_receipt(tampered_custody)


def test_frozen_empty_initializer_enters_zero_birth_then_test29_death(execution) -> None:
    core, _ = execution
    initial = core["initializer_path_state"]
    path = core["integrated_path"]

    assert core["initializer"] == {
        "selected_configuration_sha256": EXPECTED_EMPTY_CONFIGURATION_SHA256,
        "selected_event_count": 0,
        "selected_index": 1,
        "stable_execution_sha256": EXPECTED_STABLE_INITIALIZER_SHA256,
        "strategy": "fixed-budget-sir",
    }
    assert initial["empty_configuration_initial_state"] is True
    assert initial["source_event_count"] == 0
    assert initial["occurrences"] == []
    assert initial["initial_state_sha256"] == EXPECTED_EMPTY_STATE_SHA256
    assert initial["transform_sha256"] == EXPECTED_EMPTY_TRANSFORM_SHA256
    assert [(step["central_edit"]["route_id"], step["central_edit"]["family"]) for step in path["steps"]] == [
        ("beta-zero-birth", "birth"),
        ("two-step-death", "death"),
    ]
    assert [step["active_serials_before"] for step in path["steps"]] == [[], [1]]
    assert [step["active_serials_after"] for step in path["steps"]] == [[1], []]
    assert path["steps"][1]["retired_serials_after"] == [1]
    assert path["steps"][0]["left_state"] == []
    assert path["final_state"] == []
    assert path["initial_state_sha256"] == EXPECTED_EMPTY_STATE_SHA256
    assert path["final_state_sha256"] == EXPECTED_EMPTY_STATE_SHA256


def test_path_calls_actual_test29_cp24_test30_cp23_primitives(monkeypatch) -> None:
    counts = Counter()

    def instrument(owner, name):
        original = getattr(owner, name)

        def wrapped(*args, **kwargs):
            counts[name] += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(owner, name, wrapped)

    for name in (
        "run_addressed_acyclic_fixture",
        "validate_addressed_acyclic_run_result",
        "select_one_step",
        "_advance_lineage",
    ):
        instrument(successor.test29, name)
    for name in (
        "_validate_central_word",
        "_addressed_increment",
        "_validate_increment_roster",
    ):
        instrument(successor.single, name)
    instrument(successor.test30, "_heun_half")

    empty = ()
    state = successor.transform_selected_configuration(
        empty, successor._configuration_sha256(empty)
    )
    report = successor.run_bounded_integrated_path(state, empty)

    assert counts == {
        # Test-29's public validator independently replays the route and
        # lineage, so these counts include both execution and validation.
        "run_addressed_acyclic_fixture": 4,
        "validate_addressed_acyclic_run_result": 2,
        "select_one_step": 6,
        "_advance_lineage": 6,
        "_validate_central_word": 2,
        "_addressed_increment": 2,
        "_validate_increment_roster": 4,
        "_heun_half": 2,
    }
    assert report["test29_route_and_lineage_semantics_integrated"] is True
    assert report["cp24_addressed_words_validated"] is True
    assert report["test30_heun_primitive_integrated"] is True
    assert report["cp23_addressed_increments_validated"] is True
    assert report["bounded_two_macrostep_path_integrated"] is True
    assert report["arbitrary_length_general_strang_path_integrated"] is False
    assert report["formal_test28_production_law_admissible"] is False
    assert report["formal_test_28_closed"] is False
    assert report["formal_test_29_closed"] is False
    assert report["formal_test_30_closed"] is False
    assert [step["addressed_central_word"]["raw64_word"] for step in report["steps"]] == [2, 27]
    assert [step["addressed_central_word"]["key"] for step in report["steps"]] == [
        [successor.RUN_ID, successor.test29.CP24_OPERATIONAL_EPOCH_DOMAIN_TAG],
        [successor.RUN_ID, successor.test29.CP24_OPERATIONAL_EPOCH_DOMAIN_TAG],
    ]
    increment_rows = (
        report["steps"][0]["right_addressed_increments"]
        + report["steps"][1]["left_addressed_increments"]
    )
    assert [row["domain_tag"] for row in increment_rows] == [
        successor.test30.TAG_BROWNIAN_RIGHT,
        successor.test30.TAG_BROWNIAN_LEFT,
    ]


def test_path_report_and_continuous_custody_digests_recompute(execution) -> None:
    core, _ = execution
    report = core["integrated_path"]
    unsigned_report = dict(report)
    supplied_report = unsigned_report.pop("path_report_sha256")
    assert supplied_report == successor._domain_sha256(
        "heterodiff-b12-beta-integrated-path-report-v1", unsigned_report
    )
    assert report["steps"][0]["before_sha256"] == report["initial_state_sha256"]
    assert report["steps"][1]["before_sha256"] == report["steps"][0]["after_right_sha256"]
    assert core["custody_chain"]["integrated_path_input_sha256"] == report["path_input_sha256"]
    assert core["custody_chain"]["integrated_path_report_sha256"] == report["path_report_sha256"]


def test_transform_is_exactly_typed_dimensioned_and_digest_bound() -> None:
    empty = ()
    empty_state = successor.transform_selected_configuration(
        empty, EXPECTED_EMPTY_CONFIGURATION_SHA256
    )
    assert empty_state.occurrences == ()
    assert empty_state.initial_state_sha256 == EXPECTED_EMPTY_STATE_SHA256

    atom = (TransformedEvent(0, ()),)
    atom_state = successor.transform_selected_configuration(
        atom, successor._configuration_sha256(atom)
    )
    assert [(row.kind, row.coordinate) for row in atom_state.occurrences] == [("A", 0.0)]

    continuous = (TransformedEvent(1, (-1.25,)),)
    continuous_state = successor.transform_selected_configuration(
        continuous, successor._configuration_sha256(continuous)
    )
    assert [(row.kind, row.coordinate) for row in continuous_state.occurrences] == [
        ("B", -1.25)
    ]
    assert continuous_state.occurrences[0].source_event_sha256 == successor._event_sha256(
        continuous[0], 0
    )

    with pytest.raises(TypeError):
        successor.transform_selected_configuration(
            list(continuous), successor._configuration_sha256(continuous)
        )
    with pytest.raises(successor.WholeMethodInitializerPathError):
        successor.transform_selected_configuration(continuous, "1" * 64)
    for invalid in (
        (TransformedEvent(0, (0.0,)),),
        (TransformedEvent(1, ()),),
        (TransformedEvent(1, (0.0, 1.0)),),
        (TransformedEvent(2, ()),),
    ):
        with pytest.raises(successor.WholeMethodInitializerPathError):
            successor.transform_selected_configuration(
                invalid, successor._configuration_sha256(invalid)
            )


def test_transform_and_path_reject_resigned_state_or_configuration_substitution() -> None:
    configuration = (TransformedEvent(1, (-1.25,)),)
    state = successor.transform_selected_configuration(
        configuration, successor._configuration_sha256(configuration)
    )
    substituted = (TransformedEvent(1, (-1.0,)),)
    with pytest.raises(successor.WholeMethodInitializerPathError):
        successor.validate_initializer_path_state(state, substituted)
    with pytest.raises(successor.WholeMethodInitializerPathError):
        successor.run_bounded_integrated_path(state, substituted)
    with pytest.raises(successor.WholeMethodInitializerPathError):
        replace(state, initial_state_sha256="3" * 64).payload()
    with pytest.raises(successor.WholeMethodInitializerPathError):
        replace(state, transform_sha256="4" * 64).payload()
    with pytest.raises(successor.WholeMethodInitializerPathError):
        successor.run_bounded_integrated_path(state, configuration, words=(2, 26))


def test_seed14_actual_initializer_coordinate_drives_first_heun_step() -> None:
    result = _execute_initializer_seed(14)
    assert result.selected_index == 4
    assert result.selected_configuration_sha256 == EXPECTED_SEED14_CONFIGURATION_SHA256
    assert result.selected_configuration == (
        TransformedEvent(1, (-1.139088904346472,)),
    )

    state = successor.transform_selected_configuration(
        result.selected_configuration, result.selected_configuration_sha256
    )
    assert state.occurrences[0].kind == "B"
    assert state.occurrences[0].coordinate == -1.139088904346472
    report = successor.run_bounded_integrated_path(
        state, result.selected_configuration
    )
    first_step = report["steps"][0]
    increment = successor._increment(1, successor.FROZEN_WORDS[0], 0, False)
    design = successor.test30.frozen_synthetic_design()
    expected = successor.test30._heun_half(
        -1.139088904346472,
        duration=0.5 * successor.MACROSTEP_WIDTH,
        increment=increment,
        theta=design.mean_reversion,
        diffusion=design.diffusion,
        long_run_mean=design.long_run_mean_b,
    )
    assert first_step["left_addressed_increments"][0]["increment_hex"] == increment.hex()
    assert float.fromhex(first_step["left_state"][0]["coordinate_hex"]) == expected
    assert first_step["left_state"][0]["source_event_sha256"] == (
        state.occurrences[0].source_event_sha256
    )

    changed_configuration = (TransformedEvent(1, (-1.0,)),)
    changed_state = successor.transform_selected_configuration(
        changed_configuration,
        successor._configuration_sha256(changed_configuration),
    )
    changed_report = successor.run_bounded_integrated_path(
        changed_state, changed_configuration
    )
    assert changed_report["path_input_sha256"] != report["path_input_sha256"]
    assert changed_report["path_report_sha256"] != report["path_report_sha256"]
    assert changed_report["steps"][0]["left_state"][0]["coordinate_hex"] != (
        first_step["left_state"][0]["coordinate_hex"]
    )


def test_runtime_local_initializer_digest_varies_but_semantic_digest_and_core_do_not() -> None:
    supplied = successor.build_frozen_supplied_input()
    first = successor._execute_frozen_initializer(supplied)
    second = successor._execute_frozen_initializer(supplied)

    assert first.result_sha256 != second.result_sha256
    assert successor._stable_initializer_execution_sha256(first, supplied) == (
        EXPECTED_STABLE_INITIALIZER_SHA256
    )
    assert successor._stable_initializer_execution_sha256(second, supplied) == (
        EXPECTED_STABLE_INITIALIZER_SHA256
    )
    assert successor._canonical(successor._core(str(ROOT))) == successor._canonical(
        successor._core(str(ROOT))
    )


def test_predecessor_whole_run_is_neither_imported_nor_called(monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("predecessor whole-run entry point was called")

    monkeypatch.setattr(
        predecessor_runner,
        "run_supplied_nonconfirmatory_whole_method",
        forbidden,
    )
    receipt = successor.run_whole_method_beta_successor(str(ROOT))
    assert receipt.receipt_sha256 == EXPECTED_RECEIPT_SHA256

    for path in (PRIMARY_PATH, INDEPENDENT_PATH):
        source = path.read_text(encoding="utf-8")
        assert "run_supplied_nonconfirmatory_whole_method" not in source


@pytest.mark.parametrize("preloaded", ["module", "none"])
def test_captured_independent_ignores_cache_spoof_and_restores_it(
    monkeypatch, preloaded
) -> None:
    target_name = (
        "heterodiff.evaluation."
        "b12_whole_method_initializer_path_integration_recomputation"
    )
    attribute = target_name.rsplit(".", 1)[1]
    import heterodiff.evaluation as evaluation_package

    if preloaded == "module":
        cached = ModuleType(target_name)
        cached.__file__ = str(INDEPENDENT_PATH)

        def forbidden(_project_root):
            raise AssertionError("cached recomputation proxy was called")

        cached.independently_recompute_beta_successor = forbidden
    else:
        cached = None
    monkeypatch.setitem(sys.modules, target_name, cached)
    monkeypatch.setattr(evaluation_package, attribute, cached)

    receipt = successor.run_whole_method_beta_successor(str(ROOT))
    assert receipt.receipt_sha256 == EXPECTED_RECEIPT_SHA256
    assert sys.modules[target_name] is cached
    assert getattr(evaluation_package, attribute) is cached


def _copy_predecessor_root(destination: Path) -> Path:
    target = destination / successor.PREDECESSOR_MACHINE_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    shutil.copyfile(PREDECESSOR_MACHINE_PATH, target)
    target.chmod(0o644)
    return target


@pytest.mark.parametrize(
    "attack",
    [
        "leaf_symlink",
        "root_symlink",
        "parent_symlink",
        "hardlink",
        "mode_0600",
        "same_size_substitution",
    ],
)
def test_predecessor_machine_custody_refuses_filesystem_substitution(
    tmp_path: Path, attack: str
) -> None:
    actual_root = tmp_path / "actual-root"
    machine = _copy_predecessor_root(actual_root)
    project_root = actual_root

    if attack == "leaf_symlink":
        original = machine.with_name("machine-original.json")
        machine.rename(original)
        machine.symlink_to(original.name)
    elif attack == "root_symlink":
        project_root = tmp_path / "root-link"
        project_root.symlink_to(actual_root, target_is_directory=True)
    elif attack == "parent_symlink":
        parent = machine.parent
        original = parent.with_name("fixtures-original")
        parent.rename(original)
        parent.symlink_to(original.name, target_is_directory=True)
    elif attack == "hardlink":
        os.link(machine, actual_root / "machine-hardlink.json")
    elif attack == "mode_0600":
        machine.chmod(0o600)
    elif attack == "same_size_substitution":
        raw = bytearray(machine.read_bytes())
        raw[0] = ord("[") if raw[0] != ord("[") else ord("{")
        machine.write_bytes(bytes(raw))
        machine.chmod(0o644)
    else:  # pragma: no cover - the parameter roster is closed above
        raise AssertionError("unknown hostile custody case")

    with pytest.raises((OSError, successor.WholeMethodInitializerPathError)):
        successor._predecessor_binding(str(project_root))


def test_predecessor_machine_baseline_is_exact_and_not_reexecuted(tmp_path: Path) -> None:
    root = tmp_path / "baseline"
    _copy_predecessor_root(root)
    binding = successor._predecessor_binding(str(root))
    assert binding["machine_raw_sha256"] == successor.PREDECESSOR_MACHINE_SHA256
    assert binding["machine_record_sha256"] == successor.PREDECESSOR_RECORD_SHA256
    assert binding["receipt_sha256"] == successor.PREDECESSOR_RECEIPT_SHA256
    assert binding["route_binding"] == json.loads(
        PREDECESSOR_MACHINE_PATH.read_text(encoding="ascii")
    )["route_binding"]


def test_sources_are_offline_and_independent_does_not_import_primary() -> None:
    forbidden_roots = {
        "aiohttp",
        "ftplib",
        "http",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    trees = []
    for path in (PRIMARY_PATH, INDEPENDENT_PATH):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        trees.append(tree)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        assert imported.isdisjoint(forbidden_roots)
        assert "PROJECT_COMPLETION_TIMETABLE.md" not in source
        assert "PROJECT_EVIDENCE_LEDGER.md" not in source
        assert "run_supplied_nonconfirmatory_whole_method" not in source

    independent_imports = {
        node.module
        for node in ast.walk(trees[1])
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    independent_imports.update(
        alias.name
        for node in ast.walk(trees[1])
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert not any(
        name.endswith("b12_whole_method_initializer_path_integration_successor")
        for name in independent_imports
    )


def test_direct_public_api_is_explicitly_non_authoritative(execution) -> None:
    core, receipt = execution
    assert successor.DIRECT_PUBLIC_API_CUSTODY_AUTHENTICATED is False
    assert successor.AUTHORITATIVE_QUALIFICATION_REQUIRES_ISOLATED_VALIDATOR is True
    assert core["qualification_boundary"] == {
        "authoritative_isolated_hash_first_validator_required": True,
        "direct_public_api_custody_authenticated": False,
    }
    assert receipt.direct_public_api_custody_authenticated is False
    assert receipt.authoritative_qualification_requires_isolated_validator is True
    assert receipt.test28_initializer_admissible is True
    assert receipt.initializer_to_path_integrated is True
    with pytest.raises(successor.WholeMethodInitializerPathError):
        successor.validate_beta_successor_receipt(
            _resign_receipt(receipt, direct_public_api_custody_authenticated=True)
        )
    with pytest.raises(successor.WholeMethodInitializerPathError):
        successor.validate_beta_successor_receipt(
            _resign_receipt(
                receipt,
                authoritative_qualification_requires_isolated_validator=False,
            )
        )


def test_core_exact_hash_pin_is_stable(execution) -> None:
    core, _ = execution
    assert _canonical_sha256(core) == EXPECTED_CORE_SHA256


def _copy_validator_package(validator, destination: Path) -> Path:
    root = destination / "physical-copy"
    paths = {
        validator.MACHINE_REL,
        validator.VALIDATOR_REL,
        *(path for _, path, _, _ in validator.EXPECTED_AUTHORED_BINDINGS),
        *(path for path, _, _ in validator.SEMANTIC_MANIFEST),
    }
    for relative in sorted(paths):
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return root.resolve(strict=True)


def test_authoritative_validator_passes_root_and_unrelated_physical_copy(
    validator_module, tmp_path: Path
) -> None:
    first = validator_module.validate(ROOT)
    copied = _copy_validator_package(validator_module, tmp_path)
    pycache = copied / "src/heterodiff/evaluation/__pycache__"
    pycache.mkdir()
    (pycache / "hostile-shadow.cpython-311.pyc").write_bytes(b"hostile-bytecode")
    second = validator_module.validate(copied)
    assert first == second
    assert first["receipt_sha256"] == EXPECTED_RECEIPT_SHA256
    assert first["core_output_sha256"] == EXPECTED_CORE_SHA256


@pytest.mark.parametrize("poison_kind", ["proxy", "none"])
def test_isolated_validator_ignores_and_preserves_all_parent_module_cache_poison(
    validator_module, monkeypatch, poison_kind: str
) -> None:
    targets = (
        "heterodiff.evaluation.b12_whole_method_initializer_path_integration_successor",
        "heterodiff.evaluation.b12_whole_method_initializer_path_integration_recomputation",
        "heterodiff.evaluation.exact_rational_quadratic_initial_tilt",
        "heterodiff.evaluation.formal_test29_test30_single_macrostep_integration",
        "heterodiff.evaluation.formal_test29_test30_two_macrostep_path_qualification",
        "heterodiff.evaluation.formal_test30_synthetic_coupled_path_qualification",
        "heterodiff.evaluation.mixed_initializer_test28_execution_capsule",
        "heterodiff.processes.certified_initial_score_provider_v1",
        "heterodiff.processes.formal_test29_finite_acyclic_route_oracle",
        "heterodiff.processes.plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2",
    )
    poisoned = {}
    for target in targets:
        if poison_kind == "proxy":
            value = ModuleType(target)
            honest = sys.modules[target]
            value.__file__ = getattr(honest, "__file__", None)
        else:
            value = None
        poisoned[target] = value
        monkeypatch.setitem(sys.modules, target, value)
        parent_name, attribute = target.rsplit(".", 1)
        monkeypatch.setattr(sys.modules[parent_name], attribute, value, raising=False)

    result = validator_module.validate(ROOT)
    assert result["receipt_sha256"] == EXPECTED_RECEIPT_SHA256
    for target, value in poisoned.items():
        assert sys.modules[target] is value
        parent_name, attribute = target.rsplit(".", 1)
        assert getattr(sys.modules[parent_name], attribute) is value


def test_isolated_validator_ignores_pythonpath_sitecustomize_cwd_and_shadow_source(
    validator_module, monkeypatch, tmp_path: Path
) -> None:
    shadow = tmp_path / "shadow"
    fake = shadow / (
        "heterodiff/evaluation/"
        "b12_whole_method_initializer_path_integration_successor.py"
    )
    fake.parent.mkdir(parents=True)
    fake.write_text("raise RuntimeError('cwd or PYTHONPATH shadow executed')\n")
    (shadow / "sitecustomize.py").write_text(
        "raise RuntimeError('sitecustomize executed')\n"
    )
    monkeypatch.setenv("PYTHONPATH", str(shadow))
    monkeypatch.chdir(shadow)
    result = validator_module.validate(ROOT)
    assert result["receipt_sha256"] == EXPECTED_RECEIPT_SHA256


def test_two_concurrent_isolated_validators_have_identical_receipts(
    validator_module,
) -> None:
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: validator_module.validate(ROOT), range(2)))
    assert results[0] == results[1]
    assert results[0]["receipt_sha256"] == EXPECTED_RECEIPT_SHA256


@pytest.mark.parametrize(
    "attack",
    [
        "root_symlink",
        "parent_symlink",
        "leaf_symlink",
        "hardlink",
        "mode_0600",
        "same_size_substitution",
    ],
)
def test_authoritative_validator_rejects_workspace_path_and_byte_attacks(
    validator_module, tmp_path: Path, attack: str
) -> None:
    copied = _copy_validator_package(validator_module, tmp_path)
    primary = copied / validator_module.PRIMARY_REL
    supplied_root = copied
    if attack == "root_symlink":
        supplied_root = tmp_path / "root-link"
        supplied_root.symlink_to(copied, target_is_directory=True)
    elif attack == "parent_symlink":
        parent = primary.parent
        original = parent.with_name("evaluation-original")
        parent.rename(original)
        parent.symlink_to(original.name, target_is_directory=True)
    elif attack == "leaf_symlink":
        original = primary.with_name("primary-original.py")
        primary.rename(original)
        primary.symlink_to(original.name)
    elif attack == "hardlink":
        os.link(primary, copied / "primary-hardlink.py")
    elif attack == "mode_0600":
        primary.chmod(0o600)
    elif attack == "same_size_substitution":
        raw = bytearray(primary.read_bytes())
        raw[0] ^= 1
        primary.write_bytes(bytes(raw))
        primary.chmod(0o644)
    with pytest.raises((OSError, validator_module.ValidationError)):
        validator_module.validate(supplied_root)


@pytest.mark.parametrize("phase", ["before_child", "after_child"])
def test_private_capsule_tamper_fails_before_or_after_execution(
    validator_module, monkeypatch, phase: str
) -> None:
    original = validator_module._run_isolated_child

    def attacked(capsule):
        target = capsule / validator_module.PRIMARY_REL
        if phase == "before_child":
            raw = bytearray(target.read_bytes())
            raw[0] ^= 1
            target.write_bytes(bytes(raw))
            target.chmod(0o644)
            return original(capsule)
        envelope = original(capsule)
        raw = target.read_bytes()
        target.unlink()
        target.write_bytes(raw)
        target.chmod(0o644)
        return envelope

    monkeypatch.setattr(validator_module, "_run_isolated_child", attacked)
    with validator_module._opened_stable_root(ROOT) as (root_fd, root_identity):
        captures = validator_module._capture_workspace(
            root_fd, root_identity, include_machine=False
        )
        with pytest.raises(validator_module.ValidationError):
            validator_module._execute_capsule(captures)


def test_workspace_replacement_after_child_is_detected(
    validator_module, monkeypatch, tmp_path: Path
) -> None:
    copied = _copy_validator_package(validator_module, tmp_path)
    original = validator_module._execute_capsule

    def attacked(captures):
        envelope = original(captures)
        target = copied / validator_module.PRIMARY_REL
        raw = target.read_bytes()
        target.unlink()
        target.write_bytes(raw)
        target.chmod(0o644)
        return envelope

    monkeypatch.setattr(validator_module, "_execute_capsule", attacked)
    with pytest.raises(validator_module.ValidationError):
        validator_module.validate(copied)


@pytest.mark.parametrize("mode", ["failure", "stderr", "malformed", "duplicate"])
def test_isolated_child_failure_and_output_tampering_fail_closed(
    validator_module, monkeypatch, mode: str
) -> None:
    if mode == "failure":
        completed = subprocess.CompletedProcess([], 9, b"", b"child failed")
    elif mode == "stderr":
        completed = subprocess.CompletedProcess([], 0, b"{}\n", b"warning")
    elif mode == "malformed":
        completed = subprocess.CompletedProcess([], 0, b"not-json\n", b"")
    else:
        completed = subprocess.CompletedProcess([], 0, b'{"x":1,"x":2}\n', b"")
    monkeypatch.setattr(validator_module.subprocess, "run", lambda *a, **k: completed)
    with validator_module._opened_stable_root(ROOT) as (root_fd, root_identity):
        captures = validator_module._capture_workspace(
            root_fd, root_identity, include_machine=False
        )
        with pytest.raises(validator_module.ValidationError):
            validator_module._execute_capsule(captures)
