"""Write-free freezing of authority-bound V2 decision candidates.

This publisher-side layer authenticates the approved profile, snapshots exact
V2 cases and hostile controls, validates typed golden receipt/registry/source
custody, proves exact oracle-source membership in a path-free source archive,
matches the complete approved inventories, and invokes each adapter's fresh
conformance path exactly once.  It accepts no execution-guard receipt, does no
filesystem or process I/O, writes nothing, and makes no gate decision.

The supplied oracle source is deliberately not executed in-process.  A final
decision still requires a separately contained, independently reviewed oracle
runner.  The future verifier must independently reimplement both source
membership and execution checks rather than trusting this publisher module.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
from typing import NamedTuple, Tuple

from heterodiff.events import EventConfiguration

from . import adapter_contract as _contract
from . import adapter_evidence as _evidence
from . import adapter_publication_payloads as _payloads
from .adapter_conformance_runner import (
    ConformanceRun,
    RunnerConformanceCode,
    RunnerConformanceError,
    run_complete_adapter_conformance,
)
from .adapter_evidence import (
    AdapterConformanceCode,
    AdapterConformanceError,
    AdapterEvidenceResourceError,
)
from .adapter_publication_authority import (
    PublicationAuthorityCode,
    PublicationAuthorityError,
    ValidatedIndependentGoldenReceiptV1,
    ValidatedPublicationBindingAuthorityV1,
    validate_approved_profile_registry,
    validate_golden_oracle_registry,
    validate_independent_golden_receipt,
    validate_publication_binding_authority,
)
from .adapter_publication_authority_types import (
    ApprovedCaseExpectationV1,
    ApprovedPublicationAuthorityInputV1,
    DecisionHostileControlInputV1,
    DecisionPublicationFreezeInputV1,
    HostileControlRequirementV1,
    IndependentGoldenReceiptInputV1,
    IndependentGoldenReceiptV1,
    VerifiedDetachedCaseInputV2,
)
from .adapter_publication_prepare import (
    PublicationPreparationCode,
    PublicationPreparationError,
)
from .adapter_publication_types import (
    HostileControlInputV1,
    MAXIMUM_PRIVATE_ARTIFACT_BYTES,
    PUBLICATION_DEVELOPMENT_STATUS,
    PublicAdapterIdentityV1,
    PublicIdentifierRegistryV1,
    PublicationBindingInputV1,
)
from .adapter_source_archive import (
    SOURCE_ARCHIVE_ORACLE_ROLE_ID,
    SourceArchiveMembershipRequestV1,
    SourceArchiveValidationError,
    ValidatedSourceArchiveMembershipV1,
    ValidatedSourceArchiveV1,
    validate_source_archive_memberships,
)


DECISION_GOLDEN_ORACLE_EXECUTION_STATUS = (
    "RECEIPT_SOURCE_REGISTRY_ARCHIVE_BOUND_ORACLE_NOT_EXECUTED"
)
MAXIMUM_DECISION_AGGREGATE_NODES = 200_000
MAXIMUM_DECISION_REVALIDATION_WORK_BYTES = 512 * 1024 * 1024
_STRUCTURAL_NODE_OVERHEAD_BYTES = 64
_MAXIMUM_DECISION_GRAPH_DEPTH = 64

_CAPABILITY_FIELDS = (
    "semantic_reconstruction",
    "raw_byte_reconstruction",
    "fitted_state",
    "static_context",
    "evaluation_labels",
    "private_provenance",
)


class FrozenDecisionDetachedCaseV1(NamedTuple):
    """Fresh case snapshot after the untrusted adapter reference is dropped."""

    case_expectation: ApprovedCaseExpectationV1
    source_bytes: bytes
    descriptor: _contract.AdapterDescriptor
    split_manifest: _contract.SplitManifest
    complete_sample: _evidence.CompleteAdaptedEventSample
    expected_evidence: _evidence.ExpectedAdapterEvidence
    expected_configuration: EventConfiguration
    conformance_run: ConformanceRun
    independent_golden: ValidatedIndependentGoldenReceiptV1
    oracle_source_membership: ValidatedSourceArchiveMembershipV1


class FrozenDecisionPublicationInputV1(NamedTuple):
    """Canonical candidate snapshots; this is not decision evidence."""

    candidate_status: str
    golden_oracle_execution_status: str
    bindings: PublicationBindingInputV1
    public_ids: PublicIdentifierRegistryV1
    binding_authority: ValidatedPublicationBindingAuthorityV1
    cases: Tuple[FrozenDecisionDetachedCaseV1, ...]
    hostile_controls: Tuple[DecisionHostileControlInputV1, ...]


class _DecisionCaseSnapshot(NamedTuple):
    adapter: object
    source_bytes: bytes
    descriptor: _contract.AdapterDescriptor
    split_manifest: _contract.SplitManifest
    complete_sample: _evidence.CompleteAdaptedEventSample
    expected_evidence: _evidence.ExpectedAdapterEvidence
    expected_configuration: EventConfiguration
    conformance_run: ConformanceRun
    independent_golden: IndependentGoldenReceiptInputV1


class _ValidatedCaseCandidate(NamedTuple):
    snapshot: _DecisionCaseSnapshot
    golden: ValidatedIndependentGoldenReceiptV1
    oracle_source_membership: ValidatedSourceArchiveMembershipV1
    expectation: ApprovedCaseExpectationV1


def _fail(code: PublicationPreparationCode) -> None:
    raise PublicationPreparationError(code) from None


def _base64_length(value: int) -> int:
    if type(value) is not int or value < 0:
        raise TypeError("base64 length must be an exact nonnegative integer")
    return 4 * ((value + 2) // 3)


class _AggregateBudget:
    def __init__(self) -> None:
        self.nodes = 0
        self.raw_bytes = 0
        self.encoded_bytes = 0

    def add_node(self) -> None:
        self.nodes += 1
        self.encoded_bytes += _STRUCTURAL_NODE_OVERHEAD_BYTES
        self._check()

    def add_bytes(self, value: bytes) -> None:
        self.raw_bytes += len(value)
        self.encoded_bytes += _base64_length(len(value))
        self._check()

    def add_text(self, value: str) -> None:
        self.encoded_bytes += len(value.encode("utf-8"))
        self._check()

    def _check(self) -> None:
        if (
            self.nodes > MAXIMUM_DECISION_AGGREGATE_NODES
            or self.raw_bytes > MAXIMUM_PRIVATE_ARTIFACT_BYTES
            or self.encoded_bytes > MAXIMUM_PRIVATE_ARTIFACT_BYTES
        ):
            raise AdapterEvidenceResourceError(
                "decision object graph exceeds its aggregate bound"
            )


def _preflight_graph(
    value: object,
    *,
    budget: _AggregateBudget,
    active: set,
    depth: int,
) -> None:
    if depth > _MAXIMUM_DECISION_GRAPH_DEPTH:
        raise AdapterEvidenceResourceError(
            "decision object graph exceeds its depth bound"
        )
    budget.add_node()
    if value is None or type(value) in (bool, int, float):
        return
    if isinstance(value, Enum):
        budget.add_text(value.value)
        return
    if type(value) is str:
        budget.add_text(value)
        return
    if type(value) is bytes:
        budget.add_bytes(value)
        return

    identifier = id(value)
    if identifier in active:
        raise TypeError("decision object graph must be acyclic")
    active.add(identifier)
    try:
        if is_dataclass(value) and not isinstance(value, type):
            for definition in fields(value):
                _preflight_graph(
                    getattr(value, definition.name),
                    budget=budget,
                    active=active,
                    depth=depth + 1,
                )
            return
        if type(value) in (tuple, frozenset):
            for item in value:
                _preflight_graph(
                    item,
                    budget=budget,
                    active=active,
                    depth=depth + 1,
                )
            return
        if isinstance(value, Mapping):
            for key, item in value.items():
                _preflight_graph(
                    key,
                    budget=budget,
                    active=active,
                    depth=depth + 1,
                )
                _preflight_graph(
                    item,
                    budget=budget,
                    active=active,
                    depth=depth + 1,
                )
            return
        raise TypeError("decision object graph has an invalid exact leaf")
    finally:
        active.remove(identifier)


def _preflight_request(
    value: DecisionPublicationFreezeInputV1,
) -> _AggregateBudget:
    budget = _AggregateBudget()
    for case in value.cases:
        if type(case) is not VerifiedDetachedCaseInputV2:
            raise TypeError("decision case input must be exact")
        golden = case.independent_golden
        if type(golden) is not IndependentGoldenReceiptInputV1:
            raise TypeError("decision golden input must be exact")
        for root in (
            case.source_bytes,
            case.descriptor,
            case.split_manifest,
            case.complete_sample,
            case.expected_evidence,
            case.expected_configuration,
            case.conformance_run,
            golden,
        ):
            _preflight_graph(
                root,
                budget=budget,
                active=set(),
                depth=0,
            )

    for hostile in value.hostile_controls:
        if type(hostile) is not DecisionHostileControlInputV1:
            raise TypeError("decision hostile input must be exact")
        _preflight_graph(
            hostile,
            budget=budget,
            active=set(),
            depth=0,
        )
    return budget


def _preflight_profile_inventory_shape(
    request: DecisionPublicationFreezeInputV1,
    profile: object,
) -> None:
    if type(request.cases) is not tuple or type(
        request.hostile_controls
    ) is not tuple:
        _fail(PublicationPreparationCode.PUB_INPUT_TYPE)
    if any(
        type(item) is not VerifiedDetachedCaseInputV2
        for item in request.cases
    ) or any(
        type(item) is not DecisionHostileControlInputV1
        for item in request.hostile_controls
    ):
        _fail(PublicationPreparationCode.PUB_INPUT_TYPE)
    if len(request.cases) != len(profile.case_expectations):
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    if len(request.hostile_controls) != len(
        profile.hostile_control_expectations
    ):
        _fail(PublicationPreparationCode.PUB_HOSTILE_INVENTORY_MISMATCH)
    roots = []
    for case in request.cases:
        if (
            type(case) is not VerifiedDetachedCaseInputV2
            or type(case.conformance_run) is not ConformanceRun
        ):
            _fail(PublicationPreparationCode.PUB_INPUT_TYPE)
        roots.append(case.conformance_run.sample_root_sha256)
    if len(set(roots)) != len(roots):
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    approved_roots = tuple(
        item.sample_root_sha256 for item in profile.case_expectations
    )
    if len(set(approved_roots)) != len(approved_roots):
        _fail(PublicationPreparationCode.PUB_AUTHORITY_INVALID)
    control_ids = tuple(
        item.control_id for item in request.hostile_controls
    )
    if any(type(item) is not str for item in control_ids):
        _fail(PublicationPreparationCode.PUB_INPUT_TYPE)
    if len(set(control_ids)) != len(control_ids):
        _fail(PublicationPreparationCode.PUB_HOSTILE_INVENTORY_MISMATCH)


def _preflight_reason_registry(
    public_ids: PublicIdentifierRegistryV1,
) -> None:
    exclusion = public_ids.coverage_exclusion_reason_ids
    censor = public_ids.censor_reason_ids
    if type(exclusion) is not tuple or type(censor) is not tuple:
        _fail(PublicationPreparationCode.PUB_INPUT_TYPE)
    if (
        len(exclusion) > _evidence.MAXIMUM_REASON_CODES
        or len(censor) > _evidence.MAXIMUM_REASON_CODES
        or len(exclusion) + len(censor) > _evidence.MAXIMUM_REASON_CODES
    ):
        _fail(PublicationPreparationCode.PUB_INPUT_RESOURCE)


def _preflight_revalidation_work(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    budget: _AggregateBudget,
) -> None:
    binding_bytes = sum(
        len(getattr(request.bindings, name))
        for name in PublicationBindingInputV1.__dataclass_fields__
    )
    authority_bytes = len(authority_input.profile_bytes)
    per_pass = budget.encoded_bytes + binding_bytes + authority_bytes
    revalidation_passes = len(request.cases) + 1
    if (
        per_pass * revalidation_passes
        > MAXIMUM_DECISION_REVALIDATION_WORK_BYTES
    ):
        _fail(PublicationPreparationCode.PUB_INPUT_RESOURCE)


def _snapshot_bindings(value: object) -> PublicationBindingInputV1:
    if type(value) is not PublicationBindingInputV1:
        raise TypeError("publication bindings must be exact")
    return PublicationBindingInputV1(
        **{
            name: getattr(value, name)
            for name in PublicationBindingInputV1.__dataclass_fields__
        }
    )


def _snapshot_registry(value: object) -> PublicIdentifierRegistryV1:
    if type(value) is not PublicIdentifierRegistryV1:
        raise TypeError("public identifier registry must be exact")
    values = {}
    for name in PublicIdentifierRegistryV1.__dataclass_fields__:
        if name == "adapter_identities":
            values[name] = tuple(
                PublicAdapterIdentityV1(item.adapter_id, item.adapter_version)
                for item in value.adapter_identities
            )
        else:
            field_value = getattr(value, name)
            if type(field_value) is not tuple:
                raise TypeError("public identifier category must be exact")
            values[name] = tuple(field_value)
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


def _snapshot_golden(value: object) -> IndependentGoldenReceiptInputV1:
    if type(value) is not IndependentGoldenReceiptInputV1:
        raise TypeError("independent golden input must be exact")
    receipt = value.receipt
    if type(receipt) is not IndependentGoldenReceiptV1:
        raise TypeError("independent golden receipt must be exact")
    receipt_snapshot = IndependentGoldenReceiptV1(
        **{
            name: getattr(receipt, name)
            for name, definition in (
                IndependentGoldenReceiptV1.__dataclass_fields__.items()
            )
            if definition.init
        }
    )
    return IndependentGoldenReceiptInputV1(
        receipt_snapshot,
        value.receipt_bytes,
        value.oracle_source_bytes,
    )


def _snapshot_case(value: object) -> _DecisionCaseSnapshot:
    if type(value) is not VerifiedDetachedCaseInputV2:
        raise TypeError("decision case must be exact")
    checked = VerifiedDetachedCaseInputV2(
        adapter=value.adapter,
        source_bytes=value.source_bytes,
        descriptor=value.descriptor,
        split_manifest=value.split_manifest,
        complete_sample=value.complete_sample,
        expected_evidence=value.expected_evidence,
        expected_configuration=value.expected_configuration,
        conformance_run=value.conformance_run,
        independent_golden=value.independent_golden,
    )
    return _DecisionCaseSnapshot(
        adapter=checked.adapter,
        source_bytes=checked.source_bytes,
        descriptor=_contract._snapshot_descriptor(checked.descriptor),
        split_manifest=_evidence.snapshot_bounded_split_manifest(
            checked.split_manifest
        ),
        complete_sample=_evidence._snapshot_complete(checked.complete_sample),
        expected_evidence=_evidence._snapshot_expected_evidence(
            checked.expected_evidence
        ),
        expected_configuration=(
            _evidence.snapshot_bounded_native_configuration(
                checked.expected_configuration
            )
        ),
        conformance_run=_snapshot_run(checked.conformance_run),
        independent_golden=_snapshot_golden(checked.independent_golden),
    )


def _snapshot_hostile(value: object) -> DecisionHostileControlInputV1:
    if type(value) is not DecisionHostileControlInputV1:
        raise TypeError("decision hostile control must be exact")
    return DecisionHostileControlInputV1(
        attack_kind_id=value.attack_kind_id,
        control_id=value.control_id,
        error_code=value.error_code,
        expected_stage_id=value.expected_stage_id,
        input_bytes=value.input_bytes,
        origin_class_id=value.origin_class_id,
        sink_field_id=value.sink_field_id,
        status_id=value.status_id,
        test_node_bytes=value.test_node_bytes,
    )


def _configuration_key(configuration: object) -> bytes:
    """Return the complete identity-bearing canonical payload.

    Detached native digests intentionally omit sample/group/event identity, and
    ordinary dataclass equality is not a publication commitment.  Every V2
    equality and mutation comparison therefore uses the full canonical bytes.
    """

    return (
        _payloads.identity_bearing_native_configuration_payload(
            configuration
        ).canonical_json_bytes
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


def _case_snapshot_key(value: _DecisionCaseSnapshot) -> Tuple[object, ...]:
    golden = value.independent_golden
    return (
        value.source_bytes,
        value.descriptor,
        value.split_manifest,
        _complete_key(value.complete_sample),
        value.expected_evidence,
        _configuration_key(value.expected_configuration),
        value.conformance_run,
        golden.receipt,
        golden.receipt_bytes,
        golden.oracle_source_bytes,
    )


def _require_case_unchanged(
    case: _DecisionCaseSnapshot,
    retained_key: Tuple[object, ...],
) -> None:
    try:
        current_key = _case_snapshot_key(case)
    except Exception:
        _fail(PublicationPreparationCode.PUB_POSTMUTATION)
    if current_key != retained_key:
        _fail(PublicationPreparationCode.PUB_POSTMUTATION)


def _require_member(value: str, category: Tuple[str, ...]) -> None:
    if value not in category:
        _fail(PublicationPreparationCode.PUB_ID_NOT_ALLOWLISTED)


def _check_case_public_ids(
    case: _DecisionCaseSnapshot,
    registry: PublicIdentifierRegistryV1,
) -> None:
    descriptor = case.descriptor
    identity = descriptor.identity
    identity_key = (identity.adapter_id, identity.adapter_version)
    admitted = tuple(
        (item.adapter_id, item.adapter_version)
        for item in registry.adapter_identities
    )
    if identity_key not in admitted:
        _fail(PublicationPreparationCode.PUB_ID_NOT_ALLOWLISTED)
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
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
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


def _legacy_hostile(value: DecisionHostileControlInputV1) -> HostileControlInputV1:
    return HostileControlInputV1(
        control_id=value.control_id,
        status_id=value.status_id,
        error_code=value.error_code,
        input_bytes=value.input_bytes,
        test_node_bytes=value.test_node_bytes,
    )


def _hostile_requirement(
    value: DecisionHostileControlInputV1,
) -> HostileControlRequirementV1:
    receipt = _payloads.hostile_control_receipt_payload(
        _legacy_hostile(value)
    )
    return HostileControlRequirementV1(
        attack_kind_id=value.attack_kind_id,
        control_id=value.control_id,
        error_code=value.error_code,
        expected_stage_id=value.expected_stage_id,
        hostile_control_receipt_sha256=receipt.payload_sha256,
        input_sha256=_payloads.domain_separated_sha256(
            _payloads.HOSTILE_CONTROL_INPUT_DIGEST_DOMAIN,
            value.input_bytes,
        ),
        origin_class_id=value.origin_class_id,
        sink_field_id=value.sink_field_id,
        status_id=value.status_id,
        test_node_sha256=_payloads.domain_separated_sha256(
            _payloads.HOSTILE_CONTROL_TEST_NODE_DIGEST_DOMAIN,
            value.test_node_bytes,
        ),
    )


def _approved_hostile_inventory(
    values: Tuple[DecisionHostileControlInputV1, ...],
) -> Tuple[HostileControlRequirementV1, ...]:
    result = tuple(
        sorted(
            (_hostile_requirement(value) for value in values),
            key=lambda item: item.control_id,
        )
    )
    control_ids = tuple(item.control_id for item in result)
    if len(set(control_ids)) != len(control_ids):
        _fail(PublicationPreparationCode.PUB_HOSTILE_INVENTORY_MISMATCH)
    return result


def _validate_golden_case_binding(
    case: _DecisionCaseSnapshot,
    golden: ValidatedIndependentGoldenReceiptV1,
) -> None:
    receipt = golden.receipt
    identity = case.descriptor.identity
    descriptor = _payloads.adapter_descriptor_payload(case.descriptor)
    expected_configuration = (
        _payloads.identity_bearing_native_configuration_payload(
            case.expected_configuration
        )
    )
    expected_evidence = _payloads.expected_evidence_payload(
        case.expected_evidence
    )
    split = _payloads.split_manifest_payload(case.split_manifest)
    observed = (
        (receipt.adapter_id, identity.adapter_id),
        (receipt.adapter_version, identity.adapter_version),
        (receipt.descriptor_sha256, descriptor.payload_sha256),
        (
            receipt.expected_configuration_payload_byte_count,
            expected_configuration.payload_byte_count,
        ),
        (
            receipt.expected_configuration_sha256,
            expected_configuration.payload_sha256,
        ),
        (
            receipt.expected_evidence_sha256,
            expected_evidence.payload_sha256,
        ),
        (
            receipt.expected_native_observation_sha256,
            _contract.native_observation_digest(
                case.expected_configuration
            ),
        ),
        (receipt.source_byte_count, len(case.source_bytes)),
        (
            receipt.source_sha256,
            hashlib.sha256(case.source_bytes).hexdigest(),
        ),
        (receipt.split_manifest_sha256, split.payload_sha256),
    )
    if any(expected != actual for expected, actual in observed):
        _fail(PublicationPreparationCode.PUB_GOLDEN_MISMATCH)


def _validate_supplied_case_commitments(
    case: _DecisionCaseSnapshot,
) -> None:
    descriptor = _payloads.adapter_descriptor_payload(case.descriptor)
    split = _payloads.split_manifest_payload(case.split_manifest)
    expected = _payloads.expected_evidence_payload(case.expected_evidence)
    configuration = case.complete_sample.sample.configuration
    manifest = case.complete_sample.sample.manifest
    source_sha256 = hashlib.sha256(case.source_bytes).hexdigest()
    native_sha256 = _contract.native_observation_digest(
        case.expected_configuration
    )
    schema_sha256 = _contract.feature_schema_digest(
        configuration.schema
    )
    run = case.conformance_run
    observed = (
        (run.adapter_id, case.descriptor.identity.adapter_id),
        (run.adapter_version, case.descriptor.identity.adapter_version),
        (run.descriptor_sha256, descriptor.payload_sha256),
        (run.source_sha256, source_sha256),
        (run.split_manifest_sha256, split.payload_sha256),
        (run.native_observation_sha256, native_sha256),
        (run.sample_root_sha256, manifest.sample_root_sha256),
        (run.expected_evidence_sha256, expected.payload_sha256),
        (manifest.descriptor_sha256, descriptor.payload_sha256),
        (manifest.source_sha256, source_sha256),
        (manifest.source_size_bytes, len(case.source_bytes)),
        (manifest.split_manifest_sha256, split.payload_sha256),
        (manifest.native_observation_sha256, native_sha256),
        (manifest.schema_sha256, schema_sha256),
        (manifest.schema_version, configuration.schema.version),
        (
            case.expected_evidence.native_observation_sha256,
            native_sha256,
        ),
        (
            _configuration_key(configuration),
            _configuration_key(case.expected_configuration),
        ),
    )
    try:
        partition = case.split_manifest.partition_for(
            manifest.partition.sample_id
        )
    except Exception:
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    observed += (
        (manifest.partition, partition),
        (configuration.sample_id, manifest.partition.sample_id),
        (configuration.group_id, manifest.partition.group_id),
    )
    if any(supplied != recomputed for supplied, recomputed in observed):
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)


def _case_expectation(
    case: _DecisionCaseSnapshot,
    golden: ValidatedIndependentGoldenReceiptV1,
    *,
    ordinal: int,
) -> ApprovedCaseExpectationV1:
    identity = case.descriptor.identity
    descriptor = _payloads.adapter_descriptor_payload(case.descriptor)
    split = _payloads.split_manifest_payload(case.split_manifest)
    complete = _payloads.complete_sample_commitment_payload(
        case.descriptor,
        case.complete_sample,
    )
    expected = _payloads.expected_evidence_payload(case.expected_evidence)
    configuration = _payloads.identity_bearing_native_configuration_payload(
        case.expected_configuration
    )
    run = _payloads.conformance_run_payload(case.conformance_run)
    return ApprovedCaseExpectationV1(
        adapter_id=identity.adapter_id,
        adapter_version=identity.adapter_version,
        case_ordinal=ordinal,
        complete_sample_commitment_sha256=complete.payload_sha256,
        conformance_run_sha256=run.payload_sha256,
        descriptor_sha256=descriptor.payload_sha256,
        expected_configuration_sha256=configuration.payload_sha256,
        expected_evidence_sha256=expected.payload_sha256,
        independent_golden_receipt_sha256=golden.receipt_sha256,
        native_observation_sha256=_contract.native_observation_digest(
            case.expected_configuration
        ),
        sample_root_sha256=case.conformance_run.sample_root_sha256,
        source_sha256=hashlib.sha256(case.source_bytes).hexdigest(),
        split_manifest_sha256=split.payload_sha256,
    )


def _validate_case_inventory(
    candidates: Tuple[_ValidatedCaseCandidate, ...],
    approved: Tuple[ApprovedCaseExpectationV1, ...],
) -> None:
    if len(candidates) != len(approved):
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    for candidate, expected in zip(candidates, approved):
        actual = candidate.expectation
        actual_without_golden = tuple(
            getattr(actual, name)
            for name in ApprovedCaseExpectationV1.__dataclass_fields__
            if name != "independent_golden_receipt_sha256"
        )
        expected_without_golden = tuple(
            getattr(expected, name)
            for name in ApprovedCaseExpectationV1.__dataclass_fields__
            if name != "independent_golden_receipt_sha256"
        )
        if actual_without_golden != expected_without_golden:
            _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
        if (
            actual.independent_golden_receipt_sha256
            != expected.independent_golden_receipt_sha256
        ):
            _fail(PublicationPreparationCode.PUB_GOLDEN_MISMATCH)


def _adapter_surface_key(adapter: object) -> Tuple[object, ...]:
    descriptor = _contract._snapshot_descriptor(adapter.descriptor())
    schema = _evidence.snapshot_bounded_schema(adapter.schema())
    return descriptor, _contract.feature_schema_digest(schema)


def _expected_adapter_surface(
    case: _DecisionCaseSnapshot,
) -> Tuple[object, ...]:
    return (
        case.descriptor,
        _contract.feature_schema_digest(
            case.complete_sample.sample.configuration.schema
        ),
    )


def _validate_identity_surfaces(
    candidates: Tuple[_ValidatedCaseCandidate, ...],
) -> None:
    surfaces = {}
    for candidate in candidates:
        case = candidate.snapshot
        identity = (
            case.descriptor.identity.adapter_id,
            case.descriptor.identity.adapter_version,
        )
        surface = _expected_adapter_surface(case)
        prior = surfaces.setdefault(identity, surface)
        if prior != surface:
            _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)


def _fresh_run(
    case: _DecisionCaseSnapshot,
    registry: PublicIdentifierRegistryV1,
) -> ConformanceRun:
    try:
        surface_before = _adapter_surface_key(case.adapter)
    except Exception:
        _fail(PublicationPreparationCode.PUB_RUN_ORIGIN_INVALID)
    expected_surface = _expected_adapter_surface(case)
    if surface_before != expected_surface:
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    retained_case_key = _case_snapshot_key(case)
    try:
        retained_partition = (
            case.complete_sample.sample.manifest.partition
        )
        disposable_partition = _contract.SamplePartition(
            retained_partition.sample_id,
            retained_partition.group_id,
            retained_partition.split,
        )
        disposable_split = _evidence.snapshot_bounded_split_manifest(
            case.split_manifest
        )
        fresh_sample = case.adapter.adapt(
            case.source_bytes,
            disposable_partition,
            disposable_split,
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
        _fail(PublicationPreparationCode.PUB_RUN_ORIGIN_INVALID)
    if (
        fresh_sample.manifest != case.complete_sample.sample.manifest
        or _configuration_key(fresh_sample.configuration)
        != _configuration_key(case.complete_sample.sample.configuration)
    ):
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    _require_case_unchanged(case, retained_case_key)
    try:
        disposable_complete = _evidence._snapshot_complete(
            case.complete_sample
        )
        disposable_expected = _evidence._snapshot_expected_evidence(
            case.expected_evidence
        )
        disposable_split = _evidence.snapshot_bounded_split_manifest(
            case.split_manifest
        )
        result = run_complete_adapter_conformance(
            case.adapter,
            disposable_complete,
            source_bytes=case.source_bytes,
            split_manifest=disposable_split,
            expected_evidence=disposable_expected,
            allowed_exclusion_reason_codes=(
                registry.coverage_exclusion_reason_ids
            ),
            allowed_censor_reason_codes=registry.censor_reason_ids,
        )
    except AdapterConformanceError as error:
        if error.code in (
            AdapterConformanceCode.DOMAIN_VALIDATION_FAILED.value,
            AdapterConformanceCode.DOMAIN_VALIDATION_RETURNED_VALUE.value,
        ):
            _fail(PublicationPreparationCode.PUB_RUN_ORIGIN_INVALID)
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    except RunnerConformanceError as error:
        if (
            error.code
            == RunnerConformanceCode.REPRESENTATION_ROUNDTRIP_MISMATCH.value
        ):
            _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
        _fail(PublicationPreparationCode.PUB_RUN_ORIGIN_INVALID)
    except Exception:
        _fail(PublicationPreparationCode.PUB_RUN_ORIGIN_INVALID)
    fresh_run = _snapshot_run(result)
    _require_case_unchanged(case, retained_case_key)
    try:
        surface_after = _adapter_surface_key(case.adapter)
    except Exception:
        _fail(PublicationPreparationCode.PUB_POSTMUTATION)
    if surface_after != expected_surface:
        _fail(PublicationPreparationCode.PUB_POSTMUTATION)
    return fresh_run


def _validate_case_recomputations(
    case: _DecisionCaseSnapshot,
    fresh_run: ConformanceRun,
) -> None:
    if fresh_run != case.conformance_run:
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    if fresh_run.descriptor_sha256 != case.descriptor.descriptor_sha256:
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    if (
        fresh_run.source_sha256
        != case.complete_sample.sample.manifest.source_sha256
    ):
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    if (
        _configuration_key(case.complete_sample.sample.configuration)
        != _configuration_key(case.expected_configuration)
    ):
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    if (
        _contract.native_observation_digest(case.expected_configuration)
        != case.expected_evidence.native_observation_sha256
    ):
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)


def _validated_binding_authority(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
) -> ValidatedPublicationBindingAuthorityV1:
    try:
        result = validate_publication_binding_authority(
            request.bindings,
            request.public_ids,
            authority_input,
        )
        validate_approved_profile_registry(
            result.authority.profile,
            request.public_ids,
        )
        return result
    except PublicationAuthorityError as error:
        if error.code == PublicationAuthorityCode.AUTH_INPUT_TYPE.value:
            _fail(PublicationPreparationCode.PUB_INPUT_TYPE)
        if error.code == PublicationAuthorityCode.AUTH_BINDING_MISMATCH.value:
            _fail(PublicationPreparationCode.PUB_BINDING_MISMATCH)
        _fail(PublicationPreparationCode.PUB_AUTHORITY_INVALID)


def _validated_candidates(
    cases: Tuple[_DecisionCaseSnapshot, ...],
    *,
    oracle_registry_bytes: bytes,
    source_archive_inventory_bytes: bytes,
    source_archive_bytes: bytes,
) -> Tuple[_ValidatedCaseCandidate, ...]:
    golden_cases = []
    for case in cases:
        try:
            golden = validate_independent_golden_receipt(
                case.independent_golden,
                oracle_registry_bytes=oracle_registry_bytes,
            )
        except PublicationAuthorityError:
            _fail(PublicationPreparationCode.PUB_GOLDEN_MISMATCH)
        golden_cases.append((case, golden))
    try:
        membership_set = validate_source_archive_memberships(
            source_archive_inventory_bytes,
            source_archive_bytes,
            tuple(
                SourceArchiveMembershipRequestV1(
                    role_id=SOURCE_ARCHIVE_ORACLE_ROLE_ID,
                    source_object_id=golden.receipt.oracle_id,
                    source_bytes=golden.oracle_source_bytes,
                )
                for _case, golden in golden_cases
            ),
        )
    except (SourceArchiveValidationError, TypeError, ValueError):
        _fail(PublicationPreparationCode.PUB_GOLDEN_MISMATCH)
    _require_complete_oracle_source_inventory(
        membership_set.source_archive,
        oracle_registry_bytes,
    )
    provisional = []
    for (case, golden), source_membership in zip(
        golden_cases,
        membership_set.memberships,
    ):
        try:
            if (
                source_membership.role_id
                != SOURCE_ARCHIVE_ORACLE_ROLE_ID
                or source_membership.source_object_id
                != golden.receipt.oracle_id
                or source_membership.source_byte_count
                != len(golden.oracle_source_bytes)
                or source_membership.source_sha256
                != hashlib.sha256(golden.oracle_source_bytes).hexdigest()
            ):
                _fail(PublicationPreparationCode.PUB_GOLDEN_MISMATCH)
        except PublicationPreparationError:
            raise
        except Exception:
            _fail(PublicationPreparationCode.PUB_GOLDEN_MISMATCH)
        try:
            _validate_golden_case_binding(case, golden)
            _validate_supplied_case_commitments(case)
            expectation = _case_expectation(case, golden, ordinal=0)
        except PublicationPreparationError:
            raise
        except Exception:
            _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
        provisional.append((case, golden, source_membership, expectation))
    provisional.sort(
        key=lambda item: (
            item[3].sample_root_sha256,
            item[3].expected_evidence_sha256,
            item[3].adapter_id,
        )
    )
    roots = tuple(item[3].sample_root_sha256 for item in provisional)
    if len(set(roots)) != len(roots):
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)
    return tuple(
        _ValidatedCaseCandidate(
            snapshot=case,
            golden=golden,
            oracle_source_membership=source_membership,
            expectation=_case_expectation(case, golden, ordinal=index),
        )
        for index, (
            case,
            golden,
            source_membership,
            _expectation,
        ) in enumerate(provisional)
    )


def _require_complete_oracle_source_inventory(
    source_archive: ValidatedSourceArchiveV1,
    oracle_registry_bytes: bytes,
) -> None:
    try:
        registry = validate_golden_oracle_registry(oracle_registry_bytes)
    except PublicationAuthorityError:
        _fail(PublicationPreparationCode.PUB_GOLDEN_MISMATCH)
    expected = tuple(
        (
            item.oracle_id,
            item.oracle_source_byte_count,
            item.oracle_source_sha256,
        )
        for item in registry.oracles
    )
    observed = tuple(
        (
            item.source_object_id,
            item.source_byte_count,
            item.source_sha256,
        )
        for item in source_archive.inventory.source_objects
        if item.role_id == SOURCE_ARCHIVE_ORACLE_ROLE_ID
    )
    if observed != expected:
        _fail(PublicationPreparationCode.PUB_GOLDEN_MISMATCH)


def _frozen_case(
    candidate: _ValidatedCaseCandidate,
    fresh_run: ConformanceRun,
) -> FrozenDecisionDetachedCaseV1:
    case = candidate.snapshot
    return FrozenDecisionDetachedCaseV1(
        case_expectation=candidate.expectation,
        source_bytes=case.source_bytes,
        descriptor=case.descriptor,
        split_manifest=case.split_manifest,
        complete_sample=case.complete_sample,
        expected_evidence=case.expected_evidence,
        expected_configuration=case.expected_configuration,
        conformance_run=fresh_run,
        independent_golden=candidate.golden,
        oracle_source_membership=candidate.oracle_source_membership,
    )


def _require_request_unchanged(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
    *,
    binding_authority: ValidatedPublicationBindingAuthorityV1,
    bindings: PublicationBindingInputV1,
    registry: PublicIdentifierRegistryV1,
    cases: Tuple[_DecisionCaseSnapshot, ...],
    hostiles: Tuple[DecisionHostileControlInputV1, ...],
) -> None:
    try:
        binding_authority_after = _validated_binding_authority(
            request,
            authority_input,
        )
        bindings_after = _snapshot_bindings(request.bindings)
        registry_after = _snapshot_registry(request.public_ids)
        cases_after = tuple(_snapshot_case(value) for value in request.cases)
        hostiles_after = tuple(
            _snapshot_hostile(value) for value in request.hostile_controls
        )
    except Exception:
        _fail(PublicationPreparationCode.PUB_POSTMUTATION)
    if (
        binding_authority_after != binding_authority
        or bindings_after != bindings
        or registry_after != registry
        or len(cases_after) != len(cases)
        or any(
            after.adapter is not before.adapter
            for before, after in zip(cases, cases_after)
        )
        or tuple(_case_snapshot_key(value) for value in cases_after)
        != tuple(_case_snapshot_key(value) for value in cases)
        or hostiles_after != hostiles
    ):
        _fail(PublicationPreparationCode.PUB_POSTMUTATION)


def _freeze_decision_publication_input(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
) -> FrozenDecisionPublicationInputV1:
    binding_authority = _validated_binding_authority(request, authority_input)
    profile = binding_authority.authority.profile
    try:
        _preflight_profile_inventory_shape(request, profile)
        _preflight_reason_registry(request.public_ids)
        aggregate_budget = _preflight_request(request)
        _preflight_revalidation_work(
            request,
            authority_input,
            aggregate_budget,
        )
        bindings = _snapshot_bindings(request.bindings)
        registry = _snapshot_registry(request.public_ids)
        cases = tuple(_snapshot_case(value) for value in request.cases)
        hostiles = tuple(
            _snapshot_hostile(value) for value in request.hostile_controls
        )
    except AdapterEvidenceResourceError:
        _fail(PublicationPreparationCode.PUB_INPUT_RESOURCE)
    except PublicationPreparationError:
        raise
    except Exception:
        _fail(PublicationPreparationCode.PUB_INPUT_TYPE)

    try:
        candidates = _validated_candidates(
            cases,
            oracle_registry_bytes=bindings.oracle_registry_bytes,
            source_archive_inventory_bytes=(
                bindings.source_tree_manifest_bytes
            ),
            source_archive_bytes=bindings.source_tree_archive_bytes,
        )
        hostile_inventory = _approved_hostile_inventory(hostiles)
    except PublicationPreparationError:
        raise
    except SourceArchiveValidationError:
        _fail(PublicationPreparationCode.PUB_GOLDEN_MISMATCH)
    except AdapterEvidenceResourceError:
        _fail(PublicationPreparationCode.PUB_INPUT_RESOURCE)
    except Exception:
        _fail(PublicationPreparationCode.PUB_RECOMPUTATION_MISMATCH)

    _validate_case_inventory(candidates, profile.case_expectations)
    if hostile_inventory != profile.hostile_control_expectations:
        _fail(PublicationPreparationCode.PUB_HOSTILE_INVENTORY_MISMATCH)
    for candidate in candidates:
        _check_case_public_ids(candidate.snapshot, registry)
    _validate_identity_surfaces(candidates)

    frozen_cases = []
    for candidate in candidates:
        fresh_run = _fresh_run(candidate.snapshot, registry)
        _validate_case_recomputations(candidate.snapshot, fresh_run)
        frozen_cases.append(_frozen_case(candidate, fresh_run))
        _require_request_unchanged(
            request,
            authority_input,
            binding_authority=binding_authority,
            bindings=bindings,
            registry=registry,
            cases=cases,
            hostiles=hostiles,
        )

    try:
        final_adapter_surfaces = tuple(
            _adapter_surface_key(candidate.snapshot.adapter)
            for candidate in candidates
        )
    except Exception:
        _fail(PublicationPreparationCode.PUB_POSTMUTATION)
    if final_adapter_surfaces != tuple(
        _expected_adapter_surface(candidate.snapshot)
        for candidate in candidates
    ):
        _fail(PublicationPreparationCode.PUB_POSTMUTATION)
    _require_request_unchanged(
        request,
        authority_input,
        binding_authority=binding_authority,
        bindings=bindings,
        registry=registry,
        cases=cases,
        hostiles=hostiles,
    )

    sorted_hostiles = tuple(sorted(hostiles, key=lambda item: item.control_id))
    return FrozenDecisionPublicationInputV1(
        candidate_status=PUBLICATION_DEVELOPMENT_STATUS,
        golden_oracle_execution_status=(
            DECISION_GOLDEN_ORACLE_EXECUTION_STATUS
        ),
        bindings=bindings,
        public_ids=registry,
        binding_authority=binding_authority,
        cases=tuple(frozen_cases),
        hostile_controls=sorted_hostiles,
    )


def freeze_decision_publication_input(
    request: DecisionPublicationFreezeInputV1,
    authority_input: ApprovedPublicationAuthorityInputV1,
) -> FrozenDecisionPublicationInputV1:
    """Freeze one V2 candidate through the closed public error surface."""

    if type(request) is not DecisionPublicationFreezeInputV1:
        _fail(PublicationPreparationCode.PUB_INPUT_TYPE)
    if type(authority_input) is not ApprovedPublicationAuthorityInputV1:
        _fail(PublicationPreparationCode.PUB_INPUT_TYPE)
    try:
        return _freeze_decision_publication_input(request, authority_input)
    except PublicationPreparationError:
        raise
    except AdapterEvidenceResourceError:
        _fail(PublicationPreparationCode.PUB_INPUT_RESOURCE)
    except Exception:
        _fail(PublicationPreparationCode.INTERNAL_ERROR)


__all__ = [
    "DECISION_GOLDEN_ORACLE_EXECUTION_STATUS",
    "FrozenDecisionDetachedCaseV1",
    "FrozenDecisionPublicationInputV1",
    "MAXIMUM_DECISION_AGGREGATE_NODES",
    "MAXIMUM_DECISION_REVALIDATION_WORK_BYTES",
    "freeze_decision_publication_input",
]
