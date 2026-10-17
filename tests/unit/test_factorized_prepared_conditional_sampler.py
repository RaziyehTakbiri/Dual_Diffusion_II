"""Prepared-versus-fresh CPU path equivalence and bounded resource controls."""
from dataclasses import replace

import pytest
import torch

from heterodiff.experiments.factorized_common_grid_pipeline import (
    CommonGridDeviceFactorizedBasePopulation, common_grid_sample_conditional,
)
from heterodiff.experiments.factorized_prepared_conditional_sampler import (
    MAXIMUM_PREPARED_DRAWS, PreparedCommonGridConditionalSampler,
    PreparedConditionalSamplerError,
)
from tests.unit.test_factorized_common_grid_pipeline import (
    DOMAINS, GRID, METHODS, fixture,
)


@pytest.fixture(autouse=True)
def cpu_one_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        yield
    finally:
        torch.set_num_threads(previous)


def assert_same_path(left, right):
    assert left.reverse_grid == right.reverse_grid
    assert left.states == right.states
    assert left.diagnostics == right.diagnostics
    assert left.terminal_state is left.states[-2]
    assert right.terminal_state is right.states[-2]


@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize("method", METHODS)
def test_prepared_paths_and_diagnostics_exactly_match_fresh_function(domain, method):
    source, ref, base, _, model, context = fixture(domain, method)
    population = CommonGridDeviceFactorizedBasePopulation(base, ref, GRID, context)
    kwargs = {"expected_population_law_id": population.law_id}
    prepared = PreparedCommonGridConditionalSampler(
        base, model, ref, GRID, context, (source[-1],),
        maximum_draws=2, **kwargs,
    )
    assert prepared.population_law_id == population.law_id
    for seed in (15, 16):
        record = b"paired-draw-" + seed.to_bytes(8, "big")
        original = common_grid_sample_conditional(
            base, model, ref, GRID, context, (source[-1],),
            run_seed=seed, record_id=record, **kwargs,
        )
        reused = prepared.sample_path(run_seed=seed, record_id=record)
        assert_same_path(original, reused)
        assert reused.diagnostics["sampler_law_id"] == prepared.sampler_law_id
    assert prepared.draws_begun == 2


@pytest.mark.parametrize("observed", [None, ()])
def test_overflow_and_empty_observations_keep_exact_original_payload(observed):
    _, ref, base, _, model, context = fixture()
    prepared = PreparedCommonGridConditionalSampler(
        base, model, ref, GRID, context, observed, maximum_draws=1,
    )
    old = common_grid_sample_conditional(
        base, model, ref, GRID, context, observed, run_seed=33, record_id=b"boundary",
    )
    new = prepared.sample_path(run_seed=33, record_id=b"boundary")
    assert_same_path(old, new)
    assert new.diagnostics["expected_training_population_binding_checked"] is False


def test_caller_weight_and_reference_mutations_do_not_change_prepared_snapshot():
    source, ref, base, _, model, context = fixture()
    prepared = PreparedCommonGridConditionalSampler(
        base, model, ref, GRID, context, source, maximum_draws=2,
    )
    first = prepared.sample_path(run_seed=71, record_id=b"snapshot")
    identity = prepared.sampler_law_id
    with torch.no_grad():
        next(base.parameters()).add_(0.1)
        next(model.parameters()).sub_(0.1)
        model.nuisance.output.bias.add_(1.0)
    ref.schedule = replace(ref.schedule, jump_rate=0.75)
    second = prepared.sample_path(run_seed=71, record_id=b"snapshot")
    assert prepared.sampler_law_id == identity
    assert_same_path(first, second)


def test_wrong_expected_training_population_is_refused_during_preparation():
    source, ref, base, _, model, context = fixture()
    with pytest.raises(PreparedConditionalSamplerError, match="expected training law"):
        PreparedCommonGridConditionalSampler(
            base, model, ref, GRID, context, source, maximum_draws=1,
            expected_population_law_id="another-population",
        )


@pytest.mark.parametrize("limit", [0, -1, MAXIMUM_PREPARED_DRAWS + 1, True, 1.0, None])
def test_invalid_or_expanded_draw_limit_fails_before_model_inspection(limit):
    with pytest.raises(PreparedConditionalSamplerError, match="integer from 1"):
        PreparedCommonGridConditionalSampler(
            None, None, None, None, None, None, maximum_draws=limit,
        )


def test_exhausted_draw_budget_refuses_before_sampling(monkeypatch):
    source, ref, base, _, model, context = fixture()
    prepared = PreparedCommonGridConditionalSampler(
        base, model, ref, GRID, context, source, maximum_draws=1,
    )
    prepared.sample_path(run_seed=41, record_id=b"one")
    monkeypatch.setattr(
        prepared._sampler, "sample_path",
        lambda **kwargs: pytest.fail("exhausted budget began another path"),
    )
    with pytest.raises(PreparedConditionalSamplerError, match="draw limit exhausted"):
        prepared.sample_path(run_seed=42, record_id=b"two")
    assert prepared.draws_begun == 1


def test_failed_started_draw_is_charged_and_no_fallback_is_returned(monkeypatch):
    source, ref, base, _, model, context = fixture()
    prepared = PreparedCommonGridConditionalSampler(
        base, model, ref, GRID, context, source, maximum_draws=1,
    )
    calls = []

    def fail(**kwargs):
        calls.append(kwargs)
        raise RuntimeError("forced path resource refusal")

    monkeypatch.setattr(prepared._sampler, "sample_path", fail)
    with pytest.raises(RuntimeError, match="forced path resource refusal"):
        prepared.sample_path(run_seed=41, record_id=b"one")
    with pytest.raises(PreparedConditionalSamplerError, match="draw limit exhausted"):
        prepared.sample_path(run_seed=42, record_id=b"two")
    assert len(calls) == prepared.draws_begun == 1


@pytest.mark.parametrize("seed,record", [
    (True, b"x"), (-1, b"x"), (2 ** 64, b"x"), (1.0, b"x"),
    (1, b""), (1, "not-bytes"),
])
def test_invalid_stream_inputs_do_not_start_or_charge_draw(seed, record, monkeypatch):
    source, ref, base, _, model, context = fixture()
    prepared = PreparedCommonGridConditionalSampler(
        base, model, ref, GRID, context, source, maximum_draws=1,
    )
    monkeypatch.setattr(
        prepared._sampler, "sample_path",
        lambda **kwargs: pytest.fail("invalid stream input sampled a path"),
    )
    with pytest.raises(PreparedConditionalSamplerError):
        prepared.sample_path(run_seed=seed, record_id=record)
    assert prepared.draws_begun == 0


def test_public_metadata_is_read_only_or_copied():
    source, ref, base, _, model, context = fixture()
    prepared = PreparedCommonGridConditionalSampler(
        base, model, ref, GRID, context, source, maximum_draws=1,
    )
    with pytest.raises(AttributeError):
        prepared.sampler_law_id = "changed"
    with pytest.raises(AttributeError):
        prepared.maximum_draws = 100
    metadata = prepared.snapshot_binding()
    metadata["population"]["grid_values"][1] = 0.125
    metadata["scope"]["exact_numerical_doob_transform_claimed"] = True
    fresh = prepared.snapshot_binding()
    assert fresh["population"]["grid_values"] == list(GRID)
    assert fresh["scope"]["exact_numerical_doob_transform_claimed"] is False
    assert fresh["resumable_checkpoint"] is False
    assert fresh["maximum_draws"] == 1

