"""Producer-side construction of one leaf-complete expected-evidence bundle.

This module deliberately reuses the publisher's typed payload projections.  It
is therefore a deterministic producer, not an independent verifier, custody
authority, execution attestation, or gate-decision surface.  A consumer that
uses these bytes for verification must independently implement every schema,
resource bound, cross-leaf binding, and digest computation.

The bundle is private: it carries source-derived inventory, context, label,
provenance, fitted-state, reconstruction, and native-configuration preimages.
It must never be substituted for a public publication artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Tuple

from heterodiff.events import EventConfiguration

from . import adapter_contract as _contract
from . import adapter_evidence as _evidence
from . import adapter_publication_payloads as _payloads


EXPECTED_EVIDENCE_LEAF_BUNDLE_ARTIFACT_TYPE = (
    "heterodiff.adapter.expected-evidence-leaf-bundle.v1"
)
EXPECTED_EVIDENCE_LEAF_BUNDLE_DIGEST_DOMAIN = (
    EXPECTED_EVIDENCE_LEAF_BUNDLE_ARTIFACT_TYPE
)
MAXIMUM_EXPECTED_EVIDENCE_LEAF_BUNDLE_BYTES = 32 * 1024 * 1024
MAXIMUM_EXPECTED_EVIDENCE_REPRESENTATION_IDS = 64


class ExpectedEvidenceLeafBundleError(ValueError):
    """A typed expected bundle has inconsistent external or cross-leaf bindings."""


@dataclass(frozen=True)
class ExpectedEvidenceLeafBundleResultV1:
    """Constructible byte transport with exact count and digest consistency.

    Construction alone does not validate the bundle's JSON schema or evidence
    relations.  The producer below creates canonical bundles, while the
    separate independent verifier revalidates arbitrary transported bytes.
    """

    bundle_bytes: bytes
    bundle_byte_count: int
    bundle_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not ExpectedEvidenceLeafBundleResultV1:
            raise TypeError("expected-evidence leaf bundle result must be exact")
        if type(self.bundle_bytes) is not bytes or not self.bundle_bytes:
            raise TypeError("bundle_bytes must be nonempty exact bytes")
        if type(self.bundle_byte_count) is not int:
            raise TypeError("bundle_byte_count must be an exact integer")
        if (
            self.bundle_byte_count != len(self.bundle_bytes)
            or self.bundle_byte_count
            > MAXIMUM_EXPECTED_EVIDENCE_LEAF_BUNDLE_BYTES
        ):
            raise ValueError("bundle_byte_count does not match bounded bytes")
        if type(self.bundle_sha256) is not str:
            raise TypeError("bundle_sha256 must be exact text")
        if self.bundle_sha256 != expected_evidence_leaf_bundle_sha256(
            self.bundle_bytes
        ):
            raise ValueError("bundle_sha256 does not match exact bundle bytes")


def _fail(message: str) -> None:
    raise ExpectedEvidenceLeafBundleError(message) from None


def _domain_separated_sha256(domain: str, payload: bytes) -> str:
    if type(domain) is not str or type(payload) is not bytes:
        raise TypeError("bundle digest inputs must have exact types")
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except UnicodeError:
        raise TypeError("bundle digest domain must be ASCII") from None
    if (
        not domain_bytes
        or len(domain_bytes) > 256
        or b"\x00" in domain_bytes
    ):
        raise ValueError("bundle digest domain is outside its bound")
    if len(payload) > MAXIMUM_EXPECTED_EVIDENCE_LEAF_BUNDLE_BYTES:
        raise ValueError("expected-evidence leaf bundle exceeds its byte ceiling")
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def expected_evidence_leaf_bundle_sha256(bundle_bytes: bytes) -> str:
    """Return the bundle-domain digest of exact bounded bytes."""

    if type(bundle_bytes) is not bytes:
        raise TypeError("bundle_bytes must be exact immutable bytes")
    if (
        not bundle_bytes
        or len(bundle_bytes) > MAXIMUM_EXPECTED_EVIDENCE_LEAF_BUNDLE_BYTES
    ):
        raise ValueError("bundle_bytes are outside the expected bundle bound")
    return _domain_separated_sha256(
        EXPECTED_EVIDENCE_LEAF_BUNDLE_DIGEST_DOMAIN,
        bundle_bytes,
    )


def _validated_reason_registries(
    allowed_exclusion_reason_codes: Tuple[str, ...],
    allowed_censor_reason_codes: Tuple[str, ...],
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    exclusions = _evidence._validate_reason_codes(
        allowed_exclusion_reason_codes,
        name="allowed exclusion reason",
    )
    censors = _evidence._validate_reason_codes(
        allowed_censor_reason_codes,
        name="allowed censor reason",
    )
    if len(exclusions) + len(censors) > _evidence.MAXIMUM_REASON_CODES:
        _fail("combined reason registry exceeds its resource ceiling")
    return exclusions, censors


def _validate_capability_and_fitted_bindings(
    descriptor: _contract.AdapterDescriptor,
    split_manifest: _contract.SplitManifest,
    configuration: EventConfiguration,
    expected: _evidence.ExpectedAdapterEvidence,
    *,
    descriptor_sha256: str,
    split_manifest_sha256: str,
    schema_sha256: str,
) -> None:
    capabilities = descriptor.capabilities
    if (
        len(capabilities.supported_representation_ids)
        > MAXIMUM_EXPECTED_EVIDENCE_REPRESENTATION_IDS
    ):
        _fail("descriptor representation set exceeds its resource ceiling")
    if (
        capabilities.time_measure is not configuration.schema.time_measure
        or capabilities.multiplicity_mode
        is not configuration.schema.multiplicity_mode
    ):
        _fail("descriptor measure capabilities disagree with expected schema")
    if capabilities.static_context is not bool(expected.static_context.entries):
        _fail("static-context capability disagrees with expected evidence")
    if capabilities.evaluation_labels is not bool(
        expected.evaluation_labels.entries
    ):
        _fail("evaluation-label capability disagrees with expected evidence")
    provenance_present = bool(expected.provenance.entries)
    if capabilities.private_provenance is not provenance_present:
        _fail("private-provenance capability disagrees with expected evidence")
    if configuration.events and not provenance_present:
        _fail("native occurrences require expected private provenance")

    state = expected.fitted_state
    if capabilities.fitted_state is not (state is not None):
        _fail("fitted-state capability disagrees with expected evidence")
    if state is None:
        return
    identity = descriptor.identity
    if (
        state.descriptor_sha256 != descriptor_sha256
        or state.adapter_id != identity.adapter_id
        or state.adapter_version != identity.adapter_version
        or state.contract_version != identity.contract_version
        or state.policy_sha256 != identity.policy_sha256
        or state.schema_sha256 != schema_sha256
        or state.split_manifest_sha256 != split_manifest_sha256
        or state.training_group_set_sha256
        != _evidence.training_group_set_digest(split_manifest)
    ):
        _fail("fitted state is not bound to the descriptor, schema, or split")


def _wrapped_expected_payloads(
    configuration: EventConfiguration,
    expected: _evidence.ExpectedAdapterEvidence,
) -> dict:
    values = {
        "coverage_ledger": _payloads.coverage_ledger_payload(
            expected.coverage
        ),
        "detached_native_observation": (
            _payloads.detached_native_observation_payload(configuration)
        ),
        "evaluation_labels": _payloads.evaluation_labels_payload(
            expected.evaluation_labels
        ),
        "expected_evidence_commitment": (
            _payloads.expected_evidence_payload(expected)
        ),
        "fitted_state": _payloads.fitted_state_payload(expected.fitted_state),
        "identity_bearing_native_configuration": (
            _payloads.identity_bearing_native_configuration_payload(
                configuration
            )
        ),
        "private_provenance": _payloads.private_provenance_payload(
            expected.provenance
        ),
        "semantic_reconstruction": (
            _payloads.semantic_reconstruction_payload(
                expected.reconstruction
            )
        ),
        "source_inventory": _payloads.source_inventory_payload(
            expected.inventory
        ),
        "static_context": _payloads.static_context_payload(
            expected.static_context
        ),
    }
    domains = {
        "coverage_ledger": _payloads.PRIVATE_COVERAGE_LEDGER_DIGEST_DOMAIN,
        "detached_native_observation": (
            _contract.NATIVE_OBSERVATION_DIGEST_DOMAIN
        ),
        "evaluation_labels": (
            _payloads.PRIVATE_EVALUATION_LABELS_DIGEST_DOMAIN
        ),
        "expected_evidence_commitment": (
            _evidence.EXPECTED_EVIDENCE_DIGEST_DOMAIN
        ),
        "fitted_state": _payloads.PRIVATE_FITTED_STATE_DIGEST_DOMAIN,
        "identity_bearing_native_configuration": (
            _payloads.PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN
        ),
        "private_provenance": (
            _payloads.PRIVATE_PROVENANCE_PAYLOAD_DIGEST_DOMAIN
        ),
        "semantic_reconstruction": (
            _payloads.PRIVATE_SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN
        ),
        "source_inventory": (
            _payloads.PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN
        ),
        "static_context": _payloads.PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN,
    }
    return {
        name: _payloads.canonical_payload_wrapper(
            values[name],
            expected_domain=domains[name],
        )
        for name in (
            "coverage_ledger",
            "detached_native_observation",
            "evaluation_labels",
            "expected_evidence_commitment",
            "fitted_state",
            "identity_bearing_native_configuration",
            "private_provenance",
            "semantic_reconstruction",
            "source_inventory",
            "static_context",
        )
    }


def build_expected_evidence_leaf_bundle(
    descriptor: _contract.AdapterDescriptor,
    source_bytes: bytes,
    split_manifest: _contract.SplitManifest,
    expected_configuration: EventConfiguration,
    expected_evidence: _evidence.ExpectedAdapterEvidence,
    *,
    allowed_exclusion_reason_codes: Tuple[str, ...],
    allowed_censor_reason_codes: Tuple[str, ...],
) -> ExpectedEvidenceLeafBundleResultV1:
    """Build one canonical private bundle from exact typed expected evidence."""

    if type(descriptor) is not _contract.AdapterDescriptor:
        raise TypeError("descriptor must be an exact AdapterDescriptor")
    if type(source_bytes) is not bytes:
        raise TypeError("source_bytes must be exact immutable bytes")
    if type(split_manifest) is not _contract.SplitManifest:
        raise TypeError("split_manifest must be an exact SplitManifest")
    if type(expected_configuration) is not EventConfiguration:
        raise TypeError(
            "expected_configuration must be an exact EventConfiguration"
        )
    if type(expected_evidence) is not _evidence.ExpectedAdapterEvidence:
        raise TypeError(
            "expected_evidence must be an exact ExpectedAdapterEvidence"
        )
    if not source_bytes or len(source_bytes) > _evidence.MAXIMUM_SOURCE_BYTES:
        _fail("source bytes are outside the expected bundle resource bound")

    descriptor_snapshot = _contract._snapshot_descriptor(descriptor)
    split_snapshot = _evidence.snapshot_bounded_split_manifest(split_manifest)
    configuration_snapshot = (
        _evidence.snapshot_bounded_native_configuration(
            expected_configuration
        )
    )
    expected_snapshot = _evidence._snapshot_expected_evidence(
        expected_evidence
    )
    exclusions, censors = _validated_reason_registries(
        allowed_exclusion_reason_codes,
        allowed_censor_reason_codes,
    )

    try:
        partition = split_snapshot.partition_for(
            configuration_snapshot.sample_id
        )
    except Exception:
        _fail("expected configuration is absent from the split manifest")
    if (
        configuration_snapshot.sample_id != partition.sample_id
        or configuration_snapshot.group_id != partition.group_id
    ):
        _fail("expected configuration identifiers disagree with the split")

    descriptor_payload = _payloads.adapter_descriptor_payload(
        descriptor_snapshot
    )
    split_payload = _payloads.split_manifest_payload(split_snapshot)
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    native_sha256 = _contract.native_observation_digest(
        configuration_snapshot
    )
    schema_sha256 = _contract.feature_schema_digest(
        configuration_snapshot.schema
    )
    if expected_snapshot.native_observation_sha256 != native_sha256:
        _fail("expected native-observation binding does not match configuration")

    try:
        _evidence._validate_leaf_source_bindings(
            expected_snapshot,  # type: ignore[arg-type]
            source_sha256=source_sha256,
            source_size_bytes=len(source_bytes),
            policy_sha256=descriptor_snapshot.identity.policy_sha256,
            schema_sha256=schema_sha256,
            native_sha256=native_sha256,
        )
        _evidence._validate_coverage_and_provenance(
            expected_snapshot,  # type: ignore[arg-type]
            _contract.rebuild_detached_native_configuration(
                configuration_snapshot
            ),
            allowed_exclusion_reason_codes=exclusions,
            allowed_censor_reason_codes=censors,
        )
    except _evidence.AdapterConformanceError:
        _fail("expected evidence has inconsistent cross-leaf bindings")

    _validate_capability_and_fitted_bindings(
        descriptor_snapshot,
        split_snapshot,
        configuration_snapshot,
        expected_snapshot,
        descriptor_sha256=descriptor_payload.payload_sha256,
        split_manifest_sha256=split_payload.payload_sha256,
        schema_sha256=schema_sha256,
    )

    tree = {
        "allowed_censor_reason_codes": list(censors),
        "allowed_exclusion_reason_codes": list(exclusions),
        "artifact_type": EXPECTED_EVIDENCE_LEAF_BUNDLE_ARTIFACT_TYPE,
        "descriptor_sha256": descriptor_payload.payload_sha256,
        "expected": _wrapped_expected_payloads(
            configuration_snapshot,
            expected_snapshot,
        ),
        "format_version": "1",
        "source_byte_count": len(source_bytes),
        "source_sha256": source_sha256,
        "split_manifest_sha256": split_payload.payload_sha256,
    }
    try:
        bundle_bytes = _payloads._canonical_tree_bytes(
            tree,
            maximum_encoded_bytes=(
                MAXIMUM_EXPECTED_EVIDENCE_LEAF_BUNDLE_BYTES
            ),
        )
    except _payloads.PublicationPayloadError:
        _fail("expected-evidence leaf bundle exceeds its canonical resource bound")
    bundle_sha256 = expected_evidence_leaf_bundle_sha256(bundle_bytes)
    return ExpectedEvidenceLeafBundleResultV1(
        bundle_bytes=bundle_bytes,
        bundle_byte_count=len(bundle_bytes),
        bundle_sha256=bundle_sha256,
    )


__all__ = [
    "EXPECTED_EVIDENCE_LEAF_BUNDLE_ARTIFACT_TYPE",
    "EXPECTED_EVIDENCE_LEAF_BUNDLE_DIGEST_DOMAIN",
    "ExpectedEvidenceLeafBundleError",
    "ExpectedEvidenceLeafBundleResultV1",
    "MAXIMUM_EXPECTED_EVIDENCE_LEAF_BUNDLE_BYTES",
    "MAXIMUM_EXPECTED_EVIDENCE_REPRESENTATION_IDS",
    "build_expected_evidence_leaf_bundle",
    "expected_evidence_leaf_bundle_sha256",
]
