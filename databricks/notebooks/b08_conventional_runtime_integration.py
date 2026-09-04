# Databricks notebook source
"""Conventional B08 runtime setup and synthetic integration qualification.

Operator flow:

1. Pull the reviewed project snapshot into the Databricks project folder.
2. Attach the DBR 17.3 x86_64 CPU cluster and choose Run all.
3. The first run installs the locked environment and restarts Python.
4. After the restart completes, choose Run all once more.
5. Return only the final JSON object printed by the second run.

This notebook never reads study/test data and never calibrates, trains, performs
inference, or inspects a scientific outcome. Historical Candidate 002/003/004
workflows are outside its scope.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "heterodiff-b08-conventional-runtime-integration-v1"
CONTROLLER_RELATIVE_PATH = (
    "databricks/notebooks/b08_conventional_runtime_integration.py"
)
CONTROLLER_ANCHOR_RELATIVE_PATH = (
    "requirements/b08-conventional-runtime-controller-anchor-v1.json"
)
CONTROLLER_ANCHOR_SCHEMA_VERSION = (
    "heterodiff-b08-conventional-runtime-controller-anchor-v1"
)
CONTROLLER_ANCHOR_RECORD_DOMAIN = (
    b"heterodiff/b08/conventional-runtime-controller-anchor/v1\0"
)
LOCK_RELATIVE_PATH = (
    "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock"
)
SOURCE_MANIFEST_RELATIVE_PATH = (
    "requirements/b08-conventional-runtime-source-manifest-v1.json"
)
EXPECTED_SOURCE_MANIFEST_FILE_SHA256 = (
    "3e472dd77bb18baebf721a9837573e694b33cf82004624ea8c729d3f0f7f403d"
)
SOURCE_MANIFEST_SCHEMA_VERSION = (
    "heterodiff-b08-conventional-runtime-source-manifest-v1"
)
SOURCE_MANIFEST_RECORD_DOMAIN = (
    b"heterodiff/b08/conventional-runtime-source-manifest/v1\0"
)
EXPECTED_LOCK_SHA256 = (
    "c6fa5d600cd2810c40ae47d5eeeba341e0467c4c75dd7c7d310cf3628ab6349f"
)
EXPECTED_DBR_PREFIX = "17.3"
EXPECTED_PYTHON_VERSION = "3.12.3"
EXPECTED_ARCHITECTURE = "x86_64"
EXPECTED_ROUTE_RECEIPT_SHA256 = (
    "eab918f4aa9a58f56466673f5e8bcaefb6180692acbdfd9a6e6a694c2a3b6c4f"
)
EXPECTED_WHOLE_METHOD_RECEIPT_SHA256 = (
    "7f3af61499f4c618daa38d72e38570c4759c5e146eeeef61bb182b9b4f20e102"
)
DURABLE_OUTPUT_DIRECTORY = Path(
    "/Volumes/development/team_eds_supplychain/b08_runtime_output"
)

EXPECTED_ENVIRONMENT = {
    "BLIS_NUM_THREADS": "1",
    "CUDA_VISIBLE_DEVICES": "",
    "LANG": "C",
    "LC_ALL": "C",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONSAFEPATH": "1",
    "PYTHONUTF8": "1",
    "TZ": "UTC",
    "VECLIB_MAXIMUM_THREADS": "1",
}

IMPORT_MODULES = (
    "heterodiff",
    "numpy",
    "scipy",
    "threadpoolctl",
    "torch",
    "pytest",
)

TARGETED_TEST_FILES = (
    "tests/unit/test_configuration_initial_tilt_composer_torch.py",
    "tests/unit/test_plugin_bridge_operational_thinning_loop_route_evidence.py",
    "tests/unit/test_configuration_totalized_jump_potential_composer_torch.py",
    "tests/unit/test_b12_two_domain_adapter_stack.py",
    "tests/unit/test_b12_integration_stack.py",
    "tests/unit/test_b12_whole_method_initializer_path_integration_successor.py",
    "tests/unit/test_formal_test28_30_nonconfirmatory_route_v2.py",
)

WHOLE_METHOD_TEST_FILE = (
    "tests/unit/test_b12_whole_method_initializer_path_integration_successor.py"
)
WHOLE_METHOD_RUNTIME_NEUTRAL_TEST_NAMES = (
    "test_public_receipt_has_exact_core_and_separate_recomputation_parity",
    "test_core_preserves_every_scope_nonclaim_and_only_proposes_beta",
    "test_receipt_recomputes_custody_and_resigned_substitution_fails",
    "test_frozen_empty_initializer_enters_zero_birth_then_test29_death",
    "test_path_calls_actual_test29_cp24_test30_cp23_primitives",
    "test_path_report_and_continuous_custody_digests_recompute",
    "test_transform_is_exactly_typed_dimensioned_and_digest_bound",
    "test_transform_and_path_reject_resigned_state_or_configuration_substitution",
    "test_seed14_actual_initializer_coordinate_drives_first_heun_step",
    "test_runtime_local_initializer_digest_varies_but_semantic_digest_and_core_do_not",
    "test_predecessor_whole_run_is_neither_imported_nor_called",
    "test_captured_independent_ignores_cache_spoof_and_restores_it",
    "test_predecessor_machine_custody_refuses_filesystem_substitution",
    "test_predecessor_machine_baseline_is_exact_and_not_reexecuted",
    "test_sources_are_offline_and_independent_does_not_import_primary",
    "test_direct_public_api_is_explicitly_non_authoritative",
    "test_core_exact_hash_pin_is_stable",
)
WHOLE_METHOD_HISTORICAL_VALIDATOR_TEST_NAMES = (
    "test_authoritative_validator_passes_root_and_unrelated_physical_copy",
    "test_isolated_validator_ignores_and_preserves_all_parent_module_cache_poison",
    "test_isolated_validator_ignores_pythonpath_sitecustomize_cwd_and_shadow_source",
    "test_two_concurrent_isolated_validators_have_identical_receipts",
    "test_authoritative_validator_rejects_workspace_path_and_byte_attacks",
    "test_private_capsule_tamper_fails_before_or_after_execution",
    "test_workspace_replacement_after_child_is_detected",
    "test_isolated_child_failure_and_output_tampering_fail_closed",
)
TARGETED_PYTEST_SELECTORS = (
    *(path for path in TARGETED_TEST_FILES if path != WHOLE_METHOD_TEST_FILE),
    *(
        f"{WHOLE_METHOD_TEST_FILE}::{name}"
        for name in WHOLE_METHOD_RUNTIME_NEUTRAL_TEST_NAMES
    ),
)


class B08ConventionalRuntimeError(RuntimeError):
    """Fail-closed error for this data-free integration workflow."""


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise B08ConventionalRuntimeError(f"{path.name} is not a JSON object")
    return value


def _find_project_root() -> Path:
    seeds: list[Path] = []
    override = os.environ.get("HETERODIFF_PROJECT_ROOT", "").strip()
    if override:
        seeds.append(Path(override))
    seeds.append(Path.cwd())
    source_name = globals().get("__file__")
    if isinstance(source_name, str) and source_name:
        seeds.append(Path(source_name))

    checked: set[str] = set()
    for seed in seeds:
        candidate = seed.expanduser()
        if candidate.is_file():
            candidate = candidate.parent
        for possible in (candidate, *candidate.parents):
            key = str(possible)
            if key in checked:
                continue
            checked.add(key)
            if (
                (possible / "pyproject.toml").is_file()
                and (possible / "src" / "heterodiff").is_dir()
                and (possible / CONTROLLER_ANCHOR_RELATIVE_PATH).is_file()
                and (possible / LOCK_RELATIVE_PATH).is_file()
                and (possible / SOURCE_MANIFEST_RELATIVE_PATH).is_file()
            ):
                return possible.resolve()
    raise B08ConventionalRuntimeError(
        "PROJECT_ROOT_NOT_FOUND: run this notebook from the pulled project folder"
    )


def _run(
    argv: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    environment: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(argv),
        cwd=str(cwd),
        env=dict(environment) if environment is not None else None,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        tail = (result.stderr or result.stdout)[-8000:]
        raise B08ConventionalRuntimeError(
            f"COMMAND_FAILED returncode={result.returncode}: {tail}"
        )
    return result


def _source_manifest_record_sha256(manifest: Mapping[str, Any]) -> str:
    unsigned = dict(manifest)
    unsigned.pop("record_sha256", None)
    return _sha256_bytes(
        SOURCE_MANIFEST_RECORD_DOMAIN + _canonical_json_bytes(unsigned)
    )


def _safe_manifest_relative_path(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise B08ConventionalRuntimeError("SOURCE_MANIFEST_PATH_INVALID")
    relative = PurePosixPath(value)
    if (
        relative.is_absolute()
        or value != relative.as_posix()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise B08ConventionalRuntimeError(
            f"SOURCE_MANIFEST_PATH_INVALID:{value}"
        )
    return relative


def _controller_anchor_record_sha256(anchor: Mapping[str, Any]) -> str:
    unsigned = dict(anchor)
    unsigned.pop("record_sha256", None)
    return _sha256_bytes(
        CONTROLLER_ANCHOR_RECORD_DOMAIN + _canonical_json_bytes(unsigned)
    )


def _load_controller_anchor(project_root: Path) -> dict[str, Any]:
    anchor_path = project_root / CONTROLLER_ANCHOR_RELATIVE_PATH
    raw = anchor_path.read_bytes()
    file_sha256 = _sha256_bytes(raw)
    try:
        anchor = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise B08ConventionalRuntimeError(
            "CONTROLLER_ANCHOR_CANONICAL_JSON_INVALID"
        ) from error
    if not isinstance(anchor, dict):
        raise B08ConventionalRuntimeError("CONTROLLER_ANCHOR_NOT_AN_OBJECT")
    if raw != _canonical_json_bytes(anchor) + b"\n":
        raise B08ConventionalRuntimeError("CONTROLLER_ANCHOR_NOT_CANONICAL")
    if set(anchor) != {
        "schema_version",
        "identity_scope",
        "controller",
        "record_sha256",
    }:
        raise B08ConventionalRuntimeError("CONTROLLER_ANCHOR_SCHEMA_MISMATCH")
    if anchor["schema_version"] != CONTROLLER_ANCHOR_SCHEMA_VERSION:
        raise B08ConventionalRuntimeError(
            "CONTROLLER_ANCHOR_SCHEMA_VERSION_MISMATCH"
        )
    if anchor["identity_scope"] != "EXACT_CONTROLLER_BYTES":
        raise B08ConventionalRuntimeError(
            "CONTROLLER_ANCHOR_IDENTITY_SCOPE_MISMATCH"
        )
    controller = anchor["controller"]
    if not isinstance(controller, dict) or set(controller) != {
        "relative_path",
        "sha256",
        "size_bytes",
    }:
        raise B08ConventionalRuntimeError(
            "CONTROLLER_ANCHOR_CONTROLLER_SCHEMA_MISMATCH"
        )
    relative = _safe_manifest_relative_path(controller["relative_path"])
    if relative.as_posix() != CONTROLLER_RELATIVE_PATH:
        raise B08ConventionalRuntimeError(
            "CONTROLLER_ANCHOR_CONTROLLER_PATH_MISMATCH"
        )
    if re.fullmatch(r"[0-9a-f]{64}", str(controller["sha256"])) is None:
        raise B08ConventionalRuntimeError(
            "CONTROLLER_ANCHOR_CONTROLLER_SHA256_INVALID"
        )
    if type(controller["size_bytes"]) is not int or controller["size_bytes"] <= 0:
        raise B08ConventionalRuntimeError(
            "CONTROLLER_ANCHOR_CONTROLLER_SIZE_INVALID"
        )
    record_sha256 = _controller_anchor_record_sha256(anchor)
    if anchor["record_sha256"] != record_sha256:
        raise B08ConventionalRuntimeError(
            "CONTROLLER_ANCHOR_RECORD_SHA256_MISMATCH"
        )
    controller_path = project_root.joinpath(*relative.parts)
    if controller_path.is_symlink() or not controller_path.is_file():
        raise B08ConventionalRuntimeError(
            "CONTROLLER_ANCHOR_CONTROLLER_FILE_INVALID"
        )
    observed_size = controller_path.stat().st_size
    observed_sha256 = _sha256_file(controller_path)
    if (
        observed_size != controller["size_bytes"]
        or observed_sha256 != controller["sha256"]
    ):
        raise B08ConventionalRuntimeError(
            "CONTROLLER_ANCHOR_CONTROLLER_BINDING_MISMATCH"
        )
    return {
        "relative_path": CONTROLLER_ANCHOR_RELATIVE_PATH,
        "file_sha256": file_sha256,
        "record_sha256": record_sha256,
        "controller": dict(controller),
    }


def _load_source_manifest(project_root: Path) -> dict[str, Any]:
    manifest_path = project_root / SOURCE_MANIFEST_RELATIVE_PATH
    raw = manifest_path.read_bytes()
    file_sha256 = _sha256_bytes(raw)
    if re.fullmatch(r"[0-9a-f]{64}", EXPECTED_SOURCE_MANIFEST_FILE_SHA256) is None:
        raise B08ConventionalRuntimeError(
            "EXPECTED_SOURCE_MANIFEST_FILE_SHA256_NOT_CONFIGURED"
        )
    if file_sha256 != EXPECTED_SOURCE_MANIFEST_FILE_SHA256:
        raise B08ConventionalRuntimeError("SOURCE_MANIFEST_FILE_SHA256_MISMATCH")
    try:
        manifest = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise B08ConventionalRuntimeError(
            "SOURCE_MANIFEST_CANONICAL_JSON_INVALID"
        ) from error
    if not isinstance(manifest, dict):
        raise B08ConventionalRuntimeError("SOURCE_MANIFEST_NOT_AN_OBJECT")
    if raw != _canonical_json_bytes(manifest) + b"\n":
        raise B08ConventionalRuntimeError("SOURCE_MANIFEST_NOT_CANONICAL")
    required_keys = {
        "schema_version",
        "selection",
        "files",
        "file_count",
        "total_size_bytes",
        "record_sha256",
    }
    if set(manifest) != required_keys:
        raise B08ConventionalRuntimeError("SOURCE_MANIFEST_SCHEMA_MISMATCH")
    if manifest["schema_version"] != SOURCE_MANIFEST_SCHEMA_VERSION:
        raise B08ConventionalRuntimeError(
            "SOURCE_MANIFEST_SCHEMA_VERSION_MISMATCH"
        )
    if not isinstance(manifest["selection"], dict):
        raise B08ConventionalRuntimeError("SOURCE_MANIFEST_SELECTION_INVALID")
    files = manifest["files"]
    if not isinstance(files, list) or not files:
        raise B08ConventionalRuntimeError("SOURCE_MANIFEST_FILES_INVALID")

    normalized_paths: list[str] = []
    computed_total = 0
    for record in files:
        if not isinstance(record, dict) or set(record) != {
            "relative_path",
            "sha256",
            "size_bytes",
            "mode_octal",
        }:
            raise B08ConventionalRuntimeError(
                "SOURCE_MANIFEST_FILE_RECORD_SCHEMA_MISMATCH"
            )
        relative = _safe_manifest_relative_path(record["relative_path"])
        if relative.as_posix() == SOURCE_MANIFEST_RELATIVE_PATH:
            raise B08ConventionalRuntimeError(
                "SOURCE_MANIFEST_MUST_NOT_SELECT_ITSELF"
            )
        if re.fullmatch(r"[0-9a-f]{64}", str(record["sha256"])) is None:
            raise B08ConventionalRuntimeError(
                f"SOURCE_MANIFEST_FILE_SHA256_INVALID:{relative}"
            )
        if type(record["size_bytes"]) is not int or record["size_bytes"] < 0:
            raise B08ConventionalRuntimeError(
                f"SOURCE_MANIFEST_FILE_SIZE_INVALID:{relative}"
            )
        if record["mode_octal"] != "0644":
            raise B08ConventionalRuntimeError(
                f"SOURCE_MANIFEST_FILE_MODE_INVALID:{relative}"
            )
        normalized_paths.append(relative.as_posix())
        computed_total += record["size_bytes"]
    if normalized_paths != sorted(normalized_paths):
        raise B08ConventionalRuntimeError("SOURCE_MANIFEST_FILES_NOT_SORTED")
    if len(set(normalized_paths)) != len(normalized_paths):
        raise B08ConventionalRuntimeError("SOURCE_MANIFEST_DUPLICATE_PATH")
    if type(manifest["file_count"]) is not int or manifest["file_count"] != len(files):
        raise B08ConventionalRuntimeError("SOURCE_MANIFEST_FILE_COUNT_MISMATCH")
    if (
        type(manifest["total_size_bytes"]) is not int
        or manifest["total_size_bytes"] != computed_total
    ):
        raise B08ConventionalRuntimeError(
            "SOURCE_MANIFEST_TOTAL_SIZE_MISMATCH"
        )
    required_paths = {"README.md", "pyproject.toml", *TARGETED_TEST_FILES}
    absent_required_paths = sorted(required_paths.difference(normalized_paths))
    if absent_required_paths:
        raise B08ConventionalRuntimeError(
            "SOURCE_MANIFEST_REQUIRED_PATH_ABSENT:"
            + ",".join(absent_required_paths)
        )
    live_source_paths = sorted(
        path.relative_to(project_root).as_posix()
        for path in (project_root / "src" / "heterodiff").rglob("*.py")
        if path.is_file()
    )
    selected_source_paths = sorted(
        path for path in normalized_paths if path.startswith("src/heterodiff/")
    )
    if selected_source_paths != live_source_paths:
        raise B08ConventionalRuntimeError(
            "SOURCE_MANIFEST_PYTHON_SOURCE_CLOSURE_MISMATCH"
        )
    record_sha256 = _source_manifest_record_sha256(manifest)
    if manifest["record_sha256"] != record_sha256:
        raise B08ConventionalRuntimeError(
            "SOURCE_MANIFEST_RECORD_SHA256_MISMATCH"
        )
    return {
        "manifest": manifest,
        "relative_path": SOURCE_MANIFEST_RELATIVE_PATH,
        "file_sha256": file_sha256,
        "record_sha256": record_sha256,
        "file_count": len(files),
        "total_size_bytes": computed_total,
    }


def _verify_source_snapshot(
    snapshot_root: Path,
    source_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    root = snapshot_root.resolve()
    verified_records: list[dict[str, Any]] = []
    for record in source_manifest["manifest"]["files"]:
        relative = _safe_manifest_relative_path(record["relative_path"])
        path = root.joinpath(*relative.parts)
        cursor = root
        for part in relative.parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise B08ConventionalRuntimeError(
                    f"SOURCE_SNAPSHOT_SYMLINK_REJECTED:{relative}"
                )
        if not path.is_file():
            raise B08ConventionalRuntimeError(
                f"SOURCE_SNAPSHOT_FILE_ABSENT:{relative}"
            )
        if path.resolve().parent != path.parent.resolve():
            raise B08ConventionalRuntimeError(
                f"SOURCE_SNAPSHOT_PARENT_IDENTITY_MISMATCH:{relative}"
            )
        size_bytes = path.stat().st_size
        sha256 = _sha256_file(path)
        if size_bytes != record["size_bytes"] or sha256 != record["sha256"]:
            raise B08ConventionalRuntimeError(
                f"SOURCE_SNAPSHOT_FILE_BINDING_MISMATCH:{relative}"
            )
        verified_records.append(
            {
                "relative_path": relative.as_posix(),
                "sha256": sha256,
                "size_bytes": size_bytes,
                "mode_octal": "0644",
            }
        )
    projection = {
        "source_manifest_record_sha256": source_manifest["record_sha256"],
        "files": verified_records,
        "file_count": len(verified_records),
        "total_size_bytes": sum(
            record["size_bytes"] for record in verified_records
        ),
    }
    return {
        **projection,
        "verification_sha256": _sha256_bytes(
            _canonical_json_bytes(projection)
        ),
    }


def _stage_source_snapshot(
    project_root: Path,
    source_manifest: Mapping[str, Any],
    staging_root: Path,
) -> Path:
    _verify_source_snapshot(project_root, source_manifest)
    source_root = staging_root / "source"
    source_root.mkdir()
    for record in source_manifest["manifest"]["files"]:
        relative = _safe_manifest_relative_path(record["relative_path"])
        source = project_root.joinpath(*relative.parts)
        destination = source_root.joinpath(*relative.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o644)
    _verify_source_snapshot(source_root, source_manifest)
    return source_root


def _lock_versions(lock_path: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    pattern = re.compile(r"^([A-Za-z0-9_.-]+)==([^ ]+)")
    for raw_line in lock_path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(raw_line.strip())
        if match is None:
            continue
        name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
        version = match.group(2).rstrip("\\")
        if name in versions:
            raise B08ConventionalRuntimeError(f"DUPLICATE_LOCK_PIN:{name}")
        versions[name] = version
    if len(versions) != 21:
        raise B08ConventionalRuntimeError(
            f"LOCK_PIN_COUNT_MISMATCH:{len(versions)}"
        )
    return versions


def _runtime_preflight(project_root: Path) -> dict[str, Any]:
    controller_anchor = _load_controller_anchor(project_root)
    lock_path = project_root / LOCK_RELATIVE_PATH
    lock_sha256 = _sha256_file(lock_path)
    if lock_sha256 != EXPECTED_LOCK_SHA256:
        raise B08ConventionalRuntimeError("LOCK_SHA256_MISMATCH")
    source_manifest = _load_source_manifest(project_root)
    live_source_verification = _verify_source_snapshot(
        project_root, source_manifest
    )

    observed_environment = {
        name: os.environ.get(name) for name in EXPECTED_ENVIRONMENT
    }
    environment_mismatches = {
        name: {"expected": expected, "observed": observed_environment[name]}
        for name, expected in EXPECTED_ENVIRONMENT.items()
        if observed_environment[name] != expected
    }
    if environment_mismatches:
        raise B08ConventionalRuntimeError(
            "DETERMINISTIC_ENVIRONMENT_MISMATCH:"
            + json.dumps(environment_mismatches, sort_keys=True)
        )

    dbr_version = os.environ.get("DATABRICKS_RUNTIME_VERSION", "")
    checks = {
        "databricks_runtime": dbr_version.startswith(EXPECTED_DBR_PREFIX),
        "python": platform.python_version() == EXPECTED_PYTHON_VERSION,
        "system": platform.system() == "Linux",
        "architecture": platform.machine() == EXPECTED_ARCHITECTURE,
        "byteorder": sys.byteorder == "little",
        "durable_output_directory": DURABLE_OUTPUT_DIRECTORY.is_dir(),
    }
    failures = sorted(name for name, passed in checks.items() if not passed)
    if failures:
        raise B08ConventionalRuntimeError(
            "RUNTIME_PREFLIGHT_FAILED:" + ",".join(failures)
        )
    return {
        "checks": checks,
        "databricks_runtime": dbr_version,
        "python_version": platform.python_version(),
        "system": platform.system(),
        "architecture": platform.machine(),
        "environment": observed_environment,
        "controller_anchor": controller_anchor,
        "lock_sha256": lock_sha256,
        "lock_versions": _lock_versions(lock_path),
        "source_manifest": source_manifest,
        "live_source_verification": live_source_verification,
    }


def _marker_path(source_manifest_record_sha256: str) -> Path:
    return Path("/tmp") / (
        "heterodiff-b08-conventional-"
        f"{source_manifest_record_sha256[:16]}-"
        f"{EXPECTED_LOCK_SHA256[:16]}.json"
    )


def _install_and_restart(
    project_root: Path,
    preflight: Mapping[str, Any],
    marker_path: Path,
) -> None:
    source_manifest = preflight["source_manifest"]
    environment = dict(os.environ)
    environment.update(
        {
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INPUT": "1",
            "SOURCE_DATE_EPOCH": str(
                max(
                    315532800,
                    int(source_manifest["record_sha256"][:8], 16),
                )
            ),
        }
    )
    lock_path = project_root / LOCK_RELATIVE_PATH

    _run(
        (
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--force-reinstall",
            "--only-binary=:all:",
            "--require-hashes",
            "-r",
            str(lock_path),
        ),
        cwd=project_root,
        timeout_seconds=3600,
        environment=environment,
    )

    staging_root = Path(tempfile.mkdtemp(prefix="heterodiff-b08-", dir="/tmp"))
    wheel_root = staging_root / "wheel"
    wheel_root.mkdir()
    source_root = _stage_source_snapshot(
        project_root, source_manifest, staging_root
    )

    _run(
        (
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(wheel_root),
            str(source_root),
        ),
        cwd=staging_root,
        timeout_seconds=900,
        environment=environment,
    )
    wheels = tuple(wheel_root.glob("heterodiff-0.1.0-*.whl"))
    if len(wheels) != 1:
        raise B08ConventionalRuntimeError(
            f"PROJECT_WHEEL_COUNT_MISMATCH:{len(wheels)}"
        )
    wheel_path = wheels[0]
    wheel_sha256 = _sha256_file(wheel_path)
    _run(
        (
            sys.executable,
            "-m",
            "pip",
            "install",
            "--force-reinstall",
            "--no-deps",
            str(wheel_path),
        ),
        cwd=staging_root,
        timeout_seconds=300,
        environment=environment,
    )

    marker = {
        "schema_version": SCHEMA_VERSION,
        "state": "INSTALL_COMPLETE_RESTART_REQUIRED",
        "controller_anchor": preflight["controller_anchor"],
        "source_manifest_relative_path": source_manifest["relative_path"],
        "source_manifest_file_sha256": source_manifest["file_sha256"],
        "source_manifest_record_sha256": source_manifest["record_sha256"],
        "lock_sha256": preflight["lock_sha256"],
        "project_wheel_name": wheel_path.name,
        "project_wheel_sha256": wheel_sha256,
        "python_prefix": sys.prefix,
        "pre_restart_pid": os.getpid(),
        "staging_root": str(staging_root),
    }
    marker_path.write_bytes(_canonical_json_bytes(marker) + b"\n")
    print(
        json.dumps(
            {
                "decision": "INSTALL_COMPLETE_RESTARTING_PYTHON",
                "controller_sha256": preflight["controller_anchor"][
                    "controller"
                ]["sha256"],
                "source_manifest_record_sha256": source_manifest[
                    "record_sha256"
                ],
                "lock_sha256": preflight["lock_sha256"],
                "project_wheel_sha256": wheel_sha256,
                "next_action": "After Python restarts, choose Run all once more.",
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )

    databricks_utilities = globals().get("dbutils")
    if databricks_utilities is None:
        raise B08ConventionalRuntimeError(
            "DATABRICKS_RESTART_API_UNAVAILABLE: restart Python manually"
        )
    databricks_utilities.library.restartPython()
    raise B08ConventionalRuntimeError("PYTHON_RESTART_RETURNED_UNEXPECTEDLY")


def _validated_marker(
    marker_path: Path,
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    marker = _read_json(marker_path)
    required = {
        "schema_version",
        "state",
        "controller_anchor",
        "source_manifest_relative_path",
        "source_manifest_file_sha256",
        "source_manifest_record_sha256",
        "lock_sha256",
        "project_wheel_name",
        "project_wheel_sha256",
        "python_prefix",
        "pre_restart_pid",
        "staging_root",
    }
    if set(marker) != required:
        raise B08ConventionalRuntimeError("RESTART_MARKER_SCHEMA_MISMATCH")
    if (
        marker["schema_version"] != SCHEMA_VERSION
        or marker["state"] != "INSTALL_COMPLETE_RESTART_REQUIRED"
        or marker["controller_anchor"] != preflight["controller_anchor"]
        or marker["source_manifest_relative_path"]
        != preflight["source_manifest"]["relative_path"]
        or marker["source_manifest_file_sha256"]
        != preflight["source_manifest"]["file_sha256"]
        or marker["source_manifest_record_sha256"]
        != preflight["source_manifest"]["record_sha256"]
        or marker["lock_sha256"] != preflight["lock_sha256"]
        or marker["python_prefix"] != sys.prefix
    ):
        raise B08ConventionalRuntimeError("RESTART_MARKER_BINDING_MISMATCH")
    if type(marker["pre_restart_pid"]) is not int:
        raise B08ConventionalRuntimeError("RESTART_MARKER_PID_INVALID")
    if marker["pre_restart_pid"] == os.getpid():
        raise B08ConventionalRuntimeError(
            "PYTHON_WAS_NOT_RESTARTED: wait for restart, then choose Run all"
        )
    if re.fullmatch(r"[0-9a-f]{64}", marker["project_wheel_sha256"]) is None:
        raise B08ConventionalRuntimeError("PROJECT_WHEEL_SHA256_INVALID")

    wheel_path = (
        Path(marker["staging_root"]) / "wheel" / marker["project_wheel_name"]
    )
    if (
        not wheel_path.is_file()
        or _sha256_file(wheel_path) != marker["project_wheel_sha256"]
    ):
        raise B08ConventionalRuntimeError("PROJECT_WHEEL_RESTART_BINDING_MISMATCH")
    _verify_source_snapshot(
        Path(marker["staging_root"]) / "source",
        preflight["source_manifest"],
    )
    return marker


def _sanitized_path(path_value: str, project_root: Path) -> str:
    if path_value in {"built-in", "frozen"}:
        return path_value
    path = Path(path_value)
    roots = (
        ("<PYTHON_PREFIX>", Path(sys.prefix)),
        ("<PROJECT_ROOT>", project_root),
        ("<DATABRICKS_PYTHON>", Path("/databricks/python3")),
        ("<SYSTEM_PYTHON>", Path("/usr/local/lib/python3.12")),
    )
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    for label, root in roots:
        try:
            relative = resolved.relative_to(root.resolve())
        except (OSError, ValueError):
            continue
        return str(Path(label) / relative)
    return f"<EXTERNAL>/{path.name}"


def _installed_environment(
    project_root: Path, lock_versions: Mapping[str, str]
) -> dict[str, Any]:
    observed_versions: dict[str, str] = {}
    distribution_roots: dict[str, dict[str, Any]] = {}
    mismatches: dict[str, dict[str, str]] = {}
    active_prefix = Path(sys.prefix).resolve()
    for name, expected in sorted(lock_versions.items()):
        try:
            distribution = importlib.metadata.distribution(name)
        except importlib.metadata.PackageNotFoundError as error:
            raise B08ConventionalRuntimeError(
                f"LOCKED_DISTRIBUTION_ABSENT:{name}"
            ) from error
        observed = distribution.version
        observed_versions[name] = observed
        if observed != expected:
            mismatches[name] = {"expected": expected, "observed": observed}
        distribution_root = Path(distribution.locate_file("")).resolve()
        try:
            distribution_root.relative_to(active_prefix)
            under_active_prefix = True
        except ValueError:
            under_active_prefix = False
        if not under_active_prefix:
            raise B08ConventionalRuntimeError(
                f"DISTRIBUTION_OUTSIDE_ACTIVE_PREFIX:{name}"
            )
        distribution_roots[name] = {
            "version": observed,
            "distribution_root": _sanitized_path(
                str(distribution_root), project_root
            ),
            "under_active_python_prefix": True,
        }
    if mismatches:
        raise B08ConventionalRuntimeError(
            "INSTALLED_VERSION_MISMATCH:" + json.dumps(mismatches, sort_keys=True)
        )

    project_version = importlib.metadata.version("heterodiff")
    if project_version != "0.1.0":
        raise B08ConventionalRuntimeError(
            f"HETERODIFF_VERSION_MISMATCH:{project_version}"
        )

    import_origins: dict[str, dict[str, Any]] = {}
    for module_name in IMPORT_MODULES:
        specification = importlib.util.find_spec(module_name)
        if specification is None or not specification.origin:
            raise B08ConventionalRuntimeError(
                f"IMPORT_ORIGIN_UNAVAILABLE:{module_name}"
            )
        origin = Path(specification.origin).resolve()
        try:
            origin.relative_to(active_prefix)
            under_active_prefix = True
        except ValueError:
            under_active_prefix = False
        if not under_active_prefix:
            raise B08ConventionalRuntimeError(
                f"IMPORT_OUTSIDE_ACTIVE_PREFIX:{module_name}"
            )
        import_origins[module_name] = {
            "origin": _sanitized_path(str(origin), project_root),
            "under_active_python_prefix": True,
        }

    pip_check = _run(
        (sys.executable, "-m", "pip", "check"),
        cwd=project_root,
        timeout_seconds=180,
        environment=dict(os.environ),
    )
    pip_check_text = (pip_check.stdout + pip_check.stderr).strip()
    return {
        "lock_pin_count": len(lock_versions),
        "locked_versions": observed_versions,
        "locked_distribution_roots": distribution_roots,
        "all_locked_distributions_under_active_python_prefix": (
            len(distribution_roots) == len(lock_versions) == 21
        ),
        "heterodiff_version": project_version,
        "import_origins": import_origins,
        "pip_check_returncode": pip_check.returncode,
        "pip_check_output_sha256": _sha256_bytes(
            pip_check_text.encode("utf-8")
        ),
    }


def _configure_and_verify_cpu_runtime() -> dict[str, Any]:
    import threadpoolctl
    import torch

    if torch.cuda.is_available() or torch.cuda.device_count() != 0:
        raise B08ConventionalRuntimeError("CUDA_MUST_REMAIN_UNAVAILABLE")
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        if torch.get_num_interop_threads() != 1:
            raise
    torch.use_deterministic_algorithms(True)

    pools = []
    for item in threadpoolctl.threadpool_info():
        projected = {
            "internal_api": item.get("internal_api"),
            "prefix": item.get("prefix"),
            "user_api": item.get("user_api"),
            "num_threads": item.get("num_threads"),
            "version": item.get("version"),
        }
        threads = projected["num_threads"]
        if type(threads) is int and threads > 1:
            raise B08ConventionalRuntimeError(
                "NATIVE_THREADPOOL_EXCEEDS_ONE:"
                + json.dumps(projected, sort_keys=True)
            )
        pools.append(projected)
    return {
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "torch_num_threads": torch.get_num_threads(),
        "torch_num_interop_threads": torch.get_num_interop_threads(),
        "deterministic_algorithms_enabled": (
            torch.are_deterministic_algorithms_enabled()
        ),
        "native_threadpools": pools,
    }


def _read_linux_value(path: Path, prefix: str) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in lines:
        if line.startswith(prefix):
            return line.split(":", 1)[-1].strip()
    return None


def _spark_configuration_value(key: str) -> str | None:
    spark_session = globals().get("spark")
    if spark_session is None:
        return None
    try:
        value = spark_session.conf.get(key, None)
    except Exception:
        return None
    if value is None:
        return None
    return str(value)


def _runtime_manifest(
    project_root: Path,
    cpu_runtime: Mapping[str, Any],
) -> dict[str, Any]:
    spark_session = globals().get("spark")
    spark_version = None
    spark_master = None
    executor_process_count = None
    if spark_session is not None:
        spark_version = str(spark_session.version)
        try:
            spark_master = str(spark_session.sparkContext.master)
        except Exception:
            spark_master = None
        try:
            statuses = (
                spark_session.sparkContext._jsc.sc().getExecutorMemoryStatus()
            )
            executor_process_count = int(statuses.size())
        except Exception:
            executor_process_count = None

    disk = shutil.disk_usage("/tmp")
    return {
        "operator_declarations": {
            "cloud_provider": "AWS",
            "runtime_route": "DATABRICKS_DEDICATED_SINGLE_NODE_X86_64_CPU",
            "evidence_class": "OPERATOR_DECLARED_NOT_RUNTIME_OBSERVED",
        },
        "databricks_runtime": os.environ.get("DATABRICKS_RUNTIME_VERSION"),
        "spark_version": spark_version,
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "cache_tag": sys.implementation.cache_tag,
            "byteorder": sys.byteorder,
            "prefix": "<PYTHON_PREFIX>",
        },
        "operating_system": {
            "family": platform.system(),
            "release": platform.release(),
            "distribution": platform.freedesktop_os_release().get("PRETTY_NAME"),
            "architecture": platform.machine(),
        },
        "hardware": {
            "configured_node_type": _spark_configuration_value(
                "spark.databricks.clusterUsageTags.clusterNodeType"
            ),
            "configured_driver_node_type": _spark_configuration_value(
                "spark.databricks.clusterUsageTags.driverNodeType"
            ),
            "cpu_count": os.cpu_count(),
            "cpu_model": _read_linux_value(Path("/proc/cpuinfo"), "model name"),
            "memory_total": _read_linux_value(Path("/proc/meminfo"), "MemTotal"),
            "cuda_observation": {
                "observation_source": "TORCH_RUNTIME_API",
                "cuda_available": cpu_runtime["cuda_available"],
                "cuda_device_count": cpu_runtime["cuda_device_count"],
            },
        },
        "topology": {
            "data_security_mode_if_exposed": _spark_configuration_value(
                "spark.databricks.clusterUsageTags.dataSecurityMode"
            ),
            "cluster_profile": _spark_configuration_value(
                "spark.databricks.cluster.profile"
            ),
            "spark_master": spark_master,
            "executor_process_count_including_driver_if_reported": (
                executor_process_count
            ),
        },
        "storage_roles": {
            "transient_root": "/tmp",
            "transient_available_bytes": disk.free,
            "transient_total_bytes": disk.total,
            "durable_output_directory": str(DURABLE_OUTPUT_DIRECTORY),
            "study_or_test_data_path_requested": False,
        },
        "project_root": "<PROJECT_ROOT>",
    }


def _run_targeted_tests(project_root: Path) -> dict[str, Any]:
    missing = [
        name for name in TARGETED_TEST_FILES if not (project_root / name).is_file()
    ]
    if missing:
        raise B08ConventionalRuntimeError(
            "TARGETED_TEST_FILE_ABSENT:" + ",".join(missing)
        )
    test_root = Path(tempfile.mkdtemp(prefix="heterodiff-b08-tests-", dir="/tmp"))
    pytest_config = test_root / "pytest.ini"
    pytest_config.write_text("[pytest]\naddopts = -ra\n", encoding="utf-8")
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTEST_ADDOPTS", None)
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    result = _run(
        (
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-c",
            str(pytest_config),
            "--basetemp",
            str(test_root / "tmp"),
            *TARGETED_PYTEST_SELECTORS,
        ),
        cwd=project_root,
        timeout_seconds=3600,
        environment=environment,
    )
    output = (result.stdout + result.stderr).strip()
    matches = re.findall(r"(\d+) passed", output)
    if not matches:
        raise B08ConventionalRuntimeError("PYTEST_PASS_COUNT_NOT_FOUND")
    return {
        "returncode": result.returncode,
        "passed": int(matches[-1]),
        "test_file_count": len(TARGETED_TEST_FILES),
        "test_files": list(TARGETED_TEST_FILES),
        "pytest_selector_count": len(TARGETED_PYTEST_SELECTORS),
        "pytest_selectors": list(TARGETED_PYTEST_SELECTORS),
        "historical_validator_exclusion": {
            "excluded_expanded_item_count": 18,
            "excluded_function_count": len(
                WHOLE_METHOD_HISTORICAL_VALIDATOR_TEST_NAMES
            ),
            "excluded_function_names": list(
                WHOLE_METHOD_HISTORICAL_VALIDATOR_TEST_NAMES
            ),
            "reason": (
                "HISTORICAL_CPYTHON3115_VENV_M1_VALIDATOR_NOT_PORTABLE_"
                "TO_DBR17_3_PY312"
            ),
            "validator_rerun_claimed": False,
        },
        "output_sha256": _sha256_bytes(output.encode("utf-8")),
    }


def _contains_string(value: Any, expected: str) -> bool:
    if isinstance(value, str):
        return value == expected
    if isinstance(value, Mapping):
        return any(_contains_string(item, expected) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_string(item, expected) for item in value)
    return False


def _run_synthetic_smoke(project_root: Path) -> dict[str, Any]:
    from heterodiff.evaluation import formal_test28_30_nonconfirmatory_route_v2

    route = formal_test28_30_nonconfirmatory_route_v2
    receipt = route.run_nonconfirmatory_test28_30_route_v2(str(project_root))
    route.validate_nonconfirmatory_test28_30_route_v2_receipt(receipt)
    plain = dataclasses.asdict(receipt)
    if receipt.receipt_sha256 != EXPECTED_ROUTE_RECEIPT_SHA256:
        raise B08ConventionalRuntimeError("SYNTHETIC_ROUTE_RECEIPT_MISMATCH")
    if not _contains_string(plain, EXPECTED_WHOLE_METHOD_RECEIPT_SHA256):
        raise B08ConventionalRuntimeError(
            "NESTED_WHOLE_METHOD_RECEIPT_MISMATCH"
        )
    canonical = route.route_v2_receipt_canonical_json_bytes(receipt)
    return {
        "route_receipt_sha256": receipt.receipt_sha256,
        "nested_whole_method_receipt_sha256": (
            EXPECTED_WHOLE_METHOD_RECEIPT_SHA256
        ),
        "canonical_receipt_bytes_sha256": _sha256_bytes(canonical),
        "formal_test_states": [
            receipt.formal_test_28_state,
            receipt.formal_test_29_state,
            receipt.formal_test_30_state,
        ],
        "science_executed": receipt.science_executed,
        "production_receipt_issued": receipt.production_receipt_issued,
        "tracker_or_ledger_edited": receipt.tracker_or_ledger_edited,
    }


def _write_final_receipt(receipt: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    unsigned = dict(receipt)
    unsigned["record_sha256_scope"] = (
        "CANONICAL_JSON_WITHOUT_RECORD_SHA256_OR_DURABLE_RECEIPT_PATH"
    )
    unsigned["durable_write_verified"] = True
    record_sha256 = _sha256_bytes(_canonical_json_bytes(unsigned))
    output_path = DURABLE_OUTPUT_DIRECTORY / (
        "b08-conventional-runtime-integration-"
        f"{receipt['project']['source_manifest_record_sha256'][:12]}-"
        f"{record_sha256[:16]}.json"
    )
    completed = dict(unsigned)
    completed["record_sha256"] = record_sha256
    completed["durable_receipt_path"] = str(output_path)
    raw = _canonical_json_bytes(completed) + b"\n"
    output_path.write_bytes(raw)
    if output_path.read_bytes() != raw:
        raise B08ConventionalRuntimeError("DURABLE_RECEIPT_READBACK_MISMATCH")
    return completed, output_path


def _verify_and_integrate(
    project_root: Path,
    preflight: Mapping[str, Any],
    marker: Mapping[str, Any],
) -> dict[str, Any]:
    source_manifest = preflight["source_manifest"]
    staged_source_root = Path(marker["staging_root"]) / "source"
    live_verification_before = _verify_source_snapshot(
        project_root, source_manifest
    )
    staged_verification_before = _verify_source_snapshot(
        staged_source_root, source_manifest
    )
    installed = _installed_environment(
        project_root, preflight["lock_versions"]
    )
    cpu_runtime = _configure_and_verify_cpu_runtime()
    tests = _run_targeted_tests(staged_source_root)
    synthetic = _run_synthetic_smoke(staged_source_root)

    final_controller_anchor = _load_controller_anchor(project_root)
    if final_controller_anchor != preflight["controller_anchor"]:
        raise B08ConventionalRuntimeError(
            "CONTROLLER_ANCHOR_CHANGED_DURING_RUN"
        )

    final_source_manifest = _load_source_manifest(project_root)
    if (
        final_source_manifest["file_sha256"] != source_manifest["file_sha256"]
        or final_source_manifest["record_sha256"]
        != source_manifest["record_sha256"]
    ):
        raise B08ConventionalRuntimeError(
            "SOURCE_MANIFEST_CHANGED_DURING_RUN"
        )
    live_verification_after = _verify_source_snapshot(
        project_root, final_source_manifest
    )
    staged_verification_after = _verify_source_snapshot(
        staged_source_root, source_manifest
    )
    if (
        live_verification_before["verification_sha256"]
        != live_verification_after["verification_sha256"]
        or staged_verification_before["verification_sha256"]
        != staged_verification_after["verification_sha256"]
        or live_verification_after["verification_sha256"]
        != staged_verification_after["verification_sha256"]
    ):
        raise B08ConventionalRuntimeError(
            "SOURCE_SNAPSHOT_CHANGED_OR_STAGED_SNAPSHOT_DIFFERS"
        )
    runtime_manifest = _runtime_manifest(project_root, cpu_runtime)
    runtime_manifest_sha256 = _sha256_bytes(
        _canonical_json_bytes(runtime_manifest)
    )
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "decision": "PASS_CONVENTIONAL_RUNTIME_AND_SYNTHETIC_INTEGRATION",
        "captured_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": "DATA_FREE_RUNTIME_QUALIFICATION_AND_SYNTHETIC_INTEGRATION_ONLY",
        "project": {
            "controller_anchor": final_controller_anchor,
            "source_manifest_relative_path": source_manifest["relative_path"],
            "source_manifest_file_sha256": source_manifest["file_sha256"],
            "source_manifest_record_sha256": source_manifest[
                "record_sha256"
            ],
            "source_manifest_file_count": source_manifest["file_count"],
            "source_manifest_total_size_bytes": source_manifest[
                "total_size_bytes"
            ],
            "live_source_verified_before_and_after": True,
            "staged_source_verified_before_and_after": True,
            "live_source_verification_sha256": live_verification_after[
                "verification_sha256"
            ],
            "staged_source_verification_sha256": staged_verification_after[
                "verification_sha256"
            ],
            "lock_relative_path": LOCK_RELATIVE_PATH,
            "lock_sha256": preflight["lock_sha256"],
            "project_wheel_name": marker["project_wheel_name"],
            "project_wheel_sha256": marker["project_wheel_sha256"],
        },
        "runtime_manifest": runtime_manifest,
        "runtime_manifest_sha256": runtime_manifest_sha256,
        "deterministic_environment": preflight["environment"],
        "installed_environment": installed,
        "cpu_determinism": cpu_runtime,
        "targeted_integration_tests": tests,
        "synthetic_whole_method_smoke": synthetic,
        "project_delta": {
            "fields_closed": 0,
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "result_slots_filled": 0,
            "timetable_or_ledger_edited": False,
            "b08_closed": False,
        },
        "safety": {
            "dependency_network_access_authorized": True,
            "dependency_network_access_may_have_occurred": True,
            "study_or_test_data_accessed": False,
            "calibration_executed": False,
            "training_executed": False,
            "inference_executed": False,
            "scientific_outcome_inspected": False,
            "candidate_002_003_or_004_executed": False,
        },
        "not_proven_by_this_run": [
            "B08_CLOSURE",
            "COMPUTE_AND_STORAGE_CEILING_ACCEPTANCE",
            "REAL_DATA_READINESS",
            "PRODUCTION_TRAINING_PORTABILITY",
            "FORMAL_TEST_28_29_OR_30_CLOSURE",
            "SCIENTIFIC_RESULT",
        ],
    }
    completed, output_path = _write_final_receipt(receipt)
    if not output_path.is_file():
        raise B08ConventionalRuntimeError("DURABLE_RECEIPT_MISSING_AFTER_WRITE")
    return completed


def _sanitized_error_detail(error: BaseException, project_root: Path | None) -> str:
    detail = str(error)
    replacements = [(sys.prefix, "<PYTHON_PREFIX>")]
    if project_root is not None:
        replacements.append((str(project_root), "<PROJECT_ROOT>"))
    for source, replacement in replacements:
        if source:
            detail = detail.replace(source, replacement)
    return detail[-8000:]


def main() -> None:
    project_root: Path | None = None
    try:
        project_root = _find_project_root()
        preflight = _runtime_preflight(project_root)
        marker_path = _marker_path(
            preflight["source_manifest"]["record_sha256"]
        )
        if not marker_path.exists():
            _install_and_restart(project_root, preflight, marker_path)
            return
        marker = _validated_marker(marker_path, preflight)
        receipt = _verify_and_integrate(project_root, preflight, marker)
        print(json.dumps(receipt, indent=2, sort_keys=True), flush=True)
    except Exception as error:
        failure = {
            "schema_version": SCHEMA_VERSION,
            "decision": "STOP_CONVENTIONAL_RUNTIME_OR_INTEGRATION_FAILED",
            "error_type": type(error).__name__,
            "error_detail": _sanitized_error_detail(error, project_root),
            "safety": {
                "study_or_test_data_accessed": False,
                "calibration_executed": False,
                "training_executed": False,
                "inference_executed": False,
                "scientific_outcome_inspected": False,
                "candidate_002_003_or_004_executed": False,
            },
        }
        print(json.dumps(failure, indent=2, sort_keys=True), flush=True)
        raise


if __name__ == "__main__":
    main()
