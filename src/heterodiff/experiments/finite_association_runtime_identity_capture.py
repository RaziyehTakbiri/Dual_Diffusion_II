"""Deterministic, non-authorizing capture of the A1 target runtime identity.

The public boundary launches the fixed ``.venv-m1`` interpreter in a fresh
``-P -B -S`` process.  The child inventories wheel bytes before exposing the
site-packages directory, then imports exactly the four numerical runtime
packages needed to observe module origins, native thread pools, and accelerator
capabilities.  It never invokes a prerequisite, learner, optimizer, or campaign
entry point.

Every candidate emitted here has ``approved: false``.  Capture and review are
content-addressed evidence only; this module deliberately contains no approval
or compare-and-swap operation.
"""

from __future__ import annotations

from dataclasses import dataclass
import base64
import binascii
import csv
import hashlib
import importlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import selectors
import signal
import stat
import subprocess
import sys
import sysconfig
import time
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple
from urllib.parse import unquote, urlsplit


# A direct ``-S`` worker cannot import the editable project until its source is
# verified.  Reserve that bootstrap solely for the supervisor's exact child
# command.  A direct, site-enabled operator invocation is the supervisor and
# must import the canonical identity and approval modules normally.
def _is_direct_capture_child_invocation(arguments: Sequence[str]) -> bool:
    return len(arguments) == 3 and arguments[1] == "--capture-child"


_DIRECT_CAPTURE_CHILD_BOOTSTRAP = (
    __name__ == "__main__"
    and (__package__ is None or __package__ == "")
    and _is_direct_capture_child_invocation(sys.argv)
)

if _DIRECT_CAPTURE_CHILD_BOOTSTRAP:
    runtime_identity = None
    runtime_approval = None
else:
    from heterodiff.experiments import (
        finite_association_runtime_identity as runtime_identity,
        finite_association_runtime_identity_approval as runtime_approval,
    )


CAPTURE_REQUEST_SCHEMA = "heterodiff-a1-runtime-identity-capture-request-v1"
CAPTURE_ENVELOPE_SCHEMA = "heterodiff-a1-runtime-identity-capture-envelope-v1"
CAPTURE_ASSESSMENT_SCHEMA = "heterodiff-a1-runtime-identity-capture-assessment-v1"
TARGET_PROFILE_ID = "m1-reference-macos-arm64-py311"
CAPTURE_OPERATION = "CAPTURE_RUNTIME_IDENTITY_CANDIDATE_V1"

CAPTURE_SOURCE_RELATIVE_PATH = (
    "src/heterodiff/experiments/finite_association_runtime_identity_capture.py"
)
IDENTITY_SOURCE_RELATIVE_PATH = (
    "src/heterodiff/experiments/finite_association_runtime_identity.py"
)
FIXED_VENV_PYTHON_RELATIVE_PATH = ".venv-m1/bin/python"
FIXED_VENV_ROOT_RELATIVE_PATH = ".venv-m1"
FIXED_SITE_PACKAGES_RELATIVE_PATH = (
    ".venv-m1/lib/python3.11/site-packages"
)
CANDIDATE_ROOT_RELATIVE_PATH = (
    "requirements/runtime-identity-candidates/" + TARGET_PROFILE_ID
)
CANDIDATE_FILE_NAME = "candidate.json"

MAXIMUM_CAPTURE_REQUEST_BYTES = 64 * 1024
MAXIMUM_CAPTURE_ENVELOPE_BYTES = 32 * 1024 * 1024
MAXIMUM_METADATA_BYTES = 64 * 1024 * 1024
MAXIMUM_CAPTURE_FILE_BYTES = 8 * 1024 * 1024 * 1024
CAPTURE_TIMEOUT_SECONDS = 1200.0
MINIMUM_MACOS_VERSION = "14.0"

_THREAD_ENVIRONMENT = {
    "BLIS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
}
_STARTUP_ENVIRONMENT = {
    "CUDA_VISIBLE_DEVICES": "",
    "LANG": "C",
    "LC_ALL": "C",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONPYCACHEPREFIX": "/dev/null",
    "PYTHONSAFEPATH": "1",
    "PYTHONUTF8": "1",
    "TZ": "UTC",
}
SANITIZED_CAPTURE_ENVIRONMENT = dict(
    sorted({**_THREAD_ENVIRONMENT, **_STARTUP_ENVIRONMENT}.items())
)
_DARWIN_INJECTED_ENVIRONMENT_NAME = "__CF_USER_TEXT_ENCODING"

_DYNAMIC_MODULE_NAMES = ("numpy", "scipy", "threadpoolctl", "torch")
_TORCH_GENERATED_MODULE_NAME = "_remote_module_non_scriptable"
_TORCH_GENERATED_MODULE_ORIGIN = "torch-git"
_TORCH_GENERATED_LOADER_MODULE = "torch.distributed.nn.jit.instantiator"
_TORCH_GENERATED_LOADER_QUALNAME = "_StringLoader"
_TORCH_GENERATED_SOURCE_SIZE_BYTES = 2355
_TORCH_GENERATED_SOURCE_SHA256 = (
    "8205b16956fb264841ecd8644784a0d157f87df79b17c16825dc1163433ce5d8"
)
_TORCH_MODULE_ALIASES = {
    "torch.classes": ("torch._classes", "_Classes", "_classes.py"),
    "torch.ops": ("torch._ops", "_Ops", "_ops.py"),
}
_REVIEW_COMPONENTS = (
    "profile",
    "lockfile",
    "python_files",
    "modules",
    "distributions",
    "editable_install",
    "native_libraries",
    "native_pools",
    "accelerators",
)
_HEX_DIGITS = frozenset("0123456789abcdef")


