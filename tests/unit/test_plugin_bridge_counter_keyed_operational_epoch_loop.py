"""Hostile tests for checkpoint-24 counter-keyed operational epochs."""

import ast
import copy
import inspect
import math
from pathlib import Path
import pickle
import subprocess
import sys

import numpy as np
import pytest


pytest.importorskip(
    "torch", reason="counter-keyed operational epochs require the PyTorch stack"
)

import test_plugin_bridge_counter_keyed_lineage_contract as checkpoint23_tests
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_continuous_route_evidence as route_evidence,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_lineage_contract as lineage,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_operational_epoch_loop as epoch,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_operational_thinning as thinning,
)
from heterodiff.processes.plugin_bridge_sampler import (  # noqa: E402
    ProcessValidReferenceJumpComposer,
)
from heterodiff.theory.configuration_reference import (  # noqa: E402
    TransformedEvent,
)


BASE_CONTEXT = checkpoint23_tests.BASE_CONTEXT
RESIDUAL_CONTEXT = checkpoint23_tests.RESIDUAL_CONTEXT
EPOCH_ROLE = "7" * 64
TIGHT_RUN_ID = 17
TIGHT_STEP_INDEX = 3
TIGHT_RIGHT_ENDPOINT = 0.25
ORDINARY_RUN_ID = 0
ORDINARY_STEP_INDEX = 11


def _certify_epoch(bundle):
    contract_owner = checkpoint23_tests._certify_owner(bundle)
    owner = epoch.certify_plugin_bridge_counter_keyed_operational_epoch_loop(
        contract_owner,
        epoch_policy=epoch.PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY,
        epoch_role_sha256=EPOCH_ROLE,
    )
    bundle["contract_owner"] = contract_owner
    bundle["epoch_owner"] = owner
    return bundle


@pytest.fixture(scope="module")
def tight_bundle():
    return _certify_epoch(checkpoint23_tests._bundle(tight=True, total_cap=2))


@pytest.fixture(scope="module")
def ordinary_bundle():
    return _certify_epoch(checkpoint23_tests._bundle(tight=False, total_cap=1))


def _parents(bundle, *, state=(TransformedEvent(0),), reverse_time=0.4):
    intensity = bundle["reference_composer"].preflight_candidate_intensity(
        state,
        reverse_time=reverse_time,
    )
    envelope = bundle["rate_owner"].preflight_envelope(intensity)
    return intensity, envelope


def _bootstrap(bundle, intensity, *, run_id):
    return bundle["contract_owner"].bootstrap_lineage(
        intensity,
        run_id=run_id,
        initialization_index=0,
    )


def _run(
    bundle,
    intensity,
    envelope,
    initial_lineage,
    *,
    run_id,
    step_index,
    endpoint,
    budget,
):
    return bundle["epoch_owner"].run(
        intensity,
        envelope,
        initial_lineage,
        run_id=run_id,
        step_index=step_index,
        clock_start=0.0,
        right_endpoint=endpoint,
        proposal_budget=budget,
        base_context=BASE_CONTEXT,
        residual_context=RESIDUAL_CONTEXT,
    )


def _direct_generator(*, run_id, step_index, completed_proposals):
    return np.random.Generator(
        np.random.Philox(
            key=np.asarray(
                (run_id, epoch.COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH),
                dtype=np.uint64,
            ),
            counter=np.asarray(
                (0, step_index, 0, completed_proposals),
                dtype=np.uint64,
            ),
        )
    )


def _one_proposal_endpoint(
    envelope,
    *,
    run_id,
    step_index,
    completed_proposals=0,
    clock_start=0.0,
):
    generator = _direct_generator(
        run_id=run_id,
        step_index=step_index,
        completed_proposals=completed_proposals,
    )
    words = []
    trace = None
    while trace is None:
        words.append(int(generator.bit_generator.random_raw()))
        trace = thinning._waiting_trace(
            envelope.controlled_total_exit_upper_bound,
            clock_start,
            64.0,
            tuple(words),
        )
    assert trace["candidate_due"] is True
    return math.nextafter(trace["proposal_time"], math.inf)


@pytest.fixture(scope="module")
def tight_result_case(tight_bundle):
    intensity, envelope = _parents(tight_bundle)
    initial_lineage = _bootstrap(
        tight_bundle,
        intensity,
        run_id=TIGHT_RUN_ID,
    )
    result = _run(
        tight_bundle,
        intensity,
        envelope,
        initial_lineage,
        run_id=TIGHT_RUN_ID,
        step_index=TIGHT_STEP_INDEX,
        endpoint=TIGHT_RIGHT_ENDPOINT,
        budget=4,
    )
    assert result.proposal_count == 2
    assert tuple(proposal.accepted for proposal in result.proposals) == (True, True)
    return tight_bundle, intensity, envelope, initial_lineage, result


@pytest.fixture(scope="module")
def ordinary_result_case(ordinary_bundle):
    intensity, envelope = _parents(ordinary_bundle)
    initial_lineage = _bootstrap(
        ordinary_bundle,
        intensity,
        run_id=ORDINARY_RUN_ID,
    )
    endpoint = _one_proposal_endpoint(
        envelope,
        run_id=ORDINARY_RUN_ID,
        step_index=ORDINARY_STEP_INDEX,
    )
    stream = ordinary_bundle["epoch_owner"].make_operational_epoch_stream(
        ORDINARY_RUN_ID,
        ORDINARY_STEP_INDEX,
        0,
    )
    proposal, terminal = ordinary_bundle["epoch_owner"]._execute_proposal(
        stream,
        intensity,
        envelope,
        initial_lineage,
        cursor=0.0,
        right_endpoint=endpoint,
        base_context=BASE_CONTEXT,
        residual_context=RESIDUAL_CONTEXT,
        run_id=ORDINARY_RUN_ID,
        step_index=ORDINARY_STEP_INDEX,
        proposal_index=0,
    )
    assert terminal is None
    assert proposal is not None and proposal.accepted is False
    terminal_stream = ordinary_bundle["epoch_owner"].make_operational_epoch_stream(
        ORDINARY_RUN_ID,
        ORDINARY_STEP_INDEX,
        1,
    )
    next_proposal, terminal = ordinary_bundle["epoch_owner"]._execute_proposal(
        terminal_stream,
        intensity,
        envelope,
        initial_lineage,
        cursor=proposal.iteration.proposal_time,
        right_endpoint=endpoint,
        base_context=BASE_CONTEXT,
        residual_context=RESIDUAL_CONTEXT,
        run_id=ORDINARY_RUN_ID,
        step_index=ORDINARY_STEP_INDEX,
        proposal_index=1,
    )
    assert next_proposal is None and terminal is not None
    result = epoch._make_result(
        ordinary_bundle["epoch_owner"].certificate,
        run_id=ORDINARY_RUN_ID,
        step_index=ORDINARY_STEP_INDEX,
        initial_intensity=intensity,
        initial_envelope=envelope,
        initial_lineage_state=initial_lineage,
        base_context=BASE_CONTEXT,
        residual_context=RESIDUAL_CONTEXT,
        clock_start=0.0,
        right_endpoint=endpoint,
        proposal_budget=2,
        proposals=(proposal,),
        terminal=terminal,
    )
    return ordinary_bundle, intensity, envelope, initial_lineage, proposal, result


