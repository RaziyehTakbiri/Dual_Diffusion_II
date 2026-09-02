"""Hostile tests for checkpoint-27 initializer protocol allocation."""

import ast
import importlib
import inspect
from pathlib import Path
import pickle
import subprocess
import sys

import numpy as np
import pytest


pytest.importorskip("torch", reason="initializer protocol requires PyTorch stack")

checkpoint25_tests = importlib.import_module(
    "test_plugin_bridge_counter_keyed_initializer_stream_consumption"
)
checkpoint26_tests = importlib.import_module(
    "test_plugin_bridge_counter_keyed_global_initializer_control"
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initializer_protocol as protocol,
)


PROTOCOL_ROLE = "8" * 64
PROTOCOL_POLICY = protocol.PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_POLICY


def _certify(parent, *, role=PROTOCOL_ROLE):
    return protocol.certify_plugin_bridge_counter_keyed_initializer_protocol(
        parent,
        protocol_policy=PROTOCOL_POLICY,
        protocol_role_sha256=role,
    )


@pytest.fixture(scope="module")
def certified_bundle():
    bundle = checkpoint25_tests._certified_bundle(total_cap=2)
    control_owner = checkpoint26_tests._certify_control(bundle["consumption_owner"])
    bundle["control_owner"] = control_owner
    bundle["protocol_owner"] = _certify(control_owner)
    bundle["same_digest_alien_owner"] = _certify(control_owner)
    return bundle


@pytest.fixture(scope="module")
def allocations(certified_bundle):
    owner = certified_bundle["protocol_owner"]
    return {
        "enumeration": owner.allocate(
            2700,
            4,
            strategy=protocol.INITIALIZER_STRATEGY_ENUMERATION,
            strategy_budget=1,
            work_item_raw64_word_counts=(),
            selection_raw64_word_count=3,
        ),
        "rejection": owner.allocate(
            2700,
            4,
            strategy=protocol.INITIALIZER_STRATEGY_REJECTION,
            strategy_budget=3,
            work_item_raw64_word_counts=(5, 2),
            selection_raw64_word_count=0,
        ),
        "sir": owner.allocate(
            2700,
            4,
            strategy=protocol.INITIALIZER_STRATEGY_SIR,
            strategy_budget=2,
            work_item_raw64_word_counts=(4, 3),
            selection_raw64_word_count=2,
        ),
        "reference": owner.allocate(
            2700,
            4,
            strategy=protocol.INITIALIZER_STRATEGY_REFERENCE,
            strategy_budget=1,
            work_item_raw64_word_counts=(2, 3, 1),
            selection_raw64_word_count=0,
        ),
    }


def _forged(value, **updates):
    forged = object.__new__(type(value))
    for name in type(value).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(value, name)))
    return forged


def _certificate_values(certificate, **updates):
    values = {
        name: updates.get(name, getattr(certificate, name))
        for name in protocol._certificate_fields()
    }
    values["certificate_sha256"] = "0" * 64
    values["certificate_sha256"] = protocol._thinning._semantic_digest(
        protocol._certificate_payload(values)
    )
    return values


def _entry_values(entry, **updates):
    values = {
        name: updates.get(name, getattr(entry, name))
        for name in protocol._entry_fields()
    }
    values["entry_sha256"] = "0" * 64
    values["entry_sha256"] = protocol._thinning._semantic_digest(
        protocol._entry_payload(values)
    )
    return values


def _result_values(result, **updates):
    values = {
        name: updates.get(name, getattr(result, name))
        for name in protocol._result_fields()
    }
    if "entries" in updates and "entry_sha256s" not in updates:
        values["entry_sha256s"] = tuple(
            entry.entry_sha256 for entry in values["entries"]
        )
    if "parent_control_result" in updates and "parent_result_sha256" not in updates:
        values["parent_result_sha256"] = values["parent_control_result"].result_sha256
    values["result_sha256"] = "0" * 64
    values["result_sha256"] = protocol._thinning._semantic_digest(
        protocol._result_payload(values)
    )
    return values


