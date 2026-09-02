"""Exact reversible reference dynamics on heterogeneous event configurations.

The process implemented here is the executable reference process for the
general hybrid framework.  Continuous event coordinates follow a
variance-preserving Ornstein--Uhlenbeck clock.  A separate scalar clock drives
constant-rate births, per-occurrence deaths, and reversible type replacements.

The capped-Poisson reference law is invariant at every physical time.  This is
enforced structurally: the birth rate is derived as ``theta * delta`` and each
directed replacement rate is derived from a symmetric reference flux.  The
event-driven simulator analytically inverts the piecewise-constant jump clock;
it does not discretize time or numerically root-find a waiting time.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
import math
from numbers import Integral, Real
from types import MappingProxyType
from typing import Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
    MAX_CONFIGURATION_CARDINALITY,
    MIN_REFERENCE_CATEGORICAL_PROBABILITY,
    TransformedConfiguration,
    TransformedEvent,
    UnsupportedReferenceSamplingError,
)
from heterodiff.theory.finite_atomic_counting import (
    FiniteAtomicCountingSpace,
    finite_atomic_generator,
)


MAX_HYBRID_SCHEDULE_SEGMENTS = 10_000
MAX_HYBRID_REPLACEMENT_EDGES = 100_000
MAX_HYBRID_PATH_JUMPS = 100_000
MAX_HYBRID_STATE_COORDINATES = 4_000_000
MAX_HYBRID_RECORDED_EVENT_COORDINATES = 4_000_000

_MIN_NORMAL_FLOAT64 = float(np.finfo(np.float64).tiny)
_CATEGORICAL_ACCUMULATION_FACTOR = 32.0
_CATEGORICAL_INCREMENT_RTOL = 0.125
_MAX_PROCESS_KEY_NODES = 1_000_000
_MAX_PROCESS_KEY_DEPTH = 32


class UnsupportedHybridSamplingError(ValueError):
    """Raised when a valid law is below the frozen finite-RNG resolution."""


class HybridPathLimitError(RuntimeError):
    """Raised instead of returning a trajectory truncated at a jump limit."""


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
    strictly_positive: bool,
) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % name)
    if strictly_positive:
        if result <= 0.0:
            raise ValueError("%s must be strictly positive" % name)
        if result < _MIN_NORMAL_FLOAT64:
            raise ArithmeticError("%s must be a normal float64 value" % name)
    elif result < 0.0:
        raise ValueError("%s must be nonnegative" % name)
    elif 0.0 < result < _MIN_NORMAL_FLOAT64:
        raise ArithmeticError("%s must be zero or a normal float64 value" % name)
    return result


def _immutable_float_array(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    return np.frombuffer(array.tobytes(order="C"), dtype=np.float64).reshape(
        array.shape
    )


def _checked_positive_product(left: float, right: float, *, name: str) -> float:
    product = left * right
    if not math.isfinite(product):
        raise ArithmeticError("%s is not finite" % name)
    if product <= 0.0 or product < _MIN_NORMAL_FLOAT64:
        raise ArithmeticError("positive %s is not a normal float64 value" % name)
    return product


def _checked_fsum(values: Iterable[float], *, name: str) -> float:
    try:
        result = math.fsum(values)
    except OverflowError as error:
        raise ArithmeticError("%s overflowed" % name) from error
    if not math.isfinite(result):
        raise ArithmeticError("%s is not finite" % name)
    if 0.0 < result < _MIN_NORMAL_FLOAT64:
        raise ArithmeticError("positive %s is not a normal float64 value" % name)
    return result


def _positive_fraction_product3(
    first: float, second: float, third: Fraction
) -> Fraction:
    """Return an exact positive product with a rational duration factor."""

    product = (
        Fraction.from_float(first)
        * Fraction.from_float(second)
        * third
    )
    if product <= 0:
        raise ArithmeticError("internal positive hazard product is not positive")
    return product


def _ou_conditional_mean(value: float, clock: float, decay: float) -> float:
    """Evaluate ``value * exp(-clock/2)`` across exponent edge cases."""

    if value == 0.0:
        return value
    direct = decay * value
    if decay == 1.0 and clock > 0.0:
        # exp can round to one while expm1 still resolves the decrement.
        result = value + value * math.expm1(-0.5 * clock)
    elif direct == 0.0:
        # exp can underflow before multiplication even when the product with a
        # large finite coordinate is representable.
        log_magnitude = math.log(abs(value)) - 0.5 * clock
        try:
            magnitude = math.exp(log_magnitude)
        except OverflowError as error:
            raise ArithmeticError("OU conditional mean overflowed") from error
        result = math.copysign(magnitude, value)
    else:
        result = direct
    if not math.isfinite(result):
        raise ArithmeticError("OU conditional mean is not finite")
    return 0.0 if result == 0.0 else result


def _validated_rng(rng: object) -> np.random.Generator:
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator")
    return rng


def _validated_type_id(reference: CappedPoissonConfigurationReference, value: object) -> int:
    type_id = _validated_integer(
        value,
        name="event type id",
        minimum=0,
        maximum=2**63 - 1,
    )
    if type_id not in reference.type_dimensions:
        raise ValueError("unknown event type %d" % type_id)
    return type_id


def _validate_plain_immutable_key(
    value: object,
    *,
    remaining_nodes: List[int],
    depth: int = 0,
) -> None:
    if depth > _MAX_PROCESS_KEY_DEPTH:
        raise ValueError("process_key nesting exceeds the implementation limit")
    remaining_nodes[0] -= 1
    if remaining_nodes[0] < 0:
        raise ValueError("process_key exceeds the implementation size limit")
    if type(value) is tuple:
        for item in value:
            _validate_plain_immutable_key(
                item,
                remaining_nodes=remaining_nodes,
                depth=depth + 1,
            )
        return
    if type(value) is str:
        if len(value) > 4_096:
            raise ValueError("process_key text exceeds the implementation limit")
        return
    if type(value) is int:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("process_key floats must be finite")
        return
    raise TypeError("process_key must contain only immutable plain-data values")


class HybridJumpKind(str, Enum):
    """Primitive discrete edit families."""

    BIRTH = "birth"
    DEATH = "death"
    REPLACEMENT = "replacement"


@dataclass(frozen=True, eq=False, init=False)
class PiecewiseConstantHybridSchedule:
    """Two nonnegative clocks on one finite piecewise-constant time grid.

    At an interior breakpoint, the public pointwise value is the value on the
    segment immediately to its left.  Waiting-time searches starting exactly
    at a breakpoint use the segment to its right.  The isolated point
    convention has no effect on either integral.
    """

    time_grid: np.ndarray = field(repr=False)
    continuous_rates: np.ndarray = field(repr=False)
    jump_rates: np.ndarray = field(repr=False)
    clean_hold: float
    _continuous_segment_areas: np.ndarray = field(repr=False)
    _jump_segment_areas: np.ndarray = field(repr=False)

    def __init__(
        self,
        time_grid: object,
        continuous_rates: object,
        jump_rates: object,
        *,
        clean_hold: float,
    ) -> None:
        raw_grid = _bounded_tuple(
            time_grid,
            name="time_grid schedule segments",
            maximum_items=MAX_HYBRID_SCHEDULE_SEGMENTS + 1,
        )
        if len(raw_grid) < 2:
            raise ValueError("time_grid must define at least one segment")
        grid = tuple(
            _validated_real(value, name="time_grid entry", strictly_positive=False)
            for value in raw_grid
        )
        if grid[0] != 0.0:
            raise ValueError("time_grid must begin exactly at zero")
        if any(right <= left for left, right in zip(grid[:-1], grid[1:])):
            raise ValueError("time_grid must be strictly increasing")
        if len(grid) - 1 > MAX_HYBRID_SCHEDULE_SEGMENTS:
            raise ValueError(
                "schedule segment count exceeds the implementation limit of %d"
                % MAX_HYBRID_SCHEDULE_SEGMENTS
            )

        hold = _validated_real(
            clean_hold,
            name="clean_hold",
            strictly_positive=True,
        )
        if hold >= grid[-1]:
            raise ValueError("clean_hold must lie strictly inside the time horizon")
        if hold not in grid:
            raise ValueError("clean_hold must be represented by an exact grid breakpoint")

        raw_continuous = _bounded_tuple(
            continuous_rates,
            name="continuous_rates",
            maximum_items=MAX_HYBRID_SCHEDULE_SEGMENTS + 1,
        )
        raw_jump = _bounded_tuple(
            jump_rates,
            name="jump_rates",
            maximum_items=MAX_HYBRID_SCHEDULE_SEGMENTS + 1,
        )
        expected = len(grid) - 1
        if len(raw_continuous) != expected or len(raw_jump) != expected:
            raise ValueError(
                "continuous_rates and jump_rates must have one entry per segment"
            )
        continuous = tuple(
            _validated_real(
                value,
                name="continuous schedule rate",
                strictly_positive=False,
            )
            for value in raw_continuous
        )
        jumps = tuple(
            _validated_real(
                value,
                name="jump schedule rate",
                strictly_positive=False,
            )
            for value in raw_jump
        )

        continuous_areas = []
        jump_areas = []
        for index, (left, right) in enumerate(zip(grid[:-1], grid[1:])):
            in_hold = right <= hold
            if in_hold:
                if continuous[index] != 0.0 or jumps[index] != 0.0:
                    raise ValueError("both schedules must vanish exactly on the clean hold")
                continuous_areas.append(0.0)
                jump_areas.append(0.0)
                continue
            if left < hold:
                raise ArithmeticError("clean_hold did not split a schedule segment")
            if continuous[index] <= 0.0 or jumps[index] <= 0.0:
                raise ValueError("both schedules must be strictly positive on active segments")
            duration = right - left
            if duration <= 0.0 or not math.isfinite(duration):
                raise ArithmeticError("schedule duration is not positive and finite")
            continuous_areas.append(
                _checked_positive_product(
                    continuous[index], duration, name="continuous segment area"
                )
            )
            jump_areas.append(
                _checked_positive_product(jumps[index], duration, name="jump segment area")
            )

        _checked_fsum(continuous_areas, name="full continuous clock")
        _checked_fsum(jump_areas, name="full jump clock")

        object.__setattr__(self, "time_grid", _immutable_float_array(grid))
        object.__setattr__(
            self, "continuous_rates", _immutable_float_array(continuous)
        )
        object.__setattr__(self, "jump_rates", _immutable_float_array(jumps))
        object.__setattr__(self, "clean_hold", hold)
        object.__setattr__(
            self, "_continuous_segment_areas", _immutable_float_array(continuous_areas)
        )
        object.__setattr__(
            self, "_jump_segment_areas", _immutable_float_array(jump_areas)
        )

    @property
    def horizon(self) -> float:
        """Final physical time."""

        return float(self.time_grid[-1])

    @property
    def segment_count(self) -> int:
        """Number of constant schedule segments."""

        return int(self.continuous_rates.size)

    def _time(self, value: object, *, name: str) -> float:
        result = _validated_real(value, name=name, strictly_positive=False)
        if result > self.horizon:
            raise ValueError("%s must lie within [0, horizon]" % name)
        return result

    def _interval(self, start_time: object, end_time: object) -> Tuple[float, float]:
        start = self._time(start_time, name="start_time")
        end = self._time(end_time, name="end_time")
        if end < start:
            raise ValueError("end_time must not precede start_time")
        return start, end

    def _rate(self, values: np.ndarray, time: object) -> float:
        point = self._time(time, name="time")
        position = int(np.searchsorted(self.time_grid, point, side="left")) - 1
        if position < 0:
            position = 0
        return float(values[position])

    def continuous_rate(self, time: float) -> float:
        """Return the frozen left-continuous OU clock value at ``time``."""

        return self._rate(self.continuous_rates, time)

    def jump_rate(self, time: float) -> float:
        """Return the frozen left-continuous jump clock value at ``time``."""

        return self._rate(self.jump_rates, time)

    def _integral(
        self,
        values: np.ndarray,
        segment_areas: np.ndarray,
        start_time: object,
        end_time: object,
        *,
        name: str,
    ) -> float:
        start, end = self._interval(start_time, end_time)
        if start == end:
            return 0.0

        start_index = int(
            np.searchsorted(self.time_grid, start, side="right")
        ) - 1
        end_index = int(np.searchsorted(self.time_grid, end, side="left")) - 1
        start_index = max(0, min(start_index, self.segment_count - 1))
        end_index = max(0, min(end_index, self.segment_count - 1))

        if start_index == end_index:
            rate = float(values[start_index])
            if rate == 0.0:
                return 0.0
            return _checked_positive_product(
                rate, end - start, name="integrated %s clock" % name
            )

        terms = []
        first_duration = float(self.time_grid[start_index + 1]) - start
        if float(values[start_index]) > 0.0 and first_duration > 0.0:
            terms.append(
                _checked_positive_product(
                    float(values[start_index]),
                    first_duration,
                    name="initial partial %s clock" % name,
                )
            )
        terms.extend(
            float(value)
            for value in segment_areas[start_index + 1 : end_index]
            if float(value) > 0.0
        )
        final_duration = end - float(self.time_grid[end_index])
        if float(values[end_index]) > 0.0 and final_duration > 0.0:
            terms.append(
                _checked_positive_product(
                    float(values[end_index]),
                    final_duration,
                    name="final partial %s clock" % name,
                )
            )
        return _checked_fsum(terms, name="integrated %s clock" % name)

    def continuous_integral(self, start_time: float, end_time: float) -> float:
        """Return ``integral gamma_C`` on the requested interval."""

        return self._integral(
            self.continuous_rates,
            self._continuous_segment_areas,
            start_time,
            end_time,
            name="continuous",
        )

    def jump_integral(self, start_time: float, end_time: float) -> float:
        """Return ``integral gamma_J`` on the requested interval."""

        return self._integral(
            self.jump_rates,
            self._jump_segment_areas,
            start_time,
            end_time,
            name="jump",
        )

    def invert_jump_hazard(
        self,
        start_time: float,
        end_time: float,
        *,
        base_exit_rate: float,
        exponential_hazard: float,
    ) -> Optional[float]:
        """Invert ``base_exit_rate * integral gamma_J`` segment by segment.

        Segment comparisons use the exact binary-rational values of the
        supplied float64 parameters. Equality in that semantics yields a jump
        at the breakpoint or horizon. ``None`` means the requested hazard
        strictly exceeds the exact segment sum before ``end_time``; a rounded
        product of :meth:`jump_integral` is not an equality certificate.
        """

        start, end = self._interval(start_time, end_time)
        base_rate = _validated_real(
            base_exit_rate,
            name="base_exit_rate",
            strictly_positive=False,
        )
        residual = _validated_real(
            exponential_hazard,
            name="exponential_hazard",
            strictly_positive=True,
        )
        if start == end or base_rate == 0.0:
            return None

        cursor = start
        residual_exact = Fraction.from_float(residual)
        base_exact = Fraction.from_float(base_rate)
        first_index = int(np.searchsorted(self.time_grid, cursor, side="right")) - 1
        if first_index < 0:
            first_index = 0
        for index in range(first_index, self.segment_count):
            segment_left = max(cursor, float(self.time_grid[index]))
            segment_right = min(end, float(self.time_grid[index + 1]))
            if segment_right <= segment_left:
                if segment_left >= end:
                    break
                continue
            clock_rate = float(self.jump_rates[index])
            cursor = segment_left
            if clock_rate == 0.0:
                cursor = segment_right
                if cursor >= end:
                    break
                continue
            exact_duration = (
                Fraction.from_float(segment_right)
                - Fraction.from_float(cursor)
            )
            segment_hazard = _positive_fraction_product3(
                base_rate,
                clock_rate,
                exact_duration,
            )
            if residual_exact == segment_hazard:
                return segment_right
            if residual_exact < segment_hazard:
                exact_increment = (
                    residual_exact
                    / base_exact
                    / Fraction.from_float(clock_rate)
                )
                try:
                    candidate = float(
                        Fraction.from_float(cursor) + exact_increment
                    )
                except OverflowError as error:
                    raise UnsupportedHybridSamplingError(
                        "positive waiting time is not representable"
                    ) from error
                if not math.isfinite(candidate) or candidate <= cursor:
                    raise UnsupportedHybridSamplingError(
                        "positive waiting time is not representable"
                    )
                if candidate >= segment_right:
                    raise UnsupportedHybridSamplingError(
                        "waiting time cannot be resolved below the next breakpoint"
                    )
                return candidate
            residual_exact -= segment_hazard
            cursor = segment_right
            if cursor >= end:
                break
        return None

    def parameter_key(self) -> Tuple[object, ...]:
        """Return a deterministic plain-data description of both clocks."""

        return (
            "piecewise-constant-hybrid-schedule-v1",
            tuple(float(value) for value in self.time_grid),
            tuple(float(value) for value in self.continuous_rates),
            tuple(float(value) for value in self.jump_rates),
            self.clean_hold,
        )


@dataclass(frozen=True, eq=False, init=False)
class ReversibleHybridRates:
    """Balanced birth/death and sparse type-replacement rates."""

    reference_key: Tuple[object, ...]
    birth_rate: float
    per_particle_death_rate: float
    replacement_fluxes: Mapping[Tuple[int, int], float]
    replacement_rates: Mapping[Tuple[int, int], float]
    _outgoing_rates: Mapping[int, float] = field(repr=False)
    _adjacency: Mapping[int, Tuple[Tuple[int, float], ...]] = field(repr=False)

    def __init__(
        self,
        reference: CappedPoissonConfigurationReference,
        *,
        per_particle_death_rate: float,
        replacement_fluxes: Optional[Mapping[Tuple[int, int], float]] = None,
    ) -> None:
        if type(reference) is not CappedPoissonConfigurationReference:
            raise TypeError("reference must be an exact CappedPoissonConfigurationReference")
        delta = _validated_real(
            per_particle_death_rate,
            name="per_particle_death_rate",
            strictly_positive=True,
        )
        beta = _checked_positive_product(
            reference.activity, delta, name="balanced birth rate"
        )
        if replacement_fluxes is None:
            raw_items: Tuple[object, ...] = ()
        else:
            if not isinstance(replacement_fluxes, Mapping):
                raise TypeError("replacement_fluxes must be a mapping or None")
            raw_items = _bounded_tuple(
                replacement_fluxes.items(),
                name="replacement_fluxes",
                maximum_items=MAX_HYBRID_REPLACEMENT_EDGES,
            )

        fluxes = {}
        directed = {}
        adjacency_lists = {type_id: [] for type_id in reference.type_ids}
        for raw_item in raw_items:
            raw_key, raw_flux = raw_item  # mapping items are exact pairs by contract
            if type(raw_key) is not tuple or len(raw_key) != 2:
                raise TypeError(
                    "replacement_fluxes keys must be exact (lower, upper) tuples"
                )
            lower = _validated_type_id(reference, raw_key[0])
            upper = _validated_type_id(reference, raw_key[1])
            if lower >= upper:
                raise ValueError(
                    "replacement flux keys must satisfy lower_type_id < upper_type_id"
                )
            edge = (lower, upper)
            if edge in fluxes:
                raise ValueError("replacement_fluxes contains a duplicate edge")
            flux = _validated_real(
                raw_flux,
                name="replacement flux (%d, %d)" % edge,
                strictly_positive=True,
            )
            forward = flux / reference.type_weights[lower]
            reverse = flux / reference.type_weights[upper]
            if (
                not math.isfinite(forward)
                or not math.isfinite(reverse)
                or forward < _MIN_NORMAL_FLOAT64
                or reverse < _MIN_NORMAL_FLOAT64
            ):
                raise ArithmeticError("a derived directed replacement rate is invalid")
            fluxes[edge] = flux
            directed[(lower, upper)] = forward
            directed[(upper, lower)] = reverse
            adjacency_lists[lower].append((upper, forward))
            adjacency_lists[upper].append((lower, reverse))

        adjacency = {}
        outgoing = {}
        for source in reference.type_ids:
            edges = tuple(sorted(adjacency_lists[source]))
            adjacency[source] = edges
            outgoing[source] = _checked_fsum(
                (rate for _, rate in edges),
                name="outgoing replacement rate",
            )

        object.__setattr__(self, "reference_key", reference.parameter_key())
        object.__setattr__(self, "birth_rate", beta)
        object.__setattr__(self, "per_particle_death_rate", delta)
        object.__setattr__(
            self, "replacement_fluxes", MappingProxyType(dict(sorted(fluxes.items())))
        )
        object.__setattr__(
            self, "replacement_rates", MappingProxyType(dict(sorted(directed.items())))
        )
        object.__setattr__(
            self, "_outgoing_rates", MappingProxyType(dict(outgoing))
        )
        object.__setattr__(self, "_adjacency", MappingProxyType(dict(adjacency)))

    def replacement_rate(self, source_type: int, destination_type: int) -> float:
        source = _validated_integer(
            source_type,
            name="source_type",
            minimum=0,
            maximum=2**63 - 1,
        )
        destination = _validated_integer(
            destination_type,
            name="destination_type",
            minimum=0,
            maximum=2**63 - 1,
        )
        if (
            source not in self._outgoing_rates
            or destination not in self._outgoing_rates
        ):
            raise ValueError("replacement types must be declared by the reference")
        if source == destination:
            return 0.0
        return float(self.replacement_rates.get((source, destination), 0.0))

    def outgoing_replacement_rate(self, source_type: int) -> float:
        source = _validated_integer(
            source_type,
            name="source_type",
            minimum=0,
            maximum=2**63 - 1,
        )
        try:
            return float(self._outgoing_rates[source])
        except KeyError as error:
            raise ValueError("source_type is not declared by the reference") from error

    def replacement_destinations(
        self, source_type: int
    ) -> Tuple[Tuple[int, float], ...]:
        """Return the immutable positive sparse row for one source type."""

        source = _validated_integer(
            source_type,
            name="source_type",
            minimum=0,
            maximum=2**63 - 1,
        )
        try:
            return self._adjacency[source]
        except KeyError as error:
            raise ValueError("source_type is not declared by the reference") from error

    def parameter_key(self) -> Tuple[object, ...]:
        """Return the exact reference key and sparse balanced parameters."""

        return (
            "reversible-hybrid-rates-v1",
            self.reference_key,
            self.per_particle_death_rate,
            tuple(self.replacement_fluxes.items()),
        )


@dataclass(frozen=True)
class HybridJumpRates:
    """Unscaled conditional rate decomposition at one configuration."""

    birth: float
    death: float
    replacement: float
    total: float

    def __post_init__(self) -> None:
        values = (
            _validated_real(self.birth, name="birth", strictly_positive=False),
            _validated_real(self.death, name="death", strictly_positive=False),
            _validated_real(
                self.replacement,
                name="replacement",
                strictly_positive=False,
            ),
            _validated_real(self.total, name="total", strictly_positive=False),
        )
        expected = _checked_fsum(values[:3], name="total jump rate")
        if values[3] != expected:
            raise ValueError("total must exactly equal the stable sum of component rates")
        for name, value in zip(("birth", "death", "replacement", "total"), values):
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class HybridJumpRecord:
    """Compact audit record for one accepted jump."""

    time: float
    kind: HybridJumpKind
    exponential_hazard: float
    base_rates: HybridJumpRates
    cardinality_before: int
    source_event: Optional[TransformedEvent] = None
    destination_event: Optional[TransformedEvent] = None

    def __post_init__(self) -> None:
        time = _validated_real(self.time, name="jump time", strictly_positive=False)
        if type(self.kind) is not HybridJumpKind:
            raise TypeError("kind must be an exact HybridJumpKind")
        hazard = _validated_real(
            self.exponential_hazard,
            name="exponential_hazard",
            strictly_positive=True,
        )
        if type(self.base_rates) is not HybridJumpRates:
            raise TypeError("base_rates must be an exact HybridJumpRates")
        cardinality = _validated_integer(
            self.cardinality_before,
            name="cardinality_before",
            minimum=0,
            maximum=MAX_CONFIGURATION_CARDINALITY,
        )
        for name, event in (
            ("source_event", self.source_event),
            ("destination_event", self.destination_event),
        ):
            if event is not None and type(event) is not TransformedEvent:
                raise TypeError("%s must be an exact TransformedEvent or None" % name)

        if self.kind is HybridJumpKind.BIRTH:
            if self.source_event is not None or self.destination_event is None:
                raise ValueError("birth records require only a destination event")
            if self.base_rates.birth <= 0.0:
                raise ValueError("a birth record requires a positive birth rate")
            if cardinality >= MAX_CONFIGURATION_CARDINALITY:
                raise ValueError("a birth record cannot begin at the global cardinality limit")
        elif self.kind is HybridJumpKind.DEATH:
            if self.source_event is None or self.destination_event is not None:
                raise ValueError("death records require only a source event")
            if cardinality < 1 or self.base_rates.death <= 0.0:
                raise ValueError("a death record requires an occupied state and rate")
        else:
            if self.source_event is None or self.destination_event is None:
                raise ValueError("replacement records require source and destination events")
            if self.source_event.event_type == self.destination_event.event_type:
                raise ValueError("replacement records require distinct event types")
            if cardinality < 1 or self.base_rates.replacement <= 0.0:
                raise ValueError(
                    "a replacement record requires an occupied state and rate"
                )

        object.__setattr__(self, "time", time)
        object.__setattr__(self, "exponential_hazard", hazard)
        object.__setattr__(self, "cardinality_before", cardinality)


@dataclass(frozen=True, eq=False)
class HybridReferenceJumpProposal:
    """One conditional draw from the unscaled reference jump kernel.

    The proposal contains both canonical endpoint configurations and the
    primitive edit metadata required to evaluate an energy difference.  Its
    total reference mass is ``base_rates.total``; the physical-time factor
    ``gamma_J(s)`` is intentionally supplied by the objective caller.
    """

    process_key: Tuple[object, ...]
    source_configuration: TransformedConfiguration
    destination_configuration: TransformedConfiguration
    kind: HybridJumpKind
    base_rates: HybridJumpRates
    source_occurrence_index: Optional[int] = None
    source_event: Optional[TransformedEvent] = None
    destination_event: Optional[TransformedEvent] = None

    def __post_init__(self) -> None:
        if type(self.process_key) is not tuple:
            raise TypeError("process_key must be an immutable tuple")
        if (
            len(self.process_key) != 4
            or self.process_key[0] != "reversible-hybrid-reference-process-v1"
        ):
            raise ValueError("process_key does not identify this process contract")
        _validate_plain_immutable_key(
            self.process_key,
            remaining_nodes=[_MAX_PROCESS_KEY_NODES],
        )
        for name, configuration in (
            ("source_configuration", self.source_configuration),
            ("destination_configuration", self.destination_configuration),
        ):
            if type(configuration) is not tuple:
                raise TypeError("%s must be an immutable tuple" % name)
            if len(configuration) > MAX_CONFIGURATION_CARDINALITY:
                raise ValueError("%s exceeds the configuration cardinality limit" % name)
            if any(type(event) is not TransformedEvent for event in configuration):
                raise TypeError("%s must contain exact TransformedEvent values" % name)
            if (
                sum(len(event.coordinates) for event in configuration)
                > MAX_HYBRID_STATE_COORDINATES
            ):
                raise ValueError("%s exceeds the hybrid coordinate budget" % name)
            if tuple(sorted(configuration, key=TransformedEvent.model_key)) != configuration:
                raise ValueError("%s must be canonical" % name)
        if type(self.kind) is not HybridJumpKind:
            raise TypeError("kind must be an exact HybridJumpKind")
        if type(self.base_rates) is not HybridJumpRates:
            raise TypeError("base_rates must be an exact HybridJumpRates")
        if self.base_rates.total <= 0.0:
            raise ValueError("a jump proposal requires a positive total base rate")
        for name, event in (
            ("source_event", self.source_event),
            ("destination_event", self.destination_event),
        ):
            if event is not None and type(event) is not TransformedEvent:
                raise TypeError("%s must be an exact TransformedEvent or None" % name)

        source_index = None
        if self.source_occurrence_index is not None:
            if not self.source_configuration:
                raise ValueError(
                    "source_occurrence_index requires an occupied source"
                )
            source_index = _validated_integer(
                self.source_occurrence_index,
                name="source_occurrence_index",
                minimum=0,
                maximum=len(self.source_configuration) - 1,
            )
            object.__setattr__(self, "source_occurrence_index", source_index)

        expected = list(self.source_configuration)
        if self.kind is HybridJumpKind.BIRTH:
            if (
                source_index is not None
                or self.source_event is not None
                or self.destination_event is None
            ):
                raise ValueError("birth proposals require only a destination event")
            if self.base_rates.birth <= 0.0:
                raise ValueError("a birth proposal requires a positive birth rate")
            expected.append(self.destination_event)
        elif self.kind is HybridJumpKind.DEATH:
            if (
                source_index is None
                or self.source_event is None
                or self.destination_event is not None
            ):
                raise ValueError(
                    "death proposals require one indexed source event"
                )
            if self.base_rates.death <= 0.0:
                raise ValueError("a death proposal requires a positive death rate")
            if expected[source_index] != self.source_event:
                raise ValueError(
                    "death source event is absent at source_occurrence_index"
                )
            expected.pop(source_index)
        else:
            if (
                source_index is None
                or self.source_event is None
                or self.destination_event is None
            ):
                raise ValueError(
                    "replacement proposals require one indexed source and "
                    "one destination event"
                )
            if self.source_event.event_type == self.destination_event.event_type:
                raise ValueError("replacement proposals require distinct event types")
            if self.base_rates.replacement <= 0.0:
                raise ValueError(
                    "a replacement proposal requires a positive replacement rate"
                )
            if expected[source_index] != self.source_event:
                raise ValueError(
                    "replacement source event is absent at "
                    "source_occurrence_index"
                )
            expected.pop(source_index)
            expected.append(self.destination_event)

        canonical_expected = tuple(sorted(expected, key=TransformedEvent.model_key))
        if canonical_expected != self.destination_configuration:
            raise ValueError(
                "destination_configuration is inconsistent with the declared edit"
            )


@dataclass(frozen=True, eq=False)
class HybridReferencePath:
    """Canonical endpoints and compact jump records for one trajectory."""

    process_key: Tuple[object, ...]
    start_time: float
    end_time: float
    initial_configuration: TransformedConfiguration
    jumps: Tuple[HybridJumpRecord, ...]
    terminal_configuration: TransformedConfiguration

    def __post_init__(self) -> None:
        if type(self.process_key) is not tuple:
            raise TypeError("process_key must be an immutable tuple")
        if (
            len(self.process_key) != 4
            or self.process_key[0] != "reversible-hybrid-reference-process-v1"
        ):
            raise ValueError("process_key does not identify this process contract")
        _validate_plain_immutable_key(
            self.process_key,
            remaining_nodes=[_MAX_PROCESS_KEY_NODES],
        )
        start = _validated_real(
            self.start_time, name="start_time", strictly_positive=False
        )
        end = _validated_real(self.end_time, name="end_time", strictly_positive=False)
        if end < start:
            raise ValueError("end_time must not precede start_time")
        for name, configuration in (
            ("initial_configuration", self.initial_configuration),
            ("terminal_configuration", self.terminal_configuration),
        ):
            if type(configuration) is not tuple:
                raise TypeError("%s must be an immutable tuple" % name)
            if any(type(event) is not TransformedEvent for event in configuration):
                raise TypeError("%s must contain exact TransformedEvent values" % name)
            if tuple(sorted(configuration, key=TransformedEvent.model_key)) != configuration:
                raise ValueError("%s must be canonical" % name)
            if len(configuration) > MAX_CONFIGURATION_CARDINALITY:
                raise ValueError("%s exceeds the configuration cardinality limit" % name)
            if (
                sum(len(event.coordinates) for event in configuration)
                > MAX_HYBRID_STATE_COORDINATES
            ):
                raise ValueError("%s exceeds the hybrid coordinate budget" % name)
        if type(self.jumps) is not tuple:
            raise TypeError("jumps must be an immutable tuple")
        if len(self.jumps) > MAX_HYBRID_PATH_JUMPS:
            raise ValueError("jumps exceeds the hybrid path limit")
        if any(type(record) is not HybridJumpRecord for record in self.jumps):
            raise TypeError("jumps must contain exact HybridJumpRecord values")

        cardinality = len(self.initial_configuration)
        type_counts = Counter(
            event.event_type for event in self.initial_configuration
        )
        previous_time = start
        recorded_coordinates = 0
        for record in self.jumps:
            if record.time <= previous_time or record.time > end:
                raise ValueError("jump times must strictly increase inside the path interval")
            if record.cardinality_before != cardinality:
                raise ValueError("jump cardinality_before is inconsistent with path history")
            recorded_coordinates += (
                (0 if record.source_event is None else len(record.source_event.coordinates))
                + (
                    0
                    if record.destination_event is None
                    else len(record.destination_event.coordinates)
                )
            )
            if recorded_coordinates > MAX_HYBRID_RECORDED_EVENT_COORDINATES:
                raise ValueError("jump records exceed the event-coordinate budget")
            if record.kind is HybridJumpKind.BIRTH:
                cardinality += 1
                type_counts[record.destination_event.event_type] += 1  # type: ignore[union-attr]
            elif record.kind is HybridJumpKind.DEATH:
                source_type = record.source_event.event_type  # type: ignore[union-attr]
                if type_counts[source_type] <= 0:
                    raise ValueError("death source type is absent from path history")
                type_counts[source_type] -= 1
                if type_counts[source_type] == 0:
                    del type_counts[source_type]
                cardinality -= 1
            else:
                source_type = record.source_event.event_type  # type: ignore[union-attr]
                destination_type = record.destination_event.event_type  # type: ignore[union-attr]
                if type_counts[source_type] <= 0:
                    raise ValueError("replacement source type is absent from path history")
                type_counts[source_type] -= 1
                if type_counts[source_type] == 0:
                    del type_counts[source_type]
                type_counts[destination_type] += 1
            if cardinality < 0 or cardinality > MAX_CONFIGURATION_CARDINALITY:
                raise ValueError("jump history leaves the admissible cardinality range")
            previous_time = record.time

        terminal_counts = Counter(
            event.event_type for event in self.terminal_configuration
        )
        if cardinality != len(self.terminal_configuration) or type_counts != terminal_counts:
            raise ValueError("terminal event types are inconsistent with jump history")
        object.__setattr__(self, "start_time", start)
        object.__setattr__(self, "end_time", end)

    @property
    def jump_count(self) -> int:
        """Number of accepted jumps, including a jump exactly at the horizon."""

        return len(self.jumps)


class ReversibleHybridReference:
    """Event-driven simulation of the exact reversible hybrid reference."""

    __slots__ = ("_reference", "_schedule", "_rates")

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("ReversibleHybridReference is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("ReversibleHybridReference is immutable")

    def __init__(
        self,
        reference: CappedPoissonConfigurationReference,
        schedule: PiecewiseConstantHybridSchedule,
        rates: ReversibleHybridRates,
    ) -> None:
        if type(reference) is not CappedPoissonConfigurationReference:
            raise TypeError("reference must be an exact CappedPoissonConfigurationReference")
        if type(schedule) is not PiecewiseConstantHybridSchedule:
            raise TypeError("schedule must be an exact PiecewiseConstantHybridSchedule")
        if type(rates) is not ReversibleHybridRates:
            raise TypeError("rates must be an exact ReversibleHybridRates")
        if rates.reference_key != reference.parameter_key():
            raise ValueError("rates and process reference parameters do not match")
        if (
            reference.total_cap * max(reference.type_dimensions.values())
            > MAX_HYBRID_STATE_COORDINATES
        ):
            raise ValueError(
                "the declared hybrid state space is not closed within the coordinate budget"
            )
        object.__setattr__(self, "_reference", reference)
        object.__setattr__(self, "_schedule", schedule)
        object.__setattr__(self, "_rates", rates)

    @property
    def reference(self) -> CappedPoissonConfigurationReference:
        """Immutable transformed configuration reference."""

        return self._reference

    @property
    def schedule(self) -> PiecewiseConstantHybridSchedule:
        """Immutable continuous and jump clock schedule."""

        return self._schedule

    @property
    def rates(self) -> ReversibleHybridRates:
        """Immutable balanced base-rate specification."""

        return self._rates

    def parameter_key(self) -> Tuple[object, ...]:
        """Return a deterministic plain-data key for the complete process."""

        return (
            "reversible-hybrid-reference-process-v1",
            self.reference.parameter_key(),
            self.schedule.parameter_key(),
            self.rates.parameter_key(),
        )

    def _canonical_state(
        self, events: Iterable[TransformedEvent]
    ) -> TransformedConfiguration:
        configuration = self.reference.canonicalize(events)
        coordinate_count = sum(len(event.coordinates) for event in configuration)
        if coordinate_count > MAX_HYBRID_STATE_COORDINATES:
            raise ValueError("configuration exceeds the hybrid state coordinate budget")
        return configuration

    def base_jump_rates(
        self, events: Iterable[TransformedEvent]
    ) -> HybridJumpRates:
        """Return birth, death, replacement, and total rates before scaling."""

        configuration = self._canonical_state(events)
        cardinality = len(configuration)
        birth = self.rates.birth_rate if cardinality < self.reference.total_cap else 0.0
        death = self.rates.per_particle_death_rate * cardinality
        if not math.isfinite(death):
            raise ArithmeticError("aggregate death rate is not finite")
        replacement = _checked_fsum(
            (
                self.rates.outgoing_replacement_rate(event.event_type)
                for event in configuration
            ),
            name="aggregate replacement rate",
        )
        total = _checked_fsum(
            (birth, death, replacement), name="aggregate base exit rate"
        )
        return HybridJumpRates(birth, death, replacement, total)

    def ou_transition(
        self,
        events: Iterable[TransformedEvent],
        start_time: float,
        end_time: float,
        *,
        rng: np.random.Generator,
    ) -> TransformedConfiguration:
        """Apply the exact segment-integrated OU transition to every event."""

        generator = _validated_rng(rng)
        configuration = self._canonical_state(events)
        integrated_clock = self.schedule.continuous_integral(start_time, end_time)
        if integrated_clock == 0.0:
            return configuration
        decay = math.exp(-0.5 * integrated_clock)
        sigma = math.sqrt(-math.expm1(-integrated_clock))
        if not math.isfinite(decay) or not math.isfinite(sigma):
            raise ArithmeticError("OU transition coefficients are not finite")

        transitioned = []
        for event in configuration:
            dimension = len(event.coordinates)
            if dimension == 0:
                transitioned.append(event)
                continue
            noise = np.asarray(generator.standard_normal(dimension), dtype=np.float64)
            if noise.shape != (dimension,) or np.any(~np.isfinite(noise)):
                raise ArithmeticError("OU noise draw is not finite and dimension-correct")
            coordinates = []
            for value, epsilon in zip(event.coordinates, noise):
                conditional_mean = _ou_conditional_mean(
                    value, integrated_clock, decay
                )
                result = conditional_mean + sigma * float(epsilon)
                if not math.isfinite(result):
                    raise ArithmeticError("OU transition produced a non-finite coordinate")
                coordinates.append(0.0 if result == 0.0 else result)
            transitioned.append(TransformedEvent(event.event_type, tuple(coordinates)))
        return self.reference.canonicalize(transitioned)

    @staticmethod
    def _categorical_index(
        weights: Sequence[float],
        *,
        rng: np.random.Generator,
        context: str,
    ) -> int:
        if not weights:
            raise ArithmeticError("%s categorical law has no positive categories" % context)
        total = _checked_fsum(weights, name="%s categorical total" % context)
        probabilities = np.asarray(
            [float(weight) / total for weight in weights], dtype=np.float64
        )
        if np.any(~np.isfinite(probabilities)):
            raise ArithmeticError("%s categorical probabilities are invalid" % context)
        if np.any(probabilities <= 0.0):
            raise UnsupportedHybridSamplingError(
                "%s law has a positive category below float64 normalization range"
                % context
            )
        floor = max(
            MIN_REFERENCE_CATEGORICAL_PROBABILITY,
            _CATEGORICAL_ACCUMULATION_FACTOR
            * len(weights)
            * float(np.finfo(np.float64).eps),
        )
        if float(np.min(probabilities)) < floor:
            raise UnsupportedHybridSamplingError(
                "%s law has a positive category below the finite-RNG sampling resolution"
                % context
            )
        cdf = np.cumsum(probabilities, dtype=np.float64)
        if np.any(~np.isfinite(cdf)):
            raise UnsupportedHybridSamplingError(
                "%s categorical CDF is not representable" % context
            )
        cdf[-1] = 1.0
        increments = np.diff(np.concatenate((np.zeros(1), cdf)))
        if np.any(increments <= 0.0) or np.any(
            np.abs(increments - probabilities) / probabilities
            > _CATEGORICAL_INCREMENT_RTOL
        ):
            raise UnsupportedHybridSamplingError(
                "%s categorical CDF is below the finite-RNG resolution" % context
            )
        uniform = float(rng.random())
        if not math.isfinite(uniform) or uniform < 0.0 or uniform >= 1.0:
            raise ArithmeticError("numpy Generator returned an invalid uniform draw")
        return int(np.searchsorted(cdf, uniform, side="right"))

    def _replacement_destination(
        self,
        source_type: int,
        *,
        rng: np.random.Generator,
    ) -> TransformedEvent:
        edges = self.rates._adjacency[source_type]
        edge_index = self._categorical_index(
            [rate for _, rate in edges],
            rng=rng,
            context="replacement destination",
        )
        destination_type = edges[edge_index][0]
        dimension = self.reference.type_dimensions[destination_type]
        if dimension == 0:
            return TransformedEvent(destination_type)
        noise = np.asarray(rng.standard_normal(dimension), dtype=np.float64)
        if noise.shape != (dimension,) or np.any(~np.isfinite(noise)):
            raise ArithmeticError(
                "replacement destination draw is not finite and dimension-correct"
            )
        return TransformedEvent(
            destination_type, tuple(float(value) for value in noise)
        )

    def _apply_jump(
        self,
        configuration: TransformedConfiguration,
        rates: HybridJumpRates,
        *,
        rng: np.random.Generator,
    ) -> Tuple[
        TransformedConfiguration,
        HybridJumpKind,
        Optional[int],
        Optional[TransformedEvent],
        Optional[TransformedEvent],
    ]:
        families = []
        family_weights = []
        for kind, weight in (
            (HybridJumpKind.BIRTH, rates.birth),
            (HybridJumpKind.DEATH, rates.death),
            (HybridJumpKind.REPLACEMENT, rates.replacement),
        ):
            if weight > 0.0:
                families.append(kind)
                family_weights.append(weight)
        family = families[
            self._categorical_index(
                family_weights, rng=rng, context="jump family"
            )
        ]
        mutable = list(configuration)
        source_occurrence_index = None
        source_event = None
        destination_event = None

        if family is HybridJumpKind.BIRTH:
            try:
                destination_event = self.reference.sample_event(rng)
            except UnsupportedReferenceSamplingError as error:
                raise UnsupportedHybridSamplingError(str(error)) from error
            mutable.append(destination_event)
        elif family is HybridJumpKind.DEATH:
            source_occurrence_index = int(rng.integers(len(mutable)))
            if (
                source_occurrence_index < 0
                or source_occurrence_index >= len(mutable)
            ):
                raise ArithmeticError("numpy Generator returned an invalid death index")
            source_event = mutable.pop(source_occurrence_index)
        else:
            positive_indices = []
            source_weights = []
            for index, event in enumerate(mutable):
                weight = self.rates.outgoing_replacement_rate(event.event_type)
                if weight > 0.0:
                    positive_indices.append(index)
                    source_weights.append(weight)
            selected = self._categorical_index(
                source_weights, rng=rng, context="replacement source"
            )
            source_occurrence_index = positive_indices[selected]
            source_event = mutable[source_occurrence_index]
            destination_event = self._replacement_destination(
                source_event.event_type, rng=rng
            )
            mutable[source_occurrence_index] = destination_event

        result = self._canonical_state(mutable)
        return (
            result,
            family,
            source_occurrence_index,
            source_event,
            destination_event,
        )

    def _simulate(
        self,
        events: Iterable[TransformedEvent],
        *,
        start_time: float,
        end_time: Optional[float],
        rng: np.random.Generator,
        max_jumps: int,
        record_path: bool,
    ) -> Tuple[
        float,
        float,
        TransformedConfiguration,
        Tuple[HybridJumpRecord, ...],
        TransformedConfiguration,
    ]:
        generator = _validated_rng(rng)
        limit = _validated_integer(
            max_jumps,
            name="max_jumps",
            minimum=1,
            maximum=MAX_HYBRID_PATH_JUMPS,
        )
        requested_end = self.schedule.horizon if end_time is None else end_time
        start, end = self.schedule._interval(start_time, requested_end)
        initial = self._canonical_state(events)
        state = initial
        records: List[HybridJumpRecord] = []
        accepted_jumps = 0
        recorded_coordinates = 0
        time = start

        while time < end:
            base_rates = self.base_jump_rates(state)
            if base_rates.total == 0.0 or end <= self.schedule.clean_hold:
                state = self.ou_transition(state, time, end, rng=generator)
                time = end
                break

            hazard = float(generator.exponential())
            if not math.isfinite(hazard) or hazard <= 0.0:
                raise UnsupportedHybridSamplingError(
                    "exponential waiting hazard must be positive and finite"
                )
            if hazard < _MIN_NORMAL_FLOAT64:
                raise UnsupportedHybridSamplingError(
                    "exponential waiting hazard is below float64 time resolution"
                )
            jump_time = self.schedule.invert_jump_hazard(
                time,
                end,
                base_exit_rate=base_rates.total,
                exponential_hazard=hazard,
            )
            if jump_time is None:
                state = self.ou_transition(state, time, end, rng=generator)
                time = end
                break
            if accepted_jumps >= limit:
                raise HybridPathLimitError(
                    "trajectory would exceed max_jumps; no truncated path was returned"
                )

            state = self.ou_transition(state, time, jump_time, rng=generator)
            cardinality_before = len(state)
            state, kind, _, source, destination = self._apply_jump(
                state, base_rates, rng=generator
            )
            if record_path:
                added_coordinates = (
                    (0 if source is None else len(source.coordinates))
                    + (0 if destination is None else len(destination.coordinates))
                )
                if (
                    recorded_coordinates + added_coordinates
                    > MAX_HYBRID_RECORDED_EVENT_COORDINATES
                ):
                    raise HybridPathLimitError(
                        "jump records exceed the event-coordinate allocation budget"
                    )
                recorded_coordinates += added_coordinates
                records.append(
                    HybridJumpRecord(
                        time=jump_time,
                        kind=kind,
                        exponential_hazard=hazard,
                        base_rates=base_rates,
                        cardinality_before=cardinality_before,
                        source_event=source,
                        destination_event=destination,
                    )
                )
            accepted_jumps += 1
            time = jump_time

        terminal = self.reference.canonicalize(state)
        public_records = tuple(records) if record_path else ()
        return start, end, initial, public_records, terminal

    def sample_endpoint(
        self,
        events: Iterable[TransformedEvent],
        *,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        rng: np.random.Generator,
        max_jumps: int = MAX_HYBRID_PATH_JUMPS,
    ) -> TransformedConfiguration:
        """Sample only the canonical endpoint using the exact path simulator."""

        _, _, _, _, terminal = self._simulate(
            events,
            start_time=start_time,
            end_time=end_time,
            rng=rng,
            max_jumps=max_jumps,
            record_path=False,
        )
        return terminal

    def sample_base_jump(
        self,
        events: Iterable[TransformedEvent],
        *,
        rng: np.random.Generator,
    ) -> HybridReferenceJumpProposal:
        """Draw one edit from ``q^0(x, dy) / Lambda^0(x)``.

        This is the unscaled conditional reference proposal used by the
        jump-flux objective.  It does not consume an exponential waiting-time
        draw and does not apply either schedule clock.
        """

        generator = _validated_rng(rng)
        source = self._canonical_state(events)
        base_rates = self.base_jump_rates(source)
        if base_rates.total <= 0.0:
            raise UnsupportedHybridSamplingError(
                "the source configuration has zero reference exit rate"
            )
        (
            destination,
            kind,
            source_occurrence_index,
            source_event,
            destination_event,
        ) = self._apply_jump(source, base_rates, rng=generator)
        proposal = HybridReferenceJumpProposal(
            process_key=self.parameter_key(),
            source_configuration=source,
            destination_configuration=destination,
            kind=kind,
            base_rates=base_rates,
            source_occurrence_index=source_occurrence_index,
            source_event=source_event,
            destination_event=destination_event,
        )
        return self.validate_jump_proposal(proposal)

    def validate_jump_proposal(
        self,
        proposal: HybridReferenceJumpProposal,
    ) -> HybridReferenceJumpProposal:
        """Bind a proposal record to this process and recompute its base rates."""

        if type(proposal) is not HybridReferenceJumpProposal:
            raise TypeError("proposal must be an exact HybridReferenceJumpProposal")
        if (
            proposal.source_occurrence_index is not None
            and type(proposal.source_occurrence_index) is not int
        ):
            raise TypeError("source_occurrence_index must be an exact int or None")
        # Frozen dataclasses are a convenience boundary, not a tamper proof.
        # Reconstruct the record so every edit/index/endpoint invariant is
        # checked again before a downstream objective or sampler can use it.
        checked_proposal = HybridReferenceJumpProposal(
            process_key=proposal.process_key,
            source_configuration=proposal.source_configuration,
            destination_configuration=proposal.destination_configuration,
            kind=proposal.kind,
            base_rates=proposal.base_rates,
            source_occurrence_index=proposal.source_occurrence_index,
            source_event=proposal.source_event,
            destination_event=proposal.destination_event,
        )
        if checked_proposal.process_key != self.parameter_key():
            raise ValueError("proposal process_key does not match this process")
        source = self._canonical_state(checked_proposal.source_configuration)
        self._canonical_state(checked_proposal.destination_configuration)
        expected_rates = self.base_jump_rates(source)
        if checked_proposal.base_rates != expected_rates:
            raise ValueError("proposal base_rates do not match its source configuration")
        if checked_proposal.kind is HybridJumpKind.REPLACEMENT:
            assert checked_proposal.source_event is not None
            assert checked_proposal.destination_event is not None
            primitive_rate = self.rates.replacement_rate(
                checked_proposal.source_event.event_type,
                checked_proposal.destination_event.event_type,
            )
            if primitive_rate <= 0.0:
                raise ValueError(
                    "proposal replacement edge is absent from the process"
                )
        return checked_proposal

    def sample_path(
        self,
        events: Iterable[TransformedEvent],
        *,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        rng: np.random.Generator,
        max_jumps: int = MAX_HYBRID_PATH_JUMPS,
    ) -> HybridReferencePath:
        """Sample canonical endpoints and compact auditable jump records."""

        start, end, initial, jumps, terminal = self._simulate(
            events,
            start_time=start_time,
            end_time=end_time,
            rng=rng,
            max_jumps=max_jumps,
            record_path=True,
        )
        return HybridReferencePath(
            process_key=self.parameter_key(),
            start_time=start,
            end_time=end,
            initial_configuration=initial,
            jumps=jumps,
            terminal_configuration=terminal,
        )

    def finite_atomic_oracle(
        self,
    ) -> Tuple[FiniteAtomicCountingSpace, np.ndarray, np.ndarray]:
        """Return exact all-atomic reference masses and unscaled generator."""

        space, _, masses = self.reference.finite_atomic_oracle()
        births = {
            type_id: _checked_positive_product(
                self.rates.birth_rate,
                self.reference.type_weights[type_id],
                name="finite-oracle primitive birth rate",
            )
            for type_id in self.reference.type_ids
        }
        deaths = {
            type_id: self.rates.per_particle_death_rate
            for type_id in self.reference.type_ids
        }
        replacements = {
            (source, destination): self.rates.replacement_rate(source, destination)
            for source in self.reference.type_ids
            for destination in self.reference.type_ids
            if source != destination
        }
        generator = finite_atomic_generator(space, births, deaths, replacements)
        return space, masses, generator


__all__ = [
    "HybridJumpKind",
    "HybridJumpRates",
    "HybridJumpRecord",
    "HybridPathLimitError",
    "HybridReferenceJumpProposal",
    "HybridReferencePath",
    "MAX_HYBRID_PATH_JUMPS",
    "MAX_HYBRID_RECORDED_EVENT_COORDINATES",
    "MAX_HYBRID_REPLACEMENT_EDGES",
    "MAX_HYBRID_SCHEDULE_SEGMENTS",
    "MAX_HYBRID_STATE_COORDINATES",
    "PiecewiseConstantHybridSchedule",
    "ReversibleHybridRates",
    "ReversibleHybridReference",
    "UnsupportedHybridSamplingError",
]
