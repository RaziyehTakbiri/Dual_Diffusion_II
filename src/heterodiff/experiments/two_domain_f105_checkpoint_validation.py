"""Actual CPU-binary64 F105 scoring for supplied conditional configurations.

This additive bridge does not generate conditional draws, authenticate a data
split, approve a GPU runtime, or turn a model-state digest into a full checkpoint
archive digest. It preserves actual F105 factory objects and the complete-128
group binding. The frozen structural helper uses registry domain names where
F105 uses metric domain names; this module explicitly bridges those names and
does not manufacture replacement F105 integrity hashes to satisfy that helper.
"""

from collections import OrderedDict
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import sys

import torch

from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    ExactConfiguration, ExactEvent,
)
from heterodiff.evaluation.two_domain_count_normalized_event_cks_production import (
    DEFAULT_SYMBOLIC_EVENT_PAIR_WORK_LIMIT, ProductionCKSScore,
    production_conditional_cks_score, score_record,
)
from heterodiff.experiments import two_domain_training_checkpoint_plan as frozen
from heterodiff.experiments.two_domain_gpu_training import RunIdentity, ValidationObservation

DOMAIN_ALIASES = {
    'physionet-challenge-2012': 'R3-PHYS',
    'online-retail-ii': 'R4-RETAIL',
}
_SEAL = object()


class CheckpointValidationError(ValueError):
    """A supplied input or retained score binding is not exact."""


def _digest(domain, value):
    payload = json.dumps(value, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=True, allow_nan=False).encode('ascii')
    return hashlib.sha256(domain.encode('ascii') + b'\0' + payload).hexdigest()


def _roster(ids):
    if (type(ids) is not tuple or len(ids) != 128
            or any(type(item) is not bytes or not 1 <= len(item) <= 256 for item in ids)
            or ids != tuple(sorted(set(ids)))):
        raise CheckpointValidationError('validation roster must be 128 sorted unique bounded byte IDs')
    return ids


def _configuration_payload(configuration):
    if type(configuration) is not ExactConfiguration:
        raise CheckpointValidationError('metric inputs must be exact ExactConfiguration objects')
    canonical = ExactConfiguration(configuration.domain_id, configuration.events)
    if configuration != canonical:
        raise CheckpointValidationError('metric configuration must already be canonical; no input repair')
    for event in configuration.events:
        if type(event) is not ExactEvent:
            raise CheckpointValidationError('metric events must be exact')
        event.__post_init__()
    return {
        'domain_id': configuration.domain_id,
        'events': [[[part.numerator, part.denominator] for part in event.coordinates]
                   for event in configuration.events],
    }


@dataclass(frozen=True)
class GroupConditionalConfigurations:
    """Caller-supplied R64 configurations and truth, not a generator receipt."""

    group_id: bytes
    draws: tuple
    target: ExactConfiguration

    def __post_init__(self):
        if type(self.group_id) is not bytes or not 1 <= len(self.group_id) <= 256:
            raise CheckpointValidationError('group ID must be bounded nonempty exact bytes')
        if type(self.draws) is not tuple or len(self.draws) != 64:
            raise CheckpointValidationError('each group requires exactly R=64 supplied configurations')
        _configuration_payload(self.target)
        for configuration in self.draws:
            _configuration_payload(configuration)
            if configuration.domain_id != self.target.domain_id:
                raise CheckpointValidationError('draw and target metric domains differ')

    def input_sha256(self):
        self.__post_init__()
        return _digest('heterodiff-f105-supplied-group-input-v1', {
            'group_id_hex': self.group_id.hex(),
            'draws': [_configuration_payload(item) for item in self.draws],
            'target': _configuration_payload(self.target),
        })


