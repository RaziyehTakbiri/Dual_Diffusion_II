"""Development-only external execution guard for adapter conformance.

The guard launches one explicit argument vector in one exact caller-supplied
working directory.  It never invokes a shell, never inherits the parent
environment, never persists child output, and never makes a publication or
gate decision.  Standard output and standard error are reduced online to
bounded byte counts and SHA-256 commitments.

The portable Python standard library cannot certify or enforce an exact peak
resident-set-size ceiling on both macOS and Linux.  The production backend
does not mislabel an address-space limit as RSS enforcement.  On Linux it
launches relative to a retained no-follow directory descriptor through
``/proc/self/fd`` and samples process-group RSS from ``/proc``.  The sampled
RSS is non-exact, so the child is terminated immediately as
``MEASUREMENT_UNAVAILABLE``.  macOS has no equivalent stdlib descriptor-cwd
launch mechanism and fails closed before spawn.  No production path can
return ``PASS``.
Only an explicitly injected probe that certifies exact enforcement can
exercise the ``PASS`` state, which is useful for deterministic state-machine
tests but is not a decision-bearing execution path.

This module itself performs no file writes.  Passing ``cwd`` controls the
child's working directory but is not an operating-system filesystem sandbox;
the caller remains responsible for launching the guard inside an execution
context whose filesystem permissions admit only the authorized directory.
The cwd digest binds the canonical path plus device/inode/type.  The Linux
backend launches through a retained ``O_DIRECTORY|O_NOFOLLOW`` descriptor,
so rename-and-replace races cannot redirect the child's cwd; other platforms
fail closed rather than make that binding claim.
Likewise, a descendant can escape a POSIX process group by creating a new
session; decision-capable resource/process containment requires an outer
platform sandbox rather than this development guard alone.
"""

from __future__ import annotations

from collections import namedtuple
from enum import Enum
import hashlib
import os
import selectors
import signal
import stat
import struct
import subprocess
import sys
import time
from types import MappingProxyType
from typing import Mapping, Optional, Protocol, Tuple


EXECUTION_GUARD_IMPLEMENTATION_STATUS = "DEVELOPMENT_ONLY"
WALL_TIME_LIMIT_NANOSECONDS = 180 * 1_000_000_000
PEAK_RSS_LIMIT_BYTES = 2 * 1024 * 1024 * 1024
ADDRESS_SPACE_LIMIT_BYTES = 2 * 1024 * 1024 * 1024
MAXIMUM_CAPTURED_OUTPUT_BYTES = 2 * 1024 * 1024
MAXIMUM_READ_CHUNK_BYTES = 64 * 1024
MAXIMUM_SOURCE_BINDING_BYTES = 16 * 1024 * 1024
MAXIMUM_ARGV_ENTRIES = 256
MAXIMUM_ARGV_COMPONENT_BYTES = 64 * 1024
MAXIMUM_ARGV_BYTES = 256 * 1024
MAXIMUM_ENVIRONMENT_ENTRIES = 64
MAXIMUM_ENVIRONMENT_KEY_BYTES = 256
MAXIMUM_ENVIRONMENT_VALUE_BYTES = 16 * 1024
MAXIMUM_ENVIRONMENT_BYTES = 64 * 1024
MAXIMUM_WORKING_DIRECTORY_BYTES = 4096

ARGV_DIGEST_DOMAIN = b"heterodiff.adapter.execution.argv.v1"
WORKING_DIRECTORY_DIGEST_DOMAIN = (
    b"heterodiff.adapter.execution.working-directory.v1"
)
ENVIRONMENT_DIGEST_DOMAIN = b"heterodiff.adapter.execution.environment.v1"
PUBLICATION_SOURCE_BINDING_DOMAIN = (
    b"heterodiff.adapter.execution-guard-input-binding.v1"
)
MAXIMUM_PUBLICATION_BINDING_COMPONENT_BYTES = 32 * 1024 * 1024

_POLL_INTERVAL_NANOSECONDS = 10 * 1_000_000
_DIGEST_BYTES = 32

__all__ = (
    "ADDRESS_SPACE_LIMIT_BYTES",
    "ARGV_DIGEST_DOMAIN",
    "AddressSpaceLimitMethod",
    "ClockMethod",
    "CwdLaunchMethod",
    "ENVIRONMENT_DIGEST_DOMAIN",
    "EXECUTION_GUARD_IMPLEMENTATION_STATUS",
    "ExecutionDependencies",
    "ExecutionGuardCode",
    "ExecutionGuardError",
    "ExecutionReceipt",
    "ExecutionStatus",
    "ExecutionBackend",
    "ExternalProcessFactory",
    "ManagedExternalProcess",
    "MAXIMUM_CAPTURED_OUTPUT_BYTES",
    "MonotonicClock",
    "FilesystemConfinementMethod",
    "OutputCaptureMethod",
    "PEAK_RSS_LIMIT_BYTES",
    "PeakRSSMethod",
    "PeakRSSUnits",
    "ProcessOutput",
    "ProcessContainmentMethod",
    "PUBLICATION_SOURCE_BINDING_DOMAIN",
    "RSSObservation",
    "ResourceProbe",
    "SourceBindingFormat",
    "WALL_TIME_LIMIT_NANOSECONDS",
    "WORKING_DIRECTORY_DIGEST_DOMAIN",
    "argv_sha256",
    "environment_sha256",
    "execute_external_argv",
    "publication_source_binding_bytes",
    "validate_execution_receipt",
    "working_directory_sha256",
)


class ExecutionStatus(str, Enum):
    """Terminal state of one development external execution."""

    PASS = "pass"
    MEASUREMENT_UNAVAILABLE = "measurement_unavailable"
    NONZERO_EXIT = "nonzero_exit"
    SIGNALLED = "signalled"
    TIMEOUT = "timeout"
    PEAK_RSS_LIMIT_EXCEEDED = "peak_rss_limit_exceeded"
    OUTPUT_LIMIT_EXCEEDED = "output_limit_exceeded"
    PROCESS_GROUP_NOT_QUIESCENT = "process_group_not_quiescent"


class PeakRSSUnits(str, Enum):
    """Units used by the peak-RSS field in a receipt."""

    BYTES = "bytes"
    UNAVAILABLE = "unavailable"


class PeakRSSMethod(str, Enum):
    """Closed measurement-method registry for peak RSS."""

    LINUX_PROC_GROUP_SAMPLED = "linux_proc_group_sampled"
    STDLIB_UNAVAILABLE = "stdlib_unavailable"
    INJECTED_EXACT = "injected_exact"


class AddressSpaceLimitMethod(str, Enum):
    """Mechanism used for the separate virtual-address-space ceiling."""

    POSIX_RLIMIT_AS = "posix_rlimit_as"
    UNAVAILABLE = "unavailable"
    INJECTED_TEST = "injected_test"


class ClockMethod(str, Enum):
    SYSTEM_MONOTONIC_NS = "system_monotonic_ns"
    INJECTED_TEST_CLOCK = "injected_test_clock"


class ExecutionBackend(str, Enum):
    STDLIB_SUBPROCESS = "stdlib_subprocess"
    INJECTED_TEST_BACKEND = "injected_test_backend"


class CwdLaunchMethod(str, Enum):
    LINUX_PROC_SELF_FD = "linux_proc_self_fd"
    INJECTED_TEST = "injected_test"


class ProcessContainmentMethod(str, Enum):
    POSIX_PROCESS_GROUP_ESCAPEABLE = "posix_process_group_escapeable"
    INJECTED_TEST = "injected_test"


class FilesystemConfinementMethod(str, Enum):
    NOT_PROVIDED = "not_provided"


class OutputCaptureMethod(str, Enum):
    BOUNDED_PIPE_SHA256 = "bounded_pipe_sha256"


class SourceBindingFormat(str, Enum):
    OPAQUE_EXACT_BYTES = "opaque_exact_bytes"
    EXECUTION_GUARD_INPUT_BINDING_V1 = "execution-guard-input-binding-v1"