class RuntimeIdentityCaptureError(RuntimeError):
    """A fail-closed capture error carrying a stable machine code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RuntimeIdentityCaptureResult:
    """Validated child result; it carries no execution authority."""

    candidate: Mapping[str, object]
    capture_protocol: Mapping[str, object]
    assessment: Mapping[str, object]


@dataclass(frozen=True)
class RuntimeIdentityCapturePublication:
    """Paths and canonical records published by one idempotent capture."""

    candidate_path: Path
    report_path: Path
    candidate: Mapping[str, object]
    report: Mapping[str, object]
    assessment: Mapping[str, object]


def _plain_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain_json_value(item) for item in value]
    return value


def canonical_json_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(
            _plain_json_value(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ValueError("capture value is not finite canonical JSON") from error
    return encoded.encode("ascii")


def canonical_json_file_bytes(value: object) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_duplicate_pairs(pairs: Sequence[Tuple[str, object]]) -> dict:
    result: Dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("capture JSON contains duplicate keys")
        result[key] = value
    return result


def decode_canonical_json(
    payload: object, *, maximum_bytes: int, description: str
) -> Dict[str, Any]:
    if type(payload) is not bytes or not payload or len(payload) > maximum_bytes:
        raise ValueError(description + " has an invalid byte length")
    try:
        value = json.loads(
            payload.decode("ascii"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError("non-finite JSON constant " + token)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as error:
        raise ValueError(description + " is invalid JSON") from error
    if type(value) is not dict or payload != canonical_json_bytes(value):
        raise ValueError(description + " is not a canonical JSON object")
    return value


def _digest_record(body: Mapping[str, object], digest_name: str) -> Dict[str, Any]:
    record = dict(body)
    record[digest_name] = sha256_json(body)
    return record


def _validate_digest_record(
    value: object,
    *,
    fields: Iterable[str],
    digest_name: str,
    schema: str,
) -> Dict[str, Any]:
    expected = set(fields)
    expected.add(digest_name)
    if type(value) is not dict or set(value) != expected:
        raise ValueError("capture digest-record schema is invalid")
    if value.get("schema") != schema:
        raise ValueError("capture digest-record identifier is invalid")
    digest = value[digest_name]
    if (
        type(digest) is not str
        or len(digest) != 64
        or any(character not in _HEX_DIGITS for character in digest)
    ):
        raise ValueError("capture digest is invalid")
    body = dict(value)
    body.pop(digest_name)
    if digest != sha256_json(body):
        raise ValueError("capture digest differs from its body")
    return dict(value)


def _path_identity(metadata: os.stat_result) -> Tuple[int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _reject_symlink_ancestors(path: Path, *, name: str) -> None:
    absolute = Path(os.path.abspath(os.fspath(path)))
    current = absolute.parent
    while True:
        try:
            metadata = os.lstat(current)
        except FileNotFoundError as error:
            raise RuntimeIdentityCaptureError(
                "PATH_ABSENT", name + " ancestor is absent"
            ) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeIdentityCaptureError(
                "PATH_ANCESTOR_UNSAFE", name + " ancestor is not a real directory"
            )
        if current.parent == current:
            break
        current = current.parent


def _stream_file_identity(
    path: Path,
    *,
    name: str,
    maximum_bytes: int = MAXIMUM_CAPTURE_FILE_BYTES,
    allow_empty: bool = True,
) -> Dict[str, Any]:
    candidate = Path(path)
    if not candidate.is_absolute():
        raise RuntimeIdentityCaptureError("PATH_NOT_ABSOLUTE", name + " is not absolute")
    _reject_symlink_ancestors(candidate, name=name)
    try:
        before = os.lstat(candidate)
    except FileNotFoundError as error:
        raise RuntimeIdentityCaptureError("PATH_ABSENT", name + " is absent") from error
    if not stat.S_ISREG(before.st_mode):
        raise RuntimeIdentityCaptureError("PATH_NOT_REGULAR", name + " is not regular")
    if before.st_size > maximum_bytes or (not allow_empty and before.st_size == 0):
        raise RuntimeIdentityCaptureError("FILE_SIZE", name + " has an invalid size")
    descriptor = os.open(
        os.fspath(candidate), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    )
    digest = hashlib.sha256()
    consumed = 0
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or _path_identity(opened) != _path_identity(before):
            raise RuntimeIdentityCaptureError(
                "FILE_CHANGED", name + " changed while opening"
            )
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            consumed += len(block)
            if consumed > maximum_bytes:
                raise RuntimeIdentityCaptureError(
                    "FILE_SIZE", name + " exceeded its byte limit"
                )
            digest.update(block)
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after_path = os.lstat(candidate)
    except FileNotFoundError as error:
        raise RuntimeIdentityCaptureError(
            "FILE_CHANGED", name + " disappeared while reading"
        ) from error
    if (
        _path_identity(after_descriptor) != _path_identity(opened)
        or _path_identity(after_path) != _path_identity(opened)
        or consumed != opened.st_size
    ):
        raise RuntimeIdentityCaptureError("FILE_CHANGED", name + " changed while reading")
    return {
        "path": os.path.abspath(os.fspath(candidate)),
        "size_bytes": consumed,
        "sha256": digest.hexdigest(),
    }


def _read_regular_file(
    path: Path, *, name: str, maximum_bytes: int, allow_empty: bool = False
) -> bytes:
    identity = _stream_file_identity(
        path, name=name, maximum_bytes=maximum_bytes, allow_empty=allow_empty
    )
    descriptor = os.open(
        identity["path"], os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        payload = b""
        while len(payload) <= maximum_bytes:
            block = os.read(descriptor, min(1024 * 1024, maximum_bytes + 1 - len(payload)))
            if not block:
                break
            payload += block
    finally:
        os.close(descriptor)
    if len(payload) != identity["size_bytes"] or _sha256_bytes(payload) != identity["sha256"]:
        raise RuntimeIdentityCaptureError(
            "FILE_CHANGED", name + " changed between bounded reads"
        )
    return payload


def _normalized_distribution_name(value: object) -> str:
    if type(value) is not str or not value or len(value) > 256:
        raise RuntimeIdentityCaptureError(
            "DISTRIBUTION_METADATA", "distribution name is invalid"
        )
    normalized = re.sub(r"[-_.]+", "-", value).lower()
    if not normalized or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized) is None:
        raise RuntimeIdentityCaptureError(
            "DISTRIBUTION_METADATA", "distribution name is not canonicalizable"
        )
    return normalized


def _metadata_name_version(metadata_path: Path) -> Tuple[str, str]:
    payload = _read_regular_file(
        metadata_path,
        name="distribution METADATA",
        maximum_bytes=MAXIMUM_METADATA_BYTES,
    )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeIdentityCaptureError(
            "DISTRIBUTION_METADATA", "METADATA is not UTF-8"
        ) from error
    names = []
    versions = []
    for line in text.splitlines():
        if not line:
            break
        if line.startswith("Name:"):
            names.append(line[5:].strip())
        elif line.startswith("Version:"):
            versions.append(line[8:].strip())
    if len(names) != 1 or len(versions) != 1 or not names[0] or not versions[0]:
        raise RuntimeIdentityCaptureError(
            "DISTRIBUTION_METADATA", "METADATA lacks one exact Name and Version"
        )
    for value in (names[0], versions[0]):
        try:
            value.encode("ascii")
        except UnicodeEncodeError as error:
            raise RuntimeIdentityCaptureError(
                "DISTRIBUTION_METADATA", "distribution identity is not ASCII"
            ) from error
    return names[0], versions[0]


def _distribution_directories(site_packages: Path) -> Tuple[Tuple[Path, str, str], ...]:
    try:
        entries = sorted(site_packages.iterdir(), key=lambda path: path.name)
    except FileNotFoundError as error:
        raise RuntimeIdentityCaptureError(
            "SITE_PACKAGES_ABSENT", "fixed site-packages directory is absent"
        ) from error
    rows = []
    for entry in entries:
        if not (entry.name.endswith(".dist-info") or entry.name.endswith(".egg-info")):
            continue
        status = entry.lstat()
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise RuntimeIdentityCaptureError(
                "DISTRIBUTION_ORIGIN_UNSAFE", "distribution metadata origin is unsafe"
            )
        metadata_path = entry / "METADATA"
        if not metadata_path.exists() and entry.name.endswith(".egg-info"):
            metadata_path = entry / "PKG-INFO"
        name, version = _metadata_name_version(metadata_path)
        rows.append((entry, name, version))
    return tuple(rows)


def _record_path(value: object) -> str:
    if runtime_identity is not None and hasattr(runtime_identity, "_record_relative_path"):
        return runtime_identity._record_relative_path(value, name="wheel RECORD path")
    if type(value) is not str or not value or "\\" in value or "\x00" in value:
        raise RuntimeIdentityCaptureError("RECORD_PATH", "wheel RECORD path is invalid")
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value:
        raise RuntimeIdentityCaptureError("RECORD_PATH", "wheel RECORD path is invalid")
    seen = False
    for component in pure.parts:
        if component == "..":
            if seen:
                raise RuntimeIdentityCaptureError(
                    "RECORD_PATH", "wheel RECORD has interior traversal"
                )
        elif component == ".":
            raise RuntimeIdentityCaptureError("RECORD_PATH", "wheel RECORD has dot traversal")
        else:
            seen = True
    if not seen:
        raise RuntimeIdentityCaptureError("RECORD_PATH", "wheel RECORD path is empty")
    return value


def _parse_record(payload: bytes) -> Tuple[Tuple[str, str, str], ...]:
    try:
        text = payload.decode("utf-8")
        rows = tuple(tuple(row) for row in csv.reader(io.StringIO(text, newline=""), strict=True))
    except (UnicodeDecodeError, csv.Error) as error:
        raise RuntimeIdentityCaptureError("RECORD_CSV", "wheel RECORD is invalid") from error
    if not rows or len(rows) > runtime_identity.MAXIMUM_RECORD_PAYLOADS_PER_DISTRIBUTION:
        raise RuntimeIdentityCaptureError("RECORD_COUNT", "wheel RECORD row count is invalid")
    if any(len(row) != 3 for row in rows):
        raise RuntimeIdentityCaptureError(
            "RECORD_CSV", "wheel RECORD rows require three columns"
        )
    return rows


def _record_installed_path(record_file: Path, record_path: str) -> Path:
    checked = _record_path(record_path)
    return Path(
        os.path.abspath(
            os.fspath(record_file.parent.parent.joinpath(*PurePosixPath(checked).parts))
        )
    )


def _decode_record_sha256(value: str) -> str:
    if not value.startswith("sha256="):
        raise RuntimeIdentityCaptureError(
            "RECORD_HASH", "wheel RECORD uses a non-SHA-256 hash"
        )
    encoded = value[7:]
    if not encoded or re.fullmatch(r"[A-Za-z0-9_-]+", encoded) is None:
        raise RuntimeIdentityCaptureError("RECORD_HASH", "wheel RECORD hash is invalid")
    padded = encoded + "=" * ((4 - len(encoded) % 4) % 4)
    try:
        decoded = base64.b64decode(padded, altchars=b"-_", validate=True)
    except (binascii.Error, ValueError) as error:
        raise RuntimeIdentityCaptureError("RECORD_HASH", "wheel RECORD hash is invalid") from error
    if len(decoded) != 32 or base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != encoded:
        raise RuntimeIdentityCaptureError("RECORD_HASH", "wheel RECORD hash is invalid")
    return decoded.hex()


def _require_beneath(path: Path, root: Path, *, name: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as error:
        raise RuntimeIdentityCaptureError(
            "RECORD_ESCAPE", name + " escaped the fixed virtual environment"
        ) from error


def _capture_distribution(
    metadata_directory: Path,
    *,
    manifest_name: str,
    expected_version: str,
    venv_root: Path,
) -> Dict[str, Any]:
    observed_name, observed_version = _metadata_name_version(metadata_directory / "METADATA")
    if (
        _normalized_distribution_name(observed_name)
        != _normalized_distribution_name(manifest_name)
        or observed_version != expected_version
    ):
        raise RuntimeIdentityCaptureError(
            "DISTRIBUTION_VERSION", "required distribution identity differs from the lock"
        )
    metadata_rows = []
    for kind in runtime_identity.METADATA_FILE_KINDS:
        identity_row = _stream_file_identity(
            metadata_directory / kind,
            name=manifest_name + " " + kind,
            maximum_bytes=runtime_identity.MAXIMUM_RECORD_BYTES
            if kind == "RECORD"
            else MAXIMUM_METADATA_BYTES,
            allow_empty=False,
        )
        identity_row["kind"] = kind
        metadata_rows.append(identity_row)
    record_file = metadata_directory / "RECORD"
    record_payload = _read_regular_file(
        record_file,
        name=manifest_name + " RECORD",
        maximum_bytes=runtime_identity.MAXIMUM_RECORD_BYTES,
    )
    parsed = _parse_record(record_payload)
    payload_rows = []
    seen = set()
    self_count = 0
    for raw_path, claimed_hash, claimed_size in parsed:
        checked_path = _record_path(raw_path)
        if checked_path in seen:
            raise RuntimeIdentityCaptureError("RECORD_DUPLICATE", "wheel RECORD path is duplicated")
        seen.add(checked_path)
        installed_path = _record_installed_path(record_file, checked_path)
        _require_beneath(installed_path, venv_root, name="wheel RECORD payload")
        if installed_path == record_file:
            self_count += 1
            if claimed_hash or claimed_size:
                raise RuntimeIdentityCaptureError(
                    "RECORD_SELF", "wheel RECORD self-row contains a claim"
                )
            continue
        row = _stream_file_identity(
            installed_path,
            name=manifest_name + " installed payload",
            allow_empty=True,
        )
        if claimed_hash and _decode_record_sha256(claimed_hash) != row["sha256"]:
            raise RuntimeIdentityCaptureError("RECORD_HASH", "wheel RECORD hash differs")
        if claimed_size:
            if (
                not claimed_size.isdecimal()
                or str(int(claimed_size)) != claimed_size
                or int(claimed_size) != row["size_bytes"]
            ):
                raise RuntimeIdentityCaptureError("RECORD_SIZE", "wheel RECORD size differs")
        row["record_path"] = checked_path
        payload_rows.append(row)
    if self_count != 1:
        raise RuntimeIdentityCaptureError(
            "RECORD_SELF", "wheel RECORD requires one exact self-row"
        )
    payload_rows.sort(key=lambda row: row["record_path"])
    by_path = {row["path"]: row for row in payload_rows}
    for metadata_row in metadata_rows[:2]:
        payload_row = by_path.get(metadata_row["path"])
        if payload_row is None or (
            payload_row["size_bytes"], payload_row["sha256"]
        ) != (metadata_row["size_bytes"], metadata_row["sha256"]):
            raise RuntimeIdentityCaptureError(
                "RECORD_METADATA", "wheel RECORD does not bind METADATA/WHEEL"
            )
    return {
        "name": manifest_name,
        "version": expected_version,
        "metadata_files": metadata_rows,
        "record_entry_count": len(parsed),
        "record_payloads": payload_rows,
    }


def _parse_direct_url(path: Path, workspace: Path) -> Dict[str, Any]:
    payload = _read_regular_file(
        path, name="editable direct_url.json", maximum_bytes=1024 * 1024
    )
    try:
        value = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeIdentityCaptureError(
            "EDITABLE_METADATA", "direct_url.json is invalid"
        ) from error
    if (
        type(value) is not dict
        or set(value) != {"dir_info", "url"}
        or type(value["dir_info"]) is not dict
        or value["dir_info"] != {"editable": True}
        or type(value["url"]) is not str
    ):
        raise RuntimeIdentityCaptureError(
            "EDITABLE_METADATA", "direct_url.json is not the exact editable schema"
        )
    parsed = urlsplit(value["url"])
    if (
        parsed.scheme != "file"
        or parsed.netloc not in ("", "localhost")
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeIdentityCaptureError(
            "EDITABLE_METADATA", "editable URL is not a local file URL"
        )
    decoded_path = unquote(parsed.path)
    if os.path.abspath(decoded_path) != os.fspath(workspace):
        raise RuntimeIdentityCaptureError(
            "EDITABLE_WORKSPACE", "editable URL differs from the capture workspace"
        )
    return _stream_file_identity(
        path, name="editable direct_url.json", maximum_bytes=1024 * 1024, allow_empty=False
    )


def discover_static_runtime_inventory(
    workspace: Path,
    *,
    site_packages: Optional[Path] = None,
    venv_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Inventory the fixed wheels without importing any numerical package."""

    root = Path(os.path.abspath(os.fspath(workspace)))
    site = root / FIXED_SITE_PACKAGES_RELATIVE_PATH if site_packages is None else Path(site_packages)
    environment_root = root / FIXED_VENV_ROOT_RELATIVE_PATH if venv_root is None else Path(venv_root)
    directories = _distribution_directories(site)
    required_by_normalized = {
        _normalized_distribution_name(name): (name, version)
        for name, version in runtime_identity.REQUIRED_DISTRIBUTIONS
    }
    required_origins: Dict[str, list] = {name: [] for name in required_by_normalized}
    editable_origins = []
    blockers = []
    for origin, observed_name, observed_version in directories:
        normalized = _normalized_distribution_name(observed_name)
        if normalized in required_by_normalized:
            required_origins[normalized].append((origin, observed_version))
        elif normalized == "heterodiff":
            editable_origins.append((origin, observed_version))
        else:
            blockers.append(
                {
                    "code": "EXTRA_DISTRIBUTION",
                    "name": observed_name,
                    "version": observed_version,
                    "origin": os.path.abspath(os.fspath(origin)),
                }
            )
    distributions = []
    for normalized, (manifest_name, expected_version) in required_by_normalized.items():
        matches = required_origins[normalized]
        if len(matches) != 1:
            code = "MISSING_DISTRIBUTION" if not matches else "DUPLICATE_DISTRIBUTION"
            raise RuntimeIdentityCaptureError(
                code, "required distribution does not have one exact origin"
            )
        origin, observed_version = matches[0]
        if observed_version != expected_version:
            raise RuntimeIdentityCaptureError(
                "DISTRIBUTION_VERSION", "required distribution version differs"
            )
        distributions.append(
            _capture_distribution(
                origin,
                manifest_name=manifest_name,
                expected_version=expected_version,
                venv_root=environment_root,
            )
        )
    if len(editable_origins) != 1:
        raise RuntimeIdentityCaptureError(
            "EDITABLE_DISTRIBUTION", "editable heterodiff lacks one exact dist-info origin"
        )
    editable_origin, editable_version = editable_origins[0]
    if editable_version != "0.1.0" or not editable_origin.name.endswith(".dist-info"):
        raise RuntimeIdentityCaptureError(
            "EDITABLE_DISTRIBUTION", "editable heterodiff identity differs"
        )
    direct_url = _parse_direct_url(editable_origin / "direct_url.json", root)
    owners: Dict[str, str] = {}
    inode_paths: Dict[Tuple[int, int], str] = {}
    for distribution in distributions:
        for payload in distribution["record_payloads"]:
            path_text = payload["path"]
            previous_owner = owners.get(path_text)
            if previous_owner is not None:
                raise RuntimeIdentityCaptureError(
                    "CROSS_DISTRIBUTION_PATH",
                    "one installed path is owned by multiple required RECORDs",
                )
            owners[path_text] = distribution["name"]
            metadata = os.lstat(path_text)
            inode = (metadata.st_dev, metadata.st_ino)
            previous_path = inode_paths.get(inode)
            if previous_path is not None and previous_path != path_text:
                raise RuntimeIdentityCaptureError(
                    "RECORD_INODE_ALIAS",
                    "distinct RECORD paths alias one installed inode",
                )
            inode_paths[inode] = path_text
    blockers.sort(key=lambda row: (row["name"].lower(), row["version"], row["origin"]))
    installed_distributions = sorted(
        (
            (name, version, os.path.abspath(os.fspath(origin)))
            for origin, name, version in directories
        ),
        key=lambda row: (_normalized_distribution_name(row[0]), row),
    )
    normalized_installed = [
        _normalized_distribution_name(row[0]) for row in installed_distributions
    ]
    if len(normalized_installed) != len(set(normalized_installed)):
        raise RuntimeIdentityCaptureError(
            "DUPLICATE_INSTALLED_DISTRIBUTION",
            "installed distribution names are duplicated",
        )
    installed_distribution_metadata = []
    for origin, name, version in directories:
        metadata_path = origin / "METADATA"
        if not metadata_path.exists() and origin.name.endswith(".egg-info"):
            metadata_path = origin / "PKG-INFO"
        installed_distribution_metadata.append(
            {
                "name": name,
                "version": version,
                "origin": os.path.abspath(os.fspath(origin)),
                "metadata_identity": _stream_file_identity(
                    metadata_path,
                    name="installed distribution metadata",
                    maximum_bytes=MAXIMUM_METADATA_BYTES,
                    allow_empty=False,
                ),
            }
        )
    installed_distribution_metadata.sort(
        key=lambda row: (
            _normalized_distribution_name(row["name"]),
            row["version"],
            row["origin"],
        )
    )
    return {
        "distributions": distributions,
        "editable_install": {
            "distribution": "heterodiff",
            "editable": True,
            "source_manifest_authoritative": True,
            "direct_url_identity": direct_url,
        },
        "blockers": blockers,
        "installed_distributions": installed_distributions,
        "installed_distribution_metadata": installed_distribution_metadata,
    }


