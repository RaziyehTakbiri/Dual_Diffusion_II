"""Exact capped CTMC oracle on a finite atomic counting space.

This module is deliberately small and classical.  It represents an unlabelled
finite counting measure by a vector ``n = (n_0, ..., n_{K-1})`` over named
atoms, allowing repeated occupancy while imposing the hard resource bound
``sum(n) <= N``.  It is an executable check of factorial reference masses,
the finite-atomic Mecke identity, multiplicity-correct edit rates, reversal,
and finite-state path likelihoods.  It is not a scalable simulator, a neural
model, or a process-novelty claim.

All generators use the row convention: ``Q[i, j]`` is the rate from state
``i`` to state ``j``.  Birth, death, and replacement rates are respectively

``n -> n + e_j``                 at ``beta_j`` (below the cap),
``n -> n - e_j``                 at ``n_j * delta_j``, and
``n -> n - e_x + e_y``           at ``n_x * r_xy`` for ``x != y``.

In particular, births and replacements into already occupied atoms are valid.
The aggregate multiplicity factors are essential because particles occupying
the same atom are indistinguishable but each can realize the edit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from numbers import Integral, Real
from types import MappingProxyType
from typing import (
    Hashable,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import numpy as np

from .exact_reversal import reverse_generator
from .finite_state import (
    combine_generators,
    validate_generator,
    validate_probability_vector,
)
from .path_kl import CTMCPathKLDivergence, ctmc_path_kl


AtomicCountVector = Tuple[int, ...]
ExplicitAtomicVector = Union[Sequence[float], np.ndarray, Mapping[Hashable, float]]
ExplicitReplacementRates = Union[
    Sequence[Sequence[float]],
    np.ndarray,
    Mapping[Tuple[Hashable, Hashable], float],
]


MAX_FINITE_ATOMIC_ATOMS = 64
MAX_FINITE_ATOMIC_CAP = 255
MAX_FINITE_ATOMIC_STATES = 256
MAX_REALIZED_PATH_JUMPS = 100_000


def _bounded_tuple(value: object, *, name: str, maximum_items: int) -> Tuple[object, ...]:
    try:
        iterator = iter(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("%s must be iterable" % name) from error
    items = []
    for item in iterator:
        if len(items) >= maximum_items:
            raise ValueError(
                "%s exceeds the finite oracle limit of %d items"
                % (name, maximum_items)
            )
        items.append(item)
    return tuple(items)


def _reject_boolean_entries(value: object, *, name: str) -> None:
    try:
        entries = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    if any(isinstance(entry, (bool, np.bool_)) for entry in entries.flat):
        raise TypeError("%s must not contain boolean entries" % name)


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
        raise ValueError(
            "%s must lie between %d and %d" % (name, minimum, maximum)
        )
    return result


def _validated_nonnegative_real(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % name)
    if result < 0.0:
        raise ValueError("%s must be nonnegative" % name)
    return result


def _immutable_array(value: np.ndarray, *, dtype: np.dtype = np.dtype(float)) -> np.ndarray:
    array = np.asarray(value, dtype=dtype)
    return np.frombuffer(array.tobytes(order="C"), dtype=dtype).reshape(array.shape)


def _compositions(total: int, parts: int) -> Iterator[AtomicCountVector]:
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for remainder in _compositions(total - first, parts - 1):
            yield (first,) + remainder


@dataclass(frozen=True, eq=False, init=False)
class FiniteAtomicCountingSpace:
    """All nonnegative count vectors on named atoms up to a total cap.

    The hard limits keep every matrix operation exact and enumerable.  The
    number of states is checked *before* enumeration and equals
    ``comb(total_cap + atom_count, atom_count)``.
    """

    atom_names: Tuple[Hashable, ...]
    total_cap: int
    states: Tuple[AtomicCountVector, ...] = field(repr=False)
    _atom_positions: Mapping[Hashable, int] = field(repr=False)
    _state_indices: Mapping[AtomicCountVector, int] = field(repr=False)

    def __init__(self, atom_names: Iterable[Hashable], total_cap: int) -> None:
        atoms = _bounded_tuple(
            atom_names,
            name="atom_names",
            maximum_items=MAX_FINITE_ATOMIC_ATOMS,
        )
        if not atoms:
            raise ValueError("atom_names must contain at least one atom")
        for atom in atoms:
            try:
                hash(atom)
            except TypeError as error:
                raise TypeError("every atom name must be hashable") from error
        if len(set(atoms)) != len(atoms):
            raise ValueError("atom_names must be unique")

        cap = _validated_integer(
            total_cap,
            name="total_cap",
            minimum=0,
            maximum=MAX_FINITE_ATOMIC_CAP,
        )
        expected = math.comb(cap + len(atoms), len(atoms))
        if expected > MAX_FINITE_ATOMIC_STATES:
            raise ValueError(
                "counting space would have %d states, exceeding the finite "
                "oracle limit of %d"
                % (expected, MAX_FINITE_ATOMIC_STATES)
            )

        states = tuple(
            state
            for total in range(cap + 1)
            for state in _compositions(total, len(atoms))
        )
        if len(states) != expected or len(set(states)) != expected:
            raise ArithmeticError("count-vector enumeration is inconsistent")

        object.__setattr__(self, "atom_names", atoms)
        object.__setattr__(self, "total_cap", cap)
        object.__setattr__(self, "states", states)
        object.__setattr__(
            self,
            "_atom_positions",
            MappingProxyType({atom: index for index, atom in enumerate(atoms)}),
        )
        object.__setattr__(
            self,
            "_state_indices",
            MappingProxyType({state: index for index, state in enumerate(states)}),
        )

    def __len__(self) -> int:
        return len(self.states)

    @property
    def atom_count(self) -> int:
        """Number of named atoms."""

        return len(self.atom_names)

    @property
    def n_states(self) -> int:
        """Number of enumerated count vectors."""

        return len(self.states)

    @property
    def expected_state_count(self) -> int:
        """Closed-form state count ``C(N + K, K)``."""

        return math.comb(self.total_cap + self.atom_count, self.atom_count)

    def canonicalize(self, counts: Iterable[int]) -> AtomicCountVector:
        """Return a validated count vector without numeric coercion."""

        raw = _bounded_tuple(
            counts,
            name="counts",
            maximum_items=self.atom_count + 1,
        )
        if len(raw) != self.atom_count:
            raise ValueError(
                "counts must have length %d, got %d"
                % (self.atom_count, len(raw))
            )
        checked = []
        for value in raw:
            if isinstance(value, (bool, np.bool_)) or not isinstance(
                value, Integral
            ):
                raise TypeError("counts must contain integer non-boolean values")
            integer = int(value)
            if integer < 0:
                raise ValueError("counts must be nonnegative")
            checked.append(integer)
        state = tuple(checked)
        if sum(state) > self.total_cap:
            raise ValueError(
                "count total %d exceeds cap %d" % (sum(state), self.total_cap)
            )
        if state not in self._state_indices:
            raise ArithmeticError("validated state is absent from the enumeration")
        return state

    def index_of(self, counts: Iterable[int]) -> int:
        """Return the matrix index of a validated count vector."""

        return self._state_indices[self.canonicalize(counts)]

    def atom_position(self, atom_name: Hashable) -> int:
        """Return the declared coordinate of an atom name."""

        try:
            return self._atom_positions[atom_name]
        except (KeyError, TypeError) as error:
            raise KeyError("unknown atom name %r" % (atom_name,)) from error

    def incremented(
        self, counts: Iterable[int], atom_name: Hashable
    ) -> AtomicCountVector:
        """Add one count, raising rather than crossing the declared cap."""

        state = self.canonicalize(counts)
        if sum(state) >= self.total_cap:
            raise ValueError("cannot increment a state at the total cap")
        position = self.atom_position(atom_name)
        result = list(state)
        result[position] += 1
        return self.canonicalize(result)

    def decremented(
        self, counts: Iterable[int], atom_name: Hashable
    ) -> AtomicCountVector:
        """Remove one count, rejecting an unoccupied source atom."""

        state = self.canonicalize(counts)
        position = self.atom_position(atom_name)
        if state[position] == 0:
            raise ValueError("cannot decrement an unoccupied atom")
        result = list(state)
        result[position] -= 1
        return self.canonicalize(result)

    def replaced(
        self,
        counts: Iterable[int],
        source_atom: Hashable,
        destination_atom: Hashable,
    ) -> AtomicCountVector:
        """Move one count between distinct atoms, including occupied targets."""

        state = self.canonicalize(counts)
        source = self.atom_position(source_atom)
        destination = self.atom_position(destination_atom)
        if source == destination:
            raise ValueError("replacement atoms must be distinct")
        if state[source] == 0:
            raise ValueError("cannot replace from an unoccupied atom")
        result = list(state)
        result[source] -= 1
        result[destination] += 1
        return self.canonicalize(result)


def _explicit_vector(
    space: FiniteAtomicCountingSpace,
    values: ExplicitAtomicVector,
    *,
    name: str,
) -> np.ndarray:
    if isinstance(values, Mapping):
        supplied = set(values.keys())
        expected = set(space.atom_names)
        if supplied != expected or len(values) != space.atom_count:
            raise ValueError(
                "%s mapping must specify every atom exactly once" % name
            )
        result = np.asarray(
            [
                _validated_nonnegative_real(values[atom], name=name)
                for atom in space.atom_names
            ],
            dtype=float,
        )
        return result

    try:
        raw = np.asarray(values)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be a numeric vector" % name) from error
    _reject_boolean_entries(values, name=name)
    if raw.dtype.kind == "b":
        raise TypeError("%s must not have boolean dtype" % name)
    if raw.dtype.kind not in "iuf":
        raise TypeError("%s must have a real numeric dtype" % name)
    if raw.ndim != 1 or raw.shape != (space.atom_count,):
        raise ValueError(
            "%s must have shape (%d,)" % (name, space.atom_count)
        )
    try:
        result = raw.astype(float, copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s cannot be represented as floats" % name) from error
    if not np.all(np.isfinite(result)):
        raise ValueError("%s entries must be finite" % name)
    if np.any(result < 0.0):
        raise ValueError("%s entries must be nonnegative" % name)
    return result


def _explicit_replacement_matrix(
    space: FiniteAtomicCountingSpace,
    rates: ExplicitReplacementRates,
) -> np.ndarray:
    shape = (space.atom_count, space.atom_count)
    if isinstance(rates, Mapping):
        expected = {
            (source, destination)
            for source in space.atom_names
            for destination in space.atom_names
            if source != destination
        }
        supplied = set(rates.keys())
        if supplied != expected or len(rates) != len(expected):
            raise ValueError(
                "replacement_rates mapping must specify every ordered pair "
                "of distinct atoms exactly once"
            )
        result = np.zeros(shape, dtype=float)
        for source, destination in expected:
            source_index = space.atom_position(source)
            destination_index = space.atom_position(destination)
            result[source_index, destination_index] = _validated_nonnegative_real(
                rates[(source, destination)], name="replacement_rates"
            )
        return result

    try:
        raw = np.asarray(rates)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("replacement_rates must be a numeric matrix") from error
    _reject_boolean_entries(rates, name="replacement_rates")
    if raw.dtype.kind == "b":
        raise TypeError("replacement_rates must not have boolean dtype")
    if raw.dtype.kind not in "iuf":
        raise TypeError("replacement_rates must have a real numeric dtype")
    if raw.ndim != 2 or raw.shape != shape:
        raise ValueError("replacement_rates must have shape %r" % (shape,))
    try:
        result = raw.astype(float, copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(
            "replacement_rates cannot be represented as floats"
        ) from error
    if not np.all(np.isfinite(result)):
        raise ValueError("replacement_rates entries must be finite")
    if np.any(result < 0.0):
        raise ValueError("replacement_rates entries must be nonnegative")
    if np.any(np.diag(result) != 0.0):
        raise ValueError("replacement_rates diagonal must be exactly zero")
    return result


def _generator_from_off_diagonal(rates: np.ndarray) -> np.ndarray:
    matrix = np.asarray(rates, dtype=float).copy()
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("internal off-diagonal rates must be square")
    if not np.all(np.isfinite(matrix)) or np.any(matrix < 0.0):
        raise ArithmeticError("constructed off-diagonal rates are invalid")
    np.fill_diagonal(matrix, 0.0)
    for source in range(matrix.shape[0]):
        try:
            exit_rate = math.fsum(float(value) for value in matrix[source])
        except OverflowError as error:
            raise ArithmeticError("constructed exit rate overflowed") from error
        if not math.isfinite(exit_rate):
            raise ArithmeticError("constructed exit rate is not finite")
        matrix[source, source] = -exit_rate
    try:
        return validate_generator(matrix)
    except ValueError as error:
        raise ArithmeticError("constructed generator failed conservation") from error


def finite_atomic_birth_generator(
    space: FiniteAtomicCountingSpace,
    birth_rates: ExplicitAtomicVector,
) -> np.ndarray:
    """Construct constant-rate births, including births onto occupied atoms."""

    rates = _explicit_vector(space, birth_rates, name="birth_rates")
    off_diagonal = np.zeros((space.n_states, space.n_states), dtype=float)
    for source_index, state in enumerate(space.states):
        if sum(state) >= space.total_cap:
            continue
        for atom_index, rate in enumerate(rates):
            if rate == 0.0:
                continue
            destination = list(state)
            destination[atom_index] += 1
            destination_index = space._state_indices[tuple(destination)]
            off_diagonal[source_index, destination_index] = float(rate)
    return _generator_from_off_diagonal(off_diagonal)


def finite_atomic_death_generator(
    space: FiniteAtomicCountingSpace,
    per_particle_death_rates: ExplicitAtomicVector,
) -> np.ndarray:
    """Construct deaths with aggregate rate ``n_j * delta_j``."""

    rates = _explicit_vector(
        space, per_particle_death_rates, name="per_particle_death_rates"
    )
    off_diagonal = np.zeros((space.n_states, space.n_states), dtype=float)
    for source_index, state in enumerate(space.states):
        for atom_index, count in enumerate(state):
            if count == 0 or rates[atom_index] == 0.0:
                continue
            rate = float(count) * float(rates[atom_index])
            if not math.isfinite(rate):
                raise ArithmeticError("aggregate death rate is not finite")
            destination = list(state)
            destination[atom_index] -= 1
            destination_index = space._state_indices[tuple(destination)]
            off_diagonal[source_index, destination_index] = rate
    return _generator_from_off_diagonal(off_diagonal)


def finite_atomic_replacement_generator(
    space: FiniteAtomicCountingSpace,
    replacement_rates: ExplicitReplacementRates,
) -> np.ndarray:
    """Construct ``x -> y`` edits at ``n_x r_xy``, even when ``y`` is occupied."""

    rates = _explicit_replacement_matrix(space, replacement_rates)
    off_diagonal = np.zeros((space.n_states, space.n_states), dtype=float)
    for source_index, state in enumerate(space.states):
        for source_atom, count in enumerate(state):
            if count == 0:
                continue
            for destination_atom in range(space.atom_count):
                if source_atom == destination_atom:
                    continue
                rate = float(count) * float(rates[source_atom, destination_atom])
                if not math.isfinite(rate):
                    raise ArithmeticError("aggregate replacement rate is not finite")
                if rate == 0.0:
                    continue
                destination = list(state)
                destination[source_atom] -= 1
                destination[destination_atom] += 1
                destination_index = space._state_indices[tuple(destination)]
                off_diagonal[source_index, destination_index] = rate
    return _generator_from_off_diagonal(off_diagonal)


def finite_atomic_generator(
    space: FiniteAtomicCountingSpace,
    birth_rates: ExplicitAtomicVector,
    per_particle_death_rates: ExplicitAtomicVector,
    replacement_rates: ExplicitReplacementRates,
) -> np.ndarray:
    """Construct and combine all three multiplicity-correct edit components."""

    return combine_generators(
        finite_atomic_birth_generator(space, birth_rates),
        finite_atomic_death_generator(space, per_particle_death_rates),
        finite_atomic_replacement_generator(space, replacement_rates),
    )


def capped_counting_reference(
    space: FiniteAtomicCountingSpace,
    weights: ExplicitAtomicVector,
) -> np.ndarray:
    """Return normalized masses proportional to ``prod_j w_j^n_j / n_j!``.

    Zero weights are allowed: every state with a positive count at such an
    atom has exactly zero mass.  Positive weights whose normalized masses
    cannot all be represented in ``float64`` are rejected instead of silently
    creating artificial zeros.
    """

    values = _explicit_vector(space, weights, name="weights")
    log_masses = np.empty(space.n_states, dtype=float)
    for index, state in enumerate(space.states):
        terms = []
        impossible = False
        for count, weight in zip(state, values):
            if count == 0:
                continue
            if weight == 0.0:
                impossible = True
                break
            terms.append(count * math.log(float(weight)) - math.lgamma(count + 1.0))
        log_masses[index] = -math.inf if impossible else math.fsum(terms)

    finite_logs = log_masses[np.isfinite(log_masses)]
    if finite_logs.size == 0:
        raise ArithmeticError("capped reference has no representable support")
    maximum = float(np.max(finite_logs))
    shifted = np.zeros(space.n_states, dtype=float)
    finite = np.isfinite(log_masses)
    shifted[finite] = np.exp(log_masses[finite] - maximum)
    if np.any(shifted[finite] == 0.0):
        raise ArithmeticError(
            "a mathematically positive capped reference mass underflowed"
        )
    normalizer = math.fsum(float(value) for value in shifted)
    if not math.isfinite(normalizer) or normalizer <= 0.0:
        raise ArithmeticError("capped reference normalization failed")
    masses = shifted / normalizer
    if np.any(~np.isfinite(masses[finite])) or np.any(masses[finite] == 0.0):
        raise ArithmeticError(
            "a mathematically positive normalized capped reference mass underflowed"
        )
    checked = validate_probability_vector(masses, space.n_states, atol=1.0e-14)
    return _immutable_array(checked)


def capped_mecke_residuals(
    space: FiniteAtomicCountingSpace,
    weights: ExplicitAtomicVector,
    masses: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Return local residuals of the capped finite-atomic Mecke relation.

    For every state below the cap and atom ``j``, the checked identity is

    ``mu(n) * w_j = mu(n + e_j) * (n_j + 1)``.

    Rows at the cap are zero because no admissible insertion edge exists.
    """

    values = _explicit_vector(space, weights, name="weights")
    if masses is None:
        probabilities = capped_counting_reference(space, values)
    else:
        probabilities = validate_probability_vector(masses, space.n_states)
    residuals = np.zeros((space.n_states, space.atom_count), dtype=float)
    for source_index, state in enumerate(space.states):
        if sum(state) >= space.total_cap:
            continue
        for atom_index, weight in enumerate(values):
            destination = list(state)
            destination[atom_index] += 1
            destination_index = space._state_indices[tuple(destination)]
            residuals[source_index, atom_index] = (
                float(probabilities[source_index]) * float(weight)
                - float(probabilities[destination_index])
                * float(state[atom_index] + 1)
            )
    if not np.all(np.isfinite(residuals)):
        raise ArithmeticError("Mecke residuals are not finite")
    return _immutable_array(residuals)


