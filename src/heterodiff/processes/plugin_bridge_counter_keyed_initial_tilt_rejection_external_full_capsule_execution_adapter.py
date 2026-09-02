"""Execute CP43 from one externally supplied complete raw-word capsule.

Checkpoint forty-six shows why randomizing only the two public request
coordinates cannot realize a product-uniform ``L``-word source when ``L>2``.
This module adds the missing *interface*, not the missing probability law.  A
bound external provider is called at most once by an execution and exactly
once if that execution reaches the provider boundary; it must return an exact
tuple of ``L`` uint64 words.  The tuple is ingested
without a lossy map, split by CP43, and passed to CP43's combined semantic map.

The provider's law, totality, independence, physical origin, and freshness are
external premises.  In particular, value-dependent provider failure or
value-dependent downstream refusal can bias the law conditional on a returned
adapter result.  Local draw-identifier retirement is only a bounded one-owner
lifetime property.  It is not global, persistent, cryptographic, or evidence
that distinct identifiers yield independent or distinct values.
Once the API completes a retirement transition, ordinary provider exceptions,
malformed returns, and downstream failures never roll it back.  A provider
that obtains an ambient owner reference and mutates CP47 private state through
same-process introspection is outside this procedural guarantee.

The adapter itself imports and invokes no random, secrets, NumPy, Torch, or OS
entropy facility.  Provider effects lie outside that statement.  Ordinary
operations use CP46's cached binding; current live ancestry revalidation is an
explicit separate operation.  Structural result validation never calls the
provider, CP43 G/H, CP44 execute, CP27 allocation, CP36 prepare, or CP37 decide.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import marshal
import platform
import sys
import threading
from typing import Dict, Mapping, Optional, Tuple

from heterodiff.processes import (
    plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract as _contract,
)
from heterodiff.processes import (
    plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure as _closure,
)
from heterodiff.processes import (
    plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter as _factorized,
)
from heterodiff.processes import (
    plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction as _obstruction,
)


PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_EXECUTION_ADAPTER_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-external-full-capsule-"
    "execution-adapter-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_EXECUTION_ADAPTER_POLICY = (
    "exact-checkpoint46-45-44-43-owner-and-certificate-binding;"
    "at-most-one-direct-L-uint64-word-provider-call-per-execution;"
    "exactly-one-call-if-the-provider-boundary-is-reached;"
    "atomic-bounded-local-draw-retirement-before-provider-call;"
    "adapter-never-rolls-back-a-completed-retirement;"
    "hostile-same-process-private-owner-state-mutation-out-of-scope;"
    "exact-tuple-no-coercion-retry-or-fallback;"
    "identity-full-capsule-ingestion;equal-values-under-distinct-ids-allowed;"
    "exact-checkpoint43-split-join-and-combined-evaluation;"
    "structural-nonreplaying-result-and-ledger-validation;"
    "cached-ordinary-binding-with-explicit-live-ancestry-revalidation;"
    "no-adapter-rng-entropy-allocation-checkpoint44-execute-checkpoint36-prepare-"
    "or-checkpoint37-decide-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_EXECUTION_ADAPTER_SCOPE = (
    "external-direct-word-provider-interface-and-one-shot-local-retirement;"
    "provider-return-interface-has-D^L-elements-and-identity-ingestion-is-bijective;"
    "product-uniform-and-iid-conclusions-only-under-external-law-premises;"
    "returned-result-law-also-requires-total-or-value-independent-downstream-success;"
    "not-provider-totality-success-mass-law-iid-freshness-or-physical-randomness;"
    "not-hostile-same-process-private-owner-state-tamper-resilience;"
    "not-global-cross-owner-cross-process-or-restart-persistent-uniqueness;"
    "not-adapter-or-provider-loaded-code-integrity-provider-authentication-"
    "runtime-portability-or-cryptography;"
    "not-unconditional-output-law-output-TV-bound-concurrent-semantic-safety-"
    "initializer-path-sampler-scientific-model-quality-generality-or-manuscript-claim"
)
INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_INTERFACE_CAPACITY_THEOREM = (
    "the-exact-provider-return-interface-[D]^L-has-cardinality-D^L;"
    "direct-ingestion-is-the-identity-bijection;interface-capacity-does-not-certify-"
    "that-a-provider-realizes-product-uniformity"
)
INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_PRODUCT_LAW_THEOREM = (
    "if-one-successfully-returned-provider-capsule-has-product-uniform-law-U_L;"
    "the-certified-coordinate-partition-yields-independent-product-uniform-V-and-W;"
    "iid-across-calls-additionally-requires-external-iid-provider-draws-on-distinct-ids"
)
INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_SUCCESS_CONDITIONING_CAVEAT = (
    "provider-or-downstream-success-that-depends-on-capsule-value-can-bias-the-law-"
    "conditional-on-a-returned-adapter-result;totality-or-the-required-value-"
    "independence-is-an-external-premise"
)
INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_RAW_WORD_DOMAIN_SIZE = 1 << 64
INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_MIN_RETIRED_DRAWS = 1
INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_MAX_RETIRED_DRAWS = 65536
INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_PROVIDER_MODE = (
    "direct-exact-tuple-of-L-uint64-words"
)

_SCHEMA_VERSION = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_EXECUTION_ADAPTER_SCHEMA_VERSION
_POLICY = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_EXECUTION_ADAPTER_POLICY
_SCOPE = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_EXECUTION_ADAPTER_SCOPE
_CAPACITY_THEOREM = (
    INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_INTERFACE_CAPACITY_THEOREM
)
_PRODUCT_LAW_THEOREM = INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_PRODUCT_LAW_THEOREM
_SUCCESS_CAVEAT = (
    INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_SUCCESS_CONDITIONING_CAVEAT
)
_D = INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_RAW_WORD_DOMAIN_SIZE
_MIN_RETIRED = INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_MIN_RETIRED_DRAWS
_MAX_RETIRED = INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_MAX_RETIRED_DRAWS
_PROVIDER_MODE = INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_PROVIDER_MODE
_ZERO_SHA256 = "0" * 64

_JSON_DUMPS = json.dumps
_SHA256 = hashlib.sha256
_MARSHAL_DUMPS = marshal.dumps
_CODE_FINGERPRINT_FORMAT = (
    "python-marshal-v2-no-reference-table-exact-constant-domain-"
    "process-identity-default-fingerprint-v1"
)
_PYTHON_VERSION = tuple(sys.version_info[:3])
_PYTHON_IMPLEMENTATION = platform.python_implementation()
_LOCK_FACTORY = threading.Lock

_CERTIFICATE_TOKEN = object()
_RECEIPT_TOKEN = object()
_RESULT_TOKEN = object()
_LEDGER_SNAPSHOT_TOKEN = object()
_OWNER_TOKEN = object()

_CP46_OWNER_TYPE = (
    _contract.CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner
)
_CP46_CERT_TYPE = (
    _contract.CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate
)
_CP45_OWNER_TYPE = (
    _obstruction.CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner
)
_CP45_CERT_TYPE = (
    _obstruction.CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate
)
_CP44_OWNER_TYPE = (
    _factorized.CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner
)
_CP44_CERT_TYPE = (
    _factorized.CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate
)
_CP43_OWNER_TYPE = _closure.CounterKeyedInitialTiltRejectionFactorizationClosureOwner
_CP43_CERT_TYPE = (
    _closure.CounterKeyedInitialTiltRejectionFactorizationClosureCertificate
)
_CP43_APPLIED_TYPE = (
    _closure.CounterKeyedInitialTiltRejectionFactorizationClosureAppliedDecision
)

_CP46_VALIDATE_CERTIFICATE = _contract._validate_certificate
_CP46_CACHED_BINDING = _CP46_OWNER_TYPE._require_cached_binding
_CP46_LIVE_REVALIDATE = _CP46_OWNER_TYPE.revalidate_live_ancestry
_CP46_REQUIRE_DEPENDENCY_SURFACES = _contract._require_dependency_surfaces
_CP46_REQUIRE_LOCAL_SURFACES = _contract._require_local_surfaces
_CP46_CERTIFICATE_PROPERTY = _CP46_OWNER_TYPE.certificate
_CP46_PARENT_PROPERTY = _CP46_OWNER_TYPE.source_support_owner
_CP45_CERTIFICATE_PROPERTY = _CP45_OWNER_TYPE.certificate
_CP45_PARENT_PROPERTY = _CP45_OWNER_TYPE.factorized_execution_owner
_CP44_VALIDATE_CERTIFICATE = _factorized._validate_certificate
_CP44_REQUIRE_DEPENDENCY_SURFACES = _factorized._require_dependency_surfaces
_CP44_CERTIFICATE_PROPERTY = _CP44_OWNER_TYPE.certificate
_CP44_PARENT_PROPERTY = _CP44_OWNER_TYPE.factorization_closure_owner
_CP44_PARTITION_FULL_WORDS = _factorized._partition_full_words
_CP44_FULL_WORDS_SHA256 = _factorized._full_words_sha256
_CP44_PROPOSAL_WORDS_SHA256 = _factorized._proposal_words_sha256
_CP44_DECISION_WORDS_SHA256 = _factorized._decision_words_sha256
_CP44_CANONICAL_SEMANTIC_PROJECTION = _factorized._canonical_semantic_projection
_CP44_SEMANTIC_PROJECTION_SHA256 = _factorized._semantic_projection_sha256
_CP43_VALIDATE_CERTIFICATE = _closure._validate_certificate
_CP43_REQUIRE_DEPENDENCY_SURFACES = _closure._require_dependency_surfaces
_CP43_CERTIFICATE_PROPERTY = _CP43_OWNER_TYPE.certificate
_CP43_SPLIT_FULL_WORDS = _CP43_OWNER_TYPE.split_full_words
_CP43_JOIN_FULL_WORDS = _CP43_OWNER_TYPE.join_full_words
_CP43_EVALUATE_AND_APPLY = _CP43_OWNER_TYPE.evaluate_and_apply
_CP43_VALIDATE_APPLIED_RECORD = _closure._validate_applied_record


class PluginBridgeCounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterError(
    ArithmeticError
):
    """Fail-closed CP47 source, custody, or local-retirement error."""


def _canonical(value: object) -> object:
    if value is None or type(value) in (bool, str):
        return value
    if type(value) is int:
        sign = "-" if value < 0 else "+"
        return {"cp47_exact_integer_hex": sign + format(abs(value), "x")}
    if type(value) is tuple:
        return [_canonical(item) for item in value]
    if type(value) is list:
        return [_canonical(item) for item in value]
    if type(value) is dict:
        if not all(type(key) is str for key in value):
            raise TypeError("canonical mappings require exact text keys")
        return {key: _canonical(value[key]) for key in sorted(value)}
    raise TypeError("unsupported CP47 canonical value")


def _semantic_digest(payload: object) -> str:
    encoded = _JSON_DUMPS(
        _canonical(payload),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return _SHA256(encoded).hexdigest()


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    omitted = set(names)
    return {name: values[name] for name in values if name not in omitted}


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(name + " must be lowercase SHA-256 hex")
    return value


def _exact_uint64(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < 0 or value >= _D:
        raise ValueError(name + " must be in [0, 2**64)")
    return value


def _bounded_retired_draws(value: object) -> int:
    if type(value) is not int:
        raise TypeError("max_retired_draws must be an exact integer")
    if value < _MIN_RETIRED or value > _MAX_RETIRED:
        raise ValueError("max_retired_draws is outside the certified bound")
    return value


def _exact_words(value: object, *, name: str, length: int) -> Tuple[int, ...]:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if len(value) != length:
        raise ValueError(name + " has the wrong exact length")
    for index, word in enumerate(value):
        if type(word) is not int:
            raise TypeError("%s[%d] must be an exact integer" % (name, index))
        if word < 0 or word >= _D:
            raise ValueError("%s[%d] is outside uint64" % (name, index))
    return value


def _exact_bool(value: object, expected: bool, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(name + " must be an exact bool")
    if value is not expected:
        raise ValueError(name + " differs")
    return value


def _runtime_default_fingerprint(value: object) -> object:
    if value is None or type(value) in (bool, str, int):
        return value
    if type(value) is tuple:
        return tuple(_runtime_default_fingerprint(item) for item in value)
    if type(value) is dict:
        if not all(type(key) is str for key in value):
            raise TypeError("runtime default mappings require exact text keys")
        return {key: _runtime_default_fingerprint(value[key]) for key in sorted(value)}
    return {
        "runtime_type": type(value).__module__ + "." + type(value).__qualname__,
        "runtime_identity": id(value),
    }


def _code_sha256(function: object) -> str:
    code = getattr(function, "__code__", None)
    code_type = type(_code_sha256.__code__)
    if type(code) is not code_type:
        raise TypeError("runtime digest target lacks an exact Python code object")

    def require_deterministic_constant_domain(value: object) -> None:
        value_type = type(value)
        if value_type in (type(None), bool, int, str):
            return
        if value_type is tuple:
            for item in value:
                require_deterministic_constant_domain(item)
            return
        if value_type is code_type:
            for item in value.co_consts:
                require_deterministic_constant_domain(item)
            return
        raise TypeError("runtime digest code constant has an unsupported exact type")

    require_deterministic_constant_domain(code)
    defaults = getattr(function, "__defaults__", None)
    keyword_defaults = getattr(function, "__kwdefaults__", None)
    if defaults is not None and type(defaults) is not tuple:
        raise TypeError("runtime digest defaults must be an exact tuple or None")
    if keyword_defaults is not None and type(keyword_defaults) is not dict:
        raise TypeError(
            "runtime digest keyword defaults must be an exact mapping or None"
        )
    return _semantic_digest(
        {
            # Marshal's current default format records reference/interning state.
            # Version two omits that reference table, so late string interning
            # cannot change the digest of an unchanged code object.
            "marshal_code": _MARSHAL_DUMPS(code, 2).hex(),
            "defaults": _runtime_default_fingerprint(defaults),
            "keyword_defaults": _runtime_default_fingerprint(keyword_defaults),
        }
    )


def _runtime_sha256() -> str:
    owner_type = globals().get(
        "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner"
    )
    if owner_type is None:
        raise ValueError("CP47 owner type is not loaded")
    owner_methods = (
        "__init__",
        "__setattr__",
        "__delattr__",
        "__reduce_ex__",
        "_require_local_surface_binding",
        "_owner_snapshot",
        "_require_owner_snapshot",
        "_require_ledger_state_locked",
        "_reserve_draw",
        "_require_reservation",
        "revalidate_live_ancestry",
        "execute",
        "validate_result",
        "ledger_snapshot",
        "validate_ledger_snapshot",
        "retired_draw_ledger_snapshot",
        "validate_retired_draw_ledger_snapshot",
    )
    payload = {
        "schema": _SCHEMA_VERSION,
        "python_version": _PYTHON_VERSION,
        "python_implementation": _PYTHON_IMPLEMENTATION,
        "code_fingerprint_format": _CODE_FINGERPRINT_FORMAT,
        "exact_uint64": _code_sha256(_exact_uint64),
        "exact_words": _code_sha256(_exact_words),
    }
    for name in owner_methods:
        payload["owner." + name] = _code_sha256(getattr(owner_type, name))
    frozen = globals().get("_FROZEN_LOCAL_SURFACES", ())
    for name, value in frozen:
        if getattr(value, "__code__", None) is not None:
            payload["local." + name] = _code_sha256(value)
    local_guard = globals().get("_require_local_surfaces")
    if getattr(local_guard, "__code__", None) is not None:
        payload["local._require_local_surfaces"] = _code_sha256(local_guard)
    return _semantic_digest(payload)


def _require_dependency_surfaces() -> None:
    module_expectations = (
        (_contract, "_validate_certificate", _CP46_VALIDATE_CERTIFICATE),
        (_contract, "_require_dependency_surfaces", _CP46_REQUIRE_DEPENDENCY_SURFACES),
        (_contract, "_require_local_surfaces", _CP46_REQUIRE_LOCAL_SURFACES),
        (_factorized, "_validate_certificate", _CP44_VALIDATE_CERTIFICATE),
        (_factorized, "_partition_full_words", _CP44_PARTITION_FULL_WORDS),
        (_factorized, "_full_words_sha256", _CP44_FULL_WORDS_SHA256),
        (_factorized, "_proposal_words_sha256", _CP44_PROPOSAL_WORDS_SHA256),
        (_factorized, "_decision_words_sha256", _CP44_DECISION_WORDS_SHA256),
        (
            _factorized,
            "_canonical_semantic_projection",
            _CP44_CANONICAL_SEMANTIC_PROJECTION,
        ),
        (
            _factorized,
            "_semantic_projection_sha256",
            _CP44_SEMANTIC_PROJECTION_SHA256,
        ),
        (_closure, "_validate_certificate", _CP43_VALIDATE_CERTIFICATE),
        (_closure, "_validate_applied_record", _CP43_VALIDATE_APPLIED_RECORD),
    )
    for module, name, expected in module_expectations:
        if not hasattr(module, name) or getattr(module, name) is not expected:
            raise ValueError("CP47 dependency surface changed: " + name)
    method_expectations = (
        (_CP46_OWNER_TYPE, "_require_cached_binding", _CP46_CACHED_BINDING),
        (_CP46_OWNER_TYPE, "revalidate_live_ancestry", _CP46_LIVE_REVALIDATE),
        (_CP43_OWNER_TYPE, "split_full_words", _CP43_SPLIT_FULL_WORDS),
        (_CP43_OWNER_TYPE, "join_full_words", _CP43_JOIN_FULL_WORDS),
        (_CP43_OWNER_TYPE, "evaluate_and_apply", _CP43_EVALUATE_AND_APPLY),
    )
    for owner_type, name, expected in method_expectations:
        if getattr(owner_type, name) is not expected:
            raise ValueError("CP47 dependency method changed: " + name)
    property_expectations = (
        (_CP46_OWNER_TYPE, "certificate", _CP46_CERTIFICATE_PROPERTY),
        (_CP46_OWNER_TYPE, "source_support_owner", _CP46_PARENT_PROPERTY),
        (_CP45_OWNER_TYPE, "certificate", _CP45_CERTIFICATE_PROPERTY),
        (_CP45_OWNER_TYPE, "factorized_execution_owner", _CP45_PARENT_PROPERTY),
        (_CP44_OWNER_TYPE, "certificate", _CP44_CERTIFICATE_PROPERTY),
        (_CP44_OWNER_TYPE, "factorization_closure_owner", _CP44_PARENT_PROPERTY),
        (_CP43_OWNER_TYPE, "certificate", _CP43_CERTIFICATE_PROPERTY),
    )
    for owner_type, name, expected in property_expectations:
        if getattr(owner_type, name) is not expected:
            raise ValueError("CP47 dependency property changed: " + name)
    _CP46_REQUIRE_LOCAL_SURFACES()
    _CP44_REQUIRE_DEPENDENCY_SURFACES()
    _CP43_REQUIRE_DEPENDENCY_SURFACES()


def _bound_cached_ancestry(
    source_model_owner: object,
    *,
    checked_cp46: Optional[_CP46_CERT_TYPE] = None,
) -> Tuple[object, ...]:
    _require_dependency_surfaces()
    if type(source_model_owner) is not _CP46_OWNER_TYPE:
        raise TypeError("source_model_owner has the wrong exact CP46 type")
    cp46 = (
        _CP46_CACHED_BINDING(source_model_owner)
        if checked_cp46 is None
        else _CP46_VALIDATE_CERTIFICATE(checked_cp46)
    )
    cp45_owner = _CP46_PARENT_PROPERTY.__get__(source_model_owner, _CP46_OWNER_TYPE)
    if type(cp45_owner) is not _CP45_OWNER_TYPE:
        raise TypeError("CP47 CP45 owner has the wrong exact type")
    cp45 = _CP45_CERTIFICATE_PROPERTY.__get__(cp45_owner, _CP45_OWNER_TYPE)
    if type(cp45) is not _CP45_CERT_TYPE:
        raise TypeError("CP47 CP45 certificate has the wrong exact type")
    cp44_owner = _CP45_PARENT_PROPERTY.__get__(cp45_owner, _CP45_OWNER_TYPE)
    if type(cp44_owner) is not _CP44_OWNER_TYPE:
        raise TypeError("CP47 CP44 owner has the wrong exact type")
    cp44 = _CP44_CERTIFICATE_PROPERTY.__get__(cp44_owner, _CP44_OWNER_TYPE)
    cp44 = _CP44_VALIDATE_CERTIFICATE(cp44)
    cp43_owner = _CP44_PARENT_PROPERTY.__get__(cp44_owner, _CP44_OWNER_TYPE)
    if type(cp43_owner) is not _CP43_OWNER_TYPE:
        raise TypeError("CP47 CP43 owner has the wrong exact type")
    cp43 = _CP43_CERTIFICATE_PROPERTY.__get__(cp43_owner, _CP43_OWNER_TYPE)
    cp43 = _CP43_VALIDATE_CERTIFICATE(cp43)
    if cp46.checkpoint45_certificate is not cp45:
        raise ValueError("CP47 CP46-to-CP45 certificate identity differs")
    if cp46.checkpoint45_owner_runtime_identity != id(cp45_owner):
        raise ValueError("CP47 CP46-to-CP45 owner identity differs")
    if cp45.checkpoint44_certificate is not cp44:
        raise ValueError("CP47 CP45-to-CP44 certificate identity differs")
    if cp45.checkpoint44_owner_runtime_identity != id(cp44_owner):
        raise ValueError("CP47 CP45-to-CP44 owner identity differs")
    if cp44.checkpoint43_certificate is not cp43:
        raise ValueError("CP47 CP44-to-CP43 certificate identity differs")
    if cp44.checkpoint43_owner_runtime_identity != id(cp43_owner):
        raise ValueError("CP47 CP44-to-CP43 owner identity differs")
    if cp46.checkpoint44_certificate_sha256 != cp44.certificate_sha256:
        raise ValueError("CP47 CP46/CP44 certificate digests differ")
    if cp46.process_parameter_sha256 != cp44.process_parameter_sha256:
        raise ValueError("CP47 process parameter digest differs")
    if (
        cp46.full_word_count != cp44.full_word_count
        or cp46.proposal_word_count != cp44.proposal_word_count
        or cp46.decision_word_count != cp44.decision_word_count
    ):
        raise ValueError("CP47 CP46/CP44 coordinate counts differ")
    if cp44.full_word_count != cp44.proposal_word_count + cp44.decision_word_count:
        raise ValueError("CP47 full-capsule partition does not close")
    if cp43.proposal_word_count != cp44.proposal_word_count or (
        cp43.decision_word_count != cp44.decision_word_count
    ):
        raise ValueError("CP47 CP43/CP44 coordinate counts differ")
    return (
        cp45_owner,
        cp44_owner,
        cp43_owner,
        cp46,
        cp45,
        cp44,
        cp43,
    )


_CERTIFICATE_POSITIVE_FLAGS = (
    "exact_checkpoint46_owner_binding_certified",
    "exact_transitive_checkpoint45_44_43_binding_certified",
    "exact_full_capsule_coordinate_counts_certified",
    "external_direct_full_capsule_provider_interface_implemented",
    "provider_return_interface_capacity_d_to_l_recorded",
    "identity_full_capsule_ingestion_bijection_certified",
    "provider_invoked_at_most_once_per_execution_certified",
    "provider_invoked_exactly_once_when_boundary_reached_certified",
    "atomic_local_draw_retirement_before_provider_invocation_certified",
    "api_mediated_post_reservation_failure_keeps_draw_retired_certified",
    "duplicate_draw_refuses_before_provider_certified",
    "equal_capsule_values_under_distinct_draw_ids_allowed_certified",
    "exact_tuple_and_exact_uint64_words_required_certified",
    "no_coercion_retry_fallback_or_rollback_certified",
    "checkpoint43_split_join_partition_certified",
    "checkpoint43_combined_entrypoint_once_certified",
    "structural_nonreplaying_result_validation_certified",
    "sealed_provider_receipt_result_and_ledger_custody_certified",
    "adapter_direct_rng_entropy_call_absence_certified",
    "cached_ordinary_binding_boundary_certified",
    "explicit_live_ancestry_revalidation_available",
    "provider_and_downstream_success_conditioning_caveat_recorded",
)
_CERTIFICATE_NEGATIVE_FLAGS = (
    "provider_totality_certified",
    "provider_success_probability_certified",
    "provider_product_uniform_law_certified",
    "provider_iid_across_calls_certified",
    "provider_value_independent_success_certified",
    "downstream_value_independent_success_certified",
    "unconditional_returned_result_law_certified",
    "nondegenerate_live_v_w_independence_certified",
    "physical_randomness_certified",
    "cross_call_value_freshness_certified",
    "global_cross_owner_cross_process_or_restart_uniqueness_certified",
    "concurrent_or_reentrant_semantic_safety_certified",
    "adaptive_retry_with_new_draw_ids_certified",
    "hostile_same_process_private_state_tamper_resilience_certified",
    "adapter_loaded_code_integrity_certified",
    "provider_loaded_code_integrity_certified",
    "provider_cryptographic_authentication_certified",
    "runtime_portable",
    "semantic_output_tv_lower_bound_certified",
    "initializer_admissible",
    "path_admissible",
    "sampler_admissible",
    "scientific_claim_promoted",
    "model_quality_claim_promoted",
    "generality_claim_promoted",
    "manuscript_claim_promoted",
)


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate:
    """Sealed CP46/CP43-bound certificate for one external source interface."""

    schema_version: str
    certificate_scope: str
    execution_policy: str
    provider_mode: str
    provider_role_sha256: str
    execution_role_sha256: str
    source_instance_sha256: str
    provider_callback_runtime_identity: int
    checkpoint46_certificate: _CP46_CERT_TYPE
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
    full_word_count: int
    proposal_word_count: int
    decision_word_count: int
    max_retired_draws: int
    provider_return_interface_support_log2: int
    interface_capacity_theorem: str
    product_law_theorem: str
    success_conditioning_caveat: str
    execution_runtime_sha256: str
    exact_checkpoint46_owner_binding_certified: bool
    exact_transitive_checkpoint45_44_43_binding_certified: bool
    exact_full_capsule_coordinate_counts_certified: bool
    external_direct_full_capsule_provider_interface_implemented: bool
    provider_return_interface_capacity_d_to_l_recorded: bool
    identity_full_capsule_ingestion_bijection_certified: bool
    provider_invoked_at_most_once_per_execution_certified: bool
    provider_invoked_exactly_once_when_boundary_reached_certified: bool
    atomic_local_draw_retirement_before_provider_invocation_certified: bool
    api_mediated_post_reservation_failure_keeps_draw_retired_certified: bool
    duplicate_draw_refuses_before_provider_certified: bool
    equal_capsule_values_under_distinct_draw_ids_allowed_certified: bool
    exact_tuple_and_exact_uint64_words_required_certified: bool
    no_coercion_retry_fallback_or_rollback_certified: bool
    checkpoint43_split_join_partition_certified: bool
    checkpoint43_combined_entrypoint_once_certified: bool
    structural_nonreplaying_result_validation_certified: bool
    sealed_provider_receipt_result_and_ledger_custody_certified: bool
    adapter_direct_rng_entropy_call_absence_certified: bool
    cached_ordinary_binding_boundary_certified: bool
    explicit_live_ancestry_revalidation_available: bool
    provider_and_downstream_success_conditioning_caveat_recorded: bool
    provider_totality_certified: bool
    provider_success_probability_certified: bool
    provider_product_uniform_law_certified: bool
    provider_iid_across_calls_certified: bool
    provider_value_independent_success_certified: bool
    downstream_value_independent_success_certified: bool
    unconditional_returned_result_law_certified: bool
    nondegenerate_live_v_w_independence_certified: bool
    physical_randomness_certified: bool
    cross_call_value_freshness_certified: bool
    global_cross_owner_cross_process_or_restart_uniqueness_certified: bool
    concurrent_or_reentrant_semantic_safety_certified: bool
    adaptive_retry_with_new_draw_ids_certified: bool
    hostile_same_process_private_state_tamper_resilience_certified: bool
    adapter_loaded_code_integrity_certified: bool
    provider_loaded_code_integrity_certified: bool
    provider_cryptographic_authentication_certified: bool
    runtime_portable: bool
    semantic_output_tv_lower_bound_certified: bool
    initializer_admissible: bool
    path_admissible: bool
    sampler_admissible: bool
    scientific_claim_promoted: bool
    model_quality_claim_promoted: bool
    generality_claim_promoted: bool
    manuscript_claim_promoted: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP47 certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("CP47 certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP47 certificate fields are incomplete")
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP47 certificates are not pickleable")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate.__annotations__
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: (
            values["checkpoint46_certificate_sha256"]
            if name == "checkpoint46_certificate"
            else values[name]
        )
        for name in _certificate_fields()
        if name != "certificate_sha256"
    }


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    if set(values) != set(_certificate_fields()):
        raise TypeError("CP47 certificate mapping is incomplete")
    expected_text = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "execution_policy": _POLICY,
        "provider_mode": _PROVIDER_MODE,
        "interface_capacity_theorem": _CAPACITY_THEOREM,
        "product_law_theorem": _PRODUCT_LAW_THEOREM,
        "success_conditioning_caveat": _SUCCESS_CAVEAT,
    }
    for name, expected in expected_text.items():
        if type(values[name]) is not str:
            raise TypeError("certificate.%s must be exact text" % name)
        if values[name] != expected:
            raise ValueError("CP47 certificate text differs: " + name)
    for name in (
        "provider_role_sha256",
        "execution_role_sha256",
        "source_instance_sha256",
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
        "provider_callback_runtime_identity",
        "checkpoint46_owner_runtime_identity",
        "checkpoint45_owner_runtime_identity",
        "checkpoint44_owner_runtime_identity",
        "checkpoint43_owner_runtime_identity",
        "raw_word_domain_size",
        "full_word_count",
        "proposal_word_count",
        "decision_word_count",
        "max_retired_draws",
        "provider_return_interface_support_log2",
    )
    for name in integer_fields:
        if type(values[name]) is not int:
            raise TypeError("certificate.%s must be an exact integer" % name)
    parent = values["checkpoint46_certificate"]
    if type(parent) is not _CP46_CERT_TYPE:
        raise TypeError("checkpoint46_certificate has the wrong exact type")
    parent = _CP46_VALIDATE_CERTIFICATE(parent)
    cp45 = parent.checkpoint45_certificate
    cp44 = cp45.checkpoint44_certificate
    cp44 = _CP44_VALIDATE_CERTIFICATE(cp44)
    cp43 = cp44.checkpoint43_certificate
    cp43 = _CP43_VALIDATE_CERTIFICATE(cp43)
    if parent.passed is not True:
        raise ValueError("CP47 CP46 parent did not pass")
    if parent.external_full_entropy_source_interface_implemented is not False:
        raise ValueError("CP47 CP46 unexpectedly implemented a full source interface")
    if cp44.checkpoint43_split_join_partition_certified is not True:
        raise ValueError("CP47 CP44 split/join partition is not certified")
    if cp44.checkpoint43_combined_entrypoint_once_certified is not True:
        raise ValueError("CP47 CP44 combined-entrypoint contract is not certified")
    expected_owner_identities = {
        "checkpoint45_owner_runtime_identity": parent.checkpoint45_owner_runtime_identity,
        "checkpoint44_owner_runtime_identity": cp45.checkpoint44_owner_runtime_identity,
        "checkpoint43_owner_runtime_identity": cp44.checkpoint43_owner_runtime_identity,
    }
    for name, expected in expected_owner_identities.items():
        if values[name] != expected:
            raise ValueError("CP47 certificate owner identity differs: " + name)
    if values["provider_callback_runtime_identity"] <= 0 or (
        values["checkpoint46_owner_runtime_identity"] <= 0
    ):
        raise ValueError("CP47 runtime identities must be positive")
    expected_integers = {
        "raw_word_domain_size": _D,
        "full_word_count": parent.full_word_count,
        "proposal_word_count": parent.proposal_word_count,
        "decision_word_count": parent.decision_word_count,
        "provider_return_interface_support_log2": 64 * parent.full_word_count,
    }
    for name, expected in expected_integers.items():
        if values[name] != expected:
            raise ValueError("CP47 certificate integer differs: " + name)
    _bounded_retired_draws(values["max_retired_draws"])
    expected_hashes = {
        "checkpoint46_certificate_sha256": parent.certificate_sha256,
        "checkpoint45_certificate_sha256": cp45.certificate_sha256,
        "checkpoint44_certificate_sha256": cp44.certificate_sha256,
        "checkpoint43_certificate_sha256": cp43.certificate_sha256,
        "process_parameter_sha256": cp44.process_parameter_sha256,
        "execution_runtime_sha256": _runtime_sha256(),
    }
    for name, expected in expected_hashes.items():
        if values[name] != expected:
            raise ValueError("CP47 certificate digest differs: " + name)
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="certificate." + name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="certificate." + name)
    _exact_bool(values["passed"], True, name="certificate.passed")
    if values["certificate_sha256"] != _semantic_digest(_certificate_payload(values)):
        raise ValueError("CP47 certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate:
    if (
        type(certificate)
        is not CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate
    ):
        raise TypeError("certificate has the wrong exact CP47 type")
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _make_certificate(
    source_model_owner: _CP46_OWNER_TYPE,
    provider: object,
    *,
    source_instance_sha256: str,
    provider_role_sha256: str,
    execution_role_sha256: str,
    max_retired_draws: int,
    live_cp46: _CP46_CERT_TYPE,
) -> Tuple[
    CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate,
    Tuple[object, ...],
]:
    ancestry = _bound_cached_ancestry(
        source_model_owner,
        checked_cp46=live_cp46,
    )
    cp45_owner, cp44_owner, cp43_owner, cp46, cp45, cp44, cp43 = ancestry
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "execution_policy": _POLICY,
        "provider_mode": _PROVIDER_MODE,
        "provider_role_sha256": provider_role_sha256,
        "execution_role_sha256": execution_role_sha256,
        "source_instance_sha256": source_instance_sha256,
        "provider_callback_runtime_identity": id(provider),
        "checkpoint46_certificate": cp46,
        "checkpoint46_certificate_sha256": cp46.certificate_sha256,
        "checkpoint46_owner_runtime_identity": id(source_model_owner),
        "checkpoint45_certificate_sha256": cp45.certificate_sha256,
        "checkpoint45_owner_runtime_identity": id(cp45_owner),
        "checkpoint44_certificate_sha256": cp44.certificate_sha256,
        "checkpoint44_owner_runtime_identity": id(cp44_owner),
        "checkpoint43_certificate_sha256": cp43.certificate_sha256,
        "checkpoint43_owner_runtime_identity": id(cp43_owner),
        "process_parameter_sha256": cp44.process_parameter_sha256,
        "raw_word_domain_size": _D,
        "full_word_count": cp44.full_word_count,
        "proposal_word_count": cp44.proposal_word_count,
        "decision_word_count": cp44.decision_word_count,
        "max_retired_draws": max_retired_draws,
        "provider_return_interface_support_log2": 64 * cp44.full_word_count,
        "interface_capacity_theorem": _CAPACITY_THEOREM,
        "product_law_theorem": _PRODUCT_LAW_THEOREM,
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
    certificate = (
        CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate(
            **values,
            _construction_token=_CERTIFICATE_TOKEN,
        )
    )
    return certificate, ancestry


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt:
    """Sealed procedural receipt for one successful provider return."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate
    certificate_sha256: str
    provider_mode: str
    provider_role_sha256: str
    source_instance_sha256: str
    provider_callback_runtime_identity: int
    owner_runtime_identity: int
    run_id: int
    initialization_index: int
    draw_index: int
    retirement_ordinal: int
    requested_full_word_count: int
    returned_full_words: Tuple[int, ...]
    returned_full_words_sha256: str
    retirement_chain_sha256: str
    provider_invocation_count: int
    draw_retired_before_provider_invocation: bool
    provider_return_type_exact_tuple: bool
    provider_return_words_exact_uint64: bool
    direct_identity_ingestion: bool
    provider_law_or_totality_certified: bool
    cryptographic_attestation: bool
    receipt_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP47 provider receipts cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RECEIPT_TOKEN:
            raise TypeError("CP47 provider receipts are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP47 provider receipt fields are incomplete")
        _validate_receipt_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP47 provider receipts are not pickleable")


