"""Standard-library custody for the A1 target runtime identity manifest.

This module deliberately imports no numerical package and performs no
scientific computation.  It validates an exact, target-generated inventory of
the bytes that may support a future attested subprocess.  Merely loading an
inventory never authorizes a subprocess: the checked-in placeholder has
``approved: false``, and the approval-requiring boundary fails before checking
any of its placeholder installed-file paths.

The threat model is the repository's non-hostile local-host model.  Stable,
no-follow reads close accidental symlink, replacement, truncation, and stale
identity failures; they are not a defence against a hostile kernel or account.
"""

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
import re
import stat
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


RUNTIME_IDENTITY_MANIFEST_SCHEMA = (
    "heterodiff-a1-production-runtime-identity-manifest-v1"
)
RUNTIME_IDENTITY_RELATIVE_PATH = (
    "requirements/m1-reference-macos-arm64-py311.runtime-identity.json"
)
LOCKFILE_RELATIVE_PATH = "requirements/m1-reference-macos-arm64-py311.lock"

MAXIMUM_MANIFEST_BYTES = 32 * 1024 * 1024
MAXIMUM_LOCKFILE_BYTES = 2 * 1024 * 1024
MAXIMUM_IDENTITY_FILE_BYTES = 8 * 1024 * 1024 * 1024
MAXIMUM_RECORD_PAYLOADS_PER_DISTRIBUTION = 200_000
MAXIMUM_RECORD_BYTES = 64 * 1024 * 1024
MAXIMUM_NATIVE_LIBRARIES = 128

REQUIRED_MODULES = ("numpy", "scipy", "threadpoolctl", "torch")
REQUIRED_DISTRIBUTIONS = (
    ("filelock", "3.32.0"),
    ("fsspec", "2026.6.0"),
    ("iniconfig", "2.3.0"),
    ("Jinja2", "3.1.6"),
    ("MarkupSafe", "3.0.3"),
    ("mpmath", "1.3.0"),
    ("networkx", "3.6.1"),
    ("numpy", "2.4.6"),
    ("packaging", "26.2"),
    ("pip", "23.2.1"),
    ("pluggy", "1.6.0"),
    ("pyflakes", "3.4.0"),
    ("Pygments", "2.20.0"),
    ("pytest", "9.1.1"),
    ("scipy", "1.17.1"),
    ("setuptools", "65.5.0"),
    ("sympy", "1.14.0"),
    ("torch", "2.12.1"),
    ("threadpoolctl", "3.6.0"),
    ("typing_extensions", "4.16.0"),
)
PYTHON_FILE_ROLES = ("executable", "runtime", "shared_library")
METADATA_FILE_KINDS = ("METADATA", "WHEEL", "RECORD")

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema",
        "approved",
        "profile",
        "lockfile",
        "python_files",
        "modules",
        "distributions",
        "editable_install",
        "native_libraries",
        "native_pools",
        "accelerators",
        "manifest_sha256",
    }
)
_PROFILE_KEYS = frozenset(
    {
        "system",
        "machine",
        "translated",
        "python_implementation",
        "python_version",
        "python_abi",
        "pointer_bits",
        "byteorder",
        "minimum_macos_version",
    }
)
_HEX_DIGITS = frozenset("0123456789abcdef")
_MACOS_VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*))?\Z")


@dataclass(frozen=True)
class RuntimeIdentityManifest:
    """Immutable result of a bounded manifest load.

    ``identity_files_verified`` is true only after every declared installed
    file has been reread and matched.  That fact is evidence, not launch
    authority: an unapproved capture candidate may be audited with the
    candidate-only boundary below, while the approval-requiring production
    boundary still rejects it.
    """

    path: Path
    record: Mapping[str, object]
    manifest_sha256: str
    approved: bool
    identity_files_verified: bool


def _plain_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json_value(item) for item in value]
    return value


