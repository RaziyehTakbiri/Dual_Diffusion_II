"""Hostile tests for checkpoint-48 byte-source full-capsule execution."""

import ast
from contextlib import contextmanager
from fractions import Fraction
import inspect
from itertools import product
from pathlib import Path
import pickle
import random
import sys
import threading
import types

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="byte-source full-capsule certification requires PyTorch"
)

from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution as execution,
)

checkpoint46 = pytest.importorskip(  # noqa: E402
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "explicit_source_model_contract",
    reason="byte-source full-capsule certification requires the CP46 fixture",
)
checkpoint47 = pytest.importorskip(  # noqa: E402
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "external_full_capsule_execution_adapter",
    reason="byte-source full-capsule certification requires the CP47 contract",
)


POLICY = getattr(
    execution,
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_"
    "CAPSULE_EXECUTION_POLICY",
)
SYSTEM_PROFILE = getattr(
    execution,
    "INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_SYSTEM_OS_URANDOM_OPERATIONAL",
)
EXTERNAL_PROFILE = getattr(
    execution,
    "INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_"
    "UNVERIFIED",
)
CERTIFY = getattr(
    execution,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_"
    "capsule_execution",
)
MATCHING = getattr(
    execution,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_"
    "source_full_capsule_execution",
)
VALIDATE_CERTIFICATE = getattr(
    execution,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_"
    "full_capsule_execution_certificate",
)

CERTIFICATE_TYPE = getattr(
    execution,
    "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate",
)
RESULT_TYPE = getattr(
    execution,
    "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult",
)
OWNER_TYPE = getattr(
    execution,
    "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner",
)
ERROR_TYPE = getattr(
    execution,
    "PluginBridgeCounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionError",
)

SOURCE_INSTANCE_SHA256 = "1" * 64
BYTE_SOURCE_ROLE_SHA256 = "2" * 64
PROVIDER_ROLE_SHA256 = "3" * 64
EXECUTION_ROLE_SHA256 = "4" * 64
MAX_RETIRED_DRAWS = 64

VALID_DRAW_INDEX = 20
SAME_VALUE_DRAW_INDEX = 21
EXCEPTION_DRAW_INDEX = 22
MALFORMED_TYPE_DRAW_INDEX = 23
SHORT_BLOCK_DRAW_INDEX = 24
LONG_BLOCK_DRAW_INDEX = 25
ATOMIC_DRAW_INDEX = 26
REENTRANT_DRAW_INDEX = 27


class _ByteSourceFailure(RuntimeError):
    pass


class _BytesSubclass(bytes):
    pass


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

    def __bytes__(self):
        return self._touched("bytes conversion")

    def __eq__(self, other):
        del other
        return self._touched("equality")

    def __ne__(self, other):
        del other
        return self._touched("inequality")

    def __lt__(self, other):
        del other
        return self._touched("ordering")

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


def _pushforward(law, mapping):
    pushed = {}
    for value, probability in law.items():
        image = mapping[value]
        pushed[image] = pushed.get(image, Fraction(0)) + probability
    return pushed


def _manual_big_endian_word(block):
    assert type(block) is bytes
    assert len(block) == 8
    return sum(value << (8 * (7 - index)) for index, value in enumerate(block))


def _manual_decode(raw_bytes):
    assert type(raw_bytes) is bytes
    assert len(raw_bytes) % 8 == 0
    return tuple(
        _manual_big_endian_word(raw_bytes[offset : offset + 8])
        for offset in range(0, len(raw_bytes), 8)
    )


def _manual_encode(words):
    return b"".join(word.to_bytes(8, "big", signed=False) for word in words)


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


def _forged(record, **updates):
    forged = object.__new__(type(record))
    for name in type(record).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(record, name)))
    return forged


def _operation_codes():
    calls = checkpoint47._operation_codes()
    calls["cp47_execute"] = execution._CP47_OWNER_TYPE.execute.__code__
    calls["cp47_validate_result"] = execution._CP47_OWNER_TYPE.validate_result.__code__
    calls["cp48_acquire"] = execution._acquire_exact_byte_block.__code__
    calls["cp48_decode"] = execution._decode_big_endian_words.__code__
    calls["cp48_system_wrapper"] = execution._system_os_urandom_byte_source.__code__
    return calls


@contextmanager
def _trace_operations():
    codes = _operation_codes()
    calls = {name: 0 for name in codes}

    def profiler(frame, event, arg):
        del arg
        if event == "call":
            for name, code in codes.items():
                if frame.f_code is code:
                    calls[name] += 1
        return profiler

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        yield calls
    finally:
        sys.setprofile(previous)


def test_required_public_surface_profiles_and_owner_signatures_are_exact():
    expected = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_"
        "CAPSULE_EXECUTION_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_"
        "CAPSULE_EXECUTION_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_"
        "CAPSULE_EXECUTION_SCOPE",
        "INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_SYSTEM_OS_URANDOM_OPERATIONAL",
        "INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_"
        "UNVERIFIED",
        "INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILES",
        "INITIAL_TILT_REJECTION_BYTE_SOURCE_BYTE_ORDER",
        "INITIAL_TILT_REJECTION_BYTE_SOURCE_BYTES_PER_WORD",
        "INITIAL_TILT_REJECTION_BYTE_SOURCE_BLOCK_UNIFORM_PRODUCT_LAW_THEOREM",
        "INITIAL_TILT_REJECTION_BYTE_SOURCE_IID_THEOREM",
        "INITIAL_TILT_REJECTION_BYTE_SOURCE_SUCCESS_CONDITIONING_CAVEAT",
        "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate",
        "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult",
        "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner",
        "PluginBridgeCounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionError",
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_"
        "full_capsule_execution",
        "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_"
        "source_full_capsule_execution",
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_"
        "full_capsule_execution_certificate",
    }
    assert set(execution.__all__) == expected
    assert len(execution.__all__) == len(set(execution.__all__)) == 18
    assert CERTIFICATE_TYPE.__name__ in expected
    assert RESULT_TYPE.__name__ in expected
    assert OWNER_TYPE.__name__ in expected
    assert issubclass(ERROR_TYPE, Exception)
    assert execution.INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILES == (
        SYSTEM_PROFILE,
        EXTERNAL_PROFILE,
    )
    assert execution.INITIAL_TILT_REJECTION_BYTE_SOURCE_BYTE_ORDER == "big"
    assert execution.INITIAL_TILT_REJECTION_BYTE_SOURCE_BYTES_PER_WORD == 8

    certify_parameters = tuple(inspect.signature(CERTIFY).parameters)
    assert certify_parameters == (
        "source_model_owner",
        "source_instance_sha256",
        "byte_source_profile",
        "external_byte_source",
        "byte_source_role_sha256",
        "provider_role_sha256",
        "execution_role_sha256",
        "execution_policy",
        "max_retired_draws",
    )
    matching_parameters = tuple(inspect.signature(MATCHING).parameters)
    assert matching_parameters == (
        "source_model_owner",
        "owner",
        *certify_parameters[1:],
    )
    assert tuple(inspect.signature(VALIDATE_CERTIFICATE).parameters) == (
        matching_parameters
    )
    for operation in (CERTIFY, MATCHING, VALIDATE_CERTIFICATE):
        parameters = inspect.signature(operation).parameters
        positional = ("source_model_owner",)
        if operation is not CERTIFY:
            positional += ("owner",)
        for name in positional:
            assert parameters[name].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for name in certify_parameters[1:]:
            assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
            assert parameters[name].default is inspect.Parameter.empty

    assert tuple(inspect.signature(OWNER_TYPE.execute).parameters) == (
        "self",
        "run_id",
        "initialization_index",
        "draw_index",
    )
    assert tuple(inspect.signature(OWNER_TYPE.validate_result).parameters) == (
        "self",
        "result",
    )
    assert tuple(inspect.signature(OWNER_TYPE.ledger_snapshot).parameters) == ("self",)
    assert tuple(inspect.signature(OWNER_TYPE.validate_ledger_snapshot).parameters) == (
        "self",
        "snapshot",
    )
    assert tuple(inspect.signature(OWNER_TYPE.revalidate_live_ancestry).parameters) == (
        "self",
    )
    assert isinstance(OWNER_TYPE.certificate, property)
    assert isinstance(OWNER_TYPE.source_model_owner, property)


