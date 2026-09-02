"""Hostile tests for checkpoint-39 lineage and tag-3 coordination."""

import ast
from fractions import Fraction
import importlib
import inspect
from pathlib import Path
import pickle
import random
import subprocess
import sys
import textwrap

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="lineage and tag-3 coordination requires PyTorch"
)

from heterodiff.theory.configuration_reference import TransformedEvent  # noqa: E402

coordination = importlib.import_module(  # noqa: E402
    "heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "lineage_tag3_coordination"
)
checkpoint38 = importlib.import_module(  # noqa: E402
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "finite_batch_law"
)


COORDINATION_ROLE = "d" * 64
COORDINATION_POLICY = getattr(
    coordination,
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_LINEAGE_TAG3_"
    "COORDINATION_POLICY",
)
MAX_UINT64 = (1 << 64) - 1
_CERTIFY = getattr(
    coordination,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_lineage_tag3_"
    "coordination",
)
_MATCHING = getattr(
    coordination,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "lineage_tag3_coordination",
)
_VALIDATE_CERTIFICATE = getattr(
    coordination,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_lineage_tag3_"
    "coordination_certificate",
)
COORDINATION_ERROR = getattr(
    coordination,
    "PluginBridgeCounterKeyedInitialTiltRejectionLineageTag3CoordinationError",
)


def _rng_snapshot():
    numpy_state = np.random.get_state()
    return (
        random.getstate(),
        (numpy_state[0], numpy_state[1].copy(), *numpy_state[2:]),
        torch.random.get_rng_state().clone(),
    )


def _assert_rng_unchanged(before):
    python_before, numpy_before, torch_before = before
    numpy_after = np.random.get_state()
    assert random.getstate() == python_before
    assert numpy_after[0] == numpy_before[0]
    assert np.array_equal(numpy_after[1], numpy_before[1])
    assert numpy_after[2:] == numpy_before[2:]
    assert torch.equal(torch.random.get_rng_state(), torch_before)


def _forged(value, **updates):
    forged = object.__new__(type(value))
    for name in type(value).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(value, name)))
    return forged


def _forge_owner(owner, **updates):
    forged = object.__new__(type(owner))
    for name in type(owner).__slots__:
        object.__setattr__(forged, name, updates.get(name, getattr(owner, name)))
    return forged


def _redigested(record, fields, payload, digest_name, **updates):
    values = {name: updates.get(name, getattr(record, name)) for name in fields()}
    values[digest_name] = "0" * 64
    values[digest_name] = coordination._SEMANTIC_DIGEST(payload(values))
    return _forged(record, **values)


class _HashBomb:
    def __init__(self):
        self.calls = 0

    def __hash__(self):
        self.calls += 1
        raise AssertionError("hostile hashing must not execute")


class _EqualityBomb:
    def __init__(self):
        self.calls = 0

    def __eq__(self, other):
        del other
        self.calls += 1
        raise AssertionError("hostile equality must not execute")

    def __ne__(self, other):
        del other
        self.calls += 1
        raise AssertionError("hostile inequality must not execute")


@pytest.fixture(scope="module")
def live_bundle():
    """Coordinate one exact CP38 transcript without touching caller RNGs."""

    bundle = checkpoint38.live_bundle.__wrapped__()
    before = _rng_snapshot()
    owner = _CERTIFY(
        bundle["owner"],
        coordination_policy=COORDINATION_POLICY,
        coordination_role_sha256=COORDINATION_ROLE,
    )
    result = owner.coordinate(37_000, 0)
    _assert_rng_unchanged(before)
    return {**bundle, "coordination_owner": owner, "coordination_result": result}


@pytest.fixture(scope="module")
def address_owner(live_bundle):
    """Reuse the authentic CP39 owner and its actually certified domain."""

    return live_bundle["coordination_owner"]


