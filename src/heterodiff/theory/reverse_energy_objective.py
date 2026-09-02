"""Reference-relative reversal targets and population objectives.

This module is a NumPy-only theorem-to-code layer.  It implements the local
OU reversal correction, Gaussian-reference relative score matching, the
reversible marginal jump-flux objective, exact finite-state reversal checks,
and unnormalized importance contributions.  It does not implement a neural
energy, a reverse path initializer, a mixed CTMC--OU oracle, or a training
loop.

Every finite generator passed here uses the row convention and must already be
scaled by the physical jump schedule at the requested direct noising time.
Only off-diagonal rates enter the jump-flux objective.
"""

from __future__ import annotations

from dataclasses import dataclass, fields as dataclass_fields
from decimal import Decimal, localcontext
from fractions import Fraction
import math
from numbers import Integral, Real
from typing import Iterable, Optional, Tuple

import numpy as np

from .exact_reversal import reverse_generator
from .finite_atomic_counting import MAX_FINITE_ATOMIC_STATES
from .finite_state import validate_generator, validate_probability_vector
from .path_kl import information_tilt_generator


MAX_REVERSE_OBJECTIVE_STATES = MAX_FINITE_ATOMIC_STATES
MAX_REVERSE_OBJECTIVE_SAMPLES = 100_000
MAX_REVERSE_OBJECTIVE_COORDINATES = 4_000_000
MAX_REVERSE_OBJECTIVE_EXACT_FALLBACK_COORDINATES = 16_384
MAX_REVERSE_OBJECTIVE_IMPORTANCE_TERMS = 1_000_000
DETAILED_BALANCE_LOG_ATOL = 5.0e-12

_FLOAT64_EPSILON = float(np.finfo(np.float64).eps)
_MIN_SUBNORMAL_FLOAT64 = float(np.nextafter(0.0, 1.0))
_LOG_MAX_FLOAT64 = math.log(float(np.finfo(np.float64).max))
_LOG_MIN_SUBNORMAL_FLOAT64 = math.log(_MIN_SUBNORMAL_FLOAT64)
_SMALL_BREGMAN_ARGUMENT = 1.0e-5


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
            raise ValueError(
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
    strictly_positive: bool = False,
    nonnegative: bool = False,
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


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.float64
    ).reshape(contiguous.shape)


def _immutable_int_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.int64)
    contiguous = np.array(array, dtype=np.int64, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.int64
    ).reshape(contiguous.shape)


def _numeric_vector(
    value: object,
    *,
    name: str,
    maximum_items: int,
    allow_empty: bool = False,
) -> np.ndarray:
    if isinstance(value, np.ndarray):
        raw = value
        if raw.ndim != 1:
            raise ValueError("%s must be one-dimensional" % name)
        if raw.size > maximum_items:
            raise ValueError(
                "%s exceeds the implementation limit of %d entries"
                % (name, maximum_items)
            )
    else:
        bounded = _bounded_tuple(
            value,
            name=name,
            maximum_items=maximum_items,
        )
        if any(isinstance(item, (bool, np.bool_)) for item in bounded):
            raise TypeError("%s must not contain boolean entries" % name)
        raw = np.asarray(bounded)
    if raw.ndim != 1:
        raise ValueError("%s must be one-dimensional" % name)
    if raw.size == 0 and not allow_empty:
        raise ValueError("%s must not be empty" % name)
    if raw.dtype.kind == "b":
        raise TypeError("%s must not have boolean dtype" % name)
    if raw.dtype.kind not in "iuf":
        raise TypeError("%s must have a real numeric dtype" % name)
    object_view = np.asarray(raw, dtype=object)
    if any(isinstance(item, (bool, np.bool_)) for item in object_view.flat):
        raise TypeError("%s must not contain boolean entries" % name)
    try:
        result = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s cannot be represented as float64" % name) from error
    if not np.all(np.isfinite(result)):
        raise ValueError("%s entries must be finite" % name)
    return result


def _offset_vector(value: object, *, sample_count: int) -> np.ndarray:
    raw = _bounded_tuple(
        value,
        name="coordinate_offsets",
        maximum_items=MAX_REVERSE_OBJECTIVE_SAMPLES + 1,
    )
    if len(raw) != sample_count + 1:
        raise ValueError(
            "coordinate_offsets must contain sample_count + 1 entries"
        )
    offsets = []
    for item in raw:
        offsets.append(
            _validated_integer(
                item,
                name="coordinate offset",
                minimum=0,
                maximum=MAX_REVERSE_OBJECTIVE_COORDINATES,
            )
        )
    if offsets[0] != 0:
        raise ValueError("coordinate_offsets must begin at zero")
    if any(right < left for left, right in zip(offsets[:-1], offsets[1:])):
        raise ValueError("coordinate_offsets must be nondecreasing")
    return np.asarray(offsets, dtype=np.int64)


def _finite_generator(value: object) -> np.ndarray:
    if isinstance(value, np.ndarray):
        raw = value
        if raw.ndim != 2 or raw.shape[0] != raw.shape[1]:
            raise ValueError("reference_jump_generator must be square")
        if raw.shape[0] > MAX_REVERSE_OBJECTIVE_STATES:
            raise ValueError(
                "reference_jump_generator exceeds the %d-state limit"
                % MAX_REVERSE_OBJECTIVE_STATES
            )
    else:
        rows = _bounded_tuple(
            value,
            name="reference_jump_generator rows",
            maximum_items=MAX_REVERSE_OBJECTIVE_STATES,
        )
        bounded_rows = tuple(
            _bounded_tuple(
                row,
                name="reference_jump_generator row",
                maximum_items=MAX_REVERSE_OBJECTIVE_STATES,
            )
            for row in rows
        )
        if any(
            isinstance(item, (bool, np.bool_))
            for row in bounded_rows
            for item in row
        ):
            raise TypeError(
                "reference_jump_generator must not contain boolean entries"
            )
        raw = np.asarray(bounded_rows)
    if raw.ndim != 2 or raw.shape[0] != raw.shape[1]:
        raise ValueError("reference_jump_generator must be square")
    if raw.shape[0] == 0:
        raise ValueError("reference_jump_generator must contain a state")
    if raw.dtype.kind == "b":
        raise TypeError("reference_jump_generator must not have boolean dtype")
    if raw.dtype.kind not in "iuf":
        raise TypeError("reference_jump_generator must have a real numeric dtype")
    object_view = np.asarray(raw, dtype=object)
    if any(isinstance(item, (bool, np.bool_)) for item in object_view.flat):
        raise TypeError(
            "reference_jump_generator must not contain boolean entries"
        )
    generator = validate_generator(raw)
    for source in range(generator.shape[0]):
        exit_rate = _checked_fsum(
            (
                float(generator[source, destination])
                for destination in range(generator.shape[0])
                if destination != source
            ),
            name="reference generator exit rate",
        )
        residual = _checked_fsum(
            (float(generator[source, source]), exit_rate),
            name="reference generator row residual",
        )
        tolerance = 64.0 * _FLOAT64_EPSILON * max(
            abs(float(generator[source, source])), exit_rate
        )
        if abs(residual) > tolerance:
            raise ValueError(
                "reference_jump_generator rows are not conservatively scaled"
            )
    return generator


def _positive_probability_vector(
    value: object,
    *,
    state_count: int,
    name: str,
) -> np.ndarray:
    vector = _numeric_vector(
        value,
        name=name,
        maximum_items=MAX_REVERSE_OBJECTIVE_STATES,
    )
    if vector.shape != (state_count,):
        raise ValueError("%s must have shape (%d,)" % (name, state_count))
    checked = validate_probability_vector(vector, state_count)
    if np.any(checked <= 0.0):
        raise ValueError("%s must have full strictly positive support" % name)
    return checked


def _energy_vector(value: object, *, state_count: int, name: str) -> np.ndarray:
    vector = _numeric_vector(
        value,
        name=name,
        maximum_items=MAX_REVERSE_OBJECTIVE_STATES,
    )
    if vector.shape != (state_count,):
        raise ValueError("%s must have shape (%d,)" % (name, state_count))
    return vector


def _checked_fsum(values: Iterable[float], *, name: str) -> float:
    try:
        result = math.fsum(values)
    except OverflowError as error:
        raise ArithmeticError("%s overflowed" % name) from error
    if not math.isfinite(result):
        raise ArithmeticError("%s is not finite" % name)
    return 0.0 if result == 0.0 else result


