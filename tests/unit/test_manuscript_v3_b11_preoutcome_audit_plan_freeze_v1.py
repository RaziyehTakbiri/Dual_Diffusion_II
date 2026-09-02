"""Hostile qualification for the B11 pre-outcome audit-plan freeze."""

from __future__ import annotations

import ast
import copy
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
    "manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/"
    "manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.json"
)
HUMAN_REL = Path("PROJECT_B11_PREOUTCOME_AUDIT_PLAN_FREEZE.md")
TEST_REL = Path(
    "tests/unit/"
    "test_manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.py"
)


class _IntegerSubclass(int):
    pass


class _DictSubclass(dict):
    pass


class _StatProxy:
    def __init__(self, base: Any, **overrides: Any) -> None:
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name: str) -> Any:
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._base, name)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "manuscript_v3_b11_audit_plan_validator", ROOT / VALIDATOR_REL
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


def _copy_roster(module: ModuleType, target: Path) -> Path:
    for relative in _closed_roster(module):
        source = ROOT / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o644)
    return target


def _read_machine(root: Path) -> Dict[str, Any]:
    return json.loads((root / MACHINE_REL).read_text(encoding="ascii"))


def _rewrite_machine(
    module: ModuleType,
    root: Path,
    mutation: Callable[[Dict[str, Any]], None],
    *,
    recompute_digest: bool = True,
    canonical: bool = True,
) -> None:
    record = _read_machine(root)
    mutation(record)
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    raw = (
        module.canonical_machine_bytes(record)
        if canonical
        else json.dumps(record, ensure_ascii=True, sort_keys=True, indent=2).encode(
            "ascii"
        )
        + b"\n"
    )
    path = root / MACHINE_REL
    path.write_bytes(raw)
    path.chmod(0o644)


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


def _tree_digest(root: Path, paths: Iterable[str]) -> Dict[str, str]:
    return {
        relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
        for relative in paths
    }


def _passing_evidence(module: ModuleType) -> Dict[str, Any]:
    return {
        "all_required_inputs_hash_bound": True,
        "input_roster_exact_and_complete": True,
        "role_separation_satisfied": True,
        "subject_matter_competence_declared": True,
        "conflict_of_interest_disclosed": True,
        "owner_c_coi_reviewed_and_accepted": True,
        "all_ordered_steps_completed": True,
        "all_required_outputs_hash_bound": True,
        "all_findings_preserved": True,
        "actual_report_present": True,
        "known_authorship_or_implementation_overlap": False,
        "known_input_or_subject_mutation": False,
        "forbidden_rerun_or_redesign": False,
        "p0_finding_count": 0,
        "p1_finding_count": 0,
        "bounded_disclosed_p2_count": 0,
        "unbounded_or_undisclosed_p2_count": 0,
    }


def test_canonical_package_validates_exact_three_field_scope(
    validator: ModuleType,
) -> None:
    status = validator.validate(ROOT)
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": "B11_PREOUTCOME_AUDIT_PLANS_FROZEN_REPORTS_NOT_CREATED",
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "control_predicate": (
            "PREOUTCOME_PROOF_CODE_METHODS_STATISTICS_CLEAN_ROOM_AUDIT_PLANS_FROZEN"
        ),
        "fields_closed": ["F168", "F170", "F171"],
        "unresolved_fields_closed": 3,
        "effective_pre_execution_open": 145,
        "effective_pre_execution_closed": 21,
        "effective_post_execution_open": 3,
        "effective_post_execution_closed": 3,
        "effective_open_blocker_count": 12,
        "F169_open_and_null": True,
        "B11_open": True,
        "formal_tests_closed": 0,
        "results_filled": 0,
        "audit_execution": False,
        "runtime_or_scientific_execution": False,
        "tracker_edit_performed": False,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


def test_machine_is_canonical_duplicate_free_and_exact_expected_record(
    validator: ModuleType,
) -> None:
    raw = (ROOT / MACHINE_REL).read_bytes()
    record = json.loads(raw.decode("ascii"))
    assert raw == validator.canonical_machine_bytes(record)
    assert record["record_sha256"] == validator.record_sha256(record)
    assert record == validator.expected_record(ROOT)