@pytest.fixture(scope="module")
def branch_bundle():
    """Replay frozen all-atomic witnesses for both one-attempt branches."""

    checkpoint36 = checkpoint38.checkpoint36
    checkpoint37 = checkpoint38.checkpoint37
    checkpoint28 = checkpoint36.checkpoint28
    checkpoint30 = checkpoint36.checkpoint30
    bundle = checkpoint28.atomic_bundle.__wrapped__()
    potential = bundle["potential_composer"]
    bundle["totalized_guide"] = potential.totalized_guide
    bundle["totalized_residual"] = potential.totalized_residual
    bundle["initial_tilt"] = checkpoint30._certify(bundle)
    _, preparation_owner = checkpoint36._certify(
        bundle,
        attempt_budget=1,
        role="2" * 64,
    )
    decision_owner = checkpoint37._CERTIFY(
        preparation_owner,
        decision_policy=checkpoint37.DECISION_POLICY,
        decision_role_sha256="3" * 64,
    )
    word_hypothesis = checkpoint38._DECLARE(
        hypothesis_scope=(
            checkpoint38.law.FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCOPE
        ),
        word_source_premise=(
            checkpoint38.law.FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE
        ),
    )
    finite_batch_owner = checkpoint38._CERTIFY(
        decision_owner,
        word_hypothesis,
        law_policy=checkpoint38.LAW_POLICY,
        law_role_sha256="4" * 64,
    )
    owner = _CERTIFY(
        finite_batch_owner,
        coordination_policy=COORDINATION_POLICY,
        coordination_role_sha256="5" * 64,
    )
    certificate = preparation_owner.certificate
    manifest = certificate.manifest
    direct_prefix = checkpoint28.checkpoint26_tests._direct_prefix
    decision_block = certificate.blocks_per_attempt - 1
    upper = Fraction(
        certificate.global_upper_bound_numerator,
        certificate.global_upper_bound_denominator,
    )

    assert manifest.manifest_sha256 == (
        "94429648a6897773db7ad2e59ea2ce5990b15077b0b54d12ae16c03f0ae8910d"
    )
    assert manifest.type_dimensions == ((0, 0), (1, 0))
    assert manifest.total_cap == 2
    assert manifest.maximum_coordinate_dimension == 0
    assert manifest.count_cumulative_ends == (
        5_457_616_589_854_897_272,
        13_098_279_815_651_752_968,
        1 << 64,
    )
    assert manifest.type_cumulative_ends == (
        7_378_697_629_483_821_056,
        1 << 64,
    )
    assert manifest.canonical_block_raw64_word_counts == (3,)
    assert certificate.block_raw64_word_counts == (3, 1)
    assert certificate.blocks_per_attempt == 2
    assert decision_block == 1
    assert upper == Fraction(
        4_059_535_955_093_743,
        2_361_183_241_434_822_606_848,
    )
    assert preparation_owner.reference_initializer_owner is bundle["initializer_owner"]
    assert preparation_owner.initial_tilt_composer is bundle["initial_tilt"]
    assert bundle["initial_tilt"].reference_composer is bundle["reference_composer"]
    assert bundle["contract_owner"].reference_composer is bundle["reference_composer"]
    assert decision_owner.preparation_owner is preparation_owner
    assert finite_batch_owner.decision_owner is decision_owner
    assert owner.finite_batch_law_owner is finite_batch_owner
    assert (
        owner.certificate.checkpoint28_certificate
        is bundle["initializer_owner"].certificate
    )
    assert (
        owner.certificate.checkpoint23_certificate
        is bundle["contract_owner"].certificate
    )

    expected_score = Fraction(
        4_907_040_509_669_326_485,
        4_835_703_278_458_516_698_824_704,
    )
    expected_delta = Fraction(
        -3_406_889_126_362_659_179,
        4_835_703_278_458_516_698_824_704,
    )
    expected_quota = 18_446_731_077_463_495_104

    def exact_witness(
        run_id,
        *,
        expected_proposal,
        expected_decision,
        expected_cardinality,
        expected_type_positions,
        expected_model_keys,
        accepted,
    ):
        proposal_blocks = tuple(
            direct_prefix(
                run_id=run_id,
                initialization_index=0,
                stage_index=(
                    checkpoint36.preparation.INITIAL_TILT_REJECTION_STAGE_INDEX
                ),
                attempt_index=block_index,
                word_count=word_count,
            )[0]
            for block_index, word_count in enumerate(
                certificate.block_raw64_word_counts[:-1]
            )
        )
        proposal_words = tuple(word for block in proposal_blocks for word in block)
        assert proposal_words == expected_proposal
        decision_words, _ = direct_prefix(
            run_id=run_id,
            initialization_index=0,
            stage_index=checkpoint36.preparation.INITIAL_TILT_REJECTION_STAGE_INDEX,
            attempt_index=decision_block,
            word_count=1,
        )
        assert decision_words == (expected_decision,)
        cardinality = checkpoint36.preparation._CP28_QUOTA_POSITION(
            proposal_words[manifest.count_word_offset],
            manifest.count_cumulative_ends,
        )
        assert cardinality == expected_cardinality
        slot_fields = tuple(
            checkpoint36.preparation._CP28_MATERIALIZE_SLOT_FIELDS(
                manifest,
                proposal_words,
                raw_slot_index=raw_slot_index,
            )
            for raw_slot_index in range(manifest.total_cap)
        )
        assert (
            tuple(item["type_quota_position"] for item in slot_fields)
            == expected_type_positions
        )
        selected = tuple(item["event"] for item in slot_fields[:cardinality])
        order = sorted(
            range(cardinality),
            key=lambda index: (selected[index].model_key(), index),
        )
        configuration = tuple(selected[index] for index in order)
        assert tuple(event.model_key() for event in configuration) == (
            expected_model_keys
        )
        score = preparation_owner.initial_tilt_composer.evaluate(
            configuration,
            residual_context=certificate.residual_context,
        )
        exact_score = Fraction(
            score.exact_initial_log_factor_numerator,
            score.exact_initial_log_factor_denominator,
        )
        assert exact_score == expected_score
        delta = exact_score - upper
        assert delta == expected_delta
        quota = checkpoint37.decision._floor_exp_uint64_quota(delta)
        assert quota.branch == "adaptive_decimal"
        assert quota.quota == expected_quota
        assert (expected_decision < quota.quota) is accepted
        return configuration

    empty_run = 39_200
    exhausted_run = 814_655
    empty_configuration = exact_witness(
        empty_run,
        expected_proposal=(
            2_673_771_586_620_735_805,
            13_370_833_249_004_479_446,
            10_545_140_001_084_832_309,
        ),
        expected_decision=12_515_186_141_826_457_847,
        expected_cardinality=0,
        expected_type_positions=(1, 1),
        expected_model_keys=(),
        accepted=True,
    )
    exhausted_configuration = exact_witness(
        exhausted_run,
        expected_proposal=(
            10_459_586_811_134_012_693,
            15_508_737_134_228_860_040,
            11_708_325_038_492_333_495,
        ),
        expected_decision=18_446_734_589_125_001_078,
        expected_cardinality=1,
        expected_type_positions=(1, 1),
        expected_model_keys=((1, ()),),
        accepted=False,
    )
    assert empty_configuration == ()
    assert exhausted_configuration == (TransformedEvent(1),)
    selected_empty = owner.coordinate(empty_run, 0)
    exhausted = owner.coordinate(exhausted_run, 0)
    assert selected_empty.outcome == "selected"
    assert selected_empty.selected_configuration == ()
    assert selected_empty.initial_intensity is not None
    assert selected_empty.lineage_state is not None
    assert selected_empty.lineage_state.occurrences == ()
    assert selected_empty.occurrence_payloads == ()
    assert exhausted.outcome == "exhausted"
    assert exhausted.selected_configuration is None
    assert exhausted.initial_intensity is None
    assert exhausted.lineage_state is None
    assert exhausted.occurrence_payloads == ()

    def assert_live_attempt(result, proposal, decision_word, accepted):
        parent = result.parent_finite_batch_law_result.parent_decision_result
        attempt = parent.preparation_result.attempts[0]
        threshold = parent.thresholds[0]
        realized = parent.decisions[0]
        assert attempt.proposal_concatenated_raw64_words == proposal
        assert attempt.reserved_decision_raw64_word == decision_word
        assert Fraction(attempt.q_numerator, attempt.q_denominator) == expected_score
        assert (
            Fraction(
                attempt.global_upper_bound_numerator,
                attempt.global_upper_bound_denominator,
            )
            == upper
        )
        assert (
            Fraction(
                attempt.q_minus_upper_bound_numerator,
                attempt.q_minus_upper_bound_denominator,
            )
            == expected_delta
        )
        assert threshold.acceptance_quota == expected_quota
        assert realized.decision_word == decision_word
        assert realized.word_below_quota is accepted
        assert realized.accepted is accepted

    assert_live_attempt(
        selected_empty,
        (
            2_673_771_586_620_735_805,
            13_370_833_249_004_479_446,
            10_545_140_001_084_832_309,
        ),
        12_515_186_141_826_457_847,
        True,
    )
    assert_live_attempt(
        exhausted,
        (
            10_459_586_811_134_012_693,
            15_508_737_134_228_860_040,
            11_708_325_038_492_333_495,
        ),
        18_446_734_589_125_001_078,
        False,
    )
    return {
        "owner": owner,
        "selected_empty": selected_empty,
        "exhausted": exhausted,
        "empty_run": empty_run,
        "exhausted_run": exhausted_run,
    }


