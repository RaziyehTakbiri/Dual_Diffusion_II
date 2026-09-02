"""Realize CP47 full-word capsules from one exact external byte block.

This checkpoint binds either the cached :func:`os.urandom` Python API or one
exact caller callback to CP47's complete-word provider boundary.  A reached
boundary requests exactly ``8L`` bytes once, decodes them with a fixed manual
big-endian bijection, and gives the resulting exact ``L``-tuple to CP47.  CP47
remains the sole draw-retirement and semantic-execution authority.

The system profile certifies only that the cached ordinary ``os.urandom`` API
is called at the reached boundary.  It does not certify the operating system's
law, independence, totality, physical entropy, internal retries, syscall
count, or cryptographic properties.  The external profile makes the analogous
interface claim about the exact supplied callback and no law claim about it.

The byte/word codec is a bijection.  Consequently, an exactly jointly uniform
``8L``-byte block pushes forward to product-uniform uint64 words and preserves
total variation.  Per-byte marginals are insufficient.  IID word capsules
additionally require jointly/sequentially uniform backend blocks on distinct
draw identifiers.  Moreover, provided the CP48 return event has positive
probability, conditioning on a returned result preserves these conclusions
only when the complete CP48 success likelihood is constant over capsule
values; totality is sufficient.  The sequence statement analogously requires
positive joint return-event mass, and marginal per-call conditions do not
establish that joint statement.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import marshal
import os
import platform
import sys
import threading
from typing import Dict, Mapping, Optional, Tuple

from heterodiff.processes import (
    plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter as _adapter,
)


PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_CAPSULE_EXECUTION_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-byte-source-full-"
    "capsule-execution-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_CAPSULE_EXECUTION_POLICY = (
    "exact-checkpoint47-and-transitive-checkpoint46-45-44-43-binding;"
    "sealed-private-byte-provider;two-exact-byte-source-profiles;"
    "one-three-argument-backend-call-at-a-reached-provider-boundary;"
    "exact-8L-byte-block-no-coercion-retry-filter-fallback-or-replacement;"
    "manual-fixed-big-endian-bijective-codec;all-byte-values-accepted;"
    "checkpoint47-sole-draw-retirement-and-semantic-execution-authority;"
    "exact-raw-byte-and-word-result-custody;structural-nonreplaying-validation;"
    "cached-ordinary-binding-with-explicit-live-ancestry-revalidation-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_CAPSULE_EXECUTION_SCOPE = (
    "operational-byte-source-to-complete-word-capsule-interface;"
    "system-profile-means-one-cached-os-urandom-Python-API-call-site-only;"
    "external-profile-means-one-exact-caller-callback-only;"
    "uniform-product-law-only-under-joint-full-byte-block-uniformity;"
    "iid-only-under-joint-or-sequential-uniform-distinct-draw-blocks;"
    "returned-law-also-requires-complete-CP48-value-independent-success;"
    "not-backend-totality-law-iid-entropy-security-authentication-freshness-"
    "internal-syscalls-loaded-code-integrity-or-reproducibility;"
    "not-unconditional-output-law-output-TV-bound-concurrent-semantic-safety-"
    "initializer-path-sampler-scientific-model-quality-generality-or-manuscript-claim"
)

INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_SYSTEM_OS_URANDOM_OPERATIONAL = (
    "system-os-urandom-operational"
)
INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED = (
    "external-exact-byte-block-unverified"
)
INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILES = (
    INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_SYSTEM_OS_URANDOM_OPERATIONAL,
    INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED,
)
INITIAL_TILT_REJECTION_BYTE_SOURCE_BYTE_ORDER = "big"
INITIAL_TILT_REJECTION_BYTE_SOURCE_BYTES_PER_WORD = 8
INITIAL_TILT_REJECTION_BYTE_SOURCE_BLOCK_UNIFORM_PRODUCT_LAW_THEOREM = (
    "the-fixed-big-endian-map-from-exact-8L-byte-blocks-to-L-uint64-words-is-"
    "a-bijection-and-preserves-total-variation;product-uniform-words-follow-"
    "only-if-the-complete-byte-block-is-jointly-uniform"
)
INITIAL_TILT_REJECTION_BYTE_SOURCE_IID_THEOREM = (
    "iid-word-capsules-follow-only-under-joint-or-sequential-uniform-backend-"
    "blocks-on-distinct-draw-identifiers;uniform-one-call-marginals-do-not-suffice"
)
INITIAL_TILT_REJECTION_BYTE_SOURCE_SUCCESS_CONDITIONING_CAVEAT = (
    "provided-the-CP48-return-event-has-positive-probability;uniformity-"
    "conditional-on-a-returned-result-requires-the-complete-CP48-success-"
    "likelihood-to-be-constant-across-capsule-values;totality-is-sufficient;"
    "returned-sequence-iid-requires-positive-joint-return-event-mass-and-the-"
    "corresponding-joint-success-condition-over-the-full-vector"
)

_SCHEMA_VERSION = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_CAPSULE_EXECUTION_SCHEMA_VERSION
_POLICY = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_CAPSULE_EXECUTION_POLICY
_SCOPE = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_CAPSULE_EXECUTION_SCOPE
_SYSTEM_PROFILE = (
    INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_SYSTEM_OS_URANDOM_OPERATIONAL
)
_EXTERNAL_PROFILE = (
    INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED
)
_PROFILES = INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILES
_BYTE_ORDER = INITIAL_TILT_REJECTION_BYTE_SOURCE_BYTE_ORDER
_BYTES_PER_WORD = INITIAL_TILT_REJECTION_BYTE_SOURCE_BYTES_PER_WORD
_PRODUCT_THEOREM = INITIAL_TILT_REJECTION_BYTE_SOURCE_BLOCK_UNIFORM_PRODUCT_LAW_THEOREM
_IID_THEOREM = INITIAL_TILT_REJECTION_BYTE_SOURCE_IID_THEOREM
_SUCCESS_CAVEAT = INITIAL_TILT_REJECTION_BYTE_SOURCE_SUCCESS_CONDITIONING_CAVEAT
_D = 1 << 64
_ZERO_SHA256 = "0" * 64

_JSON_DUMPS = json.dumps
_SHA256 = hashlib.sha256
_MARSHAL_DUMPS = marshal.dumps
_OS_URANDOM = os.urandom
_CODE_FINGERPRINT_FORMAT = (
    "python-marshal-v2-no-reference-table-exact-constant-domain-"
    "process-identity-default-fingerprint-v1"
)
_PYTHON_VERSION = tuple(sys.version_info[:3])
_PYTHON_IMPLEMENTATION = platform.python_implementation()
_LOCK_FACTORY = threading.Lock
_THREAD_LOCAL_FACTORY = threading.local

_CERTIFICATE_TOKEN = object()
_RESULT_TOKEN = object()
_PROVIDER_TOKEN = object()
_OWNER_TOKEN = object()

_semantic_digest = _adapter._semantic_digest
_require_sha256 = _adapter._require_sha256
_exact_uint64 = _adapter._exact_uint64
_exact_bool = _adapter._exact_bool
_runtime_default_fingerprint = _adapter._runtime_default_fingerprint
_code_sha256 = _adapter._code_sha256

_CP46_OWNER_TYPE = _adapter._CP46_OWNER_TYPE
_CP46_CERT_TYPE = _adapter._CP46_CERT_TYPE
_CP47_OWNER_TYPE = (
    _adapter.CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner
)
_CP47_CERT_TYPE = (
    _adapter.CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate
)
_CP47_RESULT_TYPE = (
    _adapter.CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult
)
_CP47_LEDGER_TYPE = (
    _adapter.CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot
)
_CP47_CERTIFY = (
    _adapter.certify_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter
)
_CP47_VALIDATE_CERTIFICATE = _adapter._validate_certificate
_CP47_VALIDATE_RESULT_RECORD = _adapter._validate_result_record
_CP47_OWNER_SNAPSHOT = _CP47_OWNER_TYPE._owner_snapshot
_CP47_EXECUTE = _CP47_OWNER_TYPE.execute
_CP47_VALIDATE_RESULT = _CP47_OWNER_TYPE.validate_result
_CP47_LEDGER_SNAPSHOT = _CP47_OWNER_TYPE.ledger_snapshot
_CP47_VALIDATE_LEDGER_SNAPSHOT = _CP47_OWNER_TYPE.validate_ledger_snapshot
_CP47_LIVE_REVALIDATE = _CP47_OWNER_TYPE.revalidate_live_ancestry
_CP47_CERTIFICATE_PROPERTY = _CP47_OWNER_TYPE.certificate
_CP47_SOURCE_MODEL_OWNER_PROPERTY = _CP47_OWNER_TYPE.source_model_owner
_CP47_REQUIRE_LOCAL_SURFACES = _adapter._require_local_surfaces
_CP47_POLICY = (
    _adapter.PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_EXECUTION_ADAPTER_POLICY
)


class PluginBridgeCounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionError(
    ArithmeticError
):
    """Fail-closed CP48 byte-source, binding, or custody error."""


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    omitted = set(names)
    return {name: values[name] for name in values if name not in omitted}


def _exact_profile(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if value not in _PROFILES:
        raise ValueError(name + " is not a certified byte-source profile")
    return value


def _positive_count(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value <= 0 or value >= _D:
        raise ValueError(name + " must be in [1, 2**64)")
    return value


def _exact_byte_block(
    value: object,
    *,
    name: str,
    byte_count: object,
) -> bytes:
    expected = _positive_count(byte_count, name="byte_count")
    if type(value) is not bytes:
        raise TypeError(name + " must be exact bytes")
    if len(value) != expected:
        raise ValueError(name + " has the wrong exact byte length")
    return value


def _acquire_exact_byte_block(
    byte_source: object,
    *,
    source_instance_sha256: object,
    draw_index: object,
    byte_count: object,
) -> bytes:
    if not callable(byte_source):
        raise TypeError("byte_source must be callable")
    source = _require_sha256(
        source_instance_sha256,
        name="source_instance_sha256",
    )
    draw = _exact_uint64(draw_index, name="draw_index")
    count = _positive_count(byte_count, name="byte_count")
    returned = byte_source(source, draw, count)
    return _exact_byte_block(
        returned,
        name="byte_source_return",
        byte_count=count,
    )


def _decode_big_endian_words(
    raw_bytes: object,
    *,
    word_count: object,
) -> Tuple[int, ...]:
    count = _positive_count(word_count, name="word_count")
    raw = _exact_byte_block(
        raw_bytes,
        name="raw_bytes",
        byte_count=_BYTES_PER_WORD * count,
    )
    words = []
    for word_index in range(count):
        word = 0
        offset = _BYTES_PER_WORD * word_index
        for byte_index in range(_BYTES_PER_WORD):
            word = (word << 8) | raw[offset + byte_index]
        words.append(word)
    return tuple(words)


def _encode_big_endian_words(words: object) -> bytes:
    if type(words) is not tuple:
        raise TypeError("words must be an exact tuple")
    if len(words) == 0:
        raise ValueError("words must be nonempty")
    encoded = []
    for index, word in enumerate(words):
        if type(word) is not int:
            raise TypeError("words[%d] must be an exact integer" % index)
        if word < 0 or word >= _D:
            raise ValueError("words[%d] is outside uint64" % index)
        for shift in (56, 48, 40, 32, 24, 16, 8, 0):
            encoded.append((word >> shift) & 255)
    return bytes(encoded)


def _raw_bytes_sha256(raw_bytes: object, *, byte_count: object) -> str:
    raw = _exact_byte_block(
        raw_bytes,
        name="raw_bytes",
        byte_count=byte_count,
    )
    return _SHA256(raw).hexdigest()


def _system_os_urandom_byte_source(
    source_instance_sha256: object,
    draw_index: object,
    byte_count: object,
) -> object:
    del source_instance_sha256, draw_index
    return _OS_URANDOM(byte_count)


def _require_dependency_surfaces() -> None:
    module_expectations = (
        (
            "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter",
            _CP47_CERTIFY,
        ),
        ("_validate_certificate", _CP47_VALIDATE_CERTIFICATE),
        ("_validate_result_record", _CP47_VALIDATE_RESULT_RECORD),
        ("_require_local_surfaces", _CP47_REQUIRE_LOCAL_SURFACES),
    )
    for name, expected in module_expectations:
        if not hasattr(_adapter, name) or getattr(_adapter, name) is not expected:
            raise ValueError("CP48 CP47 dependency surface changed: " + name)
    method_expectations = (
        ("_owner_snapshot", _CP47_OWNER_SNAPSHOT),
        ("execute", _CP47_EXECUTE),
        ("validate_result", _CP47_VALIDATE_RESULT),
        ("ledger_snapshot", _CP47_LEDGER_SNAPSHOT),
        ("validate_ledger_snapshot", _CP47_VALIDATE_LEDGER_SNAPSHOT),
        ("revalidate_live_ancestry", _CP47_LIVE_REVALIDATE),
    )
    for name, expected in method_expectations:
        if getattr(_CP47_OWNER_TYPE, name) is not expected:
            raise ValueError("CP48 CP47 owner method changed: " + name)
    property_expectations = (
        ("certificate", _CP47_CERTIFICATE_PROPERTY),
        ("source_model_owner", _CP47_SOURCE_MODEL_OWNER_PROPERTY),
    )
    for name, expected in property_expectations:
        if getattr(_CP47_OWNER_TYPE, name) is not expected:
            raise ValueError("CP48 CP47 owner property changed: " + name)
    _CP47_REQUIRE_LOCAL_SURFACES()


def _checkpoint43_certificate(certificate: _CP47_CERT_TYPE) -> object:
    return (
        certificate.checkpoint46_certificate.checkpoint45_certificate.checkpoint44_certificate.checkpoint43_certificate
    )


_CERTIFICATE_POSITIVE_FLAGS = (
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
)
_CERTIFICATE_NEGATIVE_FLAGS = (
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
    "concurrent_or_reentrant_semantic_safety_beyond_checkpoint47_retirement_certified",
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
)


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate:
    """Sealed CP47-bound certificate for one exact byte-source profile."""

    schema_version: str
    certificate_scope: str
    execution_policy: str
    byte_source_profile: str
    system_profile_selected: bool
    external_profile_selected: bool
    source_instance_sha256: str
    byte_source_role_sha256: str
    provider_role_sha256: str
    execution_role_sha256: str
    backend_callback_runtime_identity: int
    external_byte_source_runtime_identity: int
    provider_runtime_identity: int
    checkpoint47_certificate: _CP47_CERT_TYPE
    checkpoint47_certificate_sha256: str
    checkpoint47_owner_runtime_identity: int
    checkpoint46_certificate_sha256: str
    checkpoint46_owner_runtime_identity: int
    checkpoint45_certificate_sha256: str
    checkpoint45_owner_runtime_identity: int
    checkpoint44_certificate_sha256: str
    checkpoint44_owner_runtime_identity: int
    checkpoint43_certificate_sha256: str
    checkpoint43_owner_runtime_identity: int
    process_parameter_sha256: str
    raw_word_domain_size: int
    bytes_per_word: int
    byte_order: str
    full_word_count: int
    proposal_word_count: int
    decision_word_count: int
    raw_byte_count: int
    max_retired_draws: int
    block_uniform_product_law_theorem: str
    iid_theorem: str
    success_conditioning_caveat: str
    execution_runtime_sha256: str
    exact_checkpoint47_owner_binding_certified: bool
    exact_transitive_checkpoint46_45_44_43_binding_certified: bool
    exact_provider_and_backend_identity_binding_certified: bool
    system_profile_restricted_to_internal_cached_os_urandom_wrapper_certified: bool
    external_profile_restricted_to_exact_caller_callable_certified: bool
    exact_three_argument_backend_invocation_certified: bool
    backend_invoked_at_most_once_per_provider_boundary_certified: bool
    backend_invoked_exactly_once_when_boundary_reached_certified: bool
    exact_8l_byte_block_required_certified: bool
    fixed_big_endian_manual_codec_bijection_certified: bool
    all_exact_byte_contents_accepted_without_filter_certified: bool
    no_coercion_retry_filter_fallback_or_replacement_certified: bool
    checkpoint47_sole_draw_retirement_authority_certified: bool
    checkpoint47_execute_invoked_at_most_once_per_execution_certified: bool
    checkpoint47_execute_invoked_exactly_once_when_boundary_reached_certified: bool
    exact_raw_bytes_and_words_result_custody_certified: bool
    structural_nonreplaying_result_validation_certified: bool
    cached_ordinary_binding_boundary_certified: bool
    explicit_live_ancestry_revalidation_available: bool
    conditional_full_block_uniform_product_law_theorem_recorded: bool
    conditional_iid_theorem_recorded: bool
    complete_cp48_success_conditioning_caveat_recorded: bool
    system_profile_claim_limited_to_operational_api_binding_certified: bool
    backend_totality_certified: bool
    backend_success_probability_certified: bool
    backend_full_block_uniform_law_certified: bool
    backend_iid_across_calls_certified: bool
    os_urandom_uniform_law_certified: bool
    os_urandom_iid_law_certified: bool
    physical_entropy_certified: bool
    cryptographic_security_certified: bool
    backend_cryptographic_authentication_certified: bool
    cross_call_value_freshness_certified: bool
    distinct_draw_ids_imply_distinct_values_certified: bool
    global_cross_owner_cross_process_fork_or_restart_uniqueness_certified: bool
    backend_internal_behavior_or_syscall_count_certified: bool
    concurrent_or_reentrant_semantic_safety_beyond_checkpoint47_retirement_certified: bool
    unconditional_returned_result_law_certified: bool
    semantic_output_tv_lower_bound_certified: bool
    adapter_loaded_code_integrity_certified: bool
    backend_loaded_code_integrity_certified: bool
    runtime_portable: bool
    initializer_admissible: bool
    path_admissible: bool
    sampler_admissible: bool
    scientific_claim_promoted: bool
    model_quality_claim_promoted: bool
    generality_claim_promoted: bool
    manuscript_claim_promoted: bool
    hostile_same_process_private_state_tamper_resilience_certified: bool
    source_instance_digest_authenticates_backend_certified: bool
    system_profile_reproducibility_certified: bool
    checkpoint46_declared_request_law_realized_certified: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP48 certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("CP48 certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP48 certificate fields are incomplete")
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP48 certificates are not pickleable")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate.__annotations__
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: (
            values["checkpoint47_certificate_sha256"]
            if name == "checkpoint47_certificate"
            else values[name]
        )
        for name in _certificate_fields()
        if name != "certificate_sha256"
    }


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    if set(values) != set(_certificate_fields()):
        raise TypeError("CP48 certificate mapping is incomplete")
    expected_text = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "execution_policy": _POLICY,
        "byte_order": _BYTE_ORDER,
        "block_uniform_product_law_theorem": _PRODUCT_THEOREM,
        "iid_theorem": _IID_THEOREM,
        "success_conditioning_caveat": _SUCCESS_CAVEAT,
    }
    for name, expected in expected_text.items():
        if type(values[name]) is not str:
            raise TypeError("certificate.%s must be exact text" % name)
        if values[name] != expected:
            raise ValueError("CP48 certificate text differs: " + name)
    profile = _exact_profile(
        values["byte_source_profile"],
        name="certificate.byte_source_profile",
    )
    system_selected = profile == _SYSTEM_PROFILE
    _exact_bool(
        values["system_profile_selected"],
        system_selected,
        name="certificate.system_profile_selected",
    )
    _exact_bool(
        values["external_profile_selected"],
        not system_selected,
        name="certificate.external_profile_selected",
    )
    for name in (
        "source_instance_sha256",
        "byte_source_role_sha256",
        "provider_role_sha256",
        "execution_role_sha256",
        "checkpoint47_certificate_sha256",
        "checkpoint46_certificate_sha256",
        "checkpoint45_certificate_sha256",
        "checkpoint44_certificate_sha256",
        "checkpoint43_certificate_sha256",
        "process_parameter_sha256",
        "execution_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(values[name], name="certificate." + name)
    integer_fields = (
        "backend_callback_runtime_identity",
        "external_byte_source_runtime_identity",
        "provider_runtime_identity",
        "checkpoint47_owner_runtime_identity",
        "checkpoint46_owner_runtime_identity",
        "checkpoint45_owner_runtime_identity",
        "checkpoint44_owner_runtime_identity",
        "checkpoint43_owner_runtime_identity",
        "raw_word_domain_size",
        "bytes_per_word",
        "full_word_count",
        "proposal_word_count",
        "decision_word_count",
        "raw_byte_count",
        "max_retired_draws",
    )
    for name in integer_fields:
        if type(values[name]) is not int:
            raise TypeError("certificate.%s must be an exact integer" % name)
    for name in (
        "backend_callback_runtime_identity",
        "provider_runtime_identity",
        "checkpoint47_owner_runtime_identity",
        "checkpoint46_owner_runtime_identity",
        "checkpoint45_owner_runtime_identity",
        "checkpoint44_owner_runtime_identity",
        "checkpoint43_owner_runtime_identity",
    ):
        if values[name] <= 0:
            raise ValueError(
                "CP48 certificate runtime identity is not positive: " + name
            )
    expected_external_identity = (
        0 if system_selected else values["backend_callback_runtime_identity"]
    )
    if values["external_byte_source_runtime_identity"] != expected_external_identity:
        raise ValueError("CP48 external byte-source identity differs")
    parent = values["checkpoint47_certificate"]
    if type(parent) is not _CP47_CERT_TYPE:
        raise TypeError("checkpoint47_certificate has the wrong exact type")
    parent = _CP47_VALIDATE_CERTIFICATE(parent)
    cp46 = parent.checkpoint46_certificate
    cp45 = cp46.checkpoint45_certificate
    cp44 = cp45.checkpoint44_certificate
    cp43 = cp44.checkpoint43_certificate
    if parent.passed is not True:
        raise ValueError("CP48 CP47 parent did not pass")
    expected_integers = {
        "raw_word_domain_size": _D,
        "bytes_per_word": _BYTES_PER_WORD,
        "full_word_count": parent.full_word_count,
        "proposal_word_count": parent.proposal_word_count,
        "decision_word_count": parent.decision_word_count,
        "raw_byte_count": _BYTES_PER_WORD * parent.full_word_count,
        "max_retired_draws": parent.max_retired_draws,
        "checkpoint46_owner_runtime_identity": parent.checkpoint46_owner_runtime_identity,
        "checkpoint45_owner_runtime_identity": parent.checkpoint45_owner_runtime_identity,
        "checkpoint44_owner_runtime_identity": parent.checkpoint44_owner_runtime_identity,
        "checkpoint43_owner_runtime_identity": parent.checkpoint43_owner_runtime_identity,
    }
    for name, expected in expected_integers.items():
        if values[name] != expected:
            raise ValueError("CP48 certificate integer differs: " + name)
    expected_hashes = {
        "checkpoint47_certificate_sha256": parent.certificate_sha256,
        "checkpoint46_certificate_sha256": cp46.certificate_sha256,
        "checkpoint45_certificate_sha256": cp45.certificate_sha256,
        "checkpoint44_certificate_sha256": cp44.certificate_sha256,
        "checkpoint43_certificate_sha256": cp43.certificate_sha256,
        "process_parameter_sha256": parent.process_parameter_sha256,
        "execution_runtime_sha256": _runtime_sha256(),
    }
    for name, expected in expected_hashes.items():
        if values[name] != expected:
            raise ValueError("CP48 certificate digest differs: " + name)
    if parent.source_instance_sha256 != values["source_instance_sha256"]:
        raise ValueError("CP48 source instance differs from CP47")
    if parent.provider_role_sha256 != values["provider_role_sha256"]:
        raise ValueError("CP48 provider role differs from CP47")
    if parent.execution_role_sha256 != values["execution_role_sha256"]:
        raise ValueError("CP48 execution role differs from CP47")
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="certificate." + name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="certificate." + name)
    _exact_bool(values["passed"], True, name="certificate.passed")
    if values["certificate_sha256"] != _semantic_digest(_certificate_payload(values)):
        raise ValueError("CP48 certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate:
    if (
        type(certificate)
        is not CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate
    ):
        raise TypeError("certificate has the wrong exact CP48 type")
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _make_certificate(
    source_model_owner: _CP46_OWNER_TYPE,
    checkpoint47_owner: _CP47_OWNER_TYPE,
    provider: object,
    backend: object,
    external_byte_source: object,
    *,
    source_instance_sha256: str,
    byte_source_profile: str,
    byte_source_role_sha256: str,
    provider_role_sha256: str,
    execution_role_sha256: str,
) -> CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate:
    parent = _CP47_CERTIFICATE_PROPERTY.__get__(
        checkpoint47_owner,
        _CP47_OWNER_TYPE,
    )
    parent = _CP47_VALIDATE_CERTIFICATE(parent)
    cp46 = parent.checkpoint46_certificate
    cp45 = cp46.checkpoint45_certificate
    cp44 = cp45.checkpoint44_certificate
    cp43 = cp44.checkpoint43_certificate
    system_selected = byte_source_profile == _SYSTEM_PROFILE
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "execution_policy": _POLICY,
        "byte_source_profile": byte_source_profile,
        "system_profile_selected": system_selected,
        "external_profile_selected": not system_selected,
        "source_instance_sha256": source_instance_sha256,
        "byte_source_role_sha256": byte_source_role_sha256,
        "provider_role_sha256": provider_role_sha256,
        "execution_role_sha256": execution_role_sha256,
        "backend_callback_runtime_identity": id(backend),
        "external_byte_source_runtime_identity": (
            0 if external_byte_source is None else id(external_byte_source)
        ),
        "provider_runtime_identity": id(provider),
        "checkpoint47_certificate": parent,
        "checkpoint47_certificate_sha256": parent.certificate_sha256,
        "checkpoint47_owner_runtime_identity": id(checkpoint47_owner),
        "checkpoint46_certificate_sha256": cp46.certificate_sha256,
        "checkpoint46_owner_runtime_identity": id(source_model_owner),
        "checkpoint45_certificate_sha256": cp45.certificate_sha256,
        "checkpoint45_owner_runtime_identity": parent.checkpoint45_owner_runtime_identity,
        "checkpoint44_certificate_sha256": cp44.certificate_sha256,
        "checkpoint44_owner_runtime_identity": parent.checkpoint44_owner_runtime_identity,
        "checkpoint43_certificate_sha256": cp43.certificate_sha256,
        "checkpoint43_owner_runtime_identity": parent.checkpoint43_owner_runtime_identity,
        "process_parameter_sha256": parent.process_parameter_sha256,
        "raw_word_domain_size": _D,
        "bytes_per_word": _BYTES_PER_WORD,
        "byte_order": _BYTE_ORDER,
        "full_word_count": parent.full_word_count,
        "proposal_word_count": parent.proposal_word_count,
        "decision_word_count": parent.decision_word_count,
        "raw_byte_count": _BYTES_PER_WORD * parent.full_word_count,
        "max_retired_draws": parent.max_retired_draws,
        "block_uniform_product_law_theorem": _PRODUCT_THEOREM,
        "iid_theorem": _IID_THEOREM,
        "success_conditioning_caveat": _SUCCESS_CAVEAT,
        "execution_runtime_sha256": _runtime_sha256(),
        "passed": True,
        "certificate_sha256": _ZERO_SHA256,
    }
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        values[name] = True
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        values[name] = False
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult:
    """One sealed CP48 byte block, word capsule, and CP47 result."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate
    certificate_sha256: str
    checkpoint47_result: _CP47_RESULT_TYPE
    checkpoint47_result_sha256: str
    checkpoint47_provider_receipt_sha256: str
    owner_runtime_identity: int
    source_instance_sha256: str
    byte_source_profile: str
    byte_source_role_sha256: str
    run_id: int
    initialization_index: int
    draw_index: int
    retirement_ordinal: int
    retirement_chain_sha256: str
    raw_byte_count: int
    raw_bytes: bytes
    raw_bytes_sha256: str
    source_full_words: Tuple[int, ...]
    source_full_words_sha256: str
    backend_invocation_count: int
    checkpoint47_execute_invocation_count: int
    exact_raw_bytes_reconstructed_from_words: bool
    fixed_big_endian_round_trip_certified: bool
    structural_validation_is_nonreplaying: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP48 results cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("CP48 results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP48 result fields are incomplete")
        _validate_result_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP48 results are not pickleable")


