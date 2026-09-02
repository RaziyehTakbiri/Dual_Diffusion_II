"""Hostile tests for checkpoint-28 finite reference initialization."""

import ast
import copy
from fractions import Fraction
import importlib
import inspect
import math
from pathlib import Path
import pickle
import subprocess
import sys

import numpy as np
import pytest


pytest.importorskip(
    "torch", reason="counter-keyed reference initialization requires PyTorch"
)

checkpoint22_tests = importlib.import_module(
    "test_plugin_bridge_operational_thinning_loop_route_evidence"
)
checkpoint24_tests = importlib.import_module(
    "test_plugin_bridge_counter_keyed_operational_epoch_loop"
)
checkpoint25_tests = importlib.import_module(
    "test_plugin_bridge_counter_keyed_initializer_stream_consumption"
)
checkpoint26_tests = importlib.import_module(
    "test_plugin_bridge_counter_keyed_global_initializer_control"
)
checkpoint27_tests = importlib.import_module(
    "test_plugin_bridge_counter_keyed_initializer_protocol"
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initializer_protocol as protocol,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_reference_initializer as initializer,
)
from heterodiff.theory.configuration_reference import (  # noqa: E402
    CappedPoissonConfigurationReference,
    TransformedEvent,
)


INITIALIZER_ROLE = "9" * 64
INITIALIZER_POLICY = (
    initializer.PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_POLICY
)
UINT64_DENOMINATOR = 1 << 64


def _certify(protocol_owner, *, role=INITIALIZER_ROLE):
    return initializer.certify_plugin_bridge_counter_keyed_reference_initializer(
        protocol_owner,
        initializer_policy=INITIALIZER_POLICY,
        initializer_role_sha256=role,
    )


def _extend_from_consumption(bundle):
    bundle["control_owner"] = checkpoint26_tests._certify_control(
        bundle["consumption_owner"]
    )
    bundle["protocol_owner"] = checkpoint27_tests._certify(bundle["control_owner"])
    bundle["initializer_owner"] = _certify(bundle["protocol_owner"])
    return bundle


@pytest.fixture(scope="module")
def atomic_bundle():
    bundle = checkpoint25_tests._certified_bundle(total_cap=2)
    _extend_from_consumption(bundle)
    bundle["alien_initializer_owner"] = _certify(bundle["protocol_owner"])
    return bundle


@pytest.fixture(scope="module")
def continuous_bundle():
    # Start with the checkpoint-22 continuous (dimensions 2 and 3) bundle.
    # The checkpoint-24 helper certifies checkpoints 23 and 24 in sequence.
    bundle = checkpoint24_tests._certify_epoch(checkpoint22_tests._bundle(tight=True))
    bundle["consumption_owner"] = checkpoint25_tests._certify_consumption(
        bundle["epoch_owner"],
        consumption_policy=checkpoint25_tests.CONSUMPTION_POLICY,
        consumption_role_sha256=checkpoint25_tests.CONSUMPTION_ROLE,
    )
    return _extend_from_consumption(bundle)


def _raw_words(manifest, *, run_id, initialization_index):
    blocks = []
    for attempt_index, word_count in enumerate(
        manifest.canonical_block_raw64_word_counts
    ):
        block, _ = checkpoint26_tests._direct_prefix(
            run_id=run_id,
            initialization_index=initialization_index,
            stage_index=protocol.INITIALIZER_STAGE_REFERENCE_CANDIDATE,
            attempt_index=attempt_index,
            word_count=word_count,
        )
        blocks.append(block)
    return tuple(word for block in blocks for word in block)


def _find_initialization(manifest, predicate, *, run_id):
    for initialization_index in range(4_096):
        words = _raw_words(
            manifest,
            run_id=run_id,
            initialization_index=initialization_index,
        )
        cardinality = initializer._quota_position(
            words[manifest.count_word_offset],
            manifest.count_cumulative_ends,
        )
        type_positions = tuple(
            initializer._quota_position(
                words[manifest.type_segment_offset + raw_slot],
                manifest.type_cumulative_ends,
            )
            for raw_slot in range(manifest.total_cap)
        )
        if predicate(cardinality, type_positions):
            return run_id, initialization_index, words
    raise AssertionError("a deterministic initializer fixture was not found")


@pytest.fixture(scope="module")
def atomic_results(atomic_bundle):
    owner = atomic_bundle["initializer_owner"]
    partial_coordinates = _find_initialization(
        owner.manifest,
        lambda cardinality, positions: cardinality == 1,
        run_id=28_000,
    )
    duplicate_coordinates = _find_initialization(
        owner.manifest,
        lambda cardinality, positions: (
            cardinality == 2 and positions[0] == positions[1]
        ),
        run_id=28_001,
    )
    return {
        "partial": owner.initialize(*partial_coordinates[:2]),
        "partial_expected_words": partial_coordinates[2],
        "duplicate": owner.initialize(*duplicate_coordinates[:2]),
        "duplicate_expected_words": duplicate_coordinates[2],
    }


@pytest.fixture(scope="module")
def continuous_results(continuous_bundle):
    owner = continuous_bundle["initializer_owner"]
    active_coordinates = _find_initialization(
        owner.manifest,
        lambda cardinality, positions: cardinality == 1 and positions == (0,),
        run_id=28_100,
    )
    inactive_coordinates = _find_initialization(
        owner.manifest,
        lambda cardinality, positions: cardinality == 0,
        run_id=28_101,
    )
    return {
        "active": owner.initialize(*active_coordinates[:2]),
        "active_expected_words": active_coordinates[2],
        "inactive": owner.initialize(*inactive_coordinates[:2]),
        "inactive_expected_words": inactive_coordinates[2],
    }


