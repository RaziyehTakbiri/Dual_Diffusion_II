from __future__ import annotations

from collections import OrderedDict
from fractions import Fraction
import json
import os
from pathlib import Path
import shutil
import stat
import types
from typing import Any, Callable, Dict

import pytest


WORKSPACE = Path(__file__).resolve().parents[2]
SOURCE = (
    WORKSPACE / "research/diagnostics/manuscript_v3_gate_a_local_statistical_and_"
    "downstream_decision_freeze_v1.py"
)
HUMAN = WORKSPACE / "PROJECT_GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISION_FREEZE.md"
R1_PHASES = (
    "R1_RANK",
    "R1_EXACT",
    "R1_PRIMARY",
    "R1_METRICS",
    "R1_CONTROLS",
)
NONPASS_OUTCOMES = ("FAIL", "HOLD", "INFRA_ABORT", "PROTOCOL_INVALID")


def _load_validator() -> types.ModuleType:
    module = types.ModuleType("gate_a_local_decision_freeze_validator")
    module.__file__ = str(SOURCE)
    code = compile(SOURCE.read_bytes(), str(SOURCE), "exec")
    exec(code, module.__dict__)
    return module


@pytest.fixture(scope="module")
def validator() -> types.ModuleType:
    return _load_validator()


@pytest.mark.parametrize(
    "pvalues,ordered,rejected,both",
    [
        (
            {"R3-PHYS": Fraction(1, 40), "R4-RETAIL": Fraction(1, 20)},
            ["R3-PHYS", "R4-RETAIL"],
            {"R3-PHYS": True, "R4-RETAIL": True},
            True,
        ),
        (
            {"R3-PHYS": Fraction(1, 20), "R4-RETAIL": Fraction(1, 40)},
            ["R4-RETAIL", "R3-PHYS"],
            {"R3-PHYS": True, "R4-RETAIL": True},
            True,
        ),
        (
            {"R3-PHYS": Fraction(1, 40), "R4-RETAIL": Fraction(1, 40)},
            ["R3-PHYS", "R4-RETAIL"],
            {"R3-PHYS": True, "R4-RETAIL": True},
            True,
        ),
        (
            {"R3-PHYS": Fraction(1, 39), "R4-RETAIL": Fraction(1, 20)},
            ["R3-PHYS", "R4-RETAIL"],
            {"R3-PHYS": False, "R4-RETAIL": False},
            False,
        ),
        (
            {"R3-PHYS": Fraction(1, 100), "R4-RETAIL": Fraction(1, 19)},
            ["R3-PHYS", "R4-RETAIL"],
            {"R3-PHYS": True, "R4-RETAIL": False},
            False,
        ),
        (
            {"R3-PHYS": 0, "R4-RETAIL": 1},
            ["R3-PHYS", "R4-RETAIL"],
            {"R3-PHYS": True, "R4-RETAIL": False},
            False,
        ),
    ],
)
def test_exact_holm_algebra(
    validator: types.ModuleType,
    pvalues: Dict[str, Any],
    ordered: list[str],
    rejected: Dict[str, bool],
    both: bool,
) -> None:
    original = dict(pvalues)
    result = validator.holm_two_domain(pvalues)
    assert result["schema_version"] == "heterodiff-two-domain-holm-decision-v1"
    assert result["ordered_domains"] == ordered
    assert result["ordered_pvalues"] == [
        {
            "numerator": Fraction(pvalues[domain]).numerator,
            "denominator": Fraction(pvalues[domain]).denominator,
        }
        for domain in ordered
    ]
    assert result["thresholds"] == [
        {"numerator": 1, "denominator": 40},
        {"numerator": 1, "denominator": 20},
    ]
    assert result["rejected"] == rejected
    assert result["both_domains_rejected"] is both
    assert result["scientific_result"] is False
    assert pvalues == original