class ExecutionGuardCode(str, Enum):
    """Stable fixed-error codes emitted before a receipt can be formed."""

    INPUT_INVALID = "INPUT_INVALID"
    WORKING_DIRECTORY_INVALID = "WORKING_DIRECTORY_INVALID"
    WORKING_DIRECTORY_MECHANISM_UNAVAILABLE = (
        "WORKING_DIRECTORY_MECHANISM_UNAVAILABLE"
    )
    SPAWN_FAILED = "SPAWN_FAILED"
    CLOCK_INVALID = "CLOCK_INVALID"
    PROCESS_PROTOCOL_INVALID = "PROCESS_PROTOCOL_INVALID"
    PROCESS_TERMINATION_FAILED = "PROCESS_TERMINATION_FAILED"
    PROCESS_CLOSE_FAILED = "PROCESS_CLOSE_FAILED"


_ERROR_MESSAGES = MappingProxyType(
    {
        ExecutionGuardCode.INPUT_INVALID: "execution guard input is invalid",
        ExecutionGuardCode.WORKING_DIRECTORY_INVALID: (
            "execution working directory is invalid"
        ),
        ExecutionGuardCode.WORKING_DIRECTORY_MECHANISM_UNAVAILABLE: (
            "exact working-directory launch mechanism is unavailable"
        ),
        ExecutionGuardCode.SPAWN_FAILED: (
            "external process could not be started"
        ),
        ExecutionGuardCode.CLOCK_INVALID: (
            "execution monotonic clock is invalid"
        ),
        ExecutionGuardCode.PROCESS_PROTOCOL_INVALID: (
            "external process protocol is invalid"
        ),
        ExecutionGuardCode.PROCESS_TERMINATION_FAILED: (
            "external process group could not be terminated"
        ),
        ExecutionGuardCode.PROCESS_CLOSE_FAILED: (
            "external process output could not be closed"
        ),
    }
)


class ExecutionGuardError(RuntimeError):
    """One fixed, coded guard failure with no untrusted message content."""

    def __init__(self, code: ExecutionGuardCode) -> None:
        if type(code) is not ExecutionGuardCode:
            raise TypeError("execution guard code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _raise_guard_error(code: ExecutionGuardCode) -> None:
    raise ExecutionGuardError(code) from None


def _validated_digest(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != _DIGEST_BYTES * 2:
        raise TypeError(name + " must be an exact SHA-256 string")
    try:
        decoded = bytes.fromhex(value)
    except ValueError:
        raise ValueError(name + " must be lowercase hexadecimal") from None
    if len(decoded) != _DIGEST_BYTES or value != value.lower():
        raise ValueError(name + " must be lowercase hexadecimal")
    return value


def _validated_nonnegative_integer(value: object, *, name: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(name + " must be an exact nonnegative integer")
    return value


def _encoded_text(
    value: object,
    *,
    name: str,
    maximum: int,
    allow_empty: bool = False,
) -> bytes:
    if (
        type(value) is not str
        or (not value and not allow_empty)
        or "\x00" in value
    ):
        raise TypeError(name + " must be an exact nonempty NUL-free string")
    try:
        encoded = value.encode("utf-8", "strict")
    except UnicodeError:
        raise ValueError(name + " must have a strict UTF-8 encoding") from None
    if len(encoded) > maximum:
        raise ValueError(name + " exceeds its byte ceiling")
    return encoded


def _length_prefixed_digest(
    domain: bytes, payloads: Tuple[bytes, ...]
) -> str:
    digest = hashlib.sha256()
    digest.update(struct.pack(">Q", len(domain)))
    digest.update(domain)
    digest.update(struct.pack(">Q", len(payloads)))
    for payload in payloads:
        digest.update(struct.pack(">Q", len(payload)))
        digest.update(payload)
    return digest.hexdigest()


def _bounded_iterable_tuple(
    iterable: object,
    *,
    exact_length: int,
    name: str,
) -> tuple:
    try:
        iterator = iter(iterable)  # type: ignore[arg-type]
    except Exception:
        raise TypeError(name + " iterable is invalid") from None
    values = []
    for _index in range(exact_length + 1):
        try:
            values.append(next(iterator))
        except StopIteration:
            break
        except Exception:
            raise TypeError(name + " iterable is invalid") from None
    if len(values) != exact_length:
        raise TypeError(name + " iterable has invalid length")
    return tuple(values)


def _snapshot_argv(argv: object) -> Tuple[str, ...]:
    if type(argv) is not tuple or not argv:
        _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
    if len(argv) > MAXIMUM_ARGV_ENTRIES:
        _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
    result = []
    total = 0
    for index, value in enumerate(argv):
        try:
            encoded = _encoded_text(
                value,
                name="argv component",
                maximum=MAXIMUM_ARGV_COMPONENT_BYTES,
                allow_empty=index != 0,
            )
        except (TypeError, ValueError):
            _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
        total += len(encoded)
        if total > MAXIMUM_ARGV_BYTES:
            _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
        result.append(value)
    snapshot = tuple(result)
    if not os.path.isabs(snapshot[0]):
        _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
    return snapshot


def _snapshot_environment(environment: object) -> Tuple[Tuple[str, str], ...]:
    if type(environment) is not dict:
        _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
    try:
        copied_environment = environment.copy()
    except Exception:
        _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
    if len(copied_environment) > MAXIMUM_ENVIRONMENT_ENTRIES:
        _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
    result = []
    total = 0
    for key, value in copied_environment.items():
        try:
            key_bytes = _encoded_text(
                key,
                name="environment key",
                maximum=MAXIMUM_ENVIRONMENT_KEY_BYTES,
            )
            value_bytes = _encoded_text(
                value,
                name="environment value",
                maximum=MAXIMUM_ENVIRONMENT_VALUE_BYTES,
                allow_empty=True,
            )
        except (TypeError, ValueError):
            _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
        if "=" in key:
            _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
        total += len(key_bytes) + len(value_bytes)
        if total > MAXIMUM_ENVIRONMENT_BYTES:
            _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
        result.append((key, value))
    return tuple(sorted(result))


def _snapshot_source(source_bytes: object) -> bytes:
    if type(source_bytes) is not bytes:
        _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
    if len(source_bytes) > MAXIMUM_SOURCE_BINDING_BYTES:
        _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
    return source_bytes


def _snapshot_working_directory(
    working_directory: object,
) -> Tuple[str, Tuple[int, int, int]]:
    try:
        _encoded_text(
            working_directory,
            name="working directory",
            maximum=MAXIMUM_WORKING_DIRECTORY_BYTES,
        )
    except (TypeError, ValueError):
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)
    if not os.path.isabs(working_directory):
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)
    normalized = os.path.normpath(working_directory)
    resolved = os.path.realpath(working_directory)
    if normalized != working_directory or resolved != working_directory:
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)
    try:
        status = os.stat(working_directory, follow_symlinks=False)
    except OSError:
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)
    if not stat.S_ISDIR(status.st_mode):
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)
    identity = (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
    )
    if any(type(value) is not int or value < 0 for value in identity):
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)
    return working_directory, identity


def _verify_working_directory_identity(
    working_directory: str,
    expected_identity: Tuple[int, int, int],
) -> None:
    try:
        status = os.stat(working_directory, follow_symlinks=False)
        observed = (
            status.st_dev,
            status.st_ino,
            stat.S_IFMT(status.st_mode),
        )
        resolved = os.path.realpath(working_directory)
    except OSError:
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)
    if (
        observed != expected_identity
        or resolved != working_directory
        or not stat.S_ISDIR(status.st_mode)
    ):
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)


def _open_working_directory_descriptor(
    working_directory: str,
    expected_identity: Tuple[int, int, int],
) -> int:
    required_flags = ("O_DIRECTORY", "O_NOFOLLOW")
    if any(not hasattr(os, name) for name in required_flags):
        _raise_guard_error(
            ExecutionGuardCode.WORKING_DIRECTORY_MECHANISM_UNAVAILABLE
        )
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor = None
    try:
        descriptor = os.open(working_directory, flags)
        status = os.fstat(descriptor)
    except OSError:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)
    observed = (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
    )
    if observed != expected_identity or not stat.S_ISDIR(status.st_mode):
        os.close(descriptor)
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)
    return descriptor


def _verify_working_directory_descriptor(
    descriptor: int,
    expected_identity: Tuple[int, int, int],
) -> None:
    try:
        status = os.fstat(descriptor)
    except OSError:
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)
    observed = (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
    )
    if observed != expected_identity or not stat.S_ISDIR(status.st_mode):
        _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)