def _receipt_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt.__annotations__
    )


def _receipt_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "certificate", "receipt_sha256")


def _validate_receipt_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate
    ] = None,
) -> None:
    if set(values) != set(_receipt_fields()):
        raise TypeError("CP47 provider receipt mapping is incomplete")
    if (
        type(values["schema_version"]) is not str
        or values["schema_version"] != _SCHEMA_VERSION
    ):
        raise ValueError("CP47 provider receipt schema differs")
    if (
        type(values["provider_mode"]) is not str
        or values["provider_mode"] != _PROVIDER_MODE
    ):
        raise ValueError("CP47 provider receipt mode differs")
    certificate = _validate_certificate(values["certificate"])
    if trusted_certificate is not None and certificate is not trusted_certificate:
        raise ValueError("CP47 provider receipt certificate identity differs")
    _require_sha256(values["certificate_sha256"], name="receipt.certificate_sha256")
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("CP47 provider receipt certificate digest differs")
    _require_sha256(values["provider_role_sha256"], name="receipt.provider_role_sha256")
    if values["provider_role_sha256"] != certificate.provider_role_sha256:
        raise ValueError("CP47 provider receipt role differs")
    _require_sha256(
        values["source_instance_sha256"], name="receipt.source_instance_sha256"
    )
    if values["source_instance_sha256"] != certificate.source_instance_sha256:
        raise ValueError("CP47 provider receipt source instance differs")
    if (
        type(values["provider_callback_runtime_identity"]) is not int
        or values["provider_callback_runtime_identity"]
        != certificate.provider_callback_runtime_identity
    ):
        raise ValueError("CP47 provider receipt callback identity differs")
    owner_identity = values["owner_runtime_identity"]
    if type(owner_identity) is not int or owner_identity <= 0:
        raise ValueError("CP47 provider receipt owner identity differs")
    run = _exact_uint64(values["run_id"], name="receipt.run_id")
    initialization = _exact_uint64(
        values["initialization_index"],
        name="receipt.initialization_index",
    )
    draw = _exact_uint64(values["draw_index"], name="receipt.draw_index")
    del run, initialization, draw
    ordinal = values["retirement_ordinal"]
    if (
        type(ordinal) is not int
        or ordinal < 0
        or ordinal >= certificate.max_retired_draws
    ):
        raise ValueError("CP47 provider receipt ordinal differs")
    if (
        type(values["requested_full_word_count"]) is not int
        or values["requested_full_word_count"] != certificate.full_word_count
    ):
        raise ValueError("CP47 provider receipt word count differs")
    words = _exact_words(
        values["returned_full_words"],
        name="receipt.returned_full_words",
        length=certificate.full_word_count,
    )
    _require_sha256(
        values["returned_full_words_sha256"],
        name="receipt.returned_full_words_sha256",
    )
    if values["returned_full_words_sha256"] != _CP44_FULL_WORDS_SHA256(words):
        raise ValueError("CP47 provider receipt word digest differs")
    _require_sha256(
        values["retirement_chain_sha256"],
        name="receipt.retirement_chain_sha256",
    )
    if type(values["provider_invocation_count"]) is not int or (
        values["provider_invocation_count"] != 1
    ):
        raise ValueError("CP47 provider receipt invocation count differs")
    for name in (
        "draw_retired_before_provider_invocation",
        "provider_return_type_exact_tuple",
        "provider_return_words_exact_uint64",
        "direct_identity_ingestion",
    ):
        _exact_bool(values[name], True, name="receipt." + name)
    for name in ("provider_law_or_totality_certified", "cryptographic_attestation"):
        _exact_bool(values[name], False, name="receipt." + name)
    _require_sha256(values["receipt_sha256"], name="receipt.receipt_sha256")
    if values["receipt_sha256"] != _semantic_digest(_receipt_payload(values)):
        raise ValueError("CP47 provider receipt digest differs")


