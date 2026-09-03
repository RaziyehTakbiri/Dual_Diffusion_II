"""Write-free source-bound freezing for Phase-D adapter publication.

This module is the only publication surface allowed to invoke an untrusted
adapter.  It snapshots all caller-owned typed inputs first, runs the complete
detached conformance path afresh, compares that result with the supplied run,
checks the category-separated public vocabulary, and then drops the adapter.

The result is still development-only and must be re-snapshotted by the later
serializer to detect mutation through Python implementation escape hatches.
No function here serializes, writes, publishes, verifies an artifact, or makes
a gate decision.
"""

from __future__ import annotations

from enum import Enum
import hashlib
from types import MappingProxyType
from typing import NamedTuple, Tuple

from heterodiff.events import EventConfiguration

from . import adapter_contract as _contract
from . import adapter_evidence as _evidence
from . import adapter_publication_payloads as _payloads
from .adapter_conformance_execution_guard import (
    SourceBindingFormat,
    publication_source_binding_bytes,
    validate_execution_receipt,
)
from .adapter_conformance_runner import (
    ConformanceRun,
    run_complete_adapter_conformance,
)
from .adapter_evidence import AdapterEvidenceResourceError
from .adapter_publication_types import (
    ExecutionGuardRunManifestV1,
    HostileControlInputV1,
    MAXIMUM_HOSTILE_CONTROL_RECEIPTS,
    MAXIMUM_PRIVATE_ARTIFACT_BYTES,
    MAXIMUM_PUBLICATION_CASES,
    MAXIMUM_REGISTRY_VALUES_PER_CATEGORY,
    PublicAdapterIdentityV1,
    PublicIdentifierRegistryV1,
    PublicationBindingInputV1,
    PublicationExecutionGuardInputV1,
    PublicationRequestV1,
    VerifiedDetachedCaseInputV1,
)


class PublicationFreezeCode(str, Enum):
    """Closed failures emitted before any publication bytes exist."""

    PUB_INPUT_TYPE = "PUB_INPUT_TYPE"
    PUB_INPUT_RESOURCE = "PUB_INPUT_RESOURCE"
    PUB_ID_NOT_ALLOWLISTED = "PUB_ID_NOT_ALLOWLISTED"
    PUB_RUN_ORIGIN_INVALID = "PUB_RUN_ORIGIN_INVALID"
    PUB_RECOMPUTATION_MISMATCH = "PUB_RECOMPUTATION_MISMATCH"
    PUB_POSTMUTATION = "PUB_POSTMUTATION"


_ERROR_MESSAGES = MappingProxyType(
    {
        PublicationFreezeCode.PUB_INPUT_TYPE: (
            "publication freeze input is invalid"
        ),
        PublicationFreezeCode.PUB_INPUT_RESOURCE: (
            "publication freeze input exceeds a resource ceiling"
        ),
        PublicationFreezeCode.PUB_ID_NOT_ALLOWLISTED: (
            "publication value is not in its public-ID category"
        ),
        PublicationFreezeCode.PUB_RUN_ORIGIN_INVALID: (
            "detached conformance run origin is invalid"
        ),
        PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH: (
            "publication recomputation does not match supplied evidence"
        ),
        PublicationFreezeCode.PUB_POSTMUTATION: (
            "publication input changed during freezing"
        ),
    }
)


