"""Certified reference for one finite occurrence-marked CTMC--OU fixture.

The fixture has an empty mode and two cap-one occupied modes.  An occupied
mode owns one scalar OU mark; births draw a destination mark from the invariant
Gaussian fiber, deaths remove it, and replacements change type while retaining
the mark.  The terminal observation is a normalized Gaussian/clutter mixture.

All authoritative calculations use exact rational arithmetic plus outward
enclosures with proved analytic tails.  Matrix exponentials use nonnegative
uniformization.  Exponential, logarithm, and square-root values use rational
Taylor/integer-root bounds.  Time integrals use composite Simpson quadrature
plus an interval fourth-derivative certificate.  No adaptive-library error
estimate, binary64 comparison, or cross-method difference is a bound.

This is a deterministic pre-outcome design/reference module.  It has no file,
network, subprocess, entropy, data, training, or runtime worker route.  The
cap-one quantitative path subject is paired in the same suite with a cap-two
``AA`` factorial/multiplicity and two-association structural witness.  The
cap-two witness is not substituted into the cap-one path integral.  This
module is not R1, R2, C17, B05, or claim evidence.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SCHEMA = "heterodiff-mixed-marked-ctmc-ou-certified-reference-v1"
STATE = "PREOUTCOME_KNOWN_LAW_DESIGN_REFERENCE_ONLY"
ORIENTATION = "KL(P_EXACT_H||P_CANDIDATE_HAT_H)"
CERTIFICATE_DOMAIN = (SCHEMA + "\0").encode("ascii")
TABLE_DOMAIN = (SCHEMA + "/tables\0").encode("ascii")
GRID_DOMAIN = (SCHEMA + "/grid\0").encode("ascii")
EXACT_SELF_DOMAIN = (SCHEMA + "/exact-self\0").encode("ascii")
FROZEN_CERTIFICATE_SHA256 = "e202379f735e76dc43105cff62e4ff443a97ff810d89edecaf8091e5eefe187d"

EXP_TERMS = 64
MAX_EXP_TERMS = 160
UNIFORMIZATION_TERMS = 32
SIMPSON_SUBINTERVALS = 1024
MAX_SERIALIZED_BYTES = 1_000_000
MAX_TREE_NODES = 80_000
MAX_TREE_DEPTH = 32
MAX_CONTAINER_ITEMS = 20_000
MAX_TEXT_CHARS = 4096
MAX_INTEGER_BITS = 100_000

ZERO = Fraction(0)
ONE = Fraction(1)
TWO = Fraction(2)
HALF = Fraction(1, 2)

MODE_NAMES = ("EMPTY", "ALPHA", "BETA")
EMPTY = 0
ALPHA = 1
BETA = 2
HORIZON = ONE

# Row-source/column-destination mode generator.
BIRTH_RATES = (Fraction(1, 2), Fraction(1, 3))
DEATH_RATES = (Fraction(2, 5), Fraction(3, 5))
REPLACEMENT_RATES = (Fraction(1, 4), Fraction(1, 5))
MODE_GENERATOR: Tuple[Tuple[Fraction, ...], ...] = (
    (Fraction(-5, 6), Fraction(1, 2), Fraction(1, 3)),
    (Fraction(2, 5), Fraction(-13, 20), Fraction(1, 4)),
    (Fraction(3, 5), Fraction(1, 5), Fraction(-4, 5)),
)
STATIONARY_MODE_PROBABILITIES = (
    Fraction(282, 767),
    Fraction(280, 767),
    Fraction(205, 767),
)

# dX_t = -kappa X_t dt + sigma dW_t; N(0,1) is invariant.
OU_MEAN_REVERSION = Fraction(1, 2)
OU_DIFFUSION = ONE
OU_INVARIANT_MEAN = ZERO
OU_INVARIANT_VARIANCE = ONE
OBSERVATION_NOISE_VARIANCE = ONE
OBSERVATION_REFERENCE_VARIANCE = TWO

# K(.|empty)=lambda; K(.|i,x)=b_i*lambda+a_i*N(.|x,1).
OBSERVATION_CLUTTER_WEIGHTS = (Fraction(1, 4), Fraction(1, 2))
OBSERVATION_MARK_WEIGHTS = (Fraction(3, 4), Fraction(1, 2))
OBSERVATION_VALUE = ZERO

# Killed occupied-type coefficient generator and terminal mark coefficients.
KILLED_TYPE_GENERATOR: Tuple[Tuple[Fraction, ...], ...] = (
    (Fraction(-13, 20), Fraction(1, 4)),
    (Fraction(1, 5), Fraction(-4, 5)),
)
TERMINAL_MARK_COEFFICIENTS = OBSERVATION_MARK_WEIGHTS

# Nonzero terminal-matched reference perturbation used only to qualify the
# five-term identity and rigorous integrator.  It is not a candidate PASS.
RESIDUAL_MODE_CONSTANTS = (ZERO, Fraction(1, 5), Fraction(-1, 4))
RESIDUAL_MARK_SLOPE = Fraction(1, 3)
NUISANCE_GAUGE = Fraction(2, 7)
CLASSIFIER_NUISANCE = Fraction(2, 7)

TIME_GRID = (
    ZERO,
    Fraction(1, 4),
    Fraction(1, 2),
    Fraction(3, 4),
    ONE,
)
MARK_GRID = (
    Fraction(-2),
    Fraction(-1),
    ZERO,
    ONE,
    TWO,
)

# Scientific known-law implementation acceptance ceilings.  A candidate
# passes only when the certified upper endpoint of its error is at most the
# ceiling.  Width budgets below are independent arithmetic-quality controls.
SCIENTIFIC_THRESHOLDS: Mapping[str, Fraction] = MappingProxyType({
    "F011_KL": Fraction(1, 10**8),
    "F011_TV": Fraction(1, 10**6),
    "F011_CALIBRATION": Fraction(1, 10**8),
    "F012_DRIFT": Fraction(1, 10**8),
    "F013_BIRTH_LOG_RATIO": Fraction(1, 10**8),
    "F014_DEATH_LOG_RATIO": Fraction(1, 10**8),
    "F015_REPLACEMENT_LOG_RATIO": Fraction(1, 10**8),
    "F016_INITIALIZER_KL": Fraction(1, 10**8),
    "F016_INITIALIZER_TV": Fraction(1, 10**6),
    "F017_ENDPOINT_KL": Fraction(1, 10**8),
    "F017_ENDPOINT_TV": Fraction(1, 10**6),
    "F018_PATH_KL": Fraction(1, 10**8),
})
NUMERICAL_WIDTH_BUDGETS: Mapping[str, Fraction] = MappingProxyType({
    "F011_KL": Fraction(1, 10**12),
    "F011_TV": Fraction(1, 10**12),
    "F011_CALIBRATION": Fraction(1, 10**12),
    "F012_DRIFT": Fraction(1, 10**12),
    "F013_BIRTH_LOG_RATIO": Fraction(1, 10**12),
    "F014_DEATH_LOG_RATIO": Fraction(1, 10**12),
    "F015_REPLACEMENT_LOG_RATIO": Fraction(1, 10**12),
    "F016_INITIALIZER_KL": Fraction(1, 10**12),
    "F016_INITIALIZER_TV": Fraction(1, 10**12),
    "F017_ENDPOINT_KL": Fraction(1, 10**12),
    "F017_ENDPOINT_TV": Fraction(1, 10**12),
    "F018_PATH_KL": Fraction(1, 10**10),
})

# Reference-arithmetic precision is a third, independent role.  These budgets
# do not certify a candidate and are never used as scientific error ceilings.
REFERENCE_WIDTH_BUDGETS: Mapping[str, Fraction] = MappingProxyType({
    "F011_CALIBRATION_REFERENCE": Fraction(1, 10**12),
    "F011_ASSOCIATION_REFERENCE": Fraction(1, 10**12),
    "F011_NONUNIT_RN_REFERENCE": Fraction(1, 10**12),
    "F011_CAP_BOUNDARY_BREGMAN_REFERENCE": Fraction(1, 10**12),
    "F012_DRIFT_REFERENCE": Fraction(1, 10**12),
    "F013_BIRTH_RATIO_REFERENCE": Fraction(1, 10**12),
    "F014_DEATH_RATIO_REFERENCE": Fraction(1, 10**12),
    "F015_REPLACEMENT_RATIO_REFERENCE": Fraction(1, 10**12),
    "F016_INITIALIZER_REFERENCE": Fraction(1, 10**12),
    "F017_ENDPOINT_REFERENCE": Fraction(1, 10**12),
    "F018_PATH_COMPONENT_REFERENCE": Fraction(1, 10**12),
    "F018_QUADRATURE_ROUTE_REFERENCE": Fraction(1, 10**12),
})

# Complete Section 7.3 table from the pre-D1 A1 specification.  The literal
# quantity labels are retained.  Its single two-denominator row is projected
# into two canonical decision rows so that both strict inequalities remain
# independently machine-checkable.
A1_SPEC_PATH = "research/62_a1_association_guided_residual_falsification_spec.md"
A1_SPEC_SHA256 = "475f4f450cb5703e6773c0d0ff242db995a16408acce5989401fa0674326e67c"
A1_SECTION_7_3: Tuple[Mapping[str, Any], ...] = (
    MappingProxyType({"canonical_id": "terminal_guide_target_log_density_max_abs_error", "literal_quantity": "terminal guide/target log-density error", "direction": "<=", "threshold": "1e-12", "unit": "log_density"}),
    MappingProxyType({"canonical_id": "terminal_residual_max_abs", "literal_quantity": "maximum terminal residual", "direction": "<=", "threshold": "1e-10", "unit": "log_density"}),
    MappingProxyType({"canonical_id": "oracle_self_path_kl", "literal_quantity": "oracle self path KL", "direction": "<=", "threshold": "1e-10", "unit": "nat"}),
    MappingProxyType({"canonical_id": "primary_refined_candidate_path_kl_abs_change", "literal_quantity": "primary/refined path-KL change", "direction": "<=", "threshold": "1e-8", "unit": "nat"}),
    MappingProxyType({"canonical_id": "primary_refined_unconditional_path_kl_abs_change", "literal_quantity": "primary/refined unconditional path-KL change", "direction": "<=", "threshold": "1e-8", "unit": "nat"}),
    MappingProxyType({"canonical_id": "primary_unconditional_denominator", "literal_quantity": "primary and refined unconditional denominator", "projected_member": "primary", "direction": ">", "threshold": "1e-12", "unit": "nat"}),
    MappingProxyType({"canonical_id": "refined_unconditional_denominator", "literal_quantity": "primary and refined unconditional denominator", "projected_member": "refined", "direction": ">", "threshold": "1e-12", "unit": "nat"}),
    MappingProxyType({"canonical_id": "exact_target_occupancy_max_abs_error", "literal_quantity": "exact-target occupancy maximum absolute error", "direction": "<=", "threshold": "1e-8", "unit": "probability"}),
    MappingProxyType({"canonical_id": "primary_refined_endpoint_tv_abs_change", "literal_quantity": "primary/refined endpoint TV", "direction": "<=", "threshold": "1e-8", "unit": "tv"}),
    MappingProxyType({"canonical_id": "generator_row_sum_max_abs_residual", "literal_quantity": "generator row-sum residual", "direction": "<=", "threshold": "1e-10", "unit": "rate"}),
    MappingProxyType({"canonical_id": "scalar_edit_cycle_max_abs_residual", "literal_quantity": "scalar edit-cycle residual", "direction": "<=", "threshold": "1e-10", "unit": "log_rate"}),
    MappingProxyType({"canonical_id": "oracle_product_positive_max_abs_logit", "literal_quantity": "oracle product-positive maximum absolute logit", "direction": "<=", "threshold": "1e-9", "unit": "logit"}),
)


class CertificationError(ValueError):
    """Raised when a frozen type, invariant, or enclosure fails closed."""


Interval = Tuple[Fraction, Fraction]
Matrix = Tuple[Tuple[Fraction, ...], ...]
IntervalMatrix = Tuple[Tuple[Interval, ...], ...]
Jet = Tuple[Interval, ...]


def _fraction_text(value: Fraction) -> str:
    if type(value) is not Fraction:
        raise TypeError("value must be an exact Fraction")
    return "%d/%d" % (value.numerator, value.denominator)


def _integer_token(value: Fraction) -> str:
    if type(value) is not Fraction or value.denominator != 1:
        raise CertificationError("normal-law label requires an exact integer parameter")
    return str(value.numerator)


def _normal_law_label(mean: Fraction, variance: Fraction) -> str:
    return "NORMAL_MEAN_%s_VARIANCE_%s" % (
        _integer_token(mean),
        _integer_token(variance),
    )


def _fraction_from_text(value: object) -> Fraction:
    if type(value) is not str or not value or len(value) > 4096 or value.count("/") != 1:
        raise CertificationError("fraction must be a bounded canonical string")
    numerator_text, denominator_text = value.split("/", 1)
    if not numerator_text or not denominator_text:
        raise CertificationError("fraction text is incomplete")
    if numerator_text.startswith("+") or denominator_text.startswith(("+", "-")):
        raise CertificationError("fraction sign form is noncanonical")
    try:
        numerator = int(numerator_text)
        denominator = int(denominator_text)
    except ValueError as exc:
        raise CertificationError("fraction text is not integral") from exc
    if denominator <= 0:
        raise CertificationError("fraction denominator must be positive")
    result = Fraction(numerator, denominator)
    if _fraction_text(result) != value:
        raise CertificationError("fraction text is not reduced canonical form")
    return result


def _interval(lower: Fraction, upper: Fraction) -> Interval:
    if type(lower) is not Fraction or type(upper) is not Fraction or lower > upper:
        raise CertificationError("invalid exact interval")
    return lower, upper


def _iexact(value: Fraction) -> Interval:
    return value, value


def _iadd(left: Interval, right: Interval) -> Interval:
    return _interval(left[0] + right[0], left[1] + right[1])


def _ineg(value: Interval) -> Interval:
    return _interval(-value[1], -value[0])


def _isub(left: Interval, right: Interval) -> Interval:
    return _iadd(left, _ineg(right))


def _imul(left: Interval, right: Interval) -> Interval:
    products = (
        left[0] * right[0],
        left[0] * right[1],
        left[1] * right[0],
        left[1] * right[1],
    )
    return _interval(min(products), max(products))


def _iscale(value: Interval, scalar: Fraction) -> Interval:
    return _imul(value, _iexact(scalar))


def _ireciprocal(value: Interval) -> Interval:
    if value[0] <= 0:
        raise CertificationError("reciprocal interval is not strictly positive")
    return _interval(ONE / value[1], ONE / value[0])


def _idiv(left: Interval, right: Interval) -> Interval:
    return _imul(left, _ireciprocal(right))


def _iwidth(value: Interval) -> Fraction:
    return value[1] - value[0]


def _imaxabs(value: Interval) -> Fraction:
    return max(abs(value[0]), abs(value[1]))


def _outward_decimal_interval(value: Interval, digits: int = 40) -> Interval:
    """Bound an internal exact interval by compact decimal rationals."""

    if type(digits) is not int or digits < 20 or digits > 100:
        raise ValueError("decimal interval precision outside frozen bounds")
    scale = 10**digits
    lower_integer = value[0].numerator * scale // value[0].denominator
    upper_numerator = value[1].numerator * scale
    upper_integer = -((-upper_numerator) // value[1].denominator)
    result = _interval(
        Fraction(lower_integer, scale),
        Fraction(upper_integer, scale),
    )
    if result[0] > value[0] or result[1] < value[1]:
        raise CertificationError("compact decimal interval is not outward")
    return result


def _exp_positive_bounds(value: Fraction, terms: int = EXP_TERMS) -> Interval:
    if type(value) is not Fraction or value < 0:
        raise TypeError("positive exponential input must be a nonnegative Fraction")
    if type(terms) is not int or terms < 8 or terms > MAX_EXP_TERMS:
        raise ValueError("exponential term count outside frozen bounds")
    term = ONE
    partial = ONE
    for index in range(1, terms + 1):
        term *= value / index
        partial += term
    next_term = term * value / (terms + 1)
    ratio = value / (terms + 2)
    if ratio >= ONE:
        raise CertificationError("exponential remainder ratio is not contractive")
    return _interval(partial, partial + next_term / (ONE - ratio))


def exp_bounds(value: Fraction) -> Interval:
    if type(value) is not Fraction:
        raise TypeError("exponential input must be an exact Fraction")
    if value >= ZERO:
        return _outward_decimal_interval(_exp_positive_bounds(value), 60)
    positive = _exp_positive_bounds(-value)
    return _outward_decimal_interval(
        _interval(ONE / positive[1], ONE / positive[0]), 60
    )


def _iexp(value: Interval) -> Interval:
    return _interval(exp_bounds(value[0])[0], exp_bounds(value[1])[1])


def _log_unit_bounds(value: Fraction, terms: int = EXP_TERMS) -> Interval:
    if value < ONE or value >= TWO:
        raise CertificationError("unit-log input must lie in [1,2)")
    z = (value - ONE) / (value + ONE)
    z_squared = z * z
    power = z
    partial = ZERO
    for index in range(terms):
        partial += power / (2 * index + 1)
        power *= z_squared
    tail = TWO * power / ((2 * terms + 1) * (ONE - z_squared))
    return _outward_decimal_interval(
        _interval(TWO * partial, TWO * partial + tail), 60
    )


_LOG_TWO_EPSILON = Fraction(1, 10**120)
_LOG_TWO_LEFT = _log_unit_bounds(TWO - _LOG_TWO_EPSILON)
_LOG_TWO = _interval(
    _LOG_TWO_LEFT[0],
    _LOG_TWO_LEFT[1] + _LOG_TWO_EPSILON / (TWO - _LOG_TWO_EPSILON),
)


def log_bounds(value: Fraction) -> Interval:
    if type(value) is not Fraction or value <= ZERO:
        raise TypeError("log input must be a positive exact Fraction")
    scaled = value
    exponent = 0
    while scaled < ONE:
        scaled *= TWO
        exponent -= 1
    while scaled >= TWO:
        scaled /= TWO
        exponent += 1
    return _outward_decimal_interval(
        _iadd(_log_unit_bounds(scaled), _iscale(_LOG_TWO, Fraction(exponent))),
        60,
    )


def _ilog(value: Interval) -> Interval:
    if value[0] <= ZERO:
        raise CertificationError("log interval is not strictly positive")
    return _interval(log_bounds(value[0])[0], log_bounds(value[1])[1])


def sqrt_bounds(value: Fraction, digits: int = 60) -> Interval:
    if type(value) is not Fraction or value < ZERO:
        raise TypeError("square-root input must be a nonnegative Fraction")
    if type(digits) is not int or digits < 10 or digits > 200:
        raise ValueError("square-root precision outside frozen bounds")
    if value == ZERO:
        return _iexact(ZERO)
    scale = 10**digits
    quotient = value.numerator * scale * scale // value.denominator
    root = math.isqrt(quotient)
    lower = Fraction(root, scale)
    upper = lower if lower * lower == value else Fraction(root + 1, scale)
    return _interval(lower, upper)


def _isqrt(value: Interval) -> Interval:
    if value[0] < ZERO:
        raise CertificationError("square-root interval contains a negative value")
    return _interval(sqrt_bounds(value[0])[0], sqrt_bounds(value[1])[1])


def _matrix_identity(size: int) -> Matrix:
    return tuple(
        tuple(ONE if row == column else ZERO for column in range(size))
        for row in range(size)
    )


def _matrix_add(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(a + b for a, b in zip(left_row, right_row))
        for left_row, right_row in zip(left, right)
    )


def _matrix_scale(matrix: Matrix, scalar: Fraction) -> Matrix:
    return tuple(tuple(value * scalar for value in row) for row in matrix)


def _matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    size = len(left)
    return tuple(
        tuple(
            sum((left[row][inner] * right[inner][column] for inner in range(size)), ZERO)
            for column in range(size)
        )
        for row in range(size)
    )


def _matrix_vector(matrix: Matrix, vector: Sequence[Fraction]) -> Tuple[Fraction, ...]:
    return tuple(
        sum((entry * value for entry, value in zip(row, vector)), ZERO)
        for row in matrix
    )


def _matrix_power(matrix: Matrix, power: int) -> Matrix:
    if type(power) is not int or power < 0 or power > 8:
        raise ValueError("matrix power outside frozen derivative bound")
    result = _matrix_identity(len(matrix))
    for _ in range(power):
        result = _matrix_multiply(result, matrix)
    return result


def _stationarity_invariants() -> None:
    if any(sum(row, ZERO) != ZERO for row in MODE_GENERATOR):
        raise CertificationError("mode generator has a nonzero exact row sum")
    for destination in range(len(MODE_NAMES)):
        flux = sum(
            (
                STATIONARY_MODE_PROBABILITIES[source]
                * MODE_GENERATOR[source][destination]
                for source in range(len(MODE_NAMES))
            ),
            ZERO,
        )
        if flux != ZERO:
            raise CertificationError("declared mode law is not exactly stationary")
    if sum(STATIONARY_MODE_PROBABILITIES, ZERO) != ONE:
        raise CertificationError("stationary mode law does not normalize")
    if TWO * OU_MEAN_REVERSION * OU_INVARIANT_VARIANCE != OU_DIFFUSION**2:
        raise CertificationError("OU invariant variance equation failed")
    for clutter, mark in zip(OBSERVATION_CLUTTER_WEIGHTS, OBSERVATION_MARK_WEIGHTS):
        if clutter <= ZERO or mark <= ZERO or clutter + mark != ONE:
            raise CertificationError("observation mixture is not positive and normalized")
    if KILLED_TYPE_GENERATOR != (
        (
            -(DEATH_RATES[0] + REPLACEMENT_RATES[0]),
            REPLACEMENT_RATES[0],
        ),
        (
            REPLACEMENT_RATES[1],
            -(DEATH_RATES[1] + REPLACEMENT_RATES[1]),
        ),
    ):
        raise CertificationError("killed type generator does not match mode edits")
    killed_times_terminal = _matrix_vector(
        KILLED_TYPE_GENERATOR, TERMINAL_MARK_COEFFICIENTS
    )
    if killed_times_terminal != (Fraction(-29, 80), Fraction(-1, 4)):
        raise CertificationError("K times terminal coefficient monotonicity anchor failed")


_stationarity_invariants()


def _absorbing_killed_generator() -> Matrix:
    return (
        (KILLED_TYPE_GENERATOR[0][0], KILLED_TYPE_GENERATOR[0][1], DEATH_RATES[0]),
        (KILLED_TYPE_GENERATOR[1][0], KILLED_TYPE_GENERATOR[1][1], DEATH_RATES[1]),
        (ZERO, ZERO, ZERO),
    )


ABSORBING_KILLED_GENERATOR = _absorbing_killed_generator()


def _uniformization_precompute(generator: Matrix) -> Tuple[Fraction, Tuple[Matrix, ...]]:
    size = len(generator)
    rate = max(-generator[index][index] for index in range(size))
    if rate <= ZERO:
        raise CertificationError("uniformization rate is not positive")
    embedded = _matrix_add(_matrix_identity(size), _matrix_scale(generator, ONE / rate))
    if any(value < ZERO for row in embedded for value in row):
        raise CertificationError("embedded chain has a negative exact entry")
    if any(sum(row, ZERO) != ONE for row in embedded):
        raise CertificationError("embedded chain is not exactly stochastic")
    powers = [_matrix_identity(size)]
    for _ in range(UNIFORMIZATION_TERMS):
        powers.append(_matrix_multiply(powers[-1], embedded))
    return rate, tuple(powers)


_KILLED_RATE, _KILLED_POWERS = _uniformization_precompute(
    ABSORBING_KILLED_GENERATOR
)
_KILLED_TERMINAL_VECTOR = TERMINAL_MARK_COEFFICIENTS + (ZERO,)
_KILLED_MARK_POWER_VALUES = tuple(
    _matrix_vector(power, _KILLED_TERMINAL_VECTOR)
    for power in _KILLED_POWERS
)


def _mark_coefficients(
    time: Fraction,
    cache: Optional[Dict[Fraction, Tuple[Interval, Interval]]] = None,
) -> Tuple[Interval, Interval]:
    if type(time) is not Fraction or time < ZERO or time > HORIZON:
        raise TypeError("time must be an exact Fraction in [0,T]")
    if cache is not None:
        cached = cache.get(time)
        if cached is not None:
            return cached
    duration = HORIZON - time
    poisson_mean = _KILLED_RATE * duration
    exp_negative = exp_bounds(-poisson_mean)
    weight = ONE
    scalar_sum = ONE
    weighted = [
        _KILLED_MARK_POWER_VALUES[0][row] for row in range(2)
    ]
    for index in range(1, UNIFORMIZATION_TERMS + 1):
        weight *= poisson_mean / index
        scalar_sum += weight
        for row in range(2):
            weighted[row] += weight * _KILLED_MARK_POWER_VALUES[index][row]
    tail_upper = ONE - exp_negative[0] * scalar_sum
    if tail_upper < ZERO:
        raise CertificationError("uniformization mark tail upper bound is negative")
    result = []
    for row in range(2):
        total = _outward_decimal_interval(_interval(
            exp_negative[0] * weighted[row],
            exp_negative[1] * weighted[row] + tail_upper,
        ), 60)
        if total[0] < ZERO or total[1] > ONE:
            raise CertificationError("mark coefficient escaped [0,1]")
        result.append(total)
    answer = (result[0], result[1])
    if cache is not None:
        cache[time] = answer
    return answer


def _rho_squared(time: Fraction) -> Interval:
    return exp_bounds(-(HORIZON - time))


def _conditional_mark_variance(time: Fraction) -> Interval:
    return _isub(_iexact(ONE), _iscale(_rho_squared(time), HALF))


def _psi(time: Fraction, coordinate: Fraction) -> Interval:
    rho_squared = _rho_squared(time)
    denominator = _isub(_iexact(TWO), rho_squared)
    prefactor = _isqrt(_idiv(_iexact(TWO), denominator))
    exponent = _ineg(
        _idiv(
            _iscale(rho_squared, coordinate * coordinate),
            _iscale(denominator, TWO),
        )
    )
    return _imul(prefactor, _iexp(exponent))


def _psi_spatial_derivative(time: Fraction, coordinate: Fraction) -> Interval:
    rho_squared = _rho_squared(time)
    denominator = _isub(_iexact(TWO), rho_squared)
    coefficient = _ineg(_idiv(_iscale(rho_squared, coordinate), denominator))
    return _imul(coefficient, _psi(time, coordinate))


def _information(
    mode: int,
    time: Fraction,
    coordinate: Fraction,
    mark_cache: Optional[Dict[Fraction, Tuple[Interval, Interval]]] = None,
) -> Interval:
    if type(mode) is not int or mode not in (EMPTY, ALPHA, BETA):
        raise TypeError("mode index is invalid")
    if mode == EMPTY:
        return _iexact(ONE)
    coefficient = _mark_coefficients(time, mark_cache)[mode - 1]
    return _iadd(_isub(_iexact(ONE), coefficient), _imul(coefficient, _psi(time, coordinate)))


def _conditioned_drift(
    mode: int,
    time: Fraction,
    coordinate: Fraction,
    mark_cache: Optional[Dict[Fraction, Tuple[Interval, Interval]]] = None,
) -> Interval:
    if mode == EMPTY:
        raise CertificationError("empty mode has no continuous tangent coordinate")
    coefficient = _mark_coefficients(time, mark_cache)[mode - 1]
    numerator = _imul(coefficient, _psi_spatial_derivative(time, coordinate))
    gradient = _idiv(numerator, _information(mode, time, coordinate, mark_cache))
    base = -OU_MEAN_REVERSION * coordinate
    return _iadd(_iexact(base), _iscale(gradient, OU_DIFFUSION**2))


def _log_information(
    mode: int,
    time: Fraction,
    coordinate: Fraction,
    mark_cache: Optional[Dict[Fraction, Tuple[Interval, Interval]]] = None,
) -> Interval:
    return _ilog(_information(mode, time, coordinate, mark_cache))


def _equal_prior_classifier_probability(
    mode: int,
    time: Fraction,
    coordinate: Fraction,
    mark_cache: Optional[Dict[Fraction, Tuple[Interval, Interval]]] = None,
) -> Interval:
    # For this normalized fixture p_A=lambda and evidence is one, hence the
    # exact joint/product density ratio is h and the equal-prior posterior is
    # tau=h/(1+h).  EMPTY has h=1 and therefore tau=1/2 exactly.
    information = _information(mode, time, coordinate, mark_cache)
    return _idiv(information, _iadd(_iexact(ONE), information))


def _classifier_probability_with_constant_nuisance(
    mode: int,
    time: Fraction,
    coordinate: Fraction,
    mark_cache: Optional[Dict[Fraction, Tuple[Interval, Interval]]] = None,
) -> Interval:
    tilted = _imul(
        _information(mode, time, coordinate, mark_cache), exp_bounds(CLASSIFIER_NUISANCE)
    )
    return _idiv(tilted, _iadd(_iexact(ONE), tilted))


LEGAL_EDGES: Tuple[Tuple[str, int, int], ...] = (
    ("birth", EMPTY, ALPHA),
    ("birth", EMPTY, BETA),
    ("death", ALPHA, EMPTY),
    ("death", BETA, EMPTY),
    ("replacement", ALPHA, BETA),
    ("replacement", BETA, ALPHA),
)
BLOCKED_CAP_BIRTHS: Tuple[Tuple[int, int], ...] = (
    (ALPHA, ALPHA),
    (ALPHA, BETA),
    (BETA, ALPHA),
    (BETA, BETA),
)

# Cap-two structural subfixture.  It is in the same F009 suite but is not used
# as a substitute for the cap-one path calculation.  The factorial reference
# activities are beta/delta.  The replacement pair below is chosen reversible
# with those activities, so the multiplicity/RN identity can be checked
# exactly at a repeated-alpha configuration.
CAP2_ALPHA_ACTIVITY = BIRTH_RATES[0] / DEATH_RATES[0]  # 5/4
CAP2_BETA_ACTIVITY = BIRTH_RATES[1] / DEATH_RATES[1]  # 5/9
CAP2_ALPHA_TO_BETA_REPLACEMENT = Fraction(1, 4)
CAP2_BETA_TO_ALPHA_REPLACEMENT = Fraction(9, 16)
CAP2_ATOMIC_REPEAT_MARK = Fraction(1)
CAP2_ASSOCIATION_MARKS = (Fraction(-1), Fraction(1))
CAP2_OBSERVATIONS = (Fraction(-1), Fraction(1))
CAP2_STRUCTURAL_CASE_ROSTER: Tuple[Tuple[str, str], ...] = (
    ("ATOMIC", "ATOMIC_REPEAT_ALPHA_DEATH_BIRTH_FACTORIAL_IDENTITY"),
    ("ATOMIC", "ATOMIC_REPEAT_ALPHA_TO_ALPHA_BETA_REPLACEMENT_MULTIPLICITY_IDENTITY"),
    ("CONTINUOUS_RN", "CONTINUOUS_GAUSSIAN_REPLACEMENT_ROUTE_SOURCE_X_MINUS_1"),
    ("CONTINUOUS_RN", "CONTINUOUS_GAUSSIAN_REPLACEMENT_ROUTE_SOURCE_X_PLUS_1"),
    ("CONTINUOUS_RN", "CONTINUOUS_GAUSSIAN_NONUNIT_DESTINATION_FIBER_RN_AT_ABS_Y_2"),
    ("ASSOCIATION", "ASSOCIATION_IDENTITY_BIJECTION"),
    ("ASSOCIATION", "ASSOCIATION_SWAP_BIJECTION"),
    ("CAP_BOUNDARY", "CAP2_BLOCKED_ALPHA_BIRTH_FAMILY"),
    ("CAP_BOUNDARY", "CAP2_BLOCKED_BETA_BIRTH_FAMILY"),
    ("CAP_BOUNDARY", "CAP2_SIGNED_AGGREGATE_HARMONIC_DEFECT"),
    ("CLASSIFIER_NUISANCE", "CLASSIFIER_NUISANCE_CONSTANCY_QUOTIENT_AND_CALIBRATION_SEPARATION"),
    ("OPTIONAL_POTENTIAL_GAUGE", "OPTIONAL_TERMINAL_MATCHED_POTENTIAL_GAUGE_INVARIANCE"),
)


def _cap2_structural_invariants() -> Dict[str, Fraction]:
    factorial_two = Fraction(math.factorial(2))
    # Ordered-chart masses for the atomic repeated-mark stratum, omitting the
    # common cap normalizer.  Relative to the canonical symmetrized
    # configuration base itself, dPi/dLambda has no explicit factorial.
    alpha_alpha_reference = CAP2_ALPHA_ACTIVITY**2 / factorial_two
    alpha_beta_reference = CAP2_ALPHA_ACTIVITY * CAP2_BETA_ACTIVITY
    death_flux_from_two_alpha = (
        alpha_alpha_reference * factorial_two * DEATH_RATES[0]
    )
    reverse_birth_flux_into_two_alpha = (
        CAP2_ALPHA_ACTIVITY
        * BIRTH_RATES[0]
    )
    if death_flux_from_two_alpha != reverse_birth_flux_into_two_alpha:
        raise CertificationError("cap2 factorial death/birth RN identity failed")
    forward_replacement_flux = (
        alpha_alpha_reference
        * factorial_two
        * CAP2_ALPHA_TO_BETA_REPLACEMENT
    )
    reverse_replacement_flux = (
        alpha_beta_reference
        * CAP2_BETA_TO_ALPHA_REPLACEMENT
    )
    if forward_replacement_flux != reverse_replacement_flux:
        raise CertificationError("cap2 replacement multiplicity/RN identity failed")
    if BIRTH_RATES[0] <= ZERO:
        raise CertificationError("cap2 pre-cap proposal birth flux is not positive")
    if BIRTH_RATES[1] <= ZERO:
        raise CertificationError("cap2 beta pre-cap proposal birth flux is not positive")
    return {
        "factorial_two": factorial_two,
        "alpha_alpha_reference": alpha_alpha_reference,
        "alpha_beta_reference": alpha_beta_reference,
        "death_birth_flux": death_flux_from_two_alpha,
        "replacement_flux": forward_replacement_flux,
        "pre_cap_alpha_birth_flux": BIRTH_RATES[0],
        "pre_cap_beta_birth_flux": BIRTH_RATES[1],
        "pre_cap_total_birth_flux": sum(BIRTH_RATES, ZERO),
        "legal_cap2_outward_birth_flux": ZERO,
    }


CAP2_STRUCTURAL_INVARIANTS: Mapping[str, Fraction] = MappingProxyType(
    _cap2_structural_invariants()
)


def _cap2_association_table() -> Dict[str, Any]:
    # With unit observation variance, x=(-1,1), and y=(-1,1), removing the
    # common Gaussian normalizer leaves identity weight 1 and swap weight
    # exp(-4): the swapped squared displacements are 2^2+2^2=8.
    identity = _iexact(ONE)
    swap = exp_bounds(Fraction(-4))
    denominator = _iadd(identity, swap)
    identity_normalized = _idiv(identity, denominator)
    swap_normalized = _idiv(swap, denominator)
    normalized_sum = _iadd(identity_normalized, swap_normalized)
    if swap[0] <= ZERO or identity[0] <= swap[1]:
        raise CertificationError("cap2 association assignments are not positive and unequal")
    if not (normalized_sum[0] <= ONE <= normalized_sum[1]):
        raise CertificationError("cap2 normalized association weights miss one")
    return {
        "source_configuration": {
            "types": ["ALPHA", "ALPHA"],
            "marks": [_fraction_text(value) for value in CAP2_ASSOCIATION_MARKS],
            "marks_are_distinct": True,
            "configuration_base": "LAMBDA_2=(1/2!)*PUSHFORWARD(NU_TENSOR_NU)",
            "dPi_dLambda_has_explicit_factorial": False,
            "used_as_repeated_atom_orbit_multiplicity_evidence": False,
        },
        "unordered_observation_marks": [
            _fraction_text(value) for value in CAP2_OBSERVATIONS
        ],
        "association_bijections": [
            {
                "name": "IDENTITY",
                "mapping": [[0, 0], [1, 1]],
                "common_factor_removed_weight": _interval_record(identity),
                "normalized_weight": _interval_record(identity_normalized),
            },
            {
                "name": "SWAP",
                "mapping": [[0, 1], [1, 0]],
                "common_factor_removed_weight": _interval_record(swap),
                "normalized_weight": _interval_record(swap_normalized),
            },
        ],
        "exact_bijection_count": 2,
        "both_weights_strictly_positive": True,
        "weights_proved_unequal": True,
        "normalized_weight_sum": _interval_record(normalized_sum),
        "normalized_weight_sum_exact_by_common_denominator_algebra": True,
        "unordered_configuration_measure_convention": "(1/2!)*DY1*DY2",
        "permanent_integrates_to_one_under_configuration_measure": True,
        "factorial_cancellation": "(1/2!)*SUM_OVER_2_BIJECTIONS",
    }


def _cap2_nonunit_mark_fiber_rn_table() -> Dict[str, Any]:
    """Certify a direction-sensitive, nonunit mark-fiber RN/Jacobian case.

    The structural replacement sends x to y=2x.  The source mark reference is
    N(0,1) on dx and the destination dominating mark reference is independently
    named N(0,1) on dy.  Relative to the destination reference, the pushforward
    density is (1/2) exp(3 y^2/8).  The factor at y=2 is deliberately nonunit;
    its reciprocal is the source/destination inversion hostile.
    """

    destination_y = Fraction(2)
    forward = _imul(_iexact(HALF), exp_bounds(Fraction(3, 2)))
    inverted = _imul(_iexact(TWO), exp_bounds(Fraction(-3, 2)))
    product = _imul(forward, inverted)
    activity_rate_coefficient = (
        CAP2_ALPHA_ACTIVITY / CAP2_BETA_ACTIVITY
        * CAP2_ALPHA_TO_BETA_REPLACEMENT
    )
    if activity_rate_coefficient != CAP2_BETA_TO_ALPHA_REPLACEMENT:
        raise CertificationError("cap2 continuous reverse coefficient changed")
    reverse_rate = _iscale(forward, activity_rate_coefficient)
    forward_flux = _iscale(
        forward,
        CAP2_ALPHA_ACTIVITY**2 * CAP2_ALPHA_TO_BETA_REPLACEMENT,
    )
    reverse_flux = _iscale(
        reverse_rate, CAP2_ALPHA_ACTIVITY * CAP2_BETA_ACTIVITY
    )
    if forward_flux != reverse_flux:
        raise CertificationError("nonunit per-destination replacement flux identity failed")
    if forward[0] <= ONE or inverted[1] >= ONE:
        raise CertificationError("nonunit mark-fiber RN direction is not separated")
    if not (product[0] <= ONE <= product[1]):
        raise CertificationError("forward/inverse mark-fiber RN identity misses one")
    return {
        "case_id": "CAP2_CONTINUOUS_GAUSSIAN_ROUTE_SUM_NONUNIT_MARK_FIBER_RN_V1",
        "legal_edge_family": "replacement",
        "source_type": "ALPHA",
        "destination_type": "BETA",
        "source_mark_dominating_measure": "MU_ALPHA=NORMAL_MEAN_0_VARIANCE_1_ON_DX",
        "destination_mark_dominating_measure": "MU_BETA=NORMAL_MEAN_0_VARIANCE_1_ON_DY",
        "subcase_local_configuration_measure": "LAMBDA_LE_2^GAUSSIAN_BUILT_ONLY_FROM_MU_ALPHA_AND_MU_BETA",
        "deterministic_mark_map": "Y=2*X",
        "reverse_deterministic_mark_map": "X=Y/2",
        "reverse_kernel": "DIRAC_AT_Y_OVER_2_RETURNS_SELECTED_BETA_MARK_TO_EXACT_ALPHA_SOURCE_MARK",
        "source_configuration_chart": "UNORDERED_AA_WITH_DISTINCT_CONTINUOUS_MARKS_UNDER_LAMBDA_2=(1/2!)*PUSHFORWARD(MU_ALPHA_TENSOR_MU_ALPHA)",
        "source_diagonal_is_null_and_not_USED_AS_ATOMIC_MULTIPLICITY_EVIDENCE": True,
        "forward_rate_per_selected_alpha_occurrence": "1/4",
        "two_distinct_source_occurrence_routes_reach_disjoint_AB_destinations": True,
        "absolute_jacobian_dx_over_dy": "1/2",
        "pushforward_rn_wrt_destination_measure": "(1/2)*EXP(3*Y^2/8)",
        "change_of_variables_identity": "INTEGRAL_F(2X)_MU_ALPHA(DX)=INTEGRAL_F(Y)*RN_DEST(Y)_MU_BETA(DY)",
        "frozen_route_rows": [
            {"selected_source_x": "-1/1", "remaining_alpha_x": "1/1", "destination_beta_y": "-2/1", "reverse_selected_beta_y": "-2/1", "reverse_returned_alpha_x": "-1/1", "per_destination_forward_flux_density": _interval_record(forward_flux), "per_destination_reverse_flux_density": _interval_record(reverse_flux)},
            {"selected_source_x": "1/1", "remaining_alpha_x": "-1/1", "destination_beta_y": "2/1", "reverse_selected_beta_y": "2/1", "reverse_returned_alpha_x": "1/1", "per_destination_forward_flux_density": _interval_record(forward_flux), "per_destination_reverse_flux_density": _interval_record(reverse_flux)},
        ],
        "rn_evaluation_absolute_destination_y": _fraction_text(destination_y),
        "forward_destination_fiber_rn": _interval_record(forward),
        "reverse_beta_to_alpha_rate_formula": "K_BA(Y)=(ZETA_ALPHA/ZETA_BETA)*(1/4)*RN_DEST(Y)=(9/16)*RN_DEST(Y)",
        "reverse_beta_to_alpha_rate_at_y_2": _interval_record(reverse_rate),
        "union_of_two_disjoint_destination_routes_measure_identity": "LAMBDA_2_EXTERIOR_1/2!*SUM_OVER_TWO_ORDERED_SOURCE_ROUTES_GIVES_ONE_COPY_OF_ZETA_ALPHA^2*(1/4)*MU_ALPHA(DX_REMAIN)*T_PUSHFORWARD(DY),EQUALS_ZETA_ALPHA*ZETA_BETA*K_BA(Y)*MU_ALPHA(DX_REMAIN)*MU_BETA(DY)",
        "per_destination_forward_flux_density_at_abs_y_2": _interval_record(forward_flux),
        "per_destination_unique_beta_reverse_flux_density_at_abs_y_2": _interval_record(reverse_flux),
        "each_per_destination_flux_interval_exactly_equal": True,
        "scalar_is_not_a_numerically_doubled_route_sum": True,
        "wrong_inverted_source_destination_factor": _interval_record(inverted),
        "forward_strictly_greater_than_one": True,
        "inverted_strictly_less_than_one": True,
        "symbolic_reciprocal_product_exactly_one": True,
        "interval_product_contains_one": _interval_record(product),
        "stationary_mode_mass_ratio_used_as_mark_fiber_rn": False,
        "primary_cap1_retained_mark_kernel_modified": False,
        "omitting_one_source_route_permitted": False,
        "dropping_jacobian_permitted": False,
        "using_constant_reverse_rate_9_over_16_permitted": False,
        "using_noninverse_reverse_mark_kernel_permitted": False,
    }


def _cap2_structural_fixture_record() -> Dict[str, Any]:
    invariants = CAP2_STRUCTURAL_INVARIANTS
    guide_ratios = (TWO, TWO)
    capped_minus_auxiliary_terms = tuple(
        -rate * (ratio - ONE)
        for rate, ratio in zip(BIRTH_RATES, guide_ratios)
    )
    auxiliary_q3_h = -sum(capped_minus_auxiliary_terms, ZERO)
    source_time_derivative = -auxiliary_q3_h
    if capped_minus_auxiliary_terms != (Fraction(-1, 2), Fraction(-1, 3)):
        raise CertificationError("cap2 family harmonic terms changed")
    if auxiliary_q3_h != Fraction(5, 6) or source_time_derivative != Fraction(-5, 6):
        raise CertificationError("cap2 aggregate harmonic identity changed")
    alpha_hypothetical_bregman = _iscale(
        _isub(_iexact(ONE), _ilog(_iexact(TWO))), BIRTH_RATES[0]
    )
    beta_ratio = TWO
    beta_hypothetical_bregman = _iscale(
        _isub(_iexact(beta_ratio - ONE), _ilog(_iexact(beta_ratio))),
        BIRTH_RATES[1],
    )
    total_hypothetical_bregman = _iadd(
        alpha_hypothetical_bregman, beta_hypothetical_bregman
    )
    if alpha_hypothetical_bregman[0] <= ZERO or beta_hypothetical_bregman[0] <= ZERO:
        raise CertificationError("cap2 hypothetical blocked-edge Bregman is not positive")
    return {
        "fixture_id": "CAP2_THREE_SUBCASE_MULTIPLICITY_RN_ASSOCIATION_AND_CAP_STRUCTURAL_WITNESS_V1",
        "cap": 2,
        "configuration_space": "GAMMA_LE_2_UNLABELED_TYPED_OCCURRENCE_CONFIGURATIONS",
        "shared_template_only": "PRODUCT_POISSON_ACTIVITIES_AND_EDIT_RATE_IDENTITIES_CONDITIONED_ON_TOTAL_COUNT_LE_2",
        "subcase_local_reference_laws_required": True,
        "one_joint_mark_measure_or_cross_subcase_balance_chain_claimed": False,
        "configuration_dominating_measure_template": "LAMBDA_LE_2^(SUBCASE)=SUM_N_0_TO_2_(1/N!)*PUSHFORWARD(NU_SUBCASE_TENSOR_N)",
        "reference_density_convention": "DPI_DLAMBDA=COMMON_CAP_NORMALIZER_TIMES_PRODUCT_ZETA_TYPE_TIMES_MARK_RN_WITH_NO_EXPLICIT_FACTORIAL",
        "common_cap_normalizer_cancels_from_displayed_flux_identities": True,
        "activities": {
            "alpha": _fraction_text(CAP2_ALPHA_ACTIVITY),
            "beta": _fraction_text(CAP2_BETA_ACTIVITY),
        },
        "subcase_A_atomic_repeated_orbit_multiplicity": {
            "case_id": "CAP2_ATOMIC_TRUE_M2_ORBIT_FACTORIAL_AND_AGGREGATE_ROUTES_V1",
            "mark_reference": "NU_ATOM=DIRAC_AT_1",
            "subcase_local_configuration_measure": "LAMBDA_LE_2^ATOM_BUILT_ONLY_FROM_DIRAC_AT_1",
            "configuration_name": "AA_ATOMIC_REPEAT",
            "configuration": "2*DELTA_(ALPHA,1)",
            "orbit_multiplicity": 2,
            "lambda_singleton_mass_factor_at_repeat": "1/2!",
            "dPi_dLambda_explicit_factorial": False,
            "Pi_singleton_mass_without_common_cap_normalizer": _fraction_text(
                invariants["alpha_alpha_reference"]
            ),
            "Pi_singleton_mass_formula": "ZETA_ALPHA^2/2!",
            "aggregate_death_source_multiplicity": 2,
            "two_indistinguishable_death_routes_same_unlabeled_destination": True,
            "death_birth_detailed_balance_identity": {
                "left_atomic_repeat_death_flux": _fraction_text(invariants["death_birth_flux"]),
                "right_atomic_singleton_birth_flux": _fraction_text(invariants["death_birth_flux"]),
                "formula": "(ZETA_ALPHA^2/2!)*(2*DELTA_ALPHA)=ZETA_ALPHA*BETA_ALPHA",
                "exact": True,
            },
            "atomic_replacement": {
                "alpha_to_beta_rate_per_occurrence": _fraction_text(
                    CAP2_ALPHA_TO_BETA_REPLACEMENT
                ),
                "beta_to_alpha_rate_per_beta_occurrence": _fraction_text(
                    CAP2_BETA_TO_ALPHA_REPLACEMENT
                ),
                "two_indistinguishable_forward_routes_same_unlabeled_AB_destination": True,
                "unique_beta_reverse_route": True,
                "retained_atomic_mark_rn_jacobian": "1/1",
                "forward_and_reverse_reference_flux": _fraction_text(
                    invariants["replacement_flux"]
                ),
                "formula": "(ZETA_ALPHA^2/2!)*(2*1/4)=ZETA_ALPHA*ZETA_BETA*(9/16)",
                "exact": True,
            },
            "continuous_gaussian_diagonal_used": False,
            "association_permanent_role": False,
        },
        "subcase_B_continuous_nonunit_rn_route_sum": _cap2_nonunit_mark_fiber_rn_table(),
        "subcase_C_distinct_mark_association_permanent": {
            "case_id": "CAP2_DISTINCT_MARK_TWO_BIJECTION_ASSOCIATION_PERMANENT_V1",
            "configuration": "DELTA_(ALPHA,-1)+DELTA_(ALPHA,1)",
            "subcase_local_configuration_measure": "LAMBDA_LE_2^GAUSSIAN_BUILT_ONLY_FROM_NORMAL_0_1_MARK_FIBERS",
            "marks_are_distinct": True,
            "emission_kernel": "NORMAL_MEAN_SOURCE_MARK_VARIANCE_1",
            "unordered_observation_measure": "(1/2!)*DY1*DY2",
            "marks": ["-1/1", "1/1"],
            "observations": ["-1/1", "1/1"],
            "relative_assignment_factors": ["1", "EXP(-4)"],
            "bijection_count": 2,
            "atomic_orbit_multiplicity_role": False,
            "nonunit_mark_fiber_rn_role": False,
        },
        "cap_boundary_attempted_birth": {
            "case_id": "CAP2_BOUNDARY_AUXILIARY_UNCAPPED_CAP3_ATTEMPTED_BIRTH_V1",
            "source_count": 2,
            "source_configuration": "DELTA_(ALPHA,-1)+DELTA_(ALPHA,1)",
            "local_time_cell": "T=1_TERMINAL_TIME_AUXILIARY_CAP3_HARMONIC_CELL",
            "auxiliary_cap3_generator": "FROM_SOURCE_ONLY_BIRTH_ALPHA_AT_RATE_1/2_AND_BIRTH_BETA_AT_RATE_1/3_TO_NAMED_COUNT3_DESTINATIONS",
            "guide_values": {"source": "1/1", "alpha_birth_destination": _fraction_text(guide_ratios[0]), "beta_birth_destination": _fraction_text(guide_ratios[1])},
            "source_time_derivative": _fraction_text(source_time_derivative),
            "auxiliary_Q3_h_at_source": _fraction_text(auxiliary_q3_h),
            "auxiliary_harmonic_identity": "D_T_H_PLUS_Q3_H=0",
            "generic_all_boundary_formula": "((D_T+L_CAP2)H_TILDE)/H_TILDE=-SUM_OVER_EVERY_BLOCKED_BIRTH_TYPE_BETA_D*(H_DEST_D/H_SOURCE-1)",
            "blocked_family_rows": [
                {
                    "attempted_destination_type": "ALPHA",
                    "attempted_destination_mark_measure": "NU_ALPHA=NORMAL_MEAN_0_VARIANCE_1_DZ",
                    "auxiliary_uncapped_or_cap3_attempted_birth_measure": "(1/2)*NU_ALPHA(DZ)",
                    "positive_omitted_proposal_mass": _fraction_text(invariants["pre_cap_alpha_birth_flux"]),
                    "attempted_guide_ratio": _fraction_text(guide_ratios[0]),
                    "capped_minus_auxiliary_harmonic_term": _fraction_text(capped_minus_auxiliary_terms[0]),
                    "hypothetical_blocked_edge_bregman_interval": _interval_record(alpha_hypothetical_bregman),
                },
                {
                    "attempted_destination_type": "BETA",
                    "attempted_destination_mark_measure": "NU_BETA=NORMAL_MEAN_0_VARIANCE_1_DZ",
                    "auxiliary_uncapped_or_cap3_attempted_birth_measure": "(1/3)*NU_BETA(DZ)",
                    "positive_omitted_proposal_mass": _fraction_text(invariants["pre_cap_beta_birth_flux"]),
                    "attempted_guide_ratio": _fraction_text(guide_ratios[1]),
                    "capped_minus_auxiliary_harmonic_term": _fraction_text(capped_minus_auxiliary_terms[1]),
                    "hypothetical_blocked_edge_bregman_interval": _interval_record(beta_hypothetical_bregman),
                },
            ],
            "positive_omitted_proposal_total_mass": _fraction_text(invariants["pre_cap_total_birth_flux"]),
            "legal_cap2_outward_birth_flux_by_type": {"ALPHA": "0/1", "BETA": "0/1"},
            "capped_minus_auxiliary_harmonic_defect": _fraction_text(source_time_derivative),
            "auxiliary_minus_capped_harmonic_defect": _fraction_text(auxiliary_q3_h),
            "harmonic_defect_sign_orientation_frozen": True,
            "all_harmonic_values_derived_from_birth_rates_and_guide_ratios": True,
            "hypothetical_blocked_edge_bregman_total_interval": _interval_record(total_hypothetical_bregman),
            "hypothetical_bregman_is_harmonic_defect": False,
            "hypothetical_bregman_is_legal_capped_path_term": False,
            "blocked_flux_is_path_kl_term": False,
            "ratio_at_blocked_edge_defined": False,
            "cap_defect_cancels_from_exact_vs_plugin_shared_guide_path_comparison": True,
            "cap_defect_may_be_owned_only_once_by_F007_selected_route": True,
            "deleting_or_swapping_either_blocked_family_permitted": False,
        },
        "three_subcases_are_disjoint_and_not_cross_substituted": True,
        "borrowing_flux_factorial_rn_or_association_facts_across_subcase_measures_permitted": False,
        "path_role": "STRUCTURAL_WITNESS_NOT_CAP1_PATH_COMPONENT_SUBSTITUTE",
    }


def _edge_log_ratio(
    family: str,
    source: int,
    destination: int,
    time: Fraction,
    coordinate: Fraction,
    mark_cache: Optional[Dict[Fraction, Tuple[Interval, Interval]]] = None,
) -> Interval:
    if (family, source, destination) not in LEGAL_EDGES:
        raise CertificationError("ratio requested for structural-zero or unknown edge")
    return _isub(
        _log_information(destination, time, coordinate, mark_cache),
        _log_information(source, time, coordinate, mark_cache),
    )


def _jet_constant(value: Interval, order: int = 4) -> Jet:
    return (value,) + tuple(_iexact(ZERO) for _ in range(order))


def _jet_add(left: Jet, right: Jet) -> Jet:
    return tuple(_iadd(a, b) for a, b in zip(left, right))


def _jet_neg(value: Jet) -> Jet:
    return tuple(_ineg(item) for item in value)


def _jet_sub(left: Jet, right: Jet) -> Jet:
    return _jet_add(left, _jet_neg(right))


def _jet_scale(value: Jet, scalar: Fraction) -> Jet:
    return tuple(_iscale(item, scalar) for item in value)


def _jet_multiply(left: Jet, right: Jet) -> Jet:
    order = min(len(left), len(right)) - 1
    return tuple(
        sum_interval(
            _imul(left[index], right[degree - index])
            for index in range(degree + 1)
        )
        for degree in range(order + 1)
    )


def _jet_exp(value: Jet) -> Jet:
    order = len(value) - 1
    result: List[Interval] = [_iexp(value[0])]
    for degree in range(1, order + 1):
        total = _iexact(ZERO)
        for index in range(1, degree + 1):
            total = _iadd(
                total,
                _iscale(_imul(value[index], result[degree - index]), Fraction(index)),
            )
        result.append(_iscale(total, Fraction(1, degree)))
    return tuple(result)


def sum_interval(values: Iterable[Interval]) -> Interval:
    total = _iexact(ZERO)
    for value in values:
        total = _iadd(total, value)
    return total


def _global_time_jet() -> Jet:
    return (
        _interval(ZERO, ONE),
        _iexact(ONE),
        _iexact(ZERO),
        _iexact(ZERO),
        _iexact(ZERO),
    )


def _global_mark_coefficient_jet(type_index: int) -> Jet:
    if type_index not in (0, 1):
        raise ValueError("type index invalid")
    values: List[Interval] = [_interval(ZERO, TERMINAL_MARK_COEFFICIENTS[type_index])]
    negative_k = tuple(tuple(-value for value in row) for row in KILLED_TYPE_GENERATOR)
    for order in range(1, 5):
        power = _matrix_power(negative_k, order)
        bound = ZERO
        for column in range(2):
            bound += abs(power[type_index][column]) * TERMINAL_MARK_COEFFICIENTS[column]
        values.append(_interval(-bound / math.factorial(order), bound / math.factorial(order)))
    return tuple(values)


def _global_integrand_jet(family: str, source: int, destination: int) -> Jet:
    t = _global_time_jet()
    u = _jet_sub(_jet_constant(_iexact(ONE)), t)
    slope_u = _jet_scale(u, RESIDUAL_MARK_SLOPE)
    slope_square = _jet_multiply(slope_u, slope_u)
    if family == "replacement":
        delta = RESIDUAL_MODE_CONSTANTS[destination] - RESIDUAL_MODE_CONSTANTS[source]
        argument = _jet_scale(u, delta)
        return _jet_sub(_jet_sub(_jet_exp(argument), _jet_constant(_iexact(ONE))), argument)
    if family == "death":
        constant = RESIDUAL_MODE_CONSTANTS[source]
        exponent = _jet_add(_jet_scale(u, -constant), _jet_scale(slope_square, HALF))
        return _jet_add(
            _jet_sub(_jet_exp(exponent), _jet_constant(_iexact(ONE))),
            _jet_scale(u, constant),
        )
    if family == "birth":
        type_index = destination - 1
        coefficient = _global_mark_coefficient_jet(type_index)
        one_minus_coefficient = _jet_sub(_jet_constant(_iexact(ONE)), coefficient)
        rho_squared = _jet_exp(_jet_sub(t, _jet_constant(_iexact(ONE))))
        conditional_variance = _jet_sub(
            _jet_constant(_iexact(ONE)), _jet_scale(rho_squared, HALF)
        )
        ordinary_mgf = _jet_exp(_jet_scale(slope_square, HALF))
        observed_mgf = _jet_exp(
            _jet_scale(_jet_multiply(slope_square, conditional_variance), HALF)
        )
        mixed_mgf = _jet_add(
            _jet_multiply(one_minus_coefficient, ordinary_mgf),
            _jet_multiply(coefficient, observed_mgf),
        )
        constant = RESIDUAL_MODE_CONSTANTS[destination]
        exponential = _jet_multiply(_jet_exp(_jet_scale(u, constant)), mixed_mgf)
        return _jet_sub(
            _jet_sub(exponential, _jet_constant(_iexact(ONE))),
            _jet_scale(u, constant),
        )
    raise CertificationError("unknown path family")


def _integrand_value(
    family: str,
    source: int,
    destination: int,
    time: Fraction,
    mark_cache: Optional[Dict[Fraction, Tuple[Interval, Interval]]] = None,
) -> Interval:
    u = ONE - time
    if family == "replacement":
        delta = RESIDUAL_MODE_CONSTANTS[destination] - RESIDUAL_MODE_CONSTANTS[source]
        argument = u * delta
        return _isub(_isub(exp_bounds(argument), _iexact(ONE)), _iexact(argument))
    if family == "death":
        constant = RESIDUAL_MODE_CONSTANTS[source]
        exponent = -u * constant + HALF * (u * RESIDUAL_MARK_SLOPE) ** 2
        return _iadd(
            _isub(exp_bounds(exponent), _iexact(ONE)),
            _iexact(u * constant),
        )
    if family == "birth":
        coefficient = _mark_coefficients(time, mark_cache)[destination - 1]
        slope_square = (u * RESIDUAL_MARK_SLOPE) ** 2
        ordinary_mgf = exp_bounds(HALF * slope_square)
        observed_mgf = _iexp(
            _iscale(_conditional_mark_variance(time), HALF * slope_square)
        )
        mixed_mgf = _iadd(
            _imul(_isub(_iexact(ONE), coefficient), ordinary_mgf),
            _imul(coefficient, observed_mgf),
        )
        constant = RESIDUAL_MODE_CONSTANTS[destination]
        return _isub(
            _isub(_imul(exp_bounds(u * constant), mixed_mgf), _iexact(ONE)),
            _iexact(u * constant),
        )
    raise CertificationError("unknown path family")


def _simpson_integral(
    family: str,
    source: int,
    destination: int,
    mark_cache: Optional[Dict[Fraction, Tuple[Interval, Interval]]] = None,
) -> Tuple[Interval, Dict[str, Any]]:
    subdivisions = SIMPSON_SUBINTERVALS
    step = HORIZON / subdivisions
    weighted = _iexact(ZERO)
    for index in range(subdivisions + 1):
        coefficient = 1 if index in (0, subdivisions) else (4 if index % 2 else 2)
        weighted = _iadd(
            weighted,
            _iscale(
                _outward_decimal_interval(
                    _integrand_value(family, source, destination, step * index, mark_cache),
                    60,
                ),
                Fraction(coefficient),
            ),
        )
    approximation = _outward_decimal_interval(_iscale(weighted, step / 3), 60)
    jet = _global_integrand_jet(family, source, destination)
    approximation_record = _interval_record(approximation)
    serialized_approximation = _interval_from_record(approximation_record)
    jet_four_record = _interval_record(jet[4])
    serialized_jet_four = _interval_from_record(jet_four_record)
    fourth_derivative_bound = (
        Fraction(math.factorial(4)) * _imaxabs(serialized_jet_four)
    )
    remainder = HORIZON * step**4 * fourth_derivative_bound / 180
    unclamped = _interval(
        serialized_approximation[0] - remainder,
        serialized_approximation[1] + remainder,
    )
    final = _interval(
        max(ZERO, serialized_approximation[0] - remainder),
        serialized_approximation[1] + remainder,
    )
    receipt = {
        "family": family.upper(),
        "source": MODE_NAMES[source],
        "destination": MODE_NAMES[destination],
        "subinterval_count": subdivisions,
        "step": _fraction_text(step),
        "simpson_approximation_enclosure": approximation_record,
        "fourth_taylor_coefficient_enclosure": jet_four_record,
        "fourth_taylor_coefficient_enclosure_role": "GLOBAL_DERIVATIVE_RANGE_NOT_ARITHMETIC_PRECISION_WIDTH",
        "fourth_derivative_bound_formula": "4!*MAX_ABS(FOURTH_TAYLOR_COEFFICIENT_ENCLOSURE)",
        "fourth_derivative_bound": _fraction_text(fourth_derivative_bound),
        "remainder_formula": "T*H^4*FOURTH_DERIVATIVE_BOUND/180",
        "remainder_upper": _fraction_text(remainder),
        "unclamped_final_enclosure": _exact_record_for_interval(unclamped),
        "final_nonnegative_enclosure": _exact_record_for_interval(final),
        "receipt_values_derived_topologically_from_serialized_parents": True,
        "lower_clamp_basis": "INTEGRAND_IS_PHI(DELTA_E)=EXP(DELTA_E)-1-DELTA_E_NONNEGATIVE_POINTWISE",
        "adaptive_quadrature_estimate_used": False,
    }
    return final, receipt


def _path_components(
    mark_cache: Optional[Dict[Fraction, Tuple[Interval, Interval]]] = None,
) -> Tuple[Dict[str, Interval], List[Dict[str, Any]]]:
    coefficients_zero = _mark_coefficients(ZERO, mark_cache)
    slope_squared = RESIDUAL_MARK_SLOPE**2
    conditional_variance_zero = _conditional_mark_variance(ZERO)
    candidate_normalizer = _iexact(STATIONARY_MODE_PROBABILITIES[EMPTY])
    target_expectation = ZERO
    for mode in (ALPHA, BETA):
        coefficient = coefficients_zero[mode - 1]
        mixed_mgf = _iadd(
            _imul(
                _isub(_iexact(ONE), coefficient),
                exp_bounds(HALF * slope_squared),
            ),
            _imul(
                coefficient,
                _iexp(_iscale(conditional_variance_zero, HALF * slope_squared)),
            ),
        )
        candidate_normalizer = _iadd(
            candidate_normalizer,
            _iscale(
                _imul(exp_bounds(RESIDUAL_MODE_CONSTANTS[mode]), mixed_mgf),
                STATIONARY_MODE_PROBABILITIES[mode],
            ),
        )
        target_expectation += (
            STATIONARY_MODE_PROBABILITIES[mode]
            * RESIDUAL_MODE_CONSTANTS[mode]
        )
    initializer = _isub(_ilog(candidate_normalizer), _iexact(target_expectation))
    continuous = _iexact(
        (
            STATIONARY_MODE_PROBABILITIES[ALPHA]
            + STATIONARY_MODE_PROBABILITIES[BETA]
        )
        * OU_DIFFUSION**2
        * slope_squared
        / 6
    )
    birth = _iexact(ZERO)
    route_receipts: List[Dict[str, Any]] = []
    for destination, rate in ((ALPHA, BIRTH_RATES[0]), (BETA, BIRTH_RATES[1])):
        route_interval, route_receipt = _simpson_integral(
            "birth", EMPTY, destination, mark_cache
        )
        occupation_rate_weight = STATIONARY_MODE_PROBABILITIES[EMPTY] * rate
        route_interval = _interval_from_record(route_receipt["final_nonnegative_enclosure"])
        weighted_contribution = _iscale(route_interval, occupation_rate_weight)
        route_receipt["target_occupation_rate_weight"] = _fraction_text(occupation_rate_weight)
        route_receipt["weighted_component_contribution"] = _exact_record_for_interval(weighted_contribution)
        route_receipts.append(route_receipt)
        birth = _iadd(
            birth,
            weighted_contribution,
        )
    death = _iexact(ZERO)
    for source, rate in ((ALPHA, DEATH_RATES[0]), (BETA, DEATH_RATES[1])):
        route_interval, route_receipt = _simpson_integral(
            "death", source, EMPTY, mark_cache
        )
        occupation_rate_weight = STATIONARY_MODE_PROBABILITIES[source] * rate
        route_interval = _interval_from_record(route_receipt["final_nonnegative_enclosure"])
        weighted_contribution = _iscale(route_interval, occupation_rate_weight)
        route_receipt["target_occupation_rate_weight"] = _fraction_text(occupation_rate_weight)
        route_receipt["weighted_component_contribution"] = _exact_record_for_interval(weighted_contribution)
        route_receipts.append(route_receipt)
        death = _iadd(
            death,
            weighted_contribution,
        )
    replacement = _iexact(ZERO)
    for source, destination, rate in (
        (ALPHA, BETA, REPLACEMENT_RATES[0]),
        (BETA, ALPHA, REPLACEMENT_RATES[1]),
    ):
        route_interval, route_receipt = _simpson_integral(
            "replacement", source, destination, mark_cache
        )
        occupation_rate_weight = STATIONARY_MODE_PROBABILITIES[source] * rate
        route_interval = _interval_from_record(route_receipt["final_nonnegative_enclosure"])
        weighted_contribution = _iscale(route_interval, occupation_rate_weight)
        route_receipt["target_occupation_rate_weight"] = _fraction_text(occupation_rate_weight)
        route_receipt["weighted_component_contribution"] = _exact_record_for_interval(weighted_contribution)
        route_receipts.append(route_receipt)
        replacement = _iadd(
            replacement,
            weighted_contribution,
        )
    dynamic = _iadd(_iadd(continuous, birth), _iadd(death, replacement))
    total = _iadd(initializer, dynamic)
    components = {
        "initializer": initializer,
        "continuous": continuous,
        "birth": birth,
        "death": death,
        "replacement": replacement,
        "dynamic": dynamic,
        "total": total,
    }
    required_names = ("initializer", "continuous", "birth", "death", "replacement")
    if any(components[name][0] < ZERO for name in required_names):
        raise CertificationError("path component nonnegativity enclosure failed")
    if dynamic != sum_interval(components[name] for name in required_names[1:]):
        raise CertificationError("dynamic path interval is not the exact four-component sum")
    if total != sum_interval(components[name] for name in required_names):
        raise CertificationError("total path interval is not the exact five-component sum")
    if len(route_receipts) != len(LEGAL_EDGES):
        raise CertificationError("quadrature route receipt roster changed")
    return components, route_receipts


def _interval_record(value: Interval) -> Dict[str, str]:
    value = _outward_decimal_interval(value)
    return {
        "lower": _fraction_text(value[0]),
        "upper": _fraction_text(value[1]),
        "width": _fraction_text(_iwidth(value)),
    }


def _interval_from_record(value: Mapping[str, Any]) -> Interval:
    if type(value) is not dict or set(value) != {"lower", "upper", "width"}:
        raise CertificationError("interval record has changed shape")
    result = _interval(
        _fraction_from_text(value["lower"]),
        _fraction_from_text(value["upper"]),
    )
    if _iwidth(result) != _fraction_from_text(value["width"]):
        raise CertificationError("interval record width is inconsistent")
    return result


def _exact_record_for_interval(value: Interval) -> Dict[str, str]:
    return {
        "lower": _fraction_text(value[0]),
        "upper": _fraction_text(value[1]),
        "width": _fraction_text(_iwidth(value)),
    }


def _sum_interval_records(values: Sequence[Mapping[str, Any]]) -> Dict[str, str]:
    return _exact_record_for_interval(
        sum_interval(_interval_from_record(value) for value in values)
    )


def _bounded_tree_check(value: Any) -> None:
    stack: List[Tuple[Any, int]] = [(value, 0)]
    seen = set()
    node_count = 0
    while stack:
        item, depth = stack.pop()
        node_count += 1
        if node_count > MAX_TREE_NODES or depth > MAX_TREE_DEPTH:
            raise CertificationError("record exceeds bounded tree limits")
        if item is None or type(item) is bool:
            continue
        if type(item) is int:
            if item.bit_length() > MAX_INTEGER_BITS:
                raise CertificationError("integer exceeds bit-length cap")
            continue
        if type(item) is str:
            if len(item) > MAX_TEXT_CHARS or not item.isascii():
                raise CertificationError("text is non-ASCII or too long")
            continue
        if type(item) not in (list, dict):
            raise CertificationError("record contains a forbidden runtime type")
        identity = id(item)
        if identity in seen:
            raise CertificationError("record contains a cycle or container alias")
        seen.add(identity)
        if len(item) > MAX_CONTAINER_ITEMS:
            raise CertificationError("container exceeds item cap")
        if type(item) is list:
            stack.extend((child, depth + 1) for child in reversed(item))
        else:
            if any(type(key) is not str for key in item):
                raise CertificationError("record keys must be exact strings")
            stack.extend((child, depth + 1) for child in reversed(list(item.values())))


def canonical_bytes(value: Any) -> bytes:
    _bounded_tree_check(value)
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    if len(raw) > MAX_SERIALIZED_BYTES:
        raise CertificationError("canonical record exceeds exact byte cap")
    return raw


def _simpson_grid_record() -> Dict[str, Any]:
    if SIMPSON_SUBINTERVALS <= 0 or SIMPSON_SUBINTERVALS % 2:
        raise CertificationError("Simpson grid requires a positive even subdivision count")
    nodes = []
    for index in range(SIMPSON_SUBINTERVALS + 1):
        weight = 1 if index in (0, SIMPSON_SUBINTERVALS) else (4 if index % 2 else 2)
        nodes.append(
            {
                "index": index,
                "time": _fraction_text(Fraction(index, SIMPSON_SUBINTERVALS)),
                "integer_weight": weight,
            }
        )
    node_bytes = canonical_bytes(nodes)
    return {
        "rule": "COMPOSITE_SIMPSON",
        "time_domain": ["0/1", "1/1"],
        "subinterval_count": SIMPSON_SUBINTERVALS,
        "node_count": SIMPSON_SUBINTERVALS + 1,
        "ordered_nodes": nodes,
        "ordered_nodes_sha256": hashlib.sha256(
            GRID_DOMAIN + b"simpson-nodes\0" + node_bytes
        ).hexdigest(),
        "scale": "(1/SUBINTERVAL_COUNT)/3",
        "fourth_derivative_certificate_domain": {
            "time": "CLOSED_INTERVAL_0_1",
            "modes_and_edges": "ALL_PRIMARY_CAP1_MODES_AND_ALL_SIX_LEGAL_EDGE_FAMILY_ROUTES",
            "mark": "FULL_REAL_LINE_INTEGRATED_BY_EXACT_GAUSSIAN_MOMENT_IDENTITIES_NOT_FINITE_MARK_GRID",
            "derivative_order": 4,
            "remainder_formula": "T*H^4*SUP_ABS_FOURTH_DERIVATIVE/180",
        },
    }


def _grid_record() -> Dict[str, Any]:
    drift_count = len(TIME_GRID) * 2 * len(MARK_GRID)
    per_family_ratio_count = len(TIME_GRID) * 2 * len(MARK_GRID)
    blocked_flux_count = len(TIME_GRID) * len(BLOCKED_CAP_BIRTHS) * len(MARK_GRID)
    calibration_count = len(TIME_GRID) * (1 + 2 * len(MARK_GRID))
    structural_ids = [case_id for _category, case_id in CAP2_STRUCTURAL_CASE_ROSTER]
    if len(structural_ids) != len(set(structural_ids)):
        raise CertificationError("structural case roster contains a duplicate")
    structural_counts = {
        category: sum(1 for item_category, _case_id in CAP2_STRUCTURAL_CASE_ROSTER if item_category == category)
        for category in sorted({category for category, _case_id in CAP2_STRUCTURAL_CASE_ROSTER})
    }
    structural_count = len(CAP2_STRUCTURAL_CASE_ROSTER)
    quadrature = _simpson_grid_record()
    return {
        "ordering": "TABLE_THEN_TIME_THEN_SOURCE_THEN_DESTINATION_THEN_MARK",
        "times": [_fraction_text(value) for value in TIME_GRID],
        "modes": list(MODE_NAMES),
        "mark_coordinates": [_fraction_text(value) for value in MARK_GRID],
        "coordinate_semantics": {
            "drift": "CURRENT_OCCUPIED_STATE_MARK_X",
            "calibration_occupied": "CURRENT_OCCUPIED_STATE_MARK_X",
            "calibration_empty": "NO_MARK_COORDINATE_ONE_CELL_PER_TIME",
            "birth_ratio": "NEWLY_DRAWN_DESTINATION_FIBER_MARK_Z_EMPTY_SOURCE_HAS_NO_MARK",
            "death_ratio": "REMOVED_SOURCE_OCCURRENCE_MARK_X_EMPTY_DESTINATION_HAS_NO_MARK",
            "retained_mark_replacement_ratio": "SAME_SELECTED_MARK_X_AT_SOURCE_AND_DESTINATION",
            "blocked_cap1_birth_flux": "GRID_COORDINATE_IS_EXISTING_CAP_SOURCE_MARK_X_ATTEMPTED_DESTINATION_MARK_Z_IS_INTEGRATED_OVER_NU_AND_NO_RATIO_EXISTS",
        },
        "legal_edges": [
            {"family": family, "source": MODE_NAMES[source], "destination": MODE_NAMES[destination]}
            for family, source, destination in LEGAL_EDGES
        ],
        "blocked_cap_births": [
            {"source": MODE_NAMES[source], "attempted_destination_type": MODE_NAMES[destination]}
            for source, destination in BLOCKED_CAP_BIRTHS
        ],
        "terminal_boundary_included": True,
        "cap_boundary_modes": ["ALPHA", "BETA"],
        "cap2_atomic_repeat_mark": _fraction_text(CAP2_ATOMIC_REPEAT_MARK),
        "cap2_distinct_association_marks": [_fraction_text(value) for value in CAP2_ASSOCIATION_MARKS],
        "cap2_fixed_observations": [_fraction_text(value) for value in CAP2_OBSERVATIONS],
        "path_quadrature_grid": quadrature,
        "table_counts": {
            "drift_time_occupied_mode_mark_product": drift_count,
            "birth_log_ratio_time_edge_mark_product": per_family_ratio_count,
            "death_log_ratio_time_edge_mark_product": per_family_ratio_count,
            "replacement_log_ratio_time_edge_mark_product": per_family_ratio_count,
            "blocked_birth_flux_time_route_mark_product": blocked_flux_count,
            "equal_prior_calibration_time_mode_mark_union": calibration_count,
            "cap2_atomic_factorial_multiplicity_cases": structural_counts["ATOMIC"],
            "cap2_continuous_rn_route_cases": structural_counts["CONTINUOUS_RN"],
            "cap2_association_bijection_cases": structural_counts["ASSOCIATION"],
            "cap2_cap_boundary_cases": structural_counts["CAP_BOUNDARY"],
            "classifier_nuisance_constancy_and_calibration_cases": structural_counts["CLASSIFIER_NUISANCE"],
            "optional_potential_gauge_invariance_cases": structural_counts["OPTIONAL_POTENTIAL_GAUGE"],
            "finite_table_cells": drift_count + 3 * per_family_ratio_count + blocked_flux_count + calibration_count,
            "structural_case_cells": structural_count,
            "path_quadrature_node_cells": quadrature["node_count"],
            "total_bound_union_cells": (
                drift_count + 3 * per_family_ratio_count + blocked_flux_count
                + calibration_count + structural_count + quadrature["node_count"]
            ),
        },
        "structural_zero_rule": "BLOCKED_CAP_BIRTH_HAS_ZERO_FLUX_AND_NO_LOG_RATIO",
        "structural_case_order": structural_ids,
        "structural_category_counts": structural_counts,
        "structural_count_derived_from_roster": True,
    }


def build_reference_tables() -> Dict[str, Any]:
    """Return the complete ordered finite grid and nonzero path witness."""

    # Authoritative caching is build-local.  No caller-writable module cache
    # can alter a fresh certificate or survive between validations.
    mark_cache: Dict[Fraction, Tuple[Interval, Interval]] = {}
    drift: List[Dict[str, Any]] = []
    ratios: Dict[str, List[Dict[str, Any]]] = {
        "birth": [],
        "death": [],
        "replacement": [],
    }
    blocked: List[Dict[str, Any]] = []
    calibration: List[Dict[str, Any]] = []
    for time_index, time in enumerate(TIME_GRID):
        empty_tau = _equal_prior_classifier_probability(EMPTY, time, ZERO, mark_cache)
        empty_shifted = _classifier_probability_with_constant_nuisance(EMPTY, time, ZERO, mark_cache)
        if empty_shifted[0] <= empty_tau[1]:
            raise CertificationError("positive classifier nuisance did not change empty calibration")
        calibration.append(
            {
                "time_index": time_index,
                "mode": "EMPTY",
                "mark_index": None,
                "coordinate_role": "NO_MARK_COORDINATE",
                "exact_nuisance": "0/1",
                "exact_equal_prior_probability": _interval_record(empty_tau),
                "positive_constant_nuisance_probability_witness": _interval_record(empty_shifted),
            }
        )
        for mode in (ALPHA, BETA):
            for mark_index, coordinate in enumerate(MARK_GRID):
                drift.append(
                    {
                        "time_index": time_index,
                        "mode": MODE_NAMES[mode],
                        "mark_index": mark_index,
                        "coordinate_role": "CURRENT_OCCUPIED_STATE_MARK_X",
                        "reference": _interval_record(_conditioned_drift(mode, time, coordinate, mark_cache)),
                    }
                )
                tau = _equal_prior_classifier_probability(mode, time, coordinate, mark_cache)
                shifted = _classifier_probability_with_constant_nuisance(
                    mode, time, coordinate, mark_cache
                )
                if shifted[0] <= tau[1]:
                    raise CertificationError("positive classifier nuisance did not change calibration")
                calibration.append(
                    {
                        "time_index": time_index,
                        "mode": MODE_NAMES[mode],
                        "mark_index": mark_index,
                        "coordinate_role": "CURRENT_OCCUPIED_STATE_MARK_X",
                        "exact_nuisance": "0/1",
                        "exact_equal_prior_probability": _interval_record(tau),
                        "positive_constant_nuisance_probability_witness": _interval_record(shifted),
                    }
                )
        for family, source, destination in LEGAL_EDGES:
            for mark_index, coordinate in enumerate(MARK_GRID):
                ratios[family].append(
                    {
                        "time_index": time_index,
                        "source": MODE_NAMES[source],
                        "destination": MODE_NAMES[destination],
                        "mark_index": mark_index,
                        "coordinate_role": {
                            "birth": "NEWLY_DRAWN_DESTINATION_FIBER_MARK_Z",
                            "death": "REMOVED_SOURCE_OCCURRENCE_MARK_X",
                            "replacement": "RETAINED_MARK_X_SHARED_BY_SOURCE_AND_DESTINATION",
                        }[family],
                        "reference": _interval_record(
                            _edge_log_ratio(family, source, destination, time, coordinate, mark_cache)
                        ),
                    }
                )
        for source, attempted_destination in BLOCKED_CAP_BIRTHS:
            for mark_index, _coordinate in enumerate(MARK_GRID):
                blocked.append(
                    {
                        "time_index": time_index,
                        "source": MODE_NAMES[source],
                        "attempted_destination_type": MODE_NAMES[attempted_destination],
                        "mark_index": mark_index,
                        "coordinate_role": "EXISTING_CAP_SOURCE_MARK_X",
                        "attempted_destination_mark_treatment": "INTEGRATED_OVER_NU_DESTINATION_FIBER",
                        "base_flux": "0/1",
                        "log_ratio": None,
                    }
                )
    endpoint = {
        "mode_probabilities": [
            _fraction_text(value) for value in STATIONARY_MODE_PROBABILITIES
        ],
        "empty_mark_law": "NOT_APPLICABLE",
        "alpha_mark_mixture": {
            "weights": ["1/4", "3/4"],
            "zero_mean_gaussian_variances": ["1/1", "1/2"],
        },
        "beta_mark_mixture": {
            "weights": ["1/2", "1/2"],
            "zero_mean_gaussian_variances": ["1/1", "1/2"],
        },
        "representation_identifies_full_joint_law": True,
    }
    initial_coefficients = _mark_coefficients(ZERO, mark_cache)
    initial_variance = _conditional_mark_variance(ZERO)
    initializer = {
        "normalizer": {"evidence": "1/1", "certified_exact": True},
        "mode_probabilities": [
            _fraction_text(value) for value in STATIONARY_MODE_PROBABILITIES
        ],
        "empty_mark_law": "NOT_APPLICABLE",
        "alpha_mark_mixture": {
            "mixture_component_count": 2,
            "weights": [
                _interval_record(_isub(_iexact(ONE), initial_coefficients[0])),
                _interval_record(initial_coefficients[0]),
            ],
            "zero_mean_gaussian_variances": [
                _interval_record(_iexact(ONE)),
                _interval_record(initial_variance),
            ],
            "weight_sum_exact_by_shared_coefficient_complement_algebra": "1/1",
            "weight_and_variance_rosters_have_equal_length": True,
        },
        "beta_mark_mixture": {
            "mixture_component_count": 2,
            "weights": [
                _interval_record(_isub(_iexact(ONE), initial_coefficients[1])),
                _interval_record(initial_coefficients[1]),
            ],
            "zero_mean_gaussian_variances": [
                _interval_record(_iexact(ONE)),
                _interval_record(initial_variance),
            ],
            "weight_sum_exact_by_shared_coefficient_complement_algebra": "1/1",
            "weight_and_variance_rosters_have_equal_length": True,
        },
        "representation_identifies_full_joint_law": True,
    }
    components, quadrature_route_certificates = _path_components(mark_cache)
    route_contributions_by_family: Dict[str, List[Mapping[str, Any]]] = {
        "BIRTH": [],
        "DEATH": [],
        "REPLACEMENT": [],
    }
    for receipt in quadrature_route_certificates:
        route_contributions_by_family[receipt["family"]].append(
            receipt["weighted_component_contribution"]
        )
    component_records = {
        "initializer": _interval_record(components["initializer"]),
        "continuous": _interval_record(components["continuous"]),
        "birth": _sum_interval_records(route_contributions_by_family["BIRTH"]),
        "death": _sum_interval_records(route_contributions_by_family["DEATH"]),
        "replacement": _sum_interval_records(route_contributions_by_family["REPLACEMENT"]),
    }
    component_records["dynamic"] = _sum_interval_records(
        [component_records[name] for name in ("continuous", "birth", "death", "replacement")]
    )
    component_records["total"] = _sum_interval_records(
        [component_records[name] for name in ("initializer", "continuous", "birth", "death", "replacement")]
    )
    for name in ("initializer", "continuous", "birth", "death", "replacement", "dynamic", "total"):
        serialized = _interval_from_record(component_records[name])
        if serialized[0] > components[name][0] or serialized[1] < components[name][1]:
            raise CertificationError(name + " serialized path enclosure misses internal interval")
    if any(
        _interval_from_record(component_records[name])[0] < ZERO
        for name in ("initializer", "continuous", "birth", "death", "replacement")
    ):
        raise CertificationError("serialized required path component has negative lower endpoint")
    cap2_association = _cap2_association_table()
    return {
        "grid": _grid_record(),
        "drift": drift,
        "log_doob_ratios": ratios,
        "blocked_cap_birth_flux": blocked,
        "equal_prior_classifier_calibration": {
            "orientation": "JOINT_CLASS_PROBABILITY_UNDER_EQUAL_PRIORS",
            "exact_ratio": "P_JOINT/P_PRODUCT=H",
            "exact_probability": "TAU=H/(1+H)",
            "empty_probability": "1/2",
            "exact_nuisance_for_calibration": "0/1",
            "candidate_metric": "MAX_ABS(SIGMOID(GAUGE_FIXED_CANDIDATE_LOGIT)-TAU)",
            "ordered_cells": calibration,
        },
        "initializer_full_law": initializer,
        "endpoint_full_law": endpoint,
        "cap2_structural_witness": {
            "parameters": _cap2_structural_fixture_record(),
            "association_table": cap2_association,
            "factorial_and_multiplicity_exact": True,
            "association_normalization_interval_certified": True,
            "cap_flux_exact": True,
            "nonunit_mark_fiber_rn_orientation_interval_certified": True,
        },
        "classifier_nuisance_constancy_and_invariance_witness": {
            "exact_calibration_nuisance": "0/1",
            "positive_structural_nuisance": _fraction_text(CLASSIFIER_NUISANCE),
            "logit_decomposition": "ELL=LOG_H+C(A,M,Z)",
            "nuisance_inputs": ["A", "M", "Z"],
            "forbidden_inputs": ["PROCESS_TIME_U", "PROCESS_STATE_Y"],
            "constant_in_every_frozen_time_mode_mark_cell": True,
            "never_folded_into_H_OR_HAT_H": True,
            "gauge_fixed_quotient_subtracts_common_nuisance": True,
            "spatial_gradients_and_legal_edge_log_differences_unchanged": True,
            "normalized_initializer_common_factor_cancels": True,
            "unquotiented_equal_prior_classifier_calibration_changes": True,
            "calibration_change_direction_for_positive_nuisance": "STRICTLY_INCREASES_EVERY_CELL",
        },
        "optional_potential_gauge_invariance_witness": {
            "gauge": "q(t)=(1-t)*(%s)" % _fraction_text(NUISANCE_GAUGE),
            "gauge_nonzero_before_terminal": True,
            "terminal_gauge_zero": True,
            "same_gauge_added_to_empty_alpha_and_beta": True,
            "spatial_gradient_change": "0/1",
            "every_legal_edge_increment_change": "0/1",
            "normalized_initializer_common_factor_cancels": True,
            "local_characteristics_unchanged": True,
            "K0_KC_K_BIRTH_K_DEATH_K_REPLACEMENT_AND_TOTAL_UNCHANGED": True,
            "classifier_observation_nuisance_claimed": False,
            "required_nuisance_identity_substitute": False,
        },
        "nonzero_residual_path_witness": {
            "orientation": ORIENTATION,
            "decision_candidate": False,
            "components": component_records,
            "ordered_six_route_quadrature_certificates": quadrature_route_certificates,
            "route_family_counts": {"BIRTH": 2, "DEATH": 2, "REPLACEMENT": 2},
            "family_components_exactly_recomposed_from_serialized_weighted_routes": True,
            "dynamic_exactly_equals_serialized_continuous_birth_death_replacement_interval_sum": True,
            "total_exactly_equals_serialized_five_component_interval_sum": True,
            "required_component_lower_endpoints_nonnegative": True,
            "nonnegativity_basis": "K0_IS_ORIENTED_INITIAL_LAW_KL_KC_IS_SQUARED_NORM_AND_EACH_LEGAL_JUMP_INTEGRAND_IS_Q_H_TIMES_PHI_WITH_PHI_NONNEGATIVE",
            "cap_defect_component_present": False,
            "simpson_subintervals": SIMPSON_SUBINTERVALS,
            "remainder": "T*h^4*SUP_ABS_FOURTH_DERIVATIVE/180",
        },
    }


def _max_reference_width(rows: Sequence[Mapping[str, Any]]) -> Fraction:
    return max(
        (_fraction_from_text(row["reference"]["width"]) for row in rows),
        default=ZERO,
    )


def _all_interval_widths(value: Any) -> List[Fraction]:
    widths: List[Fraction] = []
    stack = [value]
    while stack:
        item = stack.pop()
        if type(item) is dict:
            if set(item) == {"lower", "upper", "width"}:
                lower = _fraction_from_text(item["lower"])
                upper = _fraction_from_text(item["upper"])
                width = _fraction_from_text(item["width"])
                if upper - lower != width or width < ZERO:
                    raise CertificationError("serialized interval width is inconsistent")
                widths.append(width)
            else:
                stack.extend(item.values())
        elif type(item) is list:
            stack.extend(item)
    return widths


def _reference_summary(tables: Mapping[str, Any]) -> Dict[str, Any]:
    path = tables["nonzero_residual_path_witness"]["components"]
    path_width = max(
        _fraction_from_text(path[name]["width"])
        for name in (
            "initializer",
            "continuous",
            "birth",
            "death",
            "replacement",
            "dynamic",
            "total",
        )
    )
    association = tables["cap2_structural_witness"]["association_table"]
    association_width = max(_all_interval_widths(association), default=ZERO)
    calibration_width = max(
        _all_interval_widths(tables["equal_prior_classifier_calibration"]),
        default=ZERO,
    )
    rn_width = max(
        _all_interval_widths(
            tables["cap2_structural_witness"]["parameters"][
                "subcase_B_continuous_nonunit_rn_route_sum"
            ]
        ),
        default=ZERO,
    )
    cap_boundary_width = max(
        _all_interval_widths(
            tables["cap2_structural_witness"]["parameters"][
                "cap_boundary_attempted_birth"
            ]
        ),
        default=ZERO,
    )
    initializer_width = max(
        _all_interval_widths(tables["initializer_full_law"]), default=ZERO
    )
    endpoint_width = max(
        _all_interval_widths(tables["endpoint_full_law"]), default=ZERO
    )
    route_precision_widths = []
    for route in tables["nonzero_residual_path_witness"][
        "ordered_six_route_quadrature_certificates"
    ]:
        for key in (
            "simpson_approximation_enclosure",
            "unclamped_final_enclosure",
            "final_nonnegative_enclosure",
            "weighted_component_contribution",
        ):
            route_precision_widths.append(
                _fraction_from_text(route[key]["width"])
            )
    route_precision_width = max(route_precision_widths, default=ZERO)
    maxima = {
        "F011_CALIBRATION_REFERENCE": calibration_width,
        "F011_ASSOCIATION_REFERENCE": association_width,
        "F011_NONUNIT_RN_REFERENCE": rn_width,
        "F011_CAP_BOUNDARY_BREGMAN_REFERENCE": cap_boundary_width,
        "F012_DRIFT_REFERENCE": _max_reference_width(tables["drift"]),
        "F013_BIRTH_RATIO_REFERENCE": _max_reference_width(tables["log_doob_ratios"]["birth"]),
        "F014_DEATH_RATIO_REFERENCE": _max_reference_width(tables["log_doob_ratios"]["death"]),
        "F015_REPLACEMENT_RATIO_REFERENCE": _max_reference_width(tables["log_doob_ratios"]["replacement"]),
        "F016_INITIALIZER_REFERENCE": initializer_width,
        "F017_ENDPOINT_REFERENCE": endpoint_width,
        "F018_PATH_COMPONENT_REFERENCE": path_width,
        "F018_QUADRATURE_ROUTE_REFERENCE": route_precision_width,
    }
    if set(maxima) != set(REFERENCE_WIDTH_BUDGETS):
        raise CertificationError("reference precision surface roster changed")
    precision_checks = []
    for key in sorted(REFERENCE_WIDTH_BUDGETS):
        maximum = maxima[key]
        budget = REFERENCE_WIDTH_BUDGETS[key]
        if maximum > budget:
            raise CertificationError(key + " reference width exceeds frozen budget")
        precision_checks.append(
            {
                "surface": key,
                "maximum_width": _fraction_text(maximum),
                "budget": _fraction_text(budget),
                "pass": True,
            }
        )
    return {
        "drift_cell_count": len(tables["drift"]),
        "birth_log_ratio_cell_count": len(tables["log_doob_ratios"]["birth"]),
        "death_log_ratio_cell_count": len(tables["log_doob_ratios"]["death"]),
        "replacement_log_ratio_cell_count": len(tables["log_doob_ratios"]["replacement"]),
        "blocked_cap_birth_flux_cell_count": len(tables["blocked_cap_birth_flux"]),
        "equal_prior_calibration_cell_count": len(
            tables["equal_prior_classifier_calibration"]["ordered_cells"]
        ),
        "maximum_drift_reference_width": _fraction_text(
            _max_reference_width(tables["drift"])
        ),
        "maximum_birth_log_ratio_reference_width": _fraction_text(
            _max_reference_width(tables["log_doob_ratios"]["birth"])
        ),
        "maximum_death_log_ratio_reference_width": _fraction_text(
            _max_reference_width(tables["log_doob_ratios"]["death"])
        ),
        "maximum_replacement_log_ratio_reference_width": _fraction_text(
            _max_reference_width(tables["log_doob_ratios"]["replacement"])
        ),
        "maximum_nonzero_path_witness_width": _fraction_text(path_width),
        "maximum_quadrature_route_final_reference_width": _fraction_text(route_precision_width),
        "maximum_cap2_normalized_association_weight_width": _fraction_text(
            association_width
        ),
        "maximum_equal_prior_calibration_reference_width": _fraction_text(calibration_width),
        "maximum_cap2_nonunit_mark_fiber_rn_reference_width": _fraction_text(rn_width),
        "maximum_cap2_cap_boundary_reference_width": _fraction_text(cap_boundary_width),
        "maximum_initializer_full_law_reference_width": _fraction_text(initializer_width),
        "maximum_endpoint_full_law_reference_width": _fraction_text(endpoint_width),
        "endpoint_full_law_parameters_are_exact_rationals_so_reference_width_is_zero": endpoint_width == ZERO,
        "reference_precision_budget_checks": precision_checks,
        "all_reference_precision_budgets_pass": True,
        "reference_precision_is_distinct_from_scientific_error_and_candidate_enclosure_width": True,
        "cap2_association_bijection_count": association["exact_bijection_count"],
        "cap2_association_positive_unequal_and_normalized": True,
        "cap2_factorial_multiplicity_identities_exact": True,
        "cap2_positive_precap_zero_legal_cap_flux_exact": True,
        "classifier_nuisance_constancy_and_quotient_invariance_exact": True,
        "optional_nonzero_potential_gauge_invariance_exact": True,
        "nonzero_path_witness_components": {
            name: dict(path[name])
            for name in (
                "initializer",
                "continuous",
                "birth",
                "death",
                "replacement",
                "total",
            )
        },
    }


def _field_values() -> List[Dict[str, Any]]:
    common_fail = (
        "PASS_IFF_CERTIFIED_ERROR_UPPER_ENDPOINT_LE_SCIENTIFIC_THRESHOLD_AND_"
        "ENCLOSURE_WIDTH_LE_NUMERICAL_BUDGET;MISSING_STRADDLING_SUPPORT_LOSS_"
        "OR_STRUCTURAL_ZERO_RATIO_IS_HOLD"
    )
    return [
        {
            "field_id": "F007",
            "json_pointer": "/theory_and_known_law_plan/cap_and_reference_error_decomposition",
            "value": {
                "oriented_identity": "K_PATH=K0+KC+K_BIRTH+K_DEATH+K_REPLACEMENT",
                "shared_guide_error": "E=R_THETA-R_STAR",
                "cap_defect_is_sixth_kl_term": False,
                "ordered_nonoverlapping_error_bucket_roster": [
                    {"ordinal": 1, "bucket_id": "TARGET_REFERENCE_MISMATCH", "owner": "FUTURE_SELECTED_C17_C18_OR_OTHER_EXPLICIT_ORIENTED_TARGET_REFERENCE_ROUTE", "single_count_route": "NONINITIAL_NONTERMINAL_BASE_OR_DYNAMIC_TARGET_REFERENCE_OR_NAMED_INTERMEDIATE_LAW_COMPARISON_ONLY_EXCLUDES_F016_K0_AND_BUCKET_6_CURRENT_FIVE_TERM_SHARED_GUIDE_IDENTITY_EXCLUDES_IT"},
                    {"ordinal": 2, "bucket_id": "ANALYTIC_GUIDE_APPROXIMATION", "owner": "FUTURE_C17_ANALYTIC_AND_ASSOCIATION_GUIDE_APPROXIMATION_TERM", "single_count_route": "SHARED_GUIDE_AND_ASSOCIATION_GUIDE_APPROXIMATION_EXACTLY_ONCE_EXCLUDING_EVERY_CAP_INDUCED_RESTRICTION_OR_DEFECT_OWNED_BY_BUCKET_4"},
                    {"ordinal": 3, "bucket_id": "RESIDUAL_ESTIMATION", "owner": "FUTURE_C17_RESIDUAL_ESTIMATION_TERM", "single_count_route": "E_EQUALS_R_THETA_MINUS_R_STAR_ONLY"},
                    {"ordinal": 4, "bucket_id": "CAP_RESTRICTION_OR_DEFECT", "owner": "FUTURE_C17_SELECTED_CAP_REFERENCE_GUIDE_DEFECT_ROUTE_EXACTLY_ONCE", "single_count_route": "EXACTLY_ONE_OF_THE_THREE_ALLOWED_ROUTES_BELOW_AND_EXCLUDES_NONCAP_ANALYTIC_GUIDE_APPROXIMATION"},
                    {"ordinal": 5, "bucket_id": "INITIALIZATION", "owner": "F016_AND_K0_EXACT_VS_PLUGIN_INITIAL_LAW", "single_count_route": "NORMALIZED_INITIAL_LAW_COMPARISON_ONLY"},
                    {"ordinal": 6, "bucket_id": "TERMINAL_REFERENCE", "owner": "FUTURE_SELECTED_C17_C18_OR_OTHER_EXPLICIT_TERMINAL_REFERENCE_ROUTE", "single_count_route": "DISTINCT_FROM_F017_CANDIDATE_OWNED_CONDITIONED_ENDPOINT_VALIDATION_AND_EXCLUDED_FROM_CURRENT_SHARED_GUIDE_FIVE_TERM_IDENTITY"},
                    {"ordinal": 7, "bucket_id": "NUMERICAL", "owner": "OUTWARD_REFERENCE_AND_CANDIDATE_CERTIFICATION_BUDGETS", "single_count_route": "ARITHMETIC_ENCLOSURE_ONLY_NOT_A_SCIENTIFIC_KL_SUMMAND"},
                ],
                "bucket_ids_pairwise_disjoint": True,
                "every_bucket_counted_at_most_once": True,
                "allowed_single_count_routes": [
                    "RESIDUAL_PDE_STABILITY_COUNTS_DEFECT_DEPENDENCE_ONCE_INSIDE_E",
                    "PROJECTION_DECOMPOSITION_COUNTS_DEFECT_DEPENDENCE_ONCE_IN_THE_SELECTED_FORK",
                    "INTERMEDIATE_LAW_COMPARISON_WITH_EXPLICIT_LAWS_ORIENTATION_AND_PROVED_COMPOSITION_INEQUALITY",
                ],
                "kl_triangle_inequality_assumed": False,
                "initializer_owner": "K0",
                "continuous_owner": "KC",
                "legal_edge_family_owners": ["K_BIRTH", "K_DEATH", "K_REPLACEMENT"],
                "five_path_components_scope": "EXACT_VS_PLUGIN_SHARED_GUIDE_PATH_COMPARISON_ONLY_NOT_THE_SEVEN_END_TO_END_BUCKETS",
                "association_guide_error_owned_inside_bucket_2_exactly_once": True,
                "finite_rng_error_scope_outside_seven": "SEPARATE_FUTURE_RUNTIME_PARTICLE_OR_RNG_TERM",
                "terminal_match": "E_T_EQUALS_ZERO",
                "numerical_enclosure_is_not_scientific_error_term": True,
            },
        },
        {
            "field_id": "F008",
            "json_pointer": "/theory_and_known_law_plan/a1_exact_kl_tv_tolerances",
            "value": {
                "source": "PRE_D1_A1_SPEC_SECTION_7_3",
                "source_path": A1_SPEC_PATH,
                "source_raw_sha256": A1_SPEC_SHA256,
                "literal_table_row_count": 11,
                "canonical_decision_row_count": 12,
                "two_denominator_members_projected_as_separate_strict_checks": True,
                "rows": [dict(row) for row in A1_SECTION_7_3],
                "literal_failure_sentence": "Any numerical-gate failure places the scientific decision on HOLD.",
                "solver_controls_are_thresholds": False,
            },
        },
        {
            "field_id": "F009",
            "json_pointer": "/theory_and_known_law_plan/mixed_ctmc_ou_fixture_parameters",
            "value": _fixture_record(),
        },
        {
            "field_id": "F010",
            "json_pointer": "/theory_and_known_law_plan/mixed_evaluation_grid",
            "value": _grid_record(),
        },
        {
            "field_id": "F011",
            "json_pointer": "/theory_and_known_law_plan/mixed_exact_or_certified_kl_tv_tolerances",
            "value": {
                "role": "OMNIBUS_CANDIDATE_VS_EXACT_LAW_ACCEPTANCE_NOT_REFERENCE_WIDTH",
                "orientation": ORIENTATION,
                "law_pairs": [
                    {"pair_id": "INITIALIZER", "exact": "RHO_0^H", "candidate": "RHO_0^HAT_H", "linked_fields": ["F016_INITIALIZER_KL", "F016_INITIALIZER_TV"]},
                    {"pair_id": "CANDIDATE_OWNED_ENDPOINT", "exact": "RHO_T^H", "candidate": "RHO_T^HAT_H_PROPAGATED_BY_CANDIDATE", "linked_fields": ["F017_ENDPOINT_KL", "F017_ENDPOINT_TV"]},
                    {"pair_id": "FULL_PATH", "exact": "P_EXACT_H", "candidate": "P_CANDIDATE_HAT_H", "linked_fields": ["F018_PATH_KL", "PATH_TV"]},
                ],
                "metrics": [
                    _metric("OMNIBUS_KL", "F011_KL", "MAX_OF_INITIALIZER_ENDPOINT_AND_FULL_PATH_TARGET_FIRST_KL", "nat"),
                    _metric("OMNIBUS_TV", "F011_TV", "MAX_OF_INITIALIZER_ENDPOINT_AND_FULL_PATH_TV", "tv"),
                    _metric("EQUAL_PRIOR_CLASSIFIER_CALIBRATION", "F011_CALIBRATION", "MAX_OVER_ORDERED_55_CELL_TIME_MODE_MARK_UNION", "probability"),
                ],
                "omnibus_kl_candidate_value_definition": "COMPONENTWISE_INTERVAL_MAX_OF_F016_INITIALIZER_KL_F017_ENDPOINT_KL_F018_PATH_KL",
                "omnibus_tv_candidate_value_definition": "COMPONENTWISE_INTERVAL_MAX_OF_F016_INITIALIZER_TV_F017_ENDPOINT_TV_PATH_TV",
                "independent_self_report_permitted": False,
                "separate_structural_conjuncts_not_kl_or_tv_aggregands": [
                    "ATOMIC_TRUE_M2_ORBIT_FACTORIAL_AND_AGGREGATE_DEATH_REPLACEMENT_IDENTITIES",
                    "CONTINUOUS_TWO_ROUTE_NONUNIT_DESTINATION_MARK_FIBER_RN_JACOBIAN_IDENTITY",
                    "BOTH_POSITIVE_UNEQUAL_ASSOCIATION_BIJECTIONS",
                    "NORMALIZED_ASSOCIATION_WEIGHTS_SUM_TO_ONE",
                    "BLOCKED_ALPHA_POSITIVE_AUXILIARY_CAP3_PROPOSAL_AND_ZERO_LEGAL_CAP2_OUTWARD_BIRTH",
                    "BLOCKED_BETA_POSITIVE_AUXILIARY_CAP3_PROPOSAL_AND_ZERO_LEGAL_CAP2_OUTWARD_BIRTH",
                    "SIGNED_AGGREGATE_CAP2_VS_CAP3_HARMONIC_DEFECT_DERIVED_FROM_BOTH_FAMILIES",
                    "CLASSIFIER_NUISANCE_CONSTANT_IN_PROCESS_TIME_AND_STATE_AND_QUOTIENT_INVARIANCE",
                    "CALIBRATION_USES_GAUGE_FIXED_ZERO_NUISANCE_AND_DETECTS_NONZERO_CONSTANT_SHIFT",
                ],
                "rule": common_fail,
            },
        },
        {
            "field_id": "F012",
            "json_pointer": "/theory_and_known_law_plan/drift_error_tolerance",
            "value": {
                "metric": _metric(
                    "ABS_COVARIANCE_NORM_DRIFT_DISCREPANCY",
                    "F012_DRIFT",
                    "MAX_OVER_EVERY_OCCUPIED_TIME_MODE_MARK_GRID_CELL",
                    "drift",
                ),
                "exact_formula": "SIGMA_SQUARED_TIMES_GRADIENT_LOG_HAT_H_MINUS_GRADIENT_LOG_H",
                "coordinate_role": "CURRENT_OCCUPIED_STATE_MARK_X",
                "empty_mode": "NOT_APPLICABLE_NO_TANGENT_COORDINATE",
                "rule": common_fail,
            },
        },
        _ratio_field("F013", "birth", "F013_BIRTH_LOG_RATIO", common_fail),
        _ratio_field("F014", "death", "F014_DEATH_LOG_RATIO", common_fail),
        _ratio_field("F015", "replacement", "F015_REPLACEMENT_LOG_RATIO", common_fail),
        {
            "field_id": "F016",
            "json_pointer": "/theory_and_known_law_plan/initializer_error_tolerance",
            "value": {
                "role": "FULL_NORMALIZED_INITIAL_LAW_CANDIDATE_ERROR",
                "orientation": ORIENTATION,
                "metrics": [
                    _metric("INITIALIZER_KL", "F016_INITIALIZER_KL", "FULL_MODE_AND_MARK_MIXTURE_LAW", "nat"),
                    _metric("INITIALIZER_TV", "F016_INITIALIZER_TV", "FULL_MODE_AND_MARK_MIXTURE_LAW", "tv"),
                ],
                "normalizers_certified": True,
                "common_support_required": True,
                "rule": common_fail,
            },
        },
        {
            "field_id": "F017",
            "json_pointer": "/theory_and_known_law_plan/endpoint_error_tolerance",
            "value": {
                "role": "FULL_CANDIDATE_OWNED_ENDPOINT_LAW_ERROR_NOT_TERMINAL_POTENTIAL_OR_MOMENTS_ONLY",
                "orientation": ORIENTATION,
                "metrics": [
                    _metric("ENDPOINT_KL", "F017_ENDPOINT_KL", "FULL_MODE_AND_MARK_MIXTURE_LAW", "nat"),
                    _metric("ENDPOINT_TV", "F017_ENDPOINT_TV", "FULL_MODE_AND_MARK_MIXTURE_LAW", "tv"),
                ],
                "candidate_owned_propagation_required": True,
                "exact_self_reference_representation_identifies_full_law": True,
                "rule": common_fail,
            },
        },
        {
            "field_id": "F018",
            "json_pointer": "/theory_and_known_law_plan/path_diagnostic_tolerance",
            "value": {
                "role": "FULL_ORIENTED_CANDIDATE_PATH_ERROR",
                "metric": _metric("PATH_KL_TOTAL", "F018_PATH_KL", "IDEAL_CONTINUOUS_TIME_PATH_LAWS", "nat"),
                "orientation": ORIENTATION,
                "required_components": ["K0", "KC", "K_BIRTH", "K_DEATH", "K_REPLACEMENT"],
                "error_definition": "E=LOG(HAT_H/H)",
                "initializer_formula": "K0=LOG(Z_HAT/Z_H)-EXPECTATION_RHO0_H[E(0,X)]_WITH_Z_H=1_IN_THIS_FIXTURE",
                "continuous_formula": "KC=(1/2)*EXPECTATION_P_H[INTEGRAL_0_T_NORM(SIGMA_TRANSPOSE*GRADIENT_E)^2_DT]",
                "legal_jump_family_formula": "K_FAMILY=EXPECTATION_P_H[INTEGRAL_0_T_Q_H_FAMILY*PHI(DELTA_E)_DT]",
                "jump_convexity": "PHI(Z)=EXP(Z)-1-Z",
                "jump_increment_orientation": "DELTA_E=E(DESTINATION)-E(SOURCE)",
                "conditioned_aggregate_rate": "Q_H_INCLUDES_UNLABELED_ROUTE_MULTIPLICITY_DESTINATION_FIBER_RN_AND_JACOBIAN_BEFORE_H_RATIO",
                "structural_zero_cap_edges_in_jump_sum": False,
                "target_occupation_required": True,
                "component_nonnegative_upper_enclosures_required": True,
                "support_loss": "INFINITE_KL_AND_HOLD",
                "reverse_kl": "DIAGNOSTIC_ONLY_NOT_SUBSTITUTABLE",
                "cap_defect_component_permitted": False,
                "rule": common_fail,
            },
        },
    ]


def _metric(name: str, key: str, aggregation: str, unit: str) -> Dict[str, Any]:
    return {
        "name": name,
        "aggregation": aggregation,
        "direction": "<=",
        "scientific_error_threshold": _fraction_text(SCIENTIFIC_THRESHOLDS[key]),
        "numerical_enclosure_width_budget": _fraction_text(NUMERICAL_WIDTH_BUDGETS[key]),
        "unit": unit,
        "decision_uses_error_upper_endpoint": True,
        "width_alone_can_pass": False,
    }


def _ratio_field(field_id: str, family: str, key: str, common_fail: str) -> Dict[str, Any]:
    pointer_name = family + "_ratio_error_tolerance"
    coordinate_role = {
        "birth": "NEWLY_DRAWN_DESTINATION_FIBER_MARK_Z_EMPTY_SOURCE_HAS_NO_MARK",
        "death": "REMOVED_SOURCE_OCCURRENCE_MARK_X_EMPTY_DESTINATION_HAS_NO_MARK",
        "replacement": "RETAINED_MARK_X_IDENTICAL_AT_SOURCE_AND_DESTINATION",
    }[family]
    return {
        "field_id": field_id,
        "json_pointer": "/theory_and_known_law_plan/" + pointer_name,
        "value": {
            "metric": _metric(
                "ABS_LOG_DOOB_RATIO_DISCREPANCY",
                key,
                "MAX_OVER_EVERY_LEGAL_AGGREGATE_%s_EDGE_TIME_AND_MARK" % family.upper(),
                "log_rate_ratio",
            ),
            "exact_formula": "ABS[(LOG_HAT_H_DEST-LOG_HAT_H_SOURCE)-(LOG_H_DEST-LOG_H_SOURCE)]",
            "coordinate_role": coordinate_role,
            "base_aggregate_multiplicity_destination_fiber_rn_and_jacobian_applied_before_h_ratio": True,
            "structural_zero_or_blocked_cap_edge": "FLUX_CHECK_ONLY_NO_RATIO",
            "rule": common_fail,
        },
    }


def _fixture_record() -> Dict[str, Any]:
    return {
        "fixture_id": "COMPOSITE_CAP1_PATH_PLUS_CAP2_STRUCTURAL_MIXED_MARKED_KNOWN_LAW_SUITE_V1",
        "suite_components": [
            "CAP1_TWO_TYPE_OCCURRENCE_MARKED_STATIONARY_OU_PATH_REFERENCE",
            "CAP2_THREE_DISJOINT_MULTIPLICITY_NONUNIT_RN_AND_ASSOCIATION_STRUCTURAL_SUBCASES",
        ],
        "horizon": "1/1",
        "modes": list(MODE_NAMES),
        "caps": [1, 2],
        "primary_path_cap": 1,
        "structural_witness_cap": 2,
        "mode_generator": [[_fraction_text(value) for value in row] for row in MODE_GENERATOR],
        "stationary_mode_probabilities": [
            _fraction_text(value) for value in STATIONARY_MODE_PROBABILITIES
        ],
        "birth_destination_mark_fiber": "NU_EQUALS_" + _normal_law_label(OU_INVARIANT_MEAN, OU_INVARIANT_VARIANCE),
        "birth_rates_empty_to_alpha_beta": [_fraction_text(value) for value in BIRTH_RATES],
        "death_rates_per_occurrence_alpha_beta": [_fraction_text(value) for value in DEATH_RATES],
        "replacement_rates_alpha_to_beta_beta_to_alpha": [
            _fraction_text(value) for value in REPLACEMENT_RATES
        ],
        "replacement_mark_kernel": "DIRAC_AT_SOURCE_MARK_RN_JACOBIAN_ONE",
        "ou": {
            "sde": "dX=-(1/2)Xdt+dW",
            "invariant_law": _normal_law_label(OU_INVARIANT_MEAN, OU_INVARIANT_VARIANCE),
            "invariant_mean": _fraction_text(OU_INVARIANT_MEAN),
            "invariant_variance": _fraction_text(OU_INVARIANT_VARIANCE),
            "mean_reversion": "1/2",
            "diffusion": "1/1",
        },
        "observation": {
            "reference_lambda": _normal_law_label(OU_INVARIANT_MEAN, OBSERVATION_REFERENCE_VARIANCE),
            "reference_variance": _fraction_text(OBSERVATION_REFERENCE_VARIANCE),
            "observation_noise_variance": _fraction_text(OBSERVATION_NOISE_VARIANCE),
            "empty_kernel": "LAMBDA",
            "occupied_kernel": "B_I*LAMBDA+A_I*NORMAL_MEAN_X_VARIANCE_1",
            "alpha_clutter_mark_weights": ["1/4", "3/4"],
            "beta_clutter_mark_weights": ["1/2", "1/2"],
            "fixed_branch_y": _fraction_text(OBSERVATION_VALUE),
            "fixed_branch_density_ratio": "G0=1;GI=B_I+A_I*SQRT(2)*EXP(-X^2/2)",
            "each_kernel_normalizes_over_y": True,
            "fixed_branch_expectation_under_nu": "1/1",
        },
        "equal_prior_classifier_calibration": {
            "product_observation_marginal": "P_A=LAMBDA",
            "joint_product_density_ratio": "H",
            "exact_nuisance": "0/1",
            "exact_probability": "TAU=H/(1+H)",
            "empty_probability": "1/2",
            "positive_structural_nuisance": _fraction_text(CLASSIFIER_NUISANCE),
            "positive_nuisance_is_constant_in_process_time_and_state": True,
            "positive_nuisance_changes_unquotiented_calibration": True,
        },
        "exact_information": {
            "h_empty": "1",
            "h_type": "1-A_I(t)+A_I(t)*PSI(t,X)",
            "killed_type_generator": [
                [_fraction_text(value) for value in row]
                for row in KILLED_TYPE_GENERATOR
            ],
            "terminal_mark_coefficients": ["3/4", "1/2"],
            "A_formula": "A(t)=EXP((1-t)K)*(3/4,1/2)^T",
            "psi_formula": "SQRT(2/(2-RHO^2))*EXP(-RHO^2*X^2/(2*(2-RHO^2)))",
            "rho_formula": "EXP(-(1-t)/2)",
        },
        "nonzero_reference_perturbation": {
            "role": "REFERENCE_INTEGRATOR_AND_FIVE_TERM_PATH_IDENTITY_WITNESS_NOT_DECISION_CANDIDATE",
            "empty": "E_EMPTY(t)=0",
            "occupied_formula": "E_I(t,x)=(1-t)*(C_I+S*x)",
            "mode_constants_empty_alpha_beta": ["0/1", "1/5", "-1/4"],
            "mark_slope": "1/3",
            "terminal_match": "E_I(1,x)=0_FOR_EVERY_MODE_AND_REAL_X",
            "candidate_pass_value": False,
            "cap_defect_component": False,
        },
        "checked_exact_invariants": {
            "pi_times_mode_generator_zero": True,
            "mode_generator_rows_sum_zero": True,
            "birth_mark_law_is_ou_invariant": True,
            "replacement_retains_mark": True,
            "expectation_nu_psi_equals_one": True,
            "expectation_nu_h_type_equals_one": True,
            "empty_backward_birth_terms_cancel_and_h_empty_equals_one": True,
            "occupied_coefficient_equation_matches_killed_generator": True,
            "A_componentwise_bounded_by_terminal_coefficients": True,
            "A_bound_lemma": "K*A_TERMINAL=(-29/80,-1/4)<=0_AND_EXP(S*K)_IS_NONNEGATIVE_SUBSTOCHASTIC",
            "information_strictly_positive": True,
            "information_uniform_lower_bound": "1/4",
            "information_lower_bound_proof": "0<=A_I(t)<=3/4_AND_PSI>0_IMPLIES_H_I=1-A_I+A_I*PSI>=1-A_I>=1/4",
            "evidence_equals_one": True,
            "all_birth_death_replacement_families_nonempty": True,
            "type_changing_mark_path_exercised": True,
            "blocked_cap_birth_flux_exercised": True,
            "source_multiplicity_exact_but_only_zero_or_one": True,
            "association_kernel_normalized_but_at_most_one_occurrence": True,
            "nonzero_common_gauge_invariance_checked": True,
            "classifier_nuisance_constancy_and_quotient_invariance_checked": True,
            "equal_prior_calibration_identity_checked": True,
            "nonunit_destination_mark_fiber_rn_orientation_checked": True,
        },
        "scope_limitations": {
            "nontrivial_multiplicity_exercised_by_same_suite_cap2_witness": True,
            "ambiguous_multi_occurrence_association_exercised_by_same_suite_cap2_witness": True,
            "cap2_witness_used_as_cap1_path_component_substitute": False,
            "cap2_three_subcases_are_same_suite_but_not_primary_path_substitutes": True,
            "learned_candidate_exercised": False,
            "r2_completed": False,
            "c17_proved": False,
            "b05_closed": False,
        },
        "cap2_structural_witness": _cap2_structural_fixture_record(),
        "classifier_nuisance_identity": {
            "exact_calibration_nuisance": "0/1",
            "structural_nonzero_nuisance": _fraction_text(CLASSIFIER_NUISANCE),
            "form": "C(A,M,Z)",
            "forbidden_process_inputs": ["U", "Y"],
            "never_part_of_h_or_hat_h": True,
            "quotient_and_normalized_initializer_cancel_it": True,
            "unquotiented_calibration_detects_it": True,
        },
        "optional_potential_gauge_invariance": {
            "gauge": "q(t)=(1-t)*(%s)" % _fraction_text(NUISANCE_GAUGE),
            "applied_to_modes": ["EMPTY", "ALPHA", "BETA"],
            "terminal_match_preserved": True,
            "gradient_and_all_legal_edge_increments_unchanged": True,
            "normalized_initializer_common_factor_cancels": True,
            "all_five_path_components_unchanged": True,
            "substitutes_for_classifier_nuisance_identity": False,
        },
    }


def build_exact_self_candidate(certificate: Mapping[str, Any]) -> Dict[str, Any]:
    if type(certificate) is not dict or type(certificate.get("reference_table_sha256")) is not str:
        raise CertificationError("exact-self construction requires a canonical certificate")
    zero = {"lower": "0/1", "upper": "0/1"}
    candidate: Dict[str, Any] = {
        "schema_version": SCHEMA + "/candidate-errors-v1",
        "orientation": ORIENTATION,
        "reference_table_sha256": certificate["reference_table_sha256"],
        "grid_sha256": certificate["grid_sha256"],
        "support_preserved": True,
        "all_declared_grid_cells_evaluated": True,
        "candidate_owned_endpoint_propagated": True,
        "full_initializer_law_compared": True,
        "full_endpoint_law_compared": True,
        "cap2_atomic_factorial_multiplicity_checked": True,
        "cap2_nonunit_mark_fiber_rn_orientation_checked": True,
        "cap2_association_both_terms_checked": True,
        "cap2_association_normalization_checked": True,
        "cap2_blocked_birth_flux_checked": True,
        "cap2_blocked_alpha_birth_checked": True,
        "cap2_blocked_beta_birth_checked": True,
        "cap2_aggregate_harmonic_defect_checked": True,
        "cap2_harmonic_defect_and_bregman_distinguished": True,
        "classifier_nuisance_constancy_and_quotient_invariance_checked": True,
        "equal_prior_calibration_all_cells_checked": True,
        "structural_zero_ratio_attempted": False,
        "cap_defect_inserted_as_path_component": False,
        "path_component_roster": ["K0", "KC", "K_BIRTH", "K_DEATH", "K_REPLACEMENT"],
        "errors": {
            "F011_KL": dict(zero),
            "F011_TV": dict(zero),
            "F011_CALIBRATION": dict(zero),
            "F012_DRIFT": dict(zero),
            "F013_BIRTH_LOG_RATIO": dict(zero),
            "F014_DEATH_LOG_RATIO": dict(zero),
            "F015_REPLACEMENT_LOG_RATIO": dict(zero),
            "F016_INITIALIZER_KL": dict(zero),
            "F016_INITIALIZER_TV": dict(zero),
            "F017_ENDPOINT_KL": dict(zero),
            "F017_ENDPOINT_TV": dict(zero),
            "F018_PATH_KL": dict(zero),
        },
        "law_errors_linking_F011_F016_F017_F018": {
            "INITIALIZER_KL": dict(zero),
            "INITIALIZER_TV": dict(zero),
            "ENDPOINT_KL": dict(zero),
            "ENDPOINT_TV": dict(zero),
            "PATH_KL": dict(zero),
            "PATH_TV": dict(zero),
        },
        "path_components": {
            "K0": dict(zero),
            "KC": dict(zero),
            "K_BIRTH": dict(zero),
            "K_DEATH": dict(zero),
            "K_REPLACEMENT": dict(zero),
            "TOTAL": dict(zero),
        },
        "exact_self_reference_only": True,
        "learned_or_scientific_result": False,
    }
    payload = canonical_bytes(candidate)
    candidate["candidate_sha256"] = hashlib.sha256(EXACT_SELF_DOMAIN + payload).hexdigest()
    return candidate


def _strict_error_interval(value: object, key: str) -> Interval:
    if type(value) is not dict or set(value) != {"lower", "upper"}:
        raise CertificationError(key + " must be an exact two-endpoint dict")
    lower = _fraction_from_text(value["lower"])
    upper = _fraction_from_text(value["upper"])
    if lower < ZERO or upper < lower:
        raise CertificationError(key + " error interval is invalid")
    return lower, upper


def qualify_candidate_errors(certificate: object, candidate: object) -> Dict[str, Any]:
    """Apply frozen upper-endpoint and independent width rules fail-closed."""

    if type(certificate) is not dict or type(candidate) is not dict:
        raise CertificationError("certificate and candidate must be exact built-in dicts")
    _bounded_tree_check(certificate)
    _bounded_tree_check(candidate)
    validate_certificate(certificate)
    expected_keys = {
        "schema_version",
        "orientation",
        "reference_table_sha256",
        "grid_sha256",
        "support_preserved",
        "all_declared_grid_cells_evaluated",
        "candidate_owned_endpoint_propagated",
        "full_initializer_law_compared",
        "full_endpoint_law_compared",
        "cap2_atomic_factorial_multiplicity_checked",
        "cap2_nonunit_mark_fiber_rn_orientation_checked",
        "cap2_association_both_terms_checked",
        "cap2_association_normalization_checked",
        "cap2_blocked_birth_flux_checked",
        "cap2_blocked_alpha_birth_checked",
        "cap2_blocked_beta_birth_checked",
        "cap2_aggregate_harmonic_defect_checked",
        "cap2_harmonic_defect_and_bregman_distinguished",
        "classifier_nuisance_constancy_and_quotient_invariance_checked",
        "equal_prior_calibration_all_cells_checked",
        "structural_zero_ratio_attempted",
        "cap_defect_inserted_as_path_component",
        "path_component_roster",
        "errors",
        "law_errors_linking_F011_F016_F017_F018",
        "path_components",
        "exact_self_reference_only",
        "learned_or_scientific_result",
        "candidate_sha256",
    }
    if set(candidate) != expected_keys:
        raise CertificationError("candidate key roster changed")
    if candidate != build_exact_self_candidate(certificate):
        raise CertificationError(
            "this pre-outcome package qualifies only its freshly rebuilt exact-self reference"
        )
    payload = dict(candidate)
    supplied_digest = payload.pop("candidate_sha256")
    if type(supplied_digest) is not str or supplied_digest != hashlib.sha256(
        EXACT_SELF_DOMAIN + canonical_bytes(payload)
    ).hexdigest():
        raise CertificationError("candidate self-digest invalid")
    if candidate["schema_version"] != SCHEMA + "/candidate-errors-v1":
        raise CertificationError("candidate schema changed")
    if candidate["orientation"] != ORIENTATION:
        raise CertificationError("candidate KL orientation changed")
    if candidate["reference_table_sha256"] != certificate["reference_table_sha256"]:
        raise CertificationError("candidate reference table changed")
    if candidate["grid_sha256"] != certificate["grid_sha256"]:
        raise CertificationError("candidate grid changed")
    for flag in (
        "support_preserved",
        "all_declared_grid_cells_evaluated",
        "candidate_owned_endpoint_propagated",
        "full_initializer_law_compared",
        "full_endpoint_law_compared",
        "cap2_atomic_factorial_multiplicity_checked",
        "cap2_nonunit_mark_fiber_rn_orientation_checked",
        "cap2_association_both_terms_checked",
        "cap2_association_normalization_checked",
        "cap2_blocked_birth_flux_checked",
        "cap2_blocked_alpha_birth_checked",
        "cap2_blocked_beta_birth_checked",
        "cap2_aggregate_harmonic_defect_checked",
        "cap2_harmonic_defect_and_bregman_distinguished",
        "classifier_nuisance_constancy_and_quotient_invariance_checked",
        "equal_prior_calibration_all_cells_checked",
    ):
        if candidate[flag] is not True:
            raise CertificationError(flag + " must be true")
    if candidate["structural_zero_ratio_attempted"] is not False:
        raise CertificationError("structural-zero ratio is forbidden")
    if candidate["cap_defect_inserted_as_path_component"] is not False:
        raise CertificationError("cap defect cannot be a path component")
    if candidate["path_component_roster"] != [
        "K0", "KC", "K_BIRTH", "K_DEATH", "K_REPLACEMENT"
    ]:
        raise CertificationError("path component roster changed")
    if type(candidate["errors"]) is not dict or set(candidate["errors"]) != set(SCIENTIFIC_THRESHOLDS):
        raise CertificationError("candidate error roster changed")
    for key in sorted(SCIENTIFIC_THRESHOLDS):
        interval = _strict_error_interval(candidate["errors"][key], key)
        if interval[1] > SCIENTIFIC_THRESHOLDS[key]:
            raise CertificationError(key + " certified upper endpoint exceeds threshold")
        if _iwidth(interval) > NUMERICAL_WIDTH_BUDGETS[key]:
            raise CertificationError(key + " enclosure width exceeds budget")
    law_key_roster = {
        "INITIALIZER_KL",
        "INITIALIZER_TV",
        "ENDPOINT_KL",
        "ENDPOINT_TV",
        "PATH_KL",
        "PATH_TV",
    }
    law_errors_raw = candidate["law_errors_linking_F011_F016_F017_F018"]
    if type(law_errors_raw) is not dict or set(law_errors_raw) != law_key_roster:
        raise CertificationError("linked law-error roster changed")
    law_errors = {
        key: _strict_error_interval(law_errors_raw[key], key)
        for key in law_key_roster
    }
    alias_pairs = {
        "F016_INITIALIZER_KL": "INITIALIZER_KL",
        "F016_INITIALIZER_TV": "INITIALIZER_TV",
        "F017_ENDPOINT_KL": "ENDPOINT_KL",
        "F017_ENDPOINT_TV": "ENDPOINT_TV",
        "F018_PATH_KL": "PATH_KL",
    }
    for field_key, law_key in alias_pairs.items():
        if _strict_error_interval(candidate["errors"][field_key], field_key) != law_errors[law_key]:
            raise CertificationError(field_key + " is not linked to " + law_key)
    omnibus_kl = (
        max(law_errors[key][0] for key in ("INITIALIZER_KL", "ENDPOINT_KL", "PATH_KL")),
        max(law_errors[key][1] for key in ("INITIALIZER_KL", "ENDPOINT_KL", "PATH_KL")),
    )
    omnibus_tv = (
        max(law_errors[key][0] for key in ("INITIALIZER_TV", "ENDPOINT_TV", "PATH_TV")),
        max(law_errors[key][1] for key in ("INITIALIZER_TV", "ENDPOINT_TV", "PATH_TV")),
    )
    if _strict_error_interval(candidate["errors"]["F011_KL"], "F011_KL") != omnibus_kl:
        raise CertificationError("F011 KL is not the deterministic linked-law maximum")
    if _strict_error_interval(candidate["errors"]["F011_TV"], "F011_TV") != omnibus_tv:
        raise CertificationError("F011 TV is not the deterministic linked-law maximum")
    path_keys = {"K0", "KC", "K_BIRTH", "K_DEATH", "K_REPLACEMENT", "TOTAL"}
    if type(candidate["path_components"]) is not dict or set(candidate["path_components"]) != path_keys:
        raise CertificationError("candidate path component details changed")
    components = {
        key: _strict_error_interval(candidate["path_components"][key], key)
        for key in path_keys
    }
    component_sum = sum_interval(
        components[key] for key in ("K0", "KC", "K_BIRTH", "K_DEATH", "K_REPLACEMENT")
    )
    total = components["TOTAL"]
    if total != component_sum:
        raise CertificationError("path total must equal canonical five-component interval sum")
    if candidate["errors"]["F018_PATH_KL"] != candidate["path_components"]["TOTAL"]:
        raise CertificationError("F018 total differs from path total")
    if candidate["exact_self_reference_only"] is not True:
        raise CertificationError("exact-self flag must be true")
    if candidate["learned_or_scientific_result"] is not False:
        raise CertificationError("local candidate cannot be scientific result")
    return {
        "schema_version": candidate["schema_version"],
        "orientation": ORIENTATION,
        "candidate_sha256": supplied_digest,
        "scientific_candidate_error_upper_endpoints_pass": True,
        "numerical_width_budgets_pass": True,
        "validation": "PASS",
    }


def build_certificate() -> Dict[str, Any]:
    """Build the deterministic reference/design certificate."""

    tables = build_reference_tables()
    table_bytes = canonical_bytes(tables)
    grid = _grid_record()
    grid_bytes = canonical_bytes(grid)
    summary = _reference_summary(tables)
    certificate: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "state": STATE,
        "orientation": ORIENTATION,
        "fixture": _fixture_record(),
        "grid": grid,
        "field_values": _field_values(),
        "arithmetic": {
            "numeric_authority": "EXACT_RATIONAL_OUTWARD_INTERVAL",
            "matrix_exponential": "NONNEGATIVE_UNIFORMIZATION_PLUS_EXPLICIT_POISSON_TAIL",
            "exp_log": "RATIONAL_TAYLOR_PLUS_ANALYTIC_TAIL",
            "sqrt": "RATIONAL_INTEGER_ROOT_OUTWARD_ROUNDING",
            "time_integration": "COMPOSITE_SIMPSON_PLUS_INTERVAL_GLOBAL_FOURTH_DERIVATIVE_BOUND",
            "uniformization_terms": UNIFORMIZATION_TERMS,
            "exp_log_terms": EXP_TERMS,
            "simpson_subintervals": SIMPSON_SUBINTERVALS,
            "adaptive_quadrature_error_estimate_used_as_bound": False,
            "binary64_crosscheck_used_as_bound": False,
            "reference_output_used_as_threshold": False,
            "scientific_threshold_and_numerical_width_budget_separate": True,
        },
        "reference_table_sha256": hashlib.sha256(TABLE_DOMAIN + table_bytes).hexdigest(),
        "reference_table_bytes": len(table_bytes),
        "grid_sha256": hashlib.sha256(GRID_DOMAIN + grid_bytes).hexdigest(),
        "reference_summary": summary,
        "exact_self_qualification_only": {
            "candidate_error_is_exact_zero": True,
            "qualifies_reference_implementation": True,
            "qualifies_nonzero_or_learned_candidate": False,
            "nonzero_residual_path_witness_is_decision_candidate": False,
        },
        "nonclaims": {
            "scientific_execution": False,
            "training": False,
            "learned_checkpoint": False,
            "r1_completed": False,
            "r2_completed": False,
            "c17_proved": False,
            "b05_closed": False,
            "gate_a_closed": False,
            "formal_test_closed": False,
            "blocker_closed": False,
            "result_or_claim_promoted": False,
            "network_data_entropy_runtime_or_submission_route": False,
        },
    }
    payload = canonical_bytes(certificate)
    certificate["certificate_sha256"] = hashlib.sha256(
        CERTIFICATE_DOMAIN + payload
    ).hexdigest()
    if certificate["certificate_sha256"] != FROZEN_CERTIFICATE_SHA256:
        raise CertificationError("fresh exact certificate differs from frozen digest")
    canonical_bytes(certificate)
    return certificate


def validate_certificate(value: object) -> Dict[str, Any]:
    if type(value) is not dict:
        raise CertificationError("certificate must be an exact built-in dict")
    _bounded_tree_check(value)
    payload = dict(value)
    supplied_digest = payload.pop("certificate_sha256", None)
    if type(supplied_digest) is not str or len(supplied_digest) != 64:
        raise CertificationError("certificate digest is malformed")
    computed_digest = hashlib.sha256(
        CERTIFICATE_DOMAIN + canonical_bytes(payload)
    ).hexdigest()
    if supplied_digest != computed_digest:
        raise CertificationError("certificate self-digest is invalid")
    if supplied_digest != FROZEN_CERTIFICATE_SHA256:
        raise CertificationError("certificate differs from the source-frozen exact output")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "certificate_sha256": supplied_digest,
        "reference_table_sha256": value["reference_table_sha256"],
        "grid_sha256": value["grid_sha256"],
        "validation": "PASS",
    }


__all__ = [
    "A1_SECTION_7_3",
    "CertificationError",
    "LEGAL_EDGES",
    "MARK_GRID",
    "MODE_NAMES",
    "NUMERICAL_WIDTH_BUDGETS",
    "ORIENTATION",
    "SCHEMA",
    "SCIENTIFIC_THRESHOLDS",
    "STATE",
    "TIME_GRID",
    "build_certificate",
    "build_exact_self_candidate",
    "build_reference_tables",
    "canonical_bytes",
    "exp_bounds",
    "log_bounds",
    "qualify_candidate_errors",
    "sqrt_bounds",
    "validate_certificate",
]
