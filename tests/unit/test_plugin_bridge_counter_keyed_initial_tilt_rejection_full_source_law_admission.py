"""Hostile tests for checkpoint-49 full-source law admission."""

import ast
from contextlib import contextmanager
from fractions import Fraction
import importlib
import inspect
from itertools import product
from pathlib import Path
import pickle
import random
import sys
from types import SimpleNamespace

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="full-source law admission requires the reference dependency"
)

from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission as admission,
)


POLICY = getattr(
    admission,
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_"
    "ADMISSION_POLICY",
)
DECLARE = getattr(
    admission,
    "declare_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_"
    "law_assumption",
)
VALIDATE_DECLARATION = getattr(
    admission,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_"
    "law_assumption_declaration",
)
CERTIFY = getattr(
    admission,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_"
    "law_admission",
)
MATCHING = getattr(
    admission,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_full_"
    "source_law_admission",
)
VALIDATE_CERTIFICATE = getattr(
    admission,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_"
    "law_admission_certificate",
)

DECLARATION_TYPE = getattr(
    admission,
    "CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration",
)
CERTIFICATE_TYPE = getattr(
    admission,
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate",
)
DESCRIPTION_TYPE = getattr(
    admission,
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionDescription",
)
RESULT_TYPE = getattr(
    admission,
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionResult",
)
OWNER_TYPE = getattr(
    admission,
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionOwner",
)
ERROR_TYPE = getattr(
    admission,
    "PluginBridgeCounterKeyedInitialTiltRejectionFullSourceLawAdmissionError",
)

ASSUMPTION_ROLE_SHA256 = "a" * 64
ADMISSION_ROLE_SHA256 = "b" * 64


class _IntSubclass(int):
    pass


class _TouchBomb:
    def __init__(self):
        self.calls = 0

    def _touched(self, operation):
        self.calls += 1
        raise AssertionError("hostile object was touched by " + operation)

    def __bool__(self):
        return self._touched("truth conversion")

    def __eq__(self, other):
        del other
        return self._touched("equality")

    def __hash__(self):
        return self._touched("hashing")

    def __int__(self):
        return self._touched("integer conversion")

    def __index__(self):
        return self._touched("index conversion")

    def __iter__(self):
        return self._touched("iteration")

    def __len__(self):
        return self._touched("length")


def _uniform(domain):
    domain = tuple(domain)
    return {value: Fraction(1, len(domain)) for value in domain}


def _total_variation(left, right, domain):
    domain = tuple(domain)
    assert sum(left.values()) == 1
    assert sum(right.values()) == 1
    return Fraction(1, 2) * sum(
        abs(left.get(value, Fraction(0)) - right.get(value, Fraction(0)))
        for value in domain
    )


def _pushforward(law, mapping):
    result = {}
    for value, probability in law.items():
        image = mapping[value]
        result[image] = result.get(image, Fraction(0)) + probability
    return result


def _conditional_law(base_law, success_weights):
    success_mass = sum(
        probability * success_weights[value] for value, probability in base_law.items()
    )
    if success_mass == 0:
        return None
    return {
        value: probability * success_weights[value] / success_mass
        for value, probability in base_law.items()
        if success_weights[value] != 0
    }


def _forged(record, **updates):
    forged = object.__new__(type(record))
    for name in type(record).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(record, name)))
    return forged


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


def _owner_operation_codes(checkpoint48, evidence):
    execution = checkpoint48.execution
    closure = execution._adapter._closure
    closure_owner = closure.CounterKeyedInitialTiltRejectionFactorizationClosureOwner
    factorization_owner = closure._CP42_OWNER_TYPE
    codes = {
        "external_backend": evidence["external_byte_source"].__code__,
        "cp48_execute": type(evidence["external_owner"]).execute.__code__,
        "cp48_acquire": execution._acquire_exact_byte_block.__code__,
        "cp47_execute": execution._CP47_OWNER_TYPE.execute.__code__,
        "cp43_split": closure_owner.split_full_words.__code__,
        "cp43_join": closure_owner.join_full_words.__code__,
        "cp43_evaluate_predecision": closure_owner.evaluate_predecision.__code__,
        "cp43_apply_decision_words": closure_owner.apply_decision_words.__code__,
        "cp43_evaluate_and_apply": closure_owner.evaluate_and_apply.__code__,
        "cp43_evaluate_operation": closure_owner._evaluate_operation.__code__,
        "cp43_apply_trusted": closure_owner._apply_trusted.__code__,
        "cp42_evaluate_predecision": (
            factorization_owner.evaluate_predecision.__code__
        ),
        "cp42_validate_predecision_result": (
            factorization_owner.validate_predecision_result.__code__
        ),
        "cp42_evaluate_predecision_operation": (
            factorization_owner._evaluate_predecision_operation.__code__
        ),
        "cp42_apply_decision_words": (
            factorization_owner.apply_decision_words.__code__
        ),
        "cp42_validate_applied_decision": (
            factorization_owner.validate_applied_decision.__code__
        ),
        "cp42_applied_semantic_builder": (
            closure._factorization._make_applied_decision.__code__
        ),
        "cp42_witness_successful_parity": (
            factorization_owner.witness_successful_parity.__code__
        ),
        "cp42_validate_successful_parity_witness": (
            factorization_owner.validate_successful_parity_witness.__code__
        ),
        "cp37_decide": closure._CP37_OWNER_TYPE.decide.__code__,
        "cp36_prepare": closure._factorization._CP36_OWNER_TYPE.prepare.__code__,
        "cp48_validate_result": (
            type(evidence["external_owner"]).validate_result.__code__
        ),
        "cp48_live_revalidate": (
            type(evidence["external_owner"]).revalidate_live_ancestry.__code__
        ),
    }
    if "selected_byte_source" in evidence:
        codes["selected_external_backend"] = evidence["selected_byte_source"].__code__
    return codes


_NONSTRUCTURAL_OPERATION_NAMES = frozenset(
    {
        "external_backend",
        "cp48_execute",
        "cp48_acquire",
        "cp47_execute",
        "cp43_split",
        "cp43_join",
        "cp43_evaluate_predecision",
        "cp43_apply_decision_words",
        "cp43_evaluate_and_apply",
        "cp43_evaluate_operation",
        "cp43_apply_trusted",
        "cp42_evaluate_predecision",
        "cp42_validate_predecision_result",
        "cp42_evaluate_predecision_operation",
        "cp42_apply_decision_words",
        "cp42_validate_applied_decision",
        "cp42_applied_semantic_builder",
        "cp42_witness_successful_parity",
        "cp42_validate_successful_parity_witness",
        "cp37_decide",
        "cp36_prepare",
        "selected_external_backend",
        "cp48_live_revalidate",
    }
)


@contextmanager
def _observe_owner_operations(
    checkpoint48,
    evidence,
    *,
    forbidden=_NONSTRUCTURAL_OPERATION_NAMES,
):
    codes = _owner_operation_codes(checkpoint48, evidence)
    calls = {name: 0 for name in codes}
    forbidden = frozenset(forbidden)

    def profiler(frame, event, arg):
        del arg
        if event == "call":
            for name, code in codes.items():
                if frame.f_code is code:
                    calls[name] += 1
                    if name in forbidden:
                        raise AssertionError(
                            "CP49 crossed forbidden operational boundary: " + name
                        )
        return profiler

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        yield calls
    finally:
        sys.setprofile(previous)


def _redigest_record(record, payload_builder, digest_field, **updates):
    forged = _forged(record, **updates)
    values = {name: getattr(forged, name) for name in type(forged).__annotations__}
    return _forged(
        forged,
        **{digest_field: admission._semantic_digest(payload_builder(values))},
    )


