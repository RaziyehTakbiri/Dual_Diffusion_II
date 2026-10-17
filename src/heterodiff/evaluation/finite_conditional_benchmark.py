"""Independent, enumerable conditional-law benchmark for a finite atomic model.

This module does not import the hybrid learner, its guide, or its sampler.  All
states and observation probabilities are enumerated; transition probabilities
are computed with a finite matrix exponential.  The formulas specify an exact
finite-state CTMC, while returned arrays are floating-point numerical reference
values, not exact-arithmetic certificates.  This is a synthetic mechanism
benchmark, not a representation of either real research data domain.

State ``(n0, n1)`` is an unordered multiset with two atomic event types and at
most ``state_cap`` occurrences.  ``None`` denotes the observation overflow atom.
The initial law is the truncated product-Poisson reference law, including when
a nonzero potential changes the process generator.  An explicit alternative
initial distribution can be supplied to marginal/posterior methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
from numbers import Real
from typing import Sequence

import numpy as np
from scipy.linalg import expm


State = tuple[int, int]
Observation = State | None


def _real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite real number")
    return result


def _readonly(value: object) -> np.ndarray:
    array = np.array(value, dtype=np.float64, copy=True)
    array.setflags(write=False)
    return array


def enumerate_states(cap: int) -> tuple[State, ...]:
    """Enumerate occupancies, first by total count and then lexicographically."""
    if type(cap) is not int or not 0 <= cap <= 8:
        raise ValueError("cap must be an integer between zero and eight")
    return tuple((first, total - first) for total in range(cap + 1)
                 for first in range(total + 1))


@dataclass(frozen=True)
class FiniteBenchmarkSpec:
    """Declared toy settings; none are selected real-data hyperparameters."""

    theta: float = 1.2
    type_probabilities: tuple[float, float] = (0.65, 0.35)
    death_rate: float = 0.8
    state_cap: int = 3
    observation_cap: int = 1
    contamination: float = 0.1
    observation_reference_rate: float = 1.0
    horizon: float = 1.0

    def __post_init__(self) -> None:
        for name in ("theta", "death_rate", "observation_reference_rate", "horizon"):
            value = _real(getattr(self, name), name)
            if not 0 < value <= 10:
                raise ValueError(f"{name} must be in (0, 10]")
            object.__setattr__(self, name, value)
        if type(self.state_cap) is not int or not 1 <= self.state_cap <= 8:
            raise ValueError("state_cap must be an integer between one and eight")
        if (type(self.observation_cap) is not int
                or not 0 <= self.observation_cap <= self.state_cap):
            raise ValueError("observation_cap must be an integer in [0, state_cap]")
        if type(self.type_probabilities) is not tuple or len(self.type_probabilities) != 2:
            raise ValueError("type_probabilities must be a two-element tuple")
        probabilities = tuple(_real(p, "type probability") for p in self.type_probabilities)
        if min(probabilities) <= 0 or not math.isclose(sum(probabilities), 1., rel_tol=0., abs_tol=1e-14):
            raise ValueError("type probabilities must be positive and sum to one")
        object.__setattr__(self, "type_probabilities", probabilities)
        epsilon = _real(self.contamination, "contamination")
        if not 0 < epsilon < 1:
            raise ValueError("contamination must be strictly between zero and one")
        object.__setattr__(self, "contamination", epsilon)

    def to_dict(self) -> dict[str, object]:
        return {
            "theta": self.theta,
            "type_probabilities": list(self.type_probabilities),
            "death_rate": self.death_rate,
            "state_cap": self.state_cap,
            "observation_cap": self.observation_cap,
            "contamination": self.contamination,
            "observation_reference_rate": self.observation_reference_rate,
            "horizon": self.horizon,
            "retention_probability": 0.5,
        }


class FiniteConditionalBenchmark:
    """Finite matrix oracle, with row-vector distributions and row generators.

    ``potential`` is a bounded sequence aligned with ``states``.  Its rate tilt
    is Q_V(x,y) = Q_ref(x,y) exp(V(y)-V(x)); diagonals are minus row sums.
    This is a toy BASE process.  It is not the finite-time conditional Doob
    transform, which additionally depends on a terminal observation.
    """

    def __init__(self, spec: FiniteBenchmarkSpec | None = None,
                 potential: Sequence[float] | None = None) -> None:
        if spec is None:
            spec = FiniteBenchmarkSpec()
        if type(spec) is not FiniteBenchmarkSpec:
            raise ValueError("spec must be a FiniteBenchmarkSpec")
        self.spec = spec
        self.states = enumerate_states(spec.state_cap)
        self.observations: tuple[Observation, ...] = (*enumerate_states(spec.observation_cap), None)
        self.state_index = {state: index for index, state in enumerate(self.states)}
        if potential is None:
            values = np.zeros(len(self.states), dtype=np.float64)
        else:
            try:
                values = np.array([_real(v, "potential") for v in potential], dtype=np.float64)
            except TypeError as exc:
                raise ValueError("potential must be a finite sequence") from exc
            if values.shape != (len(self.states),) or np.max(np.abs(values), initial=0.) > 4:
                raise ValueError("potential must have one value per state and absolute values <= 4")
        self.potential = _readonly(values)

        weights = np.array([
            math.prod((spec.theta * rho) ** count / math.factorial(count)
                      for count, rho in zip(state, spec.type_probabilities))
            for state in self.states
        ])
        self.prior = _readonly(weights / weights.sum())
        tilted_weights = self.prior * np.exp(2. * self.potential)
        self.stationary_law = _readonly(tilted_weights / tilted_weights.sum())
        reference_generator = np.zeros((len(self.states), len(self.states)), dtype=np.float64)
        for i, state in enumerate(self.states):
            for event_type, probability in enumerate(spec.type_probabilities):
                if sum(state) < spec.state_cap:
                    next_state = list(state)
                    next_state[event_type] += 1
                    reference_generator[i, self.state_index[tuple(next_state)]] = (
                        spec.theta * spec.death_rate * probability
                    )
                if state[event_type]:
                    next_state = list(state)
                    next_state[event_type] -= 1
                    reference_generator[i, self.state_index[tuple(next_state)]] = (
                        spec.death_rate * state[event_type]
                    )
        generator = reference_generator * np.exp(self.potential[None, :] - self.potential[:, None])
        np.fill_diagonal(reference_generator, -reference_generator.sum(axis=1))
        np.fill_diagonal(generator, -generator.sum(axis=1))
        self.reference_generator = _readonly(reference_generator)
        self.generator = _readonly(generator)

    def _state(self, state: State) -> State:
        if (type(state) is not tuple or len(state) != 2
                or any(type(count) is not int or count < 0 for count in state)
                or sum(state) > self.spec.state_cap):
            raise ValueError("state must be an enumerated nonnegative occupancy tuple")
        return state

    def _observation(self, observation: Observation) -> Observation:
        if observation is None:
            return None
        self._state(observation)
        if sum(observation) > self.spec.observation_cap:
            raise ValueError("above-cap observations must be represented by None (overflow)")
        return observation

    def _time(self, value: float, name: str = "time") -> float:
        value = _real(value, name)
        if not 0 <= value <= self.spec.horizon:
            raise ValueError(f"{name} must lie in [0, horizon]")
        return value

    def _initial(self, initial: Sequence[float] | None) -> np.ndarray:
        if initial is None:
            return self.prior
        array = np.asarray(initial, dtype=np.float64)
        if (array.shape != self.prior.shape or not np.all(np.isfinite(array))
                or np.min(array) < 0 or not np.isclose(array.sum(), 1., rtol=0., atol=1e-12)):
            raise ValueError("initial distribution must be finite, nonnegative and sum to one")
        return array

    def _reference_observation_probability(self, observation: Observation) -> float:
        rate = self.spec.observation_reference_rate
        if observation is None:
            # Stable positive tail rather than subtracting nearly one.
            from scipy.special import gammainc
            return float(gammainc(self.spec.observation_cap + 1, rate))
        return math.exp(-rate) * math.prod(
            (rate * rho) ** count / math.factorial(count)
            for count, rho in zip(observation, self.spec.type_probabilities)
        )

    def observation_probability(self, state: State, observation: Observation) -> float:
        """Exact formula for half-thinning plus whole-observation replacement.

        Duplicate occurrences are thinned independently; the binomial factors
        retain their multiplicities.  Overflow maps the *whole* observation to
        a distinct atom, rather than retaining an arbitrary subset.
        """
        state, observation = self._state(state), self._observation(observation)
        if observation is None:
            total = sum(state)
            clean = sum(math.comb(total, count) for count in range(self.spec.observation_cap + 1, total + 1)) / (2 ** total)
        elif any(a > n for a, n in zip(observation, state)):
            clean = 0.
        else:
            clean = math.prod(math.comb(n, a) for a, n in zip(observation, state)) / (2 ** sum(state))
        epsilon = self.spec.contamination
        return (1. - epsilon) * clean + epsilon * self._reference_observation_probability(observation)

    def observation_likelihood(self, observation: Observation) -> np.ndarray:
        """Positive terminal observation likelihood g(x), one entry per state."""
        self._observation(observation)
        return _readonly([self.observation_probability(state, observation) for state in self.states])

    @lru_cache(maxsize=128, typed=True)
    def transition(self, duration: float, reference: bool = False) -> np.ndarray:
        """Numerical exp(duration Q); no sampling, clipping or renormalization."""
        duration = self._time(duration, "duration")
        if type(reference) is not bool:
            raise ValueError("reference must be bool")
        matrix = expm(duration * (self.reference_generator if reference else self.generator))
        if (not np.all(np.isfinite(matrix)) or np.min(matrix) < -1e-12
                or not np.allclose(matrix.sum(axis=1), 1., rtol=0., atol=1e-11)):
            raise ArithmeticError("matrix exponential did not produce a valid stochastic matrix")
        return _readonly(matrix)

    def marginal(self, time: float, initial: Sequence[float] | None = None) -> np.ndarray:
        return _readonly(self._initial(initial) @ self.transition(time))

    def backward_likelihood(self, time: float, observation: Observation) -> np.ndarray:
        """h_t(x)=E[g(X_T)|X_t=x] for this fixed CTMC, including its rate tilt."""
        time = self._time(time)
        return _readonly(self.transition(self.spec.horizon - time) @ self.observation_likelihood(observation))

    def evidence(self, observation: Observation, initial: Sequence[float] | None = None) -> float:
        return float(self._initial(initial) @ self.backward_likelihood(0., observation))

    def terminal_posterior(self, observation: Observation,
                           initial: Sequence[float] | None = None) -> np.ndarray:
        numerator = self.marginal(self.spec.horizon, initial) * self.observation_likelihood(observation)
        return _readonly(numerator / numerator.sum())

    def conditioned_initial(self, observation: Observation,
                            initial: Sequence[float] | None = None) -> np.ndarray:
        numerator = self._initial(initial) * self.backward_likelihood(0., observation)
        return _readonly(numerator / numerator.sum())

    def doob_transition(self, start: float, end: float, observation: Observation) -> np.ndarray:
        """Conditional grid transition on any ordered times of the same CTMC.

        Each row already sums to one by the semigroup identity.  It is not
        independently row-renormalized, so inconsistency is not concealed.
        """
        start, end = self._time(start, "start"), self._time(end, "end")
        if end < start:
            raise ValueError("end must not precede start")
        h_start = self.backward_likelihood(start, observation)
        h_end = self.backward_likelihood(end, observation)
        result = self.transition(end - start) * h_end[None, :] / h_start[:, None]
        if not np.allclose(result.sum(axis=1), 1., rtol=0., atol=2e-11):
            raise ArithmeticError("Doob transition violates backward semigroup consistency")
        return _readonly(result)

    def conditioned_path_probability(self, states: Sequence[State], times: Sequence[float],
                                      observation: Observation,
                                      initial: Sequence[float] | None = None) -> float:
        """Probability of a complete discrete-time skeleton given an observation."""
        if len(states) != len(times) or len(times) < 2:
            raise ValueError("states and times must have equal length at least two")
        checked_times = tuple(self._time(time) for time in times)
        if checked_times[0] != 0. or checked_times[-1] != self.spec.horizon:
            raise ValueError("path times must begin at zero and end at the horizon")
        if any(right <= left for left, right in zip(checked_times, checked_times[1:])):
            raise ValueError("path times must increase strictly")
        indices = [self.state_index[self._state(state)] for state in states]
        result = self.conditioned_initial(observation, initial)[indices[0]]
        for i, (start, end) in enumerate(zip(checked_times, checked_times[1:])):
            result *= self.doob_transition(start, end, observation)[indices[i], indices[i + 1]]
        return float(result)

    def capped_reference_likelihood(self, duration: float, observation: Observation) -> np.ndarray:
        """Capped reference guide, with no BASE potential rate tilt."""
        return _readonly(self.transition(duration, reference=True) @ self.observation_likelihood(observation))

    def uncapped_reference_likelihood(self, state: State, duration: float,
                                      observation: Observation) -> float:
        """Closed-form uncapped guide, independent of matrix exponentials.

        Terminal retained type-i count is Bin(n_i, exp(-delta*t)/2) plus
        Pois(theta*rho_i*(1-exp(-delta*t))/2).  This convolution automatically
        includes duplicate-assignment multiplicities.  This law does NOT
        suppress births at ``state_cap`` and thus is not the capped guide.
        """
        state, observation = self._state(state), self._observation(observation)
        duration = self._time(duration, "duration")
        survival = math.exp(-self.spec.death_rate * duration)
        retention = 0.5 * survival
        immigrant_means = [0.5 * self.spec.theta * rho * (-math.expm1(-self.spec.death_rate * duration))
                           for rho in self.spec.type_probabilities]

        def count_probability(counts: State) -> float:
            probability = 1.
            for count, n, mean in zip(counts, state, immigrant_means):
                probability *= sum(
                    math.comb(n, retained) * retention ** retained * (1. - retention) ** (n - retained)
                    * math.exp(-mean) * mean ** (count - retained) / math.factorial(count - retained)
                    for retained in range(min(n, count) + 1)
                )
            return probability

        if observation is None:
            clean = 1. - math.fsum(count_probability(counts) for counts in enumerate_states(self.spec.observation_cap))
            if clean < -1e-14:
                raise ArithmeticError("negative uncapped overflow probability")
        else:
            clean = count_probability(observation)
        return (1. - self.spec.contamination) * clean + self.spec.contamination * self._reference_observation_probability(observation)

    def compare_reference_guides(self, duration: float, observation: Observation) -> dict[str, object]:
        capped = self.capped_reference_likelihood(duration, observation)
        uncapped = _readonly([self.uncapped_reference_likelihood(state, duration, observation) for state in self.states])
        return {
            "capped": capped.tolist(),
            "uncapped": uncapped.tolist(),
            "maximum_absolute_difference": float(np.max(np.abs(capped - uncapped))),
            "maximum_relative_difference": float(np.max(np.abs(capped - uncapped) / capped)),
            "uncapped_formula_is_capped_exact": False,
        }
