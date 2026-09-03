"""Deterministic, fail-closed provenance manifests for experiments.

The module deliberately captures only an explicit command, an explicit seed,
declared package versions, and content checksums. It never snapshots the
process environment, current working directory, clock, username, or hostname.
Those values are either secret-bearing or make otherwise identical manifests
depend on incidental execution context.

All public records are frozen and contain only immutable scalar values or
tuples. Configurations are stored as canonical JSON text rather than retaining
a caller-owned mutable mapping.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import re
import stat
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from importlib import metadata as importlib_metadata
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union


PathLike = Union[str, os.PathLike]

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DISTRIBUTION_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
_UTC_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
_DIRECTORY_DOMAIN = b"heterodiff-directory-sha256-v1\0"
_MAX_SAFE_JSON_INTEGER = 2**53 - 1


def _stat_signature(status: os.stat_result) -> Tuple[int, int, int, int, int, int]:
    """Fields that must remain stable while content is checksummed."""

    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _normalized_text(value: object, *, field_name: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    normalized = unicodedata.normalize("NFC", value)
    try:
        normalized.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise ValueError(f"{field_name} must contain valid Unicode") from error
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _validate_sha256(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase 64-character SHA-256 digest")
    return value


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 digest of an immutable byte string."""

    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    return hashlib.sha256(data).hexdigest()


def _hash_file_with_size(
    path: PathLike,
) -> Tuple[str, int, Tuple[int, int, int, int, int, int]]:
    candidate = Path(path)
    try:
        before = candidate.lstat()
    except FileNotFoundError as error:
        raise FileNotFoundError(f"checksum target does not exist: {candidate}") from error
    if stat.S_ISLNK(before.st_mode):
        raise ValueError(f"checksum target must not be a symlink: {candidate}")
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"checksum target must be a regular file: {candidate}")

    digest = hashlib.sha256()
    byte_count = 0
    with candidate.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError(f"checksum target must be a regular file: {candidate}")
        if _stat_signature(opened) != _stat_signature(before):
            raise RuntimeError(f"checksum target changed while opening: {candidate}")
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            byte_count += len(chunk)
        after = os.fstat(handle.fileno())

    if _stat_signature(before) != _stat_signature(after) or byte_count != after.st_size:
        raise RuntimeError(f"checksum target changed while reading: {candidate}")
    try:
        path_after = candidate.lstat()
    except FileNotFoundError as error:
        raise RuntimeError(f"checksum target disappeared after reading: {candidate}") from error
    if _stat_signature(path_after) != _stat_signature(after):
        raise RuntimeError(f"checksum target changed after reading: {candidate}")
    return digest.hexdigest(), byte_count, _stat_signature(path_after)


def sha256_file(path: PathLike) -> str:
    """Hash one regular file, rejecting missing paths, links, and read races."""

    return _hash_file_with_size(path)[0]


def _logical_path(value: object, *, field_name: str = "path") -> str:
    normalized = _normalized_text(value, field_name=field_name)
    if "\\" in normalized:
        raise ValueError(f"{field_name} must use POSIX '/' separators")
    if normalized.startswith("/"):
        raise ValueError(f"{field_name} must be relative")
    raw_parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError(f"{field_name} must not contain empty, '.' or '..' components")
    parsed = PurePosixPath(normalized)
    if parsed.is_absolute() or str(parsed) != normalized:
        raise ValueError(f"{field_name} is not a canonical relative POSIX path")
    return normalized


