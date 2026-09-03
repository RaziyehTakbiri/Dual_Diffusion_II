"""Types-only authority boundary for decision-capable Phase-D publication.

These types describe independently custodied profile, golden, and binding
material.  Constructors enforce only exact closed shapes and cheap resource
bounds.  They perform no JSON parsing, hashing, filesystem access, adapter
callback, publication, or gate decision.

The module is intentionally not re-exported from :mod:`heterodiff.data`.
Possessing one of these Python objects is not evidence of independent custody;
the validation layer must authenticate exact bytes against an out-of-band
anchor and recompute every expectation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Tuple

from heterodiff.events import EventConfiguration

from .adapter_conformance_execution_guard import (
    MAXIMUM_CAPTURED_OUTPUT_BYTES,
    PEAK_RSS_LIMIT_BYTES,
    WALL_TIME_LIMIT_NANOSECONDS,
)
from .adapter_conformance_runner import ConformanceRun
from .adapter_contract import AdapterDescriptor, SplitManifest
from .adapter_evidence import (
    CompleteAdaptedEventSample,
    ExpectedAdapterEvidence,
    MAXIMUM_SOURCE_BYTES,
)
from .adapter_publication_types import (
    MAXIMUM_HOSTILE_CONTROL_RECEIPTS,
    MAXIMUM_HOSTILE_INPUT_BYTES,
    MAXIMUM_PUBLICATION_CASES,
    MAXIMUM_REGISTRY_VALUE_BYTES,
    MAXIMUM_SINGLE_BINDING_BYTES,
    MAXIMUM_TEST_NODE_BYTES,
    PublicIdentifierRegistryV1,
    PublicationBindingInputV1,
    PublicationTypeError,
)


APPROVED_PUBLICATION_PROFILE_ARTIFACT_TYPE = (
    "heterodiff.adapter.approved-publication-profile.v1"
)
APPROVED_PUBLICATION_PROFILE_ID = "heterodiff-adapter-publication-v1"
APPROVED_PUBLICATION_STATUS = "A9_1_APPROVED_FOR_EXECUTION"
EXECUTION_GUARD_INPUT_BINDING_FORMAT_ID = (
    "execution-guard-input-binding-v1"
)
INDEPENDENT_GOLDEN_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.independent-golden-receipt.v1"
)
GOLDEN_ORACLE_REGISTRY_ARTIFACT_TYPE = (
    "heterodiff.adapter.golden-oracle-registry.v1"
)
DECISION_EXECUTION_INPUT_SET_ARTIFACT_TYPE = (
    "heterodiff.adapter.decision-execution-input-set.v1"
)
DECISION_EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE = (
    "heterodiff.adapter.decision-execution-guard-run-manifest.v1"
)
DECISION_EXECUTION_GUARD_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.decision-execution-guard-receipt.v1"
)

MAXIMUM_APPROVED_PROFILE_BYTES = 4 * 1024 * 1024
MAXIMUM_INDEPENDENT_GOLDEN_RECEIPT_BYTES = 128 * 1024
MAXIMUM_ORACLE_SOURCE_BYTES = 1024 * 1024
MAXIMUM_EXPECTED_CONFIGURATION_BYTES = 16 * 1024 * 1024
MAXIMUM_ADDRESS_SPACE_LIMIT_BYTES = (1 << 53) - 1
MAXIMUM_DECISION_EXECUTION_INVOCATION_FIELD_BYTES = 1024 * 1024
MAXIMUM_DECISION_EXECUTION_INVOCATION_BYTES = 4 * 1024 * 1024
MAXIMUM_DECISION_GUARD_MANIFEST_BYTES = 128 * 1024

_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_ADAPTER_ID_RE = re.compile(
    r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$"
)
_VERSION_RE = re.compile(r"^[1-9][0-9]{0,9}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256(value: object, *, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise PublicationTypeError(
            name + " must be a lowercase 64-character SHA-256 digest"
        )
    return value


def _token(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be an exact string")
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        raise PublicationTypeError(name + " must contain only ASCII") from None
    if (
        not encoded
        or len(encoded) > MAXIMUM_REGISTRY_VALUE_BYTES
        or _TOKEN_RE.fullmatch(value) is None
    ):
        raise PublicationTypeError(name + " is not a canonical token")
    return value


def _adapter_identity(adapter_id: object, adapter_version: object) -> None:
    if (
        type(adapter_id) is not str
        or _ADAPTER_ID_RE.fullmatch(adapter_id) is None
    ):
        raise PublicationTypeError("adapter_id is not canonical")
    if (
        type(adapter_version) is not str
        or _VERSION_RE.fullmatch(adapter_version) is None
    ):
        raise PublicationTypeError("adapter_version is not canonical")


def _bounded_integer(
    value: object,
    *,
    name: str,
    maximum: int,
    allow_zero: bool = True,
) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < 0 or value > maximum or (value == 0 and not allow_zero):
        raise PublicationTypeError(name + " is outside its exact bound")
    return value


def _exact_bytes(
    value: object,
    *,
    name: str,
    maximum: int,
) -> bytes:
    if type(value) is not bytes:
        raise TypeError(name + " must be exact immutable bytes")
    if not value or len(value) > maximum:
        raise PublicationTypeError(name + " is outside its byte bound")
    return value


def _sorted_tokens(value: object, *, name: str) -> Tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise TypeError(name + " must be a nonempty exact tuple")
    result = tuple(_token(item, name=name) for item in value)
    if result != tuple(sorted(set(result))):
        raise PublicationTypeError(name + " must be sorted and duplicate-free")
    return result


_BINDING_DIGEST_FIELDS = (
    "a9_1_sha256",
    "contract_core_sha256",
    "dependency_lock_sha256",
    "environment_manifest_sha256",
    "execution_guard_source_sha256",
    "gate_spec_sha256",
    "interpreter_executable_sha256",
    "oracle_registry_sha256",
    "phase_c_report_sha256",
    "phase_d_spec_sha256",
    "public_id_registry_sha256",
    "publisher_source_sha256",
    "source_tree_archive_sha256",
    "source_tree_manifest_sha256",
    "test_inventory_sha256",
    "verifier_source_sha256",
)


def _validate_binding_fields(value: object) -> None:
    for name in _BINDING_DIGEST_FIELDS:
        _sha256(getattr(value, name), name=name)
    _token(getattr(value, "contract_id"), name="contract_id")
    _token(getattr(value, "gate_id"), name="gate_id")


@dataclass(frozen=True)
class PublicationBindingExpectationV1:
    """The 18 request-derived fields authenticated by one approved profile."""

    a9_1_sha256: str
    contract_core_sha256: str
    contract_id: str
    dependency_lock_sha256: str
    environment_manifest_sha256: str
    execution_guard_source_sha256: str
    gate_id: str
    gate_spec_sha256: str
    interpreter_executable_sha256: str
    oracle_registry_sha256: str
    phase_c_report_sha256: str
    phase_d_spec_sha256: str
    public_id_registry_sha256: str
    publisher_source_sha256: str
    source_tree_archive_sha256: str
    source_tree_manifest_sha256: str
    test_inventory_sha256: str
    verifier_source_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not PublicationBindingExpectationV1:
            raise TypeError("binding expectation must be exact")
        _validate_binding_fields(self)


@dataclass(frozen=True)
class PublicationBindingSetV1:
    """Final 19-field public binding set with external profile authority."""

    a9_1_sha256: str
    approved_profile_sha256: str
    contract_core_sha256: str
    contract_id: str
    dependency_lock_sha256: str
    environment_manifest_sha256: str
    execution_guard_source_sha256: str
    gate_id: str
    gate_spec_sha256: str
    interpreter_executable_sha256: str
    oracle_registry_sha256: str
    phase_c_report_sha256: str
    phase_d_spec_sha256: str
    public_id_registry_sha256: str
    publisher_source_sha256: str
    source_tree_archive_sha256: str
    source_tree_manifest_sha256: str
    test_inventory_sha256: str
    verifier_source_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not PublicationBindingSetV1:
            raise TypeError("publication binding set must be exact")
        _validate_binding_fields(self)
        _sha256(self.approved_profile_sha256, name="approved_profile_sha256")


@dataclass(frozen=True)
class ApprovedCaseExpectationV1:
    """One exact pre-run case expectation authenticated by the profile."""

    adapter_id: str
    adapter_version: str
    case_ordinal: int
    complete_sample_commitment_sha256: str
    conformance_run_sha256: str
    descriptor_sha256: str
    expected_configuration_sha256: str
    expected_evidence_sha256: str
    independent_golden_receipt_sha256: str
    native_observation_sha256: str
    sample_root_sha256: str
    source_sha256: str
    split_manifest_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not ApprovedCaseExpectationV1:
            raise TypeError("approved case expectation must be exact")
        _adapter_identity(self.adapter_id, self.adapter_version)
        _bounded_integer(
            self.case_ordinal,
            name="case_ordinal",
            maximum=MAXIMUM_PUBLICATION_CASES - 1,
        )
        for name in self.__dataclass_fields__:
            if name.endswith("_sha256"):
                _sha256(getattr(self, name), name=name)


@dataclass(frozen=True)
class HostileControlRequirementV1:
    """One exact structural-injection control required by the profile."""

    attack_kind_id: str
    control_id: str
    error_code: str
    expected_stage_id: str
    hostile_control_receipt_sha256: str
    input_sha256: str
    origin_class_id: str
    sink_field_id: str
    status_id: str
    test_node_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not HostileControlRequirementV1:
            raise TypeError("hostile control requirement must be exact")
        for name in (
            "attack_kind_id",
            "control_id",
            "error_code",
            "expected_stage_id",
            "origin_class_id",
            "sink_field_id",
            "status_id",
        ):
            _token(getattr(self, name), name=name)
        for name in (
            "hostile_control_receipt_sha256",
            "input_sha256",
            "test_node_sha256",
        ):
            _sha256(getattr(self, name), name=name)


@dataclass(frozen=True)
class ApprovedExecutionPolicyV1:
    """Decision execution policy fields that are not binding-derived."""

    address_space_limit_bytes: int
    address_space_limit_method_id: str
    allowed_execution_status_ids: Tuple[str, ...]
    argv_sha256: str
    authorized_write_root_sha256: str
    clock_method_id: str
    containment_policy_sha256: str
    cwd_launch_method_id: str
    environment_sha256: str
    execution_backend_id: str
    filesystem_confinement_id: str
    guard_implementation_status_id: str
    output_capture_method_id: str
    peak_rss_method_id: str
    process_containment_id: str
    source_binding_format_id: str
    working_directory_sha256: str
    decision_eligible_required: bool = field(default=True, init=False)
    managed_process_group_quiescence_required: bool = field(
        default=True,
        init=False,
    )
    output_complete_required: bool = field(default=True, init=False)
    output_limit_bytes: int = field(
        default=MAXIMUM_CAPTURED_OUTPUT_BYTES,
        init=False,
    )
    peak_rss_limit_bytes: int = field(
        default=PEAK_RSS_LIMIT_BYTES,
        init=False,
    )
    wall_time_limit_nanoseconds: int = field(
        default=WALL_TIME_LIMIT_NANOSECONDS,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not ApprovedExecutionPolicyV1:
            raise TypeError("approved execution policy must be exact")
        _bounded_integer(
            self.address_space_limit_bytes,
            name="address_space_limit_bytes",
            maximum=MAXIMUM_ADDRESS_SPACE_LIMIT_BYTES,
            allow_zero=False,
        )
        statuses = _sorted_tokens(
            self.allowed_execution_status_ids,
            name="allowed_execution_status_ids",
        )
        if "pass" not in statuses:
            raise PublicationTypeError(
                "allowed execution statuses must include pass"
            )
        object.__setattr__(self, "allowed_execution_status_ids", statuses)
        for name in (
            "argv_sha256",
            "authorized_write_root_sha256",
            "containment_policy_sha256",
            "environment_sha256",
            "working_directory_sha256",
        ):
            _sha256(getattr(self, name), name=name)
        for name in (
            "address_space_limit_method_id",
            "clock_method_id",
            "cwd_launch_method_id",
            "execution_backend_id",
            "filesystem_confinement_id",
            "guard_implementation_status_id",
            "output_capture_method_id",
            "peak_rss_method_id",
            "process_containment_id",
            "source_binding_format_id",
        ):
            _token(getattr(self, name), name=name)
        if self.source_binding_format_id != EXECUTION_GUARD_INPUT_BINDING_FORMAT_ID:
            raise PublicationTypeError(
                "source binding format is not the fixed V1 format"
            )


@dataclass(frozen=True)
class DecisionExecutionInvocationV1:
    """Exact pre-run byte manifests whose digests the policy approves."""

    argv_bytes: bytes
    authorized_write_root_bytes: bytes
    containment_policy_bytes: bytes
    environment_bytes: bytes
    working_directory_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not DecisionExecutionInvocationV1:
            raise TypeError("decision execution invocation must be exact")
        total = 0
        for name in self.__dataclass_fields__:
            value = _exact_bytes(
                getattr(self, name),
                name=name,
                maximum=MAXIMUM_DECISION_EXECUTION_INVOCATION_FIELD_BYTES,
            )
            total += len(value)
            if total > MAXIMUM_DECISION_EXECUTION_INVOCATION_BYTES:
                raise PublicationTypeError(
                    "decision execution invocation exceeds its byte bound"
                )


@dataclass(frozen=True)
class DecisionExecutionGuardRunManifestV1:
    """Exact final pre-run manifest; it contains no outcome or receipt."""

    address_space_limit_bytes: int
    address_space_limit_method_id: str
    allowed_execution_status_ids: Tuple[str, ...]
    argv_sha256: str
    authorized_write_root_sha256: str
    clock_method_id: str
    containment_policy_sha256: str
    cwd_launch_method_id: str
    dependency_lock_sha256: str
    environment_manifest_sha256: str
    environment_sha256: str
    execution_backend_id: str
    execution_guard_source_sha256: str
    execution_input_set_sha256: str
    filesystem_confinement_id: str
    guard_implementation_status_id: str
    interpreter_executable_sha256: str
    output_capture_method_id: str
    peak_rss_method_id: str
    process_containment_id: str
    publication_binding_set_sha256: str
    source_binding_format_id: str
    source_tree_archive_sha256: str
    source_tree_manifest_sha256: str
    test_inventory_sha256: str
    working_directory_sha256: str
    artifact_type: str = field(
        default=DECISION_EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE,
        init=False,
    )
    decision_eligible_required: bool = field(default=True, init=False)
    format_version: str = field(default="1", init=False)
    managed_process_group_quiescence_required: bool = field(
        default=True,
        init=False,
    )
    output_complete_required: bool = field(default=True, init=False)
    output_limit_bytes: int = field(
        default=MAXIMUM_CAPTURED_OUTPUT_BYTES,
        init=False,
    )
    peak_rss_limit_bytes: int = field(
        default=PEAK_RSS_LIMIT_BYTES,
        init=False,
    )
    wall_time_limit_nanoseconds: int = field(
        default=WALL_TIME_LIMIT_NANOSECONDS,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not DecisionExecutionGuardRunManifestV1:
            raise TypeError("decision execution guard manifest must be exact")
        _bounded_integer(
            self.address_space_limit_bytes,
            name="address_space_limit_bytes",
            maximum=MAXIMUM_ADDRESS_SPACE_LIMIT_BYTES,
            allow_zero=False,
        )
        statuses = _sorted_tokens(
            self.allowed_execution_status_ids,
            name="allowed_execution_status_ids",
        )
        if "pass" not in statuses:
            raise PublicationTypeError(
                "allowed execution statuses must include pass"
            )
        object.__setattr__(self, "allowed_execution_status_ids", statuses)
        for name in (
            "argv_sha256",
            "authorized_write_root_sha256",
            "containment_policy_sha256",
            "dependency_lock_sha256",
            "environment_manifest_sha256",
            "environment_sha256",
            "execution_guard_source_sha256",
            "execution_input_set_sha256",
            "interpreter_executable_sha256",
            "publication_binding_set_sha256",
            "source_tree_archive_sha256",
            "source_tree_manifest_sha256",
            "test_inventory_sha256",
            "working_directory_sha256",
        ):
            _sha256(getattr(self, name), name=name)
        for name in (
            "address_space_limit_method_id",
            "clock_method_id",
            "cwd_launch_method_id",
            "execution_backend_id",
            "filesystem_confinement_id",
            "guard_implementation_status_id",
            "output_capture_method_id",
            "peak_rss_method_id",
            "process_containment_id",
            "source_binding_format_id",
        ):
            _token(getattr(self, name), name=name)
        if self.source_binding_format_id != EXECUTION_GUARD_INPUT_BINDING_FORMAT_ID:
            raise PublicationTypeError(
                "source binding format is not the fixed V1 format"
            )


@dataclass(frozen=True)
class ApprovedPublicationProfileV1:
    """Parsed exact profile; authority still comes only from its anchor."""

    a9_1_byte_count: int
    binding_expectations: PublicationBindingExpectationV1
    case_expectations: Tuple[ApprovedCaseExpectationV1, ...]
    execution_policy: ApprovedExecutionPolicyV1
    hostile_control_expectations: Tuple[HostileControlRequirementV1, ...]
    approval_status_id: str = field(
        default=APPROVED_PUBLICATION_STATUS,
        init=False,
    )
    artifact_type: str = field(
        default=APPROVED_PUBLICATION_PROFILE_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)
    profile_id: str = field(
        default=APPROVED_PUBLICATION_PROFILE_ID,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not ApprovedPublicationProfileV1:
            raise TypeError("approved publication profile must be exact")
        _bounded_integer(
            self.a9_1_byte_count,
            name="a9_1_byte_count",
            maximum=MAXIMUM_SINGLE_BINDING_BYTES,
            allow_zero=False,
        )
        if type(self.binding_expectations) is not PublicationBindingExpectationV1:
            raise TypeError("binding_expectations must be exact")
        if type(self.execution_policy) is not ApprovedExecutionPolicyV1:
            raise TypeError("execution_policy must be exact")
        cases = self.case_expectations
        if type(cases) is not tuple or not cases:
            raise TypeError("case_expectations must be a nonempty exact tuple")
        if len(cases) > MAXIMUM_PUBLICATION_CASES:
            raise PublicationTypeError("too many approved case expectations")
        if any(type(item) is not ApprovedCaseExpectationV1 for item in cases):
            raise TypeError("approved case expectations must have exact types")
        case_keys = tuple(
            (
                item.sample_root_sha256,
                item.expected_evidence_sha256,
                item.adapter_id,
            )
            for item in cases
        )
        sample_roots = tuple(item.sample_root_sha256 for item in cases)
        if len(set(sample_roots)) != len(sample_roots):
            raise PublicationTypeError(
                "approved case sample roots must be unique"
            )
        if case_keys != tuple(sorted(set(case_keys))):
            raise PublicationTypeError(
                "approved case expectations are not canonically ordered"
            )
        if tuple(item.case_ordinal for item in cases) != tuple(range(len(cases))):
            raise PublicationTypeError(
                "approved case ordinals must equal canonical positions"
            )
        hostiles = self.hostile_control_expectations
        if type(hostiles) is not tuple or not hostiles:
            raise TypeError(
                "hostile_control_expectations must be a nonempty exact tuple"
            )
        if len(hostiles) > MAXIMUM_HOSTILE_CONTROL_RECEIPTS:
            raise PublicationTypeError("too many hostile control expectations")
        if any(type(item) is not HostileControlRequirementV1 for item in hostiles):
            raise TypeError("hostile control expectations must have exact types")
        hostile_ids = tuple(item.control_id for item in hostiles)
        if hostile_ids != tuple(sorted(set(hostile_ids))):
            raise PublicationTypeError(
                "hostile control expectations must be sorted and unique"
            )


@dataclass(frozen=True)
class ApprovedPublicationProfileAnchorV1:
    """Out-of-band procedural trust root for exact profile bytes."""

    profile_byte_count: int
    profile_file_sha256: str
    profile_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not ApprovedPublicationProfileAnchorV1:
            raise TypeError("approved profile anchor must be exact")
        _bounded_integer(
            self.profile_byte_count,
            name="profile_byte_count",
            maximum=MAXIMUM_APPROVED_PROFILE_BYTES,
            allow_zero=False,
        )
        _sha256(self.profile_file_sha256, name="profile_file_sha256")
        _sha256(self.profile_sha256, name="profile_sha256")


@dataclass(frozen=True)
class ApprovedPublicationAuthorityInputV1:
    """Separately supplied authority bytes; never a publication-request field."""

    profile_bytes: bytes
    anchor: ApprovedPublicationProfileAnchorV1

    def __post_init__(self) -> None:
        if type(self) is not ApprovedPublicationAuthorityInputV1:
            raise TypeError("approved publication authority input must be exact")
        _exact_bytes(
            self.profile_bytes,
            name="profile_bytes",
            maximum=MAXIMUM_APPROVED_PROFILE_BYTES,
        )
        if type(self.anchor) is not ApprovedPublicationProfileAnchorV1:
            raise TypeError("approved profile anchor must be exact")


@dataclass(frozen=True)
class IndependentGoldenReceiptV1:
    """Exact typed result of an independently authored golden oracle."""

    adapter_id: str
    adapter_version: str
    descriptor_sha256: str
    expected_configuration_payload_byte_count: int
    expected_configuration_sha256: str
    expected_evidence_sha256: str
    expected_native_observation_sha256: str
    oracle_id: str
    oracle_registry_sha256: str
    oracle_source_byte_count: int
    oracle_source_sha256: str
    source_byte_count: int
    source_sha256: str
    split_manifest_sha256: str
    artifact_type: str = field(
        default=INDEPENDENT_GOLDEN_RECEIPT_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)

    def __post_init__(self) -> None:
        if type(self) is not IndependentGoldenReceiptV1:
            raise TypeError("independent golden receipt must be exact")
        _adapter_identity(self.adapter_id, self.adapter_version)
        _token(self.oracle_id, name="oracle_id")
        _bounded_integer(
            self.expected_configuration_payload_byte_count,
            name="expected_configuration_payload_byte_count",
            maximum=MAXIMUM_EXPECTED_CONFIGURATION_BYTES,
            allow_zero=False,
        )
        _bounded_integer(
            self.oracle_source_byte_count,
            name="oracle_source_byte_count",
            maximum=MAXIMUM_ORACLE_SOURCE_BYTES,
            allow_zero=False,
        )
        _bounded_integer(
            self.source_byte_count,
            name="source_byte_count",
            maximum=MAXIMUM_SINGLE_BINDING_BYTES,
            allow_zero=False,
        )
        for name in self.__dataclass_fields__:
            if name.endswith("_sha256"):
                _sha256(getattr(self, name), name=name)


@dataclass(frozen=True)
class IndependentGoldenReceiptInputV1:
    """Typed receipt, exact canonical bytes, and independently held oracle."""

    receipt: IndependentGoldenReceiptV1
    receipt_bytes: bytes
    oracle_source_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not IndependentGoldenReceiptInputV1:
            raise TypeError("independent golden receipt input must be exact")
        if type(self.receipt) is not IndependentGoldenReceiptV1:
            raise TypeError("independent golden receipt must be exact")
        _exact_bytes(
            self.receipt_bytes,
            name="receipt_bytes",
            maximum=MAXIMUM_INDEPENDENT_GOLDEN_RECEIPT_BYTES,
        )
        _exact_bytes(
            self.oracle_source_bytes,
            name="oracle_source_bytes",
            maximum=MAXIMUM_ORACLE_SOURCE_BYTES,
        )


@dataclass(frozen=True)
class VerifiedDetachedCaseInputV2:
    """Decision case input with a typed, source-custodied golden receipt."""

    adapter: object
    source_bytes: bytes
    descriptor: AdapterDescriptor
    split_manifest: SplitManifest
    complete_sample: CompleteAdaptedEventSample
    expected_evidence: ExpectedAdapterEvidence
    expected_configuration: EventConfiguration
    conformance_run: ConformanceRun
    independent_golden: IndependentGoldenReceiptInputV1

    def __post_init__(self) -> None:
        if type(self) is not VerifiedDetachedCaseInputV2:
            raise TypeError("decision detached case input must be exact")
        if self.adapter is None:
            raise TypeError("adapter must be supplied for fresh validation")
        _exact_bytes(
            self.source_bytes,
            name="source_bytes",
            maximum=MAXIMUM_SOURCE_BYTES,
        )
        for name, expected_type in (
            ("descriptor", AdapterDescriptor),
            ("split_manifest", SplitManifest),
            ("complete_sample", CompleteAdaptedEventSample),
            ("expected_evidence", ExpectedAdapterEvidence),
            ("expected_configuration", EventConfiguration),
            ("conformance_run", ConformanceRun),
            ("independent_golden", IndependentGoldenReceiptInputV1),
        ):
            if type(getattr(self, name)) is not expected_type:
                raise TypeError(name + " must have its exact decision type")


@dataclass(frozen=True)
class DecisionHostileControlInputV1:
    """Exact decision hostile node with profile-authenticated semantics."""

    attack_kind_id: str
    control_id: str
    error_code: str
    expected_stage_id: str
    input_bytes: bytes
    origin_class_id: str
    sink_field_id: str
    status_id: str
    test_node_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not DecisionHostileControlInputV1:
            raise TypeError("decision hostile control input must be exact")
        for name in (
            "attack_kind_id",
            "control_id",
            "error_code",
            "expected_stage_id",
            "origin_class_id",
            "sink_field_id",
            "status_id",
        ):
            _token(getattr(self, name), name=name)
        _exact_bytes(
            self.input_bytes,
            name="input_bytes",
            maximum=MAXIMUM_HOSTILE_INPUT_BYTES,
        )
        _exact_bytes(
            self.test_node_bytes,
            name="test_node_bytes",
            maximum=MAXIMUM_TEST_NODE_BYTES,
        )


@dataclass(frozen=True)
class DecisionPublicationFreezeInputV1:
    """Pre-run cases and controls; external authority stays separate."""

    bindings: PublicationBindingInputV1
    public_ids: PublicIdentifierRegistryV1
    cases: Tuple[VerifiedDetachedCaseInputV2, ...]
    hostile_controls: Tuple[DecisionHostileControlInputV1, ...]

    def __post_init__(self) -> None:
        if type(self) is not DecisionPublicationFreezeInputV1:
            raise TypeError("decision publication freeze input must be exact")
        if type(self.bindings) is not PublicationBindingInputV1:
            raise TypeError("decision publication bindings must be exact")
        if type(self.public_ids) is not PublicIdentifierRegistryV1:
            raise TypeError("decision public identifiers must be exact")
        if type(self.cases) is not tuple or not self.cases:
            raise TypeError("decision cases must be a nonempty exact tuple")
        if len(self.cases) > MAXIMUM_PUBLICATION_CASES:
            raise PublicationTypeError("too many decision publication cases")
        if any(type(item) is not VerifiedDetachedCaseInputV2 for item in self.cases):
            raise TypeError("decision cases must have exact V2 types")
        if type(self.hostile_controls) is not tuple or not self.hostile_controls:
            raise TypeError(
                "decision hostile controls must be a nonempty exact tuple"
            )
        if len(self.hostile_controls) > MAXIMUM_HOSTILE_CONTROL_RECEIPTS:
            raise PublicationTypeError("too many decision hostile controls")
        if any(
            type(item) is not DecisionHostileControlInputV1
            for item in self.hostile_controls
        ):
            raise TypeError("decision hostile controls must have exact types")


@dataclass(frozen=True)
class GoldenOracleRegistryEntryV1:
    """One oracle source identity plus its frozen independence bans."""

    oracle_id: str
    oracle_source_byte_count: int
    oracle_source_sha256: str
    forbidden_import_ids: Tuple[str, ...]
    forbidden_name_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self) is not GoldenOracleRegistryEntryV1:
            raise TypeError("golden oracle registry entry must be exact")
        _token(self.oracle_id, name="oracle_id")
        _bounded_integer(
            self.oracle_source_byte_count,
            name="oracle_source_byte_count",
            maximum=MAXIMUM_ORACLE_SOURCE_BYTES,
            allow_zero=False,
        )
        _sha256(self.oracle_source_sha256, name="oracle_source_sha256")
        for name in ("forbidden_import_ids", "forbidden_name_ids"):
            values = _sorted_tokens(getattr(self, name), name=name)
            object.__setattr__(self, name, values)


@dataclass(frozen=True)
class GoldenOracleRegistryV1:
    """Canonical oracle-ID to exact independently authored source registry."""

    oracles: Tuple[GoldenOracleRegistryEntryV1, ...]
    artifact_type: str = field(
        default=GOLDEN_ORACLE_REGISTRY_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)

    def __post_init__(self) -> None:
        if type(self) is not GoldenOracleRegistryV1:
            raise TypeError("golden oracle registry must be exact")
        if type(self.oracles) is not tuple or not self.oracles:
            raise TypeError("oracles must be a nonempty exact tuple")
        if len(self.oracles) > MAXIMUM_PUBLICATION_CASES:
            raise PublicationTypeError("too many golden oracle entries")
        if any(type(item) is not GoldenOracleRegistryEntryV1 for item in self.oracles):
            raise TypeError("golden oracle entries must have exact types")
        oracle_ids = tuple(item.oracle_id for item in self.oracles)
        if oracle_ids != tuple(sorted(set(oracle_ids))):
            raise PublicationTypeError(
                "golden oracle entries must be sorted and unique"
            )


__all__ = [
    "APPROVED_PUBLICATION_PROFILE_ARTIFACT_TYPE",
    "APPROVED_PUBLICATION_PROFILE_ID",
    "APPROVED_PUBLICATION_STATUS",
    "ApprovedCaseExpectationV1",
    "ApprovedExecutionPolicyV1",
    "ApprovedPublicationAuthorityInputV1",
    "ApprovedPublicationProfileAnchorV1",
    "ApprovedPublicationProfileV1",
    "DECISION_EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE",
    "DECISION_EXECUTION_GUARD_RECEIPT_ARTIFACT_TYPE",
    "DECISION_EXECUTION_INPUT_SET_ARTIFACT_TYPE",
    "DecisionExecutionGuardRunManifestV1",
    "DecisionExecutionInvocationV1",
    "DecisionHostileControlInputV1",
    "DecisionPublicationFreezeInputV1",
    "EXECUTION_GUARD_INPUT_BINDING_FORMAT_ID",
    "HostileControlRequirementV1",
    "GOLDEN_ORACLE_REGISTRY_ARTIFACT_TYPE",
    "GoldenOracleRegistryEntryV1",
    "GoldenOracleRegistryV1",
    "INDEPENDENT_GOLDEN_RECEIPT_ARTIFACT_TYPE",
    "IndependentGoldenReceiptInputV1",
    "IndependentGoldenReceiptV1",
    "MAXIMUM_APPROVED_PROFILE_BYTES",
    "MAXIMUM_DECISION_EXECUTION_INVOCATION_BYTES",
    "MAXIMUM_DECISION_EXECUTION_INVOCATION_FIELD_BYTES",
    "MAXIMUM_DECISION_GUARD_MANIFEST_BYTES",
    "MAXIMUM_INDEPENDENT_GOLDEN_RECEIPT_BYTES",
    "MAXIMUM_ORACLE_SOURCE_BYTES",
    "PublicationBindingExpectationV1",
    "PublicationBindingSetV1",
    "VerifiedDetachedCaseInputV2",
]
