"""Independent N=1 capped jump/OU conditional-law oracle.

The carrier is EMPTY, one occurrence of a selected continuous key, or OTHER.
OTHER can aggregate any other atomic or continuous keys if exit rates and rate
tilts depend only on this category.  Its coordinates cannot be recovered from
this projected law.  A continuous birth has a standard normal coordinate.

The observed datum is exactly one selected-key occurrence with value y.  Clean
observations retain occurrences with probability 1/2 and add N(0, sigma^2)
coordinate noise.  Whole-observation contamination instead draws a unit-rate
Poisson reference observation, whose selected-key coordinate is N(0,1), WITHOUT
adding sigma noise.  Both state and observation caps are one (the latter has a
separate overflow atom, not the selected observed outcome).

All endpoint/initializer laws below are finite Gaussian mixtures.  Finite
matrix exponentials and floating-point Gaussian algebra are independent of the
project's learned guide and Heun implementation.  They are numerical evaluations
of an exact submodel, not exact-arithmetic or full-hybrid qualification claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
from numbers import Real

import numpy as np
from scipy.linalg import expm
from scipy.special import ndtr


STATES = ('EMPTY', 'OTHER', 'CONTINUOUS')


def _finite(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
        raise ValueError(f'{name} must be a finite real number')
    return float(value)


def _probabilities(values, length, name):
    if type(values) is not tuple or len(values) != length:
        raise ValueError(f'{name} must be a tuple of length {length}')
    result = tuple(_finite(v, name) for v in values)
    if min(result) < 0 or not math.isclose(sum(result), 1., rel_tol=0., abs_tol=1e-13):
        raise ValueError(f'{name} must be nonnegative and sum to one')
    return result


def _normal_log_density(value, mean, variance):
    return -.5 * (math.log(2. * math.pi) + math.log(variance) + (value - mean) ** 2 / variance)


def _normal_density(value, mean, variance):
    return math.exp(_normal_log_density(value, mean, variance))


def _readonly(values):
    result = np.array(values, dtype=np.float64, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class GaussianComponent:
    """Weight is joint CONTINUOUS-category mass, not conditionally normalized."""

    weight: float
    mean: float
    variance: float

    def __post_init__(self):
        for name in ('weight', 'mean', 'variance'):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if self.weight < 0 or self.variance <= 0:
            raise ValueError('Gaussian components require nonnegative weight and positive variance')


@dataclass(frozen=True)
class MixedGaussianLaw:
    """Normalized projected law with two atoms and a Gaussian-mixture fiber."""

    empty_probability: float
    other_probability: float
    components: tuple[GaussianComponent, ...]

    def __post_init__(self):
        for name in ('empty_probability', 'other_probability'):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if min(self.empty_probability, self.other_probability) < 0:
            raise ValueError('atom probabilities must be nonnegative')
        if type(self.components) is not tuple or any(type(c) is not GaussianComponent for c in self.components):
            raise ValueError('components must be a tuple of GaussianComponent values')
        if not math.isclose(sum(self.state_probabilities), 1., rel_tol=0., abs_tol=2e-12):
            raise ValueError('mixed law must have total mass one')

    @property
    def state_probabilities(self):
        return (self.empty_probability, self.other_probability, math.fsum(c.weight for c in self.components))

    def continuous_density(self, coordinate):
        """Joint density P(category=C, coordinate in dx)/dx."""
        coordinate = _finite(coordinate, 'coordinate')
        return math.fsum(c.weight * _normal_density(coordinate, c.mean, c.variance) for c in self.components)

    def continuous_cdf(self, coordinate):
        """Joint C-category sub-CDF, tending to P(C), not one."""
        coordinate = _finite(coordinate, 'coordinate')
        return math.fsum(c.weight * float(ndtr((coordinate - c.mean) / math.sqrt(c.variance)))
                         for c in self.components)

    def continuous_moments(self):
        """Return coordinate (mean, variance) conditional on category C."""
        mass = self.state_probabilities[2]
        if mass <= 0:
            raise ValueError('continuous moments are undefined at zero C mass')
        mean = math.fsum(c.weight * c.mean for c in self.components) / mass
        variance = math.fsum(c.weight * (c.variance + (c.mean - mean) ** 2) for c in self.components) / mass
        return mean, variance

    def sample(self, rng):
        """Finite-RNG sample of this projected law, returning (category, value)."""
        if type(rng) is not np.random.Generator:
            raise ValueError('an explicit numpy.random.Generator is required')
        weights = np.array([self.empty_probability, self.other_probability,
                            *(c.weight for c in self.components)], dtype=np.float64)
        # Resolve at most floating-point normalization error in mixture weights.
        index = int(rng.choice(len(weights), p=weights / weights.sum()))
        if index < 2:
            return STATES[index], None
        component = self.components[index - 2]
        return 'CONTINUOUS', float(rng.normal(component.mean, math.sqrt(component.variance)))

    def to_dict(self):
        return {'state_probabilities': dict(zip(STATES, self.state_probabilities)),
                'continuous_components': [dict(weight=c.weight, mean=c.mean, variance=c.variance)
                                          for c in self.components],
                'continuous_density_is_joint_not_conditional': True,
                'other_coordinates_not_represented': True}


@dataclass(frozen=True)
class ContinuousFiberSpec:
    theta: float = .8
    type_probabilities: tuple[float, float] = (.25, .75)  # OTHER, selected C
    death_rate: float = 1.
    continuous_rate: float = 1.
    horizon: float = 1.
    observation_sd: float = .5
    contamination: float = .1
    observation_value: float = .7
    potential: tuple[float, float, float] = (0., 0., 0.)
    initial_state_probabilities: tuple[float, float, float] | None = None
    initial_fiber_weights: tuple[float, ...] = (1.,)
    initial_fiber_means: tuple[float, ...] = (0.,)
    initial_fiber_variances: tuple[float, ...] = (1.,)

    def __post_init__(self):
        for name in ('theta', 'horizon', 'observation_sd'):
            value = _finite(getattr(self, name), name)
            if not 0 < value <= 10:
                raise ValueError(f'{name} must lie in (0,10]')
            object.__setattr__(self, name, value)
        for name in ('death_rate', 'continuous_rate'):
            value = _finite(getattr(self, name), name)
            if not 0 <= value <= 10:
                raise ValueError(f'{name} must lie in [0,10]')
            object.__setattr__(self, name, value)
        if not math.isfinite(self.observation_sd ** 2) or self.observation_sd ** 2 <= 0:
            raise ValueError('observation variance is not representable')
        rho = _probabilities(self.type_probabilities, 2, 'type_probabilities')
        if min(rho) <= 0:
            raise ValueError('both type probabilities must be positive')
        object.__setattr__(self, 'type_probabilities', rho)
        epsilon = _finite(self.contamination, 'contamination')
        if not 0 < epsilon < 1:
            raise ValueError('contamination must lie strictly between zero and one')
        object.__setattr__(self, 'contamination', epsilon)
        object.__setattr__(self, 'observation_value', _finite(self.observation_value, 'observation_value'))
        if abs(self.observation_value) > 10:
            raise ValueError('bounded benchmark observation must have absolute value <= 10')
        if type(self.potential) is not tuple or len(self.potential) != 3:
            raise ValueError('potential must have one value for each of the three states')
        potential = tuple(_finite(v, 'potential') for v in self.potential)
        if max(abs(v) for v in potential) > 4:
            raise ValueError('bounded benchmark potentials must have absolute value <= 4')
        object.__setattr__(self, 'potential', potential)
        if self.initial_state_probabilities is not None:
            object.__setattr__(self, 'initial_state_probabilities',
                               _probabilities(self.initial_state_probabilities, 3, 'initial_state_probabilities'))
        count = len(self.initial_fiber_weights) if type(self.initial_fiber_weights) is tuple else 0
        if not 1 <= count <= 8:
            raise ValueError('between one and eight initial Gaussian components are required')
        object.__setattr__(self, 'initial_fiber_weights',
                           _probabilities(self.initial_fiber_weights, count, 'initial_fiber_weights'))
        for name in ('initial_fiber_means', 'initial_fiber_variances'):
            values = getattr(self, name)
            if type(values) is not tuple or len(values) != count:
                raise ValueError('initial fiber arrays must have the same length')
            values = tuple(_finite(v, name) for v in values)
            if name.endswith('variances') and min(values) <= 0:
                raise ValueError('initial Gaussian variances must be positive')
            object.__setattr__(self, name, values)


class ContinuousFiberConditionalBenchmark:
    states = STATES

    def __init__(self, spec=None):
        self.spec = ContinuousFiberSpec() if spec is None else spec
        if type(self.spec) is not ContinuousFiberSpec:
            raise ValueError('spec must be a ContinuousFiberSpec')
        p = self.spec
        default = (1. / (1. + p.theta), p.theta * p.type_probabilities[0] / (1. + p.theta),
                   p.theta * p.type_probabilities[1] / (1. + p.theta))
        self.reference_state_prior = _readonly(default)
        self.initial_state_probabilities = _readonly(default if p.initial_state_probabilities is None
                                                     else p.initial_state_probabilities)
        self.prior = MixedGaussianLaw(*self.initial_state_probabilities[:2], tuple(
            GaussianComponent(self.initial_state_probabilities[2] * weight, mean, variance)
            for weight, mean, variance in zip(p.initial_fiber_weights, p.initial_fiber_means, p.initial_fiber_variances)
        ))
        q = np.zeros((3, 3))
        for state in (1, 2):
            q[0, state] = p.theta * p.death_rate * p.type_probabilities[state - 1] * math.exp(p.potential[state] - p.potential[0])
            q[state, 0] = p.death_rate * math.exp(p.potential[0] - p.potential[state])
        np.fill_diagonal(q, -q.sum(axis=1))
        self.generator = _readonly(q)
        # State 3 means the initial C occurrence is still alive; its death
        # enters EMPTY, and any later C birth enters reset state 2.  This avoids
        # subtracting nearly equal P_CC and survival probabilities numerically.
        memory = np.zeros((4, 4))
        memory[:3, :3] = q
        memory[3, 0], memory[3, 3] = q[2, 0], -q[2, 0]
        self.memory_generator = _readonly(memory)
        self.observation_reference_density = math.exp(-1.) * p.type_probabilities[1] * _normal_density(p.observation_value, 0., 1.)
        self._contamination_density = p.contamination * self.observation_reference_density
        self._signal_weight = (1. - p.contamination) * .5

    def _time(self, time):
        time = _finite(time, 'time')
        if not 0 <= time <= self.spec.horizon:
            raise ValueError('time must lie in [0,horizon]')
        return time

    @staticmethod
    def _state(state, coordinate):
        if state not in STATES:
            raise ValueError('unknown projected state')
        if state == 'CONTINUOUS':
            return 2, _finite(coordinate, 'continuous coordinate')
        if coordinate is not None:
            raise ValueError('EMPTY/OTHER projected states must have coordinate=None')
        return STATES.index(state), None

    @lru_cache(maxsize=128, typed=True)
    def transition(self, duration):
        duration = self._time(duration)
        result = expm(duration * self.generator)
        if np.min(result) < 0 or not np.allclose(result.sum(axis=1), 1., rtol=0., atol=2e-12):
            raise ArithmeticError('finite-state transition is not stochastic')
        return _readonly(result)

    @lru_cache(maxsize=128, typed=True)
    def _memory_transition(self, duration):
        return _readonly(expm(self._time(duration) * self.memory_generator))

    def _ou(self, duration):
        clock = self.spec.continuous_rate * duration
        return math.exp(-clock / 2.), -math.expm1(-clock)

    def marginal(self, time):
        time = self._time(time)
        transition = self.transition(time)
        state_mass = self.initial_state_probabilities @ transition
        contraction, variance = self._ou(time)
        survival = math.exp(-self.generator[2, 0] * time)
        reset_mass = (self.initial_state_probabilities[0] * transition[0, 2]
                      + self.initial_state_probabilities[1] * transition[1, 2]
                      + self.initial_state_probabilities[2] * self._memory_transition(time)[3, 2])
        components = [GaussianComponent(reset_mass, 0., 1.)]
        components.extend(GaussianComponent(c.weight * survival, contraction * c.mean,
                                            contraction ** 2 * c.variance + variance) for c in self.prior.components)
        return MixedGaussianLaw(state_mass[0], state_mass[1], tuple(components))

    def observation_likelihood(self, state, coordinate=None):
        index, coordinate = self._state(state, coordinate)
        if index != 2:
            return self._contamination_density
        return self._contamination_density + self._signal_weight * _normal_density(
            self.spec.observation_value, coordinate, self.spec.observation_sd ** 2)

    def _likelihood_parts(self, time, index):
        remaining = self.spec.horizon - self._time(time)
        contraction, ou_variance = self._ou(remaining)
        observed_stationary = _normal_density(self.spec.observation_value, 0., 1. + self.spec.observation_sd ** 2)
        if index == 2:
            reset = self._memory_transition(remaining)[3, 2]
            constant = self._contamination_density + self._signal_weight * reset * observed_stationary
            signal = self._signal_weight * math.exp(-self.generator[2, 0] * remaining)
            if signal <= 0:
                raise ArithmeticError('surviving-coordinate likelihood weight is not representable')
            return constant, signal, contraction, ou_variance + self.spec.observation_sd ** 2
        constant = self._contamination_density + self._signal_weight * self.transition(remaining)[index, 2] * observed_stationary
        return constant, 0., contraction, ou_variance + self.spec.observation_sd ** 2

    def log_likelihood_derivatives(self, time, state, coordinate=None):
        """Analytic log(h) and first/second coordinate derivatives.

        h is the ABSOLUTE observation density.  Divide h by
        observation_reference_density for the project's RN convention; this
        observation-only factor does not change coordinate derivatives.
        """
        index, coordinate = self._state(state, coordinate)
        constant, signal, contraction, variance = self._likelihood_parts(time, index)
        if index != 2:
            return {'log_likelihood': math.log(constant), 'gradient': 0., 'hessian': 0.}
        log_signal = math.log(signal) + _normal_log_density(self.spec.observation_value, contraction * coordinate, variance)
        log_h = float(np.logaddexp(math.log(constant), log_signal))
        responsibility = math.exp(log_signal - log_h)
        first = contraction * (self.spec.observation_value - contraction * coordinate) / variance
        second = -contraction ** 2 / variance
        return {'log_likelihood': log_h,
                'gradient': responsibility * first,
                'hessian': responsibility * second + responsibility * (1. - responsibility) * first ** 2}

    def backward_likelihood(self, time, state, coordinate=None):
        return math.exp(self.log_likelihood_derivatives(time, state, coordinate)['log_likelihood'])

    def evidence(self):
        terminal = self.marginal(self.spec.horizon)
        return self._contamination_density + self._signal_weight * math.fsum(
            c.weight * _normal_density(self.spec.observation_value, c.mean, c.variance + self.spec.observation_sd ** 2)
            for c in terminal.components)

    @staticmethod
    def _normalize(empty, other, components, normalizer):
        return MixedGaussianLaw(empty / normalizer, other / normalizer,
                                tuple(GaussianComponent(c.weight / normalizer, c.mean, c.variance) for c in components))

    def terminal_posterior(self):
        terminal = self.marginal(self.spec.horizon)
        components = []
        noise = self.spec.observation_sd ** 2
        for c in terminal.components:
            components.append(GaussianComponent(c.weight * self._contamination_density, c.mean, c.variance))
            likelihood = _normal_density(self.spec.observation_value, c.mean, c.variance + noise)
            mean = c.mean + c.variance / (c.variance + noise) * (self.spec.observation_value - c.mean)
            variance = c.variance * noise / (c.variance + noise)
            components.append(GaussianComponent(c.weight * self._signal_weight * likelihood, mean, variance))
        return self._normalize(terminal.empty_probability * self._contamination_density,
                               terminal.other_probability * self._contamination_density, components, self.evidence())

    def conditioned_initial(self):
        constant, signal, contraction, noise = self._likelihood_parts(0., 2)
        components = []
        for c in self.prior.components:
            components.append(GaussianComponent(c.weight * constant, c.mean, c.variance))
            observed_variance = contraction ** 2 * c.variance + noise
            likelihood = _normal_density(self.spec.observation_value, contraction * c.mean, observed_variance)
            mean = c.mean + c.variance * contraction / observed_variance * (self.spec.observation_value - contraction * c.mean)
            variance = c.variance * noise / observed_variance
            components.append(GaussianComponent(c.weight * signal * likelihood, mean, variance))
        return self._normalize(self.prior.empty_probability * self.backward_likelihood(0., 'EMPTY'),
                               self.prior.other_probability * self.backward_likelihood(0., 'OTHER'), components, self.evidence())

    def transition_continuous_density(self, duration, state, coordinate, target_coordinate):
        """Joint transition density into C; duration must be positive."""
        duration = self._time(duration)
        index, coordinate = self._state(state, coordinate)
        target_coordinate = _finite(target_coordinate, 'target coordinate')
        if duration <= 0:
            raise ValueError('a positive duration is required for a transition density')
        if index != 2:
            return float(self.transition(duration)[index, 2]) * _normal_density(target_coordinate, 0., 1.)
        contraction, variance = self._ou(duration)
        if variance <= 0:
            raise ValueError('zero-rate C transition has a point mass, not an ordinary density')
        return (math.exp(-self.generator[2, 0] * duration) * _normal_density(target_coordinate, contraction * coordinate, variance)
                + self._memory_transition(duration)[3, 2] * _normal_density(target_coordinate, 0., 1.))

    def doob_continuous_density(self, start, end, state, coordinate, target_coordinate):
        start, end = self._time(start), self._time(end)
        if end <= start:
            raise ValueError('end must exceed start')
        return (self.transition_continuous_density(end - start, state, coordinate, target_coordinate)
                * self.backward_likelihood(end, 'CONTINUOUS', target_coordinate)
                / self.backward_likelihood(start, state, coordinate))

    def doob_atom_probability(self, start, end, state, coordinate, target_state):
        start, end = self._time(start), self._time(end)
        if end <= start or target_state not in ('EMPTY', 'OTHER'):
            raise ValueError('ordered times and an EMPTY/OTHER target are required')
        index, coordinate = self._state(state, coordinate)
        return (float(self.transition(end - start)[index, STATES.index(target_state)])
                * self.backward_likelihood(end, target_state)
                / self.backward_likelihood(start, state, coordinate))