def test_certificate_flag_sets_are_exact_disjoint_and_scope_safe():
    positive = {
        "exact_checkpoint47_owner_binding_certified",
        "exact_transitive_checkpoint46_45_44_43_binding_certified",
        "exact_provider_and_backend_identity_binding_certified",
        "system_profile_restricted_to_internal_cached_os_urandom_wrapper_certified",
        "external_profile_restricted_to_exact_caller_callable_certified",
        "exact_three_argument_backend_invocation_certified",
        "backend_invoked_at_most_once_per_provider_boundary_certified",
        "backend_invoked_exactly_once_when_boundary_reached_certified",
        "exact_8l_byte_block_required_certified",
        "fixed_big_endian_manual_codec_bijection_certified",
        "all_exact_byte_contents_accepted_without_filter_certified",
        "no_coercion_retry_filter_fallback_or_replacement_certified",
        "checkpoint47_sole_draw_retirement_authority_certified",
        "checkpoint47_execute_invoked_at_most_once_per_execution_certified",
        "checkpoint47_execute_invoked_exactly_once_when_boundary_reached_certified",
        "exact_raw_bytes_and_words_result_custody_certified",
        "structural_nonreplaying_result_validation_certified",
        "cached_ordinary_binding_boundary_certified",
        "explicit_live_ancestry_revalidation_available",
        "conditional_full_block_uniform_product_law_theorem_recorded",
        "conditional_iid_theorem_recorded",
        "complete_cp48_success_conditioning_caveat_recorded",
        "system_profile_claim_limited_to_operational_api_binding_certified",
    }
    negative = {
        "backend_totality_certified",
        "backend_success_probability_certified",
        "backend_full_block_uniform_law_certified",
        "backend_iid_across_calls_certified",
        "os_urandom_uniform_law_certified",
        "os_urandom_iid_law_certified",
        "physical_entropy_certified",
        "cryptographic_security_certified",
        "backend_cryptographic_authentication_certified",
        "cross_call_value_freshness_certified",
        "distinct_draw_ids_imply_distinct_values_certified",
        "global_cross_owner_cross_process_fork_or_restart_uniqueness_certified",
        "backend_internal_behavior_or_syscall_count_certified",
        "concurrent_or_reentrant_semantic_safety_beyond_checkpoint47_retirement_"
        "certified",
        "unconditional_returned_result_law_certified",
        "semantic_output_tv_lower_bound_certified",
        "adapter_loaded_code_integrity_certified",
        "backend_loaded_code_integrity_certified",
        "runtime_portable",
        "initializer_admissible",
        "path_admissible",
        "sampler_admissible",
        "scientific_claim_promoted",
        "model_quality_claim_promoted",
        "generality_claim_promoted",
        "manuscript_claim_promoted",
        "hostile_same_process_private_state_tamper_resilience_certified",
        "source_instance_digest_authenticates_backend_certified",
        "system_profile_reproducibility_certified",
        "checkpoint46_declared_request_law_realized_certified",
    }
    assert set(execution._CERTIFICATE_POSITIVE_FLAGS) == positive
    assert set(execution._CERTIFICATE_NEGATIVE_FLAGS) == negative
    assert positive.isdisjoint(negative)


def test_manual_big_endian_oracle_boundaries_one_hot_bits_and_order_are_exact():
    boundary_words = (
        0,
        1,
        255,
        256,
        1 << 63,
        (1 << 64) - 1,
        0xAAAAAAAAAAAAAAAA,
        0x5555555555555555,
    )
    raw = _manual_encode(boundary_words)
    assert _manual_decode(raw) == boundary_words
    assert _manual_encode(_manual_decode(raw)) == raw
    assert _manual_decode(raw[::-1]) != boundary_words

    for bit in range(64):
        expected = 1 << bit
        block = expected.to_bytes(8, "big", signed=False)
        assert _manual_big_endian_word(block) == expected


def test_production_big_endian_decode_and_encode_match_independent_oracle():
    words = (
        0,
        1,
        255,
        256,
        1 << 63,
        (1 << 64) - 1,
        0x0102030405060708,
        0xF0E0D0C0B0A09080,
    )
    raw = _manual_encode(words)
    decoded = execution._decode_big_endian_words(raw, word_count=len(words))
    assert decoded == words == _manual_decode(raw)
    assert execution._encode_big_endian_words(decoded) == raw


def test_exhaustive_toy_byte_codec_is_bijective_and_uniform_pushforward_exact():
    for alphabet_size in (2, 4):
        byte_blocks = tuple(product(range(alphabet_size), repeat=2))
        encoded = {
            block: (alphabet_size * block[0] + block[1]) for block in byte_blocks
        }
        assert len(set(encoded.values())) == alphabet_size**2
        assert _pushforward(_uniform(byte_blocks), encoded) == _uniform(
            range(alphabet_size**2)
        )


def test_uniform_byte_marginals_do_not_imply_joint_or_word_uniformity():
    values = tuple(range(4))
    domain = tuple(product(values, repeat=2))
    diagonal = {(value, value): Fraction(1, 4) for value in values}
    for coordinate in (0, 1):
        marginal = {
            value: sum(
                probability
                for block, probability in diagonal.items()
                if block[coordinate] == value
            )
            for value in values
        }
        assert marginal == _uniform(values)
    assert _total_variation(diagonal, _uniform(domain), domain) == Fraction(3, 4)


def test_reused_uniform_block_breaks_cross_call_iid_exactly():
    blocks = tuple(product(range(2), repeat=2))
    joint_domain = tuple(product(blocks, repeat=2))
    reused = {(block, block): Fraction(1, 4) for block in blocks}
    assert _total_variation(reused, _uniform(joint_domain), joint_domain) == Fraction(
        3, 4
    )
    for position in (0, 1):
        marginal = {
            block: sum(
                probability
                for pair, probability in reused.items()
                if pair[position] == block
            )
            for block in blocks
        }
        assert marginal == _uniform(blocks)


