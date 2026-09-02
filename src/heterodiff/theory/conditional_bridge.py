"""Exact endpoint conditioning for a finite-state transition kernel.

This module is a finite counting-measure oracle.  It conditions a forward
finite-interval transition ``P`` on an observation made at the terminal state.
The observation is represented by a nonnegative vector
``g[j] = g(observation | terminal_state=j)``.  For a discrete observation this
may be an indicator or probability mass; for a continuous observation it is a
likelihood density evaluated at the observed value.  The vector need not sum to
one and its entries need not be bounded by one.

Nothing here establishes a bridge on continuous marked-configuration space.
It only provides exact finite-state identities for testing such a construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from .finite_state import validate_probability_vector


class ZeroEvidenceError(ValueError):
    """Raised when an observation has zero probability/density evidence."""


class UnreachableObservationStateError(ValueError):
    """Raised when the requested observation is unreachable from source rows."""

    def __init__(self, state_indices: Tuple[int, ...]) -> None:
        self.state_indices = state_indices
        super().__init__(
            "the observation is unreachable from source states %r; "
            "use unreachable_policy='identity' to request an arbitrary "
            "stochastic extension on those unreachable conditional states"
            % (state_indices,)
        )


@dataclass(frozen=True)
class ConditionalBridge:
    """Exact finite-state quantities conditioned on a terminal observation.

    ``doob_transition`` is exact on every row with positive backward
    information. When the requested unreachable-state policy is ``identity``,
    identity rows are an arbitrary extension only; ``conditional_initial`` has
    zero mass on those rows, so the extension cannot affect the conditional
    joint or either endpoint marginal.
    """

    evidence: float
    observation_likelihood: np.ndarray
    backward_information: np.ndarray
    conditional_initial: np.ndarray
    conditional_terminal: np.ndarray
    doob_transition: np.ndarray


def _validate_transition_matrix(
    transition: np.ndarray,
    atol: float = 1e-12,
) -> np.ndarray:
    raw = np.asarray(transition)
    if raw.dtype.kind == "b":
        raise TypeError("transition must not have boolean dtype")
    if raw.dtype.kind not in "iuf":
        raise TypeError("transition must have a real numeric dtype")
    matrix = raw.astype(float, copy=False)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("transition must be a square matrix")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("transition entries must be finite")
    if np.any(matrix < 0.0):
        raise ValueError("transition entries must be nonnegative")
    if not np.allclose(matrix.sum(axis=1), 1.0, atol=atol, rtol=0.0):
        raise ValueError("transition rows must sum to one")

    return matrix.copy()


def validate_observation_likelihood(
    likelihood: np.ndarray,
    n_states: int,
) -> np.ndarray:
    """Validate a nonnegative likelihood/density vector without normalizing it."""

    raw = np.asarray(likelihood)
    if raw.dtype.kind == "b":
        raise TypeError("observation likelihood must not have boolean dtype")
    if raw.dtype.kind not in "iuf":
        raise TypeError("observation likelihood must have a real numeric dtype")
    vector = raw.astype(float, copy=False)
    if vector.ndim != 1 or vector.shape != (n_states,):
        raise ValueError(
            "observation likelihood must have shape (%d,), got %r"
            % (n_states, vector.shape)
        )
    if not np.all(np.isfinite(vector)):
        raise ValueError("observation likelihood values must be finite")
    if np.any(vector < 0.0):
        raise ValueError("observation likelihood values must be nonnegative")
    return vector.copy()


def backward_information(
    forward_transition: np.ndarray,
    observation_likelihood: np.ndarray,
) -> np.ndarray:
    """Compute ``h[i] = sum_j P[i,j] g[j]`` over the finite interval."""

    transition = _validate_transition_matrix(forward_transition)
    likelihood = validate_observation_likelihood(
        observation_likelihood, transition.shape[0]
    )
    information = transition @ likelihood
    if not np.all(np.isfinite(information)):
        raise ArithmeticError("backward information is not finite")
    if np.any(information < 0.0):
        raise ArithmeticError("backward information became negative")
    return information


def doob_transform_transition(
    forward_transition: np.ndarray,
    observation_likelihood: np.ndarray,
    *,
    unreachable_policy: str = "identity",
) -> np.ndarray:
    """Return the exact finite-interval Doob-transformed transition.

    For ``h[i] > 0``, the result is ``P[i,j] g[j] / h[i]``.  The transform is
    undefined when ``h[i] == 0``.  By default, such rows are replaced by
    identity rows as an explicit arbitrary stochastic extension.  Pass
    ``unreachable_policy='raise'`` for strict rejection instead.
    """

    transition = _validate_transition_matrix(forward_transition)
    likelihood = validate_observation_likelihood(
        observation_likelihood, transition.shape[0]
    )
    information = transition @ likelihood
    zero_indices = tuple(
        int(index) for index in np.flatnonzero(information == 0.0)
    )

    if unreachable_policy not in ("identity", "raise"):
        raise ValueError("unreachable_policy must be 'identity' or 'raise'")
    if zero_indices and unreachable_policy == "raise":
        raise UnreachableObservationStateError(zero_indices)

    transformed = np.zeros_like(transition)
    zero_set = set(zero_indices)
    for source in range(transition.shape[0]):
        if source in zero_set:
            transformed[source, source] = 1.0
            continue
        transformed[source, :] = (
            transition[source, :] * likelihood / information[source]
        )

    if np.any(transformed < 0.0) or not np.allclose(
        transformed.sum(axis=1), 1.0, atol=1e-11, rtol=0.0
    ):
        raise ArithmeticError("Doob-transformed transition is not stochastic")
    return transformed


def conditional_bridge(
    initial_marginal: np.ndarray,
    forward_transition: np.ndarray,
    observation_likelihood: np.ndarray,
    *,
    unreachable_policy: str = "identity",
) -> ConditionalBridge:
    """Condition both endpoints and the finite-interval transition exactly.

    The evidence is

    ``Z = sum_i p0[i] h[i] = sum_j (p0 P)[j] g[j]``.

    Zero evidence is rejected even if an arbitrary Doob extension could be
    written, because no conditional probability law exists in that case.
    """

    transition = _validate_transition_matrix(forward_transition)
    initial = validate_probability_vector(initial_marginal, transition.shape[0])
    likelihood = validate_observation_likelihood(
        observation_likelihood, transition.shape[0]
    )
    information = transition @ likelihood
    terminal = initial @ transition
    evidence_from_initial = float(initial @ information)
    evidence_from_terminal = float(terminal @ likelihood)

    if not np.isfinite(evidence_from_initial):
        raise ArithmeticError("observation evidence is not finite")
    if not np.isclose(
        evidence_from_initial,
        evidence_from_terminal,
        atol=1e-12,
        rtol=1e-12,
    ):
        raise ArithmeticError("equivalent evidence calculations disagree")
    if evidence_from_initial <= 0.0:
        raise ZeroEvidenceError(
            "terminal observation has zero evidence under the forward law"
        )

    conditional_initial = initial * information / evidence_from_initial
    conditional_terminal = terminal * likelihood / evidence_from_initial
    conditional_initial = validate_probability_vector(
        conditional_initial, transition.shape[0], atol=1e-11
    )
    conditional_terminal = validate_probability_vector(
        conditional_terminal, transition.shape[0], atol=1e-11
    )
    transformed = doob_transform_transition(
        transition,
        likelihood,
        unreachable_policy=unreachable_policy,
    )

    recovered_terminal = conditional_initial @ transformed
    if not np.allclose(
        recovered_terminal,
        conditional_terminal,
        atol=1e-11,
        rtol=1e-11,
    ):
        raise ArithmeticError(
            "conditional initial law and Doob kernel do not recover the "
            "conditional terminal law"
        )

    return ConditionalBridge(
        evidence=evidence_from_initial,
        observation_likelihood=likelihood,
        backward_information=information,
        conditional_initial=conditional_initial,
        conditional_terminal=conditional_terminal,
        doob_transition=transformed,
    )
