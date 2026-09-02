"""Hostile tests for the stopped C17 PO13 initializer-KL proof package.

All mutations occur in pytest temporary replicas.  The suite loads only the
read-only static validator; it imports no project science, accesses no data,
draws no entropy, performs no scientific execution, and changes no canonical
project artifact.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List, Mapping

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/manuscript_v3_c17_po13_initializer_kl_proof_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/manuscript_v3_c17_po13_initializer_kl_proof_v1.json"
)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "c17_po13_initializer_kl_proof_validator", ROOT / VALIDATOR_REL
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


def _roster(module: ModuleType) -> List[str]:
    return [
        module.HUMAN_PATH,
        module.MACHINE_PATH,
        module.VALIDATOR_PATH,
        module.TEST_PATH,
        *[row["path"] for row in module.INPUT_BINDINGS],
    ]


def _copy_paths(paths: Iterable[str], tmp_path: Path) -> Path:
    for relative in paths:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return tmp_path


def _copy_package(module: ModuleType, tmp_path: Path) -> Path:
    return _copy_paths(_roster(module), tmp_path)


def _rewrite_machine(
    module: ModuleType,
    root: Path,
    mutate: Callable[[Dict[str, Any]], None],
    *,
    recompute_digest: bool = True,
    canonical: bool = True,
) -> None:
    path = root / MACHINE_REL
    record = json.loads(path.read_text(encoding="ascii"))
    mutate(record)
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    raw = module.canonical_machine_bytes(record)
    if not canonical:
        raw = json.dumps(record, indent=2, sort_keys=True).encode("ascii") + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)


def _replace(record: Dict[str, Any], pointer: str, value: Any) -> None:
    current: Any = record
    tokens = pointer.split(".")
    for token in tokens[:-1]:
        current = current[int(token)] if type(current) is list else current[token]
    final = tokens[-1]
    if type(current) is list:
        current[int(final)] = value
    else:
        current[final] = value


def _rebind(
    module: ModuleType,
    original: Mapping[str, Any],
    raw: bytes,
) -> Dict[str, Any]:
    return module._binding(
        original["ordinal"],
        original["role"],
        original["path"],
        raw,
        expected_symbols=original.get("expected_symbols"),
        foreign_self_digest=original.get("record_sha256"),
    )


def test_canonical_package_validates_with_exact_narrow_effect(
    validator: ModuleType,
) -> None:
    status = validator.validate()
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": "C17_GATE_A_ROUTE_NARROWED_NO_GO_PO13_PROVED_C17_UNPROVED",
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "control_predicate": (
            "C17_PO13_INITIALIZER_KL_DERIVATION_AND_ORIENTATION_PROVED"
        ),
        "control_predicate_value_after_independent_audit": True,
        "gate_control_predicate": "GATE_A_C17_ROUTE_NARROWED_PREOUTCOME_NO_GO",
        "gate_control_predicate_value_after_independent_audit": True,
        "selected_route": (
            "FORK_B_DIRECT_SIMULTANEOUS_TARGET_OCCUPATION_CERTIFICATES"
        ),
        "orientation": "KL(P0_H || P0_HHAT)_TARGET_FIRST",
        "proof_obligation_count": 18,
        "proof_obligations_discharged_by_package": 1,
        "discharged_obligation": "PO13",
        "PO16_open": True,
        "A1_through_A12_open_count": 12,
        "finite_nonvacuous_U0_present": False,
        "C17_status": "UNPROVED",
        "Gate_A_C17_item": "ROUTE_NARROWED_PREOUTCOME_NO_GO",
        "unresolved_fields_closed": 0,
        "blockers_closed": 0,
        "scientific_effect": 0,
        "exact_witness": "PASS",
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


def test_authority_is_exact_narrow_and_hashes(validator: ModuleType) -> None:
    authority = validator.expected_record()["authority_provenance"]
    assert authority["normalized_visible_text"] == validator.NORMALIZED_AUTHORITY_TEXT
    raw = authority["normalized_visible_text"].encode("utf-8")
    assert len(raw) == 207
    assert hashlib.sha256(raw).hexdigest() == validator.AUTHORITY_TEXT_SHA256
    assert authority["continued_bounded_local_project_work_authorized"] is True
    for key in (
        "tracker_edit_authorized_by_package",
        "external_contact_or_browsing_authorized",
        "data_access_or_download_authorized",
        "entropy_or_live_randomness_authorized",
        "runtime_approval_authorized",
        "scientific_execution_authorized",
        "training_authorized",
        "claim_promotion_or_submission_authorized",
    ):
        assert authority[key] is False


def test_general_theorem_scope_has_exact_orientation_and_extended_semantics(
    validator: ModuleType,
) -> None:
    scope = validator.expected_record()["theorem_scope"]
    assert scope["orientation"] == "KL(P0_H || P0_HHAT)_TARGET_FIRST"
    assert scope["measurable_space_general"] is True
    assert scope["finite_state_required"] is False
    assert scope["density_ratio_identity"] == (
        "DP0/DQ0=(Z_HHAT/Z_H)EXP(-E)"
    )
    assert scope["log_mgf_identity"] == "E_P0[EXP(E)]=Z_HHAT/Z_H"
    assert scope["extended_value_semantics"] == (
        "E_POSITIVE_PART_INTEGRABLE_KL_FINITE_IFF_E_NEGATIVE_PART_INTEGRABLE"
    )
    assert scope["gauge_invariant"] is True


def test_all_eight_propositions_have_uniform_order_and_no_floating_proof(
    validator: ModuleType,
) -> None:
    rows = validator.expected_record()["proposition_register"]
    assert [row["ordinal"] for row in rows] == list(range(8))
    assert [row["proposition_id"] for row in rows] == [
        "PO13.1A", "PO13.1B", "PO13.1C", "PO13.2",
        "PO13.3", "PO13.4", "PO13.5", "L16.1",
    ]
    assert all(row["uses_floating_arithmetic"] is False for row in rows)
    assert rows[-1]["status"] == (
        "PROVED_AUXILIARY_LEMMA_PO16_REMAINS_OPEN"
    )


def test_only_po13_derivation_is_discharged(validator: ModuleType) -> None:
    rows = validator.expected_record()["proof_obligation_effects"]
    assert [row["ordinal"] for row in rows] == list(range(18))
    assert [row["proof_obligation_id"] for row in rows] == [
        "PO" + str(index).zfill(2) for index in range(1, 19)
    ]
    discharged = [
        row for row in rows if row["mathematical_derivation_discharged"]
    ]
    assert len(discharged) == 1
    assert discharged[0]["proof_obligation_id"] == "PO13"
    assert discharged[0]["status"] == (
        "DISCHARGED_CONDITIONAL_ON_DECLARED_A3_OBJECTS"
    )
    assert discharged[0]["real_domain_discharged"] is False
    assert discharged[0]["sufficient_for_c17"] is False
    assert rows[15]["status"] == (
        "OPEN_AUXILIARY_SHARED_GUIDE_CANCELLATION_LEMMA_ONLY"
    )


def test_all_domain_assumptions_remain_open(validator: ModuleType) -> None:
    rows = validator.expected_record()["assumption_effects"]
    assert [row["assumption_id"] for row in rows] == [
        "A" + str(index) for index in range(1, 13)
    ]
    assert all(row["status"] == "OPEN" for row in rows)
    assert all(row["general_assumption_verified"] is False for row in rows)
    assert all(row["physionet_verified"] is False for row in rows)
    assert all(row["retail_verified"] is False for row in rows)
    assert all(row["closed_by_this_package"] is False for row in rows)


def test_exact_rational_witness_reconstructs_without_reported_float_values(
    validator: ModuleType,
) -> None:
    result = validator.evaluate_exact_witness()
    assert result == {
        "exact_rational_identities": "PASS",
        "forward_positive": True,
        "reverse_positive": True,
        "orientations_unequal": True,
        "log_mgf_formula_agrees": True,
        "range_bound_strict_for_witness": True,
        "decimal_precision": 80,
        "floating_values_reported": False,
    }
    witness = validator.expected_record()["finite_exact_witness"]
    assert witness["target_initial_p0"] == ["2/3", "1/3"]
    assert witness["plugin_initial_q0"] == ["1/4", "3/4"]
    assert witness["all_dynamic_components_exactly_zero"] is True
    assert witness["path_kl_equals_initializer_kl"] is True
    assert witness["initializer_kl_strictly_positive"] is True


def test_conditional_u0_route_is_valid_but_uninstantiated(
    validator: ModuleType,
) -> None:
    route = validator.expected_record()["conditional_U0_range_route"]
    assert route["must_bind_actual_error_rtheta_minus_rstar"] is True
    assert route["rtheta_architecture_range_alone_sufficient"] is False
    assert route["unknown_rstar_norm_accepted"] is False
    assert route["actual_error_range_certificate_present"] is False
    assert route["nonvacuity_threshold_present"] is False
    assert route["U0"] is None
    assert route["K0_numeric_value"] is None
    assert route["PO15_discharged"] is False


def test_smooth_terminal_matched_obstruction_is_exact_and_unbounded(
    validator: ModuleType,
) -> None:
    row = validator.expected_record()["smooth_terminal_matched_obstruction"]
    assert row["state_space"] == "UNIT_INTERVAL_WITH_BOREL_SIGMA_FIELD"
    assert row["base_generator"] == "ZERO_GENERATOR"
    assert row["terminal_and_clean_hold_residuals_zero"] is True
    assert row["exact_initial_density"] == "P_N(X)=N*EXP(N*X)/(EXP(N)-1)"
    assert row["plugin_initial_density"] == "Q_N(X)=1"
    assert row["K0_strict_lower_bound"] == "K0_N>LOG(N)-1"
    assert row["K0_unbounded_as_n_tends_to_infinity"] is True
    assert [row[key] for key in ("KC", "K_PLUS", "K_MINUS", "K_REPLACEMENT")] == [
        "0", "0", "0", "0"
    ]
    assert row["terminal_matching_plus_zero_dynamic_error_controls_full_path_KL"] is False
    assert row["separate_initializer_certificate_necessary"] is True
    assert row["dataset_checkpoint_solver_or_floating_execution_used"] is False


def test_gate_A_is_closed_only_by_preoutcome_route_narrowing(
    validator: ModuleType,
) -> None:
    gate = validator.expected_record()["gate_A_route_narrowing_decision"]
    assert gate["decision"] == "ROUTE_NARROWED_PREOUTCOME_NO_GO"
    assert gate["real_domain_C17_promotion_under_current_Fork_B_observability"] == "NO_GO"
    assert gate["C17_theorem_status"] == "UNPROVED"
    assert gate["surviving_scope"] == (
        "CONDITIONAL_THEORY_AND_FINITE_MIXED_KNOWN_LAW_FALSIFICATION_ONLY"
    )
    assert gate["real_domain_contribution_or_model_quality_guarantee_survives"] is False
    assert gate["decision_is_universal_impossibility_claim"] is False
    assert gate["all_reopening_conditions_conjunctive"] is True
    assert gate["partial_satisfaction_reopens_route"] is False
    assert gate["eligible_control_predicate_after_independent_audit"] == (
        "GATE_A_C17_ROUTE_NARROWED_PREOUTCOME_NO_GO"
    )
    conditions = gate["survival_conditions"]
    assert [row["ordinal"] for row in conditions] == list(range(9))
    assert [row["condition_id"] for row in conditions] == [
        "S1_PATH_IDENTITY", "S2_INITIALIZER", "S3_CONTINUOUS", "S4_BIRTH",
        "S5_DEATH", "S6_REPLACEMENT", "S7_SIMULTANEITY", "S8_NONVACUITY",
        "S9_FALSIFICATION_AND_AUDIT",
    ]
    assert conditions[0]["requirement"] == (
        "PO14_PROVED_WITH_A1_THROUGH_A12_INCLUDING_IDEAL_OPERATIONAL_"
        "SEPARATION_AND_CANDIDATE_BASE_SCOPE_AND_TARGET_FIRST_ORIENTATION"
    )
    assert all(row["currently_satisfied"] is False for row in conditions)
    assert all(row["required_to_reopen_real_domain_promotion"] is True for row in conditions)


def test_fields_blockers_gate_and_claims_remain_open(
    validator: ModuleType,
) -> None:
    effects = validator.expected_record()["field_blocker_gate_effects"]
    assert effects["C17_status"] == "UNPROVED"
    assert effects["Gate_A_C17_viability_or_narrowing_item"] == (
        "ELIGIBLE_TO_CHECK_AS_ROUTE_NARROWED_PREOUTCOME_NO_GO_AFTER_INDEPENDENT_AUDIT"
    )
    assert effects["B01"] == "OPEN"
    assert [effects["F" + str(index).zfill(3)] for index in range(1, 7)] == [
        None, None, None, None, None, None
    ]
    assert effects["unresolved_field_count"] == 172
    assert effects["effective_open_blocker_count"] == 12
    assert effects["unresolved_fields_closed"] == 0
    assert effects["blockers_closed"] == 0
    assert effects["formal_tests_closed"] == 0
    assert effects["scientific_results_produced"] == 0
    assert effects["tracker_edited"] is False


def test_crosswalk_separates_proof_from_binary64_code(validator: ModuleType) -> None:
    rows = validator.expected_record()["proof_code_crosswalk"]
    assert [row["ordinal"] for row in rows] == list(range(4))
    assert [row["symbol"] for row in rows] == [
        "conditional_initial_law", "_initial_kl", "ctmc_path_kl",
        "Theorem PO13.1",
    ]
    assert all(row["sufficient_for_real_domain_U0"] is False for row in rows)
    assert "BINARY64" in rows[0]["strength"]
    assert "GENERAL_MEASURE_THEOREM" in rows[3]["strength"]


def test_nonclaims_keep_po16_and_full_c17_open(validator: ModuleType) -> None:
    nonclaims = validator.expected_record()["scope_and_nonclaims"]
    assert nonclaims["proof_is_not_full_C17"] is True
    assert nonclaims["PO13_is_not_preregistration_field_F003"] is True
    assert nonclaims["PO16_discharged"] is False
    assert nonclaims["path_likelihood_decomposition_proved"] is False
    assert nonclaims["five_simultaneous_certificates_present"] is False
    assert nonclaims["runtime_or_scientific_execution_performed"] is False
    assert nonclaims["existing_project_file_modified"] is False
    assert nonclaims["gate_item_closure_would_mean_C17_viable"] is False
    assert nonclaims["gate_item_closure_would_mean_route_narrowed_only"] is True


def test_input_bindings_are_exact_and_source_symbols_are_ast_present(
    validator: ModuleType,
) -> None:
    assert [row["ordinal"] for row in validator.INPUT_BINDINGS] == list(range(9))
    assert validator.INPUT_BINDINGS[1]["record_sha256"] == (
        "18b695a4e10f6c7668176cf85ec6f6c32e30de5ec359128d9faf56a06d5394ef"
    )
    for row in validator.INPUT_BINDINGS:
        raw = (ROOT / row["path"]).read_bytes()
        assert len(raw) == row["bytes"]
        assert hashlib.sha256(raw).hexdigest() == row["raw_sha256"]
    validator._validate_inputs(ROOT)


def test_package_paths_are_additive_and_exclude_trackers(validator: ModuleType) -> None:
    package_paths = [row["path"] for row in validator.expected_record()["package_bindings"]]
    assert package_paths == [
        validator.HUMAN_PATH,
        validator.VALIDATOR_PATH,
        validator.TEST_PATH,
    ]
    assert "PROJECT_COMPLETION_TIMETABLE.md" not in package_paths
    assert "PROJECT_EVIDENCE_LEDGER.md" not in package_paths
    assert validator.MACHINE_PATH not in package_paths


def test_validator_imports_only_standard_library(validator: ModuleType) -> None:
    tree = ast.parse((ROOT / VALIDATOR_REL).read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    assert roots <= {
        "__future__", "ast", "decimal", "fractions", "hashlib", "json",
        "os", "pathlib", "stat", "typing",
    }
    assert "heterodiff" not in roots
    assert "numpy" not in roots
    assert "scipy" not in roots


def test_validation_is_deterministic_and_cwd_independent(
    validator: ModuleType, tmp_path: Path
) -> None:
    first = validator.validate()
    second = validator.validate()
    assert first == second
    command = [sys.executable, "-B", str(ROOT / VALIDATOR_REL)]
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    status = json.loads(completed.stdout)
    assert status["validation"] == "PASS"
    assert status["record_sha256"] == first["record_sha256"]


@pytest.mark.parametrize(
    ("pointer", "value"),
    [
        ("schema_version", "heterodiff-manuscript-v3-c17-po13-proof-v0"),
        ("state", "C17_PROVED"),
        ("global_state", "EXECUTABLE"),
        ("authority_provenance.normalized_visible_text_utf8_bytes", 208),
        ("authority_provenance.scientific_execution_authorized", True),
        ("theorem_scope.orientation", "KL(Q0||P0)"),
        ("theorem_scope.finite_state_required", True),
        ("proposition_register.1.status", "UNPROVED"),
        ("proposition_register.7.status", "PO16_DISCHARGED"),
        ("assumption_effects.2.status", "CLOSED"),
        ("proof_obligation_effects.12.closed_by_this_package", False),
        ("proof_obligation_effects.13.mathematical_derivation_discharged", True),
        ("proof_obligation_effects.15.status", "DISCHARGED"),
        ("finite_exact_witness.target_initial_p0.0", "1/2"),
        ("finite_exact_witness.all_dynamic_components_exactly_zero", False),
        ("smooth_terminal_matched_obstruction.K0_unbounded_as_n_tends_to_infinity", False),
        ("smooth_terminal_matched_obstruction.KC", "1"),
        ("conditional_U0_range_route.U0", 0.1),
        ("conditional_U0_range_route.actual_error_range_certificate_present", True),
        ("proof_code_crosswalk.0.sufficient_for_real_domain_U0", True),
        ("field_blocker_gate_effects.F003", "proof.md"),
        ("gate_A_route_narrowing_decision.decision", "C17_VIABLE"),
        (
            "gate_A_route_narrowing_decision.survival_conditions.0.requirement",
            "PO14_PROVED_WITH_A1_THROUGH_A10_AND_TARGET_FIRST_ORIENTATION",
        ),
        ("gate_A_route_narrowing_decision.survival_conditions.0.currently_satisfied", True),
        ("field_blocker_gate_effects.Gate_A_C17_viability_or_narrowing_item", "C17_VIABLE"),
        ("field_blocker_gate_effects.unresolved_field_count", 171),
        ("scope_and_nonclaims.proof_is_not_full_C17", False),
        ("scope_and_nonclaims.PO16_discharged", True),
        ("input_bindings.4.raw_sha256", "0" * 64),
        ("package_bindings.0.bytes", 1),
    ],
)
def test_semantic_or_binding_mutation_fails_closed_even_with_recomputed_digest(
    validator: ModuleType,
    tmp_path: Path,
    pointer: str,
    value: Any,
) -> None:
    root = _copy_package(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: _replace(record, pointer, value),
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_stale_self_digest_fails_closed(validator: ModuleType, tmp_path: Path) -> None:
    root = _copy_package(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: _replace(record, "state", "C17_PROVED"),
        recompute_digest=False,
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_noncanonical_machine_fails_closed(validator: ModuleType, tmp_path: Path) -> None:
    root = _copy_package(validator, tmp_path)
    _rewrite_machine(validator, root, lambda record: None, canonical=False)
    with pytest.raises(validator.ValidationError, match="not canonical"):
        validator.validate(root)


@pytest.mark.parametrize(
    "relative_path",
    [
        "PROJECT_C17_PO13_INITIALIZER_KL_PROOF.md",
        "research/diagnostics/manuscript_v3_c17_po13_initializer_kl_proof_v1.py",
        "tests/unit/test_manuscript_v3_c17_po13_initializer_kl_proof_v1.py",
        "manuscript_v3/c17_hybrid_path_error_theorem.md",
    ],
)
def test_bound_file_byte_drift_fails_closed(
    validator: ModuleType, tmp_path: Path, relative_path: str
) -> None:
    root = _copy_package(validator, tmp_path)
    path = root / relative_path
    path.write_bytes(path.read_bytes() + b"# drift\n")
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_source_symbol_removal_fails_ast_check_even_if_binding_is_rebased(
    validator: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _copy_package(validator, tmp_path)
    ordinal = 7
    original = validator.INPUT_BINDINGS[ordinal]
    path = root / original["path"]
    raw = path.read_bytes().replace(
        b"def conditional_initial_law(", b"def removed_initial_law(", 1
    )
    assert raw != path.read_bytes()
    path.write_bytes(raw)
    path.chmod(0o644)
    rebound = _rebind(validator, original, raw)
    rows = (*validator.INPUT_BINDINGS[:ordinal], rebound, *validator.INPUT_BINDINGS[ordinal + 1:])
    monkeypatch.setattr(validator, "INPUT_BINDINGS", rows)
    with pytest.raises(validator.ValidationError, match="expected source symbol absent"):
        validator._validate_inputs(root)


def test_predecessor_po13_promotion_fails_semantic_chain_even_if_rebound(
    validator: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _copy_package(validator, tmp_path)
    ordinal = 1
    original = validator.INPUT_BINDINGS[ordinal]
    path = root / original["path"]
    predecessor = json.loads(path.read_text(encoding="ascii"))
    predecessor["proof_obligation_register"][12]["status"] = "DISCHARGED"
    predecessor["proof_obligation_register"][12]["discharged"] = True
    predecessor["record_sha256"] = validator._foreign_record_sha256(predecessor)
    raw = validator.canonical_machine_bytes(predecessor)
    path.write_bytes(raw)
    path.chmod(0o644)
    rebound = _rebind(validator, original, raw)
    rebound["record_sha256"] = predecessor["record_sha256"]
    rows = (*validator.INPUT_BINDINGS[:ordinal], rebound, *validator.INPUT_BINDINGS[ordinal + 1:])
    monkeypatch.setattr(validator, "INPUT_BINDINGS", rows)
    with pytest.raises(validator.ValidationError, match="predecessor PO13 state mismatch"):
        validator._validate_inputs(root)


@pytest.mark.parametrize("bad", ["01", "2/2", " 1", "1/0", "", 1, True])
def test_noncanonical_or_invalid_exact_fraction_fails_closed(
    validator: ModuleType, bad: Any
) -> None:
    witness = dict(validator.EXPECTED_FINITE_WITNESS)
    witness["base_weights"] = [bad, "1/2"]
    with pytest.raises((validator.ValidationError, TypeError)):
        validator.evaluate_exact_witness(witness)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("target_initial_p0", ["1/2", "1/2"]),
        ("normalizer_z_h", "2"),
        ("exp_error_hhat_over_h", ["1", "3"]),
        ("target_over_plugin_density_ratio", ["1", "1"]),
    ],
)
def test_false_exact_witness_value_fails_reconstruction(
    validator: ModuleType, key: str, value: Any
) -> None:
    witness = dict(validator.EXPECTED_FINITE_WITNESS)
    witness[key] = value
    with pytest.raises(validator.ValidationError):
        validator.evaluate_exact_witness(witness)


def test_unsafe_relative_paths_are_rejected(validator: ModuleType) -> None:
    for value in ("../escape", "/absolute", "./relative", "a/../b", ""):
        with pytest.raises(validator.ValidationError):
            validator._safe_relative_path(ROOT, value)


@pytest.mark.parametrize("custody", ["mode", "symlink", "hardlink"])
def test_nonregular_or_nonowned_custody_fails_closed(
    validator: ModuleType,
    tmp_path: Path,
    custody: str,
) -> None:
    root = _copy_package(validator, tmp_path)
    path = root / validator.HUMAN_PATH
    if custody == "mode":
        path.chmod(0o600)
    elif custody == "symlink":
        target = root / "human-target.md"
        target.write_bytes(path.read_bytes())
        target.chmod(0o644)
        path.unlink()
        path.symlink_to(target)
    else:
        alias = root / "human-hardlink.md"
        os.link(path, alias)
    with pytest.raises(validator.ValidationError, match="custody"):
        validator.validate(root)
