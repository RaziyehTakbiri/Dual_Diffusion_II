"""Assumption-gated full-source law admission above checkpoint forty-eight.

Checkpoint forty-eight supplies an exact byte-acquisition boundary, a
bijection from complete ``8L``-byte blocks to ``L`` uint64 words, and one
returned CP43 semantic result.  It deliberately certifies no probability law
for either supported backend.  This additive checkpoint keeps that boundary
intact.  It records caller-declared *mathematical assumptions* that the backend
returns one exact byte block almost surely, that the block's unconditional law
is jointly uniform, that the pre-operation state is admissible, that every byte
value succeeds after the backend boundary, and that CP43/CP42 object semantics
are fixed, runtime-deterministic, replay-stable, typed, and total.  It then
states the resulting one-draw pushforward theorem.  The pre-operation
antecedent requires a fresh draw, available retirement capacity, and passing
structural/live guards; duplicate and capacity refusals are not made total by
this declaration.

Let ``C`` be CP48's byte/word bijection and ``T_obj`` the enriched CP43/CP42
semantic projection for one fixed request.  Its value is ``(status,
comparison_count, selected_attempt_index, configuration_value_or_none)``;
failures and exhaustion retain distinct status labels, while selection retains the
canonical bit-exact CP42 configuration value.  Replacing only the final value
by its canonical SHA-256 yields CP44's canonical projection of the CP43
applied decision.  A returned record separately retains the actual runtime
object by identity for custody.  Under the declared assumptions,

``Law(T_obj(C(B))) = (T_obj o C)#mu``

and data processing gives

``TV((T_obj o C)#mu, T_obj#U_words) <= TV(mu, U_bytes)``.

If a return event is not total, its likelihood ``s(b)=P(R|B=b)`` reweights the
source law.  A returned uniform law therefore additionally needs positive
return mass and constant complete-success likelihood over the entire block
domain.  Marginal per-call premises do not imply a joint sequence law.

This module never acquires bytes and never evaluates CP43.  It can describe a
fixed request and structurally admit an already-returned CP48 record into the
four-element semantic-status union.  A selected record retains the exact
nested CP42 configuration and witnesses one nonempty semantic fiber under the
abstract premise.  It does not create a CP40 result, intensity, lineage,
tag-3 payload, general initializer, path, or sampler.  In particular, choosing
the premise does not verify ``os.urandom`` or an external callback.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

from heterodiff.processes import (
    plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution as _execution,
)


PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ADMISSION_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-full-source-law-" "admission-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ADMISSION_POLICY = (
    "exact-checkpoint48-and-transitive-checkpoint47-43-binding;"
    "sealed-external-assumption-declaration;backend-almost-sure-exact-block-"
    "return-and-unconditional-joint-complete-byte-block-uniformity;fresh-draw-"
    "capacity-preboundary-guards-and-post-boundary-"
    "all-byte-value-complete-success-plus-fixed-typed-total-CP43-antecedents;"
    "pointwise-one-draw-object-semantic-pushforward-and-TV-data-processing;"
    "positive-return-and-value-independent-complete-success-conditioning;"
    "four-status-preservation;selected-nonempty-fiber-witness-only;"
    "structural-nonexecuting-nonreplaying-result-admission;"
    "no-backend-law-verification-no-CP40-admission-no-global-uniqueness-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ADMISSION_SCOPE = (
    "one-exact-CP48-owner-and-pointwise-each-individually-fixed-request-result;"
    "assumption-gated-CP43-CP42-object-semantic-reference-law-only;"
    "not-operational-backend-law-totality-positive-return-mass-or-IID-evidence;"
    "not-duplicate-draw-capacity-exhaustion-or-preboundary-refusal-totalization;"
    "not-sequence-adaptive-stopping-retry-or-random-oracle-theorem;"
    "not-cross-owner-process-fork-restart-or-machine-global-uniqueness;"
    "not-legacy-CP36-37-universal-equivalence-or-CP41-premise-discharge;"
    "not-CP40-fixed-batch-target-or-initializer-admission;"
    "not-exact-ideal-rejection-global-analytic-tilt-lineage-tag3-path-sampler;"
    "not-test28-scientific-model-quality-generality-or-manuscript-evidence"
)

INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ASSUMPTION_MODE = (
    "external-backend-almost-sure-exact-block-unconditional-joint-uniform-"
    "total-single-draw-premise"
)
INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ASSUMPTION_SCOPE = (
    "assumption-only-not-attestation-or-operational-evidence;backend-returns-"
    "one-exact-byte-block-almost-surely-and-that-block-has-an-unconditional-"
    "joint-uniform-law;pointwise-one-complete-byte-block-for-each-individually-"
    "fixed-request;repeated-uses-give-only-separate-marginal-implications-no-"
    "joint-sequence-or-adaptive-extension"
)
INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SEMANTIC_STATUSES = (
    "preparation_failure",
    "quota_certification_failure",
    "selected",
    "exhausted",
)
INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_PUSHFORWARD_THEOREM = (
    "for-each-individually-fixed-request-in-a-fixed-pre-operation-state-with-"
    "fresh-draw-available-retirement-capacity-and-passing-preboundary-guards;"
    "under-backend-almost-sure-exact-byte-block-return-unconditional-joint-"
    "complete-byte-block-law-mu-post-boundary-complete-success-for-every-exact-"
    "byte-block-and-fixed-runtime-deterministic-replay-stable-"
    "typed-total-CP43-CP42-object-semantics-T_obj;T_obj-is-the-tuple-status-"
    "comparison-count-selected-attempt-index-and-canonical-bit-exact-CP42-"
    "configuration-value-or-none;it-keeps-F36-F37-exhaustion-distinct;"
    "replacing-only-its-final-value-by-the-canonical-configuration-SHA256-"
    "yields-the-CP44-canonical-projection-of-the-CP43-applied-decision;with-"
    "the-certified-"
    "bijective-codec-C;Law(T_obj(C(B)))=(T_obj-compose-C)#mu-and-TV((T_obj-"
    "compose-C)#mu,T_obj#U_words)<=TV(mu,U_bytes);joint-uniform-mu-gives-the-"
    "CP43-CP42-object-semantic-reference-pushforward"
)
INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_RETURN_CONDITIONING_CAVEAT = (
    "for-complete-return-event-R-with-Z=sum_b(mu(b)*s(b))>0-and-s(b)=P(R|B=b);"
    "P(C(B)=w|R)=mu(C^-1(w))*s(C^-1(w))/Z;under-joint-uniform-mu-the-returned-"
    "word-law-is-uniform-iff-s-is-positive-and-constant-on-the-complete-block-"
    "domain;backend-almost-sure-exact-block-return-together-with-post-boundary-"
    "all-byte-value-complete-success-is-sufficient;"
    "duplicate-draw-capacity-and-preboundary-refusals-are-outside-this-kernel"
)
INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SELECTED_FIBER_THEOREM = (
    "one-structurally-valid-selected-CP48-result-identifies-one-exact-word-"
    "preimage-under-T_obj-of-the-retained-enriched-semantic-atom-status-"
    "comparison-count-selected-attempt-index-and-canonical-bit-exact-CP42-"
    "configuration-value;therefore-the-coarser-configuration-value-fiber-is-"
    "also-nonempty;the-record-separately-retains-runtime-object-identity;"
    "under-the-declared-abstract-"
    "uniform-and-total-semantics-premise-that-fiber-and-the-selection-event-"
    "have-positive-reference-mass-at-least-2^(-64L);this-is-not-operational-"
    "source-law-evidence-or-general-initializer-admission"
)
INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SEQUENCE_NONCLAIM = (
    "one-call-or-marginal-uniformity-and-value-independent-marginal-success-"
    "do-not-imply-returned-sequence-IID;that-conclusion-needs-a-joint-source-"
    "product-uniform-full-vector-law-or-each-new-block-conditionally-uniform-"
    "given-the-full-prior-and-adaptive-history-on-distinct-pre-admissible-"
    "requests-plus-positive-joint-return-mass-and-value-independent-joint-"
    "complete-success-over-the-full-vector;adaptive-stopping-and-retry-are-"
    "out-of-scope"
)

_SCHEMA_VERSION = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ADMISSION_SCHEMA_VERSION
_POLICY = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ADMISSION_POLICY
)
_SCOPE = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ADMISSION_SCOPE
)
_ASSUMPTION_MODE = INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ASSUMPTION_MODE
_ASSUMPTION_SCOPE = INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ASSUMPTION_SCOPE
_STATUSES = INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SEMANTIC_STATUSES
_PUSHFORWARD_THEOREM = INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_PUSHFORWARD_THEOREM
_RETURN_CAVEAT = INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_RETURN_CONDITIONING_CAVEAT
_SELECTED_THEOREM = INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SELECTED_FIBER_THEOREM
_SEQUENCE_NONCLAIM = INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SEQUENCE_NONCLAIM
_D = 1 << 64
_ZERO_SHA256 = "0" * 64

_JSON_DUMPS = json.dumps
_SHA256 = hashlib.sha256
_PYTHON_VERSION = tuple(sys.version_info[:3])
_PYTHON_IMPLEMENTATION = platform.python_implementation()

_DECLARATION_TOKEN = object()
_CERTIFICATE_TOKEN = object()
_DESCRIPTION_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()

_CP48_OWNER_TYPE = (
    _execution.CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionOwner
)
_CP48_CERT_TYPE = (
    _execution.CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionCertificate
)
_CP48_RESULT_TYPE = (
    _execution.CounterKeyedInitialTiltRejectionByteSourceFullCapsuleExecutionResult
)
_CP48_VALIDATE_CERTIFICATE = _execution._validate_certificate
_CP48_VALIDATE_RESULT_RECORD = _execution._validate_result_record
_CP48_OWNER_SNAPSHOT = _CP48_OWNER_TYPE._owner_snapshot
_CP48_VALIDATE_RESULT = _CP48_OWNER_TYPE.validate_result
_CP48_LIVE_REVALIDATE = _CP48_OWNER_TYPE.revalidate_live_ancestry
_CP48_CERTIFICATE_PROPERTY = _CP48_OWNER_TYPE.certificate
_CP48_SOURCE_MODEL_OWNER_PROPERTY = _CP48_OWNER_TYPE.source_model_owner
_CP48_REQUIRE_DEPENDENCY_SURFACES = _execution._require_dependency_surfaces
_CP48_REQUIRE_LOCAL_SURFACES = _execution._require_local_surfaces
_EXACT_UINT64 = _execution._exact_uint64
_RUNTIME_DEFAULT_FINGERPRINT = _execution._runtime_default_fingerprint
_CODE_SHA256 = _execution._code_sha256
_CODE_FINGERPRINT_FORMAT = _execution._CODE_FINGERPRINT_FORMAT

_CP48_PROFILE_SYSTEM_OS_URANDOM_OPERATIONAL = (
    _execution.INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_SYSTEM_OS_URANDOM_OPERATIONAL
)
_CP48_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED = (
    _execution.INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED
)
_CP48_PROFILES = _execution.INITIAL_TILT_REJECTION_BYTE_SOURCE_PROFILES


class PluginBridgeCounterKeyedInitialTiltRejectionFullSourceLawAdmissionError(
    ArithmeticError
):
    """Fail-closed CP49 assumption, ancestry, or admission error."""


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    excluded = set(names)
    return {name: values[name] for name in values if name not in excluded}


def _canonical(value: object) -> object:
    if value is None or type(value) in (bool, str):
        return value
    if type(value) is int:
        sign = "-" if value < 0 else "+"
        return {"cp49_exact_integer_hex": sign + format(abs(value), "x")}
    if type(value) is tuple:
        return [_canonical(item) for item in value]
    if type(value) is dict:
        return {str(key): _canonical(item) for key, item in value.items()}
    raise TypeError("unsupported value in CP49 semantic digest")


def _semantic_digest(payload: object) -> str:
    encoded = _JSON_DUMPS(
        _canonical(payload), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _SHA256(encoded).hexdigest()


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(name + " must be lowercase SHA-256 text")
    return value


def _require_text(value: object, expected: str, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if value != expected:
        raise ValueError(name + " differs")
    return value


def _exact_true(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(name + " must be an exact bool")
    if value is not True:
        raise ValueError(name + " must be true as an explicit premise")
    return value


def _exact_bool(value: object, expected: bool, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(name + " must be an exact bool")
    if value is not expected:
        raise ValueError(name + " differs")
    return value


def _exact_nonnegative_integer(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < 0:
        raise ValueError(name + " must be nonnegative")
    return value


def _exact_positive_integer(value: object, *, name: str) -> int:
    checked = _exact_nonnegative_integer(value, name=name)
    if checked == 0:
        raise ValueError(name + " must be positive")
    return checked


def _exact_profile(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if value not in _CP48_PROFILES:
        raise ValueError(name + " is not a frozen CP48 profile")
    return value


def _uniform_fiber_probability(fiber_size: object, domain_size: object) -> Fraction:
    """Exact k/n mass under a finite uniform domain; a pure proof helper."""

    fiber = _exact_nonnegative_integer(fiber_size, name="fiber_size")
    domain = _exact_positive_integer(domain_size, name="domain_size")
    if fiber > domain:
        raise ValueError("fiber_size exceeds domain_size")
    return Fraction(fiber, domain)


def _return_conditioned_fiber_probability(
    fiber_size: object, returned_domain_size: object
) -> Fraction:
    """Exact k/r only under a separately assumed uniform returned support."""

    fiber = _exact_nonnegative_integer(fiber_size, name="fiber_size")
    returned = _exact_positive_integer(
        returned_domain_size, name="returned_domain_size"
    )
    if fiber > returned:
        raise ValueError("fiber_size exceeds returned_domain_size")
    return Fraction(fiber, returned)


def _checkpoint43_certificate(certificate: _CP48_CERT_TYPE) -> object:
    return (
        certificate.checkpoint47_certificate.checkpoint46_certificate.checkpoint45_certificate.checkpoint44_certificate.checkpoint43_certificate
    )


def _process_context_sha256(certificate: _CP48_CERT_TYPE) -> str:
    return _semantic_digest(
        {
            "schema": _SCHEMA_VERSION,
            "policy": _POLICY,
            "scope": _SCOPE,
            "python_version": _PYTHON_VERSION,
            "python_implementation": _PYTHON_IMPLEMENTATION,
            "checkpoint48_runtime": certificate.execution_runtime_sha256,
        }
    )


def _require_dependency_surfaces() -> None:
    module_expectations = (
        ("_validate_certificate", _CP48_VALIDATE_CERTIFICATE),
        ("_validate_result_record", _CP48_VALIDATE_RESULT_RECORD),
        ("_require_dependency_surfaces", _CP48_REQUIRE_DEPENDENCY_SURFACES),
        ("_require_local_surfaces", _CP48_REQUIRE_LOCAL_SURFACES),
        ("_exact_uint64", _EXACT_UINT64),
        ("_runtime_default_fingerprint", _RUNTIME_DEFAULT_FINGERPRINT),
        ("_code_sha256", _CODE_SHA256),
    )
    for name, expected in module_expectations:
        if not hasattr(_execution, name) or getattr(_execution, name) is not expected:
            raise ValueError("CP49 CP48 dependency surface changed: " + name)
    method_expectations = (
        ("_owner_snapshot", _CP48_OWNER_SNAPSHOT),
        ("validate_result", _CP48_VALIDATE_RESULT),
        ("revalidate_live_ancestry", _CP48_LIVE_REVALIDATE),
    )
    for name, expected in method_expectations:
        if getattr(_CP48_OWNER_TYPE, name) is not expected:
            raise ValueError("CP49 CP48 owner surface changed: " + name)
    if _CP48_OWNER_TYPE.certificate is not _CP48_CERTIFICATE_PROPERTY:
        raise ValueError("CP49 CP48 certificate property changed")
    if _CP48_OWNER_TYPE.source_model_owner is not _CP48_SOURCE_MODEL_OWNER_PROPERTY:
        raise ValueError("CP49 CP48 source-model property changed")
    _CP48_REQUIRE_LOCAL_SURFACES()


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration:
    """Explicit external premise; never an operational attestation."""

    schema_version: str
    assumption_mode: str
    assumption_scope: str
    checkpoint48_certificate_sha256: str
    source_instance_sha256: str
    byte_source_profile: str
    assumption_role_sha256: str
    backend_exact_byte_block_almost_sure_return_assumed: bool
    unconditional_joint_full_byte_block_uniformity_assumed: bool
    fresh_draw_capacity_and_preboundary_guards_assumed: bool
    post_boundary_complete_success_for_every_byte_block_assumed: bool
    fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed: bool
    positive_complete_return_mass_assumed: bool
    value_independent_complete_success_assumed: bool
    pointwise_one_draw_theorem_only: bool
    sequence_iid_assumed: bool
    adaptive_queries_covered: bool
    assumption_only: bool
    operational_realization_certified: bool
    backend_law_verified: bool
    backend_totality_verified: bool
    os_urandom_law_verified: bool
    external_callback_law_verified: bool
    declaration_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP49 assumption declarations cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _DECLARATION_TOKEN:
            raise TypeError("CP49 assumption declarations are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP49 assumption declaration is incomplete")
        _validate_declaration_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP49 assumption declarations are not pickleable")


def _declaration_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration.__annotations__
    )


def _declaration_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "declaration_sha256")


def _validate_declaration_values(values: Mapping[str, object]) -> None:
    if set(values) != set(_declaration_fields()):
        raise TypeError("CP49 assumption declaration mapping is incomplete")
    _require_text(values["schema_version"], _SCHEMA_VERSION, name="declaration.schema")
    _require_text(values["assumption_mode"], _ASSUMPTION_MODE, name="declaration.mode")
    _require_text(
        values["assumption_scope"], _ASSUMPTION_SCOPE, name="declaration.scope"
    )
    for name in (
        "checkpoint48_certificate_sha256",
        "source_instance_sha256",
        "assumption_role_sha256",
        "declaration_sha256",
    ):
        _require_sha256(values[name], name="declaration." + name)
    _exact_profile(values["byte_source_profile"], name="declaration.profile")
    true_flags = (
        "backend_exact_byte_block_almost_sure_return_assumed",
        "unconditional_joint_full_byte_block_uniformity_assumed",
        "fresh_draw_capacity_and_preboundary_guards_assumed",
        "post_boundary_complete_success_for_every_byte_block_assumed",
        "fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed",
        "positive_complete_return_mass_assumed",
        "value_independent_complete_success_assumed",
        "pointwise_one_draw_theorem_only",
        "assumption_only",
    )
    false_flags = (
        "sequence_iid_assumed",
        "adaptive_queries_covered",
        "operational_realization_certified",
        "backend_law_verified",
        "backend_totality_verified",
        "os_urandom_law_verified",
        "external_callback_law_verified",
    )
    for name in true_flags:
        _exact_bool(values[name], True, name="declaration." + name)
    for name in false_flags:
        _exact_bool(values[name], False, name="declaration." + name)
    if values["declaration_sha256"] != _semantic_digest(_declaration_payload(values)):
        raise ValueError("CP49 assumption declaration digest differs")


def declare_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_assumption(
    *,
    checkpoint48_certificate_sha256: object,
    source_instance_sha256: object,
    byte_source_profile: object,
    assumption_role_sha256: object,
    backend_exact_byte_block_almost_sure_return_assumed: object,
    unconditional_joint_full_byte_block_uniformity_assumed: object,
    fresh_draw_capacity_and_preboundary_guards_assumed: object,
    post_boundary_complete_success_for_every_byte_block_assumed: object,
    fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed: object,
) -> CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration:
    """Create the sole v1 premise mode, explicitly as an unverified assumption."""

    _LOCAL_SURFACE_GUARD()
    checkpoint = _require_sha256(
        checkpoint48_certificate_sha256,
        name="checkpoint48_certificate_sha256",
    )
    source = _require_sha256(source_instance_sha256, name="source_instance_sha256")
    profile = _exact_profile(byte_source_profile, name="byte_source_profile")
    role = _require_sha256(assumption_role_sha256, name="assumption_role_sha256")
    backend_total = _exact_true(
        backend_exact_byte_block_almost_sure_return_assumed,
        name="backend_exact_byte_block_almost_sure_return_assumed",
    )
    joint = _exact_true(
        unconditional_joint_full_byte_block_uniformity_assumed,
        name="unconditional_joint_full_byte_block_uniformity_assumed",
    )
    admissible = _exact_true(
        fresh_draw_capacity_and_preboundary_guards_assumed,
        name="fresh_draw_capacity_and_preboundary_guards_assumed",
    )
    post_boundary_total = _exact_true(
        post_boundary_complete_success_for_every_byte_block_assumed,
        name="post_boundary_complete_success_for_every_byte_block_assumed",
    )
    semantics = _exact_true(
        fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed,
        name=(
            "fixed_runtime_deterministic_replay_stable_typed_total_"
            "cp43_cp42_object_semantics_assumed"
        ),
    )
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "assumption_mode": _ASSUMPTION_MODE,
        "assumption_scope": _ASSUMPTION_SCOPE,
        "checkpoint48_certificate_sha256": checkpoint,
        "source_instance_sha256": source,
        "byte_source_profile": profile,
        "assumption_role_sha256": role,
        "backend_exact_byte_block_almost_sure_return_assumed": backend_total,
        "unconditional_joint_full_byte_block_uniformity_assumed": joint,
        "fresh_draw_capacity_and_preboundary_guards_assumed": admissible,
        "post_boundary_complete_success_for_every_byte_block_assumed": (
            post_boundary_total
        ),
        "fixed_runtime_deterministic_replay_stable_typed_total_cp43_cp42_object_semantics_assumed": (
            semantics
        ),
        "positive_complete_return_mass_assumed": True,
        "value_independent_complete_success_assumed": True,
        "pointwise_one_draw_theorem_only": True,
        "sequence_iid_assumed": False,
        "adaptive_queries_covered": False,
        "assumption_only": True,
        "operational_realization_certified": False,
        "backend_law_verified": False,
        "backend_totality_verified": False,
        "os_urandom_law_verified": False,
        "external_callback_law_verified": False,
        "declaration_sha256": _ZERO_SHA256,
    }
    values["declaration_sha256"] = _semantic_digest(_declaration_payload(values))
    return CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration(
        _construction_token=_DECLARATION_TOKEN,
        **values,
    )


def validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_assumption_declaration(
    declaration: object,
) -> CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration:
    _LOCAL_SURFACE_GUARD()
    if (
        type(declaration)
        is not CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration
    ):
        raise TypeError("declaration has the wrong exact CP49 type")
    _validate_declaration_values(
        {name: getattr(declaration, name) for name in _declaration_fields()}
    )
    return declaration


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate:
    """Sealed CP48 ancestry plus an explicitly unverified law premise."""

    schema_version: str
    certificate_scope: str
    admission_policy: str
    admission_role_sha256: str
    byte_source_execution_certificate: _CP48_CERT_TYPE
    checkpoint48_certificate_sha256: str
    checkpoint47_certificate_sha256: str
    checkpoint43_certificate_sha256: str
    byte_source_execution_owner_runtime_identity: int
    source_instance_sha256: str
    byte_source_profile: str
    assumption_declaration: CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration
    assumption_declaration_sha256: str
    assumption_role_sha256: str
    raw_word_domain_size: int
    full_word_count: int
    proposal_word_count: int
    decision_word_count: int
    raw_byte_count: int
    pushforward_theorem: str
    return_conditioning_caveat: str
    selected_fiber_theorem: str
    sequence_nonclaim: str
    process_context_sha256: str
    admission_runtime_sha256: str
    exact_checkpoint48_owner_and_certificate_binding_certified: bool
    exact_transitive_checkpoint47_43_ancestry_bound: bool
    cp48_codec_bijection_inherited: bool
    four_semantic_statuses_preserved: bool
    one_draw_pushforward_theorem_recorded: bool
    returned_conditioning_formula_recorded: bool
    selected_nonempty_fiber_theorem_recorded: bool
    structural_nonexecuting_validation_certified: bool
    source_law_is_external_assumption_only: bool
    operational_realization_certified: bool
    backend_law_verified: bool
    backend_totality_verified: bool
    returned_sequence_iid_certified: bool
    adaptive_query_or_retry_law_certified: bool
    global_uniqueness_certified: bool
    cp40_initializer_admission_certified: bool
    live_initializer_distribution_certified: bool
    general_initializer_admissible: bool
    formal_test28_closed: bool
    scientific_claim_promoted: bool
    model_quality_claim_promoted: bool
    generality_claim_promoted: bool
    manuscript_claim_promoted: bool
    loaded_code_integrity_certified: bool
    runtime_portable: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP49 certificates cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("CP49 certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP49 certificate is incomplete")
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP49 certificates are not pickleable")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate.__annotations__
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    payload = dict(
        _without(
            values,
            "byte_source_execution_certificate",
            "assumption_declaration",
            "certificate_sha256",
        )
    )
    payload["byte_source_execution_certificate"] = values[
        "checkpoint48_certificate_sha256"
    ]
    payload["assumption_declaration"] = values["assumption_declaration_sha256"]
    return payload


_CERTIFICATE_TRUE_FLAGS = (
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
_CERTIFICATE_FALSE_FLAGS = (
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


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    if set(values) != set(_certificate_fields()):
        raise TypeError("CP49 certificate mapping is incomplete")
    _require_text(values["schema_version"], _SCHEMA_VERSION, name="certificate.schema")
    _require_text(values["certificate_scope"], _SCOPE, name="certificate.scope")
    _require_text(values["admission_policy"], _POLICY, name="certificate.policy")
    for name in (
        "admission_role_sha256",
        "checkpoint48_certificate_sha256",
        "checkpoint47_certificate_sha256",
        "checkpoint43_certificate_sha256",
        "source_instance_sha256",
        "assumption_declaration_sha256",
        "assumption_role_sha256",
        "process_context_sha256",
        "admission_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(values[name], name="certificate." + name)
    parent = _CP48_VALIDATE_CERTIFICATE(values["byte_source_execution_certificate"])
    declaration = validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_assumption_declaration(
        values["assumption_declaration"]
    )
    if values["checkpoint48_certificate_sha256"] != parent.certificate_sha256:
        raise ValueError("CP49 certificate CP48 digest differs")
    if values["checkpoint47_certificate_sha256"] != (
        parent.checkpoint47_certificate_sha256
    ):
        raise ValueError("CP49 certificate CP47 digest differs")
    cp43 = _checkpoint43_certificate(parent)
    if values["checkpoint43_certificate_sha256"] != cp43.certificate_sha256:
        raise ValueError("CP49 certificate CP43 digest differs")
    if type(values["byte_source_execution_owner_runtime_identity"]) is not int:
        raise TypeError("CP49 certificate owner identity must be an exact integer")
    if values["byte_source_execution_owner_runtime_identity"] <= 0:
        raise ValueError("CP49 certificate owner identity is invalid")
    expected_text = {
        "source_instance_sha256": parent.source_instance_sha256,
        "byte_source_profile": parent.byte_source_profile,
        "assumption_declaration_sha256": declaration.declaration_sha256,
        "assumption_role_sha256": declaration.assumption_role_sha256,
        "pushforward_theorem": _PUSHFORWARD_THEOREM,
        "return_conditioning_caveat": _RETURN_CAVEAT,
        "selected_fiber_theorem": _SELECTED_THEOREM,
        "sequence_nonclaim": _SEQUENCE_NONCLAIM,
        "process_context_sha256": _process_context_sha256(parent),
        "admission_runtime_sha256": _runtime_sha256(),
    }
    for name, expected in expected_text.items():
        actual = values[name]
        if type(actual) is not str or actual != expected:
            raise ValueError("CP49 certificate field differs: " + name)
    if declaration.checkpoint48_certificate_sha256 != parent.certificate_sha256:
        raise ValueError("CP49 assumption belongs to another CP48 certificate")
    if declaration.source_instance_sha256 != parent.source_instance_sha256:
        raise ValueError("CP49 assumption source instance differs")
    if declaration.byte_source_profile != parent.byte_source_profile:
        raise ValueError("CP49 assumption byte-source profile differs")
    expected_integers = {
        "raw_word_domain_size": _D,
        "full_word_count": parent.full_word_count,
        "proposal_word_count": parent.proposal_word_count,
        "decision_word_count": parent.decision_word_count,
        "raw_byte_count": parent.raw_byte_count,
    }
    for name, expected in expected_integers.items():
        actual = values[name]
        if type(actual) is not int or actual != expected:
            raise ValueError("CP49 certificate integer differs: " + name)
    for name in _CERTIFICATE_TRUE_FLAGS:
        _exact_bool(values[name], True, name="certificate." + name)
    for name in _CERTIFICATE_FALSE_FLAGS:
        _exact_bool(values[name], False, name="certificate." + name)
    if values["certificate_sha256"] != _semantic_digest(_certificate_payload(values)):
        raise ValueError("CP49 certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate:
    if (
        type(certificate)
        is not CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate
    ):
        raise TypeError("certificate has the wrong exact CP49 type")
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _make_certificate(
    owner: _CP48_OWNER_TYPE,
    declaration: CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration,
    admission_role_sha256: str,
) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate:
    parent = _CP48_CERTIFICATE_PROPERTY.__get__(owner, _CP48_OWNER_TYPE)
    parent = _CP48_VALIDATE_CERTIFICATE(parent)
    cp43 = _checkpoint43_certificate(parent)
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "admission_policy": _POLICY,
        "admission_role_sha256": admission_role_sha256,
        "byte_source_execution_certificate": parent,
        "checkpoint48_certificate_sha256": parent.certificate_sha256,
        "checkpoint47_certificate_sha256": parent.checkpoint47_certificate_sha256,
        "checkpoint43_certificate_sha256": cp43.certificate_sha256,
        "byte_source_execution_owner_runtime_identity": id(owner),
        "source_instance_sha256": parent.source_instance_sha256,
        "byte_source_profile": parent.byte_source_profile,
        "assumption_declaration": declaration,
        "assumption_declaration_sha256": declaration.declaration_sha256,
        "assumption_role_sha256": declaration.assumption_role_sha256,
        "raw_word_domain_size": _D,
        "full_word_count": parent.full_word_count,
        "proposal_word_count": parent.proposal_word_count,
        "decision_word_count": parent.decision_word_count,
        "raw_byte_count": parent.raw_byte_count,
        "pushforward_theorem": _PUSHFORWARD_THEOREM,
        "return_conditioning_caveat": _RETURN_CAVEAT,
        "selected_fiber_theorem": _SELECTED_THEOREM,
        "sequence_nonclaim": _SEQUENCE_NONCLAIM,
        "process_context_sha256": _process_context_sha256(parent),
        "admission_runtime_sha256": _runtime_sha256(),
        **{name: True for name in _CERTIFICATE_TRUE_FLAGS},
        **{name: False for name in _CERTIFICATE_FALSE_FLAGS},
        "certificate_sha256": _ZERO_SHA256,
    }
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate(
        _construction_token=_CERTIFICATE_TOKEN,
        **values,
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFullSourceLawAdmissionDescription:
    """One nonexecuting fixed-request theorem description."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate
    certificate_sha256: str
    run_id: int
    initialization_index: int
    draw_index: int
    source_instance_sha256: str
    byte_source_profile: str
    raw_byte_count: int
    full_word_count: int
    proposal_word_count: int
    decision_word_count: int
    assumption_mode: str
    pushforward_theorem: str
    return_conditioning_caveat: str
    selected_fiber_theorem: str
    sequence_nonclaim: str
    assumption_only: bool
    backend_exact_byte_block_almost_sure_return_is_assumed: bool
    unconditional_joint_full_byte_block_uniformity_is_assumed: bool
    preboundary_admissibility_is_assumed: bool
    post_boundary_complete_success_is_assumed: bool
    fixed_deterministic_replay_stable_typed_total_semantics_is_assumed: bool
    reference_semantic_law_defined_under_assumptions: bool
    description_is_nonexecuting: bool
    source_or_semantic_replay_performed: bool
    backend_law_operationally_verified: bool
    backend_totality_operationally_verified: bool
    preboundary_admissibility_operationally_verified: bool
    duplicate_or_capacity_refusal_totalized: bool
    operational_realization_certified: bool
    returned_sequence_iid_certified: bool
    cp40_initializer_admission_certified: bool
    general_initializer_admissible: bool
    description_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP49 descriptions cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _DESCRIPTION_TOKEN:
            raise TypeError("CP49 descriptions are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP49 description is incomplete")
        _validate_description_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP49 descriptions are not pickleable")


