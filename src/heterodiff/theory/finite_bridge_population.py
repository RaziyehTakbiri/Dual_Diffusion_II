"""Exact population tables for the finite association bridge.

This module fixes the direct continuous-time orientation

``X_0 -> X_t -> X_T,        A | X_T ~ K_epsilon(. | X_T)``.

It is an enumerable learning oracle, not a scalable estimator.  For a finite
list of direct times it constructs the physical joint probability mass
``J_t(x, a)``, the product mass ``pi_t(x) p_A(a)``, and their optimal
equal-prior density-ratio-classification logit.  Physical probability masses
are used as risk weights.  Densities relative to the declared capped-Poisson
observation reference are retained separately; they yield exactly the same
ratio but must not be confused with probability masses.

The initial marginal is required to have full support.  This makes the
population-optimal log ratio pointwise identified on the complete finite table
rather than only almost everywhere under a product law with zero cells.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
import math
from numbers import Real
from typing import Iterable, Optional, Tuple

import numpy as np

from .finite_atomic_association_bridge import (
    FiniteAtomicAssociationBridgeOracle,
)
from .finite_state import validate_probability_vector


_MAX_TIME_POINTS = 1_024
_MAX_POPULATION_CELLS = 2_000_000
_MAX_DENSE_MULTIPLY_WORK = 200_000_000
_CONSISTENCY_ATOL = 5.0e-11
_CONSISTENCY_RTOL = 5.0e-11


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.float64
    ).reshape(contiguous.shape)


def _numeric_array(
    value: object,
    *,
    name: str,
    shape: Optional[Tuple[int, ...]] = None,
    strictly_positive: bool = False,
) -> np.ndarray:
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
        array = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s cannot be represented as float64" % name) from error
    if shape is not None and array.shape != shape:
        raise ValueError("%s must have shape %r" % (name, shape))
    if not np.all(np.isfinite(array)):
        raise ValueError("%s entries must be finite" % name)
    if strictly_positive and np.any(array <= 0.0):
        raise ValueError("%s entries must be strictly positive" % name)
    return array


def _validated_terminal_time(value: object) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("terminal_time must be a real non-boolean number")
    terminal = float(value)
    if not math.isfinite(terminal) or terminal < 0.0:
        raise ValueError("terminal_time must be finite and nonnegative")
    return terminal


def _validated_times(value: object, terminal_time: float) -> np.ndarray:
    if isinstance(value, (str, bytes)):
        raise TypeError("times must be a finite iterable of real numbers")
    try:
        iterator = iter(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("times must be a finite iterable of real numbers") from error
    raw = tuple(islice(iterator, _MAX_TIME_POINTS + 1))
    if not raw:
        raise ValueError("times must contain at least one direct time")
    if len(raw) > _MAX_TIME_POINTS:
        raise ValueError(
            "times exceeds the limit of %d entries" % _MAX_TIME_POINTS
        )
    checked = []
    for index, item in enumerate(raw):
        if isinstance(item, (bool, np.bool_)) or not isinstance(item, Real):
            raise TypeError("times[%d] must be a real non-boolean number" % index)
        time = float(item)
        if not math.isfinite(time) or time < 0.0 or time > terminal_time:
            raise ValueError(
                "times[%d] must lie in [0, terminal_time]" % index
            )
        if checked and time <= checked[-1]:
            raise ValueError("times must be strictly increasing")
        checked.append(time)
    return _immutable_float_array(np.asarray(checked, dtype=np.float64))


def _positive_probability_vector(
    value: object, *, name: str, size: Optional[int] = None
) -> np.ndarray:
    raw = _numeric_array(value, name=name)
    if raw.ndim != 1:
        raise ValueError("%s must be one-dimensional" % name)
    if size is not None and raw.shape != (size,):
        raise ValueError("%s must have shape (%d,)" % (name, size))
    checked = validate_probability_vector(raw, raw.size, atol=2.0e-12)
    if np.any(checked <= 0.0):
        raise ValueError("%s must have full support" % name)
    return checked


def _columns_are_probabilities(value: np.ndarray) -> bool:
    return bool(
        np.all(value > 0.0)
        and np.allclose(
            value.sum(axis=-2),
            1.0,
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        )
    )


def _risk_per_time_from_arrays(
    joint_mass: np.ndarray,
    product_mass: np.ndarray,
    logits: np.ndarray,
) -> np.ndarray:
    positive_loss = np.logaddexp(0.0, -logits)
    negative_loss = np.logaddexp(0.0, logits)
    risks = 0.5 * np.sum(
        joint_mass * positive_loss + product_mass * negative_loss,
        axis=(1, 2),
    )
    if not np.all(np.isfinite(risks)) or np.any(risks < 0.0):
        raise ArithmeticError("population logistic risk is not representable")
    return risks


@dataclass(frozen=True, eq=False)
class FiniteBridgePopulation:
    """Immutable exact population tables on a finite direct-time grid.

    Arrays with a leading time axis follow the order in :attr:`times`.
    Observation-axis arrays follow ``oracle.observation.observations``.  This
    includes the explicit overflow atom for the A1 count-plus-overflow law and
    remains the legacy count-vector ordering for the accepted B1 law.
    ``joint_mass`` and ``product_mass`` are the physical probability weights
    for density-ratio training.  Their ``*_density`` counterparts are relative
    to ``observation_reference_mass`` and are diagnostic identities only.
    """

    times: np.ndarray
    terminal_time: float
    initial_marginal: np.ndarray
    time_marginal: np.ndarray
    terminal_marginal: np.ndarray
    observation_reference_mass: np.ndarray
    observation_marginal_mass: np.ndarray
    observation_marginal_density: np.ndarray
    backward_information_mass: np.ndarray
    backward_information_density: np.ndarray
    joint_mass: np.ndarray
    joint_density: np.ndarray
    product_mass: np.ndarray
    product_density: np.ndarray
    optimal_log_density_ratio: np.ndarray
    initial_joint_mass: np.ndarray
    terminal_joint_mass: np.ndarray
    conditional_initial: np.ndarray
    conditional_time: np.ndarray
    conditional_terminal: np.ndarray
    optimal_logistic_risk_per_time: np.ndarray

    def __post_init__(self) -> None:
        terminal = _validated_terminal_time(self.terminal_time)
        times = _numeric_array(self.times, name="times")
        if times.ndim != 1 or times.size == 0:
            raise ValueError("times must be a nonempty one-dimensional array")
        if times.size > _MAX_TIME_POINTS:
            raise ValueError("times exceeds the population time limit")
        if np.any(times < 0.0) or np.any(times > terminal):
            raise ValueError("times must lie in [0, terminal_time]")
        if times.size > 1 and np.any(times[1:] <= times[:-1]):
            raise ValueError("times must be strictly increasing")

        initial = _positive_probability_vector(
            self.initial_marginal, name="initial_marginal"
        )
        state_count = initial.size
        reference = _positive_probability_vector(
            self.observation_reference_mass,
            name="observation_reference_mass",
        )
        observation_count = reference.size
        time_count = times.size

        time_marginal = _numeric_array(
            self.time_marginal,
            name="time_marginal",
            shape=(time_count, state_count),
            strictly_positive=True,
        )
        if not np.allclose(
            time_marginal.sum(axis=1),
            1.0,
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError("time_marginal rows must be probability vectors")
        terminal_marginal = _positive_probability_vector(
            self.terminal_marginal,
            name="terminal_marginal",
            size=state_count,
        )
        observation_mass = _positive_probability_vector(
            self.observation_marginal_mass,
            name="observation_marginal_mass",
            size=observation_count,
        )
        observation_density = _numeric_array(
            self.observation_marginal_density,
            name="observation_marginal_density",
            shape=(observation_count,),
            strictly_positive=True,
        )
        if not np.allclose(
            observation_density * reference,
            observation_mass,
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError("observation marginal PMF/density conversion is invalid")

        table_shape = (time_count, state_count, observation_count)
        backward_mass = _numeric_array(
            self.backward_information_mass,
            name="backward_information_mass",
            shape=table_shape,
            strictly_positive=True,
        )
        backward_density = _numeric_array(
            self.backward_information_density,
            name="backward_information_density",
            shape=table_shape,
            strictly_positive=True,
        )
        if not np.allclose(
            backward_density * reference[None, None, :],
            backward_mass,
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError("backward-information PMF/density conversion is invalid")
        if not np.allclose(
            backward_mass.sum(axis=2),
            1.0,
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError("backward_information_mass rows must sum to one")
        if not np.allclose(
            np.sum(backward_density * reference[None, None, :], axis=2),
            1.0,
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError(
                "backward_information_density must normalize under the reference"
            )

        tables = {}
        for name in (
            "joint_mass",
            "joint_density",
            "product_mass",
            "product_density",
        ):
            tables[name] = _numeric_array(
                getattr(self, name),
                name=name,
                shape=table_shape,
                strictly_positive=True,
            )
        if not np.allclose(
            tables["joint_density"] * reference[None, None, :],
            tables["joint_mass"],
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ) or not np.allclose(
            tables["product_density"] * reference[None, None, :],
            tables["product_mass"],
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError("joint/product PMF and density tables disagree")
        if not np.allclose(
            tables["joint_mass"],
            time_marginal[:, :, None] * backward_mass,
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError("joint_mass is inconsistent with pi_t and information")
        if not np.allclose(
            tables["product_mass"],
            time_marginal[:, :, None] * observation_mass[None, None, :],
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError("product_mass is inconsistent with its marginals")
        for name in ("joint_mass", "product_mass"):
            if not np.allclose(
                tables[name].sum(axis=(1, 2)),
                1.0,
                atol=_CONSISTENCY_ATOL,
                rtol=_CONSISTENCY_RTOL,
            ):
                raise ValueError("%s must normalize at every time" % name)
        if not np.allclose(
            tables["joint_mass"].sum(axis=2),
            time_marginal,
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ) or not np.allclose(
            tables["joint_mass"].sum(axis=1),
            observation_mass[None, :],
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError("joint_mass does not recover both marginals")

        log_ratio = _numeric_array(
            self.optimal_log_density_ratio,
            name="optimal_log_density_ratio",
            shape=table_shape,
        )
        expected_log_ratio = np.log(tables["joint_mass"]) - np.log(
            tables["product_mass"]
        )
        density_log_ratio = np.log(tables["joint_density"]) - np.log(
            tables["product_density"]
        )
        if not np.allclose(
            log_ratio,
            expected_log_ratio,
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ) or not np.allclose(
            log_ratio,
            density_log_ratio,
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError("optimal log ratio is inconsistent with population tables")

        endpoint_shape = (state_count, observation_count)
        initial_joint = _numeric_array(
            self.initial_joint_mass,
            name="initial_joint_mass",
            shape=endpoint_shape,
            strictly_positive=True,
        )
        terminal_joint = _numeric_array(
            self.terminal_joint_mass,
            name="terminal_joint_mass",
            shape=endpoint_shape,
            strictly_positive=True,
        )
        for name, joint, marginal in (
            ("initial_joint_mass", initial_joint, initial),
            ("terminal_joint_mass", terminal_joint, terminal_marginal),
        ):
            if not np.allclose(
                joint.sum(axis=1),
                marginal,
                atol=_CONSISTENCY_ATOL,
                rtol=_CONSISTENCY_RTOL,
            ) or not np.allclose(
                joint.sum(axis=0),
                observation_mass,
                atol=_CONSISTENCY_ATOL,
                rtol=_CONSISTENCY_RTOL,
            ):
                raise ValueError("%s has inconsistent marginals" % name)

        conditional_initial = _numeric_array(
            self.conditional_initial,
            name="conditional_initial",
            shape=endpoint_shape,
            strictly_positive=True,
        )
        conditional_time = _numeric_array(
            self.conditional_time,
            name="conditional_time",
            shape=table_shape,
            strictly_positive=True,
        )
        conditional_terminal = _numeric_array(
            self.conditional_terminal,
            name="conditional_terminal",
            shape=endpoint_shape,
            strictly_positive=True,
        )
        if not np.allclose(
            conditional_initial,
            initial_joint / observation_mass[None, :],
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ) or not np.allclose(
            conditional_time,
            tables["joint_mass"] / observation_mass[None, None, :],
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ) or not np.allclose(
            conditional_terminal,
            terminal_joint / observation_mass[None, :],
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError("conditional laws are inconsistent with joint masses")
        if not _columns_are_probabilities(conditional_initial) or not bool(
            np.allclose(
                conditional_time.sum(axis=1),
                1.0,
                atol=_CONSISTENCY_ATOL,
                rtol=_CONSISTENCY_RTOL,
            )
        ) or not _columns_are_probabilities(conditional_terminal):
            raise ValueError("conditional laws must normalize over latent states")

        optimal_risk = _numeric_array(
            self.optimal_logistic_risk_per_time,
            name="optimal_logistic_risk_per_time",
            shape=(time_count,),
            strictly_positive=True,
        )
        expected_risk = _risk_per_time_from_arrays(
            tables["joint_mass"], tables["product_mass"], log_ratio
        )
        if not np.allclose(
            optimal_risk,
            expected_risk,
            atol=_CONSISTENCY_ATOL,
            rtol=_CONSISTENCY_RTOL,
        ):
            raise ValueError("stored optimal logistic risk is inconsistent")

        object.__setattr__(self, "terminal_time", terminal)
        for name, array in (
            ("times", times),
            ("initial_marginal", initial),
            ("time_marginal", time_marginal),
            ("terminal_marginal", terminal_marginal),
            ("observation_reference_mass", reference),
            ("observation_marginal_mass", observation_mass),
            ("observation_marginal_density", observation_density),
            ("backward_information_mass", backward_mass),
            ("backward_information_density", backward_density),
            ("joint_mass", tables["joint_mass"]),
            ("joint_density", tables["joint_density"]),
            ("product_mass", tables["product_mass"]),
            ("product_density", tables["product_density"]),
            ("optimal_log_density_ratio", log_ratio),
            ("initial_joint_mass", initial_joint),
            ("terminal_joint_mass", terminal_joint),
            ("conditional_initial", conditional_initial),
            ("conditional_time", conditional_time),
            ("conditional_terminal", conditional_terminal),
            ("optimal_logistic_risk_per_time", optimal_risk),
        ):
            object.__setattr__(self, name, _immutable_float_array(array))

    @property
    def n_times(self) -> int:
        return int(self.times.size)

    @property
    def n_states(self) -> int:
        return int(self.initial_marginal.size)

    @property
    def n_observations(self) -> int:
        return int(self.observation_reference_mass.size)

    @property
    def optimal_logistic_risk(self) -> float:
        """Uniform-time mean of the exact optimal equal-prior risk."""

        return float(np.mean(self.optimal_logistic_risk_per_time))


def finite_bridge_population(
    oracle: FiniteAtomicAssociationBridgeOracle,
    initial_marginal: object,
    times: Iterable[float],
    terminal_time: object,
) -> FiniteBridgePopulation:
    """Construct exact direct-orientation population tables.

    ``times`` are absolute direct times from the initial law.  For every
    ``t``, the observation is sampled only after propagating from ``X_t`` to
    ``X_T``.  This is intentionally not the reverse/noising orientation in
    which an anchor is sampled from ``X_0``.
    """

    if not isinstance(oracle, FiniteAtomicAssociationBridgeOracle):
        raise TypeError(
            "oracle must be an exact FiniteAtomicAssociationBridgeOracle"
        )
    terminal = _validated_terminal_time(terminal_time)
    direct_times = _validated_times(times, terminal)
    initial = _positive_probability_vector(
        initial_marginal,
        name="initial_marginal",
        size=oracle.latent_space.n_states,
    )
    state_count = oracle.latent_space.n_states
    observation_count = oracle.observation.n_observations
    time_count = direct_times.size
    population_cells = time_count * state_count * observation_count
    if population_cells > _MAX_POPULATION_CELLS:
        raise ValueError(
            "population table exceeds the cell limit of %d"
            % _MAX_POPULATION_CELLS
        )
    multiply_work = time_count * state_count * state_count * observation_count
    if multiply_work > _MAX_DENSE_MULTIPLY_WORK:
        raise ValueError(
            "population construction exceeds the dense-work limit of %d"
            % _MAX_DENSE_MULTIPLY_WORK
        )

    reference = np.asarray(oracle.observation.reference_mass, dtype=np.float64)
    terminal_kernel_mass = np.asarray(
        oracle.observation.kernel_mass, dtype=np.float64
    )
    terminal_kernel_density = np.asarray(
        oracle.observation.density_kernel, dtype=np.float64
    )
    terminal_transition = oracle.forward_transition(terminal)
    terminal_marginal = initial @ terminal_transition
    terminal_joint = terminal_marginal[:, None] * terminal_kernel_mass
    observation_mass = terminal_joint.sum(axis=0)
    observation_density = observation_mass / reference

    time_marginal = np.empty((time_count, state_count), dtype=np.float64)
    backward_mass = np.empty(
        (time_count, state_count, observation_count), dtype=np.float64
    )
    backward_density = np.empty_like(backward_mass)
    for time_index, direct_time in enumerate(direct_times):
        elapsed = float(direct_time)
        remaining = terminal - elapsed
        time_marginal[time_index] = initial @ oracle.forward_transition(elapsed)
        remaining_transition = oracle.forward_transition(remaining)
        backward_mass[time_index] = remaining_transition @ terminal_kernel_mass
        backward_density[time_index] = (
            remaining_transition @ terminal_kernel_density
        )

    joint_mass = time_marginal[:, :, None] * backward_mass
    joint_density = time_marginal[:, :, None] * backward_density
    product_mass = (
        time_marginal[:, :, None] * observation_mass[None, None, :]
    )
    product_density = (
        time_marginal[:, :, None] * observation_density[None, None, :]
    )
    optimal_log_ratio = np.log(joint_mass) - np.log(product_mass)

    initial_information_mass = terminal_transition @ terminal_kernel_mass
    initial_joint = initial[:, None] * initial_information_mass
    conditional_initial = initial_joint / observation_mass[None, :]
    conditional_time = joint_mass / observation_mass[None, None, :]
    conditional_terminal = terminal_joint / observation_mass[None, :]
    optimal_risk = _risk_per_time_from_arrays(
        joint_mass, product_mass, optimal_log_ratio
    )

    return FiniteBridgePopulation(
        times=direct_times,
        terminal_time=terminal,
        initial_marginal=initial,
        time_marginal=time_marginal,
        terminal_marginal=terminal_marginal,
        observation_reference_mass=reference,
        observation_marginal_mass=observation_mass,
        observation_marginal_density=observation_density,
        backward_information_mass=backward_mass,
        backward_information_density=backward_density,
        joint_mass=joint_mass,
        joint_density=joint_density,
        product_mass=product_mass,
        product_density=product_density,
        optimal_log_density_ratio=optimal_log_ratio,
        initial_joint_mass=initial_joint,
        terminal_joint_mass=terminal_joint,
        conditional_initial=conditional_initial,
        conditional_time=conditional_time,
        conditional_terminal=conditional_terminal,
        optimal_logistic_risk_per_time=optimal_risk,
    )


def equal_prior_logistic_risk_per_time(
    population: FiniteBridgePopulation, logits: object
) -> np.ndarray:
    """Return the exact equal-prior logistic risk at every direct time."""

    if not isinstance(population, FiniteBridgePopulation):
        raise TypeError("population must be an exact FiniteBridgePopulation")
    values = _numeric_array(
        logits,
        name="logits",
        shape=population.joint_mass.shape,
    )
    return _immutable_float_array(
        _risk_per_time_from_arrays(
            population.joint_mass, population.product_mass, values
        )
    )


def population_equal_prior_logistic_risk(
    population: FiniteBridgePopulation,
    logits: object,
    time_weights: Optional[object] = None,
) -> float:
    """Return a weighted-time equal-prior population logistic risk.

    The default is a uniform mean over the declared direct times.  Custom
    ``time_weights`` must be a strictly positive probability vector, making the
    time-sampling law explicit rather than silently weighting a nonuniform
    grid by its spacing.
    """

    per_time = equal_prior_logistic_risk_per_time(population, logits)
    if time_weights is None:
        weights = np.full(population.n_times, 1.0 / population.n_times)
    else:
        weights = _positive_probability_vector(
            time_weights,
            name="time_weights",
            size=population.n_times,
        )
    risk = math.fsum(
        float(weight) * float(value) for weight, value in zip(weights, per_time)
    )
    if not math.isfinite(risk) or risk < 0.0:
        raise ArithmeticError("weighted population logistic risk is invalid")
    return risk


__all__ = [
    "FiniteBridgePopulation",
    "equal_prior_logistic_risk_per_time",
    "finite_bridge_population",
    "population_equal_prior_logistic_risk",
]
