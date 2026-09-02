"""Hostile qualification for the additive F104 matched-compute freeze."""

from __future__ import annotations

import ast
import copy
from fractions import Fraction
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
    "manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/"
    "manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json"
)
HUMAN_REL = Path("PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md")
TEST_REL = Path(
    "tests/unit/"
    "test_manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py"
)


class _IntegerSubclass(int):
    pass


class _DictSubclass(dict):
    pass


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "manuscript_v3_f104_matched_compute_validator", ROOT / VALIDATOR_REL
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


def _zero_counts(module: ModuleType) -> Dict[str, Dict[str, int]]:
    return {
        phase: {event: 0 for event in module.RESOURCE_EVENTS}
        for phase in module.PHASES
    }


def _unit_weights(module: ModuleType) -> Dict[str, Fraction]:
    return {event: Fraction(1, 1) for event in module.RESOURCE_EVENTS}


def test_canonical_package_validates_exactly_one_field(
    validator: ModuleType,
) -> None:
    status = validator.validate(ROOT)
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": "F104_MATCHED_TOTAL_COMPUTE_FORMULA_FROZEN_RESOURCE_VALUES_NULL",
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "control_predicate": (
            "MATCHED_TOTAL_COMPUTE_FORMULA_F104_FROZEN_PREOUTCOME"
        ),
        "F104_closed": True,
        "unresolved_fields_closed": 1,
        "effective_pre_execution_open": 145,
        "effective_pre_execution_closed": 21,
        "effective_post_execution_open": 6,
        "effective_post_execution_closed": 0,
        "effective_open_blocker_count": 12,
        "B06_open": True,
        "B08_open": True,
        "B12_open": True,
        "formal_tests_closed": 0,
        "results_filled": 0,
        "scientific_execution": False,
        "tracker_edit_performed": False,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


