"""Bounded CPU tests for explicit BASE precision population/sampling routing.

Separate precision identities intentionally select separate keyed streams;
same integer seeds are not represented as cross-policy coupling evidence.
"""
from copy import deepcopy

import pytest
import torch

from heterodiff.experiments import factorized_device_training as training
from heterodiff.experiments.factorized_base_precision import PRECISION_POLICY
from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy
from tests.unit.test_factorized_device_training import fixture, adam


DOMAINS = ('R3-PHYS', 'R4-RETAIL')
METHODS = ('association-aware-guide-plus-residual', 'unified-direct-conditioner')
GRID = (0., .25, .5, .75, 1.)


@pytest.fixture(autouse=True)
def one_cpu_thread():
    before = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(before)


def setup(domain='R3-PHYS', method=METHODS[0]):
    source, reference, base, learner, context = fixture(domain, method)
    return (source, reference, DeviceFactorizedEnergy.from_cpu(base, 'cpu'),
            training.DeviceFactorizedConditionalModel.from_cpu(learner, 'cpu'), context)


def population(base, reference, context, policy):
    return training.DeviceFactorizedBasePopulation(base, reference, GRID, context,
                                                    precision_policy=policy)


def pair(pop):
    return pop.sample_pair(reverse_time=.5, run_seed=501, record_id=b'precision-pair')


@pytest.mark.parametrize('domain', DOMAINS)
def test_candidate_population_identity_diagnostics_and_replay_not_legacy_stream_coupling(domain):
    _, reference, base, _, context = setup(domain)
    candidate = population(base, reference, context, PRECISION_POLICY)
    legacy = population(base, reference, context, 'LEGACY_FP32')
    assert candidate.precision_policy == candidate.physical.precision_policy == PRECISION_POLICY
    assert candidate.law_id.startswith('device-factorized-base-precision-v1-')
    assert candidate.law_id != legacy.law_id
    first, repeated, old = pair(candidate), pair(candidate), pair(legacy)
    assert first == repeated
    joint, product, paths = first
    assert joint.law_id == product.law_id and joint.law_id.startswith(candidate.law_id)
    assert joint.states == product.states == (paths[0].at_time(.5),)
    candidate_streams = tuple(p.diagnostics['stream_binding_sha256'] for p in paths)
    legacy_streams = tuple(p.diagnostics['stream_binding_sha256'] for p in old[2])
    assert len(set(candidate_streams)) == 2
    assert set(candidate_streams).isdisjoint(legacy_streams)
    # No assertion that different streams must produce different visible states.
    for path in paths:
        assert path.diagnostics['base_precision_policy'] == PRECISION_POLICY
        assert path.diagnostics['precision_policy_bound_in_population_law_id'] is True
        assert path.diagnostics['legacy_common_random_streams_claimed'] is False
        assert path.diagnostics['exact_learned_path_or_finite_rng_law_claimed'] is False
        assert path.states[-1] is path.states[-2]
    with pytest.raises(AttributeError):
        candidate.precision_policy = 'LEGACY_FP32'
    assert candidate.precision_policy == PRECISION_POLICY


@pytest.mark.parametrize('domain', DOMAINS)
def test_population_snapshot_isolated_from_later_source_model_changes(domain):
    _, reference, base, _, context = setup(domain)
    candidate = population(base, reference, context, PRECISION_POLICY)
    before_weights = deepcopy(candidate.physical.base.state_dict())
    before_law, before_draw = candidate.law_id, pair(candidate)
    with torch.no_grad():
        base.readout_output.bias.add_(1.)
    assert candidate.law_id == before_law and pair(candidate) == before_draw
    assert all(torch.equal(value, candidate.physical.base.state_dict()[name])
               for name, value in before_weights.items())
    successor = population(base, reference, context, PRECISION_POLICY)
    assert successor.law_id != before_law


@pytest.mark.parametrize('domain', DOMAINS)
@pytest.mark.parametrize('method', METHODS)
def test_conditional_update_keeps_candidate_population_policy_and_frozen_base(domain, method):
    _, reference, base, learner, context = setup(domain, method)
    candidate = population(base, reference, context, PRECISION_POLICY)
    before_base = deepcopy(base.state_dict())
    before_snapshot = deepcopy(candidate.physical.base.state_dict())
    before_rng = torch.random.get_rng_state().clone()
    result = training.device_train_conditional_step(learner, candidate, optimizer=adam(learner),
        reverse_time=.5, run_seed=501, record_id=b'precision-conditional-update', sample_count=1)
    assert result['base_precision_policy'] == PRECISION_POLICY
    assert result['law_id'].startswith(candidate.law_id)
    assert result['changed_parameter_elements'] > 0 and result['base_paths_generated'] == 2
    assert result['scientific_training_completed'] is False
    assert candidate.physical.precision_policy == PRECISION_POLICY
    assert all(torch.equal(value, base.state_dict()[name]) for name, value in before_base.items())
    assert all(torch.equal(value, candidate.physical.base.state_dict()[name])
               for name, value in before_snapshot.items())
    assert all(p.dtype == torch.float32 and (p.grad is None or p.grad.dtype == torch.float32)
               for p in learner.parameters())
    assert torch.equal(before_rng, torch.random.get_rng_state())