def _checked_mean(values: Iterable[float], count: int, *, name: str) -> float:
    """Return a finite mean without overflowing a representable average."""

    items = tuple(float(value) for value in values)
    if len(items) != count:
        raise ValueError("%s count is inconsistent with its values" % name)
    try:
        total = math.fsum(items)
    except OverflowError:
        # A sum may overflow even though its average is representable.  Scaling
        # every term by the positive integer first preserves signs and avoids
        # that avoidable intermediate range loss.
        scaled = [value / count for value in items]
        result = _checked_fsum(scaled, name=name)
    else:
        if not math.isfinite(total):
            raise ArithmeticError("%s sum is not finite" % name)
        result = total / count
        if total != 0.0 and result == 0.0:
            raise ArithmeticError("nonzero %s underflowed" % name)
    if not math.isfinite(result):
        raise ArithmeticError("%s is not finite" % name)
    return 0.0 if result == 0.0 else result


def _checked_positive_product(left: float, right: float, *, name: str) -> float:
    result = left * right
    if not math.isfinite(result):
        raise ArithmeticError("%s is not finite" % name)
    if left > 0.0 and right > 0.0 and result <= 0.0:
        raise ArithmeticError("positive %s underflowed" % name)
    return result


def _checked_signed_product(left: float, right: float, *, name: str) -> float:
    result = left * right
    if not math.isfinite(result):
        raise ArithmeticError("%s is not finite" % name)
    if left != 0.0 and right != 0.0 and result == 0.0:
        raise ArithmeticError("nonzero %s underflowed" % name)
    return 0.0 if result == 0.0 else result


def _checked_weighted_square(
    value: float,
    weight: float,
    *,
    prefactor: float,
    name: str,
) -> float:
    """Return ``prefactor * weight * value**2`` through log-safe arithmetic."""

    if value == 0.0 or weight == 0.0:
        return 0.0
    log_value = (
        math.log(prefactor)
        + math.log(weight)
        + 2.0 * math.log(abs(value))
    )
    return _positive_from_log(log_value, name=name)


def _checked_weighted_pairing(
    left: float,
    right: float,
    weight: float,
    *,
    name: str,
) -> float:
    """Return ``weight * left * right`` without overflowing an intermediate."""

    if left == 0.0 or right == 0.0 or weight == 0.0:
        return 0.0
    magnitude = _positive_from_log(
        math.log(weight) + math.log(abs(left)) + math.log(abs(right)),
        name=name,
    )
    return -magnitude if (left < 0.0) != (right < 0.0) else magnitude


def _exact_gaussian_reverse_drift_component(
    rate: float,
    coordinate: float,
    score: float,
) -> float:
    """Round the complete binary-rational drift expression exactly once."""

    exact_bracket = (
        Fraction.from_float(score)
        - Fraction.from_float(coordinate) * Fraction(1, 2)
    )
    exact_component = Fraction.from_float(rate) * exact_bracket
    try:
        result = float(exact_component)
    except (OverflowError, ValueError) as error:
        raise ArithmeticError(
            "Gaussian reference reverse drift component is not representable"
        ) from error
    if not math.isfinite(result):
        raise ArithmeticError(
            "Gaussian reference reverse drift component is not finite"
        )
    # Preserve a correctly rounded signed zero at the half-min-subnormal tie.
    return result


def _exact_gaussian_score_contribution(
    rate: float,
    coordinate: np.ndarray,
    gradient: np.ndarray,
    laplacian: float,
) -> float:
    """Exact binary-rational fallback for a cancelling score polynomial."""

    if gradient.size > MAX_REVERSE_OBJECTIVE_EXACT_FALLBACK_COORDINATES:
        raise ValueError(
            "exact score fallback exceeds the %d-coordinate limit"
            % MAX_REVERSE_OBJECTIVE_EXACT_FALLBACK_COORDINATES
        )
    bracket = Fraction.from_float(laplacian)
    one_half = Fraction(1, 2)
    for coordinate_value, gradient_value in zip(coordinate, gradient):
        exact_coordinate = Fraction.from_float(float(coordinate_value))
        exact_gradient = Fraction.from_float(float(gradient_value))
        bracket += one_half * exact_gradient * exact_gradient
        bracket -= exact_coordinate * exact_gradient
    exact_result = Fraction.from_float(rate) * bracket
    try:
        result = float(exact_result)
    except (OverflowError, ValueError) as error:
        raise ArithmeticError(
            "continuous score-matching contribution is not representable"
        ) from error
    if not math.isfinite(result):
        raise ArithmeticError(
            "continuous score-matching contribution is not finite"
        )
    if exact_result != 0 and result == 0.0:
        raise ArithmeticError(
            "nonzero continuous score-matching contribution underflowed"
        )
    return 0.0 if result == 0.0 else result


def _positive_from_log(log_value: float, *, name: str) -> float:
    if not math.isfinite(log_value):
        raise ArithmeticError("log %s is not finite" % name)
    if log_value > _LOG_MAX_FLOAT64:
        raise ArithmeticError("positive %s overflowed" % name)
    if log_value < _LOG_MIN_SUBNORMAL_FLOAT64:
        raise ArithmeticError("positive %s underflowed" % name)
    try:
        result = math.exp(log_value)
    except OverflowError as error:
        raise ArithmeticError("positive %s overflowed" % name) from error
    if not math.isfinite(result) or result <= 0.0:
        raise ArithmeticError("positive %s is not representable" % name)
    return result


def _jump_flux_term(weight: float, edge_difference: float) -> float:
    if weight == 0.0:
        return 0.0
    if weight < 0.0 or not math.isfinite(weight):
        raise ValueError("jump-flux reference weight must be finite and nonnegative")
    difference = _validated_real(
        edge_difference,
        name="energy edge difference",
    )
    if difference == 0.0:
        return weight
    try:
        exponential_minus_one = math.expm1(difference)
    except OverflowError:
        exponential_minus_one = math.inf
    if math.isfinite(exponential_minus_one):
        bracket = _checked_fsum(
            (exponential_minus_one, 1.0, difference),
            name="jump-flux unscaled bracket",
        )
        bracket_scale = max(
            1.0,
            abs(exponential_minus_one),
            abs(difference),
        )
        if abs(bracket) <= 1.0e-8 * bracket_scale:
            with localcontext() as context:
                context.prec = 100
                decimal_difference = Decimal.from_float(difference)
                decimal_result = Decimal.from_float(weight) * (
                    decimal_difference.exp() + decimal_difference
                )
            try:
                result = float(decimal_result)
            except (OverflowError, ValueError) as error:
                raise ArithmeticError(
                    "jump-flux contribution is not representable"
                ) from error
            if not math.isfinite(result):
                raise ArithmeticError("jump-flux contribution is not finite")
            if decimal_result != 0 and result == 0.0:
                raise ArithmeticError("nonzero jump-flux contribution underflowed")
            return 0.0 if result == 0.0 else result
        return _checked_signed_product(
            weight,
            bracket,
            name="jump-flux contribution",
        )
    exponential = _positive_from_log(
        math.log(weight) + difference,
        name="weighted jump exponential",
    )
    linear = _checked_signed_product(
        weight,
        difference,
        name="weighted jump linear term",
    )
    return _checked_fsum(
        (exponential, linear),
        name="jump-flux contribution",
    )


def _exponential_bregman(value: float) -> float:
    difference = _validated_real(value, name="energy error difference")
    magnitude = abs(difference)
    if magnitude < _SMALL_BREGMAN_ARGUMENT:
        square = difference * difference
        if difference == 0.0:
            return 0.0
        if square == 0.0:
            raise ArithmeticError("jump-flux excess squared error underflowed")
        result = 0.5 * square * (
            1.0
            + difference / 3.0
            + square / 12.0
            + square * difference / 60.0
            + square * square / 360.0
        )
        if result == 0.0:
            raise ArithmeticError("jump-flux excess underflowed")
    else:
        try:
            result = math.expm1(difference) - difference
        except OverflowError as error:
            raise ArithmeticError("jump-flux excess overflowed") from error
    if not math.isfinite(result):
        raise ArithmeticError("jump-flux excess is not finite")
    if result < 0.0:
        tolerance = 32.0 * _FLOAT64_EPSILON * max(1.0, magnitude)
        if result < -tolerance:
            raise ArithmeticError("jump-flux excess became negative")
        return 0.0
    return 0.0 if result == 0.0 else result


