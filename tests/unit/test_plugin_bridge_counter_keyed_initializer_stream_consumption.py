"""Hostile tests for checkpoint-25 initializer-stream prefix custody."""

import ast
import copy
import inspect
from pathlib import Path
import pickle
import subprocess
import sys

import numpy as np
import pytest


pytest.importorskip(
    "torch", reason="initializer-stream consumption requires the PyTorch stack"
)

import test_plugin_bridge_counter_keyed_operational_epoch_loop as checkpoint24_tests
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_continuous_route_evidence as route_evidence,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initializer_stream_consumption as consumption,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_lineage_contract as lineage,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_operational_epoch_loop as epoch,
)
from heterodiff.theory.configuration_reference import TransformedEvent  # noqa: E402


CONSUMPTION_ROLE = "c" * 64
CONSUMPTION_POLICY = getattr(
    consumption,
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_POLICY",
)
MAX_WORDS_PER_OCCURRENCE = getattr(
    consumption,
    "COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_" "MAX_RAW64_WORDS_PER_OCCURRENCE",
)
MAX_TOTAL_WORDS = getattr(
    consumption,
    "COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_TOTAL_RAW64_WORDS",
)
_certify_consumption = getattr(
    consumption,
    "certify_plugin_bridge_counter_keyed_initializer_stream_consumption",
)
_require_consumption = getattr(
    consumption,
    "require_matching_plugin_bridge_counter_keyed_initializer_stream_consumption",
)
_validate_consumption_certificate = getattr(
    consumption,
    "validate_plugin_bridge_counter_keyed_"
    "initializer_stream_consumption_certificate",
)


def _certified_bundle(*, total_cap=2):
    bundle = checkpoint24_tests._certify_epoch(
        checkpoint24_tests.checkpoint23_tests._bundle(
            tight=True,
            total_cap=total_cap,
        )
    )
    owner = _certify_consumption(
        bundle["epoch_owner"],
        consumption_policy=CONSUMPTION_POLICY,
        consumption_role_sha256=CONSUMPTION_ROLE,
    )
    bundle["consumption_owner"] = owner
    return bundle


@pytest.fixture(scope="module")
def tight_bundle():
    return _certified_bundle(total_cap=2)


def _bootstrap(
    bundle,
    state,
    *,
    run_id,
    initialization_index=0,
):
    intensity, _ = checkpoint24_tests._parents(bundle, state=state)
    return bundle["contract_owner"].bootstrap_lineage(
        intensity,
        run_id=run_id,
        initialization_index=initialization_index,
    )


@pytest.fixture(scope="module")
def empty_state(tight_bundle):
    return _bootstrap(tight_bundle, (), run_id=2500)


@pytest.fixture(scope="module")
def single_state(tight_bundle):
    return _bootstrap(
        tight_bundle,
        (TransformedEvent(0),),
        run_id=2501,
        initialization_index=3,
    )


@pytest.fixture(scope="module")
def duplicate_state(tight_bundle):
    return _bootstrap(
        tight_bundle,
        (
            TransformedEvent(0),
            TransformedEvent(0),
        ),
        run_id=2502,
        initialization_index=5,
    )


@pytest.fixture(scope="module")
def duplicate_result(tight_bundle, duplicate_state):
    return tight_bundle["consumption_owner"].consume(
        duplicate_state,
        raw64_word_counts=(1, 5),
    )


def _direct_prefix(*, run_id, serial, word_count):
    generator = np.random.Generator(
        np.random.Philox(
            key=np.asarray(
                (run_id, lineage.COUNTER_KEY_DOMAIN_TAG_INITIALIZER),
                dtype=np.uint64,
            ),
            counter=np.asarray(
                (
                    0,
                    consumption.COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_STEP_INDEX,
                    serial,
                    0,
                ),
                dtype=np.uint64,
            ),
        )
    )
    raw = generator.bit_generator.random_raw(word_count)
    words = tuple(int(value) for value in np.atleast_1d(raw))
    return words, route_evidence._capture_philox_state(generator)


def _forged_record(record, **updates):
    forged = object.__new__(type(record))
    for name in type(record).__annotations__:
        object.__setattr__(
            forged,
            name,
            updates.get(name, getattr(record, name)),
        )
    return forged


def _occurrence_values(record, **updates):
    values = {
        name: updates.get(name, getattr(record, name))
        for name in consumption._occurrence_fields()
    }
    values["record_sha256"] = "0" * 64
    values["record_sha256"] = consumption._thinning._semantic_digest(
        consumption._occurrence_payload(values)
    )
    return values


def _result_values(result, **updates):
    values = {
        name: updates.get(name, getattr(result, name))
        for name in consumption._result_fields()
    }
    if "occurrences" in updates and "occurrence_sha256s" not in updates:
        values["occurrence_sha256s"] = tuple(
            record.record_sha256 for record in values["occurrences"]
        )
    values["result_sha256"] = "0" * 64
    values["result_sha256"] = consumption._thinning._semantic_digest(
        consumption._result_payload(values)
    )
    return values


def _certificate_values(certificate, **updates):
    values = {
        name: updates.get(name, getattr(certificate, name))
        for name in consumption._certificate_fields()
    }
    values["certificate_sha256"] = "0" * 64
    values["certificate_sha256"] = consumption._thinning._semantic_digest(
        consumption._certificate_payload(values)
    )
    return values


def _construct_occurrence(values):
    return consumption.CounterKeyedInitializerOccurrenceConsumption(
        **values,
        _construction_token=consumption._OCCURRENCE_TOKEN,
    )


def _construct_result(values):
    return consumption.CounterKeyedInitializerStreamConsumptionResult(
        **values,
        _construction_token=consumption._RESULT_TOKEN,
    )


def _construct_certificate(values):
    return consumption.CounterKeyedInitializerStreamConsumptionCertificate(
        **values,
        _construction_token=consumption._CERTIFICATE_TOKEN,
    )


def _structural_bootstrap_state(
    bundle,
    *,
    count,
    run_id,
    initialization_index=0,
):
    certificate = bundle["contract_owner"].certificate
    occurrences = []
    for position in range(count):
        identifier = lineage._make_identifier(
            certificate,
            run_id=run_id,
            serial=position + 1,
            origin_kind="initial",
            origin_initialization_index=initialization_index,
            origin_initial_position=position,
        )
        occurrences.append(
            lineage._make_occurrence(
                certificate,
                identifier,
                TransformedEvent(0),
            )
        )
    return lineage._make_state(
        certificate,
        run_id=run_id,
        initialization_index=initialization_index,
        occurrences=tuple(occurrences),
        retired_identifiers=(),
        next_serial=count + 1,
    )