def test_exact_four_file_roster_and_noncyclic_self_binding(
    validator: ModuleType,
) -> None:
    record = _read_machine(ROOT)
    assert record["package_file_roster"] == [
        str(HUMAN_REL),
        str(MACHINE_REL),
        str(VALIDATOR_REL),
        str(TEST_REL),
    ]
    bindings = record["package_bindings_excluding_machine_self"]
    assert [row["role"] for row in bindings] == ["human", "validator", "test"]
    assert [row["path"] for row in bindings] == [
        str(HUMAN_REL),
        str(VALIDATOR_REL),
        str(TEST_REL),
    ]
    for row in bindings:
        raw = (ROOT / row["path"]).read_bytes()
        assert row["bytes"] == len(raw)
        assert row["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        assert row["mode_octal"] == "0644"
        assert row["nlink"] == 1
        assert row["terminal_lf"] is True
    assert record["machine_self_binding"] == {
        "path": str(MACHINE_REL),
        "semantic_self_digest_field": "record_sha256",
        "raw_self_hash_embedded": False,
    }


def test_all_applicable_predecessors_are_exactly_bound(
    validator: ModuleType,
) -> None:
    record = _read_machine(ROOT)
    bindings = record["predecessor_bindings"]
    assert len(bindings) == len(validator.PREDECESSOR_SPECS) == 8
    assert record["predecessor_group_counts"] == {
        "EXECUTION_PREREGISTRATION_V1": 2,
        "ACCEPTED_F104_BASELINE": 5,
        "ANTI_DRIFT_POLICY": 1,
    }
    for row, spec in zip(bindings, validator.PREDECESSOR_SPECS):
        group, role, path, byte_count, raw_sha, semantic_sha = spec
        assert row["group"] == group
        assert row["role"] == role
        assert row["path"] == path
        assert row["bytes"] == byte_count
        assert row["raw_sha256"] == raw_sha
        assert row["mode_octal"] == "0644"
        assert row["nlink"] == 1
        if semantic_sha is not None:
            assert row["record_sha256"] == semantic_sha
            predecessor = json.loads((ROOT / path).read_text(encoding="ascii"))
            assert validator._semantic_record_sha256(predecessor) == semantic_sha


def test_accepted_post_f104_baseline_is_exact(validator: ModuleType) -> None:
    baseline = _read_machine(ROOT)["accepted_post_f104_baseline"]
    assert baseline == {
        "accepted_f104_independent_review_exactly_bound": True,
        "pre_execution_open_before": 145,
        "pre_execution_closed_before": 21,
        "post_execution_open_before": 6,
        "post_execution_closed_before": 0,
        "total_open_before": 151,
        "total_closed_before": 21,
        "blockers_open_before": 12,
        "formal_tests_closed_before": 0,
        "results_filled_before": 0,
        "f168_f169_f170_f171_open_and_null_in_original_preregistration": True,
    }


def test_exact_field_plan_roster_pointers_and_order(validator: ModuleType) -> None:
    record = _read_machine(ROOT)
    closures = record["field_closures"]
    assert [row["field_id"] for row in closures] == ["F168", "F170", "F171"]
    assert [row["json_pointer"] for row in closures] == [
        "/ethics_release_and_review_plan/proof_and_code_audit_plan",
        "/ethics_release_and_review_plan/methods_and_statistics_audit_plan",
        "/ethics_release_and_review_plan/clean_room_reproduction_audit_plan",
    ]
    assert [row["value"]["plan_id"] for row in closures] == list(
        validator.PLAN_IDS
    )
    assert [row["value"]["field_id"] for row in closures] == [
        "F168",
        "F170",
        "F171",
    ]
    assert all(
        row["status"] == "CLOSED_BY_ADDITIVE_PREOUTCOME_AUDIT_PLAN_FREEZE"
        for row in closures
    )


@pytest.mark.parametrize(
    "index,input_count,step_count,output_count",
    [(0, 7, 7, 7), (1, 8, 9, 9), (2, 8, 8, 9)],
)
def test_plan_cardinality_order_and_current_nulls(
    validator: ModuleType,
    index: int,
    input_count: int,
    step_count: int,
    output_count: int,
) -> None:
    plan = _read_machine(ROOT)["field_closures"][index]["value"]
    assert len(plan["required_future_input_classes"]) == input_count
    assert len(plan["required_future_input_classes"]) == len(
        set(plan["required_future_input_classes"])
    )
    assert len(plan["ordered_procedure"]) == step_count
    assert [row["ordinal"] for row in plan["ordered_procedure"]] == list(
        range(step_count)
    )
    assert len({row["step_id"] for row in plan["ordered_procedure"]}) == step_count
    assert len(plan["required_future_output_classes"]) == output_count
    assert len(plan["required_future_output_classes"]) == len(
        set(plan["required_future_output_classes"])
    )
    assert plan["actual_auditor_identity"] is None
    assert plan["actual_appointment_receipt"] is None
    assert plan["required_future_assignment_admission_fields"] == list(
        validator.ASSIGNMENT_ADMISSION_FIELDS
    )
    assert plan["actual_subject_matter_competence_declaration"] is None
    assert plan["actual_conflict_of_interest_disclosure"] is None
    assert plan["actual_owner_c_coi_review_and_acceptance"] is None
    assert plan["actual_input_manifest"] is None
    assert plan["actual_output_report"] is None
    assert plan["actual_output_artifact_path"] is None
    assert plan["audit_executed"] is False


def test_owner_roles_independence_and_separation_are_exact(
    validator: ModuleType,
) -> None:
    record = _read_machine(ROOT)
    process = record["shared_owner_role_and_process"]
    assert process["responsible_owner_role"] == validator.OWNER_ROLE
    assert process["proof_code_and_methods_auditor_role"] == validator.AUDITOR_ROLE
    assert process["clean_room_executor_role"] == validator.CLEAN_ROOM_ROLE
    assert process["separation_rules"] == list(validator.SEPARATION_RULES)
    assert process["required_future_assignment_admission_fields"] == list(
        validator.ASSIGNMENT_ADMISSION_FIELDS
    )
    assert len(process["separation_rules"]) == len(set(process["separation_rules"]))
    for key in (
        "actual_person_institution_account_or_external_identity",
        "actual_assignment_or_appointment_receipt",
        "actual_subject_matter_competence_declaration",
        "actual_conflict_of_interest_disclosure",
        "actual_owner_c_coi_review_and_acceptance",
        "actual_audit_input_instance",
        "actual_report_or_artifact",
        "actual_clean_room_run",
    ):
        assert process[key] is None
    assert record["severity_and_disposition_model"] == dict(
        validator.SEVERITY_MODEL
    )


def test_count_transition_and_complete_field_sweep_are_exact(
    validator: ModuleType,
) -> None:
    record = _read_machine(ROOT)
    transition = record["count_transition"]
    assert transition["before"] == {
        "pre_execution_open": 145,
        "pre_execution_closed": 21,
        "post_execution_open": 6,
        "post_execution_closed": 0,
        "total_open": 151,
        "total_closed": 21,
    }
    assert transition["closed_by_package"] == {
        "field_ids": ["F168", "F170", "F171"],
        "pre_execution": 0,
        "post_execution": 3,
        "total": 3,
    }
    assert transition["after"] == {
        "pre_execution_open": 145,
        "pre_execution_closed": 21,
        "post_execution_open": 3,
        "post_execution_closed": 3,
        "total_open": 148,
        "total_closed": 24,
    }
    assert transition["blockers_open_after"] == 12
    assert transition["blockers_closed"] == 0
    assert transition["formal_tests_closed"] == 0
    assert transition["results_filled"] == 0

    sweep = record["comprehensive_field_sweep"]
    assert sweep["closed_pre_ids"] == list(validator.CLOSED_PRE_AFTER_F104)
    assert sweep["open_pre_ids"] == list(validator.OPEN_PRE_AFTER_F104)
    assert sweep["closed_post_ids"] == ["F168", "F170", "F171"]
    assert sweep["open_post_ids"] == ["F164", "F165", "F169"]
    assert sweep["eligible_now_ids"] == ["F168", "F170", "F171"]
    assert sweep["additional_eligible_field_count"] == 0
    assert sweep["F169_value"] is None
    assert len(sweep["closed_pre_ids"]) == 21
    assert len(sweep["open_pre_ids"]) == 145
    assert set(sweep["closed_pre_ids"]).isdisjoint(sweep["open_pre_ids"])


def test_f169_b11_reports_runtime_science_and_results_remain_unclosed(
    validator: ModuleType,
) -> None:
    record = _read_machine(ROOT)
    boundary = record["current_execution_boundary"]
    assert boundary["all_three_plans_have_audit_executed_false"] is True
    assert all(
        boundary[key] is False
        for key in boundary
        if key != "all_three_plans_have_audit_executed_false"
    )
    effects = record["project_effects_and_nonclaims"]
    for key in (
        "F164_F165_F169_remain_open",
        "F169_remains_open_and_null",
        "B11_remains_open",
        "all_12_blockers_remain_open",
        "R1_R2_R3_R4_remain_unexecuted",
    ):
        assert effects[key] is True
    for key in (
        "network_contact_repository_license_or_data_access_performed",
        "entropy_generated_or_consumed",
        "subprocess_or_environment_build_performed",
        "runtime_or_operational_receipt_created",
        "audit_or_clean_room_execution_performed",
        "auditor_or_clean_room_executor_selected_or_admitted",
        "competence_declaration_or_coi_disclosure_acceptance_receipt_created",
        "training_scientific_or_production_execution_performed",
        "result_or_claim_promoted",
        "submission_or_release_performed",
        "tracker_or_evidence_ledger_edited",
    ):
        assert effects[key] is False
    assert effects["formal_test_28_status"] == "OPEN"
    assert effects["formal_test_29_status"] == "OPEN"
    assert effects["formal_test_30_status"] == "PENDING"


def test_anti_drift_scope_is_one_integrated_count_reducing_package(
    validator: ModuleType,
) -> None:
    scope = _read_machine(ROOT)["anti_drift_scope_review"]
    assert scope == {
        "one_integrated_b11_package": True,
        "shared_governance_and_completion_contract": True,
        "named_field_ids": ["F168", "F170", "F171"],
        "tracked_field_count_reduction": 3,
        "zero_delta_precursor_layer_created": False,
        "F169_or_B11_promoted": False,
        "additional_b11_artifact_requires_new_scope_review": True,
    }


def test_evidence_ready_text_is_not_registration(validator: ModuleType) -> None:
    registration = _read_machine(ROOT)["evidence_ready_registration"]
    assert registration == {
        "proposed_text": validator.EVIDENCE_READY_REGISTRATION,
        "permitted_field_delta": ["F168", "F170", "F171"],
        "registration_performed_by_this_package": False,
    }


def test_completion_rule_partitions_known_failure_from_unverified_readiness(
    validator: ModuleType,
) -> None:
    rule = _read_machine(ROOT)["shared_completion_rule"]
    assert rule["known_substantive_defect_precedes_missing_readiness"] is True
    assert rule["known_fail_conditions"] == [
        "KNOWN_AUTHORSHIP_OR_IMPLEMENTATION_OVERLAP",
        "KNOWN_INPUT_OR_SUBJECT_MUTATION",
        "FORBIDDEN_RERUN_OR_REDESIGN",
        "ANY_P0_FINDING",
        "ANY_P1_FINDING",
        "ANY_UNBOUNDED_OR_UNDISCLOSED_P2_FINDING",
    ]
    assert rule["incomplete_only_when_no_known_defect_conditions"] == [
        "MISSING_OR_UNVERIFIED_ROLE_SEPARATION",
        "MISSING_OR_UNVERIFIED_INPUT_OR_SUBJECT_CUSTODY",
        "MISSING_OR_UNVERIFIED_SUBJECT_MATTER_COMPETENCE",
        "MISSING_OR_UNVERIFIED_CONFLICT_OF_INTEREST_DISCLOSURE_OR_OWNER_C_ACCEPTANCE",
        "MISSING_OR_UNVERIFIED_OTHER_READINESS_EVIDENCE",
    ]


@pytest.mark.parametrize(
    "key",
    [
        "all_required_inputs_hash_bound",
        "input_roster_exact_and_complete",
        "role_separation_satisfied",
        "subject_matter_competence_declared",
        "conflict_of_interest_disclosed",
        "owner_c_coi_reviewed_and_accepted",
    ],
)
def test_unverified_custody_separation_competence_or_coi_without_defect_is_incomplete(
    validator: ModuleType, key: str
) -> None:
    evidence = _passing_evidence(validator)
    evidence[key] = False
    assert (
        validator.audit_completion_disposition(validator.PLAN_IDS[0], evidence)
        == "INCOMPLETE_FAIL_CLOSED"
    )


@pytest.mark.parametrize("plan_id_index", range(3))
def test_pure_completion_rule_passes_only_complete_admissible_evidence(
    validator: ModuleType, plan_id_index: int
) -> None:
    plan_id = validator.PLAN_IDS[plan_id_index]
    evidence = _passing_evidence(validator)
    assert validator.audit_completion_disposition(plan_id, evidence) == "PASS"
    evidence["bounded_disclosed_p2_count"] = 4
    assert validator.audit_completion_disposition(plan_id, evidence) == "PASS"


@pytest.mark.parametrize("key", list(range(10)))
def test_each_missing_readiness_item_is_fail_closed_incomplete(
    validator: ModuleType, key: int
) -> None:
    evidence = _passing_evidence(validator)
    evidence[validator.READINESS_KEYS[key]] = False
    assert (
        validator.audit_completion_disposition(validator.PLAN_IDS[0], evidence)
        == "INCOMPLETE_FAIL_CLOSED"
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("known_authorship_or_implementation_overlap", True),
        ("known_input_or_subject_mutation", True),
        ("forbidden_rerun_or_redesign", True),
        ("p0_finding_count", 1),
        ("p1_finding_count", 1),
        ("unbounded_or_undisclosed_p2_count", 1),
    ],
)
def test_substantive_defect_or_forbidden_effect_fails(
    validator: ModuleType, key: str, value: Any
) -> None:
    evidence = _passing_evidence(validator)
    evidence[key] = value
    assert validator.audit_completion_disposition(validator.PLAN_IDS[1], evidence) == "FAIL"


