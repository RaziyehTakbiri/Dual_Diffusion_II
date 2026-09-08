"""One-update CPU pipeline qualification on explicitly invented finite laws.

Connects candidate-base two-branch samples, actual conditional logistic loss,
AdamW, and actual F105 R64/128-group scores. Tiny width/context choices are not
the frozen real-domain architecture. The validation law is a model-weighted
categorical distribution over two supplied configurations, NOT a learned full
hybrid reverse trajectory, admitted K_m, or authenticated conditional sampler.
No study/test data, downloads, cluster jobs, or scientific outcomes are used.
"""

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import math

import numpy as np
import pytest
import torch
from torch import nn

from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    physionet_configuration, physionet_event_from_decimal_token,
    retail_configuration, retail_event_from_decimal_token,
)
from heterodiff.evaluation.two_domain_count_normalized_event_cks_production import ProductionCKSScore
from heterodiff.experiments import two_domain_f105_checkpoint_validation as f105
from heterodiff.experiments import two_domain_gpu_training as trainer
from heterodiff.experiments.two_domain_joint_product_population import (
    ConditionalContext, FiniteCandidateBasePopulation, candidate_generator_from_energy,
)
from heterodiff.models import two_domain_conditional_training_loss as conditional
from heterodiff.models.configuration_energy_torch import (
    BoundedConfigurationEnergy, ConfigurationEnergyArchitecture, SpectralNormCeilings,
)
from heterodiff.models.configuration_energy_training_torch import ConfigurationEnergyTrainingView, TrainingConfigurationBatch
from heterodiff.processes.reversible_hybrid_reference import (
    PiecewiseConstantHybridSchedule, ReversibleHybridRates, ReversibleHybridReference,
)
from heterodiff.theory.configuration_reference import CappedPoissonConfigurationReference

DOMAIN_DIMENSIONS = {'physionet-challenge-2012': 112, 'online-retail-ii': 10}
METHODS = tuple(conditional.BASELINE_KIND_BY_METHOD)
VALIDATION_IDS = tuple(f'synthetic-validation-{index:03}'.encode() for index in range(128))
TRAINING_IDS = tuple(f'synthetic-training-{index:03}'.encode() for index in range(17))
PAIR_SEED = 743
VALIDATION_SEED = 197
LAW_ID = 'SYNTHETIC_FINITE_FIXED_CONTEXT_TIME_HALF_EQUAL_PRIOR'
VALIDATION_LAW_ID = 'SYNTHETIC_MODEL_WEIGHTED_EMPTY_SINGLETON_CATEGORICAL_NOT_HYBRID_REVERSE'


class SyntheticNuisance(nn.Module):
    def __init__(self):
        super().__init__()
        self.weights = nn.Parameter(torch.tensor([0.1, -0.1, 0.2], dtype=torch.float32))
        self.bias = nn.Parameter(torch.tensor(0.0, dtype=torch.float32))

    def forward(self, observation, task, context):
        return torch.cat((observation, task, context), dim=1) @ self.weights + self.bias


def _event_and_configurations(domain):
    if domain == 'physionet-challenge-2012':
        event = physionet_event_from_decimal_token(elapsed_minutes=0, parameter='HR', value_text='80')
        empty, single = physionet_configuration(()), physionet_configuration((event,))
    else:
        event = retail_event_from_decimal_token(
            invoice_no='100001', stock_code='ITEM-A', description='Invented test event',
            quantity=1, invoice_calendar=(2010, 1, 1, 12, 0, 0, 0), unit_price_text='2.50', country='Test',
        )
        empty, single = retail_configuration(()), retail_configuration((event,))
    assert len(event.coordinates) == DOMAIN_DIMENSIONS[domain]
    vector = torch.tensor([float(value) for value in event.coordinates], dtype=torch.float32)
    return vector, (empty, single)


def _energy_view(domain):
    dimension = DOMAIN_DIMENSIONS[domain]
    reference = CappedPoissonConfigurationReference({0: dimension}, {0: 1.0}, activity=1.0, total_cap=3)
    schedule = PiecewiseConstantHybridSchedule((0.0, 0.25, 1.0), (0.0, 0.8), (0.0, 0.6), clean_hold=0.25)
    process = ReversibleHybridReference(reference, schedule, ReversibleHybridRates(reference, per_particle_death_rate=0.7))
    architecture = ConfigurationEnergyArchitecture.from_process(
        process, coordinate_scales_by_type={0: (1.0,) * dimension}, context_dimension=2,
        context_scales=(1.0, 1.0), context_schema_sha256='b' * 64,
        event_hidden_width=4, event_embedding_width=4, context_hidden_width=4,
        context_embedding_width=4, readout_hidden_width=4, value_bound=1.5,
        spectral_ceilings=SpectralNormCeilings(*(100.0,) * 7), bias_ceiling=100.0,
        first_derivative_ceiling=1_000_000.0, second_derivative_ceiling=1_000_000.0,
    )
    original = BoundedConfigurationEnergy(architecture, generator=torch.Generator().manual_seed(621))
    return ConfigurationEnergyTrainingView.from_cpu_reference(original)


