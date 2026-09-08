"""Synthetic mathematical checks; no source admission or scientific outcomes."""
from dataclasses import replace
from fractions import Fraction
import itertools
import math

import numpy as np
import pytest
from scipy.integrate import quad

from heterodiff.data.two_domain_factorized_state import (
    FactoredEvent, FactorizedMetadataReference, PhysioStateKey,
)
from heterodiff.theory.factorized_smooth_amendment import (
    AmendmentParameters, FactorizedSmoothOracle, OracleLimits,
    SmoothAmendmentError, f105_unconditional_target_mmd_bound, poisson_log_survival,
)


A = FactoredEvent(PhysioStateKey(0, "GCS", "ATOMIC", Fraction(3)))
B = FactoredEvent(PhysioStateKey(1, "MechVent", "ATOMIC", Fraction(0)))
X = PhysioStateKey(2, "HR", "POSITIVE")


class AtomicReference:
    """Normalized finite fixture, not the full-domain production reference."""
    def log_prob(self, key):
        assert key in (A.key, B.key)
        return math.log(0.25 if key == A.key else 0.75)

    def sample_event(self, rng):
        return A if rng.random() < 0.25 else B


class ContinuousReference:
    def log_prob(self, key):
        assert key == X
        return 0.0

    def sample_event(self, rng):
        return FactoredEvent(X, float(rng.normal()))


@pytest.fixture
def params():
    return AmendmentParameters(1.2, 5, 3, 0.7, 0.04, 0.2, 0.03, 0.3)


def counts(n):
    for a in range(n + 1):
        yield (A,) * a + (B,) * (n - a)


def atomic_probability(state, count_probability):
    a, n = state.count(A), len(state)
    return count_probability * math.comb(n, a) * 0.25 ** a * 0.75 ** (n - a)


def test_capped_poisson_and_lift_normalize_with_duplicate_orbits(params):
    oracle = FactorizedSmoothOracle(AtomicReference(), params)
    assert sum(math.exp(oracle.count_log_prob(n)) for n in range(6)) == pytest.approx(1.0)
    sources = ((A, B, A), (), (B, B))
    for source in sources:
        integral = 0.0
        for n in range(6):
            for target in counts(n):
                mass = atomic_probability(target, math.exp(oracle.count_log_prob(n)))
                integral += mass * math.exp(oracle.lift_log_density(source, target))
        assert integral == pytest.approx(1.0)
    integral = sum(atomic_probability(state, math.exp(oracle.count_log_prob(n))) *
                   math.exp(oracle.target_log_density(sources, state))
                   for n in range(6) for state in counts(n))
    assert integral == pytest.approx(1.0)


@pytest.mark.parametrize("jump_clock,continuous_clock", [(0.0, 0.0), (0.4, 0.8), (10.0, 2.0), (20.0, 20.0)])
@pytest.mark.parametrize("state", [(), (A,), (A, A, B), (B,) * 5])
def test_retained_plus_overflow_observation_normalizes(params, jump_clock, continuous_clock, state):
    oracle = FactorizedSmoothOracle(AtomicReference(), params)
    integral = 0.0
    for n in range(4):
        for obs in counts(n):
            lam = atomic_probability(obs, math.exp(-1) / math.factorial(n))
            integral += lam * math.exp(oracle.observation_log_density(state, obs, jump_clock=jump_clock,
                                                                      continuous_clock=continuous_clock))
    lam_overflow = math.exp(poisson_log_survival(3, 1.0))
    integral += lam_overflow * math.exp(oracle.observation_log_density(state, None, jump_clock=jump_clock,
                                                                     continuous_clock=continuous_clock))
    assert integral == pytest.approx(1.0, abs=3e-14)


def test_continuous_lift_normalizes_and_is_smooth(params):
    oracle = FactorizedSmoothOracle(ContinuousReference(), params)
    source = (FactoredEvent(X, 0.4),)
    def density(y):
        target = (FactoredEvent(X, float(y)),)
        return math.exp(oracle.lift_log_density(source, target) + oracle.count_log_prob(1)
                        - y * y / 2) / math.sqrt(2 * math.pi)
    assert quad(density, -10, 10, epsabs=1e-10)[0] == pytest.approx(1.0, abs=1e-10)
    actual = oracle.lift_log_density(source, (FactoredEvent(X, 0.1),))
    h = 1e-5
    plus = oracle.lift_log_density(source, (FactoredEvent(X, 0.1 + h),))
    minus = oracle.lift_log_density(source, (FactoredEvent(X, 0.1 - h),))
    assert (plus - minus) / (2 * h) == pytest.approx((0.4 - 0.1) / 0.2 ** 2 + 0.1)
    assert (plus - 2 * actual + minus) / h ** 2 == pytest.approx(1 - 1 / 0.2 ** 2, abs=3e-5)


@pytest.mark.parametrize("jump_clock,continuous_clock", [(0.0, 0.0), (0.3, 0.4)])
def test_continuous_observation_one_event_integrates_to_correct_count_mass(params, jump_clock, continuous_clock):
    oracle = FactorizedSmoothOracle(ContinuousReference(), params)
    state = (FactoredEvent(X, 0.6),)
    def integrand(y):
        return math.exp(oracle.observation_log_density(state, (FactoredEvent(X, float(y)),),
                                                       jump_clock=jump_clock, continuous_clock=continuous_clock)
                        - 1 - y * y / 2) / math.sqrt(2 * math.pi)
    retain = 0.5 * math.exp(-params.death_rate * jump_clock)
    clutter = 0.5 * params.reference_count_mean * (1 - math.exp(-params.death_rate * jump_clock))
    expected = params.observation_contamination / math.e + (1 - params.observation_contamination) * math.exp(-clutter) * (retain + (1 - retain) * clutter)
    assert quad(integrand, -12, 12, epsabs=1e-10)[0] == pytest.approx(expected, abs=1e-10)


