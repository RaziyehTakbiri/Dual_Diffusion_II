"""Independent structural verifier for a captured adapted-evidence bundle.

This module consumes only immutable bytes and explicit reason-code registries.
It deliberately does not import the adapted-evidence producer, publication
payload projections, expected-bundle producer, generated fixtures/adapters, or
any oracle/authority implementation.

The bounded canonical-JSON and Phase-C schema primitives are reused from the
already implementation-separated expected-leaf verifier.  The output-blind
case-input schema, adapted-bundle envelope, adapter manifest, complete-sample
commitment, raw-reconstruction policy, and all bindings among them are parsed
and checked here rather than delegated to either producer.

A successful result is a structural development result only.  In particular,
it does not prove that an adapter produced the bytes freshly, that output
blindness or containment was enforced, that reviewed source was loaded, that
the payloads are semantically true, or that any conformance decision is
eligible.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import NamedTuple, Tuple

from . import adapter_expected_leaf_bundle_verifier as _leaf


OUTPUT_BLIND_CASE_INPUT_ARTIFACT_TYPE = (
    "heterodiff.adapter.output-blind-case-input.v1"
)
OUTPUT_BLIND_CASE_INPUT_DIGEST_DOMAIN = (
    OUTPUT_BLIND_CASE_INPUT_ARTIFACT_TYPE
)
ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE = (
    "heterodiff.adapter.adapted-evidence-bundle.v1"
)
ADAPTED_EVIDENCE_BUNDLE_DIGEST_DOMAIN = (
    ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE
)
ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_INPUT_DIGEST_DOMAIN = (
    "heterodiff.adapter.development-independent-adapted-evidence-bundle-"
    "verification-input.v1"
)
ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.development-independent-adapted-evidence-bundle-"
    "verification-receipt.v1"
)
ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_RECEIPT_DIGEST_DOMAIN = (
    ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE
)
ADAPTED_EVIDENCE_BUNDLE_VERIFIER_ID = (
    "heterodiff-development-independent-adapted-evidence-bundle-verifier-v1"
)
ADAPTED_EVIDENCE_BUNDLE_VERIFIER_IMPLEMENTATION_STATUS = (
    "DEVELOPMENT_ONLY_IMPLEMENTATION_SEPARATED_ADAPTED_EVIDENCE_VERIFIER"
)
ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_STATUS = (
    "ADAPTED_EVIDENCE_SCHEMAS_AND_BINDINGS_MATCHED_"
    "UNATTESTED_DEVELOPMENT_OUTPUT"
)
ADAPTED_EVIDENCE_BUNDLE_VERIFIER_DECISION_STATUS = "NOT_MADE_BY_VERIFIER"
ADAPTED_EVIDENCE_BUNDLE_SEMANTIC_SCOPE_ID = (
    "output-blind-case-input-and-adapted-evidence-structural-bindings-only"
)

PRIVATE_PARTITION_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-partition.v1"
)
SAMPLE_MANIFEST_DIGEST_DOMAIN = (
    "heterodiff.adapter.sample-manifest.v1"
)
COMPLETE_SAMPLE_DIGEST_DOMAIN = (
    "heterodiff.adapter.complete-sample-publication.v1"
)
RAW_RECONSTRUCTION_ABSENCE_DIGEST_DOMAIN = (
    "heterodiff.adapter.raw-reconstruction-absence.v1"
)
RAW_RECONSTRUCTION_BYTES_DIGEST_DOMAIN = (
    "heterodiff.adapter.raw-reconstruction-bytes.v1"
)
REASON_CODE_REGISTRY_DIGEST_DOMAIN = (
    "heterodiff.adapter.adapted-evidence-reason-code-registry.v1"
)
CAPABILITY_CONFORMANCE_PLAN_DIGEST_DOMAIN = (
    "heterodiff.adapter.capability-conformance-plan.v1"
)

MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES = 4 * 1024 * 1024
MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES = 32 * 1024 * 1024
MAXIMUM_ADAPTED_EVIDENCE_VERIFICATION_INPUT_BYTES = (
    MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES
    + MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES
    + (2 * _leaf.MAXIMUM_SINGLE_PAYLOAD_BYTES)
)
MAXIMUM_ADAPTED_EVIDENCE_VERIFICATION_RECEIPT_BYTES = 64 * 1024

_CASE_INPUT_KEYS = (
    "artifact_type",
    "format_version",
    "partition",
    "source",
    "split_manifest",
)
_CASE_PARTITION_KEYS = ("group_id", "sample_id", "split")
_CASE_SOURCE_KEYS = ("byte_count", "payload_base64")
_CASE_SPLIT_KEYS = ("entries", "unicode_profile")
_CASE_SPLIT_ENTRY_KEYS = ("group_id", "sample_id", "split")
_BUNDLE_KEYS = (
    "adapted",
    "artifact_type",
    "case_input_sha256",
    "format_version",
    "source_byte_count",
    "source_sha256",
    "split_manifest_sha256",
)
_ADAPTED_KEYS = (
    "adapter_descriptor",
    "adapter_manifest",
    "complete_sample_commitment",
    "coverage_ledger",
    "detached_native_observation",
    "evaluation_labels",
    "fitted_state",
    "identity_bearing_native_configuration",
    "private_provenance",
    "raw_byte_reconstruction",
    "semantic_reconstruction",
    "source_inventory",
    "static_context",
)
_MANIFEST_KEYS = (
    "coverage_ledger_sha256",
    "descriptor_sha256",
    "evaluation_labels_sha256",
    "fitted_state_sha256",
    "native_observation_sha256",
    "partition",
    "private_provenance_sha256",
    "schema_sha256",
    "schema_version",
    "semantic_reconstruction_sha256",
    "source_sha256",
    "source_size_bytes",
    "split_manifest_sha256",
    "static_context_sha256",
)
_COMPLETE_SAMPLE_KEYS = (
    "adapter_manifest_sha256",
    "coverage_ledger_sha256",
    "evaluation_labels_sha256",
    "fitted_state_sha256",
    "native_observation_sha256",
    "private_provenance_sha256",
    "raw_reconstruction_sha256",
    "semantic_reconstruction_sha256",
    "source_inventory_sha256",
    "static_context_sha256",
)

_WRAPPER_DOMAINS = MappingProxyType(
    {
        "adapter_descriptor": _leaf.DESCRIPTOR_DIGEST_DOMAIN,
        "adapter_manifest": SAMPLE_MANIFEST_DIGEST_DOMAIN,
        "complete_sample_commitment": COMPLETE_SAMPLE_DIGEST_DOMAIN,
        "coverage_ledger": _leaf.PRIVATE_COVERAGE_LEDGER_DIGEST_DOMAIN,
        "detached_native_observation": (
            _leaf.NATIVE_OBSERVATION_DIGEST_DOMAIN
        ),
        "evaluation_labels": (
            _leaf.PRIVATE_EVALUATION_LABELS_DIGEST_DOMAIN
        ),
        "fitted_state": _leaf.PRIVATE_FITTED_STATE_DIGEST_DOMAIN,
        "identity_bearing_native_configuration": (
            _leaf.PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN
        ),
        "private_provenance": (
            _leaf.PRIVATE_PROVENANCE_PAYLOAD_DIGEST_DOMAIN
        ),
        "semantic_reconstruction": (
            _leaf.PRIVATE_SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN
        ),
        "source_inventory": _leaf.PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN,
        "static_context": _leaf.PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN,
    }
)


class AdaptedEvidenceBundleVerificationCode(str, Enum):
    INPUT_TYPE = "ADAPTED_EVIDENCE_INPUT_TYPE"
    INPUT_RESOURCE = "ADAPTED_EVIDENCE_INPUT_RESOURCE"
    CASE_INPUT_INVALID = "ADAPTED_EVIDENCE_CASE_INPUT_INVALID"
    JSON_INVALID = "ADAPTED_EVIDENCE_JSON_INVALID"
    BINDING_MISMATCH = "ADAPTED_EVIDENCE_BINDING_MISMATCH"
    RECEIPT_INVALID = "ADAPTED_EVIDENCE_RECEIPT_INVALID"
    CANONICALIZATION_FAILED = "ADAPTED_EVIDENCE_CANONICALIZATION_FAILED"
    INTERNAL_ERROR = "ADAPTED_EVIDENCE_INTERNAL_ERROR"


_ERROR_MESSAGES = MappingProxyType(
    {
        AdaptedEvidenceBundleVerificationCode.INPUT_TYPE: (
            "adapted-evidence verifier input has an invalid exact type"
        ),
        AdaptedEvidenceBundleVerificationCode.INPUT_RESOURCE: (
            "adapted-evidence verifier input exceeds a fixed resource bound"
        ),
        AdaptedEvidenceBundleVerificationCode.CASE_INPUT_INVALID: (
            "output-blind case-input bytes are invalid"
        ),
        AdaptedEvidenceBundleVerificationCode.JSON_INVALID: (
            "adapted-evidence bytes are not strict canonical-profile JSON"
        ),
        AdaptedEvidenceBundleVerificationCode.BINDING_MISMATCH: (
            "adapted-evidence cross-object bindings do not match"
        ),
        AdaptedEvidenceBundleVerificationCode.RECEIPT_INVALID: (
            "adapted-evidence verification receipt is invalid"
        ),
        AdaptedEvidenceBundleVerificationCode.CANONICALIZATION_FAILED: (
            "adapted-evidence canonical serialization failed"
        ),
        AdaptedEvidenceBundleVerificationCode.INTERNAL_ERROR: (
            "adapted-evidence verification failed internally"
        ),
    }
)


class AdaptedEvidenceBundleVerificationError(ValueError):
    """One closed, interpolation-free adapted-evidence verification failure."""

    def __init__(self, code: AdaptedEvidenceBundleVerificationCode) -> None:
        if type(code) is not AdaptedEvidenceBundleVerificationCode:
            raise TypeError("adapted-evidence verification code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


IndependentAdaptedEvidenceBundleVerificationError = (
    AdaptedEvidenceBundleVerificationError
)


def _fail(code: AdaptedEvidenceBundleVerificationCode) -> None:
    raise AdaptedEvidenceBundleVerificationError(code) from None


def _reason_codes(value: object) -> Tuple[str, ...]:
    if type(value) is not tuple or len(value) > _leaf.MAXIMUM_REASON_CODES:
        raise TypeError("reason-code registry must be an exact bounded tuple")
    try:
        result = tuple(_leaf._require_public_id(item) for item in value)
    except _leaf._Rejected as error:
        raise ValueError("reason-code registry is invalid") from error
    if result != tuple(sorted(set(result))):
        raise ValueError("reason-code registry must be sorted and unique")
    return result


def _reason_registry_bytes(value: Tuple[str, ...]) -> bytes:
    return _leaf._canonical_json_bytes(
        {"reason_codes": list(value)},
        maximum=_leaf.MAXIMUM_SINGLE_PAYLOAD_BYTES,
    )


def _reason_registry_sha256(value: Tuple[str, ...]) -> str:
    return _leaf._domain_sha256(
        REASON_CODE_REGISTRY_DIGEST_DOMAIN,
        _reason_registry_bytes(value),
    )


def _capability_plan_tree(
    descriptor: _leaf._DescriptorMaterial,
) -> dict:
    representation_ids = descriptor.supported_representation_ids
    return {
        "atomic_grid": (
            "required"
            if _leaf.ATOMIC_COUNTING_GRID_REPRESENTATION_ID
            in representation_ids
            else "not_applicable"
        ),
        "coverage": "required",
        "evaluation_labels": (
            "required"
            if descriptor.evaluation_labels
            else "assert_empty"
        ),
        "fitted_state": (
            "required" if descriptor.fitted_state else "assert_no_fit"
        ),
        "multiplicity_mode": descriptor.multiplicity_mode,
        "native": "required",
        "provenance": (
            "required"
            if descriptor.private_provenance
            else "assert_empty"
        ),
        "raw_reconstruction": (
            "required"
            if descriptor.raw_byte_reconstruction
            else "not_applicable"
        ),
        "representation_ids": list(representation_ids),
        "semantic_reconstruction": "required",
        "static_context": (
            "required" if descriptor.static_context else "assert_empty"
        ),
        "time_measure": descriptor.time_measure,
    }


def _capability_plan_sha256(
    descriptor: _leaf._DescriptorMaterial,
) -> str:
    return _leaf._domain_sha256(
        CAPABILITY_CONFORMANCE_PLAN_DIGEST_DOMAIN,
        _leaf._canonical_json_bytes(
            _capability_plan_tree(descriptor),
            maximum=_leaf.MAXIMUM_SINGLE_PAYLOAD_BYTES,
        ),
    )


@dataclass(frozen=True)
class IndependentAdaptedEvidenceBundleVerificationInputV1:
    """Raw output-blind input, raw adapted bundle, and closed reason registries."""

    case_input_bytes: bytes
    adapted_evidence_bundle_bytes: bytes
    allowed_exclusion_reason_codes: Tuple[str, ...] = ()
    allowed_censor_reason_codes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self) is not IndependentAdaptedEvidenceBundleVerificationInputV1:
            raise TypeError("adapted-evidence verifier input must be exact")
        _leaf._exact_bytes(
            self.case_input_bytes,
            maximum=MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES,
        )
        _leaf._exact_bytes(
            self.adapted_evidence_bundle_bytes,
            maximum=MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES,
        )
        exclusions = _reason_codes(self.allowed_exclusion_reason_codes)
        censors = _reason_codes(self.allowed_censor_reason_codes)
        if len(exclusions) + len(censors) > _leaf.MAXIMUM_REASON_CODES:
            raise ValueError("combined reason-code registry exceeds its bound")
        total = (
            len(self.case_input_bytes)
            + len(self.adapted_evidence_bundle_bytes)
            + len(_reason_registry_bytes(exclusions))
            + len(_reason_registry_bytes(censors))
        )
        if total > MAXIMUM_ADAPTED_EVIDENCE_VERIFICATION_INPUT_BYTES:
            raise ValueError("adapted-evidence verifier input exceeds aggregate")


def _snapshot_input(
    value: object,
) -> IndependentAdaptedEvidenceBundleVerificationInputV1:
    if type(value) is not IndependentAdaptedEvidenceBundleVerificationInputV1:
        _fail(AdaptedEvidenceBundleVerificationCode.INPUT_TYPE)
    try:
        IndependentAdaptedEvidenceBundleVerificationInputV1.__post_init__(value)
        return IndependentAdaptedEvidenceBundleVerificationInputV1(
            case_input_bytes=value.case_input_bytes,
            adapted_evidence_bundle_bytes=value.adapted_evidence_bundle_bytes,
            allowed_exclusion_reason_codes=tuple(
                value.allowed_exclusion_reason_codes
            ),
            allowed_censor_reason_codes=tuple(
                value.allowed_censor_reason_codes
            ),
        )
    except AdaptedEvidenceBundleVerificationError:
        raise
    except (AttributeError, TypeError):
        _fail(AdaptedEvidenceBundleVerificationCode.INPUT_TYPE)
    except ValueError:
        _fail(AdaptedEvidenceBundleVerificationCode.INPUT_RESOURCE)


class _CaseMaterial(NamedTuple):
    source_bytes: bytes
    source_sha256: str
    partition: _leaf._PartitionMaterial
    partition_sha256: str
    split_entries: Tuple[_leaf._PartitionMaterial, ...]
    split_manifest_sha256: str
    case_input_sha256: str


def _parse_case_partition(value: object) -> _leaf._PartitionMaterial:
    tree = _leaf._require_keys(value, _CASE_PARTITION_KEYS)
    split = tree["split"]
    if split not in ("train", "validation", "test"):
        _leaf._reject()
    return _leaf._PartitionMaterial(
        sample_id=_leaf._require_private_text(tree["sample_id"]),
        group_id=_leaf._require_private_text(tree["group_id"]),
        split=split,
    )


def _partition_payload_bytes(
    value: _leaf._PartitionMaterial,
) -> bytes:
    return _leaf._canonical_json_bytes(
        {
            "group_id": value.group_id,
            "sample_id": value.sample_id,
            "split": value.split,
            "unicode_profile": _leaf.UNICODE_PROFILE,
        },
        maximum=_leaf.MAXIMUM_SINGLE_PAYLOAD_BYTES,
    )


def _parse_case_source(value: object) -> bytes:
    tree = _leaf._require_keys(value, _CASE_SOURCE_KEYS)
    byte_count = _leaf._require_integer(
        tree["byte_count"],
        maximum=_leaf.MAXIMUM_SOURCE_BYTES,
        minimum=1,
    )
    encoded = tree["payload_base64"]
    if type(encoded) is not str:
        _leaf._reject()
    try:
        encoded_bytes = encoded.encode("ascii", "strict")
    except UnicodeError:
        _leaf._reject()
    if len(encoded_bytes) != 4 * ((byte_count + 2) // 3):
        _leaf._reject()
    try:
        raw = base64.b64decode(encoded_bytes, validate=True)
    except (TypeError, ValueError):
        _leaf._reject()
    if (
        len(raw) != byte_count
        or base64.b64encode(raw) != encoded_bytes
    ):
        _leaf._reject()
    return raw


def _parse_case_input(value: bytes) -> _CaseMaterial:
    tree = _leaf._strict_json_bytes(
        value, maximum=MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES
    )
    _leaf._require_keys(tree, _CASE_INPUT_KEYS)
    if (
        tree["artifact_type"] != OUTPUT_BLIND_CASE_INPUT_ARTIFACT_TYPE
        or tree["format_version"] != "1"
    ):
        _leaf._reject()
    partition = _parse_case_partition(tree["partition"])
    source_bytes = _parse_case_source(tree["source"])
    split_tree = _leaf._require_keys(
        tree["split_manifest"], _CASE_SPLIT_KEYS
    )
    if split_tree["unicode_profile"] != _leaf.UNICODE_PROFILE:
        _leaf._reject()
    entries = _leaf._require_list(
        split_tree["entries"], maximum=_leaf.MAXIMUM_SPLIT_ENTRIES
    )
    for entry in entries:
        _parse_case_partition(
            _leaf._require_keys(entry, _CASE_SPLIT_ENTRY_KEYS)
        )
    split_bytes = _leaf._canonical_json_bytes(
        split_tree, maximum=MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES
    )
    split_entries, split_sha256 = _leaf._parse_split_manifest(split_bytes)
    if partition not in split_entries:
        _leaf._reject()
    partition_bytes = _partition_payload_bytes(partition)
    return _CaseMaterial(
        source_bytes=source_bytes,
        source_sha256=_leaf._plain_sha256(source_bytes),
        partition=partition,
        partition_sha256=_leaf._domain_sha256(
            PRIVATE_PARTITION_DIGEST_DOMAIN, partition_bytes
        ),
        split_entries=split_entries,
        split_manifest_sha256=split_sha256,
        case_input_sha256=_leaf._domain_sha256(
            OUTPUT_BLIND_CASE_INPUT_DIGEST_DOMAIN, value
        ),
    )


class _ManifestMaterial(NamedTuple):
    sample_root_sha256: str


def _parse_manifest(
    wrapper: _leaf._WrapperMaterial,
    *,
    case: _CaseMaterial,
    descriptor: _leaf._DescriptorMaterial,
    configuration: _leaf._ConfigurationMaterial,
    inventory: _leaf._InventoryMaterial,
    coverage: _leaf._CoverageMaterial,
    static_context: _leaf._KeyedLeafMaterial,
    evaluation_labels: _leaf._KeyedLeafMaterial,
    provenance: _leaf._ProvenanceMaterial,
    fitted: _leaf._FittedMaterial,
    semantic: _leaf._SemanticMaterial,
) -> _ManifestMaterial:
    tree = _leaf._require_keys(wrapper.payload, _MANIFEST_KEYS)
    partition_tree = _leaf._require_keys(
        tree["partition"], _CASE_PARTITION_KEYS
    )
    manifest_partition = _parse_case_partition(partition_tree)
    digest_values = {
        name: _leaf._require_digest(tree[name])
        for name in (
            "coverage_ledger_sha256",
            "descriptor_sha256",
            "evaluation_labels_sha256",
            "fitted_state_sha256",
            "native_observation_sha256",
            "private_provenance_sha256",
            "schema_sha256",
            "semantic_reconstruction_sha256",
            "source_sha256",
            "split_manifest_sha256",
            "static_context_sha256",
        )
    }
    source_size = _leaf._require_integer(
        tree["source_size_bytes"], maximum=_leaf.MAXIMUM_SOURCE_BYTES
    )
    schema_version = _leaf._require_private_text(tree["schema_version"])
    expected = {
        "coverage_ledger_sha256": coverage.phase_c_sha256,
        "descriptor_sha256": descriptor.descriptor_sha256,
        "evaluation_labels_sha256": evaluation_labels.phase_c_sha256,
        "fitted_state_sha256": fitted.phase_c_sha256,
        "native_observation_sha256": (
            configuration.native_observation_sha256
        ),
        "private_provenance_sha256": provenance.phase_c_sha256,
        "schema_sha256": configuration.schema.schema_sha256,
        "semantic_reconstruction_sha256": semantic.phase_c_sha256,
        "source_sha256": case.source_sha256,
        "split_manifest_sha256": case.split_manifest_sha256,
        "static_context_sha256": static_context.phase_c_sha256,
    }
    if (
        digest_values != expected
        or manifest_partition != case.partition
        or source_size != len(case.source_bytes)
        or schema_version != configuration.schema.tree["version"]
        or inventory.source_sha256 != case.source_sha256
    ):
        _leaf._reject()
    return _ManifestMaterial(sample_root_sha256=wrapper.payload_sha256)


def _parse_raw_reconstruction(
    value: object,
    *,
    advertised: bool,
    source_bytes: bytes,
) -> str:
    if advertised:
        budget = _leaf._RawBudget()
        raw = budget.decode(value)
        if raw != source_bytes:
            _leaf._reject()
        return _leaf._domain_sha256(
            RAW_RECONSTRUCTION_BYTES_DIGEST_DOMAIN, raw
        )
    wrapper = _leaf._parse_wrapper(
        value, domain=RAW_RECONSTRUCTION_ABSENCE_DIGEST_DOMAIN
    )
    tree = _leaf._require_keys(wrapper.payload, ("kind",))
    if tree["kind"] != "NOT_ADVERTISED":
        _leaf._reject()
    return wrapper.payload_sha256


def _parse_complete_sample(
    wrapper: _leaf._WrapperMaterial,
    *,
    adapter_manifest_sha256: str,
    raw_reconstruction_sha256: str,
    configuration: _leaf._ConfigurationMaterial,
    inventory: _leaf._InventoryMaterial,
    coverage: _leaf._CoverageMaterial,
    static_context: _leaf._KeyedLeafMaterial,
    evaluation_labels: _leaf._KeyedLeafMaterial,
    provenance: _leaf._ProvenanceMaterial,
    fitted: _leaf._FittedMaterial,
    semantic: _leaf._SemanticMaterial,
) -> str:
    tree = _leaf._require_keys(wrapper.payload, _COMPLETE_SAMPLE_KEYS)
    parsed = {
        name: _leaf._require_digest(tree[name])
        for name in _COMPLETE_SAMPLE_KEYS
    }
    expected = {
        "adapter_manifest_sha256": adapter_manifest_sha256,
        "coverage_ledger_sha256": coverage.phase_c_sha256,
        "evaluation_labels_sha256": evaluation_labels.phase_c_sha256,
        "fitted_state_sha256": fitted.phase_c_sha256,
        "native_observation_sha256": (
            configuration.native_observation_sha256
        ),
        "private_provenance_sha256": provenance.phase_c_sha256,
        "raw_reconstruction_sha256": raw_reconstruction_sha256,
        "semantic_reconstruction_sha256": semantic.phase_c_sha256,
        "source_inventory_sha256": inventory.phase_c_sha256,
        "static_context_sha256": static_context.phase_c_sha256,
    }
    if parsed != expected:
        _leaf._reject()
    return wrapper.payload_sha256


class _BundleMaterial(NamedTuple):
    bundle_sha256: str
    adapter_id: str
    adapter_version: str
    capability_plan_sha256: str
    descriptor_sha256: str
    actual_configuration_sha256: str
    actual_evidence_sha256: str
    actual_native_observation_sha256: str
    source_inventory_sha256: str
    coverage_ledger_sha256: str
    static_context_sha256: str
    evaluation_labels_sha256: str
    private_provenance_sha256: str
    fitted_state_sha256: str
    semantic_reconstruction_sha256: str
    adapter_manifest_sha256: str
    complete_sample_commitment_sha256: str
    raw_reconstruction_sha256: str


def _parse_and_validate_bundle(
    bundle_bytes: bytes,
    *,
    case: _CaseMaterial,
    allowed_exclusions: Tuple[str, ...],
    allowed_censors: Tuple[str, ...],
) -> _BundleMaterial:
    tree = _leaf._strict_json_bytes(
        bundle_bytes, maximum=MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES
    )
    _leaf._require_keys(tree, _BUNDLE_KEYS)
    if (
        tree["artifact_type"] != ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or _leaf._require_digest(tree["case_input_sha256"])
        != case.case_input_sha256
        or _leaf._require_digest(tree["source_sha256"])
        != case.source_sha256
        or _leaf._require_integer(
            tree["source_byte_count"], maximum=_leaf.MAXIMUM_SOURCE_BYTES
        )
        != len(case.source_bytes)
        or _leaf._require_digest(tree["split_manifest_sha256"])
        != case.split_manifest_sha256
    ):
        _leaf._reject()
    adapted = _leaf._require_keys(tree["adapted"], _ADAPTED_KEYS)
    wrappers = {
        name: _leaf._parse_wrapper(adapted[name], domain=domain)
        for name, domain in _WRAPPER_DOMAINS.items()
    }

    descriptor_wrapper = wrappers["adapter_descriptor"]
    descriptor = _leaf._parse_descriptor(descriptor_wrapper.payload_bytes)
    if descriptor_wrapper.payload_sha256 != descriptor.descriptor_sha256:
        _leaf._reject()

    configuration_wrapper = wrappers[
        "identity_bearing_native_configuration"
    ]
    configuration = _leaf._parse_configuration(
        configuration_wrapper.payload
    )
    if configuration_wrapper.payload_bytes != configuration.payload_bytes:
        _leaf._reject()

    budget = _leaf._RawBudget()
    inventory = _leaf._parse_source_inventory(
        wrappers["source_inventory"].payload, budget=budget
    )
    coverage = _leaf._parse_coverage(
        wrappers["coverage_ledger"].payload,
        allowed_exclusions=allowed_exclusions,
    )
    static_context = _leaf._parse_keyed_leaf(
        wrappers["static_context"].payload,
        budget=budget,
        phase_domain=_leaf.STATIC_CONTEXT_DIGEST_DOMAIN,
    )
    evaluation_labels = _leaf._parse_keyed_leaf(
        wrappers["evaluation_labels"].payload,
        budget=budget,
        phase_domain=_leaf.EVALUATION_LABELS_DIGEST_DOMAIN,
    )
    provenance = _leaf._parse_provenance(
        wrappers["private_provenance"].payload,
        budget=budget,
        allowed_censors=allowed_censors,
    )
    fitted = _leaf._parse_fitted_state(
        wrappers["fitted_state"].payload, budget=budget
    )
    semantic = _leaf._parse_semantic_reconstruction(
        wrappers["semantic_reconstruction"].payload, budget=budget
    )
    _leaf._validate_cross_leaf_relations(
        descriptor=descriptor,
        partition=case.partition,
        split_entries=case.split_entries,
        split_sha256=case.split_manifest_sha256,
        source_bytes=case.source_bytes,
        configuration=configuration,
        inventory=inventory,
        coverage=coverage,
        static_context=static_context,
        evaluation_labels=evaluation_labels,
        provenance=provenance,
        fitted=fitted,
        semantic=semantic,
    )

    detached_wrapper = wrappers["detached_native_observation"]
    if (
        detached_wrapper.payload != configuration.detached_payload
        or detached_wrapper.payload_bytes
        != configuration.detached_payload_bytes
        or detached_wrapper.payload_sha256
        != configuration.native_observation_sha256
    ):
        _leaf._reject()

    actual_evidence = _leaf._expected_evidence_tree(
        inventory=inventory,
        coverage=coverage,
        static_context=static_context,
        evaluation_labels=evaluation_labels,
        provenance=provenance,
        fitted=fitted,
        semantic=semantic,
        native_sha256=configuration.native_observation_sha256,
    )
    actual_evidence_bytes = _leaf._canonical_json_bytes(
        actual_evidence, maximum=_leaf.MAXIMUM_SINGLE_PAYLOAD_BYTES
    )
    actual_evidence_sha256 = _leaf._domain_sha256(
        _leaf.EXPECTED_EVIDENCE_DIGEST_DOMAIN, actual_evidence_bytes
    )

    manifest = _parse_manifest(
        wrappers["adapter_manifest"],
        case=case,
        descriptor=descriptor,
        configuration=configuration,
        inventory=inventory,
        coverage=coverage,
        static_context=static_context,
        evaluation_labels=evaluation_labels,
        provenance=provenance,
        fitted=fitted,
        semantic=semantic,
    )
    raw_sha256 = _parse_raw_reconstruction(
        adapted["raw_byte_reconstruction"],
        advertised=descriptor.raw_byte_reconstruction,
        source_bytes=case.source_bytes,
    )
    complete_sha256 = _parse_complete_sample(
        wrappers["complete_sample_commitment"],
        adapter_manifest_sha256=manifest.sample_root_sha256,
        raw_reconstruction_sha256=raw_sha256,
        configuration=configuration,
        inventory=inventory,
        coverage=coverage,
        static_context=static_context,
        evaluation_labels=evaluation_labels,
        provenance=provenance,
        fitted=fitted,
        semantic=semantic,
    )
    return _BundleMaterial(
        bundle_sha256=_leaf._domain_sha256(
            ADAPTED_EVIDENCE_BUNDLE_DIGEST_DOMAIN, bundle_bytes
        ),
        adapter_id=descriptor.adapter_id,
        adapter_version=descriptor.adapter_version,
        capability_plan_sha256=_capability_plan_sha256(descriptor),
        descriptor_sha256=descriptor.descriptor_sha256,
        actual_configuration_sha256=configuration_wrapper.payload_sha256,
        actual_evidence_sha256=actual_evidence_sha256,
        actual_native_observation_sha256=(
            configuration.native_observation_sha256
        ),
        source_inventory_sha256=inventory.phase_c_sha256,
        coverage_ledger_sha256=coverage.phase_c_sha256,
        static_context_sha256=static_context.phase_c_sha256,
        evaluation_labels_sha256=evaluation_labels.phase_c_sha256,
        private_provenance_sha256=provenance.phase_c_sha256,
        fitted_state_sha256=fitted.phase_c_sha256,
        semantic_reconstruction_sha256=semantic.phase_c_sha256,
        adapter_manifest_sha256=manifest.sample_root_sha256,
        complete_sample_commitment_sha256=complete_sha256,
        raw_reconstruction_sha256=raw_sha256,
    )


@dataclass(frozen=True)
class IndependentAdaptedEvidenceBundleVerificationReceiptV1:
    """Deterministic structural receipt; never execution or case authority."""

    verification_input_sha256: str
    case_input_byte_count: int
    case_input_sha256: str
    adapted_evidence_bundle_byte_count: int
    adapted_evidence_bundle_sha256: str
    allowed_exclusion_reason_codes_sha256: str
    allowed_censor_reason_codes_sha256: str
    adapter_id: str
    adapter_version: str
    capability_plan_sha256: str
    descriptor_sha256: str
    partition_sha256: str
    source_byte_count: int
    source_sha256: str
    split_manifest_sha256: str
    actual_configuration_sha256: str
    actual_evidence_sha256: str
    actual_native_observation_sha256: str
    source_inventory_sha256: str
    coverage_ledger_sha256: str
    static_context_sha256: str
    evaluation_labels_sha256: str
    private_provenance_sha256: str
    fitted_state_sha256: str
    semantic_reconstruction_sha256: str
    adapter_manifest_sha256: str
    complete_sample_commitment_sha256: str
    raw_reconstruction_sha256: str
    artifact_type: str = field(
        default=(
            ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE
        ),
        init=False,
    )
    format_version: str = field(default="1", init=False)
    verifier_id: str = field(
        default=ADAPTED_EVIDENCE_BUNDLE_VERIFIER_ID, init=False
    )
    implementation_status_id: str = field(
        default=ADAPTED_EVIDENCE_BUNDLE_VERIFIER_IMPLEMENTATION_STATUS,
        init=False,
    )
    status_id: str = field(
        default=ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_STATUS, init=False
    )
    decision_status: str = field(
        default=ADAPTED_EVIDENCE_BUNDLE_VERIFIER_DECISION_STATUS,
        init=False,
    )
    semantic_scope_id: str = field(
        default=ADAPTED_EVIDENCE_BUNDLE_SEMANTIC_SCOPE_ID, init=False
    )
    case_input_schema_independently_validated: bool = field(
        default=True, init=False
    )
    adapted_bundle_schema_independently_validated: bool = field(
        default=True, init=False
    )
    case_input_binding_independently_validated: bool = field(
        default=True, init=False
    )
    adapted_leaf_cross_relations_independently_validated: bool = field(
        default=True, init=False
    )
    adapted_leaf_commitments_independently_recomputed: bool = field(
        default=True, init=False
    )
    actual_evidence_commitment_independently_recomputed: bool = field(
        default=True, init=False
    )
    adapter_manifest_independently_recomputed: bool = field(
        default=True, init=False
    )
    complete_sample_commitment_independently_recomputed: bool = field(
        default=True, init=False
    )
    raw_reconstruction_policy_independently_validated: bool = field(
        default=True, init=False
    )
    adapted_bundle_leaf_set_structurally_complete: bool = field(
        default=True, init=False
    )
    decision_eligible: bool = field(default=False, init=False)
    execution_attested: bool = field(default=False, init=False)
    containment_attested: bool = field(default=False, init=False)
    custody_authenticated: bool = field(default=False, init=False)
    approved_profile_authenticated: bool = field(default=False, init=False)
    execution_input_set_membership_authenticated: bool = field(
        default=False, init=False
    )
    case_authority_authenticated: bool = field(default=False, init=False)
    adapter_source_authenticated: bool = field(default=False, init=False)
    adapter_source_loaded: bool = field(default=False, init=False)
    adapter_execution_observed: bool = field(default=False, init=False)
    output_blind_execution_enforced: bool = field(default=False, init=False)
    actual_output_freshness_attested: bool = field(
        default=False, init=False
    )
    actual_output_adapter_authorship_attested: bool = field(
        default=False, init=False
    )
    semantic_truth_attested: bool = field(default=False, init=False)
    format_specific_payload_semantics_attested: bool = field(
        default=False, init=False
    )
    source_policy_semantics_independently_evaluated: bool = field(
        default=False, init=False
    )
    expected_evidence_compared: bool = field(default=False, init=False)
    adapted_evidence_leaf_complete: bool = field(
        default=False, init=False
    )
    publication_artifacts_rebuilt: bool = field(default=False, init=False)
    generalization_claim_validated: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (
            type(self)
            is not IndependentAdaptedEvidenceBundleVerificationReceiptV1
        ):
            raise TypeError("adapted-evidence receipt must be exact")
        _validate_receipt_fields(self)


_RECEIPT_DIGEST_FIELDS = (
    "verification_input_sha256",
    "case_input_sha256",
    "adapted_evidence_bundle_sha256",
    "allowed_exclusion_reason_codes_sha256",
    "allowed_censor_reason_codes_sha256",
    "capability_plan_sha256",
    "descriptor_sha256",
    "partition_sha256",
    "source_sha256",
    "split_manifest_sha256",
    "actual_configuration_sha256",
    "actual_evidence_sha256",
    "actual_native_observation_sha256",
    "source_inventory_sha256",
    "coverage_ledger_sha256",
    "static_context_sha256",
    "evaluation_labels_sha256",
    "private_provenance_sha256",
    "fitted_state_sha256",
    "semantic_reconstruction_sha256",
    "adapter_manifest_sha256",
    "complete_sample_commitment_sha256",
    "raw_reconstruction_sha256",
)
_RECEIPT_TRUE_FIELDS = (
    "case_input_schema_independently_validated",
    "adapted_bundle_schema_independently_validated",
    "case_input_binding_independently_validated",
    "adapted_leaf_cross_relations_independently_validated",
    "adapted_leaf_commitments_independently_recomputed",
    "actual_evidence_commitment_independently_recomputed",
    "adapter_manifest_independently_recomputed",
    "complete_sample_commitment_independently_recomputed",
    "raw_reconstruction_policy_independently_validated",
    "adapted_bundle_leaf_set_structurally_complete",
)
_RECEIPT_FALSE_FIELDS = (
    "decision_eligible",
    "execution_attested",
    "containment_attested",
    "custody_authenticated",
    "approved_profile_authenticated",
    "execution_input_set_membership_authenticated",
    "case_authority_authenticated",
    "adapter_source_authenticated",
    "adapter_source_loaded",
    "adapter_execution_observed",
    "output_blind_execution_enforced",
    "actual_output_freshness_attested",
    "actual_output_adapter_authorship_attested",
    "semantic_truth_attested",
    "format_specific_payload_semantics_attested",
    "source_policy_semantics_independently_evaluated",
    "expected_evidence_compared",
    "adapted_evidence_leaf_complete",
    "publication_artifacts_rebuilt",
    "generalization_claim_validated",
)


def _validate_receipt_fields(
    value: IndependentAdaptedEvidenceBundleVerificationReceiptV1,
) -> None:
    try:
        for name in _RECEIPT_DIGEST_FIELDS:
            _leaf._require_digest(getattr(value, name))
        _leaf._require_integer(
            value.case_input_byte_count,
            maximum=MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES,
            minimum=1,
        )
        _leaf._require_integer(
            value.adapted_evidence_bundle_byte_count,
            maximum=MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES,
            minimum=1,
        )
        _leaf._require_integer(
            value.source_byte_count,
            maximum=_leaf.MAXIMUM_SOURCE_BYTES,
            minimum=1,
        )
        _leaf._require_public_id(value.adapter_id)
        if (
            type(value.adapter_version) is not str
            or _leaf._VERSION_RE.fullmatch(value.adapter_version) is None
        ):
            _leaf._reject()
        fixed = {
            "artifact_type": (
                ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE
            ),
            "format_version": "1",
            "verifier_id": ADAPTED_EVIDENCE_BUNDLE_VERIFIER_ID,
            "implementation_status_id": (
                ADAPTED_EVIDENCE_BUNDLE_VERIFIER_IMPLEMENTATION_STATUS
            ),
            "status_id": ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_STATUS,
            "decision_status": (
                ADAPTED_EVIDENCE_BUNDLE_VERIFIER_DECISION_STATUS
            ),
            "semantic_scope_id": ADAPTED_EVIDENCE_BUNDLE_SEMANTIC_SCOPE_ID,
        }
        if any(
            type(getattr(value, name)) is not type(expected)
            or getattr(value, name) != expected
            for name, expected in fixed.items()
        ):
            _leaf._reject()
        if any(
            getattr(value, name) is not True
            for name in _RECEIPT_TRUE_FIELDS
        ):
            _leaf._reject()
        if any(
            getattr(value, name) is not False
            for name in _RECEIPT_FALSE_FIELDS
        ):
            _leaf._reject()
    except _leaf._Rejected as error:
        raise ValueError(
            "adapted-evidence verification receipt fields are invalid"
        ) from error


def _receipt_tree(
    value: IndependentAdaptedEvidenceBundleVerificationReceiptV1,
) -> dict:
    if (
        type(value)
        is not IndependentAdaptedEvidenceBundleVerificationReceiptV1
    ):
        raise TypeError("adapted-evidence receipt must be exact")
    IndependentAdaptedEvidenceBundleVerificationReceiptV1.__post_init__(value)
    return {item.name: getattr(value, item.name) for item in fields(value)}


def independent_adapted_evidence_bundle_verification_receipt_bytes(
    value: IndependentAdaptedEvidenceBundleVerificationReceiptV1,
) -> bytes:
    """Return canonical ASCII JSON for the structural nondecision receipt."""

    try:
        return _leaf._canonical_json_bytes(
            _receipt_tree(value),
            maximum=MAXIMUM_ADAPTED_EVIDENCE_VERIFICATION_RECEIPT_BYTES,
        )
    except (
        AttributeError,
        TypeError,
        ValueError,
        _leaf._Rejected,
        RecursionError,
    ):
        _fail(AdaptedEvidenceBundleVerificationCode.CANONICALIZATION_FAILED)


def independent_adapted_evidence_bundle_verification_receipt_sha256(
    value: IndependentAdaptedEvidenceBundleVerificationReceiptV1,
) -> str:
    """Return the domain-separated structural receipt commitment."""

    payload = independent_adapted_evidence_bundle_verification_receipt_bytes(
        value
    )
    try:
        return _leaf._domain_sha256(
            ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_RECEIPT_DIGEST_DOMAIN,
            payload,
        )
    except _leaf._Rejected:
        _fail(AdaptedEvidenceBundleVerificationCode.CANONICALIZATION_FAILED)


def validate_independent_adapted_evidence_bundle_verification_receipt(
    value: object,
) -> IndependentAdaptedEvidenceBundleVerificationReceiptV1:
    """Return a fresh receipt snapshot without upgrading its authority."""

    if (
        type(value)
        is not IndependentAdaptedEvidenceBundleVerificationReceiptV1
    ):
        _fail(AdaptedEvidenceBundleVerificationCode.RECEIPT_INVALID)
    try:
        IndependentAdaptedEvidenceBundleVerificationReceiptV1.__post_init__(
            value
        )
        return IndependentAdaptedEvidenceBundleVerificationReceiptV1(
            **{
                item.name: getattr(value, item.name)
                for item in fields(value)
                if item.init
            }
        )
    except AdaptedEvidenceBundleVerificationError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(AdaptedEvidenceBundleVerificationCode.RECEIPT_INVALID)


@dataclass(frozen=True)
class IndependentAdaptedEvidenceBundleVerificationResultV1:
    """Constructible transport; validation against raw bytes remains required."""

    receipt: IndependentAdaptedEvidenceBundleVerificationReceiptV1
    receipt_bytes: bytes
    receipt_sha256: str

    def __post_init__(self) -> None:
        if (
            type(self)
            is not IndependentAdaptedEvidenceBundleVerificationResultV1
        ):
            raise TypeError("adapted-evidence result must be exact")
        _validate_result_transport(self)


def _validate_result_transport(
    value: IndependentAdaptedEvidenceBundleVerificationResultV1,
) -> None:
    receipt = (
        validate_independent_adapted_evidence_bundle_verification_receipt(
            value.receipt
        )
    )
    if (
        type(value.receipt_bytes) is not bytes
        or not value.receipt_bytes
        or len(value.receipt_bytes)
        > MAXIMUM_ADAPTED_EVIDENCE_VERIFICATION_RECEIPT_BYTES
        or type(value.receipt_sha256) is not str
    ):
        raise ValueError("adapted-evidence result transport is outside its bound")
    try:
        _leaf._require_digest(value.receipt_sha256)
    except _leaf._Rejected as error:
        raise ValueError("adapted-evidence result digest is invalid") from error
    if (
        independent_adapted_evidence_bundle_verification_receipt_bytes(receipt)
        != value.receipt_bytes
        or independent_adapted_evidence_bundle_verification_receipt_sha256(
            receipt
        )
        != value.receipt_sha256
    ):
        raise ValueError("adapted-evidence result transport differs")


def _verification_input_sha256(
    value: IndependentAdaptedEvidenceBundleVerificationInputV1,
) -> str:
    return _leaf._named_sequence_sha256(
        ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_INPUT_DIGEST_DOMAIN,
        (
            b"case_input_bytes",
            b"adapted_evidence_bundle_bytes",
            b"allowed_exclusion_reason_codes",
            b"allowed_censor_reason_codes",
        ),
        (
            value.case_input_bytes,
            value.adapted_evidence_bundle_bytes,
            _reason_registry_bytes(value.allowed_exclusion_reason_codes),
            _reason_registry_bytes(value.allowed_censor_reason_codes),
        ),
    )


def _build_verified_result(
    value: IndependentAdaptedEvidenceBundleVerificationInputV1,
) -> IndependentAdaptedEvidenceBundleVerificationResultV1:
    try:
        case = _parse_case_input(value.case_input_bytes)
    except _leaf._Rejected:
        _fail(AdaptedEvidenceBundleVerificationCode.CASE_INPUT_INVALID)
    try:
        _leaf._strict_json_bytes(
            value.adapted_evidence_bundle_bytes,
            maximum=MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES,
        )
    except _leaf._Rejected:
        _fail(AdaptedEvidenceBundleVerificationCode.JSON_INVALID)
    try:
        bundle = _parse_and_validate_bundle(
            value.adapted_evidence_bundle_bytes,
            case=case,
            allowed_exclusions=value.allowed_exclusion_reason_codes,
            allowed_censors=value.allowed_censor_reason_codes,
        )
    except _leaf._Rejected:
        _fail(AdaptedEvidenceBundleVerificationCode.BINDING_MISMATCH)
    try:
        receipt = IndependentAdaptedEvidenceBundleVerificationReceiptV1(
            verification_input_sha256=_verification_input_sha256(value),
            case_input_byte_count=len(value.case_input_bytes),
            case_input_sha256=case.case_input_sha256,
            adapted_evidence_bundle_byte_count=len(
                value.adapted_evidence_bundle_bytes
            ),
            adapted_evidence_bundle_sha256=bundle.bundle_sha256,
            allowed_exclusion_reason_codes_sha256=_reason_registry_sha256(
                value.allowed_exclusion_reason_codes
            ),
            allowed_censor_reason_codes_sha256=_reason_registry_sha256(
                value.allowed_censor_reason_codes
            ),
            adapter_id=bundle.adapter_id,
            adapter_version=bundle.adapter_version,
            capability_plan_sha256=bundle.capability_plan_sha256,
            descriptor_sha256=bundle.descriptor_sha256,
            partition_sha256=case.partition_sha256,
            source_byte_count=len(case.source_bytes),
            source_sha256=case.source_sha256,
            split_manifest_sha256=case.split_manifest_sha256,
            actual_configuration_sha256=(
                bundle.actual_configuration_sha256
            ),
            actual_evidence_sha256=bundle.actual_evidence_sha256,
            actual_native_observation_sha256=(
                bundle.actual_native_observation_sha256
            ),
            source_inventory_sha256=bundle.source_inventory_sha256,
            coverage_ledger_sha256=bundle.coverage_ledger_sha256,
            static_context_sha256=bundle.static_context_sha256,
            evaluation_labels_sha256=bundle.evaluation_labels_sha256,
            private_provenance_sha256=bundle.private_provenance_sha256,
            fitted_state_sha256=bundle.fitted_state_sha256,
            semantic_reconstruction_sha256=(
                bundle.semantic_reconstruction_sha256
            ),
            adapter_manifest_sha256=bundle.adapter_manifest_sha256,
            complete_sample_commitment_sha256=(
                bundle.complete_sample_commitment_sha256
            ),
            raw_reconstruction_sha256=bundle.raw_reconstruction_sha256,
        )
        receipt_bytes = (
            independent_adapted_evidence_bundle_verification_receipt_bytes(
                receipt
            )
        )
        return IndependentAdaptedEvidenceBundleVerificationResultV1(
            receipt=receipt,
            receipt_bytes=receipt_bytes,
            receipt_sha256=(
                independent_adapted_evidence_bundle_verification_receipt_sha256(
                    receipt
                )
            ),
        )
    except AdaptedEvidenceBundleVerificationError:
        raise
    except (_leaf._Rejected, AttributeError, TypeError, ValueError):
        _fail(AdaptedEvidenceBundleVerificationCode.INTERNAL_ERROR)


def verify_independent_adapted_evidence_bundle(
    value: IndependentAdaptedEvidenceBundleVerificationInputV1,
) -> IndependentAdaptedEvidenceBundleVerificationResultV1:
    """Independently validate an adapted bundle against its case input."""

    raw_input = _snapshot_input(value)
    try:
        return _build_verified_result(raw_input)
    except AdaptedEvidenceBundleVerificationError:
        raise
    except Exception:
        _fail(AdaptedEvidenceBundleVerificationCode.INTERNAL_ERROR)


def validate_independent_adapted_evidence_bundle_verification_result(
    value: IndependentAdaptedEvidenceBundleVerificationResultV1,
    raw_input: IndependentAdaptedEvidenceBundleVerificationInputV1,
) -> IndependentAdaptedEvidenceBundleVerificationResultV1:
    """Rerun raw verification and require exact result identity."""

    if (
        type(value)
        is not IndependentAdaptedEvidenceBundleVerificationResultV1
    ):
        _fail(AdaptedEvidenceBundleVerificationCode.RECEIPT_INVALID)
    try:
        _validate_result_transport(value)
    except AdaptedEvidenceBundleVerificationError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(AdaptedEvidenceBundleVerificationCode.RECEIPT_INVALID)
    expected = verify_independent_adapted_evidence_bundle(raw_input)
    if value != expected:
        _fail(AdaptedEvidenceBundleVerificationCode.RECEIPT_INVALID)
    return expected


__all__ = [
    "ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE",
    "ADAPTED_EVIDENCE_BUNDLE_DIGEST_DOMAIN",
    "ADAPTED_EVIDENCE_BUNDLE_SEMANTIC_SCOPE_ID",
    "ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_INPUT_DIGEST_DOMAIN",
    "ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE",
    "ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_RECEIPT_DIGEST_DOMAIN",
    "ADAPTED_EVIDENCE_BUNDLE_VERIFICATION_STATUS",
    "ADAPTED_EVIDENCE_BUNDLE_VERIFIER_DECISION_STATUS",
    "ADAPTED_EVIDENCE_BUNDLE_VERIFIER_ID",
    "ADAPTED_EVIDENCE_BUNDLE_VERIFIER_IMPLEMENTATION_STATUS",
    "CAPABILITY_CONFORMANCE_PLAN_DIGEST_DOMAIN",
    "AdaptedEvidenceBundleVerificationCode",
    "AdaptedEvidenceBundleVerificationError",
    "IndependentAdaptedEvidenceBundleVerificationError",
    "IndependentAdaptedEvidenceBundleVerificationInputV1",
    "IndependentAdaptedEvidenceBundleVerificationReceiptV1",
    "IndependentAdaptedEvidenceBundleVerificationResultV1",
    "MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES",
    "MAXIMUM_ADAPTED_EVIDENCE_VERIFICATION_INPUT_BYTES",
    "MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES",
    "OUTPUT_BLIND_CASE_INPUT_ARTIFACT_TYPE",
    "OUTPUT_BLIND_CASE_INPUT_DIGEST_DOMAIN",
    "independent_adapted_evidence_bundle_verification_receipt_bytes",
    "independent_adapted_evidence_bundle_verification_receipt_sha256",
    "validate_independent_adapted_evidence_bundle_verification_receipt",
    "validate_independent_adapted_evidence_bundle_verification_result",
    "verify_independent_adapted_evidence_bundle",
]
