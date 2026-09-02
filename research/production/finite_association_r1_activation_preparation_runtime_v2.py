"""Read-only runtime double-capture oracle for activation preparation v2.

The child writes canonical bytes only to stdout.  It never publishes files,
approves a runtime, imports a scientific launcher, or performs scientific work.
Raw capture envelopes are validated and projected in memory by the parent and
must never be persisted.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import stat
import sys
from typing import Any, Dict, Mapping, Sequence


MODULE_PATH = Path(__file__).resolve()
HOST_WORKSPACE_ROOT = MODULE_PATH.parents[2]
WORKSPACE_ROOT = HOST_WORKSPACE_ROOT
CONTRACTS_PATH = (
    WORKSPACE_ROOT
    / "research/production/finite_association_r1_activation_preparation_contracts_v2.py"
)

try:
    from research.production import (
        finite_association_r1_activation_preparation_contracts_v2 as contracts,
    )
except ModuleNotFoundError:  # direct isolated child
    _spec = importlib.util.spec_from_file_location(
        "finite_association_r1_activation_preparation_contracts_v2",
        CONTRACTS_PATH,
    )
    if _spec is None or _spec.loader is None:
        raise RuntimeError("contracts module cannot be loaded")
    contracts = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(contracts)


RAW_ENVELOPE_SCHEMA = "heterodiff-a1-r1-runtime-raw-capture-envelope-v2"
RAW_OBSERVATION_SCHEMA = "heterodiff-a1-r1-runtime-raw-observation-v2"
RAW_ENVELOPE_DOMAIN = (RAW_ENVELOPE_SCHEMA + "\0").encode("ascii")
RAW_OBSERVATION_DOMAIN = (RAW_OBSERVATION_SCHEMA + "\0").encode("ascii")
INSTALLED_FILE_ROSTER_DOMAIN = b"heterodiff-a1-r1-runtime-installed-file-roster-v2\0"
CAPSULE_FILE_ROSTER_DOMAIN = b"heterodiff-a1-r1-runtime-capsule-file-roster-v2\0"
SEMANTIC_MANIFEST_DOMAIN = b"heterodiff-a1-r1-runtime-semantic-manifest-v2\0"
PRIVACY_PROJECTION_DOMAIN = b"heterodiff-a1-r1-runtime-privacy-projection-v2\0"
ENVIRONMENT_POLICY_DOMAIN = b"heterodiff-a1-r1-runtime-environment-policy-v2\0"
REQUEST_LAUNCH_PREIMAGE_DOMAIN = b"heterodiff-a1-r1-runtime-request-launch-seed-v2\0"
LAUNCH_BINDING_DOMAIN = b"heterodiff-a1-r1-runtime-capture-launch-binding-v2\0"
TARGET_PROFILE_ID = "M1_REFERENCE_MACOS_ARM64_PY311_ACTIVATION_PREPARATION_V2"
PYTHON_RELATIVE_PATH = ".venv-m1/bin/python"
SITE_PACKAGES_RELATIVE_PATH = ".venv-m1/lib/python3.11/site-packages"
CAPSULE_ROOT_RELATIVE_PATH = "artifacts/a1_r1_activation_preparation_v2/capsule"
CAPTURE_ENVIRONMENT = {
    "LANG": "C",
    "LC_ALL": "C",
    "PYTHONHASHSEED": "0",
}
PYTHON_FLAGS = ("-I", "-S", "-B", "-X", "utf8")
EXPECTED_INTERPRETER_REALPATH = (
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
)
EXPECTED_ISOLATED_SYS_PATH = (
    "/Library/Frameworks/Python.framework/Versions/3.11/lib/python311.zip",
    "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11",
    "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload",
)
APPROVED_PATH_ROOTS = (
    ("<WORKSPACE>", WORKSPACE_ROOT),
    ("<VENV>", WORKSPACE_ROOT / ".venv-m1"),
    ("<SYSTEM_LIBRARY_FRAMEWORKS>", Path("/Library/Frameworks")),
    ("<SYSTEM_USR>", Path("/usr")),
    ("<SYSTEM_SYSTEM>", Path("/System")),
    ("<SYSTEM_OPT>", Path("/opt")),
    ("<SYSTEM_PRIVATE>", Path("/private")),
)
MAXIMUM_RAW_ENVELOPE_BYTES = 256 * 1024 * 1024
MAXIMUM_FILE_COUNT = 250_000


class RuntimePreparationError(RuntimeError):
    """Fail-closed runtime preparation error."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(value: Any) -> bytes:
    return contracts.canonical_json(value)


def environment_policy() -> Dict[str, Any]:
    body = {
        "schema": "heterodiff-a1-r1-runtime-environment-policy-v2",
        "replacement_environment": dict(CAPTURE_ENVIRONMENT),
        "inherited_environment_permitted": False,
        "python_flags": list(PYTHON_FLAGS),
        "pythonpath_present": False,
        "pythonhome_present": False,
        "network_contact_permitted": False,
        "scientific_compute_permitted": False,
        "approved_path_tokens": [token for token, _ in APPROVED_PATH_ROOTS],
    }
    return {
        **body,
        "policy_sha256": _sha256(ENVIRONMENT_POLICY_DOMAIN + _canonical(body)),
    }


