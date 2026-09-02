"""Hostile tests for checkpoint-36 finite rejection preparation."""

import ast
from fractions import Fraction
import inspect
from pathlib import Path
import pickle
import random
import subprocess
import sys
import textwrap
import typing

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="counter-keyed rejection preparation requires PyTorch"
)

from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initial_tilt_rejection_preparation as preparation,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initializer_protocol as protocol,
)
from heterodiff.theory.configuration_reference import (  # noqa: E402
    CappedPoissonConfigurationReference,
    TransformedEvent,
)
from tests.unit import (  # noqa: E402
    test_configuration_initial_tilt_composer_torch as checkpoint30,
)
from tests.unit import (  # noqa: E402
    test_plugin_bridge_counter_keyed_reference_initializer as checkpoint28,
)


PREPARATION_POLICY = (
    preparation.PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_POLICY
)
PREPARATION_ROLE = "6" * 64
RESIDUAL_CONTEXT = checkpoint30._RESIDUAL_CONTEXT
UINT64_TOTAL = 1 << 64
_DECLARE_HYPOTHESIS = getattr(
    preparation,
    "declare_initial_tilt_rejection_preparation_word_family_hypothesis",
)
_VALIDATE_HYPOTHESIS = getattr(
    preparation,
    "validate_initial_tilt_rejection_preparation_word_family_hypothesis",
)
_CERTIFY = getattr(
    preparation,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation",
)
_MATCHING = getattr(
    preparation,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "preparation",
)
_VALIDATE_CERTIFICATE = getattr(
    preparation,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation_"
    "certificate",
)


def _certify(bundle, *, attempt_budget=2, role=PREPARATION_ROLE):
    hypothesis = _DECLARE_HYPOTHESIS(
        bundle["initializer_owner"], attempt_budget=attempt_budget
    )
    owner = _CERTIFY(
        bundle["initializer_owner"],
        bundle["initial_tilt"],
        residual_context=RESIDUAL_CONTEXT,
        attempt_budget=attempt_budget,
        preparation_policy=PREPARATION_POLICY,
        preparation_role_sha256=role,
        word_family_hypothesis=hypothesis,
    )
    return hypothesis, owner


@pytest.fixture(scope="module")
def certified_bundle():
    bundle = checkpoint28.continuous_bundle.__wrapped__()
    potential = bundle["potential_composer"]
    bundle["totalized_guide"] = potential.totalized_guide
    bundle["totalized_residual"] = potential.totalized_residual
    bundle["initial_tilt"] = checkpoint30._certify(bundle)
    hypothesis, owner = _certify(bundle)
    bundle["word_family_hypothesis"] = hypothesis
    bundle["owner"] = owner
    bundle["alien_hypothesis"], bundle["alien_owner"] = _certify(bundle)
    return bundle


@pytest.fixture(scope="module")
def prepared_result(certified_bundle):
    owner = certified_bundle["owner"]
    coordinates = _find_request(
        owner,
        lambda cardinalities, positions: set(cardinalities) == {0, 1},
        first_run_id=36_000,
    )
    return owner.prepare(*coordinates)


@pytest.fixture(scope="module")
def single_attempt_bundle(certified_bundle):
    hypothesis, owner = _certify(certified_bundle, attempt_budget=1, role="7" * 64)
    coordinates = _find_request(
        owner,
        lambda cardinalities, positions: cardinalities == (1,),
        first_run_id=36_100,
    )
    return hypothesis, owner, owner.prepare(*coordinates)


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


def _find_request(owner, predicate, *, first_run_id):
    certificate = owner.certificate
    manifest = certificate.manifest
    first_block_count = certificate.block_raw64_word_counts[0]
    for run_id in range(first_run_id, first_run_id + 4_096):
        cardinalities = []
        type_positions = []
        for attempt in range(certificate.attempt_budget):
            words, _ = checkpoint28.checkpoint26_tests._direct_prefix(
                run_id=run_id,
                initialization_index=0,
                stage_index=preparation.INITIAL_TILT_REJECTION_STAGE_INDEX,
                attempt_index=attempt * certificate.blocks_per_attempt,
                word_count=first_block_count,
            )
            cardinality = preparation._CP28_QUOTA_POSITION(
                words[manifest.count_word_offset], manifest.count_cumulative_ends
            )
            positions = tuple(
                preparation._CP28_QUOTA_POSITION(
                    words[manifest.type_segment_offset + raw_slot],
                    manifest.type_cumulative_ends,
                )
                for raw_slot in range(manifest.total_cap)
            )
            cardinalities.append(cardinality)
            type_positions.append(positions)
        if predicate(tuple(cardinalities), tuple(type_positions)):
            return run_id, 0
    raise AssertionError("a deterministic rejection-preparation fixture was not found")


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


def _fraction(record, prefix):
    return Fraction(
        getattr(record, "%s_numerator" % prefix),
        getattr(record, "%s_denominator" % prefix),
    )


def _hypothesis_values(hypothesis, **updates):
    values = {
        name: updates.get(name, getattr(hypothesis, name))
        for name in preparation._hypothesis_fields()
    }
    values["hypothesis_sha256"] = "0" * 64
    values["hypothesis_sha256"] = preparation._SEMANTIC_DIGEST(
        preparation._hypothesis_payload(values)
    )
    return values


def _certificate_values(certificate, **updates):
    values = {
        name: updates.get(name, getattr(certificate, name))
        for name in preparation._certificate_fields()
    }
    values["certificate_sha256"] = "0" * 64
    values["certificate_sha256"] = preparation._SEMANTIC_DIGEST(
        preparation._certificate_payload(values)
    )
    return values


def _attempt_values(attempt, **updates):
    values = {
        name: updates.get(name, getattr(attempt, name))
        for name in preparation._attempt_fields()
    }
    values["attempt_sha256"] = "0" * 64
    values["attempt_sha256"] = preparation._SEMANTIC_DIGEST(
        preparation._attempt_payload(values)
    )
    return values


def _result_values(result, **updates):
    values = {
        name: updates.get(name, getattr(result, name))
        for name in preparation._result_fields()
    }
    if "attempts" in updates and "attempt_sha256s" not in updates:
        values["attempt_sha256s"] = tuple(
            attempt.attempt_sha256 for attempt in values["attempts"]
        )
    if "attempts" in updates and "logical_word_coordinates" not in updates:
        values["logical_word_coordinates"] = tuple(
            coordinate
            for attempt in values["attempts"]
            for coordinate in attempt.logical_word_coordinates
        )
    if "logical_word_coordinates" in updates or "attempts" in updates:
        values["logical_word_coordinate_sha256"] = preparation._word_coordinate_digest(
            values["logical_word_coordinates"]
        )
    values["result_sha256"] = "0" * 64
    values["result_sha256"] = preparation._SEMANTIC_DIGEST(
        preparation._result_payload(values)
    )
    return values


def test_frozen_layout_constants_are_exact():
    assert preparation.INITIAL_TILT_REJECTION_STRATEGY == "rejection"
    assert preparation.INITIAL_TILT_REJECTION_STAGE_INDEX == 1
    assert preparation.INITIAL_TILT_REJECTION_DOMAIN_TAG == 7
    assert preparation.INITIAL_TILT_REJECTION_RESERVED_WORDS_PER_ATTEMPT == 1
    assert preparation.INITIAL_TILT_REJECTION_MIN_ATTEMPTS == 1
    assert preparation.INITIAL_TILT_REJECTION_MAX_ATTEMPTS == 64
    assert preparation.INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS == 64
    assert preparation.INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS == 65_536
    assert preparation.INITIAL_TILT_REJECTION_MAX_CONTEXT_DIMENSION == 4_096
    assert preparation.INITIAL_TILT_REJECTION_MAX_TEXT_LENGTH == 16_384
    assert preparation.INITIAL_TILT_REJECTION_MAX_INTEGER_BITS == 131_072
    assert protocol.INITIALIZER_STRATEGY_REJECTION == "rejection"
    assert protocol.INITIALIZER_STAGE_REJECTION_ATTEMPT == 1


def test_public_signatures_owner_surface_and_exports_are_exact(certified_bundle):
    owner = certified_bundle["owner"]
    factory = _CERTIFY
    matching = _MATCHING
    validator = _VALIDATE_CERTIFICATE
    assert tuple(inspect.signature(_DECLARE_HYPOTHESIS).parameters) == (
        "reference_initializer_owner",
        "attempt_budget",
    )
    assert tuple(inspect.signature(_VALIDATE_HYPOTHESIS).parameters) == ("hypothesis",)
    assert tuple(inspect.signature(factory).parameters) == (
        "reference_initializer_owner",
        "initial_tilt_composer",
        "residual_context",
        "attempt_budget",
        "preparation_policy",
        "preparation_role_sha256",
        "word_family_hypothesis",
    )
    for function in (matching, validator):
        assert tuple(inspect.signature(function).parameters) == (
            "reference_initializer_owner",
            "initial_tilt_composer",
            "owner",
            "residual_context",
            "attempt_budget",
            "preparation_policy",
            "preparation_role_sha256",
            "word_family_hypothesis",
        )
    assert tuple(inspect.signature(owner.prepare).parameters) == (
        "run_id",
        "initialization_index",
    )
    assert tuple(inspect.signature(owner.validate_result).parameters) == (
        "result",
        "run_id",
        "initialization_index",
    )
    assert {name for name in type(owner).__dict__ if not name.startswith("_")} == {
        "certificate",
        "reference_initializer_owner",
        "initial_tilt_composer",
        "word_family_hypothesis",
        "prepare",
        "validate_result",
    }
    for function in (factory, owner.prepare, owner.validate_result):
        forbidden = {
            "rng",
            "seed",
            "raw_word",
            "acceptance",
            "selection",
            "retry",
            "fallback",
            "lineage",
        }
        assert forbidden.isdisjoint(inspect.signature(function).parameters)

    expected_exports = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREPARATION_SCOPE",
        "INITIAL_TILT_REJECTION_WORD_FAMILY_HYPOTHESIS_SCHEMA_VERSION",
        "INITIAL_TILT_REJECTION_WORD_FAMILY_HYPOTHESIS_SCOPE",
        "INITIAL_TILT_REJECTION_WORD_FAMILY_PREMISE",
        "INITIAL_TILT_REJECTION_DATA_PROCESSING_THEOREM",
        "INITIAL_TILT_REJECTION_TRIANGLE_LEDGER",
        "INITIAL_TILT_REJECTION_STRATEGY",
        "INITIAL_TILT_REJECTION_STAGE_INDEX",
        "INITIAL_TILT_REJECTION_DOMAIN_TAG",
        "INITIAL_TILT_REJECTION_RESERVED_WORDS_PER_ATTEMPT",
        "INITIAL_TILT_REJECTION_MIN_ATTEMPTS",
        "INITIAL_TILT_REJECTION_MAX_ATTEMPTS",
        "INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS",
        "INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS",
        "INITIAL_TILT_REJECTION_MAX_CONTEXT_DIMENSION",
        "InitialTiltRejectionPreparationWordFamilyHypothesis",
        "CounterKeyedInitialTiltRejectionPreparationCertificate",
        "CounterKeyedInitialTiltRejectionAttempt",
        "CounterKeyedInitialTiltRejectionPreparationResult",
        "CounterKeyedInitialTiltRejectionPreparationOwner",
        "PluginBridgeCounterKeyedInitialTiltRejectionPreparationError",
        "declare_initial_tilt_rejection_preparation_word_family_hypothesis",
        "validate_initial_tilt_rejection_preparation_word_family_hypothesis",
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation",
        "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "preparation",
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation_"
        "certificate",
    }
    assert set(preparation.__all__) == expected_exports
    assert len(preparation.__all__) == len(set(preparation.__all__))


