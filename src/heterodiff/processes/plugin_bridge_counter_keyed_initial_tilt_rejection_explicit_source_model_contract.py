"""Bind deterministic replay and declared external request-law source models.

Checkpoint forty-five proves that one fixed checkpoint-forty-four request is a
deterministic point source, not a product-uniform word source.  This module
records the next boundary without manufacturing randomness: a fixed request
and an externally declared finite rational law over the two public uint64
request coordinates are distinct sealed models.

Let ``D=2**64`` and let the complete CP44 capsule contain ``L`` words.  If an
external request law has finite support size ``s``, any deterministic partial
request-to-capsule map, conditioned on any positive acquisition or returned-
result event, has capsule support at most ``s``.  Consequently

``TV(nu_event, Uniform([D]**L)) >= 1 - s / D**L``.

No success/value-independence premise is needed.  Even a law supported on the
entire current request surface has ``s <= D**2``; because CP45 certifies
``L>2``, randomizing only ``(run_id, initialization_index)`` cannot create a
product-uniform complete capsule.

The executable external-law declaration is deliberately finite and capped at
4096 atoms.  The full ``D**2`` request-surface result is a separate analytic
capacity theorem; this API does not enumerate that surface.  A declaration is
not a sampler or evidence that a caller realizes its probabilities.

This module performs no CP27 allocation and no CP43/CP44 semantic operation.
It provides no numeric success/refusal mass, unconditional capsule or output
law, nondegenerate V/W independence, physical randomness, freshness,
initializer, path, sampler, or scientific claim.  Certification, cached
certificate validation during ordinary model operations, and explicit live
revalidation may inherit CP45's deterministic local Philox ancestry probe.
Ordinary model construction does not call the CP45 owner's live-binding
method; each returned model says that current live ancestry was not
revalidated for that model.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import gcd
import platform
import sys
from typing import Dict, Mapping, Tuple

from heterodiff.processes import (
    plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction as _obstruction,
)


_GCD = gcd
_JSON_DUMPS = json.dumps
_SHA256 = hashlib.sha256
_PYTHON_VERSION = tuple(sys.version_info[:3])
_PYTHON_IMPLEMENTATION = platform.python_implementation()


PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_CONTRACT_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-explicit-source-model-"
    "contract-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_CONTRACT_POLICY = (
    "exact-checkpoint45-and-transitive-checkpoint44-36-27-26-binding;"
    "separate-fixed-request-and-declared-external-request-law-models;"
    "canonical-finite-positive-rational-request-mass-table;"
    "positive-event-conditional-source-support-bound;"
    "current-two-coordinate-request-surface-capacity-obstruction;"
    "finite-declaration-cap-separate-from-analytic-D2-capacity;"
    "no-success-value-independence-premise;"
    "declarative-only-no-external-law-realization-or-sampling;"
    "no-source-allocation-or-semantic-execution;"
    "cached-model-descriptors-with-explicit-live-ancestry-revalidation;"
    "model-description-without-parent-owner-live-binding;"
    "ancestry-certificate-validation-may-inherit-deterministic-local-Philox-"
    "runtime-probe-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_CONTRACT_SCOPE = (
    "fixed-request-and-finite-external-request-law-source-models;"
    "conditioning-on-positive-complete-capsule-or-returned-result-event;"
    "support-and-Hartley-capacity-statements-only;"
    "current-live-request-surface-is-exactly-two-uint64-coordinates;"
    "executable-law-declarations-have-at-most-4096-atoms;"
    "full-D2-request-capacity-is-an-analytic-theorem-not-an-enumerated-law;"
    "ordinary-model-records-use-cached-certified-ancestry;"
    "current-live-ancestry-revalidation-is-explicit-and-separate;"
    "not-realized-external-law-or-request-sampler;"
    "not-live-request-uniformity-independence-or-physical-entropy;"
    "not-full-capsule-product-uniformity-or-nondegenerate-V-W-independence;"
    "not-numeric-success-refusal-or-unconditional-law;"
    "not-output-TV-lower-bound-or-output-discrepancy;"
    "not-freshness-portability-loaded-code-integrity-or-cryptography;"
    "not-initializer-path-sampler-scientific-model-quality-or-generality-evidence"
)
INITIAL_TILT_REJECTION_FIXED_REQUEST_SOURCE_MODEL_THEOREM = (
    "for-one-exact-fixed-request-and-any-positive-declared-conditioning-event;"
    "the-deterministic-capsule-law-is-delta_z-with-"
    "TV(delta_z,U_L)=1-D^(-L);repeated-same-request-replay-does-not-certify-"
    "freshness-or-nondegenerate-independence"
)
INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_SUPPORT_THEOREM = (
    "for-any-external-request-law-with-finite-support-s-and-any-deterministic-"
    "partial-request-to-L-word-capsule-map;conditional-on-any-positive-event-"
    "the-capsule-support-is-at-most-s-and-TV(nu_event,U_L)>=1-s/D^L;"
    "no-success-value-independence-is-required"
)
INITIAL_TILT_REJECTION_CURRENT_REQUEST_SURFACE_CAPACITY_THEOREM = (
    "analytic-full-surface-theorem:the-current-request-domain-is-D^2;"
    "therefore-any-request-law-and-any-"
    "deterministic-partial-map-have-positive-event-conditional-capsule-"
    "support-at-most-D^2;when-L>2-product-uniform-U_L-is-impossible-by-support"
)
INITIAL_TILT_REJECTION_FULL_PRODUCT_UNIFORM_SOURCE_SUPPORT_AND_FIBER_CRITERION = (
    "for-a-live-claim-request-support-at-least-D^L-is-necessary-but-not-"
    "sufficient;under-a-realized-mu-and-deterministic-F-with-positive-event;"
    "conditional-product-uniformity-holds-iff-every-output-fiber-has-"
    "conditional-mass-D^(-L);CP46-certifies-neither-external-law-realization-"
    "nor-weighted-fiber-balance"
)
INITIAL_TILT_REJECTION_EXTERNAL_SOURCE_TO_OUTPUT_TV_NONCONVERSE = (
    "source-support-TV-lower-bounds-do-not-descend-through-an-arbitrary-"
    "semantic-map;data-processing-is-an-upper-bound-and-a-constant-map-can-"
    "erase-all-source-discrepancy"
)
INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_RAW_WORD_DOMAIN_SIZE = 1 << 64
INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_REQUEST_COORDINATES = 2
INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MAX_SUPPORT = 4096
INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MAX_INTEGER_BITS = 16384
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_DECLARATION_SCOPE = (
    "exact-finite-positive-rational-PMF-over-two-uint64-request-coordinates;"
    "canonical-support-at-most-4096-atoms;declarative-only;"
    "not-full-D2-enumeration-realization-sampling-randomness-uniformity-"
    "independence-or-event-law"
)
INITIAL_TILT_REJECTION_FIXED_REQUEST_MODE = "fixed-request-replay"
INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MODE = (
    "declared-external-finite-request-law"
)
INITIAL_TILT_REJECTION_COMPLETE_CAPSULE_CONDITIONING = (
    "complete-validated-capsule-event"
)
INITIAL_TILT_REJECTION_RETURNED_RESULT_CONDITIONING = (
    "checkpoint44-returned-result-event"
)

_SCHEMA_VERSION = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_CONTRACT_SCHEMA_VERSION
_POLICY = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_CONTRACT_POLICY
_SCOPE = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_CONTRACT_SCOPE
_FIXED_THEOREM = INITIAL_TILT_REJECTION_FIXED_REQUEST_SOURCE_MODEL_THEOREM
_EXTERNAL_THEOREM = INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_SUPPORT_THEOREM
_CAPACITY_THEOREM = INITIAL_TILT_REJECTION_CURRENT_REQUEST_SURFACE_CAPACITY_THEOREM
_FULL_UNIFORM_CRITERION = (
    INITIAL_TILT_REJECTION_FULL_PRODUCT_UNIFORM_SOURCE_SUPPORT_AND_FIBER_CRITERION
)
_NONCONVERSE = INITIAL_TILT_REJECTION_EXTERNAL_SOURCE_TO_OUTPUT_TV_NONCONVERSE
_D = INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_RAW_WORD_DOMAIN_SIZE
_REQUEST_COORDINATES = INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_REQUEST_COORDINATES
_MAX_SUPPORT = INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MAX_SUPPORT
_MAX_INTEGER_BITS = INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MAX_INTEGER_BITS
_DECLARATION_SCOPE = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_DECLARATION_SCOPE
_FIXED_MODE = INITIAL_TILT_REJECTION_FIXED_REQUEST_MODE
_EXTERNAL_MODE = INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MODE
_CAPSULE_CONDITIONING = INITIAL_TILT_REJECTION_COMPLETE_CAPSULE_CONDITIONING
_RETURN_CONDITIONING = INITIAL_TILT_REJECTION_RETURNED_RESULT_CONDITIONING
_CONDITIONING_EVENTS = (_CAPSULE_CONDITIONING, _RETURN_CONDITIONING)
_ZERO_SHA256 = "0" * 64

_DECLARATION_TOKEN = object()
_CERTIFICATE_TOKEN = object()
_FIXED_MODEL_TOKEN = object()
_EXTERNAL_MODEL_TOKEN = object()
_OWNER_TOKEN = object()

_CP45_OWNER_TYPE = (
    _obstruction.CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner
)
_CP45_CERT_TYPE = (
    _obstruction.CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate
)
_CP45_VALIDATE_CERTIFICATE = _obstruction._validate_certificate
_CP45_OWNER_LIVE_BINDING = _CP45_OWNER_TYPE._require_live_binding
_CP45_REQUIRE_DEPENDENCY_SURFACES = _obstruction._require_dependency_surfaces
_CP45_REQUIRE_LOCAL_SURFACES = _obstruction._require_local_surfaces
_CP45_CERTIFICATE_PROPERTY = _CP45_OWNER_TYPE.certificate


class PluginBridgeCounterKeyedInitialTiltRejectionExplicitSourceModelContractError(
    ArithmeticError
):
    """Fail-closed CP46 explicit source-model custody error."""


def _require_dependency_surfaces() -> None:
    """Refuse substituted CP45 surfaces without invoking live ancestry."""

    module_expectations = (
        (_obstruction, "_validate_certificate", _CP45_VALIDATE_CERTIFICATE),
        (
            _obstruction,
            "_require_dependency_surfaces",
            _CP45_REQUIRE_DEPENDENCY_SURFACES,
        ),
        (
            _obstruction,
            "_require_local_surfaces",
            _CP45_REQUIRE_LOCAL_SURFACES,
        ),
    )
    for module, name, expected in module_expectations:
        if not hasattr(module, name) or getattr(module, name) is not expected:
            raise ValueError("CP46 dependency surface changed: %s" % name)
    method_expectations = (
        (_CP45_OWNER_TYPE, "_require_live_binding", _CP45_OWNER_LIVE_BINDING),
    )
    for owner_type, name, expected in method_expectations:
        if getattr(owner_type, name) is not expected:
            raise ValueError("CP46 parent method changed: %s" % name)
    if _CP45_OWNER_TYPE.certificate is not _CP45_CERTIFICATE_PROPERTY:
        raise ValueError("CP46 parent property changed: certificate")
    _CP45_REQUIRE_LOCAL_SURFACES()


def _canonical(value: object) -> object:
    if value is None or type(value) in (bool, str):
        return value
    if type(value) is int:
        sign = "-" if value < 0 else "+"
        return {"cp46_exact_integer_hex": sign + format(abs(value), "x")}
    if type(value) is tuple:
        return [_canonical(item) for item in value]
    if type(value) is dict:
        return {str(key): _canonical(item) for key, item in value.items()}
    raise TypeError("unsupported value in CP46 semantic digest")


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


def _exact_nonnegative_integer(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < 0:
        raise ValueError(name + " must be nonnegative")
    return value


def _exact_uint64(value: object, *, name: str) -> int:
    checked = _exact_nonnegative_integer(value, name=name)
    if checked >= _D:
        raise ValueError(name + " must be below 2^64")
    return checked


def _bounded_positive_integer(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value <= 0:
        raise ValueError(name + " must be positive")
    if value.bit_length() > _MAX_INTEGER_BITS:
        raise ValueError(name + " exceeds the CP46 integer-bit limit")
    return value


def _exact_bool(value: object, expected: bool, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(name + " must be an exact bool")
    if value is not expected:
        raise ValueError(name + " differs from the frozen CP46 boundary")
    return value


def _conditioning_event(value: object) -> str:
    if type(value) is not str:
        raise TypeError("conditioning_event must be exact text")
    if value not in _CONDITIONING_EVENTS:
        raise ValueError("conditioning_event is not a CP46 event")
    return value


def _runtime_sha256() -> str:
    return _semantic_digest(
        {
            "domain": "cp46-explicit-source-model-runtime-v1",
            "python": _PYTHON_VERSION,
            "implementation": _PYTHON_IMPLEMENTATION,
            "schema": _SCHEMA_VERSION,
            "policy": _POLICY,
            "scope": _SCOPE,
            "fixed_theorem": _FIXED_THEOREM,
            "external_theorem": _EXTERNAL_THEOREM,
            "capacity_theorem": _CAPACITY_THEOREM,
            "full_uniform_support_and_fiber_criterion": _FULL_UNIFORM_CRITERION,
            "nonconverse": _NONCONVERSE,
            "declaration_scope": _DECLARATION_SCOPE,
        }
    )


def _preflight_request_mass_rows(value: object) -> Tuple[Tuple[int, int, int], ...]:
    if type(value) is not tuple:
        raise TypeError("request_mass_rows must be an exact tuple")
    if not value:
        raise ValueError("request_mass_rows must be nonempty")
    if len(value) > _MAX_SUPPORT:
        raise ValueError("request_mass_rows exceeds the CP46 support limit")
    checked = []
    previous = None
    for row_index, row in enumerate(value):
        if type(row) is not tuple:
            raise TypeError("request_mass_rows entries must be exact tuples")
        if len(row) != 3:
            raise ValueError("request_mass_rows entries must have length three")
        run_id = _exact_uint64(row[0], name="request_mass_rows.run_id")
        initialization_index = _exact_uint64(
            row[1], name="request_mass_rows.initialization_index"
        )
        numerator = _bounded_positive_integer(
            row[2], name="request_mass_rows.positive_numerator"
        )
        key = (run_id, initialization_index)
        if previous is not None and key <= previous:
            raise ValueError(
                "request_mass_rows must be strictly lexicographically ordered"
            )
        previous = key
        checked.append((run_id, initialization_index, numerator))
        if len(checked) != row_index + 1:
            raise AssertionError("CP46 request-row accounting failed")
    return tuple(checked)


def _declaration_summary(
    request_mass_rows: object,
    mass_denominator: object,
) -> Mapping[str, object]:
    rows = _preflight_request_mass_rows(request_mass_rows)
    denominator = _bounded_positive_integer(mass_denominator, name="mass_denominator")
    numerator_sum = sum(row[2] for row in rows)
    if numerator_sum != denominator:
        raise ValueError("request masses do not sum to the denominator")
    common = denominator
    for row in rows:
        common = _GCD(common, row[2])
    if common != 1:
        raise ValueError("request masses must use a reduced common denominator")
    return {
        "request_mass_rows": rows,
        "mass_denominator": denominator,
        "support_size": len(rows),
        "raw_word_domain_size": _D,
        "request_coordinate_count": _REQUEST_COORDINATES,
        "request_surface_support_log2": 64 * _REQUEST_COORDINATES,
        "canonical_sorted_unique_positive_rows": True,
        "exact_rational_normalization_certified": True,
        "reduced_common_denominator_certified": True,
        "point_mass_request_law": len(rows) == 1,
        "declarative_only": True,
        "external_realization_certified": False,
        "sampling_defined": False,
        "physical_randomness_certified": False,
    }


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration:
    """Sealed exact rational PMF declaration; never a sampler."""

    schema_version: str
    declaration_scope: str
    request_mass_rows: Tuple[Tuple[int, int, int], ...]
    mass_denominator: int
    support_size: int
    raw_word_domain_size: int
    request_coordinate_count: int
    request_surface_support_log2: int
    canonical_sorted_unique_positive_rows: bool
    exact_rational_normalization_certified: bool
    reduced_common_denominator_certified: bool
    point_mass_request_law: bool
    declarative_only: bool
    external_realization_certified: bool
    sampling_defined: bool
    physical_randomness_certified: bool
    declaration_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP46 request-law declarations cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _DECLARATION_TOKEN:
            raise TypeError("CP46 request-law declarations are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP46 request-law declaration fields are incomplete")
        _validate_declaration_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP46 request-law declarations are not pickleable")


def _declaration_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration.__annotations__
    )


def _declaration_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: values[name]
        for name in _declaration_fields()
        if name != "declaration_sha256"
    }


def _validate_declaration_values(values: Mapping[str, object]) -> None:
    if set(values) != set(_declaration_fields()):
        raise TypeError("CP46 request-law declaration mapping is incomplete")
    if type(values["schema_version"]) is not str:
        raise TypeError("declaration.schema_version must be exact text")
    if values["schema_version"] != _SCHEMA_VERSION:
        raise ValueError("CP46 declaration schema differs")
    if type(values["declaration_scope"]) is not str:
        raise TypeError("declaration.declaration_scope must be exact text")
    if values["declaration_scope"] != _DECLARATION_SCOPE:
        raise ValueError("CP46 declaration scope differs")
    for name in (
        "support_size",
        "raw_word_domain_size",
        "request_coordinate_count",
        "request_surface_support_log2",
    ):
        if type(values[name]) is not int:
            raise TypeError("declaration.%s must be an exact integer" % name)
    for name in (
        "canonical_sorted_unique_positive_rows",
        "exact_rational_normalization_certified",
        "reduced_common_denominator_certified",
        "point_mass_request_law",
        "declarative_only",
        "external_realization_certified",
        "sampling_defined",
        "physical_randomness_certified",
    ):
        if type(values[name]) is not bool:
            raise TypeError("declaration.%s must be an exact bool" % name)
    _require_sha256(values["declaration_sha256"], name="declaration.declaration_sha256")
    expected = _declaration_summary(
        values["request_mass_rows"], values["mass_denominator"]
    )
    for name, wanted in expected.items():
        actual = values[name]
        if type(wanted) is bool:
            if type(actual) is not bool:
                raise TypeError("declaration.%s must be an exact bool" % name)
        elif type(wanted) is int:
            if type(actual) is not int:
                raise TypeError("declaration.%s must be an exact integer" % name)
        elif type(wanted) is tuple:
            if type(actual) is not tuple:
                raise TypeError("declaration.%s must be an exact tuple" % name)
        if actual != wanted:
            raise ValueError("CP46 declaration field differs: %s" % name)
    if values["declaration_sha256"] != _semantic_digest(_declaration_payload(values)):
        raise ValueError("CP46 declaration digest differs")


def _validate_declaration(
    declaration: object,
) -> CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration:
    if (
        type(declaration)
        is not CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration
    ):
        raise TypeError("declaration has the wrong exact CP46 type")
    _validate_declaration_values(
        {name: getattr(declaration, name) for name in _declaration_fields()}
    )
    return declaration


def _make_declaration(
    request_mass_rows: object,
    mass_denominator: object,
) -> CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration:
    summary = dict(_declaration_summary(request_mass_rows, mass_denominator))
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "declaration_scope": _DECLARATION_SCOPE,
        **summary,
        "declaration_sha256": _ZERO_SHA256,
    }
    values["declaration_sha256"] = _semantic_digest(_declaration_payload(values))
    return CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration(
        **values, _construction_token=_DECLARATION_TOKEN
    )


_CERTIFICATE_POSITIVE_FLAGS = (
    "exact_checkpoint45_owner_binding_certified",
    "exact_transitive_checkpoint44_36_27_26_binding_inherited",
    "exact_checkpoint44_capsule_partition_inherited",
    "fixed_and_external_models_type_separated",
    "fixed_request_point_mass_theorem_inherited",
    "external_finite_request_support_theorem_certified",
    "conditioning_cannot_enlarge_support_certified",
    "success_value_independence_not_required_certified",
    "current_two_coordinate_request_capacity_obstruction_certified",
    "source_to_output_tv_nonconverse_recorded",
    "declaration_and_model_construction_source_allocation_and_semantic_operation_free_certified",
    "model_construction_parent_owner_live_binding_free_certified",
    "no_caller_global_rng_state_mutation_certified",
    "cached_model_descriptor_boundary_recorded",
    "explicit_live_ancestry_revalidation_available",
    "declaration_support_cap_separate_from_analytic_surface_capacity_recorded",
    "support_capacity_necessary_not_sufficient_and_fiber_balance_criterion_recorded",
)
_CERTIFICATE_NEGATIVE_FLAGS = (
    "external_request_law_realization_certified",
    "external_request_sampling_certified",
    "live_request_uniformity_certified",
    "live_request_coordinate_independence_certified",
    "full_capsule_product_uniformity_certified",
    "nondegenerate_v_w_independence_certified",
    "numeric_capsule_acquisition_probability_certified",
    "numeric_return_probability_certified",
    "numeric_refusal_probability_certified",
    "unconditional_capsule_law_certified",
    "unconditional_output_law_certified",
    "semantic_output_tv_lower_bound_certified",
    "transitive_rng_call_absence_certified",
    "hidden_entropy_or_environment_accounted",
    "physical_randomness_certified",
    "cross_call_freshness_certified",
    "per_model_live_checkpoint45_ancestry_revalidation_certified",
    "conditioning_event_positive_mass_certified",
    "current_request_surface_sufficient_for_product_uniform_capsule",
    "source_support_sufficiency_for_product_uniformity_certified",
    "weighted_fiber_balance_certified",
    "external_full_entropy_source_interface_implemented",
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
_CERTIFICATE_TEXT_FIELDS = (
    "schema_version",
    "certificate_scope",
    "source_model_policy",
    "fixed_request_source_model_theorem",
    "external_finite_request_law_support_theorem",
    "current_request_surface_capacity_theorem",
    "full_product_uniform_source_support_and_fiber_criterion",
    "source_to_output_tv_nonconverse",
)
_CERTIFICATE_SHA256_FIELDS = (
    "source_model_role_sha256",
    "checkpoint45_certificate_sha256",
    "checkpoint44_certificate_sha256",
    "process_parameter_sha256",
    "source_model_runtime_sha256",
    "certificate_sha256",
)
_CERTIFICATE_INTEGER_FIELDS = (
    "checkpoint45_owner_runtime_identity",
    "raw_word_domain_size",
    "request_coordinate_count",
    "current_request_surface_support_log2",
    "full_word_count",
    "proposal_word_count",
    "decision_word_count",
    "product_uniform_capsule_support_log2",
)


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate:
    """Sealed CP45-bound certificate for the CP46 two-model contract."""

    schema_version: str
    certificate_scope: str
    source_model_policy: str
    source_model_role_sha256: str
    checkpoint45_certificate: _CP45_CERT_TYPE
    checkpoint45_certificate_sha256: str
    checkpoint45_owner_runtime_identity: int
    checkpoint44_certificate_sha256: str
    process_parameter_sha256: str
    raw_word_domain_size: int
    request_coordinate_count: int
    current_request_surface_support_log2: int
    full_word_count: int
    proposal_word_count: int
    decision_word_count: int
    product_uniform_capsule_support_log2: int
    fixed_request_source_model_theorem: str
    external_finite_request_law_support_theorem: str
    current_request_surface_capacity_theorem: str
    full_product_uniform_source_support_and_fiber_criterion: str
    source_to_output_tv_nonconverse: str
    source_model_runtime_sha256: str
    exact_checkpoint45_owner_binding_certified: bool
    exact_transitive_checkpoint44_36_27_26_binding_inherited: bool
    exact_checkpoint44_capsule_partition_inherited: bool
    fixed_and_external_models_type_separated: bool
    fixed_request_point_mass_theorem_inherited: bool
    external_finite_request_support_theorem_certified: bool
    conditioning_cannot_enlarge_support_certified: bool
    success_value_independence_not_required_certified: bool
    current_two_coordinate_request_capacity_obstruction_certified: bool
    source_to_output_tv_nonconverse_recorded: bool
    declaration_and_model_construction_source_allocation_and_semantic_operation_free_certified: bool
    model_construction_parent_owner_live_binding_free_certified: bool
    no_caller_global_rng_state_mutation_certified: bool
    cached_model_descriptor_boundary_recorded: bool
    explicit_live_ancestry_revalidation_available: bool
    declaration_support_cap_separate_from_analytic_surface_capacity_recorded: bool
    support_capacity_necessary_not_sufficient_and_fiber_balance_criterion_recorded: bool
    external_request_law_realization_certified: bool
    external_request_sampling_certified: bool
    live_request_uniformity_certified: bool
    live_request_coordinate_independence_certified: bool
    full_capsule_product_uniformity_certified: bool
    nondegenerate_v_w_independence_certified: bool
    numeric_capsule_acquisition_probability_certified: bool
    numeric_return_probability_certified: bool
    numeric_refusal_probability_certified: bool
    unconditional_capsule_law_certified: bool
    unconditional_output_law_certified: bool
    semantic_output_tv_lower_bound_certified: bool
    transitive_rng_call_absence_certified: bool
    hidden_entropy_or_environment_accounted: bool
    physical_randomness_certified: bool
    cross_call_freshness_certified: bool
    per_model_live_checkpoint45_ancestry_revalidation_certified: bool
    conditioning_event_positive_mass_certified: bool
    current_request_surface_sufficient_for_product_uniform_capsule: bool
    source_support_sufficiency_for_product_uniformity_certified: bool
    weighted_fiber_balance_certified: bool
    external_full_entropy_source_interface_implemented: bool
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
        raise TypeError("CP46 certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("CP46 certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP46 certificate fields are incomplete")
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP46 certificates are not pickleable")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate.__annotations__
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: (
            values["checkpoint45_certificate_sha256"]
            if name == "checkpoint45_certificate"
            else values[name]
        )
        for name in _certificate_fields()
        if name != "certificate_sha256"
    }


def _validate_parent_claims(parent: _CP45_CERT_TYPE) -> None:
    _require_dependency_surfaces()
    checked = _CP45_VALIDATE_CERTIFICATE(parent)
    cp44 = checked.checkpoint44_certificate
    if checked.passed is not True:
        raise ValueError("CP45 parent did not pass")
    if checked.raw_word_domain_size != _D:
        raise ValueError("CP45 raw-word domain differs")
    if checked.current_request_coordinate_count != _REQUEST_COORDINATES:
        raise ValueError("CP45 request-coordinate count differs")
    if checked.full_word_count <= _REQUEST_COORDINATES:
        raise ValueError("CP45 capsule is not longer than the request surface")
    if checked.fixed_returned_request_point_mass_theorem_certified is not True:
        raise ValueError("CP45 fixed-request theorem is not certified")
    if checked.conditional_success_support_theorem_certified is not True:
        raise ValueError("CP45 support theorem is not certified")
    if checked.source_to_output_tv_nonconverse_recorded is not True:
        raise ValueError("CP45 source-to-output nonconverse is absent")
    if checked.live_product_uniform_source_certified is not False:
        raise ValueError("CP45 unexpectedly certifies a live uniform source")
    if checked.nondegenerate_live_v_w_independence_certified is not False:
        raise ValueError("CP45 unexpectedly certifies live V/W independence")
    if cp44.raw_word_domain_size != _D:
        raise ValueError("CP44 raw-word domain differs")
    if cp44.full_word_count != checked.full_word_count:
        raise ValueError("CP44/CP45 capsule lengths differ")
    if cp44.proposal_word_count + cp44.decision_word_count != cp44.full_word_count:
        raise ValueError("CP44 capsule partition does not close")
    if cp44.checkpoint43_split_join_partition_certified is not True:
        raise ValueError("CP44 split/join partition is not certified")
    if cp44.live_philox_source_law_certified is not False:
        raise ValueError("CP44 unexpectedly certifies a live source law")
    if cp44.live_v_w_independence_certified is not False:
        raise ValueError("CP44 unexpectedly certifies live V/W independence")


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    if set(values) != set(_certificate_fields()):
        raise TypeError("CP46 certificate mapping is incomplete")
    for name in _CERTIFICATE_TEXT_FIELDS:
        if type(values[name]) is not str:
            raise TypeError("certificate.%s must be exact text" % name)
    expected_text = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "source_model_policy": _POLICY,
        "fixed_request_source_model_theorem": _FIXED_THEOREM,
        "external_finite_request_law_support_theorem": _EXTERNAL_THEOREM,
        "current_request_surface_capacity_theorem": _CAPACITY_THEOREM,
        "full_product_uniform_source_support_and_fiber_criterion": _FULL_UNIFORM_CRITERION,
        "source_to_output_tv_nonconverse": _NONCONVERSE,
    }
    for name, expected in expected_text.items():
        if values[name] != expected:
            raise ValueError("CP46 certificate text differs: %s" % name)
    for name in _CERTIFICATE_SHA256_FIELDS:
        _require_sha256(values[name], name="certificate." + name)
    for name in _CERTIFICATE_INTEGER_FIELDS:
        if type(values[name]) is not int:
            raise TypeError("certificate.%s must be an exact integer" % name)
    for name in _CERTIFICATE_POSITIVE_FLAGS + _CERTIFICATE_NEGATIVE_FLAGS + ("passed",):
        if type(values[name]) is not bool:
            raise TypeError("certificate.%s must be an exact bool" % name)
    parent = values["checkpoint45_certificate"]
    if type(parent) is not _CP45_CERT_TYPE:
        raise TypeError("checkpoint45_certificate has the wrong exact type")
    _validate_parent_claims(parent)
    cp44 = parent.checkpoint44_certificate
    expected_integers = {
        "checkpoint45_owner_runtime_identity": values[
            "checkpoint45_owner_runtime_identity"
        ],
        "raw_word_domain_size": _D,
        "request_coordinate_count": _REQUEST_COORDINATES,
        "current_request_surface_support_log2": 64 * _REQUEST_COORDINATES,
        "full_word_count": parent.full_word_count,
        "proposal_word_count": cp44.proposal_word_count,
        "decision_word_count": cp44.decision_word_count,
        "product_uniform_capsule_support_log2": 64 * parent.full_word_count,
    }
    if type(expected_integers["checkpoint45_owner_runtime_identity"]) is not int:
        raise TypeError("CP45 owner runtime identity must be an exact integer")
    for name, expected in expected_integers.items():
        if values[name] != expected:
            raise ValueError("CP46 certificate integer differs: %s" % name)
    if values["checkpoint45_certificate_sha256"] != parent.certificate_sha256:
        raise ValueError("CP46 lost CP45 certificate custody")
    if values["checkpoint44_certificate_sha256"] != cp44.certificate_sha256:
        raise ValueError("CP46 lost CP44 certificate custody")
    if values["process_parameter_sha256"] != cp44.process_parameter_sha256:
        raise ValueError("CP46 process parameter digest differs")
    if values["source_model_runtime_sha256"] != _runtime_sha256():
        raise ValueError("CP46 runtime digest differs")
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="certificate." + name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="certificate." + name)
    _exact_bool(values["passed"], True, name="certificate.passed")
    if values["certificate_sha256"] != _semantic_digest(_certificate_payload(values)):
        raise ValueError("CP46 certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate:
    if (
        type(certificate)
        is not CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate
    ):
        raise TypeError("certificate has the wrong exact CP46 type")
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _make_certificate(
    parent_owner: _CP45_OWNER_TYPE,
    role: str,
) -> CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate:
    _require_dependency_surfaces()
    parent = _CP45_OWNER_LIVE_BINDING(parent_owner)
    _validate_parent_claims(parent)
    cp44 = parent.checkpoint44_certificate
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "source_model_policy": _POLICY,
        "source_model_role_sha256": role,
        "checkpoint45_certificate": parent,
        "checkpoint45_certificate_sha256": parent.certificate_sha256,
        "checkpoint45_owner_runtime_identity": id(parent_owner),
        "checkpoint44_certificate_sha256": cp44.certificate_sha256,
        "process_parameter_sha256": cp44.process_parameter_sha256,
        "raw_word_domain_size": _D,
        "request_coordinate_count": _REQUEST_COORDINATES,
        "current_request_surface_support_log2": 64 * _REQUEST_COORDINATES,
        "full_word_count": parent.full_word_count,
        "proposal_word_count": cp44.proposal_word_count,
        "decision_word_count": cp44.decision_word_count,
        "product_uniform_capsule_support_log2": 64 * parent.full_word_count,
        "fixed_request_source_model_theorem": _FIXED_THEOREM,
        "external_finite_request_law_support_theorem": _EXTERNAL_THEOREM,
        "current_request_surface_capacity_theorem": _CAPACITY_THEOREM,
        "full_product_uniform_source_support_and_fiber_criterion": _FULL_UNIFORM_CRITERION,
        "source_to_output_tv_nonconverse": _NONCONVERSE,
        "source_model_runtime_sha256": _runtime_sha256(),
        "passed": True,
        "certificate_sha256": _ZERO_SHA256,
    }
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        values[name] = True
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        values[name] = False
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    certificate = (
        CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate(
            **values, _construction_token=_CERTIFICATE_TOKEN
        )
    )
    after = _CP45_OWNER_LIVE_BINDING(parent_owner)
    if after is not parent:
        raise ValueError("CP45 certificate identity changed during CP46 certification")
    return certificate


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel:
    """Sealed fixed-request point-source model conditional on a positive event."""

    certificate: CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate
    certificate_sha256: str
    source_model_owner_runtime_identity: int
    model_mode: str
    conditioning_event: str
    run_id: int
    initialization_index: int
    raw_word_domain_size: int
    full_word_count: int
    proposal_word_count: int
    decision_word_count: int
    request_support_size: int
    capsule_support_size_upper_bound: int
    conditional_source_law_formula: str
    conditional_exact_source_tv_formula: str
    cached_descriptor_only: bool
    live_checkpoint45_ancestry_revalidated_for_this_model: bool
    conditional_event_positive_mass_required: bool
    conditional_event_positive_mass_certified: bool
    conditional_capsule_law_instantiated: bool
    fixed_request_point_mass_under_positive_event_derived: bool
    fixed_request_exact_tv_under_positive_event_derived: bool
    degenerate_constant_v_w_factorization_under_positive_event_recorded: bool
    nondegenerate_v_w_independence_certified: bool
    request_executed: bool
    capsule_value_materialized: bool
    cross_call_freshness_certified: bool
    physical_randomness_certified: bool
    semantic_output_tv_lower_bound_certified: bool
    source_model_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP46 fixed-request models cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _FIXED_MODEL_TOKEN:
            raise TypeError("CP46 fixed-request models are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP46 fixed-request model fields are incomplete")
        _validate_fixed_model_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP46 fixed-request models are not pickleable")


def _fixed_model_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel.__annotations__
    )


def _fixed_model_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: values[name]
        for name in _fixed_model_fields()
        if name not in ("certificate", "source_model_sha256")
    }


def _fixed_model_summary(
    certificate: CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate,
    owner_identity: int,
    conditioning_event: object,
    run_id: object,
    initialization_index: object,
) -> Mapping[str, object]:
    event = _conditioning_event(conditioning_event)
    run = _exact_uint64(run_id, name="run_id")
    initialization = _exact_uint64(initialization_index, name="initialization_index")
    length = certificate.full_word_count
    return {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "source_model_owner_runtime_identity": owner_identity,
        "model_mode": _FIXED_MODE,
        "conditioning_event": event,
        "run_id": run,
        "initialization_index": initialization,
        "raw_word_domain_size": _D,
        "full_word_count": length,
        "proposal_word_count": certificate.proposal_word_count,
        "decision_word_count": certificate.decision_word_count,
        "request_support_size": 1,
        "capsule_support_size_upper_bound": 1,
        "conditional_source_law_formula": (
            "if-P(%s)>0-then-nu_%s=Dirac-at-symbolic-capsule-for-request-(%d,%d)"
            % (event, event, run, initialization)
        ),
        "conditional_exact_source_tv_formula": (
            "if-P(%s)>0-then-TV(nu_%s,U_L)=1-2^(-64*%d)" % (event, event, length)
        ),
        "cached_descriptor_only": True,
        "live_checkpoint45_ancestry_revalidated_for_this_model": False,
        "conditional_event_positive_mass_required": True,
        "conditional_event_positive_mass_certified": False,
        "conditional_capsule_law_instantiated": False,
        "fixed_request_point_mass_under_positive_event_derived": True,
        "fixed_request_exact_tv_under_positive_event_derived": True,
        "degenerate_constant_v_w_factorization_under_positive_event_recorded": True,
        "nondegenerate_v_w_independence_certified": False,
        "request_executed": False,
        "capsule_value_materialized": False,
        "cross_call_freshness_certified": False,
        "physical_randomness_certified": False,
        "semantic_output_tv_lower_bound_certified": False,
    }


def _validate_fixed_model_values(values: Mapping[str, object]) -> None:
    if set(values) != set(_fixed_model_fields()):
        raise TypeError("CP46 fixed-request model mapping is incomplete")
    if (
        type(values["certificate"])
        is not CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate
    ):
        raise TypeError("fixed model certificate has the wrong exact type")
    for name in (
        "source_model_owner_runtime_identity",
        "run_id",
        "initialization_index",
        "raw_word_domain_size",
        "full_word_count",
        "proposal_word_count",
        "decision_word_count",
        "request_support_size",
        "capsule_support_size_upper_bound",
    ):
        if type(values[name]) is not int:
            raise TypeError("fixed model field %s must be an exact integer" % name)
    for name in (
        "model_mode",
        "conditioning_event",
        "conditional_source_law_formula",
        "conditional_exact_source_tv_formula",
    ):
        if type(values[name]) is not str:
            raise TypeError("fixed model field %s must be exact text" % name)
    for name in (
        "cached_descriptor_only",
        "live_checkpoint45_ancestry_revalidated_for_this_model",
        "conditional_event_positive_mass_required",
        "conditional_event_positive_mass_certified",
        "conditional_capsule_law_instantiated",
        "fixed_request_point_mass_under_positive_event_derived",
        "fixed_request_exact_tv_under_positive_event_derived",
        "degenerate_constant_v_w_factorization_under_positive_event_recorded",
        "nondegenerate_v_w_independence_certified",
        "request_executed",
        "capsule_value_materialized",
        "cross_call_freshness_certified",
        "physical_randomness_certified",
        "semantic_output_tv_lower_bound_certified",
    ):
        if type(values[name]) is not bool:
            raise TypeError("fixed model field %s must be an exact bool" % name)
    _require_sha256(values["certificate_sha256"], name="fixed_model.certificate_sha256")
    _require_sha256(
        values["source_model_sha256"], name="fixed_model.source_model_sha256"
    )
    certificate = _validate_certificate(values["certificate"])
    owner_identity = values["source_model_owner_runtime_identity"]
    expected = _fixed_model_summary(
        certificate,
        owner_identity,
        values["conditioning_event"],
        values["run_id"],
        values["initialization_index"],
    )
    for name, wanted in expected.items():
        actual = values[name]
        if type(wanted) is bool and type(actual) is not bool:
            raise TypeError("fixed model field %s must be an exact bool" % name)
        if type(wanted) is int and type(actual) is not int:
            raise TypeError("fixed model field %s must be an exact integer" % name)
        if type(wanted) is str and type(actual) is not str:
            raise TypeError("fixed model field %s must be exact text" % name)
        if actual is not wanted and actual != wanted:
            raise ValueError("CP46 fixed model field differs: %s" % name)
    if values["source_model_sha256"] != _semantic_digest(_fixed_model_payload(values)):
        raise ValueError("CP46 fixed model digest differs")


def _validate_fixed_model(
    model: object,
) -> CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel:
    if type(model) is not CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel:
        raise TypeError("model has the wrong exact CP46 fixed-request type")
    _validate_fixed_model_values(
        {name: getattr(model, name) for name in _fixed_model_fields()}
    )
    return model


def _make_fixed_model(
    certificate: CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate,
    owner_identity: int,
    conditioning_event: str,
    run_id: int,
    initialization_index: int,
) -> CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel:
    values = dict(
        _fixed_model_summary(
            certificate,
            owner_identity,
            conditioning_event,
            run_id,
            initialization_index,
        )
    )
    values["source_model_sha256"] = _ZERO_SHA256
    values["source_model_sha256"] = _semantic_digest(_fixed_model_payload(values))
    return CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel(
        **values, _construction_token=_FIXED_MODEL_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel:
    """Sealed conditional support model for one declared external request PMF."""

    certificate: CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate
    certificate_sha256: str
    source_model_owner_runtime_identity: int
    declaration: CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration
    declaration_sha256: str
    model_mode: str
    conditioning_event: str
    raw_word_domain_size: int
    full_word_count: int
    proposal_word_count: int
    decision_word_count: int
    declared_request_support_size: int
    declared_mass_denominator: int
    capsule_support_size_upper_bound: int
    product_uniform_capsule_support_log2: int
    uniform_support_mass_upper_bound_numerator: int
    uniform_support_mass_upper_bound_denominator_log2: int
    conditional_source_tv_lower_bound_formula: str
    cached_descriptor_only: bool
    live_checkpoint45_ancestry_revalidated_for_this_model: bool
    conditional_event_positive_mass_required: bool
    conditional_event_positive_mass_certified: bool
    conditional_capsule_law_instantiated: bool
    conditional_support_bound_under_positive_event_derived: bool
    success_value_independence_required: bool
    exact_external_request_law_declared: bool
    external_request_law_realization_certified: bool
    request_sampling_defined: bool
    strict_product_uniform_capsule_obstruction_under_positive_event: bool
    full_capsule_product_uniformity_certified: bool
    nondegenerate_v_w_independence_certified: bool
    numeric_event_probability_certified: bool
    unconditional_capsule_law_certified: bool
    physical_randomness_certified: bool
    cross_call_freshness_certified: bool
    semantic_output_tv_lower_bound_certified: bool
    source_model_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP46 external request-law models cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _EXTERNAL_MODEL_TOKEN:
            raise TypeError("CP46 external request-law models are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("CP46 external request-law model fields are incomplete")
        _validate_external_model_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP46 external request-law models are not pickleable")


def _external_model_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel.__annotations__
    )


def _external_model_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: values[name]
        for name in _external_model_fields()
        if name not in ("certificate", "declaration", "source_model_sha256")
    }


def _external_model_summary(
    certificate: CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate,
    owner_identity: int,
    declaration: CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration,
    conditioning_event: object,
) -> Mapping[str, object]:
    checked_declaration = _validate_declaration(declaration)
    event = _conditioning_event(conditioning_event)
    support = checked_declaration.support_size
    denominator_log2 = certificate.product_uniform_capsule_support_log2
    formula = "1-%d/2^(%d)" % (support, denominator_log2)
    return {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "source_model_owner_runtime_identity": owner_identity,
        "declaration": checked_declaration,
        "declaration_sha256": checked_declaration.declaration_sha256,
        "model_mode": _EXTERNAL_MODE,
        "conditioning_event": event,
        "raw_word_domain_size": _D,
        "full_word_count": certificate.full_word_count,
        "proposal_word_count": certificate.proposal_word_count,
        "decision_word_count": certificate.decision_word_count,
        "declared_request_support_size": support,
        "declared_mass_denominator": checked_declaration.mass_denominator,
        "capsule_support_size_upper_bound": support,
        "product_uniform_capsule_support_log2": denominator_log2,
        "uniform_support_mass_upper_bound_numerator": support,
        "uniform_support_mass_upper_bound_denominator_log2": denominator_log2,
        "conditional_source_tv_lower_bound_formula": (
            "if-P(%s)>0-then-TV(nu_%s,U_L)>=%s" % (event, event, formula)
        ),
        "cached_descriptor_only": True,
        "live_checkpoint45_ancestry_revalidated_for_this_model": False,
        "conditional_event_positive_mass_required": True,
        "conditional_event_positive_mass_certified": False,
        "conditional_capsule_law_instantiated": False,
        "conditional_support_bound_under_positive_event_derived": True,
        "success_value_independence_required": False,
        "exact_external_request_law_declared": True,
        "external_request_law_realization_certified": False,
        "request_sampling_defined": False,
        "strict_product_uniform_capsule_obstruction_under_positive_event": True,
        "full_capsule_product_uniformity_certified": False,
        "nondegenerate_v_w_independence_certified": False,
        "numeric_event_probability_certified": False,
        "unconditional_capsule_law_certified": False,
        "physical_randomness_certified": False,
        "cross_call_freshness_certified": False,
        "semantic_output_tv_lower_bound_certified": False,
    }


def _validate_external_model_values(values: Mapping[str, object]) -> None:
    if set(values) != set(_external_model_fields()):
        raise TypeError("CP46 external model mapping is incomplete")
    if (
        type(values["certificate"])
        is not CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate
    ):
        raise TypeError("external model certificate has the wrong exact type")
    if (
        type(values["declaration"])
        is not CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration
    ):
        raise TypeError("external model declaration has the wrong exact type")
    for name in (
        "source_model_owner_runtime_identity",
        "raw_word_domain_size",
        "full_word_count",
        "proposal_word_count",
        "decision_word_count",
        "declared_request_support_size",
        "declared_mass_denominator",
        "capsule_support_size_upper_bound",
        "product_uniform_capsule_support_log2",
        "uniform_support_mass_upper_bound_numerator",
        "uniform_support_mass_upper_bound_denominator_log2",
    ):
        if type(values[name]) is not int:
            raise TypeError("external model field %s must be an exact integer" % name)
    for name in (
        "model_mode",
        "conditioning_event",
        "conditional_source_tv_lower_bound_formula",
    ):
        if type(values[name]) is not str:
            raise TypeError("external model field %s must be exact text" % name)
    for name in (
        "cached_descriptor_only",
        "live_checkpoint45_ancestry_revalidated_for_this_model",
        "conditional_event_positive_mass_required",
        "conditional_event_positive_mass_certified",
        "conditional_capsule_law_instantiated",
        "conditional_support_bound_under_positive_event_derived",
        "success_value_independence_required",
        "exact_external_request_law_declared",
        "external_request_law_realization_certified",
        "request_sampling_defined",
        "strict_product_uniform_capsule_obstruction_under_positive_event",
        "full_capsule_product_uniformity_certified",
        "nondegenerate_v_w_independence_certified",
        "numeric_event_probability_certified",
        "unconditional_capsule_law_certified",
        "physical_randomness_certified",
        "cross_call_freshness_certified",
        "semantic_output_tv_lower_bound_certified",
    ):
        if type(values[name]) is not bool:
            raise TypeError("external model field %s must be an exact bool" % name)
    for name in (
        "certificate_sha256",
        "declaration_sha256",
        "source_model_sha256",
    ):
        _require_sha256(values[name], name="external_model." + name)
    declaration = _validate_declaration(values["declaration"])
    certificate = _validate_certificate(values["certificate"])
    owner_identity = values["source_model_owner_runtime_identity"]
    expected = _external_model_summary(
        certificate,
        owner_identity,
        declaration,
        values["conditioning_event"],
    )
    for name, wanted in expected.items():
        actual = values[name]
        if type(wanted) is bool and type(actual) is not bool:
            raise TypeError("external model field %s must be an exact bool" % name)
        if type(wanted) is int and type(actual) is not int:
            raise TypeError("external model field %s must be an exact integer" % name)
        if type(wanted) is str and type(actual) is not str:
            raise TypeError("external model field %s must be exact text" % name)
        if actual is not wanted and actual != wanted:
            raise ValueError("CP46 external model field differs: %s" % name)
    if values["source_model_sha256"] != _semantic_digest(
        _external_model_payload(values)
    ):
        raise ValueError("CP46 external model digest differs")


def _validate_external_model(
    model: object,
) -> CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel:
    if (
        type(model)
        is not CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel
    ):
        raise TypeError("model has the wrong exact CP46 external-law type")
    _validate_external_model_values(
        {name: getattr(model, name) for name in _external_model_fields()}
    )
    return model


def _make_external_model(
    certificate: CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate,
    owner_identity: int,
    declaration: CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration,
    conditioning_event: str,
) -> CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel:
    values = dict(
        _external_model_summary(
            certificate, owner_identity, declaration, conditioning_event
        )
    )
    values["source_model_sha256"] = _ZERO_SHA256
    values["source_model_sha256"] = _semantic_digest(_external_model_payload(values))
    return CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel(
        **values, _construction_token=_EXTERNAL_MODEL_TOKEN
    )


_FROZEN_LOCAL_SURFACES = (
    ("_GCD", _GCD),
    ("_JSON_DUMPS", _JSON_DUMPS),
    ("_SHA256", _SHA256),
    ("_PYTHON_VERSION", _PYTHON_VERSION),
    ("_PYTHON_IMPLEMENTATION", _PYTHON_IMPLEMENTATION),
    ("_obstruction", _obstruction),
    ("_CP45_OWNER_TYPE", _CP45_OWNER_TYPE),
    ("_CP45_CERT_TYPE", _CP45_CERT_TYPE),
    ("_CP45_VALIDATE_CERTIFICATE", _CP45_VALIDATE_CERTIFICATE),
    ("_CP45_OWNER_LIVE_BINDING", _CP45_OWNER_LIVE_BINDING),
    (
        "_CP45_REQUIRE_DEPENDENCY_SURFACES",
        _CP45_REQUIRE_DEPENDENCY_SURFACES,
    ),
    ("_CP45_REQUIRE_LOCAL_SURFACES", _CP45_REQUIRE_LOCAL_SURFACES),
    ("_CP45_CERTIFICATE_PROPERTY", _CP45_CERTIFICATE_PROPERTY),
    ("_SCHEMA_VERSION", _SCHEMA_VERSION),
    ("_POLICY", _POLICY),
    ("_SCOPE", _SCOPE),
    ("_FIXED_THEOREM", _FIXED_THEOREM),
    ("_EXTERNAL_THEOREM", _EXTERNAL_THEOREM),
    ("_CAPACITY_THEOREM", _CAPACITY_THEOREM),
    ("_FULL_UNIFORM_CRITERION", _FULL_UNIFORM_CRITERION),
    ("_NONCONVERSE", _NONCONVERSE),
    ("_D", _D),
    ("_REQUEST_COORDINATES", _REQUEST_COORDINATES),
    ("_MAX_SUPPORT", _MAX_SUPPORT),
    ("_MAX_INTEGER_BITS", _MAX_INTEGER_BITS),
    ("_DECLARATION_SCOPE", _DECLARATION_SCOPE),
    ("_FIXED_MODE", _FIXED_MODE),
    ("_EXTERNAL_MODE", _EXTERNAL_MODE),
    ("_CAPSULE_CONDITIONING", _CAPSULE_CONDITIONING),
    ("_RETURN_CONDITIONING", _RETURN_CONDITIONING),
    ("_CONDITIONING_EVENTS", _CONDITIONING_EVENTS),
    ("_ZERO_SHA256", _ZERO_SHA256),
    ("_DECLARATION_TOKEN", _DECLARATION_TOKEN),
    ("_CERTIFICATE_TOKEN", _CERTIFICATE_TOKEN),
    ("_FIXED_MODEL_TOKEN", _FIXED_MODEL_TOKEN),
    ("_EXTERNAL_MODEL_TOKEN", _EXTERNAL_MODEL_TOKEN),
    ("_OWNER_TOKEN", _OWNER_TOKEN),
    ("_CERTIFICATE_POSITIVE_FLAGS", _CERTIFICATE_POSITIVE_FLAGS),
    ("_CERTIFICATE_NEGATIVE_FLAGS", _CERTIFICATE_NEGATIVE_FLAGS),
    ("_CERTIFICATE_TEXT_FIELDS", _CERTIFICATE_TEXT_FIELDS),
    ("_CERTIFICATE_SHA256_FIELDS", _CERTIFICATE_SHA256_FIELDS),
    ("_CERTIFICATE_INTEGER_FIELDS", _CERTIFICATE_INTEGER_FIELDS),
    ("_canonical", _canonical),
    ("_semantic_digest", _semantic_digest),
    ("_require_sha256", _require_sha256),
    ("_exact_nonnegative_integer", _exact_nonnegative_integer),
    ("_exact_uint64", _exact_uint64),
    ("_bounded_positive_integer", _bounded_positive_integer),
    ("_exact_bool", _exact_bool),
    ("_conditioning_event", _conditioning_event),
    ("_runtime_sha256", _runtime_sha256),
    ("_preflight_request_mass_rows", _preflight_request_mass_rows),
    ("_declaration_summary", _declaration_summary),
    ("_declaration_fields", _declaration_fields),
    ("_declaration_payload", _declaration_payload),
    ("_validate_declaration_values", _validate_declaration_values),
    ("_validate_declaration", _validate_declaration),
    ("_make_declaration", _make_declaration),
    ("_certificate_fields", _certificate_fields),
    ("_certificate_payload", _certificate_payload),
    ("_validate_parent_claims", _validate_parent_claims),
    ("_validate_certificate_values", _validate_certificate_values),
    ("_validate_certificate", _validate_certificate),
    ("_make_certificate", _make_certificate),
    ("_fixed_model_fields", _fixed_model_fields),
    ("_fixed_model_payload", _fixed_model_payload),
    ("_fixed_model_summary", _fixed_model_summary),
    ("_validate_fixed_model_values", _validate_fixed_model_values),
    ("_validate_fixed_model", _validate_fixed_model),
    ("_make_fixed_model", _make_fixed_model),
    ("_external_model_fields", _external_model_fields),
    ("_external_model_payload", _external_model_payload),
    ("_external_model_summary", _external_model_summary),
    ("_validate_external_model_values", _validate_external_model_values),
    ("_validate_external_model", _validate_external_model),
    ("_make_external_model", _make_external_model),
    (
        "CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration",
        CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration,
    ),
    (
        "CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate",
        CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate,
    ),
    (
        "CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel",
        CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel,
    ),
    (
        "CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel",
        CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel,
    ),
)


def _require_local_surfaces(
    dependency_guard: object = _require_dependency_surfaces,
    frozen: Tuple[Tuple[str, object], ...] = _FROZEN_LOCAL_SURFACES,
) -> None:
    """Refuse CP46-local substitution before invoking a protected helper."""

    namespace = globals()
    if namespace.get("_require_dependency_surfaces") is not dependency_guard:
        raise ValueError("CP46 dependency guard changed")
    if namespace.get("_FROZEN_LOCAL_SURFACES") is not frozen:
        raise ValueError("CP46 frozen local surfaces changed")
    for name, expected in frozen:
        if namespace.get(name) is not expected:
            raise ValueError("CP46 local surface changed: %s" % name)
    dependency_guard()


_LOCAL_SURFACE_GUARD = _require_local_surfaces


class CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner:
    """Immutable owner of the operation-free CP46 source-model descriptors."""

    __slots__ = (
        "_source_support_owner",
        "_source_support_owner_identity",
        "_certificate",
        "_certificate_identity",
        "_local_surface_guard",
        "_local_surface_guard_identity",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP46 owners cannot be subclassed")

    def __init__(
        self,
        parent: _CP45_OWNER_TYPE,
        certificate: CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("CP46 owners require certification")
        if type(parent) is not _CP45_OWNER_TYPE:
            raise TypeError("source_support_owner has the wrong exact type")
        _LOCAL_SURFACE_GUARD()
        checked = _validate_certificate(certificate)
        if checked.checkpoint45_certificate is not parent.certificate:
            raise ValueError("CP46 certificate belongs to another CP45 owner")
        if checked.checkpoint45_owner_runtime_identity != id(parent):
            raise ValueError("CP46 certificate has another CP45 owner identity")
        object.__setattr__(self, "_source_support_owner", parent)
        object.__setattr__(self, "_source_support_owner_identity", parent)
        object.__setattr__(self, "_certificate", checked)
        object.__setattr__(self, "_certificate_identity", checked)
        object.__setattr__(self, "_local_surface_guard", _LOCAL_SURFACE_GUARD)
        object.__setattr__(self, "_local_surface_guard_identity", _LOCAL_SURFACE_GUARD)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("CP46 owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("CP46 owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP46 owners are not pickleable")

    @property
    def certificate(
        self,
    ) -> CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate:
        return self._certificate

    @property
    def source_support_owner(self) -> _CP45_OWNER_TYPE:
        return self._source_support_owner

    def _require_local_surface_binding(self) -> None:
        guard = self._local_surface_guard
        if guard is not self._local_surface_guard_identity:
            raise ValueError("CP46 local surface guard identity changed")
        namespace = globals()
        if namespace.get("_LOCAL_SURFACE_GUARD") is not guard:
            raise ValueError("CP46 local surface guard binding changed")
        if namespace.get("_require_local_surfaces") is not guard:
            raise ValueError("CP46 local surface guard implementation changed")
        if namespace.get(
            "CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner"
        ) is not type(self):
            raise ValueError("CP46 owner class binding changed")
        guard()

    def _require_cached_binding(
        self,
    ) -> CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate:
        self._require_local_surface_binding()
        if self._source_support_owner is not self._source_support_owner_identity:
            raise ValueError("CP46 parent owner identity changed")
        if self._certificate is not self._certificate_identity:
            raise ValueError("CP46 certificate identity changed")
        if type(self._source_support_owner) is not _CP45_OWNER_TYPE:
            raise TypeError("CP46 parent owner has the wrong exact type")
        if (
            type(self._certificate)
            is not CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate
        ):
            raise TypeError("CP46 certificate has the wrong exact type")
        checked = _validate_certificate(self._certificate)
        if checked.checkpoint45_owner_runtime_identity != id(
            self._source_support_owner
        ):
            raise ValueError("CP46 parent owner runtime identity differs")
        if (
            checked.checkpoint45_certificate
            is not self._source_support_owner.certificate
        ):
            raise ValueError("CP46 live parent certificate identity changed")
        return checked

    def revalidate_live_ancestry(
        self,
    ) -> CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate:
        """Explicitly replay the expensive CP45 live ancestry boundary once."""

        checked = self._require_cached_binding()
        parent = _CP45_OWNER_LIVE_BINDING(self._source_support_owner)
        if parent is not checked.checkpoint45_certificate:
            raise ValueError("CP46 live CP45 certificate identity differs")
        self._require_cached_binding()
        return checked

    def fixed_request_model(
        self,
        run_id: object,
        initialization_index: object,
        *,
        conditioning_event: object,
    ) -> CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel:
        """Describe one fixed request without executing it."""

        self._require_local_surface_binding()
        run = _exact_uint64(run_id, name="run_id")
        initialization = _exact_uint64(
            initialization_index, name="initialization_index"
        )
        event = _conditioning_event(conditioning_event)
        certificate = self._require_cached_binding()
        model = _make_fixed_model(certificate, id(self), event, run, initialization)
        self._require_cached_binding()
        return model

    def external_request_law_model(
        self,
        declaration: object,
        *,
        conditioning_event: object,
    ) -> CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel:
        """Describe one declared finite request law without sampling it."""

        self._require_local_surface_binding()
        if (
            type(declaration)
            is not CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration
        ):
            raise TypeError("declaration has the wrong exact CP46 type")
        checked_declaration = _validate_declaration(declaration)
        event = _conditioning_event(conditioning_event)
        certificate = self._require_cached_binding()
        model = _make_external_model(certificate, id(self), checked_declaration, event)
        self._require_cached_binding()
        return model

    def validate_source_model(self, model: object) -> object:
        """Validate one exact model without replaying CP45 live ancestry."""

        self._require_local_surface_binding()
        model_type = type(model)
        if model_type is CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel:
            if model.certificate is not self._certificate:
                raise ValueError("CP46 source model belongs to another certificate")
            if type(model.source_model_owner_runtime_identity) is not int:
                raise TypeError("CP46 source model owner identity must be exact")
            if model.source_model_owner_runtime_identity != id(self):
                raise ValueError("CP46 source model belongs to another owner")
            checked = _validate_fixed_model(model)
        elif (
            model_type
            is CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel
        ):
            if model.certificate is not self._certificate:
                raise ValueError("CP46 source model belongs to another certificate")
            if type(model.source_model_owner_runtime_identity) is not int:
                raise TypeError("CP46 source model owner identity must be exact")
            if model.source_model_owner_runtime_identity != id(self):
                raise ValueError("CP46 source model belongs to another owner")
            checked = _validate_external_model(model)
        else:
            raise TypeError("model has the wrong exact CP46 type")
        certificate = self._require_cached_binding()
        if checked.certificate is not certificate:
            raise ValueError("CP46 source model certificate changed during validation")
        if checked.source_model_owner_runtime_identity != id(self):
            raise ValueError("CP46 source model owner changed during validation")
        self._require_cached_binding()
        return checked


def declare_plugin_bridge_counter_keyed_initial_tilt_rejection_external_finite_request_law(
    request_mass_rows: object,
    *,
    mass_denominator: object,
) -> CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration:
    """Create one canonical exact finite PMF declaration without sampling."""

    _LOCAL_SURFACE_GUARD()
    return _make_declaration(request_mass_rows, mass_denominator)


def validate_plugin_bridge_counter_keyed_initial_tilt_rejection_external_finite_request_law_declaration(
    declaration: object,
) -> CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration:
    """Validate one exact CP46 request-law declaration."""

    _LOCAL_SURFACE_GUARD()
    return _validate_declaration(declaration)


def certify_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract(
    source_support_owner: _CP45_OWNER_TYPE,
    *,
    source_model_policy: object,
    source_model_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner:
    """Certify the CP45-bound CP46 source-model contract."""

    if type(source_support_owner) is not _CP45_OWNER_TYPE:
        raise TypeError("source_support_owner has the wrong exact type")
    _LOCAL_SURFACE_GUARD()
    if type(source_model_policy) is not str:
        raise TypeError("source_model_policy must be exact text")
    if source_model_policy != _POLICY:
        raise ValueError("only the exported CP46 policy is supported")
    role = _require_sha256(source_model_role_sha256, name="source_model_role_sha256")
    certificate = _make_certificate(source_support_owner, role)
    return CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner(
        source_support_owner,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )


def require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract(
    source_support_owner: _CP45_OWNER_TYPE,
    owner: CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner,
    *,
    source_model_policy: object,
    source_model_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner:
    """Require one exact CP46 owner and explicitly revalidate CP45 ancestry."""

    if (
        type(owner)
        is not CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner
    ):
        raise TypeError("owner has the wrong exact CP46 type")
    if type(source_support_owner) is not _CP45_OWNER_TYPE:
        raise TypeError("source_support_owner has the wrong exact type")
    _LOCAL_SURFACE_GUARD()
    if owner.source_support_owner is not source_support_owner:
        raise ValueError("CP46 owner belongs to another CP45 owner")
    if type(source_model_policy) is not str or source_model_policy != _POLICY:
        raise ValueError("CP46 source-model policy differs")
    role = _require_sha256(source_model_role_sha256, name="source_model_role_sha256")
    checked = owner.revalidate_live_ancestry()
    if checked.source_model_role_sha256 != role:
        raise ValueError("CP46 source-model role differs")
    return owner


def validate_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract_certificate(
    source_support_owner: _CP45_OWNER_TYPE,
    owner: CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner,
    *,
    source_model_policy: object,
    source_model_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate:
    """Validate one CP46 certificate against one exact CP45 owner."""

    matched = require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract(
        source_support_owner,
        owner,
        source_model_policy=source_model_policy,
        source_model_role_sha256=source_model_role_sha256,
    )
    return matched.certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_CONTRACT_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_CONTRACT_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_CONTRACT_SCOPE",
    "INITIAL_TILT_REJECTION_FIXED_REQUEST_SOURCE_MODEL_THEOREM",
    "INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_SUPPORT_THEOREM",
    "INITIAL_TILT_REJECTION_CURRENT_REQUEST_SURFACE_CAPACITY_THEOREM",
    "INITIAL_TILT_REJECTION_FULL_PRODUCT_UNIFORM_SOURCE_SUPPORT_AND_FIBER_CRITERION",
    "INITIAL_TILT_REJECTION_EXTERNAL_SOURCE_TO_OUTPUT_TV_NONCONVERSE",
    "INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_RAW_WORD_DOMAIN_SIZE",
    "INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_REQUEST_COORDINATES",
    "INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MAX_SUPPORT",
    "INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MAX_INTEGER_BITS",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_DECLARATION_SCOPE",
    "INITIAL_TILT_REJECTION_FIXED_REQUEST_MODE",
    "INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MODE",
    "INITIAL_TILT_REJECTION_COMPLETE_CAPSULE_CONDITIONING",
    "INITIAL_TILT_REJECTION_RETURNED_RESULT_CONDITIONING",
    "CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration",
    "CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate",
    "CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel",
    "CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel",
    "CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionExplicitSourceModelContractError",
    "declare_plugin_bridge_counter_keyed_initial_tilt_rejection_external_finite_request_law",
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_external_finite_request_law_declaration",
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract",
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract",
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract_certificate",
]