def _validate_receipt_record(
    receipt: object,
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate
    ] = None,
) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt:
    if (
        type(receipt)
        is not CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt
    ):
        raise TypeError("provider receipt has the wrong exact CP47 type")
    _validate_receipt_values(
        {name: getattr(receipt, name) for name in _receipt_fields()},
        trusted_certificate=trusted_certificate,
    )
    return receipt


def _make_receipt(
    certificate: CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate,
    *,
    run_id: int,
    initialization_index: int,
    draw_index: int,
    retirement_ordinal: int,
    owner_runtime_identity: int,
    retirement_chain_sha256: str,
    full_words: Tuple[int, ...],
) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt:
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "provider_mode": _PROVIDER_MODE,
        "provider_role_sha256": certificate.provider_role_sha256,
        "source_instance_sha256": certificate.source_instance_sha256,
        "provider_callback_runtime_identity": certificate.provider_callback_runtime_identity,
        "owner_runtime_identity": owner_runtime_identity,
        "run_id": run_id,
        "initialization_index": initialization_index,
        "draw_index": draw_index,
        "retirement_ordinal": retirement_ordinal,
        "requested_full_word_count": certificate.full_word_count,
        "returned_full_words": full_words,
        "returned_full_words_sha256": _CP44_FULL_WORDS_SHA256(full_words),
        "retirement_chain_sha256": retirement_chain_sha256,
        "provider_invocation_count": 1,
        "draw_retired_before_provider_invocation": True,
        "provider_return_type_exact_tuple": True,
        "provider_return_words_exact_uint64": True,
        "direct_identity_ingestion": True,
        "provider_law_or_totality_certified": False,
        "cryptographic_attestation": False,
        "receipt_sha256": _ZERO_SHA256,
    }
    values["receipt_sha256"] = _semantic_digest(_receipt_payload(values))
    return CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt(
        **values,
        _construction_token=_RECEIPT_TOKEN,
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult:
    """One sealed successful provider acquisition and CP43 semantic result."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate
    certificate_sha256: str
    provider_receipt: CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt
    provider_receipt_sha256: str
    owner_runtime_identity: int
    run_id: int
    initialization_index: int
    draw_index: int
    retirement_ordinal: int
    retirement_chain_sha256: str
    source_full_words: Tuple[int, ...]
    source_full_words_sha256: str
    source_proposal_words: Tuple[int, ...]
    source_proposal_words_sha256: str
    source_decision_words: Tuple[int, ...]
    source_decision_words_sha256: str
    checkpoint43_applied_decision: _CP43_APPLIED_TYPE
    checkpoint43_applied_decision_sha256: str
    semantic_status: str
    comparison_count: int
    selected_attempt_index: Optional[int]
    selected_configuration_sha256: Optional[str]
    canonical_semantic_projection: Tuple[object, ...]
    canonical_semantic_projection_sha256: str
    draw_retirement_retained: bool
    complete_source_capsule_retained: bool
    full_word_partition_verified: bool
    checkpoint43_combined_evaluated_once: bool
    structural_validation_is_nonreplaying: bool
    provider_law_or_iid_certified: bool
    unconditional_returned_result_law_certified: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP47 results cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("CP47 results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP47 result fields are incomplete")
        _validate_result_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP47 results are not pickleable")


CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionResult = (
    CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult
)


def _result_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult.__annotations__
    )


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "provider_receipt",
        "checkpoint43_applied_decision",
        "result_sha256",
    )


def _validate_result_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate
    ] = None,
    trusted_checkpoint43_certificate: Optional[_CP43_CERT_TYPE] = None,
    trusted_owner_runtime_identity: Optional[int] = None,
) -> None:
    if set(values) != set(_result_fields()):
        raise TypeError("CP47 result mapping is incomplete")
    if (
        type(values["schema_version"]) is not str
        or values["schema_version"] != _SCHEMA_VERSION
    ):
        raise ValueError("CP47 result schema differs")
    certificate = _validate_certificate(values["certificate"])
    if trusted_certificate is not None and certificate is not trusted_certificate:
        raise ValueError("CP47 result certificate identity differs")
    _require_sha256(values["certificate_sha256"], name="result.certificate_sha256")
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("CP47 result certificate digest differs")
    receipt = _validate_receipt_record(
        values["provider_receipt"],
        trusted_certificate=certificate,
    )
    _require_sha256(
        values["provider_receipt_sha256"],
        name="result.provider_receipt_sha256",
    )
    if values["provider_receipt_sha256"] != receipt.receipt_sha256:
        raise ValueError("CP47 result provider receipt digest differs")
    owner_identity = values["owner_runtime_identity"]
    if type(owner_identity) is not int or owner_identity <= 0:
        raise ValueError("CP47 result owner identity differs")
    if owner_identity != receipt.owner_runtime_identity:
        raise ValueError("CP47 result/receipt owner identity differs")
    if trusted_owner_runtime_identity is not None:
        if type(trusted_owner_runtime_identity) is not int:
            raise TypeError("trusted_owner_runtime_identity must be exact")
        if owner_identity != trusted_owner_runtime_identity:
            raise ValueError("CP47 result belongs to another owner")
    _require_sha256(
        values["retirement_chain_sha256"],
        name="result.retirement_chain_sha256",
    )
    if values["retirement_chain_sha256"] != receipt.retirement_chain_sha256:
        raise ValueError("CP47 result/receipt retirement chain differs")
    _exact_uint64(values["run_id"], name="result.run_id")
    _exact_uint64(
        values["initialization_index"],
        name="result.initialization_index",
    )
    _exact_uint64(values["draw_index"], name="result.draw_index")
    ordinal = values["retirement_ordinal"]
    if (
        type(ordinal) is not int
        or ordinal < 0
        or ordinal >= certificate.max_retired_draws
    ):
        raise ValueError("CP47 result retirement ordinal differs")
    for name in ("run_id", "initialization_index", "draw_index", "retirement_ordinal"):
        if getattr(receipt, name) != values[name]:
            raise ValueError("CP47 result/receipt field differs: " + name)
    full_words = _exact_words(
        values["source_full_words"],
        name="result.source_full_words",
        length=certificate.full_word_count,
    )
    proposal_words = _exact_words(
        values["source_proposal_words"],
        name="result.source_proposal_words",
        length=certificate.proposal_word_count,
    )
    decision_words = _exact_words(
        values["source_decision_words"],
        name="result.source_decision_words",
        length=certificate.decision_word_count,
    )
    if full_words != receipt.returned_full_words:
        raise ValueError("CP47 result changed the provider words")
    word_hashes = {
        "source_full_words_sha256": _CP44_FULL_WORDS_SHA256(full_words),
        "source_proposal_words_sha256": _CP44_PROPOSAL_WORDS_SHA256(proposal_words),
        "source_decision_words_sha256": _CP44_DECISION_WORDS_SHA256(decision_words),
    }
    for name, expected in word_hashes.items():
        _require_sha256(values[name], name="result." + name)
        if values[name] != expected:
            raise ValueError("CP47 result word digest differs: " + name)
    cp44 = (
        certificate.checkpoint46_certificate.checkpoint45_certificate.checkpoint44_certificate
    )
    if _CP44_PARTITION_FULL_WORDS(full_words, cp44) != (proposal_words, decision_words):
        raise ValueError("CP47 result full-word partition differs")
    applied = values["checkpoint43_applied_decision"]
    if trusted_checkpoint43_certificate is None:
        cp43 = cp44.checkpoint43_certificate
    else:
        cp43 = trusted_checkpoint43_certificate
    checked_applied = _CP43_VALIDATE_APPLIED_RECORD(
        applied,
        trusted_certificate=cp43,
    )
    if checked_applied is not applied:
        raise ValueError("CP47 CP43 structural validation substituted its result")
    _require_sha256(
        values["checkpoint43_applied_decision_sha256"],
        name="result.checkpoint43_applied_decision_sha256",
    )
    if (
        values["checkpoint43_applied_decision_sha256"]
        != applied.applied_decision_sha256
    ):
        raise ValueError("CP47 result CP43 digest differs")
    if applied.predecision_result.run_id != values["run_id"] or (
        applied.predecision_result.initialization_index
        != values["initialization_index"]
    ):
        raise ValueError("CP47 result CP43 request differs")
    if applied.predecision_result.proposal_words != proposal_words:
        raise ValueError("CP47 result CP43 proposal tuple differs")
    if applied.status in ("selected", "exhausted"):
        if applied.decision_words != decision_words:
            raise ValueError("CP47 result CP43 decision tuple differs")
    elif applied.decision_words is not None:
        raise ValueError("CP47 F36/F37 result retained semantic decision words")
    projection = _CP44_CANONICAL_SEMANTIC_PROJECTION(applied)
    supplied_projection = values["canonical_semantic_projection"]
    if type(supplied_projection) is not tuple or len(supplied_projection) != 4:
        raise TypeError("CP47 result semantic projection must be an exact four-tuple")
    for actual, expected in zip(supplied_projection, projection):
        if expected is None:
            if actual is not None:
                raise TypeError("CP47 result semantic projection None field differs")
        elif type(actual) is not type(expected):
            raise TypeError("CP47 result semantic projection exact type differs")
    if supplied_projection != projection:
        raise ValueError("CP47 result semantic projection differs")
    _require_sha256(
        values["canonical_semantic_projection_sha256"],
        name="result.canonical_semantic_projection_sha256",
    )
    if values["canonical_semantic_projection_sha256"] != (
        _CP44_SEMANTIC_PROJECTION_SHA256(projection)
    ):
        raise ValueError("CP47 result semantic projection digest differs")
    projection_fields = {
        "semantic_status": applied.status,
        "comparison_count": applied.comparison_count,
        "selected_attempt_index": applied.selected_attempt_index,
        "selected_configuration_sha256": applied.selected_configuration_sha256,
    }
    if type(values["semantic_status"]) is not str:
        raise TypeError("result.semantic_status must be exact text")
    if type(values["comparison_count"]) is not int or values["comparison_count"] < 0:
        raise ValueError("result.comparison_count must be an exact nonnegative integer")
    selected_index = values["selected_attempt_index"]
    if selected_index is not None and (
        type(selected_index) is not int or selected_index < 0
    ):
        raise TypeError("result.selected_attempt_index has the wrong exact type")
    selected_digest = values["selected_configuration_sha256"]
    if selected_digest is not None:
        _require_sha256(
            selected_digest,
            name="result.selected_configuration_sha256",
        )
    for name, expected in projection_fields.items():
        if values[name] != expected:
            raise ValueError("CP47 result semantic field differs: " + name)
    for name in (
        "draw_retirement_retained",
        "complete_source_capsule_retained",
        "full_word_partition_verified",
        "checkpoint43_combined_evaluated_once",
        "structural_validation_is_nonreplaying",
    ):
        _exact_bool(values[name], True, name="result." + name)
    for name in (
        "provider_law_or_iid_certified",
        "unconditional_returned_result_law_certified",
    ):
        _exact_bool(values[name], False, name="result." + name)
    _require_sha256(values["result_sha256"], name="result.result_sha256")
    if values["result_sha256"] != _semantic_digest(_result_payload(values)):
        raise ValueError("CP47 result digest differs")


def _validate_result_record(
    result: object,
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate
    ] = None,
    trusted_checkpoint43_certificate: Optional[_CP43_CERT_TYPE] = None,
    trusted_owner_runtime_identity: Optional[int] = None,
) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult:
    if (
        type(result)
        is not CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult
    ):
        raise TypeError("result has the wrong exact CP47 type")
    _validate_result_values(
        {name: getattr(result, name) for name in _result_fields()},
        trusted_certificate=trusted_certificate,
        trusted_checkpoint43_certificate=trusted_checkpoint43_certificate,
        trusted_owner_runtime_identity=trusted_owner_runtime_identity,
    )
    return result


def _make_result(
    certificate: CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate,
    receipt: CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt,
    proposal_words: Tuple[int, ...],
    decision_words: Tuple[int, ...],
    applied: _CP43_APPLIED_TYPE,
) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult:
    projection = _CP44_CANONICAL_SEMANTIC_PROJECTION(applied)
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "provider_receipt": receipt,
        "provider_receipt_sha256": receipt.receipt_sha256,
        "owner_runtime_identity": receipt.owner_runtime_identity,
        "run_id": receipt.run_id,
        "initialization_index": receipt.initialization_index,
        "draw_index": receipt.draw_index,
        "retirement_ordinal": receipt.retirement_ordinal,
        "retirement_chain_sha256": receipt.retirement_chain_sha256,
        "source_full_words": receipt.returned_full_words,
        "source_full_words_sha256": receipt.returned_full_words_sha256,
        "source_proposal_words": proposal_words,
        "source_proposal_words_sha256": _CP44_PROPOSAL_WORDS_SHA256(proposal_words),
        "source_decision_words": decision_words,
        "source_decision_words_sha256": _CP44_DECISION_WORDS_SHA256(decision_words),
        "checkpoint43_applied_decision": applied,
        "checkpoint43_applied_decision_sha256": applied.applied_decision_sha256,
        "semantic_status": applied.status,
        "comparison_count": applied.comparison_count,
        "selected_attempt_index": applied.selected_attempt_index,
        "selected_configuration_sha256": applied.selected_configuration_sha256,
        "canonical_semantic_projection": projection,
        "canonical_semantic_projection_sha256": _CP44_SEMANTIC_PROJECTION_SHA256(
            projection
        ),
        "draw_retirement_retained": True,
        "complete_source_capsule_retained": True,
        "full_word_partition_verified": True,
        "checkpoint43_combined_evaluated_once": True,
        "structural_validation_is_nonreplaying": True,
        "provider_law_or_iid_certified": False,
        "unconditional_returned_result_law_certified": False,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _semantic_digest(_result_payload(values))
    return CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult(
        **values,
        _construction_token=_RESULT_TOKEN,
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot:
    """Sealed bounded snapshot of one owner's locally retired draw IDs."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate
    certificate_sha256: str
    owner_runtime_identity: int
    source_instance_sha256: str
    max_retired_draws: int
    retired_draw_count: int
    retired_draw_rows: Tuple[Tuple[int, int, int, int], ...]
    retired_draw_rows_sha256: str
    retirement_chain_sha256s: Tuple[str, ...]
    retirement_chain_head_sha256: str
    retirement_scope: str
    current_owner_comparison_required: bool
    snapshot_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP47 ledger snapshots cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _LEDGER_SNAPSHOT_TOKEN:
            raise TypeError("CP47 ledger snapshots are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP47 ledger snapshot fields are incomplete")
        _validate_ledger_snapshot_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP47 ledger snapshots are not pickleable")


CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterRetiredDrawLedgerSnapshot = (
    CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot
)


def _ledger_snapshot_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot.__annotations__
    )