def test_word_family_hypothesis_freezes_layout_and_conditional_law_boundary(
    certified_bundle,
):
    hypothesis = certified_bundle["word_family_hypothesis"]
    manifest = certified_bundle["initializer_owner"].manifest
    blocks = manifest.canonical_block_raw64_word_counts + (1,)
    assert hypothesis.reference_initializer_certificate is (
        certified_bundle["initializer_owner"].certificate
    )
    assert hypothesis.manifest is manifest
    assert hypothesis.attempt_budget == 2
    assert hypothesis.reference_block_count == len(blocks) - 1
    assert hypothesis.blocks_per_attempt == len(blocks)
    assert hypothesis.reference_words_per_attempt == manifest.required_raw64_words
    assert hypothesis.words_per_attempt == manifest.required_raw64_words + 1
    assert hypothesis.total_stream_records == 2 * len(blocks)
    assert hypothesis.total_raw64_words == 2 * (manifest.required_raw64_words + 1)
    assert hypothesis.block_raw64_word_counts == blocks
    assert hypothesis.data_processing_theorem == "TV(F#nu,F#U)<=TV(nu,U)"
    assert "conditional-only" in hypothesis.conditional_triangle_ledger
    assert "no-live-source-bound" in hypothesis.conditional_triangle_ledger
    assert "failure" in hypothesis.abstract_pushforward_codomain

    true_names = {
        "distinct_full_logical_word_coordinates_required",
        "logical_word_coordinates_are_normalized_template",
        "universal_run_initialization_instantiation_required",
        "finite_injective_coordinate_relabeling_invariance_acknowledged",
        "failure_augmented_total_operational_map_acknowledged",
        "abstract_iid_uniform_uint64_family_assumed",
        "repeated_coordinate_same_variable_acknowledged",
        "deterministic_batch_pushforward_kernel_defined",
        "data_processing_accounting_conditional",
        "source_plus_algorithm_triangle_ledger_conditional",
    }
    false_names = {
        "live_philox_family_identified_with_abstract_family",
        "actual_live_uniformity_certified",
        "actual_live_independence_certified",
        "physical_randomness_certified",
        "live_initializer_distribution_admitted",
        "global_address_one_shot_use_certified",
        "failure_probability_certified",
        "successful_record_conditional_law_certified",
    }
    bool_names = {
        name
        for name, annotation in typing.get_type_hints(
            preparation.InitialTiltRejectionPreparationWordFamilyHypothesis
        ).items()
        if annotation is bool
    }
    assert bool_names == true_names | false_names
    assert all(getattr(hypothesis, name) is True for name in true_names)
    assert all(getattr(hypothesis, name) is False for name in false_names)


def test_word_family_coordinates_cover_each_attempt_block_and_offset_once(
    certified_bundle,
):
    hypothesis = certified_bundle["word_family_hypothesis"]
    coordinates = hypothesis.logical_word_coordinates
    blocks = hypothesis.block_raw64_word_counts
    assert len(coordinates) == hypothesis.total_raw64_words
    assert len(coordinates) == len(set(coordinates))
    cursor = 0
    for attempt in range(hypothesis.attempt_budget):
        for block, count in enumerate(blocks):
            segment = coordinates[cursor : cursor + count]
            assert segment == tuple(
                (
                    (0, 7),
                    (0, 0, 1, attempt * len(blocks) + block),
                    offset,
                )
                for offset in range(count)
            )
            cursor += count
    assert cursor == len(coordinates)
    assert hypothesis.logical_word_coordinate_sha256 == (
        preparation._word_coordinate_digest(coordinates)
    )


@pytest.mark.parametrize(
    "attempt_budget",
    (True, np.int64(1), np.uint64(1), 1.0, "1", 0, -1, 65, UINT64_TOTAL),
)
def test_hypothesis_attempt_budget_requires_bounded_exact_python_integer(
    certified_bundle,
    attempt_budget,
):
    with pytest.raises((TypeError, ValueError)):
        preparation.declare_initial_tilt_rejection_preparation_word_family_hypothesis(
            certified_bundle["initializer_owner"], attempt_budget=attempt_budget
        )


@pytest.mark.parametrize(
    "field,value,match",
    (
        ("abstract_iid_uniform_uint64_family_assumed", False, "remain True"),
        ("actual_live_uniformity_certified", True, "remain False"),
        ("actual_live_independence_certified", True, "remain False"),
        ("physical_randomness_certified", True, "remain False"),
        ("live_initializer_distribution_admitted", True, "remain False"),
        ("global_address_one_shot_use_certified", True, "remain False"),
    ),
)
def test_redigested_word_family_claim_forgeries_are_refused(
    certified_bundle,
    field,
    value,
    match,
):
    hypothesis = certified_bundle["word_family_hypothesis"]
    hostile = _forged(
        hypothesis,
        **_hypothesis_values(hypothesis, **{field: value}),
    )
    with pytest.raises(ValueError, match=match):
        preparation.validate_initial_tilt_rejection_preparation_word_family_hypothesis(
            hostile
        )


def test_word_family_layout_splice_and_same_digest_alien_are_refused(
    certified_bundle,
):
    hypothesis = certified_bundle["word_family_hypothesis"]
    alien = certified_bundle["alien_hypothesis"]
    assert alien is not hypothesis
    assert alien.hypothesis_sha256 == hypothesis.hypothesis_sha256
    assert alien.reference_initializer_certificate is (
        hypothesis.reference_initializer_certificate
    )

    coordinates = hypothesis.logical_word_coordinates
    for replacement in (
        coordinates[:-1],
        coordinates + (coordinates[-1],),
        (coordinates[1], coordinates[0], *coordinates[2:]),
    ):
        hostile = _forged(
            hypothesis,
            **_hypothesis_values(
                hypothesis,
                logical_word_coordinates=replacement,
            ),
        )
        with pytest.raises(ValueError, match="coordinates|length|bound"):
            _VALIDATE_HYPOTHESIS(hostile)


def test_word_family_hypothesis_is_sealed_and_nonpickle(certified_bundle):
    hypothesis = certified_bundle["word_family_hypothesis"]
    with pytest.raises(Exception):
        hypothesis.actual_live_uniformity_certified = True
    with pytest.raises(TypeError):
        pickle.dumps(hypothesis)
    with pytest.raises(TypeError):

        class Derived(preparation.InitialTiltRejectionPreparationWordFamilyHypothesis):
            pass


def test_certificate_binds_exact_parent_ancestry_layout_context_and_upper_bound(
    certified_bundle,
):
    owner = certified_bundle["owner"]
    certificate = owner.certificate
    parent28 = certified_bundle["initializer_owner"]
    parent30 = certified_bundle["initial_tilt"]
    parent27 = parent28.protocol_owner
    manifest = parent28.manifest
    assert certificate.checkpoint28_certificate is parent28.certificate
    assert certificate.checkpoint27_certificate is parent27.certificate
    assert certificate.checkpoint30_certificate is parent30.certificate
    assert certificate.manifest is manifest
    assert certificate.word_family_hypothesis is (
        certified_bundle["word_family_hypothesis"]
    )
    assert certificate.residual_context == RESIDUAL_CONTEXT
    assert certificate.residual_context is not RESIDUAL_CONTEXT
    assert certificate.residual_context_dimension == len(RESIDUAL_CONTEXT)
    assert certificate.attempt_budget == 2
    assert certificate.block_raw64_word_counts == (
        manifest.canonical_block_raw64_word_counts + (1,)
    )
    assert certificate.total_stream_records == (
        certificate.attempt_budget * certificate.blocks_per_attempt
    )
    assert certificate.total_raw64_words == (
        certificate.attempt_budget * certificate.words_per_attempt
    )
    assert certificate.global_initial_log_factor_upper_bound.hex() == (
        parent30.certificate.initial_log_factor_upper_bound.hex()
    )
    assert Fraction(
        certificate.global_upper_bound_numerator,
        certificate.global_upper_bound_denominator,
    ) == Fraction.from_float(certificate.global_initial_log_factor_upper_bound)
    assert certificate.process_parameter_sha256 == (
        parent28.certificate.process_parameter_sha256
    )


def test_certificate_exhaustively_freezes_only_preparation_claims(certified_bundle):
    certificate = certified_bundle["owner"].certificate
    bool_names = {
        name
        for name, annotation in typing.get_type_hints(
            preparation.CounterKeyedInitialTiltRejectionPreparationCertificate
        ).items()
        if annotation is bool
    }
    positive = set(preparation._CERTIFICATE_POSITIVE_FLAGS)
    negative = set(preparation._CERTIFICATE_NEGATIVE_FLAGS)
    assert positive.isdisjoint(negative)
    assert bool_names == positive | negative
    assert all(getattr(certificate, name) is True for name in positive)
    assert all(getattr(certificate, name) is False for name in negative)
    required_negative = {
        "acceptance_predicate_certified",
        "acceptance_decision_certified",
        "rejection_success_or_exhaustion_certified",
        "exponential_bernoulli_law_certified",
        "first_accepted_output_certified",
        "normalized_tilted_initializer_certified",
        "exact_pi_n_law_certified",
        "exact_continuous_gaussian_law_certified",
        "analytic_target_certified",
        "actual_live_uniformity_certified",
        "actual_live_independence_certified",
        "physical_randomness_certified",
        "global_address_one_shot_use_certified",
        "rejection_sampling_admissible",
        "sir_admissible",
        "initializer_admissible",
        "lineage_certified",
        "tag3_payload_coordination_certified",
        "brownian_stream_consumption_certified",
        "continuous_drift_admissible",
        "path_admissible",
        "full_sampler_admissible",
        "sampler_liveness_certified",
        "test28_closed",
        "result_promotion_admissible",
        "failure_probability_certified",
        "successful_record_conditional_law_certified",
    }
    assert required_negative <= negative


@pytest.mark.parametrize(
    "field,value,match",
    (
        ("checkpoint30_point_scoring_certified", False, "remain True"),
        ("acceptance_predicate_certified", True, "remain False"),
        ("rejection_sampling_admissible", True, "remain False"),
        ("initializer_admissible", True, "remain False"),
        ("actual_live_independence_certified", True, "remain False"),
        ("test28_closed", True, "remain False"),
        ("result_promotion_admissible", True, "remain False"),
    ),
)
def test_redigested_certificate_claim_forgeries_are_refused(
    certified_bundle,
    field,
    value,
    match,
):
    certificate = certified_bundle["owner"].certificate
    hostile = _forged(
        certificate,
        **_certificate_values(certificate, **{field: value}),
    )
    with pytest.raises(ValueError, match=match):
        preparation._validate_certificate(hostile)


def test_attempt_layout_enforces_record_and_aggregate_caps_before_allocation(
    certified_bundle,
    monkeypatch,
):
    manifest = certified_bundle["initializer_owner"].manifest
    blocks = len(manifest.canonical_block_raw64_word_counts) + 1
    words = manifest.required_raw64_words + 1
    assert preparation._attempt_layout(manifest, 1) == (
        1,
        manifest.canonical_block_raw64_word_counts + (1,),
        blocks,
        manifest.required_raw64_words,
        words,
    )
    monkeypatch.setattr(
        preparation, "INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS", 2 * blocks - 1
    )
    with pytest.raises(ValueError, match="resource bound|record cap"):
        preparation._attempt_layout(manifest, 2)
    monkeypatch.setattr(preparation, "INITIAL_TILT_REJECTION_MAX_STREAM_RECORDS", 64)
    monkeypatch.setattr(
        preparation, "INITIAL_TILT_REJECTION_MAX_TOTAL_RAW64_WORDS", 2 * words - 1
    )
    with pytest.raises(ValueError, match="resource bound|word cap"):
        preparation._attempt_layout(manifest, 2)


def test_reserved_word_overflow_at_parent_maximum_is_refused():
    reference = CappedPoissonConfigurationReference(
        {0: 3_854},
        {0: 1.0},
        activity=1.0,
        total_cap=17,
    )
    manifest = preparation._reference._make_manifest(reference)
    assert manifest.required_raw64_words == 65_536
    assert manifest.canonical_block_raw64_word_counts == (4_096,) * 16
    with pytest.raises(ValueError, match="resource bound|word cap"):
        preparation._attempt_layout(manifest, 1)


def test_hypothesis_nested_coordinate_is_typed_before_hostile_equality(
    certified_bundle,
):
    hypothesis = certified_bundle["word_family_hypothesis"]
    bomb = _EqualityBomb()
    coordinates = (bomb, *hypothesis.logical_word_coordinates[1:])
    hostile = _forged(
        hypothesis,
        logical_word_coordinates=coordinates,
    )
    with pytest.raises(TypeError, match="coordinate|tuple|integer"):
        preparation.validate_initial_tilt_rejection_preparation_word_family_hypothesis(
            hostile
        )
    assert bomb.calls == 0


