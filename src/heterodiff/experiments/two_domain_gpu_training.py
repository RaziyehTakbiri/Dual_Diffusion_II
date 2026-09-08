"""Draft CPU/CUDA training successor, for local synthetic qualification only.

This is a real forward/backward/AdamW loop over an explicitly supplied model
and loss adapter, not an implementation of a diffusion objective or admission.
The old certified CPU model/precision/receipt contracts are not modified.
Validation callbacks may provide arbitrary synthetic CPU64 values (not F105
certificates) or retained actual F105 factory results from the explicit supplied-
configuration bridge. Factory scores certify metric arithmetic, not generation
or data admission. No result here is a production checkpoint or scientific result.
The caller supplies every seed value; no scientific seed is generated.

There is deliberately no production execution, retry, or resume entrypoint.
Eight-way use means separate independent processes, never DDP or a larger
logical batch. Global Torch settings/RNG are temporarily scoped and restored;
callers must not run unrelated Torch work concurrently in the same process.
"""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
import hashlib
from io import BytesIO
import json
import os
import re
from threading import RLock
from typing import Callable, Dict, Optional, Tuple

import torch

from heterodiff.experiments import two_domain_training_checkpoint_plan as frozen


SCOPE = 'LOCAL_NONCONFIRMATORY_GPU_TRAINING_SUCCESSOR_QUALIFICATION'
SOURCE_KIND = 'SYNTHETIC_QUALIFICATION_ONLY'
_CONTEXT_LOCK = RLock()


class TrainingQualificationError(ValueError):
    """Terminal qualification failure; no retry, rollback-to-success or resume."""

    def __init__(self, message: str, completed_updates: int = 0):
        super().__init__(message)
        self.completed_updates = completed_updates


