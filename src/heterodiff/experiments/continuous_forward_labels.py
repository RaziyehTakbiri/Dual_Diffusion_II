"""Forward-only synthetic labels for a fixed-observation likelihood learner.

No backward oracle, matrix exponential, likelihood integral, score or neural
sampler is imported. Uniformization simulates the complete cap-one CTMC between
the two additive-noise Heun half-steps of each unchanged macro interval.
The terminal observation density is known; its conditional mean is h^Delta.
"""
from dataclasses import dataclass
import math

import numpy as np

GRID = tuple(i/8 for i in range(9))
MAXIMUM_EVENTS_PER_MACRO = 64


@dataclass(frozen=True)
class ForwardSpec:
    theta: float
    observation_value: float
    selected_probability: float = 393217/524288
    death_rate: float = 1.
    continuous_rate: float = 1.
    observation_sd: float = .5
    contamination: float = .1

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('finite scalar specification required')
        if not (0 < self.theta <= 10 and abs(self.observation_value) <= 10
                and 0 < self.selected_probability < 1 and 0 < self.contamination < 1
                and 0 < self.observation_sd <= 10 and 0 <= self.death_rate <= 10
                and 0 <= self.continuous_rate <= 10):
            raise ValueError('specification outside bounded reference submodel')

    @property
    def contamination_density(self):
        return self.contamination*math.exp(-1)*self.selected_probability*math.exp(-self.observation_value**2/2)/math.sqrt(2*math.pi)

    @property
    def maximum_label(self):
        return self.contamination_density+(1-self.contamination)*.5/(self.observation_sd*math.sqrt(2*math.pi))


def validate_states(states, coordinates):
    if np.ma.isMaskedArray(states) or np.ma.isMaskedArray(coordinates):
        raise ValueError('masked states or coordinates are unsupported')
    states, coordinates = np.asarray(states), np.asarray(coordinates)
    if (states.ndim != 1 or states.dtype.kind not in 'iu' or coordinates.shape != states.shape
            or coordinates.dtype.kind not in 'fiu' or np.ma.isMaskedArray(coordinates)
            or not np.isin(states, (0, 1, 2)).all() or not np.isfinite(coordinates).all()):
        raise ValueError('aligned finite E/O/C state and coordinate arrays required')
    if np.any(coordinates[states != 2] != 0):
        raise ValueError('projected atomic coordinates must be zero placeholders')
    with np.errstate(over='ignore', invalid='ignore'):
        coordinate_copy = coordinates.astype(np.float64, copy=True)
    if not np.isfinite(coordinate_copy).all():
        raise ValueError('coordinates must be representable as float64')
    return states.astype(np.int64, copy=True), coordinate_copy


def observation_density(spec, states, coordinates):
    """Raw density of one selected-key noisy half-thinned observation."""
    states, coordinates = validate_states(states, coordinates)
    label = np.full(states.shape, spec.contamination_density)
    active = states == 2
    label[active] += ((1-spec.contamination)*.5/(spec.observation_sd*math.sqrt(2*math.pi))
        *np.exp(-.5*((spec.observation_value-coordinates[active])/spec.observation_sd)**2))
    if not np.isfinite(label).all() or np.any(label <= 0) or np.any(label > spec.maximum_label):
        raise ArithmeticError('nonrepresentable observation density')
    return label


