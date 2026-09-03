"""Canonical schemas for the 24 prospective Linux observations.

Checkpoint 51 intentionally retained every observation payload as opaque
bytes.  This module narrows that surface with exact canonical schemas:

* a capture-time seven-role/five-task topology table;
* stage-1, stage-2, and postrun process-identity snapshots;
* kind-specific bindings for all 28 subject roles in the evidence plan; and
* one closed metadata, subject, field, and value-codec profile for each of the
  24 observation IDs.

The distinction between topology and snapshots is essential.  The application
and sandbox PID 1 do not exist at capture time, so a capture-time table cannot
honestly contain their observed kernel identities.  The table instead binds
logical role slots; later snapshots bind supplied task identity records and
form a predecessor chain.

All validation here is portable.  It performs no syscall, opens no pidfd,
reads no kernel filesystem, authenticates no producer or custody channel, and
does not evaluate a Linux policy predicate.  Acceptance proves canonical
shape, declared-value typing, hashes, and internal/run bindings only.  It is
not evidence of execution, origin, custody, confinement, hostile-control
success, release safety, teardown, or a scientific result.
"""

from __future__ import annotations

from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Dict, Final, Mapping, Tuple

from .adapter_linux_confinement_acceptance import (
    linux_confinement_acceptance_contract_sha256,
)
from .adapter_linux_confinement_evidence import (
    LINUX_CONFINEMENT_PROCESS_IDENTITY_ROLE_IDS,
    linux_confinement_evidence_schema_contract_sha256,
)
from .adapter_linux_confinement_evidence_plan import (
    linux_confinement_evidence_plan_sha256,
    linux_confinement_evidence_plan_tree,
)
from .adapter_linux_confinement_staging_protocol import (
    linux_confinement_staging_protocol_contract_sha256,
    linux_confinement_staging_run_binding_sha256,
)


LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-subject-role-topology-table.v1"
)
LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-process-identity-snapshot.v1"
)
LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_KERNEL_TASK_INSTANCE_DIGEST_DOMAIN: Final = (
    "heterodiff.adapter.linux-confinement-kernel-task-instance.v1"
)
LINUX_CONFINEMENT_OBSERVATION_PAYLOAD_ARTIFACT_TYPE_PREFIX: Final = (
    "heterodiff.adapter.linux-confinement-observation-payload."
)
LINUX_CONFINEMENT_SUBJECT_BINDING_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-subject-binding.v1"
)
LINUX_CONFINEMENT_EVIDENCE_MEMBER_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-evidence-member.v1"
)
LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-semantic-payload-contract.v1"
)
LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_IMPLEMENTATION_STATUS: Final = (
    "PORTABLE_CANONICAL_SCHEMA_AND_CONTEXT_BINDING_IMPLEMENTED"
)
LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_VALIDATION_SCOPE: Final = (
    "SUPPLIED_SCHEMA_CODEC_HASH_CONTEXT_RESOURCE_TASK_RUN_AND_INTERNAL_"
    "IDENTITY_BINDINGS_ONLY"
)
LINUX_CONFINEMENT_PREDICATE_EVALUATION_STATUS: Final = (
    "NOT_EVALUATED_BY_PORTABLE_SCHEMA_VALIDATOR"
)
LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_ENCODING_ID: Final = (
    "canonical-ascii-json-sorted-keys-no-whitespace-v1"
)
LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-bytes-v1"
)
LINUX_CONFINEMENT_IMPLEMENTATION_SEPARATED_VERIFIER_ID: Final = (
    "heterodiff.adapter.linux-confinement-semantic-payload-"
    "implementation-separated-verifier.v1"
)

LINUX_CONFINEMENT_CODEC_SHA256_HEX_ASCII: Final = (
    "sha256-lowercase-hex-ascii-v1"
)
LINUX_CONFINEMENT_CODEC_U64BE: Final = "unsigned-u64be-v1"
LINUX_CONFINEMENT_CODEC_NUL_FRAME: Final = (
    "nul-terminated-ordered-octet-strings-v1"
)
LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT: Final = (
    "canonical-ascii-json-object-v1"
)
LINUX_CONFINEMENT_CODEC_BOUNDED_OCTETS: Final = "bounded-opaque-octets-v1"
LINUX_CONFINEMENT_EVIDENCE_VALUE_CODEC_IDS: Final = (
    LINUX_CONFINEMENT_CODEC_SHA256_HEX_ASCII,
    LINUX_CONFINEMENT_CODEC_U64BE,
    LINUX_CONFINEMENT_CODEC_NUL_FRAME,
    LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT,
    LINUX_CONFINEMENT_CODEC_BOUNDED_OCTETS,
)

LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE1: Final = "PRE_STAGE1"
LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE2: Final = "PRE_STAGE2"
LINUX_CONFINEMENT_SNAPSHOT_STAGE_POSTRUN: Final = "POSTRUN"
LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_STAGE_IDS: Final = (
    LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE1,
    LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE2,
    LINUX_CONFINEMENT_SNAPSHOT_STAGE_POSTRUN,
)

MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_TOKEN_BYTES: Final = 512
MAXIMUM_LINUX_CONFINEMENT_JSON_STRING_BYTES: Final = 512 * 1024
MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES: Final = 256 * 1024
MAXIMUM_LINUX_CONFINEMENT_RECORD_RAW_SOURCE_BYTES: Final = (
    32 * 1024
)
MAXIMUM_LINUX_CONFINEMENT_RECORD_PROJECTION_BYTES: Final = (
    MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES // 2
)
MAXIMUM_LINUX_CONFINEMENT_OBSERVATION_PAYLOAD_BYTES: Final = 2 * 1024 * 1024
MAXIMUM_LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_BYTES: Final = 128 * 1024
MAXIMUM_LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_BYTES: Final = (
    256 * 1024
)
MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_BYTES: Final = (
    512 * 1024
)
MAXIMUM_LINUX_CONFINEMENT_JSON_DEPTH: Final = 16
MAXIMUM_LINUX_CONFINEMENT_JSON_ITEMS: Final = 8192
MAXIMUM_LINUX_CONFINEMENT_RUN_SEQUENCE_NUMBER: Final = 4095

_ZERO_SHA256: Final = "0" * 64
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$")

_SHA256_FIELD_IDS: Final = (
    "adapter-filter-sha256",
    "backend-memfd-sha256",
    "boot-configuration-digest",
    "bootstrap-execution-closure-manifest-sha256",
    "bootstrap-filter-install-transcript-leaf",
    "bootstrap-source-sha256",
    "dependency-lock-domain-sha256",
    "dependency-lock-plain-sha256",
    "interpreter-file-sha256",
    "landlock-bootstrap-transcript-leaf",
    "landlock-ruleset-sha256",
    "launch-filter-sha256",
    "platform-profile-sha256",
    "rootfs-image-sha256",
    "rootfs-manifest-sha256",
    "supervisor-dependency-closure-sha256",
    "supervisor-executable-sha256",
    "supervisor-feature-manifest-sha256",
    "supervisor-source-sha256",
)
_U64_FIELD_IDS: Final = (
    "bootstrap-source-byte-count",
    "dependency-lock-byte-count",
)
_NUL_FRAME_FIELD_IDS: Final = (
    "argv-nul-frame-bytes",
    "environment-nul-frame-bytes",
)
_BOUNDED_OCTET_FIELD_IDS: Final = (
    "cgroup-controller-file-bytes",
    "cgroup-events-before-release-bytes",
    "cgroup-events-final-bytes",
    "supervisor-dependency-inventory-bytes",
)

LINUX_CONFINEMENT_TASK_SLOT_IDS: Final = (
    "application-task",
    "helper-task",
    "monitor-task",
    "pid1-task",
    "supervisor-task",
)
LINUX_CONFINEMENT_PROCESS_IDENTITY_ALIAS_EDGES: Final = (
    (
        "unprivileged-preexec-launcher",
        "bubblewrap-monitor",
        "same-kernel-task-across-exec-v1",
    ),
    (
        "bubblewrap-setup-child",
        "sandbox-pid1-reaper",
        "same-host-task-lifecycle-transition-v1",
    ),
)
LINUX_CONFINEMENT_EXPECTED_PROCESS_INSTANCE_COUNT: Final = 5

_ROLE_ROWS: Final = (
    (
        "application",
        "application-task",
        0,
        "",
        "",
        "sandbox-pid1-reaper",
        "sandbox-pid1-reaper",
        "sandbox-pid1-reaper",
        "sandbox-pid1-clone-supervisor-pidfd-bind-v1",
        "pre-stage2-application-stopped",
        "postrun-cleanup-complete",
    ),
    (
        "bubblewrap-monitor",
        "monitor-task",
        1,
        "unprivileged-preexec-launcher",
        "",
        "privileged-supervisor",
        "privileged-supervisor",
        "privileged-supervisor",
        "predecessor-role-pidfd-continuity-v1",
        "pre-stage1-setup-blocked",
        "postrun-cleanup-complete",
    ),
    (
        "bubblewrap-setup-child",
        "pid1-task",
        0,
        "",
        "sandbox-pid1-reaper",
        "bubblewrap-monitor",
        "bubblewrap-monitor",
        "privileged-supervisor",
        "pidfd-open-proc-handle-bound-v1",
        "pre-stage1-setup-blocked",
        "stage1-release-transition",
    ),
    (
        "privileged-supervisor",
        "supervisor-task",
        0,
        "",
        "",
        "",
        "",
        "",
        "external-custody-reference-v1",
        "pre-first-child-artifact-validation",
        "postrun-receipt-finalized",
    ),
    (
        "sandbox-pid1-reaper",
        "pid1-task",
        1,
        "bubblewrap-setup-child",
        "",
        "bubblewrap-monitor",
        "bubblewrap-monitor",
        "privileged-supervisor",
        "predecessor-role-pidfd-continuity-v1",
        "post-stage1-release",
        "postrun-cleanup-complete",
    ),
    (
        "unprivileged-preexec-launcher",
        "monitor-task",
        0,
        "",
        "bubblewrap-monitor",
        "privileged-supervisor",
        "privileged-supervisor",
        "privileged-supervisor",
        "clone3-clone-pidfd-v1",
        "pre-first-child-artifact-validation",
        "launcher-monitor-exec-transition",
    ),
    (
        "userns-map-observation-helper",
        "helper-task",
        0,
        "",
        "",
        "privileged-supervisor",
        "privileged-supervisor",
        "privileged-supervisor",
        "clone3-clone-pidfd-v1",
        "pre-stage1-setup-blocked",
        "pre-stage1-helper-reaped",
    ),
)
_ROLE_ROW_FIELD_IDS: Final = (
    "role_id",
    "task_slot_id",
    "phase_index",
    "predecessor_role_id",
    "successor_role_id",
    "creator_role_id",
    "parent_role_id_at_phase_start",
    "expected_reaper_role_id",
    "pidfd_acquisition_mode_id",
    "first_valid_lifecycle_stage_id",
    "terminal_lifecycle_stage_id",
)
_ROLE_TO_TASK_SLOT: Final = MappingProxyType(
    {row[0]: row[1] for row in _ROLE_ROWS}
)

_TASK_PARENT_SLOTS: Final = MappingProxyType(
    {
        "application-task": "pid1-task",
        "helper-task": "supervisor-task",
        "monitor-task": "supervisor-task",
        "pid1-task": "monitor-task",
        "supervisor-task": "",
    }
)
_TASK_REAPER_ROLES: Final = MappingProxyType(
    {
        "application-task": "sandbox-pid1-reaper",
        "helper-task": "privileged-supervisor",
        "monitor-task": "privileged-supervisor",
        "pid1-task": "privileged-supervisor",
        "supervisor-task": "",
    }
)
_TASK_PIDFD_METHODS: Final = MappingProxyType(
    {
        "application-task": (
            "sandbox-pid1-clone-supervisor-pidfd-bind-v1"
        ),
        "helper-task": "clone3-clone-pidfd-v1",
        "monitor-task": "clone3-clone-pidfd-v1",
        "pid1-task": "pidfd-open-proc-handle-bound-v1",
        "supervisor-task": "external-custody-reference-v1",
    }
)
_SNAPSHOT_EXPECTED_STATE: Final = MappingProxyType(
    {
        LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE1: {
            "application-task": ("NOT_CREATED", ""),
            "helper-task": (
                "WAIT_REAPED",
                "userns-map-observation-helper",
            ),
            "monitor-task": ("LIVE", "bubblewrap-monitor"),
            "pid1-task": ("BLOCKED", "bubblewrap-setup-child"),
            "supervisor-task": ("LIVE", "privileged-supervisor"),
        },
        LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE2: {
            "application-task": ("PIDFD_BOUND_STOPPED", "application"),
            "helper-task": (
                "WAIT_REAPED",
                "userns-map-observation-helper",
            ),
            "monitor-task": ("LIVE", "bubblewrap-monitor"),
            "pid1-task": ("LIVE", "sandbox-pid1-reaper"),
            "supervisor-task": ("LIVE", "privileged-supervisor"),
        },
        LINUX_CONFINEMENT_SNAPSHOT_STAGE_POSTRUN: {
            "application-task": ("WAIT_REAPED", "application"),
            "helper-task": (
                "WAIT_REAPED",
                "userns-map-observation-helper",
            ),
            "monitor-task": ("WAIT_REAPED", "bubblewrap-monitor"),
            "pid1-task": ("WAIT_REAPED", "sandbox-pid1-reaper"),
            "supervisor-task": ("LIVE", "privileged-supervisor"),
        },
    }
)
_SNAPSHOT_TRUSTED_PRODUCER_IDS: Final = MappingProxyType(
    {
        LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE1: (
            "privileged-supervisor-process-identity-observer-v1"
        ),
        LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE2: (
            "privileged-supervisor-process-identity-observer-v1"
        ),
        LINUX_CONFINEMENT_SNAPSHOT_STAGE_POSTRUN: (
            "dedicated-subreaper-supervisor-process-observer-v1"
        ),
    }
)

_SUBJECT_KIND_BY_ROLE: Final = MappingProxyType(
    {
        "adapter-seccomp-filter": "security-policy-object",
        "adapter-stage-landlock-ruleset": "security-policy-object",
        "adopted-run-descendants": "process-set",
        "application": "process-role",
        "application-mount-namespace": "namespace",
        "application-network-namespace": "namespace",
        "backend-executable-memfd": "kernel-object",
        "bootstrap-execution-closure": "content-artifact",
        "bubblewrap-monitor": "process-role",
        "bubblewrap-setup-child": "process-role",
        "bubblewrap-setup-child-mount-namespace": "namespace",
        "final-user-namespace": "namespace",
        "intermediate-user-namespace": "namespace",
        "launch-seccomp-filter": "security-policy-object",
        "linux-host-platform": "platform",
        "privileged-supervisor": "process-role",
        "runtime-rootfs": "content-artifact",
        "sandbox-cgroup-v2-leaf": "kernel-object",
        "sandbox-dependency-lock": "content-artifact",
        "sandbox-interpreter": "content-artifact",
        "sandbox-pid1-reaper": "process-role",
        "stage1-barrier": "kernel-object",
        "stage2-pidfd-release": "kernel-object",
        "staging-bootstrap": "content-artifact",
        "supervisor-dependency-closure": "content-artifact",
        "supervisor-stdio-peers": "kernel-object",
        "unprivileged-preexec-launcher": "process-role",
        "userns-map-observation-helper": "process-role",
    }
)
_NAMESPACE_TYPE_BY_ROLE: Final = MappingProxyType(
    {
        "application-mount-namespace": "mount",
        "application-network-namespace": "network",
        "bubblewrap-setup-child-mount-namespace": "mount",
        "final-user-namespace": "user",
        "intermediate-user-namespace": "user",
    }
)
_KERNEL_OBJECT_TYPE_BY_ROLE: Final = MappingProxyType(
    {
        "backend-executable-memfd": "memfd-executable",
        "sandbox-cgroup-v2-leaf": "cgroup-v2-leaf",
        "stage1-barrier": "pipe-barrier",
        "stage2-pidfd-release": "pidfd-release-channel",
        "supervisor-stdio-peers": "stdio-peer-set",
    }
)
_SECURITY_OBJECT_TYPE_BY_ROLE: Final = MappingProxyType(
    {
        "adapter-seccomp-filter": "seccomp-filter",
        "adapter-stage-landlock-ruleset": "landlock-ruleset",
        "launch-seccomp-filter": "seccomp-filter",
    }
)
_RESOURCE_COMPONENT_FIELDS_BY_KIND: Final = MappingProxyType(
    {
        "content-artifact": (
            "byte_count",
            "content_sha256",
            "custody_record_sha256",
            "manifest_membership_sha256",
        ),
        "kernel-object": (
            "device",
            "generation",
            "inode",
            "kernel_object_type_id",
            "observation_record_sha256",
        ),
        "namespace": (
            "device",
            "inode",
            "namespace_type_id",
            "observation_record_sha256",
            "owner_user_namespace_inode",
        ),
        "platform": (
            "architecture_id",
            "linux_boot_id_sha256",
            "observation_record_sha256",
            "platform_profile_sha256",
        ),
        "process-set": (
            "completeness_authority_record_sha256",
            "member_count",
            "membership_sha256",
            "observation_record_sha256",
        ),
        "security-policy-object": (
            "content_sha256",
            "feature_manifest_sha256",
            "install_or_custody_record_sha256",
            "security_object_type_id",
        ),
    }
)

_FAMILY_F1: Final = (
    "backend-static-sealed-executable-identity-matched",
    "dependency-lock-identity-matched",
    "immutable-runtime-rootfs-identity-matched",
    "linux-platform-profile-matched",
    "sandbox-bootstrap-identity-matched",
    "sandbox-interpreter-identity-matched",
    "supervisor-dependency-closure-identity-matched",
    "supervisor-executable-identity-matched",
)
_FAMILY_F2: Final = (
    "application-argv-environment-cwd-umask-matched",
    "capability-securebits-dumpability-profile-matched",
    "landlock-abi-and-ruleset-matched",
    "no-new-privileges-observed-before-release",
    "rlimit-profile-matched-before-release",
    "seccomp-filter-and-architecture-observed-before-release",
)
_FAMILY_F3: Final = (
    "cgroup-v2-controller-values-matched-before-release",
    "cgroup-v2-leaf-owned-by-supervisor",
    "descriptor-inventory-and-stdio-types-closed-before-adapter-import",
    (
        "exact-two-level-uid-gid-maps-composition-empty-"
        "supplementary-groups-and-setgroups-denial-matched"
    ),
    "mount-inventory-and-write-surface-matched",
    "namespace-identities-distinct-before-release",
    "network-interface-and-route-inventory-matched",
)
_FAMILY_F4: Final = (
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
LINUX_CONFINEMENT_OBSERVATION_FAMILY_IDS: Final = (
    "F1_ARTIFACT_PLATFORM_IDENTITY",
    "F2_PIDFD_BOUND_STOPPED_STATE",
    "F3_CLOSED_RESOURCE_TOPOLOGY",
    "F4_BOUND_MONOTONIC_EVENT_GRAPH",
)


class LinuxConfinementSemanticPayloadCode(str, Enum):
    """Stable public error codes without reflecting untrusted values."""

    INPUT_TYPE = "INPUT_TYPE"
    INPUT_RESOURCE = "INPUT_RESOURCE"
    VALUE_INVALID = "VALUE_INVALID"
    ORDER_INVALID = "ORDER_INVALID"
    BINDING_MISMATCH = "BINDING_MISMATCH"
    CANONICAL_INVALID = "CANONICAL_INVALID"
    CONTRACT_DRIFT = "CONTRACT_DRIFT"
    INTERNAL = "INTERNAL"


_ERROR_MESSAGES: Final = MappingProxyType(
    {
        LinuxConfinementSemanticPayloadCode.INPUT_TYPE: (
            "semantic payload input type invalid"
        ),
        LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE: (
            "semantic payload resource limit exceeded"
        ),
        LinuxConfinementSemanticPayloadCode.VALUE_INVALID: (
            "semantic payload value invalid"
        ),
        LinuxConfinementSemanticPayloadCode.ORDER_INVALID: (
            "semantic payload order invalid"
        ),
        LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH: (
            "semantic payload binding mismatch"
        ),
        LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID: (
            "semantic payload canonical encoding invalid"
        ),
        LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT: (
            "semantic payload contract drift"
        ),
        LinuxConfinementSemanticPayloadCode.INTERNAL: (
            "semantic payload internal invariant failed"
        ),
    }
)


class LinuxConfinementSemanticPayloadError(ValueError):
    """One fixed-message semantic payload failure."""

    def __init__(self, code: LinuxConfinementSemanticPayloadCode) -> None:
        if type(code) is not LinuxConfinementSemanticPayloadCode:
            raise TypeError("semantic payload code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: LinuxConfinementSemanticPayloadCode) -> None:
    raise LinuxConfinementSemanticPayloadError(code) from None


def _validated_exact_dataclass_post_init(
    value: object,
    expected_type: type,
) -> None:
    if type(value) is not expected_type:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    try:
        expected_type.__post_init__(value)
    except LinuxConfinementSemanticPayloadError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)


def _validate_exact_mapping_keys(
    value: object,
    expected_keys: Tuple[str, ...],
) -> None:
    if not isinstance(value, MappingABC):
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    try:
        actual_keys = tuple(value.keys())
    except (AttributeError, RuntimeError, TypeError, ValueError):
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    if (
        len(actual_keys) != len(expected_keys)
        or any(type(key) is not str for key in actual_keys)
        or set(actual_keys) != set(expected_keys)
    ):
        _fail(LinuxConfinementSemanticPayloadCode.ORDER_INVALID)


def _mapping_value(value: Mapping[str, object], key: str) -> object:
    try:
        return value[key]
    except (KeyError, RuntimeError, TypeError, ValueError):
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)


def _ascii(value: str) -> bytes:
    if type(value) is not str:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    try:
        return value.encode("ascii", "strict")
    except UnicodeError:
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)


def _token(value: str, *, empty: bool = False) -> str:
    if type(value) is not str:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    if empty and value == "":
        return value
    raw = _ascii(value)
    if (
        not raw
        or len(raw) > MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_TOKEN_BYTES
        or _TOKEN_RE.fullmatch(value) is None
    ):
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    return value


def _sha256_token(value: str, *, allow_zero: bool = False) -> str:
    if (
        type(value) is not str
        or _SHA256_RE.fullmatch(value) is None
        or (not allow_zero and value == _ZERO_SHA256)
    ):
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    return value


def _u64(value: int, *, positive: bool = False) -> int:
    if (
        type(value) is not int
        or value < (1 if positive else 0)
        or value >= 1 << 64
    ):
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    return value


def _plain_sha256(value: bytes) -> str:
    if type(value) is not bytes:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    return hashlib.sha256(value).hexdigest()


def _domain_sha256(domain: str, value: bytes) -> str:
    _token(domain)
    if type(value) is not bytes:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    digest = hashlib.sha256()
    digest.update(_ascii(domain))
    digest.update(b"\x00")
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)
    return digest.hexdigest()


def _json_node_count(value: object, *, depth: int = 0) -> int:
    if depth > MAXIMUM_LINUX_CONFINEMENT_JSON_DEPTH:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
    if value is None or type(value) in (bool, int, str):
        if type(value) is int:
            _u64(value)
        if (
            type(value) is str
            and len(_ascii(value))
            > MAXIMUM_LINUX_CONFINEMENT_JSON_STRING_BYTES
        ):
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
        return 1
    if type(value) is list:
        return 1 + sum(
            _json_node_count(item, depth=depth + 1) for item in value
        )
    if type(value) is dict:
        count = 1
        for key, item in value.items():
            if type(key) is not str or len(_ascii(key)) > 512:
                _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
            count += _json_node_count(item, depth=depth + 1)
        return count
    _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)


def _canonical_json(value: object, *, maximum: int) -> bytes:
    if _json_node_count(value) > MAXIMUM_LINUX_CONFINEMENT_JSON_ITEMS:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
    try:
        result = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii", "strict")
    except (TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    if not result or len(result) > maximum:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
    return result


def _reject_float(_: str) -> object:
    _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)


def _reject_constant(_: str) -> object:
    _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
        result[key] = value
    return result


def _parse_canonical_json(value: bytes, *, maximum: int) -> dict:
    if type(value) is not bytes:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    if not value or len(value) > maximum:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
    try:
        text = value.decode("ascii", "strict")
        parsed = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except (
        UnicodeError,
        json.JSONDecodeError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
    if type(parsed) is not dict:
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
    if _canonical_json(parsed, maximum=maximum) != value:
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
    return parsed


def _exact_keys(value: dict, expected: Tuple[str, ...]) -> None:
    if type(value) is not dict or tuple(sorted(value)) != tuple(
        sorted(expected)
    ):
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)


def _false_nonclaims() -> dict:
    return {
        "evidence_custody_authenticated": False,
        "hostile_controls_executed": False,
        "kernel_semantics_validated": False,
        "linux_confinement_established": False,
        "linux_execution_observed": False,
        "policy_predicate_evaluated": False,
        "producer_origin_authenticated": False,
        "release_safety_established": False,
    }


def _role_row_tree(row: tuple) -> dict:
    return dict(zip(_ROLE_ROW_FIELD_IDS, row))


def _role_topology_rows_tree() -> list:
    return [_role_row_tree(row) for row in _ROLE_ROWS]


def _validated_role_table_catalog() -> None:
    roles = tuple(row[0] for row in _ROLE_ROWS)
    task_slots = tuple(row[1] for row in _ROLE_ROWS)
    if (
        roles != LINUX_CONFINEMENT_PROCESS_IDENTITY_ROLE_IDS
        or set(task_slots) != set(LINUX_CONFINEMENT_TASK_SLOT_IDS)
        or len(set(task_slots))
        != LINUX_CONFINEMENT_EXPECTED_PROCESS_INSTANCE_COUNT
        or tuple(
            (row[0], row[3], row[4])
            for row in _ROLE_ROWS
            if row[3] or row[4]
        )
        != (
            (
                "bubblewrap-monitor",
                "unprivileged-preexec-launcher",
                "",
            ),
            (
                "bubblewrap-setup-child",
                "",
                "sandbox-pid1-reaper",
            ),
            (
                "sandbox-pid1-reaper",
                "bubblewrap-setup-child",
                "",
            ),
            (
                "unprivileged-preexec-launcher",
                "",
                "bubblewrap-monitor",
            ),
        )
    ):
        raise RuntimeError(
            _ERROR_MESSAGES[
                LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT
            ]
        )