def _validate(owner, result):
    return owner.validate_result(
        result,
        result.run_id,
        result.initialization_index,
        strategy=result.strategy,
        strategy_budget=result.strategy_budget,
        work_item_raw64_word_counts=result.work_item_raw64_word_counts,
        selection_raw64_word_count=result.selection_raw64_word_count,
    )


def test_certificate_freezes_exact_parent_stage_map_caps_and_truth_matrix(
    certified_bundle,
):
    owner = certified_bundle["protocol_owner"]
    certificate = owner.certificate
    parent = certified_bundle["control_owner"].certificate

    assert certificate.checkpoint26_certificate is parent
    assert certificate.checkpoint26_certificate_sha256 == parent.certificate_sha256
    assert certificate.checkpoint26_role_sha256 == parent.control_role_sha256
    assert certificate.checkpoint26_runtime_sha256 == parent.control_runtime_sha256
    assert certificate.process_parameter_sha256 == parent.process_parameter_sha256
    assert certificate.strategies == (
        "enumeration",
        "rejection",
        "sir",
        "reference",
    )
    assert certificate.stage_roles == (
        (0, "enumeration_selection"),
        (1, "rejection_attempt"),
        (2, "sir_particle"),
        (3, "sir_resample"),
        (4, "reference_candidate"),
    )
    assert certificate.maximum_rejection_attempts == 64
    assert certificate.maximum_sir_particles == 63

    positive = {
        "exact_checkpoint26_owner_binding_certified",
        "disjoint_strategy_stage_semantics_certified",
        "strategy_specific_attempt_semantics_certified",
        "fixed_multiblock_work_item_allocation_certified",
        "canonical_chronological_allocation_certified",
        "fixed_nonadaptive_budget_preflight_certified",
        "within_allocation_unique_addresses_certified",
        "complete_parent_prefix_materialization_certified",
        "exact_parent_result_replay_certified",
        "no_caller_rng_certified",
        "protocol_allocation_certified",
    }
    for name in protocol.CounterKeyedInitializerProtocolCertificate.__annotations__:
        if name.endswith("certified") or name.endswith("admissible"):
            assert getattr(certificate, name) is (name in positive)
    assert certificate.passed is True
    assert certificate.analytic_target_preserved is False
    assert certificate.rounded_stationarity_certified is False
    assert certificate.sampler_liveness_certified is False
    assert certificate.runtime_portable is False
    assert certificate.cryptographic_authentication is False


def test_strategy_plans_roles_chronology_and_parent_identity(allocations):
    enumeration = allocations["enumeration"]
    rejection = allocations["rejection"]
    sir = allocations["sir"]
    reference = allocations["reference"]

    assert enumeration.control_plan == ((0, 0, 3),)
    assert rejection.control_plan == (
        (1, 0, 5),
        (1, 1, 2),
        (1, 2, 5),
        (1, 3, 2),
        (1, 4, 5),
        (1, 5, 2),
    )
    assert sir.control_plan == (
        (2, 0, 4),
        (2, 1, 3),
        (2, 2, 4),
        (2, 3, 3),
        (3, 0, 2),
    )
    assert reference.control_plan == ((4, 0, 2), (4, 1, 3), (4, 2, 1))
    assert tuple(entry.semantic_role for entry in enumeration.entries) == (
        "enumeration_selection",
    )
    assert tuple(entry.semantic_role for entry in rejection.entries) == (
        "rejection_attempt",
        "rejection_attempt",
        "rejection_attempt",
        "rejection_attempt",
        "rejection_attempt",
        "rejection_attempt",
    )
    assert tuple(entry.semantic_role for entry in sir.entries) == (
        "sir_particle",
        "sir_particle",
        "sir_particle",
        "sir_particle",
        "sir_resample",
    )
    assert tuple(entry.semantic_role for entry in reference.entries) == (
        "reference_candidate",
        "reference_candidate",
        "reference_candidate",
    )
    assert tuple(
        (entry.work_item_index, entry.block_index) for entry in rejection.entries
    ) == ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1))
    assert tuple(
        (entry.work_item_index, entry.block_index) for entry in sir.entries
    ) == ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))
    assert tuple(
        (entry.work_item_index, entry.block_index) for entry in reference.entries
    ) == ((0, 0), (0, 1), (0, 2))
    for result in allocations.values():
        assert tuple(entry.chronological_index for entry in result.entries) == tuple(
            range(len(result.entries))
        )
        assert tuple(entry.plan_position for entry in result.entries) == tuple(
            range(len(result.entries))
        )
        assert result.stream_record_count == len(result.control_plan)
        assert result.total_raw64_words == sum(item[2] for item in result.control_plan)
        assert all(
            entry.parent_consumption is parent
            for entry, parent in zip(
                result.entries,
                result.parent_control_result.consumptions,
            )
        )
        assert all(
            entry.raw64_words is entry.parent_consumption.raw64_words
            for entry in result.entries
        )