def test_exact_tag3_prefixes_and_identity_custody(
    tight_bundle,
    duplicate_state,
    duplicate_result,
):
    owner = tight_bundle["consumption_owner"]
    result = duplicate_result
    assert result.initial_state is duplicate_state
    assert result.final_state is duplicate_state
    assert result.exact_initial_final_state_identity is True
    assert result.initial_model_projection_unchanged is True
    assert result.no_caller_rng is True
    assert result.empty_state_zero_word is False
    assert result.all_requested_streams_consumed is True
    assert result.step_index == 0
    assert result.raw64_word_counts == (1, 5)
    assert result.total_raw64_words == 6
    assert result.stream_count == 2
    assert len(result.occurrences) == len(duplicate_state.occurrences)

    for position, (parent, record, count) in enumerate(
        zip(duplicate_state.occurrences, result.occurrences, (1, 5))
    ):
        stream = record.initializer_stream
        address = stream.address
        expected_words, expected_final = _direct_prefix(
            run_id=duplicate_state.run_id,
            serial=parent.identifier.serial,
            word_count=count,
        )
        assert record.position == position
        assert record.occurrence is parent
        assert record.identifier is parent.identifier
        assert record.event is parent.event
        assert record.occurrence_identity_preserved is True
        assert record.event_identity_preserved is True
        assert record.run_id == duplicate_state.run_id
        assert record.initialization_index == duplicate_state.initialization_index
        assert record.step_index == 0
        assert record.occurrence_serial == parent.identifier.serial
        assert record.raw64_word_count == count
        assert address.domain == lineage.COUNTER_KEY_DOMAIN_INITIALIZER
        assert address.domain_tag == lineage.COUNTER_KEY_DOMAIN_TAG_INITIALIZER
        assert address.philox_key == (duplicate_state.run_id, 3)
        assert address.philox_counter == (
            0,
            0,
            parent.identifier.serial,
            0,
        )
        assert record.stream_initial_state is stream.initial_state
        assert record.raw64_words == expected_words
        assert record.stream_final_state.state_sha256 == expected_final.state_sha256
        assert record.stream_final_state.snapshot_sha256 == (
            expected_final.snapshot_sha256
        )
        assert record.stream_final_state.key == stream.initial_state.key
        assert record.stream_final_state.counter[1:] == (
            stream.initial_state.counter[1:]
        )
        assert record.parent_execution_used_this_stream is False
        assert record.successor_execution_invoked_this_stream is True
        assert record.successor_execution_consumed_this_stream is True
        assert record.no_upper_counter_carry is True
        assert record.same_runtime_only is True

    assert (
        owner.validate_result(
            result,
            duplicate_state,
            raw64_word_counts=(1, 5),
        )
        is result
    )


def test_equal_events_receive_distinct_identifier_addresses(
    duplicate_state,
    duplicate_result,
):
    first, second = duplicate_state.occurrences
    first_record, second_record = duplicate_result.occurrences
    assert first.event == second.event
    assert first.event is not second.event
    assert first.identifier is not second.identifier
    assert first.identifier.serial == 1
    assert second.identifier.serial == 2
    assert first_record.initializer_stream.address != (
        second_record.initializer_stream.address
    )
    assert first_record.initializer_stream.address.philox_counter != (
        second_record.initializer_stream.address.philox_counter
    )
    assert first_record.initializer_stream_sha256 != (
        second_record.initializer_stream_sha256
    )


def test_empty_bootstrap_is_the_only_successful_zero_word_case(
    tight_bundle,
    empty_state,
    monkeypatch,
):
    owner = tight_bundle["consumption_owner"]

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("empty initialization reached a stream factory")

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_initializer_stream",
        forbidden,
    )
    result = owner.consume(empty_state, raw64_word_counts=())
    assert result.initial_state is empty_state
    assert result.final_state is empty_state
    assert result.raw64_word_counts == ()
    assert result.occurrences == ()
    assert result.occurrence_sha256s == ()
    assert result.total_raw64_words == 0
    assert result.stream_count == 0
    assert result.empty_state_zero_word is True
    assert result.all_requested_streams_consumed is True
    assert owner.validate_result(result, empty_state, raw64_word_counts=()) is result


@pytest.mark.parametrize(
    "invalid",
    [0, -1, True, False, 1.0, np.int64(1), np.uint64(1)],
)
def test_each_live_count_requires_an_exact_positive_python_integer(
    tight_bundle,
    single_state,
    invalid,
    monkeypatch,
):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("invalid count reached a stream factory")

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_initializer_stream",
        forbidden,
    )
    with pytest.raises((TypeError, ValueError)):
        tight_bundle["consumption_owner"].consume(
            single_state,
            raw64_word_counts=(invalid,),
        )
    assert calls == []


@pytest.mark.parametrize(
    "counts",
    [[], np.asarray((1,), dtype=np.int64), (1, 2), ()],
)
def test_count_plan_requires_an_exact_complete_tuple(
    tight_bundle,
    single_state,
    counts,
):
    with pytest.raises((TypeError, ValueError)):
        tight_bundle["consumption_owner"].consume(
            single_state,
            raw64_word_counts=counts,
        )


def test_late_invalid_count_refuses_before_any_stream_is_issued(
    tight_bundle,
    duplicate_state,
    monkeypatch,
):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("incomplete preflight issued a stream")

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_initializer_stream",
        forbidden,
    )
    with pytest.raises((TypeError, ValueError)):
        tight_bundle["consumption_owner"].consume(
            duplicate_state,
            raw64_word_counts=(1, 0),
        )
    assert calls == []


def test_per_occurrence_cap_refuses_before_stream_issuance(
    tight_bundle,
    single_state,
    monkeypatch,
):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("over-cap request issued a stream")

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_initializer_stream",
        forbidden,
    )
    maximum = MAX_WORDS_PER_OCCURRENCE
    with pytest.raises(ValueError, match="bound|maximum|exceed"):
        tight_bundle["consumption_owner"].consume(
            single_state,
            raw64_word_counts=(maximum + 1,),
        )
    assert calls == []


def test_aggregate_word_cap_refuses_the_complete_plan_before_issuance(
    tight_bundle,
    monkeypatch,
):
    count = 62
    state = _structural_bootstrap_state(
        tight_bundle,
        count=count,
        run_id=2510,
    )
    counts = (MAX_WORDS_PER_OCCURRENCE,) * count
    assert sum(counts) > MAX_TOTAL_WORDS
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("aggregate-over-cap plan issued a stream")

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_initializer_stream",
        forbidden,
    )
    with pytest.raises(ValueError, match="total|aggregate|bound|exceed"):
        tight_bundle["consumption_owner"].consume(
            state,
            raw64_word_counts=counts,
        )
    assert calls == []


