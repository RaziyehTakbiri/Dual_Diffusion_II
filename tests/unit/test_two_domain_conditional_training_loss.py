"""Synthetic equation/gradient qualification, not a real-domain training run."""

from dataclasses import replace
from fractions import Fraction
import math

import pytest
import torch
from torch import nn

from heterodiff.experiments import two_domain_gpu_training as trainer
from heterodiff.models import two_domain_conditional_training_loss as conditional
from heterodiff.models.configuration_energy_torch import (
    BoundedConfigurationEnergy, ConfigurationEnergyArchitecture, SpectralNormCeilings,
)
from heterodiff.models.configuration_energy_training_torch import (
    ConfigurationEnergyTrainingView, TrainingConfigurationBatch,
)
from heterodiff.processes.reversible_hybrid_reference import (
    PiecewiseConstantHybridSchedule, ReversibleHybridRates, ReversibleHybridReference,
)
from heterodiff.theory.configuration_reference import CappedPoissonConfigurationReference


class SyntheticObservationNuisance(nn.Module):
    """Explicit tiny test choice; not the unfrozen B06 nuisance architecture."""
    def __init__(self):
        super().__init__()
        self.weight = nn.Parameter(torch.tensor([0.2, 0.1, -0.3], dtype=torch.float32))
        self.bias = nn.Parameter(torch.tensor(0.05, dtype=torch.float32))
        self.calls = 0

    def forward(self, observation, task, context):
        self.calls += 1
        return torch.cat((observation, task, context), dim=1) @ self.weight + self.bias


def backbone(dimension=2):
    reference = CappedPoissonConfigurationReference({0: dimension}, {0: 1.0}, activity=1.0, total_cap=3)
    schedule = PiecewiseConstantHybridSchedule((0.0, 0.25, 1.0), (0.0, 0.8), (0.0, 0.6), clean_hold=0.25)
    process = ReversibleHybridReference(reference, schedule, ReversibleHybridRates(reference, per_particle_death_rate=0.7))
    architecture = ConfigurationEnergyArchitecture.from_process(
        process, coordinate_scales_by_type={0: (1.0,) * dimension},
        context_dimension=2, context_scales=(1.0, 1.0), context_schema_sha256='a' * 64,
        event_hidden_width=4, event_embedding_width=4, context_hidden_width=4,
        context_embedding_width=4, readout_hidden_width=4, value_bound=1.5,
        spectral_ceilings=SpectralNormCeilings(*(100.0,) * 7), bias_ceiling=100.0,
        first_derivative_ceiling=1_000_000.0, second_derivative_ceiling=1_000_000.0,
    )
    original = BoundedConfigurationEnergy(architecture, generator=torch.Generator().manual_seed(412))
    return ConfigurationEnergyTrainingView.from_cpu_reference(original)


def classifier(method_id=conditional.b06.PRIMARY_METHOD_ID, dimension=2):
    return conditional.ConditionalClassifier(
        backbone(dimension), SyntheticObservationNuisance(), method_id=method_id,
        clean_hold=0.25, nuisance_architecture_id='SYNTHETIC_THREE_FEATURE_LINEAR_V1',
    )

def paired_batches(model, size=4, times=None):
    times = torch.linspace(0.3, 1.0, size, dtype=torch.float32) if times is None else times
    observation1 = torch.arange(size, dtype=torch.float32).unsqueeze(-1) / 10
    observation2 = observation1 + 0.4
    shared_context = torch.full((size, 1), 0.125, dtype=torch.float32)
    task = torch.zeros(size, 1, dtype=torch.float32)
    coordinates = torch.full((size, model.backbone.architecture.type_dimensions[0]), 0.3, dtype=torch.float32)
    owners = torch.arange(size, dtype=torch.int64)
    configuration1 = TrainingConfigurationBatch(
        model.backbone.architecture.architecture_sha256, times,
        torch.cat((observation1, shared_context), dim=1), (coordinates,), (owners,),
    )
    configuration2 = replace(configuration1, context=torch.cat((observation2, shared_context), dim=1))
    kind = conditional.BASELINE_KIND_BY_METHOD[model.method_id]
    joint = conditional.ConditionalLogitBatch(
        configuration1, conditional.ObservationOnlyInputs(observation1, task, shared_context),
        torch.full((size,), -0.5, dtype=torch.float32), kind,
    )
    product = conditional.ConditionalLogitBatch(
        configuration2, conditional.ObservationOnlyInputs(observation2, task.clone(), shared_context.clone()),
        torch.full((size,), -0.75, dtype=torch.float32), kind,
    )
    return joint, product


