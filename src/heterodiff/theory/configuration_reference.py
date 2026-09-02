"""Capped-Poisson reference on transformed heterogeneous event fibers.

The production state in this module is an unlabelled finite counting
configuration.  A transformed event has an integer stratum identifier and an
unpadded coordinate vector whose dimension is declared for that stratum.
Zero-dimensional strata are genuine atoms and repeated occurrences are legal.

For a one-event probability measure

``nu(d, dr) = w_d N(0, I_{k_d})(dr)``

and activity ``theta > 0``, :class:`CappedPoissonConfigurationReference`
implements

``Pi_N = Z_N(theta)^-1 sum_{n=0}^N theta^n/n! (Sigma_n)_# nu^n``.

This is a Poisson point process conditioned on cardinality at most ``N``.  It
is not a clipped Poisson law.  Density APIs name their reference measure
explicitly: count mass, Lebesgue--Poisson density, and singleton point mass are
different objects and must not be interchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from numbers import Integral, Real
from types import MappingProxyType
from typing import Iterable, Mapping, Optional, Tuple, Union

import numpy as np
from scipy.special import gammaln, logsumexp

from .finite_atomic_counting import (
    FiniteAtomicCountingSpace,
    capped_counting_reference,
)


TransformedCoordinates = Tuple[float, ...]
TransformedConfiguration = Tuple["TransformedEvent", ...]

MAX_CONFIGURATION_EVENT_TYPES = 4_096
MAX_TRANSFORMED_COORDINATE_DIMENSION = 65_536
MAX_CONFIGURATION_CARDINALITY = 100_000
MAX_REFERENCE_SAMPLE_SIZE = 100_000
MAX_REFERENCE_BATCH_OCCURRENCES = 500_000
MAX_REFERENCE_BATCH_COORDINATES = 4_000_000
MAX_REFERENCE_DENSITY_COORDINATES = 4_000_000
MAX_REPLACEMENT_BALANCE_TYPES = 256
MIN_REFERENCE_CATEGORICAL_PROBABILITY = 2.0**-40
TYPE_WEIGHT_SUM_ATOL = 1.0e-12
MAX_RANDOM_SEED = 2**64 - 1

_LOG_TWO_PI = math.log(2.0 * math.pi)
_LOG_MIN_NORMAL_FLOAT64 = math.log(float(np.finfo(np.float64).tiny))
_CATEGORICAL_ACCUMULATION_FACTOR = 32.0
_CATEGORICAL_INCREMENT_RTOL = 0.125


class UnsupportedReferenceSamplingError(ValueError):
    """Raised when a valid law exceeds the frozen finite-RNG resolution."""


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    return np.frombuffer(array.tobytes(order="C"), dtype=np.float64).reshape(
        array.shape
    )


def _categorical_sampling_floor(category_count: int) -> float:
    return max(
        MIN_REFERENCE_CATEGORICAL_PROBABILITY,
        _CATEGORICAL_ACCUMULATION_FACTOR
        * category_count
        * float(np.finfo(np.float64).eps),
    )


def _resolution_safe_cdf(probabilities: np.ndarray) -> Optional[np.ndarray]:
    category_count = int(probabilities.size)
    if category_count == 0:
        raise ArithmeticError("a categorical law must contain at least one category")
    if float(np.min(probabilities)) < _categorical_sampling_floor(category_count):
        return None
    cdf = np.cumsum(probabilities, dtype=np.float64)
    if np.any(~np.isfinite(cdf)):
        return None
    cdf[-1] = 1.0
    increments = np.diff(np.concatenate((np.zeros(1), cdf)))
    if np.any(increments <= 0.0):
        return None
    relative_error = np.abs(increments - probabilities) / probabilities
    if np.any(relative_error > _CATEGORICAL_INCREMENT_RTOL):
        return None
    return _immutable_float_array(cdf)


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
    if strictly_positive and result <= 0.0:
        raise ValueError("%s must be strictly positive" % name)
    if not strictly_positive and result < 0.0:
        raise ValueError("%s must be nonnegative" % name)
    return result


def _validated_seed(seed: object) -> int:
    return _validated_integer(
        seed,
        name="seed",
        minimum=0,
        maximum=MAX_RANDOM_SEED,
    )


def _validated_sample_size(size: object) -> int:
    return _validated_integer(
        size,
        name="size",
        minimum=1,
        maximum=MAX_REFERENCE_SAMPLE_SIZE,
    )


@dataclass(frozen=True)
class TransformedEvent:
    """One event in a declared transformed Gaussian fiber.

    ``event_type`` is the executable stratum identifier.  ``coordinates`` are
    already in transformed Euclidean coordinates; there is deliberately no
    native physical-time field or occurrence identifier at this boundary.
    """

    event_type: int
    coordinates: TransformedCoordinates = ()

    def __post_init__(self) -> None:
        event_type = _validated_integer(
            self.event_type,
            name="event_type",
            minimum=0,
            maximum=2**63 - 1,
        )
        raw_coordinates = _bounded_tuple(
            self.coordinates,
            name="coordinates",
            maximum_items=MAX_TRANSFORMED_COORDINATE_DIMENSION,
        )
        checked = []
        for coordinate in raw_coordinates:
            if isinstance(coordinate, (bool, np.bool_)) or not isinstance(
                coordinate, Real
            ):
                raise TypeError(
                    "coordinates must contain real non-boolean numbers"
                )
            converted = float(coordinate)
            if not math.isfinite(converted):
                raise ValueError("coordinates must contain only finite values")
            checked.append(0.0 if converted == 0.0 else converted)
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "coordinates", tuple(checked))

    def model_key(self) -> Tuple[object, ...]:
        """Return the complete transformed model state for this occurrence."""

        return (self.event_type, self.coordinates)


@dataclass(frozen=True, eq=False, init=False)
class CappedPoissonConfigurationReference:
    """Normalized capped-Poisson law on typed standard-Gaussian fibers.

    The declared hybrid event base is

    ``xi = sum_d delta_d tensor Lebesgue_{k_d}``,

    with unit mass as ``Lebesgue_0``.  The associated configuration base used
    by :meth:`log_lebesgue_poisson_density` is

    ``Lambda_N^xi = sum_n 1/n! (Sigma_n)_# xi^n``.

    Public mappings and arrays are detached immutable copies.  Count log masses
    are authoritative and remain available when a probability vector would
    contain subnormal entries; materializing that lossy vector is then refused.
    Positive type weights and intensities must themselves remain normal
    ``float64`` values because they enter categorical and rate calculations.
    Sampling additionally refuses any categorical law below the frozen
    finite-RNG resolution gate; validity of a log law is not misreported as
    finite-precision sampleability.
    """

    type_ids: Tuple[int, ...]
    type_dimensions: Mapping[int, int]
    type_weights: Mapping[int, float]
    type_intensities: Mapping[int, float]
    activity: float
    total_cap: int
    log_normalizer: float
    count_log_masses: np.ndarray = field(repr=False)
    _count_probability_vector: Optional[np.ndarray] = field(repr=False)
    _count_sampling_cdf: Optional[np.ndarray] = field(repr=False)
    _type_positions: Mapping[int, int] = field(repr=False)
    _type_weight_vector: np.ndarray = field(repr=False)
    _type_sampling_cdf: Optional[np.ndarray] = field(repr=False)

    def __init__(
        self,
        type_dimensions: Mapping[int, int],
        type_weights: Mapping[int, float],
        *,
        activity: float,
        total_cap: int,
    ) -> None:
        if not isinstance(type_dimensions, Mapping):
            raise TypeError("type_dimensions must be a mapping")
        if not isinstance(type_weights, Mapping):
            raise TypeError("type_weights must be a mapping")

        raw_dimension_keys = _bounded_tuple(
            type_dimensions.keys(),
            name="type_dimensions keys",
            maximum_items=MAX_CONFIGURATION_EVENT_TYPES,
        )
        if not raw_dimension_keys:
            raise ValueError("at least one event type must be declared")
        checked_type_ids = []
        for type_id in raw_dimension_keys:
            checked_type_ids.append(
                _validated_integer(
                    type_id,
                    name="event type id",
                    minimum=0,
                    maximum=2**63 - 1,
                )
            )
        if len(set(checked_type_ids)) != len(checked_type_ids):
            raise ValueError("event type ids must be unique")
        type_ids = tuple(sorted(checked_type_ids))

        raw_weight_keys = _bounded_tuple(
            type_weights.keys(),
            name="type_weights keys",
            maximum_items=MAX_CONFIGURATION_EVENT_TYPES,
        )
        checked_weight_keys = []
        for type_id in raw_weight_keys:
            checked_weight_keys.append(
                _validated_integer(
                    type_id,
                    name="event type id",
                    minimum=0,
                    maximum=2**63 - 1,
                )
            )
        if len(set(checked_weight_keys)) != len(checked_weight_keys):
            raise ValueError("event type ids must be unique")
        if tuple(sorted(checked_weight_keys)) != type_ids:
            raise ValueError(
                "type_dimensions and type_weights must have identical type ids"
            )

        dimensions = {}
        raw_weights = {}
        for type_id in type_ids:
            dimensions[type_id] = _validated_integer(
                type_dimensions[type_id],
                name="coordinate dimension for type %d" % type_id,
                minimum=0,
                maximum=MAX_TRANSFORMED_COORDINATE_DIMENSION,
            )
            raw_weights[type_id] = _validated_real(
                type_weights[type_id],
                name="weight for type %d" % type_id,
                strictly_positive=True,
            )

        weight_sum = math.fsum(raw_weights[type_id] for type_id in type_ids)
        if not math.isclose(
            weight_sum,
            1.0,
            rel_tol=0.0,
            abs_tol=TYPE_WEIGHT_SUM_ATOL,
        ):
            raise ValueError(
                "type_weights must sum to one within absolute tolerance %.1e"
                % TYPE_WEIGHT_SUM_ATOL
            )
        normalized_weights = {
            type_id: raw_weights[type_id] / weight_sum for type_id in type_ids
        }
        if any(
            value < float(np.finfo(np.float64).tiny)
            for value in normalized_weights.values()
        ):
            raise ArithmeticError(
                "every normalized type weight must be a normal float64 value"
            )

        theta = _validated_real(
            activity,
            name="activity",
            strictly_positive=True,
        )
        cap = _validated_integer(
            total_cap,
            name="total_cap",
            minimum=0,
            maximum=MAX_CONFIGURATION_CARDINALITY,
        )
        intensities = {
            type_id: theta * normalized_weights[type_id] for type_id in type_ids
        }
        if any(
            not math.isfinite(value)
            or value < float(np.finfo(np.float64).tiny)
            for value in intensities.values()
        ):
            raise ArithmeticError(
                "every positive type intensity must be a normal float64 value"
            )

        log_theta = math.log(theta)
        mode = cap if theta >= cap else int(math.floor(theta))
        relative_log_weights = np.empty(cap + 1, dtype=np.float64)
        relative_log_weights[mode] = 0.0
        for count in range(mode, 0, -1):
            relative_log_weights[count - 1] = (
                relative_log_weights[count] + math.log(count) - log_theta
            )
        for count in range(mode, cap):
            relative_log_weights[count + 1] = (
                relative_log_weights[count]
                + log_theta
                - math.log(count + 1)
            )
        log_weight_at_mode = (
            mode * log_theta - float(gammaln(mode + 1.0))
        )
        relative_log_normalizer = float(logsumexp(relative_log_weights))
        log_normalizer_value = log_weight_at_mode + relative_log_normalizer
        if not math.isfinite(log_normalizer_value):
            raise ArithmeticError("capped-Poisson log normalizer is not finite")
        log_masses = relative_log_weights - relative_log_normalizer
        if not np.all(np.isfinite(log_masses)):
            raise ArithmeticError("positive count log masses are not finite")

        probability_vector = None
        if float(np.min(log_masses)) >= _LOG_MIN_NORMAL_FLOAT64:
            probabilities = np.exp(log_masses)
            probability_sum = math.fsum(float(value) for value in probabilities)
            if not math.isfinite(probability_sum) or probability_sum <= 0.0:
                raise ArithmeticError("capped-Poisson count normalization failed")
            probabilities = probabilities / probability_sum
            if np.any(~np.isfinite(probabilities)) or np.any(probabilities <= 0.0):
                raise ArithmeticError(
                    "normalized count probabilities are not positive and finite"
                )
            probability_vector = _immutable_float_array(probabilities)

        type_weight_vector = _immutable_float_array(
            [normalized_weights[type_id] for type_id in type_ids]
        )
        count_sampling_cdf = (
            None
            if probability_vector is None
            else _resolution_safe_cdf(probability_vector)
        )
        type_sampling_cdf = _resolution_safe_cdf(type_weight_vector)

        object.__setattr__(self, "type_ids", type_ids)
        object.__setattr__(
            self, "type_dimensions", MappingProxyType(dict(dimensions))
        )
        object.__setattr__(
            self,
            "type_weights",
            MappingProxyType(dict(normalized_weights)),
        )
        object.__setattr__(
            self,
            "type_intensities",
            MappingProxyType(dict(intensities)),
        )
        object.__setattr__(self, "activity", theta)
        object.__setattr__(self, "total_cap", cap)
        object.__setattr__(self, "log_normalizer", log_normalizer_value)
        object.__setattr__(
            self, "count_log_masses", _immutable_float_array(log_masses)
        )
        object.__setattr__(
            self, "_count_probability_vector", probability_vector
        )
        object.__setattr__(self, "_count_sampling_cdf", count_sampling_cdf)
        object.__setattr__(
            self,
            "_type_positions",
            MappingProxyType(
                {type_id: index for index, type_id in enumerate(type_ids)}
            ),
        )
        object.__setattr__(
            self,
            "_type_weight_vector",
            type_weight_vector,
        )
        object.__setattr__(self, "_type_sampling_cdf", type_sampling_cdf)

    def _validate_event(self, event: object) -> TransformedEvent:
        if type(event) is not TransformedEvent:
            raise TypeError("configurations must contain exact TransformedEvent instances")
        try:
            expected_dimension = self.type_dimensions[event.event_type]
        except KeyError as error:
            raise ValueError(
                "event uses unknown event type %d" % event.event_type
            ) from error
        if len(event.coordinates) != expected_dimension:
            raise ValueError(
                "event type %d requires %d coordinates, got %d"
                % (event.event_type, expected_dimension, len(event.coordinates))
            )
        return event

    @property
    def count_probabilities(self) -> np.ndarray:
        """Return a read-only float64 PMF when every entry is normal.

        :attr:`count_log_masses` is authoritative.  This convenience view is
        refused if any positive probability would be subnormal, because the
        resulting relative error can be large even before outright underflow.
        Sampling does not depend on this materialized vector.
        """

        if self._count_probability_vector is None:
            raise ArithmeticError(
                "count probabilities cannot be materialized without a "
                "subnormal or underflowed positive entry; use count_log_masses"
            )
        return self._count_probability_vector

    def parameter_key(self) -> Tuple[object, ...]:
        """Return a deterministic, plain-data key for this transformed law."""

        return (
            "capped-poisson-transformed-reference-v1",
            tuple(
                (
                    type_id,
                    self.type_dimensions[type_id],
                    self.type_weights[type_id],
                )
                for type_id in self.type_ids
            ),
            self.activity,
            self.total_cap,
        )

    def canonicalize(
        self, events: Iterable[TransformedEvent]
    ) -> TransformedConfiguration:
        """Validate, retain multiplicities, and forget occurrence ordering."""

        if isinstance(events, (str, bytes)):
            raise TypeError("events must be an iterable of TransformedEvent values")
        try:
            iterator = iter(events)
        except TypeError as error:
            raise TypeError("events must be iterable") from error
        checked = []
        for event in iterator:
            if len(checked) >= self.total_cap:
                raise ValueError(
                    "configuration cardinality exceeds total_cap %d"
                    % self.total_cap
                )
            checked.append(self._validate_event(event))
        return tuple(sorted(checked, key=TransformedEvent.model_key))

    def log_count_mass(self, cardinality: int) -> float:
        """Return ``log P(|X| = cardinality)`` under the truncated law."""

        count = _validated_integer(
            cardinality,
            name="cardinality",
            minimum=0,
            maximum=self.total_cap,
        )
        return float(self.count_log_masses[count])

    def log_one_event_density(self, event: TransformedEvent) -> float:
        """Return ``log(d nu / d xi)`` in the declared transformed fiber."""

        checked = self._validate_event(event)
        try:
            squared_norm = math.fsum(
                coordinate * coordinate for coordinate in checked.coordinates
            )
        except OverflowError as error:
            raise ArithmeticError(
                "event squared norm is not representable in float64"
            ) from error
        if not math.isfinite(squared_norm):
            raise ArithmeticError(
                "event squared norm is not representable in float64"
            )
        dimension = self.type_dimensions[checked.event_type]
        return (
            math.log(self.type_weights[checked.event_type])
            - 0.5 * (dimension * _LOG_TWO_PI + squared_norm)
        )

    def log_lebesgue_poisson_density(
        self, events: Iterable[TransformedEvent]
    ) -> float:
        """Return ``log(d Pi_N / d Lambda_N^xi)``.

        ``Lambda_N^xi`` is the symmetrized hybrid Lebesgue--Poisson base
        described in the class docstring.  Consequently there is no explicit
        ``n!`` or occurrence-multiplicity factorial in this density.  On a
        continuous duplicate diagonal, the returned product formula is merely
        a chosen Radon--Nikodym version, not a singleton probability.
        """

        configuration = self.canonicalize(events)
        aggregate_dimension = sum(
            self.type_dimensions[event.event_type] for event in configuration
        )
        if aggregate_dimension > MAX_REFERENCE_DENSITY_COORDINATES:
            raise ValueError(
                "configuration exceeds the log-density coordinate-work budget"
            )
        event_terms = tuple(
            self.log_one_event_density(event) for event in configuration
        )
        try:
            event_log_density = math.fsum(event_terms)
        except OverflowError as error:
            raise ArithmeticError(
                "configuration log density is not representable in float64"
            ) from error
        result = (
            -self.log_normalizer
            + len(configuration) * math.log(self.activity)
            + event_log_density
        )
        if not math.isfinite(result):
            raise ArithmeticError(
                "configuration log density is not representable in float64"
            )
        return result

    def log_point_mass(self, events: Iterable[TransformedEvent]) -> float:
        """Return the exact singleton log mass, or ``-inf`` if it is atomless.

        A configuration has positive singleton mass only when every occurrence
        belongs to a zero-dimensional stratum.  In that case the orbit
        multiplicities contribute ``1 / prod_a m_a!``.  This method is not a
        continuous density API.
        """

        configuration = self.canonicalize(events)
        if any(
            self.type_dimensions[event.event_type] != 0
            for event in configuration
        ):
            return -math.inf

        log_mass = (
            -self.log_normalizer
            + len(configuration) * math.log(self.activity)
            + math.fsum(
                math.log(self.type_weights[event.event_type])
                for event in configuration
            )
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

    def sample_count(self, rng: np.random.Generator) -> int:
        """Draw one cardinality when every bin passes the RNG-resolution gate."""

        if not isinstance(rng, np.random.Generator):
            raise TypeError("rng must be a numpy.random.Generator")
        if self._count_sampling_cdf is None:
            raise UnsupportedReferenceSamplingError(
                "count law is valid in log space but has a category below the "
                "finite-RNG sampling resolution; revise activity/cap or use a "
                "separately audited variable-random-bit sampler"
            )
        return int(
            np.searchsorted(
                self._count_sampling_cdf,
                rng.random(),
                side="right",
            )
        )

    def sample_event(self, rng: np.random.Generator) -> TransformedEvent:
        """Draw one event from the typed standard-Gaussian law ``nu``."""

        if not isinstance(rng, np.random.Generator):
            raise TypeError("rng must be a numpy.random.Generator")
        if self._type_sampling_cdf is None:
            raise UnsupportedReferenceSamplingError(
                "type law has a category below the finite-RNG sampling "
                "resolution; revise type weights or use a separately audited "
                "variable-random-bit sampler"
            )
        position = int(
            np.searchsorted(
                self._type_sampling_cdf,
                rng.random(),
                side="right",
            )
        )
        event_type = self.type_ids[position]
        dimension = self.type_dimensions[event_type]
        coordinates = tuple(float(value) for value in rng.standard_normal(dimension))
        return TransformedEvent(event_type, coordinates)

    def sample_configuration(
        self, rng: np.random.Generator
    ) -> TransformedConfiguration:
        """Draw one unlabelled capped configuration using a supplied RNG."""

        if not isinstance(rng, np.random.Generator):
            raise TypeError("rng must be a numpy.random.Generator")
        if (
            self.total_cap
            * max(self.type_dimensions.values())
            > MAX_REFERENCE_BATCH_COORDINATES
        ):
            raise ValueError(
                "one worst-case configuration exceeds the sampling coordinate budget"
            )
        count = self.sample_count(rng)
        if self._type_sampling_cdf is None:
            raise UnsupportedReferenceSamplingError(
                "type law has a category below the finite-RNG sampling "
                "resolution; revise type weights or use a separately audited "
                "variable-random-bit sampler"
            )
        positions = np.asarray(
            np.searchsorted(
                self._type_sampling_cdf,
                rng.random(count),
                side="right",
            ),
            dtype=np.int64,
        )
        total_coordinates = sum(
            self.type_dimensions[self.type_ids[int(position)]]
            for position in positions
        )
        if total_coordinates > MAX_REFERENCE_BATCH_COORDINATES:
            raise ValueError(
                "sampled configuration exceeds the coordinate-allocation "
                "safety budget"
            )
        events = tuple(
            TransformedEvent(
                self.type_ids[int(position)],
                tuple(
                    float(value)
                    for value in rng.standard_normal(
                        self.type_dimensions[self.type_ids[int(position)]]
                    )
                ),
            )
            for position in positions
        )
        return self.canonicalize(events)

    def sample(
        self,
        *,
        seed: Optional[int] = None,
        size: Optional[int] = None,
    ) -> Union[TransformedConfiguration, Tuple[TransformedConfiguration, ...]]:
        """Draw one or several configurations using an isolated local stream."""

        if seed is None:
            rng = np.random.default_rng()
        else:
            rng = np.random.default_rng(_validated_seed(seed))
        if size is None:
            return self.sample_configuration(rng)
        sample_size = _validated_sample_size(size)
        if sample_size * self.total_cap > MAX_REFERENCE_BATCH_OCCURRENCES:
            raise ValueError(
                "requested batch exceeds the occurrence-allocation safety budget"
            )
        if (
            sample_size
            * self.total_cap
            * max(self.type_dimensions.values())
            > MAX_REFERENCE_BATCH_COORDINATES
        ):
            raise ValueError(
                "requested batch exceeds the coordinate-allocation safety budget"
            )
        return tuple(self.sample_configuration(rng) for _ in range(sample_size))

    def finite_atomic_oracle(
        self,
    ) -> Tuple[FiniteAtomicCountingSpace, Mapping[int, float], np.ndarray]:
        """Return the existing exact finite oracle for an all-atomic reference.

        The oracle activities are ``activity * type_weight``.  Its own strict
        enumeration limits remain authoritative; this adapter is a test
        oracle, not the production sampler.
        """

        if any(dimension != 0 for dimension in self.type_dimensions.values()):
            raise ValueError(
                "finite_atomic_oracle requires every stratum to be zero-dimensional"
            )
        space = FiniteAtomicCountingSpace(self.type_ids, self.total_cap)
        intensities = MappingProxyType(dict(self.type_intensities))
        masses = capped_counting_reference(space, intensities)
        return space, intensities, masses

    def birth_death_balance_residual(
        self,
        birth_rate: float,
        per_particle_death_rate: float,
    ) -> float:
        """Return the scalar balance residual ``beta - theta * delta``."""

        beta = _validated_real(
            birth_rate,
            name="birth_rate",
            strictly_positive=True,
        )
        delta = _validated_real(
            per_particle_death_rate,
            name="per_particle_death_rate",
            strictly_positive=True,
        )
        balanced_birth_rate = self.activity * delta
        if not math.isfinite(balanced_birth_rate):
            raise ArithmeticError(
                "activity times per_particle_death_rate is not finite"
            )
        return beta - balanced_birth_rate

    def replacement_balance_residuals(self, replacement_rates: object) -> np.ndarray:
        """Return ``w_i kappa_ij - w_j kappa_ji`` for every type pair.

        Array rows and columns follow ascending :attr:`type_ids`.  This is a
        bounded diagnostic, not a scalable dense replacement representation.
        """

        type_count = len(self.type_ids)
        if type_count > MAX_REPLACEMENT_BALANCE_TYPES:
            raise ValueError(
                "replacement balance diagnostics support at most %d event types"
                % MAX_REPLACEMENT_BALANCE_TYPES
            )
        matrix = np.zeros((type_count, type_count), dtype=np.float64)
        if isinstance(replacement_rates, Mapping):
            expected_count = type_count * (type_count - 1)
            raw_keys = _bounded_tuple(
                replacement_rates.keys(),
                name="replacement_rates keys",
                maximum_items=expected_count,
            )
            if len(raw_keys) != expected_count:
                raise ValueError(
                    "replacement_rates mapping must specify every ordered pair "
                    "of distinct event types exactly once"
                )
            seen_pairs = set()
            for raw_key in raw_keys:
                if type(raw_key) is not tuple or len(raw_key) != 2:
                    raise TypeError(
                        "replacement_rates keys must be exact (source, destination) tuples"
                    )
                source = _validated_integer(
                    raw_key[0],
                    name="replacement source type",
                    minimum=0,
                    maximum=2**63 - 1,
                )
                destination = _validated_integer(
                    raw_key[1],
                    name="replacement destination type",
                    minimum=0,
                    maximum=2**63 - 1,
                )
                if (
                    source not in self._type_positions
                    or destination not in self._type_positions
                    or source == destination
                ):
                    raise ValueError(
                        "replacement_rates keys must cover distinct declared types"
                    )
                pair = (source, destination)
                if pair in seen_pairs:
                    raise ValueError("replacement_rates contains a duplicate type pair")
                seen_pairs.add(pair)
                value = _validated_real(
                    replacement_rates[raw_key],
                    name="replacement rate (%d, %d)" % (source, destination),
                    strictly_positive=False,
                )
                matrix[
                    self._type_positions[source], self._type_positions[destination]
                ] = value
        else:
            try:
                raw = np.asarray(replacement_rates)
            except (TypeError, ValueError, OverflowError) as error:
                raise ValueError(
                    "replacement_rates must be a rectangular numeric array"
                ) from error
            try:
                object_entries = np.asarray(replacement_rates, dtype=object)
            except (TypeError, ValueError, OverflowError) as error:
                raise ValueError(
                    "replacement_rates must be a rectangular numeric array"
                ) from error
            if any(
                isinstance(entry, (bool, np.bool_)) for entry in object_entries.flat
            ):
                raise TypeError("replacement_rates must not contain booleans")
            if raw.dtype.kind not in "iuf":
                raise TypeError("replacement_rates must have a real numeric dtype")
            if raw.shape != (type_count, type_count):
                raise ValueError(
                    "replacement_rates must have shape (%d, %d)"
                    % (type_count, type_count)
                )
            matrix = raw.astype(np.float64, copy=True)
            if not np.all(np.isfinite(matrix)):
                raise ValueError("replacement_rates entries must be finite")
            if np.any(matrix < 0.0):
                raise ValueError("replacement_rates entries must be nonnegative")
            if np.any(np.diag(matrix) != 0.0):
                raise ValueError("replacement_rates diagonal must be exactly zero")

        weights = np.asarray(
            [self.type_weights[type_id] for type_id in self.type_ids],
            dtype=np.float64,
        )
        weighted_rates = weights[:, None] * matrix
        positive_products = (weights[:, None] > 0.0) & (matrix > 0.0)
        if np.any(
            positive_products
            & (weighted_rates < float(np.finfo(np.float64).tiny))
        ):
            raise ArithmeticError(
                "a positive weight-times-replacement-rate product is not a "
                "normal float64 value"
            )
        residuals = weighted_rates - weighted_rates.T
        np.fill_diagonal(residuals, 0.0)
        if not np.all(np.isfinite(residuals)):
            raise ArithmeticError("replacement balance residual is not finite")
        return _immutable_float_array(residuals)


__all__ = [
    "CappedPoissonConfigurationReference",
    "MAX_CONFIGURATION_CARDINALITY",
    "MAX_CONFIGURATION_EVENT_TYPES",
    "MAX_RANDOM_SEED",
    "MAX_REFERENCE_BATCH_COORDINATES",
    "MAX_REFERENCE_BATCH_OCCURRENCES",
    "MAX_REFERENCE_DENSITY_COORDINATES",
    "MAX_REFERENCE_SAMPLE_SIZE",
    "MAX_REPLACEMENT_BALANCE_TYPES",
    "MAX_TRANSFORMED_COORDINATE_DIMENSION",
    "MIN_REFERENCE_CATEGORICAL_PROBABILITY",
    "TYPE_WEIGHT_SUM_ATOL",
    "TransformedConfiguration",
    "TransformedCoordinates",
    "TransformedEvent",
    "UnsupportedReferenceSamplingError",
]
