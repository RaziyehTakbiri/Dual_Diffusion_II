"""Read-only validator for the additive B11 pre-outcome audit-plan freeze.

The module validates three exact plan fields and exposes one pure fail-closed
completion-disposition helper.  It has no writer, network, connector,
subprocess, entropy, project-science, data, training, runtime-capture,
clean-room, production, or submission route.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-b11-preoutcome-audit-plan-freeze-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "B11_PREOUTCOME_AUDIT_PLANS_FROZEN_REPORTS_NOT_CREATED"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
REPORTED_DATE = "2026-09-01"
PACKAGE_KIND = "ADDITIVE_OFFLINE_POSTEXECUTION_PLAN_FIELD_CLOSURE"
CONTROL_PREDICATE = (
    "PREOUTCOME_PROOF_CODE_METHODS_STATISTICS_CLEAN_ROOM_AUDIT_PLANS_FROZEN"
)

HUMAN_PATH = "PROJECT_B11_PREOUTCOME_AUDIT_PLAN_FREEZE.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.py"
)
PACKAGE_ROSTER = (HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)

COORDINATOR_INSTRUCTION = (
    "Proceed with Rank 1 as author: construct one additive offline B11 "
    "pre-outcome audit-plan freeze closing exactly F168, F170, F171 under "
    "predicate PREOUTCOME_PROOF_CODE_METHODS_STATISTICS_CLEAN_ROOM_AUDIT_"
    "PLANS_FROZEN."
)

EVIDENCE_READY_REGISTRATION = (
    "Upon independent acceptance, register only this delta: F168 "
    "(`/ethics_release_and_review_plan/proof_and_code_audit_plan`), F170 "
    "(`/ethics_release_and_review_plan/methods_and_statistics_audit_plan`), "
    "and F171 (`/ethics_release_and_review_plan/clean_room_reproduction_"
    "audit_plan`) are closed by the exact pre-outcome plans "
    "`PROOF_AND_CODE_AUDIT_PLAN_V1`, "
    "`METHODS_AND_STATISTICS_AUDIT_PLAN_V1`, and "
    "`CLEAN_ROOM_REPRODUCTION_AUDIT_PLAN_V1`. Pre-execution counts remain "
    "145 open / 21 closed; post-execution counts move from 6 open / 0 closed "
    "to 3 open / 3 closed; total counts move from 151 open / 21 closed to "
    "148 open / 24 closed. F169 remains OPEN/null and B11 and all 12 "
    "blockers remain OPEN. Formal Tests 28 and 29 remain OPEN, Formal Test "
    "30 remains PENDING, R1-R4 remain unexecuted, and 0/4 results are filled. "
    "No auditor or clean-room executor identity or appointment, subject-matter "
    "competence declaration, conflict-of-interest disclosure or Owner C "
    "acceptance receipt, audit input instance, artifact/report/path, clean-room "
    "run, network, data, entropy, subprocess, runtime, "
    "scientific result, claim, submission, tracker edit, or evidence-ledger "
    "edit is supplied by this package."
)

OWNER_ROLE = "OWNER_C_DATA_GOVERNANCE_AND_REPRODUCTION_COORDINATOR"
AUDITOR_ROLE = "INDEPENDENT_AUDIT_EXECUTOR_NOT_ANY_AUTHOR_OR_IMPLEMENTER_OF_SUBJECT"
CLEAN_ROOM_ROLE = (
    "CLEAN_ROOM_EXECUTOR_NOT_ANY_AUTHOR_OR_IMPLEMENTER_OF_SUBJECT_AND_SEPARATE_"
    "FROM_SUBJECT_WORKSPACE"
)

ASSIGNMENT_ADMISSION_FIELDS = (
    "EXECUTOR_IDENTITY",
    "DECLARATION_NOT_ANY_AUTHOR_OR_IMPLEMENTER_OF_AUDITED_SUBJECT",
    "DECLARED_SUBJECT_MATTER_COMPETENCE",
    "COMPLETE_CONFLICT_OF_INTEREST_DISCLOSURE",
    "OWNER_C_CONFLICT_OF_INTEREST_REVIEW_AND_ACCEPTANCE",
    "OWNER_C_ASSIGNMENT_ACCEPTANCE",
)

SEPARATION_RULES = (
    "OWNER_C_MAY_COORDINATE_BUT_MAY_NOT_OVERRIDE_TERMINAL_FAILURE_OR_SOLELY_AUDIT",
    "AUDIT_EXECUTOR_MUST_NOT_BE_ANY_AUTHOR_OR_IMPLEMENTER_OF_AUDITED_SUBJECT",
    "CLEAN_ROOM_EXECUTOR_MUST_NOT_BE_ANY_AUTHOR_OR_IMPLEMENTER_OF_AUDITED_SUBJECT",
    "SUBJECT_AUTHOR_OR_IMPLEMENTER_MAY_ANSWER_BUT_MAY_NOT_AUDIT_OR_SELF_ACCEPT",
    "AUDITOR_IS_READ_ONLY_WITH_RESPECT_TO_FROZEN_SUBJECT_ARTIFACTS",
    "CLEAN_ROOM_EXECUTOR_USES_SEPARATE_WORKSPACE_AND_ONLY_ADMITTED_INPUTS",
    "BOTH_EXECUTOR_ROLES_REQUIRE_DECLARED_COMPETENCE_AND_OWNER_C_ACCEPTED_COI",
    "KNOWN_AUTHORSHIP_OR_IMPLEMENTATION_OVERLAP_IS_FAIL",
    "KNOWN_INPUT_OR_SUBJECT_MUTATION_IS_FAIL",
    "KNOWN_FORBIDDEN_RERUN_OR_REDESIGN_IS_FAIL",
    "MISSING_OR_UNVERIFIED_SEPARATION_CUSTODY_COMPETENCE_COI_OR_READINESS_WITH_NO_KNOWN_DEFECT_IS_INCOMPLETE_FAIL_CLOSED",
)

SEVERITY_MODEL: Mapping[str, Any] = {
    "P0": "INVALIDATES_CORE_PREDICATE_CLAIM_OR_SAFETY_AND_ALWAYS_FAILS",
    "P1": "MATERIAL_METHOD_PROOF_OR_REPRODUCIBILITY_DEFECT_AND_ALWAYS_FAILS",
    "P2": (
        "BOUNDED_NONCORE_DEFECT_MAY_COEXIST_WITH_PASS_ONLY_IF_FULLY_DISCLOSED_"
        "AND_NO_PREDICATE_CLAIM_OR_REPRODUCIBILITY_EFFECT"
    ),
    "finding_deletion_permitted": False,
    "finding_may_authorize_confirmatory_rerun_or_redesign": False,
    "claim_narrowing_or_submission_stop_permitted": True,
}


def _steps(*step_ids: str) -> List[Dict[str, Any]]:
    return [
        {"ordinal": ordinal, "step_id": step_id}
        for ordinal, step_id in enumerate(step_ids)
    ]


PROOF_CODE_PLAN: Mapping[str, Any] = {
    "plan_id": "PROOF_AND_CODE_AUDIT_PLAN_V1",
    "field_id": "F168",
    "json_pointer": "/ethics_release_and_review_plan/proof_and_code_audit_plan",
    "responsible_owner_role": OWNER_ROLE,
    "audit_executor_role": AUDITOR_ROLE,
    "actual_auditor_identity": None,
    "actual_appointment_receipt": None,
    "required_future_assignment_admission_fields": list(ASSIGNMENT_ADMISSION_FIELDS),
    "actual_subject_matter_competence_declaration": None,
    "actual_conflict_of_interest_disclosure": None,
    "actual_owner_c_coi_review_and_acceptance": None,
    "scope": (
        "FINAL_THEOREM_ASSUMPTIONS_PROOF_OBLIGATIONS_TWO_DIRECTION_CODE_"
        "CROSSWALK_BOUNDARY_CASES_AND_CLAIM_SUPPORT"
    ),
    "required_future_input_classes": [
        "FINAL_THEOREM_STATEMENT_ASSUMPTION_ROSTER_AND_CLAIM_BOUNDARY",
        "PROOF_PACKAGE_OBLIGATION_ROSTER_LEMMAS_COUNTEREXAMPLES_AND_BOUNDARY_CASES",
        "FINAL_PROOF_TO_CODE_SYMBOL_CROSSWALK",
        "EXACT_SOURCE_AND_CONFIGURATION_MANIFEST_FOR_EXECUTABLE_QUANTITIES",
        "EXACT_TEST_PREDICATES_AND_INDEPENDENT_RECOMPUTATION_RECIPE",
        "ALL_EARLIER_PROOF_CODE_FINDINGS_AND_PRESERVED_DISPOSITIONS",
        "CLAIM_LEDGER_ENTRIES_DEPENDENT_ON_THE_AUDITED_PROOF",
    ],
    "ordered_procedure": _steps(
        "ADMIT_EXACT_INPUT_CUSTODY_AND_ROSTER",
        "MATCH_THEOREM_STATEMENTS_TO_ASSUMPTIONS_AND_SCOPE",
        "VERIFY_PROOF_OBLIGATION_COMPLETENESS_AND_NONOVERLAP",
        "VERIFY_TWO_DIRECTION_PROOF_SYMBOL_AND_CODE_CROSSWALK",
        "VERIFY_EXECUTABLE_BOUNDARY_CASES_NEGATIVE_CONTROLS_AND_COUNTEREXAMPLES",
        "RECONCILE_FINDINGS_WITH_CLAIM_LEDGER_WITHOUT_MUTATION_OR_REDESIGN",
        "SEAL_TERMINAL_REPORT_AND_COMPLETE_FINDING_REGISTER",
    ),
    "required_future_output_classes": [
        "INPUT_CUSTODY_RECEIPT",
        "PROOF_OBLIGATION_COVERAGE_MATRIX",
        "TWO_DIRECTION_SYMBOL_CROSSWALK_RESULT",
        "BOUNDARY_CASE_AND_COUNTEREXAMPLE_RESULT_ROSTER",
        "COMPLETE_FINDING_REGISTER",
        "CLAIM_IMPACT_DISPOSITION",
        "TERMINAL_REPORT_DIGEST",
    ],
    "actual_input_manifest": None,
    "actual_output_report": None,
    "actual_output_artifact_path": None,
    "audit_executed": False,
    "completion_rule_id": "SHARED_FAIL_CLOSED_AUDIT_COMPLETION_RULE_V1",
}

METHODS_STATISTICS_PLAN: Mapping[str, Any] = {
    "plan_id": "METHODS_AND_STATISTICS_AUDIT_PLAN_V1",
    "field_id": "F170",
    "json_pointer": (
        "/ethics_release_and_review_plan/methods_and_statistics_audit_plan"
    ),
    "responsible_owner_role": OWNER_ROLE,
    "audit_executor_role": AUDITOR_ROLE,
    "actual_auditor_identity": None,
    "actual_appointment_receipt": None,
    "required_future_assignment_admission_fields": list(ASSIGNMENT_ADMISSION_FIELDS),
    "actual_subject_matter_competence_declaration": None,
    "actual_conflict_of_interest_disclosure": None,
    "actual_owner_c_coi_review_and_acceptance": None,
    "scope": (
        "PREREGISTRATION_CONFORMANCE_ESTIMAND_PAIRING_HIERARCHY_INFERENCE_"
        "POWER_SEEDS_FAILURES_DEVIATIONS_COMPUTE_AND_CLAIM_TRANSITION"
    ),
    "required_future_input_classes": [
        "FINAL_FROZEN_PREREGISTRATION_AND_MACHINE_COMPANION",
        "ACCEPTED_FIELD_BLOCKER_FORMAL_TEST_GATE_AND_RESULT_TRANSITION_LEDGER",
        "DOMAIN_SPLIT_METHOD_BASELINE_CHECKPOINT_SEED_AND_RUN_MANIFESTS",
        "RAW_PREDICTIONS_OR_SAMPLES_LOGS_CHECKPOINTS_AND_TERMINAL_STATUSES",
        "METRIC_ESTIMAND_MARGIN_MULTIPLICITY_INTERVAL_POWER_AND_CONSTRAINT_SPECS",
        "PRIMARY_SECONDARY_TABLES_AND_INDEPENDENT_RECOMPUTATION_RECIPES",
        "ALL_FAILURE_EXCLUSION_DEVIATION_ABORT_AND_ATTEMPTED_RERUN_RECORDS",
        "PLANNED_REALIZED_COMPUTE_RECEIPTS_AND_CLAIM_LEDGER",
    ],
    "ordered_procedure": _steps(
        "ADMIT_EXACT_INPUT_CUSTODY_AND_COMPLETE_ATTEMPT_ROSTER",
        "COMPARE_REALIZED_METHOD_DOMAIN_SPLIT_SEED_AND_CHECKPOINT_TO_FREEZE",
        "VERIFY_ESTIMAND_PAIRING_NATURAL_GROUP_HIERARCHY_MISSINGNESS_AND_FAILURES",
        "INDEPENDENTLY_RECOMPUTE_METRICS_MULTIPLICITY_INTERVALS_MARGINS_AND_GATES",
        "RECONCILE_POWER_SAMPLE_SIZE_STOPPING_AND_SEED_REGISTRY",
        "RECONCILE_FAILURES_EXCLUSIONS_DEVIATIONS_ABORTS_AND_RETRY_PROHIBITIONS",
        "RECONCILE_PLANNED_AND_REALIZED_COMPUTE_INCLUDING_FAILED_ATTEMPTS",
        "CHECK_EVERY_PROMOTED_OR_WITHHELD_CLAIM_AGAINST_TERMINAL_EVIDENCE",
        "SEAL_TERMINAL_REPORT_AND_COMPLETE_FINDING_REGISTER",
    ),
    "required_future_output_classes": [
        "INPUT_CUSTODY_RECEIPT",
        "ATTEMPT_ROSTER_COMPLETENESS_RECEIPT",
        "PREREGISTRATION_DEVIATION_MATRIX",
        "INDEPENDENT_NUMERICAL_RECOMPUTATION",
        "FAILURE_EXCLUSION_DEVIATION_REGISTER",
        "COMPUTE_RECONCILIATION",
        "CLAIM_IMPACT_DISPOSITION",
        "COMPLETE_FINDING_REGISTER",
        "TERMINAL_REPORT_DIGEST",
    ],
    "actual_input_manifest": None,
    "actual_output_report": None,
    "actual_output_artifact_path": None,
    "audit_executed": False,
    "completion_rule_id": "SHARED_FAIL_CLOSED_AUDIT_COMPLETION_RULE_V1",
}

CLEAN_ROOM_PLAN: Mapping[str, Any] = {
    "plan_id": "CLEAN_ROOM_REPRODUCTION_AUDIT_PLAN_V1",
    "field_id": "F171",
    "json_pointer": (
        "/ethics_release_and_review_plan/clean_room_reproduction_audit_plan"
    ),
    "responsible_owner_role": OWNER_ROLE,
    "audit_executor_role": CLEAN_ROOM_ROLE,
    "actual_auditor_identity": None,
    "actual_appointment_receipt": None,
    "required_future_assignment_admission_fields": list(ASSIGNMENT_ADMISSION_FIELDS),
    "actual_subject_matter_competence_declaration": None,
    "actual_conflict_of_interest_disclosure": None,
    "actual_owner_c_coi_review_and_acceptance": None,
    "scope": (
        "SEPARATE_WORKSPACE_INPUT_ENVIRONMENT_DATA_RUN_ARTIFACT_RESULT_FAILURE_"
        "COMPUTE_AND_TERMINAL_PREDICATE_REPRODUCTION"
    ),
    "required_future_input_classes": [
        "FROZEN_SOURCE_TREE_OR_COMMIT_ARCHIVE",
        "ENVIRONMENT_CONTAINER_LOCKFILE_TOOLCHAIN_AND_HARDWARE_REQUIREMENT_DIGESTS",
        "COMPLETE_CLEAN_ROOM_INPUT_MANIFEST_SCHEMA_AND_ADMITTED_INSTANCE",
        "AUTHORIZED_DATA_LICENSE_SCHEMA_PREPROCESSING_SPLIT_MANIFESTS_AND_CAPSULE",
        "METHOD_BASELINE_CHECKPOINT_SEED_SCHEDULE_AND_COMPUTE_MANIFESTS",
        "EXACT_INVOCATION_SPECIFICATIONS_AND_EXPECTED_ARTIFACT_SCHEMAS",
        "ORIGINAL_ARTIFACT_RESULT_FAILURE_AND_COMPUTE_RECEIPTS_FOR_COMPARISON",
        "FROZEN_COMPARISON_TOLERANCES_AND_TERMINAL_PREDICATES",
    ],
    "ordered_procedure": _steps(
        "ADMIT_EXACT_INPUT_CUSTODY_AND_PROVE_SUBJECT_WORKSPACE_SEPARATION",
        "CONSTRUCT_DECLARED_ENVIRONMENT_ONLY_WITH_ADMITTED_AUTHORIZED_INPUTS",
        "ADMIT_LAWFULLY_SUPPLIED_DATA_CAPSULE_WITHOUT_DISCOVERY_OR_SUBSTITUTION",
        "EXECUTE_ONLY_FROZEN_SCHEDULE_AND_PRESERVE_EVERY_ATTEMPT_AND_FAILURE",
        "REPRODUCE_ARTIFACT_INVENTORY_AND_INDEPENDENTLY_RECOMPUTE_PREDICATES",
        "COMPARE_EVERY_REQUIRED_OUTPUT_UNDER_FROZEN_EXACT_OR_NUMERIC_TOLERANCE",
        "RECONCILE_DEVIATIONS_ENVIRONMENT_FAILURES_AND_COMPUTE",
        "SEAL_TERMINAL_REPORT_AND_COMPLETE_FINDING_REGISTER",
    ),
    "required_future_output_classes": [
        "WORKSPACE_SEPARATION_RECEIPT",
        "INPUT_ADMISSION_RECEIPT",
        "ENVIRONMENT_RECONSTRUCTION_RECEIPT",
        "COMPLETE_ATTEMPT_ROSTER",
        "REPRODUCED_ARTIFACT_INVENTORY",
        "EXACT_OR_TOLERANCE_COMPARISON_MATRIX",
        "FAILURE_DEVIATION_AND_COMPUTE_RECONCILIATION",
        "COMPLETE_FINDING_REGISTER",
        "TERMINAL_REPORT_DIGEST",
    ],
    "actual_input_manifest": None,
    "actual_output_report": None,
    "actual_output_artifact_path": None,
    "audit_executed": False,
    "completion_rule_id": "SHARED_FAIL_CLOSED_AUDIT_COMPLETION_RULE_V1",
}

PLAN_VALUES = (PROOF_CODE_PLAN, METHODS_STATISTICS_PLAN, CLEAN_ROOM_PLAN)
PLAN_IDS = tuple(plan["plan_id"] for plan in PLAN_VALUES)

READINESS_KEYS = (
    "all_required_inputs_hash_bound",
    "input_roster_exact_and_complete",
    "role_separation_satisfied",
    "subject_matter_competence_declared",
    "conflict_of_interest_disclosed",
    "owner_c_coi_reviewed_and_accepted",
    "all_ordered_steps_completed",
    "all_required_outputs_hash_bound",
    "all_findings_preserved",
    "actual_report_present",
)
FORBIDDEN_EFFECT_KEYS = (
    "known_authorship_or_implementation_overlap",
    "known_input_or_subject_mutation",
    "forbidden_rerun_or_redesign",
)
FINDING_COUNT_KEYS = (
    "p0_finding_count",
    "p1_finding_count",
    "bounded_disclosed_p2_count",
    "unbounded_or_undisclosed_p2_count",
)
COMPLETION_EVIDENCE_KEYS = READINESS_KEYS + FORBIDDEN_EFFECT_KEYS + FINDING_COUNT_KEYS

POST_FIELDS = ("F164", "F165", "F168", "F169", "F170", "F171")
PRE_FIELDS = tuple(
    "F" + str(index).zfill(3)
    for index in range(1, 173)
    if "F" + str(index).zfill(3) not in POST_FIELDS
)
CLOSED_PRE_AFTER_F104 = (
    "F007",
    "F008",
    "F009",
    "F010",
    "F011",
    "F012",
    "F013",
    "F014",
    "F015",
    "F016",
    "F017",
    "F018",
    "F060",
    "F104",
    "F106",
    "F107",
    "F108",
    "F113",
    "F128",
    "F129",
    "F148",
)
OPEN_PRE_AFTER_F104 = tuple(
    field for field in PRE_FIELDS if field not in CLOSED_PRE_AFTER_F104
)
CLOSED_POST_AFTER = ("F168", "F170", "F171")
OPEN_POST_AFTER = tuple(
    field for field in POST_FIELDS if field not in CLOSED_POST_AFTER
)


class ValidationError(ValueError):
    """Exact plan, schema, custody, or semantic validation failed."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    if type(value) is not dict:
        raise ValidationError("canonical JSON input must be an exact dictionary")
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise ValidationError("value is not canonical ASCII JSON") from error


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        raise ValidationError("record must be an exact dictionary")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload))


