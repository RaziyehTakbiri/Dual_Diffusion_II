"""Tiny CPU synthetic tests; these do not claim a GPU or scientific qualification."""

from dataclasses import replace

import pytest
import torch

from heterodiff.models.configuration_energy_torch import (
    BoundedConfigurationEnergy,
    ConfigurationEnergyArchitecture,
    SpectralNormCeilings,
    pack_typed_configuration_batch,
)
from heterodiff.models.configuration_energy_training_torch import (
    ConfigurationEnergyTrainingView,
    TrainingConfigurationBatch,
)
from heterodiff.processes.reversible_hybrid_reference import (
    PiecewiseConstantHybridSchedule,
    ReversibleHybridRates,
    ReversibleHybridReference,
)
from heterodiff.theory.configuration_reference import CappedPoissonConfigurationReference


def model_fixture(*, dimension=2, context_dimension=2, width=4):
    base = CappedPoissonConfigurationReference(
        {0: dimension, 1: 0}, {0: 0.5, 1: 0.5}, activity=1.2, total_cap=4
    )
    schedule = PiecewiseConstantHybridSchedule(
        (0.0, 0.25, 1.0), (0.0, 0.8), (0.0, 0.6), clean_hold=0.25
    )
    process = ReversibleHybridReference(
        base, schedule, ReversibleHybridRates(base, per_particle_death_rate=0.7)
    )
    architecture = ConfigurationEnergyArchitecture.from_process(
        process,
        coordinate_scales_by_type={0: (1.5,) * dimension, 1: ()},
        context_dimension=context_dimension,
        context_scales=(1.25,) * context_dimension,
        context_schema_sha256="a" * 64,
        event_hidden_width=width, event_embedding_width=width,
        context_hidden_width=width, context_embedding_width=width,
        readout_hidden_width=width, value_bound=1.5,
        spectral_ceilings=SpectralNormCeilings(*(100.0,) * 7),
        bias_ceiling=100.0, first_derivative_ceiling=1_000_000.0,
        second_derivative_ceiling=1_000_000.0,
    )
    return BoundedConfigurationEnergy(architecture, generator=torch.Generator().manual_seed(718))


def reference_batch(model):
    dimension = model.architecture.type_dimensions[0]
    return pack_typed_configuration_batch(
        model.architecture,
        torch.tensor([0.25, 0.75, 1.0], dtype=torch.float64),
        torch.full((3, model.architecture.context_dimension), 0.3, dtype=torch.float64),
        {0: torch.full((3, dimension), 0.6, dtype=torch.float64),
         1: torch.empty((2, 0), dtype=torch.float64)},
        {0: torch.tensor([0, 0, 1]), 1: torch.tensor([0, 2])},
    )


def test_graph_state_names_parameter_count_and_reference_preservation():
    original = model_fixture()
    before = {key: value.clone() for key, value in original.state_dict().items()}
    view = ConfigurationEnergyTrainingView.from_cpu_reference(original)
    assert view.parameter_count == original.parameter_count
    assert view.state_dict().keys() == original.state_dict().keys()
    for key, value in view.state_dict().items():
        assert value.dtype == torch.float32
        assert torch.equal(value, before[key].float())
    optimizer = torch.optim.AdamW(view.parameters(), lr=0.001)
    output = view(view.from_cpu_batch(reference_batch(original)))
    output.square().mean().backward()
    optimizer.step()
    for key, value in original.state_dict().items():
        assert value.dtype == torch.float64
        assert torch.equal(value, before[key])
    assert any(not torch.equal(value, before[key].float()) for key, value in view.state_dict().items())
    description = view.execution_description()
    assert description["pooling"] == "DEVICE_FP32_PER_SEGMENT_TORCH_SUM"
    assert not description["certified_cpu_checkpoint"]
    assert not description["gpu_execution_qualified"]
    assert not description["scientific_training_ready"]


@pytest.mark.parametrize("dimension,context_dimension,width", [(2, 2, 4), (10, 64, 128), (112, 64, 128)])
def test_fp32_forward_matches_cpu_reference_with_predeclared_tolerance(dimension, context_dimension, width):
    # 2e-6 is a synthetic comparison threshold, not a scientific metric tolerance.
    original = model_fixture(dimension=dimension, context_dimension=context_dimension, width=width)
    view = ConfigurationEnergyTrainingView.from_cpu_reference(original)
    batch = reference_batch(original)
    expected = original(batch)
    actual = view(view.from_cpu_batch(batch))
    assert actual.dtype == torch.float32
    torch.testing.assert_close(actual.double(), expected, atol=2e-6, rtol=2e-6)
    assert bool((actual.abs() <= original.architecture.value_bound).all())