def _fixed_profile() -> Dict[str, Any]:
    observed = {
        "system": platform.system(),
        "machine": platform.machine(),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "pointer_bits": __import__("struct").calcsize("P") * 8,
        "byteorder": sys.byteorder,
        "soabi": sysconfig.get_config_var("SOABI"),
    }
    expected = {
        "system": "Darwin",
        "machine": "arm64",
        "python_implementation": "CPython",
        "python_version": "3.11.5",
        "pointer_bits": 64,
        "byteorder": "little",
        "soabi": "cpython-311-darwin",
    }
    if observed != expected:
        raise RuntimeIdentityCaptureError(
            "TARGET_PROFILE", "capture process is not the frozen target profile"
        )
    return {
        "system": "Darwin",
        "machine": "arm64",
        "translated": False,
        "python_implementation": "CPython",
        "python_version": "3.11.5",
        "python_abi": "cp311",
        "pointer_bits": 64,
        "byteorder": "little",
        "minimum_macos_version": MINIMUM_MACOS_VERSION,
    }


def _framework_shared_library() -> Path:
    framework = sysconfig.get_config_var("PYTHONFRAMEWORK")
    install = sysconfig.get_config_var("PYTHONFRAMEWORKINSTALLDIR")
    if type(framework) is not str or not framework or type(install) is not str or not install:
        raise RuntimeIdentityCaptureError(
            "PYTHON_FRAMEWORK", "CPython framework identity is unavailable"
        )
    version = "%d.%d" % (sys.version_info.major, sys.version_info.minor)
    return Path(install) / "Versions" / version / framework


