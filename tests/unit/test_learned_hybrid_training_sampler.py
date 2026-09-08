"""Local numerical tests, not real-data or production sampler qualification."""

import math

import numpy as np
import pytest

from heterodiff.processes.learned_hybrid_training_sampler import (
    GaussianFiniteEventObservation,
    HybridSamplingContext,
    HybridTrainingSamplingError,
    HybridTrajectoryPlan,
    LearnedHybridTrainingSampler,
    ReferenceConfigurationInitializer,
)
from heterodiff.processes.reversible_hybrid_reference import (
    PiecewiseConstantHybridSchedule,
    ReversibleHybridRates,
    ReversibleHybridReference,
)
from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
    TransformedEvent,
)


def _process(*, activity=0.3, cap=3, delta=1.0, gamma=0.2, replacement=False):
    reference = CappedPoissonConfigurationReference(
        {0: 1, 1: 2} if replacement else {0: 1},
        {0: 0.5, 1: 0.5} if replacement else {0: 1.0},
        activity=activity, total_cap=cap,
    )
    return ReversibleHybridReference(
        reference,
        PiecewiseConstantHybridSchedule((0.0, 0.25, 1.0), (0.0, gamma),
                                        (0.0, 1.0), clean_hold=0.25),
        ReversibleHybridRates(reference, per_particle_death_rate=delta,
                              replacement_fluxes={(0, 1): 5.0} if replacement else None),
    )


class _ZeroPotential:
    upper_value_bound = 0.0

    def __init__(self):
        self.calls = []

    def value(self, u, state):
        self.calls.append(("value", u, state))
        return 0.0

    def value_grad(self, u, state):
        self.calls.append(("gradient", u, state))
        return 0.0, tuple(tuple(0.0 for _ in e.coordinates) for e in state)


class _QuadraticPotential(_ZeroPotential):
    def value(self, u, state):
        return -0.5 * sum(x * x for e in state for x in e.coordinates)

    def value_grad(self, u, state):
        return self.value(u, state), tuple(tuple(-x for x in e.coordinates) for e in state)


class _CountPotential(_ZeroPotential):
    def __init__(self, cap, coefficient=0.3):
        super().__init__()
        self.coefficient = coefficient
        self.upper_value_bound = coefficient * cap

    def value(self, u, state):
        return self.coefficient * len(state)

    def value_grad(self, u, state):
        return self.value(u, state), tuple(tuple(0.0 for _ in e.coordinates) for e in state)


def _sampler(*, process=None, potential=None, initial=None, plan=None):
    process = _process() if process is None else process
    initializer = ReferenceConfigurationInitializer() if initial is None else lambda p, rng: initial
    return LearnedHybridTrainingSampler(
        process, _ZeroPotential() if potential is None else potential,
        HybridTrajectoryPlan((0.0, 0.375, 0.75, 1.0)) if plan is None else plan,
        initializer,
    )


def test_reference_initializer_is_exact_supplied_rng_reference_call():
    process = _process(activity=2.0)
    expected = process.reference.sample_configuration(np.random.default_rng(81))
    assert ReferenceConfigurationInitializer()(process, np.random.default_rng(81)) == expected


def test_zero_potential_heun_matches_ou_heun_formula_not_exact_ou_transition():
    sampler = _sampler(initial=(TransformedEvent(0, (0.7,)),))
    dt, gamma = 0.3, 0.2
    noise = float(np.random.default_rng(91).standard_normal()) * math.sqrt(gamma * dt)
    x = 0.7
    expected = (1 - 0.5 * gamma * dt + 0.125 * gamma**2 * dt**2) * x + (1 - 0.25 * gamma * dt) * noise
    result = sampler._heun((TransformedEvent(0, (x,)),), 0.0, dt, gamma, np.random.default_rng(91))
    assert result[0].coordinates[0] == pytest.approx(expected, rel=0, abs=2e-16)
    # This deliberate Heun result is NOT relabelled the exact reference OU step.
    exact_reference = math.exp(-0.5 * gamma * dt) * x + math.sqrt(-math.expm1(-gamma * dt)) * float(np.random.default_rng(91).standard_normal())
    assert abs(result[0].coordinates[0] - exact_reference) > 1e-8