def validate_runtime_request(value: Mapping[str, Any]) -> Dict[str, Any]:
    checked = contracts.validate_record(dict(value), "RUNTIME_REQUEST")
    if (
        checked["target_profile_id"] != TARGET_PROFILE_ID
        or checked["python_relative_path"] != PYTHON_RELATIVE_PATH
        or checked["python_flags"] != list(PYTHON_FLAGS)
        or checked["environment_policy_sha256"] != environment_policy()["policy_sha256"]
    ):
        raise RuntimePreparationError("runtime request fixed identity changed")
    _require_safe_relative_path(
        checked["capsule_root_relative_path"],
        CAPSULE_ROOT_RELATIVE_PATH,
        "runtime capsule path",
    )
    _require_safe_relative_path(
        checked["site_packages_relative_path"],
        SITE_PACKAGES_RELATIVE_PATH,
        "runtime site-packages path",
    )
    body = dict(checked)
    body["launch_binding_preimage_sha256"] = None
    body["launch_binding_a_sha256"] = None
    body["launch_binding_b_sha256"] = None
    body["request_sha256"] = None
    preimage = _sha256(REQUEST_LAUNCH_PREIMAGE_DOMAIN + _canonical(body))
    if checked["launch_binding_preimage_sha256"] != preimage:
        raise RuntimePreparationError("runtime launch preimage changed")
    expected = [
        _sha256(
            LAUNCH_BINDING_DOMAIN
            + preimage.encode("ascii")
            + b"\0"
            + str(i).encode("ascii")
        )
        for i in (0, 1)
    ]
    if [
        checked["launch_binding_a_sha256"],
        checked["launch_binding_b_sha256"],
    ] != expected:
        raise RuntimePreparationError("runtime launch bindings changed")
    return checked


def _stable_regular_payload(path: Path) -> bytes:
    ancestors = _stable_ancestor_snapshot(path)
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise RuntimePreparationError("runtime inventory entry is not regular")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    chunks = []
    try:
        opened = os.fstat(descriptor)
        if _full_identity(opened) != _full_identity(before):
            raise RuntimePreparationError("runtime inventory entry changed before open")
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(1 << 20, remaining))
            if not chunk:
                raise RuntimePreparationError("runtime inventory entry ended early")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise RuntimePreparationError("runtime inventory entry grew")
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    payload = b"".join(chunks)
    after = path.lstat()
    if (
        ancestors != _stable_ancestor_snapshot(path)
        or _full_identity(before) != _full_identity(after_descriptor)
        or _full_identity(after_descriptor) != _full_identity(after)
        or len(payload) != after.st_size
    ):
        raise RuntimePreparationError("runtime inventory entry changed during read")
    return payload


def _full_identity(value: Any) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _stable_ancestor_snapshot(path: Path) -> tuple[tuple[str, tuple[int, ...]], ...]:
    rows = []
    for ancestor in reversed(path.absolute().parents):
        try:
            information = ancestor.lstat()
        except FileNotFoundError:
            break
        if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(information.st_mode):
            raise RuntimePreparationError("runtime custody has a linked ancestor")
        rows.append(
            (
                ancestor.as_posix(),
                (
                    information.st_dev,
                    information.st_ino,
                    information.st_mode,
                    information.st_uid,
                    information.st_gid,
                ),
            )
        )
    return tuple(rows)


def _tree_snapshot(root: Path) -> Dict[str, Any]:
    root = root.absolute()
    root_information = root.lstat()
    if stat.S_ISLNK(root_information.st_mode) or not stat.S_ISDIR(
        root_information.st_mode
    ):
        raise RuntimePreparationError("runtime inventory root is not a directory")
    directories = [("", _full_identity(root_information))]
    files = []
    for current, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        directory_names.sort()
        file_names.sort()
        if current_path != root:
            information = current_path.lstat()
            if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(
                information.st_mode
            ):
                raise RuntimePreparationError("runtime inventory directory changed")
            directories.append(
                (current_path.relative_to(root).as_posix(), _full_identity(information))
            )
        for name in directory_names:
            information = (current_path / name).lstat()
            if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(
                information.st_mode
            ):
                raise RuntimePreparationError("runtime inventory linked directory")
        for name in file_names:
            path = current_path / name
            information = path.lstat()
            if stat.S_ISLNK(information.st_mode) or not stat.S_ISREG(
                information.st_mode
            ):
                raise RuntimePreparationError("runtime inventory linked file")
            files.append(
                (path.relative_to(root).as_posix(), _full_identity(information))
            )
            if len(files) > MAXIMUM_FILE_COUNT:
                raise RuntimePreparationError(
                    "runtime inventory file count is excessive"
                )
    return {"directories": sorted(directories), "files": sorted(files)}


