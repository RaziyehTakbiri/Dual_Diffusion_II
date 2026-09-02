"""Focused hostile tests for the production F104 compute contract."""

from __future__ import annotations

import ast
import copy
from fractions import Fraction
from pathlib import Path

import pytest

from heterodiff.experiments import matched_total_compute as compute


ROOT = Path(__file__).resolve().parents[2]


class _IntegerSubclass(int):
    pass


class _DictSubclass(dict):
    pass


def _weights():
    return {event: 1 for event in compute.RESOURCE_EVENTS}


def _budget(role, method_id, budget_id, *, domain="physionet-challenge-2012"):
    return {
        "schema_version": compute.PROSPECTIVE_BUDGET_SCHEMA_VERSION,
        "budget_id": budget_id,
        "method_id": method_id,
        "method_role": role,
        "domain_id": domain,
        "training_compute_budget_id": f"{domain}-shared-training-v1",
        "inference_compute_budget_id": f"{domain}-shared-inference-v1",
        "calibration_weight_record_id": f"{domain}-future-b08-weights-v1",
        "scalar_ceiling_id": f"{domain}-future-b08-scalar-ceiling-v1",
        "hard_axis_ceiling_ids": {
            axis: f"{domain}-{axis.lower()}-future-b08-v1"
            for axis in compute.HARD_AXES
        },
        "fairness_bindings": {
            "shared_base_checkpoint_id": f"{domain}-base-checkpoint-v1",
            "group_roster_id": f"{domain}-groups-v1",
            "conditioning_case_roster_id": f"{domain}-cases-v1",
            "draw_roster_id": f"{domain}-draws-v1",
            "precision_policy_id": "shared-precision-policy-v1",
            "metric_workload_id": "f105-r64-workload-v1",
        },
        "accounting_policy": {
            "failed_attempts_charged": True,
            "author_extensions_charged": True,
            "unique_preprocessing_charged": True,
            "unused_allocation_transfer_permitted": False,
            "post_result_top_up_permitted": False,
        },
        "unpopulated_b08_values": {
            "hardware_identity_value_assigned": False,
            "runtime_identity_value_assigned": False,
            "calibration_weight_values_assigned": False,
            "scalar_ceiling_value_assigned": False,
            "hard_axis_ceiling_values_assigned": False,
            "capacity_reserved": False,
        },
    }


def _pair(domain="physionet-challenge-2012"):
    return (
        _budget(
            compute.PRIMARY_METHOD_ROLE,
            "association-aware-guide-plus-residual",
            f"{domain}-guide-budget-v1",
            domain=domain,
        ),
        _budget(
            compute.PRIMARY_COMPARATOR_ROLE,
            "unified-direct-conditioner",
            f"{domain}-direct-budget-v1",
            domain=domain,
        ),
    )


def test_f104_rosters_are_exact_and_complete():
    assert compute.PHASES == (
        "PILOT",
        "TUNING",
        "FINAL_TRAINING",
        "CONFIRMATORY_INFERENCE",
    )
    assert compute.RESOURCE_EVENTS == (
        "BASE_FORWARD",
        "BASE_BACKWARD",
        "CONDITIONER_FORWARD",
        "CONDITIONER_BACKWARD",
        "GUIDE_EVALUATION",
        "RESAMPLING_STEP",
        "ODE_OR_SDE_STEP",
        "DATA_ADAPTER_RECORD",
        "METRIC_DRAW_EVALUATION",
        "OTHER_DECLARED_OPERATION",
    )
    assert compute.HARD_AXES == (
        "WALL_TIME",
        "ACCELERATOR_TIME",
        "PEAK_DEVICE_MEMORY",
        "PEAK_HOST_MEMORY",
        "MODEL_EVALUATION_COUNT",
        "PERSISTENT_BYTES",
        "FAILURE_COUNT",
        "PARAMETER_COUNT",
    )


def test_exact_cost_uses_no_binary_float_and_preserves_phase_decomposition():
    counts = compute.zero_resource_counts()
    weights = _weights()
    counts["PILOT"]["BASE_FORWARD"] = 1
    counts["TUNING"]["GUIDE_EVALUATION"] = 3
    counts["FINAL_TRAINING"]["CONDITIONER_BACKWARD"] = 2
    counts["CONFIRMATORY_INFERENCE"]["METRIC_DRAW_EVALUATION"] = 5
    weights["BASE_FORWARD"] = Fraction(1, 3)
    weights["GUIDE_EVALUATION"] = Fraction(2, 7)
    weights["CONDITIONER_BACKWARD"] = Fraction(5, 11)
    weights["METRIC_DRAW_EVALUATION"] = Fraction(3, 13)

    result = compute.exact_compute_cost(counts, weights)
    assert result == {
        "calculator_id": "EXACT_WEIGHTED_RESOURCE_LEDGER_V1",
        "phase_costs": {
            "PILOT": {"numerator": 1, "denominator": 3},
            "TUNING": {"numerator": 6, "denominator": 7},
            "FINAL_TRAINING": {"numerator": 10, "denominator": 11},
            "CONFIRMATORY_INFERENCE": {"numerator": 15, "denominator": 13},
        },
        "total_cost": {"numerator": 9770, "denominator": 3003},
        "binary_float_used": False,
    }

    def reject_float(value):
        assert type(value) is not float
        if type(value) is dict:
            for item in value.values():
                reject_float(item)

    reject_float(result)


