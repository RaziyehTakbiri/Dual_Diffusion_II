"""Prospective evidence plan for the Linux confinement acceptance gate.

This module defines what a future Linux executor must retain and verify.  It
does not execute a process, inspect Linux state, run a hostile control, or
construct a positive confinement receipt.  In particular, an inventory entry
is not evidence that its procedure ran.

The fixed plan covers every observation and hostile-control identifier in the
Checkpoint-49 acceptance contract exactly once, plus one separately
classified structural receipt join.  Each entry binds a lifecycle stage,
trusted producer, subject roles, retained raw evidence, predicate,
prerequisites, positive control, exact oracles, and prospective receipt leaf.
All execution and claim states remain false or ``NOT_EXECUTED``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Final, Tuple

from .adapter_linux_confinement_acceptance import (
    LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS,
    LINUX_CONFINEMENT_MANDATORY_NONCLAIM_IDS,
    LINUX_CONFINEMENT_PERMITTED_OUTER_POSITIVE_CLAIM_IDS,
    LINUX_CONFINEMENT_REQUIRED_HOSTILE_CONTROL_IDS,
    LINUX_CONFINEMENT_REQUIRED_OBSERVATION_IDS,
    linux_confinement_acceptance_contract_sha256,
)


LINUX_CONFINEMENT_EVIDENCE_PLAN_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-evidence-plan.v1"
)
LINUX_CONFINEMENT_EVIDENCE_PLAN_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_EVIDENCE_PLAN_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_EVIDENCE_PLAN_STATUS: Final = (
    "PROSPECTIVE_UNEXECUTED"
)
LINUX_CONFINEMENT_EVIDENCE_PLAN_EXECUTION_STATUS: Final = "NOT_EXECUTED"
MAXIMUM_LINUX_CONFINEMENT_EVIDENCE_PLAN_BYTES: Final = 256 * 1024

LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-stage1-release-gate-"
    "preimage.v1"
)
LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-stage2-release-gate-"
    "preimage.v1"
)
LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-inner-v1-completion-record.v1"
)
LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_PRE_COMPLETION_RELEASE_PREFIX_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-pre-completion-release-"
    "prefix.v1"
)
_CANONICAL_PREIMAGE_ENCODING_ID: Final = (
    "length-framed-declared-field-sequence-v1"
)
_DOMAIN_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-preimage-v1"
)
_INNER_V1_COMPLETE_DIGEST_SEMANTICS_ID: Final = (
    "caller-supplied-digest-shaped-reference-to-future-canonical-"
    "native-supervisor-inner-completion-record-v1"
)

_CAPTURE_TIME_RUN_BINDING_FIELD_IDS: Final = (
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
_POSTRUN_LEAF_FINALIZATION_BINDING_FIELD_IDS: Final = (
    _CAPTURE_TIME_RUN_BINDING_FIELD_IDS
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

_STAGE1_REQUIRED_OBSERVATION_IDS: Final = (
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
_STAGE2_REQUIRED_OBSERVATION_IDS: Final = (
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
_POSTRUN_FINALIZED_OBSERVATION_IDS: Final = (
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

_RELEASE_GATE_COMMON_PREIMAGE_FIELD_IDS: Final = (
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
_STAGE2_RELEASE_GATE_ADDITIONAL_PREIMAGE_FIELD_IDS: Final = (
    "stage1-release-gate-preimage-artifact-type",
    "stage1-release-gate-preimage-byte-count",
    "stage1-release-gate-preimage-plain-sha256",
    "stage1-release-gate-preimage-sha256",
    "stage1-release-gate-event-evidence-digest-sha256",
)
_RELEASE_GATE_PRIOR_EVENT_RECORD_DIGEST_ORDERING_ID: Final = (
    "required-prior-staging-event-id-order-independent-of-arrival-v1"
)
_STAGE1_REQUIRED_PRIOR_STAGING_EVENT_IDS: Final = (
    "SUPERVISOR_CREATED",
    "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
)
_STAGE1_PRIOR_STAGING_EVENT_PARTIAL_ORDER_EDGES: Final = (
    (
        "SUPERVISOR_CREATED",
        "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
    ),
)
_STAGE2_REQUIRED_PRIOR_STAGING_EVENT_IDS: Final = (
    "SUPERVISOR_CREATED",
    "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED",
    "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED",
    "STAGE1_RELEASED",
    "READY_FRAME_ACCEPTED",
    "PIDFD_BOUND_APPLICATION_SIGSTOP_OBSERVED",
    "PRE_RELEASE_STDOUT_DRAINED",
)
_STAGE2_PRIOR_STAGING_EVENT_PARTIAL_ORDER_EDGES: Final = (
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


class LinuxConfinementEvidencePlanCode(str, Enum):
    """Closed parsing failures for the fixed prospective plan."""

    INPUT_TYPE = "LINUX_CONFINEMENT_EVIDENCE_PLAN_INPUT_TYPE"
    INPUT_RESOURCE = "LINUX_CONFINEMENT_EVIDENCE_PLAN_INPUT_RESOURCE"
    JSON_INVALID = "LINUX_CONFINEMENT_EVIDENCE_PLAN_JSON_INVALID"
    SCHEMA_INVALID = "LINUX_CONFINEMENT_EVIDENCE_PLAN_SCHEMA_INVALID"
    CANONICAL_MISMATCH = (
        "LINUX_CONFINEMENT_EVIDENCE_PLAN_CANONICAL_MISMATCH"
    )


_ERROR_MESSAGES = MappingProxyType(
    {
        LinuxConfinementEvidencePlanCode.INPUT_TYPE: (
            "Linux confinement evidence plan input has an invalid exact type"
        ),
        LinuxConfinementEvidencePlanCode.INPUT_RESOURCE: (
            "Linux confinement evidence plan input exceeds its byte ceiling"
        ),
        LinuxConfinementEvidencePlanCode.JSON_INVALID: (
            "Linux confinement evidence plan JSON is invalid"
        ),
        LinuxConfinementEvidencePlanCode.SCHEMA_INVALID: (
            "Linux confinement evidence plan schema is invalid"
        ),
        LinuxConfinementEvidencePlanCode.CANONICAL_MISMATCH: (
            "Linux confinement evidence plan bytes are not canonical"
        ),
    }
)


class LinuxConfinementEvidencePlanError(ValueError):
    """One fixed-message failure that does not reflect untrusted input."""

    def __init__(self, code: LinuxConfinementEvidencePlanCode) -> None:
        if type(code) is not LinuxConfinementEvidencePlanCode:
            raise TypeError("evidence plan code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: LinuxConfinementEvidencePlanCode) -> None:
    raise LinuxConfinementEvidencePlanError(code) from None


@dataclass(frozen=True)
class _EvidenceSpec:
    """One immutable plan entry, never an execution result."""

    item_id: str
    lifecycle_stage_id: str
    trusted_producer_id: str
    procedure_id: str
    subject_role_ids: Tuple[str, ...]
    raw_evidence_field_ids: Tuple[str, ...]
    predicate_id: str
    prerequisite_ids: Tuple[str, ...]
    positive_control_id: str
    positive_control_oracle_id: str
    success_oracle_id: str
    failure_oracle_ids: Tuple[str, ...]
    receipt_leaf_id: str
    execution_required: bool = True
    not_executed_counts_as_pass: bool = False


@dataclass(frozen=True)
class _ReleaseGateSpec:
    """One prospective caller-supplied release-gate digest contract."""

    gate_id: str
    lifecycle_stage_id: str
    staging_event_id: str
    preimage_artifact_type: str
    preimage_digest_domain: str
    canonical_preimage_encoding_id: str
    canonical_preimage_field_ids: Tuple[str, ...]
    capture_time_run_binding_field_ids: Tuple[str, ...]
    required_observation_ids: Tuple[str, ...]
    required_prior_staging_event_ids: Tuple[str, ...]
    prior_staging_event_partial_order_edges: Tuple[
        Tuple[str, str], ...
    ]
    prior_staging_event_record_digest_ordering_id: str
    predicate_id: str
    success_oracle_id: str
    failure_oracle_ids: Tuple[str, ...]
    execution_required: bool = True
    not_executed_counts_as_pass: bool = False


def _spec(
    item_id: str,
    lifecycle_stage_id: str,
    trusted_producer_id: str,
    procedure_id: str,
    subject_role_ids: Tuple[str, ...],
    raw_evidence_field_ids: Tuple[str, ...],
    predicate_id: str,
    prerequisite_ids: Tuple[str, ...],
    positive_control_id: str,
    positive_control_oracle_id: str,
    success_oracle_id: str,
    failure_oracle_ids: Tuple[str, ...],
    receipt_leaf_id: str,
) -> _EvidenceSpec:
    return _EvidenceSpec(
        item_id=item_id,
        lifecycle_stage_id=lifecycle_stage_id,
        trusted_producer_id=trusted_producer_id,
        procedure_id=procedure_id,
        subject_role_ids=subject_role_ids,
        raw_evidence_field_ids=raw_evidence_field_ids,
        predicate_id=predicate_id,
        prerequisite_ids=prerequisite_ids,
        positive_control_id=positive_control_id,
        positive_control_oracle_id=positive_control_oracle_id,
        success_oracle_id=success_oracle_id,
        failure_oracle_ids=failure_oracle_ids,
        receipt_leaf_id=receipt_leaf_id,
    )


def _release_gate_spec(
    *,
    gate_id: str,
    lifecycle_stage_id: str,
    staging_event_id: str,
    preimage_artifact_type: str,
    canonical_preimage_field_ids: Tuple[str, ...],
    required_observation_ids: Tuple[str, ...],
    required_prior_staging_event_ids: Tuple[str, ...],
    prior_staging_event_partial_order_edges: Tuple[
        Tuple[str, str], ...
    ],
    predicate_id: str,
    success_oracle_id: str,
    failure_oracle_ids: Tuple[str, ...],
) -> _ReleaseGateSpec:
    return _ReleaseGateSpec(
        gate_id=gate_id,
        lifecycle_stage_id=lifecycle_stage_id,
        staging_event_id=staging_event_id,
        preimage_artifact_type=preimage_artifact_type,
        preimage_digest_domain=preimage_artifact_type,
        canonical_preimage_encoding_id=_CANONICAL_PREIMAGE_ENCODING_ID,
        canonical_preimage_field_ids=canonical_preimage_field_ids,
        capture_time_run_binding_field_ids=(
            _CAPTURE_TIME_RUN_BINDING_FIELD_IDS
        ),
        required_observation_ids=required_observation_ids,
        required_prior_staging_event_ids=(
            required_prior_staging_event_ids
        ),
        prior_staging_event_partial_order_edges=(
            prior_staging_event_partial_order_edges
        ),
        prior_staging_event_record_digest_ordering_id=(
            _RELEASE_GATE_PRIOR_EVENT_RECORD_DIGEST_ORDERING_ID
        ),
        predicate_id=predicate_id,
        success_oracle_id=success_oracle_id,
        failure_oracle_ids=failure_oracle_ids,
    )


_RELEASE_GATE_SPECS: Final = (
    _release_gate_spec(
        gate_id="stage1-required-observation-gate",
        lifecycle_stage_id="pre-stage1-release-setup-blocked",
        staging_event_id=(
            "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED"
        ),
        preimage_artifact_type=(
            LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
        ),
        canonical_preimage_field_ids=(
            _RELEASE_GATE_COMMON_PREIMAGE_FIELD_IDS
        ),
        required_observation_ids=_STAGE1_REQUIRED_OBSERVATION_IDS,
        required_prior_staging_event_ids=(
            _STAGE1_REQUIRED_PRIOR_STAGING_EVENT_IDS
        ),
        prior_staging_event_partial_order_edges=(
            _STAGE1_PRIOR_STAGING_EVENT_PARTIAL_ORDER_EDGES
        ),
        predicate_id=(
            "stage1-canonical-preimage-exact-observation-coverage-"
            "capture-binding-and-prior-events-match-v1"
        ),
        success_oracle_id=(
            "stage1-gate-domain-digest-recomputed-and-event-payload-"
            "matches-before-release-v1"
        ),
        failure_oracle_ids=(
            "not-executed-or-missing-stage1-gate-is-not-pass-v1",
            (
                "missing-extra-reordered-or-duplicate-stage1-"
                "observation-record-fails-gate-v1"
            ),
            (
                "stage1-capture-binding-or-prior-event-identity-"
                "mismatch-fails-gate-v1"
            ),
            (
                "stage1-preimage-byte-count-plain-or-domain-digest-"
                "mismatch-fails-gate-v1"
            ),
            (
                "stage1-event-payload-missing-zero-or-not-equal-"
                "recomputed-domain-digest-fails-gate-v1"
            ),
            "stage1-gate-after-stage1-release-fails-run-v1",
        ),
    ),
    _release_gate_spec(
        gate_id="stage2-required-observation-gate",
        lifecycle_stage_id=(
            "post-ready-and-stop-observed-stdout-drained-"
            "pre-stage2-release"
        ),
        staging_event_id=(
            "STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED"
        ),
        preimage_artifact_type=(
            LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
        ),
        canonical_preimage_field_ids=(
            _RELEASE_GATE_COMMON_PREIMAGE_FIELD_IDS
            + _STAGE2_RELEASE_GATE_ADDITIONAL_PREIMAGE_FIELD_IDS
        ),
        required_observation_ids=_STAGE2_REQUIRED_OBSERVATION_IDS,
        required_prior_staging_event_ids=(
            _STAGE2_REQUIRED_PRIOR_STAGING_EVENT_IDS
        ),
        prior_staging_event_partial_order_edges=(
            _STAGE2_PRIOR_STAGING_EVENT_PARTIAL_ORDER_EDGES
        ),
        predicate_id=(
            "stage2-canonical-preimage-exact-observation-coverage-"
            "stage1-gate-capture-binding-ready-and-stop-before-drain-"
            "match-v1"
        ),
        success_oracle_id=(
            "stage2-gate-domain-digest-recomputed-and-event-payload-"
            "matches-after-ready-and-stop-then-drain-before-release-v1"
        ),
        failure_oracle_ids=(
            "not-executed-or-missing-stage2-gate-is-not-pass-v1",
            (
                "missing-extra-reordered-or-duplicate-stage2-"
                "observation-record-fails-gate-v1"
            ),
            (
                "stage2-capture-binding-or-prior-event-identity-"
                "mismatch-fails-gate-v1"
            ),
            (
                "stage1-gate-preimage-or-event-digest-mismatch-"
                "fails-stage2-gate-v1"
            ),
            (
                "stage2-preimage-byte-count-plain-or-domain-digest-"
                "mismatch-fails-gate-v1"
            ),
            (
                "stage2-event-payload-missing-zero-or-not-equal-"
                "recomputed-domain-digest-fails-gate-v1"
            ),
            (
                "stage2-gate-before-ready-and-stop-then-drain-or-after-"
                "release-fails-run-v1"
            ),
        ),
    ),
)

_INNER_V1_COMPLETION_RECORD_PREIMAGE_FIELD_IDS: Final = (
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

_BINDING_DEPENDENCY_TOPOLOGICAL_ORDER: Final = (
    "capture-time-run-binding",
    "stage1-observation-records",
    "stage1-release-gate-preimage",
    "stage1-release-gate-event",
    "stage2-observation-records",
    "stage2-release-gate-preimage",
    "stage2-release-gate-event",
    "pre-completion-release-prefix-through-stage2-released",
    "inner-v1-receipt-and-preimages",
    "inner-v1-completion-record-preimage",
    "INNER_V1_COMPLETE-event",
    "full-release-transcript",
    "postrun-leaf-finalization-envelope",
)
_BINDING_DEPENDENCY_EDGES: Final = (
    ("capture-time-run-binding", "stage1-release-gate-preimage"),
    ("stage1-observation-records", "stage1-release-gate-preimage"),
    ("stage1-release-gate-preimage", "stage1-release-gate-event"),
    ("stage1-release-gate-event", "stage2-release-gate-preimage"),
    ("capture-time-run-binding", "stage2-release-gate-preimage"),
    ("stage2-observation-records", "stage2-release-gate-preimage"),
    ("stage2-release-gate-preimage", "stage2-release-gate-event"),
    (
        "stage2-release-gate-event",
        "pre-completion-release-prefix-through-stage2-released",
    ),
    (
        "pre-completion-release-prefix-through-stage2-released",
        "inner-v1-completion-record-preimage",
    ),
    (
        "inner-v1-receipt-and-preimages",
        "inner-v1-completion-record-preimage",
    ),
    (
        "inner-v1-completion-record-preimage",
        "INNER_V1_COMPLETE-event",
    ),
    ("INNER_V1_COMPLETE-event", "full-release-transcript"),
    (
        "full-release-transcript",
        "postrun-leaf-finalization-envelope",
    ),
    (
        "INNER_V1_COMPLETE-event",
        "postrun-leaf-finalization-envelope",
    ),
)


_OBSERVATION_SPECS: Final = (
    _spec(
        "application-argv-environment-cwd-umask-matched",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-application-runtime-surface-observation-v1",
        ("application",),
        (
            "argv-nul-frame-bytes",
            "environment-nul-frame-bytes",
            "cwd-mount-and-inode-record",
            "umask-octal-record",
        ),
        "exact-application-runtime-surface-equality-v1",
        (
            "application-pidfd-bound",
            "application-confirmed-stopped",
            "policy-digest-bound",
        ),
        "known-observer-probe-runtime-surface-v1",
        "probe-argv-environment-cwd-umask-exactly-recovered-v1",
        "all-runtime-surface-fields-equal-fixed-policy-v1",
        (
            "any-field-missing-extra-or-mismatched-fails-run-v1",
            "subject-identity-or-stop-state-mismatch-fails-run-v1",
        ),
        "pre-adapter-release-observations-matched",
    ),
    _spec(
        "backend-static-sealed-executable-identity-matched",
        "pre-backend-exec",
        "privileged-supervisor-artifact-observer-v1",
        "sealed-backend-memfd-and-elf-observation-v1",
        ("backend-executable-memfd", "unprivileged-preexec-launcher"),
        (
            "backend-memfd-sha256",
            "backend-memfd-stat-record",
            "backend-memfd-flags-record",
            "backend-memfd-seals-record",
            "backend-elf-program-header-record",
            "backend-elf-dynamic-section-record",
        ),
        "static-sealed-backend-exact-policy-match-v1",
        (
            "backend-source-content-available",
            "launcher-service-identity-bound",
            "policy-digest-bound",
        ),
        "known-static-sealed-executable-memfd-v1",
        "probe-sha-mode-owner-flags-seals-and-elf-shape-match-v1",
        "backend-digest-mode-owner-flags-seals-and-static-elf-match-v1",
        (
            "unsealed-writable-dynamic-or-digest-mismatch-fails-run-v1",
            "path-backed-or-loader-dependent-backend-fails-run-v1",
        ),
        "policy-identities-matched",
    ),
    _spec(
        "capability-securebits-dumpability-profile-matched",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-credential-profile-observation-v1",
        ("application",),
        (
            "capability-set-record",
            "securebits-mask-record",
            "dumpable-record",
            "uid-gid-and-groups-record",
        ),
        "exact-zero-capability-securebits-dumpability-match-v1",
        (
            "application-pidfd-bound",
            "application-confirmed-stopped",
            "credential-observation-privilege-available",
        ),
        "known-credential-profile-probe-v1",
        "probe-capability-securebits-and-dumpability-recovered-v1",
        "all-credential-fields-equal-fixed-policy-v1",
        (
            "any-capability-or-group-present-fails-run-v1",
            "securebits-dumpability-or-id-mismatch-fails-run-v1",
        ),
        "pre-adapter-release-observations-matched",
    ),
    _spec(
        "cgroup-v2-controller-values-matched-before-release",
        "pre-stage2-application-stopped",
        "privileged-supervisor-cgroup-observer-v1",
        "host-owned-cgroup-v2-controller-observation-v1",
        ("sandbox-cgroup-v2-leaf", "application", "sandbox-pid1-reaper"),
        (
            "cgroup-controller-file-bytes",
            "cgroup-process-membership-record",
            "cgroup-events-before-release-bytes",
        ),
        "exact-cgroup-controller-and-membership-match-v1",
        (
            "cgroup-v2-delegation-validated",
            "application-pidfd-bound",
            "sandbox-pid1-bound",
        ),
        "known-host-cgroup-leaf-controller-probe-v1",
        "probe-controller-values-and-membership-exactly-recovered-v1",
        "all-controller-values-and-two-member-roles-match-policy-v1",
        (
            "missing-controller-or-value-mismatch-fails-run-v1",
            "extra-missing-or-wrong-cgroup-member-fails-run-v1",
        ),
        "named-filesystem-network-process-resource-controls-observed",
    ),
    _spec(
        "cgroup-v2-leaf-owned-by-supervisor",
        "pre-stage1-setup-blocked",
        "privileged-supervisor-cgroup-observer-v1",
        "cgroup-v2-leaf-ownership-and-delegation-observation-v1",
        ("privileged-supervisor", "sandbox-cgroup-v2-leaf"),
        (
            "cgroup-leaf-stat-record",
            "cgroup-leaf-owner-record",
            "cgroup-delegation-record",
        ),
        "supervisor-exclusive-cgroup-leaf-custody-v1",
        (
            "cgroup-v2-mounted",
            "supervisor-host-identity-bound",
            "cgroup-parent-delegated",
        ),
        "known-supervisor-owned-cgroup-leaf-v1",
        "probe-leaf-ownership-and-delegation-exactly-recovered-v1",
        "leaf-owner-delegation-and-custody-match-platform-profile-v1",
        (
            "wrong-owner-or-delegation-fails-run-v1",
            "shared-or-prepopulated-leaf-fails-run-v1",
        ),
        "named-filesystem-network-process-resource-controls-observed",
    ),
    _spec(
        "dependency-lock-identity-matched",
        "pre-first-child-artifact-validation",
        "privileged-supervisor-artifact-observer-v1",
        "dependency-lock-content-identity-observation-v1",
        ("sandbox-dependency-lock",),
        (
            "dependency-lock-byte-count",
            "dependency-lock-plain-sha256",
            "dependency-lock-domain-sha256",
        ),
        "dependency-lock-digest-equals-policy-identity-v1",
        (
            "dependency-lock-bytes-custodied",
            "policy-digest-bound",
        ),
        "known-dependency-lock-known-answer-v1",
        "probe-lock-byte-count-and-digests-match-known-answer-v1",
        "custodied-lock-digest-equals-policy-field-v1",
        (
            "missing-or-mutated-lock-fails-run-v1",
            "digest-or-byte-count-mismatch-fails-run-v1",
        ),
        "policy-identities-matched",
    ),
    _spec(
        (
            "descriptor-inventory-and-stdio-types-closed-before-"
            "adapter-import"
        ),
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-descriptor-inventory-observation-v1",
        ("application", "supervisor-stdio-peers"),
        (
            "application-fd-inventory-record",
            "fd-kernel-object-stat-records",
            "fd-access-flags-and-offset-records",
            "fd-cloexec-and-inheritance-records",
            "stdio-isatty-records",
            "supervisor-peer-custody-records",
        ),
        "exact-closed-fd-kernel-object-contract-match-v1",
        (
            "application-pidfd-bound",
            "application-confirmed-stopped",
            "supervisor-peer-endpoints-retained",
        ),
        "known-fd-topology-probe-v1",
        "probe-fd-types-directions-flags-offsets-and-peers-match-v1",
        "no-extra-fd-and-every-role-matches-fixed-contract-v1",
        (
            "extra-missing-aliased-or-wrong-type-fd-fails-run-v1",
            "tty-wrong-peer-offset-or-flag-mismatch-fails-run-v1",
        ),
        "pre-adapter-release-observations-matched",
    ),
    _spec(
        (
            "exact-two-level-uid-gid-maps-composition-empty-"
            "supplementary-groups-and-setgroups-denial-matched"
        ),
        "pre-stage1-setup-blocked",
        "privileged-supervisor-and-userns-observer-v1",
        "two-level-userns-map-and-group-observation-v1",
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
        "exact-two-level-map-composition-and-group-state-match-v1",
        (
            "bubblewrap-setup-child-pidfd-and-proc-directory-bound",
            "initial-user-namespace-fd-retained",
            "one-shot-observer-identity-bound",
        ),
        "known-two-level-userns-map-parser-fixture-v1",
        "probe-map-triplets-parent-chain-and-setgroups-match-v1",
        "both-literal-maps-composition-groups-and-denials-match-v1",
        (
            "extra-map-line-or-parent-chain-mismatch-fails-run-v1",
            "group-or-setgroups-state-mismatch-fails-run-v1",
            "observer-timeout-or-incomplete-reap-fails-run-v1",
        ),
        "pre-adapter-release-observations-matched",
    ),
    _spec(
        "immutable-runtime-rootfs-identity-matched",
        "pre-stage1-setup-blocked",
        "privileged-supervisor-mount-observer-v1",
        "content-bound-rootfs-and-old-root-observation-v1",
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
        "immutable-rootfs-content-and-mount-identity-match-v1",
        (
            "runtime-rootfs-custody-bound",
            "bubblewrap-setup-child-pidfd-bound",
            "policy-digest-bound",
        ),
        "known-immutable-rootfs-fixture-v1",
        "probe-image-manifest-mount-flags-and-old-root-state-match-v1",
        "rootfs-digests-readonly-mount-and-old-root-absence-match-v1",
        (
            "image-manifest-or-mount-mismatch-fails-run-v1",
            "writable-root-or-old-root-handle-fails-run-v1",
        ),
        "policy-identities-matched",
    ),
    _spec(
        "landlock-abi-and-ruleset-matched",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "bootstrap-landlock-installation-evidence-observation-v1",
        ("application", "adapter-stage-landlock-ruleset"),
        (
            "landlock-queried-abi-record",
            "landlock-ruleset-sha256",
            "landlock-install-return-record",
            "landlock-bootstrap-transcript-leaf",
        ),
        "exact-landlock-abi-ruleset-and-installation-match-v1",
        (
            "application-pidfd-bound",
            "bootstrap-identity-bound",
            "landlock-host-observation-method-approved",
        ),
        "known-landlock-installation-probe-v1",
        "probe-abi-ruleset-and-install-return-evidence-match-v1",
        "abi-ruleset-digest-and-successful-install-evidence-match-v1",
        (
            "unsupported-abi-or-install-failure-fails-run-v1",
            "ruleset-or-bootstrap-transcript-mismatch-fails-run-v1",
        ),
        "pre-adapter-release-observations-matched",
    ),
    _spec(
        "linux-platform-profile-matched",
        "pre-first-child-artifact-validation",
        "privileged-supervisor-platform-observer-v1",
        "linux-kernel-boot-and-feature-profile-observation-v1",
        ("linux-host-platform",),
        (
            "architecture-record",
            "kernel-release-and-build-record",
            "boot-configuration-digest",
            "linux-security-feature-probe-record",
            "platform-profile-sha256",
        ),
        "exact-linux-platform-profile-match-v1",
        (
            "dedicated-linux-host",
            "platform-profile-bytes-custodied",
        ),
        "known-platform-feature-probe-fixture-v1",
        "probe-architecture-kernel-and-feature-records-match-v1",
        "all-platform-fields-and-profile-digest-match-policy-v1",
        (
            "darwin-or-nonlinux-platform-fails-run-v1",
            "missing-feature-or-profile-mismatch-fails-run-v1",
        ),
        "approved-linux-platform-profile-matched",
    ),
    _spec(
        "mount-inventory-and-write-surface-matched",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-mountinfo-and-write-surface-observation-v1",
        ("application-mount-namespace",),
        (
            "canonical-mountinfo-record",
            "mount-propagation-record",
            "writable-path-inventory-record",
            "device-mount-flags-record",
            "forbidden-mount-type-absence-record",
        ),
        "exact-mount-topology-and-single-write-surface-match-v1",
        (
            "application-pidfd-bound",
            "application-confirmed-stopped",
            "mount-observation-privilege-available",
        ),
        "known-mount-topology-parser-fixture-v1",
        "probe-mount-types-flags-propagation-and-writes-match-v1",
        "mount-inventory-matches-policy-and-only-work-is-writable-v1",
        (
            "extra-missing-or-shared-mount-fails-run-v1",
            "unexpected-write-surface-or-mount-type-fails-run-v1",
        ),
        "named-filesystem-network-process-resource-controls-observed",
    ),
    _spec(
        "namespace-identities-distinct-before-release",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-seven-namespace-identity-observation-v1",
        ("application", "linux-host-platform"),
        (
            "application-namespace-inode-records",
            "host-namespace-inode-records",
            "namespace-parentage-record",
        ),
        "seven-required-namespaces-distinct-from-host-and-each-other-v1",
        (
            "application-pidfd-bound",
            "application-confirmed-stopped",
            "host-namespace-fds-retained",
        ),
        "known-namespace-inode-comparison-probe-v1",
        "probe-host-child-distinction-and-type-labels-match-v1",
        "all-seven-required-namespace-identities-are-distinct-v1",
        (
            "missing-wrong-type-or-host-equal-namespace-fails-run-v1",
            "namespace-parentage-mismatch-fails-run-v1",
        ),
        "pre-adapter-release-observations-matched",
    ),
    _spec(
        "network-interface-and-route-inventory-matched",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-network-namespace-inventory-observation-v1",
        ("application-network-namespace",),
        (
            "network-interface-record",
            "ipv4-route-record",
            "ipv6-route-record",
            "network-namespace-inode-record",
        ),
        "loopback-only-no-external-route-network-inventory-match-v1",
        (
            "application-pidfd-bound",
            "application-confirmed-stopped",
            "network-observation-privilege-available",
        ),
        "known-network-namespace-inventory-probe-v1",
        "probe-interface-and-route-records-exactly-recovered-v1",
        "interfaces-routes-and-namespace-identity-match-policy-v1",
        (
            "unexpected-interface-address-or-route-fails-run-v1",
            "inventory-read-or-identity-failure-fails-run-v1",
        ),
        "named-filesystem-network-process-resource-controls-observed",
    ),
    _spec(
        "no-new-privileges-observed-before-release",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-no-new-privileges-observation-v1",
        ("application",),
        ("no-new-privileges-status-record",),
        "no-new-privileges-exactly-one-v1",
        (
            "application-pidfd-bound",
            "application-confirmed-stopped",
        ),
        "known-no-new-privileges-probe-v1",
        "probe-no-new-privileges-state-exactly-recovered-v1",
        "application-no-new-privileges-state-equals-one-v1",
        (
            "zero-missing-or-unreadable-state-fails-run-v1",
            "subject-identity-mismatch-fails-run-v1",
        ),
        "pre-adapter-release-observations-matched",
    ),
    _spec(
        (
            "nonce-generation-nonreuse-and-readiness-release-"
            "transcript-matched"
        ),
        "cross-stage-run-transcript",
        "privileged-supervisor-transcript-producer-v1",
        (
            "nonce-registry-pidfd-blocked-barrier-ready-and-release-"
            "state-machine-observation-v1"
        ),
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
        (
            "nonce-freshness-pidfd-bound-exact-blocked-barrier-read-"
            "ready-frame-stop-stdout-drain-and-release-order-match-v1"
        ),
        (
            "supervisor-epoch-bound",
            "nonce-registry-below-capacity",
            "bubblewrap-setup-child-pidfd-bound",
            (
                "stage1-barrier-read-and-write-ends-kernel-object-"
                "identity-bound"
            ),
            "pidfd-bound-kernel-barrier-read-observer-available",
            "application-pidfd-bound",
            "application-pidfd-bound-sigstop-observed-before-stdout-drain",
            "stdout-read-end-kernel-object-identity-bound",
            "stdout-drained-to-eagain-before-stage2-release",
        ),
        (
            "known-pidfd-blocked-barrier-ready-and-stop-before-stdout-"
            "drain-and-release-state-machine-fixture-v1"
        ),
        (
            "probe-child-pid-status-then-exact-blocked-barrier-read-"
            "ready-and-stop-before-stdout-drain-and-release-order-"
            "match-v1"
        ),
        (
            "nonce-sequence-child-pid-status-then-pidfd-bound-exact-"
            "blocked-barrier-read-ready-and-stop-before-stdout-drain-"
            "and-two-releases-match-v1"
        ),
        (
            "zero-reused-or-wrong-sequence-nonce-fails-run-v1",
            (
                "bubblewrap-child-pid-status-alone-is-not-stage1-"
                "barrier-proof-v1"
            ),
            (
                "missing-nonblocked-or-wrong-syscall-barrier-read-"
                "observation-fails-run-v1"
            ),
            (
                "barrier-kernel-object-or-setup-pidfd-identity-"
                "mismatch-fails-run-v1"
            ),
            "malformed-duplicate-or-trailing-ready-frame-fails-run-v1",
            (
                "missing-or-pre-sigstop-PRE_RELEASE_STDOUT_DRAINED-"
                "record-fails-run-v1"
            ),
            (
                "queued-pre-release-stdout-byte-after-drain-"
                "fails-run-v1"
            ),
            (
                "stdout-drain-not-to-eagain-or-read-end-identity-"
                "mismatch-fails-run-v1"
            ),
            "missing-reordered-or-wrong-subject-release-fails-run-v1",
        ),
        "pre-adapter-release-observations-matched",
    ),
    _spec(
        (
            "pidfd-bound-observer-helper-monitor-init-application-"
            "identities-subreaper-adoption-and-reap-observed"
        ),
        "cross-stage-through-postrun",
        "dedicated-subreaper-supervisor-process-observer-v1",
        "pidfd-role-parentage-adoption-and-reap-observation-v1",
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
            (
                "bubblewrap-setup-child-exit-adoption-and-reap-"
                "record"
            ),
            "wait-reap-status-records",
            "subreaper-setting-and-child-inventory-record",
        ),
        (
            "exact-role-pidfd-launcher-and-setup-child-lifetimes-"
            "parentage-aliases-adoption-and-reap-chain-match-v1"
        ),
        (
            "supervisor-subreaper-set-before-first-child",
            "supervisor-had-zero-preexisting-children",
            "all-role-pidfds-bound",
            "launcher-to-monitor-same-pid-exec-transition-bound",
            "bubblewrap-setup-child-pidfd-bound",
            (
                "bubblewrap-setup-child-to-sandbox-pid1-same-host-pid-"
                "lifecycle-transition-bound"
            ),
        ),
        "known-pidfd-adoption-and-wait-reap-probe-v1",
        (
            "probe-role-identities-launcher-and-setup-child-lifetimes-"
            "parentage-aliases-adoption-and-reaps-match-v1"
        ),
        (
            "complete-role-inventory-launcher-exec-and-setup-child-"
            "pid1-aliases-and-policy-reap-chain-match-v1"
        ),
        (
            (
                "pid-reuse-unapproved-role-alias-or-parentage-mismatch-"
                "fails-run-v1"
            ),
            (
                "missing-or-mismatched-launcher-parentage-lifetime-"
                "exec-alias-or-reap-evidence-fails-run-v1"
            ),
            (
                "missing-or-mismatched-setup-child-pidfd-parentage-"
                "lifetime-pid1-alias-exit-or-reap-evidence-fails-"
                "run-v1"
            ),
            "missing-adoption-wait-or-reap-record-fails-run-v1",
        ),
        "postrun-cgroup-quiescence-observed",
    ),
    _spec(
        "rlimit-profile-matched-before-release",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "pidfd-bound-rlimit-profile-observation-v1",
        ("application",),
        ("soft-and-hard-rlimit-records",),
        "exact-soft-and-hard-rlimit-profile-match-v1",
        (
            "application-pidfd-bound",
            "application-confirmed-stopped",
        ),
        "known-rlimit-profile-probe-v1",
        "probe-soft-and-hard-limits-exactly-recovered-v1",
        "every-soft-and-hard-limit-equals-fixed-policy-v1",
        (
            "missing-extra-or-mismatched-limit-fails-run-v1",
            "subject-identity-or-read-failure-fails-run-v1",
        ),
        "pre-adapter-release-observations-matched",
    ),
    _spec(
        "sandbox-bootstrap-identity-matched",
        "pre-first-child-artifact-validation",
        "privileged-supervisor-artifact-observer-v1",
        "staging-bootstrap-source-and-closure-identity-observation-v1",
        ("staging-bootstrap", "bootstrap-execution-closure"),
        (
            "bootstrap-source-byte-count",
            "bootstrap-source-sha256",
            "bootstrap-execution-closure-manifest-sha256",
            "bootstrap-rootfs-membership-record",
        ),
        "bootstrap-source-and-execution-closure-policy-match-v1",
        (
            "bootstrap-source-bytes-custodied",
            (
                "bootstrap-execution-closure-committed-by-dependency-lock-"
                "and-rootfs-manifest"
            ),
            "runtime-rootfs-manifest-bound",
        ),
        "known-bootstrap-closure-known-answer-v1",
        "probe-source-closure-and-rootfs-membership-match-v1",
        "bootstrap-source-and-closed-native-dependencies-match-policy-v1",
        (
            "source-or-closure-digest-mismatch-fails-run-v1",
            "unmanifested-native-helper-or-library-fails-run-v1",
        ),
        "policy-identities-matched",
    ),
    _spec(
        "sandbox-interpreter-identity-matched",
        "pre-first-child-artifact-validation",
        "privileged-supervisor-artifact-observer-v1",
        "sandbox-interpreter-content-and-linkage-observation-v1",
        ("sandbox-interpreter",),
        (
            "interpreter-file-sha256",
            "interpreter-stat-record",
            "interpreter-elf-linkage-record",
            "interpreter-rootfs-membership-record",
        ),
        "interpreter-content-linkage-and-rootfs-membership-match-v1",
        (
            "runtime-rootfs-manifest-bound",
            "dependency-lock-bound",
        ),
        "known-interpreter-known-answer-v1",
        "probe-interpreter-digest-linkage-and-membership-match-v1",
        "interpreter-and-dependency-identities-equal-policy-v1",
        (
            "interpreter-digest-or-linkage-mismatch-fails-run-v1",
            "path-retarget-or-unmanifested-dependency-fails-run-v1",
        ),
        "policy-identities-matched",
    ),
    _spec(
        "seccomp-filter-and-architecture-observed-before-release",
        "pre-stage2-application-stopped",
        "privileged-supervisor-stage2-observer-v1",
        "two-stage-seccomp-stack-and-architecture-observation-v1",
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
        "two-distinct-architecture-bound-seccomp-filters-match-v1",
        (
            "application-pidfd-bound",
            "application-confirmed-stopped",
            "both-filter-bytes-custodied",
        ),
        "known-two-filter-seccomp-probe-v1",
        "probe-filter-count-architecture-and-digests-match-v1",
        "two-filter-stack-architecture-and-identities-match-policy-v1",
        (
            "missing-extra-or-same-filter-fails-run-v1",
            "architecture-digest-or-install-transcript-mismatch-fails-run-v1",
        ),
        "pre-adapter-release-observations-matched",
    ),
    _spec(
        "supervisor-dependency-closure-identity-matched",
        "pre-first-child-artifact-validation",
        "external-supervisor-custody-observer-v1",
        "supervisor-transitive-dependency-closure-observation-v1",
        ("privileged-supervisor", "supervisor-dependency-closure"),
        (
            "supervisor-dependency-inventory-bytes",
            "supervisor-dependency-closure-sha256",
            "supervisor-loader-resolution-record",
        ),
        "supervisor-transitive-dependency-closure-policy-match-v1",
        (
            "supervisor-bytes-externally-custodied",
            "supervisor-not-yet-started",
        ),
        "known-supervisor-dependency-closure-fixture-v1",
        "probe-closure-inventory-digest-and-loader-resolution-match-v1",
        "complete-supervisor-dependency-closure-equals-policy-v1",
        (
            "missing-extra-or-mutated-dependency-fails-run-v1",
            "runtime-loader-resolution-outside-closure-fails-run-v1",
        ),
        "reviewed-supervisor-selected",
    ),
    _spec(
        "supervisor-executable-identity-matched",
        "pre-first-child-artifact-validation",
        "external-supervisor-custody-observer-v1",
        "supervisor-executable-content-identity-observation-v1",
        ("privileged-supervisor",),
        (
            "supervisor-executable-sha256",
            "supervisor-executable-stat-record",
            "supervisor-source-sha256",
            "supervisor-feature-manifest-sha256",
        ),
        "supervisor-executable-source-and-feature-policy-match-v1",
        (
            "supervisor-executable-externally-custodied",
            "supervisor-source-and-feature-manifest-custodied",
        ),
        "known-supervisor-build-known-answer-v1",
        "probe-executable-source-and-feature-digests-match-v1",
        "all-supervisor-identities-equal-policy-v1",
        (
            "executable-source-or-feature-mismatch-fails-run-v1",
            "mutable-or-path-retargeted-supervisor-fails-run-v1",
        ),
        "reviewed-supervisor-selected",
    ),
    _spec(
        "teardown-cgroup-populated-zero-observed",
        "postrun-cleanup-complete",
        "privileged-supervisor-cgroup-observer-v1",
        "bounded-teardown-reap-and-cgroup-quiescence-observation-v1",
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
        "complete-reap-stream-eof-and-cgroup-populated-zero-v1",
        (
            "all-run-role-identities-bound",
            "teardown-clock-bound",
            "supervisor-subreaper-contract-active",
        ),
        "known-teardown-and-cgroup-quiescence-probe-v1",
        "probe-reap-eof-deadlines-and-populated-zero-match-v1",
        "all-reaps-and-eof-complete-with-cgroup-populated-zero-v1",
        (
            "deadline-uninterruptible-or-incomplete-reap-fails-run-v1",
            "populated-leaf-extra-process-or-open-stream-fails-run-v1",
        ),
        "postrun-cgroup-quiescence-observed",
    ),
)


_STRUCTURAL_JOIN_SPECS: Final = (
    _spec(
        "inner-v1-receipt-digest-joined",
        "postrun-before-prospective-outer-receipt",
        "independent-host-receipt-validator-v1",
        "exact-inner-v1-preimage-ledger-and-run-join-validation-v1",
        (
            "inner-v1-receipt",
            "inner-v1-request",
            "inner-v1-implementation-closure",
            "linux-confinement-policy",
            "evidence-plan",
            "staging-protocol-contract",
            "evidence-schema-contract",
            "stage1-release-gate-preimage",
            "stage2-release-gate-preimage",
            "pre-completion-release-prefix",
            "native-supervisor-inner-v1-completion-record",
            "full-release-transcript",
        ),
        (
            "inner-v1-completion-record-canonical-bytes",
            "inner-v1-completion-record-byte-count",
            "inner-v1-completion-record-plain-sha256",
            "inner-v1-completion-record-sha256",
            "inner-v1-completion-record-artifact-type-record",
            "INNER_V1_COMPLETE-event-record",
            "INNER_V1_COMPLETE-event-evidence-digest-sha256",
            "staging-run-binding-sha256",
            "stage1-release-gate-preimage-canonical-bytes",
            "stage1-release-gate-preimage-byte-count",
            "stage1-release-gate-preimage-plain-sha256",
            "stage1-release-gate-preimage-sha256",
            "stage1-release-gate-event-evidence-digest-sha256",
            "stage2-release-gate-preimage-canonical-bytes",
            "stage2-release-gate-preimage-byte-count",
            "stage2-release-gate-preimage-plain-sha256",
            "stage2-release-gate-preimage-sha256",
            "stage2-release-gate-event-evidence-digest-sha256",
            "pre-completion-release-prefix-canonical-bytes",
            "pre-completion-release-prefix-byte-count",
            "pre-completion-release-prefix-plain-sha256",
            "pre-completion-release-prefix-sha256",
            "pre-completion-release-prefix-terminal-event-record",
            "full-release-transcript-canonical-bytes",
            "full-release-transcript-sha256",
            "inner-v1-receipt-canonical-bytes",
            "inner-v1-receipt-byte-count",
            "inner-v1-receipt-plain-sha256",
            "inner-v1-receipt-sha256",
            "inner-v1-receipt-artifact-type-record",
            "inner-v1-inherited-28-false-field-ledger",
            "acceptance-contract-sha256",
            "evidence-plan-sha256",
            "staging-protocol-contract-sha256",
            "evidence-schema-contract-sha256",
            "linux-confinement-policy-sha256",
            "linux-platform-profile-sha256",
            "inner-v1-run-input-sha256",
            "inner-v1-request-frame-sha256",
            "inner-v1-case-input-sha256",
            "inner-v1-implementation-closure-sha256",
            (
                "inner-v1-implementation-closure-validation-"
                "receipt-sha256"
            ),
            "inner-v1-closure-pipe-frame-sha256",
        ),
        (
            "exact-run-bound-native-completion-record-gates-release-"
            "prefix-inner-bytes-ledger-contracts-policy-request-and-"
            "closure-join-match-v1"
        ),
        (
            "exact-canonical-inner-v1-receipt-bytes-retained",
            "inner-v1-receipt-artifact-type-bound",
            "inner-v1-inherited-28-false-field-ledger-exact",
            "plan-staging-evidence-schema-and-policy-identities-bound",
            "inner-request-and-closure-preimages-and-identities-retained",
            "stage1-and-stage2-gate-preimages-recomputed-and-validated",
            (
                "pre-completion-release-prefix-through-stage2-"
                "released-recomputed-and-validated"
            ),
            (
                "native-supervisor-inner-completion-record-exact-"
                "preimage-retained"
            ),
            (
                "INNER_V1_COMPLETE-event-digest-equals-recomputed-"
                "completion-record-domain-digest"
            ),
            (
                "full-release-transcript-is-append-only-prefix-plus-"
                "completion-event-extension"
            ),
            "binding-dependency-graph-acyclic",
        ),
        "same-run-inner-receipt-preimage-and-join-known-answer-v1",
        (
            "unmodified-same-run-completion-record-gates-release-"
            "prefix-inner-bytes-ledger-contracts-request-and-closure-"
            "join-validate-v1"
        ),
        (
            "canonical-completion-record-event-digest-gates-release-"
            "prefix-inner-ledger-plan-staging-schema-policy-request-"
            "and-closure-all-match-v1"
        ),
        (
            "not-executed-or-missing-inner-preimage-is-not-pass-v1",
            (
                "caller-reconstructed-object-without-exact-retained-"
                "inner-bytes-is-not-pass-v1"
            ),
            (
                "noncanonical-truncated-extended-or-byte-count-mismatch-"
                "fails-join-v1"
            ),
            (
                "inner-plain-or-domain-sha256-mismatch-fails-join-v1"
            ),
            (
                "inner-artifact-type-or-28-false-ledger-mismatch-"
                "fails-join-v1"
            ),
            (
                "plan-staging-evidence-schema-or-policy-identity-"
                "mismatch-fails-join-v1"
            ),
            (
                "request-case-input-closure-validation-or-pipe-frame-"
                "cross-run-splice-fails-join-v1"
            ),
            (
                "run-binding-plan-staging-schema-policy-or-platform-"
                "two-run-splice-fails-join-v1"
            ),
            (
                "stage1-or-stage2-gate-preimage-or-event-digest-two-"
                "run-splice-fails-join-v1"
            ),
            (
                "pre-completion-release-prefix-two-run-splice-or-"
                "terminal-event-mismatch-fails-join-v1"
            ),
            (
                "inner-completion-record-two-run-field-mutation-or-"
                "event-digest-mismatch-fails-join-v1"
            ),
            (
                "full-release-transcript-not-exact-prefix-plus-"
                "completion-event-extension-fails-join-v1"
            ),
            (
                "full-release-transcript-digest-inside-completion-"
                "record-circularity-fails-schema-v1"
            ),
            "positive-control-failure-invalidates-join-v1",
        ),
        "inner-v1-receipt-digest-joined",
    ),
)


def _control_failures(*specific: str) -> Tuple[str, ...]:
    return (
        "not-executed-or-unsatisfied-prerequisite-is-not-pass-v1",
        "positive-control-failure-invalidates-control-v1",
    ) + tuple(specific)


_HOSTILE_CONTROL_SPECS: Final = (
    _spec(
        "abstract-and-filesystem-unix-socket-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "raw-unix-socket-connect-bind-send-control-v1",
        ("hostile-application", "host-owned-unix-socket-fixtures"),
        (
            "host-fixture-address-and-identity-record",
            "raw-socket-attempt-records",
            "server-accept-and-payload-records",
            "application-exit-and-signal-record",
        ),
        "all-abstract-and-filesystem-unix-socket-attempts-denied-v1",
        (
            "unix-socket-syscall-probe-supported",
            "host-fixtures-reachable-outside-sandbox",
        ),
        "same-binary-connects-to-both-host-unix-socket-fixtures-v1",
        "outside-run-server-accepts-and-matches-both-payloads-v1",
        "inside-run-attempts-denied-and-no-server-payload-observed-v1",
        _control_failures(
            "any-inside-connect-bind-send-or-server-payload-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "blocked-and-ignored-signal-teardown",
        "hostile-teardown",
        "privileged-supervisor-hostile-control-harness-v1",
        "ignored-sigterm-and-blocked-signal-teardown-control-v1",
        ("hostile-application", "sandbox-pid1-reaper"),
        (
            "signal-mask-and-handler-ready-record",
            "pidfd-signal-records",
            "teardown-deadline-records",
            "wait-reap-and-cgroup-events-records",
        ),
        "signal-resistant-application-is-boundedly-killed-and-reaped-v1",
        (
            "pidfd-signaling-supported",
            "hostile-handler-readiness-observed",
            "cgroup-kill-supported",
        ),
        "same-binary-survives-sigterm-until-sigkill-outside-sandbox-v1",
        "outside-run-ready-process-remains-live-after-sigterm-v1",
        "inside-run-escalates-reaps-and-reaches-populated-zero-v1",
        _control_failures(
            "surviving-task-missed-deadline-or-populated-leaf-"
            "fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "bpf-perf-keyring-and-io-uring-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "one-raw-syscall-probe-per-kernel-interface-v1",
        ("hostile-application", "linux-host-platform"),
        (
            "platform-feature-prerequisite-records",
            "raw-bpf-perf-keyring-io-uring-attempt-records",
            "per-probe-exit-signal-and-seccomp-records",
        ),
        "every-target-kernel-interface-attempt-is-policy-denied-v1",
        (
            "target-syscall-numbers-bound-to-architecture",
            "platform-feature-probes-completed",
            "host-test-harness-can-observe-each-attempt",
        ),
        "paired-host-probes-demonstrate-each-interface-dispatches-v1",
        "outside-probes-reach-interface-specific-kernel-validation-v1",
        "each-inside-raw-syscall-is-killed-or-exactly-policy-denied-v1",
        _control_failures(
            "enosys-without-platform-proof-is-not-pass-v1",
            "any-interface-operation-created-or-opened-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "capability-and-privilege-regain-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "credential-capability-setid-and-file-privilege-control-v1",
        ("hostile-application",),
        (
            "pre-attempt-credential-record",
            "capset-prctl-setid-and-file-exec-attempt-records",
            (
                "positive-control-same-binary-operation-argument-"
                "dispatch-records"
            ),
            "permissive-paired-credential-fixture-success-records",
            "post-attempt-credential-record",
            "per-probe-exit-and-signal-record",
        ),
        "no-attempt-acquires-id-capability-or-privilege-v1",
        (
            "zero-capability-precondition-observed",
            "no-new-privileges-precondition-observed",
            "test-target-identities-bound",
            "pinned-credential-regain-probe-binary-and-arguments-bound",
            "permissive-paired-userns-capability-fixture-available",
        ),
        (
            "same-pinned-binary-dispatches-identical-capset-prctl-setid-"
            "and-file-privilege-operations-in-permissive-fixture-v1"
        ),
        (
            "paired-fixture-observes-each-operation-specific-success-"
            "or-expected-credential-delta-v1"
        ),
        "all-inside-attempts-denied-and-credentials-remain-exact-v1",
        _control_failures(
            (
                "unsupported-intrinsically-denied-or-broken-positive-"
                "probe-is-not-executed-v1"
            ),
            "any-id-capability-or-privilege-delta-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "compat-x32-syscall-bypass-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "architecture-specific-compat-and-x32-dispatch-control-v1",
        ("hostile-application", "linux-host-platform"),
        (
            "architecture-and-abi-feature-record",
            "native-raw-syscall-control-record",
            "compat-and-x32-number-attempt-records",
            "per-probe-exit-and-signal-record",
        ),
        "no-compat-or-x32-path-bypasses-adapter-filter-v1",
        (
            "architecture-profile-bound",
            "raw-syscall-probe-binary-identity-bound",
            "native-control-syscall-dispatches",
        ),
        "same-probe-dispatches-approved-native-control-syscall-v1",
        "native-control-return-proves-raw-syscall-machinery-ran-v1",
        "all-applicable-compat-x32-attempts-are-killed-or-proven-absent-v1",
        _control_failures(
            "generic-enosys-without-architecture-proof-is-not-pass-v1",
            "any-forbidden-compat-operation-completes-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "cpu-exhaustion-containment",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "bounded-multithreaded-cpu-saturation-control-v1",
        ("hostile-application", "sandbox-cgroup-v2-leaf"),
        (
            "cpu-max-before-and-after-records",
            "cpu-stat-throttling-delta-record",
            "wall-clock-deadline-record",
            "teardown-and-cgroup-events-record",
        ),
        "cpu-load-is-throttled-deadline-bounded-and-quiescent-v1",
        (
            "cgroup-cpu-controller-enabled",
            "monotonic-clock-bound",
            "cpu-probe-ready-before-measurement",
        ),
        "same-probe-accumulates-measurable-cpu-time-outside-cgroup-v1",
        "outside-probe-crosses-minimum-cpu-work-threshold-v1",
        "inside-probe-shows-throttling-and-bounded-cleanup-v1",
        _control_failures(
            "no-load-no-throttling-or-missed-deadline-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "descriptor-secret-leak-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "seeded-canary-fd-scan-dup-and-read-control-v1",
        ("hostile-application", "supervisor-secret-canary-descriptors"),
        (
            "seeded-canary-digest-and-fd-role-record",
            "application-fd-probe-attempt-records",
            "application-output-canary-scan-record",
            "supervisor-peer-custody-record",
        ),
        "no-canary-fd-alias-byte-or-digest-reaches-application-output-v1",
        (
            "fresh-canary-generated",
            "canary-fds-open-in-supervisor",
            "full-admitted-fd-range-probed",
        ),
        "test-only-inherited-canary-fd-is-detected-by-same-probe-v1",
        "positive-run-reproduces-exact-canary-digest-v1",
        "confined-run-finds-no-canary-fd-alias-or-output-byte-v1",
        _control_failures(
            "any-canary-byte-digest-or-fd-alias-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "dns-ipv4-ipv6-packet-and-netlink-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "paired-network-family-connect-send-and-netlink-control-v1",
        ("hostile-application", "host-owned-network-fixtures"),
        (
            "host-network-fixture-address-record",
            "dns-ipv4-ipv6-packet-netlink-attempt-records",
            "server-packet-and-payload-records",
            "per-probe-exit-and-signal-record",
        ),
        "all-external-network-and-netlink-attempts-denied-v1",
        (
            "host-network-fixtures-reachable",
            "ipv4-and-ipv6-platform-support-probed",
            "netlink-family-support-probed",
        ),
        "same-probes-reach-paired-host-fixtures-outside-sandbox-v1",
        "outside-servers-observe-every-expected-probe-payload-v1",
        "inside-probes-denied-with-zero-host-payload-observations-v1",
        _control_failures(
            "absent-network-feature-without-proof-is-not-pass-v1",
            "any-packet-connection-or-netlink-success-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "exec-and-executable-mapping-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "post-filter-execveat-mmap-mprotect-and-memfd-control-v1",
        ("hostile-application", "in-rootfs-executable-probe"),
        (
            "target-executable-and-library-identity-record",
            "exec-and-executable-mapping-attempt-records",
            "per-attempt-exit-signal-and-seccomp-records",
            "target-side-effect-record",
        ),
        "every-post-stage2-exec-or-executable-mapping-path-denied-v1",
        (
            "adapter-seccomp-filter-observed",
            "probe-target-present-and-executable",
            "architecture-syscall-numbers-bound",
        ),
        "same-binary-executes-and-maps-probe-target-before-adapter-filter-v1",
        "positive-target-emits-bound-side-effect-v1",
        "inside-attempts-killed-or-denied-with-no-target-side-effect-v1",
        _control_failures(
            "any-exec-or-executable-mapping-completes-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "fork-clone-setsid-and-double-fork-containment",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "fork-clone-session-and-double-fork-control-v1",
        ("hostile-application", "sandbox-cgroup-v2-leaf"),
        (
            "fork-clone-setsid-attempt-records",
            "cgroup-process-inventory-timeline",
            "role-parentage-and-session-records",
            "teardown-reap-records",
        ),
        "no-descendant-or-session-escape-survives-control-v1",
        (
            "pids-controller-enabled",
            "application-and-pid1-membership-observed",
            "process-probe-binary-identity-bound",
        ),
        "same-probe-creates-and-reaps-double-fork-descendant-outside-v1",
        "outside-run-observes-ready-grandchild-and-session-change-v1",
        "inside-run-denies-or-contains-and-fully-reaps-every-attempt-v1",
        _control_failures(
            "untracked-descendant-session-or-incomplete-reap-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "host-home-workspace-and-authority-path-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "seeded-host-path-open-stat-read-and-traversal-control-v1",
        ("hostile-application", "host-protected-path-fixtures"),
        (
            "host-fixture-path-and-canary-digest-records",
            "inside-open-stat-readlink-and-traversal-attempt-records",
            "application-output-canary-scan-record",
        ),
        "all-protected-host-paths-absent-and-canaries-unreadable-v1",
        (
            "protected-host-fixtures-created",
            "fixture-custody-and-digests-bound",
            "path-probe-covers-each-forbidden-class",
        ),
        "same-probe-reads-each-fixture-from-host-namespace-v1",
        "outside-run-recovers-every-bound-canary-digest-v1",
        "inside-run-cannot-resolve-or-read-any-protected-fixture-v1",
        _control_failures(
            "any-host-path-metadata-or-canary-read-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "host-ipc-and-shared-memory-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "sysv-posix-shared-memory-and-host-ipc-control-v1",
        ("hostile-application", "host-ipc-fixtures"),
        (
            "host-ipc-fixture-identity-and-canary-records",
            "ipc-open-attach-create-and-read-attempt-records",
            "host-fixture-access-log",
            "application-output-canary-scan-record",
        ),
        "no-host-ipc-object-or-shared-memory-can-be-reached-v1",
        (
            "ipc-feature-prerequisites-probed",
            "host-ipc-fixtures-created",
            "fixture-identities-and-canaries-bound",
        ),
        "same-probe-attaches-to-and-reads-host-ipc-fixtures-outside-v1",
        "outside-run-recovers-bound-ipc-canaries-v1",
        "inside-run-denied-with-no-host-fixture-access-or-canary-v1",
        _control_failures(
            "feature-absence-without-prerequisite-proof-is-not-pass-v1",
            "any-host-ipc-access-or-canary-read-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "hostile-native-library-raw-syscall-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "pinned-native-library-direct-syscall-control-v1",
        ("hostile-application", "hostile-native-probe-library"),
        (
            "native-probe-source-binary-and-linkage-digests",
            "raw-syscall-attempt-records",
            "per-attempt-exit-signal-and-seccomp-records",
            "forbidden-operation-side-effect-records",
        ),
        "native-direct-syscalls-cannot-bypass-confinement-controls-v1",
        (
            "native-probe-closure-identity-bound",
            "raw-syscall-numbers-bound-to-architecture",
            "probe-loaded-before-adapter-filter",
        ),
        "same-library-completes-approved-control-syscall-v1",
        "approved-raw-syscall-return-proves-native-probe-executed-v1",
        "every-forbidden-raw-syscall-denied-with-no-side-effect-v1",
        _control_failures(
            "library-not-loaded-or-control-syscall-not-run-is-not-pass-v1",
            "any-forbidden-native-side-effect-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "memory-and-swap-exhaustion-containment",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "bounded-resident-memory-and-swap-pressure-control-v1",
        ("hostile-application", "sandbox-cgroup-v2-leaf"),
        (
            "memory-controller-values-record",
            "memory-current-peak-and-events-timeline",
            "swap-current-and-events-timeline",
            "oom-and-application-exit-record",
            "teardown-cgroup-events-record",
        ),
        "memory-pressure-is-limited-grouped-and-boundedly-quiescent-v1",
        (
            "memory-and-swap-controllers-enabled",
            "memory-probe-ready-before-pressure",
            "oom-group-setting-observed",
        ),
        "same-probe-allocates-and-touches-minimum-working-set-outside-v1",
        "outside-run-crosses-minimum-resident-memory-threshold-v1",
        "inside-run-hits-bound-with-expected-events-and-quiescence-v1",
        _control_failures(
            "no-pressure-bound-violation-or-populated-leaf-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "mount-pivot-setns-and-unshare-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "raw-mount-pivot-root-setns-and-unshare-control-v1",
        ("hostile-application",),
        (
            "namespace-and-root-identity-before-record",
            "mount-pivot-setns-unshare-attempt-records",
            (
                "positive-control-same-binary-operation-argument-"
                "dispatch-records"
            ),
            "permissive-paired-namespace-operation-success-records",
            "namespace-and-root-identity-after-record",
            "per-attempt-exit-signal-and-seccomp-records",
        ),
        "no-mount-or-namespace-retarget-operation-completes-v1",
        (
            "namespace-identities-observed",
            "pinned-mount-pivot-setns-unshare-probe-binary-bound",
            "target-namespace-fd-is-controlled",
            "permissive-paired-mount-userns-fixture-available",
            "identical-operation-and-argument-vector-bound",
        ),
        (
            "same-pinned-binary-dispatches-identical-mount-pivot-setns-"
            "and-unshare-operations-in-permissive-fixture-v1"
        ),
        (
            "paired-fixture-observes-each-operation-success-and-exact-"
            "root-or-namespace-delta-v1"
        ),
        "inside-attempts-denied-and-identities-remain-unchanged-v1",
        _control_failures(
            (
                "unsupported-intrinsically-denied-or-broken-positive-"
                "probe-is-not-executed-v1"
            ),
            "any-root-mount-or-namespace-identity-change-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "outer-monitor-exit-stall-escalation",
        "hostile-teardown",
        "privileged-supervisor-fault-injection-harness-v1",
        "bound-monitor-exit-stall-and-two-deadline-control-v1",
        ("bubblewrap-monitor", "privileged-supervisor"),
        (
            "test-only-stall-injection-identity-and-activation-record",
            "monitor-pidfd-identity-record",
            "first-and-second-deadline-records",
            "pidfd-sigkill-and-direct-wait-reap-records",
            "final-child-run-and-cleanup-status-record",
        ),
        "stalled-monitor-triggers-exact-failure-escalation-and-reap-v1",
        (
            "reviewed-test-only-stall-hook-selected",
            "monitor-pidfd-bound-before-activation",
            "monotonic-clock-bound",
        ),
        "same-hook-proves-monitor-remains-live-until-released-v1",
        "positive-run-observes-stall-ready-and-live-monitor-v1",
        "inside-run-fails-child-signals-exact-monitor-and-reaps-v1",
        _control_failures(
            "unstalled-hook-wrong-pidfd-or-missed-deadline-is-not-pass-v1",
            "monitor-not-directly-wait-reaped-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "output-exhaustion-containment",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "stdout-stderr-and-aggregate-output-flood-control-v1",
        ("hostile-application", "supervisor-stdio-peers"),
        (
            "output-ceiling-record",
            "stdout-stderr-byte-count-timeline",
            "aggregate-output-limit-event-record",
            "application-exit-and-teardown-record",
            "bounded-drain-and-eof-record",
        ),
        "output-flood-is-bounded-failed-drained-and-quiescent-v1",
        (
            "supervisor-concurrent-drainers-active",
            "output-ceilings-bound",
            "output-probe-ready-before-flood",
        ),
        "same-probe-emits-and-verifies-minimum-payload-outside-v1",
        "outside-run-receives-complete-bound-payload-digest-v1",
        "inside-run-hits-exact-limit-with-bounded-cleanup-and-eof-v1",
        _control_failures(
            "short-probe-unbounded-buffer-deadlock-or-open-stream-fails-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "pid-and-thread-exhaustion-containment",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "process-and-thread-creation-pressure-control-v1",
        ("hostile-application", "sandbox-cgroup-v2-leaf"),
        (
            "pids-max-and-events-before-record",
            "fork-clone-thread-attempt-timeline",
            "cgroup-process-and-thread-peak-record",
            "pids-events-delta-record",
            "teardown-and-quiescence-record",
        ),
        "pid-thread-pressure-cannot-exceed-bound-or-escape-cleanup-v1",
        (
            "pids-controller-enabled",
            "initial-two-role-membership-observed",
            "creation-probe-ready-before-pressure",
        ),
        "same-probe-creates-minimum-process-and-thread-count-outside-v1",
        "outside-run-crosses-minimum-creation-threshold-v1",
        "inside-run-denies-or-limits-creation-and-reaches-zero-v1",
        _control_failures(
            "no-pressure-limit-exceeded-or-surviving-task-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "proc-sys-cgroup-and-device-path-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "forbidden-kernel-filesystem-and-device-path-control-v1",
        ("hostile-application",),
        (
            "forbidden-path-class-attempt-records",
            "admitted-device-positive-control-records",
            (
                "positive-control-same-binary-operation-argument-"
                "dispatch-records"
            ),
            "permissive-host-namespace-forbidden-path-success-records",
            "mount-inventory-binding-record",
            "application-output-canary-scan-record",
        ),
        "forbidden-kernel-paths-absent-and-device-surface-exact-v1",
        (
            "host-forbidden-paths-exist-for-baseline",
            "private-device-projection-observed",
            "path-probe-covers-every-forbidden-class",
            "pinned-path-probe-binary-operation-and-arguments-bound",
            "permissive-host-namespace-paired-fixture-available",
        ),
        (
            "same-pinned-binary-dispatches-identical-proc-sys-cgroup-"
            "and-device-path-operations-in-permissive-host-fixture-v1"
        ),
        (
            "paired-fixture-observes-each-exact-open-stat-read-or-device-"
            "operation-success-with-bound-arguments-v1"
        ),
        "all-forbidden-path-opens-fail-and-no-canary-is-read-v1",
        _control_failures(
            (
                "unsupported-intrinsically-denied-or-broken-positive-"
                "probe-is-not-executed-v1"
            ),
            "any-forbidden-path-or-unlisted-device-open-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "ptrace-process-vm-and-pidfd-getfd-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "cross-process-introspection-and-fd-theft-control-v1",
        ("hostile-application", "host-owned-target-process"),
        (
            "target-process-pidfd-and-canary-record",
            "ptrace-process-vm-and-pidfd-getfd-attempt-records",
            "target-process-observation-log",
            "application-output-canary-scan-record",
        ),
        "all-cross-process-inspection-and-fd-theft-paths-denied-v1",
        (
            "target-process-ready-and-identity-bound",
            "target-exports-controlled-readable-canary",
            "platform-syscalls-probed",
        ),
        "privileged-host-probe-reads-controlled-target-canary-v1",
        "outside-control-recovers-bound-canary-through-each-supported-api-v1",
        "inside-probes-denied-with-no-target-event-or-canary-v1",
        _control_failures(
            "unsupported-api-without-feature-proof-is-not-pass-v1",
            "any-attach-read-or-fd-duplication-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "receipt-replay-and-cross-run-splice-denial",
        "postrun-independent-receipt-validation",
        "independent-host-receipt-validator-v1",
        "two-run-replay-and-every-binding-field-splice-control-v1",
        ("outer-receipt", "observation-transcript", "release-transcript"),
        (
            "two-complete-run-binding-records",
            "valid-receipt-positive-control-record",
            "per-field-splice-mutation-records",
            "validator-outcome-and-failure-code-records",
        ),
        "every-replay-and-cross-run-binding-splice-is-rejected-v1",
        (
            "two-distinct-complete-linux-runs-available",
            "independent-validator-identity-bound",
            "all-join-fields-covered-by-mutations",
        ),
        "each-unmodified-same-run-receipt-validates-v1",
        "both-original-receipts-pass-independent-validation-v1",
        "every-replay-or-single-field-cross-run-splice-is-rejected-v1",
        _control_failures(
            "missing-real-run-pair-or-validator-failure-is-not-pass-v1",
            "any-replay-splice-or-unlisted-positive-claim-accepted-fails-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "rootfs-and-runtime-write-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "rootfs-runtime-mutation-open-rename-link-and-truncate-control-v1",
        ("hostile-application", "runtime-rootfs"),
        (
            "rootfs-and-runtime-target-digest-records",
            "write-rename-link-truncate-attempt-records",
            "post-attempt-target-digest-records",
            "work-write-positive-control-record",
        ),
        "rootfs-runtime-remain-byte-identical-while-work-is-writable-v1",
        (
            "rootfs-identity-observed",
            "runtime-targets-present",
            "work-byte-and-inode-budget-available",
        ),
        "same-probe-writes-renames-and-unlinks-controlled-work-file-v1",
        "work-positive-control-completes-and-digest-changes-v1",
        "all-rootfs-runtime-attempts-denied-with-identical-digests-v1",
        _control_failures(
            "work-positive-control-failure-is-not-pass-v1",
            "any-rootfs-runtime-content-or-metadata-change-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "seccomp-landlock-and-namespace-retargeting-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "security-layer-weakening-replacement-and-retarget-control-v1",
        ("hostile-application",),
        (
            "pre-attempt-seccomp-landlock-namespace-record",
            "security-layer-mutation-attempt-records",
            (
                "positive-control-same-binary-operation-argument-"
                "dispatch-records"
            ),
            "permissive-paired-security-operation-success-records",
            "post-attempt-seccomp-landlock-namespace-record",
            "per-attempt-exit-signal-record",
        ),
        "no-security-layer-can-be-weakened-replaced-or-retargeted-v1",
        (
            "two-seccomp-filters-observed",
            "landlock-installation-observed",
            "namespace-identities-observed",
            "pinned-security-probe-binary-operation-and-arguments-bound",
            "permissive-paired-security-fixture-available",
        ),
        (
            "same-pinned-binary-dispatches-identical-seccomp-landlock-"
            "and-namespace-retarget-operations-in-permissive-fixture-v1"
        ),
        (
            "paired-fixture-observes-each-operation-specific-success-and-"
            "bound-security-state-delta-v1"
        ),
        "inside-attempts-denied-and-all-security-identities-stable-v1",
        _control_failures(
            (
                "unsupported-intrinsically-denied-or-broken-positive-"
                "probe-is-not-executed-v1"
            ),
            "unobservable-precondition-or-any-security-delta-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "temporary-write-byte-and-inode-exhaustion-containment",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "work-filesystem-byte-and-inode-pressure-control-v1",
        ("hostile-application", "work-write-surface"),
        (
            "work-budget-before-record",
            "write-byte-and-create-inode-attempt-timeline",
            "limit-event-and-failure-records",
            "work-budget-after-cleanup-record",
            "teardown-cgroup-events-record",
        ),
        "work-byte-and-inode-pressure-hits-bounds-and-cleans-up-v1",
        (
            "work-byte-limit-active",
            "work-inode-limit-active",
            "probe-created-in-empty-work-surface",
        ),
        "same-probe-writes-one-file-and-creates-one-inode-inside-v1",
        "small-work-positive-control-round-trips-exact-payload-v1",
        "pressure-hits-both-bounds-with-bounded-cleanup-and-zero-use-v1",
        _control_failures(
            "no-pressure-limit-overrun-or-residual-files-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "terminal-ioctl-and-tiocsti-denial",
        "post-stage2-hostile-application-running",
        "privileged-supervisor-hostile-control-harness-v1",
        "tty-open-allocation-ioctl-and-tiocsti-control-v1",
        ("hostile-application", "supervisor-stdio-peers"),
        (
            "stdio-isatty-and-kernel-object-records",
            "dev-ptmx-and-tty-open-attempt-records",
            "terminal-ioctl-and-tiocsti-attempt-records",
            (
                "positive-control-same-binary-operation-argument-"
                "dispatch-records"
            ),
            "permissive-paired-pty-exact-ioctl-success-records",
            "supervisor-input-canary-record",
        ),
        "no-tty-allocation-terminal-ioctl-or-input-injection-succeeds-v1",
        (
            "supervisor-stdio-nontty-pipes-observed",
            "host-pty-positive-fixture-available",
            "pinned-terminal-probe-binary-identity-bound",
            "exact-tty-open-ioctl-request-and-argument-vectors-bound",
        ),
        (
            "same-pinned-binary-dispatches-identical-tty-open-allocation-"
            "ioctl-and-tiocsti-operations-on-permissive-paired-pty-v1"
        ),
        (
            "paired-pty-observes-every-exact-ioctl-success-including-"
            "tiocsti-input-side-effect-v1"
        ),
        "inside-opens-and-ioctls-denied-with-no-input-injection-v1",
        _control_failures(
            (
                "unsupported-intrinsically-denied-or-broken-positive-"
                "probe-is-not-executed-v1"
            ),
            "any-tty-pty-ioctl-or-input-injection-success-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
    _spec(
        "termination-resistant-descendant-quiescence",
        "hostile-teardown",
        "privileged-supervisor-hostile-control-harness-v1",
        "session-escape-double-fork-signal-resistant-quiescence-control-v1",
        (
            "hostile-application",
            "sandbox-pid1-reaper",
            "adopted-run-descendants",
        ),
        (
            "descendant-ready-and-parentage-records",
            "session-and-signal-state-records",
            "targeted-and-emergency-signal-records",
            "adoption-wait-reap-inventory",
            "final-cgroup-events-and-process-inventory",
        ),
        "every-resistant-descendant-is-accounted-reaped-and-quiescent-v1",
        (
            "descendant-creation-path-demonstrated",
            "supervisor-subreaper-active",
            "cgroup-kill-and-pidfds-supported",
        ),
        "same-probe-creates-ready-signal-resistant-grandchild-outside-v1",
        "outside-run-observes-ready-grandchild-survive-term-grace-v1",
        "inside-run-boundedly-kills-reaps-and-reaches-populated-zero-v1",
        _control_failures(
            "probe-created-no-descendant-is-not-pass-v1",
            "missing-role-surviving-task-or-populated-leaf-fails-control-v1",
        ),
        "hostile-control-inventory-passed",
    ),
)


def _validate_fixed_specs() -> None:
    groups = (
        (
            _OBSERVATION_SPECS,
            LINUX_CONFINEMENT_REQUIRED_OBSERVATION_IDS,
        ),
        (
            _HOSTILE_CONTROL_SPECS,
            LINUX_CONFINEMENT_REQUIRED_HOSTILE_CONTROL_IDS,
        ),
        (
            _STRUCTURAL_JOIN_SPECS,
            ("inner-v1-receipt-digest-joined",),
        ),
    )
    tuple_fields = (
        "subject_role_ids",
        "raw_evidence_field_ids",
        "prerequisite_ids",
        "failure_oracle_ids",
    )
    scalar_fields = (
        "item_id",
        "lifecycle_stage_id",
        "trusted_producer_id",
        "procedure_id",
        "predicate_id",
        "positive_control_id",
        "positive_control_oracle_id",
        "success_oracle_id",
        "receipt_leaf_id",
    )
    for specs, expected_ids in groups:
        if tuple(spec.item_id for spec in specs) != expected_ids:
            raise RuntimeError(
                "evidence plan identifiers differ from acceptance contract"
            )
        if len({spec.item_id for spec in specs}) != len(specs):
            raise RuntimeError("evidence plan identifiers are not unique")
        for spec in specs:
            if any(
                type(getattr(spec, name)) is not str
                or not getattr(spec, name)
                for name in scalar_fields
            ):
                raise RuntimeError("evidence plan scalar is invalid")
            if any(
                type(getattr(spec, name)) is not tuple
                or not getattr(spec, name)
                or any(
                    type(value) is not str or not value
                    for value in getattr(spec, name)
                )
                or len(set(getattr(spec, name)))
                != len(getattr(spec, name))
                for name in tuple_fields
            ):
                raise RuntimeError("evidence plan tuple is invalid")
            if (
                spec.receipt_leaf_id
                not in LINUX_CONFINEMENT_PERMITTED_OUTER_POSITIVE_CLAIM_IDS
            ):
                raise RuntimeError("evidence plan receipt leaf is invalid")
            if (
                type(spec.execution_required) is not bool
                or spec.execution_required is not True
                or type(spec.not_executed_counts_as_pass) is not bool
                or spec.not_executed_counts_as_pass is not False
            ):
                raise RuntimeError("evidence plan execution rule is invalid")
    all_specs = (
        _OBSERVATION_SPECS
        + _HOSTILE_CONTROL_SPECS
        + _STRUCTURAL_JOIN_SPECS
    )
    if len({spec.item_id for spec in all_specs}) != len(all_specs):
        raise RuntimeError("evidence plan identifiers are not globally unique")
    receipt_leaf_ids = tuple(
        spec.receipt_leaf_id for spec in all_specs
    )
    if set(receipt_leaf_ids) != set(
        LINUX_CONFINEMENT_PERMITTED_OUTER_POSITIVE_CLAIM_IDS
    ):
        raise RuntimeError(
            "evidence plan does not cover every permitted receipt leaf"
        )
    if receipt_leaf_ids.count("inner-v1-receipt-digest-joined") != 1:
        raise RuntimeError(
            "inner receipt structural join leaf is not present exactly once"
        )
    if tuple(spec.gate_id for spec in _RELEASE_GATE_SPECS) != (
        "stage1-required-observation-gate",
        "stage2-required-observation-gate",
    ) or tuple(spec.staging_event_id for spec in _RELEASE_GATE_SPECS) != (
        "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED",
        "STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED",
    ):
        raise RuntimeError("release gate inventory is invalid")
    gate_scalar_fields = (
        "gate_id",
        "lifecycle_stage_id",
        "staging_event_id",
        "preimage_artifact_type",
        "preimage_digest_domain",
        "canonical_preimage_encoding_id",
        "prior_staging_event_record_digest_ordering_id",
        "predicate_id",
        "success_oracle_id",
    )
    gate_tuple_fields = (
        "canonical_preimage_field_ids",
        "capture_time_run_binding_field_ids",
        "required_observation_ids",
        "required_prior_staging_event_ids",
        "failure_oracle_ids",
    )
    for spec in _RELEASE_GATE_SPECS:
        if any(
            type(getattr(spec, name)) is not str
            or not getattr(spec, name)
            for name in gate_scalar_fields
        ) or any(
            type(getattr(spec, name)) is not tuple
            or not getattr(spec, name)
            or any(
                type(value) is not str or not value
                for value in getattr(spec, name)
            )
            or len(set(getattr(spec, name)))
            != len(getattr(spec, name))
            for name in gate_tuple_fields
        ):
            raise RuntimeError("release gate spec is invalid")
        if (
            spec.preimage_digest_domain != spec.preimage_artifact_type
            or spec.prior_staging_event_record_digest_ordering_id
            != _RELEASE_GATE_PRIOR_EVENT_RECORD_DIGEST_ORDERING_ID
            or spec.capture_time_run_binding_field_ids
            != _CAPTURE_TIME_RUN_BINDING_FIELD_IDS
            or not set(spec.capture_time_run_binding_field_ids).issubset(
                spec.canonical_preimage_field_ids
            )
            or type(spec.execution_required) is not bool
            or spec.execution_required is not True
            or type(spec.not_executed_counts_as_pass) is not bool
            or spec.not_executed_counts_as_pass is not False
        ):
            raise RuntimeError("release gate semantics are invalid")
        partial_order_edges = (
            spec.prior_staging_event_partial_order_edges
        )
        required_event_index = {
            event_id: index
            for index, event_id in enumerate(
                spec.required_prior_staging_event_ids
            )
        }
        if (
            type(partial_order_edges) is not tuple
            or not partial_order_edges
            or len(set(partial_order_edges)) != len(partial_order_edges)
            or any(
                type(edge) is not tuple
                or len(edge) != 2
                or any(
                    type(event_id) is not str or not event_id
                    for event_id in edge
                )
                or edge[0] not in required_event_index
                or edge[1] not in required_event_index
                or required_event_index[edge[0]]
                >= required_event_index[edge[1]]
                for edge in partial_order_edges
            )
        ):
            raise RuntimeError(
                "release gate prior-event partial order is invalid"
            )
    stage1_gate, stage2_gate = _RELEASE_GATE_SPECS
    if (
        stage1_gate.preimage_artifact_type
        != LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
        or stage1_gate.canonical_preimage_field_ids
        != _RELEASE_GATE_COMMON_PREIMAGE_FIELD_IDS
        or stage1_gate.required_observation_ids
        != _STAGE1_REQUIRED_OBSERVATION_IDS
        or stage1_gate.required_prior_staging_event_ids
        != _STAGE1_REQUIRED_PRIOR_STAGING_EVENT_IDS
        or stage1_gate.prior_staging_event_partial_order_edges
        != _STAGE1_PRIOR_STAGING_EVENT_PARTIAL_ORDER_EDGES
        or stage2_gate.preimage_artifact_type
        != LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE
        or stage2_gate.canonical_preimage_field_ids
        != (
            _RELEASE_GATE_COMMON_PREIMAGE_FIELD_IDS
            + _STAGE2_RELEASE_GATE_ADDITIONAL_PREIMAGE_FIELD_IDS
        )
        or stage2_gate.required_observation_ids
        != _STAGE2_REQUIRED_OBSERVATION_IDS
        or stage2_gate.required_prior_staging_event_ids
        != _STAGE2_REQUIRED_PRIOR_STAGING_EVENT_IDS
        or stage2_gate.prior_staging_event_partial_order_edges
        != _STAGE2_PRIOR_STAGING_EVENT_PARTIAL_ORDER_EDGES
    ):
        raise RuntimeError("release gate preimage contract is invalid")
    observation_partitions = (
        _STAGE1_REQUIRED_OBSERVATION_IDS,
        _STAGE2_REQUIRED_OBSERVATION_IDS,
        _POSTRUN_FINALIZED_OBSERVATION_IDS,
    )
    flattened_observation_ids = tuple(
        item_id
        for partition in observation_partitions
        for item_id in partition
    )
    if (
        len(flattened_observation_ids)
        != len(set(flattened_observation_ids))
        or tuple(
            len(partition) for partition in observation_partitions
        )
        != (10, 11, 3)
        or set(flattened_observation_ids)
        != set(LINUX_CONFINEMENT_REQUIRED_OBSERVATION_IDS)
        or any(
            tuple(
                item_id
                for item_id in (
                    LINUX_CONFINEMENT_REQUIRED_OBSERVATION_IDS
                )
                if item_id in set(partition)
            )
            != partition
            for partition in observation_partitions
        )
    ):
        raise RuntimeError("release gate observation coverage is invalid")
    observation_lifecycle_by_id = {
        spec.item_id: spec.lifecycle_stage_id
        for spec in _OBSERVATION_SPECS
    }
    if (
        observation_lifecycle_by_id[
            "backend-static-sealed-executable-identity-matched"
        ]
        != "pre-backend-exec"
        or "backend-static-sealed-executable-identity-matched"
        not in _STAGE1_REQUIRED_OBSERVATION_IDS
        or "backend-static-sealed-executable-identity-matched"
        in _STAGE2_REQUIRED_OBSERVATION_IDS
        or {
            observation_lifecycle_by_id[item_id]
            for item_id in _STAGE2_REQUIRED_OBSERVATION_IDS
        }
        != {"pre-stage2-application-stopped"}
    ):
        raise RuntimeError("release gate lifecycle timing is invalid")
    if (
        any(
            field_id.startswith("inner-v1-")
            for field_id in _CAPTURE_TIME_RUN_BINDING_FIELD_IDS
        )
        or _POSTRUN_LEAF_FINALIZATION_BINDING_FIELD_IDS[
            : len(_CAPTURE_TIME_RUN_BINDING_FIELD_IDS)
        ]
        != _CAPTURE_TIME_RUN_BINDING_FIELD_IDS
        or not any(
            field_id.startswith("inner-v1-")
            for field_id in (
                _POSTRUN_LEAF_FINALIZATION_BINDING_FIELD_IDS
            )
        )
    ):
        raise RuntimeError("capture and postrun binding split is invalid")
    process_observation = next(
        spec
        for spec in _OBSERVATION_SPECS
        if spec.item_id
        == (
            "pidfd-bound-observer-helper-monitor-init-application-"
            "identities-subreaper-adoption-and-reap-observed"
        )
    )
    all_subject_roles = tuple(
        role
        for spec in all_specs
        for role in spec.subject_role_ids
    )
    required_setup_child_raw_evidence_fields = {
        "bubblewrap-setup-child-pidfd-acquisition-record",
        "bubblewrap-setup-child-parentage-record",
        "bubblewrap-setup-child-lifetime-record",
        (
            "bubblewrap-setup-child-to-sandbox-pid1-same-host-"
            "pid-lifecycle-transition-record"
        ),
        "bubblewrap-setup-child-exit-adoption-and-reap-record",
    }
    if (
        "setup-child" in all_subject_roles
        or "bubblewrap-setup-child"
        not in process_observation.subject_role_ids
        or "sandbox-pid1-reaper"
        not in process_observation.subject_role_ids
        or not required_setup_child_raw_evidence_fields.issubset(
            process_observation.raw_evidence_field_ids
        )
        or "bubblewrap-setup-child-pidfd-bound"
        not in process_observation.prerequisite_ids
        or (
            "bubblewrap-setup-child-to-sandbox-pid1-same-host-pid-"
            "lifecycle-transition-bound"
        )
        not in process_observation.prerequisite_ids
        or (
            "missing-or-mismatched-setup-child-pidfd-parentage-"
            "lifetime-pid1-alias-exit-or-reap-evidence-fails-run-v1"
        )
        not in process_observation.failure_oracle_ids
    ):
        raise RuntimeError("setup child process role closure is invalid")
    completion_fields = set(
        _INNER_V1_COMPLETION_RECORD_PREIMAGE_FIELD_IDS
    )
    required_completion_fields = {
        "staging-run-binding-sha256",
        "stage1-release-gate-preimage-sha256",
        "stage2-release-gate-preimage-sha256",
        "pre-completion-release-prefix-canonical-bytes",
        "pre-completion-release-prefix-terminal-event-id",
        "inner-v1-receipt-canonical-bytes",
        "inner-v1-receipt-byte-count",
        "inner-v1-receipt-plain-sha256",
        "inner-v1-receipt-sha256",
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
    }
    if (
        len(completion_fields)
        != len(_INNER_V1_COMPLETION_RECORD_PREIMAGE_FIELD_IDS)
        or not required_completion_fields.issubset(completion_fields)
        or "full-release-transcript-sha256" in completion_fields
        or "inner-v1-completion-record-sha256" in completion_fields
        or "INNER_V1_COMPLETE-event-record" in completion_fields
    ):
        raise RuntimeError("inner completion preimage schema is invalid")
    topological_index = {
        node: index
        for index, node in enumerate(
            _BINDING_DEPENDENCY_TOPOLOGICAL_ORDER
        )
    }
    if (
        len(topological_index)
        != len(_BINDING_DEPENDENCY_TOPOLOGICAL_ORDER)
        or any(
            dependency not in topological_index
            or consumer not in topological_index
            or topological_index[dependency]
            >= topological_index[consumer]
            for dependency, consumer in _BINDING_DEPENDENCY_EDGES
        )
    ):
        raise RuntimeError("binding dependency graph is cyclic or invalid")


_validate_fixed_specs()


def _spec_tree(spec: _EvidenceSpec) -> dict:
    return {
        "execution_required": spec.execution_required,
        "execution_status_id": (
            LINUX_CONFINEMENT_EVIDENCE_PLAN_EXECUTION_STATUS
        ),
        "failure_oracle_ids": list(spec.failure_oracle_ids),
        "item_id": spec.item_id,
        "lifecycle_stage_id": spec.lifecycle_stage_id,
        "not_executed_counts_as_pass": (
            spec.not_executed_counts_as_pass
        ),
        "passed": False,
        "positive_control_id": spec.positive_control_id,
        "positive_control_oracle_id": (
            spec.positive_control_oracle_id
        ),
        "predicate_id": spec.predicate_id,
        "prerequisite_ids": list(spec.prerequisite_ids),
        "procedure_id": spec.procedure_id,
        "raw_evidence_field_ids": list(spec.raw_evidence_field_ids),
        "receipt_leaf_id": spec.receipt_leaf_id,
        "subject_role_ids": list(spec.subject_role_ids),
        "success_oracle_id": spec.success_oracle_id,
        "trusted_producer_id": spec.trusted_producer_id,
    }


def _release_gate_spec_tree(spec: _ReleaseGateSpec) -> dict:
    return {
        "canonical_preimage_constructed": False,
        "canonical_preimage_encoding_id": (
            spec.canonical_preimage_encoding_id
        ),
        "canonical_preimage_field_ids": list(
            spec.canonical_preimage_field_ids
        ),
        "canonical_preimage_validated": False,
        "capture_time_run_binding_field_ids": list(
            spec.capture_time_run_binding_field_ids
        ),
        "execution_required": spec.execution_required,
        "execution_status_id": (
            LINUX_CONFINEMENT_EVIDENCE_PLAN_EXECUTION_STATUS
        ),
        "failure_oracle_ids": list(spec.failure_oracle_ids),
        "gate_id": spec.gate_id,
        "lifecycle_stage_id": spec.lifecycle_stage_id,
        "not_executed_counts_as_pass": (
            spec.not_executed_counts_as_pass
        ),
        "passed": False,
        "predicate_id": spec.predicate_id,
        "preimage_artifact_type": spec.preimage_artifact_type,
        "preimage_digest_computation_id": (
            _DOMAIN_DIGEST_COMPUTATION_ID
        ),
        "preimage_digest_domain": spec.preimage_digest_domain,
        "prior_staging_event_partial_order_edges": [
            [dependency, consumer]
            for dependency, consumer in (
                spec.prior_staging_event_partial_order_edges
            )
        ],
        "prior_staging_event_record_digest_ordering_id": (
            spec.prior_staging_event_record_digest_ordering_id
        ),
        "required_observation_ids": list(
            spec.required_observation_ids
        ),
        "required_prior_staging_event_ids": list(
            spec.required_prior_staging_event_ids
        ),
        "staging_event_id": spec.staging_event_id,
        "staging_event_recorded": False,
        "success_oracle_id": spec.success_oracle_id,
    }


def _inner_v1_completion_record_schema_tree() -> dict:
    return {
        "artifact_type": (
            LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE
        ),
        "binding_dependency_edges": [
            [dependency, consumer]
            for dependency, consumer in _BINDING_DEPENDENCY_EDGES
        ],
        "binding_dependency_topological_order": list(
            _BINDING_DEPENDENCY_TOPOLOGICAL_ORDER
        ),
        "canonical_preimage_constructed": False,
        "canonical_preimage_custody_validated": False,
        "canonical_preimage_encoding_id": _CANONICAL_PREIMAGE_ENCODING_ID,
        "canonical_preimage_field_ids": list(
            _INNER_V1_COMPLETION_RECORD_PREIMAGE_FIELD_IDS
        ),
        "canonical_preimage_validated": False,
        "digest_computation_id": _DOMAIN_DIGEST_COMPUTATION_ID,
        "digest_domain": (
            LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_DIGEST_DOMAIN
        ),
        "digest_recomputed": False,
        "digest_transport_event_id": "INNER_V1_COMPLETE",
        "digest_transport_event_payload_field_id": (
            "evidence_digest_sha256"
        ),
        "digest_transport_semantics_id": (
            _INNER_V1_COMPLETE_DIGEST_SEMANTICS_ID
        ),
        "execution_required": True,
        "execution_status_id": (
            LINUX_CONFINEMENT_EVIDENCE_PLAN_EXECUTION_STATUS
        ),
        "format_version": "1",
        "full_release_transcript_digest_admitted_to_preimage": False,
        "inner_v1_complete_event_recorded": False,
        "not_executed_counts_as_pass": False,
        "passed": False,
        "pre_completion_release_prefix_artifact_type": (
            LINUX_CONFINEMENT_PRE_COMPLETION_RELEASE_PREFIX_ARTIFACT_TYPE
        ),
        "pre_completion_release_prefix_terminal_event_id": (
            "STAGE2_RELEASED"
        ),
        "record_id": "native-supervisor-inner-v1-completion-record",
        "staging_reducer_validates_digest_preimage": False,
        "staging_reducer_validates_preimage_custody": False,
    }


def _plan_tree() -> dict:
    return {
        "acceptance_contract_sha256": (
            linux_confinement_acceptance_contract_sha256()
        ),
        "artifact_type": LINUX_CONFINEMENT_EVIDENCE_PLAN_ARTIFACT_TYPE,
        "execution_state": {
            "all_hostile_controls_passed": False,
            "all_observations_passed": False,
            "all_release_gates_passed": False,
            "all_structural_joins_passed": False,
            "any_hostile_control_executed": False,
            "any_linux_observation_executed": False,
            "any_release_gate_executed": False,
            "any_structural_join_executed": False,
            "hostile_control_execution_status_id": (
                LINUX_CONFINEMENT_EVIDENCE_PLAN_EXECUTION_STATUS
            ),
            "inner_v1_complete_event_recorded": False,
            "inner_v1_completion_record_constructed": False,
            "inner_v1_completion_record_execution_status_id": (
                LINUX_CONFINEMENT_EVIDENCE_PLAN_EXECUTION_STATUS
            ),
            "inner_v1_completion_record_validated": False,
            "linux_execution_performed": False,
            "observation_execution_status_id": (
                LINUX_CONFINEMENT_EVIDENCE_PLAN_EXECUTION_STATUS
            ),
            "positive_receipt_generation_authorized": False,
            "release_gate_execution_status_id": (
                LINUX_CONFINEMENT_EVIDENCE_PLAN_EXECUTION_STATUS
            ),
            "structural_join_execution_status_id": (
                LINUX_CONFINEMENT_EVIDENCE_PLAN_EXECUTION_STATUS
            ),
        },
        "fixed_counts": {
            "hostile_control_count": len(_HOSTILE_CONTROL_SPECS),
            "observation_count": len(_OBSERVATION_SPECS),
            "release_gate_spec_count": len(_RELEASE_GATE_SPECS),
            "structural_join_spec_count": len(_STRUCTURAL_JOIN_SPECS),
        },
        "format_version": "1",
        "hostile_control_specs": [
            _spec_tree(spec) for spec in _HOSTILE_CONTROL_SPECS
        ],
        "inherited_inner_false_claim_state": {
            item_id: False
            for item_id in (
                LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS
            )
        },
        "mandatory_nonclaim_ids": list(
            LINUX_CONFINEMENT_MANDATORY_NONCLAIM_IDS
        ),
        "outer_positive_claim_state": {
            item_id: False
            for item_id in (
                LINUX_CONFINEMENT_PERMITTED_OUTER_POSITIVE_CLAIM_IDS
            )
        },
        "plan_rules": {
            "all_acceptance_ids_exactly_once_required": True,
            "all_permitted_receipt_leaves_covered": True,
            (
                "bubblewrap_child_pid_status_is_stage1_barrier_proof"
            ): False,
            "capture_time_binding_contains_postrun_inner_identity": False,
            "capture_time_release_gate_binding_required": True,
            "completion_record_contains_full_release_transcript_digest": (
                False
            ),
            "darwin_execution_evidence_admitted": False,
            "full_release_transcript_is_append_only_prefix_extension": True,
            "hostile_control_exact_oracle_required": True,
            "hostile_control_positive_control_required": True,
            "inner_v1_completion_preimage_validation_performed": False,
            (
                "inner_v1_complete_event_digest_is_completion_record_"
                "reference"
            ): True,
            "inventory_entry_is_execution_evidence": False,
            (
                "inner_v1_receipt_digest_join_leaf_exactly_once_required"
            ): True,
            "not_executed_is_pass": False,
            (
                "unmatched_or_intrinsically_denied_positive_control_"
                "is_pass"
            ): False,
            (
                "unsupported_intrinsically_denied_or_broken_positive_"
                "control_status_id"
            ): LINUX_CONFINEMENT_EVIDENCE_PLAN_EXECUTION_STATUS,
            "pre_release_stdout_drained_event_required": True,
            (
                "pidfd_bound_exact_stage1_barrier_read_block_"
                "observation_required"
            ): True,
            "predicate_recomputation_from_raw_evidence_required": True,
            "raw_evidence_retention_required": True,
            "release_gate_inventory_is_execution_evidence": False,
            "release_gate_preimage_validation_performed": False,
            "same_frozen_policy_platform_required": True,
            "postrun_leaf_finalization_binding_is_append_only": True,
            "postrun_leaf_finalization_binding_required": True,
            "structural_join_exact_inner_raw_bytes_required": True,
            "structural_join_is_execution_evidence": False,
            "synthetic_evidence_is_execution_evidence": False,
            "unsupported_prerequisite_is_pass": False,
        },
        "capture_time_run_binding_field_ids": list(
            _CAPTURE_TIME_RUN_BINDING_FIELD_IDS
        ),
        "inner_v1_completion_record_schema": (
            _inner_v1_completion_record_schema_tree()
        ),
        "observation_specs": [
            _spec_tree(spec) for spec in _OBSERVATION_SPECS
        ],
        "postrun_finalized_observation_ids": list(
            _POSTRUN_FINALIZED_OBSERVATION_IDS
        ),
        "postrun_leaf_finalization_binding_field_ids": list(
            _POSTRUN_LEAF_FINALIZATION_BINDING_FIELD_IDS
        ),
        "release_gate_specs": [
            _release_gate_spec_tree(spec) for spec in _RELEASE_GATE_SPECS
        ],
        "status_id": LINUX_CONFINEMENT_EVIDENCE_PLAN_STATUS,
        "structural_join_specs": [
            _spec_tree(spec) for spec in _STRUCTURAL_JOIN_SPECS
        ],
    }


def linux_confinement_evidence_plan_tree() -> dict:
    """Return a fresh exact projection of the prospective evidence plan."""

    return _plan_tree()


def linux_confinement_evidence_plan_bytes() -> bytes:
    """Return the fixed plan as bounded canonical ASCII JSON."""

    try:
        result = json.dumps(
            _plan_tree(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii", "strict")
    except (TypeError, ValueError, UnicodeError):
        raise RuntimeError(
            "Linux confinement evidence plan is not encodable"
        ) from None
    if (
        not result
        or len(result) > MAXIMUM_LINUX_CONFINEMENT_EVIDENCE_PLAN_BYTES
    ):
        raise RuntimeError(
            "Linux confinement evidence plan exceeds its byte ceiling"
        )
    return result


class _DuplicateKeyError(ValueError):
    pass


def _object_without_duplicates(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError("non-finite JSON constant")


def _same_exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        if set(left.keys()) != set(right.keys()):
            return False
        return all(
            _same_exact(left[key], right[key])
            for key in right
        )
    if type(left) is list:
        return (
            len(left) == len(right)
            and all(
                _same_exact(left_value, right_value)
                for left_value, right_value in zip(left, right)
            )
        )
    return left == right


def parse_linux_confinement_evidence_plan(value: bytes) -> dict:
    """Strictly parse the one fixed canonical evidence-plan artifact."""

    if type(value) is not bytes:
        _fail(LinuxConfinementEvidencePlanCode.INPUT_TYPE)
    if (
        not value
        or len(value) > MAXIMUM_LINUX_CONFINEMENT_EVIDENCE_PLAN_BYTES
    ):
        _fail(LinuxConfinementEvidencePlanCode.INPUT_RESOURCE)
    try:
        text = value.decode("ascii", "strict")
        decoded = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_json_constant,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _fail(LinuxConfinementEvidencePlanCode.JSON_INVALID)
    expected = _plan_tree()
    if not _same_exact(decoded, expected):
        _fail(LinuxConfinementEvidencePlanCode.SCHEMA_INVALID)
    canonical = linux_confinement_evidence_plan_bytes()
    if value != canonical:
        _fail(LinuxConfinementEvidencePlanCode.CANONICAL_MISMATCH)
    return expected


def linux_confinement_evidence_plan_plain_sha256() -> str:
    """Return the ordinary SHA-256 of the fixed canonical plan bytes."""

    return hashlib.sha256(
        linux_confinement_evidence_plan_bytes()
    ).hexdigest()


def linux_confinement_evidence_plan_sha256() -> str:
    """Return the length-bound domain SHA-256 of the fixed plan."""

    payload = linux_confinement_evidence_plan_bytes()
    digest = hashlib.sha256()
    digest.update(
        LINUX_CONFINEMENT_EVIDENCE_PLAN_DIGEST_DOMAIN.encode("ascii")
    )
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


__all__ = [
    "LINUX_CONFINEMENT_EVIDENCE_PLAN_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_EVIDENCE_PLAN_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_EVIDENCE_PLAN_EXECUTION_STATUS",
    "LINUX_CONFINEMENT_EVIDENCE_PLAN_STATUS",
    "LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_INNER_V1_COMPLETION_RECORD_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_PRE_COMPLETION_RELEASE_PREFIX_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_STAGE1_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_STAGE2_RELEASE_GATE_PREIMAGE_ARTIFACT_TYPE",
    "MAXIMUM_LINUX_CONFINEMENT_EVIDENCE_PLAN_BYTES",
    "LinuxConfinementEvidencePlanCode",
    "LinuxConfinementEvidencePlanError",
    "linux_confinement_evidence_plan_bytes",
    "linux_confinement_evidence_plan_plain_sha256",
    "linux_confinement_evidence_plan_sha256",
    "linux_confinement_evidence_plan_tree",
    "parse_linux_confinement_evidence_plan",
]