def test_certificate_block_counts_are_typed_before_hostile_equality(
    certified_bundle,
):
    certificate = certified_bundle["owner"].certificate
    bomb = _EqualityBomb()
    hostile_blocks = (bomb, *certificate.block_raw64_word_counts[1:])
    hostile = _forged(
        certificate,
        block_raw64_word_counts=hostile_blocks,
    )
    with pytest.raises(TypeError, match="block|integer"):
        preparation._validate_certificate(hostile)
    assert bomb.calls == 0


@pytest.mark.parametrize(
    "parent_name,field",
    (
        ("checkpoint28_certificate", "maximum_raw_slots"),
        ("checkpoint27_certificate", "maximum_stream_records"),
        ("checkpoint30_certificate", "residual_context_dimension"),
    ),
)
def test_nested_parent_certificate_bombs_fail_before_equality_or_delegation(
    certified_bundle,
    parent_name,
    field,
):
    certificate = certified_bundle["owner"].certificate
    parent = getattr(certificate, parent_name)
    original = getattr(parent, field)
    bomb = _EqualityBomb()
    object.__setattr__(parent, field, bomb)
    try:
        with pytest.raises(TypeError, match="primitive type"):
            preparation._validate_certificate(certificate)
    finally:
        object.__setattr__(parent, field, original)
    assert bomb.calls == 0


def test_valid_reference_arrays_are_immutable_nonowning_views(certified_bundle):
    reference = certified_bundle["initializer_owner"].manifest.reference
    for field in (
        "count_log_masses",
        "_count_probability_vector",
        "_count_sampling_cdf",
        "_type_weight_vector",
        "_type_sampling_cdf",
    ):
        array = getattr(reference, field)
        if array is not None:
            assert array.flags.owndata is False
            assert array.flags.writeable is False


@pytest.mark.parametrize("surface", ("hypothesis", "certificate", "result"))
def test_nested_cp28_manifest_is_preflighted_before_validator_delegation(
    certified_bundle,
    prepared_result,
    monkeypatch,
    surface,
):
    hypothesis = certified_bundle["word_family_hypothesis"]
    certificate = certified_bundle["owner"].certificate
    parent28 = certificate.checkpoint28_certificate
    bomb = _EqualityBomb()
    hostile_manifest = _forged(
        parent28.manifest,
        type_ids=(bomb, *parent28.manifest.type_ids[1:]),
    )
    hostile_parent28 = _forged(parent28, manifest=hostile_manifest)
    calls = []

    def forbidden_cp28_validator(*args, **kwargs):
        del args, kwargs
        calls.append("CP28 certificate validator")
        raise AssertionError("nested manifest must fail before CP28 delegation")

    monkeypatch.setattr(
        preparation._reference,
        "_validate_certificate",
        forbidden_cp28_validator,
    )
    monkeypatch.setattr(
        preparation,
        "_CP28_VALIDATE_CERTIFICATE",
        forbidden_cp28_validator,
    )
    with pytest.raises(TypeError, match="integer|manifest|primitive|type_ids"):
        if surface == "hypothesis":
            hostile = _forged(
                hypothesis,
                reference_initializer_certificate=hostile_parent28,
            )
            _VALIDATE_HYPOTHESIS(hostile)
        else:
            hostile_certificate = _forged(
                certificate,
                checkpoint28_certificate=hostile_parent28,
            )
            if surface == "certificate":
                preparation._validate_certificate(hostile_certificate)
            else:
                values = {
                    name: getattr(prepared_result, name)
                    for name in preparation._result_fields()
                }
                values["certificate"] = hostile_certificate
                preparation._validate_result_values(values)
    assert bomb.calls == 0
    assert calls == []


@pytest.mark.parametrize("surface", ("hypothesis", "certificate", "certify"))
def test_manifest_validator_callback_is_single_and_custody_wrapped(
    certified_bundle,
    monkeypatch,
    surface,
):
    hypothesis = certified_bundle["word_family_hypothesis"]
    certificate = certified_bundle["owner"].certificate
    parent28 = certificate.checkpoint28_certificate
    original_validator = preparation._CP28_VALIDATE_MANIFEST
    original_maximum = parent28.maximum_raw_slots
    calls = {"manifest": 0, "make_certificate": 0}

    def mutate_parent(manifest):
        checked = original_validator(manifest)
        calls["manifest"] += 1
        object.__setattr__(parent28, "maximum_raw_slots", original_maximum + 1)
        return checked

    def forbidden_make_certificate(*args, **kwargs):
        del args, kwargs
        calls["make_certificate"] += 1
        raise AssertionError("manifest mutation must stop certification")

    monkeypatch.setattr(preparation, "_CP28_VALIDATE_MANIFEST", mutate_parent)
    if surface == "certify":
        monkeypatch.setattr(
            preparation, "_make_certificate", forbidden_make_certificate
        )
    try:
        with pytest.raises(
            (TypeError, ValueError),
            match="certificate|changed|differs|maximum_raw_slots",
        ):
            if surface == "hypothesis":
                _VALIDATE_HYPOTHESIS(hypothesis)
            elif surface == "certificate":
                preparation._validate_certificate(certificate)
            else:
                _CERTIFY(
                    certified_bundle["initializer_owner"],
                    certified_bundle["initial_tilt"],
                    residual_context=RESIDUAL_CONTEXT,
                    attempt_budget=2,
                    preparation_policy=PREPARATION_POLICY,
                    preparation_role_sha256="4" * 64,
                    word_family_hypothesis=hypothesis,
                )
    finally:
        object.__setattr__(parent28, "maximum_raw_slots", original_maximum)
    assert calls == {"manifest": 1, "make_certificate": 0}


def test_one_and_many_attempts_are_complete_and_include_empty_and_active_cases(
    prepared_result,
    single_attempt_bundle,
):
    _, _, single = single_attempt_bundle
    assert single.attempt_budget == 1
    assert len(single.attempts) == 1
    assert single.attempts[0].sampled_cardinality == 1
    assert single.attempts[0].canonical_configuration

    assert prepared_result.attempt_budget == 2
    assert len(prepared_result.attempts) == 2
    assert {attempt.sampled_cardinality for attempt in prepared_result.attempts} == {
        0,
        1,
    }
    empty = next(
        attempt
        for attempt in prepared_result.attempts
        if attempt.sampled_cardinality == 0
    )
    active = next(
        attempt
        for attempt in prepared_result.attempts
        if attempt.sampled_cardinality == 1
    )
    assert empty.selected_raw_events == empty.canonical_configuration == ()
    assert active.selected_raw_events
    assert active.canonical_configuration


def test_parent_request_is_the_exact_fixed_budget_rejection_plan(
    certified_bundle,
    prepared_result,
):
    certificate = certified_bundle["owner"].certificate
    parent = prepared_result.parent_protocol_result
    assert parent.certificate is certificate.checkpoint27_certificate
    assert parent.strategy == protocol.INITIALIZER_STRATEGY_REJECTION
    assert parent.strategy_budget == certificate.attempt_budget
    assert parent.work_item_raw64_word_counts == certificate.block_raw64_word_counts
    assert parent.selection_raw64_word_count == 0
    assert parent.stream_record_count == certificate.total_stream_records
    assert parent.total_raw64_words == certificate.total_raw64_words
    assert parent.control_plan == tuple(
        (
            preparation.INITIAL_TILT_REJECTION_STAGE_INDEX,
            attempt * certificate.blocks_per_attempt + block,
            count,
        )
        for attempt in range(certificate.attempt_budget)
        for block, count in enumerate(certificate.block_raw64_word_counts)
    )


def test_attempts_partition_parent_entries_and_preserve_exact_block_identity(
    certified_bundle,
    prepared_result,
):
    certificate = certified_bundle["owner"].certificate
    parent = prepared_result.parent_protocol_result
    for index, attempt in enumerate(prepared_result.attempts):
        start = index * certificate.blocks_per_attempt
        stop = start + certificate.blocks_per_attempt
        assert attempt.attempt_index == index
        assert attempt.parent_entry_start == start
        assert attempt.parent_entry_stop == stop
        assert all(
            actual is expected
            for actual, expected in zip(
                attempt.parent_entries, parent.entries[start:stop]
            )
        )
        assert all(
            block is entry.raw64_words
            for block, entry in zip(
                attempt.proposal_raw64_blocks, attempt.parent_entries[:-1]
            )
        )
        assert attempt.reserved_decision_raw64_block is (
            attempt.parent_entries[-1].raw64_words
        )
        assert len(attempt.reserved_decision_raw64_block) == 1
        assert attempt.reserved_decision_raw64_word == (
            attempt.reserved_decision_raw64_block[0]
        )
        assert attempt.proposal_block_offsets[0] == 0
        assert attempt.proposal_block_offsets[-1] == (
            certificate.reference_words_per_attempt
        )
        assert attempt.proposal_concatenated_raw64_words == tuple(
            word for block in attempt.proposal_raw64_blocks for word in block
        )


def test_each_candidate_is_exactly_the_cp28_explicit_word_transform(
    certified_bundle,
    prepared_result,
):
    parent28 = certified_bundle["initializer_owner"]
    manifest = parent28.manifest
    for attempt in prepared_result.attempts:
        words = attempt.proposal_concatenated_raw64_words
        cardinality = preparation._CP28_QUOTA_POSITION(
            words[manifest.count_word_offset], manifest.count_cumulative_ends
        )
        assert attempt.sampled_cardinality == cardinality
        for position, actual in enumerate(attempt.proposal_raw_slots):
            materialized = preparation._CP28_MATERIALIZE_SLOT_FIELDS(
                manifest,
                words,
                raw_slot_index=position,
            )
            expected = preparation._CP28_MAKE_SLOT(
                parent28.certificate,
                manifest,
                materialized,
                active=position < cardinality,
            )
            assert actual.slot_sha256 == expected.slot_sha256
            assert actual.raw_slot_index == expected.raw_slot_index
            assert actual.type_raw64_word == expected.type_raw64_word
            assert actual.coordinate_raw64_words == expected.coordinate_raw64_words
            assert actual.event.model_key() == expected.event.model_key()
            assert actual.active is expected.active
        selected = tuple(
            slot.event for slot in attempt.proposal_raw_slots[:cardinality]
        )
        canonical_order = tuple(
            sorted(
                range(cardinality),
                key=lambda position: (
                    attempt.proposal_raw_slots[position].event.model_key(),
                    position,
                ),
            )
        )
        assert attempt.selected_raw_events == selected
        assert attempt.canonical_position_to_raw_slot == canonical_order
        assert attempt.canonical_configuration == tuple(
            attempt.proposal_raw_slots[position].event for position in canonical_order
        )


def test_cp30_score_and_exact_q_minus_global_upper_witness_are_literal(
    certified_bundle,
    prepared_result,
):
    owner30 = certified_bundle["initial_tilt"]
    certificate = certified_bundle["owner"].certificate
    upper = Fraction(
        certificate.global_upper_bound_numerator,
        certificate.global_upper_bound_denominator,
    )
    for attempt in prepared_result.attempts:
        score = attempt.score_evaluation
        assert score.certificate is owner30.certificate
        assert score.configuration == attempt.canonical_configuration
        assert type(score.residual_context) is tuple
        assert tuple(value.hex() for value in score.residual_context) == tuple(
            value.hex() for value in certificate.residual_context
        )
        cp28_digest = preparation._CP28_CONFIGURATION_SHA256(
            attempt.canonical_configuration
        )
        cp30_digest = preparation._TILT_CONFIGURATION_SHA256(
            attempt.canonical_configuration
        )
        assert attempt.canonical_configuration_sha256 == cp28_digest
        assert score.configuration_sha256 == cp30_digest
        assert cp28_digest != cp30_digest
        q = _fraction(attempt, "q")
        assert q == Fraction(
            score.exact_initial_log_factor_numerator,
            score.exact_initial_log_factor_denominator,
        )
        difference = _fraction(attempt, "q_minus_upper_bound")
        assert _fraction(attempt, "global_upper_bound") == upper
        assert difference == q - upper
        assert difference <= 0
        assert attempt.q_minus_upper_bound_nonpositive is True
        assert attempt.reserved_decision_word_uninterpreted is True
        assert attempt.acceptance_predicate_evaluated is False
        assert attempt.acceptance_decision_made is False
        assert attempt.exponential_or_uniform_transform_applied is False


