"""Write-free Phase-D publication preparation under an explicit HOLD.

The public entry point accepts only an original ``PublicationRequestV1``.  It
freezes and re-runs the source-bound conformance path itself, constructs the
closed public/private artifacts from typed projections, freezes the request a
second time to detect mutation, and returns bytes without writing them.

This is a development publisher, not a decision authority.  In particular,
the current request type does not yet provide an independently trusted A9.1
identity or a typed golden-provenance receipt.  No result from this module can
represent ``ADAPTER-CONFORMANCE-GO``.
"""

from __future__ import annotations

from enum import Enum
import hashlib
from types import MappingProxyType
from typing import Iterable, Tuple

from . import adapter_contract as _contract
from . import adapter_evidence as _evidence
from . import adapter_publication_payloads as _payloads
from .adapter_publication_freeze import (
    FrozenDetachedCaseV1,
    FrozenPublicationInputV1,
    PublicationFreezeError,
    freeze_publication_input,
)
from .adapter_publication_types import (
    MAXIMUM_PRIVATE_ARTIFACT_BYTES,
    MAXIMUM_PUBLIC_ARTIFACT_BYTES,
    PRIVATE_ENVELOPE_ARTIFACT_ID,
    PRIVATE_ENVELOPE_ARTIFACT_TYPE,
    PUBLICATION_DECISION_STATUS,
    PUBLICATION_DEVELOPMENT_STATUS,
    PUBLICATION_MANIFEST_ARTIFACT_TYPE,
    PUBLIC_CORE_ARTIFACT_ID,
    PUBLIC_CORE_ARTIFACT_TYPE,
    PreparedPublicationV1,
    PublicIdentifierRegistryV1,
    PublicationRequestV1,
)


PUBLICATION_PREPARATION_IMPLEMENTATION_STATUS = "DEVELOPMENT_ONLY"

PUBLIC_CORE_DIGEST_DOMAIN = PUBLIC_CORE_ARTIFACT_TYPE
PRIVATE_ENVELOPE_DIGEST_DOMAIN = PRIVATE_ENVELOPE_ARTIFACT_TYPE
PUBLICATION_MANIFEST_DIGEST_DOMAIN = PUBLICATION_MANIFEST_ARTIFACT_TYPE
PUBLICATION_BINDINGS_DIGEST_DOMAIN = (
    "heterodiff.adapter.publication-bindings.v1"
)
TEST_INVENTORY_DIGEST_DOMAIN = "heterodiff.adapter.test-inventory.v1"
HOSTILE_CONTROL_INPUT_DIGEST_DOMAIN = (
    _payloads.HOSTILE_CONTROL_INPUT_DIGEST_DOMAIN
)
HOSTILE_CONTROL_TEST_NODE_DIGEST_DOMAIN = (
    _payloads.HOSTILE_CONTROL_TEST_NODE_DIGEST_DOMAIN
)

_CAPABILITY_FIELDS = (
    "semantic_reconstruction",
    "raw_byte_reconstruction",
    "fitted_state",
    "static_context",
    "evaluation_labels",
    "private_provenance",
)


class PublicationPreparationCode(str, Enum):
    """Closed failures emitted by write-free artifact construction."""

    PUB_INPUT_TYPE = "PUB_INPUT_TYPE"
    PUB_INPUT_SCHEMA = "PUB_INPUT_SCHEMA"
    PUB_INPUT_RESOURCE = "PUB_INPUT_RESOURCE"
    PUB_ID_NOT_ALLOWLISTED = "PUB_ID_NOT_ALLOWLISTED"
    PUB_AUTHORITY_INVALID = "PUB_AUTHORITY_INVALID"
    PUB_BINDING_MISMATCH = "PUB_BINDING_MISMATCH"
    PUB_GOLDEN_MISMATCH = "PUB_GOLDEN_MISMATCH"
    PUB_HOSTILE_INVENTORY_MISMATCH = "PUB_HOSTILE_INVENTORY_MISMATCH"
    PUB_RUN_ORIGIN_INVALID = "PUB_RUN_ORIGIN_INVALID"
    PUB_RECOMPUTATION_MISMATCH = "PUB_RECOMPUTATION_MISMATCH"
    PUB_PRIVATE_PUBLIC_SEPARATION = "PUB_PRIVATE_PUBLIC_SEPARATION"
    PUB_CANONICALIZATION = "PUB_CANONICALIZATION"
    PUB_PUBLIC_SIZE_EXCEEDED = "PUB_PUBLIC_SIZE_EXCEEDED"
    PUB_PRIVATE_SIZE_EXCEEDED = "PUB_PRIVATE_SIZE_EXCEEDED"
    PUB_POSTMUTATION = "PUB_POSTMUTATION"
    INTERNAL_ERROR = "INTERNAL_ERROR"


