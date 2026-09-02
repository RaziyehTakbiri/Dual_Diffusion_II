#!/usr/bin/env python3
"""Data-free verifier for the DBR 17.3 Linux x86_64 CPU image candidate.

The verifier performs no network, Spark, subprocess, entropy, dataset, model,
training, inference, or outcome operation.  It validates the offline wheel
closure before importing the numerical runtime, then checks the exact candidate
versions, deterministic process controls, native thread pools, and CPU-only
PyTorch state.

Passing this verifier is image-construction evidence only.  It is not platform
authentication, a storage or capacity reservation, B08 closure, or authority
to access study or test data.
"""

from __future__ import annotations

import hashlib
from importlib import import_module
from importlib import metadata as importlib_metadata
import json
import os
from pathlib import Path
import platform
import re
import stat
import sys
from typing import Any, Mapping, Optional


SCHEMA_VERSION = "heterodiff-b08-databricks-container-verification-v1"
RESOLVED_MANIFEST_SCHEMA = "heterodiff-b08-databricks-container-wheel-manifest-v1"
RESOLVED_MANIFEST_STATE = "RESOLVED_OFFLINE_WHEELHOUSE"
TARGET_PROFILE = "b08-databricks-aws-dbr17.3-linux-x86_64-cpu-py312"

ROOT = Path("/opt/heterodiff")
LOCK_PATH = ROOT / "requirements.lock"
MANIFEST_PATH = ROOT / "wheel-manifest.json"
RUNTIME_PROFILE_PATH = ROOT / "runtime-profile.json"
WHEELHOUSE_PATH = ROOT / "wheelhouse"

EXPECTED_PYTHON = "3.12.3"
EXPECTED_DISTRIBUTIONS = {
    "heterodiff": "0.1.0",
    "numpy": "2.4.6",
    "scipy": "1.17.1",
    "threadpoolctl": "3.6.0",
    "torch": "2.12.1+cpu",
}
EXPECTED_PROJECT_WHEEL_FILENAME = "heterodiff-0.1.0-py3-none-any.whl"
EXPECTED_PROJECT_REQUIREMENT = "heterodiff==0.1.0"
EXPECTED_PROJECT_WHEEL_PATH = (
    "requirements/wheelhouse/"
    "b08-databricks-aws-dbr17.3-x86_64-cpu-py312/" + EXPECTED_PROJECT_WHEEL_FILENAME
)
BUILD_INPUTS_RESOLVED = "BUILD_INPUTS_RESOLVED"
RUNTIME_PROFILE_SCHEMA = "heterodiff-b08-databricks-runtime-profile-v1"
RUNTIME_PROFILE_RECORD_DOMAIN = b"heterodiff/b08/databricks-runtime-profile/v1\0"
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

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_WHEEL_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*\.whl\Z")
_EXACT_REQUIREMENT = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._-]*==[A-Za-z0-9][A-Za-z0-9.!+_-]*\Z"
)
_LOCK_REQUIREMENT_LINE = re.compile(
    r"(?P<requirement>[A-Za-z0-9][A-Za-z0-9._-]*"
    r"==[A-Za-z0-9][A-Za-z0-9.!+_-]*)(?:[ \t]+\\)?\Z"
)
_LOCK_HASH_LINE = re.compile(r"--hash=sha256:[0-9a-f]{64}(?:[ \t]+\\)?\Z")
_MANIFEST_KEYS = {
    "artifacts",
    "lock",
    "record_state",
    "schema_version",
    "target",
}
_ARTIFACT_KEYS = {"filename", "requirement", "role", "sha256", "size_bytes"}
_LOCK_KEYS = {
    "all_artifacts_hash_pinned",
    "all_requirements_exactly_pinned",
    "path",
    "pip_require_hashes_required",
    "sha256",
}