def _capture_python_files() -> list:
    import encodings

    executable = getattr(sys, "_base_executable", None)
    runtime_path = getattr(encodings, "__file__", None)
    if type(executable) is not str or type(runtime_path) is not str:
        raise RuntimeIdentityCaptureError(
            "PYTHON_FILES", "CPython executable/runtime identity is unavailable"
        )
    rows = []
    for role, path in (
        ("executable", Path(executable)),
        ("runtime", Path(runtime_path)),
        ("shared_library", _framework_shared_library()),
    ):
        row = _stream_file_identity(path, name="Python " + role, allow_empty=False)
        row["role"] = role
        rows.append(row)
    return rows


def _capture_lockfile(workspace: Path) -> Dict[str, Any]:
    row = _stream_file_identity(
        workspace / runtime_identity.LOCKFILE_RELATIVE_PATH,
        name="frozen target lockfile",
        maximum_bytes=runtime_identity.MAXIMUM_LOCKFILE_BYTES,
        allow_empty=False,
    )
    row["path"] = runtime_identity.LOCKFILE_RELATIVE_PATH
    return row


def _distribution_payload_maps(
    distributions: Sequence[Mapping[str, Any]],
) -> Dict[str, Dict[str, Mapping[str, Any]]]:
    result = {}
    for row in distributions:
        result[_normalized_distribution_name(row["name"])] = {
            item["path"]: item for item in row["record_payloads"]
        }
    return result


def _required_record_owner(
    distributions: Sequence[Mapping[str, Any]], path: str
) -> Tuple[str, Mapping[str, Any]]:
    matches = []
    for distribution in distributions:
        for row in distribution["record_payloads"]:
            if row["path"] == path:
                matches.append((distribution["name"], row))
    if len(matches) != 1:
        raise RuntimeIdentityCaptureError(
            "RECORD_OWNERSHIP",
            "runtime file lacks one exact required-distribution RECORD owner",
        )
    return matches[0]


def validate_preimport_module_origins(
    site_packages: Path,
    distributions: Sequence[Mapping[str, Any]],
) -> Dict[str, str]:
    """Reject every import candidate that could precede the RECORD-owned source."""

    import importlib.machinery

    site = Path(os.path.abspath(os.fspath(site_packages)))
    status = os.lstat(site)
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
        raise RuntimeIdentityCaptureError(
            "SITE_PACKAGES_UNSAFE", "site-packages is not a real directory"
        )
    if any(name in sys.modules for name in runtime_identity.REQUIRED_MODULES):
        raise RuntimeIdentityCaptureError(
            "MODULE_PRELOADED", "a required numerical module was loaded before admission"
        )
    payload_maps = _distribution_payload_maps(distributions)
    expected = {}
    for name in runtime_identity.REQUIRED_MODULES:
        suffix = (
            name + "/__init__.py" if name != "threadpoolctl" else "threadpoolctl.py"
        )
        matches = [
            path
            for path in payload_maps[name]
            if path == os.fspath(site / suffix)
        ]
        if len(matches) != 1:
            raise RuntimeIdentityCaptureError(
                "MODULE_STATIC_ORIGIN",
                "required module lacks its exact site-root RECORD origin",
            )
        expected[name] = matches[0]

    extension_suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
    for name, expected_path in expected.items():
        if name == "threadpoolctl":
            forbidden = [site / name, site / (name + ".pyc"), site / (name + ".pyo")]
            forbidden.extend(site / (name + suffix) for suffix in extension_suffixes)
        else:
            package = site / name
            package_status = os.lstat(package)
            if stat.S_ISLNK(package_status.st_mode) or not stat.S_ISDIR(
                package_status.st_mode
            ):
                raise RuntimeIdentityCaptureError(
                    "MODULE_STATIC_ORIGIN", "required package directory is unsafe"
                )
            forbidden = [
                site / (name + ".py"),
                site / (name + ".pyc"),
                site / (name + ".pyo"),
                package / "__init__.pyc",
                package / "__init__.pyo",
            ]
            forbidden.extend(site / (name + suffix) for suffix in extension_suffixes)
            forbidden.extend(
                package / ("__init__" + suffix) for suffix in extension_suffixes
            )
        for candidate in forbidden:
            if os.fspath(candidate) == expected_path:
                continue
            try:
                candidate_status = os.lstat(candidate)
            except FileNotFoundError:
                continue
            del candidate_status
            raise RuntimeIdentityCaptureError(
                "MODULE_SHADOW", "site-packages contains a competing module candidate"
            )
        measured = _stream_file_identity(
            Path(expected_path), name=name + " static module origin", allow_empty=False
        )
        claimed = payload_maps[name][expected_path]
        if (measured["size_bytes"], measured["sha256"]) != (
            claimed["size_bytes"],
            claimed["sha256"],
        ):
            raise RuntimeIdentityCaptureError(
                "MODULE_STATIC_ORIGIN", "static module origin differs from its RECORD"
            )
    return expected


def validate_bootstrap_sys_path(
    workspace: Path, site_packages: Path
) -> Tuple[str, ...]:
    """Freeze the exact standard-library-only path produced by ``-P -S``."""

    root = os.path.abspath(os.fspath(workspace))
    site = os.path.abspath(os.fspath(site_packages))
    if not sys.path or any(
        type(value) is not str
        or not value
        or not os.path.isabs(value)
        or os.path.abspath(value) != value
        for value in sys.path
    ):
        raise RuntimeIdentityCaptureError(
            "BOOTSTRAP_PATH", "capture bootstrap sys.path is not absolute"
        )
    paths = tuple(sys.path)
    if len(paths) != len(set(paths)):
        raise RuntimeIdentityCaptureError(
            "BOOTSTRAP_PATH", "capture bootstrap sys.path is duplicated"
        )
    configured = sysconfig.get_paths()
    stdlib_roots = {
        os.path.abspath(configured[name])
        for name in ("stdlib", "platstdlib")
        if configured.get(name)
    }
    site_roots = {
        os.path.abspath(configured[name])
        for name in ("purelib", "platlib")
        if configured.get(name)
    }
    zip_path = os.path.abspath(
        os.path.join(
            sys.base_prefix,
            "lib",
            "python%d%d.zip" % (sys.version_info.major, sys.version_info.minor),
        )
    )

    def beneath(path: str, roots: Iterable[str]) -> bool:
        return any(os.path.commonpath((path, candidate)) == candidate for candidate in roots)

    for path in paths:
        if path == root or path == site or beneath(path, site_roots):
            raise RuntimeIdentityCaptureError(
                "BOOTSTRAP_PATH", "capture bootstrap exposed project/site paths"
            )
        if path != zip_path and not beneath(path, stdlib_roots):
            raise RuntimeIdentityCaptureError(
                "BOOTSTRAP_PATH", "capture bootstrap sys.path escaped stdlib"
            )
    return paths


def validate_preimport_resolution(expected_origins: Mapping[str, str]) -> None:
    """Require import machinery to select the already RECORD-owned sources."""

    import importlib.util

    for name in runtime_identity.REQUIRED_MODULES:
        specification = importlib.util.find_spec(name)
        if specification is None or specification.loader is None:
            raise RuntimeIdentityCaptureError(
                "MODULE_RESOLUTION", "required module cannot be resolved"
            )
        origin = specification.origin
        if type(origin) is not str or os.path.abspath(origin) != expected_origins[name]:
            raise RuntimeIdentityCaptureError(
                "MODULE_RESOLUTION", "required module resolves outside RECORD custody"
            )
        locations = specification.submodule_search_locations
        if name == "threadpoolctl":
            if locations is not None:
                raise RuntimeIdentityCaptureError(
                    "MODULE_RESOLUTION", "threadpoolctl unexpectedly resolves as a package"
                )
        elif locations is None or tuple(locations) != (
            os.path.dirname(expected_origins[name]),
        ):
            raise RuntimeIdentityCaptureError(
                "MODULE_RESOLUTION", "required package search path differs"
            )


