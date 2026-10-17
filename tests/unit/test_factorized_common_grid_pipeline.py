"""Local CPU tests of the opt-in common-grid neural successor.

These use tiny synthetic typed events; they do not qualify CUDA, establish
posterior accuracy, or exercise the independent finite-state Doob benchmark.
"""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import math

import pytest
import torch

from heterodiff.data.two_domain_factorized_state import (
    FactoredEvent, FactorizedMetadataReference, PhysioStateKey, RetailStateKey,
    TrainInformedMetadataReference,
)
from heterodiff.experiments.factorized_common_grid_pipeline import (
    CommonGridDeviceFactorizedBasePopulation, CommonGridPipelineError,
    PRECISION_POLICY, RESIDUAL_GATE_POLICY,
    common_grid_integration_smoke, common_grid_sample_conditional,
    common_grid_train_conditional_step,
)
from heterodiff.experiments.factorized_conditional_pipeline import FactorizedPopulationContext
from heterodiff.experiments.factorized_conditional_training import (
    FactorizedConditionalModel, FactorizedObservation,
)
from heterodiff.experiments.factorized_device_training import DeviceFactorizedConditionalModel
from heterodiff.experiments.two_domain_baseline_registry import (
    PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID,
)
from heterodiff.models.factorized_configuration_energy_torch import (
    BoundedFactorizedConfigurationEnergy, FactorizedEnergyArchitecture,
    FactorizedEnergyLimits,
)
from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy
from heterodiff.processes.factorized_hybrid_sampler import (
    ExactFactorizedReference, FactorizedSchedule, FactorizedSamplerLimits,
)
from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide
from heterodiff.theory.factorized_smooth_amendment import (
    AmendmentParameters, FactorizedSmoothOracle,
)

GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
DOMAINS = ("R3-PHYS", "R4-RETAIL")
METHODS = (PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID)


@pytest.fixture(autouse=True)
def bounded_cpu_threads():
    old = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        yield
    finally:
        torch.set_num_threads(old)


def fixture(domain="R3-PHYS", method=PRIMARY_METHOD_ID, gate=RESIDUAL_GATE_POLICY):
    if domain == "R3-PHYS":
        source = (
            FactoredEvent(PhysioStateKey(3, "MechVent", "ATOMIC", Fraction(1))),
            FactoredEvent(PhysioStateKey(3, "HR", "POSITIVE"), 0.2),
        )
    else:
        def key(branch):
            return RetailStateKey(
                "C123456", "sku", "name", -1, (2010, 1, 2, 3, 4, 5, 6),
                "UK", branch,
            )
        source = (FactoredEvent(key("ZERO")), FactoredEvent(key("NEGATIVE"), 0.2))
    rho = TrainInformedMetadataReference(
        FactorizedMetadataReference(domain), source, beta=Fraction(1, 4),
    )
    oracle = FactorizedSmoothOracle(
        rho, AmendmentParameters(0.5, 4, 4, 0.2, 0.1, 0.25, 0.25, 1.0),
    )
    schedule = FactorizedSchedule(1.0, 0.25, 0.5, 1.0)
    reference = ExactFactorizedReference(
        oracle, schedule, FactorizedSamplerLimits(maximum_jump_candidates=20000),
    )
    arch = FactorizedEnergyArchitecture(
        "COMMON_GRID_TEST:" + domain, 4, 1.0, 0.25, 1.0, 1.0,
        FactorizedEnergyLimits(4, 16, 2048, 16384),
    )
    base = DeviceFactorizedEnergy.from_cpu(
        BoundedFactorizedConfigurationEnergy(arch, initialization_seed=41), "cpu",
    )
    cpu = FactorizedConditionalModel(
        BoundedFactorizedConfigurationEnergy(arch, initialization_seed=42),
        guide=FactorizedAssociationGuide(oracle), method_id=method,
        clean_hold=0.25, remaining_clocks=schedule.remaining_clocks,
        observation_seed=43, nuisance_seed=44, residual_gate_policy=gate,
    )
    model = DeviceFactorizedConditionalModel.from_cpu(cpu, "cpu")
    context = FactorizedPopulationContext(domain, "COMMON_GRID_TEST", b"static", (0.0,) * 64)
    return source, reference, base, cpu, model, context