def _walk_regular_files(root: Path) -> List[Tuple[str, Path]]:
    """Return normalized relative paths while rejecting links and special files."""

    found: List[Tuple[str, Path]] = []
    seen_portable: Dict[str, str] = {}

    def visit(directory: Path, relative_parts: Tuple[str, ...]) -> None:
        try:
            entries = list(os.scandir(directory))
        except FileNotFoundError as error:
            raise RuntimeError(f"directory changed while checksumming: {directory}") from error
        for entry in entries:
            component = _normalized_text(entry.name, field_name="directory entry")
            relative = _logical_path("/".join(relative_parts + (component,)))
            portable_key = relative.casefold()
            previous = seen_portable.get(portable_key)
            if previous is not None:
                raise ValueError(
                    "directory contains paths that collide under Unicode/case normalization: "
                    f"{previous!r} and {relative!r}"
                )
            seen_portable[portable_key] = relative
            if entry.is_symlink():
                raise ValueError(f"directory tree must not contain symlinks: {entry.path}")
            if entry.is_dir(follow_symlinks=False):
                visit(Path(entry.path), relative_parts + (component,))
            elif entry.is_file(follow_symlinks=False):
                found.append((relative, Path(entry.path)))
            else:
                raise ValueError(f"directory tree contains a non-regular entry: {entry.path}")

    visit(root, ())
    found.sort(key=lambda item: item[0])
    return found


def sha256_directory(path: PathLike) -> str:
    """Hash a sorted regular-file tree independently of its absolute root path.

    The tree digest commits to every normalized relative path, byte count, and
    file-content digest. Empty directories do not affect the result. Symlinks,
    sockets, devices, and case/Unicode-colliding paths are rejected.
    """

    root = Path(path)
    try:
        root_status = root.lstat()
    except FileNotFoundError as error:
        raise FileNotFoundError(f"directory checksum target does not exist: {root}") from error
    if stat.S_ISLNK(root_status.st_mode):
        raise ValueError(f"directory checksum target must not be a symlink: {root}")
    if not stat.S_ISDIR(root_status.st_mode):
        raise ValueError(f"directory checksum target must be a directory: {root}")

    initial_files = _walk_regular_files(root)
    records: List[Dict[str, Any]] = []
    file_signatures: Dict[str, Tuple[int, int, int, int, int, int]] = {}
    for relative, file_path in initial_files:
        digest, byte_count, signature = _hash_file_with_size(file_path)
        file_signatures[relative] = signature
        records.append(
            {"path": relative, "sha256": digest, "size_bytes": byte_count}
        )
    final_files = _walk_regular_files(root)
    if [item[0] for item in final_files] != [item[0] for item in initial_files]:
        raise RuntimeError(f"directory changed while checksumming: {root}")
    for relative, file_path in final_files:
        try:
            final_status = file_path.lstat()
        except FileNotFoundError as error:
            raise RuntimeError(
                f"directory changed while checksumming: {root}"
            ) from error
        if _stat_signature(final_status) != file_signatures[relative]:
            raise RuntimeError(f"directory changed while checksumming: {root}")
    try:
        final_root_status = root.lstat()
    except FileNotFoundError as error:
        raise RuntimeError(f"directory changed while checksumming: {root}") from error
    if _stat_signature(final_root_status) != _stat_signature(root_status):
        raise RuntimeError(f"directory changed while checksumming: {root}")
    payload = canonical_json_dumps(records).encode("utf-8")
    return sha256_bytes(_DIRECTORY_DOMAIN + payload)


def _canonicalize_json(value: object, active_ids: Set[int], location: str) -> Any:
    if value is None or isinstance(value, (str, bool)):
        if isinstance(value, str):
            return _normalized_text(value, field_name=location, allow_empty=True)
        return value
    if isinstance(value, int):
        if abs(value) > _MAX_SAFE_JSON_INTEGER:
            raise ValueError(
                f"{location} contains an integer outside the interoperable JSON range "
                f"[-{_MAX_SAFE_JSON_INTEGER}, {_MAX_SAFE_JSON_INTEGER}]"
            )
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{location} contains a non-finite float")
        return 0.0 if value == 0.0 else value

    container_id = id(value)
    if isinstance(value, Mapping):
        if container_id in active_ids:
            raise ValueError(f"{location} contains a reference cycle")
        active_ids.add(container_id)
        try:
            result: Dict[str, Any] = {}
            for raw_key, item in value.items():
                key = _normalized_text(raw_key, field_name=f"{location} key", allow_empty=True)
                if key in result:
                    raise ValueError(f"{location} contains duplicate key {key!r}")
                result[key] = _canonicalize_json(item, active_ids, f"{location}.{key}")
            return result
        finally:
            active_ids.remove(container_id)

    if isinstance(value, (list, tuple)):
        if container_id in active_ids:
            raise ValueError(f"{location} contains a reference cycle")
        active_ids.add(container_id)
        try:
            return [
                _canonicalize_json(item, active_ids, f"{location}[{index}]")
                for index, item in enumerate(value)
            ]
        finally:
            active_ids.remove(container_id)

    raise TypeError(
        f"{location} has unsupported type {type(value).__name__}; "
        "use only JSON scalars, mappings with string keys, lists, and tuples"
    )