def _result_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult.__annotations__
    )


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    payload = dict(_without(values, "result_sha256"))
    payload["certificate"] = values["certificate_sha256"]
    payload["checkpoint47_result"] = values["checkpoint47_result_sha256"]
    payload["raw_bytes"] = values["raw_bytes_sha256"]
    return payload


def _validate_result_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate
    ] = None,
    trusted_checkpoint47_owner_runtime_identity: Optional[int] = None,
    trusted_owner_runtime_identity: Optional[int] = None,
) -> None:
    if set(values) != set(_result_fields()):
        raise TypeError("CP48 result mapping is incomplete")
    if (
        type(values["schema_version"]) is not str
        or values["schema_version"] != _SCHEMA_VERSION
    ):
        raise ValueError("CP48 result schema differs")
    certificate = _validate_certificate(values["certificate"])
    if trusted_certificate is not None and certificate is not trusted_certificate:
        raise ValueError("CP48 result certificate identity differs")
    _require_sha256(values["certificate_sha256"], name="result.certificate_sha256")
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("CP48 result certificate digest differs")
    checkpoint47_result = _CP47_VALIDATE_RESULT_RECORD(
        values["checkpoint47_result"],
        trusted_certificate=certificate.checkpoint47_certificate,
        trusted_checkpoint43_certificate=_checkpoint43_certificate(
            certificate.checkpoint47_certificate
        ),
        trusted_owner_runtime_identity=certificate.checkpoint47_owner_runtime_identity,
    )
    if trusted_checkpoint47_owner_runtime_identity is not None:
        if type(trusted_checkpoint47_owner_runtime_identity) is not int:
            raise TypeError("trusted checkpoint47 owner identity must be exact")
        if (
            certificate.checkpoint47_owner_runtime_identity
            != trusted_checkpoint47_owner_runtime_identity
        ):
            raise ValueError("CP48 result belongs to another CP47 owner")
    for name, expected in (
        ("checkpoint47_result_sha256", checkpoint47_result.result_sha256),
        (
            "checkpoint47_provider_receipt_sha256",
            checkpoint47_result.provider_receipt.receipt_sha256,
        ),
        ("source_instance_sha256", certificate.source_instance_sha256),
        ("byte_source_role_sha256", certificate.byte_source_role_sha256),
        ("retirement_chain_sha256", checkpoint47_result.retirement_chain_sha256),
        (
            "raw_bytes_sha256",
            _raw_bytes_sha256(
                values["raw_bytes"], byte_count=certificate.raw_byte_count
            ),
        ),
        ("source_full_words_sha256", checkpoint47_result.source_full_words_sha256),
    ):
        _require_sha256(values[name], name="result." + name)
        if values[name] != expected:
            raise ValueError("CP48 result digest differs: " + name)
    if (
        type(values["byte_source_profile"]) is not str
        or values["byte_source_profile"] != certificate.byte_source_profile
    ):
        raise ValueError("CP48 result byte-source profile differs")
    owner_identity = values["owner_runtime_identity"]
    if type(owner_identity) is not int or owner_identity <= 0:
        raise ValueError("CP48 result owner identity differs")
    if trusted_owner_runtime_identity is not None:
        if type(trusted_owner_runtime_identity) is not int:
            raise TypeError("trusted owner identity must be exact")
        if owner_identity != trusted_owner_runtime_identity:
            raise ValueError("CP48 result belongs to another owner")
    scalar_fields = (
        "run_id",
        "initialization_index",
        "draw_index",
    )
    for name in scalar_fields:
        _exact_uint64(values[name], name="result." + name)
        if values[name] != getattr(checkpoint47_result, name):
            raise ValueError("CP48/CP47 scalar differs: " + name)
    ordinal = values["retirement_ordinal"]
    if type(ordinal) is not int or ordinal < 0:
        raise ValueError("CP48 retirement ordinal differs")
    if ordinal != checkpoint47_result.retirement_ordinal:
        raise ValueError("CP48/CP47 retirement ordinal differs")
    if type(values["raw_byte_count"]) is not int:
        raise TypeError("result.raw_byte_count must be an exact integer")
    if values["raw_byte_count"] != certificate.raw_byte_count:
        raise ValueError("CP48 raw byte count differs")
    _exact_byte_block(
        values["raw_bytes"],
        name="result.raw_bytes",
        byte_count=certificate.raw_byte_count,
    )
    words = values["source_full_words"]
    if type(words) is not tuple or words != checkpoint47_result.source_full_words:
        raise ValueError("CP48/CP47 full words differ")
    if _encode_big_endian_words(words) != values["raw_bytes"]:
        raise ValueError("CP48 fixed big-endian byte/word round trip differs")
    for name in (
        "backend_invocation_count",
        "checkpoint47_execute_invocation_count",
    ):
        if type(values[name]) is not int or values[name] != 1:
            raise ValueError("CP48 exact invocation count differs: " + name)
    for name in (
        "exact_raw_bytes_reconstructed_from_words",
        "fixed_big_endian_round_trip_certified",
        "structural_validation_is_nonreplaying",
    ):
        _exact_bool(values[name], True, name="result." + name)
    _require_sha256(values["result_sha256"], name="result.result_sha256")
    if values["result_sha256"] != _semantic_digest(_result_payload(values)):
        raise ValueError("CP48 result digest differs")