def _working_directory_digest(
    snapshot: Tuple[str, Tuple[int, int, int]]
) -> str:
    working_directory, identity = snapshot
    return _length_prefixed_digest(
        WORKING_DIRECTORY_DIGEST_DOMAIN,
        (
            working_directory.encode("utf-8", "strict"),
            str(identity[0]).encode("ascii"),
            str(identity[1]).encode("ascii"),
            str(identity[2]).encode("ascii"),
        ),
    )


def argv_sha256(argv: Tuple[str, ...]) -> str:
    """Return the canonical length-prefixed digest of an exact argv tuple."""

    snapshot = _snapshot_argv(argv)
    return _length_prefixed_digest(
        ARGV_DIGEST_DOMAIN,
        tuple(value.encode("utf-8", "strict") for value in snapshot),
    )


def working_directory_sha256(working_directory: str) -> str:
    """Return the canonical-path and directory-identity receipt digest."""

    snapshot = _snapshot_working_directory(working_directory)
    return _working_directory_digest(snapshot)


def environment_sha256(environment: dict) -> str:
    """Return the order-independent digest of an explicit environment."""

    snapshot = _snapshot_environment(environment)
    payloads = tuple(
        encoded
        for key, value in snapshot
        for encoded in (
            key.encode("utf-8", "strict"),
            value.encode("utf-8", "strict"),
        )
    )
    return _length_prefixed_digest(ENVIRONMENT_DIGEST_DOMAIN, payloads)


def publication_source_binding_bytes(
    run_manifest_bytes: bytes,
    test_inventory_bytes: bytes,
) -> bytes:
    """Build the exact small guard source binding for Phase-D execution.

    The guard's ``source_sha256`` remains plain SHA-256 over its exact
    ``source_bytes`` input.  Passing this fixed record as that input binds the
    run manifest and test inventory without copying either potentially large
    byte string into the receipt protocol.
    """

    components = (run_manifest_bytes, test_inventory_bytes)
    for value in components:
        if type(value) is not bytes:
            raise TypeError("publication binding components must be exact bytes")
        if not value or len(value) > MAXIMUM_PUBLICATION_BINDING_COMPONENT_BYTES:
            raise ValueError("publication binding component exceeds its bound")
    framed = bytearray(PUBLICATION_SOURCE_BINDING_DOMAIN)
    framed.extend(b"\x00")
    for value in components:
        framed.extend(len(value).to_bytes(8, "big"))
        framed.extend(hashlib.sha256(value).digest())
    return bytes(framed)


_RSSObservationTuple = namedtuple(
    "_RSSObservationTuple",
    ("rss_bytes", "method", "exact_enforcement"),
    module=__name__,
)


class RSSObservation(_RSSObservationTuple):
    """One cumulative process-group peak supplied to the guard.

    ``rss_bytes`` is the cumulative peak through this observation, not an
    instantaneous point.  ``exact_enforcement`` may be true only when the
    probe continuously enforces the ceiling *and* retains an exact cumulative
    peak for a final post-exit observation.
    """

    __slots__ = ()

    def __new__(cls, rss_bytes, method, exact_enforcement):
        if cls is not RSSObservation:
            raise TypeError("RSS observation must be exact")
        result = super().__new__(
            cls,
            rss_bytes,
            method,
            exact_enforcement,
        )
        result._validate()
        return result

    @classmethod
    def _make(cls, iterable):
        if cls is not RSSObservation:
            raise TypeError("RSS observation must be exact")
        values = _bounded_iterable_tuple(
            iterable,
            exact_length=3,
            name="RSS observation",
        )
        return cls(*values)

    def _replace(self, **changes):
        unknown = set(changes).difference(self._fields)
        if unknown:
            raise ValueError("RSS replacement field is invalid")
        values = self._asdict()
        values.update(changes)
        return RSSObservation(**values)

    def _validate(self) -> None:
        if self.rss_bytes is not None:
            _validated_nonnegative_integer(
                self.rss_bytes, name="observed RSS bytes"
            )
        if type(self.method) is not PeakRSSMethod:
            raise TypeError("RSS method must be exact")
        if type(self.exact_enforcement) is not bool:
            raise TypeError("exact_enforcement must be an exact bool")
        if self.method is PeakRSSMethod.STDLIB_UNAVAILABLE:
            if self.rss_bytes is not None or self.exact_enforcement:
                raise ValueError("unavailable RSS observation is inconsistent")
        elif self.rss_bytes is None:
            raise ValueError("measured RSS observation requires bytes")
        if (
            self.method is PeakRSSMethod.LINUX_PROC_GROUP_SAMPLED
            and self.exact_enforcement
        ):
            raise ValueError("sampled RSS cannot certify exact enforcement")
        if (
            self.method is PeakRSSMethod.INJECTED_EXACT
            and not self.exact_enforcement
        ):
            raise ValueError("exact injected RSS must certify enforcement")


_ProcessOutputTuple = namedtuple(
    "_ProcessOutputTuple",
    ("stdout", "stderr", "stdout_eof", "stderr_eof"),
    module=__name__,
)


class ProcessOutput(_ProcessOutputTuple):
    """One bounded pair of output chunks from an injected process backend."""

    __slots__ = ()

    def __new__(
        cls,
        stdout=b"",
        stderr=b"",
        stdout_eof=False,
        stderr_eof=False,
    ):
        if cls is not ProcessOutput:
            raise TypeError("process output must be exact")
        result = super().__new__(
            cls,
            stdout,
            stderr,
            stdout_eof,
            stderr_eof,
        )
        result._validate()
        return result

    @classmethod
    def _make(cls, iterable):
        if cls is not ProcessOutput:
            raise TypeError("process output must be exact")
        values = _bounded_iterable_tuple(
            iterable,
            exact_length=4,
            name="process output",
        )
        return cls(*values)

    def _replace(self, **changes):
        unknown = set(changes).difference(self._fields)
        if unknown:
            raise ValueError("process-output replacement field is invalid")
        values = self._asdict()
        values.update(changes)
        return ProcessOutput(**values)

    def _validate(self) -> None:
        for name in ("stdout", "stderr"):
            value = getattr(self, name)
            if type(value) is not bytes:
                raise TypeError(name + " chunk must be exact bytes")
            if len(value) > MAXIMUM_READ_CHUNK_BYTES:
                raise ValueError(name + " chunk exceeds its byte ceiling")
        if type(self.stdout_eof) is not bool or type(self.stderr_eof) is not bool:
            raise TypeError("output EOF flags must be exact bools")


def _snapshot_rss_observation(value: object) -> RSSObservation:
    if type(value) is not RSSObservation or len(value) != 3:
        raise TypeError("RSS observation must be exact")
    try:
        return RSSObservation(
            value.rss_bytes,
            value.method,
            value.exact_enforcement,
        )
    except (AttributeError, IndexError, TypeError, ValueError):
        raise TypeError("RSS observation is invalid") from None


def _snapshot_process_output(value: object) -> ProcessOutput:
    if type(value) is not ProcessOutput or len(value) != 4:
        raise TypeError("process output must be exact")
    try:
        return ProcessOutput(
            value.stdout,
            value.stderr,
            value.stdout_eof,
            value.stderr_eof,
        )
    except (AttributeError, IndexError, TypeError, ValueError):
        raise TypeError("process output is invalid") from None


class MonotonicClock(Protocol):
    """Injectable monotonic clock surface."""

    def monotonic_ns(self) -> int:
        ...


class ResourceProbe(Protocol):
    """Injectable per-process-group RSS probe surface."""

    def observe(self, process_group_id: int) -> RSSObservation:
        ...


class ManagedExternalProcess(Protocol):
    """Injectable process and bounded-output surface."""

    @property
    def pid(self) -> int:
        ...

    @property
    def address_space_limit_bytes(self) -> int:
        ...

    @property
    def address_space_limit_method(self) -> AddressSpaceLimitMethod:
        ...

    def poll(self) -> Optional[int]:
        ...

    def pump(self, maximum_wait_nanoseconds: int) -> ProcessOutput:
        ...

    def terminate_process_group(self) -> None:
        ...

    def process_group_is_empty(self) -> bool:
        ...

    def close(self) -> None:
        ...