def test_oversized_plan_refuses_before_entry_validation_or_stream_issuance(
    tight_bundle,
    single_state,
    monkeypatch,
):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("oversized plan traversed an entry or issued a stream")

    monkeypatch.setattr(consumption, "_exact_positive_word_count", forbidden)
    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_initializer_stream",
        forbidden,
    )
    oversized = (1,) * (
        consumption.COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS + 1
    )
    with pytest.raises(ValueError, match="record bound"):
        tight_bundle["consumption_owner"].consume(
            single_state,
            raw64_word_counts=oversized,
        )
    assert calls == []


def test_oversized_state_refuses_before_nested_lineage_validation(
    tight_bundle,
    single_state,
    monkeypatch,
):
    maximum = (
        consumption.COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS
    )
    occurrence = single_state.occurrences[0]
    oversized_state = _forged_record(
        single_state,
        occurrences=(occurrence,) * (maximum + 1),
        occurrence_sha256s=(occurrence.occurrence_sha256,) * (maximum + 1),
        model_configuration=(occurrence.event,) * (maximum + 1),
    )

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("oversized state reached nested lineage validation")

    monkeypatch.setattr(lineage, "_validate_state", forbidden)
    with pytest.raises(ValueError, match="stream bound"):
        tight_bundle["consumption_owner"].consume(
            oversized_state,
            raw64_word_counts=(),
        )


def test_record_and_result_top_level_caps_preflight_before_deep_validation(
    tight_bundle,
    duplicate_result,
    monkeypatch,
):
    maximum_records = (
        consumption.COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS
    )
    first = duplicate_result.occurrences[0]
    result_values = {
        name: getattr(duplicate_result, name) for name in consumption._result_fields()
    }
    result_values["occurrences"] = (first,) * (maximum_records + 1)

    def forbidden_result(*args, **kwargs):
        del args, kwargs
        raise AssertionError("oversized result reached deep validation")

    monkeypatch.setattr(consumption, "_validate_result_record", forbidden_result)
    with pytest.raises(ValueError, match="tuple exceeds"):
        _construct_result(result_values)

    record_values = {
        name: getattr(first, name) for name in consumption._occurrence_fields()
    }
    record_values["raw64_word_count"] = MAX_WORDS_PER_OCCURRENCE + 1
    record_values["raw64_words"] = first.raw64_words * (MAX_WORDS_PER_OCCURRENCE + 1)

    def forbidden_record(*args, **kwargs):
        del args, kwargs
        raise AssertionError("oversized raw tuple reached deep validation")

    monkeypatch.setattr(consumption, "_validate_occurrence_record", forbidden_record)
    with pytest.raises(ValueError, match="maximum bound"):
        _construct_occurrence(record_values)


def test_swapped_duplicate_bootstrap_positions_refuse_before_issuance(
    tight_bundle,
    duplicate_state,
    monkeypatch,
):
    swapped = lineage._make_state(
        tight_bundle["contract_owner"].certificate,
        run_id=duplicate_state.run_id,
        initialization_index=duplicate_state.initialization_index,
        occurrences=tuple(reversed(duplicate_state.occurrences)),
        retired_identifiers=(),
        next_serial=duplicate_state.next_serial,
    )
    assert swapped.model_configuration == duplicate_state.model_configuration
    assert swapped.occurrences[0].identifier.serial == 2

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("non-positional bootstrap issued a stream")

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_initializer_stream",
        forbidden,
    )
    with pytest.raises(ValueError, match="position|bootstrap|serial"):
        tight_bundle["consumption_owner"].consume(
            swapped,
            raw64_word_counts=(1, 1),
        )


def test_retired_initial_identifier_refuses_before_issuance(
    tight_bundle,
    duplicate_state,
    monkeypatch,
):
    first, second = duplicate_state.occurrences
    retired = lineage._make_state(
        tight_bundle["contract_owner"].certificate,
        run_id=duplicate_state.run_id,
        initialization_index=duplicate_state.initialization_index,
        occurrences=(second,),
        retired_identifiers=(first.identifier,),
        next_serial=duplicate_state.next_serial,
    )

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("retired bootstrap identifier issued a stream")

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_initializer_stream",
        forbidden,
    )
    with pytest.raises(ValueError, match="retired|bootstrap|initial"):
        tight_bundle["consumption_owner"].consume(
            retired,
            raw64_word_counts=(1,),
        )


def test_advertised_maximum_prefix_replays_without_upper_carry(
    tight_bundle,
    single_state,
):
    maximum = MAX_WORDS_PER_OCCURRENCE
    result = tight_bundle["consumption_owner"].consume(
        single_state,
        raw64_word_counts=(maximum,),
    )
    record = result.occurrences[0]
    expected, expected_final = _direct_prefix(
        run_id=single_state.run_id,
        serial=single_state.occurrences[0].identifier.serial,
        word_count=maximum,
    )
    assert record.raw64_words == expected
    assert record.stream_final_state.snapshot_sha256 == (expected_final.snapshot_sha256)
    assert record.stream_final_state.key == record.stream_initial_state.key
    assert record.stream_final_state.counter[1:] == (
        record.stream_initial_state.counter[1:]
    )


def test_reissue_replays_and_longer_request_extends_the_same_prefix(
    tight_bundle,
    single_state,
):
    owner = tight_bundle["consumption_owner"]
    short = owner.consume(single_state, raw64_word_counts=(3,))
    replay = owner.consume(single_state, raw64_word_counts=(3,))
    longer = owner.consume(single_state, raw64_word_counts=(7,))
    short_record = short.occurrences[0]
    replay_record = replay.occurrences[0]
    longer_record = longer.occurrences[0]
    assert short is not replay
    assert short.result_sha256 == replay.result_sha256
    assert short_record is not replay_record
    assert short_record.record_sha256 == replay_record.record_sha256
    assert short_record.raw64_words == replay_record.raw64_words
    assert longer_record.raw64_words[:3] == short_record.raw64_words
    assert longer_record.raw64_word_count == 7
    assert longer_record.record_sha256 != short_record.record_sha256
    assert longer.result_sha256 != short.result_sha256


def test_initialization_index_is_provenance_not_an_address_limb(tight_bundle):
    first = _bootstrap(
        tight_bundle,
        (TransformedEvent(0),),
        run_id=2511,
        initialization_index=0,
    )
    second = _bootstrap(
        tight_bundle,
        (TransformedEvent(0),),
        run_id=2511,
        initialization_index=17,
    )
    first_result = tight_bundle["consumption_owner"].consume(
        first,
        raw64_word_counts=(3,),
    )
    second_result = tight_bundle["consumption_owner"].consume(
        second,
        raw64_word_counts=(3,),
    )
    first_record = first_result.occurrences[0]
    second_record = second_result.occurrences[0]
    assert first_record.initialization_index == 0
    assert second_record.initialization_index == 17
    assert first_record.initializer_stream.address.philox_key == (
        second_record.initializer_stream.address.philox_key
    )
    assert first_record.initializer_stream.address.philox_counter == (
        second_record.initializer_stream.address.philox_counter
    )
    assert first_record.raw64_words == second_record.raw64_words
    assert first_result.result_sha256 != second_result.result_sha256