def verify_loaded_module_closure(
    workspace: Path,
    distributions: Sequence[Mapping[str, Any]],
) -> None:
    """Admit only stdlib, verified capture sources, and required RECORD bytes."""

    owned = {}
    for distribution in distributions:
        for row in distribution["record_payloads"]:
            previous = owned.get(row["path"])
            if previous is not None and previous != (
                row["size_bytes"],
                row["sha256"],
            ):
                raise RuntimeIdentityCaptureError(
                    "LOADED_MODULE_CLOSURE", "one owned path has conflicting identities"
                )
            owned[row["path"]] = (row["size_bytes"], row["sha256"])
    root = Path(os.path.abspath(os.fspath(workspace)))
    verified_sources = {
        os.fspath(root / CAPTURE_SOURCE_RELATIVE_PATH),
        os.fspath(root / IDENTITY_SOURCE_RELATIVE_PATH),
    }
    configured = sysconfig.get_paths()
    stdlib_roots = {
        os.path.abspath(configured[name])
        for name in ("stdlib", "platstdlib")
        if configured.get(name)
    }

    def beneath(path: str, roots: Iterable[str]) -> bool:
        for candidate_root in roots:
            try:
                if os.path.commonpath((path, candidate_root)) == candidate_root:
                    return True
            except ValueError:
                continue
        return False

    owned_directories = {
        os.path.dirname(path) for path in owned
    }

    def admit_exact_torch_generated_module(name: str, module: object) -> bool:
        if name != _TORCH_GENERATED_MODULE_NAME:
            return False
        spec = getattr(module, "__spec__", None)
        loader = getattr(spec, "loader", None)
        source = getattr(loader, "data", None)
        if (
            getattr(module, "__name__", None) != name
            or getattr(module, "__package__", None) != ""
            or getattr(module, "__file__", None) is not None
            or spec is None
            or getattr(spec, "name", None) != name
            or getattr(spec, "origin", None) != _TORCH_GENERATED_MODULE_ORIGIN
            or getattr(spec, "submodule_search_locations", None) is not None
            or getattr(module, "__loader__", None) is not loader
            or type(loader).__module__ != _TORCH_GENERATED_LOADER_MODULE
            or type(loader).__qualname__ != _TORCH_GENERATED_LOADER_QUALNAME
            or type(source) is not str
        ):
            return False
        try:
            encoded = source.encode("utf-8")
        except UnicodeEncodeError:
            return False
        if (
            len(encoded) != _TORCH_GENERATED_SOURCE_SIZE_BYTES
            or _sha256_bytes(encoded) != _TORCH_GENERATED_SOURCE_SHA256
        ):
            return False
        generator = sys.modules.get(_TORCH_GENERATED_LOADER_MODULE)
        generator_origin = getattr(generator, "__file__", None)
        if type(generator_origin) is not str or not os.path.isabs(generator_origin):
            return False
        generator_path = os.path.abspath(generator_origin)
        claimed = owned.get(generator_path)
        if claimed is None:
            return False
        measured = _stream_file_identity(
            Path(generator_path),
            name="Torch generated-module source owner",
            allow_empty=False,
        )
        return (measured["size_bytes"], measured["sha256"]) == claimed

    def admit_exact_torch_module_alias(name: str, module: object) -> bool:
        expected = _TORCH_MODULE_ALIASES.get(name)
        if expected is None:
            return False
        owner_name, type_qualname, relative_file = expected
        if (
            type(module).__module__ != owner_name
            or type(module).__qualname__ != type_qualname
            or getattr(module, "__name__", None) != name
            or getattr(module, "__package__", None) is not None
            or getattr(module, "__loader__", None) is not None
            or getattr(module, "__spec__", None) is not None
            or getattr(module, "__file__", None) != relative_file
        ):
            return False
        owner = sys.modules.get(owner_name)
        owner_origin = getattr(owner, "__file__", None)
        if type(owner_origin) is not str or not os.path.isabs(owner_origin):
            return False
        owner_path = os.path.abspath(owner_origin)
        claimed = owned.get(owner_path)
        if claimed is None:
            return False
        measured = _stream_file_identity(
            Path(owner_path), name="Torch module-alias owner", allow_empty=False
        )
        return (measured["size_bytes"], measured["sha256"]) == claimed

    for name, module in tuple(sorted(sys.modules.items())):
        spec = getattr(module, "__spec__", None)
        origin = getattr(module, "__file__", None)
        if origin is None and spec is not None:
            origin = getattr(spec, "origin", None)
        if origin in ("built-in", "frozen"):
            continue
        if origin is None:
            locations = getattr(spec, "submodule_search_locations", None)
            if locations is None:
                # A few interpreter bootstrap placeholders have neither an
                # origin nor package locations and cannot load file-backed code.
                continue
            checked_locations = tuple(locations)
            if not checked_locations:
                raise RuntimeIdentityCaptureError(
                    "LOADED_NAMESPACE", "loaded namespace has no search locations"
                )
            for location in checked_locations:
                if (
                    type(location) is not str
                    or not os.path.isabs(location)
                    or os.path.abspath(location) != location
                    or location not in owned_directories
                    and not any(
                        path.startswith(location + os.sep) for path in owned
                    )
                ):
                    raise RuntimeIdentityCaptureError(
                        "LOADED_NAMESPACE",
                        "loaded namespace search location is outside RECORD custody",
                    )
            continue
        if type(origin) is not str or not os.path.isabs(origin):
            if admit_exact_torch_generated_module(
                name, module
            ) or admit_exact_torch_module_alias(name, module):
                continue
            raise RuntimeIdentityCaptureError(
                "LOADED_MODULE_CLOSURE",
                "loaded module has a nonabsolute origin: " + name,
            )
        path = os.path.abspath(origin)
        if path.endswith((".pyc", ".pyo")):
            raise RuntimeIdentityCaptureError(
                "LOADED_BYTECODE", "loaded module used forbidden bytecode"
            )
        if beneath(path, stdlib_roots):
            continue
        if path in verified_sources:
            continue
        claimed = owned.get(path)
        if claimed is None:
            raise RuntimeIdentityCaptureError(
                "LOADED_MODULE_CLOSURE",
                "loaded non-stdlib module is outside required RECORD custody: " + name,
            )
        measured = _stream_file_identity(
            Path(path), name="loaded module " + name, allow_empty=True
        )
        if (measured["size_bytes"], measured["sha256"]) != claimed:
            raise RuntimeIdentityCaptureError(
                "LOADED_MODULE_CLOSURE", "loaded module differs from its RECORD identity"
            )