def _ledger_rows_sha256(rows: Tuple[Tuple[int, int, int, int], ...]) -> str:
    return _semantic_digest({"domain": "cp47-retired-draw-rows-v1", "rows": rows})


def _retirement_genesis_sha256(
    certificate: CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate,
    owner_runtime_identity: int,
) -> str:
    if type(owner_runtime_identity) is not int or owner_runtime_identity <= 0:
        raise ValueError("retirement owner identity must be a positive exact integer")
    return _semantic_digest(
        {
            "domain": "cp47-retirement-chain-genesis-v1",
            "certificate_sha256": certificate.certificate_sha256,
            "source_instance_sha256": certificate.source_instance_sha256,
            "owner_runtime_identity": owner_runtime_identity,
        }
    )


def _retirement_chain_sha256s(
    certificate: CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate,
    owner_runtime_identity: int,
    rows: Tuple[Tuple[int, int, int, int], ...],
) -> Tuple[str, ...]:
    previous = _retirement_genesis_sha256(certificate, owner_runtime_identity)
    result = []
    for row in rows:
        previous = _semantic_digest(
            {
                "domain": "cp47-retirement-chain-link-v1",
                "previous_sha256": previous,
                "row": row,
            }
        )
        result.append(previous)
    return tuple(result)