def test_every_entry_matches_the_direct_tag7_prefix(allocations):
    for result in allocations.values():
        for entry in result.entries:
            expected, final = checkpoint26_tests._direct_prefix(
                run_id=result.run_id,
                initialization_index=result.initialization_index,
                stage_index=entry.stage_index,
                attempt_index=entry.attempt_index,
                word_count=entry.raw64_word_count,
            )
            assert entry.raw64_words == expected
            assert (
                entry.parent_consumption.stream_final_state.snapshot_sha256
                == final.snapshot_sha256
            )


def test_strategy_stages_are_address_disjoint_not_word_independence(allocations):
    addresses = []
    for result in allocations.values():
        addresses.extend(
            entry.parent_consumption.control_stream.address for entry in result.entries
        )
    coordinates = tuple(
        (
            address.run_id,
            address.initialization_index,
            address.stage_index,
            address.attempt_index,
        )
        for address in addresses
    )
    assert len(coordinates) == len(set(coordinates))
    assert {address.domain_tag for address in addresses} == {7}
    assert all(address.philox_key == (2700, 7) for address in addresses)


@pytest.mark.parametrize(
    "arguments,exception,match",
    [
        ((b"enumeration", 1, (), 1), TypeError, "strategy"),
        (("unknown", 1, (), 1), ValueError, "frozen"),
        (("enumeration", 0, (), 1), ValueError, "literal"),
        (("enumeration", 1, (1,), 1), ValueError, "no work-item"),
        (("enumeration", 1, (), 0), ValueError, "positive"),
        (("rejection", 0, (1,), 0), ValueError, "at least"),
        (("rejection", 65, (1,), 0), ValueError, "maximum"),
        (("rejection", 1, (), 0), ValueError, "at least one block"),
        (("rejection", 1, (1,), 1), ValueError, "separate"),
        (("sir", 0, (1,), 1), ValueError, "at least"),
        (("sir", 64, (1,), 1), ValueError, "maximum"),
        (("sir", 1, (), 1), ValueError, "at least one block"),
        (("sir", 1, (1,), 0), ValueError, "positive"),
        (("sir", 63, (1041,), 1), ValueError, "aggregate"),
        (("reference", 0, (1,), 0), ValueError, "literal"),
        (("reference", 2, (1,), 0), ValueError, "literal"),
        (("reference", 1, (), 0), ValueError, "at least one"),
        (("reference", 1, (1,), 1), ValueError, "separate"),
        (("reference", 1, [1], 0), TypeError, "exact tuple"),
    ],
)
def test_strategy_request_matrix_refuses_before_parent_work(
    arguments,
    exception,
    match,
):
    with pytest.raises(exception, match=match):
        protocol._preflight_protocol_request(*arguments)