def test_success_conditioning_covers_balanced_biased_zero_and_joint_caveats():
    domain = tuple(range(4))
    uniform = _uniform(domain)
    balanced = _conditional_law(uniform, {value: Fraction(1, 2) for value in domain})
    biased = _conditional_law(
        uniform, {value: Fraction(int(value < 2)) for value in domain}
    )
    zero = _conditional_law(uniform, {value: Fraction(0) for value in domain})
    assert balanced == uniform
    assert biased == {0: Fraction(1, 2), 1: Fraction(1, 2)}
    assert _total_variation(biased, uniform, domain) == Fraction(1, 2)
    assert zero is None

    checked = 0
    for raw_weights in product(range(3), repeat=len(domain)):
        weights = {
            value: Fraction(weight, 2) for value, weight in zip(domain, raw_weights)
        }
        conditional = _conditional_law(uniform, weights)
        if conditional is None:
            continue
        assert (conditional == uniform) is (len(set(weights.values())) == 1)
        checked += 1
    assert checked == 3**4 - 1

    pair_domain = tuple(product(range(2), repeat=2))
    pair_uniform = _uniform(pair_domain)
    selected = _conditional_law(
        pair_uniform,
        {pair: Fraction(int(pair[0] == pair[1])) for pair in pair_domain},
    )
    assert selected == {(0, 0): Fraction(1, 2), (1, 1): Fraction(1, 2)}
    assert _total_variation(selected, pair_uniform, pair_domain) == Fraction(1, 2)


def test_lossy_codec_support_and_total_variation_boundary_are_exact():
    domain = tuple(product(range(4), repeat=2))
    uniform = _uniform(domain)
    lossy = {block: block[0] for block in domain}
    pushed = _pushforward(uniform, lossy)
    assert pushed == _uniform(range(4))
    lifted = {(value, 0): probability for value, probability in pushed.items()}
    assert len(lifted) == 4 < len(domain)
    assert _total_variation(lifted, uniform, domain) == Fraction(3, 4)

    for support_size in range(1, 9):
        eight = tuple(range(8))
        supported = _uniform(eight[:support_size])
        assert _total_variation(supported, _uniform(eight), eight) == (
            1 - Fraction(support_size, len(eight))
        )


def test_every_toy_bijection_preserves_uniformity_exactly():
    domain = tuple(range(4))
    uniform = _uniform(domain)
    checked = 0
    for images in product(domain, repeat=len(domain)):
        if len(set(images)) != len(domain):
            continue
        mapping = dict(zip(domain, images))
        inverse = {value: key for key, value in mapping.items()}
        assert _pushforward(uniform, mapping) == uniform
        assert all(inverse[mapping[value]] == value for value in domain)
        checked += 1
    assert checked == 24


def test_production_codec_accepts_every_byte_value_without_filtering():
    raw = bytes(range(256))
    words = execution._decode_big_endian_words(raw, word_count=32)
    assert words == _manual_decode(raw)
    assert execution._encode_big_endian_words(words) == raw


def test_big_endian_word_encoder_rejects_malformed_words_without_coercion():
    cases = (
        ([], TypeError),
        (iter((0,)), TypeError),
        ((False,), TypeError),
        ((np.int64(0),), TypeError),
        ((0.0,), TypeError),
        ((-1,), ValueError),
        (((1 << 64),), ValueError),
    )
    for words, error_type in cases:
        with pytest.raises(error_type):
            execution._encode_big_endian_words(words)

    bomb = _TouchBomb()
    with pytest.raises(TypeError):
        execution._encode_big_endian_words((bomb,))
    assert bomb.calls == 0


def test_noncallable_backend_refuses_before_hostile_interaction():
    bomb = _TouchBomb()
    with pytest.raises(TypeError):
        execution._acquire_exact_byte_block(
            bomb,
            source_instance_sha256=SOURCE_INSTANCE_SHA256,
            draw_index=VALID_DRAW_INDEX,
            byte_count=8,
        )
    assert bomb.calls == 0


def test_exact_byte_block_preserves_identity_and_requires_exact_type_and_length():
    raw = bytes(range(24))
    assert (
        execution._exact_byte_block(raw, name="raw_bytes", byte_count=len(raw)) is raw
    )
    invalid = (
        (bytearray(raw), TypeError),
        (memoryview(raw), TypeError),
        (list(raw), TypeError),
        (iter(raw), TypeError),
        (_BytesSubclass(raw), TypeError),
        (raw[:-1], ValueError),
        (raw + b"\x00", ValueError),
    )
    for value, error_type in invalid:
        with pytest.raises(error_type):
            execution._exact_byte_block(
                value,
                name="raw_bytes",
                byte_count=len(raw),
            )


def test_exact_byte_block_and_scalar_preflight_do_not_coerce_hostile_values():
    block = _TouchBomb()
    with pytest.raises(TypeError):
        execution._exact_byte_block(block, name="raw_bytes", byte_count=8)
    assert block.calls == 0

    for name in ("draw_index", "full_word_count"):
        scalar = _TouchBomb()
        with pytest.raises(TypeError):
            execution._exact_uint64(scalar, name=name)
        assert scalar.calls == 0


def test_acquire_exact_byte_block_calls_backend_once_with_exact_three_arguments():
    calls = []
    expected = bytes(range(24))

    def backend(source_instance_sha256, draw_index, byte_count):
        calls.append((source_instance_sha256, draw_index, byte_count))
        return expected

    returned = execution._acquire_exact_byte_block(
        backend,
        source_instance_sha256=SOURCE_INSTANCE_SHA256,
        draw_index=VALID_DRAW_INDEX,
        byte_count=len(expected),
    )
    assert returned is expected
    assert calls == [(SOURCE_INSTANCE_SHA256, VALID_DRAW_INDEX, len(expected))]


def test_backend_exception_propagates_by_identity_once_without_retry():
    calls = []
    failure = _ByteSourceFailure("one backend refusal")

    def backend(source_instance_sha256, draw_index, byte_count):
        calls.append((source_instance_sha256, draw_index, byte_count))
        raise failure

    with pytest.raises(_ByteSourceFailure) as captured:
        execution._acquire_exact_byte_block(
            backend,
            source_instance_sha256=SOURCE_INSTANCE_SHA256,
            draw_index=EXCEPTION_DRAW_INDEX,
            byte_count=24,
        )
    assert captured.value is failure
    assert calls == [(SOURCE_INSTANCE_SHA256, EXCEPTION_DRAW_INDEX, 24)]


def test_backend_wrong_exact_type_and_length_call_once_without_retry_or_decode():
    expected = bytes(range(24))
    cases = (
        bytearray(expected),
        memoryview(expected),
        list(expected),
        _BytesSubclass(expected),
        expected[:-1],
        expected + b"\x00",
    )
    for offset, returned in enumerate(cases):
        calls = []

        def backend(source_instance_sha256, draw_index, byte_count):
            calls.append((source_instance_sha256, draw_index, byte_count))
            return returned

        error_type = ValueError if type(returned) is bytes else TypeError
        with pytest.raises(error_type):
            execution._acquire_exact_byte_block(
                backend,
                source_instance_sha256=SOURCE_INSTANCE_SHA256,
                draw_index=40 + offset,
                byte_count=len(expected),
            )
        assert calls == [(SOURCE_INSTANCE_SHA256, 40 + offset, len(expected))]