_ERROR_MESSAGES = MappingProxyType(
    {
        PublicationPreparationCode.PUB_INPUT_TYPE: (
            "publication preparation input is invalid"
        ),
        PublicationPreparationCode.PUB_INPUT_SCHEMA: (
            "publication preparation schema is invalid"
        ),
        PublicationPreparationCode.PUB_INPUT_RESOURCE: (
            "publication preparation input exceeds a resource ceiling"
        ),
        PublicationPreparationCode.PUB_ID_NOT_ALLOWLISTED: (
            "publication value is not in its public-ID category"
        ),
        PublicationPreparationCode.PUB_AUTHORITY_INVALID: (
            "publication authority is invalid"
        ),
        PublicationPreparationCode.PUB_BINDING_MISMATCH: (
            "publication binding bytes do not match their typed origin"
        ),
        PublicationPreparationCode.PUB_GOLDEN_MISMATCH: (
            "independent golden evidence does not match"
        ),
        PublicationPreparationCode.PUB_HOSTILE_INVENTORY_MISMATCH: (
            "hostile control inventory does not match approved authority"
        ),
        PublicationPreparationCode.PUB_RUN_ORIGIN_INVALID: (
            "detached conformance run origin is invalid"
        ),
        PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH: (
            "publication preparation recomputation does not match"
        ),
        PublicationPreparationCode.PUB_PRIVATE_PUBLIC_SEPARATION: (
            "private material reached a public publication artifact"
        ),
        PublicationPreparationCode.PUB_CANONICALIZATION: (
            "publication artifact could not be encoded canonically"
        ),
        PublicationPreparationCode.PUB_PUBLIC_SIZE_EXCEEDED: (
            "public publication bytes exceed their resource ceiling"
        ),
        PublicationPreparationCode.PUB_PRIVATE_SIZE_EXCEEDED: (
            "private publication bytes exceed their resource ceiling"
        ),
        PublicationPreparationCode.PUB_POSTMUTATION: (
            "publication input changed during preparation"
        ),
        PublicationPreparationCode.INTERNAL_ERROR: (
            "publication preparation failed internally"
        ),
    }
)


