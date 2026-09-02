"""Admit CP39 selected states against an explicit fixed-batch target.

Checkpoint thirty-nine returns either one fully coordinated selected initial
state or bounded exhaustion.  This additive successor names the exact
checkpoint-thirty-eight finite-resolution law, conditional on its direct
word-free fixed batch ``B``, as the operational target and applies one generic
downstream initial-state admission boundary.

For decision quotas ``K_a``, ``D = 2**64``, and fixed candidates ``x_a``, the
augmented target is

``T_B(exhausted) = product_a (1 - K_a / D)``

and

``T_B(x) = sum_{a:x_a=x} (K_a / D) product_{b<a} (1 - K_b / D)``.

When ``Z_B = 1 - T_B(exhausted)`` is positive, the state target is the exact
selected-conditioned law ``T_B(x) / Z_B``.  The module also records the
conditioning-stability comparison obtained from CP38's strict augmented
bound: the raw strict rational upper bound is ``2 A / (D Z_B)``, the reported
probability-distance upper bound is the non-strict clipping of that rational
at one, and that clipped display bound is nonvacuous exactly when the raw
rational is strictly below one.  At equality the raw strict theorem remains
informative even though the clipped non-strict display is vacuous.  All
optional raw and clipped bound values are absent when ``Z_B`` is zero, and
their definition, strictness, and nonvacuity flags are false.

This target is conditional on one successfully materialized CP36 batch and on
CP38's abstract iid decision-word premise.  It is not the live Philox output
law, an unconditional CP36 batch law, exact ideal rejection, or the normalized
global plug-in tilted law.

The owner accepts one exact CP39 owner and no caller target, RNG, word, state,
manifest, or ancestry component.  ``admit`` invokes CP39 ``coordinate`` once.
A selected state, including the selected empty state, is admitted while
preserving the exact CP39 configuration, intensity, lineage, and occurrence
payload identities.  Bounded exhaustion is a valid returned no-state status.
An operational or validation failure raises and returns no CP40 result; it is
never relabelled as exhaustion.  Validation never coordinates, resolves,
bootstraps, consumes words, or constructs target/result children.

Hashes and runtime identities are same-process procedural custody witnesses
under a trusted unchanged runtime.  They are not cryptographic authentication,
loaded-code integrity evidence, or cross-runtime portability guarantees.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

try:
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_initial_tilt_rejection_lineage_tag3_coordination,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "finite-resolution rejection admission requires the optional "
            "PyTorch reference dependency; install the 'reference' extra"
        ) from error
    raise

_coord = plugin_bridge_counter_keyed_initial_tilt_rejection_lineage_tag3_coordination


PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-admission-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_POLICY = (
    "exact-checkpoint39-owner-and-transitive-checkpoint38-binding;"
    "one-parent-coordinate;fixed-B-augmented-dyadic-target;"
    "selected-conditioned-state-target-when-selection-mass-positive;"
    "raw-strict-conditioned-comparison-2A-over-2^64-Z;"
    "clipped-nonstrict-conditioned-comparison-min-one;"
    "selected-including-empty-operational-state-admission;"
    "bounded-exhaustion-valid-no-state;operational-failure-no-result;"
    "exact-selected-state-and-target-mass-row-custody;"
    "no-caller-target-rng-word-ancestry-retry-fallback-or-rollback-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_SCOPE = (
    "fixed-successful-batch-finite-resolution-operational-target-and-state-"
    "admission;abstract-iid-decision-word-premise-only;"
    "duplicate-aggregated-target-masses-and-exact-selected-object-custody;"
    "not-live-word-source-or-initializer-distribution-law;"
    "not-unconditional-cp36-batch-law-or-failure-probability;"
    "not-exact-ideal-rejection-or-normalized-global-tilted-law;"
    "not-all-strategy-general-initializer-or-formal-test28-closure;"
    "not-tag3-payload-semantics-brownian-drift-path-liveness-or-sampler;"
    "not-scientific-model-quality-generality-or-manuscript-evidence;"
    "trusted-runtime-procedural-not-portable-or-cryptographic-custody"
)

INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_FAMILY = (
    "checkpoint38-fixed-B-augmented-dyadic-with-selected-conditioned-state-law-v1"
)
INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_CONDITIONING = (
    "direct-word-free-attempt-index-configuration-score-gap-and-quota-B"
)
INITIAL_TILT_REJECTION_FINITE_RESOLUTION_ADMISSION_STATUSES = (
    "admitted",
    "exhausted",
)
INITIAL_TILT_REJECTION_FINITE_RESOLUTION_CONDITIONED_COMPARISON = (
    "if-Z_B>0-then-TV-selected-ideal-vs-dyadic-is-strictly-less-than-"
    "2A/(2^64*Z_B);reported-nonstrict-upper-is-min(1,2A/(2^64*Z_B));"
    "clipped-nonstrict-bound-nonvacuous-iff-2A/(2^64*Z_B)<1;raw-strict-"
    "theorem-remains-informative-when-the-raw-bound-equals-one"
)
INITIAL_TILT_REJECTION_FINITE_RESOLUTION_CONDITIONED_COMPARISON_PROOF = (
    "with-p_j=K_j/2^64-and-r_j=exp(delta_j),conservative-quotas-give-"
    "p_j<=r_j-and-therefore-ideal-selection-mass-Z_B^*>=dyadic-selection-"
    "mass-Z_B;conditioning-stability-gives-TV(P_sel,Q_sel)<=2*TV(P_aug,"
    "Q_aug)/min(Z_B^*,Z_B);CP38-gives-TV(P_aug,Q_aug)<A/2^64;therefore-"
    "if-Z_B>0-TV(P_sel,Q_sel)<2A/(2^64*Z_B)"
)

_SCHEMA_VERSION = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_SCHEMA_VERSION
)
_POLICY = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_POLICY
_SCOPE = PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_SCOPE
_TARGET_FAMILY = INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_FAMILY
_TARGET_CONDITIONING = INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_CONDITIONING
_COMPARISON = INITIAL_TILT_REJECTION_FINITE_RESOLUTION_CONDITIONED_COMPARISON
_COMPARISON_PROOF = (
    INITIAL_TILT_REJECTION_FINITE_RESOLUTION_CONDITIONED_COMPARISON_PROOF
)
_STATUSES = INITIAL_TILT_REJECTION_FINITE_RESOLUTION_ADMISSION_STATUSES
_ZERO_SHA256 = "0" * 64
_MAX_UINT64 = (1 << 64) - 1
_MAX_TEXT_LENGTH = 16_384

_CERTIFICATE_TOKEN = object()
_TARGET_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()

# CP39 is the only direct parent.  CP38 types and validators are reached only
# through CP39's frozen transitive module ancestry; no CP38 owner is accepted by
# any public CP40 surface.
_law = _coord._law
_CP39_OWNER_TYPE = getattr(
    _coord,
    "CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner",
)
_CP39_CERT_TYPE = (
    _coord.CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
)
_CP39_RESULT_TYPE = getattr(
    _coord,
    "CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult",
)
_CP39_OWNER_SNAPSHOT = _CP39_OWNER_TYPE._owner_snapshot
_CP39_REQUIRE_OWNER_SNAPSHOT = _CP39_OWNER_TYPE._require_owner_snapshot
_CP39_LIVE_CERTIFICATE = _CP39_OWNER_TYPE._live_certificate
_CP39_COORDINATE = _CP39_OWNER_TYPE.coordinate
_CP39_VALIDATE_RESULT = _CP39_OWNER_TYPE.validate_result
_CP39_CERTIFICATE_PROPERTY = _CP39_OWNER_TYPE.certificate
_CP39_PARENT_PROPERTY = _CP39_OWNER_TYPE.finite_batch_law_owner
_CP39_VALIDATE_CERTIFICATE = _coord._validate_certificate
_CP39_CERTIFICATE_FIELDS = _coord._certificate_fields
_CP39_PREFLIGHT_RESULT = _coord._preflight_result_record
_CP39_RESULT_FIELDS = _coord._result_fields
_CP39_RESULT_TREE_SNAPSHOT = _coord._result_tree_snapshot
_CP39_REQUIRE_RESULT_TREE_UNCHANGED = _coord._require_result_tree_unchanged
_CP39_SURFACE_GUARD = _coord._require_operation_surfaces

_CP38_OWNER_TYPE = _law.CounterKeyedInitialTiltRejectionFiniteBatchLawOwner
_CP38_CERT_TYPE = _law.CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate
_CP38_RESULT_TYPE = _law.CounterKeyedInitialTiltRejectionFiniteBatchLawResult
_CP38_CONFIGURATION_MASS_TYPE = getattr(
    _law,
    "CounterKeyedInitialTiltRejectionConfigurationMass",
)
_CP38_CERTIFICATE_PROPERTY = _CP38_OWNER_TYPE.certificate
_CP38_VALIDATE_CERTIFICATE = _law._validate_certificate
_CP38_PREFLIGHT_RESULT = _law._preflight_result_record
_CP38_RESULT_FIELDS = _law._result_fields
_CP38_CONFIGURATION_MASS_FIELDS = _law._configuration_mass_fields
_CP38_RESULT_TREE_SNAPSHOT = _law._result_tree_snapshot
_CP38_REQUIRE_RESULT_TREE_UNCHANGED = _law._require_result_tree_unchanged
_CP38_FRACTION_PARTS = _law._fraction_parts
_CP38_DYADIC_DENOMINATOR = (
    _law.INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_DYADIC_DENOMINATOR
)
_CP38_FIXED_BATCH_OUTCOME_THEOREM = (
    _law.INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_OUTCOME_THEOREM
)
_CP38_FIXED_BATCH_CONFIGURATION_THEOREM = (
    _law.INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_CONFIGURATION_THEOREM
)
_CP38_AUGMENTED_IDEAL_TV_THEOREM = (
    _law.INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_AUGMENTED_IDEAL_TV_THEOREM
)
_CP38_WORD_SOURCE_PREMISE = _law.FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE
_CP38_MAX_ATTEMPTS = _law.INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_ATTEMPTS
_CP38_MAX_EVENTS = getattr(
    _law,
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_CONFIGURATION_EVENTS",
)
_CP38_MAX_COORDINATES = (
    _law.INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_COORDINATES_PER_EVENT
)

INITIAL_TILT_REJECTION_FINITE_RESOLUTION_DYADIC_DENOMINATOR = getattr(
    _law,
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_DYADIC_DENOMINATOR",
)
INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_ATTEMPTS = _CP38_MAX_ATTEMPTS
INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TARGET_CONFIGURATIONS = getattr(
    _law,
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_ATTEMPTS",
)
INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_CONFIGURATION_EVENTS = getattr(
    _law,
    "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_CONFIGURATION_EVENTS",
)
INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_COORDINATES_PER_EVENT = (
    _CP38_MAX_COORDINATES
)
INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_STREAM_RECORDS = (
    _coord.INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_STREAM_RECORDS
)
INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_RAW64_WORDS_PER_OCCURRENCE = (
    _coord.INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE
)
INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TOTAL_RAW64_WORDS = (
    _coord.INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_TOTAL_RAW64_WORDS
)

_SEMANTIC_DIGEST = _coord._SEMANTIC_DIGEST
_REQUIRE_SHA256 = _coord._require_sha256
_RECORD_SNAPSHOT = _coord._record_snapshot
_REQUIRE_RECORD_UNCHANGED = _coord._require_record_unchanged


class PluginBridgeCounterKeyedInitialTiltRejectionAdmissionError(ArithmeticError):
    """Fail-closed checkpoint-forty target/admission error."""


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    omitted = set(names)
    return {name: value for name, value in values.items() if name not in omitted}


def _require_text(value: object, expected: str, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) > _MAX_TEXT_LENGTH:
        raise ValueError("%s exceeds the text resource limit" % name)
    if value != expected:
        raise ValueError("%s differs from the exported value" % name)
    return value


def _exact_bool(value: object, expected: bool, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be an exact Boolean" % name)
    if value is not expected:
        raise ValueError("%s must remain %s" % (name, expected))
    return value


def _exact_integer(
    value: object,
    *,
    name: str,
    minimum: int = 0,
    maximum: int = _MAX_UINT64,
) -> int:
    if type(value) is not int:
        raise TypeError("%s must be an exact Python integer" % name)
    if not minimum <= value <= maximum:
        raise ValueError("%s is outside its frozen bound" % name)
    return value


def _exact_tuple(
    value: object,
    *,
    name: str,
    maximum: int,
    length: Optional[int] = None,
) -> Tuple[object, ...]:
    if type(value) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(value) > maximum:
        raise ValueError("%s exceeds its resource bound" % name)
    if length is not None and len(value) != length:
        raise ValueError("%s has the wrong length" % name)
    return value


def _fraction_parts(
    numerator: object,
    denominator: object,
    *,
    name: str,
) -> Fraction:
    return _CP38_FRACTION_PARTS(numerator, denominator, name=name)


def _optional_fraction_parts(
    numerator: object,
    denominator: object,
    *,
    defined: bool,
    name: str,
) -> Optional[Fraction]:
    if defined:
        return _fraction_parts(numerator, denominator, name=name)
    if numerator is not None or denominator is not None:
        raise ValueError("%s must be absent when undefined" % name)
    return None


def _runtime_sha256() -> str:
    if (
        _CP38_DYADIC_DENOMINATOR != 1 << 64
        or _CP38_MAX_ATTEMPTS != 64
        or INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_STREAM_RECORDS != 64
        or INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TOTAL_RAW64_WORDS != 65_536
    ):
        raise ValueError("finite-resolution admission resource constants changed")
    return _SEMANTIC_DIGEST(
        {
            "domain": "initial-tilt-rejection-admission-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "target_family": _TARGET_FAMILY,
            "target_conditioning": _TARGET_CONDITIONING,
            "comparison": _COMPARISON,
            "comparison_proof": _COMPARISON_PROOF,
            "checkpoint38_fixed_batch_outcome_theorem": (
                _CP38_FIXED_BATCH_OUTCOME_THEOREM
            ),
            "checkpoint38_fixed_batch_configuration_theorem": (
                _CP38_FIXED_BATCH_CONFIGURATION_THEOREM
            ),
            "checkpoint38_augmented_ideal_tv_theorem": (
                _CP38_AUGMENTED_IDEAL_TV_THEOREM
            ),
            "checkpoint38_word_source_premise": _CP38_WORD_SOURCE_PREMISE,
            "dyadic_denominator": _CP38_DYADIC_DENOMINATOR,
            "maximum_attempts": _CP38_MAX_ATTEMPTS,
            "maximum_events": _CP38_MAX_EVENTS,
            "maximum_coordinates": _CP38_MAX_COORDINATES,
            "maximum_stream_records": (
                INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_STREAM_RECORDS
            ),
            "maximum_words_per_occurrence": (
                INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_RAW64_WORDS_PER_OCCURRENCE
            ),
            "maximum_total_words": (
                INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TOTAL_RAW64_WORDS
            ),
            "policy": _POLICY,
            "scope": _SCOPE,
        }
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "checkpoint39_certificate",
        "checkpoint38_certificate",
        "certificate_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionAdmissionCertificate:
    """Sealed exact-CP39 fixed-batch target/admission certificate."""

    schema_version: str
    certificate_scope: str
    admission_policy: str
    admission_role_sha256: str
    checkpoint39_certificate: _CP39_CERT_TYPE
    checkpoint39_certificate_sha256: str
    checkpoint39_runtime_sha256: str
    checkpoint39_owner_runtime_identity: int
    checkpoint38_certificate: _CP38_CERT_TYPE
    checkpoint38_certificate_sha256: str
    checkpoint38_word_law_hypothesis_sha256: str
    checkpoint38_word_source_premise: str
    checkpoint38_fixed_batch_outcome_theorem: str
    checkpoint38_fixed_batch_configuration_theorem: str
    checkpoint38_augmented_ideal_tv_theorem: str
    target_family: str
    target_conditioning: str
    conditioned_comparison: str
    conditioned_comparison_proof: str
    dyadic_denominator: int
    maximum_attempts: int
    maximum_target_configurations: int
    maximum_configuration_events: int
    maximum_coordinates_per_event: int
    maximum_stream_records: int
    maximum_raw64_words_per_occurrence: int
    maximum_total_raw64_words: int
    admission_runtime_sha256: str
    exact_checkpoint39_owner_binding_certified: bool
    transitive_checkpoint38_binding_certified: bool
    exactly_one_parent_coordinate_call_certified: bool
    fixed_batch_augmented_target_certified: bool
    selected_conditioned_target_when_positive_certified: bool
    conditioned_comparison_formula_certified: bool
    comparison_uses_separate_independent_coordinate_sequences_certified: bool
    comparison_uses_common_continuous_uniform_coupling_certified: bool
    abstract_words_iid_uniform_and_independent_of_word_free_batch_certified: bool
    conservative_quota_selection_mass_order_certified: bool
    conditioning_stability_inequality_certified: bool
    target_record_and_word_free_law_digests_distinguished_certified: bool
    selected_and_selected_empty_structural_state_admission_certified: bool
    exhaustion_valid_no_state_certified: bool
    operational_failure_no_result_certified: bool
    exact_selected_state_identity_preservation_certified: bool
    target_mass_row_by_ordinal_certified: bool
    no_caller_target_rng_word_or_ancestry_certified: bool
    no_retry_fallback_or_rollback_certified: bool
    validation_without_coordinate_or_child_construction_certified: bool
    generic_initial_state_structural_admission_boundary_certified: bool
    live_word_source_law_certified: bool
    live_initializer_distribution_certified: bool
    unconditional_checkpoint36_batch_law_certified: bool
    exact_ideal_rejection_certified: bool
    normalized_global_tilted_law_certified: bool
    all_strategy_general_initializer_certified: bool
    formal_test28_closed: bool
    tag3_payload_semantics_certified: bool
    brownian_stream_consumption_certified: bool
    continuous_drift_admissible: bool
    path_admissible: bool
    full_sampler_admissible: bool
    sampler_liveness_certified: bool
    scientific_claim_promoted: bool
    model_quality_claim_promoted: bool
    generality_claim_promoted: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("finite-resolution admission certificates cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("finite-resolution admission certificates are sealed")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("finite-resolution admission certificate is incomplete")
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("finite-resolution admission certificates are not pickleable")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionAdmissionCertificate.__annotations__)


_CERTIFICATE_POSITIVE_FLAGS = (
    "exact_checkpoint39_owner_binding_certified",
    "transitive_checkpoint38_binding_certified",
    "exactly_one_parent_coordinate_call_certified",
    "fixed_batch_augmented_target_certified",
    "selected_conditioned_target_when_positive_certified",
    "conditioned_comparison_formula_certified",
    "comparison_uses_separate_independent_coordinate_sequences_certified",
    "comparison_uses_common_continuous_uniform_coupling_certified",
    "abstract_words_iid_uniform_and_independent_of_word_free_batch_certified",
    "conservative_quota_selection_mass_order_certified",
    "conditioning_stability_inequality_certified",
    "target_record_and_word_free_law_digests_distinguished_certified",
    "selected_and_selected_empty_structural_state_admission_certified",
    "exhaustion_valid_no_state_certified",
    "operational_failure_no_result_certified",
    "exact_selected_state_identity_preservation_certified",
    "target_mass_row_by_ordinal_certified",
    "no_caller_target_rng_word_or_ancestry_certified",
    "no_retry_fallback_or_rollback_certified",
    "validation_without_coordinate_or_child_construction_certified",
    "generic_initial_state_structural_admission_boundary_certified",
)
_CERTIFICATE_NEGATIVE_FLAGS = (
    "live_word_source_law_certified",
    "live_initializer_distribution_certified",
    "unconditional_checkpoint36_batch_law_certified",
    "exact_ideal_rejection_certified",
    "normalized_global_tilted_law_certified",
    "all_strategy_general_initializer_certified",
    "formal_test28_closed",
    "tag3_payload_semantics_certified",
    "brownian_stream_consumption_certified",
    "continuous_drift_admissible",
    "path_admissible",
    "full_sampler_admissible",
    "sampler_liveness_certified",
    "scientific_claim_promoted",
    "model_quality_claim_promoted",
    "generality_claim_promoted",
    "runtime_portable",
    "cryptographic_authentication",
)


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    for name, expected in (
        ("schema_version", _SCHEMA_VERSION),
        ("certificate_scope", _SCOPE),
        ("admission_policy", _POLICY),
        ("target_family", _TARGET_FAMILY),
        ("target_conditioning", _TARGET_CONDITIONING),
        ("conditioned_comparison", _COMPARISON),
        ("conditioned_comparison_proof", _COMPARISON_PROOF),
        ("checkpoint38_word_source_premise", _CP38_WORD_SOURCE_PREMISE),
        ("checkpoint38_fixed_batch_outcome_theorem", _CP38_FIXED_BATCH_OUTCOME_THEOREM),
        (
            "checkpoint38_fixed_batch_configuration_theorem",
            _CP38_FIXED_BATCH_CONFIGURATION_THEOREM,
        ),
        (
            "checkpoint38_augmented_ideal_tv_theorem",
            _CP38_AUGMENTED_IDEAL_TV_THEOREM,
        ),
    ):
        _require_text(values[name], expected, name="certificate.%s" % name)
    for name in (
        "admission_role_sha256",
        "checkpoint39_certificate_sha256",
        "checkpoint39_runtime_sha256",
        "checkpoint38_certificate_sha256",
        "checkpoint38_word_law_hypothesis_sha256",
        "admission_runtime_sha256",
        "certificate_sha256",
    ):
        _REQUIRE_SHA256(values[name], name="certificate.%s" % name)
    parent39 = values["checkpoint39_certificate"]
    if type(parent39) is not _CP39_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP39 certificate type")
    checked39 = _CP39_VALIDATE_CERTIFICATE(parent39)
    if checked39 is not parent39:
        raise ValueError("CP39 certificate validation substituted its record")
    if values["checkpoint39_certificate_sha256"] != parent39.certificate_sha256:
        raise ValueError("certificate CP39 digest differs")
    if values["checkpoint39_runtime_sha256"] != parent39.coordination_runtime_sha256:
        raise ValueError("certificate CP39 runtime digest differs")
    parent38 = values["checkpoint38_certificate"]
    if type(parent38) is not _CP38_CERT_TYPE:
        raise TypeError("certificate has the wrong exact CP38 certificate type")
    checked38 = _CP38_VALIDATE_CERTIFICATE(parent38)
    if checked38 is not parent38:
        raise ValueError("CP38 certificate validation substituted its record")
    if parent38 is not parent39.checkpoint38_certificate:
        raise ValueError("certificate lost transitive CP38 identity")
    if values["checkpoint38_certificate_sha256"] != parent38.certificate_sha256:
        raise ValueError("certificate CP38 digest differs")
    hypothesis = parent38.word_law_hypothesis
    if values["checkpoint38_word_law_hypothesis_sha256"] != (
        hypothesis.hypothesis_sha256
    ):
        raise ValueError("certificate CP38 word-law hypothesis digest differs")
    if hypothesis.word_source_premise != _CP38_WORD_SOURCE_PREMISE:
        raise ValueError("certificate CP38 word-source premise differs")
    if (
        hypothesis.abstract_words_iid_uniform_uint64 is not True
        or hypothesis.abstract_words_independent_of_projection is not True
    ):
        raise ValueError("certificate CP38 abstract word premise is not qualified")
    if (
        parent38.fixed_batch_outcome_theorem != _CP38_FIXED_BATCH_OUTCOME_THEOREM
        or parent38.fixed_batch_configuration_theorem
        != _CP38_FIXED_BATCH_CONFIGURATION_THEOREM
        or parent38.augmented_configuration_ideal_tv_theorem
        != _CP38_AUGMENTED_IDEAL_TV_THEOREM
    ):
        raise ValueError("certificate CP38 theorem identity differs")
    _exact_integer(
        values["checkpoint39_owner_runtime_identity"],
        name="certificate.checkpoint39_owner_runtime_identity",
        minimum=1,
    )
    expected_integers = {
        "dyadic_denominator": _CP38_DYADIC_DENOMINATOR,
        "maximum_attempts": _CP38_MAX_ATTEMPTS,
        "maximum_target_configurations": _CP38_MAX_ATTEMPTS,
        "maximum_configuration_events": _CP38_MAX_EVENTS,
        "maximum_coordinates_per_event": _CP38_MAX_COORDINATES,
        "maximum_stream_records": (
            INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_STREAM_RECORDS
        ),
        "maximum_raw64_words_per_occurrence": (
            INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_RAW64_WORDS_PER_OCCURRENCE
        ),
        "maximum_total_raw64_words": (
            INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TOTAL_RAW64_WORDS
        ),
    }
    for name, expected in expected_integers.items():
        actual = values[name]
        if type(actual) is not int or actual != expected:
            raise ValueError("certificate.%s differs" % name)
    if values["admission_runtime_sha256"] != _runtime_sha256():
        raise ValueError("certificate runtime digest differs")
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="certificate.%s" % name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="certificate.%s" % name)
    expected_digest = _SEMANTIC_DIGEST(_certificate_payload(values))
    if values["certificate_sha256"] != expected_digest:
        raise ValueError("finite-resolution admission certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionAdmissionCertificate:
    if type(certificate) is not CounterKeyedInitialTiltRejectionAdmissionCertificate:
        raise TypeError("certificate has the wrong exact CP40 type")
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _make_certificate(
    coordination_owner: _CP39_OWNER_TYPE,
    admission_role_sha256: str,
) -> CounterKeyedInitialTiltRejectionAdmissionCertificate:
    if type(coordination_owner) is not _CP39_OWNER_TYPE:
        raise TypeError("coordination_owner has the wrong exact CP39 type")
    snapshot = _CP39_OWNER_SNAPSHOT(coordination_owner)
    parent39 = _CP39_LIVE_CERTIFICATE(coordination_owner, snapshot)
    _CP39_REQUIRE_OWNER_SNAPSHOT(coordination_owner, snapshot)
    if parent39 is not _CP39_CERTIFICATE_PROPERTY.__get__(
        coordination_owner, _CP39_OWNER_TYPE
    ):
        raise ValueError("CP39 live binding substituted its certificate")
    parent38_owner = _CP39_PARENT_PROPERTY.__get__(coordination_owner, _CP39_OWNER_TYPE)
    if type(parent38_owner) is not _CP38_OWNER_TYPE:
        raise TypeError("CP39 exposes the wrong exact CP38 parent type")
    parent38 = _CP38_CERTIFICATE_PROPERTY.__get__(parent38_owner, _CP38_OWNER_TYPE)
    if parent38 is not parent39.checkpoint38_certificate:
        raise ValueError("CP39 owner and certificate CP38 ancestry differ")
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "admission_policy": _POLICY,
        "admission_role_sha256": admission_role_sha256,
        "checkpoint39_certificate": parent39,
        "checkpoint39_certificate_sha256": parent39.certificate_sha256,
        "checkpoint39_runtime_sha256": parent39.coordination_runtime_sha256,
        "checkpoint39_owner_runtime_identity": id(coordination_owner),
        "checkpoint38_certificate": parent38,
        "checkpoint38_certificate_sha256": parent38.certificate_sha256,
        "checkpoint38_word_law_hypothesis_sha256": (
            parent38.word_law_hypothesis_sha256
        ),
        "checkpoint38_word_source_premise": _CP38_WORD_SOURCE_PREMISE,
        "checkpoint38_fixed_batch_configuration_theorem": (
            _CP38_FIXED_BATCH_CONFIGURATION_THEOREM
        ),
        "target_family": _TARGET_FAMILY,
        "target_conditioning": _TARGET_CONDITIONING,
        "conditioned_comparison": _COMPARISON,
        "conditioned_comparison_proof": _COMPARISON_PROOF,
        "dyadic_denominator": _CP38_DYADIC_DENOMINATOR,
        "maximum_attempts": _CP38_MAX_ATTEMPTS,
        "maximum_target_configurations": _CP38_MAX_ATTEMPTS,
        "maximum_configuration_events": _CP38_MAX_EVENTS,
        "maximum_coordinates_per_event": _CP38_MAX_COORDINATES,
        "maximum_stream_records": (
            INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_STREAM_RECORDS
        ),
        "maximum_raw64_words_per_occurrence": (
            INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_RAW64_WORDS_PER_OCCURRENCE
        ),
        "maximum_total_raw64_words": (
            INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TOTAL_RAW64_WORDS
        ),
        "admission_runtime_sha256": _runtime_sha256(),
        **{name: True for name in _CERTIFICATE_POSITIVE_FLAGS},
        **{name: False for name in _CERTIFICATE_NEGATIVE_FLAGS},
        "certificate_sha256": _ZERO_SHA256,
    }
    outcome_theorem = _CP38_FIXED_BATCH_OUTCOME_THEOREM
    augmented_theorem = _CP38_AUGMENTED_IDEAL_TV_THEOREM
    values["checkpoint38_fixed_batch_outcome_theorem"] = outcome_theorem
    values["checkpoint38_augmented_ideal_tv_theorem"] = augmented_theorem
    values["certificate_sha256"] = _SEMANTIC_DIGEST(_certificate_payload(values))
    return CounterKeyedInitialTiltRejectionAdmissionCertificate(
        _construction_token=_CERTIFICATE_TOKEN,
        **values,
    )


def _target_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "parent_finite_batch_law_result",
        "configuration_masses",
        "target_sha256",
    )


def _configuration_law_projection(
    masses: Tuple[_CP38_CONFIGURATION_MASS_TYPE, ...],
) -> Tuple[Mapping[str, object], ...]:
    return tuple(
        {
            "configuration_ordinal": row.configuration_ordinal,
            "representative_attempt_index": row.representative_attempt_index,
            "attempt_indices": row.attempt_indices,
            "duplicate_attempt_count": row.duplicate_attempt_count,
            "configuration_sha256": row.configuration_sha256,
            "fixed_batch_selection_probability_numerator": (
                row.fixed_batch_selection_probability_numerator
            ),
            "fixed_batch_selection_probability_denominator": (
                row.fixed_batch_selection_probability_denominator
            ),
            "selected_conditioned_probability_defined": (
                row.selected_conditioned_probability_defined
            ),
            "selected_conditioned_probability_numerator": (
                row.selected_conditioned_probability_numerator
            ),
            "selected_conditioned_probability_denominator": (
                row.selected_conditioned_probability_denominator
            ),
        }
        for row in masses
    )


def _word_free_target_law_payload(
    values: Mapping[str, object],
) -> Mapping[str, object]:
    payload = {
        "domain": "initial-tilt-rejection-word-free-fixed-B-target-law-v1",
        "target_family": values["target_family"],
        "target_conditioning": values["target_conditioning"],
        "conditioning_projection_sha256": values["conditioning_projection_sha256"],
        "fixed_batch_word_law_hypothesis_sha256": values[
            "fixed_batch_word_law_hypothesis_sha256"
        ],
        "fixed_batch_outcome_theorem": values["fixed_batch_outcome_theorem"],
        "fixed_batch_configuration_theorem": values[
            "fixed_batch_configuration_theorem"
        ],
        "augmented_ideal_dyadic_comparison_theorem": values[
            "augmented_ideal_dyadic_comparison_theorem"
        ],
        "conditioned_comparison": values["conditioned_comparison"],
        "conditioned_comparison_proof": values["conditioned_comparison_proof"],
        "dyadic_denominator": _CP38_DYADIC_DENOMINATOR,
        "attempt_budget": values["attempt_budget"],
        "configuration_mass_law_projection": _configuration_law_projection(
            values["configuration_masses"]
        ),
        "unique_configuration_count": values["unique_configuration_count"],
        "exhaustion_probability_denominator": values[
            "exhaustion_probability_denominator"
        ],
        "selection_probability_denominator": values[
            "selection_probability_denominator"
        ],
        "augmented_normalization_numerator": values[
            "augmented_normalization_numerator"
        ],
        "augmented_normalization_denominator": values[
            "augmented_normalization_denominator"
        ],
        "selected_conditioned_state_law_defined": values[
            "selected_conditioned_state_law_defined"
        ],
        "conditioned_ideal_dyadic_raw_strict_upper_defined": values[
            "conditioned_ideal_dyadic_raw_strict_upper_defined"
        ],
        "conditioned_ideal_dyadic_raw_strict_upper_numerator": values[
            "conditioned_ideal_dyadic_raw_strict_upper_numerator"
        ],
        "conditioned_ideal_dyadic_raw_strict_upper_denominator": values[
            "conditioned_ideal_dyadic_raw_strict_upper_denominator"
        ],
        "conditioned_ideal_dyadic_clipped_upper_defined": values[
            "conditioned_ideal_dyadic_clipped_upper_defined"
        ],
        "conditioned_ideal_dyadic_clipped_upper_numerator": values[
            "conditioned_ideal_dyadic_clipped_upper_numerator"
        ],
        "conditioned_ideal_dyadic_clipped_upper_denominator": values[
            "conditioned_ideal_dyadic_clipped_upper_denominator"
        ],
        "conditioned_ideal_dyadic_raw_upper_is_strict": values[
            "conditioned_ideal_dyadic_raw_upper_is_strict"
        ],
        "conditioned_ideal_dyadic_clipped_upper_is_non_strict": values[
            "conditioned_ideal_dyadic_clipped_upper_is_non_strict"
        ],
        "conditioned_ideal_dyadic_clipped_nonstrict_bound_nonvacuous": values[
            "conditioned_ideal_dyadic_clipped_nonstrict_bound_nonvacuous"
        ],
        "abstract_words_iid_uniform_uint64": values[
            "abstract_words_iid_uniform_uint64"
        ],
        "abstract_words_independent_of_word_free_batch": values[
            "abstract_words_independent_of_word_free_batch"
        ],
        "ideal_dyadic_comparison_uses_separate_independent_coordinate_sequences": (
            values[
                "ideal_dyadic_comparison_uses_separate_independent_coordinate_sequences"
            ]
        ),
        "ideal_dyadic_comparison_uses_common_continuous_uniform_coupling": values[
            "ideal_dyadic_comparison_uses_common_continuous_uniform_coupling"
        ],
        "conservative_dyadic_acceptance_probabilities_not_above_ideal": values[
            "conservative_dyadic_acceptance_probabilities_not_above_ideal"
        ],
        "ideal_selection_mass_at_least_dyadic_selection_mass": values[
            "ideal_selection_mass_at_least_dyadic_selection_mass"
        ],
        "conditioning_stability_factor_two_applied": values[
            "conditioning_stability_factor_two_applied"
        ],
    }
    payload["fixed_batch_word_source_premise"] = values[
        "fixed_batch_word_source_premise"
    ]
    payload["exhaustion_probability_numerator"] = values[
        "exhaustion_probability_numerator"
    ]
    payload["selection_probability_numerator"] = values[
        "selection_probability_numerator"
    ]
    return payload


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionFiniteResolutionTarget:
    """One exact CP38 fixed-B augmented and selected-conditioned target."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionAdmissionCertificate
    certificate_sha256: str
    parent_finite_batch_law_result: _CP38_RESULT_TYPE
    parent_finite_batch_law_result_sha256: str
    run_id: int
    initialization_index: int
    target_family: str
    target_conditioning: str
    conditioning_projection_sha256: str
    fixed_batch_word_law_hypothesis_sha256: str
    fixed_batch_word_source_premise: str
    fixed_batch_outcome_theorem: str
    fixed_batch_configuration_theorem: str
    augmented_ideal_dyadic_comparison_theorem: str
    conditioned_comparison: str
    conditioned_comparison_proof: str
    attempt_budget: int
    configuration_masses: Tuple[_CP38_CONFIGURATION_MASS_TYPE, ...]
    configuration_mass_sha256s: Tuple[str, ...]
    unique_configuration_count: int
    exhaustion_probability_numerator: int
    exhaustion_probability_denominator: int
    selection_probability_numerator: int
    selection_probability_denominator: int
    augmented_normalization_numerator: int
    augmented_normalization_denominator: int
    selected_conditioned_state_law_defined: bool
    conditioned_ideal_dyadic_raw_strict_upper_defined: bool
    conditioned_ideal_dyadic_raw_strict_upper_numerator: Optional[int]
    conditioned_ideal_dyadic_raw_strict_upper_denominator: Optional[int]
    conditioned_ideal_dyadic_clipped_upper_defined: bool
    conditioned_ideal_dyadic_clipped_upper_numerator: Optional[int]
    conditioned_ideal_dyadic_clipped_upper_denominator: Optional[int]
    conditioned_ideal_dyadic_raw_upper_is_strict: bool
    conditioned_ideal_dyadic_clipped_upper_is_non_strict: bool
    conditioned_ideal_dyadic_clipped_nonstrict_bound_nonvacuous: bool
    abstract_words_iid_uniform_uint64: bool
    abstract_words_independent_of_word_free_batch: bool
    ideal_dyadic_comparison_uses_separate_independent_coordinate_sequences: bool
    ideal_dyadic_comparison_uses_common_continuous_uniform_coupling: bool
    conservative_dyadic_acceptance_probabilities_not_above_ideal: bool
    ideal_selection_mass_at_least_dyadic_selection_mass: bool
    conditioning_stability_factor_two_applied: bool
    target_is_conditional_on_fixed_successful_batch: bool
    target_includes_exhaustion_atom: bool
    duplicate_configuration_aggregation_exact: bool
    selected_conditioned_target_normalized_when_defined: bool
    abstract_iid_decision_word_premise_only: bool
    target_is_live_output_law: bool
    target_integrates_checkpoint36_batch_law: bool
    target_is_exact_ideal_rejection_law: bool
    target_is_normalized_global_tilted_law: bool
    word_free_target_law_sha256: str
    word_free_target_law_digest_excludes_record_custody: bool
    target_sha256_is_record_custody_digest: bool
    target_sha256_is_word_free_target_law_digest: bool
    target_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("finite-resolution targets cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _TARGET_TOKEN:
            raise TypeError("finite-resolution targets are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("finite-resolution target fields are incomplete")
        _validate_target_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("finite-resolution targets are not pickleable")


def _target_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionFiniteResolutionTarget.__annotations__)


def _conditioned_comparison(
    parent: _CP38_RESULT_TYPE,
) -> Tuple[Optional[Fraction], Optional[Fraction], bool]:
    selection = Fraction(
        parent.fixed_batch_selection_probability_numerator,
        parent.fixed_batch_selection_probability_denominator,
    )
    if selection == 0:
        return None, None, False
    raw = Fraction(2 * parent.attempt_budget, _CP38_DYADIC_DENOMINATOR) / selection
    clipped = min(Fraction(1), raw)
    return raw, clipped, raw < 1


def _validate_target_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionAdmissionCertificate
    ] = None,
) -> None:
    if trusted_certificate is None:
        certificate = _validate_certificate(values["certificate"])
    else:
        if values["certificate"] is not trusted_certificate:
            raise ValueError("target trusted certificate identity differs")
        certificate = trusted_certificate
    _require_text(values["schema_version"], _SCHEMA_VERSION, name="target.schema")
    _REQUIRE_SHA256(values["certificate_sha256"], name="target.certificate_sha256")
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("target certificate digest differs")
    parent = values["parent_finite_batch_law_result"]
    if type(parent) is not _CP38_RESULT_TYPE:
        raise TypeError("target parent has the wrong exact CP38 result type")
    checked_parent = _CP38_PREFLIGHT_RESULT(
        parent,
        certificate=certificate.checkpoint38_certificate,
    )
    if checked_parent is not parent:
        raise ValueError("target CP38 preflight substituted its result")
    _REQUIRE_SHA256(
        values["parent_finite_batch_law_result_sha256"],
        name="target.parent_finite_batch_law_result_sha256",
    )
    if values["parent_finite_batch_law_result_sha256"] != parent.result_sha256:
        raise ValueError("target CP38 result digest differs")
    for name, expected in (
        ("run_id", parent.run_id),
        ("initialization_index", parent.initialization_index),
        ("attempt_budget", parent.attempt_budget),
        ("unique_configuration_count", parent.unique_configuration_count),
    ):
        actual = values[name]
        if type(actual) is not int or actual != expected:
            raise ValueError("target.%s differs from CP38" % name)
    _require_text(values["target_family"], _TARGET_FAMILY, name="target.target_family")
    _require_text(
        values["target_conditioning"],
        _TARGET_CONDITIONING,
        name="target.target_conditioning",
    )
    for name, expected in (
        ("fixed_batch_word_source_premise", _CP38_WORD_SOURCE_PREMISE),
        ("fixed_batch_outcome_theorem", _CP38_FIXED_BATCH_OUTCOME_THEOREM),
        (
            "fixed_batch_configuration_theorem",
            _CP38_FIXED_BATCH_CONFIGURATION_THEOREM,
        ),
        (
            "augmented_ideal_dyadic_comparison_theorem",
            _CP38_AUGMENTED_IDEAL_TV_THEOREM,
        ),
        ("conditioned_comparison", _COMPARISON),
        ("conditioned_comparison_proof", _COMPARISON_PROOF),
    ):
        _require_text(values[name], expected, name="target.%s" % name)
    _REQUIRE_SHA256(
        values["fixed_batch_word_law_hypothesis_sha256"],
        name="target.fixed_batch_word_law_hypothesis_sha256",
    )
    if values["fixed_batch_word_law_hypothesis_sha256"] != (
        certificate.checkpoint38_word_law_hypothesis_sha256
    ):
        raise ValueError("target CP38 word-law hypothesis digest differs")
    _REQUIRE_SHA256(
        values["conditioning_projection_sha256"],
        name="target.conditioning_projection_sha256",
    )
    if values["conditioning_projection_sha256"] != (
        parent.conditioning_projection_sha256
    ):
        raise ValueError("target conditioning projection differs")
    masses = _exact_tuple(
        values["configuration_masses"],
        name="target.configuration_masses",
        maximum=certificate.maximum_target_configurations,
        length=parent.unique_configuration_count,
    )
    if masses is not parent.configuration_masses:
        raise ValueError("target configuration-mass tuple lost parent identity")
    digests = _exact_tuple(
        values["configuration_mass_sha256s"],
        name="target.configuration_mass_sha256s",
        maximum=certificate.maximum_target_configurations,
        length=len(masses),
    )
    if digests is not parent.configuration_mass_sha256s:
        raise ValueError("target configuration-mass digests lost parent identity")
    for position, (row, digest) in enumerate(zip(masses, digests)):
        if type(row) is not _CP38_CONFIGURATION_MASS_TYPE:
            raise TypeError("target mass row %d has the wrong exact type" % position)
        _REQUIRE_SHA256(digest, name="target.mass_sha256s[%d]" % position)
        if row.mass_sha256 != digest or row.configuration_ordinal != position:
            raise ValueError("target configuration-mass sequence differs")
    exhaustion = _fraction_parts(
        values["exhaustion_probability_numerator"],
        values["exhaustion_probability_denominator"],
        name="target.exhaustion_probability",
    )
    selection = _fraction_parts(
        values["selection_probability_numerator"],
        values["selection_probability_denominator"],
        name="target.selection_probability",
    )
    normalization = _fraction_parts(
        values["augmented_normalization_numerator"],
        values["augmented_normalization_denominator"],
        name="target.augmented_normalization",
    )
    expected_exhaustion = Fraction(
        parent.fixed_batch_exhaustion_probability_numerator,
        parent.fixed_batch_exhaustion_probability_denominator,
    )
    expected_selection = Fraction(
        parent.fixed_batch_selection_probability_numerator,
        parent.fixed_batch_selection_probability_denominator,
    )
    if exhaustion != expected_exhaustion or selection != expected_selection:
        raise ValueError("target selection/exhaustion partition differs")
    if normalization != 1 or selection + exhaustion != 1:
        raise ValueError("target augmented law does not normalize")
    defined = values["selected_conditioned_state_law_defined"]
    if type(defined) is not bool or defined is not (selection > 0):
        raise ValueError("target selected-conditioned definition flag differs")
    raw, clipped, nonvacuous = _conditioned_comparison(parent)
    raw_defined = values["conditioned_ideal_dyadic_raw_strict_upper_defined"]
    clipped_defined = values["conditioned_ideal_dyadic_clipped_upper_defined"]
    if type(raw_defined) is not bool or type(clipped_defined) is not bool:
        raise TypeError("target comparison definition flags must be exact Booleans")
    if raw_defined is not defined or clipped_defined is not defined:
        raise ValueError("target comparison definition flags differ")
    checked_raw = _optional_fraction_parts(
        values["conditioned_ideal_dyadic_raw_strict_upper_numerator"],
        values["conditioned_ideal_dyadic_raw_strict_upper_denominator"],
        defined=raw_defined,
        name="target.conditioned_ideal_dyadic_raw_strict_upper",
    )
    checked_clipped = _optional_fraction_parts(
        values["conditioned_ideal_dyadic_clipped_upper_numerator"],
        values["conditioned_ideal_dyadic_clipped_upper_denominator"],
        defined=clipped_defined,
        name="target.conditioned_ideal_dyadic_clipped_upper",
    )
    if checked_raw != raw or checked_clipped != clipped:
        raise ValueError("target conditioned ideal/dyadic comparison differs")
    if raw is not None:
        expected_raw = (
            Fraction(2 * parent.attempt_budget, _CP38_DYADIC_DENOMINATOR) / selection
        )
        if raw != expected_raw or clipped != min(Fraction(1), raw):
            raise ValueError("target conditioned comparison formula differs")
    _exact_bool(
        values["conditioned_ideal_dyadic_raw_upper_is_strict"],
        defined,
        name="target.conditioned_ideal_dyadic_raw_upper_is_strict",
    )
    _exact_bool(
        values["conditioned_ideal_dyadic_clipped_upper_is_non_strict"],
        defined,
        name="target.conditioned_ideal_dyadic_clipped_upper_is_non_strict",
    )
    comparison_name_prefix = "target.conditioned_ideal_dyadic_"
    _exact_bool(
        values["conditioned_ideal_dyadic_clipped_nonstrict_bound_nonvacuous"],
        nonvacuous,
        name=comparison_name_prefix + "clipped_nonstrict_bound_nonvacuous",
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
        _exact_bool(values[name], True, name="target.%s" % name)
    for name in (
        "target_is_live_output_law",
        "target_integrates_checkpoint36_batch_law",
        "target_is_exact_ideal_rejection_law",
        "target_is_normalized_global_tilted_law",
        "target_sha256_is_word_free_target_law_digest",
    ):
        _exact_bool(values[name], False, name="target.%s" % name)
    _REQUIRE_SHA256(
        values["word_free_target_law_sha256"],
        name="target.word_free_target_law_sha256",
    )
    if values["word_free_target_law_sha256"] != _SEMANTIC_DIGEST(
        _word_free_target_law_payload(values)
    ):
        raise ValueError("word-free finite-resolution target-law digest differs")
    _REQUIRE_SHA256(values["target_sha256"], name="target.target_sha256")
    if values["target_sha256"] != _SEMANTIC_DIGEST(_target_payload(values)):
        raise ValueError("finite-resolution target digest differs")


_OPTIONAL_ADMISSION_CERTIFICATE = Optional[
    CounterKeyedInitialTiltRejectionAdmissionCertificate
]


def _validate_target(
    target: object,
    *,
    certificate: _OPTIONAL_ADMISSION_CERTIFICATE = None,
) -> CounterKeyedInitialTiltRejectionFiniteResolutionTarget:
    if type(target) is not CounterKeyedInitialTiltRejectionFiniteResolutionTarget:
        raise TypeError("target has the wrong exact CP40 target type")
    _validate_target_values(
        {name: getattr(target, name) for name in _target_fields()},
        trusted_certificate=certificate,
    )
    return target


def _make_target(
    certificate: CounterKeyedInitialTiltRejectionAdmissionCertificate,
    parent: _CP38_RESULT_TYPE,
) -> CounterKeyedInitialTiltRejectionFiniteResolutionTarget:
    checked_certificate = _validate_certificate(certificate)
    checked_parent = _CP38_PREFLIGHT_RESULT(
        parent,
        certificate=checked_certificate.checkpoint38_certificate,
    )
    selection = Fraction(
        checked_parent.fixed_batch_selection_probability_numerator,
        checked_parent.fixed_batch_selection_probability_denominator,
    )
    exhaustion = Fraction(
        checked_parent.fixed_batch_exhaustion_probability_numerator,
        checked_parent.fixed_batch_exhaustion_probability_denominator,
    )
    raw, clipped, nonvacuous = _conditioned_comparison(checked_parent)
    defined = selection > 0
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": checked_certificate,
        "certificate_sha256": checked_certificate.certificate_sha256,
        "parent_finite_batch_law_result": checked_parent,
        "parent_finite_batch_law_result_sha256": checked_parent.result_sha256,
        "run_id": checked_parent.run_id,
        "initialization_index": checked_parent.initialization_index,
        "target_family": _TARGET_FAMILY,
        "target_conditioning": _TARGET_CONDITIONING,
        "conditioning_projection_sha256": (
            checked_parent.conditioning_projection_sha256
        ),
        "fixed_batch_word_law_hypothesis_sha256": (
            checked_certificate.checkpoint38_word_law_hypothesis_sha256
        ),
        "fixed_batch_word_source_premise": _CP38_WORD_SOURCE_PREMISE,
        "fixed_batch_outcome_theorem": _CP38_FIXED_BATCH_OUTCOME_THEOREM,
        "conditioned_comparison": _COMPARISON,
        "conditioned_comparison_proof": _COMPARISON_PROOF,
        "attempt_budget": checked_parent.attempt_budget,
        "configuration_masses": checked_parent.configuration_masses,
        "configuration_mass_sha256s": checked_parent.configuration_mass_sha256s,
        "unique_configuration_count": checked_parent.unique_configuration_count,
        "exhaustion_probability_numerator": exhaustion.numerator,
        "exhaustion_probability_denominator": exhaustion.denominator,
        "selection_probability_numerator": selection.numerator,
        "selection_probability_denominator": selection.denominator,
        "augmented_normalization_numerator": 1,
        "augmented_normalization_denominator": 1,
        "selected_conditioned_state_law_defined": defined,
        "conditioned_ideal_dyadic_raw_strict_upper_defined": defined,
        "conditioned_ideal_dyadic_raw_strict_upper_numerator": (
            None if raw is None else raw.numerator
        ),
        "conditioned_ideal_dyadic_raw_strict_upper_denominator": (
            None if raw is None else raw.denominator
        ),
        "conditioned_ideal_dyadic_clipped_upper_defined": defined,
        "conditioned_ideal_dyadic_clipped_upper_numerator": (
            None if clipped is None else clipped.numerator
        ),
        "conditioned_ideal_dyadic_clipped_upper_denominator": (
            None if clipped is None else clipped.denominator
        ),
        "conditioned_ideal_dyadic_raw_upper_is_strict": defined,
        "conditioned_ideal_dyadic_clipped_upper_is_non_strict": defined,
        "abstract_words_iid_uniform_uint64": True,
        "abstract_words_independent_of_word_free_batch": True,
        "ideal_dyadic_comparison_uses_separate_independent_coordinate_sequences": (
            True
        ),
        "ideal_dyadic_comparison_uses_common_continuous_uniform_coupling": True,
        "conservative_dyadic_acceptance_probabilities_not_above_ideal": True,
        "ideal_selection_mass_at_least_dyadic_selection_mass": True,
        "conditioning_stability_factor_two_applied": True,
        "target_is_conditional_on_fixed_successful_batch": True,
        "target_includes_exhaustion_atom": True,
        "duplicate_configuration_aggregation_exact": True,
        "selected_conditioned_target_normalized_when_defined": True,
        "abstract_iid_decision_word_premise_only": True,
        "target_is_live_output_law": False,
        "target_integrates_checkpoint36_batch_law": False,
        "target_is_exact_ideal_rejection_law": False,
        "target_is_normalized_global_tilted_law": False,
        "word_free_target_law_sha256": _ZERO_SHA256,
        "word_free_target_law_digest_excludes_record_custody": True,
        "target_sha256_is_record_custody_digest": True,
        "target_sha256_is_word_free_target_law_digest": False,
        "target_sha256": _ZERO_SHA256,
    }
    configuration_theorem = _CP38_FIXED_BATCH_CONFIGURATION_THEOREM
    augmented_theorem = _CP38_AUGMENTED_IDEAL_TV_THEOREM
    clipped_nonvacuous_field = "conditioned_ideal_dyadic_"
    clipped_nonvacuous_field += "clipped_nonstrict_bound_nonvacuous"
    values["fixed_batch_configuration_theorem"] = configuration_theorem
    values["augmented_ideal_dyadic_comparison_theorem"] = augmented_theorem
    values[clipped_nonvacuous_field] = nonvacuous
    values["word_free_target_law_sha256"] = _SEMANTIC_DIGEST(
        _word_free_target_law_payload(values)
    )
    values["target_sha256"] = _SEMANTIC_DIGEST(_target_payload(values))
    return CounterKeyedInitialTiltRejectionFiniteResolutionTarget(
        _construction_token=_TARGET_TOKEN,
        **values,
    )


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "parent_coordination_result",
        "finite_resolution_target",
        "initial_configuration",
        "initial_intensity",
        "lineage_state",
        "occurrence_payloads",
        "target_configuration_mass",
        "result_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitializerAdmissionResult:
    """One admitted CP39 state or exact bounded-exhaustion no-state result."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionAdmissionCertificate
    certificate_sha256: str
    parent_coordination_result: _CP39_RESULT_TYPE
    parent_coordination_result_sha256: str
    finite_resolution_target: CounterKeyedInitialTiltRejectionFiniteResolutionTarget
    finite_resolution_target_sha256: str
    finite_resolution_target_law_sha256: str
    run_id: int
    initialization_index: int
    admission_status: str
    source_outcome: str
    source_selected_attempt_index: Optional[int]
    initial_configuration: Optional[object]
    initial_configuration_sha256: Optional[str]
    initial_intensity: Optional[object]
    initial_intensity_sha256: Optional[str]
    lineage_state: Optional[object]
    lineage_state_sha256: Optional[str]
    occurrence_payloads: Optional[Tuple[object, ...]]
    occurrence_payload_sha256s: Optional[Tuple[str, ...]]
    tag3_raw64_word_counts: Optional[Tuple[int, ...]]
    qualified_lineage_coordinates: Optional[Tuple[Tuple[int, int, int, int], ...]]
    target_configuration_ordinal: Optional[int]
    target_configuration_mass: Optional[_CP38_CONFIGURATION_MASS_TYPE]
    target_configuration_mass_sha256: Optional[str]
    target_aggregate_mass_numerator: Optional[int]
    target_aggregate_mass_denominator: Optional[int]
    target_conditioned_mass_numerator: Optional[int]
    target_conditioned_mass_denominator: Optional[int]
    state_present: bool
    downstream_initial_state_structurally_admitted: bool
    structurally_admissible_under_declared_fixed_batch_target: bool
    generic_structural_initial_state_boundary_applied: bool
    selected_empty_state_admitted: bool
    exhausted_valid_no_state: bool
    operational_failure_returned_as_exhaustion: bool
    exact_parent_selected_configuration_identity_preserved: bool
    exact_parent_intensity_lineage_and_payload_identity_preserved: bool
    target_mass_row_selected_by_parent_ordinal: bool
    aggregate_representative_not_substituted_for_selected_state: bool
    parent_coordinate_call_count: int
    no_added_rng_word_retry_fallback_or_rollback: bool
    deterministic_fixed_address_replay_only: bool
    actual_live_result_is_target_draw: bool
    live_initializer_distribution_certified: bool
    unconditional_initializer_distribution_certified: bool
    normalized_global_tilted_law_certified: bool
    exact_ideal_rejection_certified: bool
    formal_test28_closed: bool
    tag3_payload_semantics_certified: bool
    brownian_stream_consumption_certified: bool
    continuous_drift_admissible: bool
    path_admissible: bool
    full_sampler_admissible: bool
    sampler_liveness_certified: bool
    scientific_claim_promoted: bool
    model_quality_claim_promoted: bool
    generality_claim_promoted: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("initializer admission results cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("initializer admission results are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("initializer admission result fields are incomplete")
        _validate_result_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer admission results are not pickleable")


def _result_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitializerAdmissionResult.__annotations__)


_RESULT_ALWAYS_FALSE_FLAGS = (
    "operational_failure_returned_as_exhaustion",
    "actual_live_result_is_target_draw",
    "live_initializer_distribution_certified",
    "unconditional_initializer_distribution_certified",
    "normalized_global_tilted_law_certified",
    "exact_ideal_rejection_certified",
    "formal_test28_closed",
    "tag3_payload_semantics_certified",
    "brownian_stream_consumption_certified",
    "continuous_drift_admissible",
    "path_admissible",
    "full_sampler_admissible",
    "sampler_liveness_certified",
    "scientific_claim_promoted",
    "model_quality_claim_promoted",
    "generality_claim_promoted",
)


def _preflight_result_record(
    result: object,
    *,
    certificate: CounterKeyedInitialTiltRejectionAdmissionCertificate,
) -> CounterKeyedInitializerAdmissionResult:
    if type(result) is not CounterKeyedInitializerAdmissionResult:
        raise TypeError("result has the wrong exact CP40 admission type")
    if result.certificate is not certificate:
        raise ValueError("result belongs to another CP40 certificate")
    target = result.finite_resolution_target
    if type(target) is not CounterKeyedInitialTiltRejectionFiniteResolutionTarget:
        raise TypeError("result target has the wrong exact CP40 target type")
    target_masses = _exact_tuple(
        target.configuration_masses,
        name="result.target.configuration_masses",
        maximum=certificate.maximum_target_configurations,
    )
    target_mass_digests = _exact_tuple(
        target.configuration_mass_sha256s,
        name="result.target.configuration_mass_sha256s",
        maximum=certificate.maximum_target_configurations,
        length=len(target_masses),
    )
    optional_tuples = {}
    for name, value in (
        ("occurrence_payloads", result.occurrence_payloads),
        ("occurrence_payload_sha256s", result.occurrence_payload_sha256s),
        ("tag3_raw64_word_counts", result.tag3_raw64_word_counts),
        ("qualified_lineage_coordinates", result.qualified_lineage_coordinates),
    ):
        if value is not None:
            optional_tuples[name] = _exact_tuple(
                value,
                name="result.%s" % name,
                maximum=certificate.maximum_stream_records,
            )
    payloads = optional_tuples.get("occurrence_payloads")
    for name in (
        "occurrence_payload_sha256s",
        "tag3_raw64_word_counts",
        "qualified_lineage_coordinates",
    ):
        checked = optional_tuples.get(name)
        if (
            payloads is not None
            and checked is not None
            and len(checked) != len(payloads)
        ):
            raise ValueError("result.%s length differs from occurrence payloads" % name)
    for position, digest in enumerate(target_mass_digests):
        _REQUIRE_SHA256(
            digest,
            name="result.target.configuration_mass_sha256s[%d]" % position,
        )
    occurrence_digests = optional_tuples.get("occurrence_payload_sha256s")
    if occurrence_digests is not None:
        for position, digest in enumerate(occurrence_digests):
            _REQUIRE_SHA256(
                digest,
                name="result.occurrence_payload_sha256s[%d]" % position,
            )
    counts = optional_tuples.get("tag3_raw64_word_counts")
    if counts is not None:
        running_total = 0
        for position, count in enumerate(counts):
            running_total += _exact_integer(
                count,
                name="result.tag3_raw64_word_counts[%d]" % position,
                minimum=1,
                maximum=certificate.maximum_raw64_words_per_occurrence,
            )
            if running_total > certificate.maximum_total_raw64_words:
                raise ValueError("result tag-3 word plan exceeds aggregate bound")
    coordinates = optional_tuples.get("qualified_lineage_coordinates")
    if coordinates is not None:
        for position, coordinate in enumerate(coordinates):
            checked_coordinate = _exact_tuple(
                coordinate,
                name="result.qualified_lineage_coordinates[%d]" % position,
                maximum=4,
                length=4,
            )
            for limb_position, limb in enumerate(checked_coordinate):
                _exact_integer(
                    limb,
                    name="result.qualified_lineage_coordinates[%d][%d]"
                    % (position, limb_position),
                )
    return result


def _validate_result_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionAdmissionCertificate
    ] = None,
) -> None:
    if trusted_certificate is None:
        certificate = _validate_certificate(values["certificate"])
    else:
        if values["certificate"] is not trusted_certificate:
            raise ValueError("result trusted certificate identity differs")
        certificate = trusted_certificate
    _require_text(values["schema_version"], _SCHEMA_VERSION, name="result.schema")
    _REQUIRE_SHA256(values["certificate_sha256"], name="result.certificate_sha256")
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("result certificate digest differs")
    parent = values["parent_coordination_result"]
    if type(parent) is not _CP39_RESULT_TYPE:
        raise TypeError("result parent has the wrong exact CP39 result type")
    checked_parent = _CP39_PREFLIGHT_RESULT(
        parent,
        certificate=certificate.checkpoint39_certificate,
    )
    if checked_parent is not parent:
        raise ValueError("result CP39 preflight substituted its parent")
    _REQUIRE_SHA256(
        values["parent_coordination_result_sha256"],
        name="result.parent_coordination_result_sha256",
    )
    if values["parent_coordination_result_sha256"] != parent.result_sha256:
        raise ValueError("result CP39 parent digest differs")
    target = _validate_target(
        values["finite_resolution_target"], certificate=certificate
    )
    _REQUIRE_SHA256(
        values["finite_resolution_target_sha256"],
        name="result.finite_resolution_target_sha256",
    )
    if values["finite_resolution_target_sha256"] != target.target_sha256:
        raise ValueError("result target digest differs")
    _REQUIRE_SHA256(
        values["finite_resolution_target_law_sha256"],
        name="result.finite_resolution_target_law_sha256",
    )
    if values["finite_resolution_target_law_sha256"] != (
        target.word_free_target_law_sha256
    ):
        raise ValueError("result word-free target-law digest differs")
    law_parent = parent.parent_finite_batch_law_result
    if target.parent_finite_batch_law_result is not law_parent:
        raise ValueError("result target and CP39 parent use different CP38 results")
    for name, expected in (
        ("run_id", parent.run_id),
        ("initialization_index", parent.initialization_index),
    ):
        actual = values[name]
        if type(actual) is not int or actual != expected:
            raise ValueError("result.%s differs from CP39" % name)
    status = values["admission_status"]
    if type(status) is not str or status not in _STATUSES:
        raise ValueError("result admission status is unknown")
    source_outcome = values["source_outcome"]
    if type(source_outcome) is not str:
        raise TypeError("result source_outcome must be exact text")
    if source_outcome != parent.outcome:
        raise ValueError("result source outcome differs from CP39")
    expected_status = "admitted" if parent.outcome == "selected" else "exhausted"
    if status != expected_status:
        raise ValueError("result admission status differs from CP39 outcome")
    _exact_integer(
        values["parent_coordinate_call_count"],
        name="result.parent_coordinate_call_count",
        minimum=1,
        maximum=1,
    )
    for name in _RESULT_ALWAYS_FALSE_FLAGS:
        _exact_bool(values[name], False, name="result.%s" % name)
    _exact_bool(
        values["generic_structural_initial_state_boundary_applied"],
        True,
        name="result.generic_structural_initial_state_boundary_applied",
    )
    _exact_bool(
        values["no_added_rng_word_retry_fallback_or_rollback"],
        True,
        name="result.no_added_rng_word_retry_fallback_or_rollback",
    )
    _exact_bool(
        values["deterministic_fixed_address_replay_only"],
        True,
        name="result.deterministic_fixed_address_replay_only",
    )
    selected = parent.outcome == "selected"
    if selected:
        if not target.selected_conditioned_state_law_defined:
            raise ValueError("selected result has no selected-conditioned target")
        attempt = _exact_integer(
            values["source_selected_attempt_index"],
            name="result.source_selected_attempt_index",
            maximum=law_parent.attempt_budget - 1,
        )
        if attempt != parent.source_selected_attempt_index:
            raise ValueError("result selected attempt differs from CP39")
        configuration = values["initial_configuration"]
        if configuration is not parent.selected_configuration:
            raise ValueError("result selected configuration identity differs")
        _REQUIRE_SHA256(
            values["initial_configuration_sha256"],
            name="result.initial_configuration_sha256",
        )
        if values["initial_configuration_sha256"] != (
            parent.selected_configuration_sha256
        ):
            raise ValueError("result selected configuration digest differs")
        if values["initial_intensity"] is not parent.initial_intensity:
            raise ValueError("result initial intensity identity differs")
        _REQUIRE_SHA256(
            values["initial_intensity_sha256"],
            name="result.initial_intensity_sha256",
        )
        if values["initial_intensity_sha256"] != parent.initial_intensity_sha256:
            raise ValueError("result initial intensity digest differs")
        if values["lineage_state"] is not parent.lineage_state:
            raise ValueError("result lineage state identity differs")
        _REQUIRE_SHA256(
            values["lineage_state_sha256"],
            name="result.lineage_state_sha256",
        )
        if values["lineage_state_sha256"] != parent.lineage_state_sha256:
            raise ValueError("result lineage state digest differs")
        if values["occurrence_payloads"] is not parent.occurrence_payloads:
            raise ValueError("result occurrence payload identity differs")
        if values["occurrence_payload_sha256s"] is not (
            parent.occurrence_payload_sha256s
        ):
            raise ValueError("result occurrence digest identity differs")
        if values["tag3_raw64_word_counts"] is not parent.tag3_raw64_word_counts:
            raise ValueError("result tag-3 word-count identity differs")
        if values["qualified_lineage_coordinates"] is not (
            parent.qualified_lineage_coordinates
        ):
            raise ValueError("result lineage-coordinate identity differs")
        ordinal = _exact_integer(
            values["target_configuration_ordinal"],
            name="result.target_configuration_ordinal",
            maximum=target.unique_configuration_count - 1,
        )
        if ordinal != law_parent.selected_configuration_ordinal:
            raise ValueError("result target ordinal differs from CP38")
        row = values["target_configuration_mass"]
        if row is not target.configuration_masses[ordinal]:
            raise ValueError("result target mass row is not the ordinal row")
        if type(row) is not _CP38_CONFIGURATION_MASS_TYPE:
            raise TypeError("result target mass row has the wrong exact type")
        _REQUIRE_SHA256(
            values["target_configuration_mass_sha256"],
            name="result.target_configuration_mass_sha256",
        )
        if values["target_configuration_mass_sha256"] != row.mass_sha256:
            raise ValueError("result target mass-row digest differs")
        aggregate = _optional_fraction_parts(
            values["target_aggregate_mass_numerator"],
            values["target_aggregate_mass_denominator"],
            defined=True,
            name="result.target_aggregate_mass",
        )
        conditioned = _optional_fraction_parts(
            values["target_conditioned_mass_numerator"],
            values["target_conditioned_mass_denominator"],
            defined=True,
            name="result.target_conditioned_mass",
        )
        expected_aggregate = Fraction(
            row.fixed_batch_selection_probability_numerator,
            row.fixed_batch_selection_probability_denominator,
        )
        expected_conditioned = Fraction(
            row.selected_conditioned_probability_numerator,
            row.selected_conditioned_probability_denominator,
        )
        if aggregate != expected_aggregate or aggregate <= 0:
            raise ValueError("result selected target aggregate mass differs")
        if conditioned != expected_conditioned or conditioned <= 0:
            raise ValueError("result selected conditioned mass differs")
        if row.configuration_sha256 != parent.selected_configuration_sha256:
            raise ValueError("result target row and selected state differ structurally")
        expected_flags = {
            "state_present": True,
            "downstream_initial_state_structurally_admitted": True,
            "structurally_admissible_under_declared_fixed_batch_target": True,
            "selected_empty_state_admitted": len(configuration) == 0,
            "exhausted_valid_no_state": False,
            "exact_parent_selected_configuration_identity_preserved": True,
            "exact_parent_intensity_lineage_and_payload_identity_preserved": True,
            "target_mass_row_selected_by_parent_ordinal": True,
            "aggregate_representative_not_substituted_for_selected_state": True,
        }
    else:
        optional_state_fields = (
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
        )
        for name in optional_state_fields:
            if values[name] is not None:
                raise ValueError("exhausted result %s must be absent" % name)
        expected_flags = {
            "state_present": False,
            "downstream_initial_state_structurally_admitted": False,
            "structurally_admissible_under_declared_fixed_batch_target": False,
            "selected_empty_state_admitted": False,
            "exhausted_valid_no_state": True,
            "exact_parent_selected_configuration_identity_preserved": False,
            "exact_parent_intensity_lineage_and_payload_identity_preserved": False,
            "target_mass_row_selected_by_parent_ordinal": False,
            "aggregate_representative_not_substituted_for_selected_state": False,
        }
    for name, expected in expected_flags.items():
        _exact_bool(values[name], expected, name="result.%s" % name)
    _REQUIRE_SHA256(values["result_sha256"], name="result.result_sha256")
    if values["result_sha256"] != _SEMANTIC_DIGEST(_result_payload(values)):
        raise ValueError("initializer admission result digest differs")


def _make_result(
    certificate: CounterKeyedInitialTiltRejectionAdmissionCertificate,
    parent: _CP39_RESULT_TYPE,
    target: CounterKeyedInitialTiltRejectionFiniteResolutionTarget,
) -> CounterKeyedInitializerAdmissionResult:
    checked_certificate = _validate_certificate(certificate)
    checked_parent = _CP39_PREFLIGHT_RESULT(
        parent,
        certificate=checked_certificate.checkpoint39_certificate,
    )
    checked_target = _validate_target(target, certificate=checked_certificate)
    if checked_target.parent_finite_batch_law_result is not (
        checked_parent.parent_finite_batch_law_result
    ):
        raise ValueError("result target has another CP38 parent")
    selected = checked_parent.outcome == "selected"
    if selected:
        law_parent = checked_parent.parent_finite_batch_law_result
        ordinal = law_parent.selected_configuration_ordinal
        row = checked_target.configuration_masses[ordinal]
        aggregate = Fraction(
            row.fixed_batch_selection_probability_numerator,
            row.fixed_batch_selection_probability_denominator,
        )
        conditioned = Fraction(
            row.selected_conditioned_probability_numerator,
            row.selected_conditioned_probability_denominator,
        )
        status = "admitted"
        attempt = checked_parent.source_selected_attempt_index
        configuration = checked_parent.selected_configuration
        configuration_sha256 = checked_parent.selected_configuration_sha256
        intensity = checked_parent.initial_intensity
        intensity_sha256 = checked_parent.initial_intensity_sha256
        lineage = checked_parent.lineage_state
        lineage_sha256 = checked_parent.lineage_state_sha256
        payloads = checked_parent.occurrence_payloads
        payload_digests = checked_parent.occurrence_payload_sha256s
        counts = checked_parent.tag3_raw64_word_counts
        coordinates = checked_parent.qualified_lineage_coordinates
    else:
        status = "exhausted"
        attempt = None
        configuration = None
        configuration_sha256 = None
        intensity = None
        intensity_sha256 = None
        lineage = None
        lineage_sha256 = None
        payloads = None
        payload_digests = None
        counts = None
        coordinates = None
        ordinal = None
        row = None
        aggregate = None
        conditioned = None
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": checked_certificate,
        "certificate_sha256": checked_certificate.certificate_sha256,
        "parent_coordination_result": checked_parent,
        "parent_coordination_result_sha256": checked_parent.result_sha256,
        "finite_resolution_target": checked_target,
        "finite_resolution_target_sha256": checked_target.target_sha256,
        "finite_resolution_target_law_sha256": (
            checked_target.word_free_target_law_sha256
        ),
        "run_id": checked_parent.run_id,
        "initialization_index": checked_parent.initialization_index,
        "admission_status": status,
        "source_outcome": checked_parent.outcome,
        "source_selected_attempt_index": attempt,
        "initial_configuration": configuration,
        "initial_configuration_sha256": configuration_sha256,
        "initial_intensity": intensity,
        "initial_intensity_sha256": intensity_sha256,
        "lineage_state": lineage,
        "lineage_state_sha256": lineage_sha256,
        "occurrence_payloads": payloads,
        "occurrence_payload_sha256s": payload_digests,
        "tag3_raw64_word_counts": counts,
        "qualified_lineage_coordinates": coordinates,
        "target_configuration_ordinal": ordinal,
        "target_configuration_mass": row,
        "target_configuration_mass_sha256": None if row is None else row.mass_sha256,
        "target_aggregate_mass_numerator": (
            None if aggregate is None else aggregate.numerator
        ),
        "target_aggregate_mass_denominator": (
            None if aggregate is None else aggregate.denominator
        ),
        "target_conditioned_mass_numerator": (
            None if conditioned is None else conditioned.numerator
        ),
        "target_conditioned_mass_denominator": (
            None if conditioned is None else conditioned.denominator
        ),
        "state_present": selected,
        "downstream_initial_state_structurally_admitted": selected,
        "structurally_admissible_under_declared_fixed_batch_target": selected,
        "generic_structural_initial_state_boundary_applied": True,
        "selected_empty_state_admitted": selected and len(configuration) == 0,
        "exhausted_valid_no_state": not selected,
        "operational_failure_returned_as_exhaustion": False,
        "exact_parent_selected_configuration_identity_preserved": selected,
        "exact_parent_intensity_lineage_and_payload_identity_preserved": selected,
        "target_mass_row_selected_by_parent_ordinal": selected,
        "aggregate_representative_not_substituted_for_selected_state": selected,
        "parent_coordinate_call_count": 1,
        "no_added_rng_word_retry_fallback_or_rollback": True,
        "deterministic_fixed_address_replay_only": True,
        **{name: False for name in _RESULT_ALWAYS_FALSE_FLAGS},
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _SEMANTIC_DIGEST(_result_payload(values))
    return CounterKeyedInitializerAdmissionResult(
        _construction_token=_RESULT_TOKEN,
        **values,
    )


def _target_snapshot(
    target: CounterKeyedInitialTiltRejectionFiniteResolutionTarget,
) -> Tuple[object, ...]:
    return _RECORD_SNAPSHOT(target, _target_fields())


def _require_target_unchanged(
    target: CounterKeyedInitialTiltRejectionFiniteResolutionTarget,
    before: Tuple[object, ...],
) -> None:
    _REQUIRE_RECORD_UNCHANGED(
        target,
        _target_fields(),
        before,
        identity_fields=(
            "certificate",
            "parent_finite_batch_law_result",
            "configuration_masses",
            "configuration_mass_sha256s",
        ),
        name="finite-resolution target",
    )


def _result_tree_snapshot(
    result: CounterKeyedInitializerAdmissionResult,
) -> Tuple[object, ...]:
    return (
        _RECORD_SNAPSHOT(result, _result_fields()),
        _target_snapshot(result.finite_resolution_target),
        _CP39_RESULT_TREE_SNAPSHOT(result.parent_coordination_result),
    )


def _require_result_tree_unchanged(
    result: CounterKeyedInitializerAdmissionResult,
    before: Tuple[object, ...],
    *,
    certificate: CounterKeyedInitialTiltRejectionAdmissionCertificate,
) -> None:
    _preflight_result_record(result, certificate=certificate)
    if type(before) is not tuple or len(before) != 3:
        raise TypeError("initializer admission result-tree snapshot is malformed")
    result_before, target_before, parent_before = before
    _REQUIRE_RECORD_UNCHANGED(
        result,
        _result_fields(),
        result_before,
        identity_fields=(
            "certificate",
            "parent_coordination_result",
            "finite_resolution_target",
            "initial_configuration",
            "initial_intensity",
            "lineage_state",
            "occurrence_payloads",
            "occurrence_payload_sha256s",
            "tag3_raw64_word_counts",
            "qualified_lineage_coordinates",
            "target_configuration_mass",
        ),
        name="initializer admission result",
    )
    _require_target_unchanged(result.finite_resolution_target, target_before)
    _CP39_REQUIRE_RESULT_TREE_UNCHANGED(
        result.parent_coordination_result,
        parent_before,
        certificate=certificate.checkpoint39_certificate,
    )


def _certificate_snapshot(
    certificate: CounterKeyedInitialTiltRejectionAdmissionCertificate,
) -> Tuple[object, ...]:
    return _RECORD_SNAPSHOT(certificate, _certificate_fields())


def _require_certificate_unchanged(
    certificate: CounterKeyedInitialTiltRejectionAdmissionCertificate,
    before: Tuple[object, ...],
) -> None:
    _REQUIRE_RECORD_UNCHANGED(
        certificate,
        _certificate_fields(),
        before,
        identity_fields=("checkpoint39_certificate", "checkpoint38_certificate"),
        name="finite-resolution admission certificate",
    )


def _require_dependency_surfaces() -> None:
    expected = (
        (_CP39_OWNER_TYPE._owner_snapshot, _CP39_OWNER_SNAPSHOT),
        (_CP39_OWNER_TYPE._require_owner_snapshot, _CP39_REQUIRE_OWNER_SNAPSHOT),
        (_CP39_OWNER_TYPE._live_certificate, _CP39_LIVE_CERTIFICATE),
        (_CP39_OWNER_TYPE.coordinate, _CP39_COORDINATE),
        (_CP39_OWNER_TYPE.validate_result, _CP39_VALIDATE_RESULT),
        (_CP39_OWNER_TYPE.certificate, _CP39_CERTIFICATE_PROPERTY),
        (_CP39_OWNER_TYPE.finite_batch_law_owner, _CP39_PARENT_PROPERTY),
        (_coord._validate_certificate, _CP39_VALIDATE_CERTIFICATE),
        (_coord._preflight_result_record, _CP39_PREFLIGHT_RESULT),
        (_coord._result_tree_snapshot, _CP39_RESULT_TREE_SNAPSHOT),
        (
            _coord._require_result_tree_unchanged,
            _CP39_REQUIRE_RESULT_TREE_UNCHANGED,
        ),
        (_law._validate_certificate, _CP38_VALIDATE_CERTIFICATE),
        (_law._preflight_result_record, _CP38_PREFLIGHT_RESULT),
        (_law._result_tree_snapshot, _CP38_RESULT_TREE_SNAPSHOT),
        (_law._require_result_tree_unchanged, _CP38_REQUIRE_RESULT_TREE_UNCHANGED),
        (_law._fraction_parts, _CP38_FRACTION_PARTS),
    )
    if any(live is not frozen for live, frozen in expected):
        raise ValueError("finite-resolution admission dependency surface changed")
    _CP39_SURFACE_GUARD()


class CounterKeyedInitialTiltRejectionAdmissionOwner:
    """Immutable owner of one exact-CP39 fixed-B admission operation."""

    __slots__ = (
        "_coordination_owner",
        "_coordination_owner_identity",
        "_checkpoint39_certificate",
        "_checkpoint39_certificate_identity",
        "_checkpoint38_owner",
        "_checkpoint38_owner_identity",
        "_checkpoint38_certificate",
        "_checkpoint38_certificate_identity",
        "_admission_policy",
        "_admission_policy_identity",
        "_admission_role_sha256",
        "_admission_role_sha256_identity",
        "_certificate",
        "_certificate_identity",
        "_certificate_snapshot_value",
        "_certificate_snapshot_identity",
        "_parent_owner_snapshot",
        "_parent_require_owner_snapshot",
        "_parent_live_certificate",
        "_parent_coordinate",
        "_parent_validate_result",
        "_parent_result_preflight",
        "_parent_result_tree_snapshot",
        "_parent_result_tree_unchanged",
        "_target_builder",
        "_target_validator",
        "_result_builder",
        "_result_validator",
        "_result_preflight",
        "_result_tree_snapshotter",
        "_result_tree_unchanged_checker",
        "_certificate_validator",
        "_certificate_builder",
        "_surface_guard",
        "_surface_guard_identity",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("finite-resolution admission owners cannot subclass")

    def __init__(
        self,
        coordination_owner: _CP39_OWNER_TYPE,
        admission_policy: str,
        admission_role_sha256: str,
        certificate: CounterKeyedInitialTiltRejectionAdmissionCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("finite-resolution admission owners require certification")
        if type(coordination_owner) is not _CP39_OWNER_TYPE:
            raise TypeError("coordination_owner has the wrong exact CP39 type")
        policy = _require_text(admission_policy, _POLICY, name="admission_policy")
        role = _REQUIRE_SHA256(admission_role_sha256, name="admission_role_sha256")
        checked = _validate_certificate(certificate)
        parent39 = _CP39_CERTIFICATE_PROPERTY.__get__(
            coordination_owner, _CP39_OWNER_TYPE
        )
        parent38_owner = _CP39_PARENT_PROPERTY.__get__(
            coordination_owner, _CP39_OWNER_TYPE
        )
        if type(parent38_owner) is not _CP38_OWNER_TYPE:
            raise TypeError("CP39 exposes the wrong exact CP38 parent type")
        parent38 = _CP38_CERTIFICATE_PROPERTY.__get__(parent38_owner, _CP38_OWNER_TYPE)
        if checked.checkpoint39_certificate is not parent39:
            raise ValueError("owner CP39 certificate identity differs")
        if checked.checkpoint38_certificate is not parent38:
            raise ValueError("owner CP38 certificate identity differs")
        if checked.checkpoint39_owner_runtime_identity != id(coordination_owner):
            raise ValueError("owner CP39 runtime identity differs")
        certificate_snapshot = _certificate_snapshot(checked)
        bindings = (
            ("_coordination_owner", coordination_owner),
            ("_coordination_owner_identity", coordination_owner),
            ("_checkpoint39_certificate", parent39),
            ("_checkpoint39_certificate_identity", parent39),
            ("_checkpoint38_owner", parent38_owner),
            ("_checkpoint38_owner_identity", parent38_owner),
            ("_checkpoint38_certificate", parent38),
            ("_checkpoint38_certificate_identity", parent38),
            ("_admission_policy", policy),
            ("_admission_policy_identity", policy),
            ("_admission_role_sha256", role),
            ("_admission_role_sha256_identity", role),
            ("_certificate", checked),
            ("_certificate_identity", checked),
            ("_certificate_snapshot_value", certificate_snapshot),
            ("_certificate_snapshot_identity", certificate_snapshot),
            ("_parent_owner_snapshot", _CP39_OWNER_SNAPSHOT),
            ("_parent_require_owner_snapshot", _CP39_REQUIRE_OWNER_SNAPSHOT),
            ("_parent_live_certificate", _CP39_LIVE_CERTIFICATE),
            ("_parent_coordinate", _CP39_COORDINATE),
            ("_parent_validate_result", _CP39_VALIDATE_RESULT),
            ("_parent_result_preflight", _CP39_PREFLIGHT_RESULT),
            ("_parent_result_tree_snapshot", _CP39_RESULT_TREE_SNAPSHOT),
            (
                "_parent_result_tree_unchanged",
                _CP39_REQUIRE_RESULT_TREE_UNCHANGED,
            ),
            ("_target_builder", _make_target),
            ("_target_validator", _validate_target),
            ("_result_builder", _make_result),
            ("_result_validator", _validate_result_values),
            ("_result_preflight", _preflight_result_record),
            ("_result_tree_snapshotter", _result_tree_snapshot),
            ("_result_tree_unchanged_checker", _require_result_tree_unchanged),
            ("_certificate_validator", _validate_certificate),
            ("_certificate_builder", _make_certificate),
            ("_surface_guard", _require_parent_surfaces),
            ("_surface_guard_identity", _require_parent_surfaces),
            ("_sealed", True),
        )
        for name, value in bindings:
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("finite-resolution admission owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("finite-resolution admission owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("finite-resolution admission owners are not pickleable")

    @property
    def certificate(
        self,
    ) -> CounterKeyedInitialTiltRejectionAdmissionCertificate:
        return self._certificate

    @property
    def coordination_owner(self) -> _CP39_OWNER_TYPE:
        return self._coordination_owner

    def _identity_state(self) -> Tuple[object, ...]:
        if self._surface_guard is not _require_parent_surfaces or (
            self._surface_guard_identity is not _require_parent_surfaces
        ):
            raise ValueError("finite-resolution admission surface guard changed")
        self._surface_guard()
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("finite-resolution admission owner seal differs")
        current = (
            self._coordination_owner,
            self._checkpoint39_certificate,
            self._checkpoint38_owner,
            self._checkpoint38_certificate,
            self._admission_policy,
            self._admission_role_sha256,
            self._certificate,
            self._certificate_snapshot_value,
        )
        frozen = (
            self._coordination_owner_identity,
            self._checkpoint39_certificate_identity,
            self._checkpoint38_owner_identity,
            self._checkpoint38_certificate_identity,
            self._admission_policy_identity,
            self._admission_role_sha256_identity,
            self._certificate_identity,
            self._certificate_snapshot_identity,
        )
        if any(live is not expected for live, expected in zip(current, frozen)):
            raise ValueError("finite-resolution admission owner identity changed")
        callbacks = (
            (self._parent_owner_snapshot, _CP39_OWNER_SNAPSHOT),
            (self._parent_require_owner_snapshot, _CP39_REQUIRE_OWNER_SNAPSHOT),
            (self._parent_live_certificate, _CP39_LIVE_CERTIFICATE),
            (self._parent_coordinate, _CP39_COORDINATE),
            (self._parent_validate_result, _CP39_VALIDATE_RESULT),
            (self._parent_result_preflight, _CP39_PREFLIGHT_RESULT),
            (self._parent_result_tree_snapshot, _CP39_RESULT_TREE_SNAPSHOT),
            (
                self._parent_result_tree_unchanged,
                _CP39_REQUIRE_RESULT_TREE_UNCHANGED,
            ),
            (self._target_builder, _make_target),
            (self._target_validator, _validate_target),
            (self._result_builder, _make_result),
            (self._result_validator, _validate_result_values),
            (self._result_preflight, _preflight_result_record),
            (self._result_tree_snapshotter, _result_tree_snapshot),
            (self._result_tree_unchanged_checker, _require_result_tree_unchanged),
            (self._certificate_validator, _validate_certificate),
            (self._certificate_builder, _make_certificate),
            (self._surface_guard, _require_parent_surfaces),
        )
        if any(live is not expected for live, expected in callbacks):
            raise ValueError("finite-resolution admission cached callback changed")
        return current

    def _owner_snapshot(self) -> Tuple[object, ...]:
        return self._identity_state()

    def _require_owner_snapshot(self, snapshot: Tuple[object, ...]) -> None:
        if type(snapshot) is not tuple or len(snapshot) != 8:
            raise TypeError("finite-resolution admission owner snapshot is malformed")
        current = self._identity_state()
        if any(live is not expected for live, expected in zip(current, snapshot)):
            raise PluginBridgeCounterKeyedInitialTiltRejectionAdmissionError(
                "finite-resolution admission owner changed during operation"
            )

    def _live_certificate(
        self,
        owner_snapshot: Tuple[object, ...],
    ) -> CounterKeyedInitialTiltRejectionAdmissionCertificate:
        self._require_owner_snapshot(owner_snapshot)
        parent_snapshot = self._parent_owner_snapshot(self._coordination_owner)
        parent = self._parent_live_certificate(
            self._coordination_owner, parent_snapshot
        )
        self._parent_require_owner_snapshot(self._coordination_owner, parent_snapshot)
        if parent is not self._checkpoint39_certificate:
            raise ValueError("CP39 live binding substituted its certificate")
        if (
            _CP39_PARENT_PROPERTY.__get__(self._coordination_owner, _CP39_OWNER_TYPE)
            is not self._checkpoint38_owner
        ):
            raise ValueError("CP39 direct CP38 owner changed")
        if (
            _CP38_CERTIFICATE_PROPERTY.__get__(
                self._checkpoint38_owner, _CP38_OWNER_TYPE
            )
            is not self._checkpoint38_certificate
        ):
            raise ValueError("CP38 direct certificate changed")
        certificate = self._certificate_validator(self._certificate)
        _require_certificate_unchanged(certificate, self._certificate_snapshot_value)
        expected = self._certificate_builder(
            self._coordination_owner, self._admission_role_sha256
        )
        for field in _certificate_fields():
            actual = getattr(certificate, field)
            target = getattr(expected, field)
            if field in ("checkpoint39_certificate", "checkpoint38_certificate"):
                if actual is not target:
                    raise ValueError("CP40 certificate.%s identity differs" % field)
            elif type(actual) is not type(target) or actual != target:
                raise ValueError("CP40 certificate.%s differs" % field)
        self._require_owner_snapshot(owner_snapshot)
        return certificate

    def admit(
        self,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedInitializerAdmissionResult:
        """Coordinate CP39 once and apply the fixed-B admission boundary."""

        owner_snapshot = self._owner_snapshot()
        checked_run = _exact_integer(run_id, name="run_id")
        checked_initialization = _exact_integer(
            initialization_index, name="initialization_index"
        )
        certificate = self._live_certificate(owner_snapshot)
        parent_owner_snapshot = self._parent_owner_snapshot(self._coordination_owner)
        parent = self._parent_coordinate(
            self._coordination_owner,
            checked_run,
            checked_initialization,
        )
        self._parent_require_owner_snapshot(
            self._coordination_owner, parent_owner_snapshot
        )
        self._require_owner_snapshot(owner_snapshot)
        certificate = self._live_certificate(owner_snapshot)
        parent = self._parent_result_preflight(
            parent, certificate=certificate.checkpoint39_certificate
        )
        parent_tree = self._parent_result_tree_snapshot(parent)
        checked_parent = self._parent_validate_result(
            self._coordination_owner,
            parent,
            checked_run,
            checked_initialization,
        )
        if checked_parent is not parent:
            raise ValueError("CP39 validation substituted its result")
        self._parent_result_tree_unchanged(
            parent,
            parent_tree,
            certificate=certificate.checkpoint39_certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        certificate = self._live_certificate(owner_snapshot)
        target = self._target_builder(
            certificate, parent.parent_finite_batch_law_result
        )
        result = self._result_builder(certificate, parent, target)
        self._result_validator(
            {name: getattr(result, name) for name in _result_fields()},
            trusted_certificate=certificate,
        )
        self._parent_result_tree_unchanged(
            parent,
            parent_tree,
            certificate=certificate.checkpoint39_certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        self._live_certificate(owner_snapshot)
        return result

    def validate_result(
        self,
        result: object,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedInitializerAdmissionResult:
        """Validate without coordinating or constructing target/result children."""

        owner_snapshot = self._owner_snapshot()
        checked_run = _exact_integer(run_id, name="run_id")
        checked_initialization = _exact_integer(
            initialization_index, name="initialization_index"
        )
        if type(result) is not CounterKeyedInitializerAdmissionResult:
            raise TypeError("result has the wrong exact CP40 admission type")
        stored_run = _exact_integer(result.run_id, name="result.run_id")
        stored_initialization = _exact_integer(
            result.initialization_index,
            name="result.initialization_index",
        )
        if stored_run != checked_run or stored_initialization != checked_initialization:
            raise ValueError("result request coordinates differ")
        _require_certificate_unchanged(
            self._certificate, self._certificate_snapshot_value
        )
        checked = self._result_preflight(result, certificate=self._certificate)
        certificate = self._live_certificate(owner_snapshot)
        result_tree = self._result_tree_snapshotter(checked)
        parent = checked.parent_coordination_result
        parent_tree = self._parent_result_tree_snapshot(parent)
        checked_parent = self._parent_validate_result(
            self._coordination_owner,
            parent,
            checked_run,
            checked_initialization,
        )
        if checked_parent is not parent:
            raise ValueError("CP39 validation substituted its result")
        self._parent_result_tree_unchanged(
            parent,
            parent_tree,
            certificate=certificate.checkpoint39_certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        certificate = self._live_certificate(owner_snapshot)
        self._target_validator(
            checked.finite_resolution_target, certificate=certificate
        )
        self._result_validator(
            {name: getattr(checked, name) for name in _result_fields()},
            trusted_certificate=certificate,
        )
        self._parent_result_tree_unchanged(
            parent,
            parent_tree,
            certificate=certificate.checkpoint39_certificate,
        )
        self._result_tree_unchanged_checker(
            checked,
            result_tree,
            certificate=certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        self._live_certificate(owner_snapshot)
        return checked


def _certify_admission(
    coordination_owner: object,
    *,
    admission_policy: object,
    admission_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionAdmissionOwner:
    if type(coordination_owner) is not _CP39_OWNER_TYPE:
        raise TypeError("coordination_owner has the wrong exact CP39 type")
    _require_parent_surfaces()
    policy = _require_text(admission_policy, _POLICY, name="admission_policy")
    role = _REQUIRE_SHA256(admission_role_sha256, name="admission_role_sha256")
    certificate = _make_certificate(coordination_owner, role)
    owner = CounterKeyedInitialTiltRejectionAdmissionOwner(
        coordination_owner,
        policy,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    snapshot = owner._owner_snapshot()
    owner._live_certificate(snapshot)
    owner._require_owner_snapshot(snapshot)
    return owner


def _require_matching_admission(
    coordination_owner: object,
    owner: object,
    *,
    admission_policy: object,
    admission_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionAdmissionOwner:
    if type(coordination_owner) is not _CP39_OWNER_TYPE:
        raise TypeError("coordination_owner has the wrong exact CP39 type")
    _require_parent_surfaces()
    if type(owner) is not CounterKeyedInitialTiltRejectionAdmissionOwner:
        raise TypeError("owner has the wrong exact CP40 admission type")
    policy = _require_text(admission_policy, _POLICY, name="admission_policy")
    role = _REQUIRE_SHA256(admission_role_sha256, name="admission_role_sha256")
    if owner.coordination_owner is not coordination_owner:
        raise ValueError("admission owner uses another CP39 parent")
    snapshot = owner._owner_snapshot()
    certificate = owner._live_certificate(snapshot)
    if certificate.admission_policy != policy:
        raise ValueError("admission owner uses another policy")
    if certificate.admission_role_sha256 != role:
        raise ValueError("admission owner uses another role")
    owner._require_owner_snapshot(snapshot)
    return owner


_PUBLIC_CERTIFY_NAME = (
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_admission"
)
_PUBLIC_MATCHING_NAME = (
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_admission"
)
_PUBLIC_VALIDATE_CERTIFICATE_NAME = (
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_admission_"
    "certificate"
)
_MAX_WORDS_PER_OCCURRENCE_PUBLIC_NAME = (
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_" "MAX_RAW64_WORDS_PER_OCCURRENCE"
)


_FROZEN_OPERATION_SURFACES = (
    ("Fraction", Fraction),
    ("platform", platform),
    ("sys", sys),
    (
        "PluginBridgeCounterKeyedInitialTiltRejectionAdmissionError",
        PluginBridgeCounterKeyedInitialTiltRejectionAdmissionError,
    ),
    (
        "CounterKeyedInitialTiltRejectionAdmissionCertificate",
        CounterKeyedInitialTiltRejectionAdmissionCertificate,
    ),
    (
        "CounterKeyedInitialTiltRejectionFiniteResolutionTarget",
        CounterKeyedInitialTiltRejectionFiniteResolutionTarget,
    ),
    ("CounterKeyedInitializerAdmissionResult", CounterKeyedInitializerAdmissionResult),
    (
        "CounterKeyedInitialTiltRejectionAdmissionOwner",
        CounterKeyedInitialTiltRejectionAdmissionOwner,
    ),
    (
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_SCHEMA_VERSION",
        PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_SCHEMA_VERSION,
    ),
    (
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_POLICY",
        PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_POLICY,
    ),
    (
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_SCOPE",
        PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_SCOPE,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_FAMILY",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_FAMILY,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_CONDITIONING",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_CONDITIONING,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_ADMISSION_STATUSES",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_ADMISSION_STATUSES,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_CONDITIONED_COMPARISON",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_CONDITIONED_COMPARISON,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_CONDITIONED_COMPARISON_PROOF",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_CONDITIONED_COMPARISON_PROOF,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_DYADIC_DENOMINATOR",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_DYADIC_DENOMINATOR,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_ATTEMPTS",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_ATTEMPTS,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TARGET_CONFIGURATIONS",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TARGET_CONFIGURATIONS,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_CONFIGURATION_EVENTS",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_CONFIGURATION_EVENTS,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_COORDINATES_PER_EVENT",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_COORDINATES_PER_EVENT,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_STREAM_RECORDS",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_STREAM_RECORDS,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_RAW64_WORDS_PER_OCCURRENCE",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_RAW64_WORDS_PER_OCCURRENCE,
    ),
    (
        "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TOTAL_RAW64_WORDS",
        INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TOTAL_RAW64_WORDS,
    ),
)

_FROZEN_PRIVATE_NAMESPACE = tuple(
    sorted(
        (
            (name, value)
            for name, value in globals().items()
            if name.startswith("_") and not name.startswith("__")
        ),
        key=lambda item: item[0],
    )
)


def _bind_public_api(
    certify_impl: object,
    matching_impl: object,
) -> Tuple[object, object, object]:
    namespace = globals()
    late_surfaces: Tuple[Tuple[str, object], ...] = ()

    def require_late_surfaces() -> None:
        for name, expected in late_surfaces:
            if namespace.get(name) is not expected:
                raise ValueError("CP40 late operation surface %s changed" % name)
        _require_parent_surfaces()

    def certify(
        coordination_owner: object,
        *,
        admission_policy: object,
        admission_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionAdmissionOwner:
        require_late_surfaces()
        return certify_impl(
            coordination_owner,
            admission_policy=admission_policy,
            admission_role_sha256=admission_role_sha256,
        )

    def matching(
        coordination_owner: object,
        owner: object,
        *,
        admission_policy: object,
        admission_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionAdmissionOwner:
        require_late_surfaces()
        return matching_impl(
            coordination_owner,
            owner,
            admission_policy=admission_policy,
            admission_role_sha256=admission_role_sha256,
        )

    def validate(
        coordination_owner: object,
        owner: object,
        *,
        admission_policy: object,
        admission_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionAdmissionCertificate:
        return matching(
            coordination_owner,
            owner,
            admission_policy=admission_policy,
            admission_role_sha256=admission_role_sha256,
        ).certificate

    late_surfaces = (
        ("_certify_admission", certify_impl),
        ("_require_matching_admission", matching_impl),
        ("_require_parent_surfaces", _require_parent_surfaces),
        (
            "CounterKeyedInitialTiltRejectionAdmissionOwner",
            CounterKeyedInitialTiltRejectionAdmissionOwner,
        ),
        (_PUBLIC_CERTIFY_NAME, certify),
        (_PUBLIC_MATCHING_NAME, matching),
        (_PUBLIC_VALIDATE_CERTIFICATE_NAME, validate),
    )
    return certify, matching, validate


def _require_parent_surfaces(
    dependency_guard: object = _require_dependency_surfaces,
    frozen: Tuple[Tuple[str, object], ...] = _FROZEN_OPERATION_SURFACES,
    private_namespace: Tuple[Tuple[str, object], ...] = _FROZEN_PRIVATE_NAMESPACE,
) -> None:
    namespace = globals()
    if namespace.get("_require_dependency_surfaces") is not dependency_guard:
        raise ValueError("finite-resolution admission dependency guard changed")
    if namespace.get("_FROZEN_OPERATION_SURFACES") is not frozen:
        raise ValueError("finite-resolution admission frozen surfaces changed")
    if namespace.get("_FROZEN_PRIVATE_NAMESPACE") is not private_namespace:
        raise ValueError("finite-resolution admission namespace snapshot changed")
    for name, expected in frozen + private_namespace:
        if namespace.get(name) is not expected:
            raise ValueError("finite-resolution admission surface %s changed" % name)
    dependency_guard()


_PUBLIC_FUNCTIONS = _bind_public_api(_certify_admission, _require_matching_admission)
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
    globals()[_public_name] = _public_function


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_ADMISSION_SCOPE",
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_FAMILY",
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_TARGET_CONDITIONING",
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_ADMISSION_STATUSES",
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_CONDITIONED_COMPARISON",
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_CONDITIONED_COMPARISON_PROOF",
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_DYADIC_DENOMINATOR",
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_ATTEMPTS",
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TARGET_CONFIGURATIONS",
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_CONFIGURATION_EVENTS",
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_COORDINATES_PER_EVENT",
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_STREAM_RECORDS",
    _MAX_WORDS_PER_OCCURRENCE_PUBLIC_NAME,
    "INITIAL_TILT_REJECTION_FINITE_RESOLUTION_MAX_TOTAL_RAW64_WORDS",
    "CounterKeyedInitialTiltRejectionAdmissionCertificate",
    "CounterKeyedInitialTiltRejectionFiniteResolutionTarget",
    "CounterKeyedInitializerAdmissionResult",
    "CounterKeyedInitialTiltRejectionAdmissionOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionAdmissionError",
    _PUBLIC_CERTIFY_NAME,
    _PUBLIC_MATCHING_NAME,
    _PUBLIC_VALIDATE_CERTIFICATE_NAME,
]
