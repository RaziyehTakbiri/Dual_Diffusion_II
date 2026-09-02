"""Pure generic reference for count-normalized-event kernel scoring.

This module implements the finite-alphabet specialization of the independently
proved count-normalized-event CKS construction.  It deliberately accepts every
semantic input from its caller.  In particular, it contains no domain event
schema, embedding, cap, scale, bandwidth, draw count, data reader, random
source, project-science import, or result writer.

The caller supplies a finite event alphabet and an exact rational Gram matrix.
The matrix must be positive semidefinite and characteristic on probability
measures over that alphabet.  The latter condition is checked exactly by
requiring strict positive definiteness on the zero-sum subspace.  A positive
count channel is orthogonal to the normalized event-mean channel.  The outer
configuration kernel is Gaussian.  Conditional on caller-supplied draws being
i.i.d. from one predictive law, ``conditional_cks_u_statistic`` is the usual
off-diagonal unbiased estimator of

    E k(X,X') - 2 E k(X,y),

and therefore uses the lower-is-better loss convention.  The module cannot and
does not establish that the supplied draws satisfy that conditional premise.

This is a generic reference implementation, not a domain metric instance and
not scientific execution.  Kernel values are canonical symbolic descriptors
``exp(-q)`` with exact nonnegative rational ``q``.  Scores are canonical formal
linear combinations of those descriptors with exact rational coefficients.
No binary64 value participates in identity, positive-definiteness, strict-
propriety, or score claims.  Explicit diagnostics show why such a conversion
would be unsafe near one.

Score construction supports valid caller inputs with ``2 <= R <= 128``.
``build_reference_report`` is a separate partial operation over that score
domain.  If it raises ``CKSReportResourceError`` after its internal score
construction, the refusal does not invalidate a formal score previously
returned by the separate score API.  A standalone ``report_sha256`` resource
refusal makes no statement about whether any score input is valid.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from typing import Any, Dict, Mapping, Tuple


SCHEMA_VERSION = "heterodiff-generic-count-normalized-event-cks-reference-v1"
CONTROL_PREDICATE = (
    "GENERIC_CKS_COUNT_NORMALIZED_EVENT_REFERENCE_IMPLEMENTATION_VALIDATED"
)
SCORE_DIRECTION = "LOWER_IS_BETTER"
CONDITIONAL_PREMISE = (
    "CALLER_SUPPLIED_WITHIN_METHOD_DRAWS_ARE_CONDITIONALLY_IID;"
    "THIS_REFERENCE_DOES_NOT_TEST_OR_ASSERT_THAT PREMISE"
)

MAX_ALPHABET_SIZE = 16
MAX_CONFIGURATION_CAP = 64
MAX_CONDITIONAL_DRAWS = 128
MAX_TOKEN_BYTES = 64
MAX_INPUT_COMPONENT_BITS = 256
MAX_DERIVED_COMPONENT_BITS = 8192
MAX_REPORT_BYTES = 1_000_000
MAX_REPORT_JSON_DEPTH = 24
MAX_REPORT_JSON_NODES = 10_000
MAX_REPORT_CONTAINER_ITEMS = 4_096
MAX_REPORT_TEXT_BYTES = 4_096
MAX_REPORT_INTEGER_BITS = 8_192


class CKSReferenceError(ValueError):
    """Raised when a generic reference input violates the frozen contract."""


class CKSReportResourceError(CKSReferenceError):
    """A report graph or generated report exceeds bounded report-resource admission."""


def _exact_int(value: object, *, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact built-in integer")
    checked = value
    if checked < minimum or checked > maximum:
        raise CKSReferenceError(name + " lies outside its bounded range")
    return checked


def _bounded_fraction(value: Fraction, *, name: str, derived: bool) -> Fraction:
    bound = MAX_DERIVED_COMPONENT_BITS if derived else MAX_INPUT_COMPONENT_BITS
    if (
        value.numerator.bit_length() > bound
        or value.denominator.bit_length() > bound
    ):
        raise CKSReferenceError(name + " exceeds the exact component bound")
    return value


def _exact_fraction(value: object, *, name: str) -> Fraction:
    if type(value) is int:
        checked = Fraction(value, 1)
    elif type(value) is Fraction:
        checked = value
    else:
        raise TypeError(name + " must be an exact built-in int or Fraction")
    return _bounded_fraction(checked, name=name, derived=False)


def _exact_derived_fraction(value: object, *, name: str) -> Fraction:
    if type(value) is int:
        checked = Fraction(value, 1)
    elif type(value) is Fraction:
        checked = value
    else:
        raise TypeError(name + " must be an exact built-in int or Fraction")
    return _bounded_fraction(checked, name=name, derived=True)


def _positive_fraction(value: object, *, name: str) -> Fraction:
    checked = _exact_fraction(value, name=name)
    if checked <= 0:
        raise CKSReferenceError(name + " must be strictly positive")
    return checked


def _strict_token(value: object, *, name: str) -> str:
    if type(value) is not str or not value:
        raise TypeError(name + " must be exact nonempty text")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as error:
        raise CKSReferenceError(name + " must be ASCII") from error
    if len(encoded) > MAX_TOKEN_BYTES:
        raise CKSReferenceError(name + " exceeds the token byte bound")
    if any(byte < 0x21 or byte > 0x7E for byte in encoded):
        raise CKSReferenceError(name + " must be printable ASCII without whitespace")
    return value


def _strict_positive_definite(matrix: Tuple[Tuple[Fraction, ...], ...]) -> bool:
    """Exact LDL test for a symmetric strictly positive-definite matrix."""

    size = len(matrix)
    if size == 0:
        return True
    lower = [[Fraction(0, 1) for _ in range(size)] for _ in range(size)]
    diagonal = [Fraction(0, 1) for _ in range(size)]
    for column in range(size):
        pivot = matrix[column][column]
        for prior in range(column):
            pivot -= lower[column][prior] ** 2 * diagonal[prior]
        _bounded_fraction(pivot, name="characteristic-subspace pivot", derived=True)
        if pivot <= 0:
            return False
        diagonal[column] = pivot
        lower[column][column] = Fraction(1, 1)
        for row in range(column + 1, size):
            residual = matrix[row][column]
            for prior in range(column):
                residual -= (
                    lower[row][prior]
                    * lower[column][prior]
                    * diagonal[prior]
                )
            lower[row][column] = _bounded_fraction(
                residual / pivot,
                name="characteristic-subspace LDL coefficient",
                derived=True,
            )
    return True


def _positive_semidefinite(matrix: Tuple[Tuple[Fraction, ...], ...]) -> bool:
    """Exact symmetric Schur-complement test, including singular matrices."""

    work = [list(row) for row in matrix]
    while work:
        size = len(work)
        for index in range(size):
            if work[index][index] < 0:
                return False
        pivot_index = next(
            (index for index in range(size) if work[index][index] > 0), None
        )
        if pivot_index is None:
            return all(value == 0 for row in work for value in row)
        if pivot_index != 0:
            work[0], work[pivot_index] = work[pivot_index], work[0]
            for row in work:
                row[0], row[pivot_index] = row[pivot_index], row[0]
        pivot = work[0][0]
        reduced = []
        for row in range(1, size):
            reduced_row = []
            for column in range(1, size):
                value = work[row][column] - work[row][0] * work[0][column] / pivot
                reduced_row.append(
                    _bounded_fraction(
                        value, name="positive-semidefinite Schur entry", derived=True
                    )
                )
            reduced.append(reduced_row)
        work = reduced
    return True


@dataclass(frozen=True)
class FiniteCKSSpec:
    """Caller-supplied generic finite-alphabet CKS instance.

    ``event_gram`` may be singular on the full vector space, but it must be
    positive semidefinite and strictly positive on every nonzero zero-sum
    vector.  That is exactly the finite-alphabet form of characteristicness on
    probability measures.  No domain interpretation attaches to ``symbols``.
    """

    symbols: Tuple[str, ...]
    event_gram: Tuple[Tuple[Fraction, ...], ...]
    configuration_cap: int
    count_scale_squared: Fraction
    event_scale_squared: Fraction
    outer_bandwidth_squared: Fraction

    def __post_init__(self) -> None:
        if type(self.symbols) is not tuple:
            raise TypeError("spec.symbols must be an exact tuple")
        if not self.symbols or len(self.symbols) > MAX_ALPHABET_SIZE:
            raise CKSReferenceError("spec.symbols has invalid bounded cardinality")
        symbols = tuple(
            _strict_token(symbol, name="spec.symbols[%d]" % index)
            for index, symbol in enumerate(self.symbols)
        )
        if len(set(symbols)) != len(symbols):
            raise CKSReferenceError("spec.symbols must be unique")
        if type(self.event_gram) is not tuple or len(self.event_gram) != len(symbols):
            raise TypeError("spec.event_gram must be an exact square tuple")
        rows = []
        for row_index, row in enumerate(self.event_gram):
            if type(row) is not tuple or len(row) != len(symbols):
                raise TypeError("spec.event_gram rows must be exact square tuples")
            rows.append(
                tuple(
                    _exact_fraction(
                        value,
                        name="spec.event_gram[%d][%d]" % (row_index, column_index),
                    )
                    for column_index, value in enumerate(row)
                )
            )
        gram = tuple(rows)
        for row in range(len(gram)):
            for column in range(row + 1, len(gram)):
                if gram[row][column] != gram[column][row]:
                    raise CKSReferenceError("spec.event_gram must be exactly symmetric")
        if not _positive_semidefinite(gram):
            raise CKSReferenceError("spec.event_gram must be positive semidefinite")

        if len(gram) > 1:
            anchor = len(gram) - 1
            zero_sum_gram = tuple(
                tuple(
                    gram[row][column]
                    - gram[row][anchor]
                    - gram[anchor][column]
                    + gram[anchor][anchor]
                    for column in range(anchor)
                )
                for row in range(anchor)
            )
            if not _strict_positive_definite(zero_sum_gram):
                raise CKSReferenceError(
                    "spec.event_gram is not characteristic on event probabilities"
                )

        cap = _exact_int(
            self.configuration_cap,
            name="spec.configuration_cap",
            minimum=1,
            maximum=MAX_CONFIGURATION_CAP,
        )
        count_scale = _positive_fraction(
            self.count_scale_squared, name="spec.count_scale_squared"
        )
        event_scale = _positive_fraction(
            self.event_scale_squared, name="spec.event_scale_squared"
        )
        bandwidth = _positive_fraction(
            self.outer_bandwidth_squared, name="spec.outer_bandwidth_squared"
        )
        object.__setattr__(self, "symbols", symbols)
        object.__setattr__(self, "event_gram", gram)
        object.__setattr__(self, "configuration_cap", cap)
        object.__setattr__(self, "count_scale_squared", count_scale)
        object.__setattr__(self, "event_scale_squared", event_scale)
        object.__setattr__(self, "outer_bandwidth_squared", bandwidth)


@dataclass(frozen=True)
class DistanceBreakdown:
    left_count: int
    right_count: int
    count_channel_squared: Fraction
    event_channel_squared: Fraction
    combined_squared: Fraction
    same_counting_measure: bool


@dataclass(frozen=True)
class GaussianValue:
    """Authoritative symbolic value ``exp(-exponent)``."""

    exponent: Fraction

    def __post_init__(self) -> None:
        exponent = _exact_derived_fraction(self.exponent, name="Gaussian exponent")
        if exponent < 0:
            raise CKSReferenceError("Gaussian exponent must be nonnegative")
        object.__setattr__(self, "exponent", exponent)


@dataclass(frozen=True)
class GaussianTerm:
    """One exact coefficient times one authoritative Gaussian descriptor."""

    exponent: Fraction
    coefficient: Fraction

    def __post_init__(self) -> None:
        exponent = _exact_derived_fraction(
            self.exponent, name="Gaussian term exponent"
        )
        coefficient = _exact_derived_fraction(
            self.coefficient, name="Gaussian term coefficient"
        )
        if exponent < 0:
            raise CKSReferenceError("Gaussian term exponent must be nonnegative")
        if coefficient == 0:
            raise CKSReferenceError("Gaussian term coefficient must be nonzero")
        object.__setattr__(self, "exponent", exponent)
        object.__setattr__(self, "coefficient", coefficient)


@dataclass(frozen=True)
class FormalGaussianCombination:
    """Canonical exact formal linear combination of ``exp(-q)`` terms."""

    terms: Tuple[GaussianTerm, ...]

    def __post_init__(self) -> None:
        if type(self.terms) is not tuple:
            raise TypeError("formal Gaussian terms must be an exact tuple")
        checked = []
        for index, term in enumerate(self.terms):
            if type(term) is not GaussianTerm:
                raise TypeError(
                    "formal Gaussian term %d must have the exact GaussianTerm type"
                    % index
                )
            checked.append(
                GaussianTerm(
                    exponent=term.exponent,
                    coefficient=term.coefficient,
                )
            )
        checked_tuple = tuple(checked)
        if checked_tuple != tuple(sorted(checked_tuple, key=lambda item: item.exponent)):
            raise CKSReferenceError("formal Gaussian terms must be exponent-sorted")
        if len({term.exponent for term in checked_tuple}) != len(checked_tuple):
            raise CKSReferenceError("formal Gaussian exponents must be unique")
        object.__setattr__(self, "terms", checked_tuple)


@dataclass(frozen=True)
class ConditionalCKSScore:
    draw_count: int
    off_diagonal_kernel_values: Tuple[GaussianValue, ...]
    target_kernel_values: Tuple[GaussianValue, ...]
    formal_loss: FormalGaussianCombination
    score_direction: str
    conditional_iid_premise_asserted_by_reference: bool


def _revalidated_spec(spec: object) -> FiniteCKSSpec:
    """Re-run every constructor invariant at each public consumption boundary.

    Frozen dataclasses can still be corrupted through low-level attribute
    replacement.  Public functions therefore never trust prior construction.
    Reconstructing also rejects subclasses and bool-as-int substitutions.
    """

    if type(spec) is not FiniteCKSSpec:
        raise TypeError("spec must be an exact FiniteCKSSpec")
    return FiniteCKSSpec(
        symbols=spec.symbols,
        event_gram=spec.event_gram,
        configuration_cap=spec.configuration_cap,
        count_scale_squared=spec.count_scale_squared,
        event_scale_squared=spec.event_scale_squared,
        outer_bandwidth_squared=spec.outer_bandwidth_squared,
    )


def _configuration_counts(
    configuration: object, spec: FiniteCKSSpec, *, name: str
) -> Tuple[int, ...]:
    if type(configuration) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if len(configuration) > spec.configuration_cap:
        raise CKSReferenceError(name + " exceeds spec.configuration_cap")
    positions = {symbol: index for index, symbol in enumerate(spec.symbols)}
    counts = [0 for _ in spec.symbols]
    for ordinal, event in enumerate(configuration):
        token = _strict_token(event, name=name + "[%d]" % ordinal)
        if token not in positions:
            raise CKSReferenceError(name + " contains an event outside spec.symbols")
        index = positions[token]
        counts[index] += 1
    return tuple(counts)


def _mean_inner(
    left_counts: Tuple[int, ...],
    right_counts: Tuple[int, ...],
    left_total: int,
    right_total: int,
    gram: Tuple[Tuple[Fraction, ...], ...],
) -> Fraction:
    if left_total == 0 or right_total == 0:
        return Fraction(0, 1)
    numerator = Fraction(0, 1)
    for row, left_count in enumerate(left_counts):
        if left_count == 0:
            continue
        for column, right_count in enumerate(right_counts):
            if right_count:
                numerator += left_count * right_count * gram[row][column]
    result = numerator / (left_total * right_total)
    return _bounded_fraction(result, name="normalized event-mean inner product", derived=True)


def configuration_distance(
    spec: FiniteCKSSpec, left: object, right: object
) -> DistanceBreakdown:
    """Return the exact squared direct-sum distance between configurations."""

    checked_spec = _revalidated_spec(spec)
    left_counts = _configuration_counts(left, checked_spec, name="left")
    right_counts = _configuration_counts(right, checked_spec, name="right")
    left_total = sum(left_counts)
    right_total = sum(right_counts)
    count_term = checked_spec.count_scale_squared * (left_total - right_total) ** 2
    left_self = _mean_inner(
        left_counts, left_counts, left_total, left_total, checked_spec.event_gram
    )
    right_self = _mean_inner(
        right_counts, right_counts, right_total, right_total, checked_spec.event_gram
    )
    cross = _mean_inner(
        left_counts, right_counts, left_total, right_total, checked_spec.event_gram
    )
    event_base = _bounded_fraction(
        left_self + right_self - 2 * cross,
        name="normalized event-mean squared distance",
        derived=True,
    )
    if event_base < 0:
        raise CKSReferenceError("validated event Gram produced a negative distance")
    event_term = _bounded_fraction(
        checked_spec.event_scale_squared * event_base,
        name="scaled normalized event-mean squared distance",
        derived=True,
    )
    combined = _bounded_fraction(
        count_term + event_term,
        name="combined configuration squared distance",
        derived=True,
    )
    same = left_counts == right_counts
    if (combined == 0) is not same:
        raise CKSReferenceError("configuration injection invariant failed")
    return DistanceBreakdown(
        left_count=left_total,
        right_count=right_total,
        count_channel_squared=count_term,
        event_channel_squared=event_term,
        combined_squared=combined,
        same_counting_measure=same,
    )


def configuration_kernel(
    spec: FiniteCKSSpec, left: object, right: object
) -> GaussianValue:
    """Return the authoritative exact descriptor ``exp(-q)``."""

    checked_spec = _revalidated_spec(spec)
    distance = configuration_distance(checked_spec, left, right).combined_squared
    exponent_magnitude = distance / (2 * checked_spec.outer_bandwidth_squared)
    exponent_magnitude = _bounded_fraction(
        exponent_magnitude, name="outer Gaussian exponent", derived=True
    )
    return GaussianValue(exponent=exponent_magnitude)


def _canonical_formal_combination(
    contributions: Tuple[Tuple[GaussianValue, Fraction], ...]
) -> FormalGaussianCombination:
    coefficients: Dict[Fraction, Fraction] = {}
    for index, (value, coefficient) in enumerate(contributions):
        if type(value) is not GaussianValue:
            raise TypeError(
                "formal contribution %d must contain an exact GaussianValue" % index
            )
        checked_value = GaussianValue(exponent=value.exponent)
        checked_coefficient = _exact_derived_fraction(
            coefficient, name="formal contribution coefficient"
        )
        updated = coefficients.get(checked_value.exponent, Fraction(0, 1))
        updated += checked_coefficient
        coefficients[checked_value.exponent] = _bounded_fraction(
            updated, name="combined formal coefficient", derived=True
        )
    terms = tuple(
        GaussianTerm(exponent=exponent, coefficient=coefficient)
        for exponent, coefficient in sorted(coefficients.items())
        if coefficient != 0
    )
    return FormalGaussianCombination(terms=terms)


def conditional_cks_u_statistic(
    spec: FiniteCKSSpec, draws: object, target: object
) -> ConditionalCKSScore:
    """Compute the lower-is-better off-diagonal conditional CKS estimate.

    At least two draws are required.  The estimator is unbiased only under the
    caller-owned conditional-i.i.d. premise documented at module level.
    """

    checked_spec = _revalidated_spec(spec)
    if type(draws) is not tuple:
        raise TypeError("draws must be an exact tuple")
    draw_count = len(draws)
    if draw_count < 2 or draw_count > MAX_CONDITIONAL_DRAWS:
        raise CKSReferenceError("draws must contain between 2 and 128 configurations")
    _configuration_counts(target, checked_spec, name="target")
    for ordinal, draw in enumerate(draws):
        _configuration_counts(draw, checked_spec, name="draws[%d]" % ordinal)

    off_diagonal = []
    for left in range(draw_count):
        for right in range(left + 1, draw_count):
            off_diagonal.append(
                configuration_kernel(checked_spec, draws[left], draws[right])
            )
    target_values = [
        configuration_kernel(checked_spec, draw, target) for draw in draws
    ]
    off_diagonal_values = tuple(sorted(off_diagonal, key=lambda value: value.exponent))
    target_kernel_values = tuple(
        sorted(target_values, key=lambda value: value.exponent)
    )
    self_coefficient = Fraction(2, draw_count * (draw_count - 1))
    target_coefficient = Fraction(-2, draw_count)
    contributions = tuple(
        (value, self_coefficient) for value in off_diagonal_values
    ) + tuple((value, target_coefficient) for value in target_kernel_values)
    formal_loss = _canonical_formal_combination(contributions)
    return ConditionalCKSScore(
        draw_count=draw_count,
        off_diagonal_kernel_values=off_diagonal_values,
        target_kernel_values=target_kernel_values,
        formal_loss=formal_loss,
        score_direction=SCORE_DIRECTION,
        conditional_iid_premise_asserted_by_reference=False,
    )


def _fraction_record(value: Fraction) -> Dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _gaussian_value_record(value: GaussianValue) -> Dict[str, Any]:
    if type(value) is not GaussianValue:
        raise TypeError("Gaussian record input must have exact GaussianValue type")
    checked = GaussianValue(exponent=value.exponent)
    return {
        "kind": "EXACT_SYMBOLIC_EXP_NEGATIVE_RATIONAL",
        "exponent": _fraction_record(checked.exponent),
    }


def _formal_combination_record(
    value: FormalGaussianCombination,
) -> Dict[str, Any]:
    if type(value) is not FormalGaussianCombination:
        raise TypeError(
            "formal combination record input must have exact FormalGaussianCombination type"
        )
    checked = FormalGaussianCombination(terms=value.terms)
    return {
        "kind": "CANONICAL_EXACT_FORMAL_LINEAR_COMBINATION_OF_EXP_NEGATIVE_RATIONAL",
        "terms": [
            {
                "coefficient": _fraction_record(term.coefficient),
                "exponent": _fraction_record(term.exponent),
            }
            for term in checked.terms
        ],
        "equal_exponents_combined": True,
        "zero_coefficients_removed": True,
        "denotation": "EXACT_REAL_SUM_OF_COEFFICIENT_TIMES_EXP_NEGATIVE_EXPONENT",
        "numerical_value_provided": False,
        "numeric_order_sign_or_comparison_computed": False,
    }


def _canonical_configuration(
    configuration: object, spec: FiniteCKSSpec, *, name: str
) -> Tuple[Tuple[str, int], ...]:
    counts = _configuration_counts(configuration, spec, name=name)
    return tuple(
        (symbol, counts[index])
        for index, symbol in enumerate(spec.symbols)
        if counts[index]
    )


def _spec_record(spec: FiniteCKSSpec) -> Dict[str, Any]:
    return {
        "symbols": list(spec.symbols),
        "event_gram": [
            [_fraction_record(value) for value in row] for row in spec.event_gram
        ],
        "configuration_cap": spec.configuration_cap,
        "count_scale_squared": _fraction_record(spec.count_scale_squared),
        "event_scale_squared": _fraction_record(spec.event_scale_squared),
        "outer_bandwidth_squared": _fraction_record(
            spec.outer_bandwidth_squared
        ),
        "event_gram_psd": True,
        "event_probability_mean_map_characteristic": True,
    }


def raw_formula_counterexamples() -> Dict[str, Any]:
    """Return exact witnesses against the raw formula and count-channel drop.

    On ``{u,v}``, the rank-one feature ``g(u)=1, g(v)=2`` is characteristic on
    event probability measures, yet the raw unnormalized means of ``2 delta_u``
    and ``delta_v`` both equal two.  Separately, normalized event means of
    ``delta_u`` and ``2 delta_u`` coincide, so a positive count channel is
    indispensable.
    """

    return {
        "event_space": ["u", "v"],
        "rank_one_feature": {"u": 1, "v": 2},
        "characteristic_on_event_probabilities": True,
        "raw_unnormalized_collision": {
            "left": [["u", 2]],
            "right": [["v", 1]],
            "left_raw_mean": _fraction_record(Fraction(2, 1)),
            "right_raw_mean": _fraction_record(Fraction(2, 1)),
            "raw_squared_distance": _fraction_record(Fraction(0, 1)),
            "corrected_count_channel_squared_at_unit_scale": _fraction_record(
                Fraction(1, 1)
            ),
            "corrected_normalized_event_channel_squared_at_unit_scale": (
                _fraction_record(Fraction(1, 1))
            ),
        },
        "drop_count_collision": {
            "left": [["u", 1]],
            "right": [["u", 2]],
            "normalized_event_squared_distance": _fraction_record(Fraction(0, 1)),
            "count_channel_squared_at_unit_scale": _fraction_record(Fraction(1, 1)),
        },
        "scientific_result": False,
    }


def binary64_failure_witnesses() -> Dict[str, Any]:
    """Exact diagnostics explaining why binary64 kernel values are not used.

    The listed binary64 values are represented by their exact rational values
    and hexadecimal encodings.  They are nonauthoritative counterexamples, not
    outputs used by the reference score.
    """

    collapse_exponent = Fraction(1, 1 << 60)
    near_exponent = Fraction(1, 1 << 40)
    far_exponent = Fraction(1, 1 << 38)
    near_binary = Fraction((1 << 40) - 1, 1 << 40)
    far_binary = Fraction((1 << 38) - 1, 1 << 38)
    rounded_determinant = (
        Fraction(1, 1)
        + 2 * near_binary * near_binary * far_binary
        - near_binary * near_binary
        - near_binary * near_binary
        - far_binary * far_binary
    )
    if rounded_determinant != Fraction(
        -1, 166153499473114484112975882535043072
    ):
        raise CKSReferenceError("binary64 Gram witness determinant invariant failed")
    return {
        "binary64_values_nonauthoritative": True,
        "constant_collapse": {
            "identity_descriptor": _gaussian_value_record(
                GaussianValue(exponent=Fraction(0, 1))
            ),
            "distinct_descriptor": _gaussian_value_record(
                GaussianValue(exponent=collapse_exponent)
            ),
            "descriptors_equal": False,
            "binary64_hex_for_both": "0x1.0000000000000p+0",
            "binary64_exact_value_for_both": _fraction_record(Fraction(1, 1)),
            "rounding_reason": "ONE_MINUS_EXP_NEG_Q_LESS_THAN_Q_LESS_THAN_HALF_ULP_BELOW_ONE",
        },
        "near_one_three_by_three_gram": {
            "collinear_exponents": [
                [
                    _fraction_record(Fraction(0, 1)),
                    _fraction_record(near_exponent),
                    _fraction_record(far_exponent),
                ],
                [
                    _fraction_record(near_exponent),
                    _fraction_record(Fraction(0, 1)),
                    _fraction_record(near_exponent),
                ],
                [
                    _fraction_record(far_exponent),
                    _fraction_record(near_exponent),
                    _fraction_record(Fraction(0, 1)),
                ],
            ],
            "rounded_near_binary64_hex": "0x1.fffffffffe000p-1",
            "rounded_near_exact_rational": _fraction_record(near_binary),
            "rounded_far_binary64_hex": "0x1.fffffffff8000p-1",
            "rounded_far_exact_rational": _fraction_record(far_binary),
            "rounded_gram_determinant": _fraction_record(rounded_determinant),
            "rounded_gram_positive_semidefinite": False,
            "symbolic_gaussian_gram_governed_by_generic_theorem": True,
        },
        "score_cancellation": {
            "authoritative_formal_difference": _formal_combination_record(
                FormalGaussianCombination(
                    terms=(
                        GaussianTerm(
                            exponent=Fraction(0, 1), coefficient=Fraction(1, 1)
                        ),
                        GaussianTerm(
                            exponent=collapse_exponent,
                            coefficient=Fraction(-1, 1),
                        ),
                    )
                )
            ),
            "authoritative_difference_is_formally_zero": False,
            "binary64_subtraction_result": _fraction_record(Fraction(0, 1)),
            "binary64_subtraction_is_authoritative": False,
        },
        "scientific_result": False,
    }


def _canonical_json_bytes(value: object) -> bytes:
    _validate_strict_json_value(value, name="canonical JSON")
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _validate_strict_json_value(value: object, *, name: str) -> None:
    """Bound and type-check a JSON graph iteratively before serialization.

    Repeated container identity is refused together with cycles.  JSON has no
    alias semantics, so accepting aliases would add attack surface without
    adding a representable value.
    """

    stack = [(value, 0, name)]
    seen_containers = set()
    node_count = 0
    while stack:
        current, depth, label = stack.pop()
        node_count += 1
        if node_count > MAX_REPORT_JSON_NODES:
            raise CKSReportResourceError(name + " exceeds the JSON node bound")
        if depth > MAX_REPORT_JSON_DEPTH:
            raise CKSReportResourceError(name + " exceeds the JSON depth bound")
        if type(current) is dict:
            identity = id(current)
            if identity in seen_containers:
                raise CKSReportResourceError(
                    name + " contains a cycle or repeated container"
                )
            seen_containers.add(identity)
            if len(current) > MAX_REPORT_CONTAINER_ITEMS:
                raise CKSReportResourceError(
                    label + " exceeds the container item bound"
                )
            for key, item in current.items():
                if type(key) is not str:
                    raise TypeError(
                        label + " object keys must be exact built-in strings"
                    )
                try:
                    key_bytes = key.encode("utf-8")
                except UnicodeEncodeError as error:
                    raise CKSReportResourceError(label + " key is not UTF-8") from error
                if len(key_bytes) > MAX_REPORT_TEXT_BYTES:
                    raise CKSReportResourceError(
                        label + " key exceeds the text byte bound"
                    )
                stack.append((item, depth + 1, label + ".value"))
            continue
        if type(current) is list:
            identity = id(current)
            if identity in seen_containers:
                raise CKSReportResourceError(
                    name + " contains a cycle or repeated container"
                )
            seen_containers.add(identity)
            if len(current) > MAX_REPORT_CONTAINER_ITEMS:
                raise CKSReportResourceError(
                    label + " exceeds the container item bound"
                )
            for item in current:
                stack.append((item, depth + 1, label + "[]"))
            continue
        if current is None or type(current) is bool:
            continue
        if type(current) is int:
            if abs(current).bit_length() > MAX_REPORT_INTEGER_BITS:
                raise CKSReportResourceError(label + " exceeds the integer bit bound")
            continue
        if type(current) is str:
            try:
                encoded = current.encode("utf-8")
            except UnicodeEncodeError as error:
                raise CKSReportResourceError(label + " is not UTF-8") from error
            if len(encoded) > MAX_REPORT_TEXT_BYTES:
                raise CKSReportResourceError(label + " exceeds the text byte bound")
            continue
        if type(current) is float:
            if not math.isfinite(current):
                raise CKSReferenceError(label + " contains a nonfinite float")
            continue
        raise TypeError(label + " contains a non-exact or non-JSON scalar")


def report_sha256(report: Mapping[str, Any]) -> str:
    if type(report) is not dict:
        raise TypeError("report must be an exact built-in dict")
    _validate_strict_json_value(report, name="report")
    payload = dict(report)
    payload.pop("report_sha256", None)
    raw = _canonical_json_bytes(payload)
    if len(raw) > MAX_REPORT_BYTES:
        raise CKSReportResourceError("report exceeds its byte bound")
    return hashlib.sha256((SCHEMA_VERSION + "\0").encode("ascii") + raw).hexdigest()


def build_reference_report(
    spec: FiniteCKSSpec, draws: object, target: object
) -> Dict[str, Any]:
    """Build a complete report only when the input is report-admitted.

    Scoring supports every valid ``2 <= R <= 128`` roster.  Report generation
    is intentionally partial over that score domain: the unchanged graph and
    byte bounds may raise ``CKSReportResourceError`` after this function's
    internal score construction.  That refusal says only that the generated
    report is outside admission; it does not invalidate a formal score
    previously returned by a separate score-API call.
    """

    checked_spec = _revalidated_spec(spec)
    score = conditional_cks_u_statistic(checked_spec, draws, target)
    canonical_draws = [
        [
            list(item)
            for item in _canonical_configuration(draw, checked_spec, name="draw")
        ]
        for draw in draws
    ]
    canonical_draws.sort(key=_canonical_json_bytes)
    canonical_target = [
        list(item)
        for item in _canonical_configuration(target, checked_spec, name="target")
    ]
    report: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "control_predicate": CONTROL_PREDICATE,
        "scope": "GENERIC_FINITE_ALPHABET_REFERENCE_ONLY",
        "spec": _spec_record(checked_spec),
        "canonical_inputs": {
            "draw_multiset": canonical_draws,
            "target_counting_measure": canonical_target,
        },
        "authoritative_kernel_value_contract": {
            "kind": "EXACT_SYMBOLIC_EXP_NEGATIVE_RATIONAL",
            "denotation": "EXACT_REAL_EXP_NEGATIVE_EXPONENT",
            "descriptor_is_numeric_approximation": False,
            "binary64_kernel_or_score_value_authoritative": False,
            "identity_psd_strict_propriety_or_score_claim_uses_binary64": False,
            "implementation_computes_numeric_order_sign_or_comparison": False,
        },
        "conditional_cks_u_statistic": {
            "draw_count": score.draw_count,
            "unordered_off_diagonal_kernel_values": list(
                _gaussian_value_record(value)
                for value in score.off_diagonal_kernel_values
            ),
            "target_kernel_values": list(
                _gaussian_value_record(value)
                for value in score.target_kernel_values
            ),
            "formal_loss": _formal_combination_record(score.formal_loss),
            "score_direction": score.score_direction,
            "requires_R_at_least_two": True,
            "conditional_iid_premise": CONDITIONAL_PREMISE,
            "conditional_iid_premise_asserted_by_reference": False,
        },
        "formula_counterexamples": raw_formula_counterexamples(),
        "binary64_failure_witnesses": binary64_failure_witnesses(),
        "report_resource_contract": {
            "score_generation_supported_R_minimum": 2,
            "score_generation_supported_R_maximum": MAX_CONDITIONAL_DRAWS,
            "report_generation_total_over_score_domain": False,
            "report_complete_for_report_admitted_inputs_only": True,
            "report_resource_refusal_exception": "CKSReportResourceError",
            "build_reference_report_resource_refusal_invalidates_previously_constructed_score": False,
            "standalone_report_sha256_resource_refusal_implies_valid_score": False,
            "report_admission_worst_case_totality_claimed": False,
            "bounded_graph_validation_precedes_canonical_serialization": True,
            "cycles_or_repeated_containers_accepted": False,
            "maximum_depth": MAX_REPORT_JSON_DEPTH,
            "maximum_nodes": MAX_REPORT_JSON_NODES,
            "maximum_container_items": MAX_REPORT_CONTAINER_ITEMS,
            "maximum_text_utf8_bytes": MAX_REPORT_TEXT_BYTES,
            "maximum_integer_or_rational_component_bits": MAX_REPORT_INTEGER_BITS,
            "maximum_canonical_payload_bytes": MAX_REPORT_BYTES,
            "exact_payload_byte_cap_checked_immediately_after_bounded_serialization": True,
            "identical_single_symbol_R61_report_admitted": True,
            "identical_single_symbol_R62_score_succeeds_report_resource_refuses": True,
            "identical_single_symbol_R128_score_succeeds_report_resource_refuses": True,
        },
        "nonclosures": {
            "B04_closed": False,
            "F105_closed": False,
            "F106_modified": False,
            "F108_modified": False,
            "F109_through_F112_closed": False,
            "gate_a_exact_metric_checkbox_closed": False,
            "domain_event_schema_embedding_scales_bandwidth_or_cap_bound": False,
            "production_metric_implemented": False,
            "scientific_execution_performed": False,
            "tracker_modified": False,
        },
        "publication_boundary": {
            "internal_evidence_only": True,
            "anonymous_or_public_inclusion_permitted": False,
            "publication_safe_derivative_requires_fresh_anonymity_and_proof_code_review": True,
        },
        "scientific_result": False,
    }
    report["report_sha256"] = report_sha256(report)
    return report


def _strict_equal(actual: Any, expected: Any, *, name: str) -> None:
    if type(actual) is not type(expected):
        raise CKSReferenceError(name + " type mismatch")
    if type(expected) is dict:
        if any(type(key) is not str for key in actual) or any(
            type(key) is not str for key in expected
        ):
            raise CKSReferenceError(name + " object key type mismatch")
        if set(actual) != set(expected):
            raise CKSReferenceError(name + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], name=name + "." + key)
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise CKSReferenceError(name + " length mismatch")
        for index, (item, wanted) in enumerate(zip(actual, expected)):
            _strict_equal(item, wanted, name=name + "[%d]" % index)
        return
    if actual != expected:
        raise CKSReferenceError(name + " value mismatch")


def validate_reference_report(
    report: object, spec: FiniteCKSSpec, draws: object, target: object
) -> bool:
    """Recompute and verify a complete report for a report-admitted input."""

    checked_spec = _revalidated_spec(spec)
    if type(report) is not dict:
        raise TypeError("report must be an exact built-in dict")
    if report.get("report_sha256") != report_sha256(report):
        raise CKSReferenceError("report digest mismatch")
    expected = build_reference_report(checked_spec, draws, target)
    _strict_equal(report, expected, name="report")
    return True


__all__ = (
    "CKSReportResourceError",
    "CKSReferenceError",
    "CONDITIONAL_PREMISE",
    "CONTROL_PREDICATE",
    "ConditionalCKSScore",
    "DistanceBreakdown",
    "FiniteCKSSpec",
    "FormalGaussianCombination",
    "GaussianTerm",
    "GaussianValue",
    "SCHEMA_VERSION",
    "SCORE_DIRECTION",
    "build_reference_report",
    "binary64_failure_witnesses",
    "conditional_cks_u_statistic",
    "configuration_distance",
    "configuration_kernel",
    "raw_formula_counterexamples",
    "report_sha256",
    "validate_reference_report",
)