@pytest.fixture(scope="module")
def deterministic_terminal_cases(tight_bundle):
    cases = {}
    requests = (
        ("zero_duration", 0.4, 0.0, 240, 24),
        ("reference_zero", 0.8, 1.0, 241, 25),
        ("both", 0.8, 0.0, 242, 26),
    )
    for name, reverse_time, endpoint, run_id, step_index in requests:
        intensity, envelope = _parents(tight_bundle, reverse_time=reverse_time)
        initial_lineage = _bootstrap(tight_bundle, intensity, run_id=run_id)
        result = _run(
            tight_bundle,
            intensity,
            envelope,
            initial_lineage,
            run_id=run_id,
            step_index=step_index,
            endpoint=endpoint,
            budget=0,
        )
        cases[name] = (intensity, envelope, initial_lineage, result)
    return cases


def _forged_record(record, **updates):
    forged = object.__new__(type(record))
    for name in type(record).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(record, name)))
    return forged


def _address_values(address, **updates):
    values = {
        name: updates.get(name, getattr(address, name))
        for name in epoch.CounterKeyedOperationalEpochAddress.__annotations__
    }
    values["address_sha256"] = "0" * 64
    values["address_sha256"] = thinning._semantic_digest(
        epoch._without(values, "address_sha256")
    )
    return values


def _stream_values(stream, **updates):
    values = {
        name: updates.get(name, getattr(stream, name))
        for name in epoch.CounterKeyedOperationalEpochStream.__annotations__
    }
    values["stream_sha256"] = "0" * 64
    values["stream_sha256"] = thinning._semantic_digest(
        epoch._without(
            values,
            "certificate",
            "address",
            "initial_state",
            "stream_sha256",
        )
    )
    return values


def _proposal_values(proposal, **updates):
    values = {
        name: updates.get(name, getattr(proposal, name))
        for name in epoch.CounterKeyedOperationalEpochProposal.__annotations__
    }
    values["proposal_sha256"] = "0" * 64
    values["proposal_sha256"] = thinning._semantic_digest(
        epoch._without(
            values,
            "certificate",
            "epoch_stream",
            "iteration",
            "route_evidence",
            "lineage_transition",
            "stream_final_state",
            "proposal_sha256",
        )
    )
    return values


def _terminal_values(terminal, **updates):
    values = {
        name: updates.get(name, getattr(terminal, name))
        for name in epoch.CounterKeyedOperationalEpochTerminal.__annotations__
    }
    values["terminal_sha256"] = "0" * 64
    values["terminal_sha256"] = thinning._semantic_digest(
        epoch._without(
            values,
            "certificate",
            "operational_epoch_stream",
            "checkpoint23_terminal_wait_stream",
            "waiting_draw",
            "stream_final_state",
            "terminal_sha256",
        )
    )
    return values


def _result_values(result, **updates):
    values = {
        name: updates.get(name, getattr(result, name))
        for name in epoch.CounterKeyedOperationalEpochLoopResult.__annotations__
    }
    if "proposals" in updates:
        proposals = values["proposals"]
        values["proposal_sha256s"] = tuple(
            proposal.proposal_sha256 for proposal in proposals
        )
        values["iteration_sha256s"] = tuple(
            proposal.iteration_sha256 for proposal in proposals
        )
        values["route_evidence_sha256s"] = tuple(
            proposal.route_evidence_sha256 for proposal in proposals
        )
        values["lineage_transition_sha256s"] = tuple(
            proposal.lineage_transition_sha256 for proposal in proposals
        )
    values["result_sha256"] = "0" * 64
    values["result_sha256"] = thinning._semantic_digest(epoch._result_payload(values))
    return values


def _construct_address(values):
    return epoch.CounterKeyedOperationalEpochAddress(
        **values,
        _construction_token=epoch._ADDRESS_TOKEN,
    )


def _construct_stream(values):
    return epoch.CounterKeyedOperationalEpochStream(
        **values,
        _construction_token=epoch._STREAM_TOKEN,
    )


def _construct_proposal(values):
    return epoch.CounterKeyedOperationalEpochProposal(
        **values,
        _construction_token=epoch._PROPOSAL_TOKEN,
    )


def _construct_terminal(values):
    return epoch.CounterKeyedOperationalEpochTerminal(
        **values,
        _construction_token=epoch._TERMINAL_TOKEN,
    )


def _construct_result(values):
    return epoch.CounterKeyedOperationalEpochLoopResult(
        **values,
        _construction_token=epoch._RESULT_TOKEN,
    )


def test_certificate_scope_truth_matrix_and_exact_parent_custody(tight_bundle):
    owner = tight_bundle["epoch_owner"]
    certificate = owner.certificate
    for name in (
        "exact_checkpoint23_owner_binding_certified",
        "direct_unhashed_operational_epoch_address_certified",
        "disjoint_checkpoint23_domain_tag_certified",
        "same_runtime_epoch_reconstruction_certified",
        "actual_operational_epoch_consumption_certified",
        "active_wait_route_accept_same_stream_certified",
        "active_epoch_terminal_certified",
        "deterministic_checkpoint23_terminal_wait_certified",
        "deterministic_terminal_before_cap_certified",
        "complete_route_evidence_per_proposal_certified",
        "accepted_state_refresh_certified",
        "rejection_parent_identity_reuse_certified",
        "live_lineage_transition_per_proposal_certified",
        "terminal_exact_lineage_state_reuse_certified",
        "bounded_successful_interval_completion_certified",
        "same_runtime_address_local_replay_certified",
        "no_caller_rng_certified",
        "recorded_upper_counter_limb_preservation_certified",
        "identifier_excluded_from_model_projection_certified",
        "passed",
    ):
        assert getattr(certificate, name) is True
    for name in (
        "checkpoint23_jump_proposal_stream_consumption_certified",
        "checkpoint22_proposal_keyed_execution_certified",
        "checkpoint22_stream_consumption_certified",
        "cross_epoch_sequential_stream_certified",
        "statistical_independence_certified",
        "physical_randomness_certified",
        "global_run_id_uniqueness_certified",
        "duplicate_address_use_prevention_certified",
        "lineage_fork_prevention_certified",
        "exact_categorical_law_certified",
        "exact_integer_law_certified",
        "exact_gaussian_law_certified",
        "analytic_output_law_certified",
        "exact_active_controlled_total_exit_computed",
        "analytic_target_preserved",
        "conditional_posterior_or_doob_target",
        "rounded_stationarity_certified",
        "unconditional_local_completion_certified",
        "unconditional_exact_frozen_jump_law_certified",
        "exact_real_time_poisson_or_ctmc_path",
        "sampler_liveness_certified",
        "occurrence_stream_consumption_certified",
        "initializer_stream_consumption_certified",
        "brownian_stream_consumption_certified",
        "brownian_additive_coupling_certified",
        "continuous_drift_admissible",
        "initializer_admissible",
        "path_admissible",
        "strang_sampler_admissible",
        "full_sampler_admissible",
        "runtime_portable",
        "cryptographic_authentication",
    ):
        assert getattr(certificate, name) is False
    assert owner.contract_owner is tight_bundle["contract_owner"]
    assert owner.checkpoint22_owner is tight_bundle["integration_owner"]
    assert owner.loop_owner is tight_bundle["loop_owner"]
    assert owner.route_evidence_owner is tight_bundle["route_owner"]
    assert owner.thinning_owner is tight_bundle["thinning_owner"]
    assert certificate.checkpoint23_certificate_sha256 == (
        owner.contract_owner.certificate.certificate_sha256
    )


