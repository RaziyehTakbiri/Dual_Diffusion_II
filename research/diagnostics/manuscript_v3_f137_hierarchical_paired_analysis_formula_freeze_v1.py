"""Read-only validator and pure exact evaluator for the F137 formula freeze.

The evaluator accepts only caller-supplied synthetic exact values and explicit
index plans.  This module has no writer, RNG, network, connector, subprocess,
data, training, runtime, production, or scientific-execution route.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = (
    "heterodiff-manuscript-v3-f137-hierarchical-paired-analysis-formula-"
    "freeze-v1"
)
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = (
    "F137_PARAMETERIZED_NATURAL_GROUP_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_"
    "FROZEN_PREOUTCOME"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
REPORTED_DATE = "2026-09-01"
PACKAGE_KIND = "ADDITIVE_PREOUTCOME_EXACT_F137_FIELD_CLOSURE"
CONTROL_PREDICATE = STATE
FORMULA_ID = "F137_FIXED_ROSTER_CROSSED_HIERARCHICAL_PAIRED_BOOTSTRAP_V1"
F137_POINTER = "/power_and_seed_plan/hierarchical_paired_analysis_formula"

HUMAN_PATH = "PROJECT_F137_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_FREEZE.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.py"
)
PACKAGE_ROSTER = (HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)

MAX_EXACT_COMPONENT_BITS = 4096
MAX_EXACT_ACCUMULATED_BITS = 8192

POST_FIELDS = ("F164", "F165", "F168", "F169", "F170", "F171")
POST_CLOSED = ("F168", "F170", "F171")
POST_OPEN = ("F164", "F165", "F169")
PRE_FIELDS = tuple(
    "F" + str(index).zfill(3)
    for index in range(1, 173)
    if "F" + str(index).zfill(3) not in POST_FIELDS
)
CLOSED_BEFORE = (
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
CLOSED_AFTER = tuple(sorted(CLOSED_BEFORE + ("F137",)))
OPEN_BEFORE = tuple(field for field in PRE_FIELDS if field not in CLOSED_BEFORE)
OPEN_AFTER = tuple(field for field in PRE_FIELDS if field not in CLOSED_AFTER)

EVIDENCE_READY_REGISTRATION = (
    "Register only F137 "
    "(`/power_and_seed_plan/hierarchical_paired_analysis_formula`) as closed "
    "by the exact parameterized natural-group hierarchical paired-analysis "
    "formula and fixed-roster empirical one-plan resampling transform. "
    "Effective pre-execution counts move from 145 open / 21 closed to 144 "
    "open / 22 closed; post-execution counts remain 3 open / 3 closed, so "
    "totals move from 148 open / 24 closed to 147 open / 25 closed. F168, "
    "F170, and F171 retain their B11 closures; F164, F165, F169, B07, F112, "
    "F138, the primary metric, every weight, cardinality, seed, data, entropy, "
    "runtime, scientific result, Formal Test, and blocker remain open or "
    "unperformed."
)

FORMULA_VALUE: Mapping[str, Any] = {
    "formula_id": FORMULA_ID,
    "domain_scope": ["R3-PHYS", "R4-RETAIL"],
    "domains_evaluated_separately": True,
    "cross_domain_pooling_permitted": False,
    "paired_difference": "PRIMARY_SCORE_DIRECT_MINUS_PRIMARY_SCORE_GUIDE",
    "aggregation_order": [
        "UNWEIGHTED_MEAN_OVER_PAIRED_DRAWS_WITHIN_CASE",
        "EXACT_CASE_WEIGHTED_MEAN_WITHIN_NATURAL_GROUP",
        "EXACT_NATURAL_GROUP_WEIGHTED_MEAN_WITHIN_SEED",
        "EQUAL_MEAN_OVER_TRAINING_SEEDS",
    ],
    "point_estimator": (
        "THETA_D_EQUALS_MEAN_S_SUM_G_W_D_G_SUM_C_Q_D_G_C_MEAN_R_"
        "SCORE_DIRECT_MINUS_SCORE_GUIDE"
    ),
    "identity_and_address_contract": {
        "domain_ids": ["R3-PHYS", "R4-RETAIL"],
        "identity_encoding": "NONEMPTY_ASCII_BYTES_0X21_THROUGH_0X7E",
        "seed_ids_distinct_by_exact_bytes": True,
        "group_ids_distinct_by_exact_bytes": True,
        "case_ids_distinct_within_group_by_exact_bytes": True,
        "draw_ids_distinct_within_case_by_exact_bytes": True,
        "conditioning_ids_distinct_within_group_and_paired_one_to_one_with_cases": True,
        "conditioning_id_reuse_across_different_groups_or_domains_permitted": True,
        "direct_and_guide_row_keys": [
            "domain_id",
            "seed_id",
            "group_id",
            "case_id",
            "draw_id",
            "conditioning_id",
            "score",
        ],
        "row_order": "EXACT_SEED_THEN_GROUP_THEN_CASE_THEN_DRAW_ROSTER_PRODUCT",
        "direct_guide_addresses_and_conditioning_must_match_exactly": True,
        "missing_extra_duplicate_out_of_order_cross_domain_or_mispaired_row_permitted": False,
    },
    "weight_contract": {
        "group_weights": (
            "FUTURE_PREOUTCOME_STRICTLY_POSITIVE_EXACT_RATIONAL_SUM_EXACTLY_ONE"
        ),
        "case_weights": (
            "FUTURE_PREOUTCOME_STRICTLY_POSITIVE_EXACT_RATIONAL_SUM_EXACTLY_"
            "ONE_WITHIN_EACH_GROUP"
        ),
        "outcome_dependent_weights_permitted": False,
        "weights_populated_by_this_package": False,
    },
    "one_plan_bootstrap_law": {
        "seed_occurrence_count": "EXACTLY_CALLER_SUPPLIED_FUTURE_S_D",
        "seed_sampling": "IID_UNIFORM_WITH_REPLACEMENT_OVER_FROZEN_SEED_ROSTER",
        "group_occurrence_count": "EXACTLY_CALLER_SUPPLIED_FUTURE_G_D",
        "group_sampling": "IID_CATEGORICAL_W_D_G_WITH_REPLACEMENT",
        "case_occurrence_count_per_group": (
            "EXACTLY_CALLER_SUPPLIED_FUTURE_C_D_G_FOR_SELECTED_GROUP"
        ),
        "case_sampling": "IID_CATEGORICAL_Q_D_G_C_WITH_REPLACEMENT",
        "seed_group_multiplicities": "FULL_CARTESIAN_PRODUCT",
        "case_map_within_group_occurrence": (
            "ONE_MAP_SHARED_ACROSS_ALL_SELECTED_SEED_OCCURRENCES"
        ),
        "duplicate_group_occurrence_case_maps": "INDEPENDENT_BY_OCCURRENCE",
        "draw_sampling": "NEVER_RESAMPLED_ALWAYS_AVERAGED_WITHIN_CASE",
        "weights_reapplied_after_selection": False,
        "core_transform": "ONE_PLAN_TO_ONE_REPLICATE_APPLIED_INDEPENDENTLY",
        "caller_surface": "FINITE_NONEMPTY_TUPLE_OF_EXPLICIT_PLANS",
        "plan_count_chosen_recommended_defaulted_or_reported": False,
        "ordered_replicate_vector_returned": True,
        "replicate_formula": (
            "THETA_STAR_D_EQUALS_MEAN_OVER_SEED_AND_GROUP_OCCURRENCES_OF_"
            "UNWEIGHTED_MEAN_OVER_SELECTED_CASE_OCCURRENCES_OF_CASE_MEAN"
        ),
    },
    "interpretation": {
        "estimand_scope": "FINITE_EMPIRICAL_TRANSFORM_CONDITIONAL_ON_FROZEN_ROSTER",
        "unseen_group_superpopulation_claimed": False,
        "confidence_coverage_claimed": False,
        "training_seed_is_model_replication_unit": True,
        "seed_by_group_case_or_draw_treated_as_independent_seed": False,
    },
    "degenerate_and_failure_contract": {
        "minimum_complete_distinct_training_seeds": 2,
        "minimum_natural_groups": 1,
        "minimum_cases_per_group": 1,
        "minimum_draws_per_case": 1,
        "singleton_group_case_or_draw_layer": "ALLOWED_DETERMINISTIC_AND_FLAGGED",
        "zero_empirical_bootstrap_spread": (
            "VALID_FLAGGED_ALGEBRAIC_OUTPUT_NOT_PASS_FAIL_OR_INFERENCE"
        ),
        "invalid_input_disposition": "F137_INPUT_INVALID_TERMINAL_NO_GO",
        "drop_impute_replace_retry_topup_select_or_reweight_permitted": False,
        "fallback_or_alternate_analysis_permitted": False,
    },
    "parameterization_boundary": {
        "primary_metric_selected": False,
        "production_numeric_type_selected": False,
        "score_values_or_bounds_populated": False,
        "effect_margin_populated": False,
        "confidence_method_F112_selected": False,
        "resample_count_F138_selected": False,
        "weights_cardinalities_or_seed_values_populated": False,
        "data_entropy_runtime_or_science_performed": False,
    },
}


class ValidationError(ValueError):
    """Exact formula, schema, custody, or predecessor validation failed."""


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


def _predecessor_record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict or type(record.get("schema_version")) is not str:
        raise ValidationError("predecessor machine record has no exact schema")
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
        for index, item in enumerate(expected):
            _strict_equal(actual[index], item, label + "[" + str(index) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def _fraction_record(value: Fraction) -> Dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _exact_fraction(value: Any, label: str, *, positive: bool) -> Fraction:
    if type(value) is int:
        result = Fraction(value, 1)
    elif type(value) is Fraction:
        result = value
    else:
        raise ValidationError(label + " must be an exact int or Fraction")
    if positive and result <= 0:
        raise ValidationError(label + " must be strictly positive")
    if (
        result.numerator.bit_length() > MAX_EXACT_COMPONENT_BITS
        or result.denominator.bit_length() > MAX_EXACT_COMPONENT_BITS
    ):
        raise ValidationError(label + " exceeds the qualification bit bound")
    return result


def _checked_accumulated(value: Fraction, label: str) -> Fraction:
    if (
        value.numerator.bit_length() > MAX_EXACT_ACCUMULATED_BITS
        or value.denominator.bit_length() > MAX_EXACT_ACCUMULATED_BITS
    ):
        raise ValidationError(label + " exceeds the accumulated bit bound")
    return value


def _exact_index(value: Any, upper: int, label: str) -> int:
    if type(value) is not int:
        raise ValidationError(label + " must be an exact built-in integer")
    if value < 0 or value >= upper:
        raise ValidationError(label + " is out of range")
    return value


def _exact_tuple(value: Any, label: str) -> tuple:
    if type(value) is not tuple:
        raise ValidationError(label + " must be an exact tuple")
    return value


def _canonical_identity(value: Any, label: str) -> str:
    if type(value) is not str or not value:
        raise ValidationError(label + " must be a nonempty exact string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValidationError(label + " must be canonical ASCII") from error
    if any(byte < 0x21 or byte > 0x7E for byte in encoded):
        raise ValidationError(label + " must be printable ASCII without whitespace")
    return value


def _identity_tuple(value: Any, label: str, *, minimum: int) -> Tuple[str, ...]:
    row = _exact_tuple(value, label)
    if len(row) < minimum:
        raise ValidationError(label + " has too few identities")
    exact = tuple(
        _canonical_identity(item, label + "[" + str(index) + "]")
        for index, item in enumerate(row)
    )
    if len(set(exact)) != len(exact):
        raise ValidationError(label + " contains a duplicate or aliased identity")
    return exact


ROW_KEYS = (
    "domain_id",
    "seed_id",
    "group_id",
    "case_id",
    "draw_id",
    "conditioning_id",
    "score",
)


def _normalize_formula_inputs(
    domain_id: Any,
    seed_ids: Any,
    group_ids: Any,
    case_ids_by_group: Any,
    draw_ids_by_group_case: Any,
    conditioning_ids_by_group_case: Any,
    direct_rows: Any,
    guide_rows: Any,
    group_weights: Any,
    case_weights: Any,
) -> Tuple[
    Tuple[Tuple[Tuple[Fraction, ...], ...], ...],
    Fraction,
    Tuple[int, int, Tuple[int, ...], Tuple[Tuple[int, ...], ...]],
    Tuple[str, ...],
]:
    domain = _canonical_identity(domain_id, "domain_id")
    if domain not in ("R3-PHYS", "R4-RETAIL"):
        raise ValidationError("domain_id is outside the exact two-domain roster")
    seeds = _identity_tuple(seed_ids, "seed_ids", minimum=2)
    groups = _identity_tuple(group_ids, "group_ids", minimum=1)
    seed_count = len(seeds)
    group_count = len(groups)

    raw_case_rows = _exact_tuple(case_ids_by_group, "case_ids_by_group")
    if len(raw_case_rows) != group_count:
        raise ValidationError("case identity group roster mismatch")
    case_rosters = tuple(
        _identity_tuple(row, "case_ids_by_group[" + str(group_index) + "]", minimum=1)
        for group_index, row in enumerate(raw_case_rows)
    )
    case_counts = tuple(len(row) for row in case_rosters)

    raw_draw_group_rows = _exact_tuple(
        draw_ids_by_group_case, "draw_ids_by_group_case"
    )
    raw_conditioning_group_rows = _exact_tuple(
        conditioning_ids_by_group_case, "conditioning_ids_by_group_case"
    )
    if (
        len(raw_draw_group_rows) != group_count
        or len(raw_conditioning_group_rows) != group_count
    ):
        raise ValidationError("draw or conditioning group roster mismatch")
    draw_rosters: List[Tuple[Tuple[str, ...], ...]] = []
    conditioning_rosters: List[Tuple[str, ...]] = []
    for group_index, case_roster in enumerate(case_rosters):
        draw_case_rows = _exact_tuple(
            raw_draw_group_rows[group_index], "draw case roster"
        )
        conditioning_row = _exact_tuple(
            raw_conditioning_group_rows[group_index], "conditioning case roster"
        )
        if (
            len(draw_case_rows) != len(case_roster)
            or len(conditioning_row) != len(case_roster)
        ):
            raise ValidationError("draw or conditioning case roster mismatch")
        exact_draw_rows: List[Tuple[str, ...]] = []
        exact_conditioning: List[str] = []
        for case_index in range(len(case_roster)):
            exact_draw_rows.append(
                _identity_tuple(
                    draw_case_rows[case_index],
                    "draw_ids_by_group_case["
                    + str(group_index)
                    + "]["
                    + str(case_index)
                    + "]",
                    minimum=1,
                )
            )
            exact_conditioning.append(
                _canonical_identity(
                    conditioning_row[case_index], "conditioning identity"
                )
            )
        if len(set(exact_conditioning)) != len(exact_conditioning):
            raise ValidationError(
                "conditioning identities must be unique within each natural group"
            )
        draw_rosters.append(tuple(exact_draw_rows))
        conditioning_rosters.append(tuple(exact_conditioning))
    exact_draw_rosters = tuple(draw_rosters)
    exact_conditioning_rosters = tuple(conditioning_rosters)
    draw_counts = tuple(
        tuple(len(draws) for draws in group) for group in exact_draw_rosters
    )

    expected_addresses: List[Tuple[str, str, str, str, str, str]] = []
    for seed in seeds:
        for group_index, group in enumerate(groups):
            for case_index, case in enumerate(case_rosters[group_index]):
                conditioning = exact_conditioning_rosters[group_index][case_index]
                for draw in exact_draw_rosters[group_index][case_index]:
                    expected_addresses.append(
                        (domain, seed, group, case, draw, conditioning)
                    )

    direct = _exact_tuple(direct_rows, "direct_rows")
    guide = _exact_tuple(guide_rows, "guide_rows")
    if len(direct) != len(expected_addresses) or len(guide) != len(expected_addresses):
        raise ValidationError("direct/guide row count does not match the roster product")
    paired_differences: List[Fraction] = []
    for row_index, expected_address in enumerate(expected_addresses):
        direct_row = direct[row_index]
        guide_row = guide[row_index]
        if type(direct_row) is not dict or tuple(direct_row) != ROW_KEYS:
            raise ValidationError("direct row key roster or order mismatch")
        if type(guide_row) is not dict or tuple(guide_row) != ROW_KEYS:
            raise ValidationError("guide row key roster or order mismatch")
        direct_address = tuple(direct_row[key] for key in ROW_KEYS[:-1])
        guide_address = tuple(guide_row[key] for key in ROW_KEYS[:-1])
        if any(type(value) is not str for value in direct_address + guide_address):
            raise ValidationError("row address values must be exact strings")
        if direct_address != expected_address:
            raise ValidationError("direct row address is missing, extra, duplicate, or out of order")
        if guide_address != expected_address or guide_address != direct_address:
            raise ValidationError("direct/guide address or conditioning pairing mismatch")
        direct_value = _exact_fraction(
            direct_row["score"], "direct score", positive=False
        )
        guide_value = _exact_fraction(
            guide_row["score"], "guide score", positive=False
        )
        paired_differences.append(
            _checked_accumulated(
                direct_value - guide_value, "paired score difference"
            )
        )

    paired_case_means: List[Tuple[Tuple[Fraction, ...], ...]] = []
    cursor = 0
    for _seed_index in range(seed_count):
        seed_means: List[Tuple[Fraction, ...]] = []
        for group_index in range(group_count):
            group_means: List[Fraction] = []
            for case_index in range(case_counts[group_index]):
                draw_count = draw_counts[group_index][case_index]
                draw_total = Fraction(0, 1)
                for _draw_index in range(draw_count):
                    draw_total = _checked_accumulated(
                        draw_total + paired_differences[cursor],
                        "paired draw accumulation",
                    )
                    cursor += 1
                group_means.append(
                    _checked_accumulated(draw_total / draw_count, "paired case mean")
                )
            seed_means.append(tuple(group_means))
        paired_case_means.append(tuple(seed_means))
    if cursor != len(paired_differences):
        raise ValidationError("paired row cursor did not consume the exact roster")

    group_weight_values = _exact_tuple(group_weights, "group_weights")
    if len(group_weight_values) != group_count:
        raise ValidationError("group weight roster mismatch")
    exact_group_weights = tuple(
        _exact_fraction(value, "group weight", positive=True)
        for value in group_weight_values
    )
    if sum(exact_group_weights, Fraction(0, 1)) != 1:
        raise ValidationError("group weights must sum exactly to one")

    case_weight_rows = _exact_tuple(case_weights, "case_weights")
    if len(case_weight_rows) != group_count:
        raise ValidationError("case weight group roster mismatch")
    exact_case_weights: List[Tuple[Fraction, ...]] = []
    for group_index, row in enumerate(case_weight_rows):
        row_tuple = _exact_tuple(row, "case weight row")
        if len(row_tuple) != case_counts[group_index]:
            raise ValidationError("case weight roster mismatch")
        exact_row = tuple(
            _exact_fraction(value, "case weight", positive=True)
            for value in row_tuple
        )
        if sum(exact_row, Fraction(0, 1)) != 1:
            raise ValidationError("case weights must sum exactly to one")
        exact_case_weights.append(exact_row)

    point_total = Fraction(0, 1)
    for seed_index in range(seed_count):
        seed_total = Fraction(0, 1)
        for group_index in range(group_count):
            group_total = Fraction(0, 1)
            for case_index in range(case_counts[group_index]):
                group_total = _checked_accumulated(
                    group_total
                    + exact_case_weights[group_index][case_index]
                    * paired_case_means[seed_index][group_index][case_index],
                    "case-weighted group accumulation",
                )
            seed_total = _checked_accumulated(
                seed_total + exact_group_weights[group_index] * group_total,
                "group-weighted seed accumulation",
            )
        point_total = _checked_accumulated(
            point_total + seed_total, "seed accumulation"
        )
    point_estimate = _checked_accumulated(
        point_total / seed_count, "point estimate"
    )

    degenerate: List[str] = []
    if group_count == 1:
        degenerate.append("SINGLETON_NATURAL_GROUP_LAYER")
    if any(count == 1 for count in case_counts):
        degenerate.append("SINGLETON_CASE_LAYER_PRESENT")
    if any(count == 1 for group in draw_counts for count in group):
        degenerate.append("SINGLETON_DRAW_LAYER_PRESENT")
    dimensions = (seed_count, group_count, case_counts, draw_counts)
    return tuple(paired_case_means), point_estimate, dimensions, tuple(degenerate)


PLAN_KEYS = (
    "seed_indices",
    "group_indices",
    "case_indices_by_group_occurrence",
)


def _replicate_from_normalized(
    case_means: Tuple[Tuple[Tuple[Fraction, ...], ...], ...],
    dimensions: Tuple[int, int, Tuple[int, ...], Tuple[Tuple[int, ...], ...]],
    plan: Any,
) -> Fraction:
    seed_count, group_count, case_counts, _ = dimensions
    if type(plan) is not dict or tuple(plan) != PLAN_KEYS:
        raise ValidationError("bootstrap plan key roster or order mismatch")
    seed_indices = _exact_tuple(plan["seed_indices"], "seed_indices")
    group_indices = _exact_tuple(plan["group_indices"], "group_indices")
    case_maps = _exact_tuple(
        plan["case_indices_by_group_occurrence"],
        "case_indices_by_group_occurrence",
    )
    if len(seed_indices) != seed_count:
        raise ValidationError("seed occurrence count must equal S")
    if len(group_indices) != group_count:
        raise ValidationError("group occurrence count must equal G")
    if len(case_maps) != group_count:
        raise ValidationError("one case map is required per group occurrence")
    exact_seed_indices = tuple(
        _exact_index(value, seed_count, "seed index") for value in seed_indices
    )
    exact_group_indices = tuple(
        _exact_index(value, group_count, "group index") for value in group_indices
    )
    exact_case_maps: List[Tuple[int, ...]] = []
    for occurrence, row in enumerate(case_maps):
        row_tuple = _exact_tuple(row, "case map")
        selected_group = exact_group_indices[occurrence]
        selected_case_count = case_counts[selected_group]
        if len(row_tuple) != selected_case_count:
            raise ValidationError("case occurrence count must equal selected C_g")
        exact_case_maps.append(
            tuple(
                _exact_index(value, selected_case_count, "case index")
                for value in row_tuple
            )
        )

    total = Fraction(0, 1)
    for seed_index in exact_seed_indices:
        for occurrence, group_index in enumerate(exact_group_indices):
            case_total = Fraction(0, 1)
            for case_index in exact_case_maps[occurrence]:
                case_total = _checked_accumulated(
                    case_total + case_means[seed_index][group_index][case_index],
                    "bootstrap case accumulation",
                )
            total = _checked_accumulated(
                total + case_total / case_counts[group_index],
                "bootstrap seed-group accumulation",
            )
    return _checked_accumulated(
        total / (seed_count * group_count), "bootstrap replicate"
    )


def exact_hierarchical_paired_analysis(
    domain_id: Any,
    seed_ids: Any,
    group_ids: Any,
    case_ids_by_group: Any,
    draw_ids_by_group_case: Any,
    conditioning_ids_by_group_case: Any,
    direct_rows: Any,
    guide_rows: Any,
    group_weights: Any,
    case_weights: Any,
    bootstrap_plans: Any,
) -> Dict[str, Any]:
    """Evaluate F137 on exact synthetic rows and explicit caller plans.

    Each plan is transformed independently. The function neither generates,
    chooses, recommends, defaults, nor reports a plan count, and it draws no
    inferential conclusion from the returned vector.
    """

    case_means, point_estimate, dimensions, degenerate = _normalize_formula_inputs(
        domain_id,
        seed_ids,
        group_ids,
        case_ids_by_group,
        draw_ids_by_group_case,
        conditioning_ids_by_group_case,
        direct_rows,
        guide_rows,
        group_weights,
        case_weights,
    )
    plans = _exact_tuple(bootstrap_plans, "bootstrap_plans")
    if not plans:
        raise ValidationError("at least one explicit caller plan is required")
    replicates = tuple(
        _replicate_from_normalized(case_means, dimensions, plan) for plan in plans
    )
    zero_spread = all(value == replicates[0] for value in replicates)
    flags = list(degenerate)
    if zero_spread:
        flags.append("ZERO_EMPIRICAL_BOOTSTRAP_SPREAD")
    return {
        "formula_id": FORMULA_ID,
        "domain_id": domain_id,
        "dimensions": {
            "training_seeds": dimensions[0],
            "natural_groups": dimensions[1],
            "cases_by_group": list(dimensions[2]),
            "draws_by_group_case": [list(row) for row in dimensions[3]],
        },
        "point_estimate": _fraction_record(point_estimate),
        "bootstrap_replicates": [_fraction_record(value) for value in replicates],
        "zero_empirical_bootstrap_spread": zero_spread,
        "flags": flags,
        "identity_roster_validated": True,
        "direct_guide_pairing_validated": True,
        "draws_resampled": False,
        "weights_reapplied_after_selection": False,
        "plan_count_chosen_recommended_defaulted_or_reported": False,
        "confidence_interval_or_decision_produced": False,
    }


# group, role, path, byte count, raw SHA-256, optional semantic self-digest
PREDECESSOR_SPECS: Tuple[
    Tuple[str, str, str, int, str, Optional[str]], ...
] = (
    (
        "ANTI_DRIFT_POLICY",
        "human",
        "PROJECT_ANTI_DRIFT_OPERATING_POLICY.md",
        2240,
        "22f1006bfd0b4dde8eb51e6e30abd7b153882a3fd41d6f3a3494ffd98a98bbd3",
        None,
    ),
    (
        "EXECUTION_PREREGISTRATION",
        "human",
        "manuscript_v3/execution_preregistration.md",
        22491,
        "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
        None,
    ),
    (
        "EXECUTION_PREREGISTRATION",
        "machine",
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        39771,
        "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
        None,
    ),
    (
        "PREEXECUTION_CLOSURE_V2",
        "human",
        "manuscript_v3/execution_preregistration_preexecution_closure_v2.md",
        14938,
        "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d",
        None,
    ),
    (
        "PREEXECUTION_CLOSURE_V2",
        "machine",
        "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
        24571,
        "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
        "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4",
    ),
    (
        "POWER_ALLOCATION_ROUTE_V1",
        "human",
        "PROJECT_REAL_DOMAIN_POWER_ALLOCATION_ROUTE.md",
        15223,
        "a8edf99303e30b6ae6ea9912dce6350fadc9e07361fcd25743c03446a2bb0139",
        None,
    ),
    (
        "POWER_ALLOCATION_ROUTE_V1",
        "machine",
        "research/fixtures/manuscript_v3_real_domain_power_allocation_route_v1.json",
        15915,
        "536493388d23aac2cc3aaf6f9bdc34a12fba77103e9546cbf110c1c8223dfd28",
        "3846714fca604b3a0a5f05702326b8fd6856f08639bda51a1b7a7dad8a44eef4",
    ),
    (
        "POWER_ALLOCATION_ROUTE_V1",
        "validator",
        "research/diagnostics/manuscript_v3_real_domain_power_allocation_route_v1.py",
        36100,
        "be5bcf6cde26d1c4eff044f6fad4705c1e87c850c77f38b2a4f7ef670a03b129",
        None,
    ),
    (
        "POWER_ALLOCATION_ROUTE_V1",
        "test",
        "tests/unit/test_manuscript_v3_real_domain_power_allocation_route_v1.py",
        19344,
        "3c0846ecd924f4e39f7a98414755fdc06c2c1e5d60491879fa4190f5730b9926",
        None,
    ),
    (
        "PILOT_VARIANCE_STRATEGY_V1",
        "human",
        "PROJECT_PILOT_VARIANCE_POWER_STRATEGY_DRAFT.md",
        11609,
        "def13998bba651bf3737288079e8a79e1b7221a8aab680cf67ef248f785ed1ba",
        None,
    ),
    (
        "PILOT_VARIANCE_STRATEGY_V1",
        "machine",
        "research/fixtures/manuscript_v3_pilot_variance_power_strategy_draft_v1.json",
        8423,
        "4a01541ff60be7b0d5ef875aa7af0d646d24754d4ffb3027fb5eb65f43b7ee58",
        "883f673d99083cfb0c8aae87a718eb12f2a9c3e3bc7bd92537f725267a86b031",
    ),
    (
        "PILOT_VARIANCE_STRATEGY_V1",
        "validator",
        "research/diagnostics/manuscript_v3_pilot_variance_power_strategy_draft_v1.py",
        18533,
        "d55c6cc29bb5905623bf81bc467a35da96a67f9a0c9f7dc767e2eb646fe76c2a",
        None,
    ),
    (
        "PILOT_VARIANCE_STRATEGY_V1",
        "test",
        "tests/unit/test_manuscript_v3_pilot_variance_power_strategy_draft_v1.py",
        11737,
        "15b480991c9363d1050952015635f480a75c770ed517a42d5ae9a9f94b106229",
        None,
    ),
    (
        "GATE_A_LOCAL_STATISTICAL_FREEZE_V1",
        "human",
        "PROJECT_GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISION_FREEZE.md",
        8073,
        "ca9a593c54a9d3587f58a3d414defd5cf81a3765395d5ebb8494e6effa6dd44d",
        None,
    ),
    (
        "GATE_A_LOCAL_STATISTICAL_FREEZE_V1",
        "machine",
        "research/fixtures/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json",
        8455,
        "b8a74f1131f85aa1b7497f2f43bd34a0e30bc471953c935d4362a5a8dea1446a",
        "aa3fe845190d6c74472706749598ba245de1925ce03a5702d1d2eed81a88bffa",
    ),
    (
        "GATE_A_LOCAL_STATISTICAL_FREEZE_V1",
        "validator",
        "research/diagnostics/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.py",
        22410,
        "3769017b9d6e2b1d2e1f876a84d5cfb49ccb9160e2505338ce5095b03bf790c5",
        None,
    ),
    (
        "GATE_A_LOCAL_STATISTICAL_FREEZE_V1",
        "test",
        "tests/unit/test_manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.py",
        28454,
        "82955f1d0cfefeef439e63ebf1cc8d478225b6529485257ccdb7a5d402d245e7",
        None,
    ),
    (
        "F104_COUNT_ANCHOR_V1",
        "human",
        "PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md",
        9596,
        "4d73909714e5227175b8c0f250876ffeddcd25ad9cc4d54b27d02499c562edfb",
        None,
    ),
    (
        "F104_COUNT_ANCHOR_V1",
        "machine",
        "research/fixtures/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json",
        12639,
        "c6275a6fb6941b28c2b0ed89196efdfeeba5530d8cabe47f173452cda364af54",
        "ba1c3a7898c858ec7cf7b3073c869a134cd8a06b93aeb0f7778793c271c96d7b",
    ),
    (
        "F104_COUNT_ANCHOR_V1",
        "validator",
        "research/diagnostics/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py",
        33938,
        "817a64acaf2441314ad73190569bd969c304a9b1d01fc7533d7fdfc6dad1734b",
        None,
    ),
    (
        "F104_COUNT_ANCHOR_V1",
        "test",
        "tests/unit/test_manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py",
        30095,
        "5ef4f22b71f24f980f9553c7e32f7de912ab85c23328b4d42019d2ae107e7693",
        None,
    ),
    (
        "F104_COUNT_ANCHOR_V1",
        "independent_review",
        "PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE_INDEPENDENT_REVIEW.md",
        10230,
        "7694694d7fe2b0c2dd17f79b9e0f9d2f44c14c59c3f0568902e3cad7d75ae402",
        None,
    ),
    (
        "B11_POSTEXECUTION_COUNT_ANCHOR_V1",
        "human",
        "PROJECT_B11_PREOUTCOME_AUDIT_PLAN_FREEZE.md",
        15878,
        "1b9cb20bde42b97967a1cc0ea4ee4e2d91f8be6f42f813271eaab1531ef877e9",
        None,
    ),
    (
        "B11_POSTEXECUTION_COUNT_ANCHOR_V1",
        "machine",
        "research/fixtures/manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.json",
        23299,
        "d5770caedfd50858040eae696f9c6174f0a34266efa4c685102df7e51f8a01ff",
        "55455c716dfe09284c94ccd465919b5080423e7535e514daeee928081313f9a4",
    ),
    (
        "B11_POSTEXECUTION_COUNT_ANCHOR_V1",
        "validator",
        "research/diagnostics/manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.py",
        42156,
        "224a1ca34b806e26077ceecd78aa2b57c2189c5e4c5be7447dc82ee6ae256070",
        None,
    ),
    (
        "B11_POSTEXECUTION_COUNT_ANCHOR_V1",
        "test",
        "tests/unit/test_manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.py",
        37589,
        "790c0cec8f8f5ca565ce0edf7f76441216384b9eb45e6a44bbcc41744db9372f",
        None,
    ),
    (
        "B11_POSTEXECUTION_COUNT_ANCHOR_V1",
        "independent_review",
        "PROJECT_B11_PREOUTCOME_AUDIT_PLAN_FREEZE_INDEPENDENT_REVIEW.md",
        13072,
        "0491763f2db016e957de0023f0ca92b9d5e1a8f1b02c87320625826f25b372c6",
        None,
    ),
    (
        "PHYSIONET_PATIENT_GROUP_CARRIER_V1",
        "human",
        "PROJECT_PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN.md",
        10761,
        "2d84753fe87032a81d377a469f858f1702b14474371bfd2d147fd87824bb4b7a",
        None,
    ),
    (
        "PHYSIONET_PATIENT_GROUP_CARRIER_V1",
        "machine",
        "research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json",
        16543,
        "a9fc01ae42ba7942e6c61def5120d6497b74fc99c82b0c5b68188f221b4b68a8",
        None,
    ),
    (
        "PHYSIONET_PATIENT_GROUP_CARRIER_V1",
        "validator",
        "research/diagnostics/manuscript_v3_physionet_patient_disjoint_split_design_v1.py",
        35894,
        "429e4e9291bb42172a6de3b664b13938a537a8840e14ab0f8f4d6e963072a91e",
        None,
    ),
    (
        "PHYSIONET_PATIENT_GROUP_CARRIER_V1",
        "test",
        "tests/unit/test_manuscript_v3_physionet_patient_disjoint_split_design_v1.py",
        15720,
        "10faf21f66129330eef239ca3e561ecbddee78779a4849e5d60df07624c59982",
        None,
    ),
    (
        "RETAIL_CUSTOMER_GROUP_CARRIER_V1",
        "human",
        "PROJECT_RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN.md",
        11226,
        "49a38fbe8bfdbc2fcb93de766f7280ba8affd18b2ebedbcc004d079550b752d1",
        None,
    ),
    (
        "RETAIL_CUSTOMER_GROUP_CARRIER_V1",
        "machine",
        "research/fixtures/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json",
        13409,
        "b27086c5979d2f7018b4b8b50b3fffacf03b3fe2691d60567bc42b179d53e98b",
        "0aa3b6e992ade5343b0d840b382e544ecf5140e352b97a508f359a2fa0d0bed2",
    ),
    (
        "RETAIL_CUSTOMER_GROUP_CARRIER_V1",
        "validator",
        "research/diagnostics/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py",
        38492,
        "c377c87ae74ee3a4bfc0dd8f695e0df3531c3eec2c080f5b81379e852424a22e",
        None,
    ),
    (
        "RETAIL_CUSTOMER_GROUP_CARRIER_V1",
        "test",
        "tests/unit/test_manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py",
        24025,
        "99ecada07b8325b25e7d227bf9bb5c6e38957619115a7040c636dbdc33cb7109",
        None,
    ),
)

PREDECESSOR_GROUP_COUNTS = {
    "ANTI_DRIFT_POLICY": 1,
    "EXECUTION_PREREGISTRATION": 2,
    "PREEXECUTION_CLOSURE_V2": 2,
    "POWER_ALLOCATION_ROUTE_V1": 4,
    "PILOT_VARIANCE_STRATEGY_V1": 4,
    "GATE_A_LOCAL_STATISTICAL_FREEZE_V1": 4,
    "F104_COUNT_ANCHOR_V1": 5,
    "B11_POSTEXECUTION_COUNT_ANCHOR_V1": 5,
    "PHYSIONET_PATIENT_GROUP_CARRIER_V1": 4,
    "RETAIL_CUSTOMER_GROUP_CARRIER_V1": 4,
    "total": 35,
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


def _fingerprint(value: os.stat_result) -> Tuple[int, int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        value.st_mode,
        value.st_nlink,
    )


def _validate_leaf_status(value: os.stat_result, label: str) -> None:
    if not stat.S_ISREG(value.st_mode):
        raise ValidationError(label + " must be a regular file")
    if stat.S_IMODE(value.st_mode) != 0o644:
        raise ValidationError(label + " mode must be exactly 0644")
    if value.st_nlink != 1:
        raise ValidationError(label + " must have exactly one hard link")


def _stable_read(root: Path, relative: str) -> bytes:
    if not isinstance(root, Path) or not root.is_absolute():
        raise ValidationError("workspace root must be an absolute Path")
    parts = _canonical_relative_path(relative)
    descriptors: List[int] = []
    namespace_rows: List[Tuple[int, str, Tuple[int, ...]]] = []
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    root_before = root.lstat()
    try:
        root_fd = os.open(str(root), os.O_RDONLY | directory | nofollow | cloexec)
        descriptors.append(root_fd)
        root_open = os.fstat(root_fd)
        if (
            stat.S_ISLNK(root_before.st_mode)
            or not stat.S_ISDIR(root_before.st_mode)
            or _fingerprint(root_before) != _fingerprint(root_open)
        ):
            raise ValidationError("workspace root identity mismatch")
        parent_fd = root_fd
        for component in parts[:-1]:
            entry_before = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            child_fd = os.open(
                component,
                os.O_RDONLY | directory | nofollow | cloexec,
                dir_fd=parent_fd,
            )
            descriptors.append(child_fd)
            child_status = os.fstat(child_fd)
            if (
                stat.S_ISLNK(entry_before.st_mode)
                or not stat.S_ISDIR(entry_before.st_mode)
                or _fingerprint(entry_before) != _fingerprint(child_status)
            ):
                raise ValidationError("unsafe or changed path component")
            namespace_rows.append((parent_fd, component, _fingerprint(entry_before)))
            parent_fd = child_fd

        leaf = parts[-1]
        entry_before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        _validate_leaf_status(entry_before, "before-path binding")
        leaf_fd = os.open(
            leaf, os.O_RDONLY | nofollow | cloexec, dir_fd=parent_fd
        )
        descriptors.append(leaf_fd)
        before_fd = os.fstat(leaf_fd)
        _validate_leaf_status(before_fd, "before-descriptor binding")
        if (
            stat.S_ISLNK(entry_before.st_mode)
            or _fingerprint(entry_before) != _fingerprint(before_fd)
        ):
            raise ValidationError("binding must be a stable regular file")
        namespace_rows.append((parent_fd, leaf, _fingerprint(entry_before)))

        chunks: List[bytes] = []
        while True:
            chunk = os.read(leaf_fd, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(leaf_fd)
        _validate_leaf_status(after_fd, "after-descriptor binding")
        if _fingerprint(before_fd) != _fingerprint(after_fd):
            raise ValidationError("binding changed during descriptor read")
        for saved_parent, component, expected in namespace_rows:
            current = os.stat(
                component, dir_fd=saved_parent, follow_symlinks=False
            )
            if component == leaf and saved_parent == parent_fd:
                _validate_leaf_status(current, "after-path binding")
            if _fingerprint(current) != expected:
                raise ValidationError("binding namespace changed during read")
        root_after = root.lstat()
        if _fingerprint(root_before) != _fingerprint(root_after):
            raise ValidationError("workspace root changed during read")
        raw = b"".join(chunks)
        if len(raw) != before_fd.st_size:
            raise ValidationError("short binding read")
        return raw
    except OSError as error:
        raise ValidationError("stable no-follow read failed: " + relative) from error
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _binding(
    ordinal: int,
    group: str,
    role: str,
    path: str,
    raw: bytes,
    semantic_digest: Optional[str] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
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
        result["record_sha256"] = semantic_digest
    return result


def _predecessor_state(
    root: Path,
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, bytes]]:
    bindings: List[Dict[str, Any]] = []
    records: Dict[str, Dict[str, Any]] = {}
    raw_by_path: Dict[str, bytes] = {}
    for ordinal, spec in enumerate(PREDECESSOR_SPECS):
        group, role, path, expected_bytes, expected_sha, expected_record = spec
        raw = _stable_read(root, path)
        raw_by_path[path] = raw
        if len(raw) != expected_bytes or _sha256(raw) != expected_sha:
            raise ValidationError("predecessor exact-byte mismatch: " + path)
        if role == "machine":
            parsed = _parse_json(raw, "predecessor " + path)
            records[path] = parsed
            if expected_record is not None:
                if parsed.get("record_sha256") != expected_record:
                    raise ValidationError("predecessor semantic digest field mismatch")
                if _predecessor_record_sha256(parsed) != expected_record:
                    raise ValidationError("predecessor semantic digest recomputation failed")
        bindings.append(
            _binding(ordinal, group, role, path, raw, expected_record)
        )
    return bindings, records, raw_by_path


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    return [
        _binding(
            ordinal,
            "CURRENT_PACKAGE",
            role,
            path,
            _stable_read(root, path),
        )
        for ordinal, (role, path) in enumerate(
            (("human", HUMAN_PATH), ("validator", VALIDATOR_PATH), ("test", TEST_PATH))
        )
    ]


def _validate_predecessor_semantics(
    records: Mapping[str, Mapping[str, Any]], raw_by_path: Mapping[str, bytes]
) -> Dict[str, Any]:
    base_path = "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
    closure_path = (
        "research/fixtures/"
        "manuscript_v3_execution_preregistration_preexecution_closure_v2.json"
    )
    power_path = (
        "research/fixtures/manuscript_v3_real_domain_power_allocation_route_v1.json"
    )
    pilot_path = (
        "research/fixtures/manuscript_v3_pilot_variance_power_strategy_draft_v1.json"
    )
    gate_path = (
        "research/fixtures/"
        "manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json"
    )
    f104_path = (
        "research/fixtures/"
        "manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json"
    )
    b11_path = (
        "research/fixtures/manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.json"
    )
    phys_path = (
        "research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json"
    )
    retail_path = (
        "research/fixtures/"
        "manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json"
    )
    expected_record_paths = {
        base_path,
        closure_path,
        power_path,
        pilot_path,
        gate_path,
        f104_path,
        b11_path,
        phys_path,
        retail_path,
    }
    if set(records) != expected_record_paths:
        raise ValidationError("machine predecessor roster mismatch")

    base = records[base_path]
    power_plan = base.get("power_and_seed_plan")
    metric_plan = base.get("metric_and_estimand_plan")
    if type(power_plan) is not dict or type(metric_plan) is not dict:
        raise ValidationError("base analysis plans are absent")
    if (
        power_plan.get("design") != "FIXED_N_PAIRED"
        or power_plan.get("hierarchical_paired_analysis_formula", "ABSENT") is not None
        or power_plan.get("confidence_interval_resample_count", "ABSENT") is not None
        or power_plan.get("training_seed_is_replication_unit") is not True
        or power_plan.get("conditional_draw_is_independent_replication_unit") is not False
        or power_plan.get("primary_methods_share_paired_seeds") is not True
        or metric_plan.get("confidence_interval_method", "ABSENT") is not None
        or metric_plan.get("primary_metric_id", "ABSENT") is not None
        or metric_plan.get("domain_estimand")
        != "NATURAL_GROUP_WEIGHTED_PAIRED_MEAN_OF_PRIMARY_SCORE_DIRECT_MINUS_PRIMARY_SCORE_GUIDE"
        or metric_plan.get("cross_domain_pooling_permitted") is not False
    ):
        raise ValidationError("base F137/F112/F138 separation changed")

    closure = records[closure_path]
    if closure.get("global_state") != GLOBAL_STATE:
        raise ValidationError("preexecution closure state changed")
    closure_nonclaims = closure.get("nonclaims")
    if (
        type(closure_nonclaims) is not dict
        or closure_nonclaims.get("scientific_execution_authorized") is not False
        or closure_nonclaims.get("production_execution_authorized") is not False
        or closure_nonclaims.get("scientific_result_eligible") is not False
    ):
        raise ValidationError("preexecution closure nonclaims changed")

    power = records[power_path]
    analysis = power.get("analysis_contract")
    dependencies = power.get("dependency_audit")
    power_scope = power.get("scope_and_nonclaims")
    if type(analysis) is not dict or type(dependencies) is not dict:
        raise ValidationError("power-route analysis contract is absent")
    if (
        analysis.get("confirmatory_analysis_candidate")
        != "HIERARCHICAL_PAIRED_BOOTSTRAP_OVER_SEEDS_AND_GROUPS_WITH_CASES_RESAMPLED_WITHIN_GROUP"
        or analysis.get("pairing")
        != "CROSSED_SEED_BY_NATURAL_GROUP_AND_CASE_WITH_DIRECT_GUIDE_PAIRED_WITHIN_CELL"
        or analysis.get("draws_aggregate_inside_case") is not True
        or analysis.get("training_seed_is_replication_unit") is not True
        or analysis.get("seed_by_group_cells_treated_as_iid") is not False
        or dependencies.get("F137")
        != {"closed_by_this_package": False, "status": "OPEN", "value": None}
        or dependencies.get("F138")
        != {"closed_by_this_package": False, "status": "OPEN", "value": None}
        or dependencies.get("B07")
        != {"closed_by_this_package": False, "status": "OPEN"}
        or type(power_scope) is not dict
        or power_scope.get("unresolved_fields_closed") != 0
        or power_scope.get("scientific_execution_performed") is not False
    ):
        raise ValidationError("power-route F137 precursor semantics changed")

    pilot = records[pilot_path]
    aggregation = pilot.get("aggregation_contract")
    pilot_contract = pilot.get("pilot_contract")
    pilot_effects = pilot.get("project_control_effects")
    if (
        type(aggregation) is not dict
        or aggregation.get("difference") != "SCORE_DIRECT_MINUS_SCORE_GUIDE"
        or aggregation.get("order")
        != ["DRAWS_WITHIN_CASE", "CASES_WITHIN_GROUP", "GROUPS_WITHIN_SEED"]
        or aggregation.get(
            "case_and_group_weights_exact_positive_rational_and_sum_to_one_required"
        )
        is not True
        or aggregation.get("conditional_on_fixed_development_groups") is not True
        or aggregation.get("superpopulation_group_variance_claimed") is not False
        or aggregation.get(
            "draw_case_group_or_seed_group_cell_is_independent_seed_replication_unit"
        )
        is not False
        or type(pilot_contract) is not dict
        or pilot_contract.get("minimum_complete_seed_count_per_domain") != 2
        or pilot_contract.get("drop_impute_replace_retry_topup_or_select_permitted")
        is not False
        or type(pilot_effects) is not dict
        or pilot_effects.get("unresolved_fields_closed") != 0
        or pilot_effects.get("blockers_closed") != 0
    ):
        raise ValidationError("pilot hierarchy or nonclosure changed")

    gate = records[gate_path]
    closures = gate.get("field_closures")
    gate_scope = gate.get("scope_and_nonclaims")
    if type(closures) is not list or len(closures) != 5:
        raise ValidationError("Gate-A field closure roster changed")
    f107 = [row for row in closures if row.get("field_id") == "F107"]
    if (
        len(f107) != 1
        or f107[0].get("json_pointer")
        != "/metric_and_estimand_plan/aggregation_unit"
        or f107[0].get("value")
        != "NATURAL_GROUP_WEIGHTED_PAIRED_MEAN_OF_PRIMARY_SCORE_DIRECT_MINUS_PRIMARY_SCORE_GUIDE"
        or type(gate_scope) is not dict
        or gate_scope.get("confidence_method_selected") is not False
        or gate_scope.get("primary_metric_selected") is not False
        or gate_scope.get("pilot_observed") is not False
        or gate_scope.get("scientific_execution_performed") is not False
    ):
        raise ValidationError("Gate-A F107 or nonclosure changed")

    f104 = records[f104_path]
    transition = f104.get("count_transition")
    sweep = f104.get("comprehensive_field_sweep")
    effects = f104.get("project_effects_and_nonclaims")
    if type(transition) is not dict or type(sweep) is not dict or type(effects) is not dict:
        raise ValidationError("F104 count anchor is absent")
    if transition.get("after") != {
        "post_execution_closed": 0,
        "post_execution_open": 6,
        "pre_execution_closed": 21,
        "pre_execution_open": 145,
        "total_closed": 21,
        "total_open": 151,
    }:
        raise ValidationError("F104 current count anchor changed")
    if (
        tuple(sweep.get("closed_after_ids", ())) != CLOSED_BEFORE
        or tuple(sweep.get("open_after_ids", ())) != OPEN_BEFORE
        or "F137" not in sweep.get("open_after_ids", ())
        or transition.get("blockers_open_after") != 12
        or transition.get("blockers_closed") != 0
        or transition.get("formal_tests_closed") != 0
        or transition.get("results_filled") != 0
        or effects.get("all_12_blockers_remain_open") is not True
        or effects.get(
            "entropy_training_scientific_or_production_execution_performed"
        )
        is not False
        or effects.get("tracker_or_evidence_ledger_edited") is not False
    ):
        raise ValidationError("F104 current roster or nonclosure changed")

    review_raw = raw_by_path[
        "PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE_INDEPENDENT_REVIEW.md"
    ]
    if (
        b"**Review state:** `INDEPENDENT_REVIEW_GO`" not in review_raw
        or b"145 open / 21 closed" not in review_raw
    ):
        raise ValidationError("F104 independent current-count review changed")

    b11 = records[b11_path]
    b11_transition = b11.get("count_transition")
    b11_sweep = b11.get("comprehensive_field_sweep")
    b11_effects = b11.get("project_effects_and_nonclaims")
    if (
        type(b11_transition) is not dict
        or type(b11_sweep) is not dict
        or type(b11_effects) is not dict
    ):
        raise ValidationError("B11 post-execution count anchor is absent")
    if b11_transition.get("after") != {
        "post_execution_closed": 3,
        "post_execution_open": 3,
        "pre_execution_closed": 21,
        "pre_execution_open": 145,
        "total_closed": 24,
        "total_open": 148,
    }:
        raise ValidationError("B11 current additive count anchor changed")
    if (
        b11_transition.get("closed_by_package")
        != {
            "field_ids": ["F168", "F170", "F171"],
            "post_execution": 3,
            "pre_execution": 0,
            "total": 3,
        }
        or tuple(b11_sweep.get("closed_pre_ids", ())) != CLOSED_BEFORE
        or tuple(b11_sweep.get("open_pre_ids", ())) != OPEN_BEFORE
        or tuple(b11_sweep.get("closed_post_ids", ())) != POST_CLOSED
        or tuple(b11_sweep.get("open_post_ids", ())) != POST_OPEN
        or b11_transition.get("blockers_open_after") != 12
        or b11_transition.get("blockers_closed") != 0
        or b11_transition.get("formal_tests_closed") != 0
        or b11_transition.get("results_filled") != 0
        or b11_effects.get("B11_remains_open") is not True
        or b11_effects.get("F164_F165_F169_remain_open") is not True
        or b11_effects.get("F169_remains_open_and_null") is not True
        or b11_effects.get(
            "training_scientific_or_production_execution_performed"
        )
        is not False
    ):
        raise ValidationError("B11 roster, field scope, or nonclosure changed")
    b11_review = raw_by_path[
        "PROJECT_B11_PREOUTCOME_AUDIT_PLAN_FREEZE_INDEPENDENT_REVIEW.md"
    ]
    if (
        b"**Review state:** `INDEPENDENT_REVIEW_GO`" not in b11_review
        or b"| POST open / closed | 6 / 0 | 3 closed | 3 / 3 |" not in b11_review
    ):
        raise ValidationError("B11 independent current-count review changed")

    phys = records[phys_path]
    phys_identity = phys.get("design_identity")
    phys_effects = phys.get("checklist_effects")
    if (
        type(phys_identity) is not dict
        or phys_identity.get("algorithm_id")
        != "PHYSIONET_PATIENT_HASH_HAMILTON_70_15_15_V1"
        or type(phys_effects) is not dict
        or phys_effects.get("B07_closed") is not False
        or phys_effects.get("domain_admission_complete") is not False
    ):
        raise ValidationError("PhysioNet patient group carrier changed")

    retail = records[retail_path]
    retail_identity = retail.get("design_identity")
    retail_manifest = retail.get("normalized_manifest_contract")
    retail_effects = retail.get("checklist_effects")
    if (
        type(retail_identity) is not dict
        or retail_identity.get("algorithm_id")
        != "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_HAMILTON_70_15_15_V1"
        or type(retail_manifest) is not dict
        or not str(retail_manifest.get("customer_key", "")).startswith(
            "NONEMPTY_LOWERCASE_EVEN_LENGTH_HEX_OF_OPAQUE_CANONICAL_BYTES"
        )
        or type(retail_effects) is not dict
        or retail_effects.get("domain_admission_complete") is not False
        or retail_effects.get("power_review_complete") is not False
    ):
        raise ValidationError("Retail customer group carrier changed")

    anti_drift = raw_by_path["PROJECT_ANTI_DRIFT_OPERATING_POLICY.md"]
    if (
        b"two-artifact cap" not in anti_drift
        or b"new work must close a named item" not in anti_drift
    ):
        raise ValidationError("anti-drift scope boundary changed")

    return {
        "base_F137_open_and_null": True,
        "base_F112_open_and_null": True,
        "base_F138_open_and_null": True,
        "two_existing_B07_zero_field_precursors_verified": True,
        "natural_group_carriers": {
            "R3-PHYS": "PATIENT",
            "R4-RETAIL": "BYTE_EXACT_CUSTOMER_KEY",
        },
        "F107_exact_estimand_aggregation_verified": True,
        "F104_independently_accepted_current_count_anchor_verified": True,
        "B11_independently_accepted_postexecution_count_anchor_verified": True,
        "pre_execution_open_before": 145,
        "pre_execution_closed_before": 21,
        "post_execution_open_before": 3,
        "post_execution_closed_before": 3,
        "blockers_open_before": 12,
        "formal_tests_closed_before": 0,
        "results_filled_before": 0,
    }


def expected_record(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    predecessor_bindings, records, raw_by_path = _predecessor_state(root)
    predecessor_receipt = _validate_predecessor_semantics(records, raw_by_path)
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "reported_date": REPORTED_DATE,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": PACKAGE_KIND,
        "control_predicate": CONTROL_PREDICATE,
        "authority_and_scope": {
            "mandatory_anti_drift_scope_review_completed": True,
            "existing_zero_field_B07_precursor_count": 2,
            "third_zero_delta_precursor_permitted": False,
            "direct_F137_closure_authorized_by_active_bounded_workstream": True,
            "network_contact_data_entropy_runtime_science_or_submission_authorized": False,
            "tracker_ledger_or_predecessor_edit_authorized_by_this_package": False,
            "identity_or_time_externally_authenticated": False,
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
        "predecessor_projection_receipt": predecessor_receipt,
        "field_closures": [
            {
                "field_id": "F137",
                "json_pointer": F137_POINTER,
                "status": (
                    "CLOSED_BY_ADDITIVE_PREOUTCOME_PARAMETERIZED_NATURAL_GROUP_"
                    "HIERARCHICAL_PAIRED_FORMULA_FREEZE"
                ),
                "value": dict(FORMULA_VALUE),
            }
        ],
        "f137_parameterization_boundary": {
            "point_estimator_and_one_plan_transform_frozen": True,
            "actual_primary_metric_or_numeric_representation_populated": False,
            "actual_score_bound_margin_or_pilot_populated": False,
            "actual_group_or_case_weight_populated": False,
            "actual_seed_group_case_or_draw_cardinality_populated": False,
            "actual_seed_value_registry_or_bootstrap_address_populated": False,
            "F112_confidence_method_selected": False,
            "F138_resample_count_selected": False,
            "evaluator_plan_tuple_length_chosen_recommended_defaulted_reported_"
            "or_treated_as_F138_evidence": False,
            "data_entropy_compute_runtime_science_or_decision_present": False,
        },
        "count_transition": {
            "before": {
                "pre_execution_open": 145,
                "pre_execution_closed": 21,
                "post_execution_open": 3,
                "post_execution_closed": 3,
                "total_open": 148,
                "total_closed": 24,
            },
            "closed_by_package": {
                "field_ids": ["F137"],
                "pre_execution": 1,
                "post_execution": 0,
                "total": 1,
            },
            "after": {
                "pre_execution_open": 144,
                "pre_execution_closed": 22,
                "post_execution_open": 3,
                "post_execution_closed": 3,
                "total_open": 147,
                "total_closed": 25,
            },
            "blockers_open_after": 12,
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "results_filled": 0,
        },
        "comprehensive_field_sweep": {
            "total_pre_execution_fields": 166,
            "total_post_execution_fields": 6,
            "closed_before_ids": list(CLOSED_BEFORE),
            "eligible_now_ids": ["F137"],
            "closed_after_ids": list(CLOSED_AFTER),
            "open_after_ids": list(OPEN_AFTER),
            "open_after_count": 144,
            "closed_post_execution_ids_preserved": list(POST_CLOSED),
            "open_post_execution_ids_preserved": list(POST_OPEN),
            "additional_eligible_field_count": 0,
        },
        "project_effects_and_nonclaims": {
            "only_field_closed": "F137",
            "F168_F170_F171_B11_closures_preserved": True,
            "F164_F165_F169_remain_open": True,
            "B11_remains_open": True,
            "B07_remains_open": True,
            "all_12_blockers_remain_open": True,
            "F105_and_F109_F112_remain_open": True,
            "F130_F136_and_F138_remain_open": True,
            "primary_metric_score_bound_margin_or_confidence_method_selected": False,
            "weight_cardinality_seed_registry_or_pilot_selected": False,
            "domain_instance_admitted": False,
            "formal_test_28_status": "OPEN",
            "formal_test_29_status": "OPEN",
            "formal_test_30_status": "PENDING",
            "R1_R2_R3_R4_remain_unexecuted": True,
            "network_contact_repository_license_or_data_access_performed": False,
            "entropy_training_scientific_or_production_execution_performed": False,
            "runtime_or_operational_receipt_created": False,
            "confidence_interval_p_value_lower_bound_or_decision_produced": False,
            "result_or_claim_promoted": False,
            "submission_performed": False,
            "tracker_evidence_ledger_or_predecessor_edited": False,
        },
        "evidence_ready_registration": {
            "conditional_on_independent_acceptance": True,
            "proposed_text": EVIDENCE_READY_REGISTRATION,
            "registration_performed_by_this_package": False,
            "permitted_field_delta": ["F137"],
            "permitted_blocker_delta": [],
            "permitted_formal_test_delta": [],
            "permitted_result_delta": [],
        },
        "qualification_boundary": {
            "validator_read_only": True,
            "evaluator_accepts_caller_supplied_exact_synthetic_values_only": True,
            "bootstrap_indices_generated_by_evaluator": False,
            "caller_values_are_metric_pilot_resample_count_or_scientific_evidence": False,
            "qualification_exact_rational_type_is_production_numeric_type": False,
            "writer_rng_network_connector_subprocess_project_science_data_training_"
            "runtime_production_or_inference_route_present": False,
            "hostile_tests_mutate_only_disposable_copies": True,
            "canonical_package_or_predecessor_bytes_modified_by_qualification": False,
            "bytecode_and_pytest_cache_disabled_qualification_required": True,
        },
        "publication_boundary": {
            "internal_project_control_only": True,
            "anonymous_or_public_inclusion_permitted": False,
            "publication_safe_derivative_required": True,
            "fresh_anonymity_methods_statistics_and_claim_boundary_audit_required": True,
        },
    }
    record["record_sha256"] = record_sha256(record)
    return record


def validate(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    expected = expected_record(root)
    raw = _stable_read(root, MACHINE_PATH)
    actual = _parse_json(raw, "package machine record")
    if raw != canonical_machine_bytes(actual):
        raise ValidationError("package machine record is not canonical JSON")
    if actual.get("record_sha256") != record_sha256(actual):
        raise ValidationError("package machine record semantic digest mismatch")
    _strict_equal(actual, expected, "package machine record")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": actual["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "F137_closed": True,
        "unresolved_fields_closed": 1,
        "effective_pre_execution_open": 144,
        "effective_pre_execution_closed": 22,
        "effective_post_execution_open": 3,
        "effective_post_execution_closed": 3,
        "effective_open_blocker_count": 12,
        "B07_open": True,
        "F112_open": True,
        "F138_open": True,
        "formal_tests_closed": 0,
        "results_filled": 0,
        "scientific_execution": False,
        "tracker_edit_performed": False,
        "validation": "PASS",
    }


if __name__ == "__main__":
    print(
        json.dumps(
            validate(), ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
    )