def _closed_file_roster(root: Path, domain: bytes) -> Dict[str, Any]:
    root = root.absolute()
    ancestors = _stable_ancestor_snapshot(root)
    before = _tree_snapshot(root)

    def read_rows() -> list[Dict[str, Any]]:
        result = []
        for relative_path, _ in before["files"]:
            path = root / relative_path
            payload = _stable_regular_payload(path)
            information = path.lstat()
            if information.st_nlink != 1:
                raise RuntimePreparationError("runtime inventory contains a hard link")
            result.append(
                {
                    "path": relative_path,
                    "bytes": len(payload),
                    "raw_sha256": _sha256(payload),
                    "mode_octal": format(stat.S_IMODE(information.st_mode), "04o"),
                }
            )
        return result

    first_rows = read_rows()
    second_rows = read_rows()
    after = _tree_snapshot(root)
    if (
        ancestors != _stable_ancestor_snapshot(root)
        or before != after
        or first_rows != second_rows
    ):
        raise RuntimePreparationError("runtime inventory changed across two reopens")
    directories = [row[0] for row in before["directories"]]
    body = {
        "root": root.as_posix(),
        "file_count": len(first_rows),
        "directory_count": len(directories),
        "directories": directories,
        "rows": first_rows,
    }
    return {**body, "manifest_sha256": _sha256(domain + _canonical(body))}


def _distribution_roster(site_packages_root: Path) -> Dict[str, Any]:
    rows = []
    for distribution in importlib.metadata.distributions(
        path=[site_packages_root.as_posix()]
    ):
        name = distribution.metadata.get("Name") or ""
        version = distribution.version or ""
        if not name or not version:
            raise RuntimePreparationError(
                "installed distribution identity is incomplete"
            )
        rows.append({"name": name, "version": version})
    rows.sort(key=lambda row: (row["name"].lower(), row["version"]))
    if len({(row["name"].lower(), row["version"]) for row in rows}) != len(rows):
        raise RuntimePreparationError("installed distribution roster is duplicated")
    body = {"rows": rows, "count": len(rows)}
    return {
        **body,
        "roster_sha256": _sha256(
            b"heterodiff-a1-r1-runtime-distribution-roster-v2\0" + _canonical(body)
        ),
    }


