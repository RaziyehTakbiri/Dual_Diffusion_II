"""Hostile static checks for manuscript-v3 pre-execution closure V2."""

from __future__ import annotations

import ast
from copy import deepcopy
from decimal import Decimal
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import shutil
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
MACHINE_PATH = ROOT / (
    "research/fixtures/"
    "manuscript_v3_execution_preregistration_preexecution_closure_v2.json"
)
HUMAN_PATH = ROOT / (
    "manuscript_v3/execution_preregistration_preexecution_closure_v2.md"
)
QUALIFICATION_PATH = ROOT / (
    "research/diagnostics/" "finite_association_r1_rank_prefix_binder_qualification.py"
)
PREREG_PATH = ROOT / (
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
)
ORDER_PATH = ROOT / (
    "src/heterodiff/experiments/finite_association_production_order.py"
)

CLOSURE_DOMAIN = (
    b"heterodiff-manuscript-v3-execution-preregistration-" b"preexecution-closure-v2\0"
)
QUALIFICATION_DOMAIN = (
    b"heterodiff-manuscript-v3-r1-rank-prefix-binder-qualification-v1\0"
)

EXPECTED_TOP_KEYS = {
    "schema_version",
    "closure_id",
    "registration_mode",
    "global_state",
    "milestone_status",
    "disposition",
    "scope",
    "predecessor_bindings",
    "registration_bindings",
    "resolved_pre_d1_fields",
    "null_projection",
    "blocker_projection",
    "freeze_predicate_projection",
    "staged_freeze_states",
    "d1_prior_knowledge_boundary",
    "runtime_and_production_boundary",
    "rank_prefix_qualification",
    "state_preservation",
    "publication_anonymity_boundary",
    "nonclaims",
    "record_sha256",
}

EXPECTED_PREDECESSORS = {
    "claim_ledger": (
        "manuscript_v3/claim_ledger.md",
        "793f7fbda938f66d771af3dc480d13dc784862a439ee65452b79c776d78e8245",
    ),
    "execution_preregistration_human": (
        "manuscript_v3/execution_preregistration.md",
        "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
    ),
    "execution_preregistration_machine": (
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
    ),
    "scientific_route_test": (
        "tests/unit/test_manuscript_v3_scientific_route.py",
        "a76b2b7390999d2f43c1a7406f83f8347951d43b9762f3960410de3b188b01ae",
    ),
    "cp76_readiness_manifest": (
        "research/fixtures/cp76_manuscript_v3_submission_readiness_manifest_v1.json",
        "b9ce9744b64212bf0e762d3342c9a221438c2676ebd9d69db2f50cbbebf9ac06",
    ),
    "cp76_readiness_test": (
        "tests/unit/test_manuscript_v3_submission_readiness.py",
        "410a20e9444e5005481c2bb7c8acef0135061a86ce5bf3ad546fe3fffe83dcbc",
    ),
    "a1_specification": (
        "research/62_a1_association_guided_residual_falsification_spec.md",
        "475f4f450cb5703e6773c0d0ff242db995a16408acce5989401fa0674326e67c",
    ),
    "c17_theorem_target": (
        "manuscript_v3/c17_hybrid_path_error_theorem.md",
        "d11dc3a98d19a52e7ab653aca1e06598490ad098a450b526870508b4499b9d8d",
    ),
    "c17_a1_component_contract": (
        "manuscript_v3/c17_finite_a1_association_component_contract.md",
        "063a9acabd79a3c329aa721aded5c4ec8804749aaccde3d8e2096c41d5ce78c8",
    ),
    "a1_v2_freeze_human": (
        "manuscript_v3/a1_development_checkpoint_freeze_v2.md",
        "6639e0f15592558f03bae98fd7d75a56ec64564132f9631832c360a2be60f953",
    ),
    "a1_v2_freeze_machine": (
        "research/fixtures/manuscript_v3_a1_development_checkpoint_freeze_v2.json",
        "b0b892db1041267defe664f59d57801e723f0115b8ac5ae9fc8656c3708cd8fc",
    ),
    "a1_v2_freeze_test": (
        "tests/unit/test_manuscript_v3_a1_development_checkpoint_freeze_v2.py",
        "fb5f6a4571d6fea7f8d7b7254648770e9d459d10a481bc3742e43330c416569c",
    ),
    "d1_freeze_human": (
        "manuscript_v3/a1_trained_checkpoint_diagnostic_freeze.md",
        "59f00d83aba2545ec80b4778cfa181b0a5a0be043bddfb42aef212aaf7533e6d",
    ),
    "d1_freeze_machine": (
        "research/fixtures/manuscript_v3_a1_trained_checkpoint_diagnostic_freeze_v1.json",
        "11d341f65bde47caffcf3c946919c3c0c83254684fb58d0ad643b1874fb3a973",
    ),
    "d1_freeze_test": (
        "tests/unit/test_finite_association_trained_checkpoint_diagnostic.py",
        "fda8bafabcb8737035d0b342fd5639a6618900d0a958bd0dbbf0adb827ac0d25",
    ),
    "d1_orchestration_source": (
        "research/diagnostics/finite_association_trained_checkpoint_diagnostic.py",
        "7cf3a5785f6bb3576357fe8c9bd867955660c2ff2486ca0710c1398e32b1cb0e",
    ),
    "d1_evidence_human": (
        "manuscript_v3/a1_trained_checkpoint_diagnostic_evidence_registration.md",
        "bd00e6d145a5517ed8ecd34f6547c49d6d8d4eae67aeb8321037bf6ca54b3ba5",
    ),
    "d1_evidence_machine": (
        "research/fixtures/manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration_v1.json",
        "b52685e2b61a30c5781f0e75138eaae6410063fa2312a447eeed7a4d1902cac0",
    ),
    "d1_evidence_test": (
        "tests/unit/test_manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration.py",
        "2c6ef628557c531b91c836113b9feb31e99ca48b4b7d16134c84998d739bd1e5",
    ),
    "d1_diagnostic_record": (
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/diagnostic-record.json",
        "4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10",
    ),
    "d1_success_receipt": (
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/success-receipt.json",
        "eabecf04bfe0831fa14d60126c541774aaf25c58283ebb999dc3de2403e9cada",
    ),
    "d1_attempt_marker": (
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1.attempt.json",
        "acfc404eca9ed711279087861518b7e9b32dfdb5fec4aaba318b50e7b4854e14",
    ),
    "production_order_source": (
        "src/heterodiff/experiments/finite_association_production_order.py",
        "be2b4134672fc2895242d8cbb68d8c540345574f1b31ed8b04a50b88793235e1",
    ),
    "rank_stress_source": (
        "src/heterodiff/experiments/finite_association_rank_stress.py",
        "ead7544be821d58874fd07d4293adc078257f8efb47a82a1e91ea2fa0b702c67",
    ),
    "runtime_identity_source": (
        "src/heterodiff/experiments/finite_association_runtime_identity.py",
        "ba10c8053796b6d36bc02a2bea0716a443bba35fd1190333292b87701eb18bf0",
    ),
    "environment_lock": (
        "requirements/m1-reference-macos-arm64-py311.lock",
        "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d",
    ),
}

