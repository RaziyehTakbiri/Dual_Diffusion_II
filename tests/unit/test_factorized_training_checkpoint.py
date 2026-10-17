"""CPU-only tests for self-produced synthetic training checkpoint bytes."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import io

import numpy as np
import pytest
import torch

from heterodiff.experiments import factorized_training_checkpoint as ck
from heterodiff.experiments.factorized_base_precision import PRECISION_POLICY
from heterodiff.experiments.factorized_device_qualification import _optimizer
from heterodiff.experiments.factorized_precision_pipeline_qualification import _fixture


METHOD = 'association-aware-guide-plus-residual'
PREFIX = 'checkpoint-codec-fixture'
SEED = 117


@pytest.fixture(scope='module', autouse=True)
def bounded_cpu_threads():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        yield
    finally:
        torch.set_num_threads(previous)


def fresh(method=METHOD):
    _, _, base, conditional, _ = _fixture('R3-PHYS', method)
    binding = {
        'precision_policy': PRECISION_POLICY, 'device': 'cpu',
        'base_architecture_sha256': base.architecture.architecture_sha256,
        'conditional_architecture_sha256': conditional.conditioner.architecture.architecture_sha256,
        'method_id': method, 'conditional_seed': SEED, 'conditional_record_prefix': PREFIX,
        'fixture': 'CPU_OPTIMIZER_CODEC_NOT_SCIENTIFIC_TRAINING',
    }
    return {'binding': binding, 'base': base, 'conditional': conditional,
            'base_optimizer': _optimizer(base), 'conditional_optimizer': _optimizer(conditional),
            'base_rng': np.random.Generator(np.random.PCG64(71))}


def step(model, optimizer, scale):
    optimizer.zero_grad(set_to_none=True)
    # A cheap true autograd loss populates every parameter's AdamW state.
    loss = sum((parameter.square().mean() * scale for parameter in model.parameters()))
    loss.backward()
    optimizer.step()
    return float(loss.detach())


def prepared(phase='BASE'):
    state = fresh()
    base_steps, conditional_steps = (2, 0) if phase == 'BASE' else (4, 2)
    for _ in range(base_steps):
        step(state['base'], state['base_optimizer'], float(state['base_rng'].uniform(.5, 1.5)))
    for i in range(conditional_steps):
        step(state['conditional'], state['conditional_optimizer'], .75 + i / 8)
    state['cursor'] = {
        'phase': phase, 'completed_base_steps': base_steps,
        'completed_conditional_steps': conditional_steps,
        'base_gradient_steps': {name: base_steps for name, _ in state['base'].named_parameters()},
        'conditional_gradient_steps': {name: conditional_steps for name, _ in state['conditional'].named_parameters()},
        'conditional_run_seed': SEED, 'conditional_record_prefix': PREFIX,
        'population_law_id': None if phase == 'BASE' else 'device-factorized-base-precision-v1-' + 'a' * 64,
    }
    return state


def encode(state):
    return ck.encode_checkpoint(**state)


def restore(payload, state, *, expected_binding=None, expected_sha256=None):
    return ck.restore_checkpoint(payload,
        expected_sha256=hashlib.sha256(payload).hexdigest() if expected_sha256 is None else expected_sha256,
        expected_binding=state['binding'] if expected_binding is None else expected_binding,
        **{key: value for key, value in state.items() if key not in ('binding', 'cursor')})


def observed(state):
    result = {'base_rng': deepcopy(state['base_rng'].bit_generator.state)}
    for key in ('base', 'conditional'):
        model = state[key]
        result[key] = {
            'weights': {name: value.detach().clone() for name, value in model.state_dict().items()},
            'gradients': {name: None if value.grad is None else value.grad.detach().clone()
                          for name, value in model.named_parameters()},
            'training': {name: value.training for name, value in model.named_modules()},
            'requires_grad': {name: value.requires_grad for name, value in model.named_parameters()},
        }
        result[key + '_optimizer'] = deepcopy(state[key + '_optimizer'].state_dict())
    return result


def assert_exact(left, right):
    assert type(left) is type(right)
    if isinstance(left, torch.Tensor):
        assert left.dtype == right.dtype and left.shape == right.shape and left.device == right.device
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert left.dtype == right.dtype and left.shape == right.shape
        assert np.array_equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            assert_exact(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert len(left) == len(right)
        for a, b in zip(left, right):
            assert_exact(a, b)
    else:
        assert left == right


@pytest.mark.parametrize('phase', ('BASE', 'CONDITIONAL'))
def test_checkpoint_round_trip_restores_exact_complete_fresh_state(phase):
    original = prepared(phase)
    before = observed(original)
    torch_rng = torch.random.get_rng_state().clone()
    payload = encode(original)
    assert type(payload) is bytes and 0 < len(payload) <= ck.MAXIMUM_CHECKPOINT_BYTES == 16 * 1024**2
    restored = fresh()
    assert not restored['base_optimizer'].state and not restored['conditional_optimizer'].state
    cursor = restore(payload, restored)
    assert cursor == original['cursor']
    assert_exact(observed(restored), before)
    assert_exact(observed(original), before)
    assert torch.equal(torch_rng, torch.random.get_rng_state())


@pytest.mark.parametrize('phase', ('BASE', 'CONDITIONAL'))
def test_continuation_after_fresh_restore_matches_each_loss_rng_gradient_and_optimizer_tensor(phase):
    original = prepared(phase)
    restored = fresh()
    cursor = restore(encode(original), restored)
    for _ in range(cursor['completed_base_steps'], 4):
        scales = [float(state['base_rng'].uniform(.5, 1.5)) for state in (original, restored)]
        assert scales[0] == scales[1]
        losses = [step(state['base'], state['base_optimizer'], scale)
                  for state, scale in zip((original, restored), scales)]
        assert losses[0] == losses[1]
        assert_exact(observed(original), observed(restored))
    for i in range(cursor['completed_conditional_steps'], 4):
        losses = [step(state['conditional'], state['conditional_optimizer'], .75 + i / 8)
                  for state in (original, restored)]
        assert losses[0] == losses[1]
        assert_exact(observed(original), observed(restored))


@pytest.mark.parametrize('defect', ('wrong_sha', 'tampered', 'not_bytes', 'empty', 'oversized'))
def test_invalid_bytes_rejected_before_restricted_decode_or_target_mutation(monkeypatch, defect):
    payload = encode(prepared())
    target = fresh()
    before = observed(target)
    expected_sha = hashlib.sha256(payload).hexdigest()
    if defect == 'wrong_sha':
        expected_sha = '0' * 64
    elif defect == 'tampered':
        payload = bytes([payload[0] ^ 1]) + payload[1:]
    elif defect == 'not_bytes':
        payload = bytearray(payload)
    elif defect == 'empty':
        payload = b''
    else:
        payload = b'x' * (ck.MAXIMUM_CHECKPOINT_BYTES + 1)
    def forbidden(*_args, **_kwargs):
        pytest.fail('invalid checkpoint reached torch.load')
    monkeypatch.setattr(torch, 'load', forbidden)
    with pytest.raises(ck.FactorizedCheckpointError):
        restore(payload, target, expected_sha256=expected_sha)
    assert_exact(observed(target), before)


def test_restricted_deserialization_is_explicit_and_cpu_only(monkeypatch):
    payload = encode(prepared())
    original_load = torch.load
    calls = []
    def inspected_load(*args, **kwargs):
        calls.append(kwargs)
        assert kwargs.get('weights_only') is True
        assert kwargs.get('map_location') == 'cpu'
        return original_load(*args, **kwargs)
    monkeypatch.setattr(torch, 'load', inspected_load)
    restore(payload, fresh())
    assert len(calls) == 1


@pytest.mark.parametrize('field,value', (
    ('precision_policy', 'LEGACY_FP32'), ('device', 'cuda:0'),
    ('base_architecture_sha256', '0' * 64), ('conditional_architecture_sha256', '0' * 64),
    ('method_id', 'unified-direct-conditioner'), ('conditional_seed', SEED + 1),
    ('conditional_record_prefix', 'changed-prefix'), ('fixture', 'changed-fixture'),
))
def test_cross_binding_rejected_without_partial_fresh_target_mutation(field, value):
    payload = encode(prepared())
    target = fresh()
    before = observed(target)
    binding = deepcopy(target['binding'])
    binding[field] = value
    with pytest.raises(ck.FactorizedCheckpointError):
        restore(payload, target, expected_binding=binding)
    assert_exact(observed(target), before)


def test_missing_mandatory_binding_is_rejected():
    state = prepared()
    state['binding'].pop('precision_policy')
    with pytest.raises(ck.FactorizedCheckpointError):
        encode(state)


@pytest.mark.parametrize('defect', (
    'existing_optimizer_state', 'existing_gradient', 'wrong_optimizer_order',
    'wrong_optimizer_settings', 'wrong_method_target', 'wrong_rng_algorithm',
))
def test_restore_requires_unmodified_fresh_owned_targets(defect):
    payload = encode(prepared())
    target = fresh('unified-direct-conditioner' if defect == 'wrong_method_target' else METHOD)
    if defect == 'existing_optimizer_state':
        step(target['base'], target['base_optimizer'], .75)
        target['base_optimizer'].zero_grad(set_to_none=True)
    elif defect == 'existing_gradient':
        next(target['base'].parameters()).grad = torch.ones_like(next(target['base'].parameters()))
    elif defect == 'wrong_optimizer_order':
        target['base_optimizer'].param_groups[0]['params'].reverse()
    elif defect == 'wrong_optimizer_settings':
        target['base_optimizer'].param_groups[0]['lr'] *= 2
    elif defect == 'wrong_rng_algorithm':
        target['base_rng'] = np.random.Generator(np.random.Philox(71))
    before = observed(target)
    with pytest.raises(ck.FactorizedCheckpointError):
        restore(payload, target)
    assert_exact(observed(target), before)


def unpack(payload):
    return torch.load(io.BytesIO(payload), map_location='cpu', weights_only=True)


def pack(record):
    stream = io.BytesIO()
    torch.save(record, stream)
    return stream.getvalue()


@pytest.mark.parametrize('defect', (
    'nonfinite_weight', 'wrong_weight_dtype', 'nonfinite_gradient', 'missing_moment',
    'nonfinite_moment', 'wrong_moment_dtype', 'wrong_step', 'extra_optimizer_state',
    'missing_gradient_counter', 'incorrect_gradient_counter', 'unknown_phase',
    'negative_step', 'premature_conditional', 'BASE_with_population',
    'CONDITIONAL_without_population', 'wrong_record_prefix', 'wrong_conditional_seed',
    'wrong_rng_algorithm',
))
def test_encode_rejects_incomplete_nonfinite_or_inconsistent_training_state(defect):
    state = prepared('CONDITIONAL' if defect == 'CONDITIONAL_without_population' else 'BASE')
    first_name, first = next(iter(state['base'].named_parameters()))
    optimizer_state = state['base_optimizer'].state[first]
    if defect == 'nonfinite_weight':
        with torch.no_grad():
            first.reshape(-1)[0] = float('nan')
    elif defect == 'wrong_weight_dtype':
        first.data = first.data.double()
    elif defect == 'nonfinite_gradient':
        first.grad.reshape(-1)[0] = float('inf')
    elif defect == 'missing_moment':
        optimizer_state.pop('exp_avg')
    elif defect == 'nonfinite_moment':
        optimizer_state['exp_avg'].reshape(-1)[0] = float('nan')
    elif defect == 'wrong_moment_dtype':
        optimizer_state['exp_avg'] = optimizer_state['exp_avg'].double()
    elif defect == 'wrong_step':
        optimizer_state['step'].fill_(3)
    elif defect == 'extra_optimizer_state':
        optimizer_state['unknown'] = torch.tensor(1.)
    elif defect == 'missing_gradient_counter':
        state['cursor']['base_gradient_steps'].pop(first_name)
    elif defect == 'incorrect_gradient_counter':
        state['cursor']['base_gradient_steps'][first_name] = 1
    elif defect == 'unknown_phase':
        state['cursor']['phase'] = 'UNKNOWN'
    elif defect == 'negative_step':
        state['cursor']['completed_base_steps'] = -1
    elif defect == 'premature_conditional':
        state['cursor']['completed_conditional_steps'] = 1
    elif defect == 'BASE_with_population':
        state['cursor']['population_law_id'] = 'device-factorized-base-precision-v1-' + 'a' * 64
    elif defect == 'CONDITIONAL_without_population':
        state['cursor']['population_law_id'] = None
    elif defect == 'wrong_record_prefix':
        state['cursor']['conditional_record_prefix'] = 'other-prefix'
    elif defect == 'wrong_conditional_seed':
        state['cursor']['conditional_run_seed'] += 1
    else:
        state['base_rng'] = np.random.Generator(np.random.Philox(71))
    with pytest.raises(ck.FactorizedCheckpointError):
        encode(state)


@pytest.mark.parametrize('defect', (
    'missing_model', 'missing_gradient', 'missing_parameter', 'gradient_shape',
    'nonfinite_model', 'nonfinite_moment', 'negative_second_moment', 'missing_moment',
    'wrong_step', 'missing_counter', 'changed_optimizer_lr', 'unknown_scope',
    'production_flag', 'wrong_PCGenerator', 'missing_rng_cache', 'invalid_rng_cache',
    'even_rng_increment', 'missing_cursor', 'unexpected_top_level', 'reordered_parameters',
))
def test_rehashed_self_produced_malformed_payload_cannot_partially_mutate_targets(defect):
    record = unpack(encode(prepared()))
    base = record['models']['base']
    name = base['parameter_names'][0]
    optimizer = record['optimizers']['base']
    index = optimizer['param_groups'][0]['params'][0]
    adam = optimizer['state'][index]
    if defect == 'missing_model':
        record['models'].pop('conditional')
    elif defect == 'missing_gradient':
        base['gradients'].pop(name)
    elif defect == 'missing_parameter':
        base['state'].pop(name)
    elif defect == 'gradient_shape':
        base['gradients'][name] = torch.zeros(1, dtype=torch.float32)
    elif defect == 'nonfinite_model':
        base['state'][name].reshape(-1)[0] = float('nan')
    elif defect == 'nonfinite_moment':
        adam['exp_avg'].reshape(-1)[0] = float('inf')
    elif defect == 'negative_second_moment':
        adam['exp_avg_sq'].reshape(-1)[0] = -1.
    elif defect == 'missing_moment':
        adam.pop('exp_avg')
    elif defect == 'wrong_step':
        adam['step'].fill_(1)
    elif defect == 'missing_counter':
        record['cursor']['base_gradient_steps'].pop(name)
    elif defect == 'changed_optimizer_lr':
        optimizer['param_groups'][0]['lr'] *= 2
    elif defect == 'unknown_scope':
        record['scope'] = 'OTHER'
    elif defect == 'production_flag':
        record['production_resume_permitted'] = True
    elif defect == 'wrong_PCGenerator':
        record['base_rng']['bit_generator'] = 'Philox'
    elif defect == 'missing_rng_cache':
        record['base_rng'].pop('has_uint32')
    elif defect == 'invalid_rng_cache':
        record['base_rng']['has_uint32'] = 3
    elif defect == 'even_rng_increment':
        record['base_rng']['state']['inc'] = 2
    elif defect == 'missing_cursor':
        record.pop('cursor')
    elif defect == 'unexpected_top_level':
        record['unexpected'] = True
    else:
        base['parameter_names'] = tuple(reversed(base['parameter_names']))
    target = fresh()
    before = observed(target)
    payload = pack(record)
    with pytest.raises(ck.FactorizedCheckpointError):
        restore(payload, target)
    assert_exact(observed(target), before)


def test_mid_install_failure_rolls_fresh_targets_back_exactly(monkeypatch):
    payload = encode(prepared('CONDITIONAL'))
    target = fresh()
    before = observed(target)
    original_install = ck._install
    interrupted = False
    def fail_once(value, base, conditional, base_optimizer, conditional_optimizer, base_rng):
        nonlocal interrupted
        if base is target['base'] and not interrupted:
            interrupted = True
            with torch.no_grad():
                next(base.parameters()).add_(123.)
            raise RuntimeError('simulated partial live install')
        return original_install(value, base, conditional, base_optimizer, conditional_optimizer, base_rng)
    monkeypatch.setattr(ck, '_install', fail_once)
    with pytest.raises(ck.FactorizedCheckpointError, match='fresh target state restored'):
        restore(payload, target)
    assert interrupted
    assert_exact(observed(target), before)


def test_cached_uint32_rng_word_is_preserved_for_exact_next_draw():
    source = prepared()
    source['base_rng'].integers(0, 2**32, dtype=np.uint32)
    assert source['base_rng'].bit_generator.state['has_uint32'] == 1
    target = fresh()
    restore(encode(source), target)
    assert source['base_rng'].bit_generator.state == target['base_rng'].bit_generator.state
    assert source['base_rng'].integers(0, 2**32, dtype=np.uint32) == target['base_rng'].integers(0, 2**32, dtype=np.uint32)
    assert np.array_equal(source['base_rng'].standard_normal(12), target['base_rng'].standard_normal(12))


def test_current_none_gradient_does_not_discard_previous_adamw_history():
    source = prepared('CONDITIONAL')
    name, parameter = next(iter(source['conditional'].named_parameters()))
    parameter.grad = None
    assert source['conditional_optimizer'].state[parameter]['step'].item() == 2
    target = fresh()
    cursor = restore(encode(source), target)
    restored_parameter = dict(target['conditional'].named_parameters())[name]
    assert restored_parameter.grad is None
    assert cursor['conditional_gradient_steps'][name] == 2
    assert target['conditional_optimizer'].state[restored_parameter]['step'].item() == 2
    assert_exact(observed(source), observed(target))
    assert step(source['conditional'], source['conditional_optimizer'], 1.25) == step(
        target['conditional'], target['conditional_optimizer'], 1.25)
    assert_exact(observed(source), observed(target))


def full_binding(state):
    from heterodiff.experiments import factorized_multistep_checkpoint_qualification as qualification
    binding = qualification._binding(qualification._new_state('R3-PHYS', METHOD))
    binding['conditional_seed'] = state['cursor']['conditional_run_seed']
    binding['conditional_record_prefix'] = state['cursor']['conditional_record_prefix']
    return binding


@pytest.mark.parametrize('defect', (
    'callback', 'clean_hold', 'clock_horizon', 'bound_schedule', 'optimizer_metadata', 'step_schedule',
))
def test_full_scientific_binding_rejects_clock_or_schedule_drift_before_decode(monkeypatch, defect):
    source = prepared()
    source['binding'] = full_binding(source)
    payload = encode(source)
    target = fresh()
    target['binding'] = deepcopy(source['binding'])
    if defect == 'callback':
        target['conditional'].remaining_clocks = lambda _: (0., 0.)
    elif defect == 'clean_hold':
        target['conditional'].clean_hold += .125
    elif defect == 'clock_horizon':
        schedule = target['conditional'].remaining_clocks.__self__
        target['conditional'].remaining_clocks = replace(schedule, horizon=2.).remaining_clocks
    elif defect == 'bound_schedule':
        target['binding']['training_schedule']['schedule']['jump_rate'] += .125
    elif defect == 'optimizer_metadata':
        target['binding']['optimizer_policy']['lr'] *= 2
    else:
        target['binding']['training_schedule']['base_steps'] = 3
    before = observed(target)
    def forbidden(*_args, **_kwargs):
        pytest.fail('invalid live scientific binding reached restricted decode')
    monkeypatch.setattr(torch, 'load', forbidden)
    with pytest.raises(ck.FactorizedCheckpointError):
        restore(payload, target)
    assert_exact(observed(target), before)