def test_live_tag7_stage1_addresses_and_logical_word_coordinates_are_exact(
    certified_bundle,
    prepared_result,
):
    certificate = certified_bundle["owner"].certificate
    all_coordinates = []
    for attempt in prepared_result.attempts:
        expected_coordinates = []
        for block, (entry, count) in enumerate(
            zip(attempt.parent_entries, certificate.block_raw64_word_counts)
        ):
            address = entry.parent_consumption.control_stream.address
            flat = attempt.attempt_index * certificate.blocks_per_attempt + block
            assert address.domain_tag == 7
            assert address.philox_key == (prepared_result.run_id, 7)
            assert address.philox_counter == (
                0,
                prepared_result.initialization_index,
                1,
                flat,
            )
            expected_coordinates.extend(
                (
                    address.philox_key,
                    address.philox_counter,
                    offset,
                )
                for offset in range(count)
            )
        assert attempt.logical_word_coordinates == tuple(expected_coordinates)
        all_coordinates.extend(expected_coordinates)
    assert tuple(all_coordinates) == prepared_result.logical_word_coordinates
    assert len(all_coordinates) == len(set(all_coordinates))
    assert all(coordinate[1][2] == 1 for coordinate in all_coordinates)
    assert {coordinate[1][2] for coordinate in all_coordinates}.isdisjoint({0, 2, 3, 4})


def test_result_and_attempt_truth_matrices_are_exhaustive(prepared_result):
    attempt_true = {
        "q_minus_upper_bound_nonpositive",
        "exact_cp28_equivalent_candidate_transform",
        "all_raw_slots_materialized_before_count_decode",
        "duplicate_stable_canonical_bijection",
        "checkpoint30_point_score_validated",
        "reserved_decision_word_uninterpreted",
    }
    attempt_false = {
        "acceptance_predicate_evaluated",
        "acceptance_decision_made",
        "exponential_or_uniform_transform_applied",
    }
    attempt_bool_names = {
        name
        for name, annotation in typing.get_type_hints(
            preparation.CounterKeyedInitialTiltRejectionAttempt
        ).items()
        if annotation is bool
    }
    assert attempt_bool_names == attempt_true | attempt_false
    for attempt in prepared_result.attempts:
        assert all(getattr(attempt, name) is True for name in attempt_true)
        assert all(getattr(attempt, name) is False for name in attempt_false)

    result_true = {
        "complete_fixed_prefix_materialized_before_scoring",
        "all_attempts_materialized_and_scored_in_canonical_order",
        "reserved_decision_words_uninterpreted",
        "late_failure_has_no_result",
        "deterministic_fixed_address_replay_only",
    }
    result_false = {
        "retry_fallback_or_rollback_claimed",
        "acceptance_or_selection_performed",
    }
    result_bool_names = {
        name
        for name, annotation in typing.get_type_hints(
            preparation.CounterKeyedInitialTiltRejectionPreparationResult
        ).items()
        if annotation is bool
    }
    assert result_bool_names == result_true | result_false
    assert all(getattr(prepared_result, name) is True for name in result_true)
    assert all(getattr(prepared_result, name) is False for name in result_false)


def test_fixed_address_replay_is_deterministic_and_global_rng_is_unchanged(
    certified_bundle,
    prepared_result,
):
    owner = certified_bundle["owner"]
    before = _rng_snapshot()
    replay = owner.prepare(prepared_result.run_id, prepared_result.initialization_index)
    _assert_rng_unchanged(before)
    assert replay is not prepared_result
    assert replay.result_sha256 == prepared_result.result_sha256
    assert replay.logical_word_coordinates == prepared_result.logical_word_coordinates
    assert replay.attempt_sha256s == prepared_result.attempt_sha256s
    assert replay.deterministic_fixed_address_replay_only is True
    assert owner.certificate.actual_live_uniformity_certified is False
    assert owner.certificate.actual_live_independence_certified is False


@pytest.mark.parametrize(
    "position,value",
    (
        (0, True),
        (0, np.int64(1)),
        (0, np.uint64(1)),
        (0, 1.0),
        (0, -1),
        (0, UINT64_TOTAL),
        (1, True),
        (1, np.int64(1)),
        (1, np.uint64(1)),
        (1, 1.0),
        (1, -1),
        (1, UINT64_TOTAL),
    ),
)
def test_prepare_coordinates_are_preflighted_before_parent_allocation(
    certified_bundle,
    position,
    value,
):
    owner = certified_bundle["owner"]
    original = owner._protocol_allocate
    calls = []

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls.append("allocate")
        raise AssertionError("invalid coordinates must fail before allocation")

    object.__setattr__(owner, "_protocol_allocate", forbidden)
    arguments = [36_500, 0]
    arguments[position] = value
    try:
        with pytest.raises((TypeError, ValueError)):
            owner.prepare(*arguments)
    finally:
        object.__setattr__(owner, "_protocol_allocate", original)
    assert calls == []


