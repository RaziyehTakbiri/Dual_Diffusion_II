"""Hostile no-execution checks for the external trained-checkpoint D1 lane."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "research"
    / "diagnostics"
    / "finite_association_trained_checkpoint_diagnostic.py"
)
SPEC = importlib.util.spec_from_file_location(
    "finite_association_trained_checkpoint_diagnostic_external", SOURCE
)
assert SPEC is not None and SPEC.loader is not None
D1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(D1)


def _probability_masses():
    masses = [1.0 / 21.0] * 20
    masses.append(1.0 - sum(masses))
    return masses


def _descriptor(value, *, dtype=np.float64):
    array = np.ascontiguousarray(np.asarray(value, dtype=dtype))
    return {
        "dtype": array.dtype.str,
        "shape": list(array.shape),
        "sha256": D1._array_sha256(array),
    }


def _valid_nonpath():
    zero_grid = _descriptor(np.zeros((33, 20, 21), dtype=np.float64))
    edge = {}
    for family, count in zip(D1.FAMILY_ORDER, D1.EXPECTED_FAMILY_EDGE_COUNTS):
        edge[family] = {
            "family": family,
            "active_edge_count": count,
            "physical_weight": 1.0,
            "physical_weighted_rmse": 0.0,
            "maximum_absolute_error": 0.0,
            "weighted_median_absolute_error": 0.0,
        }
    return {
        "parameter_sha256": D1.EXPECTED_PARAMETER_SHA256,
        "feature_sha256": D1.EXPECTED_FEATURE_SHA256,
        "classifier_sha256": D1.EXPECTED_CLASSIFIER_SHA256,
        "execution_receipt_sha256": D1.EXPECTED_INNER_SUCCESS_SHA256,
        "campaign_sha256": D1.EXPECTED_CAMPAIGN_SHA256,
        "production_bound": True,
        "classifier_logit_grid": dict(zero_grid),
        "log_information_grid": dict(zero_grid),
        "residual_log_grid": dict(zero_grid),
        "masked_excess_bce": {
            "train": 0.0,
            "validation": 0.0,
            "joint_interpolation": 0.0,
            "time_interpolation": 0.0,
            "pair_interpolation": 0.0,
            "latent_three": 0.0,
            "anchor_three": 0.0,
            "both_three": 0.0,
            "overflow": 0.0,
            "balanced_ood": 0.0,
        },
        "centered_log_information": {
            "physical_weighted_rmse": 0.0,
            "maximum_absolute_error": 0.0,
        },
        "residual": {
            "physical_weighted_rmse": 0.0,
            "maximum_absolute_error": 0.0,
            "candidate_minimum": 0.0,
            "candidate_maximum": 0.0,
            "candidate_range": 0.0,
            "oracle_minimum": 0.0,
            "oracle_maximum": 0.0,
            "oracle_range": 0.0,
        },
        "edge_log_rates": edge,
        "conditional_initial_tv": {
            "per_observation": _descriptor(np.zeros(21)),
            "observation_weighted_mean": 0.0,
            "retained_observation_weighted_mean": 0.0,
            "maximum": 0.0,
            "overflow": 0.0,
        },
        "calibration": {
            "brier": 0.0,
            "optimal_brier": 0.0,
            "excess_brier": 0.0,
            "reliability_ece": 0.0,
            "maximum_reliability_gap": 0.0,
            "bin_mass": _descriptor(np.zeros(10)),
            "bin_mean_prediction": _descriptor(np.zeros(10)),
            "bin_positive_frequency": _descriptor(np.zeros(10)),
        },
        "coherence": {
            "terminal_maximum_absolute_log_information_error": 0.0,
            "terminal_maximum_absolute_residual": 0.0,
            "generator_row_sum_maximum_absolute_residual": 0.0,
            "normalization_physical_weighted_rmse": 0.0,
            "normalization_maximum_absolute_residual": 0.0,
            "semigroup_physical_weighted_rmse": 0.0,
            "semigroup_maximum_absolute_residual": 0.0,
            "edit_cycle_maximum_absolute_residual": 0.0,
            "edit_cycle_count": 1,
        },
    }


def _valid_path_sections():
    masses = _probability_masses()
    references = []
    observations = []
    for index, mass in enumerate(masses):
        reference = {
            "frozen_fixture_sha256": D1.EXPECTED_FIXTURE_SHA256,
            "fixture_content_sha256": D1.EXPECTED_PATH_CONTENT_SHA256,
            "runtime": dict(D1.EXPECTED_PATH_RUNTIME),
            "reference_sha256": ("%x" % (index % 16)) * 64,
            "observation_index": index,
            "observation_mass": mass,
            "unconditional_path_kl": 1.0,
            "refined_unconditional_path_kl": 1.0,
            "primary_refined_unconditional_path_kl_change": 0.0,
            "oracle_self_path_kl": 0.0,
            "target_marginal_maximum_absolute_error": 0.0,
            "target_initial_normalizer": 1.0,
            "target_initial_law": _descriptor(np.zeros(20)),
            "target_generator_grid": _descriptor(np.zeros((33, 20, 20))),
            "primary_solver_settings": dict(D1.EXPECTED_PRIMARY_SOLVER_SETTINGS),
            "refined_solver_settings": dict(D1.EXPECTED_REFINED_SOLVER_SETTINGS),
            "oracle_self_potential_evaluations": 1,
            "unconditional_potential_evaluations": 1,
            "refined_unconditional_potential_evaluations": 1,
        }
        references.append(reference)
        observations.append(
            {
                "parameter_sha256": D1.EXPECTED_PARAMETER_SHA256,
                "classifier_sha256": D1.EXPECTED_CLASSIFIER_SHA256,
                "execution_receipt_sha256": D1.EXPECTED_INNER_SUCCESS_SHA256,
                "campaign_sha256": D1.EXPECTED_CAMPAIGN_SHA256,
                "production_bound": True,
                "reference": reference,
                "candidate_initial_normalizer": 1.0,
                "candidate_initial_law": _descriptor(np.zeros(20)),
                "candidate_generator_grid": _descriptor(np.zeros((33, 20, 20))),
                "target_marginals": _descriptor(np.zeros((33, 20))),
                "candidate_marginals": _descriptor(np.zeros((33, 20))),
                "target_integrated_occupation": _descriptor(np.zeros(20)),
                "candidate_integrated_occupation": _descriptor(np.zeros(20)),
                "marginal_total_variation": _descriptor(np.zeros(33)),
                "path_kl_initial": 0.0,
                "path_kl_dynamic": 0.0,
                "path_kl_total": 0.0,
                "normalized_path_kl": 0.0,
                "maximum_intermediate_total_variation": 0.0,
                "endpoint_total_variation": 0.0,
                "primary_refined_path_kl_change": 0.0,
                "primary_refined_endpoint_total_variation": 0.0,
                "primary_path_quadrature_error": 0.0,
                "refined_path_quadrature_error": 0.0,
                "primary_target_marginal_maximum_absolute_error": 0.0,
                "primary_solver_settings": dict(
                    D1.EXPECTED_PRIMARY_SOLVER_SETTINGS
                ),
                "refined_solver_settings": dict(
                    D1.EXPECTED_REFINED_SOLVER_SETTINGS
                ),
                "primary_path_potential_evaluations": 1,
                "refined_path_potential_evaluations": 1,
                "primary_candidate_occupancy_potential_evaluations": 1,
                "refined_candidate_occupancy_potential_evaluations": 1,
            }
        )
    reference_set_sha = D1._reference_set_record_sha256(references)
    preflight = {
        "frozen_fixture_sha256": D1.EXPECTED_FIXTURE_SHA256,
        "fixture_content_sha256": D1.EXPECTED_PATH_CONTENT_SHA256,
        "runtime": dict(D1.EXPECTED_PATH_RUNTIME),
        "primary_solver_settings": dict(D1.EXPECTED_PRIMARY_SOLVER_SETTINGS),
        "refined_solver_settings": dict(D1.EXPECTED_REFINED_SOLVER_SETTINGS),
        "references": references,
        "reference_set_sha256": reference_set_sha,
    }
    zeros = [0.0] * 21
    aggregate = {
        "parameter_sha256": D1.EXPECTED_PARAMETER_SHA256,
        "classifier_sha256": D1.EXPECTED_CLASSIFIER_SHA256,
        "execution_receipt_sha256": D1.EXPECTED_INNER_SUCCESS_SHA256,
        "campaign_sha256": D1.EXPECTED_CAMPAIGN_SHA256,
        "production_bound": True,
        "reference_set_sha256": reference_set_sha,
        "observations": observations,
        "observation_mass": _descriptor(masses),
        "path_kl_per_observation": _descriptor(zeros),
        "unconditional_path_kl_per_observation": _descriptor([1.0] * 21),
        "normalized_path_kl_per_observation": _descriptor(zeros),
        "endpoint_total_variation_per_observation": _descriptor(zeros),
        "maximum_intermediate_total_variation_per_observation": _descriptor(zeros),
        "observation_weighted_path_kl": 0.0,
        "retained_path_kl_mean": 0.0,
        "retained_normalized_path_score": 0.0,
        "overflow_path_kl": 0.0,
        "overflow_normalized_path_score": 0.0,
        "observation_weighted_endpoint_total_variation": 0.0,
        "retained_endpoint_total_variation_mean": 0.0,
        "overflow_endpoint_total_variation": 0.0,
        "ambiguous_observation_indices": _descriptor(
            np.asarray((8, 7, 5), dtype=np.int64), dtype=np.int64
        ),
        "ambiguous_normalized_path_kl": _descriptor([0.0, 0.0, 0.0]),
        "ambiguous_normalized_path_score": 0.0,
        "numerical_gate_failures": [],
    }
    return preflight, aggregate


def _valid_family_supplement():
    masses = _probability_masses()
    rows = []
    for index, mass in enumerate(masses):
        components = []
        metadata = (
            ("APPLICABLE", "EXACT_CONDITIONED_TARGET_INITIAL_LAW", 0, True),
            (D1.CONTINUOUS_DISPOSITION, D1.CONTINUOUS_DISPOSITION, 0, False),
            (
                "APPLICABLE",
                "EXACT_CONDITIONED_TARGET_OCCUPATION",
                D1.EXPECTED_FAMILY_EDGE_COUNTS[0],
                True,
            ),
            (
                "APPLICABLE",
                "EXACT_CONDITIONED_TARGET_OCCUPATION",
                D1.EXPECTED_FAMILY_EDGE_COUNTS[1],
                True,
            ),
            (
                "APPLICABLE",
                "EXACT_CONDITIONED_TARGET_OCCUPATION",
                D1.EXPECTED_FAMILY_EDGE_COUNTS[2],
                True,
            ),
        )
        for position, values in enumerate(metadata):
            applicability, target, edge_count, entered = values
            components.append(
                {
                    "component_id": D1.COMPONENT_ORDER[position],
                    "applicability": applicability,
                    "target_measure": target,
                    "primary": None if position == 1 else 0.0,
                    "refined": None if position == 1 else 0.0,
                    "primary_refined_absolute_difference": (
                        None if position == 1 else 0.0
                    ),
                    "active_aggregate_edge_count": edge_count,
                    "entered_total": entered,
                    "interval_certified": False,
                }
            )
        rows.append(
            {
                "observation_index": index,
                "observation_mass": mass,
                "components": components,
                "primary_family_orientation": (
                    "KL(P_REFERENCE_H || P_CANDIDATE_H_HAT)"
                ),
                "refined_family_orientation": (
                    "KL(P_REFERENCE_H || P_CANDIDATE_H_HAT)"
                ),
                "primary_family_supplied_reference_marginal_used": True,
                "refined_family_supplied_reference_marginal_used": True,
                "primary_dynamic": 0.0,
                "primary_total": 0.0,
                "refined_dynamic": 0.0,
                "refined_total": 0.0,
                "separate_primary_aggregate_initial": 0.0,
                "separate_primary_aggregate_dynamic": 0.0,
                "separate_primary_aggregate_total": 0.0,
                "separate_refined_aggregate_initial": 0.0,
                "separate_refined_aggregate_dynamic": 0.0,
                "separate_refined_aggregate_total": 0.0,
                "public_primary_aggregate_initial": 0.0,
                "public_primary_aggregate_dynamic": 0.0,
                "public_primary_aggregate_total": 0.0,
                "refinements": {name: 0.0 for name in D1.FAMILY_REFINEMENT_NAMES},
                "crosschecks": {name: 0.0 for name in D1.FAMILY_CROSSCHECK_NAMES},
                "target_marginal_maximum_absolute_error": 0.0,
                "primary_family_occupancy_target_maximum_absolute_error": 0.0,
                "refined_family_occupancy_target_maximum_absolute_error": 0.0,
                "terminal_log_potential_maximum_absolute_error": 0.0,
                "primary_family_quadrature_error_estimate": 0.0,
                "refined_family_quadrature_error_estimate": 0.0,
                "numerical_failures": [],
            }
        )
    return {
        "schema_version": "heterodiff-a1-trained-family-supplement-v1",
        "orientation": "KL(P_EXACT_TARGET_H || P_TRAINED_CHECKPOINT_H_HAT)",
        "family_names": list(D1.FAMILY_ORDER),
        "component_order": list(D1.COMPONENT_ORDER),
        "active_edge_counts": list(D1.EXPECTED_FAMILY_EDGE_COUNTS),
        "edge_family_partition_sha256": D1.EXPECTED_FAMILY_PARTITION_SHA256,
        "continuous_component_disposition": D1.CONTINUOUS_DISPOSITION,
        "observation_count": 21,
        "observations": rows,
        "observation_weighted_initial": 0.0,
        "observation_weighted_birth": 0.0,
        "observation_weighted_death": 0.0,
        "observation_weighted_replacement": 0.0,
        "observation_weighted_total": 0.0,
        "maximum_primary_refined_component_change": 0.0,
        "maximum_family_aggregate_crosscheck_absolute_difference": 0.0,
        "maximum_target_marginal_absolute_error": 0.0,
        "maximum_terminal_log_potential_absolute_error": 0.0,
        "interval_certified": False,
        "rigorous_numerical_enclosure_present": False,
        "numerical_failures": [],
    }


def _valid_record(attempt=None):
    marker = attempt or {
        "path": D1.ATTEMPT_MARKER_RELATIVE_PATH,
        "state": "ATTEMPT_CONSUMED_NONRETRYABLE",
        "attempt_number": 1,
        "raw_sha256": "1" * 64,
        "record_sha256": "2" * 64,
    }
    preflight, aggregate = _valid_path_sections()
    record = {
        "schema_version": D1.SCHEMA_VERSION,
        "lane_id": D1.LANE_ID,
        "status": D1.STATUS,
        "scope": D1.SCOPE,
        "worker_request_sha256": "3" * 64,
        "implementation_sha256": "4" * 64,
        "freeze_sha256": "5" * 64,
        "human_freeze_sha256": "6" * 64,
        "attempt_marker": marker,
        "checkpoint_custody": {
            "source_artifact_root": D1.V2_ARTIFACT_RELATIVE_PATH,
            "outer_success_receipt_raw_sha256": (
                D1.EXPECTED_OUTER_RECEIPT_RAW_SHA256
            ),
            "outer_success_receipt_self_sha256": (
                D1.EXPECTED_OUTER_RECEIPT_SELF_SHA256
            ),
            "inner_success_receipt_sha256": D1.EXPECTED_INNER_SUCCESS_SHA256,
            "campaign_sha256": D1.EXPECTED_CAMPAIGN_SHA256,
            "run_key_sha256": D1.EXPECTED_RUN_KEY_SHA256,
            "checkpoint_sha256": D1.EXPECTED_CHECKPOINT_SHA256,
            "parameter_sha256": D1.EXPECTED_PARAMETER_SHA256,
            "feature_sha256": D1.EXPECTED_FEATURE_SHA256,
            "classifier_sha256": D1.EXPECTED_CLASSIFIER_SHA256,
            "certificate_sha256": D1.EXPECTED_CERTIFICATE_SHA256,
            "execution_runtime_sha256": D1.EXPECTED_EXECUTION_RUNTIME_SHA256,
            "source_sha256": D1.EXPECTED_SOURCE_SHA256,
            "configuration_sha256": D1.EXPECTED_CONFIGURATION_SHA256,
            "preflight_sha256": D1.EXPECTED_PREFLIGHT_SHA256,
            "fixture_sha256": D1.EXPECTED_FIXTURE_SHA256,
            "path_content_sha256": D1.EXPECTED_PATH_CONTENT_SHA256,
            "path_runtime_sha256": D1.EXPECTED_PATH_RUNTIME_SHA256,
            "coordinate": dict(D1.EXPECTED_COORDINATE),
            "optimizer_steps_taken": D1.EXPECTED_UPDATES,
            "checkpoint_was_loaded_through_canonical_success_ledger": True,
            "checkpoint_was_revalidated_after_diagnostics": True,
        },
        "coverage": {
            "all_33_nonpath_evaluated": True,
            "all_21_path_reference_preflight_passed": True,
            "all_21_aggregate_path_evaluated": True,
            "all_21_family_supplement_evaluated": True,
            "canonical_observation_order_used": True,
            "evidence_binder_completed": True,
        },
        "family_supplement": _valid_family_supplement(),
        "runtime": {
            "python": "3.11.5",
            "numpy": "2.4.6",
            "path_runtime": dict(D1.EXPECTED_PATH_RUNTIME),
            "path_runtime_sha256": D1.EXPECTED_PATH_RUNTIME_SHA256,
            "thread_environment": {name: "1" for name in D1._THREAD_VARIABLES},
            "pythonhashseed": "0",
            "cuda_visible_devices": "",
            "capsule_source_only": True,
        },
        "nonpath": _valid_nonpath(),
        "path_reference_preflight": preflight,
        "aggregate_path": aggregate,
        "evidence_binding": {
            "coordinate": [
                D1.EXPECTED_COORDINATE["seed"],
                D1.EXPECTED_COORDINATE["budget"],
                D1.EXPECTED_COORDINATE["method"],
            ],
            "run_key_sha256": D1.EXPECTED_RUN_KEY_SHA256,
            "success_receipt_sha256": D1.EXPECTED_INNER_SUCCESS_SHA256,
            "campaign_sha256": D1.EXPECTED_CAMPAIGN_SHA256,
            "parameter_sha256": D1.EXPECTED_PARAMETER_SHA256,
            "feature_sha256": D1.EXPECTED_FEATURE_SHA256,
            "classifier_sha256": D1.EXPECTED_CLASSIFIER_SHA256,
            "certificate_sha256": D1.EXPECTED_CERTIFICATE_SHA256,
            "optimizer_steps_taken": D1.EXPECTED_UPDATES,
            "nonpath_identity_matches": True,
            "aggregate_path_identity_matches": True,
            "internal_analysis_only": True,
        },
        "numerical_disposition": {
            "primary_refined_limit": D1.PRIMARY_REFINED_LIMIT,
            "family_aggregate_crosscheck_limit": D1.FAMILY_AGGREGATE_LIMIT,
            "target_marginal_limit": D1.TARGET_MARGINAL_LIMIT,
            "terminal_limit": D1.TERMINAL_LIMIT,
            "nonpath_terminal_log_limit": D1.NONPATH_TERMINAL_LOG_LIMIT,
            "nonpath_coherence_limit": D1.NONPATH_COHERENCE_LIMIT,
            "all_required_checks_passed": True,
            "adaptive_float64_not_interval_proof": True,
        },
        "nonclaims": {
            "scientific_result_eligible": False,
            "production_checkpoint": False,
            "production_order_admissible": False,
            "confirmatory_execution_authorized": False,
            "qualifies_r1": False,
            "qualifies_r2": False,
            "closes_c17": False,
            "c17_theorem_proved": False,
            "manuscript_claim_promoted": False,
            "real_domain_evidence": False,
            "continuous_coordinate_energy_exercised": False,
            "occurrence_attached_mark_fibers_exercised": False,
            "rigorous_numerical_enclosure_present": False,
            "interval_certified": False,
            "training_performed_by_diagnostic": False,
            "checkpoint_selected_by_diagnostic": False,
        },
    }
    record["diagnostic_record_sha256"] = D1._self_digest(
        record,
        field="diagnostic_record_sha256",
        domain=D1._RECORD_DOMAIN,
    )
    return record


def _rehash(record):
    record["diagnostic_record_sha256"] = D1._self_digest(
        record,
        field="diagnostic_record_sha256",
        domain=D1._RECORD_DOMAIN,
    )
    return record


def test_external_lane_paths_and_status_are_exact():
    assert D1.IMPLEMENTATION_RELATIVE_PATH.startswith("research/diagnostics/")
    assert not D1.IMPLEMENTATION_RELATIVE_PATH.startswith("src/")
    assert D1.TEST_RELATIVE_PATH == (
        "tests/unit/test_finite_association_trained_checkpoint_diagnostic.py"
    )
    assert D1.OUTPUT_RELATIVE_PATH == (
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1"
    )
    assert D1.ATTEMPT_MARKER_RELATIVE_PATH == (
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1.attempt.json"
    )
    assert D1.STATUS == "COMPLETE_FINITE_KNOWN_LAW_DIAGNOSTIC"
    assert D1.SCOPE == "TRAINED_DEVELOPMENT_CHECKPOINT_DIAGNOSTIC_ONLY"


def test_source_has_no_training_or_checkpoint_write_entry_point():
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "execute_frozen_association_residual_training",
        "prepare_frozen_association_residual_training",
        "launch_frozen_association_sampled_run",
        "torch.optim",
        "torch.save",
        "load_state_dict",
    )
    assert all(token not in text for token in forbidden)
    tree = ast.parse(text)
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "execute_once" in calls
    assert not ({"fit", "train", "backward", "step"} & calls)
    imports = {
        node.module: {alias.name for alias in node.names}
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        in {
            "heterodiff.experiments.finite_association_residual_training_torch",
            "heterodiff.experiments.finite_association_isolated_runner",
        }
    }
    assert imports[
        "heterodiff.experiments.finite_association_residual_training_torch"
    ] == {
        "bind_fitted_association_checkpoint_evaluator",
        "configure_frozen_association_training_environment",
    }
    assert imports[
        "heterodiff.experiments.finite_association_isolated_runner"
    ] == {
        "load_successful_frozen_association_checkpoint",
        "revalidate_successful_frozen_association_checkpoint",
    }


def test_worker_revalidates_checkpoint_and_evaluator_between_major_phases():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    worker = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_worker_record"
    )

    def call_name(node):
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    calls = sorted(
        (
            (node.lineno, call_name(node))
            for node in ast.walk(worker)
            if isinstance(node, ast.Call)
        ),
        key=lambda item: item[0],
    )
    phase_names = (
        "evaluate_finite_association_nonpath",
        "build_frozen_association_path_references",
        "evaluate_finite_association_paths",
        "bind_frozen_association_sampled_run_evidence",
        "_family_supplement",
    )
    phase_lines = [next(line for line, name in calls if name == phase) for phase in phase_names]
    revalidation_lines = [
        line
        for line, name in calls
        if name == "revalidate_successful_frozen_association_checkpoint"
    ]
    integrity_lines = [line for line, name in calls if name == "assert_integrity"]
    boundaries = list(zip(phase_lines, phase_lines[1:])) + [
        (phase_lines[-1], worker.end_lineno + 1)
    ]
    for start, end in boundaries:
        assert any(start < line < end for line in revalidation_lines)
        assert any(start < line < end for line in integrity_lines)


def test_machine_freeze_has_single_attempt_and_all_nonclaims():
    freeze = json.loads(
        (ROOT / D1.FREEZE_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    attempt = freeze["attempt_policy"]
    assert attempt["attempt_count"] == 1
    assert attempt["retry_permitted"] is False
    assert attempt["resume_permitted"] is False
    assert attempt["durable_attempt_marker_path"] == (
        D1.ATTEMPT_MARKER_RELATIVE_PATH
    )
    assert attempt["marker_committed_before_worker_launch"] is True
    assert freeze["training_boundary"]["training_permitted"] is False
    assert freeze["training_boundary"]["optimizer_update_count"] == 0
    assert freeze["scientific_boundary"]["qualifies_r1"] is False
    assert freeze["scientific_boundary"]["qualifies_r2"] is False
    assert freeze["scientific_boundary"]["c17_closed"] is False
    assert freeze["scientific_boundary"]["claim_promotion"] is False
    assert freeze["family_supplement"][
        "aggregate_dynamic_crosscheck_maximum_absolute_difference"
    ] == D1.FAMILY_AGGREGATE_LIMIT


def test_real_v2_outer_custody_reopens_without_execution():
    before = D1._file_sha256(
        ROOT / D1.V2_ARTIFACT_RELATIVE_PATH / "success-receipt.json"
    )
    custody = D1._validate_outer_v2_custody(ROOT)
    after = D1._file_sha256(
        ROOT / D1.V2_ARTIFACT_RELATIVE_PATH / "success-receipt.json"
    )
    assert before == after == D1.EXPECTED_OUTER_RECEIPT_RAW_SHA256
    assert custody["inventory_sha256"] == D1.EXPECTED_OUTER_INVENTORY_SHA256
    assert len(custody["inventory"]) == 272


def test_final_freeze_bindings_and_audit_are_no_worker_only(monkeypatch):
    def forbidden_worker(*args, **kwargs):
        raise AssertionError("audit attempted to launch a worker")

    monkeypatch.setattr(D1.subprocess, "run", forbidden_worker)
    freeze = D1._validate_machine_freeze(ROOT)
    readiness = D1.audit_ready(ROOT)
    assert readiness["ready"] is True
    assert readiness["training_permitted"] is False
    assert readiness["implementation_sha256"] == freeze["implementation_sha256"]
    assert readiness["test_sha256"] == freeze["test_sha256"]
    assert readiness["human_freeze_sha256"] == freeze["human_freeze_sha256"]


def test_worker_command_is_exact_safe_path_and_capsule_environment(monkeypatch):
    command = D1._worker_command(ROOT)
    assert command[1:3] == ("-P", "-B")
    assert Path(command[3]) == SOURCE
    assert command[4] == "--worker"
    monkeypatch.setenv("PYTHONHOME", "/hostile")
    monkeypatch.setenv("PYTHONPATH", "/hostile")
    environment = D1._worker_environment(ROOT, "a" * 64)
    assert environment["PYTHONPATH"] == str(
        ROOT / D1.V2_CAPSULE_RELATIVE_PATH / "src"
    )
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
    assert environment["PYTHONSAFEPATH"] == "1"
    assert environment["PYTHONHASHSEED"] == "0"
    assert environment["CUDA_VISIBLE_DEVICES"] == ""
    assert all(environment[name] == "1" for name in D1._THREAD_VARIABLES)
    assert environment.get("PYTHONHOME") is None


def test_capsule_dataclass_schemas_match_validators_without_evaluation():
    script = r'''
import importlib.util
import json
import sys
from dataclasses import fields
from types import SimpleNamespace

from heterodiff.evaluation.finite_association_decision import (
    FrozenAssociationSampledRunEvidence,
)
from heterodiff.evaluation.finite_association_path_evaluator import (
    FiniteAssociationObservationPathEvaluation,
    FiniteAssociationPathEvaluation,
    FiniteAssociationPathRuntime,
    FiniteAssociationPathSolverSettings,
    FrozenAssociationPathReference,
    FrozenAssociationPathReferenceSet,
    PRIMARY_PATH_SOLVER_SETTINGS,
    REFINED_PATH_SOLVER_SETTINGS,
    _solver_settings_sha256,
)
from heterodiff.evaluation.finite_association_residual_evaluator import (
    CoherenceDiagnostics,
    FiniteAssociationNonPathEvaluation,
)

spec = importlib.util.spec_from_file_location("d1_external_schema_probe", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
coherence = CoherenceDiagnostics(
    terminal_maximum_absolute_log_information_error=0.0,
    terminal_maximum_absolute_residual=0.0,
    generator_row_sum_maximum_absolute_residual=0.0,
    normalization_physical_weighted_rmse=0.0,
    normalization_maximum_absolute_residual=0.0,
    semigroup_physical_weighted_rmse=0.0,
    semigroup_maximum_absolute_residual=0.0,
    edit_cycle_maximum_absolute_residual=0.0,
    edit_cycle_count=1,
)
module._require_worker_nonpath_gates(SimpleNamespace(coherence=coherence))

def visible(cls):
    return [
        field.name
        for field in fields(cls)
        if not field.name.startswith("_") and "elapsed_" not in field.name
    ]

print(json.dumps({
    "nonpath": visible(FiniteAssociationNonPathEvaluation),
    "reference": visible(FrozenAssociationPathReference),
    "reference_set": visible(FrozenAssociationPathReferenceSet),
    "aggregate": visible(FiniteAssociationPathEvaluation),
    "observation": visible(FiniteAssociationObservationPathEvaluation),
    "runtime": visible(FiniteAssociationPathRuntime),
    "solver": visible(FiniteAssociationPathSolverSettings),
    "evidence": visible(FrozenAssociationSampledRunEvidence),
    "primary_solver_sha256": _solver_settings_sha256(PRIMARY_PATH_SOLVER_SETTINGS),
    "refined_solver_sha256": _solver_settings_sha256(REFINED_PATH_SOLVER_SETTINGS),
    "runtime_sha256": FiniteAssociationPathRuntime.current().sha256,
}, sort_keys=True))
'''
    environment = D1._worker_environment(ROOT, "a" * 64)
    completed = subprocess.run(
        [str(ROOT / D1.TARGET_PYTHON_RELATIVE_PATH), "-P", "-B", "-c", script, str(SOURCE)],
        cwd=str(ROOT / D1.V2_CAPSULE_RELATIVE_PATH),
        env=environment,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    schemas = json.loads(completed.stdout)
    assert set(schemas["nonpath"]) == D1.NONPATH_RECORD_FIELDS
    assert set(schemas["reference"]) == D1.PATH_REFERENCE_FIELDS
    assert set(schemas["reference_set"]) == D1.PATH_REFERENCE_SET_FIELDS
    assert set(schemas["aggregate"]) == D1.AGGREGATE_PATH_FIELDS
    assert set(schemas["observation"]) == D1.AGGREGATE_OBSERVATION_FIELDS
    assert set(schemas["runtime"]) == D1.PATH_RUNTIME_FIELDS
    assert set(schemas["solver"]) == D1.PATH_SOLVER_FIELDS
    assert schemas["primary_solver_sha256"] == D1._solver_settings_record_sha256(
        D1.EXPECTED_PRIMARY_SOLVER_SETTINGS
    )
    assert schemas["refined_solver_sha256"] == D1._solver_settings_record_sha256(
        D1.EXPECTED_REFINED_SOLVER_SETTINGS
    )
    assert schemas["runtime_sha256"] == D1.EXPECTED_PATH_RUNTIME_SHA256
    evidence_fields = set(schemas["evidence"])
    assert D1.EVIDENCE_BINDING_SOURCE_FIELDS <= evidence_fields
    assert {"seed", "budget", "method"} <= evidence_fields
    assert D1.EVIDENCE_BINDING_FIELDS == D1.EVIDENCE_BINDING_SOURCE_FIELDS | {
        "coordinate",
        "nonpath_identity_matches",
        "aggregate_path_identity_matches",
        "internal_analysis_only",
    }


def test_attempt_marker_is_durable_exclusive_and_contains_no_totals(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    marker = D1._consume_attempt(
        tmp_path,
        freeze_sha256="a" * 64,
        implementation_sha256="b" * 64,
        test_sha256="c" * 64,
        human_freeze_sha256="d" * 64,
    )
    path = tmp_path / D1.ATTEMPT_MARKER_RELATIVE_PATH
    assert path.is_file() and not path.is_symlink()
    saved = json.loads(path.read_text(encoding="ascii"))
    assert saved["state"] == "ATTEMPT_CONSUMED_NONRETRYABLE"
    assert saved["retry_permitted"] is False
    assert saved["resume_permitted"] is False
    assert not any("total" in key or "metric" in key for key in saved)
    D1._require_attempt_marker_unchanged(tmp_path, marker)
    with pytest.raises(D1.DiagnosticRefusal, match="already consumed"):
        D1._consume_attempt(
            tmp_path,
            freeze_sha256="a" * 64,
            implementation_sha256="b" * 64,
            test_sha256="c" * 64,
            human_freeze_sha256="d" * 64,
        )


def test_attempt_marker_tamper_is_terminally_detected(tmp_path):
    (tmp_path / "artifacts").mkdir()
    marker = D1._consume_attempt(
        tmp_path,
        freeze_sha256="a" * 64,
        implementation_sha256="b" * 64,
        test_sha256="c" * 64,
        human_freeze_sha256="d" * 64,
    )
    path = tmp_path / D1.ATTEMPT_MARKER_RELATIVE_PATH
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(D1.DiagnosticRefusal, match="changed"):
        D1._require_attempt_marker_unchanged(tmp_path, marker)


def test_attempt_marker_symlink_cannot_be_reused(tmp_path):
    (tmp_path / "artifacts").mkdir()
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="ascii")
    marker = tmp_path / D1.ATTEMPT_MARKER_RELATIVE_PATH
    marker.symlink_to(target)
    with pytest.raises(D1.DiagnosticRefusal, match="already consumed"):
        D1._consume_attempt(
            tmp_path,
            freeze_sha256="a" * 64,
            implementation_sha256="b" * 64,
            test_sha256="c" * 64,
            human_freeze_sha256="d" * 64,
        )


def test_worker_subprocess_protocol_is_mocked_and_never_executes(monkeypatch):
    attempt = {
        "path": D1.ATTEMPT_MARKER_RELATIVE_PATH,
        "state": "ATTEMPT_CONSUMED_NONRETRYABLE",
        "attempt_number": 1,
        "nonce": "d" * 64,
        "raw_sha256": "1" * 64,
        "record_sha256": "2" * 64,
    }
    observed = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed.update(kwargs)
        request = json.loads(kwargs["input"].decode("ascii"))
        request_sha = hashlib.sha256(
            D1._WORKER_REQUEST_DOMAIN + D1._canonical_json_bytes(request)
        ).hexdigest()
        record = _valid_record(
            {key: attempt[key] for key in attempt if key != "nonce"}
        )
        record["worker_request_sha256"] = request_sha
        _rehash(record)
        return SimpleNamespace(
            returncode=0,
            stdout=D1._canonical_json_bytes(record) + b"\n",
            stderr=b"",
        )

    monkeypatch.setattr(D1.subprocess, "run", fake_run)
    result = D1._run_worker_subprocess(
        ROOT,
        implementation_sha256="a" * 64,
        freeze_sha256="b" * 64,
        human_freeze_sha256="c" * 64,
        attempt_marker=attempt,
    )
    assert result["status"] == D1.STATUS
    assert observed["command"][1:3] == ("-P", "-B")
    assert observed["cwd"] == str(ROOT / D1.V2_CAPSULE_RELATIVE_PATH)
    assert observed["check"] is False
    assert observed["env"]["PYTHONPATH"] == str(
        ROOT / D1.V2_CAPSULE_RELATIVE_PATH / "src"
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (lambda value: value.update(status="PARTIAL_COMPONENT_DIAGNOSTIC"), "identity"),
        (
            lambda value: value["coverage"].update(
                all_21_family_supplement_evaluated=False
            ),
            "coverage",
        ),
        (
            lambda value: value["family_supplement"].update(observation_count=20),
            "family",
        ),
        (
            lambda value: value["nonclaims"].update(qualifies_r1=True),
            "promotion",
        ),
    ),
)
def test_worker_record_rejects_partial_coverage_and_promotions(mutation, message):
    record = _valid_record()
    mutation(record)
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match=message):
        D1._validate_worker_record(record)


def test_worker_record_rejects_digest_tamper():
    record = _valid_record()
    record["checkpoint_custody"]["checkpoint_sha256"] = "0" * 64
    with pytest.raises(D1.DiagnosticRefusal, match="self-digest"):
        D1._validate_worker_record(record)


def test_worker_record_accepts_only_complete_ordered_family_rows():
    D1._validate_worker_record(_valid_record())


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (
            lambda family: family["observations"].__setitem__(
                slice(0, 2), list(reversed(family["observations"][:2]))
            ),
            "observation order",
        ),
        (
            lambda family: family["observations"][0]["components"].pop(),
            "five ordered components",
        ),
        (
            lambda family: family["observations"][0].update(
                primary_family_occupancy_target_maximum_absolute_error=1.1e-8
            ),
            "target-marginal gate",
        ),
        (
            lambda family: family.update(observation_weighted_total=0.1),
            "weighted summaries",
        ),
        (
            lambda family: family["observations"][0].update(extra_claim=True),
            "row schema",
        ),
    ),
)
def test_family_validator_rejects_incomplete_or_hostile_rows(mutation, message):
    record = _valid_record()
    mutation(record["family_supplement"])
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match=message):
        D1._validate_worker_record(record)


def test_family_validator_rejects_total_only_cancellation():
    record = _valid_record()
    row = record["family_supplement"]["observations"][0]
    # Family (1 initial + 1 dynamic) and separate (0 initial + 2 dynamic)
    # totals agree. Component crosschecks must still reject the cancellation.
    for field in ("primary", "refined"):
        row["components"][0][field] = 1.0
        row["components"][2][field] = 1.0
    row.update(
        primary_dynamic=1.0,
        primary_total=2.0,
        refined_dynamic=1.0,
        refined_total=2.0,
        separate_primary_aggregate_dynamic=2.0,
        separate_primary_aggregate_total=2.0,
        separate_refined_aggregate_dynamic=2.0,
        separate_refined_aggregate_total=2.0,
        public_primary_aggregate_dynamic=2.0,
        public_primary_aggregate_total=2.0,
    )
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match="crosschecks"):
        D1._validate_worker_record(record)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        (
            "terminal_maximum_absolute_log_information_error",
            1.0000001e-12,
        ),
        ("terminal_maximum_absolute_residual", 1.0000001e-10),
        ("generator_row_sum_maximum_absolute_residual", 1.0000001e-10),
        ("edit_cycle_maximum_absolute_residual", 1.0000001e-10),
    ),
)
def test_worker_record_rejects_each_nonpath_frozen_gate(field, value):
    record = _valid_record()
    record["nonpath"]["coherence"][field] = value
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match="nonpath frozen numerical gate"):
        D1._validate_worker_record(record)


@pytest.mark.parametrize(
    ("section", "message"),
    (
        ("runtime", "execution runtime record"),
        ("nonpath", "nonpath record schema"),
        ("path_reference_preflight", "path-reference preflight schema"),
        ("aggregate_path", "aggregate path schema"),
        ("evidence_binding", "evidence binding"),
    ),
)
def test_coverage_flags_cannot_substitute_for_empty_records(section, message):
    record = _valid_record()
    record[section] = {}
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match=message):
        D1._validate_worker_record(record)


def test_nonpath_mandatory_group_and_grid_shape_cannot_be_omitted_or_forged():
    record = _valid_record()
    del record["nonpath"]["calibration"]
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match="nonpath record schema"):
        D1._validate_worker_record(record)

    record = _valid_record()
    record["nonpath"]["classifier_logit_grid"]["shape"] = [33, 20, 20]
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match="array descriptor"):
        D1._validate_worker_record(record)


def test_reference_and_aggregate_observation_reordering_is_rejected():
    record = _valid_record()
    references = record["path_reference_preflight"]["references"]
    references[0], references[1] = references[1], references[0]
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match="reference identity"):
        D1._validate_worker_record(record)

    record = _valid_record()
    observations = record["aggregate_path"]["observations"]
    observations[0], observations[1] = observations[1], observations[0]
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match="observation identity"):
        D1._validate_worker_record(record)


def test_aggregate_digest_observation_field_and_evidence_identity_are_closed():
    record = _valid_record()
    record["aggregate_path"]["path_kl_per_observation"]["sha256"] = "0" * 64
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match="array digest"):
        D1._validate_worker_record(record)

    record = _valid_record()
    del record["aggregate_path"]["observations"][0]["path_kl_dynamic"]
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match="observation schema"):
        D1._validate_worker_record(record)

    record = _valid_record()
    record["evidence_binding"]["internal_analysis_only"] = False
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match="evidence binding"):
        D1._validate_worker_record(record)


@pytest.mark.parametrize(
    "payload",
    (
        b'{"value":NaN}',
        b'{"value":Infinity}',
        b'{"value":1e400}',
        b'{"value":1,"value":2}',
    ),
)
def test_json_parser_rejects_nonfinite_and_duplicate_members(payload):
    with pytest.raises(D1.DiagnosticRefusal):
        D1._parse_json_object(payload)


def test_worker_record_schema_is_closed_against_extra_overclaim():
    record = _valid_record()
    record["confirmatory_result"] = True
    _rehash(record)
    with pytest.raises(D1.DiagnosticRefusal, match="top-level schema"):
        D1._validate_worker_record(record)


def test_atomic_publish_writes_only_two_result_files_and_binds_marker(
    tmp_path, monkeypatch
):
    (tmp_path / "artifacts").mkdir()
    binding_calls = []
    launch_calls = []
    monkeypatch.setattr(
        D1,
        "_require_publication_binding_bytes",
        lambda *args, **kwargs: binding_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        D1,
        "_require_launch_bindings_unchanged",
        lambda *args, **kwargs: launch_calls.append((args, kwargs)),
    )
    attempt = {
        "raw_sha256": "1" * 64,
        "record_sha256": "2" * 64,
    }
    record = _valid_record()
    receipt = D1._publish_success(
        tmp_path,
        record,
        freeze_sha256="a" * 64,
        implementation_sha256="b" * 64,
        test_sha256="c" * 64,
        human_freeze_sha256="d" * 64,
        attempt_marker=attempt,
    )
    output = tmp_path / D1.OUTPUT_RELATIVE_PATH
    assert sorted(path.name for path in output.iterdir()) == [
        "diagnostic-record.json",
        "success-receipt.json",
    ]
    assert receipt["attempt_marker_raw_sha256"] == attempt["raw_sha256"]
    assert receipt["training_performed"] is False
    assert receipt["qualifies_r1"] is False
    assert receipt["qualifies_r2"] is False
    assert receipt["closes_c17"] is False
    assert len(binding_calls) == 2
    assert len(launch_calls) == 1
    with pytest.raises(D1.DiagnosticRefusal, match="already exists"):
        D1._publish_success(
            tmp_path,
            record,
            freeze_sha256="a" * 64,
            implementation_sha256="b" * 64,
            test_sha256="c" * 64,
            human_freeze_sha256="d" * 64,
            attempt_marker=attempt,
        )


def test_staging_binding_mutation_refuses_before_atomic_install(tmp_path, monkeypatch):
    (tmp_path / "artifacts").mkdir()
    calls = []

    def mutate_on_final_rehash(*args, **kwargs):
        calls.append((args, kwargs))
        if len(calls) == 2:
            raise D1.DiagnosticRefusal("simulated staging-window mutation")

    monkeypatch.setattr(D1, "_require_publication_binding_bytes", mutate_on_final_rehash)
    monkeypatch.setattr(
        D1, "_require_launch_bindings_unchanged", lambda *args, **kwargs: {}
    )
    with pytest.raises(D1.DiagnosticRefusal, match="staging-window mutation"):
        D1._publish_success(
            tmp_path,
            _valid_record(),
            freeze_sha256="a" * 64,
            implementation_sha256="b" * 64,
            test_sha256="c" * 64,
            human_freeze_sha256="d" * 64,
            attempt_marker={"raw_sha256": "1" * 64, "record_sha256": "2" * 64},
        )
    assert len(calls) == 2
    assert not os.path.lexists(tmp_path / D1.OUTPUT_RELATIVE_PATH)
    assert not any(".staging-" in path.name for path in (tmp_path / "artifacts").iterdir())


def test_publication_rehashes_all_four_bound_inputs(tmp_path):
    values = {
        D1.FREEZE_RELATIVE_PATH: b"freeze",
        D1.IMPLEMENTATION_RELATIVE_PATH: b"implementation",
        D1.TEST_RELATIVE_PATH: b"test",
        D1.HUMAN_FREEZE_RELATIVE_PATH: b"human",
    }
    for relative, payload in values.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    digests = {
        relative: hashlib.sha256(payload).hexdigest()
        for relative, payload in values.items()
    }
    arguments = {
        "freeze_sha256": digests[D1.FREEZE_RELATIVE_PATH],
        "implementation_sha256": digests[D1.IMPLEMENTATION_RELATIVE_PATH],
        "test_sha256": digests[D1.TEST_RELATIVE_PATH],
        "human_freeze_sha256": digests[D1.HUMAN_FREEZE_RELATIVE_PATH],
    }
    D1._require_publication_binding_bytes(tmp_path, **arguments)
    (tmp_path / D1.HUMAN_FREEZE_RELATIVE_PATH).write_bytes(b"changed")
    with pytest.raises(D1.DiagnosticRefusal, match="immediately before publication"):
        D1._require_publication_binding_bytes(tmp_path, **arguments)


def test_publish_refuses_symlink_output_without_touching_target(tmp_path):
    (tmp_path / "artifacts").mkdir()
    target = tmp_path / "target"
    target.mkdir()
    output = tmp_path / D1.OUTPUT_RELATIVE_PATH
    output.symlink_to(target, target_is_directory=True)
    with pytest.raises(D1.DiagnosticRefusal, match="already exists"):
        D1._publish_success(
            tmp_path,
            _valid_record(),
            freeze_sha256="a" * 64,
            implementation_sha256="b" * 64,
            test_sha256="c" * 64,
            human_freeze_sha256="d" * 64,
            attempt_marker={"raw_sha256": "1" * 64, "record_sha256": "2" * 64},
        )
    assert list(target.iterdir()) == []


def test_post_publish_reopen_is_closed_world_and_rechecks_marker(
    tmp_path, monkeypatch
):
    (tmp_path / "artifacts").mkdir()
    monkeypatch.setattr(
        D1, "_require_publication_binding_bytes", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        D1,
        "_require_launch_bindings_unchanged",
        lambda root, readiness: {},
    )
    attempt = D1._consume_attempt(
        tmp_path,
        freeze_sha256="a" * 64,
        implementation_sha256="b" * 64,
        test_sha256="c" * 64,
        human_freeze_sha256="d" * 64,
    )
    record_marker = {
        key: attempt[key]
        for key in ("path", "state", "attempt_number", "raw_sha256", "record_sha256")
    }
    record = _valid_record(record_marker)
    receipt = D1._publish_success(
        tmp_path,
        record,
        freeze_sha256="a" * 64,
        implementation_sha256="b" * 64,
        test_sha256="c" * 64,
        human_freeze_sha256="d" * 64,
        attempt_marker=attempt,
    )
    monkeypatch.setattr(D1, "_validate_outer_v2_custody", lambda root: {})
    monkeypatch.setattr(D1, "_validate_protected_roots_absent", lambda root: None)
    reopened = D1._validate_published_success(
        tmp_path,
        expected_record=record,
        expected_receipt=receipt,
        attempt_marker=attempt,
        readiness={},
    )
    assert reopened == receipt
    receipt_path = tmp_path / D1.OUTPUT_RELATIVE_PATH / "success-receipt.json"
    hostile = dict(receipt)
    hostile["production_authorized"] = True
    receipt_path.write_bytes(D1._canonical_json_bytes(hostile))
    with pytest.raises(D1.DiagnosticRefusal, match="success receipt"):
        D1._validate_published_success(
            tmp_path,
            expected_record=record,
            expected_receipt=hostile,
            attempt_marker=attempt,
            readiness={},
        )


def test_protected_production_roots_are_currently_absent():
    for relative in D1.PROTECTED_PRODUCTION_RELATIVE_PATHS:
        assert not os.path.lexists(ROOT / relative)


def test_no_real_d1_attempt_or_result_exists_during_no_execution_suite():
    assert not os.path.lexists(ROOT / D1.ATTEMPT_MARKER_RELATIVE_PATH)
    assert not os.path.lexists(ROOT / D1.OUTPUT_RELATIVE_PATH)