def capped_mecke_sums(
    space: FiniteAtomicCountingSpace,
    weights: ExplicitAtomicVector,
    test_values: np.ndarray,
    masses: Optional[np.ndarray] = None,
) -> Tuple[float, float]:
    """Return the removal and insertion sides of the capped Mecke identity.

    ``test_values[i, j]`` is ``F(j, n)`` at ``space.states[i]``.  The returned
    pair is

    ``sum_n mu(n) sum_j n_j F(j,n)`` and
    ``sum_{|m|<N} mu(m) sum_j w_j F(j,m+e_j)``.

    The boundary restriction on the insertion side is part of the capped
    reference; omitting it would compare two different measures.
    """

    values = _explicit_vector(space, weights, name="weights")
    if masses is None:
        probabilities = capped_counting_reference(space, values)
    else:
        probabilities = validate_probability_vector(masses, space.n_states)
    try:
        raw_test = np.asarray(test_values)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("test_values must be a numeric matrix") from error
    _reject_boolean_entries(test_values, name="test_values")
    if raw_test.dtype.kind == "b":
        raise TypeError("test_values must not have boolean dtype")
    if raw_test.dtype.kind not in "iuf":
        raise TypeError("test_values must have a real numeric dtype")
    if raw_test.shape != (space.n_states, space.atom_count):
        raise ValueError(
            "test_values must have shape (%d, %d)"
            % (space.n_states, space.atom_count)
        )
    tests = raw_test.astype(float, copy=False)
    if not np.all(np.isfinite(tests)):
        raise ValueError("test_values entries must be finite")

    removal_terms = []
    insertion_terms = []
    for state_index, state in enumerate(space.states):
        mass = float(probabilities[state_index])
        for atom_index, count in enumerate(state):
            if count:
                removal_terms.append(
                    mass * float(count) * float(tests[state_index, atom_index])
                )
        if sum(state) >= space.total_cap:
            continue
        for atom_index, weight in enumerate(values):
            if weight == 0.0:
                continue
            destination = list(state)
            destination[atom_index] += 1
            destination_index = space._state_indices[tuple(destination)]
            insertion_terms.append(
                mass
                * float(weight)
                * float(tests[destination_index, atom_index])
            )
    removal = math.fsum(removal_terms)
    insertion = math.fsum(insertion_terms)
    if not math.isfinite(removal) or not math.isfinite(insertion):
        raise ArithmeticError("Mecke sums are not finite")
    return removal, insertion