@pytest.mark.parametrize(
    "pvalues,match",
    [
        (None, "exact domain roster"),
        ([], "exact domain roster"),
        ({}, "exact domain roster"),
        ({"R3-PHYS": 0}, "exact domain roster"),
        (
            {"R3-PHYS": 0, "R4-RETAIL": 0, "R5-OTHER": 0},
            "exact domain roster",
        ),
        ({"R3-PHYS": 0, "R5-OTHER": 0}, "exact domain roster"),
        (OrderedDict((("R3-PHYS", 0), ("R4-RETAIL", 0))), "exact domain roster"),
        ({"R3-PHYS": False, "R4-RETAIL": 0}, "exact int or Fraction"),
        ({"R3-PHYS": 0.0, "R4-RETAIL": 0}, "exact int or Fraction"),
        ({"R3-PHYS": "0", "R4-RETAIL": 0}, "exact int or Fraction"),
        ({"R3-PHYS": None, "R4-RETAIL": 0}, "exact int or Fraction"),
        ({"R3-PHYS": Fraction(-1, 100), "R4-RETAIL": 0}, "outside"),
        ({"R3-PHYS": Fraction(101, 100), "R4-RETAIL": 0}, "outside"),
        ({"R3-PHYS": 2, "R4-RETAIL": 0}, "outside"),
        (
            {"R3-PHYS": Fraction(1, 1 << 4097), "R4-RETAIL": 0},
            "component bound",
        ),
        ({"R3-PHYS": 1 << 4096, "R4-RETAIL": 0}, "component bound"),
    ],
)
def test_holm_refuses_invalid_roster_types_ranges_and_components(
    validator: types.ModuleType, pvalues: Any, match: str
) -> None:
    with pytest.raises(validator.ValidationError, match=match):
        validator.holm_two_domain(pvalues)


@pytest.mark.parametrize("prefix_length", range(len(R1_PHASES)))
def test_each_contiguous_r1_pass_prefix_has_only_the_next_phase_eligible(
    validator: types.ModuleType, prefix_length: int
) -> None:
    supplied = ["PASS"] * prefix_length
    result = validator.downstream_state(supplied)
    assert result == {
        "state": "R1_IN_PROGRESS",
        "r1_completed_phases": list(R1_PHASES[:prefix_length]),
        "next_eligible": R1_PHASES[prefix_length],
        "r2_eligible": False,
        "r2_attempted": False,
        "real_domains_eligible": False,
        "not_applicable": [],
        "retry_permitted": False,
        "scientific_result": False,
    }
    assert supplied == ["PASS"] * prefix_length


@pytest.mark.parametrize("phase_index", range(len(R1_PHASES)))
@pytest.mark.parametrize("outcome", NONPASS_OUTCOMES)
def test_every_nonpass_at_every_r1_phase_is_terminal(
    validator: types.ModuleType, phase_index: int, outcome: str
) -> None:
    supplied = ["PASS"] * phase_index + [outcome]
    result = validator.downstream_state(supplied)
    assert result == {
        "state": "R1_" + outcome,
        "r1_completed_phases": list(R1_PHASES[: phase_index + 1]),
        "next_eligible": None,
        "r2_eligible": False,
        "r2_attempted": False,
        "real_domains_eligible": False,
        "not_applicable": list(R1_PHASES[phase_index + 1 :])
        + ["R2-HYBRID", "R3-PHYS", "R4-RETAIL"],
        "retry_permitted": False,
        "scientific_result": False,
    }
    assert supplied == ["PASS"] * phase_index + [outcome]