def _description_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionFullSourceLawAdmissionDescription.__annotations__
    )


def _description_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    payload = dict(_without(values, "certificate", "description_sha256"))
    payload["certificate"] = values["certificate_sha256"]
    return payload


def _validate_description_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate
    ] = None,
) -> None:
    if set(values) != set(_description_fields()):
        raise TypeError("CP49 description mapping is incomplete")
    _require_text(values["schema_version"], _SCHEMA_VERSION, name="description.schema")
    certificate = _validate_certificate(values["certificate"])
    if trusted_certificate is not None and certificate is not trusted_certificate:
        raise ValueError("CP49 description certificate identity differs")
    certificate_sha256 = _require_sha256(
        values["certificate_sha256"], name="description.certificate_sha256"
    )
    if certificate_sha256 != certificate.certificate_sha256:
        raise ValueError("CP49 description certificate digest differs")
    for name in ("run_id", "initialization_index", "draw_index"):
        _EXACT_UINT64(values[name], name="description." + name)
    expected = {
        "source_instance_sha256": certificate.source_instance_sha256,
        "byte_source_profile": certificate.byte_source_profile,
        "raw_byte_count": certificate.raw_byte_count,
        "full_word_count": certificate.full_word_count,
        "proposal_word_count": certificate.proposal_word_count,
        "decision_word_count": certificate.decision_word_count,
        "assumption_mode": _ASSUMPTION_MODE,
        "pushforward_theorem": _PUSHFORWARD_THEOREM,
        "return_conditioning_caveat": _RETURN_CAVEAT,
        "selected_fiber_theorem": _SELECTED_THEOREM,
        "sequence_nonclaim": _SEQUENCE_NONCLAIM,
    }
    for name, target in expected.items():
        actual = values[name]
        if type(actual) is not type(target) or actual != target:
            raise ValueError("CP49 description field differs: " + name)
    for name in (
        "assumption_only",
        "backend_exact_byte_block_almost_sure_return_is_assumed",
        "unconditional_joint_full_byte_block_uniformity_is_assumed",
        "preboundary_admissibility_is_assumed",
        "post_boundary_complete_success_is_assumed",
        "fixed_deterministic_replay_stable_typed_total_semantics_is_assumed",
        "reference_semantic_law_defined_under_assumptions",
        "description_is_nonexecuting",
    ):
        _exact_bool(values[name], True, name="description." + name)
    for name in (
        "source_or_semantic_replay_performed",
        "backend_law_operationally_verified",
        "backend_totality_operationally_verified",
        "preboundary_admissibility_operationally_verified",
        "duplicate_or_capacity_refusal_totalized",
        "operational_realization_certified",
        "returned_sequence_iid_certified",
        "cp40_initializer_admission_certified",
        "general_initializer_admissible",
    ):
        _exact_bool(values[name], False, name="description." + name)
    _require_sha256(values["description_sha256"], name="description.digest")
    if values["description_sha256"] != _semantic_digest(_description_payload(values)):
        raise ValueError("CP49 description digest differs")


