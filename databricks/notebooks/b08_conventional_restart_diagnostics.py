# Databricks notebook source
"""Read-only explanation of the reported B08 restart-marker mismatch.

Run inside the FAILING notebook's Python session. Add a temporary final cell:
    %run ./b08_conventional_restart_diagnostics
Run only that cell, copy its JSON output, and then remove the temporary cell.
Do not open this helper separately and choose Run all: notebook environments
can differ. This helper does not install, restart, repair, or run integration.
It leaves the existing marker, wheel, and source files untouched.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import re
import sys
from pathlib import Path


_B08_DIAG_SCHEMA = "heterodiff-b08-conventional-restart-diagnostics-v1"
_B08_DIAG_CONTROLLER_SCHEMA = "heterodiff-b08-conventional-runtime-integration-v1"
_B08_DIAG_ANCHOR_PATH = "requirements/b08-conventional-runtime-controller-anchor-v1.json"
_B08_DIAG_MANIFEST_PATH = "requirements/b08-conventional-runtime-source-manifest-v1.json"
_B08_DIAG_LOCK_PATH = "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock"
_B08_DIAG_REPORTED_INSTALL = {
    "controller_sha256": "fa01936fdd0b8b80af5fc172affb3ca7225976bce14bf89cf7fa6d799e65dcc2",
    "source_manifest_record_sha256": "59d2814a79f3dd79e3fd5d352897eeaea1d35cca5c7e3ce36b5b5ce22f269e60",
    "lock_sha256": "c6fa5d600cd2810c40ae47d5eeeba341e0467c4c75dd7c7d310cf3628ab6349f",
    "project_wheel_sha256": "8c6396928b1cf7b6d6d61cd29428e02fbe4eb7903fc745d52fd567786e6a678a",
}
_B08_DIAG_MARKER_PATH = Path("/tmp") / (
    "heterodiff-b08-conventional-"
    f"{_B08_DIAG_REPORTED_INSTALL['source_manifest_record_sha256'][:16]}-"
    f"{_B08_DIAG_REPORTED_INSTALL['lock_sha256'][:16]}.json"
)


def _b08_diag_bytes(path: Path) -> bytes:
    with path.open("rb") as stream:
        payload = stream.read(1024 * 1024 + 1)
    if len(payload) > 1024 * 1024:
        raise ValueError(f"DIAGNOSTIC_FILE_TOO_LARGE:{path.name}")
    return payload


def _b08_diag_json(payload: bytes) -> dict:
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("DIAGNOSTIC_JSON_OBJECT_REQUIRED")
    return value


def _b08_diag_sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _b08_diag_root() -> Path:
    # %run executes in the caller; search only its current directory/ancestors.
    start = Path.cwd()
    for candidate in (start, *start.parents):
        if all((candidate / name).is_file() for name in (
            _B08_DIAG_ANCHOR_PATH, _B08_DIAG_MANIFEST_PATH, _B08_DIAG_LOCK_PATH
        )):
            return candidate
    raise ValueError("PROJECT_ROOT_NOT_FOUND_RUN_FROM_EXISTING_PROJECT_NOTEBOOK")


def _b08_diag_differences(stored: dict, current: dict, prefix: str = "") -> dict:
    differences = {}
    for key, value in current.items():
        name = f"{prefix}.{key}" if prefix else key
        if key not in stored:
            differences[name] = {"stored_field_absent": True, "current": value}
        elif isinstance(value, dict) and isinstance(stored[key], dict):
            differences.update(_b08_diag_differences(stored[key], value, name))
        elif stored[key] != value:
            differences[name] = {"stored": stored[key], "current": value}
    for key in sorted(stored.keys() - current.keys()):
        name = f"{prefix}.{key}" if prefix else key
        differences[name] = {"stored": stored[key], "current_field_absent": True}
    return differences


def _b08_diag_packages(lock_payload: bytes) -> dict:
    versions = dict(re.findall(
        r"^([A-Za-z0-9_.-]+)==([^\s\\]+)", lock_payload.decode("utf-8"), re.MULTILINE
    ))
    versions["heterodiff"] = "0.1.0"
    missing, mismatches, roots, observed = [], {}, {}, {}
    for name, expected in versions.items():
        try:
            distribution = importlib.metadata.distribution(name)
            observed[name] = distribution.version
            location = str(Path(distribution.locate_file("")).resolve())
            roots.setdefault(location, []).append(name)
            if distribution.version != expected:
                mismatches[name] = {"expected": expected, "observed": distribution.version}
        except importlib.metadata.PackageNotFoundError:
            missing.append(name)
    return {
        "expected_count_including_project": len(versions),
        "missing": missing,
        "version_mismatches": mismatches,
        "observed_versions": observed,
        "distribution_roots": roots,
        "library_payloads_imported": False,
    }


def _b08_restart_diagnostic_report(project_root: Path, marker_path: Path) -> dict:
    anchor_raw = _b08_diag_bytes(project_root / _B08_DIAG_ANCHOR_PATH)
    manifest_raw = _b08_diag_bytes(project_root / _B08_DIAG_MANIFEST_PATH)
    lock_raw = _b08_diag_bytes(project_root / _B08_DIAG_LOCK_PATH)
    marker_raw = _b08_diag_bytes(marker_path)
    anchor, manifest, marker = map(_b08_diag_json, (anchor_raw, manifest_raw, marker_raw))
    # Mirror the eight comparisons in the failing controller. The temporary
    # %run cell changes notebook serialization, so do not rehash its payload.
    current = {
        "schema_version": _B08_DIAG_CONTROLLER_SCHEMA,
        "state": "INSTALL_COMPLETE_RESTART_REQUIRED",
        "controller_anchor": {
            "relative_path": _B08_DIAG_ANCHOR_PATH,
            "file_sha256": _b08_diag_sha(anchor_raw),
            "record_sha256": anchor["record_sha256"],
            "identity_scope": anchor["identity_scope"],
            "controller": anchor["controller"],
        },
        "source_manifest_relative_path": _B08_DIAG_MANIFEST_PATH,
        "source_manifest_file_sha256": _b08_diag_sha(manifest_raw),
        "source_manifest_record_sha256": manifest["record_sha256"],
        "lock_sha256": _b08_diag_sha(lock_raw),
        "python_prefix": sys.prefix,
    }
    stored = {key: marker[key] for key in current if key in marker}
    mismatches = _b08_diag_differences(stored, current)
    stored_prefix = marker.get("python_prefix")
    prefix_resolution = {"checked": False}
    if isinstance(stored_prefix, str) and Path(stored_prefix).is_absolute():
        try:
            old_resolved = str(Path(stored_prefix).resolve(strict=True))
            new_resolved = str(Path(sys.prefix).resolve(strict=True))
            prefix_resolution = {
                "checked": True, "stored_resolved": old_resolved,
                "current_resolved": new_resolved,
                "same_resolved_directory": old_resolved == new_resolved,
            }
        except OSError as error:
            prefix_resolution = {"checked": False, "error_type": type(error).__name__}
    stored_install = {
        key: marker.get(key) for key in _B08_DIAG_REPORTED_INSTALL
        if key != "controller_sha256"
    }
    stored_install["controller_sha256"] = (
        marker.get("controller_anchor", {}).get("controller", {}).get("sha256")
    )
    return {
        "schema_version": _B08_DIAG_SCHEMA,
        "decision": "RESTART_BINDING_DIFFERENCES_IDENTIFIED" if mismatches else "NO_BINDING_DIFFERENCE_IN_THIS_SESSION",
        "mismatched_fields": sorted(mismatches),
        "mismatches": mismatches,
        "checks": {key: key in marker and marker[key] == value for key, value in current.items()},
        "marker_path": str(marker_path),
        "marker_sha256": _b08_diag_sha(marker_raw),
        "marker_matches_reported_install": {
            key: stored_install[key] == value for key, value in _B08_DIAG_REPORTED_INSTALL.items()
        },
        "python_session": {
            "must_be_the_original_failing_notebook": True,
            "execution_context_identity_independently_verified": False,
            "version": platform.python_version(),
            "executable": sys.executable,
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
            "recorded_pid": marker.get("pre_restart_pid"),
            "current_pid": os.getpid(),
            "pid_differs": marker.get("pre_restart_pid") != os.getpid(),
            "prefix_resolution": prefix_resolution,
        },
        "installed_packages": _b08_diag_packages(lock_raw),
        "safety": {
            "files_written": False, "marker_modified": False,
            "package_install_or_restart_executed": False,
            "subprocess_or_network_request_executed": False,
            "controller_or_project_code_executed": False,
            "training_or_integration_executed": False,
        },
        "controller_payload_reverified": False,
        "continuation_authorized_by_this_report": False,
    }


def run_b08_restart_diagnostics() -> None:
    try:
        report = _b08_restart_diagnostic_report(_b08_diag_root(), _B08_DIAG_MARKER_PATH)
    except Exception as error:
        report = {
            "schema_version": _B08_DIAG_SCHEMA,
            "decision": "RESTART_DIAGNOSTIC_READ_FAILED",
            "error_type": type(error).__name__,
            "error_detail": str(error)[-2000:],
            "files_written": False,
            "package_install_or_restart_executed": False,
        }
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    run_b08_restart_diagnostics()
