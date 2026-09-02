"""Hostile synthetic qualification for the minimum-contribution rebaseline."""

from __future__ import annotations

from collections import OrderedDict
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/"
    "manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/"
    "manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.json"
)
HUMAN_REL = Path("PROJECT_GATE_A_MINIMUM_CONTRIBUTION_ROUTE_REBASELINE.md")
TEST_REL = Path(
    "tests/unit/"
    "test_manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.py"
)
AUTHORITY_TEXT = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)


class _StringSubclass(str):
    pass


def _load_validator() -> ModuleType:
    source = ROOT / VALIDATOR_REL
    spec = importlib.util.spec_from_file_location(
        "gate_a_minimum_contribution_rebaseline_validator", source
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


def _closed_roster(module: ModuleType) -> List[str]:
    paths = list(module.PACKAGE_ROSTER)
    paths.extend(spec[2] for spec in module.PREDECESSOR_SPECS)
    assert len(paths) == len(set(paths))
    return paths


def _copy_roster(module: ModuleType, tmp_path: Path) -> Path:
    for relative in _closed_roster(module):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return tmp_path


def _replace(record: Dict[str, Any], dotted: str, value: Any) -> None:
    current: Any = record
    tokens = dotted.split(".")
    for token in tokens[:-1]:
        current = current[int(token)] if type(current) is list else current[token]
    final = tokens[-1]
    if type(current) is list:
        current[int(final)] = value
    else:
        current[final] = value


def _rewrite_machine(
    module: ModuleType,
    root: Path,
    mutation: Callable[[Dict[str, Any]], None],
    *,
    recompute_digest: bool = True,
    canonical: bool = True,
) -> None:
    path = root / MACHINE_REL
    record = json.loads(path.read_text(encoding="ascii"))
    mutation(record)
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    if canonical:
        raw = module.canonical_machine_bytes(record)
    else:
        raw = json.dumps(record, indent=2, sort_keys=True).encode("ascii") + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)


def _states(module: ModuleType, state: str = "PENDING") -> Dict[str, str]:
    return {component_id: state for component_id in module.COMPONENT_IDS}


def _tree_digest(root: Path, paths: Iterable[str]) -> Dict[str, str]:
    return {
        relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
        for relative in paths
    }


def test_canonical_package_validates_exact_additive_effects(
    validator: ModuleType,
) -> None:
    status = validator.validate(ROOT)
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": validator.STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "route_control_predicate": "EMPIRICAL_CONTRIBUTION_ROUTE_FROZEN_PREOUTCOME",
        "current_contribution_state": "EMPIRICAL_CONTRIBUTION_PENDING",
        "empirical_contribution_go_achieved": False,
        "empirical_contribution_terminal_no_go_achieved": False,
        "c17_required_real_domain_headline": False,
        "post_outcome_route_fallback_permitted": False,
        "F106_closed": True,
        "F106_value": "POSITIVE_DIRECT_MINUS_GUIDE_FAVORS_GUIDE",
        "F108_closed": True,
        "F108_value": "TRAIN_ONLY",
        "F105_open": True,
        "B04_open": True,
        "unresolved_fields_closed": 2,
        "effective_unresolved_field_count": 165,
        "effective_open_blocker_count": 12,
        "gate_a_venue_or_primary_claim_item_closed": False,
        "tracker_edit_performed": False,
        "scientific_result": False,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


def test_authority_is_narrow_and_agent_selected(validator: ModuleType) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    authority = record["authority_provenance"]
    assert authority["normalized_visible_text"] == AUTHORITY_TEXT
    assert (
        authority["normalized_visible_text_sha256"]
        == hashlib.sha256(AUTHORITY_TEXT.encode("utf-8")).hexdigest()
    )
    assert authority["local_autonomous_project_work_authorized"] is True
    assert (
        authority["agent_selected_paths_schema_class_predicates_and_direction"] is True
    )
    assert authority["raw_transport_bytes_or_trailing_html_space_bound"] is False
    assert authority["network_or_source_contact_authorized"] is False
    assert authority["data_acquisition_or_access_authorized"] is False
    assert (
        authority["scientific_entropy_runtime_training_or_execution_authorized"]
        is False
    )
    assert authority["claim_promotion_or_submission_authorized"] is False