DEFERRED_NULL_PATHS = {
    "/ethics_release_and_review_plan/code_model_and_artifact_release_plan",
    "/ethics_release_and_review_plan/submission_anonymization_plan",
    "/ethics_release_and_review_plan/proof_and_code_audit_plan",
    "/ethics_release_and_review_plan/proof_and_code_audit_artifact_path",
    "/ethics_release_and_review_plan/methods_and_statistics_audit_plan",
    "/ethics_release_and_review_plan/clean_room_reproduction_audit_plan",
}

RESOLVED_POINTERS = {
    "/theory_and_known_law_plan/a1_fixture_parameters",
    "/theory_and_known_law_plan/a1_evaluation_grid",
}

EXPECTED_FIXTURE = {
    "horizon": "1",
    "cap": 3,
    "type_count": 3,
    "state_count": 20,
    "observation_count": 21,
    "overflow_observation_index": 20,
    "birth_rates": ["0.38", "0.30", "0.24"],
    "death_rates_per_occurrence": ["0.28", "0.34", "0.25"],
    "replacement_matrix_row_source_column_destination": [
        ["0", "0.16", "0.07"],
        ["0.11", "0", "0.15"],
        ["0.09", "0.13", "0"],
    ],
    "initial_capped_factorial_parameter": ["0.65", "0.50", "0.40"],
    "detection_probabilities": ["0.72", "0.63", "0.68"],
    "confusion_matrix_row_source_column_anchor": [
        ["0.62", "0.25", "0.13"],
        ["0.22", "0.58", "0.20"],
        ["0.18", "0.27", "0.55"],
    ],
    "observation_clutter_rates": ["0.10", "0.08", "0.12"],
    "uniform_observation_reference_mass": "1/21",
    "whole_observation_contamination_probability": "0.08",
    "production_fixture_sha256": (
        "0121b487728b40356de6707a33ba4881100c3d1b587259b19723463a60cecdcc"
    ),
}

EXPECTED_GRID = {
    "formula": "t_j=j/32",
    "index_domain": "j=0,...,32",
    "point_count": 33,
    "ordered_exact_rational_points": [f"{index}/32" for index in range(33)],
    "boundary_point": "32/32",
    "boundary_supplies_gradient": False,
}

EXPECTED_PROJECTED_SOURCE_BINDINGS = [
    {
        "role": "SCIENTIFIC_SPECIFICATION",
        "path": "research/62_a1_association_guided_residual_falsification_spec.md",
        "raw_sha256": (
            "475f4f450cb5703e6773c0d0ff242db995a16408acce5989401fa0674326e67c"
        ),
    },
    {
        "role": "PRE_D1_MACHINE_FREEZE_FIXTURE_ATTESTATION",
        "path": (
            "research/fixtures/"
            "manuscript_v3_a1_development_checkpoint_freeze_v2.json"
        ),
        "raw_sha256": (
            "b0b892db1041267defe664f59d57801e723f0115b8ac5ae9fc8656c3708cd8fc"
        ),
    },
]

EXPECTED_FREEZE_PREDICATE = {
    "all_required_preexecution_scientific_semantic_and_numeric_fields_nonnull": False,
    "all_confirmatory_execution_blockers_closed": False,
    "all_claim_promotion_and_submission_blockers_closed": False,
    "all_required_preexecution_artifacts_present_and_hash_bound": False,
    "claim_boundary_approved": False,
    "domain_admission_complete": False,
    "power_review_complete": False,
    "known_law_and_whole_method_gates_complete": False,
    "test_data_unopened_before_freeze": None,
    "freeze_receipt_present": False,
    "frozen_executable_state_if_and_only_if_execution_predicates_true": (
        "FROZEN_EXECUTABLE"
    ),
    "claim_promotion_or_submission_permitted": False,
    "current_state": "DRAFT_NOT_EXECUTABLE",
}

BLOCKER_IDS = {
    "final-c17-statement-and-claim-wording",
    "physionet-data-governance-representation-task-and-admission",
    "retail-data-governance-representation-task-and-admission",
    "primary-metric-proof-and-effect-thresholds",
    "known-law-scaling-no-regression-and-failure-thresholds",
    "baseline-identities-and-matched-compute",
    "power-analysis-and-seed-schedule",
    "hardware-compute-and-tuning-budget",
    "data-license-clinical-governance-and-retail-privacy-plan",
    "code-model-artifact-release-and-submission-anonymization-plan",
    "proof-methods-statistics-and-reproduction-audit-plans",
    "remaining-method-implementation-and-whole-method-gates",
}

ALL_PRODUCTION_ROOTS = [
    "artifacts/a1_finite_association_production_order_v1",
    "artifacts/a1_rank_stress_gate_v1.json",
    "artifacts/a1_rank_stress_gate_v1.json.prepared.json",
    "artifacts/a1_rank_stress_gate_v1.json.parent-exit.json",
    "artifacts/a1_exact_population_campaign_v4",
    "artifacts/a1_campaign_v4",
    "artifacts/a1_primary_metrics_v1",
    "artifacts/a1_primary_metrics_v2",
    "artifacts/a1_candidate_decision_v1",
    "artifacts/a1_independent_audit_v1",
    "artifacts/a1_publication_decision_v1",
]

EXCLUDED_DEVELOPMENT_ARTIFACT_PATHS = [
    "artifacts/manuscript_v3_a1_development_checkpoint_v1",
    "artifacts/manuscript_v3_a1_development_checkpoint_v1/failure-receipt.json",
    "artifacts/manuscript_v3_a1_development_checkpoint_v2",
    "artifacts/manuscript_v3_a1_development_checkpoint_v2/success-receipt.json",
    "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1",
    "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/diagnostic-record.json",
    "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/success-receipt.json",
    "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1.attempt.json",
]

EXPECTED_SEMANTIC_SHA256 = {
    "d1_evidence_machine": (
        "d1c52907ba0bbb6b17cb2cb4e930d983623f39c161ad8a116afa43dccbbfa1b9"
    ),
    "d1_diagnostic_record": (
        "68434890dbd3157b70e700d6a649000dbc9ee60e297b9196af46e312beba07e6"
    ),
    "d1_success_receipt": (
        "54167cf673861b93db3dd6cd354f9e08796bef59ef19b08ca4b03e59c4a62105"
    ),
    "d1_attempt_marker": (
        "4d9bdd188be51385d08c4a7540905096ce1f4f856ee313a524542f51684bbeb6"
    ),
}


