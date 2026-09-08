"""Small known-law and refusal checks, not production convergence claims."""
from dataclasses import replace
from fractions import Fraction
import math

import numpy as np
import pytest
from scipy.linalg import expm

from heterodiff.data.two_domain_factorized_state import FactoredEvent, PhysioStateKey
from heterodiff.theory.factorized_smooth_amendment import AmendmentParameters, FactorizedSmoothOracle
from heterodiff.processes.factorized_hybrid_sampler import (
    ExactFactorizedReference, FactorizedSamplingError, FactorizedSamplerLimits,
    FactorizedSchedule, LearnedFactorizedSampler, heun_step,
)

ATOM = FactoredEvent(PhysioStateKey(0, 'GCS', 'ATOMIC', Fraction(3)))
KEY = PhysioStateKey(1, 'HR', 'POSITIVE')


class OneKeyReference:
    """Normalized finite known-law fixture, not the scientific metadata carrier."""
    def __init__(self, continuous=False):
        self.continuous = continuous

    def log_prob(self, key):
        assert key == (KEY if self.continuous else ATOM.key)
        return 0.

    def sample_event(self, rng):
        return FactoredEvent(KEY, float(rng.standard_normal())) if self.continuous else ATOM


def reference(*, continuous=False, jump=1., rate=1., cap=3, limits=FactorizedSamplerLimits()):
    p = AmendmentParameters(1.5, cap, 2, .8, .1, .2, .1, .4)
    return ExactFactorizedReference(FactorizedSmoothOracle(OneKeyReference(continuous), p),
                                   FactorizedSchedule(1., .25, jump, rate), limits)


class Zero:
    upper_value_bound = 0.

    def __init__(self):
        self.calls = []

    def value(self, u, state):
        self.calls.append(('value', u))
        return 0.

    def value_grad(self, u, state):
        self.calls.append(('gradient', u))
        return 0., tuple((0.,) if e.key.dimension else () for e in state)


@pytest.mark.parametrize('s', [0., .1, .25])
def test_forward_clean_hold_has_no_rng_request(s):
    class NoRng:
        def __getattr__(self, name):
            raise AssertionError('RNG requested in clean hold')
    process = reference(continuous=True)
    state = (FactoredEvent(KEY, .4),)
    assert process.sample_forward(state, s, NoRng()) == state


def test_reference_ou_uses_exact_transition_not_heun():
    process = reference(continuous=True, jump=0.)
    state = (FactoredEvent(KEY, .4),)
    actual = process.sample_forward(state, .75, np.random.default_rng(7))
    z = float(np.random.default_rng(7).standard_normal())
    expected = math.exp(-.25)*.4+math.sqrt(-math.expm1(-.5))*z
    assert actual[0].coordinate == expected


def test_reference_count_transition_matches_capped_ctmc_known_law():
    process = reference(rate=0.)
    generator = np.zeros((4,4))
    for n in range(4):
        if n < 3:
            generator[n,n+1] = 1.2
        if n:
            generator[n,n-1] = .8*n
        generator[n,n] = -generator[n].sum()
    expected = expm(.5*generator)[2]
    rng = np.random.default_rng(9102)
    counts = np.bincount([len(process.sample_forward((ATOM,ATOM), .75, rng))
                          for _ in range(4000)], minlength=4)/4000
    assert counts == pytest.approx(expected, abs=.03)


def test_birth_and_death_are_repeated_and_cap_is_respected():
    process, potential = reference(jump=30., rate=0.), Zero()
    sampler = LearnedFactorizedSampler(process, potential, (0., .75, 1.))
    first = sampler.sample_path(run_seed=12, record_id=b'jumps')
    repeat = sampler.sample_path(run_seed=12, record_id=b'jumps')
    assert first == repeat
    assert first.diagnostics['accepted_birth'] > 1
    assert first.diagnostics['accepted_death'] > 1
    assert all(max(row[3:5]) <= 3 for row in first.diagnostics['jump_journal'])
    assert first.states[-1] is first.states[-2]
    assert first.diagnostics['held_intervals'] == 1
    assert all(u < .75 for _,u in potential.calls)


