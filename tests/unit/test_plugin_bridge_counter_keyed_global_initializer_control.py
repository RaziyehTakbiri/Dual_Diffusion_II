"""Hostile tests for checkpoint-26 global initializer-control custody."""

import ast
import copy
import importlib
import inspect
from pathlib import Path
import pickle
import subprocess
import sys

import numpy as np
import pytest


pytest.importorskip(
    "torch", reason="global initializer control requires the PyTorch stack"
)

checkpoint25_tests = importlib.import_module(
    "test_plugin_bridge_counter_keyed_initializer_stream_consumption"
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_continuous_route_evidence as route_evidence,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_global_initializer_control as control,
)


CONTROL_ROLE = "7" * 64
CONTROL_POLICY = control.PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_POLICY
MAX_STREAMS = control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
MAX_WORDS = control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM
MAX_TOTAL_WORDS = control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_TOTAL_RAW64_WORDS
CONTROL_PLAN = ((0, 0, 1), (0, 3, 5), (4, 0, 3))
_require_control = (
    control.require_matching_plugin_bridge_counter_keyed_global_initializer_control
)
_validate_control_certificate = (
    control.validate_plugin_bridge_counter_keyed_global_initializer_control_certificate
)


def _certify_control(parent, *, role=CONTROL_ROLE):
    return control.certify_plugin_bridge_counter_keyed_global_initializer_control(
        parent,
        control_policy=CONTROL_POLICY,
        control_role_sha256=role,
    )


@pytest.fixture(scope="module")
def certified_bundle():
    bundle = checkpoint25_tests._certified_bundle(total_cap=2)
    bundle["control_owner"] = _certify_control(bundle["consumption_owner"])
    return bundle


@pytest.fixture(scope="module")
def control_result(certified_bundle):
    return certified_bundle["control_owner"].consume(
        2600,
        9,
        control_plan=CONTROL_PLAN,
    )


@pytest.fixture(scope="module")
def same_digest_alien_owner(certified_bundle):
    return _certify_control(certified_bundle["consumption_owner"])


@pytest.fixture(scope="module")
def same_digest_alien_result(same_digest_alien_owner):
    return same_digest_alien_owner.consume(2600, 9, control_plan=CONTROL_PLAN)


def _direct_prefix(
    *,
    run_id,
    initialization_index,
    stage_index,
    attempt_index,
    word_count,
):
    generator = np.random.Generator(
        np.random.Philox(
            key=np.asarray(
                (
                    run_id,
                    control.COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL,
                ),
                dtype=np.uint64,
            ),
            counter=np.asarray(
                (0, initialization_index, stage_index, attempt_index),
                dtype=np.uint64,
            ),
        )
    )
    words = tuple(
        int(value)
        for value in np.atleast_1d(generator.bit_generator.random_raw(word_count))
    )
    return words, route_evidence._capture_philox_state(generator)


def _forged(value, **updates):
    forged = object.__new__(type(value))
    for name in type(value).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(value, name)))
    return forged


def _address_values(address, **updates):
    values = {
        name: updates.get(name, getattr(address, name))
        for name in control._address_fields()
    }
    values["address_sha256"] = "0" * 64
    values["address_sha256"] = control._thinning._semantic_digest(
        control._without(values, "address_sha256")
    )
    return values


def _stream_values(stream, **updates):
    values = {
        name: updates.get(name, getattr(stream, name))
        for name in control._stream_fields()
    }
    values["stream_sha256"] = "0" * 64
    values["stream_sha256"] = control._thinning._semantic_digest(
        control._without(
            values,
            "certificate",
            "address",
            "initial_state",
            "stream_sha256",
        )
    )
    return values


def _record_values(record, **updates):
    values = {
        name: updates.get(name, getattr(record, name))
        for name in control._record_fields()
    }
    values["record_sha256"] = "0" * 64
    values["record_sha256"] = control._thinning._semantic_digest(
        control._record_payload(values)
    )
    return values


def _result_values(result, **updates):
    values = {
        name: updates.get(name, getattr(result, name))
        for name in control._result_fields()
    }
    if "consumptions" in updates and "consumption_sha256s" not in updates:
        values["consumption_sha256s"] = tuple(
            record.record_sha256 for record in values["consumptions"]
        )
    values["result_sha256"] = "0" * 64
    values["result_sha256"] = control._thinning._semantic_digest(
        control._result_payload(values)
    )
    return values


def _certificate_values(certificate, **updates):
    values = {
        name: updates.get(name, getattr(certificate, name))
        for name in control._certificate_fields()
    }
    values["certificate_sha256"] = "0" * 64
    values["certificate_sha256"] = control._thinning._semantic_digest(
        control._certificate_payload(values)
    )
    return values


def _construct_address(values):
    return control.CounterKeyedGlobalInitializerControlAddress(
        **values,
        _construction_token=control._ADDRESS_TOKEN,
    )


def _construct_stream(values):
    return control.CounterKeyedGlobalInitializerControlStream(
        **values,
        _construction_token=control._STREAM_TOKEN,
    )


def _construct_record(values):
    return control.CounterKeyedGlobalInitializerControlConsumption(
        **values,
        _construction_token=control._RECORD_TOKEN,
    )


def _construct_result(values):
    return control.CounterKeyedGlobalInitializerControlResult(
        **values,
        _construction_token=control._RESULT_TOKEN,
    )


def _construct_certificate(values):
    return control.CounterKeyedGlobalInitializerControlCertificate(
        **values,
        _construction_token=control._CERTIFICATE_TOKEN,
    )