def test_permutation_invariance_and_unseen_stratum_positive_floor(params):
    oracle = FactorizedSmoothOracle(AtomicReference(), params)
    for state in set(itertools.permutations((A, A, B))):
        assert oracle.lift_log_density(state, (B, A, A)) == pytest.approx(oracle.lift_log_density((A, A, B), state))
        assert oracle.observation_log_density(state, (B, A)) == pytest.approx(oracle.observation_log_density((B, A, A), (A, B)))
    assert oracle.target_log_density(((A,),), (B,)) == math.log(params.target_contamination)
    assert oracle.observation_log_density((A,), (B,)) == math.log(params.observation_contamination)
    assert oracle.observation_log_density((), None) == math.log(params.observation_contamination)


def test_full_factorized_reference_preserves_atomic_values_and_can_score_unseen_key(params):
    reference = FactorizedMetadataReference("R3-PHYS")
    oracle = FactorizedSmoothOracle(reference, params)
    atom = FactoredEvent(PhysioStateKey(22, "MechVent", "ATOMIC", Fraction(5, 2)))
    # Structural semantic support does not assert that 2.5 is clinically valid.
    assert atom.key.dimension == 0
    assert oracle.target_log_density(((A,),), (atom,)) == math.log(params.target_contamination)
    value = oracle.observation_log_density((atom,), (atom,))
    assert math.isfinite(value) and value > math.log(params.observation_contamination)


def test_seeded_sampling_is_repeatable_and_does_not_jitter_atoms(params):
    oracle = FactorizedSmoothOracle(AtomicReference(), params)
    def run(seed):
        rng = np.random.Generator(np.random.PCG64(seed))
        return tuple((oracle.sample_training_target(((A, B),), rng), oracle.sample_observation((A, B), rng)) for _ in range(100))
    assert run(23) == run(23)
    for target, observation in run(23):
        assert all(x in (A, B) and x.coordinate is None for x in target)
        assert observation is None or all(x in (A, B) for x in observation)


def test_resource_refusal_not_state_truncation(params):
    oracle = FactorizedSmoothOracle(AtomicReference(), params, limits=OracleLimits(maximum_events=2))
    with pytest.raises(SmoothAmendmentError, match="NO_DROPPING"):
        oracle.observation_log_density((A,) * 3, ())
    oracle = FactorizedSmoothOracle(AtomicReference(), params, limits=OracleLimits(maximum_anchors_per_key=1))
    with pytest.raises(SmoothAmendmentError, match="NO_APPROXIMATION"):
        oracle.lift_log_density((A, A), (A, A))


@pytest.mark.parametrize("name,value", [("target_log_value_sd", 1.0), ("target_log_value_sd", 0.0),
                                        ("target_contamination", 0.0), ("observation_contamination", 0.0),
                                        ("observation_log_value_sd", 0.0), ("reference_cap", -1)])
def test_invalid_scientific_parameters_rejected(params, name, value):
    with pytest.raises(SmoothAmendmentError):
        replace(params, **{name: value})


def test_poisson_tail_does_not_underflow_to_impossibility():
    assert math.isfinite(poisson_log_survival(10000, 1.0))
    assert poisson_log_survival(10000, 1.0) < -80000
    assert poisson_log_survival(0, 1.0) == pytest.approx(math.log1p(-math.exp(-1)))


def test_numeric_failure_does_not_masquerade_as_epsilon_floor(params):
    from heterodiff.theory.factorized_smooth_amendment import _logsum, _normal_log_ratio
    with pytest.raises(SmoothAmendmentError, match="NO_SILENT_ZERO"):
        _logsum((-math.inf, math.nan))
    with pytest.raises(SmoothAmendmentError):
        _normal_log_ratio(1e300, 0.0, 0.5)
    assert _normal_log_ratio(1e100, 1.0, 1.0) == 1e100
    assert _normal_log_ratio(1e300, 0.0, 1.0) == 0.0
    assert _normal_log_ratio(1.0, 0.0, 1e308) == pytest.approx(0.5 - 0.5 * math.log(1e308))
    with pytest.raises(SmoothAmendmentError, match="NOT_REPRESENTABLE"):
        replace(params, observation_log_value_sd=1e300)
    with pytest.raises(SmoothAmendmentError, match="NOT_REPRESENTABLE"):
        replace(params, target_log_value_sd=1e-300)
    oracle = FactorizedSmoothOracle(AtomicReference(), params)
    with pytest.raises(SmoothAmendmentError, match="NO_BRANCH_DELETION"):
        oracle.observation_log_density((A,), (A,), jump_clock=2000.0)


def test_f105_target_shift_bound_is_explicit_and_vanishes_in_joint_limit():
    small = f105_unconditional_target_mmd_bound(alpha=1e-6, tau=1e-6)
    assert 0 < small < 2e-6
    assert f105_unconditional_target_mmd_bound(alpha=0.1, tau=0.2, continuous_fraction=0.0) == pytest.approx(0.1 * math.sqrt(2))
    assert f105_unconditional_target_mmd_bound(alpha=0.1, tau=0.2) == pytest.approx(0.9 * 0.2 * math.sqrt(2 / math.pi) / 4 + 0.1 * math.sqrt(2))