def _ledger_snapshot_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "certificate", "snapshot_sha256")


def _validate_ledger_rows(
    rows: object,
    *,
    max_retired_draws: int,
) -> Tuple[Tuple[int, int, int, int], ...]:
    _bounded_retired_draws(max_retired_draws)
    if type(rows) is not tuple:
        raise TypeError("retired_draw_rows must be an exact tuple")
    if len(rows) > max_retired_draws:
        raise ValueError("retired_draw_rows exceed the certified capacity")
    seen = set()
    for expected_ordinal, row in enumerate(rows):
        if type(row) is not tuple or len(row) != 4:
            raise TypeError("each retired draw row must be an exact four-tuple")
        ordinal, run_id, initialization_index, draw_index = row
        if type(ordinal) is not int or ordinal != expected_ordinal:
            raise ValueError("retired draw ordinal sequence differs")
        _exact_uint64(run_id, name="ledger.run_id")
        _exact_uint64(initialization_index, name="ledger.initialization_index")
        _exact_uint64(draw_index, name="ledger.draw_index")
        if draw_index in seen:
            raise ValueError("retired draw index is duplicated")
        seen.add(draw_index)
    return rows


def _validate_ledger_snapshot_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate
    ] = None,
) -> None:
    if set(values) != set(_ledger_snapshot_fields()):
        raise TypeError("CP47 ledger snapshot mapping is incomplete")
    if (
        type(values["schema_version"]) is not str
        or values["schema_version"] != _SCHEMA_VERSION
    ):
        raise ValueError("CP47 ledger snapshot schema differs")
    certificate = _validate_certificate(values["certificate"])
    if trusted_certificate is not None and certificate is not trusted_certificate:
        raise ValueError("CP47 ledger snapshot certificate identity differs")
    _require_sha256(values["certificate_sha256"], name="ledger.certificate_sha256")
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("CP47 ledger snapshot certificate digest differs")
    owner_identity = values["owner_runtime_identity"]
    if type(owner_identity) is not int or owner_identity <= 0:
        raise ValueError("ledger owner identity must be a positive exact integer")
    _require_sha256(
        values["source_instance_sha256"], name="ledger.source_instance_sha256"
    )
    if values["source_instance_sha256"] != certificate.source_instance_sha256:
        raise ValueError("CP47 ledger snapshot source instance differs")
    if type(values["max_retired_draws"]) is not int:
        raise TypeError("ledger max_retired_draws must be an exact integer")
    if values["max_retired_draws"] != certificate.max_retired_draws:
        raise ValueError("CP47 ledger snapshot capacity differs")
    rows = _validate_ledger_rows(
        values["retired_draw_rows"],
        max_retired_draws=certificate.max_retired_draws,
    )
    if type(values["retired_draw_count"]) is not int or (
        values["retired_draw_count"] != len(rows)
    ):
        raise ValueError("CP47 ledger snapshot count differs")
    _require_sha256(
        values["retired_draw_rows_sha256"],
        name="ledger.retired_draw_rows_sha256",
    )
    if values["retired_draw_rows_sha256"] != _ledger_rows_sha256(rows):
        raise ValueError("CP47 ledger row digest differs")
    chains = values["retirement_chain_sha256s"]
    if type(chains) is not tuple or len(chains) != len(rows):
        raise TypeError("ledger retirement chain must be an exact aligned tuple")
    for index, chain in enumerate(chains):
        _require_sha256(chain, name="ledger.retirement_chain_sha256s[%d]" % index)
    expected_chains = _retirement_chain_sha256s(
        certificate,
        owner_identity,
        rows,
    )
    if chains != expected_chains:
        raise ValueError("CP47 ledger retirement chain differs")
    _require_sha256(
        values["retirement_chain_head_sha256"],
        name="ledger.retirement_chain_head_sha256",
    )
    expected_head = (
        expected_chains[-1]
        if expected_chains
        else _retirement_genesis_sha256(certificate, owner_identity)
    )
    if values["retirement_chain_head_sha256"] != expected_head:
        raise ValueError("CP47 ledger retirement chain head differs")
    expected_scope = (
        "bounded-local-one-owner-lifetime-draw-id-retirement;"
        "not-global-persistent-or-value-uniqueness"
    )
    if (
        type(values["retirement_scope"]) is not str
        or values["retirement_scope"] != expected_scope
    ):
        raise ValueError("CP47 ledger retirement scope differs")
    _exact_bool(
        values["current_owner_comparison_required"],
        True,
        name="ledger.current_owner_comparison_required",
    )
    _require_sha256(values["snapshot_sha256"], name="ledger.snapshot_sha256")
    if values["snapshot_sha256"] != _semantic_digest(_ledger_snapshot_payload(values)):
        raise ValueError("CP47 ledger snapshot digest differs")


