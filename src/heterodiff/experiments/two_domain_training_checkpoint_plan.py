"""Exact pre-outcome two-domain training and checkpoint configuration.

This module is a configuration surface, not a trainer.  It derives the exact
method/domain roster and resource-count identities from the accepted B06
registry, freezes F139--F144 and F147, and exposes pure validators that a
future B12 runner must satisfy.  It performs no I/O, data access, randomness,
optimization, checkpoint writing, metric execution, or runtime observation.
"""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
import math
from typing import Dict, List, Mapping, Sequence, Tuple

from heterodiff.experiments import two_domain_baseline_registry as b06


SCHEMA = "HETERODIFF_F139_F144_F147_TRAINING_CHECKPOINT_PLAN_V1"
PLAN_ID = "TWO_DOMAIN_EXACT_TRAINING_CHECKPOINT_PLAN_V1"
CONTROL_PREDICATE = (
    "F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FROZEN_PREOUTCOME_V1"
)

PRIMARY_METRIC_ID = "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1"
PRODUCTION_INTEGRATION_ID = "F105_CKS_BINARY64_PROJECTION_V1"
F145_POLICY_VALUE = "DISABLED_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY"
F146_RULE_ID = "F146_EARLIEST_STEP_TIED_BEST_CANONICAL_CHECKPOINT_RULE_V1"
F148_PREDICATE = "NEVER_TRUE_NO_INFRASTRUCTURE_RERUN"

FIELD_IDS = ("F139", "F140", "F141", "F142", "F143", "F144", "F147")
FIELD_POINTERS = {
    "F139": "/training_and_checkpoint_plan/optimizer",
    "F140": "/training_and_checkpoint_plan/learning_rate_schedule",
    "F141": "/training_and_checkpoint_plan/precision",
    "F142": "/training_and_checkpoint_plan/batch_construction",
    "F143": "/training_and_checkpoint_plan/maximum_epochs_or_steps",
    "F144": "/training_and_checkpoint_plan/validation_metric",
    "F147": "/training_and_checkpoint_plan/maximum_tuning_trials_per_method",
}

F134_VALIDATION_GROUP_COUNT = 128
F136_DRAWS_PER_CASE = 64
F143_MAXIMUM_COMPLETED_OPTIMIZER_UPDATES = 4096
TUNING_COMPLETED_OPTIMIZER_UPDATES_PER_TRIAL = 1024
VALIDATION_CADENCE_COMPLETED_OPTIMIZER_UPDATES = 256
TRAINING_BATCH_SIZE = 16

OPTIMIZER_ID = "TORCH_ADAMW_EXACT_RATIONAL_SINGLE_GROUP_V1"
SCHEDULE_ID = "CONSTANT_CANDIDATE_BASE_RATE_NO_WARMUP_V1"
PRECISION_ID = "CPU_BINARY32_TRAIN_BINARY64_F105_VALIDATION_V1"
BATCH_POLICY_ID = "DOMAIN_LOCAL_CANONICAL_CYCLIC_EXACT16_NO_SHUFFLE_V1"
VALIDATION_POLICY_ID = "F105_COMPLETE_F134_BINARY64_EXACT_CHECKPOINT_RULE_V1"
TUNING_POLICY_ID = "B06_GRID_OR_SINGLETON_MAXIMUM_TRIALS_V1"

_HEX = frozenset("0123456789abcdef")
_GROUP_SCORE_KEYS = (
    "binary64_score_hex",
    "f105_factory_score_integrity_sha256",
    "formal_score_sha256",
    "group_id_sha256",
    "ordinal",
    "score_integrity_sha256",
    "symbolic_event_pair_work_units",
)
_VALIDATION_INPUT_KEYS = (
    "checkpoint_content_sha256",
    "complete_roster_certificate_subject_sha256",
    "completed_optimizer_updates",
    "domain_id",
    "executable_configuration_sha256",
    "group_roster_sha256",
    "group_scores",
    "method_id",
    "selection_unit_sha256",
)


class TrainingCheckpointPlanError(ValueError):
    """Raised when a plan or structural F144 receipt is not exact."""


def _validate_exact_json_tree(value: object, path: str = "$") -> None:
    if value is None or type(value) in (str, int, bool):
        return
    if type(value) is list:
        for index, member in enumerate(value):
            _validate_exact_json_tree(member, "{}[{}]".format(path, index))
        return
    if type(value) is dict:
        for key, member in value.items():
            if type(key) is not str:
                raise TypeError("{} contains a non-string key".format(path))
            _validate_exact_json_tree(member, "{}.{}".format(path, key))
        return
    raise TypeError("{} is outside the exact JSON tree".format(path))