def test_zero_counts_are_valid_and_fresh():
    first = compute.zero_resource_counts()
    second = compute.zero_resource_counts()
    first["PILOT"]["BASE_FORWARD"] = 1
    assert second["PILOT"]["BASE_FORWARD"] == 0
    result = compute.exact_compute_cost(second, _weights())
    assert result["total_cost"] == {"numerator": 0, "denominator": 1}


@pytest.mark.parametrize(
    "bad",
    [True, 1.0, Fraction(1, 2), "1", None, -1, _IntegerSubclass(1)],
)
def test_counts_require_exact_nonnegative_builtin_integers(bad):
    counts = compute.zero_resource_counts()
    counts["PILOT"]["BASE_FORWARD"] = bad
    with pytest.raises(compute.MatchedTotalComputeError):
        compute.exact_compute_cost(counts, _weights())


@pytest.mark.parametrize(
    "bad",
    [True, 1.0, "1", None, 0, -1, Fraction(0), Fraction(-1, 2), _IntegerSubclass(1)],
)
def test_weights_require_strictly_positive_exact_int_or_fraction(bad):
    weights = _weights()
    weights["BASE_FORWARD"] = bad
    with pytest.raises(compute.MatchedTotalComputeError):
        compute.exact_compute_cost(compute.zero_resource_counts(), weights)


def test_mapping_subclasses_and_every_roster_drift_fail_closed():
    counts = compute.zero_resource_counts()
    weights = _weights()
    with pytest.raises(compute.MatchedTotalComputeError):
        compute.exact_compute_cost(_DictSubclass(counts), weights)
    with pytest.raises(compute.MatchedTotalComputeError):
        compute.exact_compute_cost(counts, _DictSubclass(weights))

    candidates = []
    missing_phase = copy.deepcopy(counts)
    missing_phase.pop("PILOT")
    candidates.append(missing_phase)
    candidates.append(dict(reversed(tuple(counts.items()))))
    extra_phase = copy.deepcopy(counts)
    extra_phase["ALIEN"] = {event: 0 for event in compute.RESOURCE_EVENTS}
    candidates.append(extra_phase)
    for candidate in candidates:
        with pytest.raises(compute.MatchedTotalComputeError):
            compute.exact_compute_cost(candidate, weights)

    bad_events = copy.deepcopy(counts)
    bad_events["PILOT"] = dict(
        reversed(tuple(bad_events["PILOT"].items()))
    )
    with pytest.raises(compute.MatchedTotalComputeError):
        compute.exact_compute_cost(bad_events, weights)


def test_component_and_accumulation_bounds_fail_closed():
    boundary = 1 << (compute.MAX_RATIONAL_COMPONENT_BITS - 1)
    weights = _weights()
    weights["BASE_FORWARD"] = boundary
    compute.exact_compute_cost(compute.zero_resource_counts(), weights)
    weights["BASE_FORWARD"] = 1 << compute.MAX_RATIONAL_COMPONENT_BITS
    with pytest.raises(compute.MatchedTotalComputeError, match="component bit"):
        compute.exact_compute_cost(compute.zero_resource_counts(), weights)

    counts = compute.zero_resource_counts()
    weights = _weights()
    huge = 1 << (compute.MAX_RATIONAL_COMPONENT_BITS - 1)
    for phase in compute.PHASES:
        for event in compute.RESOURCE_EVENTS:
            counts[phase][event] = huge
            weights[event] = huge
    with pytest.raises(compute.MatchedTotalComputeError, match="accumulated bit"):
        compute.exact_compute_cost(counts, weights)


@pytest.mark.parametrize("domain", compute.DOMAIN_IDS)
def test_prospective_budget_record_validates_without_assigning_b08_values(domain):
    method, _ = _pair(domain)
    result = compute.validate_prospective_budget_record(method)
    assert result == method
    assert tuple(result["hard_axis_ceiling_ids"]) == compute.HARD_AXES
    assert all(value is False for value in result["unpopulated_b08_values"].values())
    assert result["accounting_policy"] == {
        "failed_attempts_charged": True,
        "author_extensions_charged": True,
        "unique_preprocessing_charged": True,
        "unused_allocation_transfer_permitted": False,
        "post_result_top_up_permitted": False,
    }
    assert result is not method
    assert result["hard_axis_ceiling_ids"] is not method["hard_axis_ceiling_ids"]