def _forged(value, **updates):
    forged = object.__new__(type(value))
    for name in type(value).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(value, name)))
    return forged


def _manifest_values(manifest, **updates):
    values = {
        name: updates.get(name, getattr(manifest, name))
        for name in initializer._manifest_fields()
    }
    values["manifest_sha256"] = "0" * 64
    values["manifest_sha256"] = protocol._thinning._semantic_digest(
        initializer._manifest_payload(values)
    )
    return values


def _certificate_values(certificate, **updates):
    values = {
        name: updates.get(name, getattr(certificate, name))
        for name in initializer._certificate_fields()
    }
    values["certificate_sha256"] = "0" * 64
    values["certificate_sha256"] = protocol._thinning._semantic_digest(
        initializer._certificate_payload(values)
    )
    return values


def _slot_values(slot, **updates):
    values = {
        name: updates.get(name, getattr(slot, name))
        for name in initializer._slot_fields()
    }
    if "event" in updates and "event_sha256" not in updates:
        values["event_sha256"] = initializer._event_sha256(values["event"])
    values["slot_sha256"] = "0" * 64
    values["slot_sha256"] = protocol._thinning._semantic_digest(
        initializer._slot_payload(values)
    )
    return values


def _result_values(result, **updates):
    values = {
        name: updates.get(name, getattr(result, name))
        for name in initializer._result_fields()
    }
    if "certificate" in updates and "certificate_sha256" not in updates:
        values["certificate_sha256"] = values["certificate"].certificate_sha256
    if "manifest" in updates and "manifest_sha256" not in updates:
        values["manifest_sha256"] = values["manifest"].manifest_sha256
    if "parent_protocol_result" in updates and "parent_result_sha256" not in updates:
        values["parent_result_sha256"] = values["parent_protocol_result"].result_sha256
    if "raw_slots" in updates and "raw_slot_sha256s" not in updates:
        values["raw_slot_sha256s"] = tuple(
            slot.slot_sha256 for slot in values["raw_slots"]
        )
    if "selected_raw_events" in updates and "selected_raw_event_sha256s" not in updates:
        values["selected_raw_event_sha256s"] = tuple(
            initializer._event_sha256(event) for event in values["selected_raw_events"]
        )
    if (
        "canonical_configuration" in updates
        and "canonical_configuration_sha256" not in updates
    ):
        values["canonical_configuration_sha256"] = initializer._configuration_sha256(
            values["canonical_configuration"]
        )
    values["result_sha256"] = "0" * 64
    values["result_sha256"] = protocol._thinning._semantic_digest(
        initializer._result_payload(values)
    )
    return values


def _fraction_ratios(ratios):
    return tuple(Fraction(numerator, denominator) for numerator, denominator in ratios)


def _assert_exact_quota_evidence(target, quotas, cumulative, tv_pair):
    assert target
    assert sum(target, Fraction(0)) == 1
    assert len(target) == len(quotas) == len(cumulative)
    assert all(quota > 0 for quota in quotas)
    assert sum(quotas) == UINT64_DENOMINATOR
    assert cumulative == tuple(np.cumsum(quotas, dtype=object))
    represented = tuple(Fraction(quota, UINT64_DENOMINATOR) for quota in quotas)
    expected_tv = (
        sum(
            (abs(left - right) for left, right in zip(target, represented)),
            Fraction(0),
        )
        / 2
    )
    assert Fraction(*tv_pair) == expected_tv


def test_manifest_records_exact_binary64_induced_laws_quotas_tv_and_layout(
    atomic_bundle,
):
    owner = atomic_bundle["initializer_owner"]
    manifest = owner.manifest
    reference = owner.manifest.reference

    activity = Fraction.from_float(reference.activity)
    count_weights = (Fraction(1), activity, activity * activity / 2)
    count_total = sum(count_weights, Fraction(0))
    count_target = tuple(weight / count_total for weight in count_weights)
    type_weights = tuple(
        Fraction.from_float(reference.type_weights[type_id])
        for type_id in reference.type_ids
    )
    type_total = sum(type_weights, Fraction(0))
    type_target = tuple(weight / type_total for weight in type_weights)

    assert _fraction_ratios(manifest.count_target_probability_ratios) == (count_target)
    assert _fraction_ratios(manifest.type_target_probability_ratios) == type_target
    _assert_exact_quota_evidence(
        count_target,
        manifest.count_dyadic_quotas,
        manifest.count_cumulative_ends,
        (
            manifest.count_quantization_tv_numerator,
            manifest.count_quantization_tv_denominator,
        ),
    )
    _assert_exact_quota_evidence(
        type_target,
        manifest.type_dyadic_quotas,
        manifest.type_cumulative_ends,
        (
            manifest.type_quantization_tv_numerator,
            manifest.type_quantization_tv_denominator,
        ),
    )
    assert manifest.count_word_offset == 0
    assert manifest.type_segment_offset == 1
    assert manifest.coordinate_segment_offset == 1 + manifest.total_cap
    assert manifest.coordinate_row_stride == manifest.maximum_coordinate_dimension
    assert manifest.required_raw64_words == 1 + manifest.total_cap * (
        1 + manifest.maximum_coordinate_dimension
    )
    assert manifest.canonical_block_raw64_word_counts == (
        manifest.required_raw64_words,
    )
    assert manifest.reference is reference
    assert manifest.reference_parameter_key == reference.parameter_key()