def _semantic_record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict or type(record.get("schema_version")) is not str:
        raise ValidationError("machine predecessor has no exact schema")
    payload = dict(record)
    payload.pop("record_sha256", None)
    domain = (record["schema_version"] + "\0").encode("ascii")
    return _sha256(domain + _canonical_payload_bytes(payload))


def _object_without_duplicate_keys(
    pairs: Sequence[Tuple[str, Any]],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _parse_json(raw: bytes, label: str) -> Dict[str, Any]:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValidationError(label + " must be ASCII JSON") from error
    try:
        value = json.loads(text, object_pairs_hook=_object_without_duplicate_keys)
    except (json.JSONDecodeError, ValidationError) as error:
        raise ValidationError(label + " is not strict JSON") from error
    if type(value) is not dict:
        raise ValidationError(label + " top level must be an exact object")
    return value


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if any(type(key) is not str for key in actual):
            raise ValidationError(label + " key type mismatch")
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for index, expected_item in enumerate(expected):
            _strict_equal(actual[index], expected_item, label + "[" + str(index) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def audit_completion_disposition(plan_id: Any, evidence: Any) -> str:
    """Return the exact fail-closed disposition for caller-supplied evidence."""

    if type(plan_id) is not str or plan_id not in PLAN_IDS:
        raise ValidationError("unknown audit plan id")
    if type(evidence) is not dict or tuple(evidence) != COMPLETION_EVIDENCE_KEYS:
        raise ValidationError("completion evidence roster or order mismatch")
    for key in READINESS_KEYS + FORBIDDEN_EFFECT_KEYS:
        if type(evidence[key]) is not bool:
            raise ValidationError(key + " must be an exact boolean")
    for key in FINDING_COUNT_KEYS:
        value = evidence[key]
        if type(value) is not int or value < 0 or value.bit_length() > 31:
            raise ValidationError(key + " must be a bounded nonnegative integer")
    if any(evidence[key] for key in FORBIDDEN_EFFECT_KEYS):
        return "FAIL"
    if (
        evidence["p0_finding_count"] != 0
        or evidence["p1_finding_count"] != 0
        or evidence["unbounded_or_undisclosed_p2_count"] != 0
    ):
        return "FAIL"
    if not all(evidence[key] for key in READINESS_KEYS):
        return "INCOMPLETE_FAIL_CLOSED"
    return "PASS"


# group, role, path, byte count, raw SHA-256, optional semantic self-digest
PREDECESSOR_SPECS: Tuple[
    Tuple[str, str, str, int, str, Optional[str]], ...
] = (
    (
        "EXECUTION_PREREGISTRATION_V1",
        "human",
        "manuscript_v3/execution_preregistration.md",
        22491,
        "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
        None,
    ),
    (
        "EXECUTION_PREREGISTRATION_V1",
        "machine",
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        39771,
        "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
        None,
    ),
    (
        "ACCEPTED_F104_BASELINE",
        "human",
        "PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md",
        9596,
        "4d73909714e5227175b8c0f250876ffeddcd25ad9cc4d54b27d02499c562edfb",
        None,
    ),
    (
        "ACCEPTED_F104_BASELINE",
        "machine",
        "research/fixtures/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json",
        12639,
        "c6275a6fb6941b28c2b0ed89196efdfeeba5530d8cabe47f173452cda364af54",
        "ba1c3a7898c858ec7cf7b3073c869a134cd8a06b93aeb0f7778793c271c96d7b",
    ),
    (
        "ACCEPTED_F104_BASELINE",
        "validator",
        "research/diagnostics/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py",
        33938,
        "817a64acaf2441314ad73190569bd969c304a9b1d01fc7533d7fdfc6dad1734b",
        None,
    ),
    (
        "ACCEPTED_F104_BASELINE",
        "test",
        "tests/unit/test_manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py",
        30095,
        "5ef4f22b71f24f980f9553c7e32f7de912ab85c23328b4d42019d2ae107e7693",
        None,
    ),
    (
        "ACCEPTED_F104_BASELINE",
        "independent_review",
        "PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE_INDEPENDENT_REVIEW.md",
        10230,
        "7694694d7fe2b0c2dd17f79b9e0f9d2f44c14c59c3f0568902e3cad7d75ae402",
        None,
    ),
    (
        "ANTI_DRIFT_POLICY",
        "policy",
        "PROJECT_ANTI_DRIFT_OPERATING_POLICY.md",
        2240,
        "22f1006bfd0b4dde8eb51e6e30abd7b153882a3fd41d6f3a3494ffd98a98bbd3",
        None,
    ),
)
PREDECESSOR_GROUP_COUNTS = {
    "EXECUTION_PREREGISTRATION_V1": 2,
    "ACCEPTED_F104_BASELINE": 5,
    "ANTI_DRIFT_POLICY": 1,
}


def _canonical_relative_path(relative: Any) -> Tuple[str, ...]:
    if type(relative) is not str or not relative or "\\" in relative:
        raise ValidationError("binding path must be a nonempty POSIX string")
    path = Path(relative)
    if path.is_absolute() or relative.startswith("/"):
        raise ValidationError("binding path must be relative")
    if "/".join(path.parts) != relative:
        raise ValidationError("binding path must be canonical")
    if any(part in (".", "..") for part in path.parts):
        raise ValidationError("binding path traversal is forbidden")
    return tuple(path.parts)


def _ancestor_snapshot(root: Path, target: Path) -> Tuple[Tuple[int, int, int], ...]:
    snapshots: List[Tuple[int, int, int]] = []
    current = target.parent
    while True:
        status = current.lstat()
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise ValidationError("unsafe ancestor: " + str(current))
        snapshots.append((status.st_dev, status.st_ino, stat.S_IFMT(status.st_mode)))
        if current == root:
            return tuple(snapshots)
        if root not in current.parents:
            raise ValidationError("binding path escaped the workspace root")
        current = current.parent


def _assert_binding_status(value: os.stat_result, label: str) -> None:
    if not stat.S_ISREG(value.st_mode):
        raise ValidationError(label + " must be a regular file")
    if stat.S_IMODE(value.st_mode) != 0o644:
        raise ValidationError(label + " mode must be exactly 0644")
    if value.st_nlink != 1:
        raise ValidationError(label + " must have exactly one hard link")


def _fingerprint(
    value: os.stat_result,
) -> Tuple[int, int, int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        stat.S_IFMT(value.st_mode),
        stat.S_IMODE(value.st_mode),
        value.st_nlink,
    )


def _stable_read(root: Path, relative: str) -> bytes:
    if not isinstance(root, Path) or not root.is_absolute():
        raise ValidationError("workspace root must be an absolute Path")
    parts = _canonical_relative_path(relative)
    target = root.joinpath(*parts)
    ancestors_before = _ancestor_snapshot(root, target)
    before_path = target.lstat()
    _assert_binding_status(before_path, "before-path binding")
    descriptor = os.open(target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before_fd = os.fstat(descriptor)
        _assert_binding_status(before_fd, "before-fd binding")
        chunks: List[bytes] = []
        while True:
            chunk = os.read(descriptor, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
        _assert_binding_status(after_fd, "after-fd binding")
    finally:
        os.close(descriptor)
    after_path = target.lstat()
    _assert_binding_status(after_path, "after-path binding")
    if not (
        _fingerprint(before_path)
        == _fingerprint(before_fd)
        == _fingerprint(after_fd)
        == _fingerprint(after_path)
    ):
        raise ValidationError("binding changed during read: " + relative)
    raw = b"".join(chunks)
    if len(raw) != before_fd.st_size:
        raise ValidationError("short read: " + relative)
    if ancestors_before != _ancestor_snapshot(root, target):
        raise ValidationError("ancestor changed during read: " + relative)
    return raw


def _binding(
    ordinal: int,
    group: str,
    role: str,
    path: str,
    raw: bytes,
    semantic_digest: Optional[str] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "ordinal": ordinal,
        "group": group,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": raw.endswith(b"\n"),
    }
    if semantic_digest is not None:
        row["record_sha256"] = semantic_digest
    return row


def _predecessor_state(
    root: Path,
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    bindings: List[Dict[str, Any]] = []
    records: Dict[str, Dict[str, Any]] = {}
    for ordinal, spec in enumerate(PREDECESSOR_SPECS):
        group, role, path, expected_bytes, expected_sha, expected_record = spec
        raw = _stable_read(root, path)
        if len(raw) != expected_bytes or _sha256(raw) != expected_sha:
            raise ValidationError("predecessor exact-byte mismatch: " + path)
        if role == "machine":
            parsed = _parse_json(raw, "predecessor " + path)
            records[path] = parsed
            if expected_record is not None:
                if parsed.get("record_sha256") != expected_record:
                    raise ValidationError("predecessor semantic digest field mismatch")
                if _semantic_record_sha256(parsed) != expected_record:
                    raise ValidationError("predecessor semantic digest recomputation failed")
        bindings.append(
            _binding(ordinal, group, role, path, raw, expected_record)
        )
    return bindings, records


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for ordinal, (role, path) in enumerate(
        (("human", HUMAN_PATH), ("validator", VALIDATOR_PATH), ("test", TEST_PATH))
    ):
        rows.append(
            _binding(ordinal, "CURRENT_PACKAGE", role, path, _stable_read(root, path))
        )
    return rows


def _validate_predecessor_semantics(
    records: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    prereg_path = "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
    f104_path = (
        "research/fixtures/"
        "manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json"
    )
    if set(records) != {prereg_path, f104_path}:
        raise ValidationError("machine predecessor roster mismatch")

    prereg = records[prereg_path]
    ethics = prereg.get("ethics_release_and_review_plan")
    if (
        prereg.get("schema_version") != "manuscript-v3-execution-preregistration-v1"
        or prereg.get("state") != GLOBAL_STATE
        or type(ethics) is not dict
    ):
        raise ValidationError("execution preregistration state changed")
    expected_nulls = {
        "data_license_compliance_plan": None,
        "code_model_and_artifact_release_plan": None,
        "submission_anonymization_plan": None,
        "physionet_clinical_governance_and_interpretation_plan": None,
        "retail_privacy_duplicate_exposure_and_membership_inference_plan": None,
        "proof_and_code_audit_plan": None,
        "proof_and_code_audit_artifact_path": None,
        "methods_and_statistics_audit_plan": None,
        "clean_room_reproduction_audit_plan": None,
        "review_assignments_are_scientific_checks_not_production_authority": True,
    }
    _strict_equal(ethics, expected_nulls, "execution preregistration audit fields")

    f104 = records[f104_path]
    transition = f104.get("count_transition")
    sweep = f104.get("comprehensive_field_sweep")
    effects = f104.get("project_effects_and_nonclaims")
    if (
        f104.get("state")
        != "F104_MATCHED_TOTAL_COMPUTE_FORMULA_FROZEN_RESOURCE_VALUES_NULL"
        or f104.get("global_state") != GLOBAL_STATE
        or f104.get("control_predicate")
        != "MATCHED_TOTAL_COMPUTE_FORMULA_F104_FROZEN_PREOUTCOME"
        or type(transition) is not dict
        or type(sweep) is not dict
        or type(effects) is not dict
    ):
        raise ValidationError("accepted F104 predecessor state changed")
    if transition.get("after") != {
        "post_execution_closed": 0,
        "post_execution_open": 6,
        "pre_execution_closed": 21,
        "pre_execution_open": 145,
        "total_closed": 21,
        "total_open": 151,
    }:
        raise ValidationError("accepted F104 count baseline changed")
    if tuple(sweep.get("closed_after_ids", ())) != CLOSED_PRE_AFTER_F104:
        raise ValidationError("accepted F104 closed PRE roster changed")
    if tuple(sweep.get("open_after_ids", ())) != OPEN_PRE_AFTER_F104:
        raise ValidationError("accepted F104 open PRE roster changed")
    if tuple(sweep.get("all_post_execution_fields_remain_open", ())) != POST_FIELDS:
        raise ValidationError("accepted F104 POST roster changed")
    closures = f104.get("field_closures")
    if (
        type(closures) is not list
        or len(closures) != 1
        or type(closures[0]) is not dict
        or closures[0].get("field_id") != "F104"
        or transition.get("blockers_open_after") != 12
        or transition.get("blockers_closed") != 0
        or transition.get("formal_tests_closed") != 0
        or transition.get("results_filled") != 0
        or effects.get("tracker_or_evidence_ledger_edited") is not False
        or effects.get("runtime_or_operational_receipt_created") is not False
        or effects.get("network_contact_repository_license_or_data_access_performed")
        is not False
        or effects.get("entropy_training_scientific_or_production_execution_performed")
        is not False
        or effects.get("result_or_claim_promoted") is not False
    ):
        raise ValidationError("accepted F104 nonclosure boundary changed")
    return {
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


def _field_closures() -> List[Dict[str, Any]]:
    return [
        {
            "field_id": plan["field_id"],
            "json_pointer": plan["json_pointer"],
            "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_AUDIT_PLAN_FREEZE",
            "value": dict(plan),
        }
        for plan in PLAN_VALUES
    ]


def expected_record(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    predecessor_bindings, records = _predecessor_state(root)
    predecessor_receipt = _validate_predecessor_semantics(records)
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "reported_date": REPORTED_DATE,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": PACKAGE_KIND,
        "control_predicate": CONTROL_PREDICATE,
        "authority_provenance": {
            "normalized_internal_coordinator_instruction": COORDINATOR_INSTRUCTION,
            "normalized_internal_coordinator_instruction_sha256": _sha256(
                COORDINATOR_INSTRUCTION.encode("utf-8")
            ),
            "bounded_offline_local_package_construction_authorized": True,
            "external_identity_time_or_appointment_authenticated": False,
            "network_contact_data_or_repository_access_authorized": False,
            "entropy_subprocess_runtime_clean_room_or_science_authorized": False,
            "result_inspection_claim_promotion_or_submission_authorized": False,
            "tracker_or_evidence_ledger_edit_authorized_by_this_package": False,
        },
        "package_file_roster": list(PACKAGE_ROSTER),
        "package_bindings_excluding_machine_self": _package_bindings(root),
        "machine_self_binding": {
            "path": MACHINE_PATH,
            "semantic_self_digest_field": "record_sha256",
            "raw_self_hash_embedded": False,
        },
        "predecessor_bindings": predecessor_bindings,
        "predecessor_group_counts": dict(PREDECESSOR_GROUP_COUNTS),
        "accepted_post_f104_baseline": predecessor_receipt,
        "anti_drift_scope_review": {
            "one_integrated_b11_package": True,
            "shared_governance_and_completion_contract": True,
            "named_field_ids": list(CLOSED_POST_AFTER),
            "tracked_field_count_reduction": 3,
            "zero_delta_precursor_layer_created": False,
            "F169_or_B11_promoted": False,
            "additional_b11_artifact_requires_new_scope_review": True,
        },
        "shared_owner_role_and_process": {
            "responsible_owner_role": OWNER_ROLE,
            "proof_code_and_methods_auditor_role": AUDITOR_ROLE,
            "clean_room_executor_role": CLEAN_ROOM_ROLE,
            "separation_rules": list(SEPARATION_RULES),
            "required_future_assignment_admission_fields": list(
                ASSIGNMENT_ADMISSION_FIELDS
            ),
            "actual_person_institution_account_or_external_identity": None,
            "actual_assignment_or_appointment_receipt": None,
            "actual_subject_matter_competence_declaration": None,
            "actual_conflict_of_interest_disclosure": None,
            "actual_owner_c_coi_review_and_acceptance": None,
            "actual_audit_input_instance": None,
            "actual_report_or_artifact": None,
            "actual_clean_room_run": None,
        },
        "severity_and_disposition_model": dict(SEVERITY_MODEL),
        "field_closures": _field_closures(),
        "shared_completion_rule": {
            "rule_id": "SHARED_FAIL_CLOSED_AUDIT_COMPLETION_RULE_V1",
            "completion_evidence_key_order": list(COMPLETION_EVIDENCE_KEYS),
            "missing_or_incomplete_evidence_disposition": "INCOMPLETE_FAIL_CLOSED",
            "substantive_defect_disposition": "FAIL",
            "known_substantive_defect_precedes_missing_readiness": True,
            "known_fail_conditions": [
                "KNOWN_AUTHORSHIP_OR_IMPLEMENTATION_OVERLAP",
                "KNOWN_INPUT_OR_SUBJECT_MUTATION",
                "FORBIDDEN_RERUN_OR_REDESIGN",
                "ANY_P0_FINDING",
                "ANY_P1_FINDING",
                "ANY_UNBOUNDED_OR_UNDISCLOSED_P2_FINDING",
            ],
            "incomplete_only_when_no_known_defect_conditions": [
                "MISSING_OR_UNVERIFIED_ROLE_SEPARATION",
                "MISSING_OR_UNVERIFIED_INPUT_OR_SUBJECT_CUSTODY",
                "MISSING_OR_UNVERIFIED_SUBJECT_MATTER_COMPETENCE",
                "MISSING_OR_UNVERIFIED_CONFLICT_OF_INTEREST_DISCLOSURE_OR_OWNER_C_ACCEPTANCE",
                "MISSING_OR_UNVERIFIED_OTHER_READINESS_EVIDENCE",
            ],
            "pass_requires_actual_terminal_report": True,
            "current_package_is_a_completed_audit": False,
        },
        "count_transition": {
            "before": {
                "pre_execution_open": 145,
                "pre_execution_closed": 21,
                "post_execution_open": 6,
                "post_execution_closed": 0,
                "total_open": 151,
                "total_closed": 21,
            },
            "closed_by_package": {
                "field_ids": list(CLOSED_POST_AFTER),
                "pre_execution": 0,
                "post_execution": 3,
                "total": 3,
            },
            "after": {
                "pre_execution_open": 145,
                "pre_execution_closed": 21,
                "post_execution_open": 3,
                "post_execution_closed": 3,
                "total_open": 148,
                "total_closed": 24,
            },
            "blockers_open_after": 12,
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "results_filled": 0,
        },
        "comprehensive_field_sweep": {
            "total_pre_execution_fields": 166,
            "total_post_execution_fields": 6,
            "closed_pre_ids": list(CLOSED_PRE_AFTER_F104),
            "open_pre_ids": list(OPEN_PRE_AFTER_F104),
            "closed_post_ids": list(CLOSED_POST_AFTER),
            "open_post_ids": list(OPEN_POST_AFTER),
            "eligible_now_ids": list(CLOSED_POST_AFTER),
            "additional_eligible_field_count": 0,
            "F169_value": None,
        },
        "current_execution_boundary": {
            "actual_auditor_identity_or_appointment_present": False,
            "actual_subject_matter_competence_declaration_present": False,
            "actual_conflict_of_interest_disclosure_or_acceptance_present": False,
            "actual_audit_input_instance_present": False,
            "actual_proof_code_report_or_artifact_path_present": False,
            "actual_methods_statistics_report_present": False,
            "actual_clean_room_input_or_run_present": False,
            "result_or_metric_value_present": False,
            "all_three_plans_have_audit_executed_false": True,
        },
        "project_effects_and_nonclaims": {
            "only_fields_closed": list(CLOSED_POST_AFTER),
            "F164_F165_F169_remain_open": True,
            "F169_remains_open_and_null": True,
            "B11_remains_open": True,
            "all_12_blockers_remain_open": True,
            "formal_test_28_status": "OPEN",
            "formal_test_29_status": "OPEN",
            "formal_test_30_status": "PENDING",
            "R1_R2_R3_R4_remain_unexecuted": True,
            "network_contact_repository_license_or_data_access_performed": False,
            "entropy_generated_or_consumed": False,
            "subprocess_or_environment_build_performed": False,
            "runtime_or_operational_receipt_created": False,
            "audit_or_clean_room_execution_performed": False,
            "auditor_or_clean_room_executor_selected_or_admitted": False,
            "competence_declaration_or_coi_disclosure_acceptance_receipt_created": False,
            "training_scientific_or_production_execution_performed": False,
            "result_or_claim_promoted": False,
            "submission_or_release_performed": False,
            "tracker_or_evidence_ledger_edited": False,
        },
        "qualification_boundary": {
            "read_only_stable_no_follow_validator": True,
            "canonical_duplicate_free_ascii_json_required": True,
            "hostile_mutations_use_disposable_test_replicas_only": True,
            "synthetic_completion_evidence_only": True,
            "independent_review_required_before_registration": True,
            "self_validation_is_independent_acceptance": False,
        },
        "evidence_ready_registration": {
            "proposed_text": EVIDENCE_READY_REGISTRATION,
            "permitted_field_delta": list(CLOSED_POST_AFTER),
            "registration_performed_by_this_package": False,
        },
        "publication_boundary": {
            "internal_evidence_only": True,
            "anonymous_or_public_inclusion_permitted": False,
            "absolute_user_path_credential_person_data_or_result_present": False,
            "publication_safe_derivative_and_fresh_anonymity_review_required": True,
        },
    }
    record["record_sha256"] = record_sha256(record)
    return record


def validate(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    machine_raw = _stable_read(root, MACHINE_PATH)
    machine = _parse_json(machine_raw, "current machine record")
    if machine_raw != canonical_machine_bytes(machine):
        raise ValidationError("current machine record is not canonical")
    embedded_digest = machine.get("record_sha256")
    if type(embedded_digest) is not str or len(embedded_digest) != 64:
        raise ValidationError("current machine semantic digest is absent")
    if record_sha256(machine) != embedded_digest:
        raise ValidationError("current machine semantic digest mismatch")
    expected = expected_record(root)
    _strict_equal(machine, expected, "current machine record")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": embedded_digest,
        "control_predicate": CONTROL_PREDICATE,
        "fields_closed": list(CLOSED_POST_AFTER),
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


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=True, sort_keys=True))