def adam(model):
    return torch.optim.AdamW(
        model.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-8,
        weight_decay=0.0, foreach=False, fused=False, amsgrad=False,
        maximize=False, capturable=False, differentiable=False,
    )


@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize("method", METHODS)
def test_actual_common_grid_update_and_conditional_path(domain, method):
    source, ref, base, _, model, context = fixture(domain, method)
    pop = CommonGridDeviceFactorizedBasePopulation(base, ref, GRID, context)
    assert pop.active_times == (0.0, 0.25, 0.5)
    binding = pop.snapshot_binding()
    assert binding["grid_values"] == list(GRID)
    assert binding["active_time_weights"] == [
        {"reverse_time": u, "numerator": 1, "denominator": 3}
        for u in pop.active_times
    ]
    assert binding["resumable_checkpoint"] is False
    initial = torch.random.get_rng_state().clone()
    report = common_grid_train_conditional_step(
        model, pop, optimizer=adam(model), run_seed=501,
        record_id=b"bounded-update", sample_count=1,
    )
    assert math.isfinite(report["loss"])
    assert report["changed_parameter_elements"] > 0
    assert report["base_paths_generated"] == 2
    assert report["actual_macrosteps"] == 8
    assert report["query_refined_paths"] == 0
    assert report["time_policy"] == "UNIFORM_DISCRETE_ACTIVE_GRID"
    assert all(u in pop.active_times for u in report["reverse_times"])
    assert report["base_precision_policy"] == PRECISION_POLICY
    assert report["residual_gate_policy"] == RESIDUAL_GATE_POLICY
    assert report["scope"]["exact_numerical_doob_transform_claimed"] is False
    path = common_grid_sample_conditional(
        base, model, ref, GRID, context, (source[-1],),
        run_seed=502, record_id=b"bounded-draw", expected_population_law_id=pop.law_id,
    )
    assert path.reverse_grid == GRID
    assert path.terminal_state is path.states[-2]
    assert all(len(state) <= 4 for state in path.states)
    assert all(e.key.domain_id == domain for state in path.states for e in state)
    assert path.diagnostics["reference_pi_n_initializer"] is False
    assert path.diagnostics["residual_gate_policy"] == RESIDUAL_GATE_POLICY
    assert path.diagnostics["base_population_law_id"] == pop.law_id
    assert path.diagnostics["expected_training_population_binding_checked"] is True
    assert path.diagnostics["scope"]["stage_time_interpolation_qualified"] is False
    assert path.diagnostics["scope"]["physical_sampler"] == "COEFFICIENT_TILTED_HYBRID_NUMERICAL_SCHEME"
    assert torch.equal(torch.random.get_rng_state(), initial)


@pytest.mark.parametrize("domain", DOMAINS)
def test_query_time_does_not_change_whole_paths_or_endpoint_observations(domain):
    _, ref, base, _, _, context = fixture(domain)
    pop = CommonGridDeviceFactorizedBasePopulation(base, ref, GRID, context)
    j0, p0, paths0 = pop.sample_pair(reverse_time=0.0, run_seed=9, record_id=b"same")
    j1, p1, paths1 = pop.sample_pair(reverse_time=0.5, run_seed=9, record_id=b"same")
    assert j0.law_id == j1.law_id == p0.law_id == p1.law_id == pop.law_id
    assert j0.observations == j1.observations
    assert p0.observations == p1.observations
    assert j0.states == p0.states == (paths0[0].states[0],)
    assert j1.states == p1.states == (paths0[0].states[2],)
    for left, right in zip(paths0, paths1):
        assert left.states == right.states
        assert left.reverse_grid == right.reverse_grid == GRID
        assert left.diagnostics == right.diagnostics
    assert paths0[0].diagnostics["stream_binding_sha256"] != paths0[1].diagnostics["stream_binding_sha256"]