def checkpoint_model_state_sha256(model_or_state_dict):
    """Canonical state-name/dtype/shape/CPU-byte digest; no optimizer/archive claim."""
    state = (model_or_state_dict.state_dict() if isinstance(model_or_state_dict, torch.nn.Module)
             else model_or_state_dict)
    if type(state) not in (dict, OrderedDict) or not state or sys.byteorder != 'little':
        raise CheckpointValidationError('model state requires a nonempty exact mapping on little-endian CPU')
    if any(type(name) is not str or not name for name in state):
        raise CheckpointValidationError('state names must be nonempty exact strings')
    rows = []
    for name in sorted(state):
        value = state[name]
        if (type(value) is not torch.Tensor or value.layout != torch.strided
                or value.is_quantized or value.is_complex()):
            raise CheckpointValidationError('model state must contain ordinary real dense tensors')
        copied = value.detach().to(device='cpu').contiguous()
        if copied.is_floating_point() and not bool(torch.isfinite(copied).all()):
            raise CheckpointValidationError('model state contains nonfinite values')
        raw = copied.reshape(-1).view(torch.uint8).numpy().tobytes()
        rows.append({'name': name, 'dtype': str(copied.dtype), 'shape': list(copied.shape),
                     'byteorder': 'little', 'payload_sha256': hashlib.sha256(raw).hexdigest(),
                     'size_bytes': len(raw)})
    return _digest('heterodiff-f105-checkpoint-model-state-v1', rows)


@dataclass(frozen=True)
class CertifiedGroupScore:
    ordinal: int
    group_id: bytes
    supplied_input_sha256: str
    factory_score: ProductionCKSScore
    score_integrity_sha256: str


def _bound_group_payload(result, group):
    record = dict(score_record(group.factory_score))
    if (record['domain_id'] != DOMAIN_ALIASES[result.identity.domain_id]
            or record['draw_count'] != 64 or record['score_direction'] != 'LOWER_IS_BETTER'):
        raise CheckpointValidationError('factory score domain/draw/direction mismatch')
    value = float.fromhex(record['binary64_score_hex'])
    if value.hex() != record['binary64_score_hex'] or not -2 <= value <= 1:
        raise CheckpointValidationError('factory score must be canonical binary64 within [-2,1]')
    return {
        'ordinal': group.ordinal, 'group_id_sha256': hashlib.sha256(group.group_id).hexdigest(),
        'supplied_input_sha256': group.supplied_input_sha256,
        'registry_domain_id': result.identity.domain_id,
        'metric_domain_id': DOMAIN_ALIASES[result.identity.domain_id],
        'method_id': result.identity.method_id,
        'checkpoint_model_state_sha256': result.checkpoint_content_sha256,
        'cpu_reference_configuration_sha256': result.cpu_reference_configuration_sha256,
        'selection_unit_sha256': result.selection_unit_sha256,
        'factory_record': record,
    }


def _subject(result):
    return frozen.complete_roster_certificate_subject_sha256(
        checkpoint_content_sha256=result.checkpoint_content_sha256,
        domain_id=result.identity.domain_id,
        executable_configuration_sha256=result.cpu_reference_configuration_sha256,
        group_roster_sha256=result.group_roster_sha256,
        group_score_integrity_sha256s=[group.score_integrity_sha256 for group in result.group_records],
        method_id=result.identity.method_id, selection_unit_sha256=result.selection_unit_sha256,
    )

def _result_payload(result):
    return {
        'identity': result.identity.to_dict(), 'completed_updates': result.completed_updates,
        'checkpoint_model_state_sha256': result.checkpoint_content_sha256,
        'cpu_reference_configuration_sha256': result.cpu_reference_configuration_sha256,
        'selection_unit_sha256': result.selection_unit_sha256,
        'group_roster_sha256': result.group_roster_sha256,
        'group_score_integrity_sha256s': [row.score_integrity_sha256 for row in result.group_records],
        'complete_roster_certificate_subject_sha256': result.complete_roster_certificate_subject_sha256,
    }


