import hashlib
import json
import math
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_NOVELTY_PATH = _ROOT / "manuscript_v3/novelty_audit_matrix.md"
_PREREG_PATH = _ROOT / "manuscript_v3/execution_preregistration.md"
_MACHINE_PATH = (
    _ROOT / "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
)
_PARTIAL_CHECKPOINT_FILE_PINS = {
    "manuscript_v3/c17_cap_defect_cancellation_contract.md": (
        "a0a57cdba08c588269c8706ab78bb68ac2360f29b97d20cd05cdcd3a8c93cb3f",
        5931,
        189,
    ),
    "src/heterodiff/evaluation/mixed_ctmc_ou_cap_defect_cancellation_diagnostic.py": (
        "50b9748a50982f10f289cba94c8ace9adab6ea003e57da091958fda8844f6ef9",
        28528,
        765,
    ),
    "tests/unit/test_mixed_ctmc_ou_cap_defect_cancellation_diagnostic.py": (
        "6de986e9b40d57e4f7e4ffdac82ebe04ff4c68ab3287df61c3c8a8ab36cca663",
        10291,
        282,
    ),
    "manuscript_v3/c17_finite_a1_association_component_contract.md": (
        "063a9acabd79a3c329aa721aded5c4ec8804749aaccde3d8e2096c41d5ce78c8",
        8189,
        207,
    ),
    "src/heterodiff/theory/finite_bridge_family_path_control.py": (
        "e7427b787bfefc8c8047d8ea80c69fff2df9803628b9238309839efdcf19449f",
        16917,
        445,
    ),
    "src/heterodiff/evaluation/finite_association_fork_b_diagnostic.py": (
        "a7279bd83a0e7cc65c132a9f5f73c18fd7bd15a896ceb86788aa4194650ac94d",
        57731,
        1336,
    ),
    "tests/unit/test_finite_association_fork_b_diagnostic.py": (
        "9aca3ba8878e4e5eacef0bef255be624eb8db219b3128b67ce6ee200066cc7c6",
        30879,
        808,
    ),
}


def _strict_object_pairs(rows):
    result = {}
    for key, value in rows:
        assert key not in result, "duplicate JSON key: %s" % key
        result[key] = value
    return result


def _reject_nonfinite_json_constant(value):
    raise AssertionError("nonfinite JSON constant: %s" % value)


