"""Invented CPU configurations only: no data, generator, GPU, or paid execution."""

from collections import OrderedDict
from copy import copy
from fractions import Fraction
import hashlib

import pytest
import torch

from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    physionet_configuration, physionet_event_from_decimal_token, retail_configuration,
)
from heterodiff.evaluation.two_domain_count_normalized_event_cks_production import (
    ProductionCKSScore, score_record,
)
from heterodiff.experiments import two_domain_f105_checkpoint_validation as bridge
from heterodiff.experiments import two_domain_training_checkpoint_plan as frozen
from heterodiff.experiments.two_domain_gpu_training import RunIdentity, ValidationObservation

IDS = tuple(('validation-%03d' % index).encode() for index in range(128))
STATE = {'weight': torch.tensor([1.0, 2.0], dtype=torch.float32)}


def identity(domain='physionet-challenge-2012', seed=1):
    return RunIdentity('association-aware-guide-plus-residual', domain, 0, seed)


def groups(domain='physionet-challenge-2012', varied=False):
    configuration = (physionet_configuration(()) if domain == 'physionet-challenge-2012'
                     else retail_configuration(()))
    target = configuration
    if varied:
        target = physionet_configuration((physionet_event_from_decimal_token(
            elapsed_minutes=0, parameter='HR', value_text='80'),))
    return tuple(bridge.GroupConditionalConfigurations(
        group_id, (configuration,) * 64, target if index == 0 else configuration)
        for index, group_id in enumerate(IDS))


@pytest.fixture(scope='module', params=tuple(bridge.DOMAIN_ALIASES))
def complete(request):
    domain = request.param
    return bridge.evaluate_checkpoint_validation(identity(domain), 256, STATE, IDS, groups(domain))


def clone_result(result):
    # A plain copy would invoke the deliberately blocked public constructor.
    copied = object.__new__(bridge.F105CheckpointValidation)
    for name, value in vars(result).items():
        object.__setattr__(copied, name, value)
    return copied


def test_actual_factory_records_and_exact_complete_roster(complete):
    assert complete.validate_binding(complete.identity, 256, STATE, IDS)
    assert len(complete.group_records) == 128
    assert len({id(row.factory_score) for row in complete.group_records}) == 128
    for ordinal, group in enumerate(complete.group_records):
        assert group.ordinal == ordinal and group.group_id == IDS[ordinal]
        assert type(group.factory_score) is ProductionCKSScore
        record = score_record(group.factory_score)
        assert record['draw_count'] == 64
        assert record['domain_id'] == bridge.DOMAIN_ALIASES[complete.identity.domain_id]
        assert record['integrity_sha256'] == group.factory_score._integrity_sha256
        assert -2 <= group.factory_score.binary64_score <= 1
    observation = complete.to_validation_observation()
    assert type(observation) is ValidationObservation
    assert observation.group_scores.device.type == 'cpu'
    assert observation.group_scores.dtype == torch.float64
    assert observation.aggregate_hex() == complete.aggregate_hex() == (-1.0).hex()


def test_real_factory_digest_is_not_replaced_by_registry_domain_digest(complete):
    actual = complete.group_records[0].factory_score
    old_structural_expectation = frozen._f105_factory_integrity_sha256(
        binary64_score_hex=actual.binary64_score_hex,
        domain_id=complete.identity.domain_id, formal_score_sha256=actual.formal_score_sha256,
        symbolic_event_pair_work_units=actual.symbolic_event_pair_work_units)
    assert actual._integrity_sha256 != old_structural_expectation
    report = complete.summary()
    assert report['actual_f105_factory_records_retained']
    assert report['complete_128_group_subject_bound']
    assert report['f144_checkpoint_cadence_satisfied']
    assert not report['frozen_f144_structural_helper_compatible']
    for field in ('production_history_authenticated', 'full_checkpoint_archive_bound',
                  'conditional_draw_generation_authenticated',
                  'observed_truth_or_domain_admission_authenticated',
                  'f134_scientific_roster_membership_authenticated',
                  'gpu_training_configuration_certified', 'scientific_execution_or_selection_authorized'):
        assert report[field] is False
    expected = frozen.complete_roster_certificate_subject_sha256(
        checkpoint_content_sha256=complete.checkpoint_content_sha256,
        domain_id=complete.identity.domain_id,
        executable_configuration_sha256=complete.cpu_reference_configuration_sha256,
        group_roster_sha256=complete.group_roster_sha256,
        group_score_integrity_sha256s=[row.score_integrity_sha256 for row in complete.group_records],
        method_id=complete.identity.method_id, selection_unit_sha256=complete.selection_unit_sha256)
    assert complete.complete_roster_certificate_subject_sha256 == expected


