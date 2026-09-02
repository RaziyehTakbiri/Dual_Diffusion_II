"""Attach bootstrap lineage and initialization-indexed tag-3 prefixes to CP38.

Checkpoint thirty-eight returns either one structurally valid selected
configuration or bounded exhaustion.  This additive successor coordinates the
selected branch with checkpoint twenty-three bootstrap lineage and with a
local tag-3 prefix for every selected occurrence.  Exhaustion remains a valid
no-state result: it invokes no composer preflight or lineage bootstrap and it
creates no result tag-3 address, stream, or prefix.  Live-binding runtime
probes are separate procedural checks and still execute.

The local address is deliberately not checkpoint twenty-three's address DTO.
For selected attempt ``j`` and bootstrap lineage serial ``s`` it is exactly

``key=(run_id, 3), counter=(0, initialization_index, s, j + 1)``.

Consequently the address contains every initialization index accepted by the
uint64 API, distinguishes selected attempts, and has a positive final counter
limb.  It is therefore disjoint from the legacy checkpoint-twenty-three tag-3
reservation ``counter=(0, step_index, s, 0)``.  This is an address-layout and
same-runtime deterministic-prefix statement only.  It is not a statistical
independence, physical-randomness, one-shot-use, payload-semantics, or live-law
claim.

Word counts are shape-only metadata: an occurrence of manifest dimension
``d`` receives ``max(1, d)`` uninterpreted raw uint64 words.  Those words do
not generate, alter, or semantically explain the already selected event.

The owner is certified from one exact CP38 owner.  CP37, CP36, CP28, CP27,
CP26, CP25, CP23, the finite manifest, and the reference composer are derived
transitively from that ancestry; callers cannot splice them in separately.
Hashes are process-local custody witnesses under a trusted unchanged runtime,
not cryptographic authentication or loaded-code integrity evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

import numpy as np

try:
    from heterodiff.processes import plugin_bridge_sampler as _sampler
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_initial_tilt_rejection_finite_batch_law as _law,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "rejection lineage/tag-3 coordination requires the optional "
            "PyTorch reference dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.theory.configuration_reference import (
    TransformedConfiguration,
    TransformedEvent,
)


_SCHEMA_VERSION_VALUE = (
    "plugin-bridge-counter-keyed-initial-tilt-rejection-lineage-tag3-" "coordination-v1"
)
_PUBLIC_SCHEMA_NAME = (
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_LINEAGE_TAG3_"
    "COORDINATION_SCHEMA_VERSION"
)
globals()[_PUBLIC_SCHEMA_NAME] = _SCHEMA_VERSION_VALUE
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_LINEAGE_TAG3_COORDINATION_POLICY = (
    "exact-checkpoint38-owner-and-transitive-37-36-28-27-26-25-23-binding;"
    "one-parent-resolve;exhaustion-no-state-no-selected-branch-construction;"
    "selected-exact-configuration-and-attempt;initial-intensity-at-reverse-time-zero;"
    "checkpoint23-bootstrap-lineage;local-initialization-indexed-tag3-prefix;"
    "key-run-tag3-counter-zero-initialization-serial-attempt-plus-one;"
    "manifest-dimension-shaped-positive-word-count;bounded-prefix-replay;"
    "no-checkpoint23-address-dto-or-checkpoint25-consume;"
    "no-caller-rng-retry-fallback-rollback-or-payload-interpretation-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_LINEAGE_TAG3_COORDINATION_SCOPE = (
    "bounded-selected-state-lineage-and-uninterpreted-tag3-prefix-coordination;"
    "all-valid-uint64-run-and-initialization-indices;"
    "initialization-attempt-serial-injective-address-layout;"
    "positive-suffix-disjoint-from-legacy-tag3-suffix-zero;"
    "same-address-live-replay-is-deterministic;"
    "exhaustion-is-valid-no-state-and-operational-failure-remains-distinct;"
    "not-live-initializer-law-uniformity-independence-or-physical-randomness;"
    "not-one-shot-use-cross-bootstrap-merge-or-fork-safety;"
    "not-payload-semantics-or-coordinate-generation;"
    "not-tv-after-selection-conditioning-or-normalized-global-tilt;"
    "not-brownian-drift-path-liveness-or-full-sampler;"
    "trusted-runtime-procedural-not-portable-or-cryptographic-custody"
)

INITIAL_TILT_REJECTION_LINEAGE_TAG3_DOMAIN_TAG = 3
INITIAL_TILT_REJECTION_LINEAGE_TAG3_INITIAL_REVERSE_TIME = 0.0
INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_STREAM_RECORDS = 64
INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE = 4_096
INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_TOTAL_RAW64_WORDS = 65_536
INITIAL_TILT_REJECTION_LINEAGE_TAG3_ADDRESS_LAYOUT = (
    "key=(run_id,3);counter=(0,initialization_index,lineage_serial,"
    "selected_attempt_index+1)"
)
INITIAL_TILT_REJECTION_LINEAGE_TAG3_WORD_COUNT_POLICY = (
    "max(1,checkpoint28-manifest-dimension-of-selected-event-type)"
)
INITIAL_TILT_REJECTION_LINEAGE_TAG3_OUTCOMES = ("selected", "exhausted")

_SCHEMA_VERSION = _SCHEMA_VERSION_VALUE
_POLICY = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_LINEAGE_TAG3_COORDINATION_POLICY
)
_SCOPE = (
    PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_LINEAGE_TAG3_COORDINATION_SCOPE
)
_ZERO_SHA256 = "0" * 64
_MAX_TEXT_LENGTH = 16_384
_MAX_UINT64 = (1 << 64) - 1

_CERTIFICATE_TOKEN = object()
_ADDRESS_TOKEN = object()
_STREAM_TOKEN = object()
_OCCURRENCE_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()

# The only imported checkpoint owner is CP38.  Every earlier owner below is
# reached through the exact frozen transitive module/owner ancestry.
_CP38_OWNER_TYPE = _law.CounterKeyedInitialTiltRejectionFiniteBatchLawOwner
_CP38_CERT_TYPE = _law.CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate
_CP38_RESULT_TYPE = _law.CounterKeyedInitialTiltRejectionFiniteBatchLawResult
_CP38_OWNER_SNAPSHOT = _CP38_OWNER_TYPE._owner_snapshot
_CP38_REQUIRE_OWNER_SNAPSHOT = _CP38_OWNER_TYPE._require_owner_snapshot
_CP38_LIVE_CERTIFICATE = _CP38_OWNER_TYPE._live_certificate
_CP38_RESOLVE = _CP38_OWNER_TYPE.resolve
_CP38_VALIDATE_RESULT = _CP38_OWNER_TYPE.validate_result
_CP38_CERTIFICATE_PROPERTY = _CP38_OWNER_TYPE.certificate
_CP38_DECISION_PROPERTY = _CP38_OWNER_TYPE.decision_owner
_CP38_PREFLIGHT_RESULT = _law._preflight_result_record
_CP38_RESULT_FIELDS = _law._result_fields
_CP38_RESULT_TREE_SNAPSHOT = _law._result_tree_snapshot
_CP38_REQUIRE_RESULT_TREE_UNCHANGED = _law._require_result_tree_unchanged
_CP38_VALIDATE_CERTIFICATE = _law._validate_certificate

_decision = _law._decision
_preparation = _decision._prep
_reference = _preparation._reference
_protocol = _reference._protocol
_control = _protocol._control
_consumption = _control._consumption
_lineage = _control._lineage
_route = _lineage._route_evidence
_thinning = _protocol._thinning

_CP37_OWNER_TYPE = _decision.CounterKeyedInitialTiltRejectionDecisionOwner
_CP37_PREPARATION_PROPERTY = _CP37_OWNER_TYPE.preparation_owner
_CP36_OWNER_TYPE = _preparation.CounterKeyedInitialTiltRejectionPreparationOwner
_CP36_REFERENCE_PROPERTY = _CP36_OWNER_TYPE.reference_initializer_owner
_CP28_OWNER_TYPE = _reference.CounterKeyedReferenceInitializerOwner
_CP28_CERT_TYPE = _reference.CounterKeyedReferenceInitializerCertificate
_CP28_PROTOCOL_PROPERTY = _CP28_OWNER_TYPE.protocol_owner
_CP28_CERTIFICATE_PROPERTY = _CP28_OWNER_TYPE.certificate
_CP28_MANIFEST_PROPERTY = _CP28_OWNER_TYPE.manifest
_CP28_LIVE = _CP28_OWNER_TYPE._require_live_binding
_CP28_VALIDATE_MANIFEST = _reference._validate_manifest
_CP28_VALIDATE_CERTIFICATE = _reference._validate_certificate
_CP27_OWNER_TYPE = _protocol.CounterKeyedInitializerProtocolOwner
_CP27_CERT_TYPE = _protocol.CounterKeyedInitializerProtocolCertificate
_CP27_CONTROL_PROPERTY = _CP27_OWNER_TYPE.control_owner
_CP27_CERTIFICATE_PROPERTY = _CP27_OWNER_TYPE.certificate
_CP27_LIVE = _CP27_OWNER_TYPE._require_live_binding
_CP27_VALIDATE_CERTIFICATE = _protocol._validate_certificate
_CP26_OWNER_TYPE = _control.CounterKeyedGlobalInitializerControlOwner
_CP26_CERT_TYPE = _control.CounterKeyedGlobalInitializerControlCertificate
_CP26_CONSUMPTION_PROPERTY = _CP26_OWNER_TYPE.consumption_owner
_CP26_CONTRACT_PROPERTY = _CP26_OWNER_TYPE.contract_owner
_CP26_CERTIFICATE_PROPERTY = _CP26_OWNER_TYPE.certificate
_CP26_LIVE = _CP26_OWNER_TYPE._require_live_binding
_CP26_VALIDATE_CERTIFICATE = _control._validate_certificate
_CP25_OWNER_TYPE = _consumption.CounterKeyedInitializerStreamConsumptionOwner
_CP25_CERT_TYPE = _consumption.CounterKeyedInitializerStreamConsumptionCertificate
_CP25_CONTRACT_PROPERTY = _CP25_OWNER_TYPE.contract_owner
_CP25_CERTIFICATE_PROPERTY = _CP25_OWNER_TYPE.certificate
_CP25_LIVE = _CP25_OWNER_TYPE._require_live_binding
_CP25_VALIDATE_CERTIFICATE = _consumption._validate_certificate
_CP23_OWNER_TYPE = _lineage.CounterKeyedLineageContractOwner
_CP23_CERT_TYPE = _lineage.CounterKeyedLineageCertificate
_CP23_CERTIFICATE_PROPERTY = _CP23_OWNER_TYPE.certificate
_CP23_COMPOSER_PROPERTY = _CP23_OWNER_TYPE.reference_composer
_CP23_LIVE = _CP23_OWNER_TYPE._require_live_binding
_CP23_BOOTSTRAP = _CP23_OWNER_TYPE.bootstrap_lineage
_CP23_VALIDATE_STATE = _lineage._validate_state
_CP23_VALIDATE_CERTIFICATE = _lineage._validate_certificate
_CP23_STATE_FIELDS = _lineage._state_fields
_CP23_OCCURRENCE_FIELDS = _lineage._occurrence_fields
_CP23_IDENTIFIER_FIELDS = _lineage._identifier_fields

_COMPOSER_TYPE = _preparation._COMPOSER_TYPE
_COMPOSER_PREFLIGHT = _COMPOSER_TYPE.preflight_candidate_intensity
_COMPOSER_VALIDATE_INTENSITY = _COMPOSER_TYPE.validate_candidate_intensity
_COMPOSER_LIVE = _COMPOSER_TYPE._require_live_binding
_REFERENCE_ANCESTRY = _reference._reference_ancestry
_PROCESS_PARAMETER_SHA256 = _reference._process_parameter_sha256
_SEMANTIC_DIGEST = _thinning._semantic_digest
_REQUIRE_SHA256 = _thinning._require_sha256
_CAPTURE_ROUTE_STATE = _route._capture_philox_state
_VALIDATE_ROUTE_STATE = _route._validate_snapshot
_ROUTE_STATE_FIELDS = _route._snapshot_fields
_INTENSITY_TYPE = _sampler.ReferenceCandidateIntensity
_REQUIRE_INTENSITY_REPRESENTATION = _sampler._require_exact_intensity_representation
_CONFIGURATION_SHA256 = _preparation._CP28_CONFIGURATION_SHA256
_EVENT_MODEL_KEY = TransformedEvent.model_key


class PluginBridgeCounterKeyedInitialTiltRejectionLineageTag3CoordinationError(
    ArithmeticError
):
    """Fail-closed checkpoint-thirty-nine coordination error."""


_COORDINATION_ERROR_TYPE = (
    PluginBridgeCounterKeyedInitialTiltRejectionLineageTag3CoordinationError
)


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


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("%s must be exact text" % name)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be lowercase SHA-256 hexadecimal text" % name)
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


def _record_snapshot(record: object, fields: Tuple[str, ...]) -> Tuple[object, ...]:
    return tuple(getattr(record, field) for field in fields)


def _require_record_unchanged(
    record: object,
    fields: Tuple[str, ...],
    before: Tuple[object, ...],
    *,
    identity_fields: Tuple[str, ...],
    name: str,
) -> None:
    if type(before) is not tuple or len(before) != len(fields):
        raise TypeError("%s snapshot is malformed" % name)
    for field, expected in zip(fields, before):
        actual = getattr(record, field)
        if field in identity_fields:
            if actual is not expected:
                raise ValueError("%s.%s changed identity" % (name, field))
        elif type(actual) is not type(expected) or actual != expected:
            raise ValueError("%s.%s changed" % (name, field))


def _runtime_sha256() -> str:
    if (
        INITIAL_TILT_REJECTION_LINEAGE_TAG3_DOMAIN_TAG != 3
        or INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_STREAM_RECORDS != 64
        or INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE != 4_096
        or INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_TOTAL_RAW64_WORDS != 65_536
    ):
        raise ValueError("lineage/tag-3 resource constants changed")
    generator = np.random.Generator(
        np.random.Philox(
            key=np.asarray((7, 3), dtype=np.uint64),
            counter=np.asarray((0, 11, 2, 5), dtype=np.uint64),
        )
    )
    initial = _CAPTURE_ROUTE_STATE(generator)
    words = tuple(
        int(value) for value in np.atleast_1d(generator.bit_generator.random_raw(3))
    )
    final = _CAPTURE_ROUTE_STATE(generator)
    return _SEMANTIC_DIGEST(
        {
            "domain": "initial-tilt-rejection-lineage-tag3-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "numpy_version": np.__version__,
            "philox_type_module": np.random.Philox.__module__,
            "philox_type_name": np.random.Philox.__name__,
            "address_layout": INITIAL_TILT_REJECTION_LINEAGE_TAG3_ADDRESS_LAYOUT,
            "word_count_policy": (
                INITIAL_TILT_REJECTION_LINEAGE_TAG3_WORD_COUNT_POLICY
            ),
            "maximum_records": (INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_STREAM_RECORDS),
            "maximum_words_per_occurrence": (
                INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE
            ),
            "maximum_total_words": (
                INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_TOTAL_RAW64_WORDS
            ),
            "probe_initial_sha256": initial.snapshot_sha256,
            "probe_words": words,
            "probe_final_sha256": final.snapshot_sha256,
            "policy": _POLICY,
            "scope": _SCOPE,
        }
    )


@dataclass(frozen=True)
class _Ancestry:
    checkpoint37_owner: _CP37_OWNER_TYPE
    checkpoint36_owner: _CP36_OWNER_TYPE
    checkpoint28_owner: _CP28_OWNER_TYPE
    checkpoint27_owner: _CP27_OWNER_TYPE
    checkpoint26_owner: _CP26_OWNER_TYPE
    checkpoint25_owner: _CP25_OWNER_TYPE
    checkpoint23_owner: _CP23_OWNER_TYPE
    reference_composer: _COMPOSER_TYPE
    manifest: object
    process: object
    reference: object


def _direct_ancestry(
    finite_batch_law_owner: object,
    *,
    custody_check: Optional[object] = None,
) -> _Ancestry:
    if type(finite_batch_law_owner) is not _CP38_OWNER_TYPE:
        raise TypeError("finite_batch_law_owner has the wrong exact CP38 type")

    def require_custody() -> None:
        if custody_check is not None:
            if not callable(custody_check):
                raise TypeError("custody_check must be callable")
            custody_check()

    cp38_snapshot = _CP38_OWNER_SNAPSHOT(finite_batch_law_owner)
    cp38 = _CP38_LIVE_CERTIFICATE(finite_batch_law_owner, cp38_snapshot)
    require_custody()
    _CP38_REQUIRE_OWNER_SNAPSHOT(finite_batch_law_owner, cp38_snapshot)
    if cp38 is not _CP38_CERTIFICATE_PROPERTY.__get__(
        finite_batch_law_owner, _CP38_OWNER_TYPE
    ):
        raise ValueError("CP38 live binding substituted its certificate")
    checkpoint37 = _CP38_DECISION_PROPERTY.__get__(
        finite_batch_law_owner, _CP38_OWNER_TYPE
    )
    if type(checkpoint37) is not _CP37_OWNER_TYPE:
        raise TypeError("CP38 decision owner has the wrong exact CP37 type")
    checkpoint36 = _CP37_PREPARATION_PROPERTY.__get__(checkpoint37, _CP37_OWNER_TYPE)
    if type(checkpoint36) is not _CP36_OWNER_TYPE:
        raise TypeError("CP37 preparation owner has the wrong exact CP36 type")
    checkpoint28 = _CP36_REFERENCE_PROPERTY.__get__(checkpoint36, _CP36_OWNER_TYPE)
    if type(checkpoint28) is not _CP28_OWNER_TYPE:
        raise TypeError("CP36 reference owner has the wrong exact CP28 type")
    live28 = _CP28_LIVE(checkpoint28)
    require_custody()
    if live28 is not _CP28_CERTIFICATE_PROPERTY.__get__(checkpoint28, _CP28_OWNER_TYPE):
        raise ValueError("CP28 live binding substituted its certificate")
    checkpoint27 = _CP28_PROTOCOL_PROPERTY.__get__(checkpoint28, _CP28_OWNER_TYPE)
    if type(checkpoint27) is not _CP27_OWNER_TYPE:
        raise TypeError("CP28 protocol owner has the wrong exact CP27 type")
    live27 = _CP27_LIVE(checkpoint27)
    require_custody()
    if live27 is not _CP27_CERTIFICATE_PROPERTY.__get__(checkpoint27, _CP27_OWNER_TYPE):
        raise ValueError("CP27 live binding substituted its certificate")
    checkpoint26 = _CP27_CONTROL_PROPERTY.__get__(checkpoint27, _CP27_OWNER_TYPE)
    if type(checkpoint26) is not _CP26_OWNER_TYPE:
        raise TypeError("CP27 control owner has the wrong exact CP26 type")
    live26 = _CP26_LIVE(checkpoint26)
    require_custody()
    if live26 is not _CP26_CERTIFICATE_PROPERTY.__get__(checkpoint26, _CP26_OWNER_TYPE):
        raise ValueError("CP26 live binding substituted its certificate")
    checkpoint25 = _CP26_CONSUMPTION_PROPERTY.__get__(checkpoint26, _CP26_OWNER_TYPE)
    if type(checkpoint25) is not _CP25_OWNER_TYPE:
        raise TypeError("CP26 consumption owner has the wrong exact CP25 type")
    live25 = _CP25_LIVE(checkpoint25)
    require_custody()
    if live25 is not _CP25_CERTIFICATE_PROPERTY.__get__(checkpoint25, _CP25_OWNER_TYPE):
        raise ValueError("CP25 live binding substituted its certificate")
    checkpoint23 = _CP26_CONTRACT_PROPERTY.__get__(checkpoint26, _CP26_OWNER_TYPE)
    if type(checkpoint23) is not _CP23_OWNER_TYPE:
        raise TypeError("CP26 contract owner has the wrong exact CP23 type")
    live23 = _CP23_LIVE(checkpoint23)
    require_custody()
    if live23 is not _CP23_CERTIFICATE_PROPERTY.__get__(checkpoint23, _CP23_OWNER_TYPE):
        raise ValueError("CP23 live binding substituted its certificate")
    if _CP25_CONTRACT_PROPERTY.__get__(checkpoint25, _CP25_OWNER_TYPE) is not (
        checkpoint23
    ):
        raise ValueError("CP25 and CP26 lineage owners differ")
    composer = _CP23_COMPOSER_PROPERTY.__get__(checkpoint23, _CP23_OWNER_TYPE)
    if type(composer) is not _COMPOSER_TYPE:
        raise TypeError("CP23 reference composer has the wrong exact type")
    _COMPOSER_LIVE(composer)
    require_custody()
    ancestry_composer, process, reference = _REFERENCE_ANCESTRY(checkpoint27)
    require_custody()
    if ancestry_composer is not composer:
        raise ValueError("CP23 and CP28 reference composers differ")
    manifest = _CP28_MANIFEST_PROPERTY.__get__(checkpoint28, _CP28_OWNER_TYPE)
    checked_manifest = _CP28_VALIDATE_MANIFEST(manifest)
    require_custody()
    if checked_manifest is not manifest:
        raise ValueError("CP28 manifest validation substituted its record")
    if manifest.reference is not reference:
        raise ValueError("CP28 manifest uses another reference ancestry")
    if cp38.process_parameter_sha256 != _PROCESS_PARAMETER_SHA256(process):
        raise ValueError("CP38 process digest differs from reference ancestry")
    _CP38_REQUIRE_OWNER_SNAPSHOT(finite_batch_law_owner, cp38_snapshot)
    require_custody()
    return _Ancestry(
        checkpoint37,
        checkpoint36,
        checkpoint28,
        checkpoint27,
        checkpoint26,
        checkpoint25,
        checkpoint23,
        composer,
        manifest,
        process,
        reference,
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "checkpoint38_certificate",
        "checkpoint28_certificate",
        "checkpoint27_certificate",
        "checkpoint26_certificate",
        "checkpoint25_certificate",
        "checkpoint23_certificate",
        "manifest",
        "certificate_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate:
    """Sealed CP38-bound lineage and local tag-3 coordination certificate."""

    schema_version: str
    certificate_scope: str
    coordination_policy: str
    coordination_role_sha256: str
    checkpoint38_certificate: _CP38_CERT_TYPE
    checkpoint38_certificate_sha256: str
    checkpoint38_runtime_sha256: str
    checkpoint38_owner_runtime_identity: int
    checkpoint28_certificate: object
    checkpoint28_certificate_sha256: str
    checkpoint27_certificate: object
    checkpoint27_certificate_sha256: str
    checkpoint26_certificate: object
    checkpoint26_certificate_sha256: str
    checkpoint25_certificate: object
    checkpoint25_certificate_sha256: str
    checkpoint23_certificate: object
    checkpoint23_certificate_sha256: str
    checkpoint23_owner_runtime_identity: int
    reference_composer_runtime_identity: int
    process_parameter_sha256: str
    manifest: object
    manifest_sha256: str
    tag3_domain_tag: int
    initial_reverse_time: float
    address_layout: str
    word_count_policy: str
    maximum_stream_records: int
    maximum_raw64_words_per_occurrence: int
    maximum_total_raw64_words: int
    coordination_runtime_sha256: str
    exact_checkpoint38_owner_binding_certified: bool
    transitive_checkpoint37_to_checkpoint23_ancestry_certified: bool
    exactly_one_parent_resolve_call_certified: bool
    exhaustion_no_state_no_selected_branch_construction_certified: bool
    selected_exact_configuration_and_attempt_binding_certified: bool
    initial_intensity_at_reverse_time_zero_certified: bool
    checkpoint23_bootstrap_lineage_certified: bool
    initialization_index_in_tag3_address_certified: bool
    selected_attempt_index_in_tag3_address_certified: bool
    lineage_serial_in_tag3_address_certified: bool
    initialization_attempt_serial_address_injectivity_certified: bool
    legacy_tag3_suffix_zero_disjointness_certified: bool
    dimension_shaped_positive_prefix_certified: bool
    exact_local_prefix_replay_certified: bool
    bounded_fail_fast_preflight_certified: bool
    no_checkpoint23_address_dto_certified: bool
    no_checkpoint25_consume_certified: bool
    no_caller_rng_certified: bool
    deterministic_replay_certified: bool
    passed: bool
    initializer_output_admitted: bool
    initializer_admissible: bool
    live_initializer_law_certified: bool
    live_uniformity_certified: bool
    live_independence_certified: bool
    physical_randomness_certified: bool
    global_address_one_shot_use_certified: bool
    cross_bootstrap_merge_safety_certified: bool
    lineage_fork_prevention_certified: bool
    tag3_payload_semantics_certified: bool
    tag3_words_generate_selected_coordinates_certified: bool
    success_conditioned_ideal_tv_comparison_certified: bool
    normalized_global_tilted_law_certified: bool
    brownian_stream_consumption_certified: bool
    continuous_drift_admissible: bool
    path_admissible: bool
    full_sampler_admissible: bool
    sampler_liveness_certified: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("lineage/tag-3 certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("lineage/tag-3 certificates are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("lineage/tag-3 certificate fields are incomplete")
        _validate_certificate_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("lineage/tag-3 certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(
        getattr(
            CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
            "__annotations__",
        )
    )


_CERTIFICATE_POSITIVE_FLAGS = (
    "exact_checkpoint38_owner_binding_certified",
    "transitive_checkpoint37_to_checkpoint23_ancestry_certified",
    "exactly_one_parent_resolve_call_certified",
    "exhaustion_no_state_no_selected_branch_construction_certified",
    "selected_exact_configuration_and_attempt_binding_certified",
    "initial_intensity_at_reverse_time_zero_certified",
    "checkpoint23_bootstrap_lineage_certified",
    "initialization_index_in_tag3_address_certified",
    "selected_attempt_index_in_tag3_address_certified",
    "lineage_serial_in_tag3_address_certified",
    "initialization_attempt_serial_address_injectivity_certified",
    "legacy_tag3_suffix_zero_disjointness_certified",
    "dimension_shaped_positive_prefix_certified",
    "exact_local_prefix_replay_certified",
    "bounded_fail_fast_preflight_certified",
    "no_checkpoint23_address_dto_certified",
    "no_checkpoint25_consume_certified",
    "no_caller_rng_certified",
    "deterministic_replay_certified",
    "passed",
)
_CERTIFICATE_NEGATIVE_FLAGS = (
    "initializer_output_admitted",
    "initializer_admissible",
    "live_initializer_law_certified",
    "live_uniformity_certified",
    "live_independence_certified",
    "physical_randomness_certified",
    "global_address_one_shot_use_certified",
    "cross_bootstrap_merge_safety_certified",
    "lineage_fork_prevention_certified",
    "tag3_payload_semantics_certified",
    "tag3_words_generate_selected_coordinates_certified",
    "success_conditioned_ideal_tv_comparison_certified",
    "normalized_global_tilted_law_certified",
    "brownian_stream_consumption_certified",
    "continuous_drift_admissible",
    "path_admissible",
    "full_sampler_admissible",
    "sampler_liveness_certified",
    "runtime_portable",
    "cryptographic_authentication",
)


def _validate_certificate_values(values: Mapping[str, object]) -> None:
    for name, expected in (
        ("schema_version", _SCHEMA_VERSION),
        ("certificate_scope", _SCOPE),
        ("coordination_policy", _POLICY),
        ("address_layout", INITIAL_TILT_REJECTION_LINEAGE_TAG3_ADDRESS_LAYOUT),
        ("word_count_policy", INITIAL_TILT_REJECTION_LINEAGE_TAG3_WORD_COUNT_POLICY),
    ):
        _require_text(values[name], expected, name="certificate.%s" % name)
    for name in (
        "coordination_role_sha256",
        "checkpoint38_certificate_sha256",
        "checkpoint38_runtime_sha256",
        "checkpoint28_certificate_sha256",
        "checkpoint27_certificate_sha256",
        "checkpoint26_certificate_sha256",
        "checkpoint25_certificate_sha256",
        "checkpoint23_certificate_sha256",
        "process_parameter_sha256",
        "manifest_sha256",
        "coordination_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(values[name], name="certificate.%s" % name)
    checkpoint38 = _CP38_VALIDATE_CERTIFICATE(values["checkpoint38_certificate"])
    if values["checkpoint38_certificate_sha256"] != checkpoint38.certificate_sha256:
        raise ValueError("certificate CP38 digest differs")
    parent_bindings = (
        (
            "checkpoint28_certificate",
            "checkpoint28_certificate_sha256",
            _CP28_CERT_TYPE,
            _CP28_VALIDATE_CERTIFICATE,
        ),
        (
            "checkpoint27_certificate",
            "checkpoint27_certificate_sha256",
            _CP27_CERT_TYPE,
            _CP27_VALIDATE_CERTIFICATE,
        ),
        (
            "checkpoint26_certificate",
            "checkpoint26_certificate_sha256",
            _CP26_CERT_TYPE,
            _CP26_VALIDATE_CERTIFICATE,
        ),
        (
            "checkpoint25_certificate",
            "checkpoint25_certificate_sha256",
            _CP25_CERT_TYPE,
            _CP25_VALIDATE_CERTIFICATE,
        ),
        (
            "checkpoint23_certificate",
            "checkpoint23_certificate_sha256",
            _CP23_CERT_TYPE,
            _CP23_VALIDATE_CERTIFICATE,
        ),
    )
    checked_parents = {}
    for object_name, digest_name, exact_type, validator in parent_bindings:
        parent = values[object_name]
        if type(parent) is not exact_type:
            raise TypeError("certificate.%s has the wrong exact type" % object_name)
        checked_parent = validator(parent)
        if checked_parent is not parent:
            raise ValueError("certificate.%s validation substituted" % object_name)
        checked_parents[object_name] = checked_parent
        if values[digest_name] != parent.certificate_sha256:
            raise ValueError("certificate %s digest differs" % object_name)
    cp28 = checked_parents["checkpoint28_certificate"]
    cp27 = checked_parents["checkpoint27_certificate"]
    cp26 = checked_parents["checkpoint26_certificate"]
    cp25 = checked_parents["checkpoint25_certificate"]
    cp23 = checked_parents["checkpoint23_certificate"]
    preparation = checkpoint38.decision_certificate.preparation_certificate
    if preparation.checkpoint28_certificate is not cp28:
        raise ValueError("certificate CP38-to-CP28 identity differs")
    if preparation.checkpoint27_certificate is not cp27:
        raise ValueError("certificate CP38-to-CP27 identity differs")
    if cp28.checkpoint27_certificate is not cp27:
        raise ValueError("certificate CP28-to-CP27 identity differs")
    if cp27.checkpoint26_certificate is not cp26:
        raise ValueError("certificate CP27-to-CP26 identity differs")
    if cp26.checkpoint25_certificate is not cp25:
        raise ValueError("certificate CP26-to-CP25 identity differs")
    if cp25.checkpoint23_certificate is not cp23:
        raise ValueError("certificate CP25-to-CP23 identity differs")
    for name in (
        "checkpoint38_owner_runtime_identity",
        "checkpoint23_owner_runtime_identity",
        "reference_composer_runtime_identity",
    ):
        _exact_integer(values[name], name="certificate.%s" % name, minimum=1)
    manifest = _CP28_VALIDATE_MANIFEST(values["manifest"])
    if manifest is not cp28.manifest:
        raise ValueError("certificate manifest identity differs from CP28")
    if values["manifest_sha256"] != manifest.manifest_sha256:
        raise ValueError("certificate manifest digest differs")
    expected_scalars = {
        "process_parameter_sha256": checkpoint38.process_parameter_sha256,
        "checkpoint38_runtime_sha256": checkpoint38.law_runtime_sha256,
        "tag3_domain_tag": INITIAL_TILT_REJECTION_LINEAGE_TAG3_DOMAIN_TAG,
        "initial_reverse_time": (
            INITIAL_TILT_REJECTION_LINEAGE_TAG3_INITIAL_REVERSE_TIME
        ),
        "maximum_stream_records": (
            INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_STREAM_RECORDS
        ),
        "maximum_raw64_words_per_occurrence": (
            INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE
        ),
        "maximum_total_raw64_words": (
            INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_TOTAL_RAW64_WORDS
        ),
        "coordination_runtime_sha256": _runtime_sha256(),
    }
    for name, expected in expected_scalars.items():
        actual = values[name]
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError("certificate.%s differs" % name)
    for name in _CERTIFICATE_POSITIVE_FLAGS:
        _exact_bool(values[name], True, name="certificate.%s" % name)
    for name in _CERTIFICATE_NEGATIVE_FLAGS:
        _exact_bool(values[name], False, name="certificate.%s" % name)
    if values["certificate_sha256"] != _SEMANTIC_DIGEST(_certificate_payload(values)):
        raise ValueError("lineage/tag-3 certificate digest differs")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate:
    if (
        type(certificate)
        is not CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    ):
        raise TypeError("certificate has the wrong exact lineage/tag-3 type")
    _validate_certificate_values(
        {name: getattr(certificate, name) for name in _certificate_fields()}
    )
    return certificate


def _make_certificate(
    finite_batch_law_owner: _CP38_OWNER_TYPE,
    ancestry: _Ancestry,
    coordination_role_sha256: str,
) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate:
    cp38 = _CP38_CERTIFICATE_PROPERTY.__get__(finite_batch_law_owner, _CP38_OWNER_TYPE)
    cp28 = _CP28_CERTIFICATE_PROPERTY.__get__(
        ancestry.checkpoint28_owner, _CP28_OWNER_TYPE
    )
    cp27 = _CP27_CERTIFICATE_PROPERTY.__get__(
        ancestry.checkpoint27_owner, _CP27_OWNER_TYPE
    )
    cp26 = _CP26_CERTIFICATE_PROPERTY.__get__(
        ancestry.checkpoint26_owner, _CP26_OWNER_TYPE
    )
    cp25 = _CP25_CERTIFICATE_PROPERTY.__get__(
        ancestry.checkpoint25_owner, _CP25_OWNER_TYPE
    )
    cp23 = _CP23_CERTIFICATE_PROPERTY.__get__(
        ancestry.checkpoint23_owner, _CP23_OWNER_TYPE
    )
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate_scope": _SCOPE,
        "coordination_policy": _POLICY,
        "coordination_role_sha256": coordination_role_sha256,
        "checkpoint38_certificate": cp38,
        "checkpoint38_certificate_sha256": cp38.certificate_sha256,
        "checkpoint38_runtime_sha256": cp38.law_runtime_sha256,
        "checkpoint38_owner_runtime_identity": id(finite_batch_law_owner),
        "checkpoint28_certificate": cp28,
        "checkpoint28_certificate_sha256": cp28.certificate_sha256,
        "checkpoint27_certificate": cp27,
        "checkpoint27_certificate_sha256": cp27.certificate_sha256,
        "checkpoint26_certificate": cp26,
        "checkpoint26_certificate_sha256": cp26.certificate_sha256,
        "checkpoint25_certificate": cp25,
        "checkpoint25_certificate_sha256": cp25.certificate_sha256,
        "checkpoint23_certificate": cp23,
        "checkpoint23_certificate_sha256": cp23.certificate_sha256,
        "checkpoint23_owner_runtime_identity": id(ancestry.checkpoint23_owner),
        "reference_composer_runtime_identity": id(ancestry.reference_composer),
        "process_parameter_sha256": cp38.process_parameter_sha256,
        "manifest": ancestry.manifest,
        "manifest_sha256": ancestry.manifest.manifest_sha256,
        "tag3_domain_tag": INITIAL_TILT_REJECTION_LINEAGE_TAG3_DOMAIN_TAG,
        "initial_reverse_time": (
            INITIAL_TILT_REJECTION_LINEAGE_TAG3_INITIAL_REVERSE_TIME
        ),
        "address_layout": INITIAL_TILT_REJECTION_LINEAGE_TAG3_ADDRESS_LAYOUT,
        "word_count_policy": INITIAL_TILT_REJECTION_LINEAGE_TAG3_WORD_COUNT_POLICY,
        "maximum_stream_records": (
            INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_STREAM_RECORDS
        ),
        "maximum_raw64_words_per_occurrence": (
            INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE
        ),
        "maximum_total_raw64_words": (
            INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_TOTAL_RAW64_WORDS
        ),
        "coordination_runtime_sha256": _runtime_sha256(),
        **{name: True for name in _CERTIFICATE_POSITIVE_FLAGS},
        **{name: False for name in _CERTIFICATE_NEGATIVE_FLAGS},
        "certificate_sha256": _ZERO_SHA256,
    }
    values["certificate_sha256"] = _SEMANTIC_DIGEST(_certificate_payload(values))
    return CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate(
        _construction_token=_CERTIFICATE_TOKEN,
        **values,
    )


def _address_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "certificate", "address_sha256")


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitializationIndexedTag3Address:
    """One direct tag-3 address containing initialization and attempt limbs."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    certificate_sha256: str
    domain_tag: int
    run_id: int
    initialization_index: int
    occurrence_serial: int
    selected_attempt_index: int
    selected_attempt_suffix: int
    philox_key: Tuple[int, int]
    philox_counter: Tuple[int, int, int, int]
    direct_unhashed_components: bool
    initialization_index_encoded: bool
    selected_attempt_index_encoded: bool
    occurrence_serial_encoded: bool
    selected_attempt_suffix_positive: bool
    disjoint_from_all_legacy_tag3_suffix_zero_addresses: bool
    address_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("initialization-indexed tag-3 addresses cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ADDRESS_TOKEN:
            raise TypeError("initialization-indexed tag-3 addresses are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError(
                "initialization-indexed tag-3 address fields are incomplete"
            )
        _validate_address_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initialization-indexed tag-3 addresses are not pickle objects")


def _address_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitializationIndexedTag3Address.__annotations__)