def _require_safe_relative_path(value: Any, expected: str, name: str) -> str:
    if type(value) is not str or value != expected or "\\" in value or "\x00" in value:
        raise RuntimePreparationError(name + " changed")
    path = Path(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts:
        raise RuntimePreparationError(name + " is not a normalized relative path")
    return value


def _validate_inventory(
    value: Any,
    domain: bytes,
    expected_root: Path | None = None,
) -> Dict[str, Any]:
    fields = {
        "root",
        "file_count",
        "directory_count",
        "directories",
        "rows",
        "manifest_sha256",
    }
    if type(value) is not dict or set(value) != fields:
        raise RuntimePreparationError("runtime inventory fields changed")
    if type(value["root"]) is not str or not value["root"].startswith("/"):
        raise RuntimePreparationError("runtime inventory root is not absolute")
    if (
        expected_root is not None
        and value["root"] != expected_root.absolute().as_posix()
    ):
        raise RuntimePreparationError("runtime inventory root changed")
    directories = value["directories"]
    rows = value["rows"]
    if (
        type(value["file_count"]) is not int
        or value["file_count"] < 0
        or type(value["directory_count"]) is not int
        or value["directory_count"] < 1
        or type(directories) is not list
        or type(rows) is not list
        or value["file_count"] != len(rows)
        or value["directory_count"] != len(directories)
        or len(rows) > MAXIMUM_FILE_COUNT
    ):
        raise RuntimePreparationError("runtime inventory counts changed")
    if directories != sorted(directories) or len(set(directories)) != len(directories):
        raise RuntimePreparationError("runtime inventory directories are not ordered")
    if not directories or directories[0] != "":
        raise RuntimePreparationError("runtime inventory root directory is missing")
    for relative in directories:
        if relative == "":
            continue
        if type(relative) is not str or "\\" in relative or "\x00" in relative:
            raise RuntimePreparationError("runtime inventory directory is invalid")
        path = Path(relative)
        if path.is_absolute() or path.as_posix() != relative or ".." in path.parts:
            raise RuntimePreparationError("runtime inventory directory escapes root")
        parents = [
            parent.as_posix() for parent in path.parents if parent.as_posix() != "."
        ]
        if any(parent not in directories for parent in parents):
            raise RuntimePreparationError(
                "runtime inventory directory has an orphan parent"
            )
    prior = None
    for row in rows:
        if type(row) is not dict or set(row) != {
            "path",
            "bytes",
            "raw_sha256",
            "mode_octal",
        }:
            raise RuntimePreparationError("runtime inventory row fields changed")
        relative = row["path"]
        if (
            type(relative) is not str
            or not relative
            or "\\" in relative
            or "\x00" in relative
        ):
            raise RuntimePreparationError("runtime inventory row path is invalid")
        path = Path(relative)
        if path.is_absolute() or path.as_posix() != relative or ".." in path.parts:
            raise RuntimePreparationError("runtime inventory row escapes root")
        parents = [
            parent.as_posix() for parent in path.parents if parent.as_posix() != "."
        ]
        if any(parent not in directories for parent in parents):
            raise RuntimePreparationError("runtime inventory row has an orphan parent")
        if prior is not None and relative <= prior:
            raise RuntimePreparationError(
                "runtime inventory rows are not strictly ordered"
            )
        prior = relative
        if type(row["bytes"]) is not int or row["bytes"] < 0:
            raise RuntimePreparationError("runtime inventory row bytes changed")
        contracts.require_sha256(row["raw_sha256"], "raw_sha256")
        if (
            type(row["mode_octal"]) is not str
            or len(row["mode_octal"]) != 4
            or any(character not in "01234567" for character in row["mode_octal"])
        ):
            raise RuntimePreparationError("runtime inventory row mode changed")
    body = {name: value[name] for name in fields if name != "manifest_sha256"}
    claimed = contracts.require_sha256(value["manifest_sha256"], "manifest_sha256")
    if claimed != _sha256(domain + _canonical(body)):
        raise RuntimePreparationError("runtime inventory manifest digest changed")
    return json.loads(_canonical(value).decode("ascii"))


def _validate_distributions(value: Any) -> Dict[str, Any]:
    if type(value) is not dict or set(value) != {"rows", "count", "roster_sha256"}:
        raise RuntimePreparationError("distribution roster fields changed")
    rows = value["rows"]
    if (
        type(rows) is not list
        or type(value["count"]) is not int
        or value["count"] != len(rows)
    ):
        raise RuntimePreparationError("distribution roster count changed")
    identities = []
    for row in rows:
        if (
            type(row) is not dict
            or set(row) != {"name", "version"}
            or type(row["name"]) is not str
            or not row["name"]
            or type(row["version"]) is not str
            or not row["version"]
        ):
            raise RuntimePreparationError("distribution roster row changed")
        identities.append((row["name"].lower(), row["version"]))
    if identities != sorted(identities) or len(set(identities)) != len(identities):
        raise RuntimePreparationError("distribution roster ordering changed")
    body = {"rows": rows, "count": value["count"]}
    claimed = contracts.require_sha256(value["roster_sha256"], "roster_sha256")
    if claimed != _sha256(
        b"heterodiff-a1-r1-runtime-distribution-roster-v2\0" + _canonical(body)
    ):
        raise RuntimePreparationError("distribution roster digest changed")
    return json.loads(_canonical(value).decode("ascii"))


def _capture_observation(
    request: Mapping[str, Any], capture_ordinal: int
) -> Dict[str, Any]:
    if capture_ordinal not in (0, 1):
        raise RuntimePreparationError("capture ordinal is not A or B")
    if os.environ != CAPTURE_ENVIRONMENT:
        raise RuntimePreparationError("runtime child environment is not exact")
    observed_flags = {
        "isolated": sys.flags.isolated,
        "no_site": sys.flags.no_site,
        "dont_write_bytecode": sys.flags.dont_write_bytecode,
        "safe_path": sys.flags.safe_path,
        "utf8_mode": sys.flags.utf8_mode,
        "ignore_environment": sys.flags.ignore_environment,
        "no_user_site": sys.flags.no_user_site,
    }
    expected_flags = {
        "isolated": 1,
        "no_site": 1,
        "dont_write_bytecode": 1,
        "safe_path": True,
        "utf8_mode": 1,
        "ignore_environment": 1,
        "no_user_site": 1,
    }
    if observed_flags != expected_flags:
        raise RuntimePreparationError("runtime child isolation flags are not exact")
    capsule_root = HOST_WORKSPACE_ROOT / request["capsule_root_relative_path"]
    site_packages_root = HOST_WORKSPACE_ROOT / request["site_packages_relative_path"]
    capsule_inventory = _closed_file_roster(capsule_root, CAPSULE_FILE_ROSTER_DOMAIN)
    installed_inventory = _closed_file_roster(
        site_packages_root, INSTALLED_FILE_ROSTER_DOMAIN
    )
    distributions = _distribution_roster(site_packages_root)
    body = {
        "schema": RAW_OBSERVATION_SCHEMA,
        "request_sha256": request["request_sha256"],
        "capture_ordinal": capture_ordinal,
        "target_profile_id": request["target_profile_id"],
        "python": {
            "executable": sys.executable,
            "executable_realpath": Path(sys.executable).resolve(strict=True).as_posix(),
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "version_info": list(sys.version_info[:5]),
            "flags": observed_flags,
            "sys_path": list(sys.path),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_compiler": platform.python_compiler(),
        },
        "environment": dict(CAPTURE_ENVIRONMENT),
        "source_capsule_manifest_sha256": request["source_capsule_manifest_sha256"],
        "source_capsule_inventory": capsule_inventory,
        "installed_files_inventory": installed_inventory,
        "installed_distributions": distributions,
        "complete_installed_file_verification": True,
        "network_contacted": False,
        "scientific_compute_executed": False,
        "approved": False,
        "observation_sha256": None,
    }
    body["observation_sha256"] = _sha256(RAW_OBSERVATION_DOMAIN + _canonical(body))
    return body


def build_raw_capture_envelope(request_payload: bytes, capture_ordinal: int) -> bytes:
    request = validate_runtime_request(
        contracts.parse_record(request_payload, "RUNTIME_REQUEST")
    )
    if request["environment_policy_sha256"] != environment_policy()["policy_sha256"]:
        raise RuntimePreparationError("runtime environment policy changed")
    if request["python_relative_path"] != PYTHON_RELATIVE_PATH:
        raise RuntimePreparationError("runtime Python path changed")
    _require_safe_relative_path(
        request["capsule_root_relative_path"],
        CAPSULE_ROOT_RELATIVE_PATH,
        "runtime capsule path",
    )
    _require_safe_relative_path(
        request["site_packages_relative_path"],
        SITE_PACKAGES_RELATIVE_PATH,
        "runtime site-packages path",
    )
    if request["target_profile_id"] != TARGET_PROFILE_ID:
        raise RuntimePreparationError("runtime target profile changed")
    if request["python_flags"] != list(PYTHON_FLAGS):
        raise RuntimePreparationError("runtime Python flags changed")
    observation = _capture_observation(request, capture_ordinal)
    body = {
        "schema": RAW_ENVELOPE_SCHEMA,
        "request_sha256": request["request_sha256"],
        "capture_ordinal": capture_ordinal,
        "observation": observation,
        "observation_raw_sha256": _sha256(_canonical(observation) + b"\n"),
        "observation_record_sha256": observation["observation_sha256"],
        "raw_envelope_persisted": False,
        "envelope_sha256": None,
    }
    body["envelope_sha256"] = _sha256(RAW_ENVELOPE_DOMAIN + _canonical(body))
    payload = _canonical(body) + b"\n"
    if len(payload) > MAXIMUM_RAW_ENVELOPE_BYTES:
        raise RuntimePreparationError("raw runtime envelope is too large")
    return payload


def _validate_raw_observation(value: Any) -> Dict[str, Any]:
    fields = {
        "schema",
        "request_sha256",
        "capture_ordinal",
        "target_profile_id",
        "python",
        "platform",
        "environment",
        "source_capsule_manifest_sha256",
        "source_capsule_inventory",
        "installed_files_inventory",
        "installed_distributions",
        "complete_installed_file_verification",
        "network_contacted",
        "scientific_compute_executed",
        "approved",
        "observation_sha256",
    }
    if type(value) is not dict or set(value) != fields:
        raise RuntimePreparationError("raw observation fields changed")
    if value["schema"] != RAW_OBSERVATION_SCHEMA:
        raise RuntimePreparationError("raw observation schema changed")
    contracts.require_sha256(value["request_sha256"], "request_sha256")
    contracts.require_sha256(
        value["source_capsule_manifest_sha256"],
        "source_capsule_manifest_sha256",
    )
    if type(value["capture_ordinal"]) is not int or value["capture_ordinal"] not in (
        0,
        1,
    ):
        raise RuntimePreparationError("raw observation ordinal changed")
    if value["target_profile_id"] != TARGET_PROFILE_ID:
        raise RuntimePreparationError("raw observation target profile changed")
    python = value["python"]
    if type(python) is not dict or set(python) != {
        "executable",
        "executable_realpath",
        "implementation",
        "version",
        "version_info",
        "flags",
        "sys_path",
    }:
        raise RuntimePreparationError("raw Python identity fields changed")
    for name in ("executable", "executable_realpath", "implementation", "version"):
        if type(python[name]) is not str or not python[name]:
            raise RuntimePreparationError("raw Python identity value changed")
    if not python["executable"].startswith("/") or not python[
        "executable_realpath"
    ].startswith("/"):
        raise RuntimePreparationError("raw Python paths are not absolute")
    version_info = python["version_info"]
    if (
        type(version_info) is not list
        or len(version_info) != 5
        or any(type(item) is not int for item in version_info[:3])
        or type(version_info[3]) is not str
        or type(version_info[4]) is not int
    ):
        raise RuntimePreparationError("raw Python version tuple changed")
    if python["flags"] != {
        "isolated": 1,
        "no_site": 1,
        "dont_write_bytecode": 1,
        "safe_path": True,
        "utf8_mode": 1,
        "ignore_environment": 1,
        "no_user_site": 1,
    }:
        raise RuntimePreparationError("raw Python flags changed")
    if (
        python["executable"] != (HOST_WORKSPACE_ROOT / PYTHON_RELATIVE_PATH).as_posix()
        or python["executable_realpath"] != EXPECTED_INTERPRETER_REALPATH
        or python["implementation"] != "CPython"
        or version_info[:2] != [3, 11]
        or python["sys_path"] != list(EXPECTED_ISOLATED_SYS_PATH)
    ):
        raise RuntimePreparationError("raw Python target-profile identity changed")
    if type(python["sys_path"]) is not list or any(
        type(item) is not str for item in python["sys_path"]
    ):
        raise RuntimePreparationError("raw Python sys.path changed")
    platform_row = value["platform"]
    if (
        type(platform_row) is not dict
        or set(platform_row)
        != {
            "system",
            "release",
            "machine",
            "python_compiler",
        }
        or any(type(item) is not str or not item for item in platform_row.values())
    ):
        raise RuntimePreparationError("raw platform identity changed")
    if platform_row["system"] != "Darwin" or platform_row["machine"] != "arm64":
        raise RuntimePreparationError("raw platform target profile changed")
    if value["environment"] != CAPTURE_ENVIRONMENT:
        raise RuntimePreparationError("raw capture environment changed")
    _validate_inventory(
        value["source_capsule_inventory"],
        CAPSULE_FILE_ROSTER_DOMAIN,
        HOST_WORKSPACE_ROOT / CAPSULE_ROOT_RELATIVE_PATH,
    )
    _validate_inventory(
        value["installed_files_inventory"],
        INSTALLED_FILE_ROSTER_DOMAIN,
        HOST_WORKSPACE_ROOT / SITE_PACKAGES_RELATIVE_PATH,
    )
    _validate_distributions(value["installed_distributions"])
    if (
        value["complete_installed_file_verification"] is not True
        or value["network_contacted"] is not False
        or value["scientific_compute_executed"] is not False
        or value["approved"] is not False
    ):
        raise RuntimePreparationError("raw observation execution boundary changed")
    body = dict(value)
    claimed = contracts.require_sha256(body["observation_sha256"], "observation_sha256")
    body["observation_sha256"] = None
    if claimed != _sha256(RAW_OBSERVATION_DOMAIN + _canonical(body)):
        raise RuntimePreparationError("raw observation self digest changed")
    return json.loads(_canonical(value).decode("ascii"))


def _parse_raw_envelope(payload: bytes) -> Dict[str, Any]:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) > MAXIMUM_RAW_ENVELOPE_BYTES
    ):
        raise RuntimePreparationError("raw envelope size or type is invalid")
    try:
        row = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimePreparationError("raw envelope is not ASCII JSON") from error
    fields = {
        "schema",
        "request_sha256",
        "capture_ordinal",
        "observation",
        "observation_raw_sha256",
        "observation_record_sha256",
        "raw_envelope_persisted",
        "envelope_sha256",
    }
    if (
        type(row) is not dict
        or set(row) != fields
        or row["schema"] != RAW_ENVELOPE_SCHEMA
    ):
        raise RuntimePreparationError("raw envelope fields changed")
    body = dict(row)
    claimed = contracts.require_sha256(body["envelope_sha256"], "envelope_sha256")
    body["envelope_sha256"] = None
    if claimed != _sha256(RAW_ENVELOPE_DOMAIN + _canonical(body)):
        raise RuntimePreparationError("raw envelope self digest changed")
    observation = _validate_raw_observation(row["observation"])
    observation_claimed = observation["observation_sha256"]
    if (
        row["observation_raw_sha256"] != _sha256(_canonical(observation) + b"\n")
        or row["observation_record_sha256"] != observation_claimed
        or row["raw_envelope_persisted"] is not False
        or payload != _canonical(row) + b"\n"
    ):
        raise RuntimePreparationError("raw envelope custody changed")
    return row