@pytest.mark.parametrize(
    "table_name", ["count_cumulative_ends", "type_cumulative_ends"]
)
def test_every_integer_quota_boundary_has_the_declared_category(
    atomic_bundle,
    table_name,
):
    cumulative = getattr(atomic_bundle["initializer_owner"].manifest, table_name)
    start = 0
    for position, endpoint in enumerate(cumulative):
        assert initializer._quota_position(start, cumulative) == position
        assert initializer._quota_position(endpoint - 1, cumulative) == position
        if endpoint < UINT64_DENOMINATOR:
            assert initializer._quota_position(endpoint, cumulative) == position + 1
        start = endpoint


@pytest.mark.parametrize("word", [True, np.uint64(0), -1, UINT64_DENOMINATOR])
def test_categorical_transform_refuses_nonexact_or_out_of_range_words(
    atomic_bundle,
    word,
):
    cumulative = atomic_bundle["initializer_owner"].manifest.type_cumulative_ends
    with pytest.raises((TypeError, ValueError)):
        initializer._quota_position(word, cumulative)


@pytest.mark.parametrize(
    "cumulative,exception,match",
    [
        ([UINT64_DENOMINATOR], TypeError, "exact tuple"),
        ((0, UINT64_DENOMINATOR), ValueError, "strictly increasing"),
        ((1, UINT64_DENOMINATOR - 1), ValueError, "cover"),
        ((True, UINT64_DENOMINATOR), TypeError, "exact integer"),
    ],
)
def test_categorical_transform_preflights_hostile_tables(
    cumulative,
    exception,
    match,
):
    with pytest.raises(exception, match=match):
        initializer._quota_position(0, cumulative)


def test_top53_midpoint_transform_endpoints_and_central_symmetry():
    maximum = UINT64_DENOMINATOR - 1
    lower = initializer._coordinate_transform_details(0)
    upper = initializer._coordinate_transform_details(maximum)
    assert lower[0] == 0
    assert upper[0] == (1 << 53) - 1
    assert lower[1:3] == upper[1:3]
    assert lower[3] == -upper[3]
    assert lower[4] == (-upper[3]).hex()
    assert math.isfinite(lower[3]) and lower[3] < 0.0
    assert math.isfinite(upper[3]) and upper[3] > 0.0

    central_lower_word = ((1 << 52) - 1) << 11
    central_upper_word = (1 << 52) << 11
    central_lower = initializer._coordinate_transform_details(central_lower_word)
    central_upper = initializer._coordinate_transform_details(central_upper_word)
    assert central_lower[1:3] == central_upper[1:3]
    assert central_lower[3] == -central_upper[3]
    assert central_lower[3] != 0.0
    assert central_upper[3] != 0.0


def test_coordinate_transform_ignores_exactly_the_low_eleven_bits():
    base = 1_234_567 << 11
    expected = initializer._coordinate_transform_details(base)
    assert initializer._coordinate_transform_details(base + 1) == expected
    assert initializer._coordinate_transform_details(base + (1 << 11) - 1) == (expected)
    changed = initializer._coordinate_transform_details(base + (1 << 11))
    assert changed[0] == expected[0] + 1
    assert changed != expected


@pytest.mark.parametrize("word", [True, np.uint64(0), -1, UINT64_DENOMINATOR])
def test_coordinate_transform_refuses_nonexact_or_out_of_range_words(word):
    with pytest.raises((TypeError, ValueError)):
        initializer._coordinate_transform_details(word)


def test_atomic_initialization_consumes_exact_parent_layout_and_selects_prefix(
    atomic_bundle,
    atomic_results,
):
    owner = atomic_bundle["initializer_owner"]
    result = atomic_results["partial"]
    assert result.concatenated_raw64_words == atomic_results["partial_expected_words"]
    assert result.sampled_cardinality == 1
    assert result.total_raw64_words == owner.manifest.required_raw64_words == 3
    assert (
        result.parent_protocol_result.strategy
        == protocol.INITIALIZER_STRATEGY_REFERENCE
    )
    assert result.parent_protocol_result.strategy_budget == 1
    assert result.parent_protocol_result.selection_raw64_word_count == 0
    assert (
        result.raw64_blocks[0] is result.parent_protocol_result.entries[0].raw64_words
    )
    assert result.selected_raw_events[0] is result.raw_slots[0].event
    assert result.raw_slots[0].active is True
    assert result.raw_slots[1].active is False
    assert result.raw_slot_to_canonical_position[1] is None
    assert all(slot.event_dimension == 0 for slot in result.raw_slots)
    assert all(slot.coordinate_word_count == 0 for slot in result.raw_slots)
    assert owner.validate_result(
        result, result.run_id, result.initialization_index
    ) is (result)


