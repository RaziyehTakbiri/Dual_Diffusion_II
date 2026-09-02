"""Closed reference guide for finite atomic association experiments.

The target experiment uses a capped counting process, but the analytic guide
in this module deliberately does not.  Its reference dynamics are independent
Poisson immigration together with independent per-occurrence death and typed
replacement.  That uncapped process is closed under propagation to a terminal
missed-detection/confusion observation: current occurrences remain categorical
and future immigrants contribute an additional Poisson anchor intensity.

This is an enumerable verification implementation.  It evaluates all retained
anchor-count coefficients by dynamic programming and assigns their
unconditioned complement to one overflow outcome.  It never enumerates
occurrence-to-anchor matchings and never conditions on the retained cap.

``direct_time`` always means forward time ``t`` in ``[0, terminal_time]``;
the propagated duration is ``terminal_time - t``.  Consequently, calls at
``direct_time == terminal_time`` reproduce the terminal observation law.
"""

from __future__ import annotations

from numbers import Integral, Real
import math
from typing import Callable, Mapping, Tuple

import numpy as np
from scipy.linalg import expm

from .finite_atomic_counting import (
    ExplicitAtomicVector,
    ExplicitReplacementRates,
    FiniteAtomicCountingSpace,
)


AtomicCountVector = Tuple[int, ...]

_MAX_GRID_WORK = 25_000_000
_NUMERICAL_TOLERANCE = 5.0e-12


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    return np.frombuffer(array.tobytes(order="C"), dtype=np.float64).reshape(
        array.shape
    )


def _reject_boolean_entries(value: object, name: str) -> None:
    try:
        entries = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    if any(isinstance(entry, (bool, np.bool_)) for entry in entries.flat):
        raise TypeError("%s must not contain boolean entries" % name)


