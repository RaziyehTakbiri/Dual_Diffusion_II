"""Invertible maps from native continuous supports to Euclidean coordinates."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Sequence, Tuple, Union

import numpy as np

from .schema import ContinuousField, SupportKind


ArrayLike = Union[Sequence[float], np.ndarray]


class TransformError(ValueError):
    """Raised when a value is outside a transform's open native domain."""


def _dimension(value: object, *, name: str = "dimension") -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("{} must be an integer".format(name))
    value = int(value)
    if value <= 0:
        raise ValueError("{} must be positive".format(name))
    return value


def _array(value: ArrayLike, *, name: str, last_dimension: int) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise TransformError("{} must be numeric".format(name)) from exc
    if array.ndim == 0 or array.shape[-1] != last_dimension:
        raise TransformError(
            "{} must have last dimension {}; got shape {}".format(
                name, last_dimension, array.shape
            )
        )
    if not np.all(np.isfinite(array)):
        raise TransformError("{} must contain only finite values".format(name))
    return array


def _parameter_vector(
    value: Union[Real, Sequence[float]], *, name: str, dimension: int
) -> Tuple[float, ...]:
    if isinstance(value, bool):
        raise TypeError("{} must be numeric".format(name))
    if isinstance(value, Real):
        array = np.repeat(float(value), dimension)
    else:
        array = np.asarray(value, dtype=np.float64)
        if array.shape != (dimension,):
            raise ValueError("{} must have shape ({},)".format(name, dimension))
    if not np.all(np.isfinite(array)):
        raise ValueError("{} must contain only finite values".format(name))
    return tuple(float(item) for item in array)


