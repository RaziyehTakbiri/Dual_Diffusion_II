"""Forward-only paired raw and Rao--Blackwell cap-one observation labels.

The category jump skeleton uses one RNG, while all Gaussian coordinates use a
second RNG. Conditional on that skeleton, means and variances are propagated
through the *numerical* Heun halves and reset at births. This integrates no
category paths and imports no backward target, association guide, or learner.
Separate Generator objects are required; callers remain responsible for their
independent random streams. The raw route retains a normal draw per active
Heun half, including a zero-variance half, as in the original forward simulator.
"""

import math

import numpy as np

from heterodiff.experiments.continuous_forward_labels import (
    GRID, MAXIMUM_EVENTS_PER_MACRO, ForwardSpec, observation_density,
    validate_states,
)


def conditional_observation_moments(spec, states, means, variances):
    """Return E[label | skeleton] and Var(label | skeleton), row by row.

For a selected coordinate Z~N(m,v), the signal is alpha*phi_sigma(y-Z),
alpha=(1-epsilon)/2. Its second moment is
phi_sqrt(v+sigma^2/2)(y-m)/(2*sqrt(pi)*sigma). The variance is evaluated
without subtracting close moments; deterministic v=0 yields exact zero.
This is Gaussian integration of the known terminal observation only.
"""
    if type(spec) is not ForwardSpec:
        raise ValueError('explicit ForwardSpec required')
    state, mean = validate_states(states, means)
    if np.ma.isMaskedArray(variances):
        raise ValueError('finite nonnegative aligned variances required')
    variance = np.asarray(variances)
    if (variance.shape != state.shape or variance.dtype.kind not in 'fiu'
            or not np.isfinite(variance).all() or np.any(variance < 0)
            or np.any(variance[state != 2] != 0)):
        raise ValueError('finite nonnegative aligned variances required')
    with np.errstate(over='ignore', invalid='ignore'):
        variance = variance.astype(np.float64, copy=True)
    sigma2 = spec.observation_sd**2
    floor, ceiling = spec.contamination_density, spec.maximum_label
    if (not np.isfinite(variance).all() or not math.isfinite(sigma2)
            or sigma2 <= 0 or not 0 < floor <= ceiling < math.inf):
        raise ArithmeticError('nonrepresentable Gaussian observation moments')
    # Reuse the exact raw formula for zero-variance rows, including the terminal
    # node. Avoiding an alternative sqrt(sigma^2) route preserves exact equality.
    expected = observation_density(spec, state, mean)
    conditional_variance = np.zeros(len(state), dtype=np.float64)
    active = (state == 2) & (variance > 0)
    if np.any(active):
        v, delta = variance[active], spec.observation_value-mean[active]
        total = sigma2+v
        double = sigma2+2*v
        if not np.isfinite(total).all() or not np.isfinite(double).all():
            raise ArithmeticError('nonrepresentable Gaussian observation moments')
        # Squared standardized differences may overflow for finite extreme
        # coordinates; the corresponding Gaussian density is then exactly zero
        # in float64. This is not a clipping of a negative computed variance.
        with np.errstate(over='ignore', under='ignore', invalid='ignore'):
            standardized2 = (delta/np.sqrt(total))**2
            density = np.exp(-.5*standardized2)/np.sqrt(2*math.pi*total)
            log_ratio = (.5*np.log1p((v/sigma2)*(v/double))
                         + standardized2*(v/double))
            log_second = (-math.log(2*math.sqrt(math.pi)*spec.observation_sd)
                          -.5*np.log(2*math.pi*(v+sigma2/2))
                          -.5*(delta/np.sqrt(v+sigma2/2))**2)
            signal_variance = np.exp(log_second)*(-np.expm1(-log_ratio))
        alpha = (1-spec.contamination)*.5
        expected[active] = floor+alpha*density
        conditional_variance[active] = alpha**2*signal_variance
    if (not np.isfinite(expected).all() or np.any(expected < floor)
            or np.any(expected > ceiling)
            or not np.isfinite(conditional_variance).all()
            or np.any(conditional_variance < 0)):
        raise ArithmeticError('nonrepresentable Gaussian observation moments')
    return expected, conditional_variance