def counting_state_relabel_permutation(
    source_space: FiniteAtomicCountingSpace,
    target_space: FiniteAtomicCountingSpace,
    atom_relabeling: Mapping[Hashable, Hashable],
) -> np.ndarray:
    """Map source state indices to target indices under an atom bijection."""

    if not isinstance(source_space, FiniteAtomicCountingSpace) or not isinstance(
        target_space, FiniteAtomicCountingSpace
    ):
        raise TypeError("source_space and target_space must be counting spaces")
    if source_space.total_cap != target_space.total_cap:
        raise ValueError("source and target spaces must have the same total cap")
    if not isinstance(atom_relabeling, Mapping):
        raise TypeError("atom_relabeling must be a mapping")
    if (
        set(atom_relabeling.keys()) != set(source_space.atom_names)
        or len(atom_relabeling) != source_space.atom_count
    ):
        raise ValueError("atom_relabeling must define every source atom exactly once")
    mapped_atoms = tuple(atom_relabeling[atom] for atom in source_space.atom_names)
    if (
        len(set(mapped_atoms)) != len(mapped_atoms)
        or set(mapped_atoms) != set(target_space.atom_names)
    ):
        raise ValueError("atom_relabeling must be a bijection onto target atoms")

    permutation = np.empty(source_space.n_states, dtype=np.int64)
    for source_index, state in enumerate(source_space.states):
        target = [0] * target_space.atom_count
        for source_atom_index, source_atom in enumerate(source_space.atom_names):
            target_atom = atom_relabeling[source_atom]
            target[target_space.atom_position(target_atom)] = state[source_atom_index]
        permutation[source_index] = target_space.index_of(target)
    if len(set(int(value) for value in permutation)) != source_space.n_states:
        raise ArithmeticError("state relabeling did not produce a permutation")
    return _immutable_array(permutation, dtype=np.dtype(np.int64))