class SupportTransform(ABC):
    """Bijection between one native field and Euclidean coordinates.

    Inputs have shape ``(..., native_dimension)`` and outputs have shape
    ``(..., transformed_dimension)``. Log determinants are summed over the
    field coordinates and therefore have shape ``(...)``.
    """

    @property
    @abstractmethod
    def native_dimension(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def transformed_dimension(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def forward(self, value: ArrayLike) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def inverse(self, transformed: ArrayLike) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def log_abs_det_jacobian(self, value: ArrayLike) -> np.ndarray:
        """Return ``log |det d forward(value) / d value|``."""

        raise NotImplementedError

    def inverse_log_abs_det_jacobian(self, transformed: ArrayLike) -> np.ndarray:
        """Return ``log |det d inverse(z) / d z|`` at ``z``."""

        value = self.inverse(transformed)
        return -self.log_abs_det_jacobian(value)


@dataclass(frozen=True)
class IdentityTransform(SupportTransform):
    dimension: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimension", _dimension(self.dimension))

    @property
    def native_dimension(self) -> int:
        return self.dimension

    @property
    def transformed_dimension(self) -> int:
        return self.dimension

    def forward(self, value: ArrayLike) -> np.ndarray:
        return _array(value, name="value", last_dimension=self.dimension).copy()

    def inverse(self, transformed: ArrayLike) -> np.ndarray:
        return _array(
            transformed, name="transformed", last_dimension=self.dimension
        ).copy()

    def log_abs_det_jacobian(self, value: ArrayLike) -> np.ndarray:
        array = _array(value, name="value", last_dimension=self.dimension)
        return np.zeros(array.shape[:-1], dtype=np.float64)


@dataclass(frozen=True)
class AffineTransform(SupportTransform):
    """Training-statistics transform ``z = (x - location) / scale``."""

    dimension: int = 1
    location: Union[Real, Sequence[float]] = 0.0
    scale: Union[Real, Sequence[float]] = 1.0

    def __post_init__(self) -> None:
        dimension = _dimension(self.dimension)
        object.__setattr__(self, "dimension", dimension)
        location = _parameter_vector(
            self.location, name="location", dimension=dimension
        )
        scale = _parameter_vector(self.scale, name="scale", dimension=dimension)
        if any(item <= 0.0 for item in scale):
            raise ValueError("scale must be strictly positive")
        object.__setattr__(self, "location", location)
        object.__setattr__(self, "scale", scale)

    @property
    def native_dimension(self) -> int:
        return self.dimension

    @property
    def transformed_dimension(self) -> int:
        return self.dimension

    def forward(self, value: ArrayLike) -> np.ndarray:
        array = _array(value, name="value", last_dimension=self.dimension)
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            result = (array - np.asarray(self.location)) / np.asarray(self.scale)
        if not np.all(np.isfinite(result)):
            raise TransformError("affine transform produced a non-finite value")
        return result

    def inverse(self, transformed: ArrayLike) -> np.ndarray:
        array = _array(
            transformed, name="transformed", last_dimension=self.dimension
        )
        with np.errstate(over="ignore", invalid="ignore"):
            result = array * np.asarray(self.scale) + np.asarray(self.location)
        if not np.all(np.isfinite(result)):
            raise TransformError("inverse affine transform produced a non-finite value")
        return result

    def log_abs_det_jacobian(self, value: ArrayLike) -> np.ndarray:
        array = _array(value, name="value", last_dimension=self.dimension)
        log_det = -float(np.log(np.asarray(self.scale)).sum())
        return np.full(array.shape[:-1], log_det, dtype=np.float64)


@dataclass(frozen=True)
class LogTransform(SupportTransform):
    """Map a strictly positive field with ``z = log(x)``."""

    dimension: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimension", _dimension(self.dimension))

    @property
    def native_dimension(self) -> int:
        return self.dimension

    @property
    def transformed_dimension(self) -> int:
        return self.dimension

    def forward(self, value: ArrayLike) -> np.ndarray:
        array = _array(value, name="value", last_dimension=self.dimension)
        if np.any(array <= 0.0):
            raise TransformError("log transform requires strictly positive values")
        return np.log(array)

    def inverse(self, transformed: ArrayLike) -> np.ndarray:
        array = _array(
            transformed, name="transformed", last_dimension=self.dimension
        )
        with np.errstate(over="ignore"):
            value = np.exp(array)
        if not np.all(np.isfinite(value)):
            raise TransformError("inverse log transform overflowed")
        if np.any(value <= 0.0):
            raise TransformError(
                "inverse log transform underflowed to zero; returning it would "
                "break strict-positive support and bijectivity"
            )
        return value

    def log_abs_det_jacobian(self, value: ArrayLike) -> np.ndarray:
        array = _array(value, name="value", last_dimension=self.dimension)
        if np.any(array <= 0.0):
            raise TransformError("log transform requires strictly positive values")
        return -np.log(array).sum(axis=-1)

    def inverse_log_abs_det_jacobian(self, transformed: ArrayLike) -> np.ndarray:
        array = _array(
            transformed, name="transformed", last_dimension=self.dimension
        )
        # For x = exp(z), log |dx/dz| = z. Evaluating this directly remains
        # meaningful even when exp(z) cannot be represented as a positive
        # float, while `inverse` correctly refuses to return a boundary zero.
        return array.sum(axis=-1)


@dataclass(frozen=True)
class BoundedLogitTransform(SupportTransform):
    """Map the open interval ``(lower, upper)`` to the real line."""

    lower: float
    upper: float
    dimension: int = 1

    def __post_init__(self) -> None:
        dimension = _dimension(self.dimension)
        object.__setattr__(self, "dimension", dimension)
        if isinstance(self.lower, bool) or not isinstance(self.lower, Real):
            raise TypeError("lower must be a real number")
        if isinstance(self.upper, bool) or not isinstance(self.upper, Real):
            raise TypeError("upper must be a real number")
        lower, upper = float(self.lower), float(self.upper)
        if not math.isfinite(lower) or not math.isfinite(upper):
            raise ValueError("bounds must be finite")
        if lower >= upper:
            raise ValueError("bounded transform requires lower < upper")
        width = upper - lower
        if not math.isfinite(width):
            raise ValueError("bounded transform width must be finite")
        if math.nextafter(lower, upper) >= upper:
            raise ValueError(
                "bounded transform interval has no representable interior value"
            )
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)

    @property
    def native_dimension(self) -> int:
        return self.dimension

    @property
    def transformed_dimension(self) -> int:
        return self.dimension

    def forward(self, value: ArrayLike) -> np.ndarray:
        array = _array(value, name="value", last_dimension=self.dimension)
        if np.any(array <= self.lower) or np.any(array >= self.upper):
            raise TransformError("bounded logit requires values strictly inside bounds")
        result = np.log(array - self.lower) - np.log(self.upper - array)
        if not np.all(np.isfinite(result)):
            raise TransformError("bounded logit transform produced a non-finite value")
        return result

    def inverse(self, transformed: ArrayLike) -> np.ndarray:
        array = _array(
            transformed, name="transformed", last_dimension=self.dimension
        )
        # Stable sigmoid avoids overflow for large negative or positive inputs.
        positive = array >= 0.0
        sigmoid = np.empty_like(array)
        sigmoid[positive] = 1.0 / (1.0 + np.exp(-array[positive]))
        exp_value = np.exp(array[~positive])
        sigmoid[~positive] = exp_value / (1.0 + exp_value)
        value = self.lower + (self.upper - self.lower) * sigmoid
        if np.any(value <= self.lower) or np.any(value >= self.upper):
            raise TransformError(
                "bounded-logit inverse saturated at a floating-point boundary; "
                "returning a clipped value would break bijectivity"
            )
        return value

    def log_abs_det_jacobian(self, value: ArrayLike) -> np.ndarray:
        array = _array(value, name="value", last_dimension=self.dimension)
        if np.any(array <= self.lower) or np.any(array >= self.upper):
            raise TransformError("bounded logit requires values strictly inside bounds")
        per_coordinate = (
            math.log(self.upper - self.lower)
            - np.log(array - self.lower)
            - np.log(self.upper - array)
        )
        return per_coordinate.sum(axis=-1)

    def inverse_log_abs_det_jacobian(self, transformed: ArrayLike) -> np.ndarray:
        array = _array(
            transformed, name="transformed", last_dimension=self.dimension
        )
        per_coordinate = (
            math.log(self.upper - self.lower)
            - np.logaddexp(0.0, -array)
            - np.logaddexp(0.0, array)
        )
        return per_coordinate.sum(axis=-1)


@dataclass(frozen=True)
class SimplexALRTransform(SupportTransform):
    """Additive log-ratio map using the final component as reference."""

    dimension: int

    def __post_init__(self) -> None:
        dimension = _dimension(self.dimension)
        if dimension < 2:
            raise ValueError("simplex dimension must be at least two")
        object.__setattr__(self, "dimension", dimension)

    @property
    def native_dimension(self) -> int:
        return self.dimension

    @property
    def transformed_dimension(self) -> int:
        return self.dimension - 1

    def forward(self, value: ArrayLike) -> np.ndarray:
        array = _array(value, name="value", last_dimension=self.dimension)
        self._validate_simplex(array)
        return np.log(array[..., :-1]) - np.log(array[..., -1:])

    def inverse(self, transformed: ArrayLike) -> np.ndarray:
        array = _array(
            transformed,
            name="transformed",
            last_dimension=self.transformed_dimension,
        )
        logits = np.concatenate((array, np.zeros(array.shape[:-1] + (1,))), axis=-1)
        logits = logits - np.max(logits, axis=-1, keepdims=True)
        weights = np.exp(logits)
        weights = weights / weights.sum(axis=-1, keepdims=True)
        if np.any(weights <= 0.0):
            raise TransformError(
                "simplex inverse underflowed to a boundary; returning floored "
                "weights would break bijectivity"
            )
        if not np.all(np.isfinite(weights)):
            raise TransformError("simplex inverse produced a non-finite value")
        return weights

    def log_abs_det_jacobian(self, value: ArrayLike) -> np.ndarray:
        array = _array(value, name="value", last_dimension=self.dimension)
        self._validate_simplex(array)
        # Determinant in the first K-1 simplex coordinates, x_K=1-sum(x_1:K-1).
        return -np.log(array).sum(axis=-1)

    def inverse_log_abs_det_jacobian(self, transformed: ArrayLike) -> np.ndarray:
        array = _array(
            transformed,
            name="transformed",
            last_dimension=self.transformed_dimension,
        )
        logits = np.concatenate((array, np.zeros(array.shape[:-1] + (1,))), axis=-1)
        log_normalizer = np.logaddexp.reduce(logits, axis=-1, keepdims=True)
        return (logits - log_normalizer).sum(axis=-1)

    @staticmethod
    def _validate_simplex(array: np.ndarray) -> None:
        if np.any(array <= 0.0):
            raise TransformError("simplex components must be strictly positive")
        tolerance = 32.0 * np.finfo(np.float64).eps * array.shape[-1]
        if not np.allclose(
            array.sum(axis=-1), 1.0, rtol=0.0, atol=tolerance
        ):
            raise TransformError("simplex components must sum to one")


def transform_for_field(
    field: ContinuousField,
    *,
    location: Union[None, Real, Sequence[float]] = None,
    scale: Union[None, Real, Sequence[float]] = None,
) -> SupportTransform:
    """Build the declared native-support transform for ``field``.

    Real-valued fields default to the identity. Supplying training-only
    ``location`` and ``scale`` selects an affine standardization; both are
    required together.
    """

    if not isinstance(field, ContinuousField):
        raise TypeError("field must be a ContinuousField")
    if field.support is SupportKind.REAL:
        if (location is None) != (scale is None):
            raise ValueError("location and scale must be supplied together")
        if location is None:
            return IdentityTransform(field.dimension)
        assert scale is not None
        return AffineTransform(field.dimension, location, scale)
    if location is not None or scale is not None:
        raise ValueError(
            "location/scale standardization is only accepted directly for real fields"
        )
    if field.support is SupportKind.POSITIVE:
        return LogTransform(field.dimension)
    if field.support is SupportKind.BOUNDED:
        assert field.lower is not None and field.upper is not None
        return BoundedLogitTransform(field.lower, field.upper, field.dimension)
    if field.support is SupportKind.SIMPLEX:
        return SimplexALRTransform(field.dimension)
    raise AssertionError("unhandled support kind")
