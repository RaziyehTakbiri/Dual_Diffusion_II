"""Enumerable continuous-time Markov chains on finite event configurations.

The state space is a collection of *sets* of typed atomic events.  A universe
is finite, so all configurations up to a declared cardinality can be enumerated
exactly.  Generator matrices use the row convention: ``Q[i, j]`` is the rate
from state ``i`` to state ``j`` and a row marginal evolves as ``dp/dt = p Q``.

These routines are a reference implementation on an unlabelled **finite
counting-measure** state space, not a scalable simulator. Their purpose is to
make basic normalization and reversal claims numerically falsifiable. They do
not validate the Lebesgue--Poisson/Janossy ``1/n!`` factors, Mecke adjoints, or
continuous-location densities required by the proposed configuration process.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from numbers import Integral, Real
from typing import (
    Any,
    Callable,
    FrozenSet,
    Hashable,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import numpy as np
from scipy.linalg import expm


class GeneratorValidationError(ValueError):
    """Raised when an array is not a conservative CTMC generator."""


class ProbabilityValidationError(ValueError):
    """Raised when an array is not a normalized probability vector."""


@dataclass(frozen=True)
class AtomicEvent:
    """One indivisible event in a finite typed universe.

    Parameters
    ----------
    atom_id:
        Stable simulator identity. It is excluded from equality and hashing,
        so it cannot create two labelled copies of the same physical event.
        Identities must nevertheless be unique within a
        :class:`ConfigurationSpace` for diagnostics.
    event_type:
        Discrete event stratum/type.
    mark:
        Optional finite mark.  The exact toy engine requires every field to be
        hashable; continuous marks should therefore be discretized into atoms.
    physical_time:
        Optional discrete physical-time atom.  It is part of event identity and
        must be hashable in this finite reference engine.
    """

    atom_id: Hashable = field(compare=False, hash=False)
    event_type: Hashable
    mark: Optional[Hashable] = None
    physical_time: Optional[Hashable] = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("atom_id", self.atom_id),
            ("event_type", self.event_type),
            ("mark", self.mark),
            ("physical_time", self.physical_time),
        ):
            try:
                hash(value)
            except TypeError as error:
                raise TypeError(
                    "AtomicEvent.%s must be hashable, got %r"
                    % (field_name, type(value).__name__)
                ) from error


Configuration = FrozenSet[AtomicEvent]


class ConfigurationSpace:
    """All subsets of a finite event universe up to ``max_cardinality``.

    Configurations are represented as :class:`frozenset` objects.  Consequently
    ``[a, b]``, ``[b, a]``, and ``frozenset({a, b})`` identify the same state.
    State enumeration is deterministic relative to the supplied universe order,
    but no transition rule depends on the order in which a configuration is
    presented.
    """

    def __init__(
        self,
        events: Iterable[AtomicEvent],
        max_cardinality: Optional[int] = None,
    ) -> None:
        self.events: Tuple[AtomicEvent, ...] = tuple(events)
        if any(not isinstance(event, AtomicEvent) for event in self.events):
            raise TypeError("events must contain only AtomicEvent instances")

        event_set = set(self.events)
        if len(event_set) != len(self.events):
            raise ValueError(
                "the event universe contains duplicate physical atoms "
                "(type, time, and mark must identify a simple event)"
            )

        atom_ids = [event.atom_id for event in self.events]
        if len(set(atom_ids)) != len(atom_ids):
            raise ValueError("AtomicEvent.atom_id values must be unique")

        if max_cardinality is None:
            max_cardinality = len(self.events)
        if isinstance(max_cardinality, bool) or not isinstance(
            max_cardinality, Integral
        ):
            raise TypeError("max_cardinality must be an integer")
        if max_cardinality < 0 or max_cardinality > len(self.events):
            raise ValueError(
                "max_cardinality must lie between zero and the universe size"
            )

        self.max_cardinality = int(max_cardinality)
        self._event_set = event_set
        self._event_positions = {
            event: position for position, event in enumerate(self.events)
        }
        self.states: Tuple[Configuration, ...] = tuple(
            frozenset(subset)
            for cardinality in range(self.max_cardinality + 1)
            for subset in combinations(self.events, cardinality)
        )
        self._state_indices = {
            state: index for index, state in enumerate(self.states)
        }

    def __len__(self) -> int:
        return len(self.states)

    @property
    def n_states(self) -> int:
        """Number of enumerated configurations."""

        return len(self.states)

    def canonicalize(self, events: Iterable[AtomicEvent]) -> Configuration:
        """Convert any event iterable to its validated set configuration."""

        state = frozenset(events)
        unknown = state.difference(self._event_set)
        if unknown:
            raise KeyError("configuration contains atoms outside the universe: %r" % unknown)
        if len(state) > self.max_cardinality:
            raise ValueError(
                "configuration cardinality %d exceeds maximum %d"
                % (len(state), self.max_cardinality)
            )
        return state

    def index_of(self, events: Iterable[AtomicEvent]) -> int:
        """Return the matrix index of a configuration."""

        return self._state_indices[self.canonicalize(events)]

    def event_position(self, event: AtomicEvent) -> int:
        """Return the stable position of an atom in the declared universe."""

        try:
            return self._event_positions[event]
        except KeyError as error:
            raise KeyError("event is outside the declared universe: %r" % (event,)) from error


UnaryRateCallable = Callable[[Configuration, AtomicEvent], float]
UnaryRateSpec = Union[
    Real,
    Sequence[float],
    np.ndarray,
    Mapping[AtomicEvent, float],
    UnaryRateCallable,
]
ReplacementRateCallable = Callable[[Configuration, AtomicEvent, AtomicEvent], float]
ReplacementRateSpec = Union[
    Real,
    Sequence[Sequence[float]],
    np.ndarray,
    Mapping[Tuple[AtomicEvent, AtomicEvent], float],
    ReplacementRateCallable,
]


def _checked_rate(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError("%s rates must be real numbers, not booleans" % name)
    try:
        rate = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError("%s rate %r is not a real number" % (name, value)) from error
    if not np.isfinite(rate):
        raise ValueError("%s rates must be finite" % name)
    if rate < 0.0:
        raise ValueError("%s rates must be nonnegative" % name)
    return rate


def _unary_rate(
    rates: UnaryRateSpec,
    space: ConfigurationSpace,
    state: Configuration,
    event: AtomicEvent,
    name: str,
) -> float:
    if callable(rates):
        return _checked_rate(rates(state, event), name)
    if isinstance(rates, Mapping):
        return _checked_rate(rates.get(event, 0.0), name)
    if isinstance(rates, Real):
        return _checked_rate(rates, name)

    array = np.asarray(rates, dtype=float)
    if array.shape != (len(space.events),):
        raise ValueError(
            "%s rate array must have shape (%d,), got %r"
            % (name, len(space.events), array.shape)
        )
    return _checked_rate(array[space.event_position(event)], name)


def _replacement_rate(
    rates: ReplacementRateSpec,
    space: ConfigurationSpace,
    state: Configuration,
    source: AtomicEvent,
    destination: AtomicEvent,
) -> float:
    if callable(rates):
        return _checked_rate(
            rates(state, source, destination), "replacement"
        )
    if isinstance(rates, Mapping):
        return _checked_rate(rates.get((source, destination), 0.0), "replacement")
    if isinstance(rates, Real):
        return _checked_rate(rates, "replacement")

    array = np.asarray(rates, dtype=float)
    expected_shape = (len(space.events), len(space.events))
    if array.shape != expected_shape:
        raise ValueError(
            "replacement rate array must have shape %r, got %r"
            % (expected_shape, array.shape)
        )
    return _checked_rate(
        array[space.event_position(source), space.event_position(destination)],
        "replacement",
    )


def generator_from_off_diagonal(off_diagonal: np.ndarray) -> np.ndarray:
    """Create a conservative generator from nonnegative off-diagonal rates.

    Any supplied diagonal entries are ignored.  The returned diagonal is the
    negative sum of the other entries in its row.
    """

    rates = np.asarray(off_diagonal, dtype=float)
    if rates.ndim != 2 or rates.shape[0] != rates.shape[1]:
        raise GeneratorValidationError("off-diagonal rates must be a square matrix")
    if not np.all(np.isfinite(rates)):
        raise GeneratorValidationError("off-diagonal rates must be finite")

    generator = rates.copy()
    np.fill_diagonal(generator, 0.0)
    if np.any(generator < 0.0):
        raise GeneratorValidationError("off-diagonal rates must be nonnegative")
    np.fill_diagonal(generator, -generator.sum(axis=1))
    return generator


def birth_generator(
    space: ConfigurationSpace,
    rates: UnaryRateSpec,
) -> np.ndarray:
    """Construct rates for adding one absent atom.

    Births from a configuration at ``max_cardinality`` are disabled.  A rate
    callable receives ``(source_configuration, atom_to_add)``.
    """

    off_diagonal = np.zeros((space.n_states, space.n_states), dtype=float)
    for source_index, state in enumerate(space.states):
        if len(state) >= space.max_cardinality:
            continue
        for event in space.events:
            if event in state:
                continue
            rate = _unary_rate(rates, space, state, event, "birth")
            if rate == 0.0:
                continue
            destination = state.union((event,))
            destination_index = space._state_indices[destination]
            off_diagonal[source_index, destination_index] += rate
    return generator_from_off_diagonal(off_diagonal)


def death_generator(
    space: ConfigurationSpace,
    rates: UnaryRateSpec,
) -> np.ndarray:
    """Construct rates for removing one present atom.

    A rate callable receives ``(source_configuration, atom_to_remove)``.
    """

    off_diagonal = np.zeros((space.n_states, space.n_states), dtype=float)
    for source_index, state in enumerate(space.states):
        for event in state:
            rate = _unary_rate(rates, space, state, event, "death")
            if rate == 0.0:
                continue
            destination = state.difference((event,))
            destination_index = space._state_indices[destination]
            off_diagonal[source_index, destination_index] += rate
    return generator_from_off_diagonal(off_diagonal)


def replacement_generator(
    space: ConfigurationSpace,
    rates: ReplacementRateSpec,
) -> np.ndarray:
    """Construct cardinality-preserving atomic replacement rates.

    A present ``source`` may be replaced only by an absent ``destination``.
    Therefore every enabled transition preserves configuration cardinality and
    may change both event type and mark in one normalized jump.  A callable
    receives ``(configuration, source, destination)``.
    """

    off_diagonal = np.zeros((space.n_states, space.n_states), dtype=float)
    for source_index, state in enumerate(space.states):
        for source in state:
            for destination in space.events:
                if destination in state:
                    continue
                rate = _replacement_rate(
                    rates, space, state, source, destination
                )
                if rate == 0.0:
                    continue
                target = state.difference((source,)).union((destination,))
                target_index = space._state_indices[target]
                off_diagonal[source_index, target_index] += rate
    return generator_from_off_diagonal(off_diagonal)


def validate_generator(generator: np.ndarray, atol: float = 1e-12) -> np.ndarray:
    """Validate and return a defensive copy of a row-convention generator."""

    raw = np.asarray(generator)
    if raw.dtype.kind == "b":
        raise TypeError("generator must not have boolean dtype")
    if raw.dtype.kind not in "iuf":
        raise TypeError("generator must have a real numeric dtype")
    matrix = raw.astype(float, copy=False)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise GeneratorValidationError("generator must be a square matrix")
    if not np.all(np.isfinite(matrix)):
        raise GeneratorValidationError("generator entries must be finite")
    if isinstance(atol, bool) or not isinstance(atol, Real):
        raise TypeError("atol must be a real non-boolean number")
    if not np.isfinite(float(atol)) or atol < 0.0:
        raise ValueError("atol must be finite and nonnegative")

    diagonal = np.diag(matrix)
    off_diagonal = matrix.copy()
    np.fill_diagonal(off_diagonal, 0.0)
    if np.any(off_diagonal < 0.0):
        raise GeneratorValidationError("generator has a negative off-diagonal rate")
    if np.any(diagonal > 0.0):
        raise GeneratorValidationError("generator has a positive diagonal entry")
    if not np.allclose(matrix.sum(axis=1), 0.0, atol=atol, rtol=0.0):
        raise GeneratorValidationError("generator rows must sum to zero")
    return matrix.copy()


def combine_generators(*generators: np.ndarray) -> np.ndarray:
    """Add generator components after validating shape and conservation."""

    if not generators:
        raise ValueError("at least one generator is required")
    checked = [validate_generator(generator) for generator in generators]
    shape = checked[0].shape
    if any(generator.shape != shape for generator in checked[1:]):
        raise ValueError("all generators must have the same shape")
    combined = np.sum(np.stack(checked, axis=0), axis=0)
    return validate_generator(combined)


def validate_probability_vector(
    probabilities: np.ndarray,
    n_states: Optional[int] = None,
    atol: float = 1e-12,
) -> np.ndarray:
    """Validate and return a defensive copy of a normalized row marginal."""

    raw = np.asarray(probabilities)
    if raw.dtype.kind == "b":
        raise TypeError("probabilities must not have boolean dtype")
    if raw.dtype.kind not in "iuf":
        raise TypeError("probabilities must have a real numeric dtype")
    vector = raw.astype(float, copy=False)
    if vector.ndim != 1:
        raise ProbabilityValidationError("probabilities must be one-dimensional")
    if n_states is not None and vector.shape != (n_states,):
        raise ProbabilityValidationError(
            "expected %d probabilities, got %d" % (n_states, vector.size)
        )
    if not np.all(np.isfinite(vector)):
        raise ProbabilityValidationError("probabilities must be finite")
    if isinstance(atol, bool) or not isinstance(atol, Real):
        raise TypeError("atol must be a real non-boolean number")
    if not np.isfinite(float(atol)) or atol < 0.0:
        raise ValueError("atol must be finite and nonnegative")
    if np.any(vector < 0.0):
        raise ProbabilityValidationError("probabilities must be nonnegative")
    if not np.isclose(vector.sum(), 1.0, atol=atol, rtol=0.0):
        raise ProbabilityValidationError("probabilities must sum to one")

    return vector.copy()


def transition_matrix(generator: np.ndarray, elapsed_time: float) -> np.ndarray:
    """Return ``exp(elapsed_time * generator)`` as a stochastic matrix."""

    matrix = validate_generator(generator)
    if isinstance(elapsed_time, bool) or not isinstance(elapsed_time, Real):
        raise TypeError("elapsed_time must be a real number")
    duration = float(elapsed_time)
    if not np.isfinite(duration) or duration < 0.0:
        raise ValueError("elapsed_time must be finite and nonnegative")

    transition = expm(duration * matrix)
    numerical_tolerance = 1e-11
    if np.any(transition < -numerical_tolerance):
        raise ArithmeticError("matrix exponential produced a negative transition")
    if not np.allclose(
        transition.sum(axis=1), 1.0, atol=numerical_tolerance, rtol=0.0
    ):
        raise ArithmeticError("matrix exponential did not conserve row mass")
    # This repair is confined to a matrix exponential computed inside the
    # oracle. Public probability/generator validators fail closed and never
    # repair user-supplied negative values.
    transition[transition < 0.0] = 0.0
    transition /= transition.sum(axis=1, keepdims=True)
    return transition


def propagate_marginal(
    initial: np.ndarray,
    generator: np.ndarray,
    elapsed_time: float,
) -> np.ndarray:
    """Propagate a normalized row marginal through a homogeneous CTMC."""

    matrix = validate_generator(generator)
    marginal = validate_probability_vector(initial, matrix.shape[0])
    result = marginal @ transition_matrix(matrix, elapsed_time)
    return validate_probability_vector(result, matrix.shape[0], atol=1e-11)