def test_continuous_initialization_materializes_active_prefix_and_padding(
    continuous_bundle,
    continuous_results,
):
    owner = continuous_bundle["initializer_owner"]
    result = continuous_results["active"]
    slot = result.raw_slots[0]
    assert owner.manifest.type_dimensions == ((0, 2), (1, 3))
    assert owner.manifest.maximum_coordinate_dimension == 3
    assert owner.manifest.required_raw64_words == 5
    assert (
        result.concatenated_raw64_words == continuous_results["active_expected_words"]
    )
    assert result.sampled_cardinality == 1
    assert slot.active is True
    assert slot.event_type == 0
    assert slot.event_dimension == 2
    assert slot.coordinate_word_count == 3
    assert slot.active_coordinates == slot.coordinate_codebook_values[:2]
    assert slot.event.coordinates == slot.active_coordinates
    assert len(slot.coordinate_codebook_values[2:]) == 1
    assert slot.all_coordinate_padding_materialized is True
    for raw_word, evidence in zip(
        slot.coordinate_raw64_words,
        zip(
            slot.coordinate_bucket_indices,
            slot.coordinate_midpoint_numerators,
            slot.coordinate_probability_hexes,
            slot.coordinate_codebook_values,
            slot.coordinate_value_hexes,
        ),
    ):
        assert initializer._coordinate_transform_details(raw_word) == evidence


def test_zero_cardinality_still_materializes_every_continuous_raw_slot(
    continuous_results,
):
    result = continuous_results["inactive"]
    slot = result.raw_slots[0]
    assert (
        result.concatenated_raw64_words == continuous_results["inactive_expected_words"]
    )
    assert result.sampled_cardinality == 0
    assert slot.active is False
    assert slot.coordinate_word_count == 3
    assert len(slot.coordinate_raw64_words) == 3
    assert len(slot.coordinate_codebook_values) == 3
    assert result.selected_raw_events == ()
    assert result.canonical_configuration == ()
    assert result.canonical_position_to_raw_slot == ()
    assert result.raw_slot_to_canonical_position == (None,)


def test_duplicate_atomic_events_keep_stable_raw_slot_bijection(atomic_results):
    result = atomic_results["duplicate"]
    left, right = result.raw_slots
    assert result.concatenated_raw64_words == atomic_results["duplicate_expected_words"]
    assert result.sampled_cardinality == 2
    assert left.event == right.event
    assert left.event is not right.event
    assert left.event_sha256 == right.event_sha256
    assert result.canonical_position_to_raw_slot == (0, 1)
    assert result.raw_slot_to_canonical_position == (0, 1)
    assert result.selected_raw_events[0] is left.event
    assert result.selected_raw_events[1] is right.event
    assert result.canonical_configuration[0] is left.event
    assert result.canonical_configuration[1] is right.event


def test_reissue_is_deterministic_without_caller_or_global_rng(
    atomic_bundle,
    atomic_results,
):
    owner = atomic_bundle["initializer_owner"]
    first = atomic_results["partial"]
    caller = np.random.Generator(np.random.Philox(28))
    caller_before = copy.deepcopy(caller.bit_generator.state)
    legacy_before = np.random.get_state()
    second = owner.initialize(first.run_id, first.initialization_index)
    legacy_after = np.random.get_state()
    assert first is not second
    assert first.parent_protocol_result is not second.parent_protocol_result
    assert first.result_sha256 == second.result_sha256
    assert first.concatenated_raw64_words == second.concatenated_raw64_words
    assert first.canonical_configuration == second.canonical_configuration
    caller_after = caller.bit_generator.state
    assert caller_after["bit_generator"] == caller_before["bit_generator"]
    assert np.array_equal(
        caller_after["state"]["counter"], caller_before["state"]["counter"]
    )
    assert np.array_equal(caller_after["state"]["key"], caller_before["state"]["key"])
    assert np.array_equal(caller_after["buffer"], caller_before["buffer"])
    assert caller_after["buffer_pos"] == caller_before["buffer_pos"]
    assert caller_after["has_uint32"] == caller_before["has_uint32"]
    assert caller_after["uinteger"] == caller_before["uinteger"]
    assert legacy_before[0] == legacy_after[0]
    assert np.array_equal(legacy_before[1], legacy_after[1])
    assert legacy_before[2:] == legacy_after[2:]
    assert "rng" not in inspect.signature(owner.initialize).parameters
    assert "rng" not in inspect.signature(owner.validate_result).parameters


def test_cap_zero_and_cap_sixty_four_manifest_boundaries_are_exact():
    cap_zero = CappedPoissonConfigurationReference(
        {0: 0}, {0: 1.0}, activity=1.0, total_cap=0
    )
    zero_manifest = initializer._make_manifest(cap_zero)
    assert zero_manifest.total_cap == 0
    assert zero_manifest.count_target_probability_ratios == ((1, 1),)
    assert zero_manifest.count_dyadic_quotas == (UINT64_DENOMINATOR,)
    assert zero_manifest.count_cumulative_ends == (UINT64_DENOMINATOR,)
    assert zero_manifest.required_raw64_words == 1
    assert zero_manifest.canonical_block_raw64_word_counts == (1,)

    cap_sixty_four = CappedPoissonConfigurationReference(
        {0: 1_022}, {0: 1.0}, activity=1.0, total_cap=64
    )
    maximum_manifest = initializer._make_manifest(cap_sixty_four)
    assert maximum_manifest.total_cap == 64
    assert maximum_manifest.maximum_coordinate_dimension == 1_022
    assert maximum_manifest.required_raw64_words == 65_473
    assert len(maximum_manifest.canonical_block_raw64_word_counts) == 16
    assert maximum_manifest.canonical_block_raw64_word_counts[:-1] == (4_096,) * 15
    assert maximum_manifest.canonical_block_raw64_word_counts[-1] == 4_033
    assert sum(maximum_manifest.canonical_block_raw64_word_counts) == 65_473