def _validate_address_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    ] = None,
) -> None:
    if trusted_certificate is None:
        certificate = _validate_certificate(values["certificate"])
    else:
        if values["certificate"] is not trusted_certificate:
            raise ValueError("address trusted certificate identity differs")
        certificate = trusted_certificate
    _require_text(values["schema_version"], _SCHEMA_VERSION, name="address.schema")
    _require_sha256(values["certificate_sha256"], name="address.certificate_sha256")
    _require_sha256(values["address_sha256"], name="address.address_sha256")
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("address certificate digest differs")
    expected_tag = INITIAL_TILT_REJECTION_LINEAGE_TAG3_DOMAIN_TAG
    tag = _exact_integer(values["domain_tag"], name="address.domain_tag", maximum=3)
    if tag != expected_tag:
        raise ValueError("address tag-3 domain differs")
    run_id = _exact_integer(values["run_id"], name="address.run_id")
    initialization = _exact_integer(
        values["initialization_index"], name="address.initialization_index"
    )
    serial = _exact_integer(
        values["occurrence_serial"],
        name="address.occurrence_serial",
        minimum=1,
        maximum=certificate.maximum_stream_records,
    )
    attempt = _exact_integer(
        values["selected_attempt_index"],
        name="address.selected_attempt_index",
        maximum=certificate.checkpoint38_certificate.attempt_budget - 1,
    )
    suffix = _exact_integer(
        values["selected_attempt_suffix"],
        name="address.selected_attempt_suffix",
        minimum=1,
        maximum=certificate.checkpoint38_certificate.attempt_budget,
    )
    if suffix != attempt + 1:
        raise ValueError("address selected-attempt suffix differs")
    key = _exact_tuple(
        values["philox_key"], name="address.philox_key", maximum=2, length=2
    )
    counter = _exact_tuple(
        values["philox_counter"],
        name="address.philox_counter",
        maximum=4,
        length=4,
    )
    for position, word in enumerate(key):
        _exact_integer(word, name="address.philox_key[%d]" % position)
    for position, word in enumerate(counter):
        _exact_integer(word, name="address.philox_counter[%d]" % position)
    if key != (run_id, tag):
        raise ValueError("address Philox key differs from direct components")
    if counter != (0, initialization, serial, suffix):
        raise ValueError("address Philox counter differs from direct components")
    for name in (
        "direct_unhashed_components",
        "initialization_index_encoded",
        "selected_attempt_index_encoded",
        "occurrence_serial_encoded",
        "selected_attempt_suffix_positive",
        "disjoint_from_all_legacy_tag3_suffix_zero_addresses",
    ):
        _exact_bool(values[name], True, name="address.%s" % name)
    if values["address_sha256"] != _SEMANTIC_DIGEST(_address_payload(values)):
        raise ValueError("initialization-indexed tag-3 address digest differs")