@pytest.mark.parametrize(
    "key,value",
    [
        ("known_authorship_or_implementation_overlap", True),
        ("known_input_or_subject_mutation", True),
        ("forbidden_rerun_or_redesign", True),
        ("p0_finding_count", 1),
        ("p1_finding_count", 1),
        ("unbounded_or_undisclosed_p2_count", 1),
    ],
)
def test_known_substantive_defect_precedes_simultaneous_missing_readiness(
    validator: ModuleType, key: str, value: Any
) -> None:
    evidence = _passing_evidence(validator)
    evidence["all_required_inputs_hash_bound"] = False
    evidence["actual_report_present"] = False
    evidence[key] = value
    assert validator.audit_completion_disposition(validator.PLAN_IDS[2], evidence) == "FAIL"


def test_nonimplementing_coauthor_is_still_ineligible(
    validator: ModuleType,
) -> None:
    evidence = _passing_evidence(validator)
    evidence["known_authorship_or_implementation_overlap"] = True
    assert validator.audit_completion_disposition(validator.PLAN_IDS[0], evidence) == "FAIL"


@pytest.mark.parametrize(
    "key",
    [
        "subject_matter_competence_declared",
        "conflict_of_interest_disclosed",
        "owner_c_coi_reviewed_and_accepted",
    ],
)
def test_missing_competence_or_missing_unaccepted_coi_is_incomplete(
    validator: ModuleType, key: str
) -> None:
    evidence = _passing_evidence(validator)
    evidence[key] = False
    assert (
        validator.audit_completion_disposition(validator.PLAN_IDS[1], evidence)
        == "INCOMPLETE_FAIL_CLOSED"
    )


