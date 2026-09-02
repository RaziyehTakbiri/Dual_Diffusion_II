"""Analytic uncapped association guide and explicit capped-boundary defect.

This module implements the theorem-to-code contract in Section 6 of
``manuscript_v3/executable_method_spec.md``.  It propagates the independent
reverse-time immigration/death/type-replacement/OU reference to the terminal
association observation.  A propagated source-to-anchor law is generally a
finite Gaussian mixture, so it is represented here rather than being coerced
into :class:`TypedAffineGaussianObservationChannel`'s one-Gaussian-per-pair
terminal family.

The public ``evaluate_unbounded`` method is the auxiliary computation.  The
public ``evaluate`` method is its literal restriction to the declared capped
state space; it performs no conditioning or renormalization.  The omitted
birth at the cap is exposed both exactly and through a separately labelled,
unnormalized importance average.  The learned-base mismatch and numerical
time/Laplacian residuals are deliberately outside this module: a cap estimate
must not be misreported as the complete Section 6.3 defect diagnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import (
    Decimal,
    InvalidOperation,
    Overflow as DecimalOverflow,
    ROUND_CEILING,
    Underflow,
    localcontext,
)
from fractions import Fraction
import hashlib
import math
from numbers import Integral, Real
from types import MappingProxyType
from typing import Iterable, Mapping, Optional, Sequence, Tuple, Union
import warnings

import numpy as np
from scipy.linalg import expm

from heterodiff.processes.reversible_hybrid_reference import (
    ReversibleHybridReference,
)

from .association_observation import (
    AffineGaussianFiberChannel,
    AssociationCoordinateGradients,
    AssociationDensityEvaluation,
    AssociationObservationResourceError,
    BoundAssociationObservationRow,
    CollapsedPoissonObservationReference,
    MAX_AFFINE_OBSERVATION_DIMENSION,
    MAX_ASSOCIATION_CLUTTER_MEAN,
    MAX_ASSOCIATION_DP_WORK,
    MAX_ASSOCIATION_MATRIX_ENTRIES,
    MAX_ASSOCIATION_OCCURRENCES,
    MAX_POISSON_TAIL_TERMS,
    RetainedAssociationFactors,
    TypedAffineGaussianObservationChannel,
    TypedGaussianClutterIntensity,
    evaluate_overflow_association,
    evaluate_retained_association,
    labelled_association_edge_marginals,
    positive_association_log_density,
    _association_dp_resources,
    _association_marginal_resources,
)
from .configuration_reference import (
    MAX_CONFIGURATION_CARDINALITY,
    MAX_REFERENCE_DENSITY_COORDINATES,
    TransformedConfiguration,
    TransformedEvent,
)
from .finite_atomic_overflow_observation import (
    OVERFLOW_OBSERVATION,
    OverflowObservation,
)


PreconditionerObservation = Union[TransformedConfiguration, OverflowObservation]

MAX_PRECONDITIONER_TYPES = 128
MAX_PRECONDITIONER_EXPONENTIAL_WORK = 150_000_000
MAX_PRECONDITIONER_GAUSSIAN_COMPONENTS = 16_384
MAX_PRECONDITIONER_COVARIANCE_WORK = 100_000_000
MAX_PRECONDITIONER_KEY_DEPTH = 64
MAX_PRECONDITIONER_KEY_NODES = 100_000
MAX_PRECONDITIONER_PROPOSAL_SAMPLES = 100_000
MAX_PRECONDITIONER_PROPOSAL_COORDINATES = 4_000_000
MAX_PRECONDITIONER_PROPOSAL_EVALUATION_WORK = 50_000_000
MAX_PRECONDITIONER_EVALUATION_WORK = 50_000_000
MAX_PRECONDITIONER_GUIDE_CERTIFICATE_WORK = 50_000_000
PRECONDITIONER_NUMERICAL_ATOL = 5.0e-12

ANALYTIC_GUIDE_RANGE_SCHEMA_VERSION = "analytic-association-guide-range-v1"
ANALYTIC_GUIDE_RANGE_CERTIFICATE_SCOPE = (
    "fixed-collapsed-observation;all-reverse-times;all-capped-states;"
    "all-transformed-coordinates;positive-mixture-analytic-guide;"
    "normalized-probability-and-markov-kernel-semantics;"
    "real-arithmetic-value-edit-oscillation-and-coordinate-regularity;"
    "exact-gershgorin-covariance-witness;trusted-runtime;"
    "not-pointwise-floating-error-enclosure;not-operational-sampler-admission;"
    "not-residual;not-controlled-total-exit"
)

_MAX_PRECONDITIONER_KEY_SCALAR_LENGTH = 1_000_000
_MAX_PRECONDITIONER_KEY_INTEGER_BITS = 8_000_000
_MAX_PRECONDITIONER_HIGH_PRECISION_TERMS = 4_096

_LOG_MIN_NORMAL = math.log(float(np.finfo(np.float64).tiny))
_LOG_MAX = math.log(float(np.finfo(np.float64).max))
_LOG_TWO_PI = math.log(2.0 * math.pi)

_PROPAGATION_TOKEN = object()
_ONE_OCCURRENCE_TOKEN = object()
_EVALUATION_TOKEN = object()
_GRADIENT_TOKEN = object()
_EDGE_RATIO_TOKEN = object()
_CAP_DEFECT_TOKEN = object()
_PROPOSAL_ESTIMATE_TOKEN = object()
_GUIDE_RANGE_CERTIFICATE_TOKEN = object()


class AssociationPreconditionerNumericalError(ArithmeticError):
    """Raised when float64 cannot certify a positive analytic quantity."""


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    contiguous[contiguous == 0.0] = 0.0
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=np.float64).reshape(
        contiguous.shape
    )


def _validated_real(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % name)
    return 0.0 if result == 0.0 else result


def _validated_probability(
    value: object,
    *,
    name: str,
    strictly_positive: bool = False,
    strictly_below_one: bool = False,
) -> float:
    result = _validated_real(value, name=name)
    if result < 0.0 or result > 1.0:
        raise ValueError("%s must lie in [0, 1]" % name)
    if strictly_positive and result <= 0.0:
        raise ValueError("%s must be strictly positive" % name)
    if strictly_below_one and result >= 1.0:
        raise ValueError("%s must be strictly below one" % name)
    return result


def _validated_nonnegative_integer(value: object, *, name: str, maximum: int) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result < 0 or result > maximum:
        raise ValueError("%s must lie in [0, %d]" % (name, maximum))
    return result


def _bounded_tuple(
    value: object, *, name: str, maximum_items: int
) -> Tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError("%s must be an iterable, not text" % name)
    try:
        iterator = iter(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("%s must be iterable" % name) from error
    items = []
    for item in iterator:
        if len(items) >= maximum_items:
            raise AssociationObservationResourceError(
                "%s exceeds the implementation limit of %d items"
                % (name, maximum_items)
            )
        items.append(item)
    return tuple(items)


def _validated_key(value: object, *, name: str) -> Tuple[object, ...]:
    if type(value) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    stack = [(value, 0)]
    node_count = 0
    while stack:
        node, depth = stack.pop()
        node_count += 1
        if node_count > MAX_PRECONDITIONER_KEY_NODES:
            raise AssociationObservationResourceError(
                "%s exceeds the plain-data key node limit" % name
            )
        if type(node) is tuple:
            if depth >= MAX_PRECONDITIONER_KEY_DEPTH:
                raise AssociationObservationResourceError(
                    "%s exceeds the plain-data key depth limit" % name
                )
            remaining_nodes = MAX_PRECONDITIONER_KEY_NODES - node_count - len(stack)
            if len(node) > remaining_nodes:
                raise AssociationObservationResourceError(
                    "%s exceeds the plain-data key node limit" % name
                )
            stack.extend((item, depth + 1) for item in node)
            continue
        if type(node) not in (type(None), bool, int, float, str, bytes):
            raise TypeError("%s must contain only plain immutable scalar data" % name)
        if type(node) is float and not math.isfinite(node):
            raise ValueError("%s must not contain non-finite floats" % name)
        if (
            type(node) in (str, bytes)
            and len(node) > _MAX_PRECONDITIONER_KEY_SCALAR_LENGTH
        ):
            raise AssociationObservationResourceError(
                "%s contains an oversized scalar" % name
            )
        if (
            type(node) is int
            and node.bit_length() > _MAX_PRECONDITIONER_KEY_INTEGER_BITS
        ):
            raise AssociationObservationResourceError(
                "%s contains an oversized integer" % name
            )
    return value


def _validated_trusted_key(value: object, *, name: str) -> Tuple[object, ...]:
    """Validate an internally assembled key without rewalking its full tree."""

    if type(value) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    return value


def _logaddexp(left: float, right: float) -> float:
    if not (math.isfinite(left) or left == -math.inf) or not (
        math.isfinite(right) or right == -math.inf
    ):
        raise AssociationPreconditionerNumericalError(
            "log-add-exp inputs must be finite or -inf"
        )
    if left == -math.inf:
        return right
    if right == -math.inf:
        return left
    maximum = max(left, right)
    result = maximum + math.log(math.exp(left - maximum) + math.exp(right - maximum))
    if not math.isfinite(result):
        raise AssociationPreconditionerNumericalError(
            "log-add-exp result is not representable"
        )
    return 0.0 if result == 0.0 else result


def _propagated_affine_gaussian_fiber(
    matrix: np.ndarray,
    bias: np.ndarray,
    covariance: np.ndarray,
    *,
    name: str,
) -> AffineGaussianFiberChannel:
    """Build one internally propagated fiber with narrow numeric normalization."""

    try:
        return AffineGaussianFiberChannel(matrix, bias, covariance)
    except AssociationObservationResourceError:
        raise
    except ArithmeticError as error:
        raise AssociationPreconditionerNumericalError(
            "%s construction cannot be certified numerically" % name
        ) from error
    except ValueError as error:
        numeric_covariance_failure = str(
            error
        ) == "covariance must be finite symmetric positive definite" and isinstance(
            error.__cause__, (FloatingPointError, np.linalg.LinAlgError)
        )
        if not numeric_covariance_failure:
            raise
        raise AssociationPreconditionerNumericalError(
            "%s construction cannot be certified numerically" % name
        ) from error


def _logsumexp(values: Sequence[float]) -> float:
    finite = [value for value in values if value != -math.inf]
    if not finite:
        return -math.inf
    maximum = max(finite)
    result = maximum + math.log(
        math.fsum(math.exp(value - maximum) for value in finite)
    )
    if not math.isfinite(result):
        raise AssociationPreconditionerNumericalError(
            "log-sum-exp is not representable"
        )
    return 0.0 if result == 0.0 else result


def _ordinary_from_log(value: float, *, name: str) -> float:
    if value == -math.inf:
        return 0.0
    if value > _LOG_MAX:
        raise AssociationPreconditionerNumericalError("%s overflows float64" % name)
    result = math.exp(value)
    if result == 0.0:
        raise AssociationPreconditionerNumericalError(
            "positive %s underflows float64" % name
        )
    return result


_GUIDE_CERTIFICATE_DECIMAL_PRECISION = 180
_GUIDE_OVERFLOW_TAIL_TERMS = 64


def _fraction_from_float(value: float) -> Fraction:
    """Return the exact rational represented by one finite binary64 value."""

    numerator, denominator = value.as_integer_ratio()
    return Fraction(numerator, denominator)


def _outward_float_from_fraction(value: Fraction, *, name: str) -> float:
    """Round an exact rational toward positive infinity in binary64."""

    try:
        rounded = float(value)
    except OverflowError as error:
        raise AssociationPreconditionerNumericalError(
            "%s has no finite binary64 upper bound" % name
        ) from error
    if not math.isfinite(rounded):
        raise AssociationPreconditionerNumericalError(
            "%s has no finite binary64 upper bound" % name
        )
    if _fraction_from_float(rounded) < value:
        rounded = math.nextafter(rounded, math.inf)
    if not math.isfinite(rounded):
        raise AssociationPreconditionerNumericalError(
            "%s cannot be rounded outward" % name
        )
    return 0.0 if rounded == 0.0 else rounded


def _downward_positive_float_from_fraction(value: Fraction, *, name: str) -> float:
    """Round a strictly positive exact rational toward zero in binary64."""

    if value <= 0:
        raise ValueError("%s must be strictly positive" % name)
    try:
        rounded = float(value)
    except OverflowError as error:
        raise AssociationPreconditionerNumericalError(
            "%s is outside binary64 range" % name
        ) from error
    if not math.isfinite(rounded):
        raise AssociationPreconditionerNumericalError(
            "%s is outside binary64 range" % name
        )
    if rounded == 0.0:
        raise AssociationPreconditionerNumericalError("%s underflows binary64" % name)
    if _fraction_from_float(rounded) > value:
        rounded = math.nextafter(rounded, 0.0)
    if rounded <= 0.0 or not math.isfinite(rounded):
        raise AssociationPreconditionerNumericalError(
            "%s has no positive binary64 lower witness" % name
        )
    return rounded


def _outward_float_from_decimal(value: Decimal, *, name: str) -> float:
    """Round a finite Decimal upper witness toward positive infinity."""

    if not value.is_finite():
        raise AssociationPreconditionerNumericalError(
            "%s has no finite binary64 upper bound" % name
        )
    try:
        rounded = float(value)
    except (OverflowError, ValueError) as error:
        raise AssociationPreconditionerNumericalError(
            "%s has no finite binary64 upper bound" % name
        ) from error
    if not math.isfinite(rounded):
        raise AssociationPreconditionerNumericalError(
            "%s has no finite binary64 upper bound" % name
        )
    if Decimal.from_float(rounded) < value:
        rounded = math.nextafter(rounded, math.inf)
    if not math.isfinite(rounded):
        raise AssociationPreconditionerNumericalError(
            "%s cannot be rounded outward" % name
        )
    return 0.0 if rounded == 0.0 else rounded


def _decimal_fraction_upper(value: Fraction) -> Decimal:
    """Return a high-precision Decimal lying above an exact rational."""

    if value == 0:
        return Decimal(0)
    with localcontext() as context:
        context.prec = _GUIDE_CERTIFICATE_DECIMAL_PRECISION
        context.rounding = ROUND_CEILING
        converted = Decimal(value.numerator) / Decimal(value.denominator)
        return context.next_plus(converted)


def _decimal_log_fraction_upper(value: Fraction, *, name: str) -> Decimal:
    """Return a directed high-precision upper bound on ``log(value)``."""

    if value <= 0:
        raise ValueError("%s must be strictly positive" % name)
    if value == 1:
        return Decimal(0)
    try:
        with localcontext() as context:
            context.prec = _GUIDE_CERTIFICATE_DECIMAL_PRECISION
            context.rounding = ROUND_CEILING
            converted = Decimal(value.numerator) / Decimal(value.denominator)
            converted = context.next_plus(converted)
            logged = converted.ln()
            return context.next_plus(logged)
    except (DecimalOverflow, InvalidOperation, OverflowError, ValueError) as error:
        raise AssociationPreconditionerNumericalError(
            "%s logarithm is not certifiable" % name
        ) from error


def _outward_log_fraction(value: Fraction, *, name: str) -> float:
    return _outward_float_from_decimal(
        _decimal_log_fraction_upper(value, name=name), name=name
    )


def _outward_sum_upper(values: Iterable[float], *, name: str) -> float:
    """Add finite binary64 upper witnesses with exact accumulation."""

    checked = tuple(values)
    if any(not math.isfinite(value) for value in checked):
        raise AssociationPreconditionerNumericalError(
            "%s contains a non-finite term" % name
        )
    exact = sum((_fraction_from_float(value) for value in checked), Fraction(0))
    return _outward_float_from_fraction(exact, name=name)


def _outward_logaddexp_upper(left: float, right: float, *, name: str) -> float:
    """Directed upper log-sum-exp for already valid log upper witnesses."""

    if left == -math.inf:
        return right
    if right == -math.inf:
        return left
    if not math.isfinite(left) or not math.isfinite(right):
        raise AssociationPreconditionerNumericalError(
            "%s contains a non-finite log witness" % name
        )
    maximum = max(left, right)
    minimum = min(left, right)
    # Below -800 the positive correction is safely smaller than the least
    # binary64 subnormal, including a wide margin for the subtraction.
    if minimum - maximum < -800.0:
        rounded = math.nextafter(maximum, math.inf)
        if not math.isfinite(rounded):
            raise AssociationPreconditionerNumericalError(
                "%s has no finite binary64 upper bound" % name
            )
        return rounded
    try:
        with localcontext() as context:
            # A binary64 exponential correction can be as small as roughly
            # 1e-324. Retaining it through 1 + correction therefore needs
            # substantially more than the ordinary certificate precision.
            # Binary64-to-Decimal conversion itself is exact within 1,200
            # digits.
            context.prec = 1_200
            context.rounding = ROUND_CEILING
            difference = Decimal.from_float(minimum) - Decimal.from_float(maximum)
            # Decimal exp/ln are correctly rounded with ROUND_HALF_EVEN,
            # independently of context.rounding. Advance each transcendental
            # result separately before the next monotone operation.
            residual = context.next_plus(difference.exp())
            one_plus = Decimal(1) + residual
            correction = context.next_plus(one_plus.ln())
            result = Decimal.from_float(maximum) + correction
            result = context.next_plus(result)
    except (DecimalOverflow, InvalidOperation, OverflowError, ValueError) as error:
        raise AssociationPreconditionerNumericalError(
            "%s is not certifiable" % name
        ) from error
    return _outward_float_from_decimal(result, name=name)


def _outward_logsumexp_upper(values: Iterable[float], *, name: str) -> float:
    result = -math.inf
    for value in values:
        result = _outward_logaddexp_upper(result, value, name=name)
    return result


def _outward_exp_upper(log_value: float, *, name: str) -> float:
    """Materialize a finite upper witness from an upper log witness."""

    if log_value == -math.inf:
        return 0.0
    if not math.isfinite(log_value):
        raise AssociationPreconditionerNumericalError("log %s is not finite" % name)
    try:
        with localcontext() as context:
            context.prec = _GUIDE_CERTIFICATE_DECIMAL_PRECISION
            context.rounding = ROUND_CEILING
            result = Decimal.from_float(log_value).exp()
            result = context.next_plus(result)
    except (DecimalOverflow, InvalidOperation, OverflowError, ValueError) as error:
        raise AssociationPreconditionerNumericalError(
            "%s has no finite binary64 upper bound" % name
        ) from error
    return _outward_float_from_decimal(result, name=name)


def _outward_sqrt_fraction(value: Fraction, *, name: str) -> float:
    """Return a verified binary64 upper bound on an exact square root."""

    if value < 0:
        raise ValueError("%s must be nonnegative" % name)
    if value == 0:
        return 0.0
    numerator_root = math.isqrt(value.numerator)
    denominator_root = math.isqrt(value.denominator)
    if (
        numerator_root * numerator_root == value.numerator
        and denominator_root * denominator_root == value.denominator
    ):
        return _outward_float_from_fraction(
            Fraction(numerator_root, denominator_root), name=name
        )
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    even_exponent = exponent if exponent % 2 == 0 else exponent - 1
    scaled = value / Fraction(2) ** even_exponent
    approximate = math.sqrt(float(scaled)) * (2.0 ** (even_exponent // 2))
    if not math.isfinite(approximate) or approximate <= 0.0:
        raise AssociationPreconditionerNumericalError(
            "%s has no finite positive approximation" % name
        )
    while _fraction_from_float(approximate) ** 2 < value:
        approximate = math.nextafter(approximate, math.inf)
        if not math.isfinite(approximate):
            raise AssociationPreconditionerNumericalError(
                "%s cannot be rounded outward" % name
            )
    return approximate


def _exact_gershgorin_lower_bound(covariance: np.ndarray) -> Fraction:
    """Certify a positive eigenvalue lower bound from represented entries."""

    dimension = int(covariance.shape[0])
    lower = None
    for row in range(dimension):
        diagonal = _fraction_from_float(float(covariance[row, row]))
        radius = sum(
            (
                abs(_fraction_from_float(float(covariance[row, column])))
                for column in range(dimension)
                if column != row
            ),
            Fraction(0),
        )
        candidate = diagonal - radius
        lower = candidate if lower is None else min(lower, candidate)
    if lower is None or lower <= 0:
        raise AssociationPreconditionerNumericalError(
            "covariance is SPD numerically but has no positive exact "
            "Gershgorin certificate"
        )
    return lower


def _outward_matrix_frobenius_norm(
    matrix: np.ndarray, *, name: str
) -> Tuple[float, Fraction]:
    squared = sum(
        (_fraction_from_float(float(value)) ** 2 for value in matrix.flat),
        Fraction(0),
    )
    return _outward_sqrt_fraction(squared, name=name), squared


def _plain_key_sha256(value: Tuple[object, ...], *, domain: bytes) -> str:
    """Hash a bounded plain tree with explicit type and length framing."""

    digest = hashlib.sha256()
    digest.update(domain)
    stack = [(value, 0)]
    node_count = 0
    maximum_depth = MAX_PRECONDITIONER_KEY_DEPTH + 32
    maximum_nodes = MAX_PRECONDITIONER_KEY_NODES * 8
    while stack:
        node, depth = stack.pop()
        node_count += 1
        if node_count > maximum_nodes:
            raise AssociationObservationResourceError(
                "certificate digest tree exceeds the node limit"
            )
        if node is None:
            digest.update(b"n")
            continue
        elif type(node) is bool:
            digest.update(b"b1" if node else b"b0")
            continue
        elif type(node) is int:
            magnitude = abs(node)
            if magnitude.bit_length() > _MAX_PRECONDITIONER_KEY_INTEGER_BITS:
                raise AssociationObservationResourceError(
                    "certificate digest tree contains an oversized integer"
                )
            payload = magnitude.to_bytes(
                max(1, (magnitude.bit_length() + 7) // 8), "big"
            )
            sign = b"-" if node < 0 else b"+"
            digest.update(b"i" + sign + len(payload).to_bytes(8, "big") + payload)
            continue
        elif type(node) is float:
            payload = node.hex().encode("ascii")
            digest.update(b"f" + len(payload).to_bytes(8, "big") + payload)
            continue
        elif type(node) is str:
            if len(node) > _MAX_PRECONDITIONER_KEY_SCALAR_LENGTH:
                raise AssociationObservationResourceError(
                    "certificate digest tree contains an oversized scalar"
                )
            payload = node.encode("utf-8")
            digest.update(b"s" + len(payload).to_bytes(8, "big") + payload)
            continue
        elif type(node) is bytes:
            if len(node) > _MAX_PRECONDITIONER_KEY_SCALAR_LENGTH:
                raise AssociationObservationResourceError(
                    "certificate digest tree contains an oversized scalar"
                )
            digest.update(b"y" + len(node).to_bytes(8, "big") + node)
            continue
        elif type(node) is tuple:
            if depth >= maximum_depth:
                raise AssociationObservationResourceError(
                    "certificate digest tree exceeds the depth limit"
                )
            remaining_nodes = maximum_nodes - node_count - len(stack)
            if len(node) > remaining_nodes:
                raise AssociationObservationResourceError(
                    "certificate digest tree exceeds the node limit"
                )
            digest.update(b"t" + len(node).to_bytes(8, "big"))
            stack.extend((item, depth + 1) for item in reversed(node))
            continue
        else:
            raise TypeError("certificate digest received non-plain data")
    return digest.hexdigest()


def _log_gaussian_relative_peak_upper(
    coefficient: Fraction,
    coordinates: Tuple[float, ...],
    covariance_lower: Optional[Fraction],
    *,
    name: str,
) -> float:
    """Bound a detected/clutter Gaussian fiber relative to ``N(0, I)``."""

    if coefficient <= 0:
        return -math.inf
    dimension = len(coordinates)
    if dimension == 0:
        return _outward_log_fraction(coefficient, name=name)
    if covariance_lower is None or covariance_lower <= 0:
        raise ValueError("a positive-dimensional peak needs a covariance witness")
    squared_norm = sum(
        (_fraction_from_float(value) ** 2 for value in coordinates),
        Fraction(0),
    )
    try:
        with localcontext() as context:
            context.prec = _GUIDE_CERTIFICATE_DECIMAL_PRECISION
            context.rounding = ROUND_CEILING
            coefficient_log = _decimal_log_fraction_upper(
                coefficient, name=name + " coefficient"
            )
            squared_term = _decimal_fraction_upper(squared_norm / 2)
            inverse_covariance_log = _decimal_log_fraction_upper(
                1 / covariance_lower,
                name=name + " inverse covariance lower witness",
            )
            result = (
                coefficient_log
                + squared_term
                + (Decimal(dimension) / Decimal(2)) * inverse_covariance_log
            )
            result = context.next_plus(result)
    except (DecimalOverflow, InvalidOperation, OverflowError, ValueError) as error:
        raise AssociationPreconditionerNumericalError(
            "%s is not certifiable" % name
        ) from error
    return _outward_float_from_decimal(result, name=name)


def _log_whitened_matrix_norm_upper(
    matrix_squared_frobenius: Fraction,
    covariance_lower: Fraction,
    *,
    name: str,
) -> float:
    if matrix_squared_frobenius == 0:
        return -math.inf
    log_ratio = _outward_log_fraction(
        matrix_squared_frobenius / covariance_lower, name=name
    )
    return _outward_float_from_fraction(
        _fraction_from_float(log_ratio) / 2,
        name=name,
    )


def _log_cap_aware_injection_polynomial_upper(
    signal_log_bounds: Sequence[float],
    background_log_bounds: Sequence[float],
    *,
    source_cap: int,
) -> float:
    """Evaluate an upper log bound on the cap-aware injection polynomial."""

    if len(signal_log_bounds) != len(background_log_bounds):
        raise ValueError("signal and background bounds must have equal length")
    maximum_matches = min(source_cap, len(signal_log_bounds))
    table = [-math.inf] * (maximum_matches + 1)
    table[0] = 0.0
    processed = 0
    for signal_log, background_log in zip(signal_log_bounds, background_log_bounds):
        next_table = [-math.inf] * (maximum_matches + 1)
        upper_matches = min(maximum_matches, processed + 1)
        for matched in range(upper_matches + 1):
            unmatched_term = -math.inf
            if (
                matched <= min(maximum_matches, processed)
                and table[matched] != -math.inf
            ):
                if background_log != -math.inf:
                    unmatched_term = _outward_sum_upper(
                        (table[matched], background_log),
                        name="guide injection unmatched product",
                    )
            matched_term = -math.inf
            if (
                matched > 0
                and table[matched - 1] != -math.inf
                and signal_log != -math.inf
            ):
                remaining_sources = source_cap - matched + 1
                if remaining_sources <= 0:
                    raise RuntimeError("invalid injection falling-factorial index")
                matched_term = _outward_sum_upper(
                    (
                        table[matched - 1],
                        signal_log,
                        _outward_log_fraction(
                            Fraction(remaining_sources),
                            name="guide injection falling-factorial factor",
                        ),
                    ),
                    name="guide injection matched product",
                )
            next_table[matched] = _outward_logaddexp_upper(
                unmatched_term,
                matched_term,
                name="guide injection polynomial recurrence",
            )
        table = next_table
        processed += 1
    return _outward_logsumexp_upper(
        table, name="guide injection polynomial terminal sum"
    )


def _unit_poisson_tail_log_reciprocal_upper(retained_cap: int) -> float:
    """Bound ``-log P(Poisson(1) > retained_cap)`` from below-tail terms.

    The exact tail is ``exp(-1) * sum_{n>M} 1/n!``.  A finite positive
    partial sum is an exact lower bound, so ``1 + log(1 / partial_sum)`` is a
    rigorous upper bound on the reciprocal log mass without trusting the
    ordinary Poisson-tail evaluator.
    """

    first_count = retained_cap + 1
    term = Fraction(1, math.factorial(first_count))
    partial = term
    count = first_count
    for _ in range(1, _GUIDE_OVERFLOW_TAIL_TERMS):
        count += 1
        term /= count
        partial += term
    return _outward_sum_upper(
        (
            1.0,
            _outward_log_fraction(
                1 / partial,
                name="unit-Poisson overflow reciprocal partial-sum log",
            ),
        ),
        name="unit-Poisson overflow reciprocal log upper bound",
    )


def _validated_certificate_fiber(
    fiber: object,
    *,
    expected_input_dimension: int,
    expected_output_dimension: int,
    name: str,
) -> AffineGaussianFiberChannel:
    if type(fiber) is not AffineGaussianFiberChannel:
        raise TypeError("%s must be an exact affine Gaussian fiber" % name)
    if (
        fiber.input_dimension != expected_input_dimension
        or fiber.output_dimension != expected_output_dimension
    ):
        raise ValueError("%s dimensions do not match the declared strata" % name)
    expected_shapes = (
        (fiber.matrix, (expected_output_dimension, expected_input_dimension)),
        (fiber.bias, (expected_output_dimension,)),
        (fiber.covariance, (expected_output_dimension, expected_output_dimension)),
    )
    for array, expected_shape in expected_shapes:
        if (
            type(array) is not np.ndarray
            or array.dtype != np.dtype(np.float64)
            or array.shape != expected_shape
            or array.flags.writeable
            or not array.flags.c_contiguous
            or not np.all(np.isfinite(array))
            or np.any((array == 0.0) & np.signbit(array))
        ):
            raise ValueError("%s contains a noncanonical array" % name)
    if not np.array_equal(fiber.covariance, fiber.covariance.T):
        raise ValueError("%s covariance is not exactly symmetric" % name)
    return fiber


def _checked_product(left: float, right: float, *, name: str) -> float:
    if not math.isfinite(left) or not math.isfinite(right):
        raise AssociationPreconditionerNumericalError(
            "%s has a non-finite factor" % name
        )
    result = left * right
    if not math.isfinite(result):
        raise AssociationPreconditionerNumericalError("%s is not representable" % name)
    if result == 0.0 and left != 0.0 and right != 0.0:
        raise AssociationPreconditionerNumericalError(
            "positive-magnitude %s underflows float64" % name
        )
    return 0.0 if result == 0.0 else result


def _strict_nonnegative_fsum(values: Iterable[float], *, name: str) -> float:
    checked = tuple(float(value) for value in values)
    if any(not math.isfinite(value) or value < 0.0 for value in checked):
        raise AssociationPreconditionerNumericalError(
            "%s contains an invalid term" % name
        )
    result = math.fsum(checked)
    if not math.isfinite(result):
        raise AssociationPreconditionerNumericalError("%s is not representable" % name)
    for index, value in enumerate(checked):
        if value > 0.0 and result == math.fsum(checked[:index] + checked[index + 1 :]):
            raise AssociationPreconditionerNumericalError(
                "%s loses a positive component in float64" % name
            )
    return 0.0 if result == 0.0 else result


def _association_cardinality_is_structural_zero(
    detection_probability: np.ndarray,
    clutter_total: float,
    observation_count: int,
) -> bool:
    certain_detection_count = int(np.count_nonzero(detection_probability == 1.0))
    if observation_count < certain_detection_count:
        return True
    positive_detection_count = int(np.count_nonzero(detection_probability > 0.0))
    return clutter_total == 0.0 and observation_count > positive_detection_count


def _log_abs_expm1(value: float) -> Tuple[int, float]:
    """Return sign and log absolute value of ``exp(value) - 1``."""

    if value == 0.0:
        return 0, -math.inf
    if value > 0.0:
        if value < math.log(2.0):
            return 1, math.log(math.expm1(value))
        return 1, value + math.log1p(-math.exp(-value))
    return -1, math.log(-math.expm1(value))


def _signed_log_weighted_sum(
    terms: Iterable[Tuple[float, float]], *, name: str
) -> float:
    raw_terms = tuple(terms)
    ordinary_terms = []
    ordinary_safe = True
    for log_weight, raw_value in raw_terms:
        if log_weight == -math.inf or raw_value == 0.0:
            continue
        if not math.isfinite(log_weight) or not math.isfinite(raw_value):
            raise AssociationPreconditionerNumericalError(
                "%s contains a non-finite term" % name
            )
        try:
            weight = math.exp(log_weight)
        except OverflowError:
            ordinary_safe = False
            break
        if weight < float(np.finfo(np.float64).tiny):
            ordinary_safe = False
            break
        weighted = weight * raw_value
        if not math.isfinite(weighted) or weighted == 0.0:
            ordinary_safe = False
            break
        ordinary_terms.append(weighted)
    if ordinary_safe:
        try:
            result = math.fsum(ordinary_terms)
        except (OverflowError, ValueError):
            ordinary_safe = False
        else:
            if math.isfinite(result):
                maximum = max((abs(value) for value in ordinary_terms), default=0.0)
                scaled_absolute_sum = (
                    0.0
                    if maximum == 0.0
                    else math.fsum(abs(value) / maximum for value in ordinary_terms)
                )
                separated = (
                    result != 0.0
                    and abs(result) / maximum
                    > 64.0 * float(np.finfo(np.float64).eps) * scaled_absolute_sum
                )
                if separated:
                    return result
    checked = [
        (log_weight, raw_value)
        for log_weight, raw_value in raw_terms
        if log_weight != -math.inf and raw_value != 0.0
    ]
    if not checked:
        return 0.0
    if len(checked) > _MAX_PRECONDITIONER_HIGH_PRECISION_TERMS:
        raise AssociationObservationResourceError(
            "%s exceeds the high-precision term limit" % name
        )
    try:
        with localcontext() as context:
            context.prec = 2_200
            context.traps[Underflow] = True
            decimal_result = sum(
                Decimal.from_float(log_weight).exp() * Decimal.from_float(raw_value)
                for log_weight, raw_value in checked
            )
        result = float(decimal_result)
    except (
        DecimalOverflow,
        InvalidOperation,
        Underflow,
        OverflowError,
        ValueError,
    ) as error:
        raise AssociationPreconditionerNumericalError(
            "%s is not representable" % name
        ) from error
    if not math.isfinite(result):
        raise AssociationPreconditionerNumericalError("%s is not representable" % name)
    if decimal_result != 0 and result == 0.0:
        raise AssociationPreconditionerNumericalError("%s underflows float64" % name)
    return 0.0 if result == 0.0 else result


def _signed_log_weighted_mean(
    terms: Iterable[Tuple[float, float]],
    *,
    count: int,
    name: str,
) -> float:
    """Return a signed log-domain mean without overflowing its raw sum."""

    if count <= 0:
        raise ValueError("mean count must be positive")
    checked = []
    for log_magnitude, raw_sign in terms:
        if log_magnitude == -math.inf or raw_sign == 0.0:
            continue
        if not math.isfinite(log_magnitude) or not math.isfinite(raw_sign):
            raise AssociationPreconditionerNumericalError(
                "%s contains a non-finite term" % name
            )
        if raw_sign not in (-1.0, 1.0):
            raise AssociationPreconditionerNumericalError(
                "%s contains a value that is not a sign" % name
            )
        sign = raw_sign
        checked.append((log_magnitude, sign))
    if not checked:
        return 0.0

    scale_log = max(log_magnitude for log_magnitude, _ in checked)
    scaled = [
        math.copysign(math.exp(log_magnitude - scale_log), sign)
        for log_magnitude, sign in checked
    ]
    scaled_sum = math.fsum(scaled)
    scaled_absolute_sum = math.fsum(abs(value) for value in scaled)
    if (
        scaled_sum != 0.0
        and abs(scaled_sum)
        > 64.0 * float(np.finfo(np.float64).eps) * scaled_absolute_sum
    ):
        log_mean_magnitude = scale_log + math.log(abs(scaled_sum)) - math.log(count)
        magnitude = _ordinary_from_log(log_mean_magnitude, name=name)
        return math.copysign(magnitude, scaled_sum)

    if len(checked) > _MAX_PRECONDITIONER_HIGH_PRECISION_TERMS:
        raise AssociationObservationResourceError(
            "%s exceeds the high-precision term limit" % name
        )
    try:
        with localcontext() as context:
            context.prec = 2_200
            context.traps[Underflow] = True
            decimal_mean = sum(
                Decimal.from_float(log_magnitude).exp() * Decimal.from_float(sign)
                for log_magnitude, sign in checked
            ) / Decimal(count)
        result = float(decimal_mean)
    except (
        DecimalOverflow,
        InvalidOperation,
        Underflow,
        OverflowError,
        ValueError,
    ) as error:
        raise AssociationPreconditionerNumericalError(
            "%s is not representable" % name
        ) from error
    if not math.isfinite(result):
        raise AssociationPreconditionerNumericalError("%s is not representable" % name)
    if decimal_mean != 0 and result == 0.0:
        raise AssociationPreconditionerNumericalError("%s underflows float64" % name)
    return 0.0 if result == 0.0 else result


@dataclass(frozen=True, eq=False, init=False)
class AssociationPropagation:
    """Immutable reverse-to-terminal propagation certificate at one time."""

    reverse_time: float
    jump_clock: float
    continuous_clock: float
    ou_decay: float
    ou_variance: float
    death_survival: float
    type_transition: np.ndarray = field(repr=False)
    no_replacement_transition: np.ndarray = field(repr=False)
    replacement_refresh_transition: np.ndarray = field(repr=False)
    immigrant_survivor_mean: float
    immigrant_terminal_type_means: np.ndarray = field(repr=False)
    immigrant_anchor_mean: float
    total_background_intensity: float
    maximum_roundoff_correction: float
    preconditioner_parameter_key: Tuple[object, ...]

    def __init__(
        self,
        *,
        reverse_time: float,
        jump_clock: float,
        continuous_clock: float,
        ou_decay: float,
        ou_variance: float,
        death_survival: float,
        type_transition: object,
        no_replacement_transition: object,
        replacement_refresh_transition: object,
        immigrant_survivor_mean: float,
        immigrant_terminal_type_means: object,
        immigrant_anchor_mean: float,
        total_background_intensity: float,
        maximum_roundoff_correction: float,
        preconditioner_parameter_key: Tuple[object, ...],
        _construction_token: object = None,
    ) -> None:
        if _construction_token is not _PROPAGATION_TOKEN:
            raise TypeError(
                "propagation certificates can only be constructed by a preconditioner"
            )
        key = _validated_trusted_key(
            preconditioner_parameter_key,
            name="preconditioner_parameter_key",
        )
        transition = np.asarray(type_transition, dtype=np.float64)
        no_replacement = np.asarray(no_replacement_transition, dtype=np.float64)
        refreshed = np.asarray(replacement_refresh_transition, dtype=np.float64)
        if transition.ndim != 2 or transition.shape[0] != transition.shape[1]:
            raise ValueError("type_transition must be square")
        if (
            no_replacement.shape != transition.shape
            or refreshed.shape != transition.shape
        ):
            raise ValueError("propagation transition arrays must have the same shape")
        terminal_means = np.asarray(immigrant_terminal_type_means, dtype=np.float64)
        if terminal_means.shape != (transition.shape[0],):
            raise ValueError("immigrant terminal means must match the type count")
        object.__setattr__(self, "reverse_time", reverse_time)
        object.__setattr__(self, "jump_clock", jump_clock)
        object.__setattr__(self, "continuous_clock", continuous_clock)
        object.__setattr__(self, "ou_decay", ou_decay)
        object.__setattr__(self, "ou_variance", ou_variance)
        object.__setattr__(self, "death_survival", death_survival)
        object.__setattr__(self, "type_transition", _immutable_float_array(transition))
        object.__setattr__(
            self,
            "no_replacement_transition",
            _immutable_float_array(no_replacement),
        )
        object.__setattr__(
            self,
            "replacement_refresh_transition",
            _immutable_float_array(refreshed),
        )
        object.__setattr__(self, "immigrant_survivor_mean", immigrant_survivor_mean)
        object.__setattr__(
            self,
            "immigrant_terminal_type_means",
            _immutable_float_array(terminal_means),
        )
        object.__setattr__(self, "immigrant_anchor_mean", immigrant_anchor_mean)
        object.__setattr__(
            self, "total_background_intensity", total_background_intensity
        )
        object.__setattr__(
            self, "maximum_roundoff_correction", maximum_roundoff_correction
        )
        object.__setattr__(self, "preconditioner_parameter_key", key)

    @property
    def is_terminal_identity(self) -> bool:
        return self.jump_clock == 0.0 and self.continuous_clock == 0.0

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "association-propagation-v1",
            self.preconditioner_parameter_key,
            self.reverse_time,
        )


@dataclass(frozen=True, eq=False, init=False)
class OneOccurrenceTerminalKernel:
    """Sub-Markov terminal mixture for one current occurrence."""

    source: TransformedEvent
    propagation_parameter_key: Tuple[object, ...]
    surviving_terminal_type_masses: np.ndarray = field(repr=False)
    no_replacement_terminal_type_masses: np.ndarray = field(repr=False)
    replacement_refresh_terminal_type_masses: np.ndarray = field(repr=False)
    effective_detection_probability: float

    def __init__(
        self,
        source: TransformedEvent,
        propagation_parameter_key: Tuple[object, ...],
        surviving_terminal_type_masses: object,
        no_replacement_terminal_type_masses: object,
        replacement_refresh_terminal_type_masses: object,
        effective_detection_probability: float,
        *,
        _construction_token: object = None,
    ) -> None:
        if _construction_token is not _ONE_OCCURRENCE_TOKEN:
            raise TypeError(
                "one-occurrence kernels can only be constructed by a preconditioner"
            )
        if type(source) is not TransformedEvent:
            raise TypeError("source must be an exact TransformedEvent")
        key = _validated_trusted_key(
            propagation_parameter_key,
            name="propagation_parameter_key",
        )
        surviving = np.asarray(surviving_terminal_type_masses, dtype=np.float64)
        no_replacement = np.asarray(
            no_replacement_terminal_type_masses, dtype=np.float64
        )
        refreshed = np.asarray(
            replacement_refresh_terminal_type_masses, dtype=np.float64
        )
        if (
            surviving.ndim != 1
            or no_replacement.shape != surviving.shape
            or refreshed.shape != surviving.shape
        ):
            raise ValueError("one-occurrence mass vectors must have one shared shape")
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "propagation_parameter_key", key)
        object.__setattr__(
            self,
            "surviving_terminal_type_masses",
            _immutable_float_array(surviving),
        )
        object.__setattr__(
            self,
            "no_replacement_terminal_type_masses",
            _immutable_float_array(no_replacement),
        )
        object.__setattr__(
            self,
            "replacement_refresh_terminal_type_masses",
            _immutable_float_array(refreshed),
        )
        object.__setattr__(
            self,
            "effective_detection_probability",
            effective_detection_probability,
        )

    @property
    def survival_probability(self) -> float:
        return math.fsum(float(value) for value in self.surviving_terminal_type_masses)

    @property
    def miss_probability(self) -> float:
        return 1.0 - self.effective_detection_probability


@dataclass(frozen=True, eq=False, init=False)
class BoundPreconditionerEvaluation:
    """Association density authenticated to time, state, outcome, and model."""

    reverse_time: float
    state: TransformedConfiguration
    outcome: PreconditionerObservation
    restricted: bool
    preconditioner_parameter_key: Tuple[object, ...]
    association_evaluation: AssociationDensityEvaluation = field(repr=False)

    def __init__(
        self,
        reverse_time: float,
        state: TransformedConfiguration,
        outcome: PreconditionerObservation,
        restricted: bool,
        preconditioner_parameter_key: Tuple[object, ...],
        association_evaluation: AssociationDensityEvaluation,
        *,
        _construction_token: object = None,
    ) -> None:
        if _construction_token is not _EVALUATION_TOKEN:
            raise TypeError(
                "bound evaluations can only be constructed by a preconditioner"
            )
        if type(state) is not tuple or any(
            type(event) is not TransformedEvent for event in state
        ):
            raise TypeError("state must be a canonical transformed configuration")
        if state != tuple(sorted(state, key=TransformedEvent.model_key)):
            raise ValueError("state must be canonical")
        if type(association_evaluation) is not AssociationDensityEvaluation:
            raise TypeError("association_evaluation has the wrong type")
        object.__setattr__(self, "reverse_time", reverse_time)
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "restricted", bool(restricted))
        object.__setattr__(
            self,
            "preconditioner_parameter_key",
            _validated_trusted_key(
                preconditioner_parameter_key,
                name="preconditioner_parameter_key",
            ),
        )
        object.__setattr__(self, "association_evaluation", association_evaluation)

    @property
    def clean_log_density(self) -> float:
        return self.association_evaluation.clean_log_density

    @property
    def log_density(self) -> float:
        return self.association_evaluation.log_density

    @property
    def clean_density(self) -> float:
        return self.association_evaluation.clean_density

    @property
    def density(self) -> float:
        return self.association_evaluation.density

    @property
    def contamination_probability(self) -> float:
        return self.association_evaluation.contamination_probability

    @property
    def clean_is_structural_zero(self) -> bool:
        return self.association_evaluation.clean_is_structural_zero

    def parameter_key(self) -> Tuple[object, ...]:
        outcome_key = (
            ("overflow",)
            if self.outcome is OVERFLOW_OBSERVATION
            else tuple(event.model_key() for event in self.outcome)
        )
        return (
            "bound-association-preconditioner-evaluation-v1",
            self.preconditioner_parameter_key,
            self.reverse_time,
            tuple(event.model_key() for event in self.state),
            outcome_key,
            self.restricted,
        )


@dataclass(frozen=True, eq=False, init=False)
class BoundPreconditionerGradients:
    """Retained source-coordinate gradients with bound provenance."""

    reverse_time: float
    state: TransformedConfiguration
    outcome: TransformedConfiguration
    preconditioner_parameter_key: Tuple[object, ...]
    coordinate_gradients: AssociationCoordinateGradients = field(repr=False)

    def __init__(
        self,
        reverse_time: float,
        state: TransformedConfiguration,
        outcome: TransformedConfiguration,
        preconditioner_parameter_key: Tuple[object, ...],
        coordinate_gradients: AssociationCoordinateGradients,
        *,
        _construction_token: object = None,
    ) -> None:
        if _construction_token is not _GRADIENT_TOKEN:
            raise TypeError(
                "bound gradients can only be constructed by a preconditioner"
            )
        if type(coordinate_gradients) is not AssociationCoordinateGradients:
            raise TypeError("coordinate_gradients has the wrong type")
        object.__setattr__(self, "reverse_time", reverse_time)
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(
            self,
            "preconditioner_parameter_key",
            _validated_trusted_key(
                preconditioner_parameter_key,
                name="preconditioner_parameter_key",
            ),
        )
        object.__setattr__(self, "coordinate_gradients", coordinate_gradients)

    @property
    def clean_log_density(self) -> float:
        return self.coordinate_gradients.clean_log_density

    @property
    def log_density(self) -> float:
        return self.coordinate_gradients.log_density

    @property
    def coordinate_offsets(self) -> Tuple[int, ...]:
        return self.coordinate_gradients.coordinate_offsets

    @property
    def gradients(self) -> np.ndarray:
        return self.coordinate_gradients.gradients

    @property
    def clean_edge_log_marginals(self) -> np.ndarray:
        return self.coordinate_gradients.clean_edge_log_marginals

    @property
    def edge_log_marginals(self) -> np.ndarray:
        return self.coordinate_gradients.edge_log_marginals


@dataclass(frozen=True, eq=False, init=False)
class BoundPreconditionerEditRatio:
    """One occurrence-level birth, death, or replacement log guide ratio."""

    reverse_time: float
    edit_kind: str
    source_state: TransformedConfiguration
    destination_state: TransformedConfiguration
    outcome: PreconditionerObservation
    log_ratio: float
    preconditioner_parameter_key: Tuple[object, ...]

    def __init__(
        self,
        *,
        reverse_time: float,
        edit_kind: str,
        source_state: TransformedConfiguration,
        destination_state: TransformedConfiguration,
        outcome: PreconditionerObservation,
        log_ratio: float,
        preconditioner_parameter_key: Tuple[object, ...],
        _construction_token: object = None,
    ) -> None:
        if _construction_token is not _EDGE_RATIO_TOKEN:
            raise TypeError("edit ratios can only be constructed by a preconditioner")
        if edit_kind not in ("birth", "death", "replacement"):
            raise ValueError("unknown edit kind")
        if not math.isfinite(log_ratio):
            raise ValueError("positive-guide log ratios must be finite")
        object.__setattr__(self, "reverse_time", reverse_time)
        object.__setattr__(self, "edit_kind", edit_kind)
        object.__setattr__(self, "source_state", source_state)
        object.__setattr__(self, "destination_state", destination_state)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "log_ratio", log_ratio)
        object.__setattr__(
            self,
            "preconditioner_parameter_key",
            _validated_trusted_key(
                preconditioner_parameter_key,
                name="preconditioner_parameter_key",
            ),
        )

    @property
    def ratio(self) -> float:
        return _ordinary_from_log(self.log_ratio, name="guide edit ratio")


@dataclass(frozen=True, eq=False, init=False)
class CapBoundaryDefectEvaluation:
    """Exact blocked-birth contribution, separate from all other defects."""

    reverse_time: float
    state: TransformedConfiguration
    outcome: PreconditionerObservation
    at_cap: bool
    blocked_birth_rate: float
    guide_log_density: float
    integrated_birth_log_density: Optional[float]
    integral_ratio_minus_one: float
    cap_boundary_defect: float
    preconditioner_parameter_key: Tuple[object, ...]

    def __init__(self, *, _construction_token: object = None, **values: object) -> None:
        if _construction_token is not _CAP_DEFECT_TOKEN:
            raise TypeError("cap defects can only be constructed by a preconditioner")
        names = (
            "reverse_time",
            "state",
            "outcome",
            "at_cap",
            "blocked_birth_rate",
            "guide_log_density",
            "integrated_birth_log_density",
            "integral_ratio_minus_one",
            "cap_boundary_defect",
            "preconditioner_parameter_key",
        )
        if set(values) != set(names):
            raise TypeError("cap defect fields do not match the sealed schema")
        state = values["state"]
        if (
            type(state) is not tuple
            or any(type(event) is not TransformedEvent for event in state)
            or state != tuple(sorted(state, key=TransformedEvent.model_key))
        ):
            raise TypeError("cap defect state must be a canonical configuration")
        if type(values["at_cap"]) is not bool:
            raise TypeError("at_cap must be an exact bool")
        for name in (
            "reverse_time",
            "blocked_birth_rate",
            "guide_log_density",
            "integral_ratio_minus_one",
            "cap_boundary_defect",
        ):
            values[name] = _validated_real(values[name], name=name)
        if values["blocked_birth_rate"] < 0.0:
            raise ValueError("blocked_birth_rate must be nonnegative")
        integrated = values["integrated_birth_log_density"]
        if integrated is not None:
            values["integrated_birth_log_density"] = _validated_real(
                integrated, name="integrated_birth_log_density"
            )
        _validated_trusted_key(
            values["preconditioner_parameter_key"],
            name="preconditioner_parameter_key",
        )
        if not values["at_cap"] and (
            values["blocked_birth_rate"] != 0.0
            or values["integrated_birth_log_density"] is not None
            or values["integral_ratio_minus_one"] != 0.0
            or values["cap_boundary_defect"] != 0.0
        ):
            raise ValueError("non-cap defect records must contain exact zeros")
        for name in names:
            object.__setattr__(self, name, values[name])

    @property
    def blocked_birth_action_over_guide(self) -> float:
        return -self.cap_boundary_defect


@dataclass(frozen=True)
class BirthProposalSample:
    """One event and its joint proposal log density relative to type/Lebesgue."""

    event: TransformedEvent
    proposal_log_density: float

    def __post_init__(self) -> None:
        if type(self.event) is not TransformedEvent:
            raise TypeError("event must be an exact TransformedEvent")
        value = _validated_real(self.proposal_log_density, name="proposal_log_density")
        object.__setattr__(self, "proposal_log_density", value)


@dataclass(frozen=True, eq=False, init=False)
class CapBoundaryProposalEstimate:
    """Unnormalized importance estimate of only the cap-boundary component."""

    reverse_time: float
    state: TransformedConfiguration
    outcome: PreconditionerObservation
    sample_count: int
    proposal_key: Tuple[object, ...]
    stream_key: Tuple[object, ...]
    sample_digest: str
    importance_weight_sum: float
    integral_ratio_minus_one_estimate: float
    integral_standard_error: float
    cap_boundary_estimate: float
    cap_boundary_standard_error: float
    exact_cap_boundary_defect: Optional[float]
    preconditioner_parameter_key: Tuple[object, ...]
    sampling_provenance_certified: bool
    self_normalized: bool = False

    def __init__(self, *, _construction_token: object = None, **values: object) -> None:
        if _construction_token is not _PROPOSAL_ESTIMATE_TOKEN:
            raise TypeError(
                "proposal estimates can only be constructed by a preconditioner"
            )
        names = (
            "reverse_time",
            "state",
            "outcome",
            "sample_count",
            "proposal_key",
            "stream_key",
            "sample_digest",
            "importance_weight_sum",
            "integral_ratio_minus_one_estimate",
            "integral_standard_error",
            "cap_boundary_estimate",
            "cap_boundary_standard_error",
            "exact_cap_boundary_defect",
            "preconditioner_parameter_key",
            "sampling_provenance_certified",
        )
        if set(values) != set(names):
            raise TypeError("proposal estimate fields do not match the sealed schema")
        state = values["state"]
        if (
            type(state) is not tuple
            or any(type(event) is not TransformedEvent for event in state)
            or state != tuple(sorted(state, key=TransformedEvent.model_key))
        ):
            raise TypeError("proposal state must be a canonical configuration")
        values["sample_count"] = _validated_nonnegative_integer(
            values["sample_count"],
            name="sample_count",
            maximum=MAX_PRECONDITIONER_PROPOSAL_SAMPLES,
        )
        if values["sample_count"] < 2:
            raise ValueError("proposal estimates require at least two samples")
        for name in ("proposal_key", "stream_key"):
            _validated_key(values[name], name=name)
        _validated_trusted_key(
            values["preconditioner_parameter_key"],
            name="preconditioner_parameter_key",
        )
        digest = values["sample_digest"]
        if type(digest) is not str or len(digest) != 64:
            raise ValueError("sample_digest must be a 64-character hex digest")
        try:
            int(digest, 16)
        except ValueError as error:
            raise ValueError("sample_digest must contain hexadecimal text") from error
        for name in (
            "reverse_time",
            "importance_weight_sum",
            "integral_ratio_minus_one_estimate",
            "integral_standard_error",
            "cap_boundary_estimate",
            "cap_boundary_standard_error",
        ):
            values[name] = _validated_real(values[name], name=name)
        if values["importance_weight_sum"] <= 0.0:
            raise ValueError("importance_weight_sum must be positive")
        if (
            values["integral_standard_error"] < 0.0
            or values["cap_boundary_standard_error"] < 0.0
        ):
            raise ValueError("proposal standard errors must be nonnegative")
        exact = values["exact_cap_boundary_defect"]
        if exact is not None:
            values["exact_cap_boundary_defect"] = _validated_real(
                exact, name="exact_cap_boundary_defect"
            )
        if type(values["sampling_provenance_certified"]) is not bool:
            raise TypeError("sampling_provenance_certified must be an exact bool")
        for name in names:
            object.__setattr__(self, name, values[name])
        object.__setattr__(self, "self_normalized", False)


def _guide_range_contract_key(values: Mapping[str, object]) -> Tuple[object, ...]:
    minimum_covariance = values["minimum_covariance_eigenvalue_lower_bound"]
    return (
        values["schema_version"],
        values["certificate_scope"],
        values["preconditioner_parameter_key"],
        values["outcome_key"],
        values["state_cap"],
        values["maximum_coordinate_count"],
        values["contamination_probability"],
        values["guide_lower_bound"],
        values["clean_log_upper_bound"],
        values["guide_log_upper_bound"],
        values["guide_upper_bound"],
        values["log_guide_oscillation_bound"],
        values["log_guide_gradient_norm_bound"],
        values["log_guide_hessian_operator_norm_bound"],
        values["covariance_witness_count"],
        minimum_covariance,
        values["maximum_whitened_matrix_norm_bound"],
        values["analytic_work"],
    )


@dataclass(frozen=True, eq=False, init=False)
class AnalyticGuideRangeCertificate:
    """Global model-level range and regularity certificate for one outcome.

    The certificate covers the exact real-arithmetic analytic guide on every
    reverse time, every state admitted by the bound process cap, and every
    coordinate on each fixed typed-occurrence chart.  This uses the model's
    normalized probability-simplex and Markov-kernel semantics; represented
    normalization drift belongs to the missing floating-point bridge.  The
    certificate deliberately does
    not enclose the floating-point error of :meth:`evaluate` or
    :meth:`coordinate_gradients`, so it is not an operational thinning or
    sampler-admission certificate.  The two coordinate fields bound the full
    flattened Euclidean norm of ``grad(log h)`` and the Euclidean operator
    norm of ``Hessian(log h)``; they are not derivative bounds for ``h``.
    """

    schema_version: str
    certificate_scope: str
    preconditioner_parameter_key: Tuple[object, ...]
    outcome: PreconditionerObservation
    outcome_key: Tuple[object, ...]
    state_cap: int
    maximum_coordinate_count: int
    contamination_probability: float
    guide_lower_bound: float
    clean_log_upper_bound: float
    guide_log_upper_bound: float
    guide_upper_bound: float
    log_guide_oscillation_bound: float
    log_guide_gradient_norm_bound: float
    log_guide_hessian_operator_norm_bound: float
    covariance_witness_count: int
    minimum_covariance_eigenvalue_lower_bound: Optional[float]
    maximum_whitened_matrix_norm_bound: float
    analytic_work: int
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("AnalyticGuideRangeCertificate cannot be subclassed")

    def __reduce__(self) -> object:
        raise TypeError("guide range certificates are not pickleable")

    def __init__(
        self, *, _construction_token: object = None, **raw_values: object
    ) -> None:
        if _construction_token is not _GUIDE_RANGE_CERTIFICATE_TOKEN:
            raise TypeError(
                "guide range certificates can only be constructed by a "
                "preconditioner"
            )
        names = (
            "schema_version",
            "certificate_scope",
            "preconditioner_parameter_key",
            "outcome",
            "outcome_key",
            "state_cap",
            "maximum_coordinate_count",
            "contamination_probability",
            "guide_lower_bound",
            "clean_log_upper_bound",
            "guide_log_upper_bound",
            "guide_upper_bound",
            "log_guide_oscillation_bound",
            "log_guide_gradient_norm_bound",
            "log_guide_hessian_operator_norm_bound",
            "covariance_witness_count",
            "minimum_covariance_eigenvalue_lower_bound",
            "maximum_whitened_matrix_norm_bound",
            "analytic_work",
            "certificate_sha256",
        )
        if set(raw_values) != set(names):
            raise TypeError(
                "guide range certificate fields do not match the sealed schema"
            )
        values = dict(raw_values)
        if values["schema_version"] != ANALYTIC_GUIDE_RANGE_SCHEMA_VERSION:
            raise ValueError("unknown guide range certificate schema")
        if values["certificate_scope"] != ANALYTIC_GUIDE_RANGE_CERTIFICATE_SCOPE:
            raise ValueError("unknown guide range certificate scope")
        _validated_trusted_key(
            values["preconditioner_parameter_key"],
            name="preconditioner_parameter_key",
        )

        outcome = values["outcome"]
        if outcome is OVERFLOW_OBSERVATION:
            expected_outcome_key: Tuple[object, ...] = ("overflow",)
        else:
            if type(outcome) is not tuple:
                raise TypeError("retained certificate outcome must be an exact tuple")
            if len(outcome) > MAX_ASSOCIATION_OCCURRENCES:
                raise AssociationObservationResourceError(
                    "retained certificate outcome exceeds the occurrence limit"
                )
            checked_keys = []
            aggregate_coordinates = 0
            for event in outcome:
                if type(event) is not TransformedEvent:
                    raise TypeError(
                        "retained certificate outcome must contain exact events"
                    )
                if type(event.event_type) is not int:
                    raise TypeError("certificate event type must be an exact int")
                if type(event.coordinates) is not tuple:
                    raise TypeError(
                        "certificate event coordinates must be an exact tuple"
                    )
                if len(event.coordinates) > MAX_AFFINE_OBSERVATION_DIMENSION:
                    raise AssociationObservationResourceError(
                        "certificate event exceeds the affine coordinate limit"
                    )
                aggregate_coordinates += len(event.coordinates)
                if aggregate_coordinates > MAX_REFERENCE_DENSITY_COORDINATES:
                    raise AssociationObservationResourceError(
                        "certificate outcome exceeds the aggregate coordinate limit"
                    )
                if any(
                    type(coordinate) is not float
                    or not math.isfinite(coordinate)
                    or (coordinate == 0.0 and math.copysign(1.0, coordinate) < 0.0)
                    for coordinate in event.coordinates
                ):
                    raise TypeError(
                        "certificate event coordinates must be canonical floats"
                    )
                checked_keys.append((event.event_type, event.coordinates))
            if tuple(checked_keys) != tuple(sorted(checked_keys)):
                raise ValueError("retained certificate outcome must be canonical")
            expected_outcome_key = ("retained", tuple(checked_keys))
        if type(values["outcome_key"]) is not tuple:
            raise TypeError("outcome_key must be an exact tuple")
        if values["outcome_key"] != expected_outcome_key:
            raise ValueError("outcome_key does not match the canonical outcome")

        for name, maximum in (
            ("state_cap", MAX_CONFIGURATION_CARDINALITY),
            ("maximum_coordinate_count", MAX_REFERENCE_DENSITY_COORDINATES),
            (
                "covariance_witness_count",
                MAX_PRECONDITIONER_GAUSSIAN_COMPONENTS + MAX_PRECONDITIONER_TYPES,
            ),
            ("analytic_work", MAX_PRECONDITIONER_GUIDE_CERTIFICATE_WORK),
        ):
            values[name] = _validated_nonnegative_integer(
                values[name], name=name, maximum=maximum
            )

        float_names = (
            "contamination_probability",
            "guide_lower_bound",
            "guide_log_upper_bound",
            "guide_upper_bound",
            "log_guide_oscillation_bound",
            "log_guide_gradient_norm_bound",
            "log_guide_hessian_operator_norm_bound",
            "maximum_whitened_matrix_norm_bound",
        )
        for name in float_names:
            if type(values[name]) is not float:
                raise TypeError("%s must be an exact float" % name)
            values[name] = _validated_real(values[name], name=name)
            if values[name] < 0.0 and name not in ("guide_log_upper_bound",):
                raise ValueError("%s must be nonnegative" % name)
            if values[name] == 0.0 and math.copysign(1.0, values[name]) < 0.0:
                raise ValueError("%s must use canonical positive zero" % name)
        clean_log = values["clean_log_upper_bound"]
        if type(clean_log) is not float:
            raise TypeError("clean_log_upper_bound must be an exact float")
        if math.isnan(clean_log) or clean_log == math.inf:
            raise ValueError("clean_log_upper_bound must be finite or -inf")
        if clean_log == 0.0 and math.copysign(1.0, clean_log) < 0.0:
            raise ValueError("clean_log_upper_bound must use canonical zero")
        values["clean_log_upper_bound"] = clean_log

        if not 0.0 < values["contamination_probability"] < 1.0:
            raise ValueError("contamination_probability must lie in (0, 1)")
        if values["guide_lower_bound"] != values["contamination_probability"]:
            raise ValueError("guide lower bound must equal contamination probability")
        if values["guide_upper_bound"] < values["guide_lower_bound"]:
            raise ValueError("guide upper bound lies below its lower bound")
        if values["log_guide_oscillation_bound"] < 0.0:
            raise ValueError("guide oscillation bound must be nonnegative")

        witness_count = values["covariance_witness_count"]
        minimum_covariance = values["minimum_covariance_eigenvalue_lower_bound"]
        if witness_count == 0:
            if minimum_covariance is not None:
                raise ValueError(
                    "an atomic certificate must not fabricate a covariance witness"
                )
        else:
            if type(minimum_covariance) is not float:
                raise TypeError("minimum covariance witness must be an exact float")
            checked_minimum = _validated_real(
                minimum_covariance,
                name="minimum_covariance_eigenvalue_lower_bound",
            )
            if checked_minimum <= 0.0:
                raise ValueError("minimum covariance witness must be positive")
            values["minimum_covariance_eigenvalue_lower_bound"] = checked_minimum

        digest = values["certificate_sha256"]
        if type(digest) is not str or len(digest) != 64:
            raise ValueError("certificate_sha256 must be a 64-character digest")
        try:
            int(digest, 16)
        except ValueError as error:
            raise ValueError(
                "certificate_sha256 must contain hexadecimal text"
            ) from error
        expected_digest = _plain_key_sha256(
            _guide_range_contract_key(values),
            domain=b"heterodiff-analytic-guide-range-certificate-v1\x00",
        )
        if digest != expected_digest:
            raise ValueError("certificate_sha256 does not match certificate fields")

        for name in names:
            object.__setattr__(self, name, values[name])

    @property
    def operational_sampler_admissible(self) -> bool:
        """This model-level certificate never authorizes operational thinning."""

        return False

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "bound-analytic-association-guide-range-certificate-v1",
            self.preconditioner_parameter_key,
            self.outcome_key,
            self.certificate_sha256,
        )


@dataclass(frozen=True)
class _PropagationContext:
    propagation: AssociationPropagation
    no_replacement_channels: Mapping[Tuple[int, int], AffineGaussianFiberChannel]


class AnalyticAssociationPreconditioner:
    """Bound analytic guide for one process, observation law, and context."""

    __slots__ = (
        "_process",
        "_observation_reference",
        "_channel",
        "_clutter",
        "_detection",
        "_contamination_probability",
        "_context_key",
        "_type_positions",
        "_generator",
        "_replacement_matrix",
        "_replacement_reachability",
        "_outgoing",
        "_weights",
        "_reference_detected_probability",
        "_reference_fiber_channels",
        "_gaussian_component_count",
        "_covariance_work",
        "_parameter_key",
    )

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("AnalyticAssociationPreconditioner is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("AnalyticAssociationPreconditioner is immutable")

    def __init__(
        self,
        process: ReversibleHybridReference,
        observation_reference: CollapsedPoissonObservationReference,
        terminal_channel: TypedAffineGaussianObservationChannel,
        terminal_clutter: TypedGaussianClutterIntensity,
        detection_probability_by_type: Mapping[int, float],
        *,
        contamination_probability: object,
        context_key: Tuple[object, ...] = (),
    ) -> None:
        if type(process) is not ReversibleHybridReference:
            raise TypeError("process must be an exact ReversibleHybridReference")
        if type(observation_reference) is not CollapsedPoissonObservationReference:
            raise TypeError("observation_reference has the wrong type")
        if type(terminal_channel) is not TypedAffineGaussianObservationChannel:
            raise TypeError("terminal_channel has the wrong type")
        if type(terminal_clutter) is not TypedGaussianClutterIntensity:
            raise TypeError("terminal_clutter has the wrong type")
        reference_key = observation_reference.parameter_key()
        if terminal_channel.observation_reference.parameter_key() != reference_key:
            raise ValueError("terminal channel and observation references differ")
        if terminal_clutter.observation_reference.parameter_key() != reference_key:
            raise ValueError("terminal clutter and observation references differ")
        latent_reference = process.reference
        if terminal_channel.source_type_ids != latent_reference.type_ids:
            raise ValueError("terminal channel source types must equal process types")
        if dict(terminal_channel.source_type_dimensions) != dict(
            latent_reference.type_dimensions
        ):
            raise ValueError(
                "terminal channel source dimensions must equal process dimensions"
            )
        type_count = len(latent_reference.type_ids)
        if type_count > MAX_PRECONDITIONER_TYPES:
            raise AssociationObservationResourceError(
                "preconditioner type count exceeds %d" % MAX_PRECONDITIONER_TYPES
            )
        exponential_work = (2 * type_count) ** 3
        if exponential_work > MAX_PRECONDITIONER_EXPONENTIAL_WORK:
            raise AssociationObservationResourceError(
                "augmented type exponential exceeds the work limit"
            )
        if not isinstance(detection_probability_by_type, Mapping):
            raise TypeError("detection_probability_by_type must be a mapping")
        detection_keys = _bounded_tuple(
            detection_probability_by_type.keys(),
            name="detection_probability_by_type keys",
            maximum_items=type_count + 1,
        )
        if len(detection_keys) != type_count or set(detection_keys) != set(
            latent_reference.type_ids
        ):
            raise ValueError(
                "detection mapping must specify every process type exactly once"
            )
        detection = np.asarray(
            [
                _validated_probability(
                    detection_probability_by_type[type_id],
                    name="detection probability for type %d" % type_id,
                )
                for type_id in latent_reference.type_ids
            ],
            dtype=np.float64,
        )
        epsilon = _validated_probability(
            contamination_probability,
            name="contamination_probability",
            strictly_positive=True,
            strictly_below_one=True,
        )
        if epsilon < float(np.finfo(np.float64).tiny):
            raise ValueError("contamination_probability must be a normal float64 value")
        checked_context_key = _validated_key(context_key, name="context_key")
        positions = {
            type_id: index for index, type_id in enumerate(latent_reference.type_ids)
        }
        replacement = np.zeros((type_count, type_count), dtype=np.float64)
        for source_type in latent_reference.type_ids:
            source = positions[source_type]
            for destination_type in latent_reference.type_ids:
                if source_type == destination_type:
                    continue
                replacement[
                    source, positions[destination_type]
                ] = process.rates.replacement_rate(source_type, destination_type)
        outgoing = replacement.sum(axis=1)
        generator = replacement.copy()
        np.fill_diagonal(generator, -outgoing)
        reachability = replacement > 0.0
        for intermediate in range(type_count):
            reachability |= (
                reachability[:, intermediate, None]
                & reachability[None, intermediate, :]
            )
        weights = np.asarray(
            [
                latent_reference.type_weights[type_id]
                for type_id in latent_reference.type_ids
            ],
            dtype=np.float64,
        )
        stationarity = weights @ generator
        if np.max(np.abs(stationarity)) > PRECONDITIONER_NUMERICAL_ATOL:
            raise ValueError("process type replacement generator does not preserve nu")
        detected_terms = []
        for weight, probability in zip(weights, detection):
            product = float(weight) * float(probability)
            if probability > 0.0 and product == 0.0:
                raise AssociationPreconditionerNumericalError(
                    "positive reference detection component underflows float64"
                )
            detected_terms.append(product)
        reference_detected = _strict_nonnegative_fsum(
            detected_terms, name="reference-averaged detection"
        )
        if np.any(detection > 0.0) and reference_detected == 0.0:
            raise AssociationPreconditionerNumericalError(
                "positive reference-averaged detection underflows float64"
            )
        if reference_detected < 0.0 or reference_detected > 1.0:
            raise ArithmeticError("reference-averaged detection lies outside [0, 1]")
        miss_terms = []
        for weight, probability in zip(weights, detection):
            miss_product = float(weight) * (1.0 - float(probability))
            if probability < 1.0 and miss_product == 0.0:
                raise AssociationPreconditionerNumericalError(
                    "positive reference miss component underflows float64"
                )
            miss_terms.append(miss_product)
        reference_miss = _strict_nonnegative_fsum(
            miss_terms, name="reference-averaged miss"
        )
        if np.any(detection < 1.0) and (
            reference_miss == 0.0 or reference_detected == 1.0
        ):
            raise AssociationPreconditionerNumericalError(
                "positive reference-averaged miss is below float64 resolution"
            )

        component_specs = []
        covariance_work = 0
        for source_type in latent_reference.type_ids:
            source_position = positions[source_type]
            input_dimension = latent_reference.type_dimensions[source_type]
            for observation_type in observation_reference.type_ids:
                observation_position = terminal_channel._observation_positions[
                    observation_type
                ]
                output_dimension = observation_reference.type_dimensions[
                    observation_type
                ]
                if (
                    output_dimension == 0
                    or float(
                        terminal_channel.stratum_probability[
                            source_position, observation_position
                        ]
                    )
                    == 0.0
                ):
                    continue
                component_specs.append((source_type, observation_type))
                if len(component_specs) > MAX_PRECONDITIONER_GAUSSIAN_COMPONENTS:
                    raise AssociationObservationResourceError(
                        "propagated Gaussian component count exceeds the limit"
                    )
                covariance_work += output_dimension**3 + output_dimension**2 * max(
                    input_dimension, 1
                )
                if covariance_work > MAX_PRECONDITIONER_COVARIANCE_WORK:
                    raise AssociationObservationResourceError(
                        "aggregate propagated covariance work exceeds the limit"
                    )
        reference_channels = {}
        for source_type, observation_type in component_specs:
            terminal_fiber = terminal_channel.fiber_channels[
                (source_type, observation_type)
            ]
            try:
                with np.errstate(over="raise", invalid="raise"):
                    gram = terminal_fiber.matrix @ terminal_fiber.matrix.T
                    covariance = terminal_fiber.covariance + gram
            except FloatingPointError as error:
                raise AssociationPreconditionerNumericalError(
                    "reference-averaged channel covariance is not representable"
                ) from error
            nonzero_rows = np.any(terminal_fiber.matrix != 0.0, axis=1)
            if np.any(nonzero_rows & (np.diag(gram) == 0.0)):
                raise AssociationPreconditionerNumericalError(
                    "reference channel Gram variance underflows float64"
                )
            if np.any(
                (gram != 0.0) & (np.abs(gram) < float(np.finfo(np.float64).tiny))
            ):
                raise AssociationPreconditionerNumericalError(
                    "reference channel Gram contains a subnormal contribution"
                )
            if np.any((gram != 0.0) & (covariance == terminal_fiber.covariance)):
                raise AssociationPreconditionerNumericalError(
                    "reference channel Gram is below addition resolution"
                )
            if np.any((terminal_fiber.covariance != 0.0) & (covariance == gram)):
                raise AssociationPreconditionerNumericalError(
                    "terminal covariance is below reference-channel addition resolution"
                )
            covariance_diagonal = np.diag(covariance)
            if np.any(
                (covariance_diagonal > 0.0)
                & (covariance_diagonal < float(np.finfo(np.float64).tiny))
            ):
                raise AssociationPreconditionerNumericalError(
                    "reference channel variance is subnormal"
                )
            reference_channels[
                (source_type, observation_type)
            ] = _propagated_affine_gaussian_fiber(
                np.zeros((terminal_fiber.output_dimension, 0), dtype=np.float64),
                terminal_fiber.bias,
                covariance,
                name="reference-averaged affine Gaussian fiber",
            )

        parameter_key = (
            "analytic-association-preconditioner-v1",
            process.parameter_key(),
            reference_key,
            terminal_channel.parameter_key(),
            terminal_clutter.parameter_key(),
            tuple(
                (type_id, float(detection[positions[type_id]]))
                for type_id in latent_reference.type_ids
            ),
            epsilon,
            checked_context_key,
        )
        object.__setattr__(self, "_process", process)
        object.__setattr__(self, "_observation_reference", observation_reference)
        object.__setattr__(self, "_channel", terminal_channel)
        object.__setattr__(self, "_clutter", terminal_clutter)
        object.__setattr__(self, "_detection", _immutable_float_array(detection))
        object.__setattr__(self, "_contamination_probability", epsilon)
        object.__setattr__(self, "_context_key", checked_context_key)
        object.__setattr__(self, "_type_positions", MappingProxyType(positions))
        object.__setattr__(self, "_generator", _immutable_float_array(generator))
        object.__setattr__(
            self, "_replacement_matrix", _immutable_float_array(replacement)
        )
        object.__setattr__(
            self,
            "_replacement_reachability",
            np.frombuffer(
                np.asarray(reachability, dtype=np.bool_).tobytes(order="C"),
                dtype=np.bool_,
            ).reshape(reachability.shape),
        )
        object.__setattr__(self, "_outgoing", _immutable_float_array(outgoing))
        object.__setattr__(self, "_weights", _immutable_float_array(weights))
        object.__setattr__(self, "_reference_detected_probability", reference_detected)
        object.__setattr__(
            self, "_reference_fiber_channels", MappingProxyType(reference_channels)
        )
        object.__setattr__(self, "_gaussian_component_count", len(component_specs))
        object.__setattr__(self, "_covariance_work", covariance_work)
        object.__setattr__(self, "_parameter_key", parameter_key)

    @property
    def process(self) -> ReversibleHybridReference:
        return self._process

    @property
    def observation_reference(self) -> CollapsedPoissonObservationReference:
        return self._observation_reference

    @property
    def terminal_channel(self) -> TypedAffineGaussianObservationChannel:
        return self._channel

    @property
    def terminal_clutter(self) -> TypedGaussianClutterIntensity:
        return self._clutter

    @property
    def detection_probability(self) -> np.ndarray:
        return self._detection

    @property
    def contamination_probability(self) -> float:
        return self._contamination_probability

    @property
    def context_key(self) -> Tuple[object, ...]:
        return self._context_key

    @property
    def reference_detected_probability(self) -> float:
        return self._reference_detected_probability

    @property
    def gaussian_component_count(self) -> int:
        return self._gaussian_component_count

    @property
    def covariance_work(self) -> int:
        return self._covariance_work

    def parameter_key(self) -> Tuple[object, ...]:
        return self._parameter_key

    def _require_live_guide_certificate_binding(self) -> Tuple[object, ...]:
        """Reassemble the model key before issuing or accepting a certificate."""

        if type(self._process) is not ReversibleHybridReference:
            raise TypeError("live preconditioner process has the wrong type")
        if (
            type(self._observation_reference)
            is not CollapsedPoissonObservationReference
        ):
            raise TypeError("live observation reference has the wrong type")
        if type(self._channel) is not TypedAffineGaussianObservationChannel:
            raise TypeError("live terminal channel has the wrong type")
        if type(self._clutter) is not TypedGaussianClutterIntensity:
            raise TypeError("live terminal clutter has the wrong type")
        reference_key = self._observation_reference.parameter_key()
        if self._channel.observation_reference.parameter_key() != reference_key:
            raise ValueError(
                "live terminal channel has a foreign observation reference"
            )
        if self._clutter.observation_reference.parameter_key() != reference_key:
            raise ValueError(
                "live terminal clutter has a foreign observation reference"
            )
        latent_reference = self._process.reference
        if self._channel.source_type_ids != latent_reference.type_ids:
            raise ValueError(
                "live terminal channel source types differ from the process"
            )
        if dict(self._channel.source_type_dimensions) != dict(
            latent_reference.type_dimensions
        ):
            raise ValueError(
                "live terminal channel source dimensions differ from the process"
            )
        detection = self._detection
        if (
            type(detection) is not np.ndarray
            or detection.dtype != np.dtype(np.float64)
            or detection.shape != (len(latent_reference.type_ids),)
            or detection.flags.writeable
            or not detection.flags.c_contiguous
            or not np.all(np.isfinite(detection))
            or np.any((detection == 0.0) & np.signbit(detection))
            or np.any(detection < 0.0)
            or np.any(detection > 1.0)
        ):
            raise ValueError("live detection vector is not canonical")
        epsilon = self._contamination_probability
        if (
            type(epsilon) is not float
            or not math.isfinite(epsilon)
            or not 0.0 < epsilon < 1.0
            or epsilon < float(np.finfo(np.float64).tiny)
        ):
            raise ValueError("live contamination probability is not canonical")
        checked_context = _validated_key(self._context_key, name="context_key")
        rebuilt = (
            "analytic-association-preconditioner-v1",
            self._process.parameter_key(),
            reference_key,
            self._channel.parameter_key(),
            self._clutter.parameter_key(),
            tuple(
                (type_id, float(detection[position]))
                for position, type_id in enumerate(latent_reference.type_ids)
            ),
            epsilon,
            checked_context,
        )
        if type(self._parameter_key) is not tuple:
            raise ValueError("live preconditioner parameters differ from the bound key")
        rebuilt_digest = _plain_key_sha256(
            rebuilt, domain=b"heterodiff-live-preconditioner-key-v1\x00"
        )
        cached_digest = _plain_key_sha256(
            self._parameter_key,
            domain=b"heterodiff-live-preconditioner-key-v1\x00",
        )
        if rebuilt_digest != cached_digest:
            raise ValueError("live preconditioner parameters differ from the bound key")
        return rebuilt

    @staticmethod
    def _guide_outcome_key(
        outcome: PreconditionerObservation,
    ) -> Tuple[object, ...]:
        if outcome is OVERFLOW_OBSERVATION:
            return ("overflow",)
        return (
            "retained",
            tuple((event.event_type, event.coordinates) for event in outcome),
        )

    def _guide_certificate_resource_work(
        self, outcome: PreconditionerObservation
    ) -> int:
        if outcome is OVERFLOW_OBSERVATION:
            return _GUIDE_OVERFLOW_TAIL_TERMS
        source_cap = self.process.reference.total_cap
        type_count = len(self.process.reference.type_ids)
        observation_count = len(outcome)
        polynomial_work = observation_count * (min(source_cap, observation_count) + 1)
        regularity_work = 8 * observation_count * max(type_count, 1)
        covariance_work = 0
        for observed in outcome:
            output_dimension = len(observed.coordinates)
            if output_dimension == 0:
                continue
            observation_position = self.observation_reference.type_ids.index(
                observed.event_type
            )
            active_signal_count = sum(
                1
                for source_position in range(type_count)
                if float(self._detection[source_position]) > 0.0
                and float(
                    self.terminal_channel.stratum_probability[
                        source_position, observation_position
                    ]
                )
                > 0.0
            )
            covariance_work += (active_signal_count + 1) * output_dimension**2
        total = polynomial_work + regularity_work + covariance_work + 1
        if total > MAX_PRECONDITIONER_GUIDE_CERTIFICATE_WORK:
            raise AssociationObservationResourceError(
                "guide range certification exceeds the aggregate work limit "
                "of %d" % MAX_PRECONDITIONER_GUIDE_CERTIFICATE_WORK
            )
        return total

    @staticmethod
    def _guide_positive_range_bounds(
        clean_log_upper: float, epsilon: float
    ) -> Tuple[float, float, float]:
        if clean_log_upper == -math.inf:
            return (
                _outward_log_fraction(
                    _fraction_from_float(epsilon),
                    name="structural guide log upper bound",
                ),
                epsilon,
                0.0,
            )
        epsilon_fraction = _fraction_from_float(epsilon)
        one_minus = Fraction(1) - epsilon_fraction
        log_epsilon = _outward_log_fraction(
            epsilon_fraction, name="guide contamination log"
        )
        log_scaled_clean = _outward_sum_upper(
            (
                _outward_log_fraction(one_minus, name="guide clean-mixture weight log"),
                clean_log_upper,
            ),
            name="weighted clean guide log upper bound",
        )
        guide_log_upper = _outward_logaddexp_upper(
            log_epsilon,
            log_scaled_clean,
            name="positive guide log upper bound",
        )
        guide_upper = _outward_exp_upper(
            guide_log_upper, name="positive guide upper bound"
        )
        oscillation = _outward_sum_upper(
            (
                guide_log_upper,
                _outward_log_fraction(
                    1 / epsilon_fraction,
                    name="inverse guide lower-bound log",
                ),
            ),
            name="guide log oscillation bound",
        )
        return guide_log_upper, guide_upper, max(0.0, oscillation)

    def certify_guide_range(self, observation: object) -> AnalyticGuideRangeCertificate:
        """Certify the exact analytic guide for one collapsed observation.

        The result is global over reverse time, capped states, and continuous
        coordinates under normalized probability-simplex and Markov-kernel
        semantics.  It is a real-arithmetic theorem witness, not an interval
        enclosure of the pointwise floating-point implementation.
        """

        preconditioner_key = self._require_live_guide_certificate_binding()
        outcome = self.observation_reference.collapse(observation)
        analytic_work = self._guide_certificate_resource_work(outcome)
        source_cap = self.process.reference.total_cap
        maximum_dimension = max(
            self.process.reference.type_dimensions.values(), default=0
        )
        maximum_coordinate_count = source_cap * maximum_dimension
        if maximum_coordinate_count > MAX_REFERENCE_DENSITY_COORDINATES:
            raise AssociationObservationResourceError(
                "guide certificate coordinate count exceeds the process budget"
            )
        epsilon = self.contamination_probability

        covariance_lowers = []
        maximum_whitened_norm = 0.0
        if outcome is OVERFLOW_OBSERVATION:
            clean_log_upper = _unit_poisson_tail_log_reciprocal_upper(
                self.observation_reference.retained_cap
            )
            (
                guide_log_upper,
                guide_upper,
                oscillation,
            ) = self._guide_positive_range_bounds(clean_log_upper, epsilon)
            gradient_bound = 0.0
            hessian_bound = 0.0
        else:
            type_ids = self.process.reference.type_ids
            observation_type_positions = {
                type_id: position
                for position, type_id in enumerate(self.observation_reference.type_ids)
            }
            signal_covariance_cache = {}
            clutter_covariance_cache = {}
            signal_log_bounds = []
            background_log_bounds = []
            signal_gradient_logs = []
            signal_hessian_logs = []
            theta_fraction = _fraction_from_float(self.process.reference.activity)

            for observation_index, observed in enumerate(outcome):
                observation_type = observed.event_type
                observation_position = observation_type_positions[observation_type]
                observation_weight = _fraction_from_float(
                    self.observation_reference.type_weights[observation_type]
                )
                output_dimension = len(observed.coordinates)
                per_type_signal = []
                per_type_gradient = []
                per_type_hessian = []
                for source_position, source_type in enumerate(type_ids):
                    detection = float(self._detection[source_position])
                    stratum = float(
                        self.terminal_channel.stratum_probability[
                            source_position, observation_position
                        ]
                    )
                    if detection == 0.0 or stratum == 0.0:
                        per_type_signal.append(-math.inf)
                        per_type_gradient.append(-math.inf)
                        per_type_hessian.append(-math.inf)
                        continue
                    coefficient = (
                        _fraction_from_float(detection)
                        * _fraction_from_float(stratum)
                        / observation_weight
                    )
                    covariance_lower = None
                    log_whitened_norm = -math.inf
                    if output_dimension > 0:
                        pair = (source_type, observation_type)
                        fiber = _validated_certificate_fiber(
                            self.terminal_channel.fiber_channels[pair],
                            expected_input_dimension=(
                                self.process.reference.type_dimensions[source_type]
                            ),
                            expected_output_dimension=output_dimension,
                            name="terminal signal fiber",
                        )
                        if pair not in signal_covariance_cache:
                            lower = _exact_gershgorin_lower_bound(fiber.covariance)
                            matrix_squared = sum(
                                (
                                    _fraction_from_float(float(value)) ** 2
                                    for value in fiber.matrix.flat
                                ),
                                Fraction(0),
                            )
                            log_norm = _log_whitened_matrix_norm_upper(
                                matrix_squared,
                                lower,
                                name="terminal whitened matrix norm",
                            )
                            norm = (
                                0.0
                                if log_norm == -math.inf
                                else _outward_sqrt_fraction(
                                    matrix_squared / lower,
                                    name="terminal whitened matrix norm",
                                )
                            )
                            signal_covariance_cache[pair] = (
                                lower,
                                log_norm,
                                norm,
                            )
                            covariance_lowers.append(lower)
                            maximum_whitened_norm = max(maximum_whitened_norm, norm)
                        (
                            covariance_lower,
                            log_whitened_norm,
                            _,
                        ) = signal_covariance_cache[pair]
                    log_signal = _log_gaussian_relative_peak_upper(
                        coefficient,
                        observed.coordinates,
                        covariance_lower,
                        name=(
                            "detected anchor peak for observation %d and type %d"
                            % (observation_index, source_type)
                        ),
                    )
                    per_type_signal.append(log_signal)
                    if log_whitened_norm == -math.inf:
                        per_type_gradient.append(-math.inf)
                        per_type_hessian.append(-math.inf)
                    else:
                        per_type_gradient.append(
                            _outward_sum_upper(
                                (log_signal, log_whitened_norm, -0.5),
                                name="detected anchor gradient bound",
                            )
                        )
                        per_type_hessian.append(
                            _outward_sum_upper(
                                (
                                    log_signal,
                                    log_whitened_norm,
                                    log_whitened_norm,
                                ),
                                name="detected anchor Hessian bound",
                            )
                        )
                signal_log = max(per_type_signal, default=-math.inf)
                signal_log_bounds.append(signal_log)
                signal_gradient_logs.append(tuple(per_type_gradient))
                signal_hessian_logs.append(tuple(per_type_hessian))

                clutter_total = self.terminal_clutter.total_intensity
                clutter_stratum = float(
                    self.terminal_clutter.stratum_probability[observation_position]
                )
                physical_clutter_log = -math.inf
                if clutter_total > 0.0 and clutter_stratum > 0.0:
                    clutter_coefficient = (
                        _fraction_from_float(clutter_total)
                        * _fraction_from_float(clutter_stratum)
                        / observation_weight
                    )
                    clutter_covariance_lower = None
                    if output_dimension > 0:
                        clutter_fiber = _validated_certificate_fiber(
                            self.terminal_clutter.fiber_channels[observation_type],
                            expected_input_dimension=0,
                            expected_output_dimension=output_dimension,
                            name="terminal clutter fiber",
                        )
                        if observation_type not in clutter_covariance_cache:
                            lower = _exact_gershgorin_lower_bound(
                                clutter_fiber.covariance
                            )
                            clutter_covariance_cache[observation_type] = lower
                            covariance_lowers.append(lower)
                        clutter_covariance_lower = clutter_covariance_cache[
                            observation_type
                        ]
                    physical_clutter_log = _log_gaussian_relative_peak_upper(
                        clutter_coefficient,
                        observed.coordinates,
                        clutter_covariance_lower,
                        name=(
                            "physical clutter peak for observation %d"
                            % observation_index
                        ),
                    )
                immigrant_log = -math.inf
                if signal_log != -math.inf:
                    immigrant_log = _outward_sum_upper(
                        (
                            _outward_log_fraction(
                                theta_fraction,
                                name="reference activity log",
                            ),
                            signal_log,
                        ),
                        name="immigrant background log upper bound",
                    )
                background_log_bounds.append(
                    _outward_logaddexp_upper(
                        physical_clutter_log,
                        immigrant_log,
                        name="total background pointwise upper bound",
                    )
                )

            log_polynomial = _log_cap_aware_injection_polynomial_upper(
                signal_log_bounds,
                background_log_bounds,
                source_cap=source_cap,
            )
            clean_log_upper = (
                -math.inf
                if log_polynomial == -math.inf
                else _outward_sum_upper(
                    (1.0, log_polynomial),
                    name="clean guide log upper bound",
                )
            )
            (
                guide_log_upper,
                guide_upper,
                oscillation,
            ) = self._guide_positive_range_bounds(clean_log_upper, epsilon)

            gradient_bound = 0.0
            hessian_bound = 0.0
            if (
                source_cap > 0
                and maximum_coordinate_count > 0
                and clean_log_upper != -math.inf
            ):
                log_source_cap = _outward_log_fraction(
                    Fraction(source_cap), name="source cap log"
                )
                padded_factor_logs = []
                for signal_log, background_log in zip(
                    signal_log_bounds, background_log_bounds
                ):
                    scaled_signal = (
                        -math.inf
                        if signal_log == -math.inf
                        else _outward_sum_upper(
                            (log_source_cap, signal_log),
                            name="cap-scaled anchor factor",
                        )
                    )
                    raw_factor = _outward_logaddexp_upper(
                        background_log,
                        scaled_signal,
                        name="regularity residual-observation factor",
                    )
                    padded_factor_logs.append(max(0.0, raw_factor))
                prefix = [0.0]
                for value in padded_factor_logs:
                    prefix.append(
                        _outward_sum_upper(
                            (prefix[-1], value),
                            name="regularity prefix product",
                        )
                    )
                suffix = [0.0] * (len(padded_factor_logs) + 1)
                for index in range(len(padded_factor_logs) - 1, -1, -1):
                    suffix[index] = _outward_sum_upper(
                        (padded_factor_logs[index], suffix[index + 1]),
                        name="regularity suffix product",
                    )
                leave_one_logs = [
                    _outward_sum_upper(
                        (prefix[index], suffix[index + 1]),
                        name="regularity leave-one product",
                    )
                    for index in range(len(padded_factor_logs))
                ]
                type_gradient_logs = []
                type_hessian_logs = []
                type_gradient_sum_logs = []
                for source_position, source_type in enumerate(type_ids):
                    if self.process.reference.type_dimensions[source_type] == 0:
                        type_gradient_logs.append(-math.inf)
                        type_hessian_logs.append(-math.inf)
                        type_gradient_sum_logs.append(-math.inf)
                        continue
                    gradient_terms = []
                    hessian_terms = []
                    unpadded_gradient_terms = []
                    for observation_index in range(len(outcome)):
                        log_gradient = signal_gradient_logs[observation_index][
                            source_position
                        ]
                        log_hessian = signal_hessian_logs[observation_index][
                            source_position
                        ]
                        if log_gradient != -math.inf:
                            unpadded_gradient_terms.append(log_gradient)
                            gradient_terms.append(
                                _outward_sum_upper(
                                    (
                                        log_gradient,
                                        leave_one_logs[observation_index],
                                    ),
                                    name="one-occurrence guide gradient term",
                                )
                            )
                        if log_hessian != -math.inf:
                            hessian_terms.append(
                                _outward_sum_upper(
                                    (
                                        log_hessian,
                                        leave_one_logs[observation_index],
                                    ),
                                    name="one-occurrence guide Hessian term",
                                )
                            )
                    summed_gradient = _outward_logsumexp_upper(
                        gradient_terms,
                        name="one-occurrence guide gradient sum",
                    )
                    summed_hessian = _outward_logsumexp_upper(
                        hessian_terms,
                        name="one-occurrence guide Hessian sum",
                    )
                    type_gradient_logs.append(
                        -math.inf
                        if summed_gradient == -math.inf
                        else _outward_sum_upper(
                            (1.0, summed_gradient),
                            name="clean guide gradient bound",
                        )
                    )
                    type_hessian_logs.append(
                        -math.inf
                        if summed_hessian == -math.inf
                        else _outward_sum_upper(
                            (1.0, summed_hessian),
                            name="clean guide Hessian bound",
                        )
                    )
                    type_gradient_sum_logs.append(
                        _outward_logsumexp_upper(
                            unpadded_gradient_terms,
                            name="detected-anchor gradient sum",
                        )
                    )
                maximum_clean_gradient_log = max(type_gradient_logs, default=-math.inf)
                maximum_clean_hessian_log = max(type_hessian_logs, default=-math.inf)
                maximum_anchor_gradient_sum_log = max(
                    type_gradient_sum_logs, default=-math.inf
                )
                if maximum_clean_gradient_log != -math.inf:
                    epsilon_fraction = _fraction_from_float(epsilon)
                    mixture_ratio_log = _outward_log_fraction(
                        (Fraction(1) - epsilon_fraction) / epsilon_fraction,
                        name="positive-guide derivative mixture ratio",
                    )
                    block_gradient_log = _outward_sum_upper(
                        (mixture_ratio_log, maximum_clean_gradient_log),
                        name="positive-guide block gradient bound",
                    )
                    gradient_log = _outward_sum_upper(
                        (
                            block_gradient_log,
                            _outward_float_from_fraction(
                                _fraction_from_float(log_source_cap) / 2,
                                name="square-root source-cap log",
                            ),
                        ),
                        name="full guide gradient norm bound",
                    )
                    gradient_bound = _outward_exp_upper(
                        gradient_log, name="guide gradient norm bound"
                    )

                    diagonal_terms = [
                        _outward_sum_upper(
                            (block_gradient_log, block_gradient_log),
                            name="guide log-Hessian score-square bound",
                        )
                    ]
                    if maximum_clean_hessian_log != -math.inf:
                        diagonal_terms.append(
                            _outward_sum_upper(
                                (
                                    mixture_ratio_log,
                                    maximum_clean_hessian_log,
                                ),
                                name="guide diagonal Hessian clean term",
                            )
                        )
                    diagonal_log = _outward_logsumexp_upper(
                        diagonal_terms,
                        name="guide diagonal Hessian block bound",
                    )
                    cross_log = -math.inf
                    if source_cap > 1 and maximum_anchor_gradient_sum_log != -math.inf:
                        cross_clean_log = _outward_sum_upper(
                            (
                                1.0,
                                prefix[-1],
                                maximum_anchor_gradient_sum_log,
                                maximum_anchor_gradient_sum_log,
                            ),
                            name="clean cross-occurrence Hessian bound",
                        )
                        cross_log = _outward_logaddexp_upper(
                            _outward_sum_upper(
                                (mixture_ratio_log, cross_clean_log),
                                name="positive-guide cross Hessian clean term",
                            ),
                            _outward_sum_upper(
                                (block_gradient_log, block_gradient_log),
                                name="positive-guide cross score-square term",
                            ),
                            name="guide cross Hessian block bound",
                        )
                    hessian_log = diagonal_log
                    if cross_log != -math.inf:
                        hessian_log = _outward_logaddexp_upper(
                            diagonal_log,
                            _outward_sum_upper(
                                (
                                    _outward_log_fraction(
                                        Fraction(source_cap - 1),
                                        name="cross-occurrence row count log",
                                    ),
                                    cross_log,
                                ),
                                name="cross-occurrence Hessian row bound",
                            ),
                            name="full guide Hessian operator bound",
                        )
                    hessian_bound = _outward_exp_upper(
                        hessian_log,
                        name="guide Hessian operator norm bound",
                    )

        minimum_covariance = (
            None
            if not covariance_lowers
            else _downward_positive_float_from_fraction(
                min(covariance_lowers),
                name="minimum covariance eigenvalue witness",
            )
        )
        outcome_key = self._guide_outcome_key(outcome)
        values = {
            "schema_version": ANALYTIC_GUIDE_RANGE_SCHEMA_VERSION,
            "certificate_scope": ANALYTIC_GUIDE_RANGE_CERTIFICATE_SCOPE,
            "preconditioner_parameter_key": preconditioner_key,
            "outcome": outcome,
            "outcome_key": outcome_key,
            "state_cap": source_cap,
            "maximum_coordinate_count": maximum_coordinate_count,
            "contamination_probability": epsilon,
            "guide_lower_bound": epsilon,
            "clean_log_upper_bound": clean_log_upper,
            "guide_log_upper_bound": guide_log_upper,
            "guide_upper_bound": guide_upper,
            "log_guide_oscillation_bound": oscillation,
            "log_guide_gradient_norm_bound": gradient_bound,
            "log_guide_hessian_operator_norm_bound": hessian_bound,
            "covariance_witness_count": len(covariance_lowers),
            "minimum_covariance_eigenvalue_lower_bound": minimum_covariance,
            "maximum_whitened_matrix_norm_bound": maximum_whitened_norm,
            "analytic_work": analytic_work,
        }
        certificate_sha256 = _plain_key_sha256(
            _guide_range_contract_key(values),
            domain=b"heterodiff-analytic-guide-range-certificate-v1\x00",
        )
        return AnalyticGuideRangeCertificate(
            **values,
            certificate_sha256=certificate_sha256,
            _construction_token=_GUIDE_RANGE_CERTIFICATE_TOKEN,
        )

    def validate_guide_range_certificate(
        self,
        certificate: object,
        observation: Optional[object] = None,
    ) -> AnalyticGuideRangeCertificate:
        """Recompute and require an exact matching guide range certificate."""

        if type(certificate) is not AnalyticGuideRangeCertificate:
            raise TypeError(
                "certificate must be an exact AnalyticGuideRangeCertificate"
            )
        record_names = (
            "schema_version",
            "certificate_scope",
            "preconditioner_parameter_key",
            "outcome",
            "outcome_key",
            "state_cap",
            "maximum_coordinate_count",
            "contamination_probability",
            "guide_lower_bound",
            "clean_log_upper_bound",
            "guide_log_upper_bound",
            "guide_upper_bound",
            "log_guide_oscillation_bound",
            "log_guide_gradient_norm_bound",
            "log_guide_hessian_operator_norm_bound",
            "covariance_witness_count",
            "minimum_covariance_eigenvalue_lower_bound",
            "maximum_whitened_matrix_norm_bound",
            "analytic_work",
            "certificate_sha256",
        )
        AnalyticGuideRangeCertificate(
            **{name: getattr(certificate, name) for name in record_names},
            _construction_token=_GUIDE_RANGE_CERTIFICATE_TOKEN,
        )
        self._require_live_guide_certificate_binding()
        requested_outcome = certificate.outcome
        if observation is not None:
            requested_outcome = self.observation_reference.collapse(observation)
            if self._guide_outcome_key(requested_outcome) != certificate.outcome_key:
                raise ValueError("certificate is bound to a different observation")
        expected = self.certify_guide_range(requested_outcome)
        names = (
            "schema_version",
            "certificate_scope",
            "preconditioner_parameter_key",
            "outcome_key",
            "state_cap",
            "maximum_coordinate_count",
            "contamination_probability",
            "guide_lower_bound",
            "clean_log_upper_bound",
            "guide_log_upper_bound",
            "guide_upper_bound",
            "log_guide_oscillation_bound",
            "log_guide_gradient_norm_bound",
            "log_guide_hessian_operator_norm_bound",
            "covariance_witness_count",
            "minimum_covariance_eigenvalue_lower_bound",
            "maximum_whitened_matrix_norm_bound",
            "analytic_work",
            "certificate_sha256",
        )
        for name in names:
            supplied = getattr(certificate, name)
            recomputed = getattr(expected, name)
            if type(supplied) is float and type(recomputed) is float:
                matches = supplied.hex() == recomputed.hex()
            else:
                matches = supplied == recomputed
            if not matches:
                raise ValueError(
                    "guide range certificate field %s does not match "
                    "recomputation" % name
                )
        if certificate.outcome is OVERFLOW_OBSERVATION:
            if expected.outcome is not OVERFLOW_OBSERVATION:
                raise ValueError("overflow certificate outcome is inconsistent")
        elif self._guide_outcome_key(certificate.outcome) != expected.outcome_key:
            raise ValueError("retained certificate outcome is inconsistent")
        return certificate

    def require_matching_guide_range_certificate(
        self,
        certificate: object,
        observation: Optional[object] = None,
    ) -> AnalyticGuideRangeCertificate:
        """Alias emphasizing model-level certificate consistency only."""

        return self.validate_guide_range_certificate(
            certificate, observation=observation
        )

    def terminal_row(self, sources: object) -> BoundAssociationObservationRow:
        """Return the exact endpoint observation row on one capped state."""

        canonical = self._canonical_restricted(sources)
        detection = np.asarray(
            [
                self._detection[self._type_positions[source.event_type]]
                for source in canonical
            ],
            dtype=np.float64,
        )
        return BoundAssociationObservationRow(
            self.observation_reference,
            self.terminal_channel,
            self.terminal_clutter,
            canonical,
            detection,
            contamination_probability=self.contamination_probability,
        )

    def _reverse_time(self, value: object) -> float:
        reverse_time = _validated_real(value, name="reverse_time")
        horizon = self.process.schedule.horizon
        if reverse_time < 0.0 or reverse_time > horizon:
            raise ValueError("reverse_time must lie in [0, horizon]")
        return reverse_time

    def _context(self, reverse_time: object) -> _PropagationContext:
        current = self._reverse_time(reverse_time)
        forward_end = self.process.schedule.horizon - current
        try:
            jump_clock = self.process.schedule.jump_integral(0.0, forward_end)
            continuous_clock = self.process.schedule.continuous_integral(
                0.0, forward_end
            )
        except AssociationPreconditionerNumericalError:
            raise
        except ArithmeticError as error:
            raise AssociationPreconditionerNumericalError(
                "schedule integral cannot be certified numerically"
            ) from error
        if jump_clock < 0.0 or continuous_clock < 0.0:
            raise ArithmeticError("integrated schedules must be nonnegative")
        ou_decay = math.exp(-0.5 * continuous_clock)
        ou_variance = -math.expm1(-continuous_clock)
        if not math.isfinite(ou_decay) or not math.isfinite(ou_variance):
            raise AssociationPreconditionerNumericalError(
                "OU propagation is not finite"
            )
        if continuous_clock > 0.0 and (
            ou_decay == 0.0
            or ou_decay == 1.0
            or ou_variance == 0.0
            or ou_variance == 1.0
        ):
            raise AssociationPreconditionerNumericalError(
                "positive OU evolution is below float64 resolution"
            )
        delta = self.process.rates.per_particle_death_rate
        log_survival = -delta * jump_clock
        if log_survival < _LOG_MIN_NORMAL:
            raise AssociationPreconditionerNumericalError(
                "death survival is positive but not a normal float64 value"
            )
        death_survival = math.exp(log_survival)
        if death_survival == 0.0:
            raise AssociationPreconditionerNumericalError(
                "positive death survival underflows float64"
            )
        if log_survival < 0.0 and death_survival == 1.0:
            raise AssociationPreconditionerNumericalError(
                "positive death probability is below float64 resolution"
            )

        type_count = len(self.process.reference.type_ids)
        augmented = np.zeros((2 * type_count, 2 * type_count), dtype=np.float64)
        augmented[:type_count, :type_count] = -np.diag(self._outgoing)
        augmented[:type_count, type_count:] = self._replacement_matrix
        augmented[type_count:, type_count:] = self._generator
        try:
            with np.errstate(over="raise", invalid="raise"):
                scaled_generator = jump_clock * augmented
            if not np.all(np.isfinite(scaled_generator)):
                raise FloatingPointError
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                propagated = np.asarray(expm(scaled_generator), dtype=np.float64)
        except (
            FloatingPointError,
            RuntimeWarning,
            OverflowError,
            ValueError,
            np.linalg.LinAlgError,
        ) as error:
            raise AssociationPreconditionerNumericalError(
                "augmented type exponential cannot be certified"
            ) from error
        if not np.all(np.isfinite(propagated)):
            raise AssociationPreconditionerNumericalError(
                "augmented type exponential is non-finite"
            )
        no_replacement = np.asarray(
            propagated[:type_count, :type_count], dtype=np.float64
        ).copy()
        refreshed = np.asarray(
            propagated[:type_count, type_count:], dtype=np.float64
        ).copy()
        minimum = min(float(np.min(no_replacement)), float(np.min(refreshed)))
        if minimum < -PRECONDITIONER_NUMERICAL_ATOL:
            raise AssociationPreconditionerNumericalError(
                "augmented type exponential contains negative probability mass"
            )
        maximum_correction = max(0.0, -minimum)
        no_replacement[no_replacement < 0.0] = 0.0
        refreshed[refreshed < 0.0] = 0.0
        if jump_clock > 0.0:
            lost_replacement = self._replacement_reachability & (refreshed == 0.0)
            if np.any(lost_replacement):
                raise AssociationPreconditionerNumericalError(
                    "positive replacement-path mass underflows float64"
                )
        transition = no_replacement + refreshed
        row_sums = transition.sum(axis=1)
        row_drift = float(np.max(np.abs(row_sums - 1.0)))
        if row_drift > PRECONDITIONER_NUMERICAL_ATOL:
            raise AssociationPreconditionerNumericalError(
                "augmented type transition rows do not sum to one"
            )
        maximum_correction = max(maximum_correction, row_drift)
        for source in range(type_count):
            if (
                self._outgoing[source] > 0.0
                and jump_clock > 0.0
                and no_replacement[source, source] == 0.0
            ):
                raise AssociationPreconditionerNumericalError(
                    "positive no-replacement mass underflows float64"
                )

        immigrant_survivor_mean = _checked_product(
            self.process.reference.activity,
            -math.expm1(log_survival),
            name="immigrant survivor mean",
        )
        if jump_clock > 0.0 and immigrant_survivor_mean == 0.0:
            raise AssociationPreconditionerNumericalError(
                "positive immigrant survivor mean underflows float64"
            )
        immigrant_type_means = np.asarray(
            [
                _checked_product(
                    immigrant_survivor_mean,
                    float(weight),
                    name="immigrant terminal type mean",
                )
                for weight in self._weights
            ],
            dtype=np.float64,
        )
        if immigrant_survivor_mean > 0.0 and np.any(immigrant_type_means == 0.0):
            raise AssociationPreconditionerNumericalError(
                "positive immigrant type mean underflows float64"
            )
        immigrant_anchor_mean = _checked_product(
            immigrant_survivor_mean,
            self.reference_detected_probability,
            name="immigrant anchor mean",
        )
        if (
            immigrant_survivor_mean > 0.0
            and self.reference_detected_probability > 0.0
            and immigrant_anchor_mean == 0.0
        ):
            raise AssociationPreconditionerNumericalError(
                "positive immigrant anchor mean underflows float64"
            )
        total_background = _strict_nonnegative_fsum(
            (self.terminal_clutter.total_intensity, immigrant_anchor_mean),
            name="total propagated background intensity",
        )
        if total_background > MAX_ASSOCIATION_CLUTTER_MEAN:
            raise AssociationObservationResourceError(
                "propagated clutter total exceeds the association limit"
            )

        propagation = AssociationPropagation(
            reverse_time=current,
            jump_clock=jump_clock,
            continuous_clock=continuous_clock,
            ou_decay=ou_decay,
            ou_variance=ou_variance,
            death_survival=death_survival,
            type_transition=transition,
            no_replacement_transition=no_replacement,
            replacement_refresh_transition=refreshed,
            immigrant_survivor_mean=immigrant_survivor_mean,
            immigrant_terminal_type_means=immigrant_type_means,
            immigrant_anchor_mean=immigrant_anchor_mean,
            total_background_intensity=total_background,
            maximum_roundoff_correction=maximum_correction,
            preconditioner_parameter_key=self.parameter_key(),
            _construction_token=_PROPAGATION_TOKEN,
        )

        no_replacement_channels = {}
        if not propagation.is_terminal_identity:
            for source_type in self.process.reference.type_ids:
                source_position = self._type_positions[source_type]
                for observation_type in self.observation_reference.type_ids:
                    observation_position = self.terminal_channel._observation_positions[
                        observation_type
                    ]
                    if (
                        self.observation_reference.type_dimensions[observation_type]
                        == 0
                        or float(
                            self.terminal_channel.stratum_probability[
                                source_position, observation_position
                            ]
                        )
                        == 0.0
                    ):
                        continue
                    terminal_fiber = self.terminal_channel.fiber_channels[
                        (source_type, observation_type)
                    ]
                    try:
                        with np.errstate(over="raise", invalid="raise"):
                            gram = terminal_fiber.matrix @ terminal_fiber.matrix.T
                            scaled_gram = propagation.ou_variance * gram
                            covariance = terminal_fiber.covariance + scaled_gram
                            effective_matrix = (
                                propagation.ou_decay * terminal_fiber.matrix
                            )
                    except FloatingPointError as error:
                        raise AssociationPreconditionerNumericalError(
                            "propagated channel covariance is not representable"
                        ) from error
                    if np.any(
                        (terminal_fiber.matrix != 0.0)
                        & (propagation.ou_decay != 0.0)
                        & (effective_matrix == 0.0)
                    ):
                        raise AssociationPreconditionerNumericalError(
                            "positive-magnitude OU channel matrix term "
                            "underflows float64"
                        )
                    if np.any(
                        (effective_matrix != 0.0)
                        & (np.abs(effective_matrix) < float(np.finfo(np.float64).tiny))
                    ):
                        raise AssociationPreconditionerNumericalError(
                            "OU channel matrix contains a subnormal coefficient"
                        )
                    nonzero_rows = np.any(terminal_fiber.matrix != 0.0, axis=1)
                    if np.any(nonzero_rows & (np.diag(gram) == 0.0)):
                        raise AssociationPreconditionerNumericalError(
                            "positive channel Gram variance underflows float64"
                        )
                    if np.any(
                        (gram != 0.0)
                        & (propagation.ou_variance != 0.0)
                        & (scaled_gram == 0.0)
                    ):
                        raise AssociationPreconditionerNumericalError(
                            "positive-magnitude OU covariance term underflows float64"
                        )
                    if np.any(
                        (scaled_gram != 0.0)
                        & (np.abs(scaled_gram) < float(np.finfo(np.float64).tiny))
                    ):
                        raise AssociationPreconditionerNumericalError(
                            "OU covariance contains a subnormal contribution"
                        )
                    if np.any(
                        (scaled_gram != 0.0) & (covariance == terminal_fiber.covariance)
                    ):
                        raise AssociationPreconditionerNumericalError(
                            "OU covariance contribution is below addition resolution"
                        )
                    if np.any(
                        (terminal_fiber.covariance != 0.0) & (covariance == scaled_gram)
                    ):
                        raise AssociationPreconditionerNumericalError(
                            "terminal covariance is below addition resolution"
                        )
                    covariance_diagonal = np.diag(covariance)
                    if np.any(
                        (covariance_diagonal > 0.0)
                        & (covariance_diagonal < float(np.finfo(np.float64).tiny))
                    ):
                        raise AssociationPreconditionerNumericalError(
                            "propagated channel variance is subnormal"
                        )
                    no_replacement_channels[
                        (source_type, observation_type)
                    ] = _propagated_affine_gaussian_fiber(
                        effective_matrix,
                        terminal_fiber.bias,
                        covariance,
                        name="propagated affine Gaussian fiber",
                    )
        return _PropagationContext(
            propagation,
            MappingProxyType(no_replacement_channels),
        )

    def propagation(self, reverse_time: object) -> AssociationPropagation:
        return self._context(reverse_time).propagation

    def _canonical_unbounded(self, sources: object) -> TransformedConfiguration:
        events = _bounded_tuple(
            sources,
            name="unbounded sources",
            maximum_items=MAX_ASSOCIATION_OCCURRENCES,
        )
        coordinate_count = 0
        checked = []
        for event in events:
            checked_event = self.terminal_channel._validate_source(event)
            coordinate_count += len(checked_event.coordinates)
            if coordinate_count > MAX_REFERENCE_DENSITY_COORDINATES:
                raise AssociationObservationResourceError(
                    "unbounded sources exceed the coordinate-work limit"
                )
            checked.append(checked_event)
        return tuple(sorted(checked, key=TransformedEvent.model_key))

    def _canonical_restricted(self, state: object) -> TransformedConfiguration:
        return self.process.reference.canonicalize(state)  # type: ignore[arg-type]

    def _source_detection(
        self, context: _PropagationContext, source: TransformedEvent
    ) -> float:
        source_position = self._type_positions[source.event_type]
        conditional_detection = _strict_nonnegative_fsum(
            (
                _checked_product(
                    float(
                        context.propagation.type_transition[source_position, terminal]
                    ),
                    float(self._detection[terminal]),
                    name="terminal-type detection component",
                )
                for terminal in range(len(self._detection))
            ),
            name="conditional propagated detection",
        )
        probability = _checked_product(
            context.propagation.death_survival,
            conditional_detection,
            name="effective detection probability",
        )
        if probability < 0.0 or probability > 1.0:
            raise AssociationPreconditionerNumericalError(
                "effective detection probability lies outside [0, 1]"
            )
        if probability == 0.0:
            reachable_positive = any(
                context.propagation.type_transition[source_position, terminal] > 0.0
                and self._detection[terminal] > 0.0
                for terminal in range(len(self._detection))
            )
            if reachable_positive:
                raise AssociationPreconditionerNumericalError(
                    "positive effective detection underflows float64"
                )
        if probability == 1.0:
            positive_miss = context.propagation.jump_clock > 0.0 or any(
                context.propagation.type_transition[source_position, terminal] > 0.0
                and self._detection[terminal] < 1.0
                for terminal in range(len(self._detection))
            )
            if positive_miss:
                raise AssociationPreconditionerNumericalError(
                    "positive effective miss probability is below float64 resolution"
                )
        return probability

    def one_occurrence_propagation(
        self, reverse_time: object, source: object
    ) -> OneOccurrenceTerminalKernel:
        checked_source = self.terminal_channel._validate_source(source)
        context = self._context(reverse_time)
        position = self._type_positions[checked_source.event_type]
        no_replacement = (
            context.propagation.death_survival
            * context.propagation.no_replacement_transition[position]
        )
        refreshed = (
            context.propagation.death_survival
            * context.propagation.replacement_refresh_transition[position]
        )
        if np.any(
            (context.propagation.no_replacement_transition[position] > 0.0)
            & (no_replacement == 0.0)
        ) or np.any(
            (context.propagation.replacement_refresh_transition[position] > 0.0)
            & (refreshed == 0.0)
        ):
            raise AssociationPreconditionerNumericalError(
                "positive surviving type component underflows float64"
            )
        surviving = no_replacement + refreshed
        return OneOccurrenceTerminalKernel(
            checked_source,
            context.propagation.parameter_key(),
            surviving,
            no_replacement,
            refreshed,
            self._source_detection(context, checked_source),
            _construction_token=_ONE_OCCURRENCE_TOKEN,
        )

    def sample_one_occurrence_terminal(
        self,
        reverse_time: object,
        source: object,
        *,
        rng: np.random.Generator,
    ) -> Optional[TransformedEvent]:
        if not isinstance(rng, np.random.Generator):
            raise TypeError("rng must be a numpy.random.Generator")
        checked_source = self.terminal_channel._validate_source(source)
        context = self._context(reverse_time)
        propagation = context.propagation
        log_survival = (
            -self.process.rates.per_particle_death_rate * propagation.jump_clock
        )
        death_probability = -math.expm1(log_survival)
        survival_categories = np.asarray(
            (death_probability, propagation.death_survival), dtype=np.float64
        )
        positive_survival_categories = survival_categories[survival_categories > 0.0]
        survival_sampling_floor = max(
            2.0**-40,
            64.0 * float(np.finfo(np.float64).eps),
        )
        if (
            positive_survival_categories.size
            and float(np.min(positive_survival_categories)) < survival_sampling_floor
        ):
            raise AssociationPreconditionerNumericalError(
                "death/survival law is below finite-RNG resolution"
            )
        if float(rng.random()) < death_probability:
            return None
        source_position = self._type_positions[checked_source.event_type]
        masses = np.concatenate(
            (
                propagation.no_replacement_transition[source_position],
                propagation.replacement_refresh_transition[source_position],
            )
        )
        total_mass = math.fsum(float(value) for value in masses)
        if total_mass <= 0.0 or not math.isfinite(total_mass):
            raise AssociationPreconditionerNumericalError("alive mixture has zero mass")
        probabilities = masses / total_mass
        positive = probabilities[probabilities > 0.0]
        sampling_floor = max(
            2.0**-40,
            32.0 * len(probabilities) * float(np.finfo(np.float64).eps),
        )
        if positive.size and float(np.min(positive)) < sampling_floor:
            raise AssociationPreconditionerNumericalError(
                "alive mixture has a component below finite-RNG resolution"
            )
        cumulative = np.cumsum(probabilities, dtype=np.float64)
        cumulative[-1] = 1.0
        increments = np.diff(np.concatenate((np.zeros(1), cumulative)))
        if np.any(increments[probabilities > 0.0] <= 0.0):
            raise AssociationPreconditionerNumericalError(
                "alive mixture CDF loses a positive component"
            )
        relative_error = np.zeros_like(probabilities)
        relative_error[probabilities > 0.0] = (
            np.abs(increments[probabilities > 0.0] - probabilities[probabilities > 0.0])
            / probabilities[probabilities > 0.0]
        )
        if np.any(relative_error > 0.125):
            raise AssociationPreconditionerNumericalError(
                "alive mixture CDF is not resolution-safe"
            )
        component = int(np.searchsorted(cumulative, rng.random(), side="right"))
        type_count = len(self.process.reference.type_ids)
        if component < type_count:
            destination_position = component
            destination_type = self.process.reference.type_ids[destination_position]
            dimension = self.process.reference.type_dimensions[destination_type]
            if destination_type != checked_source.event_type:
                raise AssociationPreconditionerNumericalError(
                    "no-replacement component changed type"
                )
            if dimension == 0:
                coordinates: Tuple[float, ...] = ()
            else:
                noise = np.asarray(rng.standard_normal(dimension), dtype=np.float64)
                coordinates = tuple(
                    float(value)
                    for value in (
                        propagation.ou_decay * np.asarray(checked_source.coordinates)
                        + math.sqrt(propagation.ou_variance) * noise
                    )
                )
        else:
            destination_position = component - type_count
            destination_type = self.process.reference.type_ids[destination_position]
            dimension = self.process.reference.type_dimensions[destination_type]
            coordinates = tuple(
                float(value) for value in rng.standard_normal(dimension)
            )
        return TransformedEvent(destination_type, coordinates)

    def _reference_anchor_log_density(self, observation: TransformedEvent) -> float:
        checked = self.terminal_channel._validate_observation(observation)
        observation_position = self.terminal_channel._observation_positions[
            checked.event_type
        ]
        observation_weight = self.observation_reference.type_weights[checked.event_type]
        terms = []
        for source_position, source_type in enumerate(self.process.reference.type_ids):
            detection = float(self._detection[source_position])
            stratum = float(
                self.terminal_channel.stratum_probability[
                    source_position, observation_position
                ]
            )
            if detection == 0.0 or stratum == 0.0:
                continue
            term = (
                math.log(float(self._weights[source_position]))
                + math.log(detection)
                + math.log(stratum)
                - math.log(observation_weight)
            )
            if len(checked.coordinates) > 0:
                term += self._reference_fiber_channels[
                    (source_type, checked.event_type)
                ].log_density_ratio((), checked.coordinates)
            terms.append(term)
        return _logsumexp(terms)

    def _source_anchor_log_and_no_replacement_score(
        self,
        context: _PropagationContext,
        observation: TransformedEvent,
        source: TransformedEvent,
    ) -> Tuple[float, float, np.ndarray]:
        checked_observation = self.terminal_channel._validate_observation(observation)
        checked_source = self.terminal_channel._validate_source(source)
        source_position = self._type_positions[checked_source.event_type]
        observation_position = self.terminal_channel._observation_positions[
            checked_observation.event_type
        ]
        observation_weight = self.observation_reference.type_weights[
            checked_observation.event_type
        ]
        propagation = context.propagation
        if propagation.is_terminal_identity:
            terminal_log = self.terminal_channel.log_emission_density(
                checked_observation, checked_source
            )
            if terminal_log == -math.inf or self._detection[source_position] == 0.0:
                return (
                    -math.inf,
                    -math.inf,
                    np.zeros(len(checked_source.coordinates), dtype=np.float64),
                )
            anchor_log = (
                math.log(float(self._detection[source_position])) + terminal_log
            )
            gradient = self.terminal_channel.log_emission_gradient_source(
                checked_observation, checked_source
            )
            return anchor_log, 0.0, gradient

        terms = []
        no_replacement_log = -math.inf
        no_replacement_gradient = np.zeros(
            len(checked_source.coordinates), dtype=np.float64
        )
        no_mass = float(
            propagation.death_survival
            * propagation.no_replacement_transition[source_position, source_position]
        )
        terminal_detection = float(self._detection[source_position])
        terminal_stratum = float(
            self.terminal_channel.stratum_probability[
                source_position, observation_position
            ]
        )
        if (
            propagation.no_replacement_transition[source_position, source_position]
            > 0.0
            and propagation.death_survival > 0.0
            and no_mass == 0.0
        ):
            raise AssociationPreconditionerNumericalError(
                "positive no-replacement anchor component underflows float64"
            )
        if no_mass > 0.0 and terminal_detection > 0.0 and terminal_stratum > 0.0:
            no_replacement_log = (
                math.log(no_mass)
                + math.log(terminal_detection)
                + math.log(terminal_stratum)
                - math.log(observation_weight)
            )
            if len(checked_observation.coordinates) > 0:
                fiber = context.no_replacement_channels[
                    (checked_source.event_type, checked_observation.event_type)
                ]
                no_replacement_log += fiber.log_density_ratio(
                    checked_source.coordinates, checked_observation.coordinates
                )
                no_replacement_gradient = fiber.log_density_gradient_source(
                    checked_source.coordinates, checked_observation.coordinates
                )
            terms.append(no_replacement_log)

        for terminal_position, terminal_type in enumerate(
            self.process.reference.type_ids
        ):
            refreshed_mass = float(
                propagation.death_survival
                * propagation.replacement_refresh_transition[
                    source_position, terminal_position
                ]
            )
            detection = float(self._detection[terminal_position])
            stratum = float(
                self.terminal_channel.stratum_probability[
                    terminal_position, observation_position
                ]
            )
            if (
                propagation.replacement_refresh_transition[
                    source_position, terminal_position
                ]
                > 0.0
                and propagation.death_survival > 0.0
                and refreshed_mass == 0.0
            ):
                raise AssociationPreconditionerNumericalError(
                    "positive refreshed anchor component underflows float64"
                )
            if refreshed_mass == 0.0 or detection == 0.0 or stratum == 0.0:
                continue
            term = (
                math.log(refreshed_mass)
                + math.log(detection)
                + math.log(stratum)
                - math.log(observation_weight)
            )
            if len(checked_observation.coordinates) > 0:
                term += self._reference_fiber_channels[
                    (terminal_type, checked_observation.event_type)
                ].log_density_ratio((), checked_observation.coordinates)
            terms.append(term)
        anchor_log = _logsumexp(terms)
        if anchor_log == -math.inf or no_replacement_log == -math.inf:
            return anchor_log, -math.inf, no_replacement_gradient
        log_responsibility = no_replacement_log - anchor_log
        if log_responsibility > PRECONDITIONER_NUMERICAL_ATOL:
            raise AssociationPreconditionerNumericalError(
                "no-replacement mixture responsibility exceeds one"
            )
        return anchor_log, min(0.0, log_responsibility), no_replacement_gradient

    def effective_anchor_log_density(
        self,
        reverse_time: object,
        observation: object,
        source: object,
    ) -> float:
        context = self._context(reverse_time)
        return self._source_anchor_log_and_no_replacement_score(
            context,
            observation,  # type: ignore[arg-type]
            source,  # type: ignore[arg-type]
        )[0]

    def effective_background_log_intensity(
        self, reverse_time: object, observation: object
    ) -> float:
        context = self._context(reverse_time)
        return self._background_log_intensity(context, observation)

    def _background_log_intensity(
        self, context: _PropagationContext, observation: object
    ) -> float:
        checked = self.terminal_channel._validate_observation(observation)
        physical = self.terminal_clutter.log_intensity(checked)
        immigrant = -math.inf
        if context.propagation.immigrant_survivor_mean > 0.0:
            reference_anchor = self._reference_anchor_log_density(checked)
            if reference_anchor != -math.inf:
                immigrant = (
                    math.log(context.propagation.immigrant_survivor_mean)
                    + reference_anchor
                )
        return _logaddexp(physical, immigrant)

    @staticmethod
    def _retained_association_work(latent_count: int, observation_count: int) -> int:
        if latent_count == 0 or observation_count == 0:
            return latent_count + observation_count + 1
        return (
            latent_count
            * observation_count
            * (1 << min(latent_count, observation_count))
        )

    @staticmethod
    def _association_marginal_work(latent_count: int, observation_count: int) -> int:
        if latent_count == 0 or observation_count == 0:
            return 0
        reduced_states = 1 << min(latent_count - 1, observation_count - 1)
        edge_work = (
            latent_count
            * observation_count
            * max(1, latent_count - 1)
            * max(1, observation_count - 1)
            * reduced_states
        )
        base_states = 1 << min(latent_count, observation_count)
        forced_unmatched_work = (
            (latent_count + observation_count)
            * latent_count
            * observation_count
            * base_states
        )
        return edge_work + forced_unmatched_work

    def _detection_work(self, context: _PropagationContext, latent_count: int) -> int:
        if context.propagation.is_terminal_identity:
            return latent_count
        type_count = len(self.process.reference.type_ids)
        return latent_count * type_count**2

    def _gaussian_pair_work_unit(self) -> int:
        observation_solve_work = max(
            (
                dimension**3
                for dimension in self.observation_reference.type_dimensions.values()
            ),
            default=1,
        )
        return max(
            1,
            len(self.process.reference.type_ids),
            self.gaussian_component_count,
            self.covariance_work,
            observation_solve_work,
        )

    def preflight_capped_point_evaluation_resources(self, observation: object) -> int:
        """Preflight one fixed outcome over every capped state and reverse time.

        The returned exact integer is a conservative upper bound on the work
        charged by one point evaluation.  It uses the process cardinality cap,
        the nonterminal type-propagation cost, and the full Gaussian pair pass.
        For the collapsed overflow atom it also charges every possible
        Poisson-tail fallback to its frozen iteration limit.  The background
        check uses the time-uniform bound obtained by allowing every stationary
        immigrant to survive and be detected.
        """

        outcome = self.observation_reference.collapse(observation)
        latent_count = self.process.reference.total_cap
        type_count = len(self.process.reference.type_ids)
        maximum_dimension = max(
            self.process.reference.type_dimensions.values(), default=0
        )
        if latent_count * maximum_dimension > MAX_REFERENCE_DENSITY_COORDINATES:
            raise AssociationObservationResourceError(
                "whole-capped-domain coordinate count exceeds the process budget"
            )
        detection_work = latent_count * type_count**2

        activity = _fraction_from_float(self.process.reference.activity)
        detected = _fraction_from_float(self.reference_detected_probability)
        physical_background = _fraction_from_float(
            self.terminal_clutter.total_intensity
        )
        background_upper = _outward_float_from_fraction(
            physical_background + activity * detected,
            name="whole-capped-domain propagated background upper bound",
        )
        if background_upper > MAX_ASSOCIATION_CLUTTER_MEAN:
            raise AssociationObservationResourceError(
                "whole-capped-domain propagated background exceeds the "
                "association limit"
            )

        if outcome is OVERFLOW_OBSERVATION:
            overflow_work = latent_count * (self.observation_reference.retained_cap + 1)
            if overflow_work > MAX_ASSOCIATION_DP_WORK:
                raise AssociationObservationResourceError(
                    "overflow recursion exceeds the work limit of %d"
                    % MAX_ASSOCIATION_DP_WORK
                )
            poisson_tail_work = (
                0
                if background_upper == 0.0
                else (self.observation_reference.retained_cap + 1)
                * MAX_POISSON_TAIL_TERMS
            )
            aggregate_work = detection_work + overflow_work + poisson_tail_work
        else:
            observation_count = len(outcome)
            if latent_count * observation_count > MAX_ASSOCIATION_MATRIX_ENTRIES:
                raise AssociationObservationResourceError(
                    "propagated pair matrix exceeds the entry limit"
                )
            _association_dp_resources(latent_count, observation_count)
            aggregate_work = detection_work + self._retained_association_work(
                latent_count, observation_count
            )
            aggregate_work += (
                (latent_count + 1) * observation_count * self._gaussian_pair_work_unit()
            )
        if aggregate_work > MAX_PRECONDITIONER_EVALUATION_WORK:
            raise AssociationObservationResourceError(
                "whole-capped-domain point evaluation exceeds the aggregate "
                "work limit of %d" % MAX_PRECONDITIONER_EVALUATION_WORK
            )
        return aggregate_work

    def _preflight_retained_evaluation_resources(
        self,
        context: _PropagationContext,
        latent_count: int,
        observation_count: int,
        *,
        pair_passes: int,
        require_marginals: bool,
    ) -> None:
        if latent_count * observation_count > MAX_ASSOCIATION_MATRIX_ENTRIES:
            raise AssociationObservationResourceError(
                "propagated pair matrix exceeds the entry limit"
            )
        _association_dp_resources(latent_count, observation_count)
        if require_marginals:
            _association_marginal_resources(latent_count, observation_count)
        aggregate_work = self._detection_work(context, latent_count)
        aggregate_work += self._retained_association_work(
            latent_count, observation_count
        )
        if require_marginals:
            aggregate_work += self._association_marginal_work(
                latent_count, observation_count
            )
        if pair_passes:
            aggregate_work += (
                pair_passes
                * (latent_count + 1)
                * observation_count
                * self._gaussian_pair_work_unit()
            )
        if aggregate_work > MAX_PRECONDITIONER_EVALUATION_WORK:
            raise AssociationObservationResourceError(
                "preconditioner evaluation exceeds the aggregate work limit of %d"
                % MAX_PRECONDITIONER_EVALUATION_WORK
            )

    def _preflight_overflow_evaluation_resources(
        self, context: _PropagationContext, latent_count: int
    ) -> None:
        overflow_work = latent_count * (self.observation_reference.retained_cap + 1)
        if overflow_work > MAX_ASSOCIATION_DP_WORK:
            raise AssociationObservationResourceError(
                "overflow recursion exceeds the work limit of %d"
                % MAX_ASSOCIATION_DP_WORK
            )
        aggregate_work = self._detection_work(context, latent_count)
        aggregate_work += overflow_work
        if aggregate_work > MAX_PRECONDITIONER_EVALUATION_WORK:
            raise AssociationObservationResourceError(
                "preconditioner evaluation exceeds the aggregate work limit of %d"
                % MAX_PRECONDITIONER_EVALUATION_WORK
            )

    def _source_detection_vector(
        self,
        context: _PropagationContext,
        sources: TransformedConfiguration,
    ) -> np.ndarray:
        if context.propagation.is_terminal_identity:
            return np.asarray(
                [
                    self._detection[self._type_positions[source.event_type]]
                    for source in sources
                ],
                dtype=np.float64,
            )
        return np.asarray(
            [self._source_detection(context, source) for source in sources],
            dtype=np.float64,
        )

    def _retained_factors(
        self,
        context: _PropagationContext,
        sources: TransformedConfiguration,
        observations: TransformedConfiguration,
        *,
        pair_passes: int = 1,
        require_marginals: bool = False,
    ) -> RetainedAssociationFactors:
        self._preflight_retained_evaluation_resources(
            context,
            len(sources),
            len(observations),
            pair_passes=0,
            require_marginals=require_marginals,
        )
        detection = self._source_detection_vector(context, sources)
        if _association_cardinality_is_structural_zero(
            detection,
            context.propagation.total_background_intensity,
            len(observations),
        ):
            return RetainedAssociationFactors(
                detection,
                np.full(
                    (len(observations), len(sources)),
                    -math.inf,
                    dtype=np.float64,
                ),
                np.full(len(observations), -math.inf, dtype=np.float64),
                context.propagation.total_background_intensity,
            )
        self._preflight_retained_evaluation_resources(
            context,
            len(sources),
            len(observations),
            pair_passes=pair_passes,
            require_marginals=require_marginals,
        )
        pair_logs = self._pair_log_matrix(context, sources, observations, detection)
        clutter_logs = np.asarray(
            [
                self._background_log_intensity(context, observation)
                for observation in observations
            ],
            dtype=np.float64,
        )
        return RetainedAssociationFactors(
            detection,
            pair_logs,
            clutter_logs,
            context.propagation.total_background_intensity,
        )

    def _pair_log_matrix(
        self,
        context: _PropagationContext,
        sources: TransformedConfiguration,
        observations: TransformedConfiguration,
        detection: np.ndarray,
    ) -> np.ndarray:
        pair_logs = np.full(
            (len(observations), len(sources)), -math.inf, dtype=np.float64
        )
        for observation_index, observation in enumerate(observations):
            for source_index, source in enumerate(sources):
                if detection[source_index] == 0.0:
                    continue
                anchor_log = self._source_anchor_log_and_no_replacement_score(
                    context, observation, source
                )[0]
                if anchor_log != -math.inf:
                    pair_logs[observation_index, source_index] = anchor_log - math.log(
                        float(detection[source_index])
                    )
        return pair_logs

    def _evaluate_canonical(
        self,
        context: _PropagationContext,
        sources: TransformedConfiguration,
        observation: object,
        *,
        restricted: bool,
    ) -> BoundPreconditionerEvaluation:
        outcome = self.observation_reference.collapse(observation)
        if context.propagation.is_terminal_identity:
            if outcome is OVERFLOW_OBSERVATION:
                self._preflight_overflow_evaluation_resources(context, len(sources))
            else:
                self._preflight_retained_evaluation_resources(
                    context,
                    len(sources),
                    len(outcome),
                    pair_passes=0,
                    require_marginals=False,
                )
            terminal_detection = np.asarray(
                [
                    self._detection[self._type_positions[source.event_type]]
                    for source in sources
                ],
                dtype=np.float64,
            )
            if (
                outcome is not OVERFLOW_OBSERVATION
                and not _association_cardinality_is_structural_zero(
                    terminal_detection,
                    context.propagation.total_background_intensity,
                    len(outcome),
                )
            ):
                self._preflight_retained_evaluation_resources(
                    context,
                    len(sources),
                    len(outcome),
                    pair_passes=1,
                    require_marginals=False,
                )
            terminal_row = BoundAssociationObservationRow(
                self.observation_reference,
                self.terminal_channel,
                self.terminal_clutter,
                sources,
                terminal_detection,
                contamination_probability=self.contamination_probability,
            )
            bound_terminal = terminal_row.evaluate(outcome)
            return BoundPreconditionerEvaluation(
                context.propagation.reverse_time,
                sources,
                bound_terminal.outcome,
                restricted,
                self.parameter_key(),
                bound_terminal.evaluation,
                _construction_token=_EVALUATION_TOKEN,
            )
        if outcome is OVERFLOW_OBSERVATION:
            self._preflight_overflow_evaluation_resources(context, len(sources))
            detection = self._source_detection_vector(context, sources)
            evaluation = evaluate_overflow_association(
                self.observation_reference,
                detection,
                context.propagation.total_background_intensity,
                contamination_probability=self.contamination_probability,
            )
        else:
            evaluation = evaluate_retained_association(
                self._retained_factors(context, sources, outcome),
                contamination_probability=self.contamination_probability,
            )
        return BoundPreconditionerEvaluation(
            context.propagation.reverse_time,
            sources,
            outcome,
            restricted,
            self.parameter_key(),
            evaluation,
            _construction_token=_EVALUATION_TOKEN,
        )

    def evaluate_unbounded(
        self, reverse_time: object, sources: object, observation: object
    ) -> BoundPreconditionerEvaluation:
        context = self._context(reverse_time)
        canonical = self._canonical_unbounded(sources)
        return self._evaluate_canonical(
            context, canonical, observation, restricted=False
        )

    def evaluate(
        self, reverse_time: object, state: object, observation: object
    ) -> BoundPreconditionerEvaluation:
        context = self._context(reverse_time)
        canonical = self._canonical_restricted(state)
        outcome = self.observation_reference.collapse(observation)
        try:
            return self._evaluate_canonical(
                context, canonical, outcome, restricted=True
            )
        except AssociationPreconditionerNumericalError:
            raise
        except ArithmeticError as error:
            raise AssociationPreconditionerNumericalError(
                "point evaluation cannot be certified numerically"
            ) from error

    evaluate_restricted = evaluate

    def coordinate_gradients(
        self, reverse_time: object, state: object, observation: object
    ) -> BoundPreconditionerGradients:
        context = self._context(reverse_time)
        sources = self._canonical_restricted(state)
        outcome = self.observation_reference.collapse(observation)
        if outcome is OVERFLOW_OBSERVATION:
            raise ValueError(
                "overflow coordinate gradients are outside the retained API"
            )
        factors = self._retained_factors(
            context,
            sources,
            outcome,
            pair_passes=2,
            require_marginals=True,
        )
        clean_log_density = evaluate_retained_association(
            factors, contamination_probability=0.0
        ).clean_log_density
        offsets = [0]
        for source in sources:
            offsets.append(offsets[-1] + len(source.coordinates))
        if clean_log_density == -math.inf:
            gradients = AssociationCoordinateGradients(
                clean_log_density,
                self.contamination_probability,
                tuple(offsets),
                np.zeros(offsets[-1], dtype=np.float64),
                np.full((len(outcome), len(sources)), -math.inf, dtype=np.float64),
            )
        else:
            marginals = labelled_association_edge_marginals(factors)
            positive_log = positive_association_log_density(
                marginals.log_density, self.contamination_probability
            )
            log_clean_responsibility = (
                math.log1p(-self.contamination_probability)
                + marginals.log_density
                - positive_log
            )
            packed = []
            for source_index, source in enumerate(sources):
                component_terms = [list() for _ in source.coordinates]
                for observation_index, observed in enumerate(outcome):
                    edge_log = float(
                        marginals.edge_log_marginals[observation_index, source_index]
                    )
                    if edge_log == -math.inf:
                        continue
                    (
                        _,
                        log_no_responsibility,
                        no_gradient,
                    ) = self._source_anchor_log_and_no_replacement_score(
                        context, observed, source
                    )
                    if log_no_responsibility == -math.inf:
                        continue
                    log_weight = (
                        edge_log + log_clean_responsibility + log_no_responsibility
                    )
                    for coordinate_index, value in enumerate(no_gradient):
                        component_terms[coordinate_index].append(
                            (log_weight, float(value))
                        )
                for terms in component_terms:
                    packed.append(
                        _signed_log_weighted_sum(
                            terms, name="propagated association gradient"
                        )
                    )
            gradients = AssociationCoordinateGradients(
                marginals.log_density,
                self.contamination_probability,
                tuple(offsets),
                np.asarray(packed, dtype=np.float64),
                marginals.edge_log_marginals,
            )
        return BoundPreconditionerGradients(
            context.propagation.reverse_time,
            sources,
            outcome,
            self.parameter_key(),
            gradients,
            _construction_token=_GRADIENT_TOKEN,
        )

    @staticmethod
    def _multiset_difference(
        left: TransformedConfiguration, right: TransformedConfiguration
    ) -> Tuple[TransformedEvent, ...]:
        remainder = list(right)
        for event in left:
            try:
                remainder.remove(event)
            except ValueError:
                continue
        return tuple(remainder)

    def _classify_edit(
        self,
        source: TransformedConfiguration,
        destination: TransformedConfiguration,
    ) -> str:
        removed = self._multiset_difference(destination, source)
        added = self._multiset_difference(source, destination)
        if (
            len(removed) == 0
            and len(added) == 1
            and len(destination) == len(source) + 1
        ):
            return "birth"
        if (
            len(removed) == 1
            and len(added) == 0
            and len(destination) + 1 == len(source)
        ):
            return "death"
        if len(removed) == 1 and len(added) == 1 and len(destination) == len(source):
            before = removed[0]
            after = added[0]
            if before.event_type == after.event_type:
                raise ValueError("a replacement edge must change event type")
            if (
                self.process.rates.replacement_rate(before.event_type, after.event_type)
                == 0.0
            ):
                raise ValueError("replacement edge has zero reference rate")
            return "replacement"
        raise ValueError("states do not differ by exactly one reference edit")

    def edit_log_ratio(
        self,
        reverse_time: object,
        source_state: object,
        destination_state: object,
        observation: object,
        *,
        allow_outward_cap_birth: bool = False,
    ) -> BoundPreconditionerEditRatio:
        context = self._context(reverse_time)
        source = self._canonical_restricted(source_state)
        outcome = self.observation_reference.collapse(observation)
        if allow_outward_cap_birth:
            destination = self._canonical_unbounded(destination_state)
            if len(destination) > self.process.reference.total_cap + 1:
                raise ValueError("outward cap diagnostics admit at most N+1 events")
        else:
            destination = self._canonical_restricted(destination_state)
        edit_kind = self._classify_edit(source, destination)
        if len(destination) > self.process.reference.total_cap:
            if (
                not allow_outward_cap_birth
                or edit_kind != "birth"
                or len(source) != self.process.reference.total_cap
            ):
                raise ValueError("destination lies outside the target cap")
        source_evaluation = self._evaluate_canonical(
            context, source, outcome, restricted=True
        )
        destination_evaluation = self._evaluate_canonical(
            context,
            destination,
            outcome,
            restricted=len(destination) <= self.process.reference.total_cap,
        )
        if destination_evaluation.outcome != source_evaluation.outcome:
            raise ArithmeticError("one observation collapsed inconsistently")
        return BoundPreconditionerEditRatio(
            reverse_time=context.propagation.reverse_time,
            edit_kind=edit_kind,
            source_state=source,
            destination_state=destination,
            outcome=source_evaluation.outcome,
            log_ratio=destination_evaluation.log_density
            - source_evaluation.log_density,
            preconditioner_parameter_key=self.parameter_key(),
            _construction_token=_EDGE_RATIO_TOKEN,
        )

    def _integrated_birth_evaluation(
        self,
        context: _PropagationContext,
        state: TransformedConfiguration,
        observation: object,
    ) -> AssociationDensityEvaluation:
        outcome = self.observation_reference.collapse(observation)
        augmented_latent_count = len(state) + 1
        if (
            outcome is not OVERFLOW_OBSERVATION
            and augmented_latent_count * len(outcome) > MAX_ASSOCIATION_MATRIX_ENTRIES
        ):
            raise AssociationObservationResourceError(
                "integrated-birth pair matrix exceeds the entry limit"
            )
        if outcome is OVERFLOW_OBSERVATION:
            self._preflight_overflow_evaluation_resources(
                context, augmented_latent_count
            )
        else:
            self._preflight_retained_evaluation_resources(
                context,
                augmented_latent_count,
                len(outcome),
                pair_passes=0,
                require_marginals=False,
            )
        extra_detection = (
            context.propagation.death_survival * self.reference_detected_probability
        )
        if (
            context.propagation.death_survival > 0.0
            and self.reference_detected_probability > 0.0
            and extra_detection == 0.0
        ):
            raise AssociationPreconditionerNumericalError(
                "positive integrated-birth detection underflows float64"
            )
        current_detection = self._source_detection_vector(context, state)
        augmented_detection = np.concatenate(
            (current_detection, np.asarray((extra_detection,), dtype=np.float64))
        )
        if outcome is OVERFLOW_OBSERVATION:
            return evaluate_overflow_association(
                self.observation_reference,
                augmented_detection,
                context.propagation.total_background_intensity,
                contamination_probability=self.contamination_probability,
            )
        if _association_cardinality_is_structural_zero(
            augmented_detection,
            context.propagation.total_background_intensity,
            len(outcome),
        ):
            return evaluate_retained_association(
                RetainedAssociationFactors(
                    augmented_detection,
                    np.full(
                        (len(outcome), len(augmented_detection)),
                        -math.inf,
                        dtype=np.float64,
                    ),
                    np.full(len(outcome), -math.inf, dtype=np.float64),
                    context.propagation.total_background_intensity,
                ),
                contamination_probability=self.contamination_probability,
            )
        self._preflight_retained_evaluation_resources(
            context,
            augmented_latent_count,
            len(outcome),
            pair_passes=1,
            require_marginals=False,
        )
        base_pair_logs = self._pair_log_matrix(
            context, state, outcome, current_detection
        )
        extra_pair = np.full((len(outcome), 1), -math.inf, dtype=np.float64)
        if extra_detection > 0.0:
            for observation_index, observed in enumerate(outcome):
                reference_anchor = self._reference_anchor_log_density(observed)
                if reference_anchor != -math.inf:
                    extra_pair[observation_index, 0] = reference_anchor - math.log(
                        self.reference_detected_probability
                    )
        factors = RetainedAssociationFactors(
            augmented_detection,
            np.concatenate((base_pair_logs, extra_pair), axis=1),
            np.asarray(
                [
                    self._background_log_intensity(context, observed)
                    for observed in outcome
                ],
                dtype=np.float64,
            ),
            context.propagation.total_background_intensity,
        )
        return evaluate_retained_association(
            factors,
            contamination_probability=self.contamination_probability,
        )

    def integrated_reference_birth_log_density(
        self, reverse_time: object, state: object, observation: object
    ) -> float:
        context = self._context(reverse_time)
        canonical = self._canonical_restricted(state)
        return self._integrated_birth_evaluation(
            context, canonical, observation
        ).log_density

    def cap_boundary_defect(
        self, reverse_time: object, state: object, observation: object
    ) -> CapBoundaryDefectEvaluation:
        context = self._context(reverse_time)
        canonical = self._canonical_restricted(state)
        outcome = self.observation_reference.collapse(observation)
        evaluation = self._evaluate_canonical(
            context, canonical, outcome, restricted=True
        )
        at_cap = len(canonical) == self.process.reference.total_cap
        forward_time = self.process.schedule.horizon - context.propagation.reverse_time
        blocked_rate = (
            _checked_product(
                self.process.schedule.jump_rate(forward_time),
                self.process.rates.birth_rate,
                name="blocked birth rate",
            )
            if at_cap
            else 0.0
        )
        if at_cap:
            integrated = self._integrated_birth_evaluation(context, canonical, outcome)
            log_ratio = integrated.log_density - evaluation.log_density
            sign, log_absolute = _log_abs_expm1(log_ratio)
            if sign == 0:
                ratio_minus_one = 0.0
            else:
                ratio_minus_one = math.copysign(
                    _ordinary_from_log(
                        log_absolute, name="integrated birth guide ratio minus one"
                    ),
                    sign,
                )
            cap_defect = -_checked_product(
                blocked_rate,
                ratio_minus_one,
                name="cap-boundary defect",
            )
            integrated_log: Optional[float] = integrated.log_density
        else:
            integrated_log = None
            ratio_minus_one = 0.0
            cap_defect = 0.0
        return CapBoundaryDefectEvaluation(
            reverse_time=context.propagation.reverse_time,
            state=canonical,
            outcome=evaluation.outcome,
            at_cap=at_cap,
            blocked_birth_rate=blocked_rate,
            guide_log_density=evaluation.log_density,
            integrated_birth_log_density=integrated_log,
            integral_ratio_minus_one=ratio_minus_one,
            cap_boundary_defect=cap_defect,
            preconditioner_parameter_key=self.parameter_key(),
            _construction_token=_CAP_DEFECT_TOKEN,
        )

    def _proposal_estimate(
        self,
        context: _PropagationContext,
        state: TransformedConfiguration,
        observation: object,
        samples: Tuple[BirthProposalSample, ...],
        *,
        proposal_key: Tuple[object, ...],
        stream_key: Tuple[object, ...],
        exact_cap_boundary_defect: Optional[float],
        sampling_provenance_certified: bool,
    ) -> CapBoundaryProposalEstimate:
        if len(state) != self.process.reference.total_cap:
            raise ValueError("cap proposal estimates require a cap state")
        outcome = self.observation_reference.collapse(observation)
        base = self._evaluate_canonical(context, state, outcome, restricted=True)
        log_contributions = []
        contribution_signs = []
        log_weights = []
        digest = hashlib.sha256()
        for sample in samples:
            event = self.terminal_channel._validate_source(sample.event)
            reference_log = self.process.reference.log_one_event_density(event)
            log_weight = reference_log - sample.proposal_log_density
            if not math.isfinite(log_weight):
                raise AssociationPreconditionerNumericalError(
                    "proposal importance log weight is not representable"
                )
            log_weights.append(log_weight)
            augmented = tuple(sorted(state + (event,), key=TransformedEvent.model_key))
            plus = self._evaluate_canonical(
                context, augmented, outcome, restricted=False
            )
            sign, log_abs = _log_abs_expm1(plus.log_density - base.log_density)
            contribution_signs.append(sign)
            log_contribution = -math.inf if sign == 0 else log_weight + log_abs
            if sign != 0 and not math.isfinite(log_contribution):
                raise AssociationPreconditionerNumericalError(
                    "proposal contribution is not representable in log space"
                )
            log_contributions.append(log_contribution)
            digest.update(
                repr((event.model_key(), sample.proposal_log_density)).encode("utf-8")
            )
            digest.update(b"\n")

        finite_logs = [value for value in log_contributions if value != -math.inf]
        scale_log = max(finite_logs) if finite_logs else 0.0
        scaled = np.asarray(
            [
                0.0
                if sign == 0
                else math.copysign(math.exp(log_value - scale_log), sign)
                for sign, log_value in zip(contribution_signs, log_contributions)
            ],
            dtype=np.float64,
        )
        mean = _signed_log_weighted_mean(
            (
                (log_value, float(sign))
                for sign, log_value in zip(contribution_signs, log_contributions)
            ),
            count=len(samples),
            name="proposal integral estimate",
        )
        # Centering is needed only at the unit-scaled precision used for the
        # second moment.  A residual smaller than that scale's float64 range
        # cannot change the representable variance, even when the unscaled
        # residual above remains a representable mean.
        mean_scaled = math.fsum(float(value) for value in scaled) / len(samples)
        squared = math.fsum((float(value) - mean_scaled) ** 2 for value in scaled)
        variance_scaled = squared / (len(samples) - 1)
        standard_error_scaled = math.sqrt(variance_scaled / len(samples))
        standard_error = (
            0.0
            if standard_error_scaled == 0.0
            else _ordinary_from_log(
                math.log(standard_error_scaled) + scale_log,
                name="proposal integral standard error",
            )
        )
        weight_sum_log = _logsumexp(log_weights)
        weight_sum = _ordinary_from_log(weight_sum_log, name="importance weight sum")
        forward_time = self.process.schedule.horizon - context.propagation.reverse_time
        blocked_rate = _checked_product(
            self.process.schedule.jump_rate(forward_time),
            self.process.rates.birth_rate,
            name="proposal blocked birth rate",
        )
        cap_estimate = -_checked_product(
            blocked_rate, mean, name="proposal cap-boundary estimate"
        )
        cap_standard_error = _checked_product(
            blocked_rate,
            standard_error,
            name="proposal cap-boundary standard error",
        )
        return CapBoundaryProposalEstimate(
            reverse_time=context.propagation.reverse_time,
            state=state,
            outcome=base.outcome,
            sample_count=len(samples),
            proposal_key=proposal_key,
            stream_key=stream_key,
            sample_digest=digest.hexdigest(),
            importance_weight_sum=weight_sum,
            integral_ratio_minus_one_estimate=mean,
            integral_standard_error=standard_error,
            cap_boundary_estimate=cap_estimate,
            cap_boundary_standard_error=cap_standard_error,
            exact_cap_boundary_defect=exact_cap_boundary_defect,
            preconditioner_parameter_key=self.parameter_key(),
            sampling_provenance_certified=sampling_provenance_certified,
            _construction_token=_PROPOSAL_ESTIMATE_TOKEN,
        )

    def _preflight_proposal_resources(
        self,
        state: TransformedConfiguration,
        outcome: PreconditionerObservation,
        *,
        sample_count: int,
        coordinate_count: int,
    ) -> None:
        if coordinate_count > MAX_PRECONDITIONER_PROPOSAL_COORDINATES:
            raise AssociationObservationResourceError(
                "proposal coordinates exceed the aggregate limit of %d"
                % MAX_PRECONDITIONER_PROPOSAL_COORDINATES
            )
        latent_count = len(state) + 1
        type_count = len(self.process.reference.type_ids)
        detection_work = latent_count * type_count**2
        canonical_insertion_work = sum(len(event.coordinates) for event in state)
        if outcome is OVERFLOW_OBSERVATION:
            evaluation_work = detection_work + latent_count * (
                self.observation_reference.retained_cap + 1
            )
        else:
            observation_count = len(outcome)
            observation_solve_work = max(
                dimension**3
                for dimension in self.observation_reference.type_dimensions.values()
            )
            if latent_count == 0 or observation_count == 0:
                association_work = latent_count + observation_count + 1
            else:
                association_work = (
                    latent_count
                    * observation_count
                    * (1 << min(latent_count, observation_count))
                )
            pair_work = (
                (latent_count + 1)
                * observation_count
                * max(
                    1,
                    type_count,
                    self.gaussian_component_count,
                    self.covariance_work,
                    observation_solve_work,
                )
            )
            evaluation_work = detection_work + association_work + pair_work
        aggregate_work = (
            sample_count * max(1, evaluation_work + canonical_insertion_work)
            + coordinate_count
        )
        if aggregate_work > MAX_PRECONDITIONER_PROPOSAL_EVALUATION_WORK:
            raise AssociationObservationResourceError(
                "proposal evaluations exceed the aggregate work limit of %d"
                % MAX_PRECONDITIONER_PROPOSAL_EVALUATION_WORK
            )

    def estimate_cap_boundary_from_proposal(
        self,
        reverse_time: object,
        state: object,
        observation: object,
        samples: object,
        *,
        proposal_key: Tuple[object, ...],
        stream_key: Tuple[object, ...],
    ) -> CapBoundaryProposalEstimate:
        context = self._context(reverse_time)
        canonical = self._canonical_restricted(state)
        outcome = self.observation_reference.collapse(observation)
        raw_samples = _bounded_tuple(
            samples,
            name="birth proposal samples",
            maximum_items=MAX_PRECONDITIONER_PROPOSAL_SAMPLES,
        )
        if len(raw_samples) < 2:
            raise ValueError(
                "at least two proposal samples are required for a standard error"
            )
        checked_samples = []
        coordinate_count = 0
        for sample in raw_samples:
            if type(sample) is not BirthProposalSample:
                raise TypeError("samples must be exact BirthProposalSample instances")
            self.terminal_channel._validate_source(sample.event)
            coordinate_count += len(sample.event.coordinates)
            checked_samples.append(sample)
        self._preflight_proposal_resources(
            canonical,
            outcome,
            sample_count=len(checked_samples),
            coordinate_count=coordinate_count,
        )
        checked_proposal_key = _validated_key(proposal_key, name="proposal_key")
        checked_stream_key = _validated_key(stream_key, name="stream_key")
        exact = self.cap_boundary_defect(
            context.propagation.reverse_time, canonical, outcome
        ).cap_boundary_defect
        return self._proposal_estimate(
            context,
            canonical,
            outcome,
            tuple(checked_samples),
            proposal_key=checked_proposal_key,
            stream_key=checked_stream_key,
            exact_cap_boundary_defect=exact,
            sampling_provenance_certified=False,
        )

    def estimate_cap_boundary_from_reference(
        self,
        reverse_time: object,
        state: object,
        observation: object,
        *,
        seed: object,
        sample_count: object,
    ) -> CapBoundaryProposalEstimate:
        checked_seed = _validated_nonnegative_integer(
            seed, name="seed", maximum=2**64 - 1
        )
        count = _validated_nonnegative_integer(
            sample_count,
            name="sample_count",
            maximum=MAX_PRECONDITIONER_PROPOSAL_SAMPLES,
        )
        if count < 2:
            raise ValueError("sample_count must be at least two")
        context = self._context(reverse_time)
        canonical = self._canonical_restricted(state)
        outcome = self.observation_reference.collapse(observation)
        maximum_dimension = max(self.process.reference.type_dimensions.values())
        self._preflight_proposal_resources(
            canonical,
            outcome,
            sample_count=count,
            coordinate_count=count * maximum_dimension,
        )
        exact = self.cap_boundary_defect(
            context.propagation.reverse_time, canonical, outcome
        ).cap_boundary_defect
        rng = np.random.default_rng(checked_seed)
        samples = []
        for _ in range(count):
            event = self.process.reference.sample_event(rng)
            samples.append(
                BirthProposalSample(
                    event,
                    self.process.reference.log_one_event_density(event),
                )
            )
        return self._proposal_estimate(
            context,
            canonical,
            outcome,
            tuple(samples),
            proposal_key=(
                "reference-event-law",
                self.process.reference.parameter_key(),
            ),
            stream_key=("numpy-default-rng", np.__version__, checked_seed),
            exact_cap_boundary_defect=exact,
            sampling_provenance_certified=True,
        )


__all__ = [
    "ANALYTIC_GUIDE_RANGE_CERTIFICATE_SCOPE",
    "ANALYTIC_GUIDE_RANGE_SCHEMA_VERSION",
    "AnalyticAssociationPreconditioner",
    "AnalyticGuideRangeCertificate",
    "AssociationPreconditionerNumericalError",
    "AssociationPropagation",
    "BirthProposalSample",
    "BoundPreconditionerEditRatio",
    "BoundPreconditionerEvaluation",
    "BoundPreconditionerGradients",
    "CapBoundaryDefectEvaluation",
    "CapBoundaryProposalEstimate",
    "MAX_PRECONDITIONER_EVALUATION_WORK",
    "MAX_PRECONDITIONER_EXPONENTIAL_WORK",
    "MAX_PRECONDITIONER_GAUSSIAN_COMPONENTS",
    "MAX_PRECONDITIONER_GUIDE_CERTIFICATE_WORK",
    "MAX_PRECONDITIONER_COVARIANCE_WORK",
    "MAX_PRECONDITIONER_KEY_DEPTH",
    "MAX_PRECONDITIONER_KEY_NODES",
    "MAX_PRECONDITIONER_PROPOSAL_COORDINATES",
    "MAX_PRECONDITIONER_PROPOSAL_EVALUATION_WORK",
    "MAX_PRECONDITIONER_PROPOSAL_SAMPLES",
    "MAX_PRECONDITIONER_TYPES",
    "OneOccurrenceTerminalKernel",
    "PRECONDITIONER_NUMERICAL_ATOL",
]
