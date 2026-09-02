"""Independent analytic predictions for the Test-28 mixed fixtures.

This module derives the ideal-rational and stored-binary64-parameter analytic
laws of ``T28-M1-Q`` and ``T28-M2-Q``.  It intentionally does not import the
runtime reference sampler, an initializer kernel, a score provider, the CP50
float oracle, NumPy, SciPy, or a learned model.

Every authoritative numerical endpoint is an exact :class:`Fraction`.
Square roots are enclosed by integer-square-root dyadic brackets, and the two
negative exponentials are enclosed by alternating rational Taylor sums.  The
primitive enclosure width is at most ``2^-256``.  No floating-point or
transcendental-library result enters an authoritative prediction.

The analytic references retain ideal Gaussian fibers.  They are not the law
of the finite-precision reference sampler.  In particular, this module makes
no claim about ``mu_fp``, IID proposals, random-source uniformity,
operational ``p64``/``alpha64``/``rho64``, an exact or operational finite-J
SIR distribution, confirmatory evidence, or a manuscript result.  Separate
records expose conditional uint64-quantization and exact-IID SIR theorem
bounds for the named analytic laws; they do not establish their premises.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, fields, is_dataclass
from fractions import Fraction
from typing import Optional, Tuple


CP53_TEST28_PREDICTION_SCHEMA_VERSION = "cp53-test28-mixed-analytic-predictions-v1"
CP53_TEST28_RATIONAL_ENCLOSURE_BITS = 256
MAX_CP53_TEST28_EXACT_INTEGER_BITS = 8192
MAX_CP53_TEST28_REJECTION_ATTEMPTS = 1_000_000
MAX_CP53_TEST28_SIR_PARTICLES = 1_000_000
CP53_TEST28_RATIONAL_INTERVAL_METHOD = (
    "exact-rational-interval-v1:integer-isqrt-dyadic-brackets-256-bits;"
    "alternating-rational-taylor-exp-minus-x;exact-positive-interval-"
    "arithmetic;dyadic-outward-rounding-only-for-large-integer-powers"
)
CP53_TEST28_RATIONAL_PROOF_STATEMENT = (
    "authoritative endpoints are exact Fractions; square-root coverage follows "
    "from integer-square inequalities and exponential coverage from the "
    "alternating-series remainder theorem; no Decimal or libm premise is used"
)
CP53_TEST28_EXACT_IID_SIR_BOUND_STATEMENT = (
    "conditional on exact IID proposals from the named analytic reference, "
    "exact positive weights, and exact categorical resampling: "
    "TV(Q_J,rho) <= sqrt(Var(W))/(2*E[W]*sqrt(J)); none of those operational "
    "premises is certified here"
)
CP53_TEST28_CONDITIONAL_UINT64_BOUND_STATEMENT = (
    "for a named analytic proposal/score law with 0<W<=1 and normalizer Z, "
    "if p64=floor(2^64*W)/2^64 is used with IID proposals and independent "
    "uniform uint64 words, then 0<=W-p64<2^-64, alpha64 lies "
    "in (beta_lower-2^-64,beta_upper], fixed-A exhaustion has the recorded "
    "inclusive-lower and "
    "strict-upper bounds, and TV(rho64,rho)<2^-64/beta_lower; this is a "
    "conditional theorem bound, not a numerical mu_fp or live-kernel prediction"
)
CP53_TEST28_CONDITIONAL_EXACT_IID_SIR_BOUND_STATEMENT = (
    "for exact IID proposals from the named analytic reference, exact positive "
    "weights, and exact categorical resampling, the finite-J marginal obeys "
    "TV(Q_J,rho)<=sqrt(Var(W))/(2*Z*sqrt(J)); the record encloses this theorem "
    "bound but neither derives Q_J nor certifies any operational premise"
)
CP53_TEST28_PREDICTION_SCOPE = (
    "independent-m1-m2-ideal-rational-and-binary64-parameter-analytic-laws;"
    "exact-reference-parameters;exact-rational-outward-normalizer-"
    "acceptance-second-moment-variance-category-count-and-event-type-"
    "probabilities;conditional-exact-iid-sir-and-uint64-theorem-bounds;"
    "signed-absolute-relative-and-finite-category-tv-parameter-perturbations;"
    "ideal-gaussian-fibers;not-runtime-sampler-not-operational-rejection-"
    "not-exact-finite-j-distribution-not-operational-sir-not-confirmatory-"
    "not-manuscript-evidence"
)
CP53_TEST28_PREDICTION_NONCLAIMS = (
    "Pi_N^rat and Pi_N^b64 are not identified with the operational sampler law mu_fp",
    "no proposal IID, source uniformity, stream independence, or sampler law is verified",
    "no numerical operational p64, alpha64, rho64, exhaustion, or selected mu_fp law is derived",
    "no exact finite-J SIR distribution or operational 53-bit categorical-transform law is derived",
    "the rational enclosure implementation is tested but not mechanically proved",
    "these deterministic predictions are not a confirmatory run or manuscript evidence",
)

_DIGEST_DOMAIN = "cp53-test28-mixed-analytic-predictions-v1"
_ALLOWED_FIXTURES = ("T28-M1-Q", "T28-M2-Q")
_ALLOWED_LAYERS = ("ideal_rational", "binary64_parameter")
_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_TWO = Fraction(2, 1)
_HALF = Fraction(1, 2)
_IDEAL_ACTIVITY = Fraction(1, 1)
_IDEAL_WEIGHTS = (Fraction(2, 5), Fraction(3, 5))
_BINARY64_ACTIVITY = Fraction.from_float(1.0)
_BINARY64_WEIGHTS = (Fraction.from_float(0.4), Fraction.from_float(0.6))
_ENCLOSURE_DENOMINATOR = 1 << CP53_TEST28_RATIONAL_ENCLOSURE_BITS
_ENCLOSURE_TARGET_WIDTH = Fraction(1, _ENCLOSURE_DENOMINATOR)


@dataclass(frozen=True)
class _Interval:
    lower: Fraction
    upper: Fraction

    def __post_init__(self) -> None:
        if type(self.lower) is not Fraction or type(self.upper) is not Fraction:
            raise TypeError("internal interval endpoints must be exact Fractions")
        if self.lower > self.upper:
            raise ValueError("internal interval endpoints are reversed")


def _fraction_interval(value: Fraction) -> _Interval:
    if type(value) is not Fraction:
        raise TypeError("fraction interval input must be an exact Fraction")
    return _Interval(value, value)


def _add(left: _Interval, right: _Interval) -> _Interval:
    return _Interval(left.lower + right.lower, left.upper + right.upper)


def _subtract(left: _Interval, right: _Interval) -> _Interval:
    return _Interval(left.lower - right.upper, left.upper - right.lower)


def _multiply(left: _Interval, right: _Interval) -> _Interval:
    if left.lower < 0 or right.lower < 0:
        raise ValueError("the frozen interval product accepts nonnegative inputs only")
    return _Interval(left.lower * right.lower, left.upper * right.upper)


def _divide_positive(numerator: _Interval, denominator: _Interval) -> _Interval:
    if numerator.lower < 0 or denominator.lower <= 0:
        raise ValueError("the frozen interval quotient requires a positive denominator")
    return _Interval(
        numerator.lower / denominator.upper,
        numerator.upper / denominator.lower,
    )


def _sum(values: Tuple[_Interval, ...]) -> _Interval:
    if type(values) is not tuple or not values:
        raise TypeError("interval summation requires a nonempty exact tuple")
    result = _fraction_interval(_ZERO)
    for value in values:
        if type(value) is not _Interval:
            raise TypeError("interval summation entries have the wrong type")
        result = _add(result, value)
    return result


def _sqrt_fraction(value: Fraction) -> _Interval:
    if type(value) is not Fraction:
        raise TypeError("square-root input must be an exact Fraction")
    if value < 0:
        raise ValueError("square-root input must be nonnegative")
    scaled_numerator = value.numerator << (2 * CP53_TEST28_RATIONAL_ENCLOSURE_BITS)
    root = math.isqrt(scaled_numerator // value.denominator)
    lower = Fraction(root, _ENCLOSURE_DENOMINATOR)
    if root * root * value.denominator == scaled_numerator:
        upper = lower
    else:
        upper = Fraction(root + 1, _ENCLOSURE_DENOMINATOR)
    return _Interval(lower, upper)


def _exp_fraction(value: Fraction) -> _Interval:
    if type(value) is not Fraction:
        raise TypeError("exponential input must be an exact Fraction")
    if value > 0 or value < -1:
        raise ValueError("the frozen exponential enclosure supports [-1, 0]")
    if value == 0:
        return _fraction_interval(_ONE)
    magnitude = -value
    term = _ONE
    partial = _ONE
    lower = _ZERO
    upper = _ONE
    for index in range(1, 4097):
        term = term * magnitude / index
        if index & 1:
            partial -= term
            lower = partial
        else:
            partial += term
            upper = partial
        if upper - lower <= _ENCLOSURE_TARGET_WIDTH:
            return _Interval(lower, upper)
    raise ArithmeticError("alternating exponential enclosure exceeded its term cap")


def _absolute(value: _Interval) -> _Interval:
    zero = _ZERO
    if value.lower <= zero <= value.upper:
        lower = zero
    elif value.lower > zero:
        lower = value.lower
    else:
        lower = -value.upper
    upper = max(abs(value.lower), abs(value.upper))
    return _Interval(lower, upper)


def _nonnegative_difference(left: _Interval, right: _Interval) -> _Interval:
    result = _subtract(left, right)
    if result.upper < 0:
        raise ArithmeticError("a mathematically nonnegative interval is negative")
    return _Interval(max(_ZERO, result.lower), result.upper)


def _sqrt_interval(value: _Interval) -> _Interval:
    if value.lower < 0:
        raise ValueError("square-root interval must be nonnegative")
    return _Interval(
        _sqrt_fraction(value.lower).lower,
        _sqrt_fraction(value.upper).upper,
    )


def _dyadic_floor(value: Fraction) -> Fraction:
    numerator = (value.numerator << CP53_TEST28_RATIONAL_ENCLOSURE_BITS) // (
        value.denominator
    )
    return Fraction(numerator, _ENCLOSURE_DENOMINATOR)


def _dyadic_ceiling(value: Fraction) -> Fraction:
    return -_dyadic_floor(-value)


def _multiply_rounded(left: _Interval, right: _Interval) -> _Interval:
    if left.lower < 0 or right.lower < 0:
        raise ValueError("rounded interval multiplication requires nonnegative inputs")
    return _Interval(
        _dyadic_floor(left.lower * right.lower),
        _dyadic_ceiling(left.upper * right.upper),
    )


def _power_nonnegative(value: _Interval, exponent: int) -> _Interval:
    if value.lower < 0:
        raise ValueError("integer-power interval must be nonnegative")
    if type(exponent) is not int or isinstance(exponent, bool) or exponent < 0:
        raise TypeError("integer-power exponent must be nonnegative exact integer")
    result = _fraction_interval(_ONE)
    factor = value
    remaining = exponent
    while remaining:
        if remaining & 1:
            result = _multiply_rounded(result, factor)
        remaining >>= 1
        if remaining:
            factor = _multiply_rounded(factor, factor)
    return result


def _intersects(left: _Interval, right: _Interval) -> bool:
    return left.lower <= right.upper and right.lower <= left.upper


class _NonPickleRecord:
    def __reduce__(self) -> object:
        raise TypeError(type(self).__name__ + " is intentionally non-pickleable")

    def __reduce_ex__(self, protocol: object) -> object:
        del protocol
        raise TypeError(type(self).__name__ + " is intentionally non-pickleable")


@dataclass(frozen=True)
class ClosedRationalInterval(_NonPickleRecord):
    """A closed enclosure with authoritative exact-rational endpoints."""

    lower: Fraction
    upper: Fraction
    enclosure_bits: int

    def __post_init__(self) -> None:
        lower = _require_fraction(self.lower, name="interval lower endpoint")
        upper = _require_fraction(self.upper, name="interval upper endpoint")
        if lower > upper:
            raise ValueError("interval endpoints are reversed")
        if type(self.enclosure_bits) is not int or isinstance(
            self.enclosure_bits, bool
        ):
            raise TypeError("enclosure_bits must be an exact integer")
        if self.enclosure_bits != CP53_TEST28_RATIONAL_ENCLOSURE_BITS:
            raise ValueError("enclosure_bits differs from the frozen policy")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ClosedRationalInterval cannot be subclassed")


@dataclass(frozen=True)
class EndpointQualifiedRationalInterval(_NonPickleRecord):
    """A rational interval whose open/closed endpoints are explicit."""

    lower: Fraction
    upper: Fraction
    lower_inclusive: bool
    upper_inclusive: bool
    enclosure_bits: int

    def __post_init__(self) -> None:
        lower = _require_fraction(self.lower, name="qualified lower endpoint")
        upper = _require_fraction(self.upper, name="qualified upper endpoint")
        if lower > upper:
            raise ValueError("qualified interval endpoints are reversed")
        if (
            type(self.lower_inclusive) is not bool
            or type(self.upper_inclusive) is not bool
        ):
            raise TypeError("endpoint-inclusion fields must be exact booleans")
        if lower == upper and not (self.lower_inclusive and self.upper_inclusive):
            raise ValueError("an open singleton interval is empty")
        if type(self.enclosure_bits) is not int or isinstance(
            self.enclosure_bits, bool
        ):
            raise TypeError("enclosure_bits must be an exact integer")
        if self.enclosure_bits != CP53_TEST28_RATIONAL_ENCLOSURE_BITS:
            raise ValueError("enclosure_bits differs from the frozen policy")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("EndpointQualifiedRationalInterval cannot be subclassed")


def _publish(value: _Interval) -> ClosedRationalInterval:
    return ClosedRationalInterval(
        lower=value.lower,
        upper=value.upper,
        enclosure_bits=CP53_TEST28_RATIONAL_ENCLOSURE_BITS,
    )


def _publish_qualified(
    lower: Fraction,
    upper: Fraction,
    *,
    lower_inclusive: bool,
    upper_inclusive: bool,
) -> EndpointQualifiedRationalInterval:
    return EndpointQualifiedRationalInterval(
        lower=lower,
        upper=upper,
        lower_inclusive=lower_inclusive,
        upper_inclusive=upper_inclusive,
        enclosure_bits=CP53_TEST28_RATIONAL_ENCLOSURE_BITS,
    )


def _private_qualified(value: EndpointQualifiedRationalInterval) -> _Interval:
    if type(value) is not EndpointQualifiedRationalInterval:
        raise TypeError("qualified interval record has the wrong exact type")
    value.__post_init__()
    return _Interval(value.lower, value.upper)


def _private(value: ClosedRationalInterval) -> _Interval:
    if type(value) is not ClosedRationalInterval:
        raise TypeError("interval record has the wrong exact type")
    value.__post_init__()
    return _Interval(value.lower, value.upper)


def _exact_tuple(value: object, *, name: str, length: int) -> Tuple[object, ...]:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if len(value) != length:
        raise ValueError(name + " has the wrong length")
    return value


def _require_interval(value: object, *, name: str) -> ClosedRationalInterval:
    if type(value) is not ClosedRationalInterval:
        raise TypeError(name + " has the wrong exact type")
    value.__post_init__()
    return value


def _require_fraction(value: object, *, name: str, positive: bool = False) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError(name + " must be an exact Fraction")
    if (
        value.numerator.bit_length() > MAX_CP53_TEST28_EXACT_INTEGER_BITS
        or value.denominator.bit_length() > MAX_CP53_TEST28_EXACT_INTEGER_BITS
    ):
        raise ArithmeticError(name + " exceeds the frozen exact-integer resource bound")
    if positive and value <= 0:
        raise ValueError(name + " must be positive")
    return value


def _require_bounded_text(
    value: object,
    *,
    name: str,
    maximum_length: int,
) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if not value or len(value) > maximum_length:
        raise ValueError(name + " must be bounded nonempty text")
    return value


@dataclass(frozen=True)
class ProbabilityTablePrediction(_NonPickleRecord):
    """One finite marginal table under an analytic reference layer."""

    table_id: str
    labels: Tuple[str, ...]
    unnormalized_masses: Tuple[ClosedRationalInterval, ...]
    normalizer: ClosedRationalInterval
    probabilities: Tuple[ClosedRationalInterval, ...]

    def __post_init__(self) -> None:
        if (
            type(self.table_id) is not str
            or not self.table_id
            or len(self.table_id) > 96
        ):
            raise ValueError("table_id must be bounded nonempty exact text")
        if type(self.labels) is not tuple or not 1 <= len(self.labels) <= 16:
            raise ValueError("labels must be a bounded nonempty exact tuple")
        if any(type(label) is not str for label in self.labels):
            raise TypeError("table labels must be exact strings")
        if any(not label or len(label) > 96 for label in self.labels):
            raise ValueError("table labels must be bounded nonempty strings")
        if len(set(self.labels)) != len(self.labels):
            raise ValueError("table labels must be unique")
        masses = _exact_tuple(
            self.unnormalized_masses,
            name="unnormalized_masses",
            length=len(self.labels),
        )
        probabilities = _exact_tuple(
            self.probabilities,
            name="probabilities",
            length=len(self.labels),
        )
        for index, value in enumerate(masses):
            interval = _private(
                _require_interval(value, name="unnormalized_masses[%d]" % index)
            )
            if interval.lower < 0:
                raise ValueError("table masses must be nonnegative")
        normalizer = _private(_require_interval(self.normalizer, name="normalizer"))
        if normalizer.lower <= 0:
            raise ValueError("table normalizer must be strictly positive")
        probability_intervals = []
        for index, value in enumerate(probabilities):
            interval = _private(
                _require_interval(value, name="probabilities[%d]" % index)
            )
            if interval.lower < 0 or interval.upper > 1:
                raise ValueError("table probabilities must lie in [0, 1]")
            probability_intervals.append(interval)
        total = _sum(tuple(probability_intervals))
        if not total.lower <= 1 <= total.upper:
            raise ValueError("probability intervals do not enclose normalization")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ProbabilityTablePrediction cannot be subclassed")


@dataclass(frozen=True)
class AnalyticReferencePrediction(_NonPickleRecord):
    """Predictions for one fixture under one analytic reference layer."""

    fixture_id: str
    reference_layer: str
    activity: Fraction
    type_weights: Tuple[Fraction, Fraction]
    total_cap: int
    score_upper_bound: Fraction
    normalizer: ClosedRationalInterval
    ideal_rejection_acceptance_probability: ClosedRationalInterval
    second_weight_moment: ClosedRationalInterval
    weight_variance: ClosedRationalInterval
    exact_iid_sir_tv_coefficient: ClosedRationalInterval
    exact_iid_sir_bound_statement: str
    category_table: ProbabilityTablePrediction
    count_table: Optional[ProbabilityTablePrediction]
    event_type_table: Optional[ProbabilityTablePrediction]
    formula_id: str
    normalizer_formula_id: str
    second_weight_moment_formula_id: str
    ideal_gaussian_fibers_retained: bool
    operational_sampler_law_verified: bool
    runtime_sampler_imported: bool
    source_or_rng_law_verified: bool
    represented_measure_identified: bool
    exact_iid_sir_premises_verified: bool
    confirmatory_evidence: bool
    manuscript_claim: bool

    def __post_init__(self) -> None:
        fixture_id = _require_bounded_text(
            self.fixture_id, name="fixture_id", maximum_length=128
        )
        reference_layer = _require_bounded_text(
            self.reference_layer, name="reference_layer", maximum_length=64
        )
        bound_statement = _require_bounded_text(
            self.exact_iid_sir_bound_statement,
            name="exact_iid_sir_bound_statement",
            maximum_length=1024,
        )
        formula_id = _require_bounded_text(
            self.formula_id, name="formula_id", maximum_length=256
        )
        normalizer_formula_id = _require_bounded_text(
            self.normalizer_formula_id,
            name="normalizer_formula_id",
            maximum_length=512,
        )
        second_formula_id = _require_bounded_text(
            self.second_weight_moment_formula_id,
            name="second_weight_moment_formula_id",
            maximum_length=512,
        )
        if fixture_id not in _ALLOWED_FIXTURES:
            raise ValueError("prediction fixture_id is invalid")
        if reference_layer not in _ALLOWED_LAYERS:
            raise ValueError("prediction reference_layer is invalid")
        _require_fraction(self.activity, name="activity", positive=True)
        weights = _exact_tuple(self.type_weights, name="type_weights", length=2)
        if any(
            _require_fraction(value, name="type weight", positive=True) <= 0
            for value in weights
        ):
            raise ValueError("type weights must be positive")
        if sum(weights, _ZERO) != _ONE:
            raise ValueError("type weights must sum exactly to one")
        expected_parameters = (
            (_IDEAL_ACTIVITY, _IDEAL_WEIGHTS)
            if self.reference_layer == "ideal_rational"
            else (_BINARY64_ACTIVITY, _BINARY64_WEIGHTS)
        )
        if (self.activity, self.type_weights) != expected_parameters:
            raise ValueError("analytic reference parameters differ")
        if type(self.total_cap) is not int or isinstance(self.total_cap, bool):
            raise TypeError("total_cap must be an exact integer")
        expected_cap = 1 if self.fixture_id == "T28-M1-Q" else 2
        if self.total_cap != expected_cap:
            raise ValueError("prediction cap differs")
        if _require_fraction(self.score_upper_bound, name="score_upper_bound") != _ZERO:
            raise ValueError("prediction score upper bound must be exact zero")
        normalizer = _private(_require_interval(self.normalizer, name="normalizer"))
        acceptance = _private(
            _require_interval(
                self.ideal_rejection_acceptance_probability,
                name="ideal_rejection_acceptance_probability",
            )
        )
        if normalizer != acceptance:
            raise ValueError("U=0 analytic acceptance must equal the normalizer")
        second_moment = _private(
            _require_interval(self.second_weight_moment, name="second_weight_moment")
        )
        if second_moment.lower <= 0 or second_moment.upper > 1:
            raise ValueError("second weight moment must lie in (0, 1]")
        variance = _private(
            _require_interval(self.weight_variance, name="weight_variance")
        )
        expected_variance = _nonnegative_difference(
            second_moment,
            _multiply(normalizer, normalizer),
        )
        if variance != expected_variance:
            raise ValueError("weight variance interval differs")
        coefficient = _private(
            _require_interval(
                self.exact_iid_sir_tv_coefficient,
                name="exact_iid_sir_tv_coefficient",
            )
        )
        expected_coefficient = _divide_positive(
            _sqrt_interval(variance),
            _multiply(_fraction_interval(_TWO), normalizer),
        )
        if coefficient != expected_coefficient:
            raise ValueError("exact-IID SIR TV coefficient differs")
        if bound_statement != CP53_TEST28_EXACT_IID_SIR_BOUND_STATEMENT:
            raise ValueError("exact-IID SIR theorem statement differs")
        if type(self.category_table) is not ProbabilityTablePrediction:
            raise TypeError("category_table has the wrong exact type")
        self.category_table.__post_init__()
        if _private(self.category_table.normalizer) != normalizer:
            raise ValueError("category-table normalizer differs")
        if self.fixture_id == "T28-M1-Q":
            if self.count_table is not None or self.event_type_table is not None:
                raise ValueError("M1 must not duplicate count or event-type tables")
            expected_formula = "t28-m1-q-capped-poisson-gaussian-integral-v1"
            expected_normalizer_formula = "m1-z=p0+p1*(w0+w1*sqrt(2/3))-v1"
            expected_second_formula = "m1-ew2=p0+p1*(w0+w1*sqrt(1/2))-v1"
        else:
            if type(self.count_table) is not ProbabilityTablePrediction:
                raise TypeError("M2 count_table has the wrong exact type")
            if type(self.event_type_table) is not ProbabilityTablePrediction:
                raise TypeError("M2 event_type_table has the wrong exact type")
            self.count_table.__post_init__()
            self.event_type_table.__post_init__()
            if _private(self.count_table.normalizer) != normalizer:
                raise ValueError("M2 count-table normalizer differs")
            expected_formula = "t28-m2-q-capped-poisson-gaussian-integral-v1"
            expected_normalizer_formula = (
                "m2-z=p0+p1*m+p2*exp(-1/4)*m^2;" "m=w0*sqrt(2/3)+w1*sqrt(3/5)-v1"
            )
            expected_second_formula = (
                "m2-ew2=p0+p1*m2+p2*exp(-1/2)*m2^2;" "m2=w0*sqrt(1/2)+w1*sqrt(2/5)-v1"
            )
        if formula_id != expected_formula:
            raise ValueError("prediction formula_id differs")
        if normalizer_formula_id != expected_normalizer_formula:
            raise ValueError("normalizer formula_id differs")
        if second_formula_id != expected_second_formula:
            raise ValueError("second-moment formula_id differs")
        if self.ideal_gaussian_fibers_retained is not True:
            raise ValueError("analytic prediction must retain ideal Gaussian fibers")
        false_fields = (
            self.operational_sampler_law_verified,
            self.runtime_sampler_imported,
            self.source_or_rng_law_verified,
            self.represented_measure_identified,
            self.exact_iid_sir_premises_verified,
            self.confirmatory_evidence,
            self.manuscript_claim,
        )
        if any(value is not False for value in false_fields):
            raise ValueError(
                "analytic prediction contains a forbidden operational claim"
            )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("AnalyticReferencePrediction cannot be subclassed")


@dataclass(frozen=True)
class FixtureAnalyticPredictions(_NonPickleRecord):
    """Paired ideal-rational and binary64-parameter fixture predictions."""

    schema_version: str
    fixture_id: str
    rational_interval_method: str
    rational_proof_statement: str
    ideal_rational: AnalyticReferencePrediction
    binary64_parameter: AnalyticReferencePrediction
    record_sha256: str

    def __post_init__(self) -> None:
        schema_version = _require_bounded_text(
            self.schema_version, name="schema_version", maximum_length=128
        )
        fixture_id = _require_bounded_text(
            self.fixture_id, name="fixture_id", maximum_length=128
        )
        interval_method = _require_bounded_text(
            self.rational_interval_method,
            name="rational_interval_method",
            maximum_length=1024,
        )
        proof_statement = _require_bounded_text(
            self.rational_proof_statement,
            name="rational_proof_statement",
            maximum_length=1024,
        )
        if schema_version != CP53_TEST28_PREDICTION_SCHEMA_VERSION:
            raise ValueError("prediction schema_version differs")
        if fixture_id not in _ALLOWED_FIXTURES:
            raise ValueError("paired prediction fixture_id is invalid")
        if interval_method != CP53_TEST28_RATIONAL_INTERVAL_METHOD:
            raise ValueError("paired prediction rational_interval_method differs")
        if proof_statement != CP53_TEST28_RATIONAL_PROOF_STATEMENT:
            raise ValueError("paired prediction rational_proof_statement differs")
        for layer_name, value in (
            ("ideal_rational", self.ideal_rational),
            ("binary64_parameter", self.binary64_parameter),
        ):
            if type(value) is not AnalyticReferencePrediction:
                raise TypeError(layer_name + " has the wrong exact type")
            value.__post_init__()
            if (
                value.fixture_id != self.fixture_id
                or value.reference_layer != layer_name
            ):
                raise ValueError("paired prediction layer binding differs")
        _require_sha256(self.record_sha256, name="record_sha256")
        if self.record_sha256 != _prediction_digest(self):
            raise ValueError("paired prediction digest differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("FixtureAnalyticPredictions cannot be subclassed")


@dataclass(frozen=True)
class IntervalDifference(_NonPickleRecord):
    """Binary64-parameter minus ideal-rational interval difference."""

    label: str
    signed_difference: ClosedRationalInterval
    absolute_difference: ClosedRationalInterval

    def __post_init__(self) -> None:
        if type(self.label) is not str or not self.label or len(self.label) > 128:
            raise ValueError("difference label must be bounded nonempty exact text")
        signed = _private(
            _require_interval(self.signed_difference, name="signed_difference")
        )
        absolute = _private(
            _require_interval(self.absolute_difference, name="absolute_difference")
        )
        expected = _absolute(signed)
        if absolute != expected:
            raise ValueError("absolute difference does not follow from signed interval")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("IntervalDifference cannot be subclassed")


@dataclass(frozen=True)
class ProbabilityTablePerturbation(_NonPickleRecord):
    """Finite-table perturbation from ideal-rational to binary64 parameters."""

    table_id: str
    probability_differences: Tuple[IntervalDifference, ...]
    total_variation_distance: ClosedRationalInterval

    def __post_init__(self) -> None:
        if (
            type(self.table_id) is not str
            or not self.table_id
            or len(self.table_id) > 96
        ):
            raise ValueError("perturbation table_id must be bounded nonempty text")
        if type(self.probability_differences) is not tuple:
            raise TypeError("probability_differences must be an exact tuple")
        if not 1 <= len(self.probability_differences) <= 16:
            raise ValueError("probability_differences exceeds the frozen bound")
        labels = []
        absolute_intervals = []
        for value in self.probability_differences:
            if type(value) is not IntervalDifference:
                raise TypeError("probability difference has the wrong exact type")
            value.__post_init__()
            labels.append(value.label)
            absolute_intervals.append(_private(value.absolute_difference))
        if len(set(labels)) != len(labels):
            raise ValueError("probability-difference labels must be unique")
        expected = _multiply(_sum(tuple(absolute_intervals)), _fraction_interval(_HALF))
        actual = _private(
            _require_interval(
                self.total_variation_distance,
                name="total_variation_distance",
            )
        )
        if actual != expected:
            raise ValueError("finite-table TV interval differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ProbabilityTablePerturbation cannot be subclassed")


@dataclass(frozen=True)
class FixtureParameterPerturbation(_NonPickleRecord):
    """Exact parameter and outward analytic perturbations for one fixture."""

    schema_version: str
    fixture_id: str
    binary64_minus_ideal_activity: Fraction
    binary64_minus_ideal_type_weights: Tuple[Fraction, Fraction]
    exact_type_weight_l1_distance: Fraction
    exact_type_weight_total_variation_distance: Fraction
    exact_reference_parameter_epsilon: Fraction
    exact_proposal_measure_total_variation_distance: Fraction
    proposal_tv_formula_id: str
    normalizer_difference: IntervalDifference
    normalizer_relative_absolute_difference: ClosedRationalInterval
    table_perturbations: Tuple[ProbabilityTablePerturbation, ...]
    analytic_target_law_total_variation_distance: ClosedRationalInterval
    analytic_target_tv_equals_configuration_category_tv: bool
    analytic_target_tv_identity_statement: str
    analytic_references_only: bool
    operational_sampler_perturbation_bounded: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    record_sha256: str

    def __post_init__(self) -> None:
        schema_version = _require_bounded_text(
            self.schema_version, name="schema_version", maximum_length=128
        )
        fixture_id = _require_bounded_text(
            self.fixture_id, name="fixture_id", maximum_length=128
        )
        proposal_formula_id = _require_bounded_text(
            self.proposal_tv_formula_id,
            name="proposal_tv_formula_id",
            maximum_length=256,
        )
        target_tv_statement = _require_bounded_text(
            self.analytic_target_tv_identity_statement,
            name="analytic_target_tv_identity_statement",
            maximum_length=1024,
        )
        if schema_version != CP53_TEST28_PREDICTION_SCHEMA_VERSION:
            raise ValueError("perturbation schema_version differs")
        if fixture_id not in _ALLOWED_FIXTURES:
            raise ValueError("perturbation fixture_id is invalid")
        activity_delta = _require_fraction(
            self.binary64_minus_ideal_activity,
            name="binary64_minus_ideal_activity",
        )
        weight_deltas = _exact_tuple(
            self.binary64_minus_ideal_type_weights,
            name="binary64_minus_ideal_type_weights",
            length=2,
        )
        if any(type(value) is not Fraction for value in weight_deltas):
            raise TypeError("type-weight deltas must be exact Fractions")
        for index, value in enumerate(weight_deltas):
            _require_fraction(value, name="type-weight delta[%d]" % index)
        expected_activity = _BINARY64_ACTIVITY - _IDEAL_ACTIVITY
        expected_weights = tuple(
            binary - ideal for binary, ideal in zip(_BINARY64_WEIGHTS, _IDEAL_WEIGHTS)
        )
        if activity_delta != expected_activity or weight_deltas != expected_weights:
            raise ValueError("exact parameter deltas differ")
        expected_l1 = sum((abs(value) for value in expected_weights), _ZERO)
        if (
            _require_fraction(
                self.exact_type_weight_l1_distance,
                name="exact_type_weight_l1_distance",
            )
            != expected_l1
        ):
            raise ValueError("exact type-weight L1 distance differs")
        if (
            _require_fraction(
                self.exact_type_weight_total_variation_distance,
                name="exact_type_weight_total_variation_distance",
            )
            != expected_l1 / 2
        ):
            raise ValueError("exact type-weight TV distance differs")
        epsilon = _require_fraction(
            self.exact_reference_parameter_epsilon,
            name="exact_reference_parameter_epsilon",
            positive=True,
        )
        if epsilon != expected_weights[0] or expected_weights[1] != -epsilon:
            raise ValueError("reference-parameter epsilon differs")
        if self.fixture_id == "T28-M1-Q":
            expected_proposal_tv = epsilon / 2
            expected_proposal_formula = "m1-proposal-tv-epsilon-over-2-v1"
        else:
            expected_proposal_tv = (
                Fraction(16, 25) * epsilon - Fraction(1, 5) * epsilon * epsilon
            )
            expected_proposal_formula = (
                "m2-proposal-tv-16-epsilon-over-25-minus-" "epsilon-squared-over-5-v1"
            )
        if (
            _require_fraction(
                self.exact_proposal_measure_total_variation_distance,
                name="exact_proposal_measure_total_variation_distance",
            )
            != expected_proposal_tv
        ):
            raise ValueError("exact analytic proposal-measure TV differs")
        if proposal_formula_id != expected_proposal_formula:
            raise ValueError("analytic proposal-TV formula_id differs")
        if type(self.normalizer_difference) is not IntervalDifference:
            raise TypeError("normalizer_difference has the wrong exact type")
        self.normalizer_difference.__post_init__()
        relative = _private(
            _require_interval(
                self.normalizer_relative_absolute_difference,
                name="normalizer_relative_absolute_difference",
            )
        )
        if relative.lower < 0:
            raise ValueError("relative normalizer difference must be nonnegative")
        if type(self.table_perturbations) is not tuple:
            raise TypeError("table_perturbations must be an exact tuple")
        expected_count = 1 if self.fixture_id == "T28-M1-Q" else 3
        if len(self.table_perturbations) != expected_count:
            raise ValueError("table_perturbations has the wrong bounded length")
        for table in self.table_perturbations:
            if type(table) is not ProbabilityTablePerturbation:
                raise TypeError("table perturbation has the wrong exact type")
            table.__post_init__()
        expected_ids = (
            ("configuration-category",)
            if self.fixture_id == "T28-M1-Q"
            else ("configuration-category", "count", "event-type")
        )
        if tuple(table.table_id for table in self.table_perturbations) != expected_ids:
            raise ValueError("perturbation table order differs")
        target_tv = _private(
            _require_interval(
                self.analytic_target_law_total_variation_distance,
                name="analytic_target_law_total_variation_distance",
            )
        )
        category_tv = _private(self.table_perturbations[0].total_variation_distance)
        if target_tv != category_tv:
            raise ValueError("full analytic target-law TV differs from category TV")
        if self.analytic_target_tv_equals_configuration_category_tv is not True:
            raise ValueError("analytic target/category TV identity flag differs")
        if target_tv_statement != (
            "the configuration categories are disjoint and their conditional "
            "selected-fiber laws are identical under Pi_N^rat and Pi_N^b64; "
            "therefore full analytic target TV equals configuration-category TV"
        ):
            raise ValueError("analytic target/category TV identity statement differs")
        if self.analytic_references_only is not True:
            raise ValueError("perturbation must be marked analytic-only")
        if any(
            value is not False
            for value in (
                self.operational_sampler_perturbation_bounded,
                self.confirmatory_evidence,
                self.manuscript_claim,
            )
        ):
            raise ValueError("perturbation contains a forbidden operational claim")
        _require_sha256(self.record_sha256, name="record_sha256")
        if self.record_sha256 != _perturbation_digest(self):
            raise ValueError("perturbation digest differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("FixtureParameterPerturbation cannot be subclassed")


def _conditional_uint64_components(
    normalizer: _Interval,
    attempts: int,
) -> Tuple[_Interval, _Interval, _Interval]:
    epsilon = _fraction_interval(Fraction(1, 1 << 64))
    alpha_lower = normalizer.lower - epsilon.upper
    alpha_upper = normalizer.upper
    if alpha_lower <= 0:
        raise ValueError("the alpha64 positive-lower-bound precondition fails")
    if alpha_upper > 1:
        raise ValueError("the U=0 normalizer upper bound exceeds one")
    alpha = _Interval(alpha_lower, alpha_upper)
    exhaustion_lower_base = _ONE - alpha_upper
    exhaustion_upper_base = _ONE - alpha_lower
    exhaustion_lower = _power_nonnegative(
        _Interval(exhaustion_lower_base, exhaustion_lower_base), attempts
    ).lower
    exhaustion_upper = _power_nonnegative(
        _Interval(exhaustion_upper_base, exhaustion_upper_base), attempts
    ).upper
    exhaustion = _Interval(exhaustion_lower, exhaustion_upper)
    beta_lower = _Interval(normalizer.lower, normalizer.lower)
    total_variation = _Interval(
        _ZERO,
        _divide_positive(epsilon, beta_lower).upper,
    )
    return alpha, exhaustion, total_variation


@dataclass(frozen=True)
class ConditionalUint64RejectionBounds(_NonPickleRecord):
    """Generic floor-quantization bounds under explicitly unmet law premises."""

    schema_version: str
    fixture_id: str
    reference_layer: str
    analytic_prediction_record_sha256: str
    attempts: int
    quantization_unit: Fraction
    analytic_normalizer: ClosedRationalInterval
    alpha64_bound: EndpointQualifiedRationalInterval
    exhaustion_probability_bound: EndpointQualifiedRationalInterval
    selected_total_variation_bound: EndpointQualifiedRationalInterval
    bound_statement: str
    alpha64_positive_precondition_met: bool
    conditional_theorem_derived: bool
    iid_proposals_verified: bool
    independent_uniform_uint64_words_verified: bool
    operational_mu_fp_identified: bool
    numerical_mu_fp_prediction: bool
    operational_predictions_satisfied: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    record_sha256: str

    def __post_init__(self) -> None:
        schema_version = _require_bounded_text(
            self.schema_version, name="schema_version", maximum_length=128
        )
        fixture_id = _require_bounded_text(
            self.fixture_id, name="fixture_id", maximum_length=128
        )
        reference_layer = _require_bounded_text(
            self.reference_layer, name="reference_layer", maximum_length=64
        )
        bound_statement = _require_bounded_text(
            self.bound_statement, name="bound_statement", maximum_length=2048
        )
        if schema_version != CP53_TEST28_PREDICTION_SCHEMA_VERSION:
            raise ValueError("conditional-bound schema_version differs")
        if fixture_id not in _ALLOWED_FIXTURES:
            raise ValueError("conditional-bound fixture_id is invalid")
        if reference_layer not in _ALLOWED_LAYERS:
            raise ValueError("conditional-bound reference_layer is invalid")
        _require_sha256(
            self.analytic_prediction_record_sha256,
            name="analytic_prediction_record_sha256",
        )
        if type(self.attempts) is not int or isinstance(self.attempts, bool):
            raise TypeError("attempts must be an exact non-boolean integer")
        if not 1 <= self.attempts <= MAX_CP53_TEST28_REJECTION_ATTEMPTS:
            raise ValueError("attempts lies outside the frozen resource bound")
        if _require_fraction(
            self.quantization_unit, name="quantization_unit", positive=True
        ) != Fraction(1, 1 << 64):
            raise ValueError("uint64 quantization unit differs")
        normalizer = _private(
            _require_interval(self.analytic_normalizer, name="analytic_normalizer")
        )
        (
            expected_alpha,
            expected_exhaustion,
            expected_tv,
        ) = _conditional_uint64_components(normalizer, self.attempts)
        alpha = _private_qualified(self.alpha64_bound)
        if alpha != expected_alpha or not (
            not self.alpha64_bound.lower_inclusive
            and self.alpha64_bound.upper_inclusive
        ):
            raise ValueError("alpha64 strict endpoint contract differs")
        exhaustion = _private_qualified(self.exhaustion_probability_bound)
        if exhaustion != expected_exhaustion or not (
            self.exhaustion_probability_bound.lower_inclusive
            and not self.exhaustion_probability_bound.upper_inclusive
        ):
            raise ValueError("exhaustion strict endpoint contract differs")
        selected_tv = _private_qualified(self.selected_total_variation_bound)
        if selected_tv != expected_tv or not (
            self.selected_total_variation_bound.lower_inclusive
            and not self.selected_total_variation_bound.upper_inclusive
        ):
            raise ValueError("selected-TV strict endpoint contract differs")
        if bound_statement != CP53_TEST28_CONDITIONAL_UINT64_BOUND_STATEMENT:
            raise ValueError("conditional uint64 theorem statement differs")
        if self.alpha64_positive_precondition_met is not True:
            raise ValueError("positive alpha64 precondition must be explicitly met")
        if self.conditional_theorem_derived is not True:
            raise ValueError("the conditional theorem derivation flag differs")
        if any(
            value is not False
            for value in (
                self.iid_proposals_verified,
                self.independent_uniform_uint64_words_verified,
                self.operational_mu_fp_identified,
                self.numerical_mu_fp_prediction,
                self.operational_predictions_satisfied,
                self.confirmatory_evidence,
                self.manuscript_claim,
            )
        ):
            raise ValueError("conditional bound contains a forbidden operational claim")
        _require_sha256(self.record_sha256, name="record_sha256")
        if self.record_sha256 != _conditional_uint64_digest(self):
            raise ValueError("conditional uint64 bound digest differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ConditionalUint64RejectionBounds cannot be subclassed")


def _conditional_exact_iid_sir_component(
    coefficient: _Interval,
    particles: int,
) -> _Interval:
    if coefficient.lower < 0:
        raise ValueError("SIR TV coefficient must be nonnegative")
    square_root_particles = _sqrt_fraction(Fraction(particles, 1))
    return _Interval(
        _ZERO,
        coefficient.upper / square_root_particles.lower,
    )


@dataclass(frozen=True)
class ConditionalExactIIDSIRBounds(_NonPickleRecord):
    """Finite-J exact-IID SIR theorem bound with unmet operational premises."""

    schema_version: str
    fixture_id: str
    reference_layer: str
    analytic_prediction_record_sha256: str
    particles: int
    sir_tv_coefficient: ClosedRationalInterval
    marginal_total_variation_bound: EndpointQualifiedRationalInterval
    formula_id: str
    bound_statement: str
    conditional_theorem_derived: bool
    iid_analytic_proposals_verified: bool
    operational_exact_weights_verified: bool
    exact_categorical_resampling_verified: bool
    operational_mu_fp_identified: bool
    exact_finite_j_distribution_derived: bool
    operational_predictions_satisfied: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    record_sha256: str

    def __post_init__(self) -> None:
        schema_version = _require_bounded_text(
            self.schema_version, name="schema_version", maximum_length=128
        )
        fixture_id = _require_bounded_text(
            self.fixture_id, name="fixture_id", maximum_length=128
        )
        reference_layer = _require_bounded_text(
            self.reference_layer, name="reference_layer", maximum_length=64
        )
        formula_id = _require_bounded_text(
            self.formula_id, name="formula_id", maximum_length=256
        )
        bound_statement = _require_bounded_text(
            self.bound_statement, name="bound_statement", maximum_length=2048
        )
        if schema_version != CP53_TEST28_PREDICTION_SCHEMA_VERSION:
            raise ValueError("conditional-SIR schema_version differs")
        if fixture_id not in _ALLOWED_FIXTURES:
            raise ValueError("conditional-SIR fixture_id is invalid")
        if reference_layer not in _ALLOWED_LAYERS:
            raise ValueError("conditional-SIR reference_layer is invalid")
        _require_sha256(
            self.analytic_prediction_record_sha256,
            name="analytic_prediction_record_sha256",
        )
        if type(self.particles) is not int or isinstance(self.particles, bool):
            raise TypeError("particles must be an exact non-boolean integer")
        if not 1 <= self.particles <= MAX_CP53_TEST28_SIR_PARTICLES:
            raise ValueError("particles lies outside the frozen resource bound")
        coefficient = _private(
            _require_interval(self.sir_tv_coefficient, name="sir_tv_coefficient")
        )
        expected = _conditional_exact_iid_sir_component(
            coefficient,
            self.particles,
        )
        actual = _private_qualified(self.marginal_total_variation_bound)
        if actual != expected or not (
            self.marginal_total_variation_bound.lower_inclusive
            and self.marginal_total_variation_bound.upper_inclusive
        ):
            raise ValueError("conditional exact-IID SIR TV endpoint contract differs")
        if formula_id != "exact-iid-sir-tv-coefficient-over-sqrt-j-v1":
            raise ValueError("conditional-SIR formula_id differs")
        if bound_statement != CP53_TEST28_CONDITIONAL_EXACT_IID_SIR_BOUND_STATEMENT:
            raise ValueError("conditional-SIR theorem statement differs")
        if self.conditional_theorem_derived is not True:
            raise ValueError("conditional-SIR theorem derivation flag differs")
        if any(
            value is not False
            for value in (
                self.iid_analytic_proposals_verified,
                self.operational_exact_weights_verified,
                self.exact_categorical_resampling_verified,
                self.operational_mu_fp_identified,
                self.exact_finite_j_distribution_derived,
                self.operational_predictions_satisfied,
                self.confirmatory_evidence,
                self.manuscript_claim,
            )
        ):
            raise ValueError("conditional-SIR bound contains an operational claim")
        _require_sha256(self.record_sha256, name="record_sha256")
        if self.record_sha256 != _conditional_exact_iid_sir_digest(self):
            raise ValueError("conditional exact-IID SIR bound digest differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ConditionalExactIIDSIRBounds cannot be subclassed")


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(name + " must be lowercase SHA-256 text")
    return value


def _canonical(value: object) -> object:
    if value is None:
        return ["none-v1"]
    if type(value) is bool:
        return ["bool-v1", value]
    if type(value) is int:
        return ["integer-v1", str(value)]
    if type(value) is str:
        return ["string-v1", value]
    if type(value) is Fraction:
        return ["fraction-v1", str(value.numerator), str(value.denominator)]
    if type(value) is tuple:
        return ["tuple-v1", [_canonical(item) for item in value]]
    if is_dataclass(value) and not isinstance(value, type):
        return [
            "record-v1",
            type(value).__name__,
            [
                [field.name, _canonical(getattr(value, field.name))]
                for field in fields(value)
                if field.name != "record_sha256"
            ],
        ]
    raise TypeError("unsupported canonical value " + type(value).__name__)


def _digest(value: object, *, kind: str) -> str:
    payload = {
        "domain": _DIGEST_DOMAIN,
        "kind": kind,
        "payload": _canonical(value),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _prediction_digest(value: FixtureAnalyticPredictions) -> str:
    return _digest(value, kind="fixture-analytic-predictions")


def _perturbation_digest(value: FixtureParameterPerturbation) -> str:
    return _digest(value, kind="fixture-parameter-perturbation")


def _conditional_uint64_digest(value: ConditionalUint64RejectionBounds) -> str:
    return _digest(value, kind="conditional-uint64-rejection-bounds")


def _conditional_exact_iid_sir_digest(value: ConditionalExactIIDSIRBounds) -> str:
    return _digest(value, kind="conditional-exact-iid-sir-bounds")


def _make_table(
    table_id: str,
    labels: Tuple[str, ...],
    masses: Tuple[_Interval, ...],
    normalizer: Optional[_Interval] = None,
) -> ProbabilityTablePrediction:
    denominator = _sum(masses) if normalizer is None else normalizer
    probabilities = tuple(_divide_positive(mass, denominator) for mass in masses)
    return ProbabilityTablePrediction(
        table_id=table_id,
        labels=labels,
        unnormalized_masses=tuple(_publish(value) for value in masses),
        normalizer=_publish(denominator),
        probabilities=tuple(_publish(value) for value in probabilities),
    )


def _count_probabilities(activity: Fraction, cap: int) -> Tuple[_Interval, ...]:
    theta = _fraction_interval(activity)
    terms = [_fraction_interval(_ONE)]
    if cap >= 1:
        terms.append(theta)
    if cap >= 2:
        terms.append(
            _multiply(_multiply(theta, theta), _fraction_interval(Fraction(1, 2)))
        )
    denominator = _sum(tuple(terms))
    return tuple(_divide_positive(term, denominator) for term in terms)


def _layer_parameters(layer: str) -> Tuple[Fraction, Tuple[Fraction, Fraction]]:
    if layer == "ideal_rational":
        return _IDEAL_ACTIVITY, _IDEAL_WEIGHTS
    if layer == "binary64_parameter":
        return _BINARY64_ACTIVITY, _BINARY64_WEIGHTS
    raise ValueError("unknown analytic reference layer")


def _weight_moment_intervals(
    normalizer: _Interval,
    second_moment: _Interval,
) -> Tuple[_Interval, _Interval]:
    variance = _nonnegative_difference(
        second_moment,
        _multiply(normalizer, normalizer),
    )
    coefficient = _divide_positive(
        _sqrt_interval(variance),
        _multiply(_fraction_interval(_TWO), normalizer),
    )
    return variance, coefficient


def _m1_layer(layer: str) -> AnalyticReferencePrediction:
    activity, exact_weights = _layer_parameters(layer)
    count_zero, count_one = _count_probabilities(activity, 1)
    weight_zero, weight_one = tuple(
        _fraction_interval(value) for value in exact_weights
    )
    integrated_continuous = _sqrt_fraction(Fraction(2, 3))
    masses = (
        count_zero,
        _multiply(count_one, weight_zero),
        _multiply(_multiply(count_one, weight_one), integrated_continuous),
    )
    normalizer = _sum(masses)
    second_moment = _sum(
        (
            count_zero,
            _multiply(count_one, weight_zero),
            _multiply(
                _multiply(count_one, weight_one),
                _sqrt_fraction(Fraction(1, 2)),
            ),
        )
    )
    variance, sir_coefficient = _weight_moment_intervals(
        normalizer,
        second_moment,
    )
    category = _make_table(
        "configuration-category",
        ("empty", "atomic-a", "continuous-b"),
        masses,
        normalizer,
    )
    return AnalyticReferencePrediction(
        fixture_id="T28-M1-Q",
        reference_layer=layer,
        activity=activity,
        type_weights=exact_weights,
        total_cap=1,
        score_upper_bound=_ZERO,
        normalizer=_publish(normalizer),
        ideal_rejection_acceptance_probability=_publish(normalizer),
        second_weight_moment=_publish(second_moment),
        weight_variance=_publish(variance),
        exact_iid_sir_tv_coefficient=_publish(sir_coefficient),
        exact_iid_sir_bound_statement=CP53_TEST28_EXACT_IID_SIR_BOUND_STATEMENT,
        category_table=category,
        count_table=None,
        event_type_table=None,
        formula_id="t28-m1-q-capped-poisson-gaussian-integral-v1",
        normalizer_formula_id="m1-z=p0+p1*(w0+w1*sqrt(2/3))-v1",
        second_weight_moment_formula_id=("m1-ew2=p0+p1*(w0+w1*sqrt(1/2))-v1"),
        ideal_gaussian_fibers_retained=True,
        operational_sampler_law_verified=False,
        runtime_sampler_imported=False,
        source_or_rng_law_verified=False,
        represented_measure_identified=False,
        exact_iid_sir_premises_verified=False,
        confirmatory_evidence=False,
        manuscript_claim=False,
    )


def _m2_layer(layer: str) -> AnalyticReferencePrediction:
    activity, exact_weights = _layer_parameters(layer)
    count_zero, count_one, count_two = _count_probabilities(activity, 2)
    weight_zero, weight_one = tuple(
        _fraction_interval(value) for value in exact_weights
    )
    integrated_zero = _sqrt_fraction(Fraction(2, 3))
    integrated_one = _sqrt_fraction(Fraction(3, 5))
    count_two_factor = _exp_fraction(Fraction(-1, 4))
    tilted_zero = _multiply(weight_zero, integrated_zero)
    tilted_one = _multiply(weight_one, integrated_one)
    mean_tilt = _add(tilted_zero, tilted_one)
    category_masses = (
        count_zero,
        _multiply(count_one, tilted_zero),
        _multiply(count_one, tilted_one),
        _multiply(
            _multiply(_multiply(count_two, count_two_factor), tilted_zero),
            tilted_zero,
        ),
        _multiply(
            _multiply(
                _multiply(
                    _multiply(count_two, count_two_factor),
                    _fraction_interval(_TWO),
                ),
                tilted_zero,
            ),
            tilted_one,
        ),
        _multiply(
            _multiply(_multiply(count_two, count_two_factor), tilted_one),
            tilted_one,
        ),
    )
    normalizer = _sum(category_masses)
    second_tilted_zero = _multiply(
        weight_zero,
        _sqrt_fraction(Fraction(1, 2)),
    )
    second_tilted_one = _multiply(
        weight_one,
        _sqrt_fraction(Fraction(2, 5)),
    )
    second_mean_tilt = _add(second_tilted_zero, second_tilted_one)
    second_count_two_factor = _exp_fraction(Fraction(-1, 2))
    second_moment = _sum(
        (
            count_zero,
            _multiply(count_one, second_mean_tilt),
            _multiply(
                _multiply(
                    _multiply(count_two, second_count_two_factor),
                    second_mean_tilt,
                ),
                second_mean_tilt,
            ),
        )
    )
    variance, sir_coefficient = _weight_moment_intervals(
        normalizer,
        second_moment,
    )
    category_table = _make_table(
        "configuration-category",
        (
            "empty",
            "one-type-1d",
            "one-type-2d",
            "two-type-1d",
            "one-each",
            "two-type-2d",
        ),
        category_masses,
        normalizer,
    )
    count_masses = (
        count_zero,
        _multiply(count_one, mean_tilt),
        _multiply(
            _multiply(_multiply(count_two, count_two_factor), mean_tilt),
            mean_tilt,
        ),
    )
    if not _intersects(_sum(count_masses), normalizer):
        raise ArithmeticError("independent M2 count/category normalizers disagree")
    count_table = _make_table(
        "count",
        ("count-0", "count-1", "count-2"),
        count_masses,
        normalizer,
    )
    event_type_table = _make_table(
        "event-type",
        ("type-1d", "type-2d"),
        (tilted_zero, tilted_one),
        mean_tilt,
    )
    return AnalyticReferencePrediction(
        fixture_id="T28-M2-Q",
        reference_layer=layer,
        activity=activity,
        type_weights=exact_weights,
        total_cap=2,
        score_upper_bound=_ZERO,
        normalizer=_publish(normalizer),
        ideal_rejection_acceptance_probability=_publish(normalizer),
        second_weight_moment=_publish(second_moment),
        weight_variance=_publish(variance),
        exact_iid_sir_tv_coefficient=_publish(sir_coefficient),
        exact_iid_sir_bound_statement=CP53_TEST28_EXACT_IID_SIR_BOUND_STATEMENT,
        category_table=category_table,
        count_table=count_table,
        event_type_table=event_type_table,
        formula_id="t28-m2-q-capped-poisson-gaussian-integral-v1",
        normalizer_formula_id=(
            "m2-z=p0+p1*m+p2*exp(-1/4)*m^2;" "m=w0*sqrt(2/3)+w1*sqrt(3/5)-v1"
        ),
        second_weight_moment_formula_id=(
            "m2-ew2=p0+p1*m2+p2*exp(-1/2)*m2^2;" "m2=w0*sqrt(1/2)+w1*sqrt(2/5)-v1"
        ),
        ideal_gaussian_fibers_retained=True,
        operational_sampler_law_verified=False,
        runtime_sampler_imported=False,
        source_or_rng_law_verified=False,
        represented_measure_identified=False,
        exact_iid_sir_premises_verified=False,
        confirmatory_evidence=False,
        manuscript_claim=False,
    )


def _make_prediction_pair(
    fixture_id: str,
    ideal: AnalyticReferencePrediction,
    binary64: AnalyticReferencePrediction,
) -> FixtureAnalyticPredictions:
    provisional = FixtureAnalyticPredictions.__new__(FixtureAnalyticPredictions)
    values = {
        "schema_version": CP53_TEST28_PREDICTION_SCHEMA_VERSION,
        "fixture_id": fixture_id,
        "rational_interval_method": CP53_TEST28_RATIONAL_INTERVAL_METHOD,
        "rational_proof_statement": CP53_TEST28_RATIONAL_PROOF_STATEMENT,
        "ideal_rational": ideal,
        "binary64_parameter": binary64,
        "record_sha256": "0" * 64,
    }
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    values["record_sha256"] = _prediction_digest(provisional)
    return FixtureAnalyticPredictions(**values)


def t28_m1_analytic_predictions() -> FixtureAnalyticPredictions:
    """Return paired analytic predictions for ``T28-M1-Q``."""

    return _make_prediction_pair(
        "T28-M1-Q",
        _m1_layer("ideal_rational"),
        _m1_layer("binary64_parameter"),
    )


def t28_m2_analytic_predictions() -> FixtureAnalyticPredictions:
    """Return paired analytic predictions for ``T28-M2-Q``."""

    return _make_prediction_pair(
        "T28-M2-Q",
        _m2_layer("ideal_rational"),
        _m2_layer("binary64_parameter"),
    )


def validate_t28_analytic_reference_prediction(
    value: object,
) -> AnalyticReferencePrediction:
    """Fail closed at the trust boundary for a single analytic layer record."""

    if type(value) is not AnalyticReferencePrediction:
        raise TypeError("analytic reference prediction has the wrong exact type")
    value.__post_init__()
    pair = (
        t28_m1_analytic_predictions()
        if value.fixture_id == "T28-M1-Q"
        else t28_m2_analytic_predictions()
    )
    expected = (
        pair.ideal_rational
        if value.reference_layer == "ideal_rational"
        else pair.binary64_parameter
    )
    if value != expected:
        raise ValueError("analytic layer differs from the canonical derivation")
    return value


def conditional_uint64_rejection_bounds(
    prediction: object,
    attempts: object,
) -> ConditionalUint64RejectionBounds:
    """Derive generic conditional floor-quantization bounds.

    ``prediction`` supplies an analytic normalizer, not ``mu_fp``.  The result
    records a valid mathematical implication while leaving every operational
    proposal/source premise false.
    """

    layer = validate_t28_analytic_reference_prediction(prediction)
    if type(attempts) is not int or isinstance(attempts, bool):
        raise TypeError("attempts must be an exact non-boolean integer")
    if not 1 <= attempts <= MAX_CP53_TEST28_REJECTION_ATTEMPTS:
        raise ValueError("attempts lies outside the frozen resource bound")
    pair = (
        t28_m1_analytic_predictions()
        if layer.fixture_id == "T28-M1-Q"
        else t28_m2_analytic_predictions()
    )
    normalizer = _private(layer.normalizer)
    alpha, exhaustion, total_variation = _conditional_uint64_components(
        normalizer,
        attempts,
    )
    values = {
        "schema_version": CP53_TEST28_PREDICTION_SCHEMA_VERSION,
        "fixture_id": layer.fixture_id,
        "reference_layer": layer.reference_layer,
        "analytic_prediction_record_sha256": pair.record_sha256,
        "attempts": attempts,
        "quantization_unit": Fraction(1, 1 << 64),
        "analytic_normalizer": layer.normalizer,
        "alpha64_bound": _publish_qualified(
            alpha.lower,
            alpha.upper,
            lower_inclusive=False,
            upper_inclusive=True,
        ),
        "exhaustion_probability_bound": _publish_qualified(
            exhaustion.lower,
            exhaustion.upper,
            lower_inclusive=True,
            upper_inclusive=False,
        ),
        "selected_total_variation_bound": _publish_qualified(
            total_variation.lower,
            total_variation.upper,
            lower_inclusive=True,
            upper_inclusive=False,
        ),
        "bound_statement": CP53_TEST28_CONDITIONAL_UINT64_BOUND_STATEMENT,
        "alpha64_positive_precondition_met": True,
        "conditional_theorem_derived": True,
        "iid_proposals_verified": False,
        "independent_uniform_uint64_words_verified": False,
        "operational_mu_fp_identified": False,
        "numerical_mu_fp_prediction": False,
        "operational_predictions_satisfied": False,
        "confirmatory_evidence": False,
        "manuscript_claim": False,
        "record_sha256": "0" * 64,
    }
    provisional = ConditionalUint64RejectionBounds.__new__(
        ConditionalUint64RejectionBounds
    )
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    values["record_sha256"] = _conditional_uint64_digest(provisional)
    return ConditionalUint64RejectionBounds(**values)


def conditional_exact_iid_sir_bounds(
    prediction: object,
    particles: object,
) -> ConditionalExactIIDSIRBounds:
    """Enclose the finite-J exact-IID SIR theorem bound.

    The returned interval is a conditional analytic implication.  It is not an
    exact finite-J marginal, and every operational premise remains false.
    """

    layer = validate_t28_analytic_reference_prediction(prediction)
    if type(particles) is not int or isinstance(particles, bool):
        raise TypeError("particles must be an exact non-boolean integer")
    if not 1 <= particles <= MAX_CP53_TEST28_SIR_PARTICLES:
        raise ValueError("particles lies outside the frozen resource bound")
    pair = (
        t28_m1_analytic_predictions()
        if layer.fixture_id == "T28-M1-Q"
        else t28_m2_analytic_predictions()
    )
    bound = _conditional_exact_iid_sir_component(
        _private(layer.exact_iid_sir_tv_coefficient),
        particles,
    )
    values = {
        "schema_version": CP53_TEST28_PREDICTION_SCHEMA_VERSION,
        "fixture_id": layer.fixture_id,
        "reference_layer": layer.reference_layer,
        "analytic_prediction_record_sha256": pair.record_sha256,
        "particles": particles,
        "sir_tv_coefficient": layer.exact_iid_sir_tv_coefficient,
        "marginal_total_variation_bound": _publish_qualified(
            bound.lower,
            bound.upper,
            lower_inclusive=True,
            upper_inclusive=True,
        ),
        "formula_id": "exact-iid-sir-tv-coefficient-over-sqrt-j-v1",
        "bound_statement": CP53_TEST28_CONDITIONAL_EXACT_IID_SIR_BOUND_STATEMENT,
        "conditional_theorem_derived": True,
        "iid_analytic_proposals_verified": False,
        "operational_exact_weights_verified": False,
        "exact_categorical_resampling_verified": False,
        "operational_mu_fp_identified": False,
        "exact_finite_j_distribution_derived": False,
        "operational_predictions_satisfied": False,
        "confirmatory_evidence": False,
        "manuscript_claim": False,
        "record_sha256": "0" * 64,
    }
    provisional = ConditionalExactIIDSIRBounds.__new__(ConditionalExactIIDSIRBounds)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    values["record_sha256"] = _conditional_exact_iid_sir_digest(provisional)
    return ConditionalExactIIDSIRBounds(**values)


def _difference(
    label: str, binary64: _Interval, ideal: _Interval
) -> IntervalDifference:
    signed = _subtract(binary64, ideal)
    return IntervalDifference(
        label=label,
        signed_difference=_publish(signed),
        absolute_difference=_publish(_absolute(signed)),
    )


def _table_perturbation(
    ideal: ProbabilityTablePrediction,
    binary64: ProbabilityTablePrediction,
) -> ProbabilityTablePerturbation:
    if ideal.table_id != binary64.table_id or ideal.labels != binary64.labels:
        raise ValueError("analytic table layers do not align")
    differences = tuple(
        _difference(label, _private(right), _private(left))
        for label, left, right in zip(
            ideal.labels,
            ideal.probabilities,
            binary64.probabilities,
        )
    )
    total_variation = _multiply(
        _sum(tuple(_private(value.absolute_difference) for value in differences)),
        _fraction_interval(_HALF),
    )
    return ProbabilityTablePerturbation(
        table_id=ideal.table_id,
        probability_differences=differences,
        total_variation_distance=_publish(total_variation),
    )


def _make_perturbation(
    predictions: FixtureAnalyticPredictions,
) -> FixtureParameterPerturbation:
    validated = validate_t28_analytic_predictions(predictions)
    ideal = validated.ideal_rational
    binary64 = validated.binary64_parameter
    normalizer_difference = _difference(
        "target-normalizer",
        _private(binary64.normalizer),
        _private(ideal.normalizer),
    )
    relative = _divide_positive(
        _private(normalizer_difference.absolute_difference),
        _private(ideal.normalizer),
    )
    tables = [
        _table_perturbation(ideal.category_table, binary64.category_table),
    ]
    if ideal.count_table is not None and binary64.count_table is not None:
        tables.append(_table_perturbation(ideal.count_table, binary64.count_table))
    if ideal.event_type_table is not None and binary64.event_type_table is not None:
        tables.append(
            _table_perturbation(ideal.event_type_table, binary64.event_type_table)
        )
    weight_deltas = tuple(
        binary - rational for binary, rational in zip(_BINARY64_WEIGHTS, _IDEAL_WEIGHTS)
    )
    l1 = sum((abs(value) for value in weight_deltas), _ZERO)
    values = {
        "schema_version": CP53_TEST28_PREDICTION_SCHEMA_VERSION,
        "fixture_id": predictions.fixture_id,
        "binary64_minus_ideal_activity": _BINARY64_ACTIVITY - _IDEAL_ACTIVITY,
        "binary64_minus_ideal_type_weights": weight_deltas,
        "exact_type_weight_l1_distance": l1,
        "exact_type_weight_total_variation_distance": l1 / 2,
        "exact_reference_parameter_epsilon": weight_deltas[0],
        "exact_proposal_measure_total_variation_distance": (
            weight_deltas[0] / 2
            if predictions.fixture_id == "T28-M1-Q"
            else Fraction(16, 25) * weight_deltas[0]
            - Fraction(1, 5) * weight_deltas[0] * weight_deltas[0]
        ),
        "proposal_tv_formula_id": (
            "m1-proposal-tv-epsilon-over-2-v1"
            if predictions.fixture_id == "T28-M1-Q"
            else "m2-proposal-tv-16-epsilon-over-25-minus-" "epsilon-squared-over-5-v1"
        ),
        "normalizer_difference": normalizer_difference,
        "normalizer_relative_absolute_difference": _publish(relative),
        "table_perturbations": tuple(tables),
        "analytic_target_law_total_variation_distance": (
            tables[0].total_variation_distance
        ),
        "analytic_target_tv_equals_configuration_category_tv": True,
        "analytic_target_tv_identity_statement": (
            "the configuration categories are disjoint and their conditional "
            "selected-fiber laws are identical under Pi_N^rat and Pi_N^b64; "
            "therefore full analytic target TV equals configuration-category TV"
        ),
        "analytic_references_only": True,
        "operational_sampler_perturbation_bounded": False,
        "confirmatory_evidence": False,
        "manuscript_claim": False,
        "record_sha256": "0" * 64,
    }
    provisional = FixtureParameterPerturbation.__new__(FixtureParameterPerturbation)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    values["record_sha256"] = _perturbation_digest(provisional)
    return FixtureParameterPerturbation(**values)


def t28_m1_parameter_perturbation() -> FixtureParameterPerturbation:
    """Return analytic binary64-minus-rational perturbations for M1."""

    return _make_perturbation(t28_m1_analytic_predictions())


def t28_m2_parameter_perturbation() -> FixtureParameterPerturbation:
    """Return analytic binary64-minus-rational perturbations for M2."""

    return _make_perturbation(t28_m2_analytic_predictions())


def validate_t28_analytic_predictions(
    value: object,
) -> FixtureAnalyticPredictions:
    """Fail closed unless ``value`` exactly matches a canonical fresh derivation."""

    if type(value) is not FixtureAnalyticPredictions:
        raise TypeError("prediction record has the wrong exact type")
    value.__post_init__()
    expected = (
        t28_m1_analytic_predictions()
        if value.fixture_id == "T28-M1-Q"
        else t28_m2_analytic_predictions()
    )
    if value != expected:
        raise ValueError("prediction record differs from the canonical derivation")
    return value


def validate_t28_parameter_perturbation(
    value: object,
) -> FixtureParameterPerturbation:
    """Fail closed unless ``value`` exactly matches a canonical perturbation."""

    if type(value) is not FixtureParameterPerturbation:
        raise TypeError("perturbation record has the wrong exact type")
    value.__post_init__()
    expected = (
        t28_m1_parameter_perturbation()
        if value.fixture_id == "T28-M1-Q"
        else t28_m2_parameter_perturbation()
    )
    if value != expected:
        raise ValueError("perturbation record differs from the canonical derivation")
    return value


def validate_conditional_uint64_rejection_bounds(
    value: object,
) -> ConditionalUint64RejectionBounds:
    """Fail closed at the canonical conditional-bound trust boundary."""

    if type(value) is not ConditionalUint64RejectionBounds:
        raise TypeError("conditional uint64 bound has the wrong exact type")
    value.__post_init__()
    pair = (
        t28_m1_analytic_predictions()
        if value.fixture_id == "T28-M1-Q"
        else t28_m2_analytic_predictions()
    )
    layer = (
        pair.ideal_rational
        if value.reference_layer == "ideal_rational"
        else pair.binary64_parameter
    )
    expected = conditional_uint64_rejection_bounds(layer, value.attempts)
    if value != expected:
        raise ValueError("conditional uint64 bound differs from canonical derivation")
    return value


def validate_conditional_exact_iid_sir_bounds(
    value: object,
) -> ConditionalExactIIDSIRBounds:
    """Fail closed at the canonical conditional-SIR trust boundary."""

    if type(value) is not ConditionalExactIIDSIRBounds:
        raise TypeError("conditional exact-IID SIR bound has the wrong exact type")
    value.__post_init__()
    pair = (
        t28_m1_analytic_predictions()
        if value.fixture_id == "T28-M1-Q"
        else t28_m2_analytic_predictions()
    )
    layer = (
        pair.ideal_rational
        if value.reference_layer == "ideal_rational"
        else pair.binary64_parameter
    )
    expected = conditional_exact_iid_sir_bounds(layer, value.particles)
    if value != expected:
        raise ValueError(
            "conditional exact-IID SIR bound differs from canonical derivation"
        )
    return value


__all__ = (
    "CP53_TEST28_RATIONAL_ENCLOSURE_BITS",
    "CP53_TEST28_RATIONAL_INTERVAL_METHOD",
    "CP53_TEST28_RATIONAL_PROOF_STATEMENT",
    "CP53_TEST28_CONDITIONAL_EXACT_IID_SIR_BOUND_STATEMENT",
    "CP53_TEST28_CONDITIONAL_UINT64_BOUND_STATEMENT",
    "CP53_TEST28_EXACT_IID_SIR_BOUND_STATEMENT",
    "CP53_TEST28_PREDICTION_NONCLAIMS",
    "CP53_TEST28_PREDICTION_SCHEMA_VERSION",
    "CP53_TEST28_PREDICTION_SCOPE",
    "AnalyticReferencePrediction",
    "ClosedRationalInterval",
    "ConditionalExactIIDSIRBounds",
    "ConditionalUint64RejectionBounds",
    "EndpointQualifiedRationalInterval",
    "FixtureAnalyticPredictions",
    "FixtureParameterPerturbation",
    "IntervalDifference",
    "ProbabilityTablePerturbation",
    "ProbabilityTablePrediction",
    "MAX_CP53_TEST28_EXACT_INTEGER_BITS",
    "MAX_CP53_TEST28_REJECTION_ATTEMPTS",
    "MAX_CP53_TEST28_SIR_PARTICLES",
    "conditional_exact_iid_sir_bounds",
    "conditional_uint64_rejection_bounds",
    "t28_m1_analytic_predictions",
    "t28_m1_parameter_perturbation",
    "t28_m2_analytic_predictions",
    "t28_m2_parameter_perturbation",
    "validate_t28_analytic_predictions",
    "validate_t28_analytic_reference_prediction",
    "validate_t28_parameter_perturbation",
    "validate_conditional_uint64_rejection_bounds",
    "validate_conditional_exact_iid_sir_bounds",
)