def test_tag6_address_exactness_injectivity_and_domain_separation(tight_bundle):
    owner = tight_bundle["epoch_owner"]
    run_id = 0x0123456789ABCDEF
    step_index = 0x1020304050607080
    stream = owner.make_operational_epoch_stream(run_id, step_index, 7)
    address = stream.address
    snapshot = stream.initial_state
    assert address.domain == epoch.COUNTER_KEY_DOMAIN_OPERATIONAL_EPOCH
    assert address.domain_tag == epoch.COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH == 6
    assert address.occurrence_serial == 0
    assert address.philox_key == snapshot.key == (run_id, 6)
    assert address.philox_counter == snapshot.counter == (0, step_index, 0, 7)
    assert snapshot.buffer == (0, 0, 0, 0)
    assert snapshot.buffer_pos == 4
    assert snapshot.has_uint32 == snapshot.uinteger == 0
    assert stream.buffer_is_zero is stream.uint32_cache_is_zero is True
    assert stream.same_runtime_only is True
    assert owner.validate_operational_epoch_stream(stream) is stream
    assert 6 not in tuple(lineage.COUNTER_KEY_DOMAIN_TAGS.values())

    addresses = tuple(
        epoch._make_address(
            owner.certificate,
            run_id=run,
            step_index=step,
            completed_proposals=completed,
        )
        for run in (0, 1, lineage.MAX_UINT64)
        for step in (0, 2, lineage.MAX_UINT64)
        for completed in (0, 1, 63)
    )
    limbs = tuple((item.philox_key, item.philox_counter) for item in addresses)
    assert len(limbs) == len(set(limbs))
    assert len({item.address_sha256 for item in addresses}) == len(addresses)
    legacy = owner.contract_owner.make_jump_proposal_stream(run_id, step_index, 7)
    terminal = owner.contract_owner.make_terminal_wait_stream(run_id, step_index, 7)
    assert (address.philox_key, address.philox_counter) not in {
        (legacy.address.philox_key, legacy.address.philox_counter),
        (terminal.address.philox_key, terminal.address.philox_counter),
    }


@pytest.mark.parametrize(
    "invalid",
    [True, False, np.int64(1), 1.0, -1, lineage.MAX_UINT64 + 1],
)
def test_tag6_coordinates_are_exact_bounded_uint64(tight_bundle, invalid):
    owner = tight_bundle["epoch_owner"]
    calls = (
        lambda: owner.make_operational_epoch_stream(invalid, 2, 3),
        lambda: owner.make_operational_epoch_stream(1, invalid, 3),
        lambda: owner.make_operational_epoch_stream(1, 2, invalid),
    )
    for call in calls:
        with pytest.raises((TypeError, ValueError)):
            call()
    with pytest.raises((TypeError, ValueError)):
        owner.make_operational_epoch_stream(1, 2, 64)


def test_full_advertised_stream_prefix_replays_without_address_carry(tight_bundle):
    owner = tight_bundle["epoch_owner"]
    first = owner.make_operational_epoch_stream(31, 37, 41)
    second = owner.make_operational_epoch_stream(31, 37, 41)
    assert first is not second
    assert first.stream_sha256 == second.stream_sha256
    word_count = epoch.COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_RECORDED_RAW64_WORDS
    first_rng = owner.reconstruct_operational_epoch_stream(first)
    replay_rng = owner.reconstruct_operational_epoch_stream(second)
    direct_rng = _direct_generator(
        run_id=31,
        step_index=37,
        completed_proposals=41,
    )
    first_prefix = first_rng.bit_generator.random_raw(word_count)
    assert np.array_equal(first_prefix, replay_rng.bit_generator.random_raw(word_count))
    assert np.array_equal(first_prefix, direct_rng.bit_generator.random_raw(word_count))
    final = route_evidence._capture_philox_state(first_rng)
    assert final.key == first.initial_state.key
    assert final.counter[1:] == first.initial_state.counter[1:]
    epoch._require_no_recorded_counter_carry(first.initial_state, final)


def test_redigested_address_and_stream_forgeries_refuse(tight_bundle):
    owner = tight_bundle["epoch_owner"]
    stream = owner.make_operational_epoch_stream(3, 5, 7)
    address = stream.address
    address_attacks = (
        {"run_id": 4},
        {"step_index": 6},
        {"completed_proposals": 8},
        {"occurrence_serial": 1},
        {"domain": lineage.COUNTER_KEY_DOMAIN_TERMINAL_WAIT},
        {"domain_tag": lineage.COUNTER_KEY_DOMAIN_TAG_TERMINAL_WAIT},
        {"domain_tag": 6.0},
        {"domain_tag": np.int64(6)},
        {"domain_tag": True},
        {"domain_tag": False},
        {"philox_key": (4, 6)},
        {"philox_counter": (1, 5, 0, 7)},
    )
    for updates in address_attacks:
        with pytest.raises((TypeError, ValueError)):
            _construct_address(_address_values(address, **updates))

    other = owner.make_operational_epoch_stream(3, 5, 8)
    advanced = checkpoint23_tests._advanced_snapshot(stream.initial_state)
    stream_attacks = (
        {
            "address": other.address,
            "address_sha256": other.address_sha256,
        },
        {
            "initial_state": advanced,
            "initial_snapshot_sha256": advanced.snapshot_sha256,
            "initial_state_sha256": advanced.state_sha256,
        },
        {"buffer_is_zero": False},
        {"uint32_cache_is_zero": False},
        {"same_runtime_only": False},
    )
    for updates in stream_attacks:
        with pytest.raises((TypeError, ValueError)):
            _construct_stream(_stream_values(stream, **updates))


def test_active_proposals_terminal_and_same_stream_chains(tight_result_case):
    bundle, intensity, envelope, initial_lineage, result = tight_result_case
    assert result.terminal.active_terminal is True
    assert result.terminal.deterministic_terminal is False
    assert result.terminal.operational_epoch_stream is not None
    assert result.terminal.checkpoint23_terminal_wait_stream is None
    assert result.terminal.waiting_draw.raw_words_consumed > 0
    assert result.terminal.waiting_draw.candidate_due is False
    assert result.terminal.completed_proposals == len(result.proposals)
    assert result.terminal.operational_epoch_stream.address.completed_proposals == 2
    assert result.operational_epoch_stream_count == 3
    assert result.checkpoint23_terminal_wait_invocation_count == 0
    assert result.checkpoint23_jump_proposal_stream_count == 0
    assert result.actual_operational_epoch_consumption is True
    assert result.checkpoint23_jump_proposal_streams_consumed is False
    assert result.checkpoint22_execution_was_proposal_keyed is False
    assert result.all_within_result_epoch_addresses_unique is True
    assert result.terminal_reused_exact_lineage_state is True
    assert (
        result.final_lineage_state is result.proposals[-1].lineage_transition.post_state
    )
    assert result.identifiers_absent_from_model_projection is True

    current_intensity = intensity
    current_envelope = envelope
    current_lineage = initial_lineage
    for index, proposal in enumerate(result.proposals):
        iteration = proposal.iteration
        evidence = proposal.route_evidence
        transition = proposal.lineage_transition
        assert proposal.proposal_index == index
        assert proposal.epoch_stream.address.completed_proposals == index
        assert iteration.waiting_draw.candidate_due is True
        assert iteration.route_draw.candidate is not None
        assert iteration.pre_intensity is current_intensity
        assert iteration.pre_envelope is current_envelope
        assert transition.pre_state is current_lineage
        assert evidence.route_draw is iteration.route_draw
        assert transition.parent_iteration is iteration
        assert transition.parent_route_evidence is evidence
        assert proposal.epoch_stream.initial_state_sha256 == (
            iteration.waiting_draw.rng_state_before_sha256
        )
        assert iteration.waiting_draw.rng_state_after_sha256 == (
            evidence.rng_state_before_sha256
        )
        assert evidence.rng_state_after_sha256 == (
            iteration.decision.rng_state_before_sha256
        )
        assert iteration.decision.rng_state_after_sha256 == (
            proposal.stream_final_state_sha256
        )
        assert proposal.same_stream_wait_route_accept is True
        assert proposal.operational_epoch_stream_consumed is True
        assert proposal.recorded_upper_counter_limbs_unchanged is True
        assert iteration.post_intensity is not current_intensity
        assert iteration.post_envelope is not current_envelope
        current_intensity = iteration.post_intensity
        current_envelope = iteration.post_envelope
        current_lineage = transition.post_state

    assert "self.validate_result(" in inspect.getsource(bundle["epoch_owner"].run)


