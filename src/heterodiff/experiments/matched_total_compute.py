"""Pure production contract for F104 matched-total-compute accounting.

The scalar calculator in this module is the executable counterpart of the
frozen F104 formula.  It accepts complete, exactly ordered resource ledgers,
uses only integer and :class:`fractions.Fraction` arithmetic, and returns
canonical numerator/denominator records.

The prospective-budget surface deliberately binds *identifiers* for future
calibration and hard-axis ceilings rather than assigning their values.  Those
hardware, runtime, calibration, and capacity values belong to B08.  This
module therefore supports a pre-outcome B06 method-budget freeze without
silently closing B08 or manufacturing a capacity receipt.

Import and validation are pure: there is no file, network, process, clock,
randomness, framework, model, metric, or scientific-execution path here.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, Mapping, Sequence


CALCULATOR_ID = "EXACT_WEIGHTED_RESOURCE_LEDGER_V1"
PROSPECTIVE_BUDGET_SCHEMA_VERSION = (
    "heterodiff-f104-prospective-matched-compute-budget-v1"
)
PRIMARY_PAIR_MATCH_SCHEMA_VERSION = (
    "heterodiff-f104-primary-pair-budget-match-v1"
)

PHASES = (
    "PILOT",
    "TUNING",
    "FINAL_TRAINING",
    "CONFIRMATORY_INFERENCE",
)

RESOURCE_EVENTS = (
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

HARD_AXES = (
    "WALL_TIME",
    "ACCELERATOR_TIME",
    "PEAK_DEVICE_MEMORY",
    "PEAK_HOST_MEMORY",
    "MODEL_EVALUATION_COUNT",
    "PERSISTENT_BYTES",
    "FAILURE_COUNT",
    "PARAMETER_COUNT",
)

DOMAIN_IDS = (
    "physionet-challenge-2012",
    "online-retail-ii",
)

PRIMARY_METHOD_ROLE = "PRIMARY_METHOD"
PRIMARY_COMPARATOR_ROLE = "PRIMARY_COMPARATOR"

MAX_RATIONAL_COMPONENT_BITS = 4096
MAX_ACCUMULATED_COMPONENT_BITS = 8192
MAX_IDENTIFIER_BYTES = 512

_BUDGET_KEYS = (
    "schema_version",
    "budget_id",
    "method_id",
    "method_role",
    "domain_id",
    "training_compute_budget_id",
    "inference_compute_budget_id",
    "calibration_weight_record_id",
    "scalar_ceiling_id",
    "hard_axis_ceiling_ids",
    "fairness_bindings",
    "accounting_policy",
    "unpopulated_b08_values",
)

FAIRNESS_BINDING_KEYS = (
    "shared_base_checkpoint_id",
    "group_roster_id",
    "conditioning_case_roster_id",
    "draw_roster_id",
    "precision_policy_id",
    "metric_workload_id",
)

ACCOUNTING_POLICY_KEYS = (
    "failed_attempts_charged",
    "author_extensions_charged",
    "unique_preprocessing_charged",
    "unused_allocation_transfer_permitted",
    "post_result_top_up_permitted",
)

UNPOPULATED_B08_VALUE_KEYS = (
    "hardware_identity_value_assigned",
    "runtime_identity_value_assigned",
    "calibration_weight_values_assigned",
    "scalar_ceiling_value_assigned",
    "hard_axis_ceiling_values_assigned",
    "capacity_reserved",
)

PRIMARY_PAIR_MATCHED_FIELDS = (
    "domain_id",
    "training_compute_budget_id",
    "inference_compute_budget_id",
    "calibration_weight_record_id",
    "scalar_ceiling_id",
    "hard_axis_ceiling_ids",
    "fairness_bindings",
    "accounting_policy",
    "unpopulated_b08_values",
)


class MatchedTotalComputeError(ValueError):
    """Raised when an F104 ledger or prospective budget is malformed."""


def _exact_keys(value: object, expected: Sequence[str], *, name: str) -> dict:
    if type(value) is not dict:
        raise MatchedTotalComputeError(f"{name} must be an exact dictionary")
    if tuple(value) != tuple(expected):
        raise MatchedTotalComputeError(f"{name} key roster or order mismatch")
    return value


def _identifier(value: object, *, name: str) -> str:
    if type(value) is not str or not value:
        raise MatchedTotalComputeError(f"{name} must be a nonempty exact string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as error:
        raise MatchedTotalComputeError(f"{name} must be ASCII") from error
    if len(encoded) > MAX_IDENTIFIER_BYTES:
        raise MatchedTotalComputeError(f"{name} exceeds its byte limit")
    if any(byte < 0x21 or byte > 0x7E for byte in encoded):
        raise MatchedTotalComputeError(
            f"{name} must contain visible ASCII without whitespace"
        )
    return value


def _exact_false(value: object, *, name: str) -> bool:
    if type(value) is not bool or value is not False:
        raise MatchedTotalComputeError(f"{name} must remain exact false")
    return False


def _exact_true(value: object, *, name: str) -> bool:
    if type(value) is not bool or value is not True:
        raise MatchedTotalComputeError(f"{name} must be exact true")
    return True


def _fraction(value: object, *, name: str, positive: bool) -> Fraction:
    if type(value) is int:
        result = Fraction(value, 1)
    elif type(value) is Fraction:
        result = value
    else:
        raise MatchedTotalComputeError(
            f"{name} must be an exact int or Fraction"
        )
    if positive and result <= 0:
        raise MatchedTotalComputeError(f"{name} must be strictly positive")
    if not positive and result < 0:
        raise MatchedTotalComputeError(f"{name} must be nonnegative")
    if (
        result.numerator.bit_length() > MAX_RATIONAL_COMPONENT_BITS
        or result.denominator.bit_length() > MAX_RATIONAL_COMPONENT_BITS
    ):
        raise MatchedTotalComputeError(
            f"{name} exceeds the normalized component bit bound"
        )
    return result


def _count(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise MatchedTotalComputeError(
            f"{name} must be an exact nonnegative integer"
        )
    if value < 0:
        raise MatchedTotalComputeError(f"{name} must be nonnegative")
    if value.bit_length() > MAX_RATIONAL_COMPONENT_BITS:
        raise MatchedTotalComputeError(f"{name} exceeds the count bit bound")
    return value


def _fraction_record(value: Fraction) -> Dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def zero_resource_counts() -> Dict[str, Dict[str, int]]:
    """Return a fresh complete, exactly ordered zero-count F104 ledger."""

    return {
        phase: {event: 0 for event in RESOURCE_EVENTS}
        for phase in PHASES
    }


def exact_compute_cost(
    counts_by_phase: Mapping[str, Mapping[str, int]],
    weights: Mapping[str, Any],
) -> Dict[str, Any]:
    """Calculate the exact F104 scalar for one method/domain ledger."""

    checked_phases = _exact_keys(
        counts_by_phase, PHASES, name="counts_by_phase"
    )
    checked_weights = _exact_keys(weights, RESOURCE_EVENTS, name="weights")
    exact_weights = {
        event: _fraction(
            checked_weights[event], name=f"weight {event}", positive=True
        )
        for event in RESOURCE_EVENTS
    }

    phase_costs: Dict[str, Dict[str, int]] = {}
    total = Fraction(0, 1)
    for phase in PHASES:
        counts = _exact_keys(
            checked_phases[phase],
            RESOURCE_EVENTS,
            name=f"resource counts for {phase}",
        )
        phase_cost = Fraction(0, 1)
        for event in RESOURCE_EVENTS:
            phase_cost += (
                _count(counts[event], name=f"{phase} {event}")
                * exact_weights[event]
            )
        if (
            phase_cost.numerator.bit_length()
            > MAX_ACCUMULATED_COMPONENT_BITS
            or phase_cost.denominator.bit_length()
            > MAX_ACCUMULATED_COMPONENT_BITS
        ):
            raise MatchedTotalComputeError(
                f"{phase} cost exceeds the accumulated bit bound"
            )
        phase_costs[phase] = _fraction_record(phase_cost)
        total += phase_cost

    if (
        total.numerator.bit_length() > MAX_ACCUMULATED_COMPONENT_BITS
        or total.denominator.bit_length() > MAX_ACCUMULATED_COMPONENT_BITS
    ):
        raise MatchedTotalComputeError(
            "total cost exceeds the accumulated bit bound"
        )
    return {
        "calculator_id": CALCULATOR_ID,
        "phase_costs": phase_costs,
        "total_cost": _fraction_record(total),
        "binary_float_used": False,
    }


def _identifier_record(
    value: object, expected: Sequence[str], *, name: str
) -> Dict[str, str]:
    checked = _exact_keys(value, expected, name=name)
    return {
        key: _identifier(checked[key], name=f"{name}.{key}")
        for key in expected
    }


def _accounting_policy(value: object) -> Dict[str, bool]:
    checked = _exact_keys(
        value, ACCOUNTING_POLICY_KEYS, name="accounting_policy"
    )
    return {
        "failed_attempts_charged": _exact_true(
            checked["failed_attempts_charged"],
            name="accounting_policy.failed_attempts_charged",
        ),
        "author_extensions_charged": _exact_true(
            checked["author_extensions_charged"],
            name="accounting_policy.author_extensions_charged",
        ),
        "unique_preprocessing_charged": _exact_true(
            checked["unique_preprocessing_charged"],
            name="accounting_policy.unique_preprocessing_charged",
        ),
        "unused_allocation_transfer_permitted": _exact_false(
            checked["unused_allocation_transfer_permitted"],
            name="accounting_policy.unused_allocation_transfer_permitted",
        ),
        "post_result_top_up_permitted": _exact_false(
            checked["post_result_top_up_permitted"],
            name="accounting_policy.post_result_top_up_permitted",
        ),
    }


def _unpopulated_b08_values(value: object) -> Dict[str, bool]:
    checked = _exact_keys(
        value, UNPOPULATED_B08_VALUE_KEYS, name="unpopulated_b08_values"
    )
    return {
        key: _exact_false(
            checked[key], name=f"unpopulated_b08_values.{key}"
        )
        for key in UNPOPULATED_B08_VALUE_KEYS
    }


def validate_prospective_budget_record(record: object) -> Dict[str, object]:
    """Validate and detach one B06 prospective matched-compute record.

    The record carries stable references to future B08 calibration and ceiling
    records.  All corresponding value-assignment flags are required to remain
    false, making it impossible to smuggle a hardware or capacity claim into
    this B06-only surface.
    """

    checked = _exact_keys(record, _BUDGET_KEYS, name="budget record")
    schema = _identifier(checked["schema_version"], name="schema_version")
    if schema != PROSPECTIVE_BUDGET_SCHEMA_VERSION:
        raise MatchedTotalComputeError("budget schema_version differs")

    role = _identifier(checked["method_role"], name="method_role")
    if role not in (PRIMARY_METHOD_ROLE, PRIMARY_COMPARATOR_ROLE):
        raise MatchedTotalComputeError("method_role is not a primary-pair role")
    domain = _identifier(checked["domain_id"], name="domain_id")
    if domain not in DOMAIN_IDS:
        raise MatchedTotalComputeError("domain_id is outside the frozen roster")

    hard_axes = _identifier_record(
        checked["hard_axis_ceiling_ids"],
        HARD_AXES,
        name="hard_axis_ceiling_ids",
    )
    fairness = _identifier_record(
        checked["fairness_bindings"],
        FAIRNESS_BINDING_KEYS,
        name="fairness_bindings",
    )
    policy = _accounting_policy(checked["accounting_policy"])
    unpopulated = _unpopulated_b08_values(checked["unpopulated_b08_values"])

    return {
        "schema_version": schema,
        "budget_id": _identifier(checked["budget_id"], name="budget_id"),
        "method_id": _identifier(checked["method_id"], name="method_id"),
        "method_role": role,
        "domain_id": domain,
        "training_compute_budget_id": _identifier(
            checked["training_compute_budget_id"],
            name="training_compute_budget_id",
        ),
        "inference_compute_budget_id": _identifier(
            checked["inference_compute_budget_id"],
            name="inference_compute_budget_id",
        ),
        "calibration_weight_record_id": _identifier(
            checked["calibration_weight_record_id"],
            name="calibration_weight_record_id",
        ),
        "scalar_ceiling_id": _identifier(
            checked["scalar_ceiling_id"], name="scalar_ceiling_id"
        ),
        "hard_axis_ceiling_ids": hard_axes,
        "fairness_bindings": fairness,
        "accounting_policy": policy,
        "unpopulated_b08_values": unpopulated,
    }


def validate_primary_pair_equality(
    primary_method_budget: object,
    primary_comparator_budget: object,
) -> Dict[str, object]:
    """Require exact prospective compute equality for one primary pair."""

    method = validate_prospective_budget_record(primary_method_budget)
    comparator = validate_prospective_budget_record(primary_comparator_budget)
    if method["method_role"] != PRIMARY_METHOD_ROLE:
        raise MatchedTotalComputeError(
            "primary_method_budget does not have PRIMARY_METHOD role"
        )
    if comparator["method_role"] != PRIMARY_COMPARATOR_ROLE:
        raise MatchedTotalComputeError(
            "primary_comparator_budget does not have PRIMARY_COMPARATOR role"
        )
    if method["method_id"] == comparator["method_id"]:
        raise MatchedTotalComputeError("primary pair method IDs must differ")
    if method["budget_id"] == comparator["budget_id"]:
        raise MatchedTotalComputeError("primary pair budget record IDs must differ")

    for field in PRIMARY_PAIR_MATCHED_FIELDS:
        if method[field] != comparator[field]:
            raise MatchedTotalComputeError(
                f"primary pair prospective compute mismatch: {field}"
            )

    return {
        "schema_version": PRIMARY_PAIR_MATCH_SCHEMA_VERSION,
        "domain_id": method["domain_id"],
        "primary_method_id": method["method_id"],
        "primary_method_budget_id": method["budget_id"],
        "primary_comparator_id": comparator["method_id"],
        "primary_comparator_budget_id": comparator["budget_id"],
        "matched_fields": list(PRIMARY_PAIR_MATCHED_FIELDS),
        "equal_prospective_ceiling_and_selection_opportunity": True,
        "realized_resource_equality_claimed": False,
        "b08_resource_values_assigned": False,
    }


__all__ = [
    "ACCOUNTING_POLICY_KEYS",
    "CALCULATOR_ID",
    "DOMAIN_IDS",
    "FAIRNESS_BINDING_KEYS",
    "HARD_AXES",
    "MAX_ACCUMULATED_COMPONENT_BITS",
    "MAX_RATIONAL_COMPONENT_BITS",
    "MatchedTotalComputeError",
    "PHASES",
    "PRIMARY_COMPARATOR_ROLE",
    "PRIMARY_METHOD_ROLE",
    "PRIMARY_PAIR_MATCHED_FIELDS",
    "PRIMARY_PAIR_MATCH_SCHEMA_VERSION",
    "PROSPECTIVE_BUDGET_SCHEMA_VERSION",
    "RESOURCE_EVENTS",
    "UNPOPULATED_B08_VALUE_KEYS",
    "exact_compute_cost",
    "validate_primary_pair_equality",
    "validate_prospective_budget_record",
    "zero_resource_counts",
]