def _validate_address(
    address: object,
    *,
    certificate: Optional[
        CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    ] = None,
) -> CounterKeyedInitializationIndexedTag3Address:
    if type(address) is not CounterKeyedInitializationIndexedTag3Address:
        raise TypeError("address has the wrong exact initialization-indexed type")
    _validate_address_values(
        {name: getattr(address, name) for name in _address_fields()},
        trusted_certificate=certificate,
    )
    return address


def _make_address(
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
    *,
    run_id: int,
    initialization_index: int,
    occurrence_serial: int,
    selected_attempt_index: int,
) -> CounterKeyedInitializationIndexedTag3Address:
    suffix = selected_attempt_index + 1
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "domain_tag": INITIAL_TILT_REJECTION_LINEAGE_TAG3_DOMAIN_TAG,
        "run_id": run_id,
        "initialization_index": initialization_index,
        "occurrence_serial": occurrence_serial,
        "selected_attempt_index": selected_attempt_index,
        "selected_attempt_suffix": suffix,
        "philox_key": (run_id, INITIAL_TILT_REJECTION_LINEAGE_TAG3_DOMAIN_TAG),
        "philox_counter": (0, initialization_index, occurrence_serial, suffix),
        "direct_unhashed_components": True,
        "initialization_index_encoded": True,
        "selected_attempt_index_encoded": True,
        "occurrence_serial_encoded": True,
        "selected_attempt_suffix_positive": True,
        "disjoint_from_all_legacy_tag3_suffix_zero_addresses": True,
        "address_sha256": _ZERO_SHA256,
    }
    values["address_sha256"] = _SEMANTIC_DIGEST(_address_payload(values))
    return CounterKeyedInitializationIndexedTag3Address(
        _construction_token=_ADDRESS_TOKEN,
        **values,
    )


def _preflight_raw64_words(
    words: object,
    *,
    expected_count: int,
) -> Tuple[int, ...]:
    checked = _exact_tuple(
        words,
        name="raw64_words",
        maximum=INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE,
        length=expected_count,
    )
    for position, word in enumerate(checked):
        _exact_integer(word, name="raw64_words[%d]" % position)
    return checked  # type: ignore[return-value]


def _snapshot_matches(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    return all(
        type(getattr(left, name)) is type(getattr(right, name))
        and getattr(left, name) == getattr(right, name)
        for name in _ROUTE_STATE_FIELDS()
    )


def _stream_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "address",
        "initial_state",
        "raw64_words",
        "final_state",
        "stream_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitializationIndexedTag3Stream:
    """One consumed same-runtime raw64 prefix from a CP39-local address."""

    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    certificate_sha256: str
    address: CounterKeyedInitializationIndexedTag3Address
    address_sha256: str
    initial_state: object
    initial_snapshot_sha256: str
    initial_state_sha256: str
    raw64_word_count: int
    raw64_words: Tuple[int, ...]
    raw64_words_sha256: str
    final_state: object
    final_snapshot_sha256: str
    final_state_sha256: str
    exact_local_stream_invoked: bool
    exact_requested_prefix_consumed: bool
    no_upper_counter_carry: bool
    caller_rng_used: bool
    parent_execution_used_this_stream: bool
    same_runtime_only: bool
    stream_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("initialization-indexed tag-3 streams cannot subclass")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _STREAM_TOKEN:
            raise TypeError("initialization-indexed tag-3 streams are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("initialization-indexed tag-3 stream fields are incomplete")
        _validate_stream_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initialization-indexed tag-3 streams are not pickle objects")


def _stream_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitializationIndexedTag3Stream.__annotations__)


def _validate_stream_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    ] = None,
) -> None:
    if trusted_certificate is None:
        certificate = _validate_certificate(values["certificate"])
    else:
        if values["certificate"] is not trusted_certificate:
            raise ValueError("stream trusted certificate identity differs")
        certificate = trusted_certificate
    for name in (
        "certificate_sha256",
        "address_sha256",
        "initial_snapshot_sha256",
        "initial_state_sha256",
        "raw64_words_sha256",
        "final_snapshot_sha256",
        "final_state_sha256",
        "stream_sha256",
    ):
        _require_sha256(values[name], name="stream.%s" % name)
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("stream certificate digest differs")
    address = _validate_address(values["address"], certificate=certificate)
    if values["address_sha256"] != address.address_sha256:
        raise ValueError("stream address digest differs")
    count = _exact_integer(
        values["raw64_word_count"],
        name="stream.raw64_word_count",
        minimum=1,
        maximum=certificate.maximum_raw64_words_per_occurrence,
    )
    words = _preflight_raw64_words(values["raw64_words"], expected_count=count)
    if values["raw64_words_sha256"] != _SEMANTIC_DIGEST({"raw64_words": words}):
        raise ValueError("stream raw64 word digest differs")
    initial = _VALIDATE_ROUTE_STATE(values["initial_state"])
    final = _VALIDATE_ROUTE_STATE(values["final_state"])
    if values["initial_snapshot_sha256"] != initial.snapshot_sha256:
        raise ValueError("stream initial snapshot digest differs")
    if values["initial_state_sha256"] != initial.state_sha256:
        raise ValueError("stream initial state digest differs")
    if values["final_snapshot_sha256"] != final.snapshot_sha256:
        raise ValueError("stream final snapshot digest differs")
    if values["final_state_sha256"] != final.state_sha256:
        raise ValueError("stream final state digest differs")
    if initial.key != address.philox_key or initial.counter != address.philox_counter:
        raise ValueError("stream initial state differs from its direct address")
    if final.key != initial.key or final.counter[1:] != initial.counter[1:]:
        raise ValueError("stream prefix carried into an upper counter limb")
    expected_flags = {
        "exact_local_stream_invoked": True,
        "exact_requested_prefix_consumed": True,
        "no_upper_counter_carry": True,
        "caller_rng_used": False,
        "parent_execution_used_this_stream": False,
        "same_runtime_only": True,
    }
    for name, expected in expected_flags.items():
        _exact_bool(values[name], expected, name="stream.%s" % name)
    if values["stream_sha256"] != _SEMANTIC_DIGEST(_stream_payload(values)):
        raise ValueError("initialization-indexed tag-3 stream digest differs")


def _validate_stream(
    stream: object,
    *,
    certificate: Optional[
        CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    ] = None,
) -> CounterKeyedInitializationIndexedTag3Stream:
    if type(stream) is not CounterKeyedInitializationIndexedTag3Stream:
        raise TypeError("stream has the wrong exact initialization-indexed type")
    _validate_stream_values(
        {name: getattr(stream, name) for name in _stream_fields()},
        trusted_certificate=certificate,
    )
    return stream


def _new_generator(
    address: CounterKeyedInitializationIndexedTag3Address,
) -> np.random.Generator:
    return np.random.Generator(
        np.random.Philox(
            key=np.asarray(address.philox_key, dtype=np.uint64),
            counter=np.asarray(address.philox_counter, dtype=np.uint64),
        )
    )


def _make_stream(
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
    address: CounterKeyedInitializationIndexedTag3Address,
    raw64_word_count: int,
) -> CounterKeyedInitializationIndexedTag3Stream:
    checked_address = _validate_address(address, certificate=certificate)
    checked_count = _exact_integer(
        raw64_word_count,
        name="raw64_word_count",
        minimum=1,
        maximum=certificate.maximum_raw64_words_per_occurrence,
    )
    generator = _new_generator(checked_address)
    initial = _CAPTURE_ROUTE_STATE(generator)
    words = tuple(
        int(value)
        for value in np.atleast_1d(generator.bit_generator.random_raw(checked_count))
    )
    final = _CAPTURE_ROUTE_STATE(generator)
    if final.key != initial.key or final.counter[1:] != initial.counter[1:]:
        raise PluginBridgeCounterKeyedInitialTiltRejectionLineageTag3CoordinationError(
            "tag-3 prefix carried into an upper address limb"
        )
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "address": checked_address,
        "address_sha256": checked_address.address_sha256,
        "initial_state": initial,
        "initial_snapshot_sha256": initial.snapshot_sha256,
        "initial_state_sha256": initial.state_sha256,
        "raw64_word_count": checked_count,
        "raw64_words": words,
        "raw64_words_sha256": _SEMANTIC_DIGEST({"raw64_words": words}),
        "final_state": final,
        "final_snapshot_sha256": final.snapshot_sha256,
        "final_state_sha256": final.state_sha256,
        "exact_local_stream_invoked": True,
        "exact_requested_prefix_consumed": True,
        "no_upper_counter_carry": True,
        "caller_rng_used": False,
        "parent_execution_used_this_stream": False,
        "same_runtime_only": True,
        "stream_sha256": _ZERO_SHA256,
    }
    values["stream_sha256"] = _SEMANTIC_DIGEST(_stream_payload(values))
    return CounterKeyedInitializationIndexedTag3Stream(
        _construction_token=_STREAM_TOKEN,
        **values,
    )


def _replay_stream(
    stream: CounterKeyedInitializationIndexedTag3Stream,
    *,
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
) -> CounterKeyedInitializationIndexedTag3Stream:
    checked = _validate_stream(stream, certificate=certificate)
    generator = _new_generator(checked.address)
    initial = _CAPTURE_ROUTE_STATE(generator)
    if not _snapshot_matches(initial, checked.initial_state):
        raise ValueError("tag-3 replay initial snapshot differs")
    words = tuple(
        int(value)
        for value in np.atleast_1d(
            generator.bit_generator.random_raw(checked.raw64_word_count)
        )
    )
    final = _CAPTURE_ROUTE_STATE(generator)
    if words != checked.raw64_words:
        raise ValueError("tag-3 raw64 prefix did not replay")
    if not _snapshot_matches(final, checked.final_state):
        raise ValueError("tag-3 replay final snapshot differs")
    if final.key != initial.key or final.counter[1:] != initial.counter[1:]:
        raise PluginBridgeCounterKeyedInitialTiltRejectionLineageTag3CoordinationError(
            "tag-3 replay carried into an upper address limb"
        )
    return checked


