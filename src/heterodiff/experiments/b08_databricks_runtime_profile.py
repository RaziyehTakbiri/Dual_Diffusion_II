"""Pure contract for the additive B08 Databricks Linux runtime profile.

The historical M1/macOS profile remains a development and receipt predecessor.
It is never rewritten, reinterpreted as Linux, or admitted as the production
successor.  This module defines only a strict machine-readable declaration and
validator for the future AWS Databricks DBR 17.3 LTS, x86_64, CPU-only runtime.

``ELIGIBLE_RESOLVED`` means eligible only for the separately governed,
data-free B08 environment qualification.  It authorizes no study/test data
access, calibration, training, inference, scientific execution, field closure,
blocker closure, or timetable edit.

The module is standard-library-only and pure: it performs no file, environment,
network, registry, subprocess, package-manager, Spark, or Databricks operation.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
from typing import Dict, Iterable


SCHEMA_VERSION = "heterodiff-b08-databricks-runtime-profile-v1"
PROFILE_ID = "b08-databricks-aws-dbr17.3-linux-x86_64-cpu-py312"
DRAFT_UNRESOLVED = "DRAFT_UNRESOLVED"
BUILD_INPUTS_RESOLVED = "BUILD_INPUTS_RESOLVED"
ELIGIBLE_RESOLVED = "ELIGIBLE_RESOLVED_FOR_DATA_FREE_B08_QUALIFICATION_ONLY"
LIFECYCLE_STATES = (
    DRAFT_UNRESOLVED,
    BUILD_INPUTS_RESOLVED,
    ELIGIBLE_RESOLVED,
)

PROFILE_PATH = (
    "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312." "runtime-profile.json"
)
LOCK_PATH = "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock"
SOURCE_WHEEL_PATH = (
    "requirements/wheelhouse/b08-databricks-aws-dbr17.3-x86_64-cpu-py312/"
    "heterodiff-0.1.0-py3-none-any.whl"
)
WHEEL_MANIFEST_PATH = (
    "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312." "wheel-manifest.json"
)

HISTORICAL_PROFILE_ID = "m1-reference-macos-arm64-py311"
HISTORICAL_LOCK_PATH = "requirements/m1-reference-macos-arm64-py311.lock"
HISTORICAL_LOCK_SHA256 = (
    "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d"
)

RECORD_DOMAIN = b"heterodiff/b08/databricks-runtime-profile/v1\0"
_HEX = frozenset("0123456789abcdef")
_VERSION = re.compile(r"[0-9]+(?:\.[0-9]+){1,3}(?:[+._-][A-Za-z0-9._-]+)?\Z")

DETERMINISTIC_ENVIRONMENT = {
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

EXPECTED_DISTRIBUTIONS = {
    "heterodiff": "0.1.0",
    "numpy": "2.4.6",
    "scipy": "1.17.1",
    "threadpoolctl": "3.6.0",
    "torch": "2.12.1+cpu",
}

UNRESOLVED_PATHS = (
    "/container/base_image_manifest_digest",
    "/container/final_image_manifest_digest",
    "/container/final_image_reference_sha256",
    "/dependencies/installed_distribution_manifest_sha256",
    "/dependencies/lockfile_sha256",
    "/dependencies/source_wheel_sha256",
    "/dependencies/wheel_manifest_sha256",
    "/resolution/runtime_observation_sha256",
    "/torch/cpu_runtime_probe_sha256",
    "/torch/version",
    "/torch/wheel_filename",
    "/torch/wheel_sha256",
)

BUILD_STAGE_UNRESOLVED_PATHS = (
    "/container/final_image_manifest_digest",
    "/container/final_image_reference_sha256",
    "/dependencies/installed_distribution_manifest_sha256",
    "/resolution/runtime_observation_sha256",
    "/torch/cpu_runtime_probe_sha256",
)

_TOP_KEYS = (
    "schema_version",
    "record_sha256",
    "profile_id",
    "lifecycle_state",
    "target",
    "container",
    "dependencies",
    "torch",
    "deterministic_environment",
    "compatibility",
    "resolution",
    "qualification_boundary",
)


class RuntimeProfileError(ValueError):
    """A runtime profile is malformed, unresolved, or ineligible."""


def canonical_json_bytes(value: object) -> bytes:
    """Return exact canonical ASCII JSON bytes without a terminal newline."""

    _require_json_native(value, name="value")
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise RuntimeProfileError("value is not canonical ASCII JSON") from error


def semantic_projection(record: object) -> Dict[str, object]:
    value = _exact_object(record, _TOP_KEYS, name="record")
    projection = deepcopy(value)
    projection.pop("record_sha256")
    return projection


def semantic_sha256(record: object) -> str:
    return hashlib.sha256(
        RECORD_DOMAIN + canonical_json_bytes(semantic_projection(record))
    ).hexdigest()


def with_semantic_digest(record: object) -> Dict[str, object]:
    result = deepcopy(_exact_object(record, _TOP_KEYS, name="record"))
    result["record_sha256"] = semantic_sha256(result)
    return result


def _require_json_native(value: object, *, name: str) -> None:
    kind = type(value)
    if value is None or kind in (str, int, bool):
        return
    if kind is list:
        for ordinal, item in enumerate(value):
            _require_json_native(item, name=f"{name}[{ordinal}]")
        return
    if kind is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise RuntimeProfileError(name + " contains a non-string key")
            _require_json_native(item, name=name + "." + key)
        return
    raise RuntimeProfileError(name + " contains a non-exact JSON-native type")


def _exact_object(value: object, keys: Iterable[str], *, name: str) -> dict:
    if type(value) is not dict:
        raise RuntimeProfileError(name + " must be an exact object")
    expected = frozenset(keys)
    if frozenset(value) != expected or any(type(key) is not str for key in value):
        raise RuntimeProfileError(name + " has missing or unknown keys")
    return value


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise RuntimeProfileError(name + " must be an exact boolean")
    return value


def _exact_positive_int(value: object, *, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise RuntimeProfileError(name + " must be an exact positive integer")
    return value


def _exact_ascii(value: object, *, name: str, maximum: int = 1024) -> str:
    if type(value) is not str or not value or len(value) > maximum or "\x00" in value:
        raise RuntimeProfileError(name + " must be bounded nonempty ASCII")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as error:
        raise RuntimeProfileError(name + " must be ASCII") from error
    return value


def _sha256(value: object, *, name: str) -> str:
    digest = _exact_ascii(value, name=name, maximum=64)
    if len(digest) != 64 or any(character not in _HEX for character in digest):
        raise RuntimeProfileError(name + " must be a lowercase SHA-256 digest")
    return digest


def _oci_digest(value: object, *, name: str) -> str:
    digest = _exact_ascii(value, name=name, maximum=71)
    if not digest.startswith("sha256:"):
        raise RuntimeProfileError(name + " must use the sha256: prefix")
    _sha256(digest[7:], name=name + ".hex")
    return digest


def _compatibility_record() -> Dict[str, object]:
    return {
        "mapping_kind": "ADDITIVE_PREDECESSOR_TO_SUCCESSOR_NON_SUBSTITUTABLE",
        "historical_profile_id": HISTORICAL_PROFILE_ID,
        "historical_lock_path": HISTORICAL_LOCK_PATH,
        "historical_lock_sha256": HISTORICAL_LOCK_SHA256,
        "successor_profile_id": PROFILE_ID,
        "successor_profile_path": PROFILE_PATH,
        "historical_receipts_modified": False,
        "historical_profile_eligible_as_successor": False,
        "mapping_creates_eligibility": False,
    }


def compatibility_seam(
    historical_profile_id: str,
    historical_lock_path: str,
    historical_lock_sha256: str,
) -> Dict[str, object]:
    """Map the exact historical identity to its successor without mutation.

    The returned relation records lineage only.  It never converts the macOS
    profile into a Linux profile and never creates qualification eligibility.
    """

    if historical_profile_id != HISTORICAL_PROFILE_ID:
        raise RuntimeProfileError("historical profile identity differs")
    if historical_lock_path != HISTORICAL_LOCK_PATH:
        raise RuntimeProfileError("historical lock path differs")
    if historical_lock_sha256 != HISTORICAL_LOCK_SHA256:
        raise RuntimeProfileError("historical lock digest differs")
    return deepcopy(_compatibility_record())


def build_draft_profile() -> Dict[str, object]:
    """Return the exact unresolved declaration shipped in ``requirements``."""

    record: Dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "record_sha256": "0" * 64,
        "profile_id": PROFILE_ID,
        "lifecycle_state": DRAFT_UNRESOLVED,
        "target": {
            "cloud_provider": "AWS",
            "service": "DATABRICKS",
            "compute_mode": "CLASSIC_DEDICATED",
            "databricks_runtime_release": "17.3 LTS",
            "databricks_runtime_version": "17.3.x-scala2.13",
            "spark_version": "4.0.0",
            "scala_version": "2.13.16",
            "runtime_engine": "STANDARD",
            "machine_learning_runtime": False,
            "photon_enabled": False,
            "operating_system_family": "Linux",
            "operating_system_distribution": "Ubuntu",
            "operating_system_release": "24.04.3 LTS",
            "architecture": "x86_64",
            "oci_architecture": "amd64",
            "python_implementation": "CPython",
            "python_version": "3.12.3",
            "python_abi": "cp312",
            "java_runtime": "Zulu17.58+21-CA",
            "cpu_only": True,
            "gpu_enabled": False,
        },
        "container": {
            "container_services_mode": "DATABRICKS_CONTAINER_SERVICES_DEDICATED",
            "base_image_repository": "databricksruntime/standard",
            "base_image_discovery_tag": "17.3-LTS",
            "base_image_manifest_digest": None,
            "final_registry_kind": "AMAZON_ECR_PRIVATE",
            "final_image_manifest_digest": None,
            "final_image_reference_sha256": None,
            "final_image_reference_kind": "OCI_REPOSITORY_AT_SHA256_DIGEST",
            "mutable_tag_eligible": False,
            "docker_cmd_or_entrypoint_relied_upon": False,
            "image_platform": "linux/amd64",
        },
        "dependencies": {
            "expected_distributions": dict(EXPECTED_DISTRIBUTIONS),
            "lockfile_path": LOCK_PATH,
            "lockfile_sha256": None,
            "source_wheel_path": SOURCE_WHEEL_PATH,
            "source_wheel_sha256": None,
            "wheel_manifest_path": WHEEL_MANIFEST_PATH,
            "wheel_manifest_sha256": None,
            "installed_distribution_manifest_sha256": None,
            "complete_transitive_lock": False,
            "wheel_manifest_complete": False,
            "all_artifacts_linux_x86_64_cp312_compatible": False,
            "hashes_required_for_every_artifact": True,
            "sdist_installation_permitted": False,
            "editable_install_permitted": False,
            "network_install_during_qualification_permitted": False,
            "user_site_packages_permitted": False,
        },
        "torch": {
            "package_name": "torch",
            "version": None,
            "distribution_variant": "CPU_ONLY",
            "wheel_filename": None,
            "wheel_sha256": None,
            "cpu_runtime_probe_sha256": None,
            "cuda_compiled": False,
            "cuda_available": False,
            "mps_compiled": False,
            "mps_available": False,
            "deterministic_algorithms": True,
            "warn_only": False,
            "intraop_threads": 1,
            "interop_threads": 1,
            "cudnn_benchmark": False,
        },
        "deterministic_environment": dict(DETERMINISTIC_ENVIRONMENT),
        "compatibility": _compatibility_record(),
        "resolution": {
            "unresolved_paths": list(UNRESOLVED_PATHS),
            "runtime_observation_sha256": None,
            "eligible_for_data_free_b08_qualification": False,
            "eligible_for_scientific_execution": False,
            "independent_review_required": True,
        },
        "qualification_boundary": {
            "declaration_is_runtime_observation": False,
            "study_data_access_authorized": False,
            "test_data_access_authorized": False,
            "calibration_authorized": False,
            "training_or_inference_authorized": False,
            "scientific_execution_authorized": False,
            "b08_closure_authorized": False,
            "field_or_blocker_closure_authorized": False,
            "tracker_or_timetable_edit_authorized": False,
            "historical_mac_artifacts_rewritten": False,
        },
    }
    return with_semantic_digest(record)


def _validate_target(value: object) -> None:
    expected = build_draft_profile()["target"]
    if value != expected or type(value) is not dict:
        raise RuntimeProfileError(
            "target must be exact DBR17.3 Linux x86_64 CPython3.12 CPU profile"
        )


def _validate_container(value: object, *, state: str) -> None:
    item = _exact_object(
        value,
        (
            "container_services_mode",
            "base_image_repository",
            "base_image_discovery_tag",
            "base_image_manifest_digest",
            "final_registry_kind",
            "final_image_manifest_digest",
            "final_image_reference_sha256",
            "final_image_reference_kind",
            "mutable_tag_eligible",
            "docker_cmd_or_entrypoint_relied_upon",
            "image_platform",
        ),
        name="container",
    )
    expected_fixed = build_draft_profile()["container"]
    for key in (
        "container_services_mode",
        "base_image_repository",
        "base_image_discovery_tag",
        "final_registry_kind",
        "final_image_reference_kind",
        "mutable_tag_eligible",
        "docker_cmd_or_entrypoint_relied_upon",
        "image_platform",
    ):
        if item[key] != expected_fixed[key] or type(item[key]) is not type(
            expected_fixed[key]
        ):
            raise RuntimeProfileError("container fixed contract differs: " + key)
    build_inputs_resolved = state != DRAFT_UNRESOLVED
    eligible = state == ELIGIBLE_RESOLVED
    if build_inputs_resolved:
        _oci_digest(
            item["base_image_manifest_digest"],
            name="container.base_image_manifest_digest",
        )
    elif item["base_image_manifest_digest"] is not None:
        raise RuntimeProfileError("draft base image digest must remain unresolved")
    if eligible:
        _oci_digest(
            item["final_image_manifest_digest"],
            name="container.final_image_manifest_digest",
        )
        _sha256(
            item["final_image_reference_sha256"],
            name="container.final_image_reference_sha256",
        )
    elif (
        item["final_image_manifest_digest"] is not None
        or item["final_image_reference_sha256"] is not None
    ):
        raise RuntimeProfileError(
            "pre-build final image identity must remain unresolved"
        )


def _validate_dependencies(value: object, *, state: str) -> None:
    item = _exact_object(
        value,
        (
            "expected_distributions",
            "lockfile_path",
            "lockfile_sha256",
            "source_wheel_path",
            "source_wheel_sha256",
            "wheel_manifest_path",
            "wheel_manifest_sha256",
            "installed_distribution_manifest_sha256",
            "complete_transitive_lock",
            "wheel_manifest_complete",
            "all_artifacts_linux_x86_64_cp312_compatible",
            "hashes_required_for_every_artifact",
            "sdist_installation_permitted",
            "editable_install_permitted",
            "network_install_during_qualification_permitted",
            "user_site_packages_permitted",
        ),
        name="dependencies",
    )
    fixed = build_draft_profile()["dependencies"]
    for key in (
        "expected_distributions",
        "lockfile_path",
        "source_wheel_path",
        "wheel_manifest_path",
        "hashes_required_for_every_artifact",
        "sdist_installation_permitted",
        "editable_install_permitted",
        "network_install_during_qualification_permitted",
        "user_site_packages_permitted",
    ):
        if item[key] != fixed[key] or type(item[key]) is not type(fixed[key]):
            raise RuntimeProfileError("dependency fixed contract differs: " + key)
    build_input_digest_keys = (
        "lockfile_sha256",
        "source_wheel_sha256",
        "wheel_manifest_sha256",
    )
    completeness_keys = (
        "complete_transitive_lock",
        "wheel_manifest_complete",
        "all_artifacts_linux_x86_64_cp312_compatible",
    )
    for key in completeness_keys:
        _exact_bool(item[key], name="dependencies." + key)
    build_inputs_resolved = state != DRAFT_UNRESOLVED
    eligible = state == ELIGIBLE_RESOLVED
    if build_inputs_resolved:
        for key in build_input_digest_keys:
            _sha256(item[key], name="dependencies." + key)
        if any(item[key] is not True for key in completeness_keys):
            raise RuntimeProfileError(
                "resolved build-input dependency closure is incomplete"
            )
    else:
        if any(item[key] is not None for key in build_input_digest_keys):
            raise RuntimeProfileError("draft dependency digests must remain unresolved")
        if any(item[key] is not False for key in completeness_keys):
            raise RuntimeProfileError("draft dependency completeness overclaim")
    if eligible:
        _sha256(
            item["installed_distribution_manifest_sha256"],
            name="dependencies.installed_distribution_manifest_sha256",
        )
    elif item["installed_distribution_manifest_sha256"] is not None:
        raise RuntimeProfileError(
            "pre-runtime installed-distribution digest must remain unresolved"
        )


def _validate_torch(value: object, *, state: str) -> None:
    item = _exact_object(
        value,
        (
            "package_name",
            "version",
            "distribution_variant",
            "wheel_filename",
            "wheel_sha256",
            "cpu_runtime_probe_sha256",
            "cuda_compiled",
            "cuda_available",
            "mps_compiled",
            "mps_available",
            "deterministic_algorithms",
            "warn_only",
            "intraop_threads",
            "interop_threads",
            "cudnn_benchmark",
        ),
        name="torch",
    )
    fixed = build_draft_profile()["torch"]
    for key in (
        "package_name",
        "distribution_variant",
        "cuda_compiled",
        "cuda_available",
        "mps_compiled",
        "mps_available",
        "deterministic_algorithms",
        "warn_only",
        "intraop_threads",
        "interop_threads",
        "cudnn_benchmark",
    ):
        if item[key] != fixed[key] or type(item[key]) is not type(fixed[key]):
            raise RuntimeProfileError("CPU-only torch contract differs: " + key)
    _exact_positive_int(item["intraop_threads"], name="torch.intraop_threads")
    _exact_positive_int(item["interop_threads"], name="torch.interop_threads")
    build_inputs_resolved = state != DRAFT_UNRESOLVED
    eligible = state == ELIGIBLE_RESOLVED
    if build_inputs_resolved:
        version = _exact_ascii(item["version"], name="torch.version", maximum=128)
        if (
            _VERSION.fullmatch(version) is None
            or version != EXPECTED_DISTRIBUTIONS["torch"]
        ):
            raise RuntimeProfileError("torch.version must be an exact CPU-only version")
        filename = _exact_ascii(
            item["wheel_filename"], name="torch.wheel_filename", maximum=512
        )
        lowered = filename.casefold()
        if (
            not lowered.endswith(".whl")
            or "cp312" not in lowered
            or "x86_64" not in lowered
            or any(
                marker in lowered
                for marker in ("+cu", "cuda", "rocm", "arm64", "aarch64")
            )
        ):
            raise RuntimeProfileError(
                "torch wheel is not CPU-only Linux x86_64 CPython312"
            )
        _sha256(item["wheel_sha256"], name="torch.wheel_sha256")
    elif any(
        item[key] is not None for key in ("version", "wheel_filename", "wheel_sha256")
    ):
        raise RuntimeProfileError("draft torch identity must remain unresolved")
    if eligible:
        _sha256(item["cpu_runtime_probe_sha256"], name="torch.cpu_runtime_probe_sha256")
    elif item["cpu_runtime_probe_sha256"] is not None:
        raise RuntimeProfileError("pre-runtime torch probe must remain unresolved")


def _validate_resolution(value: object, *, state: str) -> None:
    item = _exact_object(
        value,
        (
            "unresolved_paths",
            "runtime_observation_sha256",
            "eligible_for_data_free_b08_qualification",
            "eligible_for_scientific_execution",
            "independent_review_required",
        ),
        name="resolution",
    )
    if item["eligible_for_scientific_execution"] is not False:
        raise RuntimeProfileError(
            "runtime profile cannot authorize scientific execution"
        )
    if item["independent_review_required"] is not True:
        raise RuntimeProfileError("independent review must remain required")
    eligible = state == ELIGIBLE_RESOLVED
    if eligible:
        if item["unresolved_paths"] != []:
            raise RuntimeProfileError("eligible profile retains unresolved paths")
        _sha256(
            item["runtime_observation_sha256"],
            name="resolution.runtime_observation_sha256",
        )
        if item["eligible_for_data_free_b08_qualification"] is not True:
            raise RuntimeProfileError("resolved profile lacks bounded eligibility")
    elif state == BUILD_INPUTS_RESOLVED:
        if item["unresolved_paths"] != list(BUILD_STAGE_UNRESOLVED_PATHS):
            raise RuntimeProfileError("build-stage unresolved path roster differs")
        if item["runtime_observation_sha256"] is not None:
            raise RuntimeProfileError("pre-runtime observation must remain unresolved")
        if item["eligible_for_data_free_b08_qualification"] is not False:
            raise RuntimeProfileError("build-input profile overclaims eligibility")
    else:
        if item["unresolved_paths"] != list(UNRESOLVED_PATHS):
            raise RuntimeProfileError("draft unresolved path roster differs")
        if item["runtime_observation_sha256"] is not None:
            raise RuntimeProfileError("draft runtime observation must be unresolved")
        if item["eligible_for_data_free_b08_qualification"] is not False:
            raise RuntimeProfileError("draft profile overclaims eligibility")


def validate_profile(record: object) -> Dict[str, object]:
    """Validate a draft, build-input, or eligible profile and return a copy."""

    value = _exact_object(record, _TOP_KEYS, name="record")
    _require_json_native(value, name="record")
    if value["schema_version"] != SCHEMA_VERSION:
        raise RuntimeProfileError("schema_version differs")
    if value["profile_id"] == HISTORICAL_PROFILE_ID:
        raise RuntimeProfileError(
            "historical macOS profile cannot substitute for successor"
        )
    if value["profile_id"] != PROFILE_ID:
        raise RuntimeProfileError("profile_id differs")
    state = value["lifecycle_state"]
    if type(state) is not str or state not in LIFECYCLE_STATES:
        raise RuntimeProfileError("lifecycle_state differs")
    _sha256(value["record_sha256"], name="record.record_sha256")
    if value["record_sha256"] != semantic_sha256(value):
        raise RuntimeProfileError("record semantic digest differs")
    _validate_target(value["target"])
    _validate_container(value["container"], state=state)
    _validate_dependencies(value["dependencies"], state=state)
    _validate_torch(value["torch"], state=state)
    if value["deterministic_environment"] != DETERMINISTIC_ENVIRONMENT:
        raise RuntimeProfileError("the exact 15-variable environment differs")
    if value["compatibility"] != _compatibility_record():
        raise RuntimeProfileError("historical compatibility seam differs")
    _validate_resolution(value["resolution"], state=state)

    boundary = build_draft_profile()["qualification_boundary"]
    if value["qualification_boundary"] != boundary:
        raise RuntimeProfileError("qualification boundary differs")
    return deepcopy(value)


__all__ = (
    "BUILD_INPUTS_RESOLVED",
    "BUILD_STAGE_UNRESOLVED_PATHS",
    "DETERMINISTIC_ENVIRONMENT",
    "DRAFT_UNRESOLVED",
    "ELIGIBLE_RESOLVED",
    "EXPECTED_DISTRIBUTIONS",
    "HISTORICAL_LOCK_PATH",
    "HISTORICAL_LOCK_SHA256",
    "HISTORICAL_PROFILE_ID",
    "LIFECYCLE_STATES",
    "LOCK_PATH",
    "PROFILE_ID",
    "PROFILE_PATH",
    "RuntimeProfileError",
    "SCHEMA_VERSION",
    "SOURCE_WHEEL_PATH",
    "UNRESOLVED_PATHS",
    "WHEEL_MANIFEST_PATH",
    "build_draft_profile",
    "canonical_json_bytes",
    "compatibility_seam",
    "semantic_projection",
    "semantic_sha256",
    "validate_profile",
    "with_semantic_digest",
)