@pytest.mark.parametrize("query", [-0.1, 0.125, 0.75, 1.0, float("nan"), False, 0])
def test_nonactive_or_offgrid_query_refused_before_sampling(query, monkeypatch):
    _, ref, base, _, _, context = fixture()
    pop = CommonGridDeviceFactorizedBasePopulation(base, ref, GRID, context)
    monkeypatch.setattr(pop.sampler, "sample_path", lambda **kw: pytest.fail("sampled invalid query"))
    with pytest.raises(CommonGridPipelineError, match="existing active grid time"):
        pop.sample_pair(reverse_time=query, run_seed=9, record_id=b"invalid")


@pytest.mark.parametrize("grid", [list(GRID), (0, 0.25, 0.5, 0.75, 1.0), (0.0, float("nan"), 1.0)])
def test_grid_requires_explicit_finite_float_tuple(grid):
    _, ref, base, _, _, context = fixture()
    with pytest.raises(CommonGridPipelineError, match="float grid tuple"):
        CommonGridDeviceFactorizedBasePopulation(base, ref, grid, context)


def test_common_grid_rejects_legacy_gate_without_modifying_weights():
    source, ref, base, _, model, context = fixture(gate="LEGACY_CUBIC_V1")
    pop = CommonGridDeviceFactorizedBasePopulation(base, ref, GRID, context)
    before = deepcopy(model.state_dict())
    with pytest.raises(CommonGridPipelineError, match="LINEAR_ACTIVE_TIME_V1"):
        common_grid_train_conditional_step(
            model, pop, optimizer=adam(model), run_seed=1,
            record_id=b"legacy", sample_count=1,
        )
    with pytest.raises(CommonGridPipelineError, match="LINEAR_ACTIVE_TIME_V1"):
        common_grid_sample_conditional(
            base, model, ref, GRID, context, source,
            run_seed=1, record_id=b"legacy",
        )
    assert all(torch.equal(value, model.state_dict()[name]) for name, value in before.items())


def test_linear_gate_is_copied_and_differs_from_cubic_only_in_explicit_policy():
    source, _, _, cpu, model, context = fixture()
    _, _, _, legacy_cpu, legacy, _ = fixture(gate="LEGACY_CUBIC_V1")
    assert cpu.residual_gate_policy == model.residual_gate_policy == RESIDUAL_GATE_POLICY
    row = FactorizedObservation((source[-1],), context.domain_id, context.task_id, context.context_bytes)
    for u in (0.0, 0.75, 1.0):
        assert torch.equal(model.residual((source,), (u,), (row,)),
                           legacy.residual((source,), (u,), (row,)))
    linear = model.residual((source,), (0.5,), (row,))
    cubic = legacy.residual((source,), (0.5,), (row,))
    torch.testing.assert_close(linear, 9.0 * cubic, atol=1e-12, rtol=1e-12)
    torch.testing.assert_close(cpu.residual((source,), (0.5,), (row,)), linear)
    assert legacy_cpu.residual_gate_policy == "LEGACY_CUBIC_V1"


def test_population_copies_input_base_and_rejects_internal_grid_change():
    _, ref, base, _, _, context = fixture()
    pop = CommonGridDeviceFactorizedBasePopulation(base, ref, GRID, context)
    before = pop.law_id
    with torch.no_grad():
        next(base.parameters()).add_(1.0)
    assert pop._validate_binding() == PRECISION_POLICY
    assert pop.law_id == before
    pop.sampler.grid = (0.0, 0.125, 0.25, 0.5, 0.75, 1.0)
    with pytest.raises(CommonGridPipelineError, match="snapshot or grid changed"):
        pop.sample_pair(reverse_time=0.0, run_seed=9, record_id=b"invalid")


def test_changed_schedule_or_device_binding_is_refused_before_update():
    _, ref, base, _, model, context = fixture()
    pop = CommonGridDeviceFactorizedBasePopulation(base, ref, GRID, context)
    model.remaining_clocks = replace(ref.schedule, jump_rate=0.75).remaining_clocks
    with pytest.raises(RuntimeError, match="exact reference-owned"):
        common_grid_train_conditional_step(
            model, pop, optimizer=adam(model), run_seed=2,
            record_id=b"bad-clock", sample_count=1,
        )


