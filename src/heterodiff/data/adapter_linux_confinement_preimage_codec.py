"""Portable canonical preimages for the prospective Linux evidence plan.

This module implements exact byte codecs for retained-record commitments,
staging-event records, the two release-gate preimages, the acyclic inner
completion record, release transcripts, and a post-run finalization
envelope.  It performs no syscall, starts no process, reads no kernel state,
and authenticates no producer.  Consequently a successfully constructed
artifact proves only byte-level internal consistency, never Linux execution,
evidence custody, confinement, hostile-control success, or release safety.

Every declared-field sequence has this exact V1 layout::

    u64be(field_count) ||
        u64be(name_length) || ASCII_NAME ||
        u64be(value_length) || RAW_VALUE || ...

The field names, order, and per-field value codecs are part of each artifact
schema.  The preimage deliberately has no domain prefix.  Its domain digest
is computed exactly once as::

    SHA256(ASCII_DOMAIN || NUL || u64be(preimage_length) || preimage)

Opaque retained-record commitments bind exact caller-supplied bytes and
metadata.  They do not parse the Linux-specific semantics of those bytes.
A future reviewed native supervisor and independent semantic validators must
provide that missing origin, custody, and kernel-evidence layer.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Final, Tuple

from .adapter_linux_confinement_acceptance import (
    LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS,
)
from .adapter_linux_confinement_evidence_plan import (
    LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_PRE_COMPLETION_RELEASE_PREFIX_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE,
    LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE,
    linux_confinement_evidence_plan_tree,
)
from .adapter_linux_confinement_staging_protocol import (
    LinuxConfinementStagingEvent,
    linux_confinement_staging_run_binding_sha256,
)
from .adapter_source_bound_child_runner import (
    MAXIMUM_SOURCE_BOUND_RUN_RECEIPT_BYTES,
    SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE,
    SourceBoundAdapterChildRunReceiptV1,
)


LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-preimage-codec-contract.v1"
)
LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-retained-record-commitment.v1"
)
LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_STAGING_EVENT_RECORD_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-staging-event-record.v1"
)
LINUX_CONFINEMENT_STAGING_EVENT_RECORD_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_STAGING_EVENT_RECORD_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-full-release-transcript.v1"
)
LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-postrun-staging-transcript.v1"
)
LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-postrun-finalization-"
    "envelope.v1"
)
LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_PREIMAGE_CODEC_IMPLEMENTATION_STATUS: Final = (
    "PORTABLE_CANONICAL_CODEC_IMPLEMENTED_LINUX_ORIGIN_UNEXECUTED"
)
LINUX_CONFINEMENT_PREIMAGE_CODEC_VALIDATION_STATUS: Final = (
    "BYTE_LEVEL_INTERNAL_CONSISTENCY_ONLY"
)
LINUX_CONFINEMENT_PREIMAGE_ENCODING_ID: Final = (
    "length-framed-declared-field-sequence-v1"
)
LINUX_CONFINEMENT_PREIMAGE_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-preimage-v1"
)
LINUX_CONFINEMENT_PREIMAGE_CODEC_VERIFIER_ID: Final = (
    "heterodiff.adapter.linux-confinement-preimage-independent-"
    "verifier.v1"
)
LINUX_CONFINEMENT_OPAQUE_RECORD_SEMANTIC_STATUS: Final = (
    "NOT_VALIDATED_BY_PORTABLE_CODEC"
)

MAXIMUM_LINUX_CONFINEMENT_RECORD_PAYLOAD_BYTES: Final = 2 * 1024 * 1024
MAXIMUM_LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_BYTES: Final = (
    3 * 1024 * 1024
)
MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_RECORD_BYTES: Final = 16 * 1024
MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES: Final = 256 * 1024
MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES: Final = 4 * 1024 * 1024
MAXIMUM_LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_BYTES: Final = (
    8 * 1024 * 1024
)
MAXIMUM_LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_BYTES: Final = (
    8 * 1024 * 1024
)
MAXIMUM_LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_BYTES: Final = (
    128 * 1024 * 1024
)
MAXIMUM_LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_BYTES: Final = 256 * 1024
MAXIMUM_LINUX_CONFINEMENT_PUBLIC_TOKEN_BYTES: Final = 512
MAXIMUM_LINUX_CONFINEMENT_RUN_SEQUENCE_NUMBER: Final = 4095
MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_SEQUENCE_NUMBER: Final = 127
MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE: Final = 64
MAXIMUM_LINUX_CONFINEMENT_FRAME_FIELDS: Final = 128

LINUX_CONFINEMENT_RECORD_KIND_OBSERVATION: Final = "observation"
LINUX_CONFINEMENT_RECORD_KIND_HOSTILE_CONTROL: Final = "hostile-control"
LINUX_CONFINEMENT_RECORD_KIND_IDS: Final = (
    LINUX_CONFINEMENT_RECORD_KIND_OBSERVATION,
    LINUX_CONFINEMENT_RECORD_KIND_HOSTILE_CONTROL,
)

LINUX_CONFINEMENT_STAGE1_REQUIRED_OBSERVATION_IDS: Final = (
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
LINUX_CONFINEMENT_STAGE2_REQUIRED_OBSERVATION_IDS: Final = (
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
LINUX_CONFINEMENT_POSTRUN_REQUIRED_OBSERVATION_IDS: Final = (
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
LINUX_CONFINEMENT_ENVELOPE_OBSERVATION_IDS: Final = (
    LINUX_CONFINEMENT_STAGE1_REQUIRED_OBSERVATION_IDS
    + LINUX_CONFINEMENT_STAGE2_REQUIRED_OBSERVATION_IDS
    + LINUX_CONFINEMENT_POSTRUN_REQUIRED_OBSERVATION_IDS
)
LINUX_CONFINEMENT_STAGE1_REQUIRED_PRIOR_EVENT_IDS: Final = (
    "SUPERVISOR_CREATED",
    "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
)
LINUX_CONFINEMENT_STAGE2_REQUIRED_PRIOR_EVENT_IDS: Final = (
    "SUPERVISOR_CREATED",
    "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
    "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED",
    "STAGE1_RELEASED",
    "READY_FRAME_ACCEPTED",
    "PIDFD_BOUND_APPLICATION_SIGSTOP_OBSERVED",
    "PRE_RELEASE_STDOUT_DRAINED",
)
LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_READY_FIRST: Final = (
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
LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_STOP_FIRST: Final = (
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
LINUX_CONFINEMENT_POSTRUN_CLEANUP_EVENT_IDS: Final = (
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

LINUX_CONFINEMENT_CAPTURE_BINDING_FIELD_IDS: Final = (
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
LINUX_CONFINEMENT_POSTRUN_BINDING_FIELD_IDS: Final = (
    LINUX_CONFINEMENT_CAPTURE_BINDING_FIELD_IDS
    + (
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
        (
            "inner-v1-implementation-closure-validation-"
            "receipt-sha256"
        ),
        "inner-v1-closure-pipe-frame-sha256",
        "inner-v1-completion-record-sha256",
        "full-release-transcript-sha256",
    )
)

_RETAINED_RECORD_FIELD_IDS: Final = (
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
_STAGING_EVENT_RECORD_FIELD_IDS: Final = (
    "artifact-type",
    "format-version",
    "sequence-number",
    "monotonic-timestamp-ns",
    "event-id",
    "staging-run-binding-sha256",
    "evidence-digest-sha256",
)
_RELEASE_GATE_COMMON_FIELD_IDS: Final = (
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
    (
        "prior-staging-event-record-sha256s-in-required-event-id-"
        "order"
    ),
)
_STAGE2_RELEASE_GATE_ADDITIONAL_FIELD_IDS: Final = (
    "stage1-release-gate-preimage-artifact-type",
    "stage1-release-gate-preimage-byte-count",
    "stage1-release-gate-preimage-plain-sha256",
    "stage1-release-gate-preimage-sha256",
    "stage1-release-gate-event-evidence-digest-sha256",
)
LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_FIELD_IDS: Final = (
    _RELEASE_GATE_COMMON_FIELD_IDS
)
LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_FIELD_IDS: Final = (
    _RELEASE_GATE_COMMON_FIELD_IDS
    + _STAGE2_RELEASE_GATE_ADDITIONAL_FIELD_IDS
)
LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_FIELD_IDS: Final = (
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
    (
        "inner-v1-implementation-closure-validation-"
        "receipt-sha256"
    ),
    "inner-v1-closure-pipe-frame-sha256",
)
_RELEASE_TRANSCRIPT_FIELD_IDS: Final = (
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
_POSTRUN_STAGING_TRANSCRIPT_FIELD_IDS: Final = (
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
_POSTRUN_ENVELOPE_PREFIX_FIELD_IDS: Final = (
    "artifact-type",
    "format-version",
    "envelope-id",
    "codec-contract-sha256",
)
_POSTRUN_ENVELOPE_SUFFIX_FIELD_IDS: Final = (
    "stage1-release-gate-preimage-canonical-bytes",
    "stage2-release-gate-preimage-canonical-bytes",
    "pre-completion-release-prefix-canonical-bytes",
    "inner-v1-completion-record-canonical-bytes",
    "full-release-transcript-canonical-bytes",
    "postrun-staging-transcript-canonical-bytes",
    "postrun-staging-transcript-sha256",
    "ordered-observation-record-commitment-bytes",
)
LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_FIELD_IDS: Final = (
    _POSTRUN_ENVELOPE_PREFIX_FIELD_IDS
    + LINUX_CONFINEMENT_POSTRUN_BINDING_FIELD_IDS
    + _POSTRUN_ENVELOPE_SUFFIX_FIELD_IDS
)

_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_NONZERO_SHA256_RE = re.compile(r"^(?!0{64})[0-9a-f]{64}$")
_MAXIMUM_U64 = (1 << 64) - 1
_ZERO_SHA256 = "0" * 64


class LinuxConfinementPreimageCodecCode(str, Enum):
    """Closed failures for the portable canonical codec."""

    INPUT_TYPE = "LINUX_CONFINEMENT_PREIMAGE_CODEC_INPUT_TYPE"
    INPUT_RESOURCE = "LINUX_CONFINEMENT_PREIMAGE_CODEC_INPUT_RESOURCE"
    VALUE_INVALID = "LINUX_CONFINEMENT_PREIMAGE_CODEC_VALUE_INVALID"
    FRAME_INVALID = "LINUX_CONFINEMENT_PREIMAGE_CODEC_FRAME_INVALID"
    BINDING_MISMATCH = (
        "LINUX_CONFINEMENT_PREIMAGE_CODEC_BINDING_MISMATCH"
    )
    ORDER_INVALID = "LINUX_CONFINEMENT_PREIMAGE_CODEC_ORDER_INVALID"
    INNER_RECEIPT_INVALID = (
        "LINUX_CONFINEMENT_PREIMAGE_CODEC_INNER_RECEIPT_INVALID"
    )
    CONTRACT_DRIFT = "LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_DRIFT"


_ERROR_MESSAGES = MappingProxyType(
    {
        LinuxConfinementPreimageCodecCode.INPUT_TYPE: (
            "Linux confinement preimage input has an invalid exact type"
        ),
        LinuxConfinementPreimageCodecCode.INPUT_RESOURCE: (
            "Linux confinement preimage input exceeds a resource ceiling"
        ),
        LinuxConfinementPreimageCodecCode.VALUE_INVALID: (
            "Linux confinement preimage field value is invalid"
        ),
        LinuxConfinementPreimageCodecCode.FRAME_INVALID: (
            "Linux confinement declared-field frame is invalid"
        ),
        LinuxConfinementPreimageCodecCode.BINDING_MISMATCH: (
            "Linux confinement preimage binding differs"
        ),
        LinuxConfinementPreimageCodecCode.ORDER_INVALID: (
            "Linux confinement preimage sequence order is invalid"
        ),
        LinuxConfinementPreimageCodecCode.INNER_RECEIPT_INVALID: (
            "Linux confinement inner receipt bytes are invalid"
        ),
        LinuxConfinementPreimageCodecCode.CONTRACT_DRIFT: (
            "Linux confinement preimage schema differs from its frozen plan"
        ),
    }
)


class LinuxConfinementPreimageCodecError(ValueError):
    """One nonreflecting failure with a closed machine-readable code."""

    def __init__(self, code: LinuxConfinementPreimageCodecCode) -> None:
        if type(code) is not LinuxConfinementPreimageCodecCode:
            raise TypeError("preimage codec code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: LinuxConfinementPreimageCodecCode) -> None:
    raise LinuxConfinementPreimageCodecError(code) from None


def _validated_token(value: object) -> str:
    if type(value) is not str or not value:
        _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
    if (
        len(encoded) > MAXIMUM_LINUX_CONFINEMENT_PUBLIC_TOKEN_BYTES
        or _TOKEN_RE.fullmatch(value) is None
    ):
        _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
    return value


def _validated_sha256(value: object, *, nonzero: bool = True) -> str:
    matcher = _NONZERO_SHA256_RE if nonzero else _SHA256_RE
    if type(value) is not str or matcher.fullmatch(value) is None:
        _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
    return value


def _validated_u64(value: object, *, maximum: int = _MAXIMUM_U64) -> int:
    if (
        type(value) is not int
        or value < 0
        or value > maximum
        or type(maximum) is not int
        or maximum < 0
        or maximum > _MAXIMUM_U64
    ):
        _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
    return value


def _ascii(value: str) -> bytes:
    return _validated_token(value).encode("ascii", "strict")


def _sha256_bytes(value: str, *, nonzero: bool = True) -> bytes:
    return _validated_sha256(value, nonzero=nonzero).encode(
        "ascii",
        "strict",
    )


def _u64(value: int, *, maximum: int = _MAXIMUM_U64) -> bytes:
    return _validated_u64(value, maximum=maximum).to_bytes(8, "big")


def _plain_sha256(value: bytes) -> str:
    if type(value) is not bytes:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    return hashlib.sha256(value).hexdigest()


def _domain_sha256(domain: str, payload: bytes) -> str:
    if (
        type(domain) is not str
        or type(payload) is not bytes
        or not domain
        or "\x00" in domain
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except UnicodeError:
        _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _counted_bytes(
    values: Tuple[bytes, ...],
    *,
    maximum_count: int = MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE,
    maximum_total: int,
) -> bytes:
    if (
        type(values) is not tuple
        or len(values) > maximum_count
        or any(type(value) is not bytes for value in values)
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    total = 8
    for value in values:
        if len(value) > maximum_total:
            _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
        total += 8 + len(value)
        if total > maximum_total:
            _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
    parts = [len(values).to_bytes(8, "big")]
    for value in values:
        parts.extend((len(value).to_bytes(8, "big"), value))
    return b"".join(parts)


def _counted_tokens(values: Tuple[str, ...], *, maximum_total: int) -> bytes:
    if type(values) is not tuple:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    return _counted_bytes(
        tuple(_ascii(value) for value in values),
        maximum_count=MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE,
        maximum_total=maximum_total,
    )


def _counted_sha256s(
    values: Tuple[str, ...],
    *,
    maximum_total: int,
) -> bytes:
    if type(values) is not tuple:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    return _counted_bytes(
        tuple(_sha256_bytes(value) for value in values),
        maximum_count=MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE,
        maximum_total=maximum_total,
    )


def _counted_u64s(
    values: Tuple[int, ...],
    *,
    maximum_total: int,
) -> bytes:
    if type(values) is not tuple:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    return _counted_bytes(
        tuple(_u64(value) for value in values),
        maximum_count=MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE,
        maximum_total=maximum_total,
    )


def _false_ledger_bytes(
    values: Tuple[Tuple[str, bool], ...],
) -> bytes:
    if (
        type(values) is not tuple
        or len(values)
        > MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    entries = []
    total = 8
    for entry in values:
        if (
            type(entry) is not tuple
            or len(entry) != 2
            or type(entry[0]) is not str
            or type(entry[1]) is not bool
            or entry[1] is not False
        ):
            _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
        name = _ascii(entry[0])
        encoded = len(name).to_bytes(8, "big") + name + b"\x00"
        total += 8 + len(encoded)
        if total > MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES:
            _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
        entries.append(encoded)
    return _counted_bytes(
        tuple(entries),
        maximum_count=MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE,
        maximum_total=MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
    )


def _declared_field_frame(
    field_ids: Tuple[str, ...],
    values: Tuple[bytes, ...],
    *,
    maximum: int,
) -> bytes:
    if (
        type(field_ids) is not tuple
        or type(values) is not tuple
        or len(field_ids) != len(values)
        or not field_ids
        or len(field_ids) > MAXIMUM_LINUX_CONFINEMENT_FRAME_FIELDS
        or len(set(field_ids)) != len(field_ids)
        or any(type(value) is not bytes for value in values)
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    encoded_names = tuple(_ascii(name) for name in field_ids)
    total = 8
    for name, value in zip(encoded_names, values):
        total += 16 + len(name) + len(value)
        if total > maximum:
            _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
    parts = [len(field_ids).to_bytes(8, "big")]
    for name, value in zip(encoded_names, values):
        parts.extend(
            (
                len(name).to_bytes(8, "big"),
                name,
                len(value).to_bytes(8, "big"),
                value,
            )
        )
    result = b"".join(parts)
    if not result or len(result) > maximum:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
    return result


def _decoded_declared_field_frame(
    value: bytes,
    field_ids: Tuple[str, ...],
    *,
    maximum: int,
) -> dict:
    if (
        type(value) is not bytes
        or type(field_ids) is not tuple
        or not value
        or not field_ids
        or len(field_ids) > MAXIMUM_LINUX_CONFINEMENT_FRAME_FIELDS
        or len(set(field_ids)) != len(field_ids)
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    if len(value) > maximum:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
    cursor = 0

    def take(length: int, *, ceiling: int) -> bytes:
        nonlocal cursor
        if (
            type(length) is not int
            or length < 0
            or cursor < 0
            or cursor > len(value)
        ):
            _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
        if length > ceiling:
            _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
        if length > len(value) - cursor:
            _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
        result = value[cursor : cursor + length]
        cursor += length
        return result

    def read_u64() -> int:
        return int.from_bytes(take(8, ceiling=8), "big")

    count = read_u64()
    if count > MAXIMUM_LINUX_CONFINEMENT_FRAME_FIELDS:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
    if count != len(field_ids):
        _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
    result = {}
    for expected_name in field_ids:
        name_length = read_u64()
        name_raw = take(
            name_length,
            ceiling=MAXIMUM_LINUX_CONFINEMENT_PUBLIC_TOKEN_BYTES,
        )
        try:
            name = name_raw.decode("ascii", "strict")
        except UnicodeError:
            _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
        if name != expected_name:
            _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
        result[name] = take(read_u64(), ceiling=maximum)
    if cursor != len(value):
        _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
    return result


@dataclass(frozen=True)
class LinuxConfinementCaptureBindingV1:
    """Eleven values known before either release gate."""

    acceptance_contract_sha256: str
    evidence_plan_sha256: str
    evidence_schema_contract_sha256: str
    linux_platform_profile_sha256: str
    observation_subject_identity: str
    policy_sha256: str
    run_nonce_hex: str
    run_sequence_number: int
    staging_protocol_contract_sha256: str
    staging_run_binding_sha256: str
    supervisor_epoch_id_hex: str

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementCaptureBindingV1:
            _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
        for name in (
            "acceptance_contract_sha256",
            "evidence_plan_sha256",
            "evidence_schema_contract_sha256",
            "linux_platform_profile_sha256",
            "policy_sha256",
            "staging_protocol_contract_sha256",
            "staging_run_binding_sha256",
        ):
            _validated_sha256(getattr(self, name))
        _validated_sha256(self.observation_subject_identity)
        _validated_sha256(self.run_nonce_hex)
        _validated_u64(
            self.run_sequence_number,
            maximum=MAXIMUM_LINUX_CONFINEMENT_RUN_SEQUENCE_NUMBER,
        )
        _validated_sha256(self.supervisor_epoch_id_hex)
        try:
            expected = linux_confinement_staging_run_binding_sha256(
                policy_sha256=self.policy_sha256,
                supervisor_epoch_id_hex=self.supervisor_epoch_id_hex,
                run_sequence_number=self.run_sequence_number,
                run_nonce_hex=self.run_nonce_hex,
            )
        except (TypeError, ValueError):
            _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
        if self.staging_run_binding_sha256 != expected:
            _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)


def _validated_capture_binding(
    value: LinuxConfinementCaptureBindingV1,
) -> None:
    if type(value) is not LinuxConfinementCaptureBindingV1:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    try:
        LinuxConfinementCaptureBindingV1.__post_init__(value)
    except LinuxConfinementPreimageCodecError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)


@dataclass(frozen=True)
class CanonicalLinuxConfinementArtifactV1:
    """One immutable canonical artifact plus both exact identities."""

    artifact_type: str
    canonical_bytes: bytes
    byte_count: int
    plain_sha256: str
    sha256: str

    def __post_init__(self) -> None:
        if (
            type(self) is not CanonicalLinuxConfinementArtifactV1
            or type(self.canonical_bytes) is not bytes
            or not self.canonical_bytes
            or type(self.byte_count) is not int
            or self.byte_count != len(self.canonical_bytes)
        ):
            _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
        _validated_token(self.artifact_type)
        _validated_sha256(self.plain_sha256, nonzero=False)
        _validated_sha256(self.sha256, nonzero=False)
        if (
            self.plain_sha256 != _plain_sha256(self.canonical_bytes)
            or self.sha256
            != _domain_sha256(self.artifact_type, self.canonical_bytes)
        ):
            _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)


def _validated_canonical_artifact(
    value: CanonicalLinuxConfinementArtifactV1,
) -> None:
    if type(value) is not CanonicalLinuxConfinementArtifactV1:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    try:
        CanonicalLinuxConfinementArtifactV1.__post_init__(value)
    except LinuxConfinementPreimageCodecError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)


def _canonical_artifact(
    artifact_type: str,
    canonical_bytes: bytes,
) -> CanonicalLinuxConfinementArtifactV1:
    return CanonicalLinuxConfinementArtifactV1(
        artifact_type=_validated_token(artifact_type),
        canonical_bytes=canonical_bytes,
        byte_count=len(canonical_bytes),
        plain_sha256=_plain_sha256(canonical_bytes),
        sha256=_domain_sha256(artifact_type, canonical_bytes),
    )


@dataclass(frozen=True)
class LinuxConfinementRetainedRecordV1:
    """Opaque bytes bound to one run and one declared record identity."""

    record_kind_id: str
    record_id: str
    lifecycle_stage_id: str
    trusted_producer_id: str
    staging_run_binding_sha256: str
    observation_subject_identity: str
    capture_monotonic_timestamp_ns: int
    record_artifact_type: str
    record_canonical_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementRetainedRecordV1:
            _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
        if self.record_kind_id not in LINUX_CONFINEMENT_RECORD_KIND_IDS:
            _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
        _validated_token(self.record_id)
        _validated_token(self.lifecycle_stage_id)
        _validated_token(self.trusted_producer_id)
        _validated_sha256(self.staging_run_binding_sha256)
        _validated_sha256(self.observation_subject_identity)
        _validated_u64(self.capture_monotonic_timestamp_ns)
        _validated_token(self.record_artifact_type)
        if (
            type(self.record_canonical_bytes) is not bytes
            or not self.record_canonical_bytes
            or len(self.record_canonical_bytes)
            > MAXIMUM_LINUX_CONFINEMENT_RECORD_PAYLOAD_BYTES
        ):
            _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)


def _validated_retained_record(
    value: LinuxConfinementRetainedRecordV1,
) -> None:
    if type(value) is not LinuxConfinementRetainedRecordV1:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    try:
        LinuxConfinementRetainedRecordV1.__post_init__(value)
    except LinuxConfinementPreimageCodecError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)


def linux_confinement_retained_record_commitment_bytes(
    value: LinuxConfinementRetainedRecordV1,
) -> bytes:
    """Bind exact opaque bytes without validating their Linux semantics."""

    _validated_retained_record(value)
    raw = value.record_canonical_bytes
    return _declared_field_frame(
        _RETAINED_RECORD_FIELD_IDS,
        (
            _ascii(
                LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_ARTIFACT_TYPE
            ),
            _ascii("1"),
            _ascii(value.record_kind_id),
            _ascii(value.record_id),
            _ascii(value.lifecycle_stage_id),
            _ascii(value.trusted_producer_id),
            _sha256_bytes(value.staging_run_binding_sha256),
            _sha256_bytes(value.observation_subject_identity),
            _u64(value.capture_monotonic_timestamp_ns),
            _ascii(value.record_artifact_type),
            raw,
            _u64(len(raw)),
            _sha256_bytes(_plain_sha256(raw), nonzero=False),
            _sha256_bytes(
                _domain_sha256(value.record_artifact_type, raw),
                nonzero=False,
            ),
            _ascii(LINUX_CONFINEMENT_OPAQUE_RECORD_SEMANTIC_STATUS),
        ),
        maximum=(
            MAXIMUM_LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_BYTES
        ),
    )


def linux_confinement_retained_record_commitment_sha256(
    value: LinuxConfinementRetainedRecordV1,
) -> str:
    return _domain_sha256(
        LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_DIGEST_DOMAIN,
        linux_confinement_retained_record_commitment_bytes(value),
    )


@dataclass(frozen=True)
class LinuxConfinementStagingEventRecordV1:
    """Exact supplied staging event record; never event-origin evidence."""

    sequence_number: int
    monotonic_timestamp_ns: int
    event_id: str
    staging_run_binding_sha256: str
    evidence_digest_sha256: str = ""

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementStagingEventRecordV1:
            _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
        _validated_u64(
            self.sequence_number,
            maximum=(
                MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_SEQUENCE_NUMBER
            ),
        )
        _validated_u64(self.monotonic_timestamp_ns)
        try:
            event = LinuxConfinementStagingEvent(self.event_id)
        except (TypeError, ValueError):
            _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
        _validated_sha256(self.staging_run_binding_sha256)
        evidence_events = {
            (
                LinuxConfinementStagingEvent
                .SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED
            ),
            (
                LinuxConfinementStagingEvent
                .STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED
            ),
            (
                LinuxConfinementStagingEvent
                .STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED
            ),
            LinuxConfinementStagingEvent.INNER_V1_COMPLETE,
        }
        if event in evidence_events:
            _validated_sha256(self.evidence_digest_sha256)
        elif self.evidence_digest_sha256 != "":
            _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)


def _validated_staging_event_record(
    value: LinuxConfinementStagingEventRecordV1,
) -> None:
    if type(value) is not LinuxConfinementStagingEventRecordV1:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    try:
        LinuxConfinementStagingEventRecordV1.__post_init__(value)
    except LinuxConfinementPreimageCodecError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)


def linux_confinement_staging_event_record_bytes(
    value: LinuxConfinementStagingEventRecordV1,
) -> bytes:
    _validated_staging_event_record(value)
    evidence = (
        b""
        if value.evidence_digest_sha256 == ""
        else _sha256_bytes(value.evidence_digest_sha256)
    )
    return _declared_field_frame(
        _STAGING_EVENT_RECORD_FIELD_IDS,
        (
            _ascii(LINUX_CONFINEMENT_STAGING_EVENT_RECORD_ARTIFACT_TYPE),
            _ascii("1"),
            _u64(value.sequence_number),
            _u64(value.monotonic_timestamp_ns),
            _ascii(value.event_id),
            _sha256_bytes(value.staging_run_binding_sha256),
            evidence,
        ),
        maximum=MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_RECORD_BYTES,
    )


def linux_confinement_staging_event_record_sha256(
    value: LinuxConfinementStagingEventRecordV1,
) -> str:
    return _domain_sha256(
        LINUX_CONFINEMENT_STAGING_EVENT_RECORD_DIGEST_DOMAIN,
        linux_confinement_staging_event_record_bytes(value),
    )


def _decoded_u64(value: bytes, *, maximum: int = _MAXIMUM_U64) -> int:
    if type(value) is not bytes or len(value) != 8:
        _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
    result = int.from_bytes(value, "big")
    if result > maximum:
        _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
    return result


def _decoded_ascii_token(value: bytes) -> str:
    if type(value) is not bytes:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    try:
        result = value.decode("ascii", "strict")
    except UnicodeError:
        _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
    return _validated_token(result)


def _decoded_counted_bytes(
    value: bytes,
    *,
    expected_count: int,
    maximum_entry: int,
    maximum_total: int,
) -> Tuple[bytes, ...]:
    if (
        type(value) is not bytes
        or type(expected_count) is not int
        or expected_count < 0
        or type(maximum_entry) is not int
        or maximum_entry < 0
        or type(maximum_total) is not int
        or maximum_total < 0
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    if len(value) > maximum_total:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
    cursor = 0

    def take(length: int, *, ceiling: int) -> bytes:
        nonlocal cursor
        if length > ceiling:
            _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
        if length > len(value) - cursor:
            _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
        result = value[cursor : cursor + length]
        cursor += length
        return result

    def read_u64() -> int:
        return int.from_bytes(take(8, ceiling=8), "big")

    count = read_u64()
    if count > MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
    if count != expected_count:
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    result = []
    for _ in range(count):
        result.append(take(read_u64(), ceiling=maximum_entry))
    if cursor != len(value):
        _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
    return tuple(result)


def _decoded_staging_event_record(
    value: bytes,
) -> LinuxConfinementStagingEventRecordV1:
    encoded = _decoded_declared_field_frame(
        value,
        _STAGING_EVENT_RECORD_FIELD_IDS,
        maximum=MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_RECORD_BYTES,
    )
    if (
        encoded["artifact-type"]
        != _ascii(LINUX_CONFINEMENT_STAGING_EVENT_RECORD_ARTIFACT_TYPE)
        or encoded["format-version"] != _ascii("1")
    ):
        _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
    evidence_raw = encoded["evidence-digest-sha256"]
    evidence = (
        ""
        if evidence_raw == b""
        else _decoded_ascii_token(evidence_raw)
    )
    return LinuxConfinementStagingEventRecordV1(
        sequence_number=_decoded_u64(
            encoded["sequence-number"],
            maximum=(
                MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_SEQUENCE_NUMBER
            ),
        ),
        monotonic_timestamp_ns=_decoded_u64(
            encoded["monotonic-timestamp-ns"]
        ),
        event_id=_decoded_ascii_token(encoded["event-id"]),
        staging_run_binding_sha256=_decoded_ascii_token(
            encoded["staging-run-binding-sha256"]
        ),
        evidence_digest_sha256=evidence,
    )


def _decoded_transcript_events(
    artifact: CanonicalLinuxConfinementArtifactV1,
    *,
    field_ids: Tuple[str, ...],
    maximum: int,
) -> Tuple[LinuxConfinementStagingEventRecordV1, ...]:
    encoded = _decoded_declared_field_frame(
        artifact.canonical_bytes,
        field_ids,
        maximum=maximum,
    )
    event_count = _decoded_u64(
        encoded["event-count"],
        maximum=MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE,
    )
    raw_events = _decoded_counted_bytes(
        encoded["ordered-event-record-canonical-bytes"],
        expected_count=event_count,
        maximum_entry=MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_RECORD_BYTES,
        maximum_total=maximum,
    )
    return tuple(
        _decoded_staging_event_record(raw) for raw in raw_events
    )


def _plan_record_metadata(
    kind_id: str,
    record_id: str,
) -> Tuple[str, str]:
    tree = linux_confinement_evidence_plan_tree()
    collection_name = (
        "observation_specs"
        if kind_id == LINUX_CONFINEMENT_RECORD_KIND_OBSERVATION
        else "hostile_control_specs"
    )
    matches = [
        item
        for item in tree[collection_name]
        if item["item_id"] == record_id
    ]
    if len(matches) != 1:
        _fail(LinuxConfinementPreimageCodecCode.VALUE_INVALID)
    return (
        matches[0]["lifecycle_stage_id"],
        matches[0]["trusted_producer_id"],
    )


def _validated_retained_records(
    records: Tuple[LinuxConfinementRetainedRecordV1, ...],
    *,
    expected_ids: Tuple[str, ...],
    expected_kind_id: str,
    capture: LinuxConfinementCaptureBindingV1,
) -> Tuple[str, ...]:
    _validated_capture_binding(capture)
    if (
        type(records) is not tuple
        or len(records) != len(expected_ids)
        or any(
            type(record) is not LinuxConfinementRetainedRecordV1
            for record in records
        )
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    for record in records:
        _validated_retained_record(record)
    if tuple(record.record_id for record in records) != expected_ids:
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    digests = []
    for record in records:
        expected_stage, expected_producer = _plan_record_metadata(
            expected_kind_id,
            record.record_id,
        )
        if (
            record.record_kind_id != expected_kind_id
            or record.staging_run_binding_sha256
            != capture.staging_run_binding_sha256
            or record.observation_subject_identity
            != capture.observation_subject_identity
            or record.lifecycle_stage_id != expected_stage
            or record.trusted_producer_id != expected_producer
        ):
            _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
        digests.append(
            linux_confinement_retained_record_commitment_sha256(record)
        )
    return tuple(digests)


def _event_records_in_required_order(
    records: Tuple[LinuxConfinementStagingEventRecordV1, ...],
    *,
    expected_ids: Tuple[str, ...],
    capture: LinuxConfinementCaptureBindingV1,
) -> Tuple[str, ...]:
    _validated_capture_binding(capture)
    if (
        type(records) is not tuple
        or len(records) != len(expected_ids)
        or any(
            type(record) is not LinuxConfinementStagingEventRecordV1
            for record in records
        )
    ):
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    for record in records:
        _validated_staging_event_record(record)
        if (
            record.staging_run_binding_sha256
            != capture.staging_run_binding_sha256
        ):
            _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
    if tuple(record.event_id for record in records) != expected_ids:
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    sequences = tuple(record.sequence_number for record in records)
    if (
        len(set(sequences)) != len(sequences)
        or set(sequences) != set(range(len(records)))
    ):
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    ordered = sorted(records, key=lambda item: item.sequence_number)
    if any(
        later.monotonic_timestamp_ns < earlier.monotonic_timestamp_ns
        for earlier, later in zip(ordered, ordered[1:])
    ):
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    by_id = {record.event_id: record.sequence_number for record in records}
    if expected_ids == LINUX_CONFINEMENT_STAGE1_REQUIRED_PRIOR_EVENT_IDS:
        edges = (
            (
                "SUPERVISOR_CREATED",
                "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
            ),
        )
    elif expected_ids == LINUX_CONFINEMENT_STAGE2_REQUIRED_PRIOR_EVENT_IDS:
        edges = (
            (
                "SUPERVISOR_CREATED",
                "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
            ),
            (
                "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
                "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED",
            ),
            (
                "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED",
                "STAGE1_RELEASED",
            ),
            ("STAGE1_RELEASED", "READY_FRAME_ACCEPTED"),
            (
                "STAGE1_RELEASED",
                "PIDFD_BOUND_APPLICATION_SIGSTOP_OBSERVED",
            ),
            ("READY_FRAME_ACCEPTED", "PRE_RELEASE_STDOUT_DRAINED"),
            (
                "PIDFD_BOUND_APPLICATION_SIGSTOP_OBSERVED",
                "PRE_RELEASE_STDOUT_DRAINED",
            ),
        )
    else:
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    if any(by_id[left] >= by_id[right] for left, right in edges):
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    return tuple(
        linux_confinement_staging_event_record_sha256(record)
        for record in records
    )


def _capture_gate_values(
    capture: LinuxConfinementCaptureBindingV1,
) -> Tuple[bytes, ...]:
    _validated_capture_binding(capture)
    return (
        _sha256_bytes(capture.acceptance_contract_sha256),
        _sha256_bytes(capture.evidence_plan_sha256),
        _sha256_bytes(capture.evidence_schema_contract_sha256),
        _sha256_bytes(capture.staging_protocol_contract_sha256),
        _sha256_bytes(capture.staging_run_binding_sha256),
        _sha256_bytes(capture.linux_platform_profile_sha256),
        _sha256_bytes(capture.observation_subject_identity),
        _sha256_bytes(capture.policy_sha256),
        _sha256_bytes(capture.supervisor_epoch_id_hex),
        _u64(
            capture.run_sequence_number,
            maximum=MAXIMUM_LINUX_CONFINEMENT_RUN_SEQUENCE_NUMBER,
        ),
        _sha256_bytes(capture.run_nonce_hex),
    )


def build_linux_confinement_stage1_release_gate_preimage(
    capture: LinuxConfinementCaptureBindingV1,
    observation_records: Tuple[LinuxConfinementRetainedRecordV1, ...],
    prior_event_records: Tuple[
        LinuxConfinementStagingEventRecordV1, ...
    ],
) -> CanonicalLinuxConfinementArtifactV1:
    """Construct the syntactic stage-1 gate; never authorize release."""

    observation_digests = _validated_retained_records(
        observation_records,
        expected_ids=LINUX_CONFINEMENT_STAGE1_REQUIRED_OBSERVATION_IDS,
        expected_kind_id=LINUX_CONFINEMENT_RECORD_KIND_OBSERVATION,
        capture=capture,
    )
    prior_digests = _event_records_in_required_order(
        prior_event_records,
        expected_ids=LINUX_CONFINEMENT_STAGE1_REQUIRED_PRIOR_EVENT_IDS,
        capture=capture,
    )
    raw = _declared_field_frame(
        LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_FIELD_IDS,
        (
            _ascii(
                LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
            ),
            _ascii("1"),
            _ascii("stage1-required-observation-gate"),
            _ascii("STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED"),
        )
        + _capture_gate_values(capture)
        + (
            _counted_tokens(
                LINUX_CONFINEMENT_STAGE1_REQUIRED_OBSERVATION_IDS,
                maximum_total=(
                    MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES
                ),
            ),
            _counted_sha256s(
                observation_digests,
                maximum_total=(
                    MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES
                ),
            ),
            _counted_tokens(
                LINUX_CONFINEMENT_STAGE1_REQUIRED_PRIOR_EVENT_IDS,
                maximum_total=(
                    MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES
                ),
            ),
            _counted_sha256s(
                prior_digests,
                maximum_total=(
                    MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES
                ),
            ),
        ),
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
    )
    return _canonical_artifact(
        LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE,
        raw,
    )


def build_linux_confinement_stage2_release_gate_preimage(
    capture: LinuxConfinementCaptureBindingV1,
    observation_records: Tuple[LinuxConfinementRetainedRecordV1, ...],
    prior_event_records: Tuple[
        LinuxConfinementStagingEventRecordV1, ...
    ],
    stage1_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    stage1_gate_event_record: LinuxConfinementStagingEventRecordV1,
) -> CanonicalLinuxConfinementArtifactV1:
    """Construct the syntactic stage-2 gate; never authorize release."""

    _validated_capture_binding(capture)
    if (
        type(stage1_gate_preimage)
        is not CanonicalLinuxConfinementArtifactV1
        or type(stage1_gate_event_record)
        is not LinuxConfinementStagingEventRecordV1
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    _validated_canonical_artifact(stage1_gate_preimage)
    _validated_staging_event_record(stage1_gate_event_record)
    if (
        stage1_gate_preimage.artifact_type
        != LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
        or stage1_gate_event_record.event_id
        != "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED"
        or stage1_gate_event_record.evidence_digest_sha256
        != stage1_gate_preimage.sha256
        or stage1_gate_event_record.staging_run_binding_sha256
        != capture.staging_run_binding_sha256
    ):
        _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
    observation_digests = _validated_retained_records(
        observation_records,
        expected_ids=LINUX_CONFINEMENT_STAGE2_REQUIRED_OBSERVATION_IDS,
        expected_kind_id=LINUX_CONFINEMENT_RECORD_KIND_OBSERVATION,
        capture=capture,
    )
    prior_digests = _event_records_in_required_order(
        prior_event_records,
        expected_ids=LINUX_CONFINEMENT_STAGE2_REQUIRED_PRIOR_EVENT_IDS,
        capture=capture,
    )
    matching_stage1 = [
        record
        for record in prior_event_records
        if record.event_id
        == "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED"
    ]
    if (
        len(matching_stage1) != 1
        or linux_confinement_staging_event_record_bytes(
            matching_stage1[0]
        )
        != linux_confinement_staging_event_record_bytes(
            stage1_gate_event_record
        )
    ):
        _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
    raw = _declared_field_frame(
        LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_FIELD_IDS,
        (
            _ascii(
                LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
            ),
            _ascii("1"),
            _ascii("stage2-required-observation-gate"),
            _ascii("STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED"),
        )
        + _capture_gate_values(capture)
        + (
            _counted_tokens(
                LINUX_CONFINEMENT_STAGE2_REQUIRED_OBSERVATION_IDS,
                maximum_total=(
                    MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES
                ),
            ),
            _counted_sha256s(
                observation_digests,
                maximum_total=(
                    MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES
                ),
            ),
            _counted_tokens(
                LINUX_CONFINEMENT_STAGE2_REQUIRED_PRIOR_EVENT_IDS,
                maximum_total=(
                    MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES
                ),
            ),
            _counted_sha256s(
                prior_digests,
                maximum_total=(
                    MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES
                ),
            ),
            _ascii(
                LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
            ),
            _u64(stage1_gate_preimage.byte_count),
            _sha256_bytes(
                stage1_gate_preimage.plain_sha256,
                nonzero=False,
            ),
            _sha256_bytes(stage1_gate_preimage.sha256),
            _sha256_bytes(
                stage1_gate_event_record.evidence_digest_sha256
            ),
        ),
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
    )
    return _canonical_artifact(
        LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE,
        raw,
    )


def _validated_chronological_events(
    records: Tuple[LinuxConfinementStagingEventRecordV1, ...],
    *,
    expected_ids: Tuple[str, ...],
    capture: LinuxConfinementCaptureBindingV1,
) -> None:
    _validated_capture_binding(capture)
    if (
        type(records) is not tuple
        or len(records) != len(expected_ids)
        or any(
            type(record) is not LinuxConfinementStagingEventRecordV1
            for record in records
        )
    ):
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    for record in records:
        _validated_staging_event_record(record)
    if tuple(record.event_id for record in records) != expected_ids:
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    for index, record in enumerate(records):
        if (
            record.sequence_number != index
            or record.staging_run_binding_sha256
            != capture.staging_run_binding_sha256
            or (
                index > 0
                and record.monotonic_timestamp_ns
                < records[index - 1].monotonic_timestamp_ns
            )
        ):
            _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)


def _release_transcript_values(
    *,
    artifact_type: str,
    record_id: str,
    capture: LinuxConfinementCaptureBindingV1,
    terminal_phase_id: str,
    terminal_event_id: str,
    events: Tuple[LinuxConfinementStagingEventRecordV1, ...],
    stage1_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    stage2_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    maximum: int,
) -> Tuple[bytes, ...]:
    event_bytes = tuple(
        linux_confinement_staging_event_record_bytes(event)
        for event in events
    )
    event_plain = tuple(_plain_sha256(raw) for raw in event_bytes)
    event_domain = tuple(
        _domain_sha256(
            LINUX_CONFINEMENT_STAGING_EVENT_RECORD_DIGEST_DOMAIN,
            raw,
        )
        for raw in event_bytes
    )
    return (
        _ascii(artifact_type),
        _ascii("1"),
        _ascii(record_id),
        _sha256_bytes(capture.acceptance_contract_sha256),
        _sha256_bytes(capture.evidence_plan_sha256),
        _sha256_bytes(capture.evidence_schema_contract_sha256),
        _sha256_bytes(capture.staging_protocol_contract_sha256),
        _sha256_bytes(capture.staging_run_binding_sha256),
        _sha256_bytes(capture.policy_sha256),
        _sha256_bytes(capture.linux_platform_profile_sha256),
        _sha256_bytes(capture.observation_subject_identity),
        _sha256_bytes(capture.supervisor_epoch_id_hex),
        _u64(
            capture.run_sequence_number,
            maximum=MAXIMUM_LINUX_CONFINEMENT_RUN_SEQUENCE_NUMBER,
        ),
        _sha256_bytes(capture.run_nonce_hex),
        _ascii(terminal_phase_id),
        _ascii(terminal_event_id),
        _u64(len(events)),
        _counted_tokens(
            tuple(event.event_id for event in events),
            maximum_total=maximum,
        ),
        _counted_bytes(
            event_bytes,
            maximum_count=MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE,
            maximum_total=maximum,
        ),
        _counted_u64s(
            tuple(len(raw) for raw in event_bytes),
            maximum_total=maximum,
        ),
        _counted_sha256s(event_plain, maximum_total=maximum),
        _counted_sha256s(event_domain, maximum_total=maximum),
        _sha256_bytes(stage1_gate_preimage.sha256),
        _sha256_bytes(stage2_gate_preimage.sha256),
    )


def _validate_gate_artifact_pair(
    stage1_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    stage2_gate_preimage: CanonicalLinuxConfinementArtifactV1,
) -> None:
    if (
        type(stage1_gate_preimage)
        is not CanonicalLinuxConfinementArtifactV1
        or type(stage2_gate_preimage)
        is not CanonicalLinuxConfinementArtifactV1
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    _validated_canonical_artifact(stage1_gate_preimage)
    _validated_canonical_artifact(stage2_gate_preimage)
    if (
        stage1_gate_preimage.artifact_type
        != LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
        or stage2_gate_preimage.artifact_type
        != LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)


def build_linux_confinement_pre_completion_release_prefix(
    capture: LinuxConfinementCaptureBindingV1,
    events: Tuple[LinuxConfinementStagingEventRecordV1, ...],
    stage1_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    stage2_gate_preimage: CanonicalLinuxConfinementArtifactV1,
) -> CanonicalLinuxConfinementArtifactV1:
    """Serialize the exact nine-event prefix through ``STAGE2_RELEASED``."""

    _validate_gate_artifact_pair(
        stage1_gate_preimage,
        stage2_gate_preimage,
    )
    if (
        type(events) is not tuple
        or any(
            type(event) is not LinuxConfinementStagingEventRecordV1
            for event in events
        )
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    for event in events:
        _validated_staging_event_record(event)
    event_ids = tuple(event.event_id for event in events)
    if event_ids not in (
        LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_READY_FIRST,
        LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_STOP_FIRST,
    ):
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    _validated_chronological_events(
        events,
        expected_ids=event_ids,
        capture=capture,
    )
    if (
        events[2].evidence_digest_sha256
        != stage1_gate_preimage.sha256
        or events[7].evidence_digest_sha256
        != stage2_gate_preimage.sha256
    ):
        _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
    values = _release_transcript_values(
        artifact_type=(
            LINUX_CONFINEMENT_PRE_COMPLETION_RELEASE_PREFIX_ARTIFACT_TYPE
        ),
        record_id=(
            "pre-completion-release-prefix-through-stage2-released"
        ),
        capture=capture,
        terminal_phase_id="STAGE2_RELEASED",
        terminal_event_id="STAGE2_RELEASED",
        events=events,
        stage1_gate_preimage=stage1_gate_preimage,
        stage2_gate_preimage=stage2_gate_preimage,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
    )
    raw = _declared_field_frame(
        _RELEASE_TRANSCRIPT_FIELD_IDS,
        values,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
    )
    return _canonical_artifact(
        LINUX_CONFINEMENT_PRE_COMPLETION_RELEASE_PREFIX_ARTIFACT_TYPE,
        raw,
    )


def build_linux_confinement_full_release_transcript(
    capture: LinuxConfinementCaptureBindingV1,
    release_prefix: CanonicalLinuxConfinementArtifactV1,
    release_prefix_events: Tuple[
        LinuxConfinementStagingEventRecordV1, ...
    ],
    stage1_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    stage2_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    completion_record: CanonicalLinuxConfinementArtifactV1,
    completion_event: LinuxConfinementStagingEventRecordV1,
) -> CanonicalLinuxConfinementArtifactV1:
    """Append exactly the completion event without creating a hash cycle."""

    expected_prefix = build_linux_confinement_pre_completion_release_prefix(
        capture,
        release_prefix_events,
        stage1_gate_preimage,
        stage2_gate_preimage,
    )
    if (
        type(release_prefix) is not CanonicalLinuxConfinementArtifactV1
        or type(completion_record)
        is not CanonicalLinuxConfinementArtifactV1
        or type(completion_event)
        is not LinuxConfinementStagingEventRecordV1
    ):
        _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
    _validated_canonical_artifact(release_prefix)
    _validated_canonical_artifact(completion_record)
    _validated_staging_event_record(completion_event)
    if (
        release_prefix != expected_prefix
        or completion_record.artifact_type
        != LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE
        or completion_event.event_id != "INNER_V1_COMPLETE"
        or completion_event.sequence_number != len(release_prefix_events)
        or completion_event.staging_run_binding_sha256
        != capture.staging_run_binding_sha256
        or completion_event.evidence_digest_sha256
        != completion_record.sha256
        or completion_event.monotonic_timestamp_ns
        < release_prefix_events[-1].monotonic_timestamp_ns
    ):
        _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
    events = release_prefix_events + (completion_event,)
    values = _release_transcript_values(
        artifact_type=(
            LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_ARTIFACT_TYPE
        ),
        record_id="full-release-transcript-through-inner-v1-complete",
        capture=capture,
        terminal_phase_id="INNER_COMPLETE",
        terminal_event_id="INNER_V1_COMPLETE",
        events=events,
        stage1_gate_preimage=stage1_gate_preimage,
        stage2_gate_preimage=stage2_gate_preimage,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
    )
    raw = _declared_field_frame(
        _RELEASE_TRANSCRIPT_FIELD_IDS,
        values,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
    )
    return _canonical_artifact(
        LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_ARTIFACT_TYPE,
        raw,
    )


def build_linux_confinement_postrun_staging_transcript(
    capture: LinuxConfinementCaptureBindingV1,
    full_release_transcript: CanonicalLinuxConfinementArtifactV1,
    full_release_events: Tuple[
        LinuxConfinementStagingEventRecordV1, ...
    ],
    cleanup_events: Tuple[
        LinuxConfinementStagingEventRecordV1, ...
    ],
    stage1_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    stage2_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    completion_record: CanonicalLinuxConfinementArtifactV1,
) -> CanonicalLinuxConfinementArtifactV1:
    """Bind supplied cleanup milestones through quiescence, not deadlines."""

    _validated_capture_binding(capture)
    _validate_gate_artifact_pair(
        stage1_gate_preimage,
        stage2_gate_preimage,
    )
    if (
        type(full_release_events) is not tuple
        or type(cleanup_events) is not tuple
        or any(
            type(event) is not LinuxConfinementStagingEventRecordV1
            for event in full_release_events + cleanup_events
        )
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    for event in full_release_events + cleanup_events:
        _validated_staging_event_record(event)
    if (
        type(full_release_transcript)
        is not CanonicalLinuxConfinementArtifactV1
        or type(completion_record)
        is not CanonicalLinuxConfinementArtifactV1
    ):
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    _validated_canonical_artifact(full_release_transcript)
    _validated_canonical_artifact(completion_record)
    if (
        full_release_transcript.artifact_type
        != LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_ARTIFACT_TYPE
        or completion_record.artifact_type
        != LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE
        or tuple(event.event_id for event in cleanup_events)
        != LINUX_CONFINEMENT_POSTRUN_CLEANUP_EVENT_IDS
    ):
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    all_events = full_release_events + cleanup_events
    expected_ids = tuple(event.event_id for event in all_events)
    if (
        len(full_release_events) != 10
        or full_release_events[-1].event_id != "INNER_V1_COMPLETE"
        or tuple(
            event.event_id for event in full_release_events[:-1]
        )
        not in (
            LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_READY_FIRST,
            LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_STOP_FIRST,
        )
        or full_release_events[2].evidence_digest_sha256
        != stage1_gate_preimage.sha256
        or full_release_events[7].evidence_digest_sha256
        != stage2_gate_preimage.sha256
        or full_release_events[-1].evidence_digest_sha256
        != completion_record.sha256
        or expected_ids[-9:]
        != LINUX_CONFINEMENT_POSTRUN_CLEANUP_EVENT_IDS
    ):
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    _validated_chronological_events(
        all_events,
        expected_ids=expected_ids,
        capture=capture,
    )
    expected_full_raw = _declared_field_frame(
        _RELEASE_TRANSCRIPT_FIELD_IDS,
        _release_transcript_values(
            artifact_type=(
                LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_ARTIFACT_TYPE
            ),
            record_id=(
                "full-release-transcript-through-inner-v1-complete"
            ),
            capture=capture,
            terminal_phase_id="INNER_COMPLETE",
            terminal_event_id="INNER_V1_COMPLETE",
            events=full_release_events,
            stage1_gate_preimage=stage1_gate_preimage,
            stage2_gate_preimage=stage2_gate_preimage,
            maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
        ),
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
    )
    if full_release_transcript.canonical_bytes != expected_full_raw:
        _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
    event_bytes = tuple(
        linux_confinement_staging_event_record_bytes(event)
        for event in all_events
    )
    event_plain = tuple(_plain_sha256(raw) for raw in event_bytes)
    event_domain = tuple(
        _domain_sha256(
            LINUX_CONFINEMENT_STAGING_EVENT_RECORD_DIGEST_DOMAIN,
            raw,
        )
        for raw in event_bytes
    )
    maximum = MAXIMUM_LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_BYTES
    values = (
        _ascii(
            LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_ARTIFACT_TYPE
        ),
        _ascii("1"),
        _ascii("postrun-staging-transcript-through-quiescence"),
        _sha256_bytes(capture.acceptance_contract_sha256),
        _sha256_bytes(capture.evidence_plan_sha256),
        _sha256_bytes(capture.evidence_schema_contract_sha256),
        _sha256_bytes(capture.staging_protocol_contract_sha256),
        _sha256_bytes(capture.staging_run_binding_sha256),
        _sha256_bytes(capture.policy_sha256),
        _sha256_bytes(capture.linux_platform_profile_sha256),
        _sha256_bytes(capture.observation_subject_identity),
        _sha256_bytes(capture.supervisor_epoch_id_hex),
        _u64(capture.run_sequence_number),
        _sha256_bytes(capture.run_nonce_hex),
        _ascii("POST_STAGE2_OR_RUNNING"),
        _ascii("QUIESCENT"),
        _ascii("STREAM_EOF_DRAINED"),
        _u64(len(all_events)),
        _counted_tokens(expected_ids, maximum_total=maximum),
        _counted_bytes(
            event_bytes,
            maximum_count=MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE,
            maximum_total=maximum,
        ),
        _counted_u64s(
            tuple(len(raw) for raw in event_bytes),
            maximum_total=maximum,
        ),
        _counted_sha256s(event_plain, maximum_total=maximum),
        _counted_sha256s(event_domain, maximum_total=maximum),
        _sha256_bytes(stage1_gate_preimage.sha256),
        _sha256_bytes(stage2_gate_preimage.sha256),
        _sha256_bytes(completion_record.sha256),
    )
    raw = _declared_field_frame(
        _POSTRUN_STAGING_TRANSCRIPT_FIELD_IDS,
        values,
        maximum=maximum,
    )
    return _canonical_artifact(
        LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_ARTIFACT_TYPE,
        raw,
    )


class _DuplicateKeyError(ValueError):
    pass


def _pairs_without_duplicates(
    pairs: list[Tuple[str, object]],
) -> dict:
    result = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _reject_json_constant(_: str) -> object:
    raise ValueError


def _reject_json_float(_: str) -> object:
    raise ValueError


def _parse_json_integer(value: str) -> int:
    parsed = int(value, 10)
    if parsed < 0 or parsed > _MAXIMUM_U64:
        raise ValueError
    return parsed


@dataclass(frozen=True)
class _InnerReceiptMaterial:
    canonical_bytes: bytes
    byte_count: int
    plain_sha256: str
    sha256: str
    run_input_sha256: str
    request_frame_sha256: str
    case_input_sha256: str
    implementation_closure_sha256: str
    implementation_closure_validation_receipt_sha256: str
    closure_pipe_frame_sha256: str


def _parse_inner_receipt(value: bytes) -> _InnerReceiptMaterial:
    if (
        type(value) is not bytes
        or not value
        or len(value) > MAXIMUM_SOURCE_BOUND_RUN_RECEIPT_BYTES
    ):
        _fail(LinuxConfinementPreimageCodecCode.INNER_RECEIPT_INVALID)
    try:
        text = value.decode("ascii", "strict")
        tree = json.loads(
            text,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_json_constant,
            parse_float=_reject_json_float,
            parse_int=_parse_json_integer,
        )
        expected_fields = fields(SourceBoundAdapterChildRunReceiptV1)
        if (
            type(tree) is not dict
            or set(tree) != {item.name for item in expected_fields}
        ):
            raise ValueError
        init_values = {
            item.name: tree[item.name]
            for item in expected_fields
            if item.init
        }
        receipt = SourceBoundAdapterChildRunReceiptV1(**init_values)
        expected_tree = {
            item.name: getattr(receipt, item.name)
            for item in expected_fields
        }
        if tree != expected_tree:
            raise ValueError
        canonical = json.dumps(
            tree,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii", "strict")
    except (
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
        UnicodeError,
        RecursionError,
        _DuplicateKeyError,
    ):
        _fail(LinuxConfinementPreimageCodecCode.INNER_RECEIPT_INVALID)
    if (
        canonical != value
        or tree["artifact_type"]
        != SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE
        or any(
            tree[name] is not False
            for name in LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS
        )
    ):
        _fail(LinuxConfinementPreimageCodecCode.INNER_RECEIPT_INVALID)
    for name in (
        "run_input_sha256",
        "request_frame_sha256",
        "case_input_sha256",
        "implementation_closure_sha256",
        "implementation_closure_validation_receipt_sha256",
        "closure_pipe_frame_sha256",
    ):
        _validated_sha256(tree[name], nonzero=False)
    return _InnerReceiptMaterial(
        canonical_bytes=value,
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


def build_linux_confinement_inner_v1_completion_record(
    capture: LinuxConfinementCaptureBindingV1,
    stage1_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    stage1_gate_event_record: LinuxConfinementStagingEventRecordV1,
    stage2_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    stage2_gate_event_record: LinuxConfinementStagingEventRecordV1,
    release_prefix: CanonicalLinuxConfinementArtifactV1,
    release_prefix_events: Tuple[
        LinuxConfinementStagingEventRecordV1, ...
    ],
    inner_v1_receipt_bytes: bytes,
) -> CanonicalLinuxConfinementArtifactV1:
    """Build the completion preimage before its carrying event exists."""

    _validate_gate_artifact_pair(
        stage1_gate_preimage,
        stage2_gate_preimage,
    )
    if (
        type(stage1_gate_event_record)
        is not LinuxConfinementStagingEventRecordV1
        or type(stage2_gate_event_record)
        is not LinuxConfinementStagingEventRecordV1
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    _validated_staging_event_record(stage1_gate_event_record)
    _validated_staging_event_record(stage2_gate_event_record)
    expected_prefix = build_linux_confinement_pre_completion_release_prefix(
        capture,
        release_prefix_events,
        stage1_gate_preimage,
        stage2_gate_preimage,
    )
    if type(release_prefix) is not CanonicalLinuxConfinementArtifactV1:
        _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
    _validated_canonical_artifact(release_prefix)
    if (
        release_prefix != expected_prefix
        or stage1_gate_event_record.event_id
        != "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED"
        or stage2_gate_event_record.event_id
        != "STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED"
        or stage1_gate_event_record.evidence_digest_sha256
        != stage1_gate_preimage.sha256
        or stage2_gate_event_record.evidence_digest_sha256
        != stage2_gate_preimage.sha256
        or linux_confinement_staging_event_record_bytes(
            stage1_gate_event_record
        )
        != linux_confinement_staging_event_record_bytes(
            release_prefix_events[2]
        )
        or linux_confinement_staging_event_record_bytes(
            stage2_gate_event_record
        )
        != linux_confinement_staging_event_record_bytes(
            release_prefix_events[7]
        )
    ):
        _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
    inner = _parse_inner_receipt(inner_v1_receipt_bytes)
    false_ledger = tuple(
        (name, False)
        for name in LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS
    )
    values = (
        _ascii(
            LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE
        ),
        _ascii("1"),
        _ascii("native-supervisor-inner-v1-completion-record"),
        _sha256_bytes(capture.acceptance_contract_sha256),
        _sha256_bytes(capture.evidence_plan_sha256),
        _sha256_bytes(capture.evidence_schema_contract_sha256),
        _sha256_bytes(capture.staging_protocol_contract_sha256),
        _sha256_bytes(capture.staging_run_binding_sha256),
        _sha256_bytes(capture.policy_sha256),
        _sha256_bytes(capture.linux_platform_profile_sha256),
        _sha256_bytes(capture.supervisor_epoch_id_hex),
        _u64(
            capture.run_sequence_number,
            maximum=MAXIMUM_LINUX_CONFINEMENT_RUN_SEQUENCE_NUMBER,
        ),
        _sha256_bytes(capture.run_nonce_hex),
        _ascii(
            LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
        ),
        stage1_gate_preimage.canonical_bytes,
        _u64(stage1_gate_preimage.byte_count),
        _sha256_bytes(
            stage1_gate_preimage.plain_sha256,
            nonzero=False,
        ),
        _sha256_bytes(stage1_gate_preimage.sha256),
        _sha256_bytes(
            stage1_gate_event_record.evidence_digest_sha256
        ),
        _ascii(
            LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
        ),
        stage2_gate_preimage.canonical_bytes,
        _u64(stage2_gate_preimage.byte_count),
        _sha256_bytes(
            stage2_gate_preimage.plain_sha256,
            nonzero=False,
        ),
        _sha256_bytes(stage2_gate_preimage.sha256),
        _sha256_bytes(
            stage2_gate_event_record.evidence_digest_sha256
        ),
        _ascii(
            LINUX_CONFINEMENT_PRE_COMPLETION_RELEASE_PREFIX_ARTIFACT_TYPE
        ),
        release_prefix.canonical_bytes,
        _u64(release_prefix.byte_count),
        _sha256_bytes(release_prefix.plain_sha256, nonzero=False),
        _sha256_bytes(release_prefix.sha256),
        _ascii("STAGE2_RELEASED"),
        inner.canonical_bytes,
        _u64(inner.byte_count),
        _sha256_bytes(inner.plain_sha256, nonzero=False),
        _sha256_bytes(inner.sha256),
        _ascii(SOURCE_BOUND_ADAPTER_CHILD_RUN_RECEIPT_ARTIFACT_TYPE),
        _false_ledger_bytes(false_ledger),
        _sha256_bytes(inner.run_input_sha256, nonzero=False),
        _sha256_bytes(inner.request_frame_sha256, nonzero=False),
        _sha256_bytes(inner.case_input_sha256, nonzero=False),
        _sha256_bytes(
            inner.implementation_closure_sha256,
            nonzero=False,
        ),
        _sha256_bytes(
            inner.implementation_closure_validation_receipt_sha256,
            nonzero=False,
        ),
        _sha256_bytes(inner.closure_pipe_frame_sha256, nonzero=False),
    )
    if len(values) != len(
        LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_FIELD_IDS
    ):
        _fail(LinuxConfinementPreimageCodecCode.CONTRACT_DRIFT)
    raw = _declared_field_frame(
        LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_FIELD_IDS,
        values,
        maximum=MAXIMUM_LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_BYTES,
    )
    return _canonical_artifact(
        LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE,
        raw,
    )


def _require_same_artifact(
    actual: CanonicalLinuxConfinementArtifactV1,
    expected: CanonicalLinuxConfinementArtifactV1,
) -> None:
    if actual != expected:
        _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)


def _validate_envelope_nested_consistency(
    capture: LinuxConfinementCaptureBindingV1,
    stage1_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    stage2_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    release_prefix: CanonicalLinuxConfinementArtifactV1,
    completion_record: CanonicalLinuxConfinementArtifactV1,
    full_release_transcript: CanonicalLinuxConfinementArtifactV1,
    postrun_staging_transcript: CanonicalLinuxConfinementArtifactV1,
    observation_records: Tuple[LinuxConfinementRetainedRecordV1, ...],
    inner_v1_receipt_bytes: bytes,
) -> None:
    prefix_events = _decoded_transcript_events(
        release_prefix,
        field_ids=_RELEASE_TRANSCRIPT_FIELD_IDS,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
    )
    if len(prefix_events) != 9:
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    stage1_stop = len(
        LINUX_CONFINEMENT_STAGE1_REQUIRED_OBSERVATION_IDS
    )
    stage2_stop = stage1_stop + len(
        LINUX_CONFINEMENT_STAGE2_REQUIRED_OBSERVATION_IDS
    )
    expected_stage1 = (
        build_linux_confinement_stage1_release_gate_preimage(
            capture,
            observation_records[:stage1_stop],
            prefix_events[:2],
        )
    )
    _require_same_artifact(stage1_gate_preimage, expected_stage1)
    prefix_by_id = {
        event.event_id: event for event in prefix_events
    }
    if len(prefix_by_id) != len(prefix_events):
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    if any(
        event_id not in prefix_by_id
        for event_id in (
            LINUX_CONFINEMENT_STAGE2_REQUIRED_PRIOR_EVENT_IDS
        )
    ):
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    stage2_prior_events = tuple(
        prefix_by_id[event_id]
        for event_id in (
            LINUX_CONFINEMENT_STAGE2_REQUIRED_PRIOR_EVENT_IDS
        )
    )
    expected_stage2 = (
        build_linux_confinement_stage2_release_gate_preimage(
            capture,
            observation_records[stage1_stop:stage2_stop],
            stage2_prior_events,
            stage1_gate_preimage,
            prefix_events[2],
        )
    )
    _require_same_artifact(stage2_gate_preimage, expected_stage2)
    expected_prefix = (
        build_linux_confinement_pre_completion_release_prefix(
            capture,
            prefix_events,
            stage1_gate_preimage,
            stage2_gate_preimage,
        )
    )
    _require_same_artifact(release_prefix, expected_prefix)
    expected_completion = (
        build_linux_confinement_inner_v1_completion_record(
            capture,
            stage1_gate_preimage,
            prefix_events[2],
            stage2_gate_preimage,
            prefix_events[7],
            release_prefix,
            prefix_events,
            inner_v1_receipt_bytes,
        )
    )
    _require_same_artifact(completion_record, expected_completion)
    full_events = _decoded_transcript_events(
        full_release_transcript,
        field_ids=_RELEASE_TRANSCRIPT_FIELD_IDS,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
    )
    if len(full_events) != 10:
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    expected_full = build_linux_confinement_full_release_transcript(
        capture,
        release_prefix,
        prefix_events,
        stage1_gate_preimage,
        stage2_gate_preimage,
        completion_record,
        full_events[-1],
    )
    _require_same_artifact(full_release_transcript, expected_full)
    postrun_events = _decoded_transcript_events(
        postrun_staging_transcript,
        field_ids=_POSTRUN_STAGING_TRANSCRIPT_FIELD_IDS,
        maximum=(
            MAXIMUM_LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_BYTES
        ),
    )
    expected_postrun_count = (
        len(full_events)
        + len(LINUX_CONFINEMENT_POSTRUN_CLEANUP_EVENT_IDS)
    )
    if len(postrun_events) != expected_postrun_count:
        _fail(LinuxConfinementPreimageCodecCode.ORDER_INVALID)
    expected_postrun = (
        build_linux_confinement_postrun_staging_transcript(
            capture,
            full_release_transcript,
            full_events,
            postrun_events[len(full_events) :],
            stage1_gate_preimage,
            stage2_gate_preimage,
            completion_record,
        )
    )
    _require_same_artifact(
        postrun_staging_transcript,
        expected_postrun,
    )


def build_linux_confinement_postrun_finalization_envelope(
    capture: LinuxConfinementCaptureBindingV1,
    stage1_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    stage2_gate_preimage: CanonicalLinuxConfinementArtifactV1,
    release_prefix: CanonicalLinuxConfinementArtifactV1,
    completion_record: CanonicalLinuxConfinementArtifactV1,
    full_release_transcript: CanonicalLinuxConfinementArtifactV1,
    postrun_staging_transcript: CanonicalLinuxConfinementArtifactV1,
    observation_records: Tuple[LinuxConfinementRetainedRecordV1, ...],
    inner_v1_receipt_bytes: bytes,
) -> CanonicalLinuxConfinementArtifactV1:
    """Package retained preimages for an independent consistency check.

    Hostile-control campaigns are intentionally excluded: their matched
    permissive and confined trials require distinct run bindings and a later
    campaign manifest.
    """

    _validated_capture_binding(capture)
    _validate_gate_artifact_pair(
        stage1_gate_preimage,
        stage2_gate_preimage,
    )
    expected_artifacts = (
        (
            stage1_gate_preimage,
            LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE,
            LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_FIELD_IDS,
            MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
        ),
        (
            stage2_gate_preimage,
            LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE,
            LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_FIELD_IDS,
            MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES,
        ),
        (
            release_prefix,
            LINUX_CONFINEMENT_PRE_COMPLETION_RELEASE_PREFIX_ARTIFACT_TYPE,
            _RELEASE_TRANSCRIPT_FIELD_IDS,
            MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
        ),
        (
            completion_record,
            LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE,
            LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_FIELD_IDS,
            MAXIMUM_LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_BYTES,
        ),
        (
            full_release_transcript,
            LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_ARTIFACT_TYPE,
            _RELEASE_TRANSCRIPT_FIELD_IDS,
            MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES,
        ),
        (
            postrun_staging_transcript,
            LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_ARTIFACT_TYPE,
            _POSTRUN_STAGING_TRANSCRIPT_FIELD_IDS,
            MAXIMUM_LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_BYTES,
        ),
    )
    for artifact, expected_type, schema, maximum in expected_artifacts:
        if type(artifact) is not CanonicalLinuxConfinementArtifactV1:
            _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
        _validated_canonical_artifact(artifact)
        if artifact.artifact_type != expected_type:
            _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
        encoded = _decoded_declared_field_frame(
            artifact.canonical_bytes,
            schema,
            maximum=maximum,
        )
        if (
            encoded["artifact-type"] != _ascii(expected_type)
            or encoded["format-version"] != _ascii("1")
            or encoded["staging-run-binding-sha256"]
            != _sha256_bytes(capture.staging_run_binding_sha256)
        ):
            _fail(LinuxConfinementPreimageCodecCode.BINDING_MISMATCH)
    _validated_retained_records(
        observation_records,
        expected_ids=LINUX_CONFINEMENT_ENVELOPE_OBSERVATION_IDS,
        expected_kind_id=LINUX_CONFINEMENT_RECORD_KIND_OBSERVATION,
        capture=capture,
    )
    _validate_envelope_nested_consistency(
        capture,
        stage1_gate_preimage,
        stage2_gate_preimage,
        release_prefix,
        completion_record,
        full_release_transcript,
        postrun_staging_transcript,
        observation_records,
        inner_v1_receipt_bytes,
    )
    inner = _parse_inner_receipt(inner_v1_receipt_bytes)
    observation_bytes = tuple(
        linux_confinement_retained_record_commitment_bytes(record)
        for record in observation_records
    )
    values = (
        _ascii(
            LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_ARTIFACT_TYPE
        ),
        _ascii("1"),
        _ascii("portable-postrun-finalization-preimage-envelope"),
        _sha256_bytes(linux_confinement_preimage_codec_contract_sha256()),
        _sha256_bytes(capture.acceptance_contract_sha256),
        _sha256_bytes(capture.evidence_plan_sha256),
        _sha256_bytes(capture.evidence_schema_contract_sha256),
        _sha256_bytes(capture.linux_platform_profile_sha256),
        _sha256_bytes(capture.observation_subject_identity),
        _sha256_bytes(capture.policy_sha256),
        _sha256_bytes(capture.run_nonce_hex),
        _u64(
            capture.run_sequence_number,
            maximum=MAXIMUM_LINUX_CONFINEMENT_RUN_SEQUENCE_NUMBER,
        ),
        _sha256_bytes(capture.staging_protocol_contract_sha256),
        _sha256_bytes(capture.staging_run_binding_sha256),
        _sha256_bytes(capture.supervisor_epoch_id_hex),
        _sha256_bytes(stage1_gate_preimage.sha256),
        _sha256_bytes(stage2_gate_preimage.sha256),
        _sha256_bytes(release_prefix.sha256),
        _u64(inner.byte_count),
        _sha256_bytes(inner.plain_sha256, nonzero=False),
        _sha256_bytes(inner.sha256),
        _sha256_bytes(inner.run_input_sha256, nonzero=False),
        _sha256_bytes(inner.request_frame_sha256, nonzero=False),
        _sha256_bytes(inner.case_input_sha256, nonzero=False),
        _sha256_bytes(
            inner.implementation_closure_sha256,
            nonzero=False,
        ),
        _sha256_bytes(
            inner.implementation_closure_validation_receipt_sha256,
            nonzero=False,
        ),
        _sha256_bytes(inner.closure_pipe_frame_sha256, nonzero=False),
        _sha256_bytes(completion_record.sha256),
        _sha256_bytes(full_release_transcript.sha256),
        stage1_gate_preimage.canonical_bytes,
        stage2_gate_preimage.canonical_bytes,
        release_prefix.canonical_bytes,
        completion_record.canonical_bytes,
        full_release_transcript.canonical_bytes,
        postrun_staging_transcript.canonical_bytes,
        _sha256_bytes(postrun_staging_transcript.sha256),
        _counted_bytes(
            observation_bytes,
            maximum_count=MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE,
            maximum_total=(
                MAXIMUM_LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_BYTES
            ),
        ),
    )
    if len(values) != len(
        LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_FIELD_IDS
    ):
        _fail(LinuxConfinementPreimageCodecCode.CONTRACT_DRIFT)
    raw = _declared_field_frame(
        LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_FIELD_IDS,
        values,
        maximum=(
            MAXIMUM_LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_BYTES
        ),
    )
    return _canonical_artifact(
        LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_ARTIFACT_TYPE,
        raw,
    )


def _field_codec_id(field_id: str) -> str:
    if field_id in {
        "run-sequence-number",
        "sequence-number",
        "monotonic-timestamp-ns",
        "capture-monotonic-timestamp-ns",
        "record-byte-count",
        "event-count",
        "stage1-release-gate-preimage-byte-count",
        "stage2-release-gate-preimage-byte-count",
        "pre-completion-release-prefix-byte-count",
        "inner-v1-receipt-byte-count",
    }:
        return "u64be-v1"
    if field_id in {
        "required-observation-ids",
        "required-prior-staging-event-ids",
        "ordered-event-ids",
    }:
        return "u64-counted-u64-length-ascii-token-sequence-v1"
    if field_id in {
        "ordered-observation-record-sha256s",
        (
            "prior-staging-event-record-sha256s-in-required-event-id-"
            "order"
        ),
        "ordered-event-record-plain-sha256s",
        "ordered-event-record-sha256s",
    }:
        return "u64-counted-u64-length-lowercase-sha256-sequence-v1"
    if field_id == "ordered-event-record-byte-counts":
        return "u64-counted-u64-length-u64be-sequence-v1"
    if field_id in {
        "ordered-event-record-canonical-bytes",
        "ordered-observation-record-commitment-bytes",
    }:
        return "u64-counted-u64-length-opaque-bytes-sequence-v1"
    if field_id == "inner-v1-inherited-28-false-field-ledger":
        return "u64-counted-name-length-name-false-byte-ledger-v1"
    if field_id.endswith("-canonical-bytes"):
        return "opaque-canonical-bytes-v1"
    if "sha256" in field_id or field_id in {
        "run-nonce-hex",
        "supervisor-epoch-id-hex",
        "observation-subject-identity",
    }:
        if field_id == "evidence-digest-sha256":
            return "empty-or-lowercase-nonzero-sha256-ascii-v1"
        return "lowercase-sha256-ascii-v1"
    return "bounded-ascii-token-v1"


def _schema_tree(field_ids: Tuple[str, ...]) -> dict:
    return {
        "field_ids": list(field_ids),
        "value_codec_by_field_id": {
            field_id: _field_codec_id(field_id)
            for field_id in field_ids
        },
    }


def linux_confinement_preimage_codec_contract_tree() -> dict:
    """Return the exact portable-codec contract and its nonclaims."""

    return {
        "artifact_type": (
            LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_ARTIFACT_TYPE
        ),
        "claim_boundary": {
            "all_artifact_inputs_may_be_synthetic": True,
            "canonical_byte_consistency_validated": True,
            "evidence_custody_authenticated": False,
            "hostile_control_campaign_manifest_defined": False,
            "kernel_evidence_semantics_validated": False,
            "linux_execution_observed": False,
            "native_supervisor_implemented": False,
            "opaque_record_semantic_status_id": (
                LINUX_CONFINEMENT_OPAQUE_RECORD_SEMANTIC_STATUS
            ),
            "positive_outer_receipt_authorized": False,
            "release_authorized_by_portable_codec": False,
            "same_binding_replay_rejected": False,
        },
        "declared_field_sequence_layout": [
            "u64be-field-count",
            "repeated-u64be-name-length",
            "repeated-ascii-name",
            "repeated-u64be-value-length",
            "repeated-raw-value",
        ],
        "digest_computation_id": (
            LINUX_CONFINEMENT_PREIMAGE_DIGEST_COMPUTATION_ID
        ),
        "digest_domain": (
            LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_DIGEST_DOMAIN
        ),
        "format_version": "1",
        "hostile_control_scope": {
            "control_count_in_this_envelope": 0,
            "reason_id": (
                "matched-control-campaigns-require-distinct-run-"
                "bindings-and-later-campaign-manifest-v1"
            ),
        },
        "implementation_status_id": (
            LINUX_CONFINEMENT_PREIMAGE_CODEC_IMPLEMENTATION_STATUS
        ),
        "maximums": {
            "completion_record_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_BYTES
            ),
            "contract_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_BYTES
            ),
            "envelope_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_BYTES
            ),
            "frame_fields": MAXIMUM_LINUX_CONFINEMENT_FRAME_FIELDS,
            "gate_preimage_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES
            ),
            "public_token_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_PUBLIC_TOKEN_BYTES
            ),
            "run_sequence_number": (
                MAXIMUM_LINUX_CONFINEMENT_RUN_SEQUENCE_NUMBER
            ),
            "record_commitment_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_BYTES
            ),
            "record_payload_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_RECORD_PAYLOAD_BYTES
            ),
            "records_per_sequence": (
                MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE
            ),
            "release_transcript_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES
            ),
            "postrun_staging_transcript_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_BYTES
            ),
            "staging_event_sequence_number": (
                MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_SEQUENCE_NUMBER
            ),
            "staging_event_record_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_RECORD_BYTES
            ),
        },
        "observation_partition": {
            "envelope_order_ids": list(
                LINUX_CONFINEMENT_ENVELOPE_OBSERVATION_IDS
            ),
            "postrun_ids": list(
                LINUX_CONFINEMENT_POSTRUN_REQUIRED_OBSERVATION_IDS
            ),
            "stage1_ids": list(
                LINUX_CONFINEMENT_STAGE1_REQUIRED_OBSERVATION_IDS
            ),
            "stage2_ids": list(
                LINUX_CONFINEMENT_STAGE2_REQUIRED_OBSERVATION_IDS
            ),
        },
        "preimage_encoding_id": (
            LINUX_CONFINEMENT_PREIMAGE_ENCODING_ID
        ),
        "preimage_has_domain_prefix": False,
        "schemas": {
            "full_release_transcript": _schema_tree(
                _RELEASE_TRANSCRIPT_FIELD_IDS
            ),
            "inner_completion_record": _schema_tree(
                LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_FIELD_IDS
            ),
            "postrun_finalization_envelope": _schema_tree(
                LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_FIELD_IDS
            ),
            "postrun_staging_transcript": _schema_tree(
                _POSTRUN_STAGING_TRANSCRIPT_FIELD_IDS
            ),
            "pre_completion_release_prefix": _schema_tree(
                _RELEASE_TRANSCRIPT_FIELD_IDS
            ),
            "retained_record_commitment": _schema_tree(
                _RETAINED_RECORD_FIELD_IDS
            ),
            "stage1_release_gate": _schema_tree(
                LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_FIELD_IDS
            ),
            "stage2_release_gate": _schema_tree(
                LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_FIELD_IDS
            ),
            "staging_event_record": _schema_tree(
                _STAGING_EVENT_RECORD_FIELD_IDS
            ),
        },
        "subject_identity_semantics_id": (
            "caller-supplied-domain-digest-reference-to-future-canonical-"
            "seven-role-subject-identity-table-v1"
        ),
        "validation_status_id": (
            LINUX_CONFINEMENT_PREIMAGE_CODEC_VALIDATION_STATUS
        ),
        "verifier_id": LINUX_CONFINEMENT_PREIMAGE_CODEC_VERIFIER_ID,
    }


def linux_confinement_preimage_codec_contract_bytes() -> bytes:
    try:
        raw = json.dumps(
            linux_confinement_preimage_codec_contract_tree(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii", "strict")
    except (TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
    if (
        not raw
        or len(raw)
        > MAXIMUM_LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_BYTES
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
    return raw


def parse_linux_confinement_preimage_codec_contract(
    value: bytes,
) -> dict:
    """Strictly parse only the one fixed canonical codec contract."""

    if type(value) is not bytes:
        _fail(LinuxConfinementPreimageCodecCode.INPUT_TYPE)
    if (
        not value
        or len(value)
        > MAXIMUM_LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_BYTES
    ):
        _fail(LinuxConfinementPreimageCodecCode.INPUT_RESOURCE)
    try:
        tree = json.loads(
            value.decode("ascii", "strict"),
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_json_constant,
            parse_float=_reject_json_float,
            parse_int=_parse_json_integer,
        )
    except (
        TypeError,
        ValueError,
        UnicodeError,
        RecursionError,
        _DuplicateKeyError,
    ):
        _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
    if (
        type(tree) is not dict
        or tree != linux_confinement_preimage_codec_contract_tree()
        or value != linux_confinement_preimage_codec_contract_bytes()
    ):
        _fail(LinuxConfinementPreimageCodecCode.FRAME_INVALID)
    return tree


def linux_confinement_preimage_codec_contract_sha256() -> str:
    return _domain_sha256(
        LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_DIGEST_DOMAIN,
        linux_confinement_preimage_codec_contract_bytes(),
    )


def _validate_plan_coherence() -> None:
    plan = linux_confinement_evidence_plan_tree()
    gates = plan["release_gate_specs"]
    completion = plan["inner_v1_completion_record_schema"]
    if (
        tuple(plan["capture_time_run_binding_field_ids"])
        != LINUX_CONFINEMENT_CAPTURE_BINDING_FIELD_IDS
        or tuple(plan["postrun_leaf_finalization_binding_field_ids"])
        != LINUX_CONFINEMENT_POSTRUN_BINDING_FIELD_IDS
        or len(gates) != 2
        or tuple(gates[0]["canonical_preimage_field_ids"])
        != LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_FIELD_IDS
        or tuple(gates[1]["canonical_preimage_field_ids"])
        != LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_FIELD_IDS
        or tuple(gates[0]["required_observation_ids"])
        != LINUX_CONFINEMENT_STAGE1_REQUIRED_OBSERVATION_IDS
        or tuple(gates[1]["required_observation_ids"])
        != LINUX_CONFINEMENT_STAGE2_REQUIRED_OBSERVATION_IDS
        or tuple(gates[0]["required_prior_staging_event_ids"])
        != LINUX_CONFINEMENT_STAGE1_REQUIRED_PRIOR_EVENT_IDS
        or tuple(gates[1]["required_prior_staging_event_ids"])
        != LINUX_CONFINEMENT_STAGE2_REQUIRED_PRIOR_EVENT_IDS
        or tuple(completion["canonical_preimage_field_ids"])
        != LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_FIELD_IDS
        or completion["artifact_type"]
        != LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE
        or gates[0]["preimage_artifact_type"]
        != LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
        or gates[1]["preimage_artifact_type"]
        != LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
    ):
        raise RuntimeError(_ERROR_MESSAGES[
            LinuxConfinementPreimageCodecCode.CONTRACT_DRIFT
        ])


_validate_plan_coherence()

LINUX_CONFINEMENT_RETAINED_RECORD_FIELD_IDS: Final = (
    _RETAINED_RECORD_FIELD_IDS
)
LINUX_CONFINEMENT_STAGING_EVENT_RECORD_FIELD_IDS: Final = (
    _STAGING_EVENT_RECORD_FIELD_IDS
)
LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_FIELD_IDS: Final = (
    _RELEASE_TRANSCRIPT_FIELD_IDS
)
LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_FIELD_IDS: Final = (
    _POSTRUN_STAGING_TRANSCRIPT_FIELD_IDS
)


__all__ = [
    "LINUX_CONFINEMENT_CAPTURE_BINDING_FIELD_IDS",
    "LINUX_CONFINEMENT_ENVELOPE_OBSERVATION_IDS",
    "LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_FULL_RELEASE_TRANSCRIPT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_FIELD_IDS",
    "LINUX_CONFINEMENT_OPAQUE_RECORD_SEMANTIC_STATUS",
    "LINUX_CONFINEMENT_POSTRUN_BINDING_FIELD_IDS",
    "LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_FIELD_IDS",
    "LINUX_CONFINEMENT_POSTRUN_CLEANUP_EVENT_IDS",
    "LINUX_CONFINEMENT_POSTRUN_REQUIRED_OBSERVATION_IDS",
    "LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_FIELD_IDS",
    "LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_PREIMAGE_CODEC_IMPLEMENTATION_STATUS",
    "LINUX_CONFINEMENT_PREIMAGE_CODEC_VALIDATION_STATUS",
    "LINUX_CONFINEMENT_PREIMAGE_CODEC_VERIFIER_ID",
    "LINUX_CONFINEMENT_PREIMAGE_DIGEST_COMPUTATION_ID",
    "LINUX_CONFINEMENT_PREIMAGE_ENCODING_ID",
    "LINUX_CONFINEMENT_RECORD_KIND_HOSTILE_CONTROL",
    "LINUX_CONFINEMENT_RECORD_KIND_IDS",
    "LINUX_CONFINEMENT_RECORD_KIND_OBSERVATION",
    "LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_READY_FIRST",
    "LINUX_CONFINEMENT_RELEASE_PREFIX_EVENT_ORDER_STOP_FIRST",
    "LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_FIELD_IDS",
    "LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_RETAINED_RECORD_FIELD_IDS",
    "LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_FIELD_IDS",
    "LINUX_CONFINEMENT_STAGE1_REQUIRED_OBSERVATION_IDS",
    "LINUX_CONFINEMENT_STAGE1_REQUIRED_PRIOR_EVENT_IDS",
    "LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_FIELD_IDS",
    "LINUX_CONFINEMENT_STAGE2_REQUIRED_OBSERVATION_IDS",
    "LINUX_CONFINEMENT_STAGE2_REQUIRED_PRIOR_EVENT_IDS",
    "LINUX_CONFINEMENT_STAGING_EVENT_RECORD_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_STAGING_EVENT_RECORD_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_STAGING_EVENT_RECORD_FIELD_IDS",
    "CanonicalLinuxConfinementArtifactV1",
    "LinuxConfinementCaptureBindingV1",
    "LinuxConfinementPreimageCodecCode",
    "LinuxConfinementPreimageCodecError",
    "LinuxConfinementRetainedRecordV1",
    "LinuxConfinementStagingEventRecordV1",
    "MAXIMUM_LINUX_CONFINEMENT_INNER_COMPLETION_RECORD_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_FRAME_FIELDS",
    "MAXIMUM_LINUX_CONFINEMENT_POSTRUN_FINALIZATION_ENVELOPE_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_POSTRUN_STAGING_TRANSCRIPT_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_PREIMAGE_CODEC_CONTRACT_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_PUBLIC_TOKEN_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_RECORD_PAYLOAD_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_RECORDS_PER_SEQUENCE",
    "MAXIMUM_LINUX_CONFINEMENT_RELEASE_GATE_PREIMAGE_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_RELEASE_TRANSCRIPT_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_RETAINED_RECORD_COMMITMENT_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_RUN_SEQUENCE_NUMBER",
    "MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_SEQUENCE_NUMBER",
    "MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENT_RECORD_BYTES",
    "build_linux_confinement_full_release_transcript",
    "build_linux_confinement_inner_v1_completion_record",
    "build_linux_confinement_postrun_finalization_envelope",
    "build_linux_confinement_postrun_staging_transcript",
    "build_linux_confinement_pre_completion_release_prefix",
    "build_linux_confinement_stage1_release_gate_preimage",
    "build_linux_confinement_stage2_release_gate_preimage",
    "linux_confinement_preimage_codec_contract_bytes",
    "linux_confinement_preimage_codec_contract_sha256",
    "linux_confinement_preimage_codec_contract_tree",
    "linux_confinement_retained_record_commitment_bytes",
    "linux_confinement_retained_record_commitment_sha256",
    "linux_confinement_staging_event_record_bytes",
    "linux_confinement_staging_event_record_sha256",
    "parse_linux_confinement_preimage_codec_contract",
]