def test_rejection_reuses_exact_parent_and_lineage(ordinary_result_case):
    _, intensity, envelope, initial_lineage, proposal, _ = ordinary_result_case
    transition = proposal.lineage_transition
    assert proposal.accepted is False
    assert proposal.iteration.post_intensity is intensity
    assert proposal.iteration.post_envelope is envelope
    assert transition.pre_state is initial_lineage
    assert transition.post_state is initial_lineage
    assert transition.rejection_reused_exact_state is True
    assert transition.created_occurrence is None
    assert transition.destroyed_identifier is None


def test_a_to_b_to_a_never_resurrects_lineage(tight_result_case):
    bundle, _, _, initial_lineage, result = tight_result_case
    certificate = bundle["contract_owner"].certificate
    intermediate_lineage = result.proposals[0].lineage_transition.post_state
    assert intermediate_lineage.model_configuration != (
        initial_lineage.model_configuration
    )
    replaced = intermediate_lineage.occurrences[0].identifier
    recreated = lineage._make_identifier(
        certificate,
        run_id=intermediate_lineage.run_id,
        serial=intermediate_lineage.next_serial,
        origin_kind="replacement",
        origin_step_index=7,
        origin_proposal_index=0,
    )
    recreated_occurrence = lineage._make_occurrence(
        certificate,
        recreated,
        TransformedEvent(0),
    )
    returned = lineage._make_state(
        certificate,
        run_id=intermediate_lineage.run_id,
        initialization_index=intermediate_lineage.initialization_index,
        occurrences=(recreated_occurrence,),
        retired_identifiers=intermediate_lineage.retired_identifiers + (replaced,),
        next_serial=recreated.serial + 1,
    )
    assert returned.model_configuration == initial_lineage.model_configuration
    original_identifiers = tuple(
        occurrence.identifier for occurrence in initial_lineage.occurrences
    )
    final_identifiers = tuple(
        occurrence.identifier for occurrence in returned.occurrences
    )
    assert not set(original_identifiers).intersection(final_identifiers)
    assert all(
        identifier in returned.retired_identifiers
        for identifier in original_identifiers
    )
    assert all(
        occurrence.identifier in returned.retired_identifiers
        for occurrence in intermediate_lineage.occurrences
    )
    assert min(identifier.serial for identifier in final_identifiers) >= (
        initial_lineage.next_serial
    )
    assert returned.next_serial > initial_lineage.next_serial
    resurrected = lineage._make_occurrence(
        certificate,
        original_identifiers[0],
        TransformedEvent(0),
    )
    with pytest.raises(ValueError, match="live and retired lineage serials"):
        lineage._make_state(
            certificate,
            run_id=intermediate_lineage.run_id,
            initialization_index=intermediate_lineage.initialization_index,
            occurrences=(resurrected,),
            retired_identifiers=returned.retired_identifiers,
            next_serial=returned.next_serial,
        )


def test_deterministic_tag2_zero_word_terminals_and_precedence(
    deterministic_terminal_cases,
):
    zero_duration = deterministic_terminal_cases["zero_duration"][3]
    reference_zero = deterministic_terminal_cases["reference_zero"][3]
    both = deterministic_terminal_cases["both"][3]
    for result in (zero_duration, reference_zero, both):
        terminal = result.terminal
        stream = terminal.checkpoint23_terminal_wait_stream
        assert result.proposals == ()
        assert terminal.deterministic_terminal is True
        assert terminal.active_terminal is False
        assert terminal.operational_epoch_stream is None
        assert stream is not None
        assert stream.address.domain == lineage.COUNTER_KEY_DOMAIN_TERMINAL_WAIT
        assert stream.address.domain_tag == lineage.COUNTER_KEY_DOMAIN_TAG_TERMINAL_WAIT
        assert stream.address.proposal_index == 0
        assert terminal.waiting_draw.raw_words == ()
        assert terminal.waiting_draw.raw_words_consumed == 0
        assert terminal.stream_final_state_sha256 == stream.initial_state_sha256
        assert terminal.checkpoint23_terminal_wait_invoked is True
        assert terminal.checkpoint23_terminal_wait_raw_words_consumed is False
        assert result.checkpoint23_terminal_wait_invocation_count == 1
        assert result.operational_epoch_stream_count == 0
        assert result.recorded_raw64_word_count == 0
        assert result.actual_operational_epoch_consumption is False
        assert result.final_lineage_state is result.initial_lineage_state

    assert zero_duration.reference_intensity_zero is False
    assert zero_duration.terminal.zero_duration is True
    assert zero_duration.stop_reason == "right_endpoint_exhausted"
    assert reference_zero.reference_intensity_zero is True
    assert reference_zero.terminal.zero_duration is False
    assert reference_zero.stop_reason == "reference_intensity_zero"
    assert both.reference_intensity_zero is True
    assert both.terminal.zero_duration is True
    assert both.stop_reason == "reference_intensity_zero"


def test_same_digest_alien_waiting_owner_splice_refuses(
    tight_bundle,
    deterministic_terminal_cases,
):
    intensity, envelope, initial_lineage, result = deterministic_terminal_cases[
        "zero_duration"
    ]
    terminal = result.terminal
    stream = terminal.checkpoint23_terminal_wait_stream
    assert stream is not None
    alien_thinning = thinning.certify_plugin_bridge_operational_thinning(
        tight_bundle["rate_owner"],
        thinning_policy=thinning.PLUGIN_BRIDGE_OPERATIONAL_THINNING_POLICY,
        thinning_role_sha256=(
            tight_bundle["thinning_owner"].certificate.thinning_role_sha256
        ),
    )
    generator = tight_bundle["contract_owner"].reconstruct_stream(stream)
    alien_waiting = alien_thinning.draw_waiting_time(
        intensity,
        envelope,
        clock_start=result.final_clock_cursor,
        right_endpoint=result.right_endpoint,
        rng=generator,
    )
    alien_final = route_evidence._capture_philox_state(generator)
    assert alien_waiting.certificate is not terminal.waiting_draw.certificate
    assert alien_waiting.certificate_sha256 == (
        terminal.waiting_draw.certificate_sha256
    )
    assert alien_waiting.waiting_draw_sha256 == terminal.waiting_draw_sha256
    forged_terminal = _construct_terminal(
        _terminal_values(
            terminal,
            waiting_draw=alien_waiting,
            waiting_draw_sha256=alien_waiting.waiting_draw_sha256,
            stream_final_state=alien_final,
            stream_final_snapshot_sha256=alien_final.snapshot_sha256,
            stream_final_state_sha256=alien_final.state_sha256,
        )
    )
    forged_result = _construct_result(
        _result_values(
            result,
            terminal=forged_terminal,
            terminal_sha256=forged_terminal.terminal_sha256,
        )
    )
    owner = tight_bundle["epoch_owner"]
    with pytest.raises((TypeError, ValueError)):
        owner.validate_terminal(
            forged_terminal,
            intensity,
            envelope,
            clock_start=result.final_clock_cursor,
            right_endpoint=result.right_endpoint,
        )
    with pytest.raises((TypeError, ValueError)):
        owner.validate_result(
            forged_result,
            intensity,
            envelope,
            initial_lineage,
            run_id=result.run_id,
            step_index=result.step_index,
            clock_start=result.clock_start,
            right_endpoint=result.right_endpoint,
            proposal_budget=result.proposal_budget,
            base_context=BASE_CONTEXT,
            residual_context=RESIDUAL_CONTEXT,
        )


