"""Normalized unordered observations for heterogeneous configurations.

This module is the theorem-to-code layer for the observation contract in
Section 5 of ``manuscript_v3/executable_method_spec.md``.  It provides the
unit-rate Poisson configuration reference with one collapsed overflow outcome,
the exact labelled subset dynamic program with misses and Poisson clutter, a
duplicate-orbit oracle, a typed affine-Gaussian emission family, and the
declared whole-observation positive mixture.

All association calculations are occurrence based.  Repeated identical atoms
remain repeated occurrences; quotient calculations recover the same sum using
the exact orbit coefficient.  Clean structural zeros are represented by
``-inf`` log densities and are never floored.  Positivity is introduced only
by the explicit mixture with the normalized observation reference.

This is not the analytic preconditioner, a scalable approximate matcher, a
learned residual, or a conditional sampler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, localcontext
import math
from numbers import Integral, Real
from types import MappingProxyType
from typing import Iterable, Mapping, Optional, Tuple, Union

import numpy as np
from scipy.special import gammainc

from .configuration_reference import (
    CappedPoissonConfigurationReference,
    TransformedConfiguration,
    TransformedEvent,
)
from .finite_atomic_overflow_observation import (
    OVERFLOW_OBSERVATION,
    OverflowObservation,
)


AssociationObservationValue = Union[TransformedConfiguration, OverflowObservation]

MAX_ASSOCIATION_OBSERVATION_CAP = 4_096
MAX_ASSOCIATION_OCCURRENCES = 100_000
MAX_ASSOCIATION_MATRIX_ENTRIES = 4_000_000
MAX_ASSOCIATION_SUBSET_BITS = 20
MAX_ASSOCIATION_DP_WORK = 20_000_000
MAX_ASSOCIATION_ORBIT_OCCURRENCES = 128
MAX_ASSOCIATION_ORBIT_CLASSES = 100_000
MAX_ASSOCIATION_DISTINCT_ATOMS = 64
MAX_ASSOCIATION_CLUTTER_MEAN = 10_000.0
MAX_AFFINE_OBSERVATION_DIMENSION = 256
MAX_AFFINE_COVARIANCE_WORK = 20_000_000

ASSOCIATION_NORMALIZATION_ATOL = 5.0e-12

_FLOAT64_EPSILON = float(np.finfo(np.float64).eps)
_MIN_NORMAL_FLOAT64 = float(np.finfo(np.float64).tiny)
_MIN_SUBNORMAL_FLOAT64 = float(np.nextafter(0.0, 1.0))
_LOG_MAX_FLOAT64 = math.log(float(np.finfo(np.float64).max))
_LOG_MIN_SUBNORMAL_FLOAT64 = math.log(_MIN_SUBNORMAL_FLOAT64)
_LOG_TWO_PI = math.log(2.0 * math.pi)
MAX_POISSON_TAIL_TERMS = 100_000

_BOUND_EVALUATION_CONSTRUCTION_TOKEN = object()
_BOUND_GRADIENT_CONSTRUCTION_TOKEN = object()


class AssociationObservationResourceError(ValueError):
    """Raised when an exact association calculation exceeds its hard limit."""


def _bounded_tuple(
    value: object,
    *,
    name: str,
    maximum_items: int,
) -> Tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError("%s must be an iterable of values, not text" % name)
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


def _validated_integer(
    value: object,
    *,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result < minimum or result > maximum:
        raise ValueError("%s must lie in [%d, %d]" % (name, minimum, maximum))
    return result


def _validated_real(
    value: object,
    *,
    name: str,
    nonnegative: bool = False,
    strictly_positive: bool = False,
) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % name)
    if strictly_positive and result <= 0.0:
        raise ValueError("%s must be strictly positive" % name)
    if nonnegative and result < 0.0:
        raise ValueError("%s must be nonnegative" % name)
    return 0.0 if result == 0.0 else result


def _validated_probability(
    value: object,
    *,
    name: str,
    allow_zero: bool = True,
    allow_one: bool = True,
) -> float:
    result = _validated_real(value, name=name)
    lower_ok = result >= 0.0 if allow_zero else result > 0.0
    upper_ok = result <= 1.0 if allow_one else result < 1.0
    if not lower_ok or not upper_ok:
        left = "[" if allow_zero else "("
        right = "]" if allow_one else ")"
        raise ValueError("%s must lie in %s0, 1%s" % (name, left, right))
    return result


def _validated_contamination_probability(value: object) -> float:
    result = _validated_probability(
        value,
        name="contamination_probability",
        allow_zero=True,
        allow_one=False,
    )
    if 0.0 < result < _MIN_NORMAL_FLOAT64:
        raise ValueError(
            "positive contamination_probability must be a normal float64 value"
        )
    return result


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    contiguous[contiguous == 0.0] = 0.0
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.float64
    ).reshape(contiguous.shape)


def _preflight_array(
    value: object,
    *,
    name: str,
    ndim: int,
    maximum_entries: int,
    expected_shape: Optional[Tuple[int, ...]] = None,
    maximum_axis_lengths: Optional[Tuple[int, ...]] = None,
) -> Tuple[int, ...]:
    if expected_shape is not None and len(expected_shape) != ndim:
        raise ValueError("internal expected array shape has the wrong rank")
    if maximum_axis_lengths is not None and len(maximum_axis_lengths) != ndim:
        raise ValueError("internal maximum array shape has the wrong rank")
    if isinstance(value, np.ndarray):
        if value.ndim != ndim:
            raise ValueError("%s must be %d-dimensional" % (name, ndim))
        shape = tuple(int(item) for item in value.shape)
        if expected_shape is not None and shape != expected_shape:
            raise ValueError(
                "%s must have shape %r" % (name, expected_shape)
            )
        if maximum_axis_lengths is not None and any(
            actual > maximum
            for actual, maximum in zip(shape, maximum_axis_lengths)
        ):
            raise AssociationObservationResourceError(
                "%s exceeds an axis-length limit" % name
            )
        if value.size > maximum_entries:
            raise AssociationObservationResourceError(
                "%s exceeds the %d-entry limit" % (name, maximum_entries)
            )
        return shape
    if not isinstance(value, (list, tuple)):
        raise TypeError("%s must be a NumPy array, list, or tuple" % name)
    if ndim == 1:
        if expected_shape is not None and len(value) != expected_shape[0]:
            raise ValueError(
                "%s must have shape %r" % (name, expected_shape)
            )
        if (
            maximum_axis_lengths is not None
            and len(value) > maximum_axis_lengths[0]
        ):
            raise AssociationObservationResourceError(
                "%s exceeds an axis-length limit" % name
            )
        if len(value) > maximum_entries:
            raise AssociationObservationResourceError(
                "%s exceeds the %d-entry limit" % (name, maximum_entries)
            )
        if any(
            isinstance(item, (list, tuple, np.ndarray)) for item in value
        ):
            raise ValueError("%s must be 1-dimensional" % name)
        return (len(value),)
    if ndim != 2:
        raise ValueError("unsupported array dimension")
    if expected_shape is not None and len(value) != expected_shape[0]:
        raise ValueError("%s must have shape %r" % (name, expected_shape))
    if (
        maximum_axis_lengths is not None
        and len(value) > maximum_axis_lengths[0]
    ):
        raise AssociationObservationResourceError(
            "%s exceeds an axis-length limit" % name
        )
    width = None
    total = 0
    for row in value:
        if isinstance(row, np.ndarray):
            if row.ndim != 1:
                raise ValueError("%s must be a rectangular numeric array" % name)
            row_width = int(row.size)
        elif isinstance(row, (list, tuple)):
            row_width = len(row)
        else:
            raise ValueError("%s must be a rectangular numeric array" % name)
        if expected_shape is not None and row_width != expected_shape[1]:
            raise ValueError(
                "%s must have shape %r" % (name, expected_shape)
            )
        if (
            maximum_axis_lengths is not None
            and row_width > maximum_axis_lengths[1]
        ):
            raise AssociationObservationResourceError(
                "%s exceeds an axis-length limit" % name
            )
        if width is None:
            width = row_width
        elif row_width != width:
            raise ValueError("%s must be a rectangular numeric array" % name)
        total += row_width
        if total > maximum_entries:
            raise AssociationObservationResourceError(
                "%s exceeds the %d-entry limit" % (name, maximum_entries)
            )
        if any(
            isinstance(item, (list, tuple, np.ndarray)) for item in row
        ):
            raise ValueError("%s must be 2-dimensional" % name)
    return (len(value), 0 if width is None else width)


def _numeric_array(
    value: object,
    *,
    name: str,
    ndim: int,
    maximum_entries: int,
) -> np.ndarray:
    _preflight_array(
        value,
        name=name,
        ndim=ndim,
        maximum_entries=maximum_entries,
    )
    try:
        raw = np.asarray(value)
    except (TypeError, ValueError, OverflowError, Warning) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    if raw.ndim != ndim:
        raise ValueError("%s must be %d-dimensional" % (name, ndim))
    if raw.size > maximum_entries:
        raise AssociationObservationResourceError(
            "%s exceeds the %d-entry limit" % (name, maximum_entries)
        )
    try:
        object_view = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError, Warning) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    if any(isinstance(item, (bool, np.bool_)) for item in object_view.flat):
        raise TypeError("%s must not contain boolean entries" % name)
    if raw.dtype.kind not in "iuf":
        raise TypeError("%s must have a real numeric dtype" % name)
    try:
        result = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError, OverflowError, Warning) as error:
        raise ValueError("%s cannot be represented as float64" % name) from error
    if not np.all(np.isfinite(result)):
        raise ValueError("%s entries must be finite" % name)
    result[result == 0.0] = 0.0
    return result


def _log_array(
    value: object,
    *,
    name: str,
    ndim: int,
    maximum_entries: int,
) -> np.ndarray:
    _preflight_array(
        value,
        name=name,
        ndim=ndim,
        maximum_entries=maximum_entries,
    )
    try:
        raw = np.asarray(value)
    except (TypeError, ValueError, OverflowError, Warning) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    if raw.ndim != ndim:
        raise ValueError("%s must be %d-dimensional" % (name, ndim))
    if raw.size > maximum_entries:
        raise AssociationObservationResourceError(
            "%s exceeds the %d-entry limit" % (name, maximum_entries)
        )
    try:
        object_view = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError, Warning) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    if any(isinstance(item, (bool, np.bool_)) for item in object_view.flat):
        raise TypeError("%s must not contain boolean entries" % name)
    if raw.dtype.kind not in "iuf":
        raise TypeError("%s must have a real numeric dtype" % name)
    try:
        result = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError, OverflowError, Warning) as error:
        raise ValueError("%s cannot be represented as float64" % name) from error
    if np.any(np.isnan(result)) or np.any(np.isposinf(result)):
        raise ValueError("%s entries must be finite or -inf" % name)
    result[result == 0.0] = 0.0
    return result


def _probability_vector(value: object, *, name: str) -> np.ndarray:
    result = _numeric_array(
        value,
        name=name,
        ndim=1,
        maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
    )
    if np.any(result < 0.0) or np.any(result > 1.0):
        raise ValueError("%s entries must lie in [0, 1]" % name)
    return result


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


def _nonnegative_to_log(array: np.ndarray, *, name: str) -> np.ndarray:
    if np.any(array < 0.0):
        raise ValueError("%s entries must be nonnegative" % name)
    result = np.full(array.shape, -math.inf, dtype=np.float64)
    positive = array > 0.0
    result[positive] = np.log(array[positive])
    return result


def _log_nonnegative(value: float) -> float:
    return -math.inf if value == 0.0 else math.log(value)


def _logaddexp(first: float, second: float) -> float:
    if first == -math.inf:
        return second
    if second == -math.inf:
        return first
    maximum = max(first, second)
    result = maximum + math.log1p(math.exp(-abs(first - second)))
    if not math.isfinite(result):
        raise ArithmeticError("association log-sum is not representable")
    return result


def _logsumexp(values: Iterable[float]) -> float:
    checked = tuple(value for value in values if value != -math.inf)
    if not checked:
        return -math.inf
    maximum = max(checked)
    maximum_index = checked.index(maximum)
    try:
        scaled_residual = math.fsum(
            math.exp(value - maximum)
            for index, value in enumerate(checked)
            if index != maximum_index
        )
    except OverflowError as error:
        raise ArithmeticError("association log-sum is not representable") from error
    result = maximum + math.log1p(scaled_residual)
    if not math.isfinite(result):
        raise ArithmeticError("association log-sum is not representable")
    return result


def _sum_logs(values: Iterable[float]) -> float:
    checked = tuple(values)
    if any(value == -math.inf for value in checked):
        return -math.inf
    return _high_range_fsum(checked, name="association log-product")


def _high_range_fsum(values: Iterable[float], *, name: str) -> float:
    checked = tuple(values)
    if any(not math.isfinite(value) for value in checked):
        raise ArithmeticError("%s is not representable" % name)
    try:
        result = math.fsum(checked)
    except (OverflowError, ValueError):
        try:
            with localcontext() as context:
                context.prec = 1_200
                decimal_result = sum(
                    Decimal.from_float(value) for value in checked
                )
        except (InvalidOperation, OverflowError) as error:
            raise ArithmeticError("%s is not representable" % name) from error
        try:
            result = float(decimal_result)
        except (OverflowError, ValueError) as error:
            raise ArithmeticError("%s is not representable" % name) from error
    if not math.isfinite(result):
        raise ArithmeticError("%s is not representable" % name)
    return 0.0 if result == 0.0 else result


def _quadratic_form_difference(
    positive_values: Iterable[float],
    negative_values: Iterable[float],
) -> float:
    positive = tuple(float(value) for value in positive_values)
    negative = tuple(float(value) for value in negative_values)
    ordinary_terms = [value * value for value in positive]
    ordinary_terms.extend(-(value * value) for value in negative)
    if all(math.isfinite(value) for value in ordinary_terms):
        try:
            result = math.fsum(ordinary_terms)
        except (OverflowError, ValueError):
            result = math.nan
        if math.isfinite(result):
            return 0.0 if result == 0.0 else result
    try:
        with localcontext() as context:
            context.prec = 1_200
            decimal_result = sum(
                Decimal.from_float(value) * Decimal.from_float(value)
                for value in positive
            ) - sum(
                Decimal.from_float(value) * Decimal.from_float(value)
                for value in negative
            )
    except (InvalidOperation, OverflowError) as error:
        raise ArithmeticError(
            "affine Gaussian quadratic form is not representable"
        ) from error
    try:
        result = float(decimal_result)
    except (OverflowError, ValueError) as error:
        raise ArithmeticError(
            "affine Gaussian quadratic form is not representable"
        ) from error
    if not math.isfinite(result):
        raise ArithmeticError(
            "affine Gaussian quadratic form is not representable"
        )
    return 0.0 if result == 0.0 else result


def _high_range_affine_map(
    matrix: np.ndarray,
    vector: np.ndarray,
    bias: np.ndarray,
) -> np.ndarray:
    """Evaluate an affine map with guarded products and cancellation."""

    values = []
    for row, offset in zip(matrix, bias):
        terms = [float(offset)]
        terms.extend(
            float(coefficient) * float(coordinate)
            for coefficient, coordinate in zip(row, vector)
        )
        use_decimal = any(not math.isfinite(term) for term in terms)
        if not use_decimal:
            try:
                ordinary_value = math.fsum(terms)
                absolute_sum = math.fsum(abs(term) for term in terms)
            except (OverflowError, ValueError):
                use_decimal = True
            else:
                use_decimal = (
                    absolute_sum != 0.0
                    and abs(ordinary_value)
                    <= 64.0 * _FLOAT64_EPSILON * absolute_sum
                )
        if use_decimal:
            try:
                with localcontext() as context:
                    context.prec = 2_200
                    decimal_value = Decimal.from_float(float(offset))
                    decimal_value += sum(
                        Decimal.from_float(float(coefficient))
                        * Decimal.from_float(float(coordinate))
                        for coefficient, coordinate in zip(row, vector)
                    )
                ordinary_value = float(decimal_value)
            except (InvalidOperation, OverflowError, ValueError) as error:
                raise ArithmeticError(
                    "affine Gaussian mean or residual is not representable"
                ) from error
        values.append(ordinary_value)
    result = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(result)):
        raise ArithmeticError(
            "affine Gaussian mean or residual is not representable"
        )
    return result


def _ordinary_from_log(log_value: float, *, name: str) -> float:
    if log_value == -math.inf:
        return 0.0
    if not math.isfinite(log_value):
        raise ArithmeticError("log %s is not finite" % name)
    if log_value > _LOG_MAX_FLOAT64:
        raise ArithmeticError("%s exceeds float64 range" % name)
    if log_value < _LOG_MIN_SUBNORMAL_FLOAT64:
        return 0.0
    result = math.exp(log_value)
    if not math.isfinite(result):
        raise ArithmeticError("%s exceeds float64 range" % name)
    return 0.0 if result == 0.0 else result


def _signed_log_weighted_sum(
    log_weights: Iterable[float],
    values: Iterable[float],
    *,
    name: str,
) -> float:
    checked = []
    for log_weight, value in zip(log_weights, values):
        if log_weight == -math.inf or value == 0.0:
            continue
        if not math.isfinite(log_weight) or not math.isfinite(value):
            raise ArithmeticError("%s is not representable" % name)
        mantissa, exponent = math.frexp(value)
        scale_log = log_weight + exponent * math.log(2.0)
        if not math.isfinite(scale_log):
            raise ArithmeticError("%s is not representable" % name)
        checked.append((log_weight, value, mantissa, scale_log))
    if not checked:
        return 0.0
    dominant = max(item[3] for item in checked)
    scaled_terms = [
        item[2] * math.exp(item[3] - dominant) for item in checked
    ]
    scaled_sum = math.fsum(scaled_terms)
    scaled_absolute_sum = math.fsum(abs(value) for value in scaled_terms)
    if (
        scaled_sum != 0.0
        and abs(scaled_sum)
        > 64.0 * _FLOAT64_EPSILON * scaled_absolute_sum
    ):
        log_magnitude = dominant + math.log(abs(scaled_sum))
        magnitude = _ordinary_from_log(log_magnitude, name=name)
        result = math.copysign(magnitude, scaled_sum)
        return 0.0 if result == 0.0 else result

    try:
        with localcontext() as context:
            context.prec = 200
            exact_sum = sum(
                (
                    Decimal.from_float(log_weight).exp()
                    * Decimal.from_float(value)
                )
                for log_weight, value, _, _ in checked
            )
    except (InvalidOperation, OverflowError) as error:
        raise ArithmeticError("%s is not representable" % name) from error
    try:
        result = float(exact_sum)
    except (OverflowError, ValueError) as error:
        raise ArithmeticError("%s is not representable" % name) from error
    if not math.isfinite(result):
        raise ArithmeticError("%s is not representable" % name)
    return 0.0 if result == 0.0 else result


def _signed_log_product_sum(
    terms: Iterable[Tuple[float, float, float]],
    *,
    name: str,
) -> float:
    raw_terms = tuple(terms)
    ordinary_terms = []
    ordinary_safe = True
    for log_weight, first, second in raw_terms:
        if log_weight == -math.inf or first == 0.0 or second == 0.0:
            continue
        if not all(math.isfinite(value) for value in (log_weight, first, second)):
            raise ArithmeticError("%s is not representable" % name)
        try:
            weight = math.exp(log_weight)
        except OverflowError:
            ordinary_safe = False
            break
        raw_product = first * second
        if weight < _MIN_NORMAL_FLOAT64 or not math.isfinite(raw_product):
            ordinary_safe = False
            break
        weighted_product = weight * raw_product
        if not math.isfinite(weighted_product) or weighted_product == 0.0:
            ordinary_safe = False
            break
        ordinary_terms.append(weighted_product)
    if ordinary_safe:
        try:
            ordinary_result = math.fsum(ordinary_terms)
        except (OverflowError, ValueError):
            ordinary_safe = False
        else:
            if math.isfinite(ordinary_result):
                return 0.0 if ordinary_result == 0.0 else ordinary_result
    checked = []
    for log_weight, first, second in raw_terms:
        if log_weight == -math.inf or first == 0.0 or second == 0.0:
            continue
        if not all(math.isfinite(value) for value in (log_weight, first, second)):
            raise ArithmeticError("%s is not representable" % name)
        checked.append((log_weight, first, second))
    if not checked:
        return 0.0
    try:
        with localcontext() as context:
            context.prec = 2_200
            decimal_result = sum(
                Decimal.from_float(log_weight).exp()
                * Decimal.from_float(first)
                * Decimal.from_float(second)
                for log_weight, first, second in checked
            )
    except (InvalidOperation, OverflowError) as error:
        raise ArithmeticError("%s is not representable" % name) from error
    try:
        result = float(decimal_result)
    except (OverflowError, ValueError) as error:
        raise ArithmeticError("%s is not representable" % name) from error
    if not math.isfinite(result):
        raise ArithmeticError("%s is not representable" % name)
    return 0.0 if result == 0.0 else result


def _log_poisson_tail_above(threshold: int, mean: float) -> float:
    """Return ``log P(Poisson(mean) > threshold)`` without subtraction loss."""

    if threshold < 0:
        return 0.0
    if mean == 0.0:
        return -math.inf
    special_tail = float(gammainc(float(threshold + 1), mean))
    if not math.isfinite(special_tail) or special_tail < 0.0 or special_tail > 1.0:
        raise ArithmeticError("regularized Poisson tail is invalid")
    if special_tail == 1.0:
        return 0.0
    if special_tail > 0.0:
        return math.log(special_tail)
    log_mean = math.log(mean)
    first_count = threshold + 1
    log_first = (
        -mean + first_count * log_mean - math.lgamma(first_count + 1.0)
    )
    scaled_term = 1.0
    scaled_total = 1.0
    count = first_count
    for _ in range(MAX_POISSON_TAIL_TERMS):
        next_ratio = mean / float(count + 1)
        scaled_term *= next_ratio
        scaled_total = math.fsum((scaled_total, scaled_term))
        count += 1
        following_ratio = mean / float(count + 1)
        if following_ratio >= 1.0:
            continue
        remainder_bound = (
            scaled_term * following_ratio / (1.0 - following_ratio)
        )
        if remainder_bound <= 2.0 * _FLOAT64_EPSILON * scaled_total:
            break
    else:
        raise AssociationObservationResourceError(
            "Poisson-tail series exceeded its term limit"
        )
    log_tail = log_first + math.log(scaled_total)
    if log_tail > 0.0:
        if log_tail > ASSOCIATION_NORMALIZATION_ATOL:
            raise ArithmeticError("Poisson tail exceeds one")
        return 0.0
    return log_tail


@dataclass(frozen=True, eq=False, init=False)
class CollapsedPoissonObservationReference:
    """Unit-rate Poisson configuration reference with one overflow outcome."""

    type_ids: Tuple[int, ...]
    type_dimensions: Mapping[int, int]
    type_weights: Mapping[int, float]
    retained_cap: int
    log_overflow_mass: float
    _overflow_mass: float = field(repr=False)
    _base: CappedPoissonConfigurationReference = field(repr=False)

    def __init__(
        self,
        type_dimensions: Mapping[int, int],
        type_weights: Mapping[int, float],
        *,
        retained_cap: int,
    ) -> None:
        cap = _validated_integer(
            retained_cap,
            name="retained_cap",
            minimum=0,
            maximum=MAX_ASSOCIATION_OBSERVATION_CAP,
        )
        base = CappedPoissonConfigurationReference(
            type_dimensions,
            type_weights,
            activity=1.0,
            total_cap=cap,
        )
        log_overflow = _log_poisson_tail_above(cap, 1.0)
        if log_overflow == -math.inf:
            raise ArithmeticError("collapsed Poisson overflow mass must be positive")
        overflow_mass = _ordinary_from_log(
            log_overflow, name="collapsed Poisson overflow mass"
        )
        object.__setattr__(self, "type_ids", base.type_ids)
        object.__setattr__(self, "type_dimensions", base.type_dimensions)
        object.__setattr__(self, "type_weights", base.type_weights)
        object.__setattr__(self, "retained_cap", cap)
        object.__setattr__(self, "log_overflow_mass", log_overflow)
        object.__setattr__(self, "_overflow_mass", overflow_mass)
        object.__setattr__(self, "_base", base)

    @property
    def overflow_mass(self) -> float:
        """Return the float64 overflow mass when it is representable."""

        if self._overflow_mass == 0.0:
            raise ArithmeticError(
                "overflow mass underflows in ordinary space; use log_overflow_mass"
            )
        return self._overflow_mass

    @property
    def retained_mass(self) -> float:
        return -math.expm1(self.log_overflow_mass)

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "collapsed-unit-poisson-observation-reference-v1",
            tuple(
                (
                    type_id,
                    self.type_dimensions[type_id],
                    self.type_weights[type_id],
                )
                for type_id in self.type_ids
            ),
            self.retained_cap,
        )

    def canonicalize_retained(
        self, observation: Iterable[TransformedEvent]
    ) -> TransformedConfiguration:
        if observation is OVERFLOW_OBSERVATION:
            raise TypeError("overflow is not a retained configuration")
        return self._base.canonicalize(observation)

    def collapse(self, observation: object) -> AssociationObservationValue:
        """Validate a raw configuration and collapse cardinality above the cap."""

        if observation is OVERFLOW_OBSERVATION:
            return OVERFLOW_OBSERVATION
        if isinstance(observation, OverflowObservation):
            raise ValueError("unknown overflow observation value")
        events = _bounded_tuple(
            observation,
            name="observation",
            maximum_items=MAX_ASSOCIATION_OCCURRENCES,
        )
        for event in events:
            self._base._validate_event(event)
        if len(events) > self.retained_cap:
            return OVERFLOW_OBSERVATION
        return tuple(sorted(events, key=TransformedEvent.model_key))

    def log_one_event_density(self, event: TransformedEvent) -> float:
        return self._base.log_one_event_density(event)

    def log_retained_lebesgue_poisson_density(
        self, observation: Iterable[TransformedEvent]
    ) -> float:
        configuration = self.canonicalize_retained(observation)
        try:
            event_sum = math.fsum(
                self.log_one_event_density(event) for event in configuration
            )
        except OverflowError as error:
            raise ArithmeticError(
                "observation-reference log density is not representable"
            ) from error
        result = -1.0 + event_sum
        if not math.isfinite(result):
            raise ArithmeticError(
                "observation-reference log density is not representable"
            )
        return result

    def log_point_mass(
        self, observation: Iterable[TransformedEvent]
    ) -> float:
        configuration = self.canonicalize_retained(observation)
        if any(
            self.type_dimensions[event.event_type] != 0
            for event in configuration
        ):
            return -math.inf
        log_mass = -1.0 + math.fsum(
            math.log(self.type_weights[event.event_type])
            for event in configuration
        )
        index = 0
        multiplicity_terms = []
        while index < len(configuration):
            stop = index + 1
            while (
                stop < len(configuration)
                and configuration[stop] == configuration[index]
            ):
                stop += 1
            multiplicity_terms.append(math.lgamma(stop - index + 1.0))
            index = stop
        return log_mass - math.fsum(multiplicity_terms)

    def log_reference_density(self, observation: object) -> float:
        """Return the retained density or the overflow singleton log mass."""

        if observation is OVERFLOW_OBSERVATION:
            return self.log_overflow_mass
        if isinstance(observation, OverflowObservation):
            raise ValueError("unknown overflow observation value")
        return self.log_retained_lebesgue_poisson_density(observation)  # type: ignore[arg-type]


@dataclass(frozen=True, eq=False, init=False)
class RetainedAssociationFactors:
    """Occurrence-level algebraic factors for one retained observation.

    This low-level oracle does not certify a normalized kernel row or bind a
    reference cap.  Use :class:`BoundAssociationObservationRow` for the
    theorem-facing observation law.
    """

    detection_probability: np.ndarray = field(repr=False)
    pair_log_densities: np.ndarray = field(repr=False)
    clutter_log_densities: np.ndarray = field(repr=False)
    clutter_total: float
    _centered_pair_log_densities: np.ndarray = field(repr=False)
    _centered_clutter_log_densities: np.ndarray = field(repr=False)
    _observation_log_offsets: np.ndarray = field(repr=False)
    _centered_log_detection: np.ndarray = field(repr=False)
    _centered_log_miss: np.ndarray = field(repr=False)
    _source_log_offsets: np.ndarray = field(repr=False)

    def __init__(
        self,
        detection_probability: object,
        pair_log_densities: object,
        clutter_log_densities: object,
        clutter_total: object,
    ) -> None:
        detection_shape = _preflight_array(
            detection_probability,
            name="detection_probability",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        )
        clutter_shape = _preflight_array(
            clutter_log_densities,
            name="clutter_log_densities",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        )
        expected_pair_shape = (clutter_shape[0], detection_shape[0])
        if math.prod(expected_pair_shape) > MAX_ASSOCIATION_MATRIX_ENTRIES:
            raise AssociationObservationResourceError(
                "pair_log_densities exceeds the entry limit"
            )
        _preflight_array(
            pair_log_densities,
            name="pair_log_densities",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
            expected_shape=expected_pair_shape,
        )
        detection = _probability_vector(
            detection_probability, name="detection_probability"
        )
        pair_logs = _log_array(
            pair_log_densities,
            name="pair_log_densities",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
        )
        clutter_logs = _log_array(
            clutter_log_densities,
            name="clutter_log_densities",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        )
        total = _validated_real(
            clutter_total, name="clutter_total", nonnegative=True
        )
        if total > MAX_ASSOCIATION_CLUTTER_MEAN:
            raise AssociationObservationResourceError(
                "clutter_total exceeds the implementation limit of %g"
                % MAX_ASSOCIATION_CLUTTER_MEAN
            )
        centered_pairs = np.array(pair_logs, dtype=np.float64, copy=True)
        centered_clutter = np.array(
            clutter_logs, dtype=np.float64, copy=True
        )
        centered_pairs[:, detection == 0.0] = -math.inf
        offsets = np.zeros(clutter_logs.size, dtype=np.float64)
        for observation_index in range(clutter_logs.size):
            candidates = [
                float(centered_pairs[observation_index, source_index])
                for source_index in range(detection.size)
                if detection[source_index] > 0.0
                and centered_pairs[observation_index, source_index]
                != -math.inf
            ]
            clutter_value = float(clutter_logs[observation_index])
            if clutter_value != -math.inf:
                candidates.append(clutter_value)
            if not candidates:
                continue
            offset = max(candidates)
            offsets[observation_index] = offset
            finite_pairs = np.isfinite(centered_pairs[observation_index])
            try:
                with np.errstate(over="raise", invalid="raise"):
                    centered_pairs[observation_index, finite_pairs] -= offset
                    if centered_clutter[observation_index] != -math.inf:
                        centered_clutter[observation_index] -= offset
            except FloatingPointError as error:
                raise ArithmeticError(
                    "association observation-row log span is not representable"
                ) from error
        log_detection = np.full(detection.size, -math.inf, dtype=np.float64)
        log_miss = np.full(detection.size, -math.inf, dtype=np.float64)
        positive_detection = detection > 0.0
        possible_miss = detection < 1.0
        log_detection[positive_detection] = np.log(
            detection[positive_detection]
        )
        log_miss[possible_miss] = np.log1p(-detection[possible_miss])
        source_offsets = np.zeros(detection.size, dtype=np.float64)
        centered_detection = np.array(log_detection, copy=True)
        centered_miss = np.array(log_miss, copy=True)
        for source_index in range(detection.size):
            offset = float(log_miss[source_index])
            if offset == -math.inf:
                offset = float(log_detection[source_index])
            source_offsets[source_index] = offset
            if centered_detection[source_index] != -math.inf:
                centered_detection[source_index] -= offset
            if centered_miss[source_index] != -math.inf:
                centered_miss[source_index] -= offset
        object.__setattr__(
            self, "detection_probability", _immutable_float_array(detection)
        )
        object.__setattr__(
            self, "pair_log_densities", _immutable_float_array(pair_logs)
        )
        object.__setattr__(
            self, "clutter_log_densities", _immutable_float_array(clutter_logs)
        )
        object.__setattr__(self, "clutter_total", total)
        object.__setattr__(
            self,
            "_centered_pair_log_densities",
            _immutable_float_array(centered_pairs),
        )
        object.__setattr__(
            self,
            "_centered_clutter_log_densities",
            _immutable_float_array(centered_clutter),
        )
        object.__setattr__(
            self, "_observation_log_offsets", _immutable_float_array(offsets)
        )
        object.__setattr__(
            self,
            "_centered_log_detection",
            _immutable_float_array(centered_detection),
        )
        object.__setattr__(
            self, "_centered_log_miss", _immutable_float_array(centered_miss)
        )
        object.__setattr__(
            self, "_source_log_offsets", _immutable_float_array(source_offsets)
        )

    @classmethod
    def from_densities(
        cls,
        detection_probability: object,
        pair_densities: object,
        clutter_densities: object,
        clutter_total: object,
    ) -> "RetainedAssociationFactors":
        detection_shape = _preflight_array(
            detection_probability,
            name="detection_probability",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        )
        clutter_shape = _preflight_array(
            clutter_densities,
            name="clutter_densities",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        )
        expected_pair_shape = (clutter_shape[0], detection_shape[0])
        if math.prod(expected_pair_shape) > MAX_ASSOCIATION_MATRIX_ENTRIES:
            raise AssociationObservationResourceError(
                "pair_densities exceeds the entry limit"
            )
        _preflight_array(
            pair_densities,
            name="pair_densities",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
            expected_shape=expected_pair_shape,
        )
        pairs = _numeric_array(
            pair_densities,
            name="pair_densities",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
        )
        clutter = _numeric_array(
            clutter_densities,
            name="clutter_densities",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        )
        pair_logs = _nonnegative_to_log(pairs, name="pair_densities")
        clutter_logs = _nonnegative_to_log(clutter, name="clutter_densities")
        return cls(
            detection_probability,
            pair_logs,
            clutter_logs,
            clutter_total,
        )

    @property
    def latent_occurrence_count(self) -> int:
        return int(self.detection_probability.size)

    @property
    def observation_occurrence_count(self) -> int:
        return int(self.clutter_log_densities.size)


@dataclass(frozen=True, eq=False)
class _AssociationDPFactors:
    log_detection: np.ndarray = field(repr=False)
    log_miss: np.ndarray = field(repr=False)
    pair_log_densities: np.ndarray = field(repr=False)
    clutter_log_densities: np.ndarray = field(repr=False)

    @property
    def latent_occurrence_count(self) -> int:
        return int(self.log_detection.size)

    @property
    def observation_occurrence_count(self) -> int:
        return int(self.clutter_log_densities.size)


def _centered_dp_factors(
    factors: RetainedAssociationFactors,
) -> _AssociationDPFactors:
    return _AssociationDPFactors(
        factors._centered_log_detection,
        factors._centered_log_miss,
        factors._centered_pair_log_densities,
        factors._centered_clutter_log_densities,
    )


def _association_dp_resources(latent_count: int, observation_count: int) -> None:
    subset_bits = min(latent_count, observation_count)
    if subset_bits > MAX_ASSOCIATION_SUBSET_BITS:
        raise AssociationObservationResourceError(
            "exact association requires %d subset bits, above the limit of %d"
            % (subset_bits, MAX_ASSOCIATION_SUBSET_BITS)
        )
    subset_states = 1 << subset_bits
    if latent_count == 0 or observation_count == 0:
        work = latent_count + observation_count + 1
    else:
        work = latent_count * observation_count * subset_states
    if work > MAX_ASSOCIATION_DP_WORK:
        raise AssociationObservationResourceError(
            "exact association exceeds the work limit of %d"
            % MAX_ASSOCIATION_DP_WORK
        )


def _association_marginal_resources(
    latent_count: int, observation_count: int
) -> None:
    if latent_count == 0 or observation_count == 0:
        return
    reduced_bits = min(latent_count - 1, observation_count - 1)
    reduced_states = 1 << reduced_bits
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
    if edge_work + forced_unmatched_work > MAX_ASSOCIATION_DP_WORK:
        raise AssociationObservationResourceError(
            "association-marginal calculation exceeds the work limit of %d"
            % MAX_ASSOCIATION_DP_WORK
        )


def _labelled_source_subset_log_partition(
    factors: _AssociationDPFactors,
) -> float:
    latent_count = factors.latent_occurrence_count
    observation_count = factors.observation_occurrence_count
    state_count = 1 << latent_count
    dynamic = np.full(state_count, -math.inf, dtype=np.float64)
    dynamic[0] = 0.0
    log_detection = factors.log_detection
    for observation_index in range(observation_count):
        updated = np.full(state_count, -math.inf, dtype=np.float64)
        clutter_log = float(factors.clutter_log_densities[observation_index])
        for mask in range(state_count):
            prefix = float(dynamic[mask])
            if prefix == -math.inf:
                continue
            if clutter_log != -math.inf:
                updated[mask] = _logaddexp(
                    float(updated[mask]), prefix + clutter_log
                )
            for latent_index in range(latent_count):
                bit = 1 << latent_index
                if mask & bit:
                    continue
                pair_log = float(
                    factors.pair_log_densities[
                        observation_index, latent_index
                    ]
                )
                if log_detection[latent_index] == -math.inf or pair_log == -math.inf:
                    continue
                target = mask | bit
                updated[target] = _logaddexp(
                    float(updated[target]),
                    prefix + log_detection[latent_index] + pair_log,
                )
        dynamic = updated

    terms = []
    for mask in range(state_count):
        prefix = float(dynamic[mask])
        if prefix == -math.inf:
            continue
        misses = []
        possible = True
        for latent_index in range(latent_count):
            if mask & (1 << latent_index):
                continue
            miss_log = float(factors.log_miss[latent_index])
            if miss_log == -math.inf:
                possible = False
                break
            misses.append(miss_log)
        if possible:
            terms.append(prefix + math.fsum(misses))
    return _logsumexp(terms)


def _labelled_observation_subset_log_partition(
    factors: _AssociationDPFactors,
) -> float:
    latent_count = factors.latent_occurrence_count
    observation_count = factors.observation_occurrence_count
    state_count = 1 << observation_count
    dynamic = np.full(state_count, -math.inf, dtype=np.float64)
    dynamic[0] = 0.0
    for latent_index in range(latent_count):
        updated = np.full(state_count, -math.inf, dtype=np.float64)
        log_detection = float(factors.log_detection[latent_index])
        log_miss = float(factors.log_miss[latent_index])
        for mask in range(state_count):
            prefix = float(dynamic[mask])
            if prefix == -math.inf:
                continue
            if log_miss != -math.inf:
                updated[mask] = _logaddexp(
                    float(updated[mask]), prefix + log_miss
                )
            if log_detection == -math.inf:
                continue
            for observation_index in range(observation_count):
                bit = 1 << observation_index
                if mask & bit:
                    continue
                pair_log = float(
                    factors.pair_log_densities[
                        observation_index, latent_index
                    ]
                )
                if pair_log == -math.inf:
                    continue
                target = mask | bit
                updated[target] = _logaddexp(
                    float(updated[target]),
                    prefix + log_detection + pair_log,
                )
        dynamic = updated

    terms = []
    for mask in range(state_count):
        prefix = float(dynamic[mask])
        if prefix == -math.inf:
            continue
        clutter = []
        possible = True
        for observation_index in range(observation_count):
            if mask & (1 << observation_index):
                continue
            clutter_log = float(
                factors.clutter_log_densities[observation_index]
            )
            if clutter_log == -math.inf:
                possible = False
                break
            clutter.append(clutter_log)
        if possible:
            terms.append(prefix + math.fsum(clutter))
    return _logsumexp(terms)


def _association_dp_log_partition(
    factors: _AssociationDPFactors,
) -> float:
    latent_count = factors.latent_occurrence_count
    observation_count = factors.observation_occurrence_count
    _association_dp_resources(latent_count, observation_count)
    if latent_count <= observation_count:
        return _labelled_source_subset_log_partition(factors)
    return _labelled_observation_subset_log_partition(factors)


def _labelled_association_log_partition(
    factors: RetainedAssociationFactors,
) -> float:
    return _association_dp_log_partition(_centered_dp_factors(factors))


def labelled_association_log_density(
    factors: RetainedAssociationFactors,
) -> float:
    """Return the exact retained clean log density under the PPP reference."""

    if type(factors) is not RetainedAssociationFactors:
        raise TypeError("factors must be an exact RetainedAssociationFactors")
    partition_log = _labelled_association_log_partition(factors)
    if partition_log == -math.inf:
        return -math.inf
    try:
        terms = [1.0, -factors.clutter_total, partition_log]
        terms.extend(float(value) for value in factors._source_log_offsets)
        terms.extend(
            float(value) for value in factors._observation_log_offsets
        )
        result = _high_range_fsum(
            terms, name="labelled association log density"
        )
    except (OverflowError, ValueError) as error:
        raise ArithmeticError(
            "labelled association log density is not representable"
        ) from error
    if not math.isfinite(result):
        raise ArithmeticError(
            "labelled association log density is not representable"
        )
    return 0.0 if result == 0.0 else result


def labelled_association_density(
    factors: RetainedAssociationFactors,
) -> float:
    return _ordinary_from_log(
        labelled_association_log_density(factors),
        name="labelled clean association density",
    )


def positive_association_log_density(
    clean_log_density: object,
    contamination_probability: object,
) -> float:
    """Return ``log((1-epsilon) g_clean + epsilon)`` exactly in log space."""

    if isinstance(clean_log_density, (bool, np.bool_)) or not isinstance(
        clean_log_density, Real
    ):
        raise TypeError("clean_log_density must be a real non-boolean number")
    clean = float(clean_log_density)
    if math.isnan(clean) or clean == math.inf:
        raise ValueError("clean_log_density must be finite or -inf")
    epsilon = _validated_contamination_probability(contamination_probability)
    if epsilon == 0.0:
        return clean
    clean_branch = (
        -math.inf
        if clean == -math.inf
        else math.log1p(-epsilon) + clean
    )
    return _logaddexp(clean_branch, math.log(epsilon))


@dataclass(frozen=True, init=False)
class AssociationDensityEvaluation:
    """Checked clean and optional positive-mixture density for one outcome."""

    clean_log_density: float
    contamination_probability: float
    log_density: float
    algorithm: str
    latent_occurrence_count: int
    observation_occurrence_count: int
    association_class_count: Optional[int]

    def __init__(
        self,
        *,
        clean_log_density: float,
        contamination_probability: object,
        algorithm: str,
        latent_occurrence_count: int,
        observation_occurrence_count: int,
        association_class_count: Optional[int] = None,
    ) -> None:
        if clean_log_density != -math.inf and not math.isfinite(clean_log_density):
            raise ValueError("clean_log_density must be finite or -inf")
        epsilon = _validated_contamination_probability(contamination_probability)
        if not isinstance(algorithm, str) or not algorithm:
            raise ValueError("algorithm must be a nonempty string")
        latent_count = _validated_integer(
            latent_occurrence_count,
            name="latent_occurrence_count",
            minimum=0,
            maximum=MAX_ASSOCIATION_OCCURRENCES,
        )
        observation_count = _validated_integer(
            observation_occurrence_count,
            name="observation_occurrence_count",
            minimum=0,
            maximum=MAX_ASSOCIATION_OCCURRENCES,
        )
        if association_class_count is not None:
            class_count = _validated_integer(
                association_class_count,
                name="association_class_count",
                minimum=0,
                maximum=MAX_ASSOCIATION_ORBIT_CLASSES,
            )
        else:
            class_count = None
        log_density = positive_association_log_density(
            clean_log_density, epsilon
        )
        object.__setattr__(self, "clean_log_density", clean_log_density)
        object.__setattr__(self, "contamination_probability", epsilon)
        object.__setattr__(self, "log_density", log_density)
        object.__setattr__(self, "algorithm", algorithm)
        object.__setattr__(self, "latent_occurrence_count", latent_count)
        object.__setattr__(self, "observation_occurrence_count", observation_count)
        object.__setattr__(self, "association_class_count", class_count)

    @property
    def clean_is_structural_zero(self) -> bool:
        """Whether the clean model assigns exactly zero density."""

        return self.clean_log_density == -math.inf

    @property
    def clean_density(self) -> float:
        """Materialize the clean density, raising on float64 overflow."""

        return _ordinary_from_log(
            self.clean_log_density, name="clean association density"
        )

    @property
    def density(self) -> float:
        """Materialize the final density, raising on float64 overflow."""

        epsilon = self.contamination_probability
        if self.clean_is_structural_zero and epsilon > 0.0:
            return epsilon
        result = _ordinary_from_log(
            self.log_density, name="association density"
        )
        if epsilon > 0.0 and result < epsilon:
            if not math.isclose(
                result,
                epsilon,
                rel_tol=8.0 * _FLOAT64_EPSILON,
                abs_tol=0.0,
            ):
                raise ArithmeticError("positive association bound was violated")
            return epsilon
        return result


def evaluate_retained_association(
    factors: RetainedAssociationFactors,
    *,
    contamination_probability: object = 0.0,
) -> AssociationDensityEvaluation:
    """Evaluate unbound algebraic factors; this is not a row certificate."""

    if type(factors) is not RetainedAssociationFactors:
        raise TypeError("factors must be an exact RetainedAssociationFactors")
    clean_log_density = labelled_association_log_density(factors)
    algorithm = (
        "labelled-source-subset"
        if factors.latent_occurrence_count
        <= factors.observation_occurrence_count
        else "labelled-observation-subset"
    )
    return AssociationDensityEvaluation(
        clean_log_density=clean_log_density,
        contamination_probability=contamination_probability,
        algorithm=algorithm,
        latent_occurrence_count=factors.latent_occurrence_count,
        observation_occurrence_count=factors.observation_occurrence_count,
    )


def detection_poisson_overflow_log_probability(
    detection_probability: object,
    clutter_total: object,
    retained_cap: object,
) -> float:
    """Return ``log P(sum Bernoulli(p_i) + Poisson(K) > M)``."""

    cap = _validated_integer(
        retained_cap,
        name="retained_cap",
        minimum=0,
        maximum=MAX_ASSOCIATION_OBSERVATION_CAP,
    )
    detection_shape = _preflight_array(
        detection_probability,
        name="detection_probability",
        ndim=1,
        maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
    )
    total = _validated_real(
        clutter_total, name="clutter_total", nonnegative=True
    )
    if total > MAX_ASSOCIATION_CLUTTER_MEAN:
        raise AssociationObservationResourceError(
            "clutter_total exceeds the implementation limit of %g"
            % MAX_ASSOCIATION_CLUTTER_MEAN
        )
    work = detection_shape[0] * (cap + 1)
    if work > MAX_ASSOCIATION_DP_WORK:
        raise AssociationObservationResourceError(
            "overflow recursion exceeds the work limit of %d"
            % MAX_ASSOCIATION_DP_WORK
        )
    detection = _probability_vector(
        detection_probability, name="detection_probability"
    )

    log_mass = np.full(cap + 1, -math.inf, dtype=np.float64)
    log_mass[0] = 0.0
    log_detection_overflow = -math.inf
    for raw_probability in detection:
        probability = float(raw_probability)
        log_detect = _log_nonnegative(probability)
        log_miss = (
            -math.inf if probability == 1.0 else math.log1p(-probability)
        )
        updated = np.full(cap + 1, -math.inf, dtype=np.float64)
        for count in range(cap + 1):
            if log_miss != -math.inf and float(log_mass[count]) != -math.inf:
                updated[count] = _logaddexp(
                    float(updated[count]), float(log_mass[count]) + log_miss
                )
            if (
                count > 0
                and log_detect != -math.inf
                and float(log_mass[count - 1]) != -math.inf
            ):
                updated[count] = _logaddexp(
                    float(updated[count]),
                    float(log_mass[count - 1]) + log_detect,
                )
        crossing = (
            -math.inf
            if log_detect == -math.inf or float(log_mass[cap]) == -math.inf
            else float(log_mass[cap]) + log_detect
        )
        log_detection_overflow = _logaddexp(
            log_detection_overflow, crossing
        )
        log_mass = updated

    terms = [log_detection_overflow]
    for count in range(cap + 1):
        detection_log_mass = float(log_mass[count])
        if detection_log_mass == -math.inf:
            continue
        poisson_tail = _log_poisson_tail_above(cap - count, total)
        if poisson_tail != -math.inf:
            terms.append(detection_log_mass + poisson_tail)
    result = _logsumexp(terms)
    if result > 0.0:
        if result > ASSOCIATION_NORMALIZATION_ATOL:
            raise ArithmeticError(
                "detection-plus-clutter overflow probability exceeds one"
            )
        return 0.0
    return result


def detection_poisson_overflow_probability(
    detection_probability: object,
    clutter_total: object,
    retained_cap: object,
) -> float:
    return _ordinary_from_log(
        detection_poisson_overflow_log_probability(
            detection_probability, clutter_total, retained_cap
        ),
        name="detection-plus-clutter overflow probability",
    )


def evaluate_overflow_association(
    reference: CollapsedPoissonObservationReference,
    detection_probability: object,
    clutter_total: object,
    *,
    contamination_probability: object = 0.0,
) -> AssociationDensityEvaluation:
    """Evaluate unbound overflow factors; this is not a row certificate."""

    if type(reference) is not CollapsedPoissonObservationReference:
        raise TypeError(
            "reference must be an exact CollapsedPoissonObservationReference"
        )
    detection_shape = _preflight_array(
        detection_probability,
        name="detection_probability",
        ndim=1,
        maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
    )
    log_probability = detection_poisson_overflow_log_probability(
        detection_probability, clutter_total, reference.retained_cap
    )
    clean_log_density = (
        -math.inf
        if log_probability == -math.inf
        else log_probability - reference.log_overflow_mass
    )
    return AssociationDensityEvaluation(
        clean_log_density=clean_log_density,
        contamination_probability=contamination_probability,
        algorithm="poisson-binomial-overflow",
        latent_occurrence_count=detection_shape[0],
        observation_occurrence_count=0,
    )


@dataclass(frozen=True, eq=False, init=False)
class AssociationEdgeMarginals:
    """Clean log density and posterior probability of every labelled match."""

    log_density: float
    edge_log_marginals: np.ndarray = field(repr=False)
    clutter_log_marginals: np.ndarray = field(repr=False)
    miss_log_marginals: np.ndarray = field(repr=False)
    edge_marginals: np.ndarray = field(repr=False)
    clutter_marginals: np.ndarray = field(repr=False)
    miss_marginals: np.ndarray = field(repr=False)

    def __init__(
        self,
        log_density: float,
        edge_log_marginals: object,
        clutter_log_marginals: object,
        miss_log_marginals: object,
    ) -> None:
        if not math.isfinite(log_density):
            raise ValueError("log_density must be finite for edge marginals")
        clutter_shape = _preflight_array(
            clutter_log_marginals,
            name="clutter_log_marginals",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        )
        miss_shape = _preflight_array(
            miss_log_marginals,
            name="miss_log_marginals",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        )
        expected_edge_shape = (clutter_shape[0], miss_shape[0])
        if math.prod(expected_edge_shape) > MAX_ASSOCIATION_MATRIX_ENTRIES:
            raise AssociationObservationResourceError(
                "edge_log_marginals exceeds the entry limit"
            )
        _preflight_array(
            edge_log_marginals,
            name="edge_log_marginals",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
            expected_shape=expected_edge_shape,
        )
        edge_logs = _log_array(
            edge_log_marginals,
            name="edge_log_marginals",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
        )
        clutter_logs = _log_array(
            clutter_log_marginals,
            name="clutter_log_marginals",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        )
        miss_logs = _log_array(
            miss_log_marginals,
            name="miss_log_marginals",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        )
        for name, values in (
            ("edge", edge_logs),
            ("clutter", clutter_logs),
            ("miss", miss_logs),
        ):
            if np.any(values > ASSOCIATION_NORMALIZATION_ATOL):
                raise ArithmeticError("%s log marginal exceeds zero" % name)
            values[values > 0.0] = 0.0
        for row_index in range(edge_logs.shape[0]):
            row_log_total = _logsumexp(
                tuple(float(value) for value in edge_logs[row_index])
                + (float(clutter_logs[row_index]),)
            )
            if not math.isclose(
                row_log_total,
                0.0,
                rel_tol=0.0,
                abs_tol=ASSOCIATION_NORMALIZATION_ATOL,
            ):
                raise ArithmeticError("observation marginals do not normalize")
        for column_index in range(edge_logs.shape[1]):
            column_log_total = _logsumexp(
                tuple(float(value) for value in edge_logs[:, column_index])
                + (float(miss_logs[column_index]),)
            )
            if not math.isclose(
                column_log_total,
                0.0,
                rel_tol=0.0,
                abs_tol=ASSOCIATION_NORMALIZATION_ATOL,
            ):
                raise ArithmeticError("latent marginals do not normalize")
        edge = np.exp(edge_logs)
        clutter = np.exp(clutter_logs)
        misses = np.exp(miss_logs)
        object.__setattr__(self, "log_density", log_density)
        object.__setattr__(
            self, "edge_log_marginals", _immutable_float_array(edge_logs)
        )
        object.__setattr__(
            self, "clutter_log_marginals", _immutable_float_array(clutter_logs)
        )
        object.__setattr__(
            self, "miss_log_marginals", _immutable_float_array(miss_logs)
        )
        object.__setattr__(
            self, "edge_marginals", _immutable_float_array(edge)
        )
        object.__setattr__(
            self, "clutter_marginals", _immutable_float_array(clutter)
        )
        object.__setattr__(self, "miss_marginals", _immutable_float_array(misses))


def labelled_association_edge_marginals(
    factors: RetainedAssociationFactors,
) -> AssociationEdgeMarginals:
    """Return exact match-edge derivatives of the labelled log density.

    Entry ``(j, i)`` is ``d log g / d log q_ji`` and therefore the posterior
    probability that observation occurrence ``j`` is matched to latent
    occurrence ``i``.  The calculation is an exact leave-one-edge oracle and
    is deliberately refused above its own work limit.
    """

    if type(factors) is not RetainedAssociationFactors:
        raise TypeError("factors must be an exact RetainedAssociationFactors")
    latent_count = factors.latent_occurrence_count
    observation_count = factors.observation_occurrence_count
    _association_dp_resources(latent_count, observation_count)
    _association_marginal_resources(latent_count, observation_count)
    full_partition_log = _labelled_association_log_partition(factors)
    if full_partition_log == -math.inf:
        raise ValueError("edge marginals are undefined for a zero-density row")
    full_log_density = labelled_association_log_density(factors)
    centered = _centered_dp_factors(factors)
    if latent_count == 0 or observation_count == 0:
        return AssociationEdgeMarginals(
            full_log_density,
            np.empty((observation_count, latent_count), dtype=np.float64),
            np.zeros(observation_count, dtype=np.float64),
            np.zeros(latent_count, dtype=np.float64),
        )
    log_marginals = np.full(
        (observation_count, latent_count), -math.inf, dtype=np.float64
    )
    for observation_index in range(observation_count):
        retained_observations = [
            index
            for index in range(observation_count)
            if index != observation_index
        ]
        for latent_index in range(latent_count):
            pair_log = float(
                centered.pair_log_densities[observation_index, latent_index]
            )
            detection_log = float(centered.log_detection[latent_index])
            if detection_log == -math.inf or pair_log == -math.inf:
                continue
            retained_latents = [
                index for index in range(latent_count) if index != latent_index
            ]
            reduced = _AssociationDPFactors(
                centered.log_detection[retained_latents],
                centered.log_miss[retained_latents],
                centered.pair_log_densities[
                    np.ix_(retained_observations, retained_latents)
                ],
                centered.clutter_log_densities[retained_observations],
            )
            reduced_partition_log = _association_dp_log_partition(reduced)
            numerator_log = (
                detection_log
                + pair_log
                + reduced_partition_log
            )
            log_marginal = numerator_log - full_partition_log
            if log_marginal > 0.0:
                if log_marginal > ASSOCIATION_NORMALIZATION_ATOL:
                    raise ArithmeticError("association edge marginal exceeds one")
                log_marginal = 0.0
            log_marginals[observation_index, latent_index] = log_marginal

    clutter_log_marginals = np.full(
        observation_count, -math.inf, dtype=np.float64
    )
    for observation_index in range(observation_count):
        clutter_log = float(
            centered.clutter_log_densities[observation_index]
        )
        if clutter_log == -math.inf:
            continue
        retained_observations = [
            index
            for index in range(observation_count)
            if index != observation_index
        ]
        reduced = _AssociationDPFactors(
            centered.log_detection,
            centered.log_miss,
            centered.pair_log_densities[retained_observations, :],
            centered.clutter_log_densities[retained_observations],
        )
        clutter_log_marginals[observation_index] = (
            clutter_log
            + _association_dp_log_partition(reduced)
            - full_partition_log
        )

    miss_log_marginals = np.full(latent_count, -math.inf, dtype=np.float64)
    for latent_index in range(latent_count):
        miss_log = float(centered.log_miss[latent_index])
        if miss_log == -math.inf:
            continue
        retained_latents = [
            index for index in range(latent_count) if index != latent_index
        ]
        reduced = _AssociationDPFactors(
            centered.log_detection[retained_latents],
            centered.log_miss[retained_latents],
            centered.pair_log_densities[:, retained_latents],
            centered.clutter_log_densities,
        )
        miss_log_marginals[latent_index] = (
            miss_log
            + _association_dp_log_partition(reduced)
            - full_partition_log
        )
    return AssociationEdgeMarginals(
        full_log_density,
        log_marginals,
        clutter_log_marginals,
        miss_log_marginals,
    )


def _multiplicity_tuple(value: object, *, name: str) -> Tuple[int, ...]:
    raw = _bounded_tuple(
        value,
        name=name,
        maximum_items=MAX_ASSOCIATION_DISTINCT_ATOMS,
    )
    return tuple(
        _validated_integer(
            item,
            name="%s entry" % name,
            minimum=1,
            maximum=MAX_ASSOCIATION_ORBIT_OCCURRENCES,
        )
        for item in raw
    )


@dataclass(frozen=True, init=False)
class AssociationOrbit:
    """One duplicate-quotient association matrix and its exact coefficient."""

    observation_multiplicities: Tuple[int, ...]
    latent_multiplicities: Tuple[int, ...]
    match_counts: Tuple[Tuple[int, ...], ...]
    clutter_counts: Tuple[int, ...]
    detected_counts: Tuple[int, ...]
    coefficient: int

    def __init__(
        self,
        observation_multiplicities: object,
        latent_multiplicities: object,
        match_counts: object,
    ) -> None:
        observation = _multiplicity_tuple(
            observation_multiplicities,
            name="observation_multiplicities",
        )
        latent = _multiplicity_tuple(
            latent_multiplicities,
            name="latent_multiplicities",
        )
        if sum(observation) > MAX_ASSOCIATION_ORBIT_OCCURRENCES:
            raise AssociationObservationResourceError(
                "observation multiplicity exceeds the orbit-occurrence limit"
            )
        if sum(latent) > MAX_ASSOCIATION_ORBIT_OCCURRENCES:
            raise AssociationObservationResourceError(
                "latent multiplicity exceeds the orbit-occurrence limit"
            )
        raw_rows = _bounded_tuple(
            match_counts,
            name="match_counts rows",
            maximum_items=MAX_ASSOCIATION_DISTINCT_ATOMS,
        )
        if len(raw_rows) != len(observation):
            raise ValueError(
                "match_counts must have one row per distinct observation atom"
            )
        rows = []
        for row in raw_rows:
            raw_row = _bounded_tuple(
                row,
                name="match_counts row",
                maximum_items=MAX_ASSOCIATION_DISTINCT_ATOMS,
            )
            if len(raw_row) != len(latent):
                raise ValueError(
                    "match_counts must have one column per distinct latent atom"
                )
            rows.append(
                tuple(
                    _validated_integer(
                        item,
                        name="match count",
                        minimum=0,
                        maximum=MAX_ASSOCIATION_ORBIT_OCCURRENCES,
                    )
                    for item in raw_row
                )
            )
        matrix = tuple(rows)
        row_sums = tuple(sum(row) for row in matrix)
        detected = tuple(
            sum(matrix[row][column] for row in range(len(observation)))
            for column in range(len(latent))
        )
        if any(total > multiplicity for total, multiplicity in zip(row_sums, observation)):
            raise ValueError("a match-count row exceeds observation multiplicity")
        if any(total > multiplicity for total, multiplicity in zip(detected, latent)):
            raise ValueError("a match-count column exceeds latent multiplicity")
        clutter = tuple(
            multiplicity - total
            for multiplicity, total in zip(observation, row_sums)
        )
        numerator = math.prod(math.factorial(value) for value in observation)
        numerator *= math.prod(math.factorial(value) for value in latent)
        denominator = math.prod(math.factorial(value) for value in clutter)
        denominator *= math.prod(
            math.factorial(multiplicity - total)
            for multiplicity, total in zip(latent, detected)
        )
        denominator *= math.prod(
            math.factorial(value) for row in matrix for value in row
        )
        coefficient, remainder = divmod(numerator, denominator)
        if remainder != 0 or coefficient <= 0:
            raise ArithmeticError("association orbit coefficient is not integral")
        object.__setattr__(self, "observation_multiplicities", observation)
        object.__setattr__(self, "latent_multiplicities", latent)
        object.__setattr__(self, "match_counts", matrix)
        object.__setattr__(self, "clutter_counts", clutter)
        object.__setattr__(self, "detected_counts", detected)
        object.__setattr__(self, "coefficient", coefficient)


def association_orbit_coefficient(
    observation_multiplicities: object,
    latent_multiplicities: object,
    match_counts: object,
) -> int:
    return AssociationOrbit(
        observation_multiplicities,
        latent_multiplicities,
        match_counts,
    ).coefficient


@dataclass(frozen=True, eq=False, init=False)
class QuotientAssociationFactors:
    """Unbound distinct-atom factors for the duplicate-orbit algebraic oracle."""

    observation_multiplicities: Tuple[int, ...]
    latent_multiplicities: Tuple[int, ...]
    detection_probability: np.ndarray = field(repr=False)
    pair_log_densities: np.ndarray = field(repr=False)
    clutter_log_densities: np.ndarray = field(repr=False)
    clutter_total: float

    def __init__(
        self,
        observation_multiplicities: object,
        latent_multiplicities: object,
        detection_probability: object,
        pair_log_densities: object,
        clutter_log_densities: object,
        clutter_total: object,
    ) -> None:
        observation = _multiplicity_tuple(
            observation_multiplicities,
            name="observation_multiplicities",
        )
        latent = _multiplicity_tuple(
            latent_multiplicities,
            name="latent_multiplicities",
        )
        if sum(observation) > MAX_ASSOCIATION_ORBIT_OCCURRENCES:
            raise AssociationObservationResourceError(
                "observation multiplicity exceeds the orbit-occurrence limit"
            )
        if sum(latent) > MAX_ASSOCIATION_ORBIT_OCCURRENCES:
            raise AssociationObservationResourceError(
                "latent multiplicity exceeds the orbit-occurrence limit"
            )
        expected_pair_shape = (len(observation), len(latent))
        _preflight_array(
            detection_probability,
            name="detection_probability",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_DISTINCT_ATOMS,
            expected_shape=(len(latent),),
        )
        _preflight_array(
            clutter_log_densities,
            name="clutter_log_densities",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_DISTINCT_ATOMS,
            expected_shape=(len(observation),),
        )
        _preflight_array(
            pair_log_densities,
            name="pair_log_densities",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
            expected_shape=expected_pair_shape,
        )
        detection = _probability_vector(
            detection_probability, name="detection_probability"
        )
        pair_logs = _log_array(
            pair_log_densities,
            name="pair_log_densities",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
        )
        clutter_logs = _log_array(
            clutter_log_densities,
            name="clutter_log_densities",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_DISTINCT_ATOMS,
        )
        total = _validated_real(
            clutter_total, name="clutter_total", nonnegative=True
        )
        if total > MAX_ASSOCIATION_CLUTTER_MEAN:
            raise AssociationObservationResourceError(
                "clutter_total exceeds the implementation limit of %g"
                % MAX_ASSOCIATION_CLUTTER_MEAN
            )
        object.__setattr__(self, "observation_multiplicities", observation)
        object.__setattr__(self, "latent_multiplicities", latent)
        object.__setattr__(
            self, "detection_probability", _immutable_float_array(detection)
        )
        object.__setattr__(
            self, "pair_log_densities", _immutable_float_array(pair_logs)
        )
        object.__setattr__(
            self, "clutter_log_densities", _immutable_float_array(clutter_logs)
        )
        object.__setattr__(self, "clutter_total", total)

    @classmethod
    def from_densities(
        cls,
        observation_multiplicities: object,
        latent_multiplicities: object,
        detection_probability: object,
        pair_densities: object,
        clutter_densities: object,
        clutter_total: object,
    ) -> "QuotientAssociationFactors":
        observation = _multiplicity_tuple(
            observation_multiplicities,
            name="observation_multiplicities",
        )
        latent = _multiplicity_tuple(
            latent_multiplicities,
            name="latent_multiplicities",
        )
        if sum(observation) > MAX_ASSOCIATION_ORBIT_OCCURRENCES:
            raise AssociationObservationResourceError(
                "observation multiplicity exceeds the orbit-occurrence limit"
            )
        if sum(latent) > MAX_ASSOCIATION_ORBIT_OCCURRENCES:
            raise AssociationObservationResourceError(
                "latent multiplicity exceeds the orbit-occurrence limit"
            )
        _preflight_array(
            detection_probability,
            name="detection_probability",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_DISTINCT_ATOMS,
            expected_shape=(len(latent),),
        )
        _preflight_array(
            clutter_densities,
            name="clutter_densities",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_DISTINCT_ATOMS,
            expected_shape=(len(observation),),
        )
        _preflight_array(
            pair_densities,
            name="pair_densities",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
            expected_shape=(len(observation), len(latent)),
        )
        pairs = _numeric_array(
            pair_densities,
            name="pair_densities",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
        )
        clutter = _numeric_array(
            clutter_densities,
            name="clutter_densities",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_DISTINCT_ATOMS,
        )
        return cls(
            observation,
            latent,
            detection_probability,
            _nonnegative_to_log(pairs, name="pair_densities"),
            _nonnegative_to_log(clutter, name="clutter_densities"),
            clutter_total,
        )


def _row_allocations(
    total: int,
    capacities: Tuple[int, ...],
) -> Iterable[Tuple[int, ...]]:
    allocation = [0] * len(capacities)

    def recurse(column: int, remaining: int) -> Iterable[Tuple[int, ...]]:
        if column == len(capacities):
            yield tuple(allocation)
            return
        maximum = min(remaining, capacities[column])
        for value in range(maximum + 1):
            allocation[column] = value
            yield from recurse(column + 1, remaining - value)

    return recurse(0, total)


def _log_power_terms(log_value: float, exponent: int) -> Tuple[float, ...]:
    if exponent == 0:
        return ()
    if log_value == -math.inf:
        return (-math.inf,)
    return (log_value,) * exponent


def _quotient_association_log_density_and_count(
    factors: QuotientAssociationFactors,
) -> Tuple[float, int]:
    observation = factors.observation_multiplicities
    latent = factors.latent_multiplicities
    matrix_rows = []  # type: ignore[var-annotated]
    class_count = 0
    log_total = -math.inf

    def visit(row_index: int, capacities: Tuple[int, ...]) -> None:
        nonlocal class_count, log_total
        if row_index == len(observation):
            class_count += 1
            if class_count > MAX_ASSOCIATION_ORBIT_CLASSES:
                raise AssociationObservationResourceError(
                    "quotient enumeration exceeds the %d-class limit"
                    % MAX_ASSOCIATION_ORBIT_CLASSES
                )
            orbit = AssociationOrbit(observation, latent, tuple(matrix_rows))
            terms = [
                1.0 - factors.clutter_total,
                math.log(orbit.coefficient),
            ]
            for latent_index, multiplicity in enumerate(latent):
                probability = float(
                    factors.detection_probability[latent_index]
                )
                terms.extend(
                    _log_power_terms(
                        _log_nonnegative(probability),
                        orbit.detected_counts[latent_index],
                    )
                )
                miss_log = (
                    -math.inf
                    if probability == 1.0
                    else math.log1p(-probability)
                )
                terms.extend(
                    _log_power_terms(
                        miss_log,
                        multiplicity - orbit.detected_counts[latent_index],
                    )
                )
            for observation_index, clutter_count in enumerate(
                orbit.clutter_counts
            ):
                terms.extend(
                    _log_power_terms(
                        float(
                            factors.clutter_log_densities[observation_index]
                        ),
                        clutter_count,
                    )
                )
                for latent_index, match_count in enumerate(
                    orbit.match_counts[observation_index]
                ):
                    terms.extend(
                        _log_power_terms(
                            float(
                                factors.pair_log_densities[
                                    observation_index, latent_index
                                ]
                            ),
                            match_count,
                        )
                    )
            log_term = _sum_logs(terms)
            log_total = _logaddexp(log_total, log_term)
            return

        for allocation in _row_allocations(observation[row_index], capacities):
            matrix_rows.append(allocation)
            visit(
                row_index + 1,
                tuple(
                    capacity - used
                    for capacity, used in zip(capacities, allocation)
                ),
            )
            matrix_rows.pop()

    visit(0, latent)
    return log_total, class_count


def quotient_association_log_density(
    factors: QuotientAssociationFactors,
) -> float:
    if type(factors) is not QuotientAssociationFactors:
        raise TypeError("factors must be an exact QuotientAssociationFactors")
    return _quotient_association_log_density_and_count(factors)[0]


def quotient_association_density(
    factors: QuotientAssociationFactors,
) -> float:
    return _ordinary_from_log(
        quotient_association_log_density(factors),
        name="quotient clean association density",
    )


def evaluate_quotient_association(
    factors: QuotientAssociationFactors,
    *,
    contamination_probability: object = 0.0,
) -> AssociationDensityEvaluation:
    """Evaluate unbound quotient factors; this is not a row certificate."""

    if type(factors) is not QuotientAssociationFactors:
        raise TypeError("factors must be an exact QuotientAssociationFactors")
    clean_log_density, class_count = _quotient_association_log_density_and_count(
        factors
    )
    return AssociationDensityEvaluation(
        clean_log_density=clean_log_density,
        contamination_probability=contamination_probability,
        algorithm="duplicate-quotient-orbit",
        latent_occurrence_count=sum(factors.latent_multiplicities),
        observation_occurrence_count=sum(factors.observation_multiplicities),
        association_class_count=class_count,
    )


@dataclass(frozen=True, eq=False, init=False)
class AffineGaussianFiberChannel:
    """Affine Gaussian density relative to a standard-Gaussian output fiber."""

    matrix: np.ndarray = field(repr=False)
    bias: np.ndarray = field(repr=False)
    covariance: np.ndarray = field(repr=False)
    input_dimension: int
    output_dimension: int
    log_determinant: float
    _cholesky: np.ndarray = field(repr=False)

    def __init__(
        self,
        matrix: object,
        bias: object,
        covariance: object,
    ) -> None:
        affine_entry_limit = MAX_AFFINE_OBSERVATION_DIMENSION**2
        linear_shape = _preflight_array(
            matrix,
            name="matrix",
            ndim=2,
            maximum_entries=affine_entry_limit,
        )
        offset_shape = _preflight_array(
            bias,
            name="bias",
            ndim=1,
            maximum_entries=MAX_AFFINE_OBSERVATION_DIMENSION,
        )
        covariance_shape = _preflight_array(
            covariance,
            name="covariance",
            ndim=2,
            maximum_entries=affine_entry_limit,
        )
        output_dimension = offset_shape[0]
        input_dimension = linear_shape[1]
        if output_dimension <= 0:
            raise ValueError(
                "AffineGaussianFiberChannel requires a positive output dimension"
            )
        if linear_shape[0] != output_dimension:
            raise ValueError("matrix rows must match bias length")
        if covariance_shape != (output_dimension, output_dimension):
            raise ValueError("covariance must be square with bias length")
        if input_dimension > MAX_AFFINE_OBSERVATION_DIMENSION:
            raise AssociationObservationResourceError(
                "input dimension exceeds the affine-channel limit"
            )
        work = output_dimension**3 + output_dimension * max(input_dimension, 1)
        if work > MAX_AFFINE_COVARIANCE_WORK:
            raise AssociationObservationResourceError(
                "affine covariance factorization exceeds the work limit"
            )
        linear = _numeric_array(
            matrix,
            name="matrix",
            ndim=2,
            maximum_entries=affine_entry_limit,
        )
        offset = _numeric_array(
            bias,
            name="bias",
            ndim=1,
            maximum_entries=MAX_AFFINE_OBSERVATION_DIMENSION,
        )
        cov = _numeric_array(
            covariance,
            name="covariance",
            ndim=2,
            maximum_entries=affine_entry_limit,
        )
        if not np.array_equal(cov, cov.T):
            raise ValueError("covariance must be symmetric")
        with np.errstate(over="raise", invalid="raise"):
            try:
                cholesky = np.linalg.cholesky(cov)
            except (FloatingPointError, np.linalg.LinAlgError) as error:
                raise ValueError(
                    "covariance must be finite symmetric positive definite"
                ) from error
        log_determinant = 2.0 * math.fsum(
            math.log(float(value)) for value in np.diag(cholesky)
        )
        if not math.isfinite(log_determinant):
            raise ArithmeticError("covariance log determinant is not finite")
        object.__setattr__(self, "matrix", _immutable_float_array(linear))
        object.__setattr__(self, "bias", _immutable_float_array(offset))
        object.__setattr__(self, "covariance", _immutable_float_array(cov))
        object.__setattr__(self, "input_dimension", input_dimension)
        object.__setattr__(self, "output_dimension", output_dimension)
        object.__setattr__(self, "log_determinant", log_determinant)
        object.__setattr__(self, "_cholesky", _immutable_float_array(cholesky))

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "affine-gaussian-fiber-channel-v1",
            tuple(tuple(float(value) for value in row) for row in self.matrix),
            tuple(float(value) for value in self.bias),
            tuple(
                tuple(float(value) for value in row) for row in self.covariance
            ),
        )

    def _coordinates(
        self,
        value: object,
        *,
        name: str,
        expected_dimension: int,
    ) -> np.ndarray:
        coordinates = _numeric_array(
            value,
            name=name,
            ndim=1,
            maximum_entries=MAX_AFFINE_OBSERVATION_DIMENSION,
        )
        if coordinates.shape != (expected_dimension,):
            raise ValueError(
                "%s must have length %d" % (name, expected_dimension)
            )
        return coordinates

    def _residual(
        self,
        source_coordinates: object,
        observation_coordinates: object,
    ) -> Tuple[np.ndarray, np.ndarray]:
        source = self._coordinates(
            source_coordinates,
            name="source_coordinates",
            expected_dimension=self.input_dimension,
        )
        observation = self._coordinates(
            observation_coordinates,
            name="observation_coordinates",
            expected_dimension=self.output_dimension,
        )
        mean = _high_range_affine_map(self.matrix, source, self.bias)
        with np.errstate(over="raise", invalid="raise"):
            try:
                residual = observation - mean
            except FloatingPointError as error:
                raise ArithmeticError(
                    "affine Gaussian mean or residual is not representable"
                ) from error
        if not np.all(np.isfinite(residual)):
            raise ArithmeticError(
                "affine Gaussian mean or residual is not representable"
            )
        return observation, residual

    def log_density_ratio(
        self,
        source_coordinates: object,
        observation_coordinates: object,
    ) -> float:
        """Return ``log dN(Ar+b,Sigma)/dN(0,I)`` at one output point."""

        observation, residual = self._residual(
            source_coordinates, observation_coordinates
        )
        try:
            with np.errstate(over="raise", invalid="raise"):
                whitened = np.linalg.solve(self._cholesky, residual)
            quadratic_difference = _quadratic_form_difference(
                whitened, observation
            )
            bracket = _high_range_fsum(
                (self.log_determinant, quadratic_difference),
                name="affine Gaussian quadratic bracket",
            )
        except (FloatingPointError, OverflowError, ValueError, np.linalg.LinAlgError) as error:
            raise ArithmeticError(
                "affine Gaussian quadratic form is not representable"
            ) from error
        result = -0.5 * bracket
        if not math.isfinite(result):
            raise ArithmeticError(
                "affine Gaussian log density ratio is not representable"
            )
        return 0.0 if result == 0.0 else result

    def log_density_gradient_source(
        self,
        source_coordinates: object,
        observation_coordinates: object,
    ) -> np.ndarray:
        """Return ``A.T Sigma^-1 (x-Ar-b)`` as an immutable vector."""

        factors = self._gradient_product_factors(
            source_coordinates, observation_coordinates
        )
        gradient = np.asarray(
            [
                _signed_log_product_sum(
                    ((0.0, first, second) for first, second in component),
                    name="affine Gaussian source gradient",
                )
                for component in factors
            ],
            dtype=np.float64,
        )
        return _immutable_float_array(gradient)

    def _gradient_product_factors(
        self,
        source_coordinates: object,
        observation_coordinates: object,
    ) -> Tuple[Tuple[Tuple[float, float], ...], ...]:
        """Return unmultiplied factors for stable posterior weighting."""

        _, residual = self._residual(
            source_coordinates, observation_coordinates
        )
        try:
            with np.errstate(over="raise", invalid="raise"):
                lower = np.linalg.solve(self._cholesky, residual)
                precision_residual = np.linalg.solve(self._cholesky.T, lower)
        except (FloatingPointError, np.linalg.LinAlgError) as error:
            raise ArithmeticError(
                "affine Gaussian source gradient is not representable"
            ) from error
        if not np.all(np.isfinite(precision_residual)):
            raise ArithmeticError(
                "affine Gaussian source gradient is not representable"
            )
        return tuple(
            tuple(
                (
                    float(self.matrix[output_index, input_index]),
                    float(precision_residual[output_index]),
                )
                for output_index in range(self.output_dimension)
            )
            for input_index in range(self.input_dimension)
        )


def _validated_type_dimensions(
    value: object,
) -> Tuple[Tuple[int, ...], Mapping[int, int]]:
    if not isinstance(value, Mapping):
        raise TypeError("source_type_dimensions must be a mapping")
    raw_keys = _bounded_tuple(
        value.keys(),
        name="source_type_dimensions keys",
        maximum_items=MAX_ASSOCIATION_DISTINCT_ATOMS,
    )
    if not raw_keys:
        raise ValueError("source_type_dimensions must declare at least one type")
    checked = {}
    for raw_key in raw_keys:
        type_id = _validated_integer(
            raw_key,
            name="source type id",
            minimum=0,
            maximum=2**63 - 1,
        )
        if type_id in checked:
            raise ValueError("source type ids must be unique")
        checked[type_id] = _validated_integer(
            value[raw_key],  # type: ignore[index]
            name="source type dimension",
            minimum=0,
            maximum=MAX_AFFINE_OBSERVATION_DIMENSION,
        )
    type_ids = tuple(sorted(checked))
    return type_ids, MappingProxyType(
        {type_id: checked[type_id] for type_id in type_ids}
    )


@dataclass(frozen=True, eq=False, init=False)
class TypedAffineGaussianObservationChannel:
    """Row-stochastic typed emission with Gaussian continuous fibers.

    Zero-dimensional observation strata represent complete atomic outcomes.
    A finite atomic fiber can therefore be flattened into several such strata,
    with reference weights ``omega_t * eta_t(atom)`` and physical row
    probabilities ``Pi(t|d) * P(atom|t,d)``.  Positive-dimensional strata use
    an affine Gaussian fiber channel.  In every case the returned density
    divides by the observation-reference stratum weight.
    """

    source_type_ids: Tuple[int, ...]
    source_type_dimensions: Mapping[int, int]
    observation_reference: CollapsedPoissonObservationReference
    stratum_probability: np.ndarray = field(repr=False)
    fiber_channels: Mapping[Tuple[int, int], AffineGaussianFiberChannel]
    _source_positions: Mapping[int, int] = field(repr=False)
    _observation_positions: Mapping[int, int] = field(repr=False)

    def __init__(
        self,
        source_type_dimensions: Mapping[int, int],
        observation_reference: CollapsedPoissonObservationReference,
        stratum_probability: object,
        *,
        fiber_channels: Optional[
            Mapping[Tuple[int, int], AffineGaussianFiberChannel]
        ] = None,
    ) -> None:
        source_ids, source_dimensions = _validated_type_dimensions(
            source_type_dimensions
        )
        if type(observation_reference) is not CollapsedPoissonObservationReference:
            raise TypeError(
                "observation_reference must be an exact "
                "CollapsedPoissonObservationReference"
            )
        expected_shape = (len(source_ids), len(observation_reference.type_ids))
        preflight_shape = _preflight_array(
            stratum_probability,
            name="stratum_probability",
            ndim=2,
            maximum_entries=expected_shape[0] * expected_shape[1],
        )
        if preflight_shape != expected_shape:
            raise ValueError(
                "stratum_probability must have shape %r" % (expected_shape,)
            )
        probabilities = _numeric_array(
            stratum_probability,
            name="stratum_probability",
            ndim=2,
            maximum_entries=expected_shape[0] * expected_shape[1],
        )
        if np.any(probabilities < 0.0):
            raise ValueError("stratum_probability entries must be nonnegative")
        for row in probabilities:
            total = math.fsum(float(value) for value in row)
            if not math.isclose(
                total,
                1.0,
                rel_tol=0.0,
                abs_tol=ASSOCIATION_NORMALIZATION_ATOL,
            ):
                raise ValueError("stratum_probability rows must sum to one")
            row /= total

        if fiber_channels is None:
            raw_channels = {}
        else:
            if not isinstance(fiber_channels, Mapping):
                raise TypeError("fiber_channels must be a mapping")
            raw_keys = _bounded_tuple(
                fiber_channels.keys(),
                name="fiber_channels keys",
                maximum_items=len(source_ids)
                * len(observation_reference.type_ids),
            )
            raw_channels = {}
            for raw_key in raw_keys:
                if type(raw_key) is not tuple or len(raw_key) != 2:
                    raise TypeError(
                        "fiber_channels keys must be exact "
                        "(source_type, observation_type) tuples"
                    )
                source_type = _validated_integer(
                    raw_key[0],
                    name="fiber source type",
                    minimum=0,
                    maximum=2**63 - 1,
                )
                observation_type = _validated_integer(
                    raw_key[1],
                    name="fiber observation type",
                    minimum=0,
                    maximum=2**63 - 1,
                )
                if source_type not in source_dimensions:
                    raise ValueError("fiber channel uses an unknown source type")
                if observation_type not in observation_reference.type_dimensions:
                    raise ValueError(
                        "fiber channel uses an unknown observation type"
                    )
                pair = (source_type, observation_type)
                if pair in raw_channels:
                    raise ValueError("fiber_channels contains a duplicate pair")
                channel = fiber_channels[raw_key]
                if type(channel) is not AffineGaussianFiberChannel:
                    raise TypeError(
                        "fiber channel values must be exact "
                        "AffineGaussianFiberChannel instances"
                    )
                if channel.input_dimension != source_dimensions[source_type]:
                    raise ValueError(
                        "fiber channel input dimension does not match source type"
                    )
                if (
                    channel.output_dimension
                    != observation_reference.type_dimensions[observation_type]
                ):
                    raise ValueError(
                        "fiber channel output dimension does not match "
                        "observation type"
                    )
                raw_channels[pair] = channel

        source_positions = {value: index for index, value in enumerate(source_ids)}
        observation_positions = {
            value: index
            for index, value in enumerate(observation_reference.type_ids)
        }
        for source_type in source_ids:
            source_position = source_positions[source_type]
            for observation_type in observation_reference.type_ids:
                observation_position = observation_positions[observation_type]
                dimension = observation_reference.type_dimensions[observation_type]
                probability = float(
                    probabilities[source_position, observation_position]
                )
                channel_exists = (source_type, observation_type) in raw_channels
                if dimension == 0 and channel_exists:
                    raise ValueError(
                        "zero-dimensional observation strata must not have a "
                        "Gaussian fiber channel"
                    )
                if dimension > 0 and probability > 0.0 and not channel_exists:
                    raise ValueError(
                        "every positive continuous stratum requires an affine "
                        "Gaussian fiber channel"
                    )

        object.__setattr__(self, "source_type_ids", source_ids)
        object.__setattr__(self, "source_type_dimensions", source_dimensions)
        object.__setattr__(self, "observation_reference", observation_reference)
        object.__setattr__(
            self, "stratum_probability", _immutable_float_array(probabilities)
        )
        object.__setattr__(
            self, "fiber_channels", MappingProxyType(dict(raw_channels))
        )
        object.__setattr__(
            self, "_source_positions", MappingProxyType(source_positions)
        )
        object.__setattr__(
            self, "_observation_positions", MappingProxyType(observation_positions)
        )

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "typed-affine-gaussian-observation-channel-v1",
            tuple(
                (type_id, self.source_type_dimensions[type_id])
                for type_id in self.source_type_ids
            ),
            self.observation_reference.parameter_key(),
            tuple(
                tuple(float(value) for value in row)
                for row in self.stratum_probability
            ),
            tuple(
                (pair, self.fiber_channels[pair].parameter_key())
                for pair in sorted(self.fiber_channels)
            ),
        )

    def _validate_source(self, event: object) -> TransformedEvent:
        if type(event) is not TransformedEvent:
            raise TypeError("source event must be an exact TransformedEvent")
        try:
            dimension = self.source_type_dimensions[event.event_type]
        except KeyError as error:
            raise ValueError("source event uses an unknown type") from error
        if len(event.coordinates) != dimension:
            raise ValueError("source event has the wrong coordinate dimension")
        return event

    def _validate_observation(self, event: object) -> TransformedEvent:
        if type(event) is not TransformedEvent:
            raise TypeError("observation event must be an exact TransformedEvent")
        return self.observation_reference._base._validate_event(event)

    def log_emission_density(
        self,
        observation: TransformedEvent,
        source: TransformedEvent,
    ) -> float:
        checked_observation = self._validate_observation(observation)
        checked_source = self._validate_source(source)
        source_position = self._source_positions[checked_source.event_type]
        observation_position = self._observation_positions[
            checked_observation.event_type
        ]
        probability = float(
            self.stratum_probability[source_position, observation_position]
        )
        if probability == 0.0:
            return -math.inf
        result = (
            math.log(probability)
            - math.log(
                self.observation_reference.type_weights[
                    checked_observation.event_type
                ]
            )
        )
        if len(checked_observation.coordinates) > 0:
            result += self.fiber_channels[
                (checked_source.event_type, checked_observation.event_type)
            ].log_density_ratio(
                checked_source.coordinates, checked_observation.coordinates
            )
        if not math.isfinite(result):
            raise ArithmeticError("typed emission log density is not finite")
        return 0.0 if result == 0.0 else result

    def emission_density(
        self,
        observation: TransformedEvent,
        source: TransformedEvent,
    ) -> float:
        return _ordinary_from_log(
            self.log_emission_density(observation, source),
            name="typed emission density",
        )

    def log_emission_gradient_source(
        self,
        observation: TransformedEvent,
        source: TransformedEvent,
    ) -> np.ndarray:
        checked_observation = self._validate_observation(observation)
        checked_source = self._validate_source(source)
        source_position = self._source_positions[checked_source.event_type]
        observation_position = self._observation_positions[
            checked_observation.event_type
        ]
        probability = float(
            self.stratum_probability[source_position, observation_position]
        )
        if probability == 0.0:
            raise ValueError("source gradient is undefined for a zero-density edge")
        if len(checked_observation.coordinates) == 0:
            return _immutable_float_array(
                np.zeros(len(checked_source.coordinates), dtype=np.float64)
            )
        return self.fiber_channels[
            (checked_source.event_type, checked_observation.event_type)
        ].log_density_gradient_source(
            checked_source.coordinates, checked_observation.coordinates
        )

    def _log_emission_gradient_product_factors(
        self,
        observation: TransformedEvent,
        source: TransformedEvent,
    ) -> Tuple[Tuple[Tuple[float, float], ...], ...]:
        checked_observation = self._validate_observation(observation)
        checked_source = self._validate_source(source)
        source_position = self._source_positions[checked_source.event_type]
        observation_position = self._observation_positions[
            checked_observation.event_type
        ]
        probability = float(
            self.stratum_probability[source_position, observation_position]
        )
        if probability == 0.0:
            raise ValueError("source gradient is undefined for a zero-density edge")
        if len(checked_observation.coordinates) == 0:
            return tuple(() for _ in checked_source.coordinates)
        return self.fiber_channels[
            (checked_source.event_type, checked_observation.event_type)
        ]._gradient_product_factors(
            checked_source.coordinates, checked_observation.coordinates
        )

    def pair_log_densities(
        self,
        observations: object,
        sources: object,
    ) -> np.ndarray:
        checked_observations = _bounded_tuple(
            observations,
            name="observations",
            maximum_items=MAX_ASSOCIATION_OCCURRENCES,
        )
        checked_sources = _bounded_tuple(
            sources,
            name="sources",
            maximum_items=MAX_ASSOCIATION_OCCURRENCES,
        )
        if len(checked_observations) * len(checked_sources) > MAX_ASSOCIATION_MATRIX_ENTRIES:
            raise AssociationObservationResourceError(
                "pair-density matrix exceeds the entry limit"
            )
        for event in checked_observations:
            self._validate_observation(event)
        for event in checked_sources:
            self._validate_source(event)
        result = np.empty(
            (len(checked_observations), len(checked_sources)),
            dtype=np.float64,
        )
        for observation_index, observation in enumerate(checked_observations):
            for source_index, source in enumerate(checked_sources):
                result[observation_index, source_index] = self.log_emission_density(
                    observation, source
                )
        return _immutable_float_array(result)

    def _pair_log_densities_with_detection(
        self,
        observations: object,
        sources: object,
        detection_probability: np.ndarray,
    ) -> np.ndarray:
        checked_observations = _bounded_tuple(
            observations,
            name="observations",
            maximum_items=MAX_ASSOCIATION_OCCURRENCES,
        )
        checked_sources = _bounded_tuple(
            sources,
            name="sources",
            maximum_items=MAX_ASSOCIATION_OCCURRENCES,
        )
        if detection_probability.shape != (len(checked_sources),):
            raise ValueError("detection factors must match source occurrences")
        if (
            len(checked_observations) * len(checked_sources)
            > MAX_ASSOCIATION_MATRIX_ENTRIES
        ):
            raise AssociationObservationResourceError(
                "pair-density matrix exceeds the entry limit"
            )
        for event in checked_observations:
            self._validate_observation(event)
        for event in checked_sources:
            self._validate_source(event)
        result = np.full(
            (len(checked_observations), len(checked_sources)),
            -math.inf,
            dtype=np.float64,
        )
        active_sources = np.flatnonzero(detection_probability > 0.0)
        for observation_index, observation in enumerate(checked_observations):
            for source_index in active_sources:
                result[observation_index, source_index] = (
                    self.log_emission_density(
                        observation, checked_sources[int(source_index)]
                    )
                )
        return _immutable_float_array(result)


@dataclass(frozen=True, eq=False, init=False)
class TypedGaussianClutterIntensity:
    """Normalized typed Gaussian clutter shape with a tied total intensity."""

    observation_reference: CollapsedPoissonObservationReference
    total_intensity: float
    stratum_probability: np.ndarray = field(repr=False)
    fiber_channels: Mapping[int, AffineGaussianFiberChannel]
    _observation_positions: Mapping[int, int] = field(repr=False)

    def __init__(
        self,
        observation_reference: CollapsedPoissonObservationReference,
        total_intensity: object,
        stratum_probability: object,
        *,
        fiber_channels: Optional[Mapping[int, AffineGaussianFiberChannel]] = None,
    ) -> None:
        if type(observation_reference) is not CollapsedPoissonObservationReference:
            raise TypeError(
                "observation_reference must be an exact "
                "CollapsedPoissonObservationReference"
            )
        total = _validated_real(
            total_intensity, name="total_intensity", nonnegative=True
        )
        if total > MAX_ASSOCIATION_CLUTTER_MEAN:
            raise AssociationObservationResourceError(
                "total_intensity exceeds the implementation limit of %g"
                % MAX_ASSOCIATION_CLUTTER_MEAN
            )
        probabilities = _numeric_array(
            stratum_probability,
            name="stratum_probability",
            ndim=1,
            maximum_entries=len(observation_reference.type_ids),
        )
        if probabilities.shape != (len(observation_reference.type_ids),):
            raise ValueError(
                "stratum_probability must have one entry per observation type"
            )
        if np.any(probabilities < 0.0):
            raise ValueError("stratum_probability entries must be nonnegative")
        probability_sum = math.fsum(float(value) for value in probabilities)
        if not math.isclose(
            probability_sum,
            1.0,
            rel_tol=0.0,
            abs_tol=ASSOCIATION_NORMALIZATION_ATOL,
        ):
            raise ValueError("stratum_probability must sum to one")
        probabilities /= probability_sum

        if fiber_channels is None:
            raw_channels = {}
        else:
            if not isinstance(fiber_channels, Mapping):
                raise TypeError("fiber_channels must be a mapping")
            raw_keys = _bounded_tuple(
                fiber_channels.keys(),
                name="fiber_channels keys",
                maximum_items=len(observation_reference.type_ids),
            )
            raw_channels = {}
            for raw_key in raw_keys:
                observation_type = _validated_integer(
                    raw_key,
                    name="clutter observation type",
                    minimum=0,
                    maximum=2**63 - 1,
                )
                if observation_type not in observation_reference.type_dimensions:
                    raise ValueError("clutter channel uses an unknown type")
                if observation_type in raw_channels:
                    raise ValueError("clutter channels contain a duplicate type")
                channel = fiber_channels[raw_key]  # type: ignore[index]
                if type(channel) is not AffineGaussianFiberChannel:
                    raise TypeError(
                        "clutter fiber channels must be exact "
                        "AffineGaussianFiberChannel instances"
                    )
                if channel.input_dimension != 0:
                    raise ValueError("clutter fiber channels require zero inputs")
                expected_dimension = observation_reference.type_dimensions[
                    observation_type
                ]
                if channel.output_dimension != expected_dimension:
                    raise ValueError(
                        "clutter fiber dimension does not match observation type"
                    )
                raw_channels[observation_type] = channel

        positions = {
            type_id: index
            for index, type_id in enumerate(observation_reference.type_ids)
        }
        for type_id in observation_reference.type_ids:
            dimension = observation_reference.type_dimensions[type_id]
            probability = float(probabilities[positions[type_id]])
            channel_exists = type_id in raw_channels
            if dimension == 0 and channel_exists:
                raise ValueError(
                    "zero-dimensional clutter strata must not have a "
                    "Gaussian fiber channel"
                )
            if dimension > 0 and probability > 0.0 and not channel_exists:
                raise ValueError(
                    "every positive continuous clutter stratum requires a "
                    "Gaussian fiber channel"
                )

        object.__setattr__(self, "observation_reference", observation_reference)
        object.__setattr__(self, "total_intensity", total)
        object.__setattr__(
            self, "stratum_probability", _immutable_float_array(probabilities)
        )
        object.__setattr__(
            self, "fiber_channels", MappingProxyType(dict(raw_channels))
        )
        object.__setattr__(
            self, "_observation_positions", MappingProxyType(positions)
        )

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "typed-gaussian-clutter-intensity-v1",
            self.observation_reference.parameter_key(),
            self.total_intensity,
            tuple(float(value) for value in self.stratum_probability),
            tuple(
                (type_id, self.fiber_channels[type_id].parameter_key())
                for type_id in sorted(self.fiber_channels)
            ),
        )

    def log_intensity(self, observation: TransformedEvent) -> float:
        self.observation_reference._base._validate_event(observation)
        position = self._observation_positions[observation.event_type]
        probability = float(self.stratum_probability[position])
        if self.total_intensity == 0.0 or probability == 0.0:
            return -math.inf
        result = (
            math.log(self.total_intensity)
            + math.log(probability)
            - math.log(
                self.observation_reference.type_weights[observation.event_type]
            )
        )
        if len(observation.coordinates) > 0:
            result += self.fiber_channels[
                observation.event_type
            ].log_density_ratio((), observation.coordinates)
        if not math.isfinite(result):
            raise ArithmeticError("clutter log intensity is not finite")
        return 0.0 if result == 0.0 else result

    def intensity(self, observation: TransformedEvent) -> float:
        return _ordinary_from_log(
            self.log_intensity(observation), name="clutter intensity"
        )

    def log_intensities(self, observations: object) -> np.ndarray:
        checked = _bounded_tuple(
            observations,
            name="observations",
            maximum_items=MAX_ASSOCIATION_OCCURRENCES,
        )
        values = np.empty(len(checked), dtype=np.float64)
        for index, observation in enumerate(checked):
            values[index] = self.log_intensity(observation)
        return _immutable_float_array(values)


def _distinct_configuration(
    configuration: TransformedConfiguration,
) -> Tuple[Tuple[TransformedEvent, ...], Tuple[int, ...]]:
    atoms = []
    multiplicities = []
    index = 0
    while index < len(configuration):
        stop = index + 1
        while (
            stop < len(configuration)
            and configuration[stop].model_key() == configuration[index].model_key()
        ):
            stop += 1
        atoms.append(configuration[index])
        multiplicities.append(stop - index)
        index = stop
    return tuple(atoms), tuple(multiplicities)


@dataclass(frozen=True, eq=False, init=False)
class BoundAssociationDensityEvaluation:
    """One density evaluation authenticated to an immutable kernel row."""

    outcome: AssociationObservationValue
    reference_parameter_key: Tuple[object, ...]
    row_parameter_key: Tuple[object, ...]
    evaluation: AssociationDensityEvaluation = field(repr=False)

    def __init__(
        self,
        outcome: AssociationObservationValue,
        reference_parameter_key: Tuple[object, ...],
        row_parameter_key: Tuple[object, ...],
        evaluation: AssociationDensityEvaluation,
        *,
        _construction_token: object = None,
    ) -> None:
        if _construction_token is not _BOUND_EVALUATION_CONSTRUCTION_TOKEN:
            raise TypeError(
                "bound evaluations can only be constructed by a bound row"
            )
        if outcome is not OVERFLOW_OBSERVATION:
            if type(outcome) is not tuple or any(
                type(event) is not TransformedEvent for event in outcome
            ):
                raise TypeError(
                    "outcome must be a canonical event tuple or exact overflow"
                )
            if outcome != tuple(sorted(outcome, key=TransformedEvent.model_key)):
                raise ValueError("retained outcome must be canonical")
        for name, key in (
            ("reference_parameter_key", reference_parameter_key),
            ("row_parameter_key", row_parameter_key),
        ):
            if type(key) is not tuple:
                raise TypeError("%s must be an exact tuple" % name)
            try:
                hash(key)
            except TypeError as error:
                raise TypeError("%s must be recursively immutable" % name) from error
        if type(evaluation) is not AssociationDensityEvaluation:
            raise TypeError(
                "evaluation must be an exact AssociationDensityEvaluation"
            )
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(
            self, "reference_parameter_key", reference_parameter_key
        )
        object.__setattr__(self, "row_parameter_key", row_parameter_key)
        object.__setattr__(self, "evaluation", evaluation)

    @property
    def clean_log_density(self) -> float:
        return self.evaluation.clean_log_density

    @property
    def clean_density(self) -> float:
        return self.evaluation.clean_density

    @property
    def contamination_probability(self) -> float:
        return self.evaluation.contamination_probability

    @property
    def log_density(self) -> float:
        return self.evaluation.log_density

    @property
    def density(self) -> float:
        return self.evaluation.density

    @property
    def clean_is_structural_zero(self) -> bool:
        return self.evaluation.clean_is_structural_zero

    @property
    def algorithm(self) -> str:
        return self.evaluation.algorithm

    @property
    def latent_occurrence_count(self) -> int:
        return self.evaluation.latent_occurrence_count

    @property
    def observation_occurrence_count(self) -> int:
        return self.evaluation.observation_occurrence_count

    @property
    def association_class_count(self) -> Optional[int]:
        return self.evaluation.association_class_count

    def outcome_key(self) -> Tuple[object, ...]:
        if self.outcome is OVERFLOW_OBSERVATION:
            return ("collapsed-overflow",)
        return (
            "retained-configuration",
            tuple(event.model_key() for event in self.outcome),
        )


@dataclass(frozen=True, eq=False, init=False)
class BoundAssociationObservationRow:
    """Certifying normalized observation row for one latent configuration."""

    observation_reference: CollapsedPoissonObservationReference
    channel: TypedAffineGaussianObservationChannel
    clutter: TypedGaussianClutterIntensity
    sources: TransformedConfiguration
    detection_probability: np.ndarray = field(repr=False)
    contamination_probability: float
    _parameter_key: Tuple[object, ...] = field(repr=False)

    def __init__(
        self,
        observation_reference: CollapsedPoissonObservationReference,
        channel: TypedAffineGaussianObservationChannel,
        clutter: TypedGaussianClutterIntensity,
        sources: object,
        detection_probability: object,
        *,
        contamination_probability: object = 0.0,
    ) -> None:
        if type(observation_reference) is not CollapsedPoissonObservationReference:
            raise TypeError(
                "observation_reference must be an exact "
                "CollapsedPoissonObservationReference"
            )
        if type(channel) is not TypedAffineGaussianObservationChannel:
            raise TypeError(
                "channel must be an exact TypedAffineGaussianObservationChannel"
            )
        if type(clutter) is not TypedGaussianClutterIntensity:
            raise TypeError(
                "clutter must be an exact TypedGaussianClutterIntensity"
            )
        reference_key = observation_reference.parameter_key()
        if channel.observation_reference.parameter_key() != reference_key:
            raise ValueError("channel and row observation references differ")
        if clutter.observation_reference.parameter_key() != reference_key:
            raise ValueError("clutter and row observation references differ")
        source_occurrences = _bounded_tuple(
            sources,
            name="sources",
            maximum_items=MAX_ASSOCIATION_OCCURRENCES,
        )
        for source in source_occurrences:
            channel._validate_source(source)
        _preflight_array(
            detection_probability,
            name="detection_probability",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
            expected_shape=(len(source_occurrences),),
        )
        detection = _probability_vector(
            detection_probability, name="detection_probability"
        )
        ordering = tuple(
            sorted(
                range(len(source_occurrences)),
                key=lambda index: source_occurrences[index].model_key(),
            )
        )
        canonical_sources = tuple(source_occurrences[index] for index in ordering)
        canonical_detection = detection[list(ordering)]
        for index in range(1, len(canonical_sources)):
            if (
                canonical_sources[index].model_key()
                == canonical_sources[index - 1].model_key()
                and float(canonical_detection[index])
                != float(canonical_detection[index - 1])
            ):
                raise ValueError(
                    "identical source atoms require identical detection factors"
                )
        epsilon = _validated_contamination_probability(
            contamination_probability
        )
        parameter_key = (
            "bound-association-observation-row-v1",
            reference_key,
            channel.parameter_key(),
            clutter.parameter_key(),
            tuple(source.model_key() for source in canonical_sources),
            tuple(float(value) for value in canonical_detection),
            epsilon,
        )
        object.__setattr__(self, "observation_reference", observation_reference)
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "clutter", clutter)
        object.__setattr__(self, "sources", canonical_sources)
        object.__setattr__(
            self,
            "detection_probability",
            _immutable_float_array(canonical_detection),
        )
        object.__setattr__(self, "contamination_probability", epsilon)
        object.__setattr__(self, "_parameter_key", parameter_key)

    def parameter_key(self) -> Tuple[object, ...]:
        return self._parameter_key

    def _retained_factors(
        self, observation: TransformedConfiguration
    ) -> RetainedAssociationFactors:
        _association_dp_resources(len(self.sources), len(observation))
        if _association_cardinality_is_structural_zero(
            self.detection_probability,
            self.clutter.total_intensity,
            len(observation),
        ):
            return RetainedAssociationFactors(
                self.detection_probability,
                np.full(
                    (len(observation), len(self.sources)),
                    -math.inf,
                    dtype=np.float64,
                ),
                np.full(len(observation), -math.inf, dtype=np.float64),
                self.clutter.total_intensity,
            )
        return RetainedAssociationFactors(
            self.detection_probability,
            self.channel._pair_log_densities_with_detection(
                observation, self.sources, self.detection_probability
            ),
            self.clutter.log_intensities(observation),
            self.clutter.total_intensity,
        )

    def _quotient_factors(
        self, observation: TransformedConfiguration
    ) -> QuotientAssociationFactors:
        if (
            len(observation) > MAX_ASSOCIATION_ORBIT_OCCURRENCES
            or len(self.sources) > MAX_ASSOCIATION_ORBIT_OCCURRENCES
        ):
            raise AssociationObservationResourceError(
                "quotient occurrence count exceeds the implementation limit"
            )
        observation_atoms, observation_multiplicities = _distinct_configuration(
            observation
        )
        source_atoms, source_multiplicities = _distinct_configuration(self.sources)
        if (
            len(observation_atoms) > MAX_ASSOCIATION_DISTINCT_ATOMS
            or len(source_atoms) > MAX_ASSOCIATION_DISTINCT_ATOMS
        ):
            raise AssociationObservationResourceError(
                "quotient distinct-atom count exceeds the implementation limit"
            )
        source_positions = []
        position = 0
        for multiplicity in source_multiplicities:
            source_positions.append(position)
            position += multiplicity
        detection = self.detection_probability[source_positions]
        if _association_cardinality_is_structural_zero(
            self.detection_probability,
            self.clutter.total_intensity,
            len(observation),
        ):
            return QuotientAssociationFactors(
                observation_multiplicities,
                source_multiplicities,
                detection,
                np.full(
                    (len(observation_atoms), len(source_atoms)),
                    -math.inf,
                    dtype=np.float64,
                ),
                np.full(
                    len(observation_atoms), -math.inf, dtype=np.float64
                ),
                self.clutter.total_intensity,
            )
        return QuotientAssociationFactors(
            observation_multiplicities,
            source_multiplicities,
            detection,
            self.channel._pair_log_densities_with_detection(
                observation_atoms, source_atoms, detection
            ),
            self.clutter.log_intensities(observation_atoms),
            self.clutter.total_intensity,
        )

    def evaluate(
        self,
        observation: object,
        *,
        algorithm: str = "labelled",
    ) -> BoundAssociationDensityEvaluation:
        if algorithm not in ("labelled", "quotient"):
            raise ValueError("algorithm must be 'labelled' or 'quotient'")
        outcome = self.observation_reference.collapse(observation)
        if outcome is OVERFLOW_OBSERVATION:
            evaluation = evaluate_overflow_association(
                self.observation_reference,
                self.detection_probability,
                self.clutter.total_intensity,
                contamination_probability=self.contamination_probability,
            )
        elif algorithm == "labelled":
            evaluation = evaluate_retained_association(
                self._retained_factors(outcome),
                contamination_probability=self.contamination_probability,
            )
        else:
            evaluation = evaluate_quotient_association(
                self._quotient_factors(outcome),
                contamination_probability=self.contamination_probability,
            )
        return BoundAssociationDensityEvaluation(
            outcome,
            self.observation_reference.parameter_key(),
            self.parameter_key(),
            evaluation,
            _construction_token=_BOUND_EVALUATION_CONSTRUCTION_TOKEN,
        )

    def coordinate_gradients(
        self, observation: object
    ) -> "BoundAssociationCoordinateGradients":
        outcome = self.observation_reference.collapse(observation)
        if outcome is OVERFLOW_OBSERVATION:
            raise ValueError(
                "overflow coordinate gradients are outside the retained API"
            )
        _association_dp_resources(len(self.sources), len(outcome))
        _association_marginal_resources(len(self.sources), len(outcome))
        if _association_cardinality_is_structural_zero(
            self.detection_probability,
            self.clutter.total_intensity,
            len(outcome),
        ):
            offsets = [0]
            for source in self.sources:
                offsets.append(offsets[-1] + len(source.coordinates))
            coordinate_gradients = AssociationCoordinateGradients(
                -math.inf,
                self.contamination_probability,
                tuple(offsets),
                np.zeros(offsets[-1], dtype=np.float64),
                np.full(
                    (len(outcome), len(self.sources)),
                    -math.inf,
                    dtype=np.float64,
                ),
            )
        else:
            coordinate_gradients = association_log_density_coordinate_gradients(
                self.channel,
                outcome,
                self.sources,
                self.detection_probability,
                self.clutter.log_intensities(outcome),
                self.clutter.total_intensity,
                contamination_probability=self.contamination_probability,
            )
        return BoundAssociationCoordinateGradients(
            outcome,
            self.observation_reference.parameter_key(),
            self.parameter_key(),
            coordinate_gradients,
            _construction_token=_BOUND_GRADIENT_CONSTRUCTION_TOKEN,
        )


def evaluate_association_observation(
    row: BoundAssociationObservationRow,
    observation: object,
    *,
    algorithm: str = "labelled",
) -> BoundAssociationDensityEvaluation:
    if type(row) is not BoundAssociationObservationRow:
        raise TypeError("row must be an exact BoundAssociationObservationRow")
    return row.evaluate(observation, algorithm=algorithm)


@dataclass(frozen=True, eq=False, init=False)
class AssociationCoordinateGradients:
    """Packed source gradient for a clean or positive-mixture log density."""

    clean_log_density: float
    log_density: float
    contamination_probability: float
    log_clean_responsibility: float
    coordinate_offsets: Tuple[int, ...]
    gradients: np.ndarray = field(repr=False)
    clean_edge_log_marginals: np.ndarray = field(repr=False)
    clean_edge_marginals: np.ndarray = field(repr=False)
    edge_log_marginals: np.ndarray = field(repr=False)
    edge_marginals: np.ndarray = field(repr=False)

    def __init__(
        self,
        clean_log_density: float,
        contamination_probability: object,
        coordinate_offsets: object,
        gradients: object,
        clean_edge_log_marginals: object,
    ) -> None:
        if clean_log_density != -math.inf and not math.isfinite(
            clean_log_density
        ):
            raise ValueError("clean_log_density must be finite or -inf")
        epsilon = _validated_contamination_probability(
            contamination_probability
        )
        log_density = positive_association_log_density(
            clean_log_density, epsilon
        )
        if clean_log_density == -math.inf:
            if epsilon == 0.0:
                raise ValueError(
                    "gradient is undefined for a zero-density clean row"
                )
            log_clean_responsibility = -math.inf
        else:
            log_clean_responsibility = (
                0.0
                if epsilon == 0.0
                else math.log1p(-epsilon)
                + clean_log_density
                - log_density
            )
        if log_clean_responsibility > 0.0:
            if log_clean_responsibility > ASSOCIATION_NORMALIZATION_ATOL:
                raise ArithmeticError("clean-mixture responsibility exceeds one")
            log_clean_responsibility = 0.0
        raw_offsets = _bounded_tuple(
            coordinate_offsets,
            name="coordinate_offsets",
            maximum_items=MAX_ASSOCIATION_OCCURRENCES + 1,
        )
        offsets = tuple(
            _validated_integer(
                value,
                name="coordinate offset",
                minimum=0,
                maximum=MAX_ASSOCIATION_MATRIX_ENTRIES,
            )
            for value in raw_offsets
        )
        if not offsets or offsets[0] != 0 or any(
            left > right for left, right in zip(offsets, offsets[1:])
        ):
            raise ValueError(
                "coordinate_offsets must start at zero and be nondecreasing"
            )
        _preflight_array(
            gradients,
            name="gradients",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
            expected_shape=(offsets[-1],),
        )
        clean_edge_shape = _preflight_array(
            clean_edge_log_marginals,
            name="clean_edge_log_marginals",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
            maximum_axis_lengths=(
                MAX_ASSOCIATION_OCCURRENCES,
                MAX_ASSOCIATION_OCCURRENCES,
            ),
        )
        if clean_edge_shape[1] + 1 != len(offsets):
            raise ValueError(
                "clean edge log marginals columns must match source offsets"
            )
        gradient = _numeric_array(
            gradients,
            name="gradients",
            ndim=1,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
        )
        clean_edge_logs = _log_array(
            clean_edge_log_marginals,
            name="clean_edge_log_marginals",
            ndim=2,
            maximum_entries=MAX_ASSOCIATION_MATRIX_ENTRIES,
        )
        if clean_log_density == -math.inf:
            if np.any(gradient != 0.0):
                raise ValueError(
                    "structural-zero rows require a zero packed gradient"
                )
            if np.any(clean_edge_logs != -math.inf):
                raise ValueError(
                    "structural-zero rows require -inf clean edge logs"
                )
        if np.any(clean_edge_logs > ASSOCIATION_NORMALIZATION_ATOL):
            raise ValueError("clean edge log marginals must not exceed zero")
        clean_edge_logs[clean_edge_logs > 0.0] = 0.0
        with np.errstate(over="ignore", invalid="raise"):
            effective_edge_logs = clean_edge_logs + log_clean_responsibility
        clean_edge = np.exp(clean_edge_logs)
        effective_edge = np.exp(effective_edge_logs)
        object.__setattr__(self, "clean_log_density", clean_log_density)
        object.__setattr__(self, "log_density", log_density)
        object.__setattr__(self, "contamination_probability", epsilon)
        object.__setattr__(
            self, "log_clean_responsibility", log_clean_responsibility
        )
        object.__setattr__(self, "coordinate_offsets", offsets)
        object.__setattr__(self, "gradients", _immutable_float_array(gradient))
        object.__setattr__(
            self,
            "clean_edge_log_marginals",
            _immutable_float_array(clean_edge_logs),
        )
        object.__setattr__(
            self, "clean_edge_marginals", _immutable_float_array(clean_edge)
        )
        object.__setattr__(
            self,
            "edge_log_marginals",
            _immutable_float_array(effective_edge_logs),
        )
        object.__setattr__(
            self, "edge_marginals", _immutable_float_array(effective_edge)
        )

    @property
    def clean_responsibility(self) -> float:
        return math.exp(self.log_clean_responsibility)

    @property
    def clean_is_structural_zero(self) -> bool:
        return self.clean_log_density == -math.inf


@dataclass(frozen=True, eq=False, init=False)
class BoundAssociationCoordinateGradients:
    """Retained coordinate gradients authenticated to one bound row/outcome."""

    outcome: TransformedConfiguration
    reference_parameter_key: Tuple[object, ...]
    row_parameter_key: Tuple[object, ...]
    coordinate_gradients: AssociationCoordinateGradients = field(repr=False)

    def __init__(
        self,
        outcome: TransformedConfiguration,
        reference_parameter_key: Tuple[object, ...],
        row_parameter_key: Tuple[object, ...],
        coordinate_gradients: AssociationCoordinateGradients,
        *,
        _construction_token: object = None,
    ) -> None:
        if _construction_token is not _BOUND_GRADIENT_CONSTRUCTION_TOKEN:
            raise TypeError(
                "bound gradients can only be constructed by a bound row"
            )
        if type(outcome) is not tuple or any(
            type(event) is not TransformedEvent for event in outcome
        ):
            raise TypeError("outcome must be a canonical retained event tuple")
        if outcome != tuple(sorted(outcome, key=TransformedEvent.model_key)):
            raise ValueError("retained outcome must be canonical")
        for name, key in (
            ("reference_parameter_key", reference_parameter_key),
            ("row_parameter_key", row_parameter_key),
        ):
            if type(key) is not tuple:
                raise TypeError("%s must be an exact tuple" % name)
            try:
                hash(key)
            except TypeError as error:
                raise TypeError("%s must be recursively immutable" % name) from error
        if type(coordinate_gradients) is not AssociationCoordinateGradients:
            raise TypeError(
                "coordinate_gradients must be an exact "
                "AssociationCoordinateGradients"
            )
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(
            self, "reference_parameter_key", reference_parameter_key
        )
        object.__setattr__(self, "row_parameter_key", row_parameter_key)
        object.__setattr__(self, "coordinate_gradients", coordinate_gradients)

    @property
    def clean_log_density(self) -> float:
        return self.coordinate_gradients.clean_log_density

    @property
    def log_density(self) -> float:
        return self.coordinate_gradients.log_density

    @property
    def contamination_probability(self) -> float:
        return self.coordinate_gradients.contamination_probability

    @property
    def log_clean_responsibility(self) -> float:
        return self.coordinate_gradients.log_clean_responsibility

    @property
    def clean_responsibility(self) -> float:
        return self.coordinate_gradients.clean_responsibility

    @property
    def clean_is_structural_zero(self) -> bool:
        return self.coordinate_gradients.clean_is_structural_zero

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
    def clean_edge_marginals(self) -> np.ndarray:
        return self.coordinate_gradients.clean_edge_marginals

    @property
    def edge_log_marginals(self) -> np.ndarray:
        return self.coordinate_gradients.edge_log_marginals

    @property
    def edge_marginals(self) -> np.ndarray:
        return self.coordinate_gradients.edge_marginals

    def outcome_key(self) -> Tuple[object, ...]:
        return (
            "retained-configuration-gradient",
            tuple(event.model_key() for event in self.outcome),
        )


def association_log_density_coordinate_gradients(
    channel: TypedAffineGaussianObservationChannel,
    observations: object,
    sources: object,
    detection_probability: object,
    clutter_log_densities: object,
    clutter_total: object,
    *,
    contamination_probability: object = 0.0,
) -> AssociationCoordinateGradients:
    """Evaluate a retained log density and its source-coordinate gradient."""

    if type(channel) is not TypedAffineGaussianObservationChannel:
        raise TypeError(
            "channel must be an exact TypedAffineGaussianObservationChannel"
        )
    checked_observations = _bounded_tuple(
        observations,
        name="observations",
        maximum_items=MAX_ASSOCIATION_OCCURRENCES,
    )
    checked_sources = _bounded_tuple(
        sources,
        name="sources",
        maximum_items=MAX_ASSOCIATION_OCCURRENCES,
    )
    _association_dp_resources(
        len(checked_sources), len(checked_observations)
    )
    _association_marginal_resources(
        len(checked_sources), len(checked_observations)
    )
    _preflight_array(
        detection_probability,
        name="detection_probability",
        ndim=1,
        maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        expected_shape=(len(checked_sources),),
    )
    _preflight_array(
        clutter_log_densities,
        name="clutter_log_densities",
        ndim=1,
        maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
        expected_shape=(len(checked_observations),),
    )
    detection = _probability_vector(
        detection_probability, name="detection_probability"
    )
    clutter_logs = _log_array(
        clutter_log_densities,
        name="clutter_log_densities",
        ndim=1,
        maximum_entries=MAX_ASSOCIATION_OCCURRENCES,
    )
    total = _validated_real(
        clutter_total, name="clutter_total", nonnegative=True
    )
    if total > MAX_ASSOCIATION_CLUTTER_MEAN:
        raise AssociationObservationResourceError(
            "clutter_total exceeds the implementation limit of %g"
            % MAX_ASSOCIATION_CLUTTER_MEAN
        )
    cardinality_zero = len(checked_observations) < int(
        np.count_nonzero(detection == 1.0)
    )
    if cardinality_zero:
        pair_logs = np.full(
            (len(checked_observations), len(checked_sources)),
            -math.inf,
            dtype=np.float64,
        )
        clutter_logs = np.full(
            len(checked_observations), -math.inf, dtype=np.float64
        )
    else:
        pair_logs = channel._pair_log_densities_with_detection(
            checked_observations, checked_sources, detection
        )
    factors = RetainedAssociationFactors(
        detection,
        pair_logs,
        clutter_logs,
        total,
    )
    epsilon = _validated_contamination_probability(
        contamination_probability
    )
    clean_log_density = labelled_association_log_density(factors)
    if clean_log_density == -math.inf:
        if epsilon == 0.0:
            raise ValueError(
                "coordinate gradient is undefined for a zero-density clean row"
            )
        offsets = [0]
        for source in checked_sources:
            checked_source = channel._validate_source(source)
            offsets.append(offsets[-1] + len(checked_source.coordinates))
        return AssociationCoordinateGradients(
            clean_log_density,
            epsilon,
            tuple(offsets),
            np.zeros(offsets[-1], dtype=np.float64),
            np.full(
                (len(checked_observations), len(checked_sources)),
                -math.inf,
                dtype=np.float64,
            ),
        )
    marginals = labelled_association_edge_marginals(factors)
    final_log_density = positive_association_log_density(
        marginals.log_density, epsilon
    )
    log_clean_responsibility = (
        0.0
        if epsilon == 0.0
        else math.log1p(-epsilon)
        + marginals.log_density
        - final_log_density
    )
    offsets = [0]
    packed = []
    for source_index, source in enumerate(checked_sources):
        checked_source = channel._validate_source(source)
        dimension = len(checked_source.coordinates)
        component_terms = [[] for _ in range(dimension)]
        for observation_index, observation in enumerate(checked_observations):
            log_marginal = float(
                marginals.edge_log_marginals[
                    observation_index, source_index
                ]
            ) + log_clean_responsibility
            if log_marginal == -math.inf:
                continue
            edge_factors = channel._log_emission_gradient_product_factors(
                observation, checked_source
            )
            for coordinate_index in range(dimension):
                component_terms[coordinate_index].extend(
                    (log_marginal, first, second)
                    for first, second in edge_factors[coordinate_index]
                )
        for terms in component_terms:
            component = _signed_log_product_sum(
                terms,
                name="association coordinate gradient",
            )
            packed.append(0.0 if component == 0.0 else component)
        offsets.append(len(packed))
    return AssociationCoordinateGradients(
        marginals.log_density,
        epsilon,
        tuple(offsets),
        np.asarray(packed, dtype=np.float64),
        marginals.edge_log_marginals,
    )


__all__ = [
    "ASSOCIATION_NORMALIZATION_ATOL",
    "AssociationDensityEvaluation",
    "AssociationEdgeMarginals",
    "AssociationCoordinateGradients",
    "AssociationObservationResourceError",
    "AssociationObservationValue",
    "AssociationOrbit",
    "AffineGaussianFiberChannel",
    "BoundAssociationCoordinateGradients",
    "BoundAssociationDensityEvaluation",
    "BoundAssociationObservationRow",
    "CollapsedPoissonObservationReference",
    "MAX_AFFINE_COVARIANCE_WORK",
    "MAX_AFFINE_OBSERVATION_DIMENSION",
    "MAX_ASSOCIATION_CLUTTER_MEAN",
    "MAX_ASSOCIATION_DISTINCT_ATOMS",
    "MAX_ASSOCIATION_DP_WORK",
    "MAX_ASSOCIATION_MATRIX_ENTRIES",
    "MAX_ASSOCIATION_OBSERVATION_CAP",
    "MAX_ASSOCIATION_OCCURRENCES",
    "MAX_ASSOCIATION_ORBIT_CLASSES",
    "MAX_ASSOCIATION_ORBIT_OCCURRENCES",
    "MAX_ASSOCIATION_SUBSET_BITS",
    "MAX_POISSON_TAIL_TERMS",
    "RetainedAssociationFactors",
    "QuotientAssociationFactors",
    "TypedAffineGaussianObservationChannel",
    "TypedGaussianClutterIntensity",
    "association_log_density_coordinate_gradients",
    "association_orbit_coefficient",
    "detection_poisson_overflow_log_probability",
    "detection_poisson_overflow_probability",
    "evaluate_association_observation",
    "evaluate_overflow_association",
    "evaluate_quotient_association",
    "evaluate_retained_association",
    "labelled_association_edge_marginals",
    "labelled_association_density",
    "labelled_association_log_density",
    "positive_association_log_density",
    "quotient_association_density",
    "quotient_association_log_density",
]