@pytest.mark.parametrize('method_id', list(conditional.BASELINE_KIND_BY_METHOD))
def test_equal_prior_equation_and_differentiable_nuisance_gradient(method_id):
    model = classifier(method_id)
    joint, product = paired_batches(model)
    weights = conditional.SamplingLawWeights.declared(law_id='SYNTHETIC_DECLARED_LAW', size=4)
    joint_logits, product_logits = model(joint), model(product)
    expected = 0.5 * (torch.nn.functional.softplus(-joint_logits).mean()
                      + torch.nn.functional.softplus(product_logits).mean())
    actual = conditional.equal_prior_joint_product_loss(model, joint, product, weights)
    assert actual.dtype == torch.float32 and actual.shape == torch.Size([])
    torch.testing.assert_close(actual, expected, rtol=0, atol=0)
    expected_bias_gradient = 0.5 * ((torch.sigmoid(joint_logits) - 1).mean()
                                    + torch.sigmoid(product_logits).mean())
    actual.backward()
    torch.testing.assert_close(model.nuisance.bias.grad, expected_bias_gradient)
    assert any(value.grad is not None and bool(value.grad.abs().sum() > 0) for value in model.backbone.parameters())
    assert all(value.grad.dtype == torch.float32 for value in model.parameters() if value.grad is not None)


def test_cubic_gate_uses_direct_time_clean_hold_and_no_second_saturation():
    model = classifier()
    with torch.no_grad():
        model.backbone.readout.linear3.weight.zero_()
        model.backbone.readout.linear3.bias.fill_(1.2)
    times = torch.tensor([0.125, 0.25, 0.625, 1.0], dtype=torch.float32)
    joint, _ = paired_batches(model, times=times)
    ungated = model.backbone(joint.configuration)
    seen = []
    hook = model.backbone.register_forward_pre_hook(lambda module, args: seen.append(args[0].forward_time.clone()))
    residual = model.gated_residual(joint)
    hook.remove()
    assert len(seen) == 1 and torch.equal(seen[0], times[2:])
    torch.testing.assert_close(residual, ungated * torch.tensor([0.0, 0.0, 0.125, 1.0]), rtol=0, atol=0)
    assert not torch.signbit(residual[:2]).any()
    assert residual[-1] == ungated[-1]
    assert residual[-1] != 1.5 * torch.tanh(ungated[-1] / 1.5)
    all_hold, _ = paired_batches(model, times=torch.tensor([0.0, 0.1, 0.2, 0.25]))
    hook = model.backbone.register_forward_pre_hook(lambda *args: pytest.fail('neural forward ran during clean hold'))
    try:
        hold_components = model.components(all_hold)
    finally:
        hook.remove()
    assert torch.equal(hold_components.gated_residual, torch.zeros(4))
    assert model.nuisance.calls > 0  # The nuisance is NOT gated away.


def test_physical_potential_never_evaluates_or_contains_nuisance():
    model = classifier()
    joint, _ = paired_batches(model)
    expected = model.components(joint).physical_log_potential.detach()
    model.nuisance.calls = 0
    with torch.no_grad():
        model.nuisance.bias.add_(100)
    physical = model.physical_log_potential(joint)
    assert model.nuisance.calls == 0
    torch.testing.assert_close(physical, expected, rtol=0, atol=0)
    physical.sum().backward()
    assert all(value.grad is None for value in model.nuisance.parameters())
    description = model.description()
    assert description['additional_nuisance_parameter_count'] == 4
    assert description['nuisance_architecture_or_capacity_frozen'] is False
    assert description['b06_parameter_count_successor_adopted'] is False


def test_nuisance_interface_has_no_time_or_latent_autograd_path():
    model = classifier()
    joint, _ = paired_batches(model)
    latent = joint.configuration.coordinates[0].clone().requires_grad_(True)
    direct_time = joint.configuration.forward_time.clone().requires_grad_(True)
    joint = replace(joint, configuration=replace(joint.configuration, forward_time=direct_time, coordinates=(latent,)))
    components = model.components(joint)
    gradients = torch.autograd.grad(components.nuisance.sum(), (latent, direct_time), allow_unused=True)
    assert gradients == (None, None)
    bad_observation = replace(joint.observation_only, observation=latent[:, :1])
    with pytest.raises(ValueError, match='detached'):
        model(replace(joint, observation_only=bad_observation))
    alias = replace(joint.observation_only, observation=latent.detach()[:, :1])
    with pytest.raises(ValueError, match='aliases a latent/time'):
        model(replace(joint, observation_only=alias))
    assert model.description()['observation_feature_origin_authenticated'] is False