def observe_dynamic_runtime(
    distributions: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Import only the four runtime packages and return a deterministic view."""

    modules = {
        name: importlib.import_module(name) for name in _DYNAMIC_MODULE_NAMES
    }
    torch = modules["torch"]
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    expected_versions = dict(runtime_identity.REQUIRED_DISTRIBUTIONS)
    payload_maps = _distribution_payload_maps(distributions)
    module_rows = []
    for name in runtime_identity.REQUIRED_MODULES:
        module = modules[name]
        origin = getattr(module, "__file__", None)
        version = getattr(module, "__version__", None)
        if type(origin) is not str or not origin.endswith(".py"):
            raise RuntimeIdentityCaptureError(
                "MODULE_ORIGIN", "required module origin is not source"
            )
        if version != expected_versions[name]:
            raise RuntimeIdentityCaptureError(
                "MODULE_VERSION", "required module version differs from the lock"
            )
        row = _stream_file_identity(Path(origin), name=name + " module origin", allow_empty=False)
        claimed = payload_maps[name].get(row["path"])
        if claimed is None or (
            claimed["size_bytes"], claimed["sha256"]
        ) != (row["size_bytes"], row["sha256"]):
            raise RuntimeIdentityCaptureError(
                "MODULE_RECORD", "required module origin is absent from its RECORD"
            )
        row["module"] = name
        module_rows.append(row)

    pool_rows = []
    for raw in modules["threadpoolctl"].threadpool_info():
        path = raw.get("filepath")
        if type(path) is not str or not os.path.isabs(path):
            raise RuntimeIdentityCaptureError(
                "NATIVE_POOL", "native pool lacks an absolute library path"
            )
        row = {
            "library_path": os.path.abspath(path),
            "user_api": raw.get("user_api"),
            "internal_api": raw.get("internal_api"),
            "prefix": raw.get("prefix"),
            "version": raw.get("version"),
            "num_threads": raw.get("num_threads"),
        }
        if (
            row["user_api"] not in ("blas", "openmp")
            or any(type(row[key]) is not str or not row[key] for key in ("internal_api", "prefix"))
            or (row["version"] is not None and (type(row["version"]) is not str or not row["version"]))
            or type(row["num_threads"]) is not int
            or row["num_threads"] != 1
        ):
            raise RuntimeIdentityCaptureError(
                "NATIVE_POOL", "native pool identity is incomplete or not single-threaded"
            )
        pool_rows.append(row)
    pool_rows.sort(key=lambda row: row["library_path"])
    pool_paths = [row["library_path"] for row in pool_rows]
    if not pool_rows or len(pool_paths) != len(set(pool_paths)):
        raise RuntimeIdentityCaptureError(
            "NATIVE_POOL", "native pool paths are empty or duplicated"
        )
    native_libraries = []
    for pool in pool_rows:
        identity_row = _stream_file_identity(
            Path(pool["library_path"]), name="active native library", allow_empty=False
        )
        _owner, claimed = _required_record_owner(
            distributions, identity_row["path"]
        )
        if (claimed["size_bytes"], claimed["sha256"]) != (
            identity_row["size_bytes"],
            identity_row["sha256"],
        ):
            raise RuntimeIdentityCaptureError(
                "NATIVE_RECORD", "active native library differs from its RECORD owner"
            )
        identity_row["user_api"] = pool["user_api"]
        native_libraries.append(identity_row)

    cuda_available = bool(torch.cuda.is_available())
    cuda_initialized = bool(torch.cuda.is_initialized())
    cuda_device_count = int(torch.cuda.device_count())
    xpu = getattr(torch, "xpu", None)
    xpu_available = bool(xpu is not None and xpu.is_available())
    xpu_initialized = bool(
        xpu is not None and hasattr(xpu, "is_initialized") and xpu.is_initialized()
    )
    xpu_device_count = int(xpu.device_count()) if xpu is not None else 0
    if (
        cuda_available
        or cuda_initialized
        or cuda_device_count != 0
        or xpu_available
        or xpu_initialized
        or xpu_device_count != 0
    ):
        raise RuntimeIdentityCaptureError(
            "ACCELERATOR_POLICY", "CUDA/XPU is visible or initialized"
        )
    mps = torch.backends.mps
    accelerators = {
        "execution_device_enforced_cpu": True,
        "cuda": {
            "available": cuda_available,
            "device_count": cuda_device_count,
            "initialized": cuda_initialized,
        },
        "xpu": {
            "available": xpu_available,
            "device_count": xpu_device_count,
            "initialized": xpu_initialized,
        },
        "mps": {
            "available": bool(mps.is_available()),
            "built": bool(mps.is_built()),
            "operation_performed": False,
        },
    }
    return {
        "modules": module_rows,
        "native_libraries": native_libraries,
        "native_pools": pool_rows,
        "accelerators": accelerators,
        "torch_cpu_state": {
            "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
            "interop_threads": int(torch.get_num_interop_threads()),
            "threads": int(torch.get_num_threads()),
        },
    }


def build_unapproved_runtime_identity_candidate(
    *,
    profile: Mapping[str, Any],
    lockfile: Mapping[str, Any],
    python_files: Sequence[Mapping[str, Any]],
    static_inventory: Mapping[str, Any],
    dynamic_observation: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build and validate one exact candidate; authority is always false."""

    body = {
        "schema": runtime_identity.RUNTIME_IDENTITY_MANIFEST_SCHEMA,
        "approved": False,
        "profile": _plain_json_value(profile),
        "lockfile": _plain_json_value(lockfile),
        "python_files": _plain_json_value(python_files),
        "modules": _plain_json_value(dynamic_observation["modules"]),
        "distributions": _plain_json_value(static_inventory["distributions"]),
        "editable_install": _plain_json_value(static_inventory["editable_install"]),
        "native_libraries": _plain_json_value(dynamic_observation["native_libraries"]),
        "native_pools": _plain_json_value(dynamic_observation["native_pools"]),
        "accelerators": _plain_json_value(dynamic_observation["accelerators"]),
    }
    body["manifest_sha256"] = runtime_identity.runtime_identity_manifest_self_digest(body)
    checked = runtime_identity.validate_runtime_identity_manifest(body)
    if checked["approved"] is not False:
        raise AssertionError("capture unexpectedly produced launch authority")
    return checked


def capture_contract(identity_source_sha256: str) -> Dict[str, Any]:
    """Return the stable contract whose digest is bound by the review report."""

    if (
        type(identity_source_sha256) is not str
        or len(identity_source_sha256) != 64
        or any(character not in _HEX_DIGITS for character in identity_source_sha256)
    ):
        raise ValueError("identity source digest is invalid")
    return {
        "schema": "heterodiff-a1-runtime-identity-capture-contract-v1",
        "target_profile_id": TARGET_PROFILE_ID,
        "fixed_venv_python": FIXED_VENV_PYTHON_RELATIVE_PATH,
        "fixed_site_packages": FIXED_SITE_PACKAGES_RELATIVE_PATH,
        "interpreter_arguments": ["-P", "-B", "-S", "-X", "utf8"],
        "sanitized_environment": dict(SANITIZED_CAPTURE_ENVIRONMENT),
        "darwin_exec_environment_normalization": {
            "name": _DARWIN_INJECTED_ENVIRONMENT_NAME,
            "expected_value": "0x<EFFECTIVE_UID_HEX>:0x0:0x0",
            "removed_before_numerical_imports": True,
        },
        "required_distributions": [
            [name, version] for name, version in runtime_identity.REQUIRED_DISTRIBUTIONS
        ],
        "required_modules": list(runtime_identity.REQUIRED_MODULES),
        "identity_source_relative_path": IDENTITY_SOURCE_RELATIVE_PATH,
        "identity_source_sha256": identity_source_sha256,
        "candidate_approved": False,
        "scientific_compute_executed": False,
    }


def build_capture_protocol(
    capture_source_sha256: str, identity_source_sha256: str
) -> Dict[str, Any]:
    if (
        type(capture_source_sha256) is not str
        or len(capture_source_sha256) != 64
        or any(character not in _HEX_DIGITS for character in capture_source_sha256)
    ):
        raise ValueError("capture source digest is invalid")
    return {
        "operation": CAPTURE_OPERATION,
        "capture_contract_sha256": sha256_json(
            capture_contract(identity_source_sha256)
        ),
        "source_relative_path": CAPTURE_SOURCE_RELATIVE_PATH,
        "source_sha256": capture_source_sha256,
        "identity_source_relative_path": IDENTITY_SOURCE_RELATIVE_PATH,
        "identity_source_sha256": identity_source_sha256,
        "sanitized_environment_sha256": sha256_json(
            SANITIZED_CAPTURE_ENVIRONMENT
        ),
    }


def build_capture_assessment(
    *,
    blockers: Sequence[Mapping[str, Any]],
    installed_distributions: Sequence[Sequence[str]],
    complete_installed_file_verification: bool,
    dynamic_observations_equal: bool,
) -> Dict[str, Any]:
    blocker_rows = [_plain_json_value(row) for row in blockers]
    if blocker_rows != sorted(
        blocker_rows,
        key=lambda row: (
            row.get("code", ""),
            row.get("name", ""),
            row.get("version", ""),
            row.get("origin", ""),
        ),
    ):
        raise ValueError("capture blockers are not in canonical order")
    for row in blocker_rows:
        if type(row) is not dict or set(row) != {
            "code", "name", "version", "origin"
        }:
            raise ValueError("capture blocker schema is invalid")
        if row["code"] != "EXTRA_DISTRIBUTION" or any(
            type(row[name]) is not str or not row[name]
            for name in ("name", "version", "origin")
        ):
            raise ValueError("capture blocker identity is invalid")
    if type(complete_installed_file_verification) is not bool:
        raise TypeError("capture file-verification flag must be exact bool")
    if type(dynamic_observations_equal) is not bool:
        raise TypeError("capture dynamic-equality flag must be exact bool")
    installed_rows = [list(row) for row in installed_distributions]
    if any(
        len(row) != 3
        or any(type(value) is not str or not value for value in row)
        for row in installed_rows
    ):
        raise ValueError("installed distribution assessment rows are invalid")
    if installed_rows != sorted(
        installed_rows,
        key=lambda row: (_normalized_distribution_name(row[0]), row),
    ):
        raise ValueError("installed distribution assessment is not ordered")
    if len({_normalized_distribution_name(row[0]) for row in installed_rows}) != len(
        installed_rows
    ):
        raise ValueError("installed distribution assessment is duplicated")
    body = {
        "schema": CAPTURE_ASSESSMENT_SCHEMA,
        "blockers": blocker_rows,
        "installed_distributions": installed_rows,
        "complete_installed_file_verification": complete_installed_file_verification,
        "dynamic_observations_equal": dynamic_observations_equal,
        "unexpected_distribution_count": len(blocker_rows),
        "approval_ready": not blocker_rows
        and complete_installed_file_verification
        and dynamic_observations_equal,
        "scientific_compute_executed": False,
    }
    return _digest_record(body, "assessment_sha256")


def validate_capture_assessment(value: object) -> Dict[str, Any]:
    checked = _validate_digest_record(
        value,
        fields={
            "schema",
            "blockers",
            "installed_distributions",
            "complete_installed_file_verification",
            "dynamic_observations_equal",
            "unexpected_distribution_count",
            "approval_ready",
            "scientific_compute_executed",
        },
        digest_name="assessment_sha256",
        schema=CAPTURE_ASSESSMENT_SCHEMA,
    )
    expected = build_capture_assessment(
        blockers=checked["blockers"],
        installed_distributions=checked["installed_distributions"],
        complete_installed_file_verification=checked[
            "complete_installed_file_verification"
        ],
        dynamic_observations_equal=checked["dynamic_observations_equal"],
    )
    if checked != expected:
        raise ValueError("capture assessment differs from deterministic reconstruction")
    return checked


def _validated_darwin_child_environment(
    observed: Mapping[str, str], *, uid: int
) -> Dict[str, str]:
    """Validate and remove macOS's unavoidable per-process CF injection.

    Darwin inserts ``__CF_USER_TEXT_ENCODING`` after ``execve`` even when the
    parent supplies a complete replacement environment.  It encodes only the
    effective numeric UID and a fixed encoding tuple.  The child admits that
    one exact bootstrap value, removes it before any numerical import, and
    then requires the remaining environment to equal the frozen allowlist.
    """

    if type(observed) is not dict or any(
        type(key) is not str or type(value) is not str
        for key, value in observed.items()
    ):
        raise TypeError("capture child environment must be an exact string map")
    if type(uid) is not int or type(uid) is bool or uid < 0:
        raise TypeError("capture child UID must be a nonnegative exact integer")
    normalized = dict(observed)
    injected = normalized.pop(_DARWIN_INJECTED_ENVIRONMENT_NAME, None)
    expected = "0x%X:0x0:0x0" % uid
    if injected != expected:
        raise RuntimeIdentityCaptureError(
            "CHILD_ENVIRONMENT",
            "Darwin injected environment identity is absent or unexpected",
        )
    if normalized != SANITIZED_CAPTURE_ENVIRONMENT:
        raise RuntimeIdentityCaptureError(
            "CHILD_ENVIRONMENT", "capture child environment is not exact"
        )
    return normalized


def _capture_child_envelope(request: Mapping[str, Any]) -> Dict[str, Any]:
    _validated_darwin_child_environment(dict(os.environ), uid=os.getuid())
    del os.environ[_DARWIN_INJECTED_ENVIRONMENT_NAME]
    if dict(os.environ) != SANITIZED_CAPTURE_ENVIRONMENT:
        raise RuntimeIdentityCaptureError(
            "CHILD_ENVIRONMENT", "capture child environment normalization failed"
        )
    if (
        not sys.flags.safe_path
        or not sys.flags.no_site
        or not sys.dont_write_bytecode
        or sys.pycache_prefix != "/dev/null"
    ):
        raise RuntimeIdentityCaptureError(
            "CHILD_FLAGS", "capture child interpreter flags are not exact"
        )
    workspace = Path(request["workspace"])
    if Path.cwd() != workspace:
        raise RuntimeIdentityCaptureError("CHILD_CWD", "capture child cwd differs")
    site_packages = workspace / FIXED_SITE_PACKAGES_RELATIVE_PATH
    venv_root = workspace / FIXED_VENV_ROOT_RELATIVE_PATH
    bootstrap_path = validate_bootstrap_sys_path(workspace, site_packages)
    profile = _fixed_profile()
    lockfile = _capture_lockfile(workspace)
    python_files = _capture_python_files()
    static_inventory = discover_static_runtime_inventory(
        workspace, site_packages=site_packages, venv_root=venv_root
    )
    expected_origins = validate_preimport_module_origins(
        site_packages, static_inventory["distributions"]
    )
    site_text = os.fspath(site_packages)
    if site_text in sys.path:
        raise RuntimeIdentityCaptureError(
            "SITE_PRELOADED", "site-packages was visible before static capture"
        )
    sys.path.append(site_text)
    if tuple(sys.path) != bootstrap_path + (site_text,):
        raise RuntimeIdentityCaptureError(
            "BOOTSTRAP_PATH", "capture child path changed during site admission"
        )
    validate_preimport_resolution(expected_origins)
    pre = observe_dynamic_runtime(static_inventory["distributions"])
    verify_loaded_module_closure(workspace, static_inventory["distributions"])
    candidate = build_unapproved_runtime_identity_candidate(
        profile=profile,
        lockfile=lockfile,
        python_files=python_files,
        static_inventory=static_inventory,
        dynamic_observation=pre,
    )
    candidate_manifest = runtime_identity.RuntimeIdentityManifest(
        path=workspace / CANDIDATE_FILE_NAME,
        record=candidate,
        manifest_sha256=candidate["manifest_sha256"],
        approved=False,
        identity_files_verified=False,
    )
    audited = runtime_identity.audit_unapproved_runtime_identity_candidate_files(
        candidate_manifest
    )
    if audited.identity_files_verified is not True or audited.approved is not False:
        raise RuntimeIdentityCaptureError(
            "CANDIDATE_AUDIT", "unapproved candidate audit did not complete"
        )
    post_static_inventory = discover_static_runtime_inventory(
        workspace, site_packages=site_packages, venv_root=venv_root
    )
    if post_static_inventory != static_inventory:
        raise RuntimeIdentityCaptureError(
            "STATIC_DRIFT", "static runtime inventory changed after numerical imports"
        )
    post = observe_dynamic_runtime(static_inventory["distributions"])
    verify_loaded_module_closure(workspace, static_inventory["distributions"])
    if pre != post:
        raise RuntimeIdentityCaptureError(
            "DYNAMIC_DRIFT", "dynamic runtime changed across observations"
        )
    assessment = build_capture_assessment(
        blockers=static_inventory["blockers"],
        installed_distributions=static_inventory["installed_distributions"],
        complete_installed_file_verification=True,
        dynamic_observations_equal=True,
    )
    body = {
        "schema": CAPTURE_ENVELOPE_SCHEMA,
        "request_sha256": request["request_sha256"],
        "candidate": candidate,
        "capture_protocol": build_capture_protocol(
            request["capture_source_sha256"], request["identity_source_sha256"]
        ),
        "assessment": assessment,
        "scientific_compute_executed": False,
    }
    return _digest_record(body, "envelope_sha256")


def validate_capture_envelope(
    value: object, *, expected_request: Mapping[str, Any]
) -> Dict[str, Any]:
    request = _validate_capture_request(_plain_json_value(expected_request))
    checked = _validate_digest_record(
        value,
        fields={
            "schema",
            "request_sha256",
            "candidate",
            "capture_protocol",
            "assessment",
            "scientific_compute_executed",
        },
        digest_name="envelope_sha256",
        schema=CAPTURE_ENVELOPE_SCHEMA,
    )
    if checked["request_sha256"] != request["request_sha256"]:
        raise ValueError("capture envelope request binding differs")
    candidate = runtime_identity.validate_runtime_identity_manifest(checked["candidate"])
    if candidate["approved"] is not False:
        raise ValueError("capture envelope candidate is approved")
    protocol = checked["capture_protocol"]
    if protocol != build_capture_protocol(
        request["capture_source_sha256"], request["identity_source_sha256"]
    ):
        raise ValueError("capture protocol differs from its frozen reconstruction")
    validate_capture_assessment(checked["assessment"])
    if checked["scientific_compute_executed"] is not False:
        raise ValueError("capture envelope claims scientific computation")
    return checked


def _build_capture_request(workspace: Path) -> Dict[str, Any]:
    capture_identity = _stream_file_identity(
        workspace / CAPTURE_SOURCE_RELATIVE_PATH,
        name="capture source",
        maximum_bytes=16 * 1024 * 1024,
        allow_empty=False,
    )
    identity_identity = _stream_file_identity(
        workspace / IDENTITY_SOURCE_RELATIVE_PATH,
        name="runtime identity source",
        maximum_bytes=16 * 1024 * 1024,
        allow_empty=False,
    )
    body = {
        "schema": CAPTURE_REQUEST_SCHEMA,
        "operation": CAPTURE_OPERATION,
        "workspace": os.fspath(workspace),
        "capture_source_sha256": capture_identity["sha256"],
        "identity_source_sha256": identity_identity["sha256"],
    }
    return _digest_record(body, "request_sha256")


def _validate_capture_request(value: object) -> Dict[str, Any]:
    checked = _validate_digest_record(
        value,
        fields={
            "schema",
            "operation",
            "workspace",
            "capture_source_sha256",
            "identity_source_sha256",
        },
        digest_name="request_sha256",
        schema=CAPTURE_REQUEST_SCHEMA,
    )
    if checked["operation"] != CAPTURE_OPERATION:
        raise ValueError("capture request operation differs")
    workspace = checked["workspace"]
    if type(workspace) is not str or not os.path.isabs(workspace) or os.path.abspath(workspace) != workspace:
        raise ValueError("capture workspace is not a canonical absolute path")
    for key in ("capture_source_sha256", "identity_source_sha256"):
        value_digest = checked[key]
        if type(value_digest) is not str or len(value_digest) != 64 or any(
            character not in _HEX_DIGITS for character in value_digest
        ):
            raise ValueError("capture source digest is invalid")
    return checked


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        try:
            written = os.write(descriptor, payload[offset:])
        except InterruptedError:
            continue
        if written <= 0:
            raise OSError("capture write made no progress")
        offset += written


def _bootstrap_direct_child(request: Mapping[str, Any]) -> None:
    global runtime_identity
    if runtime_identity is not None:
        raise RuntimeIdentityCaptureError(
            "BOOTSTRAP_REENTRY", "capture child bootstrap may run only once"
        )
    workspace = Path(request["workspace"])
    source = workspace / CAPTURE_SOURCE_RELATIVE_PATH
    identity_source = workspace / IDENTITY_SOURCE_RELATIVE_PATH
    for path, digest, name in (
        (source, request["capture_source_sha256"], "capture source"),
        (identity_source, request["identity_source_sha256"], "identity source"),
    ):
        observed = _stream_file_identity(
            path, name=name, maximum_bytes=16 * 1024 * 1024, allow_empty=False
        )
        if observed["sha256"] != digest:
            raise RuntimeIdentityCaptureError(
                "BOOTSTRAP_SOURCE", name + " differs from the request"
            )
    import importlib.util

    module_name = "_heterodiff_capture_runtime_identity"
    specification = importlib.util.spec_from_file_location(
        module_name, os.fspath(identity_source)
    )
    if specification is None or specification.loader is None:
        raise RuntimeIdentityCaptureError(
            "BOOTSTRAP_SOURCE", "runtime identity source cannot be loaded"
        )
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    runtime_identity = module


def _run_capture_child(workspace: Path, request: Mapping[str, Any]) -> bytes:
    interpreter = workspace / FIXED_VENV_PYTHON_RELATIVE_PATH
    source = workspace / CAPTURE_SOURCE_RELATIVE_PATH
    command = [
        os.fspath(interpreter),
        "-P",
        "-B",
        "-S",
        "-X",
        "utf8",
        os.fspath(source),
        "--capture-child",
        canonical_json_bytes(request).decode("ascii"),
    ]
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=dict(SANITIZED_CAPTURE_ENVIRONMENT),
            cwd=os.fspath(workspace),
            shell=False,
            close_fds=True,
            start_new_session=True,
        )
    except OSError as error:
        raise RuntimeIdentityCaptureError(
            "CHILD_LAUNCH", "runtime identity capture child did not spawn"
        ) from error
    stdout, returncode = _collect_capture_child_output(process)
    if returncode != 0:
        code = "CHILD_SIGNAL" if returncode < 0 else "CHILD_EXIT"
        raise RuntimeIdentityCaptureError(
            code, "runtime identity capture child exited unsuccessfully"
        )
    if not stdout:
        raise RuntimeIdentityCaptureError(
            "CHILD_OUTPUT", "runtime identity capture child output is empty"
        )
    return stdout


