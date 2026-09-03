"""Independent byte verifier for Linux-confinement finalization envelopes.

This module deliberately does not call the companion codec's builders,
serializers, digest helpers, or private parsers.  It freezes the public V1
schemas, parses every nested declared-field and counted-sequence structure,
and independently recomputes all byte identities and cross-object bindings.

A successful result establishes byte-level internal consistency only.  The
envelope and all of its nested records may be synthetic; this verifier neither
executes Linux nor authenticates evidence origin, custody, confinement,
release, a producer, or the semantics of opaque retained records.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Final, NamedTuple, Tuple

from .adapter_linux_confinement_acceptance import (
    LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS,
)
from .adapter_linux_confinement_evidence_plan import (
    LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_PRE_COMPLETION_RELEASE_PREFIX_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE,
)
from .adapter_linux_confinement_preimage_codec import (
    LINUX_CONFINEMENT_CAPTURE_BINDING_FIELD_IDS,
    LINUX_CONFINEMENT_ENVELOPE_OBSERVATION_IDS,
    LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_FIELD_IDS,
    LINUX_CONFINEMENT_OPAQUE_RECORD_SEMANTIC_STATUS,
    LINUX_CONFINEMENT_POSTRUN_BINDING_FIELD_IDS,
    LINUX_CONFINEMENT_POSTRUN_CLEANUP_EVENT_IDS,
    LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_DIGEST_DOMAIN,
    LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_FIELD_IDS,
    LINUX_CONFINEMENT_POSTRUN_REQUIRED_OBSERVATION_IDS,
    LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_PREIMAGE_CODEC_VALIDATION_STATUS,
    LINUX_CONFINEMENT_PREIMAGE_CODEC_VERIFIER_ID,
    LINUX_CONFINEMENT_RECORD_KIND_OBSERVATION,
    LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_READY_FIRST,
    LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_STOP_FIRST,
    LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_FIELD_IDS,
    LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_DIGEST_DOMAIN,
    LINUX_CONFINEMENT_RETAINED_RECORD_FIELD_IDS,
    LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_FIELD_IDS,
    LINUX_CONFINEMENT_STAGE1_REQUIRED_OBSERVATION_IDS,
    LINUX_CONFINEMENT_STAGE1_REQUIRED_PRIOR_EVENT_IDS,
    LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_FIELD_IDS,
    LINUX_CONFINEMENT_STAGE2_REQUIRED_OBSERVATION_IDS,
    LINUX_CONFINEMENT_STAGE2_REQUIRED_PRIOR_EVENT_IDS,
    LINUX_CONFINEMENT_STAGING_EVENT_RECORD_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_STAGING_EVENT_RECORD_DIGEST_DOMAIN,
    LINUX_CONFINEMENT_STAGING_EVENT_RECORD_FIELD_IDS,
    LinuxConfinementCaptureBindingV1,
    MAXIMUM_LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_BYTES,
    MAXIMUM_LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_BYTES,
    MAXIMUM_LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_BYTES,
    MAXIMUM_LINUX_CONFINEMENT_RECORD_PAYLOAD_BYTES,
    MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
    MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
    MAXIMUM_LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_BYTES,
    MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_RECORD_BYTES,
)
from .adapter_linux_confinement_preimage_codec import (
    LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_FIELD_IDS,
)
from .adapter_linux_confinement_staging_protocol import (
    LINUX_CONFINEMENT_STAGING_RUN_BINDING_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_STAGING_RUN_BINDING_DIGEST_DOMAIN,
)
from .adapter_source_bound_child_runner import (
    MAXIMUM_SOURCE_BOUND_RUN_RECEIPT_BYTES,
    SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE,
    SourceBoundAdapterChildRunReceiptV1,
)


LINUX_CONFINEMENT_PREIMAGE_VERIFICATION_RESULT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-preimage-independent-"
    "verification-result.v1"
)
LINUX_CONFINEMENT_PREIMAGE_VERIFICATION_RESULT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_PREIMAGE_VERIFICATION_RESULT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_PREIMAGE_VERIFIER_IMPLEMENTATION_STATUS: Final = (
    "INDEPENDENT_PORTABLE_RECURSIVE_BYTE_VERIFIER_IMPLEMENTED"
)
MAXIMUM_LINUX_CONFINEMENT_PREIMAGE_VERIFICATION_RESULT_BYTES: Final = (
    64 * 1024
)

_MAXIMUM_U64: Final = (1 << 64) - 1
_MAXIMUM_TOKEN_BYTES: Final = 512
_MAXIMUM_FRAME_FIELDS: Final = 128
_MAXIMUM_SEQUENCE_ITEMS: Final = 64
_MAXIMUM_RUN_SEQUENCE_NUMBER: Final = 4095
_MAXIMUM_EVENT_SEQUENCE_NUMBER: Final = 127
_ZERO_SHA256: Final = "0" * 64
_TOKEN_RE: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$")
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")

_CAPTURE_FIELDS: Final = (
    "acceptance-contract-sha256",
    "evidence-plan-sha256",
    "evidence-schema-contract-sha256",
    "linux-platform-profile-sha256",
    "observation-subject-identity",
    "policy-sha256",
    "run-nonce-hex",
    "run-sequence-number",
    "staging-protocol-contract-sha256",
    "staging-run-binding-sha256",
    "supervisor-epoch-id-hex",
)
_POSTRUN_BINDING_FIELDS: Final = _CAPTURE_FIELDS + (
    "stage1-release-gate-preimage-sha256",
    "stage2-release-gate-preimage-sha256",
    "pre-completion-release-prefix-sha256",
    "inner-v1-receipt-byte-count",
    "inner-v1-receipt-plain-sha256",
    "inner-v1-receipt-sha256",
    "inner-v1-run-input-sha256",
    "inner-v1-request-frame-sha256",
    "inner-v1-case-input-sha256",
    "inner-v1-implementation-closure-sha256",
    "inner-v1-implementation-closure-validation-receipt-sha256",
    "inner-v1-closure-pipe-frame-sha256",
    "inner-v1-completion-record-sha256",
    "full-release-transcript-sha256",
)
_RETAINED_FIELDS: Final = (
    "artifact-type",
    "format-version",
    "record-kind-id",
    "record-id",
    "lifecycle-stage-id",
    "trusted-producer-id",
    "staging-run-binding-sha256",
    "observation-subject-identity",
    "capture-monotonic-timestamp-ns",
    "record-artifact-type",
    "record-canonical-bytes",
    "record-byte-count",
    "record-plain-sha256",
    "record-sha256",
    "semantic-validation-status-id",
)
_EVENT_FIELDS: Final = (
    "artifact-type",
    "format-version",
    "sequence-number",
    "monotonic-timestamp-ns",
    "event-id",
    "staging-run-binding-sha256",
    "evidence-digest-sha256",
)
_GATE_COMMON_FIELDS: Final = (
    "artifact-type",
    "format-version",
    "release-gate-id",
    "staging-event-id",
    "acceptance-contract-sha256",
    "evidence-plan-sha256",
    "evidence-schema-contract-sha256",
    "staging-protocol-contract-sha256",
    "staging-run-binding-sha256",
    "linux-platform-profile-sha256",
    "observation-subject-identity",
    "policy-sha256",
    "supervisor-epoch-id-hex",
    "run-sequence-number",
    "run-nonce-hex",
    "required-observation-ids",
    "ordered-observation-record-sha256s",
    "required-prior-staging-event-ids",
    "prior-staging-event-record-sha256s-in-required-event-id-order",
)
_STAGE2_GATE_FIELDS: Final = _GATE_COMMON_FIELDS + (
    "stage1-release-gate-preimage-artifact-type",
    "stage1-release-gate-preimage-byte-count",
    "stage1-release-gate-preimage-plain-sha256",
    "stage1-release-gate-preimage-sha256",
    "stage1-release-gate-event-evidence-digest-sha256",
)
_COMPLETION_FIELDS: Final = (
    "artifact-type",
    "format-version",
    "record-id",
    "acceptance-contract-sha256",
    "evidence-plan-sha256",
    "evidence-schema-contract-sha256",
    "staging-protocol-contract-sha256",
    "staging-run-binding-sha256",
    "linux-confinement-policy-sha256",
    "linux-platform-profile-sha256",
    "supervisor-epoch-id-hex",
    "run-sequence-number",
    "run-nonce-hex",
    "stage1-release-gate-preimage-artifact-type",
    "stage1-release-gate-preimage-canonical-bytes",
    "stage1-release-gate-preimage-byte-count",
    "stage1-release-gate-preimage-plain-sha256",
    "stage1-release-gate-preimage-sha256",
    "stage1-release-gate-event-evidence-digest-sha256",
    "stage2-release-gate-preimage-artifact-type",
    "stage2-release-gate-preimage-canonical-bytes",
    "stage2-release-gate-preimage-byte-count",
    "stage2-release-gate-preimage-plain-sha256",
    "stage2-release-gate-preimage-sha256",
    "stage2-release-gate-event-evidence-digest-sha256",
    "pre-completion-release-prefix-artifact-type",
    "pre-completion-release-prefix-canonical-bytes",
    "pre-completion-release-prefix-byte-count",
    "pre-completion-release-prefix-plain-sha256",
    "pre-completion-release-prefix-sha256",
    "pre-completion-release-prefix-terminal-event-id",
    "inner-v1-receipt-canonical-bytes",
    "inner-v1-receipt-byte-count",
    "inner-v1-receipt-plain-sha256",
    "inner-v1-receipt-sha256",
    "inner-v1-receipt-artifact-type-record",
    "inner-v1-inherited-28-false-field-ledger",
    "inner-v1-run-input-sha256",
    "inner-v1-request-frame-sha256",
    "inner-v1-case-input-sha256",
    "inner-v1-implementation-closure-sha256",
    "inner-v1-implementation-closure-validation-receipt-sha256",
    "inner-v1-closure-pipe-frame-sha256",
)
_TRANSCRIPT_FIELDS: Final = (
    "artifact-type",
    "format-version",
    "record-id",
    "acceptance-contract-sha256",
    "evidence-plan-sha256",
    "evidence-schema-contract-sha256",
    "staging-protocol-contract-sha256",
    "staging-run-binding-sha256",
    "linux-confinement-policy-sha256",
    "linux-platform-profile-sha256",
    "observation-subject-identity",
    "supervisor-epoch-id-hex",
    "run-sequence-number",
    "run-nonce-hex",
    "terminal-phase-id",
    "terminal-event-id",
    "event-count",
    "ordered-event-ids",
    "ordered-event-record-canonical-bytes",
    "ordered-event-record-byte-counts",
    "ordered-event-record-plain-sha256s",
    "ordered-event-record-sha256s",
    "stage1-release-gate-event-evidence-digest-sha256",
    "stage2-release-gate-event-evidence-digest-sha256",
)
_POSTRUN_TRANSCRIPT_FIELDS: Final = (
    "artifact-type",
    "format-version",
    "record-id",
    "acceptance-contract-sha256",
    "evidence-plan-sha256",
    "evidence-schema-contract-sha256",
    "staging-protocol-contract-sha256",
    "staging-run-binding-sha256",
    "linux-confinement-policy-sha256",
    "linux-platform-profile-sha256",
    "observation-subject-identity",
    "supervisor-epoch-id-hex",
    "run-sequence-number",
    "run-nonce-hex",
    "cleanup-branch-id",
    "terminal-phase-id",
    "terminal-event-id",
    "event-count",
    "ordered-event-ids",
    "ordered-event-record-canonical-bytes",
    "ordered-event-record-byte-counts",
    "ordered-event-record-plain-sha256s",
    "ordered-event-record-sha256s",
    "stage1-release-gate-event-evidence-digest-sha256",
    "stage2-release-gate-event-evidence-digest-sha256",
    "inner-v1-completion-record-sha256",
)
_ENVELOPE_FIELDS: Final = (
    "artifact-type",
    "format-version",
    "envelope-id",
    "codec-contract-sha256",
) + _POSTRUN_BINDING_FIELDS + (
    "stage1-release-gate-preimage-canonical-bytes",
    "stage2-release-gate-preimage-canonical-bytes",
    "pre-completion-release-prefix-canonical-bytes",
    "inner-v1-completion-record-canonical-bytes",
    "full-release-transcript-canonical-bytes",
    "postrun-staging-transcript-canonical-bytes",
    "postrun-staging-transcript-sha256",
    "ordered-observation-record-commitment-bytes",
)

_FALSE_FIELDS: Final = (
    "actual_output_freshness_attested",
    "adapter_source_execution_identity_attested",
    "argument_consumption_attested",
    "bootstrap_proxy_call_counts_attested",
    "containment_attested",
    "containment_enforced",
    "current_child_method_return_capture_attested",
    "decision_eligible",
    "decision_made",
    "expected_material_nonexposure_attested",
    "external_custody_authenticated",
    "filesystem_confinement_attested",
    "generalization_attested",
    "guard_manifest_executed",
    "information_flow_noninterference_attested",
    "interpreter_dependency_identity_attested",
    "interpreter_executable_execution_identity_attested",
    "loaded_runtime_profile_execution_attested",
    "managed_descendant_quiescence_attested",
    "network_confinement_attested",
    "process_tree_escape_prevented",
    "protected_namespace_host_fallback_absence_attested",
    "publication_artifacts_rebuilt",
    "recursive_internal_call_counts_observed",
    "runtime_instruction_execution_attested",
    "same_process_runtime_mutation_prevented",
    "semantic_truth_attested",
    "v2_or_guard_consumption_attested",
)
_STAGE1_OBSERVATIONS: Final = (
    "backend-static-sealed-executable-identity-matched",
    "cgroup-v2-leaf-owned-by-supervisor",
    "dependency-lock-identity-matched",
    (
        "exact-two-level-uid-gid-maps-composition-empty-"
        "supplementary-groups-and-setgroups-denial-matched"
    ),
    "immutable-runtime-rootfs-identity-matched",
    "linux-platform-profile-matched",
    "sandbox-bootstrap-identity-matched",
    "sandbox-interpreter-identity-matched",
    "supervisor-dependency-closure-identity-matched",
    "supervisor-executable-identity-matched",
)
_STAGE2_OBSERVATIONS: Final = (
    "application-argv-environment-cwd-umask-matched",
    "capability-securebits-dumpability-profile-matched",
    "cgroup-v2-controller-values-matched-before-release",
    "descriptor-inventory-and-stdio-types-closed-before-adapter-import",
    "landlock-abi-and-ruleset-matched",
    "mount-inventory-and-write-surface-matched",
    "namespace-identities-distinct-before-release",
    "network-interface-and-route-inventory-matched",
    "no-new-privileges-observed-before-release",
    "rlimit-profile-matched-before-release",
    "seccomp-filter-and-architecture-observed-before-release",
)
_POSTRUN_OBSERVATIONS: Final = (
    (
        "nonce-generation-nonreuse-and-readiness-release-"
        "transcript-matched"
    ),
    (
        "pidfd-bound-observer-helper-monitor-init-application-"
        "identities-subreaper-adoption-and-reap-observed"
    ),
    "teardown-cgroup-populated-zero-observed",
)
_ENVELOPE_OBSERVATIONS: Final = (
    _STAGE1_OBSERVATIONS
    + _STAGE2_OBSERVATIONS
    + _POSTRUN_OBSERVATIONS
)
_STAGE1_PRIOR_EVENTS: Final = (
    "SUPERVISOR_CREATED",
    "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
)
_STAGE2_PRIOR_EVENTS: Final = (
    "SUPERVISOR_CREATED",
    "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
    "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED",
    "STAGE1_RELEASED",
    "READY_FRAME_ACCEPTED",
    "PIDFD_BOUND_APPLICATION_SIGSTOP_OBSERVED",
    "PRE_RELEASE_STDOUT_DRAINED",
)
_RELEASE_PREFIX_READY_FIRST: Final = (
    "SUPERVISOR_CREATED",
    "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
    "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED",
    "STAGE1_RELEASED",
    "READY_FRAME_ACCEPTED",
    "PIDFD_BOUND_APPLICATION_SIGSTOP_OBSERVED",
    "PRE_RELEASE_STDOUT_DRAINED",
    "STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED",
    "STAGE2_RELEASED",
)
_RELEASE_PREFIX_STOP_FIRST: Final = (
    "SUPERVISOR_CREATED",
    "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
    "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED",
    "STAGE1_RELEASED",
    "PIDFD_BOUND_APPLICATION_SIGSTOP_OBSERVED",
    "READY_FRAME_ACCEPTED",
    "PRE_RELEASE_STDOUT_DRAINED",
    "STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED",
    "STAGE2_RELEASED",
)
_CLEANUP_EVENTS: Final = (
    "TEARDOWN_STARTED",
    "REQUEST_WRITER_CLOSED",
    "APPLICATION_PIDFD_SIGTERM_SENT",
    "TERM_GRACE_AND_CONDITIONAL_PIDFD_SIGKILL_RESOLVED",
    "APPLICATION_REAPED_BY_SANDBOX_PID1",
    "BUBBLEWRAP_MONITOR_REAPED",
    "ADOPTED_DESCENDANTS_REAPED",
    "CGROUP_POPULATED_ZERO_OBSERVED",
    "STREAM_EOF_DRAINED",
)
_EVIDENCE_EVENTS: Final = frozenset(
    {
        "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
        "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED",
        "STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED",
        "INNER_V1_COMPLETE",
    }
)

_OBSERVATION_METADATA: Final = MappingProxyType(
    {
        "backend-static-sealed-executable-identity-matched": (
            "pre-backend-exec",
            "privileged-supervisor-artifact-observer-v1",
        ),
        "cgroup-v2-leaf-owned-by-supervisor": (
            "pre-stage1-setup-blocked",
            "privileged-supervisor-cgroup-observer-v1",
        ),
        "dependency-lock-identity-matched": (
            "pre-first-child-artifact-validation",
            "privileged-supervisor-artifact-observer-v1",
        ),
        (
            "exact-two-level-uid-gid-maps-composition-empty-"
            "supplementary-groups-and-setgroups-denial-matched"
        ): (
            "pre-stage1-setup-blocked",
            "privileged-supervisor-and-userns-observer-v1",
        ),
        "immutable-runtime-rootfs-identity-matched": (
            "pre-stage1-setup-blocked",
            "privileged-supervisor-mount-observer-v1",
        ),
        "linux-platform-profile-matched": (
            "pre-first-child-artifact-validation",
            "privileged-supervisor-platform-observer-v1",
        ),
        "sandbox-bootstrap-identity-matched": (
            "pre-first-child-artifact-validation",
            "privileged-supervisor-artifact-observer-v1",
        ),
        "sandbox-interpreter-identity-matched": (
            "pre-first-child-artifact-validation",
            "privileged-supervisor-artifact-observer-v1",
        ),
        "supervisor-dependency-closure-identity-matched": (
            "pre-first-child-artifact-validation",
            "external-supervisor-custody-observer-v1",
        ),
        "supervisor-executable-identity-matched": (
            "pre-first-child-artifact-validation",
            "external-supervisor-custody-observer-v1",
        ),
        "application-argv-environment-cwd-umask-matched": (
            "pre-stage2-application-stopped",
            "privileged-supervisor-stage2-observer-v1",
        ),
        "capability-securebits-dumpability-profile-matched": (
            "pre-stage2-application-stopped",
            "privileged-supervisor-stage2-observer-v1",
        ),
        "cgroup-v2-controller-values-matched-before-release": (
            "pre-stage2-application-stopped",
            "privileged-supervisor-cgroup-observer-v1",
        ),
        (
            "descriptor-inventory-and-stdio-types-closed-before-"
            "adapter-import"
        ): (
            "pre-stage2-application-stopped",
            "privileged-supervisor-stage2-observer-v1",
        ),
        "landlock-abi-and-ruleset-matched": (
            "pre-stage2-application-stopped",
            "privileged-supervisor-stage2-observer-v1",
        ),
        "mount-inventory-and-write-surface-matched": (
            "pre-stage2-application-stopped",
            "privileged-supervisor-stage2-observer-v1",
        ),
        "namespace-identities-distinct-before-release": (
            "pre-stage2-application-stopped",
            "privileged-supervisor-stage2-observer-v1",
        ),
        "network-interface-and-route-inventory-matched": (
            "pre-stage2-application-stopped",
            "privileged-supervisor-stage2-observer-v1",
        ),
        "no-new-privileges-observed-before-release": (
            "pre-stage2-application-stopped",
            "privileged-supervisor-stage2-observer-v1",
        ),
        "rlimit-profile-matched-before-release": (
            "pre-stage2-application-stopped",
            "privileged-supervisor-stage2-observer-v1",
        ),
        "seccomp-filter-and-architecture-observed-before-release": (
            "pre-stage2-application-stopped",
            "privileged-supervisor-stage2-observer-v1",
        ),
        (
            "nonce-generation-nonreuse-and-readiness-release-"
            "transcript-matched"
        ): (
            "cross-stage-run-transcript",
            "privileged-supervisor-transcript-producer-v1",
        ),
        (
            "pidfd-bound-observer-helper-monitor-init-application-"
            "identities-subreaper-adoption-and-reap-observed"
        ): (
            "cross-stage-through-postrun",
            "dedicated-subreaper-supervisor-process-observer-v1",
        ),
        "teardown-cgroup-populated-zero-observed": (
            "postrun-cleanup-complete",
            "privileged-supervisor-cgroup-observer-v1",
        ),
    }
)


class LinuxConfinementPreimageVerificationCode(str, Enum):
    """Closed failures from the independent byte verifier."""

    INPUT_TYPE = "LINUX_CONFINEMENT_PREIMAGE_VERIFY_INPUT_TYPE"
    INPUT_RESOURCE = "LINUX_CONFINEMENT_PREIMAGE_VERIFY_INPUT_RESOURCE"
    FRAME_INVALID = "LINUX_CONFINEMENT_PREIMAGE_VERIFY_FRAME_INVALID"
    VALUE_INVALID = "LINUX_CONFINEMENT_PREIMAGE_VERIFY_VALUE_INVALID"
    BINDING_MISMATCH = (
        "LINUX_CONFINEMENT_PREIMAGE_VERIFY_BINDING_MISMATCH"
    )
    ORDER_INVALID = "LINUX_CONFINEMENT_PREIMAGE_VERIFY_ORDER_INVALID"
    INNER_RECEIPT_INVALID = (
        "LINUX_CONFINEMENT_PREIMAGE_VERIFY_INNER_RECEIPT_INVALID"
    )
    RESULT_INVALID = "LINUX_CONFINEMENT_PREIMAGE_VERIFY_RESULT_INVALID"
    SCHEMA_DRIFT = "LINUX_CONFINEMENT_PREIMAGE_VERIFY_SCHEMA_DRIFT"
    INTERNAL_ERROR = "LINUX_CONFINEMENT_PREIMAGE_VERIFY_INTERNAL_ERROR"


_ERROR_MESSAGES = MappingProxyType(
    {
        LinuxConfinementPreimageVerificationCode.INPUT_TYPE: (
            "Linux confinement verifier input has an invalid exact type"
        ),
        LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE: (
            "Linux confinement verifier input exceeds a resource ceiling"
        ),
        LinuxConfinementPreimageVerificationCode.FRAME_INVALID: (
            "Linux confinement declared-field bytes are invalid"
        ),
        LinuxConfinementPreimageVerificationCode.VALUE_INVALID: (
            "Linux confinement encoded field value is invalid"
        ),
        LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH: (
            "Linux confinement encoded bindings differ"
        ),
        LinuxConfinementPreimageVerificationCode.ORDER_INVALID: (
            "Linux confinement encoded sequence order is invalid"
        ),
        LinuxConfinementPreimageVerificationCode.INNER_RECEIPT_INVALID: (
            "Linux confinement embedded inner receipt is invalid"
        ),
        LinuxConfinementPreimageVerificationCode.RESULT_INVALID: (
            "Linux confinement verification result is invalid"
        ),
        LinuxConfinementPreimageVerificationCode.SCHEMA_DRIFT: (
            "Linux confinement verifier schema differs from the codec"
        ),
        LinuxConfinementPreimageVerificationCode.INTERNAL_ERROR: (
            "Linux confinement byte verification failed internally"
        ),
    }
)


class LinuxConfinementPreimageVerificationError(ValueError):
    """One interpolation-free failure with a closed machine code."""

    def __init__(
        self,
        code: LinuxConfinementPreimageVerificationCode,
    ) -> None:
        if type(code) is not LinuxConfinementPreimageVerificationCode:
            raise TypeError("verification code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: LinuxConfinementPreimageVerificationCode) -> None:
    raise LinuxConfinementPreimageVerificationError(code) from None


def _plain_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _domain_sha256(domain: str, payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii", "strict"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _take(
    value: bytes,
    cursor: int,
    length: int,
    *,
    ceiling: int,
) -> Tuple[bytes, int]:
    if (
        type(length) is not int
        or length < 0
        or cursor < 0
        or cursor > len(value)
    ):
        _fail(LinuxConfinementPreimageVerificationCode.FRAME_INVALID)
    if length > ceiling:
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE)
    if length > len(value) - cursor:
        _fail(LinuxConfinementPreimageVerificationCode.FRAME_INVALID)
    return value[cursor : cursor + length], cursor + length


def _read_u64_at(
    value: bytes,
    cursor: int,
    *,
    ceiling: int,
) -> Tuple[int, int]:
    raw, cursor = _take(value, cursor, 8, ceiling=ceiling)
    return int.from_bytes(raw, "big"), cursor


def _parse_frame(
    value: bytes,
    expected_fields: Tuple[str, ...],
    *,
    maximum: int,
) -> dict[str, bytes]:
    if type(value) is not bytes:
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_TYPE)
    if not value or len(value) > maximum:
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE)
    if (
        type(expected_fields) is not tuple
        or not expected_fields
        or len(expected_fields) > _MAXIMUM_FRAME_FIELDS
        or len(set(expected_fields)) != len(expected_fields)
    ):
        _fail(LinuxConfinementPreimageVerificationCode.SCHEMA_DRIFT)
    count, cursor = _read_u64_at(value, 0, ceiling=maximum)
    if count > _MAXIMUM_FRAME_FIELDS:
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE)
    if count != len(expected_fields):
        _fail(LinuxConfinementPreimageVerificationCode.FRAME_INVALID)
    result: dict[str, bytes] = {}
    for expected in expected_fields:
        name_length, cursor = _read_u64_at(
            value, cursor, ceiling=maximum
        )
        if name_length == 0 or name_length > _MAXIMUM_TOKEN_BYTES:
            _fail(LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE)
        name_raw, cursor = _take(
            value,
            cursor,
            name_length,
            ceiling=_MAXIMUM_TOKEN_BYTES,
        )
        try:
            name = name_raw.decode("ascii", "strict")
        except UnicodeError:
            _fail(LinuxConfinementPreimageVerificationCode.FRAME_INVALID)
        if name != expected or _TOKEN_RE.fullmatch(name) is None:
            _fail(LinuxConfinementPreimageVerificationCode.FRAME_INVALID)
        value_length, cursor = _read_u64_at(
            value, cursor, ceiling=maximum
        )
        raw, cursor = _take(
            value,
            cursor,
            value_length,
            ceiling=maximum,
        )
        result[name] = raw
    if cursor != len(value):
        _fail(LinuxConfinementPreimageVerificationCode.FRAME_INVALID)
    return result


def _parse_counted(
    value: bytes,
    *,
    expected_count: int,
    maximum_entry: int,
    maximum_total: int,
) -> Tuple[bytes, ...]:
    if type(value) is not bytes:
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_TYPE)
    if len(value) > maximum_total:
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE)
    count, cursor = _read_u64_at(value, 0, ceiling=maximum_total)
    if count > _MAXIMUM_SEQUENCE_ITEMS:
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE)
    if count != expected_count:
        _fail(LinuxConfinementPreimageVerificationCode.ORDER_INVALID)
    result = []
    for _ in range(count):
        length, cursor = _read_u64_at(
            value, cursor, ceiling=maximum_total
        )
        item, cursor = _take(
            value,
            cursor,
            length,
            ceiling=maximum_entry,
        )
        result.append(item)
    if cursor != len(value):
        _fail(LinuxConfinementPreimageVerificationCode.FRAME_INVALID)
    return tuple(result)


def _token(value: bytes) -> str:
    if (
        type(value) is not bytes
        or not value
        or len(value) > _MAXIMUM_TOKEN_BYTES
    ):
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    try:
        result = value.decode("ascii", "strict")
    except UnicodeError:
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    if _TOKEN_RE.fullmatch(result) is None:
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    return result


def _sha256(value: bytes, *, nonzero: bool = True) -> str:
    if type(value) is not bytes or len(value) != 64:
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    try:
        result = value.decode("ascii", "strict")
    except UnicodeError:
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    if (
        _SHA256_RE.fullmatch(result) is None
        or (nonzero and result == _ZERO_SHA256)
    ):
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    return result


def _u64(value: bytes, *, maximum: int = _MAXIMUM_U64) -> int:
    if type(value) is not bytes or len(value) != 8:
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    result = int.from_bytes(value, "big")
    if result > maximum:
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    return result


def _tokens(
    value: bytes,
    expected: Tuple[str, ...],
    *,
    maximum_total: int,
) -> Tuple[str, ...]:
    raw = _parse_counted(
        value,
        expected_count=len(expected),
        maximum_entry=_MAXIMUM_TOKEN_BYTES,
        maximum_total=maximum_total,
    )
    result = tuple(_token(item) for item in raw)
    if result != expected:
        _fail(LinuxConfinementPreimageVerificationCode.ORDER_INVALID)
    return result


def _sha256s(
    value: bytes,
    *,
    expected_count: int,
    maximum_total: int,
) -> Tuple[str, ...]:
    raw = _parse_counted(
        value,
        expected_count=expected_count,
        maximum_entry=64,
        maximum_total=maximum_total,
    )
    return tuple(_sha256(item) for item in raw)


def _capture_values(capture: LinuxConfinementCaptureBindingV1) -> dict:
    if type(capture) is not LinuxConfinementCaptureBindingV1:
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_TYPE)
    try:
        result = {
            "acceptance-contract-sha256": (
                capture.acceptance_contract_sha256
            ),
            "evidence-plan-sha256": capture.evidence_plan_sha256,
            "evidence-schema-contract-sha256": (
                capture.evidence_schema_contract_sha256
            ),
            "linux-platform-profile-sha256": (
                capture.linux_platform_profile_sha256
            ),
            "observation-subject-identity": (
                capture.observation_subject_identity
            ),
            "policy-sha256": capture.policy_sha256,
            "run-nonce-hex": capture.run_nonce_hex,
            "run-sequence-number": capture.run_sequence_number,
            "staging-protocol-contract-sha256": (
                capture.staging_protocol_contract_sha256
            ),
            "staging-run-binding-sha256": (
                capture.staging_run_binding_sha256
            ),
            "supervisor-epoch-id-hex": capture.supervisor_epoch_id_hex,
        }
    except AttributeError:
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_TYPE)
    for name, item in result.items():
        if name == "run-sequence-number":
            if (
                type(item) is not int
                or item < 0
                or item > _MAXIMUM_RUN_SEQUENCE_NUMBER
            ):
                _fail(
                    LinuxConfinementPreimageVerificationCode.VALUE_INVALID
                )
        elif (
            type(item) is not str
            or len(item) != 64
            or _SHA256_RE.fullmatch(item) is None
            or item == _ZERO_SHA256
        ):
            _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    if (
        result["run-nonce-hex"]
        == result["supervisor-epoch-id-hex"]
    ):
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    binding_tree = {
        "artifact_type": (
            LINUX_CONFINEMENT_STAGING_RUN_BINDING_ARTIFACT_TYPE
        ),
        "format_version": "1",
        "policy_sha256": capture.policy_sha256,
        "run_nonce_hex": capture.run_nonce_hex,
        "run_sequence_number": capture.run_sequence_number,
        "supervisor_epoch_id_hex": capture.supervisor_epoch_id_hex,
    }
    try:
        binding_raw = json.dumps(
            binding_tree,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii", "strict")
    except (TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    expected_binding = _domain_sha256(
        LINUX_CONFINEMENT_STAGING_RUN_BINDING_DIGEST_DOMAIN,
        binding_raw,
    )
    if capture.staging_run_binding_sha256 != expected_binding:
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)
    return result


def _check_capture(
    encoded: dict[str, bytes],
    capture_values: dict,
    *,
    policy_field: str = "policy-sha256",
    include_subject: bool = True,
) -> None:
    names = [
        "acceptance-contract-sha256",
        "evidence-plan-sha256",
        "evidence-schema-contract-sha256",
        "staging-protocol-contract-sha256",
        "staging-run-binding-sha256",
        "linux-platform-profile-sha256",
        policy_field,
        "supervisor-epoch-id-hex",
        "run-sequence-number",
        "run-nonce-hex",
    ]
    keys = [
        "acceptance-contract-sha256",
        "evidence-plan-sha256",
        "evidence-schema-contract-sha256",
        "staging-protocol-contract-sha256",
        "staging-run-binding-sha256",
        "linux-platform-profile-sha256",
        "policy-sha256",
        "supervisor-epoch-id-hex",
        "run-sequence-number",
        "run-nonce-hex",
    ]
    if include_subject:
        names.insert(6, "observation-subject-identity")
        keys.insert(6, "observation-subject-identity")
    for name, key in zip(names, keys):
        if key == "run-sequence-number":
            actual = _u64(
                encoded[name], maximum=_MAXIMUM_RUN_SEQUENCE_NUMBER
            )
        else:
            actual = _sha256(encoded[name])
        if actual != capture_values[key]:
            _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)


def _check_envelope_capture(
    encoded: dict[str, bytes],
    capture_values: dict,
) -> None:
    for name in _CAPTURE_FIELDS:
        expected = capture_values[name]
        actual = (
            _u64(encoded[name], maximum=_MAXIMUM_RUN_SEQUENCE_NUMBER)
            if name == "run-sequence-number"
            else _sha256(encoded[name])
        )
        if actual != expected:
            _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)


@dataclass(frozen=True)
class LinuxConfinementPostrunFinalizationVerificationInputV1:
    """Raw envelope plus independently supplied immutable capture pins."""

    envelope_bytes: bytes
    expected_capture: LinuxConfinementCaptureBindingV1
    expected_codec_contract_sha256: str

    def __post_init__(self) -> None:
        if (
            type(self)
            is not LinuxConfinementPostrunFinalizationVerificationInputV1
            or type(self.envelope_bytes) is not bytes
            or type(self.expected_capture)
            is not LinuxConfinementCaptureBindingV1
            or type(self.expected_codec_contract_sha256) is not str
        ):
            _fail(LinuxConfinementPreimageVerificationCode.INPUT_TYPE)
        if (
            not self.envelope_bytes
            or len(self.envelope_bytes)
            > MAXIMUM_LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_BYTES
        ):
            _fail(LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE)
        if (
            len(self.expected_codec_contract_sha256) != 64
            or _SHA256_RE.fullmatch(self.expected_codec_contract_sha256)
            is None
            or self.expected_codec_contract_sha256 == _ZERO_SHA256
        ):
            _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)


class _Observation(NamedTuple):
    record_id: str
    raw: bytes
    plain_sha256: str
    sha256: str


class _Event(NamedTuple):
    sequence_number: int
    monotonic_timestamp_ns: int
    event_id: str
    evidence_digest_sha256: str
    raw: bytes
    plain_sha256: str
    sha256: str


class _Gate(NamedTuple):
    raw: bytes
    plain_sha256: str
    sha256: str
    observation_sha256s: Tuple[str, ...]
    prior_event_ids: Tuple[str, ...]
    prior_event_sha256s: Tuple[str, ...]


class _Transcript(NamedTuple):
    raw: bytes
    plain_sha256: str
    sha256: str
    events: Tuple[_Event, ...]


class _InnerReceipt(NamedTuple):
    raw: bytes
    byte_count: int
    plain_sha256: str
    sha256: str
    run_input_sha256: str
    request_frame_sha256: str
    case_input_sha256: str
    implementation_closure_sha256: str
    implementation_closure_validation_receipt_sha256: str
    closure_pipe_frame_sha256: str


class _Completion(NamedTuple):
    raw: bytes
    plain_sha256: str
    sha256: str
    inner: _InnerReceipt


def _parse_observations(
    value: bytes,
    capture_values: dict,
) -> Tuple[_Observation, ...]:
    items = _parse_counted(
        value,
        expected_count=len(_ENVELOPE_OBSERVATIONS),
        maximum_entry=(
            MAXIMUM_LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_BYTES
        ),
        maximum_total=(
            MAXIMUM_LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_BYTES
        ),
    )
    result = []
    for expected_id, raw in zip(
        _ENVELOPE_OBSERVATIONS,
        items,
    ):
        encoded = _parse_frame(
            raw,
            _RETAINED_FIELDS,
            maximum=(
                MAXIMUM_LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_BYTES
            ),
        )
        if (
            _token(encoded["artifact-type"])
            != LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_ARTIFACT_TYPE
            or _token(encoded["format-version"]) != "1"
            or _token(encoded["record-kind-id"])
            != LINUX_CONFINEMENT_RECORD_KIND_OBSERVATION
            or _token(encoded["record-id"]) != expected_id
            or _token(encoded["semantic-validation-status-id"])
            != LINUX_CONFINEMENT_OPAQUE_RECORD_SEMANTIC_STATUS
        ):
            _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
        expected_stage, expected_producer = _OBSERVATION_METADATA[
            expected_id
        ]
        if (
            _token(encoded["lifecycle-stage-id"]) != expected_stage
            or _token(encoded["trusted-producer-id"]) != expected_producer
            or _sha256(encoded["staging-run-binding-sha256"])
            != capture_values["staging-run-binding-sha256"]
            or _sha256(encoded["observation-subject-identity"])
            != capture_values["observation-subject-identity"]
        ):
            _fail(
                LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH
            )
        _u64(encoded["capture-monotonic-timestamp-ns"])
        artifact_type = _token(encoded["record-artifact-type"])
        payload = encoded["record-canonical-bytes"]
        if (
            type(payload) is not bytes
            or not payload
            or len(payload) > MAXIMUM_LINUX_CONFINEMENT_RECORD_PAYLOAD_BYTES
        ):
            _fail(
                LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE
            )
        if (
            _u64(encoded["record-byte-count"]) != len(payload)
            or _sha256(
                encoded["record-plain-sha256"], nonzero=False
            )
            != _plain_sha256(payload)
            or _sha256(encoded["record-sha256"], nonzero=False)
            != _domain_sha256(artifact_type, payload)
        ):
            _fail(
                LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH
            )
        result.append(
            _Observation(
                record_id=expected_id,
                raw=raw,
                plain_sha256=_plain_sha256(raw),
                sha256=_domain_sha256(
                    LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_DIGEST_DOMAIN,
                    raw,
                ),
            )
        )
    return tuple(result)


def _parse_event(
    value: bytes,
    capture_values: dict,
) -> _Event:
    encoded = _parse_frame(
        value,
        _EVENT_FIELDS,
        maximum=MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_RECORD_BYTES,
    )
    if (
        _token(encoded["artifact-type"])
        != LINUX_CONFINEMENT_STAGING_EVENT_RECORD_ARTIFACT_TYPE
        or _token(encoded["format-version"]) != "1"
    ):
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    sequence = _u64(
        encoded["sequence-number"],
        maximum=_MAXIMUM_EVENT_SEQUENCE_NUMBER,
    )
    timestamp = _u64(encoded["monotonic-timestamp-ns"])
    event_id = _token(encoded["event-id"])
    if (
        _sha256(encoded["staging-run-binding-sha256"])
        != capture_values["staging-run-binding-sha256"]
    ):
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)
    evidence_raw = encoded["evidence-digest-sha256"]
    if event_id in _EVIDENCE_EVENTS:
        evidence = _sha256(evidence_raw)
    elif evidence_raw == b"":
        evidence = ""
    else:
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    return _Event(
        sequence_number=sequence,
        monotonic_timestamp_ns=timestamp,
        event_id=event_id,
        evidence_digest_sha256=evidence,
        raw=value,
        plain_sha256=_plain_sha256(value),
        sha256=_domain_sha256(
            LINUX_CONFINEMENT_STAGING_EVENT_RECORD_DIGEST_DOMAIN,
            value,
        ),
    )


def _parse_gate(
    value: bytes,
    capture_values: dict,
    observations: Tuple[_Observation, ...],
    *,
    stage: int,
    stage1_gate: _Gate | None = None,
) -> _Gate:
    if stage == 1:
        schema = _GATE_COMMON_FIELDS
        artifact_type = (
            LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
        )
        gate_id = "stage1-required-observation-gate"
        event_id = "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED"
        observation_ids = _STAGE1_OBSERVATIONS
        prior_ids = _STAGE1_PRIOR_EVENTS
    elif stage == 2:
        schema = _STAGE2_GATE_FIELDS
        artifact_type = (
            LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
        )
        gate_id = "stage2-required-observation-gate"
        event_id = "STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED"
        observation_ids = _STAGE2_OBSERVATIONS
        prior_ids = _STAGE2_PRIOR_EVENTS
        if type(stage1_gate) is not _Gate:
            _fail(LinuxConfinementPreimageVerificationCode.INPUT_TYPE)
    else:
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    encoded = _parse_frame(
        value,
        schema,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
    )
    if (
        _token(encoded["artifact-type"]) != artifact_type
        or _token(encoded["format-version"]) != "1"
        or _token(encoded["release-gate-id"]) != gate_id
        or _token(encoded["staging-event-id"]) != event_id
    ):
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    _check_capture(encoded, capture_values)
    _tokens(
        encoded["required-observation-ids"],
        observation_ids,
        maximum_total=MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
    )
    expected_observation_sha256s = tuple(
        item.sha256
        for item in observations
        if item.record_id in frozenset(observation_ids)
    )
    actual_observation_sha256s = _sha256s(
        encoded["ordered-observation-record-sha256s"],
        expected_count=len(observation_ids),
        maximum_total=MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
    )
    if actual_observation_sha256s != expected_observation_sha256s:
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)
    _tokens(
        encoded["required-prior-staging-event-ids"],
        prior_ids,
        maximum_total=MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
    )
    prior_sha256s = _sha256s(
        encoded[
            "prior-staging-event-record-sha256s-in-required-event-id-order"
        ],
        expected_count=len(prior_ids),
        maximum_total=MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
    )
    plain = _plain_sha256(value)
    domain = _domain_sha256(artifact_type, value)
    if stage == 2:
        assert stage1_gate is not None
        if (
            _token(
                encoded[
                    "stage1-release-gate-preimage-artifact-type"
                ]
            )
            != LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
            or _u64(
                encoded["stage1-release-gate-preimage-byte-count"]
            )
            != len(stage1_gate.raw)
            or _sha256(
                encoded[
                    "stage1-release-gate-preimage-plain-sha256"
                ],
                nonzero=False,
            )
            != stage1_gate.plain_sha256
            or _sha256(
                encoded["stage1-release-gate-preimage-sha256"]
            )
            != stage1_gate.sha256
            or _sha256(
                encoded[
                    "stage1-release-gate-event-evidence-digest-sha256"
                ]
            )
            != stage1_gate.sha256
        ):
            _fail(
                LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH
            )
    return _Gate(
        raw=value,
        plain_sha256=plain,
        sha256=domain,
        observation_sha256s=actual_observation_sha256s,
        prior_event_ids=prior_ids,
        prior_event_sha256s=prior_sha256s,
    )


def _parse_event_vectors(
    encoded: dict[str, bytes],
    capture_values: dict,
    expected_ids: Tuple[str, ...],
    *,
    maximum: int,
) -> Tuple[_Event, ...]:
    count = _u64(encoded["event-count"])
    if count != len(expected_ids):
        _fail(LinuxConfinementPreimageVerificationCode.ORDER_INVALID)
    _tokens(
        encoded["ordered-event-ids"],
        expected_ids,
        maximum_total=maximum,
    )
    event_raw = _parse_counted(
        encoded["ordered-event-record-canonical-bytes"],
        expected_count=len(expected_ids),
        maximum_entry=MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_RECORD_BYTES,
        maximum_total=maximum,
    )
    byte_count_raw = _parse_counted(
        encoded["ordered-event-record-byte-counts"],
        expected_count=len(expected_ids),
        maximum_entry=8,
        maximum_total=maximum,
    )
    byte_counts = tuple(_u64(item) for item in byte_count_raw)
    plain = _sha256s(
        encoded["ordered-event-record-plain-sha256s"],
        expected_count=len(expected_ids),
        maximum_total=maximum,
    )
    domain = _sha256s(
        encoded["ordered-event-record-sha256s"],
        expected_count=len(expected_ids),
        maximum_total=maximum,
    )
    events = tuple(
        _parse_event(item, capture_values) for item in event_raw
    )
    if (
        tuple(item.event_id for item in events) != expected_ids
        or tuple(item.sequence_number for item in events)
        != tuple(range(len(events)))
        or tuple(len(item.raw) for item in events) != byte_counts
        or tuple(item.plain_sha256 for item in events) != plain
        or tuple(item.sha256 for item in events) != domain
        or any(
            later.monotonic_timestamp_ns < earlier.monotonic_timestamp_ns
            for earlier, later in zip(events, events[1:])
        )
    ):
        _fail(LinuxConfinementPreimageVerificationCode.ORDER_INVALID)
    return events


def _parse_release_transcript(
    value: bytes,
    capture_values: dict,
    gate1: _Gate,
    gate2: _Gate,
    *,
    full: bool,
    completion_sha256: str = "",
) -> _Transcript:
    encoded = _parse_frame(
        value,
        _TRANSCRIPT_FIELDS,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
    )
    if full:
        artifact_type = (
            LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_ARTIFACT_TYPE
        )
        record_id = "full-release-transcript-through-inner-v1-complete"
        terminal_phase = "INNER_COMPLETE"
        terminal_event = "INNER_V1_COMPLETE"
    else:
        artifact_type = (
            LINUX_CONFINEMENT_PRE_COMPLETION_RELEASE_PREFIX_ARTIFACT_TYPE
        )
        record_id = "pre-completion-release-prefix-through-stage2-released"
        terminal_phase = "STAGE2_RELEASED"
        terminal_event = "STAGE2_RELEASED"
    if (
        _token(encoded["artifact-type"]) != artifact_type
        or _token(encoded["format-version"]) != "1"
        or _token(encoded["record-id"]) != record_id
        or _token(encoded["terminal-phase-id"]) != terminal_phase
        or _token(encoded["terminal-event-id"]) != terminal_event
    ):
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    _check_capture(
        encoded,
        capture_values,
        policy_field="linux-confinement-policy-sha256",
    )
    prefix_ids = None
    for candidate in (
        _RELEASE_PREFIX_READY_FIRST,
        _RELEASE_PREFIX_STOP_FIRST,
    ):
        expected = candidate + (("INNER_V1_COMPLETE",) if full else ())
        try:
            _tokens(
                encoded["ordered-event-ids"],
                expected,
                maximum_total=(
                    MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES
                ),
            )
        except LinuxConfinementPreimageVerificationError as error:
            if (
                error.code
                != LinuxConfinementPreimageVerificationCode.ORDER_INVALID.value
            ):
                raise
        else:
            prefix_ids = expected
            break
    if prefix_ids is None:
        _fail(LinuxConfinementPreimageVerificationCode.ORDER_INVALID)
    events = _parse_event_vectors(
        encoded,
        capture_values,
        prefix_ids,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
    )
    if (
        events[2].evidence_digest_sha256 != gate1.sha256
        or events[7].evidence_digest_sha256 != gate2.sha256
        or _sha256(
            encoded[
                "stage1-release-gate-event-evidence-digest-sha256"
            ]
        )
        != gate1.sha256
        or _sha256(
            encoded[
                "stage2-release-gate-event-evidence-digest-sha256"
            ]
        )
        != gate2.sha256
        or (
            full
            and events[-1].evidence_digest_sha256 != completion_sha256
        )
    ):
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)
    return _Transcript(
        raw=value,
        plain_sha256=_plain_sha256(value),
        sha256=_domain_sha256(artifact_type, value),
        events=events,
    )


class _DuplicateKeyError(ValueError):
    pass


def _pairs_without_duplicates(
    pairs: list[Tuple[str, object]],
) -> dict:
    result = {}
    for key, item in pairs:
        if type(key) is not str or key in result:
            raise _DuplicateKeyError
        result[key] = item
    return result


def _reject_json_constant(_: str) -> object:
    raise ValueError


def _reject_json_float(_: str) -> object:
    raise ValueError


def _parse_json_integer(value: str) -> int:
    result = int(value, 10)
    if result < 0 or result > _MAXIMUM_U64:
        raise ValueError
    return result


def _parse_inner_receipt(value: bytes) -> _InnerReceipt:
    if type(value) is not bytes:
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_TYPE)
    if not value or len(value) > MAXIMUM_SOURCE_BOUND_RUN_RECEIPT_BYTES:
        _fail(
            LinuxConfinementPreimageVerificationCode.INNER_RECEIPT_INVALID
        )
    try:
        text = value.decode("ascii", "strict")
        tree = json.loads(
            text,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_json_constant,
            parse_float=_reject_json_float,
            parse_int=_parse_json_integer,
        )
        receipt_fields = fields(SourceBoundAdapterChildRunReceiptV1)
        if (
            type(tree) is not dict
            or set(tree) != {item.name for item in receipt_fields}
        ):
            raise ValueError
        receipt = SourceBoundAdapterChildRunReceiptV1(
            **{
                item.name: tree[item.name]
                for item in receipt_fields
                if item.init
            }
        )
        expected_tree = {
            item.name: getattr(receipt, item.name)
            for item in receipt_fields
        }
        canonical = json.dumps(
            expected_tree,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii", "strict")
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        ValueError,
        UnicodeError,
        _DuplicateKeyError,
    ):
        _fail(
            LinuxConfinementPreimageVerificationCode.INNER_RECEIPT_INVALID
        )
    if (
        canonical != value
        or tree != expected_tree
        or tree["artifact_type"]
        != SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE
        or any(tree[name] is not False for name in _FALSE_FIELDS)
    ):
        _fail(
            LinuxConfinementPreimageVerificationCode.INNER_RECEIPT_INVALID
        )
    digest_names = (
        "run_input_sha256",
        "request_frame_sha256",
        "case_input_sha256",
        "implementation_closure_sha256",
        "implementation_closure_validation_receipt_sha256",
        "closure_pipe_frame_sha256",
    )
    if any(
        type(tree[name]) is not str
        or len(tree[name]) != 64
        or _SHA256_RE.fullmatch(tree[name]) is None
        for name in digest_names
    ):
        _fail(
            LinuxConfinementPreimageVerificationCode.INNER_RECEIPT_INVALID
        )
    return _InnerReceipt(
        raw=value,
        byte_count=len(value),
        plain_sha256=_plain_sha256(value),
        sha256=_domain_sha256(
            SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE,
            value,
        ),
        run_input_sha256=tree["run_input_sha256"],
        request_frame_sha256=tree["request_frame_sha256"],
        case_input_sha256=tree["case_input_sha256"],
        implementation_closure_sha256=(
            tree["implementation_closure_sha256"]
        ),
        implementation_closure_validation_receipt_sha256=(
            tree[
                "implementation_closure_validation_receipt_sha256"
            ]
        ),
        closure_pipe_frame_sha256=tree["closure_pipe_frame_sha256"],
    )


def _check_false_ledger(value: bytes) -> None:
    entries = _parse_counted(
        value,
        expected_count=len(_FALSE_FIELDS),
        maximum_entry=_MAXIMUM_TOKEN_BYTES + 9,
        maximum_total=MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
    )
    for entry, expected_name in zip(entries, _FALSE_FIELDS):
        name_length, cursor = _read_u64_at(
            entry,
            0,
            ceiling=_MAXIMUM_TOKEN_BYTES + 9,
        )
        if name_length == 0 or name_length > _MAXIMUM_TOKEN_BYTES:
            _fail(LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE)
        name_raw, cursor = _take(
            entry,
            cursor,
            name_length,
            ceiling=_MAXIMUM_TOKEN_BYTES,
        )
        false_raw, cursor = _take(entry, cursor, 1, ceiling=1)
        if (
            cursor != len(entry)
            or _token(name_raw) != expected_name
            or false_raw != b"\x00"
        ):
            _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)


def _parse_completion(
    value: bytes,
    capture_values: dict,
    gate1: _Gate,
    gate2: _Gate,
    prefix: _Transcript,
) -> _Completion:
    encoded = _parse_frame(
        value,
        _COMPLETION_FIELDS,
        maximum=MAXIMUM_LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_BYTES,
    )
    if (
        _token(encoded["artifact-type"])
        != LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE
        or _token(encoded["format-version"]) != "1"
        or _token(encoded["record-id"])
        != "native-supervisor-inner-v1-completion-record"
    ):
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    _check_capture(
        encoded,
        capture_values,
        policy_field="linux-confinement-policy-sha256",
        include_subject=False,
    )
    references = (
        ("stage1-release-gate-preimage", gate1),
        ("stage2-release-gate-preimage", gate2),
        ("pre-completion-release-prefix", prefix),
    )
    expected_types = (
        LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE,
        LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE,
        LINUX_CONFINEMENT_PRE_COMPLETION_RELEASE_PREFIX_ARTIFACT_TYPE,
    )
    for (prefix_name, artifact), expected_type in zip(
        references, expected_types
    ):
        if (
            _token(encoded[f"{prefix_name}-artifact-type"])
            != expected_type
            or encoded[f"{prefix_name}-canonical-bytes"] != artifact.raw
            or _u64(encoded[f"{prefix_name}-byte-count"])
            != len(artifact.raw)
            or _sha256(
                encoded[f"{prefix_name}-plain-sha256"],
                nonzero=False,
            )
            != artifact.plain_sha256
            or _sha256(encoded[f"{prefix_name}-sha256"])
            != artifact.sha256
        ):
            _fail(
                LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH
            )
    if (
        _sha256(
            encoded[
                "stage1-release-gate-event-evidence-digest-sha256"
            ]
        )
        != gate1.sha256
        or _sha256(
            encoded[
                "stage2-release-gate-event-evidence-digest-sha256"
            ]
        )
        != gate2.sha256
        or _token(
            encoded["pre-completion-release-prefix-terminal-event-id"]
        )
        != "STAGE2_RELEASED"
    ):
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)
    inner = _parse_inner_receipt(
        encoded["inner-v1-receipt-canonical-bytes"]
    )
    if (
        _u64(encoded["inner-v1-receipt-byte-count"])
        != inner.byte_count
        or _sha256(
            encoded["inner-v1-receipt-plain-sha256"],
            nonzero=False,
        )
        != inner.plain_sha256
        or _sha256(encoded["inner-v1-receipt-sha256"])
        != inner.sha256
        or _token(encoded["inner-v1-receipt-artifact-type-record"])
        != SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE
    ):
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)
    _check_false_ledger(
        encoded["inner-v1-inherited-28-false-field-ledger"]
    )
    inner_bindings = (
        ("inner-v1-run-input-sha256", inner.run_input_sha256),
        ("inner-v1-request-frame-sha256", inner.request_frame_sha256),
        ("inner-v1-case-input-sha256", inner.case_input_sha256),
        (
            "inner-v1-implementation-closure-sha256",
            inner.implementation_closure_sha256,
        ),
        (
            "inner-v1-implementation-closure-validation-receipt-sha256",
            inner.implementation_closure_validation_receipt_sha256,
        ),
        (
            "inner-v1-closure-pipe-frame-sha256",
            inner.closure_pipe_frame_sha256,
        ),
    )
    if any(
        _sha256(encoded[name], nonzero=False) != expected
        for name, expected in inner_bindings
    ):
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)
    return _Completion(
        raw=value,
        plain_sha256=_plain_sha256(value),
        sha256=_domain_sha256(
            LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE,
            value,
        ),
        inner=inner,
    )


def _check_gate_event_references(
    gate1: _Gate,
    gate2: _Gate,
    prefix: _Transcript,
) -> None:
    by_id = {item.event_id: item for item in prefix.events}
    if len(by_id) != len(prefix.events):
        _fail(LinuxConfinementPreimageVerificationCode.ORDER_INVALID)
    expected1 = tuple(by_id[name].sha256 for name in gate1.prior_event_ids)
    expected2 = tuple(by_id[name].sha256 for name in gate2.prior_event_ids)
    if (
        gate1.prior_event_sha256s != expected1
        or gate2.prior_event_sha256s != expected2
    ):
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)


def _parse_postrun_transcript(
    value: bytes,
    capture_values: dict,
    gate1: _Gate,
    gate2: _Gate,
    completion: _Completion,
    full: _Transcript,
) -> _Transcript:
    encoded = _parse_frame(
        value,
        _POSTRUN_TRANSCRIPT_FIELDS,
        maximum=MAXIMUM_LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_BYTES,
    )
    if (
        _token(encoded["artifact-type"])
        != LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_ARTIFACT_TYPE
        or _token(encoded["format-version"]) != "1"
        or _token(encoded["record-id"])
        != "postrun-staging-transcript-through-quiescence"
        or _token(encoded["cleanup-branch-id"])
        != "POST_STAGE2_OR_RUNNING"
        or _token(encoded["terminal-phase-id"]) != "QUIESCENT"
        or _token(encoded["terminal-event-id"])
        != "STREAM_EOF_DRAINED"
    ):
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    _check_capture(
        encoded,
        capture_values,
        policy_field="linux-confinement-policy-sha256",
    )
    expected_ids = tuple(item.event_id for item in full.events) + (
        _CLEANUP_EVENTS
    )
    events = _parse_event_vectors(
        encoded,
        capture_values,
        expected_ids,
        maximum=(
            MAXIMUM_LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_BYTES
        ),
    )
    if (
        tuple(item.raw for item in events[: len(full.events)])
        != tuple(item.raw for item in full.events)
        or _sha256(
            encoded[
                "stage1-release-gate-event-evidence-digest-sha256"
            ]
        )
        != gate1.sha256
        or _sha256(
            encoded[
                "stage2-release-gate-event-evidence-digest-sha256"
            ]
        )
        != gate2.sha256
        or _sha256(encoded["inner-v1-completion-record-sha256"])
        != completion.sha256
    ):
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)
    return _Transcript(
        raw=value,
        plain_sha256=_plain_sha256(value),
        sha256=_domain_sha256(
            LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_ARTIFACT_TYPE,
            value,
        ),
        events=events,
    )


@dataclass(frozen=True)
class LinuxConfinementPostrunFinalizationVerificationResultV1:
    """Frozen non-authoritative result from recursive byte verification."""

    envelope_byte_count: int
    envelope_plain_sha256: str
    envelope_sha256: str
    codec_contract_sha256: str
    staging_run_binding_sha256: str
    inner_v1_receipt_sha256: str
    inner_v1_completion_record_sha256: str
    full_release_transcript_sha256: str
    postrun_staging_transcript_sha256: str
    observation_record_commitment_count: int
    full_release_event_count: int
    postrun_event_count: int
    artifact_type: str = field(
        default=(
            LINUX_CONFINEMENT_PREIMAGE_VERIFICATION_RESULT_ARTIFACT_TYPE
        ),
        init=False,
    )
    format_version: str = field(default="1", init=False)
    verifier_id: str = field(
        default=LINUX_CONFINEMENT_PREIMAGE_CODEC_VERIFIER_ID,
        init=False,
    )
    implementation_status_id: str = field(
        default=LINUX_CONFINEMENT_PREIMAGE_VERIFIER_IMPLEMENTATION_STATUS,
        init=False,
    )
    validation_status_id: str = field(
        default=LINUX_CONFINEMENT_PREIMAGE_CODEC_VALIDATION_STATUS,
        init=False,
    )
    byte_level_internal_consistency_validated: bool = field(
        default=True,
        init=False,
    )
    external_capture_pins_matched: bool = field(
        default=True,
        init=False,
    )
    codec_contract_pin_matched: bool = field(
        default=True,
        init=False,
    )
    linux_execution_observed: bool = field(default=False, init=False)
    evidence_custody_authenticated: bool = field(
        default=False,
        init=False,
    )
    release_authorized: bool = field(default=False, init=False)
    confinement_attested: bool = field(default=False, init=False)
    producer_authenticated: bool = field(default=False, init=False)
    kernel_evidence_semantics_validated: bool = field(
        default=False,
        init=False,
    )
    opaque_record_semantics_validated: bool = field(
        default=False,
        init=False,
    )
    hostile_control_campaign_validated: bool = field(
        default=False,
        init=False,
    )
    positive_outer_receipt_authorized: bool = field(
        default=False,
        init=False,
    )
    same_binding_replay_rejected: bool = field(
        default=False,
        init=False,
    )
    fully_recomputed_cross_run_rebinding_rejected_without_external_pins: (
        bool
    ) = field(default=False, init=False)
    decision_eligible: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (
            type(self)
            is not LinuxConfinementPostrunFinalizationVerificationResultV1
            or self.artifact_type
            != LINUX_CONFINEMENT_PREIMAGE_VERIFICATION_RESULT_ARTIFACT_TYPE
            or self.format_version != "1"
            or self.verifier_id
            != LINUX_CONFINEMENT_PREIMAGE_CODEC_VERIFIER_ID
            or self.implementation_status_id
            != LINUX_CONFINEMENT_PREIMAGE_VERIFIER_IMPLEMENTATION_STATUS
            or self.validation_status_id
            != LINUX_CONFINEMENT_PREIMAGE_CODEC_VALIDATION_STATUS
            or type(self.envelope_byte_count) is not int
            or self.envelope_byte_count <= 0
            or self.envelope_byte_count
            > MAXIMUM_LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_BYTES
            or type(self.observation_record_commitment_count) is not int
            or self.observation_record_commitment_count
            != len(_ENVELOPE_OBSERVATIONS)
            or type(self.full_release_event_count) is not int
            or self.full_release_event_count != 10
            or type(self.postrun_event_count) is not int
            or self.postrun_event_count != 19
        ):
            _fail(LinuxConfinementPreimageVerificationCode.RESULT_INVALID)
        digest_names = (
            "envelope_plain_sha256",
            "envelope_sha256",
            "codec_contract_sha256",
            "staging_run_binding_sha256",
            "inner_v1_receipt_sha256",
            "inner_v1_completion_record_sha256",
            "full_release_transcript_sha256",
            "postrun_staging_transcript_sha256",
        )
        if any(
            type(getattr(self, name)) is not str
            or len(getattr(self, name)) != 64
            or _SHA256_RE.fullmatch(getattr(self, name)) is None
            for name in digest_names
        ):
            _fail(LinuxConfinementPreimageVerificationCode.RESULT_INVALID)
        if any(
            getattr(self, name) is not True
            for name in (
                "byte_level_internal_consistency_validated",
                "external_capture_pins_matched",
                "codec_contract_pin_matched",
            )
        ):
            _fail(LinuxConfinementPreimageVerificationCode.RESULT_INVALID)
        nonclaim_names = (
            "linux_execution_observed",
            "evidence_custody_authenticated",
            "release_authorized",
            "confinement_attested",
            "producer_authenticated",
            "kernel_evidence_semantics_validated",
            "opaque_record_semantics_validated",
            "hostile_control_campaign_validated",
            "positive_outer_receipt_authorized",
            "same_binding_replay_rejected",
            (
                "fully_recomputed_cross_run_rebinding_rejected_without_"
                "external_pins"
            ),
            "decision_eligible",
        )
        if any(getattr(self, name) is not False for name in nonclaim_names):
            _fail(LinuxConfinementPreimageVerificationCode.RESULT_INVALID)


def _snapshot_input(
    value: LinuxConfinementPostrunFinalizationVerificationInputV1,
) -> Tuple[bytes, dict, str]:
    if (
        type(value)
        is not LinuxConfinementPostrunFinalizationVerificationInputV1
    ):
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_TYPE)
    try:
        LinuxConfinementPostrunFinalizationVerificationInputV1.__post_init__(
            value
        )
    except LinuxConfinementPreimageVerificationError:
        raise
    except (AttributeError, TypeError):
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_TYPE)
    except ValueError:
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE)
    try:
        capture_values = _capture_values(value.expected_capture)
    except LinuxConfinementPreimageVerificationError:
        raise
    except (AttributeError, TypeError):
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_TYPE)
    except ValueError:
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    return (
        value.envelope_bytes,
        capture_values,
        value.expected_codec_contract_sha256,
    )


def _verify(
    envelope_raw: bytes,
    capture_values: dict,
    expected_codec_sha256: str,
) -> LinuxConfinementPostrunFinalizationVerificationResultV1:
    encoded = _parse_frame(
        envelope_raw,
        _ENVELOPE_FIELDS,
        maximum=(
            MAXIMUM_LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_BYTES
        ),
    )
    if (
        _token(encoded["artifact-type"])
        != LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_ARTIFACT_TYPE
        or _token(encoded["format-version"]) != "1"
        or _token(encoded["envelope-id"])
        != "portable-postrun-finalization-preimage-envelope"
    ):
        _fail(LinuxConfinementPreimageVerificationCode.VALUE_INVALID)
    if (
        _sha256(encoded["codec-contract-sha256"])
        != expected_codec_sha256
    ):
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)
    _check_envelope_capture(encoded, capture_values)

    observations = _parse_observations(
        encoded["ordered-observation-record-commitment-bytes"],
        capture_values,
    )
    gate1 = _parse_gate(
        encoded["stage1-release-gate-preimage-canonical-bytes"],
        capture_values,
        observations,
        stage=1,
    )
    gate2 = _parse_gate(
        encoded["stage2-release-gate-preimage-canonical-bytes"],
        capture_values,
        observations,
        stage=2,
        stage1_gate=gate1,
    )
    prefix = _parse_release_transcript(
        encoded["pre-completion-release-prefix-canonical-bytes"],
        capture_values,
        gate1,
        gate2,
        full=False,
    )
    _check_gate_event_references(gate1, gate2, prefix)
    completion = _parse_completion(
        encoded["inner-v1-completion-record-canonical-bytes"],
        capture_values,
        gate1,
        gate2,
        prefix,
    )
    full = _parse_release_transcript(
        encoded["full-release-transcript-canonical-bytes"],
        capture_values,
        gate1,
        gate2,
        full=True,
        completion_sha256=completion.sha256,
    )
    if tuple(item.raw for item in full.events[:-1]) != tuple(
        item.raw for item in prefix.events
    ):
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)
    postrun = _parse_postrun_transcript(
        encoded["postrun-staging-transcript-canonical-bytes"],
        capture_values,
        gate1,
        gate2,
        completion,
        full,
    )

    inner = completion.inner
    direct_sha256_bindings = (
        ("stage1-release-gate-preimage-sha256", gate1.sha256, True),
        ("stage2-release-gate-preimage-sha256", gate2.sha256, True),
        ("pre-completion-release-prefix-sha256", prefix.sha256, True),
        ("inner-v1-receipt-plain-sha256", inner.plain_sha256, False),
        ("inner-v1-receipt-sha256", inner.sha256, True),
        ("inner-v1-run-input-sha256", inner.run_input_sha256, False),
        (
            "inner-v1-request-frame-sha256",
            inner.request_frame_sha256,
            False,
        ),
        ("inner-v1-case-input-sha256", inner.case_input_sha256, False),
        (
            "inner-v1-implementation-closure-sha256",
            inner.implementation_closure_sha256,
            False,
        ),
        (
            "inner-v1-implementation-closure-validation-receipt-sha256",
            inner.implementation_closure_validation_receipt_sha256,
            False,
        ),
        (
            "inner-v1-closure-pipe-frame-sha256",
            inner.closure_pipe_frame_sha256,
            False,
        ),
        (
            "inner-v1-completion-record-sha256",
            completion.sha256,
            True,
        ),
        ("full-release-transcript-sha256", full.sha256, True),
        ("postrun-staging-transcript-sha256", postrun.sha256, True),
    )
    if (
        _u64(encoded["inner-v1-receipt-byte-count"])
        != inner.byte_count
        or any(
            _sha256(encoded[name], nonzero=nonzero) != expected
            for name, expected, nonzero in direct_sha256_bindings
        )
    ):
        _fail(LinuxConfinementPreimageVerificationCode.BINDING_MISMATCH)

    return LinuxConfinementPostrunFinalizationVerificationResultV1(
        envelope_byte_count=len(envelope_raw),
        envelope_plain_sha256=_plain_sha256(envelope_raw),
        envelope_sha256=_domain_sha256(
            LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_DIGEST_DOMAIN,
            envelope_raw,
        ),
        codec_contract_sha256=expected_codec_sha256,
        staging_run_binding_sha256=(
            capture_values["staging-run-binding-sha256"]
        ),
        inner_v1_receipt_sha256=inner.sha256,
        inner_v1_completion_record_sha256=completion.sha256,
        full_release_transcript_sha256=full.sha256,
        postrun_staging_transcript_sha256=postrun.sha256,
        observation_record_commitment_count=len(observations),
        full_release_event_count=len(full.events),
        postrun_event_count=len(postrun.events),
    )


def verify_linux_confinement_postrun_finalization_envelope(
    value: LinuxConfinementPostrunFinalizationVerificationInputV1,
) -> LinuxConfinementPostrunFinalizationVerificationResultV1:
    """Recursively verify one envelope against explicit external pins."""

    try:
        envelope_raw, capture_values, codec_sha256 = _snapshot_input(value)
        return _verify(envelope_raw, capture_values, codec_sha256)
    except LinuxConfinementPreimageVerificationError:
        raise
    except Exception:
        _fail(LinuxConfinementPreimageVerificationCode.INTERNAL_ERROR)


def linux_confinement_postrun_finalization_verification_result_bytes(
    value: LinuxConfinementPostrunFinalizationVerificationResultV1,
) -> bytes:
    """Serialize the unauthenticated portable validation result."""

    if (
        type(value)
        is not LinuxConfinementPostrunFinalizationVerificationResultV1
    ):
        _fail(LinuxConfinementPreimageVerificationCode.RESULT_INVALID)
    try:
        LinuxConfinementPostrunFinalizationVerificationResultV1.__post_init__(
            value
        )
        tree = {
            item.name: getattr(value, item.name)
            for item in fields(
                LinuxConfinementPostrunFinalizationVerificationResultV1
            )
        }
        raw = json.dumps(
            tree,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii", "strict")
    except LinuxConfinementPreimageVerificationError:
        raise
    except (AttributeError, TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementPreimageVerificationCode.RESULT_INVALID)
    if (
        not raw
        or len(raw)
        > MAXIMUM_LINUX_CONFINEMENT_PREIMAGE_VERIFICATION_RESULT_BYTES
    ):
        _fail(LinuxConfinementPreimageVerificationCode.INPUT_RESOURCE)
    return raw


def linux_confinement_postrun_finalization_verification_result_sha256(
    value: LinuxConfinementPostrunFinalizationVerificationResultV1,
) -> str:
    """Return the domain digest of the portable validation result."""

    return _domain_sha256(
        LINUX_CONFINEMENT_PREIMAGE_VERIFICATION_RESULT_DIGEST_DOMAIN,
        linux_confinement_postrun_finalization_verification_result_bytes(
            value
        ),
    )


def validate_linux_confinement_postrun_finalization_verification_result(
    value: LinuxConfinementPostrunFinalizationVerificationResultV1,
    raw_input: LinuxConfinementPostrunFinalizationVerificationInputV1,
) -> LinuxConfinementPostrunFinalizationVerificationResultV1:
    """Rerun raw verification and require exact result identity."""

    if (
        type(value)
        is not LinuxConfinementPostrunFinalizationVerificationResultV1
        or type(raw_input)
        is not LinuxConfinementPostrunFinalizationVerificationInputV1
    ):
        _fail(LinuxConfinementPreimageVerificationCode.RESULT_INVALID)
    linux_confinement_postrun_finalization_verification_result_bytes(value)
    expected = verify_linux_confinement_postrun_finalization_envelope(
        raw_input
    )
    if value != expected:
        _fail(LinuxConfinementPreimageVerificationCode.RESULT_INVALID)
    return expected


def _validate_frozen_schemas() -> None:
    if (
        tuple(LINUX_CONFINEMENT_CAPTURE_BINDING_FIELD_IDS)
        != _CAPTURE_FIELDS
        or tuple(LINUX_CONFINEMENT_POSTRUN_BINDING_FIELD_IDS)
        != _POSTRUN_BINDING_FIELDS
        or tuple(LINUX_CONFINEMENT_RETAINED_RECORD_FIELD_IDS)
        != _RETAINED_FIELDS
        or tuple(LINUX_CONFINEMENT_STAGING_EVENT_RECORD_FIELD_IDS)
        != _EVENT_FIELDS
        or tuple(LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_FIELD_IDS)
        != _GATE_COMMON_FIELDS
        or tuple(LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_FIELD_IDS)
        != _STAGE2_GATE_FIELDS
        or tuple(LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_FIELD_IDS)
        != _COMPLETION_FIELDS
        or tuple(LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_FIELD_IDS)
        != _TRANSCRIPT_FIELDS
        or tuple(LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_FIELD_IDS)
        != _POSTRUN_TRANSCRIPT_FIELDS
        or tuple(
            LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_FIELD_IDS
        )
        != _ENVELOPE_FIELDS
        or tuple(LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS)
        != _FALSE_FIELDS
        or tuple(_OBSERVATION_METADATA)
        != _ENVELOPE_OBSERVATIONS
        or tuple(LINUX_CONFINEMENT_STAGE1_REQUIRED_OBSERVATION_IDS)
        != _STAGE1_OBSERVATIONS
        or tuple(LINUX_CONFINEMENT_STAGE2_REQUIRED_OBSERVATION_IDS)
        != _STAGE2_OBSERVATIONS
        or tuple(LINUX_CONFINEMENT_POSTRUN_REQUIRED_OBSERVATION_IDS)
        != _POSTRUN_OBSERVATIONS
        or tuple(LINUX_CONFINEMENT_ENVELOPE_OBSERVATION_IDS)
        != _ENVELOPE_OBSERVATIONS
        or tuple(LINUX_CONFINEMENT_STAGE1_REQUIRED_PRIOR_EVENT_IDS)
        != _STAGE1_PRIOR_EVENTS
        or tuple(LINUX_CONFINEMENT_STAGE2_REQUIRED_PRIOR_EVENT_IDS)
        != _STAGE2_PRIOR_EVENTS
        or tuple(
            LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_READY_FIRST
        )
        != _RELEASE_PREFIX_READY_FIRST
        or tuple(
            LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_STOP_FIRST
        )
        != _RELEASE_PREFIX_STOP_FIRST
        or tuple(LINUX_CONFINEMENT_POSTRUN_CLEANUP_EVENT_IDS)
        != _CLEANUP_EVENTS
        or len(_ENVELOPE_OBSERVATIONS) != 24
    ):
        raise RuntimeError(
            _ERROR_MESSAGES[
                LinuxConfinementPreimageVerificationCode.SCHEMA_DRIFT
            ]
        )


_validate_frozen_schemas()


__all__ = [
    "LINUX_CONFINEMENT_PREIMAGE_VERIFICATION_RESULT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_PREIMAGE_VERIFICATION_RESULT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_PREIMAGE_VERIFIER_IMPLEMENTATION_STATUS",
    "LinuxConfinementPostrunFinalizationVerificationInputV1",
    "LinuxConfinementPostrunFinalizationVerificationResultV1",
    "LinuxConfinementPreimageVerificationCode",
    "LinuxConfinementPreimageVerificationError",
    "MAXIMUM_LINUX_CONFINEMENT_PREIMAGE_VERIFICATION_RESULT_BYTES",
    "linux_confinement_postrun_finalization_verification_result_bytes",
    "linux_confinement_postrun_finalization_verification_result_sha256",
    "validate_linux_confinement_postrun_finalization_verification_result",
    "verify_linux_confinement_postrun_finalization_envelope",
]