def test_active_cap_refuses_before_any_stream_factory(tight_bundle, monkeypatch):
    intensity, envelope = _parents(tight_bundle)
    initial_lineage = _bootstrap(tight_bundle, intensity, run_id=81)

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("proposal cap reached a stream factory")

    monkeypatch.setattr(
        epoch.CounterKeyedOperationalEpochLoop,
        "make_operational_epoch_stream",
        forbidden,
    )
    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_terminal_wait_stream",
        forbidden,
    )
    with pytest.raises(
        epoch.PluginBridgeCounterKeyedOperationalEpochLoopError,
        match="proposal budget",
    ):
        _run(
            tight_bundle,
            intensity,
            envelope,
            initial_lineage,
            run_id=81,
            step_index=8,
            endpoint=1.0,
            budget=0,
        )


def test_checkpoint23_tag1_is_never_called_and_global_rng_is_unchanged(
    tight_bundle,
    monkeypatch,
):
    owner = tight_bundle["epoch_owner"]
    intensity, envelope = _parents(tight_bundle)
    initial_lineage = _bootstrap(tight_bundle, intensity, run_id=83)

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("checkpoint-23 jump-proposal stream was called")

    monkeypatch.setattr(
        lineage.CounterKeyedLineageContractOwner,
        "make_jump_proposal_stream",
        forbidden,
    )
    original = np.random.get_state()
    try:
        np.random.seed(2401)
        before = np.random.get_state()
        result = _run(
            tight_bundle,
            intensity,
            envelope,
            initial_lineage,
            run_id=83,
            step_index=9,
            endpoint=math.nextafter(0.0, math.inf),
            budget=1,
        )
        after = np.random.get_state()
        assert before[0] == after[0]
        assert np.array_equal(before[1], after[1])
        assert before[2:] == after[2:]
    finally:
        np.random.set_state(original)
    assert result.proposals == ()
    assert result.terminal.active_terminal is True
    assert result.checkpoint23_jump_proposal_stream_count == 0
    assert result.checkpoint23_jump_proposal_streams_consumed is False
    assert result.no_caller_rng is True
    assert "rng" not in inspect.signature(owner.run).parameters
    with pytest.raises(TypeError):
        owner.run(
            intensity,
            envelope,
            initial_lineage,
            run_id=83,
            step_index=9,
            clock_start=0.0,
            right_endpoint=0.0,
            proposal_budget=0,
            base_context=BASE_CONTEXT,
            residual_context=RESIDUAL_CONTEXT,
            rng=np.random.default_rng(1),
        )


def test_recorded_upper_counter_carry_is_fail_closed(tight_bundle, monkeypatch):
    intensity, envelope = _parents(tight_bundle)
    initial_lineage = _bootstrap(tight_bundle, intensity, run_id=89)
    endpoint = _one_proposal_endpoint(
        envelope,
        run_id=89,
        step_index=10,
    )
    original = ProcessValidReferenceJumpComposer.sample_candidate_from_intensity

    def carrying(self, candidate_intensity, *, rng):
        candidate = original(self, candidate_intensity, rng=rng)
        rng.bit_generator.advance(1 << 64)
        return candidate

    monkeypatch.setattr(
        ProcessValidReferenceJumpComposer,
        "sample_candidate_from_intensity",
        carrying,
    )
    with pytest.raises(
        epoch.PluginBridgeCounterKeyedOperationalEpochLoopError,
        match="carried into an address counter limb",
    ):
        _run(
            tight_bundle,
            intensity,
            envelope,
            initial_lineage,
            run_id=89,
            step_index=10,
            endpoint=endpoint,
            budget=2,
        )


def test_redigested_proposal_route_lineage_and_owner_splices_refuse(
    tight_result_case,
    ordinary_result_case,
):
    tight_bundle, _, _, _, tight_result = tight_result_case
    first, second = tight_result.proposals
    rejected = ordinary_result_case[4]
    alien_owner = epoch.certify_plugin_bridge_counter_keyed_operational_epoch_loop(
        tight_bundle["contract_owner"],
        epoch_policy=epoch.PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY,
        epoch_role_sha256="8" * 64,
    )
    alien_stream = alien_owner.make_operational_epoch_stream(
        first.run_id,
        first.step_index,
        first.proposal_index,
    )
    forged_base_context = checkpoint23_tests._forged_iteration(
        first.iteration,
        base_context_sha256=first.iteration.residual_context_sha256,
    )
    forged_residual_context = checkpoint23_tests._forged_iteration(
        first.iteration,
        residual_context_sha256=first.iteration.base_context_sha256,
    )
    attacks = (
        {"run_id": first.run_id + 1},
        {"step_index": first.step_index + 1},
        {"proposal_index": 1},
        {
            "epoch_stream": second.epoch_stream,
            "epoch_stream_sha256": second.epoch_stream_sha256,
            "epoch_address_sha256": second.epoch_address_sha256,
        },
        {
            "epoch_stream": alien_stream,
            "epoch_stream_sha256": alien_stream.stream_sha256,
            "epoch_address_sha256": alien_stream.address_sha256,
        },
        {
            "route_evidence": second.route_evidence,
            "route_evidence_sha256": second.route_evidence_sha256,
        },
        {
            "route_evidence": rejected.route_evidence,
            "route_evidence_sha256": rejected.route_evidence_sha256,
        },
        {
            "lineage_transition": second.lineage_transition,
            "lineage_transition_sha256": second.lineage_transition_sha256,
            "pre_lineage_state_sha256": (second.lineage_transition.pre_state_sha256),
            "post_lineage_state_sha256": (second.lineage_transition.post_state_sha256),
        },
        {
            "iteration": forged_base_context,
            "iteration_sha256": forged_base_context.iteration_sha256,
        },
        {
            "iteration": forged_residual_context,
            "iteration_sha256": forged_residual_context.iteration_sha256,
        },
        {"accepted": False},
        {"same_stream_wait_route_accept": False},
        {"operational_epoch_stream_consumed": False},
        {"recorded_upper_counter_limbs_unchanged": False},
        {"stream_final_state_sha256": "0" * 64},
    )
    for updates in attacks:
        with pytest.raises((TypeError, ValueError)):
            _construct_proposal(_proposal_values(first, **updates))