def rollout_labels(spec, u, states, coordinates, rng):
    """One forward suffix per input. Watchdog failure never truncates a path."""
    if type(spec) is not ForwardSpec or type(rng) is not np.random.Generator:
        raise ValueError('explicit specification and NumPy generator required')
    if isinstance(u, bool) or u not in GRID:
        raise ValueError('existing macro node required')
    state, coordinate = validate_states(states, coordinates)
    count = len(state)
    events = potential = half_steps = 0
    rate = spec.death_rate*max(spec.theta, 1.)
    for left, right in zip(GRID[GRID.index(u):-1], GRID[GRID.index(u)+1:]):
        duration = right-left
        clock = spec.continuous_rate*duration/2
        a, variance = 1-clock/2+clock**2/8, clock*(1-clock/4)**2
        active = state == 2
        coordinate[active] = a*coordinate[active]+math.sqrt(variance)*rng.normal(size=int(active.sum()))
        half_steps += int(active.sum())
        if rate:
            proposed = rng.poisson(rate*duration, size=count)
            maximum = int(proposed.max(initial=0))
            if maximum > MAXIMUM_EVENTS_PER_MACRO:
                raise RuntimeError('uniformization event watchdog; no truncated labels returned')
            potential += int(proposed.sum())
            # Conditional on the event count, event times can be omitted: all
            # coordinates are frozen in the middle phase and rates are constant.
            for ordinal in range(maximum):
                indices = np.flatnonzero(proposed > ordinal)
                was_empty = state[indices] == 0
                accepted = rng.random(len(indices)) < np.where(was_empty, spec.theta*spec.death_rate/rate, spec.death_rate/rate)
                selected = indices[accepted]
                births = selected[was_empty[accepted]]
                deaths = selected[~was_empty[accepted]]
                state[deaths], coordinate[deaths] = 0, 0.
                birth_continuous = rng.random(len(births)) < spec.selected_probability
                state[births] = np.where(birth_continuous, 2, 1)
                coordinate[births] = 0.
                c_births = births[birth_continuous]
                coordinate[c_births] = rng.normal(size=len(c_births))
                events += len(selected)
        active = state == 2
        coordinate[active] = a*coordinate[active]+math.sqrt(variance)*rng.normal(size=int(active.sum()))
        half_steps += int(active.sum())
    labels = observation_density(spec, state, coordinate)
    return labels, {'forward_suffix_count': count, 'macro_intervals_per_suffix': 8-GRID.index(u),
        'potential_uniformization_events': potential, 'accepted_birth_death_events': events,
        'continuous_half_step_updates': half_steps,
        'terminal_state_counts': {name: int(np.sum(state == i)) for i, name in enumerate(('EMPTY', 'OTHER', 'CONTINUOUS'))},
        'backward_likelihood_or_score_queried': False, 'conditional_endpoint_sampler_used': False}


def design_states(size, rng):
    """Nested balanced E/O/C/C roster, uniform continuous core coordinates."""
    if type(size) is not int or size <= 0 or size % 4 or type(rng) is not np.random.Generator:
        raise ValueError('positive size divisible by four and explicit RNG required')
    states = np.tile(np.array((0, 1, 2, 2), dtype=np.int64), size//4)
    coordinates = np.zeros(size)
    coordinates[states == 2] = rng.uniform(-4.5, 4.5, size=size//2)
    return states, coordinates


def baseline_rows(spec, u, states, coordinates, method):
    """Known model offsets, not the capped numerical backward target.

G+R is the uncapped retained-ancestor/immigrant association formula; DIR is
the terminal observation likelihood. Neither formula integrates the capped
numerical future. Derivatives are provided for evaluation of the fixed offset.
"""
    if method not in ('association-aware-guide-plus-residual', 'unified-direct-conditioner') or isinstance(u, bool) or u not in GRID:
        raise ValueError('declared baseline and macro node required')
    states, z = validate_states(states, coordinates)
    remaining = 1-u if method == 'association-aware-guide-plus-residual' else 0.
    retained = .5*math.exp(-spec.death_rate*remaining)
    immigrant_mean = .5*spec.theta*(-math.expm1(-spec.death_rate*remaining))
    a = math.exp(-spec.continuous_rate*remaining/2)
    variance = spec.observation_sd**2-math.expm1(-spec.continuous_rate*remaining)
    stationary = math.exp(-spec.observation_value**2/(2*(1+spec.observation_sd**2)))/math.sqrt(2*math.pi*(1+spec.observation_sd**2))
    immigrant = immigrant_mean*spec.selected_probability*stationary
    factor = (1-spec.contamination)*math.exp(-immigrant_mean)
    constant = spec.contamination_density+factor*np.where(states == 0, 1., 1-retained)*immigrant
    result = {'value': np.log(constant), 'gradient': np.zeros(len(z)), 'hessian': np.zeros(len(z))}
    active = states == 2
    signal_log = math.log(factor*retained)-.5*(math.log(2*math.pi*variance)+(spec.observation_value-a*z[active])**2/variance)
    log_h = np.logaddexp(np.log(constant[active]), signal_log)
    responsibility = np.exp(signal_log-log_h)
    slope = a*(spec.observation_value-a*z[active])/variance
    result['value'][active] = log_h
    result['gradient'][active] = responsibility*slope
    result['hessian'][active] = -responsibility*a*a/variance+responsibility*(1-responsibility)*slope*slope
    if not all(np.isfinite(row).all() for row in result.values()):
        raise ArithmeticError('nonrepresentable model offset')
    return result