def canonical_json_dumps(value: object) -> str:
    """Serialize a strictly validated JSON value in one canonical form."""

    normalized = _canonicalize_json(value, set(), "$")
    return json.dumps(
        normalized,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_config_json(config: Mapping) -> str:
    """Return canonical JSON for a configuration mapping."""

    if not isinstance(config, Mapping):
        raise TypeError("config must be a mapping")
    return canonical_json_dumps(config)


def canonical_config_digest(config: Mapping) -> str:
    """Hash the UTF-8 bytes of canonical_config_json."""

    return sha256_bytes(canonical_config_json(config).encode("utf-8"))


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant is not allowed: {value}")


def _strict_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"JSON contains duplicate key {key!r}")
        result[key] = value
    return result


def _strict_json_loads(value: str) -> Any:
    try:
        return json.loads(
            value,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as error:
        raise ValueError("invalid JSON") from error


@dataclass(frozen=True)
class CanonicalConfig:
    """Immutable canonical configuration text and its verified digest."""

    json: str
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.json, str):
            raise TypeError("config JSON must be a string")
        parsed = _strict_json_loads(self.json)
        if not isinstance(parsed, Mapping):
            raise ValueError("configuration JSON must contain a mapping at its root")
        canonical = canonical_config_json(parsed)
        if canonical != self.json:
            raise ValueError("configuration JSON is not canonical")
        digest = _validate_sha256(self.sha256, field_name="config sha256")
        if digest != sha256_bytes(self.json.encode("utf-8")):
            raise ValueError("configuration digest does not match its canonical JSON")

    @classmethod
    def from_mapping(cls, config: Mapping) -> "CanonicalConfig":
        canonical = canonical_config_json(config)
        return cls(json=canonical, sha256=sha256_bytes(canonical.encode("utf-8")))

    def value(self) -> Dict[str, Any]:
        """Return a fresh mutable JSON object; the stored record stays immutable."""

        loaded = _strict_json_loads(self.json)
        if not isinstance(loaded, dict):
            raise RuntimeError("stored canonical configuration is not a mapping")
        return loaded


@dataclass(frozen=True)
class ArtifactChecksum:
    """Content checksum under a portable, experiment-relative logical path."""

    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _logical_path(self.path, field_name="artifact path"))
        _validate_sha256(self.sha256, field_name="artifact sha256")
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int):
            raise TypeError("artifact size_bytes must be an integer")
        if self.size_bytes < 0:
            raise ValueError("artifact size_bytes must be non-negative")
        if self.size_bytes > _MAX_SAFE_JSON_INTEGER:
            raise ValueError(
                "artifact size_bytes exceeds the interoperable JSON integer range"
            )

    @classmethod
    def from_file(
        cls, path: PathLike, *, logical_path: Optional[str] = None
    ) -> "ArtifactChecksum":
        candidate = Path(path)
        digest, byte_count, _ = _hash_file_with_size(candidate)
        logical = candidate.name if logical_path is None else logical_path
        return cls(path=logical, sha256=digest, size_bytes=byte_count)


