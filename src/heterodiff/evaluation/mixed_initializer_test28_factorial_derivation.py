"""Independent exact cap-two factorial derivations for Test 28.

This stdlib-only module derives the *analytic base-measure* configuration
masses for ``T28-A0-H`` and ``T28-M2-Q`` from first principles.  Its only
mathematical inputs are the activity, normalized type weights, event
dimensions, cap, and an explicit complete support of type-count vectors.  A
target or reference mass vector is deliberately not an input.

For a count vector ``m`` the frozen formula is

``u(m) = activity**sum(m) * product_d(type_weight[d]**m[d] / m[d]!)``.

The derivation includes each type-multiplicity factorial exactly once and has
no additional total-count factorial.  It also checks the independent route
obtained by multiplying the capped-Poisson count probability by the
conditional multinomial probability.

Both the ideal-rational parameters and the exact rational values of the
stored binary64 parameters are retained.  Neither layer is identified with a
runtime sampler or ``mu_fp``.  No tilt, score, random-source law, operational
prediction, confirmatory result, or manuscript claim is established here.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, fields, is_dataclass
from fractions import Fraction
from typing import Tuple


CP54_TEST28_FACTORIAL_DERIVATION_SCHEMA_VERSION = (
    "cp54-test28-cap-two-factorial-derivation-v1"
)
CP54_TEST28_FACTORIAL_FORMULA_ID = "capped-poisson-type-multiplicity-factorial-v1"
CP54_TEST28_FACTORIAL_FORMULA_STATEMENT = (
    "u(m)=activity^sum(m)*product_d(type_weight[d]^m[d]/m[d]!);"
    "Z=sum_{sum(m)<=cap}u(m);p(m)=u(m)/Z"
)
CP54_TEST28_NO_EXTRA_FACTORIAL_STATEMENT = (
    "each type-multiplicity factorial m[d]! appears exactly once in u(m);"
    "no additional total-count factorial |m|! is inserted"
)
CP54_TEST28_INDEPENDENT_ROUTE_STATEMENT = (
    "count_raw(n)=activity^n/n!;conditional(m|n)=n!/product_d(m[d]!)"
    "*product_d(type_weight[d]^m[d]);count_raw(n)*conditional(m|n)=u(m)"
)
CP54_TEST28_EVENT_DIMENSION_SCOPE_STATEMENT = (
    "event dimensions are fixture-bound metadata but do not enter the base "
    "type-count factorial formula"
)
CP54_TEST28_FACTORIAL_DERIVATION_SCOPE = (
    "independent-exact-cap-two-base-measure-factorial-derivation;"
    "t28-a0-h-and-t28-m2-q;ideal-rational-and-stored-binary64-parameter-"
    "layers;explicit-complete-count-vector-support;support-sum-and-capped-"
    "count-series-normalizers;independent-count-times-multinomial-route;"
    "not-target-tilt-not-score-semantics-not-runtime-sampler-not-mu-fp-"
    "not-rng-law-not-operational-prediction-not-confirmatory-not-manuscript"
)
CP54_TEST28_FACTORIAL_DERIVATION_NONCLAIMS = (
    "the analytic parameter layers are not identified with the runtime sampler law mu_fp",
    "the stored-binary64-parameter layer binds parameter values only, not floating-point execution",
    "no multiplicative H factor or Q-score tilt is applied and no target law is derived",
    "no source uniformity, IID behavior, stream independence, or operational prediction is verified",
    "these deterministic identities are not a Formal Test 28 run, confirmatory evidence, or a manuscript result",
)

MAX_CP54_TEST28_EXACT_INTEGER_BITS = 4096
MAX_CP54_TEST28_TEXT_LENGTH = 2048
MAX_CP54_TEST28_TYPES = 2
MAX_CP54_TEST28_TOTAL_CAP = 2
MAX_CP54_TEST28_SUPPORT_STATES = 6

_DIGEST_DOMAIN = "cp54-test28-cap-two-factorial-derivation-v1"
_ALLOWED_FIXTURES = ("T28-A0-H", "T28-M2-Q")
_ALLOWED_PARAMETER_LAYERS = ("ideal_rational", "binary64_parameter")
_ONE = Fraction(1, 1)
_IDEAL_ACTIVITY = Fraction(1, 1)
_IDEAL_TYPE_WEIGHTS = (Fraction(2, 5), Fraction(3, 5))
_BINARY64_ACTIVITY = Fraction(1, 1)
_BINARY64_TYPE_WEIGHTS = (
    Fraction(3602879701896397, 1 << 53),
    Fraction(5404319552844595, 1 << 53),
)
_COUNT_VECTORS = (
    (0, 0),
    (1, 0),
    (0, 1),
    (2, 0),
    (1, 1),
    (0, 2),
)
_A0_TYPE_LABELS = ("a", "b")
_A0_EVENT_DIMENSIONS = (0, 0)
_A0_SUPPORT_LABELS = ("empty", "a", "b", "aa", "ab", "bb")
_M2_TYPE_LABELS = ("type-1d", "type-2d")
_M2_EVENT_DIMENSIONS = (1, 2)
_M2_SUPPORT_LABELS = (
    "empty",
    "one-type-1d",
    "one-type-2d",
    "two-type-1d",
    "one-each",
    "two-type-2d",
)


class _NonPickleRecord:
    def __reduce__(self) -> object:
        raise TypeError(type(self).__name__ + " is intentionally non-pickleable")

    def __reduce_ex__(self, protocol: object) -> object:
        del protocol
        raise TypeError(type(self).__name__ + " is intentionally non-pickleable")


def _require_text(value: object, *, name: str, maximum: int) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if not value or len(value) > maximum:
        raise ValueError(name + " has invalid bounded length")
    if any(ord(character) < 32 or ord(character) > 126 for character in value):
        raise ValueError(name + " must contain printable ASCII only")
    return value


def _require_integer(
    value: object,
    *,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact non-boolean integer")
    if value < minimum or value > maximum:
        raise ValueError("%s must lie between %d and %d" % (name, minimum, maximum))
    return value


def _require_fraction(
    value: object,
    *,
    name: str,
    nonnegative: bool = False,
    positive: bool = False,
) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError(name + " must be an exact Fraction")
    if (
        value.numerator.bit_length() > MAX_CP54_TEST28_EXACT_INTEGER_BITS
        or value.denominator.bit_length() > MAX_CP54_TEST28_EXACT_INTEGER_BITS
    ):
        raise ValueError(name + " exceeds the frozen exact-integer bit bound")
    if positive and value <= 0:
        raise ValueError(name + " must be strictly positive")
    if nonnegative and value < 0:
        raise ValueError(name + " must be nonnegative")
    return value


def _require_sha256(value: object, *, name: str) -> str:
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
        return ["integer-v1", str(value)]
    if type(value) is str:
        return ["string-v1", value]
    if type(value) is Fraction:
        return ["fraction-v1", str(value.numerator), str(value.denominator)]
    if type(value) is tuple:
        return ["tuple-v1", [_canonical(item) for item in value]]
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            FactorialStateDerivation,
            CapTwoFactorialDerivation,
            FixtureFactorialDerivationPair,
        ):
            raise TypeError("unsupported canonical record " + type(value).__name__)
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


def _digest(kind: str, payload: object) -> str:
    _require_text(kind, name="digest kind", maximum=128)
    document = {
        "domain": _DIGEST_DOMAIN,
        "kind": kind,
        "payload": _canonical(payload),
    }
    encoded = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _formula_digest() -> str:
    return _digest(
        "factorial-formula",
        (
            CP54_TEST28_FACTORIAL_FORMULA_ID,
            CP54_TEST28_FACTORIAL_FORMULA_STATEMENT,
            CP54_TEST28_NO_EXTRA_FACTORIAL_STATEMENT,
            CP54_TEST28_INDEPENDENT_ROUTE_STATEMENT,
        ),
    )


CP54_TEST28_FACTORIAL_FORMULA_SHA256 = _formula_digest()


def _support_digest(
    fixture_id: str,
    total_cap: int,
    type_labels: Tuple[str, ...],
    event_dimensions: Tuple[int, ...],
    support_labels: Tuple[str, ...],
    count_vectors: Tuple[Tuple[int, ...], ...],
) -> str:
    return _digest(
        "fixture-support",
        (
            fixture_id,
            total_cap,
            type_labels,
            event_dimensions,
            support_labels,
            count_vectors,
        ),
    )


def _parameter_digest(
    parameter_layer: str,
    activity: Fraction,
    type_weights: Tuple[Fraction, ...],
) -> str:
    return _digest(
        "exact-analytic-parameters",
        (parameter_layer, activity, type_weights),
    )


@dataclass(frozen=True)
class FactorialStateDerivation(_NonPickleRecord):
    """One exact support term derived without a supplied mass vector."""

    support_index: int
    support_label: str
    count_vector: Tuple[int, ...]
    total_count: int
    activity_power: Fraction
    type_weight_power_product: Fraction
    multiplicity_factorial_product: int
    raw_mass_from_product_formula: Fraction
    count_raw_mass: Fraction
    multinomial_coefficient: int
    conditional_multinomial_probability: Fraction
    raw_mass_via_count_multinomial: Fraction
    normalized_base_mass: Fraction
    normalized_base_mass_via_count_multinomial: Fraction

    def __post_init__(self) -> None:
        _require_integer(
            self.support_index,
            name="state support_index",
            minimum=0,
            maximum=MAX_CP54_TEST28_SUPPORT_STATES - 1,
        )
        _require_text(
            self.support_label,
            name="state support_label",
            maximum=128,
        )
        if type(self.count_vector) is not tuple:
            raise TypeError("state count_vector must be an exact tuple")
        if len(self.count_vector) != MAX_CP54_TEST28_TYPES:
            raise ValueError("state count_vector has the wrong arity")
        if any(type(value) is not int for value in self.count_vector):
            raise TypeError(
                "state count_vector entries must be exact non-boolean integers"
            )
        for index, value in enumerate(self.count_vector):
            _require_integer(
                value,
                name="state count_vector[%d]" % index,
                minimum=0,
                maximum=MAX_CP54_TEST28_TOTAL_CAP,
            )
        total_count = _require_integer(
            self.total_count,
            name="state total_count",
            minimum=0,
            maximum=MAX_CP54_TEST28_TOTAL_CAP,
        )
        if total_count != sum(self.count_vector):
            raise ValueError("state total_count differs from count_vector")
        activity_power = _require_fraction(
            self.activity_power,
            name="state activity_power",
            positive=True,
        )
        weight_product = _require_fraction(
            self.type_weight_power_product,
            name="state type_weight_power_product",
            positive=True,
        )
        multiplicity = _require_integer(
            self.multiplicity_factorial_product,
            name="state multiplicity_factorial_product",
            minimum=1,
            maximum=math.factorial(MAX_CP54_TEST28_TOTAL_CAP),
        )
        expected_multiplicity = math.prod(
            math.factorial(value) for value in self.count_vector
        )
        if multiplicity != expected_multiplicity:
            raise ValueError("state multiplicity factorial product differs")
        raw_mass = _require_fraction(
            self.raw_mass_from_product_formula,
            name="state raw_mass_from_product_formula",
            positive=True,
        )
        if raw_mass != activity_power * weight_product / multiplicity:
            raise ValueError("state product-formula raw mass differs")
        count_raw = _require_fraction(
            self.count_raw_mass,
            name="state count_raw_mass",
            positive=True,
        )
        coefficient = _require_integer(
            self.multinomial_coefficient,
            name="state multinomial_coefficient",
            minimum=1,
            maximum=math.factorial(MAX_CP54_TEST28_TOTAL_CAP),
        )
        expected_coefficient = math.factorial(total_count) // multiplicity
        if coefficient != expected_coefficient:
            raise ValueError("state multinomial coefficient differs")
        conditional = _require_fraction(
            self.conditional_multinomial_probability,
            name="state conditional_multinomial_probability",
            positive=True,
        )
        if conditional != coefficient * weight_product:
            raise ValueError("state conditional multinomial probability differs")
        alternative_raw = _require_fraction(
            self.raw_mass_via_count_multinomial,
            name="state raw_mass_via_count_multinomial",
            positive=True,
        )
        if alternative_raw != count_raw * conditional or alternative_raw != raw_mass:
            raise ValueError("state independent raw-mass routes disagree")
        normalized = _require_fraction(
            self.normalized_base_mass,
            name="state normalized_base_mass",
            positive=True,
        )
        alternative_normalized = _require_fraction(
            self.normalized_base_mass_via_count_multinomial,
            name="state normalized_base_mass_via_count_multinomial",
            positive=True,
        )
        if alternative_normalized != normalized:
            raise ValueError("state independent normalized-mass routes disagree")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("FactorialStateDerivation cannot be subclassed")


@dataclass(frozen=True)
class CapTwoFactorialDerivation(_NonPickleRecord):
    """Exact derivation for one fixture and analytic parameter layer."""

    schema_version: str
    fixture_id: str
    parameter_layer: str
    formula_id: str
    formula_statement: str
    no_extra_total_factorial_statement: str
    independent_route_statement: str
    event_dimension_scope_statement: str
    activity: Fraction
    total_cap: int
    type_labels: Tuple[str, ...]
    type_weights: Tuple[Fraction, ...]
    event_dimensions: Tuple[int, ...]
    support_labels: Tuple[str, ...]
    count_vectors: Tuple[Tuple[int, ...], ...]
    states: Tuple[FactorialStateDerivation, ...]
    raw_normalizer_by_support_sum: Fraction
    raw_normalizer_by_capped_count_series: Fraction
    base_masses: Tuple[Fraction, ...]
    count_raw_masses: Tuple[Fraction, ...]
    count_marginal_probabilities: Tuple[Fraction, ...]
    formula_sha256: str
    parameter_sha256: str
    support_sha256: str
    complete_support_verified: bool
    type_weights_normalized_exactly: bool
    multiplicity_factorials_used_exactly_once: bool
    extra_total_count_factorial_used: bool
    support_and_count_routes_agree: bool
    analytic_base_measure_only: bool
    ideal_rational_parameter_reference: bool
    stored_binary64_parameter_values_only: bool
    operational_reference_sampler_law_claim: bool
    operational_mu_fp_identified: bool
    runtime_source_or_rng_law_verified: bool
    target_tilt_or_score_applied: bool
    formal_test28_evidence: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    record_sha256: str

    def __post_init__(self) -> None:
        _validate_derivation_record(self)

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CapTwoFactorialDerivation cannot be subclassed")


@dataclass(frozen=True)
class FixtureFactorialDerivationPair(_NonPickleRecord):
    """Paired ideal-rational and stored-binary64 analytic derivations."""

    schema_version: str
    fixture_id: str
    ideal_rational: CapTwoFactorialDerivation
    binary64_parameter: CapTwoFactorialDerivation
    common_support_sha256: str
    parameter_records_distinct: bool
    base_mass_vectors_distinct: bool
    analytic_base_measure_only: bool
    operational_reference_sampler_law_claim: bool
    operational_mu_fp_identified: bool
    runtime_source_or_rng_law_verified: bool
    target_tilt_or_score_applied: bool
    formal_test28_evidence: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    record_sha256: str

    def __post_init__(self) -> None:
        schema = _require_text(
            self.schema_version,
            name="pair schema_version",
            maximum=128,
        )
        fixture_id = _require_text(
            self.fixture_id,
            name="pair fixture_id",
            maximum=128,
        )
        if schema != CP54_TEST28_FACTORIAL_DERIVATION_SCHEMA_VERSION:
            raise ValueError("pair schema_version differs from the frozen schema")
        if fixture_id not in _ALLOWED_FIXTURES:
            raise ValueError("pair fixture_id is not a frozen fixture")
        if type(self.ideal_rational) is not CapTwoFactorialDerivation:
            raise TypeError("pair ideal_rational has the wrong exact record type")
        if type(self.binary64_parameter) is not CapTwoFactorialDerivation:
            raise TypeError("pair binary64_parameter has the wrong exact record type")
        self.ideal_rational.__post_init__()
        self.binary64_parameter.__post_init__()
        if (
            self.ideal_rational.fixture_id != fixture_id
            or self.binary64_parameter.fixture_id != fixture_id
        ):
            raise ValueError("pair child fixture identifiers differ")
        if self.ideal_rational.parameter_layer != "ideal_rational":
            raise ValueError("pair ideal child has the wrong parameter layer")
        if self.binary64_parameter.parameter_layer != "binary64_parameter":
            raise ValueError("pair binary64 child has the wrong parameter layer")
        common_support = _require_sha256(
            self.common_support_sha256,
            name="pair common_support_sha256",
        )
        if (
            common_support != self.ideal_rational.support_sha256
            or common_support != self.binary64_parameter.support_sha256
        ):
            raise ValueError("pair support digests differ")
        if self.parameter_records_distinct is not True:
            raise ValueError("pair parameter-record distinction flag differs")
        if (
            self.ideal_rational.parameter_sha256
            == self.binary64_parameter.parameter_sha256
            or self.ideal_rational.record_sha256
            == self.binary64_parameter.record_sha256
        ):
            raise ValueError("pair parameter-layer records are not distinct")
        if self.base_mass_vectors_distinct is not True:
            raise ValueError("pair base-mass distinction flag differs")
        if self.ideal_rational.base_masses == self.binary64_parameter.base_masses:
            raise ValueError("pair base-mass vectors unexpectedly coincide")
        if self.analytic_base_measure_only is not True:
            raise ValueError("pair must be marked analytic-base-measure-only")
        if any(
            value is not False
            for value in (
                self.operational_reference_sampler_law_claim,
                self.operational_mu_fp_identified,
                self.runtime_source_or_rng_law_verified,
                self.target_tilt_or_score_applied,
                self.formal_test28_evidence,
                self.confirmatory_evidence,
                self.manuscript_claim,
            )
        ):
            raise ValueError("pair contains a forbidden operational or evidence claim")
        _require_sha256(self.record_sha256, name="pair record_sha256")
        if self.record_sha256 != _pair_digest(self):
            raise ValueError("pair record digest differs")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("FixtureFactorialDerivationPair cannot be subclassed")


def _expected_fixture_fields(
    fixture_id: str,
) -> Tuple[Tuple[str, ...], Tuple[int, ...], Tuple[str, ...],]:
    if fixture_id == "T28-A0-H":
        return _A0_TYPE_LABELS, _A0_EVENT_DIMENSIONS, _A0_SUPPORT_LABELS
    if fixture_id == "T28-M2-Q":
        return _M2_TYPE_LABELS, _M2_EVENT_DIMENSIONS, _M2_SUPPORT_LABELS
    raise ValueError("fixture_id is not a frozen CP54 fixture")


def _expected_parameters(
    parameter_layer: str,
) -> Tuple[Fraction, Tuple[Fraction, ...]]:
    if parameter_layer == "ideal_rational":
        return _IDEAL_ACTIVITY, _IDEAL_TYPE_WEIGHTS
    if parameter_layer == "binary64_parameter":
        return _BINARY64_ACTIVITY, _BINARY64_TYPE_WEIGHTS
    raise ValueError("parameter_layer is not a frozen analytic layer")


def _complete_count_vectors(
    type_count: int,
    total_cap: int,
) -> Tuple[Tuple[int, ...], ...]:
    """Enumerate ``sum(m) <= cap`` by count, then reverse lexicographic order."""

    _require_integer(
        type_count,
        name="complete-support type_count",
        minimum=1,
        maximum=MAX_CP54_TEST28_TYPES,
    )
    _require_integer(
        total_cap,
        name="complete-support total_cap",
        minimum=0,
        maximum=MAX_CP54_TEST28_TOTAL_CAP,
    )
    vectors = []

    def append_compositions(prefix: Tuple[int, ...], remaining: int) -> None:
        if len(prefix) == type_count - 1:
            vectors.append(prefix + (remaining,))
            return
        for value in range(remaining, -1, -1):
            append_compositions(prefix + (value,), remaining - value)

    for total_count in range(total_cap + 1):
        append_compositions((), total_count)
    expected_size = math.comb(total_cap + type_count, type_count)
    if len(vectors) != expected_size:
        raise ArithmeticError("complete-support enumeration has the wrong size")
    return tuple(vectors)


def _preflight_derivation_inputs(
    *,
    fixture_id: object,
    parameter_layer: object,
    activity: object,
    type_labels: object,
    type_weights: object,
    event_dimensions: object,
    support_labels: object,
    count_vectors: object,
    total_cap: object,
) -> None:
    """Reject non-exact container types before traversing their contents."""

    if type(fixture_id) is not str:
        raise TypeError("fixture_id must be exact text")
    if type(parameter_layer) is not str:
        raise TypeError("parameter_layer must be exact text")
    if type(activity) is not Fraction:
        raise TypeError("activity must be an exact Fraction")
    if type(type_labels) is not tuple:
        raise TypeError("type_labels must be an exact tuple")
    if type(type_weights) is not tuple:
        raise TypeError("type_weights must be an exact tuple")
    if type(event_dimensions) is not tuple:
        raise TypeError("event_dimensions must be an exact tuple")
    if type(support_labels) is not tuple:
        raise TypeError("support_labels must be an exact tuple")
    if type(count_vectors) is not tuple:
        raise TypeError("count_vectors must be an exact tuple")
    if type(total_cap) is not int:
        raise TypeError("total_cap must be an exact non-boolean integer")

    if len(type_labels) != MAX_CP54_TEST28_TYPES:
        raise ValueError("type_labels has the wrong bounded length")
    if len(type_weights) != MAX_CP54_TEST28_TYPES:
        raise ValueError("type_weights has the wrong bounded length")
    if len(event_dimensions) != MAX_CP54_TEST28_TYPES:
        raise ValueError("event_dimensions has the wrong bounded length")
    if len(support_labels) != MAX_CP54_TEST28_SUPPORT_STATES:
        raise ValueError("support_labels has the wrong bounded length")
    if len(count_vectors) != MAX_CP54_TEST28_SUPPORT_STATES:
        raise ValueError("count_vectors has the wrong bounded length")

    if any(type(value) is not str for value in type_labels):
        raise TypeError("type_labels entries must be exact text")
    if any(type(value) is not Fraction for value in type_weights):
        raise TypeError("type_weights entries must be exact Fractions")
    if any(type(value) is not int for value in event_dimensions):
        raise TypeError("event_dimensions entries must be exact non-boolean integers")
    if any(type(value) is not str for value in support_labels):
        raise TypeError("support_labels entries must be exact text")
    if any(type(row) is not tuple for row in count_vectors):
        raise TypeError("count_vectors rows must be exact tuples")
    if any(len(row) != MAX_CP54_TEST28_TYPES for row in count_vectors):
        raise ValueError("count_vectors rows have the wrong arity")
    if any(type(value) is not int for row in count_vectors for value in row):
        raise TypeError("count_vectors entries must be exact non-boolean integers")


def _validate_canonical_inputs(
    *,
    fixture_id: str,
    parameter_layer: str,
    activity: Fraction,
    type_labels: Tuple[str, ...],
    type_weights: Tuple[Fraction, ...],
    event_dimensions: Tuple[int, ...],
    support_labels: Tuple[str, ...],
    count_vectors: Tuple[Tuple[int, ...], ...],
    total_cap: int,
) -> None:
    _require_text(fixture_id, name="fixture_id", maximum=128)
    _require_text(parameter_layer, name="parameter_layer", maximum=64)
    if fixture_id not in _ALLOWED_FIXTURES:
        raise ValueError("fixture_id is not a frozen CP54 fixture")
    if parameter_layer not in _ALLOWED_PARAMETER_LAYERS:
        raise ValueError("parameter_layer is not a frozen analytic layer")
    _require_fraction(activity, name="activity", positive=True)
    cap = _require_integer(
        total_cap,
        name="total_cap",
        minimum=0,
        maximum=MAX_CP54_TEST28_TOTAL_CAP,
    )
    if cap != MAX_CP54_TEST28_TOTAL_CAP:
        raise ValueError("total_cap differs from the frozen cap two")
    for index, label in enumerate(type_labels):
        _require_text(label, name="type_labels[%d]" % index, maximum=128)
    for index, weight in enumerate(type_weights):
        _require_fraction(
            weight,
            name="type_weights[%d]" % index,
            positive=True,
        )
    if sum(type_weights, Fraction(0, 1)) != _ONE:
        raise ValueError("type_weights must normalize exactly")
    for index, dimension in enumerate(event_dimensions):
        _require_integer(
            dimension,
            name="event_dimensions[%d]" % index,
            minimum=0,
            maximum=MAX_CP54_TEST28_TOTAL_CAP,
        )
    for index, label in enumerate(support_labels):
        _require_text(label, name="support_labels[%d]" % index, maximum=128)
    if len(set(support_labels)) != len(support_labels):
        raise ValueError("support_labels contain a duplicate")
    for row_index, row in enumerate(count_vectors):
        for column_index, value in enumerate(row):
            _require_integer(
                value,
                name="count_vectors[%d][%d]" % (row_index, column_index),
                minimum=0,
                maximum=cap,
            )
        if sum(row) > cap:
            raise ValueError("count_vectors contains a vector above total_cap")
    if len(set(count_vectors)) != len(count_vectors):
        raise ValueError("count_vectors contain a duplicate")
    complete_support = _complete_count_vectors(len(type_weights), cap)
    if count_vectors != complete_support:
        raise ValueError(
            "count_vectors are incomplete, noncanonical, or in the wrong order"
        )
    (
        expected_type_labels,
        expected_dimensions,
        expected_support_labels,
    ) = _expected_fixture_fields(fixture_id)
    if type_labels != expected_type_labels:
        raise ValueError("type_labels differ from the canonical fixture order")
    if event_dimensions != expected_dimensions:
        raise ValueError("event_dimensions differ from the canonical fixture")
    if support_labels != expected_support_labels:
        raise ValueError("support_labels differ from the canonical fixture order")
    expected_activity, expected_weights = _expected_parameters(parameter_layer)
    if activity != expected_activity:
        raise ValueError("activity differs from the frozen parameter layer")
    if type_weights != expected_weights:
        raise ValueError("type_weights differ from the frozen parameter layer")


def _derive_components(
    activity: Fraction,
    type_weights: Tuple[Fraction, ...],
    count_vectors: Tuple[Tuple[int, ...], ...],
    total_cap: int,
) -> Tuple[
    Tuple[
        Tuple[
            int,
            Fraction,
            Fraction,
            int,
            Fraction,
            Fraction,
            int,
            Fraction,
            Fraction,
        ],
        ...,
    ],
    Fraction,
    Fraction,
    Tuple[Fraction, ...],
    Tuple[Fraction, ...],
    Tuple[Fraction, ...],
]:
    state_components = []
    for count_vector in count_vectors:
        total_count = sum(count_vector)
        activity_power = activity**total_count
        weight_product = math.prod(
            weight**count for weight, count in zip(type_weights, count_vector)
        )
        multiplicity = math.prod(math.factorial(count) for count in count_vector)
        raw_mass = activity_power * weight_product / multiplicity
        count_raw = activity_power / math.factorial(total_count)
        coefficient = math.factorial(total_count) // multiplicity
        conditional = coefficient * weight_product
        alternative_raw = count_raw * conditional
        if alternative_raw != raw_mass:
            raise ArithmeticError("independent exact raw-mass routes disagree")
        state_components.append(
            (
                total_count,
                activity_power,
                weight_product,
                multiplicity,
                raw_mass,
                count_raw,
                coefficient,
                conditional,
                alternative_raw,
            )
        )
    raw_normalizer = sum((values[4] for values in state_components), Fraction(0, 1))
    capped_series_normalizer = sum(
        (activity**count / math.factorial(count) for count in range(total_cap + 1)),
        Fraction(0, 1),
    )
    if raw_normalizer != capped_series_normalizer:
        raise ArithmeticError("support and capped-count normalizers disagree")
    base_masses = tuple(values[4] / raw_normalizer for values in state_components)
    count_raw_masses = tuple(
        activity**count / math.factorial(count) for count in range(total_cap + 1)
    )
    count_probabilities = tuple(
        value / capped_series_normalizer for value in count_raw_masses
    )
    for count, expected in enumerate(count_probabilities):
        actual = sum(
            (
                base_mass
                for values, base_mass in zip(state_components, base_masses)
                if values[0] == count
            ),
            Fraction(0, 1),
        )
        if actual != expected:
            raise ArithmeticError("configuration and count marginals disagree")
    return (
        tuple(state_components),
        raw_normalizer,
        capped_series_normalizer,
        base_masses,
        count_raw_masses,
        count_probabilities,
    )


def _derivation_digest(value: CapTwoFactorialDerivation) -> str:
    return _digest("cap-two-factorial-derivation", value)


def _pair_digest(value: FixtureFactorialDerivationPair) -> str:
    return _digest("fixture-factorial-derivation-pair", value)


def _validate_derivation_record(value: CapTwoFactorialDerivation) -> None:
    _preflight_derivation_inputs(
        fixture_id=value.fixture_id,
        parameter_layer=value.parameter_layer,
        activity=value.activity,
        type_labels=value.type_labels,
        type_weights=value.type_weights,
        event_dimensions=value.event_dimensions,
        support_labels=value.support_labels,
        count_vectors=value.count_vectors,
        total_cap=value.total_cap,
    )
    schema = _require_text(
        value.schema_version,
        name="derivation schema_version",
        maximum=128,
    )
    if schema != CP54_TEST28_FACTORIAL_DERIVATION_SCHEMA_VERSION:
        raise ValueError("derivation schema_version differs from the frozen schema")
    for name, actual, expected in (
        ("formula_id", value.formula_id, CP54_TEST28_FACTORIAL_FORMULA_ID),
        (
            "formula_statement",
            value.formula_statement,
            CP54_TEST28_FACTORIAL_FORMULA_STATEMENT,
        ),
        (
            "no_extra_total_factorial_statement",
            value.no_extra_total_factorial_statement,
            CP54_TEST28_NO_EXTRA_FACTORIAL_STATEMENT,
        ),
        (
            "independent_route_statement",
            value.independent_route_statement,
            CP54_TEST28_INDEPENDENT_ROUTE_STATEMENT,
        ),
        (
            "event_dimension_scope_statement",
            value.event_dimension_scope_statement,
            CP54_TEST28_EVENT_DIMENSION_SCOPE_STATEMENT,
        ),
    ):
        checked = _require_text(actual, name="derivation " + name, maximum=2048)
        if checked != expected:
            raise ValueError("derivation " + name + " differs")
    _validate_canonical_inputs(
        fixture_id=value.fixture_id,
        parameter_layer=value.parameter_layer,
        activity=value.activity,
        type_labels=value.type_labels,
        type_weights=value.type_weights,
        event_dimensions=value.event_dimensions,
        support_labels=value.support_labels,
        count_vectors=value.count_vectors,
        total_cap=value.total_cap,
    )
    if type(value.states) is not tuple:
        raise TypeError("derivation states must be an exact tuple")
    if len(value.states) != MAX_CP54_TEST28_SUPPORT_STATES:
        raise ValueError("derivation states has the wrong bounded length")
    if any(type(state) is not FactorialStateDerivation for state in value.states):
        raise TypeError("derivation states have the wrong exact record type")
    if type(value.base_masses) is not tuple:
        raise TypeError("derivation base_masses must be an exact tuple")
    if type(value.count_raw_masses) is not tuple:
        raise TypeError("derivation count_raw_masses must be an exact tuple")
    if type(value.count_marginal_probabilities) is not tuple:
        raise TypeError(
            "derivation count_marginal_probabilities must be an exact tuple"
        )
    if len(value.base_masses) != MAX_CP54_TEST28_SUPPORT_STATES:
        raise ValueError("derivation base_masses has the wrong bounded length")
    if len(value.count_raw_masses) != value.total_cap + 1:
        raise ValueError("derivation count_raw_masses has the wrong bounded length")
    if len(value.count_marginal_probabilities) != value.total_cap + 1:
        raise ValueError(
            "derivation count_marginal_probabilities has the wrong bounded length"
        )
    if any(type(item) is not Fraction for item in value.base_masses):
        raise TypeError("derivation base_masses entries must be exact Fractions")
    if any(type(item) is not Fraction for item in value.count_raw_masses):
        raise TypeError("derivation count_raw_masses entries must be exact Fractions")
    if any(type(item) is not Fraction for item in value.count_marginal_probabilities):
        raise TypeError(
            "derivation count_marginal_probabilities entries must be exact Fractions"
        )
    components = _derive_components(
        value.activity,
        value.type_weights,
        value.count_vectors,
        value.total_cap,
    )
    (
        state_components,
        raw_normalizer,
        capped_series_normalizer,
        base_masses,
        count_raw_masses,
        count_probabilities,
    ) = components
    for index, (state, expected) in enumerate(zip(value.states, state_components)):
        state.__post_init__()
        (
            total_count,
            activity_power,
            weight_product,
            multiplicity,
            raw_mass,
            count_raw,
            coefficient,
            conditional,
            alternative_raw,
        ) = expected
        expected_values = (
            index,
            value.support_labels[index],
            value.count_vectors[index],
            total_count,
            activity_power,
            weight_product,
            multiplicity,
            raw_mass,
            count_raw,
            coefficient,
            conditional,
            alternative_raw,
            base_masses[index],
            alternative_raw / raw_normalizer,
        )
        actual_values = tuple(getattr(state, field.name) for field in fields(state))
        if actual_values != expected_values:
            raise ValueError("derivation state[%d] differs" % index)
    for name, actual, expected in (
        (
            "raw_normalizer_by_support_sum",
            value.raw_normalizer_by_support_sum,
            raw_normalizer,
        ),
        (
            "raw_normalizer_by_capped_count_series",
            value.raw_normalizer_by_capped_count_series,
            capped_series_normalizer,
        ),
    ):
        checked = _require_fraction(actual, name="derivation " + name, positive=True)
        if checked != expected:
            raise ValueError("derivation " + name + " differs")
    if value.base_masses != base_masses:
        raise ValueError("derivation base_masses differ from the primitive inputs")
    if value.count_raw_masses != count_raw_masses:
        raise ValueError("derivation count_raw_masses differ")
    if value.count_marginal_probabilities != count_probabilities:
        raise ValueError("derivation count_marginal_probabilities differ")
    if sum(value.base_masses, Fraction(0, 1)) != _ONE:
        raise ValueError("derivation base_masses do not normalize exactly")
    if sum(value.count_marginal_probabilities, Fraction(0, 1)) != _ONE:
        raise ValueError("derivation count marginals do not normalize exactly")
    for name, actual, expected in (
        ("formula_sha256", value.formula_sha256, CP54_TEST28_FACTORIAL_FORMULA_SHA256),
        (
            "parameter_sha256",
            value.parameter_sha256,
            _parameter_digest(
                value.parameter_layer, value.activity, value.type_weights
            ),
        ),
        (
            "support_sha256",
            value.support_sha256,
            _support_digest(
                value.fixture_id,
                value.total_cap,
                value.type_labels,
                value.event_dimensions,
                value.support_labels,
                value.count_vectors,
            ),
        ),
    ):
        _require_sha256(actual, name="derivation " + name)
        if actual != expected:
            raise ValueError("derivation " + name + " differs")
    if any(
        flag is not True
        for flag in (
            value.complete_support_verified,
            value.type_weights_normalized_exactly,
            value.multiplicity_factorials_used_exactly_once,
            value.support_and_count_routes_agree,
            value.analytic_base_measure_only,
        )
    ):
        raise ValueError("derivation required exact-identity flags differ")
    if value.extra_total_count_factorial_used is not False:
        raise ValueError("derivation must not use an extra total-count factorial")
    expected_ideal_flag = value.parameter_layer == "ideal_rational"
    expected_binary64_flag = value.parameter_layer == "binary64_parameter"
    if value.ideal_rational_parameter_reference is not expected_ideal_flag:
        raise ValueError("derivation ideal-rational layer flag differs")
    if value.stored_binary64_parameter_values_only is not expected_binary64_flag:
        raise ValueError("derivation binary64-parameter layer flag differs")
    if any(
        flag is not False
        for flag in (
            value.operational_reference_sampler_law_claim,
            value.operational_mu_fp_identified,
            value.runtime_source_or_rng_law_verified,
            value.target_tilt_or_score_applied,
            value.formal_test28_evidence,
            value.confirmatory_evidence,
            value.manuscript_claim,
        )
    ):
        raise ValueError(
            "derivation contains a forbidden operational or evidence claim"
        )
    _require_sha256(value.record_sha256, name="derivation record_sha256")
    if value.record_sha256 != _derivation_digest(value):
        raise ValueError("derivation record digest differs")


def _make_derivation(
    *,
    fixture_id: str,
    parameter_layer: str,
    activity: Fraction,
    type_labels: Tuple[str, ...],
    type_weights: Tuple[Fraction, ...],
    event_dimensions: Tuple[int, ...],
    support_labels: Tuple[str, ...],
    count_vectors: Tuple[Tuple[int, ...], ...],
    total_cap: int,
) -> CapTwoFactorialDerivation:
    components = _derive_components(
        activity,
        type_weights,
        count_vectors,
        total_cap,
    )
    (
        state_components,
        raw_normalizer,
        capped_series_normalizer,
        base_masses,
        count_raw_masses,
        count_probabilities,
    ) = components
    states = tuple(
        FactorialStateDerivation(
            support_index=index,
            support_label=support_labels[index],
            count_vector=count_vectors[index],
            total_count=values[0],
            activity_power=values[1],
            type_weight_power_product=values[2],
            multiplicity_factorial_product=values[3],
            raw_mass_from_product_formula=values[4],
            count_raw_mass=values[5],
            multinomial_coefficient=values[6],
            conditional_multinomial_probability=values[7],
            raw_mass_via_count_multinomial=values[8],
            normalized_base_mass=base_masses[index],
            normalized_base_mass_via_count_multinomial=(values[8] / raw_normalizer),
        )
        for index, values in enumerate(state_components)
    )
    values = {
        "schema_version": CP54_TEST28_FACTORIAL_DERIVATION_SCHEMA_VERSION,
        "fixture_id": fixture_id,
        "parameter_layer": parameter_layer,
        "formula_id": CP54_TEST28_FACTORIAL_FORMULA_ID,
        "formula_statement": CP54_TEST28_FACTORIAL_FORMULA_STATEMENT,
        "no_extra_total_factorial_statement": (
            CP54_TEST28_NO_EXTRA_FACTORIAL_STATEMENT
        ),
        "independent_route_statement": CP54_TEST28_INDEPENDENT_ROUTE_STATEMENT,
        "event_dimension_scope_statement": (
            CP54_TEST28_EVENT_DIMENSION_SCOPE_STATEMENT
        ),
        "activity": activity,
        "total_cap": total_cap,
        "type_labels": type_labels,
        "type_weights": type_weights,
        "event_dimensions": event_dimensions,
        "support_labels": support_labels,
        "count_vectors": count_vectors,
        "states": states,
        "raw_normalizer_by_support_sum": raw_normalizer,
        "raw_normalizer_by_capped_count_series": capped_series_normalizer,
        "base_masses": base_masses,
        "count_raw_masses": count_raw_masses,
        "count_marginal_probabilities": count_probabilities,
        "formula_sha256": CP54_TEST28_FACTORIAL_FORMULA_SHA256,
        "parameter_sha256": _parameter_digest(
            parameter_layer,
            activity,
            type_weights,
        ),
        "support_sha256": _support_digest(
            fixture_id,
            total_cap,
            type_labels,
            event_dimensions,
            support_labels,
            count_vectors,
        ),
        "complete_support_verified": True,
        "type_weights_normalized_exactly": True,
        "multiplicity_factorials_used_exactly_once": True,
        "extra_total_count_factorial_used": False,
        "support_and_count_routes_agree": True,
        "analytic_base_measure_only": True,
        "ideal_rational_parameter_reference": parameter_layer == "ideal_rational",
        "stored_binary64_parameter_values_only": (
            parameter_layer == "binary64_parameter"
        ),
        "operational_reference_sampler_law_claim": False,
        "operational_mu_fp_identified": False,
        "runtime_source_or_rng_law_verified": False,
        "target_tilt_or_score_applied": False,
        "formal_test28_evidence": False,
        "confirmatory_evidence": False,
        "manuscript_claim": False,
        "record_sha256": "0" * 64,
    }
    provisional = CapTwoFactorialDerivation.__new__(CapTwoFactorialDerivation)
    for name, item in values.items():
        object.__setattr__(provisional, name, item)
    values["record_sha256"] = _derivation_digest(provisional)
    return CapTwoFactorialDerivation(**values)


def derive_cap_two_factorial_reference(
    *,
    fixture_id: str,
    parameter_layer: str,
    activity: Fraction,
    type_labels: Tuple[str, ...],
    type_weights: Tuple[Fraction, ...],
    event_dimensions: Tuple[int, ...],
    support_labels: Tuple[str, ...],
    count_vectors: Tuple[Tuple[int, ...], ...],
    total_cap: int,
) -> CapTwoFactorialDerivation:
    """Derive one frozen analytic base measure from exact primitive inputs.

    The signature intentionally has no target, base-mass, normalizer, or
    probability-vector argument.  All such outputs are recomputed exactly.
    """

    _preflight_derivation_inputs(
        fixture_id=fixture_id,
        parameter_layer=parameter_layer,
        activity=activity,
        type_labels=type_labels,
        type_weights=type_weights,
        event_dimensions=event_dimensions,
        support_labels=support_labels,
        count_vectors=count_vectors,
        total_cap=total_cap,
    )
    _validate_canonical_inputs(
        fixture_id=fixture_id,
        parameter_layer=parameter_layer,
        activity=activity,
        type_labels=type_labels,
        type_weights=type_weights,
        event_dimensions=event_dimensions,
        support_labels=support_labels,
        count_vectors=count_vectors,
        total_cap=total_cap,
    )
    return _make_derivation(
        fixture_id=fixture_id,
        parameter_layer=parameter_layer,
        activity=activity,
        type_labels=type_labels,
        type_weights=type_weights,
        event_dimensions=event_dimensions,
        support_labels=support_labels,
        count_vectors=count_vectors,
        total_cap=total_cap,
    )


def _fixture_layer_derivation(
    fixture_id: str,
    parameter_layer: str,
) -> CapTwoFactorialDerivation:
    type_labels, event_dimensions, support_labels = _expected_fixture_fields(fixture_id)
    activity, type_weights = _expected_parameters(parameter_layer)
    return derive_cap_two_factorial_reference(
        fixture_id=fixture_id,
        parameter_layer=parameter_layer,
        activity=activity,
        type_labels=type_labels,
        type_weights=type_weights,
        event_dimensions=event_dimensions,
        support_labels=support_labels,
        count_vectors=_COUNT_VECTORS,
        total_cap=MAX_CP54_TEST28_TOTAL_CAP,
    )


def _make_pair(fixture_id: str) -> FixtureFactorialDerivationPair:
    ideal = _fixture_layer_derivation(fixture_id, "ideal_rational")
    binary64 = _fixture_layer_derivation(fixture_id, "binary64_parameter")
    values = {
        "schema_version": CP54_TEST28_FACTORIAL_DERIVATION_SCHEMA_VERSION,
        "fixture_id": fixture_id,
        "ideal_rational": ideal,
        "binary64_parameter": binary64,
        "common_support_sha256": ideal.support_sha256,
        "parameter_records_distinct": True,
        "base_mass_vectors_distinct": True,
        "analytic_base_measure_only": True,
        "operational_reference_sampler_law_claim": False,
        "operational_mu_fp_identified": False,
        "runtime_source_or_rng_law_verified": False,
        "target_tilt_or_score_applied": False,
        "formal_test28_evidence": False,
        "confirmatory_evidence": False,
        "manuscript_claim": False,
        "record_sha256": "0" * 64,
    }
    provisional = FixtureFactorialDerivationPair.__new__(FixtureFactorialDerivationPair)
    for name, item in values.items():
        object.__setattr__(provisional, name, item)
    values["record_sha256"] = _pair_digest(provisional)
    return FixtureFactorialDerivationPair(**values)


def t28_a0_h_factorial_derivations() -> FixtureFactorialDerivationPair:
    """Return exact analytic base-measure derivations for ``T28-A0-H``."""

    return _make_pair("T28-A0-H")


def t28_m2_q_factorial_derivations() -> FixtureFactorialDerivationPair:
    """Return exact analytic base-measure derivations for ``T28-M2-Q``."""

    return _make_pair("T28-M2-Q")


def factorial_derivation_record_sha256(
    value: CapTwoFactorialDerivation,
) -> str:
    """Validate and return the canonical digest of one derivation record."""

    if type(value) is not CapTwoFactorialDerivation:
        raise TypeError("value must be an exact CapTwoFactorialDerivation")
    value.__post_init__()
    return _derivation_digest(value)


def factorial_derivation_pair_sha256(
    value: FixtureFactorialDerivationPair,
) -> str:
    """Validate and return the canonical digest of a paired fixture record."""

    if type(value) is not FixtureFactorialDerivationPair:
        raise TypeError("value must be an exact FixtureFactorialDerivationPair")
    value.__post_init__()
    return _pair_digest(value)


__all__ = (
    "CP54_TEST28_FACTORIAL_DERIVATION_SCHEMA_VERSION",
    "CP54_TEST28_FACTORIAL_FORMULA_ID",
    "CP54_TEST28_FACTORIAL_FORMULA_STATEMENT",
    "CP54_TEST28_NO_EXTRA_FACTORIAL_STATEMENT",
    "CP54_TEST28_INDEPENDENT_ROUTE_STATEMENT",
    "CP54_TEST28_EVENT_DIMENSION_SCOPE_STATEMENT",
    "CP54_TEST28_FACTORIAL_FORMULA_SHA256",
    "CP54_TEST28_FACTORIAL_DERIVATION_SCOPE",
    "CP54_TEST28_FACTORIAL_DERIVATION_NONCLAIMS",
    "MAX_CP54_TEST28_EXACT_INTEGER_BITS",
    "MAX_CP54_TEST28_TEXT_LENGTH",
    "MAX_CP54_TEST28_TYPES",
    "MAX_CP54_TEST28_TOTAL_CAP",
    "MAX_CP54_TEST28_SUPPORT_STATES",
    "FactorialStateDerivation",
    "CapTwoFactorialDerivation",
    "FixtureFactorialDerivationPair",
    "derive_cap_two_factorial_reference",
    "t28_a0_h_factorial_derivations",
    "t28_m2_q_factorial_derivations",
    "factorial_derivation_record_sha256",
    "factorial_derivation_pair_sha256",
)