def paired_rollout_labels(spec, u, states, coordinates, skeleton_rng, noise_rng):
    """Simulate paired labels; any watchdog failure refuses the whole call.

The shared skeleton contains uniformization proposals, acceptances and birth
categories. Gaussian draws are conditionally independent of it. Counters are
returned both as totals and per-suffix integer lists for exact prefix budgets.
Neither the event cap nor any numerical failure returns truncated labels.
"""
    if (type(spec) is not ForwardSpec
            or type(skeleton_rng) is not np.random.Generator
            or type(noise_rng) is not np.random.Generator
            or skeleton_rng is noise_rng):
        raise ValueError('explicit specification and distinct NumPy generators required')
    if (isinstance(u, (bool, np.bool_))
            or not isinstance(u, (int, float, np.integer, np.floating)) or u not in GRID):
        raise ValueError('existing macro node required')
    state, coordinate = validate_states(states, coordinates)
    mean, variance = coordinate.copy(), np.zeros(len(state), dtype=np.float64)
    names = ('potential_uniformization_events', 'accepted_birth_death_events',
             'accepted_births', 'accepted_deaths', 'selected_births',
             'continuous_half_step_updates', 'conditional_gaussian_affine_updates',
             'raw_half_step_normal_draws', 'raw_birth_normal_draws',
             'skeleton_acceptance_uniform_draws', 'skeleton_birth_uniform_draws',
             'skeleton_poisson_draws', 'conditional_gaussian_birth_resets',
             'conditional_gaussian_death_resets')
    counts = {name: np.zeros(len(state), dtype=np.int64) for name in names}

    def half_step(a, noise_variance):
        active = np.flatnonzero(state == 2)
        coordinate[active] = (a*coordinate[active]
                              + math.sqrt(noise_variance)*noise_rng.normal(size=len(active)))
        mean[active] *= a
        variance[active] = a*a*variance[active]+noise_variance
        for name in ('continuous_half_step_updates', 'conditional_gaussian_affine_updates',
                     'raw_half_step_normal_draws'):
            counts[name][active] += 1

    rate = spec.death_rate*max(spec.theta, 1.)
    start = GRID.index(u)
    for left, right in zip(GRID[start:-1], GRID[start+1:]):
        duration = right-left
        clock = spec.continuous_rate*duration/2
        a, noise_variance = 1-clock/2+clock**2/8, clock*(1-clock/4)**2
        half_step(a, noise_variance)
        if rate:
            proposed = skeleton_rng.poisson(rate*duration, size=len(state))
            maximum = int(proposed.max(initial=0))
            if maximum > MAXIMUM_EVENTS_PER_MACRO:
                raise RuntimeError('uniformization event watchdog; no truncated labels returned')
            counts['skeleton_poisson_draws'] += 1
            counts['potential_uniformization_events'] += proposed
            # Frozen coordinates and constant zero-BASE rates make the proposal
            # count and ordered acceptances sufficient; event times are unused.
            for ordinal in range(maximum):
                indices = np.flatnonzero(proposed > ordinal)
                was_empty = state[indices] == 0
                accepted = skeleton_rng.random(len(indices)) < np.where(
                    was_empty, spec.theta*spec.death_rate/rate, spec.death_rate/rate)
                counts['skeleton_acceptance_uniform_draws'][indices] += 1
                selected = indices[accepted]
                births = selected[was_empty[accepted]]
                deaths = selected[~was_empty[accepted]]
                state[deaths] = 0
                coordinate[deaths], mean[deaths], variance[deaths] = 0., 0., 0.
                birth_continuous = skeleton_rng.random(len(births)) < spec.selected_probability
                state[births] = np.where(birth_continuous, 2, 1)
                coordinate[births], mean[births], variance[births] = 0., 0., 0.
                c_births = births[birth_continuous]
                coordinate[c_births] = noise_rng.normal(size=len(c_births))
                variance[c_births] = 1.
                counts['accepted_birth_death_events'][selected] += 1
                counts['accepted_births'][births] += 1
                counts['accepted_deaths'][deaths] += 1
                counts['selected_births'][c_births] += 1
                counts['raw_birth_normal_draws'][c_births] += 1
                counts['skeleton_birth_uniform_draws'][births] += 1
                counts['conditional_gaussian_birth_resets'][c_births] += 1
                counts['conditional_gaussian_death_resets'][deaths] += 1
        half_step(a, noise_variance)
    raw = observation_density(spec, state, coordinate)
    rb, conditional_variance = conditional_observation_moments(spec, state, mean, variance)
    counts['raw_normal_draws_total'] = (counts['raw_half_step_normal_draws']
                                       + counts['raw_birth_normal_draws'])
    # Row-evaluation counters include assigned constant E/O values. The moment
    # helper initializes its output using the raw-density formula, even for C
    # rows whose positive-variance convolution later replaces that value.
    for name in ('raw_observation_density_evaluations', 'rb_observation_mean_evaluations',
                 'conditional_variance_evaluations', 'rb_initial_raw_formula_evaluations'):
        counts[name] = np.ones(len(state), dtype=np.int64)
    convoluted = ((state == 2) & (variance > 0)).astype(np.int64)
    counts['rb_gaussian_convolution_evaluations'] = convoluted
    counts['conditional_gaussian_second_moment_evaluations'] = convoluted.copy()
    work = {name: int(value.sum()) for name, value in counts.items()}
    work.update({
        'forward_suffix_count': len(state),
        'macro_intervals_per_suffix': len(GRID)-1-start,
        'terminal_state_counts': {name: int(np.sum(state == i))
                                 for i, name in enumerate(('EMPTY', 'OTHER', 'CONTINUOUS'))},
        'per_suffix_counts': {name: value.tolist() for name, value in counts.items()},
        'conditional_raw_label_variance': conditional_variance.tolist(),
        'terminal_gaussian_state': {'states': state.tolist(), 'means': mean.tolist(),
                                   'variances': variance.tolist(),
                                   'raw_coordinates': coordinate.tolist()},
        'terminal_record_scope': 'OBSERVED_ARRAYS_NOT_IMMUTABILITY_OR_HISTORY_CUSTODY',
        'same_jump_skeleton': True,
        'distinct_rng_objects': True,
        'random_stream_independence_is_callers_responsibility': True,
        'backward_likelihood_or_score_queried': False,
        'conditional_endpoint_sampler_used': False,
        'work_scope': 'PAIRED_SHARED_SKELETON_NOT_EQUAL_FLOPS_OR_REUSED_NOISE',
    })
    return raw, rb, work