def test_same_digest_alien_lineage_owner_splice_refuses(ordinary_result_case):
    (
        bundle,
        intensity,
        envelope,
        initial_lineage,
        proposal,
        result,
    ) = ordinary_result_case
    role = bundle["contract_owner"].certificate.contract_role_sha256
    alien_contract = checkpoint23_tests._certify_owner(bundle, role=role)
    alien_transition = lineage._make_transition(
        alien_contract.certificate,
        proposal.iteration,
        proposal.route_evidence,
        initial_lineage,
        run_id=proposal.run_id,
        step_index=proposal.step_index,
    )
    assert alien_transition.certificate is not proposal.lineage_transition.certificate
    assert alien_transition.certificate_sha256 == (
        proposal.lineage_transition.certificate_sha256
    )
    assert alien_transition.transition_sha256 == (proposal.lineage_transition_sha256)
    forged_proposal = _construct_proposal(
        _proposal_values(
            proposal,
            lineage_transition=alien_transition,
            lineage_transition_sha256=alien_transition.transition_sha256,
            pre_lineage_state_sha256=alien_transition.pre_state_sha256,
            post_lineage_state_sha256=alien_transition.post_state_sha256,
        )
    )
    forged_result = _construct_result(
        _result_values(result, proposals=(forged_proposal,))
    )
    owner = bundle["epoch_owner"]
    with pytest.raises((TypeError, ValueError)):
        owner.validate_proposal(
            forged_proposal,
            intensity,
            envelope,
            initial_lineage,
            right_endpoint=result.right_endpoint,
            base_context=BASE_CONTEXT,
            residual_context=RESIDUAL_CONTEXT,
        )
    with pytest.raises((TypeError, ValueError)):
        owner.validate_result(
            forged_result,
            intensity,
            envelope,
            initial_lineage,
            run_id=result.run_id,
            step_index=result.step_index,
            clock_start=result.clock_start,
            right_endpoint=result.right_endpoint,
            proposal_budget=result.proposal_budget,
            base_context=BASE_CONTEXT,
            residual_context=RESIDUAL_CONTEXT,
        )


def test_redigested_terminal_address_mode_and_stream_splices_refuse(
    tight_result_case,
    deterministic_terminal_cases,
):
    tight_bundle = tight_result_case[0]
    active = tight_result_case[4].terminal
    deterministic = deterministic_terminal_cases["zero_duration"][3].terminal
    first_stream = tight_result_case[4].proposals[0].epoch_stream
    alien_owner = epoch.certify_plugin_bridge_counter_keyed_operational_epoch_loop(
        tight_bundle["contract_owner"],
        epoch_policy=epoch.PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY,
        epoch_role_sha256="a" * 64,
    )
    alien_epoch_stream = alien_owner.make_operational_epoch_stream(
        active.run_id,
        active.step_index,
        active.completed_proposals,
    )
    alien_contract = checkpoint23_tests._certify_owner(
        tight_bundle,
        role="b" * 64,
    )
    alien_terminal_stream = alien_contract.make_terminal_wait_stream(
        deterministic.run_id,
        deterministic.step_index,
        deterministic.completed_proposals,
    )
    attacks = (
        {"run_id": active.run_id + 1},
        {"step_index": active.step_index + 1},
        {"completed_proposals": active.completed_proposals - 1},
        {
            "operational_epoch_stream": first_stream,
            "operational_epoch_stream_sha256": first_stream.stream_sha256,
        },
        {
            "operational_epoch_stream": alien_epoch_stream,
            "operational_epoch_stream_sha256": alien_epoch_stream.stream_sha256,
        },
        {
            "checkpoint23_terminal_wait_stream": (
                deterministic.checkpoint23_terminal_wait_stream
            ),
            "checkpoint23_terminal_wait_stream_sha256": (
                deterministic.checkpoint23_terminal_wait_stream_sha256
            ),
        },
        {"terminal_mode": epoch._TERMINAL_DETERMINISTIC_WAIT},
        {"active_terminal": False},
        {"operational_epoch_stream_consumed": False},
        {"no_route_or_acceptance": False},
        {"recorded_upper_counter_limbs_unchanged": False},
    )
    for updates in attacks:
        with pytest.raises((TypeError, ValueError)):
            _construct_terminal(_terminal_values(active, **updates))

    deterministic_attack = {
        "checkpoint23_terminal_wait_stream": alien_terminal_stream,
        "checkpoint23_terminal_wait_stream_sha256": (
            alien_terminal_stream.stream_sha256
        ),
    }
    with pytest.raises((TypeError, ValueError)):
        _construct_terminal(_terminal_values(deterministic, **deterministic_attack))


def test_result_omission_duplication_reorder_and_cross_owner_splices_refuse(
    tight_result_case,
    ordinary_result_case,
    deterministic_terminal_cases,
):
    result = tight_result_case[4]
    first, second = result.proposals
    rejected = ordinary_result_case[4]
    deterministic = deterministic_terminal_cases["zero_duration"][3].terminal
    equal_final_configuration = tuple(event for event in result.final_configuration)
    assert equal_final_configuration is not result.final_configuration
    assert equal_final_configuration == result.final_configuration
    forged_final_event = _forged_record(
        result.final_configuration[0],
        coordinates=(0.0,) * (epoch.MAX_TRANSFORMED_COORDINATE_DIMENSION + 1),
    )
    forged_final_configuration = (
        forged_final_event,
        *result.final_configuration[1:],
    )
    negative_zero_final_configuration = (
        _forged_record(result.final_configuration[0], coordinates=(-0.0,)),
        *result.final_configuration[1:],
    )
    infinite_final_configuration = (
        _forged_record(result.final_configuration[0], coordinates=(math.inf,)),
        *result.final_configuration[1:],
    )
    initial_lineage = result.initial_lineage_state
    original_event = initial_lineage.model_configuration[0]
    aliased_event = TransformedEvent(
        original_event.event_type,
        original_event.coordinates,
    )
    assert aliased_event is not original_event and aliased_event == original_event
    aliased_projection = (
        aliased_event,
        *initial_lineage.model_configuration[1:],
    )
    aliased_lineage_values = checkpoint23_tests._state_values(
        initial_lineage,
        model_configuration=aliased_projection,
    )
    aliased_lineage = lineage.OperationalLineageState(
        **aliased_lineage_values,
        _construction_token=lineage._STATE_TOKEN,
    )
    original_occurrence = initial_lineage.occurrences[0]
    aliased_occurrence_values = checkpoint23_tests._occurrence_values(
        original_occurrence,
        event=aliased_event,
    )
    aliased_occurrence = lineage.OperationalLineagedOccurrence(
        **aliased_occurrence_values,
        _construction_token=lineage._OCCURRENCE_TOKEN,
    )
    fully_aliased_lineage_values = checkpoint23_tests._state_values(
        initial_lineage,
        occurrences=(aliased_occurrence,),
        occurrence_sha256s=(aliased_occurrence.occurrence_sha256,),
        model_configuration=aliased_projection,
    )
    fully_aliased_lineage = lineage.OperationalLineageState(
        **fully_aliased_lineage_values,
        _construction_token=lineage._STATE_TOKEN,
    )
    context_attacks = tuple(
        {
            field: context,
            "%s_sha256"
            % field: epoch._loop._context_sha256(
                context,
                role=role,
            ),
        }
        for field, role in (
            ("base_context", "base"),
            ("residual_context", "residual"),
        )
        for context in ((0,), (True,), (-0.0,))
    )
    attacks = (
        {"proposals": ()},
        {"proposals": (first, first)},
        {"proposals": (second, first)},
        {"proposals": (first, rejected)},
        {"proposals": (first,)},
        {"terminal": deterministic, "terminal_sha256": deterministic.terminal_sha256},
        {"run_id": result.run_id + 1},
        {"step_index": result.step_index + 1},
        {"proposal_budget": 1},
        {"final_lineage_state": result.initial_lineage_state},
        {"initial_lineage_state": aliased_lineage},
        {"initial_lineage_state": fully_aliased_lineage},
        {"final_configuration": equal_final_configuration},
        {"final_configuration": forged_final_configuration},
        {"final_configuration": negative_zero_final_configuration},
        *context_attacks,
    )
    for updates in attacks:
        with pytest.raises((TypeError, ValueError)):
            _construct_result(_result_values(result, **updates))

    infinite_values = {
        name: getattr(result, name)
        for name in epoch.CounterKeyedOperationalEpochLoopResult.__annotations__
    }
    infinite_values["final_configuration"] = infinite_final_configuration
    with pytest.raises((TypeError, ValueError)):
        _construct_result(infinite_values)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("proposal_count", 0),
        ("accepted_count", 0),
        ("rejected_count", 1),
        ("created_lineage_count", 0),
        ("destroyed_lineage_count", 0),
        ("operational_epoch_stream_count", 0),
        ("checkpoint23_terminal_wait_invocation_count", 1),
        ("checkpoint23_jump_proposal_stream_count", 1),
        ("recorded_raw64_word_count", 0),
        ("all_within_result_epoch_addresses_unique", False),
        ("actual_operational_epoch_consumption", False),
        ("checkpoint23_jump_proposal_streams_consumed", True),
        ("checkpoint22_execution_was_proposal_keyed", True),
        ("terminal_reused_exact_lineage_state", 1),
        ("identifiers_absent_from_model_projection", False),
        ("no_caller_rng", False),
        ("terminal_sha256", "0" * 64),
    ),
)
def test_redigested_result_counts_flags_and_digests_refuse(
    tight_result_case,
    field,
    replacement,
):
    result = tight_result_case[4]
    with pytest.raises((TypeError, ValueError)):
        _construct_result(_result_values(result, **{field: replacement}))


