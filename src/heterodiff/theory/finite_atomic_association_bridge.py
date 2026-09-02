"""Exact positive-observation bridge on a capped finite counting space.

This module is an enumerable falsification oracle, not a scalable model and not
a novelty claim.  It joins four classical ingredients under one exact finite
convention:

* an unlabelled counting state with a hard cardinality cap;
* multiplicity-correct birth, death, and replacement rates;
* an unordered missed-detection/confusion law that exactly marginalizes latent
  occurrence-to-anchor association; and
* a single backward information function that Doob-tilts every active edge.

The clean association law may have structural zeros.  To instantiate the
project's proved strictly-positive dominated theorem without a numerical
epsilon floor, the declared observation process has a separate whole-
observation contamination branch.  With probability ``1 - epsilon`` it emits
the clean associated multiset and with probability ``epsilon`` it emits a draw
from a positive capped-Poisson reference ``lambda``.  The resulting probability
mass is ``K_epsilon`` and the theorem-facing density is
``g = K_epsilon / lambda``.  Thus ``g >= epsilon`` and
``sum_a g(a | x) lambda(a) = 1`` exactly up to checked floating-point error.

This small discrete regime does not justify exact anchors, support zeros in the
final observation law, unbounded cardinality, continuous marks, or a continuous
marked-configuration process.
"""

from __future__ import annotations

import math
from numbers import Integral, Real
from typing import Mapping, Optional, Tuple, Union

import numpy as np

from .conditional_bridge import ConditionalBridge, conditional_bridge
from .finite_atomic_counting import (
    ExplicitAtomicVector,
    ExplicitReplacementRates,
    FiniteAtomicCountingSpace,
    capped_counting_reference,
    finite_atomic_generator,
)
from .finite_atomic_overflow_observation import (
    PositiveFiniteAtomicOverflowObservation,
)
from .finite_state import (
    transition_matrix,
    validate_generator,
    validate_probability_vector,
)
from .path_kl import information_tilt_generator


AtomicCountVector = Tuple[int, ...]
TransitionFamily = str

_MAX_KERNEL_WORK = 20_000_000
_FAMILY_ORDER = ("birth", "death", "replacement")


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    return np.frombuffer(array.tobytes(order="C"), dtype=np.float64).reshape(
        array.shape
    )