def test_exact_four_file_roster_and_noncyclic_package_bindings(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    assert record["package_file_roster"] == [
        validator.HUMAN_PATH,
        validator.MACHINE_PATH,
        validator.VALIDATOR_PATH,
        validator.TEST_PATH,
    ]
    bindings = record["package_bindings_excluding_machine_self"]
    assert [row["role"] for row in bindings] == ["human", "validator", "test"]
    assert [row["path"] for row in bindings] == [
        validator.HUMAN_PATH,
        validator.VALIDATOR_PATH,
        validator.TEST_PATH,
    ]
    for row in bindings:
        raw = (ROOT / row["path"]).read_bytes()
        assert row["bytes"] == len(raw)
        assert row["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        assert row["mode_octal"] == "0644"
        assert row["nlink"] == 1
        assert row["terminal_lf"] is True
    assert record["machine_self_binding"] == {
        "path": validator.MACHINE_PATH,
        "semantic_self_digest_field": "record_sha256",
        "raw_self_hash_embedded": False,
    }


def test_all_exact_predecessor_packages_are_bound(validator: ModuleType) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    bindings = record["predecessor_bindings"]
    assert len(bindings) == 18
    assert record["predecessor_group_counts"] == {
        "EXECUTION_PREREGISTRATION": 2,
        "PREEXECUTION_CLOSURE_V2": 4,
        "CKS_COUNT_NORMALIZED_EVENT_THEOREM_V1": 4,
        "C17_PO13_INITIALIZER_KL_PROOF_V1": 4,
        "GATE_A_LOCAL_STATISTICAL_FREEZE_V1": 4,
        "total": 18,
    }
    for ordinal, (binding, spec) in enumerate(
        zip(bindings, validator.PREDECESSOR_SPECS)
    ):
        group, role, path, byte_count, raw_sha, semantic_sha = spec
        assert binding["ordinal"] == ordinal
        assert binding["group"] == group
        assert binding["role"] == role
        assert binding["path"] == path
        assert binding["bytes"] == byte_count
        assert binding["raw_sha256"] == raw_sha
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == raw_sha
        if semantic_sha is None:
            assert "record_sha256" not in binding
        else:
            assert binding["record_sha256"] == semantic_sha


def test_c17_is_retired_only_as_required_real_domain_headline(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    c17 = record["c17_disposition"]
    assert c17["bound_current_route_decision"] == (
        "REAL_DOMAIN_C17_PROMOTION_UNDER_CURRENT_FORK_B_OBSERVABILITY_NO_GO"
    )
    assert c17["c17_required_real_domain_headline"] is False
    assert c17["c17_required_for_empirical_contribution_go"] is False
    assert c17["c17_proved"] is False
    assert c17["c17_real_domain_promotion_permitted"] is False
    assert c17["c17_novel_mechanism_claim_permitted"] is False
    assert c17["permitted_residual_roles"] == [
        "UNPROVED_SPECIFICATION",
        "CONDITIONAL_THEOREM_TARGET",
        "FINITE_OR_MIXED_KNOWN_LAW_FALSIFICATION_ROUTE",
    ]
    assert c17["legacy_c17_field_or_blocker_closed_by_package"] is False
    assert c17["post_outcome_c17_revival_permitted"] is False


def test_contribution_class_is_empirical_and_not_novel_mechanism(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    route = record["contribution_route"]
    assert route["route_control_predicate"] == (
        "EMPIRICAL_CONTRIBUTION_ROUTE_FROZEN_PREOUTCOME"
    )
    assert route["contribution_class"] == validator.CONTRIBUTION_CLASS
    assert route["novel_mechanism_or_method_claim_required"] is False
    assert route["novel_mechanism_or_method_claim_permitted_by_route"] is False
    assert route["predicate_achievement_evidenced_by_package"] is False
    assert route["components_are_conjunctive_and_noncompensatory"] is True
    assert route["cross_domain_pooling_or_rescue_permitted"] is False
    assert route["secondary_metric_rescue_permitted"] is False


def test_exact_fourteen_component_roster_and_current_pending_state(
    validator: ModuleType,
) -> None:
    expected_ids = [
        "R1_VALID_PASS",
        "R2_VALID_PASS",
        "R3_PHYS_DOMAIN_ADMITTED",
        "R4_RETAIL_DOMAIN_ADMITTED",
        "MATCHED_COMPUTE_BASELINE_SUITE_PASS",
        "R3_PHYS_PRIMARY_EFFECT_PASS",
        "R4_RETAIL_PRIMARY_EFFECT_PASS",
        "R3_PHYS_NO_REGRESSION_PASS",
        "R4_RETAIL_NO_REGRESSION_PASS",
        "R3_PHYS_ASSOCIATION_MECHANISM_CONTRAST_PASS",
        "R4_RETAIL_ASSOCIATION_MECHANISM_CONTRAST_PASS",
        "PRECOMMITTED_KNOWN_LAW_AND_TWO_DOMAIN_SCALING_PASS",
        "FULL_FAILURE_ACCOUNTING_AND_CEILING_PASS",
        "CLEAN_ROOM_REPRODUCTION_PASS",
    ]
    assert list(validator.COMPONENT_IDS) == expected_ids
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    route = record["contribution_route"]
    assert route["exact_state_domain"] == ["PENDING", "PASS", "TERMINAL_NO_GO"]
    assert [row["ordinal"] for row in route["components"]] == list(range(14))
    assert [row["component_id"] for row in route["components"]] == expected_ids
    assert all(row["current_state"] == "PENDING" for row in route["components"])
    assert all(row["pass_predicate"] for row in route["components"])
    assert all(row["terminal_no_go_predicate"] for row in route["components"])
    assert route["current_projection"] == {
        "route_state": "EMPIRICAL_CONTRIBUTION_PENDING",
        "empirical_contribution_go": False,
        "empirical_contribution_terminal_no_go": False,
        "empirical_contribution_pending": True,
        "all_14_component_states": "PENDING",
    }


def test_required_component_semantics_cover_every_requested_gate(
    validator: ModuleType,
) -> None:
    rows = {row["component_id"]: row for row in validator.COMPONENT_DEFINITIONS}
    assert "R1" in rows["R1_VALID_PASS"]["pass_predicate"]
    assert "R2" in rows["R2_VALID_PASS"]["pass_predicate"]
    assert "PHYSIONET" in rows["R3_PHYS_DOMAIN_ADMITTED"]["pass_predicate"]
    assert "ONLINE_RETAIL_II" in rows["R4_RETAIL_DOMAIN_ADMITTED"]["pass_predicate"]
    assert (
        "MATCHING_RULES_PASS"
        in rows["MATCHED_COMPUTE_BASELINE_SUITE_PASS"]["pass_predicate"]
    )
    assert (
        "POSITIVE_MINIMUM_EFFECT"
        in rows["R3_PHYS_PRIMARY_EFFECT_PASS"]["pass_predicate"]
    )
    assert (
        "POSITIVE_MINIMUM_EFFECT"
        in rows["R4_RETAIL_PRIMARY_EFFECT_PASS"]["pass_predicate"]
    )
    assert "NO_REGRESSION" in rows["R3_PHYS_NO_REGRESSION_PASS"]["pass_predicate"]
    assert "NO_REGRESSION" in rows["R4_RETAIL_NO_REGRESSION_PASS"]["pass_predicate"]
    assert (
        "ASSOCIATION_DESTROYED_OR_FACTORIZED_EVENTWISE_CONTROL"
        in rows["R3_PHYS_ASSOCIATION_MECHANISM_CONTRAST_PASS"]["pass_predicate"]
    )
    assert (
        "ASSOCIATION_DESTROYED_OR_FACTORIZED_EVENTWISE_CONTROL"
        in rows["R4_RETAIL_ASSOCIATION_MECHANISM_CONTRAST_PASS"]["pass_predicate"]
    )
    assert (
        "SCALING_COORDINATE"
        in rows["PRECOMMITTED_KNOWN_LAW_AND_TWO_DOMAIN_SCALING_PASS"]["pass_predicate"]
    )
    assert (
        "EVERY_SCHEDULED_AND_ABORTED_ATTEMPT_RETAINED"
        in rows["FULL_FAILURE_ACCOUNTING_AND_CEILING_PASS"]["pass_predicate"]
    )
    assert (
        "INDEPENDENT_CLEAN_ROOM"
        in rows["CLEAN_ROOM_REPRODUCTION_PASS"]["pass_predicate"]
    )


def test_pending_projection_is_not_evidence(validator: ModuleType) -> None:
    supplied = _states(validator)
    original = dict(supplied)
    result = validator.evaluate_contribution_route(supplied)
    assert result["route_state"] == "EMPIRICAL_CONTRIBUTION_PENDING"
    assert result["empirical_contribution_go"] is False
    assert result["empirical_contribution_terminal_no_go"] is False
    assert result["empirical_contribution_pending"] is True
    assert result["passed_components"] == []
    assert result["pending_components"] == list(validator.COMPONENT_IDS)
    assert result["terminal_no_go_components"] == []
    assert result["caller_states_verified_as_evidence"] is False
    assert result["scientific_result"] is False
    assert supplied == original


def test_all_pass_projects_go_but_never_verifies_evidence(
    validator: ModuleType,
) -> None:
    supplied = _states(validator, "PASS")
    result = validator.evaluate_contribution_route(supplied)
    assert result["route_state"] == "EMPIRICAL_CONTRIBUTION_GO"
    assert result["empirical_contribution_go"] is True
    assert result["empirical_contribution_terminal_no_go"] is False
    assert result["empirical_contribution_pending"] is False
    assert result["passed_components"] == list(validator.COMPONENT_IDS)
    assert result["pending_components"] == []
    assert result["terminal_no_go_components"] == []
    assert result["c17_required_for_go"] is False
    assert result["post_outcome_route_fallback_permitted"] is False
    assert result["caller_states_verified_as_evidence"] is False
    assert result["scientific_result"] is False


@pytest.mark.parametrize("failed_component", range(14))
def test_every_single_component_terminal_failure_forces_no_go(
    validator: ModuleType, failed_component: int
) -> None:
    supplied = _states(validator, "PASS")
    component_id = validator.COMPONENT_IDS[failed_component]
    supplied[component_id] = "TERMINAL_NO_GO"
    result = validator.evaluate_contribution_route(supplied)
    assert result["route_state"] == "EMPIRICAL_CONTRIBUTION_TERMINAL_NO_GO"
    assert result["empirical_contribution_go"] is False
    assert result["empirical_contribution_terminal_no_go"] is True
    assert result["empirical_contribution_pending"] is False
    assert result["terminal_no_go_components"] == [component_id]
    assert component_id not in result["passed_components"]
    assert result["terminal_no_go_absorbing"] is True


def test_terminal_failure_overrides_pending_and_multiple_failures_keep_order(
    validator: ModuleType,
) -> None:
    supplied = _states(validator)
    supplied[validator.COMPONENT_IDS[11]] = "TERMINAL_NO_GO"
    supplied[validator.COMPONENT_IDS[2]] = "TERMINAL_NO_GO"
    result = validator.evaluate_contribution_route(supplied)
    assert result["route_state"] == "EMPIRICAL_CONTRIBUTION_TERMINAL_NO_GO"
    assert result["terminal_no_go_components"] == [
        validator.COMPONENT_IDS[2],
        validator.COMPONENT_IDS[11],
    ]
    assert len(result["pending_components"]) == 12


@pytest.mark.parametrize(
    "bad,match",
    [
        (None, "exact built-in dict roster"),
        ([], "exact built-in dict roster"),
        ((), "exact built-in dict roster"),
        ({}, "exact built-in dict roster"),
        (OrderedDict(), "exact built-in dict roster"),
    ],
)
def test_state_projection_rejects_nonexact_container_roster(
    validator: ModuleType, bad: Any, match: str
) -> None:
    with pytest.raises(validator.ValidationError, match=match):
        validator.evaluate_contribution_route(bad)


def test_state_projection_rejects_missing_extra_subclass_and_invalid_values(
    validator: ModuleType,
) -> None:
    missing = _states(validator)
    missing.pop(validator.COMPONENT_IDS[-1])
    with pytest.raises(validator.ValidationError, match="exact built-in dict roster"):
        validator.evaluate_contribution_route(missing)
    extra = _states(validator)
    extra["C17_PASS"] = "PASS"
    with pytest.raises(validator.ValidationError, match="exact built-in dict roster"):
        validator.evaluate_contribution_route(extra)
    subclass = OrderedDict(_states(validator))
    with pytest.raises(validator.ValidationError, match="exact built-in dict roster"):
        validator.evaluate_contribution_route(subclass)
    for bad in (True, False, 1, 0, None, "pass", "FAIL", "GO", ""):
        invalid = _states(validator)
        invalid[validator.COMPONENT_IDS[0]] = bad  # type: ignore[assignment]
        with pytest.raises(validator.ValidationError, match="invalid state"):
            validator.evaluate_contribution_route(invalid)


def test_state_projection_rejects_all_fourteen_string_subclass_keys(
    validator: ModuleType,
) -> None:
    hostile = {
        _StringSubclass(component_id): "PENDING"
        for component_id in validator.COMPONENT_IDS
    }
    assert len(hostile) == 14
    assert all(type(key) is _StringSubclass for key in hostile)
    with pytest.raises(validator.ValidationError, match="exact built-in str"):
        validator.evaluate_contribution_route(hostile)


@pytest.mark.parametrize("subclass_key_index", range(14))
def test_state_projection_rejects_each_mixed_string_subclass_key(
    validator: ModuleType, subclass_key_index: int
) -> None:
    hostile = {
        (
            _StringSubclass(component_id)
            if index == subclass_key_index
            else component_id
        ): "PENDING"
        for index, component_id in enumerate(validator.COMPONENT_IDS)
    }
    assert len(hostile) == 14
    assert sum(type(key) is _StringSubclass for key in hostile) == 1
    assert sum(type(key) is str for key in hostile) == 13
    with pytest.raises(validator.ValidationError, match="exact built-in str"):
        validator.evaluate_contribution_route(hostile)
    with pytest.raises(validator.ValidationError, match="exact built-in str"):
        validator.advance_route_states(_states(validator), hostile)


def test_advance_allows_only_fail_closed_nonreopening_transitions(
    validator: ModuleType,
) -> None:
    pending = _states(validator)
    one_pass = dict(pending)
    one_pass[validator.COMPONENT_IDS[0]] = "PASS"
    assert validator.advance_route_states(pending, one_pass)["route_state"] == (
        "EMPIRICAL_CONTRIBUTION_PENDING"
    )
    invalidated = dict(one_pass)
    invalidated[validator.COMPONENT_IDS[0]] = "TERMINAL_NO_GO"
    assert validator.advance_route_states(one_pass, invalidated)["route_state"] == (
        "EMPIRICAL_CONTRIBUTION_TERMINAL_NO_GO"
    )
    with pytest.raises(validator.ValidationError, match="PASS cannot return"):
        validator.advance_route_states(one_pass, pending)
    with pytest.raises(validator.ValidationError, match="cannot be changed"):
        validator.advance_route_states(invalidated, one_pass)
    assert (
        validator.advance_route_states(invalidated, dict(invalidated))["route_state"]
        == "EMPIRICAL_CONTRIBUTION_TERMINAL_NO_GO"
    )


def test_no_post_outcome_fallback_or_cross_domain_rescue(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    route = record["contribution_route"]
    assert route["terminal_no_go_absorbing"] is True
    assert route["post_outcome_route_fallback_permitted"] is False
    assert (
        route[
            "replacement_metric_sign_threshold_seed_baseline_control_domain_claim_or_"
            "c17_route_permitted"
        ]
        is False
    )
    assert route["different_future_project_is_current_route_fallback"] is False
    one_domain_failure = _states(validator, "PASS")
    one_domain_failure["R4_RETAIL_PRIMARY_EFFECT_PASS"] = "TERMINAL_NO_GO"
    assert (
        validator.evaluate_contribution_route(one_domain_failure)["route_state"]
        == "EMPIRICAL_CONTRIBUTION_TERMINAL_NO_GO"
    )


def test_F106_direction_is_exact_and_F105_B04_remain_open(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    freeze = record["metric_direction_freeze"]
    assert freeze["field_id"] == "F106"
    assert freeze["json_pointer"] == ("/metric_and_estimand_plan/favorable_direction")
    assert freeze["status"] == "CLOSED_BY_ADDITIVE_PREOUTCOME_FREEZE"
    assert freeze["value"] == "POSITIVE_DIRECT_MINUS_GUIDE_FAVORS_GUIDE"
    assert (
        freeze["every_admissible_primary_metric_represented_as_lower_is_better_loss"]
        is True
    )
    assert (
        freeze[
            "higher_is_better_source_metric_requires_preoutcome_fixed_order_reversing_"
            "transform"
        ]
        is True
    )
    assert freeze["outcome_dependent_sign_or_transform_permitted"] is False
    assert freeze["primary_score_token_semantics"] == (
        "PRIMARY_LOSS_DIRECT_MINUS_PRIMARY_LOSS_GUIDE"
    )
    assert freeze["strictly_positive_difference_favors_guide"] is True
    assert freeze["zero_difference_favors_guide"] is False
    assert freeze["F105_primary_metric_id_value"] is None
    assert freeze["F105_primary_metric_id_open"] is True
    assert freeze["B04_open"] is True


def test_F108_is_exact_duplicate_train_only_scope_without_overclaim(
    validator: ModuleType,
) -> None:
    prereg = json.loads(
        (
            ROOT / "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
        ).read_text(encoding="ascii")
    )
    assert prereg["split_and_leakage_plan"]["primary_metric_fitting_scope"] == (
        "TRAIN_ONLY"
    )
    assert (
        prereg["metric_and_estimand_plan"]["training_only_metric_fitting_rule"] is None
    )
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    freeze = record["metric_fitting_scope_freeze"]
    assert freeze == {
        "field_id": "F108",
        "json_pointer": "/metric_and_estimand_plan/training_only_metric_fitting_rule",
        "status": "CLOSED_BY_EXACT_DUPLICATE_SCOPE_PROJECTION",
        "value": "TRAIN_ONLY",
        "source_json_pointer": "/split_and_leakage_plan/primary_metric_fitting_scope",
        "source_value": "TRAIN_ONLY",
        "source_and_projection_semantically_identical_scope": True,
        "primary_metric_parameter_or_data_dependent_transform_fit_on_validation_"
        "permitted": False,
        "primary_metric_parameter_or_data_dependent_transform_fit_on_test_"
        "permitted": False,
        "primary_metric_selected": False,
        "fitting_algorithm_selected": False,
        "kernel_bandwidth_or_numeric_value_selected": False,
        "transform_or_approximation_selected": False,
        "validation_checkpoint_or_model_selection_rule_selected": False,
        "B04_open": True,
    }


def test_field_and_blocker_delta_is_exactly_two_fields(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    assert record["field_closures"] == [
        {
            "field_id": "F106",
            "json_pointer": "/metric_and_estimand_plan/favorable_direction",
            "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_FREEZE",
            "value": "POSITIVE_DIRECT_MINUS_GUIDE_FAVORS_GUIDE",
            "evidence": (
                "ALL_ADMISSIBLE_PRIMARY_METRICS_USE_LOWER_IS_BETTER_LOSS_"
                "REPRESENTATION_BEFORE_PROTECTED_OUTCOMES"
            ),
        },
        {
            "field_id": "F108",
            "json_pointer": (
                "/metric_and_estimand_plan/training_only_metric_fitting_rule"
            ),
            "status": "CLOSED_BY_EXACT_DUPLICATE_SCOPE_PROJECTION",
            "value": "TRAIN_ONLY",
            "source_json_pointer": (
                "/split_and_leakage_plan/primary_metric_fitting_scope"
            ),
            "source_value": "TRAIN_ONLY",
        },
    ]
    assert record["count_transition"] == {
        "before": {
            "pre_execution_open": 161,
            "pre_execution_closed": 5,
            "post_execution_open": 6,
            "post_execution_closed": 0,
            "total_open": 167,
            "total_closed": 5,
        },
        "closed_by_package": {
            "field_ids": ["F106", "F108"],
            "pre_execution": 2,
            "post_execution": 0,
            "total": 2,
        },
        "after": {
            "pre_execution_open": 159,
            "pre_execution_closed": 7,
            "post_execution_open": 6,
            "post_execution_closed": 0,
            "total_open": 165,
            "total_closed": 7,
        },
        "blockers_open_after": 12,
        "blockers_closed": 0,
        "formal_tests_closed": 0,
        "results_filled": 0,
    }
    effects = record["project_control_effects"]
    assert effects["unresolved_fields_closed"] == 2
    assert effects["only_fields_closed"] == ["F106", "F108"]
    assert effects["B04_closed"] is False
    assert effects["F105_closed"] is False
    assert effects["all_other_fields_closed"] is False
    assert effects["blockers_closed"] == 0
    assert effects["formal_tests_closed"] == 0
    assert effects["result_slots_filled"] == 0
    assert effects["gate_a_venue_or_primary_claim_item_closed"] is False
    assert effects["tracker_edit_performed"] is False


def test_package_is_project_control_not_predicate_achievement(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    effects = record["project_control_effects"]
    assert effects["minimum_contribution_route_rebaselined_preoutcome"] is True
    assert effects["c17_retired_as_required_real_domain_headline"] is True
    assert effects["empirical_contribution_go_achieved"] is False
    assert effects["empirical_contribution_terminal_no_go_achieved"] is False
    assert effects["empirical_contribution_pending"] is True
    nonclaims = record["scope_and_nonclaims"]
    assert all(
        nonclaims[key] is False
        for key in (
            "r1_or_r2_validated",
            "domain_admitted",
            "matched_compute_baseline_suite_validated",
            "two_domain_effect_or_no_regression_result_observed",
            "association_mechanism_contrast_observed",
            "scaling_result_observed",
            "failure_rate_observed",
            "clean_room_reproduction_completed",
            "primary_metric_selected",
            "scientific_execution_performed",
            "data_or_test_outcome_accessed",
            "network_or_external_contact_performed",
            "scientific_entropy_consumed",
            "runtime_or_training_performed",
            "claim_promoted",
            "submission_or_venue_quality_established",
        )
    )


def test_pure_state_helpers_perform_no_package_io(
    validator: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden_read(*args: Any, **kwargs: Any) -> bytes:
        del args, kwargs
        raise AssertionError("pure state helper attempted package I/O")

    monkeypatch.setattr(validator, "_stable_read", forbidden_read)
    monkeypatch.chdir(tmp_path)
    pending = _states(validator)
    proposed = dict(pending)
    proposed[validator.COMPONENT_IDS[0]] = "PASS"
    assert validator.evaluate_contribution_route(pending)["route_state"] == (
        "EMPIRICAL_CONTRIBUTION_PENDING"
    )
    assert validator.advance_route_states(pending, proposed)["route_state"] == (
        "EMPIRICAL_CONTRIBUTION_PENDING"
    )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "dotted,replacement",
    [
        ("state", "EXECUTABLE"),
        ("global_state", "FROZEN_EXECUTABLE"),
        ("package_kind", "SCIENTIFIC_RESULT"),
        ("c17_disposition.c17_required_real_domain_headline", True),
        ("c17_disposition.c17_required_for_empirical_contribution_go", True),
        ("c17_disposition.c17_proved", True),
        ("c17_disposition.post_outcome_c17_revival_permitted", True),
        ("contribution_route.go_predicate", "ANY_COMPONENT_PASSES"),
        ("contribution_route.components.0.current_state", "PASS"),
        ("contribution_route.components.5.pass_predicate", "POSITIVE_POINT_ESTIMATE"),
        ("contribution_route.components.13.terminal_no_go_predicate", "OPTIONAL"),
        ("contribution_route.components_are_conjunctive_and_noncompensatory", False),
        ("contribution_route.cross_domain_pooling_or_rescue_permitted", True),
        ("contribution_route.post_outcome_route_fallback_permitted", True),
        ("contribution_route.predicate_achievement_evidenced_by_package", True),
        ("metric_direction_freeze.value", "NEGATIVE_FAVORS_GUIDE"),
        (
            "metric_direction_freeze.every_admissible_primary_metric_represented_"
            "as_lower_is_better_loss",
            False,
        ),
        ("metric_direction_freeze.outcome_dependent_sign_or_transform_permitted", True),
        ("metric_direction_freeze.F105_primary_metric_id_open", False),
        ("metric_fitting_scope_freeze.value", "TRAIN_AND_VALIDATION"),
        ("metric_fitting_scope_freeze.source_value", "TEST_ONLY"),
        ("metric_fitting_scope_freeze.fitting_algorithm_selected", True),
        ("field_closures.0.field_id", "F105"),
        ("field_closures.1.value", "TRAIN_AND_VALIDATION"),
        ("count_transition.closed_by_package.field_ids.1", "F109"),
        ("count_transition.closed_by_package.total", 3),
        ("count_transition.after.total_open", 164),
        ("count_transition.blockers_closed", 1),
        ("project_control_effects.gate_a_venue_or_primary_claim_item_closed", True),
        ("project_control_effects.tracker_edit_performed", True),
        ("scope_and_nonclaims.scientific_execution_performed", True),
        ("scope_and_nonclaims.data_or_test_outcome_accessed", True),
    ],
)
def test_machine_semantic_mutations_fail_even_with_recomputed_self_digest(
    validator: ModuleType, tmp_path: Path, dotted: str, replacement: Any
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: _replace(record, dotted, replacement),
    )
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_stale_self_digest_duplicate_keys_and_noncanonical_json_fail(
    validator: ModuleType, tmp_path: Path
) -> None:
    stale_root = _copy_roster(validator, tmp_path / "stale")
    _rewrite_machine(
        validator,
        stale_root,
        lambda record: record.__setitem__("state", "MUTATED"),
        recompute_digest=False,
    )
    with pytest.raises(validator.ValidationError, match="self digest"):
        validator.validate(stale_root)

    duplicate_root = _copy_roster(validator, tmp_path / "duplicate")
    duplicate_path = duplicate_root / MACHINE_REL
    raw = duplicate_path.read_bytes()
    duplicate_path.write_bytes(b'{"schema_version":"DUPLICATE",' + raw[1:])
    duplicate_path.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="duplicate JSON key"):
        validator.validate(duplicate_root)

    noncanonical_root = _copy_roster(validator, tmp_path / "noncanonical")
    _rewrite_machine(
        validator,
        noncanonical_root,
        lambda record: None,
        canonical=False,
    )
    with pytest.raises(validator.ValidationError, match="not canonical JSON"):
        validator.validate(noncanonical_root)


@pytest.mark.parametrize(
    "package_path", [str(HUMAN_REL), str(VALIDATOR_REL), str(TEST_REL)]
)
def test_each_nonmachine_package_byte_is_bound(
    validator: ModuleType, tmp_path: Path, package_path: str
) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / package_path
    path.write_bytes(path.read_bytes() + b"\n")
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


@pytest.mark.parametrize("predecessor_index", range(18))
def test_each_predecessor_byte_roster_entry_is_live_bound(
    validator: ModuleType, tmp_path: Path, predecessor_index: int
) -> None:
    root = _copy_roster(validator, tmp_path)
    relative = validator.PREDECESSOR_SPECS[predecessor_index][2]
    path = root / relative
    raw = path.read_bytes()
    assert raw
    path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="predecessor exact-byte"):
        validator.validate(root)


def test_mode_symlink_and_hardlink_custody_fail_closed(
    validator: ModuleType, tmp_path: Path
) -> None:
    mode_root = _copy_roster(validator, tmp_path / "mode")
    (mode_root / HUMAN_REL).chmod(0o600)
    with pytest.raises(validator.ValidationError, match="leaf custody invalid"):
        validator.validate(mode_root)

    symlink_root = _copy_roster(validator, tmp_path / "symlink")
    human = symlink_root / HUMAN_REL
    replacement = symlink_root / "replacement-human.md"
    shutil.copyfile(human, replacement)
    replacement.chmod(0o644)
    human.unlink()
    human.symlink_to(replacement.name)
    with pytest.raises(validator.ValidationError, match="symlink"):
        validator.validate(symlink_root)

    hardlink_root = _copy_roster(validator, tmp_path / "hardlink")
    hardlink_human = hardlink_root / HUMAN_REL
    os.link(hardlink_human, hardlink_root / "second-human-link.md")
    with pytest.raises(validator.ValidationError, match="leaf custody invalid"):
        validator.validate(hardlink_root)


def test_validation_is_cwd_independent_and_byte_read_only(
    validator: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roster = _closed_roster(validator)
    before = _tree_digest(ROOT, roster)
    monkeypatch.chdir(tmp_path)
    assert validator.validate(ROOT)["validation"] == "PASS"
    after = _tree_digest(ROOT, roster)
    assert before == after
    assert list(tmp_path.iterdir()) == []


def test_machine_json_is_ascii_canonical_and_self_digest_is_deterministic(
    validator: ModuleType,
) -> None:
    raw = (ROOT / MACHINE_REL).read_bytes()
    raw.decode("ascii")
    record = json.loads(raw)
    assert raw == validator.canonical_machine_bytes(record)
    assert record["record_sha256"] == validator.record_sha256(record)
    assert validator.record_sha256(record) == validator.record_sha256(dict(record))


def test_validator_ast_has_no_network_science_entropy_subprocess_or_write_route(
    validator: ModuleType,
) -> None:
    source = (ROOT / VALIDATOR_REL).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert not imported_roots.intersection(
        {
            "socket",
            "urllib",
            "http",
            "requests",
            "subprocess",
            "multiprocessing",
            "random",
            "secrets",
            "numpy",
            "torch",
            "heterodiff",
        }
    )
    forbidden_attributes = {
        "write_text",
        "write_bytes",
        "mkdir",
        "touch",
        "unlink",
        "rename",
        "replace",
        "rmdir",
        "system",
        "popen",
        "fork",
        "spawn",
        "urandom",
        "getrandom",
        "urlopen",
        "connect",
        "request",
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not called_attributes.intersection(forbidden_attributes)
    write_flag_names = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "os"
        and node.attr.startswith("O_")
    }
    assert write_flag_names == {"O_RDONLY"}
    string_literals = {
        node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)
    }
    assert {"O_CLOEXEC", "O_NOFOLLOW"}.issubset(string_literals)


def test_qualification_boundary_and_publication_boundary_are_fail_closed(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    qualification = record["qualification_boundary"]
    assert qualification == {
        "validator_read_only": True,
        "validator_imports_project_science": False,
        "synthetic_state_projection_only": True,
        "validator_or_pure_state_surface_writer_present": False,
        "validator_or_pure_state_surface_network_connector_subprocess_or_scientific_"
        "worker_route_present": False,
        "validator_or_pure_state_surface_scientific_seed_or_protocol_entropy_route_"
        "present": False,
        "qualification_launches_python_and_pytest_interpreters": True,
        "hostile_tests_write_disposable_pytest_temporary_copies": True,
        "hostile_tests_mutate_only_disposable_copy_bytes_modes_and_links": True,
        "canonical_package_or_predecessor_bytes_modified_by_qualification": False,
        "global_process_absence_claimed": False,
        "global_filesystem_write_absence_claimed": False,
        "ordinary_temporary_name_randomness_absence_claimed": False,
        "cache_disabled_qualification_required": True,
        "caller_supplied_pass_labels_are_scientific_evidence": False,
    }
    assert record["publication_boundary"] == {
        "internal_project_control_only": True,
        "anonymous_or_public_inclusion_permitted": False,
        "publication_safe_derivative_required": True,
        "fresh_anonymity_methods_statistics_and_claim_boundary_audit_required": True,
    }