def test_exact_rn_factors_are_unnormalized_and_match_manual_weighted_risk():
    model = classifier()
    joint, product = paired_batches(model)
    unit = conditional.SamplingLawWeights.declared(law_id='TARGET', size=4)
    doubled = conditional.SamplingLawWeights('TARGET', 'PROPOSAL', (Fraction(2),) * 4, (Fraction(2),) * 4, False)
    unit_loss = conditional.equal_prior_joint_product_loss(model, joint, product, unit)
    double_loss = conditional.equal_prior_joint_product_loss(model, joint, product, doubled)
    torch.testing.assert_close(double_loss, 2 * unit_loss, rtol=0, atol=0)
    mixed = conditional.SamplingLawWeights('TARGET', 'OTHER',
                                         (Fraction(1, 3), Fraction(2), Fraction(0), Fraction(7, 4)),
                                         (Fraction(3, 2), Fraction(1), Fraction(1, 4), Fraction(5)), False)
    left, right = mixed.tensors(size=4, device=torch.device('cpu'))
    expected = 0.5 * ((left * torch.nn.functional.softplus(-model(joint))).mean()
                      + (right * torch.nn.functional.softplus(model(product))).mean())
    torch.testing.assert_close(conditional.equal_prior_joint_product_loss(model, joint, product, mixed), expected)
    assert mixed.description()['joint_exact_factors'][0] == '1/3'
    assert mixed.description()['self_normalization_performed'] is False


def test_finite_population_bayes_logit_risk_matches_enumerated_equal_prior_oracle():
    model = classifier()
    # Enumerate all four (latent, observation) atoms under uniform proposal;
    # exact RN weights recover each target class law, with no sampled-law claim.
    joint_mass = (Fraction(3, 10), Fraction(2, 10), Fraction(1, 10), Fraction(4, 10))
    product_mass = (Fraction(2, 10), Fraction(3, 10), Fraction(2, 10), Fraction(3, 10))
    logits = tuple(math.log(float(a / b)) for a, b in zip(joint_mass, product_mass))
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.zero_()
    joint, product = paired_batches(model)
    values = torch.tensor(logits, dtype=torch.float32)
    joint = replace(joint, baseline_log_values=values)
    product = replace(product, baseline_log_values=values.clone())
    weights = conditional.SamplingLawWeights('ENUMERATED_TARGET', 'UNIFORM_ENUMERATION',
                                            tuple(4 * value for value in joint_mass),
                                            tuple(4 * value for value in product_mass), False)
    actual = conditional.equal_prior_joint_product_loss(model, joint, product, weights)
    expected = 0.5 * sum(float(a) * math.log1p(math.exp(-value)) + float(b) * math.log1p(math.exp(value))
                         for a, b, value in zip(joint_mass, product_mass, logits))
    assert math.isclose(actual.item(), expected, abs_tol=1e-7)
    perturbed = replace(joint, baseline_log_values=values + 0.3)
    perturbed_product = replace(product, baseline_log_values=values + 0.3)
    assert conditional.equal_prior_joint_product_loss(model, perturbed, perturbed_product, weights) > actual


@pytest.mark.parametrize('field', ['time', 'latent', 'task', 'context'])
def test_cross_context_permutation_and_changed_latent_time_are_rejected(field):
    model = classifier()
    joint, product = paired_batches(model)
    if field == 'time':
        product = replace(product, configuration=replace(product.configuration, forward_time=product.configuration.forward_time.flip(0)))
    elif field == 'latent':
        product = replace(product, configuration=replace(product.configuration, coordinates=(product.configuration.coordinates[0] + 0.1,)))
    else:
        product = replace(product, observation_only=replace(product.observation_only, **{field: getattr(product.observation_only, field) + 0.1}))
    with pytest.raises(ValueError, match='must share|must use'):
        conditional.equal_prior_joint_product_loss(model, joint, product, conditional.SamplingLawWeights.declared(law_id='SYNTHETIC', size=4))


@pytest.mark.parametrize('bad', [
    conditional.SamplingLawWeights('LAW', 'LAW', (Fraction(2),) * 4, (Fraction(1),) * 4, True),
    conditional.SamplingLawWeights('LAW', 'LAW', (Fraction(1),) * 4, (Fraction(1),) * 4, False),
    conditional.SamplingLawWeights('LAW', 'OTHER', (1.0,) * 4, (Fraction(1),) * 4, False),
    conditional.SamplingLawWeights('LAW', 'OTHER', (Fraction(-1),) * 4, (Fraction(1),) * 4, False),
    conditional.SamplingLawWeights('LAW', 'OTHER', (Fraction(1),) * 3, (Fraction(1),) * 4, False),
])
def test_wrong_or_missing_sampling_law_weights_fail(bad):
    model = classifier()
    with pytest.raises(ValueError):
        conditional.equal_prior_joint_product_loss(model, *paired_batches(model), bad)