@pytest.mark.parametrize("initial", [(-0.1, 0.1), (0.0, 0.0)])
def test_heun_preserves_occurrence_noise_when_predictor_crosses_or_starts_duplicates(initial):
    class Noise:
        def __init__(self):
            self.values = iter((3.0, -3.0))

        def standard_normal(self, size):
            assert size == 1
            return np.asarray([next(self.values)])

    sampler = _sampler(potential=_QuadraticPotential())
    state = tuple(TransformedEvent(0, (x,)) for x in initial)
    gamma, dt = 0.4, 0.5
    a = 1.5 * gamma  # OU -gamma*x/2 plus gradient -gamma*x; no extra factor 2.
    expected = []
    for x, z in zip(initial, (3.0, -3.0)):
        increment = math.sqrt(gamma * dt) * z
        predicted = x - dt * a * x + increment
        expected.append(x - 0.5 * dt * a * (x + predicted) + increment)
    assert (initial[0] * (1 - dt * a) + math.sqrt(gamma * dt) * 3
            > initial[1] * (1 - dt * a) - math.sqrt(gamma * dt) * 3)
    result = sampler._heun(state, 0.0, dt, gamma, Noise())
    assert tuple(e.coordinates[0] for e in result) == pytest.approx(tuple(sorted(expected)), abs=1e-15)


def test_same_scalar_drives_continuous_and_jump_changes():
    process = _process(activity=1.0, delta=10.0)
    zero = _sampler(process=process, initial=(TransformedEvent(0, (0.2,)),))
    learned = _sampler(process=process, potential=_QuadraticPotential(), initial=(TransformedEvent(0, (0.2,)),))
    left = zero.sample_path(run_seed=55, record_id=b"learned-comparison")
    right = learned.sample_path(run_seed=55, record_id=b"learned-comparison")
    assert left.states != right.states
    assert all(j.acceptance_probability == 1.0 for j in left.jumps)
    assert any(j.acceptance_probability < 1.0 for j in right.jumps)


def test_reference_zero_potential_has_birth_death_replacement_and_cap_suppression():
    process = _process(activity=2.0, cap=2, delta=12.0, replacement=True)
    sampler = _sampler(process=process, initial=())
    path = sampler.sample_path(run_seed=48, record_id=b"all-reference-routes")
    assert {j.kind for j in path.jumps} == {"birth", "death", "replacement"}
    assert all(j.accepted and j.acceptance_probability == 1.0 for j in path.jumps)
    assert len(path.jumps) > 3  # A full operational loop, not one edit per macrostep.
    for jump in path.jumps:
        assert jump.cardinality_after <= 2
        assert jump.cardinality_after - jump.cardinality_before == {"birth": 1, "death": -1, "replacement": 0}[jump.kind]
        assert not (jump.kind == "birth" and jump.cardinality_before == 2)
    for state in path.states:
        assert state == process.reference.canonicalize(state)
        assert all(len(e.coordinates) == process.reference.type_dimensions[e.event_type] for e in state)


def test_count_energy_has_exact_unnormalized_edit_tilt_and_envelope_refresh():
    potential = _CountPotential(2)
    path = _sampler(process=_process(activity=1.0, cap=2, delta=20.0), potential=potential, initial=()).sample_path(
        run_seed=31, record_id=b"count-tilt")
    assert path.jumps
    assert any(not jump.accepted for jump in path.jumps)
    for jump in path.jumps:
        destination_count = jump.cardinality_before + {"birth": 1, "death": -1}[jump.kind]
        expected = math.exp(0.3 * destination_count - 0.6)
        assert jump.acceptance_probability == pytest.approx(expected, rel=8e-16)
    assert all(a.operational_time < b.operational_time for a, b in zip(path.jumps, path.jumps[1:]) if a.grid_step == b.grid_step)


def test_replay_purpose_separation_and_no_global_numpy_random_mutation():
    sampler = _sampler(process=_process(activity=2.0))
    before = np.random.get_state()
    a = sampler.sample_path(run_seed=2**64 - 1, record_id=b"record")
    b = sampler.sample_path(run_seed=2**64 - 1, record_id=b"record")
    c = sampler.sample_path(run_seed=2**64 - 1, record_id=b"record", branch_id=b"other")
    after = np.random.get_state()
    assert a == b
    assert (a.states, a.jumps) != (c.states, c.jumps)
    assert before[0] == after[0] and np.array_equal(before[1], after[1]) and before[2:] == after[2:]
    assert a.diagnostics["scope"] == "LOCAL_NUMERICAL_HYBRID_SUCCESSOR_NOT_PRODUCTION_QUALIFIED"


