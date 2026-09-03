"""Implementation-separated verifier for Linux-observation semantic payloads.

This module intentionally does not import the companion semantic-payload
module.  It freezes the V1 topology, snapshot, observation, subject, and
evidence-member schemas locally and parses only caller-supplied canonical
bytes.  Public evidence-plan, acceptance, evidence-schema, and staging
contracts are used only as external anchors and import-time drift checks.

Successful verification establishes canonical shape, byte identities,
declared codecs, record metadata, topology, snapshot-chain, and run-binding
consistency.  It does not establish Linux execution, kernel semantics,
producer origin, evidence custody, policy-predicate truth, confinement,
release safety, hostile-control success, teardown, or decision eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Final, Tuple

from .adapter_linux_confinement_acceptance import (
    LINUX_CONFINEMENT_REQUIRED_OBSERVATION_IDS,
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


LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_RESULT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-semantic-implementation-separated-"
    "verification-result.v1"
)
LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_RESULT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_RESULT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_IMPLEMENTATION_SEPARATED_VERIFIER_ID: Final = (
    "heterodiff.adapter.linux-confinement-semantic-payload-"
    "implementation-separated-verifier.v1"
)
LINUX_CONFINEMENT_SEMANTIC_VERIFIER_IMPLEMENTATION_STATUS: Final = (
    "IMPLEMENTATION_SEPARATED_PORTABLE_SEMANTIC_BYTE_VERIFIER_IMPLEMENTED"
)
LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_STATUS: Final = (
    "SUPPLIED_SCHEMA_CODEC_HASH_CONTEXT_RESOURCE_TASK_RUN_AND_INTERNAL_"
    "IDENTITY_BINDINGS_VALIDATED"
)
MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_RESULT_BYTES: Final = 64 * 1024

_SUBJECT_TABLE_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-subject-role-topology-table.v1"
)
_SUBJECT_TABLE_DIGEST_DOMAIN: Final = _SUBJECT_TABLE_ARTIFACT_TYPE
_SNAPSHOT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-process-identity-snapshot.v1"
)
_SNAPSHOT_DIGEST_DOMAIN: Final = _SNAPSHOT_ARTIFACT_TYPE
_TASK_INSTANCE_DIGEST_DOMAIN: Final = (
    "heterodiff.adapter.linux-confinement-kernel-task-instance.v1"
)
_OBSERVATION_ARTIFACT_TYPE_PREFIX: Final = (
    "heterodiff.adapter.linux-confinement-observation-payload."
)
_SUBJECT_BINDING_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-subject-binding.v1"
)
_EVIDENCE_MEMBER_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-evidence-member.v1"
)
_SEMANTIC_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-semantic-payload-contract.v1"
)
_SEMANTIC_CONTRACT_DIGEST_DOMAIN: Final = _SEMANTIC_CONTRACT_ARTIFACT_TYPE
_V1_SEMANTIC_CONTRACT_SHA256: Final = (
    "11a2e7890039a1bb4ca19a571e3a3772a750afb24af24e01e5f3928c9092804e"
)
_SEMANTIC_IMPLEMENTATION_STATUS: Final = (
    "PORTABLE_CANONICAL_SCHEMA_AND_CONTEXT_BINDING_IMPLEMENTED"
)
_VALIDATION_SCOPE_ID: Final = (
    "SUPPLIED_SCHEMA_CODEC_HASH_CONTEXT_RESOURCE_TASK_RUN_AND_INTERNAL_"
    "IDENTITY_BINDINGS_ONLY"
)
_PREDICATE_STATUS_ID: Final = "NOT_EVALUATED_BY_PORTABLE_SCHEMA_VALIDATOR"
_ENCODING_ID: Final = "canonical-ascii-json-sorted-keys-no-whitespace-v1"
_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-bytes-v1"
)
_STAGING_RUN_BINDING_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-staging-run-binding.v1"
)

_CODEC_SHA256: Final = "sha256-lowercase-hex-ascii-v1"
_CODEC_U64: Final = "unsigned-u64be-v1"
_CODEC_NUL: Final = "nul-terminated-ordered-octet-strings-v1"
_CODEC_RECORD: Final = "canonical-ascii-json-object-v1"
_CODEC_OCTETS: Final = "bounded-opaque-octets-v1"
_CODEC_IDS: Final = (
    _CODEC_SHA256,
    _CODEC_U64,
    _CODEC_NUL,
    _CODEC_RECORD,
    _CODEC_OCTETS,
)

_STAGES: Final = ("PRE_STAGE1", "PRE_STAGE2", "POSTRUN")
_TASK_SLOTS: Final = (
    "application-task",
    "helper-task",
    "monitor-task",
    "pid1-task",
    "supervisor-task",
)
_PROCESS_ROLES: Final = (
    "application",
    "bubblewrap-monitor",
    "bubblewrap-setup-child",
    "privileged-supervisor",
    "sandbox-pid1-reaper",
    "unprivileged-preexec-launcher",
    "userns-map-observation-helper",
)
_FAMILY_IDS: Final = (
    "F1_ARTIFACT_PLATFORM_IDENTITY",
    "F2_PIDFD_BOUND_STOPPED_STATE",
    "F3_CLOSED_RESOURCE_TOPOLOGY",
    "F4_BOUND_MONOTONIC_EVENT_GRAPH",
)

_MAX_TOKEN_BYTES: Final = 512
_MAX_VALUE_BYTES: Final = 256 * 1024
_MAX_RECORD_RAW_SOURCE_BYTES: Final = 32 * 1024
_MAX_RECORD_PROJECTION_BYTES: Final = 128 * 1024
_MAX_PAYLOAD_BYTES: Final = 2 * 1024 * 1024
_MAX_SUBJECT_TABLE_BYTES: Final = 128 * 1024
_MAX_SNAPSHOT_BYTES: Final = 256 * 1024
_MAX_CONTRACT_BYTES: Final = 512 * 1024
_MAX_JSON_DEPTH: Final = 16
_MAX_JSON_ITEMS: Final = 8192
_MAX_JSON_STRING_BYTES: Final = 512 * 1024
_MAX_RUN_SEQUENCE: Final = 4095
_ZERO_SHA256: Final = "0" * 64
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$")

_FALSE_NONCLAIMS: Final = MappingProxyType(
    {
        "evidence_custody_authenticated": False,
        "hostile_controls_executed": False,
        "kernel_semantics_validated": False,
        "linux_confinement_established": False,
        "linux_execution_observed": False,
        "policy_predicate_evaluated": False,
        "producer_origin_authenticated": False,
        "release_safety_established": False,
    }
)

_ROLE_ROW_FIELDS: Final = (
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
_ROLE_TO_SLOT: Final = MappingProxyType({row[0]: row[1] for row in _ROLE_ROWS})
_TASK_PARENT: Final = MappingProxyType(
    {
        "application-task": "pid1-task",
        "helper-task": "supervisor-task",
        "monitor-task": "supervisor-task",
        "pid1-task": "monitor-task",
        "supervisor-task": "",
    }
)
_TASK_REAPER: Final = MappingProxyType(
    {
        "application-task": "sandbox-pid1-reaper",
        "helper-task": "privileged-supervisor",
        "monitor-task": "privileged-supervisor",
        "pid1-task": "privileged-supervisor",
        "supervisor-task": "",
    }
)
_TASK_PIDFD_METHOD: Final = MappingProxyType(
    {
        "application-task": ("sandbox-pid1-clone-supervisor-pidfd-bind-v1"),
        "helper-task": "clone3-clone-pidfd-v1",
        "monitor-task": "clone3-clone-pidfd-v1",
        "pid1-task": "pidfd-open-proc-handle-bound-v1",
        "supervisor-task": "external-custody-reference-v1",
    }
)
_SNAPSHOT_STATE: Final = MappingProxyType(
    {
        "PRE_STAGE1": {
            "application-task": ("NOT_CREATED", ""),
            "helper-task": (
                "WAIT_REAPED",
                "userns-map-observation-helper",
            ),
            "monitor-task": ("LIVE", "bubblewrap-monitor"),
            "pid1-task": ("BLOCKED", "bubblewrap-setup-child"),
            "supervisor-task": ("LIVE", "privileged-supervisor"),
        },
        "PRE_STAGE2": {
            "application-task": ("PIDFD_BOUND_STOPPED", "application"),
            "helper-task": (
                "WAIT_REAPED",
                "userns-map-observation-helper",
            ),
            "monitor-task": ("LIVE", "bubblewrap-monitor"),
            "pid1-task": ("LIVE", "sandbox-pid1-reaper"),
            "supervisor-task": ("LIVE", "privileged-supervisor"),
        },
        "POSTRUN": {
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
_SNAPSHOT_PRODUCER: Final = MappingProxyType(
    {
        "PRE_STAGE1": ("privileged-supervisor-process-identity-observer-v1"),
        "PRE_STAGE2": ("privileged-supervisor-process-identity-observer-v1"),
        "POSTRUN": ("dedicated-subreaper-supervisor-process-observer-v1"),
    }
)

_SUBJECT_KIND: Final = MappingProxyType(
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
_SHA256_FIELDS: Final = (
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
_U64_FIELDS: Final = (
    "bootstrap-source-byte-count",
    "dependency-lock-byte-count",
)
_NUL_FIELDS: Final = (
    "argv-nul-frame-bytes",
    "environment-nul-frame-bytes",
)
_OCTET_FIELDS: Final = (
    "cgroup-controller-file-bytes",
    "cgroup-events-before-release-bytes",
    "cgroup-events-final-bytes",
    "supervisor-dependency-inventory-bytes",
)

_OBSERVATION_METADATA: Final = (
    (
        "application-argv-environment-cwd-umask-matched",
        "F2_PIDFD_BOUND_STOPPED_STATE",
        "PRE_STAGE2",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-application-runtime-surface-observation-v1",
        "exact-application-runtime-surface-equality-v1",
        "pre-adapter-release-observations-matched",
        ("application",),
        (
            "argv-nul-frame-bytes",
            "environment-nul-frame-bytes",
            "cwd-mount-and-inode-record",
            "umask-octal-record",
        ),
    ),
    (
        "backend-static-sealed-executable-identity-matched",
        "F1_ARTIFACT_PLATFORM_IDENTITY",
        "PRE_STAGE1",
        "pre-backend-exec",
        "privileged-supervisor-artifact-observer-v1",
        "sealed-backend-memfd-and-elf-observation-v1",
        "static-sealed-backend-exact-policy-match-v1",
        "policy-identities-matched",
        (
            "backend-executable-memfd",
            "unprivileged-preexec-launcher",
        ),
        (
            "backend-memfd-sha256",
            "backend-memfd-stat-record",
            "backend-memfd-flags-record",
            "backend-memfd-seals-record",
            "backend-elf-program-header-record",
            "backend-elf-dynamic-section-record",
        ),
    ),
    (
        "capability-securebits-dumpability-profile-matched",
        "F2_PIDFD_BOUND_STOPPED_STATE",
        "PRE_STAGE2",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-credential-profile-observation-v1",
        "exact-zero-capability-securebits-dumpability-match-v1",
        "pre-adapter-release-observations-matched",
        ("application",),
        (
            "capability-set-record",
            "securebits-mask-record",
            "dumpable-record",
            "uid-gid-and-groups-record",
        ),
    ),
    (
        "cgroup-v2-controller-values-matched-before-release",
        "F3_CLOSED_RESOURCE_TOPOLOGY",
        "PRE_STAGE2",
        "pre-stage2-application-stopped",
        "privileged-supervisor-cgroup-observer-v1",
        "host-owned-cgroup-v2-controller-observation-v1",
        "exact-cgroup-controller-and-membership-match-v1",
        "named-filesystem-network-process-resource-controls-observed",
        (
            "sandbox-cgroup-v2-leaf",
            "application",
            "sandbox-pid1-reaper",
        ),
        (
            "cgroup-controller-file-bytes",
            "cgroup-process-membership-record",
            "cgroup-events-before-release-bytes",
        ),
    ),
    (
        "cgroup-v2-leaf-owned-by-supervisor",
        "F3_CLOSED_RESOURCE_TOPOLOGY",
        "PRE_STAGE1",
        "pre-stage1-setup-blocked",
        "privileged-supervisor-cgroup-observer-v1",
        "cgroup-v2-leaf-ownership-and-delegation-observation-v1",
        "supervisor-exclusive-cgroup-leaf-custody-v1",
        "named-filesystem-network-process-resource-controls-observed",
        (
            "privileged-supervisor",
            "sandbox-cgroup-v2-leaf",
        ),
        (
            "cgroup-leaf-stat-record",
            "cgroup-leaf-owner-record",
            "cgroup-delegation-record",
        ),
    ),
    (
        "dependency-lock-identity-matched",
        "F1_ARTIFACT_PLATFORM_IDENTITY",
        "PRE_STAGE1",
        "pre-first-child-artifact-validation",
        "privileged-supervisor-artifact-observer-v1",
        "dependency-lock-content-identity-observation-v1",
        "dependency-lock-digest-equals-policy-identity-v1",
        "policy-identities-matched",
        ("sandbox-dependency-lock",),
        (
            "dependency-lock-byte-count",
            "dependency-lock-plain-sha256",
            "dependency-lock-domain-sha256",
        ),
    ),
    (
        "descriptor-inventory-and-stdio-types-closed-before-adapter-import",
        "F3_CLOSED_RESOURCE_TOPOLOGY",
        "PRE_STAGE2",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-descriptor-inventory-observation-v1",
        "exact-closed-fd-kernel-object-contract-match-v1",
        "pre-adapter-release-observations-matched",
        (
            "application",
            "supervisor-stdio-peers",
        ),
        (
            "application-fd-inventory-record",
            "fd-kernel-object-stat-records",
            "fd-access-flags-and-offset-records",
            "fd-cloexec-and-inheritance-records",
            "stdio-isatty-records",
            "supervisor-peer-custody-records",
        ),
    ),
    (
        (
            "exact-two-level-uid-gid-maps-composition-empty-"
            "supplementary-groups-and-setgroups-denial-matched"
        ),
        "F3_CLOSED_RESOURCE_TOPOLOGY",
        "PRE_STAGE1",
        "pre-stage1-setup-blocked",
        "privileged-supervisor-and-userns-observer-v1",
        "two-level-userns-map-and-group-observation-v1",
        "exact-two-level-map-composition-and-group-state-match-v1",
        "pre-adapter-release-observations-matched",
        (
            "bubblewrap-setup-child",
            "intermediate-user-namespace",
            "final-user-namespace",
        ),
        (
            "namespace-inode-parent-chain-record",
            "host-view-final-uid-gid-map-record",
            "intermediate-view-map-records",
            "setgroups-state-records",
            "application-supplementary-group-record",
            "observer-adoption-and-reap-record",
        ),
    ),
    (
        "immutable-runtime-rootfs-identity-matched",
        "F1_ARTIFACT_PLATFORM_IDENTITY",
        "PRE_STAGE1",
        "pre-stage1-setup-blocked",
        "privileged-supervisor-mount-observer-v1",
        "content-bound-rootfs-and-old-root-observation-v1",
        "immutable-rootfs-content-and-mount-identity-match-v1",
        "policy-identities-matched",
        (
            "runtime-rootfs",
            "bubblewrap-setup-child-mount-namespace",
        ),
        (
            "rootfs-image-sha256",
            "rootfs-manifest-sha256",
            "root-mount-stat-and-flags-record",
            "old-root-handle-absence-record",
        ),
    ),
    (
        "landlock-abi-and-ruleset-matched",
        "F2_PIDFD_BOUND_STOPPED_STATE",
        "PRE_STAGE2",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "bootstrap-landlock-installation-evidence-observation-v1",
        "exact-landlock-abi-ruleset-and-installation-match-v1",
        "pre-adapter-release-observations-matched",
        (
            "application",
            "adapter-stage-landlock-ruleset",
        ),
        (
            "landlock-queried-abi-record",
            "landlock-ruleset-sha256",
            "landlock-install-return-record",
            "landlock-bootstrap-transcript-leaf",
        ),
    ),
    (
        "linux-platform-profile-matched",
        "F1_ARTIFACT_PLATFORM_IDENTITY",
        "PRE_STAGE1",
        "pre-first-child-artifact-validation",
        "privileged-supervisor-platform-observer-v1",
        "linux-kernel-boot-and-feature-profile-observation-v1",
        "exact-linux-platform-profile-match-v1",
        "approved-linux-platform-profile-matched",
        ("linux-host-platform",),
        (
            "architecture-record",
            "kernel-release-and-build-record",
            "boot-configuration-digest",
            "linux-security-feature-probe-record",
            "platform-profile-sha256",
        ),
    ),
    (
        "mount-inventory-and-write-surface-matched",
        "F3_CLOSED_RESOURCE_TOPOLOGY",
        "PRE_STAGE2",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-mountinfo-and-write-surface-observation-v1",
        "exact-mount-topology-and-single-write-surface-match-v1",
        "named-filesystem-network-process-resource-controls-observed",
        ("application-mount-namespace",),
        (
            "canonical-mountinfo-record",
            "mount-propagation-record",
            "writable-path-inventory-record",
            "device-mount-flags-record",
            "forbidden-mount-type-absence-record",
        ),
    ),
    (
        "namespace-identities-distinct-before-release",
        "F3_CLOSED_RESOURCE_TOPOLOGY",
        "PRE_STAGE2",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-seven-namespace-identity-observation-v1",
        "seven-required-namespaces-distinct-from-host-and-each-other-v1",
        "pre-adapter-release-observations-matched",
        (
            "application",
            "linux-host-platform",
        ),
        (
            "application-namespace-inode-records",
            "host-namespace-inode-records",
            "namespace-parentage-record",
        ),
    ),
    (
        "network-interface-and-route-inventory-matched",
        "F3_CLOSED_RESOURCE_TOPOLOGY",
        "PRE_STAGE2",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-network-namespace-inventory-observation-v1",
        "loopback-only-no-external-route-network-inventory-match-v1",
        "named-filesystem-network-process-resource-controls-observed",
        ("application-network-namespace",),
        (
            "network-interface-record",
            "ipv4-route-record",
            "ipv6-route-record",
            "network-namespace-inode-record",
        ),
    ),
    (
        "no-new-privileges-observed-before-release",
        "F2_PIDFD_BOUND_STOPPED_STATE",
        "PRE_STAGE2",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-no-new-privileges-observation-v1",
        "no-new-privileges-exactly-one-v1",
        "pre-adapter-release-observations-matched",
        ("application",),
        ("no-new-privileges-status-record",),
    ),
    (
        (
            "nonce-generation-nonreuse-and-readiness-release-"
            "transcript-matched"
        ),
        "F4_BOUND_MONOTONIC_EVENT_GRAPH",
        "POSTRUN",
        "cross-stage-run-transcript",
        "privileged-supervisor-transcript-producer-v1",
        (
            "nonce-registry-pidfd-blocked-barrier-ready-and-release-"
            "state-machine-observation-v1"
        ),
        (
            "nonce-freshness-pidfd-bound-exact-blocked-barrier-read-"
            "ready-frame-stop-stdout-drain-and-release-order-match-v1"
        ),
        "pre-adapter-release-observations-matched",
        (
            "privileged-supervisor",
            "bubblewrap-setup-child",
            "application",
            "stage1-barrier",
            "stage2-pidfd-release",
        ),
        (
            "getrandom-call-record",
            "nonce-registry-insertion-record",
            "run-sequence-record",
            "bubblewrap-child-pid-status-record",
            "stage1-barrier-pipe-kernel-object-identity-record",
            "pidfd-bound-stage1-barrier-read-block-record",
            "ready-frame-bytes-and-chunk-record",
            "application-stop-and-pidfd-record",
            "PRE_RELEASE_STDOUT_DRAINED-event-record",
            "pre-release-stdout-drain-to-eagain-record",
            "pre-release-stdout-buffered-byte-count-zero-record",
            "stage1-and-stage2-release-record",
        ),
    ),
    (
        (
            "pidfd-bound-observer-helper-monitor-init-application-"
            "identities-subreaper-adoption-and-reap-observed"
        ),
        "F4_BOUND_MONOTONIC_EVENT_GRAPH",
        "POSTRUN",
        "cross-stage-through-postrun",
        "dedicated-subreaper-supervisor-process-observer-v1",
        "pidfd-role-parentage-adoption-and-reap-observation-v1",
        (
            "exact-role-pidfd-launcher-and-setup-child-lifetimes-"
            "parentage-aliases-adoption-and-reap-chain-match-v1"
        ),
        "postrun-cgroup-quiescence-observed",
        (
            "userns-map-observation-helper",
            "unprivileged-preexec-launcher",
            "bubblewrap-monitor",
            "bubblewrap-setup-child",
            "sandbox-pid1-reaper",
            "application",
            "privileged-supervisor",
        ),
        (
            "clone3-pidfd-acquisition-records",
            "role-process-identity-records",
            "parentage-and-adoption-records",
            "unprivileged-preexec-launcher-parentage-record",
            (
                "unprivileged-preexec-launcher-lifetime-and-exec-"
                "transition-record"
            ),
            (
                "unprivileged-preexec-launcher-to-monitor-same-pid-"
                "exec-and-reap-record"
            ),
            "bubblewrap-setup-child-pidfd-acquisition-record",
            "bubblewrap-setup-child-parentage-record",
            "bubblewrap-setup-child-lifetime-record",
            (
                "bubblewrap-setup-child-to-sandbox-pid1-same-host-"
                "pid-lifecycle-transition-record"
            ),
            "bubblewrap-setup-child-exit-adoption-and-reap-record",
            "wait-reap-status-records",
            "subreaper-setting-and-child-inventory-record",
        ),
    ),
    (
        "rlimit-profile-matched-before-release",
        "F2_PIDFD_BOUND_STOPPED_STATE",
        "PRE_STAGE2",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-rlimit-profile-observation-v1",
        "exact-soft-and-hard-rlimit-profile-match-v1",
        "pre-adapter-release-observations-matched",
        ("application",),
        ("soft-and-hard-rlimit-records",),
    ),
    (
        "sandbox-bootstrap-identity-matched",
        "F1_ARTIFACT_PLATFORM_IDENTITY",
        "PRE_STAGE1",
        "pre-first-child-artifact-validation",
        "privileged-supervisor-artifact-observer-v1",
        "staging-bootstrap-source-and-closure-identity-observation-v1",
        "bootstrap-source-and-execution-closure-policy-match-v1",
        "policy-identities-matched",
        (
            "staging-bootstrap",
            "bootstrap-execution-closure",
        ),
        (
            "bootstrap-source-byte-count",
            "bootstrap-source-sha256",
            "bootstrap-execution-closure-manifest-sha256",
            "bootstrap-rootfs-membership-record",
        ),
    ),
    (
        "sandbox-interpreter-identity-matched",
        "F1_ARTIFACT_PLATFORM_IDENTITY",
        "PRE_STAGE1",
        "pre-first-child-artifact-validation",
        "privileged-supervisor-artifact-observer-v1",
        "sandbox-interpreter-content-and-linkage-observation-v1",
        "interpreter-content-linkage-and-rootfs-membership-match-v1",
        "policy-identities-matched",
        ("sandbox-interpreter",),
        (
            "interpreter-file-sha256",
            "interpreter-stat-record",
            "interpreter-elf-linkage-record",
            "interpreter-rootfs-membership-record",
        ),
    ),
    (
        "seccomp-filter-and-architecture-observed-before-release",
        "F2_PIDFD_BOUND_STOPPED_STATE",
        "PRE_STAGE2",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "two-stage-seccomp-stack-and-architecture-observation-v1",
        "two-distinct-architecture-bound-seccomp-filters-match-v1",
        "pre-adapter-release-observations-matched",
        (
            "application",
            "launch-seccomp-filter",
            "adapter-seccomp-filter",
        ),
        (
            "architecture-record",
            "seccomp-status-and-filter-count-record",
            "launch-filter-sha256",
            "adapter-filter-sha256",
            "bootstrap-filter-install-transcript-leaf",
        ),
    ),
    (
        "supervisor-dependency-closure-identity-matched",
        "F1_ARTIFACT_PLATFORM_IDENTITY",
        "PRE_STAGE1",
        "pre-first-child-artifact-validation",
        "external-supervisor-custody-observer-v1",
        "supervisor-transitive-dependency-closure-observation-v1",
        "supervisor-transitive-dependency-closure-policy-match-v1",
        "reviewed-supervisor-selected",
        (
            "privileged-supervisor",
            "supervisor-dependency-closure",
        ),
        (
            "supervisor-dependency-inventory-bytes",
            "supervisor-dependency-closure-sha256",
            "supervisor-loader-resolution-record",
        ),
    ),
    (
        "supervisor-executable-identity-matched",
        "F1_ARTIFACT_PLATFORM_IDENTITY",
        "PRE_STAGE1",
        "pre-first-child-artifact-validation",
        "external-supervisor-custody-observer-v1",
        "supervisor-executable-content-identity-observation-v1",
        "supervisor-executable-source-and-feature-policy-match-v1",
        "reviewed-supervisor-selected",
        ("privileged-supervisor",),
        (
            "supervisor-executable-sha256",
            "supervisor-executable-stat-record",
            "supervisor-source-sha256",
            "supervisor-feature-manifest-sha256",
        ),
    ),
    (
        "teardown-cgroup-populated-zero-observed",
        "F4_BOUND_MONOTONIC_EVENT_GRAPH",
        "POSTRUN",
        "postrun-cleanup-complete",
        "privileged-supervisor-cgroup-observer-v1",
        "bounded-teardown-reap-and-cgroup-quiescence-observation-v1",
        "complete-reap-stream-eof-and-cgroup-populated-zero-v1",
        "postrun-cgroup-quiescence-observed",
        (
            "sandbox-cgroup-v2-leaf",
            "bubblewrap-monitor",
            "adopted-run-descendants",
            "supervisor-stdio-peers",
        ),
        (
            "teardown-monotonic-deadline-records",
            "monitor-and-descendant-wait-reap-records",
            "cgroup-events-final-bytes",
            "cgroup-process-final-inventory",
            "stream-eof-and-drain-records",
        ),
    ),
)


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


_OBSERVATION_SCHEMAS: Final = tuple(
    _ObservationSchema(*values) for values in _OBSERVATION_METADATA
)
_SCHEMA_BY_ID: Final = MappingProxyType(
    {item.observation_id: item for item in _OBSERVATION_SCHEMAS}
)
_OBSERVATION_IDS: Final = tuple(
    item.observation_id for item in _OBSERVATION_SCHEMAS
)
LINUX_CONFINEMENT_SEMANTIC_AGGREGATE_OBSERVATION_IDS: Final = (
    "backend-static-sealed-executable-identity-matched",
    "cgroup-v2-leaf-owned-by-supervisor",
    "dependency-lock-identity-matched",
    (
        "exact-two-level-uid-gid-maps-composition-empty-supplementary-"
        "groups-and-setgroups-denial-matched"
    ),
    "immutable-runtime-rootfs-identity-matched",
    "linux-platform-profile-matched",
    "sandbox-bootstrap-identity-matched",
    "sandbox-interpreter-identity-matched",
    "supervisor-dependency-closure-identity-matched",
    "supervisor-executable-identity-matched",
    "application-argv-environment-cwd-umask-matched",
    "capability-securebits-dumpability-profile-matched",
    "cgroup-v2-controller-values-matched-before-release",
    ("descriptor-inventory-and-stdio-types-closed-before-adapter-" "import"),
    "landlock-abi-and-ruleset-matched",
    "mount-inventory-and-write-surface-matched",
    "namespace-identities-distinct-before-release",
    "network-interface-and-route-inventory-matched",
    "no-new-privileges-observed-before-release",
    "rlimit-profile-matched-before-release",
    "seccomp-filter-and-architecture-observed-before-release",
    ("nonce-generation-nonreuse-and-readiness-release-transcript-" "matched"),
    (
        "pidfd-bound-observer-helper-monitor-init-application-"
        "identities-subreaper-adoption-and-reap-observed"
    ),
    "teardown-cgroup-populated-zero-observed",
)
_AGGREGATE_OBSERVATION_IDS: Final = (
    LINUX_CONFINEMENT_SEMANTIC_AGGREGATE_OBSERVATION_IDS
)
_RAW_FIELD_IDS: Final = tuple(
    sorted(
        {
            field_id
            for item in _OBSERVATION_SCHEMAS
            for field_id in item.raw_evidence_field_ids
        }
    )
)
_SUBJECT_ROLE_IDS: Final = tuple(
    sorted(
        {
            role_id
            for item in _OBSERVATION_SCHEMAS
            for role_id in item.subject_role_ids
        }
    )
)


class LinuxConfinementSemanticVerificationCode(str, Enum):
    """Stable nonreflecting errors for this separated verifier."""

    INPUT_TYPE = "LINUX_CONFINEMENT_SEMANTIC_VERIFY_INPUT_TYPE"
    INPUT_RESOURCE = "LINUX_CONFINEMENT_SEMANTIC_VERIFY_INPUT_RESOURCE"
    CANONICAL_INVALID = "LINUX_CONFINEMENT_SEMANTIC_VERIFY_CANONICAL_INVALID"
    VALUE_INVALID = "LINUX_CONFINEMENT_SEMANTIC_VERIFY_VALUE_INVALID"
    ORDER_INVALID = "LINUX_CONFINEMENT_SEMANTIC_VERIFY_ORDER_INVALID"
    BINDING_MISMATCH = "LINUX_CONFINEMENT_SEMANTIC_VERIFY_BINDING_MISMATCH"
    CONTRACT_DRIFT = "LINUX_CONFINEMENT_SEMANTIC_VERIFY_CONTRACT_DRIFT"
    RESULT_INVALID = "LINUX_CONFINEMENT_SEMANTIC_VERIFY_RESULT_INVALID"
    INTERNAL_ERROR = "LINUX_CONFINEMENT_SEMANTIC_VERIFY_INTERNAL_ERROR"


_ERROR_MESSAGES: Final = MappingProxyType(
    {
        LinuxConfinementSemanticVerificationCode.INPUT_TYPE: (
            "semantic verification input type invalid"
        ),
        LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE: (
            "semantic verification resource limit exceeded"
        ),
        LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID: (
            "semantic verification canonical encoding invalid"
        ),
        LinuxConfinementSemanticVerificationCode.VALUE_INVALID: (
            "semantic verification value invalid"
        ),
        LinuxConfinementSemanticVerificationCode.ORDER_INVALID: (
            "semantic verification order invalid"
        ),
        LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH: (
            "semantic verification binding mismatch"
        ),
        LinuxConfinementSemanticVerificationCode.CONTRACT_DRIFT: (
            "semantic verification contract drift"
        ),
        LinuxConfinementSemanticVerificationCode.RESULT_INVALID: (
            "semantic verification result invalid"
        ),
        LinuxConfinementSemanticVerificationCode.INTERNAL_ERROR: (
            "semantic verification internal error"
        ),
    }
)


class LinuxConfinementSemanticVerificationError(ValueError):
    """One fixed-message implementation-separated verifier failure."""

    def __init__(
        self,
        code: LinuxConfinementSemanticVerificationCode,
    ) -> None:
        if type(code) is not LinuxConfinementSemanticVerificationCode:
            raise TypeError("semantic verification code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: LinuxConfinementSemanticVerificationCode) -> None:
    raise LinuxConfinementSemanticVerificationError(code) from None


def _ascii(value: str) -> bytes:
    if type(value) is not str:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    try:
        return value.encode("ascii", "strict")
    except UnicodeError:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)


def _token(value: object, *, empty: bool = False) -> str:
    if type(value) is not str:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    if empty and value == "":
        return value
    raw = _ascii(value)
    if (
        not raw
        or len(raw) > _MAX_TOKEN_BYTES
        or _TOKEN_RE.fullmatch(value) is None
    ):
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    return value


def _sha256(value: object, *, allow_zero: bool = False) -> str:
    if (
        type(value) is not str
        or _SHA256_RE.fullmatch(value) is None
        or (not allow_zero and value == _ZERO_SHA256)
    ):
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    return value


def _u64(value: object, *, positive: bool = False) -> int:
    if (
        type(value) is not int
        or value < (1 if positive else 0)
        or value >= 1 << 64
    ):
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    return value


def _plain_sha256(value: bytes) -> str:
    if type(value) is not bytes:
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_TYPE)
    return hashlib.sha256(value).hexdigest()


def _domain_sha256(domain: str, value: bytes) -> str:
    _token(domain)
    if type(value) is not bytes:
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_TYPE)
    digest = hashlib.sha256()
    digest.update(_ascii(domain))
    digest.update(b"\x00")
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)
    return digest.hexdigest()


def _node_count(value: object, *, depth: int = 0) -> int:
    if depth > _MAX_JSON_DEPTH:
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE)
    if value is None or type(value) in (bool, int, str):
        if type(value) is int:
            _u64(value)
        if (
            type(value) is str
            and len(_ascii(value)) > _MAX_JSON_STRING_BYTES
        ):
            _fail(LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE)
        return 1
    if type(value) is list:
        return 1 + sum(_node_count(item, depth=depth + 1) for item in value)
    if type(value) is dict:
        result = 1
        for key, item in value.items():
            if type(key) is not str or len(_ascii(key)) > _MAX_TOKEN_BYTES:
                _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
            result += _node_count(item, depth=depth + 1)
        return result
    _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)


def _canonical_json(value: object, *, maximum: int) -> bytes:
    if _node_count(value) > _MAX_JSON_ITEMS:
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE)
    try:
        raw = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii", "strict")
    except (TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    if not raw or len(raw) > maximum:
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE)
    return raw


def _reject_float(_: str) -> object:
    _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)


def _reject_constant(_: str) -> object:
    _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
        result[key] = value
    return result


def _parse_canonical_object(value: bytes, *, maximum: int) -> dict:
    if type(value) is not bytes:
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_TYPE)
    if not value or len(value) > maximum:
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE)
    try:
        text = value.decode("ascii", "strict")
        parsed = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except LinuxConfinementSemanticVerificationError:
        raise
    except (
        UnicodeError,
        json.JSONDecodeError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
    if (
        type(parsed) is not dict
        or _canonical_json(parsed, maximum=maximum) != value
    ):
        _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
    return parsed


def _typed_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is list:
        return len(left) == len(right) and all(
            _typed_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    if type(left) is dict:
        return set(left) == set(right) and all(
            _typed_equal(left[key], right[key]) for key in left
        )
    return left == right


def _exact_keys(value: object, expected: Tuple[str, ...]) -> dict:
    if type(value) is not dict or tuple(sorted(value)) != tuple(
        sorted(expected)
    ):
        _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
    return value


def _decode_hex(value: object, *, maximum: int) -> bytes:
    if (
        type(value) is not str
        or len(value) % 2
        or len(value) > 2 * maximum
        or value != value.lower()
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
    try:
        return bytes.fromhex(value)
    except ValueError:
        _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)


def _false_nonclaims() -> dict:
    return dict(_FALSE_NONCLAIMS)


def _role_rows_tree() -> list:
    return [dict(zip(_ROLE_ROW_FIELDS, row)) for row in _ROLE_ROWS]


def _schema(observation_id: object) -> _ObservationSchema:
    if type(observation_id) is not str:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    try:
        return _SCHEMA_BY_ID[observation_id]
    except KeyError:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)


def _observation_artifact_type(observation_id: str) -> str:
    _schema(observation_id)
    return _OBSERVATION_ARTIFACT_TYPE_PREFIX + observation_id + ".v1"


def _semantic_type_id(field_id: str) -> str:
    if field_id not in _RAW_FIELD_IDS:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    return "heterodiff.adapter.linux-evidence-field." + field_id + ".v1"


def _field_codec(field_id: str) -> str:
    if field_id in _SHA256_FIELDS:
        return _CODEC_SHA256
    if field_id in _U64_FIELDS:
        return _CODEC_U64
    if field_id in _NUL_FIELDS:
        return _CODEC_NUL
    if field_id in _OCTET_FIELDS:
        return _CODEC_OCTETS
    if field_id in _RAW_FIELD_IDS:
        return _CODEC_RECORD
    _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)


def _field_comparator(field_id: str) -> str:
    codec = _field_codec(field_id)
    if codec == _CODEC_SHA256:
        return "exact-digest-policy-or-cross-record-pin-equality-v1"
    if codec == _CODEC_U64:
        return "exact-u64-policy-or-cross-record-equality-v1"
    return "profile-predicate-input-not-portably-evaluated-v1"


def _field_parser_id(field_id: str) -> str:
    if _field_codec(field_id) != _CODEC_RECORD:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    return "heterodiff.adapter.linux-evidence-parser." + field_id + ".v1"


def _projection_schema_id(field_id: str) -> str:
    if field_id not in _PROJECTION_SCHEMA_BY_FIELD:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    return LINUX_CONFINEMENT_PROJECTION_SCHEMA_ID_PREFIX + field_id + ".v1"


def _validate_projection_node(
    node: _ProjectionSchemaNode,
    value: object,
) -> None:
    kind_id = node.node_kind_id
    if kind_id == "boolean":
        if type(value) is not bool:
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
        return
    if kind_id == "sha256":
        _sha256(value)
        return
    if kind_id == "optional-sha256":
        if type(value) is not str:
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
        if value:
            _sha256(value, allow_zero=True)
        return
    if kind_id == "token":
        if type(value) is not str:
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
        if len(_ascii(value)) > _MAX_TOKEN_BYTES:
            _fail(LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE)
        return
    if kind_id == "u64":
        _u64(value)
        return
    if kind_id in ("octets", "path"):
        if type(value) is not str:
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
        if len(value) > _MAX_JSON_STRING_BYTES:
            _fail(LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE)
        if (
            len(value) % 2
            or value != value.lower()
            or any(
                character not in "0123456789abcdef"
                for character in value
            )
        ):
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
        return
    if kind_id == "list":
        if type(value) is not list:
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
        for item in value:
            _validate_projection_node(node.item_schema, item)
        return
    if kind_id != "object" or type(value) is not dict:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    expected = tuple(row[0] for row in node.field_rows)
    _exact_keys(value, expected)
    for field_id, child in node.field_rows:
        _validate_projection_node(child, value[field_id])


def _validate_canonical_projection(
    field_id: str,
    projection: object,
) -> dict:
    result = _exact_keys(projection, _PROJECTION_FIELD_IDS)
    schema = _schema(result["observation_id"])
    if (
        field_id not in schema.raw_evidence_field_ids
        or _field_codec(field_id) != _CODEC_RECORD
        or result["field_id"] != field_id
        or result["projection_schema_id"] != _projection_schema_id(field_id)
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    for name in (
        "process_identity_snapshot_sha256",
        "staging_run_binding_sha256",
        "subject_identity_table_sha256",
    ):
        _sha256(result[name])
    if type(result["source_observation_available"]) is not bool:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    for name in ("source_errno_id", "source_observation_status_id"):
        if type(result[name]) is not str:
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
        if len(_ascii(result[name])) > _MAX_TOKEN_BYTES:
            _fail(LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE)
    refs = result["subject_identity_refs"]
    if type(refs) is not list or len(refs) != len(schema.subject_role_ids):
        _fail(LinuxConfinementSemanticVerificationCode.ORDER_INVALID)
    for index, ref in enumerate(refs):
        _exact_keys(ref, _PROJECTION_SUBJECT_REF_FIELD_IDS)
        if ref["subject_role_id"] != schema.subject_role_ids[index]:
            _fail(LinuxConfinementSemanticVerificationCode.ORDER_INVALID)
        _sha256(ref["subject_identity_sha256"])
    _validate_projection_node(
        _PROJECTION_SCHEMA_BY_FIELD[field_id],
        result["values"],
    )
    if field_id in _ALIAS_TRANSITION_ROLE_IDS:
        predecessor, successor = _ALIAS_TRANSITION_ROLE_IDS[field_id]
        values = result["values"]
        if (
            values["predecessor_role_id"] != predecessor
            or values["successor_role_id"] != successor
        ):
            _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    return result


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
    result = []
    for field_id in LINUX_CONFINEMENT_CANONICAL_JSON_PROJECTION_FIELD_IDS:
        result.append(
            {
                "field_id": field_id,
                "observation_ids": [
                    schema.observation_id
                    for schema in _OBSERVATION_SCHEMAS
                    if field_id in schema.raw_evidence_field_ids
                ],
                "projection_schema_id": _projection_schema_id(field_id),
                "semantic_coverage_id": (
                    "substantive-field-specific-typed-values-v1"
                ),
                "values_schema": _projection_node_tree(
                    _PROJECTION_SCHEMA_BY_FIELD[field_id]
                ),
            }
        )
    return result


def _identity_schema_id(subject_role_id: str) -> str:
    try:
        kind_id = _SUBJECT_KIND[subject_role_id]
    except KeyError:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
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


_ALIAS_EDGES: Final = (
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
_RECORD_ENVELOPE_FIELDS: Final = (
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

# Schema rows correspond, in order, to the sorted canonical-JSON evidence
# fields.  Whitespace is removed before parsing, and blank lines separate
# schemas.  The compact notation is deliberately local to this verifier:
# b=boolean, h=sha256, q=optional-sha256, t=token, u=u64, x=octets, p=path.
_PROJECTION_SCHEMA_TEXT: Final = r"""
{event:{event_id:t,sequence_number:u,monotonic_timestamp_ns:u,staging_ru
n_binding_sha256:h,evidence_digest_sha256:q}}

