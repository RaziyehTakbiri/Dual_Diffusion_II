"""Torch-free production executor for the atomic-counting gate inputs.

Importing this module performs no execution and leaves repository status
``NOT_EXECUTED``.  The ``run`` entry point launches exactly six fresh pinned
worker interpreters through the source-bound bootstrap and, only after all
deterministic comparisons validate, writes one production run receipt per
domain.  It never creates an audit report, evidence bundle, empirical claim,
or gate decision.

The receipts are local procedural attestations, not cryptographic proof of who
ran a process.  A separate read-only auditor must independently inspect the
artifacts, replay the checkpoint under the pinned Torch runtime, and issue the
audit inputs required by the evidence publisher.

The parent process deliberately imports only the Python standard library.  All
Torch work is confined to fresh ``.venv-m1/bin/python`` subprocesses.

The admitted mutable entry is exactly the pinned interpreter with ``-S -s -B``,
the repository-relative ``atomic_counting_bootstrap.py`` path, and the
``execution-parent run`` role/argument pair.  Each training child additionally
uses ``-W error`` and receives only the three frozen thread/hash-seed variables
before the bootstrap replaces its environment.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import io
import json
import math
import os
from pathlib import Path
import selectors
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import time
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Sequence, Tuple
import unicodedata
import zipfile


EXECUTION_IMPLEMENTATION_STATUS = "NOT_EXECUTED"
EXECUTION_IMPLEMENTATION_BLOCKER = (
    "The production executor has not been invoked and no independent PASS "
    "audit or evidence publication is implied by importing this module."
)

_OUTPUT_ROOT = "runs"
_DOMAINS = ("music", "clinical_style")
_BRANCHES = ("continuous", "prefix", "resume")
_PINNED_PYTHON = ".venv-m1/bin/python"
_PINNED_PYTHON_VERSION = "3.11.5"
_PINNED_PYTHON_EXECUTABLE_SHA256 = (
    "ff2d7180d4aa2dcc03193194c1999509239e00101ade54fcdd736d9fc25bd0c6"
)
_PINNED_PYTHON_EXECUTABLE_SIZE_BYTES = 152_624
_BOOTSTRAP_SCHEMA = "heterodiff-atomic-counting-source-bootstrap-v1"
_BOOTSTRAP_RELATIVE_PATH = (
    "src/heterodiff/cross_domain_gate/atomic_counting_bootstrap.py"
)
_BOOTSTRAP_ENVIRONMENT_FIELDS = {
    "bootstrap_sha256": "HETERODIFF_BOOTSTRAP_SHA256",
    "executable_sha256": "HETERODIFF_PYTHON_EXECUTABLE_SHA256",
    "executable_size_bytes": "HETERODIFF_PYTHON_EXECUTABLE_SIZE",
    "python_implementation": "HETERODIFF_PYTHON_IMPLEMENTATION",
    "python_version": "HETERODIFF_PYTHON_VERSION",
    "schema": "HETERODIFF_BOOTSTRAP_SCHEMA",
}
_GATE_ID = "heterodiff-cross-domain-atomic-counting-reference-gate-v1"
_RECEIPT_SCHEMA = "heterodiff-cross-domain-completed-run-receipt-v1"
_TRAINING_MANIFEST_FORMAT = "heterodiff-atomic-counting-restart-comparison-v1"
_BINDINGS_FORMAT = "heterodiff-atomic-counting-bindings-v1"
_CHECKPOINT_FORMAT = "heterodiff-atomic-counting-checkpoint-v1"
_CHECKPOINT_MAGIC = b"HACGCP1\x00"
_CHECKPOINT_HEADER_BYTES = 4

_MAX_CHECKPOINT_BYTES = 64 * 1024 * 1024
_MAX_LOG_BYTES = 2 * 1024 * 1024
_MAX_OUTPUT_BYTES = 256 * 1024 * 1024
_MAX_RSS_BYTES = 2 * 1024 * 1024 * 1024
_MAX_RUNTIME_SECONDS = 120.0
_PROCESS_TIMEOUT_SECONDS = 125.0
_READ_CHUNK_BYTES = 1024 * 1024

_PINNED_ENVIRONMENT = MappingProxyType(
    {
        "MKL_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "PYTHONHASHSEED": "0",
    }
)

_REQUIRED_BINDING_KEYS = frozenset(
    {
        "schema",
        "task",
        "corruption",
        "model",
        "loss",
        "training_config",
        "source_fixture",
        "converted_state",
        "tensor",
        "split_group_policy",
        "train_transform",
        "code_source",
        "dependency_lock",
        "environment_manifest",
        "gate_id",
        "gate_spec",
    }
)

_SUMMARY_KEYS = frozenset(
    {
        "checkpoint_bindings",
        "checkpoint_sha256",
        "completed_step",
        "domain",
        "elapsed_seconds",
        "environment",
        "maximum_rss_bytes",
        "mode",
        "output_sha256",
        "stages",
        "status",
    }
)

_MANIFEST_KEYS = frozenset(
    {
        "bindings_digest",
        "completed_step",
        "corruption_generator_state",
        "domain",
        "format",
        "gate_id",
        "global_torch_rng_state",
        "model_state",
        "optimizer_state",
        "parameter_count",
        "sampler_state",
        "scheduler_state",
        "step_records",
        "task_bundle_digest",
        "training_config_digest",
    }
)

_TASK_SEQUENCES = MappingProxyType(
    {
        "music": (1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0),
        "clinical_style": (0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1),
    }
)


class AtomicCountingExecutionError(RuntimeError):
    """Base class for fail-closed production execution errors."""


class AtomicCountingExecutionInputError(AtomicCountingExecutionError):
    """The frozen root, command, environment, or output path is invalid."""


class AtomicCountingExecutionProcessError(AtomicCountingExecutionError):
    """A fresh worker failed, timed out, or exceeded an I/O ceiling."""


class AtomicCountingExecutionIntegrityError(AtomicCountingExecutionError):
    """Worker output or a restart relation failed exact validation."""


class AtomicCountingExecutionPublicationError(AtomicCountingExecutionError):
    """A receipt could not be durably published without replacement."""


@dataclass(frozen=True)
class AtomicCountingExecutionResult:
    """Completed run inputs that still await independent audit/publication."""

    output_root: Path
    status: str
    receipt_sha256: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.status != "RUN_INPUTS_COMPLETE_AWAITING_INDEPENDENT_AUDIT":
            raise ValueError("execution result status is invalid")
        digests = dict(self.receipt_sha256)
        if set(digests) != set(_DOMAINS):
            raise ValueError("receipt digest inventory is incomplete")
        for domain, digest in digests.items():
            _require_sha256(digest, name=domain + " receipt digest")
        object.__setattr__(self, "receipt_sha256", MappingProxyType(digests))


@dataclass(frozen=True)
class _ProcessResult:
    returncode: int
    stdout: bytes
    stderr: bytes


@dataclass(frozen=True)
class _FileRecord:
    path: Path
    raw: bytes
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class _BranchResult:
    command: Tuple[str, ...]
    summary: Mapping[str, object]
    stdout_bytes: int
    manifest: Mapping[str, object]
    artifact: _FileRecord


def repository_execution_status() -> Mapping[str, str]:
    """Return the honest no-I/O repository state."""

    return MappingProxyType(
        {
            "status": EXECUTION_IMPLEMENTATION_STATUS,
            "blocker": EXECUTION_IMPLEMENTATION_BLOCKER,
        }
    )


def assert_stdlib_only_parent() -> None:
    """Fail if the production parent imported NumPy or Torch before spawning.

    The supported production surface is the source-bound bootstrap.  A
    ``python -m heterodiff...`` invocation necessarily initializes the package
    first and therefore is not admitted for execution.
    """

    forbidden = sorted(
        name
        for name in sys.modules
        if name in {"numpy", "torch"}
        or name.startswith("numpy.")
        or name.startswith("torch.")
    )
    if forbidden:
        raise AtomicCountingExecutionInputError(
            "production parent is not stdlib-only; imported {}".format(
                ", ".join(forbidden[:8])
            )
        )


def _project_root() -> Path:
    return Path(__file__).resolve(strict=True).parents[3]


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
        raise AtomicCountingExecutionIntegrityError(
            "value is not canonical-JSON serializable"
        ) from error


def _strict_json_bytes(raw: bytes, *, name: str) -> object:
    def reject_constant(value: str) -> None:
        raise AtomicCountingExecutionIntegrityError(
            "{} contains non-standard JSON constant {}".format(name, value)
        )

    def object_pairs(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise AtomicCountingExecutionIntegrityError(
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
    except UnicodeDecodeError as error:
        raise AtomicCountingExecutionIntegrityError(
            "{} is not strict UTF-8".format(name)
        ) from error
    except json.JSONDecodeError as error:
        raise AtomicCountingExecutionIntegrityError(
            "{} is not valid JSON".format(name)
        ) from error
    if _canonical_json_bytes(value) != raw:
        raise AtomicCountingExecutionIntegrityError(
            "{} is not the exact canonical JSON encoding".format(name)
        )
    return value


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _domain_digest(domain: str, value: object) -> str:
    payload = _canonical_json_bytes(value)
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _require_sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise AtomicCountingExecutionIntegrityError(
            "{} must be a lowercase SHA-256 digest".format(name)
        )
    return value


def _plain_int(
    value: object, *, name: str, minimum: int = 0, maximum: int
) -> int:
    if type(value) is not int or value < minimum or value > maximum:
        raise AtomicCountingExecutionIntegrityError(
            "{} must be an integer in [{}, {}]".format(name, minimum, maximum)
        )
    return value


def _finite_real(
    value: object, *, name: str, minimum: float = 0.0, maximum: float
) -> float:
    if type(value) not in (int, float):
        raise AtomicCountingExecutionIntegrityError(
            "{} must be a finite real".format(name)
        )
    result = float(value)
    if not math.isfinite(result) or result < minimum or result > maximum:
        raise AtomicCountingExecutionIntegrityError(
            "{} must be finite and in [{}, {}]".format(name, minimum, maximum)
        )
    return result


def _safe_relative_token(value: str, *, name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.startswith("~")
        or "\\" in value
        or Path(value).is_absolute()
        or unicodedata.normalize("NFC", value) != value
        or any(
            part in ("", ".", "..") for part in Path(value).parts
        )
        or any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs"}
            for character in value
        )
    ):
        raise AtomicCountingExecutionInputError(
            "{} must be a safe canonical relative path".format(name)
        )
    if value != Path(value).as_posix():
        raise AtomicCountingExecutionInputError(
            "{} must use canonical POSIX separators".format(name)
        )
    return value


def _reject_symlink_components(path: Path, *, final_must_exist: bool) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    parts = absolute.parts[1:]
    for index, part in enumerate(parts):
        current = current / part
        final = index == len(parts) - 1
        try:
            status = current.lstat()
        except FileNotFoundError:
            if final and not final_must_exist:
                return
            raise AtomicCountingExecutionInputError(
                "path component does not exist: {}".format(current)
            )
        if stat.S_ISLNK(status.st_mode):
            raise AtomicCountingExecutionInputError(
                "execution paths must not contain symlink components"
            )


def _file_identity(status: os.stat_result) -> Tuple[int, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _directory_identity(status: os.stat_result) -> Tuple[int, int, int]:
    return (status.st_dev, status.st_ino, stat.S_IFMT(status.st_mode))


def _read_stable_file(path: Path, *, limit: int, name: str) -> bytes:
    _reject_symlink_components(path, final_must_exist=True)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        named = path.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(named.st_mode)
            or _file_identity(before) != _file_identity(named)
        ):
            raise AtomicCountingExecutionIntegrityError(
                "{} is not one stable regular file".format(name)
            )
        if before.st_size > limit:
            raise AtomicCountingExecutionIntegrityError(
                "{} exceeds its byte ceiling".format(name)
            )
        remaining = before.st_size
        chunks = []
        while remaining:
            chunk = os.read(descriptor, min(remaining, _READ_CHUNK_BYTES))
            if not chunk:
                raise AtomicCountingExecutionIntegrityError(
                    "{} was truncated while reading".format(name)
                )
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise AtomicCountingExecutionIntegrityError(
                "{} grew while reading".format(name)
            )
        after = os.fstat(descriptor)
        if _file_identity(after) != _file_identity(before):
            raise AtomicCountingExecutionIntegrityError(
                "{} changed while reading".format(name)
            )
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _file_record(path: Path, *, limit: int, name: str) -> _FileRecord:
    raw = _read_stable_file(path, limit=limit, name=name)
    return _FileRecord(path, raw, _sha256(raw), len(raw))


def _source_tree_digest(root: Path) -> str:
    source_root = root / "src" / "heterodiff"
    test_root = root / "tests"
    optional_relatives = (
        ".pytest.ini",
        "conftest.py",
        "pytest.ini",
        "setup.cfg",
        "sitecustomize.py",
        "src/conftest.py",
        "src/sitecustomize.py",
        "src/usercustomize.py",
        "tox.ini",
        "usercustomize.py",
    )
    required_paths = (
        *source_root.rglob("*.py"),
        *test_root.rglob("*.py"),
        root / "pyproject.toml",
    )
    if not required_paths:
        raise AtomicCountingExecutionInputError("local source tree is empty")
    optional_before = {}
    for relative in optional_relatives:
        path = root / relative
        _reject_symlink_components(path.parent, final_must_exist=True)
        try:
            optional_before[relative] = _file_identity(path.lstat())
        except FileNotFoundError:
            optional_before[relative] = None
    entries = {
        path.relative_to(root).as_posix(): path for path in required_paths
    }
    entries.update(
        {relative: root / relative for relative in optional_relatives}
    )
    digest = hashlib.sha256()
    digest.update(b"heterodiff.atomic-counting-source-test-config-startup-tree.v3\x00")
    for relative_text, path in sorted(entries.items()):
        relative = relative_text.encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        if (
            relative_text in optional_before
            and optional_before[relative_text] is None
        ):
            digest.update(b"\x00")
            continue
        raw = _read_stable_file(
            path, limit=8 * 1024 * 1024, name="implementation source"
        )
        digest.update(b"\x01")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    for relative, before in optional_before.items():
        path = root / relative
        try:
            after = _file_identity(path.lstat())
        except FileNotFoundError:
            after = None
        if after != before:
            raise AtomicCountingExecutionIntegrityError(
                "optional source/startup configuration changed while hashing"
            )
    return digest.hexdigest()


def _locked_distributions(lock_raw: bytes) -> Mapping[str, str]:
    try:
        text = lock_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AtomicCountingExecutionInputError(
            "dependency lock is not UTF-8"
        ) from error
    result = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.count("==") != 1:
            raise AtomicCountingExecutionInputError(
                "dependency lock line {} is not an exact pin".format(line_number)
            )
        declared, version = line.split("==")
        canonical = declared.lower().replace("_", "-").replace(".", "-")
        while "--" in canonical:
            canonical = canonical.replace("--", "-")
        if (
            not declared
            or not version
            or declared != declared.strip()
            or version != version.strip()
            or not canonical
            or canonical.startswith("-")
            or canonical.endswith("-")
            or canonical in result
        ):
            raise AtomicCountingExecutionInputError(
                "dependency lock line {} is noncanonical".format(line_number)
            )
        result[canonical] = version
    if not result:
        raise AtomicCountingExecutionInputError(
            "dependency lock has no distributions"
        )
    return dict(sorted(result.items()))


def _external_digests(root: Path) -> Tuple[Mapping[str, str], bytes]:
    lock_path = root / "requirements" / "m1-reference-macos-arm64-py311.lock"
    gate_path = root / "research" / "32_cross_domain_atomic_counting_reference_gate.md"
    lock_raw = _read_stable_file(
        lock_path, limit=1024 * 1024, name="dependency lock"
    )
    gate_raw = _read_stable_file(
        gate_path, limit=2 * 1024 * 1024, name="gate specification"
    )
    return (
        MappingProxyType(
            {
                "code_source": _source_tree_digest(root),
                "dependency_lock": _sha256(lock_raw),
                "gate_spec": _sha256(gate_raw),
            }
        ),
        lock_raw,
    )


def _expected_bootstrap_attestation(root: Path) -> Mapping[str, object]:
    bootstrap_raw = _read_stable_file(
        root / _BOOTSTRAP_RELATIVE_PATH,
        limit=1024 * 1024,
        name="source bootstrap",
    )
    return MappingProxyType(
        {
            "bootstrap_sha256": _sha256(bootstrap_raw),
            "executable_sha256": _PINNED_PYTHON_EXECUTABLE_SHA256,
            "executable_size_bytes": _PINNED_PYTHON_EXECUTABLE_SIZE_BYTES,
            "python_implementation": "cpython",
            "python_version": _PINNED_PYTHON_VERSION,
            "schema": _BOOTSTRAP_SCHEMA,
        }
    )


def _validate_pinned_python(
    root: Path,
    *,
    expected_attestation: Optional[Mapping[str, object]] = None,
) -> Mapping[str, object]:
    path = root / _PINNED_PYTHON
    _reject_symlink_components(path.parent, final_must_exist=True)
    try:
        resolved = path.resolve(strict=True)
        status = resolved.stat()
    except FileNotFoundError as error:
        raise AtomicCountingExecutionInputError(
            "the exact pinned interpreter path is missing"
        ) from error
    if not stat.S_ISREG(status.st_mode) or not os.access(resolved, os.X_OK):
        raise AtomicCountingExecutionInputError(
            "the exact pinned interpreter path is not executable"
        )
    executable_raw = _read_stable_file(
        resolved,
        limit=8 * 1024 * 1024,
        name="resolved pinned interpreter",
    )
    if (
        len(executable_raw) != _PINNED_PYTHON_EXECUTABLE_SIZE_BYTES
        or _sha256(executable_raw) != _PINNED_PYTHON_EXECUTABLE_SHA256
    ):
        raise AtomicCountingExecutionInputError(
            "the resolved pinned interpreter differs from the frozen identity"
        )
    attestation = _expected_bootstrap_attestation(root)
    if (
        expected_attestation is not None
        and dict(attestation) != dict(expected_attestation)
    ):
        raise AtomicCountingExecutionIntegrityError(
            "pinned interpreter or source bootstrap changed during execution"
        )
    return attestation


def _validate_parent_bootstrap_attestation(
    expected_attestation: Mapping[str, object],
) -> None:
    observed = {
        name: os.environ.get(environment_name)
        for name, environment_name in _BOOTSTRAP_ENVIRONMENT_FIELDS.items()
    }
    expected_environment = {
        **dict(expected_attestation),
        "executable_size_bytes": str(
            expected_attestation["executable_size_bytes"]
        ),
    }
    if observed != expected_environment:
        raise AtomicCountingExecutionInputError(
            "execution parent lacks the exact source-bootstrap attestation"
        )


def _prepare_output_root(root: Path, output_root: str) -> Tuple[Path, Mapping[str, Tuple[int, int, int]]]:
    if output_root != _OUTPUT_ROOT:
        raise AtomicCountingExecutionInputError(
            "production output root must be exactly {!r}".format(_OUTPUT_ROOT)
        )
    _safe_relative_token(output_root, name="output root")
    output = root / output_root
    _reject_symlink_components(output, final_must_exist=False)
    if os.path.lexists(output):
        raise AtomicCountingExecutionInputError(
            "production output root already exists and will not be reused"
        )
    os.mkdir(output, 0o700)
    identities: Dict[str, Tuple[int, int, int]] = {
        "root": _directory_identity(output.lstat())
    }
    try:
        for domain in _DOMAINS:
            path = output / domain
            os.mkdir(path, 0o700)
            identities[domain] = _directory_identity(path.lstat())
    except BaseException:
        _cleanup_owned_output(output, identities)
        raise
    return output, MappingProxyType(dict(identities))


def _cleanup_owned_output(
    output: Path, identities: Mapping[str, Tuple[int, int, int]]
) -> None:
    """Remove only known entries below directories created by this invocation."""

    known_files = (
        "continuous.json",
        "prefix.json",
        "resumed.json",
        "step5.ckpt",
        "receipt.json",
    )
    for domain in reversed(_DOMAINS):
        path = output / domain
        expected = identities.get(domain)
        try:
            status = path.lstat()
        except FileNotFoundError:
            continue
        if expected is None or _directory_identity(status) != expected:
            continue
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags)
        except OSError:
            continue
        try:
            if _directory_identity(os.fstat(descriptor)) != expected:
                continue
            for name in known_files:
                try:
                    os.unlink(name, dir_fd=descriptor)
                except (FileNotFoundError, IsADirectoryError):
                    pass
        finally:
            os.close(descriptor)
        try:
            path.rmdir()
        except OSError:
            pass
    expected_root = identities.get("root")
    try:
        status = output.lstat()
    except FileNotFoundError:
        return
    if expected_root is not None and _directory_identity(status) == expected_root:
        try:
            output.rmdir()
        except OSError:
            pass


def _kill_process(process: subprocess.Popen) -> None:
    try:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                process.kill()
    finally:
        try:
            process.wait(timeout=5.0)
        except (subprocess.TimeoutExpired, OSError):
            pass


def _run_worker_process(
    command: Tuple[str, ...], *, root: Path, environment: Mapping[str, str]
) -> _ProcessResult:
    """Run one worker while bounding wall time and both output streams."""

    try:
        process = subprocess.Popen(
            list(command),
            cwd=str(root),
            env=dict(environment),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            start_new_session=True,
        )
    except OSError as error:
        raise AtomicCountingExecutionProcessError(
            "fresh worker could not be started"
        ) from error
    assert process.stdout is not None
    assert process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    chunks: Dict[str, list[bytes]] = {"stdout": [], "stderr": []}
    sizes = {"stdout": 0, "stderr": 0}
    deadline = time.monotonic() + _PROCESS_TIMEOUT_SECONDS
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0.0:
                _kill_process(process)
                raise AtomicCountingExecutionProcessError(
                    "fresh worker exceeded the bounded process timeout"
                )
            events = selector.select(timeout=min(0.25, remaining))
            for key, _mask in events:
                chunk = os.read(key.fileobj.fileno(), 64 * 1024)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                stream = key.data
                sizes[stream] += len(chunk)
                if sizes[stream] > _MAX_LOG_BYTES:
                    _kill_process(process)
                    raise AtomicCountingExecutionProcessError(
                        "fresh worker {} exceeded the log byte ceiling".format(stream)
                    )
                chunks[stream].append(chunk)
        remaining = max(0.0, deadline - time.monotonic())
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as error:
            _kill_process(process)
            raise AtomicCountingExecutionProcessError(
                "fresh worker did not terminate after closing its output streams"
            ) from error
    finally:
        selector.close()
        process.stdout.close()
        process.stderr.close()
        if process.poll() is None:
            _kill_process(process)
    return _ProcessResult(
        returncode=returncode,
        stdout=b"".join(chunks["stdout"]),
        stderr=b"".join(chunks["stderr"]),
    )


def _expected_stage_sequence(branch: str) -> Tuple[str, ...]:
    if branch not in _BRANCHES:
        raise ValueError("unknown branch")
    result = [
        "fixture-parse-and-task-construction",
        "reference-and-task-conversion",
        "trainer-initialization",
    ]
    if branch == "resume":
        result.extend(
            (
                "checkpoint-load-preflight",
                "checkpoint-validation",
                "checkpoint-restore",
            )
        )
        steps = 7
    else:
        steps = 12 if branch == "continuous" else 5
    for _step in range(steps):
        result.extend(
            (
                "corruption-and-conversion",
                "forward",
                "backward",
                "optimizer-and-scheduler",
            )
        )
    if branch == "prefix":
        result.extend(
            (
                "checkpoint-save-preflight",
                "checkpoint-serialization",
                "checkpoint-save",
            )
        )
    result.extend(("comparison-output-preflight", "comparison-output"))
    return tuple(result)


def _validate_environment(
    value: object,
    *,
    lock_raw: bytes,
    expected_bootstrap_attestation: Mapping[str, object],
) -> Mapping[str, object]:
    keys = {
        "bootstrap_attestation",
        "default_device",
        "default_dtype",
        "environment",
        "format",
        "locked_distributions",
        "machine",
        "mps_available_but_unused",
        "numpy_version",
        "os_name",
        "platform",
        "python_implementation",
        "python_major_minor",
        "python_version",
        "torch_cuda_version",
        "torch_flags",
        "torch_version",
    }
    if type(value) is not dict or set(value) != keys:
        raise AtomicCountingExecutionIntegrityError(
            "worker environment has missing or unknown fields"
        )
    expected = {
        "default_device": "cpu",
        "default_dtype": "torch.float32",
        "environment": dict(_PINNED_ENVIRONMENT),
        "format": "heterodiff-atomic-counting-pinned-runtime-v1",
        "locked_distributions": _locked_distributions(lock_raw),
        "machine": "arm64",
        "numpy_version": "2.4.6",
        "os_name": "posix",
        "platform": "darwin",
        "python_implementation": "cpython",
        "python_major_minor": [3, 11],
        "python_version": _PINNED_PYTHON_VERSION,
        "torch_cuda_version": None,
        "torch_flags": {
            "deterministic_algorithms": True,
            "deterministic_warn_only": False,
            "mkldnn_enabled": False,
            "num_interop_threads": 1,
            "num_threads": 1,
        },
        "torch_version": "2.12.1",
    }
    for name, expected_value in expected.items():
        if value[name] != expected_value:
            raise AtomicCountingExecutionIntegrityError(
                "worker environment field {} differs from the frozen runtime".format(
                    name
                )
            )
    attestation = value["bootstrap_attestation"]
    if (
        type(attestation) is not dict
        or set(attestation) != set(expected_bootstrap_attestation)
        or attestation != dict(expected_bootstrap_attestation)
    ):
        raise AtomicCountingExecutionIntegrityError(
            "worker source-bootstrap attestation differs from the frozen runtime"
        )
    if type(value["mps_available_but_unused"]) is not bool:
        raise AtomicCountingExecutionIntegrityError(
            "worker MPS observation is invalid"
        )
    return dict(value)


def _validate_bindings(
    value: object,
    *,
    environment: Mapping[str, object],
    external: Mapping[str, str],
) -> Mapping[str, str]:
    if type(value) is not dict or set(value) != _REQUIRED_BINDING_KEYS:
        raise AtomicCountingExecutionIntegrityError(
            "worker checkpoint bindings have missing or unknown fields"
        )
    result = {}
    for name, item in value.items():
        if name == "gate_id":
            if item != _GATE_ID:
                raise AtomicCountingExecutionIntegrityError(
                    "worker gate identifier differs from the frozen gate"
                )
            result[name] = item
        else:
            result[name] = _require_sha256(item, name="binding " + name)
    expected_external = {
        **external,
        "environment_manifest": _domain_digest(
            "heterodiff.atomic-counting-local-environment.v1", environment
        ),
    }
    for name, expected in expected_external.items():
        if result[name] != expected:
            raise AtomicCountingExecutionIntegrityError(
                "worker {} binding differs from the frozen execution root".format(name)
            )
    if result["converted_state"] == result["tensor"]:
        raise AtomicCountingExecutionIntegrityError(
            "converted-state and Torch-target bindings are aliases"
        )
    return result


def _validate_stages(value: object, *, branch: str) -> Tuple[Mapping[str, object], ...]:
    required = _expected_stage_sequence(branch)
    if type(value) is not list or len(value) != len(required):
        raise AtomicCountingExecutionIntegrityError(
            "{} worker stage inventory is incomplete".format(branch)
        )
    previous_elapsed = -1.0
    previous_peak = -1
    result = []
    for index, (item, expected_stage) in enumerate(zip(value, required), start=1):
        if type(item) is not dict or set(item) != {
            "elapsed_seconds",
            "peak_rss_bytes",
            "stage",
            "stage_index",
        }:
            raise AtomicCountingExecutionIntegrityError(
                "{} stage {} has missing or unknown fields".format(branch, index)
            )
        elapsed = _finite_real(
            item["elapsed_seconds"],
            name="{} stage elapsed".format(branch),
            maximum=_MAX_RUNTIME_SECONDS,
        )
        peak = _plain_int(
            item["peak_rss_bytes"],
            name="{} stage peak RSS".format(branch),
            maximum=_MAX_RSS_BYTES,
        )
        if (
            item["stage_index"] != index
            or item["stage"] != expected_stage
            or elapsed < previous_elapsed
            or peak < previous_peak
        ):
            raise AtomicCountingExecutionIntegrityError(
                "{} stage order or monotonic observation is invalid".format(branch)
            )
        previous_elapsed = elapsed
        previous_peak = peak
        result.append(
            {
                "elapsed_seconds": elapsed,
                "peak_rss_bytes": peak,
                "stage": expected_stage,
                "stage_index": index,
            }
        )
    return tuple(result)


def _parse_worker_summary(
    result: _ProcessResult,
    *,
    domain: str,
    branch: str,
    output: _FileRecord,
    checkpoint_sha256: Optional[str],
    lock_raw: bytes,
    external: Mapping[str, str],
    expected_bootstrap_attestation: Mapping[str, object],
) -> Mapping[str, object]:
    if result.returncode != 0:
        raise AtomicCountingExecutionProcessError(
            "{} {} worker exited with code {}".format(
                domain, branch, result.returncode
            )
        )
    if result.stderr != b"":
        raise AtomicCountingExecutionProcessError(
            "{} {} worker emitted stderr".format(domain, branch)
        )
    if (
        not result.stdout.endswith(b"\n")
        or result.stdout.count(b"\n") != 1
        or b"\r" in result.stdout
    ):
        raise AtomicCountingExecutionIntegrityError(
            "{} {} worker must emit exactly one canonical JSON line".format(
                domain, branch
            )
        )
    body = result.stdout[:-1]
    value = _strict_json_bytes(body, name=domain + " " + branch + " summary")
    if type(value) is not dict or set(value) != _SUMMARY_KEYS:
        raise AtomicCountingExecutionIntegrityError(
            "{} {} worker summary has missing or unknown fields".format(
                domain, branch
            )
        )
    expected_step = 5 if branch == "prefix" else 12
    if (
        value["status"] != "restart-comparison-only"
        or value["domain"] != domain
        or value["mode"] != branch
        or value["completed_step"] != expected_step
        or value["output_sha256"] != output.sha256
    ):
        raise AtomicCountingExecutionIntegrityError(
            "{} {} worker identity/output summary is invalid".format(domain, branch)
        )
    if branch == "continuous":
        if value["checkpoint_sha256"] is not None or checkpoint_sha256 is not None:
            raise AtomicCountingExecutionIntegrityError(
                "continuous worker unexpectedly reported a checkpoint"
            )
    elif branch == "prefix":
        reported_checkpoint = _require_sha256(
            value["checkpoint_sha256"], name="prefix checkpoint digest"
        )
        if checkpoint_sha256 is not None and reported_checkpoint != checkpoint_sha256:
            raise AtomicCountingExecutionIntegrityError(
                "prefix worker checkpoint digest differs from the exact file"
            )
    elif value["checkpoint_sha256"] != checkpoint_sha256:
        raise AtomicCountingExecutionIntegrityError(
            "resume worker checkpoint digest differs from the exact file"
        )
    environment = _validate_environment(
        value["environment"],
        lock_raw=lock_raw,
        expected_bootstrap_attestation=expected_bootstrap_attestation,
    )
    bindings = _validate_bindings(
        value["checkpoint_bindings"], environment=environment, external=external
    )
    stages = _validate_stages(value["stages"], branch=branch)
    elapsed = _finite_real(
        value["elapsed_seconds"],
        name=branch + " elapsed_seconds",
        maximum=_MAX_RUNTIME_SECONDS,
    )
    peak = _plain_int(
        value["maximum_rss_bytes"],
        name=branch + " maximum_rss_bytes",
        maximum=_MAX_RSS_BYTES,
    )
    if stages[-1]["elapsed_seconds"] != elapsed or stages[-1]["peak_rss_bytes"] != peak:
        raise AtomicCountingExecutionIntegrityError(
            "{} summary maxima differ from the final monitored stage".format(branch)
        )
    return {
        **value,
        "checkpoint_bindings": dict(bindings),
        "environment": dict(environment),
        "stages": list(stages),
        "elapsed_seconds": elapsed,
        "maximum_rss_bytes": peak,
    }


def _validate_training_manifest(
    record: _FileRecord,
    *,
    domain: str,
    branch: str,
    bindings: Mapping[str, str],
) -> Mapping[str, object]:
    value = _strict_json_bytes(record.raw, name=domain + " " + branch + " manifest")
    if type(value) is not dict or set(value) != _MANIFEST_KEYS:
        raise AtomicCountingExecutionIntegrityError(
            "{} {} manifest has missing or unknown fields".format(domain, branch)
        )
    step = 5 if branch == "prefix" else 12
    expected_bindings_digest = _domain_digest(
        "heterodiff.atomic-counting-checkpoint-bindings.v1",
        {"format": _BINDINGS_FORMAT, "values": dict(bindings)},
    )
    if (
        value["format"] != _TRAINING_MANIFEST_FORMAT
        or value["gate_id"] != _GATE_ID
        or value["domain"] != domain
        or value["completed_step"] != step
        or value["bindings_digest"] != expected_bindings_digest
        or type(value["parameter_count"]) is not int
        or value["parameter_count"] < 1
        or value["parameter_count"] > 250_000
    ):
        raise AtomicCountingExecutionIntegrityError(
            "{} {} manifest identity/bindings are invalid".format(domain, branch)
        )
    _require_sha256(value["task_bundle_digest"], name="task bundle digest")
    _require_sha256(value["training_config_digest"], name="training config digest")
    records = value["step_records"]
    if type(records) is not list or len(records) != step:
        raise AtomicCountingExecutionIntegrityError(
            "{} {} manifest step records are incomplete".format(domain, branch)
        )
    expected_sequence = _TASK_SEQUENCES[domain][:step]
    for index, (item, task_index) in enumerate(zip(records, expected_sequence), start=1):
        if (
            type(item) is not dict
            or item.get("completed_step") != index
            or item.get("task_index") != task_index
            or item.get("task_id") != ("U", "A")[task_index]
        ):
            raise AtomicCountingExecutionIntegrityError(
                "{} {} manifest task sequence is invalid".format(domain, branch)
            )
    return value


def _validate_checkpoint(record: _FileRecord) -> None:
    raw = record.raw
    minimum = len(_CHECKPOINT_MAGIC) + _CHECKPOINT_HEADER_BYTES
    if len(raw) < minimum or raw[: len(_CHECKPOINT_MAGIC)] != _CHECKPOINT_MAGIC:
        raise AtomicCountingExecutionIntegrityError("checkpoint magic is invalid")
    header_size = struct.unpack(
        ">I", raw[len(_CHECKPOINT_MAGIC) : minimum]
    )[0]
    if header_size == 0 or header_size > 65_536 or minimum + header_size > len(raw):
        raise AtomicCountingExecutionIntegrityError("checkpoint header size is invalid")
    header_raw = raw[minimum : minimum + header_size]
    header = _strict_json_bytes(header_raw, name="checkpoint header")
    if type(header) is not dict or set(header) != {
        "container_version",
        "format",
        "payload_length",
        "payload_sha256",
    }:
        raise AtomicCountingExecutionIntegrityError(
            "checkpoint header has missing or unknown fields"
        )
    payload = raw[minimum + header_size :]
    if (
        header["container_version"] != 1
        or header["format"] != _CHECKPOINT_FORMAT
        or header["payload_length"] != len(payload)
        or header["payload_sha256"] != _sha256(payload)
    ):
        raise AtomicCountingExecutionIntegrityError(
            "checkpoint header/payload integrity is invalid"
        )
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload), mode="r")
    except zipfile.BadZipFile as error:
        raise AtomicCountingExecutionIntegrityError(
            "production checkpoint payload is not a bounded Torch archive"
        ) from error
    required_suffixes = {"/data.pkl", "/version", "/byteorder"}
    seen_suffixes = set()
    with archive:
        entries = archive.infolist()
        if not entries or len(entries) > 4096:
            raise AtomicCountingExecutionIntegrityError(
                "checkpoint archive entry count is invalid"
            )
        total = 0
        for entry in entries:
            parts = Path(entry.filename).parts
            if (
                not parts
                or Path(entry.filename).is_absolute()
                or ".." in parts
                or entry.file_size < 0
                or entry.compress_size < 0
                or entry.flag_bits & 0x1
            ):
                raise AtomicCountingExecutionIntegrityError(
                    "checkpoint archive contains an unsafe entry"
                )
            total += entry.file_size
            if entry.file_size > _MAX_CHECKPOINT_BYTES or total > _MAX_CHECKPOINT_BYTES:
                raise AtomicCountingExecutionIntegrityError(
                    "checkpoint expanded archive exceeds its byte ceiling"
                )
            for suffix in required_suffixes:
                if entry.filename.endswith(suffix):
                    seen_suffixes.add(suffix)
    if seen_suffixes != required_suffixes:
        raise AtomicCountingExecutionIntegrityError(
            "checkpoint archive lacks required Torch serialization entries"
        )


def _commands(
    domain: str, checkpoint_sha256: Optional[str] = None
) -> Mapping[str, Tuple[str, ...]]:
    """Return the exact source-bootstrap argv preserved in run receipts."""

    directory = "runs/{}".format(domain)
    common = (
        _PINNED_PYTHON,
        "-S",
        "-s",
        "-B",
        "-W",
        "error",
        _BOOTSTRAP_RELATIVE_PATH,
        "training-worker",
        "--domain",
        domain,
    )
    checkpoint = directory + "/step5.ckpt"
    prefix = directory + "/prefix.json"
    result = {
        "continuous": common
        + (
            "--mode",
            "continuous",
            "--output",
            directory + "/continuous.json",
        ),
        "prefix": common
        + (
            "--mode",
            "prefix",
            "--output",
            prefix,
            "--checkpoint",
            checkpoint,
        ),
    }
    if checkpoint_sha256 is not None:
        result["resume"] = common + (
            "--mode",
            "resume",
            "--output",
            directory + "/resumed.json",
            "--checkpoint",
            checkpoint,
            "--expected-checkpoint-sha",
            _require_sha256(checkpoint_sha256, name="checkpoint command digest"),
            "--prior-output",
            prefix,
        )
    return MappingProxyType(result)


def _run_branch(
    *,
    root: Path,
    domain: str,
    branch: str,
    command: Tuple[str, ...],
    checkpoint_sha256: Optional[str],
    lock_raw: bytes,
    external: Mapping[str, str],
    expected_bootstrap_attestation: Mapping[str, object],
) -> _BranchResult:
    _validate_pinned_python(
        root, expected_attestation=expected_bootstrap_attestation
    )
    # Do not inherit caller state.  These are the bootstrap's only required
    # pre-start inputs; it independently replaces the child environment.
    environment = dict(_PINNED_ENVIRONMENT)
    try:
        process = _run_worker_process(
            command, root=root, environment=environment
        )
    finally:
        _validate_pinned_python(
            root, expected_attestation=expected_bootstrap_attestation
        )
    output_token = command[command.index("--output") + 1]
    expected_output = "runs/{}/{}.json".format(
        domain, "resumed" if branch == "resume" else branch
    )
    if output_token != expected_output:
        raise AtomicCountingExecutionIntegrityError(
            "internal worker command output differs from the frozen path"
        )
    artifact = _file_record(
        root / output_token,
        limit=_MAX_OUTPUT_BYTES,
        name=domain + " " + branch + " output",
    )
    summary = _parse_worker_summary(
        process,
        domain=domain,
        branch=branch,
        output=artifact,
        checkpoint_sha256=checkpoint_sha256,
        lock_raw=lock_raw,
        external=external,
        expected_bootstrap_attestation=expected_bootstrap_attestation,
    )
    manifest = _validate_training_manifest(
        artifact,
        domain=domain,
        branch=branch,
        bindings=summary["checkpoint_bindings"],
    )
    return _BranchResult(command, summary, len(process.stdout), manifest, artifact)


def _validate_domain_relations(
    domain: str,
    branches: Mapping[str, _BranchResult],
    checkpoint: _FileRecord,
) -> None:
    if set(branches) != set(_BRANCHES):
        raise AtomicCountingExecutionIntegrityError(
            "{} branch result inventory is incomplete".format(domain)
        )
    environments = [branches[name].summary["environment"] for name in _BRANCHES]
    bindings = [branches[name].summary["checkpoint_bindings"] for name in _BRANCHES]
    if any(value != environments[0] for value in environments[1:]):
        raise AtomicCountingExecutionIntegrityError(
            "{} branch environments are not identical".format(domain)
        )
    if any(value != bindings[0] for value in bindings[1:]):
        raise AtomicCountingExecutionIntegrityError(
            "{} branch checkpoint bindings are not identical".format(domain)
        )
    continuous = branches["continuous"]
    prefix = branches["prefix"]
    resumed = branches["resume"]
    if continuous.artifact.raw != resumed.artifact.raw:
        raise AtomicCountingExecutionIntegrityError(
            "{} continuous and resumed manifests are not byte-identical".format(domain)
        )
    if prefix.manifest["step_records"] != continuous.manifest["step_records"][:5]:
        raise AtomicCountingExecutionIntegrityError(
            "{} prefix step records do not link to the continuous branch".format(domain)
        )
    for field in (
        "bindings_digest",
        "domain",
        "format",
        "gate_id",
        "global_torch_rng_state",
        "parameter_count",
        "task_bundle_digest",
        "training_config_digest",
    ):
        if prefix.manifest[field] != continuous.manifest[field]:
            raise AtomicCountingExecutionIntegrityError(
                "{} prefix field {} does not link to the continuous branch".format(
                    domain, field
                )
            )
    if (
        prefix.summary["checkpoint_sha256"] != checkpoint.sha256
        or resumed.summary["checkpoint_sha256"] != checkpoint.sha256
    ):
        raise AtomicCountingExecutionIntegrityError(
            "{} prefix/resume checkpoint linkage is invalid".format(domain)
        )
    continuous_elapsed = float(continuous.summary["elapsed_seconds"])
    interrupted_elapsed = float(prefix.summary["elapsed_seconds"]) + float(
        resumed.summary["elapsed_seconds"]
    )
    if continuous_elapsed > _MAX_RUNTIME_SECONDS:
        raise AtomicCountingExecutionIntegrityError(
            "{} continuous branch exceeded 120 seconds".format(domain)
        )
    if interrupted_elapsed > _MAX_RUNTIME_SECONDS:
        raise AtomicCountingExecutionIntegrityError(
            "{} prefix-plus-resume branch exceeded 120 seconds".format(domain)
        )


def _artifact_entries(
    branches: Mapping[str, _BranchResult], checkpoint: _FileRecord
) -> Mapping[str, Mapping[str, object]]:
    records = {
        "checkpoint": checkpoint,
        "continuous_manifest": branches["continuous"].artifact,
        "prefix_manifest": branches["prefix"].artifact,
        "resumed_manifest": branches["resume"].artifact,
    }
    return {
        name: {"sha256": record.sha256, "size_bytes": record.size_bytes}
        for name, record in sorted(records.items())
    }


def _receipt(
    domain: str,
    branches: Mapping[str, _BranchResult],
    checkpoint: _FileRecord,
) -> Mapping[str, object]:
    first = branches["continuous"].summary
    return {
        "artifact_kind": "completed-training-run",
        "artifacts": _artifact_entries(branches, checkpoint),
        "checkpoint_bindings": dict(first["checkpoint_bindings"]),
        "domain": domain,
        "environment": dict(first["environment"]),
        "gate_id": _GATE_ID,
        "resources": {
            "limits": {
                "batch_size": 1,
                "checkpoint_bytes": _MAX_CHECKPOINT_BYTES,
                "log_bytes": _MAX_LOG_BYTES,
                "output_bytes": _MAX_OUTPUT_BYTES,
                "parameter_count": 250_000,
                "peak_rss_bytes": _MAX_RSS_BYTES,
                "runtime_seconds": _MAX_RUNTIME_SECONDS,
                "training_steps": 12,
                "worker_processes": 0,
            },
            "observations": {
                branch: {
                    "log_bytes": branches[branch].stdout_bytes,
                    "output_bytes": branches[branch].artifact.size_bytes,
                    "stages": list(branches[branch].summary["stages"]),
                }
                for branch in _BRANCHES
            },
        },
        "schema_version": _RECEIPT_SCHEMA,
        "synthetic_test_only": False,
        "training_commands": {
            branch: list(branches[branch].command) for branch in _BRANCHES
        },
    }


def _atomic_write_no_replace(path: Path, payload: bytes) -> str:
    if len(payload) > _MAX_LOG_BYTES:
        raise AtomicCountingExecutionPublicationError(
            "production receipt exceeds its byte ceiling"
        )
    parent = path.parent
    if not parent.is_dir() or parent.is_symlink() or os.path.lexists(path):
        raise AtomicCountingExecutionPublicationError(
            "receipt destination is not one absent child of the owned run directory"
        )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".{}-".format(path.name), suffix=".tmp", dir=str(parent)
    )
    temporary = Path(temporary_name)
    linked = False
    try:
        os.fchmod(descriptor, 0o600)
        view = memoryview(payload)
        offset = 0
        while offset < len(view):
            written = os.write(descriptor, view[offset:])
            if written <= 0:
                raise AtomicCountingExecutionPublicationError(
                    "receipt temporary write made no progress"
                )
            offset += written
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise AtomicCountingExecutionPublicationError(
                "receipt destination appeared before no-replace publication"
            ) from error
        linked = True
        directory_fd = os.open(
            parent,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        if linked:
            try:
                linked_status = path.lstat()
                temporary_status = temporary.lstat()
                if (
                    linked_status.st_dev == temporary_status.st_dev
                    and linked_status.st_ino == temporary_status.st_ino
                ):
                    path.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return _sha256(payload)


def _fsync_completed_tree(root: Path, output: Path) -> None:
    for path in (output / "music", output / "clinical_style", output, root):
        descriptor = os.open(
            path,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def execute_atomic_counting_runs(
    output_root: str = _OUTPUT_ROOT,
) -> AtomicCountingExecutionResult:
    """Create both completed-run input sets, still awaiting independent audit.

    ``output_root`` exists only to make the frozen value explicit; production
    accepts exactly ``"runs"``.  The directory must not already exist.
    """

    root = _project_root()
    _reject_symlink_components(root, final_must_exist=True)
    bootstrap_attestation = _validate_pinned_python(root)
    _validate_parent_bootstrap_attestation(bootstrap_attestation)
    external_before, lock_raw = _external_digests(root)
    output, identities = _prepare_output_root(root, output_root)
    domain_results: Dict[str, Mapping[str, _BranchResult]] = {}
    checkpoints: Dict[str, _FileRecord] = {}
    try:
        for domain in _DOMAINS:
            branches: Dict[str, _BranchResult] = {}
            initial_commands = _commands(domain)
            branches["continuous"] = _run_branch(
                root=root,
                domain=domain,
                branch="continuous",
                command=initial_commands["continuous"],
                checkpoint_sha256=None,
                lock_raw=lock_raw,
                external=external_before,
                expected_bootstrap_attestation=bootstrap_attestation,
            )
            branches["prefix"] = _run_branch(
                root=root,
                domain=domain,
                branch="prefix",
                command=initial_commands["prefix"],
                checkpoint_sha256=None,
                lock_raw=lock_raw,
                external=external_before,
                expected_bootstrap_attestation=bootstrap_attestation,
            )
            checkpoint = _file_record(
                root / "runs" / domain / "step5.ckpt",
                limit=_MAX_CHECKPOINT_BYTES,
                name=domain + " checkpoint",
            )
            _validate_checkpoint(checkpoint)
            # Prefix is parsed a second time with the now-observed checkpoint
            # identity; its original summary is otherwise immutable.
            if branches["prefix"].summary["checkpoint_sha256"] != checkpoint.sha256:
                raise AtomicCountingExecutionIntegrityError(
                    "{} prefix summary does not bind the checkpoint file".format(domain)
                )
            resume_command = _commands(domain, checkpoint.sha256)["resume"]
            branches["resume"] = _run_branch(
                root=root,
                domain=domain,
                branch="resume",
                command=resume_command,
                checkpoint_sha256=checkpoint.sha256,
                lock_raw=lock_raw,
                external=external_before,
                expected_bootstrap_attestation=bootstrap_attestation,
            )
            _validate_domain_relations(domain, branches, checkpoint)
            domain_results[domain] = MappingProxyType(dict(branches))
            checkpoints[domain] = checkpoint

        environments = [
            domain_results[domain]["continuous"].summary["environment"]
            for domain in _DOMAINS
        ]
        if environments[0] != environments[1]:
            raise AtomicCountingExecutionIntegrityError(
                "music and clinical-style workers did not share one pinned environment"
            )
        external_names = (
            "code_source",
            "dependency_lock",
            "environment_manifest",
            "gate_id",
            "gate_spec",
        )
        music_bindings = domain_results["music"]["continuous"].summary[
            "checkpoint_bindings"
        ]
        clinical_bindings = domain_results["clinical_style"]["continuous"].summary[
            "checkpoint_bindings"
        ]
        for name in external_names:
            if music_bindings[name] != clinical_bindings[name]:
                raise AtomicCountingExecutionIntegrityError(
                    "cross-domain external binding {} differs".format(name)
                )
        _validate_pinned_python(
            root, expected_attestation=bootstrap_attestation
        )
        external_after, lock_after = _external_digests(root)
        if external_after != external_before or lock_after != lock_raw:
            raise AtomicCountingExecutionIntegrityError(
                "source tree, dependency lock, or gate specification changed during execution"
            )

        receipt_payloads = {
            domain: _canonical_json_bytes(
                _receipt(domain, domain_results[domain], checkpoints[domain])
            )
            for domain in _DOMAINS
        }
        receipt_digests = {}
        # Receipts are the final files created.  A failure after the first link
        # removes the entire invocation-owned tree, including that receipt.
        for domain in _DOMAINS:
            receipt_digests[domain] = _atomic_write_no_replace(
                output / domain / "receipt.json", receipt_payloads[domain]
            )
        _fsync_completed_tree(root, output)
        return AtomicCountingExecutionResult(
            output_root=output.resolve(strict=True),
            status="RUN_INPUTS_COMPLETE_AWAITING_INDEPENDENT_AUDIT",
            receipt_sha256=receipt_digests,
        )
    except BaseException:
        _cleanup_owned_output(output, identities)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Torch-free parent for the frozen six-process atomic-counting run"
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="report NOT_EXECUTED without artifact I/O")
    commands.add_parser(
        "run",
        help=(
            "create exact runs/ inputs and receipts; audit/publication remain separate"
        ),
    )
    return parser


def main(arguments: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(arguments)
    if args.command == "status":
        sys.stdout.write(_canonical_json_bytes(dict(repository_execution_status())).decode() + "\n")
        return 0
    try:
        result = execute_atomic_counting_runs()
        payload = {
            "gate_decision": "NOT_MADE_BY_EXECUTOR",
            "output_root": _OUTPUT_ROOT,
            "receipt_sha256": dict(result.receipt_sha256),
            "status": result.status,
        }
        sys.stdout.write(_canonical_json_bytes(payload).decode() + "\n")
        return 0
    except (AtomicCountingExecutionError, OSError, ValueError, TypeError) as error:
        payload = {
            "error_type": type(error).__name__,
            "message": str(error),
            "status": "HOLD",
        }
        sys.stderr.write(_canonical_json_bytes(payload).decode() + "\n")
        return 2


__all__ = [
    "AtomicCountingExecutionError",
    "AtomicCountingExecutionInputError",
    "AtomicCountingExecutionIntegrityError",
    "AtomicCountingExecutionProcessError",
    "AtomicCountingExecutionPublicationError",
    "AtomicCountingExecutionResult",
    "EXECUTION_IMPLEMENTATION_BLOCKER",
    "EXECUTION_IMPLEMENTATION_STATUS",
    "assert_stdlib_only_parent",
    "execute_atomic_counting_runs",
    "main",
    "repository_execution_status",
]


if __name__ == "__main__":  # pragma: no cover - exercised by shell invocation
    raise SystemExit(main())
