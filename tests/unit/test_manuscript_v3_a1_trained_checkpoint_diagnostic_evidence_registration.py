"""Post-run checks for the additive E-A1-D1 development-evidence register."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import stat
from typing import Any, Dict, Iterable, List, Mapping, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_PATH = ROOT / (
    "research/fixtures/"
    "manuscript_v3_a1_trained_checkpoint_diagnostic_evidence_registration_v1.json"
)
HUMAN_PATH = ROOT / (
    "manuscript_v3/a1_trained_checkpoint_diagnostic_evidence_registration.md"
)
RECORD_PATH = ROOT / (
    "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/"
    "diagnostic-record.json"
)
RECEIPT_PATH = ROOT / (
    "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/"
    "success-receipt.json"
)
MARKER_PATH = ROOT / (
    "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1.attempt.json"
)

REGISTRATION_DOMAIN = (
    b"heterodiff-manuscript-v3-a1-d1-development-evidence-registration-v1\0"
)
D1_RECORD_DOMAIN = b"heterodiff-a1-trained-diagnostic-record-v1\0"
D1_MARKER_DOMAIN = b"heterodiff-a1-trained-diagnostic-attempt-marker-v1\0"

EXPECTED_TOP_KEYS = {
    "schema_version",
    "evidence_id",
    "evidence_class",
    "registration_mode",
    "source_lane_id",
    "source_status",
    "scope",
    "disposition",
    "model_quality_decision",
    "registration_bindings",
    "baseline_bindings",
    "d1_artifact_bindings",
    "checkpoint_custody",
    "coverage",
    "registered_metrics",
    "visible_limitations",
    "source_nonclaims",
    "state_preservation",
    "review_boundary",
    "future_r1_boundary",
    "publication_anonymity_boundary",
    "preregistration_preservation",
    "cp76_live_delta",
    "record_sha256",
}

EXPECTED_BASELINE_HASHES = {
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
    "cp76_readiness_manifest": (
        "research/fixtures/cp76_manuscript_v3_submission_readiness_manifest_v1.json",
        "b9ce9744b64212bf0e762d3342c9a221438c2676ebd9d69db2f50cbbebf9ac06",
    ),
    "cp76_readiness_test": (
        "tests/unit/test_manuscript_v3_submission_readiness.py",
        "410a20e9444e5005481c2bb7c8acef0135061a86ce5bf3ad546fe3fffe83dcbc",
    ),
    "scientific_route_test": (
        "tests/unit/test_manuscript_v3_scientific_route.py",
        "a76b2b7390999d2f43c1a7406f83f8347951d43b9762f3960410de3b188b01ae",
    ),
}

EXPECTED_D1_HASHES = {
    "diagnostic_record": (
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/"
        "diagnostic-record.json",
        "4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10",
        "68434890dbd3157b70e700d6a649000dbc9ee60e297b9196af46e312beba07e6",
    ),
    "success_receipt": (
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1/"
        "success-receipt.json",
        "eabecf04bfe0831fa14d60126c541774aaf25c58283ebb999dc3de2403e9cada",
        "54167cf673861b93db3dd6cd354f9e08796bef59ef19b08ca4b03e59c4a62105",
    ),
    "attempt_marker": (
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1.attempt.json",
        "acfc404eca9ed711279087861518b7e9b32dfdb5fec4aaba318b50e7b4854e14",
        "4d9bdd188be51385d08c4a7540905096ce1f4f856ee313a524542f51684bbeb6",
    ),
    "machine_freeze": (
        "research/fixtures/"
        "manuscript_v3_a1_trained_checkpoint_diagnostic_freeze_v1.json",
        "11d341f65bde47caffcf3c946919c3c0c83254684fb58d0ad643b1874fb3a973",
        None,
    ),
    "human_freeze": (
        "manuscript_v3/a1_trained_checkpoint_diagnostic_freeze.md",
        "59f00d83aba2545ec80b4778cfa181b0a5a0be043bddfb42aef212aaf7533e6d",
        None,
    ),
    "orchestration_source": (
        "research/diagnostics/" "finite_association_trained_checkpoint_diagnostic.py",
        "7cf3a5785f6bb3576357fe8c9bd867955660c2ff2486ca0710c1398e32b1cb0e",
        None,
    ),
    "preexecution_hostile_test": (
        "tests/unit/test_finite_association_trained_checkpoint_diagnostic.py",
        "fda8bafabcb8737035d0b342fd5639a6618900d0a958bd0dbbf0adb827ac0d25",
        None,
    ),
}

EXPECTED_METRICS = [
    (
        "observation_weighted_path_kl",
        "/aggregate_path/observation_weighted_path_kl",
        "0.006581007621322472",
        "SUMMARY",
        "NAT",
    ),
    (
        "retained_observation_law_conditional_mean_path_kl",
        "/aggregate_path/retained_path_kl_mean",
        "0.003631773437855018",
        "SUMMARY",
        "NAT",
    ),
    (
        "overflow_path_kl",
        "/aggregate_path/overflow_path_kl",
        "0.09711382901483998",
        "MANDATORY_LIMITATION",
        "NAT",
    ),
    (
        "observation_weighted_endpoint_total_variation",
        "/aggregate_path/observation_weighted_endpoint_total_variation",
        "0.023690985304278375",
        "SUMMARY",
        "DIMENSIONLESS",
    ),
    (
        "overflow_endpoint_total_variation",
        "/aggregate_path/overflow_endpoint_total_variation",
        "0.11814236369841445",
        "MANDATORY_LIMITATION",
        "DIMENSIONLESS",
    ),
    (
        "overflow_maximum_intermediate_total_variation",
        "/aggregate_path/observations/20/maximum_intermediate_total_variation",
        "0.18287473808256435",
        "MANDATORY_LIMITATION",
        "DIMENSIONLESS",
    ),
    (
        "overflow_observation_mass",
        "/aggregate_path/observations/20/reference/observation_mass",
        "0.03154866637521339",
        "MANDATORY_LIMITATION",
        "PROBABILITY",
    ),
    (
        "overflow_normalized_path_score",
        "/aggregate_path/overflow_normalized_path_score",
        "0.17036802470127654",
        "MANDATORY_LIMITATION",
        "DIMENSIONLESS",
    ),
    (
        "observation_weighted_initial",
        "/family_supplement/observation_weighted_initial",
        "0.00279485108355441",
        "COMPONENT",
        "NAT",
    ),
    (
        "observation_weighted_birth",
        "/family_supplement/observation_weighted_birth",
        "0.0024939882142367",
        "COMPONENT",
        "NAT",
    ),
    (
        "observation_weighted_death",
        "/family_supplement/observation_weighted_death",
        "0.0011921553561048588",
        "COMPONENT",
        "NAT",
    ),
    (
        "observation_weighted_replacement",
        "/family_supplement/observation_weighted_replacement",
        "0.00010001296742650317",
        "COMPONENT",
        "NAT",
    ),
    (
        "maximum_family_aggregate_crosscheck_absolute_difference",
        "/family_supplement/maximum_family_aggregate_crosscheck_absolute_difference",
        "6.938893903907228e-18",
        "NUMERICAL_CROSSCHECK",
        "NAT",
    ),
    (
        "overflow_conditional_initial_total_variation",
        "/nonpath/conditional_initial_tv/overflow",
        "0.11726381207950134",
        "MANDATORY_LIMITATION",
        "DIMENSIONLESS",
    ),
    (
        "normalization_physical_weighted_rmse",
        "/nonpath/coherence/normalization_physical_weighted_rmse",
        "0.02547407630692731",
        "REPORT_ONLY_LIMITATION",
        "DIMENSIONLESS",
    ),
    (
        "normalization_maximum_absolute_residual",
        "/nonpath/coherence/normalization_maximum_absolute_residual",
        "0.15100529268222873",
        "REPORT_ONLY_LIMITATION",
        "DIMENSIONLESS",
    ),
    (
        "semigroup_physical_weighted_rmse",
        "/nonpath/coherence/semigroup_physical_weighted_rmse",
        "0.011197231762216917",
        "REPORT_ONLY_LIMITATION",
        "DIMENSIONLESS",
    ),
    (
        "semigroup_maximum_absolute_residual",
        "/nonpath/coherence/semigroup_maximum_absolute_residual",
        "0.15721987873877863",
        "REPORT_ONLY_LIMITATION",
        "DIMENSIONLESS",
    ),
    (
        "residual_maximum_absolute_error",
        "/nonpath/residual/maximum_absolute_error",
        "1.140606604491632",
        "REPORT_ONLY_LIMITATION",
        "LOG_POTENTIAL",
    ),
]

EXPECTED_NONCLAIMS = {
    "c17_theorem_proved": False,
    "checkpoint_selected_by_diagnostic": False,
    "closes_c17": False,
    "confirmatory_execution_authorized": False,
    "continuous_coordinate_energy_exercised": False,
    "interval_certified": False,
    "manuscript_claim_promoted": False,
    "occurrence_attached_mark_fibers_exercised": False,
    "production_checkpoint": False,
    "production_order_admissible": False,
    "qualifies_r1": False,
    "qualifies_r2": False,
    "real_domain_evidence": False,
    "rigorous_numerical_enclosure_present": False,
    "scientific_result_eligible": False,
    "training_performed_by_diagnostic": False,
}

EXPECTED_STATE = {
    "claim_ledger_mutated": False,
    "claim_row_changes": [],
    "result_slot_changes": [],
    "legacy_claim_ledger_row_added": False,
    "registered_via_additive_sidecar": True,
    "c17": {
        "ledger_status": "THEOREM-TARGET",
        "closed": False,
        "theorem_proved": False,
    },
    "r1_a1": {"status": "NOT RUN", "result": "Empty", "qualified": False},
    "r2_hybrid": {
        "status": "NOT RUN",
        "result": "Empty",
        "qualified": False,
    },
    "execution_preregistration": {
        "mutated": False,
        "state": "DRAFT_NOT_EXECUTABLE",
        "confirmatory_execution_authorized": False,
    },
    "cp76": {
        "mutated": False,
        "historical_snapshot": True,
        "superseded": False,
        "readiness_status": "NOT_READY",
        "manuscript_submission_ready": False,
        "readiness_transition": "NONE",
    },
    "manuscript_prose_changed": False,
    "claim_promotion": False,
    "scientific_result_eligible": False,
    "confirmatory_execution_authorized": False,
    "production_order_admissible": False,
    "production_execution_authorized": False,
}

EXPECTED_LIMITATIONS = {
    "overflow_weakness_must_remain_visible": True,
    "retained_summary_may_not_substitute_for_overflow": True,
    "normalization_and_semigroup_residuals_are_report_only": True,
    "residual_error_is_report_only": True,
    "learned_quality_acceptance_threshold": None,
    "post_result_threshold_introduced": False,
    "adaptive_binary64_is_interval_proof": False,
    "simultaneous_coverage_proved": False,
    "continuous_component_disposition": ("NOT_APPLICABLE_NO_CONTINUOUS_COORDINATES"),
    "continuous_component_numeric_zero_reported": False,
    "all_atomic_subject_only": True,
    "occurrence_attached_mark_fibers_exercised": False,
    "real_domain_evidence": False,
    "production_checkpoint": False,
    "training_performed_by_diagnostic": False,
    "checkpoint_selected_by_diagnostic": False,
    "production_bound_field_value": True,
    "production_bound_means_success_ledger_custody_only": True,
    "production_bound_grants_production_or_scientific_status": False,
}

EXPECTED_REVIEW_BOUNDARY = {
    "external_reviewer_panel_required_for_registration": False,
    "durable_independent_review_artifact": None,
    "transient_review_promoted_to_durable_artifact": False,
    "focused_postrun_static_validation_required": True,
    "focused_postrun_validation_launches_d1": False,
    "claim_promotion_review_still_required": True,
    "proof_review_still_required_for_c17": True,
}

EXPECTED_FUTURE_R1_BOUNDARY = {
    "d1_is_prior_observed_development_knowledge": True,
    "future_r1_freeze_must_cite_diagnostic_record_raw_sha256": (
        "4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10"
    ),
    "may_select_primary_metric_from_d1": False,
    "may_select_acceptance_threshold_from_d1": False,
    "may_select_checkpoint_from_d1": False,
    "may_select_seed_count_from_d1": False,
    "may_change_overflow_policy_from_d1": False,
    "may_exclude_overflow": False,
    "may_define_r1_success_from_d1": False,
    "post_d1_outcome_driven_design_controls_required": True,
    "eligible_for_confirmatory_decision": False,
    "used_for_threshold_selection": False,
    "used_for_checkpoint_selection": False,
    "used_for_metric_selection": False,
    "used_for_seed_selection": False,
    "used_for_overflow_policy_selection": False,
}

EXPECTED_PUBLICATION_BOUNDARY = {
    "internal_registration_not_submission_artifact": True,
    "anonymous_submission_inclusion_permitted": False,
    "public_release_inclusion_permitted": False,
    "raw_v2_artifact_inclusion_permitted": False,
    "raw_v2_contains_local_path_metadata": True,
    "raw_v2_contains_process_metadata": True,
    "raw_v2_contains_timestamp_metadata": True,
    "raw_v2_contains_runtime_metadata": True,
    "in_place_sanitization_permitted": False,
    "publication_safe_derivative_required": True,
    "publication_safe_derivative_path": None,
    "submission_include_exclude_roster_frozen": False,
    "fresh_publication_anonymity_audit_required": True,
}

EXPECTED_FREEZE_PREDICATE = {
    "all_claim_promotion_and_submission_blockers_closed": False,
    "all_confirmatory_execution_blockers_closed": False,
    "all_required_preexecution_artifacts_present_and_hash_bound": False,
    "all_required_preexecution_scientific_semantic_and_numeric_fields_nonnull": (False),
    "claim_boundary_approved": False,
    "claim_promotion_or_submission_permitted": False,
    "current_state": "DRAFT_NOT_EXECUTABLE",
    "domain_admission_complete": False,
    "freeze_receipt_present": False,
    "frozen_executable_state_if_and_only_if_execution_predicates_true": (
        "FROZEN_EXECUTABLE"
    ),
    "known_law_and_whole_method_gates_complete": False,
    "power_review_complete": False,
    "test_data_unopened_before_freeze": None,
}

EXPECTED_PREREGISTRATION_PRESERVATION = {
    "unresolved_null_count": 174,
    "unresolved_blocker_count": 12,
    "blocker_stage_counts": {
        "CONFIRMATORY_EXECUTION": 10,
        "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION": 2,
    },
    "required_preexecution_null_fields_are_execution_blocking": True,
    "postexecution_audit_plan_nulls_are_execution_blocking": False,
    "postexecution_audit_plan_nulls_block_claim_promotion_and_submission": True,
    "nulls_closed_by_registration": 0,
    "blockers_closed_by_registration": 0,
    "freeze_conditions_closed_by_registration": 0,
    "freeze_predicate": EXPECTED_FREEZE_PREDICATE,
}

EXPECTED_REMAINING_SUPPORT_PATHS = [
    "manuscript_v3/configuration_reference_code_audit.md",
    "manuscript_v3/reversible_hybrid_reference_code_audit.md",
    "manuscript_v3/reverse_energy_objective_code_audit.md",
    "manuscript_v3/association_observation_code_audit.md",
    "manuscript_v3/association_preconditioner_code_audit.md",
    "manuscript_v3/configuration_energy_code_audit.md",
]

EXPECTED_CP76_LIVE_DELTA = {
    "historical_missing_unique_count": 8,
    "historically_missing_paths_now_present": [
        "manuscript_v3/novelty_audit_matrix.md",
        "manuscript_v3/execution_preregistration.md",
    ],
    "live_remaining_missing_unique_count": 6,
    "live_remaining_missing_paths": EXPECTED_REMAINING_SUPPORT_PATHS,
    "live_presence_delta_is_non_authoritative": True,
    "cp76_historical_snapshot_rewritten": False,
    "novelty_independently_assessed_criterion_state": "BLOCKED",
    "execution_preregistered_criterion_state": "BLOCKED",
    "readiness_status": "NOT_READY",
    "manuscript_submission_ready": False,
    "readiness_transition": "NONE",
}

EXPECTED_COVERAGE = {
    "time_count": 33,
    "state_count": 20,
    "observation_count": 21,
    "nonpath_grid_shape": [33, 20, 21],
    "all_33_nonpath_evaluated": True,
    "all_21_path_reference_preflight_passed": True,
    "all_21_aggregate_path_evaluated": True,
    "all_21_family_supplement_evaluated": True,
    "canonical_observation_order_used": True,
    "evidence_binder_completed": True,
    "reference_set_sha256": (
        "000000831290fe27cd1f49fb1b180fea33e39e47ad0e0d62d38eab274c39dbd5"
    ),
    "active_edge_counts": {"birth": 30, "death": 30, "replacement": 60},
    "continuous_component_disposition": ("NOT_APPLICABLE_NO_CONTINUOUS_COORDINATES"),
}

EXPECTED_CUSTODY = {
    "source_artifact_root": "artifacts/manuscript_v3_a1_development_checkpoint_v2",
    "outer_success_receipt_raw_sha256": (
        "7c730742f38c0ad1dbfd023ee65851328f3655769ae58d23e6cdca8bbb11b885"
    ),
    "outer_success_receipt_self_sha256": (
        "154d64d654a4f175f07e323524782f90af29dbbb5f81c053ce0105a67dbfe747"
    ),
    "inner_success_receipt_sha256": (
        "df4c5770f10350e4f0a0267842de775731349de67cc282cec1e6bbddfc7bc6cc"
    ),
    "checkpoint_sha256": (
        "e414fc880a04df2a868855c195666ce400ca3f975278900aaa450032b6c66e7c"
    ),
    "run_key_sha256": (
        "dc7484372d3f8a633755450bda9d70f0ed182005dba052a0fa86747ae0fe4f70"
    ),
    "parameter_sha256": (
        "d0bf29778dd866f5cd752f76be39df05d8dc2d6a89476070b77dd25326530388"
    ),
    "classifier_sha256": (
        "5f35eddd4354b2ecf77abb9e01b46fbedf17bb917727827478a9bbc11cd3f14e"
    ),
    "campaign_sha256": (
        "5bdf07f03e5f6ebb0340c6a55a3f9af45a89ee2010232650faa8cab54dc98508"
    ),
    "fixture_sha256": (
        "0121b487728b40356de6707a33ba4881100c3d1b587259b19723463a60cecdcc"
    ),
    "path_content_sha256": (
        "ba9de201cdf249d9c2adeb07202075e20765e0bab637ce79668fde245b19f67f"
    ),
    "path_runtime_sha256": (
        "4992cb102180bb6e6bf76a70280a19a6ca0952b5148c662c331ebafcbb504cda"
    ),
    "optimizer_steps_in_source_training": 3000,
    "optimizer_steps_in_diagnostic": 0,
    "checkpoint_loaded_through_canonical_success_ledger": True,
    "checkpoint_revalidated_after_diagnostics": True,
    "checkpoint_selected_by_diagnostic": False,
    "checkpoint_mutation_permitted": False,
}


def _no_duplicate_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise AssertionError("nonfinite JSON constant: " + value)


def _parse_json(raw: bytes, *, decimal: bool = False) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {
        "object_pairs_hook": _no_duplicate_object,
        "parse_constant": _reject_constant,
    }
    if decimal:
        kwargs["parse_float"] = Decimal
    value = json.loads(raw.decode("utf-8"), **kwargs)
    assert isinstance(value, dict)
    return value


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _self_digest(record: Mapping[str, Any], *, field: str, domain: bytes) -> str:
    projected = dict(record)
    projected.pop(field, None)
    return _sha256(domain + _canonical_json_bytes(projected))


def _walk(value: object) -> Iterable[object]:
    yield value
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _assert_file_row(row: Mapping[str, Any]) -> None:
    assert set(row) == {
        "path",
        "bytes",
        "lf_count",
        "terminal_lf",
        "raw_sha256",
        "semantic_sha256",
    }
    path = ROOT / str(row["path"])
    assert path.is_file() and not path.is_symlink()
    assert stat.S_ISREG(path.stat().st_mode)
    raw = path.read_bytes()
    assert len(raw) == row["bytes"]
    assert raw.count(b"\n") == row["lf_count"]
    assert raw.endswith(b"\n") is row["terminal_lf"]
    assert _sha256(raw) == row["raw_sha256"]


def _pointer(document: object, pointer: str) -> object:
    assert pointer.startswith("/")
    value = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(part)]
        else:
            assert isinstance(value, dict)
            value = value[part]
    return value


def _metric_projection(
    document: Mapping[str, Any]
) -> List[Tuple[str, str, str, str, str]]:
    return [
        (
            str(row["metric_id"]),
            str(row["source_json_pointer"]),
            str(row["decimal"]),
            str(row["role"]),
            str(row["unit"]),
        )
        for row in document["registered_metrics"]
    ]


def _require_contract(document: Mapping[str, Any]) -> None:
    assert set(document) == EXPECTED_TOP_KEYS
    assert document["schema_version"] == (
        "heterodiff-manuscript-v3-a1-d1-development-evidence-registration-v1"
    )
    assert document["evidence_id"] == "E-A1-D1"
    assert document["evidence_class"] == "NONCONFIRMATORY_DEVELOPMENT_EVIDENCE"
    assert document["registration_mode"] == "ADDITIVE_LEDGER_SIDECAR"
    assert document["source_lane_id"] == ("A1-D1-TRAINED-CHECKPOINT-DIAGNOSTIC-V1")
    assert document["source_status"] == "COMPLETE_FINITE_KNOWN_LAW_DIAGNOSTIC"
    assert document["scope"] == "TRAINED_DEVELOPMENT_CHECKPOINT_DIAGNOSTIC_ONLY"
    assert document["disposition"] == "PASS_WITH_EXPLICIT_SCOPE_LIMITS"
    assert document["model_quality_decision"] == "NOT_MADE"
    assert document["visible_limitations"] == EXPECTED_LIMITATIONS
    assert document["source_nonclaims"] == EXPECTED_NONCLAIMS
    assert document["state_preservation"] == EXPECTED_STATE
    assert document["review_boundary"] == EXPECTED_REVIEW_BOUNDARY
    assert document["future_r1_boundary"] == EXPECTED_FUTURE_R1_BOUNDARY
    assert document["publication_anonymity_boundary"] == (EXPECTED_PUBLICATION_BOUNDARY)
    assert document["preregistration_preservation"] == (
        EXPECTED_PREREGISTRATION_PRESERVATION
    )
    assert document["cp76_live_delta"] == EXPECTED_CP76_LIVE_DELTA
    assert document["coverage"] == EXPECTED_COVERAGE
    assert document["checkpoint_custody"] == EXPECTED_CUSTODY
    assert _metric_projection(document) == EXPECTED_METRICS
    assert set(document["registration_bindings"]) == {
        "human_registration",
        "postrun_test",
    }
    for row in document["registration_bindings"].values():
        _assert_file_row(row)
    assert set(document["baseline_bindings"]) == set(EXPECTED_BASELINE_HASHES)
    for identity, (path, raw_sha256) in EXPECTED_BASELINE_HASHES.items():
        row = document["baseline_bindings"][identity]
        assert row["path"] == path
        assert row["raw_sha256"] == raw_sha256
        assert row["semantic_sha256"] is None
        _assert_file_row(row)
    assert document["d1_artifact_bindings"]["output_root"] == (
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1"
    )
    assert document["d1_artifact_bindings"]["expected_output_regular_files"] == [
        "diagnostic-record.json",
        "success-receipt.json",
    ]
    assert document["d1_artifact_bindings"]["preexecution_test_role"] == (
        "FROZEN_INPUT_NOT_POSTRUN_TEST"
    )
    d1_files = document["d1_artifact_bindings"]["files"]
    assert set(d1_files) == set(EXPECTED_D1_HASHES)
    for identity, (path, raw_sha256, semantic_sha256) in EXPECTED_D1_HASHES.items():
        row = d1_files[identity]
        assert row["path"] == path
        assert row["raw_sha256"] == raw_sha256
        assert row["semantic_sha256"] == semantic_sha256
        _assert_file_row(row)
    assert document["record_sha256"] == _self_digest(
        document, field="record_sha256", domain=REGISTRATION_DOMAIN
    )


def _rehash(document: Dict[str, Any]) -> None:
    document["record_sha256"] = _self_digest(
        document, field="record_sha256", domain=REGISTRATION_DOMAIN
    )


def _load_registration() -> Tuple[bytes, Dict[str, Any]]:
    raw = REGISTRATION_PATH.read_bytes()
    return raw, _parse_json(raw)


def test_registration_is_canonical_closed_and_self_addressed() -> None:
    raw, registration = _load_registration()
    assert raw == _canonical_json_bytes(registration)
    assert not raw.endswith(b"\n")
    assert not any(isinstance(item, float) for item in _walk(registration))
    _require_contract(registration)

    assert set(registration["registration_bindings"]) == {
        "human_registration",
        "postrun_test",
    }
    for row in registration["registration_bindings"].values():
        _assert_file_row(row)
    assert registration["registration_bindings"]["human_registration"]["path"] == (
        HUMAN_PATH.relative_to(ROOT).as_posix()
    )
    assert registration["registration_bindings"]["postrun_test"]["path"] == (
        Path(__file__).resolve().relative_to(ROOT).as_posix()
    )


def test_baseline_snapshots_are_bound_without_mutation() -> None:
    _, registration = _load_registration()
    rows = registration["baseline_bindings"]
    assert set(rows) == set(EXPECTED_BASELINE_HASHES)
    for identity, (path, raw_sha256) in EXPECTED_BASELINE_HASHES.items():
        row = rows[identity]
        _assert_file_row(row)
        assert row["path"] == path
        assert row["raw_sha256"] == raw_sha256
        assert row["semantic_sha256"] is None


def test_d1_output_custody_and_self_digests_reopen_independently() -> None:
    _, registration = _load_registration()
    bindings = registration["d1_artifact_bindings"]
    assert bindings["output_root"] == (
        "artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1"
    )
    assert bindings["expected_output_regular_files"] == [
        "diagnostic-record.json",
        "success-receipt.json",
    ]
    assert bindings["preexecution_test_role"] == "FROZEN_INPUT_NOT_POSTRUN_TEST"
    assert set(bindings["files"]) == set(EXPECTED_D1_HASHES)
    for identity, (path, raw_sha256, semantic_sha256) in EXPECTED_D1_HASHES.items():
        row = bindings["files"][identity]
        _assert_file_row(row)
        assert row["path"] == path
        assert row["raw_sha256"] == raw_sha256
        assert row["semantic_sha256"] == semantic_sha256

    output = ROOT / bindings["output_root"]
    assert output.is_dir() and not output.is_symlink()
    assert sorted(path.name for path in output.iterdir()) == (
        bindings["expected_output_regular_files"]
    )
    assert all(path.is_file() and not path.is_symlink() for path in output.iterdir())

    record = _parse_json(RECORD_PATH.read_bytes())
    receipt = _parse_json(RECEIPT_PATH.read_bytes())
    marker = _parse_json(MARKER_PATH.read_bytes())
    assert record["diagnostic_record_sha256"] == _self_digest(
        record, field="diagnostic_record_sha256", domain=D1_RECORD_DOMAIN
    )
    assert receipt["receipt_sha256"] == _self_digest(
        receipt, field="receipt_sha256", domain=b""
    )
    assert marker["record_sha256"] == _self_digest(
        marker, field="record_sha256", domain=D1_MARKER_DOMAIN
    )
    assert receipt["diagnostic_record_raw_sha256"] == _sha256(RECORD_PATH.read_bytes())
    assert receipt["diagnostic_record_sha256"] == record["diagnostic_record_sha256"]
    assert receipt["attempt_marker_raw_sha256"] == _sha256(MARKER_PATH.read_bytes())
    assert receipt["attempt_marker_record_sha256"] == marker["record_sha256"]
    assert marker["state"] == "ATTEMPT_CONSUMED_NONRETRYABLE"
    assert marker["attempt_number"] == 1
    assert marker["retry_permitted"] is False
    assert marker["resume_permitted"] is False
    assert marker["training_permitted"] is False

    for field in (
        "freeze_sha256",
        "human_freeze_sha256",
        "implementation_sha256",
    ):
        assert record[field] == receipt[field]
    assert (
        receipt["test_sha256"]
        == bindings["files"]["preexecution_hostile_test"]["raw_sha256"]
    )
    assert receipt["training_performed"] is False
    assert receipt["qualifies_r1"] is False
    assert receipt["qualifies_r2"] is False
    assert receipt["closes_c17"] is False
    assert receipt["manuscript_claim_promoted"] is False
    assert receipt["production_order_admissible"] is False
    assert receipt["confirmatory_execution_authorized"] is False


def test_complete_coverage_metrics_and_limitations_are_exact_projections() -> None:
    _, registration = _load_registration()
    record = _parse_json(RECORD_PATH.read_bytes(), decimal=True)
    coverage = registration["coverage"]
    assert coverage == EXPECTED_COVERAGE
    assert record["coverage"] == {
        "all_21_aggregate_path_evaluated": True,
        "all_21_family_supplement_evaluated": True,
        "all_21_path_reference_preflight_passed": True,
        "all_33_nonpath_evaluated": True,
        "canonical_observation_order_used": True,
        "evidence_binder_completed": True,
    }
    assert len(record["path_reference_preflight"]["references"]) == 21
    assert len(record["aggregate_path"]["observations"]) == 21
    assert len(record["family_supplement"]["observations"]) == 21
    assert [
        row["reference"]["observation_index"]
        for row in record["aggregate_path"]["observations"]
    ] == list(range(21))
    assert [
        row["observation_index"] for row in record["family_supplement"]["observations"]
    ] == list(range(21))
    assert record["nonpath"]["classifier_logit_grid"]["shape"] == [33, 20, 21]
    assert (
        record["aggregate_path"]["reference_set_sha256"]
        == coverage["reference_set_sha256"]
    )
    assert record["family_supplement"]["active_edge_counts"] == [30, 30, 60]
    assert record["family_supplement"]["continuous_component_disposition"] == (
        coverage["continuous_component_disposition"]
    )

    for row in registration["registered_metrics"]:
        assert set(row) == {
            "metric_id",
            "source_json_pointer",
            "decimal",
            "role",
            "unit",
        }
        source_value = _pointer(record, row["source_json_pointer"])
        assert isinstance(source_value, Decimal)
        projected = Decimal(row["decimal"])
        assert projected.is_finite()
        assert projected == source_value
    metric_map = {
        row["metric_id"]: Decimal(row["decimal"])
        for row in registration["registered_metrics"]
    }
    assert (
        metric_map["overflow_path_kl"]
        > metric_map["retained_observation_law_conditional_mean_path_kl"]
    )
    assert (
        metric_map["overflow_endpoint_total_variation"]
        > metric_map["observation_weighted_endpoint_total_variation"]
    )
    assert metric_map["overflow_maximum_intermediate_total_variation"] > (
        metric_map["overflow_endpoint_total_variation"]
    )
    assert record["numerical_disposition"]["all_required_checks_passed"] is True
    assert (
        record["numerical_disposition"]["adaptive_float64_not_interval_proof"] is True
    )
    assert record["nonclaims"] == EXPECTED_NONCLAIMS
    assert record["nonpath"]["production_bound"] is True
    assert record["aggregate_path"]["production_bound"] is True
    assert (
        registration["visible_limitations"][
            "production_bound_means_success_ledger_custody_only"
        ]
        is True
    )


def test_checkpoint_custody_is_exact_and_does_not_select_or_train() -> None:
    _, registration = _load_registration()
    record = _parse_json(RECORD_PATH.read_bytes())
    custody = registration["checkpoint_custody"]
    assert custody == EXPECTED_CUSTODY
    for key in (
        "source_artifact_root",
        "outer_success_receipt_raw_sha256",
        "outer_success_receipt_self_sha256",
        "inner_success_receipt_sha256",
        "checkpoint_sha256",
        "run_key_sha256",
        "parameter_sha256",
        "classifier_sha256",
        "campaign_sha256",
        "fixture_sha256",
        "path_content_sha256",
        "path_runtime_sha256",
    ):
        assert record["checkpoint_custody"][key] == custody[key]
    assert record["checkpoint_custody"]["optimizer_steps_taken"] == 3000
    assert record["nonclaims"]["training_performed_by_diagnostic"] is False
    assert record["nonclaims"]["checkpoint_selected_by_diagnostic"] is False


def test_claim_preregistration_and_cp76_states_remain_unpromoted() -> None:
    _, registration = _load_registration()
    state = registration["state_preservation"]
    ledger = (ROOT / "manuscript_v3/claim_ledger.md").read_text("utf-8")
    claim_rows = {
        match.group(1): match.group(2)
        for match in re.finditer(
            r"^\| (C\d+) \|.*?\| \*\*(.*?)\*\* \|", ledger, re.MULTILINE
        )
    }
    assert len(claim_rows) == 21
    assert claim_rows["C17"] == state["c17"]["ledger_status"]

    slots: Dict[str, Tuple[str, str]] = {}
    for line in ledger.splitlines():
        if line.startswith("| R1-A1 ") or line.startswith("| R2-HYBRID "):
            fields = [field.strip() for field in line.strip().strip("|").split("|")]
            slots[fields[0]] = (fields[-2], fields[-1].replace("**", ""))
    assert slots["R1-A1"] == (state["r1_a1"]["result"], state["r1_a1"]["status"])
    assert slots["R2-HYBRID"] == (
        state["r2_hybrid"]["result"],
        state["r2_hybrid"]["status"],
    )

    prereg_human = (ROOT / "manuscript_v3/execution_preregistration.md").read_text(
        "utf-8"
    )
    prereg_machine = _parse_json(
        (
            ROOT / "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
        ).read_bytes()
    )
    assert "**State:** `DRAFT_NOT_EXECUTABLE`" in prereg_human
    assert "**Confirmatory execution authorized:** no" in prereg_human
    assert prereg_machine["state"] == state["execution_preregistration"]["state"]
    assert prereg_machine["confirmatory_execution_authorized"] is False
    slot_projection = {
        row["slot_id"]: (row["current_result"], row["current_status"])
        for row in prereg_machine["slot_plan"]
    }
    assert slot_projection["R1-A1"] == ("Empty", "NOT_RUN")
    assert slot_projection["R2-HYBRID"] == ("Empty", "NOT_RUN")

    cp76 = _parse_json(
        (
            ROOT
            / "research/fixtures/cp76_manuscript_v3_submission_readiness_manifest_v1.json"
        ).read_bytes()
    )
    assert cp76["readiness_status"] == state["cp76"]["readiness_status"]
    assert cp76["manuscript_submission_ready"] is False
    assert cp76["manuscript_submission_disposition"] == "NOT_READY_FOR_SUBMISSION"
    assert (
        cp76["claim_ledger_observation"]["promoted_empirical_result_claim_count"] == 0
    )
    result_slots = {
        row["id"]: (row["result_cell"], row["status"])
        for row in cp76["claim_ledger_observation"]["result_slots"]
    }
    assert result_slots["R1-A1"] == ("Empty", "NOT RUN")
    assert result_slots["R2-HYBRID"] == ("Empty", "NOT RUN")


def test_preregistration_nulls_blockers_and_freeze_predicate_are_preserved() -> None:
    _, registration = _load_registration()
    observed = registration["preregistration_preservation"]
    preregistration = _parse_json(
        (
            ROOT / "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
        ).read_bytes()
    )
    assert sum(item is None for item in _walk(preregistration)) == (
        observed["unresolved_null_count"]
    )
    blockers = preregistration["unresolved_blockers"]
    assert len(blockers) == observed["unresolved_blocker_count"]
    assert (
        dict(Counter(row["blocking_stage"] for row in blockers))
        == observed["blocker_stage_counts"]
    )
    assert preregistration["freeze_predicate"] == observed["freeze_predicate"]
    assert observed["freeze_predicate"] == EXPECTED_FREEZE_PREDICATE
    assert observed["required_preexecution_null_fields_are_execution_blocking"] is True
    assert observed["postexecution_audit_plan_nulls_are_execution_blocking"] is False
    assert (
        observed["postexecution_audit_plan_nulls_block_claim_promotion_and_submission"]
        is True
    )
    audit_plan_blocker = next(
        row
        for row in blockers
        if row["blocker_id"] == "proof-methods-statistics-and-reproduction-audit-plans"
    )
    assert audit_plan_blocker["blocking_stage"] == (
        "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION"
    )
    assert all(
        _pointer(preregistration, pointer) is None
        for pointer in audit_plan_blocker["blocking_json_paths"]
    )
    assert observed["nulls_closed_by_registration"] == 0
    assert observed["blockers_closed_by_registration"] == 0
    assert observed["freeze_conditions_closed_by_registration"] == 0
    assert preregistration["state"] == "DRAFT_NOT_EXECUTABLE"
    assert preregistration["confirmatory_execution_authorized"] is False


def test_cp76_historical_to_live_support_delta_is_derived_without_promotion() -> None:
    _, registration = _load_registration()
    delta = registration["cp76_live_delta"]
    cp76 = _parse_json(
        (
            ROOT
            / "research/fixtures/cp76_manuscript_v3_submission_readiness_manifest_v1.json"
        ).read_bytes()
    )
    inventory = cp76["direct_manuscript_support_inventory"]
    historical_missing = inventory["missing_paths"]
    assert inventory["missing_unique_count"] == delta["historical_missing_unique_count"]
    now_present = [path for path in historical_missing if (ROOT / path).is_file()]
    still_missing = [path for path in historical_missing if not (ROOT / path).exists()]
    assert now_present == delta["historically_missing_paths_now_present"]
    assert still_missing == delta["live_remaining_missing_paths"]
    assert len(still_missing) == delta["live_remaining_missing_unique_count"] == 6
    assert still_missing == EXPECTED_REMAINING_SUPPORT_PATHS

    criteria = {row["id"]: row for row in cp76["readiness_criteria"]}
    assert (
        criteria["novelty-independently-assessed"]["state"]
        == delta["novelty_independently_assessed_criterion_state"]
    )
    assert (
        criteria["execution-preregistered"]["state"]
        == delta["execution_preregistered_criterion_state"]
    )
    assert cp76["readiness_status"] == delta["readiness_status"] == "NOT_READY"
    assert cp76["manuscript_submission_ready"] is False
    assert delta["readiness_transition"] == "NONE"
    assert delta["live_presence_delta_is_non_authoritative"] is True
    assert delta["cp76_historical_snapshot_rewritten"] is False
    novelty = (ROOT / "manuscript_v3/novelty_audit_matrix.md").read_text("utf-8")
    assert "`METHOD-NOVELTY-GO` remains false" in novelty
    preregistration = (ROOT / "manuscript_v3/execution_preregistration.md").read_text(
        "utf-8"
    )
    assert "**State:** `DRAFT_NOT_EXECUTABLE`" in preregistration


def test_publication_anonymity_boundary_is_fail_closed_and_factually_grounded() -> None:
    _, registration = _load_registration()
    boundary = registration["publication_anonymity_boundary"]
    assert boundary == EXPECTED_PUBLICATION_BOUNDARY
    assert boundary["internal_registration_not_submission_artifact"] is True
    assert boundary["anonymous_submission_inclusion_permitted"] is False
    assert boundary["public_release_inclusion_permitted"] is False
    assert boundary["raw_v2_artifact_inclusion_permitted"] is False
    assert boundary["in_place_sanitization_permitted"] is False
    assert boundary["publication_safe_derivative_required"] is True
    assert boundary["publication_safe_derivative_path"] is None
    assert boundary["submission_include_exclude_roster_frozen"] is False
    assert boundary["fresh_publication_anonymity_audit_required"] is True

    raw_v2 = (
        ROOT
        / "artifacts/manuscript_v3_a1_development_checkpoint_v2/success-receipt.json"
    ).read_bytes()
    assert b"/private/" in raw_v2
    assert b'"worker_process_id"' in raw_v2
    assert b'"finished_unix_ns"' in raw_v2
    assert b'"execution_runtime_record"' in raw_v2
    assert boundary["raw_v2_contains_local_path_metadata"] is True
    assert boundary["raw_v2_contains_process_metadata"] is True
    assert boundary["raw_v2_contains_timestamp_metadata"] is True
    assert boundary["raw_v2_contains_runtime_metadata"] is True


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value.update(model_quality_decision="PASS"),
        lambda value: value["state_preservation"].update(claim_promotion=True),
        lambda value: value["state_preservation"]["c17"].update(closed=True),
        lambda value: value["state_preservation"]["r1_a1"].update(
            status="COMPLETE", qualified=True
        ),
        lambda value: value["state_preservation"]["r2_hybrid"].update(
            status="COMPLETE", qualified=True
        ),
        lambda value: value["state_preservation"]["cp76"].update(
            readiness_status="READY", manuscript_submission_ready=True
        ),
        lambda value: value["state_preservation"].update(
            production_execution_authorized=True
        ),
        lambda value: value["state_preservation"].update(
            scientific_result_eligible=True
        ),
        lambda value: value["source_nonclaims"].update(interval_certified=True),
        lambda value: value["visible_limitations"].update(
            overflow_weakness_must_remain_visible=False
        ),
        lambda value: value["visible_limitations"].update(
            normalization_and_semigroup_residuals_are_report_only=False
        ),
        lambda value: value["registered_metrics"].__setitem__(
            2,
            {
                **value["registered_metrics"][2],
                "decimal": "0.003631773437855018",
            },
        ),
        lambda value: value["review_boundary"].update(
            durable_independent_review_artifact="unsupported-review.json"
        ),
        lambda value: value["future_r1_boundary"].update(may_exclude_overflow=True),
        lambda value: value["future_r1_boundary"].update(
            may_select_acceptance_threshold_from_d1=True
        ),
        lambda value: value["future_r1_boundary"].update(
            eligible_for_confirmatory_decision=True
        ),
        lambda value: value["future_r1_boundary"].update(
            used_for_threshold_selection=True
        ),
        lambda value: value["future_r1_boundary"].update(
            used_for_checkpoint_selection=True
        ),
        lambda value: value["future_r1_boundary"].update(
            used_for_metric_selection=True
        ),
        lambda value: value["future_r1_boundary"].update(used_for_seed_selection=True),
        lambda value: value["future_r1_boundary"].update(
            used_for_overflow_policy_selection=True
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            internal_registration_not_submission_artifact=False
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            anonymous_submission_inclusion_permitted=True
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            public_release_inclusion_permitted=True
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            raw_v2_artifact_inclusion_permitted=True
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            in_place_sanitization_permitted=True
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            raw_v2_contains_local_path_metadata=False
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            raw_v2_contains_process_metadata=False
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            raw_v2_contains_timestamp_metadata=False
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            raw_v2_contains_runtime_metadata=False
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            publication_safe_derivative_required=False
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            publication_safe_derivative_path="submission/raw-v2.json"
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            submission_include_exclude_roster_frozen=True
        ),
        lambda value: value["publication_anonymity_boundary"].update(
            fresh_publication_anonymity_audit_required=False
        ),
        lambda value: value["preregistration_preservation"].update(
            unresolved_null_count=0
        ),
        lambda value: value["preregistration_preservation"].update(
            unresolved_blocker_count=0
        ),
        lambda value: value["preregistration_preservation"][
            "blocker_stage_counts"
        ].update(CONFIRMATORY_EXECUTION=0),
        lambda value: value["preregistration_preservation"].update(
            required_preexecution_null_fields_are_execution_blocking=False
        ),
        lambda value: value["preregistration_preservation"].update(
            postexecution_audit_plan_nulls_are_execution_blocking=True
        ),
        lambda value: value["preregistration_preservation"].update(
            postexecution_audit_plan_nulls_block_claim_promotion_and_submission=False
        ),
        lambda value: value["preregistration_preservation"].update(
            nulls_closed_by_registration=174
        ),
        lambda value: value["preregistration_preservation"].update(
            blockers_closed_by_registration=12
        ),
        lambda value: value["preregistration_preservation"].update(
            freeze_conditions_closed_by_registration=1
        ),
        lambda value: value["preregistration_preservation"]["freeze_predicate"].update(
            all_confirmatory_execution_blockers_closed=True
        ),
        lambda value: value["cp76_live_delta"].update(
            live_remaining_missing_unique_count=0
        ),
        lambda value: value["cp76_live_delta"].update(
            historical_missing_unique_count=6
        ),
        lambda value: value["cp76_live_delta"].update(
            historically_missing_paths_now_present=[]
        ),
        lambda value: value["cp76_live_delta"].update(live_remaining_missing_paths=[]),
        lambda value: value["cp76_live_delta"].update(
            live_presence_delta_is_non_authoritative=False
        ),
        lambda value: value["cp76_live_delta"].update(
            cp76_historical_snapshot_rewritten=True
        ),
        lambda value: value["cp76_live_delta"].update(
            novelty_independently_assessed_criterion_state="READY"
        ),
        lambda value: value["cp76_live_delta"].update(
            execution_preregistered_criterion_state="READY"
        ),
        lambda value: value["cp76_live_delta"].update(readiness_status="READY"),
        lambda value: value["cp76_live_delta"].update(manuscript_submission_ready=True),
        lambda value: value["cp76_live_delta"].update(readiness_transition="PROMOTED"),
        lambda value: value["checkpoint_custody"].update(checkpoint_sha256="0" * 64),
        lambda value: value["visible_limitations"].update(
            production_bound_means_success_ledger_custody_only=False
        ),
        lambda value: value["baseline_bindings"]["claim_ledger"].update(
            raw_sha256="0" * 64
        ),
        lambda value: value.update(extra_claim=True),
    ),
)
def test_hostile_promotion_scope_and_custody_mutations_are_rejected(mutation) -> None:
    _, registration = _load_registration()
    hostile = deepcopy(registration)
    mutation(hostile)
    _rehash(hostile)
    with pytest.raises(AssertionError):
        _require_contract(hostile)


@pytest.mark.parametrize(
    "payload",
    (
        b'{"value":NaN}',
        b'{"value":Infinity}',
        b'{"value":1,"value":2}',
    ),
)
def test_parser_rejects_nonfinite_and_duplicate_json(payload: bytes) -> None:
    with pytest.raises((AssertionError, ValueError)):
        _parse_json(payload)


def test_human_registration_contains_every_mandatory_boundary() -> None:
    text = HUMAN_PATH.read_text("utf-8")
    for literal in (
        "E-A1-D1",
        "PASS WITH EXPLICIT SCOPE LIMITS",
        "Model-quality decision:** `NOT_MADE`",
        "0.09711382901483998",
        "0.11814236369841445",
        "0.18287473808256435",
        "0.03154866637521339",
        "0.17036802470127654",
        "0.11726381207950134",
        "0.15100529268222873",
        "0.02547407630692731",
        "0.15721987873877863",
        "0.011197231762216917",
        "1.140606604491632",
        "NOT_APPLICABLE_NO_CONTINUOUS_COORDINATES",
        "does not qualify `R1-A1` or",
        "close or prove `C17`",
        "CP76 remains an immutable historical",
        "No externally appointed reviewer panel is required",
        "No transient review is represented as a durable independent-review",
        "production_bound=true",
        "canonical SUCCESS-ledger custody",
        "D1 is now prior observed development knowledge",
        "may not be used to select a",
        "overflow may not be excluded",
        "exactly 174 unresolved null",
        "12 unresolved blockers",
        "none of those",
        "CP76 historically recorded eight missing",
        "The six paths still absent are",
        "substantive `novelty-independently-assessed`",
        "criteria remain `BLOCKED`",
        "internal evidence registration is not a submission artifact",
        "Raw V2 contains",
        "must not be sanitized in place",
        "publication-safe derivative is required",
        "include/exclude roster is not frozen",
        "fresh publication",
        "not eligible for a confirmatory decision",
        "used for metric, threshold, checkpoint, seed-count, or overflow-policy",
    ):
        assert literal in text
    assert "It is not a favorable" in text
    assert "The learned-quality quantities had no acceptance" in text
    assert "no model-quality pass decision" in text