@dataclass(frozen=True)
class DatasetProvenance:
    """Identity, split, and content digest of an input dataset."""

    name: str
    split: str
    sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _normalized_text(self.name, field_name="dataset name"))
        object.__setattr__(self, "split", _normalized_text(self.split, field_name="dataset split"))
        _validate_sha256(self.sha256, field_name="dataset sha256")

    @classmethod
    def from_file(cls, name: str, split: str, path: PathLike) -> "DatasetProvenance":
        return cls(name=name, split=split, sha256=sha256_file(path))

    @classmethod
    def from_directory(
        cls, name: str, split: str, path: PathLike
    ) -> "DatasetProvenance":
        return cls(name=name, split=split, sha256=sha256_directory(path))


def _distribution_name(value: object) -> str:
    name = _normalized_text(value, field_name="dependency name")
    if _DISTRIBUTION_RE.fullmatch(name) is None:
        raise ValueError(
            "dependency name must be a distribution name without a version specifier"
        )
    return re.sub(r"[-_.]+", "-", name).lower()


@dataclass(frozen=True)
class DependencyVersion:
    name: str
    version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _distribution_name(self.name))
        object.__setattr__(
            self,
            "version",
            _normalized_text(self.version, field_name=f"version for {self.name}"),
        )


@dataclass(frozen=True)
class RuntimeProvenance:
    """Non-secret runtime identity and installed declared-package versions."""

    python_version: str
    python_implementation: str
    system: str
    release: str
    machine: str
    dependencies: Tuple[DependencyVersion, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "python_version",
            "python_implementation",
            "system",
            "release",
            "machine",
        ):
            object.__setattr__(
                self,
                name,
                _normalized_text(getattr(self, name), field_name=name, allow_empty=True),
            )
        dependencies = tuple(self.dependencies)
        if not all(isinstance(item, DependencyVersion) for item in dependencies):
            raise TypeError("dependencies must contain DependencyVersion records")
        sorted_dependencies = tuple(sorted(dependencies, key=lambda item: item.name))
        names = [item.name for item in sorted_dependencies]
        if len(names) != len(set(names)):
            raise ValueError("declared dependencies contain duplicate normalized names")
        object.__setattr__(self, "dependencies", sorted_dependencies)

    @classmethod
    def capture(cls, declared_dependencies: Iterable[str]) -> "RuntimeProvenance":
        if isinstance(declared_dependencies, (str, bytes)):
            raise TypeError("declared_dependencies must be an iterable of distribution names")
        normalized_names: List[str] = []
        seen: Set[str] = set()
        for raw_name in declared_dependencies:
            name = _distribution_name(raw_name)
            if name in seen:
                raise ValueError(f"duplicate declared dependency: {name}")
            seen.add(name)
            normalized_names.append(name)
        versions: List[DependencyVersion] = []
        for name in sorted(normalized_names):
            try:
                version = importlib_metadata.version(name)
            except importlib_metadata.PackageNotFoundError as error:
                raise ValueError(f"declared dependency is not installed: {name}") from error
            versions.append(DependencyVersion(name=name, version=version))
        return cls(
            python_version=platform.python_version(),
            python_implementation=platform.python_implementation(),
            system=platform.system(),
            release=platform.release(),
            machine=platform.machine(),
            dependencies=tuple(versions),
        )