def _preflight_configuration(
    configuration: object,
    *,
    manifest: object,
    name: str,
) -> TransformedConfiguration:
    checked_manifest = _CP28_VALIDATE_MANIFEST(manifest)
    checked = _exact_tuple(
        configuration,
        name=name,
        maximum=INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_STREAM_RECORDS,
    )
    dimension_by_type = dict(checked_manifest.type_dimensions)
    keys = []
    for position, event in enumerate(checked):
        if type(event) is not TransformedEvent:
            raise TypeError(
                "%s[%d] must be an exact TransformedEvent" % (name, position)
            )
        event_type = _exact_integer(
            event.event_type,
            name="%s[%d].event_type" % (name, position),
        )
        if event_type not in dimension_by_type:
            raise ValueError(
                "%s[%d] has a type outside the manifest" % (name, position)
            )
        coordinates = _exact_tuple(
            event.coordinates,
            name="%s[%d].coordinates" % (name, position),
            maximum=INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE,
            length=dimension_by_type[event_type],
        )
        for coordinate_index, coordinate in enumerate(coordinates):
            if type(coordinate) is not float or not math.isfinite(coordinate):
                raise ValueError(
                    "%s[%d].coordinates[%d] must be finite binary64"
                    % (name, position, coordinate_index)
                )
            if coordinate == 0.0 and math.copysign(1.0, coordinate) < 0.0:
                raise ValueError(
                    "%s[%d] coordinates must use canonical zero" % (name, position)
                )
        reconstructed = TransformedEvent(event_type, coordinates)
        if _EVENT_MODEL_KEY(reconstructed) != _EVENT_MODEL_KEY(event):
            raise ValueError("%s[%d] is not canonical" % (name, position))
        keys.append(_EVENT_MODEL_KEY(event))
    if tuple(sorted(keys)) != tuple(keys):
        raise ValueError("%s is not canonically ordered" % name)
    return checked  # type: ignore[return-value]


def _configuration_keys(
    configuration: object,
    *,
    manifest: object,
    name: str,
) -> Tuple[Tuple[object, ...], ...]:
    checked = _preflight_configuration(configuration, manifest=manifest, name=name)
    return tuple(_EVENT_MODEL_KEY(event) for event in checked)


def _word_plan(
    configuration: object,
    *,
    manifest: object,
) -> Tuple[Tuple[int, ...], int]:
    checked = _preflight_configuration(
        configuration,
        manifest=manifest,
        name="selected_configuration",
    )
    dimensions = dict(manifest.type_dimensions)
    counts = []
    total = 0
    for position, event in enumerate(checked):
        count = max(1, dimensions[event.event_type])
        _exact_integer(
            count,
            name="tag3_raw64_word_counts[%d]" % position,
            minimum=1,
            maximum=INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE,
        )
        total += count
        if total > INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_TOTAL_RAW64_WORDS:
            raise ValueError("tag-3 word plan exceeds the aggregate bound")
        counts.append(count)
    return tuple(counts), total


def _intensity_snapshot(
    intensity: object,
    *,
    manifest: object,
) -> Tuple[object, ...]:
    if type(intensity) is not _INTENSITY_TYPE:
        raise TypeError("initial_intensity has the wrong exact type")
    source_keys = _configuration_keys(
        intensity.source_configuration,
        manifest=manifest,
        name="initial_intensity.source_configuration",
    )
    _REQUIRE_INTENSITY_REPRESENTATION(intensity)
    for name in (
        "reverse_time",
        "direct_time",
        "reference_schedule_rate",
        "scheduled_reference_exit_rate",
    ):
        value = getattr(intensity, name)
        if type(value) is not float or not math.isfinite(value):
            raise ValueError("initial_intensity.%s must be finite binary64" % name)
    if (
        intensity.reverse_time
        != INITIAL_TILT_REJECTION_LINEAGE_TAG3_INITIAL_REVERSE_TIME
    ):
        raise ValueError("initial intensity reverse time is not zero")
    if intensity.base_rates is None:
        base_rates = None
    else:
        base_rates = tuple(
            getattr(intensity.base_rates, name)
            for name in ("birth", "death", "replacement", "total")
        )
        if any(
            type(value) is not float or not math.isfinite(value) for value in base_rates
        ):
            raise ValueError("initial intensity base rates are not finite binary64")
    return (
        intensity.schema_version,
        intensity.contract_scope,
        intensity.process_parameter_key,
        source_keys,
        intensity.reverse_time,
        intensity.direct_time,
        base_rates,
        intensity.reference_schedule_rate,
        intensity.scheduled_reference_exit_rate,
    )


def _intensity_sha256(intensity: object, *, manifest: object) -> str:
    return _SEMANTIC_DIGEST(
        {
            "initial_intensity_snapshot": _intensity_snapshot(
                intensity, manifest=manifest
            )
        }
    )


def _require_intensity_binding(
    intensity: object,
    configuration: TransformedConfiguration,
    *,
    manifest: object,
) -> _INTENSITY_TYPE:
    snapshot = _intensity_snapshot(intensity, manifest=manifest)
    del snapshot
    if len(intensity.source_configuration) != len(configuration):
        raise ValueError("initial intensity source cardinality differs")
    for position, (source_event, selected_event) in enumerate(
        zip(intensity.source_configuration, configuration)
    ):
        if source_event is not selected_event:
            raise ValueError(
                "initial intensity event %d lost selected identity" % position
            )
    return intensity


def _preflight_lineage_shape(state: object) -> object:
    if type(state) is not _lineage.OperationalLineageState:
        raise TypeError("lineage_state has the wrong exact type")
    for name in (
        "occurrences",
        "occurrence_sha256s",
        "retired_identifiers",
        "retired_identifier_sha256s",
        "model_configuration",
    ):
        value = getattr(state, name)
        if type(value) is not tuple:
            raise TypeError("lineage_state.%s must be an exact tuple" % name)
        if len(value) > INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_STREAM_RECORDS:
            raise ValueError("lineage_state.%s exceeds the record bound" % name)
    if state.retired_identifiers or state.retired_identifier_sha256s:
        raise ValueError("lineage_state must have an empty retired ledger")
    if len(state.occurrences) != len(state.model_configuration):
        raise ValueError("lineage occurrence and model projection counts differ")
    for position, occurrence in enumerate(state.occurrences):
        if type(occurrence) is not _lineage.OperationalLineagedOccurrence:
            raise TypeError("lineage occurrence has the wrong exact type")
        if type(occurrence.event) is not TransformedEvent:
            raise TypeError("lineage occurrence event has the wrong exact type")
        if type(occurrence.event.coordinates) is not tuple:
            raise TypeError("lineage occurrence coordinate storage must be a tuple")
        if (
            len(occurrence.event.coordinates)
            > INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE
        ):
            raise ValueError("lineage occurrence coordinates exceed the bound")
        if state.model_configuration[position] is not occurrence.event:
            raise ValueError("lineage model projection lost event identity")
    return state


def _require_bootstrap_lineage_binding(
    state: object,
    configuration: TransformedConfiguration,
    *,
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
    run_id: int,
    initialization_index: int,
) -> object:
    shaped = _preflight_lineage_shape(state)
    checked = _CP23_VALIDATE_STATE(shaped)
    if checked.certificate_sha256 != certificate.checkpoint23_certificate_sha256:
        raise ValueError("lineage state belongs to another CP23 certificate")
    if checked.run_id != run_id or checked.initialization_index != initialization_index:
        raise ValueError("lineage state request coordinates differ")
    if len(checked.occurrences) != len(configuration):
        raise ValueError("lineage occurrence coverage differs")
    if checked.retired_identifiers or checked.retired_identifier_sha256s:
        raise ValueError("selected lineage is not a bootstrap state")
    if checked.next_serial != len(checked.occurrences) + 1:
        raise ValueError("bootstrap lineage next serial differs")
    for position, (occurrence, event) in enumerate(
        zip(checked.occurrences, configuration)
    ):
        if occurrence.event is not event:
            raise ValueError("lineage occurrence event identity differs")
        identifier = occurrence.identifier
        if identifier.run_id != run_id or identifier.serial != position + 1:
            raise ValueError("bootstrap lineage serial or run differs")
        if identifier.origin_kind != "initial":
            raise ValueError("bootstrap lineage origin kind differs")
        if identifier.origin_initialization_index != initialization_index:
            raise ValueError("bootstrap lineage initialization origin differs")
        if identifier.origin_initial_position != position:
            raise ValueError("bootstrap lineage origin position differs")
        if identifier.origin_step_index is not None or (
            identifier.origin_proposal_index is not None
        ):
            raise ValueError("bootstrap lineage has edit-origin fields")
    return shaped


def _occurrence_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "lineaged_occurrence",
        "identifier",
        "event",
        "tag3_stream",
        "record_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionOccurrencePayload:
    """One selected bootstrap occurrence and its uninterpreted local prefix."""

    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    certificate_sha256: str
    position: int
    lineaged_occurrence: object
    lineaged_occurrence_sha256: str
    identifier: object
    identifier_sha256: str
    event: TransformedEvent
    event_model_key: Tuple[object, ...]
    run_id: int
    initialization_index: int
    selected_attempt_index: int
    occurrence_serial: int
    qualified_lineage_coordinate: Tuple[int, int, int, int]
    manifest_coordinate_dimension: int
    raw64_word_count: int
    tag3_stream: CounterKeyedInitializationIndexedTag3Stream
    tag3_stream_sha256: str
    tag3_address_sha256: str
    exact_occurrence_identity_preserved: bool
    exact_event_identity_preserved: bool
    prefix_is_uninterpreted_shape_metadata: bool
    prefix_generates_selected_event: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("rejection occurrence payloads cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _OCCURRENCE_TOKEN:
            raise TypeError("rejection occurrence payloads are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("rejection occurrence payload fields are incomplete")
        _validate_occurrence_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("rejection occurrence payloads are not pickle objects")


def _occurrence_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitialTiltRejectionOccurrencePayload.__annotations__)


def _validate_occurrence_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    ] = None,
) -> None:
    if trusted_certificate is None:
        certificate = _validate_certificate(values["certificate"])
    else:
        if values["certificate"] is not trusted_certificate:
            raise ValueError("occurrence trusted certificate identity differs")
        certificate = trusted_certificate
    for name in (
        "certificate_sha256",
        "lineaged_occurrence_sha256",
        "identifier_sha256",
        "tag3_stream_sha256",
        "tag3_address_sha256",
        "record_sha256",
    ):
        _require_sha256(values[name], name="occurrence.%s" % name)
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("occurrence certificate digest differs")
    record_position = _exact_integer(
        values["position"],
        name="occurrence.position",
        maximum=certificate.maximum_stream_records - 1,
    )
    occurrence = values["lineaged_occurrence"]
    if type(occurrence) is not _lineage.OperationalLineagedOccurrence:
        raise TypeError("lineaged_occurrence has the wrong exact type")
    if values["lineaged_occurrence_sha256"] != occurrence.occurrence_sha256:
        raise ValueError("lineaged occurrence digest differs")
    if values["identifier"] is not occurrence.identifier:
        raise ValueError("occurrence identifier identity differs")
    identifier = values["identifier"]
    if type(identifier) is not _lineage.OperationalLineageIdentifier:
        raise TypeError("occurrence identifier has the wrong exact type")
    if values["identifier_sha256"] != identifier.identifier_sha256:
        raise ValueError("occurrence identifier digest differs")
    if values["event"] is not occurrence.event:
        raise ValueError("occurrence event identity differs")
    event = values["event"]
    if type(event) is not TransformedEvent:
        raise TypeError("occurrence event has the wrong exact type")
    event_key = _exact_tuple(
        values["event_model_key"],
        name="occurrence.event_model_key",
        maximum=2,
        length=2,
    )
    _exact_integer(event_key[0], name="occurrence.event_model_key[0]")
    key_coordinates = _exact_tuple(
        event_key[1],
        name="occurrence.event_model_key[1]",
        maximum=certificate.maximum_raw64_words_per_occurrence,
    )
    for coordinate_index, coordinate_value in enumerate(key_coordinates):
        if type(coordinate_value) is not float or not math.isfinite(coordinate_value):
            raise TypeError(
                "occurrence.event_model_key[1][%d] must be finite binary64"
                % coordinate_index
            )
    if event_key != _EVENT_MODEL_KEY(event):
        raise ValueError("occurrence event model key differs")
    run_id = _exact_integer(values["run_id"], name="occurrence.run_id")
    initialization = _exact_integer(
        values["initialization_index"], name="occurrence.initialization_index"
    )
    attempt = _exact_integer(
        values["selected_attempt_index"],
        name="occurrence.selected_attempt_index",
        maximum=certificate.checkpoint38_certificate.attempt_budget - 1,
    )
    serial = _exact_integer(
        values["occurrence_serial"],
        name="occurrence.occurrence_serial",
        minimum=1,
        maximum=certificate.maximum_stream_records,
    )
    coordinate = _exact_tuple(
        values["qualified_lineage_coordinate"],
        name="occurrence.qualified_lineage_coordinate",
        maximum=4,
        length=4,
    )
    for limb_index, limb in enumerate(coordinate):
        _exact_integer(
            limb,
            name="occurrence.qualified_lineage_coordinate[%d]" % limb_index,
        )
    if coordinate != (run_id, initialization, attempt, serial):
        raise ValueError("qualified lineage coordinate differs")
    if identifier.run_id != run_id or identifier.serial != serial:
        raise ValueError("occurrence identifier run or serial differs")
    if identifier.origin_initialization_index != initialization:
        raise ValueError("occurrence identifier initialization differs")
    if identifier.origin_initial_position != record_position:
        raise ValueError("occurrence identifier position differs")
    dimension = _exact_integer(
        values["manifest_coordinate_dimension"],
        name="occurrence.manifest_coordinate_dimension",
        maximum=certificate.maximum_raw64_words_per_occurrence,
    )
    expected_dimension = dict(certificate.manifest.type_dimensions).get(
        event.event_type
    )
    if dimension != expected_dimension or len(event.coordinates) != dimension:
        raise ValueError("occurrence manifest dimension differs")
    count = _exact_integer(
        values["raw64_word_count"],
        name="occurrence.raw64_word_count",
        minimum=1,
        maximum=certificate.maximum_raw64_words_per_occurrence,
    )
    if count != max(1, dimension):
        raise ValueError("occurrence word count differs from manifest dimension")
    stream = _validate_stream(values["tag3_stream"], certificate=certificate)
    if values["tag3_stream_sha256"] != stream.stream_sha256:
        raise ValueError("occurrence stream digest differs")
    if values["tag3_address_sha256"] != stream.address.address_sha256:
        raise ValueError("occurrence address digest differs")
    if stream.address.run_id != run_id or (
        stream.address.initialization_index != initialization
    ):
        raise ValueError("occurrence stream request coordinates differ")
    if stream.address.selected_attempt_index != attempt or (
        stream.address.occurrence_serial != serial
    ):
        raise ValueError("occurrence stream subject coordinates differ")
    if stream.raw64_word_count != count:
        raise ValueError("occurrence stream word count differs")
    _exact_bool(
        values["exact_occurrence_identity_preserved"],
        True,
        name="occurrence.exact_occurrence_identity_preserved",
    )
    _exact_bool(
        values["exact_event_identity_preserved"],
        True,
        name="occurrence.exact_event_identity_preserved",
    )
    _exact_bool(
        values["prefix_is_uninterpreted_shape_metadata"],
        True,
        name="occurrence.prefix_is_uninterpreted_shape_metadata",
    )
    _exact_bool(
        values["prefix_generates_selected_event"],
        False,
        name="occurrence.prefix_generates_selected_event",
    )
    if values["record_sha256"] != _SEMANTIC_DIGEST(_occurrence_payload(values)):
        raise ValueError("rejection occurrence payload digest differs")


def _validate_occurrence(
    record: object,
    *,
    certificate: Optional[
        CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    ] = None,
) -> CounterKeyedInitialTiltRejectionOccurrencePayload:
    if type(record) is not CounterKeyedInitialTiltRejectionOccurrencePayload:
        raise TypeError("record has the wrong exact rejection occurrence type")
    _validate_occurrence_values(
        {name: getattr(record, name) for name in _occurrence_fields()},
        trusted_certificate=certificate,
    )
    return record


