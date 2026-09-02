"""Execute the frozen A1/B1 exact-population learned bridge pilot.

This module has no data loader and writes no result artifact.  It evaluates a
known finite law by complete enumeration under the thresholds frozen in
``research/59_a1_b1_exact_population_learned_pilot_spec.md``.  The saturated
learner is a plumbing control, not a scalable model or scientific result.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Callable, Tuple

import numpy as np

from heterodiff.models.finite_bridge_potential import (
    fit_additive_count_potential,
    fit_bounded_tabular_potential,
    population_logistic_risk,
)
from heterodiff.theory import (
    FiniteAtomicAssociationBridgeOracle,
    FiniteAtomicCountingSpace,
    PositiveFiniteAtomicObservation,
    TabulatedPositivePotential,
    capped_counting_reference,
    conditional_initial_law,
    finite_bridge_population,
    integrate_tilted_occupancy,
    potential_tilted_generator,
    tilted_path_kl,
)


_TERMINAL_TIME = 1.0
_TIME_POINT_COUNT = 33
_FAMILY_ORDER = ("birth", "death", "replacement")


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.float64
    ).reshape(contiguous.shape)


@dataclass(frozen=True)
class FiniteBridgeLearnedPilotResult:
    """Complete decision record for one deterministic B1 execution."""

    time_grid: np.ndarray
    observation_marginal_mass: np.ndarray
    log_bound: float
    optimizer_converged: bool
    optimizer_iterations: int
    saturated_gradient_infinity_norm: float
    saturated_requested_gradient_tolerance: float
    additive_optimizer_converged: bool
    additive_gradient_infinity_norm: float
    additive_requested_gradient_tolerance: float
    additive_minimum_hessian_eigenvalue: float
    additive_maximum_hessian_condition_number: float
    additive_summed_half_newton_decrement: float
    initial_population_risk: float
    final_population_risk: float
    oracle_population_risk: float
    population_excess_risk: float
    product_observation_risk: float
    product_control_max_logit: float
    product_control_excess_risk: float
    additive_population_excess_risk: float
    additive_max_absolute_logit: float
    additive_count_interaction_residual: float
    max_logit_error: float
    max_centered_log_information_error: float
    edge_log_rate_error: np.ndarray
    conditional_initial_tv: np.ndarray
    ratio_normalization_residual: float
    conditional_endpoint_tv: np.ndarray
    learned_path_kl: np.ndarray
    weighted_learned_path_kl: float
    path_kl_refinement_residual: np.ndarray
    endpoint_refinement_tv: np.ndarray
    occupation_refinement_l1: np.ndarray
    exact_table_path_kl: np.ndarray
    learned_exact_table_path_kl_residual: float
    additive_path_kl: np.ndarray
    base_path_kl: np.ndarray
    oracle_self_path_kl: np.ndarray
    wrong_initial_endpoint_tv: np.ndarray
    base_endpoint_tv: np.ndarray
    generator_row_sum_residual: float
    edit_cycle_residual: float
    passed: bool
    failures: Tuple[str, ...]

    def __post_init__(self) -> None:
        scalar_names = (
            "log_bound",
            "saturated_gradient_infinity_norm",
            "saturated_requested_gradient_tolerance",
            "additive_gradient_infinity_norm",
            "additive_requested_gradient_tolerance",
            "additive_minimum_hessian_eigenvalue",
            "additive_maximum_hessian_condition_number",
            "additive_summed_half_newton_decrement",
            "initial_population_risk",
            "final_population_risk",
            "oracle_population_risk",
            "population_excess_risk",
            "product_observation_risk",
            "product_control_max_logit",
            "product_control_excess_risk",
            "additive_population_excess_risk",
            "additive_max_absolute_logit",
            "additive_count_interaction_residual",
            "max_logit_error",
            "max_centered_log_information_error",
            "ratio_normalization_residual",
            "weighted_learned_path_kl",
            "learned_exact_table_path_kl_residual",
            "generator_row_sum_residual",
            "edit_cycle_residual",
        )
        for name in scalar_names:
            raw = getattr(self, name)
            if isinstance(raw, (bool, np.bool_)) or not isinstance(raw, Real):
                raise TypeError("{} must be a real non-boolean number".format(name))
            value = float(raw)
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("{} must be finite and nonnegative".format(name))
            object.__setattr__(self, name, value)
        if not isinstance(self.optimizer_converged, bool):
            raise TypeError("optimizer_converged must be boolean")
        if not isinstance(self.additive_optimizer_converged, bool):
            raise TypeError("additive_optimizer_converged must be boolean")
        if isinstance(self.optimizer_iterations, (bool, np.bool_)) or not isinstance(
            self.optimizer_iterations, Integral
        ):
            raise TypeError("optimizer_iterations must be an integer")
        if int(self.optimizer_iterations) < 0:
            raise ValueError("optimizer_iterations must be nonnegative")
        object.__setattr__(self, "optimizer_iterations", int(self.optimizer_iterations))
        for name in (
            "time_grid",
            "observation_marginal_mass",
            "edge_log_rate_error",
            "conditional_initial_tv",
            "conditional_endpoint_tv",
            "learned_path_kl",
            "path_kl_refinement_residual",
            "endpoint_refinement_tv",
            "occupation_refinement_l1",
            "exact_table_path_kl",
            "additive_path_kl",
            "base_path_kl",
            "oracle_self_path_kl",
            "wrong_initial_endpoint_tv",
            "base_endpoint_tv",
        ):
            value = np.asarray(getattr(self, name), dtype=float)
            if not np.all(np.isfinite(value)) or np.any(value < 0.0):
                raise ValueError("{} must be finite and nonnegative".format(name))
            object.__setattr__(self, name, _immutable_float_array(value))
        if self.edge_log_rate_error.shape != (3,):
            raise ValueError("edge_log_rate_error must follow the three family order")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be boolean")
        if type(self.failures) is not tuple or not all(
            isinstance(value, str) and value for value in self.failures
        ):
            raise TypeError("failures must be a tuple of nonempty strings")
        if self.passed != (len(self.failures) == 0):
            raise ValueError("passed must be equivalent to an empty failure list")

    @property
    def edge_family_order(self) -> Tuple[str, ...]:
        return _FAMILY_ORDER


def _build_frozen_fixture():
    latent_space = FiniteAtomicCountingSpace(("a", "b"), 2)
    observation_space = FiniteAtomicCountingSpace(("x", "y"), 2)
    observation = PositiveFiniteAtomicObservation(
        latent_space,
        observation_space,
        detection_probability=(0.65, 0.40),
        confusion_matrix=((0.80, 0.20), (0.30, 0.70)),
        reference_weights=(0.35, 0.20),
        contamination_probability=0.07,
    )
    oracle = FiniteAtomicAssociationBridgeOracle(
        latent_space,
        observation,
        birth_rates=(0.45, 0.25),
        per_particle_death_rates=(0.30, 0.55),
        replacement_rates=((0.0, 0.20), (0.60, 0.0)),
    )
    initial = capped_counting_reference(latent_space, (0.55, 0.35))
    times = np.linspace(0.0, _TERMINAL_TIME, _TIME_POINT_COUNT, dtype=float)
    return latent_space, observation_space, oracle, initial, times


def _exact_potential(
    oracle: FiniteAtomicAssociationBridgeOracle,
    observed_counts: Tuple[int, ...],
) -> Callable[[float], np.ndarray]:
    def potential(direct_time: float) -> np.ndarray:
        remaining = _TERMINAL_TIME - float(direct_time)
        tolerance = 32.0 * np.finfo(np.float64).eps
        if remaining < 0.0 and remaining >= -tolerance:
            remaining = 0.0
        if remaining < 0.0:
            raise ValueError("direct time exceeds the frozen terminal time")
        return oracle.backward_information(remaining, observed_counts)

    return potential


def _tabulated_potential(log_grid: np.ndarray, observation_index: int, times):
    return TabulatedPositivePotential(
        times, np.exp(log_grid[:, :, observation_index])
    )


def _total_variation(first: np.ndarray, second: np.ndarray) -> float:
    return 0.5 * float(np.abs(first - second).sum())


def _path_controls(initial, generator, reference, candidate, times, *, refined=False):
    return tilted_path_kl(
        initial,
        generator,
        reference,
        candidate,
        _TERMINAL_TIME,
        evaluation_times=times,
        rtol=2.0e-11 if refined else 2.0e-10,
        atol=2.0e-13 if refined else 2.0e-12,
        max_step=1.0 / (256.0 if refined else 128.0),
        quadrature_epsabs=1.0e-12 if refined else 1.0e-11,
        quadrature_epsrel=1.0e-11 if refined else 1.0e-10,
        quadrature_limit=2_000,
        max_potential_evaluations=300_000,
    )


def _occupancy(initial, generator, potential, times, *, refined=False):
    return integrate_tilted_occupancy(
        initial,
        generator,
        potential,
        _TERMINAL_TIME,
        evaluation_times=times,
        rtol=2.0e-11 if refined else 2.0e-10,
        atol=2.0e-13 if refined else 2.0e-12,
        max_step=1.0 / (256.0 if refined else 128.0),
        quadrature_epsabs=1.0e-12 if refined else 1.0e-11,
        quadrature_epsrel=1.0e-11 if refined else 1.0e-10,
        quadrature_limit=2_000,
        max_potential_evaluations=300_000,
    )


def run_finite_bridge_learned_pilot() -> FiniteBridgeLearnedPilotResult:
    """Run the frozen complete-population B1 gate and return every metric."""

    latent_space, observation_space, oracle, initial, times = _build_frozen_fixture()
    population = finite_bridge_population(
        oracle, initial, times, _TERMINAL_TIME
    )
    exact_logits = population.optimal_log_density_ratio
    maximum_exact_logit = float(np.max(np.abs(exact_logits)))
    log_bound = float(1.0 + math.ceil(maximum_exact_logit))
    if log_bound > 50.0:
        raise RuntimeError("frozen B1 log bound exceeds its safety ceiling")

    fit = fit_bounded_tabular_potential(
        times,
        population.joint_mass,
        population.product_mass,
        log_bound=log_bound,
        max_iterations=2_000,
        gradient_tolerance=1.0e-12,
    )
    learned_logits = fit.potential.log_potential_grid
    additive = fit_additive_count_potential(
        times,
        np.asarray(latent_space.states, dtype=np.int64),
        population.joint_mass,
        population.product_mass,
        logit_safety_ceiling=50.0,
        max_iterations=3_000,
        gradient_tolerance=1.0e-11,
    )
    product_control = fit_bounded_tabular_potential(
        times,
        population.product_mass,
        population.product_mass,
        log_bound=1.0,
        max_iterations=500,
        gradient_tolerance=1.0e-12,
    )

    error = learned_logits - exact_logits
    centered_error = error - error.mean(axis=1, keepdims=True)
    max_logit_error = float(np.max(np.abs(error)))
    max_centered_error = float(np.max(np.abs(centered_error)))
    ratios = np.exp(learned_logits)
    ratio_residual = float(
        np.max(
            np.abs(
                np.sum(
                    ratios
                    * population.observation_marginal_mass[None, None, :],
                    axis=2,
                )
                - 1.0
            )
        )
    )

    additive_logits = additive.potential.log_potential_grid
    additive_max_absolute_logit = float(np.max(np.abs(additive_logits)))
    additive_interaction_residual = 0.0
    zero_state = (0,) * latent_space.atom_count
    zero_index = latent_space.index_of(zero_state)
    for first_atom in range(latent_space.atom_count):
        for second_atom in range(latent_space.atom_count):
            first_state = list(zero_state)
            first_state[first_atom] += 1
            second_state = list(zero_state)
            second_state[second_atom] += 1
            pair_state = list(zero_state)
            pair_state[first_atom] += 1
            pair_state[second_atom] += 1
            first_index = latent_space.index_of(tuple(first_state))
            second_index = latent_space.index_of(tuple(second_state))
            pair_index = latent_space.index_of(tuple(pair_state))
            second_difference = (
                additive_logits[:, pair_index, :]
                - additive_logits[:, first_index, :]
                - additive_logits[:, second_index, :]
                + additive_logits[:, zero_index, :]
            )
            additive_interaction_residual = max(
                additive_interaction_residual,
                float(np.max(np.abs(second_difference))),
            )

    edge_errors = {family: [] for family in _FAMILY_ORDER}
    row_residual = 0.0
    cycle_residual = 0.0
    base_generator = oracle.generator
    base_edges = np.argwhere(
        base_generator - np.diag(np.diag(base_generator)) > 0.0
    )
    for observation_index, observed_counts in enumerate(observation_space.states):
        learned_potential = _tabulated_potential(
            learned_logits, observation_index, times
        )
        for direct_time in times:
            exact_generator = oracle.bridge_generator(
                _TERMINAL_TIME - float(direct_time), observed_counts
            )
            learned_generator = potential_tilted_generator(
                base_generator, learned_potential, float(direct_time)
            )
            row_residual = max(
                row_residual,
                float(np.max(np.abs(learned_generator.sum(axis=1)))),
            )
            log_corrections = {}
            for source, destination in base_edges:
                family = oracle.transition_family(
                    latent_space.states[int(source)],
                    latent_space.states[int(destination)],
                )
                if family not in edge_errors:
                    raise ArithmeticError("an active edge has no frozen family")
                exact_rate = exact_generator[source, destination]
                learned_rate = learned_generator[source, destination]
                edge_errors[family].append(
                    abs(math.log(learned_rate) - math.log(exact_rate))
                )
                log_corrections[(int(source), int(destination))] = math.log(
                    learned_rate / base_generator[source, destination]
                )
            for (source, destination), correction in log_corrections.items():
                reverse = log_corrections.get((destination, source))
                if reverse is not None:
                    cycle_residual = max(
                        cycle_residual, abs(correction + reverse)
                    )
            for first in range(latent_space.n_states):
                for second in range(latent_space.n_states):
                    first_edge = log_corrections.get((first, second))
                    if first_edge is None:
                        continue
                    for third in range(latent_space.n_states):
                        second_edge = log_corrections.get((second, third))
                        third_edge = log_corrections.get((third, first))
                        if second_edge is not None and third_edge is not None:
                            cycle_residual = max(
                                cycle_residual,
                                abs(first_edge + second_edge + third_edge),
                            )

    family_errors = np.asarray(
        [max(edge_errors[family]) for family in _FAMILY_ORDER], dtype=float
    )

    conditional_initial_tv = []
    endpoint_tv = []
    learned_path_kl = []
    path_refinement = []
    endpoint_refinement = []
    occupation_refinement = []
    exact_table_path_kl = []
    additive_path_kl = []
    base_path_kl = []
    self_path_kl = []
    wrong_initial_endpoint_tv = []
    base_endpoint_tv = []
    ones = lambda _time: np.ones(latent_space.n_states, dtype=float)
    for observation_index, observed_counts in enumerate(observation_space.states):
        exact = _exact_potential(oracle, observed_counts)
        learned = _tabulated_potential(learned_logits, observation_index, times)
        exact_table = _tabulated_potential(
            exact_logits, observation_index, times
        )
        additive_table = _tabulated_potential(
            additive.potential.log_potential_grid, observation_index, times
        )

        learned_initial = conditional_initial_law(initial, learned).probabilities
        conditional_initial_tv.append(
            _total_variation(
                learned_initial, population.conditional_initial[:, observation_index]
            )
        )
        learned_occupancy = _occupancy(initial, base_generator, learned, times)
        refined_occupancy = _occupancy(
            initial, base_generator, learned, times, refined=True
        )
        endpoint_tv.append(
            _total_variation(
                learned_occupancy.marginals[-1],
                population.conditional_terminal[:, observation_index],
            )
        )
        primary_path = _path_controls(
            initial, base_generator, exact, learned, times
        )
        refined_path = _path_controls(
            initial, base_generator, exact, learned, times, refined=True
        )
        learned_path_kl.append(primary_path.total)
        path_refinement.append(abs(primary_path.total - refined_path.total))
        endpoint_refinement.append(
            _total_variation(
                learned_occupancy.marginals[-1],
                refined_occupancy.marginals[-1],
            )
        )
        occupation_refinement.append(
            float(
                np.abs(
                    learned_occupancy.integrated_occupation
                    - refined_occupancy.integrated_occupation
                ).sum()
            )
        )
        exact_table_path_kl.append(
            _path_controls(initial, base_generator, exact, exact_table, times).total
        )
        additive_path_kl.append(
            _path_controls(
                initial, base_generator, exact, additive_table, times
            ).total
        )
        base_path_kl.append(
            _path_controls(initial, base_generator, exact, ones, times).total
        )
        self_path_kl.append(
            _path_controls(initial, base_generator, exact, exact, times).total
        )

        direct_bridge = oracle.condition(
            initial, _TERMINAL_TIME, observed_counts
        )
        wrong_endpoint = initial @ direct_bridge.doob_transition
        wrong_initial_endpoint_tv.append(
            _total_variation(
                wrong_endpoint, population.conditional_terminal[:, observation_index]
            )
        )
        base_endpoint_tv.append(
            _total_variation(
                population.terminal_marginal,
                population.conditional_terminal[:, observation_index],
            )
        )

    learned_path_kl_array = np.asarray(learned_path_kl, dtype=float)
    exact_table_path_kl_array = np.asarray(exact_table_path_kl, dtype=float)
    learned_exact_table_residual = float(
        np.max(np.abs(learned_path_kl_array - exact_table_path_kl_array))
    )
    weighted_path_kl = float(
        population.observation_marginal_mass @ learned_path_kl_array
    )
    product_risk = population_logistic_risk(
        population.product_mass,
        population.product_mass,
        product_control.potential.log_potential_grid,
    )
    product_max_logit = float(
        np.max(np.abs(product_control.potential.log_potential_grid))
    )

    failures = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(fit.optimizer_converged, "saturated optimizer did not converge")
    require(
        fit.gradient_infinity_norm <= fit.requested_gradient_tolerance,
        "saturated optimizer missed its requested gradient tolerance",
    )
    require(additive.optimizer_converged, "additive optimizer did not converge")
    require(
        additive.gradient_infinity_norm <= additive.requested_gradient_tolerance,
        "additive optimizer missed its requested raw-gradient tolerance",
    )
    require(fit.excess_risk <= 1.0e-10, "population excess risk exceeds 1e-10")
    require(max_logit_error <= 1.0e-4, "maximum fitted-node logit error exceeds 1e-4")
    require(
        max_centered_error <= 1.0e-4,
        "maximum centered log-information error exceeds 1e-4",
    )
    for family, value in zip(_FAMILY_ORDER, family_errors):
        require(
            float(value) <= 2.0e-4,
            "{} edge log-rate error exceeds 2e-4".format(family),
        )
    require(
        max(conditional_initial_tv) <= 1.0e-5,
        "conditional-initial TV exceeds 1e-5",
    )
    require(ratio_residual <= 1.0e-5, "ratio-normalization residual exceeds 1e-5")
    require(max(endpoint_tv) <= 5.0e-3, "conditional endpoint TV exceeds 5e-3")
    require(weighted_path_kl <= 1.0e-4, "weighted path KL exceeds 1e-4 nat")
    require(max(learned_path_kl) <= 5.0e-4, "per-observation path KL exceeds 5e-4 nat")
    require(max(self_path_kl) <= 1.0e-10, "oracle self path KL exceeds 1e-10 nat")
    require(row_residual <= 1.0e-11, "generator row-sum residual exceeds 1e-11")
    require(cycle_residual <= 1.0e-11, "edit-cycle residual exceeds 1e-11")
    require(
        max(path_refinement) <= 1.0e-8,
        "path-KL refinement residual exceeds 1e-8",
    )
    require(
        max(endpoint_refinement) <= 1.0e-8,
        "endpoint refinement TV exceeds 1e-8",
    )
    require(
        max(occupation_refinement) <= 1.0e-8,
        "occupation refinement L1 residual exceeds 1e-8",
    )
    require(
        additive_interaction_residual <= 1.0e-11,
        "additive control contains a count interaction",
    )
    require(product_control.optimizer_converged, "product control did not converge")
    require(
        product_control.gradient_infinity_norm
        <= product_control.requested_gradient_tolerance,
        "product control missed its requested gradient tolerance",
    )
    require(product_max_logit <= 1.0e-10, "product control learned a nonzero logit")
    require(
        product_control.excess_risk <= 1.0e-12,
        "product control excess risk exceeds 1e-12",
    )
    require(
        abs(product_risk - math.log(2.0)) <= 1.0e-12,
        "product-positive control risk differs from log(2)",
    )
    require(
        additive.excess_risk > fit.excess_risk,
        "additive control does not have larger population excess risk",
    )
    require(
        product_risk > fit.final_risk,
        "product-positive control does not have larger risk on the true task",
    )
    require(
        bool(np.all(np.asarray(additive_path_kl) > learned_path_kl_array)),
        "additive path KL is not worse for every observation",
    )
    require(
        bool(np.all(np.asarray(base_path_kl) > learned_path_kl_array)),
        "base path KL is not worse for every observation",
    )
    require(
        bool(np.all(np.asarray(base_endpoint_tv) > np.asarray(endpoint_tv))),
        "unconditional base endpoint is not worse for every observation",
    )
    require(
        bool(
            np.all(
                np.asarray(wrong_initial_endpoint_tv) > np.asarray(endpoint_tv)
            )
        ),
        "wrong-initial endpoint is not worse for every observation",
    )
    require(
        learned_exact_table_residual <= 2.0e-8,
        "learned and exact-node table path KL differ by more than 2e-8",
    )

    return FiniteBridgeLearnedPilotResult(
        time_grid=times,
        observation_marginal_mass=population.observation_marginal_mass,
        log_bound=log_bound,
        optimizer_converged=fit.optimizer_converged,
        optimizer_iterations=fit.iterations,
        saturated_gradient_infinity_norm=fit.gradient_infinity_norm,
        saturated_requested_gradient_tolerance=fit.requested_gradient_tolerance,
        additive_optimizer_converged=additive.optimizer_converged,
        additive_gradient_infinity_norm=additive.gradient_infinity_norm,
        additive_requested_gradient_tolerance=additive.requested_gradient_tolerance,
        additive_minimum_hessian_eigenvalue=(
            additive.minimum_hessian_eigenvalue
        ),
        additive_maximum_hessian_condition_number=(
            additive.maximum_hessian_condition_number
        ),
        additive_summed_half_newton_decrement=(
            additive.summed_half_newton_decrement
        ),
        initial_population_risk=fit.initial_risk,
        final_population_risk=fit.final_risk,
        oracle_population_risk=fit.oracle_risk,
        population_excess_risk=fit.excess_risk,
        product_observation_risk=product_risk,
        product_control_max_logit=product_max_logit,
        product_control_excess_risk=product_control.excess_risk,
        additive_population_excess_risk=additive.excess_risk,
        additive_max_absolute_logit=additive_max_absolute_logit,
        additive_count_interaction_residual=additive_interaction_residual,
        max_logit_error=max_logit_error,
        max_centered_log_information_error=max_centered_error,
        edge_log_rate_error=family_errors,
        conditional_initial_tv=np.asarray(conditional_initial_tv),
        ratio_normalization_residual=ratio_residual,
        conditional_endpoint_tv=np.asarray(endpoint_tv),
        learned_path_kl=learned_path_kl_array,
        weighted_learned_path_kl=weighted_path_kl,
        path_kl_refinement_residual=np.asarray(path_refinement),
        endpoint_refinement_tv=np.asarray(endpoint_refinement),
        occupation_refinement_l1=np.asarray(occupation_refinement),
        exact_table_path_kl=exact_table_path_kl_array,
        learned_exact_table_path_kl_residual=learned_exact_table_residual,
        additive_path_kl=np.asarray(additive_path_kl),
        base_path_kl=np.asarray(base_path_kl),
        oracle_self_path_kl=np.asarray(self_path_kl),
        wrong_initial_endpoint_tv=np.asarray(wrong_initial_endpoint_tv),
        base_endpoint_tv=np.asarray(base_endpoint_tv),
        generator_row_sum_residual=row_residual,
        edit_cycle_residual=cycle_residual,
        passed=len(failures) == 0,
        failures=tuple(failures),
    )


__all__ = [
    "FiniteBridgeLearnedPilotResult",
    "run_finite_bridge_learned_pilot",
]