def _load_machine() -> dict[str, Any]:
    return json.loads(
        _MACHINE_PATH.read_text("utf-8"),
        object_pairs_hook=_strict_object_pairs,
        parse_constant=_reject_nonfinite_json_constant,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_partial_checkpoint_file_pin(relative_path: str) -> None:
    expected_sha256, expected_bytes, expected_lf = _PARTIAL_CHECKPOINT_FILE_PINS[
        relative_path
    ]
    body = (_ROOT / relative_path).read_bytes()
    assert hashlib.sha256(body).hexdigest() == expected_sha256
    assert len(body) == expected_bytes
    assert body.count(b"\n") == expected_lf
    assert body.endswith(b"\n")
    assert b"\r" not in body


def _json_pointer(document: Any, pointer: str) -> Any:
    assert pointer.startswith("/")
    current = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def _count_nulls(value: Any) -> int:
    if value is None:
        return 1
    if isinstance(value, dict):
        return sum(_count_nulls(child) for child in value.values())
    if isinstance(value, list):
        return sum(_count_nulls(child) for child in value)
    return 0


def _build_test_only_finite_a1_checkpoint():
    from heterodiff.evaluation.finite_association_fork_b_diagnostic import (
        evaluate_finite_association_fork_b_diagnostic,
    )
    from heterodiff.evaluation.finite_association_residual_evaluator import (
        bind_test_only_finite_association_logit_evaluator,
    )
    from heterodiff.experiments.finite_association_guided_residual_pilot import (
        build_frozen_association_residual_fixture,
        frozen_association_fixture_content_digests,
        frozen_association_fixture_sha256,
    )

    fixture = build_frozen_association_residual_fixture()
    maximum = 0.1
    certificate = SimpleNamespace(
        passed=True,
        parameter_sha256="1" * 64,
        frozen_fixture_sha256=frozen_association_fixture_sha256(
            frozen_association_fixture_content_digests(fixture)
        ),
        feature_sha256="2" * 64,
        input_features=21,
        hidden_width=32,
        grid_intervals=4096,
        grid_points=4097,
        time_chunk_size=128,
        pair_count=420,
        evaluated_output_count=4097 * 420,
        layer_outward_row_sums=(1.0, 1.0, 1.0),
        input_time_lipschitz=1.0,
        network_time_lipschitz=1.0,
        maximum_grid_absolute_correction=maximum,
        outward_grid_maximum=math.nextafter(maximum, math.inf),
        half_cell_allowance=0.01,
        certified_maximum_absolute_correction=0.11,
        correction_limit=20.0,
        certificate_sha256="3" * 64,
    )
    state_residual = np.linspace(-1.0, 1.0, 20)[:, None]
    observation_density = np.asarray(
        fixture.population.observation_marginal_density, dtype=np.float64
    )[None, :]

    def evaluate_logits(times):
        return np.stack(
            [
                np.log(fixture.guide.density_grid(float(direct_time)))
                + (1.0 - float(direct_time)) * 0.05 * state_residual
                - np.log(observation_density)
                for direct_time in times
            ],
            axis=0,
        )

    evaluator = bind_test_only_finite_association_logit_evaluator(
        evaluate_logits, certificate
    )
    return evaluate_finite_association_fork_b_diagnostic(
        evaluator, fixture, test_only=True
    )


def test_previously_missing_scientific_route_artifacts_now_resolve() -> None:
    assert _NOVELTY_PATH.is_file()
    assert _PREREG_PATH.is_file()
    assert _MACHINE_PATH.is_file()

    manuscript = (_ROOT / "manuscript_v3/manuscript_v3.md").read_text("utf-8")
    tex = (_ROOT / "manuscript_v3/manuscript_v3.tex").read_text("utf-8")
    assert "novelty_audit_matrix.md" in manuscript
    assert "execution_preregistration.md" in manuscript
    assert "novelty_audit_matrix.md" in tex
    assert "execution_preregistration.md" in tex

    prereg = _PREREG_PATH.read_text("utf-8")
    assert "manuscript_v3_execution_preregistration_v1.json" in prereg


def test_machine_json_loader_rejects_duplicate_and_nonfinite_constants() -> None:
    with pytest.raises(AssertionError, match="duplicate JSON key"):
        json.loads('{"state":1,"state":2}', object_pairs_hook=_strict_object_pairs)
    with pytest.raises(AssertionError, match="nonfinite JSON constant"):
        json.loads('{"value":NaN}', parse_constant=_reject_nonfinite_json_constant)


def test_novelty_audit_is_fail_closed_and_complete() -> None:
    text = _NOVELTY_PATH.read_text("utf-8")
    assert "**Status:** `UNRESOLVED`" in text
    assert "**Broad-framing verdict:** `METHOD-NOVELTY-NO-GO`" in text
    assert "**Claim promotion authorized:** `NONE`" in text
    assert "C17-CENTERED-THEORY-AND-BENCHMARK-CANDIDATE" in text
    assert "no four appointed" in text
    assert "cryptographic signature" in text

    row_ids = re.findall(r"^\| (N\d{2}) \|", text, flags=re.MULTILINE)
    assert row_ids == [f"N{ordinal:02d}" for ordinal in range(1, 17)]
    for required_source in (
        "proceedings.neurips.cc/paper_files/paper/2024/hash/22d258df",
        "proceedings.mlr.press/v267/yang25af.html",
        "proceedings.iclr.cc/paper_files/paper/2025/hash/819aaee",
        "www.jmlr.org/papers/v27/25-0693.html",
        "proceedings.iclr.cc/paper_files/paper/2025/hash/cceb6b5d",
        "proceedings.mlr.press/v216/boyd23a.html",
    ):
        assert required_source in text

    assert "prove an explicit coercivity/regularity bridge" in text
    assert "KL has no general triangle inequality" in text
    assert "again as a separate path-error summand" in text
    assert "C20 alone does not restore a new-method claim" in text


def test_preregistration_remains_nonexecutable_and_nonauthoritative() -> None:
    text = _PREREG_PATH.read_text("utf-8")
    assert "**State:** `DRAFT_NOT_EXECUTABLE`" in text
    assert "**Confirmatory execution authorized:** no" in text
    assert "no externally appointed\nfour-reviewer panel" in text
    assert "do not recreate CP75" in text
    assert "not a general heterogeneous-generation framework" in text
    assert "ASAP/R5" in text
    assert "physical-time fallback/F1" in text
    assert "No substitute dataset is permitted" in text
    assert "No seed top-up" in text
    assert "c17_cap_defect_cancellation_contract.md" in text
    assert "c17_finite_a1_association_component_contract.md" in text
    assert "These numbers test\nthe evaluator, not a learned model." in text


def test_machine_companion_has_exact_claim_slot_and_domain_scope() -> None:
    document = _load_machine()
    assert document["state"] == "DRAFT_NOT_EXECUTABLE"
    assert document["scope"] == "NARROW_THEORY_AND_TWO_DOMAIN_BENCHMARK"
    assert document["confirmatory_execution_authorized"] is False
    assert document["publication_preregistration_only"] is True
    assert document["production_gate_or_blocker_effect"] is False
    assert document["formal_test_28_effect"] is False

    claim_ids = [row["claim_id"] for row in document["claim_dispositions"]]
    assert claim_ids == [f"C{ordinal}" for ordinal in range(21)]
    slot_ids = [row["slot_id"] for row in document["slot_plan"]]
    assert slot_ids == ["R1-A1", "R2-HYBRID", "R3-PHYS", "R4-RETAIL"]
    assert [row["slot_id"] for row in document["excluded_slots"]] == [
        "R5-ASAP",
        "F1-TIME",
    ]
    assert [row["domain_id"] for row in document["domains"]] == [
        "physionet-challenge-2012",
        "online-retail-ii",
    ]


def test_partial_c17_and_mixed_oracle_checkpoint_is_bound_without_promotion() -> None:
    document = _load_machine()
    plan = document["theory_and_known_law_plan"]

    bound_files = {
        plan["current_partial_c17_target_document_path"]: plan[
            "current_partial_c17_target_document_sha256"
        ],
        plan["current_partial_mixed_oracle_source_path"]: plan[
            "current_partial_mixed_oracle_source_sha256"
        ],
        plan["current_partial_mixed_oracle_test_path"]: plan[
            "current_partial_mixed_oracle_test_sha256"
        ],
        plan["current_partial_fork_b_contract_path"]: plan[
            "current_partial_fork_b_contract_sha256"
        ],
        plan["current_partial_path_kl_source_path"]: plan[
            "current_partial_path_kl_source_sha256"
        ],
        plan["current_partial_path_kl_test_path"]: plan[
            "current_partial_path_kl_test_sha256"
        ],
    }
    for relative_path, expected_sha256 in bound_files.items():
        path = _ROOT / relative_path
        assert path.is_file()
        assert _sha256(path) == expected_sha256

    assert plan["current_partial_c17_target_status"] == (
        "UNPROVED_NOT_EXECUTABLE_NO_CLAIM_PROMOTION"
    )
    assert plan["current_partial_mixed_oracle_scope"] == (
        "FINITE_FACTORIZED_MIXED_CTMC_OU_DIAGNOSTIC"
    )
    assert plan["current_partial_mixed_oracle_focused_test_count"] == 10
    for field in (
        "current_partial_mixed_oracle_learned_residual_exercised",
        "current_partial_mixed_oracle_path_kl_decomposition_exercised",
        "current_partial_mixed_oracle_cap_defect_cancellation_exercised",
        "current_partial_mixed_oracle_association_marginalization_exercised",
        "current_partial_mixed_oracle_occurrence_attached_continuous_marks_exercised",
        "current_partial_mixed_oracle_closes_c17",
        "current_partial_mixed_oracle_closes_r2",
        "current_partial_checkpoint_authorizes_confirmatory_execution",
    ):
        assert plan[field] is False

    from heterodiff.evaluation.mixed_ctmc_ou_path_kl_diagnostic import (
        build_mixed_ctmc_ou_path_kl_diagnostic,
    )

    path_kl = build_mixed_ctmc_ou_path_kl_diagnostic()
    components = plan["current_partial_path_kl_components"]
    observed_components = {
        "initializer": path_kl.decomposition.initializer.total_exact_to_plugin,
        "ou_continuous_gradient": path_kl.decomposition.ou_continuous_gradient,
        "birth": path_kl.decomposition.jumps.birth,
        "death": path_kl.decomposition.jumps.death,
        "replacement": path_kl.decomposition.jumps.replacement,
        "total": path_kl.decomposition.total,
    }
    assert plan["current_partial_path_kl_scope"] == path_kl.scope
    assert plan["current_partial_path_kl_focused_test_count"] == 12
    assert plan["current_partial_path_kl_orientation"] == path_kl.orientation
    assert components.keys() == observed_components.keys()
    for name, observed in observed_components.items():
        assert math.isclose(components[name], observed, rel_tol=0.0, abs_tol=2.0e-15)
    assert math.isclose(
        plan["current_partial_path_kl_reverse_orientation_total"],
        path_kl.reverse_orientation.total,
        rel_tol=0.0,
        abs_tol=2.0e-15,
    )
    assert math.isclose(
        plan["current_partial_path_kl_direct_crosscheck_absolute_difference"],
        path_kl.crosscheck.absolute_difference_from_adaptive_total,
        rel_tol=0.0,
        abs_tol=2.0e-18,
    )
    assert (
        plan["current_partial_path_kl_mathematical_identity_exact_for_declared_fixture"]
        is True
    )
    for field in (
        "current_partial_path_kl_float_interval_certified",
        "current_partial_path_kl_learned_estimator_exercised",
        "current_partial_path_kl_association_marginalization_exercised",
        "current_partial_path_kl_occurrence_attached_continuous_marks_exercised",
        "current_partial_path_kl_cap_defect_cancellation_exercised",
        "current_partial_path_kl_closes_c17",
        "current_partial_path_kl_closes_r2",
        "current_partial_path_kl_authorizes_confirmatory_execution",
    ):
        assert plan[field] is False

    assert plan["c17_final_theorem_statement"] is None
    assert plan["c17_proof_artifact_path"] is None
    assert plan["mixed_ctmc_ou_fixture_parameters"] is None
    assert plan["mixed_exact_or_certified_kl_tv_tolerances"] is None
    assert document["slot_plan"][1]["current_status"] == "NOT_RUN"
    assert document["confirmatory_execution_authorized"] is False


def test_cap_defect_cancellation_checkpoint_is_bound_without_double_counting() -> None:
    from heterodiff.evaluation.mixed_ctmc_ou_cap_defect_cancellation_diagnostic import (
        build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic,
    )

    document = _load_machine()
    plan = document["theory_and_known_law_plan"]
    bound_files = {
        plan["current_partial_cap_defect_contract_path"]: plan[
            "current_partial_cap_defect_contract_sha256"
        ],
        plan["current_partial_cap_defect_source_path"]: plan[
            "current_partial_cap_defect_source_sha256"
        ],
        plan["current_partial_cap_defect_test_path"]: plan[
            "current_partial_cap_defect_test_sha256"
        ],
    }
    for relative_path, expected_sha256 in bound_files.items():
        assert expected_sha256 == _PARTIAL_CHECKPOINT_FILE_PINS[relative_path][0]
        _assert_partial_checkpoint_file_pin(relative_path)

    result = build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic()
    observed = result.shared_guide_decomposition
    expected = plan["current_partial_cap_defect_components"]
    assert plan["current_partial_cap_defect_scope"] == result.scope
    assert plan["current_partial_cap_defect_focused_test_count"] == 10
    assert plan["current_partial_cap_defect_evaluation_coordinates"] == [
        -1.0,
        0.0,
        1.0,
    ]
    assert math.isclose(
        plan["current_partial_cap_defect_maximum_absolute_value"],
        result.maximum_absolute_cap_defect,
        rel_tol=0.0,
        abs_tol=2.0e-15,
    )
    assert math.isclose(
        plan["current_partial_cap_defect_identity_residual"],
        result.maximum_defect_identity_residual,
        rel_tol=0.0,
        abs_tol=2.0e-18,
    )
    assert math.isclose(
        plan["current_partial_cap_defect_shared_guide_error_recovery_residual"],
        result.maximum_error_recovery_residual,
        rel_tol=0.0,
        abs_tol=2.0e-18,
    )
    observed_components = {
        "initializer": observed.initializer,
        "ou_continuous_gradient": observed.ou_continuous_gradient,
        "birth": observed.birth,
        "death": observed.death,
        "replacement": observed.replacement,
        "total": observed.total,
    }
    assert expected.keys() == observed_components.keys()
    for name, value in observed_components.items():
        assert math.isclose(expected[name], value, rel_tol=0.0, abs_tol=2.0e-15)
    assert plan["current_partial_cap_defect_path_total_excludes_defect"] is True
    assert result.path_total_excludes_cap_defect is True
    for field in (
        "current_partial_cap_defect_matrix_exponential_interval_certified",
        "current_partial_cap_defect_quadrature_interval_certified",
        "current_partial_cap_defect_learned_estimator_exercised",
        "current_partial_cap_defect_association_marginalization_exercised",
        "current_partial_cap_defect_occurrence_attached_continuous_marks_exercised",
        "current_partial_cap_defect_closes_c17",
        "current_partial_cap_defect_closes_r2",
        "current_partial_cap_defect_authorizes_confirmatory_execution",
    ):
        assert plan[field] is False


def test_finite_a1_association_component_is_test_only_and_nonpromotional() -> None:
    document = _load_machine()
    plan = document["theory_and_known_law_plan"]
    bound_files = {
        plan["current_partial_a1_association_contract_path"]: plan[
            "current_partial_a1_association_contract_sha256"
        ],
        plan["current_partial_a1_family_helper_source_path"]: plan[
            "current_partial_a1_family_helper_source_sha256"
        ],
        plan["current_partial_a1_association_source_path"]: plan[
            "current_partial_a1_association_source_sha256"
        ],
        plan["current_partial_a1_association_test_path"]: plan[
            "current_partial_a1_association_test_sha256"
        ],
    }
    for relative_path, expected_sha256 in bound_files.items():
        assert expected_sha256 == _PARTIAL_CHECKPOINT_FILE_PINS[relative_path][0]
        _assert_partial_checkpoint_file_pin(relative_path)

    result = _build_test_only_finite_a1_checkpoint()
    assert plan["current_partial_a1_association_scope"] == result.scope
    assert plan["current_partial_a1_association_status"] == result.status
    assert plan["current_partial_a1_association_focused_test_count"] == 24
    assert (
        plan["current_partial_a1_association_local_compatibility_fixture_sha256"]
        == result.local_compatibility_fixture_sha256
    )
    assert (
        plan["current_partial_a1_association_preregistered_production_fixture_sha256"]
        == result.preregistered_production_fixture_sha256
    )
    assert (
        plan["current_partial_a1_association_path_content_sha256"]
        == result.fixture_content_sha256
    )
    assert (
        plan["current_partial_a1_association_edge_family_partition_sha256"]
        == result.edge_family_partition_sha256
    )
    assert plan["current_partial_a1_association_test_only_callback_used"] is True
    assert result.test_only_evaluator_used is True
    assert plan["current_partial_a1_association_callback_determinism_checked"] is True
    assert result.test_only_callback_determinism_checked is True
    assert (
        plan["current_partial_a1_association_production_checkpoint_supplied"] is False
    )
    assert result.evaluator_production_bound is False
    assert (
        plan[
            "current_partial_a1_association_production_checkpoint_evaluation_supported"
        ]
        is False
    )
    assert result.production_checkpoint_evaluation_supported is False
    assert plan["current_partial_a1_association_all_21_observations_evaluated"] is True
    assert len(result.observations) == 21
    assert plan["current_partial_a1_association_overflow_observation_index"] == 20
    assert plan["current_partial_a1_association_active_edge_counts"] == list(
        result.active_edge_counts
    )
    assert plan["current_partial_a1_association_continuous_component_disposition"] == (
        result.continuous_component_disposition
    )
    expected = plan["current_partial_a1_association_observation_weighted_components"]
    observed = {
        "initializer": result.observation_weighted_initial,
        "birth": result.observation_weighted_birth,
        "death": result.observation_weighted_death,
        "replacement": result.observation_weighted_replacement,
        "total": result.observation_weighted_total,
    }
    assert expected.keys() == observed.keys()
    for name, value in observed.items():
        assert math.isclose(expected[name], value, rel_tol=0.0, abs_tol=2.0e-15)
    scalar_checks = {
        "current_partial_a1_association_maximum_primary_refined_total_change": (
            result.maximum_primary_refined_total_change
        ),
        "current_partial_a1_association_maximum_target_marginal_absolute_error": (
            result.maximum_target_marginal_absolute_error
        ),
        "current_partial_a1_association_maximum_terminal_log_potential_absolute_error": (
            result.maximum_terminal_log_potential_absolute_error
        ),
        "current_partial_a1_association_maximum_family_aggregate_crosscheck_absolute_difference": (
            result.maximum_family_aggregate_crosscheck_absolute_difference
        ),
    }
    for field, value in scalar_checks.items():
        assert math.isclose(plan[field], value, rel_tol=0.0, abs_tol=2.0e-18)
    for field in (
        "current_partial_a1_association_interval_certified",
        "current_partial_a1_association_simultaneous_coverage_proved",
        "current_partial_a1_association_rigorous_numerical_enclosure_present",
        "current_partial_a1_association_occurrence_attached_mark_fibers_exercised",
        "current_partial_a1_association_cap_defect_cancellation_exercised",
        "current_partial_a1_association_closes_c17",
        "current_partial_a1_association_r1_qualified",
        "current_partial_a1_association_r2_qualified",
        "current_partial_a1_association_promotes_manuscript_claim",
        "current_partial_a1_association_authorizes_confirmatory_execution",
    ):
        assert plan[field] is False
    assert plan["current_partial_a1_association_r1_status"] == "NOT_RUN"
    assert plan["current_partial_a1_association_r2_status"] == "NOT_RUN"
    assert document["slot_plan"][0]["current_status"] == "NOT_RUN"
    assert document["slot_plan"][1]["current_status"] == "NOT_RUN"
    assert document["confirmatory_execution_authorized"] is False


def test_source_context_and_closest_collision_comparators_are_bound() -> None:
    document = _load_machine()
    for row in document["source_context"]:
        path = _ROOT / row["path"]
        assert path.is_file()
        assert _sha256(path) == row["sha256"]

    comparator_ids = [
        row["comparator_family_id"]
        for row in document["method_and_baseline_plan"][
            "required_literature_comparator_families"
        ]
    ]
    assert comparator_ids == [
        "ngdb-style-auxiliary-guide-plus-correction",
        "deft-style-generalized-h-frozen-base-correction",
        "task-compatible-same-base-smc-or-feynman-kac",
        "closest-variable-cardinality-point-or-edit-generator",
    ]
    assert document["method_and_baseline_plan"][
        "each_literature_comparator_requires_implementation_or_frozen_domain_specific_justification"
    ]


def test_every_declared_blocker_path_resolves_and_nulls_fail_closed() -> None:
    document = _load_machine()
    assert _count_nulls(document) >= 150
    for blocker in document["unresolved_blockers"]:
        assert blocker["blocking_json_paths"]
        for pointer in blocker["blocking_json_paths"]:
            _json_pointer(document, pointer)

    freeze = document["freeze_predicate"]
    assert (
        freeze[
            "all_required_preexecution_scientific_semantic_and_numeric_fields_nonnull"
        ]
        is False
    )
    assert freeze["all_confirmatory_execution_blockers_closed"] is False
    assert freeze["all_claim_promotion_and_submission_blockers_closed"] is False
    assert freeze["all_required_preexecution_artifacts_present_and_hash_bound"] is False
    assert freeze["freeze_receipt_present"] is False
    assert freeze["claim_promotion_or_submission_permitted"] is False
    assert freeze["current_state"] == "DRAFT_NOT_EXECUTABLE"


def test_normal_research_audits_do_not_recreate_external_governance() -> None:
    document = _load_machine()
    assert document["required_preexecution_null_fields_are_execution_blocking"] is True
    assert document["postexecution_audit_plan_nulls_are_execution_blocking"] is False
    assert (
        document["postexecution_audit_plan_nulls_block_claim_promotion_and_submission"]
        is True
    )
    assert (
        document["cp75_style_external_reviewer_appointment_or_signature_required"]
        is False
    )

    review_blocker = next(
        blocker
        for blocker in document["unresolved_blockers"]
        if blocker["blocker_id"]
        == "proof-methods-statistics-and-reproduction-audit-plans"
    )
    assert review_blocker["blocking_stage"] == (
        "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION"
    )
    assert all(
        _json_pointer(document, pointer) is None
        for pointer in review_blocker["blocking_json_paths"]
    )

    blocker_stages = {
        blocker["blocker_id"]: blocker["blocking_stage"]
        for blocker in document["unresolved_blockers"]
    }
    assert set(blocker_stages.values()) == {
        "CONFIRMATORY_EXECUTION",
        "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION",
    }
    assert (
        blocker_stages["data-license-clinical-governance-and-retail-privacy-plan"]
        == "CONFIRMATORY_EXECUTION"
    )
    assert (
        blocker_stages["code-model-artifact-release-and-submission-anonymization-plan"]
        == "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION"
    )

    preexecution = document["required_preexecution_artifacts"]
    postexecution = document["required_postexecution_artifacts"]
    assert all("audit" not in artifact for artifact in preexecution)
    assert {
        "fresh-proof-and-code-audit",
        "fresh-methods-and-statistics-audit",
        "clean-room-reproduction-report",
    }.issubset(postexecution)
    assert (
        "c17_independent_proof_audit_path" not in document["theory_and_known_law_plan"]
    )
    assert (
        document["ethics_release_and_review_plan"]["proof_and_code_audit_artifact_path"]
        is None
    )


def test_cp76_missing_inventory_is_historical_not_rewritten() -> None:
    cp76_path = (
        _ROOT
        / "research/fixtures/cp76_manuscript_v3_submission_readiness_manifest_v1.json"
    )
    cp76 = json.loads(cp76_path.read_text("utf-8"))
    snapshot_missing = set(cp76["direct_manuscript_support_inventory"]["missing_paths"])
    assert "manuscript_v3/novelty_audit_matrix.md" in snapshot_missing
    assert "manuscript_v3/execution_preregistration.md" in snapshot_missing
    assert _sha256(cp76_path) == (
        "b9ce9744b64212bf0e762d3342c9a221438c2676ebd9d69db2f50cbbebf9ac06"
    )