def test_run_id_and_serial_separate_direct_prefixes(tight_bundle):
    first = _bootstrap(
        tight_bundle,
        (TransformedEvent(0),),
        run_id=2512,
    )
    second = _bootstrap(
        tight_bundle,
        (TransformedEvent(0),),
        run_id=2513,
    )
    first_record = (
        tight_bundle["consumption_owner"]
        .consume(
            first,
            raw64_word_counts=(3,),
        )
        .occurrences[0]
    )
    second_record = (
        tight_bundle["consumption_owner"]
        .consume(
            second,
            raw64_word_counts=(3,),
        )
        .occurrences[0]
    )
    assert first_record.initializer_stream.address.philox_key != (
        second_record.initializer_stream.address.philox_key
    )
    assert first_record.initializer_stream.address.philox_counter == (
        second_record.initializer_stream.address.philox_counter
    )
    assert first_record.initializer_stream_sha256 != (
        second_record.initializer_stream_sha256
    )


def test_only_tag3_factory_is_used_once_per_live_identifier(
    tight_bundle,
    duplicate_state,
    monkeypatch,
):
    owner = tight_bundle["consumption_owner"]
    contract_owner = tight_bundle["contract_owner"]
    original = lineage.CounterKeyedLineageContractOwner.make_initializer_stream
    calls = []

    def logged(self, run_id, step_index, occurrence_serial):
        calls.append((self, run_id, step_index, occurrence_serial))
        return original(self, run_id, step_index, occurrence_serial)

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("initializer consumption invoked another domain")

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_initializer_stream",
        logged,
    )
    for name in (
        "make_jump_proposal_stream",
        "make_terminal_wait_stream",
        "make_brownian_left_stream",
        "make_brownian_right_stream",
    ):
        monkeypatch.setattr(
            lineage.CounterKeyedLineageContractOwner,
            name,
            forbidden,
        )
    monkeypatch.setattr(
        epoch.CounterKeyedOperationalEpochLoop,
        "make_operational_epoch_stream",
        forbidden,
    )
    owner.consume(duplicate_state, raw64_word_counts=(2, 3))
    assert calls == [
        (contract_owner, duplicate_state.run_id, 0, 1),
        (contract_owner, duplicate_state.run_id, 0, 2),
    ]


def test_consume_and_validation_do_not_accept_or_advance_caller_rng(
    tight_bundle,
    single_state,
):
    owner = tight_bundle["consumption_owner"]
    assert "rng" not in inspect.signature(owner.consume).parameters
    assert "rng" not in inspect.signature(owner.validate_result).parameters
    original = np.random.get_state()
    try:
        np.random.seed(2505)
        before = np.random.get_state()
        result = owner.consume(single_state, raw64_word_counts=(2,))
        owner.validate_result(result, single_state, raw64_word_counts=(2,))
        after = np.random.get_state()
        assert before[0] == after[0]
        assert np.array_equal(before[1], after[1])
        assert before[2:] == after[2:]
    finally:
        np.random.set_state(original)

    with pytest.raises(TypeError):
        owner.consume(
            single_state,
            raw64_word_counts=(1,),
            rng=np.random.default_rng(1),
        )


def test_nonbootstrap_lineage_refuses_before_stream_issuance(
    tight_bundle,
    single_state,
    monkeypatch,
):
    certificate = tight_bundle["contract_owner"].certificate
    parent = single_state.occurrences[0]
    created_identifier = lineage._make_identifier(
        certificate,
        run_id=single_state.run_id,
        serial=2,
        origin_kind="birth",
        origin_step_index=0,
        origin_proposal_index=0,
    )
    created = lineage._make_occurrence(
        certificate,
        created_identifier,
        TransformedEvent(1),
    )
    edited_state = lineage._make_state(
        certificate,
        run_id=single_state.run_id,
        initialization_index=single_state.initialization_index,
        occurrences=tuple(
            sorted((parent, created), key=lambda item: item.event.model_key())
        ),
        retired_identifiers=(),
        next_serial=3,
    )

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("nonbootstrap state reached a stream factory")

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_initializer_stream",
        forbidden,
    )
    with pytest.raises(ValueError, match="bootstrap|initial"):
        tight_bundle["consumption_owner"].consume(
            edited_state,
            raw64_word_counts=(1, 1),
        )


def test_record_and_result_validation_require_exact_parent_objects(
    tight_bundle,
    duplicate_state,
    duplicate_result,
):
    owner = tight_bundle["consumption_owner"]
    record = duplicate_result.occurrences[0]
    parent = duplicate_state.occurrences[0]
    assert (
        owner.validate_occurrence_consumption(
            record,
            parent,
            position=0,
            raw64_word_count=1,
        )
        is record
    )

    parent_clone = lineage._make_occurrence(
        record.identifier.certificate
        if hasattr(record.identifier, "certificate")
        else tight_bundle["contract_owner"].certificate,
        parent.identifier,
        TransformedEvent(parent.event.event_type, parent.event.coordinates),
    )
    assert parent_clone.occurrence_sha256 == parent.occurrence_sha256
    assert parent_clone is not parent
    with pytest.raises((TypeError, ValueError)):
        owner.validate_occurrence_consumption(
            record,
            parent_clone,
            position=0,
            raw64_word_count=1,
        )

    cloned_state = lineage._make_state(
        tight_bundle["contract_owner"].certificate,
        run_id=duplicate_state.run_id,
        initialization_index=duplicate_state.initialization_index,
        occurrences=duplicate_state.occurrences,
        retired_identifiers=duplicate_state.retired_identifiers,
        next_serial=duplicate_state.next_serial,
    )
    assert cloned_state.state_sha256 == duplicate_state.state_sha256
    assert cloned_state is not duplicate_state
    with pytest.raises((TypeError, ValueError)):
        owner.validate_result(
            duplicate_result,
            cloned_state,
            raw64_word_counts=(1, 5),
        )


def test_wrong_validation_plan_position_and_occurrence_refuse(
    tight_bundle,
    duplicate_state,
    duplicate_result,
):
    owner = tight_bundle["consumption_owner"]
    first, second = duplicate_result.occurrences
    with pytest.raises((TypeError, ValueError)):
        owner.validate_occurrence_consumption(
            first,
            duplicate_state.occurrences[1],
            position=0,
            raw64_word_count=1,
        )
    with pytest.raises((TypeError, ValueError)):
        owner.validate_occurrence_consumption(
            first,
            duplicate_state.occurrences[0],
            position=1,
            raw64_word_count=1,
        )
    with pytest.raises((TypeError, ValueError)):
        owner.validate_occurrence_consumption(
            second,
            duplicate_state.occurrences[1],
            position=1,
            raw64_word_count=1,
        )
    with pytest.raises((TypeError, ValueError)):
        owner.validate_result(
            duplicate_result,
            duplicate_state,
            raw64_word_counts=(5, 1),
        )