def test_clean_hold_is_identical_and_does_not_add_model_or_rng_calls():
    process = _process(delta=1e-20)
    p1, p2 = _ZeroPotential(), _ZeroPotential()
    initial = (TransformedEvent(0, (0.8,)),)
    base = _sampler(process=process, potential=p1, initial=initial)
    split_hold = _sampler(process=process, potential=p2, initial=initial,
                          plan=HybridTrajectoryPlan((0.0, 0.375, 0.75, 0.875, 1.0)))
    a = base.sample_path(run_seed=8, record_id=b"hold")
    b = split_hold.sample_path(run_seed=8, record_id=b"hold")
    assert a.at_time(0.75) is a.terminal_state
    assert b.at_time(0.75) is b.at_time(0.875) is b.terminal_state
    assert a.terminal_state == b.terminal_state
    assert a.diagnostics["stream_request_count"] == b.diagnostics["stream_request_count"]
    assert p1.calls == p2.calls
    assert all(t <= 0.75 for _, t, _ in p1.calls)


def test_active_step_ending_at_hold_uses_declared_one_sided_coefficient():
    process = _process(delta=1e-20)
    potential = _ZeroPotential()
    sampler = _sampler(process=process, potential=potential, initial=(TransformedEvent(0, (0.4,)),),
                       plan=HybridTrajectoryPlan((0.0, 0.75, 1.0)))
    path = sampler.sample_path(run_seed=13, record_id=b"boundary")
    assert process.schedule.continuous_rate(0.25) == 0.0  # Old API unchanged.
    assert path.states[0] != path.states[1]
    assert any(kind == "gradient" and time == 0.75 for kind, time, _ in potential.calls)
    assert path.diagnostics["one_sided_segment_owned_heun_coefficients"] is True


@pytest.mark.parametrize("grid", [(0.0, 0.5, 1.0), (0.0, 0.75, 0.9), (0.0, 0.75, 0.75, 1.0)])
def test_grid_must_respect_horizon_breakpoints_and_increase(grid):
    with pytest.raises(HybridTrainingSamplingError):
        _sampler(plan=HybridTrajectoryPlan(grid))


@pytest.mark.parametrize("seed", [None, -1, 2**64, True])
def test_no_implicit_or_invalid_seed(seed):
    with pytest.raises(HybridTrainingSamplingError, match="uint64"):
        _sampler().sample_path(run_seed=seed, record_id=b"seed")


def test_interior_request_is_not_silently_snapped_or_refined():
    path = _sampler().sample_path(run_seed=1, record_id=b"grid")
    with pytest.raises(HybridTrainingSamplingError, match="exact declared grid point"):
        path.at_time(0.37)


def test_invalid_cap_state_is_rejected_not_truncated():
    sampler = _sampler(process=_process(cap=1), initial=(TransformedEvent(0, (0.0,)), TransformedEvent(0, (0.0,))))
    with pytest.raises(HybridTrainingSamplingError, match="no clipping"):
        sampler.sample_path(run_seed=1, record_id=b"overcap")


@pytest.mark.parametrize("mode", ["bound", "nan", "gradient_shape", "gradient_nan"])
def test_potential_and_gradient_failures_do_not_return_success(mode):
    class Broken(_ZeroPotential):
        def value_grad(self, u, state):
            if mode == "bound":
                return 1.0, ((0.0,),)
            if mode == "nan":
                return float("nan"), ((0.0,),)
            if mode == "gradient_shape":
                return 0.0, ()
            return 0.0, ((float("nan"),),)

    with pytest.raises(HybridTrainingSamplingError):
        _sampler(potential=Broken(), initial=(TransformedEvent(0, (0.0,)),)).sample_path(run_seed=1, record_id=b"bad")


def test_proposal_budget_exhaustion_is_failure_not_a_partial_path():
    sampler = _sampler(process=_process(activity=2.0, delta=100.0), initial=(),
                       plan=HybridTrajectoryPlan((0.0, 0.375, 0.75, 1.0), max_jump_candidates=1))
    with pytest.raises(HybridTrainingSamplingError, match="no truncated trajectory"):
        sampler.sample_path(run_seed=48, record_id=b"exhaustion")