@pytest.mark.parametrize('difference', ['seed', 'step', 'state', 'roster'])
def test_cross_checkpoint_binding_rejected(complete, difference):
    run = complete.identity
    step, state, ids = 256, STATE, IDS
    if difference == 'seed':
        run = identity(run.domain_id, seed=2)
    elif difference == 'step':
        step = 512
    elif difference == 'state':
        state = {'weight': torch.tensor([1.0, 3.0])}
    else:
        ids = tuple(item + b'-other' for item in IDS)
    with pytest.raises(bridge.CheckpointValidationError, match='does not bind'):
        complete.validate_binding(run, step, state, ids)


@pytest.mark.parametrize('difference', ['omit_group', 'group_id', 'score', 'subject', 'input'])
def test_tampered_retained_records_rejected(complete, difference):
    broken = clone_result(complete)
    if difference == 'omit_group':
        object.__setattr__(broken, 'group_records', complete.group_records[:-1])
    elif difference == 'subject':
        object.__setattr__(broken, 'complete_roster_certificate_subject_sha256', '0' * 64)
    else:
        row = copy(complete.group_records[0])
        if difference == 'group_id':
            object.__setattr__(row, 'group_id', b'wrong')
        elif difference == 'score':
            object.__setattr__(row, 'factory_score', -1.0)
        else:
            object.__setattr__(row, 'supplied_input_sha256', '0' * 64)
        object.__setattr__(broken, 'group_records', (row,) + complete.group_records[1:])
    with pytest.raises((ValueError, TypeError)):
        broken.aggregate_hex()


def test_no_arbitrary_score_constructor_or_generic_callback_as_proof():
    with pytest.raises(bridge.CheckpointValidationError, match='evaluate_checkpoint_validation'):
        bridge.F105CheckpointValidation()
    with pytest.raises(bridge.CheckpointValidationError, match='actual factory-bound'):
        bridge.select_earliest_best_checkpoint((ValidationObservation(torch.zeros(128, dtype=torch.float64)),))


@pytest.mark.parametrize('difference', ['short', 'duplicate', 'unordered', 'list', 'foreign_domain',
                                       'group_order', 'float_score', 'bad_reference', 'bad_step'])
def test_invalid_supplied_rosters_rejected_before_factory_call(monkeypatch, difference):
    supplied = groups()
    ids, expected, step = IDS, None, 256
    if difference == 'short':
        supplied = supplied[:-1]
    elif difference == 'duplicate':
        ids = (IDS[0],) + IDS[:-1]
    elif difference == 'unordered':
        ids = IDS[::-1]
    elif difference == 'list':
        ids = list(IDS)
    elif difference == 'foreign_domain':
        supplied = groups('online-retail-ii')
    elif difference == 'group_order':
        supplied = supplied[::-1]
    elif difference == 'float_score':
        supplied = (-1.0,) * 128
    elif difference == 'bad_reference':
        expected = '0' * 64
    else:
        step = True
    def forbidden(*args, **kwargs):
        raise AssertionError('factory must not run after an invalid roster/binding')
    monkeypatch.setattr(bridge, 'production_conditional_cks_score', forbidden)
    with pytest.raises(bridge.CheckpointValidationError):
        bridge.evaluate_checkpoint_validation(identity(), step, STATE, ids, supplied,
                                               expected_cpu_configuration_sha256=expected)


