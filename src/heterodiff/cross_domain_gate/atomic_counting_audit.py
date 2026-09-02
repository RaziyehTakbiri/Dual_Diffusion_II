"""Independent, standard-library audit orchestration for the counting gate.

This module is intentionally a separate process boundary from the evidence
publisher.  It imports neither NumPy nor Torch and never imports the publisher,
trainer, worker, or executor.  It launches the exact frozen test commands and a
fresh pinned audit worker, validates their bounded canonical outputs, and only
then assembles the exact audit JSON consumed by the publisher.

Procedural separation is not an authentication or trust root.  The operator is
still responsible for arranging an actually independent review and preserving
the reviewed source and inputs.  This code creates no receipt, evidence bundle,
gate decision, or manuscript claim.

For a genuinely NumPy/Torch-free parent interpreter, invoke the sibling
``atomic_counting_audit_runner.py`` by filesystem path.  Importing any module
through ``heterodiff`` may execute the package's unrelated eager imports first.

Every admitted child interpreter is content-bound to a frozen resolved regular
target.  The declared virtual-environment launcher may be a symlink so venv
semantics are preserved, but its final target, link custody, digest, size, and
version are checked before and after each spawn.  Audit JSON exposes only the
privacy-safe implementation/version/digest/size identity, never a host path.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Sequence, Tuple, Union


PathLike = Union[str, os.PathLike]

GATE_ID = "heterodiff-cross-domain-atomic-counting-reference-gate-v1"
AUDIT_SCHEMA = "heterodiff-cross-domain-independent-audit-v1"
AUDIT_WORKER_SCHEMA = "heterodiff-cross-domain-audit-worker-v1"
RUN_RECEIPT_SCHEMA = "heterodiff-cross-domain-completed-run-receipt-v1"
REVIEW_ATTESTATION_SCHEMA = (
    "heterodiff-cross-domain-read-only-review-attestation-v1"
)

MAX_CAPTURE_BYTES = 2 * 1024 * 1024
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_CHECKPOINT_BYTES = 64 * 1024 * 1024
MAX_EXECUTABLE_BYTES = 8 * 1024 * 1024
TEST_TIMEOUT_SECONDS = 240.0
WORKER_TIMEOUT_SECONDS = 180.0
INTERPRETER_PROBE_TIMEOUT_SECONDS = 10.0

BASE_SKIP_REASON = (
    "cross-domain atomic-counting gate requires the pinned Torch extra"
)

BASE_SKIP_MANIFEST = (
    (
        1,
        "tests/unit/test_atomic_counting_reference_torch.py",
        BASE_SKIP_REASON,
    ),
    (
        1,
        "tests/integration/test_cross_domain_atomic_counting_training_torch.py",
        BASE_SKIP_REASON,
    ),
)

EXPECTED_BASE_PASSED = 184
EXPECTED_PINNED_PASSED = 292

BOOTSTRAP_SCHEMA = "heterodiff-atomic-counting-source-bootstrap-v1"
BOOTSTRAP_RELATIVE_PATH = (
    "src/heterodiff/cross_domain_gate/atomic_counting_bootstrap.py"
)

FOCUSED_TEST_PATHS = (
    "tests/unit/test_atomic_counting_grid.py",
    "tests/unit/test_atomic_counting_reference.py",
    "tests/unit/test_cross_domain_counting_fixtures.py",
    "tests/unit/test_cross_domain_counting_windows.py",
    "tests/unit/test_atomic_counting_evidence.py",
    "tests/integration/test_cross_domain_atomic_counting_evidence.py",
    "tests/unit/test_atomic_counting_execution.py",
    "tests/unit/test_atomic_counting_audit.py",
    "tests/unit/test_atomic_counting_reference_torch.py",
    "tests/integration/test_cross_domain_atomic_counting_training_torch.py",
)

BASE_TEST_COMMAND = (
    "python3",
    "-S",
    "-s",
    "-B",
    BOOTSTRAP_RELATIVE_PATH,
    "focused-pytest",
    "base",
)

PINNED_TEST_COMMAND = (
    ".venv-m1/bin/python",
    "-S",
    "-s",
    "-B",
    BOOTSTRAP_RELATIVE_PATH,
    "focused-pytest",
    "pinned",
)

AUDIT_PREFLIGHT_COMMAND = (
    ".venv-m1/bin/python",
    "-S",
    "-s",
    "-B",
    BOOTSTRAP_RELATIVE_PATH,
    "audit-parent",
    "preflight",
)

AUDIT_REQUIRED_STARTUP_ENVIRONMENT = MappingProxyType(
    {
        "MKL_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "PYTHONHASHSEED": "0",
    }
)

_FROZEN_INTERPRETER_SPECS = MappingProxyType(
    {
        "base": MappingProxyType(
            {
                "declared_token": "python3",
                "implementation": "CPython",
                "resolved_executable_sha256": (
                    "b82a1dcaab6a6deae7a574bdbad8e5299909930664cb585f4a0116b905131582"
                ),
                "resolved_executable_size_bytes": 4_003_360,
                "version": "3.9.13",
            }
        ),
        "pinned": MappingProxyType(
            {
                "declared_token": ".venv-m1/bin/python",
                "implementation": "CPython",
                "resolved_executable_sha256": (
                    "ff2d7180d4aa2dcc03193194c1999509239e00101ade54fcdd736d9fc25bd0c6"
                ),
                "resolved_executable_size_bytes": 152_624,
                "version": "3.11.5",
            }
        ),
    }
)

_INTERPRETER_VERSION_PROBE = (
    "import json,platform,sys;"
    "v={'implementation':platform.python_implementation(),"
    "'version':platform.python_version()};"
    "sys.stdout.write(json.dumps(v,allow_nan=False,ensure_ascii=True,"
    "separators=(',',':'),sort_keys=True)+'\\n')"
)

COMPARISON_FIELDS = (
    "step_losses_float32_bytes",
    "model_parameters_float32_bytes",
    "optimizer_state",
    "scheduler_state",
    "completed_step",
    "ordered_task_sampler_state",
    "corruption_generator_state",
    "global_cpu_torch_rng_state",
)

FALSIFICATION_CHECKS = (
    "01_source_coverage",
    "02_exact_counts",
    "03_round_trip",
    "04_identifier_free_state",
    "05_schema_integrity",
    "06_mask_separation",
    "07_padding",
    "08_capacity",
    "09_native_support",
    "10_canonical_persistence",
    "11_corruption_draw_order_and_full_shape",
    "12_task_split_integrity",
    "13_count_two_nontriviality",
    "14_absent_mark_presence_nontriviality",
    "15_continuous_branch_nontriviality",
    "16_rng_isolation",
    "17_checkpoint_integrity_and_failure_atomicity",
    "18_fresh_process_restart_bitwise_equality",
    "19_predeclared_resource_bounds",
    "20_public_private_schema_and_atomic_publication",
)

REVIEW_PROTOCOL_TEXT = (
    "Independent adversarial review must examine representation correctness, "
    "conditioning leakage, stochastic corruption, loss normalization, RNG "
    "isolation, checkpoint integrity and replay, resource enforcement, public "
    "redaction, claim boundaries, and durable no-replace publication. Any "
    "unresolved scientific, integrity, privacy, or resource finding is HOLD."
)

REQUIRED_ARTIFACTS = (
    "checkpoint",
    "continuous_manifest",
    "prefix_manifest",
    "resumed_manifest",
)


class AtomicCountingAuditError(RuntimeError):
    """Base class for independent-audit orchestration failures."""


class AtomicCountingAuditHold(AtomicCountingAuditError):
    """A prerequisite or independently checked invariant did not pass."""


@dataclass(frozen=True)
class DomainAuditInputs:
    """Immutable artifact paths for one executor-produced domain run."""

    domain: str
    continuous_manifest: PathLike
    prefix_manifest: PathLike
    resumed_manifest: PathLike
    checkpoint: PathLike
    run_receipt: PathLike
    review_attestation: PathLike
    audit_output: PathLike

    def __post_init__(self) -> None:
        if self.domain not in ("music", "clinical_style"):
            raise ValueError("domain must be music or clinical_style")
        for name in (
            "continuous_manifest",
            "prefix_manifest",
            "resumed_manifest",
            "checkpoint",
            "run_receipt",
            "review_attestation",
            "audit_output",
        ):
            value = getattr(self, name)
            if not isinstance(value, (str, os.PathLike)):
                raise TypeError("{} must be path-like".format(name))
            object.__setattr__(self, name, Path(value))


@dataclass(frozen=True)
class ProcessCapture:
    command: Tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: bytes
    elapsed_seconds: float


@dataclass(frozen=True)
class InterpreterIdentity:
    """Privacy-safe identity of the resolved executable target."""

    implementation: str
    resolved_executable_sha256: str
    resolved_executable_size_bytes: int
    version: str

    def __post_init__(self) -> None:
        if self.implementation != "CPython":
            raise ValueError("interpreter implementation must be CPython")
        if (
            type(self.resolved_executable_sha256) is not str
            or len(self.resolved_executable_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.resolved_executable_sha256
            )
        ):
            raise ValueError("interpreter executable digest is invalid")
        if (
            type(self.resolved_executable_size_bytes) is not int
            or self.resolved_executable_size_bytes <= 0
        ):
            raise ValueError("interpreter executable size is invalid")
        if type(self.version) is not str or not self.version:
            raise ValueError("interpreter version is invalid")

    def audit_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "implementation": self.implementation,
                "resolved_executable_sha256": self.resolved_executable_sha256,
                "resolved_executable_size_bytes": (
                    self.resolved_executable_size_bytes
                ),
                "version": self.version,
            }
        )


BASE_INTERPRETER_IDENTITY = InterpreterIdentity(
    "CPython",
    _FROZEN_INTERPRETER_SPECS["base"]["resolved_executable_sha256"],
    _FROZEN_INTERPRETER_SPECS["base"]["resolved_executable_size_bytes"],
    _FROZEN_INTERPRETER_SPECS["base"]["version"],
)

PINNED_INTERPRETER_IDENTITY = InterpreterIdentity(
    "CPython",
    _FROZEN_INTERPRETER_SPECS["pinned"]["resolved_executable_sha256"],
    _FROZEN_INTERPRETER_SPECS["pinned"]["resolved_executable_size_bytes"],
    _FROZEN_INTERPRETER_SPECS["pinned"]["version"],
)


@dataclass(frozen=True)
class _ExecutableSnapshot:
    launch_path: Path
    launch_observation: Tuple[object, ...]
    launch_link_target: Optional[str]
    resolved_path: Path
    target_observation: Tuple[int, ...]
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class _ExecutableCustody:
    role: str
    declared_token: str
    snapshot: _ExecutableSnapshot
    identity: InterpreterIdentity


@dataclass(frozen=True)
class TestRunResult:
    command: Tuple[str, ...]
    passed: int
    skipped: int
    warnings: int
    skip_reasons: Tuple[Tuple[int, str, str], ...]
    interpreter_identity: InterpreterIdentity

    def audit_mapping(self) -> Mapping[str, object]:
        return {
            "command": list(self.command),
            "exit_code": 0,
            "interpreter_identity": dict(
                self.interpreter_identity.audit_mapping()
            ),
            "passed": self.passed,
            "skip_reasons": [
                {"count": count, "path": path, "reason": reason}
                for count, path, reason in self.skip_reasons
            ],
            "skipped": self.skipped,
            "warnings": self.warnings,
        }


def _project_root() -> Path:
    return Path(__file__).resolve(strict=True).parents[3]


def assert_stdlib_only_parent() -> None:
    """Reject an audit parent contaminated by NumPy or Torch imports."""

    forbidden = sorted(
        name
        for name in sys.modules
        if name in {"numpy", "torch"}
        or name.startswith("numpy.")
        or name.startswith("torch.")
    )
    if forbidden:
        raise AtomicCountingAuditHold(
            "audit parent is not stdlib-only; imported {}".format(
                ", ".join(forbidden[:8])
            )
        )


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise AtomicCountingAuditHold("value is not canonical JSON") from error


def _strict_json_bytes(raw: bytes, *, name: str) -> object:
    def reject_constant(value: str) -> None:
        raise AtomicCountingAuditHold(
            "{} contains non-standard JSON constant {}".format(name, value)
        )

    def object_pairs(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise AtomicCountingAuditHold(
                    "{} contains duplicate key {!r}".format(name, key)
                )
            result[key] = value
        return result

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=object_pairs,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AtomicCountingAuditHold("{} is not strict JSON".format(name)) from error
    if _canonical_json_bytes(value) != raw:
        raise AtomicCountingAuditHold(
            "{} is not exact canonical JSON".format(name)
        )
    return value


def _domain_digest(domain: str, value: object) -> str:
    payload = _canonical_json_bytes(value)
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _read_bounded_file(path: Path, *, limit: int, name: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise AtomicCountingAuditHold(
            "{} cannot be opened as a regular file".format(name)
        ) from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size < 0:
            raise AtomicCountingAuditHold("{} is not a regular file".format(name))
        if before.st_size > limit:
            raise AtomicCountingAuditHold("{} exceeds its byte ceiling".format(name))
        chunks = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise AtomicCountingAuditHold(
                    "{} was truncated while reading".format(name)
                )
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise AtomicCountingAuditHold("{} grew while reading".format(name))
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise AtomicCountingAuditHold("{} changed while reading".format(name))
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _file_observation(status: os.stat_result) -> Tuple[int, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _resolve_declared_launch_path(token: str, root: Path) -> Path:
    if type(token) is not str or not token or "\x00" in token:
        raise AtomicCountingAuditHold("declared executable token is invalid")
    if "/" in token:
        relative = Path(token)
        if (
            relative.is_absolute()
            or relative.as_posix() != token
            or any(part in ("", ".", "..") for part in relative.parts)
        ):
            raise AtomicCountingAuditHold(
                "declared executable path is not a canonical root-relative path"
            )
        project = root.resolve(strict=True)
        launch = project / relative
    else:
        located = shutil.which(token, path=os.environ.get("PATH"))
        if located is None:
            raise AtomicCountingAuditHold(
                "declared executable {} is unavailable on PATH".format(token)
            )
        launch = Path(located)
        if not launch.is_absolute():
            launch = Path.cwd() / launch
    return launch.absolute()


def _snapshot_executable(launch_path: Path) -> _ExecutableSnapshot:
    try:
        launch_status = launch_path.lstat()
        launch_link_target = (
            os.readlink(launch_path)
            if stat.S_ISLNK(launch_status.st_mode)
            else None
        )
        if not (
            stat.S_ISLNK(launch_status.st_mode)
            or stat.S_ISREG(launch_status.st_mode)
        ):
            raise AtomicCountingAuditHold(
                "declared executable is neither a regular file nor a symlink"
            )
        resolved = launch_path.resolve(strict=True)
        named_before = resolved.lstat()
    except (OSError, RuntimeError) as error:
        raise AtomicCountingAuditHold(
            "declared executable cannot be resolved to a final target"
        ) from error
    if (
        stat.S_ISLNK(named_before.st_mode)
        or not stat.S_ISREG(named_before.st_mode)
        or not os.access(launch_path, os.X_OK)
        or not os.access(resolved, os.X_OK)
    ):
        raise AtomicCountingAuditHold(
            "resolved executable target is not one executable regular file"
        )
    if named_before.st_size <= 0 or named_before.st_size > MAX_EXECUTABLE_BYTES:
        raise AtomicCountingAuditHold(
            "resolved executable target exceeds its bounded size contract"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(resolved, flags)
    except OSError as error:
        raise AtomicCountingAuditHold(
            "resolved executable target cannot be opened safely"
        ) from error
    try:
        before = os.fstat(descriptor)
        if _file_observation(before) != _file_observation(named_before):
            raise AtomicCountingAuditHold(
                "resolved executable target changed before reading"
            )
        remaining = before.st_size
        digest = hashlib.sha256()
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise AtomicCountingAuditHold(
                    "resolved executable target was truncated while reading"
                )
            digest.update(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise AtomicCountingAuditHold(
                "resolved executable target grew while reading"
            )
        after = os.fstat(descriptor)
        named_after = resolved.lstat()
        if (
            _file_observation(after) != _file_observation(before)
            or _file_observation(named_after) != _file_observation(before)
        ):
            raise AtomicCountingAuditHold(
                "resolved executable target changed while reading"
            )
    finally:
        os.close(descriptor)
    return _ExecutableSnapshot(
        launch_path=launch_path,
        launch_observation=(
            *_file_observation(launch_status),
            stat.S_IMODE(launch_status.st_mode),
        ),
        launch_link_target=launch_link_target,
        resolved_path=resolved,
        target_observation=_file_observation(before),
        sha256=digest.hexdigest(),
        size_bytes=before.st_size,
    )


def _expected_interpreter_identity(role: str) -> InterpreterIdentity:
    if role == "base":
        return BASE_INTERPRETER_IDENTITY
    if role == "pinned":
        return PINNED_INTERPRETER_IDENTITY
    raise ValueError("unknown interpreter custody role")


def _validate_snapshot_identity(
    snapshot: _ExecutableSnapshot, *, role: str
) -> None:
    expected = _expected_interpreter_identity(role)
    if (
        snapshot.sha256 != expected.resolved_executable_sha256
        or snapshot.size_bytes != expected.resolved_executable_size_bytes
    ):
        raise AtomicCountingAuditHold(
            "{} resolved executable digest/size differs from the frozen identity".format(
                role
            )
        )


def _interpreter_probe_environment() -> Mapping[str, str]:
    return MappingProxyType(
        {
            **AUDIT_REQUIRED_STARTUP_ENVIRONMENT,
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )


def _parse_interpreter_version_probe(
    capture: ProcessCapture, *, role: str
) -> InterpreterIdentity:
    if (
        capture.returncode != 0
        or capture.stderr
        or not capture.stdout.endswith(b"\n")
        or capture.stdout.count(b"\n") != 1
    ):
        raise AtomicCountingAuditHold(
            "{} interpreter version probe did not complete cleanly".format(role)
        )
    payload = _strict_json_bytes(
        capture.stdout[:-1], name=role + " interpreter version probe"
    )
    if type(payload) is not dict or set(payload) != {
        "implementation",
        "version",
    }:
        raise AtomicCountingAuditHold(
            "{} interpreter version probe schema is invalid".format(role)
        )
    expected = _expected_interpreter_identity(role)
    if (
        payload["implementation"] != expected.implementation
        or payload["version"] != expected.version
    ):
        raise AtomicCountingAuditHold(
            "{} interpreter implementation/version differs from the frozen identity".format(
                role
            )
        )
    return expected


def _capture_frozen_interpreter(role: str, root: Path) -> _ExecutableCustody:
    try:
        spec = _FROZEN_INTERPRETER_SPECS[role]
    except KeyError as error:
        raise ValueError("unknown interpreter custody role") from error
    declared = spec["declared_token"]
    launch_path = _resolve_declared_launch_path(declared, root)
    before = _snapshot_executable(launch_path)
    _validate_snapshot_identity(before, role=role)
    try:
        capture = _run_bounded_subprocess(
            (
                os.fspath(launch_path),
                "-S",
                "-s",
                "-B",
                "-c",
                _INTERPRETER_VERSION_PROBE,
            ),
            cwd=root,
            environment=_interpreter_probe_environment(),
            timeout_seconds=INTERPRETER_PROBE_TIMEOUT_SECONDS,
            maximum_capture_bytes=16 * 1024,
        )
    finally:
        after = _snapshot_executable(launch_path)
        _validate_snapshot_identity(after, role=role)
        if after != before:
            raise AtomicCountingAuditHold(
                "{} executable custody changed across its version probe".format(role)
            )
    identity = _parse_interpreter_version_probe(capture, role=role)
    return _ExecutableCustody(role, declared, before, identity)


def _capture_frozen_interpreters(
    root: Path,
) -> Mapping[str, _ExecutableCustody]:
    return MappingProxyType(
        {
            role: _capture_frozen_interpreter(role, root)
            for role in ("base", "pinned")
        }
    )


def _revalidate_executable_custody(custody: _ExecutableCustody) -> None:
    if type(custody) is not _ExecutableCustody:
        raise TypeError("custody must be an exact executable custody record")
    observed = _snapshot_executable(custody.snapshot.launch_path)
    _validate_snapshot_identity(observed, role=custody.role)
    if observed != custody.snapshot:
        raise AtomicCountingAuditHold(
            "{} executable custody changed before/after a spawn".format(
                custody.role
            )
        )


def _resolve_executable(token: str, root: Path) -> str:
    """Compatibility helper returning only a fully custody-validated launcher."""

    for role, spec in _FROZEN_INTERPRETER_SPECS.items():
        if token == spec["declared_token"]:
            custody = _capture_frozen_interpreter(role, root)
            return os.fspath(custody.snapshot.launch_path)
    raise AtomicCountingAuditHold("executable token is not in the frozen inventory")


def _run_bounded_subprocess(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    timeout_seconds: float,
    maximum_capture_bytes: int = MAX_CAPTURE_BYTES,
) -> ProcessCapture:
    """Capture a child without allowing either pipe to grow without bound."""

    if not command or any(type(token) is not str or not token for token in command):
        raise TypeError("command must be a nonempty sequence of strings")
    if (
        not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0.0
        or maximum_capture_bytes <= 0
    ):
        raise ValueError("subprocess bounds must be positive and finite")
    started = time.monotonic()
    process = subprocess.Popen(
        list(command),
        cwd=os.fspath(cwd),
        env=dict(environment),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
    )
    assert process.stdout is not None
    assert process.stderr is not None
    selector = selectors.DefaultSelector()
    streams = {
        process.stdout.fileno(): ("stdout", process.stdout),
        process.stderr.fileno(): ("stderr", process.stderr),
    }
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    try:
        for descriptor, (name, stream) in streams.items():
            os.set_blocking(descriptor, False)
            selector.register(stream, selectors.EVENT_READ, data=name)
        while selector.get_map():
            remaining = timeout_seconds - (time.monotonic() - started)
            if remaining <= 0.0:
                process.kill()
                process.wait()
                raise AtomicCountingAuditHold("subprocess exceeded its timeout")
            events = selector.select(min(remaining, 0.5))
            if not events and process.poll() is not None:
                # Pipes may need one final iteration to report EOF.
                continue
            for key, _mask in events:
                descriptor = key.fileobj.fileno()
                try:
                    chunk = os.read(descriptor, 64 * 1024)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                target = buffers[key.data]
                target.extend(chunk)
                if len(target) > maximum_capture_bytes:
                    process.kill()
                    process.wait()
                    raise AtomicCountingAuditHold(
                        "subprocess {} exceeded its capture ceiling".format(key.data)
                    )
        returncode = process.wait()
    finally:
        selector.close()
        process.stdout.close()
        process.stderr.close()
        if process.poll() is None:
            process.kill()
            process.wait()
    elapsed = time.monotonic() - started
    return ProcessCapture(
        tuple(command),
        returncode,
        bytes(buffers["stdout"]),
        bytes(buffers["stderr"]),
        elapsed,
    )


_SUMMARY_TOKEN = re.compile(
    r"\b(\d+) "
    r"(passed|skipped|warnings?|deselected|xfailed|xpassed|errors?|failed|reruns?)\b"
)
_SKIP_LINE = re.compile(
    r"^SKIPPED \[(\d+)\] ([^:\r\n]+?)(?::\d+){0,2}: (.+)$"
)


def _parse_pytest_capture(
    capture: ProcessCapture,
    *,
    pinned: bool,
    interpreter_identity: Optional[InterpreterIdentity] = None,
) -> TestRunResult:
    if capture.returncode != 0:
        raise AtomicCountingAuditHold(
            "{} focused tests exited with {}".format(
                "pinned" if pinned else "base", capture.returncode
            )
        )
    try:
        text = (capture.stdout + b"\n" + capture.stderr).decode("utf-8")
    except UnicodeDecodeError as error:
        raise AtomicCountingAuditHold("pytest output is not UTF-8") from error
    summary = None
    for line in reversed(text.splitlines()):
        if re.search(r"\b\d+ passed\b", line) and " in " in line:
            summary = line
            break
    if summary is None:
        raise AtomicCountingAuditHold("pytest output has no terminal pass summary")
    counts = {
        "deselected": 0,
        "error": 0,
        "errors": 0,
        "failed": 0,
        "passed": 0,
        "rerun": 0,
        "reruns": 0,
        "skipped": 0,
        "warning": 0,
        "warnings": 0,
        "xfailed": 0,
        "xpassed": 0,
    }
    for count, kind in _SUMMARY_TOKEN.findall(summary):
        counts[kind] += int(count)
    passed = counts["passed"]
    skipped = counts["skipped"]
    warnings = counts["warning"] + counts["warnings"]
    forbidden_outcomes = {
        name: count
        for name, count in counts.items()
        if name not in {"passed", "skipped", "warning", "warnings"}
        and count != 0
    }
    if passed <= 0 or warnings != 0 or forbidden_outcomes:
        raise AtomicCountingAuditHold(
            "focused tests are empty or contain warnings/non-pass outcomes"
        )
    expected_passed = (
        EXPECTED_PINNED_PASSED if pinned else EXPECTED_BASE_PASSED
    )
    if passed != expected_passed:
        raise AtomicCountingAuditHold(
            "{} focused tests passed {}, expected exactly {}".format(
                "pinned" if pinned else "base", passed, expected_passed
            )
        )

    parsed_skips: Dict[str, Tuple[int, str, str]] = {}
    for line in text.splitlines():
        if not line.startswith("SKIPPED "):
            continue
        match = _SKIP_LINE.fullmatch(line)
        if match is None:
            raise AtomicCountingAuditHold("pytest emitted a malformed skip record")
        count = int(match.group(1))
        path = match.group(2)
        reason = match.group(3)
        if path in parsed_skips:
            raise AtomicCountingAuditHold("pytest emitted a duplicate skip path")
        parsed_skips[path] = (count, path, reason)
    if sum(item[0] for item in parsed_skips.values()) != skipped:
        raise AtomicCountingAuditHold(
            "pytest skip summary differs from its exact module manifest"
        )
    if pinned:
        if skipped != 0 or parsed_skips:
            raise AtomicCountingAuditHold("pinned focused tests must have zero skips")
        normalized = ()
    else:
        expected_by_path = {item[1]: item for item in BASE_SKIP_MANIFEST}
        if skipped != 2 or parsed_skips != expected_by_path:
            raise AtomicCountingAuditHold(
                "base focused tests do not have the exact two declared skips"
            )
        normalized = BASE_SKIP_MANIFEST
    identity = (
        _expected_interpreter_identity("pinned" if pinned else "base")
        if interpreter_identity is None
        else interpreter_identity
    )
    if identity != _expected_interpreter_identity(
        "pinned" if pinned else "base"
    ):
        raise AtomicCountingAuditHold(
            "pytest interpreter identity differs from its frozen role"
        )
    return TestRunResult(
        capture.command,
        passed,
        skipped,
        warnings,
        normalized,
        identity,
    )


def _test_environment(
    root: Path,
    *,
    base_interpreter: Optional[_ExecutableCustody] = None,
) -> Mapping[str, str]:
    """Return the focused/worker allowlist with an optional custody-bound PATH.

    Focused tests exercise this auditor recursively.  Their bootstrap therefore
    needs to preserve a search path that finds the same frozen base launcher.
    Construct that one-entry path from the already-attested custody record; do
    not inherit the audit parent's caller-controlled PATH.  Workers neither
    resolve nor spawn the base interpreter and receive no PATH.
    """

    root.resolve(strict=True)
    if base_interpreter is not None:
        if (
            type(base_interpreter) is not _ExecutableCustody
            or base_interpreter.role != "base"
            or base_interpreter.declared_token != BASE_TEST_COMMAND[0]
            or not base_interpreter.snapshot.launch_path.is_absolute()
        ):
            raise AtomicCountingAuditHold(
                "focused-test base interpreter custody is invalid"
            )
        custody_path = os.fspath(
            base_interpreter.snapshot.launch_path.parent
        )
    else:
        custody_path = None

    return MappingProxyType(
        {
            **AUDIT_REQUIRED_STARTUP_ENVIRONMENT,
            **({"PATH": custody_path} if custody_path is not None else {}),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
    )


def _bootstrap_probe_environment() -> Mapping[str, str]:
    return MappingProxyType(
        {
            **AUDIT_REQUIRED_STARTUP_ENVIRONMENT,
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
    )


def _bootstrap_source_snapshot(root: Path) -> Tuple[bytes, Tuple[int, ...]]:
    path = root / BOOTSTRAP_RELATIVE_PATH
    try:
        before = path.lstat()
    except OSError as error:
        raise AtomicCountingAuditHold(
            "source bootstrap is unavailable at its frozen relative path"
        ) from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise AtomicCountingAuditHold(
            "source bootstrap must be one nonsymlink regular file"
        )
    raw = _read_bounded_file(
        path,
        limit=1024 * 1024,
        name="source bootstrap",
    )
    after = path.lstat()
    if _file_observation(after) != _file_observation(before):
        raise AtomicCountingAuditHold("source bootstrap changed while reading")
    return raw, _file_observation(before)


def _parse_bootstrap_probe(
    capture: ProcessCapture,
    *,
    root: Path,
    interpreter: _ExecutableCustody,
    bootstrap_raw: bytes,
) -> Mapping[str, object]:
    if (
        capture.returncode != 0
        or capture.stderr
        or not capture.stdout.endswith(b"\n")
        or capture.stdout.count(b"\n") != 1
    ):
        raise AtomicCountingAuditHold(
            "source bootstrap probe did not complete cleanly"
        )
    payload = _strict_json_bytes(
        capture.stdout[:-1], name="source bootstrap probe"
    )
    expected_keys = {
        "bootstrap_path",
        "bootstrap_schema",
        "bootstrap_sha256",
        "cwd_excluded_from_sys_path",
        "descendant_attestation",
        "descendant_attestation_environment_fields",
        "dont_write_bytecode",
        "effective_pythonhashseed",
        "executable_identity",
        "legacy_import_artifact_count",
        "no_site",
        "no_user_site",
        "preimport_untrusted_module_count",
        "pycache_prefix_empty",
        "pycache_prefix_owner_only",
        "python_implementation",
        "python_version",
        "pythonpath_ignored",
        "site_imported",
        "site_packages_role",
        "startup_path_replaced",
        "startup_pythonpath_present",
        "status",
        "sys_path_roles",
        "venv_detected",
        "venv_root_role",
    }
    if type(payload) is not dict or set(payload) != expected_keys:
        raise AtomicCountingAuditHold("source bootstrap probe schema is invalid")
    expected_attestation = {
        "bootstrap_sha256": hashlib.sha256(bootstrap_raw).hexdigest(),
        "executable_sha256": interpreter.identity.resolved_executable_sha256,
        "executable_size_bytes": (
            interpreter.identity.resolved_executable_size_bytes
        ),
        "python_implementation": "cpython",
        "python_version": interpreter.identity.version,
        "schema": BOOTSTRAP_SCHEMA,
    }
    expected_environment_fields = [
        "HETERODIFF_BOOTSTRAP_SCHEMA",
        "HETERODIFF_BOOTSTRAP_SHA256",
        "HETERODIFF_PYTHON_EXECUTABLE_SHA256",
        "HETERODIFF_PYTHON_EXECUTABLE_SIZE",
        "HETERODIFF_PYTHON_IMPLEMENTATION",
        "HETERODIFF_PYTHON_VERSION",
    ]
    expected_booleans = {
        "cwd_excluded_from_sys_path": True,
        "dont_write_bytecode": True,
        "no_site": True,
        "no_user_site": True,
        "pycache_prefix_empty": True,
        "pycache_prefix_owner_only": True,
        "pythonpath_ignored": True,
        "site_imported": False,
        "startup_path_replaced": True,
        "startup_pythonpath_present": False,
        "venv_detected": True,
    }
    if any(payload[name] is not expected for name, expected in expected_booleans.items()):
        raise AtomicCountingAuditHold(
            "source bootstrap probe did not establish its isolation invariants"
        )
    if (
        payload["bootstrap_path"] != BOOTSTRAP_RELATIVE_PATH
        or payload["bootstrap_schema"] != BOOTSTRAP_SCHEMA
        or payload["bootstrap_sha256"] != hashlib.sha256(bootstrap_raw).hexdigest()
        or payload["descendant_attestation"] != expected_attestation
        or payload["descendant_attestation_environment_fields"]
        != expected_environment_fields
        or payload["effective_pythonhashseed"] != "0"
        or payload["executable_identity"] != "pinned"
        or payload["legacy_import_artifact_count"] != 0
        or payload["preimport_untrusted_module_count"] != 0
        or payload["python_implementation"] != "cpython"
        or payload["python_version"] != interpreter.identity.version
        or payload["site_packages_role"] != "pinned-venv-site-packages"
        or type(payload["sys_path_roles"]) is not list
        or len(payload["sys_path_roles"]) < 3
        or payload["sys_path_roles"][-2:]
        != ["repository-src", "selected-site-packages"]
        or payload["sys_path_roles"][:-2]
        != [
            "stdlib-{}".format(index)
            for index in range(len(payload["sys_path_roles"]) - 2)
        ]
        or payload["venv_root_role"] != ".venv-m1"
        or payload["status"] != "BOOTSTRAP_READY"
    ):
        raise AtomicCountingAuditHold(
            "source bootstrap probe differs from the frozen pinned contract"
        )
    return MappingProxyType(
        {
            "bootstrap_schema": BOOTSTRAP_SCHEMA,
            "bootstrap_sha256": payload["bootstrap_sha256"],
            "status": "BOOTSTRAP_READY",
        }
    )


def _run_bootstrap_probe(
    root: Path, interpreter: _ExecutableCustody
) -> Mapping[str, object]:
    if interpreter.role != "pinned":
        raise AtomicCountingAuditHold(
            "source bootstrap probe requires pinned interpreter custody"
        )
    bootstrap_raw, bootstrap_observation = _bootstrap_source_snapshot(root)
    command = (
        os.fspath(interpreter.snapshot.launch_path),
        "-S",
        "-s",
        "-B",
        BOOTSTRAP_RELATIVE_PATH,
        "probe",
    )
    _revalidate_executable_custody(interpreter)
    try:
        capture = _run_bounded_subprocess(
            command,
            cwd=root,
            environment=_bootstrap_probe_environment(),
            timeout_seconds=INTERPRETER_PROBE_TIMEOUT_SECONDS,
            maximum_capture_bytes=64 * 1024,
        )
    finally:
        _revalidate_executable_custody(interpreter)
        after_raw, after_observation = _bootstrap_source_snapshot(root)
        if (
            after_observation != bootstrap_observation
            or after_raw != bootstrap_raw
        ):
            raise AtomicCountingAuditHold(
                "source bootstrap custody changed across its probe"
            )
    return _parse_bootstrap_probe(
        capture,
        root=root,
        interpreter=interpreter,
        bootstrap_raw=bootstrap_raw,
    )


def preflight_atomic_counting_audit() -> Mapping[str, object]:
    """Read-only A8 custody/bootstrap preflight; creates no gate output."""

    assert_stdlib_only_parent()
    root = _project_root()
    interpreters = _capture_frozen_interpreters(root)
    bootstrap = _run_bootstrap_probe(root, interpreters["pinned"])
    return MappingProxyType(
        {
            "bootstrap": dict(bootstrap),
            "gate_decision": "NOT_MADE_BY_AUDIT_PREFLIGHT",
            "interpreter_identities": {
                role: dict(interpreters[role].identity.audit_mapping())
                for role in ("base", "pinned")
            },
            "status": "AUDIT_PREFLIGHT_READY",
        }
    )


def _run_focused_tests(
    root: Path,
    *,
    interpreters: Optional[Mapping[str, _ExecutableCustody]] = None,
) -> Mapping[str, TestRunResult]:
    custody = (
        _capture_frozen_interpreters(root)
        if interpreters is None
        else interpreters
    )
    if set(custody) != {"base", "pinned"}:
        raise AtomicCountingAuditHold("interpreter custody inventory is incomplete")
    result = {}
    for name, declared, pinned in (
        ("base", BASE_TEST_COMMAND, False),
        ("pinned", PINNED_TEST_COMMAND, True),
    ):
        interpreter = custody[name]
        if (
            type(interpreter) is not _ExecutableCustody
            or interpreter.role != name
            or interpreter.declared_token != declared[0]
        ):
            raise AtomicCountingAuditHold(
                "{} test interpreter custody is invalid".format(name)
            )
        executed = (
            os.fspath(interpreter.snapshot.launch_path),
        ) + declared[1:]
        _revalidate_executable_custody(interpreter)
        try:
            capture = _run_bounded_subprocess(
                executed,
                cwd=root,
                environment=_test_environment(
                    root,
                    base_interpreter=custody["base"],
                ),
                timeout_seconds=TEST_TIMEOUT_SECONDS,
            )
        finally:
            _revalidate_executable_custody(interpreter)
        # Preserve the frozen relative argv in the audit, not a machine-specific
        # executable resolution.
        capture = ProcessCapture(
            declared,
            capture.returncode,
            capture.stdout,
            capture.stderr,
            capture.elapsed_seconds,
        )
        result[name] = _parse_pytest_capture(
            capture,
            pinned=pinned,
            interpreter_identity=interpreter.identity,
        )
    return MappingProxyType(result)


def _artifact_paths(value: DomainAuditInputs) -> Mapping[str, Path]:
    return MappingProxyType(
        {
            "checkpoint": value.checkpoint,
            "continuous_manifest": value.continuous_manifest,
            "prefix_manifest": value.prefix_manifest,
            "resumed_manifest": value.resumed_manifest,
        }
    )


def _artifact_digests(value: DomainAuditInputs) -> Mapping[str, str]:
    result = {}
    for name, path in _artifact_paths(value).items():
        limit = MAX_CHECKPOINT_BYTES if name == "checkpoint" else 256 * 1024 * 1024
        raw = _read_bounded_file(path, limit=limit, name=name)
        result[name] = hashlib.sha256(raw).hexdigest()
    return MappingProxyType(result)


def _load_receipt(value: DomainAuditInputs) -> Tuple[bytes, dict]:
    raw = _read_bounded_file(
        value.run_receipt, limit=MAX_JSON_BYTES, name=value.domain + " run receipt"
    )
    receipt = _strict_json_bytes(raw, name=value.domain + " run receipt")
    if type(receipt) is not dict:
        raise AtomicCountingAuditHold("run receipt must contain one object")
    required = {
        "artifact_kind",
        "artifacts",
        "checkpoint_bindings",
        "domain",
        "environment",
        "gate_id",
        "resources",
        "schema_version",
        "synthetic_test_only",
        "training_commands",
    }
    if set(receipt) != required:
        raise AtomicCountingAuditHold("run receipt has missing or unknown fields")
    if (
        receipt["schema_version"] != RUN_RECEIPT_SCHEMA
        or receipt["artifact_kind"] != "completed-training-run"
        or receipt["domain"] != value.domain
        or receipt["gate_id"] != GATE_ID
        or receipt["synthetic_test_only"] is not False
    ):
        raise AtomicCountingAuditHold("run receipt is not a production receipt")
    actual = _artifact_digests(value)
    artifacts = receipt["artifacts"]
    if type(artifacts) is not dict or set(artifacts) != set(REQUIRED_ARTIFACTS):
        raise AtomicCountingAuditHold("run receipt artifact inventory is invalid")
    for name, digest in actual.items():
        entry = artifacts[name]
        path = _artifact_paths(value)[name]
        size = path.stat().st_size
        if (
            type(entry) is not dict
            or set(entry) != {"sha256", "size_bytes"}
            or entry["sha256"] != digest
            or entry["size_bytes"] != size
        ):
            raise AtomicCountingAuditHold(
                "run receipt does not bind {}".format(name)
            )
    return raw, receipt


def _load_review_attestation(
    value: DomainAuditInputs,
    *,
    receipt_raw: bytes,
) -> Mapping[str, object]:
    raw = _read_bounded_file(
        value.review_attestation,
        limit=MAX_JSON_BYTES,
        name=value.domain + " read-only review attestation",
    )
    review = _strict_json_bytes(
        raw, name=value.domain + " read-only review attestation"
    )
    expected_keys = {
        "artifact_digests",
        "authored_after_read_only_review",
        "domain",
        "falsification_checks",
        "gate_id",
        "review_protocol_digest",
        "run_receipt_sha256",
        "schema_version",
        "scope",
        "status",
        "unresolved_findings",
    }
    if type(review) is not dict or set(review) != expected_keys:
        raise AtomicCountingAuditHold(
            "read-only review attestation has missing or unknown fields"
        )
    expected_protocol = _domain_digest(
        "heterodiff.atomic-counting.independent-review-protocol.v1",
        {"text": REVIEW_PROTOCOL_TEXT},
    )
    if (
        review["schema_version"] != REVIEW_ATTESTATION_SCHEMA
        or review["gate_id"] != GATE_ID
        or review["domain"] != value.domain
        or review["scope"]
        != "independent-scientific-integrity-privacy-resource"
        or review["review_protocol_digest"] != expected_protocol
        or review["run_receipt_sha256"]
        != hashlib.sha256(receipt_raw).hexdigest()
        or review["artifact_digests"] != dict(_artifact_digests(value))
        or review["authored_after_read_only_review"] is not True
    ):
        raise AtomicCountingAuditHold(
            "read-only review attestation is not bound to this exact run"
        )
    checks = review["falsification_checks"]
    if type(checks) is not dict or set(checks) != set(FALSIFICATION_CHECKS):
        raise AtomicCountingAuditHold(
            "read-only review does not cover every falsification check"
        )
    failed = sorted(name for name, status in checks.items() if status != "PASS")
    findings = review["unresolved_findings"]
    if (
        review["status"] != "PASS"
        or type(findings) is not list
        or findings
        or failed
    ):
        raise AtomicCountingAuditHold(
            "read-only review is HOLD or has unresolved checks: {}".format(
                ", ".join(failed) if failed else "review finding"
            )
        )
    return MappingProxyType(review)


def _worker_command(
    root: Path,
    value: DomainAuditInputs,
    interpreter: _ExecutableCustody,
) -> Tuple[str, ...]:
    if (
        type(interpreter) is not _ExecutableCustody
        or interpreter.role != "pinned"
        or interpreter.declared_token != PINNED_TEST_COMMAND[0]
    ):
        raise AtomicCountingAuditHold("audit worker interpreter custody is invalid")
    directory = "runs/{}".format(value.domain)
    relative_inputs = {
        "continuous_manifest": directory + "/continuous.json",
        "prefix_manifest": directory + "/prefix.json",
        "resumed_manifest": directory + "/resumed.json",
        "checkpoint": directory + "/step5.ckpt",
        "run_receipt": directory + "/receipt.json",
    }
    canonical_root = root.resolve(strict=True)
    for field, relative in relative_inputs.items():
        supplied = getattr(value, field)
        candidate = supplied if supplied.is_absolute() else canonical_root / supplied
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as error:
            raise AtomicCountingAuditHold(
                "audit worker input {} is unavailable".format(field)
            ) from error
        if resolved != canonical_root / relative:
            raise AtomicCountingAuditHold(
                "audit worker inputs must use the exact relative runs paths"
            )
    return (
        os.fspath(interpreter.snapshot.launch_path),
        "-S",
        "-s",
        "-B",
        BOOTSTRAP_RELATIVE_PATH,
        "audit-worker",
        "--domain",
        value.domain,
        "--continuous",
        relative_inputs["continuous_manifest"],
        "--prefix",
        relative_inputs["prefix_manifest"],
        "--resumed",
        relative_inputs["resumed_manifest"],
        "--checkpoint",
        relative_inputs["checkpoint"],
        "--receipt",
        relative_inputs["run_receipt"],
    )


def _run_audit_worker(
    root: Path,
    value: DomainAuditInputs,
    *,
    interpreter: Optional[_ExecutableCustody] = None,
) -> Mapping[str, object]:
    custody = (
        _capture_frozen_interpreter("pinned", root)
        if interpreter is None
        else interpreter
    )
    command = _worker_command(root, value, custody)
    _revalidate_executable_custody(custody)
    try:
        capture = _run_bounded_subprocess(
            command,
            cwd=root,
            environment=_test_environment(root),
            timeout_seconds=WORKER_TIMEOUT_SECONDS,
        )
    finally:
        _revalidate_executable_custody(custody)
    if capture.returncode != 0:
        message = "pinned audit worker returned HOLD"
        try:
            payload = _strict_json_bytes(capture.stdout, name="audit worker HOLD")
            if type(payload) is dict and type(payload.get("message")) is str:
                message = payload["message"]
        except AtomicCountingAuditError:
            pass
        raise AtomicCountingAuditHold(message)
    if capture.stderr:
        raise AtomicCountingAuditHold("pinned audit worker emitted stderr")
    payload = _strict_json_bytes(capture.stdout, name="audit worker result")
    expected = {
        "artifact_digests",
        "checkpoint_integrity",
        "checkpoint_replay",
        "domain",
        "gate_id",
        "independent_digest_inventory",
        "schema_version",
        "status",
    }
    if type(payload) is not dict or set(payload) != expected:
        raise AtomicCountingAuditHold("audit worker result schema is invalid")
    if (
        payload["schema_version"] != AUDIT_WORKER_SCHEMA
        or payload["status"] != "PASS"
        or payload["domain"] != value.domain
        or payload["gate_id"] != GATE_ID
    ):
        raise AtomicCountingAuditHold("audit worker did not return an exact PASS")
    if payload["artifact_digests"] != dict(_artifact_digests(value)):
        raise AtomicCountingAuditHold("worker and parent artifact digests differ")
    return payload


def _assemble_audit(
    value: DomainAuditInputs,
    *,
    receipt_raw: bytes,
    tests: Mapping[str, TestRunResult],
    worker: Mapping[str, object],
    review: Mapping[str, object],
) -> bytes:
    checkpoint = worker["checkpoint_integrity"]
    replay = worker["checkpoint_replay"]
    inventory = worker["independent_digest_inventory"]
    if type(checkpoint) is not dict or type(replay) is not dict or type(inventory) is not dict:
        raise AtomicCountingAuditHold("worker PASS payload contains invalid objects")
    audit = {
        "adversarial_review": {
            "review_protocol_digest": review["review_protocol_digest"],
            "scope": review["scope"],
            "status": review["status"],
            "unresolved_findings": list(review["unresolved_findings"]),
        },
        "artifact_digests": dict(worker["artifact_digests"]),
        "artifact_kind": "independent-gate-audit",
        "checkpoint_integrity": checkpoint,
        "checkpoint_replay": replay,
        "domain": value.domain,
        "falsification_checks": dict(review["falsification_checks"]),
        "gate_id": GATE_ID,
        "independent_digest_inventory": inventory,
        "run_receipt_sha256": hashlib.sha256(receipt_raw).hexdigest(),
        "schema_version": AUDIT_SCHEMA,
        "synthetic_test_only": False,
        "test_runs": {
            "base": dict(tests["base"].audit_mapping()),
            "pinned": dict(tests["pinned"].audit_mapping()),
        },
    }
    return _canonical_json_bytes(audit)


def _preflight_output(path: Path) -> None:
    if not path.name or path.name in (".", ".."):
        raise AtomicCountingAuditHold("audit output must name one file")
    parent = path.parent.resolve(strict=True)
    if not parent.is_dir() or parent.is_symlink():
        raise AtomicCountingAuditHold(
            "audit output parent must be a non-symlink directory"
        )
    if os.path.lexists(path):
        raise AtomicCountingAuditHold("audit output already exists")


def _write_audits_last_no_replace(outputs: Mapping[Path, bytes]) -> None:
    """Stage, fsync, and no-replace-publish all audit files after all checks."""

    if not outputs:
        raise ValueError("at least one audit output is required")
    for path in outputs:
        _preflight_output(path)
    staged = []
    published = []
    try:
        for output, payload in outputs.items():
            parent = output.parent.resolve(strict=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".{}-".format(output.name), suffix=".audit.tmp", dir=parent
            )
            temporary = Path(temporary_name)
            try:
                os.fchmod(descriptor, 0o600)
                position = 0
                while position < len(payload):
                    written = os.write(descriptor, payload[position:])
                    if written <= 0:
                        raise AtomicCountingAuditHold("audit staging write stalled")
                    position += written
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            staged.append((output, temporary, temporary.stat()))
        for output, temporary, identity in staged:
            os.link(temporary, output)
            published.append((output, identity))
        for parent in sorted({path.parent.resolve(strict=True) for path in outputs}):
            descriptor = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    except BaseException:
        for output, identity in reversed(published):
            try:
                observed = output.stat()
                if (
                    observed.st_dev == identity.st_dev
                    and observed.st_ino == identity.st_ino
                ):
                    output.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        for _output, temporary, _identity in staged:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def produce_atomic_counting_audits(
    runs: Sequence[DomainAuditInputs],
) -> Mapping[str, str]:
    """Run all independent checks and durably publish two audit files last."""

    assert_stdlib_only_parent()
    if type(runs) not in (tuple, list) or len(runs) != 2:
        raise AtomicCountingAuditHold("exactly two domain audit inputs are required")
    if any(type(value) is not DomainAuditInputs for value in runs):
        raise TypeError("runs must contain exact DomainAuditInputs")
    by_domain = {value.domain: value for value in runs}
    if set(by_domain) != {"music", "clinical_style"}:
        raise AtomicCountingAuditHold("one input per frozen domain is required")
    outputs = [value.audit_output for value in runs]
    if len({os.fspath(path) for path in outputs}) != 2:
        raise AtomicCountingAuditHold("audit output paths must be distinct")
    for output in outputs:
        _preflight_output(output)

    root = _project_root()
    receipt_data = {
        domain: _load_receipt(value)
        for domain, value in sorted(by_domain.items())
    }
    reviews = {
        domain: _load_review_attestation(
            value, receipt_raw=receipt_data[domain][0]
        )
        for domain, value in sorted(by_domain.items())
    }
    interpreters = _capture_frozen_interpreters(root)
    tests = _run_focused_tests(root, interpreters=interpreters)
    workers = {
        domain: _run_audit_worker(
            root,
            value,
            interpreter=interpreters["pinned"],
        )
        for domain, value in sorted(by_domain.items())
    }
    payloads = {
        by_domain[domain].audit_output: _assemble_audit(
            by_domain[domain],
            receipt_raw=receipt_data[domain][0],
            tests=tests,
            worker=workers[domain],
            review=reviews[domain],
        )
        for domain in ("music", "clinical_style")
    }
    _write_audits_last_no_replace(payloads)
    return MappingProxyType(
        {
            domain: hashlib.sha256(payloads[by_domain[domain].audit_output]).hexdigest()
            for domain in ("music", "clinical_style")
        }
    )


def _add_domain(parser: argparse.ArgumentParser, name: str) -> None:
    label = name.replace("_", "-")
    for field in (
        "continuous",
        "prefix",
        "resumed",
        "checkpoint",
        "receipt",
        "review",
        "audit",
    ):
        parser.add_argument("--{}-{}".format(label, field), type=Path, required=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="independent bounded atomic-counting audit producer"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("probe", help="report parent import boundary only")
    commands.add_parser(
        "preflight",
        help="read-only interpreter custody and source-bootstrap validation",
    )
    audit = commands.add_parser("audit", help="produce two canonical audit files")
    _add_domain(audit, "music")
    _add_domain(audit, "clinical_style")
    return parser


def _inputs(args: argparse.Namespace, domain: str) -> DomainAuditInputs:
    prefix = domain
    return DomainAuditInputs(
        domain,
        getattr(args, prefix + "_continuous"),
        getattr(args, prefix + "_prefix"),
        getattr(args, prefix + "_resumed"),
        getattr(args, prefix + "_checkpoint"),
        getattr(args, prefix + "_receipt"),
        getattr(args, prefix + "_review"),
        getattr(args, prefix + "_audit"),
    )


def main(arguments: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(arguments)
    if args.command == "probe":
        payload = {
            "numpy_loaded": "numpy" in sys.modules,
            "status": "STDLIB_PARENT_READY",
            "torch_loaded": "torch" in sys.modules,
        }
        sys.stdout.buffer.write(_canonical_json_bytes(payload) + b"\n")
        return 0 if not payload["numpy_loaded"] and not payload["torch_loaded"] else 2
    try:
        if args.command == "preflight":
            payload = dict(preflight_atomic_counting_audit())
            sys.stdout.buffer.write(_canonical_json_bytes(payload) + b"\n")
            return 0
        digests = produce_atomic_counting_audits(
            (
                _inputs(args, "music"),
                _inputs(args, "clinical_style"),
            )
        )
        payload = {
            "audit_sha256": dict(digests),
            "gate_decision": "NOT_MADE_BY_AUDIT_PRODUCER",
            "status": "PASS_AUDITS_PUBLISHED",
        }
        sys.stdout.buffer.write(_canonical_json_bytes(payload) + b"\n")
        return 0
    except (AtomicCountingAuditError, OSError, ValueError, TypeError) as error:
        payload = {
            "error_type": type(error).__name__,
            "message": str(error),
            "status": "HOLD",
        }
        sys.stdout.buffer.write(_canonical_json_bytes(payload) + b"\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "AtomicCountingAuditError",
    "AtomicCountingAuditHold",
    "AUDIT_PREFLIGHT_COMMAND",
    "AUDIT_REQUIRED_STARTUP_ENVIRONMENT",
    "BASE_TEST_COMMAND",
    "BASE_INTERPRETER_IDENTITY",
    "DomainAuditInputs",
    "FOCUSED_TEST_PATHS",
    "InterpreterIdentity",
    "PINNED_TEST_COMMAND",
    "PINNED_INTERPRETER_IDENTITY",
    "ProcessCapture",
    "TestRunResult",
    "assert_stdlib_only_parent",
    "main",
    "preflight_atomic_counting_audit",
    "produce_atomic_counting_audits",
]