class PublicationPreparationError(ValueError):
    """One interpolation-free preparation failure with a stable code."""

    def __init__(self, code: PublicationPreparationCode) -> None:
        if type(code) is not PublicationPreparationCode:
            raise TypeError("publication preparation code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: PublicationPreparationCode) -> None:
    raise PublicationPreparationError(code) from None


def _plain_sha256(value: bytes) -> str:
    if type(value) is not bytes:
        _fail(PublicationPreparationCode.PUB_INPUT_TYPE)
    return hashlib.sha256(value).hexdigest()


def _domain_sha256(domain: str, value: bytes) -> str:
    try:
        return _payloads.domain_separated_sha256(domain, value)
    except Exception:
        _fail(PublicationPreparationCode.PUB_CANONICALIZATION)


def _canonical_bytes(
    tree: object,
    *,
    maximum: int,
    size_code: PublicationPreparationCode,
) -> bytes:
    try:
        return _payloads._canonical_tree_bytes(
            tree,
            maximum_encoded_bytes=maximum,
        )
    except _payloads.PublicationPayloadError:
        _fail(size_code)
    except Exception:
        _fail(PublicationPreparationCode.PUB_CANONICALIZATION)


def _wrapped(value: object, *, expected_domain: str) -> dict:
    try:
        return _payloads.canonical_payload_wrapper(
            value,
            expected_domain=expected_domain,
        )
    except Exception:
        _fail(PublicationPreparationCode.PUB_CANONICALIZATION)


def _raw(value: object) -> dict:
    try:
        return _payloads.raw_byte_object(value)
    except Exception:
        _fail(PublicationPreparationCode.PUB_CANONICALIZATION)


def _single_registry_value(values: Tuple[str, ...]) -> str:
    if type(values) is not tuple or len(values) != 1:
        _fail(PublicationPreparationCode.PUB_INPUT_SCHEMA)
    return values[0]


def _registry_words(value: PublicIdentifierRegistryV1) -> frozenset:
    words = set()
    for name in PublicIdentifierRegistryV1.__dataclass_fields__:
        category = getattr(value, name)
        if name == "adapter_identities":
            for identity in category:
                words.add(identity.adapter_id)
                words.add(identity.adapter_version)
        else:
            words.update(category)
    return frozenset(words)


def _binding_tree(frozen: FrozenPublicationInputV1) -> dict:
    bindings = frozen.bindings
    registry_payload = _payloads.public_identifier_registry_payload(
        frozen.public_ids
    )
    if registry_payload.canonical_json_bytes != bindings.public_id_registry_bytes:
        _fail(PublicationPreparationCode.PUB_BINDING_MISMATCH)
    if registry_payload.payload_sha256 != _domain_sha256(
        _payloads.PUBLIC_ID_REGISTRY_DIGEST_DOMAIN,
        bindings.public_id_registry_bytes,
    ):
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)

    guard_manifest_payload = _payloads.execution_guard_run_manifest_payload(
        frozen.execution_guard.run_manifest
    )
    if (
        guard_manifest_payload.canonical_json_bytes
        != frozen.execution_guard.run_manifest_bytes
    ):
        _fail(PublicationPreparationCode.PUB_BINDING_MISMATCH)

    return {
        "a9_1_sha256": _plain_sha256(bindings.a9_1_bytes),
        "contract_core_sha256": _plain_sha256(
            bindings.contract_core_bytes
        ),
        "contract_id": _single_registry_value(
            frozen.public_ids.contract_ids
        ),
        "dependency_lock_sha256": _plain_sha256(
            bindings.dependency_lock_bytes
        ),
        "environment_manifest_sha256": _plain_sha256(
            bindings.environment_manifest_bytes
        ),
        "execution_guard_source_sha256": _plain_sha256(
            bindings.execution_guard_source_bytes
        ),
        "gate_id": _single_registry_value(frozen.public_ids.gate_ids),
        "gate_spec_sha256": _plain_sha256(bindings.gate_spec_bytes),
        "interpreter_executable_sha256": _plain_sha256(
            bindings.interpreter_executable_bytes
        ),
        "oracle_registry_sha256": _plain_sha256(
            bindings.oracle_registry_bytes
        ),
        "phase_c_report_sha256": _plain_sha256(
            bindings.phase_c_report_bytes
        ),
        "phase_d_spec_sha256": _plain_sha256(bindings.phase_d_spec_bytes),
        "public_id_registry_sha256": registry_payload.payload_sha256,
        "publisher_source_sha256": _plain_sha256(
            bindings.publisher_source_bytes
        ),
        "source_tree_archive_sha256": _plain_sha256(
            bindings.source_tree_archive_bytes
        ),
        "source_tree_manifest_sha256": _plain_sha256(
            bindings.source_tree_manifest_bytes
        ),
        "test_inventory_sha256": _domain_sha256(
            TEST_INVENTORY_DIGEST_DOMAIN,
            bindings.test_inventory_bytes,
        ),
        "verifier_source_sha256": _plain_sha256(
            bindings.verifier_source_bytes
        ),
    }


def _capability_ids(case: FrozenDetachedCaseV1) -> list:
    capabilities = case.descriptor.capabilities
    return sorted(
        name
        for name in _CAPABILITY_FIELDS
        if getattr(capabilities, name)
    )


def _adapter_records(cases: Tuple[FrozenDetachedCaseV1, ...]) -> list:
    by_identity = {}
    for case in cases:
        descriptor = case.descriptor
        identity = descriptor.identity
        schema_sha256 = _contract.feature_schema_digest(
            case.complete_sample.sample.configuration.schema
        )
        record = {
            "adapter_id": identity.adapter_id,
            "adapter_version": identity.adapter_version,
            "capability_ids": _capability_ids(case),
            "descriptor_sha256": descriptor.descriptor_sha256,
            "multiplicity_mode_id": (
                descriptor.capabilities.multiplicity_mode.value
            ),
            "policy_sha256": identity.policy_sha256,
            "representation_ids": list(
                descriptor.capabilities.supported_representation_ids
            ),
            "schema_sha256": schema_sha256,
            "time_measure_id": descriptor.capabilities.time_measure.value,
        }
        key = (identity.adapter_id, identity.adapter_version)
        previous = by_identity.get(key)
        if previous is not None and previous != record:
            _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
        by_identity[key] = record
    records = list(by_identity.values())
    records.sort(
        key=lambda value: (
            value["adapter_id"],
            value["adapter_version"],
            value["descriptor_sha256"],
        )
    )
    return records


