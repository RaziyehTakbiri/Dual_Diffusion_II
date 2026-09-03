"""Prospective acceptance contract for Linux adapter-child confinement.

This module freezes the observations and hostile controls that a future
Linux supervisor must satisfy before this repository may describe one run as
``linux-confined-development``.  It is deliberately write-free and has no
process-launching surface.  Constructing or hashing this contract is not
execution evidence, and Bubblewrap configuration alone cannot satisfy it.

The contract is stricter than a namespace-launch command.  It requires
pre-adapter, supervisor-side observations of the selected Linux process,
resource ownership through cgroup v2, adversarial tests of each named
boundary, and post-run process-tree quiescence.  It does not request or
authorize publication, a decision, semantic claims, expected-material
nonexposure, or information-flow noninterference.
"""

from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import Final


LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-acceptance-contract.v1"
)
LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_STATUS: Final = (
    "PROSPECTIVE_UNEXECUTED"
)
LINUX_CONFINEMENT_ACCEPTANCE_TARGET_STATUS: Final = (
    "LINUX_CONFINED_DEVELOPMENT"
)
MAXIMUM_LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_BYTES: Final = 64 * 1024


LINUX_CONFINEMENT_REQUIRED_OBSERVATION_IDS: Final = (
    "application-argv-environment-cwd-umask-matched",
    "backend-static-sealed-executable-identity-matched",
    "capability-securebits-dumpability-profile-matched",
    "cgroup-v2-controller-values-matched-before-release",
    "cgroup-v2-leaf-owned-by-supervisor",
    "dependency-lock-identity-matched",
    (
        "descriptor-inventory-and-stdio-types-closed-before-"
        "adapter-import"
    ),
    (
        "exact-two-level-uid-gid-maps-composition-empty-"
        "supplementary-groups-and-setgroups-denial-matched"
    ),
    "immutable-runtime-rootfs-identity-matched",
    "landlock-abi-and-ruleset-matched",
    "linux-platform-profile-matched",
    "mount-inventory-and-write-surface-matched",
    "namespace-identities-distinct-before-release",
    "network-interface-and-route-inventory-matched",
    "no-new-privileges-observed-before-release",
    (
        "nonce-generation-nonreuse-and-readiness-release-"
        "transcript-matched"
    ),
    (
        "pidfd-bound-observer-helper-monitor-init-application-"
        "identities-subreaper-adoption-and-reap-observed"
    ),
    "rlimit-profile-matched-before-release",
    "sandbox-bootstrap-identity-matched",
    "sandbox-interpreter-identity-matched",
    "seccomp-filter-and-architecture-observed-before-release",
    "supervisor-dependency-closure-identity-matched",
    "supervisor-executable-identity-matched",
    "teardown-cgroup-populated-zero-observed",
)


LINUX_CONFINEMENT_REQUIRED_HOSTILE_CONTROL_IDS: Final = (
    "abstract-and-filesystem-unix-socket-denial",
    "blocked-and-ignored-signal-teardown",
    "bpf-perf-keyring-and-io-uring-denial",
    "capability-and-privilege-regain-denial",
    "compat-x32-syscall-bypass-denial",
    "cpu-exhaustion-containment",
    "descriptor-secret-leak-denial",
    "dns-ipv4-ipv6-packet-and-netlink-denial",
    "exec-and-executable-mapping-denial",
    "fork-clone-setsid-and-double-fork-containment",
    "host-home-workspace-and-authority-path-denial",
    "host-ipc-and-shared-memory-denial",
    "hostile-native-library-raw-syscall-denial",
    "memory-and-swap-exhaustion-containment",
    "mount-pivot-setns-and-unshare-denial",
    "outer-monitor-exit-stall-escalation",
    "output-exhaustion-containment",
    "pid-and-thread-exhaustion-containment",
    "proc-sys-cgroup-and-device-path-denial",
    "ptrace-process-vm-and-pidfd-getfd-denial",
    "receipt-replay-and-cross-run-splice-denial",
    "rootfs-and-runtime-write-denial",
    "seccomp-landlock-and-namespace-retargeting-denial",
    "temporary-write-byte-and-inode-exhaustion-containment",
    "terminal-ioctl-and-tiocsti-denial",
    "termination-resistant-descendant-quiescence",
)


LINUX_CONFINEMENT_MANDATORY_NONCLAIM_IDS: Final = (
    "actual-output-freshness-not-attested",
    "covert-channel-freedom-not-attested",
    "decision-eligibility-not-established",
    "executed-interpreter-identity-not-attested",
    "executed-source-identity-not-attested",
    "expected-material-nonexposure-not-attested",
    "external-source-custody-not-authenticated",
    "generalization-not-attested",
    "information-flow-noninterference-not-attested",
    "kernel-or-host-administrator-compromise-outside-model",
    "publication-artifacts-not-rebuilt",
    "semantic-truth-not-attested",
)

LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS: Final = (
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

LINUX_CONFINEMENT_PERMITTED_OUTER_POSITIVE_CLAIM_IDS: Final = (
    "approved-linux-platform-profile-matched",
    "hostile-control-inventory-passed",
    "inner-v1-receipt-digest-joined",
    "named-filesystem-network-process-resource-controls-observed",
    "policy-identities-matched",
    "postrun-cgroup-quiescence-observed",
    "pre-adapter-release-observations-matched",
    "reviewed-supervisor-selected",
)


_FIXED_REQUIREMENTS = MappingProxyType(
    {
        "all_controls_required": True,
        "all_observations_required": True,
        "bounded_monotonic_teardown_sequence_required": True,
        "bubblewrap_argv_is_not_execution_evidence": True,
        "dedicated_linux_execution_required": True,
        "dedicated_single_run_subreaper_supervisor_required": True,
        "exact_fd_kernel_object_contract_required": True,
        "fail_closed_without_required_feature": True,
        "hostile_controls_must_run_after_policy_freeze": True,
        "inner_v1_false_claims_preserved_required": True,
        "inner_v1_receipt_digest_join_required": True,
        "independent_receipt_review_required": True,
        "non_setuid_backend_required": True,
        "outer_monitor_pidfd_bounded_escalation_required": True,
        "outer_transcript_nonce_join_required": True,
        "outer_positive_claim_allowlist_required": True,
        "positive_claims_before_release_forbidden": True,
        "postrun_quiescence_required": True,
        "pre_adapter_release_barrier_required": True,
        "run_nonce_csprng_nonzero_nonreuse_required": True,
        "split_privileged_supervisor_unprivileged_launcher_required": True,
        "stage2_privileged_observation_profile_required": True,
        "static_sealed_backend_execution_required": True,
        (
            "supplementary_groups_cleared_in_preexec_launcher_before_"
            "backend_exec_required"
        ): True,
        "supervisor_owned_non_tty_stdio_pipes_required": True,
        "trusted_native_supervisor_required": True,
        (
            "two_level_user_namespace_map_observation_helper_required"
        ): True,
    }
)


def _contract_tree() -> dict:
    return {
        "artifact_type": (
            LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_ARTIFACT_TYPE
        ),
        "fixed_requirements": dict(_FIXED_REQUIREMENTS),
        "format_version": "1",
        "mandatory_nonclaim_ids": list(
            LINUX_CONFINEMENT_MANDATORY_NONCLAIM_IDS
        ),
        "inherited_inner_false_field_ids": list(
            LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS
        ),
        "permitted_outer_positive_claim_ids": list(
            LINUX_CONFINEMENT_PERMITTED_OUTER_POSITIVE_CLAIM_IDS
        ),
        "required_hostile_control_ids": list(
            LINUX_CONFINEMENT_REQUIRED_HOSTILE_CONTROL_IDS
        ),
        "required_observation_ids": list(
            LINUX_CONFINEMENT_REQUIRED_OBSERVATION_IDS
        ),
        "status_id": LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_STATUS,
        "target_status_id": LINUX_CONFINEMENT_ACCEPTANCE_TARGET_STATUS,
    }


def linux_confinement_acceptance_contract_tree() -> dict:
    """Return a fresh exact projection of the prospective contract."""

    return _contract_tree()


def linux_confinement_acceptance_contract_bytes() -> bytes:
    """Return the fixed contract as canonical ASCII JSON."""

    try:
        result = json.dumps(
            _contract_tree(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise RuntimeError(
            "Linux confinement acceptance contract is not encodable"
        ) from error
    if (
        not result
        or len(result)
        > MAXIMUM_LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_BYTES
    ):
        raise RuntimeError(
            "Linux confinement acceptance contract exceeds its byte ceiling"
        )
    return result


def linux_confinement_acceptance_contract_sha256() -> str:
    """Return the length-framed domain digest of the fixed contract."""

    payload = linux_confinement_acceptance_contract_bytes()
    domain = LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_DIGEST_DOMAIN.encode(
        "ascii"
    )
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


__all__ = [
    "LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_STATUS",
    "LINUX_CONFINEMENT_ACCEPTANCE_TARGET_STATUS",
    "LINUX_CONFINEMENT_MANDATORY_NONCLAIM_IDS",
    "LINUX_CONFINEMENT_INHERITED_INNER_FALSE_FIELD_IDS",
    "LINUX_CONFINEMENT_PERMITTED_OUTER_POSITIVE_CLAIM_IDS",
    "LINUX_CONFINEMENT_REQUIRED_HOSTILE_CONTROL_IDS",
    "LINUX_CONFINEMENT_REQUIRED_OBSERVATION_IDS",
    "MAXIMUM_LINUX_CONFINEMENT_ACCEPTANCE_CONTRACT_BYTES",
    "linux_confinement_acceptance_contract_bytes",
    "linux_confinement_acceptance_contract_sha256",
    "linux_confinement_acceptance_contract_tree",
]