def test_certificate_binds_exact_checkpoint25_checkpoint24_checkpoint23_owners(
    certified_bundle,
):
    owner = certified_bundle["control_owner"]
    certificate = owner.certificate
    parent25 = certified_bundle["consumption_owner"]
    assert owner.consumption_owner is parent25
    assert owner.epoch_owner is certified_bundle["epoch_owner"]
    assert owner.contract_owner is certified_bundle["contract_owner"]
    assert certificate.checkpoint25_certificate is parent25.certificate
    assert certificate.checkpoint24_certificate_sha256 == (
        certified_bundle["epoch_owner"].certificate.certificate_sha256
    )
    assert certificate.checkpoint23_certificate_sha256 == (
        certified_bundle["contract_owner"].certificate.certificate_sha256
    )
    assert certificate.global_control_domain_tag == 7
    assert certificate.address_layout == (
        "key=(run_id,7);counter=(0,initialization_index,stage_index,attempt_index)"
    )


def test_exact_direct_tag7_prefixes_and_identity_custody(
    certified_bundle,
    control_result,
):
    assert control_result.run_id == 2600
    assert control_result.initialization_index == 9
    assert control_result.control_plan is CONTROL_PLAN
    assert control_result.stream_count == 3
    assert control_result.total_raw64_words == 9
    assert control_result.empty_plan_zero_word is False
    assert control_result.canonical_control_plan is True
    assert control_result.within_plan_unique_addresses is True
    assert control_result.all_requested_streams_consumed is True
    assert control_result.no_caller_rng is True
    assert control_result.same_runtime_only is True

    for position, (entry, record) in enumerate(
        zip(CONTROL_PLAN, control_result.consumptions)
    ):
        stage, attempt, count = entry
        expected_words, expected_final = _direct_prefix(
            run_id=2600,
            initialization_index=9,
            stage_index=stage,
            attempt_index=attempt,
            word_count=count,
        )
        address = record.control_stream.address
        assert record.position == position
        assert record.certificate is control_result.certificate
        assert record.run_id == 2600
        assert record.initialization_index == 9
        assert record.stage_index == stage
        assert record.attempt_index == attempt
        assert record.raw64_word_count == count
        assert address.domain == control.COUNTER_KEY_DOMAIN_GLOBAL_INITIALIZER_CONTROL
        assert address.domain_tag == 7
        assert address.philox_key == (2600, 7)
        assert address.philox_counter == (0, 9, stage, attempt)
        assert record.stream_initial_state is record.control_stream.initial_state
        assert record.raw64_words == expected_words
        assert record.stream_final_state.snapshot_sha256 == (
            expected_final.snapshot_sha256
        )
        assert record.stream_final_state.counter[1:] == (
            record.stream_initial_state.counter[1:]
        )
        assert record.parent_execution_used_this_stream is False
        assert record.successor_execution_invoked_this_stream is True
        assert record.successor_execution_consumed_this_stream is True
        assert record.no_upper_counter_carry is True
        assert record.same_runtime_only is True

    assert (
        certified_bundle["control_owner"].validate_result(
            control_result,
            2600,
            9,
            control_plan=CONTROL_PLAN,
        )
        is control_result
    )


def test_empty_plan_is_zero_word_and_never_constructs_a_stream(
    certified_bundle,
    monkeypatch,
):
    owner = certified_bundle["control_owner"]

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("empty plan reached a stream factory")

    monkeypatch.setattr(
        control.CounterKeyedGlobalInitializerControlOwner,
        "_make_control_stream",
        forbidden,
    )
    result = owner.consume(2601, 0, control_plan=())
    assert result.control_plan == ()
    assert result.consumptions == ()
    assert result.consumption_sha256s == ()
    assert result.total_raw64_words == 0
    assert result.stream_count == 0
    assert result.empty_plan_zero_word is True
    assert owner.validate_result(result, 2601, 0, control_plan=()) is result


@pytest.mark.parametrize(
    "invalid_plan",
    [[], np.asarray(((0, 0, 1),), dtype=np.int64), iter(((0, 0, 1),))],
)
def test_control_plan_requires_an_exact_tuple(
    certified_bundle,
    invalid_plan,
):
    with pytest.raises(TypeError, match="exact tuple"):
        certified_bundle["control_owner"].consume(
            2602,
            0,
            control_plan=invalid_plan,
        )


def test_each_plan_entry_requires_an_exact_three_tuple(certified_bundle):
    owner = certified_bundle["control_owner"]
    invalid_plans = (
        ([0, 0, 1],),
        ((0, 0),),
        ((0, 0, 1, 2),),
        ((0, 0, 1), [1, 0, 1]),
    )
    for plan in invalid_plans:
        with pytest.raises((TypeError, ValueError)):
            owner.consume(2603, 0, control_plan=plan)


def test_coordinates_and_counts_require_exact_canonical_python_integers(
    certified_bundle,
    monkeypatch,
):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("invalid plan issued a stream")

    monkeypatch.setattr(
        control.CounterKeyedGlobalInitializerControlOwner,
        "_make_control_stream",
        forbidden,
    )
    aliases = (True, False, -1, 1 << 64, 1.0, np.int64(1), np.uint64(1))
    for invalid in aliases:
        for plan in (
            ((invalid, 0, 1),),
            ((0, invalid, 1),),
            ((0, 0, invalid),),
        ):
            with pytest.raises((TypeError, ValueError)):
                certified_bundle["control_owner"].consume(
                    2604,
                    0,
                    control_plan=plan,
                )
    assert calls == []


def test_plan_addresses_must_be_strictly_lexicographically_increasing(
    certified_bundle,
):
    owner = certified_bundle["control_owner"]
    invalid_plans = (
        ((0, 0, 1), (0, 0, 2)),
        ((0, 2, 1), (0, 1, 1)),
        ((1, 0, 1), (0, 99, 1)),
        ((1, 1, 1), (1, 0, 1)),
    )
    for plan in invalid_plans:
        with pytest.raises(ValueError, match="strictly lexicographically"):
            owner.consume(2605, 0, control_plan=plan)