def test_extreme_cap_sixty_four_manifest_avoids_decimal_integer_conversion():
    reference = CappedPoissonConfigurationReference(
        {0: 0},
        {0: 1.0},
        activity=float(np.finfo(np.float64).max),
        total_cap=64,
    )
    manifest = initializer._make_manifest(reference)
    assert len(manifest.count_target_probability_ratios) == 65
    assert len(manifest.count_dyadic_quotas) == 65
    assert sum(manifest.count_dyadic_quotas) == UINT64_DENOMINATOR
    assert manifest.required_raw64_words == 65
    assert len(manifest.manifest_sha256) == 64
    assert initializer._validate_manifest(manifest) is manifest


def test_manifest_helper_refuses_raw_slot_and_word_resource_overflow():
    too_many_slots = CappedPoissonConfigurationReference(
        {0: 0}, {0: 1.0}, activity=1.0, total_cap=65
    )
    with pytest.raises(ValueError, match="cap exceeds"):
        initializer._manifest_expected_values(too_many_slots)

    too_many_words = CappedPoissonConfigurationReference(
        {0: 1_023}, {0: 1.0}, activity=1.0, total_cap=64
    )
    with pytest.raises(ValueError, match="layout exceeds"):
        initializer._manifest_expected_values(too_many_words)

    assert initializer._canonical_word_blocks(65_536) == (4_096,) * 16
    for invalid in (0, 65_537):
        with pytest.raises(ValueError, match="outside"):
            initializer._canonical_word_blocks(invalid)
    with pytest.raises(TypeError, match="exact integer"):
        initializer._canonical_word_blocks(True)

    rational_bound = (
        initializer.COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS
    )
    assert (
        initializer._bounded_exact_rational_integer(
            (1 << rational_bound) - 1,
            name="boundary",
        ).bit_length()
        == rational_bound
    )
    with pytest.raises(ValueError, match="integer-bit bound"):
        initializer._bounded_exact_rational_integer(
            1 << rational_bound,
            name="overflow",
        )

    ratio_component = (1 << 2_048) - 1
    oversized_ratios = ((ratio_component, ratio_component),) * (
        initializer.COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES
    )
    with pytest.raises(ValueError, match="aggregate integer-bit bound"):
        initializer._preflight_probability_ratios(
            oversized_ratios,
            name="hostile ratios",
            exact_length=len(oversized_ratios),
        )


def test_certificate_freezes_parent_manifest_truth_matrix_and_nonclaims(
    atomic_bundle,
):
    owner = atomic_bundle["initializer_owner"]
    certificate = owner.certificate
    parent = atomic_bundle["protocol_owner"].certificate
    assert certificate.checkpoint27_certificate is parent
    assert certificate.manifest is owner.manifest
    assert certificate.checkpoint27_certificate_sha256 == parent.certificate_sha256
    assert certificate.checkpoint27_role_sha256 == parent.protocol_role_sha256
    assert certificate.manifest_sha256 == owner.manifest.manifest_sha256
    assert certificate.reference_parameter_sha256 == (
        owner.manifest.reference_parameter_sha256
    )
    assert certificate.maximum_exact_rational_integer_bits == 131_072
    assert certificate.maximum_exact_rational_aggregate_bits == 16_777_216

    positive = {
        "exact_checkpoint27_owner_binding_certified",
        "ancestry_derived_reference_binding_certified",
        "sealed_reference_manifest_certified",
        "canonical_fixed_word_layout_certified",
        "canonical_parent_block_partition_certified",
        "positive_dyadic_count_quotas_certified",
        "positive_dyadic_type_quotas_certified",
        "exact_target_probability_tv_recorded",
        "finite_coordinate_codebook_transform_certified",
        "complete_raw_slot_materialization_certified",
        "duplicate_stable_canonical_mapping_certified",
        "finite_configuration_output_certified",
        "hypothetical_product_uniform_pushforward_defined",
        "exact_parent_result_replay_certified",
        "no_caller_rng_certified",
        "fixed_cost_no_retry_reference_transform_certified",
    }
    for name in initializer.CounterKeyedReferenceInitializerCertificate.__annotations__:
        if (
            name.endswith("certified")
            or name.endswith("defined")
            or name.endswith("recorded")
            or name.endswith("admissible")
        ):
            assert getattr(certificate, name) is (name in positive)
    assert certificate.passed is True
    assert certificate.analytic_target_preserved is False
    assert certificate.runtime_portable is False
    assert certificate.cryptographic_authentication is False


def test_positive_and_negative_certificate_claim_forgeries_are_refused(
    atomic_bundle,
):
    certificate = atomic_bundle["initializer_owner"].certificate
    with pytest.raises(ValueError, match="positive claim"):
        initializer.CounterKeyedReferenceInitializerCertificate(
            **_certificate_values(
                certificate,
                finite_configuration_output_certified=False,
            ),
            _construction_token=initializer._CERTIFICATE_TOKEN,
        )
    with pytest.raises(ValueError, match="negative claim"):
        initializer.CounterKeyedReferenceInitializerCertificate(
            **_certificate_values(
                certificate,
                exact_continuous_gaussian_law_certified=True,
            ),
            _construction_token=initializer._CERTIFICATE_TOKEN,
        )


@pytest.mark.parametrize(
    "update,match",
    [
        ({"type_ids": (0, 0)}, "strictly increasing"),
        ({"count_dyadic_quotas": (0, 1, UINT64_DENOMINATOR - 1)}, "positive"),
        ({"count_quantization_tv_denominator": 0}, "TV ratio"),
        ({"required_raw64_words": 4}, "field required_raw64_words"),
        ({"coordinate_row_stride": 1}, "field coordinate_row_stride"),
    ],
)
def test_manifest_structural_and_semantic_forgeries_are_refused(
    atomic_bundle,
    update,
    match,
):
    manifest = atomic_bundle["initializer_owner"].manifest
    forged = _forged(manifest, **_manifest_values(manifest, **update))
    with pytest.raises(ValueError, match=match):
        initializer._validate_manifest(forged)