def test_complete_r1_pass_makes_only_r2_eligible(validator: types.ModuleType) -> None:
    result = validator.downstream_state(["PASS"] * len(R1_PHASES))
    assert result == {
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


@pytest.mark.parametrize("outcome", ("PASS",) + NONPASS_OUTCOMES)
def test_every_r2_outcome_has_exact_frozen_downstream_state(
    validator: types.ModuleType, outcome: str
) -> None:
    result = validator.downstream_state(["PASS"] * len(R1_PHASES), outcome)
    common = {
        "r1_completed_phases": list(R1_PHASES),
        "r2_eligible": False,
        "r2_attempted": True,
        "retry_permitted": False,
        "scientific_result": False,
    }
    if outcome == "PASS":
        assert result == {
            "state": "R2_PASS_REAL_DOMAINS_ELIGIBLE",
            "next_eligible": "R3-PHYS_AND_R4-RETAIL_SUBJECT_TO_ALL_OTHER_GATES",
            "real_domains_eligible": True,
            "not_applicable": [],
            **common,
        }
    else:
        assert result == {
            "state": "R2_" + outcome,
            "next_eligible": None,
            "real_domains_eligible": False,
            "not_applicable": ["R3-PHYS", "R4-RETAIL"],
            **common,
        }


@pytest.mark.parametrize(
    "r1_outcomes,r2_outcome,match",
    [
        (None, None, "bounded list"),
        ((), None, "bounded list"),
        ({}, None, "bounded list"),
        (["PASS"] * 6, None, "bounded list"),
        ([True], None, "outcome invalid"),
        ([None], None, "outcome invalid"),
        (["pass"], None, "outcome invalid"),
        (["UNKNOWN"], None, "outcome invalid"),
        (["FAIL", "PASS"], None, "after terminal"),
        (["PASS", "HOLD", "PASS"], None, "after terminal"),
        (["PASS", "PROTOCOL_INVALID", "FAIL"], None, "after terminal"),
        ([], "PASS", "before complete R1 PASS"),
        (["PASS"] * 4, "PASS", "before complete R1 PASS"),
        (["PASS"] * 4 + ["FAIL"], "PASS", "before complete R1 PASS"),
        (["PASS"] * 5, True, "R2 outcome invalid"),
        (["PASS"] * 5, "UNKNOWN", "R2 outcome invalid"),
        (["PASS"] * 5, "", "R2 outcome invalid"),
    ],
)
def test_downstream_refuses_invalid_or_gapped_inputs(
    validator: types.ModuleType, r1_outcomes: Any, r2_outcome: Any, match: str
) -> None:
    with pytest.raises(validator.ValidationError, match=match):
        validator.downstream_state(r1_outcomes, r2_outcome)


def test_decision_helpers_are_pure_and_do_not_read_package_files(
    validator: types.ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden_read(*args: Any, **kwargs: Any) -> bytes:
        del args, kwargs
        raise AssertionError("pure decision helper attempted package I/O")

    monkeypatch.setattr(validator, "_stable_read", forbidden_read)
    monkeypatch.chdir(tmp_path)
    assert (
        validator.holm_two_domain(
            {"R3-PHYS": Fraction(1, 40), "R4-RETAIL": Fraction(1, 20)}
        )["both_domains_rejected"]
        is True
    )
    assert (
        validator.downstream_state(["PASS"] * 5, "PASS")["real_domains_eligible"]
        is True
    )
    assert list(tmp_path.iterdir()) == []


def test_expected_record_closes_only_five_fields_and_no_blocker(
    validator: types.ModuleType,
) -> None:
    record = validator.expected_record(WORKSPACE)
    closures = record["field_closures"]
    assert [item["field_id"] for item in closures] == [
        "F107",
        "F113",
        "F128",
        "F129",
        "F148",
    ]
    assert closures[0]["value"] == (
        "NATURAL_GROUP_WEIGHTED_PAIRED_MEAN_OF_PRIMARY_SCORE_DIRECT_MINUS_"
        "PRIMARY_SCORE_GUIDE"
    )
    assert closures[1]["value"] == (
        "TWO_DOMAIN_ONE_SIDED_HOLM_STEP_DOWN_FWER_1_OVER_20"
    )
    assert closures[2]["value"] == {
        "numerator": 1,
        "denominator": 20,
        "json_number": "0.05",
    }
    assert closures[3]["value"] == {
        "numerator": 9,
        "denominator": 10,
        "json_number": "0.9",
    }
    assert closures[4]["value"] == "NEVER_TRUE_NO_INFRASTRUCTURE_RERUN"
    assert record["count_transition"] == {
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
    }
    effects = record["project_control_effects"]
    assert effects["unresolved_fields_closed"] == 5
    assert effects["blockers_closed"] == 0
    assert effects["formal_tests_closed"] == 0
    assert effects["results_filled"] == 0
    assert effects["tracker_edit_performed_by_package"] is False


def test_nonselected_fields_and_scientific_nonclaims_remain_open(
    validator: types.ModuleType,
) -> None:
    record = validator.expected_record(WORKSPACE)
    assert record["holm_contract"]["F112_confidence_method_closed"] is False
    assert record["power_policy"]["real_power_design_complete"] is False
    assert record["power_policy"]["domain_independence_assumed"] is False
    assert (
        record["power_policy"]["marginal_power_called_joint_power_permitted"] is False
    )
    assert record["scope_and_nonclaims"] == {
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
    }
    authority = record["authority_provenance"]
    assert (
        authority[
            "external_contact_data_entropy_runtime_training_science_or_submission_authorized"
        ]
        is False
    )
    assert record["publication_boundary"]["internal_evidence_only"] is True
    assert (
        record["publication_boundary"]["anonymous_or_public_inclusion_permitted"]
        is False
    )


def test_expected_record_uses_only_exact_json_numbers(
    validator: types.ModuleType,
) -> None:
    record = validator.expected_record(WORKSPACE)

    def walk(value: Any) -> None:
        assert type(value) is not float
        if type(value) is dict:
            for item in value.values():
                walk(item)
        elif type(value) is list:
            for item in value:
                walk(item)

    walk(record)


def _copy_roster(validator: types.ModuleType, tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    relative_paths = [path for _, path, _ in validator.EXPECTED_PREDECESSORS]
    relative_paths += [
        validator.HUMAN_PATH,
        validator.VALIDATOR_PATH,
        validator.TEST_PATH,
    ]
    for relative in dict.fromkeys(relative_paths):
        source = WORKSPACE / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target, follow_symlinks=False)
        os.chmod(target, 0o644)
    machine = root / validator.MACHINE_PATH
    machine.parent.mkdir(parents=True, exist_ok=True)
    record = validator.expected_record(root)
    machine.write_bytes(validator.canonical_machine_bytes(record))
    os.chmod(machine, 0o644)
    return root


def _rewrite_machine(
    validator: types.ModuleType,
    root: Path,
    mutate: Callable[[Dict[str, Any]], None],
    *,
    refresh_digest: bool = True,
) -> None:
    path = root / validator.MACHINE_PATH
    record = json.loads(path.read_text("ascii"))
    mutate(record)
    if refresh_digest:
        record["record_sha256"] = validator.record_sha256(record)
    path.write_bytes(validator.canonical_machine_bytes(record))
    os.chmod(path, 0o644)


SEMANTIC_MUTATIONS = [
    pytest.param(
        lambda r: r["field_closures"][0].__setitem__("field_id", "F108"),
        id="field-roster",
    ),
    pytest.param(
        lambda r: r["field_closures"][0].__setitem__("value", "UNPAIRED_MEAN"),
        id="aggregation-value",
    ),
    pytest.param(
        lambda r: r["field_closures"][1].__setitem__("value", "NO_MULTIPLICITY"),
        id="multiplicity-value",
    ),
    pytest.param(
        lambda r: r["field_closures"][2]["value"].__setitem__("denominator", 10),
        id="alpha-rational",
    ),
    pytest.param(
        lambda r: r["field_closures"][2]["value"].__setitem__(
            "json_number", "0.0500001"
        ),
        id="alpha-json-projection",
    ),
    pytest.param(
        lambda r: r["field_closures"][3]["value"].__setitem__("numerator", 8),
        id="power-rational",
    ),
    pytest.param(
        lambda r: r["field_closures"][4].__setitem__("value", "RETRY_ONCE"),
        id="rerun-predicate",
    ),
    pytest.param(
        lambda r: r["field_closures"][4].__setitem__("status", "OPEN"),
        id="closure-status",
    ),
    pytest.param(
        lambda r: r["count_transition"]["closed_by_this_package"].__setitem__(
            "total", 4
        ),
        id="closed-count",
    ),
    pytest.param(
        lambda r: r["count_transition"]["after"].__setitem__("pre_execution_open", 160),
        id="after-pre-count",
    ),
    pytest.param(
        lambda r: r["count_transition"].__setitem__("blockers_open_after", 11),
        id="blocker-count",
    ),
    pytest.param(
        lambda r: r["count_transition"].__setitem__("formal_tests_closed", 1),
        id="formal-test-count",
    ),
    pytest.param(
        lambda r: r["count_transition"].__setitem__("results_filled", 1),
        id="results-count",
    ),
    pytest.param(
        lambda r: r["workstream_transition"]["theory_statistics"].__setitem__(
            "open_after", 48
        ),
        id="workstream-count",
    ),
    pytest.param(
        lambda r: r["holm_contract"].__setitem__("family", ["R3-PHYS", "R5-OTHER"]),
        id="holm-family",
    ),
    pytest.param(
        lambda r: r["holm_contract"]["ordered_thresholds"][0].__setitem__(
            "denominator", 20
        ),
        id="holm-first-threshold",
    ),
    pytest.param(
        lambda r: r["holm_contract"].__setitem__(
            "exact_tie_priority", ["R4-RETAIL", "R3-PHYS"]
        ),
        id="holm-tie-priority",
    ),
    pytest.param(
        lambda r: r["holm_contract"].__setitem__("closed_inequality", False),
        id="holm-equality",
    ),
    pytest.param(
        lambda r: r["holm_contract"].__setitem__(
            "second_rejection_requires_first_rejection", False
        ),
        id="holm-stepdown-gate",
    ),
    pytest.param(
        lambda r: r["holm_contract"].__setitem__("F112_confidence_method_closed", True),
        id="confidence-premature-closure",
    ),
    pytest.param(
        lambda r: r["power_policy"].__setitem__(
            "F129_semantics", "MARGINAL_POWER_EACH_DOMAIN"
        ),
        id="joint-power-semantics",
    ),
    pytest.param(
        lambda r: r["power_policy"].__setitem__(
            "marginal_power_called_joint_power_permitted", True
        ),
        id="marginal-called-joint",
    ),
    pytest.param(
        lambda r: r["power_policy"].__setitem__("domain_independence_assumed", True),
        id="independence-assumption",
    ),
    pytest.param(
        lambda r: r["power_policy"].__setitem__("real_power_design_complete", True),
        id="power-premature-completion",
    ),
    pytest.param(
        lambda r: r["downstream_contract"].__setitem__(
            "r1_phase_order", list(reversed(R1_PHASES))
        ),
        id="r1-order",
    ),
    pytest.param(
        lambda r: r["downstream_contract"].__setitem__(
            "later_r1_requires_prior_pass", False
        ),
        id="r1-gapped-eligibility",
    ),
    pytest.param(
        lambda r: r["downstream_contract"].__setitem__("r2_requires_r1_pass", False),
        id="r2-before-r1",
    ),
    pytest.param(
        lambda r: r["downstream_contract"].__setitem__(
            "real_domains_require_r2_pass", False
        ),
        id="domains-before-r2",
    ),
    pytest.param(
        lambda r: r["downstream_contract"].__setitem__(
            "any_nonpass_makes_all_downstream_slots_not_applicable", False
        ),
        id="nonpass-nonterminal",
    ),
    pytest.param(
        lambda r: r["downstream_contract"].__setitem__(
            "invalid_or_missing_receipt_is_protocol_invalid_terminal", False
        ),
        id="invalid-receipt-nonterminal",
    ),
    pytest.param(
        lambda r: r["downstream_contract"].__setitem__(
            "infrastructure_rerun_predicate", "RETRY_IF_NO_OUTPUT"
        ),
        id="infrastructure-retry",
    ),
    pytest.param(
        lambda r: r["downstream_contract"].__setitem__(
            "retry_resume_replacement_topup_threshold_seed_config_or_route_change_permitted",
            True,
        ),
        id="route-salvage",
    ),
    pytest.param(
        lambda r: r["project_control_effects"].__setitem__("blockers_closed", 1),
        id="project-blocker-closure",
    ),
    pytest.param(
        lambda r: r["project_control_effects"].__setitem__(
            "tracker_edit_performed_by_package", True
        ),
        id="tracker-edit-claim",
    ),
    pytest.param(
        lambda r: r["scope_and_nonclaims"].__setitem__("primary_metric_selected", True),
        id="primary-metric-nonclaim",
    ),
    pytest.param(
        lambda r: r["scope_and_nonclaims"].__setitem__("pilot_observed", True),
        id="pilot-nonclaim",
    ),
    pytest.param(
        lambda r: r["scope_and_nonclaims"].__setitem__(
            "data_or_test_outcome_accessed", True
        ),
        id="data-access-nonclaim",
    ),
    pytest.param(
        lambda r: r["scope_and_nonclaims"].__setitem__(
            "scientific_execution_performed", True
        ),
        id="science-nonclaim",
    ),
    pytest.param(
        lambda r: r["scope_and_nonclaims"].__setitem__(
            "all_12_blockers_remain_open", False
        ),
        id="all-blockers-open",
    ),
    pytest.param(
        lambda r: r["authority_provenance"].__setitem__(
            "external_contact_data_entropy_runtime_training_science_or_submission_authorized",
            True,
        ),
        id="authority-expansion",
    ),
    pytest.param(
        lambda r: r["publication_boundary"].__setitem__(
            "anonymous_or_public_inclusion_permitted", True
        ),
        id="publication-boundary",
    ),
]


@pytest.mark.parametrize("mutate", SEMANTIC_MUTATIONS)
def test_semantic_mutations_fail_even_with_refreshed_self_digest(
    validator: types.ModuleType,
    tmp_path: Path,
    mutate: Callable[[Dict[str, Any]], None],
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(validator, root, mutate)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_live_validator_passes_with_exact_nonclosure_status(
    validator: types.ModuleType,
) -> None:
    assert validator.validate(WORKSPACE) == {
        "schema_version": validator.SCHEMA,
        "state": validator.STATE,
        "control_predicate": validator.CONTROL_PREDICATE,
        "control_predicate_value": True,
        "fields_closed": ["F107", "F113", "F128", "F129", "F148"],
        "pre_execution_open_after": 161,
        "post_execution_open_after": 6,
        "total_open_after": 167,
        "blockers_open_after": 12,
        "scientific_execution": False,
        "validation": "PASS",
    }


def test_predecessor_drift_fails(validator: types.ModuleType, tmp_path: Path) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / validator.EXPECTED_PREDECESSORS[0][1]
    path.write_bytes(path.read_bytes() + b"\n")
    os.chmod(path, 0o644)
    with pytest.raises(validator.ValidationError, match="predecessor digest"):
        validator.validate(root)


@pytest.mark.parametrize("relative_kind", ("machine", "human", "predecessor"))
def test_leaf_mode_drift_fails(
    validator: types.ModuleType, tmp_path: Path, relative_kind: str
) -> None:
    root = _copy_roster(validator, tmp_path)
    relative = {
        "machine": validator.MACHINE_PATH,
        "human": validator.HUMAN_PATH,
        "predecessor": validator.EXPECTED_PREDECESSORS[0][1],
    }[relative_kind]
    os.chmod(root / relative, 0o600)
    with pytest.raises(validator.ValidationError, match="custody"):
        validator.validate(root)


@pytest.mark.parametrize("relative_kind", ("machine", "human", "predecessor"))
def test_hardlinked_leaf_fails(
    validator: types.ModuleType, tmp_path: Path, relative_kind: str
) -> None:
    root = _copy_roster(validator, tmp_path)
    relative = {
        "machine": validator.MACHINE_PATH,
        "human": validator.HUMAN_PATH,
        "predecessor": validator.EXPECTED_PREDECESSORS[0][1],
    }[relative_kind]
    target = root / relative
    os.link(target, target.with_name(target.name + ".alias"))
    with pytest.raises(validator.ValidationError, match="custody"):
        validator.validate(root)


@pytest.mark.parametrize("relative_kind", ("machine", "human", "predecessor"))
def test_symlinked_leaf_fails(
    validator: types.ModuleType, tmp_path: Path, relative_kind: str
) -> None:
    root = _copy_roster(validator, tmp_path)
    relative = {
        "machine": validator.MACHINE_PATH,
        "human": validator.HUMAN_PATH,
        "predecessor": validator.EXPECTED_PREDECESSORS[0][1],
    }[relative_kind]
    target = root / relative
    real = target.with_name(target.name + ".real")
    target.rename(real)
    target.symlink_to(real.name)
    with pytest.raises(validator.ValidationError, match="custody|resolution|unsafe"):
        validator.validate(root)


def test_symlinked_ancestor_fails(validator: types.ModuleType, tmp_path: Path) -> None:
    root = _copy_roster(validator, tmp_path)
    fixtures = root / "research/fixtures"
    real = root / "research/real-fixtures"
    fixtures.rename(real)
    fixtures.symlink_to(real.name, target_is_directory=True)
    with pytest.raises(validator.ValidationError, match="custody|resolution|unsafe"):
        validator.validate(root)


def test_noncanonical_machine_bytes_fail(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    machine = root / validator.MACHINE_PATH
    record = json.loads(machine.read_text("ascii"))
    machine.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", "ascii")
    os.chmod(machine, 0o644)
    with pytest.raises(validator.ValidationError, match="not canonical"):
        validator.validate(root)


def test_stale_machine_self_digest_fails(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: record.__setitem__("state", "ALTERED"),
        refresh_digest=False,
    )
    with pytest.raises(validator.ValidationError, match="self digest"):
        validator.validate(root)


def test_unknown_machine_key_fails_after_digest_refresh(
    validator: types.ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: record.__setitem__("unapproved_extension", True),
    )
    with pytest.raises(validator.ValidationError, match="key roster"):
        validator.validate(root)


def test_validator_has_no_network_entropy_process_or_write_capability() -> None:
    text = SOURCE.read_text("utf-8")
    for forbidden in (
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http.client",
        "secrets",
        "random",
        "os.system",
        "os.popen",
        "os.exec",
        "os.spawn",
        "urlopen",
        "Popen",
        "Path.write_bytes",
        "Path.write_text",
        "os.write",
    ):
        assert forbidden not in text
    assert "os.O_RDONLY" in text
    assert 'getattr(os, "O_NOFOLLOW", 0)' in text
    assert "os.open" in text


def test_package_is_not_bound_to_mutable_trackers(
    validator: types.ModuleType,
) -> None:
    paths = [path for _, path, _ in validator.EXPECTED_PREDECESSORS]
    paths += [
        validator.HUMAN_PATH,
        validator.MACHINE_PATH,
        validator.VALIDATOR_PATH,
        validator.TEST_PATH,
    ]
    assert "PROJECT_COMPLETION_TIMETABLE.md" not in paths
    assert "PROJECT_EVIDENCE_LEDGER.md" not in paths
    source = SOURCE.read_text("utf-8")
    assert "PROJECT_COMPLETION_TIMETABLE.md" not in source
    assert "PROJECT_EVIDENCE_LEDGER.md" not in source


def test_human_freeze_states_failure_and_nonclaim_boundaries() -> None:
    text = HUMAN.read_text("utf-8")
    assert "All 12 blockers remain open" in text
    assert "F112 remains open" in text
    assert "F149, the admissible" in text
    assert "Therefore an infrastructure abort\nis not rerun" in text
    assert "one domain\ncannot rescue the other" in text
    assert "It does not select CKS" in text
    assert "**Scientific execution:** none" in text
    assert "internal evidence only" in text


def test_live_package_files_are_regular_0644_single_link(
    validator: types.ModuleType,
) -> None:
    for relative in (
        validator.HUMAN_PATH,
        validator.MACHINE_PATH,
        validator.VALIDATOR_PATH,
        validator.TEST_PATH,
    ):
        status = os.lstat(WORKSPACE / relative)
        assert stat.S_ISREG(status.st_mode)
        assert not stat.S_ISLNK(status.st_mode)
        assert stat.S_IMODE(status.st_mode) == 0o644
        assert status.st_nlink == 1