def test_backend_hostile_return_is_not_coerced_or_touched():
    bomb = _TouchBomb()
    calls = []

    def backend(source_instance_sha256, draw_index, byte_count):
        calls.append((source_instance_sha256, draw_index, byte_count))
        return bomb

    with pytest.raises(TypeError):
        execution._acquire_exact_byte_block(
            backend,
            source_instance_sha256=SOURCE_INSTANCE_SHA256,
            draw_index=VALID_DRAW_INDEX,
            byte_count=8,
        )
    assert calls == [(SOURCE_INSTANCE_SHA256, VALID_DRAW_INDEX, 8)]
    assert bomb.calls == 0


def test_repeated_direct_acquisition_has_no_cache_and_equal_values_are_legal():
    calls = []
    raw = bytes(range(16))

    def backend(source_instance_sha256, draw_index, byte_count):
        calls.append((source_instance_sha256, draw_index, byte_count))
        return raw

    first = execution._acquire_exact_byte_block(
        backend,
        source_instance_sha256=SOURCE_INSTANCE_SHA256,
        draw_index=VALID_DRAW_INDEX,
        byte_count=len(raw),
    )
    second = execution._acquire_exact_byte_block(
        backend,
        source_instance_sha256=SOURCE_INSTANCE_SHA256,
        draw_index=SAME_VALUE_DRAW_INDEX,
        byte_count=len(raw),
    )
    assert first is second is raw
    assert calls == [
        (SOURCE_INSTANCE_SHA256, VALID_DRAW_INDEX, len(raw)),
        (SOURCE_INSTANCE_SHA256, SAME_VALUE_DRAW_INDEX, len(raw)),
    ]


def test_private_provider_discards_unreturnable_custody_without_retry():
    calls = []
    raw = bytes(range(16))

    def backend(source_instance_sha256, draw_index, byte_count):
        calls.append((source_instance_sha256, draw_index, byte_count))
        return raw

    provider = execution._PrivateFullCapsuleProvider(
        SOURCE_INSTANCE_SHA256,
        EXTERNAL_PROFILE,
        backend,
        _construction_token=execution._PROVIDER_TOKEN,
    )
    outer_token = provider._begin(VALID_DRAW_INDEX)
    words = provider(SOURCE_INSTANCE_SHA256, VALID_DRAW_INDEX, 2)
    assert words == _manual_decode(raw)
    assert len(provider._acquisitions) == 1
    nested_token = provider._begin(VALID_DRAW_INDEX)
    provider._discard(nested_token)
    provider._end(nested_token)
    assert len(provider._acquisitions) == 1
    assert (
        provider._claim(
            outer_token,
            SOURCE_INSTANCE_SHA256,
            VALID_DRAW_INDEX,
            words,
        )
        is raw
    )
    provider._end(outer_token)
    assert provider._acquisitions == {}

    cleanup_token = provider._begin(SAME_VALUE_DRAW_INDEX)
    assert provider(SOURCE_INSTANCE_SHA256, SAME_VALUE_DRAW_INDEX, 2) == words
    provider._discard(cleanup_token)
    provider._end(cleanup_token)
    assert provider._acquisitions == {}
    assert calls == [
        (SOURCE_INSTANCE_SHA256, VALID_DRAW_INDEX, len(raw)),
        (SOURCE_INSTANCE_SHA256, SAME_VALUE_DRAW_INDEX, len(raw)),
    ]


def test_private_provider_begin_failure_removes_its_thread_context(monkeypatch):
    provider = execution._PrivateFullCapsuleProvider(
        SOURCE_INSTANCE_SHA256,
        EXTERNAL_PROFILE,
        lambda source_instance_sha256, draw_index, byte_count: bytes(byte_count),
        _construction_token=execution._PROVIDER_TOKEN,
    )
    original = execution._PrivateFullCapsuleProvider._require_binding
    marker = RuntimeError("post-append binding failure")
    calls = 0

    def fail_after_append(self):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise marker
        return original(self)

    monkeypatch.setattr(
        execution._PrivateFullCapsuleProvider,
        "_require_binding",
        fail_after_append,
    )
    with pytest.raises(RuntimeError) as caught:
        provider._begin(VALID_DRAW_INDEX)
    assert caught.value is marker
    assert calls == 2
    assert not hasattr(provider._thread_context, "cp48_stack")
    assert provider._acquisitions == {}


def test_private_provider_tokens_isolate_concurrent_same_draw_contexts():
    backend_barrier = threading.Barrier(2)
    calls = []
    outcomes = []
    raw = bytes(range(16))

    def backend(source_instance_sha256, draw_index, byte_count):
        calls.append((source_instance_sha256, draw_index, byte_count))
        backend_barrier.wait(timeout=10)
        return raw

    provider = execution._PrivateFullCapsuleProvider(
        SOURCE_INSTANCE_SHA256,
        EXTERNAL_PROFILE,
        backend,
        _construction_token=execution._PROVIDER_TOKEN,
    )

    def acquire_and_claim():
        token = provider._begin(VALID_DRAW_INDEX)
        try:
            words = provider(SOURCE_INSTANCE_SHA256, VALID_DRAW_INDEX, 2)
            outcomes.append(
                provider._claim(
                    token,
                    SOURCE_INSTANCE_SHA256,
                    VALID_DRAW_INDEX,
                    words,
                )
            )
        finally:
            provider._discard(token)
            provider._end(token)

    threads = tuple(threading.Thread(target=acquire_and_claim) for _ in range(2))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)
        assert not thread.is_alive()
    assert outcomes == [raw, raw]
    assert calls == [
        (SOURCE_INSTANCE_SHA256, VALID_DRAW_INDEX, len(raw)),
        (SOURCE_INSTANCE_SHA256, VALID_DRAW_INDEX, len(raw)),
    ]
    assert provider._acquisitions == {}


def test_fixed_system_wrapper_calls_cached_os_urandom_once_and_only_checks_shape(
    monkeypatch,
):
    calls = []
    raw = bytes(range(24))

    def replacement(byte_count):
        calls.append(byte_count)
        return raw

    before = _rng_snapshot()
    monkeypatch.setattr(execution, "_OS_URANDOM", replacement)
    returned = execution._system_os_urandom_byte_source(
        SOURCE_INSTANCE_SHA256,
        VALID_DRAW_INDEX,
        len(raw),
    )
    assert returned is raw
    assert calls == [len(raw)]
    _assert_rng_unchanged(before)


def test_codec_and_acquisition_reject_exact_bool_numpy_and_range_boundaries():
    raw = bytes(range(8))
    for value, error_type in (
        (True, TypeError),
        (np.int64(1), TypeError),
        (-1, ValueError),
        (1 << 64, ValueError),
    ):
        with pytest.raises(error_type):
            execution._exact_uint64(value, name="draw_index")

    with pytest.raises(TypeError):
        execution._decode_big_endian_words(raw, word_count=True)
    with pytest.raises(TypeError):
        execution._decode_big_endian_words(raw, word_count=np.int64(1))
    with pytest.raises(ValueError):
        execution._decode_big_endian_words(raw, word_count=0)
    with pytest.raises(ValueError):
        execution._decode_big_endian_words(raw, word_count=2)