def test_coordinate_word_forgery_has_transform_and_parent_custody_defenses(
    continuous_results,
):
    result = continuous_results["active"]
    slot = result.raw_slots[0]
    changed_words = (slot.coordinate_raw64_words[0] ^ (1 << 20),) + (
        slot.coordinate_raw64_words[1:]
    )
    forged_slot = _forged(
        slot,
        **_slot_values(slot, coordinate_raw64_words=changed_words),
    )
    with pytest.raises(ValueError, match="coordinate transform evidence"):
        initializer._validate_slot_record(forged_slot)

    collision_words = (slot.coordinate_raw64_words[0] ^ 1,) + (
        slot.coordinate_raw64_words[1:]
    )
    collision_slot = _forged(
        slot,
        **_slot_values(slot, coordinate_raw64_words=collision_words),
    )
    initializer._validate_slot_record(collision_slot)
    forged_result = _forged(
        result,
        **_result_values(result, raw_slots=(collision_slot,)),
    )
    with pytest.raises(ValueError, match="coordinate words"):
        initializer._validate_result_record(forged_result)


def test_detached_equal_selected_event_is_refused_by_identity(atomic_results):
    result = atomic_results["partial"]
    event = result.selected_raw_events[0]
    detached = TransformedEvent(event.event_type, event.coordinates)
    assert detached == event and detached is not event
    forged = _forged(
        result,
        **_result_values(result, selected_raw_events=(detached,)),
    )
    with pytest.raises(ValueError, match="selected-event identity"):
        initializer._validate_result_record(forged)


def test_hostile_event_and_digest_elements_are_typed_before_equality(
    atomic_bundle,
    atomic_results,
):
    class HostileEquality:
        def __eq__(self, other):
            del other
            raise AssertionError("hostile equality must not run")

        def __ne__(self, other):
            del other
            raise AssertionError("hostile equality must not run")

    slot = atomic_results["partial"].raw_slots[0]
    hostile_event = object.__new__(TransformedEvent)
    object.__setattr__(hostile_event, "event_type", HostileEquality())
    object.__setattr__(hostile_event, "coordinates", ())
    forged_slot = _forged(slot, event=hostile_event)
    with pytest.raises(TypeError, match="exact integer"):
        initializer._validate_slot_record(forged_slot)

    manifest = atomic_bundle["initializer_owner"].manifest
    payload_values = {
        name: getattr(manifest, name) for name in initializer._manifest_fields()
    }
    ratios = list(payload_values["count_target_probability_ratios"])
    ratios[0] = (HostileEquality(), ratios[0][1])
    payload_values["count_target_probability_ratios"] = tuple(ratios)
    with pytest.raises(TypeError, match="exact integer"):
        initializer._manifest_payload(payload_values)


@pytest.mark.parametrize(
    "field,match",
    [
        ("type_word_offset", "type-word offset"),
        ("type_quota_position", "quota position"),
        ("coordinate_word_offsets", "coordinate offset"),
    ],
)
def test_slot_offsets_and_quota_positions_are_bounded_before_digesting(
    atomic_results,
    field,
    match,
):
    slot = atomic_results["partial"].raw_slots[0]
    huge = 1 << 200_000
    updates = {field: huge}
    if field == "coordinate_word_offsets":
        (
            bucket,
            numerator,
            probability_hex,
            value,
            value_hex,
        ) = initializer._coordinate_transform_details(0)
        updates = {
            "coordinate_word_count": 1,
            "coordinate_word_offsets": (huge,),
            "coordinate_raw64_words": (0,),
            "coordinate_bucket_indices": (bucket,),
            "coordinate_midpoint_numerators": (numerator,),
            "coordinate_probability_hexes": (probability_hex,),
            "coordinate_codebook_values": (value,),
            "coordinate_value_hexes": (value_hex,),
        }
    forged_slot = _forged(slot, **updates)
    with pytest.raises(ValueError, match=match):
        initializer._validate_slot_record(forged_slot)


def test_detached_equal_parent_raw_block_is_refused_by_identity(atomic_results):
    result = atomic_results["partial"]
    detached = tuple(list(result.raw64_blocks[0]))
    assert detached == result.raw64_blocks[0]
    assert detached is not result.raw64_blocks[0]
    forged = _forged(
        result,
        **_result_values(result, raw64_blocks=(detached,)),
    )
    with pytest.raises(ValueError, match="raw-block identity"):
        initializer._validate_result_record(forged)


@pytest.mark.parametrize(
    "update,match",
    [
        ({"sampled_cardinality": 0}, "cardinality transform"),
        ({"canonical_position_to_raw_slot": (1, 0)}, "canonical-to-raw"),
        ({"raw_slot_to_canonical_position": (1, 0)}, "raw-to-canonical"),
        (
            {"all_raw_slot_transforms_completed_before_cardinality_decoding": False},
            "flag",
        ),
        ({"finite_product_uniform_pushforward_only": False}, "flag"),
        ({"no_caller_rng": False}, "flag"),
    ],
)
def test_result_counts_maps_and_nonclaim_flags_are_not_self_attested(
    atomic_results,
    update,
    match,
):
    result = atomic_results["duplicate"]
    forged = _forged(result, **_result_values(result, **update))
    with pytest.raises(ValueError, match=match):
        initializer._validate_result_record(forged)