@pytest.mark.parametrize(
    ("section", "field", "hostile"),
    [
        ("accounting_policy", "failed_attempts_charged", False),
        ("accounting_policy", "author_extensions_charged", False),
        ("accounting_policy", "unique_preprocessing_charged", False),
        ("accounting_policy", "unused_allocation_transfer_permitted", True),
        ("accounting_policy", "post_result_top_up_permitted", True),
        ("unpopulated_b08_values", "hardware_identity_value_assigned", True),
        ("unpopulated_b08_values", "runtime_identity_value_assigned", True),
        ("unpopulated_b08_values", "calibration_weight_values_assigned", True),
        ("unpopulated_b08_values", "scalar_ceiling_value_assigned", True),
        ("unpopulated_b08_values", "hard_axis_ceiling_values_assigned", True),
        ("unpopulated_b08_values", "capacity_reserved", True),
    ],
)
def test_charging_no_top_up_and_b08_boundaries_are_mandatory(
    section, field, hostile
):
    method, _ = _pair()
    method[section][field] = hostile
    with pytest.raises(compute.MatchedTotalComputeError):
        compute.validate_prospective_budget_record(method)


def test_budget_record_rejects_bad_roles_domains_identifiers_and_key_order():
    method, _ = _pair()
    for field, hostile in (
        ("method_role", "CONTROL"),
        ("domain_id", "R3-PHYS"),
        ("budget_id", "contains whitespace"),
        ("method_id", "méthod"),
    ):
        candidate = copy.deepcopy(method)
        candidate[field] = hostile
        with pytest.raises(compute.MatchedTotalComputeError):
            compute.validate_prospective_budget_record(candidate)

    reordered = dict(reversed(tuple(method.items())))
    with pytest.raises(compute.MatchedTotalComputeError, match="roster or order"):
        compute.validate_prospective_budget_record(reordered)


def test_hard_axis_identifiers_are_complete_and_carry_no_values():
    method, _ = _pair()
    candidate = copy.deepcopy(method)
    candidate["hard_axis_ceiling_ids"].pop("WALL_TIME")
    with pytest.raises(compute.MatchedTotalComputeError):
        compute.validate_prospective_budget_record(candidate)

    candidate = copy.deepcopy(method)
    candidate["hard_axis_ceiling_ids"]["WALL_TIME"] = 100
    with pytest.raises(compute.MatchedTotalComputeError):
        compute.validate_prospective_budget_record(candidate)


@pytest.mark.parametrize("domain", compute.DOMAIN_IDS)
def test_primary_pair_requires_exact_prospective_budget_equality(domain):
    method, comparator = _pair(domain)
    result = compute.validate_primary_pair_equality(method, comparator)
    assert result == {
        "schema_version": compute.PRIMARY_PAIR_MATCH_SCHEMA_VERSION,
        "domain_id": domain,
        "primary_method_id": "association-aware-guide-plus-residual",
        "primary_method_budget_id": f"{domain}-guide-budget-v1",
        "primary_comparator_id": "unified-direct-conditioner",
        "primary_comparator_budget_id": f"{domain}-direct-budget-v1",
        "matched_fields": list(compute.PRIMARY_PAIR_MATCHED_FIELDS),
        "equal_prospective_ceiling_and_selection_opportunity": True,
        "realized_resource_equality_claimed": False,
        "b08_resource_values_assigned": False,
    }


@pytest.mark.parametrize("field", compute.PRIMARY_PAIR_MATCHED_FIELDS)
def test_primary_pair_refuses_every_matched_field_difference(field):
    method, comparator = _pair()
    if field == "domain_id":
        comparator[field] = "online-retail-ii"
    elif type(comparator[field]) is str:
        comparator[field] += "-different"
    else:
        first = next(iter(comparator[field]))
        if type(comparator[field][first]) is str:
            comparator[field][first] += "-different"
        else:
            comparator[field][first] = not comparator[field][first]
    with pytest.raises(compute.MatchedTotalComputeError):
        compute.validate_primary_pair_equality(method, comparator)


def test_primary_pair_roles_method_ids_and_record_ids_are_not_interchangeable():
    method, comparator = _pair()
    reversed_method = copy.deepcopy(method)
    reversed_method["method_role"] = compute.PRIMARY_COMPARATOR_ROLE
    with pytest.raises(compute.MatchedTotalComputeError, match="PRIMARY_METHOD"):
        compute.validate_primary_pair_equality(reversed_method, comparator)

    same_method = copy.deepcopy(comparator)
    same_method["method_id"] = method["method_id"]
    with pytest.raises(compute.MatchedTotalComputeError, match="method IDs"):
        compute.validate_primary_pair_equality(method, same_method)

    same_budget = copy.deepcopy(comparator)
    same_budget["budget_id"] = method["budget_id"]
    with pytest.raises(compute.MatchedTotalComputeError, match="budget record IDs"):
        compute.validate_primary_pair_equality(method, same_budget)


def test_module_import_surface_is_pure_and_framework_free():
    source_path = ROOT / "src/heterodiff/experiments/matched_total_compute.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported == {"__future__", "fractions", "typing"}