def test_same_role_alien_consumption_owner_result_refuses(
    tight_bundle,
    duplicate_state,
    duplicate_result,
):
    alien = _certify_consumption(
        tight_bundle["epoch_owner"],
        consumption_policy=CONSUMPTION_POLICY,
        consumption_role_sha256=CONSUMPTION_ROLE,
    )
    alien_result = alien.consume(
        duplicate_state,
        raw64_word_counts=(1, 5),
    )
    assert alien is not tight_bundle["consumption_owner"]
    assert alien.certificate is not duplicate_result.certificate
    assert alien.certificate.certificate_sha256 == (duplicate_result.certificate_sha256)
    assert alien_result.result_sha256 == duplicate_result.result_sha256
    with pytest.raises((TypeError, ValueError)):
        tight_bundle["consumption_owner"].validate_result(
            alien_result,
            duplicate_state,
            raw64_word_counts=(1, 5),
        )


def test_stale_nested_record_mutations_refuse_during_owner_replay(
    tight_bundle,
    duplicate_state,
    duplicate_result,
):
    owner = tight_bundle["consumption_owner"]
    first = duplicate_result.occurrences[0]
    other = duplicate_result.occurrences[1]
    attacks = (
        {"position": 1},
        {"occurrence": duplicate_state.occurrences[1]},
        {"identifier": duplicate_state.occurrences[1].identifier},
        {"event": duplicate_state.occurrences[1].event},
        {"occurrence_serial": 2},
        {"raw64_word_count": 2},
        {"raw64_words": (first.raw64_words[0] ^ 1,)},
        {"initializer_stream": other.initializer_stream},
        {"stream_final_state": other.stream_final_state},
        {"parent_execution_used_this_stream": True},
        {"successor_execution_invoked_this_stream": False},
        {"successor_execution_consumed_this_stream": False},
        {"no_upper_counter_carry": False},
        {"same_runtime_only": False},
        {"occurrence_identity_preserved": False},
        {"event_identity_preserved": False},
    )
    for updates in attacks:
        forged = _forged_record(first, **updates)
        with pytest.raises((TypeError, ValueError)):
            owner.validate_occurrence_consumption(
                forged,
                duplicate_state.occurrences[0],
                position=0,
                raw64_word_count=1,
            )


@pytest.mark.parametrize("step_alias", [False, 0.0, np.int64(0)])
def test_step_index_aliases_refuse_in_record_and_result(
    duplicate_result,
    step_alias,
):
    record = duplicate_result.occurrences[0]
    with pytest.raises((TypeError, ValueError)):
        _construct_occurrence(
            _occurrence_values(
                record,
                step_index=step_alias,
            )
        )
    with pytest.raises((TypeError, ValueError)):
        _construct_result(
            _result_values(
                duplicate_result,
                step_index=step_alias,
            )
        )


def test_post_reconstruct_record_flag_mutation_refuses(
    tight_bundle,
    single_state,
    monkeypatch,
):
    owner = tight_bundle["consumption_owner"]
    result = owner.consume(single_state, raw64_word_counts=(1,))
    record = result.occurrences[0]
    occurrence = single_state.occurrences[0]
    original = lineage.CounterKeyedLineageContractOwner.reconstruct_stream

    def mutate_after_reconstruct(self, stream):
        generator = original(self, stream)
        object.__setattr__(record, "same_runtime_only", False)
        return generator

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "reconstruct_stream",
        mutate_after_reconstruct,
    )
    try:
        with pytest.raises(ValueError):
            owner.validate_occurrence_consumption(
                record,
                occurrence,
                position=0,
                raw64_word_count=1,
            )
    finally:
        object.__setattr__(record, "same_runtime_only", True)


def test_post_reconstruct_result_flag_mutation_refuses(
    tight_bundle,
    single_state,
    monkeypatch,
):
    owner = tight_bundle["consumption_owner"]
    result = owner.consume(single_state, raw64_word_counts=(1,))
    original = lineage.CounterKeyedLineageContractOwner.reconstruct_stream

    def mutate_after_reconstruct(self, stream):
        generator = original(self, stream)
        object.__setattr__(result, "no_caller_rng", False)
        return generator

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "reconstruct_stream",
        mutate_after_reconstruct,
    )
    try:
        with pytest.raises(ValueError):
            owner.validate_result(
                result,
                single_state,
                raw64_word_counts=(1,),
            )
    finally:
        object.__setattr__(result, "no_caller_rng", True)


def test_result_replay_rejects_prior_record_equal_identity_substitution(
    tight_bundle,
    duplicate_state,
    duplicate_result,
    monkeypatch,
):
    owner = tight_bundle["consumption_owner"]
    first, second = duplicate_result.occurrences
    original_words = first.raw64_words
    equal_words = tuple(word for word in original_words)
    original_digest = first.record_sha256
    original = lineage.CounterKeyedLineageContractOwner.reconstruct_stream
    replayed_streams = []

    assert equal_words == original_words
    assert equal_words is not original_words

    def substitute_during_second_replay(self, stream):
        generator = original(self, stream)
        replayed_streams.append(stream)
        if stream is second.initializer_stream:
            object.__setattr__(first, "raw64_words", equal_words)
            assert consumption._validate_occurrence_record(first) is first
            assert first.record_sha256 == original_digest
        return generator

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "reconstruct_stream",
        substitute_during_second_replay,
    )
    try:
        with pytest.raises(
            ValueError,
            match=(
                "initializer result occurrence record 0 field "
                "raw64_words changed identity"
            ),
        ):
            owner.validate_result(
                duplicate_result,
                duplicate_state,
                raw64_word_counts=(1, 5),
            )
        assert replayed_streams == [
            first.initializer_stream,
            second.initializer_stream,
        ]
        assert first.raw64_words is equal_words
        assert consumption._validate_occurrence_record(first) is first
        assert consumption._validate_result_record(duplicate_result) is (
            duplicate_result
        )
    finally:
        object.__setattr__(first, "raw64_words", original_words)


def test_standalone_certificate_runtime_digest_forgery_refuses(tight_bundle):
    certificate = tight_bundle["consumption_owner"].certificate
    with pytest.raises(ValueError, match="runtime"):
        _construct_certificate(
            _certificate_values(
                certificate,
                consumption_runtime_sha256="0" * 64,
            )
        )