def _validate_result_record(
    result: object,
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate
    ] = None,
    trusted_checkpoint47_owner_runtime_identity: Optional[int] = None,
    trusted_owner_runtime_identity: Optional[int] = None,
) -> CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult:
    if (
        type(result)
        is not CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult
    ):
        raise TypeError("result has the wrong exact CP48 type")
    _validate_result_values(
        {name: getattr(result, name) for name in _result_fields()},
        trusted_certificate=trusted_certificate,
        trusted_checkpoint47_owner_runtime_identity=trusted_checkpoint47_owner_runtime_identity,
        trusted_owner_runtime_identity=trusted_owner_runtime_identity,
    )
    return result


def _make_result(
    certificate: CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate,
    checkpoint47_result: _CP47_RESULT_TYPE,
    raw_bytes: bytes,
    *,
    owner_runtime_identity: int,
) -> CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult:
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "checkpoint47_result": checkpoint47_result,
        "checkpoint47_result_sha256": checkpoint47_result.result_sha256,
        "checkpoint47_provider_receipt_sha256": checkpoint47_result.provider_receipt.receipt_sha256,
        "owner_runtime_identity": owner_runtime_identity,
        "source_instance_sha256": certificate.source_instance_sha256,
        "byte_source_profile": certificate.byte_source_profile,
        "byte_source_role_sha256": certificate.byte_source_role_sha256,
        "run_id": checkpoint47_result.run_id,
        "initialization_index": checkpoint47_result.initialization_index,
        "draw_index": checkpoint47_result.draw_index,
        "retirement_ordinal": checkpoint47_result.retirement_ordinal,
        "retirement_chain_sha256": checkpoint47_result.retirement_chain_sha256,
        "raw_byte_count": certificate.raw_byte_count,
        "raw_bytes": raw_bytes,
        "raw_bytes_sha256": _raw_bytes_sha256(
            raw_bytes,
            byte_count=certificate.raw_byte_count,
        ),
        "source_full_words": checkpoint47_result.source_full_words,
        "source_full_words_sha256": checkpoint47_result.source_full_words_sha256,
        "backend_invocation_count": 1,
        "checkpoint47_execute_invocation_count": 1,
        "exact_raw_bytes_reconstructed_from_words": True,
        "fixed_big_endian_round_trip_certified": True,
        "structural_validation_is_nonreplaying": True,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _semantic_digest(_result_payload(values))
    return CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult(
        **values,
        _construction_token=_RESULT_TOKEN,
    )


