#!/usr/bin/env python3
"""Operator-side Databricks AWS qualification capture.

Run this script on a Databricks AWS classic dedicated cluster before study
data, test data, calibration, training, or outcome access.  The script is
standard-library-only.  It reads only the two explicit local JSON inputs,
optionally accepts an immutable container digest literal, inspects the local
Python runtime and installed distribution metadata, and writes one private
canonical receipt.

It deliberately contains no network, Databricks REST, Spark, DBFS, Unity
Catalog, subprocess, random, or secrets API route.  Structural capture is not
platform authentication, capacity approval, production-runtime selection, or
project closure.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib import metadata as importlib_metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import stat
import struct
import sys
import sysconfig
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


SCHEMA_VERSION = "heterodiff-b08-databricks-aws-qualification-capture-v1"
CAPTURE_KIND = (
    "DATABRICKS_AWS_CLASSIC_DEDICATED_PRE_STUDY_DATA_QUALIFICATION_CAPTURE"
)
RECEIPT_DOMAIN = b"heterodiff/b08/databricks-aws-qualification-capture/v1\0"
INPUT_CONTENT_DOMAIN = b"heterodiff/b08/operator-input-content/v1\0"
MAX_JSON_INPUT_BYTES = 16 * 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_JSON_NODES = 100_000
MAX_STRING_CHARACTERS = 1_048_576
MAX_DISTRIBUTIONS = 20_000

DETERMINISM_ENV_ALLOWLIST = (
    "CUBLAS_WORKSPACE_CONFIG",
    "CUDA_VISIBLE_DEVICES",
    "DATABRICKS_RUNTIME_VERSION",
    "LANG",
    "LC_ALL",
    "MKL_NUM_THREADS",
    "NCCL_ALGO",
    "NCCL_PROTO",
    "NUMEXPR_NUM_THREADS",
    "NVIDIA_TF32_OVERRIDE",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "PYTHONHASHSEED",
    "PYTHONIOENCODING",
    "PYTHONUTF8",
    "TF_CUDNN_DETERMINISTIC",
    "TF_DETERMINISTIC_OPS",
    "TZ",
    "VECLIB_MAXIMUM_THREADS",
)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_CONTAINER_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_RFC3339_UTC = re.compile(
    r"(?:19|20)[0-9]{2}-(?:0[1-9]|1[0-2])-"
    r"(?:0[1-9]|[12][0-9]|3[01])T"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\."
    r"[0-9]{6}Z\Z"
)
_SECRET_KEY = re.compile(
    r"(?:^|_)(?:"
    r"api_key|access_key|authorization|client_secret|connection_string|"
    r"cookie|credential|credentials|oauth_token|password|passwd|private_key|"
    r"sas_token|secret|session_key|token"
    r")(?:_|$)"
)
_COMPACT_SECRET_KEYS = frozenset(
    {
        "accesskey",
        "accesskeyid",
        "apikey",
        "apitoken",
        "authorization",
        "clientsecret",
        "connectionstring",
        "cookie",
        "credential",
        "credentials",
        "oauthToken".casefold(),
        "password",
        "passwd",
        "privatekey",
        "sastoken",
        "secret",
        "sessionkey",
        "token",
    }
)
_PRIVATE_IDENTITY_KEYS = frozenset(
    {
        "creatorusername",
        "singleusername",
        "useremail",
        "username",
    }
)
_SECRET_VALUE_PATTERNS = (
    ("PRIVATE_KEY_BLOCK", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("BEARER_AUTHORIZATION", re.compile(r"(?i)\bbearer[ \t]+[A-Za-z0-9._~+/=-]{8,}")),
    ("BASIC_AUTHORIZATION", re.compile(r"(?i)\bbasic[ \t]+[A-Za-z0-9+/=]{8,}")),
    ("AWS_ACCESS_KEY_ID", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("DATABRICKS_PERSONAL_ACCESS_TOKEN", re.compile(r"\bdapi[a-fA-F0-9]{24,}\b")),
    ("JWT_LIKE_VALUE", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("GITHUB_TOKEN", re.compile(r"\bgh[opsu]_[A-Za-z0-9]{20,}\b")),
    ("SLACK_TOKEN", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b")),
    ("OPENAI_STYLE_TOKEN", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    (
        "SECRET_ASSIGNMENT",
        re.compile(
            r"(?i)(?:password|passwd|access[_-]?key|api[_-]?key|"
            r"client[_-]?secret|token|authorization)[ \t]*[:=][ \t]*[^ ,;]{4,}"
        ),
    ),
    (
        "SECRET_REFERENCE",
        re.compile(r"(?i)(?:dbutils\.secrets|get_secret|\{\{secrets?/|secret://)"),
    ),
    (
        "URL_USERINFO",
        re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^/@\s:]+:[^/@\s]+@"),
    ),
    (
        "URL_SECRET_QUERY",
        re.compile(
            r"(?i)[?&](?:sig|signature|token|password|passwd|key|credential)="
        ),
    ),
)


class CaptureError(RuntimeError):
    """Fail-closed operator input, custody, or receipt error."""


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
        raise CaptureError("NONCANONICAL_JSON_VALUE") from error


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _content_sha256(value: object) -> str:
    return _sha256(INPUT_CONTENT_DOMAIN + _canonical_bytes(value))


def _normalize_key_for_scan(value: str) -> str:
    camel_split = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    acronym_split = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", camel_split)
    return re.sub(r"[^a-z0-9]+", "_", acronym_split.casefold()).strip("_")


def _scan_string_value(value: str, location: str) -> None:
    if len(value) > MAX_STRING_CHARACTERS:
        raise CaptureError("STRING_TOO_LONG_AT:" + location)
    if any(ord(character) < 0x20 and character not in "\t\n\r" for character in value):
        raise CaptureError("CONTROL_CHARACTER_AT:" + location)
    for label, pattern in _SECRET_VALUE_PATTERNS:
        if pattern.search(value) is not None:
            raise CaptureError("SENSITIVE_VALUE_REJECTED:" + label + ":" + location)


def _validate_json_tree(value: object, label: str) -> None:
    nodes = 0

    def visit(item: object, location: str, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > MAX_JSON_NODES:
            raise CaptureError("JSON_NODE_LIMIT_EXCEEDED:" + label)
        if depth > MAX_JSON_DEPTH:
            raise CaptureError("JSON_DEPTH_LIMIT_EXCEEDED:" + label)
        if item is None or type(item) is bool:
            return
        if type(item) is int:
            if item.bit_length() > 4096:
                raise CaptureError("JSON_INTEGER_TOO_WIDE_AT:" + location)
            return
        if type(item) is float:
            if not math.isfinite(item):
                raise CaptureError("NONFINITE_NUMBER_AT:" + location)
            return
        if type(item) is str:
            _scan_string_value(item, location)
            return
        if type(item) is list:
            for ordinal, child in enumerate(item):
                visit(child, location + "[" + str(ordinal) + "]", depth + 1)
            return
        if type(item) is dict:
            for key, child in item.items():
                if type(key) is not str or not key:
                    raise CaptureError("INVALID_JSON_KEY_AT:" + location)
                normalized = _normalize_key_for_scan(key)
                compact = normalized.replace("_", "")
                if (
                    _SECRET_KEY.search(normalized) is not None
                    or compact in _COMPACT_SECRET_KEYS
                    or compact in _PRIVATE_IDENTITY_KEYS
                ):
                    raise CaptureError("SENSITIVE_KEY_REJECTED_AT:" + location + "." + key)
                _scan_string_value(key, location + ".<key>")
                visit(child, location + "." + key, depth + 1)
            return
        raise CaptureError("UNSUPPORTED_JSON_TYPE_AT:" + location)

    visit(value, label, 0)


def _duplicate_rejecting_hook(
    pairs: Iterable[Tuple[str, Any]],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CaptureError("DUPLICATE_JSON_KEY:" + key)
        result[key] = value
    return result


def _parse_canonical_json(raw: bytes, label: str) -> Dict[str, Any]:
    if not raw or len(raw) > MAX_JSON_INPUT_BYTES:
        raise CaptureError(label + "_BYTE_COUNT_OUT_OF_RANGE")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise CaptureError(label + "_MUST_BE_CANONICAL_ASCII_JSON") from error
    if not text.endswith("\n") or text.endswith("\n\n"):
        raise CaptureError(label + "_MUST_HAVE_ONE_TERMINAL_LF")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_rejecting_hook,
            parse_constant=lambda token: (_ for _ in ()).throw(
                CaptureError(label + "_FORBIDDEN_JSON_CONSTANT:" + token)
            ),
        )
    except json.JSONDecodeError as error:
        raise CaptureError(label + "_MALFORMED_JSON") from error
    if type(value) is not dict or not value:
        raise CaptureError(label + "_ROOT_MUST_BE_NONEMPTY_OBJECT")
    _validate_json_tree(value, label)
    if raw != _canonical_bytes(value) + b"\n":
        raise CaptureError(label + "_NONCANONICAL_JSON_BYTES")
    return value


def _absolute_local_path(raw_path: str, label: str) -> Path:
    if type(raw_path) is not str or not raw_path or "\x00" in raw_path:
        raise CaptureError(label + "_PATH_INVALID")
    if raw_path.startswith("~") or raw_path.startswith("dbfs:"):
        raise CaptureError(label + "_PATH_SCHEME_FORBIDDEN")
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    normalized = Path(os.path.abspath(os.fspath(path)))
    text = os.fspath(normalized)
    if text == "/dbfs" or text.startswith("/dbfs/"):
        raise CaptureError(label + "_DBFS_PATH_FORBIDDEN")
    if text == "/Volumes" or text.startswith("/Volumes/"):
        raise CaptureError(label + "_UNITY_CATALOG_VOLUME_PATH_FORBIDDEN")
    if text == "/Workspace" or text.startswith("/Workspace/"):
        raise CaptureError(label + "_WORKSPACE_FUSE_PATH_FORBIDDEN")
    return normalized


def _open_physical_parent(path: Path, label: str) -> Tuple[int, str]:
    if not path.is_absolute() or path.name in ("", ".", ".."):
        raise CaptureError(label + "_PATH_INVALID")
    parts = path.parts
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        current = os.open(os.sep, flags)
    except OSError as error:
        raise CaptureError(label + "_ROOT_OPEN_FAILED") from error
    try:
        for part in parts[1:-1]:
            if part in ("", ".", ".."):
                raise CaptureError(label + "_UNSAFE_PARENT_COMPONENT")
            try:
                following = os.open(part, flags, dir_fd=current)
            except OSError as error:
                raise CaptureError(label + "_PARENT_OPEN_FAILED") from error
            opened = os.fstat(following)
            if not stat.S_ISDIR(opened.st_mode):
                os.close(following)
                raise CaptureError(label + "_PARENT_NOT_DIRECTORY")
            os.close(current)
            current = following
        # Transfer the final descriptor to the caller.  Setting ``current``
        # to -1 makes ownership explicit and prevents the finally block from
        # closing the descriptor that is being returned.
        parent_fd = current
        current = -1
        return parent_fd, parts[-1]
    finally:
        if current >= 0:
            os.close(current)


def _read_stable_regular_file(
    raw_path: str,
    label: str,
    maximum_bytes: int,
    require_mode_0600: bool = False,
) -> Tuple[bytes, Dict[str, Any]]:
    path = _absolute_local_path(raw_path, label)
    parent_fd, name = _open_physical_parent(path, label)
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(name, flags, dir_fd=parent_fd)
        except OSError as error:
            raise CaptureError(label + "_LEAF_OPEN_FAILED") from error
        try:
            before = os.fstat(descriptor)
            mode = stat.S_IMODE(before.st_mode)
            if not stat.S_ISREG(before.st_mode):
                raise CaptureError(label + "_NOT_REGULAR_FILE")
            if before.st_nlink != 1:
                raise CaptureError(label + "_LINK_COUNT_NOT_ONE")
            if require_mode_0600:
                if mode != 0o600:
                    raise CaptureError(label + "_MODE_NOT_0600")
            elif mode & 0o022:
                raise CaptureError(label + "_GROUP_OR_WORLD_WRITABLE")
            if before.st_size <= 0 or before.st_size > maximum_bytes:
                raise CaptureError(label + "_BYTE_COUNT_OUT_OF_RANGE")
            chunks = []
            remaining = before.st_size
            while remaining:
                chunk = os.read(descriptor, min(1 << 20, remaining))
                if not chunk:
                    raise CaptureError(label + "_TRUNCATED_DURING_READ")
                chunks.append(chunk)
                remaining -= len(chunk)
            if os.read(descriptor, 1):
                raise CaptureError(label + "_GREW_DURING_READ")
            raw = b"".join(chunks)
            after = os.fstat(descriptor)
            identity_before = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
            )
            identity_after = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            )
            if identity_before != identity_after:
                raise CaptureError(label + "_IDENTITY_CHANGED_DURING_READ")
        finally:
            os.close(descriptor)
    finally:
        os.close(parent_fd)
    return raw, {
        "source_label": label,
        "source_basename": path.name,
        "source_path_recorded": False,
        "raw_byte_count": len(raw),
        "raw_sha256": _sha256(raw),
        "file_mode_octal": format(mode, "04o"),
        "link_count": 1,
    }


def _write_exclusive_private_file(raw_path: str, raw: bytes) -> Dict[str, Any]:
    path = _absolute_local_path(raw_path, "OUTPUT")
    parent_fd, name = _open_physical_parent(path, "OUTPUT")
    descriptor = -1
    try:
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            descriptor = os.open(name, flags, 0o600, dir_fd=parent_fd)
        except FileExistsError as error:
            raise CaptureError("OUTPUT_ALREADY_EXISTS_NO_CLOBBER") from error
        except OSError as error:
            raise CaptureError("OUTPUT_EXCLUSIVE_CREATE_FAILED") from error
        os.fchmod(descriptor, 0o600)
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            if written <= 0:
                raise CaptureError("OUTPUT_WRITE_FAILED")
            offset += written
        os.fsync(descriptor)
        observed = os.fstat(descriptor)
        if (
            not stat.S_ISREG(observed.st_mode)
            or stat.S_IMODE(observed.st_mode) != 0o600
            or observed.st_nlink != 1
            or observed.st_size != len(raw)
        ):
            raise CaptureError("OUTPUT_POSTWRITE_CUSTODY_MISMATCH")
        os.close(descriptor)
        descriptor = -1
        os.fsync(parent_fd)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent_fd)
    return {
        "output_basename": path.name,
        "output_path_recorded": False,
        "raw_byte_count": len(raw),
        "raw_sha256": _sha256(raw),
        "file_mode_octal": "0600",
        "exclusive_no_clobber_create": True,
    }


def _input_capture(
    raw_path: str,
    label: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    raw, custody = _read_stable_regular_file(
        raw_path, label, MAX_JSON_INPUT_BYTES
    )
    value = _parse_canonical_json(raw, label)
    return value, {
        **custody,
        "canonical_json_verified": True,
        "canonical_content_sha256": _content_sha256(value),
        "content": value,
    }


def _cluster_spec_candidate(
    cluster_json: Mapping[str, Any],
) -> Tuple[str, Mapping[str, Any]]:
    candidates = [("$", cluster_json)]
    for key in ("cluster_spec", "spec"):
        nested = cluster_json.get(key)
        if type(nested) is dict:
            candidates.append(("$." + key, nested))
    for location, candidate in candidates:
        if (
            type(candidate.get("aws_attributes")) is dict
            and type(candidate.get("spark_version")) is str
            and type(candidate.get("node_type_id")) is str
            and type(candidate.get("data_security_mode")) is str
        ):
            return location, candidate
    raise CaptureError(
        "CLUSTER_JSON_LACKS_AWS_CLASSIC_DEDICATED_STRUCTURAL_SIGNALS"
    )


def _cluster_target_signals(cluster_json: Mapping[str, Any]) -> Dict[str, Any]:
    location, candidate = _cluster_spec_candidate(cluster_json)
    mode = candidate["data_security_mode"]
    if mode not in ("SINGLE_USER", "DEDICATED"):
        raise CaptureError("CLUSTER_DATA_SECURITY_MODE_NOT_DEDICATED")
    spark_version = candidate["spark_version"]
    node_type = candidate["node_type_id"]
    driver_node_type = candidate.get("driver_node_type_id", node_type)
    for label, value in (
        ("spark_version", spark_version),
        ("node_type_id", node_type),
        ("driver_node_type_id", driver_node_type),
    ):
        if type(value) is not str or not value or len(value) > 512:
            raise CaptureError("CLUSTER_" + label.upper() + "_INVALID")
        _scan_string_value(value, "CLUSTER_SIGNALS." + label)
    return {
        "cluster_spec_location": location,
        "aws_attributes_present": True,
        "classic_compute_signals_present": True,
        "dedicated_access_mode": mode,
        "spark_version": spark_version,
        "node_type_id": node_type,
        "driver_node_type_id": driver_node_type,
        "platform_authenticated_by_capture": False,
        "structural_interpretation": (
            "CONSISTENT_WITH_DATABRICKS_AWS_CLASSIC_DEDICATED_INPUT_"
            "REQUIRES_LATER_ADMIN_NORMALIZATION"
        ),
    }


def _container_capture(value: str | None) -> Dict[str, Any]:
    if value is None:
        return {
            "provided": False,
            "digest": None,
            "text_byte_count": 0,
            "text_sha256": None,
        }
    if type(value) is not str or _CONTAINER_DIGEST.fullmatch(value) is None:
        raise CaptureError("CONTAINER_DIGEST_MUST_BE_SHA256_COLON_LOWERCASE_HEX")
    _scan_string_value(value, "CONTAINER_DIGEST")
    raw = value.encode("ascii")
    return {
        "provided": True,
        "digest": value,
        "text_byte_count": len(raw),
        "text_sha256": _sha256(raw),
    }


def _local_runtime() -> Dict[str, Any]:
    uname = os.uname() if hasattr(os, "uname") else None
    implementation_version = sys.implementation.version
    runtime = {
        "python": {
            "implementation": platform.python_implementation(),
            "implementation_name": sys.implementation.name,
            "implementation_version": {
                "major": implementation_version.major,
                "minor": implementation_version.minor,
                "micro": implementation_version.micro,
                "releaselevel": implementation_version.releaselevel,
                "serial": implementation_version.serial,
            },
            "language_version": platform.python_version(),
            "language_version_info": list(sys.version_info[:5]),
            "compiler": platform.python_compiler(),
            "build": list(platform.python_build()),
            "cache_tag": sys.implementation.cache_tag,
            "executable_path_recorded": False,
            "byteorder": sys.byteorder,
            "pointer_width_bits": struct.calcsize("P") * 8,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "sysconfig_platform": sysconfig.get_platform(),
            "os_name": os.name,
            "uname_sysname": uname.sysname if uname is not None else None,
            "uname_release": uname.release if uname is not None else None,
            "uname_version": uname.version if uname is not None else None,
            "uname_machine": uname.machine if uname is not None else None,
            "hostname_or_nodename_recorded": False,
            "logical_cpu_count": os.cpu_count(),
        },
    }
    _validate_json_tree(runtime, "LOCAL_RUNTIME")
    return runtime


def _installed_distributions() -> list[Dict[str, str]]:
    rows = []
    try:
        distributions = importlib_metadata.distributions()
        for distribution in distributions:
            name = distribution.metadata.get("Name")
            version = distribution.version
            if type(name) is not str or not name.strip():
                raise CaptureError("INSTALLED_DISTRIBUTION_NAME_MISSING")
            if type(version) is not str or not version.strip():
                raise CaptureError("INSTALLED_DISTRIBUTION_VERSION_MISSING")
            name = name.strip()
            version = version.strip()
            if len(name) > 512 or len(version) > 512:
                raise CaptureError("INSTALLED_DISTRIBUTION_VALUE_TOO_LONG")
            _scan_string_value(name, "INSTALLED_DISTRIBUTION.NAME")
            _scan_string_value(version, "INSTALLED_DISTRIBUTION.VERSION")
            rows.append({"name": name, "version": version})
            if len(rows) > MAX_DISTRIBUTIONS:
                raise CaptureError("INSTALLED_DISTRIBUTION_COUNT_LIMIT_EXCEEDED")
    except importlib_metadata.PackageNotFoundError as error:
        raise CaptureError("INSTALLED_DISTRIBUTION_ENUMERATION_FAILED") from error
    rows.sort(key=lambda row: (row["name"].casefold(), row["name"], row["version"]))
    if len({(row["name"], row["version"]) for row in rows}) != len(rows):
        raise CaptureError("DUPLICATE_INSTALLED_DISTRIBUTION_NAME_VERSION")
    return rows


def _determinism_environment() -> Dict[str, Any]:
    present: Dict[str, str] = {}
    absent = []
    for name in DETERMINISM_ENV_ALLOWLIST:
        if name in os.environ:
            value = os.environ[name]
            _scan_string_value(value, "ENV." + name)
            present[name] = value
        else:
            absent.append(name)
    return {
        "allowlist": list(DETERMINISM_ENV_ALLOWLIST),
        "present": present,
        "absent": absent,
        "nonallowlisted_environment_names_or_values_recorded": False,
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


def _build_receipt(
    cluster_capture: Dict[str, Any],
    reservation_capture: Dict[str, Any],
    container_capture: Dict[str, Any],
    cluster_signals: Dict[str, Any],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "capture_kind": CAPTURE_KIND,
        "capture_time_utc": _utc_now(),
        "capture_time_externally_attested": False,
        "operator_execution_boundary": {
            "intended_platform": "DATABRICKS_AWS_CLASSIC_DEDICATED",
            "required_phase": "BEFORE_STUDY_DATA_TEST_DATA_CALIBRATION_TRAINING_OR_OUTCOMES",
            "operator_must_run_on_target_driver": True,
            "platform_identity_authenticated": False,
            "admin_reservation_authenticated": False,
            "later_normalization_and_external_review_required": True,
        },
        "input_captures": {
            "exported_sanitized_cluster_json": cluster_capture,
            "admin_storage_reservation_json": reservation_capture,
            "immutable_container_digest_text": container_capture,
        },
        "cluster_target_signals": cluster_signals,
        "local_runtime": _local_runtime(),
        "installed_distributions": _installed_distributions(),
        "determinism_environment": _determinism_environment(),
        "safety_boundary": {
            "network_accessed": False,
            "databricks_rest_called": False,
            "subprocess_started": False,
            "random_or_secrets_api_used": False,
            "spark_session_or_context_accessed": False,
            "spark_table_enumerated": False,
            "dbfs_enumerated": False,
            "unity_catalog_enumerated": False,
            "study_or_test_data_accessed": False,
            "calibration_training_or_outcome_accessed": False,
            "input_paths_recorded": False,
        },
        "qualification_nonclaims": {
            "capture_is_platform_authentication": False,
            "capture_is_storage_reservation_approval": False,
            "capture_selects_production_hardware_or_runtime": False,
            "capture_authorizes_data_or_scientific_execution": False,
            "capture_closes_any_field": False,
            "capture_closes_B08": False,
            "capture_closes_any_blocker_or_timetable_task": False,
            "tracker_or_ledger_edit_authorized": False,
        },
    }
    _validate_json_tree(payload, "RECEIPT_PAYLOAD")
    payload["receipt_payload_sha256"] = _sha256(
        RECEIPT_DOMAIN + _canonical_bytes(payload)
    )
    return payload


def _require_exact_keys(
    value: object,
    expected: Sequence[str],
    label: str,
) -> Mapping[str, Any]:
    if type(value) is not dict or set(value) != set(expected):
        raise CaptureError(label + "_KEY_ROSTER_MISMATCH")
    return value


def _validate_input_capture(
    value: object,
    expected: Mapping[str, Any],
    label: str,
) -> None:
    row = _require_exact_keys(
        value,
        (
            "source_label",
            "source_basename",
            "source_path_recorded",
            "raw_byte_count",
            "raw_sha256",
            "file_mode_octal",
            "link_count",
            "canonical_json_verified",
            "canonical_content_sha256",
            "content",
        ),
        label,
    )
    for key in (
        "source_label",
        "source_basename",
        "source_path_recorded",
        "raw_byte_count",
        "raw_sha256",
        "file_mode_octal",
        "link_count",
        "canonical_json_verified",
        "canonical_content_sha256",
        "content",
    ):
        if row[key] != expected[key] or type(row[key]) is not type(expected[key]):
            raise CaptureError(label + "_INPUT_BINDING_MISMATCH:" + key)


def _validate_container_capture(value: object, expected: Mapping[str, Any]) -> None:
    row = _require_exact_keys(
        value,
        ("provided", "digest", "text_byte_count", "text_sha256"),
        "CONTAINER_CAPTURE",
    )
    if dict(row) != dict(expected):
        raise CaptureError("CONTAINER_CAPTURE_BINDING_MISMATCH")


def _validate_receipt_structure(
    receipt: Dict[str, Any],
    cluster_capture: Dict[str, Any],
    reservation_capture: Dict[str, Any],
    container_capture: Dict[str, Any],
) -> Dict[str, Any]:
    top = _require_exact_keys(
        receipt,
        (
            "schema_version",
            "capture_kind",
            "capture_time_utc",
            "capture_time_externally_attested",
            "operator_execution_boundary",
            "input_captures",
            "cluster_target_signals",
            "local_runtime",
            "installed_distributions",
            "determinism_environment",
            "safety_boundary",
            "qualification_nonclaims",
            "receipt_payload_sha256",
        ),
        "RECEIPT",
    )
    if top["schema_version"] != SCHEMA_VERSION:
        raise CaptureError("RECEIPT_SCHEMA_VERSION_MISMATCH")
    if top["capture_kind"] != CAPTURE_KIND:
        raise CaptureError("RECEIPT_CAPTURE_KIND_MISMATCH")
    if (
        type(top["capture_time_utc"]) is not str
        or _RFC3339_UTC.fullmatch(top["capture_time_utc"]) is None
    ):
        raise CaptureError("RECEIPT_CAPTURE_TIME_INVALID")
    if top["capture_time_externally_attested"] is not False:
        raise CaptureError("RECEIPT_TIME_ATTESTATION_OVERCLAIM")

    inputs = _require_exact_keys(
        top["input_captures"],
        (
            "exported_sanitized_cluster_json",
            "admin_storage_reservation_json",
            "immutable_container_digest_text",
        ),
        "INPUT_CAPTURES",
    )
    _validate_input_capture(
        inputs["exported_sanitized_cluster_json"],
        cluster_capture,
        "CLUSTER_CAPTURE",
    )
    _validate_input_capture(
        inputs["admin_storage_reservation_json"],
        reservation_capture,
        "STORAGE_RESERVATION_CAPTURE",
    )
    _validate_container_capture(
        inputs["immutable_container_digest_text"], container_capture
    )

    expected_signals = _cluster_target_signals(cluster_capture["content"])
    if top["cluster_target_signals"] != expected_signals:
        raise CaptureError("CLUSTER_TARGET_SIGNALS_MISMATCH")
    safety = _require_exact_keys(
        top["safety_boundary"],
        (
            "network_accessed",
            "databricks_rest_called",
            "subprocess_started",
            "random_or_secrets_api_used",
            "spark_session_or_context_accessed",
            "spark_table_enumerated",
            "dbfs_enumerated",
            "unity_catalog_enumerated",
            "study_or_test_data_accessed",
            "calibration_training_or_outcome_accessed",
            "input_paths_recorded",
        ),
        "SAFETY_BOUNDARY",
    )
    if set(safety.values()) != {False}:
        raise CaptureError("SAFETY_BOUNDARY_MUST_BE_ALL_FALSE")
    nonclaims = _require_exact_keys(
        top["qualification_nonclaims"],
        (
            "capture_is_platform_authentication",
            "capture_is_storage_reservation_approval",
            "capture_selects_production_hardware_or_runtime",
            "capture_authorizes_data_or_scientific_execution",
            "capture_closes_any_field",
            "capture_closes_B08",
            "capture_closes_any_blocker_or_timetable_task",
            "tracker_or_ledger_edit_authorized",
        ),
        "QUALIFICATION_NONCLAIMS",
    )
    if set(nonclaims.values()) != {False}:
        raise CaptureError("QUALIFICATION_NONCLAIMS_MUST_BE_ALL_FALSE")
    boundary = _require_exact_keys(
        top["operator_execution_boundary"],
        (
            "intended_platform",
            "required_phase",
            "operator_must_run_on_target_driver",
            "platform_identity_authenticated",
            "admin_reservation_authenticated",
            "later_normalization_and_external_review_required",
        ),
        "OPERATOR_EXECUTION_BOUNDARY",
    )
    if (
        type(boundary) is not dict
        or boundary.get("intended_platform")
        != "DATABRICKS_AWS_CLASSIC_DEDICATED"
        or boundary.get("required_phase")
        != "BEFORE_STUDY_DATA_TEST_DATA_CALIBRATION_TRAINING_OR_OUTCOMES"
        or boundary.get("operator_must_run_on_target_driver") is not True
        or boundary.get("platform_identity_authenticated") is not False
        or boundary.get("admin_reservation_authenticated") is not False
        or boundary.get("later_normalization_and_external_review_required")
        is not True
    ):
        raise CaptureError("OPERATOR_EXECUTION_BOUNDARY_MISMATCH")

    distributions = top["installed_distributions"]
    if type(distributions) is not list or len(distributions) > MAX_DISTRIBUTIONS:
        raise CaptureError("INSTALLED_DISTRIBUTIONS_INVALID")
    observed_rows = []
    for row in distributions:
        item = _require_exact_keys(row, ("name", "version"), "DISTRIBUTION_ROW")
        if type(item["name"]) is not str or type(item["version"]) is not str:
            raise CaptureError("INSTALLED_DISTRIBUTION_TYPE_INVALID")
        observed_rows.append(dict(item))
    expected_order = sorted(
        observed_rows,
        key=lambda row: (row["name"].casefold(), row["name"], row["version"]),
    )
    if observed_rows != expected_order or len(
        {(row["name"], row["version"]) for row in observed_rows}
    ) != len(observed_rows):
        raise CaptureError("INSTALLED_DISTRIBUTION_ORDER_OR_UNIQUENESS_INVALID")

    environment = _require_exact_keys(
        top["determinism_environment"],
        (
            "allowlist",
            "present",
            "absent",
            "nonallowlisted_environment_names_or_values_recorded",
        ),
        "DETERMINISM_ENVIRONMENT",
    )
    if environment["allowlist"] != list(DETERMINISM_ENV_ALLOWLIST):
        raise CaptureError("DETERMINISM_ENVIRONMENT_ALLOWLIST_MISMATCH")
    if environment["nonallowlisted_environment_names_or_values_recorded"] is not False:
        raise CaptureError("NONALLOWLISTED_ENVIRONMENT_CLAIM")
    present = environment["present"]
    absent = environment["absent"]
    if (
        type(present) is not dict
        or type(absent) is not list
        or set(present).intersection(absent)
        or set(present).union(absent) != set(DETERMINISM_ENV_ALLOWLIST)
        or any(type(value) is not str for value in present.values())
    ):
        raise CaptureError("DETERMINISM_ENVIRONMENT_PARTITION_INVALID")

    supplied_digest = top["receipt_payload_sha256"]
    if type(supplied_digest) is not str or _SHA256.fullmatch(supplied_digest) is None:
        raise CaptureError("RECEIPT_PAYLOAD_SHA256_INVALID")
    unsigned = dict(top)
    del unsigned["receipt_payload_sha256"]
    expected_digest = _sha256(RECEIPT_DOMAIN + _canonical_bytes(unsigned))
    if supplied_digest != expected_digest:
        raise CaptureError("RECEIPT_PAYLOAD_SHA256_MISMATCH")
    _validate_json_tree(receipt, "RECEIPT")
    return {
        "decision": "VALID_RECEIPT_REQUIRES_LATER_NORMALIZATION_AND_EXTERNAL_REVIEW",
        "receipt_payload_sha256": supplied_digest,
        "study_or_test_data_accessed": False,
        "field_or_blocker_closure_authorized": False,
    }


def _load_inputs(
    cluster_path: str,
    reservation_path: str,
    container_digest_text: str | None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    cluster_json, cluster_capture = _input_capture(cluster_path, "CLUSTER_JSON")
    reservation_json, reservation_capture = _input_capture(
        reservation_path, "STORAGE_RESERVATION_JSON"
    )
    container_capture = _container_capture(container_digest_text)
    cluster_signals = _cluster_target_signals(cluster_json)
    if reservation_capture["content"] != reservation_json:
        raise CaptureError("STORAGE_RESERVATION_INTERNAL_BINDING_MISMATCH")
    return (
        cluster_capture,
        reservation_capture,
        container_capture,
        cluster_signals,
    )


def capture(
    cluster_path: str,
    reservation_path: str,
    output_path: str,
    container_digest_text: str | None,
) -> Dict[str, Any]:
    (
        cluster_capture,
        reservation_capture,
        container_capture,
        cluster_signals,
    ) = _load_inputs(cluster_path, reservation_path, container_digest_text)
    receipt = _build_receipt(
        cluster_capture,
        reservation_capture,
        container_capture,
        cluster_signals,
    )
    _validate_receipt_structure(
        receipt,
        cluster_capture,
        reservation_capture,
        container_capture,
    )
    raw = _canonical_bytes(receipt) + b"\n"
    output = _write_exclusive_private_file(output_path, raw)
    return {
        "decision": "CAPTURE_WRITTEN_REQUIRES_LATER_NORMALIZATION_AND_EXTERNAL_REVIEW",
        **output,
        "receipt_payload_sha256": receipt["receipt_payload_sha256"],
        "study_or_test_data_accessed": False,
        "field_or_blocker_closure_authorized": False,
    }


def validate_only(
    cluster_path: str,
    reservation_path: str,
    output_path: str,
    container_digest_text: str | None,
) -> Dict[str, Any]:
    (
        cluster_capture,
        reservation_capture,
        container_capture,
        _cluster_signals,
    ) = _load_inputs(cluster_path, reservation_path, container_digest_text)
    raw, custody = _read_stable_regular_file(
        output_path,
        "OUTPUT_RECEIPT",
        MAX_JSON_INPUT_BYTES,
        require_mode_0600=True,
    )
    receipt = _parse_canonical_json(raw, "OUTPUT_RECEIPT")
    result = _validate_receipt_structure(
        receipt,
        cluster_capture,
        reservation_capture,
        container_capture,
    )
    return {
        **result,
        "output_basename": custody["source_basename"],
        "output_path_recorded": False,
        "output_raw_byte_count": custody["raw_byte_count"],
        "output_raw_sha256": custody["raw_sha256"],
        "output_file_mode_octal": custody["file_mode_octal"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Capture a private, pre-data Databricks AWS classic dedicated "
            "qualification receipt without network, REST, Spark data, or subprocess access."
        )
    )
    parser.add_argument(
        "--cluster-json",
        required=True,
        help="Canonical sanitized exported cluster JSON file.",
    )
    parser.add_argument(
        "--storage-reservation-json",
        required=True,
        help="Canonical admin storage-reservation JSON file.",
    )
    parser.add_argument(
        "--container-digest-text",
        default=None,
        help="Optional immutable OCI-style digest literal: sha256:<64 lowercase hex>.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help=(
            "Explicit local private receipt file. Capture mode creates it exclusively; "
            "validate-only mode reads it. DBFS and Unity Catalog Volume paths are forbidden."
        ),
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the existing output receipt against the same explicit inputs.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.validate_only:
            result = validate_only(
                arguments.cluster_json,
                arguments.storage_reservation_json,
                arguments.output,
                arguments.container_digest_text,
            )
        else:
            result = capture(
                arguments.cluster_json,
                arguments.storage_reservation_json,
                arguments.output,
                arguments.container_digest_text,
            )
    except (CaptureError, OSError, ValueError, TypeError) as error:
        print("FAIL:" + str(error), file=sys.stderr)
        return 1
    print(_canonical_bytes(result).decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