def test_multiplicity_empty_groups_and_permutation_with_tolerance():
    original = model_fixture()
    view = ConfigurationEnergyTrainingView.from_cpu_reference(original)
    batch = view.from_cpu_batch(reference_batch(original))
    baseline = view(batch)
    shuffled = replace(batch, coordinates=(batch.coordinates[0].flip(0), batch.coordinates[1]),
                       batch_indices=(batch.batch_indices[0].flip(0), batch.batch_indices[1]))
    torch.testing.assert_close(view(shuffled), baseline, rtol=2e-6, atol=2e-6)
    dropped = replace(batch, coordinates=(batch.coordinates[0][1:], batch.coordinates[1]),
                      batch_indices=(batch.batch_indices[0][1:], batch.batch_indices[1]))
    assert not torch.equal(view(dropped)[0], baseline[0])
    empty = replace(batch, coordinates=tuple(x[:0] for x in batch.coordinates),
                    batch_indices=tuple(x[:0] for x in batch.batch_indices))
    assert bool(torch.isfinite(view(empty)).all())


def test_first_and_second_coordinate_derivatives_are_finite():
    original = model_fixture()
    view = ConfigurationEnergyTrainingView.from_cpu_reference(original)
    batch = view.from_cpu_batch(reference_batch(original))
    coordinates = batch.coordinates[0].clone().requires_grad_(True)
    batch = replace(batch, coordinates=(coordinates, batch.coordinates[1]))
    first = torch.autograd.grad(view(batch).sum(), coordinates, create_graph=True)[0]
    second = torch.autograd.grad(first.sum(), coordinates)[0]
    assert first.dtype == second.dtype == torch.float32
    assert bool(torch.isfinite(first).all() and torch.isfinite(second).all())


@pytest.mark.parametrize("device", ["cuda", "auto", "mps", "cuda:-1", "cuda:01"])
def test_device_must_be_explicit_without_fallback(device):
    with pytest.raises(ValueError):
        ConfigurationEnergyTrainingView.from_cpu_reference(model_fixture(), device=device)