def _as_numeric_array(value: object, name: str, shape: Tuple[int, ...]) -> np.ndarray:
    try:
        raw = np.asarray(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    _reject_boolean_entries(value, name)
    if raw.dtype.kind == "b":
        raise TypeError("%s must not have boolean dtype" % name)
    if raw.dtype.kind not in "iuf":
        raise TypeError("%s must have a real numeric dtype" % name)
    if raw.shape != shape:
        raise ValueError("%s must have shape %r" % (name, shape))
    try:
        result = raw.astype(float, copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s cannot be represented as floats" % name) from error
    if not np.all(np.isfinite(result)):
        raise ValueError("%s entries must be finite" % name)
    return result


def _as_nonnegative_vector(
    space: FiniteAtomicCountingSpace,
    value: ExplicitAtomicVector,
    name: str,
) -> np.ndarray:
    if isinstance(value, Mapping):
        expected = set(space.atom_names)
        if set(value.keys()) != expected or len(value) != space.atom_count:
            raise ValueError("%s mapping must specify every atom exactly once" % name)
        checked = []
        for atom in space.atom_names:
            entry = value[atom]
            if isinstance(entry, (bool, np.bool_)) or not isinstance(entry, Real):
                raise TypeError("%s entries must be real non-boolean numbers" % name)
            number = float(entry)
            if not math.isfinite(number):
                raise ValueError("%s entries must be finite" % name)
            if number < 0.0:
                raise ValueError("%s entries must be nonnegative" % name)
            checked.append(number)
        return np.asarray(checked, dtype=float)

    result = _as_numeric_array(value, name, (space.atom_count,))
    if np.any(result < 0.0):
        raise ValueError("%s entries must be nonnegative" % name)
    return result


def _as_replacement_matrix(
    space: FiniteAtomicCountingSpace,
    value: ExplicitReplacementRates,
) -> np.ndarray:
    shape = (space.atom_count, space.atom_count)
    if isinstance(value, Mapping):
        expected = {
            (source, destination)
            for source in space.atom_names
            for destination in space.atom_names
            if source != destination
        }
        if set(value.keys()) != expected or len(value) != len(expected):
            raise ValueError(
                "replacement_rates mapping must specify every ordered pair "
                "of distinct atoms exactly once"
            )
        result = np.zeros(shape, dtype=float)
        for source, destination in expected:
            entry = value[(source, destination)]
            if isinstance(entry, (bool, np.bool_)) or not isinstance(entry, Real):
                raise TypeError(
                    "replacement_rates entries must be real non-boolean numbers"
                )
            number = float(entry)
            if not math.isfinite(number):
                raise ValueError("replacement_rates entries must be finite")
            if number < 0.0:
                raise ValueError("replacement_rates entries must be nonnegative")
            result[
                space.atom_position(source), space.atom_position(destination)
            ] = number
        return result

    result = _as_numeric_array(value, "replacement_rates", shape)
    if np.any(result < 0.0):
        raise ValueError("replacement_rates entries must be nonnegative")
    if np.any(np.diag(result) != 0.0):
        raise ValueError("replacement_rates diagonal must be exactly zero")
    return result


def _validated_positive_time(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError("%s must be finite and strictly positive" % name)
    return result


def _validated_probability(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or not 0.0 < result < 1.0:
        raise ValueError("%s must lie strictly between zero and one" % name)
    return result


def _bounded_observations(value: object, expected_length: int) -> Tuple[object, ...]:
    try:
        iterator = iter(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("observation.observations must be iterable") from error
    items = []
    for item in iterator:
        if len(items) >= expected_length:
            raise ValueError(
                "observation.observations contains more than n_observations items"
            )
        items.append(item)
    if len(items) != expected_length:
        raise ValueError(
            "observation.observations must contain exactly n_observations items"
        )
    return tuple(items)


class IndependentFiniteAtomicReferenceGuide:
    """Analytic guide for an uncapped independent typed reference process.

    The observation object is intentionally validated through its frozen
    public protocol rather than through a nominal class check.  It must expose
    ``latent_space``, ``retained_observation_space``, ``observations``,
    ``n_observations``, ``detection_probability``, ``confusion_matrix``,
    ``observation_clutter_rates``, ``reference_mass``, and
    ``contamination_probability``.
    """

    def __init__(
        self,
        latent_space: FiniteAtomicCountingSpace,
        observation: object,
        terminal_time: object,
        immigration_rates: ExplicitAtomicVector,
        per_particle_death_rates: ExplicitAtomicVector,
        replacement_rates: ExplicitReplacementRates,
    ) -> None:
        if not isinstance(latent_space, FiniteAtomicCountingSpace):
            raise TypeError("latent_space must be a FiniteAtomicCountingSpace")
        required = (
            "latent_space",
            "retained_observation_space",
            "observations",
            "n_observations",
            "detection_probability",
            "confusion_matrix",
            "observation_clutter_rates",
            "reference_mass",
            "contamination_probability",
        )
        missing = tuple(name for name in required if not hasattr(observation, name))
        if missing:
            raise TypeError(
                "observation is missing required attribute(s): %s"
                % ", ".join(missing)
            )
        if observation.latent_space is not latent_space:  # type: ignore[attr-defined]
            raise ValueError(
                "observation must be constructed from the identical latent_space"
            )
        retained_space = observation.retained_observation_space  # type: ignore[attr-defined]
        if not isinstance(retained_space, FiniteAtomicCountingSpace):
            raise TypeError(
                "observation.retained_observation_space must be a "
                "FiniteAtomicCountingSpace"
            )

        n_observations_value = observation.n_observations  # type: ignore[attr-defined]
        if isinstance(n_observations_value, (bool, np.bool_)) or not isinstance(
            n_observations_value, Integral
        ):
            raise TypeError("observation.n_observations must be an integer")
        n_observations = int(n_observations_value)
        if n_observations != retained_space.n_states + 1:
            raise ValueError(
                "observation must contain every retained count followed by one "
                "overflow outcome"
            )
        observations = _bounded_observations(
            observation.observations, n_observations  # type: ignore[attr-defined]
        )
        if observations[:-1] != retained_space.states:
            raise ValueError(
                "retained observations must follow retained_observation_space.states"
            )
        if observations[-1] in retained_space.states:
            raise ValueError("the final observation must be a distinct overflow outcome")

        terminal = _validated_positive_time(terminal_time, "terminal_time")
        immigration = _as_nonnegative_vector(
            latent_space, immigration_rates, "immigration_rates"
        )
        death = _as_nonnegative_vector(
            latent_space,
            per_particle_death_rates,
            "per_particle_death_rates",
        )
        replacement = _as_replacement_matrix(latent_space, replacement_rates)

        latent_count = latent_space.atom_count
        anchor_count = retained_space.atom_count
        detection = _as_numeric_array(
            observation.detection_probability,  # type: ignore[attr-defined]
            "observation.detection_probability",
            (latent_count,),
        )
        if np.any(detection < 0.0) or np.any(detection > 1.0):
            raise ValueError(
                "observation detection probabilities must lie in [0, one]"
            )
        confusion = _as_numeric_array(
            observation.confusion_matrix,  # type: ignore[attr-defined]
            "observation.confusion_matrix",
            (latent_count, anchor_count),
        )
        if np.any(confusion < 0.0):
            raise ValueError("observation confusion probabilities must be nonnegative")
        if not np.allclose(
            confusion.sum(axis=1), 1.0, atol=1.0e-12, rtol=0.0
        ):
            raise ValueError("observation confusion rows must sum to one")
        confusion /= confusion.sum(axis=1, keepdims=True)

        observation_clutter = _as_numeric_array(
            observation.observation_clutter_rates,  # type: ignore[attr-defined]
            "observation.observation_clutter_rates",
            (anchor_count,),
        )
        if np.any(observation_clutter < 0.0):
            raise ValueError("observation clutter rates must be nonnegative")
        reference = _as_numeric_array(
            observation.reference_mass,  # type: ignore[attr-defined]
            "observation.reference_mass",
            (n_observations,),
        )
        if np.any(reference <= 0.0):
            raise ValueError("observation reference mass must be strictly positive")
        if not math.isclose(
            float(reference.sum()), 1.0, rel_tol=0.0, abs_tol=2.0e-13
        ):
            raise ValueError("observation reference mass must sum to one")
        reference /= reference.sum()
        contamination = _validated_probability(
            observation.contamination_probability,  # type: ignore[attr-defined]
            "observation.contamination_probability",
        )

        work = latent_space.n_states * (
            retained_space.n_states * retained_space.n_states
            + latent_space.total_cap
            * retained_space.n_states
            * (anchor_count + 1)
        )
        if work > _MAX_GRID_WORK:
            raise ValueError(
                "reference guide exceeds the enumerable work limit of %d"
                % _MAX_GRID_WORK
            )

        subgenerator = replacement.copy()
        np.fill_diagonal(
            subgenerator,
            -(death + replacement.sum(axis=1)),
        )
        if not np.all(np.isfinite(subgenerator)):
            raise ValueError("one-particle exit rates must be finite")

        self._latent_space = latent_space
        self._observation = observation
        self._retained_observation_space = retained_space
        self._observations = observations
        self._n_observations = n_observations
        self._terminal_time = terminal
        self._immigration_rates = _immutable_float_array(immigration)
        self._per_particle_death_rates = _immutable_float_array(death)
        self._replacement_rates = _immutable_float_array(replacement)
        self._one_particle_subgenerator = _immutable_float_array(subgenerator)
        self._terminal_emission_mass = _immutable_float_array(
            detection[:, None] * confusion
        )
        self._observation_clutter_rates = _immutable_float_array(
            observation_clutter
        )
        self._reference_mass = _immutable_float_array(reference)
        self._contamination_probability = contamination
        self._propagation_cache = {}  # type: ignore[var-annotated]
        self._grid_cache = {}  # type: ignore[var-annotated]

    @property
    def latent_space(self) -> FiniteAtomicCountingSpace:
        return self._latent_space

    @property
    def observation(self) -> object:
        return self._observation

    @property
    def retained_observation_space(self) -> FiniteAtomicCountingSpace:
        return self._retained_observation_space

    @property
    def observations(self) -> Tuple[object, ...]:
        return self._observations

    @property
    def n_observations(self) -> int:
        return self._n_observations

    @property
    def terminal_time(self) -> float:
        return self._terminal_time

    @property
    def immigration_rates(self) -> np.ndarray:
        return self._immigration_rates

    @property
    def per_particle_death_rates(self) -> np.ndarray:
        return self._per_particle_death_rates

    @property
    def replacement_rates(self) -> np.ndarray:
        return self._replacement_rates

    @property
    def one_particle_subgenerator(self) -> np.ndarray:
        return self._one_particle_subgenerator

    @property
    def terminal_emission_mass(self) -> np.ndarray:
        """Source-by-anchor terminal emission masses ``diag(detection) C``."""

        return self._terminal_emission_mass

    @property
    def observation_clutter_rates(self) -> np.ndarray:
        return self._observation_clutter_rates

    @property
    def reference_mass(self) -> np.ndarray:
        return self._reference_mass

    @property
    def contamination_probability(self) -> float:
        return self._contamination_probability

    def _validated_direct_time(self, value: object) -> float:
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise TypeError("direct_time must be a real non-boolean number")
        direct_time = float(value)
        if (
            not math.isfinite(direct_time)
            or direct_time < 0.0
            or direct_time > self._terminal_time
        ):
            raise ValueError(
                "direct_time must lie in [zero, terminal_time]"
            )
        return direct_time

    def _propagation(self, direct_time: object) -> Tuple[np.ndarray, np.ndarray]:
        current = self._validated_direct_time(direct_time)
        cached = self._propagation_cache.get(current)
        if cached is not None:
            return cached

        duration = self._terminal_time - current
        atom_count = self._latent_space.atom_count
        block = np.zeros((2 * atom_count, 2 * atom_count), dtype=float)
        block[:atom_count, :atom_count] = self._one_particle_subgenerator
        block[:atom_count, atom_count:] = np.eye(atom_count)
        propagated = expm(duration * block)
        survival = np.asarray(
            propagated[:atom_count, :atom_count], dtype=float
        ).copy()
        integral = np.asarray(propagated[:atom_count, atom_count:], dtype=float)
        if not np.all(np.isfinite(survival)) or not np.all(np.isfinite(integral)):
            raise ArithmeticError("block exponential produced non-finite values")
        if np.any(survival < -_NUMERICAL_TOLERANCE):
            raise ArithmeticError("survival transition contains negative mass")
        survival[survival < 0.0] = 0.0
        row_sums = survival.sum(axis=1)
        if np.any(row_sums > 1.0 + _NUMERICAL_TOLERANCE):
            raise ArithmeticError("survival transition is not sub-Markov")

        immigrant_mean = np.asarray(
            self._immigration_rates @ integral, dtype=float
        ).copy()
        if not np.all(np.isfinite(immigrant_mean)):
            raise ArithmeticError("immigrant terminal mean is non-finite")
        if np.any(immigrant_mean < -_NUMERICAL_TOLERANCE):
            raise ArithmeticError("immigrant terminal mean contains negative mass")
        immigrant_mean[immigrant_mean < 0.0] = 0.0

        result = (
            _immutable_float_array(survival),
            _immutable_float_array(immigrant_mean),
        )
        self._propagation_cache[current] = result
        return result

    def survival_transition(self, direct_time: object) -> np.ndarray:
        """Sub-Markov terminal-type transition for one current occurrence."""

        return self._propagation(direct_time)[0]

    def immigrant_terminal_mean(self, direct_time: object) -> np.ndarray:
        """Terminal type means generated by future independent immigration."""

        return self._propagation(direct_time)[1]

    def effective_emission_mass(self, direct_time: object) -> np.ndarray:
        """Source-by-anchor emission mass after survival and replacement."""

        survival = self.survival_transition(direct_time)
        emission = survival @ self._terminal_emission_mass
        if not np.all(np.isfinite(emission)):
            raise ArithmeticError("effective emission mass is non-finite")
        if np.any(emission < -_NUMERICAL_TOLERANCE):
            raise ArithmeticError("effective emission mass contains negative values")
        emission = np.asarray(emission, dtype=float)
        emission[emission < 0.0] = 0.0
        return _immutable_float_array(emission)

    def effective_miss_probability(self, direct_time: object) -> np.ndarray:
        """Probability of no terminal anchor from each current source type."""

        miss = 1.0 - self.effective_emission_mass(direct_time).sum(axis=1)
        if np.any(miss < -_NUMERICAL_TOLERANCE) or np.any(
            miss > 1.0 + _NUMERICAL_TOLERANCE
        ):
            raise ArithmeticError("effective miss probability lies outside [0, one]")
        miss = np.clip(miss, 0.0, 1.0)
        return _immutable_float_array(miss)

    def immigrant_anchor_intensity(self, direct_time: object) -> np.ndarray:
        """Detected anchor intensity contributed by future immigrants."""

        intensity = (
            self.immigrant_terminal_mean(direct_time)
            @ self._terminal_emission_mass
        )
        if not np.all(np.isfinite(intensity)) or np.any(
            intensity < -_NUMERICAL_TOLERANCE
        ):
            raise ArithmeticError("immigrant anchor intensity is invalid")
        intensity = np.asarray(intensity, dtype=float)
        intensity[intensity < 0.0] = 0.0
        return _immutable_float_array(intensity)

    def effective_clutter_rates(self, direct_time: object) -> np.ndarray:
        """Observation clutter plus detected future-immigrant intensities."""

        result = (
            self._observation_clutter_rates
            + self.immigrant_anchor_intensity(direct_time)
        )
        if not np.all(np.isfinite(result)):
            raise ArithmeticError("effective clutter rates are non-finite")
        return _immutable_float_array(result)

    def _poisson_retained_mass(self, rates: np.ndarray) -> Mapping[AtomicCountVector, float]:
        total_rate = math.fsum(float(rate) for rate in rates)
        if not math.isfinite(total_rate):
            raise ArithmeticError("effective clutter total is non-finite")
        result = {}
        for counts in self._retained_observation_space.states:
            log_mass = -total_rate
            possible = True
            for count, rate in zip(counts, rates):
                if count == 0:
                    continue
                if rate == 0.0:
                    possible = False
                    break
                log_mass += count * math.log(float(rate)) - math.lgamma(count + 1.0)
            result[counts] = math.exp(log_mass) if possible else 0.0
        return result

    def _current_emission_mass(
        self,
        latent_counts: AtomicCountVector,
        emission: np.ndarray,
        miss: np.ndarray,
    ) -> Mapping[AtomicCountVector, float]:
        anchor_count = self._retained_observation_space.atom_count
        retained_cap = self._retained_observation_space.total_cap
        zero = (0,) * anchor_count
        dynamic = {zero: 1.0}
        for source, multiplicity in enumerate(latent_counts):
            for _ in range(multiplicity):
                updated = {}
                for partial, prefix in dynamic.items():
                    missed = prefix * float(miss[source])
                    if missed != 0.0:
                        updated[partial] = updated.get(partial, 0.0) + missed
                    if sum(partial) >= retained_cap:
                        continue
                    for anchor in range(anchor_count):
                        emitted = prefix * float(emission[source, anchor])
                        if emitted == 0.0:
                            continue
                        destination_list = list(partial)
                        destination_list[anchor] += 1
                        destination = tuple(destination_list)
                        updated[destination] = (
                            updated.get(destination, 0.0) + emitted
                        )
                dynamic = updated
        return dynamic

    def _grids(
        self, direct_time: object
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        current = self._validated_direct_time(direct_time)
        cached = self._grid_cache.get(current)
        if cached is not None:
            return cached

        emission = self.effective_emission_mass(current)
        miss = self.effective_miss_probability(current)
        clutter = self.effective_clutter_rates(current)
        poisson = self._poisson_retained_mass(clutter)
        retained_space = self._retained_observation_space
        clean = np.zeros(
            (self._latent_space.n_states, self._n_observations), dtype=float
        )

        for latent_index, latent_counts in enumerate(self._latent_space.states):
            source_mass = self._current_emission_mass(
                latent_counts, emission, miss
            )
            for source_counts, source_probability in source_mass.items():
                if source_probability == 0.0:
                    continue
                for clutter_counts, clutter_probability in poisson.items():
                    if clutter_probability == 0.0:
                        continue
                    combined = tuple(
                        source + noise
                        for source, noise in zip(source_counts, clutter_counts)
                    )
                    if sum(combined) > retained_space.total_cap:
                        continue
                    retained_index = retained_space.index_of(combined)
                    clean[latent_index, retained_index] += (
                        source_probability * clutter_probability
                    )

            retained_total = math.fsum(
                float(value) for value in clean[latent_index, :-1]
            )
            if not math.isfinite(retained_total):
                raise ArithmeticError("retained guide probability is non-finite")
            if retained_total < 0.0 or retained_total > 1.0 + _NUMERICAL_TOLERANCE:
                raise ArithmeticError("retained guide probability lies outside [0, one]")
            clean[latent_index, -1] = max(0.0, 1.0 - retained_total)

        if np.any(clean < 0.0) or not np.all(np.isfinite(clean)):
            raise ArithmeticError("clean guide mass contains invalid values")
        if not np.allclose(clean.sum(axis=1), 1.0, atol=5.0e-13, rtol=0.0):
            raise ArithmeticError("clean guide rows are not normalized")

        contaminated = (
            (1.0 - self._contamination_probability) * clean
            + self._contamination_probability * self._reference_mass[None, :]
        )
        density = contaminated / self._reference_mass[None, :]
        if np.any(contaminated <= 0.0) or not np.all(np.isfinite(contaminated)):
            raise ArithmeticError("contaminated guide mass is not positive")
        if not np.allclose(
            contaminated.sum(axis=1), 1.0, atol=5.0e-13, rtol=0.0
        ):
            raise ArithmeticError("contaminated guide rows are not normalized")
        if np.any(density < self._contamination_probability - 5.0e-13):
            raise ArithmeticError("guide density violates its contamination bound")
        if not np.allclose(
            (density * self._reference_mass[None, :]).sum(axis=1),
            1.0,
            atol=5.0e-13,
            rtol=0.0,
        ):
            raise ArithmeticError("guide density does not normalize under reference")

        result = (
            _immutable_float_array(clean),
            _immutable_float_array(contaminated),
            _immutable_float_array(density),
            _immutable_float_array(np.log(density)),
        )
        self._grid_cache[current] = result
        return result

    def clean_mass_grid(self, direct_time: object) -> np.ndarray:
        return self._grids(direct_time)[0]

    def mass_grid(self, direct_time: object) -> np.ndarray:
        return self._grids(direct_time)[1]

    def density_grid(self, direct_time: object) -> np.ndarray:
        return self._grids(direct_time)[2]

    def log_density_grid(self, direct_time: object) -> np.ndarray:
        return self._grids(direct_time)[3]

    def potential(self, observation_index: object) -> Callable[[object], np.ndarray]:
        """Return the positive density potential over latent states for one outcome."""

        if isinstance(observation_index, (bool, np.bool_)) or not isinstance(
            observation_index, Integral
        ):
            raise TypeError("observation_index must be an integer non-boolean value")
        index = int(observation_index)
        if index < 0 or index >= self._n_observations:
            raise IndexError("observation_index is outside the observation alphabet")

        def evaluate(direct_time: object) -> np.ndarray:
            return _immutable_float_array(self.density_grid(direct_time)[:, index])

        return evaluate


__all__ = ["IndependentFiniteAtomicReferenceGuide"]
