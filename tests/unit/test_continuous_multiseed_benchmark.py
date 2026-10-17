"""Bounded synthetic runner checks; the default experiment is never launched."""

from dataclasses import FrozenInstanceError
import hashlib
import json
import math

import pytest
import torch

from heterodiff.data.two_domain_factorized_state import FactoredEvent, PhysioStateKey
from heterodiff.evaluation.continuous_fiber_initialization_diagnostic import (
    ContinuousFiberInitializationDiagnostic,
)
from heterodiff.experiments import continuous_multiseed_benchmark as experiment
from heterodiff.experiments.factorized_common_grid_pipeline import (
    CommonGridDeviceFactorizedBasePopulation,
)
from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest


@pytest.fixture(autouse=True)
def cpu_one_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        yield
    finally:
        torch.set_num_threads(previous)


def small_budget():
    return experiment.ExperimentBudget(
        seeds=(1201,), control_draws=2, neural_draws=1, updates=1,
        pairs_per_update=2, validation_pairs=2, maximum_seconds=60,
    )


@pytest.mark.parametrize("field,cap", [
    ("control_draws", 2048), ("neural_draws", 512), ("updates", 32),
    ("pairs_per_update", 4), ("validation_pairs", 32), ("maximum_seconds", 2400),
])
@pytest.mark.parametrize("bad_kind", ["zero", "above_cap", "bool", "float"])
def test_budget_refuses_invalid_or_expanded_counts(field, cap, bad_kind):
    value = {"zero": 0, "above_cap": cap + 1, "bool": True, "float": 1.0}[bad_kind]
    with pytest.raises(ValueError, match=field):
        experiment.ExperimentBudget(**{field: value})


@pytest.mark.parametrize("seeds", [(), [1], (1, 1), (True,), (-1,), (2 ** 64,), (1.0,), (1, 2, 3, 4)])
def test_budget_requires_one_to_three_distinct_uint64_seeds(seeds):
    with pytest.raises(ValueError, match="distinct uint64"):
        experiment.ExperimentBudget(seeds=seeds)


def test_default_specification_is_frozen_and_inspect_does_not_execute(capsys, monkeypatch):
    budget = experiment.ExperimentBudget()
    with pytest.raises(FrozenInstanceError):
        budget.updates = 1
    spec = experiment.specification(budget)
    assert spec["is_default_protocol_run"] is True
    assert spec["total_route_count"] == 22
    assert spec["validation_checkpoints"] == [0, 8, 16, 32]
    assert spec["budget"]["seeds"] == (1201, 1202, 1203)
    assert spec["grid"] == [i / 8.0 for i in range(9)]
    assert len(spec["joint_cdf_grid"]) == 21
    assert spec["alpha_allocation"] == {
        "routes": 0.005, "seed_mixtures": 0.0025, "signed_contrasts": 0.0025,
    }
    assert spec["same_training_pairs_and_initial_tensors_within_seed"] is True
    for name in ("checkpoint_selection", "retry_failed_draws",
                 "common_random_numbers_between_methods",
                 "validation_used_for_model_selection_or_early_stopping",
                 "factorial_separation_of_theta_and_observation_effects",
                 "training_seed_population_confidence_claimed"):
        assert spec[name] is False
    monkeypatch.setattr(experiment, "run_experiment", lambda *a, **k: pytest.fail("inspection ran experiment"))
    assert experiment.main(["--inspect"]) == 0
    assert json.loads(capsys.readouterr().out) == json.loads(json.dumps(spec))
    reduced = experiment.specification(small_budget())
    assert reduced["is_default_protocol_run"] is False
    assert reduced["total_route_count"] == 14
    assert reduced["validation_checkpoints"] == [0, 1]


def test_seed_derivation_matches_declared_bytes_and_separates_purposes():
    seed = 1201
    expected = int.from_bytes(hashlib.sha256(seed.to_bytes(8, "big") + b"conditioner").digest()[:8], "big")
    assert experiment.seed_for(seed, "conditioner") == expected
    assert experiment.seed_for(seed, "conditioner") != experiment.seed_for(seed, "nuisance")
    assert experiment.seed_for(seed, "conditioner") != experiment.seed_for(seed + 1, "conditioner")