@dataclass(frozen=True)
class LinuxConfinementSubjectIdentityTableV1:
    """Capture-time logical role topology, not observed process identities."""

    policy_sha256: str
    supervisor_epoch_id_hex: str
    run_sequence_number: int
    run_nonce_hex: str

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementSubjectIdentityTableV1:
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
        _sha256_token(self.policy_sha256)
        _sha256_token(self.supervisor_epoch_id_hex)
        _sha256_token(self.run_nonce_hex)
        if self.supervisor_epoch_id_hex == self.run_nonce_hex:
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        _u64(self.run_sequence_number)
        if (
            self.run_sequence_number
            > MAXIMUM_LINUX_CONFINEMENT_RUN_SEQUENCE_NUMBER
        ):
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)

    @property
    def staging_run_binding_sha256(self) -> str:
        try:
            return linux_confinement_staging_run_binding_sha256(
                policy_sha256=self.policy_sha256,
                supervisor_epoch_id_hex=self.supervisor_epoch_id_hex,
                run_sequence_number=self.run_sequence_number,
                run_nonce_hex=self.run_nonce_hex,
            )
        except (TypeError, ValueError):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


def _validated_subject_table(
    value: LinuxConfinementSubjectIdentityTableV1,
) -> None:
    _validated_exact_dataclass_post_init(
        value,
        LinuxConfinementSubjectIdentityTableV1,
    )


def _subject_table_tree(
    value: LinuxConfinementSubjectIdentityTableV1,
) -> dict:
    _validated_subject_table(value)
    return {
        "acceptance_contract_sha256": (
            linux_confinement_acceptance_contract_sha256()
        ),
        "artifact_type": (
            LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_ARTIFACT_TYPE
        ),
        "evidence_plan_sha256": linux_confinement_evidence_plan_sha256(),
        "evidence_schema_contract_sha256": (
            linux_confinement_evidence_schema_contract_sha256()
        ),
        "format_version": "1",
        "nonclaims": _false_nonclaims(),
        "policy_sha256": value.policy_sha256,
        "role_rows": _role_topology_rows_tree(),
        "run_nonce_hex": value.run_nonce_hex,
        "run_sequence_number": value.run_sequence_number,
        "semantic_payload_contract_sha256": (
            linux_confinement_semantic_payload_contract_sha256()
        ),
        "staging_protocol_contract_sha256": (
            linux_confinement_staging_protocol_contract_sha256()
        ),
        "staging_run_binding_sha256": (
            value.staging_run_binding_sha256
        ),
        "supervisor_epoch_id_hex": value.supervisor_epoch_id_hex,
        "table_semantics_id": (
            "capture-time-logical-role-slot-topology-not-kernel-"
            "identity-v1"
        ),
    }


def linux_confinement_subject_identity_table_bytes(
    value: LinuxConfinementSubjectIdentityTableV1,
) -> bytes:
    return _canonical_json(
        _subject_table_tree(value),
        maximum=MAXIMUM_LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_BYTES,
    )


def linux_confinement_subject_identity_table_sha256(
    value: LinuxConfinementSubjectIdentityTableV1,
) -> str:
    return _domain_sha256(
        LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_DIGEST_DOMAIN,
        linux_confinement_subject_identity_table_bytes(value),
    )


def parse_linux_confinement_subject_identity_table(
    value: bytes,
) -> LinuxConfinementSubjectIdentityTableV1:
    tree = _parse_canonical_json(
        value,
        maximum=MAXIMUM_LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_BYTES,
    )
    _exact_keys(
        tree,
        (
            "acceptance_contract_sha256",
            "artifact_type",
            "evidence_plan_sha256",
            "evidence_schema_contract_sha256",
            "format_version",
            "nonclaims",
            "policy_sha256",
            "role_rows",
            "run_nonce_hex",
            "run_sequence_number",
            "semantic_payload_contract_sha256",
            "staging_protocol_contract_sha256",
            "staging_run_binding_sha256",
            "supervisor_epoch_id_hex",
            "table_semantics_id",
        ),
    )
    if (
        tree["artifact_type"]
        != LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or tree["table_semantics_id"]
        != "capture-time-logical-role-slot-topology-not-kernel-identity-v1"
        or tree["semantic_payload_contract_sha256"]
        != linux_confinement_semantic_payload_contract_sha256()
        or tree["role_rows"] != _role_topology_rows_tree()
        or tree["nonclaims"] != _false_nonclaims()
    ):
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    result = LinuxConfinementSubjectIdentityTableV1(
        policy_sha256=tree["policy_sha256"],
        supervisor_epoch_id_hex=tree["supervisor_epoch_id_hex"],
        run_sequence_number=tree["run_sequence_number"],
        run_nonce_hex=tree["run_nonce_hex"],
    )
    if (
        tree["staging_run_binding_sha256"]
        != result.staging_run_binding_sha256
        or tree["acceptance_contract_sha256"]
        != linux_confinement_acceptance_contract_sha256()
        or tree["evidence_plan_sha256"]
        != linux_confinement_evidence_plan_sha256()
        or tree["evidence_schema_contract_sha256"]
        != linux_confinement_evidence_schema_contract_sha256()
        or tree["staging_protocol_contract_sha256"]
        != linux_confinement_staging_protocol_contract_sha256()
        or linux_confinement_subject_identity_table_bytes(result) != value
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    return result


@dataclass(frozen=True)
class LinuxConfinementTaskIdentityV1:
    """One supplied task row retained across the three snapshot stages."""

    task_slot_id: str
    lifecycle_state_id: str
    active_role_id: str
    host_tgid: int
    proc_starttime_clock_ticks: int
    host_pid_namespace_device: int
    host_pid_namespace_inode: int
    nspid_vector: Tuple[int, ...]
    pidfd_acquisition_method_id: str
    pidfd_acquisition_record_sha256: str
    parent_task_slot_id: str
    lifecycle_transition_record_sha256: str
    exit_observation_record_sha256: str
    wait_reap_record_sha256: str
    reaper_role_id: str

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementTaskIdentityV1:
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
        if self.task_slot_id not in LINUX_CONFINEMENT_TASK_SLOT_IDS:
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        _token(self.lifecycle_state_id)
        _token(self.active_role_id, empty=True)
        if (
            self.active_role_id
            and self.active_role_id
            not in LINUX_CONFINEMENT_PROCESS_IDENTITY_ROLE_IDS
        ):
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        for item in (
            self.host_tgid,
            self.proc_starttime_clock_ticks,
            self.host_pid_namespace_device,
            self.host_pid_namespace_inode,
        ):
            _u64(item)
        if (
            type(self.nspid_vector) is not tuple
            or len(self.nspid_vector) > 16
        ):
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
        for item in self.nspid_vector:
            _u64(item, positive=True)
        _token(self.pidfd_acquisition_method_id)
        for value in (
            self.pidfd_acquisition_record_sha256,
            self.lifecycle_transition_record_sha256,
            self.exit_observation_record_sha256,
            self.wait_reap_record_sha256,
        ):
            _sha256_token(value, allow_zero=True)
        _token(self.parent_task_slot_id, empty=True)
        _token(self.reaper_role_id, empty=True)
        if (
            self.parent_task_slot_id != _TASK_PARENT_SLOTS[self.task_slot_id]
            or self.reaper_role_id != _TASK_REAPER_ROLES[self.task_slot_id]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


def _validated_task_identity(
    value: LinuxConfinementTaskIdentityV1,
    *,
    snapshot_stage_id: str,
) -> None:
    _validated_exact_dataclass_post_init(
        value,
        LinuxConfinementTaskIdentityV1,
    )
    expected_state, expected_role = _SNAPSHOT_EXPECTED_STATE[
        snapshot_stage_id
    ][value.task_slot_id]
    if (
        value.lifecycle_state_id != expected_state
        or value.active_role_id != expected_role
        or value.pidfd_acquisition_method_id
        != _TASK_PIDFD_METHODS[value.task_slot_id]
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    numeric = (
        value.host_tgid,
        value.proc_starttime_clock_ticks,
        value.host_pid_namespace_device,
        value.host_pid_namespace_inode,
    )
    if value.lifecycle_state_id == "NOT_CREATED":
        if (
            any(numeric)
            or value.nspid_vector
            or value.pidfd_acquisition_record_sha256 != _ZERO_SHA256
            or value.lifecycle_transition_record_sha256 != _ZERO_SHA256
            or value.exit_observation_record_sha256 != _ZERO_SHA256
            or value.wait_reap_record_sha256 != _ZERO_SHA256
        ):
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        return
    if (
        not all(item > 0 for item in numeric)
        or not value.nspid_vector
        or value.pidfd_acquisition_record_sha256 == _ZERO_SHA256
    ):
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    terminal = value.lifecycle_state_id == "WAIT_REAPED"
    if terminal != (
        value.exit_observation_record_sha256 != _ZERO_SHA256
        and value.wait_reap_record_sha256 != _ZERO_SHA256
    ):
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    if (
        not terminal
        and (
            value.exit_observation_record_sha256 != _ZERO_SHA256
            or value.wait_reap_record_sha256 != _ZERO_SHA256
        )
    ):
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    alias_transition_required = (
        snapshot_stage_id
        == LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE1
        and value.task_slot_id == "monitor-task"
    ) or (
        snapshot_stage_id
        == LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE2
        and value.task_slot_id == "pid1-task"
    )
    if (
        alias_transition_required
        and value.lifecycle_transition_record_sha256 == _ZERO_SHA256
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


def _task_identity_tree(
    value: LinuxConfinementTaskIdentityV1,
    *,
    kernel_task_instance_sha256: str,
) -> dict:
    return {
        "active_role_id": value.active_role_id,
        "exit_observation_record_sha256": (
            value.exit_observation_record_sha256
        ),
        "host_pid_namespace_device": value.host_pid_namespace_device,
        "host_pid_namespace_inode": value.host_pid_namespace_inode,
        "host_tgid": value.host_tgid,
        "kernel_task_instance_sha256": kernel_task_instance_sha256,
        "lifecycle_state_id": value.lifecycle_state_id,
        "lifecycle_transition_record_sha256": (
            value.lifecycle_transition_record_sha256
        ),
        "nspid_vector": list(value.nspid_vector),
        "parent_task_slot_id": value.parent_task_slot_id,
        "pidfd_acquisition_method_id": (
            value.pidfd_acquisition_method_id
        ),
        "pidfd_acquisition_record_sha256": (
            value.pidfd_acquisition_record_sha256
        ),
        "proc_starttime_clock_ticks": value.proc_starttime_clock_ticks,
        "reaper_role_id": value.reaper_role_id,
        "task_slot_id": value.task_slot_id,
        "wait_reap_record_sha256": value.wait_reap_record_sha256,
    }


def linux_confinement_kernel_task_instance_sha256(
    value: LinuxConfinementTaskIdentityV1,
    *,
    staging_run_binding_sha256: str,
    linux_platform_profile_sha256: str,
    linux_boot_id_sha256: str,
) -> str:
    _validated_exact_dataclass_post_init(
        value,
        LinuxConfinementTaskIdentityV1,
    )
    if value.lifecycle_state_id == "NOT_CREATED":
        return _ZERO_SHA256
    _sha256_token(staging_run_binding_sha256)
    _sha256_token(linux_platform_profile_sha256)
    _sha256_token(linux_boot_id_sha256)
    preimage = _canonical_json(
        {
            "host_pid_namespace_device": (
                value.host_pid_namespace_device
            ),
            "host_pid_namespace_inode": value.host_pid_namespace_inode,
            "host_tgid": value.host_tgid,
            "linux_boot_id_sha256": linux_boot_id_sha256,
            "linux_platform_profile_sha256": (
                linux_platform_profile_sha256
            ),
            "nspid_vector": list(value.nspid_vector),
            "proc_starttime_clock_ticks": (
                value.proc_starttime_clock_ticks
            ),
            "staging_run_binding_sha256": staging_run_binding_sha256,
        },
        maximum=16 * 1024,
    )
    return _domain_sha256(
        LINUX_CONFINEMENT_KERNEL_TASK_INSTANCE_DIGEST_DOMAIN,
        preimage,
    )


@dataclass(frozen=True)
class LinuxConfinementProcessIdentitySnapshotV1:
    """One stage-specific supplied task snapshot in a three-link chain."""

    staging_run_binding_sha256: str
    subject_identity_table_sha256: str
    linux_platform_profile_sha256: str
    linux_boot_id_sha256: str
    snapshot_stage_id: str
    predecessor_snapshot_sha256: str
    capture_monotonic_timestamp_ns: int
    trusted_producer_id: str
    task_identities: Tuple[LinuxConfinementTaskIdentityV1, ...]
    producer_authority_record_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementProcessIdentitySnapshotV1:
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
        for value in (
            self.staging_run_binding_sha256,
            self.subject_identity_table_sha256,
            self.linux_platform_profile_sha256,
            self.linux_boot_id_sha256,
            self.producer_authority_record_sha256,
        ):
            _sha256_token(value)
        _sha256_token(
            self.predecessor_snapshot_sha256,
            allow_zero=True,
        )
        if (
            self.snapshot_stage_id
            not in LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_STAGE_IDS
        ):
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        if (
            self.snapshot_stage_id
            == LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE1
        ) != (self.predecessor_snapshot_sha256 == _ZERO_SHA256):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
        _u64(self.capture_monotonic_timestamp_ns, positive=True)
        _token(self.trusted_producer_id)
        if (
            self.trusted_producer_id
            != _SNAPSHOT_TRUSTED_PRODUCER_IDS[self.snapshot_stage_id]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
        if (
            type(self.task_identities) is not tuple
            or any(
                type(row) is not LinuxConfinementTaskIdentityV1
                for row in self.task_identities
            )
            or tuple(row.task_slot_id for row in self.task_identities)
            != LINUX_CONFINEMENT_TASK_SLOT_IDS
        ):
            _fail(LinuxConfinementSemanticPayloadCode.ORDER_INVALID)
        for row in self.task_identities:
            _validated_task_identity(
                row,
                snapshot_stage_id=self.snapshot_stage_id,
            )


def _validated_snapshot(
    value: LinuxConfinementProcessIdentitySnapshotV1,
) -> None:
    _validated_exact_dataclass_post_init(
        value,
        LinuxConfinementProcessIdentitySnapshotV1,
    )


def _snapshot_tree(
    value: LinuxConfinementProcessIdentitySnapshotV1,
) -> dict:
    _validated_snapshot(value)
    rows = []
    for row in value.task_identities:
        rows.append(
            _task_identity_tree(
                row,
                kernel_task_instance_sha256=(
                    linux_confinement_kernel_task_instance_sha256(
                        row,
                        staging_run_binding_sha256=(
                            value.staging_run_binding_sha256
                        ),
                        linux_platform_profile_sha256=(
                            value.linux_platform_profile_sha256
                        ),
                        linux_boot_id_sha256=value.linux_boot_id_sha256,
                    )
                ),
            )
        )
    return {
        "artifact_type": (
            LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_ARTIFACT_TYPE
        ),
        "capture_monotonic_timestamp_ns": (
            value.capture_monotonic_timestamp_ns
        ),
        "format_version": "1",
        "linux_boot_id_sha256": value.linux_boot_id_sha256,
        "linux_platform_profile_sha256": (
            value.linux_platform_profile_sha256
        ),
        "nonclaims": _false_nonclaims(),
        "predecessor_snapshot_sha256": (
            value.predecessor_snapshot_sha256
        ),
        "producer_authority_record_sha256": (
            value.producer_authority_record_sha256
        ),
        "semantic_payload_contract_sha256": (
            linux_confinement_semantic_payload_contract_sha256()
        ),
        "snapshot_stage_id": value.snapshot_stage_id,
        "staging_run_binding_sha256": (
            value.staging_run_binding_sha256
        ),
        "subject_identity_table_sha256": (
            value.subject_identity_table_sha256
        ),
        "task_rows": rows,
        "trusted_producer_id": value.trusted_producer_id,
        "validation_scope_id": (
            LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_VALIDATION_SCOPE
        ),
    }


def linux_confinement_process_identity_snapshot_bytes(
    value: LinuxConfinementProcessIdentitySnapshotV1,
) -> bytes:
    return _canonical_json(
        _snapshot_tree(value),
        maximum=MAXIMUM_LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_BYTES,
    )


def linux_confinement_process_identity_snapshot_sha256(
    value: LinuxConfinementProcessIdentitySnapshotV1,
) -> str:
    return _domain_sha256(
        LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_DIGEST_DOMAIN,
        linux_confinement_process_identity_snapshot_bytes(value),
    )


_TASK_ROW_FIELD_IDS: Final = (
    "active_role_id",
    "exit_observation_record_sha256",
    "host_pid_namespace_device",
    "host_pid_namespace_inode",
    "host_tgid",
    "kernel_task_instance_sha256",
    "lifecycle_state_id",
    "lifecycle_transition_record_sha256",
    "nspid_vector",
    "parent_task_slot_id",
    "pidfd_acquisition_method_id",
    "pidfd_acquisition_record_sha256",
    "proc_starttime_clock_ticks",
    "reaper_role_id",
    "task_slot_id",
    "wait_reap_record_sha256",
)


def _parse_task_identity(
    tree: dict,
    *,
    snapshot_stage_id: str,
    staging_run_binding_sha256: str,
    linux_platform_profile_sha256: str,
    linux_boot_id_sha256: str,
) -> LinuxConfinementTaskIdentityV1:
    _exact_keys(tree, _TASK_ROW_FIELD_IDS)
    nspid = tree["nspid_vector"]
    if type(nspid) is not list:
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
    result = LinuxConfinementTaskIdentityV1(
        task_slot_id=tree["task_slot_id"],
        lifecycle_state_id=tree["lifecycle_state_id"],
        active_role_id=tree["active_role_id"],
        host_tgid=tree["host_tgid"],
        proc_starttime_clock_ticks=tree["proc_starttime_clock_ticks"],
        host_pid_namespace_device=tree["host_pid_namespace_device"],
        host_pid_namespace_inode=tree["host_pid_namespace_inode"],
        nspid_vector=tuple(nspid),
        pidfd_acquisition_method_id=tree["pidfd_acquisition_method_id"],
        pidfd_acquisition_record_sha256=(
            tree["pidfd_acquisition_record_sha256"]
        ),
        parent_task_slot_id=tree["parent_task_slot_id"],
        lifecycle_transition_record_sha256=(
            tree["lifecycle_transition_record_sha256"]
        ),
        exit_observation_record_sha256=(
            tree["exit_observation_record_sha256"]
        ),
        wait_reap_record_sha256=tree["wait_reap_record_sha256"],
        reaper_role_id=tree["reaper_role_id"],
    )
    _validated_task_identity(
        result,
        snapshot_stage_id=snapshot_stage_id,
    )
    expected_instance = linux_confinement_kernel_task_instance_sha256(
        result,
        staging_run_binding_sha256=staging_run_binding_sha256,
        linux_platform_profile_sha256=linux_platform_profile_sha256,
        linux_boot_id_sha256=linux_boot_id_sha256,
    )
    if tree["kernel_task_instance_sha256"] != expected_instance:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    return result


def parse_linux_confinement_process_identity_snapshot(
    value: bytes,
) -> LinuxConfinementProcessIdentitySnapshotV1:
    tree = _parse_canonical_json(
        value,
        maximum=MAXIMUM_LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_BYTES,
    )
    _exact_keys(
        tree,
        (
            "artifact_type",
            "capture_monotonic_timestamp_ns",
            "format_version",
            "linux_boot_id_sha256",
            "linux_platform_profile_sha256",
            "nonclaims",
            "predecessor_snapshot_sha256",
            "producer_authority_record_sha256",
            "semantic_payload_contract_sha256",
            "snapshot_stage_id",
            "staging_run_binding_sha256",
            "subject_identity_table_sha256",
            "task_rows",
            "trusted_producer_id",
            "validation_scope_id",
        ),
    )
    if (
        tree["artifact_type"]
        != LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or tree["nonclaims"] != _false_nonclaims()
        or tree["semantic_payload_contract_sha256"]
        != linux_confinement_semantic_payload_contract_sha256()
        or tree["validation_scope_id"]
        != LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_VALIDATION_SCOPE
        or type(tree["task_rows"]) is not list
        or tree["snapshot_stage_id"]
        not in LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_STAGE_IDS
    ):
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    rows = tuple(
        _parse_task_identity(
            row,
            snapshot_stage_id=tree["snapshot_stage_id"],
            staging_run_binding_sha256=(
                tree["staging_run_binding_sha256"]
            ),
            linux_platform_profile_sha256=(
                tree["linux_platform_profile_sha256"]
            ),
            linux_boot_id_sha256=tree["linux_boot_id_sha256"],
        )
        for row in tree["task_rows"]
    )
    result = LinuxConfinementProcessIdentitySnapshotV1(
        staging_run_binding_sha256=tree["staging_run_binding_sha256"],
        subject_identity_table_sha256=(
            tree["subject_identity_table_sha256"]
        ),
        linux_platform_profile_sha256=(
            tree["linux_platform_profile_sha256"]
        ),
        linux_boot_id_sha256=tree["linux_boot_id_sha256"],
        snapshot_stage_id=tree["snapshot_stage_id"],
        predecessor_snapshot_sha256=(
            tree["predecessor_snapshot_sha256"]
        ),
        capture_monotonic_timestamp_ns=(
            tree["capture_monotonic_timestamp_ns"]
        ),
        trusted_producer_id=tree["trusted_producer_id"],
        task_identities=rows,
        producer_authority_record_sha256=(
            tree["producer_authority_record_sha256"]
        ),
    )
    if linux_confinement_process_identity_snapshot_bytes(result) != value:
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
    return result


def validate_linux_confinement_process_identity_snapshot_chain(
    snapshots: Tuple[LinuxConfinementProcessIdentitySnapshotV1, ...],
    *,
    subject_identity_table: LinuxConfinementSubjectIdentityTableV1,
) -> None:
    """Validate the exact three-stage chain and stable task instances."""

    _validated_subject_table(subject_identity_table)
    if (
        type(snapshots) is not tuple
        or len(snapshots)
        != len(LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_STAGE_IDS)
        or any(
            type(item) is not LinuxConfinementProcessIdentitySnapshotV1
            for item in snapshots
        )
    ):
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    table_sha256 = linux_confinement_subject_identity_table_sha256(
        subject_identity_table
    )
    prior_sha256 = _ZERO_SHA256
    prior_timestamp = -1
    for index, snapshot in enumerate(snapshots):
        _validated_snapshot(snapshot)
        if (
            snapshot.snapshot_stage_id
            != LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_STAGE_IDS[
                index
            ]
            or snapshot.predecessor_snapshot_sha256 != prior_sha256
            or snapshot.subject_identity_table_sha256 != table_sha256
            or snapshot.staging_run_binding_sha256
            != subject_identity_table.staging_run_binding_sha256
            or snapshot.capture_monotonic_timestamp_ns <= prior_timestamp
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
        prior_sha256 = (
            linux_confinement_process_identity_snapshot_sha256(snapshot)
        )
        prior_timestamp = snapshot.capture_monotonic_timestamp_ns
    profiles = {item.linux_platform_profile_sha256 for item in snapshots}
    boots = {item.linux_boot_id_sha256 for item in snapshots}
    if len(profiles) != 1 or len(boots) != 1:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    rows_by_stage = tuple(
        {row.task_slot_id: row for row in snapshot.task_identities}
        for snapshot in snapshots
    )
    for task_slot_id in LINUX_CONFINEMENT_TASK_SLOT_IDS:
        indices = (1, 2) if task_slot_id == "application-task" else (0, 1, 2)
        instance_ids = {
            linux_confinement_kernel_task_instance_sha256(
                rows_by_stage[index][task_slot_id],
                staging_run_binding_sha256=(
                    snapshots[index].staging_run_binding_sha256
                ),
                linux_platform_profile_sha256=(
                    snapshots[index].linux_platform_profile_sha256
                ),
                linux_boot_id_sha256=(
                    snapshots[index].linux_boot_id_sha256
                ),
            )
            for index in indices
        }
        if len(instance_ids) != 1 or _ZERO_SHA256 in instance_ids:
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
        stable_rows = [
            rows_by_stage[index][task_slot_id] for index in indices
        ]
        stable_components = {
            (
                row.host_tgid,
                row.proc_starttime_clock_ticks,
                row.host_pid_namespace_device,
                row.host_pid_namespace_inode,
                row.nspid_vector,
                row.pidfd_acquisition_method_id,
                row.pidfd_acquisition_record_sha256,
                row.parent_task_slot_id,
                row.reaper_role_id,
            )
            for row in stable_rows
        }
        if len(stable_components) != 1:
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    helper_rows = tuple(
        rows["helper-task"] for rows in rows_by_stage
    )
    if len(set(helper_rows)) != 1:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    final_instances = {
        linux_confinement_kernel_task_instance_sha256(
            row,
            staging_run_binding_sha256=(
                snapshots[2].staging_run_binding_sha256
            ),
            linux_platform_profile_sha256=(
                snapshots[2].linux_platform_profile_sha256
            ),
            linux_boot_id_sha256=snapshots[2].linux_boot_id_sha256,
        )
        for row in snapshots[2].task_identities
    }
    if (
        len(final_instances)
        != LINUX_CONFINEMENT_EXPECTED_PROCESS_INSTANCE_COUNT
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


@dataclass(frozen=True)
class _ObservationSchema:
    observation_id: str
    family_id: str
    snapshot_stage_id: str
    lifecycle_stage_id: str
    trusted_producer_id: str
    procedure_id: str
    predicate_id: str
    receipt_leaf_id: str
    subject_role_ids: Tuple[str, ...]
    raw_evidence_field_ids: Tuple[str, ...]


def _family_id(observation_id: str) -> str:
    if observation_id in _FAMILY_F1:
        return LINUX_CONFINEMENT_OBSERVATION_FAMILY_IDS[0]
    if observation_id in _FAMILY_F2:
        return LINUX_CONFINEMENT_OBSERVATION_FAMILY_IDS[1]
    if observation_id in _FAMILY_F3:
        return LINUX_CONFINEMENT_OBSERVATION_FAMILY_IDS[2]
    if observation_id in _FAMILY_F4:
        return LINUX_CONFINEMENT_OBSERVATION_FAMILY_IDS[3]
    _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)


def _snapshot_stage_id(lifecycle_stage_id: str) -> str:
    if lifecycle_stage_id in (
        "pre-backend-exec",
        "pre-first-child-artifact-validation",
        "pre-stage1-setup-blocked",
    ):
        return LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE1
    if lifecycle_stage_id == "pre-stage2-application-stopped":
        return LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE2
    if lifecycle_stage_id in (
        "cross-stage-run-transcript",
        "cross-stage-through-postrun",
        "postrun-cleanup-complete",
    ):
        return LINUX_CONFINEMENT_SNAPSHOT_STAGE_POSTRUN
    _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)


def _build_observation_schemas() -> Tuple[_ObservationSchema, ...]:
    try:
        raw_specs = linux_confinement_evidence_plan_tree()[
            "observation_specs"
        ]
    except (KeyError, TypeError, ValueError):
        _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)
    if type(raw_specs) is not list or len(raw_specs) != 24:
        _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)
    result = []
    for item in raw_specs:
        try:
            schema = _ObservationSchema(
                observation_id=item["item_id"],
                family_id=_family_id(item["item_id"]),
                snapshot_stage_id=_snapshot_stage_id(
                    item["lifecycle_stage_id"]
                ),
                lifecycle_stage_id=item["lifecycle_stage_id"],
                trusted_producer_id=item["trusted_producer_id"],
                procedure_id=item["procedure_id"],
                predicate_id=item["predicate_id"],
                receipt_leaf_id=item["receipt_leaf_id"],
                subject_role_ids=tuple(item["subject_role_ids"]),
                raw_evidence_field_ids=tuple(
                    item["raw_evidence_field_ids"]
                ),
            )
        except (KeyError, TypeError, ValueError):
            _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)
        result.append(schema)
    return tuple(result)


_OBSERVATION_SCHEMAS: Final = _build_observation_schemas()
LINUX_CONFINEMENT_OBSERVATION_IDS: Final = tuple(
    item.observation_id for item in _OBSERVATION_SCHEMAS
)
_EVIDENCE_PLAN_TREE_FOR_AGGREGATE: Final = (
    linux_confinement_evidence_plan_tree()
)
LINUX_CONFINEMENT_AGGREGATE_OBSERVATION_IDS: Final = tuple(
    _EVIDENCE_PLAN_TREE_FOR_AGGREGATE["release_gate_specs"][0][
        "required_observation_ids"
    ]
    + _EVIDENCE_PLAN_TREE_FOR_AGGREGATE["release_gate_specs"][1][
        "required_observation_ids"
    ]
    + _EVIDENCE_PLAN_TREE_FOR_AGGREGATE[
        "postrun_finalized_observation_ids"
    ]
)
LINUX_CONFINEMENT_RAW_EVIDENCE_FIELD_IDS: Final = tuple(
    sorted(
        {
            field_id
            for item in _OBSERVATION_SCHEMAS
            for field_id in item.raw_evidence_field_ids
        }
    )
)
LINUX_CONFINEMENT_SUBJECT_ROLE_IDS: Final = tuple(
    sorted(
        {
            role_id
            for item in _OBSERVATION_SCHEMAS
            for role_id in item.subject_role_ids
        }
    )
)
_OBSERVATION_SCHEMA_BY_ID: Final = MappingProxyType(
    {item.observation_id: item for item in _OBSERVATION_SCHEMAS}
)


def _observation_schema(observation_id: str) -> _ObservationSchema:
    if type(observation_id) is not str:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    try:
        return _OBSERVATION_SCHEMA_BY_ID[observation_id]
    except KeyError:
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)


def linux_confinement_observation_payload_artifact_type(
    observation_id: str,
) -> str:
    _observation_schema(observation_id)
    return (
        LINUX_CONFINEMENT_OBSERVATION_PAYLOAD_ARTIFACT_TYPE_PREFIX
        + observation_id
        + ".v1"
    )


def linux_confinement_evidence_field_semantic_type_id(
    field_id: str,
) -> str:
    if field_id not in LINUX_CONFINEMENT_RAW_EVIDENCE_FIELD_IDS:
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    return (
        "heterodiff.adapter.linux-evidence-field."
        + field_id
        + ".v1"
    )


def _field_codec_id(field_id: str) -> str:
    if field_id in _SHA256_FIELD_IDS:
        return LINUX_CONFINEMENT_CODEC_SHA256_HEX_ASCII
    if field_id in _U64_FIELD_IDS:
        return LINUX_CONFINEMENT_CODEC_U64BE
    if field_id in _NUL_FRAME_FIELD_IDS:
        return LINUX_CONFINEMENT_CODEC_NUL_FRAME
    if field_id in _BOUNDED_OCTET_FIELD_IDS:
        return LINUX_CONFINEMENT_CODEC_BOUNDED_OCTETS
    if field_id in LINUX_CONFINEMENT_RAW_EVIDENCE_FIELD_IDS:
        return LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT
    _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)