def _make_description(
    certificate: CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate,
    run_id: int,
    initialization_index: int,
    draw_index: int,
) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionDescription:
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "run_id": run_id,
        "initialization_index": initialization_index,
        "draw_index": draw_index,
        "source_instance_sha256": certificate.source_instance_sha256,
        "byte_source_profile": certificate.byte_source_profile,
        "raw_byte_count": certificate.raw_byte_count,
        "full_word_count": certificate.full_word_count,
        "proposal_word_count": certificate.proposal_word_count,
        "decision_word_count": certificate.decision_word_count,
        "assumption_mode": _ASSUMPTION_MODE,
        "pushforward_theorem": _PUSHFORWARD_THEOREM,
        "return_conditioning_caveat": _RETURN_CAVEAT,
        "selected_fiber_theorem": _SELECTED_THEOREM,
        "sequence_nonclaim": _SEQUENCE_NONCLAIM,
        "assumption_only": True,
        "backend_exact_byte_block_almost_sure_return_is_assumed": True,
        "unconditional_joint_full_byte_block_uniformity_is_assumed": True,
        "preboundary_admissibility_is_assumed": True,
        "post_boundary_complete_success_is_assumed": True,
        "fixed_deterministic_replay_stable_typed_total_semantics_is_assumed": True,
        "reference_semantic_law_defined_under_assumptions": True,
        "description_is_nonexecuting": True,
        "source_or_semantic_replay_performed": False,
        "backend_law_operationally_verified": False,
        "backend_totality_operationally_verified": False,
        "preboundary_admissibility_operationally_verified": False,
        "duplicate_or_capacity_refusal_totalized": False,
        "operational_realization_certified": False,
        "returned_sequence_iid_certified": False,
        "cp40_initializer_admission_certified": False,
        "general_initializer_admissible": False,
        "description_sha256": _ZERO_SHA256,
    }
    values["description_sha256"] = _semantic_digest(_description_payload(values))
    return CounterKeyedInitialTiltRejectionFullSourceLawAdmissionDescription(
        _construction_token=_DESCRIPTION_TOKEN,
        **values,
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFullSourceLawAdmissionResult:
    """One structurally admitted returned CP48 semantic record."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate
    certificate_sha256: str
    checkpoint48_result: _CP48_RESULT_TYPE
    checkpoint48_result_sha256: str
    checkpoint43_applied_decision: object
    checkpoint43_applied_decision_sha256: str
    run_id: int
    initialization_index: int
    draw_index: int
    source_instance_sha256: str
    byte_source_profile: str
    raw_bytes_sha256: str
    source_full_words_sha256: str
    semantic_status: str
    comparison_count: int
    selected_attempt_index: Optional[int]
    selected_configuration: Optional[object]
    selected_configuration_sha256: Optional[str]
    selected_enriched_semantic_atom_fiber_nonempty: bool
    selected_configuration_value_fiber_nonempty: bool
    abstract_uniform_selection_mass_positive_under_assumptions: bool
    selected_conditioned_reference_law_defined_under_assumptions: bool
    selected_uniform_single_preimage_mass_denominator_log2: Optional[int]
    exact_status_and_selected_object_identity_preserved: bool
    structurally_admitted_to_enriched_cp43_cp42_reference_codomain: bool
    structural_validation_is_nonexecuting_and_nonreplaying: bool
    source_law_assumption_only: bool
    operational_realization_certified: bool
    backend_law_verified: bool
    backend_totality_verified: bool
    live_initializer_distribution_certified: bool
    cp40_initializer_admission_certified: bool
    general_initializer_admissible: bool
    formal_test28_closed: bool
    global_uniqueness_certified: bool
    scientific_claim_promoted: bool
    model_quality_claim_promoted: bool
    generality_claim_promoted: bool
    manuscript_claim_promoted: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP49 results cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("CP49 results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP49 result is incomplete")
        _validate_result_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP49 results are not pickleable")


def _result_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionFullSourceLawAdmissionResult.__annotations__
    )


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    payload = dict(
        _without(
            values,
            "certificate",
            "checkpoint48_result",
            "checkpoint43_applied_decision",
            "selected_configuration",
            "result_sha256",
        )
    )
    payload["certificate"] = values["certificate_sha256"]
    payload["checkpoint48_result"] = values["checkpoint48_result_sha256"]
    payload["checkpoint43_applied_decision"] = values[
        "checkpoint43_applied_decision_sha256"
    ]
    payload["selected_configuration"] = values["selected_configuration_sha256"]
    return payload


def _extract_semantic_children(cp48_result: _CP48_RESULT_TYPE) -> Tuple[object, ...]:
    cp47 = cp48_result.checkpoint47_result
    applied = cp47.checkpoint43_applied_decision
    status = cp47.semantic_status
    if type(status) is not str or status not in _STATUSES:
        raise ValueError("CP49 CP47 semantic status differs")
    if applied.status != status:
        raise ValueError("CP49 CP43 and CP47 statuses differ")
    selected_attempt = applied.selected_attempt_index
    comparison_count = applied.comparison_count
    selected_sha256 = applied.selected_configuration_sha256
    selected_configuration = None
    if status == "selected":
        cp42 = applied.checkpoint42_applied_decision
        if cp42 is None or cp42.status != "selected":
            raise ValueError("CP49 selected status lacks exact CP42 custody")
        selected_configuration = cp42.selected_configuration
        if selected_configuration is None:
            raise ValueError("CP49 selected status lacks its configuration")
        if cp42.selected_configuration_sha256 != selected_sha256:
            raise ValueError("CP49 selected configuration digest differs")
    else:
        if selected_attempt is not None or selected_sha256 is not None:
            raise ValueError("CP49 nonselected status retained selected metadata")
    return (
        applied,
        status,
        comparison_count,
        selected_attempt,
        selected_configuration,
        selected_sha256,
    )


def _validate_result_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate
    ] = None,
) -> None:
    if set(values) != set(_result_fields()):
        raise TypeError("CP49 result mapping is incomplete")
    _require_text(values["schema_version"], _SCHEMA_VERSION, name="result.schema")
    certificate = _validate_certificate(values["certificate"])
    if trusted_certificate is not None and certificate is not trusted_certificate:
        raise ValueError("CP49 result certificate identity differs")
    certificate_sha256 = _require_sha256(
        values["certificate_sha256"], name="result.certificate_sha256"
    )
    if certificate_sha256 != certificate.certificate_sha256:
        raise ValueError("CP49 result certificate digest differs")
    cp48_result = values["checkpoint48_result"]
    if type(cp48_result) is not _CP48_RESULT_TYPE:
        raise TypeError("checkpoint48_result has the wrong exact type")
    checked_cp48_result = _CP48_VALIDATE_RESULT_RECORD(
        cp48_result,
        trusted_certificate=certificate.byte_source_execution_certificate,
        trusted_checkpoint47_owner_runtime_identity=(
            certificate.byte_source_execution_certificate.checkpoint47_owner_runtime_identity
        ),
        trusted_owner_runtime_identity=(
            certificate.byte_source_execution_owner_runtime_identity
        ),
    )
    if checked_cp48_result is not cp48_result:
        raise ValueError("CP49 CP48 structural validation substituted its result")
    if cp48_result.certificate is not certificate.byte_source_execution_certificate:
        raise ValueError("CP49 result belongs to another CP48 certificate")
    checkpoint48_result_sha256 = _require_sha256(
        values["checkpoint48_result_sha256"],
        name="result.checkpoint48_result_sha256",
    )
    if checkpoint48_result_sha256 != cp48_result.result_sha256:
        raise ValueError("CP49 retained CP48 digest differs")
    (
        applied,
        status,
        comparison_count,
        selected_attempt,
        selected,
        selected_sha256,
    ) = _extract_semantic_children(cp48_result)
    if values["checkpoint43_applied_decision"] is not applied:
        raise ValueError("CP49 retained CP43 applied identity differs")
    checkpoint43_applied_decision_sha256 = _require_sha256(
        values["checkpoint43_applied_decision_sha256"],
        name="result.checkpoint43_applied_decision_sha256",
    )
    if checkpoint43_applied_decision_sha256 != applied.applied_decision_sha256:
        raise ValueError("CP49 retained CP43 applied digest differs")
    expected = {
        "run_id": cp48_result.run_id,
        "initialization_index": cp48_result.initialization_index,
        "draw_index": cp48_result.draw_index,
        "source_instance_sha256": cp48_result.source_instance_sha256,
        "byte_source_profile": cp48_result.byte_source_profile,
        "raw_bytes_sha256": cp48_result.raw_bytes_sha256,
        "source_full_words_sha256": cp48_result.source_full_words_sha256,
        "semantic_status": status,
        "comparison_count": comparison_count,
        "selected_attempt_index": selected_attempt,
        "selected_configuration_sha256": selected_sha256,
    }
    for name, target in expected.items():
        actual = values[name]
        if type(actual) is not type(target) or actual != target:
            raise ValueError("CP49 result field differs: " + name)
    if values["selected_configuration"] is not selected:
        raise ValueError("CP49 selected configuration identity differs")
    is_selected = status == "selected"
    for name in (
        "selected_enriched_semantic_atom_fiber_nonempty",
        "selected_configuration_value_fiber_nonempty",
        "abstract_uniform_selection_mass_positive_under_assumptions",
        "selected_conditioned_reference_law_defined_under_assumptions",
    ):
        _exact_bool(values[name], is_selected, name="result." + name)
    expected_log2 = 64 * certificate.full_word_count if is_selected else None
    denominator_log2 = values["selected_uniform_single_preimage_mass_denominator_log2"]
    if is_selected:
        denominator_log2 = _exact_positive_integer(
            denominator_log2,
            name="result.selected_uniform_single_preimage_mass_denominator_log2",
        )
    elif denominator_log2 is not None:
        raise TypeError(
            "result.selected_uniform_single_preimage_mass_denominator_log2 "
            "must be None for a nonselected result"
        )
    if denominator_log2 != expected_log2:
        raise ValueError("CP49 selected fiber bound differs")
    for name in (
        "exact_status_and_selected_object_identity_preserved",
        "structurally_admitted_to_enriched_cp43_cp42_reference_codomain",
        "structural_validation_is_nonexecuting_and_nonreplaying",
        "source_law_assumption_only",
    ):
        _exact_bool(values[name], True, name="result." + name)
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
        _exact_bool(values[name], False, name="result." + name)
    _require_sha256(values["result_sha256"], name="result.digest")
    if values["result_sha256"] != _semantic_digest(_result_payload(values)):
        raise ValueError("CP49 result digest differs")


def _make_result(
    certificate: CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate,
    cp48_result: _CP48_RESULT_TYPE,
) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionResult:
    (
        applied,
        status,
        comparison_count,
        selected_attempt,
        selected,
        selected_sha256,
    ) = _extract_semantic_children(cp48_result)
    is_selected = status == "selected"
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "checkpoint48_result": cp48_result,
        "checkpoint48_result_sha256": cp48_result.result_sha256,
        "checkpoint43_applied_decision": applied,
        "checkpoint43_applied_decision_sha256": applied.applied_decision_sha256,
        "run_id": cp48_result.run_id,
        "initialization_index": cp48_result.initialization_index,
        "draw_index": cp48_result.draw_index,
        "source_instance_sha256": cp48_result.source_instance_sha256,
        "byte_source_profile": cp48_result.byte_source_profile,
        "raw_bytes_sha256": cp48_result.raw_bytes_sha256,
        "source_full_words_sha256": cp48_result.source_full_words_sha256,
        "semantic_status": status,
        "comparison_count": comparison_count,
        "selected_attempt_index": selected_attempt,
        "selected_configuration": selected,
        "selected_configuration_sha256": selected_sha256,
        "selected_enriched_semantic_atom_fiber_nonempty": is_selected,
        "selected_configuration_value_fiber_nonempty": is_selected,
        "abstract_uniform_selection_mass_positive_under_assumptions": is_selected,
        "selected_conditioned_reference_law_defined_under_assumptions": is_selected,
        "selected_uniform_single_preimage_mass_denominator_log2": (
            64 * certificate.full_word_count if is_selected else None
        ),
        "exact_status_and_selected_object_identity_preserved": True,
        "structurally_admitted_to_enriched_cp43_cp42_reference_codomain": True,
        "structural_validation_is_nonexecuting_and_nonreplaying": True,
        "source_law_assumption_only": True,
        "operational_realization_certified": False,
        "backend_law_verified": False,
        "backend_totality_verified": False,
        "live_initializer_distribution_certified": False,
        "cp40_initializer_admission_certified": False,
        "general_initializer_admissible": False,
        "formal_test28_closed": False,
        "global_uniqueness_certified": False,
        "scientific_claim_promoted": False,
        "model_quality_claim_promoted": False,
        "generality_claim_promoted": False,
        "manuscript_claim_promoted": False,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _semantic_digest(_result_payload(values))
    return CounterKeyedInitialTiltRejectionFullSourceLawAdmissionResult(
        _construction_token=_RESULT_TOKEN,
        **values,
    )


class CounterKeyedInitialTiltRejectionFullSourceLawAdmissionOwner:
    """Immutable nonexecuting owner of one CP48-bound assumption gate."""

    __slots__ = (
        "_byte_source_execution_owner",
        "_byte_source_execution_owner_identity",
        "_assumption_declaration",
        "_assumption_declaration_identity",
        "_certificate",
        "_certificate_identity",
        "_certificate_snapshot",
        "_certificate_snapshot_identity",
        "_parent_owner_snapshot",
        "_parent_validate_result",
        "_parent_live_revalidate",
        "_certificate_validator",
        "_description_builder",
        "_description_validator",
        "_result_builder",
        "_result_validator",
        "_local_surface_guard",
        "_local_surface_guard_identity",
        "_exact_uint64_callback",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP49 owners cannot subclass")

    def __init__(
        self,
        byte_source_execution_owner: _CP48_OWNER_TYPE,
        assumption_declaration: CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration,
        certificate: CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("CP49 owners require certification")
        _LOCAL_SURFACE_GUARD()
        if type(byte_source_execution_owner) is not _CP48_OWNER_TYPE:
            raise TypeError("byte_source_execution_owner has the wrong exact CP48 type")
        declaration = validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_assumption_declaration(
            assumption_declaration
        )
        checked = _validate_certificate(certificate)
        parent = _CP48_CERTIFICATE_PROPERTY.__get__(
            byte_source_execution_owner, _CP48_OWNER_TYPE
        )
        if checked.byte_source_execution_certificate is not parent:
            raise ValueError("CP49 owner certificate belongs to another CP48 owner")
        if checked.assumption_declaration is not declaration:
            raise ValueError("CP49 owner certificate uses another assumption")
        if checked.byte_source_execution_owner_runtime_identity != id(
            byte_source_execution_owner
        ):
            raise ValueError("CP49 owner runtime identity differs")
        certificate_snapshot = tuple(
            getattr(checked, name) for name in _certificate_fields()
        )
        bindings = (
            ("_byte_source_execution_owner", byte_source_execution_owner),
            ("_byte_source_execution_owner_identity", byte_source_execution_owner),
            ("_assumption_declaration", declaration),
            ("_assumption_declaration_identity", declaration),
            ("_certificate", checked),
            ("_certificate_identity", checked),
            ("_certificate_snapshot", certificate_snapshot),
            ("_certificate_snapshot_identity", certificate_snapshot),
            ("_parent_owner_snapshot", _CP48_OWNER_SNAPSHOT),
            ("_parent_validate_result", _CP48_VALIDATE_RESULT),
            ("_parent_live_revalidate", _CP48_LIVE_REVALIDATE),
            ("_certificate_validator", _validate_certificate),
            ("_description_builder", _make_description),
            ("_description_validator", _validate_description_values),
            ("_result_builder", _make_result),
            ("_result_validator", _validate_result_values),
            ("_local_surface_guard", _LOCAL_SURFACE_GUARD),
            ("_local_surface_guard_identity", _LOCAL_SURFACE_GUARD),
            ("_exact_uint64_callback", _EXACT_UINT64),
            ("_sealed", True),
        )
        for name, value in bindings:
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("CP49 owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("CP49 owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP49 owners are not pickleable")

    @property
    def certificate(
        self,
    ) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate:
        return self._certificate

    @property
    def byte_source_execution_owner(self) -> _CP48_OWNER_TYPE:
        return self._byte_source_execution_owner

    @property
    def assumption_declaration(
        self,
    ) -> CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration:
        return self._assumption_declaration

    def _owner_snapshot(self) -> Tuple[object, ...]:
        guard = self._local_surface_guard
        if guard is not self._local_surface_guard_identity:
            raise ValueError("CP49 local surface guard identity changed")
        if globals().get("_LOCAL_SURFACE_GUARD") is not guard:
            raise ValueError("CP49 local surface guard binding changed")
        guard()
        property_expectations = (
            ("certificate", _OWNER_CERTIFICATE_PROPERTY),
            (
                "byte_source_execution_owner",
                _OWNER_BYTE_SOURCE_EXECUTION_OWNER_PROPERTY,
            ),
            ("assumption_declaration", _OWNER_ASSUMPTION_DECLARATION_PROPERTY),
        )
        for name, expected in property_expectations:
            if getattr(_OWNER_TYPE_IDENTITY, name) is not expected:
                raise ValueError("CP49 owner property surface changed: " + name)
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("CP49 owner seal differs")
        current = (
            self._byte_source_execution_owner,
            self._assumption_declaration,
            self._certificate,
            self._certificate_snapshot,
            self._local_surface_guard,
        )
        frozen = (
            self._byte_source_execution_owner_identity,
            self._assumption_declaration_identity,
            self._certificate_identity,
            self._certificate_snapshot_identity,
            self._local_surface_guard_identity,
        )
        if any(actual is not expected for actual, expected in zip(current, frozen)):
            raise ValueError("CP49 owner identity changed")
        callbacks = (
            (self._parent_owner_snapshot, _CP48_OWNER_SNAPSHOT),
            (self._parent_validate_result, _CP48_VALIDATE_RESULT),
            (self._parent_live_revalidate, _CP48_LIVE_REVALIDATE),
            (self._certificate_validator, _validate_certificate),
            (self._description_builder, _make_description),
            (self._description_validator, _validate_description_values),
            (self._result_builder, _make_result),
            (self._result_validator, _validate_result_values),
            (self._local_surface_guard, _LOCAL_SURFACE_GUARD),
            (self._exact_uint64_callback, _EXACT_UINT64),
        )
        if any(actual is not expected for actual, expected in callbacks):
            raise ValueError("CP49 cached callback identity changed")
        checked = self._certificate_validator(self._certificate)
        if checked is not self._certificate_identity:
            raise ValueError("CP49 certificate identity changed")
        if tuple(getattr(checked, name) for name in _certificate_fields()) != (
            self._certificate_snapshot
        ):
            raise ValueError("CP49 certificate changed")
        if checked.assumption_declaration is not self._assumption_declaration:
            raise ValueError("CP49 assumption identity changed")
        parent = _CP48_CERTIFICATE_PROPERTY.__get__(
            self._byte_source_execution_owner, _CP48_OWNER_TYPE
        )
        if checked.byte_source_execution_certificate is not parent:
            raise ValueError("CP49 parent certificate identity changed")
        self._parent_owner_snapshot(self._byte_source_execution_owner)
        return current

    def describe(
        self,
        run_id: object,
        initialization_index: object,
        draw_index: object,
    ) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionDescription:
        """Describe one pointwise fixed-request theorem without source work."""

        snapshot = self._owner_snapshot()
        checked_run = self._exact_uint64_callback(run_id, name="run_id")
        checked_initialization = self._exact_uint64_callback(
            initialization_index, name="initialization_index"
        )
        checked_draw = self._exact_uint64_callback(draw_index, name="draw_index")
        result = self._description_builder(
            self._certificate,
            checked_run,
            checked_initialization,
            checked_draw,
        )
        self._description_validator(
            {name: getattr(result, name) for name in _description_fields()},
            trusted_certificate=self._certificate,
        )
        current = self._owner_snapshot()
        if any(actual is not expected for actual, expected in zip(current, snapshot)):
            raise ValueError("CP49 owner changed during description")
        return result

    def admit_returned_result(
        self, cp48_result: object
    ) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionResult:
        """Structurally admit one returned CP48 record without executing source."""

        if type(cp48_result) is not _CP48_RESULT_TYPE:
            raise TypeError("cp48_result has the wrong exact CP48 type")
        snapshot = self._owner_snapshot()
        checked_parent = self._parent_validate_result(
            self._byte_source_execution_owner,
            cp48_result,
        )
        if checked_parent is not cp48_result:
            raise ValueError("CP49 CP48 validation substituted its result")
        result = self._result_builder(self._certificate, cp48_result)
        self._result_validator(
            {name: getattr(result, name) for name in _result_fields()},
            trusted_certificate=self._certificate,
        )
        current = self._owner_snapshot()
        if any(actual is not expected for actual, expected in zip(current, snapshot)):
            raise ValueError("CP49 owner changed during result admission")
        return result

    def validate_admission_result(
        self, result: object
    ) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionResult:
        """Structurally validate CP49 and CP48 custody without replay."""

        if (
            type(result)
            is not CounterKeyedInitialTiltRejectionFullSourceLawAdmissionResult
        ):
            raise TypeError("result has the wrong exact CP49 type")
        snapshot = self._owner_snapshot()
        record_snapshot = tuple(getattr(result, name) for name in _result_fields())
        checked_parent = self._parent_validate_result(
            self._byte_source_execution_owner,
            result.checkpoint48_result,
        )
        if checked_parent is not result.checkpoint48_result:
            raise ValueError("CP49 CP48 validation substituted its result")
        self._result_validator(
            {name: getattr(result, name) for name in _result_fields()},
            trusted_certificate=self._certificate,
        )
        if tuple(getattr(result, name) for name in _result_fields()) != record_snapshot:
            raise ValueError("CP49 result changed during validation")
        current = self._owner_snapshot()
        if any(actual is not expected for actual, expected in zip(current, snapshot)):
            raise ValueError("CP49 owner changed during result validation")
        return result

    def revalidate_live_ancestry(
        self,
    ) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate:
        """Explicitly replay CP48 live ancestry; never acquire source bytes."""

        snapshot = self._owner_snapshot()
        parent = self._parent_live_revalidate(self._byte_source_execution_owner)
        if parent is not self._certificate.byte_source_execution_certificate:
            raise ValueError("CP49 CP48 live certificate identity differs")
        current = self._owner_snapshot()
        if any(actual is not expected for actual, expected in zip(current, snapshot)):
            raise ValueError("CP49 owner changed during live revalidation")
        return self._certificate


_OWNER_TYPE_IDENTITY = CounterKeyedInitialTiltRejectionFullSourceLawAdmissionOwner
_OWNER_CERTIFICATE_PROPERTY = _OWNER_TYPE_IDENTITY.certificate
_OWNER_BYTE_SOURCE_EXECUTION_OWNER_PROPERTY = (
    _OWNER_TYPE_IDENTITY.byte_source_execution_owner
)
_OWNER_ASSUMPTION_DECLARATION_PROPERTY = _OWNER_TYPE_IDENTITY.assumption_declaration


def certify_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission(
    byte_source_execution_owner: object,
    assumption_declaration: object,
    *,
    admission_policy: object,
    admission_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionOwner:
    """Certify one exact CP48-bound, nonexecuting CP49 theorem owner."""

    _LOCAL_SURFACE_GUARD()
    if type(byte_source_execution_owner) is not _CP48_OWNER_TYPE:
        raise TypeError("byte_source_execution_owner has the wrong exact CP48 type")
    declaration = validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_assumption_declaration(
        assumption_declaration
    )
    _require_text(admission_policy, _POLICY, name="admission_policy")
    role = _require_sha256(admission_role_sha256, name="admission_role_sha256")
    _require_dependency_surfaces()
    if (
        globals().get("CounterKeyedInitialTiltRejectionFullSourceLawAdmissionOwner")
        is not _OWNER_TYPE_IDENTITY
    ):
        raise ValueError("CP49 owner type surface changed")
    parent_snapshot = _CP48_OWNER_SNAPSHOT(byte_source_execution_owner)
    parent = _CP48_CERTIFICATE_PROPERTY.__get__(
        byte_source_execution_owner, _CP48_OWNER_TYPE
    )
    parent = _CP48_VALIDATE_CERTIFICATE(parent)
    if declaration.checkpoint48_certificate_sha256 != parent.certificate_sha256:
        raise ValueError("assumption belongs to another CP48 certificate")
    if declaration.source_instance_sha256 != parent.source_instance_sha256:
        raise ValueError("assumption source instance differs")
    if declaration.byte_source_profile != parent.byte_source_profile:
        raise ValueError("assumption profile differs")
    certificate = _make_certificate(byte_source_execution_owner, declaration, role)
    owner = CounterKeyedInitialTiltRejectionFullSourceLawAdmissionOwner(
        byte_source_execution_owner,
        declaration,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    current = _CP48_OWNER_SNAPSHOT(byte_source_execution_owner)
    if len(current) != len(parent_snapshot) or any(
        actual is not expected for actual, expected in zip(current, parent_snapshot)
    ):
        raise ValueError("CP48 owner changed during CP49 certification")
    owner._owner_snapshot()
    return owner


def require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission(
    byte_source_execution_owner: object,
    assumption_declaration: object,
    owner: object,
    *,
    admission_policy: object,
    admission_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionOwner:
    _LOCAL_SURFACE_GUARD()
    if type(byte_source_execution_owner) is not _CP48_OWNER_TYPE:
        raise TypeError("byte_source_execution_owner has the wrong exact CP48 type")
    declaration = validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_assumption_declaration(
        assumption_declaration
    )
    if type(owner) is not CounterKeyedInitialTiltRejectionFullSourceLawAdmissionOwner:
        raise TypeError("owner has the wrong exact CP49 type")
    _require_text(admission_policy, _POLICY, name="admission_policy")
    role = _require_sha256(admission_role_sha256, name="admission_role_sha256")
    snapshot = owner._owner_snapshot()
    if (
        _OWNER_BYTE_SOURCE_EXECUTION_OWNER_PROPERTY.__get__(owner, _OWNER_TYPE_IDENTITY)
        is not byte_source_execution_owner
    ):
        raise ValueError("CP49 owner belongs to another CP48 owner")
    if (
        _OWNER_ASSUMPTION_DECLARATION_PROPERTY.__get__(owner, _OWNER_TYPE_IDENTITY)
        is not declaration
    ):
        raise ValueError("CP49 owner uses another assumption declaration")
    certificate = _OWNER_CERTIFICATE_PROPERTY.__get__(owner, _OWNER_TYPE_IDENTITY)
    if certificate.admission_role_sha256 != role:
        raise ValueError("CP49 owner uses another admission role")
    if certificate.admission_policy != _POLICY:
        raise ValueError("CP49 owner uses another admission policy")
    current = owner._owner_snapshot()
    if any(actual is not expected for actual, expected in zip(current, snapshot)):
        raise ValueError("CP49 owner changed during matching")
    return owner


def validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission_certificate(
    byte_source_execution_owner: object,
    assumption_declaration: object,
    owner: object,
    *,
    admission_policy: object,
    admission_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate:
    matched = require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission(
        byte_source_execution_owner,
        assumption_declaration,
        owner,
        admission_policy=admission_policy,
        admission_role_sha256=admission_role_sha256,
    )
    return _OWNER_CERTIFICATE_PROPERTY.__get__(matched, _OWNER_TYPE_IDENTITY)


def _runtime_sha256() -> str:
    """Process-local CP49 code/context witness, not loaded-code attestation."""

    owner_type = globals().get(
        "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionOwner"
    )
    if owner_type is None:
        raise ValueError("CP49 owner type is not loaded")
    owner_methods = (
        "__init__",
        "__setattr__",
        "__delattr__",
        "__reduce_ex__",
        "_owner_snapshot",
        "describe",
        "admit_returned_result",
        "validate_admission_result",
        "revalidate_live_ancestry",
    )
    payload = {
        "schema": _SCHEMA_VERSION,
        "python_version": _PYTHON_VERSION,
        "python_implementation": _PYTHON_IMPLEMENTATION,
        "code_fingerprint_format": _CODE_FINGERPRINT_FORMAT,
    }
    for name in owner_methods:
        payload["owner." + name] = _CODE_SHA256(getattr(owner_type, name))
    for name in (
        "certificate",
        "byte_source_execution_owner",
        "assumption_declaration",
    ):
        descriptor = getattr(owner_type, name)
        if type(descriptor) is not property or descriptor.fget is None:
            raise ValueError("CP49 owner property surface differs: " + name)
        payload["owner." + name + ".fget"] = _CODE_SHA256(descriptor.fget)
    frozen = globals().get("_FROZEN_LOCAL_SURFACES", ())
    for name, value in frozen:
        if getattr(value, "__code__", None) is not None:
            payload["local." + name] = _CODE_SHA256(value)
    local_guard = globals().get("_require_local_surfaces")
    if getattr(local_guard, "__code__", None) is not None:
        payload["local._require_local_surfaces"] = _CODE_SHA256(local_guard)
    return _semantic_digest(payload)


_FROZEN_LOCAL_SURFACE_NAMES = (
    "_execution",
    "_JSON_DUMPS",
    "_SHA256",
    "_PYTHON_VERSION",
    "_PYTHON_IMPLEMENTATION",
    "_CODE_FINGERPRINT_FORMAT",
    "_SCHEMA_VERSION",
    "_POLICY",
    "_SCOPE",
    "_ASSUMPTION_MODE",
    "_ASSUMPTION_SCOPE",
    "_STATUSES",
    "_PUSHFORWARD_THEOREM",
    "_RETURN_CAVEAT",
    "_SELECTED_THEOREM",
    "_SEQUENCE_NONCLAIM",
    "_D",
    "_ZERO_SHA256",
    "_DECLARATION_TOKEN",
    "_CERTIFICATE_TOKEN",
    "_DESCRIPTION_TOKEN",
    "_RESULT_TOKEN",
    "_OWNER_TOKEN",
    "_CP48_OWNER_TYPE",
    "_CP48_CERT_TYPE",
    "_CP48_RESULT_TYPE",
    "_CP48_VALIDATE_CERTIFICATE",
    "_CP48_VALIDATE_RESULT_RECORD",
    "_CP48_OWNER_SNAPSHOT",
    "_CP48_VALIDATE_RESULT",
    "_CP48_LIVE_REVALIDATE",
    "_CP48_CERTIFICATE_PROPERTY",
    "_CP48_SOURCE_MODEL_OWNER_PROPERTY",
    "_CP48_REQUIRE_DEPENDENCY_SURFACES",
    "_CP48_REQUIRE_LOCAL_SURFACES",
    "_EXACT_UINT64",
    "_RUNTIME_DEFAULT_FINGERPRINT",
    "_CODE_SHA256",
    "_CP48_PROFILE_SYSTEM_OS_URANDOM_OPERATIONAL",
    "_CP48_PROFILE_EXTERNAL_EXACT_BYTE_BLOCK_UNVERIFIED",
    "_CP48_PROFILES",
    "PluginBridgeCounterKeyedInitialTiltRejectionFullSourceLawAdmissionError",
    "_without",
    "_canonical",
    "_semantic_digest",
    "_require_sha256",
    "_require_text",
    "_exact_true",
    "_exact_bool",
    "_exact_nonnegative_integer",
    "_exact_positive_integer",
    "_exact_profile",
    "_uniform_fiber_probability",
    "_return_conditioned_fiber_probability",
    "_checkpoint43_certificate",
    "_process_context_sha256",
    "_require_dependency_surfaces",
    "CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration",
    "_declaration_fields",
    "_declaration_payload",
    "_validate_declaration_values",
    "declare_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_assumption",
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_assumption_declaration",
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate",
    "_certificate_fields",
    "_certificate_payload",
    "_CERTIFICATE_TRUE_FLAGS",
    "_CERTIFICATE_FALSE_FLAGS",
    "_validate_certificate_values",
    "_validate_certificate",
    "_make_certificate",
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionDescription",
    "_description_fields",
    "_description_payload",
    "_validate_description_values",
    "_make_description",
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionResult",
    "_result_fields",
    "_result_payload",
    "_extract_semantic_children",
    "_validate_result_values",
    "_make_result",
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionOwner",
    "_OWNER_TYPE_IDENTITY",
    "_OWNER_CERTIFICATE_PROPERTY",
    "_OWNER_BYTE_SOURCE_EXECUTION_OWNER_PROPERTY",
    "_OWNER_ASSUMPTION_DECLARATION_PROPERTY",
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission",
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission",
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission_certificate",
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
        raise ValueError("CP49 dependency guard changed")
    if namespace.get("_FROZEN_LOCAL_SURFACES") is not frozen:
        raise ValueError("CP49 frozen local surfaces changed")
    if namespace.get("_FROZEN_LOCAL_SURFACE_NAMES") is not frozen_names:
        raise ValueError("CP49 frozen local surface names changed")
    for name, expected in frozen:
        if namespace.get(name) is not expected:
            raise ValueError("CP49 local surface changed: " + name)
    dependency_guard()


_LOCAL_SURFACE_GUARD = _require_local_surfaces


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ADMISSION_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ADMISSION_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ADMISSION_SCOPE",
    "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ASSUMPTION_MODE",
    "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_ASSUMPTION_SCOPE",
    "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SEMANTIC_STATUSES",
    "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_PUSHFORWARD_THEOREM",
    "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_RETURN_CONDITIONING_CAVEAT",
    "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SELECTED_FIBER_THEOREM",
    "INITIAL_TILT_REJECTION_FULL_SOURCE_LAW_SEQUENCE_NONCLAIM",
    "CounterKeyedInitialTiltRejectionFullSourceLawAssumptionDeclaration",
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionCertificate",
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionDescription",
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionResult",
    "CounterKeyedInitialTiltRejectionFullSourceLawAdmissionOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionFullSourceLawAdmissionError",
    "declare_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_assumption",
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_assumption_declaration",
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission",
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission",
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission_certificate",
]