def test_redigested_raw_prefix_and_final_snapshot_forgeries_replay_refuse(
    tight_bundle,
    duplicate_state,
    duplicate_result,
):
    owner = tight_bundle["consumption_owner"]
    parent = duplicate_state.occurrences[0]
    record = duplicate_result.occurrences[0]

    forged_words = (record.raw64_words[0] ^ 1,)
    word_forgery = _construct_occurrence(
        _occurrence_values(record, raw64_words=forged_words)
    )
    assert word_forgery.record_sha256 != record.record_sha256
    with pytest.raises(ValueError, match="prefix did not replay"):
        owner.validate_occurrence_consumption(
            word_forgery,
            parent,
            position=0,
            raw64_word_count=1,
        )

    generator = owner.contract_owner.reconstruct_stream(record.initializer_stream)
    generator.bit_generator.random_raw(2)
    wrong_final = route_evidence._capture_philox_state(generator)
    final_forgery = _construct_occurrence(
        _occurrence_values(
            record,
            stream_final_state=wrong_final,
            stream_final_snapshot_sha256=wrong_final.snapshot_sha256,
            stream_final_state_sha256=wrong_final.state_sha256,
        )
    )
    assert final_forgery.no_upper_counter_carry is True
    with pytest.raises(ValueError, match="final snapshot did not replay"):
        owner.validate_occurrence_consumption(
            final_forgery,
            parent,
            position=0,
            raw64_word_count=1,
        )


@pytest.mark.parametrize(
    "invalid_word",
    [True, False, -1, 1 << 64, 1.0, np.uint64(1), np.int64(1)],
)
def test_raw_word_records_require_exact_canonical_uint64_integers(
    duplicate_result,
    invalid_word,
):
    record = duplicate_result.occurrences[0]
    with pytest.raises((TypeError, ValueError)):
        _construct_occurrence(
            _occurrence_values(
                record,
                raw64_words=(invalid_word,),
            )
        )


def test_redigested_equal_event_clone_refuses_exact_parent_identity(
    tight_bundle,
    duplicate_state,
    duplicate_result,
):
    owner = tight_bundle["consumption_owner"]
    parent = duplicate_state.occurrences[0]
    record = duplicate_result.occurrences[0]
    cloned_event = TransformedEvent(
        parent.event.event_type,
        parent.event.coordinates,
    )
    cloned_occurrence = lineage._make_occurrence(
        tight_bundle["contract_owner"].certificate,
        parent.identifier,
        cloned_event,
    )
    assert cloned_event == parent.event and cloned_event is not parent.event
    assert cloned_occurrence.occurrence_sha256 == parent.occurrence_sha256
    forged = _construct_occurrence(
        _occurrence_values(
            record,
            occurrence=cloned_occurrence,
            occurrence_sha256=cloned_occurrence.occurrence_sha256,
            identifier=cloned_occurrence.identifier,
            identifier_sha256=cloned_occurrence.identifier_sha256,
            event=cloned_event,
            event_model_key=cloned_event.model_key(),
        )
    )
    with pytest.raises(ValueError, match="another occurrence"):
        owner.validate_occurrence_consumption(
            forged,
            parent,
            position=0,
            raw64_word_count=1,
        )


def test_redigested_alien_parent_occurrence_certificate_refuses_before_stream(
    tight_bundle,
    duplicate_result,
):
    owner = tight_bundle["consumption_owner"]
    record = duplicate_result.occurrences[0]
    parent = record.occurrence
    alien_contract = checkpoint24_tests.checkpoint23_tests._certify_owner(
        tight_bundle,
        role="1" * 64,
    )
    alien_identifier = lineage._make_identifier(
        alien_contract.certificate,
        run_id=parent.identifier.run_id,
        serial=parent.identifier.serial,
        origin_kind="initial",
        origin_initialization_index=(parent.identifier.origin_initialization_index),
        origin_initial_position=parent.identifier.origin_initial_position,
    )
    alien_occurrence = lineage._make_occurrence(
        alien_contract.certificate,
        alien_identifier,
        parent.event,
    )
    values = _occurrence_values(
        record,
        occurrence=alien_occurrence,
        occurrence_sha256=alien_occurrence.occurrence_sha256,
        identifier=alien_identifier,
        identifier_sha256=alien_identifier.identifier_sha256,
        event=alien_occurrence.event,
        event_model_key=alien_occurrence.event_model_key,
    )
    redigested = _forged_record(record, **values)

    assert alien_occurrence.certificate_sha256 != (
        owner.contract_owner.certificate.certificate_sha256
    )
    assert redigested.record_sha256 == consumption._thinning._semantic_digest(
        consumption._occurrence_payload(values)
    )
    assert redigested.initializer_stream is record.initializer_stream
    assert redigested.initializer_stream.certificate is (
        owner.contract_owner.certificate
    )
    with pytest.raises(
        ValueError,
        match="occurrence record belongs to another lineage certificate",
    ):
        owner.validate_occurrence_consumption(
            redigested,
            alien_occurrence,
            position=0,
            raw64_word_count=1,
        )


def test_redigested_alien_parent_stream_refuses_exact_certificate_object(
    tight_bundle,
    duplicate_result,
):
    record = duplicate_result.occurrences[0]
    role = tight_bundle["contract_owner"].certificate.contract_role_sha256
    alien_contract = checkpoint24_tests.checkpoint23_tests._certify_owner(
        tight_bundle,
        role=role,
    )
    alien_stream = alien_contract.make_initializer_stream(
        record.run_id,
        record.step_index,
        record.occurrence_serial,
    )
    assert alien_stream.certificate is not record.initializer_stream.certificate
    assert alien_stream.certificate_sha256 == (
        record.initializer_stream.certificate_sha256
    )
    assert alien_stream.stream_sha256 == record.initializer_stream_sha256
    with pytest.raises(ValueError, match="certificate object"):
        _construct_occurrence(
            _occurrence_values(
                record,
                initializer_stream=alien_stream,
                initializer_stream_sha256=alien_stream.stream_sha256,
                initializer_address_sha256=alien_stream.address.address_sha256,
                stream_initial_state=alien_stream.initial_state,
                stream_initial_snapshot_sha256=(
                    alien_stream.initial_state.snapshot_sha256
                ),
                stream_initial_state_sha256=alien_stream.initial_state.state_sha256,
            )
        )