class ExternalProcessFactory(Protocol):
    """Injectable factory for a fresh process group."""

    def spawn(
        self,
        argv: Tuple[str, ...],
        *,
        working_directory: str,
        working_directory_descriptor: int,
        working_directory_identity: Tuple[int, int, int],
        environment: Mapping[str, str],
        address_space_limit_bytes: int,
    ) -> ManagedExternalProcess:
        ...


_ExecutionDependenciesTuple = namedtuple(
    "_ExecutionDependenciesTuple",
    ("clock", "process_factory", "resource_probe"),
    module=__name__,
)


class ExecutionDependencies(_ExecutionDependenciesTuple):
    """Explicit development injection surface for deterministic tests."""

    __slots__ = ()

    def __new__(cls, clock, process_factory, resource_probe):
        if cls is not ExecutionDependencies:
            raise TypeError("execution dependencies must be exact")
        return super().__new__(cls, clock, process_factory, resource_probe)

    @classmethod
    def _make(cls, iterable):
        if cls is not ExecutionDependencies:
            raise TypeError("execution dependencies must be exact")
        values = _bounded_iterable_tuple(
            iterable,
            exact_length=3,
            name="execution dependencies",
        )
        return cls(*values)

    def _replace(self, **changes):
        unknown = set(changes).difference(self._fields)
        if unknown:
            raise ValueError("dependency replacement field is invalid")
        values = self._asdict()
        values.update(changes)
        return ExecutionDependencies(**values)


_EXECUTION_RECEIPT_FIELDS = (
    "argv_sha256",
    "working_directory_sha256",
    "source_sha256",
    "environment_sha256",
    "source_binding_format",
    "clock_method",
    "execution_backend",
    "cwd_launch_method",
    "process_containment_method",
    "filesystem_confinement_method",
    "output_capture_method",
    "exit_status",
    "terminating_signal",
    "elapsed_monotonic_nanoseconds",
    "wall_limit_triggered",
    "measured_peak_rss_bytes",
    "peak_rss_units",
    "peak_rss_method",
    "peak_rss_enforcement_exact",
    "peak_rss_observation_finalized",
    "peak_rss_limit_triggered",
    "address_space_limit_bytes",
    "address_space_limit_method",
    "stdout_size_bytes",
    "stdout_sha256",
    "stdout_complete",
    "stderr_size_bytes",
    "stderr_sha256",
    "stderr_complete",
    "managed_process_group_quiescent",
    "wall_time_limit_nanoseconds",
    "peak_rss_limit_bytes",
    "output_limit_bytes",
    "status",
    "implementation_status",
    "decision_eligible",
)
_ExecutionReceiptTuple = namedtuple(
    "_ExecutionReceiptTuple",
    _EXECUTION_RECEIPT_FIELDS,
    module=__name__,
)