@pytest.mark.parametrize("scenario", experiment.SCENARIOS)
def test_paired_methods_share_initial_tensors_population_and_validation_pairs(scenario):
    fixtures = [experiment.fixture(scenario, 1201, method) for method in experiment.METHODS]
    populations = []
    initial = []
    pairs = []
    for ref, independent, key, base, model, context, observed in fixtures:
        assert ref.parameters.reference_count_mean == scenario[1] == independent.spec.theta
        assert observed == (FactoredEvent(key, scenario[2]),)
        assert model.residual_gate_policy == "LINEAR_ACTIVE_TIME_V1"
        assert all(torch.count_nonzero(p).item() == 0 for p in base.parameters())
        initial.append({name: p.detach().clone() for name, p in model.named_parameters()})
        population = CommonGridDeviceFactorizedBasePopulation(base, ref, experiment.GRID, context)
        assert population.active_times == experiment.GRID[:-1]
        populations.append(population)
        calls = []
        pairs.append(experiment.validation_pairs(population, 1201, 2, lambda: calls.append(True)))
        assert calls == [True, True]
    assert initial[0].keys() == initial[1].keys()
    assert all(torch.equal(initial[0][name], initial[1][name]) for name in initial[0])
    assert populations[0].law_id == populations[1].law_id
    assert populations[0].snapshot_binding() == populations[1].snapshot_binding()
    assert pairs[0] == pairs[1]
    for joint, product in pairs[0]:
        assert joint.law_id == product.law_id == populations[0].law_id
        assert joint.reverse_times == product.reverse_times
        assert joint.reverse_times[0] in populations[0].active_times
    for (_, _, _, _, model, _, _), held_out in zip(fixtures, pairs):
        before = _parameter_digest(model)
        first = experiment.validation_loss(model, held_out)
        assert math.isfinite(first)
        assert experiment.validation_loss(model, held_out) == first
        assert _parameter_digest(model) == before


def test_different_seed_changes_conditioner_but_not_zero_base_or_population():
    fixtures = [experiment.fixture(experiment.SCENARIOS[0], seed, experiment.METHODS[0]) for seed in (1201, 1202)]
    assert _parameter_digest(fixtures[0][4]) != _parameter_digest(fixtures[1][4])
    populations = [CommonGridDeviceFactorizedBasePopulation(f[3], f[0], experiment.GRID, f[5]) for f in fixtures]
    assert populations[0].law_id == populations[1].law_id
    assert _parameter_digest(fixtures[0][3]) == _parameter_digest(fixtures[1][3])


def test_fixture_refuses_undeclared_scenario_or_method():
    with pytest.raises(ValueError, match="declared scenario"):
        experiment.fixture(("new", 0.8, 0.7), 1201, experiment.METHODS[0])
    with pytest.raises(ValueError, match="declared scenario"):
        experiment.fixture(experiment.SCENARIOS[0], 1201, "new-method")


def test_indicators_use_joint_not_conditional_cdf_and_include_boundary():
    key = PhysioStateKey(3, "HR", "POSITIVE")
    atom = FactoredEvent(PhysioStateKey(3, "HR", "ZERO"))
    states = [(), (atom,), (FactoredEvent(key, 0.0),), (FactoredEvent(key, 1.2),)]
    values = experiment.indicators(states, key)
    assert values[:3] == [0.25, 0.25, 0.5]
    assert len(values) == 24
    assert values[3:] == [sum(x <= boundary for x in (0.0, 1.2)) / 4.0 for boundary in experiment.CDF_GRID]
    assert values[3 + experiment.CDF_GRID.index(0.0)] == 0.25
    assert values[-1] == 0.5  # Not one: denominator includes empty/OTHER draws.
    with pytest.raises(ValueError, match="nonempty"):
        experiment.indicators([], key)
    with pytest.raises(ValueError, match="cap one"):
        experiment.indicators([(atom, atom)], key)


@pytest.mark.parametrize("scenario", experiment.SCENARIOS)
def test_target_indicators_keep_exact_oracle_joint_mass(scenario):
    _, oracle, _, _, _, _, _ = experiment.fixture(scenario, 1201, experiment.METHODS[0])
    target = oracle.terminal_posterior()
    result = experiment.target_indicators(target)
    assert result[:3] == list(target.state_probabilities)
    assert result[3:] == [target.continuous_cdf(x) for x in experiment.CDF_GRID]
    assert sum(result[:3]) == pytest.approx(1.0)
    assert all(0.0 <= x <= result[2] for x in result[3:])


@pytest.mark.parametrize("scenario", experiment.SCENARIOS)
@pytest.mark.parametrize("zero_clock", [False, True])
def test_guide_control_finite_values_atom_fibers_and_continuous_derivative(scenario, zero_clock):
    _, oracle, key, _, _, _, _ = experiment.fixture(scenario, 1201, experiment.METHODS[0])
    diagnostic = ContinuousFiberInitializationDiagnostic(oracle.spec)
    guide = experiment.GuideControlPotential(diagnostic, key, zero_clock=zero_clock)
    atom = FactoredEvent(PhysioStateKey(3, "HR", "ZERO"))
    other_continuous = FactoredEvent(PhysioStateKey(4, "HR", "POSITIVE"), -0.3)
    for u in (0.0, 0.375, 1.0):
        effective = oracle.spec.horizon if zero_clock else u
        for state, label, coordinate, shape in (
            ((), "EMPTY", None, ()), ((atom,), "OTHER", None, ((),)),
            ((other_continuous,), "OTHER", None, ((0.0,),)),
            ((FactoredEvent(key, 0.2),), "CONTINUOUS", 0.2, None),
        ):
            value, gradient = guide.value_grad(u, state)
            expected = diagnostic.uncapped_log_likelihood_derivatives(effective, label, coordinate)
            assert math.isfinite(value) and value <= guide.upper_value_bound
            assert value == expected["log_likelihood"] == guide.value(u, state)
            assert gradient == (shape if shape is not None else ((expected["gradient"],),))
        h = 1e-5
        finite_difference = (
            guide.value(u, (FactoredEvent(key, 0.2 + h),))
            - guide.value(u, (FactoredEvent(key, 0.2 - h),))
        ) / (2 * h)
        assert guide.value_grad(u, (FactoredEvent(key, 0.2),))[1][0][0] == pytest.approx(
            finite_difference, rel=1e-7, abs=1e-8,
        )
    if zero_clock:
        assert guide.value_grad(0.0, (FactoredEvent(key, 0.2),)) == guide.value_grad(1.0, (FactoredEvent(key, 0.2),))