def linux_confinement_evidence_field_codec_id(field_id: str) -> str:
    return _field_codec_id(field_id)


def _field_comparator_id(field_id: str) -> str:
    codec = _field_codec_id(field_id)
    if codec == LINUX_CONFINEMENT_CODEC_SHA256_HEX_ASCII:
        return "exact-digest-policy-or-cross-record-pin-equality-v1"
    if codec == LINUX_CONFINEMENT_CODEC_U64BE:
        return "exact-u64-policy-or-cross-record-equality-v1"
    return "profile-predicate-input-not-portably-evaluated-v1"


def _validate_nul_frame(field_id: str, value: bytes) -> None:
    if len(value) > MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
    if value == b"":
        return
    if not value.endswith(b"\x00"):
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)


def _validate_canonical_json_object(value: bytes) -> None:
    parsed = _parse_canonical_json(
        value,
        maximum=MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES,
    )
    if type(parsed) is not dict:
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)


_RECORD_ENVELOPE_FIELD_IDS: Final = (
    "canonical_projection",
    "canonical_projection_sha256",
    "field_id",
    "native_origin_authenticated",
    "parser_id",
    "portable_projection_recomputed",
    "raw_source_byte_count",
    "raw_source_hex",
    "raw_source_plain_sha256",
    "schema_version",
)
_ALIAS_TRANSITION_ROLE_IDS: Final = MappingProxyType(
    {
        (
            "unprivileged-preexec-launcher-to-monitor-same-pid-"
            "exec-and-reap-record"
        ): (
            "unprivileged-preexec-launcher",
            "bubblewrap-monitor",
        ),
        (
            "bubblewrap-setup-child-to-sandbox-pid1-same-host-pid-"
            "lifecycle-transition-record"
        ): (
            "bubblewrap-setup-child",
            "sandbox-pid1-reaper",
        ),
    }
)


LINUX_CONFINEMENT_PROJECTION_SCHEMA_ID_PREFIX: Final = (
    "heterodiff.adapter.linux-evidence-projection."
)
_SEMANTIC_JOIN_ROWS: Final = (
    (
        "projection-context-pins-v1",
        "local",
        "projection observation, run, table, and snapshot pins equal payload",
    ),
    (
        "projection-subject-reference-domain-v1",
        "local",
        "ordered projection subject refs equal bound subject identities",
    ),
    (
        "scalar-resource-component-v1",
        "local",
        "typed scalar evidence equals its bound resource component",
    ),
    (
        "projection-resource-component-v1",
        "local-available-only",
        "claimed object, namespace, content, and platform identities resolve",
    ),
    (
        "task-snapshot-reference-v1",
        "local-available-only",
        "known role and slot task references resolve into snapshot rows",
    ),
    (
        "run-topology-reference-v1",
        "local-available-only",
        "run nonce, sequence, epoch, and event run pins equal topology",
    ),
    (
        "projection-internal-arithmetic-v1",
        "local-available-only",
        "declared byte and row counts agree with retained typed values",
    ),
    (
        "within-observation-reference-domain-v1",
        "local-available-only",
        "fd, mount, network, map, and stdout references resolve locally",
    ),
    (
        "aggregate-repeated-resource-stability-v1",
        "aggregate",
        "repeated resource roles retain stable identity components",
    ),
    (
        "aggregate-architecture-coherence-v1",
        "aggregate-available-only",
        "comparable projection and platform architecture identifiers agree",
    ),
    (
        "aggregate-elf-machine-coherence-v1",
        "aggregate-available-only",
        "backend and interpreter ELF machine identifiers agree",
    ),
)
LINUX_CONFINEMENT_SEMANTIC_JOIN_IDS: Final = tuple(
    row[0] for row in _SEMANTIC_JOIN_ROWS
)
LINUX_CONFINEMENT_PROJECTION_NODE_KIND_IDS: Final = (
    "boolean",
    "list",
    "object",
    "octets",
    "optional-sha256",
    "path",
    "sha256",
    "token",
    "u64",
)
_PROJECTION_FIELD_IDS: Final = (
    "field_id",
    "observation_id",
    "process_identity_snapshot_sha256",
    "projection_schema_id",
    "source_errno_id",
    "source_observation_available",
    "source_observation_status_id",
    "staging_run_binding_sha256",
    "subject_identity_refs",
    "subject_identity_table_sha256",
    "values",
)
_PROJECTION_SUBJECT_REF_FIELD_IDS: Final = (
    "subject_identity_sha256",
    "subject_role_id",
)


@dataclass(frozen=True)
class _ProjectionSchemaNode:
    """One closed recursive node in the portable projection-schema DSL."""

    node_kind_id: str
    field_rows: Tuple[Tuple[str, object], ...] = ()
    item_schema: object = None

    def __post_init__(self) -> None:
        if (
            type(self) is not _ProjectionSchemaNode
            or self.node_kind_id
            not in LINUX_CONFINEMENT_PROJECTION_NODE_KIND_IDS
            or type(self.field_rows) is not tuple
        ):
            _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)
        if self.node_kind_id == "list":
            if (
                self.field_rows
                or type(self.item_schema) is not _ProjectionSchemaNode
            ):
                _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)
            return
        if self.node_kind_id != "object":
            if self.field_rows or self.item_schema is not None:
                _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)
            return
        if self.item_schema is not None:
            _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)
        field_ids = []
        for row in self.field_rows:
            if (
                type(row) is not tuple
                or len(row) != 2
                or type(row[0]) is not str
                or type(row[1]) is not _ProjectionSchemaNode
            ):
                _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)
            _token(row[0])
            field_ids.append(row[0])
        if not field_ids or len(field_ids) != len(set(field_ids)):
            _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)


def _projection_scalar(kind_id: str) -> _ProjectionSchemaNode:
    return _ProjectionSchemaNode(node_kind_id=kind_id)


def _projection_object(
    *field_rows: Tuple[str, _ProjectionSchemaNode],
) -> _ProjectionSchemaNode:
    return _ProjectionSchemaNode(
        node_kind_id="object",
        field_rows=tuple(field_rows),
    )


def _projection_list(
    item_schema: _ProjectionSchemaNode,
) -> _ProjectionSchemaNode:
    return _ProjectionSchemaNode(
        node_kind_id="list",
        item_schema=item_schema,
    )


_P_BOOL: Final = _projection_scalar("boolean")
_P_OCTETS: Final = _projection_scalar("octets")
_P_OPTIONAL_SHA256: Final = _projection_scalar("optional-sha256")
_P_PATH: Final = _projection_scalar("path")
_P_SHA256: Final = _projection_scalar("sha256")
_P_TOKEN: Final = _projection_scalar("token")
_P_U64: Final = _projection_scalar("u64")

_P_TOKEN_LIST: Final = _projection_list(_P_TOKEN)
_P_OCTETS_LIST: Final = _projection_list(_P_OCTETS)
_P_U64_LIST: Final = _projection_list(_P_U64)
_P_FULL_STAT: Final = _projection_object(
    ("device", _P_U64),
    ("inode", _P_U64),
    ("generation", _P_U64),
    ("file_type_id", _P_TOKEN),
    ("mode", _P_U64),
    ("uid", _P_U64),
    ("gid", _P_U64),
    ("nlink", _P_U64),
    ("size_bytes", _P_U64),
)
_P_KERNEL_OBJECT: Final = _projection_object(
    ("device", _P_U64),
    ("inode", _P_U64),
    ("generation", _P_U64),
    ("kernel_object_type_id", _P_TOKEN),
)
_P_NAMESPACE_IDENTITY: Final = _projection_object(
    ("namespace_id", _P_TOKEN),
    ("device", _P_U64),
    ("inode", _P_U64),
    ("owner_user_namespace_inode", _P_U64),
)
_P_ID_MAP: Final = _projection_object(
    ("inside_id", _P_U64),
    ("outside_id", _P_U64),
    ("length", _P_U64),
)
_P_WAIT_STATUS: Final = _projection_object(
    ("wait_kind_id", _P_TOKEN),
    ("status_value", _P_U64),
    ("core_dumped", _P_BOOL),
)

_P_FIELD_01_CWD_MOUNT_AND_INODE: Final = _projection_object(
    ("cwd_path", _P_PATH),
    ("cwd_mount_id", _P_U64),
    ("cwd_device_major", _P_U64),
    ("cwd_device_minor", _P_U64),
    ("cwd_inode", _P_U64),
    ("cwd_file_type_id", _P_TOKEN),
)
_P_FIELD_02_UMASK_OCTAL: Final = _projection_object(
    ("umask_octal", _P_TOKEN),
)
_P_FIELD_03_BACKEND_MEMFD_STAT: Final = _projection_object(
    ("stat", _P_FULL_STAT),
)
_P_FIELD_04_BACKEND_MEMFD_FLAGS: Final = _projection_object(
    ("access_mode_id", _P_TOKEN),
    ("memfd_create_flags_mask", _P_U64),
    ("memfd_create_flag_ids", _P_TOKEN_LIST),
    ("fd_cloexec", _P_BOOL),
    ("executable", _P_BOOL),
)
_P_FIELD_05_BACKEND_MEMFD_SEALS: Final = _projection_object(
    ("seals_mask", _P_U64),
    ("seal_ids", _P_TOKEN_LIST),
)
_P_FIELD_06_BACKEND_ELF_PROGRAM_HEADERS: Final = _projection_object(
    ("elf_class_id", _P_TOKEN),
    ("endianness_id", _P_TOKEN),
    ("machine_id", _P_TOKEN),
    ("elf_type_id", _P_TOKEN),
    (
        "program_headers",
        _projection_list(
            _projection_object(
                ("index", _P_U64),
                ("type_id", _P_TOKEN),
                ("flag_ids", _P_TOKEN_LIST),
                ("file_offset", _P_U64),
                ("virtual_address", _P_U64),
                ("physical_address", _P_U64),
                ("file_size", _P_U64),
                ("memory_size", _P_U64),
                ("alignment", _P_U64),
            )
        ),
    ),
    ("pt_interp_count", _P_U64),
    ("writable_executable_segment_count", _P_U64),
)
_P_FIELD_07_BACKEND_ELF_DYNAMIC: Final = _projection_object(
    ("dynamic_section_present", _P_BOOL),
    ("dynamic_tag_ids", _P_TOKEN_LIST),
    ("dt_needed_sonames", _P_OCTETS_LIST),
    ("dt_needed_count", _P_U64),
    ("pt_interp_present", _P_BOOL),
)
_P_FIELD_08_CAPABILITY_SET: Final = _projection_object(
    ("ambient_mask", _P_U64),
    ("ambient", _P_TOKEN_LIST),
    ("bounding_mask", _P_U64),
    ("bounding", _P_TOKEN_LIST),
    ("effective_mask", _P_U64),
    ("effective", _P_TOKEN_LIST),
    ("inheritable_mask", _P_U64),
    ("inheritable", _P_TOKEN_LIST),
    ("permitted_mask", _P_U64),
    ("permitted", _P_TOKEN_LIST),
)
_P_FIELD_09_SECUREBITS_MASK: Final = _projection_object(
    ("securebits_mask", _P_U64),
)
_P_FIELD_10_DUMPABLE: Final = _projection_object(
    ("dumpable", _P_U64),
)
_P_FIELD_11_UID_GID_AND_GROUPS: Final = _projection_object(
    ("uid", _P_U64),
    ("gid", _P_U64),
    ("supplementary_gids", _P_U64_LIST),
)
_P_FIELD_12_CGROUP_PROCESS_MEMBERSHIP: Final = _projection_object(
    ("cgroup_version_id", _P_TOKEN),
    ("leaf_identity_sha256", _P_SHA256),
    (
        "members",
        _projection_list(
            _projection_object(
                ("role_id", _P_TOKEN),
                ("kernel_task_instance_sha256", _P_SHA256),
            )
        ),
    ),
)
_P_FIELD_13_CGROUP_LEAF_STAT: Final = _projection_object(
    ("filesystem_type_id", _P_TOKEN),
    ("object", _P_KERNEL_OBJECT),
    ("mount_id", _P_U64),
)
_P_FIELD_14_CGROUP_LEAF_OWNER: Final = _projection_object(
    ("owner_uid", _P_U64),
    ("owner_gid", _P_U64),
    ("owner_user_namespace_inode", _P_U64),
    ("owner_task_instance_sha256", _P_SHA256),
)
_P_FIELD_15_CGROUP_DELEGATION: Final = _projection_object(
    ("delegated_controller_ids", _P_TOKEN_LIST),
    ("subtree_control_controller_ids", _P_TOKEN_LIST),
    ("delegation_enabled", _P_BOOL),
    ("parent_path", _P_PATH),
    ("leaf_path", _P_PATH),
    ("preexisting_member_count", _P_U64),
)
_P_FIELD_16_APPLICATION_FD_INVENTORY: Final = _projection_object(
    (
        "descriptors",
        _projection_list(
            _projection_object(
                ("fd_number", _P_U64),
                ("fd_role_id", _P_TOKEN),
            )
        ),
    ),
)
_P_FIELD_17_FD_KERNEL_OBJECT_STATS: Final = _projection_object(
    (
        "descriptors",
        _projection_list(
            _projection_object(
                ("fd_number", _P_U64),
                ("fd_role_id", _P_TOKEN),
                ("object", _P_KERNEL_OBJECT),
            )
        ),
    ),
)
_P_FIELD_18_FD_ACCESS_FLAGS_AND_OFFSETS: Final = _projection_object(
    (
        "descriptors",
        _projection_list(
            _projection_object(
                ("fd_number", _P_U64),
                ("fd_role_id", _P_TOKEN),
                ("access_mode_id", _P_TOKEN),
                ("nonblocking", _P_BOOL),
                ("offset_rule_id", _P_TOKEN),
                ("offset_bytes", _P_U64),
            )
        ),
    ),
)
_P_FIELD_19_FD_CLOEXEC_AND_INHERITANCE: Final = _projection_object(
    (
        "descriptors",
        _projection_list(
            _projection_object(
                ("fd_number", _P_U64),
                ("fd_role_id", _P_TOKEN),
                ("fd_cloexec_before_backend_exec", _P_BOOL),
                ("inherited_by_backend", _P_BOOL),
                ("inherited_by_application", _P_BOOL),
            )
        ),
    ),
)
_P_FIELD_20_STDIO_ISATTY: Final = _projection_object(
    (
        "stdio",
        _projection_list(
            _projection_object(
                ("fd_number", _P_U64),
                ("fd_role_id", _P_TOKEN),
                ("isatty", _P_BOOL),
            )
        ),
    ),
)
_P_FIELD_21_SUPERVISOR_PEER_CUSTODY: Final = _projection_object(
    (
        "peers",
        _projection_list(
            _projection_object(
                ("application_fd_number", _P_U64),
                ("fd_role_id", _P_TOKEN),
                ("peer_kernel_object_identity_sha256", _P_SHA256),
                ("peer_custody_id", _P_TOKEN),
            )
        ),
    ),
)
_P_FIELD_22_NAMESPACE_PARENT_CHAIN: Final = _projection_object(
    (
        "levels",
        _projection_list(
            _projection_object(
                ("level_id", _P_TOKEN),
                ("identity", _P_NAMESPACE_IDENTITY),
            )
        ),
    ),
    (
        "parent_edges",
        _projection_list(
            _projection_object(
                ("child_level_id", _P_TOKEN),
                ("parent_level_id", _P_TOKEN),
            )
        ),
    ),
)
_P_FIELD_23_HOST_VIEW_FINAL_MAP: Final = _projection_object(
    ("final_uid_map", _projection_list(_P_ID_MAP)),
    ("final_gid_map", _projection_list(_P_ID_MAP)),
)
_P_VIEW_MAP_WITH_SOURCE: Final = _projection_object(
    ("inside_id", _P_U64),
    ("outside_id", _P_U64),
    ("length", _P_U64),
    ("outside_id_source_id", _P_TOKEN),
)
_P_FIELD_24_INTERMEDIATE_VIEW_MAPS: Final = _projection_object(
    (
        "intermediate_uid_map",
        _projection_list(_P_VIEW_MAP_WITH_SOURCE),
    ),
    (
        "intermediate_gid_map",
        _projection_list(_P_VIEW_MAP_WITH_SOURCE),
    ),
    ("final_uid_map", _projection_list(_P_ID_MAP)),
    ("final_gid_map", _projection_list(_P_ID_MAP)),
)
_P_FIELD_25_SETGROUPS_STATE: Final = _projection_object(
    (
        "levels",
        _projection_list(
            _projection_object(
                ("level_id", _P_TOKEN),
                ("setgroups_bytes_hex", _P_OCTETS),
            )
        ),
    ),
)
_P_FIELD_26_APPLICATION_SUPPLEMENTARY_GROUP: Final = _projection_object(
    ("supplementary_gids", _P_U64_LIST),
)
_P_FIELD_27_OBSERVER_ADOPTION_AND_REAP: Final = _projection_object(
    ("observer_task_instance_sha256", _P_SHA256),
    ("pidfd_acquisition_record_sha256", _P_OPTIONAL_SHA256),
    ("original_parent_task_instance_sha256", _P_OPTIONAL_SHA256),
    ("adopter_task_instance_sha256", _P_OPTIONAL_SHA256),
    ("exit_observation_record_sha256", _P_OPTIONAL_SHA256),
    ("wait_reap_record_sha256", _P_OPTIONAL_SHA256),
    ("wait_status", _P_WAIT_STATUS),
    ("reap_monotonic_timestamp_ns", _P_U64),
)
_P_FIELD_28_ROOT_MOUNT_STAT_AND_FLAGS: Final = _projection_object(
    ("mount_id", _P_U64),
    ("parent_mount_id", _P_U64),
    ("device_major", _P_U64),
    ("device_minor", _P_U64),
    ("inode", _P_U64),
    ("filesystem_type_id", _P_TOKEN),
    ("mount_flags", _P_TOKEN_LIST),
    ("super_options", _P_TOKEN_LIST),
    ("read_only", _P_BOOL),
)

_P_FULL_EVENT: Final = _projection_object(
    ("event_id", _P_TOKEN),
    ("sequence_number", _P_U64),
    ("monotonic_timestamp_ns", _P_U64),
    ("staging_run_binding_sha256", _P_SHA256),
    ("evidence_digest_sha256", _P_OPTIONAL_SHA256),
)
_P_FULL_MOUNT: Final = _projection_object(
    ("mount_id", _P_U64),
    ("parent_mount_id", _P_U64),
    ("device_major", _P_U64),
    ("device_minor", _P_U64),
    ("root_path", _P_PATH),
    ("mount_point", _P_PATH),
    ("mount_options", _P_TOKEN_LIST),
    ("optional_fields", _P_TOKEN_LIST),
    ("filesystem_type_id", _P_TOKEN),
    ("mount_source", _P_PATH),
    ("super_options", _P_TOKEN_LIST),
)
_P_ROUTE_ROW: Final = _projection_object(
    ("destination_address_hex", _P_OCTETS),
    ("prefix_length", _P_U64),
    ("route_type_id", _P_TOKEN),
    ("scope_id", _P_TOKEN),
    ("table_id", _P_U64),
    ("output_ifindex", _P_U64),
    ("gateway_address_hex", _P_OCTETS),
    ("preferred_source_address_hex", _P_OCTETS),
    ("metric", _P_U64),
)