def test_completion_rule_rejects_unknown_plan_roster_order_and_bad_types(
    validator: ModuleType,
) -> None:
    evidence = _passing_evidence(validator)
    with pytest.raises(validator.ValidationError, match="unknown"):
        validator.audit_completion_disposition("UNKNOWN", evidence)
    with pytest.raises(validator.ValidationError, match="roster or order"):
        validator.audit_completion_disposition(
            validator.PLAN_IDS[0], dict(reversed(tuple(evidence.items())))
        )
    with pytest.raises(validator.ValidationError, match="exact boolean"):
        bad = dict(evidence)
        bad["role_separation_satisfied"] = 1
        validator.audit_completion_disposition(validator.PLAN_IDS[0], bad)
    for value in (True, -1, 1.0, "0", None, _IntegerSubclass(0), 1 << 31):
        bad = dict(evidence)
        bad["p0_finding_count"] = value
        with pytest.raises(validator.ValidationError, match="bounded nonnegative"):
            validator.audit_completion_disposition(validator.PLAN_IDS[0], bad)
    with pytest.raises(validator.ValidationError, match="roster or order"):
        validator.audit_completion_disposition(
            validator.PLAN_IDS[0], _DictSubclass(evidence)
        )


MACHINE_MUTATIONS: List[Callable[[Dict[str, Any]], None]] = [
    lambda record: record.__setitem__("state", "PASS"),
    lambda record: record.__setitem__("global_state", "EXECUTABLE"),
    lambda record: record.__setitem__("control_predicate", "PASS"),
    lambda record: record["shared_completion_rule"]["known_fail_conditions"].pop(),
    lambda record: record["shared_completion_rule"][
        "incomplete_only_when_no_known_defect_conditions"
    ].pop(),
    lambda record: record["package_file_roster"].reverse(),
    lambda record: record["predecessor_bindings"].pop(),
    lambda record: record["predecessor_bindings"].reverse(),
    lambda record: record["field_closures"].pop(),
    lambda record: record["field_closures"].reverse(),
    lambda record: record["field_closures"].append(
        copy.deepcopy(record["field_closures"][0])
    ),
    lambda record: _replace(record, "field_closures.0.field_id", "F169"),
    lambda record: _replace(record, "field_closures.0.json_pointer", "/wrong"),
    lambda record: _replace(record, "field_closures.0.status", "CLOSED"),
    lambda record: _replace(
        record, "field_closures.0.value.plan_id", "PROOF_CODE_REPORT_V1"
    ),
    lambda record: record["field_closures"][0]["value"][
        "required_future_input_classes"
    ].pop(),
    lambda record: record["field_closures"][0]["value"][
        "required_future_input_classes"
    ].reverse(),
    lambda record: record["field_closures"][1]["value"][
        "ordered_procedure"
    ].pop(),
    lambda record: _replace(
        record, "field_closures.1.value.ordered_procedure.1.ordinal", 0
    ),
    lambda record: record["field_closures"][2]["value"][
        "required_future_output_classes"
    ].append("ALIEN_OUTPUT"),
    lambda record: _replace(
        record, "field_closures.0.value.actual_auditor_identity", "Alice"
    ),
    lambda record: _replace(
        record, "field_closures.0.value.actual_appointment_receipt", "receipt"
    ),
    lambda record: record["field_closures"][0]["value"][
        "required_future_assignment_admission_fields"
    ].pop(),
    lambda record: _replace(
        record,
        "field_closures.0.value.audit_executor_role",
        "INDEPENDENT_NONIMPLEMENTER_BUT_SUBJECT_COAUTHOR",
    ),
    lambda record: _replace(
        record,
        "field_closures.1.value.actual_subject_matter_competence_declaration",
        "claimed",
    ),
    lambda record: _replace(
        record,
        "field_closures.1.value.actual_conflict_of_interest_disclosure",
        "none-declared",
    ),
    lambda record: _replace(
        record,
        "field_closures.1.value.actual_owner_c_coi_review_and_acceptance",
        "accepted",
    ),
    lambda record: _replace(
        record,
        "field_closures.2.value.audit_executor_role",
        "CLEAN_ROOM_EXECUTOR_SEPARATE_WORKSPACE_BUT_SUBJECT_AUTHOR",
    ),
    lambda record: _replace(
        record, "field_closures.1.value.actual_input_manifest", "manifest"
    ),
    lambda record: _replace(
        record, "field_closures.1.value.actual_output_report", "report"
    ),
    lambda record: _replace(
        record, "field_closures.0.value.actual_output_artifact_path", "audit.json"
    ),
    lambda record: _replace(record, "field_closures.2.value.audit_executed", True),
    lambda record: _replace(
        record,
        "shared_owner_role_and_process.actual_person_institution_account_or_external_identity",
        "person",
    ),
    lambda record: record["shared_owner_role_and_process"][
        "required_future_assignment_admission_fields"
    ].remove("DECLARED_SUBJECT_MATTER_COMPETENCE"),
    lambda record: _replace(
        record,
        "shared_owner_role_and_process.actual_subject_matter_competence_declaration",
        "claimed",
    ),
    lambda record: _replace(
        record,
        "shared_owner_role_and_process.actual_conflict_of_interest_disclosure",
        "disclosed",
    ),
    lambda record: _replace(
        record,
        "shared_owner_role_and_process.actual_owner_c_coi_review_and_acceptance",
        "accepted",
    ),
    lambda record: _replace(
        record,
        "shared_owner_role_and_process.proof_code_and_methods_auditor_role",
        record["shared_owner_role_and_process"]["responsible_owner_role"],
    ),
    lambda record: _replace(
        record, "severity_and_disposition_model.finding_deletion_permitted", True
    ),
    lambda record: _replace(record, "count_transition.after.post_execution_open", 2),
    lambda record: _replace(record, "count_transition.after.total_closed", 25),
    lambda record: record["count_transition"]["closed_by_package"][
        "field_ids"
    ].append("F169"),
    lambda record: _replace(record, "count_transition.blockers_closed", 1),
    lambda record: _replace(record, "count_transition.formal_tests_closed", 1),
    lambda record: _replace(record, "count_transition.results_filled", 1),
    lambda record: _replace(record, "comprehensive_field_sweep.F169_value", "path"),
    lambda record: record["comprehensive_field_sweep"]["open_post_ids"].remove(
        "F169"
    ),
    lambda record: record["comprehensive_field_sweep"]["closed_post_ids"].append(
        "F169"
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.B11_remains_open", False
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.F169_remains_open_and_null", False
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.formal_test_30_status", "CLOSED"
    ),
    lambda record: _replace(
        record,
        "project_effects_and_nonclaims.network_contact_repository_license_or_data_access_performed",
        True,
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.entropy_generated_or_consumed", True
    ),
    lambda record: _replace(
        record,
        "project_effects_and_nonclaims.subprocess_or_environment_build_performed",
        True,
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.runtime_or_operational_receipt_created", True
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.audit_or_clean_room_execution_performed", True
    ),
    lambda record: _replace(
        record,
        "project_effects_and_nonclaims.auditor_or_clean_room_executor_selected_or_admitted",
        True,
    ),
    lambda record: _replace(
        record,
        "project_effects_and_nonclaims.competence_declaration_or_coi_disclosure_acceptance_receipt_created",
        True,
    ),
    lambda record: _replace(
        record,
        "project_effects_and_nonclaims.training_scientific_or_production_execution_performed",
        True,
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.result_or_claim_promoted", True
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.submission_or_release_performed", True
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.tracker_or_evidence_ledger_edited", True
    ),
    lambda record: _replace(
        record,
        "authority_provenance.entropy_subprocess_runtime_clean_room_or_science_authorized",
        True,
    ),
    lambda record: _replace(
        record, "evidence_ready_registration.registration_performed_by_this_package", True
    ),
    lambda record: record["evidence_ready_registration"][
        "permitted_field_delta"
    ].append("F169"),
    lambda record: _replace(
        record, "qualification_boundary.self_validation_is_independent_acceptance", True
    ),
]