def test_same_digest_alien_owner_and_result_are_not_interchangeable(
    atomic_bundle,
    atomic_results,
):
    owner = atomic_bundle["initializer_owner"]
    alien = atomic_bundle["alien_initializer_owner"]
    assert alien is not owner
    assert alien.manifest is not owner.manifest
    assert alien.certificate is not owner.certificate
    assert alien.manifest.manifest_sha256 == owner.manifest.manifest_sha256
    assert alien.certificate.certificate_sha256 == owner.certificate.certificate_sha256

    original = atomic_results["partial"]
    alien_result = alien.initialize(original.run_id, original.initialization_index)
    initializer._validate_result_record(alien_result)
    with pytest.raises(ValueError, match="another owner"):
        owner.validate_result(
            alien_result,
            alien_result.run_id,
            alien_result.initialization_index,
        )


def test_live_owner_refuses_equal_manifest_and_simultaneous_role_rebinding(
    atomic_bundle,
):
    owner = atomic_bundle["initializer_owner"]
    alien_manifest = atomic_bundle["alien_initializer_owner"].manifest
    original_manifest = owner._manifest
    object.__setattr__(owner, "_manifest", alien_manifest)
    try:
        with pytest.raises(ValueError, match="manifest binding"):
            owner._require_live_binding()
    finally:
        object.__setattr__(owner, "_manifest", original_manifest)
    owner._require_live_binding()

    original_role = owner._initializer_role_sha256
    original_certificate = owner._certificate
    changed_role = "a" * 64
    changed_certificate = initializer._make_certificate(
        owner.protocol_owner.certificate,
        owner.manifest,
        initializer_role_sha256=changed_role,
    )
    object.__setattr__(owner, "_initializer_role_sha256", changed_role)
    object.__setattr__(owner, "_certificate", changed_certificate)
    try:
        with pytest.raises(ValueError, match="certificate binding"):
            owner._require_live_binding()
    finally:
        object.__setattr__(owner, "_initializer_role_sha256", original_role)
        object.__setattr__(owner, "_certificate", original_certificate)
    owner._require_live_binding()


@pytest.mark.parametrize(
    "field",
    [
        "_initializer_role_sha256",
        "_certified_initializer_role_sha256",
        "_reference_parameter_sha256",
        "_certified_reference_parameter_sha256",
    ],
)
def test_cached_owner_digests_are_typed_before_hostile_equality(
    atomic_bundle,
    field,
):
    class HostileDigest:
        def __eq__(self, other):
            del other
            raise AssertionError("hostile digest equality must not run")

        def __ne__(self, other):
            del other
            raise AssertionError("hostile digest equality must not run")

    owner = atomic_bundle["initializer_owner"]
    original = getattr(owner, field)
    object.__setattr__(owner, field, HostileDigest())
    try:
        with pytest.raises(TypeError, match="exact text"):
            owner._require_live_binding()
    finally:
        object.__setattr__(owner, field, original)


def test_matching_api_checks_live_binding_before_certificate_dereference(
    atomic_bundle,
):
    class HostileCertificate:
        def __getattribute__(self, name):
            del name
            raise AssertionError("hostile certificate access must not run")

        def __eq__(self, other):
            del other
            raise AssertionError("hostile certificate equality must not run")

    owner = atomic_bundle["initializer_owner"]
    original = owner._certificate
    require_matching = getattr(
        initializer,
        "require_matching_plugin_bridge_counter_keyed_reference_initializer",
    )
    object.__setattr__(owner, "_certificate", HostileCertificate())
    try:
        with pytest.raises(ValueError, match="certificate binding"):
            require_matching(
                atomic_bundle["protocol_owner"],
                owner,
                initializer_policy=INITIALIZER_POLICY,
                initializer_role_sha256=INITIALIZER_ROLE,
            )
    finally:
        object.__setattr__(owner, "_certificate", original)


def test_matching_and_certificate_apis_require_exact_policy_role_and_owner(
    atomic_bundle,
):
    protocol_owner = atomic_bundle["protocol_owner"]
    owner = atomic_bundle["initializer_owner"]
    required = (
        initializer.require_matching_plugin_bridge_counter_keyed_reference_initializer(
            protocol_owner,
            owner,
            initializer_policy=INITIALIZER_POLICY,
            initializer_role_sha256=INITIALIZER_ROLE,
        )
    )
    validate_certificate = getattr(
        initializer,
        "validate_plugin_bridge_counter_keyed_" "reference_initializer_certificate",
    )
    certificate = validate_certificate(
        protocol_owner,
        owner,
        initializer_policy=INITIALIZER_POLICY,
        initializer_role_sha256=INITIALIZER_ROLE,
    )
    assert required is owner
    assert certificate is owner.certificate

    with pytest.raises(ValueError, match="exported reference initializer"):
        initializer.require_matching_plugin_bridge_counter_keyed_reference_initializer(
            protocol_owner,
            owner,
            initializer_policy="changed",
            initializer_role_sha256=INITIALIZER_ROLE,
        )
    with pytest.raises(ValueError, match="another role"):
        initializer.require_matching_plugin_bridge_counter_keyed_reference_initializer(
            protocol_owner,
            owner,
            initializer_policy=INITIALIZER_POLICY,
            initializer_role_sha256="a" * 64,
        )
    with pytest.raises(ValueError, match="another checkpoint-27 owner"):
        initializer.require_matching_plugin_bridge_counter_keyed_reference_initializer(
            checkpoint27_tests._certify(atomic_bundle["control_owner"]),
            owner,
            initializer_policy=INITIALIZER_POLICY,
            initializer_role_sha256=INITIALIZER_ROLE,
        )


