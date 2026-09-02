"""Certify the fixed-address source-support obstruction behind CP44.

Checkpoint forty-four consumes a deterministic, same-runtime CP27 capsule at
an exact ``(run_id, initialization_index)`` address.  It is therefore wrong to
identify that live fixed-request capsule with the counterfactual product-
uniform word family used by checkpoints thirty-six, forty-one, forty-three,
and forty-four.

Let ``D=2**64`` and let ``L`` be the number of uint64 words in the CP44
capsule.  Conditional on a fixed request returning one capsule ``z``, its
source law is the point mass ``delta_z`` and

``TV(delta_z, Uniform([D]**L)) = 1 - D**(-L)``.

More generally, a deterministic successful-capsule map driven by at most
``k`` free uint64 coordinates has support at most ``D**k``.  Conditional on
success, its distance from product uniform is at least
``1-D**(k-L)`` when ``L>k``.  Conditioning cannot enlarge support, so this
statement needs no success/value-independence premise.

This is a source-space obstruction only.  Data processing supplies an upper
bound after a semantic map, never the corresponding lower bound; a constant
map can erase the entire source discrepancy.  This module performs no source
allocation and no CP43 or CP44 semantic execution.  It supplies no refusal
probability, live product-uniform law, nondegenerate V/W independence,
physical-randomness, cryptographic, initializer, path, sampler, or scientific
claim.  Inherited ancestry validation may execute a deterministic local Philox
runtime probe; the narrower certified RNG statement is no caller/global RNG
state mutation, not absence of every transitive RNG call.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import platform
import sys
from typing import Dict, Mapping, Tuple

from heterodiff.processes import (
    plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter as _adapter,
)


PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_SUPPORT_OBSTRUCTION_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-fixed-address-source-"
    "support-obstruction-v2"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_SUPPORT_OBSTRUCTION_POLICY = (
    "exact-checkpoint44-and-transitive-checkpoint36-27-26-binding;"
    "same-runtime-fixed-address-deterministic-capsule-support;"
    "fixed-returned-request-point-mass-TV-identity;"
    "k-free-uint64-coordinate-support-TV-lower-bound;"
    "conditional-success-support-does-not-require-success-value-independence;"
    "symbolic-exponents-only-no-enormous-denominator-materialization;"
    "source-space-only-no-output-TV-lower-bound;"
    "no-source-allocation-or-semantic-execution;"
    "no-caller-global-rng-mutation;"
    "ancestry-validation-may-run-deterministic-local-Philox-runtime-probe-v2"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_SUPPORT_OBSTRUCTION_SCOPE = (
    "fixed-owner-runtime-source-support-obstruction;"
    "returned-fixed-request-and-conditional-success-laws-only;"
    "current-CP44-request-surface-has-two-uint64-coordinates;"
    "not-live-product-uniformity-or-nondegenerate-V-W-independence;"
    "not-allocation-success-value-independence-or-refusal-probability;"
    "not-output-TV-lower-bound-or-output-discrepancy;"
    "not-hidden-entropy-runtime-fault-or-random-environment-accounting;"
    "ancestry-validation-may-run-deterministic-local-Philox-runtime-probe-"
    "without-caller-global-rng-state-mutation;"
    "not-physical-randomness-freshness-portability-or-cryptography;"
    "not-initializer-path-sampler-scientific-model-quality-or-generality-evidence"
)
INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_TV_THEOREM = (
    "for-one-fixed-owner-runtime-and-exact-request-that-returns-one-L-word-"
    "capsule-z;the-canonical-live-source-law-is-delta_z-and-"
    "TV(delta_z,U_L)=1-D^(-L);D=2^64"
)
INITIAL_TILT_REJECTION_FREE_REQUEST_SOURCE_SUPPORT_TV_THEOREM = (
    "for-any-deterministic-partial-successful-capsule-map-from-a-subset-of-"
    "D^k-to-D^L-and-any-request-law-with-positive-success-probability;the-"
    "conditional-success-source-support-is-at-most-D^k-and-"
    "TV(nu_success,U_L)>=1-D^(k-L)-when-L>k;for-L<=k-the-universal-bound-is-0"
)
INITIAL_TILT_REJECTION_SOURCE_TO_OUTPUT_TV_NONCONVERSE = (
    "data-processing-gives-TV(H#nu,H#U)<=TV(nu,U)-only;no-output-TV-lower-"
    "bound-follows-and-a-constant-H-can-make-the-output-distance-zero"
)
INITIAL_TILT_REJECTION_FIXED_ADDRESS_RAW_WORD_DOMAIN_SIZE = 1 << 64
INITIAL_TILT_REJECTION_FIXED_ADDRESS_CURRENT_REQUEST_COORDINATES = 2

_SCHEMA_VERSION = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_SUPPORT_OBSTRUCTION_SCHEMA_VERSION
_POLICY = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_SUPPORT_OBSTRUCTION_POLICY
_SCOPE = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_SUPPORT_OBSTRUCTION_SCOPE
_FIXED_THEOREM = INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_TV_THEOREM
_SUPPORT_THEOREM = INITIAL_TILT_REJECTION_FREE_REQUEST_SOURCE_SUPPORT_TV_THEOREM
_NONCONVERSE = INITIAL_TILT_REJECTION_SOURCE_TO_OUTPUT_TV_NONCONVERSE
_D = INITIAL_TILT_REJECTION_FIXED_ADDRESS_RAW_WORD_DOMAIN_SIZE
_CURRENT_REQUEST_COORDINATES = (
    INITIAL_TILT_REJECTION_FIXED_ADDRESS_CURRENT_REQUEST_COORDINATES
)
_ZERO_SHA256 = "0" * 64

_CERTIFICATE_TOKEN = object()
_BOUND_TOKEN = object()
_OWNER_TOKEN = object()

_CP44_OWNER_TYPE = (
    _adapter.CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner
)
_CP44_CERT_TYPE = (
    _adapter.CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate
)
_CP44_VALIDATE_CERTIFICATE = _adapter._validate_certificate
_CP44_OWNER_SNAPSHOT = _CP44_OWNER_TYPE._owner_snapshot
_CP44_REQUIRE_OWNER_SNAPSHOT = _CP44_OWNER_TYPE._require_owner_snapshot
_CP44_REQUIRE_DEPENDENCY_SURFACES = _adapter._require_dependency_surfaces
_CP44_CERTIFICATE_PROPERTY = _CP44_OWNER_TYPE.certificate


class PluginBridgeCounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionError(
    ArithmeticError
):
    """Fail-closed CP45 fixed-address source-support custody error."""


def _require_dependency_surfaces() -> None:
    """Refuse changed CP44 call surfaces before invoking any parent callback."""

    module_expectations = (
        (_adapter, "_validate_certificate", _CP44_VALIDATE_CERTIFICATE),
        (
            _adapter,
            "_require_dependency_surfaces",
            _CP44_REQUIRE_DEPENDENCY_SURFACES,
        ),
    )
    for module, name, expected in module_expectations:
        if not hasattr(module, name) or getattr(module, name) is not expected:
            raise ValueError("CP45 dependency surface changed: %s" % name)
    method_expectations = (
        (_CP44_OWNER_TYPE, "_owner_snapshot", _CP44_OWNER_SNAPSHOT),
        (
            _CP44_OWNER_TYPE,
            "_require_owner_snapshot",
            _CP44_REQUIRE_OWNER_SNAPSHOT,
        ),
    )
    for owner_type, name, expected in method_expectations:
        if getattr(owner_type, name) is not expected:
            raise ValueError("CP45 parent method changed: %s" % name)
    if _CP44_OWNER_TYPE.certificate is not _CP44_CERTIFICATE_PROPERTY:
        raise ValueError("CP45 parent property changed: certificate")


def _canonical(value: object) -> object:
    if value is None or type(value) in (bool, str):
        return value
    if type(value) is int:
        sign = "-" if value < 0 else "+"
        return {"cp45_exact_integer_hex": sign + format(abs(value), "x")}
    if type(value) is tuple:
        return [_canonical(item) for item in value]
    if type(value) is dict:
        return {str(key): _canonical(item) for key, item in value.items()}
    if hasattr(value, "certificate_sha256"):
        return {
            "type": type(value).__module__ + "." + type(value).__qualname__,
            "certificate_sha256": getattr(value, "certificate_sha256"),
        }
    raise TypeError("unsupported value in CP45 semantic digest")


def _semantic_digest(payload: object) -> str:
    encoded = json.dumps(
        _canonical(payload), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(name + " must be lowercase SHA-256 text")
    return value


def _exact_nonnegative_integer(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < 0:
        raise ValueError(name + " must be nonnegative")
    return value


def _exact_bool(value: object, expected: bool, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(name + " must be an exact bool")
    if value is not expected:
        raise ValueError(name + " differs from the frozen claim boundary")
    return value


def _runtime_sha256() -> str:
    return _semantic_digest(
        {
            "domain": "cp45-fixed-address-source-support-runtime-v1",
            "python": tuple(sys.version_info[:3]),
            "implementation": platform.python_implementation(),
            "schema": _SCHEMA_VERSION,
            "policy": _POLICY,
            "scope": _SCOPE,
            "fixed_theorem": _FIXED_THEOREM,
            "support_theorem": _SUPPORT_THEOREM,
            "nonconverse": _NONCONVERSE,
        }
    )


def _support_bound_values(
    full_word_count: object,
    free_uint64_request_coordinates: object,
) -> Mapping[str, object]:
    """Return the exact symbolic support bound without materializing powers."""

    length = _exact_nonnegative_integer(full_word_count, name="full_word_count")
    free = _exact_nonnegative_integer(
        free_uint64_request_coordinates,
        name="free_uint64_request_coordinates",
    )
    gap = max(length - free, 0)
    strict = gap > 0
    fixed_exact = free == 0
    if gap:
        formula = "1-2^(-64*%d)" % gap
    else:
        formula = "0"
    if fixed_exact and length:
        fixed_formula = "1-2^(-64*%d)" % length
    else:
        fixed_formula = "0"
    return {
        "full_word_count": length,
        "free_uint64_request_coordinates": free,
        "source_support_log2_upper_bound": 64 * free,
        "product_uniform_support_log2": 64 * length,
        "support_exponent_gap": gap,
        "tv_lower_bound_formula": formula,
        "strict_product_uniform_obstruction": strict,
        "fixed_returned_request_exact_tv_certified": fixed_exact,
        "fixed_returned_request_exact_tv_formula": fixed_formula,
        "within_current_cp44_request_surface": free <= _CURRENT_REQUEST_COORDINATES,
    }


_CERTIFICATE_POSITIVE_FLAGS = (
    "exact_checkpoint44_owner_binding_certified",
    "exact_transitive_checkpoint36_27_26_binding_certified",
    "same_runtime_fixed_address_replay_inherited",
    "within_capsule_logical_coordinate_distinctness_inherited",
    "cp43_split_join_coordinate_permutation_inherited",
    "fixed_returned_request_point_mass_theorem_certified",
    "conditional_success_support_theorem_certified",
    "conditioning_cannot_enlarge_support_certified",
    "support_exponents_stored_without_huge_denominators",
    "source_to_output_tv_nonconverse_recorded",
    "source_and_semantic_operation_free_certification_and_bound_description_certified",
    "no_caller_global_rng_state_mutation_certified",
)
_CERTIFICATE_NEGATIVE_FLAGS = (
    "live_product_uniform_source_certified",
    "nondegenerate_live_v_w_independence_certified",
    "allocation_success_value_independence_certified",
    "allocation_or_refusal_probability_certified",
    "unconditional_adapter_law_certified",
    "semantic_output_tv_lower_bound_certified",
    "transitive_rng_call_absence_certified",
    "hidden_entropy_or_random_runtime_accounted",
    "physical_randomness_certified",
    "cross_call_freshness_certified",
    "loaded_code_integrity_certified",
    "runtime_portable",
    "cryptographic_authentication",
    "initializer_admissible",
    "path_admissible",
    "sampler_admissible",
    "scientific_claim_promoted",
    "model_quality_claim_promoted",
    "generality_claim_promoted",
)
_CERTIFICATE_SHA256_FIELDS = (
    "obstruction_role_sha256",
    "checkpoint44_certificate_sha256",
    "checkpoint36_certificate_sha256",
    "checkpoint36_word_family_hypothesis_sha256",
    "checkpoint27_certificate_sha256",
    "checkpoint26_certificate_sha256",
    "process_parameter_sha256",
    "obstruction_runtime_sha256",
    "certificate_sha256",
)
_CERTIFICATE_INTEGER_FIELDS = (
    "checkpoint44_owner_runtime_identity",
    "raw_word_domain_size",
    "full_word_count",
    "current_request_coordinate_count",
    "product_uniform_support_log2",
    "fixed_request_tv_exponent_gap",
    "one_free_request_tv_exponent_gap",
    "two_free_request_tv_exponent_gap",
)
_CERTIFICATE_TEXT_FIELDS = (
    "schema_version",
    "certificate_scope",
    "obstruction_policy",
    "fixed_request_tv_theorem",
    "free_request_support_tv_theorem",
    "source_to_output_tv_nonconverse",
)


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate:
    """Sealed CP44-bound source-support obstruction certificate."""

    schema_version: str
    certificate_scope: str
    obstruction_policy: str
    obstruction_role_sha256: str
    checkpoint44_certificate: _CP44_CERT_TYPE
    checkpoint44_certificate_sha256: str
    checkpoint44_owner_runtime_identity: int
    checkpoint36_certificate_sha256: str
    checkpoint36_word_family_hypothesis_sha256: str
    checkpoint27_certificate_sha256: str
    checkpoint26_certificate_sha256: str
    process_parameter_sha256: str
    raw_word_domain_size: int
    full_word_count: int
    current_request_coordinate_count: int
    product_uniform_support_log2: int
    fixed_request_tv_exponent_gap: int
    one_free_request_tv_exponent_gap: int
    two_free_request_tv_exponent_gap: int
    fixed_request_tv_theorem: str
    free_request_support_tv_theorem: str
    source_to_output_tv_nonconverse: str
    obstruction_runtime_sha256: str
    exact_checkpoint44_owner_binding_certified: bool
    exact_transitive_checkpoint36_27_26_binding_certified: bool
    same_runtime_fixed_address_replay_inherited: bool
    within_capsule_logical_coordinate_distinctness_inherited: bool
    cp43_split_join_coordinate_permutation_inherited: bool
    fixed_returned_request_point_mass_theorem_certified: bool
    conditional_success_support_theorem_certified: bool
    conditioning_cannot_enlarge_support_certified: bool
    support_exponents_stored_without_huge_denominators: bool
    source_to_output_tv_nonconverse_recorded: bool
    source_and_semantic_operation_free_certification_and_bound_description_certified: bool
    no_caller_global_rng_state_mutation_certified: bool
    live_product_uniform_source_certified: bool
    nondegenerate_live_v_w_independence_certified: bool
    allocation_success_value_independence_certified: bool
    allocation_or_refusal_probability_certified: bool
    unconditional_adapter_law_certified: bool
    semantic_output_tv_lower_bound_certified: bool
    transitive_rng_call_absence_certified: bool
    hidden_entropy_or_random_runtime_accounted: bool
    physical_randomness_certified: bool
    cross_call_freshness_certified: bool
    loaded_code_integrity_certified: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    initializer_admissible: bool
    path_admissible: bool
    sampler_admissible: bool
    scientific_claim_promoted: bool
    model_quality_claim_promoted: bool
    generality_claim_promoted: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP45 certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("CP45 certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP45 certificate fields are incomplete")
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP45 certificates are not pickleable")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate.__annotations__
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: (
            values["checkpoint44_certificate_sha256"]
            if name == "checkpoint44_certificate"
            else values[name]
        )
        for name in _certificate_fields()
        if name != "certificate_sha256"
    }


def _validate_parent_claims(parent: _CP44_CERT_TYPE) -> None:
    cp36 = parent.checkpoint36_certificate
    hypothesis = cp36.word_family_hypothesis
    cp27 = parent.checkpoint27_certificate
    cp26 = cp27.checkpoint26_certificate
    if parent.raw_word_domain_size != _D:
        raise ValueError("CP44 raw-word domain differs")
    if parent.full_word_count <= _CURRENT_REQUEST_COORDINATES:
        raise ValueError(
            "CP44 capsule is too short for the strict two-input obstruction"
        )
    if parent.live_philox_source_law_certified is not False:
        raise ValueError("CP44 unexpectedly certifies a live source law")
    if parent.live_v_w_independence_certified is not False:
        raise ValueError("CP44 unexpectedly certifies live V/W independence")
    if hypothesis.actual_live_uniformity_certified is not False:
        raise ValueError("CP36 unexpectedly certifies live uniformity")
    if hypothesis.actual_live_independence_certified is not False:
        raise ValueError("CP36 unexpectedly certifies live independence")
    if hypothesis.physical_randomness_certified is not False:
        raise ValueError("CP36 unexpectedly certifies physical randomness")
    if cp27.exact_parent_result_replay_certified is not True:
        raise ValueError("CP27 same-runtime parent replay is not certified")
    if cp27.within_allocation_unique_addresses_certified is not True:
        raise ValueError("CP27 within-allocation address uniqueness is not certified")
    if cp27.statistical_independence_certified is not False:
        raise ValueError("CP27 unexpectedly certifies statistical independence")
    if cp27.physical_randomness_certified is not False:
        raise ValueError("CP27 unexpectedly certifies physical randomness")
    if cp26.same_runtime_prefix_replay_certified is not True:
        raise ValueError("CP26 same-runtime prefix replay is not certified")
    if cp26.exact_uniform_law_certified is not False:
        raise ValueError("CP26 unexpectedly certifies an exact uniform law")
    if cp26.statistical_independence_certified is not False:
        raise ValueError("CP26 unexpectedly certifies independence")


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    if set(values) != set(_certificate_fields()):
        raise TypeError("CP45 certificate mapping is incomplete")
    for name in _CERTIFICATE_TEXT_FIELDS:
        if type(values[name]) is not str:
            raise TypeError("CP45 certificate field %s must be exact text" % name)
    for name in _CERTIFICATE_SHA256_FIELDS:
        _require_sha256(values[name], name="certificate." + name)
    for name in _CERTIFICATE_INTEGER_FIELDS:
        if type(values[name]) is not int:
            raise TypeError("CP45 certificate field %s must be an exact integer" % name)
    if type(values["checkpoint44_certificate"]) is not _CP44_CERT_TYPE:
        raise TypeError("CP45 checkpoint44_certificate has the wrong exact type")
    for name in _CERTIFICATE_POSITIVE_FLAGS + _CERTIFICATE_NEGATIVE_FLAGS + ("passed",):
        if type(values[name]) is not bool:
            raise TypeError("CP45 certificate field %s must be an exact bool" % name)
    if values["schema_version"] != _SCHEMA_VERSION:
        raise ValueError("CP45 certificate schema differs")
    if values["certificate_scope"] != _SCOPE:
        raise ValueError("CP45 certificate scope differs")
    if values["obstruction_policy"] != _POLICY:
        raise ValueError("CP45 certificate policy differs")
    _require_dependency_surfaces()
    parent = _CP44_VALIDATE_CERTIFICATE(values["checkpoint44_certificate"])
    _validate_parent_claims(parent)
    expected = {
        "checkpoint44_certificate_sha256": parent.certificate_sha256,
        "checkpoint36_certificate_sha256": parent.checkpoint36_certificate_sha256,
        "checkpoint36_word_family_hypothesis_sha256": (
            parent.checkpoint36_certificate.word_family_hypothesis.hypothesis_sha256
        ),
        "checkpoint27_certificate_sha256": parent.checkpoint27_certificate_sha256,
        "checkpoint26_certificate_sha256": (
            parent.checkpoint27_certificate.checkpoint26_certificate_sha256
        ),
        "process_parameter_sha256": parent.process_parameter_sha256,
        "raw_word_domain_size": _D,
        "full_word_count": parent.full_word_count,
        "current_request_coordinate_count": _CURRENT_REQUEST_COORDINATES,
        "product_uniform_support_log2": 64 * parent.full_word_count,
        "fixed_request_tv_exponent_gap": parent.full_word_count,
        "one_free_request_tv_exponent_gap": parent.full_word_count - 1,
        "two_free_request_tv_exponent_gap": parent.full_word_count - 2,
        "fixed_request_tv_theorem": _FIXED_THEOREM,
        "free_request_support_tv_theorem": _SUPPORT_THEOREM,
        "source_to_output_tv_nonconverse": _NONCONVERSE,
        "obstruction_runtime_sha256": _runtime_sha256(),
        "passed": True,
    }
    for name, expected_value in expected.items():
        if type(expected_value) is int and type(values[name]) is not int:
            raise TypeError("CP45 certificate field %s must be an exact integer" % name)
        if type(expected_value) is str and type(values[name]) is not str:
            raise TypeError("CP45 certificate field %s must be exact text" % name)
        if values[name] != expected_value:
            raise ValueError("CP45 certificate field %s differs" % name)
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="certificate." + name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="certificate." + name)
    _exact_bool(values["passed"], True, name="certificate.passed")
    if values["certificate_sha256"] != _semantic_digest(_certificate_payload(values)):
        raise ValueError("CP45 certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate:
    if type(certificate) is not (
        CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate
    ):
        raise TypeError("certificate has the wrong exact CP45 type")
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _make_certificate(
    parent_owner: _CP44_OWNER_TYPE,
    role: str,
) -> CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate:
    _require_dependency_surfaces()
    snapshot = _CP44_OWNER_SNAPSHOT(parent_owner)
    parent = _CP44_VALIDATE_CERTIFICATE(parent_owner.certificate)
    _validate_parent_claims(parent)
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "obstruction_policy": _POLICY,
        "obstruction_role_sha256": role,
        "checkpoint44_certificate": parent,
        "checkpoint44_certificate_sha256": parent.certificate_sha256,
        "checkpoint44_owner_runtime_identity": id(parent_owner),
        "checkpoint36_certificate_sha256": parent.checkpoint36_certificate_sha256,
        "checkpoint36_word_family_hypothesis_sha256": (
            parent.checkpoint36_certificate.word_family_hypothesis.hypothesis_sha256
        ),
        "checkpoint27_certificate_sha256": parent.checkpoint27_certificate_sha256,
        "checkpoint26_certificate_sha256": (
            parent.checkpoint27_certificate.checkpoint26_certificate_sha256
        ),
        "process_parameter_sha256": parent.process_parameter_sha256,
        "raw_word_domain_size": _D,
        "full_word_count": parent.full_word_count,
        "current_request_coordinate_count": _CURRENT_REQUEST_COORDINATES,
        "product_uniform_support_log2": 64 * parent.full_word_count,
        "fixed_request_tv_exponent_gap": parent.full_word_count,
        "one_free_request_tv_exponent_gap": parent.full_word_count - 1,
        "two_free_request_tv_exponent_gap": parent.full_word_count - 2,
        "fixed_request_tv_theorem": _FIXED_THEOREM,
        "free_request_support_tv_theorem": _SUPPORT_THEOREM,
        "source_to_output_tv_nonconverse": _NONCONVERSE,
        "obstruction_runtime_sha256": _runtime_sha256(),
        "passed": True,
        "certificate_sha256": _ZERO_SHA256,
    }
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        values[name] = True
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        values[name] = False
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    certificate = (
        CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate(
            **values, _construction_token=_CERTIFICATE_TOKEN
        )
    )
    _require_dependency_surfaces()
    _CP44_REQUIRE_OWNER_SNAPSHOT(parent_owner, snapshot)
    return certificate


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound:
    """Sealed symbolic TV support bound; no large power is materialized."""

    certificate: CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate
    certificate_sha256: str
    full_word_count: int
    free_uint64_request_coordinates: int
    source_support_log2_upper_bound: int
    product_uniform_support_log2: int
    support_exponent_gap: int
    tv_lower_bound_formula: str
    strict_product_uniform_obstruction: bool
    fixed_returned_request_exact_tv_certified: bool
    fixed_returned_request_exact_tv_formula: str
    conditional_on_success_only: bool
    success_value_independence_required: bool
    output_tv_lower_bound_certified: bool
    within_current_cp44_request_surface: bool
    bound_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP45 support bounds cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _BOUND_TOKEN:
            raise TypeError("CP45 support bounds are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP45 support-bound fields are incomplete")
        _validate_bound_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP45 support bounds are not pickleable")


def _bound_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound.__annotations__
    )


def _bound_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: values[name]
        for name in _bound_fields()
        if name not in ("certificate", "bound_sha256")
    }


def _validate_bound_values(values: Mapping[str, object]) -> None:
    if set(values) != set(_bound_fields()):
        raise TypeError("CP45 support-bound mapping is incomplete")
    certificate = _validate_certificate(values["certificate"])
    _require_sha256(values["certificate_sha256"], name="bound.certificate_sha256")
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("CP45 support bound lost certificate custody")
    summary = _support_bound_values(
        values["full_word_count"], values["free_uint64_request_coordinates"]
    )
    if values["full_word_count"] != certificate.full_word_count:
        raise ValueError("CP45 support-bound capsule length differs")
    for name, expected in summary.items():
        if type(expected) is int and type(values[name]) is not int:
            raise TypeError(
                "CP45 support-bound field %s must be an exact integer" % name
            )
        if type(expected) is str and type(values[name]) is not str:
            raise TypeError("CP45 support-bound field %s must be exact text" % name)
        if type(expected) is bool and type(values[name]) is not bool:
            raise TypeError("CP45 support-bound field %s must be an exact bool" % name)
        if values[name] != expected:
            raise ValueError("CP45 support-bound field %s differs" % name)
    _exact_bool(
        values["conditional_on_success_only"],
        True,
        name="bound.conditional_on_success_only",
    )
    _exact_bool(
        values["success_value_independence_required"],
        False,
        name="bound.success_value_independence_required",
    )
    _exact_bool(
        values["output_tv_lower_bound_certified"],
        False,
        name="bound.output_tv_lower_bound_certified",
    )
    _require_sha256(values["bound_sha256"], name="bound.bound_sha256")
    if values["bound_sha256"] != _semantic_digest(_bound_payload(values)):
        raise ValueError("CP45 support-bound digest differs")


def _validate_bound(
    bound: object,
) -> CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound:
    if (
        type(bound)
        is not CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound
    ):
        raise TypeError("bound has the wrong exact CP45 type")
    _validate_bound_values({name: getattr(bound, name) for name in _bound_fields()})
    return bound


def _make_bound(
    certificate: CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate,
    free: int,
) -> CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound:
    summary = dict(_support_bound_values(certificate.full_word_count, free))
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        **summary,
        "conditional_on_success_only": True,
        "success_value_independence_required": False,
        "output_tv_lower_bound_certified": False,
        "bound_sha256": _ZERO_SHA256,
    }
    values["bound_sha256"] = _semantic_digest(_bound_payload(values))
    return CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound(
        **values, _construction_token=_BOUND_TOKEN
    )


_FROZEN_LOCAL_SURFACES = (
    ("_adapter", _adapter),
    ("_CP44_OWNER_TYPE", _CP44_OWNER_TYPE),
    ("_CP44_CERT_TYPE", _CP44_CERT_TYPE),
    ("_CP44_VALIDATE_CERTIFICATE", _CP44_VALIDATE_CERTIFICATE),
    ("_CP44_OWNER_SNAPSHOT", _CP44_OWNER_SNAPSHOT),
    ("_CP44_REQUIRE_OWNER_SNAPSHOT", _CP44_REQUIRE_OWNER_SNAPSHOT),
    (
        "_CP44_REQUIRE_DEPENDENCY_SURFACES",
        _CP44_REQUIRE_DEPENDENCY_SURFACES,
    ),
    ("_CP44_CERTIFICATE_PROPERTY", _CP44_CERTIFICATE_PROPERTY),
    ("_SCHEMA_VERSION", _SCHEMA_VERSION),
    ("_POLICY", _POLICY),
    ("_SCOPE", _SCOPE),
    ("_FIXED_THEOREM", _FIXED_THEOREM),
    ("_SUPPORT_THEOREM", _SUPPORT_THEOREM),
    ("_NONCONVERSE", _NONCONVERSE),
    ("_D", _D),
    ("_CURRENT_REQUEST_COORDINATES", _CURRENT_REQUEST_COORDINATES),
    ("_ZERO_SHA256", _ZERO_SHA256),
    ("_CERTIFICATE_TOKEN", _CERTIFICATE_TOKEN),
    ("_BOUND_TOKEN", _BOUND_TOKEN),
    ("_OWNER_TOKEN", _OWNER_TOKEN),
    ("_CERTIFICATE_POSITIVE_FLAGS", _CERTIFICATE_POSITIVE_FLAGS),
    ("_CERTIFICATE_NEGATIVE_FLAGS", _CERTIFICATE_NEGATIVE_FLAGS),
    ("_CERTIFICATE_SHA256_FIELDS", _CERTIFICATE_SHA256_FIELDS),
    ("_CERTIFICATE_INTEGER_FIELDS", _CERTIFICATE_INTEGER_FIELDS),
    ("_CERTIFICATE_TEXT_FIELDS", _CERTIFICATE_TEXT_FIELDS),
    ("_canonical", _canonical),
    ("_semantic_digest", _semantic_digest),
    ("_require_sha256", _require_sha256),
    ("_exact_nonnegative_integer", _exact_nonnegative_integer),
    ("_exact_bool", _exact_bool),
    ("_runtime_sha256", _runtime_sha256),
    ("_support_bound_values", _support_bound_values),
    ("_certificate_fields", _certificate_fields),
    ("_certificate_payload", _certificate_payload),
    ("_validate_parent_claims", _validate_parent_claims),
    ("_validate_certificate_values", _validate_certificate_values),
    ("_validate_certificate", _validate_certificate),
    ("_make_certificate", _make_certificate),
    ("_bound_fields", _bound_fields),
    ("_bound_payload", _bound_payload),
    ("_validate_bound_values", _validate_bound_values),
    ("_validate_bound", _validate_bound),
    ("_make_bound", _make_bound),
    (
        "CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate",
        CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate,
    ),
    (
        "CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound",
        CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound,
    ),
)


def _require_local_surfaces(
    dependency_guard: object = _require_dependency_surfaces,
    frozen: Tuple[Tuple[str, object], ...] = _FROZEN_LOCAL_SURFACES,
) -> None:
    """Refuse CP45-local helper substitution before invoking a helper."""

    namespace = globals()
    if namespace.get("_require_dependency_surfaces") is not dependency_guard:
        raise ValueError("CP45 dependency guard changed")
    if namespace.get("_FROZEN_LOCAL_SURFACES") is not frozen:
        raise ValueError("CP45 frozen local surfaces changed")
    for name, expected in frozen:
        if namespace.get(name) is not expected:
            raise ValueError("CP45 local surface changed: %s" % name)
    dependency_guard()


_LOCAL_SURFACE_GUARD = _require_local_surfaces


class CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner:
    """Immutable operation-free owner of the CP45 support theorem."""

    __slots__ = (
        "_factorized_execution_owner",
        "_factorized_execution_owner_identity",
        "_certificate",
        "_certificate_identity",
        "_local_surface_guard",
        "_local_surface_guard_identity",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP45 owners cannot be subclassed")

    def __init__(
        self,
        parent: _CP44_OWNER_TYPE,
        certificate: CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("CP45 owners require certification")
        if type(parent) is not _CP44_OWNER_TYPE:
            raise TypeError("factorized_execution_owner has the wrong exact type")
        _LOCAL_SURFACE_GUARD()
        checked = _validate_certificate(certificate)
        if checked.checkpoint44_certificate is not parent.certificate:
            raise ValueError("CP45 certificate belongs to another CP44 owner")
        object.__setattr__(self, "_factorized_execution_owner", parent)
        object.__setattr__(self, "_factorized_execution_owner_identity", parent)
        object.__setattr__(self, "_certificate", checked)
        object.__setattr__(self, "_certificate_identity", checked)
        object.__setattr__(self, "_local_surface_guard", _LOCAL_SURFACE_GUARD)
        object.__setattr__(self, "_local_surface_guard_identity", _LOCAL_SURFACE_GUARD)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("CP45 owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("CP45 owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP45 owners are not pickleable")

    @property
    def certificate(
        self,
    ) -> CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate:
        return self._certificate

    @property
    def factorized_execution_owner(self) -> _CP44_OWNER_TYPE:
        return self._factorized_execution_owner

    def _require_local_surface_binding(self) -> None:
        guard = self._local_surface_guard
        if guard is not self._local_surface_guard_identity:
            raise ValueError("CP45 local surface guard identity changed")
        namespace = globals()
        if namespace.get("_LOCAL_SURFACE_GUARD") is not guard:
            raise ValueError("CP45 local surface guard binding changed")
        if namespace.get("_require_local_surfaces") is not guard:
            raise ValueError("CP45 local surface guard implementation changed")
        guard()

    def _require_live_binding(
        self,
    ) -> CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate:
        self._require_local_surface_binding()
        if (
            self._factorized_execution_owner
            is not self._factorized_execution_owner_identity
        ):
            raise ValueError("CP45 parent owner identity changed")
        if self._certificate is not self._certificate_identity:
            raise ValueError("CP45 certificate identity changed")
        if type(self._certificate) is not (
            CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate
        ):
            raise TypeError("certificate has the wrong exact CP45 type")
        owner_identity = self._certificate.checkpoint44_owner_runtime_identity
        if type(owner_identity) is not int:
            raise TypeError("CP45 parent owner identity must be an exact integer")
        if owner_identity != id(self._factorized_execution_owner):
            raise ValueError("CP45 parent owner runtime identity differs")
        snapshot = _CP44_OWNER_SNAPSHOT(self._factorized_execution_owner)
        checked = _validate_certificate(self._certificate)
        if (
            checked.checkpoint44_certificate
            is not self._factorized_execution_owner.certificate
        ):
            raise ValueError("CP45 live parent certificate identity changed")
        _require_dependency_surfaces()
        _CP44_REQUIRE_OWNER_SNAPSHOT(self._factorized_execution_owner, snapshot)
        return checked

    def source_support_bound(
        self,
        free_uint64_request_coordinates: object,
    ) -> CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound:
        """Describe the exact support obstruction without executing a source."""

        self._require_local_surface_binding()
        free = _exact_nonnegative_integer(
            free_uint64_request_coordinates,
            name="free_uint64_request_coordinates",
        )
        checked = self._require_live_binding()
        bound = _make_bound(checked, free)
        self._require_live_binding()
        return bound

    def validate_bound(
        self,
        bound: object,
    ) -> CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound:
        """Structurally validate one bound without allocation or semantics."""

        self._require_local_surface_binding()
        if (
            type(bound)
            is not CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound
        ):
            raise TypeError("bound has the wrong exact CP45 type")
        checked_certificate = self._require_live_binding()
        checked = _validate_bound(bound)
        if checked.certificate is not checked_certificate:
            raise ValueError("CP45 support bound belongs to another owner")
        self._require_live_binding()
        return checked


def certify_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction(
    factorized_execution_owner: _CP44_OWNER_TYPE,
    *,
    obstruction_policy: object,
    obstruction_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner:
    """Certify the operation-free CP45 source-support obstruction."""

    if type(factorized_execution_owner) is not _CP44_OWNER_TYPE:
        raise TypeError("factorized_execution_owner has the wrong exact type")
    if type(obstruction_policy) is not str:
        raise TypeError("obstruction_policy must be exact text")
    if obstruction_policy != _POLICY:
        raise ValueError("only the exported CP45 policy is supported")
    role = _require_sha256(obstruction_role_sha256, name="obstruction_role_sha256")
    certificate = _make_certificate(factorized_execution_owner, role)
    owner = CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner(
        factorized_execution_owner,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction(
    factorized_execution_owner: _CP44_OWNER_TYPE,
    owner: CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner,
    *,
    obstruction_policy: object,
    obstruction_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner:
    """Require one exact already-certified CP45 owner."""

    if type(owner) is not (
        CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner
    ):
        raise TypeError("owner has the wrong exact CP45 type")
    if owner.factorized_execution_owner is not factorized_execution_owner:
        raise ValueError("CP45 owner belongs to another CP44 owner")
    if type(obstruction_policy) is not str or obstruction_policy != _POLICY:
        raise ValueError("CP45 policy differs")
    role = _require_sha256(obstruction_role_sha256, name="obstruction_role_sha256")
    checked = owner._require_live_binding()
    if checked.obstruction_role_sha256 != role:
        raise ValueError("CP45 role differs")
    return owner


def validate_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction_certificate(
    factorized_execution_owner: _CP44_OWNER_TYPE,
    owner: CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner,
    *,
    obstruction_policy: object,
    obstruction_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate:
    """Validate one CP45 certificate against an exact CP44 owner."""

    matched = require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction(
        factorized_execution_owner,
        owner,
        obstruction_policy=obstruction_policy,
        obstruction_role_sha256=obstruction_role_sha256,
    )
    return matched.certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_SUPPORT_OBSTRUCTION_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_SUPPORT_OBSTRUCTION_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_SUPPORT_OBSTRUCTION_SCOPE",
    "INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_TV_THEOREM",
    "INITIAL_TILT_REJECTION_FREE_REQUEST_SOURCE_SUPPORT_TV_THEOREM",
    "INITIAL_TILT_REJECTION_SOURCE_TO_OUTPUT_TV_NONCONVERSE",
    "INITIAL_TILT_REJECTION_FIXED_ADDRESS_RAW_WORD_DOMAIN_SIZE",
    "INITIAL_TILT_REJECTION_FIXED_ADDRESS_CURRENT_REQUEST_COORDINATES",
    "CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate",
    "CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound",
    "CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionError",
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction",
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction",
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction_certificate",
]