def test_consume_refuses_redigested_bootstrap_mutation_against_child_baseline(
    tight_bundle,
    single_state,
    monkeypatch,
):
    owner = tight_bundle["consumption_owner"]
    occurrence = single_state.occurrences[0]
    replacement = lineage._make_occurrence(
        owner.contract_owner.certificate,
        occurrence.identifier,
        TransformedEvent(1),
    )
    replacement_state = lineage._make_state(
        owner.contract_owner.certificate,
        run_id=single_state.run_id,
        initialization_index=single_state.initialization_index,
        occurrences=(replacement,),
        retired_identifiers=single_state.retired_identifiers,
        next_serial=single_state.next_serial,
    )
    occurrence_fields = lineage._occurrence_fields()
    state_fields = lineage._state_fields()
    occurrence_before = {name: getattr(occurrence, name) for name in occurrence_fields}
    state_before = {name: getattr(single_state, name) for name in state_fields}
    original = lineage.CounterKeyedLineageContractOwner.make_initializer_stream
    mutation_validated = []

    def mutate_to_redigested_bootstrap(
        self,
        run_id,
        step_index,
        occurrence_serial,
    ):
        stream = original(self, run_id, step_index, occurrence_serial)
        for name in occurrence_fields:
            object.__setattr__(occurrence, name, getattr(replacement, name))
        for name in state_fields:
            if name != "occurrences":
                object.__setattr__(
                    single_state,
                    name,
                    getattr(replacement_state, name),
                )
        lineage._validate_occurrence(occurrence)
        lineage._validate_state(single_state)
        owner._validate_bootstrap_state(single_state)
        mutation_validated.append(True)
        return stream

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_initializer_stream",
        mutate_to_redigested_bootstrap,
    )
    try:
        with pytest.raises(
            ValueError,
            match=(
                "consumed initial lineage state field " "occurrence_sha256s changed"
            ),
        ):
            owner.consume(
                single_state,
                raw64_word_counts=(1,),
            )
        assert mutation_validated == [True]
    finally:
        for name, value in occurrence_before.items():
            object.__setattr__(occurrence, name, value)
        for name, value in state_before.items():
            object.__setattr__(single_state, name, value)


def test_redigested_duplicate_record_reorder_and_state_clone_refuse(
    tight_bundle,
    duplicate_state,
    duplicate_result,
):
    first, second = duplicate_result.occurrences
    with pytest.raises(ValueError, match="position or identity"):
        _construct_result(
            _result_values(
                duplicate_result,
                occurrences=(second, first),
            )
        )

    cloned_state = lineage._make_state(
        tight_bundle["contract_owner"].certificate,
        run_id=duplicate_state.run_id,
        initialization_index=duplicate_state.initialization_index,
        occurrences=duplicate_state.occurrences,
        retired_identifiers=duplicate_state.retired_identifiers,
        next_serial=duplicate_state.next_serial,
    )
    forged = _construct_result(
        _result_values(
            duplicate_result,
            initial_state=cloned_state,
            final_state=cloned_state,
            initial_state_sha256=cloned_state.state_sha256,
            final_state_sha256=cloned_state.state_sha256,
        )
    )
    assert forged.initial_state is not duplicate_state
    assert forged.initial_state_sha256 == duplicate_result.initial_state_sha256
    with pytest.raises(ValueError, match="another state object"):
        tight_bundle["consumption_owner"].validate_result(
            forged,
            duplicate_state,
            raw64_word_counts=(1, 5),
        )


def test_forged_upper_counter_carry_refuses(tight_bundle, single_state):
    owner = tight_bundle["consumption_owner"]
    result = owner.consume(single_state, raw64_word_counts=(1,))
    record = result.occurrences[0]
    generator = owner.contract_owner.reconstruct_stream(record.initializer_stream)
    generator.bit_generator.advance(1 << 64)
    carried = route_evidence._capture_philox_state(generator)
    assert carried.counter[1:] != record.stream_initial_state.counter[1:]
    forged = _forged_record(
        record,
        stream_final_state=carried,
        stream_final_snapshot_sha256=carried.snapshot_sha256,
        stream_final_state_sha256=carried.state_sha256,
    )
    with pytest.raises((TypeError, ValueError)):
        owner.validate_occurrence_consumption(
            forged,
            single_state.occurrences[0],
            position=0,
            raw64_word_count=1,
        )


def test_result_omission_duplication_reorder_and_flag_attacks_refuse(
    tight_bundle,
    duplicate_state,
    duplicate_result,
):
    owner = tight_bundle["consumption_owner"]
    first, second = duplicate_result.occurrences
    attacks = (
        {"raw64_word_counts": (5, 1)},
        {"occurrences": ()},
        {"occurrences": (first, first)},
        {"occurrences": (second, first)},
        {"occurrence_sha256s": ()},
        {"occurrence_sha256s": (first.record_sha256, first.record_sha256)},
        {"total_raw64_words": 5},
        {"stream_count": 1},
        {"exact_initial_final_state_identity": False},
        {"initial_model_projection_unchanged": False},
        {"no_caller_rng": False},
        {"empty_state_zero_word": True},
        {"all_requested_streams_consumed": False},
        {"result_sha256": "0" * 64},
    )
    for updates in attacks:
        forged = _forged_record(duplicate_result, **updates)
        with pytest.raises((TypeError, ValueError)):
            owner.validate_result(
                forged,
                duplicate_state,
                raw64_word_counts=(1, 5),
            )


def test_records_owner_and_certificate_are_sealed(
    tight_bundle,
    duplicate_result,
):
    owner = tight_bundle["consumption_owner"]
    records = (
        owner,
        owner.certificate,
        duplicate_result.occurrences[0],
        duplicate_result,
    )
    for record in records:
        for operation in (pickle.dumps, copy.copy, copy.deepcopy):
            with pytest.raises(TypeError):
                operation(record)
    for record_type in (
        consumption.CounterKeyedInitializerStreamConsumptionCertificate,
        consumption.CounterKeyedInitializerOccurrenceConsumption,
        consumption.CounterKeyedInitializerStreamConsumptionResult,
        consumption.CounterKeyedInitializerStreamConsumptionOwner,
    ):
        with pytest.raises(TypeError, match="subclass"):
            type("ForbiddenSubclass", (record_type,), {})