def _tokenize_absolute_path(value: str) -> str:
    if not value.startswith("/"):
        return value
    path = Path(value)
    if path.as_posix() != value or ".." in path.parts:
        raise RuntimePreparationError("raw runtime path is not normalized")
    for token, root in sorted(
        APPROVED_PATH_ROOTS, key=lambda row: len(str(row[1])), reverse=True
    ):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        suffix = relative.as_posix()
        return token if suffix == "." else token + "/" + suffix
    raise RuntimePreparationError(
        "raw runtime evidence contains an unclassified absolute path"
    )


def _privacy_projection(value: Any) -> Any:
    if type(value) is str:
        return _tokenize_absolute_path(value)
    if type(value) is list:
        return [_privacy_projection(item) for item in value]
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise RuntimePreparationError("runtime evidence has a non-string key")
        return {key: _privacy_projection(item) for key, item in value.items()}
    if value is None or type(value) in (bool, int, float):
        return value
    raise RuntimePreparationError("runtime evidence contains an unsupported value")


def _restore_tokenized_paths(value: Any) -> Any:
    if type(value) is str:
        for token, root in APPROVED_PATH_ROOTS:
            if value == token:
                return root.as_posix()
            prefix = token + "/"
            if value.startswith(prefix):
                suffix = value[len(prefix) :]
                if not suffix or "\\" in suffix or "\x00" in suffix:
                    raise RuntimePreparationError("tokenized path suffix changed")
                path = Path(suffix)
                if path.is_absolute() or ".." in path.parts:
                    raise RuntimePreparationError(
                        "tokenized path escapes approved root"
                    )
                return (root / suffix).as_posix()
        if value.startswith("/"):
            raise RuntimePreparationError(
                "privacy projection contains an absolute path"
            )
        return value
    if type(value) is list:
        return [_restore_tokenized_paths(item) for item in value]
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise RuntimePreparationError("privacy projection key type changed")
        return {key: _restore_tokenized_paths(item) for key, item in value.items()}
    if value is None or type(value) in (bool, int, float):
        return value
    raise RuntimePreparationError("privacy projection value type changed")