class ExecutionReceipt(_ExecutionReceiptTuple):
    """Slotless immutable hash-only receipt for one terminal execution."""

    __slots__ = ()

    def __new__(cls, *values: object, **named_values: object):
        if cls is not ExecutionReceipt:
            raise TypeError("execution receipt must be exact")
        result = super().__new__(cls, *values, **named_values)
        result._validate()
        return result

    @classmethod
    def _make(cls, iterable):
        if cls is not ExecutionReceipt:
            raise TypeError("execution receipt must be exact")
        values = _bounded_iterable_tuple(
            iterable,
            exact_length=len(_EXECUTION_RECEIPT_FIELDS),
            name="execution receipt",
        )
        return cls(*values)

    def _replace(self, **changes):
        unknown = set(changes).difference(self._fields)
        if unknown:
            raise ValueError("receipt replacement field is invalid")
        values = self._asdict()
        values.update(changes)
        return ExecutionReceipt(**values)

    @property
    def output_complete(self) -> bool:
        return self.stdout_complete and self.stderr_complete

    def _validate(self) -> None:
        for name in (
            "argv_sha256",
            "working_directory_sha256",
            "source_sha256",
            "environment_sha256",
            "stdout_sha256",
            "stderr_sha256",
        ):
            _validated_digest(getattr(self, name), name=name)
        for name in (
            "elapsed_monotonic_nanoseconds",
            "address_space_limit_bytes",
            "stdout_size_bytes",
            "stderr_size_bytes",
            "wall_time_limit_nanoseconds",
            "peak_rss_limit_bytes",
            "output_limit_bytes",
        ):
            _validated_nonnegative_integer(getattr(self, name), name=name)
        if self.measured_peak_rss_bytes is not None:
            _validated_nonnegative_integer(
                self.measured_peak_rss_bytes,
                name="measured_peak_rss_bytes",
            )
        for name in ("exit_status", "terminating_signal"):
            value = getattr(self, name)
            if value is not None:
                _validated_nonnegative_integer(value, name=name)
        if self.terminating_signal is not None and self.terminating_signal == 0:
            raise ValueError("terminating signal must be positive")
        if self.exit_status is not None and self.terminating_signal is not None:
            raise ValueError("exit status and signal are mutually exclusive")
        if type(self.peak_rss_units) is not PeakRSSUnits:
            raise TypeError("peak_rss_units must be exact")
        if type(self.peak_rss_method) is not PeakRSSMethod:
            raise TypeError("peak_rss_method must be exact")
        if type(self.peak_rss_enforcement_exact) is not bool:
            raise TypeError("peak_rss_enforcement_exact must be exact")
        if type(self.peak_rss_observation_finalized) is not bool:
            raise TypeError("peak_rss_observation_finalized must be exact")
        if type(self.address_space_limit_method) is not AddressSpaceLimitMethod:
            raise TypeError("address_space_limit_method must be exact")
        exact_enum_fields = (
            ("source_binding_format", SourceBindingFormat),
            ("clock_method", ClockMethod),
            ("execution_backend", ExecutionBackend),
            ("cwd_launch_method", CwdLaunchMethod),
            ("process_containment_method", ProcessContainmentMethod),
            (
                "filesystem_confinement_method",
                FilesystemConfinementMethod,
            ),
            ("output_capture_method", OutputCaptureMethod),
        )
        for name, expected_type in exact_enum_fields:
            if type(getattr(self, name)) is not expected_type:
                raise TypeError(name + " must be exact")
        for name in (
            "wall_limit_triggered",
            "stdout_complete",
            "stderr_complete",
            "managed_process_group_quiescent",
            "peak_rss_limit_triggered",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(name + " must be an exact bool")
        if not self.managed_process_group_quiescent:
            raise ValueError("managed process group must be quiescent")
        if (
            self.filesystem_confinement_method
            is not FilesystemConfinementMethod.NOT_PROVIDED
            or self.output_capture_method
            is not OutputCaptureMethod.BOUNDED_PIPE_SHA256
        ):
            raise ValueError("development containment methods are not fixed")
        if self.execution_backend is ExecutionBackend.INJECTED_TEST_BACKEND:
            if (
                self.clock_method is not ClockMethod.INJECTED_TEST_CLOCK
                or self.cwd_launch_method is not CwdLaunchMethod.INJECTED_TEST
                or self.process_containment_method
                is not ProcessContainmentMethod.INJECTED_TEST
            ):
                raise ValueError("injected execution method tuple is inconsistent")
        elif (
            self.clock_method is not ClockMethod.SYSTEM_MONOTONIC_NS
            or self.cwd_launch_method is not CwdLaunchMethod.LINUX_PROC_SELF_FD
            or self.process_containment_method
            is not ProcessContainmentMethod.POSIX_PROCESS_GROUP_ESCAPEABLE
            or self.peak_rss_method is PeakRSSMethod.INJECTED_EXACT
        ):
            raise ValueError("stdlib execution method tuple is inconsistent")
        if type(self.status) is not ExecutionStatus:
            raise TypeError("execution status must be exact")
        if (
            type(self.implementation_status) is not str
            or self.implementation_status
            != EXECUTION_GUARD_IMPLEMENTATION_STATUS
        ):
            raise ValueError("receipt implementation status is not fixed")
        if type(self.decision_eligible) is not bool:
            raise TypeError("decision_eligible must be an exact bool")
        if self.decision_eligible:
            raise ValueError("development receipt cannot be decision eligible")
        if self.wall_time_limit_nanoseconds != WALL_TIME_LIMIT_NANOSECONDS:
            raise ValueError("wall-time ceiling is not the fixed value")
        if self.peak_rss_limit_bytes != PEAK_RSS_LIMIT_BYTES:
            raise ValueError("peak-RSS ceiling is not the fixed value")
        if self.output_limit_bytes != MAXIMUM_CAPTURED_OUTPUT_BYTES:
            raise ValueError("output ceiling is not the fixed value")
        if self.measured_peak_rss_bytes is None:
            if self.peak_rss_units is not PeakRSSUnits.UNAVAILABLE:
                raise ValueError("unmeasured RSS must use unavailable units")
            if self.peak_rss_method is not PeakRSSMethod.STDLIB_UNAVAILABLE:
                raise ValueError("unmeasured RSS must use unavailable method")
            if self.peak_rss_enforcement_exact:
                raise ValueError("unmeasured RSS cannot be exact")
            if self.peak_rss_observation_finalized:
                raise ValueError("unmeasured RSS cannot have a final observation")
        elif self.peak_rss_units is not PeakRSSUnits.BYTES:
            raise ValueError("measured RSS must use byte units")
        elif self.peak_rss_method is PeakRSSMethod.STDLIB_UNAVAILABLE:
            raise ValueError("measured RSS requires an observed method")
        if (
            self.peak_rss_method is PeakRSSMethod.LINUX_PROC_GROUP_SAMPLED
            and self.peak_rss_enforcement_exact
        ):
            raise ValueError("sampled RSS cannot certify exact enforcement")
        if (
            self.peak_rss_enforcement_exact
            and not self.peak_rss_observation_finalized
        ):
            raise ValueError("exact RSS requires a final cumulative observation")
        if (
            self.status is ExecutionStatus.PASS
            and (
                self.exit_status != 0
                or self.terminating_signal is not None
                or not self.peak_rss_enforcement_exact
                or self.measured_peak_rss_bytes is None
                or self.measured_peak_rss_bytes > PEAK_RSS_LIMIT_BYTES
                or self.peak_rss_method is not PeakRSSMethod.INJECTED_EXACT
                or self.elapsed_monotonic_nanoseconds
                > WALL_TIME_LIMIT_NANOSECONDS
                or not self.output_complete
            )
        ):
            raise ValueError("PASS receipt is inconsistent")
        if (
            self.status is ExecutionStatus.MEASUREMENT_UNAVAILABLE
            and self.peak_rss_enforcement_exact
        ):
            raise ValueError("unavailable measurement cannot be exact")
        if self.status is ExecutionStatus.NONZERO_EXIT:
            if self.exit_status is None or self.exit_status == 0:
                raise ValueError("nonzero-exit receipt is inconsistent")
        if self.status is ExecutionStatus.SIGNALLED:
            if self.terminating_signal is None:
                raise ValueError("signalled receipt is inconsistent")
        if (
            self.status is ExecutionStatus.TIMEOUT
            and self.elapsed_monotonic_nanoseconds
            < WALL_TIME_LIMIT_NANOSECONDS
        ):
            raise ValueError("timeout receipt is inconsistent")
        if self.wall_limit_triggered != (
            self.status is ExecutionStatus.TIMEOUT
        ):
            raise ValueError("wall-limit trigger state is inconsistent")
        if self.status is ExecutionStatus.PEAK_RSS_LIMIT_EXCEEDED:
            if (
                self.measured_peak_rss_bytes is None
                or self.measured_peak_rss_bytes <= PEAK_RSS_LIMIT_BYTES
            ):
                raise ValueError("peak-RSS breach receipt is inconsistent")
        if self.peak_rss_limit_triggered != (
            self.status is ExecutionStatus.PEAK_RSS_LIMIT_EXCEEDED
        ):
            raise ValueError("peak-RSS trigger state is inconsistent")
        if (
            self.status is ExecutionStatus.OUTPUT_LIMIT_EXCEEDED
            and (
                self.stdout_size_bytes + self.stderr_size_bytes
                != self.output_limit_bytes
                or self.output_complete
            )
        ):
            raise ValueError("output breach receipt is inconsistent")
        if self.stdout_size_bytes + self.stderr_size_bytes > self.output_limit_bytes:
            raise ValueError("captured output exceeds its receipt ceiling")


def validate_execution_receipt(value: object) -> ExecutionReceipt:
    """Return a trusted immutable snapshot of one exact receipt.

    Exact-type checking alone is not a Python trust boundary because low-level
    tuple construction can bypass a tuple subclass's ``__new__`` method.  All
    consumers, including a future publisher, must call this function before
    relying on any receipt field.
    """

    if (
        type(value) is not ExecutionReceipt
        or len(value) != len(_EXECUTION_RECEIPT_FIELDS)
    ):
        raise TypeError("execution receipt must be exact")
    try:
        fields = tuple(
            getattr(value, name) for name in _EXECUTION_RECEIPT_FIELDS
        )
        return ExecutionReceipt(*fields)
    except (AttributeError, IndexError, TypeError, ValueError):
        raise TypeError("execution receipt is invalid") from None


class _SystemClock:
    def monotonic_ns(self) -> int:
        return time.monotonic_ns()


class _PortableResourceProbe:
    """Best-effort stdlib probe that never claims exact RSS enforcement."""

    def observe(self, process_group_id: int) -> RSSObservation:
        if not sys.platform.startswith("linux") or not os.path.isdir("/proc"):
            return RSSObservation(
                None,
                PeakRSSMethod.STDLIB_UNAVAILABLE,
                False,
            )
        measured = _linux_process_group_rss_bytes(process_group_id)
        if measured is None:
            return RSSObservation(
                None,
                PeakRSSMethod.STDLIB_UNAVAILABLE,
                False,
            )
        return RSSObservation(
            measured,
            PeakRSSMethod.LINUX_PROC_GROUP_SAMPLED,
            False,
        )


def _linux_process_group_rss_bytes(
    process_group_id: int,
) -> Optional[int]:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        entries = tuple(os.scandir("/proc"))
    except (OSError, ValueError):
        return None
    if type(page_size) is not int or page_size <= 0:
        return None
    total_pages = 0
    found = False
    for entry in entries:
        if not entry.name.isdigit():
            continue
        base = "/proc/" + entry.name
        try:
            with open(base + "/stat", "rb") as handle:
                process_stat = handle.read(64 * 1024)
            closing = process_stat.rfind(b")")
            if closing < 0:
                continue
            fields = process_stat[closing + 2 :].split()
            if len(fields) < 3 or int(fields[2]) != process_group_id:
                continue
            with open(base + "/statm", "rb") as handle:
                memory_fields = handle.read(4096).split()
            if len(memory_fields) < 2:
                continue
            resident_pages = int(memory_fields[1])
        except (FileNotFoundError, PermissionError, OSError, ValueError):
            continue
        if resident_pages < 0:
            continue
        total_pages += resident_pages
        found = True
    return total_pages * page_size if found else None


def _address_space_limit() -> Tuple[int, AddressSpaceLimitMethod]:
    # RLIMIT_AS constrains virtual address space rather than resident memory,
    # and preexec_fn can deadlock before the wall-time loop in a multithreaded
    # parent.  The stdlib backend therefore makes no address-space claim.
    return ADDRESS_SPACE_LIMIT_BYTES, AddressSpaceLimitMethod.UNAVAILABLE


def _posix_process_group_is_empty(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return True
    except (OSError, PermissionError):
        return False
    return False


class _PosixManagedProcess:
    def __init__(
        self,
        process: subprocess.Popen,
        *,
        address_space_limit_bytes: int,
        address_space_limit_method: AddressSpaceLimitMethod,
    ) -> None:
        if process.stdout is None or process.stderr is None:
            _raise_guard_error(ExecutionGuardCode.SPAWN_FAILED)
        self._process = process
        self._address_space_limit_bytes = address_space_limit_bytes
        self._address_space_limit_method = address_space_limit_method
        self._selector = selectors.DefaultSelector()
        self._selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        self._selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        self._stdout_eof = False
        self._stderr_eof = False
        self._closed = False

    @property
    def pid(self) -> int:
        return self._process.pid

    @property
    def address_space_limit_bytes(self) -> int:
        return self._address_space_limit_bytes

    @property
    def address_space_limit_method(self) -> AddressSpaceLimitMethod:
        return self._address_space_limit_method

    def poll(self) -> Optional[int]:
        return self._process.poll()

    def pump(self, maximum_wait_nanoseconds: int) -> ProcessOutput:
        if self._closed:
            _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)
        timeout = maximum_wait_nanoseconds / 1_000_000_000
        chunks = {"stdout": b"", "stderr": b""}
        try:
            events = self._selector.select(timeout=timeout)
            for key, _mask in events:
                chunk = os.read(key.fileobj.fileno(), MAXIMUM_READ_CHUNK_BYTES)
                stream = key.data
                if chunk:
                    chunks[stream] = chunk
                else:
                    self._selector.unregister(key.fileobj)
                    if stream == "stdout":
                        self._stdout_eof = True
                    else:
                        self._stderr_eof = True
        except (OSError, ValueError):
            _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)
        return ProcessOutput(
            stdout=chunks["stdout"],
            stderr=chunks["stderr"],
            stdout_eof=self._stdout_eof,
            stderr_eof=self._stderr_eof,
        )

    def terminate_process_group(self) -> None:
        failed = False
        for chosen_signal in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(self._process.pid, chosen_signal)
            except ProcessLookupError:
                break
            except (OSError, PermissionError):
                failed = True
                break
        try:
            self._process.wait(timeout=2.0)
        except (subprocess.TimeoutExpired, OSError):
            failed = True
        if self._process.poll() is None:
            failed = True
        deadline = time.monotonic() + 2.0
        while not self.process_group_is_empty() and time.monotonic() < deadline:
            try:
                os.killpg(self._process.pid, signal.SIGKILL)
            except ProcessLookupError:
                break
            except (OSError, PermissionError):
                failed = True
                break
            time.sleep(0.01)
        if not self.process_group_is_empty():
            failed = True
        if failed:
            _raise_guard_error(ExecutionGuardCode.PROCESS_TERMINATION_FAILED)

    def process_group_is_empty(self) -> bool:
        return _posix_process_group_is_empty(self._process.pid)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._selector.close()
        if self._process.stdout is not None:
            self._process.stdout.close()
        if self._process.stderr is not None:
            self._process.stderr.close()


