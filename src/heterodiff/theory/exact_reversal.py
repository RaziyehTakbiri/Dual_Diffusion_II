"""Exact finite-state time reversal under the row-generator convention."""

from __future__ import annotations

from typing import Tuple

import numpy as np

from .finite_state import validate_generator, validate_probability_vector


class ZeroMassStateError(ValueError):
    """Raised when reversal is requested at an unreachable current state."""

    def __init__(self, state_indices: Tuple[int, ...]) -> None:
        self.state_indices = state_indices
        super().__init__(
            "time reversal is undefined on zero-mass states %r; "
            "use zero_mass='zero' (generator) or 'identity' (transition) "
            "to request an explicit arbitrary extension" % (state_indices,)
        )


def _zero_indices(marginal: np.ndarray, mass_tolerance: float) -> Tuple[int, ...]:
    if not np.isfinite(mass_tolerance) or mass_tolerance < 0.0:
        raise ValueError("mass_tolerance must be finite and nonnegative")
    near_zero_positive = np.flatnonzero(
        (marginal > 0.0) & (marginal <= mass_tolerance)
    )
    if near_zero_positive.size:
        raise ValueError(
            "positive-mass states %r lie at or below mass_tolerance; "
            "they cannot be replaced by arbitrary zero-mass extensions"
            % tuple(int(index) for index in near_zero_positive)
        )
    return tuple(int(index) for index in np.flatnonzero(marginal == 0.0))


def reverse_generator(
    forward_generator: np.ndarray,
    marginal: np.ndarray,
    *,
    zero_mass: str = "raise",
    mass_tolerance: float = 0.0,
) -> np.ndarray:
    """Return the instantaneous generator of the reversed process.

    For positive current-state mass, the off-diagonal rate is

    ``Q_reverse[i, j] = Q_forward[j, i] * p[j] / p[i]``.

    The formula is undefined when ``p[i] == 0``.  The default policy raises
    :class:`ZeroMassStateError`.  ``zero_mass='zero'`` instead makes every such
    state absorbing (a zero generator row).  This is an explicit arbitrary
    extension and cannot affect trajectories initialized on the support of
    ``p`` at that instant. ``mass_tolerance`` is only a numerical guard: a
    positive mass at or below it raises rather than being treated as zero.
    """

    generator = validate_generator(forward_generator)
    probabilities = validate_probability_vector(marginal, generator.shape[0])
    zero_indices = _zero_indices(probabilities, mass_tolerance)

    if zero_mass not in ("raise", "zero"):
        raise ValueError("zero_mass must be either 'raise' or 'zero'")
    if zero_indices and zero_mass == "raise":
        raise ZeroMassStateError(zero_indices)

    reverse = np.zeros_like(generator)
    zero_set = set(zero_indices)
    for current in range(generator.shape[0]):
        if current in zero_set:
            continue
        for destination in range(generator.shape[0]):
            if current == destination:
                continue
            reverse[current, destination] = (
                generator[destination, current]
                * probabilities[destination]
                / probabilities[current]
            )
        reverse[current, current] = -reverse[current].sum()
    return validate_generator(reverse, atol=1e-11)


def _validate_transition_matrix(
    forward_transition: np.ndarray,
    atol: float = 1e-12,
) -> np.ndarray:
    transition = np.asarray(forward_transition, dtype=float)
    if transition.ndim != 2 or transition.shape[0] != transition.shape[1]:
        raise ValueError("forward_transition must be a square matrix")
    if not np.all(np.isfinite(transition)):
        raise ValueError("forward_transition entries must be finite")
    if np.any(transition < 0.0):
        raise ValueError("forward_transition entries must be nonnegative")
    if not np.allclose(
        transition.sum(axis=1), 1.0, atol=atol, rtol=0.0
    ):
        raise ValueError("forward_transition rows must sum to one")
    return transition.copy()


def reverse_transition_matrix(
    forward_transition: np.ndarray,
    initial_marginal: np.ndarray,
    *,
    zero_mass: str = "raise",
    mass_tolerance: float = 0.0,
) -> np.ndarray:
    """Return the exact finite-interval backward conditional kernel.

    If ``P[i, j]`` is the forward transition and ``p0`` is the initial law,
    the returned kernel satisfies

    ``P_reverse[j, i] = p0[i] * P[i, j] / (p0 @ P)[j]``.

    A zero final-mass row is undefined.  The default policy raises;
    ``zero_mass='identity'`` installs an identity row as a declared arbitrary
    stochastic extension.  Such rows carry no probability under the final law.
    ``mass_tolerance`` never reclassifies a positive-mass row as zero.
    """

    transition = _validate_transition_matrix(forward_transition)
    initial = validate_probability_vector(initial_marginal, transition.shape[0])
    final = initial @ transition
    final = validate_probability_vector(final, transition.shape[0], atol=1e-11)
    zero_indices = _zero_indices(final, mass_tolerance)

    if zero_mass not in ("raise", "identity"):
        raise ValueError("zero_mass must be either 'raise' or 'identity'")
    if zero_indices and zero_mass == "raise":
        raise ZeroMassStateError(zero_indices)

    reverse = np.zeros_like(transition)
    zero_set = set(zero_indices)
    for current in range(transition.shape[0]):
        if current in zero_set:
            reverse[current, current] = 1.0
            continue
        reverse[current, :] = (
            initial * transition[:, current] / final[current]
        )

    if not np.allclose(reverse.sum(axis=1), 1.0, atol=1e-11, rtol=0.0):
        raise ArithmeticError("reverse transition rows do not sum to one")
    return reverse