def _exact_int(value, name, minimum=0, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise TrainingQualificationError(f'{name} is outside its exact integer bounds')
    return value


def _ids(value, *, name, exact_count=None, minimum_count=1):
    if type(value) is not tuple or len(value) < minimum_count:
        raise TrainingQualificationError(f'{name} must be an exact nonempty ID tuple')
    if exact_count is not None and len(value) != exact_count:
        raise TrainingQualificationError(f'{name} must contain exactly {exact_count} IDs')
    if any(type(item) is not bytes or not 1 <= len(item) <= 256 for item in value):
        raise TrainingQualificationError(f'{name} IDs must be bounded nonempty bytes')
    if value != tuple(sorted(set(value))):
        raise TrainingQualificationError(f'{name} must be unique and canonical byte-ascending')
    return value


@dataclass(frozen=True)
class RunIdentity:
    method_id: str
    domain_id: str
    seed_ordinal: int
    seed_value: int
    trial_ordinal: Optional[int] = None

    def __post_init__(self):
        rows = frozen.learning_rate_schedule_value()['rows']
        if not any(row['method_id'] == self.method_id and row['domain_id'] == self.domain_id
                   for row in rows):
            raise TrainingQualificationError('method/domain identity is not in the frozen roster')
        if type(self.method_id) is not str or type(self.domain_id) is not str:
            raise TrainingQualificationError('method/domain identities must be exact strings')
        _exact_int(self.seed_ordinal, 'seed_ordinal', maximum=255)
        _exact_int(self.seed_value, 'caller-supplied seed_value', maximum=2**64 - 1)
        if self.trial_ordinal is not None:
            trial_row = next(row for row in frozen.maximum_tuning_trials_value()['rows']
                             if row['method_id'] == self.method_id and row['domain_id'] == self.domain_id)
            _exact_int(self.trial_ordinal, 'trial_ordinal', maximum=trial_row['maximum_trials'] - 1)

    def to_dict(self):
        return dict(method_id=self.method_id, domain_id=self.domain_id,
                    seed_ordinal=self.seed_ordinal, seed_value=self.seed_value,
                    trial_ordinal=self.trial_ordinal)


@dataclass(frozen=True)
class TensorTrainingRoster:
    domain_id: str
    record_ids: Tuple[bytes, ...]
    fields: Dict[str, torch.Tensor]
    source_kind: str = SOURCE_KIND

    def __post_init__(self):
        _ids(self.record_ids, name='training roster', minimum_count=16)
        if type(self.source_kind) is not str or self.source_kind != SOURCE_KIND:
            raise TrainingQualificationError('only explicitly synthetic qualification inputs accepted')
        if type(self.domain_id) is not str:
            raise TrainingQualificationError('roster domain must be an exact string')
        if type(self.fields) is not dict or not self.fields:
            raise TrainingQualificationError('fields must be an exact nonempty dictionary')
        for name, value in self.fields.items():
            if type(name) is not str or re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', name) is None:
                raise TrainingQualificationError('field names must be bounded plain identifiers')
            if type(value) is not torch.Tensor or value.layout != torch.strided:
                raise TrainingQualificationError('fields must be ordinary dense tensors')
            if value.device.type != 'cpu' or value.is_complex() or value.is_quantized:
                raise TrainingQualificationError('input staging must contain real unquantized CPU tensors')
            if value.ndim < 1 or value.shape[0] != len(self.record_ids) or value.requires_grad:
                raise TrainingQualificationError('fields must align with the full roster and not require gradients')
            if value.is_floating_point() and value.dtype != torch.float32:
                raise TrainingQualificationError('floating training fields must be FP32, without implicit casts')
            if value.is_floating_point() and not bool(torch.isfinite(value).all()):
                raise TrainingQualificationError('training field is nonfinite')


@dataclass(frozen=True)
class NonconfirmatorySchedule:
    maximum_updates: int = 4096
    validation_every: int = 256

    def __post_init__(self):
        _exact_int(self.maximum_updates, 'maximum_updates', 1, 4096)
        _exact_int(self.validation_every, 'validation_every', 1, 256)

    @property
    def checkpoint_steps(self):
        steps = tuple(range(self.validation_every, self.maximum_updates + 1,
                            self.validation_every))
        return steps if steps and steps[-1] == self.maximum_updates else steps + (self.maximum_updates,)

    @property
    def matches_frozen_final_training_schedule(self):
        return self.maximum_updates == 4096 and self.validation_every == 256


@dataclass(frozen=True)
class ValidationObservation:
    """Synthetic callback values, never authenticated F105 group-score records."""

    group_scores: torch.Tensor
    draws_per_group: int = 64

    def aggregate_hex(self):
        values = self.group_scores
        if (type(values) is not torch.Tensor or values.layout != torch.strided
                or values.device.type != 'cpu' or values.dtype != torch.float64
                or tuple(values.shape) != (128,) or values.requires_grad):
            raise TrainingQualificationError('validation requires 128 detached CPU FP64 group scores')
        if type(self.draws_per_group) is not int or self.draws_per_group != 64:
            raise TrainingQualificationError('validation requires declared R=64, not a smaller draw count')
        if not bool(torch.isfinite(values).all()) or not bool(((values >= -2) & (values <= 1)).all()):
            raise TrainingQualificationError('validation scores must be finite and within F105 [-2,1]')
        # Existing F141/F144 arithmetic: exact ratios, exact sum/128, one round.
        total = sum((Fraction(*value.as_integer_ratio()) for value in values.tolist()), Fraction(0))
        return float(total / 128).hex()


@dataclass(frozen=True)
class QualificationCheckpoint:
    identity: RunIdentity
    completed_updates: int
    validation_score_hex: str
    model_state: dict
    optimizer_state: dict
    training_configuration: dict
    f105_validation: object = None


@dataclass(frozen=True)
class QualificationResult:
    identity: RunIdentity
    device: str
    completed_updates: int
    losses: Tuple[float, ...]
    checkpoints: Tuple[QualificationCheckpoint, ...]
    selected_checkpoint_step: int
    frozen_schedule_executed: bool
    training_configuration: dict

    def summary(self):
        return {
            'decision': 'PASS_LOCAL_NONCONFIRMATORY_TRAINING_KERNEL',
            'scope': SCOPE,
            'identity': self.identity.to_dict(), 'device': self.device,
            'training_configuration': deepcopy(self.training_configuration),
            'completed_optimizer_updates': self.completed_updates,
            'logical_records_per_update': 16,
            'checkpoint_steps': [item.completed_updates for item in self.checkpoints],
            'selected_checkpoint_step': self.selected_checkpoint_step,
            'full_frozen_schedule_executed': self.frozen_schedule_executed,
            'cuda_execution_observed': self.device.startswith('cuda:'),
            'gpu_runtime_independently_qualified': False,
            'f105_factory_certification_supplied': bool(self.checkpoints) and all(
                checkpoint.f105_validation is not None for checkpoint in self.checkpoints),
            'f105_factory_scope': 'SUPPLIED_CONFIGURATION_METRIC_ONLY_NOT_GENERATOR_OR_ADMISSION',
            'conditional_draw_execution_authenticated': False,
            'actual_diffusion_loss_implemented_by_this_kernel': False,
            'model_binding_to_certified_b06_component_verified': False,
            'seed_registry_authentication_supplied': False,
            'production_training_or_resume_authorized': False,
            'scientific_result_created': False,
        }


def resolve_training_device(device: str) -> torch.device:
    if type(device) is not str:
        raise TrainingQualificationError('device must be explicit cpu or cuda:N')
    if device == 'cpu':
        return torch.device('cpu')
    if re.fullmatch(r'cuda:(0|[1-9][0-9]*)', device) is None:
        raise TrainingQualificationError('device must be explicit cpu or cuda:N; no auto/DDP/MPS route')
    if not torch.cuda.is_available():
        raise TrainingQualificationError('CUDA requested but unavailable; CPU fallback is forbidden')
    selected = torch.device(device)
    if selected.index >= torch.cuda.device_count():
        raise TrainingQualificationError('requested CUDA device is not visible')
    if os.environ.get('CUBLAS_WORKSPACE_CONFIG') not in (':4096:8', ':16:8'):
        raise TrainingQualificationError('set an approved CUBLAS_WORKSPACE_CONFIG before CUDA initialization')
    return selected


def _precision_settings():
    """Choose one precision API family; never mix new APIs and allow_tf32."""
    objects = [torch.backends, torch.backends.cuda.matmul, torch.backends.cudnn]
    if hasattr(torch.backends.cudnn, 'conv') and hasattr(torch.backends.cudnn, 'rnn'):
        objects += [torch.backends.cudnn.conv, torch.backends.cudnn.rnn]
    modern = [hasattr(obj, 'fp32_precision') for obj in objects]
    if all(modern) and len(objects) == 5:
        return [(obj, 'fp32_precision', 'ieee') for obj in objects]
    if any(modern):
        raise TrainingQualificationError('partial modern FP32 API requires an explicit compatibility implementation')
    return [(torch.backends.cuda.matmul, 'allow_tf32', False),
            (torch.backends.cudnn, 'allow_tf32', False)]


@contextmanager
def deterministic_training_context(device: torch.device, seed_value: int):
    """Temporarily apply deterministic IEEE FP32 settings and scoped RNG state."""
    _exact_int(seed_value, 'caller-supplied seed_value', maximum=2**64 - 1)
    settings = _precision_settings()
    with _CONTEXT_LOCK:
        old = [(obj, name, getattr(obj, name)) for obj, name, _ in settings]
        deterministic = torch.are_deterministic_algorithms_enabled()
        warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
        benchmark = torch.backends.cudnn.benchmark
        cudnn_deterministic = torch.backends.cudnn.deterministic
        devices = [device.index] if device.type == 'cuda' else []
        try:
            for obj, name, value in settings:
                setattr(obj, name, value)
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = True
            torch.use_deterministic_algorithms(True, warn_only=False)
            with torch.random.fork_rng(devices=devices, enabled=True):
                torch.random.default_generator.manual_seed(seed_value)
                if device.type == 'cuda':
                    torch.cuda.default_generators[device.index].manual_seed(seed_value)
                generator = torch.Generator(device=device)
                generator.manual_seed(seed_value)
                yield generator
        finally:
            for obj, name, value in reversed(old):
                setattr(obj, name, value)
            torch.backends.cudnn.benchmark = benchmark
            torch.backends.cudnn.deterministic = cudnn_deterministic
            torch.use_deterministic_algorithms(deterministic, warn_only=warn_only)


def _cpu_clone(value):
    if isinstance(value, torch.Tensor):
        return value.detach().to('cpu').clone()
    if type(value) in (dict,):
        return {key: _cpu_clone(member) for key, member in value.items()}
    if isinstance(value, dict):  # Module state_dict is an OrderedDict.
        return {key: _cpu_clone(member) for key, member in value.items()}
    if type(value) in (list, tuple):
        return type(value)(_cpu_clone(member) for member in value)
    if value is None or type(value) in (bool, str, int, float):
        return value
    raise TrainingQualificationError('unsupported checkpoint value type')


def _model_tensors_valid(model, device):
    for value in (*model.parameters(), *model.buffers()):
        if value.device != device or value.layout != torch.strided or value.is_complex():
            raise TrainingQualificationError('model tensor device/layout mismatch')
        if value.is_floating_point() and (value.dtype != torch.float32 or not bool(torch.isfinite(value).all())):
            raise TrainingQualificationError('model floating tensors must be finite FP32')


def _optimizer_moments_valid(optimizer, device):
    for state in optimizer.state.values():
        for name in ('exp_avg', 'exp_avg_sq'):
            value = state.get(name)
            if (type(value) is not torch.Tensor or value.dtype != torch.float32
                    or value.device != device or not bool(torch.isfinite(value).all())):
                raise TrainingQualificationError('AdamW moments must remain finite FP32 on the selected device')


def _frozen_parameters_valid(model, original_flags, frozen_parameters):
    if {name: (id(value), value.requires_grad) for name, value in model.named_parameters()} != original_flags:
        raise TrainingQualificationError('callback changed the all-and-only-trainable parameter roster')
    current = dict(model.named_parameters())
    for name, expected in frozen_parameters.items():
        if not torch.equal(current[name].detach().to('cpu'), expected):
            raise TrainingQualificationError('callback or optimizer mutated a frozen parameter')


@contextmanager
def _validation_rng_context(device, cpu_generator, cuda_generator):
    """Separate advancing callback stream, preserving the training stream.

    Both streams start from the caller-supplied seed, without inventing a new
    scientific seed or claiming statistically independent validation draws.
    """
    devices = [device.index] if device.type == 'cuda' else []
    with torch.random.fork_rng(devices=devices, enabled=True):
        torch.random.set_rng_state(cpu_generator.get_state())
        if cuda_generator is not None:
            torch.cuda.set_rng_state(cuda_generator.get_state(), device=device)
        try:
            yield
        finally:
            cpu_generator.set_state(torch.random.get_rng_state())
            if cuda_generator is not None:
                cuda_generator.set_state(torch.cuda.get_rng_state(device))


def _training_configuration(model, roster, validation_ids, schedule, learning_rate, configuration_id):
    if type(configuration_id) is not str or re.fullmatch(r'[A-Za-z0-9_.:-]{1,256}', configuration_id) is None:
        raise TrainingQualificationError('configuration_id must be an explicit bounded plain label')
    value = {
        'scope': SCOPE, 'caller_configuration_id': configuration_id,
        'supplied_model_class': f'{type(model).__module__}.{type(model).__qualname__}',
        'model_and_loss_scientific_configuration_independently_verified': False,
        'learning_rate_exact_rational': str(learning_rate),
        'maximum_updates': schedule.maximum_updates,
        'validation_every': schedule.validation_every,
        'logical_batch_size': 16, 'gradient_accumulation_steps': 1,
        'training_record_ids_hex': [value.hex() for value in roster.record_ids],
        'validation_group_ids_hex': [value.hex() for value in validation_ids],
        'trainable_parameter_names': [name for name, value in model.named_parameters() if value.requires_grad],
        'validation_rng_policy': 'SEPARATE_ADVANCING_STREAM_SAME_SUPPLIED_SEED_TRAINING_STATE_RESTORED',
        'independent_validation_draws_authenticated': False,
    }
    value['configuration_sha256'] = hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    return value


def run_training_qualification(
    model: torch.nn.Module, roster: TensorTrainingRoster, identity: RunIdentity, *,
    device: str, loss_adapter: Callable, validation_group_ids: Tuple[bytes, ...],
    validation_adapter: Callable, schedule: NonconfirmatorySchedule = NonconfirmatorySchedule(),
    learning_rate: Fraction = Fraction(1, 1000),
    configuration_id: str = 'UNSPECIFIED_SYNTHETIC_ADAPTER_CONFIGURATION',
) -> QualificationResult:
    """Execute a draft training kernel on caller-declared synthetic inputs only.

    The supplied model is copied. Loss adapters receive (model, batch, generator)
    and must return one FP32 scalar connected to at least one trainable parameter.
    Unused event branches may legitimately have no gradient on a given batch.
    Validation adapters receive (model, step, identity). They may return
    uncertified synthetic ValidationObservation values, or an actual retained
    F105CheckpointValidation for supplied configurations. The latter is bound
    to this run, update, model state and all 128 groups; it does not authenticate
    generation or admission. Exceptions stop this call permanently; there is
    no automatic retry or continuation API.
    """
    if type(identity) is not RunIdentity or type(roster) is not TensorTrainingRoster or type(schedule) is not NonconfirmatorySchedule:
        raise TrainingQualificationError('identity, roster and schedule must be exact supported types')
    identity.__post_init__()
    roster.__post_init__()
    schedule.__post_init__()
    if identity.trial_ordinal is not None and schedule.maximum_updates > 1024:
        raise TrainingQualificationError('tuning qualification cannot exceed the frozen 1024-update ceiling')
    if roster.domain_id != identity.domain_id:
        raise TrainingQualificationError('cross-domain training roster refused')
    validation_ids = _ids(validation_group_ids, name='validation roster', exact_count=128)
    if set(roster.record_ids) & set(validation_ids):
        raise TrainingQualificationError('training/validation group overlap refused')
    if not isinstance(model, torch.nn.Module) or isinstance(model, (torch.nn.DataParallel, torch.nn.parallel.DistributedDataParallel)):
        raise TrainingQualificationError('one ordinary model per process required; DDP/DataParallel refused')
    if not callable(loss_adapter) or not callable(validation_adapter):
        raise TrainingQualificationError('explicit callable loss and validation adapters required')
    row = next(row for row in frozen.learning_rate_schedule_value()['rows']
               if row['method_id'] == identity.method_id and row['domain_id'] == identity.domain_id)
    if type(learning_rate) is not Fraction or str(learning_rate) not in row['base_learning_rate_candidates_exact_rational']:
        raise TrainingQualificationError('learning rate must be an exact frozen candidate rational')
    selected_device = resolve_training_device(device)
    parameters = tuple(model.parameters())
    if not parameters or not any(value.requires_grad for value in parameters):
        raise TrainingQualificationError('model must have trainable parameters')
    if any(value.is_floating_point() and value.dtype != torch.float32
           for value in (*model.parameters(), *model.buffers())):
        raise TrainingQualificationError('supply an explicit FP32 successor model; implicit certificate conversion refused')
    configuration = _training_configuration(model, roster, validation_ids, schedule, learning_rate, configuration_id)
    completed = 0
    losses, checkpoints = [], []
    with deterministic_training_context(selected_device, identity.seed_value) as generator:
        working_model = deepcopy(model).to(device=selected_device)
        _model_tensors_valid(working_model, selected_device)
        working_model.train()
        original_flags = {name: (id(value), value.requires_grad) for name, value in working_model.named_parameters()}
        frozen_parameters = {name: _cpu_clone(value) for name, value in working_model.named_parameters() if not value.requires_grad}
        validation_cpu_rng = torch.Generator(device='cpu').manual_seed(identity.seed_value)
        validation_cuda_rng = (torch.Generator(device=selected_device).manual_seed(identity.seed_value)
                               if selected_device.type == 'cuda' else None)
        trainable = [value for value in working_model.parameters() if value.requires_grad]
        optimizer = torch.optim.AdamW(
            trainable, lr=float(learning_rate), betas=(0.9, 0.999), eps=1e-8,
            weight_decay=0.0, amsgrad=False, maximize=False, foreach=False,
            fused=False, capturable=False, differentiable=False,
        )
        try:
            for update in range(schedule.maximum_updates):
                indices = torch.tensor([(16 * update + j) % len(roster.record_ids)
                                        for j in range(16)], dtype=torch.int64)
                batch = {name: value.index_select(0, indices).to(selected_device)
                         for name, value in roster.fields.items()}
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type=selected_device.type, enabled=False):
                    loss = loss_adapter(working_model, batch, generator)
                if (type(loss) is not torch.Tensor or loss.shape != torch.Size([])
                        or loss.dtype != torch.float32 or loss.device != selected_device
                        or not loss.requires_grad or not bool(torch.isfinite(loss))):
                    raise TrainingQualificationError('loss must be a finite connected FP32 scalar on selected device')
                loss.backward()
                _frozen_parameters_valid(working_model, original_flags, frozen_parameters)
                gradients = [value.grad for value in trainable if value.grad is not None]
                if not gradients or any(gradient.dtype != torch.float32
                       or gradient.device != selected_device or not bool(torch.isfinite(gradient).all())
                       for gradient in gradients):
                    raise TrainingQualificationError('present gradients must be finite FP32 on selected device')
                optimizer.step()
                completed += 1
                _model_tensors_valid(working_model, selected_device)
                _optimizer_moments_valid(optimizer, selected_device)
                _frozen_parameters_valid(working_model, original_flags, frozen_parameters)
                losses.append(float(loss.detach().to('cpu')))
                if completed in schedule.checkpoint_steps:
                    working_model.eval()
                    before_validation = _cpu_clone(working_model.state_dict())
                    with _validation_rng_context(selected_device, validation_cpu_rng, validation_cuda_rng):
                        with torch.no_grad(), torch.autocast(device_type=selected_device.type, enabled=False):
                            observation = validation_adapter(working_model, completed, identity)
                    after_validation = _cpu_clone(working_model.state_dict())
                    if (before_validation.keys() != after_validation.keys()
                            or any(not torch.equal(before_validation[key], after_validation[key])
                                   for key in before_validation)):
                        raise TrainingQualificationError('validation callback mutated model state')
                    _frozen_parameters_valid(working_model, original_flags, frozen_parameters)
                    # Imported only here: the metric bridge uses RunIdentity above.
                    from heterodiff.experiments.two_domain_f105_checkpoint_validation import F105CheckpointValidation
                    f105_validation = None
                    if type(observation) is F105CheckpointValidation:
                        observation.validate_binding(identity, completed, after_validation, validation_ids)
                        f105_validation = observation  # Retain all 128 real factory objects.
                    elif type(observation) is not ValidationObservation:
                        raise TrainingQualificationError('validation adapter returned an unsupported observation')
                    score_hex = observation.aggregate_hex()
                    _model_tensors_valid(working_model, selected_device)
                    checkpoints.append(QualificationCheckpoint(
                        identity, completed, score_hex,
                        _cpu_clone(working_model.state_dict()), _cpu_clone(optimizer.state_dict()),
                        deepcopy(configuration), f105_validation,
                    ))
                    working_model.train()
        except Exception as error:
            raise TrainingQualificationError(f'TERMINAL_QUALIFICATION_FAILURE:{error}', completed) from error
    minimum = min(float.fromhex(item.validation_score_hex) for item in checkpoints)
    tied = [item for item in checkpoints if float.fromhex(item.validation_score_hex) == minimum]
    if len({item.validation_score_hex for item in tied}) != 1:
        raise TrainingQualificationError('canonical equality is ambiguous at signed zero; selection refused', completed)
    best = min(tied, key=lambda item: item.completed_updates)
    return QualificationResult(identity, str(selected_device), completed, tuple(losses),
                               tuple(checkpoints), best.completed_updates,
                               schedule.matches_frozen_final_training_schedule and identity.trial_ordinal is None,
                               deepcopy(configuration))