def test_public_api_constants_signatures_and_owner_surface_are_exact(live_bundle):
    owner = live_bundle["coordination_owner"]
    owner_type = (
        coordination.CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner
    )
    assert type(owner) is owner_type
    assert owner.finite_batch_law_owner is live_bundle["owner"]
    assert owner.certificate is live_bundle["coordination_result"].certificate
    assert coordination.INITIAL_TILT_REJECTION_LINEAGE_TAG3_DOMAIN_TAG == 3
    assert coordination.INITIAL_TILT_REJECTION_LINEAGE_TAG3_INITIAL_REVERSE_TIME == 0.0
    assert coordination.INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_STREAM_RECORDS == 64
    assert (
        coordination.INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE
        == 4_096
    )
    assert (
        coordination.INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_TOTAL_RAW64_WORDS == 65_536
    )
    assert coordination.INITIAL_TILT_REJECTION_LINEAGE_TAG3_OUTCOMES == (
        "selected",
        "exhausted",
    )
    coordinate_signature = (
        "(run_id: 'object', initialization_index: 'object') -> "
        "'CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult'"
    )
    validation_signature = (
        "(result: 'object', run_id: 'object', initialization_index: 'object') -> "
        "'CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult'"
    )
    assert str(inspect.signature(owner.coordinate)) == coordinate_signature
    assert str(inspect.signature(owner.validate_result)) == validation_signature
    assert tuple(inspect.signature(_CERTIFY).parameters) == (
        "finite_batch_law_owner",
        "coordination_policy",
        "coordination_role_sha256",
    )
    assert tuple(inspect.signature(_MATCHING).parameters) == (
        "finite_batch_law_owner",
        "owner",
        "coordination_policy",
        "coordination_role_sha256",
    )
    assert tuple(inspect.signature(_VALIDATE_CERTIFICATE).parameters) == (
        "finite_batch_law_owner",
        "owner",
        "coordination_policy",
        "coordination_role_sha256",
    )


def test_certificate_binds_exact_transitive_ancestry_and_conservative_claims(
    live_bundle,
):
    owner = live_bundle["coordination_owner"]
    certificate = owner.certificate
    assert certificate.checkpoint38_certificate is live_bundle["owner"].certificate
    assert (
        certificate.checkpoint28_certificate
        is live_bundle["initializer_owner"].certificate
    )
    assert (
        certificate.checkpoint27_certificate
        is live_bundle["protocol_owner"].certificate
    )
    assert (
        certificate.checkpoint26_certificate is live_bundle["control_owner"].certificate
    )
    assert (
        certificate.checkpoint25_certificate
        is live_bundle["consumption_owner"].certificate
    )
    assert (
        certificate.checkpoint23_certificate
        is live_bundle["contract_owner"].certificate
    )
    assert certificate.checkpoint38_owner_runtime_identity == id(live_bundle["owner"])
    assert certificate.checkpoint23_owner_runtime_identity == id(
        live_bundle["contract_owner"]
    )
    assert certificate.reference_composer_runtime_identity == id(
        live_bundle["contract_owner"].reference_composer
    )
    assert certificate.manifest is live_bundle["initializer_owner"].manifest
    for name in coordination._CERTIFICATE_POSITIVE_FLAGS:
        assert getattr(certificate, name) is True
    for name in coordination._CERTIFICATE_NEGATIVE_FLAGS:
        assert getattr(certificate, name) is False
    assert (
        _VALIDATE_CERTIFICATE(
            live_bundle["owner"],
            owner,
            coordination_policy=COORDINATION_POLICY,
            coordination_role_sha256=COORDINATION_ROLE,
        )
        is certificate
    )
    assert (
        _MATCHING(
            live_bundle["owner"],
            owner,
            coordination_policy=COORDINATION_POLICY,
            coordination_role_sha256=COORDINATION_ROLE,
        )
        is owner
    )


@pytest.mark.parametrize(
    "object_field,digest_field,foreign_field",
    (
        (
            "checkpoint28_certificate",
            "checkpoint28_certificate_sha256",
            "checkpoint27_certificate",
        ),
        (
            "checkpoint27_certificate",
            "checkpoint27_certificate_sha256",
            "checkpoint26_certificate",
        ),
        (
            "checkpoint26_certificate",
            "checkpoint26_certificate_sha256",
            "checkpoint25_certificate",
        ),
        (
            "checkpoint25_certificate",
            "checkpoint25_certificate_sha256",
            "checkpoint23_certificate",
        ),
        (
            "checkpoint23_certificate",
            "checkpoint23_certificate_sha256",
            "checkpoint25_certificate",
        ),
    ),
)
def test_standalone_certificate_rejects_redigested_wrong_parent_exact_types(
    live_bundle,
    object_field,
    digest_field,
    foreign_field,
):
    certificate = live_bundle["coordination_owner"].certificate
    foreign = getattr(certificate, foreign_field)
    forged = _redigested(
        certificate,
        coordination._certificate_fields,
        coordination._certificate_payload,
        "certificate_sha256",
        **{
            object_field: foreign,
            digest_field: foreign.certificate_sha256,
        },
    )
    with pytest.raises((TypeError, ValueError), match="wrong exact|certificate"):
        coordination._validate_certificate(forged)


@pytest.mark.parametrize("initialization_index", (0, MAX_UINT64))
@pytest.mark.parametrize("attempt_boundary", ("first", "last"))
@pytest.mark.parametrize("occurrence_serial", (1, 64))
def test_direct_tag3_address_formula_boundaries_injectivity_and_legacy_disjointness(
    address_owner,
    initialization_index,
    attempt_boundary,
    occurrence_serial,
):
    certificate = address_owner.certificate
    last_attempt_index = certificate.checkpoint38_certificate.attempt_budget - 1
    selected_attempt_index = 0 if attempt_boundary == "first" else last_attempt_index
    address = coordination._make_address(
        certificate,
        run_id=MAX_UINT64,
        initialization_index=initialization_index,
        occurrence_serial=occurrence_serial,
        selected_attempt_index=selected_attempt_index,
    )
    assert address.run_id == MAX_UINT64
    assert address.philox_key == (MAX_UINT64, 3)
    assert address.philox_counter == (
        0,
        initialization_index,
        occurrence_serial,
        selected_attempt_index + 1,
    )
    assert address.selected_attempt_suffix == selected_attempt_index + 1
    assert address.philox_counter[-1] > 0
    legacy = address_owner._checkpoint23_owner.make_initializer_stream(
        MAX_UINT64,
        initialization_index,
        occurrence_serial,
    )
    assert legacy.address.philox_counter == (
        0,
        initialization_index,
        occurrence_serial,
        0,
    )
    assert address.philox_key == legacy.address.philox_key
    assert address.philox_counter != legacy.address.philox_counter