@pytest.mark.parametrize(
    "position,value",
    [
        (1, True),
        (1, np.uint64(1)),
        (1, -1),
        (3, True),
        (3, np.uint64(1)),
    ],
)
def test_strategy_scalars_require_exact_python_uint64(position, value):
    arguments = ["sir", 1, (1,), 1]
    arguments[position] = value
    with pytest.raises((TypeError, ValueError)):
        protocol._preflight_protocol_request(*arguments)


@pytest.mark.parametrize(
    "blocks,exception,match",
    [
        ((True,), TypeError, "exact integer"),
        ((np.uint64(1),), TypeError, "exact integer"),
        ((0,), ValueError, "positive"),
        ((4097,), ValueError, "per-stream"),
        ((1,) * 65, ValueError, "record bound"),
    ],
)
def test_work_item_blocks_are_exact_positive_bounded_words(
    blocks,
    exception,
    match,
):
    with pytest.raises(exception, match=match):
        protocol._preflight_protocol_request("reference", 1, blocks, 0)


def test_inclusive_protocol_boundaries_are_canonical():
    rejection = protocol._preflight_protocol_request("rejection", 64, (1024,), 0)
    sir = protocol._preflight_protocol_request("sir", 63, (1024,), 1024)
    reference = protocol._preflight_protocol_request("reference", 1, (1024,) * 64, 0)
    assert len(rejection[-1]) == 64
    assert rejection[-1][-1] == (1, 63, 1024)
    assert sum(item[2] for item in rejection[-1]) == 65_536
    assert len(sir[-1]) == 64
    assert sir[-1][-1] == (3, 0, 1024)
    assert sum(item[2] for item in sir[-1]) == 65_536
    assert len(reference[-1]) == 64
    assert reference[-1][-1] == (4, 63, 1024)
    assert sum(item[2] for item in reference[-1]) == 65_536


def test_reissue_replays_instead_of_appending(certified_bundle, allocations):
    owner = certified_bundle["protocol_owner"]
    first = allocations["enumeration"]
    second = owner.allocate(
        first.run_id,
        first.initialization_index,
        strategy=first.strategy,
        strategy_budget=first.strategy_budget,
        work_item_raw64_word_counts=first.work_item_raw64_word_counts,
        selection_raw64_word_count=first.selection_raw64_word_count,
    )
    assert second is not first
    assert second.result_sha256 == first.result_sha256
    assert second.entries[0].raw64_words == first.entries[0].raw64_words
    assert second.entries[0].parent_consumption is not (
        first.entries[0].parent_consumption
    )


def test_live_owner_and_certificate_api(certified_bundle):
    control_owner = certified_bundle["control_owner"]
    owner = certified_bundle["protocol_owner"]
    required = (
        protocol.require_matching_plugin_bridge_counter_keyed_initializer_protocol(
            control_owner,
            owner,
            protocol_policy=PROTOCOL_POLICY,
            protocol_role_sha256=PROTOCOL_ROLE,
        )
    )
    certificate = (
        protocol.validate_plugin_bridge_counter_keyed_initializer_protocol_certificate(
            control_owner,
            owner,
            protocol_policy=PROTOCOL_POLICY,
            protocol_role_sha256=PROTOCOL_ROLE,
        )
    )
    assert required is owner
    assert certificate is owner.certificate


def test_same_digest_alien_certificate_and_owner_are_not_interchangeable(
    certified_bundle,
    allocations,
):
    owner = certified_bundle["protocol_owner"]
    alien = certified_bundle["same_digest_alien_owner"]
    assert alien is not owner
    assert alien.certificate is not owner.certificate
    assert alien.certificate.certificate_sha256 == owner.certificate.certificate_sha256

    result = allocations["enumeration"]
    forged = _forged(
        result,
        **_result_values(
            result,
            certificate=alien.certificate,
            certificate_sha256=alien.certificate.certificate_sha256,
        ),
    )
    protocol._validate_result_record(forged)
    with pytest.raises(ValueError, match="another owner"):
        _validate(owner, forged)