def _reject_duplicate_keys(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    value: Dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise AssertionError("duplicate JSON key: " + key)
        value[key] = item
    return value


def _load(path: Path) -> Tuple[bytes, Dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=lambda token: (_ for _ in ()).throw(
            AssertionError("nonfinite JSON number: " + token)
        ),
    )
    assert type(value) is dict
    return raw, value


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _file_row(relative_path: str) -> Dict[str, Any]:
    raw = (ROOT / relative_path).read_bytes()
    return {
        "path": relative_path,
        "bytes": len(raw),
        "lf_count": raw.count(b"\n"),
        "terminal_lf": raw.endswith(b"\n"),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _count_null_paths(value: Any, pointer: str = "") -> List[str]:
    if value is None:
        return [pointer]
    if type(value) is dict:
        result: List[str] = []
        for key, item in value.items():
            escaped = key.replace("~", "~0").replace("/", "~1")
            result.extend(_count_null_paths(item, pointer + "/" + escaped))
        return result
    if type(value) is list:
        result = []
        for index, item in enumerate(value):
            result.extend(_count_null_paths(item, pointer + "/" + str(index)))
        return result
    return []


def _literal_assignment(path: Path, name: str) -> object:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if type(node) is ast.Assign and any(
            type(target) is ast.Name and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("missing assignment: " + name)


def _load_qualification_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "finite_association_r1_rank_prefix_binder_qualification",
        QUALIFICATION_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _without_digest(value: Mapping[str, Any]) -> Dict[str, Any]:
    body = dict(value)
    body.pop("record_sha256", None)
    return body


def _assert_contract(value: Mapping[str, Any]) -> None:
    assert set(value) == EXPECTED_TOP_KEYS
    assert value["schema_version"] == (
        "heterodiff-manuscript-v3-execution-preregistration-" "preexecution-closure-v2"
    )
    assert value["closure_id"] == ("EXECUTION-PREREGISTRATION-PREEXECUTION-CLOSURE-V2")
    assert value["registration_mode"] == "ADDITIVE_SUCCESSOR_SIDECAR"
    assert value["global_state"] == "DRAFT_NOT_EXECUTABLE"
    assert value["milestone_status"] == ("R1_RANK_BINDER_QUALIFIED_ZERO_EXECUTION")
    assert value["disposition"] == "STATIC_PREFIX_QUALIFIED_NOT_EXECUTABLE"
    assert value["scope"] == (
        "SUCCESSOR_PREEXECUTION_FREEZE_CLOSURE_" "AND_ZERO_EXECUTION_RANK_PREFIX"
    )

    for row in value["predecessor_bindings"].values():
        assert set(row) == {
            "path",
            "bytes",
            "lf_count",
            "terminal_lf",
            "raw_sha256",
            "semantic_sha256",
        }
    for row in value["registration_bindings"].values():
        assert set(row) == {
            "path",
            "bytes",
            "lf_count",
            "terminal_lf",
            "raw_sha256",
        }

    resolved = value["resolved_pre_d1_fields"]
    assert type(resolved) is list and len(resolved) == 2
    for item in resolved:
        assert set(item) == {
            "source_json_pointer",
            "resolution_status",
            "observed_after_d1",
            "pre_d1_source_bindings",
            "projected_value",
        }
        assert item["pre_d1_source_bindings"] == EXPECTED_PROJECTED_SOURCE_BINDINGS
    by_pointer = {item["source_json_pointer"]: item for item in resolved}
    assert set(by_pointer) == RESOLVED_POINTERS
    assert (
        by_pointer["/theory_and_known_law_plan/a1_fixture_parameters"][
            "projected_value"
        ]
        == EXPECTED_FIXTURE
    )
    assert (
        by_pointer["/theory_and_known_law_plan/a1_evaluation_grid"]["projected_value"]
        == EXPECTED_GRID
    )
    for item in resolved:
        assert item["resolution_status"] == (
            "PROJECTED_FROM_HASH_BOUND_PRE_D1_SPECIFICATION"
        )
        assert item["observed_after_d1"] is False

    nulls = value["null_projection"]
    assert nulls == {
        "historical_total_null_count": 174,
        "historical_preexecution_null_count": 168,
        "historical_deferred_postexecution_null_count": 6,
        "projected_resolved_pre_d1_null_count": 2,
        "effective_total_unresolved_null_count": 172,
        "effective_preexecution_unresolved_null_count": 166,
        "effective_deferred_postexecution_unresolved_null_count": 6,
        "deferred_postexecution_null_paths": sorted(DEFERRED_NULL_PATHS),
        "other_nulls_resolved": False,
        "historical_preregistration_mutated": False,
        "required_preexecution_null_fields_are_execution_blocking": True,
        "postexecution_audit_plan_nulls_are_execution_blocking": False,
        "postexecution_audit_plan_nulls_block_claim_promotion_and_submission": True,
    }

    blockers = value["blocker_projection"]
    assert blockers == {
        "historical_unresolved_blocker_count": 12,
        "effective_unresolved_blocker_count": 12,
        "blockers_closed_by_closure": 0,
        "blocker_ids": sorted(BLOCKER_IDS),
        "historical_stage_counts": {
            "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION": 2,
            "CONFIRMATORY_EXECUTION": 10,
        },
        "effective_stage_counts": {
            "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION": 2,
            "CONFIRMATORY_EXECUTION": 10,
        },
    }

    freeze = value["freeze_predicate_projection"]
    assert freeze == {
        "historical_predicate": EXPECTED_FREEZE_PREDICATE,
        "effective_predicate": EXPECTED_FREEZE_PREDICATE,
        "conditions_closed_by_closure": 0,
        "projection_matches_historical_exactly": True,
    }

    stages = value["staged_freeze_states"]
    assert stages == {
        "required_order": ["R1_A1", "R2_HYBRID", "REAL_DOMAIN_TESTS"],
        "stage_skipping_permitted": False,
        "historical_combined_r1_r2_result_receipt_cannot_gate_r1": True,
        "successor_decomposes_preexecution_and_result_receipts": True,
        "stages": [
            {
                "stage_id": "R1_A1",
                "target_state": "R1_A1_FROZEN_EXECUTABLE",
                "current_state": "NOT_EXECUTABLE",
                "execution_authorized": False,
                "preexecution_freeze_receipt_present": False,
                "result_receipt_present": False,
                "depends_on_prior_stage_results": [],
                "preexecution_requirements": [
                    "VERSIONED_R1_SCIENTIFIC_FREEZE",
                    "NON_OUTCOME_DRIVEN_POWER_AND_SEED_REVIEW",
                    "FORMAL_RUNTIME_IDENTITY_MANIFEST",
                    "TYPED_RUNNER_BINDING",
                    "PRODUCTION_PLAN_AND_PHASE_CUSTODY_BINDING",
                    "R1_PREEXECUTION_FREEZE_RECEIPT",
                ],
                "result_receipts_not_required_before_execution": [
                    "R1_RESULT_RECEIPT",
                    "COMBINED_R1_R2_RESULT_RECEIPT",
                ],
            },
            {
                "stage_id": "R2_HYBRID",
                "target_state": "R2_HYBRID_FROZEN_EXECUTABLE",
                "current_state": "LOCKED_WAITING_FOR_R1_RESULT_RECEIPT",
                "execution_authorized": False,
                "preexecution_freeze_receipt_present": False,
                "result_receipt_present": False,
                "depends_on_prior_stage_results": [
                    "ACCEPTED_R1_RESULT_RECEIPT",
                ],
                "preexecution_requirements": [
                    "R2_PREEXECUTION_FREEZE_RECEIPT",
                ],
                "result_receipts_not_required_before_execution": ["R2_RESULT_RECEIPT"],
            },
            {
                "stage_id": "REAL_DOMAIN_TESTS",
                "target_state": "REAL_DOMAIN_TEST_FROZEN_EXECUTABLE",
                "current_state": ("LOCKED_WAITING_FOR_R1_R2_AND_ALL_REAL_DOMAIN_GATES"),
                "execution_authorized": False,
                "preexecution_freeze_receipt_present": False,
                "result_receipt_present": False,
                "depends_on_prior_stage_results": [
                    "ACCEPTED_R1_RESULT_RECEIPT",
                    "ACCEPTED_R2_RESULT_RECEIPT",
                ],
                "preexecution_requirements": [
                    "REAL_DOMAIN_PREEXECUTION_FREEZE_RECEIPT",
                    "ALL_REAL_DOMAIN_PREEXECUTION_GATES",
                ],
                "result_receipts_not_required_before_execution": [
                    "REAL_DOMAIN_RESULT_RECEIPT"
                ],
            },
        ],
    }

    d1 = value["d1_prior_knowledge_boundary"]
    expected_exact = [
        {"seed": 1729, "accepted_example_budget": None, "method": method}
        for method in ("direct", "guided", "strong_direct")
    ]
    expected_primary = [
        {"seed": 1729, "accepted_example_budget": budget, "method": method}
        for budget in (512, 4096, 32768)
        for method in ("direct", "guided")
    ]
    expected_controls = [
        {"seed": 1729, "accepted_example_budget": budget, "method": method}
        for budget in (512, 4096, 32768)
        for method in ("strong_direct", "guide_input", "mismatch")
    ]
    assert d1 == {
        "d1_is_prior_observed_development_knowledge": True,
        "observed_coordinate": {
            "seed": 1729,
            "accepted_example_budget": 32768,
            "method": "guided",
        },
        "observed_coordinate_is_inside_frozen_primary_grid": True,
        "exposed_seed": 1729,
        "whole_seed_exposure_selector": {
            "seed": 1729,
            "lane": "*",
            "method": "*",
            "accepted_example_budget": "*",
        },
        "whole_seed_exposure_scope": (
            "ALL_METHODS_LANES_AND_BUDGETS_" "WITH_BUDGET_WILDCARD_WHERE_NOT_APPLICABLE"
        ),
        "seed_disposition": "PILOT_NONCONFIRMATORY_EXPOSED",
        "current_grid_examples_are_illustrative_not_exhaustive": True,
        "exposed_current_grid_examples": {
            "exact_budget_not_applicable": expected_exact,
            "primary": expected_primary,
            "controls": expected_controls,
        },
        "replacement_seed_selected": False,
        "seven_seed_confirmatory_design_selected": False,
        "confirmatory_seed_count_selected": False,
        "eligible_for_confirmatory_decision": False,
        "used_for_success_rule_selection": False,
        "may_define_r1_success_from_d1": False,
        "may_change_overflow_policy_from_d1": False,
        "used_for_metric_selection": False,
        "used_for_threshold_selection": False,
        "used_for_checkpoint_selection": False,
        "used_for_seed_selection": False,
        "used_for_overflow_policy_selection": False,
        "d1_admissible_as_production_evidence": False,
        "overflow_exclusion_permitted": False,
        "future_r1_freeze_must_cite_d1_diagnostic_record_raw_sha256": (
            "4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10"
        ),
        "future_r1_freeze_must_cite_e_a1_d1_registration_raw_sha256": (
            "b52685e2b61a30c5781f0e75138eaae6410063fa2312a447eeed7a4d1902cac0"
        ),
        "non_outcome_driven_power_and_seed_review_required": True,
    }

    runtime = value["runtime_and_production_boundary"]
    assert runtime == {
        "formal_runtime_identity_manifest_path": (
            "requirements/m1-reference-macos-arm64-py311.runtime-identity.json"
        ),
        "formal_runtime_identity_manifest_present": False,
        "protected_roots": [
            "artifacts/a1_campaign_v4",
            "artifacts/a1_finite_association_production_order_v1",
        ],
        "protected_roots_present": False,
        "all_checked_production_roots": ALL_PRODUCTION_ROOTS,
        "any_checked_production_root_present": False,
        "production_plan_present": False,
        "production_phase_consumption_present": False,
        "production_coordinate_permit_present": False,
        "rank_result_present": False,
    }

    rank = value["rank_prefix_qualification"]
    assert rank == {
        "qualification_module_path": (
            "research/diagnostics/"
            "finite_association_r1_rank_prefix_binder_qualification.py"
        ),
        "qualification_schema": (
            "heterodiff-manuscript-v3-r1-rank-prefix-binder-qualification-v1"
        ),
        "qualification_record_sha256": (
            "eda18e9599c526750e5179d2cc5eb7091fcea8ed490f4265221fc80465359ad9"
        ),
        "qualification_kind": "STATIC_SCHEMA_AND_CUSTODY_PREFIX_ONLY",
        "status": "R1_RANK_BINDER_QUALIFIED_ZERO_EXECUTION",
        "closed_world_input_count": len(EXPECTED_PREDECESSORS),
        "production_order_source_raw_sha256": (
            "be2b4134672fc2895242d8cbb68d8c540345574f1b31ed8b04a50b88793235e1"
        ),
        "rank_stress_source_raw_sha256": (
            "ead7544be821d58874fd07d4293adc078257f8efb47a82a1e91ea2fa0b702c67"
        ),
        "runtime_identity_source_raw_sha256": (
            "ba10c8053796b6d36bc02a2bea0716a443bba35fd1190333292b87701eb18bf0"
        ),
        "environment_lock_raw_sha256": (
            "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d"
        ),
        "plan_gate_values": {
            "production_order_authority": True,
            "production_execution_authority": False,
            "runner_integration_complete": False,
            "test_only_no_run": False,
            "opaque_evidence_admission_allowed": False,
        },
        "phase_consumption_gate_values": {
            "production_execution_permit_issued": False,
            "runner_binding_complete": False,
            "scientific_execution_authorized": False,
        },
        "implemented_transition_count": 2,
        "furthest_structurally_implemented_state": "RANK_AUTHORIZED",
        "launcher_symbol_observed_but_not_called": True,
        "closed_world_paths_are_static_audit_inputs_not_execution_inputs": True,
        "development_artifacts_admissible_as_r1_execution_inputs": False,
        "development_checkpoints_admissible_as_r1_execution_inputs": False,
        "development_metrics_admissible_as_r1_execution_inputs": False,
        "development_results_admissible_as_r1_execution_inputs": False,
        "excluded_development_artifact_paths": EXCLUDED_DEVELOPMENT_ARTIFACT_PATHS,
        "actual_production_plan_state": "ABSENT",
        "rank_phase_opened": False,
        "rank_phase_authorized": False,
        "production_order_admissible": False,
        "runner_binding_complete": False,
        "production_execution_authorized": False,
        "scientific_execution_authorized": False,
        "confirmatory_execution_authorized": False,
        "qualification_reusable_as_execution_permit": False,
        "plan_initialization_performed": False,
        "phase_consumption_performed": False,
        "coordinate_permit_issued": False,
        "worker_launched": False,
        "rank_computation_performed": False,
        "training_performed": False,
        "explicit_project_artifact_write_performed": False,
    }

    state = value["state_preservation"]
    assert state == {
        "claim_ledger_mutated": False,
        "execution_preregistration_mutated": False,
        "c17_artifact_mutated": False,
        "d1_or_v2_artifact_mutated": False,
        "c17": {
            "ledger_status": "THEOREM-TARGET",
            "closed": False,
            "theorem_proved": False,
        },
        "r1_a1": {
            "status": "NOT RUN",
            "result": "Empty",
            "qualified": False,
        },
        "r2_hybrid": {
            "status": "NOT RUN",
            "result": "Empty",
            "qualified": False,
        },
        "claim_promoted": False,
        "confirmatory_execution_authorized": False,
        "production_execution_authorized": False,
        "scientific_result_eligible": False,
        "readiness_transition_occurred": False,
        "readiness_status": "NOT_READY",
        "readiness_basis": (
            "DIRECTLY_BOUND_CP76_HISTORICAL_SNAPSHOT_NO_LIVE_RECOMPUTATION"
        ),
        "cp76_historical_snapshot_mutated": False,
    }

    anonymity = value["publication_anonymity_boundary"]
    assert anonymity == {
        "internal_closure_not_submission_artifact": True,
        "raw_new_artifact_paths": [
            "manuscript_v3/execution_preregistration_preexecution_closure_v2.md",
            "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
            "research/diagnostics/finite_association_r1_rank_prefix_binder_qualification.py",
            "tests/unit/test_manuscript_v3_execution_preregistration_preexecution_closure_v2.py",
        ],
        "raw_new_artifacts_are_internal_only": True,
        "anonymous_submission_inclusion_permitted": False,
        "public_release_inclusion_permitted": False,
        "raw_v2_artifact_inclusion_permitted": False,
        "in_place_sanitization_permitted": False,
        "publication_safe_derivative_required": True,
        "publication_safe_derivative_path": None,
        "submission_include_exclude_roster_frozen": False,
        "fresh_publication_anonymity_audit_required": True,
    }

    nonclaims = value["nonclaims"]
    assert set(nonclaims) == {
        "r1_qualified",
        "r2_qualified",
        "c17_closed",
        "c17_proved",
        "claim_promoted",
        "confirmatory_execution_authorized",
        "production_execution_authorized",
        "scientific_execution_authorized",
        "scientific_result_eligible",
        "production_plan_created",
        "production_phase_consumed",
        "coordinate_permit_issued",
        "rank_executed",
        "training_executed",
        "d1_rerun",
        "d1_admitted_as_production_evidence",
        "runner_binding_complete",
        "formal_runtime_identity_approved",
        "submission_ready",
        "rank_phase_opened",
        "rank_phase_authorized",
        "production_order_admissible",
    }
    assert all(item is False for item in nonclaims.values())


def test_machine_sidecar_is_strict_canonical_and_self_digest_valid() -> None:
    raw, value = _load(MACHINE_PATH)
    assert raw == _canonical(value) + b"\n"
    assert raw.endswith(b"\n") and raw.count(b"\n") == 1
    claimed = value["record_sha256"]
    assert (
        claimed
        == hashlib.sha256(
            CLOSURE_DOMAIN + _canonical(_without_digest(value))
        ).hexdigest()
    )
    _assert_contract(value)


def test_all_predecessor_bindings_match_exact_current_bytes() -> None:
    _, value = _load(MACHINE_PATH)
    assert set(value["predecessor_bindings"]) == set(EXPECTED_PREDECESSORS)
    for role, (relative_path, expected_hash) in EXPECTED_PREDECESSORS.items():
        expected_row = _file_row(relative_path)
        assert expected_row["raw_sha256"] == expected_hash
        row = value["predecessor_bindings"][role]
        assert set(row) == set(expected_row) | {"semantic_sha256"}
        assert {key: row[key] for key in expected_row} == expected_row
        assert row["semantic_sha256"] == EXPECTED_SEMANTIC_SHA256.get(role)


def test_all_registration_bindings_match_actual_files_and_lf_custody() -> None:
    _, value = _load(MACHINE_PATH)
    expected = {
        "human_closure": (
            "manuscript_v3/execution_preregistration_preexecution_closure_v2.md"
        ),
        "qualification_module": (
            "research/diagnostics/"
            "finite_association_r1_rank_prefix_binder_qualification.py"
        ),
        "focused_test": (
            "tests/unit/"
            "test_manuscript_v3_execution_preregistration_preexecution_closure_v2.py"
        ),
    }
    assert set(value["registration_bindings"]) == set(expected)
    for role, relative_path in expected.items():
        row = value["registration_bindings"][role]
        assert row == _file_row(relative_path)


def test_null_projection_is_independently_recomputed_from_historical_bytes() -> None:
    _, closure = _load(MACHINE_PATH)
    _, prereg = _load(PREREG_PATH)
    null_paths = set(_count_null_paths(prereg))
    assert len(null_paths) == 174
    assert RESOLVED_POINTERS.issubset(null_paths)
    assert DEFERRED_NULL_PATHS.issubset(null_paths)
    assert len(null_paths - DEFERRED_NULL_PATHS) == 168
    effective = null_paths - RESOLVED_POINTERS
    assert len(effective) == 172
    assert len(effective - DEFERRED_NULL_PATHS) == 166
    assert len(effective & DEFERRED_NULL_PATHS) == 6
    assert closure["null_projection"]["deferred_postexecution_null_paths"] == sorted(
        DEFERRED_NULL_PATHS
    )


def test_blockers_and_freeze_predicate_are_independently_recomputed() -> None:
    _, closure = _load(MACHINE_PATH)
    _, prereg = _load(PREREG_PATH)
    blockers = prereg["unresolved_blockers"]
    assert len(blockers) == 12
    assert {item["blocker_id"] for item in blockers} == BLOCKER_IDS
    stage_counts: Dict[str, int] = {}
    for item in blockers:
        stage = item["blocking_stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    assert stage_counts == {
        "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION": 2,
        "CONFIRMATORY_EXECUTION": 10,
    }
    assert closure["blocker_projection"]["blockers_closed_by_closure"] == 0
    assert prereg["freeze_predicate"] == EXPECTED_FREEZE_PREDICATE
    assert (
        closure["freeze_predicate_projection"]["effective_predicate"]
        == prereg["freeze_predicate"]
    )


def test_exact_projected_fields_are_decimal_strings_and_rational_grid() -> None:
    _, closure = _load(MACHINE_PATH)
    by_pointer = {
        item["source_json_pointer"]: item["projected_value"]
        for item in closure["resolved_pre_d1_fields"]
    }
    fixture = by_pointer["/theory_and_known_law_plan/a1_fixture_parameters"]
    assert fixture == EXPECTED_FIXTURE
    decimal_leaves = [
        fixture["horizon"],
        *fixture["birth_rates"],
        *fixture["death_rates_per_occurrence"],
        *[
            item
            for row in fixture["replacement_matrix_row_source_column_destination"]
            for item in row
        ],
        *fixture["initial_capped_factorial_parameter"],
        *fixture["detection_probabilities"],
        *[
            item
            for row in fixture["confusion_matrix_row_source_column_anchor"]
            for item in row
        ],
        *fixture["observation_clutter_rates"],
        fixture["whole_observation_contamination_probability"],
    ]
    assert all(type(item) is str for item in decimal_leaves)
    assert by_pointer["/theory_and_known_law_plan/a1_evaluation_grid"] == EXPECTED_GRID


def test_every_projected_leaf_is_supported_by_its_cited_pre_d1_sources() -> None:
    _, closure = _load(MACHINE_PATH)
    for item in closure["resolved_pre_d1_fields"]:
        assert item["pre_d1_source_bindings"] == EXPECTED_PROJECTED_SOURCE_BINDINGS
        for binding in item["pre_d1_source_bindings"]:
            assert _file_row(binding["path"])["raw_sha256"] == binding["raw_sha256"]

    _, v2 = _load(
        ROOT
        / "research/fixtures/manuscript_v3_a1_development_checkpoint_freeze_v2.json"
    )
    source = v2["fixture"]
    projected = EXPECTED_FIXTURE
    assert Decimal(projected["horizon"]) == Decimal(str(source["horizon"]))
    assert projected["cap"] == source["cap"]
    assert projected["type_count"] == len(source["birth_rates"])
    assert projected["state_count"] == source["state_count"]
    assert projected["observation_count"] == source["observation_count"]
    assert (
        projected["overflow_observation_index"] == source["overflow_observation_index"]
    )
    for projected_key, source_key in (
        ("birth_rates", "birth_rates"),
        ("death_rates_per_occurrence", "death_rates_per_occurrence"),
        (
            "initial_capped_factorial_parameter",
            "initial_capped_factorial_parameter",
        ),
        ("detection_probabilities", "detection_probabilities"),
        ("observation_clutter_rates", "observation_clutter_rates"),
    ):
        assert [Decimal(item) for item in projected[projected_key]] == [
            Decimal(str(item)) for item in source[source_key]
        ]
    for projected_key, source_key in (
        (
            "replacement_matrix_row_source_column_destination",
            "replacement_matrix_row_source_column_destination",
        ),
        ("confusion_matrix_row_source_column_anchor", "confusion_matrix"),
    ):
        assert [
            [Decimal(item) for item in row] for row in projected[projected_key]
        ] == [[Decimal(str(item)) for item in row] for row in source[source_key]]
    assert projected["uniform_observation_reference_mass"] == "1/21"
    assert source["observation_reference"] == "UNIFORM_MASS_1_OVER_21"
    assert Decimal(projected["whole_observation_contamination_probability"]) == Decimal(
        str(source["whole_observation_contamination_probability"])
    )
    assert projected["production_fixture_sha256"] == source["production_fixture_sha256"]
    assert source["evaluation_grid"] == "t_j=j/32_for_j=0,...,32"

    specification = (
        ROOT / "research/62_a1_association_guided_residual_falsification_spec.md"
    ).read_text(encoding="utf-8")
    for literal in (
        "t_j=j/32",
        "beta=(0.38,0.30,0.24)",
        "delta=(0.28,0.34,0.25)",
        "vartheta=(0.65,0.50,0.40)",
        "d=(0.72,0.63,0.68)",
        "nu_{\\rm obs}=(0.10,0.08,0.12)",
        "lambda_A(a)=1/21",
        "epsilon=0.08",
    ):
        assert literal in specification


def test_seed_1729_exposure_is_derived_across_entire_primary_grid() -> None:
    _, closure = _load(MACHINE_PATH)
    seeds = _literal_assignment(ORDER_PATH, "PAIRED_SEEDS")
    budgets = _literal_assignment(ORDER_PATH, "SAMPLE_BUDGETS")
    exact_methods = _literal_assignment(ORDER_PATH, "EXACT_METHODS")
    methods = _literal_assignment(ORDER_PATH, "PRIMARY_METHODS")
    control_methods = _literal_assignment(ORDER_PATH, "CONTROL_METHODS")
    assert seeds == (1729, 3253, 5003, 7411, 10007, 13007, 16001, 20011)
    expected_primary = [
        {"seed": 1729, "accepted_example_budget": budget, "method": method}
        for budget in budgets
        for method in methods
    ]
    expected_controls = [
        {"seed": 1729, "accepted_example_budget": budget, "method": method}
        for budget in budgets
        for method in control_methods
    ]
    expected_exact = [
        {"seed": 1729, "accepted_example_budget": None, "method": method}
        for method in exact_methods
    ]
    d1 = closure["d1_prior_knowledge_boundary"]
    assert d1["whole_seed_exposure_selector"] == {
        "seed": 1729,
        "lane": "*",
        "method": "*",
        "accepted_example_budget": "*",
    }
    assert d1["exposed_current_grid_examples"] == {
        "exact_budget_not_applicable": expected_exact,
        "primary": expected_primary,
        "controls": expected_controls,
    }
    assert d1["current_grid_examples_are_illustrative_not_exhaustive"] is True
    assert d1["observed_coordinate"] in expected_primary
    assert d1["replacement_seed_selected"] is False
    assert d1["seven_seed_confirmatory_design_selected"] is False
    assert d1["confirmatory_seed_count_selected"] is False


def test_qualification_module_returns_bound_deterministic_zero_execution_record() -> None:
    module = _load_qualification_module()
    first = dict(module.audit_r1_rank_prefix(ROOT))
    second = dict(module.audit_r1_rank_prefix(ROOT))
    assert first == second
    assert module.qualification_status(ROOT) == (
        "R1_RANK_BINDER_QUALIFIED_ZERO_EXECUTION"
    )
    claimed = first["record_sha256"]
    body = dict(first)
    del body["record_sha256"]
    assert (
        claimed == hashlib.sha256(QUALIFICATION_DOMAIN + _canonical(body)).hexdigest()
    )
    _, closure = _load(MACHINE_PATH)
    qualified = closure["rank_prefix_qualification"]
    assert qualified["qualification_record_sha256"] == claimed
    assert len(EXPECTED_PREDECESSORS) == 26
    assert len(first["closed_world_input_paths"]) == len(EXPECTED_PREDECESSORS)
    assert qualified["closed_world_input_count"] == len(
        first["closed_world_input_paths"]
    )
    assert (
        first["authority_boundary"]["qualification_reusable_as_execution_permit"]
        is False
    )
    assert (
        first["authority_boundary"][
            "closed_world_paths_are_static_audit_inputs_not_execution_inputs"
        ]
        is True
    )
    for key in (
        "development_artifacts_admissible_as_r1_execution_inputs",
        "development_checkpoints_admissible_as_r1_execution_inputs",
        "development_metrics_admissible_as_r1_execution_inputs",
        "development_results_admissible_as_r1_execution_inputs",
    ):
        assert first["authority_boundary"][key] is False
    assert (
        first["authority_boundary"]["excluded_development_artifact_paths"]
        == EXCLUDED_DEVELOPMENT_ARTIFACT_PATHS
    )
    assert first["authority_boundary"]["actual_production_plan_state"] == "ABSENT"
    for key in (
        "rank_phase_opened",
        "rank_phase_authorized",
        "production_order_admissible",
    ):
        assert first["authority_boundary"][key] is False
    assert (
        first["authority_boundary"]["explicit_project_artifact_write_performed"]
        is False
    )


def test_qualification_api_is_closed_world_and_replay_inputs_are_refused() -> None:
    module = _load_qualification_module()
    assert module.__all__ == (
        "R1RankPrefixQualificationRefusal",
        "audit_r1_rank_prefix",
        "qualification_status",
    )
    signature = inspect.signature(module.audit_r1_rank_prefix)
    assert list(signature.parameters) == ["workspace_root"]
    with pytest.raises(TypeError):
        module.audit_r1_rank_prefix(ROOT, replay_token="forbidden")
    with pytest.raises(TypeError):
        module.audit_r1_rank_prefix(ROOT, evidence={"forbidden": True})


def test_qualification_module_ast_has_only_safe_static_imports_and_no_execution() -> None:
    tree = ast.parse(QUALIFICATION_PATH.read_text(encoding="utf-8"))
    allowed_import_roots = {
        "__future__",
        "ast",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "stat",
        "types",
        "typing",
    }
    imported = set()
    for node in ast.walk(tree):
        if type(node) is ast.Import:
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif type(node) is ast.ImportFrom:
            imported.add((node.module or "").split(".")[0])
    assert imported <= allowed_import_roots
    assert not imported & {"numpy", "scipy", "torch", "subprocess", "heterodiff"}

    called_names = set()
    called_attributes = set()
    for node in ast.walk(tree):
        if type(node) is ast.Call:
            if type(node.func) is ast.Name:
                called_names.add(node.func.id)
            elif type(node.func) is ast.Attribute:
                called_attributes.add(node.func.attr)
    assert not called_names & {
        "initialize_production_order_plan",
        "issue_next_production_coordinate_permit",
        "launch_association_rank_stress_gate",
        "execute_association_rank_stress_gate_in_worker",
        "train",
        "fit",
    }
    assert not called_attributes & {
        "write_bytes",
        "write_text",
        "mkdir",
        "touch",
        "rename",
        "unlink",
        "rmdir",
        "run",
        "Popen",
    }
    assert not any(
        type(node) is ast.If
        and any(
            type(child) is ast.Name and child.id == "__name__"
            for child in ast.walk(node.test)
        )
        for node in tree.body
    )


def _copy_closed_world_inputs(destination: Path) -> None:
    for relative_path, _ in EXPECTED_PREDECESSORS.values():
        source = ROOT / relative_path
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def _mutate_bytes(path: Path) -> None:
    path.write_bytes(path.read_bytes() + b"\nHOSTILE-DRIFT\n")


@pytest.mark.parametrize(
    ("role", "error_code"),
    [
        ("production_order_source", "STALE_BINDING"),
        ("rank_stress_source", "STALE_BINDING"),
        ("execution_preregistration_machine", "STALE_BINDING"),
        ("claim_ledger", "STALE_BINDING"),
        ("a1_v2_freeze_machine", "STALE_BINDING"),
        ("d1_evidence_machine", "STALE_BINDING"),
    ],
)
def test_qualification_refuses_stale_hash_freeze_seed_claim_and_d1_flips(
    tmp_path: Path, role: str, error_code: str
) -> None:
    module = _load_qualification_module()
    _copy_closed_world_inputs(tmp_path)
    relative_path = EXPECTED_PREDECESSORS[role][0]
    _mutate_bytes(tmp_path / relative_path)
    with pytest.raises(module.R1RankPrefixQualificationRefusal, match=error_code):
        module.audit_r1_rank_prefix(tmp_path)


def test_qualification_refuses_formal_runtime_manifest_presence(
    tmp_path: Path,
) -> None:
    module = _load_qualification_module()
    _copy_closed_world_inputs(tmp_path)
    manifest = tmp_path / (
        "requirements/m1-reference-macos-arm64-py311.runtime-identity.json"
    )
    manifest.write_text("{}", encoding="utf-8")
    with pytest.raises(
        module.R1RankPrefixQualificationRefusal,
        match="RUNTIME_MANIFEST_PRESENT",
    ):
        module.audit_r1_rank_prefix(tmp_path)


@pytest.mark.parametrize(
    "relative_path",
    [
        "artifacts/a1_campaign_v4",
        "artifacts/a1_finite_association_production_order_v1",
        "artifacts/a1_rank_stress_gate_v1.json",
    ],
)
def test_qualification_refuses_any_production_root_presence(
    tmp_path: Path, relative_path: str
) -> None:
    module = _load_qualification_module()
    _copy_closed_world_inputs(tmp_path)
    target = tmp_path / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix:
        target.write_text("{}", encoding="utf-8")
    else:
        target.mkdir()
    with pytest.raises(
        module.R1RankPrefixQualificationRefusal,
        match="PRODUCTION_ROOT_PRESENT",
    ):
        module.audit_r1_rank_prefix(tmp_path)


@pytest.mark.parametrize(
    ("path", "bad_value"),
    [
        (("global_state",), "FROZEN_EXECUTABLE"),
        (("scope",), "PRODUCTION_EXECUTION"),
        (("milestone_status",), "R1_EXECUTED"),
        (
            ("null_projection", "effective_total_unresolved_null_count"),
            171,
        ),
        (("blocker_projection", "blockers_closed_by_closure"), 1),
        (
            ("freeze_predicate_projection", "conditions_closed_by_closure"),
            1,
        ),
        (
            ("staged_freeze_states", "stage_skipping_permitted"),
            True,
        ),
        (
            ("d1_prior_knowledge_boundary", "seed_disposition"),
            "CONFIRMATORY",
        ),
        (
            ("d1_prior_knowledge_boundary", "replacement_seed_selected"),
            True,
        ),
        (
            (
                "d1_prior_knowledge_boundary",
                "seven_seed_confirmatory_design_selected",
            ),
            True,
        ),
        (
            ("d1_prior_knowledge_boundary", "eligible_for_confirmatory_decision"),
            True,
        ),
        (
            ("d1_prior_knowledge_boundary", "may_define_r1_success_from_d1"),
            True,
        ),
        (
            ("d1_prior_knowledge_boundary", "may_change_overflow_policy_from_d1"),
            True,
        ),
        (
            (
                "runtime_and_production_boundary",
                "formal_runtime_identity_manifest_present",
            ),
            True,
        ),
        (
            ("runtime_and_production_boundary", "production_plan_present"),
            True,
        ),
        (
            ("rank_prefix_qualification", "runner_binding_complete"),
            True,
        ),
        (
            ("rank_prefix_qualification", "production_execution_authorized"),
            True,
        ),
        (
            ("rank_prefix_qualification", "qualification_reusable_as_execution_permit"),
            True,
        ),
        (
            (
                "rank_prefix_qualification",
                "closed_world_paths_are_static_audit_inputs_not_execution_inputs",
            ),
            False,
        ),
        (
            (
                "rank_prefix_qualification",
                "development_artifacts_admissible_as_r1_execution_inputs",
            ),
            True,
        ),
        (("rank_prefix_qualification", "rank_phase_opened"), True),
        (("rank_prefix_qualification", "rank_phase_authorized"), True),
        (("rank_prefix_qualification", "production_order_admissible"), True),
        (("state_preservation", "claim_promoted"), True),
        (("state_preservation", "scientific_result_eligible"), True),
        (("nonclaims", "rank_executed"), True),
        (
            (
                "publication_anonymity_boundary",
                "anonymous_submission_inclusion_permitted",
            ),
            True,
        ),
    ],
)
def test_semantically_rehashed_hostile_sidecar_flips_are_rejected(
    path: Tuple[str, ...], bad_value: object
) -> None:
    _, original = _load(MACHINE_PATH)
    changed = deepcopy(original)
    cursor: Dict[str, Any] = changed
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = bad_value
    body = _without_digest(changed)
    changed["record_sha256"] = hashlib.sha256(
        CLOSURE_DOMAIN + _canonical(body)
    ).hexdigest()
    with pytest.raises(AssertionError):
        _assert_contract(changed)


def test_unknown_machine_key_is_rejected_even_with_valid_recomputed_digest() -> None:
    _, original = _load(MACHINE_PATH)
    changed = deepcopy(original)
    changed["unaudited_extension"] = True
    body = _without_digest(changed)
    changed["record_sha256"] = hashlib.sha256(
        CLOSURE_DOMAIN + _canonical(body)
    ).hexdigest()
    with pytest.raises(AssertionError):
        _assert_contract(changed)


@pytest.mark.parametrize(
    "section",
    [
        "resolved_pre_d1_fields",
        "blocker_projection",
        "freeze_predicate_projection",
        "staged_freeze_states",
        "d1_prior_knowledge_boundary",
        "runtime_and_production_boundary",
        "rank_prefix_qualification",
        "state_preservation",
        "publication_anonymity_boundary",
        "nonclaims",
    ],
)
def test_unknown_nested_contradiction_is_rejected_after_semantic_rehash(
    section: str,
) -> None:
    _, original = _load(MACHINE_PATH)
    changed = deepcopy(original)
    target = changed[section]
    if section == "resolved_pre_d1_fields":
        target = target[0]
    target["seed_1729_confirmatory_allowed"] = True
    body = _without_digest(changed)
    changed["record_sha256"] = hashlib.sha256(
        CLOSURE_DOMAIN + _canonical(body)
    ).hexdigest()
    with pytest.raises(AssertionError):
        _assert_contract(changed)


def test_human_closure_contains_every_mandatory_visible_boundary() -> None:
    text = HUMAN_PATH.read_text(encoding="utf-8")
    normalized_text = " ".join(text.split())
    required_literals: Iterable[str] = (
        "DRAFT_NOT_EXECUTABLE",
        "R1_RANK_BINDER_QUALIFIED_ZERO_EXECUTION",
        "174 unresolved `null` values",
        "168 pre-execution nulls and six deferred post-execution audit-plan nulls",
        "effective unresolved count is therefore 172",
        "166 pre-execution nulls plus the same six deferred post-execution nulls",
        "None of the 12 unresolved blockers is closed",
        "All ten",
        "both",
        "R1_A1_FROZEN_EXECUTABLE",
        "R2_HYBRID_FROZEN_EXECUTABLE",
        "REAL_DOMAIN_TEST_FROZEN_EXECUTABLE",
        "whole seed `1729`",
        "PILOT_NONCONFIRMATORY_EXPOSED",
        "does not select a seven-seed confirmatory design",
        "choose a replacement seed",
        "does not use D1 to define an R1 success rule",
        "D1 may not change the future overflow policy",
        "every lane, method, and budget",
        "illustrative audited",
        "cannot gate R1 without circularity",
        "pre-execution freeze receipt",
        "R1 does not depend on an R1 post-run result receipt",
        "formal runtime-identity manifest",
        "runner_binding_complete=false",
        "production_execution_authority=false",
        "No production-plan initialization",
        "rank computation",
        "model training",
        "D1 is not admissible as production or confirmatory evidence",
        "`C17` remains",
        "`R1-A1` and `R2-HYBRID` remain",
        "no readiness transition",
        "not anonymous submission artifacts",
        "All four raw artifacts",
        "static-audit input inventory, not an R1 input",
        "V1, V2, and D1 files are reopened only to verify custody",
        "excluded from R1 execution inputs",
        "cannot be relabeled as production checkpoints",
        "no actual rank phase is opened or authorized",
        "production order is not admissible for execution",
    )
    for literal in required_literals:
        assert literal in normalized_text


def test_closure_files_do_not_bind_machine_raw_hash_and_create_no_cycle() -> None:
    machine_hash = hashlib.sha256(MACHINE_PATH.read_bytes()).hexdigest()
    assert machine_hash.encode("ascii") not in HUMAN_PATH.read_bytes()
    assert machine_hash.encode("ascii") not in QUALIFICATION_PATH.read_bytes()
    assert machine_hash.encode("ascii") not in Path(__file__).read_bytes()
