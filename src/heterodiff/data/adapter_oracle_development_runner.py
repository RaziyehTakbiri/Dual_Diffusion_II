"""Archive-selected, permanently nondecision oracle-worker execution.

This module closes one narrow development boundary.  It selects exact Python
source bytes from a strictly validated path-free archive, reconciles those
bytes with a raw oracle registry and a separately supplied canonical
membership receipt, reruns the static oracle-source policy, and passes the
selected ASCII source directly as a Python-style ``-c`` argument.  It
attempts to write one exact ABI request while concurrently capturing bounded
stdout and stderr; the success-like state requires complete input.  The
receipt binds intended interpreter bytes but does not attest that the
executable implements CPython or that the kernel executed those bytes.

The resulting receipt is a local, canonical execution record.  It is not an
attestation and can never be decision eligible.  The returned raw-byte
transport is privileged development material: bounded failure stderr may
contain worker-controlled diagnostics and must not cross a public diagnostic
boundary.  In particular, the standard-library backend does not seal the
interpreter actually executed, bind the working directory by descriptor,
confine filesystem or network access, prevent a descendant from escaping its
POSIX process group, enforce a memory ceiling, or authenticate the
caller-supplied registry/archive trust root.  Passing source in argv removes a
working-tree source-path race only.

This module does not directly call a publisher payload projection,
expected-output helper, case protocol, or gate implementation.  Its registry
validator comes from the publisher authority module, whose transitive import
graph may load publisher payload helpers, so no import-independence claim is
made.  A successful status means only that a complete zero-exit byte-stream
response matched the fixed ABI request identity, with empty stderr, under the
recorded development limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
import errno
import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
from types import MappingProxyType
from typing import Optional, Tuple

from .adapter_conformance_execution_guard import (
    WORKING_DIRECTORY_DIGEST_DOMAIN,
    argv_sha256,
    environment_sha256,
)
from .adapter_oracle_abi import (
    MAXIMUM_ORACLE_WORKER_FRAME_BYTES,
    OracleWorkerABICode,
    OracleWorkerABIError,
    ValidatedOracleWorkerResponseIdentityV1,
    parse_oracle_worker_request_frame,
    parse_oracle_worker_response_frame,
    validate_oracle_worker_response_identity,
)
from .adapter_oracle_source_policy import (
    MAXIMUM_ORACLE_POLICY_RECEIPT_BYTES,
    oracle_source_policy_receipt_sha256,
    validate_oracle_source_policy,
)
from .adapter_publication_authority import (
    validate_golden_oracle_registry,
)
from .adapter_publication_authority_types import (
    MAXIMUM_APPROVED_PROFILE_BYTES,
)
from .adapter_source_archive import (
    MAXIMUM_SOURCE_ARCHIVE_BYTES,
    MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES,
    SOURCE_ARCHIVE_ORACLE_ROLE_ID,
    SourceArchiveCode,
    SourceArchiveValidationError,
    resolve_source_archive_object,
    source_archive_membership_receipt_bytes,
    source_archive_membership_receipt_sha256,
)


DEVELOPMENT_ORACLE_RUN_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.development-archive-selected-oracle-run-receipt.v1"
)
DEVELOPMENT_ORACLE_RUN_RECEIPT_DIGEST_DOMAIN = (
    DEVELOPMENT_ORACLE_RUN_RECEIPT_ARTIFACT_TYPE
)
DEVELOPMENT_ORACLE_RUN_INPUT_DIGEST_DOMAIN = (
    "heterodiff.adapter.development-oracle-run-input.v1"
)
DEVELOPMENT_ORACLE_RUNNER_ID = (
    "heterodiff-development-archive-selected-oracle-runner-v1"
)
DEVELOPMENT_ORACLE_IMPLEMENTATION_STATUS = (
    "DEVELOPMENT_ONLY_ARCHIVE_SELECTED_ARGV_BOUND"
)

ORACLE_DEVELOPMENT_WALL_TIME_LIMIT_NANOSECONDS = 180 * 1_000_000_000
ORACLE_DEVELOPMENT_STDIN_LIMIT_BYTES = MAXIMUM_ORACLE_WORKER_FRAME_BYTES
ORACLE_DEVELOPMENT_STDOUT_LIMIT_BYTES = MAXIMUM_ORACLE_WORKER_FRAME_BYTES
ORACLE_DEVELOPMENT_STDERR_LIMIT_BYTES = 64 * 1024
ORACLE_DEVELOPMENT_AGGREGATE_OUTPUT_LIMIT_BYTES = (
    MAXIMUM_ORACLE_WORKER_FRAME_BYTES + 32 * 1024
)
MAXIMUM_ORACLE_DEVELOPMENT_SOURCE_ARGV_BYTES = 64 * 1024
MAXIMUM_ORACLE_DEVELOPMENT_INTERPRETER_BYTES = 64 * 1024 * 1024
MAXIMUM_ORACLE_DEVELOPMENT_PATH_BYTES = 4096
MAXIMUM_ORACLE_DEVELOPMENT_RECEIPT_BYTES = 64 * 1024
MAXIMUM_ORACLE_DEVELOPMENT_READ_CHUNK_BYTES = 64 * 1024
MAXIMUM_ORACLE_DEVELOPMENT_WRITE_CHUNK_BYTES = 64 * 1024

ORACLE_DEVELOPMENT_ARGV_MODE_ID = (
    "interpreter-isolated-no-site-no-bytecode-command-flags-v1"
)
ORACLE_DEVELOPMENT_SOURCE_LOAD_METHOD_ID = (
    "exact-archive-member-as-interpreter-command-argv-v1"
)
ORACLE_DEVELOPMENT_INTERPRETER_CAPTURE_METHOD_ID = (
    "retained-read-fd-pre-post-path-stat-not-exec-sealed-v1"
)
ORACLE_DEVELOPMENT_EXECUTION_BACKEND_ID = (
    "python-stdlib-posix-selector-subprocess-development-v1"
)
ORACLE_DEVELOPMENT_CWD_LAUNCH_METHOD_ID = (
    "path-cwd-pre-post-stat-unsealed-v1"
)
ORACLE_DEVELOPMENT_OUTPUT_CAPTURE_METHOD_ID = (
    "bounded-duplex-pipe-retained-prefix-sha256-v1"
)
ORACLE_DEVELOPMENT_PROCESS_CONTAINMENT_ID = (
    "posix-process-group-escapeable-v1"
)
ORACLE_DEVELOPMENT_PROCESS_CLEANUP_METHOD_ID = (
    "posix-process-group-term-kill-reap-observation-v1"
)
ORACLE_DEVELOPMENT_CLOCK_METHOD_ID = "system-monotonic-ns"
ORACLE_DEVELOPMENT_NOT_PROVIDED_ID = "not-provided"
ORACLE_DEVELOPMENT_CONTAINMENT_STATUS_ID = "absent"
ORACLE_DEVELOPMENT_SEMANTIC_STATUS_ID = "not-evaluated"
ORACLE_DEVELOPMENT_WORKER_REJECTION_BYTES = b"ORACLE_WORKER_REJECTED\n"

_RUN_INPUT_DOMAIN_BYTES = DEVELOPMENT_ORACLE_RUN_INPUT_DIGEST_DOMAIN.encode(
    "ascii"
)
_RECEIPT_DOMAIN_BYTES = (
    DEVELOPMENT_ORACLE_RUN_RECEIPT_DIGEST_DOMAIN.encode("ascii")
)
_INTERPRETER_OBSERVATION_DOMAIN = (
    b"heterodiff.adapter.development-interpreter-observation.v1"
)
_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1
_IO_POLL_INTERVAL_SECONDS = 0.01
_TERMINATION_GRACE_SECONDS = 0.25
_TERMINATION_FINAL_SECONDS = 2.0


class DevelopmentOracleRunStatus(str, Enum):
    """Closed terminal states; no state is a publication ``PASS``."""

    COMPLETED_RESPONSE_IDENTITY_MATCHED = (
        "completed_response_identity_matched"
    )
    WORKER_REJECTED = "worker_rejected"
    STDIN_INCOMPLETE = "stdin_incomplete"
    WALL_TIME_LIMIT_EXCEEDED = "wall_time_limit_exceeded"
    STDOUT_LIMIT_EXCEEDED = "stdout_limit_exceeded"
    STDERR_LIMIT_EXCEEDED = "stderr_limit_exceeded"
    AGGREGATE_OUTPUT_LIMIT_EXCEEDED = (
        "aggregate_output_limit_exceeded"
    )
    SIGNALLED = "signalled"
    NONZERO_EXIT = "nonzero_exit"
    STDERR_NONEMPTY = "stderr_nonempty"
    # Defensive/future backend state.  The POSIX selector backend normally
    # drains both streams or records an earlier forced-stop condition.
    OUTPUT_INCOMPLETE = "output_incomplete"
    RESPONSE_FRAME_INVALID = "response_frame_invalid"
    RESPONSE_IDENTITY_MISMATCH = "response_identity_mismatch"
    PROCESS_GROUP_CLEANUP_REQUIRED = (
        "process_group_cleanup_required_after_child_exit"
    )


class DevelopmentOracleResponseIdentityStatus(str, Enum):
    NOT_AVAILABLE = "not_available"
    FRAME_INVALID = "frame_invalid"
    IDENTITY_MISMATCH = "identity_mismatch"
    MATCHED = "matched"


class DevelopmentOracleOutputLimitKind(str, Enum):
    NONE = "none"
    STDOUT = "stdout"
    STDERR = "stderr"
    AGGREGATE = "aggregate"


class DevelopmentOracleRunCode(str, Enum):
    """Receipt-blocking, interpolation-free failures."""

    INPUT_TYPE = "DEV_ORACLE_INPUT_TYPE"
    INPUT_RESOURCE = "DEV_ORACLE_INPUT_RESOURCE"
    REGISTRY_INVALID = "DEV_ORACLE_REGISTRY_INVALID"
    ARCHIVE_INVALID = "DEV_ORACLE_ARCHIVE_INVALID"
    SOURCE_SELECTION_INVALID = "DEV_ORACLE_SOURCE_SELECTION_INVALID"
    MEMBERSHIP_MISMATCH = "DEV_ORACLE_MEMBERSHIP_MISMATCH"
    SOURCE_POLICY_REJECTED = "DEV_ORACLE_SOURCE_POLICY_REJECTED"
    REQUEST_INVALID = "DEV_ORACLE_REQUEST_INVALID"
    REQUEST_SOURCE_MISMATCH = "DEV_ORACLE_REQUEST_SOURCE_MISMATCH"
    INTERPRETER_CAPTURE_FAILED = "DEV_ORACLE_INTERPRETER_CAPTURE_FAILED"
    INTERPRETER_IDENTITY_MISMATCH = (
        "DEV_ORACLE_INTERPRETER_IDENTITY_MISMATCH"
    )
    WORKING_DIRECTORY_INVALID = "DEV_ORACLE_WORKING_DIRECTORY_INVALID"
    PLATFORM_UNAVAILABLE = "DEV_ORACLE_PLATFORM_UNAVAILABLE"
    SPAWN_FAILED = "DEV_ORACLE_SPAWN_FAILED"
    CLOCK_INVALID = "DEV_ORACLE_CLOCK_INVALID"
    PROCESS_PROTOCOL_INVALID = "DEV_ORACLE_PROCESS_PROTOCOL_INVALID"
    TERMINATION_FAILED = "DEV_ORACLE_TERMINATION_FAILED"
    REAP_FAILED = "DEV_ORACLE_REAP_FAILED"
    CLOSE_FAILED = "DEV_ORACLE_CLOSE_FAILED"
    CANONICALIZATION_FAILED = "DEV_ORACLE_CANONICALIZATION_FAILED"
    RECEIPT_INVALID = "DEV_ORACLE_RECEIPT_INVALID"


_ERROR_MESSAGES = MappingProxyType(
    {
        DevelopmentOracleRunCode.INPUT_TYPE: (
            "development oracle input has an invalid exact type"
        ),
        DevelopmentOracleRunCode.INPUT_RESOURCE: (
            "development oracle input exceeds a fixed resource ceiling"
        ),
        DevelopmentOracleRunCode.REGISTRY_INVALID: (
            "development oracle registry is invalid"
        ),
        DevelopmentOracleRunCode.ARCHIVE_INVALID: (
            "development oracle source archive is invalid"
        ),
        DevelopmentOracleRunCode.SOURCE_SELECTION_INVALID: (
            "development oracle source selection is invalid"
        ),
        DevelopmentOracleRunCode.MEMBERSHIP_MISMATCH: (
            "development oracle source membership differs"
        ),
        DevelopmentOracleRunCode.SOURCE_POLICY_REJECTED: (
            "development oracle source policy rejected the selected source"
        ),
        DevelopmentOracleRunCode.REQUEST_INVALID: (
            "development oracle request frame is invalid"
        ),
        DevelopmentOracleRunCode.REQUEST_SOURCE_MISMATCH: (
            "development oracle request source identity differs"
        ),
        DevelopmentOracleRunCode.INTERPRETER_CAPTURE_FAILED: (
            "development interpreter identity could not be captured"
        ),
        DevelopmentOracleRunCode.INTERPRETER_IDENTITY_MISMATCH: (
            "development interpreter identity differs"
        ),
        DevelopmentOracleRunCode.WORKING_DIRECTORY_INVALID: (
            "development working directory is invalid"
        ),
        DevelopmentOracleRunCode.PLATFORM_UNAVAILABLE: (
            "development oracle execution platform is unavailable"
        ),
        DevelopmentOracleRunCode.SPAWN_FAILED: (
            "development oracle worker could not be started"
        ),
        DevelopmentOracleRunCode.CLOCK_INVALID: (
            "development oracle monotonic clock is invalid"
        ),
        DevelopmentOracleRunCode.PROCESS_PROTOCOL_INVALID: (
            "development oracle process protocol is invalid"
        ),
        DevelopmentOracleRunCode.TERMINATION_FAILED: (
            "development oracle process group could not be terminated"
        ),
        DevelopmentOracleRunCode.REAP_FAILED: (
            "development oracle direct child could not be reaped"
        ),
        DevelopmentOracleRunCode.CLOSE_FAILED: (
            "development oracle process streams could not be closed"
        ),
        DevelopmentOracleRunCode.CANONICALIZATION_FAILED: (
            "development oracle receipt could not be canonicalized"
        ),
        DevelopmentOracleRunCode.RECEIPT_INVALID: (
            "development oracle receipt is invalid"
        ),
    }
)


class DevelopmentOracleRunError(RuntimeError):
    """One fixed runner failure without attacker-controlled diagnostics."""

    def __init__(self, code: DevelopmentOracleRunCode) -> None:
        if type(code) is not DevelopmentOracleRunCode:
            raise TypeError("development oracle error code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: DevelopmentOracleRunCode) -> None:
    raise DevelopmentOracleRunError(code) from None


def _exact_bytes(
    value: object,
    *,
    maximum: int,
    allow_empty: bool = False,
) -> bytes:
    if type(value) is not bytes:
        _fail(DevelopmentOracleRunCode.INPUT_TYPE)
    if (not value and not allow_empty) or len(value) > maximum:
        _fail(DevelopmentOracleRunCode.INPUT_RESOURCE)
    return value


def _sha256(value: object) -> str:
    if type(value) is not str:
        raise TypeError("SHA-256 value must be an exact string")
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError("SHA-256 value must be lowercase hexadecimal")
    return value


def _token(value: object) -> str:
    if type(value) is not str:
        raise TypeError("token must be an exact string")
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        raise ValueError("token must contain only ASCII") from None
    if (
        not encoded
        or len(encoded) > 128
        or _TOKEN_RE.fullmatch(value) is None
    ):
        raise ValueError("token is invalid")
    return value


def _nonnegative_integer(value: object, *, name: str) -> int:
    if (
        type(value) is not int
        or value < 0
        or value > _MAXIMUM_SAFE_INTEGER
    ):
        raise TypeError(name + " must be an exact bounded integer")
    return value


def _positive_integer(value: object, *, name: str) -> int:
    result = _nonnegative_integer(value, name=name)
    if result == 0:
        raise ValueError(name + " must be positive")
    return result


def _path_text(value: object) -> str:
    if type(value) is not str or not value or "\x00" in value:
        _fail(DevelopmentOracleRunCode.INPUT_TYPE)
    try:
        encoded = value.encode("utf-8", "strict")
    except UnicodeError:
        _fail(DevelopmentOracleRunCode.INPUT_TYPE)
    if len(encoded) > MAXIMUM_ORACLE_DEVELOPMENT_PATH_BYTES:
        _fail(DevelopmentOracleRunCode.INPUT_RESOURCE)
    if not os.path.isabs(value) or os.path.normpath(value) != value:
        _fail(DevelopmentOracleRunCode.INPUT_TYPE)
    return value


def _length_framed_sha256(
    domain: bytes,
    values: Tuple[bytes, ...],
) -> str:
    digest = hashlib.sha256()
    digest.update(len(domain).to_bytes(8, "big"))
    digest.update(domain)
    digest.update(len(values).to_bytes(8, "big"))
    for value in values:
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    return digest.hexdigest()


@dataclass(frozen=True)
class DevelopmentOracleRunInputV1:
    """Raw, pre-execution inputs; no selected source object is accepted."""

    oracle_registry_bytes: bytes
    source_archive_inventory_bytes: bytes
    source_archive_bytes: bytes
    source_archive_membership_receipt_bytes: bytes
    request_frame_bytes: bytes
    interpreter_executable_bytes: bytes
    interpreter_path: str
    working_directory: str

    def __post_init__(self) -> None:
        if type(self) is not DevelopmentOracleRunInputV1:
            raise TypeError("development oracle input must be exact")
        _exact_bytes(
            self.oracle_registry_bytes,
            maximum=MAXIMUM_APPROVED_PROFILE_BYTES,
        )
        _exact_bytes(
            self.source_archive_inventory_bytes,
            maximum=MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES,
        )
        _exact_bytes(
            self.source_archive_bytes,
            maximum=MAXIMUM_SOURCE_ARCHIVE_BYTES,
        )
        _exact_bytes(
            self.source_archive_membership_receipt_bytes,
            maximum=MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES,
        )
        _exact_bytes(
            self.request_frame_bytes,
            maximum=ORACLE_DEVELOPMENT_STDIN_LIMIT_BYTES,
        )
        _exact_bytes(
            self.interpreter_executable_bytes,
            maximum=MAXIMUM_ORACLE_DEVELOPMENT_INTERPRETER_BYTES,
        )
        _path_text(self.interpreter_path)
        _path_text(self.working_directory)


def _snapshot_input(value: object) -> DevelopmentOracleRunInputV1:
    if type(value) is not DevelopmentOracleRunInputV1:
        _fail(DevelopmentOracleRunCode.INPUT_TYPE)
    try:
        DevelopmentOracleRunInputV1.__post_init__(value)
        return DevelopmentOracleRunInputV1(
            oracle_registry_bytes=value.oracle_registry_bytes,
            source_archive_inventory_bytes=(
                value.source_archive_inventory_bytes
            ),
            source_archive_bytes=value.source_archive_bytes,
            source_archive_membership_receipt_bytes=(
                value.source_archive_membership_receipt_bytes
            ),
            request_frame_bytes=value.request_frame_bytes,
            interpreter_executable_bytes=value.interpreter_executable_bytes,
            interpreter_path=value.interpreter_path,
            working_directory=value.working_directory,
        )
    except DevelopmentOracleRunError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(DevelopmentOracleRunCode.INPUT_TYPE)


@dataclass(frozen=True)
class DevelopmentArchiveSelectedOracleRunReceiptV1:
    """Canonical local record; structural validity is not attestation."""

    run_input_sha256: str
    oracle_id: str
    oracle_registry_byte_count: int
    oracle_registry_sha256: str
    source_archive_inventory_byte_count: int
    source_archive_inventory_sha256: str
    source_archive_byte_count: int
    source_archive_sha256: str
    source_archive_membership_receipt_byte_count: int
    source_archive_membership_receipt_sha256: str
    source_object_id: str
    selected_source_byte_count: int
    selected_source_sha256: str
    source_policy_receipt_byte_count: int
    source_policy_receipt_sha256: str
    captured_interpreter_executable_byte_count: int
    captured_interpreter_executable_sha256: str
    interpreter_observation_sha256: str
    argv_sha256: str
    environment_sha256: str
    working_directory_sha256: str
    request_frame_byte_count: int
    request_frame_sha256: str
    stdin_written_size_bytes: int
    stdin_written_sha256: str
    stdin_complete: bool
    response_frame_byte_count: Optional[int]
    response_frame_sha256: Optional[str]
    response_identity_status_id: DevelopmentOracleResponseIdentityStatus
    stdout_size_bytes: int
    stdout_sha256: str
    stdout_complete: bool
    stderr_size_bytes: int
    stderr_sha256: str
    stderr_complete: bool
    exit_status: Optional[int]
    terminating_signal: Optional[int]
    elapsed_monotonic_nanoseconds: int
    output_limit_kind_id: DevelopmentOracleOutputLimitKind
    wall_limit_triggered: bool
    process_group_cleanup_triggered: bool
    process_group_nonquiescence_triggered: bool
    managed_process_group_observed_quiescent: bool
    status_id: DevelopmentOracleRunStatus
    artifact_type: str = field(
        default=DEVELOPMENT_ORACLE_RUN_RECEIPT_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)
    runner_id: str = field(
        default=DEVELOPMENT_ORACLE_RUNNER_ID,
        init=False,
    )
    implementation_status_id: str = field(
        default=DEVELOPMENT_ORACLE_IMPLEMENTATION_STATUS,
        init=False,
    )
    decision_eligible: bool = field(default=False, init=False)
    execution_attested: bool = field(default=False, init=False)
    containment_status_id: str = field(
        default=ORACLE_DEVELOPMENT_CONTAINMENT_STATUS_ID,
        init=False,
    )
    containment_attestation_sha256: None = field(default=None, init=False)
    source_role_id: str = field(
        default=SOURCE_ARCHIVE_ORACLE_ROLE_ID,
        init=False,
    )
    source_load_method_id: str = field(
        default=ORACLE_DEVELOPMENT_SOURCE_LOAD_METHOD_ID,
        init=False,
    )
    argv_mode_id: str = field(
        default=ORACLE_DEVELOPMENT_ARGV_MODE_ID,
        init=False,
    )
    interpreter_capture_method_id: str = field(
        default=ORACLE_DEVELOPMENT_INTERPRETER_CAPTURE_METHOD_ID,
        init=False,
    )
    interpreter_execution_identity_attested: bool = field(
        default=False,
        init=False,
    )
    execution_backend_id: str = field(
        default=ORACLE_DEVELOPMENT_EXECUTION_BACKEND_ID,
        init=False,
    )
    cwd_launch_method_id: str = field(
        default=ORACLE_DEVELOPMENT_CWD_LAUNCH_METHOD_ID,
        init=False,
    )
    output_capture_method_id: str = field(
        default=ORACLE_DEVELOPMENT_OUTPUT_CAPTURE_METHOD_ID,
        init=False,
    )
    semantic_validation_status_id: str = field(
        default=ORACLE_DEVELOPMENT_SEMANTIC_STATUS_ID,
        init=False,
    )
    clock_method_id: str = field(
        default=ORACLE_DEVELOPMENT_CLOCK_METHOD_ID,
        init=False,
    )
    direct_child_reaped: bool = field(default=True, init=False)
    stdin_limit_bytes: int = field(
        default=ORACLE_DEVELOPMENT_STDIN_LIMIT_BYTES,
        init=False,
    )
    stdout_limit_bytes: int = field(
        default=ORACLE_DEVELOPMENT_STDOUT_LIMIT_BYTES,
        init=False,
    )
    stderr_limit_bytes: int = field(
        default=ORACLE_DEVELOPMENT_STDERR_LIMIT_BYTES,
        init=False,
    )
    aggregate_output_limit_bytes: int = field(
        default=ORACLE_DEVELOPMENT_AGGREGATE_OUTPUT_LIMIT_BYTES,
        init=False,
    )
    wall_time_limit_nanoseconds: int = field(
        default=ORACLE_DEVELOPMENT_WALL_TIME_LIMIT_NANOSECONDS,
        init=False,
    )
    address_space_limit_bytes: None = field(default=None, init=False)
    address_space_limit_method_id: str = field(
        default=ORACLE_DEVELOPMENT_NOT_PROVIDED_ID,
        init=False,
    )
    peak_rss_limit_bytes: None = field(default=None, init=False)
    measured_peak_rss_bytes: None = field(default=None, init=False)
    peak_rss_method_id: str = field(
        default=ORACLE_DEVELOPMENT_NOT_PROVIDED_ID,
        init=False,
    )
    peak_rss_enforcement_exact: bool = field(default=False, init=False)
    filesystem_confinement_id: str = field(
        default=ORACLE_DEVELOPMENT_NOT_PROVIDED_ID,
        init=False,
    )
    network_confinement_id: str = field(
        default=ORACLE_DEVELOPMENT_NOT_PROVIDED_ID,
        init=False,
    )
    process_containment_id: str = field(
        default=ORACLE_DEVELOPMENT_PROCESS_CONTAINMENT_ID,
        init=False,
    )
    process_cleanup_method_id: str = field(
        default=ORACLE_DEVELOPMENT_PROCESS_CLEANUP_METHOD_ID,
        init=False,
    )
    process_tree_escape_prevented: bool = field(default=False, init=False)
    process_tree_quiescence_attested: bool = field(default=False, init=False)
    filesystem_read_scope_attested: bool = field(default=False, init=False)
    filesystem_write_scope_attested: bool = field(default=False, init=False)
    network_denial_attested: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if type(self) is not DevelopmentArchiveSelectedOracleRunReceiptV1:
            raise TypeError("development oracle receipt must be exact")
        _validate_receipt_fields(self)


def _validate_receipt_fields(
    value: DevelopmentArchiveSelectedOracleRunReceiptV1,
) -> None:
    for name in (
        "run_input_sha256",
        "oracle_registry_sha256",
        "source_archive_inventory_sha256",
        "source_archive_sha256",
        "source_archive_membership_receipt_sha256",
        "selected_source_sha256",
        "source_policy_receipt_sha256",
        "captured_interpreter_executable_sha256",
        "interpreter_observation_sha256",
        "argv_sha256",
        "environment_sha256",
        "working_directory_sha256",
        "request_frame_sha256",
        "stdin_written_sha256",
        "stdout_sha256",
        "stderr_sha256",
    ):
        _sha256(getattr(value, name))
    if value.response_frame_sha256 is not None:
        _sha256(value.response_frame_sha256)
    _token(value.oracle_id)
    _token(value.source_object_id)
    for name in (
        "oracle_registry_byte_count",
        "source_archive_inventory_byte_count",
        "source_archive_byte_count",
        "source_archive_membership_receipt_byte_count",
        "selected_source_byte_count",
        "source_policy_receipt_byte_count",
        "captured_interpreter_executable_byte_count",
        "request_frame_byte_count",
    ):
        _positive_integer(getattr(value, name), name=name)
    for name in (
        "stdin_written_size_bytes",
        "stdout_size_bytes",
        "stderr_size_bytes",
        "elapsed_monotonic_nanoseconds",
    ):
        _nonnegative_integer(getattr(value, name), name=name)
    if value.response_frame_byte_count is not None:
        _nonnegative_integer(
            value.response_frame_byte_count,
            name="response_frame_byte_count",
        )
        if value.response_frame_byte_count == 0:
            raise ValueError("response frame commitment must be nonempty")
    for name in ("exit_status", "terminating_signal"):
        item = getattr(value, name)
        if item is not None:
            _nonnegative_integer(item, name=name)
    if value.terminating_signal == 0:
        raise ValueError("terminating signal must be positive")
    if value.exit_status is not None and value.terminating_signal is not None:
        raise ValueError("exit status and signal are mutually exclusive")
    if value.exit_status is None and value.terminating_signal is None:
        raise ValueError("terminal receipt lacks exit or signal state")
    if value.exit_status is not None and value.exit_status > 255:
        raise ValueError("exit status exceeds its platform range")
    if (
        value.terminating_signal is not None
        and value.terminating_signal >= signal.NSIG
    ):
        raise ValueError("terminating signal exceeds its platform range")
    if type(value.response_identity_status_id) is not (
        DevelopmentOracleResponseIdentityStatus
    ):
        raise TypeError("response identity status must be exact")
    if type(value.output_limit_kind_id) is not DevelopmentOracleOutputLimitKind:
        raise TypeError("output limit kind must be exact")
    if type(value.status_id) is not DevelopmentOracleRunStatus:
        raise TypeError("run status must be exact")
    for name in (
        "stdin_complete",
        "stdout_complete",
        "stderr_complete",
        "wall_limit_triggered",
        "process_group_cleanup_triggered",
        "process_group_nonquiescence_triggered",
        "managed_process_group_observed_quiescent",
    ):
        if type(getattr(value, name)) is not bool:
            raise TypeError(name + " must be an exact bool")
    fixed_values = {
        "artifact_type": DEVELOPMENT_ORACLE_RUN_RECEIPT_ARTIFACT_TYPE,
        "format_version": "1",
        "runner_id": DEVELOPMENT_ORACLE_RUNNER_ID,
        "implementation_status_id": (
            DEVELOPMENT_ORACLE_IMPLEMENTATION_STATUS
        ),
        "containment_status_id": (
            ORACLE_DEVELOPMENT_CONTAINMENT_STATUS_ID
        ),
        "source_role_id": SOURCE_ARCHIVE_ORACLE_ROLE_ID,
        "source_load_method_id": (
            ORACLE_DEVELOPMENT_SOURCE_LOAD_METHOD_ID
        ),
        "argv_mode_id": ORACLE_DEVELOPMENT_ARGV_MODE_ID,
        "interpreter_capture_method_id": (
            ORACLE_DEVELOPMENT_INTERPRETER_CAPTURE_METHOD_ID
        ),
        "execution_backend_id": ORACLE_DEVELOPMENT_EXECUTION_BACKEND_ID,
        "cwd_launch_method_id": ORACLE_DEVELOPMENT_CWD_LAUNCH_METHOD_ID,
        "output_capture_method_id": (
            ORACLE_DEVELOPMENT_OUTPUT_CAPTURE_METHOD_ID
        ),
        "semantic_validation_status_id": (
            ORACLE_DEVELOPMENT_SEMANTIC_STATUS_ID
        ),
        "clock_method_id": ORACLE_DEVELOPMENT_CLOCK_METHOD_ID,
        "stdin_limit_bytes": ORACLE_DEVELOPMENT_STDIN_LIMIT_BYTES,
        "stdout_limit_bytes": ORACLE_DEVELOPMENT_STDOUT_LIMIT_BYTES,
        "stderr_limit_bytes": ORACLE_DEVELOPMENT_STDERR_LIMIT_BYTES,
        "aggregate_output_limit_bytes": (
            ORACLE_DEVELOPMENT_AGGREGATE_OUTPUT_LIMIT_BYTES
        ),
        "wall_time_limit_nanoseconds": (
            ORACLE_DEVELOPMENT_WALL_TIME_LIMIT_NANOSECONDS
        ),
        "address_space_limit_method_id": (
            ORACLE_DEVELOPMENT_NOT_PROVIDED_ID
        ),
        "peak_rss_method_id": ORACLE_DEVELOPMENT_NOT_PROVIDED_ID,
        "filesystem_confinement_id": ORACLE_DEVELOPMENT_NOT_PROVIDED_ID,
        "network_confinement_id": ORACLE_DEVELOPMENT_NOT_PROVIDED_ID,
        "process_containment_id": (
            ORACLE_DEVELOPMENT_PROCESS_CONTAINMENT_ID
        ),
        "process_cleanup_method_id": (
            ORACLE_DEVELOPMENT_PROCESS_CLEANUP_METHOD_ID
        ),
    }
    for name, expected in fixed_values.items():
        observed = getattr(value, name)
        if type(observed) is not type(expected) or observed != expected:
            raise ValueError("development oracle receipt fixed value differs")
    fixed_false = (
        "decision_eligible",
        "execution_attested",
        "interpreter_execution_identity_attested",
        "peak_rss_enforcement_exact",
        "process_tree_escape_prevented",
        "process_tree_quiescence_attested",
        "filesystem_read_scope_attested",
        "filesystem_write_scope_attested",
        "network_denial_attested",
    )
    if any(getattr(value, name) is not False for name in fixed_false):
        raise ValueError("development oracle receipt attestation is not fixed")
    if (
        value.containment_attestation_sha256 is not None
        or value.address_space_limit_bytes is not None
        or value.peak_rss_limit_bytes is not None
        or value.measured_peak_rss_bytes is not None
        or value.direct_child_reaped is not True
        or not value.managed_process_group_observed_quiescent
    ):
        raise ValueError("development oracle unavailable fields differ")
    if value.source_object_id != value.oracle_id:
        raise ValueError("source object and oracle identifiers differ")
    bounded_counts = (
        (
            value.oracle_registry_byte_count,
            MAXIMUM_APPROVED_PROFILE_BYTES,
        ),
        (
            value.source_archive_inventory_byte_count,
            MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES,
        ),
        (
            value.source_archive_byte_count,
            MAXIMUM_SOURCE_ARCHIVE_BYTES,
        ),
        (
            value.source_archive_membership_receipt_byte_count,
            MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES,
        ),
        (
            value.selected_source_byte_count,
            MAXIMUM_ORACLE_DEVELOPMENT_SOURCE_ARGV_BYTES,
        ),
        (
            value.source_policy_receipt_byte_count,
            MAXIMUM_ORACLE_POLICY_RECEIPT_BYTES,
        ),
        (
            value.captured_interpreter_executable_byte_count,
            MAXIMUM_ORACLE_DEVELOPMENT_INTERPRETER_BYTES,
        ),
        (
            value.request_frame_byte_count,
            ORACLE_DEVELOPMENT_STDIN_LIMIT_BYTES,
        ),
    )
    if any(observed > maximum for observed, maximum in bounded_counts):
        raise ValueError("development receipt byte count exceeds its ceiling")
    if value.stdin_written_size_bytes > value.request_frame_byte_count:
        raise ValueError("written stdin exceeds the request")
    if value.stdin_complete and (
        value.stdin_written_size_bytes != value.request_frame_byte_count
        or value.stdin_written_sha256 != value.request_frame_sha256
    ):
        raise ValueError("complete stdin differs from the request")
    if (
        not value.stdin_complete
        and value.stdin_written_size_bytes >= value.request_frame_byte_count
    ):
        raise ValueError("incomplete stdin is not a strict request prefix")
    if value.stdout_size_bytes > value.stdout_limit_bytes:
        raise ValueError("captured stdout exceeds its ceiling")
    if value.stderr_size_bytes > value.stderr_limit_bytes:
        raise ValueError("captured stderr exceeds its ceiling")
    if (
        value.stdout_size_bytes + value.stderr_size_bytes
        > value.aggregate_output_limit_bytes
    ):
        raise ValueError("captured aggregate output exceeds its ceiling")
    response_present = value.response_frame_byte_count is not None
    if response_present != (value.response_frame_sha256 is not None):
        raise ValueError("response frame commitment is incomplete")
    if response_present and (
        value.response_frame_byte_count != value.stdout_size_bytes
        or value.response_frame_sha256 != value.stdout_sha256
    ):
        raise ValueError("response frame and stdout commitments differ")
    if (
        value.response_identity_status_id
        is DevelopmentOracleResponseIdentityStatus.MATCHED
        and (not response_present or not value.stdout_complete)
    ):
        raise ValueError("matched response requires a frame commitment")
    if (
        value.response_identity_status_id
        is DevelopmentOracleResponseIdentityStatus.IDENTITY_MISMATCH
        and (not response_present or not value.stdout_complete)
    ):
        raise ValueError("identity mismatch requires a parsed frame")
    if (
        value.response_identity_status_id
        is DevelopmentOracleResponseIdentityStatus.FRAME_INVALID
        and (
            response_present
            or not value.stdout_complete
            or value.stdout_size_bytes == 0
        )
    ):
        raise ValueError("invalid frame status is inconsistent")
    if (
        value.response_identity_status_id
        is DevelopmentOracleResponseIdentityStatus.NOT_AVAILABLE
        and (
            response_present
            or (value.stdout_complete and value.stdout_size_bytes != 0)
        )
    ):
        raise ValueError("unavailable response status is inconsistent")
    if value.output_limit_kind_id is DevelopmentOracleOutputLimitKind.NONE:
        if value.status_id in (
            DevelopmentOracleRunStatus.STDOUT_LIMIT_EXCEEDED,
            DevelopmentOracleRunStatus.STDERR_LIMIT_EXCEEDED,
            DevelopmentOracleRunStatus.AGGREGATE_OUTPUT_LIMIT_EXCEEDED,
        ):
            raise ValueError("output-limit status lacks a trigger")
    expected_limit_status = {
        DevelopmentOracleOutputLimitKind.STDOUT: (
            DevelopmentOracleRunStatus.STDOUT_LIMIT_EXCEEDED
        ),
        DevelopmentOracleOutputLimitKind.STDERR: (
            DevelopmentOracleRunStatus.STDERR_LIMIT_EXCEEDED
        ),
        DevelopmentOracleOutputLimitKind.AGGREGATE: (
            DevelopmentOracleRunStatus.AGGREGATE_OUTPUT_LIMIT_EXCEEDED
        ),
    }.get(value.output_limit_kind_id)
    if (
        expected_limit_status is not None
        and value.status_id
        not in (
            DevelopmentOracleRunStatus.WALL_TIME_LIMIT_EXCEEDED,
            expected_limit_status,
        )
    ):
        raise ValueError("output-limit trigger and status differ")
    if value.output_limit_kind_id is DevelopmentOracleOutputLimitKind.STDOUT:
        if (
            value.stdout_size_bytes != value.stdout_limit_bytes
            or value.stdout_complete
        ):
            raise ValueError("stdout-limit receipt is inconsistent")
    if value.output_limit_kind_id is DevelopmentOracleOutputLimitKind.STDERR:
        if (
            value.stderr_size_bytes != value.stderr_limit_bytes
            or value.stderr_complete
        ):
            raise ValueError("stderr-limit receipt is inconsistent")
    if (
        value.output_limit_kind_id
        is DevelopmentOracleOutputLimitKind.AGGREGATE
        and (
            value.stdout_size_bytes + value.stderr_size_bytes
            != value.aggregate_output_limit_bytes
            or (value.stdout_complete and value.stderr_complete)
        )
    ):
        raise ValueError("aggregate-limit receipt is inconsistent")
    if value.wall_limit_triggered != (
        value.status_id is DevelopmentOracleRunStatus.WALL_TIME_LIMIT_EXCEEDED
    ):
        raise ValueError("wall-limit trigger and status differ")
    if (
        value.wall_limit_triggered
        and value.elapsed_monotonic_nanoseconds
        < value.wall_time_limit_nanoseconds
    ):
        raise ValueError("wall-limit elapsed time is inconsistent")
    if (
        value.status_id
        is DevelopmentOracleRunStatus.PROCESS_GROUP_CLEANUP_REQUIRED
        and not value.process_group_nonquiescence_triggered
    ):
        raise ValueError("process-group status lacks its trigger")
    if value.process_group_nonquiescence_triggered and (
        not value.process_group_cleanup_triggered
        or value.status_id
        not in (
            DevelopmentOracleRunStatus.WALL_TIME_LIMIT_EXCEEDED,
            DevelopmentOracleRunStatus.STDOUT_LIMIT_EXCEEDED,
            DevelopmentOracleRunStatus.STDERR_LIMIT_EXCEEDED,
            DevelopmentOracleRunStatus.AGGREGATE_OUTPUT_LIMIT_EXCEEDED,
            DevelopmentOracleRunStatus.WORKER_REJECTED,
            DevelopmentOracleRunStatus.STDIN_INCOMPLETE,
            DevelopmentOracleRunStatus.PROCESS_GROUP_CLEANUP_REQUIRED,
        )
    ):
        raise ValueError("process-group trigger and status differ")
    if value.process_group_cleanup_triggered and value.status_id not in (
        DevelopmentOracleRunStatus.WALL_TIME_LIMIT_EXCEEDED,
        DevelopmentOracleRunStatus.STDOUT_LIMIT_EXCEEDED,
        DevelopmentOracleRunStatus.STDERR_LIMIT_EXCEEDED,
        DevelopmentOracleRunStatus.AGGREGATE_OUTPUT_LIMIT_EXCEEDED,
        DevelopmentOracleRunStatus.WORKER_REJECTED,
        DevelopmentOracleRunStatus.STDIN_INCOMPLETE,
        DevelopmentOracleRunStatus.PROCESS_GROUP_CLEANUP_REQUIRED,
    ):
        raise ValueError("forced cleanup and status differ")
    if value.status_id is DevelopmentOracleRunStatus.SIGNALLED:
        if value.terminating_signal is None:
            raise ValueError("signalled status requires a signal")
    if value.status_id is DevelopmentOracleRunStatus.NONZERO_EXIT:
        if value.exit_status is None or value.exit_status == 0:
            raise ValueError("nonzero status requires an exit code")
    if value.status_id is DevelopmentOracleRunStatus.WORKER_REJECTED:
        if (
            value.exit_status != 64
            or value.stderr_size_bytes
            != len(ORACLE_DEVELOPMENT_WORKER_REJECTION_BYTES)
            or value.stderr_sha256
            != hashlib.sha256(
                ORACLE_DEVELOPMENT_WORKER_REJECTION_BYTES
            ).hexdigest()
        ):
            raise ValueError("worker rejection requires exit status 64")
    if value.status_id is DevelopmentOracleRunStatus.STDIN_INCOMPLETE:
        if value.stdin_complete:
            raise ValueError("stdin-incomplete status is inconsistent")
    if value.status_id is DevelopmentOracleRunStatus.OUTPUT_INCOMPLETE:
        if value.stdout_complete and value.stderr_complete:
            raise ValueError("output-incomplete status is inconsistent")
    if value.status_id is DevelopmentOracleRunStatus.STDERR_NONEMPTY:
        if value.stderr_size_bytes == 0:
            raise ValueError("stderr-nonempty status is inconsistent")
    if value.status_id is DevelopmentOracleRunStatus.RESPONSE_FRAME_INVALID:
        if value.response_identity_status_id not in (
            DevelopmentOracleResponseIdentityStatus.NOT_AVAILABLE,
            DevelopmentOracleResponseIdentityStatus.FRAME_INVALID,
        ):
            raise ValueError("response-frame-invalid status is inconsistent")
    if (
        value.status_id
        is DevelopmentOracleRunStatus.RESPONSE_IDENTITY_MISMATCH
        and value.response_identity_status_id
        is not DevelopmentOracleResponseIdentityStatus.IDENTITY_MISMATCH
    ):
        raise ValueError("response-identity status is inconsistent")
    structural_stderr = b""
    if value.stderr_size_bytes:
        rejection_sha256 = hashlib.sha256(
            ORACLE_DEVELOPMENT_WORKER_REJECTION_BYTES
        ).hexdigest()
        if (
            value.stderr_size_bytes
            == len(ORACLE_DEVELOPMENT_WORKER_REJECTION_BYTES)
            and value.stderr_sha256 == rejection_sha256
        ):
            structural_stderr = ORACLE_DEVELOPMENT_WORKER_REJECTION_BYTES
        else:
            structural_stderr = b"x"
    structural_observation = _ProcessObservation(
        returncode=(
            value.exit_status
            if value.exit_status is not None
            else -value.terminating_signal
        ),
        elapsed_nanoseconds=value.elapsed_monotonic_nanoseconds,
        stdin_written_bytes=b"",
        stdin_complete=value.stdin_complete,
        stdout_bytes=(b"x" if value.stdout_size_bytes else b""),
        stdout_complete=value.stdout_complete,
        stderr_bytes=structural_stderr,
        stderr_complete=value.stderr_complete,
        output_limit_kind=value.output_limit_kind_id,
        wall_limit_triggered=value.wall_limit_triggered,
        process_group_cleanup_triggered=(
            value.process_group_cleanup_triggered
        ),
        process_group_nonquiescence_triggered=(
            value.process_group_nonquiescence_triggered
        ),
        process_group_quiescent=(
            value.managed_process_group_observed_quiescent
        ),
    )
    if _terminal_status(
        structural_observation,
        value.response_identity_status_id,
    ) is not value.status_id:
        raise ValueError("development terminal status is not canonical")
    if (
        value.status_id
        is DevelopmentOracleRunStatus.COMPLETED_RESPONSE_IDENTITY_MATCHED
    ):
        if (
            value.exit_status != 0
            or value.terminating_signal is not None
            or not value.stdin_complete
            or not value.stdout_complete
            or not value.stderr_complete
            or value.stderr_size_bytes != 0
            or value.stdin_written_size_bytes != value.request_frame_byte_count
            or value.stdin_written_sha256 != value.request_frame_sha256
            or value.response_identity_status_id
            is not DevelopmentOracleResponseIdentityStatus.MATCHED
            or value.output_limit_kind_id
            is not DevelopmentOracleOutputLimitKind.NONE
            or value.wall_limit_triggered
            or value.elapsed_monotonic_nanoseconds
            > value.wall_time_limit_nanoseconds
            or value.process_group_cleanup_triggered
            or value.process_group_nonquiescence_triggered
        ):
            raise ValueError("completed development status is inconsistent")


def _receipt_tree(
    value: DevelopmentArchiveSelectedOracleRunReceiptV1,
) -> dict:
    if type(value) is not DevelopmentArchiveSelectedOracleRunReceiptV1:
        raise TypeError("development oracle receipt must be exact")
    DevelopmentArchiveSelectedOracleRunReceiptV1.__post_init__(value)
    result = {}
    for item in fields(value):
        field_value = getattr(value, item.name)
        if isinstance(field_value, Enum):
            field_value = field_value.value
        result[item.name] = field_value
    return result


def development_oracle_run_receipt_bytes(
    value: DevelopmentArchiveSelectedOracleRunReceiptV1,
) -> bytes:
    """Return exact canonical ASCII JSON for one local receipt."""

    try:
        result = json.dumps(
            _receipt_tree(value),
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (AttributeError, TypeError, ValueError, UnicodeError):
        _fail(DevelopmentOracleRunCode.CANONICALIZATION_FAILED)
    if not result or len(result) > MAXIMUM_ORACLE_DEVELOPMENT_RECEIPT_BYTES:
        _fail(DevelopmentOracleRunCode.CANONICALIZATION_FAILED)
    return result


def development_oracle_run_receipt_sha256(
    value: DevelopmentArchiveSelectedOracleRunReceiptV1,
) -> str:
    """Return the length-framed receipt-domain digest."""

    payload = development_oracle_run_receipt_bytes(value)
    return _length_framed_sha256(_RECEIPT_DOMAIN_BYTES, (payload,))


def validate_development_oracle_run_receipt(
    value: object,
) -> DevelopmentArchiveSelectedOracleRunReceiptV1:
    """Return a fresh structural receipt snapshot, never an attestation."""

    if type(value) is not DevelopmentArchiveSelectedOracleRunReceiptV1:
        _fail(DevelopmentOracleRunCode.RECEIPT_INVALID)
    try:
        DevelopmentArchiveSelectedOracleRunReceiptV1.__post_init__(value)
        kwargs = {
            item.name: getattr(value, item.name)
            for item in fields(value)
            if item.init
        }
        return DevelopmentArchiveSelectedOracleRunReceiptV1(**kwargs)
    except DevelopmentOracleRunError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(DevelopmentOracleRunCode.RECEIPT_INVALID)


@dataclass(frozen=True)
class ValidatedDevelopmentOracleRunV1:
    """Privileged transport whose deep validity does not prove execution.

    Failure stdout/stderr remain worker-controlled and are retained only so a
    local reviewer can revalidate their receipt commitments.  This value must
    not be serialized as a public diagnostic artifact.
    """

    receipt: DevelopmentArchiveSelectedOracleRunReceiptV1
    receipt_bytes: bytes
    receipt_sha256: str
    request_frame_bytes: bytes
    stdout_bytes: bytes
    stderr_bytes: bytes
    response_frame_bytes: Optional[bytes]
    validated_response_identity: Optional[
        ValidatedOracleWorkerResponseIdentityV1
    ]

    def __post_init__(self) -> None:
        if type(self) is not ValidatedDevelopmentOracleRunV1:
            raise TypeError("validated development oracle run must be exact")
        _validate_run_transport(self)


def _validate_run_transport(value: ValidatedDevelopmentOracleRunV1) -> None:
    receipt = validate_development_oracle_run_receipt(value.receipt)
    if type(value.receipt_bytes) is not bytes:
        raise TypeError("receipt bytes must be exact")
    if (
        value.response_frame_bytes is not None
        and type(value.response_frame_bytes) is not bytes
    ):
        raise TypeError("optional response frame must contain exact bytes")
    if (
        value.validated_response_identity is not None
        and type(value.validated_response_identity)
        is not ValidatedOracleWorkerResponseIdentityV1
    ):
        raise TypeError("optional response identity must be exact")
    if value.validated_response_identity is not None:
        try:
            ValidatedOracleWorkerResponseIdentityV1.__post_init__(
                value.validated_response_identity
            )
        except (AttributeError, OracleWorkerABIError, TypeError, ValueError):
            raise TypeError("optional response identity is invalid") from None
    if development_oracle_run_receipt_bytes(receipt) != value.receipt_bytes:
        raise ValueError("receipt bytes differ")
    _sha256(value.receipt_sha256)
    if (
        development_oracle_run_receipt_sha256(receipt)
        != value.receipt_sha256
    ):
        raise ValueError("receipt digest differs")
    for name, maximum in (
        ("request_frame_bytes", ORACLE_DEVELOPMENT_STDIN_LIMIT_BYTES),
        ("stdout_bytes", ORACLE_DEVELOPMENT_STDOUT_LIMIT_BYTES),
        ("stderr_bytes", ORACLE_DEVELOPMENT_STDERR_LIMIT_BYTES),
    ):
        item = getattr(value, name)
        if type(item) is not bytes or len(item) > maximum:
            raise TypeError(name + " violates its exact byte bound")
    if (
        len(value.stdout_bytes) + len(value.stderr_bytes)
        > ORACLE_DEVELOPMENT_AGGREGATE_OUTPUT_LIMIT_BYTES
    ):
        raise ValueError("transport aggregate output exceeds its ceiling")
    if (
        len(value.request_frame_bytes) != receipt.request_frame_byte_count
        or hashlib.sha256(value.request_frame_bytes).hexdigest()
        != receipt.request_frame_sha256
        or len(value.stdout_bytes) != receipt.stdout_size_bytes
        or hashlib.sha256(value.stdout_bytes).hexdigest()
        != receipt.stdout_sha256
        or len(value.stderr_bytes) != receipt.stderr_size_bytes
        or hashlib.sha256(value.stderr_bytes).hexdigest()
        != receipt.stderr_sha256
    ):
        raise ValueError("transport raw-byte commitment differs")
    stdin_prefix = value.request_frame_bytes[
        : receipt.stdin_written_size_bytes
    ]
    if hashlib.sha256(stdin_prefix).hexdigest() != (
        receipt.stdin_written_sha256
    ):
        raise ValueError("written stdin is not the exact request prefix")
    returncode = (
        receipt.exit_status
        if receipt.exit_status is not None
        else -receipt.terminating_signal
    )
    observation = _ProcessObservation(
        returncode=returncode,
        elapsed_nanoseconds=receipt.elapsed_monotonic_nanoseconds,
        stdin_written_bytes=stdin_prefix,
        stdin_complete=receipt.stdin_complete,
        stdout_bytes=value.stdout_bytes,
        stdout_complete=receipt.stdout_complete,
        stderr_bytes=value.stderr_bytes,
        stderr_complete=receipt.stderr_complete,
        output_limit_kind=receipt.output_limit_kind_id,
        wall_limit_triggered=receipt.wall_limit_triggered,
        process_group_cleanup_triggered=(
            receipt.process_group_cleanup_triggered
        ),
        process_group_nonquiescence_triggered=(
            receipt.process_group_nonquiescence_triggered
        ),
        process_group_quiescent=(
            receipt.managed_process_group_observed_quiescent
        ),
    )
    observed_response_status, observed_frame, observed_identity = (
        _response_identity(value.request_frame_bytes, observation)
    )
    if (
        receipt.response_identity_status_id is not observed_response_status
        or value.response_frame_bytes != observed_frame
        or value.validated_response_identity != observed_identity
    ):
        raise ValueError("transport response identity state differs")
    if observed_frame is None:
        if (
            receipt.response_frame_byte_count is not None
            or receipt.response_frame_sha256 is not None
        ):
            raise ValueError("unexpected response frame commitment")
    elif (
        type(value.response_frame_bytes) is not bytes
        or len(observed_frame) != receipt.response_frame_byte_count
        or hashlib.sha256(observed_frame).hexdigest()
        != receipt.response_frame_sha256
    ):
        raise ValueError("response frame raw bytes differ")
    if _terminal_status(observation, observed_response_status) is not (
        receipt.status_id
    ):
        raise ValueError("transport terminal status differs")


def validate_validated_development_oracle_run(
    value: object,
) -> ValidatedDevelopmentOracleRunV1:
    """Return a fresh deep transport snapshot without historical authority."""

    if type(value) is not ValidatedDevelopmentOracleRunV1:
        _fail(DevelopmentOracleRunCode.RECEIPT_INVALID)
    try:
        _validate_run_transport(value)
        receipt = validate_development_oracle_run_receipt(value.receipt)
        identity = None
        if value.validated_response_identity is not None:
            assert value.response_frame_bytes is not None
            identity = validate_oracle_worker_response_identity(
                value.request_frame_bytes,
                value.response_frame_bytes,
            )
        return ValidatedDevelopmentOracleRunV1(
            receipt=receipt,
            receipt_bytes=bytes(value.receipt_bytes),
            receipt_sha256=value.receipt_sha256,
            request_frame_bytes=bytes(value.request_frame_bytes),
            stdout_bytes=bytes(value.stdout_bytes),
            stderr_bytes=bytes(value.stderr_bytes),
            response_frame_bytes=(
                None
                if value.response_frame_bytes is None
                else bytes(value.response_frame_bytes)
            ),
            validated_response_identity=identity,
        )
    except DevelopmentOracleRunError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(DevelopmentOracleRunCode.RECEIPT_INVALID)


@dataclass(frozen=True)
class _InterpreterSnapshot:
    path: str
    descriptor: int
    content_bytes: bytes
    content_sha256: str
    identity: Tuple[int, int, int, int, int]
    observation_sha256: str


@dataclass(frozen=True)
class _WorkingDirectorySnapshot:
    path: str
    identity: Tuple[int, int, int]
    digest: str


@dataclass(frozen=True)
class _PreparedRun:
    input: DevelopmentOracleRunInputV1
    request_oracle_id: str
    source_bytes: bytes
    source_policy_receipt_bytes: bytes
    source_policy_receipt_sha256: str
    membership_receipt_sha256: str
    interpreter: _InterpreterSnapshot
    working_directory: _WorkingDirectorySnapshot
    argv: Tuple[str, ...]
    argv_sha256: str
    environment_sha256: str
    run_input_sha256: str


def _interpreter_identity(status: os.stat_result) -> Tuple[int, int, int, int, int]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        status.st_size,
        status.st_mtime_ns,
    )


def _interpreter_observation_sha256(
    path: str,
    identity: Tuple[int, int, int, int, int],
) -> str:
    return _length_framed_sha256(
        _INTERPRETER_OBSERVATION_DOMAIN,
        (
            path.encode("utf-8", "strict"),
            *(str(item).encode("ascii") for item in identity),
        ),
    )


def _capture_interpreter(
    input_path: str,
    expected_bytes: bytes,
) -> _InterpreterSnapshot:
    path = os.path.realpath(input_path)
    if (
        not os.path.isabs(path)
        or os.path.normpath(path) != path
        or len(path.encode("utf-8", "strict"))
        > MAXIMUM_ORACLE_DEVELOPMENT_PATH_BYTES
    ):
        _fail(DevelopmentOracleRunCode.INTERPRETER_CAPTURE_FAILED)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = None
    try:
        descriptor = os.open(path, flags)
        status = os.fstat(descriptor)
        if (
            not stat.S_ISREG(status.st_mode)
            or status.st_size <= 0
            or status.st_size
            > MAXIMUM_ORACLE_DEVELOPMENT_INTERPRETER_BYTES
            or not os.access(path, os.X_OK)
        ):
            _fail(DevelopmentOracleRunCode.INTERPRETER_CAPTURE_FAILED)
        chunks = []
        remaining = status.st_size
        while remaining:
            chunk = os.read(
                descriptor,
                min(MAXIMUM_ORACLE_DEVELOPMENT_READ_CHUNK_BYTES, remaining),
            )
            if not chunk:
                _fail(DevelopmentOracleRunCode.INTERPRETER_CAPTURE_FAILED)
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1) != b"":
            _fail(DevelopmentOracleRunCode.INTERPRETER_CAPTURE_FAILED)
        content = b"".join(chunks)
        if content != expected_bytes:
            _fail(DevelopmentOracleRunCode.INTERPRETER_IDENTITY_MISMATCH)
        identity = _interpreter_identity(status)
        try:
            path_status = os.stat(path, follow_symlinks=False)
        except OSError:
            _fail(DevelopmentOracleRunCode.INTERPRETER_CAPTURE_FAILED)
        if _interpreter_identity(path_status) != identity:
            _fail(DevelopmentOracleRunCode.INTERPRETER_CAPTURE_FAILED)
        return _InterpreterSnapshot(
            path=path,
            descriptor=descriptor,
            content_bytes=content,
            content_sha256=hashlib.sha256(content).hexdigest(),
            identity=identity,
            observation_sha256=_interpreter_observation_sha256(
                path,
                identity,
            ),
        )
    except DevelopmentOracleRunError:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise
    except (OSError, UnicodeError):
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        _fail(DevelopmentOracleRunCode.INTERPRETER_CAPTURE_FAILED)
    except Exception:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        _fail(DevelopmentOracleRunCode.INTERPRETER_CAPTURE_FAILED)
    except BaseException:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise


def _verify_and_close_interpreter(
    value: _InterpreterSnapshot,
) -> None:
    failed = False
    try:
        descriptor_status = os.fstat(value.descriptor)
        path_status = os.stat(value.path, follow_symlinks=False)
        os.lseek(value.descriptor, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        remaining = len(value.content_bytes)
        while remaining:
            chunk = os.read(
                value.descriptor,
                min(MAXIMUM_ORACLE_DEVELOPMENT_READ_CHUNK_BYTES, remaining),
            )
            if not chunk:
                failed = True
                break
            digest.update(chunk)
            remaining -= len(chunk)
        trailing = os.read(value.descriptor, 1)
        if (
            _interpreter_identity(descriptor_status) != value.identity
            or _interpreter_identity(path_status) != value.identity
            or remaining != 0
            or trailing != b""
            or digest.hexdigest() != value.content_sha256
        ):
            failed = True
    except Exception:
        failed = True
    finally:
        try:
            os.close(value.descriptor)
        except OSError:
            failed = True
    if failed:
        _fail(DevelopmentOracleRunCode.INTERPRETER_IDENTITY_MISMATCH)


def _capture_working_directory(
    input_path: str,
) -> _WorkingDirectorySnapshot:
    path = os.path.realpath(input_path)
    try:
        if (
            not os.path.isabs(path)
            or os.path.normpath(path) != path
            or len(path.encode("utf-8", "strict"))
            > MAXIMUM_ORACLE_DEVELOPMENT_PATH_BYTES
        ):
            raise ValueError
        status = os.stat(path, follow_symlinks=False)
        if not stat.S_ISDIR(status.st_mode):
            raise ValueError
        identity = (
            status.st_dev,
            status.st_ino,
            stat.S_IFMT(status.st_mode),
        )
        digest = _length_framed_sha256(
            WORKING_DIRECTORY_DIGEST_DOMAIN,
            (
                path.encode("utf-8", "strict"),
                *(str(item).encode("ascii") for item in identity),
            ),
        )
    except (OSError, TypeError, UnicodeError, ValueError):
        _fail(DevelopmentOracleRunCode.WORKING_DIRECTORY_INVALID)
    return _WorkingDirectorySnapshot(
        path=path,
        identity=identity,
        digest=digest,
    )


def _verify_working_directory(
    value: _WorkingDirectorySnapshot,
) -> None:
    try:
        status = os.stat(value.path, follow_symlinks=False)
        observed = (
            status.st_dev,
            status.st_ino,
            stat.S_IFMT(status.st_mode),
        )
        resolved = os.path.realpath(value.path)
    except OSError:
        _fail(DevelopmentOracleRunCode.WORKING_DIRECTORY_INVALID)
    if (
        observed != value.identity
        or resolved != value.path
        or not stat.S_ISDIR(status.st_mode)
    ):
        _fail(DevelopmentOracleRunCode.WORKING_DIRECTORY_INVALID)


def _run_input_sha256(prepared: _PreparedRun) -> str:
    value = prepared.input
    return _length_framed_sha256(
        _RUN_INPUT_DOMAIN_BYTES,
        (
            value.oracle_registry_bytes,
            value.source_archive_inventory_bytes,
            value.source_archive_bytes,
            value.source_archive_membership_receipt_bytes,
            value.request_frame_bytes,
            value.interpreter_executable_bytes,
            value.interpreter_path.encode("utf-8", "strict"),
            value.working_directory.encode("utf-8", "strict"),
            prepared.request_oracle_id.encode("ascii"),
            prepared.source_bytes,
            prepared.source_policy_receipt_bytes,
            prepared.interpreter.path.encode("utf-8", "strict"),
            prepared.interpreter.observation_sha256.encode("ascii"),
            prepared.working_directory.path.encode("utf-8", "strict"),
            prepared.working_directory.digest.encode("ascii"),
            prepared.argv_sha256.encode("ascii"),
            prepared.environment_sha256.encode("ascii"),
        ),
    )


def _prepare_run(
    value: DevelopmentOracleRunInputV1,
) -> _PreparedRun:
    run_input = _snapshot_input(value)
    try:
        request = parse_oracle_worker_request_frame(
            run_input.request_frame_bytes
        )
    except (OracleWorkerABIError, TypeError, ValueError):
        _fail(DevelopmentOracleRunCode.REQUEST_INVALID)
    try:
        registry = validate_golden_oracle_registry(
            run_input.oracle_registry_bytes
        )
    except Exception:
        _fail(DevelopmentOracleRunCode.REGISTRY_INVALID)
    entries = tuple(
        item for item in registry.oracles if item.oracle_id == request.oracle_id
    )
    if len(entries) != 1:
        _fail(DevelopmentOracleRunCode.SOURCE_SELECTION_INVALID)
    entry = entries[0]
    try:
        resolved = resolve_source_archive_object(
            run_input.source_archive_inventory_bytes,
            run_input.source_archive_bytes,
            role_id=SOURCE_ARCHIVE_ORACLE_ROLE_ID,
            source_object_id=request.oracle_id,
        )
    except SourceArchiveValidationError as error:
        if error.code == SourceArchiveCode.MEMBERSHIP_MISMATCH.value:
            _fail(DevelopmentOracleRunCode.SOURCE_SELECTION_INVALID)
        _fail(DevelopmentOracleRunCode.ARCHIVE_INVALID)
    except Exception:
        _fail(DevelopmentOracleRunCode.ARCHIVE_INVALID)
    membership = resolved.membership
    source_bytes = resolved.source_bytes
    registry_source_identities = tuple(
        (
            item.oracle_id,
            item.oracle_source_byte_count,
            item.oracle_source_sha256,
        )
        for item in registry.oracles
    )
    archive_source_identities = tuple(
        (
            item.source_object_id,
            item.source_byte_count,
            item.source_sha256,
        )
        for item in resolved.source_archive.inventory.source_objects
        if item.role_id == SOURCE_ARCHIVE_ORACLE_ROLE_ID
    )
    if registry_source_identities != archive_source_identities:
        _fail(DevelopmentOracleRunCode.SOURCE_SELECTION_INVALID)
    if (
        membership.role_id != SOURCE_ARCHIVE_ORACLE_ROLE_ID
        or membership.source_object_id != request.oracle_id
        or membership.source_byte_count != entry.oracle_source_byte_count
        or membership.source_sha256 != entry.oracle_source_sha256
        or len(source_bytes) != entry.oracle_source_byte_count
        or hashlib.sha256(source_bytes).hexdigest()
        != entry.oracle_source_sha256
    ):
        _fail(DevelopmentOracleRunCode.SOURCE_SELECTION_INVALID)
    expected_membership_bytes = source_archive_membership_receipt_bytes(
        membership
    )
    if (
        expected_membership_bytes
        != run_input.source_archive_membership_receipt_bytes
    ):
        _fail(DevelopmentOracleRunCode.MEMBERSHIP_MISMATCH)
    if (
        request.oracle_source_byte_count != len(source_bytes)
        or request.oracle_source_sha256
        != hashlib.sha256(source_bytes).hexdigest()
    ):
        _fail(DevelopmentOracleRunCode.REQUEST_SOURCE_MISMATCH)
    if len(source_bytes) > MAXIMUM_ORACLE_DEVELOPMENT_SOURCE_ARGV_BYTES:
        _fail(DevelopmentOracleRunCode.INPUT_RESOURCE)
    try:
        source_text = source_bytes.decode("ascii", "strict")
    except UnicodeError:
        _fail(DevelopmentOracleRunCode.SOURCE_POLICY_REJECTED)
    if source_text.encode("ascii", "strict") != source_bytes:
        _fail(DevelopmentOracleRunCode.SOURCE_POLICY_REJECTED)
    try:
        policy = validate_oracle_source_policy(
            source_bytes,
            oracle_id=entry.oracle_id,
            oracle_source_byte_count=entry.oracle_source_byte_count,
            oracle_source_sha256=entry.oracle_source_sha256,
            forbidden_import_ids=entry.forbidden_import_ids,
            forbidden_name_ids=entry.forbidden_name_ids,
        )
    except Exception:
        _fail(DevelopmentOracleRunCode.SOURCE_POLICY_REJECTED)
    interpreter = _capture_interpreter(
        run_input.interpreter_path,
        run_input.interpreter_executable_bytes,
    )
    try:
        working_directory = _capture_working_directory(
            run_input.working_directory
        )
        argv = (
            interpreter.path,
            "-I",
            "-S",
            "-B",
            "-c",
            source_text,
        )
        argv_digest = argv_sha256(argv)
        environment_digest = environment_sha256({})
        provisional = _PreparedRun(
            input=run_input,
            request_oracle_id=request.oracle_id,
            source_bytes=source_bytes,
            source_policy_receipt_bytes=policy.receipt_bytes,
            source_policy_receipt_sha256=(
                oracle_source_policy_receipt_sha256(policy.receipt)
            ),
            membership_receipt_sha256=(
                source_archive_membership_receipt_sha256(membership)
            ),
            interpreter=interpreter,
            working_directory=working_directory,
            argv=argv,
            argv_sha256=argv_digest,
            environment_sha256=environment_digest,
            run_input_sha256=_EMPTY_SHA256,
        )
        return _PreparedRun(
            **{
                **provisional.__dict__,
                "run_input_sha256": _run_input_sha256(provisional),
            }
        )
    except DevelopmentOracleRunError:
        try:
            os.close(interpreter.descriptor)
        except OSError:
            pass
        raise
    except Exception:
        try:
            os.close(interpreter.descriptor)
        except OSError:
            pass
        _fail(DevelopmentOracleRunCode.INPUT_TYPE)
    except BaseException:
        try:
            os.close(interpreter.descriptor)
        except OSError:
            pass
        raise


@dataclass(frozen=True)
class _ProcessObservation:
    returncode: int
    elapsed_nanoseconds: int
    stdin_written_bytes: bytes
    stdin_complete: bool
    stdout_bytes: bytes
    stdout_complete: bool
    stderr_bytes: bytes
    stderr_complete: bool
    output_limit_kind: DevelopmentOracleOutputLimitKind
    wall_limit_triggered: bool
    process_group_cleanup_triggered: bool
    process_group_nonquiescence_triggered: bool
    process_group_quiescent: bool


def _clock_nanoseconds() -> int:
    try:
        value = time.monotonic_ns()
    except Exception:
        _fail(DevelopmentOracleRunCode.CLOCK_INVALID)
    if type(value) is not int or value < 0:
        _fail(DevelopmentOracleRunCode.CLOCK_INVALID)
    return value


def _process_group_is_empty(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return True
    except OSError as error:
        if error.errno == errno.ESRCH:
            return True
        return False
    return False


def _wait_direct_child(
    process: subprocess.Popen,
    *,
    timeout: float,
) -> bool:
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return False
    except OSError:
        _fail(DevelopmentOracleRunCode.REAP_FAILED)
    return process.poll() is not None


def _terminate_process_group(process: subprocess.Popen) -> None:
    process_group_id = process.pid
    process.poll()
    for chosen_signal, wait_seconds in (
        (signal.SIGTERM, _TERMINATION_GRACE_SECONDS),
        (signal.SIGKILL, _TERMINATION_FINAL_SECONDS),
    ):
        if _process_group_is_empty(process_group_id):
            break
        try:
            os.killpg(process_group_id, chosen_signal)
        except ProcessLookupError:
            break
        except OSError as error:
            if error.errno == errno.ESRCH:
                break
            _fail(DevelopmentOracleRunCode.TERMINATION_FAILED)
        _wait_direct_child(process, timeout=wait_seconds)
    if process.poll() is None and not _wait_direct_child(
        process,
        timeout=_TERMINATION_FINAL_SECONDS,
    ):
        _fail(DevelopmentOracleRunCode.REAP_FAILED)
    deadline = time.monotonic() + _TERMINATION_FINAL_SECONDS
    while not _process_group_is_empty(process_group_id):
        if time.monotonic() >= deadline:
            _fail(DevelopmentOracleRunCode.TERMINATION_FAILED)
        try:
            os.killpg(process_group_id, signal.SIGKILL)
        except ProcessLookupError:
            break
        except OSError as error:
            if error.errno == errno.ESRCH:
                break
            _fail(DevelopmentOracleRunCode.TERMINATION_FAILED)
        time.sleep(0.01)


def _close_selector_stream(
    selector: selectors.BaseSelector,
    stream,
) -> None:
    try:
        selector.unregister(stream)
    except (KeyError, ValueError):
        pass
    try:
        stream.close()
    except OSError:
        _fail(DevelopmentOracleRunCode.CLOSE_FAILED)


def _admit_output(
    target: bytearray,
    chunk: bytes,
    *,
    stream_limit: int,
    other_size: int,
) -> Tuple[DevelopmentOracleOutputLimitKind, int]:
    stream_remaining = max(0, stream_limit - len(target))
    aggregate_remaining = max(
        0,
        ORACLE_DEVELOPMENT_AGGREGATE_OUTPUT_LIMIT_BYTES
        - len(target)
        - other_size,
    )
    admitted_size = min(
        len(chunk),
        stream_remaining,
        aggregate_remaining,
    )
    target.extend(chunk[:admitted_size])
    if admitted_size == len(chunk):
        return DevelopmentOracleOutputLimitKind.NONE, admitted_size
    if aggregate_remaining <= stream_remaining:
        return DevelopmentOracleOutputLimitKind.AGGREGATE, admitted_size
    if stream_limit == ORACLE_DEVELOPMENT_STDOUT_LIMIT_BYTES:
        return DevelopmentOracleOutputLimitKind.STDOUT, admitted_size
    return DevelopmentOracleOutputLimitKind.STDERR, admitted_size


def _run_posix_duplex(
    prepared: _PreparedRun,
) -> _ProcessObservation:
    if os.name != "posix":
        _fail(DevelopmentOracleRunCode.PLATFORM_UNAVAILABLE)
    process = None
    selector = selectors.DefaultSelector()
    stdout = bytearray()
    stderr = bytearray()
    stdin_written = bytearray()
    stdin_complete = False
    stdout_complete = False
    stderr_complete = False
    output_limit_kind = DevelopmentOracleOutputLimitKind.NONE
    wall_limit_triggered = False
    process_group_cleanup_triggered = False
    process_group_nonquiescence_triggered = False
    forced_stop = False
    try:
        _verify_working_directory(prepared.working_directory)
        start = _clock_nanoseconds()
        previous = start
        try:
            process = subprocess.Popen(
                prepared.argv,
                cwd=prepared.working_directory.path,
                env={},
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                close_fds=True,
                shell=False,
                start_new_session=True,
            )
        except (OSError, ValueError, subprocess.SubprocessError):
            _fail(DevelopmentOracleRunCode.SPAWN_FAILED)
        if (
            process.stdin is None
            or process.stdout is None
            or process.stderr is None
            or type(process.pid) is not int
            or process.pid <= 0
        ):
            _fail(DevelopmentOracleRunCode.PROCESS_PROTOCOL_INVALID)
        for stream in (process.stdin, process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
        selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        drain_deadline = None
        while True:
            now = _clock_nanoseconds()
            if now < previous:
                _fail(DevelopmentOracleRunCode.CLOCK_INVALID)
            previous = now
            elapsed = now - start
            returncode = process.poll()
            if returncode is not None and type(returncode) is not int:
                _fail(DevelopmentOracleRunCode.PROCESS_PROTOCOL_INVALID)
            execution_active = (
                returncode is None
                or not (stdout_complete and stderr_complete)
            )
            wall_limit_reached = (
                elapsed > ORACLE_DEVELOPMENT_WALL_TIME_LIMIT_NANOSECONDS
                or (
                    elapsed
                    == ORACLE_DEVELOPMENT_WALL_TIME_LIMIT_NANOSECONDS
                    and execution_active
                )
            )
            if not forced_stop and wall_limit_reached:
                wall_limit_triggered = True
                forced_stop = True
                if process.stdin is not None and not process.stdin.closed:
                    _close_selector_stream(selector, process.stdin)
                if (
                    process.poll() is None
                    or not _process_group_is_empty(process.pid)
                ):
                    process_group_cleanup_triggered = True
                    _terminate_process_group(process)
                drain_deadline = time.monotonic() + _TERMINATION_FINAL_SECONDS
                returncode = process.poll()
            if returncode is not None and not forced_stop:
                if process.stdin is not None and not process.stdin.closed:
                    _close_selector_stream(selector, process.stdin)
                if not _process_group_is_empty(process.pid):
                    process_group_cleanup_triggered = True
                    process_group_nonquiescence_triggered = True
                    forced_stop = True
                    _terminate_process_group(process)
                    drain_deadline = (
                        time.monotonic() + _TERMINATION_FINAL_SECONDS
                    )
            if (
                returncode is not None
                and stdout_complete
                and stderr_complete
            ):
                break
            if (
                forced_stop
                and drain_deadline is not None
                and time.monotonic() >= drain_deadline
            ):
                break
            remaining_seconds = max(
                0.0,
                (
                    ORACLE_DEVELOPMENT_WALL_TIME_LIMIT_NANOSECONDS
                    - elapsed
                )
                / 1_000_000_000,
            )
            timeout = min(_IO_POLL_INTERVAL_SECONDS, remaining_seconds)
            if forced_stop:
                timeout = _IO_POLL_INTERVAL_SECONDS
            try:
                events = selector.select(timeout=timeout)
            except (OSError, ValueError):
                _fail(DevelopmentOracleRunCode.PROCESS_PROTOCOL_INVALID)
            for key, mask in events:
                stream = key.fileobj
                if key.data == "stdin":
                    if forced_stop or stream.closed:
                        continue
                    if not (mask & selectors.EVENT_WRITE):
                        continue
                    remaining = prepared.input.request_frame_bytes[
                        len(stdin_written) :
                    ]
                    if not remaining:
                        stdin_complete = True
                        _close_selector_stream(selector, stream)
                        continue
                    try:
                        count = os.write(
                            stream.fileno(),
                            remaining[
                                :MAXIMUM_ORACLE_DEVELOPMENT_WRITE_CHUNK_BYTES
                            ],
                        )
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        _close_selector_stream(selector, stream)
                        if not forced_stop:
                            forced_stop = True
                            if (
                                process.poll() is None
                                or not _process_group_is_empty(process.pid)
                            ):
                                process_group_cleanup_triggered = True
                                _terminate_process_group(process)
                            drain_deadline = (
                                time.monotonic()
                                + _TERMINATION_FINAL_SECONDS
                            )
                        continue
                    except OSError as error:
                        if error.errno in (errno.EAGAIN, errno.EINTR):
                            continue
                        _fail(
                            DevelopmentOracleRunCode.PROCESS_PROTOCOL_INVALID
                        )
                    if type(count) is not int or count <= 0:
                        _fail(
                            DevelopmentOracleRunCode.PROCESS_PROTOCOL_INVALID
                        )
                    stdin_written.extend(remaining[:count])
                    if len(stdin_written) == len(
                        prepared.input.request_frame_bytes
                    ):
                        stdin_complete = True
                        _close_selector_stream(selector, stream)
                    continue
                if not (mask & selectors.EVENT_READ):
                    continue
                try:
                    chunk = os.read(
                        stream.fileno(),
                        MAXIMUM_ORACLE_DEVELOPMENT_READ_CHUNK_BYTES,
                    )
                except BlockingIOError:
                    continue
                except OSError as error:
                    if error.errno in (errno.EAGAIN, errno.EINTR):
                        continue
                    _fail(DevelopmentOracleRunCode.PROCESS_PROTOCOL_INVALID)
                if not chunk:
                    _close_selector_stream(selector, stream)
                    if key.data == "stdout":
                        stdout_complete = True
                    else:
                        stderr_complete = True
                    continue
                if key.data == "stdout":
                    limit_kind, _admitted = _admit_output(
                        stdout,
                        chunk,
                        stream_limit=ORACLE_DEVELOPMENT_STDOUT_LIMIT_BYTES,
                        other_size=len(stderr),
                    )
                else:
                    limit_kind, _admitted = _admit_output(
                        stderr,
                        chunk,
                        stream_limit=ORACLE_DEVELOPMENT_STDERR_LIMIT_BYTES,
                        other_size=len(stdout),
                    )
                if (
                    limit_kind is not DevelopmentOracleOutputLimitKind.NONE
                    and output_limit_kind
                    is DevelopmentOracleOutputLimitKind.NONE
                ):
                    output_limit_kind = limit_kind
                    forced_stop = True
                    if process.stdin is not None and not process.stdin.closed:
                        _close_selector_stream(selector, process.stdin)
                    if (
                        process.poll() is None
                        or not _process_group_is_empty(process.pid)
                    ):
                        process_group_cleanup_triggered = True
                        _terminate_process_group(process)
                    drain_deadline = (
                        time.monotonic() + _TERMINATION_FINAL_SECONDS
                    )
                    break
            if (
                forced_stop
                and output_limit_kind
                is not DevelopmentOracleOutputLimitKind.NONE
            ):
                # Prefix commitments are complete by definition only up to the
                # fixed cap; close readers rather than silently discarding.
                if process.stdout is not None and not process.stdout.closed:
                    _close_selector_stream(selector, process.stdout)
                if process.stderr is not None and not process.stderr.closed:
                    _close_selector_stream(selector, process.stderr)
                break
        if process.poll() is None:
            process_group_cleanup_triggered = True
            _terminate_process_group(process)
        if process.poll() is None:
            _fail(DevelopmentOracleRunCode.REAP_FAILED)
        group_quiescent = _process_group_is_empty(process.pid)
        if not group_quiescent:
            _fail(DevelopmentOracleRunCode.TERMINATION_FAILED)
        end = _clock_nanoseconds()
        if end < previous:
            _fail(DevelopmentOracleRunCode.CLOCK_INVALID)
        return _ProcessObservation(
            returncode=process.returncode,
            elapsed_nanoseconds=end - start,
            stdin_written_bytes=bytes(stdin_written),
            stdin_complete=stdin_complete,
            stdout_bytes=bytes(stdout),
            stdout_complete=stdout_complete,
            stderr_bytes=bytes(stderr),
            stderr_complete=stderr_complete,
            output_limit_kind=output_limit_kind,
            wall_limit_triggered=wall_limit_triggered,
            process_group_cleanup_triggered=(
                process_group_cleanup_triggered
            ),
            process_group_nonquiescence_triggered=(
                process_group_nonquiescence_triggered
            ),
            process_group_quiescent=group_quiescent,
        )
    except DevelopmentOracleRunError:
        if process is not None:
            try:
                if process.poll() is None or not _process_group_is_empty(
                    process.pid
                ):
                    _terminate_process_group(process)
            except DevelopmentOracleRunError:
                _fail(DevelopmentOracleRunCode.TERMINATION_FAILED)
        raise
    except Exception:
        if process is not None:
            try:
                if process.poll() is None or not _process_group_is_empty(
                    process.pid
                ):
                    _terminate_process_group(process)
            except Exception:
                _fail(DevelopmentOracleRunCode.TERMINATION_FAILED)
        _fail(DevelopmentOracleRunCode.PROCESS_PROTOCOL_INVALID)
    except BaseException:
        if process is not None:
            try:
                if process.poll() is None or not _process_group_is_empty(
                    process.pid
                ):
                    _terminate_process_group(process)
            except BaseException:
                _fail(DevelopmentOracleRunCode.TERMINATION_FAILED)
        raise
    finally:
        active_error = sys.exc_info()[0] is not None
        close_failed = False
        try:
            selector.close()
        except Exception:
            close_failed = True
        if process is not None:
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None and not stream.closed:
                    try:
                        stream.close()
                    except OSError:
                        close_failed = True
        if close_failed and not active_error:
            _fail(DevelopmentOracleRunCode.CLOSE_FAILED)


def _exit_fields(returncode: int) -> Tuple[Optional[int], Optional[int]]:
    if type(returncode) is not int:
        _fail(DevelopmentOracleRunCode.PROCESS_PROTOCOL_INVALID)
    if returncode < 0:
        chosen_signal = -returncode
        if chosen_signal <= 0 or chosen_signal >= signal.NSIG:
            _fail(DevelopmentOracleRunCode.PROCESS_PROTOCOL_INVALID)
        return None, chosen_signal
    if returncode > 255:
        _fail(DevelopmentOracleRunCode.PROCESS_PROTOCOL_INVALID)
    return returncode, None


def _response_identity(
    request_frame_bytes: bytes,
    observation: _ProcessObservation,
) -> Tuple[
    DevelopmentOracleResponseIdentityStatus,
    Optional[bytes],
    Optional[ValidatedOracleWorkerResponseIdentityV1],
]:
    if not observation.stdout_complete or not observation.stdout_bytes:
        return (
            DevelopmentOracleResponseIdentityStatus.NOT_AVAILABLE,
            None,
            None,
        )
    try:
        parse_oracle_worker_response_frame(observation.stdout_bytes)
    except OracleWorkerABIError:
        return (
            DevelopmentOracleResponseIdentityStatus.FRAME_INVALID,
            None,
            None,
        )
    try:
        identity = validate_oracle_worker_response_identity(
            request_frame_bytes,
            observation.stdout_bytes,
        )
    except OracleWorkerABIError as error:
        if error.code == OracleWorkerABICode.ABI_RESPONSE_IDENTITY.value:
            return (
                DevelopmentOracleResponseIdentityStatus.IDENTITY_MISMATCH,
                observation.stdout_bytes,
                None,
            )
        return (
            DevelopmentOracleResponseIdentityStatus.FRAME_INVALID,
            None,
            None,
        )
    return (
        DevelopmentOracleResponseIdentityStatus.MATCHED,
        observation.stdout_bytes,
        identity,
    )


def _terminal_status(
    observation: _ProcessObservation,
    response_status: DevelopmentOracleResponseIdentityStatus,
) -> DevelopmentOracleRunStatus:
    if observation.wall_limit_triggered:
        return DevelopmentOracleRunStatus.WALL_TIME_LIMIT_EXCEEDED
    limit_status = {
        DevelopmentOracleOutputLimitKind.AGGREGATE: (
            DevelopmentOracleRunStatus.AGGREGATE_OUTPUT_LIMIT_EXCEEDED
        ),
        DevelopmentOracleOutputLimitKind.STDOUT: (
            DevelopmentOracleRunStatus.STDOUT_LIMIT_EXCEEDED
        ),
        DevelopmentOracleOutputLimitKind.STDERR: (
            DevelopmentOracleRunStatus.STDERR_LIMIT_EXCEEDED
        ),
    }.get(observation.output_limit_kind)
    if limit_status is not None:
        return limit_status
    exit_status, terminating_signal = _exit_fields(observation.returncode)
    if (
        exit_status == 64
        and observation.stderr_bytes
        == ORACLE_DEVELOPMENT_WORKER_REJECTION_BYTES
    ):
        return DevelopmentOracleRunStatus.WORKER_REJECTED
    if not observation.stdin_complete:
        return DevelopmentOracleRunStatus.STDIN_INCOMPLETE
    if observation.process_group_nonquiescence_triggered:
        return DevelopmentOracleRunStatus.PROCESS_GROUP_CLEANUP_REQUIRED
    if terminating_signal is not None:
        return DevelopmentOracleRunStatus.SIGNALLED
    if exit_status != 0:
        return DevelopmentOracleRunStatus.NONZERO_EXIT
    if not observation.stdout_complete or not observation.stderr_complete:
        return DevelopmentOracleRunStatus.OUTPUT_INCOMPLETE
    if observation.stderr_bytes:
        return DevelopmentOracleRunStatus.STDERR_NONEMPTY
    if (
        response_status
        is DevelopmentOracleResponseIdentityStatus.FRAME_INVALID
        or response_status
        is DevelopmentOracleResponseIdentityStatus.NOT_AVAILABLE
    ):
        return DevelopmentOracleRunStatus.RESPONSE_FRAME_INVALID
    if (
        response_status
        is DevelopmentOracleResponseIdentityStatus.IDENTITY_MISMATCH
    ):
        return DevelopmentOracleRunStatus.RESPONSE_IDENTITY_MISMATCH
    return DevelopmentOracleRunStatus.COMPLETED_RESPONSE_IDENTITY_MATCHED


def _receipt_from_observation(
    prepared: _PreparedRun,
    observation: _ProcessObservation,
    *,
    response_status: DevelopmentOracleResponseIdentityStatus,
    response_frame_bytes: Optional[bytes],
) -> DevelopmentArchiveSelectedOracleRunReceiptV1:
    run_input = prepared.input
    exit_status, terminating_signal = _exit_fields(observation.returncode)
    status = _terminal_status(observation, response_status)
    return DevelopmentArchiveSelectedOracleRunReceiptV1(
        run_input_sha256=prepared.run_input_sha256,
        oracle_id=prepared.request_oracle_id,
        oracle_registry_byte_count=len(run_input.oracle_registry_bytes),
        oracle_registry_sha256=hashlib.sha256(
            run_input.oracle_registry_bytes
        ).hexdigest(),
        source_archive_inventory_byte_count=len(
            run_input.source_archive_inventory_bytes
        ),
        source_archive_inventory_sha256=hashlib.sha256(
            run_input.source_archive_inventory_bytes
        ).hexdigest(),
        source_archive_byte_count=len(run_input.source_archive_bytes),
        source_archive_sha256=hashlib.sha256(
            run_input.source_archive_bytes
        ).hexdigest(),
        source_archive_membership_receipt_byte_count=len(
            run_input.source_archive_membership_receipt_bytes
        ),
        source_archive_membership_receipt_sha256=(
            prepared.membership_receipt_sha256
        ),
        source_object_id=prepared.request_oracle_id,
        selected_source_byte_count=len(prepared.source_bytes),
        selected_source_sha256=hashlib.sha256(
            prepared.source_bytes
        ).hexdigest(),
        source_policy_receipt_byte_count=len(
            prepared.source_policy_receipt_bytes
        ),
        source_policy_receipt_sha256=(
            prepared.source_policy_receipt_sha256
        ),
        captured_interpreter_executable_byte_count=len(
            prepared.interpreter.content_bytes
        ),
        captured_interpreter_executable_sha256=(
            prepared.interpreter.content_sha256
        ),
        interpreter_observation_sha256=(
            prepared.interpreter.observation_sha256
        ),
        argv_sha256=prepared.argv_sha256,
        environment_sha256=prepared.environment_sha256,
        working_directory_sha256=prepared.working_directory.digest,
        request_frame_byte_count=len(run_input.request_frame_bytes),
        request_frame_sha256=hashlib.sha256(
            run_input.request_frame_bytes
        ).hexdigest(),
        stdin_written_size_bytes=len(observation.stdin_written_bytes),
        stdin_written_sha256=hashlib.sha256(
            observation.stdin_written_bytes
        ).hexdigest(),
        stdin_complete=observation.stdin_complete,
        response_frame_byte_count=(
            None if response_frame_bytes is None else len(response_frame_bytes)
        ),
        response_frame_sha256=(
            None
            if response_frame_bytes is None
            else hashlib.sha256(response_frame_bytes).hexdigest()
        ),
        response_identity_status_id=response_status,
        stdout_size_bytes=len(observation.stdout_bytes),
        stdout_sha256=hashlib.sha256(
            observation.stdout_bytes
        ).hexdigest(),
        stdout_complete=observation.stdout_complete,
        stderr_size_bytes=len(observation.stderr_bytes),
        stderr_sha256=hashlib.sha256(
            observation.stderr_bytes
        ).hexdigest(),
        stderr_complete=observation.stderr_complete,
        exit_status=exit_status,
        terminating_signal=terminating_signal,
        elapsed_monotonic_nanoseconds=(
            observation.elapsed_nanoseconds
        ),
        output_limit_kind_id=observation.output_limit_kind,
        wall_limit_triggered=observation.wall_limit_triggered,
        process_group_cleanup_triggered=(
            observation.process_group_cleanup_triggered
        ),
        process_group_nonquiescence_triggered=(
            observation.process_group_nonquiescence_triggered
        ),
        managed_process_group_observed_quiescent=(
            observation.process_group_quiescent
        ),
        status_id=status,
    )


def execute_archive_selected_oracle_worker(
    value: DevelopmentOracleRunInputV1,
) -> ValidatedDevelopmentOracleRunV1:
    """Execute one exact archive-selected worker request.

    The function returns a local nondecision record for terminal child states.
    Pre-spawn validation, spawn, clock, protocol, cleanup, or identity-capture
    failures raise one fixed :class:`DevelopmentOracleRunError` instead.
    """

    prepared = _prepare_run(value)
    try:
        observation = _run_posix_duplex(prepared)
        _verify_working_directory(prepared.working_directory)
        response_status, response_frame, identity = _response_identity(
            prepared.input.request_frame_bytes,
            observation,
        )
        receipt = _receipt_from_observation(
            prepared,
            observation,
            response_status=response_status,
            response_frame_bytes=response_frame,
        )
        receipt_bytes = development_oracle_run_receipt_bytes(receipt)
        result = ValidatedDevelopmentOracleRunV1(
            receipt=receipt,
            receipt_bytes=receipt_bytes,
            receipt_sha256=development_oracle_run_receipt_sha256(receipt),
            request_frame_bytes=prepared.input.request_frame_bytes,
            stdout_bytes=observation.stdout_bytes,
            stderr_bytes=observation.stderr_bytes,
            response_frame_bytes=response_frame,
            validated_response_identity=identity,
        )
        return validate_validated_development_oracle_run(result)
    finally:
        _verify_and_close_interpreter(prepared.interpreter)


def revalidate_development_oracle_run_bindings(
    value: ValidatedDevelopmentOracleRunV1,
    run_input: DevelopmentOracleRunInputV1,
) -> ValidatedDevelopmentOracleRunV1:
    """Revalidate all raw-input and transport bindings without re-executing.

    Event-only fields such as elapsed time, exit state, and cleanup remain
    unauthenticated local claims.  A coherent forged event can therefore pass
    this non-executing revalidator.  Preparation still performs local
    filesystem reads and observations; the function is neither pure nor
    historical attestation.
    """

    result = validate_validated_development_oracle_run(value)
    prepared = _prepare_run(run_input)
    try:
        receipt = result.receipt
        static_pairs = (
            (receipt.run_input_sha256, prepared.run_input_sha256),
            (receipt.oracle_id, prepared.request_oracle_id),
            (
                receipt.oracle_registry_byte_count,
                len(prepared.input.oracle_registry_bytes),
            ),
            (
                receipt.oracle_registry_sha256,
                hashlib.sha256(
                    prepared.input.oracle_registry_bytes
                ).hexdigest(),
            ),
            (
                receipt.source_archive_inventory_byte_count,
                len(prepared.input.source_archive_inventory_bytes),
            ),
            (
                receipt.source_archive_inventory_sha256,
                hashlib.sha256(
                    prepared.input.source_archive_inventory_bytes
                ).hexdigest(),
            ),
            (
                receipt.source_archive_byte_count,
                len(prepared.input.source_archive_bytes),
            ),
            (
                receipt.source_archive_sha256,
                hashlib.sha256(
                    prepared.input.source_archive_bytes
                ).hexdigest(),
            ),
            (
                receipt.source_archive_membership_receipt_byte_count,
                len(
                    prepared.input.source_archive_membership_receipt_bytes
                ),
            ),
            (
                receipt.source_archive_membership_receipt_sha256,
                prepared.membership_receipt_sha256,
            ),
            (receipt.source_object_id, prepared.request_oracle_id),
            (
                receipt.selected_source_byte_count,
                len(prepared.source_bytes),
            ),
            (
                receipt.selected_source_sha256,
                hashlib.sha256(prepared.source_bytes).hexdigest(),
            ),
            (
                receipt.source_policy_receipt_byte_count,
                len(prepared.source_policy_receipt_bytes),
            ),
            (
                receipt.source_policy_receipt_sha256,
                prepared.source_policy_receipt_sha256,
            ),
            (
                receipt.captured_interpreter_executable_byte_count,
                len(prepared.interpreter.content_bytes),
            ),
            (
                receipt.captured_interpreter_executable_sha256,
                prepared.interpreter.content_sha256,
            ),
            (
                receipt.interpreter_observation_sha256,
                prepared.interpreter.observation_sha256,
            ),
            (receipt.argv_sha256, prepared.argv_sha256),
            (
                receipt.environment_sha256,
                prepared.environment_sha256,
            ),
            (
                receipt.working_directory_sha256,
                prepared.working_directory.digest,
            ),
            (
                receipt.request_frame_byte_count,
                len(prepared.input.request_frame_bytes),
            ),
            (
                receipt.request_frame_sha256,
                hashlib.sha256(
                    prepared.input.request_frame_bytes
                ).hexdigest(),
            ),
            (
                result.request_frame_bytes,
                prepared.input.request_frame_bytes,
            ),
        )
        if any(observed != expected for observed, expected in static_pairs):
            _fail(DevelopmentOracleRunCode.RECEIPT_INVALID)
        return result
    finally:
        _verify_and_close_interpreter(prepared.interpreter)


__all__ = [
    "DEVELOPMENT_ORACLE_IMPLEMENTATION_STATUS",
    "DEVELOPMENT_ORACLE_RUNNER_ID",
    "DEVELOPMENT_ORACLE_RUN_INPUT_DIGEST_DOMAIN",
    "DEVELOPMENT_ORACLE_RUN_RECEIPT_ARTIFACT_TYPE",
    "DEVELOPMENT_ORACLE_RUN_RECEIPT_DIGEST_DOMAIN",
    "DevelopmentArchiveSelectedOracleRunReceiptV1",
    "DevelopmentOracleOutputLimitKind",
    "DevelopmentOracleResponseIdentityStatus",
    "DevelopmentOracleRunCode",
    "DevelopmentOracleRunError",
    "DevelopmentOracleRunInputV1",
    "DevelopmentOracleRunStatus",
    "MAXIMUM_ORACLE_DEVELOPMENT_INTERPRETER_BYTES",
    "MAXIMUM_ORACLE_DEVELOPMENT_RECEIPT_BYTES",
    "MAXIMUM_ORACLE_DEVELOPMENT_SOURCE_ARGV_BYTES",
    "ORACLE_DEVELOPMENT_AGGREGATE_OUTPUT_LIMIT_BYTES",
    "ORACLE_DEVELOPMENT_STDERR_LIMIT_BYTES",
    "ORACLE_DEVELOPMENT_STDIN_LIMIT_BYTES",
    "ORACLE_DEVELOPMENT_STDOUT_LIMIT_BYTES",
    "ORACLE_DEVELOPMENT_WALL_TIME_LIMIT_NANOSECONDS",
    "ValidatedDevelopmentOracleRunV1",
    "development_oracle_run_receipt_bytes",
    "development_oracle_run_receipt_sha256",
    "execute_archive_selected_oracle_worker",
    "revalidate_development_oracle_run_bindings",
    "validate_development_oracle_run_receipt",
    "validate_validated_development_oracle_run",
]