def test_runner_refuses_nonbudget_and_expired_budget_before_fixture(monkeypatch):
    with pytest.raises(ValueError, match="exact explicit experiment budget"):
        experiment.run_experiment(None)
    clock = iter((0.0, 61.0))
    monkeypatch.setattr(experiment.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(experiment, "fixture", lambda *args: pytest.fail("expired budget constructed fixture"))
    with pytest.raises(TimeoutError, match="partial routes are not a complete experiment"):
        experiment.run_experiment(small_budget())


def test_reduced_actual_experiment_completes_all_fourteen_routes_without_quality_claim():
    progress = []
    report = experiment.run_experiment(
        small_budget(), progress=lambda record, completed, total: progress.append((record, completed, total)),
    )
    assert report["decision"] == "COMPLETE_PREDECLARED_MULTISEED_COMPARISON_REVIEW_ALL_ROUTES"
    assert report["specification"]["is_default_protocol_run"] is False
    assert report["elapsed_seconds"] <= 60
    assert len(report["routes"]) == 14
    assert [p[1:] for p in progress] == [(i, 14) for i in range(1, 15)]
    assert [p[0] for p in progress] == report["routes"]
    assert len(report["summaries"]) == len(report["initializer_diagnostics"]) == 2
    for scenario, _, _ in experiment.SCENARIOS:
        routes = [r for r in report["routes"] if r["scenario"] == scenario]
        assert len(routes) == 7
        assert {r["route"] for r in routes} == set(experiment.CONTROLS + experiment.METHODS)
        assert all(r["metrics"]["target_indicators"] == routes[0]["metrics"]["target_indicators"] for r in routes)
        neural = [r for r in routes if r["kind"] == "neural"]
        assert neural[0]["initial_parameter_sha256"] == neural[1]["initial_parameter_sha256"]
        assert neural[0]["population_law_id"] == neural[1]["population_law_id"]
        for route in routes:
            assert route["metrics"]["draw_count"] == (1 if route["kind"] == "neural" else 2)
            assert route["metrics"]["finite_indicator_error_interval"] == [0.0, 1.0]
            assert len(route["metrics"]["empirical_indicators"]) == 24
        for route in neural:
            assert route["initial_parameter_sha256"] != route["final_parameter_sha256"]
            assert len(route["updates"]) == 1
            assert [x["update"] for x in route["held_out_paired_loss_curve"]] == [0, 1]
            assert all(math.isfinite(x["held_out_paired_loss"]) for x in route["held_out_paired_loss_curve"])
            assert route["training_pairs"] == route["validation_pairs"] == 2
            assert route["training_base_paths"] == route["validation_base_paths"] == 4
            assert route["work"]["macrosteps"] == 8
            assert route["prepared_sampler"]["population_law_id"] == route["population_law_id"]
            assert route["prepared_sampler"]["maximum_draws"] == 1
            assert route["initialization_attempt_count"] is None
            assert route["sampler_preparation_seconds"] >= 0.0
        summary = next(s for s in report["summaries"] if s["scenario"] == scenario)
        assert summary["general_superiority_claimed"] is False
        assert summary["training_seed_roster"] == [1201]
        for method in experiment.METHODS:
            assert summary["methods"][method]["seed_error_sd_descriptive"] is None
            assert summary["methods"][method]["training_seed_population_confidence_claimed"] is False
    assert report["environment"]["device"] == "cpu"
    assert report["environment"]["threads"] == 1
    assert report["scope"]["actual_mixed_neural_conditional_learner_and_sampler"] is True
    assert report["scope"]["base_weights_zero_frozen_not_trained"] is True
    for name in ("real_data_accessed", "GPU_requested", "cloud_or_paid_jobs_launched",
                 "checkpoint_or_hyperparameter_selection",
                 "full_posterior_recovery_or_general_superiority_claimed",
                 "matched_quality_speedup_claimed", "continuous_TV_or_KL_estimated_from_samples"):
        assert report["scope"][name] is False
    assert report["scope"]["failed_samples_discarded"] == report["scope"]["retries"] == 0
    json.dumps(report, allow_nan=False)