def _declaration_arguments(
    cp48_certificate,
    *,
    assumption_role_sha256=ASSUMPTION_ROLE_SHA256,
):
    return {
        "checkpoint48_certificate_sha256": cp48_certificate.certificate_sha256,
        "source_instance_sha256": cp48_certificate.source_instance_sha256,
        "byte_source_profile": cp48_certificate.byte_source_profile,
        "assumption_role_sha256": assumption_role_sha256,
        "backend_exact_byte_block_almost_sure_return_assumed": True,
        "unconditional_joint_full_byte_block_uniformity_assumed": True,
        "fresh_draw_capacity_and_preboundary_guards_assumed": True,
        "post_boundary_complete_success_for_every_byte_block_assumed": True,
        "fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed": True,
    }


def test_required_public_surface_and_signatures_are_exact():
    expected_public = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_"
        "ADMISSION_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_"
        "ADMISSION_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_"
        "ADMISSION_SCOPE",
        "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ASSUMPTION_MODE",
        "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ASSUMPTION_SCOPE",
        "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SEMANTIC_STATUSES",
        "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_PUSHFORWARD_THEOREM",
        "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_RETURN_CONDITIONING_CAVEAT",
        "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SELECTED_FIBER_THEOREM",
        "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SEQUENCE_NONCLAIM",
        DECLARATION_TYPE.__name__,
        CERTIFICATE_TYPE.__name__,
        DESCRIPTION_TYPE.__name__,
        RESULT_TYPE.__name__,
        OWNER_TYPE.__name__,
        ERROR_TYPE.__name__,
        DECLARE.__name__,
        VALIDATE_DECLARATION.__name__,
        CERTIFY.__name__,
        MATCHING.__name__,
        VALIDATE_CERTIFICATE.__name__,
    }
    assert set(admission.__all__) == expected_public
    assert len(admission.__all__) == len(expected_public)
    assert issubclass(ERROR_TYPE, Exception)

    assert tuple(inspect.signature(DECLARE).parameters) == (
        "checkpoint48_certificate_sha256",
        "source_instance_sha256",
        "byte_source_profile",
        "assumption_role_sha256",
        "backend_exact_byte_block_almost_sure_return_assumed",
        "unconditional_joint_full_byte_block_uniformity_assumed",
        "fresh_draw_capacity_and_preboundary_guards_assumed",
        "post_boundary_complete_success_for_every_byte_block_assumed",
        "fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed",
    )
    for parameter in inspect.signature(DECLARE).parameters.values():
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty
    assert tuple(inspect.signature(VALIDATE_DECLARATION).parameters) == ("declaration",)
    assert tuple(inspect.signature(CERTIFY).parameters) == (
        "byte_source_execution_owner",
        "assumption_declaration",
        "admission_policy",
        "admission_role_sha256",
    )
    assert tuple(inspect.signature(MATCHING).parameters) == (
        "byte_source_execution_owner",
        "assumption_declaration",
        "owner",
        "admission_policy",
        "admission_role_sha256",
    )
    assert tuple(inspect.signature(VALIDATE_CERTIFICATE).parameters) == tuple(
        inspect.signature(MATCHING).parameters
    )
    for operation in (CERTIFY, MATCHING, VALIDATE_CERTIFICATE):
        parameters = inspect.signature(operation).parameters
        assert parameters["byte_source_execution_owner"].kind is (
            inspect.Parameter.POSITIONAL_OR_KEYWORD
        )
        assert parameters["assumption_declaration"].kind is (
            inspect.Parameter.POSITIONAL_OR_KEYWORD
        )
        if operation is not CERTIFY:
            assert parameters["owner"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        assert parameters["admission_policy"].kind is inspect.Parameter.KEYWORD_ONLY
        assert parameters["admission_role_sha256"].kind is (
            inspect.Parameter.KEYWORD_ONLY
        )

    assert tuple(inspect.signature(OWNER_TYPE.describe).parameters) == (
        "self",
        "run_id",
        "initialization_index",
        "draw_index",
    )
    assert tuple(inspect.signature(OWNER_TYPE.admit_returned_result).parameters) == (
        "self",
        "cp48_result",
    )
    assert tuple(
        inspect.signature(OWNER_TYPE.validate_admission_result).parameters
    ) == (
        "self",
        "result",
    )
    assert tuple(inspect.signature(OWNER_TYPE.revalidate_live_ancestry).parameters) == (
        "self",
    )
    assert not hasattr(OWNER_TYPE, "execute")


def test_exhaustive_toy_bijection_and_total_variation_identity_are_exact():
    byte_blocks = tuple(product(range(2), repeat=2))
    words = tuple(range(4))
    codec = {block: 2 * block[0] + block[1] for block in byte_blocks}
    assert set(codec.values()) == set(words)
    assert len(set(codec.values())) == len(byte_blocks)

    uniform_bytes = _uniform(byte_blocks)
    uniform_words = _uniform(words)
    assert _pushforward(uniform_bytes, codec) == uniform_words

    for integer_weights in product(range(4), repeat=len(byte_blocks)):
        total = sum(integer_weights)
        if total == 0:
            continue
        byte_law = {
            block: Fraction(weight, total)
            for block, weight in zip(byte_blocks, integer_weights)
            if weight
        }
        word_law = _pushforward(byte_law, codec)
        assert _total_variation(byte_law, uniform_bytes, byte_blocks) == (
            _total_variation(word_law, uniform_words, words)
        )


def test_uniform_marginals_do_not_imply_joint_full_block_uniformity():
    domain = tuple(product(range(2), repeat=2))
    correlated = {(0, 0): Fraction(1, 2), (1, 1): Fraction(1, 2)}
    uniform = _uniform(domain)
    for coordinate in (0, 1):
        marginal = {
            value: sum(
                probability
                for block, probability in correlated.items()
                if block[coordinate] == value
            )
            for value in (0, 1)
        }
        assert marginal == {0: Fraction(1, 2), 1: Fraction(1, 2)}
    assert _total_variation(correlated, uniform, domain) == Fraction(1, 2)


def test_constant_success_preserves_uniformity_and_value_dependence_biases_it():
    domain = tuple(range(4))
    uniform = _uniform(domain)
    balanced = {value: Fraction(3, 7) for value in domain}
    assert _conditional_law(uniform, balanced) == uniform

    value_dependent = {0: 1, 1: 1, 2: 0, 3: 0}
    conditioned = _conditional_law(uniform, value_dependent)
    assert conditioned == {0: Fraction(1, 2), 1: Fraction(1, 2)}
    assert _total_variation(conditioned, uniform, domain) == Fraction(1, 2)
    assert _conditional_law(uniform, dict.fromkeys(domain, 0)) is None


def test_exhaustive_toy_returned_uniformity_iff_success_weights_are_constant():
    domain = tuple(range(4))
    uniform = _uniform(domain)
    rational_grid = (
        Fraction(0),
        Fraction(1, 3),
        Fraction(2, 3),
        Fraction(1),
    )
    for weights in product(rational_grid, repeat=len(domain)):
        success = dict(zip(domain, weights))
        returned = _conditional_law(uniform, success)
        if all(weight == 0 for weight in weights):
            assert returned is None
            continue
        is_constant_positive = len(set(weights)) == 1 and weights[0] > 0
        assert (returned == uniform) is is_constant_positive


def test_per_call_uniformity_does_not_imply_joint_iid():
    pair_domain = tuple(product(range(2), repeat=2))
    reused = {(0, 0): Fraction(1, 2), (1, 1): Fraction(1, 2)}
    product_uniform = _uniform(pair_domain)
    for position in (0, 1):
        assert {
            bit: sum(
                probability
                for pair, probability in reused.items()
                if pair[position] == bit
            )
            for bit in (0, 1)
        } == {0: Fraction(1, 2), 1: Fraction(1, 2)}
    assert _total_variation(reused, product_uniform, pair_domain) == Fraction(1, 2)


def test_adaptive_stopping_can_bias_the_returned_value():
    histories = tuple(product(range(2), repeat=2))
    history_law = _uniform(histories)

    def stopped_value(history):
        first, second = history
        return first if first == 1 else second

    output = _pushforward(history_law, {h: stopped_value(h) for h in histories})
    assert output == {0: Fraction(1, 4), 1: Fraction(3, 4)}
    assert _total_variation(output, _uniform((0, 1)), (0, 1)) == Fraction(1, 4)


def test_zero_selection_is_undefined_and_one_fiber_has_abstract_uniform_mass():
    source = tuple(range(8))
    uniform = _uniform(source)
    all_exhausted = {value: "exhausted" for value in source}
    outcome = _pushforward(uniform, all_exhausted)
    assert outcome == {"exhausted": Fraction(1)}
    assert _conditional_law(uniform, dict.fromkeys(source, 0)) is None

    one_selected = dict(all_exhausted)
    one_selected[3] = "selected"
    outcome = _pushforward(uniform, one_selected)
    assert outcome["selected"] == Fraction(1, len(source))
    selected = _conditional_law(
        uniform,
        {value: int(one_selected[value] == "selected") for value in source},
    )
    assert selected == {3: Fraction(1)}


def test_joint_return_event_can_destroy_returned_sequence_product_law():
    pairs = tuple(product(range(2), repeat=2))
    iid_source = _uniform(pairs)
    joint_success = {pair: int(pair[0] == pair[1]) for pair in pairs}
    returned = _conditional_law(iid_source, joint_success)
    assert returned == {(0, 0): Fraction(1, 2), (1, 1): Fraction(1, 2)}
    for position in (0, 1):
        marginal = {
            value: sum(
                probability
                for pair, probability in returned.items()
                if pair[position] == value
            )
            for value in (0, 1)
        }
        assert marginal == {0: Fraction(1, 2), 1: Fraction(1, 2)}
    assert _total_variation(returned, iid_source, pairs) == Fraction(1, 2)


def test_data_processing_holds_and_source_to_output_lower_bound_has_no_converse():
    source_domain = tuple(range(4))
    uniform_source = _uniform(source_domain)
    point_source = {0: Fraction(1)}
    source_tv = _total_variation(point_source, uniform_source, source_domain)
    assert source_tv == Fraction(3, 4)

    parity = {value: value % 2 for value in source_domain}
    parity_point = _pushforward(point_source, parity)
    parity_uniform = _pushforward(uniform_source, parity)
    assert _total_variation(parity_point, parity_uniform, (0, 1)) == Fraction(1, 2)
    assert Fraction(1, 2) <= source_tv

    constant = dict.fromkeys(source_domain, "same-output")
    assert _pushforward(point_source, constant) == _pushforward(
        uniform_source, constant
    )
    assert (
        _total_variation(
            _pushforward(point_source, constant),
            _pushforward(uniform_source, constant),
            ("same-output",),
        )
        == 0
    )


def test_identifier_uniqueness_is_orthogonal_to_sample_value_collision():
    draw_identifiers = (11, 12, 13)
    returned_blocks = (b"same", b"same", b"same")
    assert len(set(draw_identifiers)) == len(draw_identifiers)
    assert len(set(returned_blocks)) == 1
    duplicate_identifier_rows = ((11, b"left"), (11, b"right"))
    assert len({row[0] for row in duplicate_identifier_rows}) == 1
    assert len({row[1] for row in duplicate_identifier_rows}) == 2


def test_pure_exact_count_helpers_are_arithmetic_not_source_law_evidence():
    uniform_probability = admission._uniform_fiber_probability
    conditioned_probability = admission._return_conditioned_fiber_probability
    assert uniform_probability(0, 16) == Fraction(0)
    assert uniform_probability(1, 16) == Fraction(1, 16)
    assert uniform_probability(16, 16) == Fraction(1)
    assert conditioned_probability(0, 9) == Fraction(0)
    assert conditioned_probability(3, 9) == Fraction(1, 3)
    assert conditioned_probability(9, 9) == Fraction(1)
    # The second denominator is only a declared uniform-domain returned-support
    # count.  The arithmetic helper cannot establish CP48 return totality or a
    # live source law; CP49's production premise separately assumes totality.
    for malformed in (True, 1.0, _IntSubclass(1), -1):
        with pytest.raises((TypeError, ValueError)):
            uniform_probability(malformed, 16)
    for malformed in (False, 0.0, _IntSubclass(9), -1):
        with pytest.raises((TypeError, ValueError)):
            conditioned_probability(1, malformed)
    for operation in (uniform_probability, conditioned_probability):
        for malformed in (True, 1.0, _IntSubclass(1), _TouchBomb()):
            with pytest.raises((TypeError, ValueError)):
                operation(malformed, 16)
            if isinstance(malformed, _TouchBomb):
                assert malformed.calls == 0
    with pytest.raises(ValueError):
        conditioned_probability(1, 0)
    with pytest.raises(ValueError):
        uniform_probability(17, 16)


def test_private_selected_extractor_is_only_structural_branch_evidence():
    """Exercise all branches without presenting a synthetic object as CP48 evidence."""

    selected_configuration = object()
    selected_sha256 = "d" * 64
    statuses = admission.INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SEMANTIC_STATUSES
    assert statuses == (
        "preparation_failure",
        "quota_certification_failure",
        "selected",
        "exhausted",
    )
    for status in statuses:
        is_selected = status == "selected"
        cp42 = SimpleNamespace(
            status=status,
            selected_configuration=(selected_configuration if is_selected else None),
            selected_configuration_sha256=(selected_sha256 if is_selected else None),
        )
        applied = SimpleNamespace(
            status=status,
            comparison_count=3,
            selected_attempt_index=(2 if is_selected else None),
            selected_configuration_sha256=(selected_sha256 if is_selected else None),
            checkpoint42_applied_decision=(
                cp42 if status != "preparation_failure" else None
            ),
        )
        synthetic = SimpleNamespace(
            checkpoint47_result=SimpleNamespace(
                semantic_status=status,
                checkpoint43_applied_decision=applied,
            )
        )
        extracted = admission._extract_semantic_children(synthetic)
        assert extracted[0] is applied
        assert extracted[1] == status
        assert extracted[2] == 3
        assert extracted[3] == (2 if is_selected else None)
        assert extracted[4] is (selected_configuration if is_selected else None)
        assert extracted[5] == (selected_sha256 if is_selected else None)

    mismatched_cp42 = SimpleNamespace(
        status="selected",
        selected_configuration=selected_configuration,
        selected_configuration_sha256="e" * 64,
    )
    mismatched = SimpleNamespace(
        checkpoint47_result=SimpleNamespace(
            semantic_status="selected",
            checkpoint43_applied_decision=SimpleNamespace(
                status="selected",
                comparison_count=3,
                selected_attempt_index=2,
                selected_configuration_sha256=selected_sha256,
                checkpoint42_applied_decision=mismatched_cp42,
            ),
        )
    )
    with pytest.raises(ValueError):
        admission._extract_semantic_children(mismatched)


def test_flag_partition_and_record_shapes_make_every_nonclaim_explicit():
    assert admission._CERTIFICATE_TRUE_FLAGS == (
        "exact_checkpoint48_owner_and_certificate_binding_certified",
        "exact_transitive_checkpoint47_43_ancestry_bound",
        "cp48_codec_bijection_inherited",
        "four_semantic_statuses_preserved",
        "one_draw_pushforward_theorem_recorded",
        "returned_conditioning_formula_recorded",
        "selected_nonempty_fiber_theorem_recorded",
        "structural_nonexecuting_validation_certified",
        "source_law_is_external_assumption_only",
        "passed",
    )
    assert admission._CERTIFICATE_FALSE_FLAGS == (
        "operational_realization_certified",
        "backend_law_verified",
        "backend_totality_verified",
        "returned_sequence_iid_certified",
        "adaptive_query_or_retry_law_certified",
        "global_uniqueness_certified",
        "cp40_initializer_admission_certified",
        "live_initializer_distribution_certified",
        "general_initializer_admissible",
        "formal_test28_closed",
        "scientific_claim_promoted",
        "model_quality_claim_promoted",
        "generality_claim_promoted",
        "manuscript_claim_promoted",
        "loaded_code_integrity_certified",
        "runtime_portable",
    )
    forbidden_artifacts = {
        "checkpoint40_result",
        "initializer_result",
        "intensity",
        "lineage",
        "tag3_payload",
        "sampler_path",
    }
    for record_type in (
        DECLARATION_TYPE,
        CERTIFICATE_TYPE,
        DESCRIPTION_TYPE,
        RESULT_TYPE,
    ):
        assert forbidden_artifacts.isdisjoint(record_type.__annotations__)
    assert "assumption-only" in (
        admission.INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ASSUMPTION_SCOPE
    )
    assert "do-not-imply-returned-sequence-IID" in (
        admission.INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SEQUENCE_NONCLAIM
    )
    assert "not-CP40" in (
        admission.PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ADMISSION_SCOPE
    )
    selected_theorem = (
        admission.INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SELECTED_FIBER_THEOREM
    )
    assert "configuration-value" in selected_theorem
    assert "record-separately-retains-runtime-object-identity" in selected_theorem


def test_source_ast_has_no_execution_rng_retry_or_cp39_cp40_route():
    source_path = Path(inspect.getsourcefile(admission)).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert {"os", "random", "secrets", "numpy"}.isdisjoint(imports)
    assert not tuple(node for node in ast.walk(tree) if isinstance(node, ast.While))

    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    replay_capable_callees = {
        "execute",
        "coordinate",
        "resolve",
        "prepare",
        "decide",
        "evaluate_predecision",
        "validate_predecision_result",
        "_evaluate_predecision_operation",
        "apply_decision_words",
        "validate_applied_decision",
        "_make_applied_decision",
        "witness_successful_parity",
        "validate_successful_parity_witness",
        "evaluate_and_apply",
        "_evaluate_operation",
        "_apply_trusted",
        "_CP42_EVALUATE",
        "_CP42_VALIDATE_PREDECISION",
        "_CP42_APPLY",
        "_CP42_VALIDATE_APPLIED",
        "_CP42_APPLIED_BUILDER",
        "_CP42_WITNESS",
        "_CP42_VALIDATE_WITNESS",
        "_CP43_EVALUATE_AND_APPLY",
    }
    assert replay_capable_callees.isdisjoint(called_attributes)
    assert replay_capable_callees.isdisjoint(called_names)

    imported_modules = tuple(
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    )
    assert all("checkpoint39" not in module for module in imported_modules)
    assert all("checkpoint40" not in module for module in imported_modules)
    assert "_CP48_EXECUTE" not in source_path.read_text(encoding="utf-8")


def test_record_types_are_sealed_nonpickleable_and_not_publicly_constructible():
    for record_type in (
        DECLARATION_TYPE,
        CERTIFICATE_TYPE,
        DESCRIPTION_TYPE,
        RESULT_TYPE,
        OWNER_TYPE,
    ):
        with pytest.raises(TypeError):
            type("HostileSubclass", (record_type,), {})
        with pytest.raises(TypeError):
            record_type()

    declaration = DECLARE(
        checkpoint48_certificate_sha256="1" * 64,
        source_instance_sha256="2" * 64,
        byte_source_profile=(
            admission._CP48_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED
        ),
        assumption_role_sha256=ASSUMPTION_ROLE_SHA256,
        backend_exact_byte_block_almost_sure_return_assumed=True,
        unconditional_joint_full_byte_block_uniformity_assumed=True,
        fresh_draw_capacity_and_preboundary_guards_assumed=True,
        post_boundary_complete_success_for_every_byte_block_assumed=True,
        fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed=True,
    )
    assert VALIDATE_DECLARATION(declaration) is declaration
    with pytest.raises((TypeError, AttributeError)):
        declaration.assumption_only = False
    with pytest.raises(TypeError):
        pickle.dumps(declaration)


def test_assumption_declaration_is_exact_explicit_and_never_self_attesting():
    declaration = DECLARE(
        checkpoint48_certificate_sha256="1" * 64,
        source_instance_sha256="2" * 64,
        byte_source_profile=(
            admission._CP48_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED
        ),
        assumption_role_sha256=ASSUMPTION_ROLE_SHA256,
        backend_exact_byte_block_almost_sure_return_assumed=True,
        unconditional_joint_full_byte_block_uniformity_assumed=True,
        fresh_draw_capacity_and_preboundary_guards_assumed=True,
        post_boundary_complete_success_for_every_byte_block_assumed=True,
        fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed=True,
    )
    assert declaration.assumption_only is True
    assert declaration.operational_realization_certified is False
    assert declaration.backend_law_verified is False
    assert declaration.backend_totality_verified is False
    assert declaration.backend_exact_byte_block_almost_sure_return_assumed is True
    assert declaration.unconditional_joint_full_byte_block_uniformity_assumed is True
    assert declaration.fresh_draw_capacity_and_preboundary_guards_assumed is True
    assert (
        declaration.post_boundary_complete_success_for_every_byte_block_assumed is True
    )
    assert declaration.pointwise_one_draw_theorem_only is True
    assert (
        declaration.fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed
        is True
    )
    assert VALIDATE_DECLARATION(declaration) is declaration


def test_neither_operational_profile_can_turn_an_assumption_into_attestation():
    profiles = (
        admission._CP48_PROFILE_SYSTEM_OS_URANDOM_OPERATIONAL,
        admission._CP48_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED,
    )
    for profile in profiles:
        declaration = DECLARE(
            checkpoint48_certificate_sha256="1" * 64,
            source_instance_sha256="2" * 64,
            byte_source_profile=profile,
            assumption_role_sha256=ASSUMPTION_ROLE_SHA256,
            backend_exact_byte_block_almost_sure_return_assumed=True,
            unconditional_joint_full_byte_block_uniformity_assumed=True,
            fresh_draw_capacity_and_preboundary_guards_assumed=True,
            post_boundary_complete_success_for_every_byte_block_assumed=True,
            fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed=True,
        )
        assert declaration.byte_source_profile == profile
        assert declaration.assumption_only is True
        assert declaration.operational_realization_certified is False
        assert declaration.backend_law_verified is False
        assert declaration.backend_totality_verified is False


def test_declaration_hostile_scalars_and_false_premises_refuse_without_coercion():
    valid = {
        "checkpoint48_certificate_sha256": "1" * 64,
        "source_instance_sha256": "2" * 64,
        "byte_source_profile": (
            admission._CP48_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED
        ),
        "assumption_role_sha256": ASSUMPTION_ROLE_SHA256,
        "backend_exact_byte_block_almost_sure_return_assumed": True,
        "unconditional_joint_full_byte_block_uniformity_assumed": True,
        "fresh_draw_capacity_and_preboundary_guards_assumed": True,
        "post_boundary_complete_success_for_every_byte_block_assumed": True,
        "fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed": True,
    }
    for name in (
        "backend_exact_byte_block_almost_sure_return_assumed",
        "unconditional_joint_full_byte_block_uniformity_assumed",
        "fresh_draw_capacity_and_preboundary_guards_assumed",
        "post_boundary_complete_success_for_every_byte_block_assumed",
        "fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed",
    ):
        for malformed in (False, 1, _IntSubclass(1), _TouchBomb()):
            arguments = dict(valid)
            arguments[name] = malformed
            with pytest.raises((TypeError, ValueError)):
                DECLARE(**arguments)
            if isinstance(malformed, _TouchBomb):
                assert malformed.calls == 0
    for name in (
        "checkpoint48_certificate_sha256",
        "source_instance_sha256",
        "assumption_role_sha256",
    ):
        arguments = dict(valid)
        arguments[name] = _TouchBomb()
        with pytest.raises(TypeError):
            DECLARE(**arguments)
        assert arguments[name].calls == 0
    arguments = dict(valid)
    arguments["byte_source_profile"] = "invented-source-profile"
    with pytest.raises(ValueError):
        DECLARE(**arguments)


def test_declaration_tamper_refuses_even_after_attacker_redigests():
    declaration = DECLARE(
        checkpoint48_certificate_sha256="1" * 64,
        source_instance_sha256="2" * 64,
        byte_source_profile=(
            admission._CP48_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED
        ),
        assumption_role_sha256=ASSUMPTION_ROLE_SHA256,
        backend_exact_byte_block_almost_sure_return_assumed=True,
        unconditional_joint_full_byte_block_uniformity_assumed=True,
        fresh_draw_capacity_and_preboundary_guards_assumed=True,
        post_boundary_complete_success_for_every_byte_block_assumed=True,
        fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed=True,
    )
    forged = _forged(declaration, operational_realization_certified=True)
    with pytest.raises(ValueError):
        VALIDATE_DECLARATION(forged)
    payload = admission._declaration_payload(
        {name: getattr(forged, name) for name in DECLARATION_TYPE.__annotations__}
    )
    forged = _forged(
        forged,
        declaration_sha256=admission._semantic_digest(payload),
    )
    with pytest.raises(ValueError):
        VALIDATE_DECLARATION(forged)


def test_declaration_and_pure_law_helpers_leave_global_rng_states_unchanged():
    before = _rng_snapshot()
    declaration = DECLARE(
        checkpoint48_certificate_sha256="1" * 64,
        source_instance_sha256="2" * 64,
        byte_source_profile=(
            admission._CP48_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED
        ),
        assumption_role_sha256=ASSUMPTION_ROLE_SHA256,
        backend_exact_byte_block_almost_sure_return_assumed=True,
        unconditional_joint_full_byte_block_uniformity_assumed=True,
        fresh_draw_capacity_and_preboundary_guards_assumed=True,
        post_boundary_complete_success_for_every_byte_block_assumed=True,
        fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed=True,
    )
    assert VALIDATE_DECLARATION(declaration) is declaration
    assert admission._uniform_fiber_probability(3, 17) == Fraction(3, 17)
    assert admission._return_conditioned_fiber_probability(3, 17) == Fraction(3, 17)
    _assert_rng_unchanged(before)


@pytest.fixture(scope="module")
def owner_bound_evidence():
    checkpoint48 = importlib.import_module(
        "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "byte_source_full_capsule_execution"
    )
    evidence = checkpoint48.owner_bound_evidence.__wrapped__()
    external_parent = evidence["external_owner"]
    system_parent = evidence["system_owner"]
    selected_run_id = 60_001
    selected_initialization_index = 60_002
    selected_draw_index = 60_003
    selected_source_instance_sha256 = "9" * 64
    cp43_owner = evidence[
        "source_support_owner"
    ].factorized_execution_owner.factorization_closure_owner
    assert cp43_owner.certificate.attempt_budget == 1
    # Frozen CP42 `test_g_is_w_free_and_h_uses_exact_half_open_quota_boundaries`
    # proves that all-zero V yields positive quotas on this same underlying
    # one-attempt model.  Thus exact W=0 must select its first row.
    proposal_words = (0,) * cp43_owner.certificate.proposal_word_count
    decision_words = (0,) * cp43_owner.certificate.decision_word_count
    selected_backend_calls = []
    selected_payload = {}

    def selected_byte_source(source_instance_sha256, draw_index, byte_count):
        selected_backend_calls.append((source_instance_sha256, draw_index, byte_count))
        assert source_instance_sha256 == selected_source_instance_sha256
        assert draw_index == selected_draw_index
        raw_bytes = selected_payload["raw_bytes"]
        assert byte_count == len(raw_bytes)
        return raw_bytes

    evidence["selected_byte_source"] = selected_byte_source
    with _observe_owner_operations(
        checkpoint48,
        evidence,
        forbidden=frozenset(),
    ) as selected_construction_calls:
        selected_full_words = cp43_owner.join_full_words(
            proposal_words,
            decision_words,
        )
        selected_raw_bytes = checkpoint48.execution._encode_big_endian_words(
            selected_full_words
        )
        selected_payload["raw_bytes"] = selected_raw_bytes
        selected_parent = checkpoint48.CERTIFY(
            evidence["source_model_owner"],
            source_instance_sha256=selected_source_instance_sha256,
            byte_source_profile=checkpoint48.EXTERNAL_PROFILE,
            external_byte_source=selected_byte_source,
            byte_source_role_sha256="8" * 64,
            provider_role_sha256="7" * 64,
            execution_role_sha256="6" * 64,
            execution_policy=checkpoint48.POLICY,
            max_retired_draws=checkpoint48.MAX_RETIRED_DRAWS,
        )
        selected_parent_result = selected_parent.execute(
            selected_run_id,
            selected_initialization_index,
            selected_draw_index,
        )
    assert selected_backend_calls == [
        (
            selected_source_instance_sha256,
            selected_draw_index,
            len(selected_raw_bytes),
        )
    ]
    assert selected_construction_calls["selected_external_backend"] == 1
    assert selected_construction_calls["cp48_execute"] == 1
    assert selected_construction_calls["cp47_execute"] == 1
    assert selected_construction_calls["cp43_evaluate_and_apply"] == 1
    assert selected_construction_calls["cp42_applied_semantic_builder"] == 1
    selected_applied = (
        selected_parent_result.checkpoint47_result.checkpoint43_applied_decision
    )
    assert selected_parent_result.checkpoint47_result.semantic_status == "selected"
    assert selected_applied.status == "selected"
    assert selected_applied.selected_attempt_index == 0
    assert selected_applied.comparison_count == 1
    selected_cp42 = selected_applied.checkpoint42_applied_decision
    assert selected_cp42 is not None
    assert selected_cp42.selected_configuration is not None
    assert selected_cp42.predecision_result.status == "ready"
    assert len(selected_cp42.predecision_result.rows) == 1
    assert selected_cp42.predecision_result.rows[0].acceptance_quota > 0
    assert selected_cp42.decision_words == (0,)

    external_declaration = DECLARE(
        **_declaration_arguments(external_parent.certificate)
    )
    system_declaration = DECLARE(
        **_declaration_arguments(
            system_parent.certificate,
            assumption_role_sha256="c" * 64,
        )
    )
    selected_declaration = DECLARE(
        **_declaration_arguments(
            selected_parent.certificate,
            assumption_role_sha256="e" * 64,
        )
    )
    before_backend_calls = len(evidence["backend_calls"])
    with _observe_owner_operations(checkpoint48, evidence) as certification_calls:
        external_owner = CERTIFY(
            external_parent,
            external_declaration,
            admission_policy=POLICY,
            admission_role_sha256=ADMISSION_ROLE_SHA256,
        )
        system_owner = CERTIFY(
            system_parent,
            system_declaration,
            admission_policy=POLICY,
            admission_role_sha256="d" * 64,
        )
        selected_owner = CERTIFY(
            selected_parent,
            selected_declaration,
            admission_policy=POLICY,
            admission_role_sha256="f" * 64,
        )
    assert len(evidence["backend_calls"]) == before_backend_calls
    assert all(
        certification_calls[name] == 0 for name in _NONSTRUCTURAL_OPERATION_NAMES
    )
    return {
        "checkpoint48": checkpoint48,
        "evidence": evidence,
        "external_declaration": external_declaration,
        "system_declaration": system_declaration,
        "selected_declaration": selected_declaration,
        "external_owner": external_owner,
        "system_owner": system_owner,
        "selected_owner": selected_owner,
        "selected_parent": selected_parent,
        "selected_parent_result": selected_parent_result,
        "selected_full_words": selected_full_words,
        "selected_decision_words": decision_words,
        "selected_backend_calls": selected_backend_calls,
        "selected_construction_calls": selected_construction_calls,
        "external_admission_role_sha256": ADMISSION_ROLE_SHA256,
        "system_admission_role_sha256": "d" * 64,
        "selected_admission_role_sha256": "f" * 64,
        "certification_calls": certification_calls,
    }


def test_owner_bound_certificate_has_exact_cp48_through_cp43_ancestry(
    owner_bound_evidence,
):
    bound = owner_bound_evidence
    base = bound["evidence"]
    checkpoint48 = bound["checkpoint48"]
    rows = (
        (
            base["external_owner"],
            bound["external_declaration"],
            bound["external_owner"],
            bound["external_admission_role_sha256"],
        ),
        (
            base["system_owner"],
            bound["system_declaration"],
            bound["system_owner"],
            bound["system_admission_role_sha256"],
        ),
        (
            bound["selected_parent"],
            bound["selected_declaration"],
            bound["selected_owner"],
            bound["selected_admission_role_sha256"],
        ),
    )
    for cp48_owner, declaration, owner, admission_role in rows:
        certificate = owner.certificate
        cp48_certificate = cp48_owner.certificate
        cp47_certificate = cp48_certificate.checkpoint47_certificate
        cp46_certificate = cp47_certificate.checkpoint46_certificate
        cp45_certificate = cp46_certificate.checkpoint45_certificate
        cp44_certificate = cp45_certificate.checkpoint44_certificate
        cp43_certificate = cp44_certificate.checkpoint43_certificate

        assert owner.byte_source_execution_owner is cp48_owner
        assert owner.assumption_declaration is declaration
        assert certificate.byte_source_execution_certificate is cp48_certificate
        assert certificate.assumption_declaration is declaration
        assert cp46_certificate is base["source_model_owner"].certificate
        assert certificate.checkpoint48_certificate_sha256 == (
            cp48_certificate.certificate_sha256
        )
        assert certificate.checkpoint47_certificate_sha256 == (
            cp47_certificate.certificate_sha256
        )
        assert certificate.checkpoint43_certificate_sha256 == (
            cp43_certificate.certificate_sha256
        )
        assert certificate.byte_source_execution_owner_runtime_identity == id(
            cp48_owner
        )
        assert certificate.source_instance_sha256 == (
            cp48_certificate.source_instance_sha256
        )
        assert certificate.byte_source_profile == cp48_certificate.byte_source_profile
        assert certificate.raw_byte_count == cp48_certificate.raw_byte_count
        assert certificate.full_word_count == cp48_certificate.full_word_count
        assert certificate.proposal_word_count == cp48_certificate.proposal_word_count
        assert certificate.decision_word_count == cp48_certificate.decision_word_count
        for name in admission._CERTIFICATE_TRUE_FLAGS:
            assert getattr(certificate, name) is True
        for name in admission._CERTIFICATE_FALSE_FLAGS:
            assert getattr(certificate, name) is False
        assert certificate.source_law_is_external_assumption_only is True
        assert certificate.operational_realization_certified is False
        assert declaration.assumption_only is True
        assert declaration.fresh_draw_capacity_and_preboundary_guards_assumed is True
        assert (
            declaration.post_boundary_complete_success_for_every_byte_block_assumed
            is True
        )

        with _observe_owner_operations(checkpoint48, base) as calls:
            assert (
                MATCHING(
                    cp48_owner,
                    declaration,
                    owner,
                    admission_policy=POLICY,
                    admission_role_sha256=admission_role,
                )
                is owner
            )
            assert (
                VALIDATE_CERTIFICATE(
                    cp48_owner,
                    declaration,
                    owner,
                    admission_policy=POLICY,
                    admission_role_sha256=admission_role,
                )
                is certificate
            )
        assert all(calls[name] == 0 for name in _NONSTRUCTURAL_OPERATION_NAMES)


def test_owner_bound_describe_is_pointwise_nonexecuting_and_hostile_scalar_safe(
    owner_bound_evidence,
):
    bound = owner_bound_evidence
    checkpoint48 = bound["checkpoint48"]
    base = bound["evidence"]
    owner = bound["external_owner"]
    before_backend_calls = len(base["backend_calls"])
    with _observe_owner_operations(checkpoint48, base) as calls:
        first = owner.describe(701, 702, 703)
        second = owner.describe(701, 702, 704)
    assert len(base["backend_calls"]) == before_backend_calls
    assert all(calls[name] == 0 for name in calls)
    assert type(first) is DESCRIPTION_TYPE
    assert first.certificate is owner.certificate
    assert (first.run_id, first.initialization_index, first.draw_index) == (
        701,
        702,
        703,
    )
    assert second.certificate is owner.certificate
    assert second.draw_index == 704
    assert second.description_sha256 != first.description_sha256
    assert first.assumption_only is True
    assert first.backend_exact_byte_block_almost_sure_return_is_assumed is True
    assert first.unconditional_joint_full_byte_block_uniformity_is_assumed is True
    assert first.preboundary_admissibility_is_assumed is True
    assert first.post_boundary_complete_success_is_assumed is True
    assert (
        first.fixed_deterministic_replay_stable_typed_total_semantics_is_assumed is True
    )
    assert first.reference_semantic_law_defined_under_assumptions is True
    assert first.description_is_nonexecuting is True
    assert first.source_or_semantic_replay_performed is False
    assert first.backend_law_operationally_verified is False
    assert first.backend_totality_operationally_verified is False
    assert first.preboundary_admissibility_operationally_verified is False
    assert first.duplicate_or_capacity_refusal_totalized is False
    assert first.operational_realization_certified is False
    assert first.returned_sequence_iid_certified is False
    assert first.cp40_initializer_admission_certified is False
    assert first.general_initializer_admissible is False

    valid_coordinates = [701, 702, 703]
    for index in range(3):
        for malformed in (True, -1, 1.0, _IntSubclass(1), _TouchBomb()):
            arguments = list(valid_coordinates)
            arguments[index] = malformed
            with _observe_owner_operations(checkpoint48, base) as hostile_calls:
                with pytest.raises((TypeError, ValueError)):
                    owner.describe(*arguments)
            assert all(value == 0 for value in hostile_calls.values())
            if isinstance(malformed, _TouchBomb):
                assert malformed.calls == 0


def test_owner_bound_admit_preserves_natural_status_and_exact_selected_custody(
    owner_bound_evidence,
):
    bound = owner_bound_evidence
    checkpoint48 = bound["checkpoint48"]
    base = bound["evidence"]
    rows = (
        (bound["external_owner"], base["first_result"]),
        (bound["system_owner"], base["system_result"]),
        (bound["selected_owner"], bound["selected_parent_result"]),
    )
    for owner, cp48_result in rows:
        before_backend_calls = len(base["backend_calls"])
        with _observe_owner_operations(checkpoint48, base) as calls:
            result = owner.admit_returned_result(cp48_result)
        assert len(base["backend_calls"]) == before_backend_calls
        assert calls["cp48_validate_result"] == 1
        assert all(calls[name] == 0 for name in _NONSTRUCTURAL_OPERATION_NAMES)
        cp47 = cp48_result.checkpoint47_result
        applied = cp47.checkpoint43_applied_decision
        assert type(result) is RESULT_TYPE
        assert result.certificate is owner.certificate
        assert result.checkpoint48_result is cp48_result
        assert result.checkpoint43_applied_decision is applied
        assert result.semantic_status == cp47.semantic_status == applied.status
        assert result.semantic_status in (
            admission.INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SEMANTIC_STATUSES
        )
        assert result.checkpoint48_result_sha256 == cp48_result.result_sha256
        assert result.checkpoint43_applied_decision_sha256 == (
            applied.applied_decision_sha256
        )
        assert result.comparison_count == applied.comparison_count
        assert result.exact_status_and_selected_object_identity_preserved is True
        assert (
            result.structurally_admitted_to_enriched_cp43_cp42_reference_codomain
            is True
        )
        assert result.structural_validation_is_nonexecuting_and_nonreplaying is True
        assert result.source_law_assumption_only is True
        for name in (
            "operational_realization_certified",
            "backend_law_verified",
            "backend_totality_verified",
            "live_initializer_distribution_certified",
            "cp40_initializer_admission_certified",
            "general_initializer_admissible",
            "formal_test28_closed",
            "global_uniqueness_certified",
            "scientific_claim_promoted",
            "model_quality_claim_promoted",
            "generality_claim_promoted",
            "manuscript_claim_promoted",
        ):
            assert getattr(result, name) is False

        if result.semantic_status == "selected":
            cp42 = applied.checkpoint42_applied_decision
            assert cp42 is not None
            assert result.selected_configuration is cp42.selected_configuration
            assert result.selected_configuration_sha256 == (
                cp42.selected_configuration_sha256
            )
            assert result.selected_attempt_index == applied.selected_attempt_index
            assert result.selected_enriched_semantic_atom_fiber_nonempty is True
            assert result.selected_configuration_value_fiber_nonempty is True
            # This positive mass is only under the declared abstract uniform and
            # pre/post-boundary totality assumptions, never observed source-law
            # or operational initializer evidence.
            assert (
                result.abstract_uniform_selection_mass_positive_under_assumptions
                is True
            )
            assert (
                result.selected_conditioned_reference_law_defined_under_assumptions
                is True
            )
            assert result.selected_uniform_single_preimage_mass_denominator_log2 == (
                64 * owner.certificate.full_word_count
            )
            assert owner.assumption_declaration.assumption_only is True
            assert result.operational_realization_certified is False
        else:
            assert result.selected_attempt_index is None
            assert result.selected_configuration is None
            assert result.selected_configuration_sha256 is None
            assert result.selected_enriched_semantic_atom_fiber_nonempty is False
            assert result.selected_configuration_value_fiber_nonempty is False
            assert (
                result.abstract_uniform_selection_mass_positive_under_assumptions
                is False
            )
            assert (
                result.selected_conditioned_reference_law_defined_under_assumptions
                is False
            )
            assert result.selected_uniform_single_preimage_mass_denominator_log2 is None
            cp42 = applied.checkpoint42_applied_decision
            if cp42 is not None:
                assert cp42.selected_configuration is None
                assert cp42.selected_configuration_sha256 is None

    selected_parent_result = bound["selected_parent_result"]
    selected_applied = (
        selected_parent_result.checkpoint47_result.checkpoint43_applied_decision
    )
    with _observe_owner_operations(checkpoint48, base) as selected_calls:
        selected_result = bound["selected_owner"].admit_returned_result(
            selected_parent_result
        )
    assert selected_calls["cp48_validate_result"] == 1
    assert all(selected_calls[name] == 0 for name in _NONSTRUCTURAL_OPERATION_NAMES)
    assert selected_parent_result.source_full_words == bound["selected_full_words"]
    selected_cp42 = selected_applied.checkpoint42_applied_decision
    assert selected_cp42 is not None
    selected_quota = selected_cp42.predecision_result.rows[0].acceptance_quota
    selected_decision_word = bound["selected_decision_words"][0]
    assert selected_decision_word == 0
    assert 0 <= selected_decision_word < selected_quota
    assert selected_result.semantic_status == "selected"
    assert selected_applied.status == "selected"
    assert selected_applied.selected_attempt_index == 0
    assert selected_cp42.status == "selected"
    assert selected_result.selected_attempt_index == 0
    assert selected_result.selected_configuration is (
        selected_cp42.selected_configuration
    )
    assert selected_result.selected_configuration_sha256 == (
        selected_cp42.selected_configuration_sha256
    )
    assert selected_result.selected_enriched_semantic_atom_fiber_nonempty is True
    assert selected_result.selected_configuration_value_fiber_nonempty is True
    # This is positive reference mass only under CP49's explicit abstract
    # source/totality/deterministic-object-semantics assumptions.  Exact object
    # identity below is custody evidence, not a probability law over runtime IDs.
    assert (
        selected_result.abstract_uniform_selection_mass_positive_under_assumptions
        is True
    )
    assert (
        selected_result.selected_conditioned_reference_law_defined_under_assumptions
        is True
    )
    assert selected_result.selected_uniform_single_preimage_mass_denominator_log2 == (
        64 * bound["selected_owner"].certificate.full_word_count
    )
    assert selected_result.operational_realization_certified is False


def test_owner_bound_validation_is_structural_and_explicit_live_revalidation_only(
    owner_bound_evidence,
):
    bound = owner_bound_evidence
    checkpoint48 = bound["checkpoint48"]
    base = bound["evidence"]
    owner = bound["external_owner"]
    with _observe_owner_operations(checkpoint48, base) as admission_calls:
        result = owner.admit_returned_result(base["first_result"])
    assert admission_calls["cp48_validate_result"] == 1
    with _observe_owner_operations(checkpoint48, base) as validation_calls:
        assert owner.validate_admission_result(result) is result
    assert validation_calls["cp48_validate_result"] == 1
    assert all(validation_calls[name] == 0 for name in _NONSTRUCTURAL_OPERATION_NAMES)

    allowed = _NONSTRUCTURAL_OPERATION_NAMES - {"cp48_live_revalidate"}
    with _observe_owner_operations(
        checkpoint48,
        base,
        forbidden=allowed,
    ) as live_calls:
        assert owner.revalidate_live_ancestry() is owner.certificate
    assert live_calls["cp48_live_revalidate"] == 1
    assert live_calls["cp48_execute"] == 0
    assert live_calls["cp48_acquire"] == 0
    assert live_calls["cp47_execute"] == 0
    assert live_calls["cp43_evaluate_and_apply"] == 0
    assert live_calls["external_backend"] == 0


def test_owner_bound_cross_owner_declaration_certificate_and_result_splices_refuse(
    owner_bound_evidence,
):
    bound = owner_bound_evidence
    checkpoint48 = bound["checkpoint48"]
    base = bound["evidence"]
    external_owner = bound["external_owner"]
    system_owner = bound["system_owner"]
    system_declaration = bound["system_declaration"]

    with _observe_owner_operations(checkpoint48, base):
        external_result = external_owner.admit_returned_result(base["first_result"])
        system_result = system_owner.admit_returned_result(base["system_result"])
        with pytest.raises(ValueError):
            external_owner.admit_returned_result(base["system_result"])
        with pytest.raises(ValueError):
            system_owner.admit_returned_result(base["first_result"])
        with pytest.raises(ValueError):
            system_owner.validate_admission_result(external_result)
        with pytest.raises(ValueError):
            external_owner.validate_admission_result(system_result)
        with pytest.raises(ValueError):
            MATCHING(
                base["external_owner"],
                system_declaration,
                external_owner,
                admission_policy=POLICY,
                admission_role_sha256=ADMISSION_ROLE_SHA256,
            )
        with pytest.raises(ValueError):
            VALIDATE_CERTIFICATE(
                base["system_owner"],
                system_declaration,
                external_owner,
                admission_policy=POLICY,
                admission_role_sha256=ADMISSION_ROLE_SHA256,
            )
        with pytest.raises(ValueError):
            CERTIFY(
                base["external_owner"],
                system_declaration,
                admission_policy=POLICY,
                admission_role_sha256="f" * 64,
            )

    spliced_certificate = _redigest_record(
        external_owner.certificate,
        admission._certificate_payload,
        "certificate_sha256",
        assumption_declaration=system_declaration,
        assumption_declaration_sha256=system_declaration.declaration_sha256,
        assumption_role_sha256=system_declaration.assumption_role_sha256,
    )
    with pytest.raises(ValueError):
        admission._validate_certificate(spliced_certificate)

    spliced_result = _redigest_record(
        external_result,
        admission._result_payload,
        "result_sha256",
        certificate=system_owner.certificate,
        certificate_sha256=system_owner.certificate.certificate_sha256,
    )
    with _observe_owner_operations(checkpoint48, base):
        with pytest.raises(ValueError):
            external_owner.validate_admission_result(spliced_result)
        with pytest.raises(ValueError):
            system_owner.validate_admission_result(spliced_result)


def test_owner_bound_tamper_redigest_and_claim_promotion_all_refuse(
    owner_bound_evidence,
):
    bound = owner_bound_evidence
    checkpoint48 = bound["checkpoint48"]
    base = bound["evidence"]
    owner = bound["external_owner"]
    certificate = owner.certificate
    description = owner.describe(801, 802, 803)
    result = owner.admit_returned_result(base["first_result"])
    selected_owner = bound["selected_owner"]
    selected_result = selected_owner.admit_returned_result(
        bound["selected_parent_result"]
    )
    assert selected_result.semantic_status == "selected"

    for field in (
        "backend_law_verified",
        "backend_totality_verified",
        "returned_sequence_iid_certified",
        "adaptive_query_or_retry_law_certified",
        "global_uniqueness_certified",
        "cp40_initializer_admission_certified",
        "live_initializer_distribution_certified",
        "formal_test28_closed",
    ):
        plain = _forged(certificate, **{field: True})
        with pytest.raises(ValueError):
            admission._validate_certificate(plain)
        redigested = _redigest_record(
            certificate,
            admission._certificate_payload,
            "certificate_sha256",
            **{field: True},
        )
        with pytest.raises(ValueError):
            admission._validate_certificate(redigested)

    replayed_description = _redigest_record(
        description,
        admission._description_payload,
        "description_sha256",
        source_or_semantic_replay_performed=True,
    )
    with pytest.raises(ValueError):
        admission._validate_description_values(
            {
                name: getattr(replayed_description, name)
                for name in DESCRIPTION_TYPE.__annotations__
            },
            trusted_certificate=certificate,
        )

    hostile_description_sha256 = _TouchBomb()
    hostile_description = _forged(
        description,
        certificate_sha256=hostile_description_sha256,
    )
    with pytest.raises(TypeError):
        admission._validate_description_values(
            {
                name: getattr(hostile_description, name)
                for name in DESCRIPTION_TYPE.__annotations__
            },
            trusted_certificate=certificate,
        )
    assert hostile_description_sha256.calls == 0

    for field in (
        "certificate_sha256",
        "checkpoint48_result_sha256",
        "checkpoint43_applied_decision_sha256",
    ):
        hostile_sha256 = _TouchBomb()
        hostile_result = _forged(result, **{field: hostile_sha256})
        with _observe_owner_operations(checkpoint48, base):
            with pytest.raises(TypeError):
                owner.validate_admission_result(hostile_result)
        assert hostile_sha256.calls == 0

    for malformed_denominator in (
        True,
        1.0,
        _IntSubclass(64 * certificate.full_word_count),
        _TouchBomb(),
    ):
        malformed_result = _forged(
            selected_result,
            selected_uniform_single_preimage_mass_denominator_log2=(
                malformed_denominator
            ),
        )
        with _observe_owner_operations(checkpoint48, base):
            with pytest.raises(TypeError):
                selected_owner.validate_admission_result(malformed_result)
        if isinstance(malformed_denominator, _TouchBomb):
            assert malformed_denominator.calls == 0

    for field in (
        "backend_law_verified",
        "backend_totality_verified",
        "live_initializer_distribution_certified",
        "cp40_initializer_admission_certified",
        "formal_test28_closed",
        "global_uniqueness_certified",
    ):
        plain = _forged(result, **{field: True})
        with _observe_owner_operations(checkpoint48, base):
            with pytest.raises(ValueError):
                owner.validate_admission_result(plain)
        redigested = _redigest_record(
            result,
            admission._result_payload,
            "result_sha256",
            **{field: True},
        )
        with _observe_owner_operations(checkpoint48, base):
            with pytest.raises(ValueError):
                owner.validate_admission_result(redigested)

    for record in (certificate, description, result, owner):
        with pytest.raises(TypeError):
            pickle.dumps(record)
    with pytest.raises(AttributeError):
        owner._certificate = certificate


def test_owner_bound_hostile_nested_parent_and_local_surface_drift_fail_closed(
    owner_bound_evidence,
    monkeypatch,
):
    bound = owner_bound_evidence
    checkpoint48 = bound["checkpoint48"]
    base = bound["evidence"]
    owner = bound["external_owner"]
    result = owner.admit_returned_result(base["first_result"])
    hostile_child = _TouchBomb()
    forged_cp48 = _forged(
        base["first_result"],
        checkpoint47_result=hostile_child,
    )
    forged_result = _forged(result, checkpoint48_result=forged_cp48)
    forged_values = {
        name: getattr(forged_result, name) for name in RESULT_TYPE.__annotations__
    }
    with _observe_owner_operations(checkpoint48, base):
        with pytest.raises((TypeError, ValueError)):
            admission._validate_result_values(
                forged_values,
                trusted_certificate=owner.certificate,
            )
    assert hostile_child.calls == 0

    with _observe_owner_operations(checkpoint48, base):
        with pytest.raises((TypeError, ValueError)):
            owner.validate_admission_result(forged_result)
    assert hostile_child.calls == 0

    for property_name in (
        "certificate",
        "byte_source_execution_owner",
        "assumption_declaration",
    ):
        replacement_getter_calls = []

        def replacement_getter(instance, property_name=property_name):
            del instance
            replacement_getter_calls.append(property_name)
            raise AssertionError("replacement CP49 property getter executed")

        with monkeypatch.context() as patcher:
            patcher.setattr(OWNER_TYPE, property_name, property(replacement_getter))
            with _observe_owner_operations(checkpoint48, base):
                with pytest.raises(ValueError):
                    MATCHING(
                        base["external_owner"],
                        bound["external_declaration"],
                        owner,
                        admission_policy=POLICY,
                        admission_role_sha256=(bound["external_admission_role_sha256"]),
                    )
                with pytest.raises(ValueError):
                    VALIDATE_CERTIFICATE(
                        base["external_owner"],
                        bound["external_declaration"],
                        owner,
                        admission_policy=POLICY,
                        admission_role_sha256=(bound["external_admission_role_sha256"]),
                    )
        assert replacement_getter_calls == []

    with monkeypatch.context() as patcher:
        patcher.setattr(admission, "_make_result", lambda *args: args)
        with _observe_owner_operations(checkpoint48, base):
            with pytest.raises(ValueError):
                owner.describe(901, 902, 903)

    throwaway = CERTIFY(
        base["external_owner"],
        bound["external_declaration"],
        admission_policy=POLICY,
        admission_role_sha256="9" * 64,
    )
    object.__setattr__(throwaway, "_result_validator", lambda *args: None)
    with _observe_owner_operations(checkpoint48, base):
        with pytest.raises(ValueError):
            throwaway.describe(904, 905, 906)
