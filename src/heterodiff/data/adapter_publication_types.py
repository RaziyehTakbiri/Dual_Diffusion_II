"""Types-only transport boundary for Phase-D adapter publication.

This module deliberately performs no serialization, hashing, filesystem I/O,
subprocess execution, adapter callback, or gate decision.  Its constructors
only reject malformed outer shapes and cheaply bounded inputs.  The later
freezing layer must treat every accepted value as untrusted, take fresh
snapshots, re-run detached conformance, and recompute every commitment.

The implementation status is development-only.  No object in this module can
represent ``ADAPTER-CONFORMANCE-GO``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Tuple

from heterodiff.events import EventConfiguration

from .adapter_conformance_execution_guard import (
    MAXIMUM_CAPTURED_OUTPUT_BYTES,
    PEAK_RSS_LIMIT_BYTES,
    WALL_TIME_LIMIT_NANOSECONDS,
    ExecutionReceipt,
)
from .adapter_conformance_runner import ConformanceRun
from .adapter_contract import AdapterDescriptor, SplitManifest
from .adapter_evidence import (
    CompleteAdaptedEventSample,
    ExpectedAdapterEvidence,
    MAXIMUM_SOURCE_BYTES,
)


PUBLICATION_IMPLEMENTATION_STATUS = "DEVELOPMENT_ONLY"
PUBLICATION_DECISION_STATUS = "NOT_MADE_BY_PUBLISHER"
PUBLICATION_DEVELOPMENT_STATUS = "ADAPTER-CONFORMANCE-HOLD"
VERIFIER_DECISION_STATUS = "NOT_MADE_BY_VERIFIER"
VERIFICATION_SUCCESS_STATUS = (
    "VERIFIED_SOURCE_BOUND_BYTE_IDENTICAL_PUBLIC_AND_PRIVATE"
)

PUBLIC_CORE_ARTIFACT_TYPE = (
    "heterodiff.adapter.development-public-core.v1"
)
PUBLIC_CORE_ARTIFACT_ID = "public-core"
PRIVATE_ENVELOPE_ARTIFACT_TYPE = (
    "heterodiff.adapter.development-private-envelope.v1"
)
PRIVATE_ENVELOPE_ARTIFACT_ID = "private-envelope"
PUBLICATION_MANIFEST_ARTIFACT_TYPE = (
    "heterodiff.adapter.development-publication-manifest.v1"
)
VERIFICATION_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.verification-receipt.v1"
)
EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE = (
    "heterodiff.adapter.development-execution-guard-run-manifest.v1"
)

MAXIMUM_PUBLICATION_CASES = 4096
MAXIMUM_HOSTILE_CONTROL_RECEIPTS = 1024
MAXIMUM_REGISTRY_VALUES_PER_CATEGORY = 4096
MAXIMUM_REGISTRY_VALUE_BYTES = 128
MAXIMUM_REGISTRY_REASON_BYTES = 256
MAXIMUM_REGISTRY_BYTES = 8 * 1024 * 1024
MAXIMUM_SINGLE_BINDING_BYTES = 32 * 1024 * 1024
MAXIMUM_TOTAL_BINDING_BYTES = 64 * 1024 * 1024
MAXIMUM_GOLDEN_DEFINITION_BYTES = 128 * 1024
MAXIMUM_HOSTILE_INPUT_BYTES = 1024 * 1024
MAXIMUM_TEST_NODE_BYTES = 1024 * 1024
MAXIMUM_PUBLIC_ARTIFACT_BYTES = 2 * 1024 * 1024
MAXIMUM_PRIVATE_ARTIFACT_BYTES = 16 * 1024 * 1024
PUBLIC_COUNT_IDS = (
    "advertised_representations",
    "conformance_checks",
)

_REGISTRY_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_ADAPTER_ID_RE = re.compile(
    r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$"
)
_VERSION_RE = re.compile(r"^[1-9][0-9]{0,9}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class PublicationTypeError(ValueError):
    """A types-only publication input violates its closed outer contract."""


class PublicationCommitState(str, Enum):
    """Publication visibility/durability state; neither member decides a gate."""

    PUBLISHED_DURABLE = "PUBLISHED_DURABLE"
    PUBLISHED_DURABILITY_UNCONFIRMED = (
        "PUBLISHED_DURABILITY_UNCONFIRMED"
    )


def _exact_bytes(
    value: object,
    *,
    name: str,
    maximum: int,
    allow_empty: bool = False,
) -> bytes:
    if type(value) is not bytes:
        raise TypeError(name + " must be exact immutable bytes")
    if not value and not allow_empty:
        raise PublicationTypeError(name + " must not be empty")
    if len(value) > maximum:
        raise PublicationTypeError(name + " exceeds its byte ceiling")
    return value


def _sha256(value: object, *, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise PublicationTypeError(
            name + " must be a lowercase 64-character SHA-256 digest"
        )
    return value


def _registry_token(
    value: object,
    *,
    name: str,
    maximum: int = MAXIMUM_REGISTRY_VALUE_BYTES,
) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be an exact string")
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        raise PublicationTypeError(name + " must contain only ASCII") from None
    if (
        not encoded
        or len(encoded) > maximum
        or _REGISTRY_TOKEN_RE.fullmatch(value) is None
    ):
        raise PublicationTypeError(name + " is not a canonical registry token")
    return value


def _token_tuple(
    values: object,
    *,
    name: str,
    required: Tuple[str, ...] = (),
    allow_empty: bool = False,
    maximum: int = MAXIMUM_REGISTRY_VALUE_BYTES,
) -> Tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if not values and not allow_empty:
        raise PublicationTypeError(name + " must not be empty")
    if len(values) > MAXIMUM_REGISTRY_VALUES_PER_CATEGORY:
        raise PublicationTypeError(name + " exceeds its value ceiling")
    result = tuple(
        _registry_token(value, name=name, maximum=maximum)
        for value in values
    )
    if result != tuple(sorted(set(result))):
        raise PublicationTypeError(name + " must be sorted and duplicate-free")
    if any(value not in result for value in required):
        raise PublicationTypeError(name + " omits a required fixed token")
    return result


@dataclass(frozen=True)
class PublicAdapterIdentityV1:
    """One allowlisted adapter ID/version pair."""

    adapter_id: str
    adapter_version: str

    def __post_init__(self) -> None:
        if type(self) is not PublicAdapterIdentityV1:
            raise TypeError("public adapter identity must be exact")
        if type(self.adapter_id) is not str:
            raise TypeError("adapter_id must be an exact string")
        try:
            encoded = self.adapter_id.encode("ascii", "strict")
        except UnicodeError:
            raise PublicationTypeError(
                "adapter_id must contain only ASCII"
            ) from None
        if (
            len(encoded) > MAXIMUM_REGISTRY_VALUE_BYTES
            or _ADAPTER_ID_RE.fullmatch(self.adapter_id) is None
        ):
            raise PublicationTypeError("adapter_id is not canonical")
        if (
            type(self.adapter_version) is not str
            or _VERSION_RE.fullmatch(self.adapter_version) is None
        ):
            raise PublicationTypeError("adapter_version is not canonical")


@dataclass(frozen=True)
class PublicIdentifierRegistryV1:
    """Category-separated public vocabulary; no string is dynamically added."""

    artifact_ids: Tuple[str, ...]
    format_ids: Tuple[str, ...]
    gate_ids: Tuple[str, ...]
    contract_ids: Tuple[str, ...]
    publisher_decision_ids: Tuple[str, ...]
    verifier_decision_ids: Tuple[str, ...]
    development_status_ids: Tuple[str, ...]
    verification_result_ids: Tuple[str, ...]
    verification_receipt_ids: Tuple[str, ...]
    adapter_identities: Tuple[PublicAdapterIdentityV1, ...]
    capability_ids: Tuple[str, ...]
    time_measure_ids: Tuple[str, ...]
    multiplicity_ids: Tuple[str, ...]
    representation_ids: Tuple[str, ...]
    check_ids: Tuple[str, ...]
    plan_mode_ids: Tuple[str, ...]
    terminal_status_ids: Tuple[str, ...]
    not_applicable_reason_ids: Tuple[str, ...]
    coverage_exclusion_reason_ids: Tuple[str, ...]
    censor_reason_ids: Tuple[str, ...]
    hostile_control_ids: Tuple[str, ...]
    rejection_code_ids: Tuple[str, ...]
    hostile_status_ids: Tuple[str, ...]
    count_ids: Tuple[str, ...]
    resource_ids: Tuple[str, ...]
    unit_ids: Tuple[str, ...]
    wall_time_method_ids: Tuple[str, ...]
    peak_rss_method_ids: Tuple[str, ...]
    resource_status_ids: Tuple[str, ...]
    execution_status_ids: Tuple[str, ...]
    execution_backend_ids: Tuple[str, ...]
    cwd_launch_method_ids: Tuple[str, ...]
    process_containment_ids: Tuple[str, ...]
    filesystem_confinement_ids: Tuple[str, ...]
    output_capture_method_ids: Tuple[str, ...]
    source_binding_format_ids: Tuple[str, ...]
    guard_implementation_status_ids: Tuple[str, ...]
    address_space_limit_method_ids: Tuple[str, ...]
    allowed_claim_ids: Tuple[str, ...]
    blocked_claim_ids: Tuple[str, ...]
    claim_boundary_ids: Tuple[str, ...]
    visibility_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self) is not PublicIdentifierRegistryV1:
            raise TypeError("public identifier registry must be exact")
        fixed_requirements = {
            "artifact_ids": (
                PRIVATE_ENVELOPE_ARTIFACT_ID,
                PRIVATE_ENVELOPE_ARTIFACT_TYPE,
                PUBLIC_CORE_ARTIFACT_ID,
                PUBLICATION_MANIFEST_ARTIFACT_TYPE,
                PUBLIC_CORE_ARTIFACT_TYPE,
                EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE,
                VERIFICATION_RECEIPT_ARTIFACT_TYPE,
            ),
            "format_ids": ("1",),
            "publisher_decision_ids": (PUBLICATION_DECISION_STATUS,),
            "verifier_decision_ids": (VERIFIER_DECISION_STATUS,),
            "development_status_ids": (
                PUBLICATION_DEVELOPMENT_STATUS,
            ),
            "verification_result_ids": (VERIFICATION_SUCCESS_STATUS,),
            "verification_receipt_ids": (
                VERIFICATION_RECEIPT_ARTIFACT_TYPE,
            ),
            "representation_ids": ("NONE",),
            "not_applicable_reason_ids": ("NONE",),
            "visibility_ids": ("PRIVATE_OWNER_ONLY", "PUBLIC"),
        }
        empty_categories = {
            "coverage_exclusion_reason_ids",
            "censor_reason_ids",
        }
        singleton_categories = {
            "contract_ids",
            "gate_ids",
            "claim_boundary_ids",
        }
        exact_categories = {
            "format_ids": ("1",),
            "publisher_decision_ids": (PUBLICATION_DECISION_STATUS,),
            "verifier_decision_ids": (VERIFIER_DECISION_STATUS,),
            "development_status_ids": (PUBLICATION_DEVELOPMENT_STATUS,),
            "verification_result_ids": (VERIFICATION_SUCCESS_STATUS,),
            "verification_receipt_ids": (
                VERIFICATION_RECEIPT_ARTIFACT_TYPE,
            ),
            "visibility_ids": ("PRIVATE_OWNER_ONLY", "PUBLIC"),
        }
        total_bytes = 0
        for name in (
            "artifact_ids",
            "format_ids",
            "gate_ids",
            "contract_ids",
            "publisher_decision_ids",
            "verifier_decision_ids",
            "development_status_ids",
            "verification_result_ids",
            "verification_receipt_ids",
            "capability_ids",
            "time_measure_ids",
            "multiplicity_ids",
            "representation_ids",
            "check_ids",
            "plan_mode_ids",
            "terminal_status_ids",
            "not_applicable_reason_ids",
            "coverage_exclusion_reason_ids",
            "censor_reason_ids",
            "hostile_control_ids",
            "rejection_code_ids",
            "hostile_status_ids",
            "count_ids",
            "resource_ids",
            "unit_ids",
            "wall_time_method_ids",
            "peak_rss_method_ids",
            "resource_status_ids",
            "execution_status_ids",
            "execution_backend_ids",
            "cwd_launch_method_ids",
            "process_containment_ids",
            "filesystem_confinement_ids",
            "output_capture_method_ids",
            "source_binding_format_ids",
            "guard_implementation_status_ids",
            "address_space_limit_method_ids",
            "allowed_claim_ids",
            "blocked_claim_ids",
            "claim_boundary_ids",
            "visibility_ids",
        ):
            values = _token_tuple(
                getattr(self, name),
                name=name,
                required=fixed_requirements.get(name, ()),
                allow_empty=name in empty_categories,
                maximum=(
                    MAXIMUM_REGISTRY_REASON_BYTES
                    if name == "not_applicable_reason_ids"
                    else MAXIMUM_REGISTRY_VALUE_BYTES
                ),
            )
            object.__setattr__(self, name, values)
            if name == "count_ids" and values != PUBLIC_COUNT_IDS:
                raise PublicationTypeError(
                    "count_ids must equal the fixed privacy-safe census"
                )
            if name in singleton_categories and len(values) != 1:
                raise PublicationTypeError(
                    name + " must contain exactly one selected identifier"
                )
            if name in exact_categories and values != exact_categories[name]:
                raise PublicationTypeError(
                    name + " must equal its fixed identifier set"
                )
            total_bytes += sum(len(value.encode("ascii")) for value in values)
            if total_bytes > MAXIMUM_REGISTRY_BYTES:
                raise PublicationTypeError(
                    "public identifier registry exceeds its byte ceiling"
                )
        identities = self.adapter_identities
        if type(identities) is not tuple or not identities:
            raise TypeError("adapter_identities must be a nonempty exact tuple")
        if len(identities) > MAXIMUM_REGISTRY_VALUES_PER_CATEGORY:
            raise PublicationTypeError(
                "adapter_identities exceed their value ceiling"
            )
        if any(type(value) is not PublicAdapterIdentityV1 for value in identities):
            raise TypeError("adapter identities must have exact types")
        identity_keys = tuple(
            (value.adapter_id, value.adapter_version) for value in identities
        )
        if identity_keys != tuple(sorted(set(identity_keys))):
            raise PublicationTypeError(
                "adapter identities must be sorted and duplicate-free"
            )
        total_bytes += sum(
            len(adapter_id.encode("ascii"))
            + len(adapter_version.encode("ascii"))
            for adapter_id, adapter_version in identity_keys
        )
        if total_bytes > MAXIMUM_REGISTRY_BYTES:
            raise PublicationTypeError(
                "public identifier registry exceeds its byte ceiling"
            )
        if set(self.allowed_claim_ids).intersection(self.blocked_claim_ids):
            raise PublicationTypeError(
                "allowed and blocked claim identifiers must be disjoint"
            )


@dataclass(frozen=True)
class PublicationBindingInputV1:
    """Exact binding bytes; a later layer recomputes every digest."""

    a9_1_bytes: bytes
    contract_core_bytes: bytes
    dependency_lock_bytes: bytes
    environment_manifest_bytes: bytes
    execution_guard_source_bytes: bytes
    interpreter_executable_bytes: bytes
    gate_spec_bytes: bytes
    phase_c_report_bytes: bytes
    phase_d_spec_bytes: bytes
    oracle_registry_bytes: bytes
    public_id_registry_bytes: bytes
    publisher_source_bytes: bytes
    verifier_source_bytes: bytes
    source_tree_manifest_bytes: bytes
    source_tree_archive_bytes: bytes
    test_inventory_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not PublicationBindingInputV1:
            raise TypeError("publication binding input must be exact")
        total = 0
        for name in self.__dataclass_fields__:
            value = _exact_bytes(
                getattr(self, name),
                name=name,
                maximum=MAXIMUM_SINGLE_BINDING_BYTES,
            )
            total += len(value)
            if total > MAXIMUM_TOTAL_BINDING_BYTES:
                raise PublicationTypeError(
                    "publication bindings exceed their aggregate byte ceiling"
                )


@dataclass(frozen=True)
class VerifiedDetachedCaseInputV1:
    """Untrusted case inputs that the freezing layer must validate afresh."""

    adapter: object
    source_bytes: bytes
    descriptor: AdapterDescriptor
    split_manifest: SplitManifest
    complete_sample: CompleteAdaptedEventSample
    expected_evidence: ExpectedAdapterEvidence
    expected_configuration: EventConfiguration
    conformance_run: ConformanceRun
    independent_golden_definition_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not VerifiedDetachedCaseInputV1:
            raise TypeError("detached case input must be exact")
        if self.adapter is None:
            raise TypeError("adapter must be supplied for fresh validation")
        _exact_bytes(
            self.source_bytes,
            name="source_bytes",
            maximum=MAXIMUM_SOURCE_BYTES,
        )
        exact_types = (
            ("descriptor", AdapterDescriptor),
            ("split_manifest", SplitManifest),
            ("complete_sample", CompleteAdaptedEventSample),
            ("expected_evidence", ExpectedAdapterEvidence),
            ("expected_configuration", EventConfiguration),
            ("conformance_run", ConformanceRun),
        )
        for name, expected_type in exact_types:
            if type(getattr(self, name)) is not expected_type:
                raise TypeError(name + " must have its exact contract type")
        _exact_bytes(
            self.independent_golden_definition_bytes,
            name="independent_golden_definition_bytes",
            maximum=MAXIMUM_GOLDEN_DEFINITION_BYTES,
        )


@dataclass(frozen=True)
class HostileControlInputV1:
    """One hostile outcome plus the exact bytes whose digests are published."""

    control_id: str
    status_id: str
    error_code: str
    input_bytes: bytes
    test_node_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not HostileControlInputV1:
            raise TypeError("hostile control input must be exact")
        for name in ("control_id", "status_id", "error_code"):
            object.__setattr__(
                self,
                name,
                _registry_token(getattr(self, name), name=name),
            )
        _exact_bytes(
            self.input_bytes,
            name="hostile input bytes",
            maximum=MAXIMUM_HOSTILE_INPUT_BYTES,
        )
        _exact_bytes(
            self.test_node_bytes,
            name="hostile test-node bytes",
            maximum=MAXIMUM_TEST_NODE_BYTES,
        )


@dataclass(frozen=True)
class ExecutionGuardRunManifestV1:
    """Typed declaration cross-checked with one development guard receipt."""

    address_space_limit_bytes: int
    allowed_execution_status_ids: Tuple[str, ...]
    argv_sha256: str
    working_directory_sha256: str
    environment_sha256: str
    clock_method_id: str
    dependency_lock_sha256: str
    environment_manifest_sha256: str
    execution_backend_id: str
    execution_guard_source_sha256: str
    filesystem_confinement_id: str
    interpreter_executable_sha256: str
    publication_invocation_input_sha256: str
    publication_profile_input_sha256: str
    output_capture_method_id: str
    peak_rss_method_id: str
    cwd_launch_method_id: str
    process_containment_id: str
    source_binding_format_id: str
    source_tree_manifest_sha256: str
    test_inventory_sha256: str
    guard_implementation_status_id: str
    address_space_limit_method_id: str
    output_complete_required: bool
    artifact_type: str = field(
        default=EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)
    decision_eligible_required: bool = field(default=False, init=False)
    managed_process_group_quiescence_required: bool = field(
        default=True,
        init=False,
    )
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
        if type(self) is not ExecutionGuardRunManifestV1:
            raise TypeError("execution guard run manifest must be exact")
        statuses = _token_tuple(
            self.allowed_execution_status_ids,
            name="allowed_execution_status_ids",
        )
        object.__setattr__(self, "allowed_execution_status_ids", statuses)
        for name in (
            "argv_sha256",
            "working_directory_sha256",
            "environment_sha256",
            "dependency_lock_sha256",
            "environment_manifest_sha256",
            "execution_guard_source_sha256",
            "interpreter_executable_sha256",
            "publication_invocation_input_sha256",
            "publication_profile_input_sha256",
            "source_tree_manifest_sha256",
            "test_inventory_sha256",
        ):
            _sha256(getattr(self, name), name=name)
        for name in (
            "clock_method_id",
            "execution_backend_id",
            "filesystem_confinement_id",
            "output_capture_method_id",
            "peak_rss_method_id",
            "cwd_launch_method_id",
            "process_containment_id",
            "source_binding_format_id",
            "guard_implementation_status_id",
            "address_space_limit_method_id",
        ):
            object.__setattr__(
                self,
                name,
                _registry_token(getattr(self, name), name=name),
            )
        if type(self.output_complete_required) is not bool:
            raise TypeError("output_complete_required must be an exact bool")
        if (
            type(self.address_space_limit_bytes) is not int
            or self.address_space_limit_bytes <= 0
            or self.address_space_limit_bytes > (1 << 53) - 1
        ):
            raise PublicationTypeError(
                "address_space_limit_bytes is outside its exact bound"
            )


@dataclass(frozen=True)
class PublicationExecutionGuardInputV1:
    """Development guard result and exact bytes needed to bind its origin."""

    receipt: ExecutionReceipt
    run_manifest: ExecutionGuardRunManifestV1
    run_manifest_bytes: bytes
    test_inventory_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not PublicationExecutionGuardInputV1:
            raise TypeError("publication execution-guard input must be exact")
        if type(self.receipt) is not ExecutionReceipt:
            raise TypeError("execution receipt must be exact")
        if type(self.run_manifest) is not ExecutionGuardRunManifestV1:
            raise TypeError("execution guard run manifest must be exact")
        _exact_bytes(
            self.run_manifest_bytes,
            name="run_manifest_bytes",
            maximum=MAXIMUM_SINGLE_BINDING_BYTES,
        )
        _exact_bytes(
            self.test_inventory_bytes,
            name="guard test_inventory_bytes",
            maximum=MAXIMUM_SINGLE_BINDING_BYTES,
        )


@dataclass(frozen=True)
class PublicationRequestV1:
    """Closed top-level request with no public/free-text extension mapping."""

    bindings: PublicationBindingInputV1
    public_ids: PublicIdentifierRegistryV1
    cases: Tuple[VerifiedDetachedCaseInputV1, ...]
    hostile_controls: Tuple[HostileControlInputV1, ...]
    execution_guard: PublicationExecutionGuardInputV1

    def __post_init__(self) -> None:
        if type(self) is not PublicationRequestV1:
            raise TypeError("publication request must be exact")
        exact_types = (
            ("bindings", PublicationBindingInputV1),
            ("public_ids", PublicIdentifierRegistryV1),
            ("execution_guard", PublicationExecutionGuardInputV1),
        )
        for name, expected_type in exact_types:
            if type(getattr(self, name)) is not expected_type:
                raise TypeError(name + " must have its exact publication type")
        if type(self.cases) is not tuple or not self.cases:
            raise TypeError("cases must be a nonempty exact tuple")
        if len(self.cases) > MAXIMUM_PUBLICATION_CASES:
            raise PublicationTypeError("cases exceed their value ceiling")
        if any(type(value) is not VerifiedDetachedCaseInputV1 for value in self.cases):
            raise TypeError("cases must contain exact detached-case inputs")
        if type(self.hostile_controls) is not tuple:
            raise TypeError("hostile_controls must be an exact tuple")
        if len(self.hostile_controls) > MAXIMUM_HOSTILE_CONTROL_RECEIPTS:
            raise PublicationTypeError(
                "hostile_controls exceed their value ceiling"
            )
        if any(type(value) is not HostileControlInputV1 for value in self.hostile_controls):
            raise TypeError(
                "hostile_controls must contain exact hostile-control inputs"
            )


@dataclass(frozen=True)
class PreparedPublicationV1:
    """Untrusted transport container returned by write-free preparation.

    Its constructor enforces only outer byte/digest grammar and fixed HOLD
    states.  A commit consumer must strict-parse the artifacts and recompute
    every file/domain digest; exact Python type is not preparation provenance.
    """

    public_core_bytes: bytes
    private_envelope_bytes: bytes
    manifest_bytes: bytes
    public_core_sha256: str
    private_envelope_sha256: str
    manifest_sha256: str
    public_core_file_sha256: str
    private_envelope_file_sha256: str
    manifest_file_sha256: str
    decision_status: str = field(
        default=PUBLICATION_DECISION_STATUS,
        init=False,
    )
    development_status: str = field(
        default=PUBLICATION_DEVELOPMENT_STATUS,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not PreparedPublicationV1:
            raise TypeError("prepared publication must be exact")
        public_core = _exact_bytes(
            self.public_core_bytes,
            name="public_core_bytes",
            maximum=MAXIMUM_PUBLIC_ARTIFACT_BYTES,
        )
        manifest = _exact_bytes(
            self.manifest_bytes,
            name="manifest_bytes",
            maximum=MAXIMUM_PUBLIC_ARTIFACT_BYTES,
        )
        if len(public_core) + len(manifest) > MAXIMUM_PUBLIC_ARTIFACT_BYTES:
            raise PublicationTypeError(
                "public artifact bytes exceed their aggregate ceiling"
            )
        _exact_bytes(
            self.private_envelope_bytes,
            name="private_envelope_bytes",
            maximum=MAXIMUM_PRIVATE_ARTIFACT_BYTES,
        )
        for name in (
            "public_core_sha256",
            "private_envelope_sha256",
            "manifest_sha256",
            "public_core_file_sha256",
            "private_envelope_file_sha256",
            "manifest_file_sha256",
        ):
            _sha256(getattr(self, name), name=name)


@dataclass(frozen=True)
class PublicationVerificationReceiptV1:
    """Path-free source-bound byte-identity receipt; never a gate decision."""

    manifest_sha256: str
    private_envelope_sha256: str
    public_core_sha256: str
    artifact_type: str = field(
        default=VERIFICATION_RECEIPT_ARTIFACT_TYPE,
        init=False,
    )
    decision_status: str = field(
        default=VERIFIER_DECISION_STATUS,
        init=False,
    )
    status_id: str = field(
        default=VERIFICATION_SUCCESS_STATUS,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not PublicationVerificationReceiptV1:
            raise TypeError("publication verification receipt must be exact")
        for name in (
            "manifest_sha256",
            "private_envelope_sha256",
            "public_core_sha256",
        ):
            _sha256(getattr(self, name), name=name)


@dataclass(frozen=True)
class PublicationCommitReceiptV1:
    """Path-free commit state; visibility is not adapter-conformance GO."""

    manifest_sha256: str
    state: PublicationCommitState
    decision_status: str = field(
        default=PUBLICATION_DECISION_STATUS,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not PublicationCommitReceiptV1:
            raise TypeError("publication commit receipt must be exact")
        _sha256(self.manifest_sha256, name="manifest_sha256")
        if type(self.state) is not PublicationCommitState:
            raise TypeError("publication commit state must be exact")


__all__ = [
    "EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE",
    "ExecutionGuardRunManifestV1",
    "HostileControlInputV1",
    "MAXIMUM_PRIVATE_ARTIFACT_BYTES",
    "MAXIMUM_PUBLIC_ARTIFACT_BYTES",
    "PRIVATE_ENVELOPE_ARTIFACT_ID",
    "PRIVATE_ENVELOPE_ARTIFACT_TYPE",
    "PUBLICATION_DECISION_STATUS",
    "PUBLICATION_DEVELOPMENT_STATUS",
    "PUBLICATION_IMPLEMENTATION_STATUS",
    "PUBLICATION_MANIFEST_ARTIFACT_TYPE",
    "PUBLIC_CORE_ARTIFACT_ID",
    "PUBLIC_CORE_ARTIFACT_TYPE",
    "PUBLIC_COUNT_IDS",
    "PreparedPublicationV1",
    "PublicAdapterIdentityV1",
    "PublicIdentifierRegistryV1",
    "PublicationBindingInputV1",
    "PublicationCommitReceiptV1",
    "PublicationCommitState",
    "PublicationExecutionGuardInputV1",
    "PublicationRequestV1",
    "PublicationTypeError",
    "PublicationVerificationReceiptV1",
    "VERIFICATION_RECEIPT_ARTIFACT_TYPE",
    "VERIFICATION_SUCCESS_STATUS",
    "VERIFIER_DECISION_STATUS",
    "VerifiedDetachedCaseInputV1",
]