def test_unavailable_cuda_is_an_error(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(ValueError, match="no CPU fallback"):
        ConfigurationEnergyTrainingView.from_cpu_reference(model_fixture(), device="cuda:0")


@pytest.mark.parametrize("case", ["architecture", "dtype", "nan", "owner", "owner_dtype", "dimension", "context", "time", "cap"])
def test_invalid_inputs_are_rejected(case):
    original = model_fixture()
    view = ConfigurationEnergyTrainingView.from_cpu_reference(original)
    batch = view.from_cpu_batch(reference_batch(original))
    if case == "architecture":
        batch = replace(batch, architecture_sha256="f" * 64)
    elif case == "dtype":
        batch = replace(batch, context=batch.context.double())
    elif case == "nan":
        batch.context[0, 0] = float("nan")
    elif case == "owner":
        batch.batch_indices[0][0] = 3
    elif case == "owner_dtype":
        batch = replace(batch, batch_indices=(batch.batch_indices[0].float(), batch.batch_indices[1]))
    elif case == "dimension":
        batch = replace(batch, coordinates=(batch.coordinates[0][:, :1], batch.coordinates[1]))
    elif case == "context":
        batch = replace(batch, context=batch.context[:2])
    elif case == "time":
        batch.forward_time[0] = -1
    else:
        batch = replace(batch, coordinates=(batch.coordinates[0].repeat(3, 1), batch.coordinates[1]),
                        batch_indices=(batch.batch_indices[0].repeat(3), batch.batch_indices[1]))
    with pytest.raises((ValueError, TypeError)):
        view(batch)


def test_mutated_scales_and_autocast_are_rejected():
    original = model_fixture()
    view = ConfigurationEnergyTrainingView.from_cpu_reference(original)
    batch = view.from_cpu_batch(reference_batch(original))
    with torch.autocast("cpu", dtype=torch.bfloat16):
        with pytest.raises(ValueError, match="autocast"):
            view(batch)
    view.event_encoders[0].coordinate_scales[0] = 0
    with pytest.raises(ValueError, match="scales"):
        view(batch)


def test_plain_or_reference_batch_cannot_be_mislabelled_training_batch():
    original = model_fixture()
    view = ConfigurationEnergyTrainingView.from_cpu_reference(original)
    with pytest.raises(TypeError, match="TrainingConfigurationBatch"):
        view(reference_batch(original))
    assert TrainingConfigurationBatch is not type(reference_batch(original))


def test_empty_event_batch_still_preflights_context_and_readout_work():
    from heterodiff.models import configuration_energy_torch as reference
    original = model_fixture(dimension=2, context_dimension=64, width=128)
    view = ConfigurationEnergyTrainingView.from_cpu_reference(original)
    batch = view.from_cpu_batch(reference_batch(original))
    empty = replace(batch, coordinates=tuple(x[:0] for x in batch.coordinates),
                    batch_indices=tuple(x[:0] for x in batch.batch_indices),
                    context=torch.zeros((4096, 64), dtype=torch.float32),
                    forward_time=torch.zeros(4096, dtype=torch.float32))
    with pytest.raises(reference.ConfigurationEnergyResourceError, match="work limit"):
        view(empty)


def test_resource_preflight_precedes_owner_scan():
    from heterodiff.models import configuration_energy_torch as reference
    original = model_fixture()
    view = ConfigurationEnergyTrainingView.from_cpu_reference(original)
    batch = view.from_cpu_batch(reference_batch(original))
    count = reference.MAX_CONFIGURATION_ENERGY_BATCH_OCCURRENCES + 1
    batch = replace(batch, coordinates=(torch.zeros((count, 2)), batch.coordinates[1]),
                    batch_indices=(torch.full((count,), 999, dtype=torch.int64), batch.batch_indices[1]))
    with pytest.raises(ValueError, match="implementation limits"):
        view(batch)


@pytest.mark.parametrize("domain,dimension", [("physionet-challenge-2012", 112), ("online-retail-ii", 10)])
def test_actual_energy_graph_integrates_with_synthetic_optimizer_and_checkpoint(domain, dimension):
    from heterodiff.experiments.two_domain_gpu_training import (
        NonconfirmatorySchedule, RunIdentity, TensorTrainingRoster,
        ValidationObservation, checkpoint_to_bytes, inspect_checkpoint_bytes,
        run_training_qualification,
    )
    original = model_fixture(dimension=dimension, context_dimension=64, width=128)
    view = ConfigurationEnergyTrainingView.from_cpu_reference(original)
    before = {name: value.clone() for name, value in view.state_dict().items()}
    roster = TensorTrainingRoster(
        domain, tuple(f"train-{i:03}".encode() for i in range(17)),
        {"event": torch.full((17, dimension), 0.2),
         "context": torch.full((17, 64), 0.1),
         "time": torch.full((17,), 0.5)},
    )

    def synthetic_loss(model, fields, generator):
        # Deliberately a synthetic differentiability exercise, NOT the
        # diffusion joint/product classification objective or corruption path.
        batch = TrainingConfigurationBatch(
            model.architecture.architecture_sha256, fields["time"], fields["context"],
            (fields["event"], fields["event"].new_empty((0, 0))),
            (torch.arange(16, device=fields["time"].device),
             torch.empty(0, dtype=torch.int64, device=fields["time"].device)),
        )
        return model(batch).square().mean()

    result = run_training_qualification(
        view, roster, RunIdentity("unified-direct-conditioner", domain, 0, 718),
        device="cpu", loss_adapter=synthetic_loss,
        validation_group_ids=tuple(f"validation-{i:03}".encode() for i in range(128)),
        validation_adapter=lambda model, step, identity: ValidationObservation(
            torch.full((128,), -0.5, dtype=torch.float64)
        ),
        schedule=NonconfirmatorySchedule(maximum_updates=2, validation_every=1),
    )
    assert result.completed_updates == 2
    assert result.selected_checkpoint_step == 1  # Earliest exact tied score.
    summary = result.summary()
    assert not summary["full_frozen_schedule_executed"]
    assert not summary["f105_factory_certification_supplied"]
    assert not summary["actual_diffusion_loss_implemented_by_this_kernel"]
    assert not summary["scientific_result_created"]
    checkpoint = result.checkpoints[-1]
    payload = inspect_checkpoint_bytes(checkpoint_to_bytes(checkpoint))
    assert payload["production_resume_permitted"] is False
    for name, value in payload["model_state"].items():
        assert value.device.type == "cpu" and value.dtype == torch.float32
        assert torch.equal(value, checkpoint.model_state[name])
    assert any(not torch.equal(value, before[name]) for name, value in checkpoint.model_state.items())
    for name, value in view.state_dict().items():
        assert torch.equal(value, before[name])
        assert torch.equal(original.state_dict()[name].float(), before[name])
