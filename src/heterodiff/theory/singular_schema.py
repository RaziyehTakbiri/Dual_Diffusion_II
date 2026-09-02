"""Analytic two-type singular-schema coupling oracle.

Type A carries a generic shared coordinate ``s`` and a scalar ``a``.  Type B
carries exactly the same ``s`` and a vector ``b``.  The forward schema edit is

``(s, a) -> (s, b)``,  ``a ~ N(0, 1)``,  ``b = C a + epsilon``,
``epsilon ~ N(0, sigma**2 I)``.

Copying ``s`` exactly places the pairwise edit law on an equality graph, while
the reverse edit must recreate the dropped scalar from the exact Gaussian
posterior ``a | b``.  This module is a model-agnostic analytic oracle for that
edge case.

Crucially, a fully source-conditioned mark head that receives ``a`` can express
the very same kernel ``N(C a, sigma**2 I)``.  Therefore success on this slice is
a falsification/control tool for schema-edit implementations, not evidence of
methodological novelty or superiority over that control.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Any, Optional, Sequence, Tuple, Union

import numpy as np


_FLOAT64 = np.dtype(np.float64)
_LOG_MAX_FLOAT = math.log(np.finfo(np.float64).max)
_LOG_MIN_SUBNORMAL = math.log(float(np.nextafter(0.0, 1.0)))


def _as_real_array(value: object, name: str) -> np.ndarray:
    """Return a float view/copy while rejecting coercive nonnumeric inputs."""

    raw = np.asarray(value)
    if raw.dtype.kind not in "iuf":
        raise TypeError("%s must contain real non-boolean numbers" % name)
    converted = raw.astype(np.float64, copy=False)
    if not np.all(np.isfinite(converted)):
        raise ValueError("%s must contain only finite values" % name)
    return converted


def _immutable_real_array(
    value: object,
    *,
    name: str,
    require_nonempty_vector: bool = False,
) -> np.ndarray:
    """Return a defensive, bytes-backed, read-only float array."""

    converted = _as_real_array(value, name)
    if require_nonempty_vector and (converted.ndim != 1 or converted.size == 0):
        raise ValueError("%s must be a nonempty one-dimensional vector" % name)
    contiguous = np.array(converted, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=_FLOAT64).reshape(
        contiguous.shape
    )


def _validate_real_scalar(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("%s must be a real number" % name)
    scalar = float(value)
    if not math.isfinite(scalar):
        raise ValueError("%s must be finite" % name)
    return scalar


def _freeze_shared_coordinate(value: Any) -> Any:
    """Defensively freeze numeric array-like shared coordinates.

    Hashable nonnumeric labels are treated as opaque immutable identifiers.
    Unhashable objects must be finite real array-like values; mutable mappings
    and object arrays are rejected rather than retained by reference.
    """

    if isinstance(value, Real):
        if isinstance(value, bool):
            raise TypeError("shared must not be boolean")
        return _validate_real_scalar(value, "shared")
    if isinstance(value, np.ndarray):
        return _immutable_real_array(value, name="shared")
    try:
        hash(value)
    except TypeError:
        try:
            return _immutable_real_array(value, name="shared")
        except (TypeError, ValueError) as error:
            raise TypeError(
                "shared must be a hashable label or finite real array-like coordinate"
            ) from error
    return value


def _safe_value_equal(left: Any, right: Any) -> bool:
    """Compare opaque labels/arrays without NumPy ambiguous-truth failures."""

    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
        return isinstance(left, np.ndarray) and isinstance(
            right, np.ndarray
        ) and bool(np.array_equal(left, right))
    try:
        comparison = left == right
    except Exception:
        return False
    if isinstance(comparison, (bool, np.bool_)):
        return bool(comparison)
    return False


@dataclass(frozen=True, eq=False)
class TypeAMark:
    """A type-A mark with a shared coordinate and one scalar-only field."""

    shared: Any
    a: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "shared", _freeze_shared_coordinate(self.shared))
        object.__setattr__(self, "a", _validate_real_scalar(self.a, "a"))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TypeAMark) and self.a == other.a and _safe_value_equal(
            self.shared, other.shared
        )

    __hash__ = None


@dataclass(frozen=True, eq=False)
class TypeBMark:
    """A type-B mark with the same shared coordinate and a created vector."""

    shared: Any
    b: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "shared", _freeze_shared_coordinate(self.shared))
        object.__setattr__(
            self,
            "b",
            _immutable_real_array(
                self.b,
                name="b",
                require_nonempty_vector=True,
            ),
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TypeBMark)
            and _safe_value_equal(self.shared, other.shared)
            and bool(np.array_equal(self.b, other.b))
        )

    __hash__ = None


ArrayOrScalar = Union[np.ndarray, float]


class TwoTypeSingularSchemaOracle:
    """Closed-form oracle for an absorbing A-to-B schema edit.

    All type mass starts in A.  The forward type process jumps A to absorbing B
    at rate ``rate``.  At elapsed time ``t``,

    ``p_A(t) = exp(-rate*t)`` and ``p_B(t) = 1 - p_A(t)``.

    The instantaneous time-reversed B-to-A rate is
    ``rate / expm1(rate*t)`` for ``t > 0``.  The implementation evaluates an
    algebraically equivalent expression that remains stable for large times.

    The parameter domain requires ``sigma**2``, ``||C||**2``, their sum, and
    the posterior variance to be representable finite binary64 values.  Within
    that domain, log determinants and quadratic forms use scaled formulas and
    fail closed if a requested NLL itself lies outside binary64 range.
    """

    def __init__(
        self,
        coupling: Sequence[float] = (1.0, 2.0),
        sigma: float = 0.4,
        rate: float = 0.7,
    ) -> None:
        coupling_array = np.asarray(coupling)
        if coupling_array.dtype.kind not in "iuf":
            raise TypeError("coupling must contain real non-boolean numbers")
        coupling_array = coupling_array.astype(np.float64, copy=True)
        if coupling_array.ndim != 1 or coupling_array.size == 0:
            raise ValueError("coupling must be a nonempty one-dimensional vector")
        if not np.all(np.isfinite(coupling_array)):
            raise ValueError("coupling entries must be finite")

        self._sigma = self._validate_positive_scalar(sigma, "sigma")
        self._rate = self._validate_positive_scalar(rate, "rate")
        sigma_squared = self._sigma * self._sigma
        if not np.isfinite(sigma_squared) or sigma_squared == 0.0:
            raise ValueError(
                "sigma**2 must be representable, finite, and strictly positive"
            )
        coupling_array.setflags(write=False)
        self._coupling = coupling_array
        # hypot.reduce is scale-stable where a direct dot product can overflow
        # before it is known whether the squared norm is representable.
        coupling_norm = float(np.hypot.reduce(np.abs(coupling_array)))
        coupling_norm_squared = coupling_norm * coupling_norm
        if not np.isfinite(coupling_norm_squared) or (
            coupling_norm > 0.0 and coupling_norm_squared == 0.0
        ):
            raise ValueError(
                "the squared coupling norm must be representable, finite, and "
                "zero only for an exactly zero coupling"
            )
        denominator = sigma_squared + coupling_norm_squared
        if not np.isfinite(denominator):
            raise ValueError(
                "sigma**2 + ||coupling||**2 must be representable and finite"
            )
        if coupling_norm == 0.0:
            log_denominator = 2.0 * math.log(self._sigma)
            posterior_variance = 1.0
        else:
            log_sigma_squared = 2.0 * math.log(self._sigma)
            log_norm_squared = 2.0 * math.log(coupling_norm)
            larger = max(log_sigma_squared, log_norm_squared)
            log_denominator = larger + math.log1p(
                math.exp(min(log_sigma_squared, log_norm_squared) - larger)
            )
            log_ratio = log_norm_squared - log_sigma_squared
            if log_ratio >= 0.0:
                inverse_ratio = math.exp(-log_ratio)
                posterior_variance = inverse_ratio / (1.0 + inverse_ratio)
            else:
                posterior_variance = 1.0 / (1.0 + math.exp(log_ratio))
        if posterior_variance == 0.0:
            raise ValueError(
                "the posterior variance is below the representable float range"
            )
        self._sigma_squared = sigma_squared
        self._coupling_norm = coupling_norm
        self._coupling_norm_squared = coupling_norm_squared
        self._posterior_denominator = denominator
        self._posterior_variance = posterior_variance
        self._log_sigma = math.log(self._sigma)
        self._log_posterior_denominator = log_denominator

    @staticmethod
    def _validate_positive_scalar(value: float, name: str) -> float:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError("%s must be a real number" % name)
        scalar = float(value)
        if not np.isfinite(scalar) or scalar <= 0.0:
            raise ValueError("%s must be finite and strictly positive" % name)
        return scalar

    @staticmethod
    def _validate_elapsed_time(elapsed_time: float, allow_zero: bool) -> float:
        if isinstance(elapsed_time, bool) or not isinstance(elapsed_time, Real):
            raise TypeError("elapsed_time must be a real number")
        time = float(elapsed_time)
        if not np.isfinite(time) or time < 0.0 or (time == 0.0 and not allow_zero):
            qualifier = "nonnegative" if allow_zero else "strictly positive"
            raise ValueError("elapsed_time must be finite and %s" % qualifier)
        return time

    @staticmethod
    def _rng(seed: Optional[int]) -> np.random.Generator:
        if seed is not None:
            if isinstance(seed, bool) or not isinstance(seed, Integral):
                raise TypeError("seed must be a nonnegative integer or None")
            if seed < 0:
                raise ValueError("seed must be nonnegative")
        return np.random.default_rng(seed)

    @property
    def coupling(self) -> np.ndarray:
        """Return a defensive copy of ``C``."""

        return self._coupling.copy()

    @property
    def sigma(self) -> float:
        return self._sigma

    @property
    def rate(self) -> float:
        return self._rate

    @property
    def dimension(self) -> int:
        return self._coupling.size

    def forward_type_probabilities(self, elapsed_time: float) -> np.ndarray:
        """Return stable ``[p_A(t), p_B(t)]`` from the all-A initial law."""

        time = self._validate_elapsed_time(elapsed_time, allow_zero=True)
        scaled_time = self._rate * time
        probability_a = float(np.exp(-scaled_time))
        # -expm1(-x) avoids catastrophic cancellation in 1 - exp(-x).
        probability_b = float(-np.expm1(-scaled_time))
        probabilities = np.array([probability_a, probability_b])
        if (
            not np.all(np.isfinite(probabilities))
            or np.any(probabilities < 0.0)
            or not np.isclose(probabilities.sum(), 1.0, atol=1e-15, rtol=0.0)
        ):
            raise ArithmeticError("forward type probabilities are not normalized")
        return probabilities

    def reverse_b_to_a_rate(self, elapsed_time: float) -> float:
        """Return the exact reverse B-to-A rate at forward time ``t > 0``.

        Mathematically this is ``rate / expm1(rate*t)``.  The computation stays
        in the log domain so a large rate can compensate an ``exp(-rate*t)``
        that would underflow if it were evaluated first.  A result below the
        smallest binary64 value rounds to zero; an unrepresentably large result
        raises instead of silently returning infinity.
        """

        time = self._validate_elapsed_time(elapsed_time, allow_zero=False)
        scaled_time = self._rate * time
        if scaled_time == 0.0:
            # rate*time underflowed, so log(expm1(rate*time)) is accurately
            # log(rate)+log(time) to binary64 precision.
            log_reverse_rate = -math.log(time)
        elif math.isinf(scaled_time):
            log_reverse_rate = -math.inf
        elif scaled_time <= math.log(2.0):
            log_reverse_rate = math.log(self._rate) - math.log(
                math.expm1(scaled_time)
            )
        else:
            log_expm1 = scaled_time + math.log1p(-math.exp(-scaled_time))
            log_reverse_rate = math.log(self._rate) - log_expm1

        if log_reverse_rate > _LOG_MAX_FLOAT:
            raise ArithmeticError("reverse type rate exceeds floating-point range")
        if log_reverse_rate < _LOG_MIN_SUBNORMAL:
            return 0.0
        reverse_rate = math.exp(log_reverse_rate)
        if not np.isfinite(reverse_rate) or reverse_rate < 0.0:
            raise ArithmeticError("reverse type rate is not finite and nonnegative")
        return reverse_rate

    def created_covariance(self) -> np.ndarray:
        """Return ``Cov(b) = C C^T + sigma**2 I`` under the joint oracle."""

        covariance = np.outer(self._coupling, self._coupling) + (
            self._sigma_squared * np.eye(self.dimension)
        )
        if not np.all(np.isfinite(covariance)):
            raise ArithmeticError("the created covariance is not representable")
        return covariance

    def posterior_variance(self) -> float:
        """Return the constant scalar variance of ``a | b``."""

        return self._posterior_variance

    @staticmethod
    def _finite_exponential(log_values: np.ndarray, name: str) -> np.ndarray:
        """Exponentiate nonnegative terms with explicit float-range handling."""

        if np.any(np.isnan(log_values)) or np.any(log_values > _LOG_MAX_FLOAT):
            raise ArithmeticError("%s exceeds the representable float range" % name)
        result = np.zeros(log_values.shape, dtype=np.float64)
        representable = log_values >= _LOG_MIN_SUBNORMAL
        result[representable] = np.exp(log_values[representable])
        if not np.all(np.isfinite(result)):
            raise ArithmeticError("%s is not finite" % name)
        return result

    def _row_squared_norm_over_sigma(
        self,
        values: np.ndarray,
        name: str,
    ) -> np.ndarray:
        """Compute row-wise ``||values||**2 / sigma**2`` without squaring first."""

        matrix = values.reshape(1, -1) if values.ndim == 1 else values
        row_scale = np.max(np.abs(matrix), axis=1)
        normalized = np.zeros_like(matrix)
        nonzero = row_scale > 0.0
        normalized[nonzero] = matrix[nonzero] / row_scale[nonzero, None]
        normalized_norm = np.sum(normalized * normalized, axis=1)
        log_terms = np.full(row_scale.shape, -np.inf, dtype=np.float64)
        log_terms[nonzero] = (
            2.0 * np.log(row_scale[nonzero])
            + np.log(normalized_norm[nonzero])
            - 2.0 * self._log_sigma
        )
        return self._finite_exponential(log_terms, name)

    def _marginal_quadratic(self, b: np.ndarray) -> np.ndarray:
        """Evaluate ``b^T (sigma^2 I + C C^T)^-1 b`` stably.

        The usual Woodbury form subtracts two terms of order ``1/sigma**2``
        and is unusable when ``b`` is close to the coupling direction.  The
        Lagrange identity instead gives the nonnegative decomposition

        ``||b||^2 / D + sum_{i<j}(C_i b_j - C_j b_i)^2 / (sigma^2 D)``,

        where ``D = sigma^2 + ||C||^2``.  Row scaling prevents either outer
        magnitude from overflowing before the final, representable result is
        known.
        """

        matrix = b.reshape(1, -1) if b.ndim == 1 else b
        row_scale = np.max(np.abs(matrix), axis=1)
        normalized_b = np.zeros_like(matrix)
        nonzero_rows = row_scale > 0.0
        normalized_b[nonzero_rows] = (
            matrix[nonzero_rows] / row_scale[nonzero_rows, None]
        )
        normalized_b_norm = np.sum(normalized_b * normalized_b, axis=1)

        log_parallel = np.full(row_scale.shape, -np.inf, dtype=np.float64)
        log_parallel[nonzero_rows] = (
            2.0 * np.log(row_scale[nonzero_rows])
            + np.log(normalized_b_norm[nonzero_rows])
            - self._log_posterior_denominator
        )
        quadratic = self._finite_exponential(
            log_parallel,
            "marginal Gaussian quadratic",
        )

        coupling_scale = float(np.max(np.abs(self._coupling)))
        if coupling_scale > 0.0 and np.any(nonzero_rows):
            normalized_coupling = self._coupling / coupling_scale
            wedge_norm = np.zeros(row_scale.shape, dtype=np.float64)
            for left in range(self.dimension):
                for right in range(left + 1, self.dimension):
                    wedge = (
                        normalized_coupling[left] * normalized_b[:, right]
                        - normalized_coupling[right] * normalized_b[:, left]
                    )
                    wedge_norm += wedge * wedge
            nonzero_wedge = nonzero_rows & (wedge_norm > 0.0)
            log_wedge = np.full(row_scale.shape, -np.inf, dtype=np.float64)
            log_wedge[nonzero_wedge] = (
                2.0 * math.log(coupling_scale)
                + 2.0 * np.log(row_scale[nonzero_wedge])
                + np.log(wedge_norm[nonzero_wedge])
                - 2.0 * self._log_sigma
                - self._log_posterior_denominator
            )
            quadratic += self._finite_exponential(
                log_wedge,
                "marginal Gaussian quadratic",
            )
            if not np.all(np.isfinite(quadratic)):
                raise ArithmeticError(
                    "marginal Gaussian quadratic exceeds the representable float range"
                )
        return quadratic

    def _validate_b(self, b: np.ndarray) -> Tuple[np.ndarray, bool]:
        array = _as_real_array(b, "b")

        is_single = array.ndim == 1
        valid_shape = (is_single and array.shape == (self.dimension,)) or (
            array.ndim == 2 and array.shape[1] == self.dimension
        )
        if not valid_shape:
            raise ValueError(
                "b must have shape (%d,) or (n, %d), got %r"
                % (self.dimension, self.dimension, array.shape)
            )
        return array, is_single

    @staticmethod
    def _validate_a(a: ArrayOrScalar, n: Optional[int] = None) -> Tuple[np.ndarray, bool]:
        array = _as_real_array(a, "a")
        is_single = array.ndim == 0
        if is_single:
            if n is not None:
                raise ValueError("batched b requires a one-dimensional a vector")
        elif array.ndim != 1 or (n is not None and array.shape != (n,)):
            expected = "one-dimensional" if n is None else "shape (%d,)" % n
            raise ValueError("a must be scalar or have %s" % expected)
        return array, is_single

    def posterior_a_given_b(self, b: np.ndarray) -> Tuple[ArrayOrScalar, float]:
        """Return the exact Gaussian posterior mean and variance of ``a | b``."""

        b_array, is_single = self._validate_b(b)
        matrix = b_array.reshape(1, -1) if is_single else b_array
        row_scale = np.max(np.abs(matrix), axis=1)
        normalized = np.zeros_like(matrix)
        nonzero = row_scale > 0.0
        normalized[nonzero] = matrix[nonzero] / row_scale[nonzero, None]
        normalized_dot = normalized @ self._coupling
        nonzero_dot = nonzero & (normalized_dot != 0.0)
        log_absolute_mean = np.full(row_scale.shape, -np.inf, dtype=np.float64)
        log_absolute_mean[nonzero_dot] = (
            np.log(row_scale[nonzero_dot])
            + np.log(np.abs(normalized_dot[nonzero_dot]))
            - self._log_posterior_denominator
        )
        absolute_mean = self._finite_exponential(
            log_absolute_mean,
            "posterior mean",
        )
        posterior_mean = np.sign(normalized_dot) * absolute_mean
        if is_single:
            posterior_mean = float(posterior_mean[0])
        return posterior_mean, self.posterior_variance()

    def sample_joint(
        self,
        n_samples: int,
        *,
        seed: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Sample ``a`` and ``b`` jointly using a reproducible local RNG."""

        if isinstance(n_samples, bool) or not isinstance(n_samples, Integral):
            raise TypeError("n_samples must be a strictly positive integer")
        if n_samples <= 0:
            raise ValueError("n_samples must be strictly positive")
        rng = self._rng(seed)
        a = rng.normal(size=int(n_samples))
        epsilon = rng.normal(
            scale=self._sigma, size=(int(n_samples), self.dimension)
        )
        b = a[:, None] * self._coupling[None, :] + epsilon
        return a, b

    def forward_replace(
        self,
        source: TypeAMark,
        *,
        seed: Optional[int] = None,
    ) -> TypeBMark:
        """Sample the A-to-B mark kernel while copying ``shared`` exactly."""

        if not isinstance(source, TypeAMark):
            raise TypeError("source must be a TypeAMark")
        a, is_single = self._validate_a(source.a)
        if not is_single:
            raise ValueError("TypeAMark.a must be scalar")
        rng = self._rng(seed)
        epsilon = rng.normal(scale=self._sigma, size=self.dimension)
        b = self._coupling * float(a) + epsilon
        return TypeBMark(shared=source.shared, b=b)

    def reverse_replace(
        self,
        source: TypeBMark,
        *,
        seed: Optional[int] = None,
    ) -> TypeAMark:
        """Sample the exact reverse posterior while copying ``shared`` exactly."""

        if not isinstance(source, TypeBMark):
            raise TypeError("source must be a TypeBMark")
        b, is_single = self._validate_b(source.b)
        if not is_single:
            raise ValueError("TypeBMark.b must be a vector")
        posterior_mean, posterior_variance = self.posterior_a_given_b(b)
        rng = self._rng(seed)
        a = rng.normal(float(posterior_mean), np.sqrt(posterior_variance))
        return TypeAMark(shared=source.shared, a=float(a))

    def conditional_nll(self, a: ArrayOrScalar, b: np.ndarray) -> ArrayOrScalar:
        """Return ``-log p(b | a)`` for the source-conditioned Gaussian head."""

        b_array, b_is_single = self._validate_b(b)
        batch_size = None if b_is_single else b_array.shape[0]
        a_array, a_is_single = self._validate_a(a, n=batch_size)
        if b_is_single != a_is_single:
            raise ValueError("a and b must either both be single or both be batched")
        with np.errstate(over="ignore", invalid="ignore"):
            residual = (
                b_array
                - np.expand_dims(a_array, axis=-1) * self._coupling
            )
        if not np.all(np.isfinite(residual)):
            raise ArithmeticError("conditional Gaussian residual is not representable")
        quadratic = self._row_squared_norm_over_sigma(
            residual,
            "conditional Gaussian quadratic",
        )
        normalizer = self.dimension * (
            math.log(2.0 * math.pi) + 2.0 * self._log_sigma
        )
        nll = 0.5 * (normalizer + quadratic)
        if not np.all(np.isfinite(nll)):
            raise ArithmeticError("conditional Gaussian NLL is not representable")
        return float(nll[0]) if b_is_single else nll

    def marginal_nll(self, b: np.ndarray) -> ArrayOrScalar:
        """Return ``-log p(b)`` for the best source-independent Gaussian head."""

        b_array, is_single = self._validate_b(b)
        quadratic = self._marginal_quadratic(b_array)
        log_determinant = (
            2.0 * (self.dimension - 1) * self._log_sigma
            + self._log_posterior_denominator
        )
        nll = 0.5 * (
            self.dimension * math.log(2.0 * math.pi)
            + log_determinant
            + quadratic
        )
        if not np.all(np.isfinite(nll)):
            raise ArithmeticError("marginal Gaussian NLL is not representable")
        return float(nll[0]) if is_single else nll

    def mutual_information(self) -> float:
        """Return ``I(a; b)`` in nats under the Gaussian oracle."""

        if self._coupling_norm == 0.0:
            return 0.0
        log_ratio = 2.0 * (math.log(self._coupling_norm) - self._log_sigma)
        if log_ratio > 0.0:
            softplus = log_ratio + math.log1p(math.exp(-log_ratio))
        else:
            softplus = math.log1p(math.exp(log_ratio))
        mutual_information = 0.5 * softplus
        if not math.isfinite(mutual_information):
            raise ArithmeticError("mutual information is not representable")
        return mutual_information

    def expected_nll_gap(self) -> float:
        """Return the independent-minus-source-conditioned expected NLL gap.

        The gap is exactly ``I(a; b)``.  It quantifies the price of a mark head
        that is forbidden from using the source scalar.  It does *not* separate
        this coupling construction from a fully source-conditioned control.
        """

        return self.mutual_information()