def _off_diagonal_edges(generator: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    off_diagonal = generator.copy()
    np.fill_diagonal(off_diagonal, 0.0)
    sources, destinations = np.nonzero(off_diagonal > 0.0)
    return sources.astype(np.int64), destinations.astype(np.int64)


def _validate_reference_reversibility(
    generator: np.ndarray,
    reference: np.ndarray,
) -> None:
    state_count = generator.shape[0]
    logs = np.log(reference)
    for source in range(state_count):
        for destination in range(source + 1, state_count):
            forward = float(generator[source, destination])
            reverse = float(generator[destination, source])
            if (forward == 0.0) != (reverse == 0.0):
                raise ValueError(
                    "reference_jump_generator support is not reversible"
                )
            if forward == 0.0:
                continue
            residual = (
                float(logs[source])
                + math.log(forward)
                - float(logs[destination])
                - math.log(reverse)
            )
            if abs(residual) > DETAILED_BALANCE_LOG_ATOL:
                raise ValueError(
                    "reference_jump_generator is not reversible under "
                    "invariant_reference"
                )


class _ValidatedPickleMixin:
    """Reconstruct dataclass records through their validating constructors."""

    def __reduce__(self):
        return (
            type(self),
            tuple(getattr(self, field.name) for field in dataclass_fields(self)),
        )


@dataclass(frozen=True, eq=False)
class ContinuousScoreMatchingResult(_ValidatedPickleMixin):
    """Packed-batch Gaussian-reference score-matching contributions."""

    per_sample: np.ndarray
    mean: float
    sample_count: int
    coordinate_count: int

    def __post_init__(self) -> None:
        count = _validated_integer(
            self.sample_count,
            name="sample_count",
            minimum=1,
            maximum=MAX_REVERSE_OBJECTIVE_SAMPLES,
        )
        coordinates = _validated_integer(
            self.coordinate_count,
            name="coordinate_count",
            minimum=0,
            maximum=MAX_REVERSE_OBJECTIVE_COORDINATES,
        )
        terms = _numeric_vector(
            self.per_sample,
            name="per_sample",
            maximum_items=MAX_REVERSE_OBJECTIVE_SAMPLES,
        )
        if terms.shape != (count,):
            raise ValueError("per_sample shape does not match sample_count")
        mean = _validated_real(self.mean, name="mean")
        expected = _checked_mean(
            terms, count, name="score-matching batch mean"
        )
        if mean != expected:
            raise ValueError("mean is inconsistent with per_sample")
        object.__setattr__(self, "per_sample", _immutable_float_array(terms))
        object.__setattr__(self, "mean", mean)
        object.__setattr__(self, "sample_count", count)
        object.__setattr__(self, "coordinate_count", coordinates)


@dataclass(frozen=True, eq=False)
class ContinuousScoreExcessResult(_ValidatedPickleMixin):
    """Packed-batch nonnegative relative-score excess."""

    per_sample: np.ndarray
    mean: float
    sample_count: int
    coordinate_count: int

    def __post_init__(self) -> None:
        matching = ContinuousScoreMatchingResult(
            self.per_sample,
            self.mean,
            self.sample_count,
            self.coordinate_count,
        )
        if np.any(matching.per_sample < 0.0) or matching.mean < 0.0:
            raise ValueError("continuous score excess must be nonnegative")
        object.__setattr__(self, "per_sample", matching.per_sample)
        object.__setattr__(self, "mean", matching.mean)
        object.__setattr__(self, "sample_count", matching.sample_count)
        object.__setattr__(self, "coordinate_count", matching.coordinate_count)


@dataclass(frozen=True, eq=False)
class FiniteJumpFluxEvaluation(_ValidatedPickleMixin):
    """Exact finite-state marginal jump-flux value and derivatives."""

    energy: np.ndarray
    marginal: np.ndarray
    invariant_reference: np.ndarray
    reference_jump_generator: np.ndarray
    per_state_loss: np.ndarray
    loss: float
    gradient: np.ndarray
    hessian: np.ndarray
    tilted_generator: np.ndarray
    state_count: int
    edge_count: int

    def __post_init__(self) -> None:
        states = _validated_integer(
            self.state_count,
            name="state_count",
            minimum=1,
            maximum=MAX_REVERSE_OBJECTIVE_STATES,
        )
        edges = _validated_integer(
            self.edge_count,
            name="edge_count",
            minimum=0,
            maximum=MAX_REVERSE_OBJECTIVE_STATES
            * (MAX_REVERSE_OBJECTIVE_STATES - 1),
        )
        energy = _energy_vector(self.energy, state_count=states, name="energy")
        marginal = _positive_probability_vector(
            self.marginal,
            state_count=states,
            name="marginal",
        )
        reference = _positive_probability_vector(
            self.invariant_reference,
            state_count=states,
            name="invariant_reference",
        )
        generator = _finite_generator(self.reference_jump_generator)
        if generator.shape != (states, states):
            raise ValueError(
                "reference_jump_generator shape does not match state_count"
            )
        _validate_reference_reversibility(generator, reference)
        per_state = _energy_vector(
            self.per_state_loss,
            state_count=states,
            name="per_state_loss",
        )
        gradient = _energy_vector(
            self.gradient,
            state_count=states,
            name="gradient",
        )
        raw_hessian = np.asarray(self.hessian)
        if raw_hessian.dtype.kind == "b":
            raise TypeError("hessian must not have boolean dtype")
        if raw_hessian.dtype.kind not in "iuf":
            raise TypeError("hessian must have a real numeric dtype")
        hessian = raw_hessian.astype(np.float64, copy=True)
        if hessian.shape != (states, states) or not np.all(np.isfinite(hessian)):
            raise ValueError("hessian must be a finite state_count square matrix")
        if not np.array_equal(hessian, hessian.T):
            raise ValueError("hessian must be exactly symmetric")
        tilted = validate_generator(np.asarray(self.tilted_generator))
        if tilted.shape != (states, states):
            raise ValueError("tilted_generator shape does not match state_count")
        observed_edges = int(np.count_nonzero(tilted - np.diag(np.diag(tilted))))
        if observed_edges != edges:
            raise ValueError("edge_count is inconsistent with tilted_generator")
        loss = _validated_real(self.loss, name="loss")
        if loss != _checked_fsum(per_state, name="finite jump-flux loss"):
            raise ValueError("loss is inconsistent with per_state_loss")
        (
            expected_per_state,
            expected_loss,
            expected_gradient,
            expected_hessian,
            expected_tilted,
            expected_edges,
        ) = _finite_jump_flux_arrays(marginal, generator, energy)
        for name, observed, expected in (
            ("per_state_loss", per_state, expected_per_state),
            ("gradient", gradient, expected_gradient),
            ("hessian", hessian, expected_hessian),
            ("tilted_generator", tilted, expected_tilted),
        ):
            if not np.array_equal(observed, expected):
                raise ValueError("%s is inconsistent with finite inputs" % name)
        if loss != expected_loss or edges != expected_edges:
            raise ValueError("finite jump summary is inconsistent with inputs")
        object.__setattr__(self, "energy", _immutable_float_array(energy))
        object.__setattr__(self, "marginal", _immutable_float_array(marginal))
        object.__setattr__(
            self, "invariant_reference", _immutable_float_array(reference)
        )
        object.__setattr__(
            self,
            "reference_jump_generator",
            _immutable_float_array(generator),
        )
        object.__setattr__(
            self, "per_state_loss", _immutable_float_array(per_state)
        )
        object.__setattr__(self, "loss", loss)
        object.__setattr__(self, "gradient", _immutable_float_array(gradient))
        object.__setattr__(self, "hessian", _immutable_float_array(hessian))
        object.__setattr__(
            self, "tilted_generator", _immutable_float_array(tilted)
        )
        object.__setattr__(self, "state_count", states)
        object.__setattr__(self, "edge_count", edges)


@dataclass(frozen=True, eq=False)
class FiniteEnergyReversal(_ValidatedPickleMixin):
    """Finite exact relative energy and two independent reversed generators."""

    reference_jump_generator: np.ndarray
    invariant_reference: np.ndarray
    marginal: np.ndarray
    relative_energy: np.ndarray
    energy_tilted_generator: np.ndarray
    direct_reverse_generator: np.ndarray
    maximum_residual: float
    state_count: int
    edge_count: int

    def __post_init__(self) -> None:
        states = _validated_integer(
            self.state_count,
            name="state_count",
            minimum=1,
            maximum=MAX_REVERSE_OBJECTIVE_STATES,
        )
        edges = _validated_integer(
            self.edge_count,
            name="edge_count",
            minimum=0,
            maximum=MAX_REVERSE_OBJECTIVE_STATES
            * (MAX_REVERSE_OBJECTIVE_STATES - 1),
        )
        generator = _finite_generator(self.reference_jump_generator)
        if generator.shape != (states, states):
            raise ValueError(
                "reference_jump_generator shape does not match state_count"
            )
        reference = _positive_probability_vector(
            self.invariant_reference,
            state_count=states,
            name="invariant_reference",
        )
        marginal = _positive_probability_vector(
            self.marginal,
            state_count=states,
            name="marginal",
        )
        _validate_reference_reversibility(generator, reference)
        energy = _energy_vector(
            self.relative_energy,
            state_count=states,
            name="relative_energy",
        )
        expected_energy = np.log(marginal) - np.log(reference)
        if not np.array_equal(energy, expected_energy):
            raise ValueError("relative_energy is inconsistent with the two laws")
        tilted = validate_generator(np.asarray(self.energy_tilted_generator))
        direct = validate_generator(np.asarray(self.direct_reverse_generator))
        if tilted.shape != (states, states) or direct.shape != (states, states):
            raise ValueError("reversed generator shapes do not match state_count")
        expected_tilted = information_tilt_generator(generator, energy)
        expected_direct = reverse_generator(generator, marginal)
        if not np.array_equal(tilted, expected_tilted):
            raise ValueError("energy_tilted_generator is inconsistent with inputs")
        if not np.array_equal(direct, expected_direct):
            raise ValueError("direct_reverse_generator is inconsistent with inputs")
        maximum = _validated_real(
            self.maximum_residual,
            name="maximum_residual",
            nonnegative=True,
        )
        observed = float(np.max(np.abs(tilted - direct)))
        if maximum != observed:
            raise ValueError("maximum_residual is inconsistent with generators")
        observed_edges = int(np.count_nonzero(tilted - np.diag(np.diag(tilted))))
        if observed_edges != edges:
            raise ValueError("edge_count is inconsistent with reversed generator")
        object.__setattr__(
            self,
            "reference_jump_generator",
            _immutable_float_array(generator),
        )
        object.__setattr__(
            self, "invariant_reference", _immutable_float_array(reference)
        )
        object.__setattr__(self, "marginal", _immutable_float_array(marginal))
        object.__setattr__(
            self, "relative_energy", _immutable_float_array(energy)
        )
        object.__setattr__(
            self,
            "energy_tilted_generator",
            _immutable_float_array(tilted),
        )
        object.__setattr__(
            self,
            "direct_reverse_generator",
            _immutable_float_array(direct),
        )
        object.__setattr__(self, "maximum_residual", maximum)
        object.__setattr__(self, "state_count", states)
        object.__setattr__(self, "edge_count", edges)


@dataclass(frozen=True, eq=False)
class FiniteJumpFluxExcess(_ValidatedPickleMixin):
    """Non-certifying diagnostic summary of two jump-flux excess forms.

    The constructor checks internal arithmetic but does not retain enough
    source data to authenticate provenance.  Use :func:`finite_jump_flux_excess`
    to produce theorem-to-code evidence.
    """

    exact_loss: float
    candidate_loss: float
    direct_difference: float
    stable_excess: float
    identity_residual: float
    exact_gradient_infinity_norm: float
    energy_error: np.ndarray

    def __post_init__(self) -> None:
        exact = _validated_real(self.exact_loss, name="exact_loss")
        candidate = _validated_real(self.candidate_loss, name="candidate_loss")
        direct = _validated_real(self.direct_difference, name="direct_difference")
        stable = _validated_real(
            self.stable_excess,
            name="stable_excess",
            nonnegative=True,
        )
        residual = _validated_real(self.identity_residual, name="identity_residual")
        gradient = _validated_real(
            self.exact_gradient_infinity_norm,
            name="exact_gradient_infinity_norm",
            nonnegative=True,
        )
        error = _numeric_vector(
            self.energy_error,
            name="energy_error",
            maximum_items=MAX_REVERSE_OBJECTIVE_STATES,
        )
        if direct != _checked_fsum(
            (candidate, -exact), name="direct jump-flux difference"
        ):
            raise ValueError("direct_difference is inconsistent with losses")
        if residual != _checked_fsum(
            (direct, -stable), name="jump-flux excess identity residual"
        ):
            raise ValueError("identity_residual is inconsistent with excess forms")
        object.__setattr__(self, "exact_loss", exact)
        object.__setattr__(self, "candidate_loss", candidate)
        object.__setattr__(self, "direct_difference", direct)
        object.__setattr__(self, "stable_excess", stable)
        object.__setattr__(self, "identity_residual", residual)
        object.__setattr__(self, "exact_gradient_infinity_norm", gradient)
        object.__setattr__(self, "energy_error", _immutable_float_array(error))


@dataclass(frozen=True, eq=False)
class JumpFluxImportanceResult(_ValidatedPickleMixin):
    """Non-certifying summary of unnormalized ``q/R`` contributions.

    The record validates its arrays and mean, but it cannot prove that the
    declared values came from actual draws under the stated proposal.
    """

    importance_weights: np.ndarray
    contributions: np.ndarray
    estimate: float
    proposal_count: int

    def __post_init__(self) -> None:
        count = _validated_integer(
            self.proposal_count,
            name="proposal_count",
            minimum=1,
            maximum=MAX_REVERSE_OBJECTIVE_IMPORTANCE_TERMS,
        )
        weights = _numeric_vector(
            self.importance_weights,
            name="importance_weights",
            maximum_items=MAX_REVERSE_OBJECTIVE_IMPORTANCE_TERMS,
        )
        contributions = _numeric_vector(
            self.contributions,
            name="contributions",
            maximum_items=MAX_REVERSE_OBJECTIVE_IMPORTANCE_TERMS,
        )
        if weights.shape != (count,) or contributions.shape != (count,):
            raise ValueError("importance arrays must match proposal_count")
        if np.any(weights < 0.0):
            raise ValueError("importance_weights must be nonnegative")
        estimate = _validated_real(self.estimate, name="estimate")
        expected = _checked_mean(
            contributions,
            count,
            name="importance contribution mean",
        )
        if estimate != expected:
            raise ValueError("estimate is inconsistent with contributions")
        object.__setattr__(
            self, "importance_weights", _immutable_float_array(weights)
        )
        object.__setattr__(
            self, "contributions", _immutable_float_array(contributions)
        )
        object.__setattr__(self, "estimate", estimate)
        object.__setattr__(self, "proposal_count", count)


@dataclass(frozen=True)
class JumpFluxProposalFactors:
    """Named disintegration factors for one jump-flux proposal draw.

    The target edge measure is

    ``omega * p * gamma_J * lambda_family * a_occurrence * a_destination``

    and the proposal measure replaces those factors by
    ``tau * rho * r_family * r_occurrence * r_destination``.  Unit factors
    represent inapplicable branches (for example occurrence selection for a
    birth).  Target/reference factors may be zero under a dominating proposal;
    every proposal factor must be strictly positive at a supplied draw.
    """

    target_time_density: float
    proposal_time_density: float
    target_state_density: float
    proposal_state_density: float
    reference_schedule_rate: float
    reference_family_rate: float
    proposal_family_probability: float
    reference_occurrence_probability: float
    proposal_occurrence_probability: float
    reference_destination_density: float
    proposal_destination_density: float

    def __post_init__(self) -> None:
        nonnegative = (
            "target_time_density",
            "target_state_density",
            "reference_schedule_rate",
            "reference_family_rate",
            "reference_destination_density",
        )
        positive = (
            "proposal_time_density",
            "proposal_state_density",
            "proposal_destination_density",
        )
        for name in nonnegative:
            object.__setattr__(
                self,
                name,
                _validated_real(getattr(self, name), name=name, nonnegative=True),
            )
        for name in positive:
            object.__setattr__(
                self,
                name,
                _validated_real(
                    getattr(self, name), name=name, strictly_positive=True
                ),
            )
        for name, strictly_positive in (
            ("reference_occurrence_probability", False),
            ("proposal_family_probability", True),
            ("proposal_occurrence_probability", True),
        ):
            probability = _validated_real(
                getattr(self, name),
                name=name,
                strictly_positive=strictly_positive,
                nonnegative=not strictly_positive,
            )
            if probability > 1.0:
                raise ValueError("%s must not exceed one" % name)
            object.__setattr__(self, name, probability)

    @property
    def has_zero_target_mass(self) -> bool:
        return any(
            getattr(self, name) == 0.0
            for name in (
                "target_time_density",
                "target_state_density",
                "reference_schedule_rate",
                "reference_family_rate",
                "reference_occurrence_probability",
                "reference_destination_density",
            )
        )

    @property
    def importance_weight(self) -> float:
        if self.has_zero_target_mass:
            return 0.0
        log_weight = math.fsum(
            (
                math.log(self.target_time_density),
                -math.log(self.proposal_time_density),
                math.log(self.target_state_density),
                -math.log(self.proposal_state_density),
                math.log(self.reference_schedule_rate),
                math.log(self.reference_family_rate),
                -math.log(self.proposal_family_probability),
                math.log(self.reference_occurrence_probability),
                -math.log(self.proposal_occurrence_probability),
                math.log(self.reference_destination_density),
                -math.log(self.proposal_destination_density),
            )
        )
        return _positive_from_log(log_weight, name="factorized jump importance weight")


@dataclass(frozen=True)
class EnergyBoundConsequences:
    """Arithmetic consequences of externally proved global energy bounds.

    This record does not certify a model or checkpoint.  The later neural
    module must prove that its architecture and parameters satisfy the supplied
    value and derivative bounds.
    """

    value_bound: float
    first_derivative_bound: float
    second_derivative_bound: float

    def __post_init__(self) -> None:
        value = _validated_real(
            self.value_bound,
            name="value_bound",
            nonnegative=True,
        )
        first = _validated_real(
            self.first_derivative_bound,
            name="first_derivative_bound",
            nonnegative=True,
        )
        second = _validated_real(
            self.second_derivative_bound,
            name="second_derivative_bound",
            nonnegative=True,
        )
        edge_bound = 2.0 * value
        if not math.isfinite(edge_bound):
            raise ArithmeticError("edge-difference bound is not finite")
        _positive_from_log(edge_bound, name="jump-rate multiplier bound")
        object.__setattr__(self, "value_bound", value)
        object.__setattr__(self, "first_derivative_bound", first)
        object.__setattr__(self, "second_derivative_bound", second)

    @property
    def edge_difference_bound(self) -> float:
        return 2.0 * self.value_bound

    @property
    def jump_rate_multiplier_bound(self) -> float:
        """Mathematical ``exp(2 B)`` multiplier in binary64.

        Use :meth:`tilted_rate_upper_bound` for an operational floating-point
        envelope on a particular base rate.
        """

        return _positive_from_log(
            self.edge_difference_bound,
            name="jump-rate multiplier bound",
        )

    def tilted_rate_upper_bound(self, base_rate: object) -> float:
        """Bound this implementation's two rounded binary64 rate paths.

        This operational guard is not an interval enclosure of the real-valued
        expression ``q * exp(2 B)``.  The mathematical multiplier statement
        and this finite-arithmetic guard are deliberately distinct.
        """

        rate = _validated_real(
            base_rate,
            name="base_rate",
            nonnegative=True,
        )
        if rate == 0.0:
            return 0.0
        if self.edge_difference_bound == 0.0:
            return rate
        log_path = _positive_from_log(
            math.log(rate) + self.edge_difference_bound,
            name="tilted jump-rate upper bound",
        )
        direct_path = _checked_positive_product(
            rate,
            self.jump_rate_multiplier_bound,
            name="direct tilted jump-rate upper bound",
        )
        candidate = max(log_path, direct_path)
        envelope = math.nextafter(candidate, math.inf)
        if not math.isfinite(envelope):
            raise ArithmeticError(
                "tilted jump-rate upper bound cannot be rounded outward"
            )
        return envelope


@dataclass(frozen=True)
class ReverseEnergyObjectiveValue:
    """Stable combination of continuous and jump population losses."""

    continuous: float
    jump: float
    jump_weight: float
    total: float

    def __post_init__(self) -> None:
        continuous = _validated_real(self.continuous, name="continuous")
        jump = _validated_real(self.jump, name="jump")
        weight = _validated_real(
            self.jump_weight,
            name="jump_weight",
            strictly_positive=True,
        )
        weighted_jump = _checked_signed_product(
            weight,
            jump,
            name="weighted jump objective",
        )
        total = _validated_real(self.total, name="total")
        expected = _checked_fsum(
            (continuous, weighted_jump),
            name="combined reverse-energy objective",
        )
        if total != expected:
            raise ValueError("total is inconsistent with objective components")
        object.__setattr__(self, "continuous", continuous)
        object.__setattr__(self, "jump", jump)
        object.__setattr__(self, "jump_weight", weight)
        object.__setattr__(self, "total", total)


def gaussian_relative_score_matching(
    continuous_rates: object,
    coordinate_offsets: object,
    coordinates: object,
    energy_coordinate_gradients: object,
    energy_laplacians: object,
) -> ContinuousScoreMatchingResult:
    """Evaluate the packed-batch Gaussian-reference relative-score risk."""

    rates = _numeric_vector(
        continuous_rates,
        name="continuous_rates",
        maximum_items=MAX_REVERSE_OBJECTIVE_SAMPLES,
    )
    if np.any(rates < 0.0):
        raise ValueError("continuous_rates must be nonnegative")
    sample_count = int(rates.size)
    offsets = _offset_vector(coordinate_offsets, sample_count=sample_count)
    coordinate_count = int(offsets[-1])
    values = _numeric_vector(
        coordinates,
        name="coordinates",
        maximum_items=MAX_REVERSE_OBJECTIVE_COORDINATES,
        allow_empty=True,
    )
    gradients = _numeric_vector(
        energy_coordinate_gradients,
        name="energy_coordinate_gradients",
        maximum_items=MAX_REVERSE_OBJECTIVE_COORDINATES,
        allow_empty=True,
    )
    laplacians = _numeric_vector(
        energy_laplacians,
        name="energy_laplacians",
        maximum_items=MAX_REVERSE_OBJECTIVE_SAMPLES,
    )
    if values.shape != (coordinate_count,) or gradients.shape != (coordinate_count,):
        raise ValueError("coordinate arrays must end at coordinate_offsets[-1]")
    if laplacians.shape != (sample_count,):
        raise ValueError("energy_laplacians must have one value per sample")

    terms = []
    for index in range(sample_count):
        rate = float(rates[index])
        if rate == 0.0:
            terms.append(0.0)
            continue
        left = int(offsets[index])
        right = int(offsets[index + 1])
        if left == right:
            if float(laplacians[index]) != 0.0:
                raise ValueError(
                    "a coordinate-free sample must have zero Laplacian"
                )
            terms.append(0.0)
            continue
        gradient = gradients[left:right]
        coordinate = values[left:right]
        laplacian = float(laplacians[index])
        base_failed = False
        squares = []
        pairings = []
        for coordinate_value, gradient_value in zip(coordinate, gradient):
            coordinate_float = float(coordinate_value)
            gradient_float = float(gradient_value)
            square = gradient_float * gradient_float
            pairing = coordinate_float * gradient_float
            if (
                not math.isfinite(square)
                or (gradient_float != 0.0 and square == 0.0)
                or not math.isfinite(pairing)
                or (
                    coordinate_float != 0.0
                    and gradient_float != 0.0
                    and pairing == 0.0
                )
            ):
                base_failed = True
                break
            squares.append(square)
            pairings.append(pairing)
        if not base_failed:
            try:
                half_squared_norm = 0.5 * math.fsum(squares)
                reference_pairing = math.fsum(pairings)
                bracket = math.fsum(
                    (half_squared_norm, laplacian, -reference_pairing)
                )
            except OverflowError:
                base_failed = True
        if not base_failed:
            bracket_scale = max(
                1.0,
                abs(half_squared_norm),
                abs(laplacian),
                abs(reference_pairing),
            )
            if abs(bracket) > 1.0e-8 * bracket_scale:
                terms.append(
                    _checked_signed_product(
                        rate,
                        bracket,
                        name="continuous score-matching contribution",
                    )
                )
                continue
        terms.append(
            _exact_gaussian_score_contribution(
                rate, coordinate, gradient, laplacian
            )
        )
    mean = _checked_mean(
        terms,
        sample_count,
        name="continuous score-matching batch mean",
    )
    return ContinuousScoreMatchingResult(
        per_sample=np.asarray(terms, dtype=np.float64),
        mean=mean,
        sample_count=sample_count,
        coordinate_count=coordinate_count,
    )


def gaussian_relative_score_excess(
    continuous_rates: object,
    coordinate_offsets: object,
    candidate_coordinate_gradients: object,
    exact_relative_scores: object,
) -> ContinuousScoreExcessResult:
    """Evaluate ``gamma_C / 2`` times the packed squared score error."""

    rates = _numeric_vector(
        continuous_rates,
        name="continuous_rates",
        maximum_items=MAX_REVERSE_OBJECTIVE_SAMPLES,
    )
    if np.any(rates < 0.0):
        raise ValueError("continuous_rates must be nonnegative")
    sample_count = int(rates.size)
    offsets = _offset_vector(coordinate_offsets, sample_count=sample_count)
    coordinate_count = int(offsets[-1])
    candidate = _numeric_vector(
        candidate_coordinate_gradients,
        name="candidate_coordinate_gradients",
        maximum_items=MAX_REVERSE_OBJECTIVE_COORDINATES,
        allow_empty=True,
    )
    exact = _numeric_vector(
        exact_relative_scores,
        name="exact_relative_scores",
        maximum_items=MAX_REVERSE_OBJECTIVE_COORDINATES,
        allow_empty=True,
    )
    if candidate.shape != (coordinate_count,) or exact.shape != (coordinate_count,):
        raise ValueError("score arrays must end at coordinate_offsets[-1]")

    terms = []
    for index in range(sample_count):
        rate = float(rates[index])
        if rate == 0.0:
            terms.append(0.0)
            continue
        left = int(offsets[index])
        right = int(offsets[index + 1])
        squared_terms = []
        for position in range(left, right):
            candidate_value = float(candidate[position])
            exact_value = float(exact[position])
            try:
                difference = math.fsum((candidate_value, -exact_value))
            except OverflowError:
                square_root_weight = math.sqrt(0.5 * rate)
                if square_root_weight == 0.0:
                    square_root_weight = math.sqrt(rate) / math.sqrt(2.0)
                scaled_difference = _checked_fsum(
                    (
                        _checked_signed_product(
                            square_root_weight,
                            candidate_value,
                            name="scaled candidate relative score",
                        ),
                        _checked_signed_product(
                            -square_root_weight,
                            exact_value,
                            name="scaled exact relative score",
                        ),
                    ),
                    name="scaled relative-score error",
                )
                squared_terms.append(
                    _checked_weighted_square(
                        scaled_difference,
                        1.0,
                        prefactor=1.0,
                        name="continuous score excess",
                    )
                )
            else:
                squared_terms.append(
                    _checked_weighted_square(
                        difference,
                        rate,
                        prefactor=0.5,
                        name="continuous score excess",
                    )
                )
        squared_error = _checked_fsum(
            squared_terms,
            name="continuous score excess",
        )
        terms.append(squared_error)
    mean = _checked_mean(
        terms,
        sample_count,
        name="continuous score excess batch mean",
    )
    return ContinuousScoreExcessResult(
        per_sample=np.asarray(terms, dtype=np.float64),
        mean=mean,
        sample_count=sample_count,
        coordinate_count=coordinate_count,
    )


def gaussian_reference_reverse_drift(
    coordinate: object,
    relative_score: Optional[object],
    continuous_rate: object,
) -> np.ndarray:
    """Return ``-gamma_C r / 2 + gamma_C grad V`` for one packed event."""

    rate = _validated_real(
        continuous_rate,
        name="continuous_rate",
        nonnegative=True,
    )
    values = _numeric_vector(
        coordinate,
        name="coordinate",
        maximum_items=MAX_REVERSE_OBJECTIVE_COORDINATES,
        allow_empty=True,
    )
    if rate == 0.0:
        return _immutable_float_array(np.zeros(values.shape, dtype=np.float64))
    if relative_score is None:
        raise ValueError("relative_score is required when continuous_rate is positive")
    score = _numeric_vector(
        relative_score,
        name="relative_score",
        maximum_items=MAX_REVERSE_OBJECTIVE_COORDINATES,
        allow_empty=True,
    )
    if score.shape != values.shape:
        raise ValueError("relative_score must match coordinate shape")
    result = []
    for coordinate_value, score_value in zip(values, score):
        coordinate_float = float(coordinate_value)
        score_float = float(score_value)
        half_coordinate = 0.5 * coordinate_float
        # Multiplying by 1/2 is exact for ordinary binary64 values, but not
        # for odd subnormal significands (including the normal/subnormal
        # boundary).  The round-trip check detects precisely when forming the
        # unscaled bracket would already have rounded the reference term.
        bracket_is_safe = (
            coordinate_float == 0.0
            or half_coordinate * 2.0 == coordinate_float
        )
        if bracket_is_safe:
            try:
                bracket = math.fsum((-half_coordinate, score_float))
            except OverflowError:
                bracket_is_safe = False
        if bracket_is_safe:
            try:
                component = _checked_signed_product(
                    rate,
                    bracket,
                    name="Gaussian reference reverse drift component",
                )
            except ArithmeticError:
                # Exact fallback distinguishes a legitimate rounded zero from
                # an unrepresentable overflow and makes the underflow policy
                # consistent with the inexact-halving path below.
                component = _exact_gaussian_reverse_drift_component(
                    rate,
                    coordinate_float,
                    score_float,
                )
        else:
            # When halving is inexact, rounding the reference and score terms
            # separately can change the final ulp or even the sign.  Evaluate
            # the complete binary-input expression exactly, then round once.
            component = _exact_gaussian_reverse_drift_component(
                rate,
                coordinate_float,
                score_float,
            )
        result.append(component)
    return _immutable_float_array(np.asarray(result, dtype=np.float64))


def finite_relative_energy(
    marginal: object,
    invariant_reference: object,
) -> np.ndarray:
    """Return the canonical finite relative energy ``log p - log pi``."""

    raw_marginal = _numeric_vector(
        marginal,
        name="marginal",
        maximum_items=MAX_REVERSE_OBJECTIVE_STATES,
    )
    state_count = int(raw_marginal.size)
    checked_marginal = _positive_probability_vector(
        raw_marginal,
        state_count=state_count,
        name="marginal",
    )
    reference = _positive_probability_vector(
        invariant_reference,
        state_count=state_count,
        name="invariant_reference",
    )
    energy = np.log(checked_marginal) - np.log(reference)
    if not np.all(np.isfinite(energy)):
        raise ArithmeticError("finite relative energy is not representable")
    return _immutable_float_array(energy)


def validate_finite_energy_gauge_shift(
    reference_jump_generator: object,
    energy: object,
    shifted_energy: object,
) -> float:
    """Validate a materialized binary64 state-independent gauge shift.

    Real-arithmetic gauge invariance cannot recover edge differences already
    destroyed when a caller forms ``energy + c`` in finite precision.  This
    diagnostic accepts only a common represented shift that preserves every
    active edge difference bit for bit and returns that shift.
    """

    generator = _finite_generator(reference_jump_generator)
    state_count = int(generator.shape[0])
    baseline = _energy_vector(energy, state_count=state_count, name="energy")
    shifted = _energy_vector(
        shifted_energy,
        state_count=state_count,
        name="shifted_energy",
    )
    offsets = []
    for baseline_value, shifted_value in zip(baseline, shifted):
        offsets.append(
            _checked_fsum(
                (float(shifted_value), -float(baseline_value)),
                name="represented energy gauge",
            )
        )
    gauge = offsets[0]
    if any(offset != gauge for offset in offsets[1:]):
        raise ValueError("shifted_energy does not contain one represented gauge")
    sources, destinations = _off_diagonal_edges(generator)
    for raw_source, raw_destination in zip(sources, destinations):
        source = int(raw_source)
        destination = int(raw_destination)
        baseline_difference = _checked_fsum(
            (
                float(baseline[destination]),
                -float(baseline[source]),
            ),
            name="baseline active edge difference",
        )
        shifted_difference = _checked_fsum(
            (
                float(shifted[destination]),
                -float(shifted[source]),
            ),
            name="shifted active edge difference",
        )
        if baseline_difference != shifted_difference:
            raise ValueError(
                "materialized gauge does not preserve active edge differences"
            )
    return gauge


def finite_exact_energy_reversal(
    reference_jump_generator: object,
    marginal: object,
    invariant_reference: object,
) -> FiniteEnergyReversal:
    """Compare an energy tilt with direct finite-state time reversal.

    ``reference_jump_generator`` must already include ``gamma_J(s)`` for the
    requested direct forward time.
    """

    generator = _finite_generator(reference_jump_generator)
    state_count = int(generator.shape[0])
    reference = _positive_probability_vector(
        invariant_reference,
        state_count=state_count,
        name="invariant_reference",
    )
    checked_marginal = _positive_probability_vector(
        marginal,
        state_count=state_count,
        name="marginal",
    )
    _validate_reference_reversibility(generator, reference)
    energy = np.log(checked_marginal) - np.log(reference)
    tilted = information_tilt_generator(generator, energy)
    direct = reverse_generator(generator, checked_marginal)
    maximum = float(np.max(np.abs(tilted - direct)))
    for source in range(state_count):
        for destination in range(state_count):
            tilted_rate = float(tilted[source, destination])
            direct_rate = float(direct[source, destination])
            if (tilted_rate == 0.0) != (direct_rate == 0.0):
                raise ArithmeticError(
                    "energy tilt and direct reversal have different support"
                )
            if tilted_rate == direct_rate:
                continue
            scale = max(abs(tilted_rate), abs(direct_rate))
            if scale == 0.0 or abs(tilted_rate - direct_rate) > 2.0e-11 * scale:
                raise ArithmeticError(
                    "energy tilt does not reconstruct the direct reversed generator"
                )
    sources, _ = _off_diagonal_edges(generator)
    return FiniteEnergyReversal(
        reference_jump_generator=generator,
        invariant_reference=reference,
        marginal=checked_marginal,
        relative_energy=energy,
        energy_tilted_generator=tilted,
        direct_reverse_generator=direct,
        maximum_residual=maximum,
        state_count=state_count,
        edge_count=int(sources.size),
    )


def _finite_jump_flux_arrays(
    probabilities: np.ndarray,
    generator: np.ndarray,
    values: np.ndarray,
) -> Tuple[np.ndarray, float, np.ndarray, np.ndarray, np.ndarray, int]:
    state_count = int(generator.shape[0])
    tilted = information_tilt_generator(generator, values)
    sources, destinations = _off_diagonal_edges(generator)
    per_state_terms = [[] for _ in range(state_count)]
    gradient_terms = [[] for _ in range(state_count)]
    hessian = np.zeros((state_count, state_count), dtype=np.float64)

    for raw_source, raw_destination in zip(sources, destinations):
        source = int(raw_source)
        destination = int(raw_destination)
        base_rate = float(generator[source, destination])
        tilted_rate = float(tilted[source, destination])
        base_flux = _checked_positive_product(
            float(probabilities[source]),
            base_rate,
            name="forward marginal reference flux",
        )
        tilted_flux = _checked_positive_product(
            float(probabilities[source]),
            tilted_rate,
            name="forward marginal tilted flux",
        )
        difference = _checked_fsum(
            (float(values[destination]), -float(values[source])),
            name="energy edge difference",
        )
        per_state_terms[source].append(
            _jump_flux_term(base_flux, difference)
        )
        gradient_weight = _checked_fsum(
            (tilted_flux, base_flux),
            name="finite jump gradient edge weight",
        )
        gradient_terms[source].append(-gradient_weight)
        gradient_terms[destination].append(gradient_weight)
        for row, column, signed_flux in (
            (source, source, tilted_flux),
            (destination, destination, tilted_flux),
            (source, destination, -tilted_flux),
            (destination, source, -tilted_flux),
        ):
            hessian[row, column] = _checked_fsum(
                (float(hessian[row, column]), signed_flux),
                name="finite jump Hessian entry",
            )

    per_state = np.asarray(
        [
            _checked_fsum(terms, name="finite jump state loss")
            if terms
            else 0.0
            for terms in per_state_terms
        ],
        dtype=np.float64,
    )
    gradient = np.asarray(
        [
            _checked_fsum(terms, name="finite jump energy gradient")
            if terms
            else 0.0
            for terms in gradient_terms
        ],
        dtype=np.float64,
    )
    loss = _checked_fsum(per_state, name="finite jump-flux loss")
    return per_state, loss, gradient, hessian, tilted, int(sources.size)


def finite_jump_flux_objective(
    marginal: object,
    invariant_reference: object,
    reference_jump_generator: object,
    energy: object,
    *,
    bounds: Optional[EnergyBoundConsequences] = None,
) -> FiniteJumpFluxEvaluation:
    """Evaluate the checked reversible finite jump-flux risk and derivatives."""

    generator = _finite_generator(reference_jump_generator)
    state_count = int(generator.shape[0])
    probabilities = _positive_probability_vector(
        marginal,
        state_count=state_count,
        name="marginal",
    )
    reference = _positive_probability_vector(
        invariant_reference,
        state_count=state_count,
        name="invariant_reference",
    )
    _validate_reference_reversibility(generator, reference)
    values = _energy_vector(energy, state_count=state_count, name="energy")
    if bounds is not None:
        if type(bounds) is not EnergyBoundConsequences:
            raise TypeError("bounds must be an exact EnergyBoundConsequences")
        if np.any(np.abs(values) > bounds.value_bound):
            raise ValueError("energy values violate the declared global bound")
    per_state, loss, gradient, hessian, tilted, edge_count = (
        _finite_jump_flux_arrays(probabilities, generator, values)
    )
    return FiniteJumpFluxEvaluation(
        energy=values,
        marginal=probabilities,
        invariant_reference=reference,
        reference_jump_generator=generator,
        per_state_loss=per_state,
        loss=loss,
        gradient=gradient,
        hessian=hessian,
        tilted_generator=tilted,
        state_count=state_count,
        edge_count=edge_count,
    )


def finite_jump_flux_excess(
    marginal: object,
    invariant_reference: object,
    reference_jump_generator: object,
    candidate_energy: object,
) -> FiniteJumpFluxExcess:
    """Compare direct and stable nonnegative jump-flux excess formulas."""

    reversal = finite_exact_energy_reversal(
        reference_jump_generator,
        marginal,
        invariant_reference,
    )
    exact_evaluation = finite_jump_flux_objective(
        reversal.marginal,
        reversal.invariant_reference,
        reference_jump_generator,
        reversal.relative_energy,
    )
    candidate = _energy_vector(
        candidate_energy,
        state_count=reversal.state_count,
        name="candidate_energy",
    )
    candidate_evaluation = finite_jump_flux_objective(
        reversal.marginal,
        reversal.invariant_reference,
        reference_jump_generator,
        candidate,
    )
    error = candidate - reversal.relative_energy
    sources, destinations = _off_diagonal_edges(
        reversal.energy_tilted_generator
    )
    terms = []
    for raw_source, raw_destination in zip(sources, destinations):
        source = int(raw_source)
        destination = int(raw_destination)
        reverse_flux = _checked_positive_product(
            float(reversal.marginal[source]),
            float(reversal.energy_tilted_generator[source, destination]),
            name="exact reverse marginal flux",
        )
        bregman = _exponential_bregman(
            float(error[destination] - error[source])
        )
        terms.append(
            _checked_positive_product(
                reverse_flux,
                bregman,
                name="jump-flux Bregman contribution",
            )
        )
    stable = _checked_fsum(terms, name="stable jump-flux excess")
    direct = _checked_fsum(
        (candidate_evaluation.loss, -exact_evaluation.loss),
        name="direct jump-flux difference",
    )
    residual = _checked_fsum(
        (direct, -stable),
        name="jump-flux excess identity residual",
    )
    exact_gradient_norm = float(np.max(np.abs(exact_evaluation.gradient)))
    return FiniteJumpFluxExcess(
        exact_loss=exact_evaluation.loss,
        candidate_loss=candidate_evaluation.loss,
        direct_difference=direct,
        stable_excess=stable,
        identity_residual=residual,
        exact_gradient_infinity_norm=exact_gradient_norm,
        energy_error=error,
    )


def jump_flux_measure_integral(
    reference_measure_weights: object,
    energy_differences: object,
) -> float:
    """Evaluate an unnormalized finite/quadrature jump reference integral."""

    weights = _numeric_vector(
        reference_measure_weights,
        name="reference_measure_weights",
        maximum_items=MAX_REVERSE_OBJECTIVE_IMPORTANCE_TERMS,
    )
    differences = _numeric_vector(
        energy_differences,
        name="energy_differences",
        maximum_items=MAX_REVERSE_OBJECTIVE_IMPORTANCE_TERMS,
    )
    if differences.shape != weights.shape:
        raise ValueError("energy_differences must match reference_measure_weights")
    if np.any(weights < 0.0):
        raise ValueError("reference_measure_weights must be nonnegative")
    return _checked_fsum(
        (
            _jump_flux_term(float(weight), float(difference))
            for weight, difference in zip(weights, differences)
        ),
        name="jump-flux reference integral",
    )


def jump_flux_importance_contribution(
    edge_difference: object,
    *,
    target_time_density: object,
    proposal_time_density: object,
    reference_edge_density: object,
    proposal_edge_density: object,
) -> float:
    """Return one unnormalized ``(omega/tau)(dq/dR)`` contribution."""

    difference = _validated_real(
        edge_difference,
        name="edge_difference",
    )
    target_time = _validated_real(
        target_time_density,
        name="target_time_density",
        nonnegative=True,
    )
    proposal_time = _validated_real(
        proposal_time_density,
        name="proposal_time_density",
        strictly_positive=True,
    )
    reference_edge = _validated_real(
        reference_edge_density,
        name="reference_edge_density",
        nonnegative=True,
    )
    proposal_edge = _validated_real(
        proposal_edge_density,
        name="proposal_edge_density",
        strictly_positive=True,
    )
    if target_time == 0.0 or reference_edge == 0.0:
        return 0.0
    log_weight = _checked_fsum(
        (
            math.log(target_time),
            -math.log(proposal_time),
            math.log(reference_edge),
            -math.log(proposal_edge),
        ),
        name="jump importance log weight",
    )
    weight = _positive_from_log(log_weight, name="jump importance weight")
    return _jump_flux_term(weight, difference)


def factorized_jump_flux_importance_contribution(
    edge_difference: object,
    factors: JumpFluxProposalFactors,
) -> float:
    """Return one contribution from explicitly named proposal factors."""

    difference = _validated_real(edge_difference, name="edge_difference")
    if type(factors) is not JumpFluxProposalFactors:
        raise TypeError("factors must be an exact JumpFluxProposalFactors")
    weight = factors.importance_weight
    if weight == 0.0:
        return 0.0
    return _jump_flux_term(weight, difference)


def jump_flux_importance_estimate(
    reference_density_values: object,
    proposal_density_values: object,
    energy_differences: object,
) -> JumpFluxImportanceResult:
    """Average unnormalized ``q/R`` contributions at proposal draws.

    The caller is responsible for drawing the supplied points from the declared
    proposal.  This function never self-normalizes the weights.
    """

    reference = _numeric_vector(
        reference_density_values,
        name="reference_density_values",
        maximum_items=MAX_REVERSE_OBJECTIVE_IMPORTANCE_TERMS,
    )
    proposal = _numeric_vector(
        proposal_density_values,
        name="proposal_density_values",
        maximum_items=MAX_REVERSE_OBJECTIVE_IMPORTANCE_TERMS,
    )
    differences = _numeric_vector(
        energy_differences,
        name="energy_differences",
        maximum_items=MAX_REVERSE_OBJECTIVE_IMPORTANCE_TERMS,
    )
    if proposal.shape != reference.shape or differences.shape != reference.shape:
        raise ValueError("importance arrays must have identical shapes")
    if np.any(reference < 0.0) or np.any(proposal <= 0.0):
        raise ValueError(
            "reference densities must be nonnegative and proposal densities positive"
        )
    weights = []
    contributions = []
    for target, proposed, difference in zip(reference, proposal, differences):
        if target == 0.0:
            weights.append(0.0)
            contributions.append(0.0)
            continue
        log_weight = math.log(float(target)) - math.log(float(proposed))
        weight = _positive_from_log(log_weight, name="jump importance weight")
        weights.append(weight)
        contributions.append(_jump_flux_term(weight, float(difference)))
    estimate = _checked_mean(
        contributions,
        len(contributions),
        name="jump importance estimate",
    )
    return JumpFluxImportanceResult(
        importance_weights=np.asarray(weights, dtype=np.float64),
        contributions=np.asarray(contributions, dtype=np.float64),
        estimate=estimate,
        proposal_count=len(contributions),
    )


def tilted_jump_rate(
    base_rate: object,
    source_energy: object,
    destination_energy: object,
    *,
    bounds: Optional[EnergyBoundConsequences] = None,
) -> float:
    """Return ``q * exp(V_destination - V_source)`` without clipping."""

    rate = _validated_real(
        base_rate,
        name="base_rate",
        nonnegative=True,
    )
    source = _validated_real(source_energy, name="source_energy")
    destination = _validated_real(destination_energy, name="destination_energy")
    if bounds is not None:
        if type(bounds) is not EnergyBoundConsequences:
            raise TypeError("bounds must be an exact EnergyBoundConsequences")
        if abs(source) > bounds.value_bound or abs(destination) > bounds.value_bound:
            raise ValueError("energy value violates the declared global bound")
    if rate == 0.0:
        return 0.0
    difference = destination - source
    if not math.isfinite(difference):
        raise ArithmeticError("energy edge difference is not finite")
    if bounds is not None:
        if abs(difference) > bounds.edge_difference_bound:
            raise ValueError("energy edge difference violates the declared bound")
    if difference == 0.0:
        return rate
    result = _positive_from_log(
        math.log(rate) + difference,
        name="tilted jump rate",
    )
    if bounds is not None:
        envelope = bounds.tilted_rate_upper_bound(rate)
        if result > envelope:
            raise ArithmeticError(
                "tilted jump rate exceeds its outward-rounded bound"
            )
    return result


def reverse_energy_objective_value(
    continuous: object,
    jump: object,
    *,
    jump_weight: object,
) -> ReverseEnergyObjectiveValue:
    """Combine ``L_C + lambda_J L_J`` with a positive jump weight."""

    continuous_value = _validated_real(continuous, name="continuous")
    jump_value = _validated_real(jump, name="jump")
    weight = _validated_real(
        jump_weight,
        name="jump_weight",
        strictly_positive=True,
    )
    weighted_jump = _checked_signed_product(
        weight,
        jump_value,
        name="weighted jump objective",
    )
    total = _checked_fsum(
        (continuous_value, weighted_jump),
        name="combined reverse-energy objective",
    )
    return ReverseEnergyObjectiveValue(
        continuous=continuous_value,
        jump=jump_value,
        jump_weight=weight,
        total=total,
    )


__all__ = [
    "ContinuousScoreExcessResult",
    "ContinuousScoreMatchingResult",
    "DETAILED_BALANCE_LOG_ATOL",
    "EnergyBoundConsequences",
    "FiniteEnergyReversal",
    "FiniteJumpFluxEvaluation",
    "FiniteJumpFluxExcess",
    "JumpFluxImportanceResult",
    "JumpFluxProposalFactors",
    "MAX_REVERSE_OBJECTIVE_COORDINATES",
    "MAX_REVERSE_OBJECTIVE_EXACT_FALLBACK_COORDINATES",
    "MAX_REVERSE_OBJECTIVE_IMPORTANCE_TERMS",
    "MAX_REVERSE_OBJECTIVE_SAMPLES",
    "MAX_REVERSE_OBJECTIVE_STATES",
    "ReverseEnergyObjectiveValue",
    "finite_exact_energy_reversal",
    "finite_jump_flux_excess",
    "finite_jump_flux_objective",
    "finite_relative_energy",
    "factorized_jump_flux_importance_contribution",
    "gaussian_reference_reverse_drift",
    "gaussian_relative_score_excess",
    "gaussian_relative_score_matching",
    "jump_flux_importance_contribution",
    "jump_flux_importance_estimate",
    "jump_flux_measure_integral",
    "reverse_energy_objective_value",
    "tilted_jump_rate",
    "validate_finite_energy_gauge_shift",
]