def validate_persisted_binding(
    value: Mapping[str, Any], request: Mapping[str, Any]
) -> Dict[str, Any]:
    checked = contracts.validate_record(dict(value), "RUNTIME_ENVELOPE_BINDING")
    checked_request = validate_runtime_request(request)
    ordinal = checked["capture_ordinal"]
    expected_launch = (
        checked_request["launch_binding_a_sha256"]
        if ordinal == 0
        else checked_request["launch_binding_b_sha256"]
    )
    if (
        type(ordinal) is not int
        or ordinal not in (0, 1)
        or checked["request_sha256"] != checked_request["request_sha256"]
        or checked["launch_binding_sha256"] != expected_launch
        or checked["source_capsule_manifest_sha256"]
        != checked_request["source_capsule_manifest_sha256"]
        or checked["target_profile_id"] != TARGET_PROFILE_ID
        or checked["raw_envelope_persisted"] is not False
        or checked["approved"] is not False
        or checked["scientific_compute_executed"] is not False
        or checked["complete_installed_file_verification"] is not True
        or checked["unclassified_absolute_path_count"] != 0
    ):
        raise RuntimePreparationError("persisted runtime binding semantics changed")
    projection_record = checked["privacy_safe_projection"]
    if type(projection_record) is not dict or set(projection_record) != {
        "schema",
        "semantic_projection",
        "semantic_manifest_sha256",
        "path_tokens",
    }:
        raise RuntimePreparationError("privacy-safe projection fields changed")
    if projection_record[
        "schema"
    ] != "heterodiff-a1-r1-runtime-complete-privacy-safe-semantic-projection-v2" or projection_record[
        "path_tokens"
    ] != [
        token for token, _ in APPROVED_PATH_ROOTS
    ]:
        raise RuntimePreparationError("privacy-safe projection policy changed")
    semantic_projection = projection_record["semantic_projection"]
    if type(semantic_projection) is not dict or set(semantic_projection) != {
        "schema",
        "request_sha256",
        "capture_ordinal",
        "target_profile_id",
        "python",
        "platform",
        "environment",
        "source_capsule_manifest_sha256",
        "source_capsule_inventory",
        "installed_files_inventory",
        "installed_distributions",
        "complete_installed_file_verification",
        "network_contacted",
        "scientific_compute_executed",
        "approved",
        "observation_sha256",
    }:
        raise RuntimePreparationError("semantic projection fields changed")
    if (
        semantic_projection["capture_ordinal"] is not None
        or semantic_projection["observation_sha256"] is not None
    ):
        raise RuntimePreparationError("semantic projection retained capture identity")
    semantic_sha256 = _sha256(
        SEMANTIC_MANIFEST_DOMAIN + _canonical(semantic_projection)
    )
    if (
        semantic_sha256 != projection_record["semantic_manifest_sha256"]
        or semantic_sha256 != checked["semantic_manifest_sha256"]
        or _sha256(PRIVACY_PROJECTION_DOMAIN + _canonical(projection_record))
        != checked["privacy_projection_sha256"]
    ):
        raise RuntimePreparationError("privacy-safe semantic digest changed")
    restored = _restore_tokenized_paths(semantic_projection)
    if (
        restored["schema"] != RAW_OBSERVATION_SCHEMA
        or restored["request_sha256"] != checked_request["request_sha256"]
        or restored["target_profile_id"] != TARGET_PROFILE_ID
        or restored["environment"] != CAPTURE_ENVIRONMENT
        or restored["source_capsule_manifest_sha256"]
        != checked_request["source_capsule_manifest_sha256"]
        or restored["complete_installed_file_verification"] is not True
        or restored["network_contacted"] is not False
        or restored["scientific_compute_executed"] is not False
        or restored["approved"] is not False
    ):
        raise RuntimePreparationError("restored semantic projection changed")
    reconstructed_observation = dict(restored)
    reconstructed_observation["capture_ordinal"] = ordinal
    reconstructed_observation["observation_sha256"] = _sha256(
        RAW_OBSERVATION_DOMAIN + _canonical(reconstructed_observation)
    )
    _validate_raw_observation(reconstructed_observation)
    capsule_inventory = _validate_inventory(
        restored["source_capsule_inventory"],
        CAPSULE_FILE_ROSTER_DOMAIN,
        HOST_WORKSPACE_ROOT / CAPSULE_ROOT_RELATIVE_PATH,
    )
    installed_inventory = _validate_inventory(
        restored["installed_files_inventory"],
        INSTALLED_FILE_ROSTER_DOMAIN,
        HOST_WORKSPACE_ROOT / SITE_PACKAGES_RELATIVE_PATH,
    )
    _validate_distributions(restored["installed_distributions"])
    if (
        capsule_inventory["manifest_sha256"]
        != restored["source_capsule_inventory"]["manifest_sha256"]
        or installed_inventory["manifest_sha256"]
        != checked["installed_files_manifest_sha256"]
    ):
        raise RuntimePreparationError("persisted inventory binding changed")
    return checked