def test_envelope_overflow_and_tiny_acceptance_have_no_fallback():
    class TooLow(_ZeroPotential):
        def value(self, u, state):
            return -1000.0

    with pytest.raises(HybridTrainingSamplingError, match="envelope overflow"):
        _sampler(potential=TooLow(), initial=()).sample_path(run_seed=1, record_id=b"envelope")

    class Rare(_ZeroPotential):
        def value(self, u, state):
            return -100.0 if state else 0.0

    with pytest.raises(HybridTrainingSamplingError, match="finite-RNG range"):
        _sampler(process=_process(activity=2.0, delta=100.0), potential=Rare(), initial=()).sample_path(run_seed=1, record_id=b"rare")


def test_continuous_gaussian_observation_is_actual_noise_not_finite_table():
    law = GaussianFiniteEventObservation(0.25)
    context = HybridSamplingContext("SYNTHETIC", b"task", b"context")
    state = (TransformedEvent(0, (0.5,)), TransformedEvent(1, (0.2, -0.4)))
    rng = np.random.default_rng(21)
    expected = (
        TransformedEvent(0, (0.5 + 0.25 * float(rng.standard_normal()),)),
        TransformedEvent(1, tuple(np.asarray((0.2, -0.4)) + 0.25 * rng.standard_normal(2))),
    )
    assert law(state, context, np.random.default_rng(21)) == expected
    assert law((), context, np.random.default_rng(21)) == ()
    assert law.declaration_id.endswith("NOT_REAL_DOMAIN_K_M")


def test_pairs_share_only_context_time_and_use_separate_complete_reference_paths():
    sampler = _sampler(process=_process(activity=2.0, cap=4))
    context = HybridSamplingContext("SYNTHETIC", b"task", b"context")
    seen = []

    def observation(state, actual_context, rng):
        assert actual_context is context
        value = GaussianFiniteEventObservation(0.3)(state, context, rng)
        seen.append((state, value))
        return value

    pair = sampler.sample_pair(context=context, reverse_time=0.375, run_seed=7,
                               record_id=b"pair", observation_law=observation)
    assert pair.joint_pair[0] is pair.product_pair[0]
    assert pair.joint_pair[1] is pair.branch_one.observation
    assert pair.product_pair[1] is pair.branch_two.observation
    assert pair.branch_one.trajectory.states != pair.branch_two.trajectory.states
    assert seen == [(pair.branch_one.terminal_state, pair.branch_one.observation),
                    (pair.branch_two.terminal_state, pair.branch_two.observation)]
    again = sampler.sample_pair(context=context, reverse_time=0.375, run_seed=7,
                                record_id=b"pair", observation_law=observation)
    assert pair == again
    assert pair.branch_one.trajectory.diagnostics["initializer_is_reference_pi_n"] is True


def test_classifier_pairs_refuse_custom_initial_law_and_noninterior_time():
    context = HybridSamplingContext("SYNTHETIC", b"task", b"context")
    kwargs = dict(context=context, reverse_time=0.375, run_seed=1, record_id=b"pair", observation_law=GaussianFiniteEventObservation(1.0))
    with pytest.raises(HybridTrainingSamplingError, match="reference Pi_N"):
        _sampler(initial=()).sample_pair(**kwargs)
    for time in (0.0, 1.0, 0.37):
        with pytest.raises(HybridTrainingSamplingError, match="interior sampling time"):
            _sampler().sample_pair(**{**kwargs, "reverse_time": time})


def test_recorded_coordinate_budget_cannot_return_partial_success():
    plan = HybridTrajectoryPlan((0.0, 0.375, 0.75, 1.0), max_recorded_coordinates=1)
    with pytest.raises(HybridTrainingSamplingError, match="no partial success"):
        _sampler(process=_process(delta=1e-20), initial=(TransformedEvent(0, (0.1,)),), plan=plan).sample_path(
            run_seed=5, record_id=b"records")


