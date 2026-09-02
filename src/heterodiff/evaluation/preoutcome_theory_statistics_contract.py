"""Frozen pre-outcome theory and statistics decisions.

This module contains no data reader, writer, randomness, training, network, or
runtime entrypoint.  It implements the exact decision algebra needed by the
F109--F112, F114--F127/F149, and F130--F138 closure package.  All scientific
inputs are caller supplied; invalid or incomplete inputs refuse rather than
silently changing the frozen plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
from typing import Dict, Mapping, Sequence, Tuple


PHYSIONET_DOMAIN_ID = "R3-PHYS"
RETAIL_DOMAIN_ID = "R4-RETAIL"
DOMAIN_IDS = (PHYSIONET_DOMAIN_ID, RETAIL_DOMAIN_ID)

CONDITIONAL_DRAWS_PER_CASE = 64
PRIMARY_SCORE_RANGE = (Fraction(-2), Fraction(1))
PAIRED_DIFFERENCE_RANGE = (Fraction(-3), Fraction(3))
PAIRED_DIFFERENCE_WIDTH = Fraction(6)
MINIMUM_MEANINGFUL_EFFECT = Fraction(1, 100)
PLANNING_ALTERNATIVE_EFFECT = Fraction(1)

FAMILYWISE_ALPHA = Fraction(1, 20)
PLANNING_ALPHA_PER_DOMAIN = Fraction(1, 40)
PLANNING_FAILURE_PROBABILITY_PER_DOMAIN = Fraction(1, 20)
TARGET_JOINT_POWER = Fraction(9, 10)

INDEPENDENT_TRAINING_SEED_COUNT = 256
NATURAL_GROUP_COUNT_BY_DOMAIN: Mapping[str, int] = {
    PHYSIONET_DOMAIN_ID: 128,
    RETAIL_DOMAIN_ID: 128,
}
CONDITIONING_CASES_PER_GROUP = 1
CONFIDENCE_INTERVAL_RESAMPLE_COUNT = 0

REAL_REAL_FLOOR_PARTITION_COUNT = 256
REAL_REAL_FLOOR_QUANTILE = Fraction(19, 20)
REAL_REAL_FLOOR_ID = (
    "VALIDATION_ONLY_GROUP_DISJOINT_SAME_CKS_BIASED_MMD2_"
    "DETERMINISTIC_256_SPLIT_Q95_NOT_SUBTRACTED"
)
CONFIDENCE_METHOD_ID = (
    "FIXED_N_SEED_LEVEL_ONE_SIDED_HOEFFDING_"
    "EXACT_LOG_BOUND_TWO_DOMAIN_HOLM_V1"
)
PILOT_VARIANCE_SOURCE = (
    "NO_EMPIRICAL_PILOT_DISTRIBUTION_FREE_CKS_PAIRED_RANGE_"
    "MINUS3_TO3_WIDTH6"
)

C17_FINAL_PUBLICATION_WORDING = (
    "Claim C17 is retired from this route. We do not state or imply an "
    "end-to-end path-KL or total-variation theorem, an excess-risk-to-hybrid-"
    "Dirichlet control, or any empirical consequence attributed to C17."
)

LOG_SERIES_TERMS = 64
SQRT_FRACTION_BITS = 192
_MAX_COMPONENT_BITS = 4096
_SEED_PREFIX = b"HETERODIFF-CONFIRMATORY-TRAINING-SEED-REGISTRY-V1\x00"
_FLOOR_PREFIX = b"HETERODIFF-REAL-REAL-FLOOR-PARTITION-V1\x00"


class StatisticalContractError(ValueError):
    """Raised when caller material violates the frozen contract."""


def _exact_fraction(value: object, *, label: str) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError(f"{label} must be an exact Fraction")
    if (
        value.numerator.bit_length() > _MAX_COMPONENT_BITS
        or value.denominator.bit_length() > _MAX_COMPONENT_BITS
    ):
        raise StatisticalContractError(f"{label} exceeds the rational bit bound")
    return value


def _exact_int(value: object, *, label: str, minimum: int = 0) -> int:
    if type(value) is not int:
        raise TypeError(f"{label} must be an exact integer")
    if value < minimum:
        raise StatisticalContractError(f"{label} is below its minimum")
    return value


def _log_unit_interval(value: Fraction) -> Tuple[Fraction, Fraction]:
    if not Fraction(1) <= value <= Fraction(2):
        raise StatisticalContractError("log series input must lie in [1,2]")
    z = (value - 1) / (value + 1)
    z_squared = z * z
    power = z
    lower = Fraction(0)
    for ordinal in range(LOG_SERIES_TERMS):
        lower += Fraction(2, 2 * ordinal + 1) * power
        power *= z_squared
    if z == 0:
        return lower, lower
    tail = Fraction(2, 2 * LOG_SERIES_TERMS + 1) * power / (1 - z_squared)
    return lower, lower + tail


def log_interval_ge_one(value: object) -> Tuple[Fraction, Fraction]:
    """Return rigorous rational lower and upper bounds for ``ln(value)``."""

    exact = _exact_fraction(value, label="value")
    if exact < 1:
        raise StatisticalContractError("log input must be at least one")
    exponent = 0
    normalized = exact
    while normalized >= 2:
        normalized /= 2
        exponent += 1
        if exponent > _MAX_COMPONENT_BITS:
            raise StatisticalContractError("log normalization exceeded the bound")
    ln2_lower, ln2_upper = _log_unit_interval(Fraction(2))
    residual_lower, residual_upper = _log_unit_interval(normalized)
    return (
        exponent * ln2_lower + residual_lower,
        exponent * ln2_upper + residual_upper,
    )


def _ceil_fraction(value: Fraction) -> int:
    quotient, remainder = divmod(value.numerator, value.denominator)
    return quotient + (1 if remainder else 0)


def _ceil_sqrt_integer(value: int) -> int:
    root = math.isqrt(value)
    return root if root * root == value else root + 1


def sqrt_upper(value: object) -> Fraction:
    """Return a 192-bit rational upper enclosure of a nonnegative square root."""

    exact = _exact_fraction(value, label="value")
    if exact < 0:
        raise StatisticalContractError("square-root input must be nonnegative")
    if exact == 0:
        return Fraction(0)
    scale = 1 << SQRT_FRACTION_BITS
    numerator = exact.numerator * exact.denominator * scale * scale
    root = _ceil_sqrt_integer(numerator)
    return Fraction(root, exact.denominator * scale)


def certified_seed_count(
    *,
    width: object,
    alpha_star: object,
    beta_star: object,
    null_margin: object,
    alternative: object,
) -> int:
    """Return the exact conservative Hoeffding sufficient seed count."""

    width_f = _exact_fraction(width, label="width")
    alpha_f = _exact_fraction(alpha_star, label="alpha_star")
    beta_f = _exact_fraction(beta_star, label="beta_star")
    null_f = _exact_fraction(null_margin, label="null_margin")
    alternative_f = _exact_fraction(alternative, label="alternative")
    if width_f <= 0:
        raise StatisticalContractError("width must be positive")
    if not 0 < alpha_f < 1 or not 0 < beta_f < 1:
        raise StatisticalContractError("tail probabilities must lie in (0,1)")
    if alternative_f <= null_f:
        raise StatisticalContractError("alternative must exceed the null margin")
    _, log_alpha_upper = log_interval_ge_one(1 / alpha_f)
    _, log_beta_upper = log_interval_ge_one(1 / beta_f)
    gap = alternative_f - null_f
    conservative = width_f * width_f * (log_alpha_upper + log_beta_upper) / (
        gap * gap
    )
    return _ceil_fraction(conservative)


CERTIFIED_MINIMUM_TRAINING_SEEDS = certified_seed_count(
    width=PAIRED_DIFFERENCE_WIDTH,
    alpha_star=PLANNING_ALPHA_PER_DOMAIN,
    beta_star=PLANNING_FAILURE_PROBABILITY_PER_DOMAIN,
    null_margin=MINIMUM_MEANINGFUL_EFFECT,
    alternative=PLANNING_ALTERNATIVE_EFFECT,
)


def confirmatory_seed_registry() -> Tuple[int, ...]:
    """Return the frozen deterministic 256-value uint64 training-seed roster.

    The roster is an address schedule, not evidence of physical randomness or
    independence.  Execution remains inadmissible until the separately required
    runtime audit verifies disjoint streams and the assumed seed-level law.
    """

    values = []
    for ordinal in range(INDEPENDENT_TRAINING_SEED_COUNT):
        payload = _SEED_PREFIX + ordinal.to_bytes(4, "big")
        values.append(int.from_bytes(hashlib.sha256(payload).digest()[:8], "big"))
    result = tuple(values)
    if len(set(result)) != len(result):
        raise RuntimeError("the frozen seed derivation has a collision")
    return result


CONFIRMATORY_SEED_REGISTRY = confirmatory_seed_registry()
CONFIRMATORY_SEED_REGISTRY_SHA256 = hashlib.sha256(
    b"".join(value.to_bytes(8, "big") for value in CONFIRMATORY_SEED_REGISTRY)
).hexdigest()


def _seed_level_values(values: object) -> Tuple[Fraction, ...]:
    if type(values) is not tuple:
        raise TypeError("seed values must be an exact tuple")
    if len(values) != INDEPENDENT_TRAINING_SEED_COUNT:
        raise StatisticalContractError("the complete 256-seed roster is required")
    result = []
    for ordinal, value in enumerate(values):
        exact = _exact_fraction(value, label=f"seed_values[{ordinal}]")
        if not PAIRED_DIFFERENCE_RANGE[0] <= exact <= PAIRED_DIFFERENCE_RANGE[1]:
            raise StatisticalContractError("a seed statistic is outside [-3,3]")
        result.append(exact)
    return tuple(result)


def hoeffding_exponent(seed_values: object) -> Fraction:
    """Return ``2*S*max(mean-delta0,0)^2/W^2`` exactly."""

    values = _seed_level_values(seed_values)
    mean = sum(values, Fraction(0)) / len(values)
    gap = max(mean - MINIMUM_MEANINGFUL_EFFECT, Fraction(0))
    return Fraction(2 * len(values)) * gap * gap / (
        PAIRED_DIFFERENCE_WIDTH * PAIRED_DIFFERENCE_WIDTH
    )


def hoeffding_lower_bound(seed_values: object, *, alpha: object) -> Fraction:
    """Return a conservative exact rational one-sided lower confidence bound."""

    values = _seed_level_values(seed_values)
    alpha_f = _exact_fraction(alpha, label="alpha")
    if not 0 < alpha_f < 1:
        raise StatisticalContractError("alpha must lie in (0,1)")
    mean = sum(values, Fraction(0)) / len(values)
    _, log_upper = log_interval_ge_one(1 / alpha_f)
    radius = PAIRED_DIFFERENCE_WIDTH * sqrt_upper(
        log_upper / (2 * len(values))
    )
    return mean - radius


@dataclass(frozen=True)
class HolmHoeffdingResult:
    ordered_domains: Tuple[str, str]
    exponent_by_domain: Mapping[str, Fraction]
    alpha_by_domain: Mapping[str, Fraction]
    lower_bound_by_domain: Mapping[str, Fraction]
    rejected_by_domain: Mapping[str, bool]
    family_pass: bool


def two_domain_holm_hoeffding(
    *, physionet_seed_values: object, retail_seed_values: object
) -> HolmHoeffdingResult:
    """Apply the exact conservative two-domain Holm/Hoeffding decision."""

    values_by_domain = {
        PHYSIONET_DOMAIN_ID: _seed_level_values(physionet_seed_values),
        RETAIL_DOMAIN_ID: _seed_level_values(retail_seed_values),
    }
    exponents = {
        domain: hoeffding_exponent(values) for domain, values in values_by_domain.items()
    }
    ordered = tuple(
        sorted(DOMAIN_IDS, key=lambda domain: (-exponents[domain], DOMAIN_IDS.index(domain)))
    )
    if len(ordered) != 2:
        raise RuntimeError("the frozen family must contain exactly two domains")
    first, second = ordered
    alpha_by_domain: Dict[str, Fraction] = {
        first: Fraction(1, 40),
        second: Fraction(1, 20),
    }
    _, log40_upper = log_interval_ge_one(Fraction(40))
    _, log20_upper = log_interval_ge_one(Fraction(20))
    first_reject = exponents[first] >= log40_upper
    second_reject = first_reject and exponents[second] >= log20_upper
    rejected = {first: first_reject, second: second_reject}
    lower_bounds = {
        domain: hoeffding_lower_bound(
            values_by_domain[domain], alpha=alpha_by_domain[domain]
        )
        for domain in DOMAIN_IDS
    }
    return HolmHoeffdingResult(
        ordered_domains=(first, second),
        exponent_by_domain=exponents,
        alpha_by_domain=alpha_by_domain,
        lower_bound_by_domain=lower_bounds,
        rejected_by_domain=rejected,
        family_pass=all(rejected.values()),
    )


def _canonical_group_id(value: object) -> str:
    if type(value) is not str:
        raise TypeError("group IDs must be exact strings")
    if not value or not value.isascii() or any(ord(character) < 0x21 or ord(character) > 0x7E for character in value):
        raise StatisticalContractError("group IDs must be nonempty visible ASCII")
    return value


def real_real_floor_partitions(
    *, domain_id: object, group_ids: object
) -> Tuple[Tuple[Tuple[str, ...], Tuple[str, ...]], ...]:
    """Return 256 deterministic, balanced, group-disjoint floor partitions."""

    if type(domain_id) is not str or domain_id not in DOMAIN_IDS:
        raise StatisticalContractError("domain_id is not frozen")
    if type(group_ids) is not tuple:
        raise TypeError("group_ids must be an exact tuple")
    groups = tuple(_canonical_group_id(value) for value in group_ids)
    if len(groups) != NATURAL_GROUP_COUNT_BY_DOMAIN[domain_id]:
        raise StatisticalContractError("the exact 128-group roster is required")
    if len(set(groups)) != len(groups):
        raise StatisticalContractError("group IDs must be distinct")
    canonical = tuple(sorted(groups))
    partitions = []
    for repeat in range(REAL_REAL_FLOOR_PARTITION_COUNT):
        salt = repeat.to_bytes(4, "big")
        ranked = sorted(
            canonical,
            key=lambda group: (
                hashlib.sha256(
                    _FLOOR_PREFIX
                    + domain_id.encode("ascii")
                    + b"\x00"
                    + salt
                    + b"\x00"
                    + group.encode("ascii")
                ).digest(),
                group,
            ),
        )
        midpoint = len(ranked) // 2
        partitions.append((tuple(ranked[:midpoint]), tuple(ranked[midpoint:])))
    return tuple(partitions)


def real_real_floor_q95(values: object) -> Fraction:
    """Return the frozen nearest-rank 95th percentile of 256 floor values."""

    if type(values) is not tuple or len(values) != REAL_REAL_FLOOR_PARTITION_COUNT:
        raise StatisticalContractError("exactly 256 floor values are required")
    exact_values = []
    for ordinal, value in enumerate(values):
        exact = _exact_fraction(value, label=f"floor_values[{ordinal}]")
        if not 0 <= exact <= 2:
            raise StatisticalContractError("a biased MMD-squared floor is outside [0,2]")
        exact_values.append(exact)
    ordered = sorted(exact_values)
    rank = _ceil_fraction(REAL_REAL_FLOOR_QUANTILE * len(ordered))
    return ordered[rank - 1]


CALIBRATION_COVERAGE_MAX_ABSOLUTE_ERROR = Fraction(1, 20)
SUPPORT_VIOLATION_MAXIMUM = 0
FIDELITY_GUIDE_MINUS_DIRECT_MAXIMUM = Fraction(0)
INITIALIZER_KL_MAXIMUM_NAT = Fraction(1, 100)
ASSOCIATION_TV_MAXIMUM = Fraction(1, 100)
RUN_FAILURE_RATE_MAXIMUM = Fraction(1, 20)
LATENCY_RATIO_MAXIMUM = Fraction(2)
PEAK_MEMORY_RATIO_MAXIMUM = Fraction(2)
TOTAL_COMPUTE_RATIO_MAXIMUM = Fraction(1)
B05_CERTIFICATION_SCOPE_ID = "B05_FROZEN_CONSTRAINT_INPUT_ENVELOPE_V1"
B05_ATTEMPT_MANIFEST_DOMAIN = b"HETERODIFF-B05-ATTEMPT-MANIFEST-V1\x00"
B05_TERMINAL_STATUSES = (
    "COMPLETE",
    "ALGORITHMIC_FAILURE",
    "NONFINITE",
    "OOM_OR_TIMEOUT",
    "INFRA_ABORT",
)
B05_VALUE_SPECS = (
    (
        "calibration_coverage_abs_error_upper",
        "ABSOLUTE_PROBABILITY_ERROR",
        "CERTIFIED_UPPER_ENDPOINT",
    ),
    (
        "support_violation_count",
        "INTEGER_VIOLATION_COUNT",
        "CERTIFIED_EXACT_COUNT",
    ),
    (
        "fidelity_guide_minus_direct_upper",
        "FROZEN_EVENT_COUNT_TYPE_MARK_TIME_ERROR_DIFFERENCE",
        "CERTIFIED_UPPER_ENDPOINT",
    ),
    (
        "initializer_kl_upper_nat",
        "NAT",
        "CERTIFIED_UPPER_ENDPOINT",
    ),
    (
        "association_tv_upper",
        "TOTAL_VARIATION",
        "CERTIFIED_UPPER_ENDPOINT",
    ),
    (
        "guide_latency_upper",
        "NANOSECOND",
        "CERTIFIED_UPPER_ENDPOINT",
    ),
    (
        "direct_latency_lower",
        "NANOSECOND",
        "CERTIFIED_POSITIVE_LOWER_ENDPOINT",
    ),
    (
        "guide_peak_memory_upper",
        "BYTE",
        "CERTIFIED_UPPER_ENDPOINT",
    ),
    (
        "direct_peak_memory_lower",
        "BYTE",
        "CERTIFIED_POSITIVE_LOWER_ENDPOINT",
    ),
    (
        "guide_total_compute_upper",
        "F104_MATCHED_TOTAL_COMPUTE_UNIT",
        "CERTIFIED_UPPER_ENDPOINT",
    ),
    (
        "direct_total_compute_lower",
        "F104_MATCHED_TOTAL_COMPUTE_UNIT",
        "CERTIFIED_POSITIVE_LOWER_ENDPOINT",
    ),
)


def _lower_hex_sha256(value: object, *, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise StatisticalContractError(f"{label} must be lowercase SHA-256 hex")
    return value


def _canonical_attempt_id(value: object) -> str:
    if type(value) is not str or not value:
        raise TypeError("attempt_id must be a nonempty exact string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as error:
        raise StatisticalContractError("attempt_id must be canonical ASCII") from error
    if any(byte < 0x21 or byte > 0x7E for byte in encoded):
        raise StatisticalContractError(
            "attempt_id must be visible ASCII without whitespace"
        )
    return value


@dataclass(frozen=True)
class B05AttemptStatus:
    """One scheduled attempt and its terminal, never-dropped status."""

    attempt_id: str
    status: str

    def __post_init__(self) -> None:
        _canonical_attempt_id(self.attempt_id)
        if type(self.status) is not str or self.status not in B05_TERMINAL_STATUSES:
            raise StatisticalContractError("status is outside the frozen terminal roster")


def b05_attempt_manifest_sha256(attempts: object) -> str:
    """Bind the exact ordered scheduled-attempt roster and terminal statuses."""

    if type(attempts) is not tuple or not attempts:
        raise StatisticalContractError("attempts must be a nonempty exact tuple")
    payload = bytearray(B05_ATTEMPT_MANIFEST_DOMAIN)
    seen = set()
    for ordinal, attempt in enumerate(attempts):
        if type(attempt) is not B05AttemptStatus:
            raise TypeError(f"attempts[{ordinal}] must be an exact B05AttemptStatus")
        if attempt.attempt_id in seen:
            raise StatisticalContractError("scheduled attempt IDs must be unique")
        seen.add(attempt.attempt_id)
        for value in (attempt.attempt_id, attempt.status):
            encoded = value.encode("ascii")
            payload.extend(len(encoded).to_bytes(4, "big"))
            payload.extend(encoded)
    return hashlib.sha256(bytes(payload)).hexdigest()


@dataclass(frozen=True)
class B05CertifiedValue:
    """One typed scalar plus exact roster/attempt/receipt bindings.

    The receipt digest is an opaque caller-supplied reference.  This pure
    module checks internal binding consistency but does not authenticate the
    external certifier or turn a digest into scientific evidence.
    """

    metric_id: str
    unit_id: str
    bound_kind: str
    value: object
    roster_sha256: str
    attempt_manifest_sha256: str
    certification_receipt_sha256: str
    certification_scope_id: str

    def __post_init__(self) -> None:
        if type(self.metric_id) is not str:
            raise TypeError("metric_id must be an exact string")
        if type(self.unit_id) is not str:
            raise TypeError("unit_id must be an exact string")
        if type(self.bound_kind) is not str:
            raise TypeError("bound_kind must be an exact string")
        _lower_hex_sha256(self.roster_sha256, label="roster_sha256")
        _lower_hex_sha256(
            self.attempt_manifest_sha256, label="attempt_manifest_sha256"
        )
        _lower_hex_sha256(
            self.certification_receipt_sha256,
            label="certification_receipt_sha256",
        )
        if self.certification_scope_id != B05_CERTIFICATION_SCOPE_ID:
            raise StatisticalContractError("certification_scope_id is not frozen")


@dataclass(frozen=True)
class B05ConstraintDecision:
    component_thresholds_satisfied: Mapping[str, bool]
    failure_rate: Fraction
    latency_ratio: Fraction
    peak_memory_ratio: Fraction
    total_compute_ratio: Fraction
    all_frozen_inequalities_satisfied: bool
    project_gate_pass: bool
    external_certification_authenticated: bool
    roster_sha256: str
    attempt_manifest_sha256: str
    certification_receipt_sha256: str


def evaluate_b05_constraints(
    *,
    certified_values: object,
    attempts: object,
    roster_sha256: object,
    certification_receipt_sha256: object,
) -> B05ConstraintDecision:
    """Apply frozen algebra after exact metadata-shape and cross-binding checks.

    A true ``all_frozen_inequalities_satisfied`` value is not a project PASS.
    This offline pure function cannot authenticate the external receipt or the
    truth of caller-supplied roster/value assertions, so both authentication
    and ``project_gate_pass`` are deliberately returned as false.
    """

    roster_digest = _lower_hex_sha256(roster_sha256, label="roster_sha256")
    receipt_digest = _lower_hex_sha256(
        certification_receipt_sha256, label="certification_receipt_sha256"
    )
    if type(attempts) is not tuple:
        raise TypeError("attempts must be an exact tuple")
    attempt_digest = b05_attempt_manifest_sha256(attempts)
    if type(certified_values) is not tuple:
        raise TypeError("certified_values must be an exact tuple")
    if len(certified_values) != len(B05_VALUE_SPECS):
        raise StatisticalContractError("the complete B05 certified-value roster is required")
    normalized: Dict[str, object] = {}
    for ordinal, (supplied, spec) in enumerate(zip(certified_values, B05_VALUE_SPECS)):
        if type(supplied) is not B05CertifiedValue:
            raise TypeError(
                f"certified_values[{ordinal}] must be an exact B05CertifiedValue"
            )
        metric_id, unit_id, bound_kind = spec
        if (
            supplied.metric_id != metric_id
            or supplied.unit_id != unit_id
            or supplied.bound_kind != bound_kind
        ):
            raise StatisticalContractError(
                "certified value metric/unit/bound roster mismatch"
            )
        if (
            supplied.roster_sha256 != roster_digest
            or supplied.attempt_manifest_sha256 != attempt_digest
            or supplied.certification_receipt_sha256 != receipt_digest
        ):
            raise StatisticalContractError(
                "certified value roster/attempt/receipt cross-binding mismatch"
            )
        normalized[metric_id] = supplied.value

    calibration = _exact_fraction(
        normalized["calibration_coverage_abs_error_upper"],
        label="calibration error upper",
    )
    violations = _exact_int(
        normalized["support_violation_count"], label="support violations"
    )
    fidelity = _exact_fraction(
        normalized["fidelity_guide_minus_direct_upper"],
        label="fidelity difference upper",
    )
    initializer = _exact_fraction(
        normalized["initializer_kl_upper_nat"], label="initializer KL"
    )
    association = _exact_fraction(
        normalized["association_tv_upper"], label="association TV"
    )
    if calibration < 0 or initializer < 0 or not 0 <= association <= 1:
        raise StatisticalContractError("error endpoints are outside their domains")

    def positive_ratio(numerator: object, denominator: object, label: str) -> Fraction:
        left = _exact_fraction(numerator, label=label + " numerator")
        right = _exact_fraction(denominator, label=label + " denominator")
        if left < 0 or right <= 0:
            raise StatisticalContractError(label + " inputs are outside their domain")
        return left / right

    failures = sum(attempt.status != "COMPLETE" for attempt in attempts)
    failure_rate = Fraction(failures, len(attempts))
    latency_ratio = positive_ratio(
        normalized["guide_latency_upper"],
        normalized["direct_latency_lower"],
        "latency",
    )
    memory_ratio = positive_ratio(
        normalized["guide_peak_memory_upper"],
        normalized["direct_peak_memory_lower"],
        "peak memory",
    )
    compute_ratio = positive_ratio(
        normalized["guide_total_compute_upper"],
        normalized["direct_total_compute_lower"],
        "total compute",
    )
    passes = {
        "calibration-and-coverage": calibration
        <= CALIBRATION_COVERAGE_MAX_ABSOLUTE_ERROR,
        "support-validity": violations <= SUPPORT_VIOLATION_MAXIMUM,
        "event-count-type-mark-and-time-fidelity": fidelity
        <= FIDELITY_GUIDE_MINUS_DIRECT_MAXIMUM,
        "initializer-error": initializer <= INITIALIZER_KL_MAXIMUM_NAT,
        "association-approximation-error": association <= ASSOCIATION_TV_MAXIMUM,
        "run-failure-rate": failure_rate <= RUN_FAILURE_RATE_MAXIMUM,
        "latency": latency_ratio <= LATENCY_RATIO_MAXIMUM,
        "peak-memory": memory_ratio <= PEAK_MEMORY_RATIO_MAXIMUM,
        "total-compute": compute_ratio <= TOTAL_COMPUTE_RATIO_MAXIMUM,
    }
    return B05ConstraintDecision(
        component_thresholds_satisfied=passes,
        failure_rate=failure_rate,
        latency_ratio=latency_ratio,
        peak_memory_ratio=memory_ratio,
        total_compute_ratio=compute_ratio,
        all_frozen_inequalities_satisfied=all(passes.values()),
        project_gate_pass=False,
        external_certification_authenticated=False,
        roster_sha256=roster_digest,
        attempt_manifest_sha256=attempt_digest,
        certification_receipt_sha256=receipt_digest,
    )


__all__ = [
    "ASSOCIATION_TV_MAXIMUM",
    "B05_ATTEMPT_MANIFEST_DOMAIN",
    "B05_CERTIFICATION_SCOPE_ID",
    "B05_TERMINAL_STATUSES",
    "B05_VALUE_SPECS",
    "B05AttemptStatus",
    "B05CertifiedValue",
    "B05ConstraintDecision",
    "CALIBRATION_COVERAGE_MAX_ABSOLUTE_ERROR",
    "CERTIFIED_MINIMUM_TRAINING_SEEDS",
    "C17_FINAL_PUBLICATION_WORDING",
    "CONDITIONAL_DRAWS_PER_CASE",
    "CONDITIONING_CASES_PER_GROUP",
    "CONFIDENCE_INTERVAL_RESAMPLE_COUNT",
    "CONFIDENCE_METHOD_ID",
    "CONFIRMATORY_SEED_REGISTRY",
    "CONFIRMATORY_SEED_REGISTRY_SHA256",
    "DOMAIN_IDS",
    "FAMILYWISE_ALPHA",
    "FIDELITY_GUIDE_MINUS_DIRECT_MAXIMUM",
    "HolmHoeffdingResult",
    "INDEPENDENT_TRAINING_SEED_COUNT",
    "INITIALIZER_KL_MAXIMUM_NAT",
    "LATENCY_RATIO_MAXIMUM",
    "MINIMUM_MEANINGFUL_EFFECT",
    "NATURAL_GROUP_COUNT_BY_DOMAIN",
    "PAIRED_DIFFERENCE_RANGE",
    "PAIRED_DIFFERENCE_WIDTH",
    "PEAK_MEMORY_RATIO_MAXIMUM",
    "PHYSIONET_DOMAIN_ID",
    "PILOT_VARIANCE_SOURCE",
    "PLANNING_ALTERNATIVE_EFFECT",
    "REAL_REAL_FLOOR_ID",
    "REAL_REAL_FLOOR_PARTITION_COUNT",
    "REAL_REAL_FLOOR_QUANTILE",
    "RETAIL_DOMAIN_ID",
    "RUN_FAILURE_RATE_MAXIMUM",
    "StatisticalContractError",
    "TOTAL_COMPUTE_RATIO_MAXIMUM",
    "TARGET_JOINT_POWER",
    "certified_seed_count",
    "b05_attempt_manifest_sha256",
    "confirmatory_seed_registry",
    "evaluate_b05_constraints",
    "hoeffding_exponent",
    "hoeffding_lower_bound",
    "log_interval_ge_one",
    "real_real_floor_partitions",
    "real_real_floor_q95",
    "sqrt_upper",
    "two_domain_holm_hoeffding",
]