@dataclass(frozen=True, init=False)
class F105CheckpointValidation:
    identity: RunIdentity
    completed_updates: int
    checkpoint_content_sha256: str
    cpu_reference_configuration_sha256: str
    selection_unit_sha256: str
    group_roster_sha256: str
    group_records: tuple
    complete_roster_certificate_subject_sha256: str
    _integrity_sha256: str
    _seal: object

    def __new__(cls, *args, **kwargs):
        raise CheckpointValidationError('use evaluate_checkpoint_validation, not arbitrary score values')

    def _validate(self):
        if type(self) is not F105CheckpointValidation or self._seal is not _SEAL:
            raise CheckpointValidationError('checkpoint validation has no local factory seal')
        if type(self.identity) is not RunIdentity:
            raise CheckpointValidationError('run identity type mismatch')
        self.identity.__post_init__()
        if type(self.completed_updates) is not int or not 1 <= self.completed_updates <= 4096:
            raise CheckpointValidationError('checkpoint step must lie within 1..4096')
        if (type(self.group_records) is not tuple or len(self.group_records) != 128
                or any(type(row) is not CertifiedGroupScore for row in self.group_records)):
            raise CheckpointValidationError('complete retained 128-group factory record roster required')
        ids = _roster(tuple(row.group_id for row in self.group_records))
        for ordinal, row in enumerate(self.group_records):
            if type(row.ordinal) is not int or row.ordinal != ordinal:
                raise CheckpointValidationError('group ordinal mismatch')
            if row.score_integrity_sha256 != _digest(
                    'heterodiff-f144-domain-bridged-group-score-v1', _bound_group_payload(self, row)):
                raise CheckpointValidationError('group score checkpoint/input binding mismatch')
        roster_sha = _digest('heterodiff-f144-complete-f134-validation-group-roster-v1',
                             [hashlib.sha256(item).hexdigest() for item in ids])
        if roster_sha != self.group_roster_sha256 or _subject(self) != self.complete_roster_certificate_subject_sha256:
            raise CheckpointValidationError('complete roster subject binding mismatch')
        if _digest('heterodiff-f105-checkpoint-validation-bridge-v1', _result_payload(self)) != self._integrity_sha256:
            raise CheckpointValidationError('checkpoint validation integrity mismatch')

    def aggregate_hex(self):
        self._validate()
        total = sum((Fraction(*row.factory_score.binary64_score.as_integer_ratio())
                     for row in self.group_records), Fraction(0))
        return float(total / 128).hex()

    def validate_binding(self, identity, completed_updates, model_state, validation_group_ids):
        self._validate()
        _roster(validation_group_ids)
        if (type(identity) is not RunIdentity or identity != self.identity
                or type(completed_updates) is not int or completed_updates != self.completed_updates
                or validation_group_ids != tuple(row.group_id for row in self.group_records)
                or checkpoint_model_state_sha256(model_state) != self.checkpoint_content_sha256):
            raise CheckpointValidationError('validation does not bind this run/checkpoint/roster/model state')
        return True

    def to_validation_observation(self):
        """Compatibility projection only; callers must also retain this full result."""
        self._validate()
        return ValidationObservation(torch.tensor(
            [row.factory_score.binary64_score for row in self.group_records], dtype=torch.float64))

    def summary(self):
        self._validate()
        return {
            'schema_version': 'heterodiff-f105-checkpoint-validation-bridge-v1',
            'scope': 'LOCAL_SUPPLIED_CONFIGURATION_F105_SCORING_NOT_PRODUCTION_ADMISSION',
            'identity': self.identity.to_dict(), 'completed_optimizer_updates': self.completed_updates,
            'group_count': 128, 'draws_per_group': 64,
            'aggregate_binary64_hex': self.aggregate_hex(),
            'checkpoint_model_state_sha256': self.checkpoint_content_sha256,
            'checkpoint_binding_kind': 'MODEL_STATE_ONLY_NOT_FULL_CHECKPOINT_ARCHIVE',
            'cpu_reference_configuration_sha256': self.cpu_reference_configuration_sha256,
            'group_roster_sha256': self.group_roster_sha256,
            'complete_roster_certificate_subject_sha256': self.complete_roster_certificate_subject_sha256,
            'validation_integrity_sha256': self._integrity_sha256,
            'registry_domain_id': self.identity.domain_id,
            'metric_domain_id': DOMAIN_ALIASES[self.identity.domain_id],
            'actual_f105_factory_records_retained': True,
            'f144_checkpoint_cadence_satisfied': self.completed_updates % 256 == 0,
            'complete_128_group_subject_bound': True,
            'frozen_f144_structural_helper_compatible': False,
            'frozen_helper_incompatibility': 'REGISTRY_DOMAIN_VS_METRIC_DOMAIN_FACTORY_DIGEST',
            'production_history_authenticated': False,
            'full_checkpoint_archive_bound': False,
            'conditional_draw_generation_authenticated': False,
            'observed_truth_or_domain_admission_authenticated': False,
            'f134_scientific_roster_membership_authenticated': False,
            'gpu_training_configuration_certified': False,
            'scientific_execution_or_selection_authorized': False,
        }