def _abort_capture_child(process: object) -> None:
    try:
        os.killpg(int(getattr(process, "pid")), signal.SIGKILL)
    except (OSError, TypeError, ValueError):
        try:
            process.kill()
        except (AttributeError, OSError):
            pass
    try:
        process.wait(timeout=2.0)
    except (AttributeError, OSError, subprocess.TimeoutExpired):
        pass


def _collect_capture_child_output(process: object) -> Tuple[bytes, int]:
    stdout = getattr(process, "stdout", None)
    stderr = getattr(process, "stderr", None)
    if stdout is None or stderr is None:
        _abort_capture_child(process)
        raise RuntimeIdentityCaptureError("CHILD_LAUNCH", "capture pipes are absent")
    selector = selectors.DefaultSelector()
    output = bytearray()
    deadline = time.monotonic() + CAPTURE_TIMEOUT_SECONDS
    try:
        for stream, label in ((stdout, "stdout"), (stderr, "stderr")):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _abort_capture_child(process)
                raise RuntimeIdentityCaptureError("CHILD_TIMEOUT", "capture child timed out")
            for key, _mask in selector.select(min(remaining, 0.1)):
                try:
                    block = os.read(key.fileobj.fileno(), 65536)
                except BlockingIOError:
                    continue
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                if key.data == "stderr":
                    _abort_capture_child(process)
                    raise RuntimeIdentityCaptureError(
                        "CHILD_STDERR", "runtime identity capture child wrote stderr"
                    )
                output.extend(block)
                if len(output) > MAXIMUM_CAPTURE_ENVELOPE_BYTES:
                    _abort_capture_child(process)
                    raise RuntimeIdentityCaptureError(
                        "CHILD_OUTPUT", "capture stdout exceeded its byte limit"
                    )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _abort_capture_child(process)
            raise RuntimeIdentityCaptureError("CHILD_TIMEOUT", "capture child timed out")
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as error:
            _abort_capture_child(process)
            raise RuntimeIdentityCaptureError(
                "CHILD_TIMEOUT", "capture child timed out"
            ) from error
    finally:
        selector.close()
        for stream in (stdout, stderr):
            try:
                stream.close()
            except OSError:
                pass
    return bytes(output), int(returncode)