def test_direct_tag3_address_cartesian_coordinates_are_injective(address_owner):
    certificate = address_owner.certificate
    last_attempt_index = certificate.checkpoint38_certificate.attempt_budget - 1
    attempt_indices = tuple(sorted({0, last_attempt_index}))
    coordinates = set()
    digests = set()
    for initialization_index in (0, MAX_UINT64):
        for selected_attempt_index in attempt_indices:
            for occurrence_serial in (1, 64):
                address = coordination._make_address(
                    certificate,
                    run_id=71,
                    initialization_index=initialization_index,
                    occurrence_serial=occurrence_serial,
                    selected_attempt_index=selected_attempt_index,
                )
                coordinates.add((address.philox_key, address.philox_counter))
                digests.add(address.address_sha256)
    expected_count = 4 * len(attempt_indices)
    assert len(coordinates) == expected_count
    assert len(digests) == expected_count


def test_maximum_prefix_has_no_upper_carry_and_same_address_replays_exactly(
    address_owner,
):
    certificate = address_owner.certificate
    last_attempt_index = certificate.checkpoint38_certificate.attempt_budget - 1
    address = coordination._make_address(
        certificate,
        run_id=MAX_UINT64,
        initialization_index=MAX_UINT64,
        occurrence_serial=64,
        selected_attempt_index=last_attempt_index,
    )
    before = _rng_snapshot()
    first = coordination._make_stream(certificate, address, 4_096)
    second = coordination._make_stream(certificate, address, 4_096)
    _assert_rng_unchanged(before)
    assert first.raw64_words == second.raw64_words
    assert first.raw64_words_sha256 == second.raw64_words_sha256
    assert first.initial_snapshot_sha256 == second.initial_snapshot_sha256
    assert first.final_snapshot_sha256 == second.final_snapshot_sha256
    assert first.initial_state.counter == address.philox_counter
    assert first.final_state.key == first.initial_state.key
    assert first.final_state.counter[1:] == first.initial_state.counter[1:]
    assert first.no_upper_counter_carry is True
    assert coordination._replay_stream(first, certificate=certificate) is first


def test_redigested_address_formula_tamper_and_stream_splices_fail_closed(
    address_owner,
):
    certificate = address_owner.certificate
    last_attempt_index = certificate.checkpoint38_certificate.attempt_budget - 1
    address = coordination._make_address(
        certificate,
        run_id=77,
        initialization_index=11,
        occurrence_serial=3,
        selected_attempt_index=last_attempt_index,
    )
    altered_address = _redigested(
        address,
        coordination._address_fields,
        coordination._address_payload,
        "address_sha256",
        philox_counter=(0, 11, 3, last_attempt_index),
    )
    with pytest.raises(ValueError, match="counter differs"):
        coordination._validate_address(altered_address, certificate=certificate)

    one = coordination._make_stream(certificate, address, 1)
    two = coordination._make_stream(certificate, address, 2)
    altered_words = (one.raw64_words[0] ^ 1,)
    word_splice = _redigested(
        one,
        coordination._stream_fields,
        coordination._stream_payload,
        "stream_sha256",
        raw64_words=altered_words,
        raw64_words_sha256=coordination._SEMANTIC_DIGEST(
            {"raw64_words": altered_words}
        ),
    )
    assert coordination._validate_stream(word_splice, certificate=certificate) is (
        word_splice
    )
    with pytest.raises(ValueError, match="prefix did not replay"):
        coordination._replay_stream(word_splice, certificate=certificate)

    final_splice = _redigested(
        one,
        coordination._stream_fields,
        coordination._stream_payload,
        "stream_sha256",
        final_state=two.final_state,
        final_snapshot_sha256=two.final_snapshot_sha256,
        final_state_sha256=two.final_state_sha256,
    )
    assert coordination._validate_stream(final_splice, certificate=certificate) is (
        final_splice
    )
    with pytest.raises(ValueError, match="final snapshot differs"):
        coordination._replay_stream(final_splice, certificate=certificate)

    other_address = coordination._make_address(
        certificate,
        run_id=77,
        initialization_index=12,
        occurrence_serial=3,
        selected_attempt_index=last_attempt_index,
    )
    address_splice = _redigested(
        one,
        coordination._stream_fields,
        coordination._stream_payload,
        "stream_sha256",
        address=other_address,
        address_sha256=other_address.address_sha256,
    )
    with pytest.raises(ValueError, match="initial state differs"):
        coordination._validate_stream(address_splice, certificate=certificate)


def test_live_selected_result_preserves_source_attempt_configuration_and_lineage(
    live_bundle,
):
    result = live_bundle["coordination_result"]
    parent = result.parent_finite_batch_law_result
    assert parent is not live_bundle["result"]
    assert parent.result_sha256 == live_bundle["result"].result_sha256
    assert result.outcome == parent.outcome == "selected"
    assert result.source_selected_attempt_index == parent.selected_attempt_index == 0
    assert result.selected_configuration is parent.selected_configuration
    assert result.selected_configuration_sha256 == parent.selected_configuration_sha256
    assert (
        result.initial_intensity.source_configuration == result.selected_configuration
    )
    assert all(
        actual is selected
        for actual, selected in zip(
            result.initial_intensity.source_configuration,
            result.selected_configuration,
        )
    )
    assert result.initial_intensity.reverse_time == 0.0
    assert result.lineage_state.model_configuration == result.selected_configuration
    assert all(
        actual is selected
        for actual, selected in zip(
            result.lineage_state.model_configuration,
            result.selected_configuration,
        )
    )
    assert result.stream_count == len(result.selected_configuration) == 1
    assert len(result.occurrence_payloads) == result.stream_count
    expected_counts, expected_total = coordination._word_plan(
        result.selected_configuration,
        manifest=result.certificate.manifest,
    )
    assert result.tag3_raw64_word_counts == expected_counts == (2,)
    assert result.total_raw64_words == expected_total == 2
    occurrence = result.lineage_state.occurrences[0]
    payload = result.occurrence_payloads[0]
    assert payload.lineaged_occurrence is occurrence
    assert payload.identifier is occurrence.identifier
    assert payload.event is result.selected_configuration[0]
    assert payload.position == 0
    assert payload.occurrence_serial == occurrence.identifier.serial == 1
    assert payload.qualified_lineage_coordinate == (37_000, 0, 0, 1)
    assert occurrence.identifier.origin_kind == "initial"
    assert occurrence.identifier.origin_initialization_index == 0
    assert occurrence.identifier.origin_initial_position == 0
    assert occurrence.identifier.origin_step_index is None
    assert occurrence.identifier.origin_proposal_index is None
    assert payload.manifest_coordinate_dimension == 2
    assert payload.raw64_word_count == 2
    assert payload.tag3_stream.address.philox_key == (37_000, 3)
    assert payload.tag3_stream.address.philox_counter == (0, 0, 1, 1)
    assert payload.prefix_generates_selected_event is False
    assert result.selected_branch_materialized is True
    assert result.exhausted_no_state is False
    assert result.parent_resolve_call_count == 1
    assert result.initializer_output_admitted is False
    assert result.initializer_admissible is False