def test_record_types_and_private_constructors_are_statically_sealed():
    for record_type in (CERTIFICATE_TYPE, RESULT_TYPE):
        with pytest.raises(TypeError):
            type("ForbiddenSubclass", (record_type,), {})
        values = {name: None for name in record_type.__annotations__}
        with pytest.raises(TypeError):
            record_type(_construction_token=object(), **values)
    with pytest.raises(TypeError):
        type("ForbiddenOwnerSubclass", (OWNER_TYPE,), {})


def test_transitive_local_surfaces_and_runtime_fingerprint_changes_are_detected():
    frozen = dict(execution._FROZEN_LOCAL_SURFACES)
    for name in (
        "_OS_URANDOM",
        "_SHA256",
        "_MARSHAL_DUMPS",
        "_CODE_FINGERPRINT_FORMAT",
        "_exact_byte_block",
        "_acquire_exact_byte_block",
        "_decode_big_endian_words",
        "_encode_big_endian_words",
        "_PrivateFullCapsuleProvider",
    ):
        assert frozen[name] is getattr(execution, name)

    def returns_one():
        return 1

    constants = tuple(
        2 if value == 1 else value for value in returns_one.__code__.co_consts
    )
    changed = types.FunctionType(
        returns_one.__code__.replace(co_consts=constants),
        returns_one.__globals__,
    )
    assert returns_one() == 1
    assert changed() == 2
    assert execution._code_sha256(returns_one) != execution._code_sha256(changed)

    def returns_none():
        return None

    late_text = "".join(("cp48 late ", "interning regression ", "payload 931742"))
    late_code = returns_none.__code__.replace(co_consts=(None, late_text))
    late_function = types.FunctionType(late_code, returns_none.__globals__)
    digest = execution._code_sha256(late_function)
    assert sys.intern(late_text) is late_text
    assert execution._code_sha256(late_function) == digest


def test_source_ast_has_one_os_call_site_no_retry_and_no_domain_dependency():
    source_path = Path(execution.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots.isdisjoint(
        {
            "random",
            "secrets",
            "numpy",
            "torch",
            "mido",
            "librosa",
            "music21",
        }
    )

    call_text = tuple(
        ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)
    )
    assert call_text.count("_OS_URANDOM") == 1
    assert all(
        fragment not in call
        for call in call_text
        for fragment in (
            "os.getrandom",
            "os.getentropy",
            "secrets.",
            "numpy.random",
            "np.random",
            "torch.random",
        )
    )

    system_wrapper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_system_os_urandom_byte_source"
    )
    wrapper_calls = tuple(
        ast.unparse(node.func)
        for node in ast.walk(system_wrapper)
        if isinstance(node, ast.Call)
    )
    assert wrapper_calls == ("_OS_URANDOM",)

    provider_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "_PrivateFullCapsuleProvider"
    )
    provider_call = next(
        node
        for node in provider_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "__call__"
    )
    assert not any(
        isinstance(node, (ast.For, ast.While)) for node in ast.walk(provider_call)
    )
    provider_calls = tuple(
        ast.unparse(node.func)
        for node in ast.walk(provider_call)
        if isinstance(node, ast.Call)
    )
    assert provider_calls.count("_acquire_exact_byte_block") == 1
    assert provider_calls.count("_decode_big_endian_words") == 1

    owner_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name
        == "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner"
    )
    owner_execute = next(
        node
        for node in owner_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "execute"
    )
    exception_handlers = tuple(
        node for node in ast.walk(owner_execute) if isinstance(node, ast.ExceptHandler)
    )
    assert len(exception_handlers) == 1
    assert ast.unparse(exception_handlers[0].type) == "BaseException"
    execute_calls = tuple(
        ast.unparse(node.func)
        for node in ast.walk(owner_execute)
        if isinstance(node, ast.Call)
    )
    assert execute_calls.count("self._provider._begin") == 1
    assert execute_calls.count("self._provider._discard") == 1
    assert execute_calls.count("self._provider._end") == 1


