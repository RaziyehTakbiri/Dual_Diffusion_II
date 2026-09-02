"""Pure contract for the additive native-DBR B08 runtime successor.

This successor deliberately uses the managed Databricks Runtime directly.  It
does not require a custom container, a registry, or an AWS instance profile.
Its candidate identity is instead the conjunction of one exact DBR target,
the future F152 lock observation, the source binding, and an observed native-
runtime receipt.  Syntax and metadata observations do not prove dependency or
installed-payload closure.

The shipped profile is intentionally unresolved because the F152 production
lock does not yet exist.  Neither the draft nor a later observed profile
authorizes network access, study/test-data access, calibration, training,
inference, scientific execution, field or blocker closure, or tracker edits.

This module is standard-library-only and pure.  It performs no file,
environment, package, network, subprocess, Spark, or Databricks operation.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
from typing import Dict, Iterable


SCHEMA_VERSION = "heterodiff-b08-databricks-native-runtime-profile-v1"
PROFILE_ID = "b08-databricks-aws-native-dbr17.3-linux-x86_64-cpu-py312"
DRAFT_UNRESOLVED_F152_LOCK = "DRAFT_UNRESOLVED_F152_LOCK"
OBSERVED_REVIEW_PENDING = "OBSERVED_REVIEW_PENDING_NO_AUTHORITY"
LIFECYCLE_STATES = (DRAFT_UNRESOLVED_F152_LOCK, OBSERVED_REVIEW_PENDING)

PROFILE_PATH = (
    "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312."
    "native-runtime-profile.template.json"
)
F152_LOCK_PATH = "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock"

RECORD_DOMAIN = b"heterodiff/b08/databricks-native-runtime-profile/v1\0"
_HEX = frozenset("0123456789abcdef")
_REVISION = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")

F153_ENVIRONMENT = {
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

EXPECTED_MODULES = {
    "heterodiff": "heterodiff",
    "numpy": "numpy",
    "scipy": "scipy",
    "threadpoolctl": "threadpoolctl",
    "torch": "torch",
}

UNOBSERVED_TARGET_PATHS = (
    "/target/cloud_provider",
    "/target/compute_mode",
    "/target/runtime_engine",
    "/target/machine_learning_runtime",
    "/target/photon_enabled",
    "/target/spark_version",
    "/target/operating_system_distribution",
    "/target/operating_system_release",
    "/target/cpu_only",
    "/target/gpu_enabled",
)

UNRESOLVED_PATHS = (
    "/f152_lock/sha256",
    "/f152_lock/complete_transitive_lock",
    "/f152_lock/artifact_closure_verified",
    "/runtime_bindings/source_revision",
    "/runtime_bindings/source_manifest_sha256",
    "/runtime_bindings/installed_distribution_metadata_observation_sha256",
    "/runtime_bindings/module_origin_observation_sha256",
    "/runtime_bindings/python_abi_observation_sha256",
    "/runtime_bindings/native_runtime_capture_sha256",
    "/runtime_bindings/torch_deterministic_runtime_observation_sha256",
    "/runtime_bindings/every_process_worker_equivalence_verified",
    "/runtime_bindings/f153_effective_runtime_satisfaction_verified",
) + UNOBSERVED_TARGET_PATHS

REVIEW_PENDING_UNRESOLVED_PATHS = (
    "/f152_lock/complete_transitive_lock",
    "/f152_lock/artifact_closure_verified",
    "/runtime_bindings/torch_deterministic_runtime_observation_sha256",
    "/runtime_bindings/every_process_worker_equivalence_verified",
    "/runtime_bindings/f153_effective_runtime_satisfaction_verified",
) + UNOBSERVED_TARGET_PATHS

_TOP_KEYS = (
    "schema_version",
    "record_sha256",
    "profile_id",
    "lifecycle_state",
    "native_route",
    "target",
    "f152_lock",
    "f153_environment",
    "runtime_bindings",
    "resolution",
    "safety_boundary",
)


class NativeRuntimeProfileError(ValueError):
    """The native-runtime profile is malformed or overclaims eligibility."""


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
                raise NativeRuntimeProfileError(name + " contains a non-string key")
            _require_json_native(item, name=name + "." + key)
        return
    raise NativeRuntimeProfileError(name + " contains a non-JSON-native value")


def _exact_object(value: object, keys: Iterable[str], *, name: str) -> dict:
    if type(value) is not dict:
        raise NativeRuntimeProfileError(name + " must be an exact object")
    expected = frozenset(keys)
    if frozenset(value) != expected or any(type(key) is not str for key in value):
        raise NativeRuntimeProfileError(name + " has missing or unknown keys")
    return value


def _sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise NativeRuntimeProfileError(name + " must be a lowercase SHA-256")
    return value


def canonical_json_bytes(value: object) -> bytes:
    """Return exact canonical ASCII JSON without a terminal newline."""

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
        raise NativeRuntimeProfileError("value is not canonical ASCII JSON") from error


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


def build_draft_profile() -> Dict[str, object]:
    """Build the exact unresolved native-DBR declaration shipped in-repo."""

    record: Dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "record_sha256": "0" * 64,
        "profile_id": PROFILE_ID,
        "lifecycle_state": DRAFT_UNRESOLVED_F152_LOCK,
        "native_route": {
            "route_kind": "NATIVE_DBR_HASH_LOCKED_WHEELHOUSE",
            "custom_container_required": False,
            "container_registry_required": False,
            "aws_instance_profile_required": False,
            "network_resolution_or_install_permitted": False,
            "editable_install_permitted": False,
            "sdist_install_permitted": False,
            "pip_no_index_required": True,
            "pip_require_hashes_required": True,
            "pip_only_binary_required": True,
            "module_origin_observation_required": True,
            "module_distribution_ownership_claimed": False,
        },
        "target": {
            "service": "DATABRICKS",
            "cloud_provider": "AWS",
            "compute_mode": "CLASSIC_DEDICATED_SINGLE_NODE",
            "runtime_engine": "STANDARD",
            "machine_learning_runtime": False,
            "photon_enabled": False,
            "databricks_runtime_release": "17.3 LTS",
            "databricks_runtime_version_prefix": "17.3",
            "spark_version": "4.0.0",
            "python_implementation": "CPython",
            "python_version": "3.12.3",
            "python_abi": "cp312",
            "operating_system_family": "Linux",
            "operating_system_distribution": "Ubuntu",
            "operating_system_release": "24.04.3 LTS",
            "architecture": "x86_64",
            "pointer_bits": 64,
            "byteorder": "little",
            "cpu_only": True,
            "gpu_enabled": False,
        },
        "f152_lock": {
            "field_path": "/compute_and_fairness_plan/container_or_lockfile_sha256",
            "role": "PRODUCTION_NATIVE_DBR_LOCKFILE",
            "path": F152_LOCK_PATH,
            "sha256": None,
            "present_and_regular": False,
            "complete_transitive_lock": False,
            "artifact_closure_verified": False,
            "all_requirements_exactly_pinned": False,
            "all_declared_requirements_sha256_hashed": False,
            "expected_distributions": dict(EXPECTED_DISTRIBUTIONS),
        },
        "f153_environment": dict(F153_ENVIRONMENT),
        "runtime_bindings": {
            "source_revision": None,
            "source_manifest_sha256": None,
            "installed_distribution_metadata_observation_sha256": None,
            "module_origin_observation_sha256": None,
            "python_abi_observation_sha256": None,
            "native_runtime_capture_sha256": None,
            "torch_deterministic_runtime_observation_sha256": None,
            "required_modules": dict(EXPECTED_MODULES),
            "installed_payload_closure_verified": False,
            "module_distribution_ownership_verified": False,
            "every_process_worker_equivalence_verified": False,
            "f153_effective_runtime_satisfaction_verified": False,
            "source_declaration_externally_authenticated": False,
            "runtime_observation_externally_attested": False,
        },
        "resolution": {
            "unresolved_paths": list(UNRESOLVED_PATHS),
            "eligible_for_data_free_independent_review": False,
            "eligible_for_scientific_execution": False,
            "independent_review_required": True,
        },
        "safety_boundary": {
            "network_or_contact_authorized": False,
            "study_data_access_authorized": False,
            "test_data_access_authorized": False,
            "calibration_authorized": False,
            "training_or_inference_authorized": False,
            "scientific_execution_authorized": False,
            "field_or_blocker_closure_authorized": False,
            "b08_closure_authorized": False,
            "tracker_or_timetable_edit_authorized": False,
        },
    }
    return with_semantic_digest(record)


def bind_observed_capture(
    draft: object,
    *,
    lock_sha256: str,
    source_revision: str,
    source_manifest_sha256: str,
    installed_distribution_metadata_observation_sha256: str,
    module_origin_observation_sha256: str,
    python_abi_observation_sha256: str,
    native_runtime_capture_sha256: str,
) -> Dict[str, object]:
    """Bind one observation for review without granting execution authority."""

    value = validate_profile(draft)
    if value["lifecycle_state"] != DRAFT_UNRESOLVED_F152_LOCK:
        raise NativeRuntimeProfileError("only the exact draft can bind a capture")
    for name, digest in (
        ("lock_sha256", lock_sha256),
        ("source_manifest_sha256", source_manifest_sha256),
        (
            "installed_distribution_metadata_observation_sha256",
            installed_distribution_metadata_observation_sha256,
        ),
        ("module_origin_observation_sha256", module_origin_observation_sha256),
        ("python_abi_observation_sha256", python_abi_observation_sha256),
        ("native_runtime_capture_sha256", native_runtime_capture_sha256),
    ):
        _sha256(digest, name=name)
    if type(source_revision) is not str or _REVISION.fullmatch(source_revision) is None:
        raise NativeRuntimeProfileError("source_revision must be a lowercase Git digest")

    result = deepcopy(value)
    result["lifecycle_state"] = OBSERVED_REVIEW_PENDING
    result["f152_lock"].update(
        {
            "sha256": lock_sha256,
            "present_and_regular": True,
            "complete_transitive_lock": False,
            "artifact_closure_verified": False,
            "all_requirements_exactly_pinned": True,
            "all_declared_requirements_sha256_hashed": True,
        }
    )
    result["runtime_bindings"].update(
        {
            "source_revision": source_revision,
            "source_manifest_sha256": source_manifest_sha256,
            "installed_distribution_metadata_observation_sha256": (
                installed_distribution_metadata_observation_sha256
            ),
            "module_origin_observation_sha256": module_origin_observation_sha256,
            "python_abi_observation_sha256": python_abi_observation_sha256,
            "native_runtime_capture_sha256": native_runtime_capture_sha256,
        }
    )
    result["resolution"].update(
        {
            "unresolved_paths": list(REVIEW_PENDING_UNRESOLVED_PATHS),
            "eligible_for_data_free_independent_review": True,
        }
    )
    return with_semantic_digest(result)


def _validate_exact_fixed_sections(value: dict) -> None:
    draft = build_draft_profile()
    for section in ("native_route", "target", "f153_environment", "safety_boundary"):
        if value[section] != draft[section] or type(value[section]) is not dict:
            raise NativeRuntimeProfileError(section + " differs from exact contract")
    if len(value["f153_environment"]) != 15:
        raise NativeRuntimeProfileError("F153 environment must contain exactly 15 keys")


def _validate_f152_lock(value: object, *, observed: bool) -> None:
    item = _exact_object(
        value,
        (
            "field_path",
            "role",
            "path",
            "sha256",
            "present_and_regular",
            "complete_transitive_lock",
            "artifact_closure_verified",
            "all_requirements_exactly_pinned",
            "all_declared_requirements_sha256_hashed",
            "expected_distributions",
        ),
        name="f152_lock",
    )
    fixed = build_draft_profile()["f152_lock"]
    for key in ("field_path", "role", "path", "expected_distributions"):
        if item[key] != fixed[key] or type(item[key]) is not type(fixed[key]):
            raise NativeRuntimeProfileError("F152 fixed binding differs: " + key)
    booleans = (
        "present_and_regular",
        "complete_transitive_lock",
        "artifact_closure_verified",
        "all_requirements_exactly_pinned",
        "all_declared_requirements_sha256_hashed",
    )
    if any(type(item[key]) is not bool for key in booleans):
        raise NativeRuntimeProfileError("F152 status flags must be exact booleans")
    if observed:
        _sha256(item["sha256"], name="f152_lock.sha256")
        if item["present_and_regular"] is not True:
            raise NativeRuntimeProfileError("observed F152 lock is not regular")
        if item["all_requirements_exactly_pinned"] is not True:
            raise NativeRuntimeProfileError("observed F152 syntax is not exactly pinned")
        if item["all_declared_requirements_sha256_hashed"] is not True:
            raise NativeRuntimeProfileError("observed F152 declarations lack hashes")
        if item["complete_transitive_lock"] is not False:
            raise NativeRuntimeProfileError(
                "capture cannot claim complete F152 transitive closure"
            )
        if item["artifact_closure_verified"] is not False:
            raise NativeRuntimeProfileError(
                "capture cannot claim F152 artifact closure"
            )
    else:
        if item["sha256"] is not None or any(item[key] is not False for key in booleans):
            raise NativeRuntimeProfileError("draft must keep F152 lock unresolved")


def _validate_runtime_bindings(value: object, *, observed: bool) -> None:
    item = _exact_object(
        value,
        (
            "source_revision",
            "source_manifest_sha256",
            "installed_distribution_metadata_observation_sha256",
            "module_origin_observation_sha256",
            "python_abi_observation_sha256",
            "native_runtime_capture_sha256",
            "torch_deterministic_runtime_observation_sha256",
            "required_modules",
            "installed_payload_closure_verified",
            "module_distribution_ownership_verified",
            "every_process_worker_equivalence_verified",
            "f153_effective_runtime_satisfaction_verified",
            "source_declaration_externally_authenticated",
            "runtime_observation_externally_attested",
        ),
        name="runtime_bindings",
    )
    if item["required_modules"] != EXPECTED_MODULES:
        raise NativeRuntimeProfileError("required native module roster differs")
    if item["installed_payload_closure_verified"] is not False:
        raise NativeRuntimeProfileError("installed payload closure is unverified")
    if item["module_distribution_ownership_verified"] is not False:
        raise NativeRuntimeProfileError("module ownership is unverified")
    if item["every_process_worker_equivalence_verified"] is not False:
        raise NativeRuntimeProfileError("worker equivalence is unverified")
    if item["f153_effective_runtime_satisfaction_verified"] is not False:
        raise NativeRuntimeProfileError("F153 runtime satisfaction is unverified")
    if item["torch_deterministic_runtime_observation_sha256"] is not None:
        raise NativeRuntimeProfileError("Torch deterministic state is unobserved")
    if item["source_declaration_externally_authenticated"] is not False:
        raise NativeRuntimeProfileError("source identity cannot be overauthenticated")
    if item["runtime_observation_externally_attested"] is not False:
        raise NativeRuntimeProfileError("runtime identity cannot be overattested")
    digest_keys = (
        "source_manifest_sha256",
        "installed_distribution_metadata_observation_sha256",
        "module_origin_observation_sha256",
        "python_abi_observation_sha256",
        "native_runtime_capture_sha256",
    )
    if observed:
        revision = item["source_revision"]
        if type(revision) is not str or _REVISION.fullmatch(revision) is None:
            raise NativeRuntimeProfileError("observed source revision is invalid")
        for key in digest_keys:
            _sha256(item[key], name="runtime_bindings." + key)
    elif item["source_revision"] is not None or any(
        item[key] is not None for key in digest_keys
    ):
        raise NativeRuntimeProfileError("draft runtime bindings must remain unresolved")


def _validate_resolution(value: object, *, observed: bool) -> None:
    item = _exact_object(
        value,
        (
            "unresolved_paths",
            "eligible_for_data_free_independent_review",
            "eligible_for_scientific_execution",
            "independent_review_required",
        ),
        name="resolution",
    )
    if item["eligible_for_scientific_execution"] is not False:
        raise NativeRuntimeProfileError("profile cannot authorize science")
    if item["independent_review_required"] is not True:
        raise NativeRuntimeProfileError("independent review must remain required")
    if observed:
        if item["unresolved_paths"] != list(REVIEW_PENDING_UNRESOLVED_PATHS):
            raise NativeRuntimeProfileError(
                "observed profile must retain unobserved target paths"
            )
        if item["eligible_for_data_free_independent_review"] is not True:
            raise NativeRuntimeProfileError("observed profile lacks review eligibility")
    else:
        if item["unresolved_paths"] != list(UNRESOLVED_PATHS):
            raise NativeRuntimeProfileError("draft unresolved-path roster differs")
        if item["eligible_for_data_free_independent_review"] is not False:
            raise NativeRuntimeProfileError("draft overclaims review eligibility")


def validate_profile(record: object) -> Dict[str, object]:
    """Validate an unresolved draft or observation-bound review candidate."""

    value = _exact_object(record, _TOP_KEYS, name="record")
    _require_json_native(value, name="record")
    if value["schema_version"] != SCHEMA_VERSION:
        raise NativeRuntimeProfileError("schema_version differs")
    if value["profile_id"] != PROFILE_ID:
        raise NativeRuntimeProfileError("native profile_id differs")
    state = value["lifecycle_state"]
    if type(state) is not str or state not in LIFECYCLE_STATES:
        raise NativeRuntimeProfileError("lifecycle_state differs")
    _sha256(value["record_sha256"], name="record.record_sha256")
    if value["record_sha256"] != semantic_sha256(value):
        raise NativeRuntimeProfileError("record semantic digest differs")
    _validate_exact_fixed_sections(value)
    observed = state == OBSERVED_REVIEW_PENDING
    _validate_f152_lock(value["f152_lock"], observed=observed)
    _validate_runtime_bindings(value["runtime_bindings"], observed=observed)
    _validate_resolution(value["resolution"], observed=observed)
    return deepcopy(value)


__all__ = (
    "DRAFT_UNRESOLVED_F152_LOCK",
    "EXPECTED_DISTRIBUTIONS",
    "EXPECTED_MODULES",
    "F152_LOCK_PATH",
    "F153_ENVIRONMENT",
    "LIFECYCLE_STATES",
    "NativeRuntimeProfileError",
    "OBSERVED_REVIEW_PENDING",
    "PROFILE_ID",
    "PROFILE_PATH",
    "REVIEW_PENDING_UNRESOLVED_PATHS",
    "SCHEMA_VERSION",
    "UNRESOLVED_PATHS",
    "UNOBSERVED_TARGET_PATHS",
    "bind_observed_capture",
    "build_draft_profile",
    "canonical_json_bytes",
    "semantic_projection",
    "semantic_sha256",
    "validate_profile",
    "with_semantic_digest",
)