{descriptors:[{fd_number:u,fd_role_id:t}]}

{namespaces:[{namespace_id:t,device:u,inode:u,owner_user_namespace_inode
:u}]}

{application_task_instance_sha256:h,pidfd_acquisition_record_sha256:q,st
op_signal_id:t,stop_state_id:t,stop_observed_monotonic_ns:u}

{supplementary_gids:[u]}

{architecture_id:t}

{dynamic_section_present:b,dynamic_tag_ids:[t],dt_needed_sonames:[x],dt_
needed_count:u,pt_interp_present:b}

{elf_class_id:t,endianness_id:t,machine_id:t,elf_type_id:t,program_heade
rs:[{index:u,type_id:t,flag_ids:[t],file_offset:u,virtual_address:u,phys
ical_address:u,file_size:u,memory_size:u,alignment:u}],pt_interp_count:u
,writable_executable_segment_count:u}

{access_mode_id:t,memfd_create_flags_mask:u,memfd_create_flag_ids:[t],fd
_cloexec:b,executable:b}

{seals_mask:u,seal_ids:[t]}

{stat:{device:u,inode:u,generation:u,file_type_id:t,mode:u,uid:u,gid:u,n
link:u,size_bytes:u}}

{path:p,content_sha256:q,rootfs_manifest_sha256:q,manifest_entry_sha256:
q,present:b}