def test_machine_is_canonical_and_exact_expected_record(
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


def test_every_predecessor_is_exactly_bound_and_machine_digest_recomputed(
    validator: ModuleType,
) -> None:
    record = _read_machine(ROOT)
    bindings = record["predecessor_bindings"]
    assert len(bindings) == len(validator.PREDECESSOR_SPECS) == 9
    assert record["predecessor_group_counts"] == {
        "BASELINE_COMPUTE_DRAFT_V1": 4,
        "GATE_A_B05_FREEZE_V1": 5,
    }
    for ordinal, (row, spec) in enumerate(
        zip(bindings, validator.PREDECESSOR_SPECS)
    ):
        group, role, path, byte_count, raw_sha, semantic_sha = spec
        raw = (ROOT / path).read_bytes()
        assert row["ordinal"] == ordinal
        assert row["group"] == group
        assert row["role"] == role
        assert row["path"] == path
        assert row["bytes"] == byte_count == len(raw)
        assert row["raw_sha256"] == raw_sha == hashlib.sha256(raw).hexdigest()
        if semantic_sha is not None:
            parsed = json.loads(raw.decode("ascii"))
            assert row["record_sha256"] == semantic_sha
            assert parsed["record_sha256"] == semantic_sha
            assert validator._predecessor_record_sha256(parsed) == semantic_sha


def test_authority_is_narrow_and_no_tracker_is_bound_as_output(
    validator: ModuleType,
) -> None:
    record = _read_machine(ROOT)
    authority = record["authority_provenance"]
    assert authority["normalized_visible_text"] == validator.AUTHORITY_TEXT
    assert authority["normalized_visible_text_sha256"] == hashlib.sha256(
        validator.AUTHORITY_TEXT.encode("utf-8")
    ).hexdigest()
    assert authority["bounded_offline_local_project_work_authorized"] is True
    for key in (
        "network_contact_repository_license_or_data_access_authorized",
        "hardware_reservation_operational_receipt_or_runtime_capture_authorized",
        "entropy_training_scientific_or_production_execution_authorized",
        "claim_promotion_submission_or_tracker_edit_authorized_by_this_package",
    ):
        assert authority[key] is False
    assert "PROJECT_COMPLETION_TIMETABLE.md" not in record["package_file_roster"]
    assert "PROJECT_EVIDENCE_LEDGER.md" not in record["package_file_roster"]


def test_evidence_ready_wording_is_exact_bounded_and_prospective(
    validator: ModuleType,
) -> None:
    record = _read_machine(ROOT)
    registration = record["evidence_ready_registration"]
    assert registration == {
        "conditional_on_independent_acceptance": True,
        "proposed_text": validator.EVIDENCE_READY_REGISTRATION,
        "registration_performed_by_this_package": False,
        "permitted_field_delta": ["F104"],
        "permitted_blocker_delta": [],
        "permitted_formal_test_delta": [],
        "permitted_result_delta": [],
    }
    human = (ROOT / HUMAN_REL).read_text(encoding="utf-8")
    assert validator.EVIDENCE_READY_REGISTRATION in human
    for required in (
        "146 open / 20 closed to 145 open / 21 closed",
        "post-execution counts remain 6 open / 0 closed",
        "all 12 blockers remain open",
        "Formal Tests 28 and 29 remain OPEN",
        "Formal Test 30 remains PENDING",
        "R1-R4 remain unexecuted",
    ):
        assert required in registration["proposed_text"]


def test_f104_value_is_exact_predecessor_contract(
    validator: ModuleType,
) -> None:
    record = _read_machine(ROOT)
    value = record["field_closures"][0]["value"]
    predecessor = json.loads(
        (
            ROOT
            / "research/fixtures/"
            "manuscript_v3_baseline_capability_compute_model_draft_v1.json"
        ).read_text(encoding="ascii")
    )
    assert value == dict(validator.FORMULA_VALUE)
    assert value == predecessor["matched_compute_contract"]
    assert record["field_closures"] == [
        {
            "field_id": "F104",
            "json_pointer": (
                "/method_and_baseline_plan/matched_total_compute_formula"
            ),
            "status": (
                "CLOSED_BY_ADDITIVE_PREOUTCOME_PARAMETERIZED_FORMULA_FREEZE"
            ),
            "value": value,
        }
    ]


def test_count_transition_and_complete_field_sweep_are_exact(
    validator: ModuleType,
) -> None:
    record = _read_machine(ROOT)
    transition = record["count_transition"]
    assert transition["before"] == {
        "pre_execution_open": 146,
        "pre_execution_closed": 20,
        "post_execution_open": 6,
        "post_execution_closed": 0,
        "total_open": 152,
        "total_closed": 20,
    }
    assert transition["closed_by_package"] == {
        "field_ids": ["F104"],
        "pre_execution": 1,
        "post_execution": 0,
        "total": 1,
    }
    assert transition["after"] == {
        "pre_execution_open": 145,
        "pre_execution_closed": 21,
        "post_execution_open": 6,
        "post_execution_closed": 0,
        "total_open": 151,
        "total_closed": 21,
    }
    assert transition["blockers_open_after"] == 12
    assert transition["blockers_closed"] == 0
    sweep = record["comprehensive_field_sweep"]
    assert sweep["closed_before_ids"] == list(validator.CLOSED_BEFORE)
    assert sweep["eligible_now_ids"] == ["F104"]
    assert sweep["closed_after_ids"] == list(validator.CLOSED_AFTER)
    assert sweep["open_after_ids"] == list(validator.OPEN_AFTER)
    assert len(sweep["open_after_ids"]) == sweep["open_after_count"] == 145
    assert "F104" not in sweep["open_after_ids"]
    assert set(sweep["closed_after_ids"]).isdisjoint(sweep["open_after_ids"])
    assert len(sweep["closed_after_ids"]) == 21


def test_nonclosures_preserve_every_prohibited_effect(validator: ModuleType) -> None:
    record = _read_machine(ROOT)
    boundary = record["f104_parameterization_boundary"]
    assert boundary["formula_and_accounting_semantics_frozen"] is True
    for key in (
        "resource_counts_populated",
        "calibration_weights_populated",
        "hardware_or_environment_selected",
        "method_training_inference_or_tuning_budgets_populated",
        "resource_ceilings_or_allocations_populated",
        "actual_compute_capacity_or_reservation_present",
        "synthetic_vector_is_budget_or_capacity_evidence",
    ):
        assert boundary[key] is False
    effects = record["project_effects_and_nonclaims"]
    assert effects["only_field_closed"] == "F104"
    for key in (
        "F062_F103_remain_open",
        "F139_F147_remain_open",
        "F150_F162_remain_open",
        "B06_remains_open",
        "B08_remains_open",
        "B12_remains_open",
        "all_12_blockers_remain_open",
        "R1_R2_R3_R4_remain_unexecuted",
    ):
        assert effects[key] is True
    for key in (
        "hardware_or_capacity_selected_reserved_or_claimed",
        "runtime_or_operational_receipt_created",
        "network_contact_repository_license_or_data_access_performed",
        "entropy_training_scientific_or_production_execution_performed",
        "result_or_claim_promoted",
        "submission_performed",
        "tracker_or_evidence_ledger_edited",
    ):
        assert effects[key] is False
    assert effects["formal_test_28_status"] == "OPEN"
    assert effects["formal_test_29_status"] == "OPEN"
    assert effects["formal_test_30_status"] == "PENDING"


def test_exact_synthetic_calculator_replays_predecessor_receipt(
    validator: ModuleType,
) -> None:
    assert validator.SYNTHETIC_QUALIFICATION == {
        "calculator_id": "EXACT_WEIGHTED_RESOURCE_LEDGER_V1",
        "phase_costs": {
            "PILOT": {"numerator": 4, "denominator": 1},
            "TUNING": {"numerator": 20, "denominator": 1},
            "FINAL_TRAINING": {"numerator": 31, "denominator": 1},
            "CONFIRMATORY_INFERENCE": {"numerator": 30, "denominator": 1},
        },
        "total_cost": {"numerator": 85, "denominator": 1},
        "binary_float_used": False,
    }
    assert validator.exact_compute_cost(
        validator.SYNTHETIC_COUNTS, validator.SYNTHETIC_WEIGHTS
    ) == validator.SYNTHETIC_QUALIFICATION


def test_fractional_cost_is_exact_and_contains_no_float(
    validator: ModuleType,
) -> None:
    counts = _zero_counts(validator)
    weights = _unit_weights(validator)
    counts["PILOT"]["BASE_FORWARD"] = 1
    counts["TUNING"]["GUIDE_EVALUATION"] = 3
    weights["BASE_FORWARD"] = Fraction(1, 3)
    weights["GUIDE_EVALUATION"] = Fraction(2, 7)
    result = validator.exact_compute_cost(counts, weights)
    assert result["phase_costs"]["PILOT"] == {"numerator": 1, "denominator": 3}
    assert result["phase_costs"]["TUNING"] == {"numerator": 6, "denominator": 7}
    assert result["total_cost"] == {"numerator": 25, "denominator": 21}

    def inspect(value: Any) -> None:
        assert type(value) is not float
        if type(value) is dict:
            for child in value.values():
                inspect(child)
        elif type(value) is list:
            for child in value:
                inspect(child)

    inspect(result)


def test_zero_counts_are_valid_but_zero_weights_are_not(
    validator: ModuleType,
) -> None:
    result = validator.exact_compute_cost(
        _zero_counts(validator), _unit_weights(validator)
    )
    assert result["total_cost"] == {"numerator": 0, "denominator": 1}
    weights = _unit_weights(validator)
    weights["BASE_FORWARD"] = 0
    with pytest.raises(validator.ValidationError, match="strictly positive"):
        validator.exact_compute_cost(_zero_counts(validator), weights)


@pytest.mark.parametrize(
    "bad",
    [True, 1.0, Fraction(1, 2), "1", None, -1, _IntegerSubclass(1)],
)
def test_invalid_count_type_or_value_fails_closed(
    validator: ModuleType, bad: Any
) -> None:
    counts = _zero_counts(validator)
    counts["PILOT"]["BASE_FORWARD"] = bad
    with pytest.raises(validator.ValidationError):
        validator.exact_compute_cost(counts, _unit_weights(validator))


@pytest.mark.parametrize(
    "bad",
    [
        True,
        1.0,
        "1",
        None,
        0,
        -1,
        Fraction(0, 1),
        Fraction(-1, 2),
        _IntegerSubclass(1),
    ],
)
def test_invalid_weight_type_or_value_fails_closed(
    validator: ModuleType, bad: Any
) -> None:
    weights = _unit_weights(validator)
    weights["BASE_FORWARD"] = bad
    with pytest.raises(validator.ValidationError):
        validator.exact_compute_cost(_zero_counts(validator), weights)


def test_mapping_subclasses_and_key_roster_drift_fail_closed(
    validator: ModuleType,
) -> None:
    counts = _zero_counts(validator)
    weights = _unit_weights(validator)
    with pytest.raises(validator.ValidationError):
        validator.exact_compute_cost(_DictSubclass(counts), weights)
    with pytest.raises(validator.ValidationError):
        validator.exact_compute_cost(counts, _DictSubclass(weights))
    bad_counts = copy.deepcopy(counts)
    bad_counts["PILOT"] = _DictSubclass(bad_counts["PILOT"])
    with pytest.raises(validator.ValidationError):
        validator.exact_compute_cost(bad_counts, weights)
    missing_phase = copy.deepcopy(counts)
    missing_phase.pop("PILOT")
    extra_phase = copy.deepcopy(counts)
    extra_phase["ALIEN"] = {event: 0 for event in validator.RESOURCE_EVENTS}
    reversed_phases = dict(reversed(tuple(counts.items())))
    for mapping in (missing_phase, extra_phase, reversed_phases):
        with pytest.raises(validator.ValidationError, match="phase key roster"):
            validator.exact_compute_cost(mapping, weights)
    missing_weights = dict(weights)
    missing_weights.pop("BASE_FORWARD")
    extra_weights = dict(weights)
    extra_weights["ALIEN"] = 1
    reversed_weights = dict(reversed(tuple(weights.items())))
    for mapping in (missing_weights, extra_weights, reversed_weights):
        with pytest.raises(validator.ValidationError, match="weight key roster"):
            validator.exact_compute_cost(counts, mapping)
    missing_event = copy.deepcopy(counts)
    missing_event["PILOT"].pop("BASE_FORWARD")
    extra_event = copy.deepcopy(counts)
    extra_event["PILOT"]["ALIEN"] = 0
    reversed_events = copy.deepcopy(counts)
    reversed_events["PILOT"] = dict(
        reversed(tuple(reversed_events["PILOT"].items()))
    )
    for mapping in (missing_event, extra_event, reversed_events):
        with pytest.raises(validator.ValidationError, match="resource count key roster"):
            validator.exact_compute_cost(mapping, weights)


def test_component_and_accumulation_bit_bounds_fail_closed(
    validator: ModuleType,
) -> None:
    boundary = 1 << (validator.MAX_RATIONAL_COMPONENT_BITS - 1)
    weights = _unit_weights(validator)
    weights["BASE_FORWARD"] = Fraction(boundary, 1)
    validator.exact_compute_cost(_zero_counts(validator), weights)
    weights["BASE_FORWARD"] = Fraction(
        1 << validator.MAX_RATIONAL_COMPONENT_BITS, 1
    )
    with pytest.raises(validator.ValidationError, match="component bit bound"):
        validator.exact_compute_cost(_zero_counts(validator), weights)

    counts = _zero_counts(validator)
    weights = _unit_weights(validator)
    huge = 1 << (validator.MAX_RATIONAL_COMPONENT_BITS - 1)
    for phase in validator.PHASES:
        for event in validator.RESOURCE_EVENTS:
            counts[phase][event] = huge
            weights[event] = huge
    with pytest.raises(validator.ValidationError, match="accumulated bit bound"):
        validator.exact_compute_cost(counts, weights)


MACHINE_MUTATIONS: List[Callable[[Dict[str, Any]], None]] = [
    lambda record: record.__setitem__("state", "PASS"),
    lambda record: record.__setitem__("global_state", "EXECUTABLE"),
    lambda record: record.__setitem__("control_predicate", "PASS"),
    lambda record: _replace(record, "field_closures.0.field_id", "F103"),
    lambda record: _replace(record, "field_closures.0.json_pointer", "/wrong"),
    lambda record: _replace(record, "field_closures.0.value.formula", "C=m+d"),
    lambda record: _replace(record, "field_closures.0.value.phases.0", "SCIENCE"),
    lambda record: _replace(
        record, "field_closures.0.value.resource_events.0", "ALIEN"
    ),
    lambda record: _replace(
        record, "field_closures.0.value.hardware_calibration_weights_populated", True
    ),
    lambda record: _replace(
        record, "f104_parameterization_boundary.resource_counts_populated", True
    ),
    lambda record: _replace(
        record, "f104_parameterization_boundary.calibration_weights_populated", True
    ),
    lambda record: _replace(
        record, "f104_parameterization_boundary.hardware_or_environment_selected", True
    ),
    lambda record: _replace(
        record,
        "f104_parameterization_boundary.method_training_inference_or_tuning_budgets_populated",
        True,
    ),
    lambda record: _replace(
        record,
        "f104_parameterization_boundary.resource_ceilings_or_allocations_populated",
        True,
    ),
    lambda record: _replace(
        record,
        "f104_parameterization_boundary.actual_compute_capacity_or_reservation_present",
        True,
    ),
    lambda record: _replace(
        record,
        "f104_parameterization_boundary.synthetic_vector_is_budget_or_capacity_evidence",
        True,
    ),
    lambda record: _replace(
        record,
        "f104_parameterization_boundary.f104_may_be_evaluated_only_after_future_inputs_are_frozen",
        False,
    ),
    lambda record: _replace(record, "count_transition.after.pre_execution_open", 144),
    lambda record: _replace(record, "count_transition.blockers_closed", 1),
    lambda record: _replace(record, "count_transition.formal_tests_closed", 1),
    lambda record: _replace(record, "count_transition.results_filled", 1),
    lambda record: record["field_closures"].append(
        copy.deepcopy(record["field_closures"][0])
    ),
    lambda record: record["comprehensive_field_sweep"]["open_after_ids"].remove(
        "F103"
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.B06_remains_open", False
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.B08_remains_open", False
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.B12_remains_open", False
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.all_12_blockers_remain_open", False
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.formal_test_28_status", "CLOSED"
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.formal_test_29_status", "CLOSED"
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.formal_test_30_status", "CLOSED"
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.R1_R2_R3_R4_remain_unexecuted", False
    ),
    lambda record: _replace(
        record,
        "project_effects_and_nonclaims.hardware_or_capacity_selected_reserved_or_claimed",
        True,
    ),
    lambda record: _replace(
        record,
        "project_effects_and_nonclaims.entropy_training_scientific_or_production_execution_performed",
        True,
    ),
    lambda record: _replace(
        record,
        "project_effects_and_nonclaims.runtime_or_operational_receipt_created",
        True,
    ),
    lambda record: _replace(
        record,
        "project_effects_and_nonclaims.network_contact_repository_license_or_data_access_performed",
        True,
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.result_or_claim_promoted", True
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.submission_performed", True
    ),
    lambda record: _replace(
        record, "project_effects_and_nonclaims.tracker_or_evidence_ledger_edited", True
    ),
    lambda record: _replace(
        record,
        "authority_provenance.network_contact_repository_license_or_data_access_authorized",
        True,
    ),
    lambda record: _replace(
        record,
        "authority_provenance.hardware_reservation_operational_receipt_or_runtime_capture_authorized",
        True,
    ),
    lambda record: _replace(
        record,
        "authority_provenance.entropy_training_scientific_or_production_execution_authorized",
        True,
    ),
    lambda record: _replace(
        record,
        "authority_provenance.claim_promotion_submission_or_tracker_edit_authorized_by_this_package",
        True,
    ),
    lambda record: _replace(
        record, "evidence_ready_registration.proposed_text", "PROMOTE EVERYTHING"
    ),
    lambda record: _replace(
        record,
        "evidence_ready_registration.registration_performed_by_this_package",
        True,
    ),
    lambda record: record["evidence_ready_registration"][
        "permitted_field_delta"
    ].append("F105"),
    lambda record: record["predecessor_bindings"].pop(),
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


def test_machine_tamper_without_rehash_fails_self_digest(
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


@pytest.mark.parametrize("index", range(9))
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
def test_link_substitution_fails_closed(
    validator: ModuleType, tmp_path: Path, kind: str
) -> None:
    root = _copy_roster(validator, tmp_path / "root")
    target = root / str(HUMAN_REL)
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
