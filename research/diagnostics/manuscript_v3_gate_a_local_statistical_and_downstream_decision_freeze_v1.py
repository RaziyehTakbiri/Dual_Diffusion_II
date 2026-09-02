"""Read-only validator and pure helpers for the Gate-A local decision freeze."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = (
    "heterodiff-manuscript-v3-gate-a-local-statistical-and-"
    "downstream-decision-freeze-v1"
)
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISIONS_FROZEN"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
CONTROL_PREDICATE = "R1_R2_DOWNSTREAM_FAILURE_BEHAVIOR_FROZEN"
REPORTED_DATE = "2026-08-30"
MAX_COMPONENT_BITS = 4096

HUMAN_PATH = "PROJECT_GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISION_FREEZE.md"
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_gate_a_local_statistical_and_"
    "downstream_decision_freeze_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_gate_a_local_statistical_and_"
    "downstream_decision_freeze_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_gate_a_local_statistical_and_"
    "downstream_decision_freeze_v1.py"
)

AUTHORITY_TEXT = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)
TRACKER_AUTHORITY_TEXT = (
    "Sounds great. Go ahead and finish them in parallel. Mark all the completed "
    "tasks as the end."
)

EXPECTED_PREDECESSORS = [
    (
        "execution_preregistration_human",
        "manuscript_v3/execution_preregistration.md",
        "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
    ),
    (
        "execution_preregistration_machine",
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
    ),
    (
        "preexecution_closure_human",
        "manuscript_v3/execution_preregistration_preexecution_closure_v2.md",
        "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d",
    ),
    (
        "preexecution_closure_machine",
        "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
        "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
    ),
    (
        "power_route_human",
        "PROJECT_REAL_DOMAIN_POWER_ALLOCATION_ROUTE.md",
        "a8edf99303e30b6ae6ea9912dce6350fadc9e07361fcd25743c03446a2bb0139",
    ),
    (
        "power_route_machine",
        "research/fixtures/manuscript_v3_real_domain_power_allocation_route_v1.json",
        "536493388d23aac2cc3aaf6f9bdc34a12fba77103e9546cbf110c1c8223dfd28",
    ),
    (
        "power_route_validator",
        "research/diagnostics/manuscript_v3_real_domain_power_allocation_route_v1.py",
        "be5bcf6cde26d1c4eff044f6fad4705c1e87c850c77f38b2a4f7ef670a03b129",
    ),
    (
        "power_route_test",
        "tests/unit/test_manuscript_v3_real_domain_power_allocation_route_v1.py",
        "3c0846ecd924f4e39f7a98414755fdc06c2c1e5d60491879fa4190f5730b9926",
    ),
    (
        "pilot_strategy_human",
        "PROJECT_PILOT_VARIANCE_POWER_STRATEGY_DRAFT.md",
        "def13998bba651bf3737288079e8a79e1b7221a8aab680cf67ef248f785ed1ba",
    ),
    (
        "pilot_strategy_machine",
        "research/fixtures/manuscript_v3_pilot_variance_power_strategy_draft_v1.json",
        "4a01541ff60be7b0d5ef875aa7af0d646d24754d4ffb3027fb5eb65f43b7ee58",
    ),
    (
        "pilot_strategy_validator",
        "research/diagnostics/manuscript_v3_pilot_variance_power_strategy_draft_v1.py",
        "d55c6cc29bb5905623bf81bc467a35da96a67f9a0c9f7dc767e2eb646fe76c2a",
    ),
    (
        "pilot_strategy_test",
        "tests/unit/test_manuscript_v3_pilot_variance_power_strategy_draft_v1.py",
        "15b480991c9363d1050952015635f480a75c770ed517a42d5ae9a9f94b106229",
    ),
]

R1_PHASES = (
    "R1_RANK",
    "R1_EXACT",
    "R1_PRIMARY",
    "R1_METRICS",
    "R1_CONTROLS",
)
OUTCOMES = ("PASS", "FAIL", "HOLD", "INFRA_ABORT", "PROTOCOL_INVALID")
DOMAINS = ("R3-PHYS", "R4-RETAIL")


class ValidationError(ValueError):
    """Raised when exact custody, schema, or semantics fail."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _payload_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _payload_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _payload_bytes(payload))


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for index, (item, wanted) in enumerate(zip(actual, expected)):
            _strict_equal(item, wanted, label + "[" + str(index) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def _safe_path(root: Path, relative: str) -> Path:
    if type(relative) is not str or not relative or relative.startswith("/"):
        raise ValidationError("relative path invalid")
    if ".." in Path(relative).parts:
        raise ValidationError("parent traversal forbidden")
    resolved_root = root.resolve()
    target = root.joinpath(relative)
    if target.resolve(strict=False) != resolved_root.joinpath(relative):
        raise ValidationError("path resolution mismatch")
    return target


def _fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode),
        status.st_uid,
        status.st_gid,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _stable_read(root: Path, relative: str) -> bytes:
    target = _safe_path(root, relative)
    cursor = root.resolve()
    for part in Path(relative).parts[:-1]:
        cursor = cursor.joinpath(part)
        status = os.lstat(cursor)
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise ValidationError("unsafe ancestor")
    before_path = os.lstat(target)
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != 0o644
        or before_path.st_nlink != 1
    ):
        raise ValidationError("leaf custody invalid")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(target, flags)
    try:
        before_fd = os.fstat(descriptor)
        chunks: List[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = os.lstat(target)
    if not (
        _fingerprint(before_path)
        == _fingerprint(before_fd)
        == _fingerprint(after_fd)
        == _fingerprint(after_path)
    ):
        raise ValidationError("leaf changed during read")
    raw = b"".join(chunks)
    if len(raw) != before_fd.st_size:
        raise ValidationError("read size mismatch")
    return raw


def _exact_probability(value: Any, label: str) -> Fraction:
    if type(value) is int:
        result = Fraction(value, 1)
    elif type(value) is Fraction:
        result = value
    else:
        raise ValidationError(label + " must be exact int or Fraction")
    if (
        result.numerator.bit_length() > MAX_COMPONENT_BITS
        or result.denominator.bit_length() > MAX_COMPONENT_BITS
    ):
        raise ValidationError(label + " exceeds component bound")
    if result < 0 or result > 1:
        raise ValidationError(label + " outside [0,1]")
    return result


def _fraction_record(value: Fraction) -> Dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def holm_two_domain(pvalues: Any) -> Dict[str, Any]:
    """Apply the exact frozen two-hypothesis one-sided Holm rule."""

    if type(pvalues) is not dict or set(pvalues) != set(DOMAINS):
        raise ValidationError("pvalue mapping must contain exact domain roster")
    checked = {
        domain: _exact_probability(pvalues[domain], domain + " pvalue")
        for domain in DOMAINS
    }
    ordered = sorted(
        DOMAINS, key=lambda domain: (checked[domain], DOMAINS.index(domain))
    )
    first, second = ordered
    first_rejected = checked[first] <= Fraction(1, 40)
    second_rejected = first_rejected and checked[second] <= Fraction(1, 20)
    rejected = {first: first_rejected, second: second_rejected}
    return {
        "schema_version": "heterodiff-two-domain-holm-decision-v1",
        "ordered_domains": ordered,
        "ordered_pvalues": [_fraction_record(checked[domain]) for domain in ordered],
        "thresholds": [
            {"numerator": 1, "denominator": 40},
            {"numerator": 1, "denominator": 20},
        ],
        "rejected": {domain: rejected[domain] for domain in DOMAINS},
        "both_domains_rejected": all(rejected.values()),
        "scientific_result": False,
    }


def downstream_state(r1_outcomes: Any, r2_outcome: Any = None) -> Dict[str, Any]:
    """Return the frozen eligibility/terminal projection for a supplied prefix."""

    if type(r1_outcomes) is not list or len(r1_outcomes) > len(R1_PHASES):
        raise ValidationError("R1 outcomes must be a bounded list")
    checked: List[str] = []
    terminal_index: Optional[int] = None
    for index, outcome in enumerate(r1_outcomes):
        if type(outcome) is not str or outcome not in OUTCOMES:
            raise ValidationError("R1 outcome invalid")
        if terminal_index is not None:
            raise ValidationError("outcome supplied after terminal R1 branch")
        checked.append(outcome)
        if outcome != "PASS":
            terminal_index = index
    if r2_outcome is not None:
        if type(r2_outcome) is not str or r2_outcome not in OUTCOMES:
            raise ValidationError("R2 outcome invalid")
        if len(checked) != len(R1_PHASES) or any(item != "PASS" for item in checked):
            raise ValidationError("R2 outcome supplied before complete R1 PASS")

    if terminal_index is not None:
        outcome = checked[terminal_index]
        later = list(R1_PHASES[terminal_index + 1 :])
        return {
            "state": "R1_" + outcome,
            "r1_completed_phases": list(R1_PHASES[: terminal_index + 1]),
            "next_eligible": None,
            "r2_eligible": False,
            "r2_attempted": False,
            "real_domains_eligible": False,
            "not_applicable": later + ["R2-HYBRID", "R3-PHYS", "R4-RETAIL"],
            "retry_permitted": False,
            "scientific_result": False,
        }

    if len(checked) < len(R1_PHASES):
        return {
            "state": "R1_IN_PROGRESS",
            "r1_completed_phases": list(R1_PHASES[: len(checked)]),
            "next_eligible": R1_PHASES[len(checked)],
            "r2_eligible": False,
            "r2_attempted": False,
            "real_domains_eligible": False,
            "not_applicable": [],
            "retry_permitted": False,
            "scientific_result": False,
        }

    if r2_outcome is None:
        return {
            "state": "R1_PASS_R2_ELIGIBLE",
            "r1_completed_phases": list(R1_PHASES),
            "next_eligible": "R2-HYBRID",
            "r2_eligible": True,
            "r2_attempted": False,
            "real_domains_eligible": False,
            "not_applicable": [],
            "retry_permitted": False,
            "scientific_result": False,
        }

    if r2_outcome == "PASS":
        return {
            "state": "R2_PASS_REAL_DOMAINS_ELIGIBLE",
            "r1_completed_phases": list(R1_PHASES),
            "next_eligible": "R3-PHYS_AND_R4-RETAIL_SUBJECT_TO_ALL_OTHER_GATES",
            "r2_eligible": False,
            "r2_attempted": True,
            "real_domains_eligible": True,
            "not_applicable": [],
            "retry_permitted": False,
            "scientific_result": False,
        }

    return {
        "state": "R2_" + r2_outcome,
        "r1_completed_phases": list(R1_PHASES),
        "next_eligible": None,
        "r2_eligible": False,
        "r2_attempted": True,
        "real_domains_eligible": False,
        "not_applicable": ["R3-PHYS", "R4-RETAIL"],
        "retry_permitted": False,
        "scientific_result": False,
    }


def _binding(
    root: Path, role: str, path: str, expected_sha: Optional[str] = None
) -> Dict[str, Any]:
    raw = _stable_read(root, path)
    digest = _sha256(raw)
    if expected_sha is not None and digest != expected_sha:
        raise ValidationError(role + " predecessor digest mismatch")
    return {"role": role, "path": path, "raw_sha256": digest, "bytes": len(raw)}


def expected_record(root: Optional[Path] = None) -> Dict[str, Any]:
    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    predecessors = [
        _binding(workspace, role, path, digest)
        for role, path, digest in EXPECTED_PREDECESSORS
    ]
    package = [
        _binding(workspace, "human", HUMAN_PATH),
        _binding(workspace, "validator", VALIDATOR_PATH),
        _binding(workspace, "test", TEST_PATH),
    ]
    field_closures = [
        {
            "field_id": "F107",
            "json_pointer": "/metric_and_estimand_plan/aggregation_unit",
            "value": "NATURAL_GROUP_WEIGHTED_PAIRED_MEAN_OF_PRIMARY_SCORE_DIRECT_MINUS_PRIMARY_SCORE_GUIDE",
            "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_FREEZE",
        },
        {
            "field_id": "F113",
            "json_pointer": "/metric_and_estimand_plan/multiplicity_rule",
            "value": "TWO_DOMAIN_ONE_SIDED_HOLM_STEP_DOWN_FWER_1_OVER_20",
            "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_FREEZE",
        },
        {
            "field_id": "F128",
            "json_pointer": "/power_and_seed_plan/familywise_alpha",
            "value": {"numerator": 1, "denominator": 20, "json_number": "0.05"},
            "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_FREEZE",
        },
        {
            "field_id": "F129",
            "json_pointer": "/power_and_seed_plan/target_power",
            "value": {"numerator": 9, "denominator": 10, "json_number": "0.9"},
            "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_FREEZE",
        },
        {
            "field_id": "F148",
            "json_pointer": "/stopping_failure_and_exclusion_plan/infrastructure_rerun_predicate",
            "value": "NEVER_TRUE_NO_INFRASTRUCTURE_RERUN",
            "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_FREEZE",
        },
    ]
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "reported_date": REPORTED_DATE,
        "package_kind": "ADDITIVE_PREOUTCOME_FIELD_AND_PROJECT_CONTROL_CLOSURE",
        "authority_provenance": {
            "normalized_visible_text": AUTHORITY_TEXT,
            "normalized_visible_text_sha256": _sha256(AUTHORITY_TEXT.encode("utf-8")),
            "normalized_tracker_authority_text": TRACKER_AUTHORITY_TEXT,
            "normalized_tracker_authority_text_sha256": _sha256(
                TRACKER_AUTHORITY_TEXT.encode("utf-8")
            ),
            "raw_transport_or_trailing_html_space_bound": False,
            "local_autonomous_gate_a_work_authorized": True,
            "tracker_marking_after_independent_validation_authorized_by_standing_instruction": True,
            "external_contact_data_entropy_runtime_training_science_or_submission_authorized": False,
            "agent_selected_paths_schema_statistics_and_failure_rules": True,
        },
        "field_closures": field_closures,
        "count_transition": {
            "before": {
                "pre_execution_open": 166,
                "post_execution_open": 6,
                "total_open": 172,
            },
            "closed_by_this_package": {
                "pre_execution": 5,
                "post_execution": 0,
                "total": 5,
                "field_ids": ["F107", "F113", "F128", "F129", "F148"],
            },
            "after": {
                "pre_execution_open": 161,
                "post_execution_open": 6,
                "total_open": 167,
            },
            "blockers_open_after": 12,
            "formal_tests_closed": 0,
            "results_filled": 0,
        },
        "workstream_transition": {
            "theory_statistics": {
                "open_before": 54,
                "closed_before": 0,
                "open_after": 49,
                "closed_after": 5,
            },
            "method_runtime_compute": {"open_after": 65, "closed_after": 0},
            "data_governance_reproduction": {"open_after": 52, "closed_after": 0},
            "final_sealed_freeze": {"open_after": 1, "closed_after": 0},
        },
        "holm_contract": {
            "family": list(DOMAINS),
            "hypothesis": "H_D_THETA_LE_DELTA0_VS_A_D_THETA_GT_DELTA0",
            "familywise_alpha": {"numerator": 1, "denominator": 20},
            "ordered_thresholds": [
                {"numerator": 1, "denominator": 40},
                {"numerator": 1, "denominator": 20},
            ],
            "exact_tie_priority": list(DOMAINS),
            "closed_inequality": True,
            "second_rejection_requires_first_rejection": True,
            "both_domains_required_for_C20": True,
            "F112_confidence_method_closed": False,
        },
        "power_policy": {
            "F129_semantics": "JOINT_PROBABILITY_BOTH_R3_AND_R4_PASS",
            "marginal_power_called_joint_power_permitted": False,
            "candidate_per_domain_failure_upper_bound": {
                "numerator": 1,
                "denominator": 20,
            },
            "union_bound_joint_lower_bound": {"numerator": 9, "denominator": 10},
            "domain_independence_assumed": False,
            "real_power_design_complete": False,
        },
        "downstream_contract": {
            "r1_phase_order": list(R1_PHASES),
            "outcome_domain": list(OUTCOMES),
            "later_r1_requires_prior_pass": True,
            "r2_requires_r1_pass": True,
            "real_domains_require_r2_pass": True,
            "any_nonpass_makes_all_downstream_slots_not_applicable": True,
            "invalid_or_missing_receipt_is_protocol_invalid_terminal": True,
            "infrastructure_rerun_predicate": "NEVER_TRUE_NO_INFRASTRUCTURE_RERUN",
            "retry_resume_replacement_topup_threshold_seed_config_or_route_change_permitted": False,
            "failed_and_completed_receipts_retained": True,
        },
        "project_control_effects": {
            "project_control_predicate": CONTROL_PREDICATE,
            "value_after_validation": True,
            "gate_a_downstream_behavior_checkbox_may_close_after_independent_review": True,
            "unresolved_fields_closed": 5,
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "results_filled": 0,
            "tracker_edit_performed_by_package": False,
        },
        "scope_and_nonclaims": {
            "primary_metric_selected": False,
            "confidence_method_selected": False,
            "effect_margin_selected": False,
            "pilot_observed": False,
            "real_seed_count_or_registry_selected": False,
            "compute_reserved": False,
            "domain_admitted": False,
            "data_or_test_outcome_accessed": False,
            "scientific_execution_performed": False,
            "claim_promoted": False,
            "all_12_blockers_remain_open": True,
        },
        "publication_boundary": {
            "internal_evidence_only": True,
            "anonymous_or_public_inclusion_permitted": False,
            "publication_safe_derivative_and_fresh_anonymity_audit_required": True,
            "absolute_user_path_credentials_person_or_dataset_rows_present": False,
        },
        "predecessor_bindings": predecessors,
        "package_bindings": package,
        "record_sha256": "",
    }
    record["record_sha256"] = record_sha256(record)
    return record


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    raw = _stable_read(workspace, MACHINE_PATH)
    record = json.loads(raw.decode("ascii"))
    if type(record) is not dict:
        raise ValidationError("machine record must be object")
    if canonical_machine_bytes(record) != raw:
        raise ValidationError("machine record is not canonical")
    if record.get("record_sha256") != record_sha256(record):
        raise ValidationError("machine self digest invalid")
    _strict_equal(record, expected_record(workspace), "record")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "control_predicate": CONTROL_PREDICATE,
        "control_predicate_value": True,
        "fields_closed": ["F107", "F113", "F128", "F129", "F148"],
        "pre_execution_open_after": 161,
        "post_execution_open_after": 6,
        "total_open_after": 167,
        "blockers_open_after": 12,
        "scientific_execution": False,
        "validation": "PASS",
    }


__all__ = [
    "ValidationError",
    "canonical_machine_bytes",
    "downstream_state",
    "expected_record",
    "holm_two_domain",
    "record_sha256",
    "validate",
]