def _case_public_record(case: FrozenDetachedCaseV1) -> dict:
    run = case.conformance_run
    run_payload = _payloads.conformance_run_payload(run)
    return {
        "adapter_id": run.adapter_id,
        "adapter_version": run.adapter_version,
        "checks": [
            {
                "check_id": record.check_id,
                "plan_mode_id": record.plan_mode.value,
                "reason_code": (
                    "NONE" if record.reason is None else record.reason
                ),
                "representation_id": (
                    "NONE"
                    if record.representation_id is None
                    else record.representation_id
                ),
                "status_id": record.status.value,
            }
            for record in run.records
        ],
        "conformance_run_sha256": run_payload.payload_sha256,
        "counts": [
            {
                "count_id": "advertised_representations",
                "value": len(
                    case.descriptor.capabilities.supported_representation_ids
                ),
            },
            {
                "count_id": "conformance_checks",
                "value": len(run.records),
            },
        ],
        "expected_evidence_sha256": run.expected_evidence_sha256,
        "native_observation_sha256": run.native_observation_sha256,
        "sample_root_sha256": run.sample_root_sha256,
        "source_sha256": _plain_sha256(case.source_bytes),
        "split_manifest_sha256": run.split_manifest_sha256,
    }


def _hostile_public_records(frozen: FrozenPublicationInputV1) -> list:
    return [
        {
            "control_id": value.control_id,
            "error_code": value.error_code,
            "input_sha256": _domain_sha256(
                HOSTILE_CONTROL_INPUT_DIGEST_DOMAIN,
                value.input_bytes,
            ),
            "status_id": value.status_id,
            "test_node_sha256": _domain_sha256(
                HOSTILE_CONTROL_TEST_NODE_DIGEST_DOMAIN,
                value.test_node_bytes,
            ),
        }
        for value in frozen.hostile_controls
    ]


def _resource_records(frozen: FrozenPublicationInputV1) -> list:
    receipt = frozen.execution_guard.receipt
    if receipt.wall_limit_triggered:
        wall_status = "ceiling_triggered"
    elif (
        receipt.elapsed_monotonic_nanoseconds
        > receipt.wall_time_limit_nanoseconds
    ):
        wall_status = "observed_above_ceiling"
    else:
        wall_status = "observed_within_ceiling_noncertifying"
    wall = {
        "ceiling": receipt.wall_time_limit_nanoseconds,
        "decision_eligible": False,
        "execution_status_id": receipt.status.value,
        "measurement_method_id": receipt.clock_method.value,
        "resource_id": "elapsed_wall_nanoseconds",
        "resource_status_id": wall_status,
        "unit_id": "nanoseconds",
    }

    measured = receipt.measured_peak_rss_bytes
    if receipt.peak_rss_limit_triggered:
        rss_status = "ceiling_triggered"
    elif measured is None:
        rss_status = "observation_unavailable"
    elif measured > receipt.peak_rss_limit_bytes:
        rss_status = "observed_above_ceiling"
    elif (
        not receipt.peak_rss_enforcement_exact
        or not receipt.peak_rss_observation_finalized
    ):
        rss_status = "observed_within_ceiling_noncertifying"
    else:
        rss_status = "observed_within_ceiling"
    rss = {
        "ceiling": receipt.peak_rss_limit_bytes,
        "decision_eligible": False,
        "execution_status_id": receipt.status.value,
        "measurement_method_id": receipt.peak_rss_method.value,
        "resource_id": "peak_rss_bytes",
        "resource_status_id": rss_status,
        "unit_id": "bytes",
    }
    return [wall, rss]


def _public_core_tree(
    frozen: FrozenPublicationInputV1,
    bindings: dict,
) -> dict:
    return {
        "adapters": _adapter_records(frozen.cases),
        "artifact_type": PUBLIC_CORE_ARTIFACT_TYPE,
        "bindings": bindings,
        "cases": [_case_public_record(case) for case in frozen.cases],
        "claim_boundary": {
            "allowed_claim_ids": list(frozen.public_ids.allowed_claim_ids),
            "blocked_claim_ids": list(frozen.public_ids.blocked_claim_ids),
            "claim_boundary_id": _single_registry_value(
                frozen.public_ids.claim_boundary_ids
            ),
        },
        "decision_status": PUBLICATION_DECISION_STATUS,
        "development_status": PUBLICATION_DEVELOPMENT_STATUS,
        "format_version": "1",
        "hostile_controls": _hostile_public_records(frozen),
        "resource_receipts": _resource_records(frozen),
    }