def test_baseline_roles_and_finite_fp32_boundary_are_explicit():
    model = classifier()
    joint, product = paired_batches(model)
    with pytest.raises(ValueError, match='baseline role'):
        model(replace(joint, baseline_kind='TERMINAL_LIKELIHOOD_LOG'))
    with pytest.raises(ValueError, match='finite dense FP32'):
        model(replace(joint, baseline_log_values=joint.baseline_log_values.double()))
    with pytest.raises(ValueError, match='finite dense FP32'):
        model(replace(joint, baseline_log_values=torch.full((4,), float('inf'))))
    with pytest.raises(TypeError):
        conditional.equal_prior_joint_product_loss(model, joint, product, None)


@pytest.mark.parametrize('domain,dimension', [('physionet-challenge-2012', 112), ('online-retail-ii', 10)])
def test_real_conditional_objective_updates_model_and_nuisance_through_generic_optimizer(domain, dimension):
    model = classifier(dimension=dimension)
    before = {name: value.clone() for name, value in model.state_dict().items()}
    supplied = trainer.TensorTrainingRoster(domain, tuple(f'train{i:03}'.encode() for i in range(17)),
                                            {'index': torch.arange(17, dtype=torch.int64)})
    # The tiny supplied codec only qualifies the actual loss/optimizer graph;
    # an independently simulated candidate-base pairing codec is still external.
    def pair_builder(fields, generator):
        assert fields['index'].numel() == 16
        joint, product = paired_batches(model, size=16)
        return joint, product, conditional.SamplingLawWeights.declared(law_id='TINY_SYNTHETIC_PAIR_CODEC', size=16)
    result = trainer.run_training_qualification(
        model, supplied, trainer.RunIdentity(model.method_id, domain, 0, 412), device='cpu',
        loss_adapter=conditional.make_joint_product_loss_adapter(pair_builder),
        validation_group_ids=tuple(f'valid{i:03}'.encode() for i in range(128)),
        validation_adapter=lambda *args: trainer.ValidationObservation(torch.zeros(128, dtype=torch.float64)),
        schedule=trainer.NonconfirmatorySchedule(2, 1), configuration_id='TINY_ACTUAL_CONDITIONAL_LOGISTIC_GRAPH',
    )
    assert result.completed_updates == 2
    final = result.checkpoints[-1].model_state
    assert any(not torch.equal(before[name], final[name]) for name in before if name.startswith('backbone.') and 'weight' in name)
    assert not torch.equal(before['nuisance.weight'], final['nuisance.weight'])
    assert all(torch.equal(before[name], value) for name, value in model.state_dict().items())
    assert result.summary()['scientific_result_created'] is False


def test_clean_hold_cannot_be_silently_changed_from_process_owned_architecture():
    with pytest.raises(ValueError, match='process-owned architecture'):
        conditional.ConditionalClassifier(backbone(), SyntheticObservationNuisance(),
                                         method_id=conditional.b06.PRIMARY_METHOD_ID,
                                         clean_hold=0.0, nuisance_architecture_id='SYNTHETIC_NUISANCE')


def test_exact_fraction_fp32_conversion_corrects_binary64_double_rounding():
    lower = Fraction(1)
    upper = Fraction(1) + Fraction(1, 2**23)
    midpoint = (lower + upper) / 2
    tiny = Fraction(1, 2**80)
    # Both values first round to the same binary64 midpoint. The exact
    # rational correction must select opposite FP32 neighbours.
    assert float(midpoint - tiny) == float(midpoint + tiny)
    convert = conditional._round_nonnegative_fraction_fp32
    assert convert(midpoint - tiny) == float(lower)
    assert convert(midpoint + tiny) == float(upper)
    assert convert(midpoint) == float(lower)  # even significand wins the tie.
    next_upper = upper + Fraction(1, 2**23)
    assert convert((upper + next_upper) / 2) == float(next_upper)
    assert convert(Fraction(1, 3)) == torch.tensor(1 / 3, dtype=torch.float32).item()
    assert convert(Fraction(0)) == 0.0
    with pytest.raises(ArithmeticError, match='underflowed'):
        convert(Fraction(1, 2**200))
    with pytest.raises(ArithmeticError, match='finite FP32 range'):
        convert(Fraction(2**129))