@pytest.mark.parametrize("mutation", MACHINE_MUTATIONS)
def test_coherently_rehashed_machine_tampering_fails_expected_projection(
    validator: ModuleType,
    tmp_path: Path,
    mutation: Callable[[Dict[str, Any]], None],
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(validator, root, mutation)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_machine_tamper_without_rehash_fails_semantic_digest(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: record.__setitem__("state", "PASS"),
        recompute_digest=False,
    )
    with pytest.raises(validator.ValidationError, match="semantic digest"):
        validator.validate(root)


@pytest.mark.parametrize("index", range(8))
def test_every_predecessor_byte_fails_closed(
    validator: ModuleType, tmp_path: Path, index: int
) -> None:
    root = _copy_roster(validator, tmp_path)
    relative = validator.PREDECESSOR_SPECS[index][2]
    path = root / relative
    raw = path.read_bytes()
    path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="predecessor exact-byte"):
        validator.validate(root)


@pytest.mark.parametrize(
    "relative", [str(HUMAN_REL), str(VALIDATOR_REL), str(TEST_REL)]
)
def test_every_nonmachine_package_byte_fails_closed(
    validator: ModuleType, tmp_path: Path, relative: str
) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / relative
    path.write_bytes(path.read_bytes() + b"X")
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_noncanonical_machine_json_fails_closed(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(validator, root, lambda record: None, canonical=False)
    with pytest.raises(validator.ValidationError, match="not canonical"):
        validator.validate(root)


def test_duplicate_machine_key_fails_closed(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / MACHINE_REL
    path.write_bytes(b'{"schema_version":"a","schema_version":"b"}\n')
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="strict JSON"):
        validator.validate(root)


@pytest.mark.parametrize("relative", [str(MACHINE_REL), str(HUMAN_REL)])
def test_executable_mode_fails_closed(
    validator: ModuleType, tmp_path: Path, relative: str
) -> None:
    root = _copy_roster(validator, tmp_path)
    (root / relative).chmod(0o755)
    with pytest.raises(validator.ValidationError, match="mode"):
        validator.validate(root)


@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_link_substitution_or_alias_fails_closed(
    validator: ModuleType, tmp_path: Path, kind: str
) -> None:
    root = _copy_roster(validator, tmp_path / "root")
    target = root / HUMAN_REL
    alternate = tmp_path / "alternate.md"
    shutil.copyfile(target, alternate)
    alternate.chmod(0o644)
    target.unlink()
    if kind == "symlink":
        target.symlink_to(alternate)
    else:
        os.link(alternate, target)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_fingerprint_covers_inode_and_exact_permission_bits(
    validator: ModuleType,
) -> None:
    status = (ROOT / HUMAN_REL).lstat()
    assert validator._fingerprint(status) != validator._fingerprint(
        _StatProxy(status, st_ino=status.st_ino + 1)
    )
    changed_mode = (status.st_mode & ~0o777) | 0o600
    assert validator._fingerprint(status) != validator._fingerprint(
        _StatProxy(status, st_mode=changed_mode)
    )


@pytest.mark.parametrize("observation", [1, 2])
@pytest.mark.parametrize("drift", ["inode", "mode", "nlink"])
def test_each_fd_observation_rejects_inode_mode_or_link_drift(
    validator: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    observation: int,
    drift: str,
) -> None:
    original_fstat = validator.os.fstat
    calls = 0

    def drifting_fstat(descriptor: int) -> Any:
        nonlocal calls
        calls += 1
        status = original_fstat(descriptor)
        if calls != observation:
            return status
        if drift == "inode":
            return _StatProxy(status, st_ino=status.st_ino + 1)
        if drift == "mode":
            return _StatProxy(
                status, st_mode=(status.st_mode & ~0o777) | 0o600
            )
        return _StatProxy(status, st_nlink=status.st_nlink + 1)

    monkeypatch.setattr(validator.os, "fstat", drifting_fstat)
    with pytest.raises(validator.ValidationError):
        validator._stable_read(ROOT, str(HUMAN_REL))


@pytest.mark.parametrize("race", ["mode", "inode"])
def test_post_open_path_mode_or_inode_substitution_race_fails_closed(
    validator: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    race: str,
) -> None:
    root = _copy_roster(validator, tmp_path / "root")
    target = root / HUMAN_REL
    original_raw = target.read_bytes()
    original_close = validator.os.close
    mutated = False

    def close_then_substitute(descriptor: int) -> None:
        nonlocal mutated
        original_close(descriptor)
        if mutated:
            return
        mutated = True
        if race == "mode":
            target.chmod(0o600)
            return
        target.unlink()
        target.write_bytes(original_raw)
        target.chmod(0o644)

    monkeypatch.setattr(validator.os, "close", close_then_substitute)
    with pytest.raises(validator.ValidationError):
        validator._stable_read(root, str(HUMAN_REL))
    assert mutated is True


@pytest.mark.parametrize("bad", ["../escape", "/absolute", "a//b", "./x", "a\\b"])
def test_path_escape_or_noncanonical_path_fails_closed(
    validator: ModuleType, bad: str
) -> None:
    with pytest.raises(validator.ValidationError):
        validator._stable_read(ROOT, bad)


def test_validator_has_no_effectful_import_or_write_surface(
    validator: ModuleType,
) -> None:
    source = (ROOT / VALIDATOR_REL).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(
        {
            "socket",
            "subprocess",
            "urllib",
            "http",
            "requests",
            "random",
            "secrets",
            "numpy",
            "torch",
            "heterodiff",
        }
    )
    forbidden_fragments = (
        "O_CREAT",
        "O_TRUNC",
        "O_WRONLY",
        ".write_text(",
        ".write_bytes(",
        "os.write(",
        "os.remove(",
        "os.unlink(",
        ".unlink(",
        ".mkdir(",
        ".rename(",
        ".replace(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_validation_is_cwd_independent_and_byte_read_only(
    validator: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _closed_roster(validator)
    before = _tree_digest(ROOT, paths)
    monkeypatch.chdir(tmp_path)
    assert validator.validate(ROOT)["validation"] == "PASS"
    after = _tree_digest(ROOT, paths)
    assert after == before