def test_local_equal_events_keep_positional_lineage_and_distinct_addresses(
    live_bundle,
):
    result = live_bundle["coordination_result"]
    certificate = result.certificate
    lineage_certificate = certificate.checkpoint23_certificate
    selected_attempt_index = result.source_selected_attempt_index
    left = result.occurrence_payloads[0]
    first = left.event
    second = TransformedEvent(first.event_type, first.coordinates)
    assert first == second and first is not second
    identifier = coordination._lineage._make_identifier(
        lineage_certificate,
        run_id=result.run_id,
        serial=2,
        origin_kind="initial",
        origin_initialization_index=result.initialization_index,
        origin_initial_position=1,
    )
    occurrence = coordination._lineage._make_occurrence(
        lineage_certificate,
        identifier,
        second,
    )
    assert occurrence.event is second
    address = coordination._make_address(
        certificate,
        run_id=result.run_id,
        initialization_index=result.initialization_index,
        occurrence_serial=identifier.serial,
        selected_attempt_index=selected_attempt_index,
    )
    stream = coordination._make_stream(certificate, address, left.raw64_word_count)
    right = coordination._make_occurrence(
        certificate,
        occurrence,
        stream,
        position=1,
        selected_attempt_index=selected_attempt_index,
    )
    assert left.event is first and right.event is second
    assert left.event_model_key == right.event_model_key
    assert left.occurrence_serial == 1 and right.occurrence_serial == 2
    assert left.qualified_lineage_coordinate == (
        result.run_id,
        result.initialization_index,
        selected_attempt_index,
        1,
    )
    assert right.qualified_lineage_coordinate == (
        result.run_id,
        result.initialization_index,
        selected_attempt_index,
        2,
    )
    expected_suffix = selected_attempt_index + 1
    assert left.tag3_stream.address.philox_counter == (
        0,
        result.initialization_index,
        1,
        expected_suffix,
    )
    assert right.tag3_stream.address.philox_counter == (
        0,
        result.initialization_index,
        2,
        expected_suffix,
    )
    assert left.tag3_address_sha256 != right.tag3_address_sha256

    position_splice = _redigested(
        left,
        coordination._occurrence_fields,
        coordination._occurrence_payload,
        "record_sha256",
        position=1,
    )
    with pytest.raises(ValueError, match="position differs"):
        coordination._validate_occurrence(position_splice, certificate=certificate)

    stream_splice = _redigested(
        left,
        coordination._occurrence_fields,
        coordination._occurrence_payload,
        "record_sha256",
        tag3_stream=right.tag3_stream,
        tag3_stream_sha256=right.tag3_stream_sha256,
        tag3_address_sha256=right.tag3_address_sha256,
    )
    with pytest.raises(ValueError, match="stream subject"):
        coordination._validate_occurrence(stream_splice, certificate=certificate)

    occurrence_splice = _redigested(
        left,
        coordination._occurrence_fields,
        coordination._occurrence_payload,
        "record_sha256",
        lineaged_occurrence=right.lineaged_occurrence,
        lineaged_occurrence_sha256=right.lineaged_occurrence_sha256,
        identifier=right.identifier,
        identifier_sha256=right.identifier_sha256,
        event=right.event,
        occurrence_serial=right.occurrence_serial,
        qualified_lineage_coordinate=right.qualified_lineage_coordinate,
    )
    with pytest.raises(ValueError, match="identifier position"):
        coordination._validate_occurrence(occurrence_splice, certificate=certificate)


def test_selected_empty_is_a_present_state_with_no_local_stream(branch_bundle):
    result = branch_bundle["selected_empty"]
    assert result.outcome == "selected"
    assert result.selected_configuration == ()
    assert result.initial_intensity is not None
    assert result.initial_intensity.source_configuration == ()
    assert result.lineage_state is not None
    assert result.lineage_state.model_configuration == ()
    assert result.lineage_state.occurrences == ()
    assert result.tag3_raw64_word_counts == ()
    assert result.occurrence_payloads == ()
    assert result.stream_count == result.total_raw64_words == 0
    assert result.selected_empty_state_retained is True
    assert result.composer_preflight_invoked is True
    assert result.lineage_bootstrap_invoked is True
    assert result.local_tag3_streams_consumed is False
    assert result.exhausted_no_state is False