class _PosixProcessFactory:
    def spawn(
        self,
        argv: Tuple[str, ...],
        *,
        working_directory: str,
        working_directory_descriptor: int,
        working_directory_identity: Tuple[int, int, int],
        environment: Mapping[str, str],
        address_space_limit_bytes: int,
    ) -> ManagedExternalProcess:
        del working_directory, working_directory_identity
        if not sys.platform.startswith("linux"):
            _raise_guard_error(
                ExecutionGuardCode.WORKING_DIRECTORY_MECHANISM_UNAVAILABLE
            )
        if (
            type(working_directory_descriptor) is not int
            or working_directory_descriptor < 0
        ):
            _raise_guard_error(ExecutionGuardCode.WORKING_DIRECTORY_INVALID)
        limit, limit_method = _address_space_limit()
        limit = min(limit, address_space_limit_bytes)
        descriptor_cwd = "/proc/self/fd/{}".format(
            working_directory_descriptor
        )
        try:
            process = subprocess.Popen(
                argv,
                cwd=descriptor_cwd,
                env=dict(environment),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                pass_fds=(working_directory_descriptor,),
                start_new_session=True,
                shell=False,
            )
        except (OSError, ValueError, subprocess.SubprocessError):
            _raise_guard_error(ExecutionGuardCode.SPAWN_FAILED)
        try:
            return _PosixManagedProcess(
                process,
                address_space_limit_bytes=limit,
                address_space_limit_method=limit_method,
            )
        except Exception:
            failed = False
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except (OSError, PermissionError):
                failed = True
            try:
                process.wait(timeout=2.0)
            except (subprocess.TimeoutExpired, OSError):
                failed = True
            deadline = time.monotonic() + 2.0
            while (
                not _posix_process_group_is_empty(process.pid)
                and time.monotonic() < deadline
            ):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    break
                except (OSError, PermissionError):
                    failed = True
                    break
                time.sleep(0.01)
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        failed = True
            if (
                failed
                or process.poll() is None
                or not _posix_process_group_is_empty(process.pid)
            ):
                _raise_guard_error(
                    ExecutionGuardCode.PROCESS_TERMINATION_FAILED
                )
            _raise_guard_error(ExecutionGuardCode.SPAWN_FAILED)


_DEFAULT_DEPENDENCIES = ExecutionDependencies(
    clock=_SystemClock(),
    process_factory=_PosixProcessFactory(),
    resource_probe=_PortableResourceProbe(),
)


class _OutputCommitment:
    def __init__(self) -> None:
        self.digest = hashlib.sha256()
        self.size = 0

    def consume(self, chunk: bytes, *, remaining: int) -> bool:
        admitted = chunk[:remaining]
        self.digest.update(admitted)
        self.size += len(admitted)
        return len(admitted) != len(chunk)


def _clock_value(clock: MonotonicClock) -> int:
    try:
        value = clock.monotonic_ns()
    except Exception:
        _raise_guard_error(ExecutionGuardCode.CLOCK_INVALID)
    if type(value) is not int or value < 0:
        _raise_guard_error(ExecutionGuardCode.CLOCK_INVALID)
    return value


def _process_value(process: ManagedExternalProcess, name: str) -> object:
    try:
        return getattr(process, name)
    except Exception:
        _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)


def _poll_process(process: ManagedExternalProcess) -> Optional[int]:
    try:
        returncode = process.poll()
    except Exception:
        _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)
    if returncode is not None and type(returncode) is not int:
        _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)
    if returncode is not None and (
        returncode > 255 or returncode <= -signal.NSIG
    ):
        _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)
    return returncode


def _terminate_process(process: ManagedExternalProcess) -> int:
    try:
        process.terminate_process_group()
    except ExecutionGuardError:
        raise
    except Exception:
        _raise_guard_error(ExecutionGuardCode.PROCESS_TERMINATION_FAILED)
    returncode = _poll_process(process)
    if returncode is None:
        _raise_guard_error(ExecutionGuardCode.PROCESS_TERMINATION_FAILED)
    try:
        group_empty = process.process_group_is_empty()
    except Exception:
        _raise_guard_error(ExecutionGuardCode.PROCESS_TERMINATION_FAILED)
    if type(group_empty) is not bool or not group_empty:
        _raise_guard_error(ExecutionGuardCode.PROCESS_TERMINATION_FAILED)
    return returncode


def _process_group_is_empty(process: ManagedExternalProcess) -> bool:
    try:
        result = process.process_group_is_empty()
    except Exception:
        _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)
    if type(result) is not bool:
        _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)
    return result


