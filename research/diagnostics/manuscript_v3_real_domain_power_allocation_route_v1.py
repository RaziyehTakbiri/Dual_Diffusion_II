"""Read-only validator and exact calculator for the real-domain power route.

This module is administrative/statistical design infrastructure only.  It
does not import project science, contact a source, inspect data, draw entropy,
open held-out material, or execute an experiment.  The calculator accepts
only exact integers and :class:`fractions.Fraction` values.  Its certificate
uses a rational upper bound for logarithms and an algebraic upper bound for
the square-root cross term; no binary floating-point value is part of the
proof.
"""

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

SCHEMA = "heterodiff-manuscript-v3-real-domain-power-allocation-route-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = (
    "REAL_DOMAIN_POWER_ALLOCATION_ROUTE_FROZEN_AND_SYNTHETICALLY_QUALIFIED_"
    "AWAITING_METRIC_MARGIN_PILOT_AND_COMPUTE"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
PACKAGE_KIND = "STATIC_POWER_AND_ALLOCATION_ROUTE_NO_SCIENTIFIC_EFFECT"
CONTROL_PREDICATE = "POWER_AND_ALLOCATION_ROUTE_DEPENDENCY_AUDIT_VALIDATED"
REPORTED_DATE = "2026-08-30"

HUMAN_PATH = "PROJECT_REAL_DOMAIN_POWER_ALLOCATION_ROUTE.md"
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_real_domain_power_allocation_route_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_real_domain_power_allocation_route_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_real_domain_power_allocation_route_v1.py"
)

PREREG_HUMAN_PATH = "manuscript_v3/execution_preregistration.md"
PREREG_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
)
CLOSURE_HUMAN_PATH = (
    "manuscript_v3/execution_preregistration_preexecution_closure_v2.md"
)
CLOSURE_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_execution_preregistration_preexecution_closure_v2.json"
)
CANDIDATE_HUMAN_PATH = "PROJECT_SOLO_BLOCK2_PRECONTACT_INSTANCE_CANDIDATE.md"
CANDIDATE_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_solo_block2_precontact_instance_candidate_v1.json"
)
CANDIDATE_VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_solo_block2_precontact_instance_candidate_v1.py"
)
CANDIDATE_TEST_PATH = (
    "tests/unit/test_manuscript_v3_solo_block2_precontact_instance_candidate_v1.py"
)

NORMALIZED_AUTHORITY_TEXT = "Alright, sounds good. Go ahead then."
AUTHORITY_TEXT_SHA256 = (
    "834e4a9458adde27cebea9341c11ef09e49dc04dbfb2d7b9a05ed9108a16413b"
)

LOG_SERIES_TERMS = 64
MAX_RATIONAL_COMPONENT_BITS = 4096