@pytest.fixture(scope="module")
def owner_bound_evidence():
    source_support_owner = checkpoint46.source_support_owner.__wrapped__()
    source_model_owner = checkpoint46.CERTIFY(
        source_support_owner,
        source_model_policy=checkpoint46.POLICY,
        source_model_role_sha256=checkpoint46.ROLE,
    )

    backend_calls = []
    backend_failure = _ByteSourceFailure("backend refused this retired draw")
    atomic_backend_failure = _ByteSourceFailure(
        "race winner stopped after the sole backend boundary"
    )
    atomic_backend_entered = threading.Event()
    atomic_backend_release = threading.Event()
    atomic_outcome_ready = threading.Event()
    race_barrier_timeout_seconds = 300
    race_phase_timeout_seconds = 900
    owner_holder = {}
    reentrant_errors = []
    reentrant_attempted = set()

    def canonical_raw(byte_count):
        pattern = bytes(
            (
                0,
                1,
                255,
                2,
                254,
                0xAA,
                0x55,
                0x80,
                0x7F,
                0x10,
                0x20,
                0x40,
            )
        )
        return bytes(pattern[index % len(pattern)] for index in range(byte_count))

    def external_byte_source(source_instance_sha256, draw_index, byte_count):
        backend_calls.append((source_instance_sha256, draw_index, byte_count))
        raw = canonical_raw(byte_count)
        if draw_index == EXCEPTION_DRAW_INDEX:
            raise backend_failure
        if draw_index == ATOMIC_DRAW_INDEX:
            atomic_backend_entered.set()
            if not atomic_backend_release.wait(
                timeout=race_phase_timeout_seconds + 120
            ):
                raise AssertionError("race winner backend was not released")
            raise atomic_backend_failure
        if draw_index == MALFORMED_TYPE_DRAW_INDEX:
            return bytearray(raw)
        if draw_index == SHORT_BLOCK_DRAW_INDEX:
            return raw[:-1]
        if draw_index == LONG_BLOCK_DRAW_INDEX:
            return raw + b"\x00"
        if draw_index == REENTRANT_DRAW_INDEX and draw_index not in reentrant_attempted:
            reentrant_attempted.add(draw_index)
            try:
                owner_holder["external_owner"].execute(106, 206, draw_index)
            except Exception as error:  # exact type is asserted below
                reentrant_errors.append(error)
            else:
                raise AssertionError("same-draw reentry unexpectedly returned")
        return raw

    before = _rng_snapshot()
    with _trace_operations() as external_certification_calls:
        external_owner = CERTIFY(
            source_model_owner,
            source_instance_sha256=SOURCE_INSTANCE_SHA256,
            byte_source_profile=EXTERNAL_PROFILE,
            external_byte_source=external_byte_source,
            byte_source_role_sha256=BYTE_SOURCE_ROLE_SHA256,
            provider_role_sha256=PROVIDER_ROLE_SHA256,
            execution_role_sha256=EXECUTION_ROLE_SHA256,
            execution_policy=POLICY,
            max_retired_draws=MAX_RETIRED_DRAWS,
        )
    owner_holder["external_owner"] = external_owner

    with _trace_operations() as system_certification_calls:
        system_owner = CERTIFY(
            source_model_owner,
            source_instance_sha256="5" * 64,
            byte_source_profile=SYSTEM_PROFILE,
            external_byte_source=None,
            byte_source_role_sha256="6" * 64,
            provider_role_sha256="7" * 64,
            execution_role_sha256="8" * 64,
            execution_policy=POLICY,
            max_retired_draws=MAX_RETIRED_DRAWS,
        )

    with _trace_operations() as valid_calls:
        first_result = external_owner.execute(101, 201, VALID_DRAW_INDEX)
    first_snapshot = external_owner.ledger_snapshot()

    with _trace_operations() as same_value_calls:
        same_value_result = external_owner.execute(
            102,
            202,
            SAME_VALUE_DRAW_INDEX,
        )

    before_duplicate_backend_calls = len(backend_calls)
    with _trace_operations() as duplicate_calls:
        with pytest.raises(Exception) as duplicate_info:
            external_owner.execute(999, 998, VALID_DRAW_INDEX)
    assert len(backend_calls) == before_duplicate_backend_calls

    with _trace_operations() as exception_calls:
        with pytest.raises(_ByteSourceFailure) as exception_info:
            external_owner.execute(103, 203, EXCEPTION_DRAW_INDEX)

    with _trace_operations() as malformed_type_calls:
        with pytest.raises(TypeError) as malformed_type_info:
            external_owner.execute(104, 204, MALFORMED_TYPE_DRAW_INDEX)

    with _trace_operations() as short_calls:
        with pytest.raises(ValueError) as short_info:
            external_owner.execute(105, 205, SHORT_BLOCK_DRAW_INDEX)

    with _trace_operations() as long_calls:
        with pytest.raises(ValueError) as long_info:
            external_owner.execute(106, 206, LONG_BLOCK_DRAW_INDEX)

    with _trace_operations() as reentrant_calls:
        reentrant_result = external_owner.execute(107, 207, REENTRANT_DRAW_INDEX)
    reentrant_context_cleanup = not hasattr(
        external_owner._provider._thread_context,
        "cp48_stack",
    )
    reentrant_acquisitions_empty = external_owner._provider._acquisitions == {}

    barrier = threading.Barrier(3)
    atomic_outcomes = []
    atomic_context_cleanup = []

    def execute_same_draw():
        try:
            barrier.wait(timeout=race_barrier_timeout_seconds)
            try:
                result = external_owner.execute(108, 208, ATOMIC_DRAW_INDEX)
            except Exception as error:  # exact type is asserted below
                atomic_outcomes.append(("error", error))
            else:
                atomic_outcomes.append(("result", result))
        finally:
            atomic_context_cleanup.append(
                not hasattr(
                    external_owner._provider._thread_context,
                    "cp48_stack",
                )
            )
            atomic_outcome_ready.set()

    threads = tuple(threading.Thread(target=execute_same_draw) for _ in range(2))
    before_race_backend_calls = len(backend_calls)
    for thread in threads:
        thread.start()
    backend_was_entered = False
    duplicate_was_observed = False
    try:
        barrier.wait(timeout=race_barrier_timeout_seconds)
        backend_was_entered = atomic_backend_entered.wait(
            timeout=race_phase_timeout_seconds
        )
        if backend_was_entered:
            duplicate_was_observed = atomic_outcome_ready.wait(
                timeout=race_phase_timeout_seconds
            )
    finally:
        atomic_backend_release.set()
    for thread in threads:
        thread.join(timeout=race_barrier_timeout_seconds)
        assert not thread.is_alive()
    assert backend_was_entered
    assert duplicate_was_observed
    assert len(atomic_context_cleanup) == 2
    assert all(cleaned is True for cleaned in atomic_context_cleanup)
    assert external_owner._provider._acquisitions == {}
    race_backend_call_count = len(backend_calls) - before_race_backend_calls

    with _trace_operations() as result_validation_calls:
        assert external_owner.validate_result(first_result) is first_result
        assert external_owner.validate_result(same_value_result) is same_value_result

    final_snapshot = external_owner.ledger_snapshot()
    with _trace_operations() as snapshot_validation_calls:
        assert external_owner.validate_ledger_snapshot(final_snapshot) is final_snapshot
    with pytest.raises(ValueError) as stale_snapshot_info:
        external_owner.validate_ledger_snapshot(first_snapshot)

    with _trace_operations() as system_execution_calls:
        system_result = system_owner.execute(501, 601, 50)
    system_snapshot = system_owner.ledger_snapshot()
    _assert_rng_unchanged(before)

    return {
        "source_support_owner": source_support_owner,
        "source_model_owner": source_model_owner,
        "external_owner": external_owner,
        "system_owner": system_owner,
        "external_byte_source": external_byte_source,
        "backend_calls": backend_calls,
        "backend_failure": backend_failure,
        "atomic_backend_failure": atomic_backend_failure,
        "first_result": first_result,
        "same_value_result": same_value_result,
        "reentrant_result": reentrant_result,
        "system_result": system_result,
        "first_snapshot": first_snapshot,
        "final_snapshot": final_snapshot,
        "system_snapshot": system_snapshot,
        "duplicate_error": duplicate_info.value,
        "exception_error": exception_info.value,
        "malformed_type_error": malformed_type_info.value,
        "short_error": short_info.value,
        "long_error": long_info.value,
        "stale_snapshot_error": stale_snapshot_info.value,
        "reentrant_errors": tuple(reentrant_errors),
        "reentrant_context_cleanup": reentrant_context_cleanup,
        "reentrant_acquisitions_empty": reentrant_acquisitions_empty,
        "atomic_outcomes": tuple(atomic_outcomes),
        "atomic_context_cleanup": tuple(atomic_context_cleanup),
        "race_backend_call_count": race_backend_call_count,
        "external_certification_calls": external_certification_calls,
        "system_certification_calls": system_certification_calls,
        "valid_calls": valid_calls,
        "same_value_calls": same_value_calls,
        "duplicate_calls": duplicate_calls,
        "exception_calls": exception_calls,
        "malformed_type_calls": malformed_type_calls,
        "short_calls": short_calls,
        "long_calls": long_calls,
        "reentrant_calls": reentrant_calls,
        "result_validation_calls": result_validation_calls,
        "snapshot_validation_calls": snapshot_validation_calls,
        "system_execution_calls": system_execution_calls,
    }


