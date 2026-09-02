"""Reference categorical D3PM forward kernels.

The implementation uses row vectors: ``Q[n, a, b]`` is the probability of
moving from state ``a`` to state ``b`` at numerical diffusion step ``n + 1``.
``diffusion_progress`` is a normalized corruption coordinate and is unrelated
to physical event timestamps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]
ImpossiblePolicy = Literal["raise", "zeros"]


class ImpossibleConditioningEvent(ValueError):
    """Raised when the requested categorical posterior conditions on zero mass."""


def _validate_diffusion_progress(
    progress: Optional[FloatArray], num_diffusion_steps: int
) -> FloatArray:
    if progress is None:
        values = np.linspace(0.0, 1.0, num_diffusion_steps + 1, dtype=np.float64)
    else:
        values = np.array(progress, dtype=np.float64, copy=True)
        if values.shape != (num_diffusion_steps + 1,):
            raise ValueError(
                "diffusion_progress must have one entry for step zero and each "
                "corruption step"
            )
        if not np.all(np.isfinite(values)):
            raise ValueError("diffusion_progress must be finite")
        if values[0] != 0.0 or values[-1] != 1.0:
            raise ValueError("diffusion_progress must start at zero and end at one")
        if np.any(np.diff(values) <= 0.0):
            raise ValueError("diffusion_progress must be strictly increasing")
    values.setflags(write=False)
    return values


def _validate_betas(betas: object) -> FloatArray:
    values = np.asarray(betas, dtype=np.float64)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("betas must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(values)) or np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError("categorical betas must lie in [0, 1]")
    return values


def _validate_state_array(states: object, num_states: int, name: str) -> IntArray:
    values = np.asarray(states)
    if values.dtype == np.bool_ or not np.issubdtype(values.dtype, np.integer):
        raise TypeError("%s must contain integer state indices" % name)
    values = values.astype(np.int64, copy=False)
    if np.any(values < 0) or np.any(values >= num_states):
        raise ValueError("%s contains a state outside [0, %d)" % (name, num_states))
    return values


def _broadcast_mask(mask: Optional[object], shape: tuple) -> NDArray[np.bool_]:
    if mask is None:
        return np.ones(shape, dtype=bool)
    values = np.asarray(mask)
    if values.dtype != np.bool_:
        raise TypeError("valid_mask must contain booleans")
    try:
        return np.broadcast_to(values, shape)
    except ValueError as error:
        raise ValueError("valid_mask cannot be broadcast to categorical states") from error


def cumulative_transitions(step_transitions: object, atol: float = 1e-12) -> FloatArray:
    """Return ``[I, Q_1, Q_1 Q_2, ...]`` for row-stochastic transitions."""

    transitions = np.asarray(step_transitions, dtype=np.float64)
    if transitions.ndim != 3 or transitions.shape[0] == 0:
        raise ValueError("step_transitions must have shape [steps, states, states]")
    if transitions.shape[1] != transitions.shape[2]:
        raise ValueError("categorical transitions must be square")
    if not np.all(np.isfinite(transitions)):
        raise ValueError("categorical transitions must be finite")
    # A negative entry is not a probability, even when its magnitude is below
    # the row-sum tolerance.  Silently clipping it would make ``transitions``
    # disagree with the cumulative kernels used by the posterior.
    if np.any(transitions < 0.0):
        raise ValueError("categorical transitions cannot contain negative probabilities")
    if not np.allclose(transitions.sum(axis=-1), 1.0, atol=atol, rtol=0.0):
        raise ValueError("every categorical transition row must sum to one")

    num_steps, num_states, _ = transitions.shape
    cumulative = np.empty((num_steps + 1, num_states, num_states), dtype=np.float64)
    cumulative[0] = np.eye(num_states, dtype=np.float64)
    for step in range(num_steps):
        cumulative[step + 1] = cumulative[step] @ transitions[step]
    if not np.allclose(cumulative.sum(axis=-1), 1.0, atol=10.0 * atol, rtol=0.0):
        raise RuntimeError("cumulative categorical transitions lost normalization")
    cumulative.setflags(write=False)
    return cumulative


@dataclass(frozen=True)
class CategoricalSchedule:
    """A validated finite-step categorical corruption schedule."""

    transitions: FloatArray
    diffusion_progress: Optional[FloatArray] = None
    atol: float = 1e-12
    cumulative: FloatArray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not np.isfinite(self.atol) or self.atol <= 0.0:
            raise ValueError("atol must be finite and positive")
        transitions = np.array(self.transitions, dtype=np.float64, copy=True)
        cumulative = cumulative_transitions(transitions, atol=self.atol)
        transitions.setflags(write=False)
        progress = _validate_diffusion_progress(
            self.diffusion_progress, transitions.shape[0]
        )
        object.__setattr__(self, "transitions", transitions)
        object.__setattr__(self, "cumulative", cumulative)
        object.__setattr__(self, "diffusion_progress", progress)

    @property
    def num_diffusion_steps(self) -> int:
        return self.transitions.shape[0]

    @property
    def num_states(self) -> int:
        return self.transitions.shape[1]

    def _validate_step(self, diffusion_step: int, allow_zero: bool = True) -> int:
        if isinstance(diffusion_step, bool) or not isinstance(diffusion_step, (int, np.integer)):
            raise TypeError("diffusion_step must be an integer")
        minimum = 0 if allow_zero else 1
        if diffusion_step < minimum or diffusion_step > self.num_diffusion_steps:
            raise ValueError(
                "diffusion_step must lie in [%d, %d]"
                % (minimum, self.num_diffusion_steps)
            )
        return int(diffusion_step)

    def marginal_probabilities(
        self,
        clean_states: object,
        diffusion_step: int,
        valid_mask: Optional[object] = None,
    ) -> FloatArray:
        """Compute ``q(x_n | x_0)`` at every requested categorical site."""

        step = self._validate_step(diffusion_step)
        clean = _validate_state_array(clean_states, self.num_states, "clean_states")
        probabilities = np.array(self.cumulative[step][clean], copy=True)
        mask = _broadcast_mask(valid_mask, clean.shape)
        if not np.all(mask):
            deterministic = np.eye(self.num_states, dtype=np.float64)[clean]
            probabilities = np.where(mask[..., None], probabilities, deterministic)
        return probabilities

    def q_sample(
        self,
        clean_states: object,
        diffusion_step: int,
        rng: np.random.Generator,
        valid_mask: Optional[object] = None,
    ) -> IntArray:
        """Draw categorical corruptions; invalid/padded sites remain unchanged."""

        if not isinstance(rng, np.random.Generator):
            raise TypeError("rng must be a numpy.random.Generator")
        clean = _validate_state_array(clean_states, self.num_states, "clean_states")
        probabilities = self.marginal_probabilities(clean, diffusion_step, valid_mask)
        flat = probabilities.reshape((-1, self.num_states))
        cumulative = np.cumsum(flat, axis=1)
        cumulative[:, -1] = 1.0
        uniforms = rng.random(flat.shape[0])
        # ``>=`` is important at a zero-width leading bin when a generator
        # returns exactly zero: that state must remain impossible.
        samples = np.sum(uniforms[:, None] >= cumulative, axis=1, dtype=np.int64)
        return samples.reshape(clean.shape)

    def exact_posterior(
        self,
        clean_states: object,
        noisy_states: object,
        diffusion_step: int,
        impossible: ImpossiblePolicy = "raise",
        valid_mask: Optional[object] = None,
    ) -> FloatArray:
        """Compute ``q(x_{n-1} | x_n, x_0)`` exactly by Bayes' rule.

        If a valid site conditions on an event with zero forward probability,
        ``impossible='raise'`` reports it explicitly. ``'zeros'`` returns an
        all-zero row for that site, which is intentionally not a probability
        distribution and therefore cannot be mistaken for a valid posterior.
        Invalid/padded sites are deterministic at their clean state.
        """

        step = self._validate_step(diffusion_step, allow_zero=False)
        if impossible not in ("raise", "zeros"):
            raise ValueError("impossible must be 'raise' or 'zeros'")
        clean = _validate_state_array(clean_states, self.num_states, "clean_states")
        noisy = _validate_state_array(noisy_states, self.num_states, "noisy_states")
        clean, noisy = np.broadcast_arrays(clean, noisy)
        mask = _broadcast_mask(valid_mask, clean.shape)
        result = np.zeros(clean.shape + (self.num_states,), dtype=np.float64)

        flat_clean = clean.reshape(-1)
        flat_noisy = noisy.reshape(-1)
        flat_mask = mask.reshape(-1)
        flat_result = result.reshape((-1, self.num_states))
        impossible_sites = []
        for site, (clean_state, noisy_state, is_valid) in enumerate(
            zip(flat_clean, flat_noisy, flat_mask)
        ):
            if not is_valid:
                flat_result[site, clean_state] = 1.0
                continue
            denominator = self.cumulative[step, clean_state, noisy_state]
            # Impossibility is a support statement, not a tolerance decision.
            # A rare but positive event must still receive its exact posterior.
            if denominator == 0.0:
                impossible_sites.append(site)
                continue
            weights = (
                self.cumulative[step - 1, clean_state, :]
                * self.transitions[step - 1, :, noisy_state]
            )
            flat_result[site] = weights / denominator
            row_sum = flat_result[site].sum()
            if not np.isclose(row_sum, 1.0, atol=50.0 * self.atol, rtol=0.0):
                raise RuntimeError("categorical posterior lost normalization")
            flat_result[site] /= row_sum

        if impossible_sites and impossible == "raise":
            preview = impossible_sites[:5]
            raise ImpossibleConditioningEvent(
                "zero-probability conditioning event at flattened site(s) %s "
                "for diffusion step %d" % (preview, step)
            )
        return result


def absorbing_d3pm_schedule(
    betas: object,
    num_categories: int,
    mask_state: Optional[int] = None,
    diffusion_progress: Optional[FloatArray] = None,
) -> CategoricalSchedule:
    """Construct an absorbing schedule with one diffusion-only mask state.

    ``num_categories`` counts clean states; the returned process has one extra
    state. By default that mask state is the final index.
    """

    beta_values = _validate_betas(betas)
    if isinstance(num_categories, bool) or not isinstance(num_categories, (int, np.integer)):
        raise TypeError("num_categories must be an integer")
    if num_categories <= 0:
        raise ValueError("num_categories must be positive")
    num_states = int(num_categories) + 1
    if mask_state is None:
        mask_state = num_states - 1
    if isinstance(mask_state, bool) or not isinstance(mask_state, (int, np.integer)):
        raise TypeError("mask_state must be an integer")
    if mask_state < 0 or mask_state >= num_states:
        raise ValueError("mask_state is outside the augmented state space")

    transitions = np.empty((beta_values.size, num_states, num_states), dtype=np.float64)
    identity = np.eye(num_states, dtype=np.float64)
    for step, beta in enumerate(beta_values):
        transition = (1.0 - beta) * identity
        transition[:, mask_state] += beta
        transition[mask_state, :] = 0.0
        transition[mask_state, mask_state] = 1.0
        transitions[step] = transition
    return CategoricalSchedule(transitions, diffusion_progress)


def uniform_d3pm_schedule(
    betas: object,
    num_states: int,
    diffusion_progress: Optional[FloatArray] = None,
) -> CategoricalSchedule:
    """Construct ``(1-beta) I + beta Uniform(states)`` transitions."""

    beta_values = _validate_betas(betas)
    if isinstance(num_states, bool) or not isinstance(num_states, (int, np.integer)):
        raise TypeError("num_states must be an integer")
    if num_states <= 1:
        raise ValueError("num_states must exceed one")
    identity = np.eye(int(num_states), dtype=np.float64)
    base = np.full((int(num_states), int(num_states)), 1.0 / num_states)
    transitions = np.asarray(
        [(1.0 - beta) * identity + beta * base for beta in beta_values]
    )
    return CategoricalSchedule(transitions, diffusion_progress)


def base_distribution_d3pm_schedule(
    betas: object,
    base_probabilities: object,
    diffusion_progress: Optional[FloatArray] = None,
) -> CategoricalSchedule:
    """Construct replacement transitions toward a documented base measure."""

    beta_values = _validate_betas(betas)
    base = np.asarray(base_probabilities, dtype=np.float64)
    if base.ndim != 1 or base.size <= 1:
        raise ValueError("base_probabilities must be a one-dimensional state law")
    if not np.all(np.isfinite(base)) or np.any(base < 0.0):
        raise ValueError("base_probabilities must be finite and non-negative")
    if not np.isclose(base.sum(), 1.0, atol=1e-12, rtol=0.0):
        raise ValueError("base_probabilities must sum to one")
    base = base / base.sum()
    identity = np.eye(base.size, dtype=np.float64)
    replacement = np.broadcast_to(base, (base.size, base.size))
    transitions = np.asarray(
        [(1.0 - beta) * identity + beta * replacement for beta in beta_values]
    )
    return CategoricalSchedule(transitions, diffusion_progress)