def _configuration_batch(view, event_vector, states, observations, *, direct_time=0.5):
    states = torch.tensor(states, dtype=torch.int64)
    observations = torch.tensor(observations, dtype=torch.float32).reshape(-1, 1)
    owners = torch.nonzero(states == 1, as_tuple=False).flatten()
    coordinates = event_vector.unsqueeze(0).repeat(owners.numel(), 1)
    context = torch.full((len(states), 1), 0.25, dtype=torch.float32)
    return TrainingConfigurationBatch(
        view.architecture.architecture_sha256,
        torch.full((len(states),), direct_time, dtype=torch.float32),
        torch.cat((observations, context), dim=1), (coordinates,), (owners,),
    )


def _finite_population(domain, base, vector):
    for parameter in base.parameters():
        parameter.requires_grad_(False)
    with torch.no_grad():
        values = base(_configuration_batch(base, vector, [0, 1], [0, 0])).numpy()
    generator = candidate_generator_from_energy(np.array([[-0.8, 0.8], [0.4, -0.4]]), values)
    return FiniteCandidateBasePopulation(
        context=ConditionalContext(domain, b'synthetic-task', b'synthetic-fixed-context'),
        generator=generator, initial_law=np.array([0.5, 0.5]),
        observation_kernel=np.array([[0.85, 0.15], [0.2, 0.8]]), horizon=1.0,
        declaration_id='SYNTHETIC_TWO_STATE_CANDIDATE_WITH_FIXED_NEURAL_BASE_VALUES',
    ).at_time(0.5)


def _logit_batch(model, vector, fixed, states, observations):
    configuration = _configuration_batch(model.backbone, vector, states, observations)
    observations_array = np.asarray(observations, dtype=np.int64)
    states_array = np.asarray(states, dtype=np.int64)
    baseline_table = (fixed.u_to_terminal @ fixed.population.observation_kernel
                      if model.method_id == conditional.b06.PRIMARY_METHOD_ID
                      else fixed.population.observation_kernel)
    baseline = np.log(baseline_table[states_array, observations_array])
    nuisance_inputs = conditional.ObservationOnlyInputs(
        torch.tensor(observations, dtype=torch.float32).reshape(-1, 1),
        torch.zeros(len(states), 1, dtype=torch.float32),
        torch.full((len(states), 1), 0.25, dtype=torch.float32),
    )
    return conditional.ConditionalLogitBatch(
        configuration, nuisance_inputs, torch.tensor(baseline, dtype=torch.float32),
        conditional.BASELINE_KIND_BY_METHOD[model.method_id],
    )


def _validation_probabilities(model, vector, fixed):
    batch = _logit_batch(model, vector, fixed, [0, 1], [1, 1])
    physical = model.physical_log_potential(batch)
    # This normalization defines an enumerable two-atom validation fixture;
    # it is NOT self-normalization of RN weights in the training objective.
    prior = torch.tensor([63 / 64, 1 / 64], dtype=torch.float32)
    probabilities = torch.softmax(physical + prior.log(), dim=0)
    assert torch.isfinite(probabilities).all() and bool((probabilities > 0).all())
    return probabilities