def test_wrong_validation_inputs_and_distinct_owner_refuse(tight_result_case):
    bundle, intensity, envelope, initial_lineage, result = tight_result_case
    owner = bundle["epoch_owner"]
    clone = lineage._make_state(
        bundle["contract_owner"].certificate,
        run_id=initial_lineage.run_id,
        initialization_index=initial_lineage.initialization_index,
        occurrences=initial_lineage.occurrences,
        retired_identifiers=initial_lineage.retired_identifiers,
        next_serial=initial_lineage.next_serial,
    )
    assert clone is not initial_lineage
    assert clone.state_sha256 == initial_lineage.state_sha256
    with pytest.raises((TypeError, ValueError)):
        owner.validate_result(
            result,
            intensity,
            envelope,
            clone,
            run_id=result.run_id,
            step_index=result.step_index,
            clock_start=result.clock_start,
            right_endpoint=result.right_endpoint,
            proposal_budget=result.proposal_budget,
            base_context=BASE_CONTEXT,
            residual_context=RESIDUAL_CONTEXT,
        )
    with pytest.raises((TypeError, ValueError)):
        owner.validate_result(
            result,
            intensity,
            envelope,
            initial_lineage,
            run_id=result.run_id + 1,
            step_index=result.step_index,
            clock_start=result.clock_start,
            right_endpoint=result.right_endpoint,
            proposal_budget=result.proposal_budget,
            base_context=BASE_CONTEXT,
            residual_context=RESIDUAL_CONTEXT,
        )
    alien = epoch.certify_plugin_bridge_counter_keyed_operational_epoch_loop(
        bundle["contract_owner"],
        epoch_policy=epoch.PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY,
        epoch_role_sha256="9" * 64,
    )
    with pytest.raises((TypeError, ValueError)):
        alien.validate_result(
            result,
            intensity,
            envelope,
            initial_lineage,
            run_id=result.run_id,
            step_index=result.step_index,
            clock_start=result.clock_start,
            right_endpoint=result.right_endpoint,
            proposal_budget=result.proposal_budget,
            base_context=BASE_CONTEXT,
            residual_context=RESIDUAL_CONTEXT,
        )


def test_owner_replay_refuses_stale_nested_child_mutations(tight_result_case):
    bundle, intensity, envelope, initial_lineage, result = tight_result_case
    first, second = result.proposals
    iteration = first.iteration
    stale_children = (
        (
            "waiting_draw",
            _forged_record(
                iteration.waiting_draw,
                decimal_precision_used=(
                    iteration.waiting_draw.decimal_precision_used + 1
                ),
            ),
        ),
        (
            "potential_evaluation",
            _forged_record(
                iteration.potential_evaluation,
                combined_log_increment=(
                    iteration.potential_evaluation.combined_log_increment + 1.0
                ),
            ),
        ),
        (
            "rate_evaluation",
            _forged_record(
                iteration.rate_evaluation,
                decimal_precision_used=(
                    iteration.rate_evaluation.decimal_precision_used + 1
                ),
            ),
        ),
    )
    hostile_results = []
    for field, child in stale_children:
        stale_iteration = _forged_record(iteration, **{field: child})
        stale_proposal = _forged_record(first, iteration=stale_iteration)
        hostile_results.append(
            _forged_record(result, proposals=(stale_proposal, second))
        )
    stale_evidence = _forged_record(
        first.route_evidence,
        pre_route_snapshot_sha256="0" * 64,
    )
    stale_proposal = _forged_record(first, route_evidence=stale_evidence)
    hostile_results.append(_forged_record(result, proposals=(stale_proposal, second)))

    owner = bundle["epoch_owner"]
    for hostile in hostile_results:
        with pytest.raises((TypeError, ValueError)):
            owner.validate_result(
                hostile,
                intensity,
                envelope,
                initial_lineage,
                run_id=result.run_id,
                step_index=result.step_index,
                clock_start=result.clock_start,
                right_endpoint=result.right_endpoint,
                proposal_budget=result.proposal_budget,
                base_context=BASE_CONTEXT,
                residual_context=RESIDUAL_CONTEXT,
            )


