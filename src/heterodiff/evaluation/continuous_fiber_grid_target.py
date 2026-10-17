"""Independent backward target of the zero-BASE cap-one numerical path.

This is the ideal real-arithmetic law of a *fixed* common grid: each macro
interval applies additive-noise Heun to the OU drift, runs the complete capped
birth/death CTMC with coordinates frozen, and applies a second Heun half-step.
A birth in the middle phase draws N(0,1), irrespective of its jump time, and
receives only the final Heun step.  This is not the continuous-time OU target.

The projection is EMPTY, OTHER, CONTINUOUS (one selected key).  OTHER can
contain other continuous keys only because the zero BASE, constant rates and
one selected-key observation make their coordinates irrelevant to this law.
Both caps are one.  The initial law is the capped Poisson reference with a
standard-normal C coordinate.  There is no clean hold or extra jump-clock
multiplier.  Queries must be existing grid nodes; query-driven refinement
would change the target.  Nonzero learned BASE/conditional potentials, actual
finite RNG, floating-point paths, resource refusals, and physical samplers
using a log-h potential are NOT certified by this module.

For a half-duration d and continuous rate c, the zero-BASE Heun map is
    x' = A*x + sqrt(V)*Z,
    A = 1-c*d/2+(c*d)**2/8, V = c*d*(1-c*d/4)**2.
Writing L/R for the two halves, an ancestral C survivor has coefficient A_R*A_L
and variance A_R**2*V_L+V_R.  A reset C birth has variance A_R**2+V_R.
An augmented finite CTMC separates the surviving ancestor from reset C births
without subtracting near-equal probabilities.  Backward closure has two atom
constants and h_C(x)=constant+weight*Normal(y; coefficient*x, variance).
Forward closure is a finite mixture over the last reset interval.  Evidence
therefore need not equal the continuous-time stationary-reference evidence.

The only project imports are passive specification/mixture-law dataclasses.
No native guide, sampler, trainer or previously computed target is called.
Matrix exponentials and Gaussian algebra are numerical evaluations, not
certified exact arithmetic.  Unrepresentable arithmetic fails explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
from numbers import Real

import numpy as np
from scipy.linalg import expm

from heterodiff.evaluation.continuous_fiber_conditional_benchmark import (
    ContinuousFiberSpec, GaussianComponent, MixedGaussianLaw,
)


STATES = ('EMPTY', 'OTHER', 'CONTINUOUS')


def _finite(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
        raise ValueError(f'{name} must be a finite real number')
    return float(value)


def _normal_log_density(value, mean, variance):
    if not math.isfinite(variance) or variance <= 0:
        raise ArithmeticError('positive Gaussian variance is not representable')
    return -.5 * (math.log(2 * math.pi) + math.log(variance) + (value - mean) ** 2 / variance)


def _normal_density(value, mean, variance):
    return math.exp(_normal_log_density(value, mean, variance))


def _readonly(values):
    result = np.array(values, dtype=np.float64, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class _Step:
    start: float
    midpoint: float
    end: float
    left_coefficient: float
    left_variance: float
    right_coefficient: float
    right_variance: float
    survivor_coefficient: float
    survivor_variance: float
    reset_variance: float
    survival_probability: float
    reset_probabilities: tuple[float, float, float]
    transition: np.ndarray


@dataclass(frozen=True)
class _Likelihood:
    constants: tuple[float, float, float]
    weight: float
    coefficient: float
    variance: float


class ContinuousFiberGridTarget:
    """Analytic finite-Gaussian target of one explicitly declared numerical grid."""

    states = STATES

    def __init__(self, spec, grid):
        if type(spec) is not ContinuousFiberSpec:
            raise ValueError('spec must be a ContinuousFiberSpec')
        if spec.potential != (0., 0., 0.):
            raise ValueError('this numerical target requires zero BASE potential')
        if type(grid) is not tuple or not 2 <= len(grid) <= 1025:
            raise ValueError('grid must be a tuple with 2 to 1025 nodes')
        grid = tuple(_finite(u, 'grid node') for u in grid)
        if grid[0] != 0. or grid[-1] != spec.horizon or not all(a < b for a, b in zip(grid, grid[1:])):
            raise ValueError('grid must increase strictly from zero to horizon')
        self.spec, self.grid = spec, grid
        theta, delta = spec.theta, spec.death_rate
        rho_o, rho_c = spec.type_probabilities
        prior = (1 / (1 + theta), theta * rho_o / (1 + theta), theta * rho_c / (1 + theta))
        if spec.initial_state_probabilities is not None and not np.allclose(
                spec.initial_state_probabilities, prior, rtol=0., atol=1e-14):
            raise ValueError('initial category law must be the capped reference prior')
        if any(m != 0. for m in spec.initial_fiber_means) or any(v != 1. for v in spec.initial_fiber_variances):
            raise ValueError('initial C coordinate must be standard normal')
        self.initial_state_probabilities = _readonly(prior)
        self.prior = MixedGaussianLaw(prior[0], prior[1], (GaussianComponent(prior[2], 0., 1.),))
        q = np.array([[-theta * delta, theta * delta * rho_o, theta * delta * rho_c],
                      [delta, -delta, 0.], [delta, 0., -delta]], dtype=np.float64)
        self.generator = _readonly(q)
        # The extra state is the still-living original C occurrence.  Its
        # first death enters E; subsequent selected-key births enter reset C.
        memory = np.zeros((4, 4))
        memory[:3, :3] = q
        memory[3, 0], memory[3, 3] = delta, -delta
        self._memory_generator = _readonly(memory)
        self.observation_reference_density = math.exp(-1.) * rho_c * _normal_density(spec.observation_value, 0., 1.)
        self._contamination = spec.contamination * self.observation_reference_density
        self._signal = (1 - spec.contamination) * .5
        if not math.isfinite(self._contamination) or self._contamination <= 0:
            raise ArithmeticError('positive contamination density is not representable')
        self._steps = tuple(self._make_step(start, end) for start, end in zip(grid, grid[1:]))
        backwards = [_Likelihood((self._contamination,) * 3, self._signal, 1., spec.observation_sd ** 2)]
        for step in reversed(self._steps):
            following = backwards[-1]
            reset_average = _normal_density(spec.observation_value, 0.,
                following.variance + following.coefficient ** 2 * step.reset_variance)
            constants = step.transition @ np.asarray(following.constants)
            constants += np.asarray(step.reset_probabilities) * following.weight * reset_average
            weight = following.weight * step.survival_probability
            coefficient = following.coefficient * step.survivor_coefficient
            variance = following.variance + following.coefficient ** 2 * step.survivor_variance
            if (not np.all(np.isfinite(constants)) or np.min(constants) <= 0
                    or not math.isfinite(weight) or weight <= 0
                    or not math.isfinite(coefficient) or not math.isfinite(variance) or variance <= 0):
                raise ArithmeticError('backward Gaussian target is not representable')
            backwards.append(_Likelihood(tuple(float(x) for x in constants), weight, coefficient, variance))
        self._likelihoods = tuple(reversed(backwards))

    def _make_step(self, start, end):
        midpoint = start + (end - start) / 2
        if not start < midpoint < end:
            raise ValueError('grid midpoint is not representable')

        def half(duration):
            clock = self.spec.continuous_rate * duration
            coefficient = 1 - clock / 2 + clock ** 2 / 8
            variance = clock * (1 - clock / 4) ** 2
            if not math.isfinite(coefficient) or not math.isfinite(variance):
                raise ArithmeticError('Heun half-step is not representable')
            return coefficient, variance

        left_a, left_v = half(midpoint - start)
        right_a, right_v = half(end - midpoint)
        transition = expm((end - start) * self.generator)
        memory = expm((end - start) * self._memory_generator)
        if (not np.all(np.isfinite(transition)) or np.min(transition) < 0
                or not np.allclose(transition.sum(axis=1), 1., rtol=0., atol=2e-12)
                or not np.all(np.isfinite(memory)) or np.min(memory) < 0):
            raise ArithmeticError('finite-state transition is not stochastic')
        survival = math.exp(-self.spec.death_rate * (end - start))
        reset = (float(transition[0, 2]), float(transition[1, 2]), float(memory[3, 2]))
        if not math.isclose(reset[2] + survival, transition[2, 2], rel_tol=0., abs_tol=2e-12):
            raise ArithmeticError('ancestry transition does not match category transition')
        return _Step(start, midpoint, end, left_a, left_v, right_a, right_v,
                     right_a * left_a, right_a ** 2 * left_v + right_v,
                     right_a ** 2 + right_v, survival, reset, _readonly(transition))

    def _node(self, time):
        time = _finite(time, 'time')
        try:
            return self.grid.index(time)
        except ValueError as exc:
            raise ValueError('time must be an existing common-grid node; no interpolation or refinement') from exc

    def _step(self, time):
        index = self._node(time)
        if index == len(self._steps):
            raise ValueError('terminal grid node has no outgoing step')
        return self._steps[index]

    @staticmethod
    def _state(state, coordinate):
        if state not in STATES:
            raise ValueError('unknown projected state')
        if state == 'CONTINUOUS':
            return 2, _finite(coordinate, 'continuous coordinate')
        if coordinate is not None:
            raise ValueError('EMPTY/OTHER projected states require coordinate=None')
        return STATES.index(state), None

    def log_likelihood_derivatives(self, time, state, coordinate=None):
        """Absolute-density log h, score, and coordinate Hessian at a grid node.

        Dividing h by observation_reference_density gives the native RN
        convention, without changing the score, Hessian, or normalized law.
        """
        row = self._likelihoods[self._node(time)]
        index, coordinate = self._state(state, coordinate)
        if index != 2:
            return {'log_likelihood': math.log(row.constants[index]), 'gradient': 0., 'hessian': 0.}
        log_signal = math.log(row.weight) + _normal_log_density(
            self.spec.observation_value, row.coefficient * coordinate, row.variance)
        log_h = float(np.logaddexp(math.log(row.constants[2]), log_signal))
        responsibility = math.exp(log_signal - log_h)
        slope = row.coefficient * (self.spec.observation_value - row.coefficient * coordinate) / row.variance
        result = {'log_likelihood': log_h, 'gradient': responsibility * slope,
                  'hessian': -responsibility * row.coefficient ** 2 / row.variance
                  + responsibility * (1 - responsibility) * slope ** 2}
        if not all(math.isfinite(x) for x in result.values()):
            raise ArithmeticError('likelihood derivatives are not representable')
        return result

    def backward_likelihood(self, time, state, coordinate=None):
        return math.exp(self.log_likelihood_derivatives(time, state, coordinate)['log_likelihood'])

    def evidence(self):
        row = self._likelihoods[0]
        result = float(self.initial_state_probabilities @ np.asarray(row.constants))
        result += self.initial_state_probabilities[2] * row.weight * _normal_density(
            self.spec.observation_value, 0., row.variance + row.coefficient ** 2)
        if not math.isfinite(result) or result <= 0:
            raise ArithmeticError('evidence is not representable')
        return float(result)

    @lru_cache(maxsize=16, typed=True)
    def marginal(self, time):
        """Unconditional numerical-grid marginal; C weights are joint masses."""
        node = self._node(time)
        law = self.prior
        for step in self._steps[:node]:
            masses = np.asarray(law.state_probabilities)
            next_mass = masses @ step.transition
            reset_mass = float(masses @ np.asarray(step.reset_probabilities))
            components = [GaussianComponent(reset_mass, 0., step.reset_variance)]
            components.extend(GaussianComponent(c.weight * step.survival_probability,
                step.survivor_coefficient * c.mean,
                step.survivor_coefficient ** 2 * c.variance + step.survivor_variance)
                for c in law.components)
            law = MixedGaussianLaw(float(next_mass[0]), float(next_mass[1]), tuple(components))
        return law

    @staticmethod
    def _normalize(empty, other, components, evidence):
        return MixedGaussianLaw(empty / evidence, other / evidence,
            tuple(GaussianComponent(c.weight / evidence, c.mean, c.variance) for c in components))

    def conditioned_initial(self):
        row = self._likelihoods[0]
        combined_variance = row.variance + row.coefficient ** 2
        signal_mass = self.initial_state_probabilities[2] * row.weight * _normal_density(
            self.spec.observation_value, 0., combined_variance)
        components = (
            GaussianComponent(self.initial_state_probabilities[2] * row.constants[2], 0., 1.),
            GaussianComponent(signal_mass, row.coefficient * self.spec.observation_value / combined_variance,
                              row.variance / combined_variance),
        )
        return self._normalize(self.initial_state_probabilities[0] * row.constants[0],
                               self.initial_state_probabilities[1] * row.constants[1], components, self.evidence())

    def terminal_posterior(self):
        terminal = self.marginal(self.spec.horizon)
        noise = self.spec.observation_sd ** 2
        components = []
        for component in terminal.components:
            components.append(GaussianComponent(component.weight * self._contamination,
                                                component.mean, component.variance))
            combined = component.variance + noise
            signal_mass = component.weight * self._signal * _normal_density(
                self.spec.observation_value, component.mean, combined)
            components.append(GaussianComponent(signal_mass,
                component.mean + component.variance / combined * (self.spec.observation_value - component.mean),
                component.variance * noise / combined))
        return self._normalize(terminal.empty_probability * self._contamination,
                               terminal.other_probability * self._contamination, components, self.evidence())

    def step_parameters(self, time):
        """Expose analytic macro-kernel coefficients for independent diagnostics."""
        step = self._step(time)
        return {name: getattr(step, name) for name in (
            'start', 'midpoint', 'end', 'left_coefficient', 'left_variance',
            'right_coefficient', 'right_variance', 'survivor_coefficient',
            'survivor_variance', 'reset_variance', 'survival_probability',
            'reset_probabilities')}

    def step_transition(self, time):
        """Category transition of the single outgoing macro step, in E/O/C order."""
        return self._step(time).transition

    def step_continuous_density(self, time, state, coordinate, target_coordinate):
        """Joint next-node C density; refuses a surviving-coordinate point mass."""
        step = self._step(time)
        index, coordinate = self._state(state, coordinate)
        target_coordinate = _finite(target_coordinate, 'target coordinate')
        reset = step.reset_probabilities[index] * _normal_density(target_coordinate, 0., step.reset_variance)
        if index != 2:
            return reset
        if step.survivor_variance == 0:
            raise ValueError('surviving C transition contains a point mass, not an ordinary density')
        return reset + step.survival_probability * _normal_density(
            target_coordinate, step.survivor_coefficient * coordinate, step.survivor_variance)


# Short public name for stand-alone diagnostic scripts.
GridTarget = ContinuousFiberGridTarget