class PublicationFreezeError(ValueError):
    """One fixed coded, interpolation-free freeze failure."""

    def __init__(self, code: PublicationFreezeCode) -> None:
        if type(code) is not PublicationFreezeCode:
            raise TypeError("publication freeze code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: PublicationFreezeCode) -> None:
    raise PublicationFreezeError(code) from None


class FrozenDetachedCaseV1(NamedTuple):
    """Fresh snapshots retained only after the adapter has been dropped."""

    source_bytes: bytes
    descriptor: _contract.AdapterDescriptor
    split_manifest: _contract.SplitManifest
    complete_sample: _evidence.CompleteAdaptedEventSample
    expected_evidence: _evidence.ExpectedAdapterEvidence
    expected_configuration: EventConfiguration
    conformance_run: ConformanceRun
    independent_golden_definition_bytes: bytes


class FrozenPublicationInputV1(NamedTuple):
    """Canonical case/control order and fresh write-free input snapshots."""

    bindings: PublicationBindingInputV1
    public_ids: PublicIdentifierRegistryV1
    cases: Tuple[FrozenDetachedCaseV1, ...]
    hostile_controls: Tuple[HostileControlInputV1, ...]
    execution_guard: PublicationExecutionGuardInputV1


class _CaseSnapshot(NamedTuple):
    adapter: object
    source_bytes: bytes
    descriptor: _contract.AdapterDescriptor
    split_manifest: _contract.SplitManifest
    complete_sample: _evidence.CompleteAdaptedEventSample
    expected_evidence: _evidence.ExpectedAdapterEvidence
    expected_configuration: EventConfiguration
    conformance_run: ConformanceRun
    independent_golden_definition_bytes: bytes


_CAPABILITY_FIELDS = (
    "semantic_reconstruction",
    "raw_byte_reconstruction",
    "fitted_state",
    "static_context",
    "evaluation_labels",
    "private_provenance",
)
_TEST_INVENTORY_DIGEST_DOMAIN = b"heterodiff.adapter.test-inventory.v1"
_PUBLICATION_PROFILE_INPUT_DOMAIN = (
    b"heterodiff.adapter.publication-profile-input-binding.v1"
)
_PUBLICATION_INVOCATION_INPUT_DOMAIN = (
    b"heterodiff.adapter.publication-invocation-input.v1"
)


def _base64_length(value: int) -> int:
    if type(value) is not int or value < 0:
        raise TypeError("base64 length input must be nonnegative")
    return 4 * ((value + 2) // 3)


def _evidence_raw_lengths(value: object) -> Tuple[int, ...]:
    if type(value) not in (
        _evidence.CompleteAdaptedEventSample,
        _evidence.ExpectedAdapterEvidence,
    ):
        raise TypeError("evidence aggregate has an invalid exact type")
    def payload_lengths(
        container: object,
        *,
        container_type: object,
        item_type: object,
        attribute: str,
        maximum_items: int,
    ) -> list:
        if type(container) is not container_type:
            raise TypeError("evidence leaf has an invalid exact type")
        entries = getattr(container, "items", None)
        if entries is None:
            entries = getattr(container, "entries", None)
        if type(entries) is not tuple:
            raise TypeError("evidence entries must be an exact tuple")
        if len(entries) > maximum_items:
            raise AdapterEvidenceResourceError(
                "evidence entries exceed their aggregate preflight bound"
            )
        result = []
        for item in entries:
            if type(item) is not item_type:
                raise TypeError("evidence entry has an invalid exact type")
            payload = getattr(item, attribute)
            if type(payload) is not bytes:
                raise TypeError("evidence payload must be exact bytes")
            if len(payload) > _evidence.MAXIMUM_SINGLE_PAYLOAD_BYTES:
                raise AdapterEvidenceResourceError(
                    "evidence payload exceeds its preflight bound"
                )
            result.append(len(payload))
        return result

    if type(value.inventory) is not _evidence.SourceInventory:
        raise TypeError("inventory has an invalid exact type")
    lengths = payload_lengths(
        value.inventory,
        container_type=_evidence.SourceInventory,
        item_type=_evidence.SourceInventoryItem,
        attribute="canonical_item_bytes",
        maximum_items=_evidence.MAXIMUM_INVENTORY_ITEMS,
    )
    lengths.extend(
        payload_lengths(
            value.static_context,
            container_type=_evidence.StaticContext,
            item_type=_evidence.StaticContextEntry,
            attribute="canonical_payload_bytes",
            maximum_items=_evidence.MAXIMUM_KEYED_LEAF_ENTRIES,
        )
    )
    lengths.extend(
        payload_lengths(
            value.evaluation_labels,
            container_type=_evidence.EvaluationLabels,
            item_type=_evidence.EvaluationLabelEntry,
            attribute="canonical_payload_bytes",
            maximum_items=_evidence.MAXIMUM_KEYED_LEAF_ENTRIES,
        )
    )
    lengths.extend(
        payload_lengths(
            value.provenance,
            container_type=_evidence.PrivateProvenance,
            item_type=_evidence.OccurrenceProvenance,
            attribute="private_payload_bytes",
            maximum_items=_evidence.MAXIMUM_SEMANTIC_OCCURRENCES,
        )
    )
    if value.fitted_state is not None:
        if type(value.fitted_state) is not _evidence.FittedAdapterState:
            raise TypeError("fitted state has an invalid exact type")
        for payload in (
            value.fitted_state.fit_configuration_bytes,
            value.fitted_state.parameter_bytes,
        ):
            if type(payload) is not bytes:
                raise TypeError("fitted-state payload must be exact bytes")
            if len(payload) > _evidence.MAXIMUM_SINGLE_PAYLOAD_BYTES:
                raise AdapterEvidenceResourceError(
                    "fitted-state payload exceeds its preflight bound"
                )
            lengths.append(len(payload))
    if type(value.reconstruction) is not _evidence.SemanticReconstruction:
        raise TypeError("reconstruction has an invalid exact type")
    reconstruction = value.reconstruction.canonical_payload_bytes
    if type(reconstruction) is not bytes:
        raise TypeError("reconstruction payload must be exact bytes")
    if len(reconstruction) > _evidence.MAXIMUM_SINGLE_PAYLOAD_BYTES:
        raise AdapterEvidenceResourceError(
            "reconstruction payload exceeds its preflight bound"
        )
    lengths.append(len(reconstruction))
    return tuple(lengths)


def _preflight_request_aggregate(request: PublicationRequestV1) -> None:
    """Apply request-global byte bounds before invoking any adapter callback."""

    if type(request.cases) is not tuple or not request.cases:
        raise TypeError("cases must be an exact nonempty tuple")
    if len(request.cases) > MAXIMUM_PUBLICATION_CASES:
        raise AdapterEvidenceResourceError("too many publication cases")
    raw_private_bytes = 0
    minimum_encoded_bytes = 0
    for case in request.cases:
        if type(case) is not VerifiedDetachedCaseInputV1:
            raise TypeError("case input must be exact")
        if type(case.source_bytes) is not bytes:
            raise TypeError("source bytes must be exact")
        if type(case.independent_golden_definition_bytes) is not bytes:
            raise TypeError("golden bytes must be exact")
        source_length = len(case.source_bytes)
        golden_length = len(case.independent_golden_definition_bytes)
        raw_private_bytes += source_length + golden_length
        minimum_encoded_bytes += _base64_length(source_length)
        minimum_encoded_bytes += _base64_length(golden_length)
        for evidence in (case.complete_sample, case.expected_evidence):
            for length in _evidence_raw_lengths(evidence):
                raw_private_bytes += length
                minimum_encoded_bytes += _base64_length(length)
        raw_reconstruction = case.complete_sample.raw_reconstruction_bytes
        if raw_reconstruction is not None:
            if type(raw_reconstruction) is not bytes:
                raise TypeError("raw reconstruction must be exact bytes")
            length = len(raw_reconstruction)
            raw_private_bytes += length
            minimum_encoded_bytes += _base64_length(length)
        if (
            raw_private_bytes > MAXIMUM_PRIVATE_ARTIFACT_BYTES
            or minimum_encoded_bytes > MAXIMUM_PRIVATE_ARTIFACT_BYTES
        ):
            raise AdapterEvidenceResourceError(
                "publication private bytes exceed their aggregate ceiling"
            )
    if type(request.hostile_controls) is not tuple:
        raise TypeError("hostile controls must be an exact tuple")
    if len(request.hostile_controls) > MAXIMUM_HOSTILE_CONTROL_RECEIPTS:
        raise AdapterEvidenceResourceError("too many hostile controls")
    hostile_bytes = 0
    for value in request.hostile_controls:
        if type(value) is not HostileControlInputV1:
            raise TypeError("hostile control must be exact")
        if type(value.input_bytes) is not bytes:
            raise TypeError("hostile input must be exact bytes")
        if type(value.test_node_bytes) is not bytes:
            raise TypeError("hostile test node must be exact bytes")
        hostile_bytes += len(value.input_bytes) + len(value.test_node_bytes)
        if hostile_bytes > MAXIMUM_PRIVATE_ARTIFACT_BYTES:
            raise AdapterEvidenceResourceError(
                "hostile control bytes exceed their aggregate ceiling"
            )


def _domain_digest_bytes(domain: bytes, payload: bytes) -> str:
    if type(domain) is not bytes or type(payload) is not bytes:
        raise TypeError("digest inputs must be exact bytes")
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def publication_profile_input_sha256(
    value: PublicationBindingInputV1,
) -> str:
    """Bind every exact request binding through one fixed binary frame."""

    if type(value) is not PublicationBindingInputV1:
        raise TypeError("publication bindings must be exact")
    digest = hashlib.sha256()
    digest.update(_PUBLICATION_PROFILE_INPUT_DOMAIN)
    digest.update(b"\x00")
    names = tuple(PublicationBindingInputV1.__dataclass_fields__)
    digest.update(len(names).to_bytes(8, "big"))
    for name in names:
        encoded_name = name.encode("ascii", "strict")
        component = getattr(value, name)
        if type(component) is not bytes or not component:
            raise TypeError("publication binding component must be exact bytes")
        digest.update(len(encoded_name).to_bytes(8, "big"))
        digest.update(encoded_name)
        digest.update(len(component).to_bytes(8, "big"))
        digest.update(hashlib.sha256(component).digest())
    return digest.hexdigest()


def publication_invocation_input_sha256(
    bindings: PublicationBindingInputV1,
    public_ids: PublicIdentifierRegistryV1,
    cases: Tuple[VerifiedDetachedCaseInputV1, ...],
    hostile_controls: Tuple[HostileControlInputV1, ...],
) -> str:
    """Bind the complete callback-free development invocation input set."""

    if type(bindings) is not PublicationBindingInputV1:
        raise TypeError("publication bindings must be exact")
    if type(public_ids) is not PublicIdentifierRegistryV1:
        raise TypeError("public IDs must be exact")
    if type(cases) is not tuple or not cases:
        raise TypeError("cases must be a nonempty exact tuple")
    if len(cases) > MAXIMUM_PUBLICATION_CASES:
        raise AdapterEvidenceResourceError("too many publication cases")
    if type(hostile_controls) is not tuple:
        raise TypeError("hostile controls must be an exact tuple")
    if len(hostile_controls) > MAXIMUM_HOSTILE_CONTROL_RECEIPTS:
        raise AdapterEvidenceResourceError("too many hostile controls")

    case_records = []
    for value in cases:
        if type(value) is not VerifiedDetachedCaseInputV1:
            raise TypeError("case input must be exact")
        descriptor = _payloads.adapter_descriptor_payload(value.descriptor)
        split = _payloads.split_manifest_payload(value.split_manifest)
        complete = _payloads.complete_sample_commitment_payload(
            value.descriptor,
            value.complete_sample
        )
        expected = _payloads.expected_evidence_payload(
            value.expected_evidence
        )
        configuration = (
            _payloads.identity_bearing_native_configuration_payload(
                value.expected_configuration
            )
        )
        run = _payloads.conformance_run_payload(value.conformance_run)
        identity = value.descriptor.identity
        case_records.append(
            {
                "adapter_id": identity.adapter_id,
                "adapter_version": identity.adapter_version,
                "complete_sample_commitment_sha256": (
                    complete.payload_sha256
                ),
                "conformance_run_sha256": run.payload_sha256,
                "descriptor_sha256": descriptor.payload_sha256,
                "expected_configuration_sha256": (
                    configuration.payload_sha256
                ),
                "expected_evidence_sha256": expected.payload_sha256,
                "golden_definition_byte_count": len(
                    value.independent_golden_definition_bytes
                ),
                "golden_definition_file_sha256": hashlib.sha256(
                    value.independent_golden_definition_bytes
                ).hexdigest(),
                "sample_root_sha256": value.conformance_run.sample_root_sha256,
                "source_byte_count": len(value.source_bytes),
                "source_sha256": hashlib.sha256(
                    value.source_bytes
                ).hexdigest(),
                "split_manifest_sha256": split.payload_sha256,
            }
        )
    case_records.sort(
        key=lambda item: (
            item["sample_root_sha256"],
            item["expected_evidence_sha256"],
            item["adapter_id"],
        )
    )

    hostile_records = []
    for value in hostile_controls:
        if type(value) is not HostileControlInputV1:
            raise TypeError("hostile control must be exact")
        receipt = _payloads.hostile_control_receipt_payload(value)
        hostile_records.append(
            {
                "control_id": value.control_id,
                "error_code": value.error_code,
                "hostile_control_receipt_sha256": receipt.payload_sha256,
                "input_sha256": _payloads.domain_separated_sha256(
                    _payloads.HOSTILE_CONTROL_INPUT_DIGEST_DOMAIN,
                    value.input_bytes,
                ),
                "status_id": value.status_id,
                "test_node_sha256": _payloads.domain_separated_sha256(
                    _payloads.HOSTILE_CONTROL_TEST_NODE_DIGEST_DOMAIN,
                    value.test_node_bytes,
                ),
            }
        )
    hostile_records.sort(key=lambda item: item["control_id"])
    tree = {
        "binding_input_sha256": publication_profile_input_sha256(bindings),
        "cases": case_records,
        "hostile_controls": hostile_records,
        "public_id_registry_sha256": (
            _payloads.public_identifier_registry_payload(
                public_ids
            ).payload_sha256
        ),
    }
    encoded = _payloads._canonical_tree_bytes(
        tree,
        maximum_encoded_bytes=MAXIMUM_PRIVATE_ARTIFACT_BYTES,
    )
    return _domain_digest_bytes(_PUBLICATION_INVOCATION_INPUT_DOMAIN, encoded)


def _snapshot_bindings(value: object) -> PublicationBindingInputV1:
    if type(value) is not PublicationBindingInputV1:
        raise TypeError("bindings must be exact")
    return PublicationBindingInputV1(
        **{
            name: getattr(value, name)
            for name in PublicationBindingInputV1.__dataclass_fields__
        }
    )


def _snapshot_registry(value: object) -> PublicIdentifierRegistryV1:
    if type(value) is not PublicIdentifierRegistryV1:
        raise TypeError("public-ID registry must be exact")
    values = {
        name: getattr(value, name)
        for name in PublicIdentifierRegistryV1.__dataclass_fields__
        if name != "adapter_identities"
    }
    identities = value.adapter_identities
    if type(identities) is not tuple:
        raise TypeError("adapter identities must be exact")
    if not identities:
        raise TypeError("adapter identities must not be empty")
    if len(identities) > MAXIMUM_REGISTRY_VALUES_PER_CATEGORY:
        raise AdapterEvidenceResourceError(
            "adapter identities are outside their value bound"
        )
    copied_identities = []
    for item in identities:
        if type(item) is not PublicAdapterIdentityV1:
            raise TypeError("adapter identity must be exact")
        copied_identities.append(
            PublicAdapterIdentityV1(item.adapter_id, item.adapter_version)
        )
    values["adapter_identities"] = tuple(copied_identities)
    return PublicIdentifierRegistryV1(**values)


def _snapshot_run(value: object) -> ConformanceRun:
    if type(value) is not ConformanceRun:
        raise TypeError("conformance run must be exact")
    return ConformanceRun(
        adapter_id=value.adapter_id,
        adapter_version=value.adapter_version,
        descriptor_sha256=value.descriptor_sha256,
        source_sha256=value.source_sha256,
        split_manifest_sha256=value.split_manifest_sha256,
        native_observation_sha256=value.native_observation_sha256,
        sample_root_sha256=value.sample_root_sha256,
        expected_evidence_sha256=value.expected_evidence_sha256,
        plan=value.plan,
        records=value.records,
        capability_control_trace=value.capability_control_trace,
    )


def _snapshot_case(value: object) -> _CaseSnapshot:
    if type(value) is not VerifiedDetachedCaseInputV1:
        raise TypeError("case input must be exact")
    checked = VerifiedDetachedCaseInputV1(
        adapter=value.adapter,
        source_bytes=value.source_bytes,
        descriptor=value.descriptor,
        split_manifest=value.split_manifest,
        complete_sample=value.complete_sample,
        expected_evidence=value.expected_evidence,
        expected_configuration=value.expected_configuration,
        conformance_run=value.conformance_run,
        independent_golden_definition_bytes=(
            value.independent_golden_definition_bytes
        ),
    )
    return _CaseSnapshot(
        adapter=checked.adapter,
        source_bytes=checked.source_bytes,
        descriptor=_contract._snapshot_descriptor(checked.descriptor),
        split_manifest=_evidence.snapshot_bounded_split_manifest(
            checked.split_manifest
        ),
        complete_sample=_evidence._snapshot_complete(
            checked.complete_sample
        ),
        expected_evidence=_evidence._snapshot_expected_evidence(
            checked.expected_evidence
        ),
        expected_configuration=(
            _evidence.snapshot_bounded_native_configuration(
                checked.expected_configuration
            )
        ),
        conformance_run=_snapshot_run(checked.conformance_run),
        independent_golden_definition_bytes=(
            checked.independent_golden_definition_bytes
        ),
    )


def _snapshot_hostile(value: object) -> HostileControlInputV1:
    if type(value) is not HostileControlInputV1:
        raise TypeError("hostile control must be exact")
    return HostileControlInputV1(
        control_id=value.control_id,
        status_id=value.status_id,
        error_code=value.error_code,
        input_bytes=value.input_bytes,
        test_node_bytes=value.test_node_bytes,
    )


def _snapshot_guard(value: object) -> PublicationExecutionGuardInputV1:
    if type(value) is not PublicationExecutionGuardInputV1:
        raise TypeError("execution-guard input must be exact")
    manifest = value.run_manifest
    if type(manifest) is not ExecutionGuardRunManifestV1:
        raise TypeError("execution guard run manifest must be exact")
    manifest_snapshot = ExecutionGuardRunManifestV1(
        **{
            name: getattr(manifest, name)
            for name, definition in (
                ExecutionGuardRunManifestV1.__dataclass_fields__.items()
            )
            if definition.init
        }
    )
    return PublicationExecutionGuardInputV1(
        receipt=validate_execution_receipt(value.receipt),
        run_manifest=manifest_snapshot,
        run_manifest_bytes=value.run_manifest_bytes,
        test_inventory_bytes=value.test_inventory_bytes,
    )


def _event_id_key(value: object) -> Tuple[object, ...]:
    if value is None:
        return (0,)
    if type(value) is str:
        _contract._validated_private_text(value, name="event_id")
        return (1, value)
    if type(value) is not tuple:
        raise TypeError("event_id has no frozen private ordering")
    components = []
    for item in value:
        if type(item) is int:
            components.append((0, item))
        elif type(item) is str:
            _contract._validated_private_text(item, name="event_id component")
            components.append((1, item))
        else:
            raise TypeError("event_id component has no frozen private ordering")
    return (2, tuple(components))


def _configuration_key(configuration: object) -> Tuple[object, ...]:
    snapshot = _evidence.snapshot_bounded_native_configuration(configuration)
    observed = snapshot.observed
    if observed is None:
        raise TypeError("configuration observation must be present")
    occurrences = tuple(
        sorted(
            zip(snapshot.events, observed.events),
            key=lambda pair: (
                pair[0].model_key(),
                pair[1].signature_key(),
                _event_id_key(pair[0].event_id),
            ),
        )
    )
    return (
        _contract.feature_schema_digest(snapshot.schema),
        tuple(
            (
                event.model_key(),
                observation.signature_key(),
                _event_id_key(event.event_id),
            )
            for event, observation in occurrences
        ),
        observed.cardinality_observed,
        snapshot.sample_id,
        snapshot.group_id,
        _contract.native_observation_digest(snapshot),
    )


def _complete_key(
    complete: _evidence.CompleteAdaptedEventSample,
) -> Tuple[object, ...]:
    return (
        _configuration_key(complete.sample.configuration),
        complete.sample.manifest,
        complete.inventory,
        complete.coverage,
        complete.static_context,
        complete.evaluation_labels,
        complete.provenance,
        complete.fitted_state,
        complete.reconstruction,
        complete.raw_reconstruction_bytes,
    )


def _case_key(value: _CaseSnapshot) -> Tuple[object, ...]:
    return (
        value.source_bytes,
        value.descriptor,
        value.split_manifest,
        _complete_key(value.complete_sample),
        value.expected_evidence,
        _configuration_key(value.expected_configuration),
        value.conformance_run,
        value.independent_golden_definition_bytes,
    )


def _require_member(value: str, category: Tuple[str, ...]) -> None:
    if value not in category:
        _fail(PublicationFreezeCode.PUB_ID_NOT_ALLOWLISTED)


def _check_case_public_ids(
    case: _CaseSnapshot,
    registry: PublicIdentifierRegistryV1,
) -> None:
    descriptor = case.descriptor
    identity = descriptor.identity
    identity_key = (identity.adapter_id, identity.adapter_version)
    admitted_identities = tuple(
        (item.adapter_id, item.adapter_version)
        for item in registry.adapter_identities
    )
    if identity_key not in admitted_identities:
        _fail(PublicationFreezeCode.PUB_ID_NOT_ALLOWLISTED)
    _require_member(identity.contract_version, registry.contract_ids)
    capabilities = descriptor.capabilities
    _require_member(capabilities.time_measure.value, registry.time_measure_ids)
    _require_member(
        capabilities.multiplicity_mode.value,
        registry.multiplicity_ids,
    )
    for name in _CAPABILITY_FIELDS:
        if getattr(capabilities, name):
            _require_member(name, registry.capability_ids)
    for representation_id in capabilities.supported_representation_ids:
        _require_member(representation_id, registry.representation_ids)

    run = case.conformance_run
    if (
        run.adapter_id != identity.adapter_id
        or run.adapter_version != identity.adapter_version
    ):
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    for record in run.records:
        _require_member(record.check_id, registry.check_ids)
        _require_member(record.plan_mode.value, registry.plan_mode_ids)
        _require_member(record.status.value, registry.terminal_status_ids)
        _require_member(
            "NONE" if record.reason is None else record.reason,
            registry.not_applicable_reason_ids,
        )
        _require_member(
            (
                "NONE"
                if record.representation_id is None
                else record.representation_id
            ),
            registry.representation_ids,
        )

    for evidence in (case.complete_sample, case.expected_evidence):
        for entry in evidence.coverage.entries:
            if entry.exclusion_reason_code is not None:
                _require_member(
                    entry.exclusion_reason_code,
                    registry.coverage_exclusion_reason_ids,
                )
        for entry in evidence.provenance.entries:
            for status in entry.field_statuses:
                if status.reason_code is not None:
                    _require_member(
                        status.reason_code,
                        registry.censor_reason_ids,
                    )


def _check_hostile_public_ids(
    values: Tuple[HostileControlInputV1, ...],
    registry: PublicIdentifierRegistryV1,
) -> None:
    control_ids = tuple(value.control_id for value in values)
    if len(set(control_ids)) != len(control_ids):
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    if tuple(sorted(control_ids)) != registry.hostile_control_ids:
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    for value in values:
        _require_member(value.control_id, registry.hostile_control_ids)
        _require_member(value.status_id, registry.hostile_status_ids)
        _require_member(value.error_code, registry.rejection_code_ids)


def _check_guard_public_ids(
    value: PublicationExecutionGuardInputV1,
    registry: PublicIdentifierRegistryV1,
) -> None:
    receipt = value.receipt
    _require_member(receipt.status.value, registry.execution_status_ids)
    for resource_id in ("elapsed_wall_nanoseconds", "peak_rss_bytes"):
        _require_member(resource_id, registry.resource_ids)
    for unit_id in ("bytes", "nanoseconds"):
        _require_member(unit_id, registry.unit_ids)
    manifest = value.run_manifest
    _require_member(manifest.clock_method_id, registry.wall_time_method_ids)
    _require_member(
        manifest.peak_rss_method_id,
        registry.peak_rss_method_ids,
    )
    _require_member(
        manifest.execution_backend_id,
        registry.execution_backend_ids,
    )
    _require_member(
        manifest.cwd_launch_method_id,
        registry.cwd_launch_method_ids,
    )
    _require_member(
        manifest.process_containment_id,
        registry.process_containment_ids,
    )
    _require_member(
        manifest.filesystem_confinement_id,
        registry.filesystem_confinement_ids,
    )
    _require_member(
        manifest.output_capture_method_id,
        registry.output_capture_method_ids,
    )
    _require_member(
        manifest.source_binding_format_id,
        registry.source_binding_format_ids,
    )
    _require_member(
        manifest.guard_implementation_status_id,
        registry.guard_implementation_status_ids,
    )
    _require_member(
        manifest.address_space_limit_method_id,
        registry.address_space_limit_method_ids,
    )
    for status_id in manifest.allowed_execution_status_ids:
        _require_member(status_id, registry.execution_status_ids)
    if receipt.wall_limit_triggered:
        wall_status = "ceiling_triggered"
    elif (
        receipt.elapsed_monotonic_nanoseconds
        > receipt.wall_time_limit_nanoseconds
    ):
        wall_status = "observed_above_ceiling"
    else:
        wall_status = "observed_within_ceiling_noncertifying"
    if receipt.peak_rss_limit_triggered:
        rss_status = "ceiling_triggered"
    elif (
        receipt.measured_peak_rss_bytes is not None
        and receipt.measured_peak_rss_bytes > receipt.peak_rss_limit_bytes
    ):
        rss_status = "observed_above_ceiling"
    elif receipt.measured_peak_rss_bytes is None:
        rss_status = "observation_unavailable"
    elif (
        not receipt.peak_rss_enforcement_exact
        or not receipt.peak_rss_observation_finalized
    ):
        rss_status = "observed_within_ceiling_noncertifying"
    else:
        rss_status = "observed_within_ceiling"
    _require_member(wall_status, registry.resource_status_ids)
    _require_member(rss_status, registry.resource_status_ids)


def _check_guard_source_binding(
    value: PublicationExecutionGuardInputV1,
) -> None:
    if (
        value.receipt.source_binding_format
        is not SourceBindingFormat.EXECUTION_GUARD_INPUT_BINDING_V1
    ):
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)


def _check_guard_manifest(
    value: PublicationExecutionGuardInputV1,
    bindings: PublicationBindingInputV1,
    invocation_input_sha256: str,
) -> None:
    manifest = value.run_manifest
    receipt = value.receipt
    if receipt.status.value not in manifest.allowed_execution_status_ids:
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    receipt_pairs = (
        (manifest.argv_sha256, receipt.argv_sha256),
        (
            manifest.working_directory_sha256,
            receipt.working_directory_sha256,
        ),
        (manifest.environment_sha256, receipt.environment_sha256),
        (manifest.clock_method_id, receipt.clock_method.value),
        (manifest.execution_backend_id, receipt.execution_backend.value),
        (manifest.cwd_launch_method_id, receipt.cwd_launch_method.value),
        (
            manifest.process_containment_id,
            receipt.process_containment_method.value,
        ),
        (
            manifest.filesystem_confinement_id,
            receipt.filesystem_confinement_method.value,
        ),
        (
            manifest.output_capture_method_id,
            receipt.output_capture_method.value,
        ),
        (manifest.peak_rss_method_id, receipt.peak_rss_method.value),
        (
            manifest.source_binding_format_id,
            receipt.source_binding_format.value,
        ),
        (
            manifest.guard_implementation_status_id,
            receipt.implementation_status,
        ),
        (
            manifest.address_space_limit_method_id,
            receipt.address_space_limit_method.value,
        ),
        (manifest.output_limit_bytes, receipt.output_limit_bytes),
        (manifest.peak_rss_limit_bytes, receipt.peak_rss_limit_bytes),
        (
            manifest.wall_time_limit_nanoseconds,
            receipt.wall_time_limit_nanoseconds,
        ),
        (
            manifest.address_space_limit_bytes,
            receipt.address_space_limit_bytes,
        ),
        (
            manifest.decision_eligible_required,
            receipt.decision_eligible,
        ),
    )
    if any(expected != observed for expected, observed in receipt_pairs):
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    if (
        manifest.managed_process_group_quiescence_required
        and not receipt.managed_process_group_quiescent
    ):
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    if manifest.output_complete_required and not receipt.output_complete:
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    binding_pairs = (
        (
            manifest.dependency_lock_sha256,
            hashlib.sha256(bindings.dependency_lock_bytes).hexdigest(),
        ),
        (
            manifest.environment_manifest_sha256,
            hashlib.sha256(bindings.environment_manifest_bytes).hexdigest(),
        ),
        (
            manifest.execution_guard_source_sha256,
            hashlib.sha256(
                bindings.execution_guard_source_bytes
            ).hexdigest(),
        ),
        (
            manifest.interpreter_executable_sha256,
            hashlib.sha256(
                bindings.interpreter_executable_bytes
            ).hexdigest(),
        ),
        (
            manifest.publication_invocation_input_sha256,
            invocation_input_sha256,
        ),
        (
            manifest.publication_profile_input_sha256,
            publication_profile_input_sha256(bindings),
        ),
        (
            manifest.source_tree_manifest_sha256,
            hashlib.sha256(
                bindings.source_tree_manifest_bytes
            ).hexdigest(),
        ),
        (
            manifest.test_inventory_sha256,
            _domain_digest_bytes(
                _TEST_INVENTORY_DIGEST_DOMAIN,
                value.test_inventory_bytes,
            ),
        ),
    )
    if any(expected != observed for expected, observed in binding_pairs):
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    if value.test_inventory_bytes != bindings.test_inventory_bytes:
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    binding_bytes = publication_source_binding_bytes(
        value.run_manifest_bytes,
        value.test_inventory_bytes,
    )
    if value.receipt.source_sha256 != hashlib.sha256(
        binding_bytes
    ).hexdigest():
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)


