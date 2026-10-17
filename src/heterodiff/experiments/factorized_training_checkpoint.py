"""Bounded CPU-only checkpoints for the local synthetic four-plus-four check.

This is a new local resume protocol, not the older inspection-only checkpoint
format and not production/external checkpoint admission. Only trusted,
self-produced bytes with an independently retained expected SHA256 are loaded.
Restricted ``weights_only`` decoding does not establish provenance or make
arbitrary downloaded files safe. No global RNG, data loader, dropout, CUDA or
distributed-process state is supported or claimed here.
"""
from copy import deepcopy
import hashlib
import hmac
from io import BytesIO
import json
import math
import platform
import re
import zipfile

import numpy as np
import torch

from heterodiff.experiments.factorized_base_precision import PRECISION_POLICY
from heterodiff.experiments.factorized_device_training import DeviceFactorizedConditionalModel
from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy
from heterodiff.processes.factorized_hybrid_sampler import FactorizedSchedule


SCHEMA_VERSION = 'factorized-training-checkpoint-v1'
SCOPE = 'LOCAL_SYNTHETIC_FACTORIZED_TRAINING_RESUME_ONLY'
MAXIMUM_CHECKPOINT_BYTES = 16 * 1024**2
CURSOR_KEYS = {'phase', 'completed_base_steps', 'completed_conditional_steps',
               'base_gradient_steps', 'conditional_gradient_steps', 'conditional_run_seed',
               'conditional_record_prefix', 'population_law_id'}
PAYLOAD_KEYS = {'schema_version', 'scope', 'production_resume_permitted', 'binding',
                'cursor', 'models', 'optimizers', 'base_rng'}
MODEL_KEYS = {'state', 'gradients', 'parameter_names', 'requires_grad', 'training_modes'}


class FactorizedCheckpointError(ValueError):
    """Invalid, incompatible or incomplete local checkpoint; never a retry."""


def _need(condition, message):
    if not condition:
        raise FactorizedCheckpointError(message)


def _sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def _json_binding(value):
    """Bounded plain JSON metadata; no executable factory/classes in archives."""
    items = 0
    def inspect(item, depth):
        nonlocal items
        items += 1
        _need(depth <= 12 and items <= 4096, 'binding structure limit exceeded')
        if item is None or type(item) is bool:
            return
        if type(item) is int:
            _need(abs(item) < 2**128, 'binding integer limit exceeded')
        elif type(item) is float:
            _need(math.isfinite(item), 'nonfinite binding number')
        elif type(item) is str:
            _need(len(item.encode('utf-8')) <= 4096, 'binding string limit exceeded')
        elif type(item) is list:
            for child in item:
                inspect(child, depth + 1)
        elif type(item) is dict:
            _need(all(type(key) is str for key in item), 'binding keys must be strings')
            for key, child in item.items():
                inspect(key, depth + 1)
                inspect(child, depth + 1)
        else:
            raise FactorizedCheckpointError('binding must contain plain JSON primitives only')
    _need(type(value) is dict, 'binding must be a plain mapping')
    inspect(value, 0)
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    _need(len(encoded.encode()) <= 65536, 'binding byte limit exceeded')
    return encoded


def _safe_clone(value):
    """Primitive containers and finite dense CPU tensors, with total budgets."""
    count, tensor_bytes, tensor_count = 0, 0, 0
    def clone(item, depth):
        nonlocal count, tensor_bytes, tensor_count
        count += 1
        _need(depth <= 16 and count <= 100000, 'checkpoint tree limit exceeded')
        if item is None or type(item) is bool:
            return item
        if type(item) is int:
            # Explicit PCG64 state/stream increments are unsigned128, not JSON53.
            _need(abs(item) < 2**128, 'checkpoint integer limit exceeded')
            return item
        if type(item) is float:
            _need(math.isfinite(item), 'nonfinite checkpoint scalar')
            return item
        if type(item) is str:
            _need(len(item.encode('utf-8')) <= 65536, 'checkpoint string limit exceeded')
            return item
        if type(item) is torch.Tensor:
            _need(item.device.type == 'cpu' and item.layout == torch.strided
                  and item.dtype == torch.float32 and not item.is_quantized,
                  'checkpoint tensors must be dense CPU FP32')
            tensor_count += 1
            tensor_bytes += item.numel() * item.element_size()
            _need(tensor_count <= 2048 and tensor_bytes <= MAXIMUM_CHECKPOINT_BYTES,
                  'checkpoint tensor budget exceeded')
            _need(bool(torch.isfinite(item).all()), 'nonfinite checkpoint tensor')
            return item.detach().clone().contiguous()
        if type(item) is dict:
            _need(all(type(key) in (str, int) for key in item), 'checkpoint mapping key type invalid')
            return {clone(key, depth + 1): clone(child, depth + 1) for key, child in item.items()}
        if type(item) in (list, tuple):
            children = [clone(child, depth + 1) for child in item]
            return children if type(item) is list else tuple(children)
        raise FactorizedCheckpointError('unsupported checkpoint object type')
    return clone(value, 0)