def test_purpose_separated_branches_do_not_reuse_initial_stream():
    sampler = LearnedFactorizedSampler(reference(), Zero(), (0., .75, 1.))
    a = sampler.sample_path(run_seed=4, record_id=b'x', branch_id=b'one')
    b = sampler.sample_path(run_seed=4, record_id=b'x', branch_id=b'two')
    assert a.diagnostics['stream_binding_sha256'] != b.diagnostics['stream_binding_sha256']


def test_missing_hold_breakpoint_is_rejected():
    with pytest.raises(FactorizedSamplingError, match='breakpoint'):
        LearnedFactorizedSampler(reference(), Zero(), (0., 1.))


def test_resource_exhaustion_refuses_entire_path():
    limits = replace(FactorizedSamplerLimits(), maximum_jump_candidates=1)
    sampler = LearnedFactorizedSampler(reference(jump=100., rate=0., limits=limits),
                                       Zero(), (0., .75, 1.))
    with pytest.raises(FactorizedSamplingError, match='no partial trajectory'):
        sampler.sample_path(run_seed=12, record_id=b'jumps')


def test_invalid_potential_bound_refuses_before_returning_path():
    class Bad(Zero):
        def value(self, u, state):
            return 1.
    sampler = LearnedFactorizedSampler(reference(jump=20., rate=0.), Bad(), (0., .75, 1.))
    with pytest.raises(FactorizedSamplingError, match='bound violated'):
        sampler.sample_path(run_seed=3, record_id=b'bad')


def test_heun_zero_noise_refinement_has_second_order_global_drift_error():
    zero, state = Zero(), (FactoredEvent(KEY, 1.),)
    def integrate(h):
        x = state
        for i in range(round(.5/h)):
            x = heun_step(x, i*h, h, zero, 1., ((0.,),))
        return x[0].coordinate
    target = math.exp(-.25)
    coarse, fine = abs(integrate(.125)-target), abs(integrate(.0625)-target)
    assert .23 < fine/coarse < .27


def test_heun_crossing_duplicate_keys_preserves_occurrence_noise_assignment():
    state = (FactoredEvent(KEY, -.1), FactoredEvent(KEY, .1))
    result = heun_step(state, 0., .1, Zero(), 1., ((1.,),(-1.,)))
    expected = []
    for e, noise in zip(state, (1.,-1.)):
        predictor = e.coordinate-.05*e.coordinate+noise
        expected.append(e.coordinate+.05*(-e.coordinate/2-predictor/2)+noise)
    assert sorted(e.coordinate for e in result) == pytest.approx(sorted(expected))


def test_heun_atomic_rows_have_no_derivative_or_noise():
    class NoPotential:
        def __getattr__(self, name):
            raise AssertionError('atomic derivative requested')
    assert heun_step((ATOM,ATOM), 0., .1, NoPotential(), 1., ((),())) == (ATOM,ATOM)


def test_heun_invalid_coordinate_dimension_refuses():
    with pytest.raises(FactorizedSamplingError, match='Brownian fiber'):
        heun_step((FactoredEvent(KEY, .1),), 0., .1, Zero(), 1., ((),))


def test_heun_noncanonical_input_refuses_instead_of_recoupling_noise():
    with pytest.raises(FactorizedSamplingError, match='canonical input order'):
        heun_step((FactoredEvent(KEY, .1), FactoredEvent(KEY, -.1)), 0., .1, Zero(), 1., ((0.,),(0.,)))


def test_reference_cap_zero_is_absorbing_without_birth_proposal():
    process = reference(cap=0)
    assert process.proposal((), np.random.default_rng(4)) is None
    assert process.sample_forward((), .8, np.random.default_rng(9)) == ()


@pytest.mark.parametrize('horizon,hold,jump,rate', [(0.,0.,1.,1.),(1.,1.,1.,1.),(1.,-.1,1.,1.),
                                                (1.,0.,-1.,1.),(1.,0.,1.,float('nan'))])
def test_bad_schedule_rejected(horizon, hold, jump, rate):
    with pytest.raises(FactorizedSamplingError):
        FactorizedSchedule(horizon,hold,jump,rate)
