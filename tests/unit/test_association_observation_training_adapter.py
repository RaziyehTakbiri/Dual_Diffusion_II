"""Local synthetic tests; no adopted real-domain observation law or paid run."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import math

import numpy as np
import pytest
import torch

from heterodiff.experiments import association_observation_training_adapter as a
from heterodiff.experiments import hybrid_conditional_training as h
from heterodiff.models.configuration_energy_torch import (
    BoundedConfigurationEnergy, ConfigurationEnergyArchitecture, SpectralNormCeilings,
)
from heterodiff.models.configuration_energy_training_torch import ConfigurationEnergyTrainingView
from heterodiff.models.two_domain_observation_training_design import (
    ObservationConditionEncoderV1, ObservationOnlyNuisanceV1, VisibleObservationSchema,
)
from heterodiff.processes.learned_hybrid_training_sampler import (
    HybridSamplingContext, HybridTrajectoryPlan, LearnedHybridTrainingSampler,
    ReferenceConfigurationInitializer,
)
from heterodiff.processes.reversible_hybrid_reference import (
    PiecewiseConstantHybridSchedule, ReversibleHybridRates, ReversibleHybridReference,
)
from heterodiff.theory.association_observation import (
    AffineGaussianFiberChannel, CollapsedPoissonObservationReference,
    TypedAffineGaussianObservationChannel, TypedGaussianClutterIntensity,
)
from heterodiff.theory.association_preconditioner import AnalyticAssociationPreconditioner
from heterodiff.theory.configuration_reference import CappedPoissonConfigurationReference, TransformedEvent
from heterodiff.theory.finite_atomic_overflow_observation import OVERFLOW_OBSERVATION

DOMAIN = 'physionet-challenge-2012'
METHODS = tuple(h.BASELINE_KIND_BY_METHOD)
CONTEXT = HybridSamplingContext(DOMAIN, b'association', b'synthetic-static-quarter')


def make_kernel(*, atomic=False, cap=2, dimension=1):
    latent_dimensions = {0: 0} if atomic else {0: dimension, 1: 0}
    latent_weights = {0: 1.0} if atomic else {0: 0.7, 1: 0.3}
    reference = CappedPoissonConfigurationReference(latent_dimensions, latent_weights,
                                                  activity=0.2, total_cap=3)
    schedule = PiecewiseConstantHybridSchedule((0.0, 0.0625, 0.25), (0.0, 0.4),
                                               (0.0, 0.2), clean_hold=0.0625)
    process = ReversibleHybridReference(reference, schedule,
        ReversibleHybridRates(reference, per_particle_death_rate=0.3))
    observation_reference = CollapsedPoissonObservationReference(
        {10: 0 if atomic else 1, 11: 0}, {10: 0.2, 11: 0.8}, retained_cap=cap)
    fibers = {} if atomic else {
        (0, 10): AffineGaussianFiberChannel([[1.4] if dimension == 1 else [1.4, -0.8]], [0.2], [[0.6]]),
        (1, 10): AffineGaussianFiberChannel(np.empty((1, 0)), [-0.1], [[0.7]]),
    }
    channel = TypedAffineGaussianObservationChannel(latent_dimensions, observation_reference,
        ((0.75, 0.25),) if atomic else ((0.75, 0.25), (0.4, 0.6)), fiber_channels=fibers)
    clutter = TypedGaussianClutterIntensity(observation_reference, 0.4, (0.1, 0.9),
        fiber_channels={} if atomic else {10: AffineGaussianFiberChannel(np.empty((1, 0)), [-0.2], [[1.2]])})
    guide = AnalyticAssociationPreconditioner(process, observation_reference, channel, clutter,
        {0: 0.65} if atomic else {0: 0.65, 1: 0.5}, contamination_probability=0.2,
        context_key=('synthetic-association-only',))
    return a.NormalizedAssociationTrainingKernel(guide, declaration_id='LOCAL_SYNTHETIC_PROPOSAL',
                                                 declared_context=CONTEXT, static_context=(0.25,))


@pytest.fixture(scope='module')
def kernel():
    return make_kernel()


@pytest.fixture(scope='module')
def atomic_kernel():
    return make_kernel(atomic=True)


def visible_schema(kernel):
    marks = tuple((f'chart_{kind}', (1.0,)*width)
                  for kind, width in kernel.guide.observation_reference.type_dimensions.items() if width)
    return VisibleObservationSchema(DOMAIN, (10, 11), marks, ('association',), ('static',), (1.0,))


def visible(kernel, outcomes):
    return a.tensorize_association_observations(kernel, outcomes, schema=visible_schema(kernel),
        task_ids=('association',)*len(outcomes), static_contexts=((0.25,),)*len(outcomes))


def energy(process, seed=52):
    architecture = ConfigurationEnergyArchitecture.from_process(process,
        coordinate_scales_by_type={kind: (1.0,)*width for kind, width in process.reference.type_dimensions.items()},
        context_dimension=64, context_scales=(1.0,)*64, context_schema_sha256='b'*64,
        event_hidden_width=4, event_embedding_width=4, context_hidden_width=4,
        context_embedding_width=4, readout_hidden_width=4, value_bound=0.1,
        spectral_ceilings=SpectralNormCeilings(*(100.0,)*7), bias_ceiling=100.0,
        first_derivative_ceiling=1e6, second_derivative_ceiling=1e6)
    return ConfigurationEnergyTrainingView.from_cpu_reference(BoundedConfigurationEnergy(
        architecture, generator=torch.Generator().manual_seed(seed)))


def models(kernel, method):
    schema = visible_schema(kernel)
    retained = h.ObservedConditionalTrainingModel(energy(kernel.guide.process),
        ObservationConditionEncoderV1(schema, initialization_seed=12),
        ObservationOnlyNuisanceV1(schema, initialization_seed=24), method_id=method)
    wrapped = a.AssociationConditionalTrainingModel(retained, wrapper_seed=37,
                                                    kernel_sha256=kernel.kernel_sha256)
    return retained, wrapped


def test_whole_mixture_physical_confusion_and_poisson_collapse_match_explicit_rng_replay(atomic_kernel):
    state = (TransformedEvent(0, ()),)*2
    saw_outlier = saw_clean = saw_overflow = saw_duplicate = False
    for seed in range(160):
        actual = np.random.Generator(np.random.PCG64(seed))
        replay = np.random.Generator(np.random.PCG64(seed))
        outlier = float(replay.random()) < 0.2
        if outlier:
            count = int(replay.poisson(1.0))
            signal = None
            clutter = None
        else:
            signal = sum(float(replay.random()) < 0.65 for _ in state)
            clutter = int(replay.poisson(0.4))
            count = signal+clutter
        if count > 2:
            expected = OVERFLOW_OBSERVATION
        else:
            probabilities = [(0.2, 0.8)]*count if outlier else [(0.75, 0.25)]*signal+[(0.1, 0.9)]*clutter
            expected = tuple(sorted((TransformedEvent((10, 11)[int(replay.choice(2, p=p))], ())
                                     for p in probabilities), key=TransformedEvent.model_key))
        result = atomic_kernel.sample(state, rng=actual)
        assert result.outcome == expected
        assert actual.bit_generator.state == replay.bit_generator.state
        assert result.diagnostics['whole_observation_outlier_branch'] is outlier
        assert result.diagnostics['sampled_total_count'] == count
        assert result.diagnostics['signal_count'] == signal
        assert result.diagnostics['clutter_count'] == clutter
        assert not result.diagnostics['observation_truncated_or_redrawn']
        assert not result.diagnostics['hidden_labels_are_model_inputs']
        assert not result.diagnostics['real_domain_kernel_adopted']
        saw_outlier |= outlier
        saw_clean |= not outlier
        saw_overflow |= expected is OVERFLOW_OBSERVATION
        saw_duplicate |= expected is not OVERFLOW_OBSERVATION and len(expected) == 2 and expected[0] == expected[1]
    assert saw_outlier and saw_clean and saw_overflow and saw_duplicate


def _atomic_clean_mass(n_sources, left, right):
    result = 0.0
    for signal_left in range(n_sources+1):
        for signal_right in range(n_sources-signal_left+1):
            missed = n_sources-signal_left-signal_right
            if signal_left > left or signal_right > right:
                continue
            source = (math.factorial(n_sources)/(math.factorial(signal_left)*math.factorial(signal_right)*math.factorial(missed))
                      * (0.65*0.75)**signal_left * (0.65*0.25)**signal_right * 0.35**missed)
            clutter_left, clutter_right = left-signal_left, right-signal_right
            clutter = math.exp(-0.4)*0.04**clutter_left*0.36**clutter_right/(math.factorial(clutter_left)*math.factorial(clutter_right))
            result += source*clutter
    return result


@pytest.mark.parametrize('source_count', [0, 2])
def test_duplicate_atomic_retained_and_overflow_probabilities_normalize_exactly(atomic_kernel, source_count):
    state = (TransformedEvent(0, ()),)*source_count
    reference = atomic_kernel.guide.observation_reference
    masses = []
    for left in range(3):
        for right in range(3-left):
            outcome = (TransformedEvent(10, ()),)*left+(TransformedEvent(11, ()),)*right
            eta = math.exp(-1)*0.2**left*0.8**right/(math.factorial(left)*math.factorial(right))
            log_value, gradient = atomic_kernel.log_value_and_gradient(0.1, state, outcome, propagated=False)
            mass = eta*math.exp(log_value)
            expected = 0.8*_atomic_clean_mass(source_count, left, right)+0.2*eta
            assert math.isclose(mass, expected, rel_tol=2e-12, abs_tol=2e-14)
            assert gradient == ((),)*source_count
            masses.append(mass)
    log_overflow, gradients = atomic_kernel.log_value_and_gradient(0.1, state, OVERFLOW_OBSERVATION, propagated=False)
    overflow_mass = reference.overflow_mass*math.exp(log_overflow)
    assert math.isclose(sum(masses)+overflow_mass, 1.0, rel_tol=0, abs_tol=3e-12)
    assert overflow_mass > 0
    assert gradients == ((),)*source_count


def test_outlier_poisson_is_not_conditioned_on_retained_cap():
    kernel = make_kernel(atomic=True, cap=0)
    matched = False
    for seed in range(100):
        replay = np.random.default_rng(seed)
        if float(replay.random()) < 0.2 and int(replay.poisson(1.0)) > 0:
            actual = np.random.default_rng(seed)
            sample = kernel.sample((), rng=actual)
            assert sample.outcome is OVERFLOW_OBSERVATION
            assert sample.diagnostics['coordinate_generation_skipped_by_exact_overflow_collapse']
            assert actual.bit_generator.state == replay.bit_generator.state
            matched = True
            break
    assert matched


@pytest.mark.parametrize('propagated', [False, True])
def test_continuous_oracle_value_first_gradient_and_terminal_clean_hold(kernel, propagated):
    state = (TransformedEvent(0, (0.25,)), TransformedEvent(1, ()))
    outcome = (TransformedEvent(10, (0.4,)), TransformedEvent(11, ()))
    value, gradient = kernel.log_value_and_gradient(0.1, state, outcome, propagated=propagated)
    delta = 1e-5
    perturbed = lambda x: (TransformedEvent(0, (x,)), state[1])
    difference = (kernel.log_value_and_gradient(0.1, perturbed(0.25+delta), outcome, propagated=propagated)[0]
                  - kernel.log_value_and_gradient(0.1, perturbed(0.25-delta), outcome, propagated=propagated)[0])/(2*delta)
    assert math.isclose(gradient[0][0], difference, rel_tol=1e-5, abs_tol=1e-7)
    assert gradient[1] == ()
    callback = kernel.torch_baseline(outcome, propagated=propagated)
    coordinates = (torch.tensor([[0.25]], requires_grad=True), torch.empty((1, 0), requires_grad=True))
    observed = callback(0.1, state, coordinates)
    derivatives = torch.autograd.grad(observed, coordinates)
    assert float(observed.detach()) == float(torch.tensor(value, dtype=torch.float32))
    assert torch.equal(derivatives[0], torch.tensor([gradient[0]], dtype=torch.float32))
    assert derivatives[1].shape == (1, 0)
    assert callback.kernel_sha256 == kernel.kernel_sha256
    assert callback.propagated is propagated
    terminal = kernel.log_value_and_gradient(0.2, state, outcome, propagated=False)
    held = kernel.log_value_and_gradient(0.2, state, outcome, propagated=True)
    assert np.allclose(held[0], terminal[0], rtol=0, atol=1e-12)
    assert np.allclose(held[1][0], terminal[1][0], rtol=0, atol=1e-12)
    overflow = kernel.log_value_and_gradient(0.1, state, OVERFLOW_OBSERVATION, propagated=propagated)
    assert math.isfinite(overflow[0]) and overflow[1] == ((0.0,), ())


def test_fp32_induced_reordering_keeps_original_occurrence_gradient_owners():
    kernel = make_kernel(dimension=2)
    state = (TransformedEvent(0, (1.0, 2.0)), TransformedEvent(0, (1.0+1e-8, -2.0)))
    coordinates = (torch.tensor([[1.0, 2.0], [1.0+1e-8, -2.0]], requires_grad=True),
                   torch.empty((0, 0), requires_grad=True))
    represented = tuple(TransformedEvent(0, tuple(row)) for row in coordinates[0].detach().tolist())
    assert represented != tuple(sorted(represented, key=TransformedEvent.model_key))
    outcome = (TransformedEvent(10, (0.4,)),)
    callback = kernel.torch_baseline(outcome, propagated=False)
    actual = torch.autograd.grad(callback(0.1, state, coordinates), coordinates)[0]
    for occurrence in range(2):
        for coordinate in range(2):
            def log_at(offset):
                rows = [list(e.coordinates) for e in represented]
                rows[occurrence][coordinate] += offset
                events = tuple(TransformedEvent(0, tuple(row)) for row in rows)
                return kernel.log_value_and_gradient(0.1, events, outcome, propagated=False)[0]
            expected = (log_at(1e-5)-log_at(-1e-5))/2e-5
            assert math.isclose(float(actual[occurrence, coordinate]), expected, rel_tol=2e-5, abs_tol=2e-7)


def test_visible_overflow_is_explicit_and_no_latent_cardinality_or_physical_time_is_fabricated(kernel):
    duplicate = (TransformedEvent(10, (-0.3,)),)*2
    batch = visible(kernel, (duplicate, (), OVERFLOW_OBSERVATION))
    assert batch.validate(visible_schema(kernel)) == 3
    assert batch.overflow.tolist() == [False, False, True]
    assert batch.retained.batch_indices.tolist() == [0, 0]
    assert bool((batch.retained.global_features[:, 1:3] == 0).all())
    assert bool((batch.retained.global_features[2, :3] == 0).all())
    # Physical-time value and presence are absent; negative chart coordinates are marks.
    assert bool((batch.retained.anchor_features[:, :2] == 0).all())
    assert torch.equal(batch.retained.anchor_features[0], batch.retained.anchor_features[1])
    assert not batch.retained.anchor_features.requires_grad
    assert batch.to('cpu').kernel_sha256 == kernel.kernel_sha256
    bad = replace(batch, overflow=torch.tensor([True, False, True]))
    with pytest.raises(a.AssociationTrainingError, match='empty unknown-count'):
        bad.validate(visible_schema(kernel))
    leaked = batch.retained.global_features.clone()
    leaked[:, 1] = 1.0
    with pytest.raises(a.AssociationTrainingError, match='latent cardinality'):
        replace(batch, retained=replace(batch.retained, global_features=leaked)).validate(visible_schema(kernel))


def test_independent_wrapped_encoders_add_exact_parameters_and_preserve_all_visible_rows(kernel):
    retained, current = models(kernel, METHODS[0])
    assert current.parameter_summary()['all_unique_parameters'] - sum(p.numel() for p in retained.parameters()) == 8448
    assert current.encoder.parameter_count - retained.encoder.parameter_count == 4224
    assert current.nuisance.encoder.parameter_count - retained.nuisance.encoder.parameter_count == 4224
    assert {p.data_ptr() for p in current.encoder.parameters()}.isdisjoint(p.data_ptr() for p in current.nuisance.encoder.parameters())
    batch = visible(kernel, ((), OVERFLOW_OBSERVATION))
    calls = []
    handle = current.encoder.retained_encoder.register_forward_hook(lambda module, inputs, output: calls.append(output.shape))
    encoded = current.encoder(batch)
    handle.remove()
    assert calls == [torch.Size([2, 64])]
    assert encoded.shape == (2, 64) and bool((encoded.abs() <= 1).all())
    assert not torch.equal(encoded[0], encoded[1])
    assert current.parameter_summary()['production_configuration_adopted'] is False


def test_overflow_flag_cannot_alias_forbidden_latent_storage(kernel):
    latent = torch.zeros(1, dtype=torch.float32)
    overflow = latent.view(torch.bool)[:1]
    batch = replace(visible(kernel, ((),)), overflow=overflow)
    assert batch.validate(visible_schema(kernel)) == 1
    with pytest.raises(a.AssociationTrainingError, match='alias'):
        batch.validate(visible_schema(kernel), forbidden_tensors=(latent,))


@pytest.mark.parametrize('method', METHODS)
def test_both_paired_losses_have_encoder_nuisance_and_conditioner_gradients(kernel, method):
    _, current = models(kernel, method)
    states = ((TransformedEvent(0, (0.25,)), TransformedEvent(1, ())), ())
    joint_outcomes = ((TransformedEvent(10, (0.4,)),), OVERFLOW_OBSERVATION)
    product_outcomes = ((), (TransformedEvent(11, ()),))
    times = (0.1, 0.1)
    propagated = method == METHODS[0]
    def batch(outcomes):
        baselines = torch.tensor([kernel.log_value_and_gradient(u, y, obs, propagated=propagated)[0]
                                  for u, y, obs in zip(times, states, outcomes)], dtype=torch.float32)
        return a.AssociationLogitBatch(states, times, visible(kernel, outcomes), baselines,
                                       h.BASELINE_KIND_BY_METHOD[method])
    joint, product = batch(joint_outcomes), batch(product_outcomes)
    weights = h.SamplingLawWeights.declared(law_id='SYNTHETIC_ASSOCIATION_TEST_ONLY', size=2)
    result = a.association_joint_product_loss(current, joint, product, weights)
    expected = 0.5*(torch.nn.functional.softplus(-current(joint)).mean()+torch.nn.functional.softplus(current(product)).mean())
    assert torch.equal(result, expected)
    result.backward()
    for prefix in ('conditioner.backbone', 'encoder', 'nuisance.encoder', 'nuisance.hidden'):
        parameters = [p for name, p in current.named_parameters() if name.startswith(prefix)]
        assert any(p.grad is not None and bool((p.grad != 0).any()) for p in parameters), prefix
    altered = deepcopy(current)
    with torch.no_grad():
        for parameter in altered.nuisance.parameters():
            parameter.add_(0.2)
    assert torch.equal(current.residual(states, times, joint.observation), altered.residual(states, times, joint.observation))
    with pytest.raises(a.AssociationTrainingError, match='kernel'):
        current(replace(joint, observation=replace(joint.observation, kernel_sha256='d'*64)))
    with pytest.raises(a.AssociationTrainingError, match='time'):
        a.association_joint_product_loss(current, joint, replace(product, reverse_times=(0.2, 0.1)), weights)


def test_context_and_rng_boundaries_and_immutable_declaration(kernel):
    with pytest.raises(FrozenInstanceError):
        kernel.declaration_id = 'replacement'
    with pytest.raises(a.AssociationTrainingError, match='context'):
        kernel.sample_outcome((), replace(CONTEXT, context_id=b'other'), np.random.default_rng(1))
    with pytest.raises(a.AssociationTrainingError, match='PCG64'):
        kernel.sample((), rng=np.random.Generator(np.random.Philox(1)))
    with pytest.raises(a.AssociationTrainingError):
        kernel.torch_baseline((), propagated=1)
    with pytest.raises(a.AssociationTrainingError, match='coordinate'):
        a.NormalizedAssociationTrainingKernel(kernel.guide, declaration_id='small-bound',
            declared_context=CONTEXT, static_context=(0.25,), max_retained_coordinates=1)


def test_small_actual_base_pair_sampler_uses_bound_normalized_observation_callback(kernel):
    process = kernel.guide.process
    base = energy(process)
    base.requires_grad_(False)
    potential = h.TorchHybridPotential(base, torch.zeros(1, 64))
    sampler = LearnedHybridTrainingSampler(process, potential,
        HybridTrajectoryPlan((0.0, 0.125, 0.1875, 0.25)), ReferenceConfigurationInitializer())
    pair = sampler.sample_pair(context=CONTEXT, reverse_time=0.125, run_seed=28,
        record_id=b'synthetic-association-record', observation_law=kernel.sample_outcome)
    assert pair.context == CONTEXT
    assert pair.branch_one.trajectory.diagnostics['actual_macrostep_count'] == 3
    assert pair.branch_two.trajectory.diagnostics['actual_macrostep_count'] == 3
    for branch in (pair.branch_one, pair.branch_two):
        assert branch.observation is OVERFLOW_OBSERVATION or len(branch.observation) <= 2
        assert visible(kernel, (branch.observation,)).validate(visible_schema(kernel)) == 1
    assert all(parameter.grad is None for parameter in base.parameters())


def test_byte_context_identity_exact_static_binding_and_overflow_context_retention(kernel):
    def declared(value, context=CONTEXT):
        return a.NormalizedAssociationTrainingKernel(kernel.guide, declaration_id='same-declaration',
            declared_context=context, static_context=(value,))
    first = declared(1e100)
    second = declared(1e101)
    assert first.kernel_sha256 != second.kernel_sha256
    assert first.kernel_sha256 == declared(1e100).kernel_sha256
    assert first.kernel_sha256 != declared(1e100, replace(CONTEXT, context_id=b'opaque-\xff')).kernel_sha256
    s = visible_schema(kernel)
    def tensorized(k, value):
        return a.tensorize_association_observations(k, (OVERFLOW_OBSERVATION,), schema=s,
            task_ids=('association',), static_contexts=((value,),))
    one, two = tensorized(first, 1e100), tensorized(second, 1e101)
    assert torch.equal(one.retained.static_context_features, two.retained.static_context_features)
    assert one.retained.task_context_sha256s != two.retained.task_context_sha256s
    with pytest.raises(a.AssociationTrainingError, match='static context'):
        tensorized(first, 1e101)
    _, model = models(kernel, METHODS[0])
    small = tensorized(declared(0.25), 0.25)
    other = tensorized(declared(-0.5), -0.5)
    # An encoder can inspect both declared batches; the model's kernel guard is separate.
    assert not torch.equal(model.encoder(small), model.encoder(other))
    for schema, tasks in ((replace(s, domain_id='online-retail-ii'), ('association',)), (s, ('wrong-task',))):
        with pytest.raises(a.AssociationTrainingError, match='domain/task'):
            a.tensorize_association_observations(kernel, ((),), schema=schema,
                task_ids=tasks, static_contexts=((0.25,),))


def test_oracle_rejects_non_fp32_and_second_derivative_is_not_claimed(kernel):
    state = (TransformedEvent(0, (0.25,)),)
    outcome = (TransformedEvent(10, (0.4,)),)
    callback = kernel.torch_baseline(outcome, propagated=False)
    with pytest.raises(a.AssociationTrainingError, match='CPU FP32'):
        callback(0.1, state, (torch.tensor([[0.25]], dtype=torch.float64), torch.empty(0, 0)))
    with pytest.raises(a.AssociationTrainingError, match='CPU FP32'):
        callback(0.1, state, (torch.tensor([[float('nan')]]), torch.empty(0, 0)))
    coordinates = (torch.tensor([[0.25]], requires_grad=True), torch.empty(0, 0, requires_grad=True))
    first = torch.autograd.grad(callback(0.1, state, coordinates), coordinates, create_graph=True)[0]
    with pytest.raises(RuntimeError):
        torch.autograd.grad(first.sum(), coordinates)


@pytest.mark.parametrize('component', ['value', 'gradient'])
def test_finite_binary64_oracle_output_must_remain_finite_after_fp32_cast(kernel, monkeypatch, component):
    def oversized(self, reverse_time, state, observation, *, propagated):
        return (1e100 if component == 'value' else 0.0,
                ((1e100 if component == 'gradient' else 0.0,),))
    monkeypatch.setattr(a.NormalizedAssociationTrainingKernel, 'log_value_and_gradient', oversized)
    callback = kernel.torch_baseline((), propagated=False)
    with pytest.raises(a.AssociationTrainingError, match='not representable in FP32'):
        callback(0.125, (TransformedEvent(0, (0.25,)),),
                 (torch.tensor([[0.25]], requires_grad=True), torch.empty(0, 0)))


@pytest.mark.parametrize('method', METHODS)
def test_two_actual_sampled_pairs_feed_oracle_paired_loss_and_one_adamw_update(kernel, method):
    process = kernel.guide.process
    base = energy(process)
    base.requires_grad_(False)
    sampler = LearnedHybridTrainingSampler(process, h.TorchHybridPotential(base, torch.zeros(1, 64)),
        HybridTrajectoryPlan((0.0, 0.125, 0.1875, 0.25)), ReferenceConfigurationInitializer())
    pairs = tuple(sampler.sample_pair(context=CONTEXT, reverse_time=0.125, run_seed=28,
        record_id=f'local-association-optimizer-{i}'.encode(), observation_law=kernel.sample_outcome)
        for i in range(2))
    assert all(p.branch_one.trajectory.diagnostics['actual_macrostep_count'] == 3
               and p.branch_two.trajectory.diagnostics['actual_macrostep_count'] == 3 for p in pairs)
    states = tuple(p.joint_pair[0] for p in pairs)
    assert states == tuple(p.product_pair[0] for p in pairs)
    times = tuple(p.reverse_time for p in pairs)
    _, current = models(kernel, method)
    propagated = h.BASELINE_KIND_BY_METHOD[method] == 'ANALYTIC_PROPAGATED_GUIDE_LOG'

    def logit_batch(outcomes):
        values = tuple(kernel.log_value_and_gradient(u, state, obs, propagated=propagated)[0]
                       for u, state, obs in zip(times, states, outcomes))
        return a.AssociationLogitBatch(states, times, visible(kernel, outcomes),
            torch.tensor(values, dtype=torch.float32), h.BASELINE_KIND_BY_METHOD[method])

    joint = logit_batch(tuple(p.joint_pair[1] for p in pairs))
    product = logit_batch(tuple(p.product_pair[1] for p in pairs))
    optimizer = torch.optim.AdamW(current.parameters(), lr=1e-3, weight_decay=0.0)
    before = {name: value.detach().clone() for name, value in current.named_parameters()}
    optimizer.zero_grad(set_to_none=True)
    loss = a.association_joint_product_loss(current, joint, product,
        h.SamplingLawWeights.declared(law_id='LOCAL_EXPLICIT_TWO_PAIR_SYNTHETIC_ONLY', size=2))
    assert bool(torch.isfinite(loss))
    loss.backward()
    for prefix in ('conditioner.backbone', 'encoder', 'nuisance.encoder', 'nuisance.hidden'):
        parameters = [(name, value) for name, value in current.named_parameters() if name.startswith(prefix)]
        assert any(p.grad is not None and bool((p.grad != 0).any()) for _, p in parameters), prefix
        assert all(p.grad is None or bool(torch.isfinite(p.grad).all()) for _, p in parameters), prefix
    optimizer.step()
    for prefix in ('conditioner.backbone', 'encoder', 'nuisance.encoder', 'nuisance.hidden'):
        assert any(not torch.equal(before[name], value.detach())
                   for name, value in current.named_parameters() if name.startswith(prefix)), prefix
    assert all(parameter.grad is None for parameter in base.parameters())


@pytest.mark.parametrize('method', METHODS)
def test_conditional_physical_adapter_binds_oracle_role_and_runs_one_small_path(kernel, method):
    process = kernel.guide.process
    base = energy(process)
    base.requires_grad_(False)
    _, current = models(kernel, method)
    outcome = (TransformedEvent(10, (0.4,)),)
    observation = visible(kernel, (outcome,))
    propagated = method == METHODS[0]
    baseline = kernel.torch_baseline(outcome, propagated=propagated)
    bound = kernel.guide.certify_guide_range(outcome).guide_log_upper_bound
    options = dict(conditional=current, observation=observation, baseline=baseline,
                   baseline_upper_bound=float(bound))
    potential = h.TorchHybridPotential(base, torch.zeros(1, 64), **options)
    state = (TransformedEvent(0, (0.25,)), TransformedEvent(1, ()))
    value, gradient = potential.value_grad(0.125, state)
    assert value == potential.value(0.125, state)
    delta = 0.001
    numerical = (potential.value(0.125, (TransformedEvent(0, (0.25+delta,)), state[1]))
                 - potential.value(0.125, (TransformedEvent(0, (0.25-delta,)), state[1])))/(2*delta)
    assert math.isclose(gradient[0][0], numerical, rel_tol=0.02, abs_tol=5e-5)
    assert gradient[1] == ()
    initial = h.TorchHybridPotential(base, torch.zeros(1, 64), include_base=False, **options)
    initializer = h.ConditionalRejectionInitializer(initial, max_proposals=1000)
    sampler = LearnedHybridTrainingSampler(process, potential,
        HybridTrajectoryPlan((0.0, 0.125, 0.1875, 0.25)), initializer)
    path = sampler.sample_path(run_seed=75, record_id=b'synthetic-conditional-association')
    assert path.diagnostics['actual_macrostep_count'] == 3
    assert not path.diagnostics['partial_trajectory_returned']
    assert all(parameter.grad is None for parameter in base.parameters())
    with pytest.raises(h.HybridTrainingError, match='baseline role'):
        h.TorchHybridPotential(base, torch.zeros(1, 64), **dict(options,
            baseline=kernel.torch_baseline(outcome, propagated=not propagated)))
    with pytest.raises(h.HybridTrainingError, match='kernel'):
        h.TorchHybridPotential(base, torch.zeros(1, 64), **dict(options,
            observation=replace(observation, kernel_sha256='d'*64)))