def test_resource_preflights_refuse_before_nested_traversal(
    tight_result_case,
    monkeypatch,
):
    bundle, intensity, envelope, initial_lineage, result = tight_result_case
    proposal = result.proposals[0]
    oversized_waiting = _forged_record(
        proposal.iteration.waiting_draw,
        raw_words=(0,) * (thinning.OPERATIONAL_THINNING_MAX_WAITING_RAW64_WORDS + 1),
    )
    oversized_iteration = _forged_record(
        proposal.iteration,
        waiting_draw=oversized_waiting,
    )
    oversized_proposal = _forged_record(proposal, iteration=oversized_iteration)
    with pytest.raises(ValueError, match="resource bound"):
        epoch._validate_proposal_record(oversized_proposal)

    route = proposal.iteration.route_draw
    candidate = route.candidate
    route_proposal = candidate.proposal
    source_event = route_proposal.source_event
    assert source_event is not None
    hostile_coordinates = (
        [0.0],
        (0.0,) * (epoch.MAX_TRANSFORMED_COORDINATE_DIMENSION + 1),
    )
    for coordinates in hostile_coordinates:
        hostile_event = _forged_record(source_event, coordinates=coordinates)
        hostile_route_proposal = _forged_record(
            route_proposal,
            source_event=hostile_event,
        )
        hostile_candidate = _forged_record(
            candidate,
            proposal=hostile_route_proposal,
        )
        hostile_route = _forged_record(route, candidate=hostile_candidate)
        hostile_iteration = _forged_record(
            proposal.iteration,
            route_draw=hostile_route,
        )
        with pytest.raises((TypeError, ValueError), match="coordinates"):
            epoch._preflight_iteration_resources(hostile_iteration)

    class HostileIndex:
        def __str__(self):
            raise AssertionError("preflight stringified a hostile source index")

    factorization = candidate.factorization
    hostile_candidate_shells = []
    for source_index in (HostileIndex(), 1 << 100_000):
        hostile_proposal = _forged_record(
            route_proposal,
            source_occurrence_index=source_index,
        )
        hostile_candidate_shells.append(
            _forged_record(candidate, proposal=hostile_proposal)
        )
    hostile_factor = _forged_record(
        factorization,
        source_event_multiplicity=1 << 100_000,
    )
    hostile_candidate_shells.append(
        _forged_record(candidate, factorization=hostile_factor)
    )
    hostile_rates = _forged_record(
        route_proposal.base_rates,
        birth=np.float64(route_proposal.base_rates.birth),
    )
    hostile_proposal = _forged_record(route_proposal, base_rates=hostile_rates)
    hostile_candidate_shells.append(
        _forged_record(candidate, proposal=hostile_proposal)
    )
    hostile_factor = _forged_record(
        factorization,
        family_rate=np.float64(factorization.family_rate),
    )
    hostile_candidate_shells.extend(
        (
            _forged_record(candidate, factorization=hostile_factor),
            _forged_record(candidate, schema_version="x" * 100_000),
            _forged_record(candidate, contract_scope="x" * 100_000),
        )
    )
    for hostile_candidate in hostile_candidate_shells:
        hostile_route = _forged_record(route, candidate=hostile_candidate)
        hostile_iteration = _forged_record(
            proposal.iteration,
            route_draw=hostile_route,
        )
        with pytest.raises((TypeError, ValueError)):
            epoch._preflight_iteration_resources(hostile_iteration)

    oversized_result = _forged_record(
        result,
        proposals=(proposal,)
        * (epoch.COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS + 1),
    )

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("resource preflight entered nested result validation")

    monkeypatch.setattr(epoch, "_validate_result_record", forbidden)
    with pytest.raises(ValueError, match="resource bound"):
        bundle["epoch_owner"].validate_result(
            oversized_result,
            intensity,
            envelope,
            initial_lineage,
            run_id=result.run_id,
            step_index=result.step_index,
            clock_start=result.clock_start,
            right_endpoint=result.right_endpoint,
            proposal_budget=result.proposal_budget,
            base_context=BASE_CONTEXT,
            residual_context=RESIDUAL_CONTEXT,
        )

    oversized_lineage = _forged_record(
        initial_lineage,
        occurrences=(initial_lineage.occurrences[0],)
        * (lineage.MAX_CONFIGURATION_CARDINALITY + 1),
    )
    with pytest.raises(ValueError, match="live occurrences exceed"):
        epoch._preflight_lineage_state_resources(
            oversized_lineage,
            name="hostile lineage",
        )


def test_factory_require_validator_and_owner_sealing(tight_bundle):
    owner = tight_bundle["epoch_owner"]
    contract_owner = tight_bundle["contract_owner"]
    assert (
        epoch.require_matching_plugin_bridge_counter_keyed_operational_epoch_loop(
            contract_owner,
            owner,
            epoch_policy=(
                epoch.PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY
            ),
            epoch_role_sha256=EPOCH_ROLE,
        )
        is owner
    )
    assert (
        epoch.validate_plugin_bridge_counter_keyed_operational_epoch_loop_certificate(
            contract_owner,
            owner,
            epoch_policy=(
                epoch.PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY
            ),
            epoch_role_sha256=EPOCH_ROLE,
        )
        is owner.certificate
    )
    for updates in (
        {"epoch_policy": "unsupported"},
        {"epoch_role_sha256": "1" * 64},
    ):
        arguments = {
            "epoch_policy": (
                epoch.PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY
            ),
            "epoch_role_sha256": EPOCH_ROLE,
        }
        arguments.update(updates)
        with pytest.raises((TypeError, ValueError)):
            epoch.require_matching_plugin_bridge_counter_keyed_operational_epoch_loop(
                contract_owner,
                owner,
                **arguments,
            )
    with pytest.raises(AttributeError):
        owner._contract_owner = None
    with pytest.raises(AttributeError):
        del owner._certificate


def test_records_are_nonpickle_noncopy_and_nonsubclassable(
    tight_result_case,
):
    bundle, _, _, _, result = tight_result_case
    proposal = result.proposals[0]
    records = (
        bundle["epoch_owner"],
        bundle["epoch_owner"].certificate,
        proposal.epoch_stream.address,
        proposal.epoch_stream,
        proposal,
        result.terminal,
        result,
    )
    for record in records:
        for operation in (pickle.dumps, copy.copy, copy.deepcopy):
            with pytest.raises(TypeError):
                operation(record)
    for record_type in (
        epoch.CounterKeyedOperationalEpochLoopCertificate,
        epoch.CounterKeyedOperationalEpochAddress,
        epoch.CounterKeyedOperationalEpochStream,
        epoch.CounterKeyedOperationalEpochProposal,
        epoch.CounterKeyedOperationalEpochTerminal,
        epoch.CounterKeyedOperationalEpochLoopResult,
        epoch.CounterKeyedOperationalEpochLoop,
    ):
        with pytest.raises(TypeError, match="subclassed"):
            type("ForbiddenSubclass", (record_type,), {})


def test_public_surface_and_no_legacy_tag1_execution_path(tight_bundle):
    expected = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCOPE",
        "COUNTER_KEY_DOMAIN_OPERATIONAL_EPOCH",
        "COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH",
        "COUNTER_KEYED_OPERATIONAL_EPOCH_ADDRESS_LAYOUT",
        "COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS",
        "COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_STREAM_RECORDS",
        "COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_RECORDED_RAW64_WORDS",
        "CounterKeyedOperationalEpochLoopCertificate",
        "CounterKeyedOperationalEpochAddress",
        "CounterKeyedOperationalEpochStream",
        "CounterKeyedOperationalEpochProposal",
        "CounterKeyedOperationalEpochTerminal",
        "CounterKeyedOperationalEpochLoopResult",
        "CounterKeyedOperationalEpochLoop",
        "PluginBridgeCounterKeyedOperationalEpochLoopError",
        "certify_plugin_bridge_counter_keyed_operational_epoch_loop",
        "require_matching_plugin_bridge_counter_keyed_operational_epoch_loop",
        "validate_plugin_bridge_counter_keyed_operational_epoch_loop_certificate",
    }
    assert set(epoch.__all__) == expected
    owner = tight_bundle["epoch_owner"]
    for name in (
        "make_operational_epoch_stream",
        "validate_operational_epoch_stream",
        "reconstruct_operational_epoch_stream",
        "run",
        "validate_proposal",
        "validate_terminal",
        "validate_result",
    ):
        assert "rng" not in inspect.signature(getattr(owner, name)).parameters
    owner_source = inspect.getsource(epoch.CounterKeyedOperationalEpochLoop)
    assert "make_jump_proposal_stream" not in owner_source
    assert "make_terminal_wait_stream" in owner_source
    source = inspect.getsource(epoch)
    tree = ast.parse(source)
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "hash" not in called_names
    assert "not-checkpoint23-jump-proposal-stream-consumption" in source
    assert "not-cross-epoch-sequential-stream" in source
    assert "not-statistical-independence" in source
    result_fields = epoch.CounterKeyedOperationalEpochLoopResult.__annotations__
    assert "checkpoint23_jump_proposal_stream_count" in result_fields
    assert "checkpoint23_jump_proposal_streams_consumed" in result_fields


def test_optional_torch_import_boundary_is_explicit():
    module_path = Path(epoch.__file__).resolve()
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
    import heterodiff.processes.plugin_bridge_counter_keyed_operational_epoch_loop
except ModuleNotFoundError as error:
    text = str(error)
    assert "counter-keyed operational epoch loops require" in text
    assert "optional PyTorch" in text
else:
    raise AssertionError("optional PyTorch boundary did not refuse")
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=source_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