class _PrivateFullCapsuleProvider:
    """Private sealed CP47 provider retaining exact byte/word custody."""

    __slots__ = (
        "_source_instance_sha256",
        "_source_instance_identity",
        "_byte_source_profile",
        "_byte_source_profile_identity",
        "_backend",
        "_backend_identity",
        "_acquisitions",
        "_acquisitions_identity",
        "_lock",
        "_lock_identity",
        "_thread_context",
        "_thread_context_identity",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP48 private providers cannot be subclassed")

    def __init__(
        self,
        source_instance_sha256: str,
        byte_source_profile: str,
        backend: object,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _PROVIDER_TOKEN:
            raise TypeError("CP48 private providers are module-created")
        source = _require_sha256(
            source_instance_sha256,
            name="source_instance_sha256",
        )
        profile = _exact_profile(
            byte_source_profile,
            name="byte_source_profile",
        )
        if not callable(backend):
            raise TypeError("backend must be callable")
        acquisitions = {}
        lock = _LOCK_FACTORY()
        thread_context = _THREAD_LOCAL_FACTORY()
        for name, value in (
            ("_source_instance_sha256", source),
            ("_source_instance_identity", source),
            ("_byte_source_profile", profile),
            ("_byte_source_profile_identity", profile),
            ("_backend", backend),
            ("_backend_identity", backend),
            ("_acquisitions", acquisitions),
            ("_acquisitions_identity", acquisitions),
            ("_lock", lock),
            ("_lock_identity", lock),
            ("_thread_context", thread_context),
            ("_thread_context_identity", thread_context),
            ("_sealed", True),
        ):
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("CP48 private providers are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("CP48 private providers are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP48 private providers are not pickleable")

    def _require_binding(self) -> None:
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("CP48 provider seal differs")
        current = (
            self._source_instance_sha256,
            self._byte_source_profile,
            self._backend,
            self._acquisitions,
            self._lock,
            self._thread_context,
        )
        frozen = (
            self._source_instance_identity,
            self._byte_source_profile_identity,
            self._backend_identity,
            self._acquisitions_identity,
            self._lock_identity,
            self._thread_context_identity,
        )
        if any(actual is not expected for actual, expected in zip(current, frozen)):
            raise ValueError("CP48 provider identity changed")
        if not callable(self._backend):
            raise TypeError("CP48 bound backend is no longer callable")

    def _context_stack(self) -> list:
        stack = getattr(self._thread_context, "cp48_stack", None)
        if stack is None:
            stack = []
            setattr(self._thread_context, "cp48_stack", stack)
        if type(stack) is not list:
            raise TypeError("CP48 provider thread context is malformed")
        return stack

    def _begin(self, draw_index: object) -> object:
        self._require_binding()
        draw = _exact_uint64(draw_index, name="draw_index")
        token = object()
        stack = self._context_stack()
        try:
            stack.append((token, draw))
            self._require_binding()
        except BaseException:
            if len(stack) != 0 and stack[-1] == (token, draw):
                stack.pop()
            if (
                len(stack) == 0
                and getattr(self._thread_context, "cp48_stack", None) is stack
            ):
                delattr(self._thread_context, "cp48_stack")
            raise
        return token

    def _active_token(self, draw_index: object) -> object:
        self._require_binding()
        draw = _exact_uint64(draw_index, name="draw_index")
        stack = self._context_stack()
        if len(stack) == 0:
            raise PluginBridgeCounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionError(
                "CP48 provider has no active execution context"
            )
        pair = stack[-1]
        if type(pair) is not tuple or len(pair) != 2:
            raise TypeError("CP48 provider execution context is malformed")
        token, expected_draw = pair
        if type(token) is not object or type(expected_draw) is not int:
            raise TypeError("CP48 provider execution context is inexact")
        if expected_draw != draw:
            raise ValueError("CP48 provider active draw differs")
        return token

    def _end(self, token: object) -> None:
        self._require_binding()
        if type(token) is not object:
            raise TypeError("CP48 execution token has the wrong exact type")
        stack = self._context_stack()
        if len(stack) == 0:
            raise PluginBridgeCounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionError(
                "CP48 provider execution context is absent"
            )
        pair = stack[-1]
        if type(pair) is not tuple or len(pair) != 2 or pair[0] is not token:
            raise ValueError("CP48 provider execution context order differs")
        stack.pop()
        if len(stack) == 0:
            delattr(self._thread_context, "cp48_stack")
        self._require_binding()

    def __call__(
        self,
        source_instance_sha256: object,
        draw_index: object,
        full_word_count: object,
    ) -> Tuple[int, ...]:
        self._require_binding()
        source = _require_sha256(
            source_instance_sha256,
            name="source_instance_sha256",
        )
        draw = _exact_uint64(draw_index, name="draw_index")
        count = _positive_count(full_word_count, name="full_word_count")
        token = self._active_token(draw)
        if source != self._source_instance_sha256:
            raise ValueError("CP48 provider source instance differs")
        byte_count = _BYTES_PER_WORD * count
        raw = _acquire_exact_byte_block(
            self._backend,
            source_instance_sha256=source,
            draw_index=draw,
            byte_count=byte_count,
        )
        words = _decode_big_endian_words(raw, word_count=count)
        if _encode_big_endian_words(words) != raw:
            raise ValueError("CP48 manual fixed-endian round trip differs")
        with self._lock:
            if token in self._acquisitions:
                raise PluginBridgeCounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionError(
                    "CP48 provider execution custody already exists"
                )
            self._acquisitions[token] = (draw, source, byte_count, raw, words)
        self._require_binding()
        return words

    def _claim(
        self,
        token: object,
        source_instance_sha256: object,
        draw_index: object,
        full_words: object,
    ) -> bytes:
        self._require_binding()
        source = _require_sha256(
            source_instance_sha256,
            name="source_instance_sha256",
        )
        draw = _exact_uint64(draw_index, name="draw_index")
        if type(token) is not object:
            raise TypeError("CP48 execution token has the wrong exact type")
        if self._active_token(draw) is not token:
            raise ValueError("CP48 provider active execution token differs")
        if type(full_words) is not tuple:
            raise TypeError("full_words must be an exact tuple")
        with self._lock:
            if token not in self._acquisitions:
                raise PluginBridgeCounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionError(
                    "CP48 provider execution custody is absent"
                )
            retained = self._acquisitions[token]
            retained_draw, retained_source, byte_count, raw, words = retained
            if (
                retained_draw != draw
                or retained_source != source
                or words != full_words
            ):
                raise ValueError("CP48 provider retained custody differs")
            del self._acquisitions[token]
        if (
            _exact_byte_block(
                raw,
                name="retained_raw_bytes",
                byte_count=byte_count,
            )
            is not raw
        ):
            raise ValueError("CP48 provider substituted retained bytes")
        return raw

    def _discard(self, token: object) -> None:
        """Remove this invocation's private reference without changing CP47 retirement."""

        self._require_binding()
        if type(token) is not object:
            raise TypeError("CP48 execution token has the wrong exact type")
        with self._lock:
            if token in self._acquisitions:
                del self._acquisitions[token]
        self._require_binding()


def _runtime_sha256() -> str:
    owner_type = globals().get(
        "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner"
    )
    if owner_type is None:
        raise ValueError("CP48 owner type is not loaded")
    owner_methods = (
        "__init__",
        "__setattr__",
        "__delattr__",
        "__reduce_ex__",
        "_require_local_surface_binding",
        "_owner_snapshot",
        "execute",
        "validate_result",
        "ledger_snapshot",
        "validate_ledger_snapshot",
        "revalidate_live_ancestry",
    )
    provider_methods = (
        "__init__",
        "__setattr__",
        "__delattr__",
        "__reduce_ex__",
        "_require_binding",
        "_context_stack",
        "_begin",
        "_active_token",
        "_end",
        "__call__",
        "_claim",
        "_discard",
    )
    payload = {
        "schema": _SCHEMA_VERSION,
        "python_version": _PYTHON_VERSION,
        "python_implementation": _PYTHON_IMPLEMENTATION,
        "code_fingerprint_format": _CODE_FINGERPRINT_FORMAT,
    }
    for name in owner_methods:
        payload["owner." + name] = _code_sha256(getattr(owner_type, name))
    for name in provider_methods:
        payload["provider." + name] = _code_sha256(
            getattr(_PrivateFullCapsuleProvider, name)
        )
    frozen = globals().get("_FROZEN_LOCAL_SURFACES", ())
    for name, value in frozen:
        if getattr(value, "__code__", None) is not None:
            payload["local." + name] = _code_sha256(value)
    local_guard = globals().get("_require_local_surfaces")
    if getattr(local_guard, "__code__", None) is not None:
        payload["local._require_local_surfaces"] = _code_sha256(local_guard)
    return _semantic_digest(payload)


_FROZEN_LOCAL_SURFACE_NAMES = (
    "_adapter",
    "_JSON_DUMPS",
    "_SHA256",
    "_MARSHAL_DUMPS",
    "_OS_URANDOM",
    "_CODE_FINGERPRINT_FORMAT",
    "_PYTHON_VERSION",
    "_PYTHON_IMPLEMENTATION",
    "_LOCK_FACTORY",
    "_THREAD_LOCAL_FACTORY",
    "_SCHEMA_VERSION",
    "_POLICY",
    "_SCOPE",
    "_SYSTEM_PROFILE",
    "_EXTERNAL_PROFILE",
    "_PROFILES",
    "_BYTE_ORDER",
    "_BYTES_PER_WORD",
    "_PRODUCT_THEOREM",
    "_IID_THEOREM",
    "_SUCCESS_CAVEAT",
    "_D",
    "_ZERO_SHA256",
    "_CERTIFICATE_TOKEN",
    "_RESULT_TOKEN",
    "_PROVIDER_TOKEN",
    "_OWNER_TOKEN",
    "_semantic_digest",
    "_require_sha256",
    "_exact_uint64",
    "_exact_bool",
    "_runtime_default_fingerprint",
    "_code_sha256",
    "_CP46_OWNER_TYPE",
    "_CP46_CERT_TYPE",
    "_CP47_OWNER_TYPE",
    "_CP47_CERT_TYPE",
    "_CP47_RESULT_TYPE",
    "_CP47_LEDGER_TYPE",
    "_CP47_CERTIFY",
    "_CP47_VALIDATE_CERTIFICATE",
    "_CP47_VALIDATE_RESULT_RECORD",
    "_CP47_OWNER_SNAPSHOT",
    "_CP47_EXECUTE",
    "_CP47_VALIDATE_RESULT",
    "_CP47_LEDGER_SNAPSHOT",
    "_CP47_VALIDATE_LEDGER_SNAPSHOT",
    "_CP47_LIVE_REVALIDATE",
    "_CP47_CERTIFICATE_PROPERTY",
    "_CP47_SOURCE_MODEL_OWNER_PROPERTY",
    "_CP47_REQUIRE_LOCAL_SURFACES",
    "_CP47_POLICY",
    "PluginBridgeCounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionError",
    "_without",
    "_exact_profile",
    "_positive_count",
    "_exact_byte_block",
    "_acquire_exact_byte_block",
    "_decode_big_endian_words",
    "_encode_big_endian_words",
    "_raw_bytes_sha256",
    "_system_os_urandom_byte_source",
    "_require_dependency_surfaces",
    "_checkpoint43_certificate",
    "_CERTIFICATE_POSITIVE_FLAGS",
    "_CERTIFICATE_NEGATIVE_FLAGS",
    "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate",
    "_certificate_fields",
    "_certificate_payload",
    "_validate_certificate_values",
    "_validate_certificate",
    "_make_certificate",
    "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult",
    "_result_fields",
    "_result_payload",
    "_validate_result_values",
    "_validate_result_record",
    "_make_result",
    "_PrivateFullCapsuleProvider",
    "_runtime_sha256",
)
_FROZEN_LOCAL_SURFACES = tuple(
    (name, globals()[name]) for name in _FROZEN_LOCAL_SURFACE_NAMES
)


def _require_local_surfaces(
    dependency_guard: object = _require_dependency_surfaces,
    frozen: Tuple[Tuple[str, object], ...] = _FROZEN_LOCAL_SURFACES,
    frozen_names: Tuple[str, ...] = _FROZEN_LOCAL_SURFACE_NAMES,
) -> None:
    namespace = globals()
    if namespace.get("_require_dependency_surfaces") is not dependency_guard:
        raise ValueError("CP48 dependency guard changed")
    if namespace.get("_FROZEN_LOCAL_SURFACES") is not frozen:
        raise ValueError("CP48 frozen local surfaces changed")
    if namespace.get("_FROZEN_LOCAL_SURFACE_NAMES") is not frozen_names:
        raise ValueError("CP48 frozen local surface names changed")
    for name, expected in frozen:
        if namespace.get(name) is not expected:
            raise ValueError("CP48 local surface changed: " + name)
    dependency_guard()


_LOCAL_SURFACE_GUARD = _require_local_surfaces


class CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner:
    """Immutable owner of one private byte provider and one CP47 owner."""

    __slots__ = (
        "_source_model_owner",
        "_source_model_owner_identity",
        "_external_byte_source",
        "_external_byte_source_identity",
        "_backend",
        "_backend_identity",
        "_provider",
        "_provider_identity",
        "_checkpoint47_owner",
        "_checkpoint47_owner_identity",
        "_checkpoint47_snapshot",
        "_certificate",
        "_certificate_identity",
        "_certificate_snapshot",
        "_certificate_snapshot_identity",
        "_local_surface_guard",
        "_local_surface_guard_identity",
        "_checkpoint47_execute",
        "_checkpoint47_validate_result",
        "_checkpoint47_ledger_snapshot",
        "_checkpoint47_validate_ledger_snapshot",
        "_checkpoint47_live_revalidate",
        "_exact_uint64_callback",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP48 owners cannot be subclassed")

    def __init__(
        self,
        source_model_owner: _CP46_OWNER_TYPE,
        external_byte_source: object,
        backend: object,
        provider: _PrivateFullCapsuleProvider,
        checkpoint47_owner: _CP47_OWNER_TYPE,
        certificate: CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("CP48 owners require certification")
        if type(source_model_owner) is not _CP46_OWNER_TYPE:
            raise TypeError("source_model_owner has the wrong exact CP46 type")
        if type(provider) is not _PrivateFullCapsuleProvider:
            raise TypeError("provider has the wrong exact CP48 private type")
        if type(checkpoint47_owner) is not _CP47_OWNER_TYPE:
            raise TypeError("checkpoint47_owner has the wrong exact CP47 type")
        _LOCAL_SURFACE_GUARD()
        checked = _validate_certificate(certificate)
        if (
            _CP47_SOURCE_MODEL_OWNER_PROPERTY.__get__(
                checkpoint47_owner,
                _CP47_OWNER_TYPE,
            )
            is not source_model_owner
        ):
            raise ValueError("CP48 CP47 owner belongs to another CP46 owner")
        parent = _CP47_CERTIFICATE_PROPERTY.__get__(
            checkpoint47_owner,
            _CP47_OWNER_TYPE,
        )
        if checked.checkpoint47_certificate is not parent:
            raise ValueError("CP48 certificate belongs to another CP47 certificate")
        identities = {
            "backend_callback_runtime_identity": id(backend),
            "provider_runtime_identity": id(provider),
            "checkpoint47_owner_runtime_identity": id(checkpoint47_owner),
            "checkpoint46_owner_runtime_identity": id(source_model_owner),
        }
        for name, expected in identities.items():
            if getattr(checked, name) != expected:
                raise ValueError("CP48 certificate runtime identity differs: " + name)
        expected_external_identity = (
            0 if external_byte_source is None else id(external_byte_source)
        )
        if checked.external_byte_source_runtime_identity != expected_external_identity:
            raise ValueError("CP48 external byte-source identity differs")
        provider._require_binding()
        checkpoint47_snapshot = _CP47_OWNER_SNAPSHOT(checkpoint47_owner)
        certificate_snapshot = tuple(
            getattr(checked, name) for name in _certificate_fields()
        )
        bindings = (
            ("_source_model_owner", source_model_owner),
            ("_source_model_owner_identity", source_model_owner),
            ("_external_byte_source", external_byte_source),
            ("_external_byte_source_identity", external_byte_source),
            ("_backend", backend),
            ("_backend_identity", backend),
            ("_provider", provider),
            ("_provider_identity", provider),
            ("_checkpoint47_owner", checkpoint47_owner),
            ("_checkpoint47_owner_identity", checkpoint47_owner),
            ("_checkpoint47_snapshot", checkpoint47_snapshot),
            ("_certificate", checked),
            ("_certificate_identity", checked),
            ("_certificate_snapshot", certificate_snapshot),
            ("_certificate_snapshot_identity", certificate_snapshot),
            ("_local_surface_guard", _LOCAL_SURFACE_GUARD),
            ("_local_surface_guard_identity", _LOCAL_SURFACE_GUARD),
            ("_checkpoint47_execute", _CP47_EXECUTE),
            ("_checkpoint47_validate_result", _CP47_VALIDATE_RESULT),
            ("_checkpoint47_ledger_snapshot", _CP47_LEDGER_SNAPSHOT),
            (
                "_checkpoint47_validate_ledger_snapshot",
                _CP47_VALIDATE_LEDGER_SNAPSHOT,
            ),
            ("_checkpoint47_live_revalidate", _CP47_LIVE_REVALIDATE),
            ("_exact_uint64_callback", _exact_uint64),
            ("_sealed", True),
        )
        for name, value in bindings:
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("CP48 owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("CP48 owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP48 owners are not pickleable")

    @property
    def certificate(
        self,
    ) -> CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate:
        return self._certificate

    @property
    def source_model_owner(self) -> _CP46_OWNER_TYPE:
        return self._source_model_owner

    def _require_local_surface_binding(self) -> None:
        guard = self._local_surface_guard
        if guard is not self._local_surface_guard_identity:
            raise ValueError("CP48 local surface guard identity changed")
        namespace = globals()
        if namespace.get("_LOCAL_SURFACE_GUARD") is not guard:
            raise ValueError("CP48 local surface guard binding changed")
        if namespace.get("_require_local_surfaces") is not guard:
            raise ValueError("CP48 local surface guard implementation changed")
        if namespace.get(
            "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner"
        ) is not type(self):
            raise ValueError("CP48 owner class binding changed")
        guard()

    def _owner_snapshot(self) -> Tuple[object, ...]:
        self._require_local_surface_binding()
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("CP48 owner seal differs")
        current = (
            self._source_model_owner,
            self._external_byte_source,
            self._backend,
            self._provider,
            self._checkpoint47_owner,
            self._certificate,
            self._certificate_snapshot,
            self._local_surface_guard,
        )
        frozen = (
            self._source_model_owner_identity,
            self._external_byte_source_identity,
            self._backend_identity,
            self._provider_identity,
            self._checkpoint47_owner_identity,
            self._certificate_identity,
            self._certificate_snapshot_identity,
            self._local_surface_guard_identity,
        )
        if any(actual is not expected for actual, expected in zip(current, frozen)):
            raise ValueError("CP48 owner identity changed")
        callbacks = (
            (self._checkpoint47_execute, _CP47_EXECUTE),
            (self._checkpoint47_validate_result, _CP47_VALIDATE_RESULT),
            (self._checkpoint47_ledger_snapshot, _CP47_LEDGER_SNAPSHOT),
            (
                self._checkpoint47_validate_ledger_snapshot,
                _CP47_VALIDATE_LEDGER_SNAPSHOT,
            ),
            (self._checkpoint47_live_revalidate, _CP47_LIVE_REVALIDATE),
            (self._exact_uint64_callback, _exact_uint64),
        )
        if any(actual is not expected for actual, expected in callbacks):
            raise ValueError("CP48 cached callback identity changed")
        self._provider._require_binding()
        checked = _validate_certificate(self._certificate)
        if checked is not self._certificate_identity:
            raise ValueError("CP48 certificate identity differs")
        if tuple(getattr(checked, name) for name in _certificate_fields()) != (
            self._certificate_snapshot
        ):
            raise ValueError("CP48 certificate changed")
        parent_snapshot = _CP47_OWNER_SNAPSHOT(self._checkpoint47_owner)
        if len(parent_snapshot) != len(self._checkpoint47_snapshot) or any(
            actual is not expected
            for actual, expected in zip(parent_snapshot, self._checkpoint47_snapshot)
        ):
            raise ValueError("CP48 CP47 owner binding changed")
        return current

    def execute(
        self,
        run_id: object,
        initialization_index: object,
        draw_index: object,
    ) -> CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult:
        """Execute CP47 once and retain the exact originating byte block."""

        checked_run = self._exact_uint64_callback(run_id, name="run_id")
        checked_initialization = self._exact_uint64_callback(
            initialization_index,
            name="initialization_index",
        )
        checked_draw = self._exact_uint64_callback(draw_index, name="draw_index")
        owner_snapshot = self._owner_snapshot()
        execution_token = None
        try:
            execution_token = self._provider._begin(checked_draw)
            checkpoint47_result = self._checkpoint47_execute(
                self._checkpoint47_owner,
                checked_run,
                checked_initialization,
                checked_draw,
            )
            self._owner_snapshot()
            checked_parent = _CP47_VALIDATE_RESULT_RECORD(
                checkpoint47_result,
                trusted_certificate=self._certificate.checkpoint47_certificate,
                trusted_checkpoint43_certificate=_checkpoint43_certificate(
                    self._certificate.checkpoint47_certificate
                ),
                trusted_owner_runtime_identity=id(self._checkpoint47_owner),
            )
            if checked_parent is not checkpoint47_result:
                raise ValueError("CP48 CP47 validation substituted its result")
            raw = self._provider._claim(
                execution_token,
                self._certificate.source_instance_sha256,
                checked_draw,
                checkpoint47_result.source_full_words,
            )
            if _encode_big_endian_words(checkpoint47_result.source_full_words) != raw:
                raise ValueError("CP48 retained byte/word custody differs")
            result = _make_result(
                self._certificate,
                checkpoint47_result,
                raw,
                owner_runtime_identity=id(self),
            )
            current = self._owner_snapshot()
            if len(current) != len(owner_snapshot) or any(
                actual is not expected
                for actual, expected in zip(current, owner_snapshot)
            ):
                raise ValueError("CP48 owner changed during execution")
            return result
        except BaseException:
            if execution_token is not None:
                self._provider._discard(execution_token)
            raise
        finally:
            if execution_token is not None:
                self._provider._end(execution_token)

    def validate_result(
        self,
        result: object,
    ) -> CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult:
        """Structurally validate retained custody without replaying the source."""

        if (
            type(result)
            is not CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult
        ):
            raise TypeError("result has the wrong exact CP48 type")
        owner_snapshot = self._owner_snapshot()
        record_snapshot = tuple(getattr(result, name) for name in _result_fields())
        checked = _validate_result_record(
            result,
            trusted_certificate=self._certificate,
            trusted_checkpoint47_owner_runtime_identity=id(self._checkpoint47_owner),
            trusted_owner_runtime_identity=id(self),
        )
        parent = self._checkpoint47_validate_result(
            self._checkpoint47_owner,
            result.checkpoint47_result,
        )
        if parent is not result.checkpoint47_result:
            raise ValueError("CP48 CP47 validation substituted its result")
        if tuple(getattr(result, name) for name in _result_fields()) != record_snapshot:
            raise ValueError("CP48 result changed during structural validation")
        current = self._owner_snapshot()
        if len(current) != len(owner_snapshot) or any(
            actual is not expected for actual, expected in zip(current, owner_snapshot)
        ):
            raise ValueError("CP48 owner changed during result validation")
        return checked

    def ledger_snapshot(self) -> _CP47_LEDGER_TYPE:
        """Delegate the sealed draw ledger to CP47, its sole authority."""

        owner_snapshot = self._owner_snapshot()
        snapshot = self._checkpoint47_ledger_snapshot(self._checkpoint47_owner)
        current = self._owner_snapshot()
        if len(current) != len(owner_snapshot) or any(
            actual is not expected for actual, expected in zip(current, owner_snapshot)
        ):
            raise ValueError("CP48 owner changed during ledger snapshot")
        return snapshot

    def validate_ledger_snapshot(self, snapshot: object) -> _CP47_LEDGER_TYPE:
        """Delegate structural/current-ledger validation to CP47."""

        owner_snapshot = self._owner_snapshot()
        checked = self._checkpoint47_validate_ledger_snapshot(
            self._checkpoint47_owner,
            snapshot,
        )
        current = self._owner_snapshot()
        if len(current) != len(owner_snapshot) or any(
            actual is not expected for actual, expected in zip(current, owner_snapshot)
        ):
            raise ValueError("CP48 owner changed during ledger validation")
        return checked

    def revalidate_live_ancestry(
        self,
    ) -> CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate:
        """Explicitly replay CP47's live ancestry revalidation once."""

        owner_snapshot = self._owner_snapshot()
        parent = self._checkpoint47_live_revalidate(self._checkpoint47_owner)
        if parent is not self._certificate.checkpoint47_certificate:
            raise ValueError("CP48 live CP47 certificate identity differs")
        current = self._owner_snapshot()
        if len(current) != len(owner_snapshot) or any(
            actual is not expected for actual, expected in zip(current, owner_snapshot)
        ):
            raise ValueError("CP48 owner changed during live revalidation")
        return self._certificate


_OWNER_TYPE_IDENTITY = (
    CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner
)


def _preflight_factory_arguments(
    source_model_owner: object,
    *,
    source_instance_sha256: object,
    byte_source_profile: object,
    external_byte_source: object,
    byte_source_role_sha256: object,
    provider_role_sha256: object,
    execution_role_sha256: object,
    execution_policy: object,
    max_retired_draws: object,
) -> Tuple[object, ...]:
    if type(source_model_owner) is not _CP46_OWNER_TYPE:
        raise TypeError("source_model_owner has the wrong exact CP46 type")
    source = _require_sha256(
        source_instance_sha256,
        name="source_instance_sha256",
    )
    profile = _exact_profile(byte_source_profile, name="byte_source_profile")
    byte_role = _require_sha256(
        byte_source_role_sha256,
        name="byte_source_role_sha256",
    )
    provider_role = _require_sha256(
        provider_role_sha256,
        name="provider_role_sha256",
    )
    execution_role = _require_sha256(
        execution_role_sha256,
        name="execution_role_sha256",
    )
    if type(execution_policy) is not str:
        raise TypeError("execution_policy must be exact text")
    if execution_policy != _POLICY:
        raise ValueError("only the exported CP48 execution policy is supported")
    maximum = _adapter._bounded_retired_draws(max_retired_draws)
    if profile == _SYSTEM_PROFILE:
        if external_byte_source is not None:
            raise TypeError("system profile requires external_byte_source=None")
        backend = _system_os_urandom_byte_source
    else:
        if not callable(external_byte_source):
            raise TypeError("external profile requires one callable byte source")
        backend = external_byte_source
    return (
        source,
        profile,
        external_byte_source,
        backend,
        byte_role,
        provider_role,
        execution_role,
        maximum,
    )


def certify_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution(
    source_model_owner: object,
    *,
    source_instance_sha256: object,
    byte_source_profile: object,
    external_byte_source: object,
    byte_source_role_sha256: object,
    provider_role_sha256: object,
    execution_role_sha256: object,
    execution_policy: object,
    max_retired_draws: object,
) -> CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner:
    """Certify one sealed CP46/CP47-bound byte-source execution owner."""

    _LOCAL_SURFACE_GUARD()
    if (
        globals().get(
            "CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner"
        )
        is not _OWNER_TYPE_IDENTITY
    ):
        raise ValueError("CP48 owner type surface changed")
    (
        source,
        profile,
        external,
        backend,
        byte_role,
        provider_role,
        execution_role,
        maximum,
    ) = _preflight_factory_arguments(
        source_model_owner,
        source_instance_sha256=source_instance_sha256,
        byte_source_profile=byte_source_profile,
        external_byte_source=external_byte_source,
        byte_source_role_sha256=byte_source_role_sha256,
        provider_role_sha256=provider_role_sha256,
        execution_role_sha256=execution_role_sha256,
        execution_policy=execution_policy,
        max_retired_draws=max_retired_draws,
    )
    provider = _PrivateFullCapsuleProvider(
        source,
        profile,
        backend,
        _construction_token=_PROVIDER_TOKEN,
    )
    checkpoint47_owner = _CP47_CERTIFY(
        source_model_owner,
        provider,
        source_instance_sha256=source,
        provider_role_sha256=provider_role,
        execution_policy=_CP47_POLICY,
        execution_role_sha256=execution_role,
        max_retired_draws=maximum,
    )
    certificate = _make_certificate(
        source_model_owner,
        checkpoint47_owner,
        provider,
        backend,
        external,
        source_instance_sha256=source,
        byte_source_profile=profile,
        byte_source_role_sha256=byte_role,
        provider_role_sha256=provider_role,
        execution_role_sha256=execution_role,
    )
    return CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner(
        source_model_owner,
        external,
        backend,
        provider,
        checkpoint47_owner,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )


def require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution(
    source_model_owner: object,
    owner: object,
    *,
    source_instance_sha256: object,
    byte_source_profile: object,
    external_byte_source: object,
    byte_source_role_sha256: object,
    provider_role_sha256: object,
    execution_role_sha256: object,
    execution_policy: object,
    max_retired_draws: object,
) -> CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner:
    """Require one exact owner and explicitly revalidate live ancestry."""

    if (
        type(owner)
        is not CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner
    ):
        raise TypeError("owner has the wrong exact CP48 type")
    _LOCAL_SURFACE_GUARD()
    if owner.source_model_owner is not source_model_owner:
        raise ValueError("CP48 owner belongs to another CP46 owner")
    (
        source,
        profile,
        external,
        backend,
        byte_role,
        provider_role,
        execution_role,
        maximum,
    ) = _preflight_factory_arguments(
        source_model_owner,
        source_instance_sha256=source_instance_sha256,
        byte_source_profile=byte_source_profile,
        external_byte_source=external_byte_source,
        byte_source_role_sha256=byte_source_role_sha256,
        provider_role_sha256=provider_role_sha256,
        execution_role_sha256=execution_role_sha256,
        execution_policy=execution_policy,
        max_retired_draws=max_retired_draws,
    )
    if owner._external_byte_source is not external:
        raise ValueError("CP48 owner belongs to another external byte source")
    if owner._backend is not backend:
        raise ValueError("CP48 owner belongs to another backend")
    expected = {
        "source_instance_sha256": source,
        "byte_source_profile": profile,
        "byte_source_role_sha256": byte_role,
        "provider_role_sha256": provider_role,
        "execution_role_sha256": execution_role,
        "max_retired_draws": maximum,
    }
    for name, value in expected.items():
        if getattr(owner.certificate, name) != value:
            raise ValueError("CP48 owner binding differs: " + name)
    owner.revalidate_live_ancestry()
    return owner


def validate_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution_certificate(
    source_model_owner: object,
    owner: object,
    *,
    source_instance_sha256: object,
    byte_source_profile: object,
    external_byte_source: object,
    byte_source_role_sha256: object,
    provider_role_sha256: object,
    execution_role_sha256: object,
    execution_policy: object,
    max_retired_draws: object,
) -> CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate:
    """Validate one CP48 certificate against its exact owner and backend."""

    matched = require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution(
        source_model_owner,
        owner,
        source_instance_sha256=source_instance_sha256,
        byte_source_profile=byte_source_profile,
        external_byte_source=external_byte_source,
        byte_source_role_sha256=byte_source_role_sha256,
        provider_role_sha256=provider_role_sha256,
        execution_role_sha256=execution_role_sha256,
        execution_policy=execution_policy,
        max_retired_draws=max_retired_draws,
    )
    return matched.certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_CAPSULE_EXECUTION_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_CAPSULE_EXECUTION_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_BYTE_SOURCE_FULL_CAPSULE_EXECUTION_SCOPE",
    "INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_SYSTEM_OS_URANDOM_OPERATIONAL",
    "INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED",
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
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution",
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution",
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution_certificate",
]