def finite_atomic_reverse_generator(
    space: FiniteAtomicCountingSpace,
    forward_generator: np.ndarray,
    marginal: np.ndarray,
    *,
    zero_mass: str = "raise",
    mass_tolerance: float = 0.0,
) -> np.ndarray:
    """Apply the exact finite-state reversal after enforcing space shape."""

    generator = validate_generator(forward_generator)
    if generator.shape != (space.n_states, space.n_states):
        raise ValueError("forward_generator shape does not match counting space")
    probabilities = validate_probability_vector(marginal, space.n_states)
    return reverse_generator(
        generator,
        probabilities,
        zero_mass=zero_mass,
        mass_tolerance=mass_tolerance,
    )


def finite_atomic_reverse_flux_residuals(
    space: FiniteAtomicCountingSpace,
    forward_generator: np.ndarray,
    marginal: np.ndarray,
    *,
    zero_mass: str = "raise",
    mass_tolerance: float = 0.0,
) -> np.ndarray:
    """Return off-diagonal Bayes-flux residuals for exact reversal.

    Entry ``(i,j)`` is ``p_i Q_rev[i,j] - p_j Q_fwd[j,i]``.  Diagonal entries
    are set to zero because the identity concerns jump fluxes.
    """

    forward = validate_generator(forward_generator)
    if forward.shape != (space.n_states, space.n_states):
        raise ValueError("forward_generator shape does not match counting space")
    probabilities = validate_probability_vector(marginal, space.n_states)
    reverse = finite_atomic_reverse_generator(
        space,
        forward,
        probabilities,
        zero_mass=zero_mass,
        mass_tolerance=mass_tolerance,
    )
    residuals = probabilities[:, None] * reverse - (
        probabilities[:, None] * forward
    ).T
    np.fill_diagonal(residuals, 0.0)
    if not np.all(np.isfinite(residuals)):
        raise ArithmeticError("reverse-flux residuals are not finite")
    return _immutable_array(residuals)