def test_fixed_reverse_time_zero_is_admitted_and_recorded():
    _, ref, base, _, model, context = fixture()
    pop = CommonGridDeviceFactorizedBasePopulation(base, ref, GRID, context)
    report = common_grid_train_conditional_step(
        model, pop, optimizer=adam(model), run_seed=3,
        record_id=b"zero-time", sample_count=1, reverse_time=0.0,
    )
    assert report["reverse_times"] == (0.0,)
    assert report["time_policy"] == "FIXED_ACTIVE_GRID_TIME_DIAGNOSTIC"
    assert report["base_paths_generated"] == 2


def test_legacy_checkpoint_binding_rejects_linear_successor():
    from heterodiff.experiments.factorized_training_checkpoint import (
        FactorizedCheckpointError, _binding,
    )
    _, _, base, _, model, _ = fixture()
    with pytest.raises(FactorizedCheckpointError, match="does not bind the successor"):
        _binding({"purpose": "negative-test"}, base, model)


def test_near_hold_gate_is_linear_not_cubic():
    from heterodiff.experiments.factorized_conditional_training import _conditional_gate
    _, _, _, cpu, _, _ = fixture()
    _, _, _, legacy, _, _ = fixture(gate="LEGACY_CUBIC_V1")
    times = (0.75 - 2.0 ** -10, 0.75 - 2.0 ** -11)
    linear = _conditional_gate(cpu, times)
    cubic = _conditional_gate(legacy, times)
    assert float(linear[0] / linear[1]) == 2.0
    assert float(cubic[0] / cubic[1]) == 8.0
    assert float(_conditional_gate(cpu, (0.75,))[0]) == 0.0


def test_sampler_can_require_exact_training_population_binding():
    source, ref, base, _, model, context = fixture()
    pop = CommonGridDeviceFactorizedBasePopulation(base, ref, GRID, context)
    with torch.no_grad():
        next(base.parameters()).add_(0.01)
    with pytest.raises(CommonGridPipelineError, match="expected training law"):
        common_grid_sample_conditional(
            base, model, ref, GRID, context, source,
            run_seed=7, record_id=b"wrong-base",
            expected_population_law_id=pop.law_id,
        )


def test_trained_base_two_update_two_draw_integration_all_four_cases():
    report = common_grid_integration_smoke()
    assert report["decision"] == "PASS_LOCAL_CPU_TRAINED_BASE_COMMON_GRID_INTEGRATION_ONLY"
    assert report["completed_case_count"] == 4
    assert report["shared_trained_base_within_domain"] is True
    assert {(row["domain_id"], row["method_id"]) for row in report["cases"]} == {
        (domain, method) for domain in DOMAINS for method in METHODS
    }
    assert report["bounds"]["base_optimizer_updates"] == 8
    assert report["bounds"]["conditional_optimizer_updates"] == 8
    assert report["bounds"]["paired_base_paths"] == 16
    assert report["bounds"]["conditional_paths"] == 8
    assert report["scope"]["exact_posterior_comparison_performed"] is False
    assert report["scope"]["checkpoint_resume_exercised"] is False
    assert report["scope"]["gpu_requested"] is False
    for row in report["cases"]:
        assert row["base_optimizer_updates"] == row["conditional_optimizer_updates"] == 2
        assert row["conditional_draw_count"] == 2
        assert row["frozen_population_matches_trained_base"] is True
        assert row["all_checked_quantities_finite"] is True
        assert row["base_initial_parameters_sha256"] != row["base_trained_parameters_sha256"]
        assert row["conditional_initial_parameters_sha256"] != row["conditional_trained_parameters_sha256"]
        assert len(row["base_updates"]) == len(row["conditional_updates"]) == 2
        assert len(row["conditional_paths"]) == 2
        assert all(item["expected_training_population_binding_checked"]
                   for item in row["conditional_paths"])


@pytest.mark.parametrize("seconds", [0.0, -1.0, 31.0, 30, True, float("inf")])
def test_integration_smoke_refuses_invalid_or_expanded_deadline(seconds):
    with pytest.raises(CommonGridPipelineError, match="positive float <=30"):
        common_grid_integration_smoke(maximum_seconds=seconds)