def _make_occurrence(
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
    occurrence: object,
    stream: CounterKeyedInitializationIndexedTag3Stream,
    *,
    position: int,
    selected_attempt_index: int,
) -> CounterKeyedInitialTiltRejectionOccurrencePayload:
    event = occurrence.event
    dimension = dict(certificate.manifest.type_dimensions)[event.event_type]
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "position": position,
        "lineaged_occurrence": occurrence,
        "lineaged_occurrence_sha256": occurrence.occurrence_sha256,
        "identifier": occurrence.identifier,
        "identifier_sha256": occurrence.identifier.identifier_sha256,
        "event": event,
        "event_model_key": _EVENT_MODEL_KEY(event),
        "run_id": stream.address.run_id,
        "initialization_index": stream.address.initialization_index,
        "selected_attempt_index": selected_attempt_index,
        "occurrence_serial": occurrence.identifier.serial,
        "qualified_lineage_coordinate": (
            stream.address.run_id,
            stream.address.initialization_index,
            selected_attempt_index,
            occurrence.identifier.serial,
        ),
        "manifest_coordinate_dimension": dimension,
        "raw64_word_count": stream.raw64_word_count,
        "tag3_stream": stream,
        "tag3_stream_sha256": stream.stream_sha256,
        "tag3_address_sha256": stream.address.address_sha256,
        "exact_occurrence_identity_preserved": True,
        "exact_event_identity_preserved": True,
        "prefix_is_uninterpreted_shape_metadata": True,
        "prefix_generates_selected_event": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _SEMANTIC_DIGEST(_occurrence_payload(values))
    return CounterKeyedInitialTiltRejectionOccurrencePayload(
        _construction_token=_OCCURRENCE_TOKEN,
        **values,
    )


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "parent_finite_batch_law_result",
        "selected_configuration",
        "initial_intensity",
        "lineage_state",
        "occurrence_payloads",
        "result_sha256",
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult:
    """Selected coordinated state or exact exhausted no-state outcome."""

    schema_version: str
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    certificate_sha256: str
    parent_finite_batch_law_result: _CP38_RESULT_TYPE
    parent_finite_batch_law_result_sha256: str
    run_id: int
    initialization_index: int
    outcome: str
    source_selected_attempt_index: Optional[int]
    selected_configuration: Optional[TransformedConfiguration]
    selected_configuration_sha256: Optional[str]
    initial_intensity: Optional[_INTENSITY_TYPE]
    initial_intensity_sha256: Optional[str]
    lineage_state: Optional[object]
    lineage_state_sha256: Optional[str]
    tag3_raw64_word_counts: Tuple[int, ...]
    occurrence_payloads: Tuple[CounterKeyedInitialTiltRejectionOccurrencePayload, ...]
    occurrence_payload_sha256s: Tuple[str, ...]
    tag3_address_sha256s: Tuple[str, ...]
    qualified_lineage_coordinates: Tuple[Tuple[int, int, int, int], ...]
    stream_count: int
    total_raw64_words: int
    selected_branch_materialized: bool
    exhausted_no_state: bool
    selected_empty_state_retained: bool
    composer_preflight_invoked: bool
    lineage_bootstrap_invoked: bool
    local_tag3_streams_consumed: bool
    exact_parent_selected_configuration_identity_preserved: bool
    exact_parent_selected_attempt_index_preserved: bool
    lineage_projection_per_event_identity_preserved: bool
    complete_occurrence_payload_coverage: bool
    within_result_unique_tag3_addresses: bool
    initialization_attempt_serial_address_injectivity: bool
    legacy_tag3_suffix_zero_disjointness: bool
    exhausted_branch_invoked_selected_state_construction_callback: bool
    parent_resolve_call_count: int
    no_caller_rng: bool
    deterministic_fixed_address_replay_only: bool
    initializer_output_admitted: bool
    initializer_admissible: bool
    live_initializer_law_certified: bool
    tag3_payload_semantics_certified: bool
    tag3_words_generate_selected_coordinates_certified: bool
    success_conditioned_ideal_tv_comparison_certified: bool
    cross_bootstrap_merge_safety_certified: bool
    lineage_fork_prevention_certified: bool
    brownian_stream_consumption_certified: bool
    continuous_drift_admissible: bool
    path_admissible: bool
    full_sampler_admissible: bool
    sampler_liveness_certified: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("lineage/tag-3 coordination results cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("lineage/tag-3 coordination results are module-created")
        if len(values) != len(self.__annotations__) or set(values) != set(
            self.__annotations__
        ):
            raise TypeError("lineage/tag-3 coordination result fields are incomplete")
        _validate_result_values(values)
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("lineage/tag-3 coordination results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(
        CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult.__annotations__
    )


_RESULT_ALWAYS_TRUE_FLAGS = (
    "initialization_attempt_serial_address_injectivity",
    "legacy_tag3_suffix_zero_disjointness",
    "no_caller_rng",
    "deterministic_fixed_address_replay_only",
)
_RESULT_ALWAYS_FALSE_FLAGS = (
    "initializer_output_admitted",
    "initializer_admissible",
    "live_initializer_law_certified",
    "tag3_payload_semantics_certified",
    "tag3_words_generate_selected_coordinates_certified",
    "success_conditioned_ideal_tv_comparison_certified",
    "cross_bootstrap_merge_safety_certified",
    "lineage_fork_prevention_certified",
    "brownian_stream_consumption_certified",
    "continuous_drift_admissible",
    "path_admissible",
    "full_sampler_admissible",
    "sampler_liveness_certified",
)


def _preflight_result_record(
    result: object,
    *,
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult:
    if (
        type(result)
        is not CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult
    ):
        raise TypeError("result has the wrong exact lineage/tag-3 type")
    if result.certificate is not certificate:
        raise ValueError("result belongs to another lineage/tag-3 certificate")
    _require_text(result.schema_version, _SCHEMA_VERSION, name="result.schema")
    for name in (
        "certificate_sha256",
        "parent_finite_batch_law_result_sha256",
        "result_sha256",
    ):
        _require_sha256(getattr(result, name), name="result.%s" % name)
    if result.certificate_sha256 != certificate.certificate_sha256:
        raise ValueError("result certificate digest differs")
    _exact_integer(result.run_id, name="result.run_id")
    _exact_integer(result.initialization_index, name="result.initialization_index")
    if type(result.outcome) is not str or (
        result.outcome not in INITIAL_TILT_REJECTION_LINEAGE_TAG3_OUTCOMES
    ):
        raise ValueError("result outcome is unknown")
    counts = _exact_tuple(
        result.tag3_raw64_word_counts,
        name="result.tag3_raw64_word_counts",
        maximum=certificate.maximum_stream_records,
    )
    running_total = 0
    for position, count in enumerate(counts):
        running_total += _exact_integer(
            count,
            name="result.tag3_raw64_word_counts[%d]" % position,
            minimum=1,
            maximum=certificate.maximum_raw64_words_per_occurrence,
        )
        if running_total > certificate.maximum_total_raw64_words:
            raise ValueError("result tag-3 word plan exceeds the aggregate bound")
    records = _exact_tuple(
        result.occurrence_payloads,
        name="result.occurrence_payloads",
        maximum=certificate.maximum_stream_records,
        length=len(counts),
    )
    digests = _exact_tuple(
        result.occurrence_payload_sha256s,
        name="result.occurrence_payload_sha256s",
        maximum=certificate.maximum_stream_records,
        length=len(records),
    )
    addresses = _exact_tuple(
        result.tag3_address_sha256s,
        name="result.tag3_address_sha256s",
        maximum=certificate.maximum_stream_records,
        length=len(records),
    )
    coordinates = _exact_tuple(
        result.qualified_lineage_coordinates,
        name="result.qualified_lineage_coordinates",
        maximum=certificate.maximum_stream_records,
        length=len(records),
    )
    for position, record in enumerate(records):
        if type(record) is not CounterKeyedInitialTiltRejectionOccurrencePayload:
            raise TypeError("result occurrence payload has the wrong exact type")
        _require_sha256(
            record.record_sha256,
            name="result.occurrence_payloads[%d].record_sha256" % position,
        )
        record_count = _exact_integer(
            record.raw64_word_count,
            name="result.occurrence_payloads[%d].raw64_word_count" % position,
            minimum=1,
            maximum=certificate.maximum_raw64_words_per_occurrence,
        )
        if record_count != counts[position]:
            raise ValueError("result occurrence count differs from its word plan")
        if type(record.tag3_stream) is not CounterKeyedInitializationIndexedTag3Stream:
            raise TypeError("result occurrence stream has the wrong exact type")
        stream_word_count = _exact_integer(
            record.tag3_stream.raw64_word_count,
            name="result.occurrence_payloads[%d].stream.raw64_word_count" % position,
            minimum=1,
            maximum=certificate.maximum_raw64_words_per_occurrence,
        )
        if stream_word_count != record_count:
            raise ValueError("result occurrence stream count differs")
        raw_words = _exact_tuple(
            record.tag3_stream.raw64_words,
            name="result.occurrence_payloads[%d].raw64_words" % position,
            maximum=certificate.maximum_raw64_words_per_occurrence,
            length=record_count,
        )
        for word_position, word in enumerate(raw_words):
            _exact_integer(
                word,
                name="result.occurrence_payloads[%d].raw64_words[%d]"
                % (position, word_position),
            )
    for position, digest in enumerate(digests):
        _require_sha256(digest, name="result.occurrence_payload_sha256s[%d]" % position)
    for position, digest in enumerate(addresses):
        _require_sha256(digest, name="result.tag3_address_sha256s[%d]" % position)
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
    stream_count = _exact_integer(
        result.stream_count,
        name="result.stream_count",
        maximum=certificate.maximum_stream_records,
    )
    total_words = _exact_integer(
        result.total_raw64_words,
        name="result.total_raw64_words",
        maximum=certificate.maximum_total_raw64_words,
    )
    if stream_count != len(records):
        raise ValueError("result stream count differs from record count")
    if total_words != running_total:
        raise ValueError("result total raw64 words differs from its plan")
    _exact_integer(
        result.parent_resolve_call_count,
        name="result.parent_resolve_call_count",
        minimum=1,
        maximum=1,
    )
    for name in (
        _RESULT_ALWAYS_TRUE_FLAGS
        + _RESULT_ALWAYS_FALSE_FLAGS
        + (
            "selected_branch_materialized",
            "exhausted_no_state",
            "selected_empty_state_retained",
            "composer_preflight_invoked",
            "lineage_bootstrap_invoked",
            "local_tag3_streams_consumed",
            "exact_parent_selected_configuration_identity_preserved",
            "exact_parent_selected_attempt_index_preserved",
            "lineage_projection_per_event_identity_preserved",
            "complete_occurrence_payload_coverage",
            "within_result_unique_tag3_addresses",
            "exhausted_branch_invoked_selected_state_construction_callback",
        )
    ):
        if type(getattr(result, name)) is not bool:
            raise TypeError("result.%s must be an exact Boolean" % name)
    for name in _RESULT_ALWAYS_TRUE_FLAGS:
        _exact_bool(getattr(result, name), True, name="result.%s" % name)
    for name in _RESULT_ALWAYS_FALSE_FLAGS:
        _exact_bool(getattr(result, name), False, name="result.%s" % name)
    if result.outcome == "selected":
        shallow_expected_flags = {
            "selected_branch_materialized": True,
            "exhausted_no_state": False,
            "selected_empty_state_retained": len(counts) == 0,
            "composer_preflight_invoked": True,
            "lineage_bootstrap_invoked": True,
            "local_tag3_streams_consumed": len(records) > 0,
            "exact_parent_selected_configuration_identity_preserved": True,
            "exact_parent_selected_attempt_index_preserved": True,
            "lineage_projection_per_event_identity_preserved": True,
            "complete_occurrence_payload_coverage": True,
            "within_result_unique_tag3_addresses": True,
            "exhausted_branch_invoked_selected_state_construction_callback": False,
        }
    else:
        shallow_expected_flags = {
            "selected_branch_materialized": False,
            "exhausted_no_state": True,
            "selected_empty_state_retained": False,
            "composer_preflight_invoked": False,
            "lineage_bootstrap_invoked": False,
            "local_tag3_streams_consumed": False,
            "exact_parent_selected_configuration_identity_preserved": False,
            "exact_parent_selected_attempt_index_preserved": False,
            "lineage_projection_per_event_identity_preserved": False,
            "complete_occurrence_payload_coverage": True,
            "within_result_unique_tag3_addresses": True,
            "exhausted_branch_invoked_selected_state_construction_callback": False,
        }
    for name, expected in shallow_expected_flags.items():
        _exact_bool(getattr(result, name), expected, name="result.%s" % name)
    if result.outcome == "selected":
        _exact_integer(
            result.source_selected_attempt_index,
            name="result.source_selected_attempt_index",
            maximum=certificate.checkpoint38_certificate.attempt_budget - 1,
        )
        _require_sha256(
            result.selected_configuration_sha256,
            name="result.selected_configuration_sha256",
        )
        _preflight_configuration(
            result.selected_configuration,
            manifest=certificate.manifest,
            name="result.selected_configuration",
        )
        if type(result.initial_intensity) is not _INTENSITY_TYPE:
            raise TypeError(
                "selected result initial_intensity has the wrong exact type"
            )
        _require_sha256(
            result.initial_intensity_sha256,
            name="result.initial_intensity_sha256",
        )
        _preflight_lineage_shape(result.lineage_state)
        _require_sha256(
            result.lineage_state_sha256,
            name="result.lineage_state_sha256",
        )
    else:
        for name in (
            "source_selected_attempt_index",
            "selected_configuration",
            "selected_configuration_sha256",
            "initial_intensity",
            "initial_intensity_sha256",
            "lineage_state",
            "lineage_state_sha256",
        ):
            if getattr(result, name) is not None:
                raise ValueError("exhausted result %s must be absent" % name)
        if counts or records or digests or addresses or coordinates:
            raise ValueError("exhausted result cannot contain tag-3 records")
    if type(result.parent_finite_batch_law_result) is not _CP38_RESULT_TYPE:
        raise TypeError("result CP38 parent has the wrong exact type")
    return result


def _validate_result_values(
    values: Mapping[str, object],
    *,
    trusted_certificate: Optional[
        CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate
    ] = None,
) -> None:
    if trusted_certificate is None:
        certificate = _validate_certificate(values["certificate"])
    else:
        if values["certificate"] is not trusted_certificate:
            raise ValueError("result trusted certificate identity differs")
        certificate = trusted_certificate
    _require_text(values["schema_version"], _SCHEMA_VERSION, name="result.schema")
    for name in (
        "certificate_sha256",
        "parent_finite_batch_law_result_sha256",
        "result_sha256",
    ):
        _require_sha256(values[name], name="result.%s" % name)
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("result certificate digest differs")
    parent = values["parent_finite_batch_law_result"]
    if type(parent) is not _CP38_RESULT_TYPE:
        raise TypeError("result CP38 parent has the wrong exact type")
    if parent.certificate is not certificate.checkpoint38_certificate:
        raise ValueError("result CP38 parent belongs to another certificate")
    parent = _CP38_PREFLIGHT_RESULT(
        parent, certificate=certificate.checkpoint38_certificate
    )
    if values["parent_finite_batch_law_result_sha256"] != parent.result_sha256:
        raise ValueError("result CP38 parent digest differs")
    for name, expected in (
        ("run_id", parent.run_id),
        ("initialization_index", parent.initialization_index),
        ("outcome", parent.outcome),
    ):
        actual = values[name]
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError("result.%s differs from CP38" % name)
    counts = _exact_tuple(
        values["tag3_raw64_word_counts"],
        name="result.tag3_raw64_word_counts",
        maximum=certificate.maximum_stream_records,
    )
    records = _exact_tuple(
        values["occurrence_payloads"],
        name="result.occurrence_payloads",
        maximum=certificate.maximum_stream_records,
        length=len(counts),
    )
    digests = _exact_tuple(
        values["occurrence_payload_sha256s"],
        name="result.occurrence_payload_sha256s",
        maximum=certificate.maximum_stream_records,
        length=len(records),
    )
    addresses = _exact_tuple(
        values["tag3_address_sha256s"],
        name="result.tag3_address_sha256s",
        maximum=certificate.maximum_stream_records,
        length=len(records),
    )
    coordinates = _exact_tuple(
        values["qualified_lineage_coordinates"],
        name="result.qualified_lineage_coordinates",
        maximum=certificate.maximum_stream_records,
        length=len(records),
    )
    total = 0
    for position, count in enumerate(counts):
        total += _exact_integer(
            count,
            name="result.tag3_raw64_word_counts[%d]" % position,
            minimum=1,
            maximum=certificate.maximum_raw64_words_per_occurrence,
        )
        if total > certificate.maximum_total_raw64_words:
            raise ValueError("result word plan exceeds its aggregate bound")
    if values["stream_count"] != len(records):
        raise ValueError("result stream count differs")
    if values["total_raw64_words"] != total:
        raise ValueError("result total raw64 word count differs")
    if len(set(addresses)) != len(addresses):
        raise ValueError("result tag-3 addresses are not unique")
    if len(set(coordinates)) != len(coordinates):
        raise ValueError("result qualified lineage coordinates are not unique")
    for name in _RESULT_ALWAYS_TRUE_FLAGS:
        _exact_bool(values[name], True, name="result.%s" % name)
    for name in _RESULT_ALWAYS_FALSE_FLAGS:
        _exact_bool(values[name], False, name="result.%s" % name)
    _exact_integer(
        values["parent_resolve_call_count"],
        name="result.parent_resolve_call_count",
        minimum=1,
        maximum=1,
    )
    if parent.outcome == "selected":
        attempt = _exact_integer(
            values["source_selected_attempt_index"],
            name="result.source_selected_attempt_index",
            maximum=certificate.checkpoint38_certificate.attempt_budget - 1,
        )
        if attempt != parent.selected_attempt_index:
            raise ValueError("result selected attempt differs from CP38")
        configuration = _preflight_configuration(
            values["selected_configuration"],
            manifest=certificate.manifest,
            name="result.selected_configuration",
        )
        if configuration is not parent.selected_configuration:
            raise ValueError("result selected configuration identity differs from CP38")
        _require_sha256(
            values["selected_configuration_sha256"],
            name="result.selected_configuration_sha256",
        )
        configuration_digest = _CONFIGURATION_SHA256(configuration)
        if values["selected_configuration_sha256"] != configuration_digest or (
            configuration_digest != parent.selected_configuration_sha256
        ):
            raise ValueError("result selected configuration digest differs")
        intensity = _require_intensity_binding(
            values["initial_intensity"],
            configuration,
            manifest=certificate.manifest,
        )
        _require_sha256(
            values["initial_intensity_sha256"], name="result.initial_intensity_sha256"
        )
        if values["initial_intensity_sha256"] != _intensity_sha256(
            intensity, manifest=certificate.manifest
        ):
            raise ValueError("result initial intensity digest differs")
        lineage = _require_bootstrap_lineage_binding(
            values["lineage_state"],
            configuration,
            certificate=certificate,
            run_id=parent.run_id,
            initialization_index=parent.initialization_index,
        )
        _require_sha256(
            values["lineage_state_sha256"], name="result.lineage_state_sha256"
        )
        if values["lineage_state_sha256"] != lineage.state_sha256:
            raise ValueError("result lineage-state digest differs")
        expected_counts, expected_total = _word_plan(
            configuration, manifest=certificate.manifest
        )
        if counts != expected_counts or total != expected_total:
            raise ValueError(
                "result tag-3 word plan differs from selected configuration"
            )
        if len(records) != len(lineage.occurrences):
            raise ValueError("result occurrence payload coverage differs")
        for position, (occurrence, record, count) in enumerate(
            zip(lineage.occurrences, records, counts)
        ):
            if type(record) is not CounterKeyedInitialTiltRejectionOccurrencePayload:
                raise TypeError("result occurrence payload has the wrong exact type")
            record_position = _exact_integer(
                record.position,
                name="result.occurrence_payloads[%d].position" % position,
                maximum=certificate.maximum_stream_records - 1,
            )
            if record_position != position or (
                record.lineaged_occurrence is not occurrence
            ):
                raise ValueError("result occurrence position or identity differs")
            checked_record = _validate_occurrence(record, certificate=certificate)
            if checked_record.certificate is not certificate:
                raise ValueError("result occurrence has another certificate")
            if checked_record.raw64_word_count != count:
                raise ValueError("result occurrence word count differs")
            if digests[position] != checked_record.record_sha256:
                raise ValueError("result occurrence digest sequence differs")
            if addresses[position] != checked_record.tag3_address_sha256:
                raise ValueError("result address digest sequence differs")
            if coordinates[position] != checked_record.qualified_lineage_coordinate:
                raise ValueError("result qualified lineage coordinate sequence differs")
        expected_flags = {
            "selected_branch_materialized": True,
            "exhausted_no_state": False,
            "selected_empty_state_retained": len(configuration) == 0,
            "composer_preflight_invoked": True,
            "lineage_bootstrap_invoked": True,
            "local_tag3_streams_consumed": len(records) > 0,
            "exact_parent_selected_configuration_identity_preserved": True,
            "exact_parent_selected_attempt_index_preserved": True,
            "lineage_projection_per_event_identity_preserved": True,
            "complete_occurrence_payload_coverage": True,
            "within_result_unique_tag3_addresses": True,
            "exhausted_branch_invoked_selected_state_construction_callback": False,
        }
    else:
        for name in (
            "source_selected_attempt_index",
            "selected_configuration",
            "selected_configuration_sha256",
            "initial_intensity",
            "initial_intensity_sha256",
            "lineage_state",
            "lineage_state_sha256",
        ):
            if values[name] is not None:
                raise ValueError("exhausted result %s must be absent" % name)
        if counts or records or digests or addresses or coordinates or total != 0:
            raise ValueError("exhausted result must contain no tag-3 state")
        expected_flags = {
            "selected_branch_materialized": False,
            "exhausted_no_state": True,
            "selected_empty_state_retained": False,
            "composer_preflight_invoked": False,
            "lineage_bootstrap_invoked": False,
            "local_tag3_streams_consumed": False,
            "exact_parent_selected_configuration_identity_preserved": False,
            "exact_parent_selected_attempt_index_preserved": False,
            "lineage_projection_per_event_identity_preserved": False,
            "complete_occurrence_payload_coverage": True,
            "within_result_unique_tag3_addresses": True,
            "exhausted_branch_invoked_selected_state_construction_callback": False,
        }
    for name, expected in expected_flags.items():
        _exact_bool(values[name], expected, name="result.%s" % name)
    if values["result_sha256"] != _SEMANTIC_DIGEST(_result_payload(values)):
        raise ValueError("lineage/tag-3 coordination result digest differs")


def _make_result(
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
    parent: _CP38_RESULT_TYPE,
    *,
    intensity: Optional[_INTENSITY_TYPE],
    lineage: Optional[object],
    counts: Tuple[int, ...],
    records: Tuple[CounterKeyedInitialTiltRejectionOccurrencePayload, ...],
) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult:
    selected = parent.outcome == "selected"
    if selected:
        configuration = parent.selected_configuration
        configuration_sha256 = parent.selected_configuration_sha256
        attempt = parent.selected_attempt_index
        intensity_sha256 = _intensity_sha256(intensity, manifest=certificate.manifest)
        lineage_sha256 = lineage.state_sha256
    else:
        configuration = None
        configuration_sha256 = None
        attempt = None
        intensity_sha256 = None
        lineage_sha256 = None
    values: Dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "parent_finite_batch_law_result": parent,
        "parent_finite_batch_law_result_sha256": parent.result_sha256,
        "run_id": parent.run_id,
        "initialization_index": parent.initialization_index,
        "outcome": parent.outcome,
        "source_selected_attempt_index": attempt,
        "selected_configuration": configuration,
        "selected_configuration_sha256": configuration_sha256,
        "initial_intensity": intensity,
        "initial_intensity_sha256": intensity_sha256,
        "lineage_state": lineage,
        "lineage_state_sha256": lineage_sha256,
        "tag3_raw64_word_counts": counts,
        "occurrence_payloads": records,
        "occurrence_payload_sha256s": tuple(record.record_sha256 for record in records),
        "tag3_address_sha256s": tuple(record.tag3_address_sha256 for record in records),
        "qualified_lineage_coordinates": tuple(
            record.qualified_lineage_coordinate for record in records
        ),
        "stream_count": len(records),
        "total_raw64_words": sum(counts),
        "selected_branch_materialized": selected,
        "exhausted_no_state": not selected,
        "selected_empty_state_retained": selected and len(configuration) == 0,
        "composer_preflight_invoked": selected,
        "lineage_bootstrap_invoked": selected,
        "local_tag3_streams_consumed": selected and bool(records),
        "exact_parent_selected_configuration_identity_preserved": selected,
        "exact_parent_selected_attempt_index_preserved": selected,
        "lineage_projection_per_event_identity_preserved": selected,
        "complete_occurrence_payload_coverage": True,
        "within_result_unique_tag3_addresses": True,
        "initialization_attempt_serial_address_injectivity": True,
        "legacy_tag3_suffix_zero_disjointness": True,
        "exhausted_branch_invoked_selected_state_construction_callback": False,
        "parent_resolve_call_count": 1,
        "no_caller_rng": True,
        "deterministic_fixed_address_replay_only": True,
        **{name: False for name in _RESULT_ALWAYS_FALSE_FLAGS},
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _SEMANTIC_DIGEST(_result_payload(values))
    return CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult(
        _construction_token=_RESULT_TOKEN,
        **values,
    )


def _result_tree_snapshot(
    result: CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult,
) -> Tuple[object, ...]:
    if result.outcome == "selected":
        intensity_snapshot = _intensity_snapshot(
            result.initial_intensity,
            manifest=result.certificate.manifest,
        )
        intensity_source_snapshot = (
            result.initial_intensity.source_configuration,
            tuple(result.initial_intensity.source_configuration),
        )
        lineage_snapshot = _record_snapshot(result.lineage_state, _CP23_STATE_FIELDS())
        lineage_occurrences = tuple(
            _record_snapshot(occurrence, _CP23_OCCURRENCE_FIELDS())
            for occurrence in result.lineage_state.occurrences
        )
        lineage_identifiers = tuple(
            _record_snapshot(occurrence.identifier, _CP23_IDENTIFIER_FIELDS())
            for occurrence in result.lineage_state.occurrences
        )
    else:
        intensity_snapshot = None
        intensity_source_snapshot = None
        lineage_snapshot = None
        lineage_occurrences = ()
        lineage_identifiers = ()
    return (
        _record_snapshot(result, _result_fields()),
        tuple(
            _record_snapshot(record, _occurrence_fields())
            for record in result.occurrence_payloads
        ),
        tuple(
            _record_snapshot(record.tag3_stream, _stream_fields())
            for record in result.occurrence_payloads
        ),
        tuple(
            _record_snapshot(record.tag3_stream.address, _address_fields())
            for record in result.occurrence_payloads
        ),
        tuple(
            (
                _record_snapshot(
                    record.tag3_stream.initial_state,
                    _ROUTE_STATE_FIELDS(),
                ),
                _record_snapshot(
                    record.tag3_stream.final_state,
                    _ROUTE_STATE_FIELDS(),
                ),
            )
            for record in result.occurrence_payloads
        ),
        intensity_snapshot,
        intensity_source_snapshot,
        lineage_snapshot,
        lineage_occurrences,
        lineage_identifiers,
        _CP38_RESULT_TREE_SNAPSHOT(result.parent_finite_batch_law_result),
    )


def _require_result_tree_unchanged(
    result: CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult,
    before: Tuple[object, ...],
    *,
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
) -> None:
    _preflight_result_record(result, certificate=certificate)
    if type(before) is not tuple or len(before) != 11:
        raise TypeError("lineage/tag-3 result-tree snapshot is malformed")
    (
        result_before,
        record_befores,
        stream_befores,
        address_befores,
        route_state_befores,
        intensity_before,
        intensity_source_before,
        lineage_before,
        lineage_occurrence_befores,
        lineage_identifier_befores,
        parent_before,
    ) = before
    _require_record_unchanged(
        result,
        _result_fields(),
        result_before,
        identity_fields=(
            "certificate",
            "parent_finite_batch_law_result",
            "selected_configuration",
            "initial_intensity",
            "lineage_state",
            "tag3_raw64_word_counts",
            "occurrence_payloads",
            "occurrence_payload_sha256s",
            "tag3_address_sha256s",
            "qualified_lineage_coordinates",
        ),
        name="lineage/tag-3 result",
    )
    if len(record_befores) != len(result.occurrence_payloads):
        raise ValueError("lineage/tag-3 occurrence count changed")
    for position, (
        record,
        record_before,
        stream_before,
        address_before,
        route_state_before,
    ) in enumerate(
        zip(
            result.occurrence_payloads,
            record_befores,
            stream_befores,
            address_befores,
            route_state_befores,
        )
    ):
        _require_record_unchanged(
            record,
            _occurrence_fields(),
            record_before,
            identity_fields=(
                "certificate",
                "lineaged_occurrence",
                "identifier",
                "event",
                "event_model_key",
                "qualified_lineage_coordinate",
                "tag3_stream",
            ),
            name="lineage/tag-3 occurrence %d" % position,
        )
        _require_record_unchanged(
            record.tag3_stream,
            _stream_fields(),
            stream_before,
            identity_fields=(
                "certificate",
                "address",
                "initial_state",
                "raw64_words",
                "final_state",
            ),
            name="lineage/tag-3 stream %d" % position,
        )
        _require_record_unchanged(
            record.tag3_stream.address,
            _address_fields(),
            address_before,
            identity_fields=("certificate", "philox_key", "philox_counter"),
            name="lineage/tag-3 address %d" % position,
        )
        initial_route_before, final_route_before = route_state_before
        _require_record_unchanged(
            record.tag3_stream.initial_state,
            _ROUTE_STATE_FIELDS(),
            initial_route_before,
            identity_fields=(),
            name="lineage/tag-3 initial route state %d" % position,
        )
        _require_record_unchanged(
            record.tag3_stream.final_state,
            _ROUTE_STATE_FIELDS(),
            final_route_before,
            identity_fields=(),
            name="lineage/tag-3 final route state %d" % position,
        )
    if result.outcome == "selected":
        if (
            _intensity_snapshot(result.initial_intensity, manifest=certificate.manifest)
            != intensity_before
        ):
            raise ValueError("lineage/tag-3 intensity changed")
        source_tuple_before, source_events_before = intensity_source_before
        if result.initial_intensity.source_configuration is not source_tuple_before:
            raise ValueError("lineage/tag-3 intensity source tuple changed identity")
        if len(result.initial_intensity.source_configuration) != len(
            source_events_before
        ) or any(
            event is not expected
            for event, expected in zip(
                result.initial_intensity.source_configuration,
                source_events_before,
            )
        ):
            raise ValueError("lineage/tag-3 intensity event identity changed")
        _require_record_unchanged(
            result.lineage_state,
            _CP23_STATE_FIELDS(),
            lineage_before,
            identity_fields=(
                "occurrences",
                "occurrence_sha256s",
                "retired_identifiers",
                "retired_identifier_sha256s",
                "model_configuration",
            ),
            name="lineage/tag-3 lineage state",
        )
        for position, (occurrence, occurrence_before, identifier_before) in enumerate(
            zip(
                result.lineage_state.occurrences,
                lineage_occurrence_befores,
                lineage_identifier_befores,
            )
        ):
            _require_record_unchanged(
                occurrence,
                _CP23_OCCURRENCE_FIELDS(),
                occurrence_before,
                identity_fields=("identifier", "event", "event_model_key"),
                name="lineage/tag-3 lineage occurrence %d" % position,
            )
            _require_record_unchanged(
                occurrence.identifier,
                _CP23_IDENTIFIER_FIELDS(),
                identifier_before,
                identity_fields=(),
                name="lineage/tag-3 lineage identifier %d" % position,
            )
    _CP38_REQUIRE_RESULT_TREE_UNCHANGED(
        result.parent_finite_batch_law_result,
        parent_before,
        certificate=certificate.checkpoint38_certificate,
    )


def _certificate_record_snapshots(
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
) -> Tuple[Tuple[object, ...], ...]:
    return (
        _record_snapshot(certificate, _certificate_fields()),
        _record_snapshot(
            certificate.checkpoint38_certificate,
            tuple(_CP38_CERT_TYPE.__annotations__),
        ),
        _record_snapshot(
            certificate.checkpoint28_certificate,
            tuple(_CP28_CERT_TYPE.__annotations__),
        ),
        _record_snapshot(
            certificate.checkpoint27_certificate,
            tuple(_CP27_CERT_TYPE.__annotations__),
        ),
        _record_snapshot(
            certificate.checkpoint26_certificate,
            tuple(_CP26_CERT_TYPE.__annotations__),
        ),
        _record_snapshot(
            certificate.checkpoint25_certificate,
            tuple(_CP25_CERT_TYPE.__annotations__),
        ),
        _record_snapshot(
            certificate.checkpoint23_certificate,
            tuple(_CP23_CERT_TYPE.__annotations__),
        ),
        _record_snapshot(
            certificate.manifest,
            tuple(type(certificate.manifest).__annotations__),
        ),
    )


def _require_certificate_records_unchanged(
    certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
    snapshots: Tuple[Tuple[object, ...], ...],
) -> None:
    if type(snapshots) is not tuple or len(snapshots) != 8:
        raise TypeError("certificate record snapshots are malformed")
    records = (
        (certificate, _certificate_fields(), "CP39 certificate"),
        (
            certificate.checkpoint38_certificate,
            tuple(_CP38_CERT_TYPE.__annotations__),
            "CP38 certificate",
        ),
        (
            certificate.checkpoint28_certificate,
            tuple(_CP28_CERT_TYPE.__annotations__),
            "CP28 certificate",
        ),
        (
            certificate.checkpoint27_certificate,
            tuple(_CP27_CERT_TYPE.__annotations__),
            "CP27 certificate",
        ),
        (
            certificate.checkpoint26_certificate,
            tuple(_CP26_CERT_TYPE.__annotations__),
            "CP26 certificate",
        ),
        (
            certificate.checkpoint25_certificate,
            tuple(_CP25_CERT_TYPE.__annotations__),
            "CP25 certificate",
        ),
        (
            certificate.checkpoint23_certificate,
            tuple(_CP23_CERT_TYPE.__annotations__),
            "CP23 certificate",
        ),
        (
            certificate.manifest,
            tuple(type(certificate.manifest).__annotations__),
            "CP28 manifest",
        ),
    )
    for (record, fields, name), before in zip(records, snapshots):
        _require_record_unchanged(
            record,
            fields,
            before,
            identity_fields=tuple(
                field
                for field in fields
                if field.endswith("_certificate")
                or field in ("manifest", "reference", "word_law_hypothesis")
            ),
            name=name,
        )


_FROZEN_OPERATION_SURFACES = (
    ("math", math),
    ("np", np),
    ("platform", platform),
    ("sys", sys),
    ("TransformedEvent", TransformedEvent),
    (
        "CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate",
        CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
    ),
    (
        "CounterKeyedInitializationIndexedTag3Address",
        CounterKeyedInitializationIndexedTag3Address,
    ),
    (
        "CounterKeyedInitializationIndexedTag3Stream",
        CounterKeyedInitializationIndexedTag3Stream,
    ),
    (
        "CounterKeyedInitialTiltRejectionOccurrencePayload",
        CounterKeyedInitialTiltRejectionOccurrencePayload,
    ),
    (
        "CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult",
        CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult,
    ),
    ("_CP38_OWNER_SNAPSHOT", _CP38_OWNER_SNAPSHOT),
    ("_CP38_REQUIRE_OWNER_SNAPSHOT", _CP38_REQUIRE_OWNER_SNAPSHOT),
    ("_CP38_LIVE_CERTIFICATE", _CP38_LIVE_CERTIFICATE),
    ("_CP38_RESOLVE", _CP38_RESOLVE),
    ("_CP38_VALIDATE_RESULT", _CP38_VALIDATE_RESULT),
    ("_CP38_PREFLIGHT_RESULT", _CP38_PREFLIGHT_RESULT),
    ("_CP38_RESULT_TREE_SNAPSHOT", _CP38_RESULT_TREE_SNAPSHOT),
    ("_CP38_REQUIRE_RESULT_TREE_UNCHANGED", _CP38_REQUIRE_RESULT_TREE_UNCHANGED),
    ("_CP37_PREPARATION_PROPERTY", _CP37_PREPARATION_PROPERTY),
    ("_CP36_REFERENCE_PROPERTY", _CP36_REFERENCE_PROPERTY),
    ("_CP28_PROTOCOL_PROPERTY", _CP28_PROTOCOL_PROPERTY),
    ("_CP28_CERTIFICATE_PROPERTY", _CP28_CERTIFICATE_PROPERTY),
    ("_CP28_MANIFEST_PROPERTY", _CP28_MANIFEST_PROPERTY),
    ("_CP28_LIVE", _CP28_LIVE),
    ("_CP28_VALIDATE_MANIFEST", _CP28_VALIDATE_MANIFEST),
    ("_CP28_VALIDATE_CERTIFICATE", _CP28_VALIDATE_CERTIFICATE),
    ("_CP27_CONTROL_PROPERTY", _CP27_CONTROL_PROPERTY),
    ("_CP27_CERTIFICATE_PROPERTY", _CP27_CERTIFICATE_PROPERTY),
    ("_CP27_LIVE", _CP27_LIVE),
    ("_CP27_VALIDATE_CERTIFICATE", _CP27_VALIDATE_CERTIFICATE),
    ("_CP26_CONSUMPTION_PROPERTY", _CP26_CONSUMPTION_PROPERTY),
    ("_CP26_CONTRACT_PROPERTY", _CP26_CONTRACT_PROPERTY),
    ("_CP26_CERTIFICATE_PROPERTY", _CP26_CERTIFICATE_PROPERTY),
    ("_CP26_LIVE", _CP26_LIVE),
    ("_CP26_VALIDATE_CERTIFICATE", _CP26_VALIDATE_CERTIFICATE),
    ("_CP25_CONTRACT_PROPERTY", _CP25_CONTRACT_PROPERTY),
    ("_CP25_CERTIFICATE_PROPERTY", _CP25_CERTIFICATE_PROPERTY),
    ("_CP25_LIVE", _CP25_LIVE),
    ("_CP25_VALIDATE_CERTIFICATE", _CP25_VALIDATE_CERTIFICATE),
    ("_CP23_CERTIFICATE_PROPERTY", _CP23_CERTIFICATE_PROPERTY),
    ("_CP23_COMPOSER_PROPERTY", _CP23_COMPOSER_PROPERTY),
    ("_CP23_LIVE", _CP23_LIVE),
    ("_CP23_BOOTSTRAP", _CP23_BOOTSTRAP),
    ("_CP23_VALIDATE_STATE", _CP23_VALIDATE_STATE),
    ("_CP23_VALIDATE_CERTIFICATE", _CP23_VALIDATE_CERTIFICATE),
    ("_COMPOSER_LIVE", _COMPOSER_LIVE),
    ("_COMPOSER_PREFLIGHT", _COMPOSER_PREFLIGHT),
    ("_COMPOSER_VALIDATE_INTENSITY", _COMPOSER_VALIDATE_INTENSITY),
    ("_REFERENCE_ANCESTRY", _REFERENCE_ANCESTRY),
    ("_PROCESS_PARAMETER_SHA256", _PROCESS_PARAMETER_SHA256),
    ("_SEMANTIC_DIGEST", _SEMANTIC_DIGEST),
    ("_REQUIRE_INTENSITY_REPRESENTATION", _REQUIRE_INTENSITY_REPRESENTATION),
    ("_CONFIGURATION_SHA256", _CONFIGURATION_SHA256),
    ("_EVENT_MODEL_KEY", _EVENT_MODEL_KEY),
    ("_CAPTURE_ROUTE_STATE", _CAPTURE_ROUTE_STATE),
    ("_VALIDATE_ROUTE_STATE", _VALIDATE_ROUTE_STATE),
    ("_ROUTE_STATE_FIELDS", _ROUTE_STATE_FIELDS),
    ("_runtime_sha256", _runtime_sha256),
    ("_direct_ancestry", _direct_ancestry),
    ("_validate_certificate", _validate_certificate),
    ("_make_certificate", _make_certificate),
    ("_require_certificate_records_unchanged", _require_certificate_records_unchanged),
    ("_preflight_configuration", _preflight_configuration),
    ("_configuration_keys", _configuration_keys),
    ("_preflight_raw64_words", _preflight_raw64_words),
    ("_snapshot_matches", _snapshot_matches),
    ("_new_generator", _new_generator),
    ("_validate_address", _validate_address),
    ("_validate_stream", _validate_stream),
    ("_validate_occurrence", _validate_occurrence),
    ("_intensity_snapshot", _intensity_snapshot),
    ("_intensity_sha256", _intensity_sha256),
    ("_require_intensity_binding", _require_intensity_binding),
    ("_require_bootstrap_lineage_binding", _require_bootstrap_lineage_binding),
    ("_word_plan", _word_plan),
    ("_make_address", _make_address),
    ("_make_stream", _make_stream),
    ("_replay_stream", _replay_stream),
    ("_make_occurrence", _make_occurrence),
    ("_make_result", _make_result),
    ("_preflight_result_record", _preflight_result_record),
    ("_validate_result_values", _validate_result_values),
    ("_result_tree_snapshot", _result_tree_snapshot),
    ("_require_result_tree_unchanged", _require_result_tree_unchanged),
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


def _require_operation_surfaces(
    frozen: Tuple[Tuple[str, object], ...] = _FROZEN_OPERATION_SURFACES,
    private_namespace: Tuple[Tuple[str, object], ...] = _FROZEN_PRIVATE_NAMESPACE,
) -> None:
    for name, expected in frozen + private_namespace:
        if globals().get(name) is not expected:
            raise ValueError("lineage/tag-3 operation surface %s changed" % name)


class CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner:
    """Immutable owner of one CP38-bound coordination operation."""

    __slots__ = (
        "_finite_batch_law_owner",
        "_finite_batch_law_owner_identity",
        "_checkpoint38_certificate",
        "_checkpoint38_certificate_identity",
        "_checkpoint37_owner",
        "_checkpoint37_owner_identity",
        "_checkpoint36_owner",
        "_checkpoint36_owner_identity",
        "_checkpoint28_owner",
        "_checkpoint28_owner_identity",
        "_checkpoint27_owner",
        "_checkpoint27_owner_identity",
        "_checkpoint26_owner",
        "_checkpoint26_owner_identity",
        "_checkpoint25_owner",
        "_checkpoint25_owner_identity",
        "_checkpoint23_owner",
        "_checkpoint23_owner_identity",
        "_reference_composer",
        "_reference_composer_identity",
        "_manifest",
        "_manifest_identity",
        "_coordination_policy",
        "_coordination_policy_identity",
        "_coordination_role_sha256",
        "_coordination_role_sha256_identity",
        "_certificate",
        "_certificate_identity",
        "_certificate_snapshots",
        "_certificate_snapshots_identity",
        "_parent_owner_snapshot",
        "_parent_require_owner_snapshot",
        "_parent_live_certificate",
        "_parent_resolve",
        "_parent_validate_result",
        "_parent_result_preflight",
        "_parent_tree_snapshotter",
        "_parent_tree_unchanged_checker",
        "_composer_preflight",
        "_composer_validate_intensity",
        "_lineage_bootstrap",
        "_lineage_validate_state",
        "_address_builder",
        "_stream_builder",
        "_stream_replayer",
        "_occurrence_builder",
        "_result_builder",
        "_result_preflight",
        "_result_validator",
        "_result_tree_snapshotter",
        "_result_tree_unchanged_checker",
        "_surface_guard",
        "_surface_guard_identity",
        "_ancestry_resolver",
        "_certificate_validator",
        "_certificate_builder",
        "_certificate_custody_checker",
        "_configuration_preflight",
        "_intensity_binding_checker",
        "_lineage_binding_checker",
        "_word_planner",
        "_sealed",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("lineage/tag-3 coordination owners cannot be subclassed")

    def __init__(
        self,
        finite_batch_law_owner: _CP38_OWNER_TYPE,
        ancestry: _Ancestry,
        coordination_policy: str,
        coordination_role_sha256: str,
        certificate: CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("lineage/tag-3 coordination owners require certification")
        if type(finite_batch_law_owner) is not _CP38_OWNER_TYPE:
            raise TypeError("finite_batch_law_owner has the wrong exact CP38 type")
        policy = _require_text(coordination_policy, _POLICY, name="coordination_policy")
        role = _require_sha256(
            coordination_role_sha256, name="coordination_role_sha256"
        )
        checked = _validate_certificate(certificate)
        cp38 = _CP38_CERTIFICATE_PROPERTY.__get__(
            finite_batch_law_owner, _CP38_OWNER_TYPE
        )
        if checked.checkpoint38_certificate is not cp38:
            raise ValueError("owner CP38 certificate identity differs")
        if checked.checkpoint38_owner_runtime_identity != id(finite_batch_law_owner):
            raise ValueError("owner CP38 runtime identity differs")
        if checked.checkpoint23_owner_runtime_identity != id(
            ancestry.checkpoint23_owner
        ):
            raise ValueError("owner CP23 runtime identity differs")
        if checked.reference_composer_runtime_identity != id(
            ancestry.reference_composer
        ):
            raise ValueError("owner reference-composer runtime identity differs")
        snapshots = _certificate_record_snapshots(checked)
        bindings = (
            ("_finite_batch_law_owner", finite_batch_law_owner),
            ("_finite_batch_law_owner_identity", finite_batch_law_owner),
            ("_checkpoint38_certificate", cp38),
            ("_checkpoint38_certificate_identity", cp38),
            ("_checkpoint37_owner", ancestry.checkpoint37_owner),
            ("_checkpoint37_owner_identity", ancestry.checkpoint37_owner),
            ("_checkpoint36_owner", ancestry.checkpoint36_owner),
            ("_checkpoint36_owner_identity", ancestry.checkpoint36_owner),
            ("_checkpoint28_owner", ancestry.checkpoint28_owner),
            ("_checkpoint28_owner_identity", ancestry.checkpoint28_owner),
            ("_checkpoint27_owner", ancestry.checkpoint27_owner),
            ("_checkpoint27_owner_identity", ancestry.checkpoint27_owner),
            ("_checkpoint26_owner", ancestry.checkpoint26_owner),
            ("_checkpoint26_owner_identity", ancestry.checkpoint26_owner),
            ("_checkpoint25_owner", ancestry.checkpoint25_owner),
            ("_checkpoint25_owner_identity", ancestry.checkpoint25_owner),
            ("_checkpoint23_owner", ancestry.checkpoint23_owner),
            ("_checkpoint23_owner_identity", ancestry.checkpoint23_owner),
            ("_reference_composer", ancestry.reference_composer),
            ("_reference_composer_identity", ancestry.reference_composer),
            ("_manifest", ancestry.manifest),
            ("_manifest_identity", ancestry.manifest),
            ("_coordination_policy", policy),
            ("_coordination_policy_identity", policy),
            ("_coordination_role_sha256", role),
            ("_coordination_role_sha256_identity", role),
            ("_certificate", checked),
            ("_certificate_identity", checked),
            ("_certificate_snapshots", snapshots),
            ("_certificate_snapshots_identity", snapshots),
            ("_parent_owner_snapshot", _CP38_OWNER_SNAPSHOT),
            ("_parent_require_owner_snapshot", _CP38_REQUIRE_OWNER_SNAPSHOT),
            ("_parent_live_certificate", _CP38_LIVE_CERTIFICATE),
            ("_parent_resolve", _CP38_RESOLVE),
            ("_parent_validate_result", _CP38_VALIDATE_RESULT),
            ("_parent_result_preflight", _CP38_PREFLIGHT_RESULT),
            ("_parent_tree_snapshotter", _CP38_RESULT_TREE_SNAPSHOT),
            (
                "_parent_tree_unchanged_checker",
                _CP38_REQUIRE_RESULT_TREE_UNCHANGED,
            ),
            ("_composer_preflight", _COMPOSER_PREFLIGHT),
            ("_composer_validate_intensity", _COMPOSER_VALIDATE_INTENSITY),
            ("_lineage_bootstrap", _CP23_BOOTSTRAP),
            ("_lineage_validate_state", _CP23_VALIDATE_STATE),
            ("_address_builder", _make_address),
            ("_stream_builder", _make_stream),
            ("_stream_replayer", _replay_stream),
            ("_occurrence_builder", _make_occurrence),
            ("_result_builder", _make_result),
            ("_result_preflight", _preflight_result_record),
            ("_result_validator", _validate_result_values),
            ("_result_tree_snapshotter", _result_tree_snapshot),
            ("_result_tree_unchanged_checker", _require_result_tree_unchanged),
            ("_surface_guard", _require_operation_surfaces),
            ("_surface_guard_identity", _require_operation_surfaces),
            ("_ancestry_resolver", _direct_ancestry),
            ("_certificate_validator", _validate_certificate),
            ("_certificate_builder", _make_certificate),
            (
                "_certificate_custody_checker",
                _require_certificate_records_unchanged,
            ),
            ("_configuration_preflight", _preflight_configuration),
            ("_intensity_binding_checker", _require_intensity_binding),
            ("_lineage_binding_checker", _require_bootstrap_lineage_binding),
            ("_word_planner", _word_plan),
            ("_sealed", True),
        )
        for name, value in bindings:
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("lineage/tag-3 coordination owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("lineage/tag-3 coordination owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("lineage/tag-3 coordination owners are not pickle objects")

    @property
    def certificate(
        self,
    ) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate:
        return self._certificate

    @property
    def finite_batch_law_owner(self) -> _CP38_OWNER_TYPE:
        return self._finite_batch_law_owner

    def _identity_state(
        self,
        expected_surface_guard: object = _require_operation_surfaces,
    ) -> Tuple[object, ...]:
        if self._surface_guard is not expected_surface_guard or (
            self._surface_guard_identity is not expected_surface_guard
        ):
            raise ValueError("lineage/tag-3 surface-guard identity changed")
        self._surface_guard()
        if type(self._sealed) is not bool or self._sealed is not True:
            raise ValueError("lineage/tag-3 coordination owner seal differs")
        current = (
            self._finite_batch_law_owner,
            self._checkpoint38_certificate,
            self._checkpoint37_owner,
            self._checkpoint36_owner,
            self._checkpoint28_owner,
            self._checkpoint27_owner,
            self._checkpoint26_owner,
            self._checkpoint25_owner,
            self._checkpoint23_owner,
            self._reference_composer,
            self._manifest,
            self._coordination_policy,
            self._coordination_role_sha256,
            self._certificate,
            self._certificate_snapshots,
        )
        frozen = (
            self._finite_batch_law_owner_identity,
            self._checkpoint38_certificate_identity,
            self._checkpoint37_owner_identity,
            self._checkpoint36_owner_identity,
            self._checkpoint28_owner_identity,
            self._checkpoint27_owner_identity,
            self._checkpoint26_owner_identity,
            self._checkpoint25_owner_identity,
            self._checkpoint23_owner_identity,
            self._reference_composer_identity,
            self._manifest_identity,
            self._coordination_policy_identity,
            self._coordination_role_sha256_identity,
            self._certificate_identity,
            self._certificate_snapshots_identity,
        )
        if any(live is not expected for live, expected in zip(current, frozen)):
            raise ValueError("lineage/tag-3 coordination owner identity changed")
        callbacks = (
            (self._parent_owner_snapshot, _CP38_OWNER_SNAPSHOT),
            (self._parent_require_owner_snapshot, _CP38_REQUIRE_OWNER_SNAPSHOT),
            (self._parent_live_certificate, _CP38_LIVE_CERTIFICATE),
            (self._parent_resolve, _CP38_RESOLVE),
            (self._parent_validate_result, _CP38_VALIDATE_RESULT),
            (self._parent_result_preflight, _CP38_PREFLIGHT_RESULT),
            (self._parent_tree_snapshotter, _CP38_RESULT_TREE_SNAPSHOT),
            (
                self._parent_tree_unchanged_checker,
                _CP38_REQUIRE_RESULT_TREE_UNCHANGED,
            ),
            (self._composer_preflight, _COMPOSER_PREFLIGHT),
            (self._composer_validate_intensity, _COMPOSER_VALIDATE_INTENSITY),
            (self._lineage_bootstrap, _CP23_BOOTSTRAP),
            (self._lineage_validate_state, _CP23_VALIDATE_STATE),
            (self._address_builder, _make_address),
            (self._stream_builder, _make_stream),
            (self._stream_replayer, _replay_stream),
            (self._occurrence_builder, _make_occurrence),
            (self._result_builder, _make_result),
            (self._result_preflight, _preflight_result_record),
            (self._result_validator, _validate_result_values),
            (self._result_tree_snapshotter, _result_tree_snapshot),
            (self._result_tree_unchanged_checker, _require_result_tree_unchanged),
            (self._surface_guard, _require_operation_surfaces),
            (self._ancestry_resolver, _direct_ancestry),
            (self._certificate_validator, _validate_certificate),
            (self._certificate_builder, _make_certificate),
            (
                self._certificate_custody_checker,
                _require_certificate_records_unchanged,
            ),
            (self._configuration_preflight, _preflight_configuration),
            (self._intensity_binding_checker, _require_intensity_binding),
            (self._lineage_binding_checker, _require_bootstrap_lineage_binding),
            (self._word_planner, _word_plan),
        )
        if any(live is not expected for live, expected in callbacks):
            raise ValueError("lineage/tag-3 coordination cached callback changed")
        return current

    def _owner_snapshot(self) -> Tuple[object, ...]:
        return self._identity_state()

    def _require_owner_snapshot(self, snapshot: Tuple[object, ...]) -> None:
        if type(snapshot) is not tuple or len(snapshot) != 15:
            raise TypeError("lineage/tag-3 coordination owner snapshot is malformed")
        current = self._identity_state()
        if any(live is not expected for live, expected in zip(current, snapshot)):
            raise _COORDINATION_ERROR_TYPE(
                "lineage/tag-3 coordination owner changed during operation"
            )

    def _live_certificate(
        self,
        owner_snapshot: Tuple[object, ...],
    ) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate:
        self._require_owner_snapshot(owner_snapshot)
        parent_snapshot = self._parent_owner_snapshot(self._finite_batch_law_owner)
        parent = self._parent_live_certificate(
            self._finite_batch_law_owner, parent_snapshot
        )
        self._parent_require_owner_snapshot(
            self._finite_batch_law_owner, parent_snapshot
        )
        if parent is not self._checkpoint38_certificate:
            raise ValueError("CP38 live binding substituted its certificate")

        def require_custody() -> None:
            self._require_owner_snapshot(owner_snapshot)
            self._certificate_custody_checker(
                self._certificate, self._certificate_snapshots
            )

        ancestry = self._ancestry_resolver(
            self._finite_batch_law_owner,
            custody_check=require_custody,
        )
        expected_owners = (
            self._checkpoint37_owner,
            self._checkpoint36_owner,
            self._checkpoint28_owner,
            self._checkpoint27_owner,
            self._checkpoint26_owner,
            self._checkpoint25_owner,
            self._checkpoint23_owner,
            self._reference_composer,
            self._manifest,
        )
        live_owners = (
            ancestry.checkpoint37_owner,
            ancestry.checkpoint36_owner,
            ancestry.checkpoint28_owner,
            ancestry.checkpoint27_owner,
            ancestry.checkpoint26_owner,
            ancestry.checkpoint25_owner,
            ancestry.checkpoint23_owner,
            ancestry.reference_composer,
            ancestry.manifest,
        )
        if any(
            live is not expected for live, expected in zip(live_owners, expected_owners)
        ):
            raise ValueError("lineage/tag-3 transitive owner ancestry changed")
        certificate = self._certificate_validator(self._certificate)
        require_custody()
        expected = self._certificate_builder(
            self._finite_batch_law_owner,
            ancestry,
            self._coordination_role_sha256,
        )
        for field in _certificate_fields():
            actual = getattr(certificate, field)
            target = getattr(expected, field)
            if field in (
                "checkpoint38_certificate",
                "checkpoint28_certificate",
                "checkpoint27_certificate",
                "checkpoint26_certificate",
                "checkpoint25_certificate",
                "checkpoint23_certificate",
                "manifest",
            ):
                if actual is not target:
                    raise ValueError("CP39 certificate.%s identity differs" % field)
            elif type(actual) is not type(target) or actual != target:
                raise ValueError("CP39 certificate.%s differs" % field)
        require_custody()
        return certificate

    def coordinate(
        self,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult:
        """Resolve CP38 once, then coordinate only its selected branch."""

        checked_run = _exact_integer(run_id, name="run_id")
        checked_initialization = _exact_integer(
            initialization_index, name="initialization_index"
        )
        owner_snapshot = self._owner_snapshot()
        certificate = self._live_certificate(owner_snapshot)
        parent_owner_snapshot = self._parent_owner_snapshot(
            self._finite_batch_law_owner
        )
        parent = self._parent_resolve(
            self._finite_batch_law_owner,
            checked_run,
            checked_initialization,
        )
        self._parent_require_owner_snapshot(
            self._finite_batch_law_owner, parent_owner_snapshot
        )
        self._require_owner_snapshot(owner_snapshot)
        certificate = self._live_certificate(owner_snapshot)
        parent = self._parent_result_preflight(
            parent, certificate=certificate.checkpoint38_certificate
        )
        parent_tree = self._parent_tree_snapshotter(parent)
        checked_parent = self._parent_validate_result(
            self._finite_batch_law_owner,
            parent,
            checked_run,
            checked_initialization,
        )
        if checked_parent is not parent:
            raise ValueError("CP38 validation substituted its result")
        self._parent_tree_unchanged_checker(
            parent,
            parent_tree,
            certificate=certificate.checkpoint38_certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        certificate = self._live_certificate(owner_snapshot)
        if parent.outcome == "exhausted":
            result = self._result_builder(
                certificate,
                parent,
                intensity=None,
                lineage=None,
                counts=(),
                records=(),
            )
        else:
            configuration = self._configuration_preflight(
                parent.selected_configuration,
                manifest=certificate.manifest,
                name="CP38 selected_configuration",
            )
            counts, _ = self._word_planner(configuration, manifest=certificate.manifest)
            intensity = self._composer_preflight(
                self._reference_composer,
                configuration,
                reverse_time=INITIAL_TILT_REJECTION_LINEAGE_TAG3_INITIAL_REVERSE_TIME,
            )
            self._require_owner_snapshot(owner_snapshot)
            self._intensity_binding_checker(
                intensity, configuration, manifest=certificate.manifest
            )
            lineage = self._lineage_bootstrap(
                self._checkpoint23_owner,
                intensity,
                run_id=checked_run,
                initialization_index=checked_initialization,
            )
            self._require_owner_snapshot(owner_snapshot)
            self._lineage_binding_checker(
                lineage,
                configuration,
                certificate=certificate,
                run_id=checked_run,
                initialization_index=checked_initialization,
            )
            records = []
            for position, (occurrence, count) in enumerate(
                zip(lineage.occurrences, counts)
            ):
                address = self._address_builder(
                    certificate,
                    run_id=checked_run,
                    initialization_index=checked_initialization,
                    occurrence_serial=occurrence.identifier.serial,
                    selected_attempt_index=parent.selected_attempt_index,
                )
                stream = self._stream_builder(certificate, address, count)
                record = self._occurrence_builder(
                    certificate,
                    occurrence,
                    stream,
                    position=position,
                    selected_attempt_index=parent.selected_attempt_index,
                )
                records.append(record)
            result = self._result_builder(
                certificate,
                parent,
                intensity=intensity,
                lineage=lineage,
                counts=counts,
                records=tuple(records),
            )
        self._parent_tree_unchanged_checker(
            parent,
            parent_tree,
            certificate=certificate.checkpoint38_certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        self._live_certificate(owner_snapshot)
        return result

    def validate_result(
        self,
        result: object,
        run_id: object,
        initialization_index: object,
    ) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult:
        """Validate deterministically without resolving or bootstrapping again.

        Composer validation recomputes its deterministic intensity preflight,
        and every stored local stream is replayed.  CP38 ``resolve``, CP23
        bootstrap, and CP39 address/stream/occurrence construction are absent.
        """

        checked_run = _exact_integer(run_id, name="run_id")
        checked_initialization = _exact_integer(
            initialization_index, name="initialization_index"
        )
        if (
            type(result)
            is not CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult
        ):
            raise TypeError("result has the wrong exact lineage/tag-3 type")
        shallow_run = _exact_integer(result.run_id, name="result.run_id")
        shallow_initialization = _exact_integer(
            result.initialization_index, name="result.initialization_index"
        )
        if (
            shallow_run != checked_run
            or shallow_initialization != checked_initialization
        ):
            raise ValueError("result request coordinates differ")
        owner_snapshot = self._owner_snapshot()
        self._certificate_custody_checker(
            self._certificate, self._certificate_snapshots
        )
        checked = self._result_preflight(result, certificate=self._certificate)
        certificate = self._live_certificate(owner_snapshot)
        result_tree = self._result_tree_snapshotter(checked)
        parent = checked.parent_finite_batch_law_result
        parent_tree = self._parent_tree_snapshotter(parent)
        checked_parent = self._parent_validate_result(
            self._finite_batch_law_owner,
            parent,
            checked_run,
            checked_initialization,
        )
        if checked_parent is not parent:
            raise ValueError("CP38 validation substituted its result")
        self._parent_tree_unchanged_checker(
            parent,
            parent_tree,
            certificate=certificate.checkpoint38_certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        certificate = self._live_certificate(owner_snapshot)
        self._result_validator(
            {name: getattr(checked, name) for name in _result_fields()},
            trusted_certificate=certificate,
        )
        if checked.outcome == "selected":
            validated_intensity = self._composer_validate_intensity(
                self._reference_composer, checked.initial_intensity
            )
            if validated_intensity is not checked.initial_intensity:
                raise ValueError("composer validation substituted stored intensity")
            self._intensity_binding_checker(
                checked.initial_intensity,
                checked.selected_configuration,
                manifest=certificate.manifest,
            )
            self._lineage_validate_state(checked.lineage_state)
            self._lineage_binding_checker(
                checked.lineage_state,
                checked.selected_configuration,
                certificate=certificate,
                run_id=checked_run,
                initialization_index=checked_initialization,
            )
            for record in checked.occurrence_payloads:
                replayed = self._stream_replayer(
                    record.tag3_stream, certificate=certificate
                )
                if replayed is not record.tag3_stream:
                    raise ValueError("tag-3 replay substituted its stream")
        self._parent_tree_unchanged_checker(
            parent,
            parent_tree,
            certificate=certificate.checkpoint38_certificate,
        )
        self._result_tree_unchanged_checker(
            checked,
            result_tree,
            certificate=certificate,
        )
        self._require_owner_snapshot(owner_snapshot)
        self._live_certificate(owner_snapshot)
        return checked


def _certify_coordination(
    finite_batch_law_owner: object,
    *,
    coordination_policy: object,
    coordination_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner:
    """Certify the exact CP38-derived selected-state coordination layer."""

    if type(finite_batch_law_owner) is not _CP38_OWNER_TYPE:
        raise TypeError("finite_batch_law_owner has the wrong exact CP38 type")
    _require_operation_surfaces()
    policy = _require_text(coordination_policy, _POLICY, name="coordination_policy")
    role = _require_sha256(coordination_role_sha256, name="coordination_role_sha256")
    ancestry = _direct_ancestry(finite_batch_law_owner)
    certificate = _make_certificate(finite_batch_law_owner, ancestry, role)
    owner = CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner(
        finite_batch_law_owner,
        ancestry,
        policy,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner_snapshot = owner._owner_snapshot()
    owner._live_certificate(owner_snapshot)
    owner._require_owner_snapshot(owner_snapshot)
    return owner


def _require_matching_coordination(
    finite_batch_law_owner: object,
    owner: object,
    *,
    coordination_policy: object,
    coordination_role_sha256: object,
) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner:
    """Require exact CP38 parent, policy, role, and transitive live custody."""

    if type(finite_batch_law_owner) is not _CP38_OWNER_TYPE:
        raise TypeError("finite_batch_law_owner has the wrong exact CP38 type")
    _require_operation_surfaces()
    if type(owner) is not CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner:
        raise TypeError("owner has the wrong exact lineage/tag-3 type")
    policy = _require_text(coordination_policy, _POLICY, name="coordination_policy")
    role = _require_sha256(coordination_role_sha256, name="coordination_role_sha256")
    if owner.finite_batch_law_owner is not finite_batch_law_owner:
        raise ValueError("lineage/tag-3 owner uses another CP38 parent")
    snapshot = owner._owner_snapshot()
    certificate = owner._live_certificate(snapshot)
    if certificate.coordination_policy != policy:
        raise ValueError("lineage/tag-3 owner uses another policy")
    if certificate.coordination_role_sha256 != role:
        raise ValueError("lineage/tag-3 owner uses another role")
    owner._require_owner_snapshot(snapshot)
    return owner


_PUBLIC_CERTIFY_NAME = (
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_lineage_"
    "tag3_coordination"
)
_PUBLIC_MATCHING_NAME = (
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "lineage_tag3_coordination"
)
_PUBLIC_VALIDATE_CERTIFICATE_NAME = (
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_lineage_"
    "tag3_coordination_certificate"
)


def _bind_public_coordination_api(
    certify_impl: object,
    matching_impl: object,
    surface_guard: object,
    owner_type: object,
    certify_name: str,
    matching_name: str,
    validate_name: str,
) -> Tuple[object, object, object]:
    """Bind public calls to the authentic late-defined operation surfaces."""

    namespace = globals()
    late_surfaces: Tuple[Tuple[str, object], ...] = ()

    def require_late_surfaces() -> None:
        for name, expected in late_surfaces:
            if namespace.get(name) is not expected:
                raise ValueError(
                    "lineage/tag-3 late operation surface %s changed" % name
                )
        surface_guard()

    def certify(
        finite_batch_law_owner: object,
        *,
        coordination_policy: object,
        coordination_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner:
        """Certify the exact CP38-derived selected-state coordination layer."""

        require_late_surfaces()
        return certify_impl(
            finite_batch_law_owner,
            coordination_policy=coordination_policy,
            coordination_role_sha256=coordination_role_sha256,
        )

    def matching(
        finite_batch_law_owner: object,
        owner: object,
        *,
        coordination_policy: object,
        coordination_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner:
        """Require exact CP38 parent, policy, role, and live custody."""

        require_late_surfaces()
        return matching_impl(
            finite_batch_law_owner,
            owner,
            coordination_policy=coordination_policy,
            coordination_role_sha256=coordination_role_sha256,
        )

    def validate(
        finite_batch_law_owner: object,
        owner: object,
        *,
        coordination_policy: object,
        coordination_role_sha256: object,
    ) -> CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate:
        """Return the reconstructed live checkpoint-thirty-nine certificate."""

        return matching(
            finite_batch_law_owner,
            owner,
            coordination_policy=coordination_policy,
            coordination_role_sha256=coordination_role_sha256,
        ).certificate

    late_surfaces = (
        ("_require_operation_surfaces", surface_guard),
        (
            "CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner",
            owner_type,
        ),
        ("_certify_coordination", certify_impl),
        ("_require_matching_coordination", matching_impl),
        (certify_name, certify),
        (matching_name, matching),
        (validate_name, validate),
    )
    return certify, matching, validate


_PUBLIC_COORDINATION_FUNCTIONS = _bind_public_coordination_api(
    _certify_coordination,
    _require_matching_coordination,
    _require_operation_surfaces,
    CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner,
    _PUBLIC_CERTIFY_NAME,
    _PUBLIC_MATCHING_NAME,
    _PUBLIC_VALIDATE_CERTIFICATE_NAME,
)
for _public_name, _public_function in zip(
    (
        _PUBLIC_CERTIFY_NAME,
        _PUBLIC_MATCHING_NAME,
        _PUBLIC_VALIDATE_CERTIFICATE_NAME,
    ),
    _PUBLIC_COORDINATION_FUNCTIONS,
):
    _public_function.__name__ = _public_name
    _public_function.__qualname__ = _public_name
    globals()[_public_name] = _public_function


__all__ = [
    _PUBLIC_SCHEMA_NAME,
    (
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_LINEAGE_TAG3_"
        "COORDINATION_POLICY"
    ),
    (
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_LINEAGE_TAG3_"
        "COORDINATION_SCOPE"
    ),
    "INITIAL_TILT_REJECTION_LINEAGE_TAG3_DOMAIN_TAG",
    "INITIAL_TILT_REJECTION_LINEAGE_TAG3_INITIAL_REVERSE_TIME",
    "INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_STREAM_RECORDS",
    "INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_RAW64_WORDS_PER_OCCURRENCE",
    "INITIAL_TILT_REJECTION_LINEAGE_TAG3_MAX_TOTAL_RAW64_WORDS",
    "INITIAL_TILT_REJECTION_LINEAGE_TAG3_ADDRESS_LAYOUT",
    "INITIAL_TILT_REJECTION_LINEAGE_TAG3_WORD_COUNT_POLICY",
    "INITIAL_TILT_REJECTION_LINEAGE_TAG3_OUTCOMES",
    "CounterKeyedInitialTiltRejectionLineageTag3CoordinationCertificate",
    "CounterKeyedInitializationIndexedTag3Address",
    "CounterKeyedInitializationIndexedTag3Stream",
    "CounterKeyedInitialTiltRejectionOccurrencePayload",
    "CounterKeyedInitialTiltRejectionLineageTag3CoordinationResult",
    "CounterKeyedInitialTiltRejectionLineageTag3CoordinationOwner",
    "PluginBridgeCounterKeyedInitialTiltRejectionLineageTag3CoordinationError",
    _PUBLIC_CERTIFY_NAME,
    _PUBLIC_MATCHING_NAME,
    _PUBLIC_VALIDATE_CERTIFICATE_NAME,
]
