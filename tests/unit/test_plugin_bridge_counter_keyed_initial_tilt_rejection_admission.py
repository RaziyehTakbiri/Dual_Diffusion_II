"""Hostile tests for checkpoint-40 fixed-batch initializer admission."""

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
from types import SimpleNamespace

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="finite-resolution initializer admission requires PyTorch"
)

admission = importlib.import_module(  # noqa: E402
    "heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "admission"
)
checkpoint39 = importlib.import_module(  # noqa: E402
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "lineage_tag3_coordination"
)


ADMISSION_POLICY = getattr(
    admission,
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_POLICY",
)
ADMISSION_ROLE = "6" * 64
MAX_UINT64 = (1 << 64) - 1
DYADIC_DENOMINATOR = 1 << 64
_CERTIFY = getattr(
    admission,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_admission",
)
_MATCHING = getattr(
    admission,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_" "admission",
)
_VALIDATE_CERTIFICATE = getattr(
    admission,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_admission_"
    "certificate",
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
    values[digest_name] = admission._SEMANTIC_DIGEST(payload(values))
    return _forged(record, **values)


def _profile_call(callback, *args):
    watched = {
        "coordinate": admission._CP39_COORDINATE.__code__,
        "validate_parent": admission._CP39_VALIDATE_RESULT.__code__,
        "make_target": admission._make_target.__code__,
        "make_result": admission._make_result.__code__,
    }
    calls = {name: 0 for name in watched}

    def profiler(frame, event, arg):
        del arg
        if event == "call":
            for name, code in watched.items():
                if frame.f_code is code:
                    calls[name] += 1
        return profiler

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        result = callback(*args)
    finally:
        sys.setprofile(previous)
    return result, calls


def _profile_failure(callback, *args):
    watched = {
        "coordinate": admission._CP39_COORDINATE.__code__,
        "validate_parent": admission._CP39_VALIDATE_RESULT.__code__,
        "make_target": admission._make_target.__code__,
        "make_result": admission._make_result.__code__,
    }
    calls = {name: 0 for name in watched}

    def profiler(frame, event, arg):
        del arg
        if event == "call":
            for name, code in watched.items():
                if frame.f_code is code:
                    calls[name] += 1
        return profiler

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        callback(*args)
    except Exception as error:
        return error, calls
    finally:
        sys.setprofile(previous)
    raise AssertionError("profiled callback unexpectedly succeeded")


def _synthetic_cp38_result(certificate, parent, specs):
    checkpoint37 = checkpoint39.checkpoint38.checkpoint37
    decision_result = checkpoint37._synthetic_case(parent, specs)
    law = admission._law._materialize_law(certificate, decision_result)
    return admission._law._make_result(
        certificate,
        decision_result,
        law=law,
    )


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


class _TargetTraversalBomb:
    def __init__(self):
        self.calls = 0

    @property
    def configuration_masses(self):
        self.calls += 1
        raise AssertionError("foreign target traversal must not execute")


@pytest.fixture(scope="module")
def branch_bundle():
    """Reuse CP39's fixed all-atomic selected-empty/exhaustion witnesses."""

    parent = checkpoint39.branch_bundle.__wrapped__()
    before = _rng_snapshot()
    owner = _CERTIFY(
        parent["owner"],
        admission_policy=ADMISSION_POLICY,
        admission_role_sha256=ADMISSION_ROLE,
    )
    selected, selected_calls = _profile_call(
        owner.admit,
        parent["empty_run"],
        0,
    )
    exhausted, exhausted_calls = _profile_call(
        owner.admit,
        parent["exhausted_run"],
        0,
    )
    _assert_rng_unchanged(before)
    return {
        **parent,
        "admission_owner": owner,
        "selected_admission": selected,
        "exhausted_admission": exhausted,
        "selected_calls": selected_calls,
        "exhausted_calls": exhausted_calls,
    }


def test_public_api_constants_signatures_and_exports_are_exact(branch_bundle):
    owner = branch_bundle["admission_owner"]
    owner_type = admission.CounterKeyedInitialTiltRejectionAdmissionOwner
    assert type(owner) is owner_type
    assert type(owner.certificate) is (
        admission.CounterKeyedInitialTiltRejectionAdmissionCertificate
    )
    assert owner.coordination_owner is branch_bundle["owner"]
    assert tuple(inspect.signature(owner.admit).parameters) == (
        "run_id",
        "initialization_index",
    )
    assert tuple(inspect.signature(owner.validate_result).parameters) == (
        "result",
        "run_id",
        "initialization_index",
    )
    for function in (_CERTIFY, _MATCHING, _VALIDATE_CERTIFICATE):
        parameters = inspect.signature(function).parameters
        assert parameters["admission_policy"].kind is inspect.Parameter.KEYWORD_ONLY
        assert (
            parameters["admission_role_sha256"].kind is inspect.Parameter.KEYWORD_ONLY
        )
    assert admission.INITIAL_TILT_REJECTION_FINITE_RESOLUTION_DYADIC_DENOMINATOR == (
        DYADIC_DENOMINATOR
    )
    assert admission.INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_ATTEMPTS == 64
    assert (
        admission.INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TARGET_CONFIGURATIONS
        == 64
    )
    assert admission.INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_STREAM_RECORDS == 64
    assert (
        admission.INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TOTAL_RAW64_WORDS
        == 65_536
    )
    assert admission.INITIAL_TILT_REJECTION_FINITE_RESOLUTION_ADMISSION_STATUSES == (
        "admitted",
        "exhausted",
    )
    assert len(admission.__all__) == len(set(admission.__all__))
    assert all(hasattr(admission, name) for name in admission.__all__)


@pytest.mark.parametrize(
    "selection_numerator,selection_denominator,attempts,raw,clipped,nonvacuous",
    (
        (0, 1, 64, None, None, False),
        (
            1,
            2,
            1,
            Fraction(4, DYADIC_DENOMINATOR),
            Fraction(4, DYADIC_DENOMINATOR),
            True,
        ),
        (2, DYADIC_DENOMINATOR, 1, Fraction(1), Fraction(1), False),
        (1, DYADIC_DENOMINATOR, 1, Fraction(2), Fraction(1), False),
        (1, DYADIC_DENOMINATOR, 64, Fraction(128), Fraction(1), False),
        (
            1,
            1,
            64,
            Fraction(128, DYADIC_DENOMINATOR),
            Fraction(128, DYADIC_DENOMINATOR),
            True,
        ),
    ),
)
def test_pure_conditioned_comparison_covers_zero_clipping_and_nonstrict_boundary(
    selection_numerator,
    selection_denominator,
    attempts,
    raw,
    clipped,
    nonvacuous,
):
    parent = SimpleNamespace(
        fixed_batch_selection_probability_numerator=selection_numerator,
        fixed_batch_selection_probability_denominator=selection_denominator,
        attempt_budget=attempts,
    )
    assert admission._conditioned_comparison(parent) == (
        raw,
        clipped,
        nonvacuous,
    )


def test_pure_fixed_batch_partition_and_duplicate_ordinals_are_exact():
    law = admission._law
    quotas = (0, DYADIC_DENOMINATOR // 2, DYADIC_DENOMINATOR)
    survival, first, exhaustion, selection = law._first_success_partition(quotas)
    assert survival == (Fraction(1), Fraction(1), Fraction(1, 2))
    assert first == (Fraction(0), Fraction(1, 2), Fraction(1, 2))
    assert exhaustion == 0
    assert selection == 1
    keys = (("x",), ("y",), ("x",), ("x",))
    representatives, contributors, mapping = law._stable_configuration_key_partition(
        keys
    )
    assert representatives == (0, 1)
    assert contributors == ((0, 2, 3), (1,))
    assert mapping == (0, 1, 0, 0)


def test_certificate_binds_exact_cp39_cp38_target_and_conservative_claims(
    branch_bundle,
):
    owner = branch_bundle["admission_owner"]
    certificate = owner.certificate
    parent39 = owner.coordination_owner.certificate
    parent38_owner = owner.coordination_owner.finite_batch_law_owner
    assert certificate.checkpoint39_certificate is parent39
    assert certificate.checkpoint38_certificate is parent38_owner.certificate
    assert parent39.checkpoint38_certificate is parent38_owner.certificate
    assert certificate.checkpoint39_owner_runtime_identity == id(
        owner.coordination_owner
    )
    assert certificate.target_family == (
        admission.INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_FAMILY
    )
    assert certificate.target_conditioning == (
        admission.INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_CONDITIONING
    )
    assert certificate.conditioned_comparison == (
        admission.INITIAL_TILT_REJECTION_FINITE_RESOLUTION_CONDITIONED_COMPARISON
    )
    for name in admission._CERTIFICATE_POSITIVE_FLAGS:
        assert getattr(certificate, name) is True
    for name in admission._CERTIFICATE_NEGATIVE_FLAGS:
        assert getattr(certificate, name) is False
    assert (
        _VALIDATE_CERTIFICATE(
            owner.coordination_owner,
            owner,
            admission_policy=ADMISSION_POLICY,
            admission_role_sha256=ADMISSION_ROLE,
        )
        is certificate
    )


@pytest.mark.parametrize("key", ("selected_admission", "exhausted_admission"))
def test_materialized_target_is_exact_normalized_fixed_batch_projection(
    branch_bundle,
    key,
):
    result = branch_bundle[key]
    target = result.finite_resolution_target
    parent39 = result.parent_coordination_result
    parent38 = parent39.parent_finite_batch_law_result
    assert target.parent_finite_batch_law_result is parent38
    assert target.configuration_masses is parent38.configuration_masses
    assert target.configuration_mass_sha256s is parent38.configuration_mass_sha256s
    assert target.conditioning_projection_sha256 == (
        parent38.conditioning_projection_sha256
    )
    assert result.finite_resolution_target_law_sha256 == (
        target.word_free_target_law_sha256
    )
    assert target.word_free_target_law_sha256 == admission._SEMANTIC_DIGEST(
        admission._word_free_target_law_payload(
            {name: getattr(target, name) for name in admission._target_fields()}
        )
    )
    assert target.target_sha256 != target.word_free_target_law_sha256
    exhaustion = Fraction(
        target.exhaustion_probability_numerator,
        target.exhaustion_probability_denominator,
    )
    selection = Fraction(
        target.selection_probability_numerator,
        target.selection_probability_denominator,
    )
    assert exhaustion + selection == 1
    assert (
        Fraction(
            target.augmented_normalization_numerator,
            target.augmented_normalization_denominator,
        )
        == 1
    )
    assert (
        sum(
            (
                Fraction(
                    row.fixed_batch_selection_probability_numerator,
                    row.fixed_batch_selection_probability_denominator,
                )
                for row in target.configuration_masses
            ),
            Fraction(0),
        )
        == selection
    )
    assert target.selected_conditioned_state_law_defined is (selection > 0)
    if selection > 0:
        assert (
            sum(
                (
                    Fraction(
                        row.selected_conditioned_probability_numerator,
                        row.selected_conditioned_probability_denominator,
                    )
                    for row in target.configuration_masses
                ),
                Fraction(0),
            )
            == 1
        )
        raw = Fraction(2 * target.attempt_budget, DYADIC_DENOMINATOR) / selection
        assert (
            Fraction(
                target.conditioned_ideal_dyadic_raw_strict_upper_numerator,
                target.conditioned_ideal_dyadic_raw_strict_upper_denominator,
            )
            == raw
        )
        assert Fraction(
            target.conditioned_ideal_dyadic_clipped_upper_numerator,
            target.conditioned_ideal_dyadic_clipped_upper_denominator,
        ) == min(Fraction(1), raw)
        assert target.conditioned_ideal_dyadic_clipped_nonstrict_bound_nonvacuous is (
            raw < 1
        )
    for name in (
        "abstract_words_iid_uniform_uint64",
        "abstract_words_independent_of_word_free_batch",
        "ideal_dyadic_comparison_uses_separate_independent_coordinate_sequences",
        "ideal_dyadic_comparison_uses_common_continuous_uniform_coupling",
        "conservative_dyadic_acceptance_probabilities_not_above_ideal",
        "ideal_selection_mass_at_least_dyadic_selection_mass",
        "conditioning_stability_factor_two_applied",
        "target_is_conditional_on_fixed_successful_batch",
        "target_includes_exhaustion_atom",
        "duplicate_configuration_aggregation_exact",
        "selected_conditioned_target_normalized_when_defined",
        "abstract_iid_decision_word_premise_only",
        "word_free_target_law_digest_excludes_record_custody",
        "target_sha256_is_record_custody_digest",
    ):
        assert getattr(target, name) is True
    for name in (
        "target_is_live_output_law",
        "target_integrates_checkpoint36_batch_law",
        "target_is_exact_ideal_rejection_law",
        "target_is_normalized_global_tilted_law",
        "target_sha256_is_word_free_target_law_digest",
    ):
        assert getattr(target, name) is False


def test_zero_selection_materializes_a_total_augmented_target_without_conditioning(
    branch_bundle,
):
    certificate = branch_bundle["admission_owner"].certificate
    base_parent = branch_bundle[
        "selected_admission"
    ].parent_coordination_result.parent_finite_batch_law_result.parent_decision_result
    zero_result = _synthetic_cp38_result(
        certificate.checkpoint38_certificate,
        base_parent,
        ((Fraction(-64), 0),),
    )
    assert zero_result.outcome == "exhausted"
    assert zero_result.fixed_batch_selection_probability_numerator == 0
    target = admission._make_target(certificate, zero_result)
    assert target.parent_finite_batch_law_result is zero_result
    assert (
        Fraction(
            target.augmented_normalization_numerator,
            target.augmented_normalization_denominator,
        )
        == 1
    )
    assert (
        Fraction(
            target.exhaustion_probability_numerator,
            target.exhaustion_probability_denominator,
        )
        == 1
    )
    assert (
        Fraction(
            target.selection_probability_numerator,
            target.selection_probability_denominator,
        )
        == 0
    )
    assert target.selected_conditioned_state_law_defined is False
    assert target.conditioned_ideal_dyadic_raw_strict_upper_defined is False
    assert target.conditioned_ideal_dyadic_clipped_upper_defined is False
    for name in (
        "conditioned_ideal_dyadic_raw_strict_upper_numerator",
        "conditioned_ideal_dyadic_raw_strict_upper_denominator",
        "conditioned_ideal_dyadic_clipped_upper_numerator",
        "conditioned_ideal_dyadic_clipped_upper_denominator",
    ):
        assert getattr(target, name) is None
    for name in (
        "conditioned_ideal_dyadic_raw_upper_is_strict",
        "conditioned_ideal_dyadic_clipped_upper_is_non_strict",
        "conditioned_ideal_dyadic_clipped_nonstrict_bound_nonvacuous",
    ):
        assert getattr(target, name) is False
    assert all(
        row.fixed_batch_selection_probability_numerator == 0
        and row.selected_conditioned_probability_defined is False
        and row.selected_conditioned_probability_numerator is None
        and row.selected_conditioned_probability_denominator is None
        for row in target.configuration_masses
    )
    target_values = {name: getattr(target, name) for name in admission._target_fields()}
    assert target.word_free_target_law_sha256 == admission._SEMANTIC_DIGEST(
        admission._word_free_target_law_payload(target_values)
    )
    assert admission._validate_target(target, certificate=certificate) is target


def test_word_free_target_digest_is_invariant_to_same_batch_decision_trace(
    branch_bundle,
):
    certificate = branch_bundle["admission_owner"].certificate
    law_certificate = certificate.checkpoint38_certificate
    base_parent = branch_bundle[
        "selected_admission"
    ].parent_coordination_result.parent_finite_batch_law_result.parent_decision_result
    checkpoint37 = checkpoint39.checkpoint38.checkpoint37
    quota = checkpoint37.decision._floor_exp_uint64_quota(Fraction(-1)).quota
    assert 0 < quota < DYADIC_DENOMINATOR
    selected = _synthetic_cp38_result(
        law_certificate,
        base_parent,
        ((Fraction(-1), 0),),
    )
    exhausted = _synthetic_cp38_result(
        law_certificate,
        base_parent,
        ((Fraction(-1), quota),),
    )
    assert selected.outcome == "selected"
    assert exhausted.outcome == "exhausted"
    assert selected.parent_decision_result.result_sha256 != (
        exhausted.parent_decision_result.result_sha256
    )
    assert selected.conditioning_projection_sha256 == (
        exhausted.conditioning_projection_sha256
    )
    selected_target = admission._make_target(certificate, selected)
    exhausted_target = admission._make_target(certificate, exhausted)
    assert admission._configuration_law_projection(
        selected_target.configuration_masses
    ) == admission._configuration_law_projection(exhausted_target.configuration_masses)
    assert selected_target.word_free_target_law_sha256 == (
        exhausted_target.word_free_target_law_sha256
    )
    assert selected_target.target_sha256 != exhausted_target.target_sha256


def test_selected_empty_is_present_admitted_and_preserves_exact_parent_identities(
    branch_bundle,
):
    result = branch_bundle["selected_admission"]
    parent = result.parent_coordination_result
    law_parent = parent.parent_finite_batch_law_result
    assert result.admission_status == "admitted"
    assert result.source_outcome == "selected"
    assert result.initial_configuration is parent.selected_configuration
    assert result.initial_configuration == ()
    assert result.initial_intensity is parent.initial_intensity
    assert result.lineage_state is parent.lineage_state
    assert result.occurrence_payloads is parent.occurrence_payloads == ()
    assert result.occurrence_payload_sha256s is (parent.occurrence_payload_sha256s)
    assert result.tag3_raw64_word_counts is parent.tag3_raw64_word_counts == ()
    assert result.qualified_lineage_coordinates is (
        parent.qualified_lineage_coordinates
    )
    assert result.target_configuration_ordinal == (
        law_parent.selected_configuration_ordinal
    )
    row = result.finite_resolution_target.configuration_masses[
        result.target_configuration_ordinal
    ]
    assert result.target_configuration_mass is row
    assert result.target_configuration_mass_sha256 == row.mass_sha256
    assert result.state_present is True
    assert result.downstream_initial_state_structurally_admitted is True
    assert result.structurally_admissible_under_declared_fixed_batch_target is True
    assert result.selected_empty_state_admitted is True
    assert result.exhausted_valid_no_state is False
    assert result.aggregate_representative_not_substituted_for_selected_state is True
    assert result.parent_coordinate_call_count == 1
    for name in admission._RESULT_ALWAYS_FALSE_FLAGS:
        assert getattr(result, name) is False


def test_exhaustion_retains_target_but_returns_exact_no_state(branch_bundle):
    result = branch_bundle["exhausted_admission"]
    assert result.admission_status == "exhausted"
    assert result.source_outcome == "exhausted"
    assert result.finite_resolution_target is not None
    assert result.finite_resolution_target.target_includes_exhaustion_atom is True
    for name in (
        "source_selected_attempt_index",
        "initial_configuration",
        "initial_configuration_sha256",
        "initial_intensity",
        "initial_intensity_sha256",
        "lineage_state",
        "lineage_state_sha256",
        "occurrence_payloads",
        "occurrence_payload_sha256s",
        "tag3_raw64_word_counts",
        "qualified_lineage_coordinates",
        "target_configuration_ordinal",
        "target_configuration_mass",
        "target_configuration_mass_sha256",
        "target_aggregate_mass_numerator",
        "target_aggregate_mass_denominator",
        "target_conditioned_mass_numerator",
        "target_conditioned_mass_denominator",
    ):
        assert getattr(result, name) is None
    assert result.state_present is False
    assert result.downstream_initial_state_structurally_admitted is False
    assert result.structurally_admissible_under_declared_fixed_batch_target is False
    assert result.selected_empty_state_admitted is False
    assert result.exhausted_valid_no_state is True
    assert result.operational_failure_returned_as_exhaustion is False
    assert result.parent_coordinate_call_count == 1


def test_live_admit_invokes_one_parent_coordinate_and_one_child_construction(
    branch_bundle,
):
    expected = {
        "coordinate": 1,
        "validate_parent": 1,
        "make_target": 1,
        "make_result": 1,
    }
    assert branch_bundle["selected_calls"] == expected
    assert branch_bundle["exhausted_calls"] == expected


def test_validation_never_coordinates_or_constructs_children_and_preserves_rng(
    branch_bundle,
):
    owner = branch_bundle["admission_owner"]
    result = branch_bundle["selected_admission"]
    before = _rng_snapshot()
    checked, calls = _profile_call(
        owner.validate_result,
        result,
        branch_bundle["empty_run"],
        0,
    )
    _assert_rng_unchanged(before)
    assert checked is result
    assert calls == {
        "coordinate": 0,
        "validate_parent": 1,
        "make_target": 0,
        "make_result": 0,
    }


@pytest.mark.parametrize(
    "position,bad",
    ((0, True), (0, -1), (0, 1 << 64), (1, False), (1, -1), (1, 1 << 64)),
)
def test_coordinate_preflight_refuses_exact_integer_hostility_before_parent(
    branch_bundle,
    position,
    bad,
):
    owner = branch_bundle["admission_owner"]
    coordinates = [branch_bundle["empty_run"], 0]
    coordinates[position] = bad
    expected = TypeError if type(bad) is bool else ValueError
    error, calls = _profile_failure(owner.admit, *coordinates)
    assert type(error) is expected
    assert calls == {
        "coordinate": 0,
        "validate_parent": 0,
        "make_target": 0,
        "make_result": 0,
    }


def test_validation_preflights_mutated_request_scalars_before_equality(
    branch_bundle,
):
    owner = branch_bundle["admission_owner"]
    result = branch_bundle["selected_admission"]
    for name in ("run_id", "initialization_index"):
        bomb = _EqualityBomb()
        forged = _forged(result, **{name: bomb})
        with pytest.raises(TypeError, match="exact Python integer"):
            owner.validate_result(
                forged,
                branch_bundle["empty_run"],
                0,
            )
        assert bomb.calls == 0


def test_result_preflight_rejects_foreign_target_before_nested_traversal(
    branch_bundle,
):
    result = branch_bundle["selected_admission"]
    bomb = _TargetTraversalBomb()
    forged = _forged(result, finite_resolution_target=bomb)
    with pytest.raises(TypeError, match="wrong exact CP40 target type"):
        admission._preflight_result_record(
            forged,
            certificate=result.certificate,
        )
    assert bomb.calls == 0


def test_selected_empty_and_exhaustion_status_splices_are_refused(branch_bundle):
    selected = branch_bundle["selected_admission"]
    exhausted = branch_bundle["exhausted_admission"]
    status_splice = _redigested(
        selected,
        admission._result_fields,
        admission._result_payload,
        "result_sha256",
        admission_status="exhausted",
    )
    with pytest.raises(ValueError, match="status differs"):
        admission._validate_result_values(
            {name: getattr(status_splice, name) for name in admission._result_fields()},
            trusted_certificate=selected.certificate,
        )
    parent_splice = _redigested(
        selected,
        admission._result_fields,
        admission._result_payload,
        "result_sha256",
        parent_coordination_result=exhausted.parent_coordination_result,
        parent_coordination_result_sha256=(exhausted.parent_coordination_result_sha256),
    )
    with pytest.raises(ValueError, match="target and CP39 parent"):
        admission._validate_result_values(
            {name: getattr(parent_splice, name) for name in admission._result_fields()},
            trusted_certificate=selected.certificate,
        )


def test_target_probability_and_identity_splices_fail_closed(
    branch_bundle,
):
    result = branch_bundle["selected_admission"]
    target = result.finite_resolution_target
    copied_masses = tuple([*target.configuration_masses])
    assert copied_masses == target.configuration_masses
    assert copied_masses is not target.configuration_masses
    identity_splice = _forged(target, configuration_masses=copied_masses)
    with pytest.raises(ValueError, match="lost parent identity"):
        admission._validate_target(identity_splice, certificate=result.certificate)
    probability_splice = _redigested(
        target,
        admission._target_fields,
        admission._target_payload,
        "target_sha256",
        selection_probability_numerator=0,
        selection_probability_denominator=1,
    )
    with pytest.raises(ValueError, match="partition differs"):
        admission._validate_target(probability_splice, certificate=result.certificate)


@pytest.mark.parametrize(
    "field",
    (
        "target.configuration_masses",
        "target.configuration_mass_sha256s",
        "occurrence_payloads",
        "occurrence_payload_sha256s",
        "tag3_raw64_word_counts",
        "qualified_lineage_coordinates",
    ),
)
def test_all_cp40_owned_outer_tuples_refuse_before_parent_validation(
    branch_bundle,
    field,
):
    owner = branch_bundle["admission_owner"]
    result = branch_bundle["selected_admission"]
    if field.startswith("target."):
        target = result.finite_resolution_target
        target_field = field.removeprefix("target.")
        oversized = (getattr(target, target_field)[0],) * 65
        forged_target = _forged(
            target,
            **{target_field: oversized},
        )
        forged = _forged(result, finite_resolution_target=forged_target)
    else:
        forged = _forged(result, **{field: (object(),) * 65})
    error, calls = _profile_failure(
        owner.validate_result,
        forged,
        branch_bundle["empty_run"],
        0,
    )
    assert type(error) is ValueError
    assert "resource bound" in str(error)
    assert calls == {
        "coordinate": 0,
        "validate_parent": 0,
        "make_target": 0,
        "make_result": 0,
    }


def test_redigested_positive_and_negative_claim_forgeries_are_refused(
    branch_bundle,
):
    result = branch_bundle["selected_admission"]
    target = result.finite_resolution_target
    certificate = result.certificate
    target_forgery = _redigested(
        target,
        admission._target_fields,
        admission._target_payload,
        "target_sha256",
        target_is_live_output_law=True,
    )
    with pytest.raises(ValueError, match="must remain False"):
        admission._validate_target(target_forgery, certificate=certificate)
    law_digest_forgery = _redigested(
        target,
        admission._target_fields,
        admission._target_payload,
        "target_sha256",
        word_free_target_law_sha256="7" * 64,
    )
    with pytest.raises(ValueError, match="word-free.*digest differs"):
        admission._validate_target(law_digest_forgery, certificate=certificate)
    result_forgery = _redigested(
        result,
        admission._result_fields,
        admission._result_payload,
        "result_sha256",
        formal_test28_closed=True,
    )
    with pytest.raises(ValueError, match="must remain False"):
        admission._validate_result_values(
            {
                name: getattr(result_forgery, name)
                for name in admission._result_fields()
            },
            trusted_certificate=certificate,
        )
    result_law_digest_forgery = _redigested(
        result,
        admission._result_fields,
        admission._result_payload,
        "result_sha256",
        finite_resolution_target_law_sha256="8" * 64,
    )
    with pytest.raises(ValueError, match="word-free target-law digest differs"):
        admission._validate_result_values(
            {
                name: getattr(result_law_digest_forgery, name)
                for name in admission._result_fields()
            },
            trusted_certificate=certificate,
        )
    certificate_values = {
        name: getattr(certificate, name) for name in admission._certificate_fields()
    }
    certificate_values["scientific_claim_promoted"] = True
    certificate_values["certificate_sha256"] = "0" * 64
    certificate_values["certificate_sha256"] = admission._SEMANTIC_DIGEST(
        admission._certificate_payload(certificate_values)
    )
    certificate_forgery = _forged(certificate, **certificate_values)
    with pytest.raises(ValueError, match="must remain False"):
        admission._validate_certificate(certificate_forgery)


def test_same_digest_alien_certificate_and_target_are_not_interchangeable(
    branch_bundle,
):
    result = branch_bundle["selected_admission"]
    certificate = result.certificate
    alien_certificate = _forged(certificate)
    assert alien_certificate.certificate_sha256 == certificate.certificate_sha256
    alien_target = _forged(
        result.finite_resolution_target,
        certificate=alien_certificate,
    )
    assert alien_target.target_sha256 == result.finite_resolution_target_sha256
    with pytest.raises(ValueError, match="trusted certificate identity"):
        admission._validate_target(alien_target, certificate=certificate)
    foreign_target_result = _forged(
        result,
        finite_resolution_target=alien_target,
    )
    with pytest.raises(ValueError, match="target trusted certificate identity"):
        admission._validate_result_values(
            {
                name: getattr(foreign_target_result, name)
                for name in admission._result_fields()
            },
            trusted_certificate=certificate,
        )


def test_matching_helpers_require_exact_parent_policy_role_and_owner(
    branch_bundle,
):
    owner = branch_bundle["admission_owner"]
    parent = branch_bundle["owner"]
    assert (
        _MATCHING(
            parent,
            owner,
            admission_policy=ADMISSION_POLICY,
            admission_role_sha256=ADMISSION_ROLE,
        )
        is owner
    )
    with pytest.raises(ValueError, match="policy"):
        _MATCHING(
            parent,
            owner,
            admission_policy=ADMISSION_POLICY + "x",
            admission_role_sha256=ADMISSION_ROLE,
        )
    with pytest.raises(ValueError, match="role"):
        _MATCHING(
            parent,
            owner,
            admission_policy=ADMISSION_POLICY,
            admission_role_sha256="7" * 64,
        )
    with pytest.raises(TypeError, match="CP39"):
        _CERTIFY(
            parent.finite_batch_law_owner,
            admission_policy=ADMISSION_POLICY,
            admission_role_sha256=ADMISSION_ROLE,
        )


def test_cached_callback_and_parent_surface_substitution_fail_before_coordinate(
    branch_bundle,
):
    owner = branch_bundle["admission_owner"]
    calls = {"coordinate": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["coordinate"] += 1
        raise AssertionError("substituted coordinate must not execute")

    forged_owner = _forge_owner(owner, _parent_coordinate=forbidden)
    with pytest.raises(ValueError, match="cached callback changed"):
        forged_owner.admit(branch_bundle["empty_run"], 0)
    assert calls == {"coordinate": 0}

    original = admission._CP39_OWNER_TYPE.coordinate
    admission._CP39_OWNER_TYPE.coordinate = forbidden
    try:
        with pytest.raises(ValueError, match="dependency surface changed"):
            owner.admit(branch_bundle["empty_run"], 0)
    finally:
        admission._CP39_OWNER_TYPE.coordinate = original
    assert calls == {"coordinate": 0}


@pytest.mark.parametrize(
    "symbol",
    (
        "CounterKeyedInitialTiltRejectionAdmissionCertificate",
        "CounterKeyedInitialTiltRejectionFiniteResolutionTarget",
        "CounterKeyedInitializerAdmissionResult",
        "_SEMANTIC_DIGEST",
    ),
)
def test_hostile_cp40_surface_substitution_fails_before_every_operation(
    branch_bundle,
    symbol,
):
    owner = branch_bundle["admission_owner"]
    original = getattr(admission, symbol)
    side_effects = {"wrapper": 0}

    def hostile_wrapper(*args, **kwargs):
        del args, kwargs
        side_effects["wrapper"] += 1
        raise AssertionError("hostile substituted surface must not execute")

    setattr(admission, symbol, hostile_wrapper)
    try:
        error, calls = _profile_failure(
            owner.admit,
            branch_bundle["empty_run"],
            0,
        )
    finally:
        setattr(admission, symbol, original)
    assert getattr(admission, symbol) is original
    assert type(error) is ValueError
    assert "surface %s changed" % symbol in str(error)
    assert side_effects == {"wrapper": 0}
    assert calls == {
        "coordinate": 0,
        "validate_parent": 0,
        "make_target": 0,
        "make_result": 0,
    }


def test_records_and_owner_are_immutable_sealed_and_nonpickle(branch_bundle):
    owner = branch_bundle["admission_owner"]
    result = branch_bundle["selected_admission"]
    records = (owner.certificate, result.finite_resolution_target, result)
    for record in records:
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, "schema_version", "forged")
        with pytest.raises(TypeError):
            pickle.dumps(record)
    with pytest.raises(AttributeError):
        owner._certificate = owner.certificate
    with pytest.raises(AttributeError):
        del owner._certificate
    with pytest.raises(TypeError):
        pickle.dumps(owner)
    for cls in (
        admission.CounterKeyedInitialTiltRejectionAdmissionCertificate,
        admission.CounterKeyedInitialTiltRejectionFiniteResolutionTarget,
        admission.CounterKeyedInitializerAdmissionResult,
    ):
        with pytest.raises(TypeError):
            cls(_construction_token=object())

        with pytest.raises(TypeError):

            class ForbiddenSubclass(cls):
                pass

    with pytest.raises(TypeError):

        class ForbiddenOwnerSubclass(
            admission.CounterKeyedInitialTiltRejectionAdmissionOwner
        ):
            pass


def test_source_ast_has_one_parent_coordinate_no_cp34_retry_fallback_or_rng():
    source_path = Path(admission.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    assert "random" not in {name.split(".")[0] for name in imported_modules}
    assert "numpy" not in {name.split(".")[0] for name in imported_modules}
    assert not any("initial_tilt_atomic_admission" in name for name in imported_modules)
    owner_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CounterKeyedInitialTiltRejectionAdmissionOwner"
    )
    admit_method = next(
        node
        for node in owner_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "admit"
    )
    validate_method = next(
        node
        for node in owner_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "validate_result"
    )

    def attribute_calls(node):
        return [
            child.func.attr
            for child in ast.walk(node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
        ]

    admit_calls = attribute_calls(admit_method)
    validate_calls = attribute_calls(validate_method)
    assert admit_calls.count("_parent_coordinate") == 1
    assert admit_calls.count("_target_builder") == 1
    assert admit_calls.count("_result_builder") == 1
    assert "_parent_coordinate" not in validate_calls
    assert "_target_builder" not in validate_calls
    assert "_result_builder" not in validate_calls
    assert not any(
        isinstance(node, (ast.For, ast.While)) for node in ast.walk(admit_method)
    )
    assert not any(isinstance(node, ast.Try) for node in ast.walk(admit_method))
    assert "default_rng" not in source
    assert ".initialize(" not in source
    assert ".consume(" not in source
    assert "fallback_owner" not in source


def test_module_is_not_reexported_from_dependency_light_process_package():
    import heterodiff.processes as processes

    assert not hasattr(
        processes,
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_admission",
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
                "rejection_admission"
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