def _leaf_payloads(case: FrozenDetachedCaseV1) -> Tuple[dict, dict]:
    complete = case.complete_sample
    expected = case.expected_evidence
    adapted_payloads = {
        "coverage_ledger": _payloads.coverage_ledger_payload(
            complete.coverage
        ),
        "detached_native_observation": (
            _payloads.detached_native_observation_payload(
                complete.sample.configuration
            )
        ),
        "evaluation_labels": _payloads.evaluation_labels_payload(
            complete.evaluation_labels
        ),
        "fitted_state": _payloads.fitted_state_payload(
            complete.fitted_state
        ),
        "identity_bearing_native_configuration": (
            _payloads.identity_bearing_native_configuration_payload(
                complete.sample.configuration
            )
        ),
        "private_provenance": _payloads.private_provenance_payload(
            complete.provenance
        ),
        "semantic_reconstruction": (
            _payloads.semantic_reconstruction_payload(
                complete.reconstruction
            )
        ),
        "source_inventory": _payloads.source_inventory_payload(
            complete.inventory
        ),
        "static_context": _payloads.static_context_payload(
            complete.static_context
        ),
    }
    expected_payloads = {
        "coverage_ledger": _payloads.coverage_ledger_payload(
            expected.coverage
        ),
        "detached_native_observation": (
            _payloads.detached_native_observation_payload(
                case.expected_configuration
            )
        ),
        "evaluation_labels": _payloads.evaluation_labels_payload(
            expected.evaluation_labels
        ),
        "fitted_state": _payloads.fitted_state_payload(
            expected.fitted_state
        ),
        "identity_bearing_native_configuration": (
            _payloads.identity_bearing_native_configuration_payload(
                case.expected_configuration
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
    for name in adapted_payloads:
        adapted = adapted_payloads[name]
        expected_value = expected_payloads[name]
        if (
            adapted.canonical_json_bytes
            != expected_value.canonical_json_bytes
            or adapted.payload_sha256 != expected_value.payload_sha256
        ):
            _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    return adapted_payloads, expected_payloads


def _wrapped_leaf_set(values: dict) -> dict:
    domains = {
        "coverage_ledger": _payloads.PRIVATE_COVERAGE_LEDGER_DIGEST_DOMAIN,
        "detached_native_observation": (
            _contract.NATIVE_OBSERVATION_DIGEST_DOMAIN
        ),
        "evaluation_labels": (
            _payloads.PRIVATE_EVALUATION_LABELS_DIGEST_DOMAIN
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
        "source_inventory": _payloads.PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN,
        "static_context": _payloads.PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN,
    }
    return {
        name: _wrapped(values[name], expected_domain=domains[name])
        for name in (
            "coverage_ledger",
            "detached_native_observation",
            "evaluation_labels",
            "fitted_state",
            "identity_bearing_native_configuration",
            "private_provenance",
            "semantic_reconstruction",
            "source_inventory",
            "static_context",
        )
    }


def _private_case_record(
    case: FrozenDetachedCaseV1,
    *,
    ordinal: int,
) -> dict:
    adapted_payloads, expected_payloads = _leaf_payloads(case)
    complete = case.complete_sample
    adapted = {
        "adapter_descriptor": _wrapped(
            _payloads.adapter_descriptor_payload(case.descriptor),
            expected_domain=_contract.DESCRIPTOR_DIGEST_DOMAIN,
        ),
        "adapter_manifest": _wrapped(
            _payloads.adapter_manifest_payload(complete.sample.manifest),
            expected_domain=_contract.SAMPLE_MANIFEST_DIGEST_DOMAIN,
        ),
        "complete_sample_commitment": _wrapped(
            _payloads.complete_sample_commitment_payload(
                case.descriptor,
                complete,
            ),
            expected_domain=_payloads.COMPLETE_SAMPLE_DIGEST_DOMAIN,
        ),
        **_wrapped_leaf_set(adapted_payloads),
    }
    raw_reconstruction = _payloads.raw_reconstruction_payload(
        case.descriptor,
        complete,
    )
    if type(raw_reconstruction) is _payloads.RawByteObjectV1:
        adapted["raw_byte_reconstruction"] = _raw(raw_reconstruction)
    elif type(raw_reconstruction) is _payloads.CanonicalPayloadV1:
        adapted["raw_byte_reconstruction"] = _wrapped(
            raw_reconstruction,
            expected_domain=(
                _payloads.RAW_RECONSTRUCTION_ABSENCE_DIGEST_DOMAIN
            ),
        )
    else:  # pragma: no cover - typed projection invariant
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)

    expected = {
        **_wrapped_leaf_set(expected_payloads),
        "expected_evidence_commitment": _wrapped(
            _payloads.expected_evidence_payload(case.expected_evidence),
            expected_domain=_evidence.EXPECTED_EVIDENCE_DIGEST_DOMAIN,
        ),
    }
    return {
        "adapted": adapted,
        "case_ordinal": ordinal,
        "expected": expected,
        "golden_case": _wrapped(
            _payloads.independent_golden_case_payload(
                case.independent_golden_definition_bytes
            ),
            expected_domain=_payloads.INDEPENDENT_GOLDEN_CASE_DIGEST_DOMAIN,
        ),
        "partition": _wrapped(
            _payloads.partition_payload(complete.sample.manifest.partition),
            expected_domain=_payloads.PRIVATE_PARTITION_DIGEST_DOMAIN,
        ),
        "run_receipt": _wrapped(
            _payloads.conformance_run_payload(case.conformance_run),
            expected_domain=_payloads.CONFORMANCE_RUN_DIGEST_DOMAIN,
        ),
        "source": _raw(_payloads.source_bytes_payload(case.source_bytes)),
        "split_manifest": _wrapped(
            _payloads.split_manifest_payload(case.split_manifest),
            expected_domain=_contract.SPLIT_MANIFEST_DIGEST_DOMAIN,
        ),
    }


def _private_envelope_tree(
    frozen: FrozenPublicationInputV1,
    *,
    binding_set_sha256: str,
    public_core_sha256: str,
) -> dict:
    guard_manifest = _payloads.execution_guard_run_manifest_payload(
        frozen.execution_guard.run_manifest
    )
    if (
        guard_manifest.canonical_json_bytes
        != frozen.execution_guard.run_manifest_bytes
    ):
        _fail(PublicationPreparationCode.PUB_BINDING_MISMATCH)
    return {
        "artifact_type": PRIVATE_ENVELOPE_ARTIFACT_TYPE,
        "binding_set_sha256": binding_set_sha256,
        "cases": [
            _private_case_record(case, ordinal=index)
            for index, case in enumerate(frozen.cases)
        ],
        "execution_guard_receipt": _wrapped(
            _payloads.execution_guard_receipt_payload(
                frozen.execution_guard.receipt
            ),
            expected_domain=_payloads.EXECUTION_GUARD_RECEIPT_DIGEST_DOMAIN,
        ),
        "execution_guard_run_manifest": _wrapped(
            guard_manifest,
            expected_domain=(
                _payloads.EXECUTION_GUARD_RUN_MANIFEST_DIGEST_DOMAIN
            ),
        ),
        "format_version": "1",
        "hostile_control_receipts": [
            _wrapped(
                _payloads.hostile_control_receipt_payload(value),
                expected_domain=(
                    _payloads.HOSTILE_CONTROL_RECEIPT_DIGEST_DOMAIN
                ),
            )
            for value in frozen.hostile_controls
        ],
        "public_core_sha256": public_core_sha256,
    }


def _decoded_private_payload_bytes(case: FrozenDetachedCaseV1) -> int:
    def leaf_bytes(evidence: object) -> int:
        total = sum(
            len(item.canonical_item_bytes) for item in evidence.inventory.items
        )
        total += sum(
            len(item.canonical_payload_bytes)
            for item in evidence.static_context.entries
        )
        total += sum(
            len(item.canonical_payload_bytes)
            for item in evidence.evaluation_labels.entries
        )
        total += sum(
            len(item.private_payload_bytes)
            for item in evidence.provenance.entries
        )
        if evidence.fitted_state is not None:
            total += len(evidence.fitted_state.fit_configuration_bytes)
            total += len(evidence.fitted_state.parameter_bytes)
        total += len(evidence.reconstruction.canonical_payload_bytes)
        return total

    result = len(case.source_bytes)
    result += len(case.independent_golden_definition_bytes)
    result += leaf_bytes(case.complete_sample)
    result += leaf_bytes(case.expected_evidence)
    if case.complete_sample.raw_reconstruction_bytes is not None:
        result += len(case.complete_sample.raw_reconstruction_bytes)
    return result


def _preflight_private_envelope(frozen: FrozenPublicationInputV1) -> None:
    minimum_payload_bytes = sum(
        _decoded_private_payload_bytes(case) for case in frozen.cases
    )
    if minimum_payload_bytes > MAXIMUM_PRIVATE_ARTIFACT_BYTES:
        _fail(PublicationPreparationCode.PUB_PRIVATE_SIZE_EXCEEDED)


def _private_text_tokens(case: FrozenDetachedCaseV1) -> Iterable[str]:
    configuration = case.complete_sample.sample.configuration
    manifest = case.complete_sample.sample.manifest
    yield manifest.partition.sample_id
    yield manifest.partition.group_id
    for entry in case.split_manifest.entries:
        yield entry.sample_id
        yield entry.group_id
    for event in configuration.events:
        event_id = event.event_id
        if type(event_id) is str:
            yield event_id
        elif type(event_id) is tuple:
            for component in event_id:
                if type(component) is str:
                    yield component
    for evidence in (case.complete_sample, case.expected_evidence):
        for item in evidence.inventory.items:
            yield item.item_key
        for entry in evidence.coverage.entries:
            yield entry.item_key
            if entry.target_key is not None:
                yield entry.target_key
        for entry in evidence.static_context.entries:
            yield entry.entry_key
        for entry in evidence.evaluation_labels.entries:
            yield entry.entry_key
        for entry in evidence.provenance.entries:
            yield entry.provenance_key
            for key in entry.source_item_keys:
                yield key


def _sentinel_check(
    frozen: FrozenPublicationInputV1,
    public_core_tree: dict,
    public_core_bytes: bytes,
    manifest_tree: dict,
    manifest_bytes: bytes,
) -> None:
    public_words = _registry_words(frozen.public_ids)

    def public_digests(tree: object) -> set:
        digests = set()
        stack = [tree]
        while stack:
            value = stack.pop()
            if type(value) is list:
                stack.extend(value)
            elif type(value) is dict:
                for key, item in value.items():
                    if key.endswith("_sha256") and type(item) is str:
                        digests.add(item)
                    else:
                        stack.append(item)
        return digests

    admitted_digest_values = public_digests(public_core_tree)
    admitted_digest_values.update(public_digests(manifest_tree))
    for case in frozen.cases:
        for token in _private_text_tokens(case):
            if token in public_words or token in admitted_digest_values:
                continue
            try:
                encoded = _payloads._canonical_tree_bytes(
                    token,
                    maximum_encoded_bytes=4096,
                )
            except Exception:
                _fail(PublicationPreparationCode.PUB_INPUT_SCHEMA)
            if encoded in public_core_bytes or encoded in manifest_bytes:
                _fail(
                    PublicationPreparationCode.PUB_PRIVATE_PUBLIC_SEPARATION
                )


def _manifest_tree(
    *,
    public_core_bytes: bytes,
    public_core_sha256: str,
    private_envelope_bytes: bytes,
    private_envelope_sha256: str,
) -> dict:
    return {
        "artifact_type": PUBLICATION_MANIFEST_ARTIFACT_TYPE,
        "artifacts": [
            {
                "artifact_id": PUBLIC_CORE_ARTIFACT_ID,
                "content_sha256": public_core_sha256,
                "encoded_byte_count": len(public_core_bytes),
                "file_sha256": _plain_sha256(public_core_bytes),
                "visibility_id": "PUBLIC",
            },
            {
                "artifact_id": PRIVATE_ENVELOPE_ARTIFACT_ID,
                "content_sha256": private_envelope_sha256,
                "encoded_byte_count": len(private_envelope_bytes),
                "file_sha256": _plain_sha256(private_envelope_bytes),
                "visibility_id": "PRIVATE_OWNER_ONLY",
            },
        ],
        "decision_status": PUBLICATION_DECISION_STATUS,
        "format_version": "1",
        "private_envelope_sha256": private_envelope_sha256,
        "public_core_sha256": public_core_sha256,
    }


def _build_prepared(frozen: FrozenPublicationInputV1) -> PreparedPublicationV1:
    _preflight_private_envelope(frozen)
    bindings = _binding_tree(frozen)
    binding_bytes = _canonical_bytes(
        bindings,
        maximum=MAXIMUM_PUBLIC_ARTIFACT_BYTES,
        size_code=PublicationPreparationCode.PUB_PUBLIC_SIZE_EXCEEDED,
    )
    binding_set_sha256 = _domain_sha256(
        PUBLICATION_BINDINGS_DIGEST_DOMAIN,
        binding_bytes,
    )

    public_core_tree = _public_core_tree(frozen, bindings)
    public_core_bytes = _canonical_bytes(
        public_core_tree,
        maximum=MAXIMUM_PUBLIC_ARTIFACT_BYTES,
        size_code=PublicationPreparationCode.PUB_PUBLIC_SIZE_EXCEEDED,
    )
    public_core_sha256 = _domain_sha256(
        PUBLIC_CORE_DIGEST_DOMAIN,
        public_core_bytes,
    )

    try:
        private_tree = _private_envelope_tree(
            frozen,
            binding_set_sha256=binding_set_sha256,
            public_core_sha256=public_core_sha256,
        )
        private_envelope_bytes = _payloads._canonical_tree_bytes(
            private_tree,
            maximum_encoded_bytes=MAXIMUM_PRIVATE_ARTIFACT_BYTES,
        )
    except PublicationPreparationError:
        raise
    except _payloads.PublicationPayloadError:
        _fail(PublicationPreparationCode.PUB_PRIVATE_SIZE_EXCEEDED)
    except Exception:
        _fail(PublicationPreparationCode.PUB_CANONICALIZATION)
    private_envelope_sha256 = _domain_sha256(
        PRIVATE_ENVELOPE_DIGEST_DOMAIN,
        private_envelope_bytes,
    )

    manifest_tree = _manifest_tree(
        public_core_bytes=public_core_bytes,
        public_core_sha256=public_core_sha256,
        private_envelope_bytes=private_envelope_bytes,
        private_envelope_sha256=private_envelope_sha256,
    )
    try:
        manifest_bytes = _payloads._canonical_tree_bytes(
            manifest_tree,
            maximum_encoded_bytes=MAXIMUM_PUBLIC_ARTIFACT_BYTES,
        )
    except _payloads.PublicationPayloadError:
        _fail(PublicationPreparationCode.PUB_PUBLIC_SIZE_EXCEEDED)
    except Exception:
        _fail(PublicationPreparationCode.PUB_CANONICALIZATION)
    if len(public_core_bytes) + len(manifest_bytes) > (
        MAXIMUM_PUBLIC_ARTIFACT_BYTES
    ):
        _fail(PublicationPreparationCode.PUB_PUBLIC_SIZE_EXCEEDED)
    _sentinel_check(
        frozen,
        public_core_tree,
        public_core_bytes,
        manifest_tree,
        manifest_bytes,
    )
    manifest_sha256 = _domain_sha256(
        PUBLICATION_MANIFEST_DIGEST_DOMAIN,
        manifest_bytes,
    )
    return PreparedPublicationV1(
        public_core_bytes=public_core_bytes,
        private_envelope_bytes=private_envelope_bytes,
        manifest_bytes=manifest_bytes,
        public_core_sha256=public_core_sha256,
        private_envelope_sha256=private_envelope_sha256,
        manifest_sha256=manifest_sha256,
        public_core_file_sha256=_plain_sha256(public_core_bytes),
        private_envelope_file_sha256=_plain_sha256(private_envelope_bytes),
        manifest_file_sha256=_plain_sha256(manifest_bytes),
    )


def prepare_publication(request: PublicationRequestV1) -> PreparedPublicationV1:
    """Return exact artifact bytes without writing or deciding the gate."""

    if type(request) is not PublicationRequestV1:
        _fail(PublicationPreparationCode.PUB_INPUT_TYPE)
    before = freeze_publication_input(request)
    try:
        prepared = _build_prepared(before)
    except PublicationPreparationError:
        raise
    except _payloads.PublicationPayloadError:
        _fail(PublicationPreparationCode.PUB_CANONICALIZATION)
    except (TypeError, ValueError):
        _fail(PublicationPreparationCode.PUB_INPUT_SCHEMA)
    except Exception:
        _fail(PublicationPreparationCode.INTERNAL_ERROR)
    try:
        after = freeze_publication_input(request)
    except PublicationFreezeError:
        _fail(PublicationPreparationCode.PUB_POSTMUTATION)
    except Exception:
        _fail(PublicationPreparationCode.PUB_POSTMUTATION)
    if after != before:
        _fail(PublicationPreparationCode.PUB_POSTMUTATION)
    try:
        rebuilt = _build_prepared(after)
    except PublicationPreparationError:
        raise
    except _payloads.PublicationPayloadError:
        _fail(PublicationPreparationCode.PUB_CANONICALIZATION)
    except (TypeError, ValueError):
        _fail(PublicationPreparationCode.PUB_INPUT_SCHEMA)
    except Exception:
        _fail(PublicationPreparationCode.INTERNAL_ERROR)
    if rebuilt != prepared:
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    return prepared


__all__ = [
    "PRIVATE_ENVELOPE_DIGEST_DOMAIN",
    "PUBLICATION_BINDINGS_DIGEST_DOMAIN",
    "PUBLICATION_MANIFEST_DIGEST_DOMAIN",
    "PUBLICATION_PREPARATION_IMPLEMENTATION_STATUS",
    "PUBLIC_CORE_DIGEST_DOMAIN",
    "PublicationPreparationCode",
    "PublicationPreparationError",
    "TEST_INVENTORY_DIGEST_DOMAIN",
    "prepare_publication",
]
