"""Family-resolved numerical path KL for a finite tilted CTMC.

This module is a narrow sibling of :mod:`finite_bridge_path_control`.  It
keeps that module's target-first orientation and numerical engine, but
partitions each *aggregate state-to-state* jump-rate divergence into a fixed
edge family.  It does not infer occurrence labels, continuous-coordinate
energy, or an interval enclosure.

For reference potential ``h`` and candidate potential ``h_hat``, the returned
orientation is ``KL(P^h || P^h_hat)``.  With
``e = log(h_hat / h)`` and an aggregate reference edge rate ``q^h_ij``, each
edge contributes

``q^h_ij * (exp(e_j-e_i) - 1 - (e_j-e_i))``.

The expectation is therefore under the reference/target occupancy.  The
initializer KL is retained separately.  Adaptive ODE and quadrature error
estimates are diagnostics only and are not rigorous enclosures.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Optional, Tuple

import numpy as np

from .finite_bridge_path_control import (
    PositivePotential,
    TiltedInitialLaw,
    TimeIndexedOccupancy,
    _EvaluationBudget,
    _MAX_POTENTIAL_EVALUATIONS,
    _TiltEngine,
    _categorical_kl,
    _dense_marginal,
    _evaluation_grid,
    _immutable_array,
    _initial_from_values,
    _nonnegative_integer,
    _numeric_array,
    _numerical_controls,
    _poisson_rate_divergence,
    _potential_values,
    _quadrature,
    _real_number,
    _solve_marginal,
    _validated_marginal,
)
from .finite_state import validate_probability_vector


FINITE_BRIDGE_JUMP_FAMILY_ORDER = ("birth", "death", "replacement")
_UNASSIGNED_EDGE = -1


def _family_index_array(
    value: object, *, engine: _TiltEngine
) -> Tuple[np.ndarray, Tuple[int, int, int]]:
    try:
        raw = np.asarray(value)
        objects = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("edge_family_indices must be a rectangular array") from error
    if any(isinstance(item, (bool, np.bool_)) for item in objects.flat):
        raise TypeError("edge_family_indices must not contain booleans")
    if raw.dtype.kind not in "iu":
        raise TypeError("edge_family_indices must have integer dtype")
    expected = (engine.state_count, engine.state_count)
    if raw.shape != expected:
        raise ValueError("edge_family_indices must have shape %r" % (expected,))
    families = np.asarray(raw, dtype=np.int64).copy()
    off_diagonal = np.asarray(engine.generator, dtype=np.float64).copy()
    np.fill_diagonal(off_diagonal, 0.0)
    active = off_diagonal > 0.0
    inactive = ~active
    if np.any(families[inactive] != _UNASSIGNED_EDGE):
        raise ValueError("diagonal and structural-zero edges must use family index -1")
    if np.any(families[active] < 0) or np.any(families[active] >= 3):
        raise ValueError(
            "every positive aggregate edge must have one frozen family index"
        )
    counts = tuple(int(np.count_nonzero(families == index)) for index in range(3))
    if any(count <= 0 for count in counts):
        raise ValueError("all three frozen jump families must be active")
    return _immutable_array(families, dtype=np.dtype(np.int64)), counts  # type: ignore[return-value]


def _state_family_rate_divergence(
    reference_generator: np.ndarray,
    candidate_generator: np.ndarray,
    family_indices: np.ndarray,
) -> np.ndarray:
    state_count = int(reference_generator.shape[0])
    result = np.zeros((state_count, 3), dtype=np.float64)
    for source in range(state_count):
        terms = [[], [], []]
        for destination in range(state_count):
            family = int(family_indices[source, destination])
            if family == _UNASSIGNED_EDGE:
                continue
            reference_rate = float(reference_generator[source, destination])
            candidate_rate = float(candidate_generator[source, destination])
            divergence = _poisson_rate_divergence(reference_rate, candidate_rate)
            if not math.isfinite(divergence):
                raise ArithmeticError("family jump-rate divergence is not finite")
            terms[family].append(divergence)
        for family in range(3):
            result[source, family] = math.fsum(terms[family])
    return result


@dataclass(frozen=True, eq=False)
class FiniteBridgeFamilyPathKL:
    """Target-first numerical KL split over three aggregate jump families."""

    orientation: str
    family_names: Tuple[str, str, str]
    aggregate_state_transition_rates_used: bool
    supplied_reference_marginal_used: bool
    initial: float
    birth_dynamic: float
    death_dynamic: float
    replacement_dynamic: float
    dynamic: float
    total: float
    reference_initial: TiltedInitialLaw
    candidate_initial: TiltedInitialLaw
    occupancy: TimeIndexedOccupancy
    state_family_rate_divergence: np.ndarray
    active_edge_counts: Tuple[int, int, int]
    quadrature_error_estimate: float
    potential_evaluations: int
    interval_enclosure_provided: bool
    ode_discretization_error_enclosed: bool

    def __post_init__(self) -> None:
        if self.orientation != "KL(P_REFERENCE_H || P_CANDIDATE_H_HAT)":
            raise ValueError("orientation must remain target/reference first")
        if self.family_names != FINITE_BRIDGE_JUMP_FAMILY_ORDER:
            raise ValueError("family_names must use the frozen family order")
        if self.aggregate_state_transition_rates_used is not True:
            raise ValueError("family accounting must use aggregate state rates")
        if type(self.supplied_reference_marginal_used) is not bool:
            raise TypeError("supplied_reference_marginal_used must be boolean")
        checked = {}
        for name in (
            "initial",
            "birth_dynamic",
            "death_dynamic",
            "replacement_dynamic",
            "dynamic",
            "total",
            "quadrature_error_estimate",
        ):
            checked[name] = _real_number(getattr(self, name), name=name, minimum=0.0)
        expected_dynamic = math.fsum(
            (
                checked["birth_dynamic"],
                checked["death_dynamic"],
                checked["replacement_dynamic"],
            )
        )
        if not math.isclose(
            checked["dynamic"],
            expected_dynamic,
            rel_tol=2.0e-12,
            abs_tol=2.0e-14,
        ):
            raise ValueError("dynamic KL does not equal the family sum")
        if not math.isclose(
            checked["total"],
            checked["initial"] + checked["dynamic"],
            rel_tol=2.0e-12,
            abs_tol=2.0e-14,
        ):
            raise ValueError("total KL does not equal initializer plus jumps")
        if (
            type(self.reference_initial) is not TiltedInitialLaw
            or type(self.candidate_initial) is not TiltedInitialLaw
        ):
            raise TypeError("initial records must be exact TiltedInitialLaw records")
        if type(self.occupancy) is not TimeIndexedOccupancy:
            raise TypeError("occupancy must be an exact TimeIndexedOccupancy record")
        rates = _numeric_array(
            self.state_family_rate_divergence,
            name="state_family_rate_divergence",
            ndim=3,
        )
        expected_shape = self.occupancy.marginals.shape + (3,)
        if rates.shape != expected_shape or np.any(rates < 0.0):
            raise ValueError(
                "state_family_rate_divergence must be nonnegative and match "
                "time/state/family dimensions"
            )
        if (
            type(self.active_edge_counts) is not tuple
            or len(self.active_edge_counts) != 3
        ):
            raise TypeError("active_edge_counts must be an exact length-three tuple")
        counts = tuple(
            _nonnegative_integer(
                value,
                name="active_edge_counts",
                maximum=1_000_000,
            )
            for value in self.active_edge_counts
        )
        if any(value == 0 for value in counts):
            raise ValueError("every frozen jump family must contain an active edge")
        evaluations = _nonnegative_integer(
            self.potential_evaluations,
            name="potential_evaluations",
            maximum=_MAX_POTENTIAL_EVALUATIONS,
        )
        if self.interval_enclosure_provided is not False:
            raise ValueError("this adaptive diagnostic cannot claim an interval")
        if self.ode_discretization_error_enclosed is not False:
            raise ValueError("ODE discretization error is not enclosed")
        for name, value in checked.items():
            object.__setattr__(self, name, value)
        object.__setattr__(
            self,
            "state_family_rate_divergence",
            _immutable_array(rates),
        )
        object.__setattr__(self, "active_edge_counts", counts)
        object.__setattr__(self, "potential_evaluations", evaluations)


def tilted_path_kl_by_edge_family(
    base_initial: object,
    base_generator: object,
    reference_potential: PositivePotential,
    candidate_potential: PositivePotential,
    horizon: object,
    edge_family_indices: object,
    *,
    evaluation_times: object = None,
    rtol: object = 2.0e-10,
    atol: object = 2.0e-12,
    max_step: object = None,
    quadrature_epsabs: object = 1.0e-10,
    quadrature_epsrel: object = 1.0e-9,
    quadrature_limit: object = 1_000,
    max_potential_evaluations: object = 200_000,
    reference_marginal: Optional[Callable[[float], object]] = None,
) -> FiniteBridgeFamilyPathKL:
    """Numerically split ``KL(P^h || P^h_hat)`` by aggregate edge family.

    ``edge_family_indices`` must be an integer matrix with ``-1`` on the
    diagonal and every structural-zero base edge, and indices ``0, 1, 2`` on
    positive aggregate edges for birth, death, and replacement respectively.
    The base generator must already have aggregated any occurrence-labelled
    routes and multiplicities that reach the same unlabeled destination.
    """

    engine = _TiltEngine(np.asarray(base_generator))
    families, edge_counts = _family_index_array(edge_family_indices, engine=engine)
    base_p = validate_probability_vector(np.asarray(base_initial), engine.state_count)
    (
        duration,
        relative,
        absolute,
        step,
        quad_absolute,
        quad_relative,
        quad_limit,
    ) = _numerical_controls(
        horizon,
        rtol,
        atol,
        max_step,
        quadrature_epsabs,
        quadrature_epsrel,
        quadrature_limit,
    )
    times = _evaluation_grid(duration, evaluation_times)
    budget = _EvaluationBudget(max_potential_evaluations)  # type: ignore[arg-type]
    reference_values = _potential_values(
        reference_potential, 0.0, engine.state_count, budget
    )
    candidate_values = _potential_values(
        candidate_potential, 0.0, engine.state_count, budget
    )
    reference_initial = _initial_from_values(base_p, reference_values, 0.0)
    candidate_initial = _initial_from_values(base_p, candidate_values, 0.0)
    initial_kl = _categorical_kl(
        reference_initial.probabilities, candidate_initial.probabilities
    )

    if reference_marginal is None:
        solution, marginals, ode_evaluations = _solve_marginal(
            reference_initial.probabilities,
            engine,
            reference_potential,
            duration,
            times,
            relative,
            absolute,
            step,
            budget,
        )
    else:
        if not callable(reference_marginal):
            raise TypeError("reference_marginal must be callable or None")

        def checked_supplied_marginal(time: float) -> np.ndarray:
            return _validated_marginal(
                reference_marginal(float(time)),
                state_count=engine.state_count,
                numerical_atol=absolute,
            )

        marginals = np.stack(
            [checked_supplied_marginal(float(time)) for time in times], axis=0
        )
        if not np.allclose(
            marginals[0],
            reference_initial.probabilities,
            atol=max(2.0e-10, 128.0 * absolute),
            rtol=0.0,
        ):
            raise ValueError(
                "supplied reference marginal disagrees with the reference "
                "tilted initial law"
            )
        solution = None
        ode_evaluations = 0

    if duration == 0.0:
        occupation = np.zeros(engine.state_count, dtype=np.float64)
        family_dynamic = np.zeros(3, dtype=np.float64)
        quadrature_error = 0.0
    else:

        def path_integrand(time: float) -> np.ndarray:
            if reference_marginal is None:
                marginal = _dense_marginal(solution, time, engine.state_count, absolute)
            else:
                marginal = checked_supplied_marginal(time)
            reference = engine.tilt(
                _potential_values(reference_potential, time, engine.state_count, budget)
            )
            candidate = engine.tilt(
                _potential_values(candidate_potential, time, engine.state_count, budget)
            )
            state_family = _state_family_rate_divergence(reference, candidate, families)
            family_rate = marginal @ state_family
            if np.any(family_rate < 0.0) or not np.all(np.isfinite(family_rate)):
                raise ArithmeticError("instantaneous family KL is invalid")
            return np.concatenate((marginal, family_rate))

        combined, quadrature_error = _quadrature(
            path_integrand,
            duration,
            quad_absolute,
            quad_relative,
            quad_limit,
        )
        occupation = combined[:-3]
        family_dynamic = combined[-3:]
        tolerance = max(
            2.0e-9 * max(duration, 1.0),
            8.0 * quadrature_error,
            128.0 * absolute,
        )
        if np.any(occupation < -tolerance):
            raise ArithmeticError("integrated occupation became negative")
        occupation[occupation < 0.0] = 0.0
        if not math.isclose(
            math.fsum(float(value) for value in occupation),
            duration,
            rel_tol=0.0,
            abs_tol=tolerance,
        ):
            raise ArithmeticError("integrated occupation does not sum to horizon")
        if np.any(family_dynamic < -tolerance):
            raise ArithmeticError("a family path KL became materially negative")
        family_dynamic[family_dynamic < 0.0] = 0.0
        if not np.all(np.isfinite(family_dynamic)):
            raise ArithmeticError("a family path KL is not representable")

    occupancy = TimeIndexedOccupancy(
        initial_law=reference_initial,
        times=times,
        marginals=marginals,
        integrated_occupation=occupation,
        quadrature_error=quadrature_error,
        ode_evaluations=ode_evaluations,
        potential_evaluations=budget.count,
    )
    time_rates = []
    for direct_time in times:
        reference = engine.tilt(
            _potential_values(
                reference_potential,
                float(direct_time),
                engine.state_count,
                budget,
            )
        )
        candidate = engine.tilt(
            _potential_values(
                candidate_potential,
                float(direct_time),
                engine.state_count,
                budget,
            )
        )
        time_rates.append(_state_family_rate_divergence(reference, candidate, families))
    birth, death, replacement = (float(value) for value in family_dynamic)
    dynamic = math.fsum((birth, death, replacement))
    total = initial_kl + dynamic
    if not math.isfinite(total) or total < 0.0:
        raise ArithmeticError("total family path KL is not representable")
    return FiniteBridgeFamilyPathKL(
        orientation="KL(P_REFERENCE_H || P_CANDIDATE_H_HAT)",
        family_names=FINITE_BRIDGE_JUMP_FAMILY_ORDER,
        aggregate_state_transition_rates_used=True,
        supplied_reference_marginal_used=reference_marginal is not None,
        initial=initial_kl,
        birth_dynamic=birth,
        death_dynamic=death,
        replacement_dynamic=replacement,
        dynamic=dynamic,
        total=total,
        reference_initial=reference_initial,
        candidate_initial=candidate_initial,
        occupancy=occupancy,
        state_family_rate_divergence=np.stack(time_rates, axis=0),
        active_edge_counts=edge_counts,
        quadrature_error_estimate=quadrature_error,
        potential_evaluations=budget.count,
        interval_enclosure_provided=False,
        ode_discretization_error_enclosed=False,
    )


__all__ = [
    "FINITE_BRIDGE_JUMP_FAMILY_ORDER",
    "FiniteBridgeFamilyPathKL",
    "tilted_path_kl_by_edge_family",
]