{status_schema_id:t,child_host_tgid:u,child_task_instance_sha256:h,statu
s_received_monotonic_ns:u}

{kernel_task_instance_sha256:h,exit_observation_record_sha256:q,adopter_
task_instance_sha256:q,wait_reap_record_sha256:q,wait_status:{wait_kind_
id:t,status_value:u,core_dumped:b},reap_monotonic_timestamp_ns:u}

{kernel_task_instance_sha256:h,creation_monotonic_ns:u,pid1_transition_m
onotonic_ns:u,exit_monotonic_ns:u,lifecycle_transition_record_sha256:q,e
xit_observation_record_sha256:q}

{child_task_instance_sha256:h,parent_task_instance_sha256:q,relation_id:
t,observed_monotonic_timestamp_ns:u}

{kernel_task_instance_sha256:h,pidfd_acquisition_method_id:t,pidfd_acqui
sition_record_sha256:q,pidfd_number:u,acquisition_monotonic_ns:u}

{kernel_task_instance_sha256:h,lifecycle_transition_record_sha256:q,pred
ecessor_role_id:t,successor_role_id:t}

{mounts:[{mount_id:u,parent_mount_id:u,device_major:u,device_minor:u,roo
t_path:p,mount_point:p,mount_options:[t],optional_fields:[t],filesystem_
type_id:t,mount_source:p,super_options:[t]}]}

{ambient_mask:u,ambient:[t],bounding_mask:u,bounding:[t],effective_mask:
u,effective:[t],inheritable_mask:u,inheritable:[t],permitted_mask:u,perm
itted:[t]}

{delegated_controller_ids:[t],subtree_control_controller_ids:[t],delegat
ion_enabled:b,parent_path:p,leaf_path:p,preexisting_member_count:u}

{owner_uid:u,owner_gid:u,owner_user_namespace_inode:u,owner_task_instanc
e_sha256:h}

{filesystem_type_id:t,object:{device:u,inode:u,generation:u,kernel_objec
t_type_id:t},mount_id:u}

{leaf_identity_sha256:h,populated:b,member_count:u,members:[{role_id:t,k
ernel_task_instance_sha256:h}]}

{cgroup_version_id:t,leaf_identity_sha256:h,members:[{role_id:t,kernel_t
ask_instance_sha256:h}]}

{records:[{task_slot_id:t,host_tgid:u,kernel_task_instance_sha256:h,clon
e_flag_ids:[t],exit_signal_id:t,pidfd_number:u,pidfd_acquisition_record_
sha256:q,monotonic_timestamp_ns:u}]}

{cwd_path:p,cwd_mount_id:u,cwd_device_major:u,cwd_device_minor:u,cwd_ino
de:u,cwd_file_type_id:t}

{dev_read_only:b,devpts_read_only:b,dev_shm_mode_octal:t,dev_shm_writabl
e:b,ptmx_mode_octal:t,host_tty_device_binding_present:b,pty_allocation_a
dmitted:b}

{dumpable:u}

{descriptors:[{fd_number:u,fd_role_id:t,access_mode_id:t,nonblocking:b,o
ffset_rule_id:t,offset_bytes:u}]}

{descriptors:[{fd_number:u,fd_role_id:t,fd_cloexec_before_backend_exec:b
,inherited_by_backend:b,inherited_by_application:b}]}

{descriptors:[{fd_number:u,fd_role_id:t,object:{device:u,inode:u,generat
ion:u,kernel_object_type_id:t}}]}

{forbidden_mount_type_ids:[t],observed_forbidden_mounts:[{mount_id:u,fil
esystem_type_id:t}]}

{syscall_id:t,flags:u,requested_byte_count:u,returned_byte_count:u,retur
ned_nonce_hex:x,call_start_monotonic_ns:u,call_end_monotonic_ns:u}

{namespaces:[{namespace_id:t,device:u,inode:u,owner_user_namespace_inode
:u}]}

{final_uid_map:[{inside_id:u,outside_id:u,length:u}],final_gid_map:[{ins
ide_id:u,outside_id:u,length:u}]}

{intermediate_uid_map:[{inside_id:u,outside_id:u,length:u,outside_id_sou
rce_id:t}],intermediate_gid_map:[{inside_id:u,outside_id:u,length:u,outs
ide_id_source_id:t}],final_uid_map:[{inside_id:u,outside_id:u,length:u}]
,final_gid_map:[{inside_id:u,outside_id:u,length:u}]}

{elf_class_id:t,machine_id:t,pt_interp_path:p,dependencies:[{soname_byte
s_hex:x,resolved_path:p,content_sha256:q,manifest_entry_sha256:q}]}

{path:p,content_sha256:q,rootfs_manifest_sha256:q,manifest_entry_sha256:
q,present:b}

{path:p,stat:{device:u,inode:u,generation:u,file_type_id:t,mode:u,uid:u,
gid:u,nlink:u,size_bytes:u}}

{routes:[{destination_address_hex:x,prefix_length:u,route_type_id:t,scop
e_id:t,table_id:u,output_ifindex:u,gateway_address_hex:x,preferred_sourc
e_address_hex:x,metric:u}]}

{routes:[{destination_address_hex:x,prefix_length:u,route_type_id:t,scop
e_id:t,table_id:u,output_ifindex:u,gateway_address_hex:x,preferred_sourc
e_address_hex:x,metric:u}]}

{sysname:t,release_bytes_hex:x,version_bytes_hex:x,machine_id:t,boot_id_
sha256:h}

{syscall_id:t,return_status_id:t,errno_id:t,ruleset_content_sha256:h,no_
new_privileges:b}

{return_status_id:t,errno_id:t,queried_abi_version:u}

{platform_profile_sha256:h,features:[{feature_id:t,available:b,version_n
umber:u,probe_result_id:t}]}

{records:[{task_slot_id:t,kernel_task_instance_sha256:h,reaper_role_id:t
,exit_observation_record_sha256:q,wait_reap_record_sha256:q,wait_status:
{wait_kind_id:t,status_value:u,core_dumped:b},reap_monotonic_timestamp_n
s:u}]}

{mounts:[{mount_id:u,propagation_id:t,peer_group_id:u,master_group_id:u}
]}

{levels:[{level_id:t,identity:{namespace_id:t,device:u,inode:u,owner_use
r_namespace_inode:u}}],parent_edges:[{child_level_id:t,parent_level_id:t
}]}

{relations:[{namespace_id:t,child_identity:{namespace_id:t,device:u,inod
e:u,owner_user_namespace_inode:u},parent_identity:{namespace_id:t,device
:u,inode:u,owner_user_namespace_inode:u},parent_level_id:t}]}

{interfaces:[{ifindex:u,interface_name_bytes_hex:x,flags:[t],mtu:u,opers
tate_id:t,addresses:[{family_id:t,address_hex:x,prefix_length:u,scope_id
:t}]}]}

{namespace_id:t,device:u,inode:u,owner_user_namespace_inode:u}

{no_new_privileges:b}

{supervisor_epoch_id_hex:x,run_nonce_hex:x,insertion_index:u,prior_entry
_count:u,post_entry_count:u,registry_capacity:u,prior_registry_commitmen
t_sha256:h,post_registry_commitment_sha256:h,atomic_result_id:t}

{observer_task_instance_sha256:h,pidfd_acquisition_record_sha256:q,origi
nal_parent_task_instance_sha256:q,adopter_task_instance_sha256:q,exit_ob
servation_record_sha256:q,wait_reap_record_sha256:q,wait_status:{wait_ki
nd_id:t,status_value:u,core_dumped:b},reap_monotonic_timestamp_ns:u}

{probe_scope_id:t,old_root_mount_present:b,reachable_old_root_handle_cou
nt:u}

{relations:[{child_task_slot_id:t,parent_task_slot_id:t,relation_id:t,ch
ild_task_instance_sha256:h,parent_task_instance_sha256:q,observed_monoto
nic_timestamp_ns:u}]}

{reader_task_instance_sha256:h,reader_pidfd_acquisition_record_sha256:q,
barrier_identity_sha256:h,syscall_id:t,requested_byte_count:u,blocked_st
ate_id:t,observation_method_id:t,observed_monotonic_timestamp_ns:u}

{stdout_read_end_identity_sha256:h,buffered_byte_count:u,observation_mon
otonic_ns:u}

{stdout_read_end_identity_sha256:h,read_chunk_byte_counts:[u],total_drai
ned_byte_count:u,terminal_errno_id:t,drain_start_monotonic_ns:u,drain_en
d_monotonic_ns:u}