@pytest.mark.parametrize(
    "update,match",
    [
        ({"semantic_role": "sir_particle"}, "role"),
        ({"stage_index": 3}, "stage"),
        ({"attempt_index": 7}, "chronology"),
        ({"chronological_index": 2}, "chronology"),
        ({"raw64_word_count": 4}, "parent record"),
        ({"prefix_materialized_without_semantic_resolution": False}, "flag"),
    ],
)
def test_entry_semantic_and_parent_tampering_is_refused(allocations, update, match):
    entry = allocations["enumeration"].entries[0]
    forged = _forged(entry, **_entry_values(entry, **update))
    with pytest.raises(ValueError, match=match):
        protocol._validate_entry_record(forged)


def test_distinct_equal_raw_tuple_is_not_a_valid_nested_relation(allocations):
    entry = allocations["rejection"].entries[0]
    cloned_words = tuple(list(entry.raw64_words))
    assert cloned_words == entry.raw64_words
    assert cloned_words is not entry.raw64_words
    forged = _forged(
        entry,
        **_entry_values(entry, raw64_words=cloned_words),
    )
    with pytest.raises(ValueError, match="identity"):
        protocol._validate_entry_record(forged)


@pytest.mark.parametrize(
    "update,match",
    [
        ({"strategy": "rejection"}, "at least one block"),
        ({"strategy_budget": 2}, "literal"),
        ({"work_item_raw64_word_counts": (1,)}, "no work-item"),
        ({"work_item_block_count": 1}, "work_item_block_count"),
        ({"selection_raw64_word_count": 1}, "plan"),
        ({"stream_record_count": 2}, "stream_record_count"),
        ({"total_raw64_words": 4}, "total_raw64_words"),
        ({"fixed_nonadaptive_budget": False}, "flag"),
        ({"complete_parent_prefix_materialization": False}, "flag"),
        ({"canonical_chronological_allocation": False}, "flag"),
        ({"no_caller_rng": False}, "flag"),
    ],
)
def test_result_semantic_flags_and_counts_are_not_self_attested(
    allocations,
    update,
    match,
):
    result = allocations["enumeration"]
    forged = _forged(result, **_result_values(result, **update))
    with pytest.raises((TypeError, ValueError), match=match):
        protocol._validate_result_record(forged)


def test_entry_omission_duplication_reorder_and_cross_parent_are_refused(allocations):
    rejection = allocations["rejection"]
    sir = allocations["sir"]
    variants = (
        rejection.entries[:-1],
        rejection.entries + (rejection.entries[-1],),
        tuple(reversed(rejection.entries)),
        (sir.entries[0],) + rejection.entries[1:],
    )
    for entries in variants:
        forged = _forged(
            rejection,
            **_result_values(rejection, entries=entries),
        )
        with pytest.raises(ValueError):
            protocol._validate_result_record(forged)


@pytest.mark.parametrize("update", [{"work_item_index": 1}, {"block_index": 1}])
def test_nested_work_item_or_block_mapping_tampering_is_refused(
    allocations,
    update,
):
    result = allocations["rejection"]
    forged_entry = _forged(
        result.entries[0],
        **_entry_values(result.entries[0], **update),
    )
    forged_entries = (forged_entry,) + result.entries[1:]
    forged_result = _forged(
        result,
        **_result_values(result, entries=forged_entries),
    )
    with pytest.raises(ValueError, match="work-item/block mapping"):
        protocol._validate_result_record(forged_result)


@pytest.mark.parametrize(
    "update,exception,match",
    [
        ({"control_plan": ((False, False, 3.0),)}, TypeError, "exact integer"),
        (
            {"active_stage_roles": ((False, "enumeration_selection"),)},
            TypeError,
            "exact integer",
        ),
        (
            {
                "active_stage_roles": ((0, "enumeration_selection"),) * 65,
            },
            ValueError,
            "wrong fixed length",
        ),
    ],
)
def test_equal_looking_noncanonical_result_tuples_are_refused(
    certified_bundle,
    allocations,
    update,
    exception,
    match,
):
    owner = certified_bundle["protocol_owner"]
    result = allocations["enumeration"]
    forged = _forged(result, **_result_values(result, **update))
    with pytest.raises(exception, match=match):
        _validate(owner, forged)