def test_late_invalid_entry_refuses_before_any_stream_is_constructed(
    certified_bundle,
    monkeypatch,
):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("incomplete preflight issued a stream")

    monkeypatch.setattr(
        control.CounterKeyedGlobalInitializerControlOwner,
        "_make_control_stream",
        forbidden,
    )
    with pytest.raises(ValueError, match="positive"):
        certified_bundle["control_owner"].consume(
            2606,
            0,
            control_plan=((0, 0, 1), (1, 0, 0)),
        )
    assert calls == []


def test_oversized_plan_refuses_before_entry_traversal_or_stream_construction(
    certified_bundle,
    monkeypatch,
):
    inclusive_maximum = tuple((index, 0, 1) for index in range(MAX_STREAMS))
    checked, total = control._preflight_control_plan(inclusive_maximum)
    assert checked is inclusive_maximum
    assert total == MAX_STREAMS

    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("oversized plan was traversed")

    monkeypatch.setattr(control, "_exact_positive_word_count", forbidden)
    monkeypatch.setattr(
        control.CounterKeyedGlobalInitializerControlOwner,
        "_make_control_stream",
        forbidden,
    )
    oversized = tuple((index, 0, 1) for index in range(MAX_STREAMS + 1))
    with pytest.raises(ValueError, match="stream-record bound"):
        certified_bundle["control_owner"].consume(
            2607,
            0,
            control_plan=oversized,
        )
    assert calls == []


def test_per_stream_word_cap_refuses_before_stream_construction(
    certified_bundle,
    monkeypatch,
):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("over-cap request issued a stream")

    monkeypatch.setattr(
        control.CounterKeyedGlobalInitializerControlOwner,
        "_make_control_stream",
        forbidden,
    )
    with pytest.raises(ValueError, match="maximum bound"):
        certified_bundle["control_owner"].consume(
            2608,
            0,
            control_plan=((0, 0, MAX_WORDS + 1),),
        )
    assert calls == []