def test_query_refinement_is_explicit_and_reports_changed_numerical_grid():
    base = HybridTrajectoryPlan((0.0, 0.375, 0.75, 1.0))
    refined = base.refined_for_query(0.37)
    assert base.reverse_grid == (0.0, 0.375, 0.75, 1.0)
    assert refined.reverse_grid == (0.0, 0.37, 0.375, 0.75, 1.0)
    path = _sampler(plan=refined).sample_path(run_seed=6, record_id=b"query-refinement")
    assert path.at_time(0.37) is path.states[1]
    assert path.diagnostics["actual_macrostep_count"] == 4
    assert path.diagnostics["query_refined_numerical_path_law"] is True
    assert path.diagnostics["base_grid_before_query_refinement_hex"] == tuple(t.hex() for t in base.reverse_grid)
    assert base.refined_for_query(0.375) is base
    with pytest.raises(HybridTrainingSamplingError, match="only one query"):
        refined.refined_for_query(0.38)
    with pytest.raises(HybridTrainingSamplingError, match="interior time"):
        base.refined_for_query(0.0)
    normalized = HybridTrajectoryPlan((0, 0.5, 1), query_refined_from=(0, 1))
    assert all(type(t) is float for t in normalized.query_refined_from)
    for malformed in ((False, 1), (0, float("nan")), [0, 1]):
        with pytest.raises(HybridTrainingSamplingError):
            HybridTrajectoryPlan((0, 0.5, 1), query_refined_from=malformed)


def test_nonfinite_heun_intermediate_fails_without_silent_clipping():
    class HugeGradient(_ZeroPotential):
        def value_grad(self, u, state):
            return 0.0, tuple(tuple(1e308 for _ in event.coordinates) for event in state)

    sampler = _sampler(potential=HugeGradient())
    with pytest.raises(HybridTrainingSamplingError, match="nonfinite Heun predictor"):
        sampler._heun((TransformedEvent(0, (0.0,)),), 0.0, 0.5, 100.0, np.random.default_rng(1))


def test_invalid_reference_categorical_preflight_happens_before_any_jump_rng():
    reference = CappedPoissonConfigurationReference(
        {0: 1, 1: 2}, {0: 1.0 - 1e-14, 1: 1e-14}, activity=0.3, total_cap=2)
    process = ReversibleHybridReference(
        reference, _process().schedule,
        ReversibleHybridRates(reference, per_particle_death_rate=1.0))
    potential = _ZeroPotential()
    sampler = _sampler(process=process, potential=potential, initial=())

    class NoRngAllowed:
        def rng(self, *args):
            raise AssertionError("jump RNG was requested before categorical rejection")

    with pytest.raises((ArithmeticError, ValueError), match="categorical|resolution|mass"):
        sampler._jump_substep((), 0.2, 0.1, 0, NoRngAllowed(), [],
                              {"waiting_time_draws": 0, "jump_candidates": 0, "accepted_jumps": 0})
    assert potential.calls == []


def test_multisegment_coefficients_map_reverse_to_direct_time_exactly():
    reference = _process().reference
    process = ReversibleHybridReference(
        reference,
        PiecewiseConstantHybridSchedule((0.0, 0.25, 0.5, 1.0),
                                        (0.0, 0.1, 0.6), (0.0, 1.0, 3.0), clean_hold=0.25),
        ReversibleHybridRates(reference, per_particle_death_rate=1e-20),
    )
    sampler = _sampler(process=process, initial=(TransformedEvent(0, (0.4,)),),
                       plan=HybridTrajectoryPlan((0.0, 0.5, 0.75, 1.0)))
    calls = []
    original = sampler._heun

    def record_halfstep(state, start, end, gamma, rng):
        calls.append((start, end, gamma))
        return original(state, start, end, gamma, rng)

    sampler._heun = record_halfstep
    path = sampler.sample_path(run_seed=31, record_id=b"reverse-direct-mapping")
    assert calls == [(0.0, 0.25, 0.6), (0.25, 0.5, 0.6),
                     (0.5, 0.625, 0.1), (0.625, 0.75, 0.1)]
    assert path.diagnostics["active_grid_intervals"] == 2
    assert path.diagnostics["held_grid_intervals"] == 1


def test_potential_upper_bound_cannot_change_between_evaluations():
    class Changing(_ZeroPotential):
        def value_grad(self, u, state):
            result = super().value_grad(u, state)
            self.upper_value_bound = 1.0
            return result

    with pytest.raises(HybridTrainingSamplingError, match="upper bound changed"):
        _sampler(potential=Changing(), initial=(TransformedEvent(0, (0.1,)),)).sample_path(
            run_seed=4, record_id=b"changed-bound")