def test_certificate_complete_truth_matrix(tight_bundle):
    certificate = tight_bundle["consumption_owner"].certificate
    positive = (
        "exact_checkpoint24_owner_binding_certified",
        "exact_checkpoint23_owner_binding_certified",
        "bootstrap_form_initial_state_gate_certified",
        "fixed_initializer_step_zero_certified",
        "exact_initializer_tag3_address_certified",
        "complete_live_occurrence_coverage_certified",
        "positive_raw64_prefix_per_nonempty_occurrence_certified",
        "exact_pre_post_snapshot_custody_certified",
        "same_runtime_prefix_replay_certified",
        "recorded_upper_counter_limb_preservation_certified",
        "bounded_work_preflight_certified",
        "no_caller_rng_certified",
        "unchanged_lineage_state_identity_certified",
        "occurrence_stream_consumption_certified",
        "initializer_stream_consumption_certified",
        "passed",
    )
    negative = (
        "event_or_configuration_generation_certified",
        "initializer_output_law_certified",
        "reference_initializer_law_certified",
        "conditional_or_tilted_initializer_law_certified",
        "enumeration_rejection_or_sir_certified",
        "exact_uniform_law_certified",
        "exact_categorical_law_certified",
        "exact_integer_law_certified",
        "exact_gaussian_law_certified",
        "analytic_output_law_certified",
        "statistical_independence_certified",
        "physical_randomness_certified",
        "global_run_id_uniqueness_certified",
        "duplicate_address_use_prevention_certified",
        "lineage_fork_prevention_certified",
        "brownian_stream_consumption_certified",
        "brownian_additive_coupling_certified",
        "continuous_drift_admissible",
        "initializer_admissible",
        "path_admissible",
        "strang_sampler_admissible",
        "full_sampler_admissible",
        "analytic_target_preserved",
        "rounded_stationarity_certified",
        "sampler_liveness_certified",
        "runtime_portable",
        "cryptographic_authentication",
    )
    assert all(getattr(certificate, name) is True for name in positive)
    assert all(getattr(certificate, name) is False for name in negative)
    accounted = {
        *positive,
        *negative,
        "schema_version",
        "certificate_scope",
        "consumption_policy",
        "consumption_role_sha256",
        "process_parameter_sha256",
        "checkpoint24_certificate",
        "checkpoint24_certificate_sha256",
        "checkpoint24_role_sha256",
        "checkpoint24_runtime_sha256",
        "checkpoint23_certificate",
        "checkpoint23_certificate_sha256",
        "checkpoint23_role_sha256",
        "checkpoint23_runtime_sha256",
        "consumption_runtime_sha256",
        "philox_snapshot_schema_version",
        "rng_bit_generator",
        "initializer_domain",
        "initializer_domain_tag",
        "initializer_step_index",
        "maximum_stream_records",
        "maximum_raw64_words_per_occurrence",
        "maximum_total_raw64_words",
        "certificate_sha256",
    }
    assert accounted == set(type(certificate).__annotations__)


def test_live_owner_binding_rejects_same_digest_parent_substitution(tight_bundle):
    parent = tight_bundle["epoch_owner"]
    local_owner = _certify_consumption(
        parent,
        consumption_policy=CONSUMPTION_POLICY,
        consumption_role_sha256="e" * 64,
    )
    alien_epoch = epoch.certify_plugin_bridge_counter_keyed_operational_epoch_loop(
        tight_bundle["contract_owner"],
        epoch_policy=epoch.PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY,
        epoch_role_sha256=parent.certificate.epoch_role_sha256,
    )
    assert alien_epoch is not parent
    assert alien_epoch.certificate.certificate_sha256 == (
        parent.certificate.certificate_sha256
    )
    object.__setattr__(local_owner, "_epoch_owner", alien_epoch)
    with pytest.raises(ValueError, match="epoch-owner binding"):
        local_owner.consume(
            _structural_bootstrap_state(
                tight_bundle,
                count=0,
                run_id=2514,
            ),
            raw64_word_counts=(),
        )


def test_public_surface_static_rng_boundary_and_nonclaims(tight_bundle):
    expected = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCOPE",
        "COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_STEP_INDEX",
        "COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_STREAM_RECORDS",
        "COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_"
        "MAX_RAW64_WORDS_PER_OCCURRENCE",
        "COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_MAX_TOTAL_RAW64_WORDS",
        "CounterKeyedInitializerStreamConsumptionCertificate",
        "CounterKeyedInitializerOccurrenceConsumption",
        "CounterKeyedInitializerStreamConsumptionResult",
        "CounterKeyedInitializerStreamConsumptionOwner",
        "PluginBridgeCounterKeyedInitializerStreamConsumptionError",
        "certify_plugin_bridge_counter_keyed_" "initializer_stream_consumption",
        "require_matching_plugin_bridge_counter_keyed_"
        "initializer_stream_consumption",
        "validate_plugin_bridge_counter_keyed_"
        "initializer_stream_consumption_certificate",
    }
    assert set(consumption.__all__) == expected
    source = inspect.getsource(consumption)
    tree = ast.parse(source)
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "hash" not in called_names
    assert "default_rng" not in source
    assert ".choice(" not in source
    assert ".integers(" not in source
    assert ".normal(" not in source
    assert "make_jump_proposal_stream" not in source
    assert "make_brownian_left_stream" not in source
    assert "make_brownian_right_stream" not in source
    scope = consumption.PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_STREAM_CONSUMPTION_SCOPE
    for phrase in (
        "not-initializer",
        "not-statistical-independence",
        "not-brownian",
        "not-drift",
        "not-path",
        "not-full-sampler",
        "not-runtime-portable",
        "not-cryptographic",
    ):
        assert phrase in scope
    certificate = tight_bundle["consumption_owner"].certificate
    assert certificate.initializer_admissible is False
    assert certificate.path_admissible is False
    assert certificate.strang_sampler_admissible is False
    assert certificate.full_sampler_admissible is False
    assert certificate.statistical_independence_certified is False
    assert certificate.runtime_portable is False
    assert certificate.cryptographic_authentication is False


def test_factory_require_validator_and_exact_parent_binding(tight_bundle):
    owner = tight_bundle["consumption_owner"]
    parent = tight_bundle["epoch_owner"]
    policy = CONSUMPTION_POLICY
    assert (
        _require_consumption(
            parent,
            owner,
            consumption_policy=policy,
            consumption_role_sha256=CONSUMPTION_ROLE,
        )
        is owner
    )
    assert (
        _validate_consumption_certificate(
            parent,
            owner,
            consumption_policy=policy,
            consumption_role_sha256=CONSUMPTION_ROLE,
        )
        is owner.certificate
    )
    for updates in (
        {"consumption_policy": "unsupported"},
        {"consumption_role_sha256": "d" * 64},
    ):
        arguments = {
            "consumption_policy": policy,
            "consumption_role_sha256": CONSUMPTION_ROLE,
        }
        arguments.update(updates)
        with pytest.raises((TypeError, ValueError)):
            _require_consumption(
                parent,
                owner,
                **arguments,
            )


def test_optional_torch_import_boundary_is_explicit():
    module_path = Path(consumption.__file__).resolve()
    source_root = module_path.parents[3]
    script = """
import builtins

real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == 'torch' or name.startswith('torch.'):
        raise ModuleNotFoundError("No module named 'torch'", name='torch')
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
try:
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_initializer_stream_consumption,
    )
except ModuleNotFoundError as error:
    text = str(error)
    assert "initializer-stream" in text
    assert "optional PyTorch" in text
else:
    raise AssertionError("optional PyTorch boundary did not refuse")
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=source_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