def test_exhaustion_is_exact_no_state_and_has_no_child_construction(branch_bundle):
    owner = branch_bundle["owner"]
    result = branch_bundle["exhausted"]
    assert result.outcome == "exhausted"
    for name in (
        "source_selected_attempt_index",
        "selected_configuration",
        "selected_configuration_sha256",
        "initial_intensity",
        "initial_intensity_sha256",
        "lineage_state",
        "lineage_state_sha256",
    ):
        assert getattr(result, name) is None
    assert result.tag3_raw64_word_counts == ()
    assert result.occurrence_payloads == ()
    assert result.occurrence_payload_sha256s == ()
    assert result.tag3_address_sha256s == ()
    assert result.qualified_lineage_coordinates == ()
    assert result.stream_count == result.total_raw64_words == 0
    assert result.selected_branch_materialized is False
    assert result.exhausted_no_state is True
    assert result.composer_preflight_invoked is False
    assert result.lineage_bootstrap_invoked is False
    assert result.local_tag3_streams_consumed is False
    assert result.exhausted_branch_invoked_selected_state_construction_callback is False
    original = coordination._COMPOSER_TYPE.preflight_candidate_intensity
    calls = {"composer": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["composer"] += 1
        raise AssertionError("exhaustion validation reached the composer")

    coordination._COMPOSER_TYPE.preflight_candidate_intensity = forbidden
    try:
        assert (
            owner.validate_result(
                result,
                branch_bundle["exhausted_run"],
                0,
            )
            is result
        )
    finally:
        coordination._COMPOSER_TYPE.preflight_candidate_intensity = original
    assert calls == {"composer": 0}


def test_parent_result_outcome_binding_refuses_before_selected_callbacks(branch_bundle):
    owner = branch_bundle["owner"]
    exhausted = branch_bundle["exhausted"]
    selected_empty = branch_bundle["selected_empty"]
    values = {name: getattr(exhausted, name) for name in coordination._result_fields()}
    for name in (
        "source_selected_attempt_index",
        "selected_configuration",
        "selected_configuration_sha256",
        "initial_intensity",
        "initial_intensity_sha256",
        "lineage_state",
        "lineage_state_sha256",
        "tag3_raw64_word_counts",
        "occurrence_payloads",
        "occurrence_payload_sha256s",
        "tag3_address_sha256s",
        "qualified_lineage_coordinates",
        "stream_count",
        "total_raw64_words",
    ):
        values[name] = getattr(selected_empty, name)
    values.update(
        {
            "outcome": "selected",
            "selected_branch_materialized": True,
            "exhausted_no_state": False,
            "selected_empty_state_retained": True,
            "composer_preflight_invoked": True,
            "lineage_bootstrap_invoked": True,
            "local_tag3_streams_consumed": False,
            "exact_parent_selected_configuration_identity_preserved": True,
            "exact_parent_selected_attempt_index_preserved": True,
            "lineage_projection_per_event_identity_preserved": True,
        }
    )
    values["result_sha256"] = "0" * 64
    values["result_sha256"] = coordination._SEMANTIC_DIGEST(
        coordination._result_payload(values)
    )
    forged = _forged(exhausted, **values)
    original_preflight = coordination._COMPOSER_TYPE.preflight_candidate_intensity
    calls = {"composer": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["composer"] += 1
        raise AssertionError("parent/result mismatch reached selected callbacks")

    coordination._COMPOSER_TYPE.preflight_candidate_intensity = forbidden
    try:
        with pytest.raises(ValueError, match="differs from CP38"):
            owner.validate_result(
                forged,
                branch_bundle["exhausted_run"],
                0,
            )
    finally:
        coordination._COMPOSER_TYPE.preflight_candidate_intensity = original_preflight
    assert calls == {"composer": 0}


def test_validation_has_one_intensity_recompute_and_no_child_construction(
    live_bundle,
):
    owner = live_bundle["coordination_owner"]
    result = live_bundle["coordination_result"]
    original_preflight = coordination._COMPOSER_TYPE.preflight_candidate_intensity
    calls = {"recompute": 0}

    def counted_preflight(composer, state, *, reverse_time):
        calls["recompute"] += 1
        return original_preflight(
            composer,
            state,
            reverse_time=reverse_time,
        )

    coordination._COMPOSER_TYPE.preflight_candidate_intensity = counted_preflight
    before = _rng_snapshot()
    try:
        checked = owner.validate_result(
            result, result.run_id, result.initialization_index
        )
    finally:
        coordination._COMPOSER_TYPE.preflight_candidate_intensity = original_preflight
    _assert_rng_unchanged(before)
    assert checked is result
    assert calls == {"recompute": 1}


@pytest.mark.parametrize(
    "bad",
    (True, np.int64(1), np.uint64(1), 1.0, "1", -1, 1 << 64),
)
@pytest.mark.parametrize("coordinate_name", ("run_id", "initialization_index"))
def test_request_coordinates_fail_before_parent_resolution(
    live_bundle,
    bad,
    coordinate_name,
):
    owner = live_bundle["coordination_owner"]
    original_global = coordination._CP38_RESOLVE
    original_owner = owner._parent_resolve
    calls = {"resolve": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["resolve"] += 1
        raise AssertionError("malformed request reached CP38 resolve")

    coordination._CP38_RESOLVE = forbidden
    object.__setattr__(owner, "_parent_resolve", forbidden)
    coordinates = {"run_id": 37_000, "initialization_index": 0}
    coordinates[coordinate_name] = bad
    try:
        with pytest.raises((TypeError, ValueError)):
            owner.coordinate(
                coordinates["run_id"],
                coordinates["initialization_index"],
            )
    finally:
        coordination._CP38_RESOLVE = original_global
        object.__setattr__(owner, "_parent_resolve", original_owner)
    assert calls == {"resolve": 0}


def test_result_request_binding_wrong_types_and_foreign_intensity_fail_closed(
    live_bundle,
):
    owner = live_bundle["coordination_owner"]
    result = live_bundle["coordination_result"]
    with pytest.raises(TypeError, match="wrong exact"):
        owner.validate_result(object(), result.run_id, result.initialization_index)
    with pytest.raises(ValueError, match="request coordinates"):
        owner.validate_result(result, result.run_id + 1, result.initialization_index)

    foreign_intensity = _forged(
        result.initial_intensity,
        process_parameter_key=("foreign-process",),
    )
    foreign_sha256 = coordination._intensity_sha256(
        foreign_intensity,
        manifest=result.certificate.manifest,
    )
    values = {name: getattr(result, name) for name in coordination._result_fields()}
    values["initial_intensity"] = foreign_intensity
    values["initial_intensity_sha256"] = foreign_sha256
    values["result_sha256"] = "0" * 64
    values["result_sha256"] = coordination._SEMANTIC_DIGEST(
        coordination._result_payload(values)
    )
    forged = _forged(result, **values)
    with pytest.raises(ValueError, match="different process"):
        owner.validate_result(forged, result.run_id, result.initialization_index)


def test_redigested_parent_record_word_and_sequence_splices_fail_closed(live_bundle):
    owner = live_bundle["coordination_owner"]
    result = live_bundle["coordination_result"]
    occurrence = result.occurrence_payloads[0]
    stream = occurrence.tag3_stream

    parent_splice = _redigested(
        result,
        coordination._result_fields,
        coordination._result_payload,
        "result_sha256",
        parent_finite_batch_law_result=live_bundle["result"],
        parent_finite_batch_law_result_sha256=live_bundle["result"].result_sha256,
    )
    with pytest.raises(ValueError, match="selected configuration identity"):
        owner.validate_result(
            parent_splice,
            result.run_id,
            result.initialization_index,
        )

    words = (stream.raw64_words[0] ^ 1,) + stream.raw64_words[1:]
    word_stream = _redigested(
        stream,
        coordination._stream_fields,
        coordination._stream_payload,
        "stream_sha256",
        raw64_words=words,
        raw64_words_sha256=coordination._SEMANTIC_DIGEST({"raw64_words": words}),
    )
    word_occurrence = _redigested(
        occurrence,
        coordination._occurrence_fields,
        coordination._occurrence_payload,
        "record_sha256",
        tag3_stream=word_stream,
        tag3_stream_sha256=word_stream.stream_sha256,
    )
    word_result = _redigested(
        result,
        coordination._result_fields,
        coordination._result_payload,
        "result_sha256",
        occurrence_payloads=(word_occurrence,),
        occurrence_payload_sha256s=(word_occurrence.record_sha256,),
    )
    with pytest.raises(ValueError, match="prefix did not replay"):
        owner.validate_result(
            word_result,
            result.run_id,
            result.initialization_index,
        )

    duplicate_result = _redigested(
        result,
        coordination._result_fields,
        coordination._result_payload,
        "result_sha256",
        tag3_raw64_word_counts=(stream.raw64_word_count,) * 2,
        occurrence_payloads=(occurrence, occurrence),
        occurrence_payload_sha256s=(occurrence.record_sha256,) * 2,
        tag3_address_sha256s=(occurrence.tag3_address_sha256,) * 2,
        qualified_lineage_coordinates=(occurrence.qualified_lineage_coordinate,) * 2,
        stream_count=2,
        total_raw64_words=2 * stream.raw64_word_count,
    )
    with pytest.raises(ValueError, match="addresses are not unique|coordinates"):
        owner.validate_result(
            duplicate_result,
            result.run_id,
            result.initialization_index,
        )


@pytest.mark.parametrize(
    "updates",
    (
        {"stream_count": True},
        {"total_raw64_words": True},
        {"occurrence_payloads": (object(),) * 65},
        {"tag3_raw64_word_counts": (1,) * 65},
    ),
)
def test_result_resource_and_exact_integer_preflight_is_shallow_and_bounded(
    live_bundle,
    updates,
):
    owner = live_bundle["coordination_owner"]
    result = live_bundle["coordination_result"]
    forged = _forged(result, **updates)
    with pytest.raises((TypeError, ValueError)):
        coordination._preflight_result_record(
            forged,
            certificate=owner.certificate,
        )


def test_inflated_nested_counts_refuse_before_raw_word_traversal(live_bundle):
    owner = live_bundle["coordination_owner"]
    result = live_bundle["coordination_result"]
    occurrence = result.occurrence_payloads[0]
    stream = occurrence.tag3_stream
    inflated_stream = _forged(
        stream,
        raw64_word_count=4_096,
        raw64_words=(0,) * 4_096,
    )
    inflated_occurrence = _forged(
        occurrence,
        raw64_word_count=4_096,
        tag3_stream=inflated_stream,
    )
    forged = _forged(
        result,
        tag3_raw64_word_counts=(1_024,) * 64,
        occurrence_payloads=(inflated_occurrence,) * 64,
        occurrence_payload_sha256s=(inflated_occurrence.record_sha256,) * 64,
        tag3_address_sha256s=(inflated_occurrence.tag3_address_sha256,) * 64,
        qualified_lineage_coordinates=(
            inflated_occurrence.qualified_lineage_coordinate,
        )
        * 64,
        stream_count=64,
        total_raw64_words=65_536,
    )
    original_exact_integer = coordination._exact_integer
    calls = {"raw_word": 0}

    def counted_exact_integer(value, *, name, minimum=0, maximum=MAX_UINT64):
        if ".raw64_words[" in name:
            calls["raw_word"] += 1
        return original_exact_integer(
            value,
            name=name,
            minimum=minimum,
            maximum=maximum,
        )

    coordination._exact_integer = counted_exact_integer
    try:
        with pytest.raises(ValueError, match="count differs from its word plan"):
            coordination._preflight_result_record(
                forged,
                certificate=owner.certificate,
            )
    finally:
        coordination._exact_integer = original_exact_integer
    assert calls == {"raw_word": 0}


@pytest.mark.parametrize(
    "case",
    (
        "boolean-event-type-index",
        "boolean-event-coordinate",
        "non-binary64-event-coordinate",
        "boolean-lineage-limb",
    ),
)
def test_occurrence_key_and_lineage_coordinates_require_exact_scalars(
    live_bundle,
    case,
):
    owner = live_bundle["coordination_owner"]
    occurrence = live_bundle["coordination_result"].occurrence_payloads[0]
    event_type_index, event_coordinates = occurrence.event_model_key
    assert event_coordinates
    if case == "boolean-event-type-index":
        updates = {"event_model_key": (True, event_coordinates)}
    elif case == "boolean-event-coordinate":
        updates = {
            "event_model_key": (
                event_type_index,
                (True,) + event_coordinates[1:],
            )
        }
    elif case == "non-binary64-event-coordinate":
        updates = {
            "event_model_key": (
                event_type_index,
                (np.float64(event_coordinates[0]),) + event_coordinates[1:],
            )
        }
    else:
        coordinate = occurrence.qualified_lineage_coordinate
        updates = {"qualified_lineage_coordinate": coordinate[:-1] + (True,)}
    forged = _forged(occurrence, **updates)
    with pytest.raises(TypeError):
        coordination._validate_occurrence(forged, certificate=owner.certificate)


def test_foreign_lineaged_occurrence_identity_refuses_before_hostile_equality(
    live_bundle,
):
    owner = live_bundle["coordination_owner"]
    result = live_bundle["coordination_result"]
    record = result.occurrence_payloads[0]
    bomb = _EqualityBomb()
    foreign_occurrence = _forged(
        record.lineaged_occurrence,
        occurrence_sha256=bomb,
    )
    assert type(foreign_occurrence) is type(record.lineaged_occurrence)
    foreign_record = _forged(
        record,
        lineaged_occurrence=foreign_occurrence,
    )
    forged = _forged(result, occurrence_payloads=(foreign_record,))
    with pytest.raises(ValueError, match="occurrence position or identity"):
        owner.validate_result(forged, result.run_id, result.initialization_index)
    assert bomb.calls == 0


@pytest.mark.parametrize(
    "field", ("tag3_address_sha256s", "qualified_lineage_coordinates")
)
def test_hostile_unhashable_sequence_cells_fail_before_hash_or_set_traversal(
    live_bundle,
    field,
):
    owner = live_bundle["coordination_owner"]
    result = live_bundle["coordination_result"]
    bomb = _HashBomb()
    update = (bomb,)
    if field == "qualified_lineage_coordinates":
        update = ((result.run_id, result.initialization_index, 0, bomb),)
    forged = _forged(result, **{field: update})
    with pytest.raises((TypeError, ValueError)):
        owner.validate_result(forged, result.run_id, result.initialization_index)
    assert bomb.calls == 0


def test_owner_callback_identity_certificate_and_transitive_ancestry_tamper_refuse(
    live_bundle,
):
    owner = live_bundle["coordination_owner"]
    snapshot = owner._owner_snapshot()
    error_type = COORDINATION_ERROR
    with pytest.raises(ValueError, match="seal"):
        _forge_owner(owner, _sealed=False)._owner_snapshot()
    with pytest.raises(ValueError, match="cached callback"):
        _forge_owner(owner, _stream_builder=lambda *args: None)._owner_snapshot()
    with pytest.raises(ValueError, match="identity changed"):
        _forge_owner(owner, _reference_composer=object())._owner_snapshot()
    with pytest.raises(
        error_type,
        match="changed during operation",
    ):
        owner._require_owner_snapshot(snapshot[:-1] + (object(),))

    original_surface = coordination._make_stream
    coordination._make_stream = lambda *args: None
    try:
        with pytest.raises(ValueError, match="operation surface"):
            owner._owner_snapshot()
    finally:
        coordination._make_stream = original_surface

    certificate = owner.certificate
    original_passed = certificate.passed
    object.__setattr__(certificate, "passed", False)
    try:
        with pytest.raises((TypeError, ValueError)):
            owner._live_certificate(snapshot)
    finally:
        object.__setattr__(certificate, "passed", original_passed)

    lineage_owner = owner._checkpoint23_owner
    original_composer = lineage_owner._reference_composer
    object.__setattr__(lineage_owner, "_reference_composer", object())
    try:
        with pytest.raises((TypeError, ValueError)):
            owner._live_certificate(snapshot)
    finally:
        object.__setattr__(lineage_owner, "_reference_composer", original_composer)
    assert owner._live_certificate(snapshot) is certificate


def test_live_owner_swap_during_validation_is_detected_and_custody_recovers(
    live_bundle,
):
    owner = live_bundle["coordination_owner"]
    result = live_bundle["coordination_result"]
    original_preflight = coordination._COMPOSER_TYPE.preflight_candidate_intensity
    original_manifest = owner._manifest
    error_type = COORDINATION_ERROR

    def mutating_preflight(composer, state, *, reverse_time):
        checked = original_preflight(
            composer,
            state,
            reverse_time=reverse_time,
        )
        object.__setattr__(owner, "_manifest", object())
        return checked

    coordination._COMPOSER_TYPE.preflight_candidate_intensity = mutating_preflight
    try:
        with pytest.raises(
            (
                ValueError,
                error_type,
            )
        ):
            owner.validate_result(result, result.run_id, result.initialization_index)
    finally:
        object.__setattr__(owner, "_manifest", original_manifest)
        coordination._COMPOSER_TYPE.preflight_candidate_intensity = original_preflight
    snapshot = owner._owner_snapshot()
    assert owner._live_certificate(snapshot) is owner.certificate


def test_persistent_route_state_mutation_during_validation_fails_closed(live_bundle):
    owner = live_bundle["coordination_owner"]
    result = live_bundle["coordination_result"]
    stream = result.occurrence_payloads[0].tag3_stream
    initial_state = stream.initial_state
    original_counter = initial_state.counter
    original_preflight = coordination._COMPOSER_TYPE.preflight_candidate_intensity
    calls = {"mutate": 0}

    def mutating_preflight(composer, state, *, reverse_time):
        checked = original_preflight(
            composer,
            state,
            reverse_time=reverse_time,
        )
        calls["mutate"] += 1
        object.__setattr__(
            initial_state,
            "counter",
            (original_counter[0] ^ 1,) + original_counter[1:],
        )
        return checked

    coordination._COMPOSER_TYPE.preflight_candidate_intensity = mutating_preflight
    try:
        with pytest.raises((TypeError, ValueError)):
            owner.validate_result(result, result.run_id, result.initialization_index)
    finally:
        object.__setattr__(initial_state, "counter", original_counter)
        coordination._COMPOSER_TYPE.preflight_candidate_intensity = original_preflight
    assert calls == {"mutate": 1}
    assert (
        coordination._validate_stream(
            stream,
            certificate=owner.certificate,
        )
        is stream
    )


@pytest.mark.parametrize(
    "surface",
    ("certificate", "address", "stream", "occurrence", "result", "owner"),
)
def test_records_and_owner_are_immutable_nonpickle_and_nonsubclassable(
    live_bundle,
    surface,
):
    owner = live_bundle["coordination_owner"]
    result = live_bundle["coordination_result"]
    occurrence = result.occurrence_payloads[0]
    values = {
        "certificate": owner.certificate,
        "address": occurrence.tag3_stream.address,
        "stream": occurrence.tag3_stream,
        "occurrence": occurrence,
        "result": result,
        "owner": owner,
    }
    value = values[surface]
    with pytest.raises((AttributeError, TypeError)):
        value.passed = False
    with pytest.raises(TypeError, match="pickle"):
        pickle.dumps(value)
    with pytest.raises(TypeError):
        type("ForbiddenSubclass", (type(value),), {})


def test_public_record_constructors_are_token_sealed():
    for cls in (
        coordination.CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
        coordination.CounterKeyedInitializationIndexedTag3Address,
        coordination.CounterKeyedInitializationIndexedTag3Stream,
        coordination.CounterKeyedInitialTiltRejectionOccurrencePayload,
        coordination.CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult,
    ):
        with pytest.raises(TypeError, match="module-created"):
            cls(_construction_token=object())


def test_source_ast_parent_resolve_once_and_validation_avoids_child_construction():
    source_path = Path(coordination.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert "random" not in imported_roots
    assert "torch" not in imported_roots
    owner_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner"
    )
    coordinate_method = next(
        node
        for node in owner_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "coordinate"
    )
    validate_method = next(
        node
        for node in owner_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "validate_result"
    )
    resolve_calls = [
        node
        for node in ast.walk(coordinate_method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_parent_resolve"
    ]
    assert len(resolve_calls) == 1
    coordinate_source = ast.get_source_segment(source, coordinate_method)
    assert coordinate_source is not None
    assert "parent.selected_attempt_index" in coordinate_source
    assert "selected_configuration_ordinal" not in coordinate_source
    outcome_branch = next(
        node
        for node in ast.walk(coordinate_method)
        if isinstance(node, ast.If)
        and "parent.outcome" in (ast.get_source_segment(source, node.test) or "")
        and "exhausted" in (ast.get_source_segment(source, node.test) or "")
    )

    def called_attributes(nodes):
        return {
            node.func.attr
            for root in nodes
            for node in ast.walk(root)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }

    selected_state_builders = {
        "_configuration_preflight",
        "_composer_preflight",
        "_lineage_bootstrap",
        "_lineage_binding_checker",
        "_word_planner",
        "_address_builder",
        "_stream_builder",
        "_occurrence_builder",
    }
    assert selected_state_builders.isdisjoint(called_attributes(outcome_branch.body))
    assert selected_state_builders <= called_attributes(outcome_branch.orelse)
    assert not any(
        isinstance(parent, (ast.For, ast.While))
        and resolve_calls[0] in set(ast.walk(parent))
        for parent in ast.walk(coordinate_method)
    )
    validation_calls = {
        node.func.attr
        for node in ast.walk(validate_method)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert {
        "_parent_resolve",
        "_composer_preflight",
        "_lineage_bootstrap",
        "_stream_builder",
        "decide",
        "prepare",
        "bootstrap_lineage",
        "consume",
        "initialize",
    }.isdisjoint(validation_calls)
    assert ".consume(" not in source
    assert ".initialize(" not in source
    assert "default_rng" not in source


def test_module_is_not_reexported_from_dependency_light_process_package():
    import heterodiff.processes as processes

    assert not hasattr(
        processes,
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_lineage_"
        "tag3_coordination",
    )


def test_optional_torch_boundary_translates_dependency_failure():
    source = textwrap.dedent(
        """
        import builtins
        original_import = builtins.__import__
        def guarded_import(name, *args, **kwargs):
            if name == 'torch' or name.startswith('torch.'):
                raise ModuleNotFoundError("No module named 'torch'", name='torch')
            return original_import(name, *args, **kwargs)
        builtins.__import__ = guarded_import
        try:
            __import__(
                "heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_"
                "rejection_lineage_tag3_coordination"
            )
        except ModuleNotFoundError as error:
            assert "optional PyTorch reference dependency" in str(error)
            assert error.name is None
        else:
            raise AssertionError("missing optional dependency was not translated")
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", source],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