def _validate_ledger_snapshot_record(
    snapshot: object,
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate
    ] = None,
) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot:
    if (
        type(snapshot)
        is not CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot
    ):
        raise TypeError("ledger snapshot has the wrong exact CP47 type")
    _validate_ledger_snapshot_values(
        {name: getattr(snapshot, name) for name in _ledger_snapshot_fields()},
        trusted_certificate=trusted_certificate,
    )
    return snapshot


def _make_ledger_snapshot(
    certificate: CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate,
    owner_runtime_identity: int,
    rows: Tuple[Tuple[int, int, int, int], ...],
    retirement_chains: Tuple[str, ...],
) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot:
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "owner_runtime_identity": owner_runtime_identity,
        "source_instance_sha256": certificate.source_instance_sha256,
        "max_retired_draws": certificate.max_retired_draws,
        "retired_draw_count": len(rows),
        "retired_draw_rows": rows,
        "retired_draw_rows_sha256": _ledger_rows_sha256(rows),
        "retirement_chain_sha256s": retirement_chains,
        "retirement_chain_head_sha256": (
            retirement_chains[-1]
            if retirement_chains
            else _retirement_genesis_sha256(certificate, owner_runtime_identity)
        ),
        "retirement_scope": (
            "bounded-local-one-owner-lifetime-draw-id-retirement;"
            "not-global-persistent-or-value-uniqueness"
        ),
        "current_owner_comparison_required": True,
        "snapshot_sha256": _ZERO_SHA256,
    }
    values["snapshot_sha256"] = _semantic_digest(_ledger_snapshot_payload(values))
    return CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot(
        **values,
        _construction_token=_LEDGER_SNAPSHOT_TOKEN,
    )