def test_result_plan_type_is_checked_before_hostile_equality(allocations):
    class HostilePlan:
        def __ne__(self, other):
            del other
            raise AssertionError("hostile equality must not execute")

    result = allocations["enumeration"]
    forged = _forged(result, control_plan=HostilePlan())
    with pytest.raises(TypeError, match="exact tuple"):
        protocol._validate_result_record(forged)


def test_exact_equal_but_detached_result_plan_is_refused(allocations):
    result = allocations["enumeration"]
    detached_plan = tuple(tuple(field for field in row) for row in result.control_plan)
    assert detached_plan == result.control_plan
    assert detached_plan is not result.control_plan
    forged = _forged(
        result,
        **_result_values(result, control_plan=detached_plan),
    )
    with pytest.raises(ValueError, match="plan identity"):
        protocol._validate_result_record(forged)


def test_parent_result_and_record_splicing_is_refused(allocations):
    rejection = allocations["rejection"]
    sir = allocations["sir"]
    forged_result = _forged(
        rejection,
        **_result_values(rejection, parent_control_result=sir.parent_control_result),
    )
    with pytest.raises(ValueError):
        protocol._validate_result_record(forged_result)

    entry = rejection.entries[0]
    alien_record = sir.parent_control_result.consumptions[0]
    forged_entry = _forged(
        entry,
        **_entry_values(
            entry,
            parent_consumption=alien_record,
            parent_record_sha256=alien_record.record_sha256,
            raw64_words=alien_record.raw64_words,
        ),
    )
    with pytest.raises(ValueError):
        protocol._validate_entry_record(forged_entry)


def test_live_parent_owner_substitution_is_refused(certified_bundle):
    owner = certified_bundle["protocol_owner"]
    original = owner._control_owner
    object.__setattr__(
        owner,
        "_control_owner",
        checkpoint26_tests._certify_control(certified_bundle["consumption_owner"]),
    )
    try:
        with pytest.raises(ValueError, match="parent-owner binding"):
            owner._require_live_binding()
    finally:
        object.__setattr__(owner, "_control_owner", original)
    owner._require_live_binding()


def test_changed_role_and_certificate_truth_flag_are_refused(certified_bundle):
    owner = certified_bundle["protocol_owner"]
    certificate = owner.certificate
    changed_role = protocol.CounterKeyedInitializerProtocolCertificate(
        **_certificate_values(certificate, protocol_role_sha256="9" * 64),
        _construction_token=protocol._CERTIFICATE_TOKEN,
    )
    original = owner._certificate
    object.__setattr__(owner, "_certificate", changed_role)
    try:
        with pytest.raises(ValueError, match="certified certificate"):
            owner._require_live_binding()
    finally:
        object.__setattr__(owner, "_certificate", original)
    owner._require_live_binding()
    with pytest.raises(ValueError, match="positive claim"):
        protocol.CounterKeyedInitializerProtocolCertificate(
            **_certificate_values(
                certificate,
                protocol_allocation_certified=False,
            ),
            _construction_token=protocol._CERTIFICATE_TOKEN,
        )
    with pytest.raises(ValueError, match="negative claim"):
        protocol.CounterKeyedInitializerProtocolCertificate(
            **_certificate_values(
                certificate,
                initializer_output_law_certified=True,
            ),
            _construction_token=protocol._CERTIFICATE_TOKEN,
        )
    noncanonical_stage_roles = (
        (False, certificate.stage_roles[0][1]),
    ) + certificate.stage_roles[1:]
    with pytest.raises(TypeError, match="exact integer"):
        protocol.CounterKeyedInitializerProtocolCertificate(
            **_certificate_values(
                certificate,
                stage_roles=noncanonical_stage_roles,
            ),
            _construction_token=protocol._CERTIFICATE_TOKEN,
        )


