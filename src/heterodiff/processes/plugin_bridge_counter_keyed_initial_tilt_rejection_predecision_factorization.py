"""Evaluate a staged decision-word-free predecision reference semantics.

This additive checkpoint binds one exact checkpoint-41 owner and its transitive
checkpoint-36/37 ancestry.  Its executable ``G`` stage accepts proposal and
scoring words ``V`` only.  A separate ``H`` stage accepts reserved decision
words only after a complete quota tuple exists.  The implementation is a
reference semantics assembled from identity-bound direct checkpoint-28/30
callbacks and the checkpoint-37 quota primitive under a trusted, unchanged
transitive runtime.  It is not a proof of universal equivalence to the live
checkpoint-36/37 failure behavior or of loaded-code closure integrity.

The ``preparation_failure`` tag is retained in the public codomain so that the
record schema matches the checkpoint-41 mathematical union.  It is reserved:
the current evaluator never constructs it and validation refuses it.  All
checkpoint-28/30 exceptions remain operational refusals.  Only an exact
checkpoint-37 quota-certification error, after independent exact gap
preflight, is collapsed to ``quota_certification_failure``.

Hashes and runtime identities are same-process procedural custody witnesses.
They are not cryptographic authentication or portable loaded-code evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

_LOCAL_NAMESPACE_GETTER = globals
_LOCAL_NAMESPACE = _LOCAL_NAMESPACE_GETTER()
_LOCAL_NAMESPACE_ERROR = ValueError
_MISSING_LOCAL_GLOBAL = object()
_FROZEN_ABSENT_LOCAL_RUNTIME_GLOBALS = (
    "ArithmeticError",
    "AttributeError",
    "ModuleNotFoundError",
    "TypeError",
    "ValueError",
    "any",
    "bool",
    "enumerate",
    "float",
    "getattr",
    "globals",
    "id",
    "int",
    "len",
    "list",
    "max",
    "object",
    "property",
    "range",
    "set",
    "sorted",
    "str",
    "super",
    "tuple",
    "type",
    "zip",
)


def _require_unshadowed_local_runtime(
    namespace_getter: object = _LOCAL_NAMESPACE_GETTER,
    namespace: Dict[str, object] = _LOCAL_NAMESPACE,
    absent_names: Tuple[str, ...] = _FROZEN_ABSENT_LOCAL_RUNTIME_GLOBALS,
    missing: object = _MISSING_LOCAL_GLOBAL,
    error_type: object = _LOCAL_NAMESPACE_ERROR,
) -> None:
    for name in absent_names:
        if name in namespace:
            raise error_type("CP42 absent runtime global %s was injected" % name)
    if namespace_getter() is not namespace:
        raise error_type("CP42 captured module namespace changed")
    expectations = (
        ("_LOCAL_NAMESPACE_GETTER", namespace_getter),
        ("_LOCAL_NAMESPACE", namespace),
        ("_FROZEN_ABSENT_LOCAL_RUNTIME_GLOBALS", absent_names),
        ("_MISSING_LOCAL_GLOBAL", missing),
        ("_LOCAL_NAMESPACE_ERROR", error_type),
    )
    for name, expected in expectations:
        if name not in namespace or namespace[name] is not expected:
            raise error_type("CP42 local runtime guard binding changed: %s" % name)


try:
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law,
    )

    _source = (
        plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "predecision factorization requires the optional PyTorch "
            "reference dependency; install the 'reference' extra"
        ) from error
    raise


_PUBLIC_SCHEMA_VERSION_NAME = (
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_"
    "PREDECISION_FACTORIZATION_SCHEMA_VERSION"
)
_LOCAL_NAMESPACE[_PUBLIC_SCHEMA_VERSION_NAME] = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-predecision-" "factorization-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_POLICY = (
    "exact-checkpoint41-owner-hypothesis-and-transitive-checkpoint36-37-binding;"
    "exact-proposal-coordinate-order-and-uint64-V-only-random-word-input;"
    "identity-bound-direct-checkpoint28-transform-and-checkpoint30-score-callbacks;"
    "complete-checkpoint37-quota-tuple-before-separate-decision-stage;"
    "reserved-preparation-failure-and-modeled-quota-failure-union;"
    "successful-per-instance-live-projection-parity-witness;"
    "no-live-failure-equivalence-assumption-discharge-or-source-law-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_SCOPE = (
    "bounded-staged-reference-semantics-G-r-j-of-V-and-H-of-G-W;"
    "preparation-failure-tag-reserved-and-not-executable;"
    "quota-failure-only-after-exact-valid-gap-preflight;"
    "not-universal-live-checkpoint36-37-failure-equivalence;"
    "not-checkpoint41-factorization-assumption-discharge;"
    "not-whole-record-invariance-or-live-Philox-source-law;"
    "not-numeric-fibers-failure-probabilities-initializer-path-or-sampler;"
    "not-scientific-model-quality-or-generality-evidence;"
    "concurrent-or-ABA-external-record-mutation-out-of-scope;"
    "transitive-callback-loaded-code-integrity-and-concurrent-monkeypatch-out-"
    "of-scope;"
    "trusted-runtime-procedural-not-portable-or-cryptographic-custody"
)

INITIAL_TILT_REJECTION_PREDECISION_STATUSES = (
    "preparation_failure",
    "quota_certification_failure",
    "ready",
)
INITIAL_TILT_REJECTION_APPLIED_DECISION_STATUSES = (
    "preparation_failure",
    "quota_certification_failure",
    "selected",
    "exhausted",
)
INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_THEOREM = (
    "for-every-valid-r-j-and-V-the-executable-predecision-is-G_{r,j}(V)-with-"
    "no-W-argument-and-V-is-the-only-random-word-input;"
    "H-passes-through-validated-modeled-failure-without-reading-W;"
    "for-ready-G-all-A-quotas-exist-before-H-validates-W-and-before-the-first-"
    "comparison-w_i<K_i"
)

INITIAL_TILT_REJECTION_PREDECISION_DYADIC_DENOMINATOR = 1 << 64
INITIAL_TILT_REJECTION_PREDECISION_MAX_ATTEMPTS = 64
INITIAL_TILT_REJECTION_PREDECISION_MAX_PROPOSAL_WORDS = 65_536

_SCHEMA_VERSION = _LOCAL_NAMESPACE[_PUBLIC_SCHEMA_VERSION_NAME]
_POLICY = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_POLICY
)
_SCOPE = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_SCOPE
)
_THEOREM = INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_THEOREM
_D = INITIAL_TILT_REJECTION_PREDECISION_DYADIC_DENOMINATOR
_ZERO_SHA256 = "0" * 64

_prep = _source._prep
_decision = _source._decision

_CP41_OWNER_TYPE = _source.CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner
_CP41_CERT_TYPE = (
    _source.CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate
)
_CP41_HYPOTHESIS_TYPE = _source.InitialTiltRejectionPredecisionFactorizationHypothesis
_CP40_CERT_TYPE = _source._CP40_CERT_TYPE
_CP39_CERT_TYPE = _source._CP39_CERT_TYPE
_CP38_CERT_TYPE = _source._CP38_CERT_TYPE
_CP37_OWNER_TYPE = _source._CP37_OWNER_TYPE
_CP37_CERT_TYPE = _source._CP37_CERT_TYPE
_CP37_RESULT_TYPE = _decision.CounterKeyedInitialTiltRejectionDecisionResult
_CP36_OWNER_TYPE = _source._CP36_OWNER_TYPE
_CP36_CERT_TYPE = _source._CP36_CERT_TYPE
_CONFIGURATION_TYPE = Tuple[_prep.TransformedEvent, ...]
_COORDINATE_TYPE = Tuple[Tuple[int, int], Tuple[int, int, int, int], int]

_CP41_CERTIFICATE_PROPERTY = _CP41_OWNER_TYPE.certificate
_CP41_PARENT_PROPERTY = _CP41_OWNER_TYPE.admission_owner
_CP41_HYPOTHESIS_PROPERTY = _CP41_OWNER_TYPE.factorization_hypothesis
_CP41_OWNER_SNAPSHOT = _CP41_OWNER_TYPE._owner_snapshot
_CP41_REQUIRE_OWNER_SNAPSHOT = _CP41_OWNER_TYPE._require_owner_snapshot
_CP41_LIVE_CERTIFICATE = _CP41_OWNER_TYPE._live_certificate
_CP41_BOUND_ANCESTRY = _source._bound_ancestry
_CP41_PARTITION_COORDINATES = _source._partition_coordinates
_CP41_COORDINATE_DIGEST = _source._coordinate_digest
_CP41_VALIDATE_COORDINATE_TUPLE = _source._validate_coordinate_tuple
_CP41_VALIDATE_CERTIFICATE = _source._validate_certificate
_CP41_VALIDATE_HYPOTHESIS = _source._validate_factorization_hypothesis
_CP41_REQUIRE_SURFACES = _source._require_surfaces

_CP40_OWNER_TYPE = _source._CP40_OWNER_TYPE
_CP40_OWNER_SNAPSHOT = _CP40_OWNER_TYPE._owner_snapshot
_CP40_REQUIRE_OWNER_SNAPSHOT = _CP40_OWNER_TYPE._require_owner_snapshot
_CP39_OWNER_TYPE = _source._CP39_OWNER_TYPE
_CP39_OWNER_SNAPSHOT = _CP39_OWNER_TYPE._owner_snapshot
_CP39_REQUIRE_OWNER_SNAPSHOT = _CP39_OWNER_TYPE._require_owner_snapshot
_CP38_OWNER_TYPE = _source._CP38_OWNER_TYPE
_CP38_OWNER_SNAPSHOT = _CP38_OWNER_TYPE._owner_snapshot
_CP38_REQUIRE_OWNER_SNAPSHOT = _CP38_OWNER_TYPE._require_owner_snapshot

_CP37_CERTIFICATE_PROPERTY = _CP37_OWNER_TYPE.certificate
_CP37_PARENT_PROPERTY = _CP37_OWNER_TYPE.preparation_owner
_CP37_OWNER_SNAPSHOT = _CP37_OWNER_TYPE._owner_snapshot
_CP37_REQUIRE_OWNER_SNAPSHOT = _CP37_OWNER_TYPE._require_owner_snapshot
_CP37_LIVE_CERTIFICATE = _CP37_OWNER_TYPE._live_certificate
_CP37_VALIDATE_RESULT = _CP37_OWNER_TYPE.validate_result
_CP37_VALIDATE_CERTIFICATE = _decision._validate_certificate
_CP37_QUOTA = _decision._floor_exp_uint64_quota
_CP37_QUOTA_ERROR = _decision.PluginBridgeCounterKeyedInitialTiltRejectionDecisionError
_CP37_FRACTION_PARTS = _decision._fraction_parts

_CP36_CERTIFICATE_PROPERTY = _CP36_OWNER_TYPE.certificate
_CP36_OWNER_SNAPSHOT = _CP36_OWNER_TYPE._owner_snapshot
_CP36_REQUIRE_OWNER_SNAPSHOT = _CP36_OWNER_TYPE._require_owner_snapshot
_CP36_LIVE_CERTIFICATE = _CP36_OWNER_TYPE._live_certificate
_CP36_REQUIRE_DEPENDENCY_RETURN = _CP36_OWNER_TYPE._require_dependency_return
_CP36_VALIDATE_CERTIFICATE = _prep._validate_certificate
_CP36_REQUIRE_PARENT_SURFACES = _prep._require_parent_surfaces

_SLOT_MATERIALIZER = _prep._CP28_MATERIALIZE_SLOT_FIELDS
_MATERIALIZED_PREFLIGHT = _prep._preflight_materialized_slot_fields
_MATERIALIZED_SNAPSHOT = _prep._materialized_slot_fields_snapshot
_MATERIALIZED_UNCHANGED = _prep._require_materialized_slot_fields_unchanged
_QUOTA_POSITION = _prep._CP28_QUOTA_POSITION
_SLOT_MAKER = _prep._CP28_MAKE_SLOT
_SLOT_PREFLIGHT = _prep._preflight_raw_slot
_SLOT_VALIDATOR = _prep._CP28_VALIDATE_SLOT_RECORD
_SLOT_SNAPSHOT = _prep._slot_operation_snapshot
_SLOT_UNCHANGED = _prep._require_slot_operation_unchanged
_EVENT_MODEL_KEY = _prep._EVENT_MODEL_KEY
_CONFIGURATION_SHA256 = _prep._CP28_CONFIGURATION_SHA256
_CONFIGURATION_PREFLIGHT = _prep._preflight_configuration
_TILT_EVALUATE = _prep._TILT_EVALUATE
_TILT_PREFLIGHT = _prep._preflight_tilt_evaluation
_SCORE_SNAPSHOT = _prep._score_operation_snapshot
_SCORE_UNCHANGED = _prep._require_score_operation_unchanged
_TILT_VALIDATE = _prep._TILT_VALIDATE_EVALUATION
_CP28_MAX_RAW_SLOTS = _prep._reference.COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS
_CP28_MAX_COORDINATE_DIMENSION = _prep._reference.MAX_TRANSFORMED_COORDINATE_DIMENSION

_MISSING_PROVIDER_GLOBAL = object()

_CRITICAL_PROVIDER_SURFACES = (
    (_source, "_bound_ancestry", _CP41_BOUND_ANCESTRY),
    (_source, "_partition_coordinates", _CP41_PARTITION_COORDINATES),
    (_source, "_coordinate_digest", _CP41_COORDINATE_DIGEST),
    (_source, "_validate_coordinate_tuple", _CP41_VALIDATE_COORDINATE_TUPLE),
    (_prep, "_CP28_MATERIALIZE_SLOT_FIELDS", _SLOT_MATERIALIZER),
    (_prep, "_preflight_materialized_slot_fields", _MATERIALIZED_PREFLIGHT),
    (_prep, "_materialized_slot_fields_snapshot", _MATERIALIZED_SNAPSHOT),
    (_prep, "_require_materialized_slot_fields_unchanged", _MATERIALIZED_UNCHANGED),
    (_prep, "_CP28_QUOTA_POSITION", _QUOTA_POSITION),
    (_prep, "_CP28_MAKE_SLOT", _SLOT_MAKER),
    (_prep, "_preflight_raw_slot", _SLOT_PREFLIGHT),
    (_prep, "_CP28_VALIDATE_SLOT_RECORD", _SLOT_VALIDATOR),
    (_prep, "_slot_operation_snapshot", _SLOT_SNAPSHOT),
    (_prep, "_require_slot_operation_unchanged", _SLOT_UNCHANGED),
    (_prep, "_EVENT_MODEL_KEY", _EVENT_MODEL_KEY),
    (_prep, "_CP28_CONFIGURATION_SHA256", _CONFIGURATION_SHA256),
    (_prep, "_preflight_configuration", _CONFIGURATION_PREFLIGHT),
    (_prep, "_TILT_EVALUATE", _TILT_EVALUATE),
    (_prep, "_preflight_tilt_evaluation", _TILT_PREFLIGHT),
    (_prep, "_score_operation_snapshot", _SCORE_SNAPSHOT),
    (_prep, "_require_score_operation_unchanged", _SCORE_UNCHANGED),
    (_prep, "_TILT_VALIDATE_EVALUATION", _TILT_VALIDATE),
    (_decision, "_floor_exp_uint64_quota", _CP37_QUOTA),
    (_decision, "_fraction_parts", _CP37_FRACTION_PARTS),
    (
        _decision,
        "PluginBridgeCounterKeyedInitialTiltRejectionDecisionError",
        _CP37_QUOTA_ERROR,
    ),
    (_decision, "_QuotaData", _decision._QuotaData),
    (_decision, "Fraction", _decision.Fraction),
    (_decision, "_exact_dyadic_decimal", _decision._exact_dyadic_decimal),
    (
        _decision,
        "_nonnegative_integer_decimal_digits",
        _decision._nonnegative_integer_decimal_digits,
    ),
    (_decision, "_signed_integer", _decision._signed_integer),
    (_decision, "_exact_integer", _decision._exact_integer),
    (_decision, "_precision_schedule", _decision._precision_schedule),
    (_decision, "_decimal_context", _decision._decimal_context),
    (_decision, "_D", _decision._D),
    (
        _decision,
        "INITIAL_TILT_REJECTION_DECISION_ZERO_QUOTA_LOG_CUTOFF",
        _decision.INITIAL_TILT_REJECTION_DECISION_ZERO_QUOTA_LOG_CUTOFF,
    ),
    (
        _decision,
        "INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS",
        _decision.INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS,
    ),
    (
        _decision,
        "INITIAL_TILT_REJECTION_DECISION_MAX_EXACT_INTEGER_BITS",
        _decision.INITIAL_TILT_REJECTION_DECISION_MAX_EXACT_INTEGER_BITS,
    ),
    (
        _decision,
        "INITIAL_TILT_REJECTION_DECISION_PRIMARY_PRECISION",
        _decision.INITIAL_TILT_REJECTION_DECISION_PRIMARY_PRECISION,
    ),
    (
        _decision,
        "INITIAL_TILT_REJECTION_DECISION_AUDIT_PRECISION",
        _decision.INITIAL_TILT_REJECTION_DECISION_AUDIT_PRECISION,
    ),
    (
        _decision,
        "INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION",
        _decision.INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION,
    ),
    (_decision, "_DECIMAL_MIN_EXPONENT", _decision._DECIMAL_MIN_EXPONENT),
    (_decision, "_DECIMAL_MAX_EXPONENT", _decision._DECIMAL_MAX_EXPONENT),
    (_decision, "Decimal", _decision.Decimal),
    (_decision, "Context", _decision.Context),
    (_decision, "ROUND_HALF_EVEN", _decision.ROUND_HALF_EVEN),
    (_decision, "decimal", _decision.decimal),
    (
        _decision.decimal,
        "DecimalException",
        _decision.decimal.DecimalException,
    ),
    (
        _decision.decimal,
        "InvalidOperation",
        _decision.decimal.InvalidOperation,
    ),
    (_decision.decimal, "DivisionByZero", _decision.decimal.DivisionByZero),
    (_decision.decimal, "Overflow", _decision.decimal.Overflow),
    (_decision.decimal, "Underflow", _decision.decimal.Underflow),
    (
        _prep._reference,
        "COUNTER_KEYED_REFERENCE_INITIALIZER_MAX_RAW_SLOTS",
        _CP28_MAX_RAW_SLOTS,
    ),
    (
        _prep._reference,
        "MAX_TRANSFORMED_COORDINATE_DIMENSION",
        _CP28_MAX_COORDINATE_DIMENSION,
    ),
)

_ABSENT_PROVIDER_SURFACES = tuple(
    (_decision, name)
    for name in (
        "TypeError",
        "ValueError",
        "type",
        "tuple",
        "bool",
        "int",
        "isinstance",
        "abs",
        "divmod",
        "len",
        "list",
    )
)

_CERTIFICATE_TOKEN = object()
_ROW_TOKEN = object()
_PREDECISION_TOKEN = object()
_APPLIED_TOKEN = object()
_WITNESS_TOKEN = object()
_OWNER_TOKEN = object()


class PluginBridgeCounterKeyedInitialTiltRejectionPredecisionFactorizationError(
    ArithmeticError
):
    """Fail-closed staged-reference and procedural-custody error."""


_CP42_ERROR = PluginBridgeCounterKeyedInitialTiltRejectionPredecisionFactorizationError


def _semantic_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    omitted = set(names)
    return {name: value for name, value in values.items() if name not in omitted}


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _exact_integer(
    value: object,
    *,
    name: str,
    minimum: int = 0,
    maximum: int = (1 << 64) - 1,
) -> int:
    if type(value) is not int:
        raise TypeError("%s must be an exact integer" % name)
    if not minimum <= value <= maximum:
        raise ValueError("%s is outside its frozen bound" % name)
    return value


def _exact_bool(value: object, expected: bool, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be an exact Boolean" % name)
    if value is not expected:
        raise ValueError("%s differs" % name)
    return value


def _require_text(value: object, expected: str, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if value != expected:
        raise ValueError("%s differs" % name)
    return value


def _exact_words(value: object, *, name: str, length: int) -> Tuple[int, ...]:
    if type(value) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(value) != length or len(value) > _MAX_PROPOSAL_WORDS:
        raise ValueError("%s has the wrong bounded length" % name)
    for position, word in enumerate(value):
        _exact_integer(word, name="%s[%d]" % (name, position))
    return value


_MAX_PROPOSAL_WORDS = INITIAL_TILT_REJECTION_PREDECISION_MAX_PROPOSAL_WORDS


def _require_dependency_surfaces(
    frozen: Tuple[Tuple[object, str, object], ...] = _CRITICAL_PROVIDER_SURFACES,
    absent: Tuple[Tuple[object, str], ...] = _ABSENT_PROVIDER_SURFACES,
    local_guard: object = _require_unshadowed_local_runtime,
    namespace: Dict[str, object] = _LOCAL_NAMESPACE,
    error_type: object = _LOCAL_NAMESPACE_ERROR,
) -> None:
    local_guard()
    if (
        "_CRITICAL_PROVIDER_SURFACES" not in namespace
        or namespace["_CRITICAL_PROVIDER_SURFACES"] is not frozen
    ):
        raise error_type("CP42 frozen provider surfaces changed")
    if (
        "_ABSENT_PROVIDER_SURFACES" not in namespace
        or namespace["_ABSENT_PROVIDER_SURFACES"] is not absent
    ):
        raise error_type("CP42 absent provider surfaces changed")
    for module, name, expected in frozen:
        if name not in module.__dict__ or module.__dict__[name] is not expected:
            raise error_type("CP42 provider surface %s changed" % name)
    for module, name in absent:
        if name in module.__dict__:
            raise error_type("CP42 absent provider surface %s was injected" % name)
    _CP41_REQUIRE_SURFACES()
    _CP36_REQUIRE_PARENT_SURFACES()


def _bound_context(source_law_owner: object) -> Tuple[object, ...]:
    _require_surfaces()
    if type(source_law_owner) is not _CP41_OWNER_TYPE:
        raise TypeError("source_law_owner has the wrong exact CP41 type")
    source_snapshot = _CP41_OWNER_SNAPSHOT(source_law_owner)
    source_certificate = _CP41_CERTIFICATE_PROPERTY.__get__(
        source_law_owner, _CP41_OWNER_TYPE
    )
    live_source = _CP41_LIVE_CERTIFICATE(source_law_owner, source_snapshot)
    _CP41_REQUIRE_OWNER_SNAPSHOT(source_law_owner, source_snapshot)
    if live_source is not source_certificate:
        raise ValueError("CP41 live binding substituted its certificate")
    hypothesis = _CP41_HYPOTHESIS_PROPERTY.__get__(source_law_owner, _CP41_OWNER_TYPE)
    if _CP41_VALIDATE_HYPOTHESIS(hypothesis) is not hypothesis:
        raise ValueError("CP41 hypothesis validation substituted")
    admission_owner = _CP41_PARENT_PROPERTY.__get__(source_law_owner, _CP41_OWNER_TYPE)
    ancestry = _CP41_BOUND_ANCESTRY(admission_owner, require_live=True)
    cp37_owner = ancestry[6]
    cp37_certificate = ancestry[7]
    cp36_owner = ancestry[8]
    cp36_certificate = ancestry[9]
    cp37_snapshot = _CP37_OWNER_SNAPSHOT(cp37_owner)
    if _CP37_LIVE_CERTIFICATE(cp37_owner, cp37_snapshot) is not cp37_certificate:
        raise ValueError("CP37 live binding substituted its certificate")
    _CP37_REQUIRE_OWNER_SNAPSHOT(cp37_owner, cp37_snapshot)
    cp36_snapshot = _CP36_OWNER_SNAPSHOT(cp36_owner)
    if _CP36_LIVE_CERTIFICATE(cp36_owner, cp36_snapshot) is not cp36_certificate:
        raise ValueError("CP36 live binding substituted its certificate")
    _CP36_REQUIRE_OWNER_SNAPSHOT(cp36_owner, cp36_snapshot)
    if source_certificate.checkpoint37_certificate is not cp37_certificate:
        raise ValueError("CP41-to-CP37 certificate identity differs")
    if source_certificate.checkpoint36_certificate is not cp36_certificate:
        raise ValueError("CP41-to-CP36 certificate identity differs")
    if source_certificate.factorization_hypothesis is not hypothesis:
        raise ValueError("CP41 factorization hypothesis identity differs")
    _require_surfaces()
    return (
        source_snapshot,
        source_certificate,
        hypothesis,
        ancestry,
        cp37_owner,
        cp37_snapshot,
        cp37_certificate,
        cp36_owner,
        cp36_snapshot,
        cp36_certificate,
    )


def _runtime_sha256() -> str:
    _require_surfaces()
    return _semantic_digest(
        {
            "schema": _SCHEMA_VERSION,
            "policy": _POLICY,
            "scope": _SCOPE,
            "theorem": _THEOREM,
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "raw_word_domain_size": _D,
            "maximum_attempts": INITIAL_TILT_REJECTION_PREDECISION_MAX_ATTEMPTS,
            "maximum_proposal_words": _MAX_PROPOSAL_WORDS,
            "quota_bytecode_sha256": hashlib.sha256(
                _CP37_QUOTA.__code__.co_code
            ).hexdigest(),
        }
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate:
    """Sealed CP41-bound staged reference-semantics certificate."""

    schema_version: str
    certificate_scope: str
    factorization_policy: str
    factorization_role_sha256: str
    checkpoint41_certificate: _CP41_CERT_TYPE
    checkpoint41_certificate_sha256: str
    checkpoint41_owner_runtime_identity: int
    factorization_hypothesis: _CP41_HYPOTHESIS_TYPE
    factorization_hypothesis_sha256: str
    checkpoint40_certificate: _CP40_CERT_TYPE
    checkpoint39_certificate: _CP39_CERT_TYPE
    checkpoint38_certificate: _CP38_CERT_TYPE
    checkpoint37_certificate: _CP37_CERT_TYPE
    checkpoint36_certificate: _CP36_CERT_TYPE
    checkpoint37_owner_runtime_identity: int
    checkpoint36_owner_runtime_identity: int
    process_parameter_sha256: str
    attempt_budget: int
    proposal_words_per_attempt: int
    proposal_word_count: int
    decision_word_count: int
    raw_word_domain_size: int
    proposal_word_coordinates: Tuple[_COORDINATE_TYPE, ...]
    decision_word_coordinates: Tuple[_COORDINATE_TYPE, ...]
    proposal_coordinate_sha256: str
    decision_coordinate_sha256: str
    factorization_theorem: str
    factorization_runtime_sha256: str
    exact_checkpoint41_owner_binding_certified: bool
    exact_checkpoint41_hypothesis_binding_certified: bool
    checkpoint41_assumption_used_as_proof_premise: bool
    transitive_checkpoint36_37_owner_binding_certified: bool
    exact_proposal_coordinate_order_bound: bool
    exact_v_only_input_domain_certified: bool
    cp42_noninterference_by_input_signature_and_staging: bool
    direct_checkpoint28_30_reference_callbacks_bound: bool
    complete_quota_tuple_before_decision_stage_certified: bool
    failure_passthrough_without_decision_word_access_certified: bool
    operational_exceptions_propagated_not_relabelled: bool
    preparation_failure_branch_executable: bool
    successful_per_instance_projection_parity_witness_supported: bool
    universal_equivalence_to_live_checkpoint36_37_failure_semantics_certified: bool
    checkpoint41_factorization_assumption_discharged: bool
    whole_checkpoint36_37_record_invariance_certified: bool
    live_philox_source_law_certified: bool
    live_source_law_certified: bool
    numeric_fiber_counts_materialized: bool
    numeric_failure_probability_materialized: bool
    live_initializer_distribution_certified: bool
    initializer_admissible: bool
    path_admissible: bool
    full_sampler_admissible: bool
    sampler_liveness_certified: bool
    scientific_claim_promoted: bool
    model_quality_claim_promoted: bool
    generality_claim_promoted: bool
    transitive_callback_closure_integrity_certified: bool
    concurrent_or_aba_external_record_mutation_resilience_certified: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("predecision factorization certificates cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("predecision factorization certificates are sealed")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("predecision factorization certificate is incomplete")
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("predecision factorization certificates are not pickleable")


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionPredecisionRow:
    """One decision-word-free ready row with a complete quota witness."""

    attempt_index: int
    canonical_configuration: _CONFIGURATION_TYPE
    canonical_configuration_sha256: str
    delta_numerator: int
    delta_denominator: int
    threshold_branch: str
    decimal_precision_used: int
    ideal_probability_lower_numerator: int
    ideal_probability_lower_denominator: int
    ideal_probability_upper_numerator: int
    ideal_probability_upper_denominator: int
    ideal_probability_upper_strict: bool
    acceptance_quota: int
    quota_probability_numerator: int
    quota_probability_denominator: int
    ideal_minus_quota_error_strict_upper_numerator: int
    ideal_minus_quota_error_strict_upper_denominator: int
    row_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("predecision rows cannot subclass")

    def __init__(
        self,
        *,
        _construction_token: object,
        _trusted_certificate: Optional[
            CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
        ] = None,
        **values: object,
    ) -> None:
        if _construction_token is not _ROW_TOKEN:
            raise TypeError("predecision rows are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("predecision row is incomplete")
        _validate_row_values(
            values,
            trusted_certificate=_trusted_certificate,
        )
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("predecision rows are not pickleable")


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionPredecisionResult:
    """Sealed tagged predecision record; valid F36 records are refused."""

    certificate: CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    certificate_sha256: str
    run_id: int
    initialization_index: int
    status: str
    proposal_word_count: int
    proposal_words: Tuple[int, ...]
    proposal_words_sha256: str
    attempt_budget: int
    rows: Tuple[CounterKeyedInitialTiltRejectionPredecisionRow, ...]
    row_sha256s: Tuple[str, ...]
    semantic_predecision_sha256: str
    v_only_input_consumed: bool
    reserved_decision_words_present: bool
    all_attempts_scored_before_quota_stage: bool
    all_ready_quotas_complete: bool
    live_failure_equivalence_claimed: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("predecision results cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _PREDECISION_TOKEN:
            raise TypeError("predecision results are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("predecision result is incomplete")
        _validate_predecision_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("predecision results are not pickleable")


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionAppliedDecision:
    """Separate H-stage result over one validated predecision record."""

    certificate: CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    certificate_sha256: str
    predecision_result: CounterKeyedInitialTiltRejectionPredecisionResult
    predecision_result_sha256: str
    status: str
    decision_words: Optional[Tuple[int, ...]]
    decision_words_sha256: Optional[str]
    decision_words_validated_before_first_comparison: bool
    comparison_count: int
    selected_attempt_index: Optional[int]
    selected_configuration: Optional[_CONFIGURATION_TYPE]
    selected_configuration_sha256: Optional[str]
    failure_passed_through_without_decision_word_access: bool
    applied_decision_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("applied decisions cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _APPLIED_TOKEN:
            raise TypeError("applied decisions are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("applied decision is incomplete")
        _validate_applied_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("applied decisions are not pickleable")


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionSuccessfulParityWitness:
    """One successful-path CP42-to-live-CP36/37 projection witness."""

    certificate: CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    certificate_sha256: str
    predecision_result: CounterKeyedInitialTiltRejectionPredecisionResult
    predecision_result_sha256: str
    checkpoint37_result: _CP37_RESULT_TYPE
    checkpoint37_result_sha256: str
    proposal_words_sha256: str
    semantic_predecision_sha256: str
    successful_projection_equal: bool
    universal_equivalence_claimed: bool
    live_failure_equivalence_claimed: bool
    witness_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("successful parity witnesses cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _WITNESS_TOKEN:
            raise TypeError("successful parity witnesses are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("successful parity witness is incomplete")
        _validate_witness_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("successful parity witnesses are not pickleable")


_CERTIFICATE_POSITIVE_FLAGS = (
    "exact_checkpoint41_owner_binding_certified",
    "exact_checkpoint41_hypothesis_binding_certified",
    "transitive_checkpoint36_37_owner_binding_certified",
    "exact_proposal_coordinate_order_bound",
    "exact_v_only_input_domain_certified",
    "cp42_noninterference_by_input_signature_and_staging",
    "direct_checkpoint28_30_reference_callbacks_bound",
    "complete_quota_tuple_before_decision_stage_certified",
    "failure_passthrough_without_decision_word_access_certified",
    "operational_exceptions_propagated_not_relabelled",
    "successful_per_instance_projection_parity_witness_supported",
    "passed",
)
_CERTIFICATE_NEGATIVE_FLAGS = (
    "checkpoint41_assumption_used_as_proof_premise",
    "preparation_failure_branch_executable",
    "universal_equivalence_to_live_checkpoint36_37_failure_semantics_certified",
    "checkpoint41_factorization_assumption_discharged",
    "whole_checkpoint36_37_record_invariance_certified",
    "live_philox_source_law_certified",
    "live_source_law_certified",
    "numeric_fiber_counts_materialized",
    "numeric_failure_probability_materialized",
    "live_initializer_distribution_certified",
    "initializer_admissible",
    "path_admissible",
    "full_sampler_admissible",
    "sampler_liveness_certified",
    "scientific_claim_promoted",
    "model_quality_claim_promoted",
    "generality_claim_promoted",
    "transitive_callback_closure_integrity_certified",
    "concurrent_or_aba_external_record_mutation_resilience_certified",
    "runtime_portable",
    "cryptographic_authentication",
)


def _certificate_fields() -> Tuple[str, ...]:
    certificate_type = (
        CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    )
    return tuple(certificate_type.__annotations__)


def _row_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionPredecisionRow.__annotations__)


def _predecision_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionPredecisionResult.__annotations__)


def _applied_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionAppliedDecision.__annotations__)


def _witness_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionSuccessfulParityWitness.__annotations__
    )


def _signed_integer(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError("%s must be an exact integer" % name)
    if value.bit_length() > 131_072:
        raise ValueError("%s exceeds the exact-integer bound" % name)
    return value


def _proposal_words_sha256(words: Tuple[int, ...]) -> str:
    return _semantic_digest(
        {"domain": "cp42-proposal-words-v1", "proposal_words": words}
    )


def _decision_words_sha256(words: Tuple[int, ...]) -> str:
    return _semantic_digest(
        {"domain": "cp42-decision-words-v1", "decision_words": words}
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "checkpoint41_certificate",
        "factorization_hypothesis",
        "checkpoint40_certificate",
        "checkpoint39_certificate",
        "checkpoint38_certificate",
        "checkpoint37_certificate",
        "checkpoint36_certificate",
        "proposal_word_coordinates",
        "decision_word_coordinates",
        "certificate_sha256",
    )


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    for name, expected in (
        ("schema_version", _SCHEMA_VERSION),
        ("certificate_scope", _SCOPE),
        ("factorization_policy", _POLICY),
        ("factorization_theorem", _THEOREM),
    ):
        _require_text(values[name], expected, name="certificate." + name)
    for name in (
        "factorization_role_sha256",
        "checkpoint41_certificate_sha256",
        "factorization_hypothesis_sha256",
        "process_parameter_sha256",
        "proposal_coordinate_sha256",
        "decision_coordinate_sha256",
        "factorization_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(values[name], name="certificate." + name)
    for name in (
        "checkpoint41_owner_runtime_identity",
        "checkpoint37_owner_runtime_identity",
        "checkpoint36_owner_runtime_identity",
    ):
        _exact_integer(values[name], name="certificate." + name, minimum=1)
    cp41 = values["checkpoint41_certificate"]
    if type(cp41) is not _CP41_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP41 parent type")
    if _CP41_VALIDATE_CERTIFICATE(cp41) is not cp41:
        raise ValueError("CP41 certificate validation substituted")
    hypothesis = values["factorization_hypothesis"]
    if type(hypothesis) is not _CP41_HYPOTHESIS_TYPE:
        raise TypeError("certificate has the wrong exact CP41 hypothesis type")
    if _CP41_VALIDATE_HYPOTHESIS(hypothesis) is not hypothesis:
        raise ValueError("CP41 hypothesis validation substituted")
    if cp41.factorization_hypothesis is not hypothesis:
        raise ValueError("certificate CP41 hypothesis identity differs")
    parents = (
        ("checkpoint40_certificate", _CP40_CERT_TYPE),
        ("checkpoint39_certificate", _CP39_CERT_TYPE),
        ("checkpoint38_certificate", _CP38_CERT_TYPE),
        ("checkpoint37_certificate", _CP37_CERT_TYPE),
        ("checkpoint36_certificate", _CP36_CERT_TYPE),
    )
    for name, expected_type in parents:
        if type(values[name]) is not expected_type:
            raise TypeError("certificate.%s has the wrong exact type" % name)
    cp37 = values["checkpoint37_certificate"]
    cp36 = values["checkpoint36_certificate"]
    if _CP37_VALIDATE_CERTIFICATE(cp37) is not cp37:
        raise ValueError("CP37 certificate validation substituted")
    if _CP36_VALIDATE_CERTIFICATE(cp36) is not cp36:
        raise ValueError("CP36 certificate validation substituted")
    identity_expectations = (
        (values["checkpoint40_certificate"], cp41.checkpoint40_certificate),
        (values["checkpoint39_certificate"], cp41.checkpoint39_certificate),
        (values["checkpoint38_certificate"], cp41.checkpoint38_certificate),
        (cp37, cp41.checkpoint37_certificate),
        (cp36, cp41.checkpoint36_certificate),
    )
    if any(actual is not expected for actual, expected in identity_expectations):
        raise ValueError("certificate transitive parent identity differs")
    if values["checkpoint41_certificate_sha256"] != cp41.certificate_sha256:
        raise ValueError("certificate CP41 digest differs")
    if values["factorization_hypothesis_sha256"] != hypothesis.hypothesis_sha256:
        raise ValueError("certificate CP41 hypothesis digest differs")
    if values["process_parameter_sha256"] != cp41.process_parameter_sha256:
        raise ValueError("certificate process digest differs")
    full, proposal, decision = _CP41_PARTITION_COORDINATES(cp36)
    del full
    checked_proposal = _CP41_VALIDATE_COORDINATE_TUPLE(
        values["proposal_word_coordinates"],
        name="certificate.proposal_word_coordinates",
        expected_length=cp41.proposal_word_count,
    )
    checked_decision = _CP41_VALIDATE_COORDINATE_TUPLE(
        values["decision_word_coordinates"],
        name="certificate.decision_word_coordinates",
        expected_length=cp41.decision_word_count,
    )
    if checked_proposal != proposal:
        raise ValueError("certificate proposal coordinate tuple differs")
    if checked_decision != decision:
        raise ValueError("certificate decision coordinate tuple differs")
    if values["proposal_coordinate_sha256"] != _CP41_COORDINATE_DIGEST(
        checked_proposal
    ):
        raise ValueError("certificate proposal coordinate digest is not exact")
    if values["decision_coordinate_sha256"] != _CP41_COORDINATE_DIGEST(
        checked_decision
    ):
        raise ValueError("certificate decision coordinate digest is not exact")
    if values["proposal_coordinate_sha256"] != cp41.proposal_coordinate_sha256:
        raise ValueError("certificate proposal coordinate digest differs")
    if values["decision_coordinate_sha256"] != cp41.decision_coordinate_sha256:
        raise ValueError("certificate decision coordinate digest differs")
    expected_scalars = {
        "attempt_budget": cp41.attempt_budget,
        "proposal_words_per_attempt": cp41.proposal_words_per_attempt,
        "proposal_word_count": cp41.proposal_word_count,
        "decision_word_count": cp41.decision_word_count,
        "raw_word_domain_size": _D,
    }
    for name, expected in expected_scalars.items():
        actual = _exact_integer(
            values[name],
            name="certificate." + name,
            minimum=1,
            maximum=max(_D, _MAX_PROPOSAL_WORDS),
        )
        if actual != expected:
            raise ValueError("certificate.%s differs" % name)
    if values["factorization_runtime_sha256"] != _runtime_sha256():
        raise ValueError("certificate runtime digest differs")
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="certificate." + name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="certificate." + name)
    if values["certificate_sha256"] != _semantic_digest(_certificate_payload(values)):
        raise ValueError("predecision factorization certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate:
    expected_type = CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    if type(certificate) is not expected_type:
        raise TypeError("certificate has the wrong exact CP42 type")
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _make_certificate_from_context(
    source_law_owner: _CP41_OWNER_TYPE,
    factorization_role_sha256: str,
    context: Tuple[object, ...],
) -> CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate:
    if type(source_law_owner) is not _CP41_OWNER_TYPE:
        raise TypeError("source_law_owner has the wrong exact CP41 type")
    if type(context) is not tuple or len(context) != 10:
        raise TypeError("CP42 bound context is malformed")
    source_snapshot = context[0]
    if type(source_snapshot) is not tuple or len(source_snapshot) != 10:
        raise TypeError("CP42 source-owner snapshot is malformed")
    ancestry = context[3]
    if type(ancestry) is not tuple or len(ancestry) != 12:
        raise TypeError("CP42 bound ancestry is malformed")
    if context[4] is not ancestry[6] or context[7] is not ancestry[8]:
        raise ValueError("CP42 bound context owner identities differ")
    if source_snapshot[8] is not context[1] or source_snapshot[5] is not context[2]:
        raise ValueError("CP42 bound context CP41 identities differ")
    if context[1].checkpoint40_certificate is not ancestry[1]:
        raise ValueError("CP42 bound context CP40 ancestry differs")
    cp41 = context[1]
    hypothesis = context[2]
    cp37_owner = context[4]
    cp36_owner = context[7]
    cp36 = context[9]
    _, proposal, decision = _CP41_PARTITION_COORDINATES(cp36)
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "factorization_policy": _POLICY,
        "factorization_role_sha256": factorization_role_sha256,
        "checkpoint41_certificate": cp41,
        "checkpoint41_certificate_sha256": cp41.certificate_sha256,
        "checkpoint41_owner_runtime_identity": id(source_law_owner),
        "factorization_hypothesis": hypothesis,
        "factorization_hypothesis_sha256": hypothesis.hypothesis_sha256,
        "checkpoint40_certificate": ancestry[1],
        "checkpoint39_certificate": ancestry[3],
        "checkpoint38_certificate": ancestry[5],
        "checkpoint37_certificate": ancestry[7],
        "checkpoint36_certificate": ancestry[9],
        "checkpoint37_owner_runtime_identity": id(cp37_owner),
        "checkpoint36_owner_runtime_identity": id(cp36_owner),
        "process_parameter_sha256": cp41.process_parameter_sha256,
        "attempt_budget": cp41.attempt_budget,
        "proposal_words_per_attempt": cp41.proposal_words_per_attempt,
        "proposal_word_count": cp41.proposal_word_count,
        "decision_word_count": cp41.decision_word_count,
        "raw_word_domain_size": _D,
        "proposal_word_coordinates": proposal,
        "decision_word_coordinates": decision,
        "proposal_coordinate_sha256": cp41.proposal_coordinate_sha256,
        "decision_coordinate_sha256": cp41.decision_coordinate_sha256,
        "factorization_theorem": _THEOREM,
        "factorization_runtime_sha256": _runtime_sha256(),
        **{name: True for name in _CERTIFICATE_POSITIVE_FLAGS},
        **{name: False for name in _CERTIFICATE_NEGATIVE_FLAGS},
        "certificate_sha256": _ZERO_SHA256,
    }
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate(
        _construction_token=_CERTIFICATE_TOKEN,
        **values,
    )


def _make_certificate(
    source_law_owner: _CP41_OWNER_TYPE,
    factorization_role_sha256: str,
) -> CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate:
    context = _bound_context(source_law_owner)
    return _make_certificate_from_context(
        source_law_owner,
        factorization_role_sha256,
        context,
    )


def _row_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "canonical_configuration", "row_sha256")


def _validate_row_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    ] = None,
) -> None:
    attempt_index = _exact_integer(
        values["attempt_index"],
        name="row.attempt_index",
        maximum=INITIAL_TILT_REJECTION_PREDECISION_MAX_ATTEMPTS - 1,
    )
    del attempt_index
    configuration = values["canonical_configuration"]
    if trusted_certificate is None:
        maximum_cardinality = _CP28_MAX_RAW_SLOTS
        maximum_dimension = _CP28_MAX_COORDINATE_DIMENSION
    else:
        manifest = trusted_certificate.checkpoint36_certificate.manifest
        maximum_cardinality = manifest.total_cap
        maximum_dimension = manifest.maximum_coordinate_dimension
    configuration = _CONFIGURATION_PREFLIGHT(
        configuration,
        name="row.canonical_configuration",
        maximum_cardinality=maximum_cardinality,
        maximum_dimension=maximum_dimension,
    )
    configuration_sha256 = _CONFIGURATION_SHA256(configuration)
    _require_sha256(
        values["canonical_configuration_sha256"],
        name="row.canonical_configuration_sha256",
    )
    if values["canonical_configuration_sha256"] != configuration_sha256:
        raise ValueError("row canonical configuration digest differs")
    delta = _CP37_FRACTION_PARTS(
        values["delta_numerator"],
        values["delta_denominator"],
        name="row.delta",
    )
    if delta.denominator & (delta.denominator - 1):
        raise ValueError("row delta must be dyadic")
    if delta > 0:
        raise ValueError("row delta must be nonpositive")
    data = _CP37_QUOTA(delta)
    probability = Fraction(data.quota, _D)
    expected = {
        "threshold_branch": data.branch,
        "decimal_precision_used": data.precision,
        "ideal_probability_lower_numerator": data.ideal_lower.numerator,
        "ideal_probability_lower_denominator": data.ideal_lower.denominator,
        "ideal_probability_upper_numerator": data.ideal_upper.numerator,
        "ideal_probability_upper_denominator": data.ideal_upper.denominator,
        "ideal_probability_upper_strict": data.ideal_upper_strict,
        "acceptance_quota": data.quota,
        "quota_probability_numerator": probability.numerator,
        "quota_probability_denominator": probability.denominator,
        "ideal_minus_quota_error_strict_upper_numerator": 1,
        "ideal_minus_quota_error_strict_upper_denominator": _D,
    }
    for name, expected_value in expected.items():
        actual = values[name]
        if type(actual) is not type(expected_value) or actual != expected_value:
            raise ValueError("row.%s differs" % name)
    _require_sha256(values["row_sha256"], name="row.row_sha256")
    if values["row_sha256"] != _semantic_digest(_row_payload(values)):
        raise ValueError("predecision row digest differs")


def _validate_row(
    row: object,
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    ] = None,
) -> CounterKeyedInitialTiltRejectionPredecisionRow:
    if type(row) is not CounterKeyedInitialTiltRejectionPredecisionRow:
        raise TypeError("row has the wrong exact CP42 type")
    _validate_row_values(
        {name: getattr(row, name) for name in _row_fields()},
        trusted_certificate=trusted_certificate,
    )
    return row


def _make_row(
    attempt_index: int,
    configuration: _CONFIGURATION_TYPE,
    delta: Fraction,
    data: object,
    *,
    trusted_certificate: (
        CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    ),
) -> CounterKeyedInitialTiltRejectionPredecisionRow:
    probability = Fraction(data.quota, _D)
    values: Dict[str, object] = {
        "attempt_index": attempt_index,
        "canonical_configuration": configuration,
        "canonical_configuration_sha256": _CONFIGURATION_SHA256(configuration),
        "delta_numerator": delta.numerator,
        "delta_denominator": delta.denominator,
        "threshold_branch": data.branch,
        "decimal_precision_used": data.precision,
        "ideal_probability_lower_numerator": data.ideal_lower.numerator,
        "ideal_probability_lower_denominator": data.ideal_lower.denominator,
        "ideal_probability_upper_numerator": data.ideal_upper.numerator,
        "ideal_probability_upper_denominator": data.ideal_upper.denominator,
        "ideal_probability_upper_strict": data.ideal_upper_strict,
        "acceptance_quota": data.quota,
        "quota_probability_numerator": probability.numerator,
        "quota_probability_denominator": probability.denominator,
        "ideal_minus_quota_error_strict_upper_numerator": 1,
        "ideal_minus_quota_error_strict_upper_denominator": _D,
        "row_sha256": _ZERO_SHA256,
    }
    values["row_sha256"] = _semantic_digest(_row_payload(values))
    return CounterKeyedInitialTiltRejectionPredecisionRow(
        _construction_token=_ROW_TOKEN,
        _trusted_certificate=trusted_certificate,
        **values,
    )


def _semantic_predecision_sha256(
    status: str,
    rows: Tuple[CounterKeyedInitialTiltRejectionPredecisionRow, ...],
) -> str:
    if status == "ready":
        projection = tuple(
            {
                "attempt_index": row.attempt_index,
                "canonical_configuration_sha256": (row.canonical_configuration_sha256),
                "delta_numerator": row.delta_numerator,
                "delta_denominator": row.delta_denominator,
                "acceptance_quota": row.acceptance_quota,
            }
            for row in rows
        )
    else:
        projection = ()
    return _semantic_digest(
        {"domain": "cp42-semantic-predecision-v1", "status": status, "rows": projection}
    )


def _predecision_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "certificate", "rows", "result_sha256")


def _validate_predecision_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    ] = None,
) -> None:
    certificate = values["certificate"]
    if trusted_certificate is None:
        checked_certificate = _validate_certificate(certificate)
    else:
        if certificate is not trusted_certificate:
            raise ValueError("predecision certificate identity differs")
        checked_certificate = trusted_certificate
    _require_sha256(
        values["certificate_sha256"],
        name="predecision.certificate_sha256",
    )
    if values["certificate_sha256"] != checked_certificate.certificate_sha256:
        raise ValueError("predecision certificate digest differs")
    _exact_integer(values["run_id"], name="predecision.run_id")
    _exact_integer(
        values["initialization_index"],
        name="predecision.initialization_index",
    )
    if type(values["status"]) is not str:
        raise TypeError("predecision status must be exact text")
    status = values["status"]
    if status not in INITIAL_TILT_REJECTION_PREDECISION_STATUSES:
        raise ValueError("predecision status is unknown")
    if status == "preparation_failure":
        raise ValueError("reserved preparation_failure records are not executable")
    proposal_count = _exact_integer(
        values["proposal_word_count"],
        name="predecision.proposal_word_count",
        maximum=_MAX_PROPOSAL_WORDS,
    )
    if proposal_count != checked_certificate.proposal_word_count:
        raise ValueError("predecision proposal word count differs")
    words = _exact_words(
        values["proposal_words"],
        name="predecision.proposal_words",
        length=proposal_count,
    )
    if values["proposal_words"] is not words:
        raise ValueError("predecision proposal words are not canonical")
    _require_sha256(
        values["proposal_words_sha256"],
        name="predecision.proposal_words_sha256",
    )
    if values["proposal_words_sha256"] != _proposal_words_sha256(words):
        raise ValueError("predecision proposal word digest differs")
    attempt_budget = _exact_integer(
        values["attempt_budget"],
        name="predecision.attempt_budget",
        minimum=1,
        maximum=INITIAL_TILT_REJECTION_PREDECISION_MAX_ATTEMPTS,
    )
    if attempt_budget != checked_certificate.attempt_budget:
        raise ValueError("predecision attempt budget differs")
    rows = values["rows"]
    if type(rows) is not tuple or len(rows) > checked_certificate.attempt_budget:
        raise ValueError("predecision rows have the wrong bounded shape")
    row_sha256s = values["row_sha256s"]
    if type(row_sha256s) is not tuple or len(row_sha256s) != len(rows):
        raise ValueError("predecision row digest tuple differs")
    for position, row_sha256 in enumerate(row_sha256s):
        _require_sha256(
            row_sha256,
            name="predecision.row_sha256s[%d]" % position,
        )
    for position, row in enumerate(rows):
        _validate_row(row, trusted_certificate=checked_certificate)
        if row.attempt_index != position:
            raise ValueError("predecision row chronology differs")
    if row_sha256s != tuple(row.row_sha256 for row in rows):
        raise ValueError("predecision row digests differ")
    if status == "ready" and len(rows) != checked_certificate.attempt_budget:
        raise ValueError("ready predecision does not contain every quota")
    if status == "quota_certification_failure" and rows:
        raise ValueError("quota failure must discard partial rows")
    flag_expectations = {
        "v_only_input_consumed": True,
        "reserved_decision_words_present": False,
        "all_attempts_scored_before_quota_stage": True,
        "all_ready_quotas_complete": status == "ready",
        "live_failure_equivalence_claimed": False,
    }
    for name, expected in flag_expectations.items():
        _exact_bool(values[name], expected, name="predecision." + name)
    semantic_sha256 = _semantic_predecision_sha256(status, rows)
    _require_sha256(
        values["semantic_predecision_sha256"],
        name="predecision.semantic_predecision_sha256",
    )
    if values["semantic_predecision_sha256"] != semantic_sha256:
        raise ValueError("predecision semantic digest differs")
    _require_sha256(values["result_sha256"], name="predecision.result_sha256")
    if values["result_sha256"] != _semantic_digest(_predecision_payload(values)):
        raise ValueError("predecision result digest differs")


def _validate_predecision_record(
    result: object,
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    ] = None,
) -> CounterKeyedInitialTiltRejectionPredecisionResult:
    if type(result) is not CounterKeyedInitialTiltRejectionPredecisionResult:
        raise TypeError("result has the wrong exact CP42 predecision type")
    _validate_predecision_values(
        {name: getattr(result, name) for name in _predecision_fields()},
        trusted_certificate=trusted_certificate,
    )
    return result


def _make_predecision_result(
    certificate: CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate,
    run_id: int,
    initialization_index: int,
    proposal_words: Tuple[int, ...],
    status: str,
    rows: Tuple[CounterKeyedInitialTiltRejectionPredecisionRow, ...],
) -> CounterKeyedInitialTiltRejectionPredecisionResult:
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "run_id": run_id,
        "initialization_index": initialization_index,
        "status": status,
        "proposal_word_count": len(proposal_words),
        "proposal_words": proposal_words,
        "proposal_words_sha256": _proposal_words_sha256(proposal_words),
        "attempt_budget": certificate.attempt_budget,
        "rows": rows,
        "row_sha256s": tuple(row.row_sha256 for row in rows),
        "semantic_predecision_sha256": _semantic_predecision_sha256(status, rows),
        "v_only_input_consumed": True,
        "reserved_decision_words_present": False,
        "all_attempts_scored_before_quota_stage": True,
        "all_ready_quotas_complete": status == "ready",
        "live_failure_equivalence_claimed": False,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _semantic_digest(_predecision_payload(values))
    return CounterKeyedInitialTiltRejectionPredecisionResult(
        _construction_token=_PREDECISION_TOKEN,
        **values,
    )


def _configuration_keys(configuration: _CONFIGURATION_TYPE) -> Tuple[object, ...]:
    if type(configuration) is not tuple:
        raise TypeError("configuration must be an exact tuple")
    _CONFIGURATION_SHA256(configuration)
    return tuple(_EVENT_MODEL_KEY(event) for event in configuration)


def _same_configuration(
    left: object,
    right: object,
    *,
    maximum_cardinality: int = _CP28_MAX_RAW_SLOTS,
    maximum_dimension: int = _CP28_MAX_COORDINATE_DIMENSION,
) -> bool:
    if type(left) is not tuple or type(right) is not tuple:
        return False
    left = _CONFIGURATION_PREFLIGHT(
        left,
        name="left configuration",
        maximum_cardinality=maximum_cardinality,
        maximum_dimension=maximum_dimension,
    )
    right = _CONFIGURATION_PREFLIGHT(
        right,
        name="right configuration",
        maximum_cardinality=maximum_cardinality,
        maximum_dimension=maximum_dimension,
    )
    if _CONFIGURATION_SHA256(left) != _CONFIGURATION_SHA256(right):
        return False
    return _configuration_keys(left) == _configuration_keys(right)


def _applied_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "predecision_result",
        "selected_configuration",
        "applied_decision_sha256",
    )


def _validate_applied_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    ] = None,
) -> None:
    certificate = values["certificate"]
    if trusted_certificate is None:
        checked_certificate = _validate_certificate(certificate)
    else:
        if certificate is not trusted_certificate:
            raise ValueError("applied decision certificate identity differs")
        checked_certificate = trusted_certificate
    _require_sha256(
        values["certificate_sha256"],
        name="applied_decision.certificate_sha256",
    )
    if values["certificate_sha256"] != checked_certificate.certificate_sha256:
        raise ValueError("applied decision certificate digest differs")
    parent = _validate_predecision_record(
        values["predecision_result"],
        trusted_certificate=checked_certificate,
    )
    _require_sha256(
        values["predecision_result_sha256"],
        name="applied_decision.predecision_result_sha256",
    )
    if values["predecision_result_sha256"] != parent.result_sha256:
        raise ValueError("applied decision parent digest differs")
    status = values["status"]
    if type(status) is not str or (
        status not in INITIAL_TILT_REJECTION_APPLIED_DECISION_STATUSES
    ):
        raise ValueError("applied decision status is unknown")
    if parent.status == "quota_certification_failure":
        if status != parent.status:
            raise ValueError("modeled failure was not passed through")
        if values["decision_words"] is not None:
            raise ValueError("failure pass-through retained decision words")
        if values["decision_words_sha256"] is not None:
            raise ValueError("failure pass-through retained a decision digest")
        _exact_bool(
            values["decision_words_validated_before_first_comparison"],
            False,
            name="applied_decision.words_validated_before_comparison",
        )
        comparison_count = _exact_integer(
            values["comparison_count"],
            name="applied_decision.comparison_count",
            maximum=checked_certificate.attempt_budget,
        )
        if comparison_count != 0:
            raise ValueError("failure pass-through comparison count differs")
        for name in (
            "selected_attempt_index",
            "selected_configuration",
            "selected_configuration_sha256",
        ):
            if values[name] is not None:
                raise ValueError("failure pass-through field %s differs" % name)
        _exact_bool(
            values["failure_passed_through_without_decision_word_access"],
            True,
            name="applied_decision.failure_passed_through",
        )
    else:
        if parent.status != "ready":
            raise ValueError("applied decision parent status is not executable")
        if status not in ("selected", "exhausted"):
            raise ValueError("ready predecision did not produce an outcome")
        words = _exact_words(
            values["decision_words"],
            name="applied_decision.decision_words",
            length=checked_certificate.decision_word_count,
        )
        if values["decision_words"] is not words:
            raise ValueError("applied decision words are not canonical")
        _require_sha256(
            values["decision_words_sha256"],
            name="applied_decision.decision_words_sha256",
        )
        if values["decision_words_sha256"] != _decision_words_sha256(words):
            raise ValueError("applied decision word digest differs")
        _exact_bool(
            values["decision_words_validated_before_first_comparison"],
            True,
            name="applied_decision.words_validated_before_comparison",
        )
        _exact_bool(
            values["failure_passed_through_without_decision_word_access"],
            False,
            name="applied_decision.failure_passed_through",
        )
        selected_index = None
        for position, (row, word) in enumerate(zip(parent.rows, words)):
            if word < row.acceptance_quota:
                selected_index = position
                break
        expected_count = (
            len(parent.rows) if selected_index is None else selected_index + 1
        )
        comparison_count = _exact_integer(
            values["comparison_count"],
            name="applied_decision.comparison_count",
            minimum=1,
            maximum=checked_certificate.attempt_budget,
        )
        if comparison_count != expected_count:
            raise ValueError("applied decision comparison count differs")
        if selected_index is None:
            if status != "exhausted":
                raise ValueError("applied decision exhaustion status differs")
            if any(
                values[name] is not None
                for name in (
                    "selected_attempt_index",
                    "selected_configuration",
                    "selected_configuration_sha256",
                )
            ):
                raise ValueError("exhausted decision retained a selection")
        else:
            row = parent.rows[selected_index]
            if status != "selected":
                raise ValueError("applied decision selection status differs")
            checked_selected_index = _exact_integer(
                values["selected_attempt_index"],
                name="applied_decision.selected_attempt_index",
                maximum=checked_certificate.attempt_budget - 1,
            )
            if checked_selected_index != selected_index:
                raise ValueError("applied decision selected index differs")
            manifest = checked_certificate.checkpoint36_certificate.manifest
            if not _same_configuration(
                values["selected_configuration"],
                row.canonical_configuration,
                maximum_cardinality=manifest.total_cap,
                maximum_dimension=manifest.maximum_coordinate_dimension,
            ):
                raise ValueError("applied decision selected configuration differs")
            _require_sha256(
                values["selected_configuration_sha256"],
                name="applied_decision.selected_configuration_sha256",
            )
            if (
                values["selected_configuration_sha256"]
                != row.canonical_configuration_sha256
            ):
                raise ValueError("applied decision selected digest differs")
    _require_sha256(
        values["applied_decision_sha256"],
        name="applied_decision.applied_decision_sha256",
    )
    if values["applied_decision_sha256"] != _semantic_digest(_applied_payload(values)):
        raise ValueError("applied decision digest differs")


def _validate_applied_record(
    result: object,
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    ] = None,
) -> CounterKeyedInitialTiltRejectionAppliedDecision:
    if type(result) is not CounterKeyedInitialTiltRejectionAppliedDecision:
        raise TypeError("result has the wrong exact CP42 applied-decision type")
    _validate_applied_values(
        {name: getattr(result, name) for name in _applied_fields()},
        trusted_certificate=trusted_certificate,
    )
    return result


def _make_applied_decision(
    certificate: CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate,
    parent: CounterKeyedInitialTiltRejectionPredecisionResult,
    decision_words: object,
) -> CounterKeyedInitialTiltRejectionAppliedDecision:
    if parent.status == "quota_certification_failure":
        values: Dict[str, object] = {
            "certificate": certificate,
            "certificate_sha256": certificate.certificate_sha256,
            "predecision_result": parent,
            "predecision_result_sha256": parent.result_sha256,
            "status": parent.status,
            "decision_words": None,
            "decision_words_sha256": None,
            "decision_words_validated_before_first_comparison": False,
            "comparison_count": 0,
            "selected_attempt_index": None,
            "selected_configuration": None,
            "selected_configuration_sha256": None,
            "failure_passed_through_without_decision_word_access": True,
            "applied_decision_sha256": _ZERO_SHA256,
        }
    else:
        words = _exact_words(
            decision_words,
            name="decision_words",
            length=certificate.decision_word_count,
        )
        selected_index = None
        for position, (row, word) in enumerate(zip(parent.rows, words)):
            if word < row.acceptance_quota:
                selected_index = position
                break
        selected_row = None if selected_index is None else parent.rows[selected_index]
        values = {
            "certificate": certificate,
            "certificate_sha256": certificate.certificate_sha256,
            "predecision_result": parent,
            "predecision_result_sha256": parent.result_sha256,
            "status": "exhausted" if selected_row is None else "selected",
            "decision_words": words,
            "decision_words_sha256": _decision_words_sha256(words),
            "decision_words_validated_before_first_comparison": True,
            "comparison_count": (
                len(parent.rows) if selected_index is None else selected_index + 1
            ),
            "selected_attempt_index": selected_index,
            "selected_configuration": (
                None if selected_row is None else selected_row.canonical_configuration
            ),
            "selected_configuration_sha256": (
                None
                if selected_row is None
                else selected_row.canonical_configuration_sha256
            ),
            "failure_passed_through_without_decision_word_access": False,
            "applied_decision_sha256": _ZERO_SHA256,
        }
    values["applied_decision_sha256"] = _semantic_digest(_applied_payload(values))
    return CounterKeyedInitialTiltRejectionAppliedDecision(
        _construction_token=_APPLIED_TOKEN,
        **values,
    )


def _witness_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "predecision_result",
        "checkpoint37_result",
        "witness_sha256",
    )


def _validate_witness_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    ] = None,
) -> None:
    certificate = values["certificate"]
    if trusted_certificate is None:
        checked_certificate = _validate_certificate(certificate)
    else:
        if certificate is not trusted_certificate:
            raise ValueError("parity witness certificate identity differs")
        checked_certificate = trusted_certificate
    _require_sha256(
        values["certificate_sha256"],
        name="parity_witness.certificate_sha256",
    )
    if values["certificate_sha256"] != checked_certificate.certificate_sha256:
        raise ValueError("parity witness certificate digest differs")
    predecision = _validate_predecision_record(
        values["predecision_result"],
        trusted_certificate=checked_certificate,
    )
    if predecision.status != "ready":
        raise ValueError("parity witness requires a ready predecision")
    _require_sha256(
        values["predecision_result_sha256"],
        name="parity_witness.predecision_result_sha256",
    )
    if values["predecision_result_sha256"] != predecision.result_sha256:
        raise ValueError("parity witness predecision digest differs")
    live = values["checkpoint37_result"]
    if type(live) is not _CP37_RESULT_TYPE:
        raise TypeError("parity witness has the wrong exact CP37 result type")
    _require_sha256(
        live.result_sha256,
        name="parity_witness.checkpoint37_result.result_sha256",
    )
    _require_sha256(
        values["checkpoint37_result_sha256"],
        name="parity_witness.checkpoint37_result_sha256",
    )
    if values["checkpoint37_result_sha256"] != live.result_sha256:
        raise ValueError("parity witness CP37 result digest differs")
    _require_sha256(
        values["proposal_words_sha256"],
        name="parity_witness.proposal_words_sha256",
    )
    if values["proposal_words_sha256"] != predecision.proposal_words_sha256:
        raise ValueError("parity witness proposal word digest differs")
    _require_sha256(
        values["semantic_predecision_sha256"],
        name="parity_witness.semantic_predecision_sha256",
    )
    if values["semantic_predecision_sha256"] != (
        predecision.semantic_predecision_sha256
    ):
        raise ValueError("parity witness semantic digest differs")
    _exact_bool(
        values["successful_projection_equal"],
        True,
        name="parity_witness.successful_projection_equal",
    )
    _exact_bool(
        values["universal_equivalence_claimed"],
        False,
        name="parity_witness.universal_equivalence_claimed",
    )
    _exact_bool(
        values["live_failure_equivalence_claimed"],
        False,
        name="parity_witness.live_failure_equivalence_claimed",
    )
    _require_sha256(values["witness_sha256"], name="parity_witness.witness_sha256")
    if values["witness_sha256"] != _semantic_digest(_witness_payload(values)):
        raise ValueError("successful parity witness digest differs")


def _validate_witness_record(
    witness: object,
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
    ] = None,
) -> CounterKeyedInitialTiltRejectionSuccessfulParityWitness:
    if type(witness) is not CounterKeyedInitialTiltRejectionSuccessfulParityWitness:
        raise TypeError("witness has the wrong exact CP42 parity type")
    _validate_witness_values(
        {name: getattr(witness, name) for name in _witness_fields()},
        trusted_certificate=trusted_certificate,
    )
    return witness


_MAX_OPERATION_RECORD_GRAPH_SIZE = 256


def _persistent_record_fields(record: object) -> Tuple[str, ...]:
    record_type = type(record)
    if not record_type.__module__.startswith("heterodiff."):
        return ()
    annotations = record_type.__dict__.get("__annotations__")
    if type(annotations) is not type(_LOCAL_NAMESPACE):
        return ()
    fields = tuple(annotations)
    if len(fields) > _MAX_OPERATION_RECORD_GRAPH_SIZE:
        raise ValueError("CP42 persistent record has too many fields")
    return fields


def _operation_record_graph_snapshot(
    roots: Tuple[object, ...],
) -> Tuple[Tuple[object, ...], ...]:
    if type(roots) is not tuple or len(roots) > 16:
        raise TypeError("CP42 persistent record roots are malformed")
    pending = list(roots)
    seen = set()
    snapshot = []
    while pending:
        record = pending.pop()
        fields = _persistent_record_fields(record)
        if not fields:
            continue
        identity = id(record)
        if identity in seen:
            continue
        seen.add(identity)
        if len(snapshot) >= _MAX_OPERATION_RECORD_GRAPH_SIZE:
            raise ValueError("CP42 persistent record graph is too large")
        before = tuple(getattr(record, name) for name in fields)
        snapshot.append((type(record), record, fields, before))
        for child in before:
            if _persistent_record_fields(child):
                pending.append(child)
    return tuple(snapshot)


def _require_operation_record_graph_unchanged(
    snapshot: Tuple[Tuple[object, ...], ...],
) -> None:
    if type(snapshot) is not tuple or len(snapshot) > _MAX_OPERATION_RECORD_GRAPH_SIZE:
        raise TypeError("CP42 persistent record graph snapshot is malformed")
    for position, item in enumerate(snapshot):
        if type(item) is not tuple or len(item) != 4:
            raise TypeError("CP42 persistent record graph snapshot is malformed")
        record_type, record, fields, before = item
        if type(record_type) is not type or type(record) is not record_type:
            raise TypeError("CP42 persistent record graph type changed")
        if (
            type(fields) is not tuple
            or type(before) is not tuple
            or len(fields) != len(before)
        ):
            raise TypeError("CP42 persistent record snapshot is malformed")
        for name, expected in zip(fields, before):
            current = getattr(record, name)
            if current is expected:
                continue
            if type(expected) in (str, int, bool, float) and (
                type(current) is type(expected) and current == expected
            ):
                continue
            raise _CP42_ERROR(
                "CP42 persistent record %d field %s changed during operation"
                % (position, name)
            )


class CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner:
    """Immutable owner of one CP41-bound staged reference evaluator."""

    __slots__ = (
        "_source_law_owner",
        "_source_law_owner_identity",
        "_decision_owner",
        "_decision_owner_identity",
        "_preparation_owner",
        "_preparation_owner_identity",
        "_factorization_policy",
        "_factorization_policy_identity",
        "_factorization_role_sha256",
        "_factorization_role_sha256_identity",
        "_certificate",
        "_certificate_identity",
        "_source_owner_snapshot",
        "_source_require_owner_snapshot",
        "_source_live_certificate",
        "_ancestry_resolver",
        "_coordinate_partitioner",
        "_admission_owner_snapshot",
        "_admission_require_owner_snapshot",
        "_coordination_owner_snapshot",
        "_coordination_require_owner_snapshot",
        "_finite_batch_owner_snapshot",
        "_finite_batch_require_owner_snapshot",
        "_decision_owner_snapshot",
        "_decision_require_owner_snapshot",
        "_decision_live_certificate",
        "_decision_validate_result",
        "_preparation_owner_snapshot",
        "_preparation_require_owner_snapshot",
        "_preparation_live_certificate",
        "_preparation_require_dependency_return",
        "_slot_materializer",
        "_materialized_preflight",
        "_materialized_snapshot",
        "_materialized_unchanged",
        "_quota_position",
        "_slot_maker",
        "_slot_preflight",
        "_slot_validator",
        "_slot_snapshot",
        "_slot_unchanged",
        "_event_model_key",
        "_configuration_sha256",
        "_configuration_preflight",
        "_tilt_evaluate",
        "_tilt_preflight",
        "_score_snapshot",
        "_score_unchanged",
        "_tilt_validate",
        "_fraction_parts",
        "_quota_builder",
        "_quota_error",
        "_row_builder",
        "_certificate_validator",
        "_certificate_builder",
        "_context_certificate_builder",
        "_predecision_validator",
        "_predecision_builder",
        "_applied_validator",
        "_applied_builder",
        "_witness_validator",
        "_surface_guard",
        "_surface_guard_identity",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("predecision factorization owners cannot subclass")

    def __init__(
        self,
        source_law_owner: _CP41_OWNER_TYPE,
        decision_owner: _CP37_OWNER_TYPE,
        preparation_owner: _CP36_OWNER_TYPE,
        factorization_policy: str,
        factorization_role_sha256: str,
        certificate: (
            CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate
        ),
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("predecision factorization owners require certification")
        if type(source_law_owner) is not _CP41_OWNER_TYPE:
            raise TypeError("source_law_owner has the wrong exact CP41 type")
        if type(decision_owner) is not _CP37_OWNER_TYPE:
            raise TypeError("decision_owner has the wrong exact CP37 type")
        if type(preparation_owner) is not _CP36_OWNER_TYPE:
            raise TypeError("preparation_owner has the wrong exact CP36 type")
        policy = _require_text(
            factorization_policy,
            _POLICY,
            name="factorization_policy",
        )
        role = _require_sha256(
            factorization_role_sha256,
            name="factorization_role_sha256",
        )
        checked_certificate = _validate_certificate(certificate)
        context = _bound_context(source_law_owner)
        if context[4] is not decision_owner or context[7] is not preparation_owner:
            raise ValueError("owner transitive CP36/37 identity differs")
        if checked_certificate.checkpoint41_certificate is not context[1]:
            raise ValueError("owner CP41 certificate identity differs")
        if checked_certificate.factorization_role_sha256 != role:
            raise ValueError("owner factorization role differs")
        bindings = (
            ("_source_law_owner", source_law_owner),
            ("_source_law_owner_identity", source_law_owner),
            ("_decision_owner", decision_owner),
            ("_decision_owner_identity", decision_owner),
            ("_preparation_owner", preparation_owner),
            ("_preparation_owner_identity", preparation_owner),
            ("_factorization_policy", policy),
            ("_factorization_policy_identity", policy),
            ("_factorization_role_sha256", role),
            ("_factorization_role_sha256_identity", role),
            ("_certificate", checked_certificate),
            ("_certificate_identity", checked_certificate),
            ("_source_owner_snapshot", _CP41_OWNER_SNAPSHOT),
            ("_source_require_owner_snapshot", _CP41_REQUIRE_OWNER_SNAPSHOT),
            ("_source_live_certificate", _CP41_LIVE_CERTIFICATE),
            ("_ancestry_resolver", _CP41_BOUND_ANCESTRY),
            ("_coordinate_partitioner", _CP41_PARTITION_COORDINATES),
            ("_admission_owner_snapshot", _CP40_OWNER_SNAPSHOT),
            ("_admission_require_owner_snapshot", _CP40_REQUIRE_OWNER_SNAPSHOT),
            ("_coordination_owner_snapshot", _CP39_OWNER_SNAPSHOT),
            (
                "_coordination_require_owner_snapshot",
                _CP39_REQUIRE_OWNER_SNAPSHOT,
            ),
            ("_finite_batch_owner_snapshot", _CP38_OWNER_SNAPSHOT),
            (
                "_finite_batch_require_owner_snapshot",
                _CP38_REQUIRE_OWNER_SNAPSHOT,
            ),
            ("_decision_owner_snapshot", _CP37_OWNER_SNAPSHOT),
            ("_decision_require_owner_snapshot", _CP37_REQUIRE_OWNER_SNAPSHOT),
            ("_decision_live_certificate", _CP37_LIVE_CERTIFICATE),
            ("_decision_validate_result", _CP37_VALIDATE_RESULT),
            ("_preparation_owner_snapshot", _CP36_OWNER_SNAPSHOT),
            ("_preparation_require_owner_snapshot", _CP36_REQUIRE_OWNER_SNAPSHOT),
            ("_preparation_live_certificate", _CP36_LIVE_CERTIFICATE),
            (
                "_preparation_require_dependency_return",
                _CP36_REQUIRE_DEPENDENCY_RETURN,
            ),
            ("_slot_materializer", _SLOT_MATERIALIZER),
            ("_materialized_preflight", _MATERIALIZED_PREFLIGHT),
            ("_materialized_snapshot", _MATERIALIZED_SNAPSHOT),
            ("_materialized_unchanged", _MATERIALIZED_UNCHANGED),
            ("_quota_position", _QUOTA_POSITION),
            ("_slot_maker", _SLOT_MAKER),
            ("_slot_preflight", _SLOT_PREFLIGHT),
            ("_slot_validator", _SLOT_VALIDATOR),
            ("_slot_snapshot", _SLOT_SNAPSHOT),
            ("_slot_unchanged", _SLOT_UNCHANGED),
            ("_event_model_key", _EVENT_MODEL_KEY),
            ("_configuration_sha256", _CONFIGURATION_SHA256),
            ("_configuration_preflight", _CONFIGURATION_PREFLIGHT),
            ("_tilt_evaluate", _TILT_EVALUATE),
            ("_tilt_preflight", _TILT_PREFLIGHT),
            ("_score_snapshot", _SCORE_SNAPSHOT),
            ("_score_unchanged", _SCORE_UNCHANGED),
            ("_tilt_validate", _TILT_VALIDATE),
            ("_fraction_parts", _CP37_FRACTION_PARTS),
            ("_quota_builder", _CP37_QUOTA),
            ("_quota_error", _CP37_QUOTA_ERROR),
            ("_row_builder", _make_row),
            ("_certificate_validator", _validate_certificate),
            ("_certificate_builder", _make_certificate),
            ("_context_certificate_builder", _make_certificate_from_context),
            ("_predecision_validator", _validate_predecision_record),
            ("_predecision_builder", _make_predecision_result),
            ("_applied_validator", _validate_applied_record),
            ("_applied_builder", _make_applied_decision),
            ("_witness_validator", _validate_witness_record),
            ("_surface_guard", _require_surfaces),
            ("_surface_guard_identity", _require_surfaces),
            ("_sealed", True),
        )
        for name, value in bindings:
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("predecision factorization owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("predecision factorization owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("predecision factorization owners are not pickleable")

    @property
    def certificate(
        self,
        _local_guard: object = _require_unshadowed_local_runtime,
    ) -> CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate:
        _local_guard()
        return self._certificate

    @property
    def source_law_owner(
        self,
        _local_guard: object = _require_unshadowed_local_runtime,
    ) -> _CP41_OWNER_TYPE:
        _local_guard()
        return self._source_law_owner

    def _identity_state(
        self,
        _local_guard: object = _require_unshadowed_local_runtime,
        _error_type: object = _LOCAL_NAMESPACE_ERROR,
    ) -> Tuple[object, ...]:
        _local_guard()
        if self._surface_guard is not self._surface_guard_identity:
            raise _error_type("predecision factorization surface guard changed")
        self._surface_guard()
        if self._surface_guard is not _require_surfaces:
            raise ValueError("predecision factorization surface guard changed")
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("predecision factorization owner seal differs")
        current = (
            self._source_law_owner,
            self._decision_owner,
            self._preparation_owner,
            self._factorization_policy,
            self._factorization_role_sha256,
            self._certificate,
        )
        frozen = (
            self._source_law_owner_identity,
            self._decision_owner_identity,
            self._preparation_owner_identity,
            self._factorization_policy_identity,
            self._factorization_role_sha256_identity,
            self._certificate_identity,
        )
        if any(live is not expected for live, expected in zip(current, frozen)):
            raise ValueError("predecision factorization owner identity changed")
        callbacks = (
            (self._source_owner_snapshot, _CP41_OWNER_SNAPSHOT),
            (self._source_require_owner_snapshot, _CP41_REQUIRE_OWNER_SNAPSHOT),
            (self._source_live_certificate, _CP41_LIVE_CERTIFICATE),
            (self._ancestry_resolver, _CP41_BOUND_ANCESTRY),
            (self._coordinate_partitioner, _CP41_PARTITION_COORDINATES),
            (self._admission_owner_snapshot, _CP40_OWNER_SNAPSHOT),
            (
                self._admission_require_owner_snapshot,
                _CP40_REQUIRE_OWNER_SNAPSHOT,
            ),
            (self._coordination_owner_snapshot, _CP39_OWNER_SNAPSHOT),
            (
                self._coordination_require_owner_snapshot,
                _CP39_REQUIRE_OWNER_SNAPSHOT,
            ),
            (self._finite_batch_owner_snapshot, _CP38_OWNER_SNAPSHOT),
            (
                self._finite_batch_require_owner_snapshot,
                _CP38_REQUIRE_OWNER_SNAPSHOT,
            ),
            (self._decision_owner_snapshot, _CP37_OWNER_SNAPSHOT),
            (self._decision_require_owner_snapshot, _CP37_REQUIRE_OWNER_SNAPSHOT),
            (self._decision_live_certificate, _CP37_LIVE_CERTIFICATE),
            (self._decision_validate_result, _CP37_VALIDATE_RESULT),
            (self._preparation_owner_snapshot, _CP36_OWNER_SNAPSHOT),
            (self._preparation_require_owner_snapshot, _CP36_REQUIRE_OWNER_SNAPSHOT),
            (self._preparation_live_certificate, _CP36_LIVE_CERTIFICATE),
            (
                self._preparation_require_dependency_return,
                _CP36_REQUIRE_DEPENDENCY_RETURN,
            ),
            (self._slot_materializer, _SLOT_MATERIALIZER),
            (self._materialized_preflight, _MATERIALIZED_PREFLIGHT),
            (self._materialized_snapshot, _MATERIALIZED_SNAPSHOT),
            (self._materialized_unchanged, _MATERIALIZED_UNCHANGED),
            (self._quota_position, _QUOTA_POSITION),
            (self._slot_maker, _SLOT_MAKER),
            (self._slot_preflight, _SLOT_PREFLIGHT),
            (self._slot_validator, _SLOT_VALIDATOR),
            (self._slot_snapshot, _SLOT_SNAPSHOT),
            (self._slot_unchanged, _SLOT_UNCHANGED),
            (self._event_model_key, _EVENT_MODEL_KEY),
            (self._configuration_sha256, _CONFIGURATION_SHA256),
            (self._configuration_preflight, _CONFIGURATION_PREFLIGHT),
            (self._tilt_evaluate, _TILT_EVALUATE),
            (self._tilt_preflight, _TILT_PREFLIGHT),
            (self._score_snapshot, _SCORE_SNAPSHOT),
            (self._score_unchanged, _SCORE_UNCHANGED),
            (self._tilt_validate, _TILT_VALIDATE),
            (self._fraction_parts, _CP37_FRACTION_PARTS),
            (self._quota_builder, _CP37_QUOTA),
            (self._quota_error, _CP37_QUOTA_ERROR),
            (self._row_builder, _make_row),
            (self._certificate_validator, _validate_certificate),
            (self._certificate_builder, _make_certificate),
            (self._context_certificate_builder, _make_certificate_from_context),
            (self._predecision_validator, _validate_predecision_record),
            (self._predecision_builder, _make_predecision_result),
            (self._applied_validator, _validate_applied_record),
            (self._applied_builder, _make_applied_decision),
            (self._witness_validator, _validate_witness_record),
            (self._surface_guard, _require_surfaces),
        )
        if any(live is not expected for live, expected in callbacks):
            raise ValueError("predecision factorization cached callback changed")
        return current

    def _owner_snapshot(self) -> Tuple[object, ...]:
        return self._identity_state()

    def _require_owner_snapshot(self, snapshot: Tuple[object, ...]) -> None:
        if type(snapshot) is not tuple or len(snapshot) != 6:
            raise TypeError("predecision factorization owner snapshot is malformed")
        current = self._identity_state()
        if any(live is not expected for live, expected in zip(current, snapshot)):
            raise _CP42_ERROR(
                "predecision factorization owner changed during operation"
            )

    def _live_certificate(
        self,
        owner_snapshot: Tuple[object, ...],
    ) -> CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate:
        self._require_owner_snapshot(owner_snapshot)
        context = _bound_context(self._source_law_owner)
        if context[4] is not self._decision_owner:
            raise ValueError("CP42 transitive CP37 owner changed")
        if context[7] is not self._preparation_owner:
            raise ValueError("CP42 transitive CP36 owner changed")
        certificate = self._certificate_validator(self._certificate)
        expected = self._context_certificate_builder(
            self._source_law_owner,
            self._factorization_role_sha256,
            context,
        )
        for name in _certificate_fields():
            actual = getattr(certificate, name)
            target = getattr(expected, name)
            if name in (
                "checkpoint41_certificate",
                "factorization_hypothesis",
                "checkpoint40_certificate",
                "checkpoint39_certificate",
                "checkpoint38_certificate",
                "checkpoint37_certificate",
                "checkpoint36_certificate",
            ):
                if actual is not target:
                    raise ValueError("CP42 certificate.%s identity differs" % name)
            elif type(actual) is not type(target) or actual != target:
                raise ValueError("CP42 certificate.%s differs" % name)
        self._require_owner_snapshot(owner_snapshot)
        return certificate

    def _operation_snapshots(
        self,
        owner_snapshot: Optional[Tuple[object, ...]] = None,
    ) -> Tuple[object, ...]:
        if owner_snapshot is None:
            owner_snapshot = self._owner_snapshot()
        else:
            self._require_owner_snapshot(owner_snapshot)
        certificate = self._live_certificate(owner_snapshot)
        source_snapshot = self._source_owner_snapshot(self._source_law_owner)
        admission_owner = source_snapshot[0]
        coordination_owner = source_snapshot[1]
        finite_batch_owner = source_snapshot[2]
        if type(admission_owner) is not _CP40_OWNER_TYPE:
            raise TypeError("CP42 source ancestry has the wrong CP40 owner type")
        if type(coordination_owner) is not _CP39_OWNER_TYPE:
            raise TypeError("CP42 source ancestry has the wrong CP39 owner type")
        if type(finite_batch_owner) is not _CP38_OWNER_TYPE:
            raise TypeError("CP42 source ancestry has the wrong CP38 owner type")
        admission_snapshot = self._admission_owner_snapshot(admission_owner)
        coordination_snapshot = self._coordination_owner_snapshot(coordination_owner)
        finite_batch_snapshot = self._finite_batch_owner_snapshot(finite_batch_owner)
        decision_snapshot = self._decision_owner_snapshot(self._decision_owner)
        preparation_snapshot = self._preparation_owner_snapshot(self._preparation_owner)
        record_graph_snapshot = _operation_record_graph_snapshot((certificate,))
        self._require_owner_snapshot(owner_snapshot)
        return (
            owner_snapshot,
            certificate,
            source_snapshot,
            admission_snapshot,
            coordination_snapshot,
            finite_batch_snapshot,
            decision_snapshot,
            preparation_snapshot,
            record_graph_snapshot,
        )

    def _require_operation_custody_lightweight(
        self,
        snapshots: Tuple[object, ...],
    ) -> None:
        if type(snapshots) is not tuple or len(snapshots) != 9:
            raise TypeError("CP42 operation snapshot is malformed")
        (
            owner_snapshot,
            certificate,
            source_snapshot,
            admission_snapshot,
            coordination_snapshot,
            finite_batch_snapshot,
            decision_snapshot,
            prep_snapshot,
            record_graph_snapshot,
        ) = snapshots
        self._require_owner_snapshot(owner_snapshot)
        if certificate is not owner_snapshot[5]:
            raise ValueError("CP42 operation certificate identity changed")
        self._source_require_owner_snapshot(
            self._source_law_owner,
            source_snapshot,
        )
        self._admission_require_owner_snapshot(
            source_snapshot[0],
            admission_snapshot,
        )
        self._coordination_require_owner_snapshot(
            source_snapshot[1],
            coordination_snapshot,
        )
        self._finite_batch_require_owner_snapshot(
            source_snapshot[2],
            finite_batch_snapshot,
        )
        self._decision_require_owner_snapshot(
            self._decision_owner,
            decision_snapshot,
        )
        self._preparation_require_owner_snapshot(
            self._preparation_owner,
            prep_snapshot,
        )
        _require_operation_record_graph_unchanged(record_graph_snapshot)
        self._require_owner_snapshot(owner_snapshot)

    def _require_operation_custody(self, snapshots: Tuple[object, ...]) -> None:
        self._require_operation_custody_lightweight(snapshots)
        owner_snapshot, certificate = snapshots[:2]
        if self._live_certificate(owner_snapshot) is not certificate:
            raise ValueError("CP42 live certificate identity changed")
        self._require_operation_custody_lightweight(snapshots)

    def _evaluate_predecision_operation(
        self,
        run_id: int,
        initialization_index: int,
        proposal_words: Tuple[int, ...],
        operation_snapshots: Optional[Tuple[object, ...]] = None,
    ) -> CounterKeyedInitialTiltRejectionPredecisionResult:
        if operation_snapshots is None:
            snapshots = self._operation_snapshots()
        else:
            snapshots = operation_snapshots
            self._require_operation_custody_lightweight(snapshots)
        certificate = snapshots[1]
        prep_certificate = certificate.checkpoint36_certificate
        prep_snapshot = snapshots[7]
        manifest = prep_certificate.manifest
        words_per_attempt = certificate.proposal_words_per_attempt
        scored = []
        retained = []

        def require_retained_attempts() -> None:
            self._require_operation_custody_lightweight(snapshots)
            for position, record in enumerate(retained):
                configuration, configuration_sha256, score, score_snapshot = record
                checked_configuration = self._configuration_preflight(
                    configuration,
                    name="retained CP42 configuration %d" % position,
                    maximum_cardinality=manifest.total_cap,
                    maximum_dimension=manifest.maximum_coordinate_dimension,
                )
                self._require_operation_custody_lightweight(snapshots)
                if checked_configuration is not configuration:
                    raise ValueError("retained CP42 configuration was substituted")
                current_sha256 = self._configuration_sha256(configuration)
                self._require_operation_custody_lightweight(snapshots)
                if current_sha256 != configuration_sha256:
                    raise ValueError("retained CP42 configuration changed")
                self._score_unchanged(
                    score,
                    score_snapshot,
                    certificate=prep_certificate,
                )
                self._require_operation_custody_lightweight(snapshots)

        for attempt_index in range(certificate.attempt_budget):
            start = attempt_index * words_per_attempt
            words = proposal_words[start : start + words_per_attempt]
            materialized = []
            materialized_snapshots = []
            for raw_slot_index in range(manifest.total_cap):
                fields = self._slot_materializer(
                    manifest,
                    words,
                    raw_slot_index=raw_slot_index,
                )
                self._require_operation_custody_lightweight(snapshots)
                fields = self._materialized_preflight(
                    fields,
                    manifest=manifest,
                    words=words,
                    raw_slot_index=raw_slot_index,
                )
                self._require_operation_custody_lightweight(snapshots)
                fields_snapshot = self._materialized_snapshot(fields)
                self._require_operation_custody_lightweight(snapshots)
                self._materialized_unchanged(
                    fields,
                    fields_snapshot,
                    manifest=manifest,
                    words=words,
                    raw_slot_index=raw_slot_index,
                )
                materialized.append(fields)
                materialized_snapshots.append(fields_snapshot)
            cardinality = self._quota_position(
                words[manifest.count_word_offset],
                manifest.count_cumulative_ends,
            )
            self._require_operation_custody_lightweight(snapshots)
            slots = []
            slot_snapshots = []
            for raw_slot_index, fields in enumerate(materialized):
                slot = self._slot_maker(
                    prep_certificate.checkpoint28_certificate,
                    manifest,
                    fields,
                    active=raw_slot_index < cardinality,
                )
                self._require_operation_custody_lightweight(snapshots)
                self._slot_preflight(
                    slot,
                    name="fresh CP42 raw slot %d" % raw_slot_index,
                    manifest=manifest,
                )
                self._require_operation_custody_lightweight(snapshots)
                slot_snapshot = self._slot_snapshot(slot)
                self._require_operation_custody_lightweight(snapshots)
                checked_slot = self._slot_validator(slot)
                self._require_operation_custody_lightweight(snapshots)
                if checked_slot is not slot:
                    raise ValueError("CP28 slot validation substituted its record")
                self._slot_unchanged(
                    slot,
                    slot_snapshot,
                    position=raw_slot_index,
                    manifest=manifest,
                )
                slots.append(slot)
                slot_snapshots.append(slot_snapshot)

            def canonical_key(index: int) -> Tuple[object, ...]:
                key = self._event_model_key(slots[index].event)
                self._require_operation_custody_lightweight(snapshots)
                return (key, index)

            canonical_order = tuple(
                sorted(
                    range(cardinality),
                    key=canonical_key,
                )
            )
            canonical = tuple(slots[index].event for index in canonical_order)
            canonical_sha256 = self._configuration_sha256(canonical)
            self._require_operation_custody_lightweight(snapshots)
            score = self._tilt_evaluate(
                prep_snapshot[1],
                canonical,
                residual_context=prep_snapshot[6],
            )
            self._require_operation_custody_lightweight(snapshots)
            self._tilt_preflight(score, certificate=prep_certificate)
            self._require_operation_custody_lightweight(snapshots)
            score_snapshot = self._score_snapshot(score)
            self._require_operation_custody_lightweight(snapshots)
            self._score_unchanged(
                score,
                score_snapshot,
                certificate=prep_certificate,
            )
            checked_score = self._tilt_validate(
                prep_snapshot[1],
                score,
                canonical,
                residual_context=prep_snapshot[6],
            )
            self._require_operation_custody_lightweight(snapshots)
            if checked_score is not score:
                raise ValueError("CP30 validation substituted its score record")
            self._score_unchanged(
                score,
                score_snapshot,
                certificate=prep_certificate,
            )
            for position, (fields, before) in enumerate(
                zip(materialized, materialized_snapshots)
            ):
                self._materialized_unchanged(
                    fields,
                    before,
                    manifest=manifest,
                    words=words,
                    raw_slot_index=position,
                )
            for position, (slot, before) in enumerate(zip(slots, slot_snapshots)):
                self._slot_unchanged(
                    slot,
                    before,
                    position=position,
                    manifest=manifest,
                )
            q = self._fraction_parts(
                score.exact_initial_log_factor_numerator,
                score.exact_initial_log_factor_denominator,
                name="CP42 exact q",
            )
            self._require_operation_custody_lightweight(snapshots)
            upper = self._fraction_parts(
                prep_certificate.global_upper_bound_numerator,
                prep_certificate.global_upper_bound_denominator,
                name="CP42 global upper bound",
            )
            self._require_operation_custody_lightweight(snapshots)
            delta = q - upper
            if delta.denominator & (delta.denominator - 1):
                raise ValueError("CP42 score gap is not dyadic")
            if delta > 0:
                raise ValueError("CP42 score exceeds the certified global bound")
            scored.append((canonical, delta))
            retained.append((canonical, canonical_sha256, score, score_snapshot))
            require_retained_attempts()
        rows = []
        for attempt_index, (configuration, delta) in enumerate(scored):
            require_retained_attempts()
            checked_delta = self._fraction_parts(
                delta.numerator,
                delta.denominator,
                name="CP42 quota delta",
            )
            self._require_operation_custody_lightweight(snapshots)
            if checked_delta.denominator & (checked_delta.denominator - 1):
                raise ValueError("CP42 quota delta is not dyadic")
            if checked_delta > 0:
                raise ValueError("CP42 quota delta is positive")
            self._require_operation_custody_lightweight(snapshots)
            try:
                quota = self._quota_builder(checked_delta)
            except self._quota_error as error:
                self._require_operation_custody_lightweight(snapshots)
                if type(error) is not self._quota_error:
                    raise
                require_retained_attempts()
                result = self._predecision_builder(
                    certificate,
                    run_id,
                    initialization_index,
                    proposal_words,
                    "quota_certification_failure",
                    (),
                )
                self._require_operation_custody(snapshots)
                return result
            self._require_operation_custody_lightweight(snapshots)
            require_retained_attempts()
            row = self._row_builder(
                attempt_index,
                configuration,
                checked_delta,
                quota,
                trusted_certificate=certificate,
            )
            self._require_operation_custody_lightweight(snapshots)
            rows.append(row)
        result = self._predecision_builder(
            certificate,
            run_id,
            initialization_index,
            proposal_words,
            "ready",
            tuple(rows),
        )
        self._require_operation_custody(snapshots)
        return result

    def evaluate_predecision(
        self,
        run_id: object,
        initialization_index: object,
        proposal_words: object,
    ) -> CounterKeyedInitialTiltRejectionPredecisionResult:
        owner_snapshot = self._owner_snapshot()
        checked_run = _exact_integer(run_id, name="run_id")
        checked_initialization = _exact_integer(
            initialization_index,
            name="initialization_index",
        )
        operation_snapshots = self._operation_snapshots(owner_snapshot)
        certificate = operation_snapshots[1]
        words = _exact_words(
            proposal_words,
            name="proposal_words",
            length=certificate.proposal_word_count,
        )
        result = self._evaluate_predecision_operation(
            checked_run,
            checked_initialization,
            words,
            operation_snapshots,
        )
        self._require_owner_snapshot(owner_snapshot)
        return result

    def validate_predecision_result(
        self,
        result: object,
    ) -> CounterKeyedInitialTiltRejectionPredecisionResult:
        owner_snapshot = self._owner_snapshot()
        operation_snapshots = self._operation_snapshots(owner_snapshot)
        certificate = operation_snapshots[1]
        checked = self._predecision_validator(
            result,
            trusted_certificate=certificate,
        )
        self._require_operation_custody_lightweight(operation_snapshots)
        replay = self._evaluate_predecision_operation(
            checked.run_id,
            checked.initialization_index,
            checked.proposal_words,
            operation_snapshots,
        )
        if replay.result_sha256 != checked.result_sha256:
            raise ValueError("predecision result differs from exact V-only replay")
        self._require_owner_snapshot(owner_snapshot)
        return checked

    def apply_decision_words(
        self,
        predecision_result: object,
        decision_words: object,
    ) -> CounterKeyedInitialTiltRejectionAppliedDecision:
        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        parent = self.validate_predecision_result(predecision_result)
        result = self._applied_builder(certificate, parent, decision_words)
        checked = self._applied_validator(
            result,
            trusted_certificate=certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        return checked

    def validate_applied_decision(
        self,
        result: object,
    ) -> CounterKeyedInitialTiltRejectionAppliedDecision:
        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        checked = self._applied_validator(
            result,
            trusted_certificate=certificate,
        )
        self.validate_predecision_result(checked.predecision_result)
        replay = self._applied_builder(
            certificate,
            checked.predecision_result,
            checked.decision_words,
        )
        if replay.applied_decision_sha256 != checked.applied_decision_sha256:
            raise ValueError("applied decision differs from exact H-stage replay")
        self._require_owner_snapshot(owner_snapshot)
        return checked

    def _require_successful_projection_parity(
        self,
        predecision: CounterKeyedInitialTiltRejectionPredecisionResult,
        live: _CP37_RESULT_TYPE,
    ) -> None:
        if predecision.status != "ready":
            raise ValueError("successful parity requires a ready CP42 result")
        if type(live) is not _CP37_RESULT_TYPE:
            raise TypeError("checkpoint37_result has the wrong exact type")
        checked_live = self._decision_validate_result(
            self._decision_owner,
            live,
            predecision.run_id,
            predecision.initialization_index,
        )
        if checked_live is not live:
            raise ValueError("CP37 validation substituted its result")
        parent = live.preparation_result
        live_words = tuple(
            word
            for attempt in parent.attempts
            for word in attempt.proposal_concatenated_raw64_words
        )
        _exact_words(
            live_words,
            name="live CP36 proposal words",
            length=self._certificate.proposal_word_count,
        )
        if live_words != predecision.proposal_words:
            raise ValueError("CP42 proposal words differ from live CP36")
        if len(parent.attempts) != len(live.thresholds) or len(live.thresholds) != len(
            predecision.rows
        ):
            raise ValueError("successful parity attempt count differs")
        witness_names = (
            "delta_numerator",
            "delta_denominator",
            "threshold_branch",
            "decimal_precision_used",
            "ideal_probability_lower_numerator",
            "ideal_probability_lower_denominator",
            "ideal_probability_upper_numerator",
            "ideal_probability_upper_denominator",
            "ideal_probability_upper_strict",
            "acceptance_quota",
            "quota_probability_numerator",
            "quota_probability_denominator",
            "ideal_minus_quota_error_strict_upper_numerator",
            "ideal_minus_quota_error_strict_upper_denominator",
        )
        for position, (row, attempt, threshold) in enumerate(
            zip(predecision.rows, parent.attempts, live.thresholds)
        ):
            if row.attempt_index != position or attempt.attempt_index != position:
                raise ValueError("successful parity attempt chronology differs")
            if threshold.attempt_index != position:
                raise ValueError("successful parity threshold chronology differs")
            if not _same_configuration(
                row.canonical_configuration,
                attempt.canonical_configuration,
            ):
                raise ValueError("successful parity configuration differs")
            if row.canonical_configuration_sha256 != (
                attempt.canonical_configuration_sha256
            ):
                raise ValueError("successful parity configuration digest differs")
            if row.delta_numerator != attempt.q_minus_upper_bound_numerator or (
                row.delta_denominator != attempt.q_minus_upper_bound_denominator
            ):
                raise ValueError("successful parity score gap differs")
            for name in witness_names:
                if getattr(row, name) != getattr(threshold, name):
                    raise ValueError("successful parity field %s differs" % name)

    def witness_successful_parity(
        self,
        predecision_result: object,
        checkpoint37_result: object,
    ) -> CounterKeyedInitialTiltRejectionSuccessfulParityWitness:
        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        predecision = self.validate_predecision_result(predecision_result)
        self._require_successful_projection_parity(
            predecision,
            checkpoint37_result,
        )
        values: Dict[str, object] = {
            "certificate": certificate,
            "certificate_sha256": certificate.certificate_sha256,
            "predecision_result": predecision,
            "predecision_result_sha256": predecision.result_sha256,
            "checkpoint37_result": checkpoint37_result,
            "checkpoint37_result_sha256": checkpoint37_result.result_sha256,
            "proposal_words_sha256": predecision.proposal_words_sha256,
            "semantic_predecision_sha256": (predecision.semantic_predecision_sha256),
            "successful_projection_equal": True,
            "universal_equivalence_claimed": False,
            "live_failure_equivalence_claimed": False,
            "witness_sha256": _ZERO_SHA256,
        }
        values["witness_sha256"] = _semantic_digest(_witness_payload(values))
        witness = CounterKeyedInitialTiltRejectionSuccessfulParityWitness(
            _construction_token=_WITNESS_TOKEN,
            **values,
        )
        self._require_owner_snapshot(owner_snapshot)
        return witness

    def validate_successful_parity_witness(
        self,
        witness: object,
    ) -> CounterKeyedInitialTiltRejectionSuccessfulParityWitness:
        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        checked = self._witness_validator(
            witness,
            trusted_certificate=certificate,
        )
        predecision = self.validate_predecision_result(checked.predecision_result)
        self._require_successful_projection_parity(
            predecision,
            checked.checkpoint37_result,
        )
        self._require_owner_snapshot(owner_snapshot)
        return checked


def _certify_predecision_factorization(
    source_law_owner: object,
    *,
    factorization_policy: object,
    factorization_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner:
    if type(source_law_owner) is not _CP41_OWNER_TYPE:
        raise TypeError("source_law_owner has the wrong exact CP41 type")
    policy = _require_text(
        factorization_policy,
        _POLICY,
        name="factorization_policy",
    )
    role = _require_sha256(
        factorization_role_sha256,
        name="factorization_role_sha256",
    )
    context = _bound_context(source_law_owner)
    certificate = _make_certificate_from_context(source_law_owner, role, context)
    owner = CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner(
        source_law_owner,
        context[4],
        context[7],
        policy,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    snapshot = owner._owner_snapshot()
    owner._live_certificate(snapshot)
    owner._require_owner_snapshot(snapshot)
    return owner


def _require_matching_predecision_factorization(
    source_law_owner: object,
    owner: object,
    *,
    factorization_policy: object,
    factorization_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner:
    if type(source_law_owner) is not _CP41_OWNER_TYPE:
        raise TypeError("source_law_owner has the wrong exact CP41 type")
    if type(owner) is not CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner:
        raise TypeError("owner has the wrong exact CP42 type")
    policy = _require_text(
        factorization_policy,
        _POLICY,
        name="factorization_policy",
    )
    role = _require_sha256(
        factorization_role_sha256,
        name="factorization_role_sha256",
    )
    snapshot = owner._owner_snapshot()
    certificate = owner._live_certificate(snapshot)
    if owner.source_law_owner is not source_law_owner:
        raise ValueError("owner belongs to another CP41 parent")
    if owner._factorization_policy != policy:
        raise ValueError("owner factorization policy differs")
    if owner._factorization_role_sha256 != role:
        raise ValueError("owner factorization role differs")
    if certificate.checkpoint41_owner_runtime_identity != id(source_law_owner):
        raise ValueError("owner certificate CP41 identity differs")
    owner._require_owner_snapshot(snapshot)
    return owner


def _validate_predecision_factorization_certificate(
    source_law_owner: object,
    owner: object,
    *,
    factorization_policy: object,
    factorization_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate:
    return _require_matching_predecision_factorization(
        source_law_owner,
        owner,
        factorization_policy=factorization_policy,
        factorization_role_sha256=factorization_role_sha256,
    ).certificate


_PUBLIC_CERTIFY_NAME = (
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "predecision_factorization"
)
_PUBLIC_MATCHING_NAME = (
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "predecision_factorization"
)
_PUBLIC_VALIDATE_CERTIFICATE_NAME = (
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "predecision_factorization_certificate"
)

_FROZEN_OPERATION_SURFACES = tuple(
    sorted(
        (
            (name, value)
            for name, value in _LOCAL_NAMESPACE.items()
            if not name.startswith("_")
        ),
        key=lambda item: item[0],
    )
)
_FROZEN_PRIVATE_NAMESPACE = tuple(
    sorted(
        (
            (name, value)
            for name, value in _LOCAL_NAMESPACE.items()
            if name.startswith("_") and not name.startswith("__")
        ),
        key=lambda item: item[0],
    )
)


def _require_surfaces(
    dependency_guard: object = _require_dependency_surfaces,
    frozen: Tuple[Tuple[str, object], ...] = _FROZEN_OPERATION_SURFACES,
    private_namespace: Tuple[Tuple[str, object], ...] = _FROZEN_PRIVATE_NAMESPACE,
    local_guard: object = _require_unshadowed_local_runtime,
    namespace: Dict[str, object] = _LOCAL_NAMESPACE,
    missing: object = _MISSING_LOCAL_GLOBAL,
    error_type: object = _LOCAL_NAMESPACE_ERROR,
) -> None:
    local_guard()
    if (
        "_require_dependency_surfaces" not in namespace
        or namespace["_require_dependency_surfaces"] is not dependency_guard
    ):
        raise error_type("CP42 dependency guard changed")
    if (
        "_FROZEN_OPERATION_SURFACES" not in namespace
        or namespace["_FROZEN_OPERATION_SURFACES"] is not frozen
    ):
        raise error_type("CP42 frozen operation surfaces changed")
    if (
        "_FROZEN_PRIVATE_NAMESPACE" not in namespace
        or namespace["_FROZEN_PRIVATE_NAMESPACE"] is not private_namespace
    ):
        raise error_type("CP42 private namespace snapshot changed")
    for name, expected in frozen + private_namespace:
        if name not in namespace or namespace[name] is not expected:
            raise error_type("CP42 operation surface %s changed" % name)
    dependency_guard()


def _bind_owner_identity_state(
    implementation: object,
    expected_surface_guard: object,
    local_guard: object,
    error_type: object,
) -> object:
    def identity_state(
        self: CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner,
    ) -> Tuple[object, ...]:
        local_guard()
        if self._surface_guard is not expected_surface_guard:
            raise error_type("predecision factorization surface guard changed")
        if self._surface_guard_identity is not expected_surface_guard:
            raise error_type("predecision factorization guard identity changed")
        expected_surface_guard()
        return implementation(
            self,
            _local_guard=local_guard,
            _error_type=error_type,
        )

    return identity_state


_OWNER_IDENTITY_STATE = _bind_owner_identity_state(
    CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner._identity_state,
    _require_surfaces,
    _require_unshadowed_local_runtime,
    _LOCAL_NAMESPACE_ERROR,
)
_OWNER_IDENTITY_STATE.__name__ = "_identity_state"
_OWNER_IDENTITY_STATE.__qualname__ = (
    "CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner._identity_state"
)
CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner._identity_state = (
    _OWNER_IDENTITY_STATE
)


def _bind_public_api(
    certify_impl: object,
    matching_impl: object,
    namespace: Dict[str, object] = _LOCAL_NAMESPACE,
    local_guard: object = _require_unshadowed_local_runtime,
    surface_guard: object = _require_surfaces,
    error_type: object = _LOCAL_NAMESPACE_ERROR,
    owner_type: object = (
        CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner
    ),
    owner_identity_state: object = _OWNER_IDENTITY_STATE,
) -> Tuple[object, object, object]:
    late_surfaces: Tuple[Tuple[str, object], ...] = ()

    def require_late_surfaces() -> None:
        local_guard()
        for name, expected in late_surfaces:
            if name not in namespace or namespace[name] is not expected:
                raise error_type("CP42 late operation surface %s changed" % name)
        if owner_type._identity_state is not owner_identity_state:
            raise error_type("CP42 owner identity-state surface changed")
        surface_guard()

    def certify(
        source_law_owner: object,
        *,
        factorization_policy: object,
        factorization_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner:
        require_late_surfaces()
        return certify_impl(
            source_law_owner,
            factorization_policy=factorization_policy,
            factorization_role_sha256=factorization_role_sha256,
        )

    def matching(
        source_law_owner: object,
        owner: object,
        *,
        factorization_policy: object,
        factorization_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner:
        require_late_surfaces()
        return matching_impl(
            source_law_owner,
            owner,
            factorization_policy=factorization_policy,
            factorization_role_sha256=factorization_role_sha256,
        )

    def validate_certificate(
        source_law_owner: object,
        owner: object,
        *,
        factorization_policy: object,
        factorization_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate:
        return matching(
            source_law_owner,
            owner,
            factorization_policy=factorization_policy,
            factorization_role_sha256=factorization_role_sha256,
        ).certificate

    late_surfaces = (
        ("_certify_predecision_factorization", certify_impl),
        ("_require_matching_predecision_factorization", matching_impl),
        ("_require_surfaces", surface_guard),
        ("_OWNER_IDENTITY_STATE", owner_identity_state),
        (
            "CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner",
            owner_type,
        ),
        (_PUBLIC_CERTIFY_NAME, certify),
        (_PUBLIC_MATCHING_NAME, matching),
        (_PUBLIC_VALIDATE_CERTIFICATE_NAME, validate_certificate),
    )
    return certify, matching, validate_certificate


_PUBLIC_FUNCTIONS = _bind_public_api(
    _certify_predecision_factorization,
    _require_matching_predecision_factorization,
)
for _public_name, _public_function in zip(
    (
        _PUBLIC_CERTIFY_NAME,
        _PUBLIC_MATCHING_NAME,
        _PUBLIC_VALIDATE_CERTIFICATE_NAME,
    ),
    _PUBLIC_FUNCTIONS,
):
    _public_function.__name__ = _public_name
    _public_function.__qualname__ = _public_name
    _LOCAL_NAMESPACE[_public_name] = _public_function


__all__ = [
    _PUBLIC_SCHEMA_VERSION_NAME,
    (
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_"
        "PREDECISION_FACTORIZATION_POLICY"
    ),
    (
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_"
        "PREDECISION_FACTORIZATION_SCOPE"
    ),
    "INITIAL_TILT_REJECTION_PREDECISION_STATUSES",
    "INITIAL_TILT_REJECTION_APPLIED_DECISION_STATUSES",
    "INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_THEOREM",
    "INITIAL_TILT_REJECTION_PREDECISION_DYADIC_DENOMINATOR",
    "INITIAL_TILT_REJECTION_PREDECISION_MAX_ATTEMPTS",
    "INITIAL_TILT_REJECTION_PREDECISION_MAX_PROPOSAL_WORDS",
    "CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate",
    "CounterKeyedInitialTiltRejectionPredecisionRow",
    "CounterKeyedInitialTiltRejectionPredecisionResult",
    "CounterKeyedInitialTiltRejectionAppliedDecision",
    "CounterKeyedInitialTiltRejectionSuccessfulParityWitness",
    "CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionPredecisionFactorizationError",
    _PUBLIC_CERTIFY_NAME,
    _PUBLIC_MATCHING_NAME,
    _PUBLIC_VALIDATE_CERTIFICATE_NAME,
]