def canonical_runtime_identity_candidate_bytes(
    candidate: Mapping[str, Any]
) -> bytes:
    checked = runtime_identity.validate_runtime_identity_manifest(candidate)
    if checked["approved"] is not False:
        raise ValueError("capture candidate must remain approved=false")
    return runtime_identity.canonical_runtime_identity_manifest_bytes(checked)


def runtime_identity_candidate_relative_path(manifest_sha256: str) -> str:
    if (
        type(manifest_sha256) is not str
        or len(manifest_sha256) != 64
        or any(character not in _HEX_DIGITS for character in manifest_sha256)
    ):
        raise ValueError("candidate manifest digest is invalid")
    return "%s/%s/%s" % (
        CANDIDATE_ROOT_RELATIVE_PATH,
        manifest_sha256,
        CANDIDATE_FILE_NAME,
    )


def _approval_assessment(
    result: RuntimeIdentityCaptureResult,
) -> object:
    assessment = validate_capture_assessment(result.assessment)
    return runtime_approval.RuntimeIdentityCaptureAssessment(
        capture_protocol=dict(result.capture_protocol),
        complete_installed_file_verification=assessment[
            "complete_installed_file_verification"
        ],
        double_capture_stable=assessment["dynamic_observations_equal"],
        installed_distributions=tuple(
            tuple(row) for row in assessment["installed_distributions"]
        ),
        placeholder_paths_absent=all(
            row["path"] != "/UNAPPROVED"
            and not row["path"].startswith("/UNAPPROVED/")
            for row in _candidate_file_rows(result.candidate)
        ),
        scientific_compute_executed=assessment[
            "scientific_compute_executed"
        ],
    )


def _candidate_file_rows(
    candidate: Mapping[str, Any]
) -> Iterable[Mapping[str, Any]]:
    for row in candidate["python_files"]:
        yield row
    for row in candidate["modules"]:
        yield row
    for distribution in candidate["distributions"]:
        for row in distribution["metadata_files"]:
            yield row
        for row in distribution["record_payloads"]:
            yield row
    yield candidate["editable_install"]["direct_url_identity"]
    for row in candidate["native_libraries"]:
        yield row


def _capture_runtime_identity_candidate_at_root(
    root: Path,
) -> RuntimeIdentityCaptureResult:
    root = Path(root).resolve(strict=True)
    request = _build_capture_request(root)
    request_bytes = canonical_json_bytes(request)
    if len(request_bytes) > MAXIMUM_CAPTURE_REQUEST_BYTES:
        raise RuntimeIdentityCaptureError("REQUEST_SIZE", "capture request is too large")
    output = _run_capture_child(root, request)
    envelope = decode_canonical_json(
        output,
        maximum_bytes=MAXIMUM_CAPTURE_ENVELOPE_BYTES,
        description="capture child envelope",
    )
    checked = validate_capture_envelope(
        envelope, expected_request=request
    )
    return RuntimeIdentityCaptureResult(
        candidate=checked["candidate"],
        capture_protocol=checked["capture_protocol"],
        assessment=checked["assessment"],
    )


def capture_runtime_identity_candidate() -> RuntimeIdentityCapturePublication:
    """Capture and content-address publish one explicitly unapproved review."""

    root = Path(__file__).resolve(strict=True).parents[3]
    result = _capture_runtime_identity_candidate_at_root(root)
    placeholder_payload = _read_regular_file(
        root / runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH,
        name="frozen runtime identity placeholder",
        maximum_bytes=runtime_identity.MAXIMUM_MANIFEST_BYTES,
    )
    approval_assessment = _approval_assessment(result)
    report = runtime_approval.build_runtime_identity_review_report(
        result.candidate,
        frozen_placeholder_payload=placeholder_payload,
        capture_assessment=approval_assessment,
    )
    candidate_path, report_path = (
        runtime_approval.publish_runtime_identity_candidate_and_review(
            result.candidate, report
        )
    )
    return RuntimeIdentityCapturePublication(
        candidate_path=candidate_path,
        report_path=report_path,
        candidate=result.candidate,
        report=report,
        assessment=result.assessment,
    )


def recapture_runtime_identity_candidate_for_approval(
    root: Path,
) -> object:
    """Fresh non-publishing boundary used only after interactive confirmation."""

    repository = Path(__file__).resolve(strict=True).parents[3]
    supplied = Path(root).resolve(strict=True)
    if supplied != repository:
        raise ValueError("approval recapture root differs from this repository")
    result = _capture_runtime_identity_candidate_at_root(repository)
    return runtime_approval.RuntimeIdentityRecapture(
        record=result.candidate,
        assessment=_approval_assessment(result),
    )


def _child_main(argument: str) -> int:
    request = decode_canonical_json(
        argument.encode("ascii"),
        maximum_bytes=MAXIMUM_CAPTURE_REQUEST_BYTES,
        description="capture child request",
    )
    checked_request = _validate_capture_request(request)
    _bootstrap_direct_child(checked_request)
    envelope = _capture_child_envelope(checked_request)
    payload = canonical_json_bytes(envelope)
    if len(payload) > MAXIMUM_CAPTURE_ENVELOPE_BYTES:
        raise RuntimeIdentityCaptureError(
            "CHILD_OUTPUT", "capture child envelope exceeds its byte limit"
        )
    _write_all(1, payload)
    return 0


def main(arguments: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if arguments is None else arguments)
    if len(argv) == 2 and argv[0] == "--capture-child":
        return _child_main(argv[1])
    if argv not in ([], ["capture"]):
        raise SystemExit("usage: finite_association_runtime_identity_capture.py capture")
    publication = capture_runtime_identity_candidate()
    summary = {
        "candidate_path": os.fspath(publication.candidate_path),
        "report_path": os.fspath(publication.report_path),
        "manifest_sha256": publication.candidate["manifest_sha256"],
        "report_sha256": publication.report["report_sha256"],
        "approved": False,
        "approval_ready": publication.report["approval_ready"],
    }
    _write_all(1, canonical_json_file_bytes(summary))
    return 0


if __name__ == "__main__":  # pragma: no cover - explicit operator command
    raise SystemExit(main())


__all__ = [
    "CAPTURE_ASSESSMENT_SCHEMA",
    "CAPTURE_ENVELOPE_SCHEMA",
    "CAPTURE_OPERATION",
    "CAPTURE_REQUEST_SCHEMA",
    "CAPTURE_SOURCE_RELATIVE_PATH",
    "CANDIDATE_FILE_NAME",
    "CANDIDATE_ROOT_RELATIVE_PATH",
    "FIXED_SITE_PACKAGES_RELATIVE_PATH",
    "FIXED_VENV_PYTHON_RELATIVE_PATH",
    "IDENTITY_SOURCE_RELATIVE_PATH",
    "RuntimeIdentityCaptureError",
    "RuntimeIdentityCapturePublication",
    "RuntimeIdentityCaptureResult",
    "SANITIZED_CAPTURE_ENVIRONMENT",
    "build_capture_assessment",
    "build_capture_protocol",
    "build_unapproved_runtime_identity_candidate",
    "canonical_json_bytes",
    "canonical_json_file_bytes",
    "canonical_runtime_identity_candidate_bytes",
    "capture_contract",
    "capture_runtime_identity_candidate",
    "discover_static_runtime_inventory",
    "observe_dynamic_runtime",
    "recapture_runtime_identity_candidate_for_approval",
    "runtime_identity_candidate_relative_path",
    "sha256_json",
    "TARGET_PROFILE_ID",
    "validate_bootstrap_sys_path",
    "validate_capture_assessment",
    "validate_capture_envelope",
    "validate_preimport_module_origins",
    "validate_preimport_resolution",
    "verify_loaded_module_closure",
]