def _same(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is torch.Tensor:
        return left.dtype == right.dtype and left.shape == right.shape and torch.equal(left, right)
    if type(left) is dict:
        return left.keys() == right.keys() and all(_same(left[key], right[key]) for key in left)
    if type(left) in (tuple, list):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return left == right


def _live_model(model, cls):
    _need(type(model) is cls and str(model.device) == 'cpu', 'exact CPU device model required')
    parameters = dict(model.named_parameters())
    _need(bool(parameters), 'empty model parameter roster')
    for parameter in parameters.values():
        _need(parameter.dtype == torch.float32 and parameter.device.type == 'cpu'
              and parameter.layout == torch.strided and bool(torch.isfinite(parameter).all()),
              'model parameter dtype/device/finite mismatch')
    _need(all(type(flag) is bool for flag in (module.training for module in model.modules())),
          'model training mode invalid')
    return parameters


def _binding(binding, base, conditional):
    canonical = _json_binding(binding)
    _live_model(base, DeviceFactorizedEnergy)
    _live_model(conditional, DeviceFactorizedConditionalModel)
    _need(conditional.residual_gate_policy == 'LEGACY_CUBIC_V1',
          'legacy checkpoint format does not bind the successor residual gate or common-grid law')
    expected = {'precision_policy': PRECISION_POLICY, 'device': 'cpu',
                'base_architecture_sha256': base.architecture.architecture_sha256,
                'conditional_architecture_sha256': conditional.conditioner.architecture.architecture_sha256,
                'method_id': conditional.method_id}
    _need(all(key in binding and type(binding[key]) is str and binding[key] == value
              for key, value in expected.items()), 'live model/architecture/method/precision binding mismatch')
    optional = {'torch_version': str(torch.__version__), 'numpy_version': str(np.__version__),
                'python_version': platform.python_version(),
                'reference_sha256': conditional.guide.identity_sha256}
    _need(all(key not in binding or binding[key] == value for key, value in optional.items()),
          'runtime or reference binding mismatch')
    _need(base.architecture == conditional.conditioner.architecture,
          'BASE and conditional architecture mismatch')
    schedule_binding = binding.get('training_schedule')
    if type(schedule_binding) is dict and 'schedule' in schedule_binding:
        schedule = schedule_binding['schedule']
        fields = {'horizon', 'clean_hold', 'jump_rate', 'continuous_rate'}
        _need(type(schedule) is dict and set(schedule) == fields,
              'reference schedule binding schema mismatch')
        callback = conditional.remaining_clocks
        owner = getattr(callback, '__self__', None)
        _need(type(owner) is FactorizedSchedule
              and getattr(callback, '__func__', None) is FactorizedSchedule.remaining_clocks,
              'exact reference-owned schedule callback required')
        live = {key: getattr(owner, key) for key in fields}
        _need(all(type(value) in (float, int) and math.isfinite(value)
                  for value in live.values())
              and 0 <= owner.clean_hold < owner.horizon
              and owner.jump_rate >= 0 and owner.continuous_rate >= 0,
              'live reference schedule invalid')
        _need(_same(schedule, live), 'live reference schedule binding mismatch')
        _need(type(conditional.horizon) in (float, int)
              and type(conditional.clean_hold) in (float, int)
              and conditional.horizon == owner.horizon
              and conditional.clean_hold == owner.clean_hold
              and base.architecture.horizon == owner.horizon,
              'conditional horizon/clean-hold binding mismatch')
    return canonical


def _cursor(cursor, binding, base, conditional):
    _need(type(cursor) is dict and set(cursor) == CURSOR_KEYS, 'checkpoint cursor roster mismatch')
    phase = cursor['phase']
    b, c = cursor['completed_base_steps'], cursor['completed_conditional_steps']
    _need(type(phase) is str and phase in ('BASE', 'CONDITIONAL'), 'checkpoint phase invalid')
    _need(type(b) is int and type(c) is int and 0 <= b <= 4 and 0 <= c <= 4,
          'checkpoint phase step count invalid')
    if phase == 'BASE':
        _need(b < 4 and c == 0 and cursor['population_law_id'] is None,
              'BASE checkpoint has conditional work or frozen population')
    else:
        law = cursor['population_law_id']
        _need(b == 4 and type(law) is str and re.fullmatch(
            'device-factorized-base-precision-v1-[0-9a-f]{64}', law) is not None,
            'conditional checkpoint lacks completed BASE or candidate population identity')
    for name, model, completed in (('base_gradient_steps', base, b),
                                    ('conditional_gradient_steps', conditional, c)):
        counts = cursor[name]
        _need(type(counts) is dict and counts.keys() == dict(model.named_parameters()).keys()
              and all(type(value) is int and 0 <= value <= completed for value in counts.values()),
              'per-parameter gradient-step counters invalid')
    seed, prefix = cursor['conditional_run_seed'], cursor['conditional_record_prefix']
    _need(type(seed) is int and 0 <= seed < 2**64 and type(prefix) is str
          and 0 < len(prefix) <= 256 and prefix.isascii(), 'conditional stream cursor invalid')
    _need('conditional_seed' not in binding or binding['conditional_seed'] == seed,
          'conditional seed differs from binding')
    _need('conditional_record_prefix' not in binding or binding['conditional_record_prefix'] == prefix,
          'conditional record prefix differs from binding')


def _rng_state(rng, supplied=None):
    _need(type(rng) is np.random.Generator and type(rng.bit_generator) is np.random.PCG64,
          'explicit PCG64 Generator required for BASE continuation')
    state = deepcopy(rng.bit_generator.state) if supplied is None else supplied
    _need(type(state) is dict and set(state) == {'bit_generator', 'state', 'has_uint32', 'uinteger'}
          and state['bit_generator'] == 'PCG64' and type(state['state']) is dict
          and set(state['state']) == {'state', 'inc'}, 'PCG64 state schema mismatch')
    _need(all(type(state['state'][key]) is int and 0 <= state['state'][key] < 2**128
              for key in ('state', 'inc')) and state['state']['inc'] % 2 == 1,
          'PCG64 state/stream increment invalid')
    _need(type(state['has_uint32']) is int and state['has_uint32'] in (0, 1)
          and type(state['uinteger']) is int and 0 <= state['uinteger'] < 2**32,
          'PCG64 cached uint32 state invalid')
    probe = np.random.Generator(np.random.PCG64(0))
    try:
        probe.bit_generator.state = deepcopy(state)
    except (ValueError, TypeError, OverflowError) as error:
        raise FactorizedCheckpointError('PCG64 state restore rejected') from error
    _need(probe.bit_generator.state == state, 'PCG64 state does not restore exactly')
    return deepcopy(state)


def _live_optimizer(model, optimizer):
    _need(type(optimizer) is torch.optim.AdamW and len(optimizer.param_groups) == 1,
          'one exact AdamW group required')
    names = tuple(name for name, _ in model.named_parameters())
    parameters = tuple(model.parameters())
    group = optimizer.param_groups[0]
    _need(tuple(id(p) for p in group['params']) == tuple(id(p) for p in parameters)
          and all(p.requires_grad for p in parameters)
          and all(any(p is owned for owned in parameters) for p in optimizer.state),
          'AdamW ordered parameter ownership mismatch')
    _need(group['betas'] == (.9, .999) and group['eps'] == 1e-8 and group['weight_decay'] == 0.
          and all(group.get(key, False) is False for key in
                  ('foreach', 'fused', 'amsgrad', 'maximize', 'capturable', 'differentiable'))
          and type(group['lr']) is float and math.isfinite(group['lr']) and group['lr'] > 0,
          'AdamW scientific policy/settings mismatch')
    return names


def _optimizer_binding(binding, base_optimizer, conditional_optimizer):
    if 'optimizer_policy' in binding:
        expected_keys = {'class', 'lr', 'betas', 'eps', 'weight_decay', 'foreach', 'fused',
                         'amsgrad', 'maximize', 'capturable', 'differentiable'}
        policy = binding['optimizer_policy']
        _need(type(policy) is dict and set(policy) == expected_keys and policy['class'] == 'AdamW',
              'optimizer binding schema mismatch')
        for optimizer in (base_optimizer, conditional_optimizer):
            group = optimizer.param_groups[0]
            actual = {key: list(group[key]) if key == 'betas' else group[key]
                      for key in expected_keys if key != 'class'}
            actual['class'] = 'AdamW'
            _need(_same(policy, actual), 'declared optimizer policy differs from live AdamW settings')
    if 'training_schedule' in binding:
        schedule = binding['training_schedule']
        _need(type(schedule) is dict and type(schedule.get('base_steps')) is int
              and type(schedule.get('conditional_steps')) is int
              and schedule['base_steps'] == schedule['conditional_steps'] == 4,
              'checkpoint binding requires fixed four-plus-four training schedule')


def _model_record(model):
    return {'state': dict(model.state_dict()),
            'gradients': {name: None if p.grad is None else p.grad for name, p in model.named_parameters()},
            'parameter_names': tuple(name for name, _ in model.named_parameters()),
            'requires_grad': {name: p.requires_grad for name, p in model.named_parameters()},
            'training_modes': {name: module.training for name, module in model.named_modules()}}


def _validate_model_record(record, model, counts):
    _need(type(record) is dict and set(record) == MODEL_KEYS, 'model checkpoint field roster invalid')
    expected = _model_record(model)
    _need(type(record['parameter_names']) is tuple and record['parameter_names'] == expected['parameter_names'],
          'ordered model parameter names mismatch')
    _need(_same(record['requires_grad'], expected['requires_grad'])
          and _same(record['training_modes'], expected['training_modes']),
          'model trainability or mode binding mismatch')
    _need(type(record['state']) is dict and record['state'].keys() == expected['state'].keys()
          and type(record['gradients']) is dict and record['gradients'].keys() == expected['gradients'].keys(),
          'model state or gradient roster mismatch')
    for name, target in expected['state'].items():
        value = record['state'][name]
        _need(type(value) is torch.Tensor and value.dtype == target.dtype == torch.float32
              and value.device.type == 'cpu' and value.shape == target.shape
              and bool(torch.isfinite(value).all()), 'saved model tensor mismatch')
    for name, p in model.named_parameters():
        gradient = record['gradients'][name]
        if gradient is not None:
            _need(counts[name] > 0 and type(gradient) is torch.Tensor
                  and gradient.dtype == torch.float32 and gradient.device.type == 'cpu'
                  and gradient.shape == p.shape and bool(torch.isfinite(gradient).all()),
                  'saved gradient incompatible with parameter or update cursor')


def _validate_optimizer_record(record, model, optimizer, counts):
    names = _live_optimizer(model, optimizer)
    _need(type(record) is dict and set(record) == {'state', 'param_groups'}
          and type(record['state']) is dict and type(record['param_groups']) is list
          and len(record['param_groups']) == 1, 'saved AdamW schema invalid')
    group = record['param_groups'][0]
    current = optimizer.state_dict()['param_groups'][0]
    _need(type(group) is dict and group.keys() == current.keys()
          and _same(group, current), 'saved AdamW group/order/settings differ from target')
    indices = group['params']
    _need(type(indices) is list and len(indices) == len(names)
          and all(type(i) is int for i in indices) and len(set(indices)) == len(indices),
          'saved AdamW parameter indices invalid')
    expected_indices = {index for index, name in zip(indices, names) if counts[name] > 0}
    _need(set(record['state']) == expected_indices
          and all(type(index) is int for index in record['state']), 'saved AdamW state/counter roster mismatch')
    for index, (name, p) in zip(indices, model.named_parameters()):
        if counts[name] == 0:
            continue
        row = record['state'][index]
        _need(type(row) is dict and set(row) == {'step', 'exp_avg', 'exp_avg_sq'},
              'saved AdamW moment roster invalid')
        step = row['step']
        _need(type(step) is torch.Tensor and step.device.type == 'cpu'
              and step.dtype == torch.float32 and step.shape == torch.Size([])
              and float(step) == float(counts[name]), 'saved AdamW per-parameter step mismatch')
        for field in ('exp_avg', 'exp_avg_sq'):
            value = row[field]
            _need(type(value) is torch.Tensor and value.device.type == 'cpu'
                  and value.dtype == torch.float32 and value.shape == p.shape
                  and bool(torch.isfinite(value).all()), 'saved AdamW moment shape/dtype/finite mismatch')
        _need(bool((row['exp_avg_sq'] >= 0).all()), 'saved AdamW second moment is negative')


def _preflight_archive(payload):
    try:
        archive = zipfile.ZipFile(BytesIO(payload))
    except (zipfile.BadZipFile, OSError) as error:
        raise FactorizedCheckpointError('checkpoint is not a Torch ZIP archive') from error
    with archive:
        entries = archive.infolist()
        _need(0 < len(entries) <= 4096, 'checkpoint archive entry limit exceeded')
        names, total = set(), 0
        for entry in entries:
            name = entry.filename
            _need(type(name) is str and 0 < len(name) <= 255 and name.isascii()
                  and not name.startswith('/') and '\\' not in name
                  and all(part not in ('', '.', '..') for part in name.split('/'))
                  and name not in names and not entry.is_dir(), 'checkpoint archive name invalid')
            _need(entry.compress_type == zipfile.ZIP_STORED and not entry.flag_bits & 1
                  and entry.file_size == entry.compress_size
                  and 0 <= entry.file_size <= MAXIMUM_CHECKPOINT_BYTES,
                  'checkpoint compressed/encrypted/oversized entry refused')
            names.add(name)
            total += entry.file_size
            _need(total <= MAXIMUM_CHECKPOINT_BYTES, 'checkpoint archive expansion limit exceeded')
        _need(any(name.endswith('/data.pkl') for name in names), 'checkpoint archive data record missing')


def _validate_payload(value, expected_binding, base, conditional, base_optimizer, conditional_optimizer, base_rng):
    _need(type(value) is dict and set(value) == PAYLOAD_KEYS and value['schema_version'] == SCHEMA_VERSION
          and value['scope'] == SCOPE and value['production_resume_permitted'] is False,
          'checkpoint format/scope mismatch')
    expected = _binding(expected_binding, base, conditional)
    _need(_json_binding(value['binding']) == expected, 'checkpoint expected binding mismatch')
    _cursor(value['cursor'], expected_binding, base, conditional)
    _need(type(value['models']) is dict and set(value['models']) == {'base', 'conditional'}
          and type(value['optimizers']) is dict and set(value['optimizers']) == {'base', 'conditional'},
          'checkpoint model/optimizer pair roster mismatch')
    for label, model, optimizer in (('base', base, base_optimizer), ('conditional', conditional, conditional_optimizer)):
        counts = value['cursor'][label + '_gradient_steps']
        _validate_model_record(value['models'][label], model, counts)
        _validate_optimizer_record(value['optimizers'][label], model, optimizer, counts)
    _optimizer_binding(expected_binding, base_optimizer, conditional_optimizer)
    _rng_state(base_rng, value['base_rng'])


def encode_checkpoint(*, binding, cursor, base, conditional, base_optimizer, conditional_optimizer, base_rng):
    """Detached restricted archive at a completed update boundary; no file I/O."""
    _binding(binding, base, conditional)
    _cursor(cursor, binding, base, conditional)
    value = _safe_clone({'schema_version': SCHEMA_VERSION, 'scope': SCOPE,
        'production_resume_permitted': False, 'binding': binding, 'cursor': cursor,
        'models': {'base': _model_record(base), 'conditional': _model_record(conditional)},
        'optimizers': {'base': base_optimizer.state_dict(), 'conditional': conditional_optimizer.state_dict()},
        'base_rng': _rng_state(base_rng)})
    _validate_payload(value, binding, base, conditional, base_optimizer, conditional_optimizer, base_rng)
    buffer = BytesIO()
    torch.save(value, buffer, _use_new_zipfile_serialization=True)
    payload = buffer.getvalue()
    _need(0 < len(payload) <= MAXIMUM_CHECKPOINT_BYTES, 'checkpoint byte limit exceeded')
    _preflight_archive(payload)
    return payload


def _install(value, base, conditional, base_optimizer, conditional_optimizer, base_rng):
    for label, model, optimizer in (('base', base, base_optimizer), ('conditional', conditional, conditional_optimizer)):
        model.load_state_dict(value['models'][label]['state'], strict=True)
        optimizer.load_state_dict(value['optimizers'][label])
        for name, p in model.named_parameters():
            gradient = value['models'][label]['gradients'][name]
            p.grad = None if gradient is None else gradient.detach().clone()
    # Explicit private RNG is installed last; no global RNG state is touched.
    base_rng.bit_generator.state = deepcopy(value['base_rng'])


def restore_checkpoint(payload, *, expected_sha256, expected_binding, base, conditional,
                       base_optimizer, conditional_optimizer, base_rng):
    """Validate before mutation; install only into fresh CPU model/AdamW objects."""
    _need(type(payload) is bytes and 0 < len(payload) <= MAXIMUM_CHECKPOINT_BYTES,
          'bounded nonempty checkpoint bytes required')
    _need(_sha(expected_sha256) and hmac.compare_digest(hashlib.sha256(payload).hexdigest(), expected_sha256),
          'checkpoint expected SHA256 mismatch')
    _binding(expected_binding, base, conditional)
    for model, optimizer in ((base, base_optimizer), (conditional, conditional_optimizer)):
        _live_optimizer(model, optimizer)
        _need(not optimizer.state and all(p.grad is None for p in model.parameters()),
              'checkpoint restoration requires fresh optimizer/no-gradient targets')
    _optimizer_binding(expected_binding, base_optimizer, conditional_optimizer)
    _rng_state(base_rng)
    _preflight_archive(payload)
    try:
        loaded = torch.load(BytesIO(payload), map_location='cpu', weights_only=True)
    except Exception as error:
        raise FactorizedCheckpointError('restricted checkpoint decoding failed') from error
    value = _safe_clone(loaded)
    _validate_payload(value, expected_binding, base, conditional, base_optimizer, conditional_optimizer, base_rng)
    # Fully validate isolated object installation before touching the live targets.
    base_probe, conditional_probe = deepcopy(base), deepcopy(conditional)
    probe_optimizers = []
    for model, original in ((base_probe, base_optimizer), (conditional_probe, conditional_optimizer)):
        group = deepcopy(original.state_dict()['param_groups'][0])
        group['params'] = list(model.parameters())
        probe_optimizers.append(torch.optim.AdamW([group], lr=group['lr']))
    rng_probe = np.random.Generator(np.random.PCG64(0))
    _install(value, base_probe, conditional_probe, *probe_optimizers, rng_probe)
    _validate_payload(value, expected_binding, base_probe, conditional_probe, *probe_optimizers, rng_probe)
    before = _safe_clone({'models': {'base': _model_record(base), 'conditional': _model_record(conditional)},
        'optimizers': {'base': base_optimizer.state_dict(), 'conditional': conditional_optimizer.state_dict()},
        'base_rng': _rng_state(base_rng)})
    try:
        _install(value, base, conditional, base_optimizer, conditional_optimizer, base_rng)
        for label, model, optimizer in (('base', base, base_optimizer), ('conditional', conditional, conditional_optimizer)):
            _need(_same(_safe_clone(_model_record(model)), value['models'][label])
                  and _same(_safe_clone(optimizer.state_dict()), value['optimizers'][label]),
                  'checkpoint installation did not restore tensors/optimizer exactly')
        _need(base_rng.bit_generator.state == value['base_rng'], 'checkpoint RNG installation mismatch')
    except Exception as error:
        try:
            _install(before, base, conditional, base_optimizer, conditional_optimizer, base_rng)
        except Exception as rollback_error:
            raise FactorizedCheckpointError('checkpoint installation and rollback failed') from rollback_error
        raise FactorizedCheckpointError('checkpoint installation failed; fresh target state restored') from error
    return deepcopy(value['cursor'])
