"""Replay evidence for finite-resolution operational reference routes.

Checkpoint nineteen delegates a post-clock route draw to the process-owned
normalized reference composer and checks the live draw against a shadow
Philox stream.  Its compact route record intentionally retains only hashes of
the Philox states.  This successor layer adds immutable, reconstructable
snapshots of the exact NumPy Philox state immediately before and after that
delegated draw.  Offline validation reconstructs a fresh local generator from
the pre-route snapshot, repeats the frozen composer draw, and requires both
the candidate semantic digest and the complete post-route state to agree.

The evidence covers every route that the frozen owner successfully returns.
It additionally classifies positive-dimensional birth and replacement
destinations, including replacements whose positive source and destination
dimensions differ.  The result is a same-runtime, finite-resolution replay
contract.  It is not an exact-law proof for NumPy categorical, integer, or
Gaussian sampling; it contains no bounded trace of the raw words used by
``standard_normal``; and it does not certify an analytic Lebesgue law, a
controlled target, liveness, a path, or a complete sampler.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

import numpy as np

from heterodiff.processes import plugin_bridge_operational_thinning as _thinning
from heterodiff.processes.plugin_bridge_operational_thinning import (
    OperationalJumpThinning,
    OperationalReferenceRouteDraw,
    OperationalThinningCertificate,
    OperationalWaitingTimeDraw,
    TotalizedJumpRateEnvelope,
)
from heterodiff.processes.plugin_bridge_sampler import (
    ProcessValidReferenceJump,
    ProcessValidReferenceJumpComposer,
    ReferenceCandidateIntensity,
)
from heterodiff.processes.reversible_hybrid_reference import HybridJumpKind


PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_SCHEMA_VERSION = (
    "plugin-bridge-continuous-route-evidence-v1"
)
PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION = "plugin-bridge-philox-route-state-v1"
PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_POLICY = (
    "checkpoint19-delegated-live-route;"
    "canonical-exact-philox-pre-post-snapshots;"
    "fresh-local-philox-same-runtime-replay;"
    "candidate-semantic-and-post-state-equality;"
    "continuous-destination-and-unequal-dimension-classification-v1"
)
PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_SCOPE = (
    "checkpoint19-operational-reference-route;"
    "all-successfully-returned-route-kinds;"
    "finite-resolution-same-runtime-procedural-replay;"
    "positive-dimensional-birth-and-replacement-evidence;"
    "source-occurrence-destination-coordinate-and-factor-custody;"
    "not-bounded-raw-normal-word-trace;not-exact-categorical-law;"
    "not-exact-integer-law;not-exact-gaussian-law;"
    "not-analytic-lebesgue-output-law;not-distribution-recovery;"
    "not-all-route-totality;not-liveness;not-controlled-target;"
    "not-drift;not-initializer;not-path;not-full-sampler;"
    "not-runtime-portable;not-cryptographic-authentication"
)

_PHILOX_BIT_GENERATOR = "numpy.random.Philox"
_PHILOX_STATE_KEYS = {
    "bit_generator",
    "state",
    "buffer",
    "buffer_pos",
    "has_uint32",
    "uinteger",
}
_PHILOX_CORE_STATE_KEYS = {"counter", "key"}
_UINT64_LIMIT = 1 << 64
_UINT32_LIMIT = 1 << 32

_SNAPSHOT_TOKEN = object()
_CERTIFICATE_TOKEN = object()
_EVIDENCE_TOKEN = object()
_OWNER_TOKEN = object()


class PluginBridgeContinuousRouteEvidenceError(ArithmeticError):
    """Raised when an operational route cannot be replayed exactly."""


def _exact_bounded_integer(
    value: object,
    *,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if value < minimum or value > maximum:
        raise ValueError("%s is outside its canonical range" % name)
    return value


def _exact_uint_tuple(
    values: object,
    *,
    name: str,
    length: int,
) -> Tuple[int, ...]:
    if type(values) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(values) != length:
        raise ValueError("%s must contain exactly %d values" % (name, length))
    for index, value in enumerate(values):
        _exact_bounded_integer(
            value,
            name="%s[%d]" % (name, index),
            minimum=0,
            maximum=_UINT64_LIMIT - 1,
        )
    return values


def _exact_uint64_array(
    value: object,
    *,
    name: str,
    length: int,
) -> Tuple[int, ...]:
    if type(value) is not np.ndarray:
        raise TypeError("%s must be an exact numpy.ndarray" % name)
    if value.dtype != np.dtype(np.uint64):
        raise TypeError("%s must have exact uint64 dtype" % name)
    if value.shape != (length,):
        raise ValueError("%s has the wrong shape" % name)
    if not value.flags.c_contiguous:
        raise ValueError("%s must be C-contiguous" % name)
    return tuple(int(item) for item in value)


def _snapshot_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {name: value for name, value in values.items() if name != "snapshot_sha256"}


@dataclass(frozen=True, eq=False, init=False)
class PhiloxRouteStateSnapshot:
    """Immutable plain-data snapshot of the complete NumPy Philox state."""

    schema_version: str
    rng_bit_generator: str
    counter: Tuple[int, ...]
    key: Tuple[int, ...]
    buffer: Tuple[int, ...]
    buffer_pos: int
    has_uint32: int
    uinteger: int
    state_sha256: str
    snapshot_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("PhiloxRouteStateSnapshot cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _SNAPSHOT_TOKEN:
            raise TypeError("Philox route snapshots are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("Philox route snapshot fields are incomplete")
        if values["schema_version"] != PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION:
            raise ValueError("Philox route snapshot schema differs")
        if values["rng_bit_generator"] != _PHILOX_BIT_GENERATOR:
            raise ValueError("Philox route snapshot RNG type differs")
        _exact_uint_tuple(values["counter"], name="snapshot.counter", length=4)
        _exact_uint_tuple(values["key"], name="snapshot.key", length=2)
        _exact_uint_tuple(values["buffer"], name="snapshot.buffer", length=4)
        _exact_bounded_integer(
            values["buffer_pos"],
            name="snapshot.buffer_pos",
            minimum=0,
            maximum=4,
        )
        _exact_bounded_integer(
            values["has_uint32"],
            name="snapshot.has_uint32",
            minimum=0,
            maximum=1,
        )
        _exact_bounded_integer(
            values["uinteger"],
            name="snapshot.uinteger",
            minimum=0,
            maximum=_UINT32_LIMIT - 1,
        )
        for name in ("state_sha256", "snapshot_sha256"):
            _thinning._require_sha256(values[name], name="snapshot.%s" % name)
        reconstructed = _philox_state_mapping(values)
        if values["state_sha256"] != _thinning._rng_state_sha256(reconstructed):
            raise ValueError("Philox route state digest differs")
        expected_digest = _thinning._semantic_digest(_snapshot_payload(values))
        if values["snapshot_sha256"] != expected_digest:
            raise ValueError("Philox route snapshot digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("Philox route snapshots are not pickle objects")


def _snapshot_fields() -> Tuple[str, ...]:
    return tuple(PhiloxRouteStateSnapshot.__annotations__)


def _snapshot_values(snapshot: PhiloxRouteStateSnapshot) -> Dict[str, object]:
    return {name: getattr(snapshot, name) for name in _snapshot_fields()}


def _validate_snapshot(snapshot: object) -> PhiloxRouteStateSnapshot:
    if type(snapshot) is not PhiloxRouteStateSnapshot:
        raise TypeError("snapshot must be an exact PhiloxRouteStateSnapshot")
    return PhiloxRouteStateSnapshot(
        **_snapshot_values(snapshot),
        _construction_token=_SNAPSHOT_TOKEN,
    )


def _philox_state_mapping(values: Mapping[str, object]) -> Dict[str, object]:
    return {
        "bit_generator": "Philox",
        "state": {
            "counter": np.asarray(values["counter"], dtype=np.uint64),
            "key": np.asarray(values["key"], dtype=np.uint64),
        },
        "buffer": np.asarray(values["buffer"], dtype=np.uint64),
        "buffer_pos": values["buffer_pos"],
        "has_uint32": values["has_uint32"],
        "uinteger": values["uinteger"],
    }


def _snapshot_from_state(state: object) -> PhiloxRouteStateSnapshot:
    if type(state) is not dict or set(state) != _PHILOX_STATE_KEYS:
        raise ValueError("Philox state has an unexpected top-level schema")
    if state["bit_generator"] != "Philox":
        raise ValueError("Philox state has the wrong bit-generator label")
    core = state["state"]
    if type(core) is not dict or set(core) != _PHILOX_CORE_STATE_KEYS:
        raise ValueError("Philox state has an unexpected counter/key schema")
    values: Dict[str, object] = {
        "schema_version": PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION,
        "rng_bit_generator": _PHILOX_BIT_GENERATOR,
        "counter": _exact_uint64_array(
            core["counter"], name="Philox counter", length=4
        ),
        "key": _exact_uint64_array(core["key"], name="Philox key", length=2),
        "buffer": _exact_uint64_array(state["buffer"], name="Philox buffer", length=4),
        "buffer_pos": _exact_bounded_integer(
            state["buffer_pos"],
            name="Philox buffer_pos",
            minimum=0,
            maximum=4,
        ),
        "has_uint32": _exact_bounded_integer(
            state["has_uint32"],
            name="Philox has_uint32",
            minimum=0,
            maximum=1,
        ),
        "uinteger": _exact_bounded_integer(
            state["uinteger"],
            name="Philox uinteger",
            minimum=0,
            maximum=_UINT32_LIMIT - 1,
        ),
        "state_sha256": _thinning._rng_state_sha256(state),
        "snapshot_sha256": "0" * 64,
    }
    values["snapshot_sha256"] = _thinning._semantic_digest(_snapshot_payload(values))
    return PhiloxRouteStateSnapshot(
        **values,
        _construction_token=_SNAPSHOT_TOKEN,
    )


def _capture_philox_state(rng: object) -> PhiloxRouteStateSnapshot:
    generator = _thinning._require_philox_rng(rng)
    state = copy.deepcopy(generator.bit_generator.state)
    result = _snapshot_from_state(state)
    if _thinning._rng_state_sha256(generator.bit_generator.state) != (
        result.state_sha256
    ):
        raise PluginBridgeContinuousRouteEvidenceError(
            "Philox state changed while it was being snapshotted"
        )
    return result


def _generator_from_snapshot(
    snapshot: PhiloxRouteStateSnapshot,
) -> np.random.Generator:
    checked = _validate_snapshot(snapshot)
    bit_generator = np.random.Philox(0)
    bit_generator.state = copy.deepcopy(
        _philox_state_mapping(_snapshot_values(checked))
    )
    generator = np.random.Generator(bit_generator)
    reconstructed = _capture_philox_state(generator)
    for name in _snapshot_fields():
        if getattr(reconstructed, name) != getattr(checked, name):
            raise PluginBridgeContinuousRouteEvidenceError(
                "NumPy did not reconstruct the exact Philox route state"
            )
    return generator


def _evidence_runtime_sha256() -> str:
    probe = np.random.Generator(np.random.Philox(0))
    probe_snapshot = _capture_philox_state(probe)
    return _thinning._semantic_digest(
        {
            "domain": "plugin-bridge-continuous-route-evidence-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "numpy_version": np.__version__,
            "philox_type_module": np.random.Philox.__module__,
            "philox_type_name": np.random.Philox.__name__,
            "snapshot_schema": PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION,
            "probe_snapshot_sha256": probe_snapshot.snapshot_sha256,
            "policy": PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_POLICY,
        }
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: value for name, value in values.items() if name != "certificate_sha256"
    }


@dataclass(frozen=True, eq=False, init=False)
class ContinuousRouteEvidenceCertificate:
    """Transitive boundary for checkpoint-twenty-one route replay evidence."""

    schema_version: str
    certificate_scope: str
    evidence_policy: str
    philox_snapshot_schema_version: str
    evidence_role_sha256: str
    process_parameter_sha256: str
    thinning_certificate_sha256: str
    thinning_role_sha256: str
    rate_certificate_sha256: str
    thinning_runtime_sha256: str
    evidence_runtime_sha256: str
    rng_bit_generator: str
    delegated_live_route_draw_certified: bool
    exact_canonical_philox_pre_post_state_certified: bool
    same_runtime_finite_resolution_route_replay_certified: bool
    candidate_semantic_and_post_state_replay_certified: bool
    offline_validation_no_caller_rng_certified: bool
    all_returned_route_kinds_supported: bool
    positive_dimensional_destination_classification_certified: bool
    unequal_positive_dimensional_replacement_classification_certified: bool
    source_occurrence_and_multiplicity_custody_certified: bool
    destination_coordinate_and_factor_custody_certified: bool
    bounded_raw_normal_word_trace_certified: bool
    exact_categorical_law_certified: bool
    exact_integer_law_certified: bool
    exact_gaussian_law_certified: bool
    analytic_lebesgue_output_law_certified: bool
    ideal_distribution_recovery_certified: bool
    unconditional_continuous_route_occurrence_certified: bool
    all_route_rate_totality_certified: bool
    sampler_liveness_certified: bool
    active_controlled_target_certified: bool
    conditional_posterior_or_doob_target: bool
    continuous_drift_admissible: bool
    initializer_admissible: bool
    path_admissible: bool
    full_sampler_admissible: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ContinuousRouteEvidenceCertificate cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("continuous-route certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("continuous-route certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "plugin-bridge-continuous-route-evidence-certificate-v1",
            self.certificate_sha256,
        )

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("continuous-route certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(ContinuousRouteEvidenceCertificate.__annotations__)


def _validate_certificate(
    certificate: object,
) -> ContinuousRouteEvidenceCertificate:
    if type(certificate) is not ContinuousRouteEvidenceCertificate:
        raise TypeError(
            "certificate must be an exact ContinuousRouteEvidenceCertificate"
        )
    expected_text = {
        "schema_version": PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_SCHEMA_VERSION,
        "certificate_scope": PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_SCOPE,
        "evidence_policy": PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_POLICY,
        "philox_snapshot_schema_version": (
            PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION
        ),
        "rng_bit_generator": _PHILOX_BIT_GENERATOR,
    }
    for name, expected in expected_text.items():
        if getattr(certificate, name) != expected:
            raise ValueError("continuous-route certificate %s differs" % name)
    for name in (
        "evidence_role_sha256",
        "process_parameter_sha256",
        "thinning_certificate_sha256",
        "thinning_role_sha256",
        "rate_certificate_sha256",
        "thinning_runtime_sha256",
        "evidence_runtime_sha256",
        "certificate_sha256",
    ):
        _thinning._require_sha256(
            getattr(certificate, name), name="certificate.%s" % name
        )
    true_flags = (
        "delegated_live_route_draw_certified",
        "exact_canonical_philox_pre_post_state_certified",
        "same_runtime_finite_resolution_route_replay_certified",
        "candidate_semantic_and_post_state_replay_certified",
        "offline_validation_no_caller_rng_certified",
        "all_returned_route_kinds_supported",
        "positive_dimensional_destination_classification_certified",
        "unequal_positive_dimensional_replacement_classification_certified",
        "source_occurrence_and_multiplicity_custody_certified",
        "destination_coordinate_and_factor_custody_certified",
        "passed",
    )
    false_flags = (
        "bounded_raw_normal_word_trace_certified",
        "exact_categorical_law_certified",
        "exact_integer_law_certified",
        "exact_gaussian_law_certified",
        "analytic_lebesgue_output_law_certified",
        "ideal_distribution_recovery_certified",
        "unconditional_continuous_route_occurrence_certified",
        "all_route_rate_totality_certified",
        "sampler_liveness_certified",
        "active_controlled_target_certified",
        "conditional_posterior_or_doob_target",
        "continuous_drift_admissible",
        "initializer_admissible",
        "path_admissible",
        "full_sampler_admissible",
        "runtime_portable",
        "cryptographic_authentication",
    )
    for name in true_flags + false_flags:
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be boolean" % name)
    if any(not getattr(certificate, name) for name in true_flags):
        raise ValueError("continuous-route positive flags are inconsistent")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("continuous-route negative flags are inconsistent")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    if certificate.certificate_sha256 != _thinning._semantic_digest(
        _certificate_payload(values)
    ):
        raise ValueError("continuous-route certificate digest differs")
    return certificate


def _make_certificate(
    thinning_certificate: OperationalThinningCertificate,
    *,
    evidence_role_sha256: str,
) -> ContinuousRouteEvidenceCertificate:
    checked_thinning = _thinning._validate_certificate(thinning_certificate)
    values: Dict[str, object] = {
        "schema_version": PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_SCHEMA_VERSION,
        "certificate_scope": PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_SCOPE,
        "evidence_policy": PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_POLICY,
        "philox_snapshot_schema_version": (
            PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION
        ),
        "evidence_role_sha256": evidence_role_sha256,
        "process_parameter_sha256": checked_thinning.process_parameter_sha256,
        "thinning_certificate_sha256": checked_thinning.certificate_sha256,
        "thinning_role_sha256": checked_thinning.thinning_role_sha256,
        "rate_certificate_sha256": checked_thinning.rate_certificate_sha256,
        "thinning_runtime_sha256": checked_thinning.thinning_runtime_sha256,
        "evidence_runtime_sha256": _evidence_runtime_sha256(),
        "rng_bit_generator": _PHILOX_BIT_GENERATOR,
        "delegated_live_route_draw_certified": True,
        "exact_canonical_philox_pre_post_state_certified": True,
        "same_runtime_finite_resolution_route_replay_certified": True,
        "candidate_semantic_and_post_state_replay_certified": True,
        "offline_validation_no_caller_rng_certified": True,
        "all_returned_route_kinds_supported": True,
        "positive_dimensional_destination_classification_certified": True,
        "unequal_positive_dimensional_replacement_classification_certified": True,
        "source_occurrence_and_multiplicity_custody_certified": True,
        "destination_coordinate_and_factor_custody_certified": True,
        "bounded_raw_normal_word_trace_certified": False,
        "exact_categorical_law_certified": False,
        "exact_integer_law_certified": False,
        "exact_gaussian_law_certified": False,
        "analytic_lebesgue_output_law_certified": False,
        "ideal_distribution_recovery_certified": False,
        "unconditional_continuous_route_occurrence_certified": False,
        "all_route_rate_totality_certified": False,
        "sampler_liveness_certified": False,
        "active_controlled_target_certified": False,
        "conditional_posterior_or_doob_target": False,
        "continuous_drift_admissible": False,
        "initializer_admissible": False,
        "path_admissible": False,
        "full_sampler_admissible": False,
        "runtime_portable": False,
        "cryptographic_authentication": False,
        "passed": True,
        "certificate_sha256": "0" * 64,
    }
    values["certificate_sha256"] = _thinning._semantic_digest(
        _certificate_payload(values)
    )
    return ContinuousRouteEvidenceCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


def _optional_event_metadata(event: object) -> Mapping[str, object]:
    if event is None:
        return {
            "event_type": None,
            "dimension": None,
            "coordinates": None,
        }
    return {
        "event_type": event.event_type,  # type: ignore[attr-defined]
        "dimension": len(event.coordinates),  # type: ignore[attr-defined]
        "coordinates": tuple(event.coordinates),  # type: ignore[attr-defined]
    }


def _candidate_metadata(candidate: ProcessValidReferenceJump) -> Mapping[str, object]:
    if type(candidate) is not ProcessValidReferenceJump:
        raise TypeError("route candidate has the wrong exact type")
    proposal = candidate.proposal
    factors = candidate.factorization
    source = _optional_event_metadata(proposal.source_event)
    destination = _optional_event_metadata(proposal.destination_event)
    destination_dimension = destination["dimension"]
    source_dimension = source["dimension"]
    positive_birth = (
        proposal.kind is HybridJumpKind.BIRTH
        and type(destination_dimension) is int
        and destination_dimension > 0
    )
    positive_replacement = (
        proposal.kind is HybridJumpKind.REPLACEMENT
        and type(destination_dimension) is int
        and destination_dimension > 0
    )
    unequal_positive_replacement = (
        positive_replacement
        and type(source_dimension) is int
        and source_dimension > 0
        and source_dimension != destination_dimension
    )
    return {
        "edit_kind": proposal.kind.value,
        "source_state_sha256": _thinning._configuration_sha256(
            proposal.source_configuration
        ),
        "destination_state_sha256": _thinning._configuration_sha256(
            proposal.destination_configuration
        ),
        "source_occurrence_index": proposal.source_occurrence_index,
        "source_event_type": source["event_type"],
        "source_event_dimension": source["dimension"],
        "source_event_coordinates": source["coordinates"],
        "destination_event_type": destination["event_type"],
        "destination_event_dimension": destination["dimension"],
        "destination_event_coordinates": destination["coordinates"],
        "family_rate": factors.family_rate,
        "family_probability": factors.family_probability,
        "occurrence_probability": factors.occurrence_probability,
        "source_event_multiplicity": factors.source_event_multiplicity,
        "quotient_occurrence_probability": (factors.quotient_occurrence_probability),
        "destination_type_probability": factors.destination_type_probability,
        "destination_coordinate_log_density": (
            factors.destination_coordinate_log_density
        ),
        "destination_log_density": factors.destination_log_density,
        "proposal_log_density": factors.proposal_log_density,
        "unscaled_reference_edge_log_density": (
            factors.unscaled_reference_edge_log_density
        ),
        "continuous_destination": positive_birth or positive_replacement,
        "positive_dimensional_birth": positive_birth,
        "positive_dimensional_replacement": positive_replacement,
        "unequal_positive_dimensional_replacement": (unequal_positive_replacement),
    }


def _metadata_field_matches(supplied: object, expected: object) -> bool:
    """Compare copied route metadata without Python scalar aliases."""

    if expected is None:
        return supplied is None
    if type(expected) is float:
        return type(supplied) is float and _thinning._same_float(
            supplied,
            expected,
        )
    if type(expected) is tuple:
        if type(supplied) is not tuple or len(supplied) != len(expected):
            return False
        return all(
            type(supplied_value) is float
            and type(expected_value) is float
            and _thinning._same_float(supplied_value, expected_value)
            for supplied_value, expected_value in zip(supplied, expected)
        )
    return type(supplied) is type(expected) and supplied == expected


def _evidence_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {
        "certificate",
        "route_draw",
        "pre_route_state",
        "post_route_state",
        "evidence_sha256",
    }
    return {name: value for name, value in values.items() if name not in omitted}


@dataclass(frozen=True, eq=False, init=False)
class OperationalReferenceRouteEvidence:
    """Sealed exact-state replay evidence for one checkpoint-nineteen route."""

    certificate: ContinuousRouteEvidenceCertificate
    certificate_sha256: str
    route_draw: OperationalReferenceRouteDraw
    route_draw_sha256: str
    waiting_draw_sha256: str
    intensity_sha256: str
    envelope_sha256: str
    process_parameter_sha256: str
    pre_route_state: PhiloxRouteStateSnapshot
    pre_route_snapshot_sha256: str
    post_route_state: PhiloxRouteStateSnapshot
    post_route_snapshot_sha256: str
    rng_state_before_sha256: str
    rng_state_after_sha256: str
    edit_kind: str
    source_state_sha256: str
    destination_state_sha256: str
    source_occurrence_index: Optional[int]
    source_event_type: Optional[int]
    source_event_dimension: Optional[int]
    source_event_coordinates: Optional[Tuple[float, ...]]
    destination_event_type: Optional[int]
    destination_event_dimension: Optional[int]
    destination_event_coordinates: Optional[Tuple[float, ...]]
    family_rate: float
    family_probability: float
    occurrence_probability: float
    source_event_multiplicity: int
    quotient_occurrence_probability: float
    destination_type_probability: float
    destination_coordinate_log_density: float
    destination_log_density: float
    proposal_log_density: float
    unscaled_reference_edge_log_density: float
    continuous_destination: bool
    positive_dimensional_birth: bool
    positive_dimensional_replacement: bool
    unequal_positive_dimensional_replacement: bool
    evidence_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalReferenceRouteEvidence cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _EVIDENCE_TOKEN:
            raise TypeError("operational route evidence is module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational route evidence fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("route-evidence certificate digest differs")
        route_draw = values["route_draw"]
        if type(route_draw) is not OperationalReferenceRouteDraw:
            raise TypeError("route_draw has the wrong exact type")
        OperationalReferenceRouteDraw(
            **_thinning._snapshot_fields(route_draw, _thinning._route_fields()),
            _construction_token=_thinning._ROUTE_TOKEN,
        )
        if route_draw.certificate_sha256 != certificate.thinning_certificate_sha256:
            raise ValueError("route evidence belongs to another thinning certificate")
        if values["route_draw_sha256"] != route_draw.route_draw_sha256:
            raise ValueError("route-evidence route digest differs")
        pre = _validate_snapshot(values["pre_route_state"])
        post = _validate_snapshot(values["post_route_state"])
        for name in (
            "certificate_sha256",
            "route_draw_sha256",
            "waiting_draw_sha256",
            "intensity_sha256",
            "envelope_sha256",
            "process_parameter_sha256",
            "pre_route_snapshot_sha256",
            "post_route_snapshot_sha256",
            "rng_state_before_sha256",
            "rng_state_after_sha256",
            "source_state_sha256",
            "destination_state_sha256",
            "evidence_sha256",
        ):
            _thinning._require_sha256(values[name], name="evidence.%s" % name)
        expected_parent_fields = {
            "waiting_draw_sha256": route_draw.waiting_draw_sha256,
            "intensity_sha256": route_draw.intensity_sha256,
            "envelope_sha256": route_draw.envelope_sha256,
            "process_parameter_sha256": route_draw.process_parameter_sha256,
            "pre_route_snapshot_sha256": pre.snapshot_sha256,
            "post_route_snapshot_sha256": post.snapshot_sha256,
            "rng_state_before_sha256": pre.state_sha256,
            "rng_state_after_sha256": post.state_sha256,
        }
        for name, expected in expected_parent_fields.items():
            if values[name] != expected:
                raise ValueError("route-evidence %s differs" % name)
        if pre.state_sha256 != route_draw.rng_state_before_sha256:
            raise ValueError("pre-route snapshot differs from the route record")
        if post.state_sha256 != route_draw.rng_state_after_sha256:
            raise ValueError("post-route snapshot differs from the route record")
        if pre.snapshot_sha256 == post.snapshot_sha256:
            raise ValueError("route evidence did not advance the Philox state")
        metadata = _candidate_metadata(route_draw.candidate)
        for name, expected in metadata.items():
            supplied = values[name]
            if not _metadata_field_matches(supplied, expected):
                raise ValueError("route-evidence %s differs" % name)
        for name in (
            "continuous_destination",
            "positive_dimensional_birth",
            "positive_dimensional_replacement",
            "unequal_positive_dimensional_replacement",
        ):
            if type(values[name]) is not bool:
                raise TypeError("route-evidence %s must be boolean" % name)
        expected_digest = _thinning._semantic_digest(_evidence_payload(values))
        if values["evidence_sha256"] != expected_digest:
            raise ValueError("operational route evidence digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational route evidence is not a pickle object")


def _evidence_fields() -> Tuple[str, ...]:
    return tuple(OperationalReferenceRouteEvidence.__annotations__)


class ContinuousRouteEvidenceOwner:
    """Immutable successor owner for exact-state route replay evidence."""

    __slots__ = ("_thinning_owner", "_reference_composer", "_role", "_certificate")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ContinuousRouteEvidenceOwner cannot be subclassed")

    def __init__(
        self,
        thinning_owner: OperationalJumpThinning,
        reference_composer: ProcessValidReferenceJumpComposer,
        role: str,
        certificate: ContinuousRouteEvidenceCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("continuous-route owners require certification")
        if type(thinning_owner) is not OperationalJumpThinning:
            raise TypeError("thinning_owner has the wrong exact type")
        if type(reference_composer) is not ProcessValidReferenceJumpComposer:
            raise TypeError("reference_composer has the wrong exact type")
        checked_role = _thinning._require_sha256(role, name="evidence_role_sha256")
        checked_certificate = _validate_certificate(certificate)
        if checked_certificate.evidence_role_sha256 != checked_role:
            raise ValueError("continuous-route role differs from certificate")
        object.__setattr__(self, "_thinning_owner", thinning_owner)
        object.__setattr__(self, "_reference_composer", reference_composer)
        object.__setattr__(self, "_role", checked_role)
        object.__setattr__(self, "_certificate", checked_certificate)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("ContinuousRouteEvidenceOwner is immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("ContinuousRouteEvidenceOwner is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("continuous-route owners are not pickle objects")

    @property
    def certificate(self) -> ContinuousRouteEvidenceCertificate:
        return self._certificate

    @property
    def thinning_owner(self) -> OperationalJumpThinning:
        return self._thinning_owner

    @property
    def reference_composer(self) -> ProcessValidReferenceJumpComposer:
        return self._reference_composer

    def _require_live_binding(self) -> ContinuousRouteEvidenceCertificate:
        _thinning._require_binary64_environment()
        if type(self._thinning_owner) is not OperationalJumpThinning:
            raise TypeError("thinning owner has the wrong exact type")
        if type(self._reference_composer) is not ProcessValidReferenceJumpComposer:
            raise TypeError("reference composer has the wrong exact type")
        if self._thinning_owner.reference_composer is not self._reference_composer:
            raise ValueError(
                "route-evidence and thinning owners use different references"
            )
        thinning_certificate = self._thinning_owner._require_live_binding()
        if self.certificate.evidence_runtime_sha256 != _evidence_runtime_sha256():
            raise ValueError("live continuous-route runtime differs from certificate")
        expected = _make_certificate(
            thinning_certificate,
            evidence_role_sha256=self._role,
        )
        for name in _certificate_fields():
            if not _thinning._field_matches(
                name,
                getattr(self.certificate, name),
                getattr(expected, name),
            ):
                raise ValueError("continuous-route certificate field %s differs" % name)
        _thinning._require_binary64_environment()
        return self.certificate

    def draw_reference_route_with_evidence(
        self,
        waiting_draw: OperationalWaitingTimeDraw,
        intensity: ReferenceCandidateIntensity,
        envelope: TotalizedJumpRateEnvelope,
        *,
        rng: np.random.Generator,
    ) -> OperationalReferenceRouteEvidence:
        """Delegate one live route draw and retain exact pre/post Philox state."""

        self._require_live_binding()
        checked_rng = _thinning._require_philox_rng(rng)
        self._thinning_owner.validate_waiting_time(
            waiting_draw,
            intensity,
            envelope,
        )
        pre = _capture_philox_state(checked_rng)
        route = self._thinning_owner.draw_reference_route(
            waiting_draw,
            intensity,
            envelope,
            rng=checked_rng,
        )
        post = _capture_philox_state(checked_rng)
        if route.rng_state_before_sha256 != pre.state_sha256:
            raise PluginBridgeContinuousRouteEvidenceError(
                "delegated route began from another Philox state"
            )
        if route.rng_state_after_sha256 != post.state_sha256:
            raise PluginBridgeContinuousRouteEvidenceError(
                "delegated route ended at another Philox state"
            )
        metadata = _candidate_metadata(route.candidate)
        values: Dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "route_draw": route,
            "route_draw_sha256": route.route_draw_sha256,
            "waiting_draw_sha256": route.waiting_draw_sha256,
            "intensity_sha256": route.intensity_sha256,
            "envelope_sha256": route.envelope_sha256,
            "process_parameter_sha256": route.process_parameter_sha256,
            "pre_route_state": pre,
            "pre_route_snapshot_sha256": pre.snapshot_sha256,
            "post_route_state": post,
            "post_route_snapshot_sha256": post.snapshot_sha256,
            "rng_state_before_sha256": pre.state_sha256,
            "rng_state_after_sha256": post.state_sha256,
            **metadata,
            "evidence_sha256": "0" * 64,
        }
        values["evidence_sha256"] = _thinning._semantic_digest(
            _evidence_payload(values)
        )
        result = OperationalReferenceRouteEvidence(
            **values,
            _construction_token=_EVIDENCE_TOKEN,
        )
        self.validate_reference_route_evidence(
            result,
            waiting_draw,
            intensity,
            envelope,
        )
        unchanged = _capture_philox_state(checked_rng)
        for name in _snapshot_fields():
            if getattr(unchanged, name) != getattr(post, name):
                raise PluginBridgeContinuousRouteEvidenceError(
                    "offline route validation consumed caller randomness"
                )
        self._require_live_binding()
        return result

    def validate_reference_route_evidence(
        self,
        evidence: OperationalReferenceRouteEvidence,
        waiting_draw: OperationalWaitingTimeDraw,
        intensity: ReferenceCandidateIntensity,
        envelope: TotalizedJumpRateEnvelope,
    ) -> OperationalReferenceRouteEvidence:
        """Replay one route using only a fresh local same-runtime Philox."""

        self._require_live_binding()
        if type(evidence) is not OperationalReferenceRouteEvidence:
            raise TypeError("evidence has the wrong exact type")
        OperationalReferenceRouteEvidence(
            **{name: getattr(evidence, name) for name in _evidence_fields()},
            _construction_token=_EVIDENCE_TOKEN,
        )
        if evidence.certificate is not self.certificate:
            raise ValueError("route evidence belongs to a different evidence owner")
        route = self._thinning_owner.validate_reference_route(
            evidence.route_draw,
            waiting_draw,
            intensity,
            envelope,
        )
        if route.route_draw_sha256 != evidence.route_draw_sha256:
            raise ValueError("route evidence and delegated route differ")
        checked_intensity = self._reference_composer.validate_candidate_intensity(
            intensity
        )
        replay_rng = _generator_from_snapshot(evidence.pre_route_state)
        replayed = self._reference_composer.sample_candidate_from_intensity(
            checked_intensity,
            rng=replay_rng,
        )
        if replayed is None:
            raise PluginBridgeContinuousRouteEvidenceError(
                "an admitted route replay unexpectedly returned no candidate"
            )
        replayed = self._reference_composer.validate_candidate(replayed)
        _thinning._require_candidate_intensity_binding(replayed, checked_intensity)
        replayed_sha256 = _thinning._candidate_sha256(replayed)
        if replayed_sha256 != route.candidate_sha256:
            raise PluginBridgeContinuousRouteEvidenceError(
                "same-runtime Philox replay produced a different route candidate"
            )
        replay_post = _capture_philox_state(replay_rng)
        for name in _snapshot_fields():
            if getattr(replay_post, name) != getattr(evidence.post_route_state, name):
                raise PluginBridgeContinuousRouteEvidenceError(
                    "same-runtime route replay produced a different Philox post-state"
                )
        self._thinning_owner.validate_reference_route(
            evidence.route_draw,
            waiting_draw,
            intensity,
            envelope,
        )
        self._require_live_binding()
        return evidence


def certify_plugin_bridge_continuous_route_evidence(
    thinning_owner: OperationalJumpThinning,
    *,
    evidence_policy: object,
    evidence_role_sha256: object,
) -> ContinuousRouteEvidenceOwner:
    """Certify same-runtime replay evidence over one frozen thinning owner."""

    if type(evidence_policy) is not str:
        raise TypeError("evidence_policy must be exact text")
    if evidence_policy != PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_POLICY:
        raise ValueError("only the exported continuous-route policy is supported")
    role = _thinning._require_sha256(
        evidence_role_sha256,
        name="evidence_role_sha256",
    )
    if type(thinning_owner) is not OperationalJumpThinning:
        raise TypeError("thinning_owner has the wrong exact type")
    thinning_certificate = thinning_owner._require_live_binding()
    reference_composer = thinning_owner.reference_composer
    certificate = _make_certificate(
        thinning_certificate,
        evidence_role_sha256=role,
    )
    owner = ContinuousRouteEvidenceOwner(
        thinning_owner,
        reference_composer,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_plugin_bridge_continuous_route_evidence(
    thinning_owner: OperationalJumpThinning,
    owner: ContinuousRouteEvidenceOwner,
    *,
    evidence_policy: object,
    evidence_role_sha256: object,
) -> ContinuousRouteEvidenceOwner:
    """Require owner identity and reconstructed transitive route custody."""

    if type(evidence_policy) is not str:
        raise TypeError("evidence_policy must be exact text")
    if evidence_policy != PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_POLICY:
        raise ValueError("only the exported continuous-route policy is supported")
    role = _thinning._require_sha256(
        evidence_role_sha256,
        name="evidence_role_sha256",
    )
    if type(owner) is not ContinuousRouteEvidenceOwner:
        raise TypeError("owner must be an exact ContinuousRouteEvidenceOwner")
    if owner.thinning_owner is not thinning_owner:
        raise ValueError("continuous-route owner uses another thinning owner")
    if owner.certificate.evidence_role_sha256 != role:
        raise ValueError("continuous-route owner uses another role")
    owner._require_live_binding()
    return owner


def validate_plugin_bridge_continuous_route_evidence_certificate(
    thinning_owner: OperationalJumpThinning,
    owner: ContinuousRouteEvidenceOwner,
    *,
    evidence_policy: object,
    evidence_role_sha256: object,
) -> ContinuousRouteEvidenceCertificate:
    """Return the reconstructed live checkpoint-twenty-one certificate."""

    return require_matching_plugin_bridge_continuous_route_evidence(
        thinning_owner,
        owner,
        evidence_policy=evidence_policy,
        evidence_role_sha256=evidence_role_sha256,
    ).certificate


__all__ = [
    "PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_POLICY",
    "PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_SCOPE",
    "PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION",
    "ContinuousRouteEvidenceCertificate",
    "ContinuousRouteEvidenceOwner",
    "OperationalReferenceRouteEvidence",
    "PhiloxRouteStateSnapshot",
    "PluginBridgeContinuousRouteEvidenceError",
    "certify_plugin_bridge_continuous_route_evidence",
    "require_matching_plugin_bridge_continuous_route_evidence",
    "validate_plugin_bridge_continuous_route_evidence_certificate",
]