class RuntimeVerificationError(RuntimeError):
    """Fail-closed candidate image verification error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeVerificationError(code)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _validate_lock_bytes(raw: bytes) -> tuple[str, ...]:
    """Accept only exact hash-pinned package requirements, never URLs/paths."""

    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise RuntimeVerificationError("LOCK_NOT_ASCII") from error
    _require(text.endswith("\n") and "\r" not in text, "LOCK_FRAMING_INVALID")
    requirements: list[str] = []
    current_requirement = None
    current_hash_count = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        hash_match = _LOCK_HASH_LINE.fullmatch(line)
        if hash_match is not None:
            _require(current_requirement is not None, "LOCK_HASH_WITHOUT_REQUIREMENT")
            current_hash_count += 1
            continue
        if current_requirement is not None:
            _require(current_hash_count > 0, "LOCK_REQUIREMENT_WITHOUT_HASH")
        requirement_match = _LOCK_REQUIREMENT_LINE.fullmatch(line)
        _require(requirement_match is not None, "LOCK_FORBIDDEN_REQUIREMENT_SYNTAX")
        current_requirement = requirement_match.group("requirement")
        requirements.append(current_requirement)
        current_hash_count = 0
    _require(current_requirement is not None, "LOCK_HAS_NO_REQUIREMENTS")
    _require(current_hash_count > 0, "LOCK_REQUIREMENT_WITHOUT_HASH")
    _require(
        len(requirements) == len(set(requirements)),
        "LOCK_DUPLICATE_REQUIREMENT",
    )
    return tuple(requirements)


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise RuntimeVerificationError("RUNTIME_PROFILE_NOT_CANONICAL") from error


def _load_build_runtime_profile(
    path: Path,
    *,
    base_image_reference: str,
    lock_sha256: str,
    manifest_sha256: str,
    project_wheel_sha256: str,
    torch_wheel_filename: str,
    torch_wheel_sha256: str,
) -> Mapping[str, Any]:
    """Bind resolved build inputs to the canonical intermediate profile."""

    raw = _read_stable_regular_file(path, maximum_bytes=4 * 1024 * 1024)
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeVerificationError("RUNTIME_PROFILE_INVALID_JSON") from error
    _require(type(value) is dict, "RUNTIME_PROFILE_ROOT_NOT_OBJECT")
    _require(
        value.get("schema_version") == RUNTIME_PROFILE_SCHEMA,
        "RUNTIME_PROFILE_SCHEMA_MISMATCH",
    )
    _require(value.get("profile_id") == TARGET_PROFILE, "RUNTIME_PROFILE_ID_MISMATCH")
    _require(
        value.get("lifecycle_state") == BUILD_INPUTS_RESOLVED,
        "RUNTIME_PROFILE_BUILD_INPUTS_NOT_RESOLVED",
    )
    record_sha256 = value.get("record_sha256")
    _require(
        type(record_sha256) is str and _SHA256.fullmatch(record_sha256) is not None,
        "RUNTIME_PROFILE_RECORD_SHA256_FORMAT",
    )
    projection = dict(value)
    projection.pop("record_sha256", None)
    semantic_sha256 = _sha256(
        RUNTIME_PROFILE_RECORD_DOMAIN + _canonical_json_bytes(projection)
    )
    _require(record_sha256 == semantic_sha256, "RUNTIME_PROFILE_RECORD_SHA256_MISMATCH")

    target = value.get("target")
    _require(type(target) is dict, "RUNTIME_PROFILE_TARGET_INVALID")
    expected_target = {
        "architecture": "x86_64",
        "cloud_provider": "AWS",
        "compute_mode": "CLASSIC_DEDICATED",
        "cpu_only": True,
        "databricks_runtime_version": "17.3.x-scala2.13",
        "gpu_enabled": False,
        "operating_system_family": "Linux",
        "python_abi": "cp312",
        "python_implementation": "CPython",
        "python_version": EXPECTED_PYTHON,
        "runtime_engine": "STANDARD",
        "service": "DATABRICKS",
    }
    for key, expected in expected_target.items():
        _require(target.get(key) == expected, "RUNTIME_PROFILE_TARGET_MISMATCH:" + key)

    dependencies = value.get("dependencies")
    _require(type(dependencies) is dict, "RUNTIME_PROFILE_DEPENDENCIES_INVALID")
    _require(
        dependencies.get("expected_distributions") == EXPECTED_DISTRIBUTIONS,
        "RUNTIME_PROFILE_DISTRIBUTIONS_MISMATCH",
    )
    _require(
        dependencies.get("source_wheel_path") == EXPECTED_PROJECT_WHEEL_PATH,
        "RUNTIME_PROFILE_PROJECT_WHEEL_PATH_MISMATCH",
    )
    expected_dependency_values = {
        "lockfile_sha256": lock_sha256,
        "source_wheel_sha256": project_wheel_sha256,
        "wheel_manifest_sha256": manifest_sha256,
        "complete_transitive_lock": True,
        "wheel_manifest_complete": True,
        "all_artifacts_linux_x86_64_cp312_compatible": True,
        "hashes_required_for_every_artifact": True,
        "network_install_during_qualification_permitted": False,
        "sdist_installation_permitted": False,
        "editable_install_permitted": False,
        "user_site_packages_permitted": False,
    }
    for key, expected in expected_dependency_values.items():
        _require(
            dependencies.get(key) == expected,
            "RUNTIME_PROFILE_DEPENDENCY_MISMATCH:" + key,
        )

    torch = value.get("torch")
    _require(type(torch) is dict, "RUNTIME_PROFILE_TORCH_INVALID")
    expected_torch_values = {
        "package_name": "torch",
        "version": EXPECTED_DISTRIBUTIONS["torch"],
        "distribution_variant": "CPU_ONLY",
        "wheel_filename": torch_wheel_filename,
        "wheel_sha256": torch_wheel_sha256,
        "cuda_compiled": False,
        "cuda_available": False,
        "mps_compiled": False,
        "mps_available": False,
    }
    for key, expected in expected_torch_values.items():
        _require(
            torch.get(key) == expected,
            "RUNTIME_PROFILE_TORCH_MISMATCH:" + key,
        )

    container = value.get("container")
    _require(type(container) is dict, "RUNTIME_PROFILE_CONTAINER_INVALID")
    marker = "@sha256:"
    _require(
        type(base_image_reference) is str and base_image_reference.count(marker) == 1,
        "BASE_IMAGE_REFERENCE_NOT_DIGEST_ADDRESSED",
    )
    base_repository, base_digest = base_image_reference.rsplit(marker, 1)
    _require(_SHA256.fullmatch(base_digest) is not None, "BASE_IMAGE_DIGEST_FORMAT")
    _require(
        base_repository == "databricksruntime/standard:17.3-LTS",
        "BASE_IMAGE_REFERENCE_REPOSITORY_MISMATCH",
    )
    _require(
        container.get("base_image_manifest_digest") == "sha256:" + base_digest,
        "RUNTIME_PROFILE_BASE_IMAGE_DIGEST_MISMATCH",
    )
    return {
        "record_sha256": record_sha256,
        "source_wheel_sha256": project_wheel_sha256,
    }


def _read_stable_regular_file(path: Path, *, maximum_bytes: int) -> bytes:
    try:
        before = path.lstat()
    except OSError as error:
        raise RuntimeVerificationError("SUPPLY_CHAIN_FILE_UNAVAILABLE") from error
    _require(stat.S_ISREG(before.st_mode), "SUPPLY_CHAIN_PATH_NOT_REGULAR")
    _require(before.st_nlink == 1, "SUPPLY_CHAIN_LINK_COUNT_NOT_ONE")
    _require(before.st_size > 0, "SUPPLY_CHAIN_FILE_EMPTY")
    _require(before.st_size <= maximum_bytes, "SUPPLY_CHAIN_FILE_TOO_LARGE")
    _require(
        stat.S_IMODE(before.st_mode) & 0o022 == 0,
        "SUPPLY_CHAIN_FILE_GROUP_OR_WORLD_WRITABLE",
    )
    try:
        raw = path.read_bytes()
        after = path.lstat()
    except OSError as error:
        raise RuntimeVerificationError("SUPPLY_CHAIN_FILE_READ_FAILED") from error
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
    _require(identity_before == identity_after, "SUPPLY_CHAIN_FILE_CHANGED")
    _require(len(raw) == before.st_size, "SUPPLY_CHAIN_FILE_TRUNCATED")
    return raw


def _decode_resolved_manifest(raw: bytes) -> Mapping[str, Any]:
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeVerificationError("WHEEL_MANIFEST_INVALID_JSON") from error
    _require(type(value) is dict, "WHEEL_MANIFEST_ROOT_NOT_OBJECT")
    canonical = (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        + b"\n"
    )
    _require(raw == canonical, "WHEEL_MANIFEST_NOT_CANONICAL")
    _require(set(value) == _MANIFEST_KEYS, "WHEEL_MANIFEST_KEY_ROSTER")
    _require(
        value["schema_version"] == RESOLVED_MANIFEST_SCHEMA,
        "WHEEL_MANIFEST_SCHEMA_MISMATCH",
    )
    _require(
        value["record_state"] == RESOLVED_MANIFEST_STATE,
        "WHEEL_MANIFEST_NOT_RESOLVED",
    )
    _require(value["target"] == TARGET_PROFILE, "WHEEL_MANIFEST_TARGET_MISMATCH")
    return value


def _load_resolved_manifest(path: Path) -> Mapping[str, Any]:
    raw = _read_stable_regular_file(path, maximum_bytes=16 * 1024 * 1024)
    return _decode_resolved_manifest(raw)


def verify_offline_wheel_closure(
    *,
    manifest_path: Path = MANIFEST_PATH,
    lock_path: Path = LOCK_PATH,
    wheelhouse_path: Path = WHEELHOUSE_PATH,
    runtime_profile_path: Path = RUNTIME_PROFILE_PATH,
    base_image_reference: Optional[str] = None,
) -> Mapping[str, Any]:
    """Verify the resolved lock and every wheel payload by exact SHA-256."""

    manifest_raw = _read_stable_regular_file(
        manifest_path,
        maximum_bytes=16 * 1024 * 1024,
    )
    manifest = _decode_resolved_manifest(manifest_raw)
    lock = manifest["lock"]
    _require(type(lock) is dict and set(lock) == _LOCK_KEYS, "LOCK_RECORD_SCHEMA")
    _require(
        lock["path"] == "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock",
        "LOCK_RECORD_PATH_MISMATCH",
    )
    for key in (
        "all_artifacts_hash_pinned",
        "all_requirements_exactly_pinned",
        "pip_require_hashes_required",
    ):
        _require(lock[key] is True, "LOCK_RECORD_INCOMPLETE:" + key)
    _require(type(lock["sha256"]) is str, "LOCK_SHA256_TYPE")
    _require(_SHA256.fullmatch(lock["sha256"]) is not None, "LOCK_SHA256_FORMAT")
    lock_raw = _read_stable_regular_file(lock_path, maximum_bytes=4 * 1024 * 1024)
    _require(_sha256(lock_raw) == lock["sha256"], "LOCK_SHA256_MISMATCH")
    locked_requirements = _validate_lock_bytes(lock_raw)

    artifacts = manifest["artifacts"]
    _require(type(artifacts) is list and artifacts, "WHEEL_ARTIFACTS_EMPTY")
    names: list[str] = []
    artifact_requirements: list[str] = []
    artifacts_by_requirement: dict[str, Mapping[str, Any]] = {}
    project_wheel_count = 0
    project_wheel_sha256 = None
    for ordinal, artifact in enumerate(artifacts):
        label = "WHEEL_ARTIFACT:" + str(ordinal)
        _require(type(artifact) is dict, label + ":NOT_OBJECT")
        _require(set(artifact) == _ARTIFACT_KEYS, label + ":KEY_ROSTER")
        name = artifact["filename"]
        _require(type(name) is str, label + ":FILENAME_TYPE")
        _require(_SAFE_WHEEL_NAME.fullmatch(name) is not None, label + ":FILENAME")
        requirement = artifact["requirement"]
        _require(type(requirement) is str, label + ":REQUIREMENT")
        _require(
            _EXACT_REQUIREMENT.fullmatch(requirement) is not None,
            label + ":REQUIREMENT_NOT_EXACT_PIN",
        )
        _require(
            artifact["role"] in {"PROJECT_WHEEL", "RUNTIME_DEPENDENCY"},
            label + ":ROLE",
        )
        if artifact["role"] == "PROJECT_WHEEL":
            project_wheel_count += 1
            _require(
                name == EXPECTED_PROJECT_WHEEL_FILENAME,
                "PROJECT_WHEEL_FILENAME_MISMATCH",
            )
            _require(
                requirement == EXPECTED_PROJECT_REQUIREMENT,
                "PROJECT_WHEEL_REQUIREMENT_MISMATCH",
            )
        digest = artifact["sha256"]
        _require(type(digest) is str, label + ":SHA256_TYPE")
        _require(_SHA256.fullmatch(digest) is not None, label + ":SHA256_FORMAT")
        if artifact["role"] == "PROJECT_WHEEL":
            project_wheel_sha256 = digest
        size = artifact["size_bytes"]
        _require(type(size) is int and size > 0, label + ":SIZE")
        raw = _read_stable_regular_file(
            wheelhouse_path / name,
            maximum_bytes=8 * 1024 * 1024 * 1024,
        )
        _require(len(raw) == size, label + ":SIZE_MISMATCH")
        _require(_sha256(raw) == digest, label + ":SHA256_MISMATCH")
        names.append(name)
        artifact_requirements.append(requirement)
        artifacts_by_requirement[requirement] = artifact
    _require(len(names) == len(set(names)), "WHEEL_ARTIFACT_DUPLICATE")
    _require(
        len(artifact_requirements) == len(set(artifact_requirements)),
        "WHEEL_REQUIREMENT_DUPLICATE",
    )
    _require(project_wheel_count == 1, "PROJECT_WHEEL_COUNT_NOT_ONE")
    _require(
        tuple(sorted(artifact_requirements)) == tuple(sorted(locked_requirements)),
        "LOCK_AND_WHEEL_REQUIREMENT_ROSTERS_DIFFER",
    )
    expected_root_requirements = {
        name + "==" + version for name, version in EXPECTED_DISTRIBUTIONS.items()
    }
    _require(
        expected_root_requirements.issubset(set(artifact_requirements)),
        "EXPECTED_RUNTIME_REQUIREMENT_MISSING",
    )
    try:
        on_disk = sorted(
            path.name for path in wheelhouse_path.iterdir() if path.is_file()
        )
    except OSError as error:
        raise RuntimeVerificationError("WHEELHOUSE_ENUMERATION_FAILED") from error
    _require(on_disk == sorted(names), "WHEELHOUSE_FILE_ROSTER_MISMATCH")
    _require(project_wheel_sha256 is not None, "PROJECT_WHEEL_SHA256_MISSING")
    torch_artifact = artifacts_by_requirement[
        "torch==" + EXPECTED_DISTRIBUTIONS["torch"]
    ]
    if base_image_reference is None:
        base_image_reference = os.environ.get("B08_BASE_IMAGE_REFERENCE", "")
    runtime_profile = _load_build_runtime_profile(
        runtime_profile_path,
        base_image_reference=base_image_reference,
        lock_sha256=lock["sha256"],
        manifest_sha256=_sha256(manifest_raw),
        project_wheel_sha256=project_wheel_sha256,
        torch_wheel_filename=torch_artifact["filename"],
        torch_wheel_sha256=torch_artifact["sha256"],
    )
    return {
        "artifact_count": len(names),
        "lock_sha256": lock["sha256"],
        "project_wheel_sha256": project_wheel_sha256,
        "runtime_profile_record_sha256": runtime_profile["record_sha256"],
        "wheelhouse_complete": True,
    }


def verify_environment(environment: Mapping[str, str]) -> None:
    observed = {name: environment.get(name) for name in EXPECTED_ENVIRONMENT}
    _require(observed == EXPECTED_ENVIRONMENT, "DETERMINISTIC_ENVIRONMENT_MISMATCH")


def _distribution_versions() -> Mapping[str, str]:
    observed: dict[str, str] = {}
    for name in EXPECTED_DISTRIBUTIONS:
        try:
            observed[name] = importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError as error:
            raise RuntimeVerificationError("DISTRIBUTION_MISSING:" + name) from error
    _require(observed == EXPECTED_DISTRIBUTIONS, "DISTRIBUTION_VERSION_MISMATCH")
    return observed


def verify_numerical_runtime() -> Mapping[str, Any]:
    """Import and enforce the exact CPU-only deterministic numerical runtime."""

    _require(platform.system() == "Linux", "PLATFORM_SYSTEM_NOT_LINUX")
    _require(platform.machine() == "x86_64", "PLATFORM_MACHINE_NOT_X86_64")
    _require(
        platform.python_implementation() == "CPython",
        "PYTHON_IMPLEMENTATION_NOT_CPYTHON",
    )
    _require(platform.python_version() == EXPECTED_PYTHON, "PYTHON_VERSION_MISMATCH")
    versions = _distribution_versions()

    numpy = import_module("numpy")
    scipy = import_module("scipy")
    threadpoolctl = import_module("threadpoolctl")
    torch = import_module("torch")
    import_module("heterodiff")

    _require(numpy.__version__ == EXPECTED_DISTRIBUTIONS["numpy"], "NUMPY_DRIFT")
    _require(scipy.__version__ == EXPECTED_DISTRIBUTIONS["scipy"], "SCIPY_DRIFT")
    _require(
        threadpoolctl.__version__ == EXPECTED_DISTRIBUTIONS["threadpoolctl"],
        "THREADPOOLCTL_DRIFT",
    )
    _require(str(torch.__version__) == EXPECTED_DISTRIBUTIONS["torch"], "TORCH_DRIFT")
    _require(torch.version.cuda is None, "TORCH_WHEEL_EXPOSES_CUDA_BUILD")
    _require(torch.cuda.is_available() is False, "TORCH_CUDA_AVAILABLE")
    _require(torch.cuda.device_count() == 0, "TORCH_CUDA_DEVICE_COUNT_NONZERO")
    mps = getattr(torch.backends, "mps", None)
    if mps is not None:
        _require(mps.is_available() is False, "TORCH_MPS_AVAILABLE")

    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        _require(torch.get_num_interop_threads() == 1, "TORCH_INTEROP_NOT_ONE")
    torch.use_deterministic_algorithms(True, warn_only=False)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False
    _require(torch.get_num_threads() == 1, "TORCH_INTRAOP_NOT_ONE")
    _require(torch.get_num_interop_threads() == 1, "TORCH_INTEROP_NOT_ONE")
    _require(
        torch.are_deterministic_algorithms_enabled(),
        "TORCH_DETERMINISM_DISABLED",
    )
    warn_only = getattr(
        torch,
        "is_deterministic_algorithms_warn_only_enabled",
        lambda: False,
    )
    _require(warn_only() is False, "TORCH_DETERMINISM_WARN_ONLY")

    # Fixed zero-valued operations load the relevant native pools without using
    # scientific input, randomness, training, inference, or an outcome.
    numpy.matmul(numpy.zeros((2, 2)), numpy.zeros((2, 2)))
    torch.mm(torch.zeros((2, 2)), torch.zeros((2, 2)))
    pools = threadpoolctl.threadpool_info()
    _require(type(pools) is list and pools, "NATIVE_THREAD_POOL_NOT_DISCOVERED")
    for pool in pools:
        _require(type(pool) is dict, "NATIVE_THREAD_POOL_ROW_INVALID")
        count = pool.get("num_threads")
        _require(type(count) is int and count == 1, "NATIVE_THREAD_POOL_NOT_ONE")
    return {
        "cpu_only": True,
        "deterministic_algorithms": True,
        "distribution_versions": dict(sorted(versions.items())),
        "native_thread_pool_count": len(pools),
        "torch_interop_threads": torch.get_num_interop_threads(),
        "torch_intraop_threads": torch.get_num_threads(),
    }


def main(argv: Optional[list[str]] = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments not in ([], ["--supply-chain-only"]):
        raise RuntimeVerificationError("UNRECOGNIZED_ARGUMENTS")
    verify_environment(os.environ)
    supply_chain = verify_offline_wheel_closure()
    supply_chain_only = arguments == ["--supply-chain-only"]
    runtime = None if supply_chain_only else verify_numerical_runtime()
    receipt = {
        "decision": (
            "PASS_DATA_FREE_CONTAINER_SUPPLY_CHAIN_PREFLIGHT_ONLY"
            if supply_chain_only
            else "PASS_DATA_FREE_CONTAINER_RUNTIME_PREFLIGHT_ONLY"
        ),
        "network_accessed": False,
        "qualification_or_closure_claimed": False,
        "runtime": runtime,
        "schema_version": SCHEMA_VERSION,
        "study_or_test_data_accessed": False,
        "supply_chain": supply_chain,
        "target_profile": TARGET_PROFILE,
    }
    print(
        json.dumps(
            receipt,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
