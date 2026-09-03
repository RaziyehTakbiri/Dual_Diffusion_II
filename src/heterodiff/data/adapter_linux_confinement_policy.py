"""Canonical prospective Linux confinement policy and launch template.

The artifact in this module is a policy candidate, not execution evidence.
It freezes exact identities and control requirements for a future reviewed
Linux supervisor.  The deterministic Bubblewrap argument tuple is only one
low-level mechanism selected by that supervisor.  This module never opens a
path, allocates a descriptor, starts a process, inspects Linux state, or
constructs a positive containment receipt.

All positive execution, confinement, attestation, custody, publication, and
decision claims are fixed false.  The only implementation status admitted by
V1 is ``PROSPECTIVE_UNEXECUTED``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Final

from .adapter_linux_confinement_acceptance import (
    linux_confinement_acceptance_contract_sha256,
)


LINUX_CONFINEMENT_POLICY_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-policy.v1"
)
LINUX_CONFINEMENT_POLICY_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_POLICY_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_POLICY_IMPLEMENTATION_STATUS: Final = (
    "PROSPECTIVE_UNEXECUTED"
)
LINUX_CONFINEMENT_BACKEND_ID: Final = (
    "reviewed-supervisor-bubblewrap-mechanism-v1"
)
LINUX_CONFINEMENT_TARGET_STATUS: Final = "LINUX_CONFINED_DEVELOPMENT"
MAXIMUM_LINUX_CONFINEMENT_POLICY_BYTES: Final = 128 * 1024
MAXIMUM_LINUX_CONFINEMENT_RUN_NONCE_REGISTRY_ENTRIES: Final = 4096

LINUX_CONFINEMENT_ARCHITECTURE_IDS: Final = ("aarch64", "x86_64")
LINUX_CONFINEMENT_NAMESPACE_IDS: Final = (
    "cgroup",
    "ipc",
    "mount",
    "network",
    "pid",
    "user",
    "uts",
)
LINUX_CONFINEMENT_FD_ROLE_IDS: Final = (
    "backend-executable-sealed-memfd-exec",
    "closure-data-read",
    "diagnostic-stderr-write",
    "launch-seccomp-bpf-read",
    "release-barrier-read",
    "request-stdin-read",
    "response-stdout-write",
    "rootfs-read",
    "status-write",
)
LINUX_CONFINEMENT_FORBIDDEN_BWRAP_OPTIONS: Final = (
    "--bind-try",
    "--dev-bind-try",
    "--not-a-security-boundary",
    "--ro-bind-try",
    "--share-net",
    "--unshare-all",
    "--unshare-cgroup-try",
    "--unshare-user-try",
)

LINUX_CONFINEMENT_FALSE_CLAIM_IDS: Final = (
    "actual_output_freshness_attested",
    "adapter_source_execution_identity_attested",
    "covert_channel_freedom_attested",
    "containment_attested",
    "decision_eligible",
    "decision_made",
    "executed_interpreter_identity_attested",
    "expected_material_nonexposure_attested",
    "external_custody_authenticated",
    "filesystem_confinement_attested",
    "generalization_attested",
    "information_flow_noninterference_attested",
    "network_confinement_attested",
    "process_tree_escape_prevented",
    "publication_artifacts_rebuilt",
    "semantic_truth_attested",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RUN_NONCE_RE = re.compile(r"^[0-9a-f]{64}$")
_VERSION_RE = re.compile(r"^[a-z0-9][a-z0-9._+-]{0,63}$")

_BWRAP_FD_TOKENS = MappingProxyType(
    {
        (
            "backend-executable-sealed-memfd-exec"
        ): "${BUBBLEWRAP_EXECUTABLE}",
        "closure-data-read": "${FD_CLOSURE_DATA_READ}",
        "launch-seccomp-bpf-read": "${FD_LAUNCH_SECCOMP_BPF_READ}",
        "release-barrier-read": "${FD_RELEASE_BARRIER_READ}",
        "rootfs-read": "${FD_ROOTFS_READ}",
        "status-write": "${FD_STATUS_WRITE}",
    }
)
_BWRAP_EXECUTABLE_TOKEN = "${BUBBLEWRAP_EXECUTABLE}"
_BWRAP_EXECUTABLE_ARGV0 = "bwrap"
_RUN_NONCE_TOKEN = "${RUN_NONCE_HEX}"
_RUN_NONCE_BYTES = 32
_READY_FRAME_PREFIX_ASCII = "HETERODIFF-LINUX-READY-V1 "
_READY_FRAME_SUFFIX_ASCII = "\n"
_SANDBOX_INTERPRETER_PATH = "/opt/heterodiff/bin/python3"
_SANDBOX_BOOTSTRAP_PATH = "/opt/heterodiff/bootstrap.py"
_SANDBOX_ADAPTER_SECCOMP_PATH = (
    "/opt/heterodiff/adapter-stage-seccomp.bpf"
)
_SANDBOX_CLOSURE_PATH = "/run/heterodiff/closure.frame"
_SANDBOX_WORKING_DIRECTORY = "/work"

_FIXED_NAMESPACES = LINUX_CONFINEMENT_NAMESPACE_IDS
_FIXED_OUTER_ENVIRONMENT = ()
_FIXED_APPLICATION_ENVIRONMENT = (
    ("MKL_NUM_THREADS", "1"),
    ("NUMEXPR_NUM_THREADS", "1"),
    ("OMP_NUM_THREADS", "1"),
    ("OPENBLAS_NUM_THREADS", "1"),
    ("PWD", _SANDBOX_WORKING_DIRECTORY),
    ("PYTHONHASHSEED", "0"),
)
_FIXED_WRITABLE_PATHS = (_SANDBOX_WORKING_DIRECTORY,)
_FIXED_FORBIDDEN_MOUNT_TYPES = (
    "cgroup",
    "cgroup2",
    "mqueue",
    "proc",
    "sysfs",
)
_FIXED_FORBIDDEN_HOST_PATH_CLASSES = (
    "authority-material",
    "daemon-sockets",
    "expected-material",
    "host-root",
    "publication-material",
    "user-home",
    "workspace",
)

_FIXED_CGROUP = MappingProxyType(
    {
        "cpu_max": "100000 100000",
        "memory_high_bytes": 1536 * 1024 * 1024,
        "memory_max_bytes": 2 * 1024 * 1024 * 1024,
        "memory_oom_group": 1,
        "memory_swap_max_bytes": 0,
        "pids_max": 2,
    }
)
_FIXED_RLIMITS = MappingProxyType(
    {
        "address_space_bytes": 2 * 1024 * 1024 * 1024,
        "core_bytes": 0,
        "cpu_hard_seconds": 180,
        "cpu_soft_seconds": 170,
        "file_bytes": 16 * 1024 * 1024,
        "locked_memory_bytes": 0,
        "message_queue_bytes": 0,
        "nofile": 16,
        "nproc": 2,
        "realtime_priority": 0,
        "stack_bytes": 32 * 1024 * 1024,
    }
)
_FIXED_LIMITS = MappingProxyType(
    {
        "aggregate_output_bytes": 34 * 1024 * 1024,
        "temporary_inode_count": 4096,
        "temporary_storage_bytes": 64 * 1024 * 1024,
        "wall_time_nanoseconds": 180 * 1_000_000_000,
    }
)


class LinuxConfinementPolicyCode(str, Enum):
    INPUT_TYPE = "LINUX_CONFINEMENT_POLICY_INPUT_TYPE"
    INPUT_RESOURCE = "LINUX_CONFINEMENT_POLICY_INPUT_RESOURCE"
    JSON_INVALID = "LINUX_CONFINEMENT_POLICY_JSON_INVALID"
    SCHEMA_INVALID = "LINUX_CONFINEMENT_POLICY_SCHEMA_INVALID"
    CANONICAL_MISMATCH = "LINUX_CONFINEMENT_POLICY_CANONICAL_MISMATCH"
    POLICY_INVALID = "LINUX_CONFINEMENT_POLICY_INVALID"
    LAUNCH_SUBSTITUTION_INVALID = (
        "LINUX_CONFINEMENT_LAUNCH_SUBSTITUTION_INVALID"
    )


_ERROR_MESSAGES = MappingProxyType(
    {
        LinuxConfinementPolicyCode.INPUT_TYPE: (
            "Linux confinement policy input has an invalid exact type"
        ),
        LinuxConfinementPolicyCode.INPUT_RESOURCE: (
            "Linux confinement policy input exceeds its byte ceiling"
        ),
        LinuxConfinementPolicyCode.JSON_INVALID: (
            "Linux confinement policy JSON is invalid"
        ),
        LinuxConfinementPolicyCode.SCHEMA_INVALID: (
            "Linux confinement policy schema is invalid"
        ),
        LinuxConfinementPolicyCode.CANONICAL_MISMATCH: (
            "Linux confinement policy bytes are not canonical"
        ),
        LinuxConfinementPolicyCode.POLICY_INVALID: (
            "Linux confinement policy value is invalid"
        ),
        LinuxConfinementPolicyCode.LAUNCH_SUBSTITUTION_INVALID: (
            "Linux confinement launch substitution is invalid"
        ),
    }
)


class LinuxConfinementPolicyError(ValueError):
    """One closed policy failure without untrusted text interpolation."""

    def __init__(self, code: LinuxConfinementPolicyCode) -> None:
        if type(code) is not LinuxConfinementPolicyCode:
            raise TypeError("Linux confinement policy code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: LinuxConfinementPolicyCode) -> None:
    raise LinuxConfinementPolicyError(code) from None


def _sha256(value: object, *, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise TypeError(name + " must be a lowercase SHA-256 string")
    return value


def _version(value: object) -> str:
    if type(value) is not str or _VERSION_RE.fullmatch(value) is None:
        raise TypeError("backend_version_id must be a closed version token")
    return value


@dataclass(frozen=True)
class LinuxConfinementPolicyV1:
    """Exact identities selected by the prospective fixed V1 policy."""

    acceptance_contract_sha256: str
    architecture_id: str
    adapter_seccomp_bpf_sha256: str
    adapter_seccomp_feature_manifest_sha256: str
    backend_executable_sha256: str
    backend_feature_manifest_sha256: str
    backend_version_id: str
    bootstrap_source_sha256: str
    dependency_lock_sha256: str
    hostile_test_inventory_sha256: str
    landlock_ruleset_sha256: str
    launch_seccomp_bpf_sha256: str
    launch_seccomp_feature_manifest_sha256: str
    linux_platform_profile_sha256: str
    runtime_rootfs_image_sha256: str
    runtime_rootfs_manifest_sha256: str
    sandbox_interpreter_sha256: str
    supervisor_dependency_closure_sha256: str
    supervisor_executable_sha256: str
    supervisor_feature_manifest_sha256: str
    supervisor_source_sha256: str
    artifact_type: str = field(
        default=LINUX_CONFINEMENT_POLICY_ARTIFACT_TYPE,
        init=False,
    )
    backend_id: str = field(
        default=LINUX_CONFINEMENT_BACKEND_ID,
        init=False,
    )
    format_version: str = field(default="1", init=False)
    implementation_status_id: str = field(
        default=LINUX_CONFINEMENT_POLICY_IMPLEMENTATION_STATUS,
        init=False,
    )
    landlock_abi_version: int = field(default=10, init=False)
    target_status_id: str = field(
        default=LINUX_CONFINEMENT_TARGET_STATUS,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementPolicyV1:
            raise TypeError("Linux confinement policy must be exact")
        fixed = (
            (
                self.artifact_type,
                LINUX_CONFINEMENT_POLICY_ARTIFACT_TYPE,
            ),
            (self.backend_id, LINUX_CONFINEMENT_BACKEND_ID),
            (self.format_version, "1"),
            (
                self.implementation_status_id,
                LINUX_CONFINEMENT_POLICY_IMPLEMENTATION_STATUS,
            ),
            (self.landlock_abi_version, 10),
            (self.target_status_id, LINUX_CONFINEMENT_TARGET_STATUS),
        )
        if any(
            type(observed) is not type(expected) or observed != expected
            for observed, expected in fixed
        ):
            raise ValueError("fixed Linux confinement policy field changed")
        for name in (
            "acceptance_contract_sha256",
            "adapter_seccomp_bpf_sha256",
            "adapter_seccomp_feature_manifest_sha256",
            "backend_executable_sha256",
            "backend_feature_manifest_sha256",
            "bootstrap_source_sha256",
            "dependency_lock_sha256",
            "hostile_test_inventory_sha256",
            "landlock_ruleset_sha256",
            "launch_seccomp_bpf_sha256",
            "launch_seccomp_feature_manifest_sha256",
            "linux_platform_profile_sha256",
            "runtime_rootfs_image_sha256",
            "runtime_rootfs_manifest_sha256",
            "sandbox_interpreter_sha256",
            "supervisor_dependency_closure_sha256",
            "supervisor_executable_sha256",
            "supervisor_feature_manifest_sha256",
            "supervisor_source_sha256",
        ):
            _sha256(getattr(self, name), name=name)
        if self.acceptance_contract_sha256 != (
            linux_confinement_acceptance_contract_sha256()
        ):
            raise ValueError(
                "acceptance contract does not match the fixed V1 contract"
            )
        if (
            self.adapter_seccomp_bpf_sha256
            == self.launch_seccomp_bpf_sha256
            or self.adapter_seccomp_feature_manifest_sha256
            == self.launch_seccomp_feature_manifest_sha256
        ):
            raise ValueError("the two seccomp stages must be distinct")
        if (
            type(self.architecture_id) is not str
            or self.architecture_id
            not in LINUX_CONFINEMENT_ARCHITECTURE_IDS
        ):
            raise ValueError("architecture is not admitted by V1")
        _version(self.backend_version_id)


def _revalidate_policy(policy: object) -> LinuxConfinementPolicyV1:
    if type(policy) is not LinuxConfinementPolicyV1:
        raise TypeError("Linux confinement policy must be exact")
    try:
        LinuxConfinementPolicyV1.__post_init__(policy)
    except (AttributeError, TypeError, ValueError):
        _fail(LinuxConfinementPolicyCode.POLICY_INVALID)
    return policy


def _fixed_launch_template() -> tuple[str, ...]:
    fd = _BWRAP_FD_TOKENS
    return (
        _BWRAP_EXECUTABLE_TOKEN,
        "--unshare-user",
        "--unshare-ipc",
        "--unshare-pid",
        "--unshare-net",
        "--unshare-uts",
        "--unshare-cgroup",
        "--disable-userns",
        "--uid",
        "65534",
        "--gid",
        "65534",
        "--hostname",
        "heterodiff-child",
        "--cap-drop",
        "ALL",
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--setenv",
        "MKL_NUM_THREADS",
        "1",
        "--setenv",
        "NUMEXPR_NUM_THREADS",
        "1",
        "--setenv",
        "OMP_NUM_THREADS",
        "1",
        "--setenv",
        "OPENBLAS_NUM_THREADS",
        "1",
        "--setenv",
        "PWD",
        _SANDBOX_WORKING_DIRECTORY,
        "--setenv",
        "PYTHONHASHSEED",
        "0",
        "--ro-bind-fd",
        fd["rootfs-read"],
        "/",
        "--dev",
        "/dev",
        "--chmod",
        "000",
        "/dev/shm",
        "--chmod",
        "000",
        "/dev/pts/ptmx",
        "--remount-ro",
        "/dev/pts",
        "--remount-ro",
        "/dev",
        "--size",
        str(_FIXED_LIMITS["temporary_storage_bytes"]),
        "--perms",
        "0700",
        "--tmpfs",
        _SANDBOX_WORKING_DIRECTORY,
        "--perms",
        "0400",
        "--ro-bind-data",
        fd["closure-data-read"],
        _SANDBOX_CLOSURE_PATH,
        "--seccomp",
        fd["launch-seccomp-bpf-read"],
        "--json-status-fd",
        fd["status-write"],
        "--block-fd",
        fd["release-barrier-read"],
        "--chdir",
        _SANDBOX_WORKING_DIRECTORY,
        "--",
        _SANDBOX_INTERPRETER_PATH,
        "-I",
        "-B",
        _SANDBOX_BOOTSTRAP_PATH,
        _SANDBOX_CLOSURE_PATH,
        _RUN_NONCE_TOKEN,
    )


def build_bubblewrap_launch_template(
    policy: LinuxConfinementPolicyV1,
) -> tuple[str, ...]:
    """Return the exact symbolic V1 argv; never substitute or execute it."""

    _revalidate_policy(policy)
    return _fixed_launch_template()


def bubblewrap_launch_template_bytes(
    policy: LinuxConfinementPolicyV1,
) -> bytes:
    """Return canonical JSON bytes for the exact symbolic argument tuple."""

    try:
        return json.dumps(
            list(build_bubblewrap_launch_template(policy)),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementPolicyCode.POLICY_INVALID)


def _validate_run_nonce(
    value: object,
    *,
    code: LinuxConfinementPolicyCode,
) -> str:
    if (
        type(value) is not str
        or _RUN_NONCE_RE.fullmatch(value) is None
        or value == "0" * (_RUN_NONCE_BYTES * 2)
    ):
        _fail(code)
    return value


def linux_confinement_ready_frame(run_nonce_hex: str) -> bytes:
    """Build the one exact first-stdout READY frame for a valid nonce."""

    nonce = _validate_run_nonce(
        run_nonce_hex,
        code=LinuxConfinementPolicyCode.LAUNCH_SUBSTITUTION_INVALID,
    )
    return (
        _READY_FRAME_PREFIX_ASCII
        + nonce
        + _READY_FRAME_SUFFIX_ASCII
    ).encode("ascii")


def materialize_bubblewrap_launch_argv(
    policy: LinuxConfinementPolicyV1,
    *,
    fd_by_role: dict[str, int],
    run_nonce_hex: str,
    run_sequence_number: int,
    prior_run_nonce_hexes: tuple[str, ...],
) -> tuple[str, ...]:
    """Validate and apply the only admitted per-run substitutions.

    This pure helper neither allocates descriptors nor establishes nonce
    freshness.  A future trusted supervisor must supply its complete,
    bounded current-epoch nonce registry and descriptors that it opened and
    content-verified.  It also requires the run sequence to equal the supplied
    registry insertion index.  The helper rejects registry exhaustion, reuse,
    malformed roles, stdio aliasing, setup-FD collisions, and unresolved
    symbolic tokens.  Descriptor types and ``isatty`` state remain future
    supervisor observations; this pure helper cannot inspect them.
    """

    _revalidate_policy(policy)
    code = LinuxConfinementPolicyCode.LAUNCH_SUBSTITUTION_INVALID
    if (
        type(fd_by_role) is not dict
        or len(fd_by_role) != len(LINUX_CONFINEMENT_FD_ROLE_IDS)
        or any(type(role) is not str for role in fd_by_role)
        or set(fd_by_role) != set(LINUX_CONFINEMENT_FD_ROLE_IDS)
        or any(type(value) is not int for value in fd_by_role.values())
    ):
        _fail(code)
    if (
        fd_by_role["request-stdin-read"] != 0
        or fd_by_role["response-stdout-write"] != 1
        or fd_by_role["diagnostic-stderr-write"] != 2
        or len(set(fd_by_role.values())) != len(fd_by_role)
    ):
        _fail(code)
    non_stdio_roles = (
        set(LINUX_CONFINEMENT_FD_ROLE_IDS)
        - {
            "request-stdin-read",
            "response-stdout-write",
            "diagnostic-stderr-write",
        }
    )
    if any(
        fd_by_role[role] < 3
        or fd_by_role[role] >= _FIXED_RLIMITS["nofile"]
        for role in non_stdio_roles
    ):
        _fail(code)
    nonce = _validate_run_nonce(run_nonce_hex, code=code)
    if (
        type(run_sequence_number) is not int
        or run_sequence_number < 0
        or run_sequence_number
        >= MAXIMUM_LINUX_CONFINEMENT_RUN_NONCE_REGISTRY_ENTRIES
    ):
        _fail(code)
    if (
        type(prior_run_nonce_hexes) is not tuple
        or len(prior_run_nonce_hexes)
        >= MAXIMUM_LINUX_CONFINEMENT_RUN_NONCE_REGISTRY_ENTRIES
        or run_sequence_number != len(prior_run_nonce_hexes)
    ):
        _fail(code)
    prior = []
    for value in prior_run_nonce_hexes:
        prior.append(_validate_run_nonce(value, code=code))
    if len(prior) != len(set(prior)) or nonce in prior:
        _fail(code)

    replacements = {
        _BWRAP_EXECUTABLE_TOKEN: _BWRAP_EXECUTABLE_ARGV0,
        _RUN_NONCE_TOKEN: nonce,
    }
    replacements.update(
        {
            token: str(fd_by_role[role])
            for role, token in _BWRAP_FD_TOKENS.items()
            if role != "backend-executable-sealed-memfd-exec"
        }
    )
    result = tuple(
        replacements.get(argument, argument)
        for argument in build_bubblewrap_launch_template(policy)
    )
    if any("${" in argument or "}" in argument for argument in result):
        _fail(code)
    return result


def _domain_sha256(domain: str, payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def bubblewrap_launch_template_sha256(
    policy: LinuxConfinementPolicyV1,
) -> str:
    return _domain_sha256(
        "heterodiff.adapter.linux-bubblewrap-launch-template.v1",
        bubblewrap_launch_template_bytes(policy),
    )


def _fixed_fd_contract_tree() -> dict:
    pipe_read = "fresh-supervisor-owned-anonymous-pipe-read-end-v1"
    pipe_write = "fresh-supervisor-owned-anonymous-pipe-write-end-v1"
    return {
        "backend-executable-sealed-memfd-exec": {
            "access_mode_id": "f-getfl-o-rdwr-from-memfd-create-v1",
            "execution_permission_id": "mfd-exec-inode-mode-0500-v1",
            "fd_cloexec_before_backend_exec": True,
            "inherited_by_application": False,
            "inherited_by_backend": False,
            "inode_gid_rule_id": "bound-launcher-service-gid-v1",
            "kernel_object_type_id": "sealed-memfd-static-elf-v1",
            "memfd_create_flag_ids": [
                "MFD_ALLOW_SEALING",
                "MFD_CLOEXEC",
                "MFD_EXEC",
            ],
            "nonblocking": False,
            "offset_rule_id": "kernel-exec-image-offset-independent-v1",
            "inode_uid_rule_id": "bound-launcher-service-uid-v1",
        },
        "closure-data-read": {
            "access_mode_id": "read-only",
            "content_identity_binding_id": "per-run-closure-sha256-v1",
            "fd_cloexec_before_backend_exec": False,
            "inherited_by_application": False,
            "inherited_by_backend": True,
            "kernel_object_type_id": "sealed-memfd-regular-file-v1",
            "nonblocking": False,
            "offset_rule_id": "exactly-zero-before-backend-exec-v1",
        },
        "diagnostic-stderr-write": {
            "access_mode_id": "write-only",
            "fd_cloexec_before_backend_exec": False,
            "inherited_by_application": True,
            "inherited_by_backend": True,
            "isatty": False,
            "kernel_object_type_id": pipe_write,
            "nonblocking": False,
            "peer_custody_id": "supervisor-only-read-end-concurrent-drain-v1",
        },
        "launch-seccomp-bpf-read": {
            "access_mode_id": "read-only",
            "content_identity_binding_id": "policy-launch-seccomp-sha256-v1",
            "fd_cloexec_before_backend_exec": False,
            "inherited_by_application": False,
            "inherited_by_backend": True,
            "kernel_object_type_id": "sealed-memfd-regular-file-v1",
            "nonblocking": False,
            "offset_rule_id": "exactly-zero-before-backend-exec-v1",
        },
        "release-barrier-read": {
            "access_mode_id": "read-only",
            "fd_cloexec_before_backend_exec": False,
            "inherited_by_application": False,
            "inherited_by_backend": True,
            "kernel_object_type_id": pipe_read,
            "nonblocking": False,
            "peer_custody_id": "supervisor-only-write-end-v1",
            "pre_release_failure_close_before_blocked_child_reap_forbidden": (
                True
            ),
            "release_payload_hex": "01",
            "release_write_count": 1,
        },
        "request-stdin-read": {
            "access_mode_id": "read-only",
            "fd_cloexec_before_backend_exec": False,
            "inherited_by_application": True,
            "inherited_by_backend": True,
            "isatty": False,
            "kernel_object_type_id": pipe_read,
            "nonblocking": False,
            "peer_custody_id": "supervisor-only-write-end-v1",
        },
        "response-stdout-write": {
            "access_mode_id": "write-only",
            "fd_cloexec_before_backend_exec": False,
            "inherited_by_application": True,
            "inherited_by_backend": True,
            "isatty": False,
            "kernel_object_type_id": pipe_write,
            "nonblocking": False,
            "peer_custody_id": "supervisor-only-read-end-concurrent-drain-v1",
        },
        "rootfs-read": {
            "access_mode_id": "path-directory",
            "content_identity_binding_id": "policy-rootfs-manifest-sha256-v1",
            "fd_cloexec_before_backend_exec": False,
            "inherited_by_application": False,
            "inherited_by_backend": True,
            "kernel_object_type_id": "immutable-root-directory-o-path-v1",
            "nonblocking": False,
            "offset_rule_id": "not-applicable-directory-v1",
        },
        "status-write": {
            "access_mode_id": "write-only",
            "fd_cloexec_before_backend_exec": False,
            "inherited_by_application": False,
            "inherited_by_backend": True,
            "kernel_object_type_id": pipe_write,
            "nonblocking": False,
            "peer_custody_id": "supervisor-only-read-end-concurrent-drain-v1",
        },
    }


def linux_confinement_policy_tree(
    policy: LinuxConfinementPolicyV1,
) -> dict:
    """Project the exact nested V1 policy tree."""

    _revalidate_policy(policy)
    identities = {
        name: getattr(policy, name)
        for name in (
            "acceptance_contract_sha256",
            "adapter_seccomp_bpf_sha256",
            "adapter_seccomp_feature_manifest_sha256",
            "backend_executable_sha256",
            "backend_feature_manifest_sha256",
            "bootstrap_source_sha256",
            "dependency_lock_sha256",
            "hostile_test_inventory_sha256",
            "landlock_ruleset_sha256",
            "launch_seccomp_bpf_sha256",
            "launch_seccomp_feature_manifest_sha256",
            "linux_platform_profile_sha256",
            "runtime_rootfs_image_sha256",
            "runtime_rootfs_manifest_sha256",
            "sandbox_interpreter_sha256",
            "supervisor_dependency_closure_sha256",
            "supervisor_executable_sha256",
            "supervisor_feature_manifest_sha256",
            "supervisor_source_sha256",
        )
    }
    return {
        "artifact_type": policy.artifact_type,
        "backend": {
            "backend_id": policy.backend_id,
            "backend_version_id": policy.backend_version_id,
            "backend_argv0": _BWRAP_EXECUTABLE_ARGV0,
            "backend_exec_path_lookup_forbidden": True,
            "backend_execution_method_id": (
                "execveat-content-verified-fd-at-empty-path-v1"
            ),
            "backend_executable_fd_close_or_remap_before_exec_forbidden": True,
            "backend_executable_linkage_id": (
                "fully-static-elf-no-pt-interp-no-dt-needed-v1"
            ),
            "backend_executable_mode_and_digest_preverified": True,
            "backend_execution_memfd_required": True,
            "backend_execution_memfd_seal_ids": [
                "F_SEAL_GROW",
                "F_SEAL_SEAL",
                "F_SEAL_SHRINK",
                "F_SEAL_WRITE",
            ],
            "backend_execution_memfd_sha256_reverified": True,
            "backend_dynamic_loader_admitted": False,
            "backend_dynamic_library_count": 0,
            "backend_runtime_dynamic_loading_forbidden": True,
            "backend_path_fallback_forbidden": True,
            "backend_unsealed_or_path_backed_execution_forbidden": True,
            "bubblewrap_launch_template_sha256": (
                bubblewrap_launch_template_sha256(policy)
            ),
            "bubblewrap_role_tokens": dict(_BWRAP_FD_TOKENS),
            "forbidden_option_ids": list(
                LINUX_CONFINEMENT_FORBIDDEN_BWRAP_OPTIONS
            ),
            "template_enforces_temporary_inode_limit": False,
            "template_enforces_temporary_noexec": False,
            (
                "template_remounts_device_regular_filesystem_read_only"
            ): True,
            "template_is_execution_evidence": False,
            "setup_stage_block_required": True,
            "trusted_supervisor_required": True,
        },
        "claim_state": {
            name: False for name in LINUX_CONFINEMENT_FALSE_CLAIM_IDS
        },
        "credentials": {
            "ambient_capabilities": [],
            "bounding_capabilities": [],
            "dumpable": False,
            "effective_capabilities": [],
            "gid": 65534,
            "backend_launcher_service_identity_bound_by_platform_profile": (
                True
            ),
            "backend_launcher_service_identity_nonroot_required": True,
            "inheritable_capabilities": [],
            "no_new_privileges": True,
            "permitted_capabilities": [],
            "securebits_lock_required": False,
            "securebits_mask_hex": "00000000",
            "securebits_profile_id": (
                "mask-zero-zero-capability-no-new-privileges-v1"
            ),
            "split_launcher_model_id": (
                "privileged-supervisor-unprivileged-preexec-child-v1"
            ),
            "supplementary_groups": [],
            (
                "preexec_launcher_clears_and_verifies_supplementary_groups_"
                "before_backend_exec"
            ): True,
            "preexec_launcher_umask_octal": "077",
            "preexec_launcher_umask_set_and_verified_before_backend_exec": (
                True
            ),
            (
                "supervisor_observes_empty_application_supplementary_groups_"
                "before_stage2_release"
            ): True,
            (
                "unprivileged_launcher_drops_all_capabilities_before_"
                "backend_exec"
            ): True,
            (
                "unprivileged_launcher_sets_no_new_privileges_before_"
                "backend_exec"
            ): True,
            "uid": 65534,
            "user_namespace_map_topology": {
                (
                    "application_depth_from_launcher_user_namespace"
                ): 2,
                "composed_host_gid_rule_id": (
                    "sandbox-65534-to-bound-launcher-service-gid-v1"
                ),
                "composed_host_uid_rule_id": (
                    "sandbox-65534-to-bound-launcher-service-uid-v1"
                ),
                "final_level_id": "application-user-namespace",
                "final_level_gid_map": [
                    {
                        "inside_id": 65534,
                        "length": 1,
                        "outside_id": 0,
                    }
                ],
                "final_level_setgroups_ascii": "deny\n",
                "final_level_uid_map": [
                    {
                        "inside_id": 65534,
                        "length": 1,
                        "outside_id": 0,
                    }
                ],
                "intermediate_level_gid_map": [
                    {
                        "inside_id": 0,
                        "length": 1,
                        "outside_id_source_id": (
                            "bound-launcher-service-gid"
                        ),
                    }
                ],
                "intermediate_level_id": "devpts-setup-user-namespace",
                "intermediate_level_setgroups_ascii": "deny\n",
                "intermediate_level_uid_map": [
                    {
                        "inside_id": 0,
                        "length": 1,
                        "outside_id_source_id": (
                            "bound-launcher-service-uid"
                        ),
                    }
                ],
                "literal_map_line_terminator_ascii": "\n",
                "topology_id": (
                    "bubblewrap-devpts-disable-userns-two-level-v1"
                ),
            },
        },
        "filesystem": {
            "closure_path": _SANDBOX_CLOSURE_PATH,
            "device_projection_id": "bubblewrap-private-minimal-dev-v1",
            "device_character_io_semantics_admitted": True,
            "device_console_present": False,
            "host_tty_device_binding_admitted": False,
            "device_projection_regular_filesystem_read_only": True,
            (
                "device_projection_regular_filesystem_remount_by_template_"
                "required"
            ): True,
            "device_shm_mode_octal": "000",
            "device_shm_writable": False,
            "devpts_read_only": True,
            "ptmx_mode_octal": "000",
            "pty_allocation_admitted": False,
            "forbidden_host_path_class_ids": list(
                _FIXED_FORBIDDEN_HOST_PATH_CLASSES
            ),
            "forbidden_mount_type_ids": list(
                _FIXED_FORBIDDEN_MOUNT_TYPES
            ),
            "immutable_rootfs_required": True,
            "old_root_detached_observation_required": True,
            "rootfs_mount_id": "descriptor-readonly-bind-v1",
            "runtime_root_read_only": True,
            "temporary_mount_flags": [
                "nodev",
                "noexec",
                "nosuid",
            ],
            "temporary_noexec_remount_by_supervisor_required": True,
            "writable_paths": list(_FIXED_WRITABLE_PATHS),
        },
        "format_version": policy.format_version,
        "identities": identities,
        "implementation_status_id": policy.implementation_status_id,
        "isolation": {
            "application_environment": [
                {"name": name, "value": value}
                for name, value in _FIXED_APPLICATION_ENVIRONMENT
            ],
            "adapter_import_after_second_release_required": True,
            "application_umask_octal": "077",
            "application_working_directory": (
                _SANDBOX_WORKING_DIRECTORY
            ),
            "bootstrap_input_descriptors_closed_before_sigstop_required": (
                True
            ),
            "distinct_namespace_ids": list(_FIXED_NAMESPACES),
            "fd_role_ids": list(LINUX_CONFINEMENT_FD_ROLE_IDS),
            "fd_contract_by_role": _fixed_fd_contract_tree(),
            "fd_contract_observation_required": True,
            "fd_roles_pairwise_distinct_required": True,
            "first_stage_barrier_id": (
                "bubblewrap-block-fd-before-application-fork-v1"
            ),
            "host_network_visible": False,
            "landlock_abi_version": policy.landlock_abi_version,
            "nested_user_namespaces_disabled": True,
            "outer_environment": list(_FIXED_OUTER_ENVIRONMENT),
            "bubblewrap_monitor_child_exit_signal_id": "SIGCHLD",
            "bubblewrap_monitor_pidfd_acquisition_id": (
                "clone3-clone-pidfd-sigchld-atomic-before-child-execution-v1"
            ),
            "bubblewrap_monitor_pidfd_required": True,
            "pidfd_identity_required": True,
            (
                "supervisor_child_subreaper_set_before_first_child_"
                "creation"
            ): True,
            "supervisor_preexisting_child_count": 0,
            "supervisor_process_model_id": (
                "dedicated-single-run-child-subreaper-v1"
            ),
            "supervisor_run_concurrency": 1,
            "user_namespace_map_observation": {
                "final_namespace_fd_acquisition_id": (
                    "pidfd-bound-setup-pid-proc-user-namespace-open-v1"
                ),
                "helper_control_fd_contract_id": (
                    "sole-seqpacket-end-plus-scm-rights-observation-fds-v1"
                ),
                "helper_control_received_fd_role_ids": [
                    "final-user-namespace-fd",
                    "intermediate-user-namespace-fd",
                    "pidfd-bound-setup-proc-directory-fd",
                ],
                "helper_child_creation_id": (
                    "clone3-clone-pidfd-sigchld-no-shared-state-v1"
                ),
                (
                    "helper_created_before_child_visible_fd_allocation"
                ): True,
                "helper_deadline_nanoseconds": 1_000_000_000,
                "helper_direct_wait_reap_required": True,
                "helper_in_run_cgroup": False,
                (
                    "helper_inherits_backend_barrier_or_stdio_peer_fds"
                ): False,
                "helper_entry_closes_all_unlisted_fds_required": True,
                "helper_pre_control_open_fd_role_ids": [
                    "supervisor-control-seqpacket-end",
                ],
                "helper_stdio_closed_before_control_receive_required": True,
                "helper_join_namespace_id": (
                    "intermediate-devpts-setup-user-namespace"
                ),
                "helper_pidfd_sigkill_on_failure_required": True,
                (
                    "helper_privilege_profile_bound_by_platform_profile"
                ): True,
                "helper_reap_before_first_stage_release_required": True,
                "helper_result_frame_id": (
                    "canonical-userns-map-observation-transcript-v1"
                ),
                "helper_result_transport_id": (
                    "supervisor-owned-seqpacket-scm-rights-v1"
                ),
                "helper_single_threaded_required": True,
                "helper_state_sharing_clone_flag_ids": [],
                "helper_transcript_join_required": True,
                "initial_namespace_fd_acquisition_id": (
                    "pre-first-child-proc-self-ns-user-open-v1"
                ),
                "intermediate_namespace_fd_acquisition_id": (
                    "ns-get-parent-from-final-user-namespace-fd-v1"
                ),
                (
                    "intermediate_parent_chain_to_initial_fstat_match_"
                    "required"
                ): True,
                "map_read_ids": [
                    "host-view-final-gid-map",
                    "host-view-final-uid-map",
                    "intermediate-self-gid-map",
                    "intermediate-self-setgroups",
                    "intermediate-self-uid-map",
                    "intermediate-view-final-gid-map",
                    "intermediate-view-final-setgroups",
                    "intermediate-view-final-uid-map",
                ],
                "namespace_fd_type_and_inode_chain_verified": True,
                "proc_map_parse_id": (
                    "strict-one-decimal-triplet-canonicalized-v1"
                ),
                "proc_map_raw_write_byte_equality_required": False,
                "setns_flag_id": "CLONE_NEWUSER",
                "setns_return_to_host_attempted": False,
                "setup_proc_directory_fd_acquisition_id": (
                    "pidfd-bound-proc-pid-o-path-directory-v1"
                ),
            },
            "readiness_channel_id": (
                "stdout-nonce-bound-ready-prefix-before-response-v1"
            ),
            "readiness_frame_constant_time_nonce_match_required": True,
            "readiness_frame_exactly_once_required": True,
            "readiness_frame_length_bytes": (
                len(_READY_FRAME_PREFIX_ASCII)
                + (_RUN_NONCE_BYTES * 2)
                + len(_READY_FRAME_SUFFIX_ASCII)
            ),
            "readiness_frame_first_stdout_bytes_required": True,
            "readiness_frame_parser_id": (
                "chunking-independent-exact-first-frame-state-machine-v1"
            ),
            "readiness_frame_prefix_ascii": _READY_FRAME_PREFIX_ASCII,
            "readiness_frame_pre_release_trailing_bytes_forbidden": True,
            "readiness_frame_stripped_before_response_parse": True,
            "readiness_frame_suffix_ascii": _READY_FRAME_SUFFIX_ASCII,
            "readiness_like_postrelease_bytes_reinterpreted": False,
            "readiness_stopped_process_pidfd_match_required": True,
            "run_nonce_argv_token": _RUN_NONCE_TOKEN,
            "run_nonce_bits": _RUN_NONCE_BYTES * 8,
            "run_nonce_encoding_id": "lowercase-hex-fixed-64-v1",
            "run_nonce_generation_id": (
                "linux-getrandom-flags-zero-exact-32-bytes-v1"
            ),
            "run_nonce_is_authenticator": False,
            "run_nonce_is_secret": False,
            "run_nonce_nonzero_required": True,
            (
                "run_nonce_registry_atomic_check_and_register_before_spawn"
            ): True,
            "run_nonce_registry_total_entry_capacity": (
                MAXIMUM_LINUX_CONFINEMENT_RUN_NONCE_REGISTRY_ENTRIES
            ),
            "run_nonce_registry_exhaustion_fails_closed": True,
            "run_nonce_registry_nonreuse_required": True,
            "run_nonce_registry_scope_id": (
                "trusted-supervisor-process-epoch-v1"
            ),
            "run_sequence_equals_atomic_registry_insertion_index": True,
            "run_sequence_maximum": (
                MAXIMUM_LINUX_CONFINEMENT_RUN_NONCE_REGISTRY_ENTRIES - 1
            ),
            "run_sequence_minimum": 0,
            "run_sequence_no_wrap": True,
            "supervisor_epoch_restart_rule_id": (
                "new-getrandom-256-bit-epoch-id-and-sequence-zero-v1"
            ),
            "transcript_join_field_ids": [
                "inner-v1-receipt-sha256",
                "observation-transcript-sha256",
                "pidfd-bound-process-identities",
                "policy-sha256",
                "release-transcript-sha256",
                "run-nonce-hex",
                "run-sequence-number",
                "supervisor-epoch-id",
                "userns-map-observation-transcript-sha256",
            ],
            "stdio_fd_by_role": {
                "diagnostic-stderr-write": 2,
                "request-stdin-read": 0,
                "response-stdout-write": 1,
            },
            "stdio_isatty_by_role": {
                "diagnostic-stderr-write": False,
                "request-stdin-read": False,
                "response-stdout-write": False,
            },
            "stdio_transport_by_role": {
                "diagnostic-stderr-write": (
                    "supervisor-owned-anonymous-pipe-write-end-v1"
                ),
                "request-stdin-read": (
                    "supervisor-owned-anonymous-pipe-read-end-v1"
                ),
                "response-stdout-write": (
                    "supervisor-owned-anonymous-pipe-write-end-v1"
                ),
            },
            "supervisor_owned_stdio_pipes_required": True,
            "substitution_manifest_validation_required": True,
            "unresolved_symbolic_token_forbidden": True,
            "adapter_seccomp_bpf_path": (
                _SANDBOX_ADAPTER_SECCOMP_PATH
            ),
            "adapter_seccomp_installed_before_sigstop": True,
            "adapter_stage_later_exec_and_exec_mapping_denied": True,
            (
                "launch_seccomp_allows_exact_bubblewrap_pid1_reaper_syscalls"
            ): True,
            "launch_seccomp_allows_initial_interpreter_exec": True,
            "launch_seccomp_process_role_ids": [
                "bubblewrap-pid1-reaper",
                "staging-bootstrap-loader",
            ],
            "sandbox_bootstrap_path": _SANDBOX_BOOTSTRAP_PATH,
            "sandbox_interpreter_path": _SANDBOX_INTERPRETER_PATH,
            "seccomp_default_action_id": "kill-process",
            "seccomp_filter_count": 2,
            "seccomp_no_compat_abi": True,
            "second_stage_barrier_id": (
                "bootstrap-sigstop-pidfd-sigcont-v1"
            ),
            "two_stage_release_barrier_required": True,
        },
        "platform": {
            "architecture_id": policy.architecture_id,
            "cgroup_version_id": "v2",
            "landlock_required": True,
            "linux_only": True,
            "namespace_feature_probe_required": True,
            "non_setuid_backend_required": True,
            "pidfd_required": True,
            "privileged_supervisor_direct_backend_exec_forbidden": True,
            (
                "privileged_supervisor_host_capability_profile_bound_by_"
                "platform_profile"
            ): True,
            "seccomp_filter_required": True,
            (
                "stage2_cross_user_namespace_inspection_privilege_profile_"
                "required"
            ): True,
            (
                "supervisor_preexec_setgroups_privilege_profile_required"
            ): True,
            "supervisor_initial_user_namespace_required": True,
        },
        "resources": {
            "cgroup_v2": dict(_FIXED_CGROUP),
            "cgroup_counted_process_role_ids": [
                "application",
                "sandbox-pid1-reaper",
            ],
            "cgroup_outer_process_role_ids": [
                "bubblewrap-monitor",
                "privileged-supervisor",
                "unprivileged-preexec-launcher",
                "userns-map-observation-helper",
            ],
            "limits": dict(_FIXED_LIMITS),
            "rlimits": dict(_FIXED_RLIMITS),
            "supervisor_owns_cgroup_leaf": True,
            "temporary_inode_limit_supervisor_enforced": True,
            "teardown_cgroup_kill_quiescence_deadline_nanoseconds": (
                2_000_000_000
            ),
            "teardown_cleanup_failure_overrides_child_success": True,
            "teardown_clock_id": "CLOCK_MONOTONIC",
            "teardown_method_id": (
                "bounded-targeted-signal-monitor-escalation-cgroup-"
                "quiescence-v1"
            ),
            "teardown_outer_monitor_direct_wait_reap_required": True,
            "teardown_outer_monitor_exit_deadline_nanoseconds": (
                1_000_000_000
            ),
            "teardown_outer_monitor_first_deadline_action_id": (
                "mark-child-run-failed-and-pidfd-sigkill-exact-monitor-v1"
            ),
            "teardown_outer_monitor_pidfd_signal_id": "SIGKILL",
            "teardown_outer_monitor_second_deadline_action_id": (
                "fail-cleanup-gate-v1"
            ),
            "teardown_outer_monitor_sigkill_reap_deadline_nanoseconds": (
                1_000_000_000
            ),
            "teardown_pidfd_exit_observation_deadline_nanoseconds": (
                2_000_000_000
            ),
            "teardown_targeted_reap_chain_role_ids": [
                "application-reaped-by-sandbox-pid1",
                "bubblewrap-monitor-wait-reaped-by-supervisor",
                (
                    "sandbox-pid1-adopted-and-wait-reaped-by-supervisor-"
                    "subreaper"
                ),
            ],
            "teardown_emergency_cgroup_kill_forces_child_run_failure": True,
            "teardown_emergency_reap_chain_role_ids": [
                "bubblewrap-monitor-wait-reaped-by-supervisor",
                (
                    "remaining-sandbox-processes-adopted-and-wait-reaped-"
                    "by-supervisor-subreaper"
                ),
            ],
            "teardown_emergency_sequence_ids": [
                "cgroup-kill-and-mark-child-run-failed",
                "pidfd-observe-all-bound-sandbox-process-exits",
                (
                    "wait-for-bubblewrap-monitor-exit-until-first-"
                    "deadline"
                ),
                (
                    "on-first-deadline-mark-child-run-failed-and-pidfd-"
                    "sigkill-exact-monitor"
                ),
                (
                    "wait-reap-bubblewrap-monitor-within-second-"
                    "deadline"
                ),
                "wait-reap-complete-adopted-run-descendant-inventory",
                "require-cgroup-populated-zero",
                "require-stream-eof-and-bounded-drain",
            ],
            "teardown_phase_sequence_ids": {
                "post-stage1-pre-stage2": [
                    "close-request-writer",
                    "pidfd-sigkill-application-without-term-grace",
                    "require-application-reap-by-sandbox-pid1",
                    (
                        "wait-for-bubblewrap-monitor-exit-until-first-"
                        "deadline"
                    ),
                    (
                        "on-first-deadline-mark-child-run-failed-and-"
                        "pidfd-sigkill-exact-monitor"
                    ),
                    (
                        "wait-reap-bubblewrap-monitor-within-second-"
                        "deadline"
                    ),
                    "wait-reap-adopted-sandbox-pid1",
                    "require-cgroup-populated-zero",
                    "require-stream-eof-and-bounded-drain",
                    "enter-emergency-branch-on-any-deadline",
                ],
                "post-stage2-or-running": [
                    "close-request-writer",
                    "pidfd-sigterm-application",
                    "term-grace-unless-leaf-empty",
                    "pidfd-sigkill-application-if-still-running",
                    "require-application-reap-by-sandbox-pid1",
                    (
                        "wait-for-bubblewrap-monitor-exit-until-first-"
                        "deadline"
                    ),
                    (
                        "on-first-deadline-mark-child-run-failed-and-"
                        "pidfd-sigkill-exact-monitor"
                    ),
                    (
                        "wait-reap-bubblewrap-monitor-within-second-"
                        "deadline"
                    ),
                    "wait-reap-adopted-sandbox-pid1",
                    "require-cgroup-populated-zero",
                    "require-stream-eof-and-bounded-drain",
                    "enter-emergency-branch-on-any-deadline",
                ],
                "pre-stage1-release": [
                    "retain-barrier-writer-without-write",
                    (
                        "pidfd-sigkill-userns-map-observation-helper-if-"
                        "not-reaped"
                    ),
                    (
                        "wait-reap-userns-map-observation-helper-within-"
                        "deadline"
                    ),
                    "pidfd-sigkill-blocked-setup-child",
                    (
                        "wait-for-bubblewrap-monitor-exit-until-first-"
                        "deadline"
                    ),
                    (
                        "on-first-deadline-mark-child-run-failed-and-"
                        "pidfd-sigkill-exact-monitor"
                    ),
                    (
                        "wait-reap-bubblewrap-monitor-within-second-"
                        "deadline"
                    ),
                    (
                        "wait-reap-setup-child-if-adopted-by-supervisor-"
                        "subreaper"
                    ),
                    "close-barrier-writer-after-child-exit-observation",
                    "require-stream-eof-and-bounded-drain",
                    "enter-emergency-branch-on-any-deadline",
                ],
            },
            "teardown_stream_eof_drain_deadline_nanoseconds": 1_000_000_000,
            "teardown_wait_nonchild_before_subreaper_adoption_forbidden": True,
            "teardown_term_grace_nanoseconds": 250_000_000,
            "teardown_uninterruptible_task_at_deadline_fails_gate": True,
        },
        "target_status_id": policy.target_status_id,
    }


def linux_confinement_policy_bytes(
    policy: LinuxConfinementPolicyV1,
) -> bytes:
    """Serialize one exact policy as bounded canonical ASCII JSON."""

    if type(policy) is not LinuxConfinementPolicyV1:
        raise TypeError("Linux confinement policy must be exact")
    try:
        result = json.dumps(
            linux_confinement_policy_tree(policy),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except LinuxConfinementPolicyError:
        raise
    except (TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementPolicyCode.POLICY_INVALID)
    if (
        not result
        or len(result) > MAXIMUM_LINUX_CONFINEMENT_POLICY_BYTES
    ):
        _fail(LinuxConfinementPolicyCode.INPUT_RESOURCE)
    return result


def linux_confinement_policy_sha256(
    policy: LinuxConfinementPolicyV1,
) -> str:
    return _domain_sha256(
        LINUX_CONFINEMENT_POLICY_DIGEST_DOMAIN,
        linux_confinement_policy_bytes(policy),
    )


class _DuplicateKeyError(ValueError):
    pass


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError()
        result[key] = value
    return result


def _reject_constant(_: str) -> object:
    raise ValueError()


def parse_linux_confinement_policy(
    raw: bytes,
) -> LinuxConfinementPolicyV1:
    """Strictly parse, reconstruct, and canonical-check arbitrary bytes."""

    if type(raw) is not bytes:
        _fail(LinuxConfinementPolicyCode.INPUT_TYPE)
    if not raw or len(raw) > MAXIMUM_LINUX_CONFINEMENT_POLICY_BYTES:
        _fail(LinuxConfinementPolicyCode.INPUT_RESOURCE)
    try:
        text = raw.decode("ascii", "strict")
        tree = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except (
        UnicodeError,
        json.JSONDecodeError,
        _DuplicateKeyError,
        RecursionError,
        ValueError,
    ):
        _fail(LinuxConfinementPolicyCode.JSON_INVALID)
    if type(tree) is not dict:
        _fail(LinuxConfinementPolicyCode.SCHEMA_INVALID)
    try:
        identities = tree["identities"]
        backend = tree["backend"]
        platform = tree["platform"]
        if (
            type(identities) is not dict
            or type(backend) is not dict
            or type(platform) is not dict
        ):
            raise TypeError()
        policy = LinuxConfinementPolicyV1(
            acceptance_contract_sha256=(
                identities["acceptance_contract_sha256"]
            ),
            adapter_seccomp_bpf_sha256=(
                identities["adapter_seccomp_bpf_sha256"]
            ),
            adapter_seccomp_feature_manifest_sha256=(
                identities["adapter_seccomp_feature_manifest_sha256"]
            ),
            architecture_id=platform["architecture_id"],
            backend_executable_sha256=(
                identities["backend_executable_sha256"]
            ),
            backend_feature_manifest_sha256=(
                identities["backend_feature_manifest_sha256"]
            ),
            backend_version_id=backend["backend_version_id"],
            bootstrap_source_sha256=(
                identities["bootstrap_source_sha256"]
            ),
            dependency_lock_sha256=(
                identities["dependency_lock_sha256"]
            ),
            hostile_test_inventory_sha256=(
                identities["hostile_test_inventory_sha256"]
            ),
            landlock_ruleset_sha256=(
                identities["landlock_ruleset_sha256"]
            ),
            launch_seccomp_bpf_sha256=(
                identities["launch_seccomp_bpf_sha256"]
            ),
            launch_seccomp_feature_manifest_sha256=(
                identities["launch_seccomp_feature_manifest_sha256"]
            ),
            linux_platform_profile_sha256=(
                identities["linux_platform_profile_sha256"]
            ),
            runtime_rootfs_image_sha256=(
                identities["runtime_rootfs_image_sha256"]
            ),
            runtime_rootfs_manifest_sha256=(
                identities["runtime_rootfs_manifest_sha256"]
            ),
            sandbox_interpreter_sha256=(
                identities["sandbox_interpreter_sha256"]
            ),
            supervisor_executable_sha256=(
                identities["supervisor_executable_sha256"]
            ),
            supervisor_dependency_closure_sha256=(
                identities["supervisor_dependency_closure_sha256"]
            ),
            supervisor_feature_manifest_sha256=(
                identities["supervisor_feature_manifest_sha256"]
            ),
            supervisor_source_sha256=(
                identities["supervisor_source_sha256"]
            ),
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        _fail(LinuxConfinementPolicyCode.SCHEMA_INVALID)
    if linux_confinement_policy_bytes(policy) != raw:
        _fail(LinuxConfinementPolicyCode.CANONICAL_MISMATCH)
    return policy


__all__ = [
    "LINUX_CONFINEMENT_ARCHITECTURE_IDS",
    "LINUX_CONFINEMENT_BACKEND_ID",
    "LINUX_CONFINEMENT_FALSE_CLAIM_IDS",
    "LINUX_CONFINEMENT_FD_ROLE_IDS",
    "LINUX_CONFINEMENT_FORBIDDEN_BWRAP_OPTIONS",
    "LINUX_CONFINEMENT_NAMESPACE_IDS",
    "LINUX_CONFINEMENT_POLICY_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_POLICY_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_POLICY_IMPLEMENTATION_STATUS",
    "LINUX_CONFINEMENT_TARGET_STATUS",
    "MAXIMUM_LINUX_CONFINEMENT_POLICY_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_RUN_NONCE_REGISTRY_ENTRIES",
    "LinuxConfinementPolicyCode",
    "LinuxConfinementPolicyError",
    "LinuxConfinementPolicyV1",
    "bubblewrap_launch_template_bytes",
    "bubblewrap_launch_template_sha256",
    "build_bubblewrap_launch_template",
    "linux_confinement_ready_frame",
    "linux_confinement_policy_bytes",
    "linux_confinement_policy_sha256",
    "linux_confinement_policy_tree",
    "materialize_bubblewrap_launch_argv",
    "parse_linux_confinement_policy",
]