def test_simultaneous_role_and_matching_certificate_rebinding_is_refused(
    certified_bundle,
):
    owner = certified_bundle["protocol_owner"]
    original_role = owner._protocol_role_sha256
    original_certificate = owner._certificate
    changed_role = "9" * 64
    changed_certificate = protocol._make_certificate(
        certified_bundle["control_owner"].certificate,
        protocol_role_sha256=changed_role,
    )
    object.__setattr__(owner, "_protocol_role_sha256", changed_role)
    object.__setattr__(owner, "_certificate", changed_certificate)
    try:
        with pytest.raises(ValueError, match="certified role binding"):
            owner._require_live_binding()
    finally:
        object.__setattr__(owner, "_protocol_role_sha256", original_role)
        object.__setattr__(owner, "_certificate", original_certificate)
    owner._require_live_binding()


@pytest.mark.parametrize(
    "name,replacement,match",
    [
        ("INITIALIZER_STRATEGY_ENUMERATION", "changed", "strategy constants"),
        ("INITIALIZER_STAGE_ENUMERATION_SELECTION", 9, "stage constants"),
        ("INITIALIZER_ROLE_ENUMERATION_SELECTION", "changed", "role constants"),
    ],
)
def test_individual_protocol_constant_mutation_is_refused_by_live_binding(
    certified_bundle,
    name,
    replacement,
    match,
):
    owner = certified_bundle["protocol_owner"]
    original = getattr(protocol, name)
    setattr(protocol, name, replacement)
    try:
        with pytest.raises(ValueError, match=match):
            owner._require_live_binding()
    finally:
        setattr(protocol, name, original)
    owner._require_live_binding()


def test_no_caller_rng_or_legacy_global_rng_movement(certified_bundle):
    owner = certified_bundle["protocol_owner"]
    legacy_before = np.random.get_state()
    owner.allocate(
        2701,
        0,
        strategy="enumeration",
        strategy_budget=1,
        work_item_raw64_word_counts=(),
        selection_raw64_word_count=1,
    )
    legacy_after = np.random.get_state()
    assert legacy_before[0] == legacy_after[0]
    assert np.array_equal(legacy_before[1], legacy_after[1])
    assert legacy_before[2:] == legacy_after[2:]
    assert "rng" not in inspect.signature(owner.allocate).parameters
    assert "rng" not in inspect.signature(owner.validate_result).parameters


def test_records_and_owner_are_sealed_nonpickle_objects(certified_bundle, allocations):
    owner = certified_bundle["protocol_owner"]
    objects = (
        owner,
        owner.certificate,
        allocations["enumeration"],
        allocations["enumeration"].entries[0],
    )
    for value in objects:
        with pytest.raises((TypeError, AttributeError)):
            value.new_field = 1
        with pytest.raises(TypeError):
            pickle.dumps(value)
    with pytest.raises(TypeError):
        protocol.CounterKeyedInitializerProtocolCertificate(
            _construction_token=object()
        )

    with pytest.raises(TypeError):

        class BadResult(protocol.CounterKeyedInitializerProtocolResult):
            pass