def project_envelope_binding(
    raw_payload: bytes,
    request: Mapping[str, Any],
    launch_claim_sha256: str,
    launch_binding_sha256: str,
    child_process_receipt: Mapping[str, Any],
) -> Dict[str, Any]:
    checked_request = validate_runtime_request(request)
    envelope = _parse_raw_envelope(raw_payload)
    ordinal = envelope["capture_ordinal"]
    if type(ordinal) is not int or ordinal not in (0, 1):
        raise RuntimePreparationError("runtime capture ordinal changed")
    expected_launch = (
        checked_request["launch_binding_a_sha256"]
        if ordinal == 0
        else checked_request["launch_binding_b_sha256"]
    )
    if (
        envelope["request_sha256"] != checked_request["request_sha256"]
        or launch_binding_sha256 != expected_launch
    ):
        raise RuntimePreparationError("runtime envelope request binding changed")
    contracts.require_sha256(launch_claim_sha256, "launch_claim_sha256")
    observation = envelope["observation"]
    if (
        observation["request_sha256"] != checked_request["request_sha256"]
        or observation["capture_ordinal"] != ordinal
        or observation["target_profile_id"] != checked_request["target_profile_id"]
        or observation["source_capsule_manifest_sha256"]
        != checked_request["source_capsule_manifest_sha256"]
        or observation["complete_installed_file_verification"] is not True
        or observation["scientific_compute_executed"] is not False
        or observation["network_contacted"] is not False
        or observation["approved"] is not False
    ):
        raise RuntimePreparationError("runtime observation semantics changed")
    process_fields = {
        "child_process_id",
        "child_exit_code",
        "child_stdout_byte_count",
        "child_stderr_byte_count",
        "child_oracle_raw_sha256",
        "child_oracle_api_sha256",
    }
    if (
        type(child_process_receipt) is not dict
        or set(child_process_receipt) != process_fields
    ):
        raise RuntimePreparationError("runtime child process receipt fields changed")
    if (
        type(child_process_receipt["child_process_id"]) is not int
        or child_process_receipt["child_process_id"] <= 0
        or child_process_receipt["child_exit_code"] != 0
        or type(child_process_receipt["child_stdout_byte_count"]) is not int
        or child_process_receipt["child_stdout_byte_count"] != len(raw_payload)
        or child_process_receipt["child_stderr_byte_count"] != 0
    ):
        raise RuntimePreparationError("runtime child process receipt changed")
    contracts.require_sha256(
        child_process_receipt["child_oracle_raw_sha256"],
        "child_oracle_raw_sha256",
    )
    contracts.require_sha256(
        child_process_receipt["child_oracle_api_sha256"],
        "child_oracle_api_sha256",
    )
    semantic = dict(observation)
    semantic["capture_ordinal"] = None
    semantic["observation_sha256"] = None
    projection = _privacy_projection(semantic)
    semantic_sha256 = _sha256(SEMANTIC_MANIFEST_DOMAIN + _canonical(projection))
    installed_sha256 = observation["installed_files_inventory"]["manifest_sha256"]
    contracts.require_sha256(installed_sha256, "installed_files_manifest_sha256")
    privacy_summary = {
        "schema": "heterodiff-a1-r1-runtime-complete-privacy-safe-semantic-projection-v2",
        "semantic_projection": projection,
        "semantic_manifest_sha256": semantic_sha256,
        "path_tokens": [token for token, _ in APPROVED_PATH_ROOTS],
    }
    privacy_sha256 = _sha256(PRIVACY_PROJECTION_DOMAIN + _canonical(privacy_summary))
    record = {
        "schema": contracts.RUNTIME_ENVELOPE_BINDING_SCHEMA,
        "request_sha256": checked_request["request_sha256"],
        "capture_ordinal": ordinal,
        "launch_claim_sha256": launch_claim_sha256,
        "launch_binding_sha256": launch_binding_sha256,
        "child_process_id": child_process_receipt["child_process_id"],
        "child_exit_code": 0,
        "child_stdout_byte_count": len(raw_payload),
        "child_stderr_byte_count": 0,
        "child_oracle_raw_sha256": child_process_receipt["child_oracle_raw_sha256"],
        "child_oracle_api_sha256": child_process_receipt["child_oracle_api_sha256"],
        "raw_envelope_sha256": _sha256(raw_payload),
        "raw_envelope_record_sha256": envelope["envelope_sha256"],
        "raw_envelope_persisted": False,
        "embedded_candidate_raw_sha256": envelope["observation_raw_sha256"],
        "embedded_candidate_record_sha256": envelope["observation_record_sha256"],
        "semantic_manifest_sha256": semantic_sha256,
        "installed_files_manifest_sha256": installed_sha256,
        "source_capsule_manifest_sha256": checked_request[
            "source_capsule_manifest_sha256"
        ],
        "target_profile_id": checked_request["target_profile_id"],
        "privacy_safe_projection": privacy_summary,
        "privacy_projection_sha256": privacy_sha256,
        "unclassified_absolute_path_count": 0,
        "complete_installed_file_verification": True,
        "scientific_compute_executed": False,
        "approved": False,
        "binding_sha256": None,
    }
    return validate_persisted_binding(
        contracts.finish_record(record, "RUNTIME_ENVELOPE_BINDING"),
        checked_request,
    )