def _run_pipeline(domain, method):
    vector, configurations = _event_and_configurations(domain)
    base = _energy_view(domain)
    fixed = _finite_population(domain, base, vector)
    base_before = {name: value.clone() for name, value in base.state_dict().items()}
    model = conditional.ConditionalClassifier(
        _energy_view(domain), SyntheticNuisance(), method_id=method, clean_hold=0.25,
        nuisance_architecture_id='EXPLICIT_SYNTHETIC_THREE_FEATURE_AFFINE_ONLY',
    )
    before = {name: value.clone() for name, value in model.state_dict().items()}
    diagnostics = dict(scope='LOCAL_ONE_UPDATE_FINITE_SYNTHETIC_PIPELINE_ONLY',
                       population=fixed.population.summary(), rn_weights=[], sampled_pairs=[],
                       validation_draw_law=VALIDATION_LAW_ID, validation_rows=[],
                       learned_hybrid_reverse_trajectory_generated=False,
                       conditional_generation_authenticated=False, actual_data_accessed=False)
    calls = 0
    def pair_builder(fields, generator):
        nonlocal calls
        assert generator.device.type == 'cpu'
        pairs = [fixed.sample(run_seed=PAIR_SEED, record_id=TRAINING_IDS[index], draw_ordinal=calls)
                 for index in fields['index'].tolist()]
        calls += 1
        for pair in pairs:
            assert pair.joint_pair[0] == pair.product_pair[0]
            assert len(set(pair.branch_one.stream_addresses + pair.branch_two.stream_addresses)) == 8
        diagnostics['sampled_pairs'].extend(pairs)
        states = [pair.branch_one.latent_at_u for pair in pairs]
        joint = _logit_batch(model, vector, fixed, states, [pair.branch_one.observation for pair in pairs])
        product = _logit_batch(model, vector, fixed, states, [pair.branch_two.observation for pair in pairs])
        weights = conditional.SamplingLawWeights.declared(law_id=LAW_ID, size=len(pairs))
        diagnostics['rn_weights'].append(weights.description())
        return joint, product, weights
    def validate(current_model, step, identity):
        probabilities = _validation_probabilities(current_model, vector, fixed)
        generator = torch.Generator().manual_seed(VALIDATION_SEED)
        uniforms = torch.rand((128, 64), generator=generator, dtype=torch.float32)
        choices = (uniforms >= probabilities[0]).to(torch.int64)
        assert bool((choices == 0).any()) and bool((choices == 1).any())
        groups = tuple(f105.GroupConditionalConfigurations(
            group_id, tuple(configurations[value] for value in choices[index].tolist()),
            configurations[1 if index < 2 else 0],
        ) for index, group_id in enumerate(VALIDATION_IDS))
        diagnostics['validation_rows'].append(dict(
            completed_updates=step, model_state_sha256=f105.checkpoint_model_state_sha256(current_model),
            probabilities=probabilities.tolist(), law=VALIDATION_LAW_ID,
            prior_exact_rationals=['63/64', '1/64'],
            empty_draw_count=int((choices == 0).sum()), singleton_draw_count=int((choices == 1).sum()),
            supplied_group_count=128, draws_per_group=64,
            learned_hybrid_reverse_trajectory_generated=False,
        ))
        return f105.evaluate_checkpoint_validation(identity, step, current_model, VALIDATION_IDS, groups)
    result = trainer.run_training_qualification(
        model, trainer.TensorTrainingRoster(domain, TRAINING_IDS, {'index': torch.arange(17, dtype=torch.int64)}),
        trainer.RunIdentity(method, domain, 0, PAIR_SEED), device='cpu',
        loss_adapter=conditional.make_joint_product_loss_adapter(pair_builder),
        validation_group_ids=VALIDATION_IDS, validation_adapter=validate,
        schedule=trainer.NonconfirmatorySchedule(1, 1),
        configuration_id='SYNTHETIC_FINITE_POPULATION_ACTUAL_LOGISTIC_ACTUAL_F105_PIPELINE',
    )
    assert all(torch.equal(before[name], value) for name, value in model.state_dict().items())
    assert all(torch.equal(base_before[name], value) for name, value in base.state_dict().items())
    assert any(not torch.equal(before[name], result.checkpoints[0].model_state[name])
               for name in before if name.startswith('backbone.') and 'weight' in name)
    assert not torch.equal(before['nuisance.weights'], result.checkpoints[0].model_state['nuisance.weights'])
    return result, diagnostics, model, vector, fixed


@pytest.fixture(scope='module', params=[(domain, method) for domain in DOMAIN_DIMENSIONS for method in METHODS])
def pipeline(request):
    return _run_pipeline(*request.param)