def checkpoint_to_bytes(checkpoint: QualificationCheckpoint) -> bytes:
    """Serialize detached CPU copies for inspection, not production resumption."""
    if type(checkpoint) is not QualificationCheckpoint:
        raise TrainingQualificationError('exact qualification checkpoint required')
    evidence = None
    if checkpoint.f105_validation is not None:
        from heterodiff.experiments.two_domain_f105_checkpoint_validation import F105CheckpointValidation
        from heterodiff.evaluation.two_domain_count_normalized_event_cks_production import score_record
        validation = checkpoint.f105_validation
        if type(validation) is not F105CheckpointValidation:
            raise TrainingQualificationError('checkpoint contains unsupported F105 evidence')
        validation.validate_binding(checkpoint.identity, checkpoint.completed_updates, checkpoint.model_state,
                                    tuple(row.group_id for row in validation.group_records))
        if checkpoint.validation_score_hex != validation.aggregate_hex():
            raise TrainingQualificationError('checkpoint score differs from its F105 factory evidence')
        evidence = {
            'summary': validation.summary(),
            'serialization_scope': 'COMPACT_AUDIT_PROJECTION_NOT_RECONSTRUCTED_FACTORY_OBJECTS',
            'group_records': [dict(group_id_hex=row.group_id.hex(), ordinal=row.ordinal,
                                   supplied_input_sha256=row.supplied_input_sha256,
                                   score_integrity_sha256=row.score_integrity_sha256,
                                   factory_record=dict(score_record(row.factory_score)))
                              for row in validation.group_records],
        }
    buffer = BytesIO()
    torch.save({
        'scope': SCOPE, 'production_resume_permitted': False,
        'identity': checkpoint.identity.to_dict(),
        'training_configuration': deepcopy(checkpoint.training_configuration),
        'completed_updates': checkpoint.completed_updates,
        'validation_score_hex': checkpoint.validation_score_hex,
        'model_state': _cpu_clone(checkpoint.model_state),
        'optimizer_state': _cpu_clone(checkpoint.optimizer_state),
        'f105_validation_audit_projection': evidence,
    }, buffer)
    return buffer.getvalue()


def inspect_checkpoint_bytes(payload: bytes) -> dict:
    """Load our primitive/tensor archive with weights_only; no trainer is resumed.

    This helper is for local self-produced payloads, not untrusted downloads.
    Any future external checkpoint must be independently bound before loading.
    """
    if type(payload) is not bytes or not payload:
        raise TrainingQualificationError('nonempty local checkpoint bytes required')
    result = torch.load(BytesIO(payload), map_location='cpu', weights_only=True)
    if (type(result) is not dict or result.get('scope') != SCOPE
            or result.get('production_resume_permitted') is not False):
        raise TrainingQualificationError('not a local inspection-only qualification checkpoint')
    return _cpu_clone(result)