def _read_stdin(maximum_bytes: int) -> bytes:
    chunks = []
    total = 0
    while True:
        chunk = os.read(0, min(1 << 20, maximum_bytes - total + 1))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > maximum_bytes:
            raise RuntimePreparationError("runtime child request is too large")
    return b"".join(chunks)


def _write_stdout(payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(1, view)
        if written <= 0:
            raise RuntimePreparationError("runtime child stdout write failed")
        view = view[written:]


def main(arguments: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if arguments is None else arguments)
    if argv not in (["--capture-a"], ["--capture-b"]):
        raise SystemExit(
            "usage: finite_association_r1_activation_preparation_runtime_v2.py "
            "--capture-a|--capture-b"
        )
    ordinal = 0 if argv == ["--capture-a"] else 1
    request_payload = _read_stdin(contracts.MAXIMUM_RECORD_BYTES)
    _write_stdout(build_raw_capture_envelope(request_payload, ordinal))
    return 0


if __name__ == "__main__":  # pragma: no cover - future audited child only
    raise SystemExit(main())


__all__ = [
    "CAPTURE_ENVIRONMENT",
    "PYTHON_FLAGS",
    "PYTHON_RELATIVE_PATH",
    "RuntimePreparationError",
    "SITE_PACKAGES_RELATIVE_PATH",
    "TARGET_PROFILE_ID",
    "build_raw_capture_envelope",
    "environment_policy",
    "project_envelope_binding",
    "validate_runtime_request",
    "validate_persisted_binding",
]