def test_finite_pairs_real_loss_optimizer_and_f105_complete_pipeline(pipeline):
    result, diagnostics, model, vector, fixed = pipeline
    assert vector.numel() == DOMAIN_DIMENSIONS[result.identity.domain_id]
    assert result.completed_updates == 1 and result.losses[0] > 0
    assert len(diagnostics['sampled_pairs']) == 16
    assert all(pair.context == fixed.population.context and pair.reverse_time == 0.5
               for pair in diagnostics['sampled_pairs'])
    assert diagnostics['rn_weights'] == [conditional.SamplingLawWeights.declared(law_id=LAW_ID, size=16).description()]
    assert diagnostics['rn_weights'][0]['joint_exact_factors'] == ['1'] * 16
    assert not diagnostics['rn_weights'][0]['self_normalization_performed']
    checkpoint = result.checkpoints[0]
    validation = checkpoint.f105_validation
    assert type(validation) is f105.F105CheckpointValidation
    assert validation.validate_binding(result.identity, 1, checkpoint.model_state, VALIDATION_IDS)
    assert len(validation.group_records) == 128
    assert all(type(row.factory_score) is ProductionCKSScore for row in validation.group_records)
    assert all(row.factory_score.draw_count == 64 for row in validation.group_records)
    assert checkpoint.validation_score_hex == validation.aggregate_hex()
    total = sum((Fraction(*row.factory_score.binary64_score.as_integer_ratio())
                 for row in validation.group_records), Fraction(0))
    assert checkpoint.validation_score_hex == float(total / 128).hex()
    assert diagnostics['validation_rows'][0]['singleton_draw_count'] > 0
    assert diagnostics['validation_rows'][0]['model_state_sha256'] == validation.checkpoint_content_sha256
    assert result.summary()['f105_factory_certification_supplied']
    assert not result.summary()['full_frozen_schedule_executed']
    assert not validation.summary()['f144_checkpoint_cadence_satisfied']
    assert not validation.summary()['conditional_draw_generation_authenticated']
    assert not diagnostics['learned_hybrid_reverse_trajectory_generated']
    assert not diagnostics['actual_data_accessed']


def test_checkpoint_serialization_retains_audit_rows_not_factory_objects(pipeline):
    result = pipeline[0]
    checkpoint = result.checkpoints[0]
    loaded = trainer.inspect_checkpoint_bytes(trainer.checkpoint_to_bytes(checkpoint))
    assert loaded['production_resume_permitted'] is False
    assert loaded['completed_updates'] == 1
    audit = loaded['f105_validation_audit_projection']
    assert audit['serialization_scope'] == 'COMPACT_AUDIT_PROJECTION_NOT_RECONSTRUCTED_FACTORY_OBJECTS'
    assert len(audit['group_records']) == 128
    assert all(type(row) is dict and type(row['factory_record']) is dict for row in audit['group_records'])
    for expected, observed in zip(checkpoint.f105_validation.group_records, audit['group_records']):
        assert observed['group_id_hex'] == expected.group_id.hex()
        assert observed['score_integrity_sha256'] == expected.score_integrity_sha256
        assert observed['factory_record']['binary64_score_hex'] == expected.factory_score.binary64_score_hex
    assert 'f105_validation' not in loaded
    assert type(checkpoint.f105_validation.group_records[0].factory_score) is ProductionCKSScore
    assert f105.checkpoint_model_state_sha256(loaded['model_state']) == checkpoint.f105_validation.checkpoint_content_sha256


def test_wrong_step_or_model_state_cannot_reuse_retained_validation(pipeline):
    result = pipeline[0]
    checkpoint = result.checkpoints[0]
    validation = checkpoint.f105_validation
    with pytest.raises(f105.CheckpointValidationError, match='does not bind'):
        validation.validate_binding(result.identity, 2, checkpoint.model_state, VALIDATION_IDS)
    wrong = deepcopy(checkpoint.model_state)
    wrong['nuisance.bias'].add_(0.125)
    with pytest.raises(f105.CheckpointValidationError, match='does not bind'):
        validation.validate_binding(result.identity, 1, wrong, VALIDATION_IDS)
    with pytest.raises(f105.CheckpointValidationError, match='does not bind'):
        trainer.checkpoint_to_bytes(replace(checkpoint, completed_updates=2))
    with pytest.raises(f105.CheckpointValidationError, match='does not bind'):
        trainer.checkpoint_to_bytes(replace(checkpoint, model_state=wrong))


def test_validation_probability_formula_uses_current_physical_model_not_nuisance(pipeline):
    result, diagnostics, original, vector, fixed = pipeline
    current = deepcopy(original)
    current.load_state_dict(result.checkpoints[0].model_state)
    with torch.no_grad():
        before = _validation_probabilities(current, vector, fixed)
        assert all(math.isclose(value, expected, abs_tol=1e-7) for value, expected
                   in zip(before.tolist(), diagnostics['validation_rows'][0]['probabilities']))
        current.nuisance.bias.add_(50)
        assert torch.equal(before, _validation_probabilities(current, vector, fixed))
        current.backbone.readout.linear1.weight[:, :4].add_(1.0)
        after = _validation_probabilities(current, vector, fixed)
        assert not torch.equal(before, after)