{frame_hex:x,frame_byte_count:u,chunk_byte_counts:[u],run_nonce_hex:x,st
dout_read_end_identity_sha256:h,first_stdout_offset:u,accepted_frame_cou
nt:u,trailing_pre_release_byte_count:u,parser_id:t}

{roles:[{role_id:t,task_slot_id:t,kernel_task_instance_sha256:q,pidfd_ac
quisition_record_sha256:q,lifecycle_transition_record_sha256:q}]}

{mount_id:u,parent_mount_id:u,device_major:u,device_minor:u,inode:u,file
system_type_id:t,mount_flags:[t],super_options:[t],read_only:b}

{run_sequence_number:u}

{seccomp_mode_id:t,filter_count:u,no_new_privileges:b,architecture_id:t}

{securebits_mask:u}

{levels:[{level_id:t,setgroups_bytes_hex:x}]}

{limits:[{resource_id:t,soft_value:u,hard_value:u}]}

{stage1:{event:{event_id:t,sequence_number:u,monotonic_timestamp_ns:u,st
aging_run_binding_sha256:h,evidence_digest_sha256:q},release_channel_ide
ntity_sha256:q,release_payload_hex:x,release_write_count:u},stage2:{even
t:{event_id:t,sequence_number:u,monotonic_timestamp_ns:u,staging_run_bin
ding_sha256:h,evidence_digest_sha256:q},target_task_instance_sha256:q,si
gnal_id:t}}

{read_end:{device:u,inode:u,generation:u,kernel_object_type_id:t},write_
end:{device:u,inode:u,generation:u,kernel_object_type_id:t},same_pipe_ob
ject:b}

{stdio:[{fd_number:u,fd_role_id:t,isatty:b}]}

{streams:[{fd_role_id:t,peer_identity_sha256:q,completion_status_id:t,te
rminal_errno_id:t,completion_evidence_sha256:q,drained_byte_count:u,dead
line_ns:u,completed_ns:u}]}

{supervisor_task_instance_sha256:h,child_subreaper_enabled:b,set_before_
first_child:b,preexisting_child_count:u,adopted_task_slot_ids:[t],final_
child_count:u}

{resolved_path:p,stat:{device:u,inode:u,generation:u,file_type_id:t,mode
:u,uid:u,gid:u,nlink:u,size_bytes:u}}

{loader_path:p,resolved_objects:[{soname_bytes_hex:x,resolved_path:p,sta
t:{device:u,inode:u,generation:u,file_type_id:t,mode:u,uid:u,gid:u,nlink
:u,size_bytes:u},content_sha256:q}],closure_sha256:h}

{peers:[{application_fd_number:u,fd_role_id:t,peer_kernel_object_identit
y_sha256:h,peer_custody_id:t}]}

{clock_id:t,cleanup_branch_id:t,teardown_started_ns:u,term_grace_deadlin
e_ns:u,pidfd_exit_deadline_ns:u,monitor_first_deadline_ns:u,monitor_seco
nd_deadline_ns:u,cgroup_quiescence_deadline_ns:u,stream_eof_deadline_ns:
u,emergency_entered:b}

{uid:u,gid:u,supplementary_gids:[u]}

{umask_octal:t}

{kernel_task_instance_sha256:h,creation_monotonic_ns:u,exec_monotonic_ns
:u,exit_monotonic_ns:u,lifecycle_transition_record_sha256:q,exit_observa
tion_record_sha256:q}

{launcher_task_instance_sha256:h,parent_task_instance_sha256:q,parent_re
lation_id:t,observed_monotonic_timestamp_ns:u}

{kernel_task_instance_sha256:h,lifecycle_transition_record_sha256:q,pred
ecessor_role_id:t,successor_role_id:t}

{records:[{task_slot_id:t,kernel_task_instance_sha256:h,reaper_role_id:t
,exit_observation_record_sha256:q,wait_reap_record_sha256:q,wait_status:
{wait_kind_id:t,status_value:u,core_dumped:b},reap_monotonic_timestamp_n
s:u}]}