@dataclass(frozen=True)
class RealizedCountingPathLogLikelihood:
    """Decomposition of a homogeneous CTMC realized-path log density."""

    initial_log_mass: float
    realized_jump_log_intensity: float
    integrated_compensator: float
    total: float
    jump_count: int

    def __post_init__(self) -> None:
        initial = _validated_log_component(
            self.initial_log_mass, name="initial_log_mass"
        )
        jumps = _validated_log_component(
            self.realized_jump_log_intensity,
            name="realized_jump_log_intensity",
        )
        compensator = _validated_nonnegative_real(
            self.integrated_compensator, name="integrated_compensator"
        )
        count = _validated_integer(
            self.jump_count,
            name="jump_count",
            minimum=0,
            maximum=MAX_REALIZED_PATH_JUMPS,
        )
        if isinstance(self.total, (bool, np.bool_)) or not isinstance(
            self.total, Real
        ):
            raise TypeError("total must be a real non-boolean number")
        total = float(self.total)
        if math.isnan(total) or total == math.inf:
            raise ValueError("total must be finite or -inf")
        expected = (
            -math.inf
            if initial == -math.inf or jumps == -math.inf
            else initial + jumps - compensator
        )
        if expected == -math.inf:
            if total != -math.inf:
                raise ValueError("total is inconsistent with path components")
        elif not math.isclose(total, expected, rel_tol=1.0e-13, abs_tol=1.0e-15):
            raise ValueError("total is inconsistent with path components")
        object.__setattr__(self, "initial_log_mass", initial)
        object.__setattr__(self, "realized_jump_log_intensity", jumps)
        object.__setattr__(self, "integrated_compensator", compensator)
        object.__setattr__(self, "total", total)
        object.__setattr__(self, "jump_count", count)