def _as_float_array(value: object, name: str, shape: Tuple[int, ...]) -> np.ndarray:
    try:
        raw = np.asarray(value)
        object_view = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    if any(isinstance(item, (bool, np.bool_)) for item in object_view.flat):
        raise TypeError("%s must not contain boolean entries" % name)
    if raw.dtype.kind == "b":
        raise TypeError("%s must not have boolean dtype" % name)
    if raw.dtype.kind not in "iuf":
        raise TypeError("%s must have a real numeric dtype" % name)
    try:
        array = raw.astype(float, copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s cannot be represented as floats" % name) from error
    if array.shape != shape:
        raise ValueError("%s must have shape %r" % (name, shape))
    if not np.all(np.isfinite(array)):
        raise ValueError("%s entries must be finite" % name)
    return array


def _validated_open_probability(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    probability = float(value)
    if not math.isfinite(probability) or not 0.0 < probability < 1.0:
        raise ValueError("%s must lie strictly between zero and one" % name)
    return probability


def _validated_elapsed_time(value: object) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("elapsed_time must be a real non-boolean number")
    elapsed = float(value)
    if not math.isfinite(elapsed) or elapsed < 0.0:
        raise ValueError("elapsed_time must be finite and nonnegative")
    return elapsed


def _logaddexp(first: float, second: float) -> float:
    if first == -math.inf:
        return second
    if second == -math.inf:
        return first
    maximum = max(first, second)
    return maximum + math.log1p(math.exp(-abs(first - second)))


def _incremented_within_cap(
    counts: AtomicCountVector,
    position: int,
    cap: int,
) -> Optional[AtomicCountVector]:
    if sum(counts) >= cap:
        return None
    result = list(counts)
    result[position] += 1
    return tuple(result)


class PositiveFiniteAtomicObservation:
    """Positive dominated kernel over unordered finite anchor counts.

    Rows index latent count vectors and columns index observed anchor count
    vectors.  ``kernel_mass`` is the ordinary observation PMF.
    ``density_kernel`` is its density relative to ``reference_mass`` and is the
    quantity propagated by the bridge oracle.  Occurrence labels are used only
    inside the coefficient dynamic program and never enter the public state.
    """

    def __init__(
        self,
        latent_space: FiniteAtomicCountingSpace,
        observation_space: FiniteAtomicCountingSpace,
        detection_probability: object,
        confusion_matrix: object,
        reference_weights: ExplicitAtomicVector,
        contamination_probability: object,
    ) -> None:
        if not isinstance(latent_space, FiniteAtomicCountingSpace):
            raise TypeError("latent_space must be a FiniteAtomicCountingSpace")
        if not isinstance(observation_space, FiniteAtomicCountingSpace):
            raise TypeError(
                "observation_space must be a FiniteAtomicCountingSpace"
            )
        if observation_space.total_cap < latent_space.total_cap:
            raise ValueError(
                "observation cap must be at least the latent cap so the clean "
                "association law is normalized without overflow conditioning"
            )

        detection = _as_float_array(
            detection_probability,
            "detection_probability",
            (latent_space.atom_count,),
        )
        if np.any(detection <= 0.0) or np.any(detection >= 1.0):
            raise ValueError(
                "detection probabilities must lie strictly between zero and one"
            )

        confusion = _as_float_array(
            confusion_matrix,
            "confusion_matrix",
            (latent_space.atom_count, observation_space.atom_count),
        )
        if np.any(confusion < 0.0):
            raise ValueError("confusion probabilities must be nonnegative")
        if not np.allclose(
            confusion.sum(axis=1), 1.0, atol=1.0e-12, rtol=0.0
        ):
            raise ValueError("confusion_matrix rows must sum to one")
        confusion /= confusion.sum(axis=1, keepdims=True)

        epsilon = _validated_open_probability(
            contamination_probability, "contamination_probability"
        )
        work = (
            latent_space.n_states
            * latent_space.total_cap
            * observation_space.n_states
            * (observation_space.atom_count + 1)
        )
        if work > _MAX_KERNEL_WORK:
            raise ValueError(
                "observation kernel exceeds the enumerable work limit of %d"
                % _MAX_KERNEL_WORK
            )

        reference = capped_counting_reference(observation_space, reference_weights)
        if np.any(reference <= 0.0):
            raise ValueError(
                "reference_weights must induce positive mass on every observation"
            )

        self._latent_space = latent_space
        self._observation_space = observation_space
        self._detection_probability = _immutable_float_array(detection)
        self._confusion_matrix = _immutable_float_array(confusion)
        self._reference_mass = _immutable_float_array(reference)
        self._contamination_probability = epsilon

        clean = np.zeros(
            (latent_space.n_states, observation_space.n_states), dtype=float
        )
        for latent_index, latent_counts in enumerate(latent_space.states):
            distribution = self._clean_log_distribution(latent_counts)
            for observed_counts, log_probability in distribution.items():
                probability = math.exp(log_probability)
                if probability == 0.0 or not math.isfinite(probability):
                    raise ArithmeticError(
                        "a positive clean association mass is not representable"
                    )
                clean[
                    latent_index, observation_space.index_of(observed_counts)
                ] = probability
            row_sum = float(clean[latent_index].sum())
            if not math.isfinite(row_sum) or not math.isclose(
                row_sum, 1.0, rel_tol=0.0, abs_tol=2.0e-13
            ):
                raise ArithmeticError(
                    "clean association observation row is not normalized"
                )
            clean[latent_index] /= row_sum

        kernel_mass = (
            (1.0 - epsilon) * clean + epsilon * reference[None, :]
        )
        density = kernel_mass / reference[None, :]
        if np.any(kernel_mass <= 0.0) or not np.all(np.isfinite(kernel_mass)):
            raise ArithmeticError("contaminated observation mass is not positive")
        if not np.allclose(
            kernel_mass.sum(axis=1), 1.0, atol=2.0e-14, rtol=0.0
        ):
            raise ArithmeticError("observation probability rows are not normalized")
        if np.any(density < epsilon - 2.0e-14) or not np.all(np.isfinite(density)):
            raise ArithmeticError("observation density violates its positive bound")
        if not np.allclose(
            (density * reference[None, :]).sum(axis=1),
            1.0,
            atol=2.0e-14,
            rtol=0.0,
        ):
            raise ArithmeticError(
                "observation density does not normalize under its reference"
            )

        self._clean_kernel_mass = _immutable_float_array(clean)
        self._kernel_mass = _immutable_float_array(kernel_mass)
        self._density_kernel = _immutable_float_array(density)
        self._log_density_kernel = _immutable_float_array(np.log(density))

    @property
    def latent_space(self) -> FiniteAtomicCountingSpace:
        return self._latent_space

    @property
    def observation_space(self) -> FiniteAtomicCountingSpace:
        return self._observation_space

    @property
    def observations(self) -> Tuple[AtomicCountVector, ...]:
        """Return the legacy all-count observation alphabet.

        The explicit accessor makes this class structurally compatible with
        the sibling count-plus-overflow observation without changing the
        accepted B1 reference law.
        """

        return self._observation_space.states

    @property
    def n_observations(self) -> int:
        return self._observation_space.n_states

    def index_of_observation(self, observation: object) -> int:
        return self._observation_space.index_of(observation)  # type: ignore[arg-type]

    def observation_at(self, index: object) -> AtomicCountVector:
        if isinstance(index, (bool, np.bool_)) or not isinstance(index, Integral):
            raise TypeError("observation index must be an integer non-boolean value")
        position = int(index)
        if position < 0 or position >= self.n_observations:
            raise IndexError("observation index is out of range")
        return self._observation_space.states[position]

    @property
    def detection_probability(self) -> np.ndarray:
        return self._detection_probability

    @property
    def confusion_matrix(self) -> np.ndarray:
        return self._confusion_matrix

    @property
    def reference_mass(self) -> np.ndarray:
        return self._reference_mass

    @property
    def contamination_probability(self) -> float:
        return self._contamination_probability

    @property
    def clean_kernel_mass(self) -> np.ndarray:
        return self._clean_kernel_mass

    @property
    def kernel_mass(self) -> np.ndarray:
        return self._kernel_mass

    @property
    def density_kernel(self) -> np.ndarray:
        return self._density_kernel

    @property
    def log_density_kernel(self) -> np.ndarray:
        return self._log_density_kernel

    @property
    def lower_bound(self) -> float:
        """Minimum theorem-facing density, at least contamination probability."""

        return float(np.min(self._density_kernel))

    @property
    def upper_bound(self) -> float:
        return float(np.max(self._density_kernel))

    def _clean_log_distribution(
        self, latent_counts: AtomicCountVector
    ) -> Mapping[AtomicCountVector, float]:
        zero = (0,) * self._observation_space.atom_count
        dynamic = {zero: 0.0}
        for latent_atom, count in enumerate(latent_counts):
            log_miss = math.log1p(-self._detection_probability[latent_atom])
            log_detection = math.log(self._detection_probability[latent_atom])
            for _ in range(count):
                updated = {}
                for partial, log_prefix in dynamic.items():
                    updated[partial] = _logaddexp(
                        updated.get(partial, -math.inf), log_prefix + log_miss
                    )
                    for observed_atom in range(
                        self._observation_space.atom_count
                    ):
                        confusion = self._confusion_matrix[
                            latent_atom, observed_atom
                        ]
                        if confusion == 0.0:
                            continue
                        destination = _incremented_within_cap(
                            partial,
                            observed_atom,
                            self._observation_space.total_cap,
                        )
                        if destination is None:
                            raise ArithmeticError(
                                "clean association exceeded the declared anchor cap"
                            )
                        log_outcome = (
                            log_prefix
                            + log_detection
                            + math.log(confusion)
                        )
                        updated[destination] = _logaddexp(
                            updated.get(destination, -math.inf), log_outcome
                        )
                dynamic = updated
        return dynamic

    def mass_row(self, latent_counts: object) -> np.ndarray:
        index = self._latent_space.index_of(latent_counts)  # type: ignore[arg-type]
        return _immutable_float_array(self._kernel_mass[index])

    def density_row(self, latent_counts: object) -> np.ndarray:
        index = self._latent_space.index_of(latent_counts)  # type: ignore[arg-type]
        return _immutable_float_array(self._density_kernel[index])

    def likelihood(self, observed_counts: object) -> np.ndarray:
        """Return theorem-facing density values over all latent states."""

        index = self.index_of_observation(observed_counts)
        return _immutable_float_array(self._density_kernel[:, index])

    def probability(
        self, latent_counts: object, observed_counts: object
    ) -> float:
        latent_index = self._latent_space.index_of(  # type: ignore[arg-type]
            latent_counts
        )
        observed_index = self.index_of_observation(observed_counts)
        return float(self._kernel_mass[latent_index, observed_index])

    def density(self, latent_counts: object, observed_counts: object) -> float:
        latent_index = self._latent_space.index_of(  # type: ignore[arg-type]
            latent_counts
        )
        observed_index = self.index_of_observation(observed_counts)
        return float(self._density_kernel[latent_index, observed_index])


class FiniteAtomicAssociationBridgeOracle:
    """Exact bridge using one positive association-marginalized density."""

    def __init__(
        self,
        latent_space: FiniteAtomicCountingSpace,
        observation: Union[
            PositiveFiniteAtomicObservation,
            PositiveFiniteAtomicOverflowObservation,
        ],
        birth_rates: ExplicitAtomicVector,
        per_particle_death_rates: ExplicitAtomicVector,
        replacement_rates: ExplicitReplacementRates,
    ) -> None:
        if not isinstance(latent_space, FiniteAtomicCountingSpace):
            raise TypeError("latent_space must be a FiniteAtomicCountingSpace")
        if not isinstance(
            observation,
            (
                PositiveFiniteAtomicObservation,
                PositiveFiniteAtomicOverflowObservation,
            ),
        ):
            raise TypeError(
                "observation must be a positive finite atomic observation"
            )
        if observation.latent_space is not latent_space:
            raise ValueError(
                "observation must be constructed from the identical latent_space"
            )
        generator = finite_atomic_generator(
            latent_space,
            birth_rates,
            per_particle_death_rates,
            replacement_rates,
        )
        self._latent_space = latent_space
        self._observation = observation
        self._generator = _immutable_float_array(validate_generator(generator))
        active = set()
        for source in range(latent_space.n_states):
            for destination in range(latent_space.n_states):
                if (
                    source == destination
                    or self._generator[source, destination] <= 0.0
                ):
                    continue
                family = self._transition_family_from_states(
                    latent_space.states[source], latent_space.states[destination]
                )
                if family is None:
                    raise ArithmeticError(
                        "positive generator edge has no declared transition family"
                    )
                active.add(family)
        self._active_transition_families = tuple(
            family for family in _FAMILY_ORDER if family in active
        )

    @property
    def latent_space(self) -> FiniteAtomicCountingSpace:
        return self._latent_space

    @property
    def observation(
        self,
    ) -> Union[
        PositiveFiniteAtomicObservation,
        PositiveFiniteAtomicOverflowObservation,
    ]:
        return self._observation

    @property
    def generator(self) -> np.ndarray:
        return self._generator

    @property
    def active_transition_families(self) -> Tuple[TransitionFamily, ...]:
        return self._active_transition_families

    @staticmethod
    def _transition_family_from_states(
        source: AtomicCountVector,
        destination: AtomicCountVector,
    ) -> Optional[TransitionFamily]:
        delta = tuple(
            destination[index] - source[index] for index in range(len(source))
        )
        positive = tuple(value for value in delta if value > 0)
        negative = tuple(value for value in delta if value < 0)
        if sum(delta) == 1 and positive == (1,) and not negative:
            return "birth"
        if sum(delta) == -1 and negative == (-1,) and not positive:
            return "death"
        if (
            sum(delta) == 0
            and positive == (1,)
            and negative == (-1,)
        ):
            return "replacement"
        return None

    def transition_family(
        self, source_counts: object, destination_counts: object
    ) -> Optional[TransitionFamily]:
        source = self._latent_space.canonicalize(source_counts)  # type: ignore[arg-type]
        destination = self._latent_space.canonicalize(  # type: ignore[arg-type]
            destination_counts
        )
        return self._transition_family_from_states(source, destination)

    def forward_transition(self, elapsed_time: object) -> np.ndarray:
        elapsed = _validated_elapsed_time(elapsed_time)
        return transition_matrix(self._generator, elapsed)

    def backward_information(
        self, elapsed_time: object, observed_counts: object
    ) -> np.ndarray:
        transition = self.forward_transition(elapsed_time)
        likelihood = self._observation.likelihood(observed_counts)
        information = transition @ likelihood
        if np.any(information <= 0.0) or not np.all(np.isfinite(information)):
            raise ArithmeticError(
                "positive observation density produced invalid information"
            )
        return _immutable_float_array(information)

    def condition(
        self,
        initial_marginal: object,
        elapsed_time: object,
        observed_counts: object,
    ) -> ConditionalBridge:
        """Condition on an observation; returned evidence is a density value.

        Multiplying ``bridge.evidence`` by the selected observation's
        ``reference_mass`` recovers its ordinary physical probability mass.
        The normalized conditional laws are identical under either convention.
        """

        initial = validate_probability_vector(
            initial_marginal, self._latent_space.n_states
        )
        return conditional_bridge(
            initial,
            self.forward_transition(elapsed_time),
            self._observation.likelihood(observed_counts),
            unreachable_policy="raise",
        )

    def bridge_generator(
        self, time_to_observation: object, observed_counts: object
    ) -> np.ndarray:
        information = self.backward_information(
            time_to_observation, observed_counts
        )
        return information_tilt_generator(self._generator, np.log(information))


__all__ = [
    "AtomicCountVector",
    "FiniteAtomicAssociationBridgeOracle",
    "PositiveFiniteAtomicObservation",
    "TransitionFamily",
]