def test_records_owner_and_manifest_are_sealed_nonpickle_objects(
    atomic_bundle,
    atomic_results,
):
    owner = atomic_bundle["initializer_owner"]
    result = atomic_results["partial"]
    values = (owner, owner.manifest, owner.certificate, result, result.raw_slots[0])
    for value in values:
        with pytest.raises((AttributeError, TypeError)):
            value.new_field = 1
        with pytest.raises(TypeError):
            pickle.dumps(value)
    with pytest.raises(TypeError):
        initializer.FiniteResolutionCappedPoissonManifest(_construction_token=object())
    sealed_types = (
        initializer.FiniteResolutionCappedPoissonManifest,
        initializer.CounterKeyedReferenceInitializerCertificate,
        initializer.CounterKeyedReferenceInitializerRawSlot,
        initializer.CounterKeyedReferenceInitializerResult,
        initializer.CounterKeyedReferenceInitializerOwner,
    )
    for sealed_type in sealed_types:
        with pytest.raises(TypeError):
            type("HostileSubclass", (sealed_type,), {})


def test_public_surface_is_exact_and_only_exposes_reference_strategy():
    expected = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCOPE",
        "FINITE_RESOLUTION_REFERENCE_COORDINATE_TRANSFORM",
        "COUNTER_KEYED_REFERENCE_INITIALIZER_RAW_WORD_BITS",
        "COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_BUCKET_BITS",
        "COUNTER_KEYED_REFERENCE_INITIALIZER_COORDINATE_IGNORED_LOW_BITS",
        "COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS",
        "COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_CATEGORIES",
        "COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_INTEGER_BITS",
        "COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_EXACT_RATIONAL_AGGREGATE_BITS",
        "FiniteResolutionCappedPoissonManifest",
        "CounterKeyedReferenceInitializerCertificate",
        "CounterKeyedReferenceInitializerRawSlot",
        "CounterKeyedReferenceInitializerResult",
        "CounterKeyedReferenceInitializerOwner",
        "PluginBridgeCounterKeyedReferenceInitializerError",
        "certify_plugin_bridge_counter_keyed_reference_initializer",
        "require_matching_plugin_bridge_counter_keyed_reference_initializer",
        "validate_plugin_bridge_counter_keyed_reference_initializer_certificate",
    }
    assert set(initializer.__all__) == expected
    assert len(initializer.__all__) == len(set(initializer.__all__))
    assert all(getattr(initializer, name) is not None for name in expected)
    assert not any(
        word in name
        for name in initializer.__all__
        for word in ("rejection", "sir", "enumeration", "conditional", "tilted")
    )
    owner_properties = {
        name
        for name, value in vars(
            initializer.CounterKeyedReferenceInitializerOwner
        ).items()
        if isinstance(value, property)
    }
    assert owner_properties == {"certificate", "manifest", "protocol_owner"}


def test_source_has_one_parent_rng_path_and_no_hidden_random_draw_api():
    source = inspect.getsource(initializer)
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
    assert "ndtri" in source
    assert "protocol_owner.allocate" in source


def test_optional_torch_boundary_translates_dependency_failure():
    source = Path(initializer.__file__).resolve()
    script = """
import builtins
import runpy

real_import = builtins.__import__

def blocked(name, *args, **kwargs):
    if name == 'torch' or name.startswith('torch.'):
        raise ModuleNotFoundError("No module named 'torch'", name='torch')
    return real_import(name, *args, **kwargs)

builtins.__import__ = blocked
runpy.run_path(%r, run_name='reference_initializer_without_torch')
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
    assert (
        "counter-keyed reference initialization requires the optional PyTorch"
        in completed.stderr
    )


def test_scope_retains_mandatory_law_sampler_and_custody_nonclaims(atomic_bundle):
    certificate = atomic_bundle["initializer_owner"].certificate
    names = (
        "exact_continuous_gaussian_law_certified",
        "exact_capped_poisson_reference_law_certified",
        "quantitative_weak_or_wasserstein_bound_certified",
        "unconditional_full_configuration_tv_one_certified",
        "actual_philox_uniformity_certified",
        "statistical_independence_certified",
        "physical_randomness_certified",
        "enumeration_strategy_certified",
        "rejection_strategy_certified",
        "sir_strategy_certified",
        "conditional_or_tilted_initializer_law_certified",
        "accepted_configuration_to_lineage_mapping_certified",
        "tag3_occurrence_payload_coordination_certified",
        "tag3_cross_initialization_disjointness_certified",
        "global_duplicate_address_use_prevention_certified",
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
    assert all(getattr(certificate, name) is False for name in names)
    scope = initializer.PLUGIN_BRIDGE_COUNTER_KEYED_REFERENCE_INITIALIZER_SCOPE
    for phrase in (
        "not-exact-capped-poisson-or-continuous-gaussian-reference-law",
        "not-actual-philox-uniformity-independence-or-physical-randomness",
        "not-enumeration-rejection-sir-conditional-or-tilted-initialization",
        "not-lineage-or-tag3-payload-coordination",
        "not-brownian-drift-path-strang-liveness-or-full-sampler",
    ):
        assert phrase in scope