def _adapter_surface_key(adapter: object) -> Tuple[object, ...]:
    descriptor = _contract._snapshot_descriptor(adapter.descriptor())
    schema = _evidence.snapshot_bounded_schema(adapter.schema())
    return descriptor, _contract.feature_schema_digest(schema)


def _fresh_run(case: _CaseSnapshot, registry: PublicIdentifierRegistryV1) -> ConformanceRun:
    try:
        fresh_sample = case.adapter.adapt(
            case.source_bytes,
            case.complete_sample.sample.manifest.partition,
            case.split_manifest,
        )
        if type(fresh_sample) is not _contract.AdaptedEventSample:
            raise TypeError("adapter output must be an exact adapted sample")
        fresh_sample = _contract.AdaptedEventSample(
            _evidence.snapshot_bounded_native_configuration(
                fresh_sample.configuration
            ),
            fresh_sample.manifest,
        )
    except Exception:
        _fail(PublicationFreezeCode.PUB_RUN_ORIGIN_INVALID)
    if (
        fresh_sample.manifest != case.complete_sample.sample.manifest
        or _configuration_key(fresh_sample.configuration)
        != _configuration_key(case.complete_sample.sample.configuration)
    ):
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    try:
        result = run_complete_adapter_conformance(
            case.adapter,
            case.complete_sample,
            source_bytes=case.source_bytes,
            split_manifest=case.split_manifest,
            expected_evidence=case.expected_evidence,
            allowed_exclusion_reason_codes=(
                registry.coverage_exclusion_reason_ids
            ),
            allowed_censor_reason_codes=registry.censor_reason_ids,
        )
    except Exception:
        _fail(PublicationFreezeCode.PUB_RUN_ORIGIN_INVALID)
    return _snapshot_run(result)