def _validate_explicit_timestamp(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = _normalized_text(value, field_name="created_at")
    if _UTC_TIMESTAMP_RE.fullmatch(normalized) is None:
        raise ValueError("created_at must be an explicit RFC 3339 UTC timestamp ending in 'Z'")
    try:
        datetime.fromisoformat(normalized[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError("created_at is not a valid calendar timestamp") from error
    return normalized


@dataclass(frozen=True)
class ExperimentManifest:
    """Complete deterministic record of one experiment invocation."""

    command: Tuple[str, ...]
    seed: int
    dataset: DatasetProvenance
    code_sha256: str
    config: CanonicalConfig
    runtime: RuntimeProvenance
    artifacts: Tuple[ArtifactChecksum, ...] = ()
    created_at: Optional[str] = None
    schema_version: int = field(default=1, init=False)

    def __post_init__(self) -> None:
        if isinstance(self.command, (str, bytes)):
            raise TypeError("command must be an iterable of argument strings")
        command = tuple(self.command)
        if not command:
            raise ValueError("command must contain at least an executable")
        normalized_command = tuple(
            _normalized_text(
                part,
                field_name=f"command[{index}]",
                allow_empty=index > 0,
            )
            for index, part in enumerate(command)
        )
        object.__setattr__(self, "command", normalized_command)
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise TypeError("seed must be an integer")
        if self.seed < 0:
            raise ValueError("seed must be non-negative")
        if self.seed > _MAX_SAFE_JSON_INTEGER:
            raise ValueError("seed exceeds the interoperable JSON integer range")
        if not isinstance(self.dataset, DatasetProvenance):
            raise TypeError("dataset must be a DatasetProvenance record")
        _validate_sha256(self.code_sha256, field_name="code sha256")
        if not isinstance(self.config, CanonicalConfig):
            raise TypeError("config must be a CanonicalConfig record")
        if not isinstance(self.runtime, RuntimeProvenance):
            raise TypeError("runtime must be a RuntimeProvenance record")

        artifacts = tuple(self.artifacts)
        if not all(isinstance(item, ArtifactChecksum) for item in artifacts):
            raise TypeError("artifacts must contain ArtifactChecksum records")
        artifacts = tuple(sorted(artifacts, key=lambda item: item.path))
        portable_paths: Dict[str, str] = {}
        for artifact in artifacts:
            portable_key = artifact.path.casefold()
            previous = portable_paths.get(portable_key)
            if previous is not None:
                raise ValueError(
                    "artifact paths must be unique under Unicode/case normalization: "
                    f"{previous!r} and {artifact.path!r}"
                )
            portable_paths[portable_key] = artifact.path
        object.__setattr__(self, "artifacts", artifacts)
        object.__setattr__(self, "created_at", _validate_explicit_timestamp(self.created_at))

    @classmethod
    def create(
        cls,
        *,
        command: Iterable[str],
        seed: int,
        dataset: DatasetProvenance,
        code_sha256: str,
        config: Mapping,
        artifacts: Iterable[ArtifactChecksum] = (),
        declared_dependencies: Iterable[str] = (),
        created_at: Optional[str] = None,
    ) -> "ExperimentManifest":
        """Build a manifest, querying only installed declared-package metadata."""

        return cls(
            command=tuple(command),
            seed=seed,
            dataset=dataset,
            code_sha256=code_sha256,
            config=CanonicalConfig.from_mapping(config),
            runtime=RuntimeProvenance.capture(declared_dependencies),
            artifacts=tuple(artifacts),
            created_at=created_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "command": list(self.command),
            "seed": self.seed,
            "dataset": {
                "name": self.dataset.name,
                "split": self.dataset.split,
                "sha256": self.dataset.sha256,
            },
            "code": {"sha256": self.code_sha256},
            "config": {
                "value": self.config.value(),
                "sha256": self.config.sha256,
            },
            "runtime": {
                "python_version": self.runtime.python_version,
                "python_implementation": self.runtime.python_implementation,
                "system": self.runtime.system,
                "release": self.runtime.release,
                "machine": self.runtime.machine,
                "dependencies": [
                    {"name": item.name, "version": item.version}
                    for item in self.runtime.dependencies
                ],
            },
            "artifacts": [
                {
                    "path": item.path,
                    "sha256": item.sha256,
                    "size_bytes": item.size_bytes,
                }
                for item in self.artifacts
            ],
        }
        if self.created_at is not None:
            result["created_at"] = self.created_at
        return result

    def to_json(self) -> str:
        """Return deterministic canonical JSON without an implicit timestamp."""

        return canonical_json_dumps(self.to_dict())

    @property
    def digest(self) -> str:
        """SHA-256 of exactly the canonical UTF-8 manifest JSON."""

        return sha256_bytes(self.to_json().encode("utf-8"))
