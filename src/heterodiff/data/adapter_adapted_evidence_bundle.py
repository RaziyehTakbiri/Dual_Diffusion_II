"""Adapter-return capture and deterministic private bundle production.

The bundle producer in this module is write-free.  It snapshots one exact
output-blind case input, adapter descriptor, and complete adapted sample, then
serializes the actual adapter-side preimages with the existing typed publisher
projections.  The local runner obtains that complete sample from one direct
``adapt_complete`` call site; it has no direct ``adapt`` call and never
accepts a caller-supplied complete sample.

This boundary establishes only call-time method-return capture and structural
self-consistency.  It cannot determine whether adapter internals recomputed
the return or served a cached object.  The
self-derived ``ExpectedAdapterEvidence`` passed to the shared conformance
runner is not an independent oracle.  In-process protocol inspection and
callbacks do not enforce an output-blind child, prevent access through globals
or closures, load a measured adapter source closure, attest execution or
containment, establish semantic truth, make a publication decision, or support
a generalization claim.  Those claims remain explicitly false in the local
result.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from types import MappingProxyType
from typing import Tuple

from . import adapter_adapted_evidence_bundle_verifier as _bundle_verifier
from . import adapter_contract as _contract
from . import adapter_evidence as _evidence
from . import adapter_publication_payloads as _payloads
from .adapter_complete_protocol import CompleteEvidenceAdapterV1
from .adapter_conformance_runner import (
    ConformanceRun,
    run_complete_adapter_conformance,
)
from .adapter_output_blind_case_input import (
    ActualAdapterCaseInputV1,
    PreparedOutputBlindCaseInputV1,
    build_output_blind_case_input_v1,
    validate_prepared_output_blind_case_input_v1,
)


ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE = (
    "heterodiff.adapter.adapted-evidence-bundle.v1"
)
ADAPTED_EVIDENCE_BUNDLE_DIGEST_DOMAIN = (
    ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE
)
MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES = 32 * 1024 * 1024


class AdaptedEvidenceBundleCode(str, Enum):
    """Closed failures for production and local return capture."""

    INPUT_TYPE = "ADAPTED_EVIDENCE_INPUT_TYPE"
    INPUT_PREPARATION = "ADAPTED_EVIDENCE_INPUT_PREPARATION"
    REASON_REGISTRY = "ADAPTED_EVIDENCE_REASON_REGISTRY"
    ADAPTER_PROTOCOL = "ADAPTED_EVIDENCE_ADAPTER_PROTOCOL"
    ADAPTER_SNAPSHOT = "ADAPTED_EVIDENCE_ADAPTER_SNAPSHOT"
    ADAPTER_EXECUTION = "ADAPTED_EVIDENCE_ADAPTER_EXECUTION"
    ADAPTER_OUTPUT = "ADAPTED_EVIDENCE_ADAPTER_OUTPUT"
    SELF_CONFORMANCE = "ADAPTED_EVIDENCE_SELF_CONFORMANCE"
    POSTMUTATION = "ADAPTED_EVIDENCE_POSTMUTATION"
    BINDING = "ADAPTED_EVIDENCE_BINDING"
    RESOURCE_LIMIT = "ADAPTED_EVIDENCE_RESOURCE_LIMIT"
    INTERNAL = "ADAPTED_EVIDENCE_INTERNAL"


_ERROR_MESSAGES = MappingProxyType(
    {
        AdaptedEvidenceBundleCode.INPUT_TYPE: (
            "adapted-evidence input has an invalid exact type"
        ),
        AdaptedEvidenceBundleCode.INPUT_PREPARATION: (
            "output-blind case input preparation did not complete"
        ),
        AdaptedEvidenceBundleCode.REASON_REGISTRY: (
            "adapted-evidence reason registry has an invalid frozen shape"
        ),
        AdaptedEvidenceBundleCode.ADAPTER_PROTOCOL: (
            "adapter does not satisfy the complete-evidence protocol"
        ),
        AdaptedEvidenceBundleCode.ADAPTER_SNAPSHOT: (
            "adapter descriptor snapshot did not complete"
        ),
        AdaptedEvidenceBundleCode.ADAPTER_EXECUTION: (
            "adapter complete-evidence execution did not complete"
        ),
        AdaptedEvidenceBundleCode.ADAPTER_OUTPUT: (
            "adapter complete-evidence output has an invalid exact shape"
        ),
        AdaptedEvidenceBundleCode.SELF_CONFORMANCE: (
            "captured adapted evidence failed local self-consistency conformance"
        ),
        AdaptedEvidenceBundleCode.POSTMUTATION: (
            "adapted-evidence input or output changed during local execution"
        ),
        AdaptedEvidenceBundleCode.BINDING: (
            "adapted-evidence case, descriptor, manifest, or leaves disagree"
        ),
        AdaptedEvidenceBundleCode.RESOURCE_LIMIT: (
            "adapted-evidence bundle exceeds its frozen resource bound"
        ),
        AdaptedEvidenceBundleCode.INTERNAL: (
            "adapted-evidence processing failed internally"
        ),
    }
)


class AdaptedEvidenceBundleError(ValueError):
    """One fixed, coded failure that never reflects adapter-controlled text."""

    def __init__(self, code: AdaptedEvidenceBundleCode) -> None:
        if type(code) is not AdaptedEvidenceBundleCode:
            raise TypeError("adapted-evidence error code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: AdaptedEvidenceBundleCode) -> None:
    raise AdaptedEvidenceBundleError(code) from None


def _domain_separated_sha256(domain: str, payload: bytes) -> str:
    if type(domain) is not str or type(payload) is not bytes:
        raise TypeError("adapted-evidence digest inputs must have exact types")
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except UnicodeError:
        raise TypeError("adapted-evidence digest domain must be ASCII") from None
    if not domain_bytes or len(domain_bytes) > 256 or b"\x00" in domain_bytes:
        raise ValueError("adapted-evidence digest domain is outside its bound")
    if len(payload) > MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES:
        raise ValueError("adapted-evidence digest payload exceeds its bound")
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def adapted_evidence_bundle_sha256(bundle_bytes: bytes) -> str:
    """Return the bundle-domain digest of exact bounded canonical bytes."""

    if type(bundle_bytes) is not bytes:
        raise TypeError("bundle_bytes must be exact immutable bytes")
    if (
        not bundle_bytes
        or len(bundle_bytes) > MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES
    ):
        raise ValueError("bundle_bytes are outside the adapted bundle bound")
    return _domain_separated_sha256(
        ADAPTED_EVIDENCE_BUNDLE_DIGEST_DOMAIN,
        bundle_bytes,
    )


@dataclass(frozen=True)
class AdaptedEvidenceBundleResultV1:
    """Exact canonical bundle transport with one domain-separated digest."""

    bundle_bytes: bytes
    bundle_byte_count: int
    bundle_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not AdaptedEvidenceBundleResultV1:
            raise TypeError("adapted-evidence bundle result must be exact")
        if type(self.bundle_bytes) is not bytes or not self.bundle_bytes:
            raise TypeError("bundle_bytes must be nonempty exact bytes")
        if type(self.bundle_byte_count) is not int:
            raise TypeError("bundle_byte_count must be an exact integer")
        if (
            self.bundle_byte_count != len(self.bundle_bytes)
            or self.bundle_byte_count
            > MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES
        ):
            raise ValueError("bundle_byte_count does not match bounded bytes")
        if type(self.bundle_sha256) is not str:
            raise TypeError("bundle_sha256 must be exact text")
        if self.bundle_sha256 != adapted_evidence_bundle_sha256(
            self.bundle_bytes
        ):
            raise ValueError("bundle_sha256 does not match exact bundle bytes")


@dataclass(frozen=True)
class LocalCapturedAdaptedEvidenceResultV1:
    """Narrow local method-return result with frozen claims and nonclaims."""

    prepared_case_input: PreparedOutputBlindCaseInputV1
    conformance_run: ConformanceRun
    adapted_evidence_bundle: AdaptedEvidenceBundleResultV1
    allowed_exclusion_reason_codes: Tuple[str, ...]
    allowed_censor_reason_codes: Tuple[str, ...]
    runner_direct_adapt_complete_call_count: int
    runner_direct_adapt_call_count: int
    adapt_complete_preoutput_arguments_supplied: bool
    adapt_complete_return_captured: bool
    self_consistency_conformance_passed: bool
    bundle_built_from_adapt_complete_return: bool
    output_blind_adapter_child_enforced: bool
    expected_material_nonexposure_attested: bool
    adapter_source_loaded: bool
    adapter_source_execution_identity_attested: bool
    execution_attested: bool
    containment_enforced: bool
    containment_attested: bool
    semantic_truth_attested: bool
    decision_made: bool
    generalization_attested: bool

    def __post_init__(self) -> None:
        if type(self) is not LocalCapturedAdaptedEvidenceResultV1:
            raise TypeError("local adapted-evidence result must be exact")
        if type(self.prepared_case_input) is not PreparedOutputBlindCaseInputV1:
            raise TypeError("prepared_case_input must be exact")
        if type(self.conformance_run) is not ConformanceRun:
            raise TypeError("conformance_run must be exact")
        if (
            type(self.adapted_evidence_bundle)
            is not AdaptedEvidenceBundleResultV1
        ):
            raise TypeError("adapted_evidence_bundle must be exact")
        try:
            exclusions = _evidence._validate_reason_codes(
                self.allowed_exclusion_reason_codes,
                name="allowed exclusion reason",
            )
            censors = _evidence._validate_reason_codes(
                self.allowed_censor_reason_codes,
                name="allowed censor reason",
            )
            if len(exclusions) + len(censors) > _evidence.MAXIMUM_REASON_CODES:
                raise ValueError("combined reason registry exceeds its bound")
        except Exception as error:
            raise ValueError(
                "local result reason registries are invalid"
            ) from error
        if self.runner_direct_adapt_complete_call_count != 1 or type(
            self.runner_direct_adapt_complete_call_count
        ) is not int:
            raise ValueError(
                "local runner must directly call adapt_complete exactly once"
            )
        if self.runner_direct_adapt_call_count != 0 or type(
            self.runner_direct_adapt_call_count
        ) is not int:
            raise ValueError("local runner must not directly call adapt")
        true_claims = (
            self.adapt_complete_preoutput_arguments_supplied,
            self.adapt_complete_return_captured,
            self.self_consistency_conformance_passed,
            self.bundle_built_from_adapt_complete_return,
        )
        false_claims = (
            self.output_blind_adapter_child_enforced,
            self.expected_material_nonexposure_attested,
            self.adapter_source_loaded,
            self.adapter_source_execution_identity_attested,
            self.execution_attested,
            self.containment_enforced,
            self.containment_attested,
            self.semantic_truth_attested,
            self.decision_made,
            self.generalization_attested,
        )
        if any(value is not True for value in true_claims):
            raise ValueError("local adapted-evidence consistency claims must be true")
        if any(value is not False for value in false_claims):
            raise ValueError("strong adapted-evidence claims must remain false")
        try:
            prepared = validate_prepared_output_blind_case_input_v1(
                self.prepared_case_input
            )
            AdaptedEvidenceBundleResultV1.__post_init__(
                self.adapted_evidence_bundle
            )
            ConformanceRun.__post_init__(self.conformance_run)
            verified = (
                _bundle_verifier.verify_independent_adapted_evidence_bundle(
                    _bundle_verifier
                    .IndependentAdaptedEvidenceBundleVerificationInputV1(
                        case_input_bytes=prepared.input_bytes,
                        adapted_evidence_bundle_bytes=(
                            self.adapted_evidence_bundle.bundle_bytes
                        ),
                        allowed_exclusion_reason_codes=exclusions,
                        allowed_censor_reason_codes=censors,
                    )
                )
            )
            receipt = verified.receipt
            run = self.conformance_run
            if (
                receipt.case_input_sha256 != prepared.input_sha256
                or receipt.case_input_byte_count != prepared.input_byte_count
                or receipt.adapted_evidence_bundle_sha256
                != self.adapted_evidence_bundle.bundle_sha256
                or receipt.adapted_evidence_bundle_byte_count
                != self.adapted_evidence_bundle.bundle_byte_count
                or receipt.source_byte_count
                != len(prepared.case_input.source_bytes)
                or receipt.adapter_id != run.adapter_id
                or receipt.adapter_version != run.adapter_version
                or receipt.capability_plan_sha256
                != _conformance_plan_sha256(run)
                or receipt.descriptor_sha256 != run.descriptor_sha256
                or receipt.source_sha256 != run.source_sha256
                or receipt.split_manifest_sha256
                != run.split_manifest_sha256
                or receipt.actual_native_observation_sha256
                != run.native_observation_sha256
                or receipt.adapter_manifest_sha256
                != run.sample_root_sha256
                or receipt.actual_evidence_sha256
                != run.expected_evidence_sha256
            ):
                raise ValueError("local result identities differ")
        except Exception as error:
            raise ValueError(
                "local result components do not match raw adapted evidence"
            ) from error


def _validated_prepared_input(
    prepared_case_input: PreparedOutputBlindCaseInputV1,
) -> PreparedOutputBlindCaseInputV1:
    if type(prepared_case_input) is not PreparedOutputBlindCaseInputV1:
        _fail(AdaptedEvidenceBundleCode.INPUT_TYPE)
    try:
        rebuilt = validate_prepared_output_blind_case_input_v1(
            prepared_case_input
        )
    except Exception:
        _fail(AdaptedEvidenceBundleCode.INPUT_PREPARATION)
    if (
        type(rebuilt) is not PreparedOutputBlindCaseInputV1
        or rebuilt != prepared_case_input
    ):
        _fail(AdaptedEvidenceBundleCode.INPUT_PREPARATION)
    return rebuilt


def _snapshot_descriptor(
    descriptor: _contract.AdapterDescriptor,
) -> _contract.AdapterDescriptor:
    if type(descriptor) is not _contract.AdapterDescriptor:
        _fail(AdaptedEvidenceBundleCode.INPUT_TYPE)
    try:
        return _contract._snapshot_descriptor(descriptor)
    except Exception:
        _fail(AdaptedEvidenceBundleCode.BINDING)


def _snapshot_complete(
    complete: _evidence.CompleteAdaptedEventSample,
) -> _evidence.CompleteAdaptedEventSample:
    if type(complete) is not _evidence.CompleteAdaptedEventSample:
        _fail(AdaptedEvidenceBundleCode.INPUT_TYPE)
    try:
        return _evidence._snapshot_complete(complete)
    except _evidence.AdapterEvidenceResourceError:
        _fail(AdaptedEvidenceBundleCode.RESOURCE_LIMIT)
    except Exception:
        _fail(AdaptedEvidenceBundleCode.BINDING)


def _validate_bundle_bindings(
    prepared: PreparedOutputBlindCaseInputV1,
    descriptor: _contract.AdapterDescriptor,
    complete: _evidence.CompleteAdaptedEventSample,
) -> None:
    case_input = prepared.case_input
    if type(case_input) is not ActualAdapterCaseInputV1:
        _fail(AdaptedEvidenceBundleCode.BINDING)
    source_bytes = case_input.source_bytes
    partition = case_input.partition
    split_manifest = case_input.split_manifest
    try:
        split_snapshot = _evidence.snapshot_bounded_split_manifest(
            split_manifest
        )
        manifest = _contract._validate_manifest_shape(
            complete.sample.manifest
        )
        configuration = (
            _evidence.snapshot_bounded_native_configuration(
                complete.sample.configuration
            )
        )
        source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        descriptor_sha256 = _contract.adapter_descriptor_digest(descriptor)
        split_sha256 = _contract.split_manifest_digest(split_snapshot)
        schema_sha256 = _contract.feature_schema_digest(configuration.schema)
        native_sha256 = _contract.native_observation_digest(configuration)
        capabilities = descriptor.capabilities

        if (
            manifest.partition != partition
            or not split_snapshot.contains_exactly(partition)
            or configuration.sample_id != partition.sample_id
            or configuration.group_id != partition.group_id
        ):
            raise ValueError("partition binding mismatch")
        if (
            manifest.source_size_bytes != len(source_bytes)
            or manifest.source_sha256 != source_sha256
            or manifest.split_manifest_sha256 != split_sha256
            or manifest.descriptor_sha256 != descriptor_sha256
        ):
            raise ValueError("external binding mismatch")
        if (
            manifest.schema_sha256 != schema_sha256
            or manifest.schema_version != configuration.schema.version
            or manifest.native_observation_sha256 != native_sha256
            or capabilities.time_measure
            is not configuration.schema.time_measure
            or capabilities.multiplicity_mode
            is not configuration.schema.multiplicity_mode
        ):
            raise ValueError("native binding mismatch")

        _evidence._validate_leaf_source_bindings(
            complete,
            source_sha256=source_sha256,
            source_size_bytes=len(source_bytes),
            policy_sha256=descriptor.identity.policy_sha256,
            schema_sha256=schema_sha256,
            native_sha256=native_sha256,
        )
        leaf_bindings = (
            (
                manifest.static_context_sha256,
                _evidence.static_context_digest(complete.static_context),
            ),
            (
                manifest.evaluation_labels_sha256,
                _evidence.evaluation_labels_digest(
                    complete.evaluation_labels
                ),
            ),
            (
                manifest.coverage_ledger_sha256,
                _evidence.source_coverage_ledger_digest(complete.coverage),
            ),
            (
                manifest.private_provenance_sha256,
                _evidence.private_provenance_digest(complete.provenance),
            ),
            (
                manifest.semantic_reconstruction_sha256,
                _evidence.semantic_reconstruction_digest(
                    complete.reconstruction
                ),
            ),
            (
                manifest.fitted_state_sha256,
                (
                    _contract.NO_FITTED_STATE_SHA256
                    if complete.fitted_state is None
                    else _evidence.fitted_adapter_state_digest(
                        complete.fitted_state
                    )
                ),
            ),
        )
        if any(actual != expected for actual, expected in leaf_bindings):
            raise ValueError("leaf binding mismatch")

        _evidence._validate_capabilities_and_fitted_state(
            capabilities,
            complete,
            descriptor,
            manifest,
            split_snapshot,
        )
        if capabilities.raw_byte_reconstruction:
            if complete.raw_reconstruction_bytes != source_bytes:
                raise ValueError("raw reconstruction mismatch")
        elif complete.raw_reconstruction_bytes is not None:
            raise ValueError("unadvertised raw reconstruction")
    except _evidence.AdapterEvidenceResourceError:
        _fail(AdaptedEvidenceBundleCode.RESOURCE_LIMIT)
    except Exception:
        _fail(AdaptedEvidenceBundleCode.BINDING)


def _wrapped_adapted_payloads(
    descriptor: _contract.AdapterDescriptor,
    complete: _evidence.CompleteAdaptedEventSample,
) -> dict:
    configuration = complete.sample.configuration
    values = {
        "adapter_descriptor": _payloads.adapter_descriptor_payload(
            descriptor
        ),
        "adapter_manifest": _payloads.adapter_manifest_payload(
            complete.sample.manifest
        ),
        "complete_sample_commitment": (
            _payloads.complete_sample_commitment_payload(
                descriptor,
                complete,
            )
        ),
        "coverage_ledger": _payloads.coverage_ledger_payload(
            complete.coverage
        ),
        "detached_native_observation": (
            _payloads.detached_native_observation_payload(configuration)
        ),
        "evaluation_labels": _payloads.evaluation_labels_payload(
            complete.evaluation_labels
        ),
        "fitted_state": _payloads.fitted_state_payload(
            complete.fitted_state
        ),
        "identity_bearing_native_configuration": (
            _payloads.identity_bearing_native_configuration_payload(
                configuration
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
    domains = {
        "adapter_descriptor": _contract.DESCRIPTOR_DIGEST_DOMAIN,
        "adapter_manifest": _contract.SAMPLE_MANIFEST_DIGEST_DOMAIN,
        "complete_sample_commitment": _payloads.COMPLETE_SAMPLE_DIGEST_DOMAIN,
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
        "source_inventory": (
            _payloads.PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN
        ),
        "static_context": _payloads.PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN,
    }
    wrapped = {
        name: _payloads.canonical_payload_wrapper(
            value,
            expected_domain=domains[name],
        )
        for name, value in values.items()
    }
    raw = _payloads.raw_reconstruction_payload(descriptor, complete)
    if type(raw) is _payloads.CanonicalPayloadV1:
        wrapped["raw_byte_reconstruction"] = (
            _payloads.canonical_payload_wrapper(
                raw,
                expected_domain=(
                    _payloads.RAW_RECONSTRUCTION_ABSENCE_DIGEST_DOMAIN
                ),
            )
        )
    elif type(raw) is _payloads.RawByteObjectV1:
        wrapped["raw_byte_reconstruction"] = _payloads.raw_byte_object(raw)
    else:  # pragma: no cover - typed publisher invariant
        raise TypeError("raw reconstruction projection has an invalid type")
    return wrapped


def build_adapted_evidence_bundle(
    prepared_case_input: PreparedOutputBlindCaseInputV1,
    descriptor: _contract.AdapterDescriptor,
    complete: _evidence.CompleteAdaptedEventSample,
) -> AdaptedEvidenceBundleResultV1:
    """Build a canonical private bundle from one exact actual adapter output."""

    prepared = _validated_prepared_input(prepared_case_input)
    descriptor_snapshot = _snapshot_descriptor(descriptor)
    complete_snapshot = _snapshot_complete(complete)
    _validate_bundle_bindings(
        prepared,
        descriptor_snapshot,
        complete_snapshot,
    )
    case_input = prepared.case_input
    try:
        tree = {
            "adapted": _wrapped_adapted_payloads(
                descriptor_snapshot,
                complete_snapshot,
            ),
            "artifact_type": ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE,
            "case_input_sha256": prepared.input_sha256,
            "format_version": "1",
            "source_byte_count": len(case_input.source_bytes),
            "source_sha256": hashlib.sha256(
                case_input.source_bytes
            ).hexdigest(),
            "split_manifest_sha256": _contract.split_manifest_digest(
                case_input.split_manifest
            ),
        }
        bundle_bytes = _payloads._canonical_tree_bytes(
            tree,
            maximum_encoded_bytes=MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES,
        )
        return AdaptedEvidenceBundleResultV1(
            bundle_bytes=bundle_bytes,
            bundle_byte_count=len(bundle_bytes),
            bundle_sha256=adapted_evidence_bundle_sha256(bundle_bytes),
        )
    except _payloads.PublicationPayloadError:
        _fail(AdaptedEvidenceBundleCode.RESOURCE_LIMIT)
    except AdaptedEvidenceBundleError:
        raise
    except Exception:
        _fail(AdaptedEvidenceBundleCode.INTERNAL)


def _self_derived_expected_evidence(
    complete: _evidence.CompleteAdaptedEventSample,
) -> _evidence.ExpectedAdapterEvidence:
    return _evidence.ExpectedAdapterEvidence(
        native_observation_sha256=_contract.native_observation_digest(
            complete.sample.configuration
        ),
        inventory=complete.inventory,
        coverage=complete.coverage,
        static_context=complete.static_context,
        evaluation_labels=complete.evaluation_labels,
        provenance=complete.provenance,
        fitted_state=complete.fitted_state,
        reconstruction=complete.reconstruction,
    )


def _conformance_plan_sha256(run: ConformanceRun) -> str:
    plan = run.plan
    tree = {
        "atomic_grid": plan.atomic_grid.value,
        "coverage": plan.coverage.value,
        "evaluation_labels": plan.evaluation_labels.value,
        "fitted_state": plan.fitted_state.value,
        "multiplicity_mode": plan.multiplicity_mode.value,
        "native": plan.native.value,
        "provenance": plan.provenance.value,
        "raw_reconstruction": plan.raw_reconstruction.value,
        "representation_ids": list(plan.representation_ids),
        "semantic_reconstruction": plan.semantic_reconstruction.value,
        "static_context": plan.static_context.value,
        "time_measure": plan.time_measure.value,
    }
    return _contract._domain_digest(
        _bundle_verifier.CAPABILITY_CONFORMANCE_PLAN_DIGEST_DOMAIN,
        tree,
    )


def _snapshot_adapter_descriptor(
    adapter: CompleteEvidenceAdapterV1,
) -> _contract.AdapterDescriptor:
    try:
        descriptor = adapter.descriptor()
        if type(descriptor) is not _contract.AdapterDescriptor:
            raise TypeError("descriptor must be exact")
        return _contract._snapshot_descriptor(descriptor)
    except Exception:
        _fail(AdaptedEvidenceBundleCode.ADAPTER_SNAPSHOT)


def _validated_reason_registries(
    allowed_exclusion_reason_codes: Tuple[str, ...],
    allowed_censor_reason_codes: Tuple[str, ...],
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    try:
        exclusions = _evidence._validate_reason_codes(
            allowed_exclusion_reason_codes,
            name="allowed exclusion reason",
        )
        censors = _evidence._validate_reason_codes(
            allowed_censor_reason_codes,
            name="allowed censor reason",
        )
        if len(exclusions) + len(censors) > _evidence.MAXIMUM_REASON_CODES:
            raise ValueError("combined reason registry exceeds its bound")
        return exclusions, censors
    except Exception:
        _fail(AdaptedEvidenceBundleCode.REASON_REGISTRY)


def run_local_captured_adapted_evidence(
    adapter: CompleteEvidenceAdapterV1,
    case_input: ActualAdapterCaseInputV1,
    *,
    allowed_exclusion_reason_codes: Tuple[str, ...] = (),
    allowed_censor_reason_codes: Tuple[str, ...] = (),
) -> LocalCapturedAdaptedEvidenceResultV1:
    """Capture one complete method return and bundle it after self-consistency.

    The direct ``adapt_complete`` invocation receives only the three fields in
    :class:`ActualAdapterCaseInputV1`.  Later conformance callbacks receive the
    applicable returned samples, configurations, schemas, and representation
    payloads.  This same-process call-order property is not information-flow
    enforcement or execution attestation, and the runner cannot tell whether
    adapter internals recomputed or cached their return.
    """

    if type(case_input) is not ActualAdapterCaseInputV1:
        _fail(AdaptedEvidenceBundleCode.INPUT_TYPE)
    exclusions, censors = _validated_reason_registries(
        allowed_exclusion_reason_codes,
        allowed_censor_reason_codes,
    )
    try:
        prepared = build_output_blind_case_input_v1(case_input)
        prepared = _validated_prepared_input(prepared)
    except AdaptedEvidenceBundleError:
        raise
    except Exception:
        _fail(AdaptedEvidenceBundleCode.INPUT_PREPARATION)
    try:
        satisfies_protocol = isinstance(adapter, CompleteEvidenceAdapterV1)
    except Exception:
        satisfies_protocol = False
    if not satisfies_protocol:
        _fail(AdaptedEvidenceBundleCode.ADAPTER_PROTOCOL)

    descriptor_before = _snapshot_adapter_descriptor(adapter)
    call_count = 0
    try:
        call_count += 1
        complete = adapter.adapt_complete(
            prepared.case_input.source_bytes,
            prepared.case_input.partition,
            prepared.case_input.split_manifest,
        )
    except Exception:
        _fail(AdaptedEvidenceBundleCode.ADAPTER_EXECUTION)
    if call_count != 1 or type(complete) is not _evidence.CompleteAdaptedEventSample:
        _fail(AdaptedEvidenceBundleCode.ADAPTER_OUTPUT)
    try:
        complete_snapshot = _evidence._snapshot_complete(complete)
        self_expected = _self_derived_expected_evidence(complete_snapshot)
    except Exception:
        _fail(AdaptedEvidenceBundleCode.ADAPTER_OUTPUT)

    try:
        conformance_run = run_complete_adapter_conformance(
            adapter,
            complete_snapshot,
            source_bytes=prepared.case_input.source_bytes,
            split_manifest=prepared.case_input.split_manifest,
            expected_evidence=self_expected,
            allowed_exclusion_reason_codes=exclusions,
            allowed_censor_reason_codes=censors,
        )
    except Exception:
        _fail(AdaptedEvidenceBundleCode.SELF_CONFORMANCE)

    try:
        descriptor_after = _snapshot_adapter_descriptor(adapter)
        prepared_after = build_output_blind_case_input_v1(case_input)
        prepared_after = _validated_prepared_input(prepared_after)
        complete_after = _evidence._snapshot_complete(complete)
    except Exception:
        _fail(AdaptedEvidenceBundleCode.POSTMUTATION)
    if (
        prepared_after != prepared
        or complete_after != complete_snapshot
        or descriptor_after != descriptor_before
    ):
        _fail(AdaptedEvidenceBundleCode.POSTMUTATION)

    try:
        bundle = build_adapted_evidence_bundle(
            prepared,
            descriptor_before,
            complete_snapshot,
        )
    except AdaptedEvidenceBundleError:
        raise
    except Exception:
        _fail(AdaptedEvidenceBundleCode.INTERNAL)

    try:
        return LocalCapturedAdaptedEvidenceResultV1(
            prepared_case_input=prepared,
            conformance_run=conformance_run,
            adapted_evidence_bundle=bundle,
            allowed_exclusion_reason_codes=exclusions,
            allowed_censor_reason_codes=censors,
            runner_direct_adapt_complete_call_count=1,
            runner_direct_adapt_call_count=0,
            adapt_complete_preoutput_arguments_supplied=True,
            adapt_complete_return_captured=True,
            self_consistency_conformance_passed=True,
            bundle_built_from_adapt_complete_return=True,
            output_blind_adapter_child_enforced=False,
            expected_material_nonexposure_attested=False,
            adapter_source_loaded=False,
            adapter_source_execution_identity_attested=False,
            execution_attested=False,
            containment_enforced=False,
            containment_attested=False,
            semantic_truth_attested=False,
            decision_made=False,
            generalization_attested=False,
        )
    except Exception:
        _fail(AdaptedEvidenceBundleCode.BINDING)


__all__ = [
    "ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE",
    "ADAPTED_EVIDENCE_BUNDLE_DIGEST_DOMAIN",
    "AdaptedEvidenceBundleCode",
    "AdaptedEvidenceBundleError",
    "AdaptedEvidenceBundleResultV1",
    "LocalCapturedAdaptedEvidenceResultV1",
    "MAXIMUM_ADAPTED_EVIDENCE_BUNDLE_BYTES",
    "adapted_evidence_bundle_sha256",
    "build_adapted_evidence_bundle",
    "run_local_captured_adapted_evidence",
]