def canonical_json_bytes(value: object) -> bytes:
    _validate_exact_json_tree(value)
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _domain_sha256(domain: str, value: object) -> str:
    if type(domain) is not str or not domain:
        raise TypeError("domain must be a nonempty exact string")
    return hashlib.sha256(domain.encode("ascii") + b"\0" + canonical_json_bytes(value)).hexdigest()


def _sha256(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise TrainingCheckpointPlanError("{} is not lowercase SHA-256".format(name))
    return value


def _fraction_record(numerator: int, denominator: int) -> Dict[str, int]:
    if type(numerator) is not int or type(denominator) is not int:
        raise TypeError("fraction components must be exact integers")
    value = Fraction(numerator, denominator)
    return {"denominator": value.denominator, "numerator": value.numerator}


def _derive_b06_adapter_rows() -> List[Dict[str, object]]:
    """Derive the exact 22 rows from B06; no B12 hardcoded roster is used."""

    registry = b06.validate_registry(deepcopy(b06.FROZEN_REGISTRY))
    rows: List[Dict[str, object]] = []

    for primary in registry["primary_pair"]:
        for domain_id in b06.DOMAIN_IDS:
            rows.append(
                {
                    "b06_config_sha256": primary["config_sha256"],
                    "domain_id": domain_id,
                    "method_id": primary["method_id"],
                    "registry_kind": "PRIMARY",
                }
            )

    for control in registry["controls"]:
        for domain_id in b06.DOMAIN_IDS:
            rows.append(
                {
                    "b06_config_sha256": control["config_sha256"],
                    "domain_id": domain_id,
                    "method_id": control["control_id"],
                    "registry_kind": "CONTROL",
                }
            )

    for family in registry["literature_families"]:
        for domain_id in b06.DOMAIN_IDS:
            implementation = family["implementation_by_domain"][domain_id]
            rows.append(
                {
                    "b06_config_sha256": implementation["config_sha256"],
                    "domain_id": domain_id,
                    "method_id": implementation["implementation_id"],
                    "registry_kind": "LITERATURE_FAMILY",
                }
            )

    for external in registry["external_baselines"]:
        rows.append(
            {
                "b06_config_sha256": external["config_sha256"],
                "domain_id": external["domain_id"],
                "method_id": external["method_id"],
                "registry_kind": "EXTERNAL_BASELINE",
            }
        )

    rows.sort(key=lambda row: (row["method_id"], row["domain_id"]))
    if len(rows) != 22 or len(
        {(row["method_id"], row["domain_id"]) for row in rows}
    ) != 22:
        raise TrainingCheckpointPlanError("B06 adapter roster is not exact-22")
    for row in rows:
        _sha256(row["b06_config_sha256"], "B06 configuration digest")
    return rows


@lru_cache(maxsize=1)
def _b06_adapter_rows_canonical() -> bytes:
    return canonical_json_bytes(_derive_b06_adapter_rows())


def _b06_adapter_rows() -> List[Dict[str, object]]:
    value = json.loads(_b06_adapter_rows_canonical().decode("ascii"))
    if type(value) is not list:
        raise TrainingCheckpointPlanError("cached B06 adapter roster differs")
    return value


def _derive_external_tuning_by_identity() -> Dict[Tuple[str, str], Dict[str, object]]:
    registry = b06.validate_registry(deepcopy(b06.FROZEN_REGISTRY))
    result: Dict[Tuple[str, str], Dict[str, object]] = {}
    for external in registry["external_baselines"]:
        budget = external["tuning_budget"]
        grid = deepcopy(budget["candidate_grid"])
        cardinality = 1
        for values in grid.values():
            if type(values) is not list or not values:
                raise TrainingCheckpointPlanError("B06 tuning grid is malformed")
            cardinality *= len(values)
        if cardinality != budget["maximum_trials"] or cardinality != b06.TUNING_TRIAL_LIMIT:
            raise TrainingCheckpointPlanError("B06 tuning grid/cardinality differs")
        result[(external["method_id"], external["domain_id"])] = {
            "candidate_grid": grid,
            "candidate_grid_sha256": budget["candidate_grid_sha256"],
            "maximum_trials": budget["maximum_trials"],
        }
    if len(result) != 2:
        raise TrainingCheckpointPlanError("B06 external tuning roster differs")
    return result


@lru_cache(maxsize=1)
def _external_tuning_canonical() -> bytes:
    derived = _derive_external_tuning_by_identity()
    rows = [
        {
            "candidate_grid": value["candidate_grid"],
            "candidate_grid_sha256": value["candidate_grid_sha256"],
            "domain_id": identity[1],
            "maximum_trials": value["maximum_trials"],
            "method_id": identity[0],
        }
        for identity, value in sorted(derived.items())
    ]
    return canonical_json_bytes(rows)


def _external_tuning_by_identity() -> Dict[Tuple[str, str], Dict[str, object]]:
    rows = json.loads(_external_tuning_canonical().decode("ascii"))
    return {
        (row["method_id"], row["domain_id"]): {
            "candidate_grid": row["candidate_grid"],
            "candidate_grid_sha256": row["candidate_grid_sha256"],
            "maximum_trials": row["maximum_trials"],
        }
        for row in rows
    }


def optimizer_value() -> Dict[str, object]:
    return {
        "algorithm": "ADAMW_DECOUPLED_WEIGHT_DECAY",
        "algorithm_class": "torch.optim.AdamW",
        "amsgrad": False,
        "beta1": _fraction_record(9, 10),
        "beta2": _fraction_record(999, 1000),
        "capturable": False,
        "differentiable": False,
        "epsilon": _fraction_record(1, 100_000_000),
        "foreach": False,
        "fused": False,
        "gradient_accumulation_steps": 1,
        "maximize": False,
        "one_optimizer_update_per_admitted_batch": True,
        "optimizer_id": OPTIMIZER_ID,
        "parameter_group_policy": "ONE_GROUP_ALL_AND_ONLY_TRAINABLE_PARAMETERS",
        "weight_decay": _fraction_record(0, 1),
    }


def learning_rate_schedule_value() -> Dict[str, object]:
    rows = []
    external = _external_tuning_by_identity()
    for adapter in _b06_adapter_rows():
        identity = (adapter["method_id"], adapter["domain_id"])
        if identity in external and "learning_rate" in external[identity]["candidate_grid"]:
            candidates = list(external[identity]["candidate_grid"]["learning_rate"])
            source = "EXACT_B06_EXTERNAL_TUNING_GRID"
        else:
            candidates = ["1/1000"]
            source = "F139_F144_F147_PLAN_FIXED_SINGLETON"
        rows.append(
            {
                "base_learning_rate_candidates_exact_rational": candidates,
                "b06_config_sha256": adapter["b06_config_sha256"],
                "domain_id": adapter["domain_id"],
                "method_id": adapter["method_id"],
                "rate_source": source,
            }
        )
    return {
        "adaptive_or_validation_driven_change_permitted": False,
        "learning_rate_multiplier": _fraction_record(1, 1),
        "schedule_id": SCHEDULE_ID,
        "schedule_kind": "CONSTANT_AT_SELECTED_PREDECLARED_CANDIDATE_BASE_RATE",
        "warmup_completed_optimizer_updates": 0,
        "rows": rows,
    }


def precision_value() -> Dict[str, object]:
    return {
        "autocast_permitted": False,
        "checkpoint_parameter_dtype": "IEEE754_BINARY32",
        "f105_group_score_representation": "IEEE754_BINARY64_HEX_BOUND",
        "f105_mean_aggregation": "EXACT_RATIONAL_OF_BINARY64_INPUTS_THEN_ONE_BINARY64_ROUND",
        "gradient_dtype": "IEEE754_BINARY32",
        "mixed_precision_permitted": False,
        "model_parameter_dtype": "IEEE754_BINARY32",
        "nonfinite_disposition": "TERMINAL_NONFINITE_NO_CHECKPOINT_ELIGIBILITY",
        "optimizer_moment_dtype": "IEEE754_BINARY32",
        "precision_id": PRECISION_ID,
        "tf32_permitted": False,
        "validation_equality": "EXACT_CANONICAL_BINARY64_HEX_IDENTITY_NO_TOLERANCE",
    }


def _batch_contract(adapter: Mapping[str, object]) -> Dict[str, object]:
    domain_id = adapter["domain_id"]
    logical_record_kind = (
        "ONE_PATIENT_TRAINING_RECORD"
        if domain_id == b06.PHYSIONET_DOMAIN_ID
        else "ONE_CUSTOMER_WINDOW_TRAINING_RECORD"
    )
    payload = {
        "b06_config_sha256": adapter["b06_config_sha256"],
        "batch_policy_id": BATCH_POLICY_ID,
        "batch_size_logical_records": TRAINING_BATCH_SIZE,
        "cross_domain_batch_permitted": False,
        "domain_id": domain_id,
        "drop_last": False,
        "implicit_or_random_shuffle_permitted": False,
        "logical_record_kind": logical_record_kind,
        "method_id": adapter["method_id"],
        "minimum_admitted_training_roster_size": TRAINING_BATCH_SIZE,
        "ordering": "CANONICAL_ASCENDING_TRAIN_RECORD_ID_BYTES",
        "record_index_formula": "(16*COMPLETED_OPTIMIZER_UPDATES+j)_MOD_N_FOR_j_0_TO_15",
        "roster_wrap_is_deterministic_not_padding": True,
        "seed_or_trial_mixing_permitted": False,
        "test_record_permitted": False,
        "training_and_validation_roles_may_not_mix_within_batch": True,
    }
    result = dict(payload)
    result["batch_contract_sha256"] = _domain_sha256(
        "heterodiff-f142-method-domain-batch-contract-v1", payload
    )
    return result


def batch_construction_value() -> Dict[str, object]:
    return {
        "batch_policy_id": BATCH_POLICY_ID,
        "b06_data_adapter_records_per_optimizer_update": TRAINING_BATCH_SIZE,
        "cross_domain_batch_permitted": False,
        "implicit_or_random_shuffle_permitted": False,
        "method_domain_contracts": [
            _batch_contract(adapter) for adapter in _b06_adapter_rows()
        ],
        "unadmitted_or_test_record_permitted": False,
    }


def validation_metric_value() -> Dict[str, object]:
    return {
        "aggregation": "ARITHMETIC_MEAN_OVER_COMPLETE_F134_VALIDATION_GROUP_ROSTER",
        "aggregation_arithmetic": (
            "EXACT_SUM_OF_BINARY64_AS_INTEGER_RATIOS_DIVIDED_BY_128_"
            "THEN_ONE_CORRECT_BINARY64_ROUND"
        ),
        "binary64_representation": "PYTHON_FLOAT_HEX_CANONICAL_FINITE_ONLY",
        "checkpoint_cadence": {
            "every_completed_optimizer_updates": VALIDATION_CADENCE_COMPLETED_OPTIMIZER_UPDATES,
            "terminal_f143_bound_included": True,
        },
        "checkpoint_eligibility": (
            "EXACT_CADENCE_AND_COMPLETE_128_GROUP_CERTIFICATE_AND_"
            "F105_FACTORY_RECORDS_AND_FINITE_AGGREGATE"
        ),
        "checkpoint_tie_rule": F146_RULE_ID,
        "complete_group_roster_certificate_required": True,
        "complete_roster_certificate_subject": (
            "BINDS_SELECTION_UNIT_METHOD_DOMAIN_EXECUTABLE_CONFIG_CHECKPOINT_"
            "F134_ROSTER_AND_ALL_128_BOUND_F105_SCORE_INTEGRITY_DIGESTS"
        ),
        "direction": "LOWER_IS_BETTER",
        "draw_count_per_group": F136_DRAWS_PER_CASE,
        "equality": "EXACT_CANONICAL_BINARY64_HEX_IDENTITY_NO_TOLERANCE",
        "f105_factory_record_requirement": (
            "EXACT_FACTORY_ISSUED_ProductionCKSScore_WITH_REVALIDATED_INTEGRITY"
        ),
        "f105_formal_score_interval": {"closed_lower": -2, "closed_upper": 1},
        "f105_production_boundary_policy": {
            "binary64_epsilon_multiples": 512,
            "outside_interval_plus_tolerance": "REFUSE",
            "within_tolerance_below_minus2": "CLAMP_TO_MINUS2",
            "within_tolerance_above_plus1": "CLAMP_TO_PLUS1",
        },
        "f134_validation_group_count": F134_VALIDATION_GROUP_COUNT,
        "f145_early_stopping": F145_POLICY_VALUE,
        "metric_id": PRIMARY_METRIC_ID,
        "nonfinite_group_or_aggregate_disposition": (
            "TERMINAL_NONFINITE_NO_CHECKPOINT_NO_FALLBACK"
        ),
        "production_integration_id": PRODUCTION_INTEGRATION_ID,
        "test_data_permitted": False,
        "pure_structural_helper_authenticates_production_history": False,
        "validation_policy_id": VALIDATION_POLICY_ID,
    }


def _tuning_row(adapter: Mapping[str, object]) -> Dict[str, object]:
    identity = (adapter["method_id"], adapter["domain_id"])
    external = _external_tuning_by_identity()
    if identity in external:
        tuning = external[identity]
        grid_kind = "EXACT_B06_EXTERNAL_GRID"
        grid_sha256 = tuning["candidate_grid_sha256"]
        maximum_trials = tuning["maximum_trials"]
    else:
        grid_kind = "EXACT_SINGLETON_FROZEN_B06_CONFIGURATION"
        grid_sha256 = adapter["b06_config_sha256"]
        maximum_trials = 1
    return {
        "b06_config_sha256": adapter["b06_config_sha256"],
        "b06_global_tuning_trial_ceiling": b06.TUNING_TRIAL_LIMIT,
        "candidate_grid_kind": grid_kind,
        "candidate_grid_or_singleton_sha256": grid_sha256,
        "domain_id": adapter["domain_id"],
        "failed_or_aborted_trials_charged": True,
        "maximum_trials": maximum_trials,
        "method_id": adapter["method_id"],
        "selection_data": "TRAIN_AND_VALIDATION_ONLY",
        "selection_metric": VALIDATION_POLICY_ID,
        "test_access_permitted": False,
        "tuning_completed_optimizer_updates_per_trial": (
            TUNING_COMPLETED_OPTIMIZER_UPDATES_PER_TRIAL
        ),
        "unused_transfer_or_postresult_topup_permitted": False,
    }


def maximum_tuning_trials_value() -> Dict[str, object]:
    return {
        "policy_id": TUNING_POLICY_ID,
        "rows": [_tuning_row(adapter) for adapter in _b06_adapter_rows()],
    }


def field_values() -> Dict[str, object]:
    return {
        "F139": optimizer_value(),
        "F140": learning_rate_schedule_value(),
        "F141": precision_value(),
        "F142": batch_construction_value(),
        "F143": F143_MAXIMUM_COMPLETED_OPTIMIZER_UPDATES,
        "F144": validation_metric_value(),
        "F147": maximum_tuning_trials_value(),
    }


def f144_semantics_sha256() -> str:
    return _domain_sha256(
        "heterodiff-f144-final-validation-semantics-v1",
        validation_metric_value(),
    )


def _executable_configuration_row(adapter: Mapping[str, object]) -> Dict[str, object]:
    schedule_rows = {
        (row["method_id"], row["domain_id"]): row
        for row in learning_rate_schedule_value()["rows"]
    }
    batch_rows = {
        (row["method_id"], row["domain_id"]): row
        for row in batch_construction_value()["method_domain_contracts"]
    }
    tuning_rows = {
        (row["method_id"], row["domain_id"]): row
        for row in maximum_tuning_trials_value()["rows"]
    }
    identity = (adapter["method_id"], adapter["domain_id"])
    payload = {
        "b06_config_sha256": adapter["b06_config_sha256"],
        "batch_contract_sha256": batch_rows[identity]["batch_contract_sha256"],
        "domain_id": adapter["domain_id"],
        "f143_completed_optimizer_update_bound": F143_MAXIMUM_COMPLETED_OPTIMIZER_UPDATES,
        "f144_semantics_sha256": f144_semantics_sha256(),
        "learning_rate_candidates_exact_rational": schedule_rows[identity][
            "base_learning_rate_candidates_exact_rational"
        ],
        "method_id": adapter["method_id"],
        "optimizer_id": OPTIMIZER_ID,
        "precision_id": PRECISION_ID,
        "registry_kind": adapter["registry_kind"],
        "schedule_id": SCHEDULE_ID,
        "tuning_maximum_trials": tuning_rows[identity]["maximum_trials"],
        "tuning_updates_per_trial": TUNING_COMPLETED_OPTIMIZER_UPDATES_PER_TRIAL,
    }
    result = dict(payload)
    result["executable_configuration_sha256"] = _domain_sha256(
        "heterodiff-f139-f144-f147-executable-method-domain-config-v1",
        payload,
    )
    return result


def executable_configuration_rows() -> List[Dict[str, object]]:
    return [
        _executable_configuration_row(adapter) for adapter in _b06_adapter_rows()
    ]


def field_closures() -> List[Dict[str, object]]:
    values = field_values()
    return [
        {
            "field_id": field_id,
            "json_pointer": FIELD_POINTERS[field_id],
            "status": "PROPOSED_CLOSED_ALL_OR_NOTHING_PENDING_INDEPENDENT_REVIEW",
            "value": deepcopy(values[field_id]),
        }
        for field_id in FIELD_IDS
    ]


def plan_semantics() -> Dict[str, object]:
    return {
        "control_predicate": CONTROL_PREDICATE,
        "effects": {
            "b08_closed": False,
            "b12_closed": False,
            "blocker_delta": 0,
            "field_delta": 7,
            "formal_test_delta": 0,
            "result_delta": 0,
            "runtime_or_science_executed": False,
            "timetable_task_delta": 1,
        },
        "executable_configuration_rows": executable_configuration_rows(),
        "f143_unit": "COMPLETED_OPTIMIZER_UPDATES",
        "f144_semantics_sha256": f144_semantics_sha256(),
        "f145_policy_value": F145_POLICY_VALUE,
        "f146_rule_id": F146_RULE_ID,
        "f148_predicate": F148_PREDICATE,
        "field_closures": field_closures(),
        "plan_id": PLAN_ID,
        "schema": SCHEMA,
        "source_boundary": (
            "PURE_CONFIGURATION_NO_IO_DATA_RANDOMNESS_TRAINING_CHECKPOINT_WRITE_"
            "METRIC_EXECUTION_RUNTIME_OR_CAPACITY_CLAIM"
        ),
    }


def plan_semantics_sha256() -> str:
    return _domain_sha256(
        "heterodiff-f139-f144-f147-plan-semantics-v1", plan_semantics()
    )


def validate_plan(value: object) -> Dict[str, object]:
    _validate_exact_json_tree(value)
    expected = plan_semantics()
    if canonical_json_bytes(value) != canonical_json_bytes(expected):
        raise TrainingCheckpointPlanError("training/checkpoint plan differs")
    return deepcopy(expected)


def _binary64_from_canonical_hex(value: object) -> float:
    if type(value) is not str or len(value) > 64:
        raise TrainingCheckpointPlanError("binary64 score hex is not exact")
    try:
        number = float.fromhex(value)
    except ValueError as error:
        raise TrainingCheckpointPlanError("binary64 score hex is invalid") from error
    if not math.isfinite(number) or number.hex() != value:
        raise TrainingCheckpointPlanError("binary64 score must be finite and canonical")
    if number < -2.0 or number > 1.0:
        raise TrainingCheckpointPlanError("binary64 F105 score is outside [-2,1]")
    return number


def validation_values_equal(left_hex: object, right_hex: object) -> bool:
    _binary64_from_canonical_hex(left_hex)
    _binary64_from_canonical_hex(right_hex)
    return left_hex == right_hex


def _group_roster_sha256(rows: Sequence[Mapping[str, object]]) -> str:
    return _domain_sha256(
        "heterodiff-f144-complete-f134-validation-group-roster-v1",
        [row["group_id_sha256"] for row in rows],
    )


def _f105_factory_integrity_sha256(
    *,
    binary64_score_hex: str,
    domain_id: str,
    formal_score_sha256: str,
    symbolic_event_pair_work_units: int,
) -> str:
    return _domain_sha256(
        "heterodiff-production-cks-score-v1",
        {
            "binary64_score_hex": binary64_score_hex,
            "domain_id": domain_id,
            "draw_count": F136_DRAWS_PER_CASE,
            "formal_score_sha256": formal_score_sha256,
            "integration_id": PRODUCTION_INTEGRATION_ID,
            "metric_id": PRIMARY_METRIC_ID,
            "score_direction": "LOWER_IS_BETTER",
            "symbolic_event_pair_work_units": symbolic_event_pair_work_units,
        },
    )


def _group_score_integrity_sha256(
    *,
    binary64_score_hex: str,
    checkpoint_content_sha256: str,
    domain_id: str,
    executable_configuration_sha256: str,
    f105_factory_score_integrity_sha256: str,
    group_id_sha256: str,
    method_id: str,
    ordinal: int,
    selection_unit_sha256: str,
) -> str:
    return _domain_sha256(
        "heterodiff-f144-bound-group-score-integrity-v1",
        {
            "binary64_score_hex": binary64_score_hex,
            "checkpoint_content_sha256": checkpoint_content_sha256,
            "domain_id": domain_id,
            "draw_count": F136_DRAWS_PER_CASE,
            "executable_configuration_sha256": executable_configuration_sha256,
            "f105_factory_score_integrity_sha256": (
                f105_factory_score_integrity_sha256
            ),
            "group_id_sha256": group_id_sha256,
            "integration_id": PRODUCTION_INTEGRATION_ID,
            "method_id": method_id,
            "metric_id": PRIMARY_METRIC_ID,
            "ordinal": ordinal,
            "selection_unit_sha256": selection_unit_sha256,
        },
    )


def complete_roster_certificate_subject_sha256(
    *,
    checkpoint_content_sha256: object,
    domain_id: object,
    executable_configuration_sha256: object,
    group_roster_sha256: object,
    group_score_integrity_sha256s: object,
    method_id: object,
    selection_unit_sha256: object,
) -> str:
    checkpoint_sha = _sha256(checkpoint_content_sha256, "checkpoint content digest")
    selection_sha = _sha256(selection_unit_sha256, "selection unit digest")
    executable_sha = _sha256(
        executable_configuration_sha256, "executable configuration digest"
    )
    roster_sha = _sha256(group_roster_sha256, "group roster digest")
    if type(method_id) is not str or not method_id:
        raise TrainingCheckpointPlanError("method_id is not exact")
    if type(domain_id) is not str or domain_id not in b06.DOMAIN_IDS:
        raise TrainingCheckpointPlanError("domain_id is not exact")
    if type(group_score_integrity_sha256s) is not list or len(
        group_score_integrity_sha256s
    ) != F134_VALIDATION_GROUP_COUNT:
        raise TrainingCheckpointPlanError("group-score digest roster is not exact-128")
    digests = [
        _sha256(digest, "group-score integrity digest")
        for digest in group_score_integrity_sha256s
    ]
    return _domain_sha256(
        "heterodiff-f144-complete-roster-certificate-subject-v1",
        {
            "checkpoint_content_sha256": checkpoint_sha,
            "domain_id": domain_id,
            "executable_configuration_sha256": executable_sha,
            "f134_validation_group_count": F134_VALIDATION_GROUP_COUNT,
            "f144_semantics_sha256": f144_semantics_sha256(),
            "group_roster_sha256": roster_sha,
            "group_score_integrity_sha256s": digests,
            "method_id": method_id,
            "selection_unit_sha256": selection_sha,
        },
    )


def validate_structural_checkpoint_validation(value: object) -> Dict[str, object]:
    """Validate an unauthenticated future F144 structural input.

    The return value proves only internal structure and arithmetic.  It says
    explicitly that production history, checkpoint custody, and the claimed
    validation roster are not authenticated by this pure helper.
    """

    _validate_exact_json_tree(value)
    if type(value) is not dict or tuple(value) != _VALIDATION_INPUT_KEYS:
        raise TrainingCheckpointPlanError("validation input keys/order differ")
    checkpoint_sha = _sha256(
        value["checkpoint_content_sha256"], "checkpoint content digest"
    )
    selection_sha = _sha256(
        value["selection_unit_sha256"], "selection unit digest"
    )
    method_id = value["method_id"]
    domain_id = value["domain_id"]
    executable_sha = _sha256(
        value["executable_configuration_sha256"],
        "executable configuration digest",
    )
    if type(method_id) is not str or not method_id:
        raise TrainingCheckpointPlanError("method_id is not exact")
    if type(domain_id) is not str or domain_id not in b06.DOMAIN_IDS:
        raise TrainingCheckpointPlanError("domain_id is not exact")
    matching = [
        row
        for row in executable_configuration_rows()
        if row["method_id"] == method_id and row["domain_id"] == domain_id
    ]
    if (
        len(matching) != 1
        or matching[0]["executable_configuration_sha256"] != executable_sha
    ):
        raise TrainingCheckpointPlanError("method/domain executable configuration differs")
    step = value["completed_optimizer_updates"]
    if (
        type(step) is not int
        or step <= 0
        or step > F143_MAXIMUM_COMPLETED_OPTIMIZER_UPDATES
        or step % VALIDATION_CADENCE_COMPLETED_OPTIMIZER_UPDATES != 0
    ):
        raise TrainingCheckpointPlanError("checkpoint is outside exact cadence")
    rows = value["group_scores"]
    if type(rows) is not list or len(rows) != F134_VALIDATION_GROUP_COUNT:
        raise TrainingCheckpointPlanError("group score roster is not exact-128")
    seen_groups = set()
    exact_sum = Fraction(0, 1)
    group_integrity_digests = []
    for ordinal, row in enumerate(rows):
        if type(row) is not dict or tuple(row) != _GROUP_SCORE_KEYS:
            raise TrainingCheckpointPlanError("group score keys/order differ")
        if type(row["ordinal"]) is not int or row["ordinal"] != ordinal:
            raise TrainingCheckpointPlanError("group score ordinal differs")
        group_sha = _sha256(row["group_id_sha256"], "group identity digest")
        formal_sha = _sha256(row["formal_score_sha256"], "formal score digest")
        factory_sha = _sha256(
            row["f105_factory_score_integrity_sha256"],
            "F105 factory score integrity digest",
        )
        work_units = row["symbolic_event_pair_work_units"]
        if (
            type(work_units) is not int
            or work_units < 0
            or work_units > 1_000_000_000
        ):
            raise TrainingCheckpointPlanError("symbolic event-pair work differs")
        if group_sha in seen_groups:
            raise TrainingCheckpointPlanError("validation group identity repeats")
        seen_groups.add(group_sha)
        score = _binary64_from_canonical_hex(row["binary64_score_hex"])
        expected_factory_sha = _f105_factory_integrity_sha256(
            binary64_score_hex=row["binary64_score_hex"],
            domain_id=domain_id,
            formal_score_sha256=formal_sha,
            symbolic_event_pair_work_units=work_units,
        )
        if factory_sha != expected_factory_sha:
            raise TrainingCheckpointPlanError("F105 factory score integrity differs")
        expected_group_sha = _group_score_integrity_sha256(
            binary64_score_hex=row["binary64_score_hex"],
            checkpoint_content_sha256=checkpoint_sha,
            domain_id=domain_id,
            executable_configuration_sha256=executable_sha,
            f105_factory_score_integrity_sha256=factory_sha,
            group_id_sha256=group_sha,
            method_id=method_id,
            ordinal=ordinal,
            selection_unit_sha256=selection_sha,
        )
        if row["score_integrity_sha256"] != expected_group_sha:
            raise TrainingCheckpointPlanError("bound group-score integrity differs")
        group_integrity_digests.append(expected_group_sha)
        numerator, denominator = score.as_integer_ratio()
        exact_sum += Fraction(numerator, denominator)
    roster_sha = _group_roster_sha256(rows)
    if value["group_roster_sha256"] != roster_sha:
        raise TrainingCheckpointPlanError("complete group roster digest differs")
    certificate_subject_sha = complete_roster_certificate_subject_sha256(
        checkpoint_content_sha256=checkpoint_sha,
        domain_id=domain_id,
        executable_configuration_sha256=executable_sha,
        group_roster_sha256=roster_sha,
        group_score_integrity_sha256s=group_integrity_digests,
        method_id=method_id,
        selection_unit_sha256=selection_sha,
    )
    if value["complete_roster_certificate_subject_sha256"] != certificate_subject_sha:
        raise TrainingCheckpointPlanError("complete-roster certificate subject differs")
    aggregate = float(exact_sum / F134_VALIDATION_GROUP_COUNT)
    if not math.isfinite(aggregate):
        raise TrainingCheckpointPlanError("validation aggregate is nonfinite")
    output_payload = {
        "aggregate_binary64_hex": aggregate.hex(),
        "checkpoint_content_sha256": checkpoint_sha,
        "complete_roster_certificate_subject_sha256": certificate_subject_sha,
        "completed_optimizer_updates": step,
        "domain_id": domain_id,
        "eligible_under_f144_structure": True,
        "executable_configuration_sha256": executable_sha,
        "f144_semantics_sha256": f144_semantics_sha256(),
        "group_roster_sha256": roster_sha,
        "method_id": method_id,
        "production_history_authenticated": False,
        "selection_unit_sha256": selection_sha,
    }
    result = dict(output_payload)
    result["structural_receipt_sha256"] = _domain_sha256(
        "heterodiff-f144-structural-checkpoint-validation-v1", output_payload
    )
    return result


__all__ = [
    "BATCH_POLICY_ID",
    "CONTROL_PREDICATE",
    "F134_VALIDATION_GROUP_COUNT",
    "F136_DRAWS_PER_CASE",
    "F143_MAXIMUM_COMPLETED_OPTIMIZER_UPDATES",
    "FIELD_IDS",
    "FIELD_POINTERS",
    "OPTIMIZER_ID",
    "PLAN_ID",
    "PRECISION_ID",
    "SCHEDULE_ID",
    "SCHEMA",
    "TRAINING_BATCH_SIZE",
    "TUNING_COMPLETED_OPTIMIZER_UPDATES_PER_TRIAL",
    "VALIDATION_CADENCE_COMPLETED_OPTIMIZER_UPDATES",
    "VALIDATION_POLICY_ID",
    "TrainingCheckpointPlanError",
    "canonical_json_bytes",
    "complete_roster_certificate_subject_sha256",
    "executable_configuration_rows",
    "f144_semantics_sha256",
    "field_closures",
    "field_values",
    "plan_semantics",
    "plan_semantics_sha256",
    "validate_plan",
    "validate_structural_checkpoint_validation",
    "validation_values_equal",
]