_FROZEN_LOCAL_SURFACE_NAMES = (
    "_contract",
    "_closure",
    "_factorized",
    "_obstruction",
    "_JSON_DUMPS",
    "_SHA256",
    "_MARSHAL_DUMPS",
    "_CODE_FINGERPRINT_FORMAT",
    "_PYTHON_VERSION",
    "_PYTHON_IMPLEMENTATION",
    "_LOCK_FACTORY",
    "_SCHEMA_VERSION",
    "_POLICY",
    "_SCOPE",
    "_CAPACITY_THEOREM",
    "_PRODUCT_LAW_THEOREM",
    "_SUCCESS_CAVEAT",
    "_D",
    "_MIN_RETIRED",
    "_MAX_RETIRED",
    "_PROVIDER_MODE",
    "_ZERO_SHA256",
    "_CERTIFICATE_TOKEN",
    "_RECEIPT_TOKEN",
    "_RESULT_TOKEN",
    "_LEDGER_SNAPSHOT_TOKEN",
    "_OWNER_TOKEN",
    "_CP46_OWNER_TYPE",
    "_CP46_CERT_TYPE",
    "_CP45_OWNER_TYPE",
    "_CP45_CERT_TYPE",
    "_CP44_OWNER_TYPE",
    "_CP44_CERT_TYPE",
    "_CP43_OWNER_TYPE",
    "_CP43_CERT_TYPE",
    "_CP43_APPLIED_TYPE",
    "_CP46_VALIDATE_CERTIFICATE",
    "_CP46_CACHED_BINDING",
    "_CP46_LIVE_REVALIDATE",
    "_CP46_REQUIRE_DEPENDENCY_SURFACES",
    "_CP46_REQUIRE_LOCAL_SURFACES",
    "_CP46_CERTIFICATE_PROPERTY",
    "_CP46_PARENT_PROPERTY",
    "_CP45_CERTIFICATE_PROPERTY",
    "_CP45_PARENT_PROPERTY",
    "_CP44_VALIDATE_CERTIFICATE",
    "_CP44_REQUIRE_DEPENDENCY_SURFACES",
    "_CP44_CERTIFICATE_PROPERTY",
    "_CP44_PARENT_PROPERTY",
    "_CP44_PARTITION_FULL_WORDS",
    "_CP44_FULL_WORDS_SHA256",
    "_CP44_PROPOSAL_WORDS_SHA256",
    "_CP44_DECISION_WORDS_SHA256",
    "_CP44_CANONICAL_SEMANTIC_PROJECTION",
    "_CP44_SEMANTIC_PROJECTION_SHA256",
    "_CP43_VALIDATE_CERTIFICATE",
    "_CP43_REQUIRE_DEPENDENCY_SURFACES",
    "_CP43_CERTIFICATE_PROPERTY",
    "_CP43_SPLIT_FULL_WORDS",
    "_CP43_JOIN_FULL_WORDS",
    "_CP43_EVALUATE_AND_APPLY",
    "_CP43_VALIDATE_APPLIED_RECORD",
    "PluginBridgeCounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterError",
    "_canonical",
    "_semantic_digest",
    "_without",
    "_require_sha256",
    "_exact_uint64",
    "_bounded_retired_draws",
    "_exact_words",
    "_exact_bool",
    "_runtime_default_fingerprint",
    "_code_sha256",
    "_runtime_sha256",
    "_require_dependency_surfaces",
    "_bound_cached_ancestry",
    "_CERTIFICATE_POSITIVE_FLAGS",
    "_CERTIFICATE_NEGATIVE_FLAGS",
    "_certificate_fields",
    "_certificate_payload",
    "_validate_certificate_values",
    "_validate_certificate",
    "_make_certificate",
    "_receipt_fields",
    "_receipt_payload",
    "_validate_receipt_values",
    "_validate_receipt_record",
    "_make_receipt",
    "_result_fields",
    "_result_payload",
    "_validate_result_values",
    "_validate_result_record",
    "_make_result",
    "_ledger_snapshot_fields",
    "_ledger_rows_sha256",
    "_retirement_genesis_sha256",
    "_retirement_chain_sha256s",
    "_ledger_snapshot_payload",
    "_validate_ledger_rows",
    "_validate_ledger_snapshot_values",
    "_validate_ledger_snapshot_record",
    "_make_ledger_snapshot",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionResult",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterRetiredDrawLedgerSnapshot",
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
        raise ValueError("CP47 dependency guard changed")
    if namespace.get("_FROZEN_LOCAL_SURFACES") is not frozen:
        raise ValueError("CP47 frozen local surfaces changed")
    if namespace.get("_FROZEN_LOCAL_SURFACE_NAMES") is not frozen_names:
        raise ValueError("CP47 frozen local surface names changed")
    for name, expected in frozen:
        if namespace.get(name) is not expected:
            raise ValueError("CP47 local surface changed: " + name)
    dependency_guard()


_LOCAL_SURFACE_GUARD = _require_local_surfaces


class CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner:
    """Immutable owner of one provider and one bounded local draw ledger."""

    __slots__ = (
        "_source_model_owner",
        "_source_model_owner_identity",
        "_checkpoint45_owner",
        "_checkpoint45_owner_identity",
        "_checkpoint44_owner",
        "_checkpoint44_owner_identity",
        "_checkpoint43_owner",
        "_checkpoint43_owner_identity",
        "_full_capsule_provider",
        "_full_capsule_provider_identity",
        "_certificate",
        "_certificate_identity",
        "_certificate_snapshot",
        "_certificate_snapshot_identity",
        "_ledger_lock",
        "_ledger_lock_identity",
        "_retired_draw_state",
        "_local_surface_guard",
        "_local_surface_guard_identity",
        "_cached_binding",
        "_live_revalidate",
        "_split_full_words",
        "_join_full_words",
        "_evaluate_and_apply",
        "_validate_applied_record",
        "_partition_full_words",
        "_exact_uint64_callback",
        "_exact_words_callback",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP47 owners cannot be subclassed")

    def __init__(
        self,
        source_model_owner: _CP46_OWNER_TYPE,
        full_capsule_provider: object,
        certificate: CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate,
        ancestry: Tuple[object, ...],
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("CP47 owners require certification")
        if type(source_model_owner) is not _CP46_OWNER_TYPE:
            raise TypeError("source_model_owner has the wrong exact CP46 type")
        if not callable(full_capsule_provider):
            raise TypeError("full_capsule_provider must be callable")
        _LOCAL_SURFACE_GUARD()
        checked = _validate_certificate(certificate)
        if type(ancestry) is not tuple or len(ancestry) != 7:
            raise TypeError("CP47 certified ancestry is malformed")
        current_ancestry = _bound_cached_ancestry(source_model_owner)
        if any(
            actual is not expected
            for actual, expected in zip(current_ancestry, ancestry)
        ):
            raise ValueError("CP47 ancestry changed during certification")
        cp45_owner, cp44_owner, cp43_owner, cp46, cp45, cp44, cp43 = ancestry
        if checked.checkpoint46_certificate is not cp46:
            raise ValueError("CP47 certificate belongs to another CP46 certificate")
        owner_identities = {
            "checkpoint46_owner_runtime_identity": id(source_model_owner),
            "checkpoint45_owner_runtime_identity": id(cp45_owner),
            "checkpoint44_owner_runtime_identity": id(cp44_owner),
            "checkpoint43_owner_runtime_identity": id(cp43_owner),
            "provider_callback_runtime_identity": id(full_capsule_provider),
        }
        for name, expected in owner_identities.items():
            if getattr(checked, name) != expected:
                raise ValueError("CP47 certificate runtime identity differs: " + name)
        certificate_snapshot = tuple(
            getattr(checked, name) for name in _certificate_fields()
        )
        ledger_lock = _LOCK_FACTORY()
        retired_state = ((), ())
        bindings = (
            ("_source_model_owner", source_model_owner),
            ("_source_model_owner_identity", source_model_owner),
            ("_checkpoint45_owner", cp45_owner),
            ("_checkpoint45_owner_identity", cp45_owner),
            ("_checkpoint44_owner", cp44_owner),
            ("_checkpoint44_owner_identity", cp44_owner),
            ("_checkpoint43_owner", cp43_owner),
            ("_checkpoint43_owner_identity", cp43_owner),
            ("_full_capsule_provider", full_capsule_provider),
            ("_full_capsule_provider_identity", full_capsule_provider),
            ("_certificate", checked),
            ("_certificate_identity", checked),
            ("_certificate_snapshot", certificate_snapshot),
            ("_certificate_snapshot_identity", certificate_snapshot),
            ("_ledger_lock", ledger_lock),
            ("_ledger_lock_identity", ledger_lock),
            ("_retired_draw_state", retired_state),
            ("_local_surface_guard", _LOCAL_SURFACE_GUARD),
            ("_local_surface_guard_identity", _LOCAL_SURFACE_GUARD),
            ("_cached_binding", _CP46_CACHED_BINDING),
            ("_live_revalidate", _CP46_LIVE_REVALIDATE),
            ("_split_full_words", _CP43_SPLIT_FULL_WORDS),
            ("_join_full_words", _CP43_JOIN_FULL_WORDS),
            ("_evaluate_and_apply", _CP43_EVALUATE_AND_APPLY),
            ("_validate_applied_record", _CP43_VALIDATE_APPLIED_RECORD),
            ("_partition_full_words", _CP44_PARTITION_FULL_WORDS),
            ("_exact_uint64_callback", _exact_uint64),
            ("_exact_words_callback", _exact_words),
            ("_sealed", True),
        )
        for name, value in bindings:
            object.__setattr__(self, name, value)
        del cp45, cp44, cp43

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("CP47 owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("CP47 owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP47 owners are not pickleable")

    @property
    def certificate(
        self,
    ) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate:
        return self._certificate

    @property
    def source_model_owner(self) -> _CP46_OWNER_TYPE:
        return self._source_model_owner

    def _require_local_surface_binding(self) -> None:
        guard = self._local_surface_guard
        if guard is not self._local_surface_guard_identity:
            raise ValueError("CP47 local surface guard identity changed")
        namespace = globals()
        if namespace.get("_LOCAL_SURFACE_GUARD") is not guard:
            raise ValueError("CP47 local surface guard binding changed")
        if namespace.get("_require_local_surfaces") is not guard:
            raise ValueError("CP47 local surface guard implementation changed")
        if namespace.get(
            "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner"
        ) is not type(self):
            raise ValueError("CP47 owner class binding changed")
        guard()

    def _owner_snapshot(self) -> Tuple[object, ...]:
        self._require_local_surface_binding()
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("CP47 owner seal differs")
        current = (
            self._source_model_owner,
            self._checkpoint45_owner,
            self._checkpoint44_owner,
            self._checkpoint43_owner,
            self._full_capsule_provider,
            self._certificate,
            self._certificate_snapshot,
            self._ledger_lock,
            self._local_surface_guard,
        )
        frozen = (
            self._source_model_owner_identity,
            self._checkpoint45_owner_identity,
            self._checkpoint44_owner_identity,
            self._checkpoint43_owner_identity,
            self._full_capsule_provider_identity,
            self._certificate_identity,
            self._certificate_snapshot_identity,
            self._ledger_lock_identity,
            self._local_surface_guard_identity,
        )
        if any(actual is not expected for actual, expected in zip(current, frozen)):
            raise ValueError("CP47 owner identity changed")
        callbacks = (
            (self._cached_binding, _CP46_CACHED_BINDING),
            (self._live_revalidate, _CP46_LIVE_REVALIDATE),
            (self._split_full_words, _CP43_SPLIT_FULL_WORDS),
            (self._join_full_words, _CP43_JOIN_FULL_WORDS),
            (self._evaluate_and_apply, _CP43_EVALUATE_AND_APPLY),
            (self._validate_applied_record, _CP43_VALIDATE_APPLIED_RECORD),
            (self._partition_full_words, _CP44_PARTITION_FULL_WORDS),
            (self._exact_uint64_callback, _exact_uint64),
            (self._exact_words_callback, _exact_words),
        )
        if any(actual is not expected for actual, expected in callbacks):
            raise ValueError("CP47 cached callback identity changed")
        if not callable(self._full_capsule_provider):
            raise TypeError("CP47 bound provider is no longer callable")
        checked = _validate_certificate(self._certificate)
        if checked is not self._certificate_identity:
            raise ValueError("CP47 certificate identity differs")
        if tuple(getattr(checked, name) for name in _certificate_fields()) != (
            self._certificate_snapshot
        ):
            raise ValueError("CP47 certificate changed")
        ancestry = _bound_cached_ancestry(self._source_model_owner)
        expected_ancestry = (
            self._checkpoint45_owner,
            self._checkpoint44_owner,
            self._checkpoint43_owner,
            checked.checkpoint46_certificate,
            checked.checkpoint46_certificate.checkpoint45_certificate,
            checked.checkpoint46_certificate.checkpoint45_certificate.checkpoint44_certificate,
            checked.checkpoint46_certificate.checkpoint45_certificate.checkpoint44_certificate.checkpoint43_certificate,
        )
        if any(
            actual is not expected
            for actual, expected in zip(ancestry, expected_ancestry)
        ):
            raise ValueError("CP47 cached ancestry identity differs")
        if checked.provider_callback_runtime_identity != id(
            self._full_capsule_provider
        ):
            raise ValueError("CP47 provider callback runtime identity differs")
        with self._ledger_lock:
            self._require_ledger_state_locked()
        return current[:7]

    def _require_owner_snapshot(self, snapshot: Tuple[object, ...]) -> None:
        if type(snapshot) is not tuple or len(snapshot) != 7:
            raise TypeError("CP47 owner snapshot is malformed")
        current = self._owner_snapshot()
        if any(actual is not expected for actual, expected in zip(current, snapshot)):
            raise PluginBridgeCounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterError(
                "CP47 owner changed during operation"
            )

    def _require_ledger_state_locked(
        self,
    ) -> Tuple[Tuple[Tuple[int, int, int, int], ...], Tuple[str, ...],]:
        state = self._retired_draw_state
        if type(state) is not tuple or len(state) != 2:
            raise TypeError("CP47 retired-draw state must be an exact pair")
        rows, retirement_chains = state
        _validate_ledger_rows(
            rows, max_retired_draws=self._certificate.max_retired_draws
        )
        if type(retirement_chains) is not tuple or len(retirement_chains) != len(rows):
            raise TypeError("CP47 retired-draw chain must be an exact aligned tuple")
        for index, chain in enumerate(retirement_chains):
            _require_sha256(chain, name="retirement_chain[%d]" % index)
        expected_chains = _retirement_chain_sha256s(
            self._certificate,
            id(self),
            rows,
        )
        if retirement_chains != expected_chains:
            raise ValueError("CP47 retired-draw chain differs")
        return rows, retirement_chains

    def _reserve_draw(
        self, run_id: int, initialization_index: int, draw_index: int
    ) -> int:
        run_id = self._exact_uint64_callback(run_id, name="run_id")
        initialization_index = self._exact_uint64_callback(
            initialization_index,
            name="initialization_index",
        )
        draw_index = self._exact_uint64_callback(draw_index, name="draw_index")
        with self._ledger_lock:
            rows, retirement_chains = self._require_ledger_state_locked()
            if any(row[3] == draw_index for row in rows):
                raise PluginBridgeCounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterError(
                    "CP47 draw_index is already retired"
                )
            if len(rows) >= self._certificate.max_retired_draws:
                raise PluginBridgeCounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterError(
                    "CP47 retired-draw capacity is exhausted"
                )
            ordinal = len(rows)
            row = (ordinal, run_id, initialization_index, draw_index)
            after_rows = rows + (row,)
            after_chains = _retirement_chain_sha256s(
                self._certificate,
                id(self),
                after_rows,
            )
            object.__setattr__(self, "_retired_draw_state", (after_rows, after_chains))
            checked_rows, checked_chains = self._require_ledger_state_locked()
            if (
                checked_rows[-1] != row
                or len(checked_rows) != ordinal + 1
                or checked_chains[:-1] != retirement_chains
            ):
                raise ValueError("CP47 draw retirement was not atomic")
            return ordinal

    def _require_reservation(
        self,
        run_id: int,
        initialization_index: int,
        draw_index: int,
        retirement_ordinal: int,
        retirement_chain_sha256: object = None,
    ) -> str:
        run_id = self._exact_uint64_callback(run_id, name="run_id")
        initialization_index = self._exact_uint64_callback(
            initialization_index,
            name="initialization_index",
        )
        draw_index = self._exact_uint64_callback(draw_index, name="draw_index")
        if type(retirement_ordinal) is not int or retirement_ordinal < 0:
            raise TypeError("retirement_ordinal must be an exact nonnegative integer")
        if retirement_chain_sha256 is not None:
            _require_sha256(
                retirement_chain_sha256,
                name="retirement_chain_sha256",
            )
        expected = (
            retirement_ordinal,
            run_id,
            initialization_index,
            draw_index,
        )
        with self._ledger_lock:
            rows, retirement_chains = self._require_ledger_state_locked()
            if retirement_ordinal >= len(rows) or rows[retirement_ordinal] != expected:
                raise ValueError("CP47 retained draw reservation differs")
            chain = retirement_chains[retirement_ordinal]
            if retirement_chain_sha256 is not None and chain != retirement_chain_sha256:
                raise ValueError("CP47 retained retirement chain differs")
            return chain

    def revalidate_live_ancestry(
        self,
    ) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate:
        """Explicitly replay CP46's live ancestry boundary exactly once."""

        snapshot = self._owner_snapshot()
        live = self._live_revalidate(self._source_model_owner)
        if live is not self._certificate.checkpoint46_certificate:
            raise ValueError("CP47 live CP46 certificate identity differs")
        self._require_owner_snapshot(snapshot)
        return self._certificate

    def execute(
        self,
        run_id: object,
        initialization_index: object,
        draw_index: object,
    ) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult:
        """Burn one draw ID, call the provider once, and apply CP43 once."""

        checked_run = self._exact_uint64_callback(run_id, name="run_id")
        checked_initialization = self._exact_uint64_callback(
            initialization_index,
            name="initialization_index",
        )
        checked_draw = self._exact_uint64_callback(draw_index, name="draw_index")
        owner_snapshot = self._owner_snapshot()
        certificate = self._certificate
        ordinal = self._reserve_draw(
            checked_run,
            checked_initialization,
            checked_draw,
        )
        retirement_chain = self._require_reservation(
            checked_run,
            checked_initialization,
            checked_draw,
            ordinal,
        )

        returned = self._full_capsule_provider(
            certificate.source_instance_sha256,
            checked_draw,
            certificate.full_word_count,
        )
        full_words = self._exact_words_callback(
            returned,
            name="provider_return",
            length=certificate.full_word_count,
        )
        self._require_owner_snapshot(owner_snapshot)
        self._require_reservation(
            checked_run,
            checked_initialization,
            checked_draw,
            ordinal,
            retirement_chain,
        )
        receipt = _make_receipt(
            certificate,
            run_id=checked_run,
            initialization_index=checked_initialization,
            draw_index=checked_draw,
            retirement_ordinal=ordinal,
            owner_runtime_identity=id(self),
            retirement_chain_sha256=retirement_chain,
            full_words=full_words,
        )
        split = self._split_full_words(self._checkpoint43_owner, full_words)
        self._require_owner_snapshot(owner_snapshot)
        if type(split) is not tuple or len(split) != 2:
            raise TypeError("CP47 CP43 split returned the wrong exact pair")
        proposal_words, decision_words = split
        expected_partition = self._partition_full_words(
            full_words,
            self._certificate.checkpoint46_certificate.checkpoint45_certificate.checkpoint44_certificate,
        )
        if split != expected_partition:
            raise ValueError("CP47 CP43 split differs from the CP44 layout")
        joined = self._join_full_words(
            self._checkpoint43_owner,
            proposal_words,
            decision_words,
        )
        self._require_owner_snapshot(owner_snapshot)
        if joined != full_words:
            raise ValueError("CP47 CP43 split/join round trip differs")
        applied = self._evaluate_and_apply(
            self._checkpoint43_owner,
            checked_run,
            checked_initialization,
            proposal_words,
            decision_words,
        )
        self._require_owner_snapshot(owner_snapshot)
        checked_applied = self._validate_applied_record(
            applied,
            trusted_certificate=self._certificate.checkpoint46_certificate.checkpoint45_certificate.checkpoint44_certificate.checkpoint43_certificate,
        )
        if checked_applied is not applied:
            raise ValueError("CP47 CP43 structural validation substituted its result")
        result = _make_result(
            certificate,
            receipt,
            proposal_words,
            decision_words,
            applied,
        )
        self._require_reservation(
            checked_run,
            checked_initialization,
            checked_draw,
            ordinal,
            retirement_chain,
        )
        self._require_owner_snapshot(owner_snapshot)
        return result

    def validate_result(
        self,
        result: object,
    ) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult:
        """Structurally validate one retained result without replaying source or semantics."""

        if (
            type(result)
            is not CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult
        ):
            raise TypeError("result has the wrong exact CP47 type")
        owner_snapshot = self._owner_snapshot()
        record_snapshot = tuple(getattr(result, name) for name in _result_fields())
        checked = _validate_result_record(
            result,
            trusted_certificate=self._certificate,
            trusted_checkpoint43_certificate=self._certificate.checkpoint46_certificate.checkpoint45_certificate.checkpoint44_certificate.checkpoint43_certificate,
            trusted_owner_runtime_identity=id(self),
        )
        if checked is not result:
            raise ValueError("CP47 result validation substituted its result")
        self._require_reservation(
            result.run_id,
            result.initialization_index,
            result.draw_index,
            result.retirement_ordinal,
            result.retirement_chain_sha256,
        )
        if tuple(getattr(result, name) for name in _result_fields()) != record_snapshot:
            raise ValueError("CP47 result changed during structural validation")
        self._require_owner_snapshot(owner_snapshot)
        return result

    def ledger_snapshot(
        self,
    ) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot:
        """Return one sealed linearizable copy of the bounded local ledger."""

        owner_snapshot = self._owner_snapshot()
        with self._ledger_lock:
            rows, retirement_chains = self._require_ledger_state_locked()
        result = _make_ledger_snapshot(
            self._certificate,
            id(self),
            rows,
            retirement_chains,
        )
        self._require_owner_snapshot(owner_snapshot)
        return result

    def validate_ledger_snapshot(
        self,
        snapshot: object,
    ) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot:
        """Validate a snapshot and require equality with this owner's current ledger."""

        owner_snapshot = self._owner_snapshot()
        checked = _validate_ledger_snapshot_record(
            snapshot,
            trusted_certificate=self._certificate,
        )
        if checked.owner_runtime_identity != id(self):
            raise ValueError("CP47 ledger snapshot belongs to another owner")
        with self._ledger_lock:
            rows, retirement_chains = self._require_ledger_state_locked()
        if checked.retired_draw_rows != rows or (
            checked.retirement_chain_sha256s != retirement_chains
        ):
            raise ValueError("CP47 ledger snapshot is not current")
        self._require_owner_snapshot(owner_snapshot)
        return checked

    def retired_draw_ledger_snapshot(
        self,
    ) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot:
        return self.ledger_snapshot()

    def validate_retired_draw_ledger_snapshot(
        self,
        snapshot: object,
    ) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot:
        return self.validate_ledger_snapshot(snapshot)


_OWNER_TYPE_IDENTITY = (
    CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner
)


def certify_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter(
    source_model_owner: object,
    full_capsule_provider: object,
    *,
    source_instance_sha256: object,
    provider_role_sha256: object,
    execution_policy: object,
    execution_role_sha256: object,
    max_retired_draws: object,
) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner:
    """Certify one CP46-bound external direct-word provider adapter."""

    if type(source_model_owner) is not _CP46_OWNER_TYPE:
        raise TypeError("source_model_owner has the wrong exact CP46 type")
    _LOCAL_SURFACE_GUARD()
    if (
        globals().get(
            "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner"
        )
        is not _OWNER_TYPE_IDENTITY
    ):
        raise ValueError("CP47 owner type surface changed")
    if not callable(full_capsule_provider):
        raise TypeError("full_capsule_provider must be callable")
    source_instance = _require_sha256(
        source_instance_sha256,
        name="source_instance_sha256",
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
        raise ValueError("only the exported CP47 execution policy is supported")
    maximum = _bounded_retired_draws(max_retired_draws)
    live_cp46 = _CP46_LIVE_REVALIDATE(source_model_owner)
    certificate, ancestry = _make_certificate(
        source_model_owner,
        full_capsule_provider,
        source_instance_sha256=source_instance,
        provider_role_sha256=provider_role,
        execution_role_sha256=execution_role,
        max_retired_draws=maximum,
        live_cp46=live_cp46,
    )
    return CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner(
        source_model_owner,
        full_capsule_provider,
        certificate,
        ancestry,
        _construction_token=_OWNER_TOKEN,
    )


def require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter(
    source_model_owner: object,
    full_capsule_provider: object,
    owner: object,
    *,
    source_instance_sha256: object,
    provider_role_sha256: object,
    execution_policy: object,
    execution_role_sha256: object,
    max_retired_draws: object,
) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner:
    """Require one exact owner and explicitly revalidate its live ancestry."""

    if (
        type(owner)
        is not CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner
    ):
        raise TypeError("owner has the wrong exact CP47 type")
    if type(source_model_owner) is not _CP46_OWNER_TYPE:
        raise TypeError("source_model_owner has the wrong exact CP46 type")
    _LOCAL_SURFACE_GUARD()
    if (
        globals().get(
            "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner"
        )
        is not _OWNER_TYPE_IDENTITY
    ):
        raise ValueError("CP47 owner type surface changed")
    if owner.source_model_owner is not source_model_owner:
        raise ValueError("CP47 owner belongs to another CP46 owner")
    if owner._full_capsule_provider is not full_capsule_provider:
        raise ValueError("CP47 owner belongs to another provider callback")
    expected = {
        "source_instance_sha256": _require_sha256(
            source_instance_sha256,
            name="source_instance_sha256",
        ),
        "provider_role_sha256": _require_sha256(
            provider_role_sha256,
            name="provider_role_sha256",
        ),
        "execution_role_sha256": _require_sha256(
            execution_role_sha256,
            name="execution_role_sha256",
        ),
        "max_retired_draws": _bounded_retired_draws(max_retired_draws),
    }
    if type(execution_policy) is not str or execution_policy != _POLICY:
        raise ValueError("CP47 execution policy differs")
    for name, value in expected.items():
        if getattr(owner.certificate, name) != value:
            raise ValueError("CP47 owner binding differs: " + name)
    owner.revalidate_live_ancestry()
    return owner


def validate_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter_certificate(
    source_model_owner: object,
    full_capsule_provider: object,
    owner: object,
    *,
    source_instance_sha256: object,
    provider_role_sha256: object,
    execution_policy: object,
    execution_role_sha256: object,
    max_retired_draws: object,
) -> CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate:
    """Validate one CP47 certificate against its exact owner and provider."""

    matched = require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter(
        source_model_owner,
        full_capsule_provider,
        owner,
        source_instance_sha256=source_instance_sha256,
        provider_role_sha256=provider_role_sha256,
        execution_policy=execution_policy,
        execution_role_sha256=execution_role_sha256,
        max_retired_draws=max_retired_draws,
    )
    return matched.certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_EXECUTION_ADAPTER_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_EXECUTION_ADAPTER_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_EXECUTION_ADAPTER_SCOPE",
    "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_INTERFACE_CAPACITY_THEOREM",
    "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_PRODUCT_LAW_THEOREM",
    "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_SUCCESS_CONDITIONING_CAVEAT",
    "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_RAW_WORD_DOMAIN_SIZE",
    "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_MIN_RETIRED_DRAWS",
    "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_MAX_RETIRED_DRAWS",
    "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_PROVIDER_MODE",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterRetiredDrawLedgerSnapshot",
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterError",
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter",
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter",
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter_certificate",
]