def _validated_log_component(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if math.isnan(result) or result == math.inf:
        raise ValueError("%s must be finite or -inf" % name)
    return result


def _validated_horizon(value: object) -> float:
    return _validated_nonnegative_real(value, name="horizon")


def realized_counting_path_log_likelihood(
    space: FiniteAtomicCountingSpace,
    initial: np.ndarray,
    generator: np.ndarray,
    state_path: Iterable[Iterable[int]],
    jump_times: Iterable[float],
    horizon: float,
) -> RealizedCountingPathLogLikelihood:
    """Evaluate exact realized jumps plus the integrated compensator.

    ``state_path`` contains the initial state and one state after each jump.
    ``jump_times`` must be strictly increasing and lie in the open interval
    ``(0, horizon)``.  Boundary jumps are rejected because ``state_path``
    explicitly contains both the initial and post-jump state, which is not a
    valid initial/post-jump representation at time zero.  The terminal point
    is a measure-zero boundary whose density value is not identified; the
    oracle therefore uses the canonical open-simplex density domain.
    The returned log density is

    ``log p0[n0] + sum_k log Q[n_{k-1},n_k]``
    ``- integral_0^T (-Q[n_t,n_t]) dt``.

    A zero initial mass or impossible generator edge yields ``-inf`` rather
    than an epsilon repair.  Structural path errors still raise.
    """

    matrix = validate_generator(generator)
    if matrix.shape != (space.n_states, space.n_states):
        raise ValueError("generator shape does not match counting space")
    probabilities = validate_probability_vector(initial, space.n_states)
    duration = _validated_horizon(horizon)

    raw_states = _bounded_tuple(
        state_path,
        name="state_path",
        maximum_items=MAX_REALIZED_PATH_JUMPS + 1,
    )
    if not raw_states:
        raise ValueError("state_path must contain an initial state")
    raw_times = _bounded_tuple(
        jump_times,
        name="jump_times",
        maximum_items=MAX_REALIZED_PATH_JUMPS,
    )
    if len(raw_states) != len(raw_times) + 1:
        raise ValueError("state_path must contain one state after every jump")

    states = tuple(space.canonicalize(state) for state in raw_states)
    times = []
    previous = 0.0
    for value in raw_times:
        time = _validated_nonnegative_real(value, name="jump time")
        if time <= 0.0 or time >= duration:
            raise ValueError("jump times must lie strictly inside the horizon")
        if time <= previous:
            raise ValueError("jump times must be strictly increasing")
        times.append(time)
        previous = time

    indices = tuple(space._state_indices[state] for state in states)
    for source, destination in zip(indices[:-1], indices[1:]):
        if source == destination:
            raise ValueError("a realized jump must change the state")

    initial_mass = float(probabilities[indices[0]])
    initial_log_mass = -math.inf if initial_mass == 0.0 else math.log(initial_mass)

    jump_logs = []
    impossible_jump = False
    for source, destination in zip(indices[:-1], indices[1:]):
        rate = float(matrix[source, destination])
        if rate == 0.0:
            impossible_jump = True
        else:
            jump_logs.append(math.log(rate))
    jump_log_intensity = (
        -math.inf if impossible_jump else math.fsum(jump_logs)
    )

    interval_ends = tuple(times) + (duration,)
    interval_starts = (0.0,) + tuple(times)
    compensator_terms = []
    for state_index, start, end in zip(indices, interval_starts, interval_ends):
        holding_time = end - start
        exit_rate = -float(matrix[state_index, state_index])
        compensator_terms.append(holding_time * exit_rate)
    try:
        compensator = math.fsum(compensator_terms)
    except OverflowError as error:
        raise ArithmeticError("integrated compensator overflowed") from error
    if not math.isfinite(compensator) or compensator < 0.0:
        raise ArithmeticError("integrated compensator is not representable")

    total = (
        -math.inf
        if initial_log_mass == -math.inf or jump_log_intensity == -math.inf
        else initial_log_mass + jump_log_intensity - compensator
    )
    return RealizedCountingPathLogLikelihood(
        initial_log_mass=initial_log_mass,
        realized_jump_log_intensity=jump_log_intensity,
        integrated_compensator=compensator,
        total=total,
        jump_count=len(times),
    )


def finite_atomic_path_kl(
    space: FiniteAtomicCountingSpace,
    reference_initial: np.ndarray,
    reference_generator: np.ndarray,
    candidate_initial: np.ndarray,
    candidate_generator: np.ndarray,
    horizon: float,
) -> CTMCPathKLDivergence:
    """Return exact finite-horizon path KL after enforcing counting-space shape."""

    expected_shape = (space.n_states, space.n_states)
    reference = validate_generator(reference_generator)
    candidate = validate_generator(candidate_generator)
    if reference.shape != expected_shape or candidate.shape != expected_shape:
        raise ValueError("generator shape does not match counting space")
    return ctmc_path_kl(
        reference_initial,
        reference,
        candidate_initial,
        candidate,
        horizon,
    )


__all__ = [
    "AtomicCountVector",
    "ExplicitAtomicVector",
    "ExplicitReplacementRates",
    "FiniteAtomicCountingSpace",
    "MAX_FINITE_ATOMIC_ATOMS",
    "MAX_FINITE_ATOMIC_CAP",
    "MAX_FINITE_ATOMIC_STATES",
    "MAX_REALIZED_PATH_JUMPS",
    "RealizedCountingPathLogLikelihood",
    "capped_counting_reference",
    "capped_mecke_residuals",
    "capped_mecke_sums",
    "counting_state_relabel_permutation",
    "finite_atomic_birth_generator",
    "finite_atomic_death_generator",
    "finite_atomic_generator",
    "finite_atomic_path_kl",
    "finite_atomic_replacement_generator",
    "finite_atomic_reverse_flux_residuals",
    "finite_atomic_reverse_generator",
    "realized_counting_path_log_likelihood",
]
