#!/usr/bin/env python3
"""Data-free native Databricks Runtime capture for the additive B08 route.

The helper reads only the exact native profile and F152 lock below one explicit
project root, inspects standard-library runtime/package metadata and module
origins, and writes one no-clobber private receipt.  It performs no network,
Databricks API, Spark, subprocess, entropy, dataset, model, calibration,
training, inference, or outcome operation.

The checked-in native profile intentionally names a missing, unresolved F152
lock.  Until that exact path contains a complete hash-pinned lock, capture
fails with ``F152_LOCK_UNRESOLVED``.  A successful receipt is only a candidate
for independent review and never grants scientific-execution authority.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata as importlib_metadata
from importlib import util as importlib_util
import json
import os
from pathlib import Path
import platform
import re
import stat
import struct
import sys
import sysconfig
from typing import Dict, Mapping, Sequence, Tuple

from heterodiff.experiments import b08_databricks_native_runtime_profile as profile


SCHEMA_VERSION = "heterodiff-b08-databricks-native-runtime-capture-v1"
RECEIPT_DOMAIN = b"heterodiff/b08/databricks-native-runtime-capture/v1\0"
COLLECTION_DOMAIN = b"heterodiff/b08/databricks-native-runtime-collection/v1\0"
MAX_PROFILE_BYTES = 4 * 1024 * 1024
MAX_LOCK_BYTES = 32 * 1024 * 1024
MAX_DISTRIBUTIONS = 20_000
MAX_MODULE_BYTES = 256 * 1024 * 1024
MAX_RECEIPT_BYTES = 64 * 1024 * 1024

FORBIDDEN_OUTPUT_ROOTS = (
    (Path("/dbfs"), "DBFS_OUTPUT_FORBIDDEN"),
    (Path("/Volumes"), "VOLUME_OUTPUT_FORBIDDEN"),
    (Path("/Workspace"), "WORKSPACE_OUTPUT_FORBIDDEN"),
)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_REVISION = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_DBR_VERSION = re.compile(r"17\.3(?:\..*)?\Z")
_REQUIREMENT = re.compile(
    r"(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)=="
    r"(?P<version>[A-Za-z0-9][A-Za-z0-9.!+_-]*)(?:[ \t]+\\)?\Z"
)
_HASH_LINE = re.compile(r"--hash=sha256:[0-9a-f]{64}(?:[ \t]+\\)?\Z")

_TOP_KEYS = frozenset(
    {
        "schema_version",
        "receipt_payload_sha256",
        "profile_binding",
        "f152_lock_observation",
        "source_binding",
        "native_runtime",
        "python_abi",
        "f153_controls",
        "installed_distributions",
        "module_origins",
        "safety_boundary",
        "decision",
    }
)

_PROFILE_BINDING_KEYS = frozenset(
    {"path", "profile_id", "record_sha256", "file_sha256", "lifecycle_state"}
)
_LOCK_OBSERVATION_KEYS = frozenset(
    {
        "path",
        "sha256",
        "size_bytes",
        "requirement_count",
        "requirements",
        "complete_transitive_lock_verified_by_capture",
        "artifact_closure_verified_by_capture",
        "all_requirements_exactly_pinned",
        "all_declared_requirements_sha256_hashed",
    }
)
_REQUIREMENT_KEYS = frozenset({"name", "version", "sha256_hash_count"})
_SOURCE_BINDING_KEYS = frozenset(
    {"revision", "manifest_sha256", "declaration_externally_authenticated"}
)
_F153_CONTROL_KEYS = frozenset(
    {
        "requested_preimport_environment",
        "torch_runtime_observation_performed",
        "torch_deterministic_algorithms_verified",
        "torch_warn_only_false_verified",
        "torch_intraop_threads_one_verified",
        "torch_interop_threads_one_verified",
        "cudnn_benchmark_false_verified",
        "cuda_unavailable_or_disabled_verified",
        "mps_unavailable_or_disabled_verified",
        "every_process_worker_equivalence_verified",
        "f153_effective_runtime_satisfaction_claimed",
        "unresolved_runtime_controls",
    }
)
_RUNTIME_KEYS = frozenset(
    {
        "databricks_runtime_environment",
        "system",
        "machine",
        "python_implementation",
        "python_version",
        "python_executable",
        "unobserved_target_paths",
    }
)
_ABI_KEYS = frozenset(
    {
        "soabi",
        "multiarch",
        "extension_suffix",
        "cache_tag",
        "pointer_bits",
        "byteorder",
        "libc_name",
        "libc_version",
        "platform_tag",
    }
)
_DISTRIBUTION_OBSERVATION_KEYS = frozenset(
    {"entries", "metadata_observation_sha256", "payload_closure_verified"}
)
_DISTRIBUTION_ENTRY_KEYS = frozenset({"name", "version", "metadata_root"})
_MODULE_OBSERVATION_KEYS = frozenset(
    {"entries", "origin_observation_sha256", "distribution_ownership_verified"}
)
_MODULE_ENTRY_KEYS = frozenset(
    {
        "distribution",
        "module",
        "origin",
        "origin_sha256",
        "origin_size_bytes",
        "distribution_metadata_root_observation",
        "distribution_ownership_verified",
    }
)


class NativeRuntimeCaptureError(RuntimeError):
    """A native runtime input, observation, or receipt failed closed."""


def _exact_object(value: object, keys: frozenset[str], label: str) -> dict:
    if type(value) is not dict or frozenset(value) != keys:
        raise NativeRuntimeCaptureError(label + "_KEY_ROSTER_INVALID")
    return value


def _nonempty_ascii(value: object, label: str, maximum: int = 4096) -> str:
    if type(value) is not str or not value or len(value) > maximum or "\x00" in value:
        raise NativeRuntimeCaptureError(label + "_INVALID")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as error:
        raise NativeRuntimeCaptureError(label + "_INVALID") from error
    return value


def _require_sha256(value: object, label: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise NativeRuntimeCaptureError(label + "_INVALID")
    return value


def _validate_source_literals(revision: object, manifest_sha256: object) -> None:
    if type(revision) is not str or _REVISION.fullmatch(revision) is None:
        raise NativeRuntimeCaptureError("SOURCE_REVISION_INVALID")
    if type(manifest_sha256) is not str or _SHA256.fullmatch(manifest_sha256) is None:
        raise NativeRuntimeCaptureError("SOURCE_MANIFEST_SHA256_INVALID")


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise NativeRuntimeCaptureError("NONCANONICAL_JSON_VALUE") from error


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _collection_sha256(value: object) -> str:
    return _sha256(COLLECTION_DOMAIN + _canonical_bytes(value))


def _normalize_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).casefold()


def _absolute_directory(value: str, label: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        raise NativeRuntimeCaptureError(label + "_MUST_BE_ABSOLUTE")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise NativeRuntimeCaptureError(label + "_UNAVAILABLE") from error
    try:
        mode = resolved.stat().st_mode
    except OSError as error:
        raise NativeRuntimeCaptureError(label + "_UNAVAILABLE") from error
    if not stat.S_ISDIR(mode):
        raise NativeRuntimeCaptureError(label + "_NOT_DIRECTORY")
    return resolved


def _output_path(value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        raise NativeRuntimeCaptureError("OUTPUT_MUST_BE_ABSOLUTE")
    try:
        parent = candidate.parent.resolve(strict=True)
    except OSError as error:
        raise NativeRuntimeCaptureError("OUTPUT_PARENT_UNAVAILABLE") from error
    if not stat.S_ISDIR(parent.stat().st_mode):
        raise NativeRuntimeCaptureError("OUTPUT_PARENT_NOT_DIRECTORY")
    resolved_candidate = parent / candidate.name
    for forbidden_root, code in FORBIDDEN_OUTPUT_ROOTS:
        try:
            resolved_candidate.relative_to(forbidden_root)
        except ValueError:
            continue
        raise NativeRuntimeCaptureError(code)
    return resolved_candidate


def _read_stable_regular_file(path: Path, maximum_bytes: int, label: str) -> bytes:
    try:
        before = path.lstat()
    except FileNotFoundError as error:
        if label == "F152_LOCK":
            raise NativeRuntimeCaptureError("F152_LOCK_UNRESOLVED") from error
        raise NativeRuntimeCaptureError(label + "_MISSING") from error
    except OSError as error:
        raise NativeRuntimeCaptureError(label + "_UNREADABLE") from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise NativeRuntimeCaptureError(label + "_NOT_REGULAR")
    if before.st_size <= 0 or before.st_size > maximum_bytes:
        raise NativeRuntimeCaptureError(label + "_SIZE_OUT_OF_RANGE")
    try:
        raw = path.read_bytes()
        after = path.lstat()
    except OSError as error:
        raise NativeRuntimeCaptureError(label + "_UNREADABLE") from error
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after or len(raw) != before.st_size:
        raise NativeRuntimeCaptureError(label + "_CHANGED_DURING_READ")
    return raw


def _validate_private_receipt_stat(value: os.stat_result, label: str) -> None:
    if not stat.S_ISREG(value.st_mode):
        raise NativeRuntimeCaptureError(label + "_NOT_REGULAR")
    if stat.S_IMODE(value.st_mode) != 0o600:
        raise NativeRuntimeCaptureError(label + "_MODE_NOT_PRIVATE_0600")
    if value.st_uid != os.geteuid():
        raise NativeRuntimeCaptureError(label + "_OWNER_MISMATCH")
    if value.st_nlink != 1:
        raise NativeRuntimeCaptureError(label + "_HARDLINK_FORBIDDEN")


def _read_private_receipt(path: Path) -> bytes:
    try:
        before = path.lstat()
    except OSError as error:
        raise NativeRuntimeCaptureError("RECEIPT_UNAVAILABLE") from error
    if stat.S_ISLNK(before.st_mode):
        raise NativeRuntimeCaptureError("RECEIPT_SYMLINK_FORBIDDEN")
    _validate_private_receipt_stat(before, "RECEIPT")
    if before.st_size <= 0 or before.st_size > MAX_RECEIPT_BYTES:
        raise NativeRuntimeCaptureError("RECEIPT_SIZE_OUT_OF_RANGE")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise NativeRuntimeCaptureError("RECEIPT_OPEN_FAILED") from error
    try:
        opened = os.fstat(descriptor)
        _validate_private_receipt_stat(opened, "RECEIPT")
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise NativeRuntimeCaptureError("RECEIPT_CHANGED_BEFORE_OPEN")
        chunks = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, MAX_RECEIPT_BYTES - total + 1))
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_RECEIPT_BYTES:
                raise NativeRuntimeCaptureError("RECEIPT_SIZE_OUT_OF_RANGE")
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
        if (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
            opened.st_nlink,
        ) != (
            after_fd.st_dev,
            after_fd.st_ino,
            after_fd.st_size,
            after_fd.st_mtime_ns,
            after_fd.st_nlink,
        ):
            raise NativeRuntimeCaptureError("RECEIPT_CHANGED_DURING_READ")
    finally:
        os.close(descriptor)
    try:
        after_path = path.lstat()
    except OSError as error:
        raise NativeRuntimeCaptureError("RECEIPT_CHANGED_AFTER_READ") from error
    _validate_private_receipt_stat(after_path, "RECEIPT")
    if (after_path.st_dev, after_path.st_ino) != (before.st_dev, before.st_ino):
        raise NativeRuntimeCaptureError("RECEIPT_CHANGED_AFTER_READ")
    raw = b"".join(chunks)
    if len(raw) != before.st_size:
        raise NativeRuntimeCaptureError("RECEIPT_CHANGED_DURING_READ")
    return raw


def _load_profile(project_root: Path) -> Tuple[dict, bytes]:
    path = project_root / profile.PROFILE_PATH
    raw = _read_stable_regular_file(path, MAX_PROFILE_BYTES, "NATIVE_PROFILE")
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise NativeRuntimeCaptureError("NATIVE_PROFILE_INVALID_JSON") from error
    if raw != profile.canonical_json_bytes(value) + b"\n":
        raise NativeRuntimeCaptureError("NATIVE_PROFILE_NONCANONICAL")
    try:
        validated = profile.validate_profile(value)
    except profile.NativeRuntimeProfileError as error:
        raise NativeRuntimeCaptureError("NATIVE_PROFILE_INVALID:" + str(error)) from error
    if validated["lifecycle_state"] != profile.DRAFT_UNRESOLVED_F152_LOCK:
        raise NativeRuntimeCaptureError("NATIVE_PROFILE_NOT_EXACT_DRAFT")
    return validated, raw


def _parse_lock(raw: bytes) -> Tuple[dict, ...]:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise NativeRuntimeCaptureError("F152_LOCK_NOT_ASCII") from error
    if not text.endswith("\n") or "\r" in text:
        raise NativeRuntimeCaptureError("F152_LOCK_FRAMING_INVALID")

    entries = []
    current = None
    current_hashes = 0
    seen = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if _HASH_LINE.fullmatch(line) is not None:
            if current is None:
                raise NativeRuntimeCaptureError("F152_LOCK_HASH_WITHOUT_REQUIREMENT")
            current_hashes += 1
            continue
        if current is not None:
            if current_hashes < 1:
                raise NativeRuntimeCaptureError("F152_LOCK_REQUIREMENT_WITHOUT_HASH")
            entries.append({**current, "sha256_hash_count": current_hashes})
        match = _REQUIREMENT.fullmatch(line)
        if match is None:
            raise NativeRuntimeCaptureError("F152_LOCK_FORBIDDEN_SYNTAX")
        name = _normalize_distribution_name(match.group("name"))
        if name in seen:
            raise NativeRuntimeCaptureError("F152_LOCK_DUPLICATE_REQUIREMENT:" + name)
        seen.add(name)
        current = {"name": name, "version": match.group("version")}
        current_hashes = 0
    if current is None:
        raise NativeRuntimeCaptureError("F152_LOCK_EMPTY")
    if current_hashes < 1:
        raise NativeRuntimeCaptureError("F152_LOCK_REQUIREMENT_WITHOUT_HASH")
    entries.append({**current, "sha256_hash_count": current_hashes})

    versions = {entry["name"]: entry["version"] for entry in entries}
    for name, expected in profile.EXPECTED_DISTRIBUTIONS.items():
        if versions.get(name) != expected:
            raise NativeRuntimeCaptureError("F152_LOCK_EXPECTED_VERSION_MISMATCH:" + name)
    return tuple(entries)


def _f153_environment() -> Dict[str, str]:
    captured = {name: os.environ.get(name) for name in profile.F153_ENVIRONMENT}
    if captured != profile.F153_ENVIRONMENT:
        mismatches = sorted(
            name
            for name, expected in profile.F153_ENVIRONMENT.items()
            if captured.get(name) != expected
        )
        raise NativeRuntimeCaptureError("F153_ENVIRONMENT_MISMATCH:" + ",".join(mismatches))
    return dict(captured)


def _f153_controls(environment: Mapping[str, str]) -> Dict[str, object]:
    return {
        "requested_preimport_environment": dict(environment),
        "torch_runtime_observation_performed": False,
        "torch_deterministic_algorithms_verified": False,
        "torch_warn_only_false_verified": False,
        "torch_intraop_threads_one_verified": False,
        "torch_interop_threads_one_verified": False,
        "cudnn_benchmark_false_verified": False,
        "cuda_unavailable_or_disabled_verified": False,
        "mps_unavailable_or_disabled_verified": False,
        "every_process_worker_equivalence_verified": False,
        "f153_effective_runtime_satisfaction_claimed": False,
        "unresolved_runtime_controls": [
            "torch.use_deterministic_algorithms(True,warn_only=False)",
            "torch.set_num_threads(1)",
            "torch.set_num_interop_threads(1)",
            "torch.backends.cudnn.benchmark=False",
            "CUDA_UNAVAILABLE_OR_DISABLED",
            "MPS_UNAVAILABLE_OR_DISABLED",
            "EVERY_ELIGIBLE_DRIVER_AND_WORKER_PROCESS_EQUIVALENT",
        ],
    }


def _runtime_identity() -> Tuple[Dict[str, object], Dict[str, object]]:
    dbr = os.environ.get("DATABRICKS_RUNTIME_VERSION")
    if type(dbr) is not str or _DBR_VERSION.fullmatch(dbr) is None:
        raise NativeRuntimeCaptureError("DBR_17_3_RUNTIME_NOT_OBSERVED")
    if platform.system() != "Linux":
        raise NativeRuntimeCaptureError("RUNTIME_SYSTEM_NOT_LINUX")
    if platform.machine().casefold() != "x86_64":
        raise NativeRuntimeCaptureError("RUNTIME_ARCH_NOT_X86_64")
    version = platform.python_version()
    if version != "3.12.3" or platform.python_implementation() != "CPython":
        raise NativeRuntimeCaptureError("RUNTIME_NOT_CPYTHON_3_12_3")
    pointer_bits = struct.calcsize("P") * 8
    if pointer_bits != 64 or sys.byteorder != "little":
        raise NativeRuntimeCaptureError("RUNTIME_ABI_WORD_OR_BYTEORDER_MISMATCH")

    soabi = sysconfig.get_config_var("SOABI")
    multiarch = sysconfig.get_config_var("MULTIARCH")
    ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
    if type(soabi) is not str or not soabi.startswith("cpython-312-"):
        raise NativeRuntimeCaptureError("PYTHON_SOABI_MISMATCH")
    if multiarch != "x86_64-linux-gnu":
        raise NativeRuntimeCaptureError("PYTHON_MULTIARCH_MISMATCH")
    if type(ext_suffix) is not str or "cpython-312" not in ext_suffix:
        raise NativeRuntimeCaptureError("PYTHON_EXTENSION_SUFFIX_MISMATCH")
    libc_name, libc_version = platform.libc_ver()
    abi = {
        "soabi": soabi,
        "multiarch": multiarch,
        "extension_suffix": ext_suffix,
        "cache_tag": sys.implementation.cache_tag,
        "pointer_bits": pointer_bits,
        "byteorder": sys.byteorder,
        "libc_name": libc_name,
        "libc_version": libc_version,
        "platform_tag": sysconfig.get_platform(),
    }
    runtime = {
        "databricks_runtime_environment": dbr,
        "system": platform.system(),
        "machine": platform.machine(),
        "python_implementation": platform.python_implementation(),
        "python_version": version,
        "python_executable": str(Path(sys.executable).resolve()),
        "unobserved_target_paths": list(profile.UNOBSERVED_TARGET_PATHS),
    }
    return runtime, abi


def _installed_distributions() -> Tuple[Dict[str, object], Dict[str, Path]]:
    entries = []
    roots: Dict[str, Path] = {}
    seen = set()
    distributions = list(importlib_metadata.distributions())
    if not distributions or len(distributions) > MAX_DISTRIBUTIONS:
        raise NativeRuntimeCaptureError("INSTALLED_DISTRIBUTION_COUNT_INVALID")
    for distribution in distributions:
        raw_name = distribution.metadata.get("Name")
        version = distribution.version
        if type(raw_name) is not str or not raw_name or type(version) is not str or not version:
            raise NativeRuntimeCaptureError("INSTALLED_DISTRIBUTION_METADATA_INVALID")
        name = _normalize_distribution_name(raw_name)
        if name in seen:
            raise NativeRuntimeCaptureError("INSTALLED_DISTRIBUTION_DUPLICATE:" + name)
        seen.add(name)
        try:
            root = Path(distribution.locate_file("")).resolve(strict=True)
        except OSError as error:
            raise NativeRuntimeCaptureError(
                "INSTALLED_DISTRIBUTION_ROOT_UNAVAILABLE:" + name
            ) from error
        entries.append(
            {"name": name, "version": version, "metadata_root": str(root)}
        )
        roots[name] = root
    entries.sort(key=lambda item: item["name"])
    installed = {item["name"]: item["version"] for item in entries}
    for name, expected in profile.EXPECTED_DISTRIBUTIONS.items():
        if installed.get(name) != expected:
            raise NativeRuntimeCaptureError("INSTALLED_VERSION_MISMATCH:" + name)
    result = {
        "entries": entries,
        "metadata_observation_sha256": _collection_sha256(entries),
        "payload_closure_verified": False,
    }
    return result, roots


def _module_origins(distribution_roots: Mapping[str, Path]) -> Dict[str, object]:
    entries = []
    for distribution_name, module_name in profile.EXPECTED_MODULES.items():
        root = distribution_roots.get(distribution_name)
        if root is None:
            raise NativeRuntimeCaptureError("MODULE_DISTRIBUTION_ROOT_MISSING:" + module_name)
        spec = importlib_util.find_spec(module_name)
        if spec is None or type(spec.origin) is not str or spec.origin in ("built-in", "frozen"):
            raise NativeRuntimeCaptureError("MODULE_ORIGIN_UNAVAILABLE:" + module_name)
        origin = Path(spec.origin)
        raw = _read_stable_regular_file(origin, MAX_MODULE_BYTES, "MODULE_" + module_name)
        resolved = origin.resolve(strict=True)
        entries.append(
            {
                "distribution": distribution_name,
                "module": module_name,
                "origin": str(resolved),
                "origin_sha256": _sha256(raw),
                "origin_size_bytes": len(raw),
                "distribution_metadata_root_observation": str(root),
                "distribution_ownership_verified": False,
            }
        )
    entries.sort(key=lambda item: item["module"])
    return {
        "entries": entries,
        "origin_observation_sha256": _collection_sha256(entries),
        "distribution_ownership_verified": False,
    }


def _safety_boundary() -> Dict[str, object]:
    return {
        "capture_kind": "DATA_FREE_NATIVE_RUNTIME_OBSERVATION_ONLY",
        "network_or_contact_executed": False,
        "study_or_test_data_accessed": False,
        "calibration_executed": False,
        "training_or_inference_executed": False,
        "scientific_execution_performed": False,
        "field_or_blocker_closure_authorized": False,
        "b08_closure_authorized": False,
        "tracker_or_timetable_edit_authorized": False,
        "independent_review_required": True,
    }


def _build_receipt(
    project_root: Path,
    source_revision: str,
    source_manifest_sha256: str,
) -> Dict[str, object]:
    _validate_source_literals(source_revision, source_manifest_sha256)
    profile_value, profile_raw = _load_profile(project_root)
    lock_path = project_root / profile.F152_LOCK_PATH
    lock_raw = _read_stable_regular_file(lock_path, MAX_LOCK_BYTES, "F152_LOCK")
    lock_entries = _parse_lock(lock_raw)
    environment = _f153_environment()
    runtime, abi = _runtime_identity()
    distributions, roots = _installed_distributions()
    origins = _module_origins(roots)

    receipt: Dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "receipt_payload_sha256": "0" * 64,
        "profile_binding": {
            "path": profile.PROFILE_PATH,
            "profile_id": profile_value["profile_id"],
            "record_sha256": profile_value["record_sha256"],
            "file_sha256": _sha256(profile_raw),
            "lifecycle_state": profile_value["lifecycle_state"],
        },
        "f152_lock_observation": {
            "path": profile.F152_LOCK_PATH,
            "sha256": _sha256(lock_raw),
            "size_bytes": len(lock_raw),
            "requirement_count": len(lock_entries),
            "requirements": list(lock_entries),
            "complete_transitive_lock_verified_by_capture": False,
            "artifact_closure_verified_by_capture": False,
            "all_requirements_exactly_pinned": True,
            "all_declared_requirements_sha256_hashed": True,
        },
        "source_binding": {
            "revision": source_revision,
            "manifest_sha256": source_manifest_sha256,
            "declaration_externally_authenticated": False,
        },
        "native_runtime": runtime,
        "python_abi": {
            "observation": abi,
            "observation_sha256": _collection_sha256(abi),
        },
        "f153_controls": _f153_controls(environment),
        "installed_distributions": distributions,
        "module_origins": origins,
        "safety_boundary": _safety_boundary(),
        "decision": "CAPTURE_WRITTEN_REQUIRES_INDEPENDENT_REVIEW_NO_AUTHORITY",
    }
    unsigned = dict(receipt)
    unsigned.pop("receipt_payload_sha256")
    receipt["receipt_payload_sha256"] = _sha256(
        RECEIPT_DOMAIN + _canonical_bytes(unsigned)
    )
    return receipt


def _validate_requirement_observations(value: object) -> Tuple[dict, ...]:
    if type(value) is not list or not value:
        raise NativeRuntimeCaptureError("RECEIPT_REQUIREMENTS_INVALID")
    result = []
    seen = set()
    for item in value:
        entry = _exact_object(item, _REQUIREMENT_KEYS, "RECEIPT_REQUIREMENT")
        name = _nonempty_ascii(entry["name"], "RECEIPT_REQUIREMENT_NAME", 256)
        if _normalize_distribution_name(name) != name or name in seen:
            raise NativeRuntimeCaptureError("RECEIPT_REQUIREMENT_NAME_INVALID")
        seen.add(name)
        version = _nonempty_ascii(
            entry["version"], "RECEIPT_REQUIREMENT_VERSION", 256
        )
        count = entry["sha256_hash_count"]
        if type(count) is not int or count <= 0:
            raise NativeRuntimeCaptureError("RECEIPT_REQUIREMENT_HASH_COUNT_INVALID")
        result.append({"name": name, "version": version, "sha256_hash_count": count})
    versions = {entry["name"]: entry["version"] for entry in result}
    for name, expected in profile.EXPECTED_DISTRIBUTIONS.items():
        if versions.get(name) != expected:
            raise NativeRuntimeCaptureError(
                "RECEIPT_EXPECTED_REQUIREMENT_VERSION_MISMATCH:" + name
            )
    return tuple(result)


def _validate_runtime_observation(value: object) -> Dict[str, object]:
    item = _exact_object(value, _RUNTIME_KEYS, "RECEIPT_NATIVE_RUNTIME")
    dbr = _nonempty_ascii(
        item["databricks_runtime_environment"], "RECEIPT_DBR_VERSION", 256
    )
    if _DBR_VERSION.fullmatch(dbr) is None:
        raise NativeRuntimeCaptureError("RECEIPT_DBR_VERSION_INVALID")
    if item["system"] != "Linux" or item["machine"].casefold() != "x86_64":
        raise NativeRuntimeCaptureError("RECEIPT_PLATFORM_INVALID")
    if (
        item["python_implementation"] != "CPython"
        or item["python_version"] != "3.12.3"
    ):
        raise NativeRuntimeCaptureError("RECEIPT_PYTHON_RUNTIME_INVALID")
    executable = _nonempty_ascii(
        item["python_executable"], "RECEIPT_PYTHON_EXECUTABLE", 8192
    )
    if not Path(executable).is_absolute():
        raise NativeRuntimeCaptureError("RECEIPT_PYTHON_EXECUTABLE_INVALID")
    if item["unobserved_target_paths"] != list(profile.UNOBSERVED_TARGET_PATHS):
        raise NativeRuntimeCaptureError("RECEIPT_UNOBSERVED_TARGET_ROSTER_INVALID")
    return dict(item)


def _validate_abi_observation(value: object) -> Dict[str, object]:
    wrapper = _exact_object(
        value, frozenset({"observation", "observation_sha256"}), "RECEIPT_ABI"
    )
    observation = _exact_object(wrapper["observation"], _ABI_KEYS, "RECEIPT_ABI_BODY")
    for key in (
        "soabi",
        "multiarch",
        "extension_suffix",
        "cache_tag",
        "libc_name",
        "libc_version",
        "platform_tag",
    ):
        _nonempty_ascii(observation[key], "RECEIPT_ABI_" + key.upper(), 4096)
    if not observation["soabi"].startswith("cpython-312-"):
        raise NativeRuntimeCaptureError("RECEIPT_ABI_SOABI_INVALID")
    if observation["multiarch"] != "x86_64-linux-gnu":
        raise NativeRuntimeCaptureError("RECEIPT_ABI_MULTIARCH_INVALID")
    if "cpython-312" not in observation["extension_suffix"]:
        raise NativeRuntimeCaptureError("RECEIPT_ABI_EXTENSION_SUFFIX_INVALID")
    if observation["cache_tag"] != "cpython-312":
        raise NativeRuntimeCaptureError("RECEIPT_ABI_CACHE_TAG_INVALID")
    if observation["pointer_bits"] != 64 or type(observation["pointer_bits"]) is not int:
        raise NativeRuntimeCaptureError("RECEIPT_ABI_POINTER_BITS_INVALID")
    if observation["byteorder"] != "little":
        raise NativeRuntimeCaptureError("RECEIPT_ABI_BYTEORDER_INVALID")
    digest = _require_sha256(wrapper["observation_sha256"], "RECEIPT_ABI_SHA256")
    if digest != _collection_sha256(observation):
        raise NativeRuntimeCaptureError("RECEIPT_ABI_SHA256_MISMATCH")
    return dict(wrapper)


def _validate_distribution_observation(value: object) -> Dict[str, object]:
    wrapper = _exact_object(
        value, _DISTRIBUTION_OBSERVATION_KEYS, "RECEIPT_DISTRIBUTIONS"
    )
    if wrapper["payload_closure_verified"] is not False:
        raise NativeRuntimeCaptureError("RECEIPT_PAYLOAD_CLOSURE_OVERCLAIM")
    entries = wrapper["entries"]
    if type(entries) is not list or not entries or len(entries) > MAX_DISTRIBUTIONS:
        raise NativeRuntimeCaptureError("RECEIPT_DISTRIBUTION_ENTRIES_INVALID")
    seen = set()
    previous = None
    normalized = []
    for value_entry in entries:
        entry = _exact_object(
            value_entry, _DISTRIBUTION_ENTRY_KEYS, "RECEIPT_DISTRIBUTION_ENTRY"
        )
        name = _nonempty_ascii(entry["name"], "RECEIPT_DISTRIBUTION_NAME", 256)
        if _normalize_distribution_name(name) != name or name in seen:
            raise NativeRuntimeCaptureError("RECEIPT_DISTRIBUTION_NAME_INVALID")
        if previous is not None and name <= previous:
            raise NativeRuntimeCaptureError("RECEIPT_DISTRIBUTION_ORDER_INVALID")
        previous = name
        seen.add(name)
        version = _nonempty_ascii(
            entry["version"], "RECEIPT_DISTRIBUTION_VERSION", 256
        )
        metadata_root = _nonempty_ascii(
            entry["metadata_root"], "RECEIPT_DISTRIBUTION_ROOT", 8192
        )
        if not Path(metadata_root).is_absolute():
            raise NativeRuntimeCaptureError("RECEIPT_DISTRIBUTION_ROOT_INVALID")
        normalized.append(
            {"name": name, "version": version, "metadata_root": metadata_root}
        )
    versions = {entry["name"]: entry["version"] for entry in normalized}
    for name, expected in profile.EXPECTED_DISTRIBUTIONS.items():
        if versions.get(name) != expected:
            raise NativeRuntimeCaptureError(
                "RECEIPT_INSTALLED_VERSION_MISMATCH:" + name
            )
    digest = _require_sha256(
        wrapper["metadata_observation_sha256"],
        "RECEIPT_DISTRIBUTION_OBSERVATION_SHA256",
    )
    if digest != _collection_sha256(normalized):
        raise NativeRuntimeCaptureError(
            "RECEIPT_DISTRIBUTION_OBSERVATION_SHA256_MISMATCH"
        )
    return dict(wrapper)


def _validate_module_origin_observation(value: object) -> Dict[str, object]:
    wrapper = _exact_object(value, _MODULE_OBSERVATION_KEYS, "RECEIPT_MODULES")
    if wrapper["distribution_ownership_verified"] is not False:
        raise NativeRuntimeCaptureError("RECEIPT_MODULE_OWNERSHIP_OVERCLAIM")
    entries = wrapper["entries"]
    if type(entries) is not list or len(entries) != len(profile.EXPECTED_MODULES):
        raise NativeRuntimeCaptureError("RECEIPT_MODULE_ENTRIES_INVALID")
    normalized = []
    previous = None
    for value_entry in entries:
        entry = _exact_object(
            value_entry, _MODULE_ENTRY_KEYS, "RECEIPT_MODULE_ENTRY"
        )
        distribution = _nonempty_ascii(
            entry["distribution"], "RECEIPT_MODULE_DISTRIBUTION", 256
        )
        module = _nonempty_ascii(entry["module"], "RECEIPT_MODULE_NAME", 256)
        if profile.EXPECTED_MODULES.get(distribution) != module:
            raise NativeRuntimeCaptureError("RECEIPT_MODULE_ROSTER_INVALID")
        if previous is not None and module <= previous:
            raise NativeRuntimeCaptureError("RECEIPT_MODULE_ORDER_INVALID")
        previous = module
        origin = _nonempty_ascii(entry["origin"], "RECEIPT_MODULE_ORIGIN", 8192)
        metadata_root = _nonempty_ascii(
            entry["distribution_metadata_root_observation"],
            "RECEIPT_MODULE_METADATA_ROOT",
            8192,
        )
        if not Path(origin).is_absolute() or not Path(metadata_root).is_absolute():
            raise NativeRuntimeCaptureError("RECEIPT_MODULE_PATH_INVALID")
        _require_sha256(entry["origin_sha256"], "RECEIPT_MODULE_ORIGIN_SHA256")
        size = entry["origin_size_bytes"]
        if type(size) is not int or size <= 0 or size > MAX_MODULE_BYTES:
            raise NativeRuntimeCaptureError("RECEIPT_MODULE_ORIGIN_SIZE_INVALID")
        if entry["distribution_ownership_verified"] is not False:
            raise NativeRuntimeCaptureError("RECEIPT_MODULE_OWNERSHIP_OVERCLAIM")
        normalized.append(dict(entry))
    if {entry["module"] for entry in normalized} != set(profile.EXPECTED_MODULES.values()):
        raise NativeRuntimeCaptureError("RECEIPT_MODULE_ROSTER_INVALID")
    digest = _require_sha256(
        wrapper["origin_observation_sha256"], "RECEIPT_MODULE_OBSERVATION_SHA256"
    )
    if digest != _collection_sha256(normalized):
        raise NativeRuntimeCaptureError("RECEIPT_MODULE_OBSERVATION_SHA256_MISMATCH")
    return dict(wrapper)


def _validate_receipt_structure(value: object) -> Dict[str, object]:
    receipt = _exact_object(value, _TOP_KEYS, "RECEIPT")
    digest = _require_sha256(
        receipt["receipt_payload_sha256"], "RECEIPT_DIGEST"
    )
    unsigned = dict(receipt)
    unsigned.pop("receipt_payload_sha256")
    expected = _sha256(RECEIPT_DOMAIN + _canonical_bytes(unsigned))
    if digest != expected:
        raise NativeRuntimeCaptureError("RECEIPT_DIGEST_MISMATCH")
    if receipt["schema_version"] != SCHEMA_VERSION:
        raise NativeRuntimeCaptureError("RECEIPT_SCHEMA_MISMATCH")

    binding = _exact_object(
        receipt["profile_binding"], _PROFILE_BINDING_KEYS, "RECEIPT_PROFILE_BINDING"
    )
    if binding["path"] != profile.PROFILE_PATH or binding["profile_id"] != profile.PROFILE_ID:
        raise NativeRuntimeCaptureError("RECEIPT_PROFILE_IDENTITY_INVALID")
    if binding["lifecycle_state"] != profile.DRAFT_UNRESOLVED_F152_LOCK:
        raise NativeRuntimeCaptureError("RECEIPT_PROFILE_STATE_INVALID")
    _require_sha256(binding["record_sha256"], "RECEIPT_PROFILE_RECORD_SHA256")
    _require_sha256(binding["file_sha256"], "RECEIPT_PROFILE_FILE_SHA256")

    lock = _exact_object(
        receipt["f152_lock_observation"],
        _LOCK_OBSERVATION_KEYS,
        "RECEIPT_F152_LOCK",
    )
    if lock["path"] != profile.F152_LOCK_PATH:
        raise NativeRuntimeCaptureError("RECEIPT_F152_LOCK_PATH_INVALID")
    _require_sha256(lock["sha256"], "RECEIPT_F152_LOCK_SHA256")
    if type(lock["size_bytes"]) is not int or lock["size_bytes"] <= 0:
        raise NativeRuntimeCaptureError("RECEIPT_F152_LOCK_SIZE_INVALID")
    requirements = _validate_requirement_observations(lock["requirements"])
    if type(lock["requirement_count"]) is not int or lock["requirement_count"] != len(
        requirements
    ):
        raise NativeRuntimeCaptureError("RECEIPT_F152_LOCK_COUNT_INVALID")
    if lock["complete_transitive_lock_verified_by_capture"] is not False:
        raise NativeRuntimeCaptureError("RECEIPT_F152_COMPLETENESS_OVERCLAIM")
    if lock["artifact_closure_verified_by_capture"] is not False:
        raise NativeRuntimeCaptureError("RECEIPT_F152_ARTIFACT_CLOSURE_OVERCLAIM")
    if lock["all_requirements_exactly_pinned"] is not True:
        raise NativeRuntimeCaptureError("RECEIPT_F152_EXACT_PIN_CLAIM_INVALID")
    if lock["all_declared_requirements_sha256_hashed"] is not True:
        raise NativeRuntimeCaptureError("RECEIPT_F152_DECLARED_HASH_CLAIM_INVALID")

    source = _exact_object(
        receipt["source_binding"], _SOURCE_BINDING_KEYS, "RECEIPT_SOURCE_BINDING"
    )
    _validate_source_literals(source["revision"], source["manifest_sha256"])
    if source["declaration_externally_authenticated"] is not False:
        raise NativeRuntimeCaptureError("RECEIPT_SOURCE_AUTHENTICATION_OVERCLAIM")

    _validate_runtime_observation(receipt["native_runtime"])
    _validate_abi_observation(receipt["python_abi"])
    controls = _exact_object(
        receipt["f153_controls"], _F153_CONTROL_KEYS, "RECEIPT_F153_CONTROLS"
    )
    if controls != _f153_controls(profile.F153_ENVIRONMENT):
        raise NativeRuntimeCaptureError("RECEIPT_F153_CONTROLS_INVALID")
    _validate_distribution_observation(receipt["installed_distributions"])
    _validate_module_origin_observation(receipt["module_origins"])
    if receipt["safety_boundary"] != _safety_boundary():
        raise NativeRuntimeCaptureError("RECEIPT_SAFETY_BOUNDARY_MISMATCH")
    if receipt["decision"] != (
        "CAPTURE_WRITTEN_REQUIRES_INDEPENDENT_REVIEW_NO_AUTHORITY"
    ):
        raise NativeRuntimeCaptureError("RECEIPT_DECISION_MISMATCH")
    return dict(receipt)


def _write_private_no_clobber(path: Path, raw: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as error:
        raise NativeRuntimeCaptureError("OUTPUT_NO_CLOBBER") from error
    except OSError as error:
        raise NativeRuntimeCaptureError("OUTPUT_CREATE_FAILED") from error
    created_identity = None
    try:
        opened = os.fstat(descriptor)
        _validate_private_receipt_stat(opened, "OUTPUT")
        created_identity = (opened.st_dev, opened.st_ino)
        total = 0
        while total < len(raw):
            written = os.write(descriptor, raw[total:])
            if written <= 0:
                raise NativeRuntimeCaptureError("OUTPUT_SHORT_WRITE")
            total += written
        os.fsync(descriptor)
        final_fd = os.fstat(descriptor)
        _validate_private_receipt_stat(final_fd, "OUTPUT")
        if (final_fd.st_dev, final_fd.st_ino) != created_identity:
            raise NativeRuntimeCaptureError("OUTPUT_IDENTITY_CHANGED")
    except BaseException:
        os.close(descriptor)
        try:
            path.unlink()
        except OSError:
            pass
        raise
    os.close(descriptor)
    try:
        final_path = path.lstat()
    except OSError as error:
        raise NativeRuntimeCaptureError("OUTPUT_DISAPPEARED") from error
    if stat.S_ISLNK(final_path.st_mode):
        raise NativeRuntimeCaptureError("OUTPUT_SYMLINK_FORBIDDEN")
    _validate_private_receipt_stat(final_path, "OUTPUT")
    if (final_path.st_dev, final_path.st_ino) != created_identity:
        raise NativeRuntimeCaptureError("OUTPUT_IDENTITY_CHANGED")
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    try:
        parent_descriptor = os.open(path.parent, directory_flags)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    except OSError as error:
        raise NativeRuntimeCaptureError("OUTPUT_PARENT_FSYNC_FAILED") from error


def capture(
    project_root: str,
    source_revision: str,
    source_manifest_sha256: str,
    output: str,
) -> Dict[str, object]:
    root = _absolute_directory(project_root, "PROJECT_ROOT")
    output_path = _output_path(output)
    receipt = _build_receipt(root, source_revision, source_manifest_sha256)
    _write_private_no_clobber(output_path, _canonical_bytes(receipt) + b"\n")
    return dict(receipt)


def validate_only(
    project_root: str,
    source_revision: str,
    source_manifest_sha256: str,
    receipt_path: str,
) -> Dict[str, object]:
    _validate_source_literals(source_revision, source_manifest_sha256)
    root = _absolute_directory(project_root, "PROJECT_ROOT")
    receipt_file = Path(receipt_path)
    if not receipt_file.is_absolute():
        raise NativeRuntimeCaptureError("RECEIPT_PATH_MUST_BE_ABSOLUTE")
    raw = _read_private_receipt(receipt_file)
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise NativeRuntimeCaptureError("RECEIPT_INVALID_JSON") from error
    if raw != _canonical_bytes(value) + b"\n":
        raise NativeRuntimeCaptureError("RECEIPT_NONCANONICAL")
    receipt = _validate_receipt_structure(value)

    profile_value, profile_raw = _load_profile(root)
    lock_raw = _read_stable_regular_file(
        root / profile.F152_LOCK_PATH, MAX_LOCK_BYTES, "F152_LOCK"
    )
    parsed_lock = _parse_lock(lock_raw)
    binding = receipt["profile_binding"]
    if binding != {
        "path": profile.PROFILE_PATH,
        "profile_id": profile_value["profile_id"],
        "record_sha256": profile_value["record_sha256"],
        "file_sha256": _sha256(profile_raw),
        "lifecycle_state": profile_value["lifecycle_state"],
    }:
        raise NativeRuntimeCaptureError("RECEIPT_PROFILE_BINDING_MISMATCH")
    lock_observation = receipt["f152_lock_observation"]
    expected_lock_observation = {
        "path": profile.F152_LOCK_PATH,
        "sha256": _sha256(lock_raw),
        "size_bytes": len(lock_raw),
        "requirement_count": len(parsed_lock),
        "requirements": list(parsed_lock),
        "complete_transitive_lock_verified_by_capture": False,
        "artifact_closure_verified_by_capture": False,
        "all_requirements_exactly_pinned": True,
        "all_declared_requirements_sha256_hashed": True,
    }
    if lock_observation != expected_lock_observation:
        raise NativeRuntimeCaptureError("RECEIPT_F152_LOCK_BINDING_MISMATCH")
    if receipt["source_binding"] != {
        "revision": source_revision,
        "manifest_sha256": source_manifest_sha256,
        "declaration_externally_authenticated": False,
    }:
        raise NativeRuntimeCaptureError("RECEIPT_SOURCE_BINDING_MISMATCH")
    environment = _f153_environment()
    runtime, abi = _runtime_identity()
    distributions, roots = _installed_distributions()
    origins = _module_origins(roots)
    if receipt["f153_controls"] != _f153_controls(environment):
        raise NativeRuntimeCaptureError("RECEIPT_F153_CURRENT_STATE_MISMATCH")
    if receipt["native_runtime"] != runtime:
        raise NativeRuntimeCaptureError("RECEIPT_RUNTIME_CURRENT_STATE_MISMATCH")
    if receipt["python_abi"] != {
        "observation": abi,
        "observation_sha256": _collection_sha256(abi),
    }:
        raise NativeRuntimeCaptureError("RECEIPT_ABI_CURRENT_STATE_MISMATCH")
    if receipt["installed_distributions"] != distributions:
        raise NativeRuntimeCaptureError(
            "RECEIPT_DISTRIBUTIONS_CURRENT_STATE_MISMATCH"
        )
    if receipt["module_origins"] != origins:
        raise NativeRuntimeCaptureError("RECEIPT_MODULES_CURRENT_STATE_MISMATCH")
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--source-manifest-sha256", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--validate-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.validate_only:
        receipt = validate_only(
            arguments.project_root,
            arguments.source_revision,
            arguments.source_manifest_sha256,
            arguments.output,
        )
    else:
        receipt = capture(
            arguments.project_root,
            arguments.source_revision,
            arguments.source_manifest_sha256,
            arguments.output,
        )
    print(
        json.dumps(
            {
                "decision": receipt["decision"],
                "receipt_payload_sha256": receipt["receipt_payload_sha256"],
                "study_or_test_data_accessed": False,
                "scientific_execution_performed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
