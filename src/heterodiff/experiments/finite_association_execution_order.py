"""No-execution ordering foundation for the frozen finite A1 campaign.

This standard-library-only module is not integrated with the rank, exact,
sampled, decision, or audit runners and therefore does **not** yet block or
authorize any real run.  It records an immutable plan, test-only state
transitions, and single-use phase-authorization custody that later integration
may bind to runner-specific permits.  Evidence references are opaque digests;
this foundation does not validate scientific evidence or mint finalized
decision wrappers.  Every persisted schema is explicitly namespaced
``TEST_ONLY_NO_RUN`` so these records cannot be mistaken for a later
production-order protocol.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
from types import MappingProxyType
from typing import Any, Dict, Iterator, Mapping, Optional, Sequence, Tuple


PLAN_SCHEMA = (
    "heterodiff-a1-finite-association-test-only-no-run-execution-plan-v2"
)
EVENT_SCHEMA = (
    "heterodiff-a1-finite-association-test-only-no-run-execution-event-v2"
)
EVIDENCE_SCHEMA = "heterodiff-a1-finite-association-opaque-evidence-reference-v1"
AUTHORIZATION_SCHEMA = (
    "heterodiff-a1-finite-association-test-only-no-run-phase-authorization-v2"
)
AUTHORIZATION_CONSUMPTION_SCHEMA = (
    "heterodiff-a1-finite-association-test-only-no-run-authorization-consumption-v2"
)
ARTIFACT_IDENTITY_SCHEMA = "heterodiff-a1-finite-association-artifact-identity-v1"
AUTHORITY_DOMAIN = "TEST_ONLY_NO_RUN"
ARTIFACT_DIRECTORY_NAME = "a1_finite_association_execution_order"
ARTIFACT_RELATIVE_PATH = "artifacts/" + ARTIFACT_DIRECTORY_NAME
PLAN_FILE_NAME = "plan.json"
EVENT_DIRECTORY_NAME = "events"
AUTHORIZATION_DIRECTORY_NAME = "authorizations"
LOCK_FILE_NAME = ".ledger.lock"
MAXIMUM_PLAN_BYTES = 1_048_576
MAXIMUM_EVENT_BYTES = 131_072
MAXIMUM_AUTHORIZATION_BYTES = 65_536
GENESIS_EVENT_SHA256 = "0" * 64
_PENDING_FILE_PREFIX = ".pending-uncommitted-"
_PENDING_NONCE_HEX_LENGTH = 32

PAIRED_SEEDS = (1729, 3253, 5003, 7411, 10007, 13007, 16001, 20011)
EXACT_METHODS = ("direct", "guided", "strong_direct")
SAMPLED_METHODS = ("direct", "guided", "strong_direct", "guide_input", "mismatch")
SAMPLE_BUDGETS = (512, 4096, 32768)

EXACT_COORDINATES = tuple((seed, method) for seed in PAIRED_SEEDS for method in EXACT_METHODS)
PRIMARY_COORDINATES = tuple(
    (seed, budget, method)
    for seed in PAIRED_SEEDS
    for budget in SAMPLE_BUDGETS
    for method in ("direct", "guided")
)
CONTROL_COORDINATES = tuple(
    (seed, budget, method)
    for seed in PAIRED_SEEDS
    for budget in SAMPLE_BUDGETS
    for method in ("strong_direct", "guide_input", "mismatch")
)
# The complete manifest is ordered by the actual sampled-run key, while the
# primary/control manifests preserve their own decision-subset order.
COMPLETE_SAMPLED_COORDINATES = tuple(
    (seed, budget, method)
    for seed in PAIRED_SEEDS
    for budget in SAMPLE_BUDGETS
    for method in SAMPLED_METHODS
)

ORDERED_STATES = (
    "NEW",
    "PREREQUISITE_VERIFIED",
    "RANK_AUTHORIZED",
    "RANK_VERIFIED",
    "EXACT_AUTHORIZED",
    "EXACT_RUNNING",
    "EXACT_AGGREGATED",
    "PRIMARY_AUTHORIZED",
    "PRIMARY_RUNNING",
    "PRIMARY_SUCCESS_SET",
    "PRIMARY_METRICS_COMMITTED",
    "CONTROLS_AUTHORIZED",
    "CONTROLS_RUNNING",
    "SAMPLED_SUCCESS_SET",
    "SAMPLED_AGGREGATED",
    "DECISION_AUTHORIZED",
    "DECISION_CANDIDATE",
    "AUDIT_AUTHORIZED",
    "FINALIZED",
)
TERMINAL_STATES = ("HOLD", "FAILURE")
AUTHORIZATION_STATES = (
    "RANK_AUTHORIZED",
    "EXACT_AUTHORIZED",
    "PRIMARY_AUTHORIZED",
    "CONTROLS_AUTHORIZED",
    "DECISION_AUTHORIZED",
    "AUDIT_AUTHORIZED",
)
_STATE_INDEX = {state: index for index, state in enumerate(ORDERED_STATES)}
_SNAPSHOT_CONSTRUCTION_KEY = object()
_AUTHORIZATION_CONSTRUCTION_KEY = object()
_CONSUMPTION_CONSTRUCTION_KEY = object()

_REQUIRED_NONPACKAGE_SOURCE_PATHS = (
    "pyproject.toml",
    "requirements/m1-reference-macos-arm64-py311.lock",
    "research/62_a1_association_guided_residual_falsification_spec.md",
)
SPECIFICATION_SOURCE_PATH = "research/62_a1_association_guided_residual_falsification_spec.md"
NON_HOSTILE_HOST_THREAT_MODEL = (
    "This ledger is custody and API enforcement on a non-hostile host; it does not "
    "authenticate a local adversary able to modify processes or the filesystem."
)


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                          allow_nan=False).encode("ascii")
    except (TypeError, ValueError) as error:
        raise TypeError("value is not canonical JSON serializable") from error


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _deep_freeze(value: object) -> object:
    """Recursively detach and freeze one already-validated JSON value."""
    if type(value) is dict:
        return MappingProxyType(
            {key: _deep_freeze(item) for key, item in value.items()}
        )
    if type(value) is list:
        return tuple(_deep_freeze(item) for item in value)
    return value


def _frozen_runtime_contract_record() -> Dict[str, Any]:
    """Return a detached literal; validation never trusts a live public object."""

    return {
        "schema": "heterodiff-a1-frozen-runtime-contract-v1",
        "python": "3.11.5",
        "numpy": "2.4.6",
        "scipy": "1.17.1",
        "torch": "2.12.1",
        "threadpoolctl": "3.6.0",
        "python_implementation": "CPython",
        "cpu_only": True,
        "accelerators_hidden": True,
        "thread_environment": {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "BLIS_NUM_THREADS": "1",
            "PYTHONHASHSEED": "0",
            "CUDA_VISIBLE_DEVICES": "",
        },
        "deterministic_algorithms": True,
        "torch_intraop_threads": 1,
        "torch_interop_threads": 1,
        "native_pool_contract": {
            "minimum_discovered_pool_count": 1,
            "every_discovered_pool_thread_count": 1,
        },
        "numpy_build_configuration_nonempty": True,
        "host_identity_contract": {
            "os_name_nonempty": True,
            "platform_nonempty": True,
            "machine_nonempty": True,
            "cpu_identity_nonempty": True,
        },
    }


# Public inspection is supported, mutation is not.  Plan construction and
# validation deliberately call the fresh-literal factory above instead of
# consulting this name, so rebinding it cannot weaken the persisted contract.
FROZEN_RUNTIME_CONTRACT = _deep_freeze(_frozen_runtime_contract_record())


def _artifact_identity(workspace_root: Path) -> Dict[str, str]:
    resolved = (workspace_root / ARTIFACT_RELATIVE_PATH).resolve(strict=False)
    body = {
        "schema": ARTIFACT_IDENTITY_SCHEMA,
        "relative_path": ARTIFACT_RELATIVE_PATH,
        "resolved_path_sha256": hashlib.sha256(
            b"heterodiff-a1-artifact-path-v1\0" + os.fsencode(str(resolved))
        ).hexdigest(),
    }
    body["identity_sha256"] = _sha256_json(body)
    return body


def _sha256_file(path: Path, maximum_bytes: int = MAXIMUM_PLAN_BYTES * 16) -> Tuple[str, int]:
    before = path.stat()
    if not path.is_file() or path.is_symlink() or before.st_size > maximum_bytes:
        raise ValueError("source identity requires a bounded regular non-symlink file: %s" % path)
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            block = handle.read(65536)
            if not block:
                break
            size += len(block)
            if size > maximum_bytes:
                raise ValueError("source file exceeds byte bound")
            digest.update(block)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ):
        raise RuntimeError("source changed while its identity was read: %s" % path)
    return digest.hexdigest(), size


def _is_sha256(value: object) -> bool:
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _relative_path(value: object) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError("source path must be a nonempty relative POSIX path")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts) or value.startswith("/"):
        raise ValueError("source path is not canonical")
    return value


def _discover_source_paths(workspace_root: Path) -> Tuple[str, ...]:
    """Return the complete deterministic local Python-code closure."""

    root = workspace_root.resolve(strict=True)
    package_root = root / "src" / "heterodiff"
    if package_root.is_symlink() or not package_root.is_dir():
        raise ValueError("src/heterodiff must be a regular non-symlink directory")
    python_paths = []
    for current, directory_names, file_names in os.walk(
        str(package_root), followlinks=False
    ):
        current_path = Path(current)
        for directory_name in directory_names:
            child = current_path / directory_name
            if child.is_symlink():
                raise ValueError("Python source tree may not contain symlink directories")
        for file_name in file_names:
            if not file_name.endswith(".py"):
                continue
            candidate = current_path / file_name
            if candidate.is_symlink() or not candidate.is_file():
                raise ValueError("Python source closure requires regular non-symlink files")
            python_paths.append(candidate.relative_to(root).as_posix())
    paths = tuple(sorted((*_REQUIRED_NONPACKAGE_SOURCE_PATHS, *python_paths)))
    if len(paths) != len(set(paths)):
        raise ValueError("source closure contains duplicate paths")
    for relative in paths:
        _relative_path(relative)
        candidate = root / relative
        if candidate.is_symlink() or not candidate.is_file():
            raise ValueError("required source is not a regular non-symlink file: %s" % relative)
    return paths


# This tuple is an inspection aid and a test-fixture template.  Every plan
# creation and load performs a fresh tree discovery; neither operation trusts
# this import-time snapshot.
_MODULE_WORKSPACE_ROOT = Path(__file__).resolve(strict=True).parents[3]
DEFAULT_SOURCE_PATHS = _discover_source_paths(_MODULE_WORKSPACE_ROOT)


def _read_json_bounded(path: Path, maximum_bytes: int) -> Dict[str, Any]:
    try:
        status = path.lstat()
    except FileNotFoundError:
        raise
    if path.is_symlink() or not path.is_file() or status.st_size > maximum_bytes:
        raise ValueError("ledger file is not a bounded regular file: %s" % path)
    with path.open("rb") as handle:
        data = handle.read(maximum_bytes + 1)
    if len(data) > maximum_bytes:
        raise ValueError("ledger file exceeds its byte bound")
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("ledger file is not valid UTF-8 JSON: %s" % path) from error
    if type(value) is not dict or _canonical_json(value) != data:
        raise ValueError("ledger file is not canonical JSON: %s" % path)
    return value


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(str(directory), flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_directory_durable(directory: Path) -> None:
    """Create missing directory components and fsync each parent entry."""

    missing = []
    cursor = directory
    while not cursor.exists():
        missing.append(cursor)
        if cursor.parent == cursor:
            raise ValueError("cannot find an existing parent directory")
        cursor = cursor.parent
    if cursor.is_symlink() or not cursor.is_dir():
        raise ValueError("directory ancestry is not a regular directory")
    for candidate in reversed(missing):
        try:
            candidate.mkdir(mode=0o700)
        except FileExistsError:
            if candidate.is_symlink() or not candidate.is_dir():
                raise ValueError("directory path was replaced during creation")
        _fsync_directory(candidate.parent)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("target directory is not a regular non-symlink directory")


def _new_pending_file(parent: Path) -> Tuple[int, Path]:
    for _ in range(128):
        path = parent / (_PENDING_FILE_PREFIX + secrets.token_hex(16))
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            return os.open(str(path), flags, 0o600), path
        except FileExistsError:
            continue
    raise RuntimeError("could not allocate a unique pending ledger file")


def _is_pending_file_name(name: str) -> bool:
    if not name.startswith(_PENDING_FILE_PREFIX):
        return False
    suffix = name[len(_PENDING_FILE_PREFIX):]
    return (
        len(suffix) == _PENDING_NONCE_HEX_LENGTH
        and all(character in "0123456789abcdef" for character in suffix)
    )


def _reconcile_one_pending_directory_locked(directory: Path) -> None:
    """Durably remove exact abandoned pending names while holding the lock."""
    try:
        status = directory.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISDIR(status.st_mode):
        raise ValueError("pending-custody path is not a regular directory")
    pending_paths = []
    for path in directory.iterdir():
        if not path.name.startswith(_PENDING_FILE_PREFIX):
            continue
        if not _is_pending_file_name(path.name):
            raise ValueError("malformed pending ledger filename")
        status = path.lstat()
        if not stat.S_ISREG(status.st_mode):
            raise ValueError("pending ledger path is not a regular file")
        pending_paths.append(path)
    if not pending_paths:
        return
    # A canonical hard link may have become visible immediately before its
    # writer died.  Promote every visible directory entry before discarding
    # the uncommitted peer name, then durably record each removal.
    _fsync_directory(directory)
    for path in sorted(pending_paths, key=lambda item: item.name):
        path.unlink()
    _fsync_directory(directory)


def _reconcile_pending_entries_locked(artifact_directory: Path) -> None:
    for directory in (
        artifact_directory,
        artifact_directory / EVENT_DIRECTORY_NAME,
        artifact_directory / AUTHORIZATION_DIRECTORY_NAME,
    ):
        _reconcile_one_pending_directory_locked(directory)


def _atomic_exclusive_json(path: Path, value: Mapping[str, Any]) -> None:
    """Publish one canonical file with fsync and an exclusive atomic link."""
    payload = _canonical_json(dict(value))
    parent = path.parent
    _ensure_directory_durable(parent)
    fd, temporary = _new_pending_file(parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(str(temporary), str(path))
        except FileExistsError:
            raise FileExistsError("append-only ledger file already exists: %s" % path)
        _fsync_directory(parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        else:
            # The first directory fsync makes the canonical hard link durable;
            # this second one makes removal of its temporary peer durable.
            _fsync_directory(parent)


@contextmanager
def _locked_artifact_directory(directory: Path) -> Iterator[None]:
    """Hold the campaign lock while callers reload and mutate custody files."""
    if directory.name != ARTIFACT_DIRECTORY_NAME or directory.parent.name != "artifacts":
        raise ValueError("ledger is not in the canonical artifact directory")
    lock_path = directory / LOCK_FILE_NAME
    _ensure_directory_durable(lock_path.parent)
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    existed = lock_path.exists()
    lock_fd = os.open(str(lock_path), flags, 0o600)
    if not existed:
        os.fsync(lock_fd)
        _fsync_directory(lock_path.parent)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        _reconcile_pending_entries_locked(directory)
        yield
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


@dataclass(frozen=True)
class SourcePathIdentity:
    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        _relative_path(self.path)
        if not _is_sha256(self.sha256):
            raise ValueError("source sha256 must be lowercase SHA-256")
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise ValueError("source size_bytes must be a nonnegative integer")


@dataclass(frozen=True)
class EvidenceReference:
    """Opaque caller-asserted digest; no content or scientific validation."""
    evidence_id: str
    sha256: str

    def __post_init__(self) -> None:
        if type(self.evidence_id) is not str or not self.evidence_id:
            raise ValueError("evidence_id must be nonempty")
        if not _is_sha256(self.sha256):
            raise ValueError("evidence sha256 must be lowercase SHA-256")

    def as_record(self) -> Dict[str, Any]:
        return {
            "schema": EVIDENCE_SCHEMA,
            "evidence_id": self.evidence_id,
            "sha256": self.sha256,
            "digest_only": True,
            "scientific_evidence_validated": False,
        }


class PhaseAuthorizationReceipt:
    """Loader-only, immutable custody receipt; explicitly not a run permit."""

    __slots__ = ("_artifact_directory", "_record")

    def __init__(self, key: object, artifact_directory: Path,
                 record: Mapping[str, Any]) -> None:
        if key is not _AUTHORIZATION_CONSTRUCTION_KEY:
            raise TypeError("PhaseAuthorizationReceipt is loader-only")
        object.__setattr__(self, "_artifact_directory", artifact_directory)
        object.__setattr__(self, "_record", _deep_freeze(dict(record)))

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("PhaseAuthorizationReceipt is immutable")

    @property
    def artifact_directory(self) -> Path:
        return self._artifact_directory

    @property
    def phase(self) -> str:
        return self._record["phase"]  # type: ignore[return-value]

    @property
    def plan_sha256(self) -> str:
        return self._record["plan_sha256"]  # type: ignore[return-value]

    @property
    def head_event_sha256(self) -> str:
        return self._record["head_event_sha256"]  # type: ignore[return-value]

    @property
    def receipt_sha256(self) -> str:
        return self._record["authorization_sha256"]  # type: ignore[return-value]

    @property
    def record(self) -> Mapping[str, Any]:
        return self._record

    def assert_binds(self, phase: str) -> None:
        assert_phase_authorization(self, phase)

    def consume(self, phase: str, consumer_id: str) -> "PhaseAuthorizationConsumptionReceipt":
        return consume_phase_authorization(self, phase, consumer_id)


class PhaseAuthorizationConsumptionReceipt:
    """Loader-only immutable record of one atomic authorization consumption."""

    __slots__ = ("_artifact_directory", "_record")

    def __init__(self, key: object, artifact_directory: Path,
                 record: Mapping[str, Any]) -> None:
        if key is not _CONSUMPTION_CONSTRUCTION_KEY:
            raise TypeError("PhaseAuthorizationConsumptionReceipt is loader-only")
        object.__setattr__(self, "_artifact_directory", artifact_directory)
        object.__setattr__(self, "_record", _deep_freeze(dict(record)))

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("PhaseAuthorizationConsumptionReceipt is immutable")

    @property
    def phase(self) -> str:
        return self._record["phase"]  # type: ignore[return-value]

    @property
    def consumption_sha256(self) -> str:
        return self._record["consumption_sha256"]  # type: ignore[return-value]

    @property
    def record(self) -> Mapping[str, Any]:
        return self._record


class ExecutionOrderSnapshot:
    """Immutable status view; instances may only be returned by the loader."""
    __slots__ = ("artifact_directory", "plan_sha256", "state", "head_event_sha256", "event_count", "_plan")

    def __init__(self, key: object, artifact_directory: Path, plan: Mapping[str, Any], state: str,
                 head_event_sha256: str, event_count: int) -> None:
        if key is not _SNAPSHOT_CONSTRUCTION_KEY:
            raise TypeError("ExecutionOrderSnapshot is loader-only; use load_execution_order_snapshot")
        object.__setattr__(self, "artifact_directory", artifact_directory)
        object.__setattr__(self, "plan_sha256", plan["plan_sha256"])
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "head_event_sha256", head_event_sha256)
        object.__setattr__(self, "event_count", event_count)
        object.__setattr__(self, "_plan", _deep_freeze(dict(plan)))

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("ExecutionOrderSnapshot is immutable")

    @property
    def plan(self) -> Mapping[str, Any]:
        return self._plan

    def issue_phase_authorization(self, phase: str) -> PhaseAuthorizationReceipt:
        return issue_phase_authorization(self.artifact_directory, phase)


def canonical_artifact_directory(workspace_root: os.PathLike) -> Path:
    root = Path(workspace_root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("workspace root must be a directory")
    return root / "artifacts" / ARTIFACT_DIRECTORY_NAME


def source_path_identity(workspace_root: os.PathLike, relative_path: str) -> SourcePathIdentity:
    root = Path(workspace_root).resolve(strict=True)
    relative = _relative_path(relative_path)
    candidate = root / relative
    resolved = candidate.resolve(strict=True)
    if root not in resolved.parents and resolved != root:
        raise ValueError("source path escapes workspace root")
    digest, size = _sha256_file(candidate)
    return SourcePathIdentity(relative, digest, size)


def _coordinate_payload() -> Dict[str, Any]:
    return {
        "exact": [[seed, method] for seed, method in EXACT_COORDINATES],
        "primary": [[seed, budget, method] for seed, budget, method in PRIMARY_COORDINATES],
        "controls": [[seed, budget, method] for seed, budget, method in CONTROL_COORDINATES],
        "complete_sampled": [[seed, budget, method] for seed, budget, method in COMPLETE_SAMPLED_COORDINATES],
    }


def _validate_coordinates(value: object) -> None:
    if type(value) is not dict or set(value) != {"exact", "primary", "controls", "complete_sampled"}:
        raise ValueError("plan coordinate schema is invalid")
    expected = _coordinate_payload()
    if value != expected or (len(value["exact"]), len(value["primary"]), len(value["controls"]), len(value["complete_sampled"])) != (24, 48, 72, 120):
        raise ValueError("plan coordinate sets or order are not frozen")


def _plan_body(workspace_root: Path, sources: Sequence[str]) -> Dict[str, Any]:
    identities = [asdict(source_path_identity(workspace_root, path)) for path in sources]
    specification = next(item for item in identities if item["path"] == SPECIFICATION_SOURCE_PATH)
    body = {"schema": PLAN_SCHEMA, "artifact_directory_name": ARTIFACT_DIRECTORY_NAME,
            "specification": specification, "source_paths": identities,
            "coordinates": _coordinate_payload(), "transition_states": list(ORDERED_STATES),
            "terminal_states": list(TERMINAL_STATES),
            "authorization_states": list(AUTHORIZATION_STATES),
            "campaign_instance_nonce_sha256": hashlib.sha256(secrets.token_bytes(32)).hexdigest(),
            "artifact_identity": _artifact_identity(workspace_root),
            "runtime_contract": _frozen_runtime_contract_record(),
            "threat_model": NON_HOSTILE_HOST_THREAT_MODEL,
            "authority_domain": AUTHORITY_DOMAIN,
            "test_only_no_run": True,
            "runner_integration_complete": False,
            "scientific_evidence_validated": False}
    body["source_manifest_sha256"] = _sha256_json(identities)
    return body


def initialize_execution_order_plan(workspace_root: os.PathLike,
                                    source_paths: Optional[Sequence[str]] = None) -> ExecutionOrderSnapshot:
    """Create the one canonical plan; a second initialization is rejected."""
    root = Path(workspace_root).resolve(strict=True)
    artifact_directory = canonical_artifact_directory(root)
    with _locked_artifact_directory(artifact_directory):
        discovered_paths = _discover_source_paths(root)
        if source_paths is not None and tuple(source_paths) != discovered_paths:
            raise ValueError("the execution-order source-path manifest is frozen")
        body = _plan_body(root, discovered_paths)
        plan = dict(body)
        plan["plan_sha256"] = _sha256_json(body)
        _atomic_exclusive_json(artifact_directory / PLAN_FILE_NAME, plan)
        return _load_execution_order_snapshot_locked(artifact_directory)


def _validate_plan(plan: Mapping[str, Any], expected_source_paths: Sequence[str]) -> None:
    required = {"schema", "artifact_directory_name", "specification", "source_paths", "coordinates",
                "transition_states", "terminal_states", "authorization_states",
                "campaign_instance_nonce_sha256", "artifact_identity", "runtime_contract",
                "threat_model", "authority_domain", "test_only_no_run",
                "runner_integration_complete", "scientific_evidence_validated",
                "source_manifest_sha256", "plan_sha256"}
    if set(plan) != required or plan.get("schema") != PLAN_SCHEMA or plan.get("artifact_directory_name") != ARTIFACT_DIRECTORY_NAME:
        raise ValueError("plan schema is invalid")
    _validate_coordinates(plan["coordinates"])
    if plan["transition_states"] != list(ORDERED_STATES) or plan["terminal_states"] != list(TERMINAL_STATES):
        raise ValueError("plan transition graph is invalid")
    if plan["authorization_states"] != list(AUTHORIZATION_STATES):
        raise ValueError("plan authorization-state allowlist is invalid")
    identities = plan["source_paths"]
    if type(identities) is not list or len(identities) != len(expected_source_paths):
        raise ValueError("plan source manifest is invalid")
    for expected_path, item in zip(expected_source_paths, identities):
        if type(item) is not dict or set(item) != {"path", "sha256", "size_bytes"}:
            raise ValueError("plan source identity schema is invalid")
        if item["path"] != expected_path:
            raise ValueError("plan source manifest paths/order are not frozen")
    parsed = tuple(SourcePathIdentity(**item) for item in identities)
    specification = plan["specification"]
    if type(specification) is not dict or set(specification) != {"path", "sha256", "size_bytes"}:
        raise ValueError("plan specification identity schema is invalid")
    expected_specification = next(
        asdict(identity) for identity in parsed if identity.path == SPECIFICATION_SOURCE_PATH
    )
    if specification != expected_specification or _sha256_json(identities) != plan["source_manifest_sha256"]:
        raise ValueError("plan specification/source identity binding is invalid")
    body = {key: value for key, value in plan.items() if key != "plan_sha256"}
    if not _is_sha256(plan["plan_sha256"]) or _sha256_json(body) != plan["plan_sha256"]:
        raise ValueError("plan digest is invalid")
    if not _is_sha256(plan["campaign_instance_nonce_sha256"]):
        raise ValueError("campaign-instance nonce digest is invalid")
    artifact_identity = plan["artifact_identity"]
    if type(artifact_identity) is not dict or set(artifact_identity) != {
        "schema", "relative_path", "resolved_path_sha256", "identity_sha256"
    }:
        raise ValueError("artifact-path identity schema is invalid")
    artifact_body = {
        key: value for key, value in artifact_identity.items()
        if key != "identity_sha256"
    }
    if (artifact_identity["schema"] != ARTIFACT_IDENTITY_SCHEMA
            or artifact_identity["relative_path"] != ARTIFACT_RELATIVE_PATH
            or not _is_sha256(artifact_identity["resolved_path_sha256"])
            or _sha256_json(artifact_body) != artifact_identity["identity_sha256"]):
        raise ValueError("artifact-path identity is invalid")
    if plan["runtime_contract"] != _frozen_runtime_contract_record():
        raise ValueError("frozen runtime contract is invalid")
    if plan["threat_model"] != NON_HOSTILE_HOST_THREAT_MODEL:
        raise ValueError("threat model is invalid")
    if (plan["authority_domain"] != AUTHORITY_DOMAIN
            or plan["test_only_no_run"] is not True
            or plan["runner_integration_complete"] is not False
            or plan["scientific_evidence_validated"] is not False):
        raise ValueError("foundation may not claim runner integration or evidence validation")


def _event_path(artifact_directory: Path, ordinal: int) -> Path:
    return artifact_directory / EVENT_DIRECTORY_NAME / ("%012d.json" % ordinal)


def _validate_event(event: Mapping[str, Any], plan_sha256: str, ordinal: int,
                    previous_digest: str, state: str) -> str:
    required = {"schema", "ordinal", "plan_sha256", "previous_event_sha256", "from_state", "to_state",
                "event", "evidence", "timestamp_utc", "authority_domain",
                "test_only_no_run", "event_sha256"}
    if set(event) != required or event.get("schema") != EVENT_SCHEMA or event.get("ordinal") != ordinal:
        raise ValueError("event schema/ordinal is invalid")
    if event["plan_sha256"] != plan_sha256 or event["previous_event_sha256"] != previous_digest:
        raise ValueError("event chain binding is invalid")
    if event["from_state"] != state or not isinstance(event["event"], str) or not event["event"]:
        raise ValueError("event state or label is invalid")
    if event["authority_domain"] != AUTHORITY_DOMAIN or event["test_only_no_run"] is not True:
        raise ValueError("event is not in the test-only/no-run authority domain")
    evidence = event["evidence"]
    if (type(evidence) is not dict
            or set(evidence) != {
                "schema", "evidence_id", "sha256", "digest_only",
                "scientific_evidence_validated",
            }
            or evidence.get("schema") != EVIDENCE_SCHEMA
            or evidence.get("digest_only") is not True
            or evidence.get("scientific_evidence_validated") is not False):
        raise ValueError("event evidence schema is invalid")
    EvidenceReference(evidence["evidence_id"], evidence["sha256"])
    try:
        parsed_time = datetime.strptime(event["timestamp_utc"], "%Y-%m-%dT%H:%M:%S.%fZ")
    except (TypeError, ValueError) as error:
        raise ValueError("event timestamp must be UTC RFC3339 microseconds") from error
    if parsed_time.tzinfo is not None:
        raise ValueError("event timestamp is invalid")
    if not _transition_allowed(state, event["to_state"]):
        raise ValueError("event transition is not allowed")
    expected_label = _event_label(event["to_state"])
    if event["event"] != expected_label:
        raise ValueError("event label is not the canonical transition label")
    body = {key: value for key, value in event.items() if key != "event_sha256"}
    if not _is_sha256(event["event_sha256"]) or _sha256_json(body) != event["event_sha256"]:
        raise ValueError("event digest is invalid")
    return event["event_sha256"]


def _transition_allowed(from_state: str, to_state: str) -> bool:
    if from_state not in _STATE_INDEX or to_state not in _STATE_INDEX and to_state not in TERMINAL_STATES:
        return False
    if from_state == "FINALIZED":
        return False
    if to_state in TERMINAL_STATES:
        return True
    return _STATE_INDEX[to_state] == _STATE_INDEX[from_state] + 1


def _event_label(to_state: str) -> str:
    return "RECORDED_%s" % to_state


def validate_transition_for_testing(from_state: str, to_state: str) -> str:
    """Pure graph check exposed only for no-execution tests and future binders."""
    if not _transition_allowed(from_state, to_state):
        raise ValueError("transition from %s to %s is forbidden" % (from_state, to_state))
    return _event_label(to_state)


def _load_execution_order_snapshot_locked(directory: Path) -> ExecutionOrderSnapshot:
    """Validate a snapshot while the caller holds the campaign lock."""
    if directory.name != ARTIFACT_DIRECTORY_NAME or directory.parent.name != "artifacts":
        raise ValueError("ledger is not in the canonical artifact directory")
    workspace_root = directory.parent.parent.resolve(strict=True)
    expected_source_paths = _discover_source_paths(workspace_root)
    plan = _read_json_bounded(directory / PLAN_FILE_NAME, MAXIMUM_PLAN_BYTES)
    _validate_plan(plan, expected_source_paths)
    if plan["artifact_identity"] != _artifact_identity(workspace_root):
        raise ValueError("plan artifact-path identity does not match the canonical directory")
    current_identities = [
        asdict(source_path_identity(workspace_root, path))
        for path in expected_source_paths
    ]
    if current_identities != plan["source_paths"]:
        raise ValueError("plan source identities are stale or do not match the current workspace")
    events_directory = directory / EVENT_DIRECTORY_NAME
    try:
        events_status = events_directory.lstat()
    except FileNotFoundError:
        paths = []
    else:
        if not stat.S_ISDIR(events_status.st_mode):
            raise ValueError("event ledger path is not a directory")
        paths = sorted(events_directory.iterdir(), key=lambda item: item.name)
    if len(paths) > len(ORDERED_STATES) + 1:
        raise ValueError("event ledger exceeds the bounded transition graph")
    state, previous = "NEW", GENESIS_EVENT_SHA256
    for ordinal, path in enumerate(paths, 1):
        if path.name != "%012d.json" % ordinal:
            raise ValueError("event ledger ordinals are not contiguous")
        event = _read_json_bounded(path, MAXIMUM_EVENT_BYTES)
        previous = _validate_event(event, plan["plan_sha256"], ordinal, previous, state)
        state = event["to_state"]
    return ExecutionOrderSnapshot(_SNAPSHOT_CONSTRUCTION_KEY, directory, plan, state, previous, len(paths))


def load_execution_order_snapshot(artifact_directory: os.PathLike) -> ExecutionOrderSnapshot:
    """Lock, recover exact pending entries, and load canonical custody."""
    directory = Path(artifact_directory).resolve(strict=True)
    with _locked_artifact_directory(directory):
        return _load_execution_order_snapshot_locked(directory)


def _authorization_paths(directory: Path, phase: str) -> Tuple[Path, Path]:
    if phase not in AUTHORIZATION_STATES:
        raise PermissionError("phase is not one of the six authorization states")
    stem = phase.lower()
    authorization_directory = directory / AUTHORIZATION_DIRECTORY_NAME
    return (
        authorization_directory / (stem + ".issued.json"),
        authorization_directory / (stem + ".consumed.json"),
    )


def _validate_authorization_record(record: Mapping[str, Any]) -> None:
    required = {
        "schema", "phase", "plan_sha256", "campaign_instance_nonce_sha256",
        "artifact_identity_sha256", "head_event_sha256", "authorization_nonce_sha256",
        "issued_timestamp_utc", "authority_domain", "test_only_no_run",
        "production_execution_authorized",
        "scientific_evidence_validated", "authorization_sha256",
    }
    if set(record) != required or record.get("schema") != AUTHORIZATION_SCHEMA:
        raise ValueError("authorization record schema is invalid")
    if record["phase"] not in AUTHORIZATION_STATES:
        raise ValueError("authorization record phase is not allowed")
    for name in (
        "plan_sha256", "campaign_instance_nonce_sha256", "artifact_identity_sha256",
        "head_event_sha256", "authorization_nonce_sha256",
    ):
        if not _is_sha256(record[name]):
            raise ValueError("authorization %s is invalid" % name)
    try:
        datetime.strptime(record["issued_timestamp_utc"], "%Y-%m-%dT%H:%M:%S.%fZ")
    except (TypeError, ValueError) as error:
        raise ValueError("authorization timestamp is invalid") from error
    if (record["authority_domain"] != AUTHORITY_DOMAIN
            or record["test_only_no_run"] is not True
            or record["production_execution_authorized"] is not False
            or record["scientific_evidence_validated"] is not False):
        raise ValueError("foundation authorization may not claim execution or evidence authority")
    body = {key: value for key, value in record.items() if key != "authorization_sha256"}
    if not _is_sha256(record["authorization_sha256"]) or _sha256_json(body) != record["authorization_sha256"]:
        raise ValueError("authorization record digest is invalid")


def _load_authorization_locked(directory: Path, phase: str) -> PhaseAuthorizationReceipt:
    issued_path, _ = _authorization_paths(directory, phase)
    record = _read_json_bounded(issued_path, MAXIMUM_AUTHORIZATION_BYTES)
    _validate_authorization_record(record)
    return PhaseAuthorizationReceipt(
        _AUTHORIZATION_CONSTRUCTION_KEY, directory, record
    )


def _assert_authorization_locked(receipt: PhaseAuthorizationReceipt, phase: str,
                                 snapshot: ExecutionOrderSnapshot) -> None:
    if type(receipt) is not PhaseAuthorizationReceipt:
        raise TypeError("receipt must be a loader-created PhaseAuthorizationReceipt")
    if phase not in AUTHORIZATION_STATES or receipt.phase != phase:
        raise PermissionError("authorization receipt is for a different or forbidden phase")
    current = _load_authorization_locked(snapshot.artifact_directory, phase)
    _, consumed_path = _authorization_paths(snapshot.artifact_directory, phase)
    if consumed_path.exists():
        raise PermissionError("authorization receipt has already been consumed")
    plan = snapshot.plan
    if (snapshot.state != phase
            or current.receipt_sha256 != receipt.receipt_sha256
            or current.record != receipt.record
            or receipt.plan_sha256 != snapshot.plan_sha256
            or receipt.head_event_sha256 != snapshot.head_event_sha256
            or receipt.record["campaign_instance_nonce_sha256"]
            != plan["campaign_instance_nonce_sha256"]
            or receipt.record["artifact_identity_sha256"]
            != plan["artifact_identity"]["identity_sha256"]):
        raise PermissionError("authorization receipt is stale or has mismatched custody")


def issue_phase_authorization(artifact_directory: os.PathLike,
                              phase: str) -> PhaseAuthorizationReceipt:
    """Issue one foundation-only receipt after a locked canonical reload."""
    directory = Path(artifact_directory).resolve(strict=True)
    with _locked_artifact_directory(directory):
        snapshot = _load_execution_order_snapshot_locked(directory)
        if phase not in AUTHORIZATION_STATES or snapshot.state != phase:
            raise PermissionError("only the current allowlisted authorization state may issue")
        issued_path, consumed_path = _authorization_paths(directory, phase)
        if issued_path.exists() or consumed_path.exists():
            raise FileExistsError("phase authorization custody already exists")
        body = {
            "schema": AUTHORIZATION_SCHEMA,
            "phase": phase,
            "plan_sha256": snapshot.plan_sha256,
            "campaign_instance_nonce_sha256": snapshot.plan["campaign_instance_nonce_sha256"],
            "artifact_identity_sha256": snapshot.plan["artifact_identity"]["identity_sha256"],
            "head_event_sha256": snapshot.head_event_sha256,
            "authorization_nonce_sha256": hashlib.sha256(secrets.token_bytes(32)).hexdigest(),
            "issued_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "authority_domain": AUTHORITY_DOMAIN,
            "test_only_no_run": True,
            "production_execution_authorized": False,
            "scientific_evidence_validated": False,
        }
        record = dict(body)
        record["authorization_sha256"] = _sha256_json(body)
        _atomic_exclusive_json(issued_path, record)
        loaded = _load_authorization_locked(directory, phase)
        _assert_authorization_locked(loaded, phase, snapshot)
        return loaded


def load_phase_authorization_receipt(artifact_directory: os.PathLike,
                                     phase: str) -> PhaseAuthorizationReceipt:
    """Reload an unconsumed receipt under the campaign lock."""
    directory = Path(artifact_directory).resolve(strict=True)
    with _locked_artifact_directory(directory):
        snapshot = _load_execution_order_snapshot_locked(directory)
        receipt = _load_authorization_locked(directory, phase)
        _assert_authorization_locked(receipt, phase, snapshot)
        return receipt


def assert_phase_authorization(receipt: PhaseAuthorizationReceipt,
                               phase: str) -> None:
    """Revalidate a receipt against current source and ledger custody."""
    if type(receipt) is not PhaseAuthorizationReceipt:
        raise TypeError("receipt must be loader-created")
    directory = receipt.artifact_directory.resolve(strict=True)
    with _locked_artifact_directory(directory):
        snapshot = _load_execution_order_snapshot_locked(directory)
        _assert_authorization_locked(receipt, phase, snapshot)


def _validate_consumer_id(value: object) -> str:
    if type(value) is not str or not value or len(value) > 256 or "\x00" in value:
        raise ValueError("consumer_id must be a nonempty bounded string without NUL")
    return value


def _validate_consumption_record(record: Mapping[str, Any]) -> None:
    required = {
        "schema", "phase", "authorization_sha256", "plan_sha256",
        "campaign_instance_nonce_sha256", "artifact_identity_sha256",
        "head_event_sha256", "consumer_id", "consumed_timestamp_utc",
        "authority_domain", "test_only_no_run",
        "production_execution_permit_issued", "scientific_evidence_validated",
        "consumption_sha256",
    }
    if set(record) != required or record.get("schema") != AUTHORIZATION_CONSUMPTION_SCHEMA:
        raise ValueError("authorization-consumption record schema is invalid")
    if record["phase"] not in AUTHORIZATION_STATES:
        raise ValueError("authorization-consumption phase is invalid")
    for name in (
        "authorization_sha256", "plan_sha256", "campaign_instance_nonce_sha256",
        "artifact_identity_sha256", "head_event_sha256",
    ):
        if not _is_sha256(record[name]):
            raise ValueError("authorization-consumption %s is invalid" % name)
    _validate_consumer_id(record["consumer_id"])
    try:
        datetime.strptime(record["consumed_timestamp_utc"], "%Y-%m-%dT%H:%M:%S.%fZ")
    except (TypeError, ValueError) as error:
        raise ValueError("authorization-consumption timestamp is invalid") from error
    if (record["authority_domain"] != AUTHORITY_DOMAIN
            or record["test_only_no_run"] is not True
            or record["production_execution_permit_issued"] is not False
            or record["scientific_evidence_validated"] is not False):
        raise ValueError("foundation consumption may not claim execution or evidence authority")
    body = {key: value for key, value in record.items() if key != "consumption_sha256"}
    if not _is_sha256(record["consumption_sha256"]) or _sha256_json(body) != record["consumption_sha256"]:
        raise ValueError("authorization-consumption digest is invalid")


def consume_phase_authorization(
    receipt: PhaseAuthorizationReceipt, phase: str, consumer_id: str
) -> PhaseAuthorizationConsumptionReceipt:
    """Atomically consume one receipt without changing the main phase state."""
    if type(receipt) is not PhaseAuthorizationReceipt:
        raise TypeError("receipt must be loader-created")
    consumer = _validate_consumer_id(consumer_id)
    directory = receipt.artifact_directory.resolve(strict=True)
    with _locked_artifact_directory(directory):
        snapshot = _load_execution_order_snapshot_locked(directory)
        _assert_authorization_locked(receipt, phase, snapshot)
        _, consumed_path = _authorization_paths(directory, phase)
        body = {
            "schema": AUTHORIZATION_CONSUMPTION_SCHEMA,
            "phase": phase,
            "authorization_sha256": receipt.receipt_sha256,
            "plan_sha256": snapshot.plan_sha256,
            "campaign_instance_nonce_sha256": snapshot.plan["campaign_instance_nonce_sha256"],
            "artifact_identity_sha256": snapshot.plan["artifact_identity"]["identity_sha256"],
            "head_event_sha256": snapshot.head_event_sha256,
            "consumer_id": consumer,
            "consumed_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "authority_domain": AUTHORITY_DOMAIN,
            "test_only_no_run": True,
            "production_execution_permit_issued": False,
            "scientific_evidence_validated": False,
        }
        record = dict(body)
        record["consumption_sha256"] = _sha256_json(body)
        _atomic_exclusive_json(consumed_path, record)
        loaded = _read_json_bounded(consumed_path, MAXIMUM_AUTHORIZATION_BYTES)
        _validate_consumption_record(loaded)
        return PhaseAuthorizationConsumptionReceipt(
            _CONSUMPTION_CONSTRUCTION_KEY, directory, loaded
        )


def append_transition_for_testing(artifact_directory: os.PathLike, to_state: str,
                                  evidence: EvidenceReference) -> ExecutionOrderSnapshot:
    """Append test-only state emulation; never validate evidence or mint a permit.

    A returned snapshot, including one whose test state reads ``FINALIZED``, is
    only a loader view.  It is not a production or scientific-result wrapper.
    """
    directory = Path(artifact_directory).resolve(strict=True)
    with _locked_artifact_directory(directory):
        snapshot = _load_execution_order_snapshot_locked(directory)
        label = validate_transition_for_testing(snapshot.state, to_state)
        ordinal = snapshot.event_count + 1
        body = {"schema": EVENT_SCHEMA, "ordinal": ordinal, "plan_sha256": snapshot.plan_sha256,
                "previous_event_sha256": snapshot.head_event_sha256, "from_state": snapshot.state,
                "to_state": to_state, "event": label, "evidence": evidence.as_record(),
                "authority_domain": AUTHORITY_DOMAIN, "test_only_no_run": True,
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
        record = dict(body)
        record["event_sha256"] = _sha256_json(body)
        _atomic_exclusive_json(_event_path(directory, ordinal), record)
        return _load_execution_order_snapshot_locked(directory)


def _status_payload(snapshot: ExecutionOrderSnapshot) -> Dict[str, Any]:
    return {"schema": "heterodiff-a1-finite-association-test-only-no-run-status-v2",
            "artifact_directory": str(snapshot.artifact_directory), "plan_sha256": snapshot.plan_sha256,
            "state": snapshot.state, "head_event_sha256": snapshot.head_event_sha256,
            "event_count": snapshot.event_count,
            "authority_domain": AUTHORITY_DOMAIN,
            "test_only_no_run": True,
            "runner_integration_complete": False,
            "scientific_evidence_validated": False,
            "coordinate_counts": {"exact": 24, "primary": 48, "controls": 72, "complete_sampled": 120}}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Finite A1 execution-order ledger (no runner execution).")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init-plan", help="write the canonical immutable plan")
    init.add_argument("--workspace-root", default=".")
    status = commands.add_parser("status", help="read and validate ledger status")
    status.add_argument("--workspace-root", default=".")
    arguments = parser.parse_args(argv)
    if arguments.command == "init-plan":
        snapshot = initialize_execution_order_plan(arguments.workspace_root)
    else:
        snapshot = load_execution_order_snapshot(canonical_artifact_directory(arguments.workspace_root))
    print(_canonical_json(_status_payload(snapshot)).decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