@pytest.mark.parametrize('draw_count', [0, 2, 63, 65, 128])
def test_not_exact_r64_rejected(draw_count):
    empty = physionet_configuration(())
    with pytest.raises(bridge.CheckpointValidationError, match='R=64'):
        bridge.GroupConditionalConfigurations(b'group', (empty,) * draw_count, empty)


def test_state_hash_binds_dtype_shape_name_bytes_and_not_mapping_order():
    a = torch.tensor([1.0, 2.0])
    original = {'a': a, 'b': torch.tensor(3, dtype=torch.int64)}
    digest = bridge.checkpoint_model_state_sha256(original)
    assert digest == bridge.checkpoint_model_state_sha256(OrderedDict(reversed(list(original.items()))))
    for changed in ({'a': a.to(torch.float64), 'b': original['b']},
                    {'a': a.reshape(1, 2), 'b': original['b']},
                    {'a': torch.tensor([1.0, 3.0]), 'b': original['b']},
                    {'other': a, 'b': original['b']}):
        assert bridge.checkpoint_model_state_sha256(changed) != digest
    model = torch.nn.Linear(1, 1)
    assert bridge.checkpoint_model_state_sha256(model) == bridge.checkpoint_model_state_sha256(model.state_dict())
    with pytest.raises(bridge.CheckpointValidationError, match='nonfinite'):
        bridge.checkpoint_model_state_sha256({'weight': torch.tensor(float('nan'))})


def test_noncanonical_input_is_rejected_without_repair_or_mutation():
    events = tuple(physionet_event_from_decimal_token(
        elapsed_minutes=0, parameter='HR', value_text=value) for value in ('80', '90'))
    configuration = physionet_configuration(events)
    tampered_events = configuration.events[::-1]
    object.__setattr__(configuration, 'events', tampered_events)
    with pytest.raises(bridge.CheckpointValidationError, match='no input repair'):
        bridge.GroupConditionalConfigurations(b'group', (configuration,) * 64, configuration)
    assert configuration.events == tampered_events


def test_nontrivial_actual_factory_scores_exact_sum_round_once_and_earliest_tie():
    supplied = groups(varied=True)
    later = bridge.evaluate_checkpoint_validation(identity(), 512, STATE, IDS, supplied)
    earlier = bridge.evaluate_checkpoint_validation(identity(), 256, STATE, IDS, supplied)
    assert later.group_records[0].factory_score.binary64_score != -1.0
    exact = sum((Fraction(*row.factory_score.binary64_score.as_integer_ratio())
                 for row in later.group_records), Fraction(0)) / 128
    assert later.aggregate_hex() == float(exact).hex()
    assert later.aggregate_hex() == earlier.aggregate_hex()
    assert bridge.select_earliest_best_checkpoint((later, earlier)) is earlier
    assert later.complete_roster_certificate_subject_sha256 == earlier.complete_roster_certificate_subject_sha256
    # The complete subject binds model state, while the validation record also binds step.
    assert later.summary()['validation_integrity_sha256'] != earlier.summary()['validation_integrity_sha256']
    with pytest.raises(bridge.CheckpointValidationError, match='duplicate steps'):
        bridge.select_earliest_best_checkpoint((later, later))


def test_short_local_checkpoint_scores_do_not_claim_f144_cadence():
    result = bridge.evaluate_checkpoint_validation(identity(), 1, STATE, IDS, groups())
    assert not result.summary()['f144_checkpoint_cadence_satisfied']
    assert result.summary()['complete_128_group_subject_bound']
    assert result.group_roster_sha256 == bridge._digest(
        'heterodiff-f144-complete-f134-validation-group-roster-v1',
        [hashlib.sha256(item).hexdigest() for item in IDS])