def test_public_surface_is_exact_and_contains_no_transform_api():
    expected = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCOPE",
        "INITIALIZER_STRATEGY_ENUMERATION",
        "INITIALIZER_STRATEGY_REJECTION",
        "INITIALIZER_STRATEGY_SIR",
        "INITIALIZER_STRATEGY_REFERENCE",
        "INITIALIZER_STRATEGIES",
        "INITIALIZER_STAGE_ENUMERATION_SELECTION",
        "INITIALIZER_STAGE_REJECTION_ATTEMPT",
        "INITIALIZER_STAGE_SIR_PARTICLE",
        "INITIALIZER_STAGE_SIR_RESAMPLE",
        "INITIALIZER_STAGE_REFERENCE_CANDIDATE",
        "INITIALIZER_ROLE_ENUMERATION_SELECTION",
        "INITIALIZER_ROLE_REJECTION_ATTEMPT",
        "INITIALIZER_ROLE_SIR_PARTICLE",
        "INITIALIZER_ROLE_SIR_RESAMPLE",
        "INITIALIZER_ROLE_REFERENCE_CANDIDATE",
        "INITIALIZER_STAGE_ROLES",
        "COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_REJECTION_ATTEMPTS",
        "COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_SIR_PARTICLES",
        "CounterKeyedInitializerProtocolCertificate",
        "CounterKeyedInitializerProtocolEntry",
        "CounterKeyedInitializerProtocolResult",
        "CounterKeyedInitializerProtocolOwner",
        "PluginBridgeCounterKeyedInitializerProtocolError",
        "certify_plugin_bridge_counter_keyed_initializer_protocol",
        "require_matching_plugin_bridge_counter_keyed_initializer_protocol",
        "validate_plugin_bridge_counter_keyed_initializer_protocol_certificate",
    }
    assert set(protocol.__all__) == expected
    assert len(protocol.__all__) == len(set(protocol.__all__))
    assert all(getattr(protocol, name) is not None for name in expected)


def test_source_contains_no_second_rng_or_initializer_transform():
    source = inspect.getsource(protocol)
    tree = ast.parse(source)
    attributes = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    assert "default_rng" not in attributes
    assert "random_raw" not in attributes
    assert "random" not in attributes
    assert "choice" not in attributes
    assert "integers" not in attributes
    assert "normal" not in attributes
    assert "standard_normal" not in attributes
    assert "searchsorted" not in attributes
    assert "ndtri" not in source


def test_optional_torch_boundary_translates_dependency_failure():
    source = Path(protocol.__file__).resolve()
    script = """
import builtins
import runpy

real_import = builtins.__import__

def blocked(name, *args, **kwargs):
    if name == 'torch' or name.startswith('torch.'):
        raise ModuleNotFoundError("No module named 'torch'", name='torch')
    return real_import(name, *args, **kwargs)

builtins.__import__ = blocked
runpy.run_path(%r, run_name='initializer_protocol_without_torch')
""" % str(
        source
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "initializer protocol requires the optional PyTorch" in completed.stderr


def test_protocol_scope_retains_all_mandatory_initializer_nonclaims(
    certified_bundle,
):
    certificate = certified_bundle["protocol_owner"].certificate
    assert certificate.actual_branch_decision_certified is False
    assert certificate.rejection_predicate_certified is False
    assert certificate.rejection_success_or_failure_certified is False
    assert certificate.sir_weights_or_resampling_law_certified is False
    assert certificate.enumeration_support_or_normalization_certified is False
    assert certificate.finite_resolution_output_transform_certified is False
    assert certificate.cardinality_law_certified is False
    assert certificate.event_type_law_certified is False
    assert certificate.coordinate_law_certified is False
    assert certificate.initializer_output_law_certified is False
    assert certificate.reference_initializer_law_certified is False
    assert certificate.conditional_or_tilted_initializer_law_certified is False
    assert certificate.accepted_configuration_to_lineage_mapping_certified is False
    assert certificate.tag3_occurrence_payload_coordination_certified is False
    assert certificate.tag3_cross_initialization_disjointness_certified is False
    assert certificate.global_duplicate_address_use_prevention_certified is False
    assert certificate.global_run_id_uniqueness_certified is False
    assert certificate.statistical_independence_certified is False
    assert certificate.physical_randomness_certified is False
    assert certificate.brownian_stream_consumption_certified is False
    assert certificate.brownian_additive_coupling_certified is False
    assert certificate.continuous_drift_admissible is False
    assert certificate.initializer_admissible is False
    assert certificate.path_admissible is False
    assert certificate.strang_sampler_admissible is False
    assert certificate.full_sampler_admissible is False