@pytest.mark.parametrize('domain', DOMAINS)
@pytest.mark.parametrize('method', METHODS)
def test_candidate_conditional_sampler_policy_replay_rng_and_source_isolation(domain, method):
    source, reference, base, learner, context = setup(domain, method)
    before_base, before_learner = deepcopy(base.state_dict()), deepcopy(learner.state_dict())
    before_rng = torch.random.get_rng_state().clone()
    kwargs = dict(run_seed=502, record_id=b'precision-conditional-sample')
    candidate = training.device_sample_conditional(base, learner, reference, GRID, context,
        (source[-1],), precision_policy=PRECISION_POLICY, **kwargs)
    repeated = training.device_sample_conditional(base, learner, reference, GRID, context,
        (source[-1],), precision_policy=PRECISION_POLICY, **kwargs)
    legacy = training.device_sample_conditional(base, learner, reference, GRID, context,
        (source[-1],), precision_policy='LEGACY_FP32', **kwargs)
    assert candidate == repeated
    diagnostics = candidate.diagnostics
    assert diagnostics['base_precision_policy'] == PRECISION_POLICY
    assert diagnostics['conditioner_precision_policy'] == 'LEGACY_FP32'
    assert diagnostics['precision_policy_bound_in_stream_namespace'] is True
    assert diagnostics['legacy_common_random_streams_claimed'] is False
    assert diagnostics['production_precision_policy_adopted'] is False
    assert diagnostics['stream_binding_sha256'] != legacy.diagnostics['stream_binding_sha256']
    assert candidate.states[-1] is candidate.states[-2]
    assert torch.equal(before_rng, torch.random.get_rng_state())
    assert all(torch.equal(value, base.state_dict()[name]) for name, value in before_base.items())
    assert all(torch.equal(value, learner.state_dict()[name]) for name, value in before_learner.items())


@pytest.mark.parametrize('domain', DOMAINS)
@pytest.mark.parametrize('method', METHODS)
def test_default_and_explicit_legacy_population_and_sampler_records_are_exact(domain, method):
    source, reference, base, learner, context = setup(domain, method)
    default = training.DeviceFactorizedBasePopulation(base, reference, GRID, context)
    explicit = population(base, reference, context, 'LEGACY_FP32')
    assert default.law_id == explicit.law_id and pair(default) == pair(explicit)
    assert default.precision_policy == explicit.precision_policy == 'LEGACY_FP32'
    kwargs = dict(run_seed=502, record_id=b'legacy-still-exact')
    default_draw = training.device_sample_conditional(base, learner, reference, GRID, context,
                                                      (source[-1],), **kwargs)
    explicit_draw = training.device_sample_conditional(base, learner, reference, GRID, context,
        (source[-1],), precision_policy='LEGACY_FP32', **kwargs)
    assert default_draw == explicit_draw
    assert 'base_precision_policy' not in default_draw.diagnostics
    assert all('base_precision_policy' not in p.diagnostics for p in pair(default)[2])


class StringSubclass(str):
    pass


@pytest.mark.parametrize('bad', ('AUTO', '', None, 1, True, ['LEGACY_FP32'], StringSubclass('LEGACY_FP32')))
@pytest.mark.parametrize('entry', ('population', 'conditional_sampler'))
def test_invalid_policy_rejected_before_snapshot_initialization_or_sampling(monkeypatch, bad, entry):
    source, reference, base, learner, context = setup()
    def forbidden(*_args, **_kwargs):
        pytest.fail('invalid precision policy reached numerical or sampling work')
    monkeypatch.setattr(training, 'deepcopy', forbidden)
    monkeypatch.setattr(training, 'conditional_initializer', forbidden)
    monkeypatch.setattr(training, 'LearnedFactorizedSampler', forbidden)
    with pytest.raises(ValueError):
        if entry == 'population':
            population(base, reference, context, bad)
        else:
            training.device_sample_conditional(base, learner, reference, GRID, context,
                (source[-1],), run_seed=502, record_id=b'bad-policy', precision_policy=bad)


@pytest.mark.parametrize('entry', ('sample_pair', 'conditional_update'))
def test_population_physical_policy_cross_binding_rejected_before_paths_or_update(monkeypatch, entry):
    _, reference, base, learner, context = setup()
    candidate = population(base, reference, context, PRECISION_POLICY)
    candidate.physical._precision_policy = 'LEGACY_FP32'  # Deliberately corrupt the private binding.
    before = deepcopy(learner.state_dict())
    optimizer = adam(learner)
    def forbidden(*_args, **_kwargs):
        pytest.fail('mismatched population precision binding reached path sampling')
    monkeypatch.setattr(training.FactorizedBasePopulation, 'sample_pair', forbidden)
    with pytest.raises(ValueError, match='precision policy mismatch'):
        if entry == 'sample_pair':
            pair(candidate)
        else:
            training.device_train_conditional_step(learner, candidate, optimizer=optimizer,
                reverse_time=.5, run_seed=501, record_id=b'bad-binding', sample_count=1)
    assert not optimizer.state
    assert all(torch.equal(value, learner.state_dict()[name]) for name, value in before.items())