def _canonical_json(value: object) -> bytes:
    try:
        encoded = json.dumps(
            _plain_json_value(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise TypeError("value is not canonical-JSON serializable") from error
    return encoded.encode("ascii")


def canonical_runtime_identity_manifest_bytes(record: object) -> bytes:
    """Return the sole admitted on-disk encoding (canonical JSON plus LF)."""

    return _canonical_json(record) + b"\n"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def runtime_identity_manifest_self_digest(record: Mapping[str, object]) -> str:
    """Digest the canonical manifest body, excluding its self-digest field."""

    if not isinstance(record, Mapping):
        raise TypeError("runtime identity manifest must be a mapping")
    body = dict(record)
    body.pop("manifest_sha256", None)
    return _sha256_bytes(_canonical_json(body))


def _deep_freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType(
            {key: _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _exact_keys(value: object, expected: Iterable[str], *, name: str) -> dict:
    if type(value) is not dict:
        raise ValueError("%s must be an object" % name)
    expected_keys = frozenset(expected)
    actual_keys = frozenset(value)
    if actual_keys != expected_keys or any(type(key) is not str for key in value):
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys, key=str)
        raise ValueError(
            "%s has a non-exact schema (missing=%r, extra=%r)"
            % (name, missing, extra)
        )
    return value


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError("%s must be an exact boolean" % name)
    return value


def _bounded_string(
    value: object, *, name: str, maximum: int = 4096, nonempty: bool = True
) -> str:
    if type(value) is not str:
        raise ValueError("%s must be a string" % name)
    if (nonempty and not value) or len(value) > maximum or "\x00" in value:
        raise ValueError("%s has an invalid length or NUL byte" % name)
    try:
        value.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("%s must be ASCII" % name) from error
    return value


def _sha256(value: object, *, name: str) -> str:
    digest = _bounded_string(value, name=name, maximum=64)
    if len(digest) != 64 or any(character not in _HEX_DIGITS for character in digest):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return digest


def _positive_size(value: object, *, name: str) -> int:
    if type(value) is not int or value <= 0 or value > MAXIMUM_IDENTITY_FILE_BYTES:
        raise ValueError("%s must be a bounded positive exact integer" % name)
    return value


def _nonnegative_file_size(value: object, *, name: str) -> int:
    if type(value) is not int or value < 0 or value > MAXIMUM_IDENTITY_FILE_BYTES:
        raise ValueError("%s must be a bounded nonnegative exact integer" % name)
    return value


def _nonnegative_count(value: object, *, name: str, maximum: int) -> int:
    if type(value) is not int or value < 0 or value > maximum:
        raise ValueError("%s must be a bounded nonnegative exact integer" % name)
    return value


def _absolute_manifest_path(value: object, *, name: str) -> str:
    path = _bounded_string(value, name=name)
    pure = PurePosixPath(path)
    if (
        not pure.is_absolute()
        or path == "/"
        or str(pure) != path
        or any(part in (".", "..") for part in pure.parts)
    ):
        raise ValueError("%s must be a normalized absolute POSIX file path" % name)
    return path


def _relative_manifest_path(value: object, *, name: str) -> str:
    path = _bounded_string(value, name=name)
    pure = PurePosixPath(path)
    if pure.is_absolute() or str(pure) != path or any(
        part in (".", "..") for part in pure.parts
    ):
        raise ValueError("%s must be a normalized relative POSIX path" % name)
    return path


def _record_relative_path(value: object, *, name: str) -> str:
    """Validate one exact wheel-RECORD path without resolving it yet.

    Wheel installers may use leading ``..`` components for scripts or data
    outside site-packages.  Interior traversal is unnecessary and ambiguous,
    so every traversal component must precede the first ordinary component.
    """

    if type(value) is not str or not value or len(value) > 8192 or "\x00" in value:
        raise ValueError("%s has an invalid length or NUL byte" % name)
    path = value
    try:
        path.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("%s is not valid UTF-8 text" % name) from error
    if "\\" in path:
        raise ValueError("%s must use POSIX separators" % name)
    pure = PurePosixPath(path)
    if pure.is_absolute() or pure.as_posix() != path:
        raise ValueError("%s must be a canonical relative POSIX path" % name)
    seen_component = False
    for component in pure.parts:
        if component == ".":
            raise ValueError("%s contains a dot component" % name)
        if component == "..":
            if seen_component:
                raise ValueError("%s has interior parent traversal" % name)
        else:
            seen_component = True
    if not seen_component:
        raise ValueError("%s does not identify a file" % name)
    return path


def _validate_file_identity(
    value: object,
    *,
    name: str,
    discriminator_name: Optional[str] = None,
    discriminator_value: Optional[str] = None,
) -> dict:
    keys = {"path", "size_bytes", "sha256"}
    if discriminator_name is not None:
        keys.add(discriminator_name)
    row = _exact_keys(value, keys, name=name)
    _absolute_manifest_path(row["path"], name=name + ".path")
    _positive_size(row["size_bytes"], name=name + ".size_bytes")
    _sha256(row["sha256"], name=name + ".sha256")
    if discriminator_name is not None:
        discriminator = _bounded_string(
            row[discriminator_name], name=name + "." + discriminator_name
        )
        if discriminator_value is not None and discriminator != discriminator_value:
            raise ValueError(
                "%s.%s must equal %r"
                % (name, discriminator_name, discriminator_value)
            )
    return row


def _require_list(value: object, *, name: str) -> list:
    if type(value) is not list:
        raise ValueError("%s must be an array" % name)
    return value


def _require_unique_ordered_paths(rows: Sequence[Mapping[str, object]], *, name: str) -> None:
    paths = tuple(row["path"] for row in rows)
    if len(set(paths)) != len(paths):
        raise ValueError("%s paths must be unique" % name)
    if paths != tuple(sorted(paths)):
        raise ValueError("%s paths must be in canonical lexical order" % name)


def _validate_profile(value: object) -> None:
    profile = _exact_keys(value, _PROFILE_KEYS, name="profile")
    exact_values = {
        "system": "Darwin",
        "machine": "arm64",
        "translated": False,
        "python_implementation": "CPython",
        "python_version": "3.11.5",
        "python_abi": "cp311",
        "pointer_bits": 64,
        "byteorder": "little",
    }
    for key, expected in exact_values.items():
        if type(profile[key]) is not type(expected) or profile[key] != expected:
            raise ValueError("profile.%s must equal %r" % (key, expected))
    version = _bounded_string(
        profile["minimum_macos_version"], name="profile.minimum_macos_version", maximum=32
    )
    if _MACOS_VERSION.fullmatch(version) is None:
        raise ValueError("profile.minimum_macos_version is not canonical")


def _validate_lockfile(value: object) -> None:
    row = _exact_keys(value, {"path", "size_bytes", "sha256"}, name="lockfile")
    path = _relative_manifest_path(row["path"], name="lockfile.path")
    if path != LOCKFILE_RELATIVE_PATH:
        raise ValueError("lockfile.path does not name the frozen M1 lock")
    _positive_size(row["size_bytes"], name="lockfile.size_bytes")
    _sha256(row["sha256"], name="lockfile.sha256")


def _validate_python_files(value: object) -> None:
    rows = _require_list(value, name="python_files")
    if len(rows) != len(PYTHON_FILE_ROLES):
        raise ValueError("python_files must contain exactly three role rows")
    checked = []
    for index, expected_role in enumerate(PYTHON_FILE_ROLES):
        row = _validate_file_identity(
            rows[index],
            name="python_files[%d]" % index,
            discriminator_name="role",
            discriminator_value=expected_role,
        )
        checked.append(row)
    paths = tuple(row["path"] for row in checked)
    if len(set(paths)) != len(paths):
        raise ValueError("python_files paths must be unique")


def _validate_modules(value: object) -> None:
    rows = _require_list(value, name="modules")
    if len(rows) != len(REQUIRED_MODULES):
        raise ValueError("modules must contain exactly the required module rows")
    checked = []
    for index, expected_module in enumerate(REQUIRED_MODULES):
        row = _validate_file_identity(
            rows[index],
            name="modules[%d]" % index,
            discriminator_name="module",
            discriminator_value=expected_module,
        )
        checked.append(row)
    paths = tuple(row["path"] for row in checked)
    if len(set(paths)) != len(paths):
        raise ValueError("module origin paths must be unique")


def _validate_metadata_files(value: object, *, distribution_index: int) -> None:
    name = "distributions[%d].metadata_files" % distribution_index
    rows = _require_list(value, name=name)
    if len(rows) != len(METADATA_FILE_KINDS):
        raise ValueError("%s must contain METADATA, WHEEL, and RECORD" % name)
    checked = []
    for index, expected_kind in enumerate(METADATA_FILE_KINDS):
        row = _validate_file_identity(
            rows[index],
            name="%s[%d]" % (name, index),
            discriminator_name="kind",
            discriminator_value=expected_kind,
        )
        checked.append(row)
    if len({row["path"] for row in checked}) != len(checked):
        raise ValueError("%s paths must be unique" % name)


def _validate_record_payloads(
    value: object, *, distribution_index: int, expected_count: int
) -> None:
    name = "distributions[%d].record_payloads" % distribution_index
    rows = _require_list(value, name=name)
    if not rows or len(rows) != expected_count - 1:
        raise ValueError(
            "%s must contain every declared RECORD row except RECORD itself"
            % name
        )
    checked = []
    for index, value_row in enumerate(rows):
        row_name = "%s[%d]" % (name, index)
        row = _exact_keys(
            value_row,
            {"path", "record_path", "size_bytes", "sha256"},
            name=row_name,
        )
        _absolute_manifest_path(row["path"], name=row_name + ".path")
        _nonnegative_file_size(
            row["size_bytes"], name=row_name + ".size_bytes"
        )
        _sha256(row["sha256"], name=row_name + ".sha256")
        _record_relative_path(
            row["record_path"], name=row_name + ".record_path"
        )
        checked.append(row)
    paths = tuple(row["path"] for row in checked)
    record_paths = tuple(row["record_path"] for row in checked)
    if len(set(paths)) != len(paths):
        raise ValueError("%s installed paths must be unique" % name)
    if (
        len(set(record_paths)) != len(record_paths)
        or record_paths != tuple(sorted(record_paths))
    ):
        raise ValueError("%s RECORD paths must be unique and ordered" % name)


def _validate_distributions(value: object) -> None:
    rows = _require_list(value, name="distributions")
    if len(rows) != len(REQUIRED_DISTRIBUTIONS):
        raise ValueError(
            "distributions must contain exactly the required distribution rows"
        )
    for index, (expected_name, expected_version) in enumerate(REQUIRED_DISTRIBUTIONS):
        name = "distributions[%d]" % index
        row = _exact_keys(
            rows[index],
            {
                "name",
                "version",
                "metadata_files",
                "record_entry_count",
                "record_payloads",
            },
            name=name,
        )
        if _bounded_string(row["name"], name=name + ".name", maximum=128) != expected_name:
            raise ValueError("%s.name must equal %r" % (name, expected_name))
        if _bounded_string(row["version"], name=name + ".version", maximum=128) != expected_version:
            raise ValueError("%s.version must equal %r" % (name, expected_version))
        count = _nonnegative_count(
            row["record_entry_count"],
            name=name + ".record_entry_count",
            maximum=MAXIMUM_RECORD_PAYLOADS_PER_DISTRIBUTION,
        )
        if count == 0:
            raise ValueError(name + ".record_entry_count must be positive")
        _validate_metadata_files(row["metadata_files"], distribution_index=index)
        _validate_record_payloads(
            row["record_payloads"],
            distribution_index=index,
            expected_count=count,
        )


def _validate_editable_install(value: object) -> None:
    row = _exact_keys(
        value,
        {
            "distribution",
            "editable",
            "source_manifest_authoritative",
            "direct_url_identity",
        },
        name="editable_install",
    )
    if row["distribution"] != "heterodiff" or type(row["distribution"]) is not str:
        raise ValueError("editable_install.distribution must equal 'heterodiff'")
    if _exact_bool(row["editable"], name="editable_install.editable") is not True:
        raise ValueError("editable_install.editable must be true")
    if (
        _exact_bool(
            row["source_manifest_authoritative"],
            name="editable_install.source_manifest_authoritative",
        )
        is not True
    ):
        raise ValueError("production source manifest must remain authoritative")
    _validate_file_identity(
        row["direct_url_identity"], name="editable_install.direct_url_identity"
    )


def _validate_native_libraries(value: object) -> Tuple[str, ...]:
    rows = _require_list(value, name="native_libraries")
    if not rows or len(rows) > MAXIMUM_NATIVE_LIBRARIES:
        raise ValueError("native_libraries has an invalid row count")
    checked = []
    for index, value_row in enumerate(rows):
        name = "native_libraries[%d]" % index
        expanded = _exact_keys(
            value_row, {"path", "size_bytes", "sha256", "user_api"}, name=name
        )
        _absolute_manifest_path(expanded["path"], name=name + ".path")
        _positive_size(expanded["size_bytes"], name=name + ".size_bytes")
        _sha256(expanded["sha256"], name=name + ".sha256")
        user_api = _bounded_string(
            expanded["user_api"], name=name + ".user_api", maximum=32
        )
        if user_api not in ("blas", "openmp"):
            raise ValueError(name + ".user_api must be 'blas' or 'openmp'")
        checked.append(expanded)
    _require_unique_ordered_paths(checked, name="native_libraries")
    return tuple(row["path"] for row in checked)


def _validate_native_pools(value: object, *, library_paths: Tuple[str, ...]) -> None:
    rows = _require_list(value, name="native_pools")
    if not rows or len(rows) > MAXIMUM_NATIVE_LIBRARIES:
        raise ValueError("native_pools has an invalid row count")
    checked_paths = []
    for index, value_row in enumerate(rows):
        name = "native_pools[%d]" % index
        row = _exact_keys(
            value_row,
            {
                "library_path",
                "user_api",
                "internal_api",
                "prefix",
                "version",
                "num_threads",
            },
            name=name,
        )
        path = _absolute_manifest_path(
            row["library_path"], name=name + ".library_path"
        )
        user_api = _bounded_string(row["user_api"], name=name + ".user_api", maximum=32)
        if user_api not in ("blas", "openmp"):
            raise ValueError(name + ".user_api must be 'blas' or 'openmp'")
        for key in ("internal_api", "prefix"):
            _bounded_string(row[key], name=name + "." + key, maximum=256)
        if row["version"] is not None:
            _bounded_string(
                row["version"], name=name + ".version", maximum=256
            )
        if type(row["num_threads"]) is not int or row["num_threads"] != 1:
            raise ValueError(name + ".num_threads must be the exact integer one")
        checked_paths.append(path)
    paths = tuple(checked_paths)
    if len(set(paths)) != len(paths) or paths != tuple(sorted(paths)):
        raise ValueError("native_pools library paths must be unique and ordered")
    if paths != library_paths:
        raise ValueError(
            "native_pools must cover every and only declared native library"
        )


def _validate_native_pool_api_alignment(
    native_libraries: Sequence[Mapping[str, object]],
    native_pools: Sequence[Mapping[str, object]],
) -> None:
    library_api = {row["path"]: row["user_api"] for row in native_libraries}
    for index, row in enumerate(native_pools):
        if row["user_api"] != library_api[row["library_path"]]:
            raise ValueError(
                "native_pools[%d].user_api differs from its library identity"
                % index
            )


def _validate_accelerator(value: object, *, name: str, allow_available: bool) -> None:
    expected_keys = {"available", "initialized"}
    if name in ("cuda", "xpu"):
        expected_keys.add("device_count")
    row = _exact_keys(value, expected_keys, name="accelerators." + name)
    available = _exact_bool(
        row["available"], name="accelerators.%s.available" % name
    )
    initialized = _exact_bool(
        row["initialized"], name="accelerators.%s.initialized" % name
    )
    if initialized:
        raise ValueError("accelerators.%s must not be initialized" % name)
    if not allow_available and available:
        raise ValueError("accelerators.%s must be unavailable" % name)
    if name in ("cuda", "xpu"):
        count = _nonnegative_count(
            row["device_count"],
            name="accelerators.%s.device_count" % name,
            maximum=1024,
        )
        if count != 0:
            raise ValueError("accelerators.%s.device_count must be zero" % name)


def _validate_accelerators(value: object) -> None:
    row = _exact_keys(
        value,
        {"execution_device_enforced_cpu", "cuda", "xpu", "mps"},
        name="accelerators",
    )
    if (
        _exact_bool(
            row["execution_device_enforced_cpu"],
            name="accelerators.execution_device_enforced_cpu",
        )
        is not True
    ):
        raise ValueError("the execution device must be enforced CPU")
    _validate_accelerator(row["cuda"], name="cuda", allow_available=False)
    _validate_accelerator(row["xpu"], name="xpu", allow_available=False)
    mps = _exact_keys(
        row["mps"],
        {"built", "available", "operation_performed"},
        name="accelerators.mps",
    )
    built = _exact_bool(mps["built"], name="accelerators.mps.built")
    available = _exact_bool(mps["available"], name="accelerators.mps.available")
    operation_performed = _exact_bool(
        mps["operation_performed"],
        name="accelerators.mps.operation_performed",
    )
    if operation_performed or (available and not built):
        raise ValueError("accelerators.mps policy is not CPU-safe or coherent")


def validate_runtime_identity_manifest(record: object) -> Dict[str, Any]:
    """Validate and return a shallow copy of one exact manifest record."""

    manifest = _exact_keys(record, _TOP_LEVEL_KEYS, name="runtime identity manifest")
    if manifest["schema"] != RUNTIME_IDENTITY_MANIFEST_SCHEMA:
        raise ValueError("runtime identity manifest schema is not frozen")
    _exact_bool(manifest["approved"], name="approved")
    _validate_profile(manifest["profile"])
    _validate_lockfile(manifest["lockfile"])
    _validate_python_files(manifest["python_files"])
    _validate_modules(manifest["modules"])
    _validate_distributions(manifest["distributions"])
    _validate_editable_install(manifest["editable_install"])
    library_paths = _validate_native_libraries(manifest["native_libraries"])
    _validate_native_pools(manifest["native_pools"], library_paths=library_paths)
    _validate_native_pool_api_alignment(
        manifest["native_libraries"], manifest["native_pools"]
    )
    _validate_accelerators(manifest["accelerators"])
    supplied_digest = _sha256(
        manifest["manifest_sha256"], name="manifest_sha256"
    )
    expected_digest = runtime_identity_manifest_self_digest(manifest)
    if supplied_digest != expected_digest:
        raise ValueError("runtime identity manifest self-digest differs")
    return dict(manifest)


def _reject_duplicate_keys(pairs: Sequence[Tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("runtime identity manifest contains duplicate keys")
        result[key] = value
    return result


def parse_runtime_identity_manifest_bytes(payload: object) -> Dict[str, Any]:
    """Parse bounded, duplicate-free, finite, canonical manifest bytes."""

    if type(payload) is not bytes:
        raise TypeError("runtime identity manifest payload must be exact bytes")
    if not payload or len(payload) > MAXIMUM_MANIFEST_BYTES:
        raise ValueError("runtime identity manifest has an invalid byte length")
    try:
        decoded = payload.decode("ascii")
        value = json.loads(
            decoded,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError("non-finite JSON constant %s" % token)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as error:
        raise ValueError("runtime identity manifest is invalid JSON") from error
    checked = validate_runtime_identity_manifest(value)
    if payload != canonical_runtime_identity_manifest_bytes(checked):
        raise ValueError("runtime identity manifest bytes are not canonical")
    return checked


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
            raise RuntimeError("%s ancestor is absent" % name) from error
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError("%s ancestors must not be symlinks" % name)
        if not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError("%s ancestor is not a directory" % name)
        if current.parent == current:
            break
        current = current.parent


def _read_regular_file_stably(path: Path, maximum_bytes: int, *, name: str) -> bytes:
    if not path.is_absolute():
        raise RuntimeError("%s path must be absolute" % name)
    _reject_symlink_ancestors(path, name=name)
    try:
        before = os.lstat(path)
    except FileNotFoundError as error:
        raise RuntimeError("%s is absent" % name) from error
    if not stat.S_ISREG(before.st_mode):
        raise RuntimeError("%s is not a regular file" % name)
    if before.st_size <= 0 or before.st_size > maximum_bytes:
        raise RuntimeError("%s has an invalid byte length" % name)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(os.fspath(path), flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or _path_identity(opened) != _path_identity(before):
            raise RuntimeError("%s identity changed while opening" % name)
        chunks = []
        remaining = maximum_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after_path = os.lstat(path)
    except FileNotFoundError as error:
        raise RuntimeError("%s disappeared while reading" % name) from error
    if (
        _path_identity(after_descriptor) != _path_identity(opened)
        or _path_identity(after_path) != _path_identity(opened)
    ):
        raise RuntimeError("%s changed while reading" % name)
    if not payload or len(payload) > maximum_bytes or len(payload) != opened.st_size:
        raise RuntimeError("%s read length is invalid" % name)
    return payload


def _bind_lockfile(record: Mapping[str, object], lockfile_path: Path) -> None:
    payload = _read_regular_file_stably(
        lockfile_path, MAXIMUM_LOCKFILE_BYTES, name="runtime identity lockfile"
    )
    declared = record["lockfile"]
    if len(payload) != declared["size_bytes"]:
        raise RuntimeError("runtime identity lockfile size differs from manifest")
    if _sha256_bytes(payload) != declared["sha256"]:
        raise RuntimeError("runtime identity lockfile digest differs from manifest")


def _verify_regular_file_identity_stably(
    path: Path, *, expected_size: int, expected_sha256: str, name: str
) -> None:
    """Stream one installed identity without materializing its payload."""

    if not path.is_absolute():
        raise RuntimeError("%s path must be absolute" % name)
    if expected_size < 0 or expected_size > MAXIMUM_IDENTITY_FILE_BYTES:
        raise RuntimeError("%s declared size exceeds its byte limit" % name)
    _reject_symlink_ancestors(path, name=name)
    try:
        before = os.lstat(path)
    except FileNotFoundError as error:
        raise RuntimeError("%s is absent" % name) from error
    if not stat.S_ISREG(before.st_mode):
        raise RuntimeError("%s is not a regular file" % name)
    if before.st_size != expected_size:
        raise RuntimeError("runtime identity installed-file size differs")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(os.fspath(path), flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or _path_identity(opened) != _path_identity(before):
            raise RuntimeError("%s identity changed while opening" % name)
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > expected_size:
                raise RuntimeError("runtime identity installed-file size differs")
            digest.update(chunk)
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after_path = os.lstat(path)
    except FileNotFoundError as error:
        raise RuntimeError("%s disappeared while reading" % name) from error
    if (
        _path_identity(after_descriptor) != _path_identity(opened)
        or _path_identity(after_path) != _path_identity(opened)
    ):
        raise RuntimeError("%s changed while reading" % name)
    if total != expected_size:
        raise RuntimeError("runtime identity installed-file size differs")
    if digest.hexdigest() != expected_sha256:
        raise RuntimeError("runtime identity installed-file digest differs")


def _record_installed_path(record_file: Path, record_path: str) -> Path:
    """Map a canonical wheel RECORD path to its installed absolute path."""

    checked = _record_relative_path(record_path, name="wheel RECORD path")
    base = record_file.parent.parent
    return Path(
        os.path.abspath(
            os.fspath(base.joinpath(*PurePosixPath(checked).parts))
        )
    )


def _decode_record_sha256(value: str) -> str:
    prefix = "sha256="
    if not value.startswith(prefix):
        raise RuntimeError("wheel RECORD uses a non-SHA-256 payload hash")
    encoded = value[len(prefix) :]
    allowed = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz"
        "0123456789-_"
    )
    if not encoded or any(character not in allowed for character in encoded):
        raise RuntimeError("wheel RECORD SHA-256 encoding is not canonical")
    padded = encoded + "=" * ((4 - len(encoded) % 4) % 4)
    try:
        decoded = base64.b64decode(
            padded.encode("ascii"), altchars=b"-_", validate=True
        )
    except (binascii.Error, ValueError) as error:
        raise RuntimeError("wheel RECORD SHA-256 encoding is invalid") from error
    if (
        len(decoded) != hashlib.sha256().digest_size
        or base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii")
        != encoded
    ):
        raise RuntimeError("wheel RECORD SHA-256 encoding is invalid")
    return decoded.hex()


def _parse_record_rows(payload: bytes) -> Tuple[Tuple[str, str, str], ...]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError("wheel RECORD is not valid UTF-8") from error
    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        rows = tuple(tuple(row) for row in reader)
    except (csv.Error, UnicodeError) as error:
        raise RuntimeError("wheel RECORD CSV is invalid") from error
    if not rows or len(rows) > MAXIMUM_RECORD_PAYLOADS_PER_DISTRIBUTION:
        raise RuntimeError("wheel RECORD row count is invalid")
    if any(len(row) != 3 for row in rows):
        raise RuntimeError("wheel RECORD rows must have exactly three columns")
    return rows


def _verify_distribution_record_claims(
    record: Mapping[str, object]
) -> None:
    """Bind every wheel RECORD row to one independently measured file row."""

    for distribution_index, distribution in enumerate(record["distributions"]):
        metadata = {
            row["kind"]: row for row in distribution["metadata_files"]
        }
        record_identity = metadata["RECORD"]
        record_path = Path(record_identity["path"])
        payload = _read_regular_file_stably(
            record_path,
            MAXIMUM_RECORD_BYTES,
            name="distribution %d RECORD" % distribution_index,
        )
        if (
            len(payload) != record_identity["size_bytes"]
            or _sha256_bytes(payload) != record_identity["sha256"]
        ):
            raise RuntimeError("wheel RECORD bytes differ from the manifest")
        parsed = _parse_record_rows(payload)
        if len(parsed) != distribution["record_entry_count"]:
            raise RuntimeError("wheel RECORD row count differs from the manifest")
        declared = {
            row["record_path"]: row for row in distribution["record_payloads"]
        }
        observed = {}
        self_rows = 0
        for raw_path, record_hash, record_size in parsed:
            checked_path = _record_relative_path(
                raw_path, name="wheel RECORD path"
            )
            if checked_path in observed:
                raise RuntimeError("wheel RECORD paths are duplicated")
            installed_path = _record_installed_path(record_path, checked_path)
            if installed_path == record_path:
                self_rows += 1
                if record_hash or record_size:
                    raise RuntimeError(
                        "wheel RECORD self-row must not hash or size itself"
                    )
                observed[checked_path] = None
                continue
            row = declared.get(checked_path)
            if row is None or Path(row["path"]) != installed_path:
                raise RuntimeError(
                    "wheel RECORD claim lacks its exact installed identity"
                )
            if record_hash and _decode_record_sha256(record_hash) != row["sha256"]:
                raise RuntimeError("wheel RECORD payload hash differs")
            if record_size:
                if (
                    not record_size.isdecimal()
                    or str(int(record_size)) != record_size
                    or int(record_size) != row["size_bytes"]
                ):
                    raise RuntimeError("wheel RECORD payload size differs")
            observed[checked_path] = row
        if self_rows != 1:
            raise RuntimeError("wheel RECORD must contain one exact self-row")
        nonself = {key for key, value in observed.items() if value is not None}
        if nonself != set(declared):
            raise RuntimeError(
                "wheel RECORD and manifest payload coverage differ"
            )
        declared_by_installed_path = {
            row["path"]: row for row in distribution["record_payloads"]
        }
        for kind in ("METADATA", "WHEEL"):
            metadata_row = metadata[kind]
            payload_row = declared_by_installed_path.get(metadata_row["path"])
            if payload_row is None or (
                payload_row["size_bytes"], payload_row["sha256"]
            ) != (metadata_row["size_bytes"], metadata_row["sha256"]):
                raise RuntimeError(
                    "wheel RECORD does not bind the exact %s bytes" % kind
                )


def load_runtime_identity_manifest(
    path: Path, *, lockfile_path: Path
) -> RuntimeIdentityManifest:
    """Load one manifest and bind it to the exact supplied lockfile bytes.

    This structural loader does not verify installed identity paths and does not
    grant execution authority, even if the record says it is approved.
    """

    manifest_path = Path(path)
    lock_path = Path(lockfile_path)
    payload = _read_regular_file_stably(
        manifest_path, MAXIMUM_MANIFEST_BYTES, name="runtime identity manifest"
    )
    record = parse_runtime_identity_manifest_bytes(payload)
    _bind_lockfile(record, lock_path)
    return RuntimeIdentityManifest(
        path=manifest_path,
        record=_deep_freeze(record),
        manifest_sha256=record["manifest_sha256"],
        approved=record["approved"],
        identity_files_verified=False,
    )


def _declared_file_rows(record: Mapping[str, object]) -> Iterable[Mapping[str, object]]:
    for row in record["python_files"]:
        yield row
    for row in record["modules"]:
        yield row
    for distribution in record["distributions"]:
        for row in distribution["metadata_files"]:
            yield row
        for row in distribution["record_payloads"]:
            yield row
    yield record["editable_install"]["direct_url_identity"]
    for row in record["native_libraries"]:
        yield row


def _verify_runtime_identity_files_impl(
    manifest: RuntimeIdentityManifest,
) -> RuntimeIdentityManifest:
    """Recheck every declared installed file without granting authority."""

    _verify_distribution_record_claims(manifest.record)
    expected_by_path = {}
    for index, row in enumerate(_declared_file_rows(manifest.record)):
        path = row["path"]
        identity = (row["size_bytes"], row["sha256"])
        previous = expected_by_path.get(path)
        if previous is not None and previous != identity:
            raise RuntimeError(
                "one installed path has conflicting declared identities"
            )
        expected_by_path[path] = identity
    for index, path_text in enumerate(sorted(expected_by_path)):
        expected_size, expected_digest = expected_by_path[path_text]
        _verify_regular_file_identity_stably(
            Path(path_text),
            expected_size=expected_size,
            expected_sha256=expected_digest,
            name="runtime identity installed file %d" % index,
        )
    return RuntimeIdentityManifest(
        path=manifest.path,
        record=manifest.record,
        manifest_sha256=manifest.manifest_sha256,
        approved=manifest.approved,
        identity_files_verified=True,
    )


def verify_runtime_identity_files(
    manifest: RuntimeIdentityManifest,
) -> RuntimeIdentityManifest:
    """Recheck an approved manifest's files for the production boundary."""

    if type(manifest) is not RuntimeIdentityManifest:
        raise TypeError("identity-file verification requires a loaded manifest")
    if manifest.approved is not True:
        raise RuntimeError(
            "unapproved runtime identity files must not be inspected by the "
            "approval-requiring boundary"
        )
    return _verify_runtime_identity_files_impl(manifest)


def audit_unapproved_runtime_identity_candidate_files(
    manifest: RuntimeIdentityManifest,
) -> RuntimeIdentityManifest:
    """Fully inspect a capture candidate while preserving ``approved=false``.

    This function exists only for deterministic capture and human review.  It
    refuses approved manifests, never changes the approval bit, and cannot be
    used by the scientific-launch boundary as a source of authority.
    """

    if type(manifest) is not RuntimeIdentityManifest:
        raise TypeError("candidate-file audit requires a loaded manifest")
    if manifest.approved is not False:
        raise RuntimeError("candidate-file audit requires approved=false")
    return _verify_runtime_identity_files_impl(manifest)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def checked_in_runtime_identity_path() -> Path:
    return _repository_root() / RUNTIME_IDENTITY_RELATIVE_PATH


def checked_in_runtime_identity_lockfile_path() -> Path:
    return _repository_root() / LOCKFILE_RELATIVE_PATH


def load_checked_in_runtime_identity_manifest() -> RuntimeIdentityManifest:
    """Load the fixed checked-in manifest without granting launch authority."""

    return load_runtime_identity_manifest(
        checked_in_runtime_identity_path(),
        lockfile_path=checked_in_runtime_identity_lockfile_path(),
    )


def require_approved_checked_in_runtime_identity_manifest() -> RuntimeIdentityManifest:
    """Require the complete reviewed approval bundle and all installed bytes.

    The inline Boolean is only an early rejection signal.  It never grants
    authority by itself: an approved manifest must reconstruct its immutable
    approved-false candidate and match the content-addressed review, archived
    placeholder, procedural receipt, and live installed-file verification.
    """

    manifest = load_checked_in_runtime_identity_manifest()
    if manifest.approved is not True:
        raise RuntimeError(
            "target runtime identity manifest is not operator-approved; "
            "scientific child launch is forbidden"
        )
    approval = importlib.import_module(
        "heterodiff.experiments."
        "finite_association_runtime_identity_approval"
    )
    bundle = approval.verify_checked_in_runtime_identity_approval()
    verified = getattr(bundle, "manifest", None)
    if (
        verified is None
        or getattr(verified, "approved", None) is not True
        or getattr(verified, "identity_files_verified", None) is not True
        or getattr(verified, "manifest_sha256", None)
        != manifest.manifest_sha256
        or Path(getattr(verified, "path", "")) != manifest.path
        or _plain_json_value(getattr(verified, "record", None))
        != _plain_json_value(manifest.record)
    ):
        raise RuntimeError(
            "approved runtime identity bundle differs from the checked-in manifest"
        )
    # The fresh-process attestor deliberately direct-loads this source under a
    # private module name before admitting the project package.  The approval
    # verifier is then imported canonically, so its dataclass is a distinct
    # Python type even though both modules are source-identical.  Rewrap the
    # already related/verified result into this calling module's exact type so
    # subsequent PRE/POST file verification remains type-safe.
    return RuntimeIdentityManifest(
        path=manifest.path,
        record=manifest.record,
        manifest_sha256=manifest.manifest_sha256,
        approved=True,
        identity_files_verified=True,
    )


__all__ = [
    "LOCKFILE_RELATIVE_PATH",
    "MAXIMUM_MANIFEST_BYTES",
    "RUNTIME_IDENTITY_MANIFEST_SCHEMA",
    "RUNTIME_IDENTITY_RELATIVE_PATH",
    "RuntimeIdentityManifest",
    "audit_unapproved_runtime_identity_candidate_files",
    "canonical_runtime_identity_manifest_bytes",
    "checked_in_runtime_identity_lockfile_path",
    "checked_in_runtime_identity_path",
    "load_checked_in_runtime_identity_manifest",
    "load_runtime_identity_manifest",
    "parse_runtime_identity_manifest_bytes",
    "require_approved_checked_in_runtime_identity_manifest",
    "runtime_identity_manifest_self_digest",
    "validate_runtime_identity_manifest",
    "verify_runtime_identity_files",
]