{writable_paths:[{path:p,mount_id:u,device_major:u,device_minor:u,inode:
u}]}
"""


@dataclass(frozen=True)
class _ProjectionSchemaNode:
    node_kind_id: str
    field_rows: Tuple[Tuple[str, object], ...] = ()
    item_schema: object = None


class _ProjectionSchemaParser:
    _SCALARS: Final = MappingProxyType(
        {
            "b": "boolean",
            "h": "sha256",
            "p": "path",
            "q": "optional-sha256",
            "t": "token",
            "u": "u64",
            "x": "octets",
        }
    )

    def __init__(self, text: str) -> None:
        self.text = "".join(text.split())
        self.index = 0

    def parse(self) -> _ProjectionSchemaNode:
        result = self._node()
        if self.index != len(self.text):
            raise RuntimeError("projection schema text trailing input")
        return result

    def _take(self, expected: str) -> None:
        if (
            self.index >= len(self.text)
            or self.text[self.index] != expected
        ):
            raise RuntimeError("projection schema text malformed")
        self.index += 1

    def _node(self) -> _ProjectionSchemaNode:
        if self.index >= len(self.text):
            raise RuntimeError("projection schema text truncated")
        marker = self.text[self.index]
        if marker in self._SCALARS:
            self.index += 1
            return _ProjectionSchemaNode(self._SCALARS[marker])
        if marker == "[":
            self.index += 1
            item = self._node()
            self._take("]")
            return _ProjectionSchemaNode("list", item_schema=item)
        self._take("{")
        rows = []
        while True:
            start = self.index
            while (
                self.index < len(self.text)
                and self.text[self.index] not in ":}"
            ):
                self.index += 1
            if self.index == start or self.index >= len(self.text):
                raise RuntimeError("projection object schema malformed")
            field_id = self.text[start : self.index]
            self._take(":")
            rows.append((field_id, self._node()))
            if self.text[self.index] == "}":
                self.index += 1
                break
            self._take(",")
        return _ProjectionSchemaNode("object", tuple(rows))


_CANONICAL_JSON_FIELD_IDS: Final = tuple(
    field_id
    for field_id in _RAW_FIELD_IDS
    if field_id
    not in set(_SHA256_FIELDS + _U64_FIELDS + _NUL_FIELDS + _OCTET_FIELDS)
)
_PROJECTION_SCHEMA_TEXT_ROWS: Final = tuple(
    _PROJECTION_SCHEMA_TEXT.strip().split("\n\n")
)
if len(_CANONICAL_JSON_FIELD_IDS) != 84 or len(
    _PROJECTION_SCHEMA_TEXT_ROWS
) != 84:
    raise RuntimeError("projection schema registry cardinality drift")
_PROJECTION_SCHEMA_BY_FIELD: Final = MappingProxyType(
    {
        field_id: _ProjectionSchemaParser(text).parse()
        for field_id, text in zip(
            _CANONICAL_JSON_FIELD_IDS,
            _PROJECTION_SCHEMA_TEXT_ROWS,
        )
    }
)
LINUX_CONFINEMENT_CANONICAL_JSON_PROJECTION_FIELD_IDS: Final = tuple(
    sorted(_PROJECTION_SCHEMA_BY_FIELD)
)
_RESOURCE_IDENTITY_FIELDS: Final = (
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
_SUBJECT_BINDING_FIELDS: Final = (
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
_EVIDENCE_MEMBER_FIELDS: Final = (
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
_PAYLOAD_FIELDS: Final = (
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
_TOPOLOGY_FIELDS: Final = (
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
)
_SNAPSHOT_FIELDS: Final = (
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
)
_TASK_ROW_FIELDS: Final = (
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
_CONTEXT_FIELDS: Final = [
    "staging_run_binding_sha256",
    "subject_identity_table_sha256",
    "process_identity_snapshot_sha256",
]


def _subject_schema_tree(role_id: str) -> dict:
    return {
        "context_binding_field_ids": list(_CONTEXT_FIELDS),
        "identity_schema_id": _identity_schema_id(role_id),
        "origin_authenticated": False,
        "subject_kind_id": _SUBJECT_KIND[role_id],
        "subject_role_id": role_id,
    }


def _field_schema_tree(field_id: str) -> dict:
    return {
        "comparator_id": _field_comparator(field_id),
        "context_binding_field_ids": list(_CONTEXT_FIELDS),
        "field_id": field_id,
        "semantic_type_id": _semantic_type_id(field_id),
        "value_codec_id": _field_codec(field_id),
    }


def _observation_schema_tree(schema: _ObservationSchema) -> dict:
    return {
        "artifact_type": _observation_artifact_type(schema.observation_id),
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


def linux_confinement_semantic_verifier_contract_tree() -> dict:
    """Return this implementation-separated projection of the V1 contract."""

    return {
        "artifact_type": _SEMANTIC_CONTRACT_ARTIFACT_TYPE,
        "capture_time_subject_semantics": {
            "artifact_type": _SUBJECT_TABLE_ARTIFACT_TYPE,
            "concrete_future_process_identities_in_capture_table": False,
            "digest_field_id": "observation-subject-identity",
            "process_instance_count": 5,
            "role_alias_edges": [list(edge) for edge in _ALIAS_EDGES],
            "role_count": len(_PROCESS_ROLES),
            "role_rows": _role_rows_tree(),
            "semantics_id": (
                "capture-time-logical-role-slot-topology-not-kernel-"
                "identity-v1"
            ),
        },
        "digest_computation_id": _DIGEST_COMPUTATION_ID,
        "encoding_id": _ENCODING_ID,
        "evidence_value_codecs": {
            "bounded_octet_field_ids": list(_OCTET_FIELDS),
            "canonical_json_object_field_ids": [
                field_id
                for field_id in _RAW_FIELD_IDS
                if _field_codec(field_id) == _CODEC_RECORD
            ],
            "codec_ids": list(_CODEC_IDS),
            "nul_frame_field_ids": list(_NUL_FIELDS),
            "sha256_field_ids": list(_SHA256_FIELDS),
            "u64_field_ids": list(_U64_FIELDS),
        },
        "record_envelope_schema": {
            "alias_transition_role_ids": {
                key: list(value)
                for key, value in _ALIAS_TRANSITION_ROLE_IDS.items()
            },
            "field_ids": list(_RECORD_ENVELOPE_FIELDS),
            "native_origin_authenticated": False,
            "portable_projection_recomputed": False,
            "raw_and_projection_identities_bound": True,
        },
        "canonical_projection_schema": {
            "canonical_json_field_occurrence_count": sum(
                1
                for schema in _OBSERVATION_SCHEMAS
                for field_id in schema.raw_evidence_field_ids
                if _field_codec(field_id) == _CODEC_RECORD
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
            "observation_count": len(_OBSERVATION_IDS),
            "process_role_count": len(_PROCESS_ROLES),
            "raw_evidence_field_occurrence_count": sum(
                len(item.raw_evidence_field_ids)
                for item in _OBSERVATION_SCHEMAS
            ),
            "raw_evidence_unique_field_count": len(_RAW_FIELD_IDS),
            "semantic_join_count": len(
                LINUX_CONFINEMENT_SEMANTIC_JOIN_IDS
            ),
            "snapshot_count": len(_STAGES),
            "subject_role_count": len(_SUBJECT_ROLE_IDS),
            "task_slot_count": len(_TASK_SLOTS),
        },
        "format_version": "1",
        "implementation_status_id": _SEMANTIC_IMPLEMENTATION_STATUS,
        "nonclaims": _false_nonclaims(),
        "observation_family_ids": list(_FAMILY_IDS),
        "observation_schemas": [
            _observation_schema_tree(schema) for schema in _OBSERVATION_SCHEMAS
        ],
        "predicate_evaluation_status_id": _PREDICATE_STATUS_ID,
        "process_identity_snapshot_schema": {
            "artifact_type": _SNAPSHOT_ARTIFACT_TYPE,
            "predecessor_chain_required": True,
            (
                "producer_authority_record_is_authenticated_by_"
                "portable_code"
            ): False,
            "snapshot_expected_state": {
                stage_id: {
                    slot_id: list(state)
                    for slot_id, state in _SNAPSHOT_STATE[stage_id].items()
                }
                for stage_id in _STAGES
            },
            "snapshot_stage_ids": list(_STAGES),
            "task_parent_slots": dict(_TASK_PARENT),
            "task_pidfd_acquisition_method_ids": dict(_TASK_PIDFD_METHOD),
            "task_reaper_roles": dict(_TASK_REAPER),
            "task_slot_ids": list(_TASK_SLOTS),
            "trusted_producer_ids": dict(_SNAPSHOT_PRODUCER),
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
            "maximum_contract_bytes": _MAX_CONTRACT_BYTES,
            "maximum_json_depth": _MAX_JSON_DEPTH,
            "maximum_json_items": _MAX_JSON_ITEMS,
            "maximum_json_string_bytes": _MAX_JSON_STRING_BYTES,
            "maximum_observation_payload_bytes": _MAX_PAYLOAD_BYTES,
            "maximum_record_projection_bytes": (
                _MAX_RECORD_PROJECTION_BYTES
            ),
            "maximum_record_raw_source_bytes": (
                _MAX_RECORD_RAW_SOURCE_BYTES
            ),
            "maximum_semantic_value_bytes": _MAX_VALUE_BYTES,
            "maximum_semantic_token_bytes": _MAX_TOKEN_BYTES,
            "maximum_snapshot_bytes": _MAX_SNAPSHOT_BYTES,
            "maximum_subject_identity_table_bytes": (_MAX_SUBJECT_TABLE_BYTES),
        },
        "aggregate_observation_set_joins": {
            "architecture_record_count": 2,
            "available_architecture_records_equal_platform_identity": True,
            "available_elf_machine_identifiers_equal": True,
            "available_seccomp_architecture_equal_platform_identity": True,
            "exact_observation_order_required": True,
            "observation_ids": list(_AGGREGATE_OBSERVATION_IDS),
            "repeated_resource_stable_components_equal": True,
            "unavailable_projection_values_excluded_from_value_joins": True,
        },
        "subject_kind_by_role": dict(_SUBJECT_KIND),
        "resource_identity_envelope_schema": {
            "component_field_ids_by_kind": {
                key: list(value)
                for key, value in _RESOURCE_COMPONENT_FIELDS_BY_KIND.items()
            },
            "field_ids": list(_RESOURCE_IDENTITY_FIELDS),
            "kernel_object_type_by_role": dict(_KERNEL_OBJECT_TYPE_BY_ROLE),
            "namespace_type_by_role": dict(_NAMESPACE_TYPE_BY_ROLE),
            "native_origin_authenticated": False,
            "security_object_type_by_role": dict(
                _SECURITY_OBJECT_TYPE_BY_ROLE
            ),
        },
        "validation_scope_id": _VALIDATION_SCOPE_ID,
        "verifier_id": (
            LINUX_CONFINEMENT_IMPLEMENTATION_SEPARATED_VERIFIER_ID
        ),
    }


def linux_confinement_semantic_verifier_contract_bytes() -> bytes:
    return _canonical_json(
        linux_confinement_semantic_verifier_contract_tree(),
        maximum=_MAX_CONTRACT_BYTES,
    )


def linux_confinement_semantic_verifier_contract_sha256() -> str:
    return _domain_sha256(
        _SEMANTIC_CONTRACT_DIGEST_DOMAIN,
        linux_confinement_semantic_verifier_contract_bytes(),
    )


@dataclass(frozen=True)
class LinuxConfinementSemanticVerificationPinsV1:
    """External retained-record metadata and binding pins."""

    record_kind_id: str
    record_id: str
    lifecycle_stage_id: str
    trusted_producer_id: str
    staging_run_binding_sha256: str
    observation_subject_identity: str
    capture_monotonic_timestamp_ns: int
    record_artifact_type: str
    policy_sha256: str
    linux_platform_profile_sha256: str
    semantic_payload_contract_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementSemanticVerificationPinsV1:
            _fail(LinuxConfinementSemanticVerificationCode.INPUT_TYPE)
        for value in (
            self.record_kind_id,
            self.record_id,
            self.lifecycle_stage_id,
            self.trusted_producer_id,
            self.record_artifact_type,
        ):
            _token(value)
        for value in (
            self.staging_run_binding_sha256,
            self.observation_subject_identity,
            self.policy_sha256,
            self.linux_platform_profile_sha256,
            self.semantic_payload_contract_sha256,
        ):
            _sha256(value)
        _u64(self.capture_monotonic_timestamp_ns, positive=True)


def _validated_pins(
    value: LinuxConfinementSemanticVerificationPinsV1,
) -> None:
    if type(value) is not LinuxConfinementSemanticVerificationPinsV1:
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_TYPE)
    try:
        LinuxConfinementSemanticVerificationPinsV1.__post_init__(value)
    except LinuxConfinementSemanticVerificationError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_TYPE)


@dataclass(frozen=True)
class _Topology:
    raw: bytes
    sha256: str
    policy_sha256: str
    staging_run_binding_sha256: str
    supervisor_epoch_id_hex: str
    run_sequence_number: int
    run_nonce_hex: str


@dataclass(frozen=True)
class _Task:
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
    kernel_task_instance_sha256: str


@dataclass(frozen=True)
class _Snapshot:
    raw: bytes
    sha256: str
    stage_id: str
    predecessor_sha256: str
    capture_monotonic_timestamp_ns: int
    staging_run_binding_sha256: str
    subject_identity_table_sha256: str
    linux_platform_profile_sha256: str
    linux_boot_id_sha256: str
    trusted_producer_id: str
    producer_authority_record_sha256: str
    tasks: Tuple[_Task, ...]


@dataclass(frozen=True)
class _SubjectView:
    role_id: str
    identity_sha256: str
    raw: bytes
    resource_identity: object


@dataclass(frozen=True)
class _EvidenceView:
    field_id: str
    raw: bytes
    projection: object


@dataclass(frozen=True)
class _Payload:
    raw: bytes
    plain_sha256: str
    sha256: str
    schema: _ObservationSchema
    staging_run_binding_sha256: str
    subject_identity_table_sha256: str
    process_identity_snapshot_sha256: str
    capture_window_start_monotonic_ns: int
    capture_window_end_monotonic_ns: int
    subject_binding_count: int
    evidence_member_count: int
    subjects: Tuple[_SubjectView, ...]
    evidence: Tuple[_EvidenceView, ...]


def _staging_run_binding(
    *,
    policy_sha256: str,
    supervisor_epoch_id_hex: str,
    run_sequence_number: int,
    run_nonce_hex: str,
) -> str:
    policy = _sha256(policy_sha256)
    epoch = _sha256(supervisor_epoch_id_hex)
    nonce = _sha256(run_nonce_hex)
    sequence = _u64(run_sequence_number)
    if sequence > _MAX_RUN_SEQUENCE or epoch == nonce:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    raw = _canonical_json(
        {
            "artifact_type": _STAGING_RUN_BINDING_ARTIFACT_TYPE,
            "format_version": "1",
            "policy_sha256": policy,
            "run_nonce_hex": nonce,
            "run_sequence_number": sequence,
            "supervisor_epoch_id_hex": epoch,
        },
        maximum=16 * 1024,
    )
    return _domain_sha256(_STAGING_RUN_BINDING_ARTIFACT_TYPE, raw)


def _parse_topology(
    raw: bytes,
    pins: LinuxConfinementSemanticVerificationPinsV1,
) -> _Topology:
    tree = _exact_keys(
        _parse_canonical_object(raw, maximum=_MAX_SUBJECT_TABLE_BYTES),
        _TOPOLOGY_FIELDS,
    )
    expected_contract = linux_confinement_semantic_verifier_contract_sha256()
    if (
        tree["artifact_type"] != _SUBJECT_TABLE_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or tree["table_semantics_id"]
        != "capture-time-logical-role-slot-topology-not-kernel-identity-v1"
        or not _typed_equal(tree["role_rows"], _role_rows_tree())
        or not _typed_equal(tree["nonclaims"], _false_nonclaims())
        or tree["semantic_payload_contract_sha256"] != expected_contract
        or expected_contract != pins.semantic_payload_contract_sha256
        or tree["acceptance_contract_sha256"]
        != linux_confinement_acceptance_contract_sha256()
        or tree["evidence_plan_sha256"]
        != linux_confinement_evidence_plan_sha256()
        or tree["evidence_schema_contract_sha256"]
        != linux_confinement_evidence_schema_contract_sha256()
        or tree["staging_protocol_contract_sha256"]
        != linux_confinement_staging_protocol_contract_sha256()
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    policy = _sha256(tree["policy_sha256"])
    epoch = _sha256(tree["supervisor_epoch_id_hex"])
    nonce = _sha256(tree["run_nonce_hex"])
    sequence = _u64(tree["run_sequence_number"])
    expected_run = _staging_run_binding(
        policy_sha256=policy,
        supervisor_epoch_id_hex=epoch,
        run_sequence_number=sequence,
        run_nonce_hex=nonce,
    )
    table_sha256 = _domain_sha256(_SUBJECT_TABLE_DIGEST_DOMAIN, raw)
    if (
        tree["staging_run_binding_sha256"] != expected_run
        or policy != pins.policy_sha256
        or expected_run != pins.staging_run_binding_sha256
        or table_sha256 != pins.observation_subject_identity
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    return _Topology(
        raw=raw,
        sha256=table_sha256,
        policy_sha256=policy,
        staging_run_binding_sha256=expected_run,
        supervisor_epoch_id_hex=epoch,
        run_sequence_number=sequence,
        run_nonce_hex=nonce,
    )


def _task_instance_sha256(
    task: _Task,
    *,
    staging_run_binding_sha256: str,
    linux_platform_profile_sha256: str,
    linux_boot_id_sha256: str,
) -> str:
    if task.lifecycle_state_id == "NOT_CREATED":
        return _ZERO_SHA256
    raw = _canonical_json(
        {
            "host_pid_namespace_device": (task.host_pid_namespace_device),
            "host_pid_namespace_inode": task.host_pid_namespace_inode,
            "host_tgid": task.host_tgid,
            "linux_boot_id_sha256": linux_boot_id_sha256,
            "linux_platform_profile_sha256": (linux_platform_profile_sha256),
            "nspid_vector": list(task.nspid_vector),
            "proc_starttime_clock_ticks": (task.proc_starttime_clock_ticks),
            "staging_run_binding_sha256": staging_run_binding_sha256,
        },
        maximum=16 * 1024,
    )
    return _domain_sha256(_TASK_INSTANCE_DIGEST_DOMAIN, raw)


def _parse_task(
    value: object,
    *,
    stage_id: str,
    staging_run_binding_sha256: str,
    linux_platform_profile_sha256: str,
    linux_boot_id_sha256: str,
) -> _Task:
    tree = _exact_keys(value, _TASK_ROW_FIELDS)
    slot = _token(tree["task_slot_id"])
    if slot not in _TASK_SLOTS:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    state = _token(tree["lifecycle_state_id"])
    role = _token(tree["active_role_id"], empty=True)
    if role and role not in _PROCESS_ROLES:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    host_tgid = _u64(tree["host_tgid"])
    starttime = _u64(tree["proc_starttime_clock_ticks"])
    namespace_device = _u64(tree["host_pid_namespace_device"])
    namespace_inode = _u64(tree["host_pid_namespace_inode"])
    nspid_raw = tree["nspid_vector"]
    if type(nspid_raw) is not list or len(nspid_raw) > 16:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    nspid = tuple(_u64(item, positive=True) for item in nspid_raw)
    method = _token(tree["pidfd_acquisition_method_id"])
    pidfd_digest = _sha256(
        tree["pidfd_acquisition_record_sha256"],
        allow_zero=True,
    )
    parent = _token(tree["parent_task_slot_id"], empty=True)
    transition = _sha256(
        tree["lifecycle_transition_record_sha256"],
        allow_zero=True,
    )
    exit_digest = _sha256(
        tree["exit_observation_record_sha256"],
        allow_zero=True,
    )
    reap_digest = _sha256(
        tree["wait_reap_record_sha256"],
        allow_zero=True,
    )
    reaper = _token(tree["reaper_role_id"], empty=True)
    expected_state, expected_role = _SNAPSHOT_STATE[stage_id][slot]
    if (
        state != expected_state
        or role != expected_role
        or method != _TASK_PIDFD_METHOD[slot]
        or parent != _TASK_PARENT[slot]
        or reaper != _TASK_REAPER[slot]
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    numeric = (host_tgid, starttime, namespace_device, namespace_inode)
    if state == "NOT_CREATED":
        if (
            any(numeric)
            or nspid
            or pidfd_digest != _ZERO_SHA256
            or transition != _ZERO_SHA256
            or exit_digest != _ZERO_SHA256
            or reap_digest != _ZERO_SHA256
        ):
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    else:
        if (
            not all(item > 0 for item in numeric)
            or not nspid
            or pidfd_digest == _ZERO_SHA256
        ):
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
        terminal = state == "WAIT_REAPED"
        if terminal != (
            exit_digest != _ZERO_SHA256 and reap_digest != _ZERO_SHA256
        ):
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
        if not terminal and (
            exit_digest != _ZERO_SHA256 or reap_digest != _ZERO_SHA256
        ):
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
        alias_transition_required = (
            stage_id == "PRE_STAGE1" and slot == "monitor-task"
        ) or (stage_id == "PRE_STAGE2" and slot == "pid1-task")
        if alias_transition_required and transition == _ZERO_SHA256:
            _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    provisional = _Task(
        task_slot_id=slot,
        lifecycle_state_id=state,
        active_role_id=role,
        host_tgid=host_tgid,
        proc_starttime_clock_ticks=starttime,
        host_pid_namespace_device=namespace_device,
        host_pid_namespace_inode=namespace_inode,
        nspid_vector=nspid,
        pidfd_acquisition_method_id=method,
        pidfd_acquisition_record_sha256=pidfd_digest,
        parent_task_slot_id=parent,
        lifecycle_transition_record_sha256=transition,
        exit_observation_record_sha256=exit_digest,
        wait_reap_record_sha256=reap_digest,
        reaper_role_id=reaper,
        kernel_task_instance_sha256=_ZERO_SHA256,
    )
    instance = _task_instance_sha256(
        provisional,
        staging_run_binding_sha256=staging_run_binding_sha256,
        linux_platform_profile_sha256=linux_platform_profile_sha256,
        linux_boot_id_sha256=linux_boot_id_sha256,
    )
    if tree["kernel_task_instance_sha256"] != instance:
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    return _Task(
        **{
            item.name: (
                instance
                if item.name == "kernel_task_instance_sha256"
                else getattr(provisional, item.name)
            )
            for item in fields(_Task)
        }
    )


def _parse_snapshot(
    raw: bytes,
    *,
    expected_stage_id: str,
    expected_predecessor_sha256: str,
    topology: _Topology,
    pins: LinuxConfinementSemanticVerificationPinsV1,
) -> _Snapshot:
    tree = _exact_keys(
        _parse_canonical_object(raw, maximum=_MAX_SNAPSHOT_BYTES),
        _SNAPSHOT_FIELDS,
    )
    if (
        tree["artifact_type"] != _SNAPSHOT_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or tree["snapshot_stage_id"] != expected_stage_id
        or tree["trusted_producer_id"] != _SNAPSHOT_PRODUCER[expected_stage_id]
        or not _typed_equal(tree["nonclaims"], _false_nonclaims())
        or tree["validation_scope_id"] != _VALIDATION_SCOPE_ID
        or tree["semantic_payload_contract_sha256"]
        != pins.semantic_payload_contract_sha256
        or tree["predecessor_snapshot_sha256"] != expected_predecessor_sha256
        or tree["staging_run_binding_sha256"]
        != topology.staging_run_binding_sha256
        or tree["subject_identity_table_sha256"] != topology.sha256
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    platform = _sha256(tree["linux_platform_profile_sha256"])
    boot = _sha256(tree["linux_boot_id_sha256"])
    predecessor = _sha256(
        tree["predecessor_snapshot_sha256"],
        allow_zero=True,
    )
    timestamp = _u64(
        tree["capture_monotonic_timestamp_ns"],
        positive=True,
    )
    authority = _sha256(tree["producer_authority_record_sha256"])
    rows = tree["task_rows"]
    if type(rows) is not list:
        _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
    tasks = tuple(
        _parse_task(
            item,
            stage_id=expected_stage_id,
            staging_run_binding_sha256=(topology.staging_run_binding_sha256),
            linux_platform_profile_sha256=platform,
            linux_boot_id_sha256=boot,
        )
        for item in rows
    )
    if tuple(item.task_slot_id for item in tasks) != _TASK_SLOTS:
        _fail(LinuxConfinementSemanticVerificationCode.ORDER_INVALID)
    return _Snapshot(
        raw=raw,
        sha256=_domain_sha256(_SNAPSHOT_DIGEST_DOMAIN, raw),
        stage_id=expected_stage_id,
        predecessor_sha256=predecessor,
        capture_monotonic_timestamp_ns=timestamp,
        staging_run_binding_sha256=topology.staging_run_binding_sha256,
        subject_identity_table_sha256=topology.sha256,
        linux_platform_profile_sha256=platform,
        linux_boot_id_sha256=boot,
        trusted_producer_id=tree["trusted_producer_id"],
        producer_authority_record_sha256=authority,
        tasks=tasks,
    )


def _stable_task_components(task: _Task) -> tuple:
    return (
        task.host_tgid,
        task.proc_starttime_clock_ticks,
        task.host_pid_namespace_device,
        task.host_pid_namespace_inode,
        task.nspid_vector,
        task.pidfd_acquisition_method_id,
        task.pidfd_acquisition_record_sha256,
        task.parent_task_slot_id,
        task.reaper_role_id,
    )


def _parse_snapshot_chain(
    raw_snapshots: Tuple[bytes, ...],
    *,
    topology: _Topology,
    pins: LinuxConfinementSemanticVerificationPinsV1,
) -> Tuple[_Snapshot, ...]:
    if (
        type(raw_snapshots) is not tuple
        or len(raw_snapshots) != 3
        or any(type(item) is not bytes for item in raw_snapshots)
    ):
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_TYPE)
    result = []
    predecessor = _ZERO_SHA256
    for stage_id, raw in zip(_STAGES, raw_snapshots):
        snapshot = _parse_snapshot(
            raw,
            expected_stage_id=stage_id,
            expected_predecessor_sha256=predecessor,
            topology=topology,
            pins=pins,
        )
        result.append(snapshot)
        predecessor = snapshot.sha256
    snapshots = tuple(result)
    if any(
        later.capture_monotonic_timestamp_ns
        <= earlier.capture_monotonic_timestamp_ns
        for earlier, later in zip(snapshots, snapshots[1:])
    ):
        _fail(LinuxConfinementSemanticVerificationCode.ORDER_INVALID)
    if (
        len({item.linux_platform_profile_sha256 for item in snapshots}) != 1
        or len({item.linux_boot_id_sha256 for item in snapshots}) != 1
        or snapshots[0].linux_platform_profile_sha256
        != pins.linux_platform_profile_sha256
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    rows = tuple(
        {task.task_slot_id: task for task in snapshot.tasks}
        for snapshot in snapshots
    )
    for slot in _TASK_SLOTS:
        indices = (1, 2) if slot == "application-task" else (0, 1, 2)
        selected = tuple(rows[index][slot] for index in indices)
        if (
            len({item.kernel_task_instance_sha256 for item in selected}) != 1
            or _ZERO_SHA256
            in {item.kernel_task_instance_sha256 for item in selected}
            or len({_stable_task_components(item) for item in selected}) != 1
        ):
            _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    if len({rows[index]["helper-task"] for index in range(3)}) != 1:
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    if (
        len({task.kernel_task_instance_sha256 for task in snapshots[2].tasks})
        != 5
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    return snapshots


def _validate_nul_frame(field_id: str, value: bytes) -> None:
    if len(value) > _MAX_VALUE_BYTES:
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE)
    if value == b"":
        return
    if not value.endswith(b"\x00"):
        _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)


def _validate_record_envelope(field_id: str, value: bytes) -> dict:
    tree = _exact_keys(
        _parse_canonical_object(value, maximum=_MAX_VALUE_BYTES),
        _RECORD_ENVELOPE_FIELDS,
    )
    projection = tree["canonical_projection"]
    if type(projection) is not dict or not projection:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    raw_source_hex = tree["raw_source_hex"]
    if (
        type(raw_source_hex) is str
        and len(raw_source_hex) > 2 * _MAX_RECORD_RAW_SOURCE_BYTES
    ):
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE)
    raw_source = _decode_hex(
        raw_source_hex,
        maximum=_MAX_RECORD_RAW_SOURCE_BYTES,
    )
    projection_bytes = _canonical_json(
        projection,
        maximum=_MAX_RECORD_PROJECTION_BYTES,
    )
    raw_source_byte_count = _u64(
        tree["raw_source_byte_count"],
        positive=True,
    )
    if (
        not raw_source
        or tree["field_id"] != field_id
        or tree["schema_version"] != "1"
        or tree["parser_id"] != _field_parser_id(field_id)
        or tree["native_origin_authenticated"] is not False
        or tree["portable_projection_recomputed"] is not False
        or raw_source_byte_count != len(raw_source)
        or tree["raw_source_plain_sha256"] != _plain_sha256(raw_source)
        or tree["canonical_projection_sha256"]
        != _domain_sha256(_semantic_type_id(field_id), projection_bytes)
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    _validate_canonical_projection(field_id, projection)
    return tree


def _validate_evidence_value(field_id: str, value: bytes) -> None:
    if type(value) is not bytes:
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_TYPE)
    if len(value) > _MAX_VALUE_BYTES:
        _fail(LinuxConfinementSemanticVerificationCode.INPUT_RESOURCE)
    codec = _field_codec(field_id)
    if codec == _CODEC_SHA256:
        try:
            decoded = value.decode("ascii", "strict")
        except UnicodeError:
            _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
        _sha256(decoded)
    elif codec == _CODEC_U64:
        if len(value) != 8:
            _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
        _u64(int.from_bytes(value, "big"))
    elif codec == _CODEC_NUL:
        _validate_nul_frame(field_id, value)
    elif codec == _CODEC_OCTETS:
        if not value:
            _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    elif codec == _CODEC_RECORD:
        _validate_record_envelope(field_id, value)
    else:
        _fail(LinuxConfinementSemanticVerificationCode.INTERNAL_ERROR)


def _validate_resource_components(
    subject_role_id: str,
    components: object,
) -> dict:
    if type(components) is not dict:
        _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
    kind = _SUBJECT_KIND[subject_role_id]
    expected = _RESOURCE_COMPONENT_FIELDS_BY_KIND[kind]
    result = _exact_keys(components, expected)
    if kind == "namespace":
        if (
            result["namespace_type_id"]
            != _NAMESPACE_TYPE_BY_ROLE[subject_role_id]
        ):
            _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
        for name in ("device", "inode", "owner_user_namespace_inode"):
            _u64(result[name], positive=True)
        _sha256(result["observation_record_sha256"])
    elif kind == "kernel-object":
        if (
            result["kernel_object_type_id"]
            != _KERNEL_OBJECT_TYPE_BY_ROLE[subject_role_id]
        ):
            _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
        for name in ("device", "generation", "inode"):
            _u64(result[name], positive=True)
        _sha256(result["observation_record_sha256"])
    elif kind == "content-artifact":
        _u64(result["byte_count"], positive=True)
        for name in (
            "content_sha256",
            "custody_record_sha256",
            "manifest_membership_sha256",
        ):
            _sha256(result[name])
    elif kind == "security-policy-object":
        if (
            result["security_object_type_id"]
            != _SECURITY_OBJECT_TYPE_BY_ROLE[subject_role_id]
        ):
            _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
        for name in (
            "content_sha256",
            "feature_manifest_sha256",
            "install_or_custody_record_sha256",
        ):
            _sha256(result[name])
    elif kind == "platform":
        _token(result["architecture_id"])
        for name in (
            "linux_boot_id_sha256",
            "observation_record_sha256",
            "platform_profile_sha256",
        ):
            _sha256(result[name])
    elif kind == "process-set":
        _u64(result["member_count"])
        for name in (
            "completeness_authority_record_sha256",
            "membership_sha256",
            "observation_record_sha256",
        ):
            _sha256(result[name])
    else:
        _fail(LinuxConfinementSemanticVerificationCode.INTERNAL_ERROR)
    return result


def _validate_resource_identity(
    subject_role_id: str,
    raw: bytes,
    *,
    staging_run_binding_sha256: str,
    subject_identity_table_sha256: str,
    process_identity_snapshot_sha256: str,
    linux_boot_id_sha256: str,
    linux_platform_profile_sha256: str,
) -> dict:
    tree = _exact_keys(
        _parse_canonical_object(raw, maximum=_MAX_VALUE_BYTES),
        _RESOURCE_IDENTITY_FIELDS,
    )
    if (
        tree["resource_role_id"] != subject_role_id
        or tree["identity_schema_id"] != _identity_schema_id(subject_role_id)
        or tree["schema_version"] != "1"
        or tree["native_origin_authenticated"] is not False
        or tree["staging_run_binding_sha256"] != staging_run_binding_sha256
        or tree["subject_identity_table_sha256"]
        != subject_identity_table_sha256
        or tree["process_identity_snapshot_sha256"]
        != process_identity_snapshot_sha256
        or tree["linux_boot_id_sha256"] != linux_boot_id_sha256
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    components = _validate_resource_components(
        subject_role_id,
        tree["identity_components"],
    )
    if subject_role_id == "linux-host-platform" and (
        components["linux_boot_id_sha256"] != linux_boot_id_sha256
        or components["platform_profile_sha256"]
        != linux_platform_profile_sha256
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    return tree


def _parse_subject_binding(
    value: object,
    *,
    expected_role_id: str,
    staging_run_binding_sha256: str,
    subject_identity_table_sha256: str,
    process_identity_snapshot_sha256: str,
    snapshot: _Snapshot,
) -> _SubjectView:
    tree = _exact_keys(value, _SUBJECT_BINDING_FIELDS)
    role_id = _token(tree["subject_role_id"])
    if role_id != expected_role_id:
        _fail(LinuxConfinementSemanticVerificationCode.ORDER_INVALID)
    try:
        kind_id = _SUBJECT_KIND[role_id]
    except KeyError:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    raw = _decode_hex(
        tree["canonical_identity_hex"],
        maximum=_MAX_VALUE_BYTES,
    )
    schema_id = _identity_schema_id(role_id)
    identity_byte_count = _u64(
        tree["identity_byte_count"],
        positive=True,
    )
    if (
        not raw
        or tree["artifact_type"] != _SUBJECT_BINDING_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or identity_byte_count != len(raw)
        or tree["identity_plain_sha256"] != _plain_sha256(raw)
        or tree["identity_schema_id"] != schema_id
        or tree["identity_sha256"] != _domain_sha256(schema_id, raw)
        or tree["origin_authenticated"] is not False
        or tree["subject_kind_id"] != kind_id
        or tree["staging_run_binding_sha256"] != staging_run_binding_sha256
        or tree["subject_identity_table_sha256"]
        != subject_identity_table_sha256
        or tree["process_identity_snapshot_sha256"]
        != process_identity_snapshot_sha256
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    resource_identity = None
    if kind_id == "process-role":
        try:
            observed_instance = raw.decode("ascii", "strict")
        except UnicodeError:
            _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
        _sha256(observed_instance)
        task_by_slot = {item.task_slot_id: item for item in snapshot.tasks}
        expected_instance = task_by_slot[
            _ROLE_TO_SLOT[role_id]
        ].kernel_task_instance_sha256
        if (
            expected_instance == _ZERO_SHA256
            or observed_instance != expected_instance
        ):
            _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    else:
        resource_identity = _validate_resource_identity(
            role_id,
            raw,
            staging_run_binding_sha256=staging_run_binding_sha256,
            subject_identity_table_sha256=subject_identity_table_sha256,
            process_identity_snapshot_sha256=(
                process_identity_snapshot_sha256
            ),
            linux_boot_id_sha256=snapshot.linux_boot_id_sha256,
            linux_platform_profile_sha256=(
                snapshot.linux_platform_profile_sha256
            ),
        )
    return _SubjectView(
        role_id=role_id,
        identity_sha256=tree["identity_sha256"],
        raw=raw,
        resource_identity=resource_identity,
    )


def _parse_evidence_member(
    value: object,
    *,
    expected_field_id: str,
    observation_id: str,
    expected_subject_refs: list,
    staging_run_binding_sha256: str,
    subject_identity_table_sha256: str,
    process_identity_snapshot_sha256: str,
) -> _EvidenceView:
    tree = _exact_keys(value, _EVIDENCE_MEMBER_FIELDS)
    field_id = _token(tree["field_id"])
    if field_id != expected_field_id:
        _fail(LinuxConfinementSemanticVerificationCode.ORDER_INVALID)
    raw = _decode_hex(
        tree["canonical_value_hex"],
        maximum=_MAX_VALUE_BYTES,
    )
    semantic_type_id = _semantic_type_id(field_id)
    value_byte_count = _u64(tree["value_byte_count"])
    if (
        tree["artifact_type"] != _EVIDENCE_MEMBER_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or tree["comparator_id"] != _field_comparator(field_id)
        or tree["semantic_type_id"] != semantic_type_id
        or value_byte_count != len(raw)
        or tree["value_codec_id"] != _field_codec(field_id)
        or tree["value_plain_sha256"] != _plain_sha256(raw)
        or tree["value_sha256"] != _domain_sha256(semantic_type_id, raw)
        or tree["staging_run_binding_sha256"] != staging_run_binding_sha256
        or tree["subject_identity_table_sha256"]
        != subject_identity_table_sha256
        or tree["process_identity_snapshot_sha256"]
        != process_identity_snapshot_sha256
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    projection = None
    if _field_codec(field_id) == _CODEC_RECORD:
        projection = _validate_record_envelope(
            field_id,
            raw,
        )["canonical_projection"]
        if (
            projection["observation_id"] != observation_id
            or projection["staging_run_binding_sha256"]
            != staging_run_binding_sha256
            or projection["subject_identity_table_sha256"]
            != subject_identity_table_sha256
            or projection["process_identity_snapshot_sha256"]
            != process_identity_snapshot_sha256
            or not _typed_equal(
                projection["subject_identity_refs"],
                expected_subject_refs,
            )
        ):
            _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    else:
        _validate_evidence_value(field_id, raw)
    return _EvidenceView(
        field_id=field_id,
        raw=raw,
        projection=projection,
    )


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


def _resource_views(
    subjects: Tuple[_SubjectView, ...],
) -> Tuple[dict, dict]:
    components = {}
    identities = {}
    for subject in subjects:
        if subject.resource_identity is None:
            continue
        components[subject.role_id] = subject.resource_identity[
            "identity_components"
        ]
        identities[subject.role_id] = subject.identity_sha256
    return components, identities


def _evidence_sha256_value(raw: bytes) -> str:
    try:
        result = raw.decode("ascii", "strict")
    except UnicodeError:
        _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
    return _sha256(result)


def _join_resource_record_components(
    resource_components: dict,
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
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)


def _join_optional_digest(claimed: str, expected: str) -> None:
    if claimed not in ("", _ZERO_SHA256) and claimed != expected:
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)


def _validate_resource_projection_joins(
    subjects: Tuple[_SubjectView, ...],
    evidence: Tuple[_EvidenceView, ...],
    projection_values: dict,
) -> None:
    resource_components, resource_identities = _resource_views(subjects)
    members = {item.field_id: item.raw for item in evidence}
    for field_id, role_id, component_id in _U64_RESOURCE_EVIDENCE_JOINS:
        if field_id not in members or role_id not in resource_components:
            continue
        observed = int.from_bytes(members[field_id], "big")
        if observed != resource_components[role_id][component_id]:
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    for field_id, role_id, component_id in (
        _SHA256_RESOURCE_EVIDENCE_JOINS
    ):
        if field_id not in members or role_id not in resource_components:
            continue
        if (
            _evidence_sha256_value(members[field_id])
            != resource_components[role_id][component_id]
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
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
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    if "architecture-record" in projection_values:
        components = resource_components.get("linux-host-platform")
        if (
            components is not None
            and projection_values["architecture-record"][
                "architecture_id"
            ]
            != components["architecture_id"]
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    if "kernel-release-and-build-record" in projection_values:
        components = resource_components.get("linux-host-platform")
        if (
            components is not None
            and projection_values["kernel-release-and-build-record"][
                "boot_id_sha256"
            ]
            != components["linux_boot_id_sha256"]
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    if "linux-security-feature-probe-record" in projection_values:
        components = resource_components.get("linux-host-platform")
        if (
            components is not None
            and projection_values[
                "linux-security-feature-probe-record"
            ]["platform_profile_sha256"]
            != components["platform_profile_sha256"]
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
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
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
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
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    barrier_field = (
        "stage1-barrier-pipe-kernel-object-identity-record"
    )
    if barrier_field in projection_values:
        _join_resource_record_components(
            resource_components,
            "stage1-barrier",
            projection_values[barrier_field]["read_end"],
            (
                "device",
                "inode",
                "generation",
                "kernel_object_type_id",
            ),
        )
    read_block_field = "pidfd-bound-stage1-barrier-read-block-record"
    if read_block_field in projection_values:
        expected = resource_identities.get("stage1-barrier")
        if (
            expected is not None
            and projection_values[read_block_field][
                "barrier_identity_sha256"
            ]
            != expected
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    release_field = "stage1-and-stage2-release-record"
    if release_field in projection_values:
        expected = resource_identities.get("stage1-barrier")
        if expected is not None:
            _join_optional_digest(
                projection_values[release_field]["stage1"][
                    "release_channel_identity_sha256"
                ],
                expected,
            )
    for field_id, role_id in (
        ("bootstrap-rootfs-membership-record", "staging-bootstrap"),
        ("interpreter-rootfs-membership-record", "sandbox-interpreter"),
    ):
        if field_id not in projection_values:
            continue
        components = resource_components.get(role_id)
        if components is not None:
            _join_optional_digest(
                projection_values[field_id]["content_sha256"],
                components["content_sha256"],
            )
    loader_field = "supervisor-loader-resolution-record"
    if loader_field in projection_values:
        components = resource_components.get(
            "supervisor-dependency-closure"
        )
        if components is not None:
            _join_optional_digest(
                projection_values[loader_field]["closure_sha256"],
                components["content_sha256"],
            )


def _task_join_catalog(
    snapshots: Tuple[_Snapshot, ...],
) -> dict:
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
        for slot_id in _TASK_SLOTS
    }
    for snapshot in snapshots:
        for task in snapshot.tasks:
            row = result[task.task_slot_id]
            instance_sha256 = task.kernel_task_instance_sha256
            if instance_sha256 != _ZERO_SHA256:
                if (
                    row["instance_sha256"]
                    and row["instance_sha256"] != instance_sha256
                ):
                    _fail(
                        LinuxConfinementSemanticVerificationCode
                        .BINDING_MISMATCH
                    )
                row["instance_sha256"] = instance_sha256
                if row["host_tgid"] not in (0, task.host_tgid):
                    _fail(
                        LinuxConfinementSemanticVerificationCode
                        .BINDING_MISMATCH
                    )
                row["host_tgid"] = task.host_tgid
                if (
                    row["pidfd_acquisition_method_id"]
                    and row["pidfd_acquisition_method_id"]
                    != task.pidfd_acquisition_method_id
                ):
                    _fail(
                        LinuxConfinementSemanticVerificationCode
                        .BINDING_MISMATCH
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
    catalog: dict,
    task_slot_id: str,
    digest: str,
) -> None:
    if task_slot_id not in catalog or digest in ("", _ZERO_SHA256):
        return
    if digest != catalog[task_slot_id]["instance_sha256"]:
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)


def _join_task_record(
    catalog: dict,
    task_slot_id: str,
    record_field_id: str,
    digest: str,
) -> None:
    if task_slot_id not in catalog or digest in ("", _ZERO_SHA256):
        return
    if digest not in catalog[task_slot_id][record_field_id]:
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)


def _join_role_instance(
    catalog: dict,
    role_id: str,
    digest: str,
) -> None:
    if role_id in _ROLE_TO_SLOT:
        _join_task_instance(catalog, _ROLE_TO_SLOT[role_id], digest)


def _join_task_reference_bundle(
    catalog: dict,
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
    projection_values: dict,
    snapshots: Tuple[_Snapshot, ...],
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
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    read_block_field = "pidfd-bound-stage1-barrier-read-block-record"
    if read_block_field in projection_values:
        record = projection_values[read_block_field]
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
    release_field = "stage1-and-stage2-release-record"
    if release_field in projection_values:
        _join_task_instance(
            catalog,
            "application-task",
            projection_values[release_field]["stage2"][
                "target_task_instance_sha256"
            ],
        )
    if "clone3-pidfd-acquisition-records" in projection_values:
        records = projection_values[
            "clone3-pidfd-acquisition-records"
        ]["records"]
        for row in records:
            slot_id = row["task_slot_id"]
            _join_task_reference_bundle(
                catalog,
                slot_id,
                row,
                instance_field_id="kernel_task_instance_sha256",
                record_field_ids=("pidfd_acquisition_record_sha256",),
            )
            if (
                slot_id in catalog
                and row["host_tgid"] != catalog[slot_id]["host_tgid"]
            ):
                _fail(
                    LinuxConfinementSemanticVerificationCode
                    .BINDING_MISMATCH
                )
    if "role-process-identity-records" in projection_values:
        roles = projection_values[
            "role-process-identity-records"
        ]["roles"]
        for row in roles:
            role_id = row["role_id"]
            slot_id = row["task_slot_id"]
            if (
                role_id in _ROLE_TO_SLOT
                and _ROLE_TO_SLOT[role_id] != slot_id
            ):
                _fail(
                    LinuxConfinementSemanticVerificationCode
                    .BINDING_MISMATCH
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
        relations = projection_values[
            "parentage-and-adoption-records"
        ]["relations"]
        for row in relations:
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
    launcher_parentage = (
        "unprivileged-preexec-launcher-parentage-record"
    )
    if launcher_parentage in projection_values:
        _join_task_instance(
            catalog,
            "supervisor-task",
            projection_values[launcher_parentage][
                "parent_task_instance_sha256"
            ],
        )
    child_parentage = "bubblewrap-setup-child-parentage-record"
    if child_parentage in projection_values:
        _join_task_instance(
            catalog,
            "monitor-task",
            projection_values[child_parentage][
                "parent_task_instance_sha256"
            ],
        )
    child_pidfd = "bubblewrap-setup-child-pidfd-acquisition-record"
    if child_pidfd in projection_values:
        record = projection_values[child_pidfd]
        if (
            record["pidfd_acquisition_method_id"]
            != catalog["pid1-task"]["pidfd_acquisition_method_id"]
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    child_reap = (
        "bubblewrap-setup-child-exit-adoption-and-reap-record"
    )
    if child_reap in projection_values:
        _join_task_instance(
            catalog,
            "supervisor-task",
            projection_values[child_reap][
                "adopter_task_instance_sha256"
            ],
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
    subreaper = "subreaper-setting-and-child-inventory-record"
    if subreaper in projection_values:
        _join_task_instance(
            catalog,
            "supervisor-task",
            projection_values[subreaper][
                "supervisor_task_instance_sha256"
            ],
        )


def _require_unique_rows(
    rows: list,
    key_ids: Tuple[str, ...],
) -> set:
    keys = {tuple(row[key_id] for key_id in key_ids) for row in rows}
    if len(keys) != len(rows):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    return keys


def _validate_run_and_internal_projection_joins(
    projection_values: dict,
    topology: _Topology,
) -> None:
    if "nonce-registry-insertion-record" in projection_values:
        record = projection_values["nonce-registry-insertion-record"]
        if (
            record["supervisor_epoch_id_hex"]
            != topology.supervisor_epoch_id_hex
            or record["run_nonce_hex"] != topology.run_nonce_hex
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
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
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    if (
        "run-sequence-record" in projection_values
        and projection_values["run-sequence-record"][
            "run_sequence_number"
        ]
        != topology.run_sequence_number
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    if (
        "ready-frame-bytes-and-chunk-record" in projection_values
        and projection_values["ready-frame-bytes-and-chunk-record"][
            "run_nonce_hex"
        ]
        != topology.run_nonce_hex
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    event_rows = []
    event_field = "PRE_RELEASE_STDOUT_DRAINED-event-record"
    if event_field in projection_values:
        event_rows.append(projection_values[event_field]["event"])
    release_field = "stage1-and-stage2-release-record"
    if release_field in projection_values:
        release = projection_values[release_field]
        event_rows.extend(
            (release["stage1"]["event"], release["stage2"]["event"])
        )
    if any(
        row["staging_run_binding_sha256"]
        != topology.staging_run_binding_sha256
        for row in event_rows
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    dynamic_field = "backend-elf-dynamic-section-record"
    if dynamic_field in projection_values:
        record = projection_values[dynamic_field]
        if record["dt_needed_count"] != len(
            record["dt_needed_sonames"]
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
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
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    ready_field = "ready-frame-bytes-and-chunk-record"
    if ready_field in projection_values:
        record = projection_values[ready_field]
        if (
            record["frame_byte_count"] != len(record["frame_hex"]) // 2
            or sum(record["chunk_byte_counts"])
            != record["frame_byte_count"]
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    drain_field = "pre-release-stdout-drain-to-eagain-record"
    if drain_field in projection_values:
        record = projection_values[drain_field]
        if (
            sum(record["read_chunk_byte_counts"])
            != record["total_drained_byte_count"]
            or record["drain_start_monotonic_ns"]
            > record["drain_end_monotonic_ns"]
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    endpoint_fields = (
        (ready_field, "stdout_read_end_identity_sha256"),
        (drain_field, "stdout_read_end_identity_sha256"),
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
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    if release_field in projection_values:
        stage1 = projection_values[release_field]["stage1"]
        if stage1["release_write_count"] != (
            len(stage1["release_payload_hex"]) // 2
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
    if "cgroup-process-final-inventory" in projection_values:
        record = projection_values["cgroup-process-final-inventory"]
        if record["member_count"] != len(record["members"]):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )
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
                    LinuxConfinementSemanticVerificationCode
                    .BINDING_MISMATCH
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
                        LinuxConfinementSemanticVerificationCode
                        .BINDING_MISMATCH
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
                        LinuxConfinementSemanticVerificationCode
                        .BINDING_MISMATCH
                    )
    host_map = "host-view-final-uid-gid-map-record"
    intermediate_map = "intermediate-view-map-records"
    if (
        host_map in projection_values
        and intermediate_map in projection_values
    ):
        host_view = projection_values[host_map]
        intermediate = projection_values[intermediate_map]
        if (
            host_view["final_uid_map"] != intermediate["final_uid_map"]
            or host_view["final_gid_map"] != intermediate["final_gid_map"]
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )


def _validate_transition_projection_joins(
    observation_id: str,
    projection_values: dict,
    snapshots: Tuple[_Snapshot, ...],
) -> None:
    if observation_id != (
        "pidfd-bound-observer-helper-monitor-init-application-"
        "identities-subreaper-adoption-and-reap-observed"
    ):
        return
    transition_checks = (
        (
            (
                "unprivileged-preexec-launcher-to-monitor-same-pid-"
                "exec-and-reap-record"
            ),
            "PRE_STAGE1",
            "monitor-task",
        ),
        (
            (
                "bubblewrap-setup-child-to-sandbox-pid1-same-host-"
                "pid-lifecycle-transition-record"
            ),
            "PRE_STAGE2",
            "pid1-task",
        ),
    )
    snapshots_by_stage = {item.stage_id: item for item in snapshots}
    for field_id, stage_id, task_slot_id in transition_checks:
        if field_id not in projection_values:
            continue
        transition = projection_values[field_id]
        snapshot = snapshots_by_stage[stage_id]
        task = {
            item.task_slot_id: item for item in snapshot.tasks
        }[task_slot_id]
        if (
            transition["kernel_task_instance_sha256"]
            != task.kernel_task_instance_sha256
            or (
                transition["lifecycle_transition_record_sha256"]
                not in ("", _ZERO_SHA256)
                and transition["lifecycle_transition_record_sha256"]
                != task.lifecycle_transition_record_sha256
            )
        ):
            _fail(
                LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH
            )


def _observation_snapshot(
    schema: _ObservationSchema,
    snapshots: Tuple[_Snapshot, ...],
) -> _Snapshot:
    matches = tuple(
        item for item in snapshots if item.stage_id == schema.snapshot_stage_id
    )
    if len(matches) != 1:
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    return matches[0]


def _validate_capture_window(
    schema: _ObservationSchema,
    *,
    start: int,
    end: int,
    snapshots: Tuple[_Snapshot, ...],
) -> None:
    stage1_time = snapshots[0].capture_monotonic_timestamp_ns
    stage2_time = snapshots[1].capture_monotonic_timestamp_ns
    postrun_time = snapshots[2].capture_monotonic_timestamp_ns
    if schema.snapshot_stage_id == "PRE_STAGE1":
        valid = end <= stage1_time
    elif schema.snapshot_stage_id == "PRE_STAGE2":
        valid = start >= stage1_time and end <= stage2_time
    elif schema.observation_id == "teardown-cgroup-populated-zero-observed":
        valid = start >= stage2_time and end <= postrun_time
    elif schema.observation_id == (
        "pidfd-bound-observer-helper-monitor-init-application-"
        "identities-subreaper-adoption-and-reap-observed"
    ):
        valid = start <= stage1_time and end == postrun_time
    else:
        valid = (
            start <= stage1_time and end >= stage2_time and end <= postrun_time
        )
    if not valid:
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)


def _parse_payload(
    raw: bytes,
    *,
    topology: _Topology,
    snapshots: Tuple[_Snapshot, ...],
    pins: LinuxConfinementSemanticVerificationPinsV1,
) -> _Payload:
    tree = _exact_keys(
        _parse_canonical_object(raw, maximum=_MAX_PAYLOAD_BYTES),
        _PAYLOAD_FIELDS,
    )
    schema = _schema(tree["observation_id"])
    snapshot = _observation_snapshot(schema, snapshots)
    start = _u64(
        tree["capture_window_start_monotonic_ns"],
        positive=True,
    )
    end = _u64(
        tree["capture_window_end_monotonic_ns"],
        positive=True,
    )
    if start > end:
        _fail(LinuxConfinementSemanticVerificationCode.VALUE_INVALID)
    artifact_type = _observation_artifact_type(schema.observation_id)
    if (
        tree["artifact_type"] != artifact_type
        or tree["semantic_schema_id"] != artifact_type
        or tree["format_version"] != "1"
        or tree["family_id"] != schema.family_id
        or tree["snapshot_stage_id"] != schema.snapshot_stage_id
        or tree["lifecycle_stage_id"] != schema.lifecycle_stage_id
        or tree["trusted_producer_id"] != schema.trusted_producer_id
        or tree["procedure_id"] != schema.procedure_id
        or tree["predicate_id"] != schema.predicate_id
        or tree["receipt_leaf_id"] != schema.receipt_leaf_id
        or tree["predicate_evaluation_status_id"] != _PREDICATE_STATUS_ID
        or tree["validation_scope_id"] != _VALIDATION_SCOPE_ID
        or not _typed_equal(tree["nonclaims"], _false_nonclaims())
        or tree["semantic_payload_contract_sha256"]
        != pins.semantic_payload_contract_sha256
        or tree["staging_run_binding_sha256"]
        != topology.staging_run_binding_sha256
        or tree["subject_identity_table_sha256"] != topology.sha256
        or tree["process_identity_snapshot_sha256"] != snapshot.sha256
        or end > snapshot.capture_monotonic_timestamp_ns
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    if (
        pins.record_kind_id != "observation"
        or pins.record_id != schema.observation_id
        or pins.lifecycle_stage_id != schema.lifecycle_stage_id
        or pins.trusted_producer_id != schema.trusted_producer_id
        or pins.record_artifact_type != artifact_type
        or pins.capture_monotonic_timestamp_ns != end
    ):
        _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
    _validate_capture_window(
        schema,
        start=start,
        end=end,
        snapshots=snapshots,
    )
    subjects = tree["subject_bindings"]
    members = tree["evidence_members"]
    if type(subjects) is not list or type(members) is not list:
        _fail(LinuxConfinementSemanticVerificationCode.CANONICAL_INVALID)
    if len(subjects) != len(schema.subject_role_ids) or len(members) != len(
        schema.raw_evidence_field_ids
    ):
        _fail(LinuxConfinementSemanticVerificationCode.ORDER_INVALID)
    subject_views = tuple(
        _parse_subject_binding(
            item,
            expected_role_id=role_id,
            staging_run_binding_sha256=(topology.staging_run_binding_sha256),
            subject_identity_table_sha256=topology.sha256,
            process_identity_snapshot_sha256=snapshot.sha256,
            snapshot=snapshot,
        )
        for item, role_id in zip(subjects, schema.subject_role_ids)
    )
    expected_subject_refs = [
        {
            "subject_identity_sha256": subject.identity_sha256,
            "subject_role_id": subject.role_id,
        }
        for subject in subject_views
    ]
    evidence_views = tuple(
        _parse_evidence_member(
            item,
            expected_field_id=field_id,
            observation_id=schema.observation_id,
            expected_subject_refs=expected_subject_refs,
            staging_run_binding_sha256=(topology.staging_run_binding_sha256),
            subject_identity_table_sha256=topology.sha256,
            process_identity_snapshot_sha256=snapshot.sha256,
        )
        for item, field_id in zip(
            members,
            schema.raw_evidence_field_ids,
        )
    )
    projection_values = {
        item.field_id: item.projection["values"]
        for item in evidence_views
        if (
            item.projection is not None
            and item.projection["source_observation_available"]
        )
    }
    _validate_resource_projection_joins(
        subject_views,
        evidence_views,
        projection_values,
    )
    _validate_task_projection_joins(projection_values, snapshots)
    _validate_run_and_internal_projection_joins(
        projection_values,
        topology,
    )
    _validate_transition_projection_joins(
        schema.observation_id,
        projection_values,
        snapshots,
    )
    return _Payload(
        raw=raw,
        plain_sha256=_plain_sha256(raw),
        sha256=_domain_sha256(artifact_type, raw),
        schema=schema,
        staging_run_binding_sha256=topology.staging_run_binding_sha256,
        subject_identity_table_sha256=topology.sha256,
        process_identity_snapshot_sha256=snapshot.sha256,
        capture_window_start_monotonic_ns=start,
        capture_window_end_monotonic_ns=end,
        subject_binding_count=len(subjects),
        evidence_member_count=len(members),
        subjects=subject_views,
        evidence=evidence_views,
    )


@dataclass(frozen=True)
class LinuxConfinementSemanticVerificationResultV1:
    """Non-authoritative result from the implementation-separated verifier."""

    subject_identity_table_byte_count: int
    subject_identity_table_plain_sha256: str
    subject_identity_table_sha256: str
    process_identity_snapshot_sha256s: Tuple[str, ...]
    observation_payload_byte_count: int
    observation_payload_plain_sha256: str
    observation_payload_sha256: str
    semantic_payload_contract_sha256: str
    staging_run_binding_sha256: str
    observation_id: str
    family_id: str
    snapshot_stage_id: str
    lifecycle_stage_id: str
    capture_window_start_monotonic_ns: int
    capture_window_end_monotonic_ns: int
    subject_binding_count: int
    evidence_member_count: int
    artifact_type: str = field(
        default=(LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_RESULT_ARTIFACT_TYPE),
        init=False,
    )
    format_version: str = field(default="1", init=False)
    verifier_id: str = field(
        default=LINUX_CONFINEMENT_IMPLEMENTATION_SEPARATED_VERIFIER_ID,
        init=False,
    )
    implementation_status_id: str = field(
        default=(LINUX_CONFINEMENT_SEMANTIC_VERIFIER_IMPLEMENTATION_STATUS),
        init=False,
    )
    validation_status_id: str = field(
        default=LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_STATUS,
        init=False,
    )
    canonical_bytes_validated: bool = field(default=True, init=False)
    external_record_metadata_pins_matched: bool = field(
        default=True,
        init=False,
    )
    semantic_contract_pin_matched: bool = field(
        default=True,
        init=False,
    )
    topology_snapshot_chain_validated: bool = field(
        default=True,
        init=False,
    )
    member_codecs_and_bindings_validated: bool = field(
        default=True,
        init=False,
    )
    projection_recursive_schemas_validated: bool = field(
        default=True,
        init=False,
    )
    available_self_contained_joins_validated: bool = field(
        default=True,
        init=False,
    )
    linux_execution_observed: bool = field(default=False, init=False)
    producer_origin_authenticated: bool = field(
        default=False,
        init=False,
    )
    evidence_custody_authenticated: bool = field(
        default=False,
        init=False,
    )
    kernel_semantics_validated: bool = field(
        default=False,
        init=False,
    )
    policy_predicate_evaluated: bool = field(
        default=False,
        init=False,
    )
    linux_confinement_established: bool = field(
        default=False,
        init=False,
    )
    release_safety_established: bool = field(
        default=False,
        init=False,
    )
    hostile_controls_executed: bool = field(
        default=False,
        init=False,
    )
    teardown_established: bool = field(default=False, init=False)
    same_binding_replay_rejected: bool = field(
        default=False,
        init=False,
    )
    native_source_projection_relation_validated: bool = field(
        default=False,
        init=False,
    )
    policy_value_equality_evaluated: bool = field(
        default=False,
        init=False,
    )
    external_native_transcript_equality_validated: bool = field(
        default=False,
        init=False,
    )
    source_observation_status_verified: bool = field(
        default=False,
        init=False,
    )
    decision_eligible: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (
            type(self) is not LinuxConfinementSemanticVerificationResultV1
            or self.artifact_type
            != LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_RESULT_ARTIFACT_TYPE
            or self.format_version != "1"
            or self.verifier_id
            != LINUX_CONFINEMENT_IMPLEMENTATION_SEPARATED_VERIFIER_ID
            or self.implementation_status_id
            != LINUX_CONFINEMENT_SEMANTIC_VERIFIER_IMPLEMENTATION_STATUS
            or self.validation_status_id
            != LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_STATUS
            or type(self.subject_identity_table_byte_count) is not int
            or self.subject_identity_table_byte_count <= 0
            or self.subject_identity_table_byte_count
            > _MAX_SUBJECT_TABLE_BYTES
            or type(self.observation_payload_byte_count) is not int
            or self.observation_payload_byte_count <= 0
            or self.observation_payload_byte_count > _MAX_PAYLOAD_BYTES
            or type(self.process_identity_snapshot_sha256s) is not tuple
            or len(self.process_identity_snapshot_sha256s) != 3
        ):
            _fail(LinuxConfinementSemanticVerificationCode.RESULT_INVALID)
        digest_names = (
            "subject_identity_table_plain_sha256",
            "subject_identity_table_sha256",
            "observation_payload_plain_sha256",
            "observation_payload_sha256",
            "semantic_payload_contract_sha256",
            "staging_run_binding_sha256",
        )
        digest_values = (
            tuple(getattr(self, name) for name in digest_names)
            + self.process_identity_snapshot_sha256s
        )
        if any(
            type(value) is not str
            or _SHA256_RE.fullmatch(value) is None
            or value == _ZERO_SHA256
            for value in digest_values
        ):
            _fail(LinuxConfinementSemanticVerificationCode.RESULT_INVALID)
        try:
            schema = _SCHEMA_BY_ID[self.observation_id]
        except (KeyError, TypeError):
            _fail(LinuxConfinementSemanticVerificationCode.RESULT_INVALID)
        if (
            type(self.family_id) is not str
            or self.family_id != schema.family_id
            or type(self.snapshot_stage_id) is not str
            or self.snapshot_stage_id != schema.snapshot_stage_id
            or type(self.lifecycle_stage_id) is not str
            or self.lifecycle_stage_id != schema.lifecycle_stage_id
            or type(self.capture_window_start_monotonic_ns) is not int
            or type(self.capture_window_end_monotonic_ns) is not int
            or self.capture_window_start_monotonic_ns <= 0
            or self.capture_window_end_monotonic_ns
            < self.capture_window_start_monotonic_ns
            or self.capture_window_end_monotonic_ns >= 1 << 64
            or type(self.subject_binding_count) is not int
            or self.subject_binding_count != len(schema.subject_role_ids)
            or type(self.evidence_member_count) is not int
            or self.evidence_member_count != len(schema.raw_evidence_field_ids)
        ):
            _fail(LinuxConfinementSemanticVerificationCode.RESULT_INVALID)
        true_fields = (
            "canonical_bytes_validated",
            "external_record_metadata_pins_matched",
            "semantic_contract_pin_matched",
            "topology_snapshot_chain_validated",
            "member_codecs_and_bindings_validated",
            "projection_recursive_schemas_validated",
            "available_self_contained_joins_validated",
        )
        false_fields = (
            "linux_execution_observed",
            "producer_origin_authenticated",
            "evidence_custody_authenticated",
            "kernel_semantics_validated",
            "policy_predicate_evaluated",
            "linux_confinement_established",
            "release_safety_established",
            "hostile_controls_executed",
            "teardown_established",
            "same_binding_replay_rejected",
            "native_source_projection_relation_validated",
            "policy_value_equality_evaluated",
            "external_native_transcript_equality_validated",
            "source_observation_status_verified",
            "decision_eligible",
        )
        if any(getattr(self, name) is not True for name in true_fields):
            _fail(LinuxConfinementSemanticVerificationCode.RESULT_INVALID)
        if any(getattr(self, name) is not False for name in false_fields):
            _fail(LinuxConfinementSemanticVerificationCode.RESULT_INVALID)


def _verification_result(
    *,
    topology: _Topology,
    snapshots: Tuple[_Snapshot, ...],
    payload: _Payload,
    pins: LinuxConfinementSemanticVerificationPinsV1,
) -> LinuxConfinementSemanticVerificationResultV1:
    return LinuxConfinementSemanticVerificationResultV1(
        subject_identity_table_byte_count=len(topology.raw),
        subject_identity_table_plain_sha256=_plain_sha256(topology.raw),
        subject_identity_table_sha256=topology.sha256,
        process_identity_snapshot_sha256s=tuple(
            item.sha256 for item in snapshots
        ),
        observation_payload_byte_count=len(payload.raw),
        observation_payload_plain_sha256=payload.plain_sha256,
        observation_payload_sha256=payload.sha256,
        semantic_payload_contract_sha256=(
            pins.semantic_payload_contract_sha256
        ),
        staging_run_binding_sha256=payload.staging_run_binding_sha256,
        observation_id=payload.schema.observation_id,
        family_id=payload.schema.family_id,
        snapshot_stage_id=payload.schema.snapshot_stage_id,
        lifecycle_stage_id=payload.schema.lifecycle_stage_id,
        capture_window_start_monotonic_ns=(
            payload.capture_window_start_monotonic_ns
        ),
        capture_window_end_monotonic_ns=(
            payload.capture_window_end_monotonic_ns
        ),
        subject_binding_count=payload.subject_binding_count,
        evidence_member_count=payload.evidence_member_count,
    )


def _stable_resource_components(role_id: str, components: dict) -> tuple:
    kind_id = _SUBJECT_KIND[role_id]
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
        _fail(LinuxConfinementSemanticVerificationCode.INTERNAL_ERROR)
    return tuple(components[name] for name in names)


def _aggregate_join_values(payload: _Payload) -> tuple:
    resources = []
    platform_architectures = []
    for subject in payload.subjects:
        identity = subject.resource_identity
        if identity is None:
            continue
        role_id = subject.role_id
        components = identity["identity_components"]
        resources.append(
            (
                role_id,
                _stable_resource_components(role_id, components),
            )
        )
        if role_id == "linux-host-platform":
            platform_architectures.append(components["architecture_id"])
    architecture_ids = []
    seccomp_architecture_ids = []
    elf_machine_ids = []
    for member in payload.evidence:
        if (
            member.projection is None
            or not member.projection["source_observation_available"]
        ):
            continue
        values = member.projection["values"]
        if member.field_id == "architecture-record":
            architecture_ids.append(values["architecture_id"])
        elif member.field_id == "seccomp-status-and-filter-count-record":
            seccomp_architecture_ids.append(values["architecture_id"])
        elif member.field_id in (
            "backend-elf-program-header-record",
            "interpreter-elf-linkage-record",
        ):
            elf_machine_ids.append(values["machine_id"])
    return (
        tuple(resources),
        tuple(architecture_ids),
        tuple(seccomp_architecture_ids),
        tuple(elf_machine_ids),
        tuple(platform_architectures),
    )


def verify_linux_confinement_semantic_payload(
    raw_topology_bytes: bytes,
    raw_snapshot_bytes: Tuple[bytes, ...],
    raw_observation_payload: bytes,
    expected_pins: LinuxConfinementSemanticVerificationPinsV1,
) -> LinuxConfinementSemanticVerificationResultV1:
    """Validate one portable observation with separated implementation."""

    try:
        _validated_pins(expected_pins)
        topology = _parse_topology(raw_topology_bytes, expected_pins)
        snapshots = _parse_snapshot_chain(
            raw_snapshot_bytes,
            topology=topology,
            pins=expected_pins,
        )
        payload = _parse_payload(
            raw_observation_payload,
            topology=topology,
            snapshots=snapshots,
            pins=expected_pins,
        )
        return _verification_result(
            topology=topology,
            snapshots=snapshots,
            payload=payload,
            pins=expected_pins,
        )
    except LinuxConfinementSemanticVerificationError:
        raise
    except Exception:
        _fail(LinuxConfinementSemanticVerificationCode.INTERNAL_ERROR)


def verify_linux_confinement_semantic_payload_set(
    raw_topology_bytes: bytes,
    raw_snapshot_bytes: Tuple[bytes, ...],
    raw_observation_payloads: Tuple[bytes, ...],
    expected_pins: Tuple[LinuxConfinementSemanticVerificationPinsV1, ...],
) -> Tuple[LinuxConfinementSemanticVerificationResultV1, ...]:
    """Validate all 24 payloads plus their aggregate semantic joins."""

    try:
        if (
            type(raw_observation_payloads) is not tuple
            or type(expected_pins) is not tuple
            or any(
                type(item) is not bytes for item in raw_observation_payloads
            )
            or any(
                type(item) is not LinuxConfinementSemanticVerificationPinsV1
                for item in expected_pins
            )
        ):
            _fail(LinuxConfinementSemanticVerificationCode.INPUT_TYPE)
        if len(raw_observation_payloads) != len(
            _AGGREGATE_OBSERVATION_IDS
        ) or len(expected_pins) != len(_AGGREGATE_OBSERVATION_IDS):
            _fail(LinuxConfinementSemanticVerificationCode.ORDER_INVALID)
        for pins in expected_pins:
            _validated_pins(pins)
        first_pins = expected_pins[0]
        shared_pin_values = (
            first_pins.staging_run_binding_sha256,
            first_pins.observation_subject_identity,
            first_pins.policy_sha256,
            first_pins.linux_platform_profile_sha256,
            first_pins.semantic_payload_contract_sha256,
        )
        if any(
            (
                pins.staging_run_binding_sha256,
                pins.observation_subject_identity,
                pins.policy_sha256,
                pins.linux_platform_profile_sha256,
                pins.semantic_payload_contract_sha256,
            )
            != shared_pin_values
            for pins in expected_pins[1:]
        ):
            _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
        topology = _parse_topology(raw_topology_bytes, first_pins)
        snapshots = _parse_snapshot_chain(
            raw_snapshot_bytes,
            topology=topology,
            pins=first_pins,
        )
        payloads = tuple(
            _parse_payload(
                raw,
                topology=topology,
                snapshots=snapshots,
                pins=pins,
            )
            for raw, pins in zip(
                raw_observation_payloads,
                expected_pins,
            )
        )
        if (
            tuple(item.schema.observation_id for item in payloads)
            != _AGGREGATE_OBSERVATION_IDS
        ):
            _fail(LinuxConfinementSemanticVerificationCode.ORDER_INVALID)
        stable_resources = {}
        architecture_ids = []
        seccomp_architecture_ids = []
        elf_machine_ids = []
        platform_architectures = []
        for payload in payloads:
            (
                resources,
                architectures,
                seccomp_architectures,
                elf_machines,
                platforms,
            ) = _aggregate_join_values(payload)
            architecture_ids.extend(architectures)
            seccomp_architecture_ids.extend(seccomp_architectures)
            elf_machine_ids.extend(elf_machines)
            platform_architectures.extend(platforms)
            for role_id, stable in resources:
                prior = stable_resources.setdefault(role_id, stable)
                if prior != stable:
                    _fail(
                        LinuxConfinementSemanticVerificationCode
                        .BINDING_MISMATCH
                    )
        comparable_architectures = set(
            architecture_ids
            + seccomp_architecture_ids
            + platform_architectures
        )
        if (
            len(platform_architectures) != 2
            or len(comparable_architectures) != 1
            or len(set(elf_machine_ids)) > 1
        ):
            _fail(LinuxConfinementSemanticVerificationCode.BINDING_MISMATCH)
        return tuple(
            _verification_result(
                topology=topology,
                snapshots=snapshots,
                payload=payload,
                pins=pins,
            )
            for payload, pins in zip(payloads, expected_pins)
        )
    except LinuxConfinementSemanticVerificationError:
        raise
    except Exception:
        _fail(LinuxConfinementSemanticVerificationCode.INTERNAL_ERROR)


def linux_confinement_semantic_verification_result_bytes(
    value: LinuxConfinementSemanticVerificationResultV1,
) -> bytes:
    """Serialize one non-authoritative verification result."""

    if type(value) is not LinuxConfinementSemanticVerificationResultV1:
        _fail(LinuxConfinementSemanticVerificationCode.RESULT_INVALID)
    try:
        LinuxConfinementSemanticVerificationResultV1.__post_init__(value)
        tree = {
            item.name: getattr(value, item.name)
            for item in fields(LinuxConfinementSemanticVerificationResultV1)
        }
        tree["process_identity_snapshot_sha256s"] = list(
            value.process_identity_snapshot_sha256s
        )
        raw = _canonical_json(
            tree,
            maximum=(
                MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_RESULT_BYTES
            ),
        )
    except LinuxConfinementSemanticVerificationError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementSemanticVerificationCode.RESULT_INVALID)
    return raw


def linux_confinement_semantic_verification_result_sha256(
    value: LinuxConfinementSemanticVerificationResultV1,
) -> str:
    """Return the domain digest of one verification result."""

    return _domain_sha256(
        LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_RESULT_DIGEST_DOMAIN,
        linux_confinement_semantic_verification_result_bytes(value),
    )


def validate_linux_confinement_semantic_verification_result(
    value: LinuxConfinementSemanticVerificationResultV1,
    raw_topology_bytes: bytes,
    raw_snapshot_bytes: Tuple[bytes, ...],
    raw_observation_payload: bytes,
    expected_pins: LinuxConfinementSemanticVerificationPinsV1,
) -> LinuxConfinementSemanticVerificationResultV1:
    """Rerun raw verification and require exact result identity."""

    if type(value) is not LinuxConfinementSemanticVerificationResultV1:
        _fail(LinuxConfinementSemanticVerificationCode.RESULT_INVALID)
    linux_confinement_semantic_verification_result_bytes(value)
    expected = verify_linux_confinement_semantic_payload(
        raw_topology_bytes,
        raw_snapshot_bytes,
        raw_observation_payload,
        expected_pins,
    )
    if value != expected:
        _fail(LinuxConfinementSemanticVerificationCode.RESULT_INVALID)
    return expected


def _frozen_plan_observation_rows() -> tuple:
    return tuple(
        (
            item.observation_id,
            item.lifecycle_stage_id,
            item.trusted_producer_id,
            item.procedure_id,
            item.predicate_id,
            item.receipt_leaf_id,
            item.subject_role_ids,
            item.raw_evidence_field_ids,
        )
        for item in _OBSERVATION_SCHEMAS
    )


def _public_plan_observation_rows() -> tuple:
    plan = linux_confinement_evidence_plan_tree()
    specs = plan["observation_specs"]
    if type(specs) is not list:
        raise TypeError
    return tuple(
        (
            item["item_id"],
            item["lifecycle_stage_id"],
            item["trusted_producer_id"],
            item["procedure_id"],
            item["predicate_id"],
            item["receipt_leaf_id"],
            tuple(item["subject_role_ids"]),
            tuple(item["raw_evidence_field_ids"]),
        )
        for item in specs
    )


def _public_aggregate_observation_ids() -> tuple:
    plan = linux_confinement_evidence_plan_tree()
    gates = plan["release_gate_specs"]
    postrun = plan["postrun_finalized_observation_ids"]
    if type(gates) is not list or len(gates) != 2 or type(postrun) is not list:
        raise TypeError
    return tuple(
        gates[0]["required_observation_ids"]
        + gates[1]["required_observation_ids"]
        + postrun
    )


def _validate_frozen_contracts() -> None:
    policy = "11" * 32
    epoch = "22" * 32
    nonce = "33" * 32
    try:
        drift = (
            tuple(LINUX_CONFINEMENT_REQUIRED_OBSERVATION_IDS)
            != _OBSERVATION_IDS
            or tuple(LINUX_CONFINEMENT_PROCESS_IDENTITY_ROLE_IDS)
            != _PROCESS_ROLES
            or _public_plan_observation_rows()
            != _frozen_plan_observation_rows()
            or _public_aggregate_observation_ids()
            != _AGGREGATE_OBSERVATION_IDS
            or len(_OBSERVATION_SCHEMAS) != 24
            or sum(
                len(item.raw_evidence_field_ids)
                for item in _OBSERVATION_SCHEMAS
            )
            != 112
            or len(_RAW_FIELD_IDS) != 111
            or len(_PROJECTION_SCHEMA_BY_FIELD) != 84
            or set(_PROJECTION_SCHEMA_BY_FIELD)
            != set(_CANONICAL_JSON_FIELD_IDS)
            or sum(
                1
                for schema in _OBSERVATION_SCHEMAS
                for field_id in schema.raw_evidence_field_ids
                if _field_codec(field_id) == _CODEC_RECORD
            )
            != 85
            or len(_PROJECTION_FIELD_IDS) != 11
            or len(LINUX_CONFINEMENT_SEMANTIC_JOIN_IDS) != 11
            or len(set(LINUX_CONFINEMENT_SEMANTIC_JOIN_IDS)) != 11
            or len(_SUBJECT_ROLE_IDS) != 28
            or len(_PROCESS_ROLES) != 7
            or len(_TASK_SLOTS) != 5
            or linux_confinement_semantic_verifier_contract_sha256()
            != _V1_SEMANTIC_CONTRACT_SHA256
            or _staging_run_binding(
                policy_sha256=policy,
                supervisor_epoch_id_hex=epoch,
                run_sequence_number=7,
                run_nonce_hex=nonce,
            )
            != linux_confinement_staging_run_binding_sha256(
                policy_sha256=policy,
                supervisor_epoch_id_hex=epoch,
                run_sequence_number=7,
                run_nonce_hex=nonce,
            )
        )
    except Exception as error:
        raise RuntimeError(
            _ERROR_MESSAGES[
                LinuxConfinementSemanticVerificationCode.CONTRACT_DRIFT
            ]
        ) from error
    if drift:
        raise RuntimeError(
            _ERROR_MESSAGES[
                LinuxConfinementSemanticVerificationCode.CONTRACT_DRIFT
            ]
        )


_validate_frozen_contracts()


__all__ = [
    "LINUX_CONFINEMENT_CANONICAL_JSON_PROJECTION_FIELD_IDS",
    "LINUX_CONFINEMENT_IMPLEMENTATION_SEPARATED_VERIFIER_ID",
    "LINUX_CONFINEMENT_PROJECTION_NODE_KIND_IDS",
    "LINUX_CONFINEMENT_PROJECTION_SCHEMA_ID_PREFIX",
    "LINUX_CONFINEMENT_SEMANTIC_AGGREGATE_OBSERVATION_IDS",
    "LINUX_CONFINEMENT_SEMANTIC_JOIN_IDS",
    "LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_RESULT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_RESULT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_STATUS",
    "LINUX_CONFINEMENT_SEMANTIC_VERIFIER_IMPLEMENTATION_STATUS",
    "LinuxConfinementSemanticVerificationCode",
    "LinuxConfinementSemanticVerificationError",
    "LinuxConfinementSemanticVerificationPinsV1",
    "LinuxConfinementSemanticVerificationResultV1",
    "MAXIMUM_LINUX_CONFINEMENT_SEMANTIC_VERIFICATION_RESULT_BYTES",
    "linux_confinement_semantic_verification_result_bytes",
    "linux_confinement_semantic_verification_result_sha256",
    "linux_confinement_semantic_verifier_contract_bytes",
    "linux_confinement_semantic_verifier_contract_sha256",
    "linux_confinement_semantic_verifier_contract_tree",
    "validate_linux_confinement_semantic_verification_result",
    "verify_linux_confinement_semantic_payload",
    "verify_linux_confinement_semantic_payload_set",
]