_P_FIELD_29_OLD_ROOT_HANDLE_ABSENCE: Final = _projection_object(
    ("probe_scope_id", _P_TOKEN),
    ("old_root_mount_present", _P_BOOL),
    ("reachable_old_root_handle_count", _P_U64),
)
_P_FIELD_30_LANDLOCK_QUERIED_ABI: Final = _projection_object(
    ("return_status_id", _P_TOKEN),
    ("errno_id", _P_TOKEN),
    ("queried_abi_version", _P_U64),
)
_P_FIELD_31_LANDLOCK_INSTALL_RETURN: Final = _projection_object(
    ("syscall_id", _P_TOKEN),
    ("return_status_id", _P_TOKEN),
    ("errno_id", _P_TOKEN),
    ("ruleset_content_sha256", _P_SHA256),
    ("no_new_privileges", _P_BOOL),
)
_P_FIELD_32_ARCHITECTURE: Final = _projection_object(
    ("architecture_id", _P_TOKEN),
)
_P_FIELD_33_KERNEL_RELEASE_AND_BUILD: Final = _projection_object(
    ("sysname", _P_TOKEN),
    ("release_bytes_hex", _P_OCTETS),
    ("version_bytes_hex", _P_OCTETS),
    ("machine_id", _P_TOKEN),
    ("boot_id_sha256", _P_SHA256),
)
_P_FIELD_34_LINUX_SECURITY_FEATURE_PROBE: Final = _projection_object(
    ("platform_profile_sha256", _P_SHA256),
    (
        "features",
        _projection_list(
            _projection_object(
                ("feature_id", _P_TOKEN),
                ("available", _P_BOOL),
                ("version_number", _P_U64),
                ("probe_result_id", _P_TOKEN),
            )
        ),
    ),
)
_P_FIELD_35_CANONICAL_MOUNTINFO: Final = _projection_object(
    ("mounts", _projection_list(_P_FULL_MOUNT)),
)
_P_FIELD_36_MOUNT_PROPAGATION: Final = _projection_object(
    (
        "mounts",
        _projection_list(
            _projection_object(
                ("mount_id", _P_U64),
                ("propagation_id", _P_TOKEN),
                ("peer_group_id", _P_U64),
                ("master_group_id", _P_U64),
            )
        ),
    ),
)
_P_FIELD_37_WRITABLE_PATH_INVENTORY: Final = _projection_object(
    (
        "writable_paths",
        _projection_list(
            _projection_object(
                ("path", _P_PATH),
                ("mount_id", _P_U64),
                ("device_major", _P_U64),
                ("device_minor", _P_U64),
                ("inode", _P_U64),
            )
        ),
    ),
)
_P_FIELD_38_DEVICE_MOUNT_FLAGS: Final = _projection_object(
    ("dev_read_only", _P_BOOL),
    ("devpts_read_only", _P_BOOL),
    ("dev_shm_mode_octal", _P_TOKEN),
    ("dev_shm_writable", _P_BOOL),
    ("ptmx_mode_octal", _P_TOKEN),
    ("host_tty_device_binding_present", _P_BOOL),
    ("pty_allocation_admitted", _P_BOOL),
)
_P_FIELD_39_FORBIDDEN_MOUNT_TYPE_ABSENCE: Final = _projection_object(
    ("forbidden_mount_type_ids", _P_TOKEN_LIST),
    (
        "observed_forbidden_mounts",
        _projection_list(
            _projection_object(
                ("mount_id", _P_U64),
                ("filesystem_type_id", _P_TOKEN),
            )
        ),
    ),
)
_P_FIELD_40_APPLICATION_NAMESPACE_INODES: Final = _projection_object(
    ("namespaces", _projection_list(_P_NAMESPACE_IDENTITY)),
)
_P_FIELD_41_HOST_NAMESPACE_INODES: Final = _projection_object(
    ("namespaces", _projection_list(_P_NAMESPACE_IDENTITY)),
)
_P_FIELD_42_NAMESPACE_PARENTAGE: Final = _projection_object(
    (
        "relations",
        _projection_list(
            _projection_object(
                ("namespace_id", _P_TOKEN),
                ("child_identity", _P_NAMESPACE_IDENTITY),
                ("parent_identity", _P_NAMESPACE_IDENTITY),
                ("parent_level_id", _P_TOKEN),
            )
        ),
    ),
)
_P_FIELD_43_NETWORK_INTERFACE: Final = _projection_object(
    (
        "interfaces",
        _projection_list(
            _projection_object(
                ("ifindex", _P_U64),
                ("interface_name_bytes_hex", _P_OCTETS),
                ("flags", _P_TOKEN_LIST),
                ("mtu", _P_U64),
                ("operstate_id", _P_TOKEN),
                (
                    "addresses",
                    _projection_list(
                        _projection_object(
                            ("family_id", _P_TOKEN),
                            ("address_hex", _P_OCTETS),
                            ("prefix_length", _P_U64),
                            ("scope_id", _P_TOKEN),
                        )
                    ),
                ),
            )
        ),
    ),
)
_P_FIELD_44_IPV4_ROUTE: Final = _projection_object(
    ("routes", _projection_list(_P_ROUTE_ROW)),
)
_P_FIELD_45_IPV6_ROUTE: Final = _projection_object(
    ("routes", _projection_list(_P_ROUTE_ROW)),
)
_P_FIELD_46_NETWORK_NAMESPACE_INODE: Final = _projection_object(
    ("namespace_id", _P_TOKEN),
    ("device", _P_U64),
    ("inode", _P_U64),
    ("owner_user_namespace_inode", _P_U64),
)
_P_FIELD_47_NO_NEW_PRIVILEGES: Final = _projection_object(
    ("no_new_privileges", _P_BOOL),
)
_P_FIELD_48_GETRANDOM_CALL: Final = _projection_object(
    ("syscall_id", _P_TOKEN),
    ("flags", _P_U64),
    ("requested_byte_count", _P_U64),
    ("returned_byte_count", _P_U64),
    ("returned_nonce_hex", _P_OCTETS),
    ("call_start_monotonic_ns", _P_U64),
    ("call_end_monotonic_ns", _P_U64),
)
_P_FIELD_49_NONCE_REGISTRY_INSERTION: Final = _projection_object(
    ("supervisor_epoch_id_hex", _P_OCTETS),
    ("run_nonce_hex", _P_OCTETS),
    ("insertion_index", _P_U64),
    ("prior_entry_count", _P_U64),
    ("post_entry_count", _P_U64),
    ("registry_capacity", _P_U64),
    ("prior_registry_commitment_sha256", _P_SHA256),
    ("post_registry_commitment_sha256", _P_SHA256),
    ("atomic_result_id", _P_TOKEN),
)
_P_FIELD_50_RUN_SEQUENCE: Final = _projection_object(
    ("run_sequence_number", _P_U64),
)
_P_FIELD_51_BUBBLEWRAP_CHILD_PID_STATUS: Final = _projection_object(
    ("status_schema_id", _P_TOKEN),
    ("child_host_tgid", _P_U64),
    ("child_task_instance_sha256", _P_SHA256),
    ("status_received_monotonic_ns", _P_U64),
)
_P_FIELD_52_STAGE1_BARRIER_PIPE_IDENTITY: Final = _projection_object(
    ("read_end", _P_KERNEL_OBJECT),
    ("write_end", _P_KERNEL_OBJECT),
    ("same_pipe_object", _P_BOOL),
)
_P_FIELD_53_PIDFD_BOUND_STAGE1_BARRIER_BLOCK: Final = (
    _projection_object(
        ("reader_task_instance_sha256", _P_SHA256),
        (
            "reader_pidfd_acquisition_record_sha256",
            _P_OPTIONAL_SHA256,
        ),
        ("barrier_identity_sha256", _P_SHA256),
        ("syscall_id", _P_TOKEN),
        ("requested_byte_count", _P_U64),
        ("blocked_state_id", _P_TOKEN),
        ("observation_method_id", _P_TOKEN),
        ("observed_monotonic_timestamp_ns", _P_U64),
    )
)
_P_FIELD_54_READY_FRAME_BYTES_AND_CHUNKS: Final = _projection_object(
    ("frame_hex", _P_OCTETS),
    ("frame_byte_count", _P_U64),
    ("chunk_byte_counts", _P_U64_LIST),
    ("run_nonce_hex", _P_OCTETS),
    ("stdout_read_end_identity_sha256", _P_SHA256),
    ("first_stdout_offset", _P_U64),
    ("accepted_frame_count", _P_U64),
    ("trailing_pre_release_byte_count", _P_U64),
    ("parser_id", _P_TOKEN),
)
_P_FIELD_55_APPLICATION_STOP_AND_PIDFD: Final = _projection_object(
    ("application_task_instance_sha256", _P_SHA256),
    ("pidfd_acquisition_record_sha256", _P_OPTIONAL_SHA256),
    ("stop_signal_id", _P_TOKEN),
    ("stop_state_id", _P_TOKEN),
    ("stop_observed_monotonic_ns", _P_U64),
)
_P_FIELD_56_PRE_RELEASE_STDOUT_DRAINED_EVENT: Final = (
    _projection_object(
        ("event", _P_FULL_EVENT),
    )
)
_P_FIELD_57_PRE_RELEASE_STDOUT_DRAIN: Final = _projection_object(
    ("stdout_read_end_identity_sha256", _P_SHA256),
    ("read_chunk_byte_counts", _P_U64_LIST),
    ("total_drained_byte_count", _P_U64),
    ("terminal_errno_id", _P_TOKEN),
    ("drain_start_monotonic_ns", _P_U64),
    ("drain_end_monotonic_ns", _P_U64),
)
_P_FIELD_58_PRE_RELEASE_STDOUT_BUFFERED_COUNT: Final = (
    _projection_object(
        ("stdout_read_end_identity_sha256", _P_SHA256),
        ("buffered_byte_count", _P_U64),
        ("observation_monotonic_ns", _P_U64),
    )
)
_P_FIELD_59_STAGE1_AND_STAGE2_RELEASE: Final = _projection_object(
    (
        "stage1",
        _projection_object(
            ("event", _P_FULL_EVENT),
            (
                "release_channel_identity_sha256",
                _P_OPTIONAL_SHA256,
            ),
            ("release_payload_hex", _P_OCTETS),
            ("release_write_count", _P_U64),
        ),
    ),
    (
        "stage2",
        _projection_object(
            ("event", _P_FULL_EVENT),
            ("target_task_instance_sha256", _P_OPTIONAL_SHA256),
            ("signal_id", _P_TOKEN),
        ),
    ),
)
_P_FIELD_60_CLONE3_PIDFD_ACQUISITIONS: Final = _projection_object(
    (
        "records",
        _projection_list(
            _projection_object(
                ("task_slot_id", _P_TOKEN),
                ("host_tgid", _P_U64),
                ("kernel_task_instance_sha256", _P_SHA256),
                ("clone_flag_ids", _P_TOKEN_LIST),
                ("exit_signal_id", _P_TOKEN),
                ("pidfd_number", _P_U64),
                (
                    "pidfd_acquisition_record_sha256",
                    _P_OPTIONAL_SHA256,
                ),
                ("monotonic_timestamp_ns", _P_U64),
            )
        ),
    ),
)
_P_FIELD_61_ROLE_PROCESS_IDENTITIES: Final = _projection_object(
    (
        "roles",
        _projection_list(
            _projection_object(
                ("role_id", _P_TOKEN),
                ("task_slot_id", _P_TOKEN),
                (
                    "kernel_task_instance_sha256",
                    _P_OPTIONAL_SHA256,
                ),
                (
                    "pidfd_acquisition_record_sha256",
                    _P_OPTIONAL_SHA256,
                ),
                (
                    "lifecycle_transition_record_sha256",
                    _P_OPTIONAL_SHA256,
                ),
            )
        ),
    ),
)
_P_FIELD_62_PARENTAGE_AND_ADOPTION: Final = _projection_object(
    (
        "relations",
        _projection_list(
            _projection_object(
                ("child_task_slot_id", _P_TOKEN),
                ("parent_task_slot_id", _P_TOKEN),
                ("relation_id", _P_TOKEN),
                ("child_task_instance_sha256", _P_SHA256),
                (
                    "parent_task_instance_sha256",
                    _P_OPTIONAL_SHA256,
                ),
                ("observed_monotonic_timestamp_ns", _P_U64),
            )
        ),
    ),
)
_P_FIELD_63_LAUNCHER_PARENTAGE: Final = _projection_object(
    ("launcher_task_instance_sha256", _P_SHA256),
    ("parent_task_instance_sha256", _P_OPTIONAL_SHA256),
    ("parent_relation_id", _P_TOKEN),
    ("observed_monotonic_timestamp_ns", _P_U64),
)
_P_FIELD_64_LAUNCHER_LIFETIME_AND_EXEC: Final = _projection_object(
    ("kernel_task_instance_sha256", _P_SHA256),
    ("creation_monotonic_ns", _P_U64),
    ("exec_monotonic_ns", _P_U64),
    ("exit_monotonic_ns", _P_U64),
    ("lifecycle_transition_record_sha256", _P_OPTIONAL_SHA256),
    ("exit_observation_record_sha256", _P_OPTIONAL_SHA256),
)
_P_ALIAS_LIFECYCLE_TRANSITION: Final = _projection_object(
    ("kernel_task_instance_sha256", _P_SHA256),
    ("lifecycle_transition_record_sha256", _P_OPTIONAL_SHA256),
    ("predecessor_role_id", _P_TOKEN),
    ("successor_role_id", _P_TOKEN),
)
_P_FIELD_66_SETUP_CHILD_PIDFD_ACQUISITION: Final = _projection_object(
    ("kernel_task_instance_sha256", _P_SHA256),
    ("pidfd_acquisition_method_id", _P_TOKEN),
    ("pidfd_acquisition_record_sha256", _P_OPTIONAL_SHA256),
    ("pidfd_number", _P_U64),
    ("acquisition_monotonic_ns", _P_U64),
)
_P_FIELD_67_SETUP_CHILD_PARENTAGE: Final = _projection_object(
    ("child_task_instance_sha256", _P_SHA256),
    ("parent_task_instance_sha256", _P_OPTIONAL_SHA256),
    ("relation_id", _P_TOKEN),
    ("observed_monotonic_timestamp_ns", _P_U64),
)
_P_FIELD_68_SETUP_CHILD_LIFETIME: Final = _projection_object(
    ("kernel_task_instance_sha256", _P_SHA256),
    ("creation_monotonic_ns", _P_U64),
    ("pid1_transition_monotonic_ns", _P_U64),
    ("exit_monotonic_ns", _P_U64),
    ("lifecycle_transition_record_sha256", _P_OPTIONAL_SHA256),
    ("exit_observation_record_sha256", _P_OPTIONAL_SHA256),
)
_P_FIELD_70_SETUP_CHILD_EXIT_ADOPTION_REAP: Final = (
    _projection_object(
        ("kernel_task_instance_sha256", _P_SHA256),
        ("exit_observation_record_sha256", _P_OPTIONAL_SHA256),
        ("adopter_task_instance_sha256", _P_OPTIONAL_SHA256),
        ("wait_reap_record_sha256", _P_OPTIONAL_SHA256),
        ("wait_status", _P_WAIT_STATUS),
        ("reap_monotonic_timestamp_ns", _P_U64),
    )
)
_P_WAIT_REAP_ROW: Final = _projection_object(
    ("task_slot_id", _P_TOKEN),
    ("kernel_task_instance_sha256", _P_SHA256),
    ("reaper_role_id", _P_TOKEN),
    ("exit_observation_record_sha256", _P_OPTIONAL_SHA256),
    ("wait_reap_record_sha256", _P_OPTIONAL_SHA256),
    ("wait_status", _P_WAIT_STATUS),
    ("reap_monotonic_timestamp_ns", _P_U64),
)
_P_FIELD_71_WAIT_REAP_STATUSES: Final = _projection_object(
    ("records", _projection_list(_P_WAIT_REAP_ROW)),
)
_P_FIELD_72_SUBREAPER_AND_CHILD_INVENTORY: Final = _projection_object(
    ("supervisor_task_instance_sha256", _P_SHA256),
    ("child_subreaper_enabled", _P_BOOL),
    ("set_before_first_child", _P_BOOL),
    ("preexisting_child_count", _P_U64),
    ("adopted_task_slot_ids", _P_TOKEN_LIST),
    ("final_child_count", _P_U64),
)
_P_FIELD_73_SOFT_AND_HARD_RLIMITS: Final = _projection_object(
    (
        "limits",
        _projection_list(
            _projection_object(
                ("resource_id", _P_TOKEN),
                ("soft_value", _P_U64),
                ("hard_value", _P_U64),
            )
        ),
    ),
)
_P_CONTENT_MEMBERSHIP: Final = _projection_object(
    ("path", _P_PATH),
    ("content_sha256", _P_OPTIONAL_SHA256),
    ("rootfs_manifest_sha256", _P_OPTIONAL_SHA256),
    ("manifest_entry_sha256", _P_OPTIONAL_SHA256),
    ("present", _P_BOOL),
)
_P_FIELD_75_INTERPRETER_STAT: Final = _projection_object(
    ("path", _P_PATH),
    ("stat", _P_FULL_STAT),
)
_P_FIELD_76_INTERPRETER_ELF_LINKAGE: Final = _projection_object(
    ("elf_class_id", _P_TOKEN),
    ("machine_id", _P_TOKEN),
    ("pt_interp_path", _P_PATH),
    (
        "dependencies",
        _projection_list(
            _projection_object(
                ("soname_bytes_hex", _P_OCTETS),
                ("resolved_path", _P_PATH),
                ("content_sha256", _P_OPTIONAL_SHA256),
                ("manifest_entry_sha256", _P_OPTIONAL_SHA256),
            )
        ),
    ),
)
_P_FIELD_78_SECCOMP_STATUS_AND_FILTER_COUNT: Final = (
    _projection_object(
        ("seccomp_mode_id", _P_TOKEN),
        ("filter_count", _P_U64),
        ("no_new_privileges", _P_BOOL),
        ("architecture_id", _P_TOKEN),
    )
)
_P_FIELD_79_SUPERVISOR_LOADER_RESOLUTION: Final = (
    _projection_object(
        ("loader_path", _P_PATH),
        (
            "resolved_objects",
            _projection_list(
                _projection_object(
                    ("soname_bytes_hex", _P_OCTETS),
                    ("resolved_path", _P_PATH),
                    ("stat", _P_FULL_STAT),
                    ("content_sha256", _P_OPTIONAL_SHA256),
                )
            ),
        ),
        ("closure_sha256", _P_SHA256),
    )
)
_P_FIELD_80_SUPERVISOR_EXECUTABLE_STAT: Final = _projection_object(
    ("resolved_path", _P_PATH),
    ("stat", _P_FULL_STAT),
)
_P_FIELD_81_TEARDOWN_DEADLINES: Final = _projection_object(
    ("clock_id", _P_TOKEN),
    ("cleanup_branch_id", _P_TOKEN),
    ("teardown_started_ns", _P_U64),
    ("term_grace_deadline_ns", _P_U64),
    ("pidfd_exit_deadline_ns", _P_U64),
    ("monitor_first_deadline_ns", _P_U64),
    ("monitor_second_deadline_ns", _P_U64),
    ("cgroup_quiescence_deadline_ns", _P_U64),
    ("stream_eof_deadline_ns", _P_U64),
    ("emergency_entered", _P_BOOL),
)
_P_FIELD_82_MONITOR_AND_DESCENDANT_WAIT_REAP: Final = (
    _projection_object(
        ("records", _projection_list(_P_WAIT_REAP_ROW)),
    )
)
_P_FIELD_83_CGROUP_FINAL_INVENTORY: Final = _projection_object(
    ("leaf_identity_sha256", _P_SHA256),
    ("populated", _P_BOOL),
    ("member_count", _P_U64),
    (
        "members",
        _projection_list(
            _projection_object(
                ("role_id", _P_TOKEN),
                ("kernel_task_instance_sha256", _P_SHA256),
            )
        ),
    ),
)
_P_FIELD_84_STREAM_EOF_AND_DRAIN: Final = _projection_object(
    (
        "streams",
        _projection_list(
            _projection_object(
                ("fd_role_id", _P_TOKEN),
                ("peer_identity_sha256", _P_OPTIONAL_SHA256),
                ("completion_status_id", _P_TOKEN),
                ("terminal_errno_id", _P_TOKEN),
                ("completion_evidence_sha256", _P_OPTIONAL_SHA256),
                ("drained_byte_count", _P_U64),
                ("deadline_ns", _P_U64),
                ("completed_ns", _P_U64),
            )
        ),
    ),
)

_PROJECTION_SCHEMA_GROUPS: Final = (
    (
        _P_FIELD_01_CWD_MOUNT_AND_INODE,
        ("cwd-mount-and-inode-record",),
    ),
    (
        _P_FIELD_02_UMASK_OCTAL,
        ("umask-octal-record",),
    ),
    (
        _P_FIELD_03_BACKEND_MEMFD_STAT,
        ("backend-memfd-stat-record",),
    ),
    (
        _P_FIELD_04_BACKEND_MEMFD_FLAGS,
        ("backend-memfd-flags-record",),
    ),
    (
        _P_FIELD_05_BACKEND_MEMFD_SEALS,
        ("backend-memfd-seals-record",),
    ),
    (
        _P_FIELD_06_BACKEND_ELF_PROGRAM_HEADERS,
        ("backend-elf-program-header-record",),
    ),
    (
        _P_FIELD_07_BACKEND_ELF_DYNAMIC,
        ("backend-elf-dynamic-section-record",),
    ),
    (
        _P_FIELD_08_CAPABILITY_SET,
        ("capability-set-record",),
    ),
    (
        _P_FIELD_09_SECUREBITS_MASK,
        ("securebits-mask-record",),
    ),
    (
        _P_FIELD_10_DUMPABLE,
        ("dumpable-record",),
    ),
    (
        _P_FIELD_11_UID_GID_AND_GROUPS,
        ("uid-gid-and-groups-record",),
    ),
    (
        _P_FIELD_12_CGROUP_PROCESS_MEMBERSHIP,
        ("cgroup-process-membership-record",),
    ),
    (
        _P_FIELD_13_CGROUP_LEAF_STAT,
        ("cgroup-leaf-stat-record",),
    ),
    (
        _P_FIELD_14_CGROUP_LEAF_OWNER,
        ("cgroup-leaf-owner-record",),
    ),
    (
        _P_FIELD_15_CGROUP_DELEGATION,
        ("cgroup-delegation-record",),
    ),
    (
        _P_FIELD_16_APPLICATION_FD_INVENTORY,
        ("application-fd-inventory-record",),
    ),
    (
        _P_FIELD_17_FD_KERNEL_OBJECT_STATS,
        ("fd-kernel-object-stat-records",),
    ),
    (
        _P_FIELD_18_FD_ACCESS_FLAGS_AND_OFFSETS,
        ("fd-access-flags-and-offset-records",),
    ),
    (
        _P_FIELD_19_FD_CLOEXEC_AND_INHERITANCE,
        ("fd-cloexec-and-inheritance-records",),
    ),
    (
        _P_FIELD_20_STDIO_ISATTY,
        ("stdio-isatty-records",),
    ),
    (
        _P_FIELD_21_SUPERVISOR_PEER_CUSTODY,
        ("supervisor-peer-custody-records",),
    ),
    (
        _P_FIELD_22_NAMESPACE_PARENT_CHAIN,
        ("namespace-inode-parent-chain-record",),
    ),
    (
        _P_FIELD_23_HOST_VIEW_FINAL_MAP,
        ("host-view-final-uid-gid-map-record",),
    ),
    (
        _P_FIELD_24_INTERMEDIATE_VIEW_MAPS,
        ("intermediate-view-map-records",),
    ),
    (
        _P_FIELD_25_SETGROUPS_STATE,
        ("setgroups-state-records",),
    ),
    (
        _P_FIELD_26_APPLICATION_SUPPLEMENTARY_GROUP,
        ("application-supplementary-group-record",),
    ),
    (
        _P_FIELD_27_OBSERVER_ADOPTION_AND_REAP,
        ("observer-adoption-and-reap-record",),
    ),
    (
        _P_FIELD_28_ROOT_MOUNT_STAT_AND_FLAGS,
        ("root-mount-stat-and-flags-record",),
    ),
    (
        _P_FIELD_29_OLD_ROOT_HANDLE_ABSENCE,
        ("old-root-handle-absence-record",),
    ),
    (
        _P_FIELD_30_LANDLOCK_QUERIED_ABI,
        ("landlock-queried-abi-record",),
    ),
    (
        _P_FIELD_31_LANDLOCK_INSTALL_RETURN,
        ("landlock-install-return-record",),
    ),
    (
        _P_FIELD_32_ARCHITECTURE,
        ("architecture-record",),
    ),
    (
        _P_FIELD_33_KERNEL_RELEASE_AND_BUILD,
        ("kernel-release-and-build-record",),
    ),
    (
        _P_FIELD_34_LINUX_SECURITY_FEATURE_PROBE,
        ("linux-security-feature-probe-record",),
    ),
    (
        _P_FIELD_35_CANONICAL_MOUNTINFO,
        ("canonical-mountinfo-record",),
    ),
    (
        _P_FIELD_36_MOUNT_PROPAGATION,
        ("mount-propagation-record",),
    ),
    (
        _P_FIELD_37_WRITABLE_PATH_INVENTORY,
        ("writable-path-inventory-record",),
    ),
    (
        _P_FIELD_38_DEVICE_MOUNT_FLAGS,
        ("device-mount-flags-record",),
    ),
    (
        _P_FIELD_39_FORBIDDEN_MOUNT_TYPE_ABSENCE,
        ("forbidden-mount-type-absence-record",),
    ),
    (
        _P_FIELD_40_APPLICATION_NAMESPACE_INODES,
        ("application-namespace-inode-records",),
    ),
    (
        _P_FIELD_41_HOST_NAMESPACE_INODES,
        ("host-namespace-inode-records",),
    ),
    (
        _P_FIELD_42_NAMESPACE_PARENTAGE,
        ("namespace-parentage-record",),
    ),
    (
        _P_FIELD_43_NETWORK_INTERFACE,
        ("network-interface-record",),
    ),
    (
        _P_FIELD_44_IPV4_ROUTE,
        ("ipv4-route-record",),
    ),
    (
        _P_FIELD_45_IPV6_ROUTE,
        ("ipv6-route-record",),
    ),
    (
        _P_FIELD_46_NETWORK_NAMESPACE_INODE,
        ("network-namespace-inode-record",),
    ),
    (
        _P_FIELD_47_NO_NEW_PRIVILEGES,
        ("no-new-privileges-status-record",),
    ),
    (
        _P_FIELD_48_GETRANDOM_CALL,
        ("getrandom-call-record",),
    ),
    (
        _P_FIELD_49_NONCE_REGISTRY_INSERTION,
        ("nonce-registry-insertion-record",),
    ),
    (
        _P_FIELD_50_RUN_SEQUENCE,
        ("run-sequence-record",),
    ),
    (
        _P_FIELD_51_BUBBLEWRAP_CHILD_PID_STATUS,
        ("bubblewrap-child-pid-status-record",),
    ),
    (
        _P_FIELD_52_STAGE1_BARRIER_PIPE_IDENTITY,
        ("stage1-barrier-pipe-kernel-object-identity-record",),
    ),
    (
        _P_FIELD_53_PIDFD_BOUND_STAGE1_BARRIER_BLOCK,
        ("pidfd-bound-stage1-barrier-read-block-record",),
    ),
    (
        _P_FIELD_54_READY_FRAME_BYTES_AND_CHUNKS,
        ("ready-frame-bytes-and-chunk-record",),
    ),
    (
        _P_FIELD_55_APPLICATION_STOP_AND_PIDFD,
        ("application-stop-and-pidfd-record",),
    ),
    (
        _P_FIELD_56_PRE_RELEASE_STDOUT_DRAINED_EVENT,
        ("PRE_RELEASE_STDOUT_DRAINED-event-record",),
    ),
    (
        _P_FIELD_57_PRE_RELEASE_STDOUT_DRAIN,
        ("pre-release-stdout-drain-to-eagain-record",),
    ),
    (
        _P_FIELD_58_PRE_RELEASE_STDOUT_BUFFERED_COUNT,
        ("pre-release-stdout-buffered-byte-count-zero-record",),
    ),
    (
        _P_FIELD_59_STAGE1_AND_STAGE2_RELEASE,
        ("stage1-and-stage2-release-record",),
    ),
    (
        _P_FIELD_60_CLONE3_PIDFD_ACQUISITIONS,
        ("clone3-pidfd-acquisition-records",),
    ),
    (
        _P_FIELD_61_ROLE_PROCESS_IDENTITIES,
        ("role-process-identity-records",),
    ),
    (
        _P_FIELD_62_PARENTAGE_AND_ADOPTION,
        ("parentage-and-adoption-records",),
    ),
    (
        _P_FIELD_63_LAUNCHER_PARENTAGE,
        ("unprivileged-preexec-launcher-parentage-record",),
    ),
    (
        _P_FIELD_64_LAUNCHER_LIFETIME_AND_EXEC,
        (
            (
                "unprivileged-preexec-launcher-lifetime-and-exec-"
                "transition-record"
            ),
        ),
    ),
    (
        _P_ALIAS_LIFECYCLE_TRANSITION,
        (
            (
                "unprivileged-preexec-launcher-to-monitor-same-pid-"
                "exec-and-reap-record"
            ),
        ),
    ),
    (
        _P_FIELD_66_SETUP_CHILD_PIDFD_ACQUISITION,
        ("bubblewrap-setup-child-pidfd-acquisition-record",),
    ),
    (
        _P_FIELD_67_SETUP_CHILD_PARENTAGE,
        ("bubblewrap-setup-child-parentage-record",),
    ),
    (
        _P_FIELD_68_SETUP_CHILD_LIFETIME,
        ("bubblewrap-setup-child-lifetime-record",),
    ),
    (
        _P_ALIAS_LIFECYCLE_TRANSITION,
        (
            (
                "bubblewrap-setup-child-to-sandbox-pid1-same-host-"
                "pid-lifecycle-transition-record"
            ),
        ),
    ),
    (
        _P_FIELD_70_SETUP_CHILD_EXIT_ADOPTION_REAP,
        ("bubblewrap-setup-child-exit-adoption-and-reap-record",),
    ),
    (
        _P_FIELD_71_WAIT_REAP_STATUSES,
        ("wait-reap-status-records",),
    ),
    (
        _P_FIELD_72_SUBREAPER_AND_CHILD_INVENTORY,
        ("subreaper-setting-and-child-inventory-record",),
    ),
    (
        _P_FIELD_73_SOFT_AND_HARD_RLIMITS,
        ("soft-and-hard-rlimit-records",),
    ),
    (
        _P_CONTENT_MEMBERSHIP,
        ("bootstrap-rootfs-membership-record",),
    ),
    (
        _P_FIELD_75_INTERPRETER_STAT,
        ("interpreter-stat-record",),
    ),
    (
        _P_FIELD_76_INTERPRETER_ELF_LINKAGE,
        ("interpreter-elf-linkage-record",),
    ),
    (
        _P_CONTENT_MEMBERSHIP,
        ("interpreter-rootfs-membership-record",),
    ),
    (
        _P_FIELD_78_SECCOMP_STATUS_AND_FILTER_COUNT,
        ("seccomp-status-and-filter-count-record",),
    ),
    (
        _P_FIELD_79_SUPERVISOR_LOADER_RESOLUTION,
        ("supervisor-loader-resolution-record",),
    ),
    (
        _P_FIELD_80_SUPERVISOR_EXECUTABLE_STAT,
        ("supervisor-executable-stat-record",),
    ),
    (
        _P_FIELD_81_TEARDOWN_DEADLINES,
        ("teardown-monotonic-deadline-records",),
    ),
    (
        _P_FIELD_82_MONITOR_AND_DESCENDANT_WAIT_REAP,
        ("monitor-and-descendant-wait-reap-records",),
    ),
    (
        _P_FIELD_83_CGROUP_FINAL_INVENTORY,
        ("cgroup-process-final-inventory",),
    ),
    (
        _P_FIELD_84_STREAM_EOF_AND_DRAIN,
        ("stream-eof-and-drain-records",),
    ),
)