def test_owner_bound_certificate_ancestry_profiles_flags_and_nonclaims(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    external_owner = evidence["external_owner"]
    system_owner = evidence["system_owner"]
    assert external_owner.source_model_owner is evidence["source_model_owner"]
    assert system_owner.source_model_owner is evidence["source_model_owner"]

    external = external_owner.certificate
    system = system_owner.certificate
    assert external.byte_source_profile == EXTERNAL_PROFILE
    assert external.external_profile_selected is True
    assert external.system_profile_selected is False
    assert system.byte_source_profile == SYSTEM_PROFILE
    assert system.system_profile_selected is True
    assert system.external_profile_selected is False
    assert external.source_instance_sha256 == SOURCE_INSTANCE_SHA256
    assert external.byte_source_role_sha256 == BYTE_SOURCE_ROLE_SHA256
    assert external.provider_role_sha256 == PROVIDER_ROLE_SHA256
    assert external.execution_role_sha256 == EXECUTION_ROLE_SHA256
    assert external.max_retired_draws == MAX_RETIRED_DRAWS
    assert external.raw_byte_count == 8 * external.full_word_count
    assert external.passed is system.passed is True
    for certificate in (external, system):
        for name in execution._CERTIFICATE_POSITIVE_FLAGS:
            assert getattr(certificate, name) is True
        for name in execution._CERTIFICATE_NEGATIVE_FLAGS:
            assert getattr(certificate, name) is False


def test_owner_bound_exact_execution_and_validation_call_budgets(owner_bound_evidence):
    evidence = owner_bound_evidence
    certification_forbidden = (
        "cp47_execute",
        "cp48_acquire",
        "cp48_decode",
        "cp48_system_wrapper",
        "cp43_combined",
        "cp43_g",
        "cp43_semantic_h",
    )
    for key in ("external_certification_calls", "system_certification_calls"):
        calls = evidence[key]
        assert all(calls[name] == 0 for name in certification_forbidden)
        assert calls["cp46_live_revalidation"] == 1

    for key in ("valid_calls", "same_value_calls", "reentrant_calls"):
        calls = evidence[key]
        assert calls["cp47_execute"] >= 1
        assert calls["cp48_acquire"] == 1
        assert calls["cp48_decode"] == 1
        assert calls["cp48_system_wrapper"] == 0
        assert calls["cp43_combined"] == 1
        assert calls["cp43_g"] == 1
        assert calls["cp43_semantic_h"] == 1

    system = evidence["system_execution_calls"]
    assert system["cp47_execute"] == 1
    assert system["cp48_acquire"] == 1
    assert system["cp48_decode"] == 1
    assert system["cp48_system_wrapper"] == 1
    assert system["cp43_combined"] == 1

    validation = evidence["result_validation_calls"]
    assert validation["cp47_validate_result"] == 2
    assert validation["cp47_execute"] == 0
    assert validation["cp48_acquire"] == 0
    assert validation["cp48_decode"] == 0
    assert validation["cp43_combined"] == 0
    snapshot = evidence["snapshot_validation_calls"]
    assert snapshot["cp47_execute"] == 0
    assert snapshot["cp48_acquire"] == 0
    assert snapshot["cp48_decode"] == 0
    assert snapshot["cp43_combined"] == 0


def test_owner_bound_raw_bytes_words_and_cp47_custody_are_exact(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    first = evidence["first_result"]
    second = evidence["same_value_result"]
    reentrant = evidence["reentrant_result"]
    assert type(first) is type(second) is type(reentrant) is RESULT_TYPE
    assert first.raw_bytes == second.raw_bytes == reentrant.raw_bytes
    assert first.source_full_words == second.source_full_words
    assert first.draw_index == VALID_DRAW_INDEX
    assert second.draw_index == SAME_VALUE_DRAW_INDEX
    for result in (first, second, reentrant):
        assert result.source_full_words == _manual_decode(result.raw_bytes)
        assert _manual_encode(result.source_full_words) == result.raw_bytes
        assert result.raw_byte_count == 8 * len(result.source_full_words)
        assert result.backend_invocation_count == 1
        assert result.checkpoint47_execute_invocation_count == 1
        assert result.exact_raw_bytes_reconstructed_from_words is True
        assert result.fixed_big_endian_round_trip_certified is True
        assert result.structural_validation_is_nonreplaying is True
        cp47 = result.checkpoint47_result
        assert cp47.source_full_words == result.source_full_words
        assert cp47.draw_index == result.draw_index
        assert cp47.retirement_ordinal == result.retirement_ordinal
        assert cp47.retirement_chain_sha256 == result.retirement_chain_sha256
        assert (
            cp47.provider_receipt.receipt_sha256
            == result.checkpoint47_provider_receipt_sha256
        )


def test_owner_bound_failures_burn_draws_duplicate_and_backend_never_retries(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    assert evidence["exception_error"] is evidence["backend_failure"]
    assert type(evidence["malformed_type_error"]) is TypeError
    assert type(evidence["short_error"]) is ValueError
    assert type(evidence["long_error"]) is ValueError
    assert type(evidence["duplicate_error"]) is checkpoint47.ERROR_TYPE
    assert evidence["duplicate_error"].args == ("CP47 draw_index is already retired",)

    backend_draws = tuple(call[1] for call in evidence["backend_calls"])
    assert backend_draws.count(VALID_DRAW_INDEX) == 1
    assert backend_draws.count(SAME_VALUE_DRAW_INDEX) == 1
    assert backend_draws.count(EXCEPTION_DRAW_INDEX) == 1
    assert backend_draws.count(MALFORMED_TYPE_DRAW_INDEX) == 1
    assert backend_draws.count(SHORT_BLOCK_DRAW_INDEX) == 1
    assert backend_draws.count(LONG_BLOCK_DRAW_INDEX) == 1
    assert backend_draws.count(REENTRANT_DRAW_INDEX) == 1
    assert backend_draws.count(ATOMIC_DRAW_INDEX) == 1

    for key in (
        "duplicate_calls",
        "exception_calls",
        "malformed_type_calls",
        "short_calls",
        "long_calls",
    ):
        calls = evidence[key]
        assert calls["cp43_combined"] == 0
        assert calls["cp43_g"] == 0
        assert calls["cp43_semantic_h"] == 0
    assert evidence["duplicate_calls"]["cp48_acquire"] == 0
    assert evidence["exception_calls"]["cp48_acquire"] == 1
    assert evidence["exception_calls"]["cp48_decode"] == 0
    for key in ("malformed_type_calls", "short_calls", "long_calls"):
        assert evidence[key]["cp48_acquire"] == 1
        assert evidence[key]["cp48_decode"] == 0

    final = evidence["final_snapshot"]
    assert final.retired_draw_count == 8
    assert tuple(row[3] for row in final.retired_draw_rows) == (
        VALID_DRAW_INDEX,
        SAME_VALUE_DRAW_INDEX,
        EXCEPTION_DRAW_INDEX,
        MALFORMED_TYPE_DRAW_INDEX,
        SHORT_BLOCK_DRAW_INDEX,
        LONG_BLOCK_DRAW_INDEX,
        REENTRANT_DRAW_INDEX,
        ATOMIC_DRAW_INDEX,
    )
    assert type(evidence["stale_snapshot_error"]) is ValueError


def test_owner_bound_same_draw_race_and_reentry_have_one_backend_boundary(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    assert evidence["race_backend_call_count"] == 1
    outcomes = evidence["atomic_outcomes"]
    assert len(outcomes) == 2
    results = tuple(value for status, value in outcomes if status == "result")
    errors = tuple(value for status, value in outcomes if status == "error")
    assert results == ()
    assert len(errors) == 2
    marker = evidence["atomic_backend_failure"]
    assert sum(error is marker for error in errors) == 1
    duplicate_errors = tuple(error for error in errors if error is not marker)
    assert len(duplicate_errors) == 1
    assert type(duplicate_errors[0]) is checkpoint47.ERROR_TYPE
    assert duplicate_errors[0].args == ("CP47 draw_index is already retired",)
    assert evidence["atomic_context_cleanup"] == (True, True)
    assert evidence["external_owner"]._provider._acquisitions == {}
    assert len(evidence["reentrant_errors"]) == 1
    assert type(evidence["reentrant_errors"][0]) is checkpoint47.ERROR_TYPE
    assert evidence["reentrant_errors"][0].args == (
        "CP47 draw_index is already retired",
    )
    assert evidence["reentrant_context_cleanup"] is True
    assert evidence["reentrant_acquisitions_empty"] is True
    assert (
        evidence[
            "external_owner"
        ].certificate.concurrent_or_reentrant_semantic_safety_beyond_checkpoint47_retirement_certified
        is False
    )


def test_owner_bound_system_os_urandom_profile_has_shape_roundtrip_only(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    result = evidence["system_result"]
    certificate = evidence["system_owner"].certificate
    assert type(result) is RESULT_TYPE
    assert type(result.raw_bytes) is bytes
    assert len(result.raw_bytes) == result.raw_byte_count
    assert result.raw_byte_count == 8 * certificate.full_word_count
    assert result.source_full_words == _manual_decode(result.raw_bytes)
    assert _manual_encode(result.source_full_words) == result.raw_bytes
    assert result.checkpoint47_result.source_full_words == result.source_full_words
    assert evidence["system_snapshot"].retired_draw_count == 1
    assert certificate.system_profile_selected is True
    assert certificate.os_urandom_uniform_law_certified is False
    assert certificate.os_urandom_iid_law_certified is False
    assert certificate.physical_entropy_certified is False
    assert certificate.cryptographic_security_certified is False
    assert certificate.system_profile_reproducibility_certified is False


def test_owner_bound_records_owner_tamper_and_cross_owner_splice_refuse_without_replay(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    external_owner = evidence["external_owner"]
    system_owner = evidence["system_owner"]
    result = evidence["first_result"]
    records = (external_owner.certificate, result)
    for record in records:
        field = next(iter(type(record).__annotations__))
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, field, getattr(record, field))
        with pytest.raises(TypeError):
            pickle.dumps(record)
        with pytest.raises(TypeError):
            type(record)(
                _construction_token=object(),
                **{
                    name: getattr(record, name) for name in type(record).__annotations__
                },
            )
    with pytest.raises(AttributeError):
        external_owner._certificate = external_owner.certificate
    with pytest.raises(TypeError):
        pickle.dumps(external_owner)

    changed_raw = bytes([result.raw_bytes[0] ^ 1]) + result.raw_bytes[1:]
    tampered = _forged(result, raw_bytes=changed_raw)
    with pytest.raises(ValueError):
        external_owner.validate_result(tampered)
    values = {name: getattr(tampered, name) for name in type(tampered).__annotations__}
    redigested = _forged(
        tampered,
        result_sha256=execution._semantic_digest(execution._result_payload(values)),
    )
    with pytest.raises(ValueError):
        external_owner.validate_result(redigested)

    nonexact_count = _forged(
        result,
        raw_byte_count=_IntSubclass(result.raw_byte_count),
    )
    with pytest.raises(TypeError):
        external_owner.validate_result(nonexact_count)
    hostile_count = _TouchBomb()
    with pytest.raises(TypeError):
        external_owner.validate_result(_forged(result, raw_byte_count=hostile_count))
    assert hostile_count.calls == 0

    promoted_certificate = _forged(
        external_owner.certificate,
        backend_full_block_uniform_law_certified=True,
    )
    certificate_values = {
        name: getattr(promoted_certificate, name)
        for name in type(promoted_certificate).__annotations__
    }
    promoted_certificate = _forged(
        promoted_certificate,
        certificate_sha256=execution._semantic_digest(
            execution._certificate_payload(certificate_values)
        ),
    )
    with pytest.raises(ValueError):
        execution._validate_certificate(promoted_certificate)

    before_external_backend = len(evidence["backend_calls"])
    with _trace_operations() as system_splice_calls:
        with pytest.raises(ValueError):
            system_owner.validate_result(result)
    with _trace_operations() as external_splice_calls:
        with pytest.raises(ValueError):
            external_owner.validate_result(evidence["system_result"])
    assert len(evidence["backend_calls"]) == before_external_backend
    for calls in (system_splice_calls, external_splice_calls):
        assert calls["cp47_execute"] == 0
        assert calls["cp48_acquire"] == 0
        assert calls["cp48_decode"] == 0
        assert calls["cp43_combined"] == 0


def test_owner_bound_hostile_scalars_refuse_before_parent_backend_or_ledger(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    owner = evidence["external_owner"]
    backend_count = len(evidence["backend_calls"])
    ledger_rows = evidence["final_snapshot"].retired_draw_rows
    cases = (
        ((_TouchBomb(), 0, 40), TypeError),
        ((0, _TouchBomb(), 41), TypeError),
        ((0, 0, _TouchBomb()), TypeError),
        ((True, 0, 42), TypeError),
        ((np.int64(0), 0, 43), TypeError),
        ((-1, 0, 44), ValueError),
        (((1 << 64), 0, 45), ValueError),
    )
    for arguments, error_type in cases:
        bombs = tuple(value for value in arguments if isinstance(value, _TouchBomb))
        with _trace_operations() as calls:
            with pytest.raises(error_type):
                owner.execute(*arguments)
        assert all(bomb.calls == 0 for bomb in bombs)
        assert all(count == 0 for count in calls.values())
    assert len(evidence["backend_calls"]) == backend_count
    assert owner.ledger_snapshot().retired_draw_rows == ledger_rows


def test_owner_bound_local_backend_and_cp47_drift_refuse_before_backend(
    owner_bound_evidence,
    monkeypatch,
):
    evidence = owner_bound_evidence
    owner = evidence["external_owner"]
    backend_count = len(evidence["backend_calls"])
    ledger_rows = owner.ledger_snapshot().retired_draw_rows
    replacement_calls = []

    def replacement(*args, **kwargs):
        replacement_calls.append((args, kwargs))
        raise AssertionError("drift replacement executed")

    cases = (
        (execution, "_semantic_digest"),
        (execution, "_validate_result_values"),
        (execution, "_decode_big_endian_words"),
        (execution, "_acquire_exact_byte_block"),
        (execution._CP47_OWNER_TYPE, "execute"),
    )
    for offset, (namespace, name) in enumerate(cases):
        with monkeypatch.context() as patcher:
            patcher.setattr(namespace, name, replacement)
            with _trace_operations() as calls:
                with pytest.raises(ValueError):
                    owner.execute(301, 401, 50 + offset)
        assert calls["cp47_execute"] == 0
        assert calls["cp48_acquire"] == 0
        assert calls["cp48_decode"] == 0
        assert calls["cp43_combined"] == 0
    assert replacement_calls == []
    assert len(evidence["backend_calls"]) == backend_count
    assert owner.ledger_snapshot().retired_draw_rows == ledger_rows