def _validate_case_recomputations(
    case: _CaseSnapshot,
    fresh_run: ConformanceRun,
) -> None:
    if fresh_run != case.conformance_run:
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    if fresh_run.descriptor_sha256 != case.descriptor.descriptor_sha256:
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    if fresh_run.source_sha256 != case.complete_sample.sample.manifest.source_sha256:
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    if (
        _configuration_key(case.complete_sample.sample.configuration)
        != _configuration_key(case.expected_configuration)
    ):
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    if (
        _contract.native_observation_digest(case.expected_configuration)
        != case.expected_evidence.native_observation_sha256
    ):
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)


def _frozen_case(
    case: _CaseSnapshot,
    fresh_run: ConformanceRun,
) -> FrozenDetachedCaseV1:
    return FrozenDetachedCaseV1(
        source_bytes=case.source_bytes,
        descriptor=case.descriptor,
        split_manifest=case.split_manifest,
        complete_sample=case.complete_sample,
        expected_evidence=case.expected_evidence,
        expected_configuration=case.expected_configuration,
        conformance_run=fresh_run,
        independent_golden_definition_bytes=(
            case.independent_golden_definition_bytes
        ),
    )


def freeze_publication_input(request: PublicationRequestV1) -> FrozenPublicationInputV1:
    """Return fresh source-bound snapshots without serializing or writing."""

    if type(request) is not PublicationRequestV1:
        _fail(PublicationFreezeCode.PUB_INPUT_TYPE)
    try:
        _preflight_request_aggregate(request)
        bindings = _snapshot_bindings(request.bindings)
        registry = _snapshot_registry(request.public_ids)
        if type(request.cases) is not tuple or not request.cases:
            raise TypeError("cases must be exact")
        if len(request.cases) > MAXIMUM_PUBLICATION_CASES:
            raise AdapterEvidenceResourceError("too many publication cases")
        cases = tuple(_snapshot_case(value) for value in request.cases)
        if type(request.hostile_controls) is not tuple:
            raise TypeError("hostile controls must be exact")
        if (
            len(request.hostile_controls)
            > MAXIMUM_HOSTILE_CONTROL_RECEIPTS
        ):
            raise AdapterEvidenceResourceError("too many hostile controls")
        hostiles = tuple(
            _snapshot_hostile(value) for value in request.hostile_controls
        )
        guard = _snapshot_guard(request.execution_guard)
        invocation_input_sha256 = publication_invocation_input_sha256(
            request.bindings,
            request.public_ids,
            request.cases,
            request.hostile_controls,
        )
    except AdapterEvidenceResourceError:
        _fail(PublicationFreezeCode.PUB_INPUT_RESOURCE)
    except PublicationFreezeError:
        raise
    except Exception:
        _fail(PublicationFreezeCode.PUB_INPUT_TYPE)

    _check_hostile_public_ids(hostiles, registry)
    _check_guard_public_ids(guard, registry)
    _check_guard_source_binding(guard)
    _check_guard_manifest(guard, bindings, invocation_input_sha256)
    for case in cases:
        _check_case_public_ids(case, registry)

    frozen_cases = []
    for case in cases:
        fresh_run = _fresh_run(case, registry)
        _validate_case_recomputations(case, fresh_run)
        try:
            descriptor_after, schema_after = _adapter_surface_key(case.adapter)
        except Exception:
            _fail(PublicationFreezeCode.PUB_POSTMUTATION)
        if (
            descriptor_after != case.descriptor
            or schema_after
            != _contract.feature_schema_digest(
                case.complete_sample.sample.configuration.schema
            )
        ):
            _fail(PublicationFreezeCode.PUB_POSTMUTATION)
        frozen_cases.append(_frozen_case(case, fresh_run))

    try:
        bindings_after = _snapshot_bindings(request.bindings)
        registry_after = _snapshot_registry(request.public_ids)
        if type(request.cases) is not tuple or not request.cases:
            raise TypeError("cases changed outer shape")
        if len(request.cases) > MAXIMUM_PUBLICATION_CASES:
            raise TypeError("cases changed outer bound")
        cases_after = tuple(_snapshot_case(value) for value in request.cases)
        if type(request.hostile_controls) is not tuple:
            raise TypeError("hostile controls changed outer shape")
        if (
            len(request.hostile_controls)
            > MAXIMUM_HOSTILE_CONTROL_RECEIPTS
        ):
            raise TypeError("hostile controls changed outer bound")
        hostiles_after = tuple(
            _snapshot_hostile(value) for value in request.hostile_controls
        )
        guard_after = _snapshot_guard(request.execution_guard)
        invocation_input_sha256_after = publication_invocation_input_sha256(
            request.bindings,
            request.public_ids,
            request.cases,
            request.hostile_controls,
        )
    except Exception:
        _fail(PublicationFreezeCode.PUB_POSTMUTATION)
    if (
        bindings_after != bindings
        or registry_after != registry
        or any(
            after.adapter is not before.adapter
            for before, after in zip(cases, cases_after)
        )
        or tuple(_case_key(value) for value in cases_after)
        != tuple(_case_key(value) for value in cases)
        or hostiles_after != hostiles
        or guard_after != guard
        or invocation_input_sha256_after != invocation_input_sha256
    ):
        _fail(PublicationFreezeCode.PUB_POSTMUTATION)

    frozen_cases.sort(
        key=lambda value: (
            value.conformance_run.sample_root_sha256,
            value.conformance_run.expected_evidence_sha256,
            value.conformance_run.adapter_id,
        )
    )
    sample_roots = tuple(
        value.conformance_run.sample_root_sha256 for value in frozen_cases
    )
    if len(set(sample_roots)) != len(sample_roots):
        _fail(PublicationFreezeCode.PUB_RECOMPUTATION_MISMATCH)
    sorted_hostiles = tuple(sorted(hostiles, key=lambda value: value.control_id))
    return FrozenPublicationInputV1(
        bindings=bindings,
        public_ids=registry,
        cases=tuple(frozen_cases),
        hostile_controls=sorted_hostiles,
        execution_guard=guard,
    )


__all__ = [
    "FrozenDetachedCaseV1",
    "FrozenPublicationInputV1",
    "PublicationFreezeCode",
    "PublicationFreezeError",
    "freeze_publication_input",
    "publication_invocation_input_sha256",
    "publication_profile_input_sha256",
]