def evaluate_checkpoint_validation(identity, completed_updates, model_state,
                                   validation_group_ids, group_inputs, *,
                                   expected_cpu_configuration_sha256=None,
                                   symbolic_event_pair_work_limit=DEFAULT_SYMBOLIC_EVENT_PAIR_WORK_LIMIT):
    """Compute 128 real F105 scores from exact supplied R64 configurations."""
    if type(identity) is not RunIdentity:
        raise CheckpointValidationError('identity must be an exact RunIdentity')
    identity.__post_init__()
    if type(completed_updates) is not int or not 1 <= completed_updates <= 4096:
        raise CheckpointValidationError('checkpoint step must lie within 1..4096')
    ids = _roster(validation_group_ids)
    if (type(group_inputs) is not tuple or len(group_inputs) != 128
            or any(type(item) is not GroupConditionalConfigurations for item in group_inputs)):
        raise CheckpointValidationError('128 exact supplied conditional-configuration groups required')
    for group_id, supplied in zip(ids, group_inputs):
        supplied.__post_init__()
        if supplied.group_id != group_id or supplied.target.domain_id != DOMAIN_ALIASES[identity.domain_id]:
            raise CheckpointValidationError('supplied group order/ID/domain does not match validation roster')
    row = next(row for row in frozen.executable_configuration_rows()
               if row['method_id'] == identity.method_id and row['domain_id'] == identity.domain_id)
    reference_sha = row['executable_configuration_sha256']
    if expected_cpu_configuration_sha256 is not None and expected_cpu_configuration_sha256 != reference_sha:
        raise CheckpointValidationError('CPU reference configuration binding mismatch')
    result = object.__new__(F105CheckpointValidation)
    for name, value in {
        'identity': identity, 'completed_updates': completed_updates,
        'checkpoint_content_sha256': checkpoint_model_state_sha256(model_state),
        'cpu_reference_configuration_sha256': reference_sha,
        'selection_unit_sha256': _digest('heterodiff-f105-checkpoint-selection-unit-v1', {
            'identity': identity.to_dict(), 'cpu_reference_configuration_sha256': reference_sha,
            'f144_semantics_sha256': frozen.f144_semantics_sha256()}),
        'group_roster_sha256': _digest('heterodiff-f144-complete-f134-validation-group-roster-v1',
                                      [hashlib.sha256(item).hexdigest() for item in ids]),
        '_seal': _SEAL,
    }.items():
        object.__setattr__(result, name, value)
    records = []
    for ordinal, supplied in enumerate(group_inputs):
        actual_score = production_conditional_cks_score(
            supplied.draws, supplied.target,
            symbolic_event_pair_work_limit=symbolic_event_pair_work_limit)
        record = CertifiedGroupScore(ordinal, supplied.group_id, supplied.input_sha256(), actual_score, '')
        object.__setattr__(record, 'score_integrity_sha256', _digest(
            'heterodiff-f144-domain-bridged-group-score-v1', _bound_group_payload(result, record)))
        records.append(record)
    object.__setattr__(result, 'group_records', tuple(records))
    object.__setattr__(result, 'complete_roster_certificate_subject_sha256', _subject(result))
    object.__setattr__(result, '_integrity_sha256', _digest(
        'heterodiff-f105-checkpoint-validation-bridge-v1', _result_payload(result)))
    result._validate()
    return result


def select_earliest_best_checkpoint(validations):
    """Lower-is-better, canonical-hex equality, earliest exact tie; not admission."""
    if type(validations) is not tuple or not validations:
        raise CheckpointValidationError('selection requires a nonempty exact tuple')
    for item in validations:
        if type(item) is not F105CheckpointValidation:
            raise CheckpointValidationError('selection requires actual factory-bound validation results')
        item._validate()
    first = validations[0]
    if (len({item.completed_updates for item in validations}) != len(validations)
            or any((item.identity, item.group_roster_sha256, item.selection_unit_sha256)
                   != (first.identity, first.group_roster_sha256, first.selection_unit_sha256)
                   for item in validations)):
        raise CheckpointValidationError('checkpoint roster has duplicate steps or cross-run bindings')
    scores = [(item, item.aggregate_hex()) for item in validations]
    lowest = min(float.fromhex(value) for _, value in scores)
    tied = [(item, value) for item, value in scores if float.fromhex(value) == lowest]
    if len({value for _, value in tied}) != 1:
        raise CheckpointValidationError('numerically equal but nonidentical canonical hex scores')
    return min((item for item, _ in tied), key=lambda item: item.completed_updates)