def test_aggregate_word_cap_refuses_complete_plan_before_construction(
    certified_bundle,
    monkeypatch,
):
    exact_cap_plan = tuple(
        (index, 0, MAX_WORDS) for index in range(MAX_TOTAL_WORDS // MAX_WORDS)
    )
    checked, total = control._preflight_control_plan(exact_cap_plan)
    assert checked is exact_cap_plan
    assert total == MAX_TOTAL_WORDS

    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("aggregate-over-cap plan issued a stream")

    monkeypatch.setattr(
        control.CounterKeyedGlobalInitializerControlOwner,
        "_make_control_stream",
        forbidden,
    )
    stream_count = MAX_TOTAL_WORDS // MAX_WORDS + 1
    plan = tuple((index, 0, MAX_WORDS) for index in range(stream_count))
    assert len(plan) <= MAX_STREAMS
    assert sum(entry[2] for entry in plan) > MAX_TOTAL_WORDS
    with pytest.raises(ValueError, match="aggregate raw64 bound"):
        certified_bundle["control_owner"].consume(
            2609,
            0,
            control_plan=plan,
        )
    assert calls == []


def test_run_and_initialization_coordinates_require_exact_uint64(
    certified_bundle,
):
    owner = certified_bundle["control_owner"]
    invalid = (True, False, -1, 1 << 64, 1.0, np.int64(1), np.uint64(1))
    for value in invalid:
        with pytest.raises((TypeError, ValueError)):
            owner.consume(value, 0, control_plan=())
        with pytest.raises((TypeError, ValueError)):
            owner.consume(1, value, control_plan=())

    maximum = (1 << 64) - 1
    result = owner.consume(
        maximum,
        maximum,
        control_plan=((maximum, maximum, 1),),
    )
    record = result.consumptions[0]
    expected_words, expected_final = _direct_prefix(
        run_id=maximum,
        initialization_index=maximum,
        stage_index=maximum,
        attempt_index=maximum,
        word_count=1,
    )
    assert record.control_stream.address.philox_key == (maximum, 7)
    assert record.control_stream.address.philox_counter == (
        0,
        maximum,
        maximum,
        maximum,
    )
    assert record.raw64_words == expected_words
    assert record.stream_final_state.snapshot_sha256 == (expected_final.snapshot_sha256)
    assert (
        owner.validate_result(
            result,
            maximum,
            maximum,
            control_plan=result.control_plan,
        )
        is result
    )


def test_advertised_maximum_prefix_replays_without_upper_counter_carry(
    certified_bundle,
):
    owner = certified_bundle["control_owner"]
    result = owner.consume(2610, 11, control_plan=((6, 2, MAX_WORDS),))
    record = result.consumptions[0]
    expected_words, expected_final = _direct_prefix(
        run_id=2610,
        initialization_index=11,
        stage_index=6,
        attempt_index=2,
        word_count=MAX_WORDS,
    )
    assert record.raw64_words == expected_words
    assert record.stream_final_state.snapshot_sha256 == (expected_final.snapshot_sha256)
    assert record.stream_final_state.counter[1:] == (
        record.stream_initial_state.counter[1:]
    )


def test_reissue_replays_and_longer_request_extends_the_same_prefix(
    certified_bundle,
):
    owner = certified_bundle["control_owner"]
    short = owner.consume(2611, 2, control_plan=((5, 8, 3),))
    replay = owner.consume(2611, 2, control_plan=((5, 8, 3),))
    longer = owner.consume(2611, 2, control_plan=((5, 8, 9),))
    short_record = short.consumptions[0]
    replay_record = replay.consumptions[0]
    longer_record = longer.consumptions[0]
    assert short is not replay
    assert short.result_sha256 == replay.result_sha256
    assert short_record is not replay_record
    assert short_record.record_sha256 == replay_record.record_sha256
    assert short_record.raw64_words == replay_record.raw64_words
    assert longer_record.raw64_words[:3] == short_record.raw64_words
    assert longer_record.record_sha256 != short_record.record_sha256
    assert longer.result_sha256 != short.result_sha256


def test_each_address_coordinate_is_custodied_and_collision_disjoint(
    certified_bundle,
):
    owner = certified_bundle["control_owner"]
    requests = (
        (2612, 0, 0, 0),
        (2613, 0, 0, 0),
        (2612, 1, 0, 0),
        (2612, 0, 1, 0),
        (2612, 0, 0, 1),
    )
    records = tuple(
        owner.consume(
            run, initialization, control_plan=((stage, attempt, 2),)
        ).consumptions[0]
        for run, initialization, stage, attempt in requests
    )
    addresses = tuple(record.control_stream.address for record in records)
    assert len({(item.philox_key, item.philox_counter) for item in addresses}) == 5
    assert len({item.address_sha256 for item in addresses}) == 5
    assert all(item.philox_counter[0] == 0 for item in addresses)
    assert tuple(tag for _, tag in owner.certificate.reserved_parent_domain_tags) == (
        1,
        2,
        3,
        4,
        5,
        6,
    )
    assert all(item.domain_tag == 7 for item in addresses)


def test_validate_and_reconstruct_control_stream_are_exact_and_fresh(
    certified_bundle,
    control_result,
):
    owner = certified_bundle["control_owner"]
    stream = control_result.consumptions[1].control_stream
    assert (
        owner.validate_control_stream(
            stream,
            run_id=2600,
            initialization_index=9,
            stage_index=0,
            attempt_index=3,
        )
        is stream
    )
    first = owner.reconstruct_control_stream(
        stream,
        run_id=2600,
        initialization_index=9,
        stage_index=0,
        attempt_index=3,
    )
    second = owner.reconstruct_control_stream(
        stream,
        run_id=2600,
        initialization_index=9,
        stage_index=0,
        attempt_index=3,
    )
    assert first is not second
    assert route_evidence._capture_philox_state(first).snapshot_sha256 == (
        stream.initial_state.snapshot_sha256
    )
    assert route_evidence._capture_philox_state(second).snapshot_sha256 == (
        stream.initial_state.snapshot_sha256
    )


def test_validate_control_stream_refuses_wrong_coordinates(
    certified_bundle,
    control_result,
):
    owner = certified_bundle["control_owner"]
    stream = control_result.consumptions[0].control_stream
    baseline = {
        "run_id": 2600,
        "initialization_index": 9,
        "stage_index": 0,
        "attempt_index": 0,
    }
    for name, value in (
        ("run_id", 2601),
        ("initialization_index", 10),
        ("stage_index", 1),
        ("attempt_index", 1),
    ):
        arguments = dict(baseline)
        arguments[name] = value
        with pytest.raises(ValueError, match="coordinates"):
            owner.validate_control_stream(stream, **arguments)


def test_validate_stream_consumption_refuses_wrong_external_coordinates(
    certified_bundle,
    control_result,
):
    owner = certified_bundle["control_owner"]
    record = control_result.consumptions[0]
    attacks = (
        {"position": 1},
        {"plan_entry": (0, 0, 2)},
        {"plan_entry": (0, 1, 1)},
        {"run_id": 2601},
        {"initialization_index": 10},
    )
    for updates in attacks:
        arguments = {
            "position": 0,
            "plan_entry": (0, 0, 1),
            "run_id": 2600,
            "initialization_index": 9,
        }
        arguments.update(updates)
        with pytest.raises((TypeError, ValueError)):
            owner.validate_stream_consumption(record, **arguments)


def test_validate_result_refuses_wrong_external_request(
    certified_bundle,
    control_result,
):
    owner = certified_bundle["control_owner"]
    attacks = (
        (2601, 9, CONTROL_PLAN),
        (2600, 10, CONTROL_PLAN),
        (2600, 9, ((0, 0, 1),)),
        (2600, 9, ((0, 0, 2), (0, 3, 5), (4, 0, 3))),
    )
    for run_id, initialization_index, plan in attacks:
        with pytest.raises((TypeError, ValueError)):
            owner.validate_result(
                control_result,
                run_id,
                initialization_index,
                control_plan=plan,
            )


def test_stale_record_mutations_fail_closed(
    certified_bundle,
    control_result,
):
    owner = certified_bundle["control_owner"]
    record = control_result.consumptions[0]
    other = control_result.consumptions[1]
    attacks = (
        {"position": 1},
        {"run_id": 2601},
        {"initialization_index": 10},
        {"stage_index": 1},
        {"attempt_index": 1},
        {"raw64_word_count": 2},
        {"raw64_words": (record.raw64_words[0] ^ 1,)},
        {"control_stream": other.control_stream},
        {"stream_final_state": other.stream_final_state},
        {"parent_execution_used_this_stream": True},
        {"successor_execution_invoked_this_stream": False},
        {"successor_execution_consumed_this_stream": False},
        {"no_upper_counter_carry": False},
        {"same_runtime_only": False},
        {"record_sha256": "0" * 64},
    )
    for updates in attacks:
        forged = _forged(record, **updates)
        with pytest.raises((TypeError, ValueError)):
            owner.validate_stream_consumption(
                forged,
                position=0,
                plan_entry=(0, 0, 1),
                run_id=2600,
                initialization_index=9,
            )


def test_redigested_raw_prefix_forgery_fails_replay(
    certified_bundle,
    control_result,
):
    owner = certified_bundle["control_owner"]
    record = control_result.consumptions[0]
    forged = _construct_record(
        _record_values(
            record,
            raw64_words=(record.raw64_words[0] ^ 1,),
        )
    )
    assert forged.record_sha256 != record.record_sha256
    with pytest.raises(ValueError, match="prefix did not replay"):
        owner.validate_stream_consumption(
            forged,
            position=0,
            plan_entry=(0, 0, 1),
            run_id=2600,
            initialization_index=9,
        )


def test_redigested_final_snapshot_forgery_fails_replay(
    certified_bundle,
    control_result,
):
    owner = certified_bundle["control_owner"]
    record = control_result.consumptions[0]
    generator = owner.reconstruct_control_stream(
        record.control_stream,
        run_id=2600,
        initialization_index=9,
        stage_index=0,
        attempt_index=0,
    )
    generator.bit_generator.random_raw(2)
    wrong_final = route_evidence._capture_philox_state(generator)
    forged = _construct_record(
        _record_values(
            record,
            stream_final_state=wrong_final,
            stream_final_snapshot_sha256=wrong_final.snapshot_sha256,
            stream_final_state_sha256=wrong_final.state_sha256,
        )
    )
    with pytest.raises(ValueError, match="final snapshot did not replay"):
        owner.validate_stream_consumption(
            forged,
            position=0,
            plan_entry=(0, 0, 1),
            run_id=2600,
            initialization_index=9,
        )


def test_forged_upper_counter_carry_fails_closed(
    certified_bundle,
    control_result,
):
    owner = certified_bundle["control_owner"]
    record = control_result.consumptions[0]
    generator = owner.reconstruct_control_stream(
        record.control_stream,
        run_id=2600,
        initialization_index=9,
        stage_index=0,
        attempt_index=0,
    )
    generator.bit_generator.advance(1 << 64)
    carried = route_evidence._capture_philox_state(generator)
    assert carried.counter[1:] != record.stream_initial_state.counter[1:]
    forged = _forged(
        record,
        stream_final_state=carried,
        stream_final_snapshot_sha256=carried.snapshot_sha256,
        stream_final_state_sha256=carried.state_sha256,
    )
    with pytest.raises((TypeError, ValueError)):
        owner.validate_stream_consumption(
            forged,
            position=0,
            plan_entry=(0, 0, 1),
            run_id=2600,
            initialization_index=9,
        )


def test_address_constructor_rejects_redigested_key_counter_and_tag_forgeries(
    control_result,
):
    address = control_result.consumptions[0].control_stream.address
    attacks = (
        {"domain": "initializer"},
        {"domain_tag": 3},
        {"run_id": 2601},
        {"initialization_index": 10},
        {"stage_index": 1},
        {"attempt_index": 1},
        {"philox_key": (2600, 3)},
        {"philox_counter": (0, 9, 0, 1)},
    )
    for updates in attacks:
        with pytest.raises((TypeError, ValueError)):
            _construct_address(_address_values(address, **updates))


def test_stream_constructor_rejects_redigested_nested_address_substitution(
    control_result,
):
    first = control_result.consumptions[0].control_stream
    other = control_result.consumptions[1].control_stream
    with pytest.raises((TypeError, ValueError)):
        _construct_stream(
            _stream_values(
                first,
                address=other.address,
                address_sha256=other.address_sha256,
            )
        )


def test_record_rejects_same_digest_alien_stream_certificate_object(
    control_result,
    same_digest_alien_result,
):
    record = control_result.consumptions[0]
    alien = same_digest_alien_result.consumptions[0].control_stream
    assert alien.certificate is not record.control_stream.certificate
    assert alien.certificate_sha256 == record.control_stream.certificate_sha256
    assert alien.address_sha256 == record.control_stream.address_sha256
    assert alien.stream_sha256 == record.control_stream.stream_sha256
    with pytest.raises(ValueError, match="another certificate object"):
        _construct_record(
            _record_values(
                record,
                control_stream=alien,
                control_stream_sha256=alien.stream_sha256,
                control_address_sha256=alien.address.address_sha256,
                stream_initial_state=alien.initial_state,
                stream_initial_snapshot_sha256=alien.initial_state.snapshot_sha256,
                stream_initial_state_sha256=alien.initial_state.state_sha256,
            )
        )


def test_same_digest_alien_owner_result_refuses_exact_certificate_identity(
    certified_bundle,
    control_result,
    same_digest_alien_owner,
    same_digest_alien_result,
):
    owner = certified_bundle["control_owner"]
    assert same_digest_alien_owner is not owner
    assert same_digest_alien_owner.certificate is not owner.certificate
    assert same_digest_alien_owner.certificate.certificate_sha256 == (
        owner.certificate.certificate_sha256
    )
    assert same_digest_alien_result.result_sha256 == control_result.result_sha256
    with pytest.raises(ValueError, match="another owner"):
        owner.validate_result(
            same_digest_alien_result,
            2600,
            9,
            control_plan=CONTROL_PLAN,
        )


def test_result_stale_omission_duplication_reorder_and_flag_attacks_fail_closed(
    certified_bundle,
    control_result,
):
    owner = certified_bundle["control_owner"]
    first, second, third = control_result.consumptions
    attacks = (
        {"control_plan": ((0, 0, 1),)},
        {"consumptions": ()},
        {"consumptions": (first, first, third)},
        {"consumptions": (second, first, third)},
        {"consumption_sha256s": ()},
        {"total_raw64_words": 8},
        {"stream_count": 2},
        {"empty_plan_zero_word": True},
        {"canonical_control_plan": False},
        {"within_plan_unique_addresses": False},
        {"all_requested_streams_consumed": False},
        {"no_caller_rng": False},
        {"same_runtime_only": False},
        {"result_sha256": "0" * 64},
    )
    for updates in attacks:
        forged = _forged(control_result, **updates)
        with pytest.raises((TypeError, ValueError)):
            owner.validate_result(
                forged,
                2600,
                9,
                control_plan=CONTROL_PLAN,
            )


def test_redigested_result_reorder_and_plan_substitution_fail_closed(
    control_result,
):
    first, second, third = control_result.consumptions
    with pytest.raises(ValueError, match="position|plan"):
        _construct_result(
            _result_values(
                control_result,
                consumptions=(second, first, third),
            )
        )
    with pytest.raises(ValueError, match="record differs from its plan"):
        _construct_result(
            _result_values(
                control_result,
                control_plan=((0, 0, 1), (0, 3, 5), (5, 0, 3)),
            )
        )


def test_post_reconstruct_record_and_direct_stream_mutations_are_detected(
    certified_bundle,
    monkeypatch,
):
    owner = certified_bundle["control_owner"]
    result = owner.consume(2613, 0, control_plan=((0, 0, 1),))
    record = result.consumptions[0]
    original = route_evidence._generator_from_snapshot

    def mutate_after_reconstruct(snapshot):
        generator = original(snapshot)
        object.__setattr__(record, "same_runtime_only", False)
        return generator

    monkeypatch.setattr(
        route_evidence, "_generator_from_snapshot", mutate_after_reconstruct
    )
    try:
        with pytest.raises(ValueError):
            owner.validate_stream_consumption(
                record,
                position=0,
                plan_entry=(0, 0, 1),
                run_id=2613,
                initialization_index=0,
            )
    finally:
        object.__setattr__(record, "same_runtime_only", True)

    monkeypatch.setattr(route_evidence, "_generator_from_snapshot", original)
    stream = record.control_stream
    original_address = stream.address
    equal_address = _construct_address(_address_values(original_address))
    reconstruction_calls = []

    assert equal_address is not original_address
    assert equal_address.address_sha256 == original_address.address_sha256

    def mutate_after_direct_validation(snapshot):
        generator = original(snapshot)
        reconstruction_calls.append(snapshot)
        if len(reconstruction_calls) == 2:
            object.__setattr__(stream, "address", equal_address)
        return generator

    monkeypatch.setattr(
        route_evidence,
        "_generator_from_snapshot",
        mutate_after_direct_validation,
    )
    try:
        with pytest.raises(ValueError, match="address"):
            owner.reconstruct_control_stream(
                stream,
                run_id=2613,
                initialization_index=0,
                stage_index=0,
                attempt_index=0,
            )
        assert len(reconstruction_calls) == 2
    finally:
        object.__setattr__(stream, "address", original_address)


def test_post_reconstruct_result_mutation_is_detected(
    certified_bundle,
    monkeypatch,
):
    owner = certified_bundle["control_owner"]
    result = owner.consume(2614, 0, control_plan=((0, 0, 1),))
    original = route_evidence._generator_from_snapshot

    def mutate_after_reconstruct(snapshot):
        generator = original(snapshot)
        object.__setattr__(result, "no_caller_rng", False)
        return generator

    monkeypatch.setattr(
        route_evidence, "_generator_from_snapshot", mutate_after_reconstruct
    )
    try:
        with pytest.raises(ValueError):
            owner.validate_result(
                result,
                2614,
                0,
                control_plan=((0, 0, 1),),
            )
    finally:
        object.__setattr__(result, "no_caller_rng", True)


def test_result_replay_rejects_equal_identity_tuple_substitution(
    certified_bundle,
    control_result,
    monkeypatch,
):
    owner = certified_bundle["control_owner"]
    first, second, _ = control_result.consumptions
    original_words = first.raw64_words
    equal_words = tuple(word for word in original_words)
    original = route_evidence._generator_from_snapshot
    calls = []
    assert equal_words == original_words
    assert equal_words is not original_words

    def substitute_during_second_replay(snapshot):
        generator = original(snapshot)
        calls.append(snapshot)
        if snapshot is second.stream_initial_state:
            object.__setattr__(first, "raw64_words", equal_words)
            assert control._validate_consumption_record(first) is first
        return generator

    monkeypatch.setattr(
        route_evidence,
        "_generator_from_snapshot",
        substitute_during_second_replay,
    )
    try:
        with pytest.raises(ValueError, match="raw64_words changed identity"):
            owner.validate_result(
                control_result,
                2600,
                9,
                control_plan=CONTROL_PLAN,
            )
        assert len(calls) >= 2
    finally:
        object.__setattr__(first, "raw64_words", original_words)


def test_result_replay_rejects_prior_value_equal_address_substitution(
    certified_bundle,
    control_result,
    monkeypatch,
):
    owner = certified_bundle["control_owner"]
    first, second, _ = control_result.consumptions
    stream = first.control_stream
    original_address = stream.address
    equal_address = _construct_address(_address_values(original_address))
    original = route_evidence._generator_from_snapshot
    substitution_made = []

    assert equal_address is not original_address
    assert equal_address.address_sha256 == original_address.address_sha256

    def substitute_during_later_sibling_replay(snapshot):
        generator = original(snapshot)
        if snapshot is second.stream_initial_state and not substitution_made:
            object.__setattr__(stream, "address", equal_address)
            control._validate_stream_record(stream)
            assert control._validate_consumption_record(first) is first
            substitution_made.append(True)
        return generator

    monkeypatch.setattr(
        route_evidence,
        "_generator_from_snapshot",
        substitute_during_later_sibling_replay,
    )
    try:
        with pytest.raises(ValueError, match="stream 0 field address changed identity"):
            owner.validate_result(
                control_result,
                2600,
                9,
                control_plan=CONTROL_PLAN,
            )
        assert substitution_made == [True]
    finally:
        object.__setattr__(stream, "address", original_address)


def test_consume_and_all_validators_exclude_and_do_not_advance_caller_rng(
    certified_bundle,
):
    owner = certified_bundle["control_owner"]
    for method in (
        owner.consume,
        owner.validate_control_stream,
        owner.reconstruct_control_stream,
        owner.validate_stream_consumption,
        owner.validate_result,
    ):
        assert "rng" not in inspect.signature(method).parameters
    original_state = np.random.get_state()
    try:
        np.random.seed(2615)
        before = np.random.get_state()
        result = owner.consume(2615, 0, control_plan=((0, 0, 2),))
        owner.validate_result(
            result,
            2615,
            0,
            control_plan=((0, 0, 2),),
        )
        after = np.random.get_state()
        assert before[0] == after[0]
        assert np.array_equal(before[1], after[1])
        assert before[2:] == after[2:]
    finally:
        np.random.set_state(original_state)
    with pytest.raises(TypeError):
        owner.consume(
            2615,
            0,
            control_plan=(),
            rng=np.random.default_rng(1),
        )


def test_raw_word_record_requires_exact_canonical_uint64_integers(control_result):
    record = control_result.consumptions[0]
    for invalid in (True, False, -1, 1 << 64, 1.0, np.int64(1), np.uint64(1)):
        with pytest.raises((TypeError, ValueError)):
            _construct_record(
                _record_values(
                    record,
                    raw64_words=(invalid,),
                )
            )


def test_record_and_result_top_level_caps_preflight_before_deep_validation(
    control_result,
    monkeypatch,
):
    record = control_result.consumptions[0]
    record_values = {name: getattr(record, name) for name in control._record_fields()}
    record_values["raw64_word_count"] = MAX_WORDS + 1
    record_values["raw64_words"] = (record.raw64_words[0],) * (MAX_WORDS + 1)

    def forbidden_record(*args, **kwargs):
        del args, kwargs
        raise AssertionError("oversized raw tuple reached deep record validation")

    monkeypatch.setattr(control, "_validate_consumption_record", forbidden_record)
    with pytest.raises(ValueError, match="maximum bound"):
        _construct_record(record_values)

    result_values = {
        name: getattr(control_result, name) for name in control._result_fields()
    }
    result_values["consumptions"] = (record,) * (MAX_STREAMS + 1)

    def forbidden_result(*args, **kwargs):
        del args, kwargs
        raise AssertionError("oversized result reached deep result validation")

    monkeypatch.setattr(control, "_validate_result_record", forbidden_result)
    with pytest.raises(ValueError, match="tuple exceeds"):
        _construct_result(result_values)


def test_standalone_certificate_runtime_and_oversized_tag_forgeries_refuse(
    certified_bundle,
    monkeypatch,
):
    certificate = certified_bundle["control_owner"].certificate
    with pytest.raises(ValueError, match="runtime"):
        _construct_certificate(
            _certificate_values(
                certificate,
                control_runtime_sha256="0" * 64,
            )
        )

    oversized = certificate.reserved_parent_domain_tags + (("alien", 8),)
    values = _certificate_values(
        certificate,
        reserved_parent_domain_tags=oversized,
    )

    def accepted_parent(value):
        assert value is certificate.checkpoint25_certificate
        return value

    def forbidden_entry_traversal(*args, **kwargs):
        del args, kwargs
        raise AssertionError("oversized reserved-tag tuple was traversed")

    monkeypatch.setattr(
        control._consumption,
        "_validate_certificate",
        accepted_parent,
    )
    monkeypatch.setattr(
        control._lineage,
        "_exact_uint64",
        forbidden_entry_traversal,
    )
    with pytest.raises(ValueError, match="exactly six pairs"):
        _construct_certificate(values)


def test_records_owner_certificate_address_and_stream_are_sealed(
    certified_bundle,
    control_result,
):
    owner = certified_bundle["control_owner"]
    record = control_result.consumptions[0]
    values = (
        owner,
        owner.certificate,
        record.control_stream.address,
        record.control_stream,
        record,
        control_result,
    )
    for value in values:
        for operation in (pickle.dumps, copy.copy, copy.deepcopy):
            with pytest.raises(TypeError):
                operation(value)
    for value_type in (
        control.CounterKeyedGlobalInitializerControlCertificate,
        control.CounterKeyedGlobalInitializerControlAddress,
        control.CounterKeyedGlobalInitializerControlStream,
        control.CounterKeyedGlobalInitializerControlConsumption,
        control.CounterKeyedGlobalInitializerControlResult,
        control.CounterKeyedGlobalInitializerControlOwner,
    ):
        with pytest.raises(TypeError, match="subclass"):
            type("ForbiddenSubclass", (value_type,), {})


def test_certificate_complete_truth_matrix(certified_bundle):
    certificate = certified_bundle["control_owner"].certificate
    positive = {
        "exact_checkpoint25_owner_binding_certified",
        "exact_checkpoint24_owner_binding_certified",
        "exact_checkpoint23_owner_binding_certified",
        "collision_disjoint_tag7_domain_certified",
        "initialization_index_address_coordinate_certified",
        "exact_direct_control_address_certified",
        "canonical_control_plan_certified",
        "within_plan_unique_address_certified",
        "bounded_work_preflight_certified",
        "empty_plan_zero_word_certified",
        "exact_pre_post_snapshot_custody_certified",
        "same_runtime_prefix_replay_certified",
        "recorded_upper_counter_limb_preservation_certified",
        "no_caller_rng_certified",
        "global_control_stream_consumption_certified",
        "global_initializer_control_namespace_certified",
        "passed",
    }
    negative = {
        "stage_semantics_certified",
        "attempt_semantics_certified",
        "branch_chronology_semantics_certified",
        "abandoned_or_retry_address_nonreuse_certified",
        "global_duplicate_address_use_prevention_certified",
        "global_run_id_uniqueness_certified",
        "tag3_cross_initialization_disjointness_certified",
        "tag3_occurrence_payload_coordination_certified",
        "tag3_occurrence_stream_consumption_certified",
        "accepted_configuration_to_lineage_mapping_certified",
        "occurrence_serial_allocation_certified",
        "initialization_index_uniqueness_certified",
        "append_or_continuation_semantics_certified",
        "event_or_configuration_generation_certified",
        "cardinality_law_certified",
        "event_type_law_certified",
        "coordinate_law_certified",
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
    }
    assert all(getattr(certificate, name) is True for name in positive)
    assert all(getattr(certificate, name) is False for name in negative)
    metadata = {
        "schema_version",
        "certificate_scope",
        "control_policy",
        "control_role_sha256",
        "process_parameter_sha256",
        "checkpoint25_certificate",
        "checkpoint25_certificate_sha256",
        "checkpoint25_role_sha256",
        "checkpoint25_runtime_sha256",
        "checkpoint24_certificate_sha256",
        "checkpoint24_role_sha256",
        "checkpoint24_runtime_sha256",
        "checkpoint23_certificate_sha256",
        "checkpoint23_role_sha256",
        "checkpoint23_runtime_sha256",
        "control_runtime_sha256",
        "philox_snapshot_schema_version",
        "rng_bit_generator",
        "global_control_domain",
        "global_control_domain_tag",
        "address_layout",
        "reserved_parent_domain_tags",
        "maximum_stream_records",
        "maximum_raw64_words_per_stream",
        "maximum_total_raw64_words",
        "certificate_sha256",
    }
    assert positive | negative | metadata == set(type(certificate).__annotations__)


def test_live_owner_binding_rejects_same_digest_parent_substitution(
    certified_bundle,
    same_digest_alien_owner,
):
    parent = certified_bundle["consumption_owner"]
    local_owner = _certify_control(parent, role="8" * 64)
    alien_parent = checkpoint25_tests._certify_consumption(
        certified_bundle["epoch_owner"],
        consumption_policy=checkpoint25_tests.CONSUMPTION_POLICY,
        consumption_role_sha256=checkpoint25_tests.CONSUMPTION_ROLE,
    )
    assert alien_parent is not parent
    assert alien_parent.certificate.certificate_sha256 == (
        parent.certificate.certificate_sha256
    )
    object.__setattr__(local_owner, "_consumption_owner", alien_parent)
    with pytest.raises(ValueError, match="checkpoint-25 owner binding changed"):
        local_owner.consume(2616, 0, control_plan=())

    local_same_role = _certify_control(parent)
    assert local_same_role.certificate is not same_digest_alien_owner.certificate
    assert local_same_role.certificate.certificate_sha256 == (
        same_digest_alien_owner.certificate.certificate_sha256
    )
    object.__setattr__(
        local_same_role,
        "_certificate",
        same_digest_alien_owner.certificate,
    )
    with pytest.raises(ValueError, match="certified certificate object changed"):
        local_same_role.consume(2617, 0, control_plan=())

    local_role = _certify_control(parent, role="a" * 64)
    alien_role = _certify_control(parent, role="b" * 64)
    object.__setattr__(
        local_role,
        "_control_role_sha256",
        alien_role.certificate.control_role_sha256,
    )
    object.__setattr__(local_role, "_certificate", alien_role.certificate)
    with pytest.raises(ValueError, match="certified role changed"):
        local_role.consume(2618, 0, control_plan=())


def test_factory_require_validator_and_exact_parent_binding(certified_bundle):
    parent = certified_bundle["consumption_owner"]
    owner = certified_bundle["control_owner"]
    assert (
        _require_control(
            parent,
            owner,
            control_policy=CONTROL_POLICY,
            control_role_sha256=CONTROL_ROLE,
        )
        is owner
    )
    assert (
        _validate_control_certificate(
            parent,
            owner,
            control_policy=CONTROL_POLICY,
            control_role_sha256=CONTROL_ROLE,
        )
        is owner.certificate
    )
    for arguments in (
        {
            "control_policy": "unsupported",
            "control_role_sha256": CONTROL_ROLE,
        },
        {
            "control_policy": CONTROL_POLICY,
            "control_role_sha256": "9" * 64,
        },
        {
            "control_policy": None,
            "control_role_sha256": CONTROL_ROLE,
        },
    ):
        with pytest.raises((TypeError, ValueError)):
            _require_control(
                parent,
                owner,
                **arguments,
            )


def test_public_surface_static_rng_boundary_and_nonclaims(certified_bundle):
    expected = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCOPE",
        "COUNTER_KEY_DOMAIN_GLOBAL_INITIALIZER_CONTROL",
        "COUNTER_KEY_DOMAIN_TAG_GLOBAL_INITIALIZER_CONTROL",
        "COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_ADDRESS_LAYOUT",
        "COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS",
        "COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM",
        "COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_TOTAL_RAW64_WORDS",
        "CounterKeyedGlobalInitializerControlCertificate",
        "CounterKeyedGlobalInitializerControlAddress",
        "CounterKeyedGlobalInitializerControlStream",
        "CounterKeyedGlobalInitializerControlConsumption",
        "CounterKeyedGlobalInitializerControlResult",
        "CounterKeyedGlobalInitializerControlOwner",
        "PluginBridgeCounterKeyedGlobalInitializerControlError",
        "certify_plugin_bridge_counter_keyed_global_initializer_control",
        "require_matching_plugin_bridge_counter_keyed_global_initializer_control",
        "validate_plugin_bridge_counter_keyed_global_initializer_control_certificate",
    }
    assert set(control.__all__) == expected
    source = inspect.getsource(control)
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
    assert "make_initializer_stream" not in source
    assert "make_operational_epoch_stream" not in source
    scope = control.PLUGIN_BRIDGE_COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_SCOPE
    for phrase in (
        "empty-plan-is-namespace-noop-not-empty-configuration",
        "not-stage-or-attempt-semantics",
        "not-branch-or-retry-chronology",
        "not-cardinality-type-event-coordinate-or-configuration-law",
        "not-reference-conditional-or-tilted-initializer-law",
        "not-enumeration-rejection-resampling-or-sir",
        "not-tag3-cross-initialization-disjointness-or-payload-coordination",
        "not-accepted-configuration-to-lineage-mapping",
        "not-append-or-continuation-semantics",
        "not-statistical-independence",
        "not-brownian",
        "not-drift",
        "not-path",
        "not-full-sampler",
        "not-runtime-portable",
        "not-cryptographic",
    ):
        assert phrase in scope
    certificate = certified_bundle["control_owner"].certificate
    assert certificate.initializer_admissible is False
    assert certificate.full_sampler_admissible is False
    assert certificate.statistical_independence_certified is False
    assert certificate.runtime_portable is False
    assert certificate.cryptographic_authentication is False


def test_optional_torch_import_boundary_is_explicit():
    module_path = Path(control.__file__).resolve()
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
        plugin_bridge_counter_keyed_global_initializer_control,
    )
except ModuleNotFoundError as error:
    text = str(error)
    assert "global initializer control" in text
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
