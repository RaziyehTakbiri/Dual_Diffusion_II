"""Exact direct-score atomic oracle for the Test-28 A0-Q fixture.

This stdlib-only development artifact freezes a new direct rational score
table on the six-state cap-two atomic support.  The scores are deliberately
*not* logarithms of the rational factors in T28-A0-H.  Exact base masses are
reconstructed from activity, type weights, count vectors, and multiplicity
factorials; no base or target mass vector is accepted as input.

The analytic oracle uses an alternating rational Taylor enclosure of
``s=exp(-1/2)``.  Direct target masses use powers and reciprocals of ``s``;
an independent shifted route uses ``exp(q-U)`` with ``U=1``.  Paired records
separate ideal-rational from exact stored-binary64 parameter values.  They do
not identify a runtime source law, integrate with the score-provider facade
or initializer kernel, authorize Test 28, or establish a manuscript result.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, fields, is_dataclass
from fractions import Fraction
from typing import Tuple


CP55_TEST28_ATOMIC_Q_SCHEMA_VERSION = "cp55-test28-atomic-direct-q-oracle-v1"
CP55_TEST28_ATOMIC_Q_FIXTURE_ID = "T28-A0-Q"
CP55_TEST28_ATOMIC_Q_FORMULA_ID = "atomic-direct-exact-rational-score-table-v1"
CP55_TEST28_ATOMIC_Q_INTERVAL_METHOD = (
    "exact-fraction-alternating-taylor-exp-minus-half;"
    "positive-powers-reciprocals-and-interval-intersection-v1"
)
CP55_TEST28_ATOMIC_Q_SCOPE = (
    "sealed-count-keyed-exact-score-table-provider;paired-ideal-rational-and-"
    "stored-binary64-parameter-analytic-base-layers;exact-factorial-base-"
    "reconstruction;direct-and-upper-shifted-rational-interval-target-routes;"
    "binary64-minus-ideal-perturbation;not-a0-h-logarithms;not-facade-or-"
    "kernel-integrated;not-runtime-law;not-confirmatory;not-manuscript"
)
CP55_TEST28_ATOMIC_Q_NONCLAIMS = (
    "the direct rational q table is a new design and is not log of the T28-A0-H factors",
    "the stored-binary64 layer binds exact parameter values, not floating-point execution",
    "the analytic layers are not identified with mu_fp or an operational sampler law",
    "the score-provider facade and initializer kernel are not integrated by this artifact",
    "no RNG, IID, categorical-transform, confirmatory, Test-28, or manuscript claim is made",
)

MAX_CP55_EXACT_INTEGER_BITS = 32768
MAX_CP55_TEXT_LENGTH = 2048
MAX_CP55_TAYLOR_TERMS = 4096
_DIGEST_DOMAIN = CP55_TEST28_ATOMIC_Q_SCHEMA_VERSION
_ONE = Fraction(1, 1)
_ZERO = Fraction(0, 1)
_HALF = Fraction(1, 2)
_ACTIVITY = _ONE
_CAP = 2
_TYPE_LABELS = ("a", "b")
_EVENT_DIMENSIONS = (0, 0)
_IDEAL_WEIGHTS = (Fraction(2, 5), Fraction(3, 5))
_B64_WEIGHTS = (
    Fraction(3602879701896397, 1 << 53),
    Fraction(5404319552844595, 1 << 53),
)
_SUPPORT_LABELS = ("empty", "a", "b", "aa", "ab", "bb")
_COUNT_VECTORS = ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2))
_RUNTIME_COUNT_VECTORS = ((0, 0), (0, 1), (1, 0), (0, 2), (1, 1), (2, 0))
_RUNTIME_TO_PROTOCOL = (0, 2, 1, 5, 4, 3)
_SCORES = (_ZERO, _HALF, -_HALF, _ONE, _HALF, -_ONE)
_LOWER_SCORE = -_ONE
_UPPER_SCORE = _ONE
_PRECISION_SCHEDULE = (64, 128, 192, 256)
_LAYERS = ("ideal_rational", "binary64_parameter")
_EXACT_BASE_PROPOSAL_TV = Fraction(
    144115188075855871,
    10141204801825835211973625643008000,
)


class _SealedRecord:
    def __reduce__(self) -> object:
        raise TypeError(type(self).__name__ + " is intentionally non-pickleable")

    def __reduce_ex__(self, protocol: object) -> object:
        del protocol
        raise TypeError(type(self).__name__ + " is intentionally non-pickleable")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if cls.__bases__ != (_SealedRecord,):
            raise TypeError(cls.__name__ + " cannot be subclassed")


def _text(value: object, name: str, maximum: int = MAX_CP55_TEXT_LENGTH) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if not value or len(value) > maximum:
        raise ValueError(name + " has invalid bounded length")
    if any(ord(character) < 32 or ord(character) > 126 for character in value):
        raise ValueError(name + " must contain printable ASCII only")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact non-boolean integer")
    if value < minimum or value > maximum:
        raise ValueError(name + " is outside its frozen bound")
    return value


def _fraction(value: object, name: str) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError(name + " must be an exact Fraction")
    if (
        max(value.numerator.bit_length(), value.denominator.bit_length())
        > MAX_CP55_EXACT_INTEGER_BITS
    ):
        raise ValueError(name + " exceeds the exact-integer bit bound")
    return value


def _exact_tuple(value: object, name: str, length: int) -> tuple:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if len(value) != length:
        raise ValueError(name + " has the wrong frozen length")
    return value


def _sha(value: object, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(name + " must be lowercase SHA-256 text")
    return value


def _canonical(value: object) -> object:
    if type(value) is bool:
        return ["bool-v1", value]
    if type(value) is int:
        return ["integer-hex-v1", ("-" + hex(-value)) if value < 0 else hex(value)]
    if type(value) is str:
        return ["string-v1", value]
    if type(value) is Fraction:
        numerator = (
            ("-" + hex(-value.numerator))
            if value.numerator < 0
            else hex(value.numerator)
        )
        return ["fraction-hex-v1", numerator, hex(value.denominator)]
    if type(value) is tuple:
        return ["tuple-v1", [_canonical(item) for item in value]]
    if is_dataclass(value) and not isinstance(value, type):
        if type(value).__module__ != __name__:
            raise TypeError("unsupported canonical record")
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


def _digest(kind: str, value: object) -> str:
    document = {
        "domain": _DIGEST_DOMAIN,
        "kind": _text(kind, "digest kind", 128),
        "payload": _canonical(value),
    }
    encoded = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class ClosedRationalInterval(_SealedRecord):
    lower: Fraction
    upper: Fraction

    def __post_init__(self) -> None:
        lower = _fraction(self.lower, "interval lower")
        upper = _fraction(self.upper, "interval upper")
        if lower > upper:
            raise ValueError("interval endpoints are reversed")

    @property
    def width(self) -> Fraction:
        return self.upper - self.lower


def _point(value: Fraction) -> ClosedRationalInterval:
    return ClosedRationalInterval(value, value)


def _add(
    left: ClosedRationalInterval, right: ClosedRationalInterval
) -> ClosedRationalInterval:
    return ClosedRationalInterval(left.lower + right.lower, left.upper + right.upper)


def _sum(values: Tuple[ClosedRationalInterval, ...]) -> ClosedRationalInterval:
    result = _point(_ZERO)
    for value in values:
        if type(value) is not ClosedRationalInterval:
            raise TypeError("interval sum requires exact interval records")
        result = _add(result, value)
    return result


def _scale(value: ClosedRationalInterval, scalar: Fraction) -> ClosedRationalInterval:
    scalar = _fraction(scalar, "interval scale")
    if scalar < 0:
        return ClosedRationalInterval(value.upper * scalar, value.lower * scalar)
    return ClosedRationalInterval(value.lower * scalar, value.upper * scalar)


def _multiply_positive(
    left: ClosedRationalInterval, right: ClosedRationalInterval
) -> ClosedRationalInterval:
    if left.lower < 0 or right.lower < 0:
        raise ValueError("positive interval product received a negative endpoint")
    return ClosedRationalInterval(left.lower * right.lower, left.upper * right.upper)


def _power_positive(
    value: ClosedRationalInterval, exponent: int
) -> ClosedRationalInterval:
    exponent = _integer(exponent, "interval exponent", 0, 16)
    return ClosedRationalInterval(value.lower**exponent, value.upper**exponent)


def _reciprocal_positive(value: ClosedRationalInterval) -> ClosedRationalInterval:
    if value.lower <= 0:
        raise ValueError("interval reciprocal requires a positive lower endpoint")
    return ClosedRationalInterval(_ONE / value.upper, _ONE / value.lower)


def _divide_positive(
    numerator: ClosedRationalInterval, denominator: ClosedRationalInterval
) -> ClosedRationalInterval:
    return _multiply_positive(numerator, _reciprocal_positive(denominator))


def _difference(
    left: ClosedRationalInterval, right: ClosedRationalInterval
) -> ClosedRationalInterval:
    return ClosedRationalInterval(left.lower - right.upper, left.upper - right.lower)


def _absolute(value: ClosedRationalInterval) -> ClosedRationalInterval:
    if value.lower >= 0:
        return value
    if value.upper <= 0:
        return ClosedRationalInterval(-value.upper, -value.lower)
    return ClosedRationalInterval(_ZERO, max(-value.lower, value.upper))


def _intersect(
    left: ClosedRationalInterval, right: ClosedRationalInterval
) -> ClosedRationalInterval:
    lower = max(left.lower, right.lower)
    upper = min(left.upper, right.upper)
    if lower > upper:
        raise ArithmeticError("independent exact interval routes are disjoint")
    return ClosedRationalInterval(lower, upper)


def _exp_minus_half(bits: int) -> Tuple[ClosedRationalInterval, int]:
    bits = _integer(bits, "precision bits", 32, 1024)
    target = Fraction(1, 1 << bits)
    term = _ONE
    partial = _ONE
    upper = _ONE
    lower = _ZERO
    for index in range(1, MAX_CP55_TAYLOR_TERMS + 1):
        term *= _HALF / index
        if index % 2:
            partial -= term
            lower = partial
        else:
            partial += term
            upper = partial
        if index >= 2 and upper - lower <= target:
            return ClosedRationalInterval(lower, upper), index
    raise ArithmeticError("alternating Taylor enclosure exhausted its term bound")


@dataclass(frozen=True, slots=True)
class AtomicQScoreEvaluation(_SealedRecord):
    fixture_id: str
    protocol_index: int
    state_label: str
    count_vector: Tuple[int, int]
    exact_score: Fraction
    record_sha256: str

    def __post_init__(self) -> None:
        fixture_id = _text(self.fixture_id, "score evaluation fixture", 64)
        index = _integer(self.protocol_index, "protocol index", 0, 5)
        state_label = _text(self.state_label, "score evaluation state label", 32)
        count_vector = _exact_tuple(
            self.count_vector, "score evaluation count vector", 2
        )
        for item in count_vector:
            _integer(item, "score evaluation count", 0, 2)
        exact_score = _fraction(self.exact_score, "exact score")
        _sha(self.record_sha256, "score evaluation digest")
        if fixture_id != CP55_TEST28_ATOMIC_Q_FIXTURE_ID:
            raise ValueError("score evaluation fixture differs")
        if (
            state_label != _SUPPORT_LABELS[index]
            or count_vector != _COUNT_VECTORS[index]
        ):
            raise ValueError("score evaluation identity differs")
        if exact_score != _SCORES[index]:
            raise ValueError("score evaluation value differs")
        if self.record_sha256 != _digest("score-evaluation", self):
            raise ValueError("score evaluation digest differs")


@dataclass(frozen=True, slots=True)
class AtomicQScoreTableProvider(_SealedRecord):
    schema_version: str
    fixture_id: str
    state_labels: Tuple[str, ...]
    count_vectors: Tuple[Tuple[int, int], ...]
    exact_scores: Tuple[Fraction, ...]
    lower_score_bound: Fraction
    upper_score_bound: Fraction
    runtime_count_vectors: Tuple[Tuple[int, int], ...]
    runtime_to_protocol_permutation: Tuple[int, ...]
    count_keyed_lookup_required: bool
    a0_h_logarithm_claim: bool
    facade_integrated: bool
    kernel_integrated: bool
    record_sha256: str

    def __post_init__(self) -> None:
        schema_version = _text(self.schema_version, "score-table schema", 128)
        fixture_id = _text(self.fixture_id, "score-table fixture", 64)
        state_labels = _exact_tuple(self.state_labels, "score-table state labels", 6)
        for value in state_labels:
            _text(value, "score-table state label", 32)
        count_vectors = _exact_tuple(self.count_vectors, "score-table count vectors", 6)
        for vector in count_vectors:
            entries = _exact_tuple(vector, "score-table count vector", 2)
            for entry in entries:
                _integer(entry, "score-table count", 0, 2)
        exact_scores = _exact_tuple(self.exact_scores, "score-table scores", 6)
        for value in exact_scores:
            _fraction(value, "score-table score")
        lower = _fraction(self.lower_score_bound, "score lower bound")
        upper = _fraction(self.upper_score_bound, "score upper bound")
        runtime_vectors = _exact_tuple(
            self.runtime_count_vectors, "runtime count vectors", 6
        )
        for vector in runtime_vectors:
            entries = _exact_tuple(vector, "runtime count vector", 2)
            for entry in entries:
                _integer(entry, "runtime count", 0, 2)
        permutation = _exact_tuple(
            self.runtime_to_protocol_permutation, "runtime permutation", 6
        )
        for value in permutation:
            _integer(value, "runtime permutation entry", 0, 5)
        for name in (
            "count_keyed_lookup_required",
            "a0_h_logarithm_claim",
            "facade_integrated",
            "kernel_integrated",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(name + " must be bool")
        _sha(self.record_sha256, "score-table digest")
        if (
            schema_version != CP55_TEST28_ATOMIC_Q_SCHEMA_VERSION
            or fixture_id != CP55_TEST28_ATOMIC_Q_FIXTURE_ID
        ):
            raise ValueError("score-table identity differs")
        if (
            state_labels != _SUPPORT_LABELS
            or count_vectors != _COUNT_VECTORS
            or exact_scores != _SCORES
        ):
            raise ValueError("score-table contents differ")
        if lower != _LOWER_SCORE or upper != _UPPER_SCORE:
            raise ValueError("score-table bounds differ")
        if (
            runtime_vectors != _RUNTIME_COUNT_VECTORS
            or permutation != _RUNTIME_TO_PROTOCOL
        ):
            raise ValueError("runtime count-vector mapping differs")
        for name, value in (
            ("count_keyed_lookup_required", self.count_keyed_lookup_required),
        ):
            if type(value) is not bool or not value:
                raise ValueError(name + " must be true")
        for name, value in (
            ("a0_h_logarithm_claim", self.a0_h_logarithm_claim),
            ("facade_integrated", self.facade_integrated),
            ("kernel_integrated", self.kernel_integrated),
        ):
            if type(value) is not bool or value:
                raise ValueError(name + " must be false")
        if self.record_sha256 != _digest("score-table-provider", self):
            raise ValueError("score-table digest differs")

    def evaluate(self, count_vector: Tuple[int, int]) -> AtomicQScoreEvaluation:
        self.__post_init__()
        count_vector = _exact_tuple(count_vector, "count_vector", 2)
        for item in count_vector:
            _integer(item, "count_vector entry", 0, 2)
        try:
            index = self.count_vectors.index(count_vector)
        except ValueError as error:
            raise ValueError(
                "count_vector is outside the complete frozen support"
            ) from error
        payload = AtomicQScoreEvaluation.__new__(AtomicQScoreEvaluation)
        object.__setattr__(payload, "fixture_id", self.fixture_id)
        object.__setattr__(payload, "protocol_index", index)
        object.__setattr__(payload, "state_label", self.state_labels[index])
        object.__setattr__(payload, "count_vector", count_vector)
        object.__setattr__(payload, "exact_score", self.exact_scores[index])
        object.__setattr__(
            payload, "record_sha256", _digest("score-evaluation", payload)
        )
        payload.__post_init__()
        return payload

    def scores_in_runtime_order(self) -> Tuple[Fraction, ...]:
        self.__post_init__()
        return tuple(
            self.exact_scores[index] for index in self.runtime_to_protocol_permutation
        )


def _make_record(record_type: type, kind: str, **values: object) -> object:
    record = record_type.__new__(record_type)
    for name, value in values.items():
        object.__setattr__(record, name, value)
    object.__setattr__(record, "record_sha256", _digest(kind, record))
    record.__post_init__()
    return record


def _score_provider() -> AtomicQScoreTableProvider:
    return _make_record(
        AtomicQScoreTableProvider,
        "score-table-provider",
        schema_version=CP55_TEST28_ATOMIC_Q_SCHEMA_VERSION,
        fixture_id=CP55_TEST28_ATOMIC_Q_FIXTURE_ID,
        state_labels=_SUPPORT_LABELS,
        count_vectors=_COUNT_VECTORS,
        exact_scores=_SCORES,
        lower_score_bound=_LOWER_SCORE,
        upper_score_bound=_UPPER_SCORE,
        runtime_count_vectors=_RUNTIME_COUNT_VECTORS,
        runtime_to_protocol_permutation=_RUNTIME_TO_PROTOCOL,
        count_keyed_lookup_required=True,
        a0_h_logarithm_claim=False,
        facade_integrated=False,
        kernel_integrated=False,
    )


@dataclass(frozen=True, slots=True)
class AtomicQStateOracle(_SealedRecord):
    protocol_index: int
    state_label: str
    count_vector: Tuple[int, int]
    multiplicity_factorials: Tuple[int, int]
    raw_base_weight: Fraction
    normalized_base_mass: Fraction
    exact_score: Fraction
    exact_shifted_score: Fraction
    exp_score_interval: ClosedRationalInterval
    exp_shifted_score_interval: ClosedRationalInterval
    direct_target_mass_interval: ClosedRationalInterval
    shifted_target_mass_interval: ClosedRationalInterval
    target_probability_interval: ClosedRationalInterval
    record_sha256: str

    def __post_init__(self) -> None:
        index = _integer(self.protocol_index, "state protocol index", 0, 5)
        state_label = _text(self.state_label, "state label", 32)
        vector = _exact_tuple(self.count_vector, "state count vector", 2)
        for item in vector:
            _integer(item, "state count", 0, 2)
        factorials = _exact_tuple(
            self.multiplicity_factorials, "multiplicity factorials", 2
        )
        for item in factorials:
            _integer(item, "multiplicity factorial", 1, 2)
        raw_base = _fraction(self.raw_base_weight, "raw_base_weight")
        base_mass = _fraction(self.normalized_base_mass, "normalized_base_mass")
        score = _fraction(self.exact_score, "exact_score")
        shifted_score = _fraction(self.exact_shifted_score, "exact_shifted_score")
        if state_label != _SUPPORT_LABELS[index]:
            raise ValueError("state label differs")
        if vector != _COUNT_VECTORS[index]:
            raise ValueError("state count vector differs")
        if factorials != tuple(math.factorial(item) for item in vector):
            raise ValueError("multiplicity factorials differ")
        if raw_base <= 0 or base_mass != raw_base / Fraction(5, 2):
            raise ValueError(
                "state normalized base mass differs from raw factorial mass"
            )
        if score != _SCORES[index] or shifted_score != _SCORES[index] - _UPPER_SCORE:
            raise ValueError("state score differs")
        for name in (
            "exp_score_interval",
            "exp_shifted_score_interval",
            "direct_target_mass_interval",
            "shifted_target_mass_interval",
            "target_probability_interval",
        ):
            value = getattr(self, name)
            if type(value) is not ClosedRationalInterval:
                raise TypeError(name + " has the wrong exact type")
            value.__post_init__()
            if value.lower < 0:
                raise ValueError(name + " must be nonnegative")
        if self.target_probability_interval.upper > 1:
            raise ValueError("target probability interval exceeds one")
        s, unused_terms = _exp_minus_half(_PRECISION_SCHEDULE[-1])
        del unused_terms
        inverse = _reciprocal_positive(s)
        expected_exp = (
            _point(_ONE),
            inverse,
            s,
            _power_positive(inverse, 2),
            inverse,
            _power_positive(s, 2),
        )[index]
        expected_shifted = (
            _power_positive(s, 2),
            s,
            _power_positive(s, 3),
            _point(_ONE),
            s,
            _power_positive(s, 4),
        )[index]
        if (
            self.exp_score_interval != expected_exp
            or self.exp_shifted_score_interval != expected_shifted
        ):
            raise ValueError("state exponential interval differs")
        if self.direct_target_mass_interval != _scale(
            expected_exp, base_mass
        ) or self.shifted_target_mass_interval != _scale(expected_shifted, base_mass):
            raise ValueError("state target mass interval differs")
        if _sha(self.record_sha256, "state digest") != _digest("state-oracle", self):
            raise ValueError("state digest differs")


@dataclass(frozen=True, slots=True)
class AtomicQPrecisionStage(_SealedRecord):
    precision_bits: int
    taylor_terms: int
    exp_minus_half_interval: ClosedRationalInterval
    exp_score_intervals: Tuple[ClosedRationalInterval, ...]
    exp_shifted_score_intervals: Tuple[ClosedRationalInterval, ...]
    direct_target_mass_intervals: Tuple[ClosedRationalInterval, ...]
    shifted_target_mass_intervals: Tuple[ClosedRationalInterval, ...]
    direct_normalizer_interval: ClosedRationalInterval
    shifted_acceptance_interval: ClosedRationalInterval
    shifted_recovered_normalizer_interval: ClosedRationalInterval
    normalizer_interval: ClosedRationalInterval
    direct_probability_intervals: Tuple[ClosedRationalInterval, ...]
    shifted_probability_intervals: Tuple[ClosedRationalInterval, ...]
    probability_intervals: Tuple[ClosedRationalInterval, ...]
    probability_sum_interval: ClosedRationalInterval
    record_sha256: str

    def __post_init__(self) -> None:
        bits = _integer(self.precision_bits, "stage precision", 32, 1024)
        terms = _integer(
            self.taylor_terms, "stage Taylor terms", 1, MAX_CP55_TAYLOR_TERMS
        )
        if bits not in _PRECISION_SCHEDULE:
            raise ValueError("stage precision is outside the frozen schedule")
        if type(self.exp_minus_half_interval) is not ClosedRationalInterval:
            raise TypeError("exp-minus-half interval has the wrong type")
        self.exp_minus_half_interval.__post_init__()
        if (
            self.exp_minus_half_interval.lower <= 0
            or self.exp_minus_half_interval.upper >= 1
        ):
            raise ValueError("exp-minus-half interval is outside (0,1)")
        if self.exp_minus_half_interval.width > Fraction(1, 1 << bits):
            raise ValueError("exp-minus-half interval misses its precision target")
        tuple_names = (
            "exp_score_intervals",
            "exp_shifted_score_intervals",
            "direct_target_mass_intervals",
            "shifted_target_mass_intervals",
            "direct_probability_intervals",
            "shifted_probability_intervals",
            "probability_intervals",
        )
        for name in tuple_names:
            values = _exact_tuple(getattr(self, name), name, 6)
            for value in values:
                if type(value) is not ClosedRationalInterval:
                    raise TypeError(name + " must contain exact intervals")
                value.__post_init__()
                if value.lower < 0:
                    raise ValueError(name + " must contain nonnegative intervals")
        scalar_names = (
            "direct_normalizer_interval",
            "shifted_acceptance_interval",
            "shifted_recovered_normalizer_interval",
            "normalizer_interval",
            "probability_sum_interval",
        )
        for name in scalar_names:
            value = getattr(self, name)
            if type(value) is not ClosedRationalInterval:
                raise TypeError(name + " has the wrong exact type")
            value.__post_init__()
        if (
            self.normalizer_interval.lower <= 0
            or self.shifted_acceptance_interval.lower <= 0
        ):
            raise ValueError("stage normalizers must be positive")
        if not (
            self.probability_sum_interval.lower
            <= 1
            <= self.probability_sum_interval.upper
        ):
            raise ValueError("probability intervals do not enclose normalization")
        expected_s, expected_terms = _exp_minus_half(bits)
        inverse = _reciprocal_positive(expected_s)
        expected_exp = (
            _point(_ONE),
            inverse,
            expected_s,
            _power_positive(inverse, 2),
            inverse,
            _power_positive(expected_s, 2),
        )
        expected_shifted = (
            _power_positive(expected_s, 2),
            expected_s,
            _power_positive(expected_s, 3),
            _point(_ONE),
            expected_s,
            _power_positive(expected_s, 4),
        )
        if self.exp_minus_half_interval != expected_s or terms != expected_terms:
            raise ValueError("alternating Taylor stage differs")
        if (
            self.exp_score_intervals != expected_exp
            or self.exp_shifted_score_intervals != expected_shifted
        ):
            raise ValueError("stage exponential powers differ")
        direct_z = _sum(self.direct_target_mass_intervals)
        beta = _sum(self.shifted_target_mass_intervals)
        recovered_z = _divide_positive(beta, _power_positive(expected_s, 2))
        normalizer = _intersect(direct_z, recovered_z)
        direct_probabilities = tuple(
            _divide_positive(value, normalizer)
            for value in self.direct_target_mass_intervals
        )
        shifted_probabilities = tuple(
            _divide_positive(value, beta)
            for value in self.shifted_target_mass_intervals
        )
        probabilities = tuple(
            _intersect(left, right)
            for left, right in zip(direct_probabilities, shifted_probabilities)
        )
        if (
            self.direct_normalizer_interval != direct_z
            or self.shifted_acceptance_interval != beta
            or self.shifted_recovered_normalizer_interval != recovered_z
            or self.normalizer_interval != normalizer
        ):
            raise ValueError("stage normalizer routes differ")
        if (
            self.direct_probability_intervals != direct_probabilities
            or self.shifted_probability_intervals != shifted_probabilities
            or self.probability_intervals != probabilities
            or self.probability_sum_interval != _sum(probabilities)
        ):
            raise ValueError("stage probability routes differ")
        if _sha(self.record_sha256, "precision-stage digest") != _digest(
            "precision-stage", self
        ):
            raise ValueError("precision-stage digest differs")


@dataclass(frozen=True, slots=True)
class AtomicQAnalyticLayer(_SealedRecord):
    schema_version: str
    fixture_id: str
    parameter_layer: str
    activity: Fraction
    total_cap: int
    type_labels: Tuple[str, ...]
    event_dimensions: Tuple[int, ...]
    type_weights: Tuple[Fraction, ...]
    support_labels: Tuple[str, ...]
    count_vectors: Tuple[Tuple[int, int], ...]
    exact_scores: Tuple[Fraction, ...]
    score_lower_bound: Fraction
    score_upper_bound: Fraction
    raw_base_normalizer_by_support: Fraction
    raw_base_normalizer_by_count_series: Fraction
    normalized_base_masses: Tuple[Fraction, ...]
    precision_schedule: Tuple[int, ...]
    precision_stages: Tuple[AtomicQPrecisionStage, ...]
    states: Tuple[AtomicQStateOracle, ...]
    target_normalizer_interval: ClosedRationalInterval
    shifted_acceptance_interval: ClosedRationalInterval
    target_probability_intervals: Tuple[ClosedRationalInterval, ...]
    probability_sum_interval: ClosedRationalInterval
    support_sha256: str
    parameter_sha256: str
    score_table_sha256: str
    exact_score_table_bound: bool
    base_factorials_reconstructed: bool
    high_precision_interval_oracle_derived: bool
    stored_binary64_parameter_values_only: bool
    operational_mu_fp_identified: bool
    runtime_source_or_rng_law_verified: bool
    facade_integrated: bool
    kernel_integrated: bool
    operational_categorical_record_compared: bool
    formal_test28_evidence: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    record_sha256: str

    def __post_init__(self) -> None:
        schema = _text(self.schema_version, "layer schema", 128)
        fixture = _text(self.fixture_id, "layer fixture", 64)
        layer = _text(self.parameter_layer, "parameter layer", 64)
        activity = _fraction(self.activity, "activity")
        cap = _integer(self.total_cap, "total cap", 0, 2)
        type_labels = _exact_tuple(self.type_labels, "type labels", 2)
        for value in type_labels:
            _text(value, "type label", 32)
        dimensions = _exact_tuple(self.event_dimensions, "event dimensions", 2)
        for value in dimensions:
            _integer(value, "event dimension", 0, 16)
        weights = _exact_tuple(self.type_weights, "type weights", 2)
        for value in weights:
            _fraction(value, "type weight")
        support_labels = _exact_tuple(self.support_labels, "support labels", 6)
        for value in support_labels:
            _text(value, "support label", 32)
        count_vectors = _exact_tuple(self.count_vectors, "count vectors", 6)
        for vector in count_vectors:
            entries = _exact_tuple(vector, "count vector", 2)
            for entry in entries:
                _integer(entry, "count", 0, 2)
        scores = _exact_tuple(self.exact_scores, "exact scores", 6)
        for value in scores:
            _fraction(value, "exact score")
        lower_score = _fraction(self.score_lower_bound, "score_lower_bound")
        upper_score = _fraction(self.score_upper_bound, "score_upper_bound")
        raw_support_z = _fraction(
            self.raw_base_normalizer_by_support, "raw_base_normalizer_by_support"
        )
        raw_series_z = _fraction(
            self.raw_base_normalizer_by_count_series,
            "raw_base_normalizer_by_count_series",
        )
        schedule = _exact_tuple(self.precision_schedule, "precision schedule", 4)
        for value in schedule:
            _integer(value, "precision schedule entry", 32, 1024)
        if (
            schema != CP55_TEST28_ATOMIC_Q_SCHEMA_VERSION
            or fixture != CP55_TEST28_ATOMIC_Q_FIXTURE_ID
            or layer not in _LAYERS
        ):
            raise ValueError("analytic layer identity differs")
        if activity != _ACTIVITY or cap != _CAP:
            raise ValueError("analytic layer activity/cap differs")
        if type_labels != _TYPE_LABELS or dimensions != _EVENT_DIMENSIONS:
            raise ValueError("analytic layer type metadata differs")
        expected_weights = _IDEAL_WEIGHTS if layer == "ideal_rational" else _B64_WEIGHTS
        if weights != expected_weights:
            raise ValueError("analytic layer weights differ")
        if (
            support_labels != _SUPPORT_LABELS
            or count_vectors != _COUNT_VECTORS
            or scores != _SCORES
        ):
            raise ValueError("analytic layer support/score table differs")
        if lower_score != _LOWER_SCORE or upper_score != _UPPER_SCORE:
            raise ValueError("analytic layer score bounds differ")
        if raw_support_z != Fraction(5, 2) or raw_series_z != Fraction(5, 2):
            raise ValueError("analytic layer base normalizer differs")
        masses = _exact_tuple(self.normalized_base_masses, "normalized base masses", 6)
        for value in masses:
            _fraction(value, "normalized base mass")
        expected_raw = []
        for vector in _COUNT_VECTORS:
            raw = activity ** sum(vector)
            for count, weight in zip(vector, weights):
                raw *= weight**count / math.factorial(count)
            expected_raw.append(raw)
        expected_raw_tuple = tuple(expected_raw)
        expected_masses = tuple(value / raw_support_z for value in expected_raw_tuple)
        if masses != expected_masses or sum(masses, _ZERO) != 1:
            raise ValueError("normalized base masses are invalid")
        if schedule != _PRECISION_SCHEDULE:
            raise ValueError("precision schedule differs")
        stages = _exact_tuple(self.precision_stages, "precision stages", 4)
        previous = None
        for stage_index, stage in enumerate(stages):
            if type(stage) is not AtomicQPrecisionStage:
                raise TypeError("precision stages have the wrong exact type")
            stage.__post_init__()
            if stage.precision_bits != schedule[stage_index]:
                raise ValueError("precision stage does not match its schedule entry")
            expected_direct_masses = tuple(
                _scale(value, mass)
                for value, mass in zip(stage.exp_score_intervals, expected_masses)
            )
            expected_shifted_masses = tuple(
                _scale(value, mass)
                for value, mass in zip(
                    stage.exp_shifted_score_intervals, expected_masses
                )
            )
            if (
                stage.direct_target_mass_intervals != expected_direct_masses
                or stage.shifted_target_mass_intervals != expected_shifted_masses
            ):
                raise ValueError(
                    "stage masses do not follow from factorial base masses"
                )
            if previous is not None:
                scalar_names = (
                    "exp_minus_half_interval",
                    "direct_normalizer_interval",
                    "shifted_acceptance_interval",
                    "shifted_recovered_normalizer_interval",
                    "normalizer_interval",
                    "probability_sum_interval",
                )
                vector_names = (
                    "exp_score_intervals",
                    "exp_shifted_score_intervals",
                    "direct_target_mass_intervals",
                    "shifted_target_mass_intervals",
                    "direct_probability_intervals",
                    "shifted_probability_intervals",
                    "probability_intervals",
                )
                for name in scalar_names:
                    old = getattr(previous, name)
                    new = getattr(stage, name)
                    if new.lower < old.lower or new.upper > old.upper:
                        raise ValueError(name + " precision stages are not nested")
                for name in vector_names:
                    for old, new in zip(getattr(previous, name), getattr(stage, name)):
                        if new.lower < old.lower or new.upper > old.upper:
                            raise ValueError(name + " precision stages are not nested")
            previous = stage
        states = _exact_tuple(self.states, "state records", 6)
        final = stages[-1]
        for index, state in enumerate(states):
            if type(state) is not AtomicQStateOracle:
                raise TypeError("state records have the wrong exact type")
            state.__post_init__()
            expected_state_values = (
                index,
                _SUPPORT_LABELS[index],
                _COUNT_VECTORS[index],
                tuple(math.factorial(value) for value in _COUNT_VECTORS[index]),
                expected_raw_tuple[index],
                expected_masses[index],
                _SCORES[index],
                _SCORES[index] - _UPPER_SCORE,
                final.exp_score_intervals[index],
                final.exp_shifted_score_intervals[index],
                final.direct_target_mass_intervals[index],
                final.shifted_target_mass_intervals[index],
                final.probability_intervals[index],
            )
            actual_state_values = tuple(
                getattr(state, field.name)
                for field in fields(AtomicQStateOracle)
                if field.name != "record_sha256"
            )
            if actual_state_values != expected_state_values:
                raise ValueError("state record differs from its analytic layer")
        for name in (
            "target_normalizer_interval",
            "shifted_acceptance_interval",
            "probability_sum_interval",
        ):
            value = getattr(self, name)
            if type(value) is not ClosedRationalInterval:
                raise TypeError(name + " has the wrong exact type")
            value.__post_init__()
        probabilities = _exact_tuple(
            self.target_probability_intervals, "target probability intervals", 6
        )
        for value in probabilities:
            if type(value) is not ClosedRationalInterval:
                raise TypeError("target probabilities must contain exact intervals")
            value.__post_init__()
        if (
            self.target_normalizer_interval != final.normalizer_interval
            or self.shifted_acceptance_interval != final.shifted_acceptance_interval
            or self.target_probability_intervals != final.probability_intervals
            or self.probability_sum_interval != final.probability_sum_interval
        ):
            raise ValueError(
                "published final intervals differ from final precision stage"
            )
        for name in ("support_sha256", "parameter_sha256", "score_table_sha256"):
            _sha(getattr(self, name), name)
        if (
            self.support_sha256 != _support_digest()
            or self.parameter_sha256 != _parameter_digest(layer, expected_weights)
            or self.score_table_sha256 != _score_digest()
        ):
            raise ValueError("analytic layer primitive digest differs")
        true_flags = (
            "exact_score_table_bound",
            "base_factorials_reconstructed",
            "high_precision_interval_oracle_derived",
        )
        false_flags = (
            "operational_mu_fp_identified",
            "runtime_source_or_rng_law_verified",
            "facade_integrated",
            "kernel_integrated",
            "operational_categorical_record_compared",
            "formal_test28_evidence",
            "confirmatory_evidence",
            "manuscript_claim",
        )
        for name in true_flags:
            if type(getattr(self, name)) is not bool:
                raise TypeError(name + " must be bool")
            if not getattr(self, name):
                raise ValueError(name + " must be true")
        for name in false_flags:
            if type(getattr(self, name)) is not bool:
                raise TypeError(name + " must be bool")
            if getattr(self, name):
                raise ValueError(name + " must be false")
        expected_b64_flag = layer == "binary64_parameter"
        if type(self.stored_binary64_parameter_values_only) is not bool:
            raise TypeError("stored-binary64 flag must be bool")
        if self.stored_binary64_parameter_values_only is not expected_b64_flag:
            raise ValueError("stored-binary64 flag differs")
        if _sha(self.record_sha256, "analytic-layer digest") != _digest(
            "analytic-layer", self
        ):
            raise ValueError("analytic-layer digest differs")


@dataclass(frozen=True, slots=True)
class AtomicQParameterPerturbation(_SealedRecord):
    direction: str
    exact_base_proposal_total_variation: Fraction
    binary64_minus_ideal_normalizer_difference: ClosedRationalInterval
    binary64_minus_ideal_shifted_acceptance_difference: ClosedRationalInterval
    binary64_minus_ideal_probability_differences: Tuple[ClosedRationalInterval, ...]
    target_total_variation_interval: ClosedRationalInterval
    record_sha256: str

    def __post_init__(self) -> None:
        if (
            _text(self.direction, "perturbation direction", 128)
            != "binary64_parameter-minus-ideal_rational"
        ):
            raise ValueError("perturbation direction differs")
        tv = _fraction(self.exact_base_proposal_total_variation, "base proposal TV")
        if tv != _EXACT_BASE_PROPOSAL_TV:
            raise ValueError(
                "base proposal TV differs from the frozen parameter layers"
            )
        for name in (
            "binary64_minus_ideal_normalizer_difference",
            "binary64_minus_ideal_shifted_acceptance_difference",
            "target_total_variation_interval",
        ):
            value = getattr(self, name)
            if type(value) is not ClosedRationalInterval:
                raise TypeError(name + " has the wrong exact type")
            value.__post_init__()
        if self.binary64_minus_ideal_normalizer_difference.lower <= 0:
            raise ValueError(
                "binary64-minus-ideal normalizer difference must be certified positive"
            )
        differences = _exact_tuple(
            self.binary64_minus_ideal_probability_differences,
            "probability differences",
            6,
        )
        for value in differences:
            if type(value) is not ClosedRationalInterval:
                raise TypeError("probability differences must contain exact intervals")
            value.__post_init__()
        expected_target_tv = _scale(
            _sum(tuple(_absolute(value) for value in differences)), _HALF
        )
        if self.target_total_variation_interval != expected_target_tv:
            raise ValueError("target TV does not follow from category differences")
        if self.target_total_variation_interval.lower <= 0:
            raise ValueError("target TV must be certified positive")
        if _sha(self.record_sha256, "perturbation digest") != _digest(
            "parameter-perturbation", self
        ):
            raise ValueError("perturbation digest differs")


@dataclass(frozen=True, slots=True)
class AtomicQOraclePair(_SealedRecord):
    schema_version: str
    fixture_id: str
    formula_id: str
    interval_method: str
    scope: str
    nonclaims: Tuple[str, ...]
    score_provider: AtomicQScoreTableProvider
    ideal_rational: AtomicQAnalyticLayer
    binary64_parameter: AtomicQAnalyticLayer
    perturbation: AtomicQParameterPerturbation
    analytic_parameter_layers_distinct: bool
    count_keyed_runtime_adapter_required: bool
    operational_adapter_implemented: bool
    kernel_integration_implemented: bool
    formal_test28_evidence: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    record_sha256: str

    def __post_init__(self) -> None:
        for name in (
            "schema_version",
            "fixture_id",
            "formula_id",
            "interval_method",
            "scope",
        ):
            _text(getattr(self, name), name)
        nonclaims = _exact_tuple(
            self.nonclaims, "nonclaims", len(CP55_TEST28_ATOMIC_Q_NONCLAIMS)
        )
        for value in nonclaims:
            _text(value, "nonclaim")
        if (
            self.schema_version != CP55_TEST28_ATOMIC_Q_SCHEMA_VERSION
            or self.fixture_id != CP55_TEST28_ATOMIC_Q_FIXTURE_ID
            or self.formula_id != CP55_TEST28_ATOMIC_Q_FORMULA_ID
            or self.interval_method != CP55_TEST28_ATOMIC_Q_INTERVAL_METHOD
            or self.scope != CP55_TEST28_ATOMIC_Q_SCOPE
        ):
            raise ValueError("oracle-pair identity differs")
        if nonclaims != CP55_TEST28_ATOMIC_Q_NONCLAIMS:
            raise ValueError("oracle-pair nonclaims differ")
        if type(self.score_provider) is not AtomicQScoreTableProvider:
            raise TypeError("score provider has the wrong exact type")
        self.score_provider.__post_init__()
        if (
            type(self.ideal_rational) is not AtomicQAnalyticLayer
            or type(self.binary64_parameter) is not AtomicQAnalyticLayer
        ):
            raise TypeError("analytic layers have the wrong exact type")
        self.ideal_rational.__post_init__()
        self.binary64_parameter.__post_init__()
        if (
            self.ideal_rational.parameter_layer != "ideal_rational"
            or self.binary64_parameter.parameter_layer != "binary64_parameter"
        ):
            raise ValueError("analytic layer order differs")
        if type(self.perturbation) is not AtomicQParameterPerturbation:
            raise TypeError("perturbation has the wrong exact type")
        self.perturbation.__post_init__()
        if (
            self.score_provider.count_vectors != self.ideal_rational.count_vectors
            or self.score_provider.count_vectors
            != self.binary64_parameter.count_vectors
            or self.score_provider.exact_scores != self.ideal_rational.exact_scores
            or self.score_provider.exact_scores != self.binary64_parameter.exact_scores
        ):
            raise ValueError("provider and analytic layers are not cross-bound")
        if self.ideal_rational.type_weights == self.binary64_parameter.type_weights:
            raise ValueError("analytic parameter layers must be distinct")
        expected_perturbation = _perturbation(
            self.ideal_rational, self.binary64_parameter
        )
        if self.perturbation != expected_perturbation:
            raise ValueError("perturbation differs from paired analytic layers")
        for name in (
            "analytic_parameter_layers_distinct",
            "count_keyed_runtime_adapter_required",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(name + " must be bool")
            if not getattr(self, name):
                raise ValueError(name + " must be true")
        for name in (
            "operational_adapter_implemented",
            "kernel_integration_implemented",
            "formal_test28_evidence",
            "confirmatory_evidence",
            "manuscript_claim",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(name + " must be bool")
            if getattr(self, name):
                raise ValueError(name + " must be false")
        if _sha(self.record_sha256, "oracle-pair digest") != _digest(
            "oracle-pair", self
        ):
            raise ValueError("oracle-pair digest differs")


def _derive_base(
    type_weights: Tuple[Fraction, Fraction]
) -> Tuple[Tuple[Fraction, ...], Fraction]:
    raw = []
    for vector in _COUNT_VECTORS:
        value = _ACTIVITY ** sum(vector)
        for count, weight in zip(vector, type_weights):
            value *= weight**count / math.factorial(count)
        raw.append(value)
    normalizer = sum(raw, _ZERO)
    count_series = sum(
        (_ACTIVITY**count / math.factorial(count) for count in range(_CAP + 1)), _ZERO
    )
    if normalizer != count_series or normalizer != Fraction(5, 2):
        raise ArithmeticError("support and capped-count base normalizers disagree")
    return tuple(value / normalizer for value in raw), normalizer


def _stage(bits: int, base: Tuple[Fraction, ...]) -> AtomicQPrecisionStage:
    s, terms = _exp_minus_half(bits)
    inverse = _reciprocal_positive(s)
    s2 = _power_positive(s, 2)
    direct_exp = (_point(_ONE), inverse, s, _power_positive(inverse, 2), inverse, s2)
    shifted_exp = (s2, s, _power_positive(s, 3), _point(_ONE), s, _power_positive(s, 4))
    direct_masses = tuple(_scale(value, mass) for value, mass in zip(direct_exp, base))
    shifted_masses = tuple(
        _scale(value, mass) for value, mass in zip(shifted_exp, base)
    )
    direct_z = _sum(direct_masses)
    beta = _sum(shifted_masses)
    recovered_z = _divide_positive(beta, s2)
    normalizer = _intersect(direct_z, recovered_z)
    direct_probabilities = tuple(
        _divide_positive(value, normalizer) for value in direct_masses
    )
    shifted_probabilities = tuple(
        _divide_positive(value, beta) for value in shifted_masses
    )
    probabilities = tuple(
        _intersect(left, right)
        for left, right in zip(direct_probabilities, shifted_probabilities)
    )
    probability_sum = _sum(probabilities)
    return _make_record(
        AtomicQPrecisionStage,
        "precision-stage",
        precision_bits=bits,
        taylor_terms=terms,
        exp_minus_half_interval=s,
        exp_score_intervals=direct_exp,
        exp_shifted_score_intervals=shifted_exp,
        direct_target_mass_intervals=direct_masses,
        shifted_target_mass_intervals=shifted_masses,
        direct_normalizer_interval=direct_z,
        shifted_acceptance_interval=beta,
        shifted_recovered_normalizer_interval=recovered_z,
        normalizer_interval=normalizer,
        direct_probability_intervals=direct_probabilities,
        shifted_probability_intervals=shifted_probabilities,
        probability_intervals=probabilities,
        probability_sum_interval=probability_sum,
    )


def _support_digest() -> str:
    return _digest(
        "support",
        (_SUPPORT_LABELS, _COUNT_VECTORS, _RUNTIME_COUNT_VECTORS, _RUNTIME_TO_PROTOCOL),
    )


def _score_digest() -> str:
    return _digest(
        "score-table",
        (_SUPPORT_LABELS, _COUNT_VECTORS, _SCORES, _LOWER_SCORE, _UPPER_SCORE),
    )


def _parameter_digest(layer: str, weights: Tuple[Fraction, Fraction]) -> str:
    return _digest(
        "analytic-parameters",
        (layer, _ACTIVITY, _CAP, _TYPE_LABELS, _EVENT_DIMENSIONS, weights),
    )


def _layer(layer: str, weights: Tuple[Fraction, Fraction]) -> AtomicQAnalyticLayer:
    base, raw_normalizer = _derive_base(weights)
    stages = tuple(_stage(bits, base) for bits in _PRECISION_SCHEDULE)
    final = stages[-1]
    states = []
    for index, vector in enumerate(_COUNT_VECTORS):
        raw = _ACTIVITY ** sum(vector)
        for count, weight in zip(vector, weights):
            raw *= weight**count / math.factorial(count)
        states.append(
            _make_record(
                AtomicQStateOracle,
                "state-oracle",
                protocol_index=index,
                state_label=_SUPPORT_LABELS[index],
                count_vector=vector,
                multiplicity_factorials=tuple(
                    math.factorial(value) for value in vector
                ),
                raw_base_weight=raw,
                normalized_base_mass=base[index],
                exact_score=_SCORES[index],
                exact_shifted_score=_SCORES[index] - _UPPER_SCORE,
                exp_score_interval=final.exp_score_intervals[index],
                exp_shifted_score_interval=final.exp_shifted_score_intervals[index],
                direct_target_mass_interval=final.direct_target_mass_intervals[index],
                shifted_target_mass_interval=final.shifted_target_mass_intervals[index],
                target_probability_interval=final.probability_intervals[index],
            )
        )
    return _make_record(
        AtomicQAnalyticLayer,
        "analytic-layer",
        schema_version=CP55_TEST28_ATOMIC_Q_SCHEMA_VERSION,
        fixture_id=CP55_TEST28_ATOMIC_Q_FIXTURE_ID,
        parameter_layer=layer,
        activity=_ACTIVITY,
        total_cap=_CAP,
        type_labels=_TYPE_LABELS,
        event_dimensions=_EVENT_DIMENSIONS,
        type_weights=weights,
        support_labels=_SUPPORT_LABELS,
        count_vectors=_COUNT_VECTORS,
        exact_scores=_SCORES,
        score_lower_bound=_LOWER_SCORE,
        score_upper_bound=_UPPER_SCORE,
        raw_base_normalizer_by_support=raw_normalizer,
        raw_base_normalizer_by_count_series=Fraction(5, 2),
        normalized_base_masses=base,
        precision_schedule=_PRECISION_SCHEDULE,
        precision_stages=stages,
        states=tuple(states),
        target_normalizer_interval=final.normalizer_interval,
        shifted_acceptance_interval=final.shifted_acceptance_interval,
        target_probability_intervals=final.probability_intervals,
        probability_sum_interval=final.probability_sum_interval,
        support_sha256=_support_digest(),
        parameter_sha256=_parameter_digest(layer, weights),
        score_table_sha256=_score_digest(),
        exact_score_table_bound=True,
        base_factorials_reconstructed=True,
        high_precision_interval_oracle_derived=True,
        stored_binary64_parameter_values_only=layer == "binary64_parameter",
        operational_mu_fp_identified=False,
        runtime_source_or_rng_law_verified=False,
        facade_integrated=False,
        kernel_integrated=False,
        operational_categorical_record_compared=False,
        formal_test28_evidence=False,
        confirmatory_evidence=False,
        manuscript_claim=False,
    )


def _perturbation(
    ideal: AtomicQAnalyticLayer, binary64: AtomicQAnalyticLayer
) -> AtomicQParameterPerturbation:
    base_tv = (
        sum(
            (
                abs(right - left)
                for left, right in zip(
                    ideal.normalized_base_masses, binary64.normalized_base_masses
                )
            ),
            _ZERO,
        )
        / 2
    )
    if base_tv != _EXACT_BASE_PROPOSAL_TV:
        raise ArithmeticError("base proposal TV differs from its frozen exact value")
    normalizer_difference = _difference(
        binary64.target_normalizer_interval, ideal.target_normalizer_interval
    )
    acceptance_difference = _difference(
        binary64.shifted_acceptance_interval, ideal.shifted_acceptance_interval
    )
    probability_differences = tuple(
        _difference(right, left)
        for left, right in zip(
            ideal.target_probability_intervals, binary64.target_probability_intervals
        )
    )
    target_tv = _scale(
        _sum(tuple(_absolute(value) for value in probability_differences)), _HALF
    )
    return _make_record(
        AtomicQParameterPerturbation,
        "parameter-perturbation",
        direction="binary64_parameter-minus-ideal_rational",
        exact_base_proposal_total_variation=base_tv,
        binary64_minus_ideal_normalizer_difference=normalizer_difference,
        binary64_minus_ideal_shifted_acceptance_difference=acceptance_difference,
        binary64_minus_ideal_probability_differences=probability_differences,
        target_total_variation_interval=target_tv,
    )


def _preflight_fixture_inputs(
    fixture_id: object,
    state_labels: object,
    count_vectors: object,
    activity: object,
    ideal_type_weights: object,
    binary64_type_weights: object,
    type_labels: object,
    event_dimensions: object,
    total_cap: object,
    exact_scores: object,
    precision_schedule: object,
) -> None:
    _text(fixture_id, "fixture_id", 64)
    labels = _exact_tuple(state_labels, "state_labels", 6)
    for value in labels:
        _text(value, "state label", 32)
    vectors = _exact_tuple(count_vectors, "count_vectors", 6)
    for vector in vectors:
        entries = _exact_tuple(vector, "count vector", 2)
        for entry in entries:
            _integer(entry, "count", 0, 2)
    _fraction(activity, "activity")
    for name, values in (
        ("ideal_type_weights", ideal_type_weights),
        ("binary64_type_weights", binary64_type_weights),
    ):
        pair = _exact_tuple(values, name, 2)
        for value in pair:
            _fraction(value, name + " entry")
    types = _exact_tuple(type_labels, "type_labels", 2)
    for value in types:
        _text(value, "type label", 32)
    dimensions = _exact_tuple(event_dimensions, "event_dimensions", 2)
    for value in dimensions:
        _integer(value, "event dimension", 0, 16)
    _integer(total_cap, "total_cap", 0, 2)
    scores = _exact_tuple(exact_scores, "exact_scores", 6)
    for value in scores:
        _fraction(value, "exact score")
    schedule = _exact_tuple(precision_schedule, "precision_schedule", 4)
    for value in schedule:
        _integer(value, "precision schedule entry", 32, 1024)


def derive_t28_a0_q_oracle_pair(
    *,
    fixture_id: str,
    state_labels: Tuple[str, ...],
    count_vectors: Tuple[Tuple[int, int], ...],
    activity: Fraction,
    ideal_type_weights: Tuple[Fraction, Fraction],
    binary64_type_weights: Tuple[Fraction, Fraction],
    type_labels: Tuple[str, str],
    event_dimensions: Tuple[int, int],
    total_cap: int,
    exact_scores: Tuple[Fraction, ...],
    precision_schedule: Tuple[int, ...],
) -> AtomicQOraclePair:
    """Derive the fixture-locked paired oracle from primitive inputs only."""

    _preflight_fixture_inputs(
        fixture_id,
        state_labels,
        count_vectors,
        activity,
        ideal_type_weights,
        binary64_type_weights,
        type_labels,
        event_dimensions,
        total_cap,
        exact_scores,
        precision_schedule,
    )
    supplied = (
        fixture_id,
        state_labels,
        count_vectors,
        activity,
        ideal_type_weights,
        binary64_type_weights,
        type_labels,
        event_dimensions,
        total_cap,
        exact_scores,
        precision_schedule,
    )
    expected = (
        CP55_TEST28_ATOMIC_Q_FIXTURE_ID,
        _SUPPORT_LABELS,
        _COUNT_VECTORS,
        _ACTIVITY,
        _IDEAL_WEIGHTS,
        _B64_WEIGHTS,
        _TYPE_LABELS,
        _EVENT_DIMENSIONS,
        _CAP,
        _SCORES,
        _PRECISION_SCHEDULE,
    )
    if supplied != expected:
        raise ValueError("inputs differ from the frozen T28-A0-Q design")
    provider = _score_provider()
    ideal = _layer("ideal_rational", _IDEAL_WEIGHTS)
    binary64 = _layer("binary64_parameter", _B64_WEIGHTS)
    perturbation = _perturbation(ideal, binary64)
    return _make_record(
        AtomicQOraclePair,
        "oracle-pair",
        schema_version=CP55_TEST28_ATOMIC_Q_SCHEMA_VERSION,
        fixture_id=CP55_TEST28_ATOMIC_Q_FIXTURE_ID,
        formula_id=CP55_TEST28_ATOMIC_Q_FORMULA_ID,
        interval_method=CP55_TEST28_ATOMIC_Q_INTERVAL_METHOD,
        scope=CP55_TEST28_ATOMIC_Q_SCOPE,
        nonclaims=CP55_TEST28_ATOMIC_Q_NONCLAIMS,
        score_provider=provider,
        ideal_rational=ideal,
        binary64_parameter=binary64,
        perturbation=perturbation,
        analytic_parameter_layers_distinct=True,
        count_keyed_runtime_adapter_required=True,
        operational_adapter_implemented=False,
        kernel_integration_implemented=False,
        formal_test28_evidence=False,
        confirmatory_evidence=False,
        manuscript_claim=False,
    )


def t28_a0_q_oracle_pair() -> AtomicQOraclePair:
    """Return the canonical paired direct-q atomic oracle."""

    return derive_t28_a0_q_oracle_pair(
        fixture_id=CP55_TEST28_ATOMIC_Q_FIXTURE_ID,
        state_labels=_SUPPORT_LABELS,
        count_vectors=_COUNT_VECTORS,
        activity=_ACTIVITY,
        ideal_type_weights=_IDEAL_WEIGHTS,
        binary64_type_weights=_B64_WEIGHTS,
        type_labels=_TYPE_LABELS,
        event_dimensions=_EVENT_DIMENSIONS,
        total_cap=_CAP,
        exact_scores=_SCORES,
        precision_schedule=_PRECISION_SCHEDULE,
    )


def validate_t28_a0_q_oracle_pair(value: AtomicQOraclePair) -> AtomicQOraclePair:
    """Fail closed unless ``value`` equals a fresh primitive rederivation."""

    if type(value) is not AtomicQOraclePair:
        raise TypeError("oracle pair has the wrong exact type")
    value.__post_init__()
    expected = t28_a0_q_oracle_pair()
    if value != expected:
        raise ValueError("oracle pair differs from the primitive rederivation")
    return value


def atomic_q_oracle_pair_record_sha256(value: AtomicQOraclePair) -> str:
    """Return the validated canonical pair digest."""

    return validate_t28_a0_q_oracle_pair(value).record_sha256


__all__ = (
    "AtomicQAnalyticLayer",
    "AtomicQOraclePair",
    "AtomicQParameterPerturbation",
    "AtomicQPrecisionStage",
    "AtomicQScoreEvaluation",
    "AtomicQScoreTableProvider",
    "AtomicQStateOracle",
    "CP55_TEST28_ATOMIC_Q_FIXTURE_ID",
    "CP55_TEST28_ATOMIC_Q_FORMULA_ID",
    "CP55_TEST28_ATOMIC_Q_INTERVAL_METHOD",
    "CP55_TEST28_ATOMIC_Q_NONCLAIMS",
    "CP55_TEST28_ATOMIC_Q_SCHEMA_VERSION",
    "CP55_TEST28_ATOMIC_Q_SCOPE",
    "ClosedRationalInterval",
    "MAX_CP55_EXACT_INTEGER_BITS",
    "MAX_CP55_TAYLOR_TERMS",
    "MAX_CP55_TEXT_LENGTH",
    "atomic_q_oracle_pair_record_sha256",
    "derive_t28_a0_q_oracle_pair",
    "t28_a0_q_oracle_pair",
    "validate_t28_a0_q_oracle_pair",
)