def _build_projection_schema_registry() -> Mapping[str, _ProjectionSchemaNode]:
    result: Dict[str, _ProjectionSchemaNode] = {}
    for node, field_ids in _PROJECTION_SCHEMA_GROUPS:
        for field_id in field_ids:
            if field_id in result:
                _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)
            result[field_id] = node
    return MappingProxyType(result)


_PROJECTION_VALUE_SCHEMA_BY_FIELD: Final = (
    _build_projection_schema_registry()
)
LINUX_CONFINEMENT_CANONICAL_JSON_PROJECTION_FIELD_IDS: Final = tuple(
    sorted(_PROJECTION_VALUE_SCHEMA_BY_FIELD)
)


def _projection_schema_id(field_id: str) -> str:
    if field_id not in _PROJECTION_VALUE_SCHEMA_BY_FIELD:
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    return LINUX_CONFINEMENT_PROJECTION_SCHEMA_ID_PREFIX + field_id + ".v1"


def _projection_occurrence_schema(
    *,
    observation_id: str,
    field_id: str,
) -> _ObservationSchema:
    schema = _observation_schema(observation_id)
    if (
        field_id not in schema.raw_evidence_field_ids
        or field_id not in _PROJECTION_VALUE_SCHEMA_BY_FIELD
        or _field_codec_id(field_id)
        != LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    return schema


def _validate_projection_node(
    node: _ProjectionSchemaNode,
    value: object,
) -> None:
    kind_id = node.node_kind_id
    if kind_id == "boolean":
        if type(value) is not bool:
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        return
    if kind_id == "sha256":
        _sha256_token(value)
        return
    if kind_id == "optional-sha256":
        if type(value) is not str:
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        if value:
            _sha256_token(value, allow_zero=True)
        return
    if kind_id == "token":
        if type(value) is not str:
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        if (
            len(_ascii(value))
            > MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_TOKEN_BYTES
        ):
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
        return
    if kind_id == "u64":
        _u64(value)
        return
    if kind_id in ("octets", "path"):
        if type(value) is not str:
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        if len(value) > MAXIMUM_LINUX_CONFINEMENT_JSON_STRING_BYTES:
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
        if (
            len(value) % 2
            or value != value.lower()
            or any(
                character not in "0123456789abcdef"
                for character in value
            )
        ):
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        return
    if kind_id == "list":
        if type(value) is not list:
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        for item in value:
            _validate_projection_node(node.item_schema, item)
        return
    if kind_id != "object" or type(value) is not dict:
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    expected = tuple(row[0] for row in node.field_rows)
    _exact_keys(value, expected)
    for field_id, child in node.field_rows:
        _validate_projection_node(child, value[field_id])


def _validate_canonical_projection(
    field_id: str,
    projection: dict,
) -> None:
    if type(projection) is not dict:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    _exact_keys(projection, _PROJECTION_FIELD_IDS)
    schema = _projection_occurrence_schema(
        observation_id=projection["observation_id"],
        field_id=field_id,
    )
    if (
        projection["field_id"] != field_id
        or projection["projection_schema_id"]
        != _projection_schema_id(field_id)
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    for name in (
        "process_identity_snapshot_sha256",
        "staging_run_binding_sha256",
        "subject_identity_table_sha256",
    ):
        _sha256_token(projection[name])
    if type(projection["source_observation_available"]) is not bool:
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    for name in (
        "source_errno_id",
        "source_observation_status_id",
    ):
        if type(projection[name]) is not str:
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        if (
            len(_ascii(projection[name]))
            > MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_TOKEN_BYTES
        ):
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
    refs = projection["subject_identity_refs"]
    if type(refs) is not list or len(refs) != len(schema.subject_role_ids):
        _fail(LinuxConfinementSemanticPayloadCode.ORDER_INVALID)
    for index, ref in enumerate(refs):
        _exact_keys(ref, _PROJECTION_SUBJECT_REF_FIELD_IDS)
        if ref["subject_role_id"] != schema.subject_role_ids[index]:
            _fail(LinuxConfinementSemanticPayloadCode.ORDER_INVALID)
        _sha256_token(ref["subject_identity_sha256"])
    _validate_projection_node(
        _PROJECTION_VALUE_SCHEMA_BY_FIELD[field_id],
        projection["values"],
    )
    if field_id in _ALIAS_TRANSITION_ROLE_IDS:
        predecessor, successor = _ALIAS_TRANSITION_ROLE_IDS[field_id]
        values = projection["values"]
        if (
            values["predecessor_role_id"] != predecessor
            or values["successor_role_id"] != successor
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


def _projection_node_tree(node: _ProjectionSchemaNode) -> dict:
    if node.node_kind_id == "list":
        return {
            "item_schema": _projection_node_tree(node.item_schema),
            "node_kind_id": node.node_kind_id,
        }
    if node.node_kind_id != "object":
        return {"node_kind_id": node.node_kind_id}
    return {
        "field_rows": [
            {
                "field_id": field_id,
                "schema": _projection_node_tree(child),
            }
            for field_id, child in node.field_rows
        ],
        "node_kind_id": node.node_kind_id,
    }


def _projection_schema_registry_tree() -> list:
    occurrences_by_field: Dict[str, list] = {
        field_id: []
        for field_id in (
            LINUX_CONFINEMENT_CANONICAL_JSON_PROJECTION_FIELD_IDS
        )
    }
    for schema in _OBSERVATION_SCHEMAS:
        for field_id in schema.raw_evidence_field_ids:
            if field_id in occurrences_by_field:
                occurrences_by_field[field_id].append(schema.observation_id)
    return [
        {
            "field_id": field_id,
            "observation_ids": occurrences_by_field[field_id],
            "projection_schema_id": _projection_schema_id(field_id),
            "semantic_coverage_id": (
                "substantive-field-specific-typed-values-v1"
            ),
            "values_schema": _projection_node_tree(
                _PROJECTION_VALUE_SCHEMA_BY_FIELD[field_id]
            ),
        }
        for field_id in (
            LINUX_CONFINEMENT_CANONICAL_JSON_PROJECTION_FIELD_IDS
        )
    ]


def linux_confinement_evidence_field_parser_id(field_id: str) -> str:
    if (
        _field_codec_id(field_id)
        != LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT
    ):
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    return (
        "heterodiff.adapter.linux-evidence-parser."
        + field_id
        + ".v1"
    )


def build_linux_confinement_canonical_record_value(
    *,
    field_id: str,
    raw_source_bytes: bytes,
    canonical_projection: dict,
) -> bytes:
    """Bind one supplied native record to one supplied projection.

    The projection is not recomputed here; a later native/domain parser must
    establish that relation.  The two representations cannot silently drift
    within the portable envelope because their exact identities are retained.
    """

    parser_id = linux_confinement_evidence_field_parser_id(field_id)
    if (
        type(raw_source_bytes) is not bytes
        or not raw_source_bytes
        or type(canonical_projection) is not dict
        or not canonical_projection
    ):
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    if (
        len(raw_source_bytes)
        > MAXIMUM_LINUX_CONFINEMENT_RECORD_RAW_SOURCE_BYTES
    ):
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
    _validate_canonical_projection(field_id, canonical_projection)
    projection_bytes = _canonical_json(
        canonical_projection,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RECORD_PROJECTION_BYTES,
    )
    result = _canonical_json(
        {
            "canonical_projection": canonical_projection,
            "canonical_projection_sha256": _domain_sha256(
                linux_confinement_evidence_field_semantic_type_id(
                    field_id
                ),
                projection_bytes,
            ),
            "field_id": field_id,
            "native_origin_authenticated": False,
            "parser_id": parser_id,
            "portable_projection_recomputed": False,
            "raw_source_byte_count": len(raw_source_bytes),
            "raw_source_hex": raw_source_bytes.hex(),
            "raw_source_plain_sha256": _plain_sha256(raw_source_bytes),
            "schema_version": "1",
        },
        maximum=MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES,
    )
    _validate_canonical_record_value(field_id, result)
    return result


def _validate_canonical_record_value(
    field_id: str,
    value: bytes,
) -> dict:
    tree = _parse_canonical_json(
        value,
        maximum=MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES,
    )
    _exact_keys(tree, _RECORD_ENVELOPE_FIELD_IDS)
    projection = tree["canonical_projection"]
    if type(projection) is not dict or not projection:
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    raw = _decoded_hex(
        tree["raw_source_hex"],
        maximum=MAXIMUM_LINUX_CONFINEMENT_RECORD_RAW_SOURCE_BYTES,
    )
    projection_bytes = _canonical_json(
        projection,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RECORD_PROJECTION_BYTES,
    )
    if (
        not raw
        or tree["field_id"] != field_id
        or tree["schema_version"] != "1"
        or tree["parser_id"]
        != linux_confinement_evidence_field_parser_id(field_id)
        or tree["native_origin_authenticated"] is not False
        or tree["portable_projection_recomputed"] is not False
        or tree["raw_source_byte_count"] != len(raw)
        or tree["raw_source_plain_sha256"] != _plain_sha256(raw)
        or tree["canonical_projection_sha256"]
        != _domain_sha256(
            linux_confinement_evidence_field_semantic_type_id(field_id),
            projection_bytes,
        )
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    _validate_canonical_projection(field_id, projection)
    return tree


def _validate_evidence_value(field_id: str, value: bytes) -> None:
    if type(value) is not bytes:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    if len(value) > MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
    codec = _field_codec_id(field_id)
    if codec == LINUX_CONFINEMENT_CODEC_SHA256_HEX_ASCII:
        try:
            decoded = value.decode("ascii", "strict")
        except UnicodeError:
            _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
        _sha256_token(decoded)
    elif codec == LINUX_CONFINEMENT_CODEC_U64BE:
        if len(value) != 8:
            _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
        _u64(int.from_bytes(value, "big"))
    elif codec == LINUX_CONFINEMENT_CODEC_NUL_FRAME:
        _validate_nul_frame(field_id, value)
    elif codec == LINUX_CONFINEMENT_CODEC_BOUNDED_OCTETS:
        if not value:
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    elif codec == LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT:
        _validate_canonical_record_value(field_id, value)
    else:
        _fail(LinuxConfinementSemanticPayloadCode.INTERNAL)


def _identity_schema_id(subject_role_id: str) -> str:
    kind_id = _SUBJECT_KIND_BY_ROLE[subject_role_id]
    prefix = (
        "process-snapshot-reference"
        if kind_id == "process-role"
        else "declared-resource-identity"
    )
    return (
        "heterodiff.adapter.linux-confinement."
        + prefix
        + "."
        + subject_role_id
        + ".v1"
    )


_RESOURCE_IDENTITY_FIELD_IDS: Final = (
    "identity_components",
    "identity_schema_id",
    "linux_boot_id_sha256",
    "native_origin_authenticated",
    "process_identity_snapshot_sha256",
    "resource_role_id",
    "schema_version",
    "staging_run_binding_sha256",
    "subject_identity_table_sha256",
)


def _validate_resource_identity_components(
    subject_role_id: str,
    identity_components: dict,
) -> None:
    kind_id = _SUBJECT_KIND_BY_ROLE[subject_role_id]
    expected_fields = _RESOURCE_COMPONENT_FIELDS_BY_KIND[kind_id]
    _exact_keys(identity_components, expected_fields)
    if kind_id == "namespace":
        if (
            identity_components["namespace_type_id"]
            != _NAMESPACE_TYPE_BY_ROLE[subject_role_id]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
        for name in ("device", "inode", "owner_user_namespace_inode"):
            _u64(identity_components[name], positive=True)
        _sha256_token(identity_components["observation_record_sha256"])
    elif kind_id == "kernel-object":
        if (
            identity_components["kernel_object_type_id"]
            != _KERNEL_OBJECT_TYPE_BY_ROLE[subject_role_id]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
        for name in ("device", "generation", "inode"):
            _u64(identity_components[name], positive=True)
        _sha256_token(identity_components["observation_record_sha256"])
    elif kind_id == "content-artifact":
        _u64(identity_components["byte_count"], positive=True)
        for name in (
            "content_sha256",
            "custody_record_sha256",
            "manifest_membership_sha256",
        ):
            _sha256_token(identity_components[name])
    elif kind_id == "security-policy-object":
        if (
            identity_components["security_object_type_id"]
            != _SECURITY_OBJECT_TYPE_BY_ROLE[subject_role_id]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
        for name in (
            "content_sha256",
            "feature_manifest_sha256",
            "install_or_custody_record_sha256",
        ):
            _sha256_token(identity_components[name])
    elif kind_id == "platform":
        _token(identity_components["architecture_id"])
        for name in (
            "linux_boot_id_sha256",
            "observation_record_sha256",
            "platform_profile_sha256",
        ):
            _sha256_token(identity_components[name])
    elif kind_id == "process-set":
        _u64(identity_components["member_count"])
        for name in (
            "completeness_authority_record_sha256",
            "membership_sha256",
            "observation_record_sha256",
        ):
            _sha256_token(identity_components[name])
    else:
        _fail(LinuxConfinementSemanticPayloadCode.INTERNAL)


def build_linux_confinement_resource_subject_identity_bytes(
    *,
    subject_role_id: str,
    identity_components: dict,
    staging_run_binding_sha256: str,
    subject_identity_table_sha256: str,
    process_identity_snapshot_sha256: str,
    linux_boot_id_sha256: str,
) -> bytes:
    if (
        type(subject_role_id) is not str
        or subject_role_id not in _SUBJECT_KIND_BY_ROLE
        or _SUBJECT_KIND_BY_ROLE[subject_role_id] == "process-role"
        or type(identity_components) is not dict
        or not identity_components
    ):
        _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
    for digest in (
        staging_run_binding_sha256,
        subject_identity_table_sha256,
        process_identity_snapshot_sha256,
        linux_boot_id_sha256,
    ):
        _sha256_token(digest)
    _validate_resource_identity_components(
        subject_role_id,
        identity_components,
    )
    return _canonical_json(
        {
            "identity_components": identity_components,
            "identity_schema_id": _identity_schema_id(subject_role_id),
            "linux_boot_id_sha256": linux_boot_id_sha256,
            "native_origin_authenticated": False,
            "process_identity_snapshot_sha256": (
                process_identity_snapshot_sha256
            ),
            "resource_role_id": subject_role_id,
            "schema_version": "1",
            "staging_run_binding_sha256": staging_run_binding_sha256,
            "subject_identity_table_sha256": (
                subject_identity_table_sha256
            ),
        },
        maximum=MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES,
    )


def _validate_resource_subject_identity(
    subject_role_id: str,
    value: bytes,
) -> dict:
    tree = _parse_canonical_json(
        value,
        maximum=MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES,
    )
    _exact_keys(tree, _RESOURCE_IDENTITY_FIELD_IDS)
    if (
        tree["resource_role_id"] != subject_role_id
        or tree["identity_schema_id"] != _identity_schema_id(subject_role_id)
        or tree["schema_version"] != "1"
        or tree["native_origin_authenticated"] is not False
        or type(tree["identity_components"]) is not dict
        or not tree["identity_components"]
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    for name in (
        "linux_boot_id_sha256",
        "process_identity_snapshot_sha256",
        "staging_run_binding_sha256",
        "subject_identity_table_sha256",
    ):
        _sha256_token(tree[name])
    _validate_resource_identity_components(
        subject_role_id,
        tree["identity_components"],
    )
    return tree


@dataclass(frozen=True)
class LinuxConfinementSubjectBindingV1:
    """One typed supplied subject reference in plan-declared role order."""

    subject_role_id: str
    canonical_identity_bytes: bytes
    staging_run_binding_sha256: str
    subject_identity_table_sha256: str
    process_identity_snapshot_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementSubjectBindingV1:
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
        if (
            type(self.subject_role_id) is not str
            or self.subject_role_id not in _SUBJECT_KIND_BY_ROLE
        ):
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        for digest in (
            self.staging_run_binding_sha256,
            self.subject_identity_table_sha256,
            self.process_identity_snapshot_sha256,
        ):
            _sha256_token(digest)
        if (
            type(self.canonical_identity_bytes) is not bytes
            or not self.canonical_identity_bytes
            or len(self.canonical_identity_bytes)
            > MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES
        ):
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
        if (
            _SUBJECT_KIND_BY_ROLE[self.subject_role_id]
            == "process-role"
        ):
            try:
                digest = self.canonical_identity_bytes.decode(
                    "ascii",
                    "strict",
                )
            except UnicodeError:
                _fail(
                    LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID
                )
            _sha256_token(digest)
        else:
            resource = _validate_resource_subject_identity(
                self.subject_role_id,
                self.canonical_identity_bytes,
            )
            if (
                resource["staging_run_binding_sha256"]
                != self.staging_run_binding_sha256
                or resource["subject_identity_table_sha256"]
                != self.subject_identity_table_sha256
                or resource["process_identity_snapshot_sha256"]
                != self.process_identity_snapshot_sha256
            ):
                _fail(
                    LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                )


def _validated_subject_binding(
    value: LinuxConfinementSubjectBindingV1,
) -> None:
    _validated_exact_dataclass_post_init(
        value,
        LinuxConfinementSubjectBindingV1,
    )


def _subject_binding_tree(
    value: LinuxConfinementSubjectBindingV1,
) -> dict:
    _validated_subject_binding(value)
    schema_id = _identity_schema_id(value.subject_role_id)
    raw = value.canonical_identity_bytes
    return {
        "artifact_type": LINUX_CONFINEMENT_SUBJECT_BINDING_ARTIFACT_TYPE,
        "canonical_identity_hex": raw.hex(),
        "format_version": "1",
        "identity_byte_count": len(raw),
        "identity_plain_sha256": _plain_sha256(raw),
        "identity_schema_id": schema_id,
        "identity_sha256": _domain_sha256(schema_id, raw),
        "origin_authenticated": False,
        "process_identity_snapshot_sha256": (
            value.process_identity_snapshot_sha256
        ),
        "staging_run_binding_sha256": (
            value.staging_run_binding_sha256
        ),
        "subject_kind_id": _SUBJECT_KIND_BY_ROLE[value.subject_role_id],
        "subject_identity_table_sha256": (
            value.subject_identity_table_sha256
        ),
        "subject_role_id": value.subject_role_id,
    }


@dataclass(frozen=True)
class LinuxConfinementEvidenceMemberV1:
    """One fixed raw-evidence field with a profile-derived value codec."""

    field_id: str
    canonical_value_bytes: bytes
    staging_run_binding_sha256: str
    subject_identity_table_sha256: str
    process_identity_snapshot_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementEvidenceMemberV1:
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
        if (
            type(self.field_id) is not str
            or self.field_id not in LINUX_CONFINEMENT_RAW_EVIDENCE_FIELD_IDS
        ):
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        for digest in (
            self.staging_run_binding_sha256,
            self.subject_identity_table_sha256,
            self.process_identity_snapshot_sha256,
        ):
            _sha256_token(digest)
        _validate_evidence_value(
            self.field_id,
            self.canonical_value_bytes,
        )


def _validated_evidence_member(
    value: LinuxConfinementEvidenceMemberV1,
) -> None:
    _validated_exact_dataclass_post_init(
        value,
        LinuxConfinementEvidenceMemberV1,
    )


def _evidence_member_tree(
    value: LinuxConfinementEvidenceMemberV1,
) -> dict:
    _validated_evidence_member(value)
    semantic_type_id = linux_confinement_evidence_field_semantic_type_id(
        value.field_id
    )
    raw = value.canonical_value_bytes
    return {
        "artifact_type": LINUX_CONFINEMENT_EVIDENCE_MEMBER_ARTIFACT_TYPE,
        "canonical_value_hex": raw.hex(),
        "comparator_id": _field_comparator_id(value.field_id),
        "field_id": value.field_id,
        "format_version": "1",
        "process_identity_snapshot_sha256": (
            value.process_identity_snapshot_sha256
        ),
        "semantic_type_id": semantic_type_id,
        "staging_run_binding_sha256": (
            value.staging_run_binding_sha256
        ),
        "subject_identity_table_sha256": (
            value.subject_identity_table_sha256
        ),
        "value_byte_count": len(raw),
        "value_codec_id": _field_codec_id(value.field_id),
        "value_plain_sha256": _plain_sha256(raw),
        "value_sha256": _domain_sha256(semantic_type_id, raw),
    }


@dataclass(frozen=True)
class LinuxConfinementObservationPayloadV1:
    """One closed observation payload without a caller-supplied pass bit."""

    observation_id: str
    staging_run_binding_sha256: str
    subject_identity_table_sha256: str
    process_identity_snapshot_sha256: str
    capture_window_start_monotonic_ns: int
    capture_window_end_monotonic_ns: int
    subject_bindings: Tuple[LinuxConfinementSubjectBindingV1, ...]
    evidence_members: Tuple[LinuxConfinementEvidenceMemberV1, ...]

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementObservationPayloadV1:
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
        schema = _observation_schema(self.observation_id)
        for value in (
            self.staging_run_binding_sha256,
            self.subject_identity_table_sha256,
            self.process_identity_snapshot_sha256,
        ):
            _sha256_token(value)
        _u64(self.capture_window_start_monotonic_ns, positive=True)
        _u64(self.capture_window_end_monotonic_ns, positive=True)
        if (
            self.capture_window_start_monotonic_ns
            > self.capture_window_end_monotonic_ns
        ):
            _fail(LinuxConfinementSemanticPayloadCode.VALUE_INVALID)
        if (
            type(self.subject_bindings) is not tuple
            or any(
                type(item) is not LinuxConfinementSubjectBindingV1
                for item in self.subject_bindings
            )
            or tuple(
                item.subject_role_id for item in self.subject_bindings
            )
            != schema.subject_role_ids
        ):
            _fail(LinuxConfinementSemanticPayloadCode.ORDER_INVALID)
        if (
            type(self.evidence_members) is not tuple
            or any(
                type(item) is not LinuxConfinementEvidenceMemberV1
                for item in self.evidence_members
            )
            or tuple(item.field_id for item in self.evidence_members)
            != schema.raw_evidence_field_ids
        ):
            _fail(LinuxConfinementSemanticPayloadCode.ORDER_INVALID)
        for item in self.subject_bindings:
            _validated_subject_binding(item)
            if (
                item.staging_run_binding_sha256
                != self.staging_run_binding_sha256
                or item.subject_identity_table_sha256
                != self.subject_identity_table_sha256
                or item.process_identity_snapshot_sha256
                != self.process_identity_snapshot_sha256
            ):
                _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
        for item in self.evidence_members:
            _validated_evidence_member(item)
            if (
                item.staging_run_binding_sha256
                != self.staging_run_binding_sha256
                or item.subject_identity_table_sha256
                != self.subject_identity_table_sha256
                or item.process_identity_snapshot_sha256
                != self.process_identity_snapshot_sha256
            ):
                _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


def _validated_observation_payload(
    value: LinuxConfinementObservationPayloadV1,
) -> None:
    _validated_exact_dataclass_post_init(
        value,
        LinuxConfinementObservationPayloadV1,
    )


def _observation_payload_tree(
    value: LinuxConfinementObservationPayloadV1,
) -> dict:
    _validated_observation_payload(value)
    schema = _observation_schema(value.observation_id)
    artifact_type = linux_confinement_observation_payload_artifact_type(
        value.observation_id
    )
    return {
        "artifact_type": artifact_type,
        "capture_window_end_monotonic_ns": (
            value.capture_window_end_monotonic_ns
        ),
        "capture_window_start_monotonic_ns": (
            value.capture_window_start_monotonic_ns
        ),
        "evidence_members": [
            _evidence_member_tree(item) for item in value.evidence_members
        ],
        "family_id": schema.family_id,
        "format_version": "1",
        "lifecycle_stage_id": schema.lifecycle_stage_id,
        "nonclaims": _false_nonclaims(),
        "observation_id": value.observation_id,
        "predicate_evaluation_status_id": (
            LINUX_CONFINEMENT_PREDICATE_EVALUATION_STATUS
        ),
        "predicate_id": schema.predicate_id,
        "procedure_id": schema.procedure_id,
        "process_identity_snapshot_sha256": (
            value.process_identity_snapshot_sha256
        ),
        "receipt_leaf_id": schema.receipt_leaf_id,
        "semantic_payload_contract_sha256": (
            linux_confinement_semantic_payload_contract_sha256()
        ),
        "semantic_schema_id": artifact_type,
        "snapshot_stage_id": schema.snapshot_stage_id,
        "staging_run_binding_sha256": (
            value.staging_run_binding_sha256
        ),
        "subject_bindings": [
            _subject_binding_tree(item) for item in value.subject_bindings
        ],
        "subject_identity_table_sha256": (
            value.subject_identity_table_sha256
        ),
        "trusted_producer_id": schema.trusted_producer_id,
        "validation_scope_id": (
            LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_VALIDATION_SCOPE
        ),
    }


def linux_confinement_observation_payload_bytes(
    value: LinuxConfinementObservationPayloadV1,
) -> bytes:
    return _canonical_json(
        _observation_payload_tree(value),
        maximum=MAXIMUM_LINUX_CONFINEMENT_OBSERVATION_PAYLOAD_BYTES,
    )


def linux_confinement_observation_payload_sha256(
    value: LinuxConfinementObservationPayloadV1,
) -> str:
    _validated_observation_payload(value)
    return _domain_sha256(
        linux_confinement_observation_payload_artifact_type(
            value.observation_id
        ),
        linux_confinement_observation_payload_bytes(value),
    )


_SUBJECT_BINDING_FIELD_IDS: Final = (
    "artifact_type",
    "canonical_identity_hex",
    "format_version",
    "identity_byte_count",
    "identity_plain_sha256",
    "identity_schema_id",
    "identity_sha256",
    "origin_authenticated",
    "process_identity_snapshot_sha256",
    "staging_run_binding_sha256",
    "subject_kind_id",
    "subject_identity_table_sha256",
    "subject_role_id",
)
_EVIDENCE_MEMBER_FIELD_IDS: Final = (
    "artifact_type",
    "canonical_value_hex",
    "comparator_id",
    "field_id",
    "format_version",
    "process_identity_snapshot_sha256",
    "semantic_type_id",
    "staging_run_binding_sha256",
    "subject_identity_table_sha256",
    "value_byte_count",
    "value_codec_id",
    "value_plain_sha256",
    "value_sha256",
)
_OBSERVATION_PAYLOAD_FIELD_IDS: Final = (
    "artifact_type",
    "capture_window_end_monotonic_ns",
    "capture_window_start_monotonic_ns",
    "evidence_members",
    "family_id",
    "format_version",
    "lifecycle_stage_id",
    "nonclaims",
    "observation_id",
    "predicate_evaluation_status_id",
    "predicate_id",
    "procedure_id",
    "process_identity_snapshot_sha256",
    "receipt_leaf_id",
    "semantic_payload_contract_sha256",
    "semantic_schema_id",
    "snapshot_stage_id",
    "staging_run_binding_sha256",
    "subject_bindings",
    "subject_identity_table_sha256",
    "trusted_producer_id",
    "validation_scope_id",
)


def _decoded_hex(value: object, *, maximum: int) -> bytes:
    if type(value) is not str:
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
    if len(value) > 2 * maximum:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_RESOURCE)
    if (
        len(value) % 2
        or value != value.lower()
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
    try:
        return bytes.fromhex(value)
    except ValueError:
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)


def _parse_subject_binding(tree: dict) -> LinuxConfinementSubjectBindingV1:
    _exact_keys(tree, _SUBJECT_BINDING_FIELD_IDS)
    raw = _decoded_hex(
        tree["canonical_identity_hex"],
        maximum=MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES,
    )
    result = LinuxConfinementSubjectBindingV1(
        subject_role_id=tree["subject_role_id"],
        canonical_identity_bytes=raw,
        staging_run_binding_sha256=tree["staging_run_binding_sha256"],
        subject_identity_table_sha256=(
            tree["subject_identity_table_sha256"]
        ),
        process_identity_snapshot_sha256=(
            tree["process_identity_snapshot_sha256"]
        ),
    )
    if _subject_binding_tree(result) != tree:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    return result


def _parse_evidence_member(tree: dict) -> LinuxConfinementEvidenceMemberV1:
    _exact_keys(tree, _EVIDENCE_MEMBER_FIELD_IDS)
    raw = _decoded_hex(
        tree["canonical_value_hex"],
        maximum=MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES,
    )
    result = LinuxConfinementEvidenceMemberV1(
        field_id=tree["field_id"],
        canonical_value_bytes=raw,
        staging_run_binding_sha256=tree["staging_run_binding_sha256"],
        subject_identity_table_sha256=(
            tree["subject_identity_table_sha256"]
        ),
        process_identity_snapshot_sha256=(
            tree["process_identity_snapshot_sha256"]
        ),
    )
    if _evidence_member_tree(result) != tree:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    return result


def parse_linux_confinement_observation_payload(
    value: bytes,
) -> LinuxConfinementObservationPayloadV1:
    tree = _parse_canonical_json(
        value,
        maximum=MAXIMUM_LINUX_CONFINEMENT_OBSERVATION_PAYLOAD_BYTES,
    )
    _exact_keys(tree, _OBSERVATION_PAYLOAD_FIELD_IDS)
    if (
        type(tree["subject_bindings"]) is not list
        or type(tree["evidence_members"]) is not list
    ):
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
    result = LinuxConfinementObservationPayloadV1(
        observation_id=tree["observation_id"],
        staging_run_binding_sha256=tree["staging_run_binding_sha256"],
        subject_identity_table_sha256=(
            tree["subject_identity_table_sha256"]
        ),
        process_identity_snapshot_sha256=(
            tree["process_identity_snapshot_sha256"]
        ),
        capture_window_start_monotonic_ns=(
            tree["capture_window_start_monotonic_ns"]
        ),
        capture_window_end_monotonic_ns=(
            tree["capture_window_end_monotonic_ns"]
        ),
        subject_bindings=tuple(
            _parse_subject_binding(item)
            for item in tree["subject_bindings"]
        ),
        evidence_members=tuple(
            _parse_evidence_member(item)
            for item in tree["evidence_members"]
        ),
    )
    if _observation_payload_tree(result) != tree:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if linux_confinement_observation_payload_bytes(result) != value:
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
    return result


def _snapshot_for_observation(
    observation_id: str,
    snapshots: Tuple[LinuxConfinementProcessIdentitySnapshotV1, ...],
) -> LinuxConfinementProcessIdentitySnapshotV1:
    expected_stage = _observation_schema(
        observation_id
    ).snapshot_stage_id
    matches = tuple(
        item for item in snapshots if item.snapshot_stage_id == expected_stage
    )
    if len(matches) != 1:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    return matches[0]


def _task_by_slot(
    snapshot: LinuxConfinementProcessIdentitySnapshotV1,
) -> Dict[str, LinuxConfinementTaskIdentityV1]:
    return {item.task_slot_id: item for item in snapshot.task_identities}


def _canonicalize_projection_value(
    node: _ProjectionSchemaNode,
    value: object,
) -> object:
    if node.node_kind_id == "object":
        expected = tuple(field_id for field_id, _ in node.field_rows)
        _validate_exact_mapping_keys(value, expected)
        try:
            return {
                field_id: _canonicalize_projection_value(
                    child,
                    value[field_id],
                )
                for field_id, child in node.field_rows
            }
        except (
            AttributeError,
            KeyError,
            RuntimeError,
            TypeError,
            ValueError,
        ):
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    if node.node_kind_id == "list":
        if type(value) is not list:
            _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
        return [
            _canonicalize_projection_value(node.item_schema, item)
            for item in value
        ]
    return value


def build_linux_confinement_canonical_projection(
    *,
    observation_id: str,
    field_id: str,
    subject_identity_table: LinuxConfinementSubjectIdentityTableV1,
    process_identity_snapshots: Tuple[
        LinuxConfinementProcessIdentitySnapshotV1, ...
    ],
    resource_subject_identity_bytes: Mapping[str, bytes],
    source_observation_available: bool,
    source_observation_status_id: str,
    source_errno_id: str,
    values: Mapping[str, object],
) -> dict:
    """Build one projection with all context pins derived by this module."""

    schema = _projection_occurrence_schema(
        observation_id=observation_id,
        field_id=field_id,
    )
    validate_linux_confinement_process_identity_snapshot_chain(
        process_identity_snapshots,
        subject_identity_table=subject_identity_table,
    )
    snapshot = _snapshot_for_observation(
        observation_id,
        process_identity_snapshots,
    )
    resource_roles = tuple(
        role_id
        for role_id in schema.subject_role_ids
        if _SUBJECT_KIND_BY_ROLE[role_id] != "process-role"
    )
    _validate_exact_mapping_keys(
        resource_subject_identity_bytes,
        resource_roles,
    )
    table_sha256 = linux_confinement_subject_identity_table_sha256(
        subject_identity_table
    )
    snapshot_sha256 = (
        linux_confinement_process_identity_snapshot_sha256(snapshot)
    )
    rows = _task_by_slot(snapshot)
    subject_refs = []
    for role_id in schema.subject_role_ids:
        if _SUBJECT_KIND_BY_ROLE[role_id] == "process-role":
            task = rows[_ROLE_TO_TASK_SLOT[role_id]]
            instance_sha256 = (
                linux_confinement_kernel_task_instance_sha256(
                    task,
                    staging_run_binding_sha256=(
                        snapshot.staging_run_binding_sha256
                    ),
                    linux_platform_profile_sha256=(
                        snapshot.linux_platform_profile_sha256
                    ),
                    linux_boot_id_sha256=(
                        snapshot.linux_boot_id_sha256
                    ),
                )
            )
            if instance_sha256 == _ZERO_SHA256:
                _fail(
                    LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                )
            identity_bytes = _ascii(instance_sha256)
        else:
            identity_bytes = _mapping_value(
                resource_subject_identity_bytes,
                role_id,
            )
        binding = LinuxConfinementSubjectBindingV1(
            subject_role_id=role_id,
            canonical_identity_bytes=identity_bytes,
            staging_run_binding_sha256=(
                subject_identity_table.staging_run_binding_sha256
            ),
            subject_identity_table_sha256=table_sha256,
            process_identity_snapshot_sha256=snapshot_sha256,
        )
        subject_refs.append(
            {
                "subject_identity_sha256": _domain_sha256(
                    _identity_schema_id(role_id),
                    binding.canonical_identity_bytes,
                ),
                "subject_role_id": role_id,
            }
        )
    canonical_values = _canonicalize_projection_value(
        _PROJECTION_VALUE_SCHEMA_BY_FIELD[field_id],
        values,
    )
    result = {
        "field_id": field_id,
        "observation_id": observation_id,
        "process_identity_snapshot_sha256": snapshot_sha256,
        "projection_schema_id": _projection_schema_id(field_id),
        "source_errno_id": source_errno_id,
        "source_observation_available": source_observation_available,
        "source_observation_status_id": source_observation_status_id,
        "staging_run_binding_sha256": (
            subject_identity_table.staging_run_binding_sha256
        ),
        "subject_identity_refs": subject_refs,
        "subject_identity_table_sha256": table_sha256,
        "values": canonical_values,
    }
    _validate_canonical_projection(field_id, result)
    _canonical_json(
        result,
        maximum=MAXIMUM_LINUX_CONFINEMENT_RECORD_PROJECTION_BYTES,
    )
    return result


def _validate_projection_context(
    value: LinuxConfinementObservationPayloadV1,
) -> Dict[str, dict]:
    expected_subject_refs = [
        {
            "subject_identity_sha256": _domain_sha256(
                _identity_schema_id(binding.subject_role_id),
                binding.canonical_identity_bytes,
            ),
            "subject_role_id": binding.subject_role_id,
        }
        for binding in value.subject_bindings
    ]
    result = {}
    for member in value.evidence_members:
        if (
            _field_codec_id(member.field_id)
            != LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT
        ):
            continue
        projection = _validate_canonical_record_value(
            member.field_id,
            member.canonical_value_bytes,
        )["canonical_projection"]
        if (
            projection["observation_id"] != value.observation_id
            or projection["staging_run_binding_sha256"]
            != value.staging_run_binding_sha256
            or projection["subject_identity_table_sha256"]
            != value.subject_identity_table_sha256
            or projection["process_identity_snapshot_sha256"]
            != value.process_identity_snapshot_sha256
            or projection["subject_identity_refs"]
            != expected_subject_refs
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
        result[member.field_id] = projection
    return result


_U64_RESOURCE_EVIDENCE_JOINS: Final = (
    (
        "dependency-lock-byte-count",
        "sandbox-dependency-lock",
        "byte_count",
    ),
    (
        "bootstrap-source-byte-count",
        "staging-bootstrap",
        "byte_count",
    ),
)
_SHA256_RESOURCE_EVIDENCE_JOINS: Final = (
    (
        "dependency-lock-plain-sha256",
        "sandbox-dependency-lock",
        "content_sha256",
    ),
    (
        "bootstrap-source-sha256",
        "staging-bootstrap",
        "content_sha256",
    ),
    (
        "bootstrap-execution-closure-manifest-sha256",
        "bootstrap-execution-closure",
        "content_sha256",
    ),
    (
        "interpreter-file-sha256",
        "sandbox-interpreter",
        "content_sha256",
    ),
    (
        "rootfs-image-sha256",
        "runtime-rootfs",
        "content_sha256",
    ),
    (
        "rootfs-manifest-sha256",
        "runtime-rootfs",
        "manifest_membership_sha256",
    ),
    (
        "landlock-ruleset-sha256",
        "adapter-stage-landlock-ruleset",
        "content_sha256",
    ),
    (
        "platform-profile-sha256",
        "linux-host-platform",
        "platform_profile_sha256",
    ),
    (
        "launch-filter-sha256",
        "launch-seccomp-filter",
        "content_sha256",
    ),
    (
        "adapter-filter-sha256",
        "adapter-seccomp-filter",
        "content_sha256",
    ),
    (
        "supervisor-dependency-closure-sha256",
        "supervisor-dependency-closure",
        "content_sha256",
    ),
)


def _binding_identity_sha256(
    binding: LinuxConfinementSubjectBindingV1,
) -> str:
    return _domain_sha256(
        _identity_schema_id(binding.subject_role_id),
        binding.canonical_identity_bytes,
    )


def _resource_views(
    value: LinuxConfinementObservationPayloadV1,
) -> Tuple[Dict[str, dict], Dict[str, str]]:
    components = {}
    identities = {}
    for binding in value.subject_bindings:
        role_id = binding.subject_role_id
        if _SUBJECT_KIND_BY_ROLE[role_id] == "process-role":
            continue
        resource = _validate_resource_subject_identity(
            role_id,
            binding.canonical_identity_bytes,
        )
        components[role_id] = resource["identity_components"]
        identities[role_id] = _binding_identity_sha256(binding)
    return components, identities


def _evidence_sha256_value(
    member: LinuxConfinementEvidenceMemberV1,
) -> str:
    try:
        value = member.canonical_value_bytes.decode("ascii", "strict")
    except UnicodeError:
        _fail(LinuxConfinementSemanticPayloadCode.CANONICAL_INVALID)
    _sha256_token(value)
    return value


def _task_join_catalog(
    snapshots: Tuple[LinuxConfinementProcessIdentitySnapshotV1, ...],
) -> Dict[str, dict]:
    result = {
        slot_id: {
            "exit_observation_record_sha256": set(),
            "host_tgid": 0,
            "instance_sha256": "",
            "lifecycle_transition_record_sha256": set(),
            "pidfd_acquisition_method_id": "",
            "pidfd_acquisition_record_sha256": set(),
            "wait_reap_record_sha256": set(),
        }
        for slot_id in LINUX_CONFINEMENT_TASK_SLOT_IDS
    }
    for snapshot in snapshots:
        for task in snapshot.task_identities:
            row = result[task.task_slot_id]
            instance_sha256 = (
                linux_confinement_kernel_task_instance_sha256(
                    task,
                    staging_run_binding_sha256=(
                        snapshot.staging_run_binding_sha256
                    ),
                    linux_platform_profile_sha256=(
                        snapshot.linux_platform_profile_sha256
                    ),
                    linux_boot_id_sha256=(
                        snapshot.linux_boot_id_sha256
                    ),
                )
            )
            if instance_sha256 != _ZERO_SHA256:
                if (
                    row["instance_sha256"]
                    and row["instance_sha256"] != instance_sha256
                ):
                    _fail(
                        LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                    )
                row["instance_sha256"] = instance_sha256
                if row["host_tgid"] not in (0, task.host_tgid):
                    _fail(
                        LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                    )
                row["host_tgid"] = task.host_tgid
                if (
                    row["pidfd_acquisition_method_id"]
                    and row["pidfd_acquisition_method_id"]
                    != task.pidfd_acquisition_method_id
                ):
                    _fail(
                        LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                    )
                row["pidfd_acquisition_method_id"] = (
                    task.pidfd_acquisition_method_id
                )
            for name in (
                "exit_observation_record_sha256",
                "lifecycle_transition_record_sha256",
                "pidfd_acquisition_record_sha256",
                "wait_reap_record_sha256",
            ):
                digest = getattr(task, name)
                if digest != _ZERO_SHA256:
                    row[name].add(digest)
    return result


def _join_task_instance(
    catalog: Dict[str, dict],
    task_slot_id: str,
    digest: str,
) -> None:
    if (
        task_slot_id not in catalog
        or digest in ("", _ZERO_SHA256)
    ):
        return
    if digest != catalog[task_slot_id]["instance_sha256"]:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


def _join_task_record(
    catalog: Dict[str, dict],
    task_slot_id: str,
    record_field_id: str,
    digest: str,
) -> None:
    if (
        task_slot_id not in catalog
        or digest in ("", _ZERO_SHA256)
    ):
        return
    if digest not in catalog[task_slot_id][record_field_id]:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


def _join_role_instance(
    catalog: Dict[str, dict],
    role_id: str,
    digest: str,
) -> None:
    if role_id in _ROLE_TO_TASK_SLOT:
        _join_task_instance(
            catalog,
            _ROLE_TO_TASK_SLOT[role_id],
            digest,
        )


def _join_resource_record_components(
    resource_components: Dict[str, dict],
    role_id: str,
    record: dict,
    component_names: Tuple[str, ...],
) -> None:
    if role_id not in resource_components:
        return
    components = resource_components[role_id]
    if any(
        record[name] != components[name] for name in component_names
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


def _join_optional_digest(
    claimed: str,
    expected: str,
) -> None:
    if claimed not in ("", _ZERO_SHA256) and claimed != expected:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


def _validate_resource_projection_joins(
    value: LinuxConfinementObservationPayloadV1,
    projection_values: Dict[str, dict],
) -> None:
    resource_components, resource_identities = _resource_views(value)
    members = {item.field_id: item for item in value.evidence_members}
    for field_id, role_id, component_id in (
        _U64_RESOURCE_EVIDENCE_JOINS
    ):
        if field_id not in members or role_id not in resource_components:
            continue
        observed = int.from_bytes(
            members[field_id].canonical_value_bytes,
            "big",
        )
        if observed != resource_components[role_id][component_id]:
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    for field_id, role_id, component_id in (
        _SHA256_RESOURCE_EVIDENCE_JOINS
    ):
        if field_id not in members or role_id not in resource_components:
            continue
        if (
            _evidence_sha256_value(members[field_id])
            != resource_components[role_id][component_id]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "backend-memfd-stat-record" in projection_values:
        _join_resource_record_components(
            resource_components,
            "backend-executable-memfd",
            projection_values["backend-memfd-stat-record"]["stat"],
            ("device", "inode", "generation"),
        )
    if "cgroup-leaf-stat-record" in projection_values:
        _join_resource_record_components(
            resource_components,
            "sandbox-cgroup-v2-leaf",
            projection_values["cgroup-leaf-stat-record"]["object"],
            (
                "device",
                "inode",
                "generation",
                "kernel_object_type_id",
            ),
        )
    if "network-namespace-inode-record" in projection_values:
        record = projection_values["network-namespace-inode-record"]
        components = resource_components.get(
            "application-network-namespace"
        )
        if components is not None and (
            record["namespace_id"] != components["namespace_type_id"]
            or any(
                record[name] != components[name]
                for name in (
                    "device",
                    "inode",
                    "owner_user_namespace_inode",
                )
            )
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "architecture-record" in projection_values:
        components = resource_components.get("linux-host-platform")
        if (
            components is not None
            and projection_values["architecture-record"][
                "architecture_id"
            ]
            != components["architecture_id"]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "kernel-release-and-build-record" in projection_values:
        components = resource_components.get("linux-host-platform")
        if (
            components is not None
            and projection_values["kernel-release-and-build-record"][
                "boot_id_sha256"
            ]
            != components["linux_boot_id_sha256"]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "linux-security-feature-probe-record" in projection_values:
        components = resource_components.get("linux-host-platform")
        if (
            components is not None
            and projection_values[
                "linux-security-feature-probe-record"
            ]["platform_profile_sha256"]
            != components["platform_profile_sha256"]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "landlock-install-return-record" in projection_values:
        components = resource_components.get(
            "adapter-stage-landlock-ruleset"
        )
        if (
            components is not None
            and projection_values["landlock-install-return-record"][
                "ruleset_content_sha256"
            ]
            != components["content_sha256"]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    for field_id in (
        "cgroup-process-membership-record",
        "cgroup-process-final-inventory",
    ):
        if (
            field_id in projection_values
            and "sandbox-cgroup-v2-leaf" in resource_identities
            and projection_values[field_id]["leaf_identity_sha256"]
            != resource_identities["sandbox-cgroup-v2-leaf"]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "stage1-barrier-pipe-kernel-object-identity-record" in (
        projection_values
    ):
        _join_resource_record_components(
            resource_components,
            "stage1-barrier",
            projection_values[
                "stage1-barrier-pipe-kernel-object-identity-record"
            ]["read_end"],
            (
                "device",
                "inode",
                "generation",
                "kernel_object_type_id",
            ),
        )
    if "pidfd-bound-stage1-barrier-read-block-record" in (
        projection_values
    ):
        expected = resource_identities.get("stage1-barrier")
        if (
            expected is not None
            and projection_values[
                "pidfd-bound-stage1-barrier-read-block-record"
            ]["barrier_identity_sha256"]
            != expected
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "stage1-and-stage2-release-record" in projection_values:
        expected = resource_identities.get("stage1-barrier")
        if expected is not None:
            _join_optional_digest(
                projection_values["stage1-and-stage2-release-record"][
                    "stage1"
                ]["release_channel_identity_sha256"],
                expected,
            )
    membership_joins = (
        (
            "bootstrap-rootfs-membership-record",
            "staging-bootstrap",
        ),
        (
            "interpreter-rootfs-membership-record",
            "sandbox-interpreter",
        ),
    )
    for field_id, role_id in membership_joins:
        if field_id not in projection_values:
            continue
        components = resource_components.get(role_id)
        if components is not None:
            _join_optional_digest(
                projection_values[field_id]["content_sha256"],
                components["content_sha256"],
            )
    if "supervisor-loader-resolution-record" in projection_values:
        components = resource_components.get(
            "supervisor-dependency-closure"
        )
        if components is not None:
            _join_optional_digest(
                projection_values[
                    "supervisor-loader-resolution-record"
                ]["closure_sha256"],
                components["content_sha256"],
            )


def _join_task_reference_bundle(
    catalog: Dict[str, dict],
    task_slot_id: str,
    record: dict,
    *,
    instance_field_id: str,
    record_field_ids: Tuple[str, ...] = (),
) -> None:
    _join_task_instance(
        catalog,
        task_slot_id,
        record[instance_field_id],
    )
    for field_id in record_field_ids:
        _join_task_record(
            catalog,
            task_slot_id,
            field_id,
            record[field_id],
        )


def _validate_task_projection_joins(
    projection_values: Dict[str, dict],
    snapshots: Tuple[LinuxConfinementProcessIdentitySnapshotV1, ...],
) -> None:
    catalog = _task_join_catalog(snapshots)
    for field_id in (
        "cgroup-process-membership-record",
        "cgroup-process-final-inventory",
    ):
        if field_id not in projection_values:
            continue
        for row in projection_values[field_id]["members"]:
            _join_role_instance(
                catalog,
                row["role_id"],
                row["kernel_task_instance_sha256"],
            )
    if "cgroup-leaf-owner-record" in projection_values:
        _join_task_instance(
            catalog,
            "supervisor-task",
            projection_values["cgroup-leaf-owner-record"][
                "owner_task_instance_sha256"
            ],
        )
    if "observer-adoption-and-reap-record" in projection_values:
        record = projection_values[
            "observer-adoption-and-reap-record"
        ]
        _join_task_reference_bundle(
            catalog,
            "helper-task",
            record,
            instance_field_id="observer_task_instance_sha256",
            record_field_ids=(
                "pidfd_acquisition_record_sha256",
                "exit_observation_record_sha256",
                "wait_reap_record_sha256",
            ),
        )
        _join_task_instance(
            catalog,
            "supervisor-task",
            record["original_parent_task_instance_sha256"],
        )
        _join_task_instance(
            catalog,
            "supervisor-task",
            record["adopter_task_instance_sha256"],
        )
    if "bubblewrap-child-pid-status-record" in projection_values:
        record = projection_values["bubblewrap-child-pid-status-record"]
        _join_task_instance(
            catalog,
            "pid1-task",
            record["child_task_instance_sha256"],
        )
        if record["child_host_tgid"] != catalog["pid1-task"]["host_tgid"]:
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "pidfd-bound-stage1-barrier-read-block-record" in (
        projection_values
    ):
        record = projection_values[
            "pidfd-bound-stage1-barrier-read-block-record"
        ]
        _join_task_reference_bundle(
            catalog,
            "pid1-task",
            record,
            instance_field_id="reader_task_instance_sha256",
        )
        _join_task_record(
            catalog,
            "pid1-task",
            "pidfd_acquisition_record_sha256",
            record["reader_pidfd_acquisition_record_sha256"],
        )
    if "application-stop-and-pidfd-record" in projection_values:
        record = projection_values["application-stop-and-pidfd-record"]
        _join_task_reference_bundle(
            catalog,
            "application-task",
            record,
            instance_field_id="application_task_instance_sha256",
            record_field_ids=("pidfd_acquisition_record_sha256",),
        )
    if "stage1-and-stage2-release-record" in projection_values:
        _join_task_instance(
            catalog,
            "application-task",
            projection_values["stage1-and-stage2-release-record"][
                "stage2"
            ]["target_task_instance_sha256"],
        )
    if "clone3-pidfd-acquisition-records" in projection_values:
        for row in projection_values[
            "clone3-pidfd-acquisition-records"
        ]["records"]:
            slot_id = row["task_slot_id"]
            _join_task_reference_bundle(
                catalog,
                slot_id,
                row,
                instance_field_id="kernel_task_instance_sha256",
                record_field_ids=(
                    "pidfd_acquisition_record_sha256",
                ),
            )
            if (
                slot_id in catalog
                and row["host_tgid"] != catalog[slot_id]["host_tgid"]
            ):
                _fail(
                    LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                )
    if "role-process-identity-records" in projection_values:
        for row in projection_values[
            "role-process-identity-records"
        ]["roles"]:
            role_id = row["role_id"]
            slot_id = row["task_slot_id"]
            if (
                role_id in _ROLE_TO_TASK_SLOT
                and _ROLE_TO_TASK_SLOT[role_id] != slot_id
            ):
                _fail(
                    LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                )
            _join_task_reference_bundle(
                catalog,
                slot_id,
                row,
                instance_field_id="kernel_task_instance_sha256",
                record_field_ids=(
                    "pidfd_acquisition_record_sha256",
                    "lifecycle_transition_record_sha256",
                ),
            )
    if "parentage-and-adoption-records" in projection_values:
        for row in projection_values[
            "parentage-and-adoption-records"
        ]["relations"]:
            _join_task_instance(
                catalog,
                row["child_task_slot_id"],
                row["child_task_instance_sha256"],
            )
            _join_task_instance(
                catalog,
                row["parent_task_slot_id"],
                row["parent_task_instance_sha256"],
            )
    fixed_records = (
        (
            "unprivileged-preexec-launcher-parentage-record",
            "monitor-task",
            "launcher_task_instance_sha256",
            (),
        ),
        (
            (
                "unprivileged-preexec-launcher-lifetime-and-exec-"
                "transition-record"
            ),
            "monitor-task",
            "kernel_task_instance_sha256",
            (
                "lifecycle_transition_record_sha256",
                "exit_observation_record_sha256",
            ),
        ),
        (
            (
                "unprivileged-preexec-launcher-to-monitor-same-pid-"
                "exec-and-reap-record"
            ),
            "monitor-task",
            "kernel_task_instance_sha256",
            ("lifecycle_transition_record_sha256",),
        ),
        (
            "bubblewrap-setup-child-pidfd-acquisition-record",
            "pid1-task",
            "kernel_task_instance_sha256",
            ("pidfd_acquisition_record_sha256",),
        ),
        (
            "bubblewrap-setup-child-parentage-record",
            "pid1-task",
            "child_task_instance_sha256",
            (),
        ),
        (
            "bubblewrap-setup-child-lifetime-record",
            "pid1-task",
            "kernel_task_instance_sha256",
            (
                "lifecycle_transition_record_sha256",
                "exit_observation_record_sha256",
            ),
        ),
        (
            (
                "bubblewrap-setup-child-to-sandbox-pid1-same-host-"
                "pid-lifecycle-transition-record"
            ),
            "pid1-task",
            "kernel_task_instance_sha256",
            ("lifecycle_transition_record_sha256",),
        ),
        (
            "bubblewrap-setup-child-exit-adoption-and-reap-record",
            "pid1-task",
            "kernel_task_instance_sha256",
            (
                "exit_observation_record_sha256",
                "wait_reap_record_sha256",
            ),
        ),
    )
    for field_id, slot_id, instance_field_id, record_fields in (
        fixed_records
    ):
        if field_id in projection_values:
            _join_task_reference_bundle(
                catalog,
                slot_id,
                projection_values[field_id],
                instance_field_id=instance_field_id,
                record_field_ids=record_fields,
            )
    if "unprivileged-preexec-launcher-parentage-record" in (
        projection_values
    ):
        _join_task_instance(
            catalog,
            "supervisor-task",
            projection_values[
                "unprivileged-preexec-launcher-parentage-record"
            ]["parent_task_instance_sha256"],
        )
    if "bubblewrap-setup-child-parentage-record" in projection_values:
        _join_task_instance(
            catalog,
            "monitor-task",
            projection_values[
                "bubblewrap-setup-child-parentage-record"
            ]["parent_task_instance_sha256"],
        )
    if "bubblewrap-setup-child-pidfd-acquisition-record" in (
        projection_values
    ):
        record = projection_values[
            "bubblewrap-setup-child-pidfd-acquisition-record"
        ]
        if (
            record["pidfd_acquisition_method_id"]
            != catalog["pid1-task"]["pidfd_acquisition_method_id"]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "bubblewrap-setup-child-exit-adoption-and-reap-record" in (
        projection_values
    ):
        _join_task_instance(
            catalog,
            "supervisor-task",
            projection_values[
                "bubblewrap-setup-child-exit-adoption-and-reap-record"
            ]["adopter_task_instance_sha256"],
        )
    for field_id in (
        "wait-reap-status-records",
        "monitor-and-descendant-wait-reap-records",
    ):
        if field_id not in projection_values:
            continue
        for row in projection_values[field_id]["records"]:
            _join_task_reference_bundle(
                catalog,
                row["task_slot_id"],
                row,
                instance_field_id="kernel_task_instance_sha256",
                record_field_ids=(
                    "exit_observation_record_sha256",
                    "wait_reap_record_sha256",
                ),
            )
    if "subreaper-setting-and-child-inventory-record" in (
        projection_values
    ):
        _join_task_instance(
            catalog,
            "supervisor-task",
            projection_values[
                "subreaper-setting-and-child-inventory-record"
            ]["supervisor_task_instance_sha256"],
        )


def _require_unique_rows(
    rows: list,
    key_ids: Tuple[str, ...],
) -> set:
    keys = {
        tuple(row[key_id] for key_id in key_ids) for row in rows
    }
    if len(keys) != len(rows):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    return keys


def _validate_run_and_internal_projection_joins(
    projection_values: Dict[str, dict],
    subject_identity_table: LinuxConfinementSubjectIdentityTableV1,
) -> None:
    if "nonce-registry-insertion-record" in projection_values:
        record = projection_values["nonce-registry-insertion-record"]
        if (
            record["supervisor_epoch_id_hex"]
            != subject_identity_table.supervisor_epoch_id_hex
            or record["run_nonce_hex"]
            != subject_identity_table.run_nonce_hex
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
        prior = record["prior_entry_count"]
        post = record["post_entry_count"]
        capacity = record["registry_capacity"]
        if (
            prior > capacity
            or post > capacity
            or post not in (prior, prior + 1)
            or (
                post == prior + 1
                and record["insertion_index"] != prior
            )
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if (
        "run-sequence-record" in projection_values
        and projection_values["run-sequence-record"][
            "run_sequence_number"
        ]
        != subject_identity_table.run_sequence_number
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if (
        "ready-frame-bytes-and-chunk-record" in projection_values
        and projection_values["ready-frame-bytes-and-chunk-record"][
            "run_nonce_hex"
        ]
        != subject_identity_table.run_nonce_hex
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    event_rows = []
    if "PRE_RELEASE_STDOUT_DRAINED-event-record" in projection_values:
        event_rows.append(
            projection_values[
                "PRE_RELEASE_STDOUT_DRAINED-event-record"
            ]["event"]
        )
    if "stage1-and-stage2-release-record" in projection_values:
        release = projection_values["stage1-and-stage2-release-record"]
        event_rows.extend(
            (release["stage1"]["event"], release["stage2"]["event"])
        )
    if any(
        row["staging_run_binding_sha256"]
        != subject_identity_table.staging_run_binding_sha256
        for row in event_rows
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "backend-elf-dynamic-section-record" in projection_values:
        record = projection_values[
            "backend-elf-dynamic-section-record"
        ]
        if record["dt_needed_count"] != len(
            record["dt_needed_sonames"]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "getrandom-call-record" in projection_values:
        record = projection_values["getrandom-call-record"]
        if (
            record["returned_byte_count"]
            != len(record["returned_nonce_hex"]) // 2
            or record["returned_byte_count"]
            > record["requested_byte_count"]
            or record["call_start_monotonic_ns"]
            > record["call_end_monotonic_ns"]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "ready-frame-bytes-and-chunk-record" in projection_values:
        record = projection_values[
            "ready-frame-bytes-and-chunk-record"
        ]
        if (
            record["frame_byte_count"] != len(record["frame_hex"]) // 2
            or sum(record["chunk_byte_counts"])
            != record["frame_byte_count"]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "pre-release-stdout-drain-to-eagain-record" in (
        projection_values
    ):
        record = projection_values[
            "pre-release-stdout-drain-to-eagain-record"
        ]
        if (
            sum(record["read_chunk_byte_counts"])
            != record["total_drained_byte_count"]
            or record["drain_start_monotonic_ns"]
            > record["drain_end_monotonic_ns"]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    endpoint_fields = (
        (
            "ready-frame-bytes-and-chunk-record",
            "stdout_read_end_identity_sha256",
        ),
        (
            "pre-release-stdout-drain-to-eagain-record",
            "stdout_read_end_identity_sha256",
        ),
        (
            "pre-release-stdout-buffered-byte-count-zero-record",
            "stdout_read_end_identity_sha256",
        ),
    )
    endpoints = {
        projection_values[field_id][key_id]
        for field_id, key_id in endpoint_fields
        if field_id in projection_values
    }
    if len(endpoints) > 1:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "stage1-and-stage2-release-record" in projection_values:
        stage1 = projection_values[
            "stage1-and-stage2-release-record"
        ]["stage1"]
        if stage1["release_write_count"] != (
            len(stage1["release_payload_hex"]) // 2
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "cgroup-process-final-inventory" in projection_values:
        record = projection_values["cgroup-process-final-inventory"]
        if record["member_count"] != len(record["members"]):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    if "application-fd-inventory-record" in projection_values:
        inventory = _require_unique_rows(
            projection_values["application-fd-inventory-record"][
                "descriptors"
            ],
            ("fd_number", "fd_role_id"),
        )
        fd_rows = (
            (
                "fd-kernel-object-stat-records",
                "descriptors",
                "fd_number",
            ),
            (
                "fd-access-flags-and-offset-records",
                "descriptors",
                "fd_number",
            ),
            (
                "fd-cloexec-and-inheritance-records",
                "descriptors",
                "fd_number",
            ),
            ("stdio-isatty-records", "stdio", "fd_number"),
            (
                "supervisor-peer-custody-records",
                "peers",
                "application_fd_number",
            ),
        )
        for field_id, rows_id, number_id in fd_rows:
            if field_id not in projection_values:
                continue
            rows = projection_values[field_id][rows_id]
            keys = _require_unique_rows(
                rows,
                (number_id, "fd_role_id"),
            )
            if not keys.issubset(inventory):
                _fail(
                    LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                )
    if "canonical-mountinfo-record" in projection_values:
        mount_ids = _require_unique_rows(
            projection_values["canonical-mountinfo-record"]["mounts"],
            ("mount_id",),
        )
        for field_id, rows_id in (
            ("mount-propagation-record", "mounts"),
            ("writable-path-inventory-record", "writable_paths"),
            (
                "forbidden-mount-type-absence-record",
                "observed_forbidden_mounts",
            ),
        ):
            if field_id not in projection_values:
                continue
            for row in projection_values[field_id][rows_id]:
                if (row["mount_id"],) not in mount_ids:
                    _fail(
                        LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                    )
    if "network-interface-record" in projection_values:
        interfaces = _require_unique_rows(
            projection_values["network-interface-record"]["interfaces"],
            ("ifindex",),
        )
        for field_id in ("ipv4-route-record", "ipv6-route-record"):
            if field_id not in projection_values:
                continue
            for row in projection_values[field_id]["routes"]:
                if (
                    row["output_ifindex"] != 0
                    and (row["output_ifindex"],) not in interfaces
                ):
                    _fail(
                        LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                    )
    if (
        "host-view-final-uid-gid-map-record" in projection_values
        and "intermediate-view-map-records" in projection_values
    ):
        host_view = projection_values[
            "host-view-final-uid-gid-map-record"
        ]
        intermediate = projection_values[
            "intermediate-view-map-records"
        ]
        if (
            host_view["final_uid_map"] != intermediate["final_uid_map"]
            or host_view["final_gid_map"]
            != intermediate["final_gid_map"]
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


def validate_linux_confinement_observation_payload_context(
    value: LinuxConfinementObservationPayloadV1,
    *,
    subject_identity_table: LinuxConfinementSubjectIdentityTableV1,
    process_identity_snapshots: Tuple[
        LinuxConfinementProcessIdentitySnapshotV1, ...
    ],
) -> None:
    """Join one payload to the topology and exact three-snapshot chain."""

    _validated_observation_payload(value)
    validate_linux_confinement_process_identity_snapshot_chain(
        process_identity_snapshots,
        subject_identity_table=subject_identity_table,
    )
    table_sha256 = linux_confinement_subject_identity_table_sha256(
        subject_identity_table
    )
    snapshot = _snapshot_for_observation(
        value.observation_id,
        process_identity_snapshots,
    )
    snapshot_sha256 = (
        linux_confinement_process_identity_snapshot_sha256(snapshot)
    )
    snapshot_times = {
        item.snapshot_stage_id: item.capture_monotonic_timestamp_ns
        for item in process_identity_snapshots
    }
    stage1_time = snapshot_times[
        LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE1
    ]
    stage2_time = snapshot_times[
        LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE2
    ]
    postrun_time = snapshot_times[
        LINUX_CONFINEMENT_SNAPSHOT_STAGE_POSTRUN
    ]
    if (
        value.staging_run_binding_sha256
        != subject_identity_table.staging_run_binding_sha256
        or value.subject_identity_table_sha256 != table_sha256
        or value.process_identity_snapshot_sha256 != snapshot_sha256
        or value.capture_window_end_monotonic_ns
        > snapshot.capture_monotonic_timestamp_ns
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    schema = _observation_schema(value.observation_id)
    if schema.snapshot_stage_id == (
        LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE1
    ):
        timing_valid = value.capture_window_end_monotonic_ns <= stage1_time
    elif schema.snapshot_stage_id == (
        LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE2
    ):
        timing_valid = (
            value.capture_window_start_monotonic_ns >= stage1_time
            and value.capture_window_end_monotonic_ns <= stage2_time
        )
    elif value.observation_id == (
        "teardown-cgroup-populated-zero-observed"
    ):
        timing_valid = (
            value.capture_window_start_monotonic_ns >= stage2_time
            and value.capture_window_end_monotonic_ns <= postrun_time
        )
    elif value.observation_id == (
        "pidfd-bound-observer-helper-monitor-init-application-"
        "identities-subreaper-adoption-and-reap-observed"
    ):
        timing_valid = (
            value.capture_window_start_monotonic_ns <= stage1_time
            and value.capture_window_end_monotonic_ns == postrun_time
        )
    else:
        timing_valid = (
            value.capture_window_start_monotonic_ns <= stage1_time
            and value.capture_window_end_monotonic_ns >= stage2_time
            and value.capture_window_end_monotonic_ns <= postrun_time
        )
    if not timing_valid:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    projection_records = _validate_projection_context(value)
    projection_values = {
        field_id: projection["values"]
        for field_id, projection in projection_records.items()
        if projection["source_observation_available"]
    }
    rows = _task_by_slot(snapshot)
    for binding in value.subject_bindings:
        if (
            _SUBJECT_KIND_BY_ROLE[binding.subject_role_id]
            != "process-role"
        ):
            resource = _validate_resource_subject_identity(
                binding.subject_role_id,
                binding.canonical_identity_bytes,
            )
            if (
                resource["staging_run_binding_sha256"]
                != value.staging_run_binding_sha256
                or resource["subject_identity_table_sha256"]
                != value.subject_identity_table_sha256
                or resource["process_identity_snapshot_sha256"]
                != value.process_identity_snapshot_sha256
                or resource["linux_boot_id_sha256"]
                != snapshot.linux_boot_id_sha256
            ):
                _fail(
                    LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                )
            if (
                binding.subject_role_id == "linux-host-platform"
                and (
                    resource["identity_components"][
                        "linux_boot_id_sha256"
                    ]
                    != snapshot.linux_boot_id_sha256
                    or resource["identity_components"][
                        "platform_profile_sha256"
                    ]
                    != snapshot.linux_platform_profile_sha256
                )
            ):
                _fail(
                    LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                )
            continue
        task = rows[_ROLE_TO_TASK_SLOT[binding.subject_role_id]]
        instance_sha256 = (
            linux_confinement_kernel_task_instance_sha256(
                task,
                staging_run_binding_sha256=(
                    snapshot.staging_run_binding_sha256
                ),
                linux_platform_profile_sha256=(
                    snapshot.linux_platform_profile_sha256
                ),
                linux_boot_id_sha256=snapshot.linux_boot_id_sha256,
            )
        )
        if (
            instance_sha256 == _ZERO_SHA256
            or binding.canonical_identity_bytes
            != _ascii(instance_sha256)
        ):
            _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    _validate_resource_projection_joins(value, projection_values)
    _validate_task_projection_joins(
        projection_values,
        process_identity_snapshots,
    )
    _validate_run_and_internal_projection_joins(
        projection_values,
        subject_identity_table,
    )
    if value.observation_id == (
        "pidfd-bound-observer-helper-monitor-init-application-"
        "identities-subreaper-adoption-and-reap-observed"
    ):
        transition_checks = (
            (
                (
                    "unprivileged-preexec-launcher-to-monitor-same-pid-"
                    "exec-and-reap-record"
                ),
                LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE1,
                "monitor-task",
            ),
            (
                (
                    "bubblewrap-setup-child-to-sandbox-pid1-same-host-"
                    "pid-lifecycle-transition-record"
                ),
                LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE2,
                "pid1-task",
            ),
        )
        snapshots_by_stage = {
            item.snapshot_stage_id: item
            for item in process_identity_snapshots
        }
        for field_id, stage_id, task_slot_id in transition_checks:
            if field_id not in projection_values:
                continue
            transition = projection_values[field_id]
            transition_snapshot = snapshots_by_stage[stage_id]
            transition_task = _task_by_slot(
                transition_snapshot
            )[task_slot_id]
            expected_instance = (
                linux_confinement_kernel_task_instance_sha256(
                    transition_task,
                    staging_run_binding_sha256=(
                        transition_snapshot.staging_run_binding_sha256
                    ),
                    linux_platform_profile_sha256=(
                        transition_snapshot.linux_platform_profile_sha256
                    ),
                    linux_boot_id_sha256=(
                        transition_snapshot.linux_boot_id_sha256
                    ),
                )
            )
            if (
                transition["kernel_task_instance_sha256"]
                != expected_instance
                or (
                    transition[
                        "lifecycle_transition_record_sha256"
                    ]
                    not in ("", _ZERO_SHA256)
                    and transition[
                        "lifecycle_transition_record_sha256"
                    ]
                    != transition_task.lifecycle_transition_record_sha256
                )
            ):
                _fail(
                    LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                )


def _stable_resource_identity(
    role_id: str,
    identity_bytes: bytes,
) -> tuple:
    tree = _validate_resource_subject_identity(role_id, identity_bytes)
    components = tree["identity_components"]
    kind_id = _SUBJECT_KIND_BY_ROLE[role_id]
    if kind_id == "namespace":
        names = (
            "namespace_type_id",
            "device",
            "inode",
            "owner_user_namespace_inode",
        )
    elif kind_id == "kernel-object":
        names = (
            "kernel_object_type_id",
            "device",
            "inode",
            "generation",
        )
    elif kind_id == "content-artifact":
        names = (
            "byte_count",
            "content_sha256",
            "manifest_membership_sha256",
        )
    elif kind_id == "security-policy-object":
        names = (
            "security_object_type_id",
            "content_sha256",
            "feature_manifest_sha256",
        )
    elif kind_id == "platform":
        names = (
            "architecture_id",
            "linux_boot_id_sha256",
            "platform_profile_sha256",
        )
    elif kind_id == "process-set":
        names = ("member_count", "membership_sha256")
    else:
        _fail(LinuxConfinementSemanticPayloadCode.INTERNAL)
    return tuple(components[name] for name in names)


def validate_linux_confinement_observation_payload_set(
    values: Tuple[LinuxConfinementObservationPayloadV1, ...],
    *,
    subject_identity_table: LinuxConfinementSubjectIdentityTableV1,
    process_identity_snapshots: Tuple[
        LinuxConfinementProcessIdentitySnapshotV1, ...
    ],
) -> None:
    """Validate exact 24-record coverage and shared subject identities."""

    if (
        type(values) is not tuple
        or len(values) != len(LINUX_CONFINEMENT_OBSERVATION_IDS)
        or any(
            type(item) is not LinuxConfinementObservationPayloadV1
            for item in values
        )
        or tuple(item.observation_id for item in values)
        != LINUX_CONFINEMENT_AGGREGATE_OBSERVATION_IDS
    ):
        _fail(LinuxConfinementSemanticPayloadCode.ORDER_INVALID)
    stable_resources: Dict[str, tuple] = {}
    architecture_ids = []
    seccomp_architecture_ids = []
    elf_machine_ids = []
    for payload in values:
        validate_linux_confinement_observation_payload_context(
            payload,
            subject_identity_table=subject_identity_table,
            process_identity_snapshots=process_identity_snapshots,
        )
        for binding in payload.subject_bindings:
            if (
                _SUBJECT_KIND_BY_ROLE[binding.subject_role_id]
                == "process-role"
            ):
                continue
            stable = _stable_resource_identity(
                binding.subject_role_id,
                binding.canonical_identity_bytes,
            )
            prior = stable_resources.setdefault(
                binding.subject_role_id,
                stable,
            )
            if prior != stable:
                _fail(
                    LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH
                )
        for member in payload.evidence_members:
            if member.field_id not in (
                "architecture-record",
                "backend-elf-program-header-record",
                "interpreter-elf-linkage-record",
                "seccomp-status-and-filter-count-record",
            ):
                continue
            projection = _validate_canonical_record_value(
                member.field_id,
                member.canonical_value_bytes,
            )
            projection = projection["canonical_projection"]
            if not projection["source_observation_available"]:
                continue
            record = projection["values"]
            if member.field_id == "architecture-record":
                architecture_ids.append(record["architecture_id"])
            elif member.field_id == (
                "seccomp-status-and-filter-count-record"
            ):
                seccomp_architecture_ids.append(
                    record["architecture_id"]
                )
            else:
                elf_machine_ids.append(record["machine_id"])
    platform_bindings = tuple(
        binding
        for payload in values
        for binding in payload.subject_bindings
        if binding.subject_role_id == "linux-host-platform"
    )
    if len(platform_bindings) != 2:
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    platform_architecture_ids = {
        _validate_resource_subject_identity(
            "linux-host-platform",
            binding.canonical_identity_bytes,
        )["identity_components"]["architecture_id"]
        for binding in platform_bindings
    }
    comparable_architecture_ids = (
        set(architecture_ids)
        | set(seccomp_architecture_ids)
        | platform_architecture_ids
    )
    if (
        len(comparable_architecture_ids) != 1
        or len(set(elf_machine_ids)) > 1
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)


def build_linux_confinement_observation_payload(
    *,
    observation_id: str,
    subject_identity_table: LinuxConfinementSubjectIdentityTableV1,
    process_identity_snapshots: Tuple[
        LinuxConfinementProcessIdentitySnapshotV1, ...
    ],
    capture_window_start_monotonic_ns: int,
    capture_window_end_monotonic_ns: int,
    resource_subject_identity_bytes: Mapping[str, bytes],
    evidence_value_bytes: Mapping[str, bytes],
) -> LinuxConfinementObservationPayloadV1:
    """Build a context-bound payload; no predicate result is accepted."""

    schema = _observation_schema(observation_id)
    validate_linux_confinement_process_identity_snapshot_chain(
        process_identity_snapshots,
        subject_identity_table=subject_identity_table,
    )
    snapshot = _snapshot_for_observation(
        observation_id,
        process_identity_snapshots,
    )
    resource_roles = tuple(
        role_id
        for role_id in schema.subject_role_ids
        if _SUBJECT_KIND_BY_ROLE[role_id] != "process-role"
    )
    _validate_exact_mapping_keys(
        resource_subject_identity_bytes,
        resource_roles,
    )
    _validate_exact_mapping_keys(
        evidence_value_bytes,
        schema.raw_evidence_field_ids,
    )
    rows = _task_by_slot(snapshot)
    subject_bindings = []
    for role_id in schema.subject_role_ids:
        if _SUBJECT_KIND_BY_ROLE[role_id] == "process-role":
            task = rows[_ROLE_TO_TASK_SLOT[role_id]]
            identity = linux_confinement_kernel_task_instance_sha256(
                task,
                staging_run_binding_sha256=(
                    snapshot.staging_run_binding_sha256
                ),
                linux_platform_profile_sha256=(
                    snapshot.linux_platform_profile_sha256
                ),
                linux_boot_id_sha256=snapshot.linux_boot_id_sha256,
            )
            if identity == _ZERO_SHA256:
                _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
            raw = _ascii(identity)
        else:
            raw = _mapping_value(
                resource_subject_identity_bytes,
                role_id,
            )
        subject_bindings.append(
            LinuxConfinementSubjectBindingV1(
                subject_role_id=role_id,
                canonical_identity_bytes=raw,
                staging_run_binding_sha256=(
                    subject_identity_table.staging_run_binding_sha256
                ),
                subject_identity_table_sha256=(
                    linux_confinement_subject_identity_table_sha256(
                        subject_identity_table
                    )
                ),
                process_identity_snapshot_sha256=(
                    linux_confinement_process_identity_snapshot_sha256(
                        snapshot
                    )
                ),
            )
        )
    result = LinuxConfinementObservationPayloadV1(
        observation_id=observation_id,
        staging_run_binding_sha256=(
            subject_identity_table.staging_run_binding_sha256
        ),
        subject_identity_table_sha256=(
            linux_confinement_subject_identity_table_sha256(
                subject_identity_table
            )
        ),
        process_identity_snapshot_sha256=(
            linux_confinement_process_identity_snapshot_sha256(snapshot)
        ),
        capture_window_start_monotonic_ns=(
            capture_window_start_monotonic_ns
        ),
        capture_window_end_monotonic_ns=(
            capture_window_end_monotonic_ns
        ),
        subject_bindings=tuple(subject_bindings),
        evidence_members=tuple(
            LinuxConfinementEvidenceMemberV1(
                field_id=field_id,
                canonical_value_bytes=_mapping_value(
                    evidence_value_bytes,
                    field_id,
                ),
                staging_run_binding_sha256=(
                    subject_identity_table.staging_run_binding_sha256
                ),
                subject_identity_table_sha256=(
                    linux_confinement_subject_identity_table_sha256(
                        subject_identity_table
                    )
                ),
                process_identity_snapshot_sha256=(
                    linux_confinement_process_identity_snapshot_sha256(
                        snapshot
                    )
                ),
            )
            for field_id in schema.raw_evidence_field_ids
        ),
    )
    validate_linux_confinement_observation_payload_context(
        result,
        subject_identity_table=subject_identity_table,
        process_identity_snapshots=process_identity_snapshots,
    )
    return result


def build_linux_confinement_semantic_retained_record(
    *,
    payload: LinuxConfinementObservationPayloadV1,
    subject_identity_table: LinuxConfinementSubjectIdentityTableV1,
    process_identity_snapshots: Tuple[
        LinuxConfinementProcessIdentitySnapshotV1, ...
    ],
    capture_binding: object,
    capture_monotonic_timestamp_ns: int,
) -> object:
    """Place validated bytes in the unchanged Checkpoint-51 record type."""

    from .adapter_linux_confinement_preimage_codec import (
        LinuxConfinementCaptureBindingV1,
        LinuxConfinementRetainedRecordV1,
    )

    if type(capture_binding) is not LinuxConfinementCaptureBindingV1:
        _fail(LinuxConfinementSemanticPayloadCode.INPUT_TYPE)
    validate_linux_confinement_observation_payload_context(
        payload,
        subject_identity_table=subject_identity_table,
        process_identity_snapshots=process_identity_snapshots,
    )
    snapshot = _snapshot_for_observation(
        payload.observation_id,
        process_identity_snapshots,
    )
    table_sha256 = linux_confinement_subject_identity_table_sha256(
        subject_identity_table
    )
    if (
        type(capture_monotonic_timestamp_ns) is not int
        or capture_monotonic_timestamp_ns
        != payload.capture_window_end_monotonic_ns
        or capture_binding.staging_run_binding_sha256
        != payload.staging_run_binding_sha256
        or capture_binding.observation_subject_identity != table_sha256
        or capture_binding.policy_sha256
        != subject_identity_table.policy_sha256
        or capture_binding.linux_platform_profile_sha256
        != snapshot.linux_platform_profile_sha256
        or capture_binding.run_nonce_hex
        != subject_identity_table.run_nonce_hex
        or capture_binding.run_sequence_number
        != subject_identity_table.run_sequence_number
        or capture_binding.supervisor_epoch_id_hex
        != subject_identity_table.supervisor_epoch_id_hex
        or capture_binding.acceptance_contract_sha256
        != linux_confinement_acceptance_contract_sha256()
        or capture_binding.evidence_plan_sha256
        != linux_confinement_evidence_plan_sha256()
        or capture_binding.evidence_schema_contract_sha256
        != linux_confinement_evidence_schema_contract_sha256()
        or capture_binding.staging_protocol_contract_sha256
        != linux_confinement_staging_protocol_contract_sha256()
    ):
        _fail(LinuxConfinementSemanticPayloadCode.BINDING_MISMATCH)
    schema = _observation_schema(payload.observation_id)
    return LinuxConfinementRetainedRecordV1(
        record_kind_id="observation",
        record_id=payload.observation_id,
        lifecycle_stage_id=schema.lifecycle_stage_id,
        trusted_producer_id=schema.trusted_producer_id,
        staging_run_binding_sha256=payload.staging_run_binding_sha256,
        observation_subject_identity=table_sha256,
        capture_monotonic_timestamp_ns=capture_monotonic_timestamp_ns,
        record_artifact_type=(
            linux_confinement_observation_payload_artifact_type(
                payload.observation_id
            )
        ),
        record_canonical_bytes=(
            linux_confinement_observation_payload_bytes(payload)
        ),
    )


def _subject_schema_tree(role_id: str) -> dict:
    return {
        "context_binding_field_ids": [
            "staging_run_binding_sha256",
            "subject_identity_table_sha256",
            "process_identity_snapshot_sha256",
        ],
        "identity_schema_id": _identity_schema_id(role_id),
        "origin_authenticated": False,
        "subject_kind_id": _SUBJECT_KIND_BY_ROLE[role_id],
        "subject_role_id": role_id,
    }


def _field_schema_tree(field_id: str) -> dict:
    return {
        "comparator_id": _field_comparator_id(field_id),
        "context_binding_field_ids": [
            "staging_run_binding_sha256",
            "subject_identity_table_sha256",
            "process_identity_snapshot_sha256",
        ],
        "field_id": field_id,
        "semantic_type_id": (
            linux_confinement_evidence_field_semantic_type_id(field_id)
        ),
        "value_codec_id": _field_codec_id(field_id),
    }


def _observation_schema_tree(schema: _ObservationSchema) -> dict:
    return {
        "artifact_type": (
            linux_confinement_observation_payload_artifact_type(
                schema.observation_id
            )
        ),
        "family_id": schema.family_id,
        "lifecycle_stage_id": schema.lifecycle_stage_id,
        "observation_id": schema.observation_id,
        "predicate_id": schema.predicate_id,
        "procedure_id": schema.procedure_id,
        "raw_evidence_fields": [
            _field_schema_tree(field_id)
            for field_id in schema.raw_evidence_field_ids
        ],
        "receipt_leaf_id": schema.receipt_leaf_id,
        "snapshot_stage_id": schema.snapshot_stage_id,
        "subject_schemas": [
            _subject_schema_tree(role_id)
            for role_id in schema.subject_role_ids
        ],
        "trusted_producer_id": schema.trusted_producer_id,
    }


def linux_confinement_semantic_payload_contract_tree() -> dict:
    """Return a fresh, audit-friendly projection of every fixed schema."""

    return {
        "artifact_type": (
            LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_ARTIFACT_TYPE
        ),
        "capture_time_subject_semantics": {
            "artifact_type": (
                LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_ARTIFACT_TYPE
            ),
            "concrete_future_process_identities_in_capture_table": False,
            "digest_field_id": "observation-subject-identity",
            "process_instance_count": (
                LINUX_CONFINEMENT_EXPECTED_PROCESS_INSTANCE_COUNT
            ),
            "role_alias_edges": [
                list(edge)
                for edge in LINUX_CONFINEMENT_PROCESS_IDENTITY_ALIAS_EDGES
            ],
            "role_count": len(
                LINUX_CONFINEMENT_PROCESS_IDENTITY_ROLE_IDS
            ),
            "role_rows": _role_topology_rows_tree(),
            "semantics_id": (
                "capture-time-logical-role-slot-topology-not-kernel-"
                "identity-v1"
            ),
        },
        "digest_computation_id": (
            LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_DIGEST_COMPUTATION_ID
        ),
        "encoding_id": LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_ENCODING_ID,
        "evidence_value_codecs": {
            "bounded_octet_field_ids": list(_BOUNDED_OCTET_FIELD_IDS),
            "canonical_json_object_field_ids": [
                field_id
                for field_id in LINUX_CONFINEMENT_RAW_EVIDENCE_FIELD_IDS
                if _field_codec_id(field_id)
                == LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT
            ],
            "codec_ids": list(
                LINUX_CONFINEMENT_EVIDENCE_VALUE_CODEC_IDS
            ),
            "nul_frame_field_ids": list(_NUL_FRAME_FIELD_IDS),
            "sha256_field_ids": list(_SHA256_FIELD_IDS),
            "u64_field_ids": list(_U64_FIELD_IDS),
        },
        "record_envelope_schema": {
            "alias_transition_role_ids": {
                key: list(value)
                for key, value in _ALIAS_TRANSITION_ROLE_IDS.items()
            },
            "field_ids": list(_RECORD_ENVELOPE_FIELD_IDS),
            "native_origin_authenticated": False,
            "portable_projection_recomputed": False,
            "raw_and_projection_identities_bound": True,
        },
        "canonical_projection_schema": {
            "canonical_json_field_occurrence_count": sum(
                1
                for item in _OBSERVATION_SCHEMAS
                for field_id in item.raw_evidence_field_ids
                if _field_codec_id(field_id)
                == LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT
            ),
            "canonical_json_unique_field_count": len(
                LINUX_CONFINEMENT_CANONICAL_JSON_PROJECTION_FIELD_IDS
            ),
            "field_ids": list(_PROJECTION_FIELD_IDS),
            "native_source_projection_relation_validated": False,
            "node_kind_ids": list(
                LINUX_CONFINEMENT_PROJECTION_NODE_KIND_IDS
            ),
            "octets_encoding_id": "even-lowercase-hex-lossless-bytes-v1",
            "optional_sha256_empty_value_permitted": True,
            "path_encoding_id": (
                "even-lowercase-hex-lossless-linux-path-bytes-v1"
            ),
            "projection_registry": _projection_schema_registry_tree(),
            "projection_schema_id_prefix": (
                LINUX_CONFINEMENT_PROJECTION_SCHEMA_ID_PREFIX
            ),
            "subject_identity_ref_field_ids": list(
                _PROJECTION_SUBJECT_REF_FIELD_IDS
            ),
            "source_observation_header_schema": {
                "source_errno_id": "open-token",
                "source_observation_available": "boolean",
                "source_observation_status_id": "open-token",
            },
            "token_encoding_id": "bounded-open-ascii-string-v1",
            "tokens_may_be_empty": True,
        },
        "semantic_join_contract": {
            "common_context_joined_when_source_unavailable": True,
            "external_native_transcript_equality_validated": False,
            "field_value_join_gate": (
                "source_observation_available-is-true"
            ),
            "join_rows": [
                {
                    "description": description,
                    "join_id": join_id,
                    "scope_id": scope_id,
                }
                for join_id, scope_id, description in _SEMANTIC_JOIN_ROWS
            ],
            "native_source_projection_relation_validated": False,
            "policy_bytes_accepted_by_validator": False,
            "policy_value_equality_evaluated": False,
            "source_status_caller_supplied_and_unverified": True,
        },
        "fixed_counts": {
            "observation_count": len(LINUX_CONFINEMENT_OBSERVATION_IDS),
            "process_role_count": len(
                LINUX_CONFINEMENT_PROCESS_IDENTITY_ROLE_IDS
            ),
            "raw_evidence_field_occurrence_count": sum(
                len(item.raw_evidence_field_ids)
                for item in _OBSERVATION_SCHEMAS
            ),
            "raw_evidence_unique_field_count": len(
                LINUX_CONFINEMENT_RAW_EVIDENCE_FIELD_IDS
            ),
            "semantic_join_count": len(
                LINUX_CONFINEMENT_SEMANTIC_JOIN_IDS
            ),
            "snapshot_count": len(
                LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_STAGE_IDS
            ),
            "subject_role_count": len(
                LINUX_CONFINEMENT_SUBJECT_ROLE_IDS
            ),
            "task_slot_count": len(LINUX_CONFINEMENT_TASK_SLOT_IDS),
        },
        "format_version": "1",
        "implementation_status_id": (
            LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_IMPLEMENTATION_STATUS
        ),
        "nonclaims": _false_nonclaims(),
        "observation_family_ids": list(
            LINUX_CONFINEMENT_OBSERVATION_FAMILY_IDS
        ),
        "observation_schemas": [
            _observation_schema_tree(schema)
            for schema in _OBSERVATION_SCHEMAS
        ],
        "predicate_evaluation_status_id": (
            LINUX_CONFINEMENT_PREDICATE_EVALUATION_STATUS
        ),
        "process_identity_snapshot_schema": {
            "artifact_type": (
                LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_ARTIFACT_TYPE
            ),
            "predecessor_chain_required": True,
            "producer_authority_record_is_authenticated_by_portable_code": (
                False
            ),
            "snapshot_expected_state": {
                stage_id: {
                    slot_id: list(state)
                    for slot_id, state in _SNAPSHOT_EXPECTED_STATE[
                        stage_id
                    ].items()
                }
                for stage_id in (
                    LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_STAGE_IDS
                )
            },
            "snapshot_stage_ids": list(
                LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_STAGE_IDS
            ),
            "task_parent_slots": dict(_TASK_PARENT_SLOTS),
            "task_pidfd_acquisition_method_ids": dict(
                _TASK_PIDFD_METHODS
            ),
            "task_reaper_roles": dict(_TASK_REAPER_ROLES),
            "task_slot_ids": list(LINUX_CONFINEMENT_TASK_SLOT_IDS),
            "trusted_producer_ids": dict(
                _SNAPSHOT_TRUSTED_PRODUCER_IDS
            ),
        },
        "observation_capture_window_rules": {
            "cross_stage_run_transcript": (
                "start<=pre-stage1-snapshot<pre-stage2-snapshot"
                "<=end<=postrun-snapshot"
            ),
            "cross_stage_through_postrun": (
                "start<=pre-stage1-snapshot<pre-stage2-snapshot"
                "<postrun-snapshot==end"
            ),
            "postrun_cleanup": (
                "pre-stage2-snapshot<=start<=end<=postrun-snapshot"
            ),
            "pre_stage1": "start<=end<=pre-stage1-snapshot",
            "pre_stage2": (
                "pre-stage1-snapshot<=start<=end<=pre-stage2-snapshot"
            ),
        },
        "resource_limits": {
            "maximum_contract_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_BYTES
            ),
            "maximum_json_depth": (
                MAXIMUM_LINUX_CONFINEMENT_JSON_DEPTH
            ),
            "maximum_json_items": (
                MAXIMUM_LINUX_CONFINEMENT_JSON_ITEMS
            ),
            "maximum_json_string_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_JSON_STRING_BYTES
            ),
            "maximum_observation_payload_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_OBSERVATION_PAYLOAD_BYTES
            ),
            "maximum_record_projection_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_RECORD_PROJECTION_BYTES
            ),
            "maximum_record_raw_source_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_RECORD_RAW_SOURCE_BYTES
            ),
            "maximum_semantic_value_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES
            ),
            "maximum_semantic_token_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_TOKEN_BYTES
            ),
            "maximum_snapshot_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_BYTES
            ),
            "maximum_subject_identity_table_bytes": (
                MAXIMUM_LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_BYTES
            ),
        },
        "aggregate_observation_set_joins": {
            "architecture_record_count": 2,
            "available_architecture_records_equal_platform_identity": (
                True
            ),
            "available_elf_machine_identifiers_equal": True,
            "available_seccomp_architecture_equal_platform_identity": (
                True
            ),
            "exact_observation_order_required": True,
            "observation_ids": list(
                LINUX_CONFINEMENT_AGGREGATE_OBSERVATION_IDS
            ),
            "repeated_resource_stable_components_equal": True,
            "unavailable_projection_values_excluded_from_value_joins": (
                True
            ),
        },
        "subject_kind_by_role": dict(_SUBJECT_KIND_BY_ROLE),
        "resource_identity_envelope_schema": {
            "component_field_ids_by_kind": {
                key: list(value)
                for key, value in (
                    _RESOURCE_COMPONENT_FIELDS_BY_KIND.items()
                )
            },
            "field_ids": list(_RESOURCE_IDENTITY_FIELD_IDS),
            "kernel_object_type_by_role": dict(
                _KERNEL_OBJECT_TYPE_BY_ROLE
            ),
            "namespace_type_by_role": dict(_NAMESPACE_TYPE_BY_ROLE),
            "native_origin_authenticated": False,
            "security_object_type_by_role": dict(
                _SECURITY_OBJECT_TYPE_BY_ROLE
            ),
        },
        "validation_scope_id": (
            LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_VALIDATION_SCOPE
        ),
        "verifier_id": (
            LINUX_CONFINEMENT_IMPLEMENTATION_SEPARATED_VERIFIER_ID
        ),
    }


def linux_confinement_semantic_payload_contract_bytes() -> bytes:
    return _canonical_json(
        linux_confinement_semantic_payload_contract_tree(),
        maximum=(
            MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_BYTES
        ),
    )


def linux_confinement_semantic_payload_contract_sha256() -> str:
    return _domain_sha256(
        LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_DIGEST_DOMAIN,
        linux_confinement_semantic_payload_contract_bytes(),
    )


def parse_linux_confinement_semantic_payload_contract(
    value: bytes,
) -> dict:
    parsed = _parse_canonical_json(
        value,
        maximum=(
            MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_BYTES
        ),
    )
    if parsed != linux_confinement_semantic_payload_contract_tree():
        _fail(LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT)
    return parsed


def _validate_contract_coherence() -> None:
    _validated_role_table_catalog()
    family_members = _FAMILY_F1 + _FAMILY_F2 + _FAMILY_F3 + _FAMILY_F4
    all_fields = tuple(
        field_id
        for item in _OBSERVATION_SCHEMAS
        for field_id in item.raw_evidence_field_ids
    )
    canonical_json_fields = tuple(
        field_id
        for field_id in all_fields
        if _field_codec_id(field_id)
        == LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT
    )
    digest_named_fields = {
        field_id
        for field_id in all_fields
        if (
            field_id.endswith("-sha256")
            or field_id.endswith("-digest")
            or field_id.endswith("-leaf")
        )
    }
    lifecycle_observation_id = (
        "pidfd-bound-observer-helper-monitor-init-application-"
        "identities-subreaper-adoption-and-reap-observed"
    )
    lifecycle_roles = (
        "userns-map-observation-helper",
        "unprivileged-preexec-launcher",
        "bubblewrap-monitor",
        "bubblewrap-setup-child",
        "sandbox-pid1-reaper",
        "application",
        "privileged-supervisor",
    )
    if (
        len(LINUX_CONFINEMENT_OBSERVATION_IDS) != 24
        or len(set(LINUX_CONFINEMENT_OBSERVATION_IDS)) != 24
        or len(family_members) != 24
        or len(set(family_members)) != 24
        or set(family_members) != set(LINUX_CONFINEMENT_OBSERVATION_IDS)
        or len(LINUX_CONFINEMENT_AGGREGATE_OBSERVATION_IDS) != 24
        or len(set(LINUX_CONFINEMENT_AGGREGATE_OBSERVATION_IDS)) != 24
        or set(LINUX_CONFINEMENT_AGGREGATE_OBSERVATION_IDS)
        != set(LINUX_CONFINEMENT_OBSERVATION_IDS)
        or len(all_fields) != 112
        or len(LINUX_CONFINEMENT_RAW_EVIDENCE_FIELD_IDS) != 111
        or len(canonical_json_fields) != 85
        or len(set(canonical_json_fields)) != 84
        or canonical_json_fields.count("architecture-record") != 2
        or any(
            canonical_json_fields.count(field_id) != 1
            for field_id in set(canonical_json_fields)
            if field_id != "architecture-record"
        )
        or set(canonical_json_fields)
        != set(_PROJECTION_VALUE_SCHEMA_BY_FIELD)
        or len(_PROJECTION_VALUE_SCHEMA_BY_FIELD) != 84
        or len(_PROJECTION_FIELD_IDS) != 11
        or len(LINUX_CONFINEMENT_SEMANTIC_JOIN_IDS) != 11
        or len(set(LINUX_CONFINEMENT_SEMANTIC_JOIN_IDS)) != 11
        or any(
            node.node_kind_id != "object"
            for node in _PROJECTION_VALUE_SCHEMA_BY_FIELD.values()
        )
        or digest_named_fields != set(_SHA256_FIELD_IDS)
        or set(LINUX_CONFINEMENT_SUBJECT_ROLE_IDS)
        != set(_SUBJECT_KIND_BY_ROLE)
        or len(LINUX_CONFINEMENT_SUBJECT_ROLE_IDS) != 28
        or _OBSERVATION_SCHEMA_BY_ID[
            lifecycle_observation_id
        ].subject_role_ids
        != lifecycle_roles
        or set(LINUX_CONFINEMENT_PROCESS_IDENTITY_ROLE_IDS)
        != {
            role_id
            for role_id, kind_id in _SUBJECT_KIND_BY_ROLE.items()
            if kind_id == "process-role"
        }
        or any(
            len(item.subject_role_ids) == 0
            or len(item.raw_evidence_field_ids) == 0
            or len(set(item.subject_role_ids))
            != len(item.subject_role_ids)
            or len(set(item.raw_evidence_field_ids))
            != len(item.raw_evidence_field_ids)
            for item in _OBSERVATION_SCHEMAS
        )
    ):
        raise RuntimeError(
            _ERROR_MESSAGES[
                LinuxConfinementSemanticPayloadCode.CONTRACT_DRIFT
            ]
        )


_validate_contract_coherence()


__all__ = [
    "LINUX_CONFINEMENT_CODEC_BOUNDED_OCTETS",
    "LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT",
    "LINUX_CONFINEMENT_CODEC_NUL_FRAME",
    "LINUX_CONFINEMENT_CODEC_SHA256_HEX_ASCII",
    "LINUX_CONFINEMENT_CODEC_U64BE",
    "LINUX_CONFINEMENT_AGGREGATE_OBSERVATION_IDS",
    "LINUX_CONFINEMENT_EVIDENCE_MEMBER_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_EVIDENCE_VALUE_CODEC_IDS",
    "LINUX_CONFINEMENT_EXPECTED_PROCESS_INSTANCE_COUNT",
    "LINUX_CONFINEMENT_KERNEL_TASK_INSTANCE_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_OBSERVATION_FAMILY_IDS",
    "LINUX_CONFINEMENT_OBSERVATION_IDS",
    "LINUX_CONFINEMENT_OBSERVATION_PAYLOAD_ARTIFACT_TYPE_PREFIX",
    "LINUX_CONFINEMENT_PREDICATE_EVALUATION_STATUS",
    "LINUX_CONFINEMENT_PROCESS_IDENTITY_ALIAS_EDGES",
    "LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_STAGE_IDS",
    "LINUX_CONFINEMENT_CANONICAL_JSON_PROJECTION_FIELD_IDS",
    "LINUX_CONFINEMENT_PROJECTION_NODE_KIND_IDS",
    "LINUX_CONFINEMENT_PROJECTION_SCHEMA_ID_PREFIX",
    "LINUX_CONFINEMENT_RAW_EVIDENCE_FIELD_IDS",
    "LINUX_CONFINEMENT_SEMANTIC_JOIN_IDS",
    "LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_DIGEST_COMPUTATION_ID",
    "LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_ENCODING_ID",
    "LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_IMPLEMENTATION_STATUS",
    "LINUX_CONFINEMENT_IMPLEMENTATION_SEPARATED_VERIFIER_ID",
    "LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_VALIDATION_SCOPE",
    "LINUX_CONFINEMENT_SNAPSHOT_STAGE_POSTRUN",
    "LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE1",
    "LINUX_CONFINEMENT_SNAPSHOT_STAGE_PRE_STAGE2",
    "LINUX_CONFINEMENT_SUBJECT_BINDING_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_SUBJECT_ROLE_IDS",
    "LINUX_CONFINEMENT_TASK_SLOT_IDS",
    "LinuxConfinementEvidenceMemberV1",
    "LinuxConfinementObservationPayloadV1",
    "LinuxConfinementProcessIdentitySnapshotV1",
    "LinuxConfinementSemanticPayloadCode",
    "LinuxConfinementSemanticPayloadError",
    "LinuxConfinementSubjectBindingV1",
    "LinuxConfinementSubjectIdentityTableV1",
    "LinuxConfinementTaskIdentityV1",
    "MAXIMUM_LINUX_CONFINEMENT_OBSERVATION_PAYLOAD_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_JSON_STRING_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_PROCESS_IDENTITY_SNAPSHOT_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_RECORD_PROJECTION_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_RECORD_RAW_SOURCE_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_PAYLOAD_CONTRACT_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VALUE_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_SUBJECT_IDENTITY_TABLE_BYTES",
    "build_linux_confinement_canonical_record_value",
    "build_linux_confinement_canonical_projection",
    "build_linux_confinement_observation_payload",
    "build_linux_confinement_resource_subject_identity_bytes",
    "build_linux_confinement_semantic_retained_record",
    "linux_confinement_evidence_field_codec_id",
    "linux_confinement_evidence_field_parser_id",
    "linux_confinement_evidence_field_semantic_type_id",
    "linux_confinement_kernel_task_instance_sha256",
    "linux_confinement_observation_payload_artifact_type",
    "linux_confinement_observation_payload_bytes",
    "linux_confinement_observation_payload_sha256",
    "linux_confinement_process_identity_snapshot_bytes",
    "linux_confinement_process_identity_snapshot_sha256",
    "linux_confinement_semantic_payload_contract_bytes",
    "linux_confinement_semantic_payload_contract_sha256",
    "linux_confinement_semantic_payload_contract_tree",
    "linux_confinement_subject_identity_table_bytes",
    "linux_confinement_subject_identity_table_sha256",
    "parse_linux_confinement_observation_payload",
    "parse_linux_confinement_process_identity_snapshot",
    "parse_linux_confinement_semantic_payload_contract",
    "parse_linux_confinement_subject_identity_table",
    "validate_linux_confinement_observation_payload_context",
    "validate_linux_confinement_observation_payload_set",
    "validate_linux_confinement_process_identity_snapshot_chain",
]