def test_validation_replays_cp27_and_cp30_but_never_allocates_or_initializes_cp28(
    certified_bundle,
    prepared_result,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    original_allocate = owner._protocol_allocate
    calls = {"allocate": 0, "initialize": 0, "cp27": 0, "cp30": 0}
    original_cp27 = owner._protocol_validate_result
    original_cp30 = owner._tilt_validate_evaluation

    def forbidden_allocate(*args, **kwargs):
        del args, kwargs
        calls["allocate"] += 1
        raise AssertionError("validation must not allocate")

    def forbidden_initialize(*args, **kwargs):
        del args, kwargs
        calls["initialize"] += 1
        raise AssertionError("validation must not invoke CP28 initialize")

    def cp27_probe(*args, **kwargs):
        calls["cp27"] += 1
        return original_cp27(*args, **kwargs)

    def cp30_probe(*args, **kwargs):
        calls["cp30"] += 1
        return original_cp30(*args, **kwargs)

    monkeypatch.setattr(preparation._CP27_TYPE, "allocate", forbidden_allocate)
    monkeypatch.setattr(preparation, "_CP27_ALLOCATE", forbidden_allocate)
    monkeypatch.setattr(preparation._CP27_TYPE, "validate_result", cp27_probe)
    monkeypatch.setattr(preparation, "_CP27_VALIDATE_RESULT", cp27_probe)
    monkeypatch.setattr(
        preparation._TILT_TYPE,
        "validate_evaluation",
        cp30_probe,
    )
    monkeypatch.setattr(preparation, "_TILT_VALIDATE_EVALUATION", cp30_probe)
    object.__setattr__(owner, "_protocol_allocate", forbidden_allocate)
    object.__setattr__(owner, "_protocol_validate_result", cp27_probe)
    object.__setattr__(owner, "_tilt_validate_evaluation", cp30_probe)
    monkeypatch.setattr(preparation._CP28_TYPE, "initialize", forbidden_initialize)
    try:
        assert (
            owner.validate_result(
                prepared_result,
                prepared_result.run_id,
                prepared_result.initialization_index,
            )
            is prepared_result
        )
    finally:
        object.__setattr__(owner, "_protocol_allocate", original_allocate)
        object.__setattr__(owner, "_protocol_validate_result", original_cp27)
        object.__setattr__(owner, "_tilt_validate_evaluation", original_cp30)
    assert calls == {
        "allocate": 0,
        "initialize": 0,
        "cp27": 1,
        "cp30": prepared_result.attempt_budget,
    }


def test_protocol_allocation_happens_once_and_wrong_type_stops_all_next_steps(
    certified_bundle,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    originals = {
        "allocate": owner._protocol_allocate,
        "validate": owner._protocol_validate_result,
        "slot": owner._slot_materializer,
        "score": owner._tilt_evaluate,
    }
    calls = {name: 0 for name in originals}

    def wrong_allocate(*args, **kwargs):
        del args, kwargs
        calls["allocate"] += 1
        return object()

    def forbidden(name):
        def callback(*args, **kwargs):
            del args, kwargs
            calls[name] += 1
            raise AssertionError("the next callback must not execute")

        return callback

    forbidden_validate = forbidden("validate")
    forbidden_slot = forbidden("slot")
    forbidden_score = forbidden("score")
    monkeypatch.setattr(preparation._CP27_TYPE, "allocate", wrong_allocate)
    monkeypatch.setattr(preparation, "_CP27_ALLOCATE", wrong_allocate)
    monkeypatch.setattr(
        preparation._CP27_TYPE,
        "validate_result",
        forbidden_validate,
    )
    monkeypatch.setattr(preparation, "_CP27_VALIDATE_RESULT", forbidden_validate)
    monkeypatch.setattr(
        preparation._reference,
        "_materialize_slot_fields",
        forbidden_slot,
    )
    monkeypatch.setattr(
        preparation,
        "_CP28_MATERIALIZE_SLOT_FIELDS",
        forbidden_slot,
    )
    monkeypatch.setattr(preparation._TILT_TYPE, "evaluate", forbidden_score)
    monkeypatch.setattr(preparation, "_TILT_EVALUATE", forbidden_score)
    object.__setattr__(owner, "_protocol_allocate", wrong_allocate)
    object.__setattr__(owner, "_protocol_validate_result", forbidden_validate)
    object.__setattr__(owner, "_slot_materializer", forbidden_slot)
    object.__setattr__(owner, "_tilt_evaluate", forbidden_score)
    try:
        with pytest.raises(TypeError, match="parent_protocol_result|CP27|type"):
            owner.prepare(36_600, 0)
    finally:
        object.__setattr__(owner, "_protocol_allocate", originals["allocate"])
        object.__setattr__(owner, "_protocol_validate_result", originals["validate"])
        object.__setattr__(owner, "_slot_materializer", originals["slot"])
        object.__setattr__(owner, "_tilt_evaluate", originals["score"])
    assert calls == {"allocate": 1, "validate": 0, "slot": 0, "score": 0}


def test_full_parent_prefix_exists_before_first_score_callback(
    certified_bundle,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    original_allocate = owner._protocol_allocate
    original_evaluate = owner._tilt_evaluate
    captured = {}
    observed = []

    def allocate_probe(*args, **kwargs):
        parent = original_allocate(*args, **kwargs)
        captured["parent"] = parent
        return parent

    def probe(composer, configuration, *, residual_context):
        parent = captured["parent"]
        observed.append(
            (
                parent.stream_record_count,
                parent.total_raw64_words,
                len(parent.entries),
                all(entry.raw64_words for entry in parent.entries),
            )
        )
        return original_evaluate(
            composer,
            configuration,
            residual_context=residual_context,
        )

    monkeypatch.setattr(preparation._CP27_TYPE, "allocate", allocate_probe)
    monkeypatch.setattr(preparation, "_CP27_ALLOCATE", allocate_probe)
    monkeypatch.setattr(preparation._TILT_TYPE, "evaluate", probe)
    monkeypatch.setattr(preparation, "_TILT_EVALUATE", probe)
    object.__setattr__(owner, "_protocol_allocate", allocate_probe)
    object.__setattr__(owner, "_tilt_evaluate", probe)
    try:
        result = owner.prepare(36_601, 0)
    finally:
        object.__setattr__(owner, "_protocol_allocate", original_allocate)
        object.__setattr__(owner, "_tilt_evaluate", original_evaluate)
    expected = (
        result.total_stream_records,
        result.total_raw64_words,
        result.total_stream_records,
        True,
    )
    assert len(observed) >= result.attempt_budget
    assert all(item == expected for item in observed)


def test_slot_materializer_failure_is_not_retried_and_blocks_score(
    certified_bundle,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    original_slot = owner._slot_materializer
    original_score = owner._tilt_evaluate
    calls = {"slot": 0, "score": 0}

    def fail_once(*args, **kwargs):
        del args, kwargs
        calls["slot"] += 1
        raise RuntimeError("one materializer failure")

    def forbidden_score(*args, **kwargs):
        del args, kwargs
        calls["score"] += 1
        raise AssertionError("scoring must not begin")

    monkeypatch.setattr(preparation._reference, "_materialize_slot_fields", fail_once)
    monkeypatch.setattr(preparation, "_CP28_MATERIALIZE_SLOT_FIELDS", fail_once)
    monkeypatch.setattr(preparation._TILT_TYPE, "evaluate", forbidden_score)
    monkeypatch.setattr(preparation, "_TILT_EVALUATE", forbidden_score)
    object.__setattr__(owner, "_slot_materializer", fail_once)
    object.__setattr__(owner, "_tilt_evaluate", forbidden_score)
    try:
        with pytest.raises(RuntimeError, match="one materializer"):
            owner.prepare(36_602, 0)
    finally:
        object.__setattr__(owner, "_slot_materializer", original_slot)
        object.__setattr__(owner, "_tilt_evaluate", original_score)
    assert calls == {"slot": 1, "score": 0}


def test_cp30_wrong_type_is_called_once_and_late_failure_returns_no_result(
    certified_bundle,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    original_evaluate = owner._tilt_evaluate
    original_validate = owner._tilt_validate_evaluation
    calls = {"evaluate": 0, "validate": 0}

    def wrong_type(*args, **kwargs):
        del args, kwargs
        calls["evaluate"] += 1
        return object()

    def forbidden_validate(*args, **kwargs):
        del args, kwargs
        calls["validate"] += 1
        raise AssertionError("wrong score must not be validated")

    monkeypatch.setattr(preparation._TILT_TYPE, "evaluate", wrong_type)
    monkeypatch.setattr(preparation, "_TILT_EVALUATE", wrong_type)
    monkeypatch.setattr(
        preparation._TILT_TYPE, "validate_evaluation", forbidden_validate
    )
    monkeypatch.setattr(preparation, "_TILT_VALIDATE_EVALUATION", forbidden_validate)
    object.__setattr__(owner, "_tilt_evaluate", wrong_type)
    object.__setattr__(owner, "_tilt_validate_evaluation", forbidden_validate)
    try:
        with pytest.raises(
            TypeError,
            match="CP30 evaluate returned|wrong exact checkpoint-30 type",
        ):
            owner.prepare(36_603, 0)
    finally:
        object.__setattr__(owner, "_tilt_evaluate", original_evaluate)
        object.__setattr__(owner, "_tilt_validate_evaluation", original_validate)
    assert calls == {"evaluate": 1, "validate": 0}


@pytest.mark.parametrize("target", ("attempt", "slot", "score"))
def test_cp27_validation_callback_cannot_mutate_result_tree_before_cp30(
    certified_bundle,
    prepared_result,
    monkeypatch,
    target,
):
    owner = certified_bundle["owner"]
    original_cp27 = owner._protocol_validate_result
    original_cp30 = owner._tilt_validate_evaluation
    attempt = prepared_result.attempts[0]
    if target == "attempt":
        record = attempt
        field = "reserved_decision_word_uninterpreted"
        replacement = False
    elif target == "slot":
        record = attempt.proposal_raw_slots[0]
        field = "active"
        replacement = not record.active
    else:
        record = attempt.score_evaluation
        field = "evaluation_sha256"
        replacement = "0" * 64
    original_value = getattr(record, field)
    calls = {"cp27": 0, "cp30": 0}

    def mutate_after_cp27_validation(*args, **kwargs):
        checked = original_cp27(*args, **kwargs)
        calls["cp27"] += 1
        object.__setattr__(record, field, replacement)
        return checked

    def forbidden_cp30(*args, **kwargs):
        del args, kwargs
        calls["cp30"] += 1
        raise AssertionError("mutation must be caught before the first CP30 call")

    monkeypatch.setattr(
        preparation._CP27_TYPE,
        "validate_result",
        mutate_after_cp27_validation,
    )
    monkeypatch.setattr(
        preparation,
        "_CP27_VALIDATE_RESULT",
        mutate_after_cp27_validation,
    )
    monkeypatch.setattr(
        preparation._TILT_TYPE,
        "validate_evaluation",
        forbidden_cp30,
    )
    monkeypatch.setattr(
        preparation,
        "_TILT_VALIDATE_EVALUATION",
        forbidden_cp30,
    )
    object.__setattr__(
        owner,
        "_protocol_validate_result",
        mutate_after_cp27_validation,
    )
    object.__setattr__(owner, "_tilt_validate_evaluation", forbidden_cp30)
    try:
        with pytest.raises(
            (TypeError, ValueError),
            match="changed|differs|remain",
        ):
            owner.validate_result(
                prepared_result,
                prepared_result.run_id,
                prepared_result.initialization_index,
            )
    finally:
        object.__setattr__(record, field, original_value)
        object.__setattr__(owner, "_protocol_validate_result", original_cp27)
        object.__setattr__(owner, "_tilt_validate_evaluation", original_cp30)
    assert calls == {"cp27": 1, "cp30": 0}


def test_later_attempt_callback_cannot_mutate_completed_attempt(
    certified_bundle,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    original_evaluate = owner._tilt_evaluate
    attempt_type = preparation.CounterKeyedInitialTiltRejectionAttempt
    original_attempt_init = attempt_type.__init__
    completed = []
    calls = []

    def capture_attempt(self, *args, **kwargs):
        original_attempt_init(self, *args, **kwargs)
        completed.append(self)

    def mutate_completed_attempt(*args, **kwargs):
        calls.append("evaluate")
        if completed:
            object.__setattr__(
                completed[0],
                "reserved_decision_word_uninterpreted",
                False,
            )
        return original_evaluate(*args, **kwargs)

    monkeypatch.setattr(attempt_type, "__init__", capture_attempt)
    monkeypatch.setattr(preparation._TILT_TYPE, "evaluate", mutate_completed_attempt)
    monkeypatch.setattr(preparation, "_TILT_EVALUATE", mutate_completed_attempt)
    object.__setattr__(owner, "_tilt_evaluate", mutate_completed_attempt)
    try:
        with pytest.raises((TypeError, ValueError), match="attempt|changed|differs"):
            owner.prepare(36_604, 0)
    finally:
        if completed:
            object.__setattr__(
                completed[0],
                "reserved_decision_word_uninterpreted",
                True,
            )
        object.__setattr__(owner, "_tilt_evaluate", original_evaluate)
    assert calls[:2] == ["evaluate", "evaluate"]
    assert len(completed) == 1


def test_later_callback_cannot_mutate_earlier_materialized_field_map(
    certified_bundle,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    original_materialize = owner._slot_materializer
    original_evaluate = owner._tilt_evaluate
    materialized = []
    calls = []

    def capture_fields(*args, **kwargs):
        fields = original_materialize(*args, **kwargs)
        materialized.append(fields)
        return fields

    def mutate_fields_before_scoring(*args, **kwargs):
        calls.append("evaluate")
        current = materialized[-1]["type_quota_position"]
        materialized[-1]["type_quota_position"] = 1 - current
        return original_evaluate(*args, **kwargs)

    monkeypatch.setattr(
        preparation._reference,
        "_materialize_slot_fields",
        capture_fields,
    )
    monkeypatch.setattr(
        preparation,
        "_CP28_MATERIALIZE_SLOT_FIELDS",
        capture_fields,
    )
    monkeypatch.setattr(
        preparation._TILT_TYPE,
        "evaluate",
        mutate_fields_before_scoring,
    )
    monkeypatch.setattr(preparation, "_TILT_EVALUATE", mutate_fields_before_scoring)
    object.__setattr__(owner, "_slot_materializer", capture_fields)
    object.__setattr__(owner, "_tilt_evaluate", mutate_fields_before_scoring)
    try:
        with pytest.raises(
            (TypeError, ValueError),
            match="materialized|changed|differs",
        ):
            owner.prepare(36_605, 0)
    finally:
        if materialized:
            materialized[-1]["type_quota_position"] = (
                1 - materialized[-1]["type_quota_position"]
            )
        object.__setattr__(owner, "_slot_materializer", original_materialize)
        object.__setattr__(owner, "_tilt_evaluate", original_evaluate)
    assert calls == ["evaluate"]


def test_cp28_validator_cannot_mutate_current_slot_after_validation(
    certified_bundle,
    prepared_result,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    original_cp28 = preparation._CP28_VALIDATE_SLOT_RECORD
    original_cp27 = owner._protocol_validate_result
    target = prepared_result.attempts[0].proposal_raw_slots[0]
    calls = {"cp28": 0, "cp27": 0}

    def mutate_current(slot):
        checked = original_cp28(slot)
        calls["cp28"] += 1
        object.__setattr__(slot, "all_coordinate_padding_materialized", False)
        return checked

    def forbidden_cp27(*args, **kwargs):
        del args, kwargs
        calls["cp27"] += 1
        raise AssertionError("slot mutation must fail before CP27 replay")

    monkeypatch.setattr(
        preparation._reference,
        "_validate_slot_record",
        mutate_current,
    )
    monkeypatch.setattr(preparation, "_CP28_VALIDATE_SLOT_RECORD", mutate_current)
    monkeypatch.setattr(preparation._CP27_TYPE, "validate_result", forbidden_cp27)
    monkeypatch.setattr(preparation, "_CP27_VALIDATE_RESULT", forbidden_cp27)
    object.__setattr__(owner, "_protocol_validate_result", forbidden_cp27)
    try:
        with pytest.raises((TypeError, ValueError), match="slot|changed|differs"):
            owner.validate_result(
                prepared_result,
                prepared_result.run_id,
                prepared_result.initialization_index,
            )
    finally:
        object.__setattr__(target, "all_coordinate_padding_materialized", True)
        object.__setattr__(owner, "_protocol_validate_result", original_cp27)
    assert calls == {"cp28": 1, "cp27": 0}


def test_cp28_validator_of_later_attempt_cannot_mutate_earlier_slot(
    certified_bundle,
    prepared_result,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    original_cp28 = preparation._CP28_VALIDATE_SLOT_RECORD
    original_cp27 = owner._protocol_validate_result
    earlier = prepared_result.attempts[0].proposal_raw_slots[0]
    calls = {"cp28": 0, "cp27": 0}

    def mutate_earlier_from_later(slot):
        checked = original_cp28(slot)
        calls["cp28"] += 1
        if calls["cp28"] == 2:
            object.__setattr__(
                earlier,
                "all_coordinate_padding_materialized",
                False,
            )
        return checked

    def forbidden_cp27(*args, **kwargs):
        del args, kwargs
        calls["cp27"] += 1
        raise AssertionError("earlier-slot mutation must fail before CP27 replay")

    monkeypatch.setattr(
        preparation._reference,
        "_validate_slot_record",
        mutate_earlier_from_later,
    )
    monkeypatch.setattr(
        preparation,
        "_CP28_VALIDATE_SLOT_RECORD",
        mutate_earlier_from_later,
    )
    monkeypatch.setattr(preparation._CP27_TYPE, "validate_result", forbidden_cp27)
    monkeypatch.setattr(preparation, "_CP27_VALIDATE_RESULT", forbidden_cp27)
    object.__setattr__(owner, "_protocol_validate_result", forbidden_cp27)
    try:
        with pytest.raises((TypeError, ValueError), match="slot|changed|differs"):
            owner.validate_result(
                prepared_result,
                prepared_result.run_id,
                prepared_result.initialization_index,
            )
    finally:
        object.__setattr__(earlier, "all_coordinate_padding_materialized", True)
        object.__setattr__(owner, "_protocol_validate_result", original_cp27)
    assert calls == {"cp28": 2, "cp27": 0}


@pytest.mark.parametrize("target", ("parent_result", "attempt"))
@pytest.mark.parametrize("caller", ("helper", "owner"))
def test_cp27_record_validator_cannot_mutate_presnapshot_operation_tree(
    certified_bundle,
    prepared_result,
    monkeypatch,
    target,
    caller,
):
    owner = certified_bundle["owner"]
    original_record_validator = preparation._CP27_VALIDATE_RESULT_RECORD
    original_live_validator = owner._protocol_validate_result
    if target == "parent_result":
        record = prepared_result.parent_protocol_result
        field = "fixed_nonadaptive_budget"
    else:
        record = prepared_result.attempts[0]
        field = "reserved_decision_word_uninterpreted"
    original_value = getattr(record, field)
    calls = {"record": 0, "live": 0}

    def mutate_after_record_validation(parent):
        checked = original_record_validator(parent)
        calls["record"] += 1
        object.__setattr__(record, field, False)
        return checked

    def forbidden_live_validation(*args, **kwargs):
        del args, kwargs
        calls["live"] += 1
        raise AssertionError("pre-snapshot mutation must fail before live CP27")

    monkeypatch.setattr(
        preparation._PROTOCOL,
        "_validate_result_record",
        mutate_after_record_validation,
    )
    monkeypatch.setattr(
        preparation,
        "_CP27_VALIDATE_RESULT_RECORD",
        mutate_after_record_validation,
    )
    if caller == "owner":
        monkeypatch.setattr(
            preparation._CP27_TYPE,
            "validate_result",
            forbidden_live_validation,
        )
        monkeypatch.setattr(
            preparation,
            "_CP27_VALIDATE_RESULT",
            forbidden_live_validation,
        )
        object.__setattr__(
            owner,
            "_protocol_validate_result",
            forbidden_live_validation,
        )
    try:
        with pytest.raises((TypeError, ValueError), match="changed|differs|attempt"):
            if caller == "helper":
                preparation._validate_result_values(
                    {
                        name: getattr(prepared_result, name)
                        for name in preparation._result_fields()
                    }
                )
            else:
                owner.validate_result(
                    prepared_result,
                    prepared_result.run_id,
                    prepared_result.initialization_index,
                )
    finally:
        object.__setattr__(record, field, original_value)
        object.__setattr__(
            owner,
            "_protocol_validate_result",
            original_live_validator,
        )
    assert calls == {"record": 1, "live": 0}


def test_cp28_certificate_validator_cannot_mutate_result_attempt_in_helper(
    prepared_result,
    monkeypatch,
):
    original_cp28 = preparation._CP28_VALIDATE_CERTIFICATE
    original_cp27_record = preparation._CP27_VALIDATE_RESULT_RECORD
    attempt = prepared_result.attempts[0]
    calls = {"cp28": 0, "cp27_record": 0}
    mutated = []

    def mutate_attempt(parent):
        checked = original_cp28(parent)
        calls["cp28"] += 1
        if not mutated:
            object.__setattr__(
                attempt,
                "reserved_decision_word_uninterpreted",
                False,
            )
            mutated.append(True)
        return checked

    def forbidden_cp27_record(*args, **kwargs):
        del args, kwargs
        calls["cp27_record"] += 1
        raise AssertionError("attempt mutation must fail before CP27 record replay")

    monkeypatch.setattr(
        preparation._reference,
        "_validate_certificate",
        mutate_attempt,
    )
    monkeypatch.setattr(preparation, "_CP28_VALIDATE_CERTIFICATE", mutate_attempt)
    monkeypatch.setattr(
        preparation._PROTOCOL,
        "_validate_result_record",
        forbidden_cp27_record,
    )
    monkeypatch.setattr(
        preparation,
        "_CP27_VALIDATE_RESULT_RECORD",
        forbidden_cp27_record,
    )
    try:
        with pytest.raises((TypeError, ValueError), match="attempt|changed|remain"):
            preparation._validate_result_values(
                {
                    name: getattr(prepared_result, name)
                    for name in preparation._result_fields()
                }
            )
    finally:
        object.__setattr__(
            attempt,
            "reserved_decision_word_uninterpreted",
            True,
        )
    assert calls["cp28"] >= 1
    assert calls["cp27_record"] == 0
    assert original_cp27_record is not forbidden_cp27_record


def test_cp28_certificate_callback_in_live_owner_cannot_mutate_result_attempt(
    certified_bundle,
    prepared_result,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    original_cp28 = preparation._CP28_VALIDATE_CERTIFICATE
    original_cp27_live = preparation._CP27_LIVE
    attempt = prepared_result.attempts[0]
    calls = {"cp28": 0, "cp27_live": 0, "result_semantics": 0}
    mutated = []

    def mutate_attempt(parent):
        checked = original_cp28(parent)
        calls["cp28"] += 1
        if not mutated:
            object.__setattr__(
                attempt,
                "reserved_decision_word_uninterpreted",
                False,
            )
            mutated.append(True)
        return checked

    def forbidden_cp27_live(*args, **kwargs):
        del args, kwargs
        calls["cp27_live"] += 1
        raise AssertionError("attempt mutation must fail before live CP27")

    def forbidden_result_semantics(*args, **kwargs):
        del args, kwargs
        calls["result_semantics"] += 1
        raise AssertionError("attempt mutation must fail before result semantics")

    monkeypatch.setattr(
        preparation._reference,
        "_validate_certificate",
        mutate_attempt,
    )
    monkeypatch.setattr(preparation, "_CP28_VALIDATE_CERTIFICATE", mutate_attempt)
    monkeypatch.setattr(
        preparation._CP27_TYPE,
        "_require_live_binding",
        forbidden_cp27_live,
    )
    monkeypatch.setattr(preparation, "_CP27_LIVE", forbidden_cp27_live)
    monkeypatch.setattr(
        preparation,
        "_validate_result_values",
        forbidden_result_semantics,
    )
    try:
        with pytest.raises((TypeError, ValueError), match="attempt|changed|remain"):
            owner.validate_result(
                prepared_result,
                prepared_result.run_id,
                prepared_result.initialization_index,
            )
    finally:
        object.__setattr__(
            attempt,
            "reserved_decision_word_uninterpreted",
            True,
        )
    assert calls["cp28"] >= 1
    assert calls["cp27_live"] == 0
    assert calls["result_semantics"] == 0
    assert original_cp27_live is not forbidden_cp27_live


def test_hypothesis_cp28_callback_cannot_mutate_persistent_cp30_certificate(
    certified_bundle,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    original_cp28 = preparation._CP28_VALIDATE_CERTIFICATE
    parent30 = owner.certificate.checkpoint30_certificate
    original_digest = parent30.composer_runtime_sha256
    calls = {"cp28": 0, "manifest": 0}

    def mutate_persistent_parent(parent):
        checked = original_cp28(parent)
        calls["cp28"] += 1
        object.__setattr__(parent30, "composer_runtime_sha256", "f" * 64)
        return checked

    def forbidden_manifest(*args, **kwargs):
        del args, kwargs
        calls["manifest"] += 1
        raise AssertionError("persistent mutation must fail before manifest callback")

    monkeypatch.setattr(
        preparation,
        "_CP28_VALIDATE_CERTIFICATE",
        mutate_persistent_parent,
    )
    monkeypatch.setattr(preparation, "_CP28_VALIDATE_MANIFEST", forbidden_manifest)
    try:
        with pytest.raises(
            (TypeError, ValueError),
            match="certificate|changed|differs|runtime",
        ):
            owner._require_persistent_records()
    finally:
        object.__setattr__(parent30, "composer_runtime_sha256", original_digest)
    assert calls == {"cp28": 1, "manifest": 0}


@pytest.mark.parametrize("target", ("alien_cp26", "alien_cp30"))
def test_cp28_callback_cannot_mutate_alien_attempt_certificate_subtree(
    prepared_result,
    monkeypatch,
    target,
):
    attempt = prepared_result.attempts[0]
    values = {name: getattr(attempt, name) for name in preparation._attempt_fields()}
    if target == "alien_cp26":
        entry = attempt.parent_entries[0]
        consumption = entry.parent_consumption
        alien_certificate = _forged(consumption.certificate)
        alien_stream = _forged(
            consumption.control_stream,
            certificate=alien_certificate,
        )
        alien_consumption = _forged(
            consumption,
            certificate=alien_certificate,
            control_stream=alien_stream,
        )
        alien_entry = _forged(entry, parent_consumption=alien_consumption)
        values["parent_entries"] = (alien_entry, *attempt.parent_entries[1:])
        field = "control_runtime_sha256"
    else:
        score = attempt.score_evaluation
        alien_certificate = _forged(score.certificate)
        alien_score = _forged(score, certificate=alien_certificate)
        values["score_evaluation"] = alien_score
        field = "composer_runtime_sha256"
    original_value = getattr(alien_certificate, field)
    original_cp28 = preparation._CP28_VALIDATE_CERTIFICATE
    calls = {"cp28": 0, "next": 0}

    def mutate_alien_certificate(parent):
        checked = original_cp28(parent)
        calls["cp28"] += 1
        object.__setattr__(alien_certificate, field, "e" * 64)
        return checked

    def forbidden_next(*args, **kwargs):
        del args, kwargs
        calls["next"] += 1
        raise AssertionError("alien mutation must fail before the next callback")

    monkeypatch.setattr(
        preparation,
        "_CP28_VALIDATE_CERTIFICATE",
        mutate_alien_certificate,
    )
    monkeypatch.setattr(preparation, "_CP27_VALIDATE_CERTIFICATE", forbidden_next)
    try:
        with pytest.raises(
            (TypeError, ValueError),
            match="certificate|changed|differs|runtime",
        ):
            preparation._validate_attempt_values(values)
    finally:
        object.__setattr__(alien_certificate, field, original_value)
    assert calls == {"cp28": 1, "next": 0}


@pytest.mark.parametrize("target", ("parent_nested", "slot", "score"))
def test_cp28_certificate_validator_cannot_mutate_attempt_tree_before_slots(
    prepared_result,
    monkeypatch,
    target,
):
    attempt = prepared_result.attempts[0]
    original_cp28 = preparation._CP28_VALIDATE_CERTIFICATE
    original_slot_validator = preparation._CP28_VALIDATE_SLOT_RECORD
    if target == "parent_nested":
        record = attempt.parent_entries[
            0
        ].parent_consumption.control_stream.initial_state
        field = "buffer_pos"
        replacement = 0 if record.buffer_pos != 0 else 1
    elif target == "slot":
        record = attempt.proposal_raw_slots[0]
        field = "all_coordinate_padding_materialized"
        replacement = False
    else:
        record = attempt.score_evaluation
        field = "evaluation_sha256"
        replacement = "0" * 64
    original_value = getattr(record, field)
    calls = {"cp28": 0, "slot": 0}
    mutated = []

    def mutate_attempt_tree(parent):
        checked = original_cp28(parent)
        calls["cp28"] += 1
        if not mutated:
            object.__setattr__(record, field, replacement)
            mutated.append(True)
        return checked

    def forbidden_slot_validator(*args, **kwargs):
        del args, kwargs
        calls["slot"] += 1
        raise AssertionError("certificate mutation must fail before slot validation")

    monkeypatch.setattr(
        preparation._reference,
        "_validate_certificate",
        mutate_attempt_tree,
    )
    monkeypatch.setattr(
        preparation,
        "_CP28_VALIDATE_CERTIFICATE",
        mutate_attempt_tree,
    )
    monkeypatch.setattr(
        preparation._reference,
        "_validate_slot_record",
        forbidden_slot_validator,
    )
    monkeypatch.setattr(
        preparation,
        "_CP28_VALIDATE_SLOT_RECORD",
        forbidden_slot_validator,
    )
    try:
        with pytest.raises(
            (TypeError, ValueError),
            match="attempt|changed|differs|remain|state",
        ):
            preparation._validate_attempt_values(
                {name: getattr(attempt, name) for name in preparation._attempt_fields()}
            )
    finally:
        object.__setattr__(record, field, original_value)
    assert calls["cp28"] >= 1
    assert calls["slot"] == 0
    assert original_slot_validator is not forbidden_slot_validator


def test_cp28_slot_validator_cannot_mutate_parent_tree_during_result_helper(
    prepared_result,
    monkeypatch,
):
    original_slot_validator = preparation._CP28_VALIDATE_SLOT_RECORD
    state = prepared_result.parent_protocol_result.entries[
        0
    ].parent_consumption.control_stream.initial_state
    original_position = state.buffer_pos
    replacement = 0 if original_position != 0 else 1
    calls = []

    def mutate_parent_after_slot_validation(slot):
        checked = original_slot_validator(slot)
        calls.append("slot")
        object.__setattr__(state, "buffer_pos", replacement)
        return checked

    monkeypatch.setattr(
        preparation._reference,
        "_validate_slot_record",
        mutate_parent_after_slot_validation,
    )
    monkeypatch.setattr(
        preparation,
        "_CP28_VALIDATE_SLOT_RECORD",
        mutate_parent_after_slot_validation,
    )
    try:
        with pytest.raises(
            (TypeError, ValueError),
            match="parent|state|changed|differs",
        ):
            preparation._validate_result_values(
                {
                    name: getattr(prepared_result, name)
                    for name in preparation._result_fields()
                }
            )
    finally:
        object.__setattr__(state, "buffer_pos", original_position)
    assert calls == ["slot"]


@pytest.mark.parametrize("stage", ("parent", "fields", "slot", "score"))
def test_dependency_return_cannot_bless_mutated_fresh_callback_output(
    certified_bundle,
    monkeypatch,
    stage,
):
    owner = certified_bundle["owner"]
    original_cp28_live = preparation._CP28_LIVE
    retained = {}
    mutation = {}
    calls = {"producer": 0, "dependency": 0, "downstream": 0}
    owner_restores = []

    def retain_output(original):
        def callback(*args, **kwargs):
            value = original(*args, **kwargs)
            calls["producer"] += 1
            retained["value"] = value
            return value

        return callback

    def mutate_retained_output():
        value = retained["value"]
        if stage == "parent":
            field = "fixed_nonadaptive_budget"
            before = value.fixed_nonadaptive_budget
            object.__setattr__(value, field, False)
        elif stage == "fields":
            field = "type_quota_position"
            before = value[field]
            value[field] = 1 - before
        elif stage == "slot":
            field = "all_coordinate_padding_materialized"
            before = value.all_coordinate_padding_materialized
            object.__setattr__(value, field, False)
        else:
            field = "evaluation_sha256"
            before = value.evaluation_sha256
            object.__setattr__(value, field, "0" * 64)
        mutation.update(value=value, field=field, before=before)

    def dependency_callback(initializer_owner):
        checked = original_cp28_live(initializer_owner)
        calls["dependency"] += 1
        if retained and not mutation:
            mutate_retained_output()
        return checked

    def downstream_callback(original):
        def callback(*args, **kwargs):
            if mutation:
                calls["downstream"] += 1
                raise AssertionError(
                    "mutated fresh output must fail before its downstream consumer"
                )
            return original(*args, **kwargs)

        return callback

    def patch_owner(name, callback):
        owner_restores.append((name, getattr(owner, name)))
        object.__setattr__(owner, name, callback)

    monkeypatch.setattr(
        preparation._CP28_TYPE,
        "_require_live_binding",
        dependency_callback,
    )
    monkeypatch.setattr(preparation, "_CP28_LIVE", dependency_callback)

    if stage == "parent":
        producer = retain_output(owner._protocol_allocate)
        consumer = downstream_callback(owner._protocol_validate_result)
        monkeypatch.setattr(preparation._CP27_TYPE, "allocate", producer)
        monkeypatch.setattr(preparation, "_CP27_ALLOCATE", producer)
        patch_owner("_protocol_allocate", producer)
        monkeypatch.setattr(preparation._CP27_TYPE, "validate_result", consumer)
        monkeypatch.setattr(preparation, "_CP27_VALIDATE_RESULT", consumer)
        patch_owner("_protocol_validate_result", consumer)
    elif stage == "fields":
        producer = retain_output(owner._slot_materializer)
        consumer = downstream_callback(owner._slot_maker)
        monkeypatch.setattr(
            preparation._reference,
            "_materialize_slot_fields",
            producer,
        )
        monkeypatch.setattr(preparation, "_CP28_MATERIALIZE_SLOT_FIELDS", producer)
        patch_owner("_slot_materializer", producer)
        monkeypatch.setattr(preparation._reference, "_make_slot", consumer)
        monkeypatch.setattr(preparation, "_CP28_MAKE_SLOT", consumer)
        patch_owner("_slot_maker", consumer)
    elif stage == "slot":
        producer = retain_output(owner._slot_maker)
        consumer = downstream_callback(preparation._CP28_VALIDATE_SLOT_RECORD)
        monkeypatch.setattr(preparation._reference, "_make_slot", producer)
        monkeypatch.setattr(preparation, "_CP28_MAKE_SLOT", producer)
        patch_owner("_slot_maker", producer)
        monkeypatch.setattr(
            preparation._reference,
            "_validate_slot_record",
            consumer,
        )
        monkeypatch.setattr(preparation, "_CP28_VALIDATE_SLOT_RECORD", consumer)
    else:
        producer = retain_output(owner._tilt_evaluate)
        consumer = downstream_callback(owner._tilt_validate_evaluation)
        monkeypatch.setattr(preparation._TILT_TYPE, "evaluate", producer)
        monkeypatch.setattr(preparation, "_TILT_EVALUATE", producer)
        patch_owner("_tilt_evaluate", producer)
        monkeypatch.setattr(
            preparation._TILT_TYPE,
            "validate_evaluation",
            consumer,
        )
        monkeypatch.setattr(preparation, "_TILT_VALIDATE_EVALUATION", consumer)
        patch_owner("_tilt_validate_evaluation", consumer)

    try:
        with pytest.raises(
            (TypeError, ValueError),
            match="changed|differs|remain|materialized|digest|budget",
        ):
            owner.prepare(
                36_606 + ("parent", "fields", "slot", "score").index(stage), 0
            )
    finally:
        if mutation:
            value = mutation["value"]
            if type(value) is dict:
                value[mutation["field"]] = mutation["before"]
            else:
                object.__setattr__(value, mutation["field"], mutation["before"])
        for name, original in reversed(owner_restores):
            object.__setattr__(owner, name, original)
    assert calls["producer"] == 1
    assert calls["dependency"] >= 1
    assert calls["downstream"] == 0
    assert mutation


def test_alien_cp26_subtree_is_snapshotted_before_certificate_callback(
    prepared_result,
    monkeypatch,
):
    attempt = prepared_result.attempts[0]
    original_entry = attempt.parent_entries[0]
    original_consumption = original_entry.parent_consumption
    original_stream = original_consumption.control_stream
    alien_address = _forged(original_stream.address)
    alien_initial_state = _forged(original_stream.initial_state)
    alien_stream = _forged(
        original_stream,
        address=alien_address,
        initial_state=alien_initial_state,
    )
    alien_consumption = _forged(
        original_consumption,
        control_stream=alien_stream,
        stream_initial_state=alien_initial_state,
    )
    alien_entry = _forged(
        original_entry,
        parent_consumption=alien_consumption,
    )
    alien_entries = (alien_entry, *attempt.parent_entries[1:])
    values = {name: getattr(attempt, name) for name in preparation._attempt_fields()}
    values["parent_entries"] = alien_entries
    original_cp28 = preparation._CP28_VALIDATE_CERTIFICATE
    calls = {"cp28": 0, "slot": 0}
    original_buffer_position = alien_initial_state.buffer_pos
    replacement = 0 if original_buffer_position != 0 else 1

    def mutate_alien_subtree(parent):
        checked = original_cp28(parent)
        calls["cp28"] += 1
        if calls["cp28"] == 1:
            object.__setattr__(alien_initial_state, "buffer_pos", replacement)
        return checked

    def forbidden_slot(*args, **kwargs):
        del args, kwargs
        calls["slot"] += 1
        raise AssertionError("alien-subtree mutation must fail before slot validation")

    monkeypatch.setattr(
        preparation._reference,
        "_validate_certificate",
        mutate_alien_subtree,
    )
    monkeypatch.setattr(
        preparation,
        "_CP28_VALIDATE_CERTIFICATE",
        mutate_alien_subtree,
    )
    monkeypatch.setattr(
        preparation._reference,
        "_validate_slot_record",
        forbidden_slot,
    )
    monkeypatch.setattr(preparation, "_CP28_VALIDATE_SLOT_RECORD", forbidden_slot)
    try:
        with pytest.raises(
            (TypeError, ValueError),
            match="alien|attempt|parent|state|changed|differs",
        ):
            preparation._validate_attempt_values(values)
    finally:
        object.__setattr__(
            alien_initial_state,
            "buffer_pos",
            original_buffer_position,
        )
    assert calls["cp28"] >= 1
    assert calls["slot"] == 0


def test_alien_exact_result_certificate_is_rejected_before_live_certificate(
    certified_bundle,
    prepared_result,
    monkeypatch,
):
    owner = certified_bundle["owner"]
    alien_certificate = _forged(owner.certificate)
    hostile = _forged(prepared_result, certificate=alien_certificate)
    calls = []

    def forbidden_live_certificate(*args, **kwargs):
        del args, kwargs
        calls.append("live certificate")
        raise AssertionError("alien certificate must fail before live callbacks")

    monkeypatch.setattr(
        type(owner),
        "_live_certificate",
        forbidden_live_certificate,
    )
    with pytest.raises(ValueError, match="certificate|owner|identity"):
        owner.validate_result(
            hostile,
            prepared_result.run_id,
            prepared_result.initialization_index,
        )
    assert calls == []


@pytest.mark.parametrize("target", ("nested_cp28", "manifest_type_ids"))
def test_result_certificate_tree_is_preflighted_before_parent_validators(
    prepared_result,
    monkeypatch,
    target,
):
    certificate = prepared_result.certificate
    bomb = _EqualityBomb()
    if target == "nested_cp28":
        hostile_parent = _forged(
            certificate.checkpoint28_certificate,
            maximum_raw_slots=bomb,
        )
        hostile_certificate = _forged(
            certificate,
            checkpoint28_certificate=hostile_parent,
        )
    else:
        hostile_manifest = _forged(
            certificate.manifest,
            type_ids=(bomb, *certificate.manifest.type_ids[1:]),
        )
        hostile_certificate = _forged(
            certificate,
            manifest=hostile_manifest,
        )
    values = {
        name: getattr(prepared_result, name) for name in preparation._result_fields()
    }
    values["certificate"] = hostile_certificate
    calls = []

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls.append("validator")
        raise AssertionError("malformed certificate must fail before validation")

    for module, name, frozen_name in (
        (preparation._reference, "_validate_certificate", "_CP28_VALIDATE_CERTIFICATE"),
        (preparation._PROTOCOL, "_validate_certificate", "_CP27_VALIDATE_CERTIFICATE"),
        (preparation._tilt, "_validate_certificate", "_TILT_VALIDATE_CERTIFICATE"),
        (preparation._reference, "_validate_manifest", "_CP28_VALIDATE_MANIFEST"),
    ):
        monkeypatch.setattr(module, name, forbidden)
        monkeypatch.setattr(preparation, frozen_name, forbidden)
    with pytest.raises(TypeError, match="primitive|integer|type_ids|certificate"):
        preparation._validate_result_values(values)
    assert bomb.calls == 0
    assert calls == []


def test_hypothesis_manifest_is_preflighted_before_direct_ancestry(
    certified_bundle,
    monkeypatch,
):
    hypothesis = certified_bundle["word_family_hypothesis"]
    bomb = _EqualityBomb()
    hostile_manifest = _forged(
        hypothesis.manifest,
        type_ids=(bomb, *hypothesis.manifest.type_ids[1:]),
    )
    hostile_hypothesis = _forged(hypothesis, manifest=hostile_manifest)
    calls = []

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls.append("ancestry")
        raise AssertionError("hostile hypothesis must fail before ancestry")

    monkeypatch.setattr(preparation, "_direct_ancestry", forbidden)
    with pytest.raises(TypeError, match="integer|type_ids|manifest"):
        _CERTIFY(
            certified_bundle["initializer_owner"],
            certified_bundle["initial_tilt"],
            residual_context=RESIDUAL_CONTEXT,
            attempt_budget=2,
            preparation_policy=PREPARATION_POLICY,
            preparation_role_sha256="5" * 64,
            word_family_hypothesis=hostile_hypothesis,
        )
    assert bomb.calls == 0
    assert calls == []


@pytest.mark.parametrize(
    "field",
    ("selected_raw_events", "canonical_configuration"),
)
def test_detached_event_is_snapshotted_before_early_certificate_callback(
    prepared_result,
    monkeypatch,
    field,
):
    attempt = next(
        candidate
        for candidate in prepared_result.attempts
        if candidate.canonical_configuration
    )
    original_event = getattr(attempt, field)[0]
    detached = TransformedEvent(
        original_event.event_type,
        original_event.coordinates,
    )
    assert detached is not original_event
    values = {name: getattr(attempt, name) for name in preparation._attempt_fields()}
    events = list(values[field])
    events[0] = detached
    values[field] = tuple(events)
    original_cp28 = preparation._CP28_VALIDATE_CERTIFICATE
    original_event_type = detached.event_type
    calls = {"cp28": 0, "slot": 0}
    mutated = []

    def mutate_detached_event(parent):
        checked = original_cp28(parent)
        calls["cp28"] += 1
        if not mutated:
            object.__setattr__(detached, "event_type", original_event_type ^ 1)
            mutated.append(True)
        return checked

    def forbidden_slot(*args, **kwargs):
        del args, kwargs
        calls["slot"] += 1
        raise AssertionError("detached-event mutation must fail before slot validation")

    monkeypatch.setattr(
        preparation._reference,
        "_validate_certificate",
        mutate_detached_event,
    )
    monkeypatch.setattr(
        preparation,
        "_CP28_VALIDATE_CERTIFICATE",
        mutate_detached_event,
    )
    monkeypatch.setattr(
        preparation._reference,
        "_validate_slot_record",
        forbidden_slot,
    )
    monkeypatch.setattr(preparation, "_CP28_VALIDATE_SLOT_RECORD", forbidden_slot)
    try:
        with pytest.raises((TypeError, ValueError), match="event|changed|differs"):
            preparation._validate_attempt_values(values)
    finally:
        object.__setattr__(detached, "event_type", original_event_type)
    assert calls["cp28"] >= 1
    assert calls["slot"] == 0


def test_attempt_reorder_duplicate_omission_and_parent_splice_are_refused(
    certified_bundle,
    prepared_result,
):
    owner = certified_bundle["owner"]
    first, second = prepared_result.attempts
    variants = (
        (second, first),
        (first, first),
        (first,),
    )
    for attempts in variants:
        hostile = _forged(
            prepared_result,
            **_result_values(prepared_result, attempts=attempts),
        )
        with pytest.raises((TypeError, ValueError)):
            owner.validate_result(
                hostile,
                prepared_result.run_id,
                prepared_result.initialization_index,
            )


def test_redigested_in_range_slot_cannot_disagree_with_type_proposal_word(
    certified_bundle,
    prepared_result,
):
    owner = certified_bundle["owner"]
    manifest = owner.certificate.manifest
    attempt_position, attempt = next(
        (position, candidate)
        for position, candidate in enumerate(prepared_result.attempts)
        if candidate.sampled_cardinality == 0
    )
    slot = attempt.proposal_raw_slots[0]
    assert slot.active is False
    assert len(manifest.type_ids) >= 2
    alternative_position = (slot.type_quota_position + 1) % len(manifest.type_ids)
    alternative_type = manifest.type_ids[alternative_position]
    alternative_dimension = dict(manifest.type_dimensions)[alternative_type]
    assert alternative_position != slot.type_quota_position
    assert alternative_type != slot.event_type
    assert alternative_dimension != slot.event_dimension
    alternative_coordinates = slot.coordinate_codebook_values[:alternative_dimension]
    alternative_event = TransformedEvent(alternative_type, alternative_coordinates)
    hostile_slot = _forged(
        slot,
        **checkpoint28._slot_values(
            slot,
            type_quota_position=alternative_position,
            event_type=alternative_type,
            event_dimension=alternative_dimension,
            active_coordinates=alternative_coordinates,
            event=alternative_event,
        ),
    )
    assert checkpoint28.initializer._validate_slot_record(hostile_slot) is hostile_slot
    assert hostile_slot.type_raw64_word == slot.type_raw64_word
    hostile_slots = (hostile_slot, *attempt.proposal_raw_slots[1:])
    hostile_attempt = _forged(
        attempt,
        **_attempt_values(
            attempt,
            proposal_raw_slots=hostile_slots,
            proposal_raw_slot_sha256s=tuple(
                candidate.slot_sha256 for candidate in hostile_slots
            ),
        ),
    )
    hostile_attempts = list(prepared_result.attempts)
    hostile_attempts[attempt_position] = hostile_attempt
    hostile_result = _forged(
        prepared_result,
        **_result_values(prepared_result, attempts=tuple(hostile_attempts)),
    )
    with pytest.raises(ValueError, match="type transform|proposal word|raw slot"):
        owner.validate_result(
            hostile_result,
            prepared_result.run_id,
            prepared_result.initialization_index,
        )


def test_reserved_decision_word_and_no_decision_flags_cannot_be_forged(
    certified_bundle,
    prepared_result,
):
    owner = certified_bundle["owner"]
    first = prepared_result.attempts[0]
    variants = (
        {"reserved_decision_raw64_word": first.reserved_decision_raw64_word ^ 1},
        {"reserved_decision_word_uninterpreted": False},
        {"acceptance_predicate_evaluated": True},
        {"acceptance_decision_made": True},
        {"exponential_or_uniform_transform_applied": True},
    )
    for updates in variants:
        hostile_attempt = _forged(first, **_attempt_values(first, **updates))
        hostile_result = _forged(
            prepared_result,
            **_result_values(
                prepared_result,
                attempts=(hostile_attempt, prepared_result.attempts[1]),
            ),
        )
        with pytest.raises((TypeError, ValueError)):
            owner.validate_result(
                hostile_result,
                prepared_result.run_id,
                prepared_result.initialization_index,
            )


def test_detached_equal_canonical_events_are_not_interchangeable(
    certified_bundle,
    prepared_result,
):
    owner = certified_bundle["owner"]
    position = next(
        index
        for index, attempt in enumerate(prepared_result.attempts)
        if attempt.canonical_configuration
    )
    attempt = prepared_result.attempts[position]
    detached = tuple(
        TransformedEvent(event.event_type, event.coordinates)
        for event in attempt.canonical_configuration
    )
    assert detached == attempt.canonical_configuration
    assert all(
        actual is not expected
        for actual, expected in zip(detached, attempt.canonical_configuration)
    )
    hostile_attempt = _forged(
        attempt,
        **_attempt_values(attempt, canonical_configuration=detached),
    )
    attempts = list(prepared_result.attempts)
    attempts[position] = hostile_attempt
    hostile_result = _forged(
        prepared_result,
        **_result_values(prepared_result, attempts=tuple(attempts)),
    )
    with pytest.raises(ValueError, match="identity|canonical"):
        owner.validate_result(
            hostile_result,
            prepared_result.run_id,
            prepared_result.initialization_index,
        )


def test_attempt_scalars_are_typed_before_hostile_equality(prepared_result):
    attempt = prepared_result.attempts[0]
    bomb = _EqualityBomb()
    values = {name: getattr(attempt, name) for name in preparation._attempt_fields()}
    values["reserved_decision_raw64_word"] = bomb
    with pytest.raises(TypeError, match="integer"):
        preparation._preflight_attempt_values(values)
    assert bomb.calls == 0


@pytest.mark.parametrize(
    "target",
    (
        "control_address_schema",
        "initial_state_buffer_pos",
        "checkpoint26_result_digest",
        "checkpoint27_entry_role",
    ),
)
def test_nested_cp27_cp26_records_preflight_before_parent_validator(
    certified_bundle,
    prepared_result,
    target,
):
    owner = certified_bundle["owner"]
    entry = prepared_result.parent_protocol_result.entries[0]
    consumption = entry.parent_consumption
    if target == "control_address_schema":
        record = consumption.control_stream.address
        field = "schema_version"
    elif target == "initial_state_buffer_pos":
        record = consumption.control_stream.initial_state
        field = "buffer_pos"
    elif target == "checkpoint26_result_digest":
        record = prepared_result.parent_protocol_result.parent_control_result
        field = "result_sha256"
    else:
        record = entry
        field = "semantic_role"
    original = getattr(record, field)
    original_validator = owner._protocol_validate_result
    bomb = _EqualityBomb()
    calls = []

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls.append("parent validator")
        raise AssertionError("parent validation must not begin")

    object.__setattr__(record, field, bomb)
    object.__setattr__(owner, "_protocol_validate_result", forbidden)
    try:
        with pytest.raises(TypeError):
            owner.validate_result(
                prepared_result,
                prepared_result.run_id,
                prepared_result.initialization_index,
            )
    finally:
        object.__setattr__(record, field, original)
        object.__setattr__(owner, "_protocol_validate_result", original_validator)
    assert bomb.calls == 0
    assert calls == []


def test_oversized_nested_protocol_tuple_refuses_before_element_or_delegation(
    certified_bundle,
    prepared_result,
):
    owner = certified_bundle["owner"]
    state = prepared_result.parent_protocol_result.entries[
        0
    ].parent_consumption.control_stream.initial_state
    original = state.buffer
    original_validator = owner._protocol_validate_result
    bomb = _EqualityBomb()
    calls = []

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls.append("parent validator")
        raise AssertionError("parent validation must not begin")

    object.__setattr__(state, "buffer", (bomb,) * 5)
    object.__setattr__(owner, "_protocol_validate_result", forbidden)
    try:
        with pytest.raises(ValueError, match="buffer|length|tuple|bound"):
            owner.validate_result(
                prepared_result,
                prepared_result.run_id,
                prepared_result.initialization_index,
            )
    finally:
        object.__setattr__(state, "buffer", original)
        object.__setattr__(owner, "_protocol_validate_result", original_validator)
    assert bomb.calls == 0
    assert calls == []


def test_matching_helpers_bind_exact_parents_hypothesis_context_budget_and_role(
    certified_bundle,
):
    owner = certified_bundle["owner"]
    parent28 = certified_bundle["initializer_owner"]
    parent30 = certified_bundle["initial_tilt"]
    hypothesis = certified_bundle["word_family_hypothesis"]
    kwargs = {
        "residual_context": RESIDUAL_CONTEXT,
        "attempt_budget": 2,
        "preparation_policy": PREPARATION_POLICY,
        "preparation_role_sha256": PREPARATION_ROLE,
        "word_family_hypothesis": hypothesis,
    }
    matching = _MATCHING
    validator = _VALIDATE_CERTIFICATE
    assert matching(parent28, parent30, owner, **kwargs) is owner
    assert validator(parent28, parent30, owner, **kwargs) is owner.certificate
    with pytest.raises(ValueError, match="hypothesis"):
        matching(
            parent28,
            parent30,
            owner,
            **{
                **kwargs,
                "word_family_hypothesis": certified_bundle["alien_hypothesis"],
            },
        )
    with pytest.raises(ValueError, match="attempt budget"):
        matching(parent28, parent30, owner, **{**kwargs, "attempt_budget": 1})
    with pytest.raises(ValueError, match="role"):
        matching(
            parent28,
            parent30,
            owner,
            **{**kwargs, "preparation_role_sha256": "8" * 64},
        )


def test_records_and_owner_are_sealed_nonpickle_and_nonsubclassable(
    certified_bundle,
    prepared_result,
):
    records = (
        certified_bundle["word_family_hypothesis"],
        certified_bundle["owner"].certificate,
        prepared_result.attempts[0],
        prepared_result,
        certified_bundle["owner"],
    )
    for value in records:
        with pytest.raises(Exception):
            pickle.dumps(value)
    for sealed_type in (
        preparation.InitialTiltRejectionPreparationWordFamilyHypothesis,
        preparation.CounterKeyedInitialTiltRejectionPreparationCertificate,
        preparation.CounterKeyedInitialTiltRejectionAttempt,
        preparation.CounterKeyedInitialTiltRejectionPreparationResult,
        preparation.CounterKeyedInitialTiltRejectionPreparationOwner,
    ):
        with pytest.raises(TypeError):
            type("HostileSubclass", (sealed_type,), {})


def test_source_ast_has_no_hidden_decision_rng_or_cp28_initializer():
    source = inspect.getsource(preparation)
    tree = ast.parse(source)
    prepare_tree = ast.parse(
        textwrap.dedent(
            inspect.getsource(
                preparation.CounterKeyedInitialTiltRejectionPreparationOwner.prepare
            )
        )
    )
    direct_calls = [
        node.func.attr
        for node in ast.walk(prepare_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
    ]
    assert direct_calls.count("_protocol_allocate") == 1
    attributes = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    for forbidden in (
        "default_rng",
        "random_raw",
        "random",
        "uniform",
        "choice",
        "integers",
        "normal",
        "standard_normal",
        "randint",
        "randrange",
        "exp",
        "expm1",
        "bootstrap_lineage",
        "consume",
        "initialize",
    ):
        assert forbidden not in attributes


def test_module_is_not_reexported_from_dependency_light_process_package():
    import heterodiff.processes as processes

    for name in (
        "InitialTiltRejectionPreparationWordFamilyHypothesis",
        "CounterKeyedInitialTiltRejectionPreparationCertificate",
        "CounterKeyedInitialTiltRejectionAttempt",
        "CounterKeyedInitialTiltRejectionPreparationResult",
        "CounterKeyedInitialTiltRejectionPreparationOwner",
    ):
        assert name not in processes.__dict__


def test_optional_torch_boundary_translates_dependency_failure():
    source = Path(preparation.__file__).resolve()
    script = """
import builtins
import runpy

real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == "heterodiff.models" or name.startswith("torch"):
        error = ModuleNotFoundError("No module named 'torch'")
        error.name = "torch"
        raise error
    return real_import(name, *args, **kwargs)

builtins.__import__ = guarded
runpy.run_path(%r, run_name="hostile_optional_import")
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
    assert "counter-keyed rejection preparation requires the optional PyTorch" in (
        completed.stderr
    )