def _exit_fields(returncode: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
    if returncode is None:
        return None, None
    if returncode < 0:
        return None, -returncode
    return returncode, None


def _receipt_status(
    *,
    forced_status: Optional[ExecutionStatus],
    returncode: int,
    exact_enforcement: bool,
) -> ExecutionStatus:
    if forced_status is not None:
        return forced_status
    if returncode < 0:
        return ExecutionStatus.SIGNALLED
    if returncode != 0:
        return ExecutionStatus.NONZERO_EXIT
    if not exact_enforcement:
        return ExecutionStatus.MEASUREMENT_UNAVAILABLE
    return ExecutionStatus.PASS


def execute_external_argv(
    argv: Tuple[str, ...],
    *,
    working_directory: str,
    environment: dict,
    source_bytes: bytes,
    source_binding_format: SourceBindingFormat = (
        SourceBindingFormat.OPAQUE_EXACT_BYTES
    ),
    dependencies: Optional[ExecutionDependencies] = None,
) -> ExecutionReceipt:
    """Execute one explicit argv and return a non-publication receipt.

    ``environment`` is the complete child environment; the parent environment
    is never merged into it.  ``source_bytes`` are receipt binding bytes only
    and are not sent to the child.  The production backend cannot produce a
    decision-capable ``PASS`` because stdlib RSS enforcement is not exact.
    """

    argv_snapshot = _snapshot_argv(argv)
    environment_snapshot = _snapshot_environment(environment)
    source_snapshot = _snapshot_source(source_bytes)
    if type(source_binding_format) is not SourceBindingFormat:
        _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
    working_directory_snapshot = _snapshot_working_directory(
        working_directory
    )
    working_directory_path, working_directory_identity = (
        working_directory_snapshot
    )
    if dependencies is None:
        chosen_dependencies = _DEFAULT_DEPENDENCIES
        clock_method = ClockMethod.SYSTEM_MONOTONIC_NS
        execution_backend = ExecutionBackend.STDLIB_SUBPROCESS
        cwd_launch_method = CwdLaunchMethod.LINUX_PROC_SELF_FD
        process_containment_method = (
            ProcessContainmentMethod.POSIX_PROCESS_GROUP_ESCAPEABLE
        )
    elif type(dependencies) is ExecutionDependencies:
        chosen_dependencies = dependencies
        clock_method = ClockMethod.INJECTED_TEST_CLOCK
        execution_backend = ExecutionBackend.INJECTED_TEST_BACKEND
        cwd_launch_method = CwdLaunchMethod.INJECTED_TEST
        process_containment_method = ProcessContainmentMethod.INJECTED_TEST
    else:
        _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)

    argv_digest = _length_prefixed_digest(
        ARGV_DIGEST_DOMAIN,
        tuple(value.encode("utf-8", "strict") for value in argv_snapshot),
    )
    cwd_digest = _working_directory_digest(working_directory_snapshot)
    environment_payloads = tuple(
        encoded
        for key, value in environment_snapshot
        for encoded in (
            key.encode("utf-8", "strict"),
            value.encode("utf-8", "strict"),
        )
    )
    environment_digest = _length_prefixed_digest(
        ENVIRONMENT_DIGEST_DOMAIN,
        environment_payloads,
    )
    source_digest = hashlib.sha256(source_snapshot).hexdigest()
    child_environment = MappingProxyType(dict(environment_snapshot))
    try:
        if len(chosen_dependencies) != 3:
            _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)
        clock = chosen_dependencies.clock
        process_factory = chosen_dependencies.process_factory
        resource_probe = chosen_dependencies.resource_probe
    except ExecutionGuardError:
        raise
    except Exception:
        _raise_guard_error(ExecutionGuardCode.INPUT_INVALID)

    start = _clock_value(clock)
    previous_clock = start
    process = None
    forced_status = None
    returncode = None
    stdout = _OutputCommitment()
    stderr = _OutputCommitment()
    stdout_eof = False
    stderr_eof = False
    peak_rss = None
    peak_method = PeakRSSMethod.STDLIB_UNAVAILABLE
    exact_enforcement = True
    final_rss_observation_complete = False
    final_rss_observation_finalized = False
    observed_terminal_returncode = None
    working_directory_descriptor = _open_working_directory_descriptor(
        working_directory_path,
        working_directory_identity,
    )
    try:
        _verify_working_directory_identity(
            working_directory_path,
            working_directory_identity,
        )
        _verify_working_directory_descriptor(
            working_directory_descriptor,
            working_directory_identity,
        )
        try:
            process = process_factory.spawn(
                argv_snapshot,
                working_directory=working_directory_path,
                working_directory_descriptor=working_directory_descriptor,
                working_directory_identity=working_directory_identity,
                environment=child_environment,
                address_space_limit_bytes=ADDRESS_SPACE_LIMIT_BYTES,
            )
        except ExecutionGuardError:
            raise
        except Exception:
            _raise_guard_error(ExecutionGuardCode.SPAWN_FAILED)
        _verify_working_directory_identity(
            working_directory_path,
            working_directory_identity,
        )
        _verify_working_directory_descriptor(
            working_directory_descriptor,
            working_directory_identity,
        )
        pid = _process_value(process, "pid")
        address_limit = _process_value(
            process, "address_space_limit_bytes"
        )
        address_method = _process_value(
            process, "address_space_limit_method"
        )
        if type(pid) is not int or pid <= 0:
            _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)
        if (
            type(address_limit) is not int
            or address_limit <= 0
            or address_limit > ADDRESS_SPACE_LIMIT_BYTES
        ):
            _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)
        if type(address_method) is not AddressSpaceLimitMethod:
            _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)

        while True:
            now = _clock_value(clock)
            if now < previous_clock:
                _raise_guard_error(ExecutionGuardCode.CLOCK_INVALID)
            previous_clock = now
            elapsed = now - start
            returncode = _poll_process(process)
            if observed_terminal_returncode is not None:
                if returncode != observed_terminal_returncode:
                    _raise_guard_error(
                        ExecutionGuardCode.PROCESS_PROTOCOL_INVALID
                    )
            elif returncode is not None:
                observed_terminal_returncode = returncode
            active = returncode is None or not (stdout_eof and stderr_eof)
            if elapsed > WALL_TIME_LIMIT_NANOSECONDS:
                forced_status = ExecutionStatus.TIMEOUT
                if active:
                    returncode = _terminate_process(process)
                break
            if active and elapsed == WALL_TIME_LIMIT_NANOSECONDS:
                forced_status = ExecutionStatus.TIMEOUT
                returncode = _terminate_process(process)
                break
            if returncode is not None:
                if not _process_group_is_empty(process):
                    forced_status = (
                        ExecutionStatus.PROCESS_GROUP_NOT_QUIESCENT
                    )
                    returncode = _terminate_process(process)
                    break
                if not final_rss_observation_complete:
                    final_rss_observation_complete = True
                    try:
                        final_observation = _snapshot_rss_observation(
                            resource_probe.observe(pid)
                        )
                    except Exception:
                        exact_enforcement = False
                        forced_status = (
                            ExecutionStatus.MEASUREMENT_UNAVAILABLE
                        )
                        break
                    if (
                        final_observation.method
                        is PeakRSSMethod.STDLIB_UNAVAILABLE
                        or not final_observation.exact_enforcement
                    ):
                        exact_enforcement = False
                        forced_status = (
                            ExecutionStatus.MEASUREMENT_UNAVAILABLE
                        )
                        break
                    if peak_method is PeakRSSMethod.STDLIB_UNAVAILABLE:
                        peak_method = final_observation.method
                    elif peak_method is not final_observation.method:
                        exact_enforcement = False
                        forced_status = (
                            ExecutionStatus.MEASUREMENT_UNAVAILABLE
                        )
                        break
                    assert final_observation.rss_bytes is not None
                    if (
                        peak_rss is not None
                        and final_observation.rss_bytes < peak_rss
                    ):
                        exact_enforcement = False
                        forced_status = (
                            ExecutionStatus.MEASUREMENT_UNAVAILABLE
                        )
                        break
                    if (
                        peak_rss is None
                        or final_observation.rss_bytes > peak_rss
                    ):
                        peak_rss = final_observation.rss_bytes
                    final_rss_observation_finalized = True
                    if final_observation.rss_bytes > PEAK_RSS_LIMIT_BYTES:
                        forced_status = (
                            ExecutionStatus.PEAK_RSS_LIMIT_EXCEEDED
                        )
                        break
                if stdout_eof and stderr_eof:
                    break
            if returncode is None:
                try:
                    observation = _snapshot_rss_observation(
                        resource_probe.observe(pid)
                    )
                except Exception:
                    exact_enforcement = False
                    forced_status = ExecutionStatus.MEASUREMENT_UNAVAILABLE
                    returncode = _terminate_process(process)
                    break
                if observation.method is PeakRSSMethod.STDLIB_UNAVAILABLE:
                    exact_enforcement = False
                    forced_status = ExecutionStatus.MEASUREMENT_UNAVAILABLE
                    returncode = _terminate_process(process)
                    break
                else:
                    if peak_method is PeakRSSMethod.STDLIB_UNAVAILABLE:
                        peak_method = observation.method
                    elif peak_method is not observation.method:
                        exact_enforcement = False
                    exact_enforcement = (
                        exact_enforcement and observation.exact_enforcement
                    )
                    assert observation.rss_bytes is not None
                    if (
                        peak_rss is not None
                        and observation.rss_bytes < peak_rss
                    ):
                        exact_enforcement = False
                        forced_status = (
                            ExecutionStatus.MEASUREMENT_UNAVAILABLE
                        )
                        returncode = _terminate_process(process)
                        break
                    if peak_rss is None or observation.rss_bytes > peak_rss:
                        peak_rss = observation.rss_bytes
                    if observation.rss_bytes > PEAK_RSS_LIMIT_BYTES:
                        forced_status = (
                            ExecutionStatus.PEAK_RSS_LIMIT_EXCEEDED
                        )
                        returncode = _terminate_process(process)
                        break
                    if not observation.exact_enforcement:
                        exact_enforcement = False
                        forced_status = (
                            ExecutionStatus.MEASUREMENT_UNAVAILABLE
                        )
                        returncode = _terminate_process(process)
                        break

            remaining_time = max(
                0,
                WALL_TIME_LIMIT_NANOSECONDS - elapsed,
            )
            wait = min(_POLL_INTERVAL_NANOSECONDS, remaining_time)
            try:
                output = _snapshot_process_output(process.pump(wait))
            except ExecutionGuardError:
                raise
            except Exception:
                _raise_guard_error(
                    ExecutionGuardCode.PROCESS_PROTOCOL_INVALID
                )
            if stdout_eof and (
                output.stdout or not output.stdout_eof
            ):
                _raise_guard_error(
                    ExecutionGuardCode.PROCESS_PROTOCOL_INVALID
                )
            if stderr_eof and (
                output.stderr or not output.stderr_eof
            ):
                _raise_guard_error(
                    ExecutionGuardCode.PROCESS_PROTOCOL_INVALID
                )
            stdout_eof = stdout_eof or output.stdout_eof
            stderr_eof = stderr_eof or output.stderr_eof
            remaining_output = max(
                0,
                MAXIMUM_CAPTURED_OUTPUT_BYTES - stdout.size - stderr.size,
            )
            overflow = stdout.consume(
                output.stdout,
                remaining=remaining_output,
            )
            remaining_output = max(
                0,
                MAXIMUM_CAPTURED_OUTPUT_BYTES - stdout.size - stderr.size,
            )
            overflow = (
                stderr.consume(output.stderr, remaining=remaining_output)
                or overflow
            )
            if overflow:
                forced_status = ExecutionStatus.OUTPUT_LIMIT_EXCEEDED
                returncode = _terminate_process(process)
                break

        if not final_rss_observation_complete:
            final_rss_observation_complete = True
            try:
                final_observation = _snapshot_rss_observation(
                    resource_probe.observe(pid)
                )
            except Exception:
                exact_enforcement = False
            else:
                final_observation_valid = True
                if (
                    final_observation.method
                    is PeakRSSMethod.STDLIB_UNAVAILABLE
                    or not final_observation.exact_enforcement
                ):
                    exact_enforcement = False
                    final_observation_valid = False
                else:
                    if peak_method is PeakRSSMethod.STDLIB_UNAVAILABLE:
                        peak_method = final_observation.method
                    elif peak_method is not final_observation.method:
                        exact_enforcement = False
                        final_observation_valid = False
                    assert final_observation.rss_bytes is not None
                    if (
                        peak_rss is not None
                        and final_observation.rss_bytes < peak_rss
                    ):
                        exact_enforcement = False
                        final_observation_valid = False
                    if (
                        peak_rss is None
                        or final_observation.rss_bytes > peak_rss
                    ):
                        peak_rss = final_observation.rss_bytes
                    if (
                        forced_status is None
                        and final_observation.rss_bytes
                        > PEAK_RSS_LIMIT_BYTES
                    ):
                        forced_status = (
                            ExecutionStatus.PEAK_RSS_LIMIT_EXCEEDED
                        )
                    if final_observation_valid:
                        final_rss_observation_finalized = True

        end = _clock_value(clock)
        if end < previous_clock:
            _raise_guard_error(ExecutionGuardCode.CLOCK_INVALID)
        elapsed = end - start
        if returncode is None:
            _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)
        exit_status, terminating_signal = _exit_fields(returncode)
        if peak_rss is None:
            peak_units = PeakRSSUnits.UNAVAILABLE
            peak_method = PeakRSSMethod.STDLIB_UNAVAILABLE
            exact_enforcement = False
        else:
            peak_units = PeakRSSUnits.BYTES
        status = _receipt_status(
            forced_status=forced_status,
            returncode=returncode,
            exact_enforcement=exact_enforcement,
        )
        receipt = ExecutionReceipt(
            argv_sha256=argv_digest,
            working_directory_sha256=cwd_digest,
            source_sha256=source_digest,
            environment_sha256=environment_digest,
            source_binding_format=source_binding_format,
            clock_method=clock_method,
            execution_backend=execution_backend,
            cwd_launch_method=cwd_launch_method,
            process_containment_method=process_containment_method,
            filesystem_confinement_method=(
                FilesystemConfinementMethod.NOT_PROVIDED
            ),
            output_capture_method=OutputCaptureMethod.BOUNDED_PIPE_SHA256,
            exit_status=exit_status,
            terminating_signal=terminating_signal,
            elapsed_monotonic_nanoseconds=elapsed,
            wall_limit_triggered=(status is ExecutionStatus.TIMEOUT),
            measured_peak_rss_bytes=peak_rss,
            peak_rss_units=peak_units,
            peak_rss_method=peak_method,
            peak_rss_enforcement_exact=exact_enforcement,
            peak_rss_observation_finalized=(
                final_rss_observation_finalized
            ),
            peak_rss_limit_triggered=(
                status is ExecutionStatus.PEAK_RSS_LIMIT_EXCEEDED
            ),
            address_space_limit_bytes=address_limit,
            address_space_limit_method=address_method,
            stdout_size_bytes=stdout.size,
            stdout_sha256=stdout.digest.hexdigest(),
            stdout_complete=stdout_eof,
            stderr_size_bytes=stderr.size,
            stderr_sha256=stderr.digest.hexdigest(),
            stderr_complete=stderr_eof,
            managed_process_group_quiescent=True,
            wall_time_limit_nanoseconds=WALL_TIME_LIMIT_NANOSECONDS,
            peak_rss_limit_bytes=PEAK_RSS_LIMIT_BYTES,
            output_limit_bytes=MAXIMUM_CAPTURED_OUTPUT_BYTES,
            status=status,
            implementation_status=EXECUTION_GUARD_IMPLEMENTATION_STATUS,
            decision_eligible=False,
        )
        return validate_execution_receipt(receipt)
    except Exception as execution_error:
        if process is not None:
            raw_returncode = None
            try:
                raw_returncode = process.poll()
            except Exception:
                pass
            must_terminate = type(raw_returncode) is not int
            if not must_terminate:
                try:
                    group_empty = process.process_group_is_empty()
                    must_terminate = type(group_empty) is not bool or not group_empty
                except Exception:
                    must_terminate = True
            if must_terminate:
                try:
                    process.terminate_process_group()
                except Exception:
                    _raise_guard_error(
                        ExecutionGuardCode.PROCESS_TERMINATION_FAILED
                    )
                try:
                    final_returncode = process.poll()
                    final_group_empty = process.process_group_is_empty()
                except Exception:
                    _raise_guard_error(
                        ExecutionGuardCode.PROCESS_TERMINATION_FAILED
                    )
                if (
                    type(final_returncode) is not int
                    or type(final_group_empty) is not bool
                    or not final_group_empty
                ):
                    _raise_guard_error(
                        ExecutionGuardCode.PROCESS_TERMINATION_FAILED
                    )
        if isinstance(execution_error, ExecutionGuardError):
            raise
        _raise_guard_error(ExecutionGuardCode.PROCESS_PROTOCOL_INVALID)
    finally:
        active_error = sys.exc_info()[0] is not None
        close_failed = False
        if process is not None:
            try:
                process.close()
            except Exception:
                close_failed = True
        try:
            os.close(working_directory_descriptor)
        except OSError:
            close_failed = True
        # A termination/protocol failure has higher diagnostic priority;
        # otherwise descriptor-close failure blocks a receipt.
        if close_failed and not active_error:
            _raise_guard_error(ExecutionGuardCode.PROCESS_CLOSE_FAILED)