class ValidationError(ValueError):
    """Raised when exact arithmetic, schema, semantics, or custody fail."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload))


def _foreign_self_digest(record: Mapping[str, Any]) -> str:
    schema = record.get("schema_version")
    if type(schema) is not str or not schema.isascii():
        raise ValidationError("foreign self-digest schema invalid")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(
        (schema + "\0").encode("ascii") + _canonical_payload_bytes(payload)
    )


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
        for ordinal, (item, wanted) in enumerate(zip(actual, expected)):
            _strict_equal(item, wanted, label + "[" + str(ordinal) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def _exact_fraction(value: Any, label: str) -> Fraction:
    if type(value) is int:
        result = Fraction(value, 1)
    elif type(value) is Fraction:
        result = value
    else:
        raise ValidationError(label + " must be an exact int or Fraction")
    if (
        result.numerator.bit_length() > MAX_RATIONAL_COMPONENT_BITS
        or result.denominator.bit_length() > MAX_RATIONAL_COMPONENT_BITS
    ):
        raise ValidationError(label + " exceeds the rational bit bound")
    return result


def _fraction_record(value: Fraction) -> Dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _log_unit_interval(value: Fraction) -> Tuple[Fraction, Fraction]:
    """Return exact lower/upper bounds for ln(value), for 1 <= value <= 2."""

    if value < 1 or value > 2:
        raise ValidationError("log series argument outside [1,2]")
    z = (value - 1) / (value + 1)
    z_squared = z * z
    power = z
    lower = Fraction(0, 1)
    for ordinal in range(LOG_SERIES_TERMS):
        lower += Fraction(2, 2 * ordinal + 1) * power
        power *= z_squared
    if z == 0:
        return lower, lower
    tail_upper = (
        Fraction(2, 2 * LOG_SERIES_TERMS + 1)
        * power
        / (1 - z_squared)
    )
    return lower, lower + tail_upper


def _log_interval_ge_one(value: Fraction) -> Tuple[Fraction, Fraction]:
    """Return exact rational bounds for ln(value), for value >= 1."""

    if value < 1:
        raise ValidationError("log argument must be at least one")
    exponent = 0
    normalized = value
    while normalized >= 2:
        normalized /= 2
        exponent += 1
        if exponent > MAX_RATIONAL_COMPONENT_BITS:
            raise ValidationError("log normalization exceeded bound")
    ln2_lower, ln2_upper = _log_unit_interval(Fraction(2, 1))
    residual_lower, residual_upper = _log_unit_interval(normalized)
    return (
        exponent * ln2_lower + residual_lower,
        exponent * ln2_upper + residual_upper,
    )


def _ceil_fraction(value: Fraction) -> int:
    if value < 0:
        raise ValidationError("cannot ceiling a negative sample-size bound")
    quotient, remainder = divmod(value.numerator, value.denominator)
    return quotient + (1 if remainder else 0)


def certified_seed_count(
    W: Any,
    alpha_star: Any,
    beta_star: Any,
    delta0: Any,
    delta1: Any,
) -> Dict[str, Any]:
    """Certify a conservative fixed seed count with exact arithmetic.

    The target expression is

        W^2 (sqrt(ln(1/alpha*)) + sqrt(ln(1/beta*)))^2
        ------------------------------------------------------------- .
                         2 (delta1-delta0)^2

    For exact log upper bounds A and B, ``(sqrt(A)+sqrt(B))^2 <=
    2(A+B)`` gives the exact conservative rational alternative
    ``W^2(A+B)/(delta1-delta0)^2``.  Its integer ceiling is returned.
    """

    width = _exact_fraction(W, "W")
    alpha = _exact_fraction(alpha_star, "alpha_star")
    beta = _exact_fraction(beta_star, "beta_star")
    null_margin = _exact_fraction(delta0, "delta0")
    alternative_margin = _exact_fraction(delta1, "delta1")
    if width <= 0:
        raise ValidationError("W must be positive")
    if not 0 < alpha < 1:
        raise ValidationError("alpha_star must be in (0,1)")
    if not 0 < beta < 1:
        raise ValidationError("beta_star must be in (0,1)")
    if alternative_margin <= null_margin:
        raise ValidationError("delta1 must be strictly greater than delta0")

    alpha_lower, alpha_upper = _log_interval_ge_one(1 / alpha)
    beta_lower, beta_upper = _log_interval_ge_one(1 / beta)
    gap = alternative_margin - null_margin
    rational_upper = width * width * (alpha_upper + beta_upper) / (gap * gap)
    result = {
        "calculator_id": "EXACT_RATIONAL_HOEFFDING_SEED_COUNT_V1",
        "inputs": {
            "W": _fraction_record(width),
            "alpha_star": _fraction_record(alpha),
            "beta_star": _fraction_record(beta),
            "delta0": _fraction_record(null_margin),
            "delta1": _fraction_record(alternative_margin),
        },
        "strict_gap": _fraction_record(gap),
        "ln_inverse_alpha_interval": {
            "lower": _fraction_record(alpha_lower),
            "upper": _fraction_record(alpha_upper),
        },
        "ln_inverse_beta_interval": {
            "lower": _fraction_record(beta_lower),
            "upper": _fraction_record(beta_upper),
        },
        "log_series_terms": LOG_SERIES_TERMS,
        "target_formula": (
            "CEIL(W^2*(SQRT(LN(1/ALPHA_STAR))+SQRT(LN(1/BETA_STAR)))^2/"
            "(2*(DELTA1-DELTA0)^2))"
        ),
        "certifying_inequality": (
            "(SQRT(A)+SQRT(B))^2_LE_2*(A+B)_WITH_A_B_REPLACED_BY_"
            "EXACT_RATIONAL_LOG_UPPER_BOUNDS"
        ),
        "conservative_rational_upper": _fraction_record(rational_upper),
        "certified_seed_count": _ceil_fraction(rational_upper),
        "arithmetic_contract": (
            "PURE_STDLIB_EXACT_INTEGER_AND_FRACTION_NO_FLOAT_DECIMAL_OR_MATH_"
            "LIBRARY_IN_CERTIFICATE"
        ),
        "certificate_status": "EXACT_CONSERVATIVE_UPPER_BOUND",
    }
    return result


def _safe_relative_path(root: Path, relative_path: str) -> Path:
    if type(relative_path) is not str:
        raise ValidationError("path type invalid")
    rel = Path(relative_path)
    if rel.is_absolute() or not rel.parts or ".." in rel.parts:
        raise ValidationError("unsafe path")
    return root.joinpath(*rel.parts)


def _ancestor_snapshot(root: Path, path: Path) -> Tuple[Tuple[Any, ...], ...]:
    rows: List[Tuple[Any, ...]] = []
    current = path.parent
    while True:
        status = current.lstat()
        if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
            raise ValidationError("unsafe ancestor")
        rows.append(
            (
                str(current), status.st_dev, status.st_ino,
                stat.S_IFMT(status.st_mode), stat.S_IMODE(status.st_mode),
                status.st_uid, status.st_gid,
            )
        )
        if current == root:
            break
        if root not in current.parents:
            raise ValidationError("path escaped root")
        current = current.parent
    return tuple(reversed(rows))


def _leaf_fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
    return (
        status.st_dev, status.st_ino, stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode), status.st_uid, status.st_gid,
        status.st_nlink, status.st_size, status.st_mtime_ns, status.st_ctime_ns,
    )


def _stable_read(root: Path, relative_path: str) -> bytes:
    path = _safe_relative_path(root, relative_path)
    ancestors = _ancestor_snapshot(root, path)
    before_path = path.lstat()
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != 0o644
        or before_path.st_nlink != 1
    ):
        raise ValidationError("file custody invalid: " + relative_path)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before_fd = os.fstat(descriptor)
        chunks: List[bytes] = []
        while True:
            chunk = os.read(descriptor, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    raw = b"".join(chunks)
    fingerprint = _leaf_fingerprint(before_path)
    if not (
        fingerprint == _leaf_fingerprint(before_fd)
        == _leaf_fingerprint(after_fd) == _leaf_fingerprint(after_path)
    ):
        raise ValidationError("file changed during read: " + relative_path)
    if len(raw) != before_fd.st_size:
        raise ValidationError("short read: " + relative_path)
    if ancestors != _ancestor_snapshot(root, path):
        raise ValidationError("ancestor changed during read")
    return raw


def _binding(
    ordinal: int,
    role: str,
    path: str,
    raw: bytes,
    *,
    self_digest: Optional[str] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "ordinal": ordinal,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": raw.endswith(b"\n"),
    }
    if self_digest is not None:
        result["record_sha256"] = self_digest
    return result


LIVE_IMMUTABLE_BINDINGS: Tuple[Mapping[str, Any], ...] = (
    {"ordinal": 0, "role": "EXECUTION_PREREGISTRATION_HUMAN", "path": PREREG_HUMAN_PATH, "bytes": 22491, "raw_sha256": "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 1, "role": "EXECUTION_PREREGISTRATION_MACHINE", "path": PREREG_MACHINE_PATH, "bytes": 39771, "raw_sha256": "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 2, "role": "PREEXECUTION_CLOSURE_HUMAN", "path": CLOSURE_HUMAN_PATH, "bytes": 14938, "raw_sha256": "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 3, "role": "PREEXECUTION_CLOSURE_MACHINE", "path": CLOSURE_MACHINE_PATH, "bytes": 24571, "raw_sha256": "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "record_sha256": "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4"},
    {"ordinal": 4, "role": "PRECONTACT_CANDIDATE_HUMAN", "path": CANDIDATE_HUMAN_PATH, "bytes": 17965, "raw_sha256": "ed211b7bf5aaf45a839e18d15484177fa0c51d7cb95540cdccc61587b2b8250f", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 5, "role": "PRECONTACT_CANDIDATE_MACHINE", "path": CANDIDATE_MACHINE_PATH, "bytes": 23932, "raw_sha256": "95bae0a0ff0d5a199afc23cfc048de04cce28c47300ada301b927c21c60166be", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "record_sha256": "2c4c068c553bdfab04d49f01163c84923b9108b2f762872ba00015c2fadd9304"},
    {"ordinal": 6, "role": "PRECONTACT_CANDIDATE_VALIDATOR", "path": CANDIDATE_VALIDATOR_PATH, "bytes": 46460, "raw_sha256": "6bdfe3c943c8238d88dc5fba908918d9304ab9f377517a483c65cfac887a39dc", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 7, "role": "PRECONTACT_CANDIDATE_HOSTILE_TEST", "path": CANDIDATE_TEST_PATH, "bytes": 27389, "raw_sha256": "40ba6642f81323fb9254520113697785513bb705e72232731657ae1c481d2856", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
)


EXPECTED_AUTHORITY: Mapping[str, Any] = {
    "normalized_visible_text": NORMALIZED_AUTHORITY_TEXT,
    "normalized_visible_text_utf8_bytes": 36,
    "normalized_visible_text_sha256": AUTHORITY_TEXT_SHA256,
    "normalization": "TRAILING_HTML_SPACE_ENTITY_AND_TRANSPORT_WHITESPACE_REMOVED_ONLY",
    "raw_transport_bytes_bound": False,
    "raw_trailing_transport_content_bound": False,
    "conversation_envelope_bound": False,
    "account_identity_bound": False,
    "timestamp_bound": False,
    "cryptographic_user_authentication_claimed": False,
    "additive_static_power_route_authorized": True,
    "tracker_edit_authorized": False,
    "external_contact_or_browsing_authorized": False,
    "data_access_or_download_authorized": False,
    "runtime_or_scientific_execution_authorized": False,
    "scientific_entropy_authorized": False,
    "pilot_execution_authorized": False,
}


EXPECTED_ROUTE_IDENTITY: Mapping[str, Any] = {
    "route_id": "REAL_DOMAIN_POWER_ALLOCATION_ROUTE_V1",
    "control_predicate": CONTROL_PREDICATE,
    "control_predicate_value_after_validation": True,
    "distribution_free_calculator_frozen": True,
    "synthetic_calculator_qualification_complete": True,
    "future_simulation_route_frozen": True,
    "real_domain_power_review_complete": False,
    "real_domain_allocation_selected": False,
    "primary_metric_selected": False,
    "margin_selected": False,
    "pilot_observed": False,
    "compute_budget_selected": False,
    "scientific_effect": 0,
}


EXPECTED_DEPENDENCIES: Mapping[str, Any] = {
    "B07": {"status": "OPEN", "closed_by_this_package": False},
    "F060": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F061": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F110": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F128": {"status": "OPEN", "value": None, "candidate_value": {"numerator": 1, "denominator": 20}, "closed_by_this_package": False},
    "F129": {"status": "OPEN", "value": None, "candidate_value": {"numerator": 9, "denominator": 10}, "closed_by_this_package": False},
    "F130": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F131": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F132": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F133": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F134": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F135": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F136": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F137": {"status": "OPEN", "value": None, "closed_by_this_package": False},
    "F138": {"status": "OPEN", "value": None, "closed_by_this_package": False},
}


EXPECTED_CALCULATOR: Mapping[str, Any] = {
    "calculator_id": "EXACT_RATIONAL_HOEFFDING_SEED_COUNT_V1",
    "parameters": ["W", "alpha_star", "beta_star", "delta0", "delta1"],
    "accepted_numeric_types": ["EXACT_INT", "FRACTIONS_FRACTION"],
    "normalized_numerator_maximum_bit_length": MAX_RATIONAL_COMPONENT_BITS,
    "normalized_denominator_maximum_bit_length": MAX_RATIONAL_COMPONENT_BITS,
    "component_bit_bound_applied_after_fraction_normalization": True,
    "component_exceeding_bit_bound_disposition": "REFUSE_BEFORE_CERTIFICATE_CONSTRUCTION",
    "binary_float_accepted": False,
    "boolean_accepted_as_integer": False,
    "domain": "W_GT_0_AND_0_LT_ALPHA_STAR_BETA_STAR_LT_1_AND_DELTA1_GT_DELTA0",
    "target_formula": "CEIL(W^2*(SQRT(LN(1/ALPHA_STAR))+SQRT(LN(1/BETA_STAR)))^2/(2*(DELTA1-DELTA0)^2))",
    "certificate_route": "EXACT_RATIONAL_LOG_INTERVAL_PLUS_SQRT_CROSS_TERM_UPPER_BOUND",
    "log_bound": "64_TERM_ATANH_SERIES_WITH_EXACT_GEOMETRIC_TAIL_UPPER_BOUND_AFTER_POWER_OF_TWO_NORMALIZATION",
    "sqrt_bound": "(SQRT(A)+SQRT(B))^2_LE_2*(A+B)",
    "returned_safe_alternative": "CEIL(W^2*(UPPER_LN_1_OVER_ALPHA+UPPER_LN_1_OVER_BETA)/(DELTA1-DELTA0)^2)",
    "proof_arithmetic": "PURE_STDLIB_EXACT_INTEGER_AND_FRACTION",
    "float_or_decimal_used_in_certificate": False,
    "delta1_less_than_or_equal_to_delta0_disposition": "REFUSE",
    "delta0_project_field": "F110_MINIMUM_MEANINGFUL_DECISION_THRESHOLD_NULL_MARGIN",
    "delta1_project_field": "F130_PLANNING_ALTERNATIVE_MINIMUM_EFFECT_USED_FOR_POWER",
    "F110_delta0_value_selected": False,
    "F130_delta1_value_selected": False,
    "interpretation": "SUFFICIENT_SEED_COUNT_FOR_FIXED_BOUNDED_PAIRED_SEED_MEANS_CONDITIONAL_ON_FROZEN_HELD_OUT_CASES",
    "superpopulation_group_claimed": False,
}


SYNTHETIC_QUALIFICATION = certified_seed_count(
    Fraction(6, 1), Fraction(1, 40), Fraction(1, 20),
    Fraction(0, 1), Fraction(1, 1),
)


EXPECTED_CANDIDATE_FAMILY: Mapping[str, Any] = {
    "status": "CANDIDATE_ONLY_NOT_PREREGISTRATION_CLOSURE",
    "primary_family": ["R3-PHYS", "R4-RETAIL"],
    "familywise_alpha_candidate": {"numerator": 1, "denominator": 20},
    "target_joint_power_candidate": {"numerator": 9, "denominator": 10},
    "multiplicity_candidate": "HOLM_TWO_HYPOTHESIS_FAMILY",
    "planning_alpha_star_per_domain": {"numerator": 1, "denominator": 40},
    "planning_beta_star_per_domain": {"numerator": 1, "denominator": 20},
    "joint_power_argument": "UNION_BOUND_ON_TWO_DOMAIN_FAILURE_EVENTS_NO_DOMAIN_INDEPENDENCE_ASSUMED",
    "minimum_effect_delta1": None,
    "null_margin_delta0": None,
    "delta0_project_field": "F110_MINIMUM_MEANINGFUL_DECISION_THRESHOLD_NULL_MARGIN",
    "delta1_project_field": "F130_PLANNING_ALTERNATIVE_MINIMUM_EFFECT_USED_FOR_POWER",
    "delta1_strictly_greater_than_delta0_required": True,
    "metric_bound_W": None,
    "candidate_values_close_F128_or_F129": False,
    "synthetic_CKS_example_is_metric_selection": False,
    "synthetic_CKS_bound": {
        "normalized_kernel_range": "ZERO_TO_ONE",
        "single_method_score_range": "MINUS_TWO_TO_ONE",
        "paired_difference_range": "MINUS_THREE_TO_THREE",
        "W": {"numerator": 6, "denominator": 1},
        "delta0": {"numerator": 0, "denominator": 1},
        "delta1": {"numerator": 1, "denominator": 1},
        "certified_seed_count": 241,
        "qualification_only": True,
    },
}


EXPECTED_ANALYSIS: Mapping[str, Any] = {
    "estimand": "NATURAL_GROUP_WEIGHTED_PAIRED_MEAN_PRIMARY_SCORE_DIRECT_MINUS_PRIMARY_SCORE_GUIDE",
    "pairing": "CROSSED_SEED_BY_NATURAL_GROUP_AND_CASE_WITH_DIRECT_GUIDE_PAIRED_WITHIN_CELL",
    "training_seed_is_replication_unit": True,
    "conditional_draw_is_independent_replication_unit": False,
    "draws_aggregate_inside_case": True,
    "seed_by_group_cells_treated_as_iid": False,
    "fixed_N": True,
    "seed_topup_replacement_favorable_selection_or_sequential_stopping_permitted": False,
    "confirmatory_analysis_candidate": "HIERARCHICAL_PAIRED_BOOTSTRAP_OVER_SEEDS_AND_GROUPS_WITH_CASES_RESAMPLED_WITHIN_GROUP",
    "holm_adjusted_one_sided_lower_bounds_required": True,
    "both_R3_and_R4_must_exceed_frozen_effect": True,
    "post_outcome_metric_margin_allocation_or_analysis_change_permitted": False,
}


EXPECTED_SIMULATION: Mapping[str, Any] = {
    "status": "FUTURE_ROUTE_ONLY_NOT_EXECUTED",
    "pilot_source": "BLINDED_TRAIN_VALIDATION_ONLY_CENTERED_PAIRED_RESIDUAL_OBJECTS",
    "pilot_test_outcomes_permitted": False,
    "pilot_seed_overlap_with_confirmatory_registry_permitted": False,
    "allocation_grid": "FINITE_LITERAL_PREDECLARED_GRID_OVER_SEEDS_GROUPS_CASES_DRAWS_BOOTSTRAP_RESAMPLES_AND_COMPUTE",
    "grid_fixed_before_simulation": True,
    "grid_expansion_after_results_permitted": False,
    "null_configurations": ["BOTH_DOMAIN_NULL", "R3_NULL_R4_ALTERNATIVE", "R3_ALTERNATIVE_R4_NULL"],
    "null_configuration_list_semantics": "THREE_NAMED_STRUCTURAL_TRUTH_PATTERNS_NOT_COMPOSITE_NULL_EXHAUSTION",
    "three_named_null_truth_patterns_are_exhaustive_for_composite_null": False,
    "composite_null_coverage_required_before_execution": True,
    "composite_null_coverage_route": "FORMAL_LEAST_FAVORABLE_OR_MONOTONICITY_PROOF_OR_FINITE_LITERAL_PREDECLARED_NUISANCE_GRID",
    "uncovered_composite_null_disposition": "TERMINAL_NO_GO",
    "alternative_requires_both_domains_at_frozen_effect": True,
    "stress_alternatives": ["EVENT_COUNT_MARGINAL_PRESERVING_ASSOCIATION_DESTRUCTION", "ASSOCIATION_MARGINAL_PRESERVING_DEPENDENCE_DESTRUCTION", "TEMPORAL_MARGINAL_PRESERVING_ORDER_DESTRUCTION"],
    "simulation_pairing": "SAME_SEED_GROUP_CASE_AND_DRAW_ADDRESSES_FOR_DIRECT_AND_GUIDE",
    "draws_are_replicates": False,
    "clopper_pearson_requires_within_condition_independent_bernoulli_trials": True,
    "bernoulli_success_indicator_exactly_frozen_before_simulation": True,
    "independence_established_by_distinct_addresses_alone": False,
    "literal_immutable_trial_stream_seed_registry_required": True,
    "trial_registry_pairwise_disjoint_across_grid_condition_and_trial_ordinal": True,
    "trial_registry_disjoint_from_pilot_and_confirmatory_seed_registries": True,
    "trial_registry_custody_required": True,
    "trial_stream_or_seed_reuse_permitted": False,
    "multiplicity": "EXACT_CONFIRMATORY_HOLM_RULE",
    "fwer_acceptance": "SIMULTANEOUS_CLOPPER_PEARSON_UPPER_BOUNDS_FOR_EVERY_ADMITTED_NULL_CONDITION_LE_FROZEN_FAMILYWISE_ALPHA",
    "power_acceptance": "SIMULTANEOUS_CLOPPER_PEARSON_LOWER_BOUND_FOR_JOINT_TWO_DOMAIN_POWER_GE_FROZEN_TARGET_POWER",
    "mc_error_control": "SIMULTANEOUSLY_ALLOCATED_ACROSS_EVERY_GRID_POINT_ADMITTED_NULL_CONDITION_AND_STRESS_ALTERNATIVE",
    "selection_rule": "MINIMUM_TOTAL_COMPUTE_THEN_FIXED_LEXICOGRAPHIC_TIE_BREAK",
    "topup_retry_replacement_or_favorable_selection_permitted": False,
    "no_passing_grid_point_disposition": "TERMINAL_NO_GO_NEW_PREOUTCOME_VERSION_REQUIRED",
    "required_before_execution": ["PRIMARY_METRIC_AND_BOUND", "F110_DELTA0_AND_F130_DELTA1", "TRAIN_VALIDATION_PILOT_RECEIPT", "FINITE_GRID_AND_COMPUTE_BUDGET", "EXACT_CLOPPER_PEARSON_CONFIDENCE_ALLOCATION", "PROVED_WITHIN_CONDITION_INDEPENDENT_BERNOULLI_TRIAL_LAW", "DISJOINT_IMMUTABLE_TRIAL_STREAM_SEED_REGISTRY_AND_CUSTODY", "COMPOSITE_NULL_COVERAGE_PROOF_OR_FROZEN_NUISANCE_GRID", "LITERAL_CONFIRMATORY_SEED_REGISTRY", "INDEPENDENT_REVIEW"],
}


EXPECTED_SCOPE: Mapping[str, Any] = {
    "static_or_synthetic_only": True,
    "web_or_network_used": False,
    "dataset_source_license_or_governance_contacted": False,
    "data_accessed": False,
    "project_or_scientific_code_imported": False,
    "scientific_execution_performed": False,
    "test_outcome_accessed": False,
    "tracker_edited": False,
    "existing_files_modified": False,
    "unresolved_fields_closed": 0,
    "blockers_closed": 0,
    "formal_scientific_tests_closed": 0,
    "scientific_results_produced": 0,
    "one_way_predecessor_bindings": True,
}


EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version", "state", "global_state", "package_kind", "reported_date",
    "authority_provenance", "route_identity", "dependency_audit",
    "distribution_free_calculator_contract", "synthetic_qualification",
    "candidate_family_design", "analysis_contract",
    "future_simulation_qualification_route", "scope_and_nonclaims",
    "live_immutable_input_bindings", "package_bindings", "record_sha256",
}


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for ordinal, role, path in (
        (0, "HUMAN_ROUTE", HUMAN_PATH),
        (1, "READ_ONLY_VALIDATOR_AND_EXACT_CALCULATOR", VALIDATOR_PATH),
        (2, "HOSTILE_UNIT_TEST", TEST_PATH),
    ):
        rows.append(_binding(ordinal, role, path, _stable_read(root, path)))
    return rows


def expected_record(root: Optional[Path] = None) -> Dict[str, Any]:
    """Construct the exact acyclic machine record."""

    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": PACKAGE_KIND,
        "reported_date": REPORTED_DATE,
        "authority_provenance": dict(EXPECTED_AUTHORITY),
        "route_identity": dict(EXPECTED_ROUTE_IDENTITY),
        "dependency_audit": dict(EXPECTED_DEPENDENCIES),
        "distribution_free_calculator_contract": dict(EXPECTED_CALCULATOR),
        "synthetic_qualification": dict(SYNTHETIC_QUALIFICATION),
        "candidate_family_design": dict(EXPECTED_CANDIDATE_FAMILY),
        "analysis_contract": dict(EXPECTED_ANALYSIS),
        "future_simulation_qualification_route": dict(EXPECTED_SIMULATION),
        "scope_and_nonclaims": dict(EXPECTED_SCOPE),
        "live_immutable_input_bindings": [dict(row) for row in LIVE_IMMUTABLE_BINDINGS],
        "package_bindings": _package_bindings(workspace),
        "record_sha256": "",
    }
    record["record_sha256"] = record_sha256(record)
    return record


def _validate_live_inputs(root: Path) -> None:
    raws: Dict[str, bytes] = {}
    for expected in LIVE_IMMUTABLE_BINDINGS:
        raw = _stable_read(root, expected["path"])
        raws[expected["path"]] = raw
        observed = _binding(
            expected["ordinal"], expected["role"], expected["path"], raw,
            self_digest=expected.get("record_sha256"),
        )
        _strict_equal(observed, dict(expected), "immutable predecessor binding")

    prereg = json.loads(raws[PREREG_MACHINE_PATH].decode("ascii"))
    if type(prereg) is not dict or prereg.get("state") != GLOBAL_STATE:
        raise ValidationError("preregistration state changed")
    if prereg.get("confirmatory_execution_authorized") is not False:
        raise ValidationError("preregistration authority changed")
    power = prereg.get("power_and_seed_plan")
    metric = prereg.get("metric_and_estimand_plan")
    if type(power) is not dict or type(metric) is not dict:
        raise ValidationError("preregistration plan type changed")
    for field in (
        "familywise_alpha", "target_power", "minimum_effect_used_for_power",
        "pilot_variance_source", "independent_training_seed_count",
        "training_seed_values_or_generation_receipt", "natural_group_count_by_domain",
        "conditioning_cases_per_group", "conditional_draws_per_case",
        "hierarchical_paired_analysis_formula", "confidence_interval_resample_count",
    ):
        if power.get(field) is not None:
            raise ValidationError("power dependency no longer open: " + field)
    if metric.get("primary_metric_id") is not None or metric.get("minimum_meaningful_effect") is not None:
        raise ValidationError("metric or margin dependency no longer open")

    closure = json.loads(raws[CLOSURE_MACHINE_PATH].decode("ascii"))
    if type(closure) is not dict or _foreign_self_digest(closure) != closure.get("record_sha256"):
        raise ValidationError("closure self digest invalid")
    blockers = closure.get("blocker_projection")
    if type(blockers) is not dict or blockers.get("blockers_closed_by_closure") != 0:
        raise ValidationError("closure blocker projection changed")

    candidate = json.loads(raws[CANDIDATE_MACHINE_PATH].decode("ascii"))
    if type(candidate) is not dict or _foreign_self_digest(candidate) != candidate.get("record_sha256"):
        raise ValidationError("candidate self digest invalid")
    checklist = candidate.get("checklist_effects")
    split = candidate.get("candidate_split_and_leakage_rules")
    if (
        type(checklist) is not dict or checklist.get("power_review_complete") is not False
        or checklist.get("primary_metric_selected") is not False
        or type(split) is not dict or split.get("power_justified") is not False
    ):
        raise ValidationError("candidate nonclosure boundary changed")


def _validate_semantics(record: Mapping[str, Any]) -> None:
    route = record["route_identity"]
    if route["scientific_effect"] != 0 or type(route["scientific_effect"]) is not int:
        raise ValidationError("scientific effect is not exact zero")
    if route["control_predicate"] != CONTROL_PREDICATE:
        raise ValidationError("unexpected control predicate")
    if record["state"] != STATE or record["global_state"] != GLOBAL_STATE:
        raise ValidationError("state mismatch")
    dependencies = record["dependency_audit"]
    if set(dependencies) != {
        "B07", "F060", "F061", "F110",
        *["F" + str(i) for i in range(128, 139)],
    }:
        raise ValidationError("dependency roster mismatch")
    if any(row["status"] != "OPEN" or row["closed_by_this_package"] is not False for row in dependencies.values()):
        raise ValidationError("dependency overclaimed")
    for field in (
        "F060", "F061", "F110", *["F" + str(i) for i in range(128, 139)]
    ):
        if dependencies[field]["value"] is not None:
            raise ValidationError("typed-null dependency populated")
    candidate = record["candidate_family_design"]
    if candidate["candidate_values_close_F128_or_F129"] is not False:
        raise ValidationError("candidate alpha or power promoted")
    if (
        candidate["null_margin_delta0"] is not None
        or candidate["minimum_effect_delta1"] is not None
    ):
        raise ValidationError("F110/F130 margins promoted")
    if record["analysis_contract"]["conditional_draw_is_independent_replication_unit"] is not False:
        raise ValidationError("conditional draws misclassified")
    simulation = record["future_simulation_qualification_route"]
    if (
        simulation["grid_fixed_before_simulation"] is not True
        or simulation["grid_expansion_after_results_permitted"] is not False
        or simulation["topup_retry_replacement_or_favorable_selection_permitted"] is not False
        or simulation[
            "clopper_pearson_requires_within_condition_independent_bernoulli_trials"
        ] is not True
        or simulation["independence_established_by_distinct_addresses_alone"] is not False
        or simulation["literal_immutable_trial_stream_seed_registry_required"] is not True
        or simulation[
            "trial_registry_pairwise_disjoint_across_grid_condition_and_trial_ordinal"
        ] is not True
        or simulation["trial_registry_custody_required"] is not True
        or simulation["trial_stream_or_seed_reuse_permitted"] is not False
        or simulation[
            "three_named_null_truth_patterns_are_exhaustive_for_composite_null"
        ] is not False
        or simulation["composite_null_coverage_required_before_execution"] is not True
        or simulation["uncovered_composite_null_disposition"] != "TERMINAL_NO_GO"
    ):
        raise ValidationError("simulation anti-drift contract changed")
    qualification = record["synthetic_qualification"]
    recalculated = certified_seed_count(
        Fraction(6, 1), Fraction(1, 40), Fraction(1, 20),
        Fraction(0, 1), Fraction(1, 1),
    )
    _strict_equal(qualification, recalculated, "synthetic qualification")
    if qualification["certified_seed_count"] != 241:
        raise ValidationError("synthetic certificate changed")


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate exact custody and semantics and return a safe status."""

    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    raw = _stable_read(workspace, MACHINE_PATH)
    record = json.loads(raw.decode("ascii"))
    if type(record) is not dict or set(record) != EXPECTED_TOP_LEVEL_KEYS:
        raise ValidationError("machine record schema mismatch")
    if canonical_machine_bytes(record) != raw:
        raise ValidationError("machine record is not canonical")
    if type(record.get("record_sha256")) is not str:
        raise ValidationError("record digest type invalid")
    if record["record_sha256"] != record_sha256(record):
        raise ValidationError("record self digest invalid")
    _strict_equal(record, expected_record(workspace), "power route record")
    _validate_live_inputs(workspace)
    _validate_semantics(record)
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "control_predicate_value": True,
        "synthetic_certified_seed_count": 241,
        "B07_open": True,
        "F060_open": True,
        "F061_open": True,
        "F110_open": True,
        "F128_through_F138_open_count": 11,
        "candidate_alpha_and_power_only": True,
        "scientific_effect": 0,
        "validation": "PASS",
    }


__all__ = [
    "ValidationError", "canonical_machine_bytes", "certified_seed_count",
    "expected_record", "record_sha256", "validate",
]
