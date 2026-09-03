"""Pure Ubuntu-24.04.4 successor to the reviewed native-DBR V1 profile.

V2 is an additive wrapper over the exact, independently reviewed V1 semantic
contract.  It changes only its own schema/profile/path/domain identities and the
prospective Ubuntu patch target from 24.04.3 LTS to 24.04.4 LTS.  The F152 lock,
expected distributions, F153 environment, unresolved evidence, and all-false
authority boundary remain exactly inherited from V1.

This module is standard-library-only and pure.  It performs no file,
environment, package, network, subprocess, Spark, or Databricks operation.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Dict

from heterodiff.experiments import b08_databricks_native_runtime_profile as v1


SCHEMA_VERSION = "heterodiff-b08-databricks-native-runtime-profile-v2"
PROFILE_ID = (
    "b08-databricks-aws-native-dbr17.3-ubuntu24.04.4-"
    "linux-x86_64-cpu-py312-v2"
)
PROFILE_PATH = (
    "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312."
    "native-runtime-profile-v2.template.json"
)
TARGET_OPERATING_SYSTEM_RELEASE = "24.04.4 LTS"
RECORD_DOMAIN = b"heterodiff/b08/databricks-native-runtime-profile/v2\0"

PREDECESSOR_SCHEMA_VERSION = v1.SCHEMA_VERSION
PREDECESSOR_PROFILE_ID = v1.PROFILE_ID
PREDECESSOR_PROFILE_PATH = v1.PROFILE_PATH
PREDECESSOR_OPERATING_SYSTEM_RELEASE = "24.04.3 LTS"
PREDECESSOR_RECORD_DOMAIN = (
    b"heterodiff/b08/databricks-native-runtime-profile/v1\0"
)
PREDECESSOR_PROFILE_SOURCE_SHA256 = (
    "a9258e63a4dc45822ce4d67b2535c5d22dcb9dad14323c00fbc01cfc366a9004"
)
PREDECESSOR_TEMPLATE_FILE_SHA256 = (
    "2e05801bf65ede62b2c318ba82a6d4f35aa9191b64a4ac24608fda05df071a91"
)
PREDECESSOR_TEMPLATE_RECORD_SHA256 = (
    "e2bd94423e9049a612ec865087e25c71c8711dccc0cda500979b387875cc79e5"
)
PREDECESSOR_INDEPENDENT_REVIEW_SHA256 = (
    "09deb7b2144e948c3b5b6a6010ec78904dfe3dd71da0889a8cfd4d8c59e3e81f"
)

DRAFT_UNRESOLVED_F152_LOCK = v1.DRAFT_UNRESOLVED_F152_LOCK
OBSERVED_REVIEW_PENDING = v1.OBSERVED_REVIEW_PENDING
LIFECYCLE_STATES = tuple(v1.LIFECYCLE_STATES)
F152_LOCK_PATH = v1.F152_LOCK_PATH
F153_ENVIRONMENT = deepcopy(v1.F153_ENVIRONMENT)
EXPECTED_DISTRIBUTIONS = deepcopy(v1.EXPECTED_DISTRIBUTIONS)
EXPECTED_MODULES = deepcopy(v1.EXPECTED_MODULES)
UNOBSERVED_TARGET_PATHS = tuple(v1.UNOBSERVED_TARGET_PATHS)
UNRESOLVED_PATHS = tuple(v1.UNRESOLVED_PATHS)
REVIEW_PENDING_UNRESOLVED_PATHS = tuple(v1.REVIEW_PENDING_UNRESOLVED_PATHS)

_TOP_KEYS = frozenset(
    {
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
    }
)
_HEX = frozenset("0123456789abcdef")


class NativeRuntimeProfileV2Error(ValueError):
    """The V2 native-runtime profile is malformed or overclaims eligibility."""


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
                raise NativeRuntimeProfileV2Error(
                    name + " contains a non-string key"
                )
            _require_json_native(item, name=name + "." + key)
        return
    raise NativeRuntimeProfileV2Error(name + " contains a non-JSON-native value")


def _exact_record(value: object) -> dict:
    if type(value) is not dict:
        raise NativeRuntimeProfileV2Error("record must be an exact object")
    if frozenset(value) != _TOP_KEYS or any(type(key) is not str for key in value):
        raise NativeRuntimeProfileV2Error("record has missing or unknown keys")
    return value


def _exact_sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise NativeRuntimeProfileV2Error(name + " must be a lowercase SHA-256")
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
        raise NativeRuntimeProfileV2Error(
            "value is not canonical ASCII JSON"
        ) from error


def semantic_projection(record: object) -> Dict[str, object]:
    result = deepcopy(_exact_record(record))
    result.pop("record_sha256")
    return result


def semantic_sha256(record: object) -> str:
    return hashlib.sha256(
        RECORD_DOMAIN + canonical_json_bytes(semantic_projection(record))
    ).hexdigest()


def with_semantic_digest(record: object) -> Dict[str, object]:
    result = deepcopy(_exact_record(record))
    result["record_sha256"] = semantic_sha256(result)
    return result


_PREDECESSOR_DRAFT = v1.build_draft_profile()
if (
    _PREDECESSOR_DRAFT.get("schema_version") != PREDECESSOR_SCHEMA_VERSION
    or _PREDECESSOR_DRAFT.get("profile_id") != PREDECESSOR_PROFILE_ID
    or _PREDECESSOR_DRAFT.get("record_sha256")
    != PREDECESSOR_TEMPLATE_RECORD_SHA256
    or _PREDECESSOR_DRAFT.get("target", {}).get("operating_system_release")
    != PREDECESSOR_OPERATING_SYSTEM_RELEASE
    or hashlib.sha256(
        PREDECESSOR_RECORD_DOMAIN
        + canonical_json_bytes(semantic_projection(_PREDECESSOR_DRAFT))
    ).hexdigest()
    != PREDECESSOR_TEMPLATE_RECORD_SHA256
):
    raise RuntimeError("reviewed native-runtime V1 semantic predecessor differs")


def _with_predecessor_digest(record: object) -> Dict[str, object]:
    result = deepcopy(_exact_record(record))
    projection = deepcopy(result)
    projection.pop("record_sha256")
    result["record_sha256"] = hashlib.sha256(
        PREDECESSOR_RECORD_DOMAIN + canonical_json_bytes(projection)
    ).hexdigest()
    return result


def _validate_predecessor_projection(record: object) -> Dict[str, object]:
    value = deepcopy(_exact_record(record))
    _require_json_native(value, name="predecessor")
    _exact_sha256(value.get("record_sha256"), name="predecessor.record_sha256")
    if value["record_sha256"] != _with_predecessor_digest(value)["record_sha256"]:
        raise NativeRuntimeProfileV2Error("predecessor semantic digest differs")

    expected = deepcopy(_PREDECESSOR_DRAFT)
    state = value.get("lifecycle_state")
    if state == DRAFT_UNRESOLVED_F152_LOCK:
        pass
    elif state == OBSERVED_REVIEW_PENDING:
        f152 = value.get("f152_lock")
        bindings = value.get("runtime_bindings")
        if type(f152) is not dict or type(bindings) is not dict:
            raise NativeRuntimeProfileV2Error(
                "observed predecessor sections are malformed"
            )
        lock_sha256 = _exact_sha256(
            f152.get("sha256"), name="f152_lock.sha256"
        )
        source_revision = bindings.get("source_revision")
        if (
            type(source_revision) is not str
            or len(source_revision) not in (40, 64)
            or any(character not in _HEX for character in source_revision)
        ):
            raise NativeRuntimeProfileV2Error(
                "source_revision must be a lowercase Git digest"
            )
        digest_keys = (
            "source_manifest_sha256",
            "installed_distribution_metadata_observation_sha256",
            "module_origin_observation_sha256",
            "python_abi_observation_sha256",
            "native_runtime_capture_sha256",
        )
        digests = {
            key: _exact_sha256(bindings.get(key), name="runtime_bindings." + key)
            for key in digest_keys
        }
        expected["lifecycle_state"] = OBSERVED_REVIEW_PENDING
        expected["f152_lock"].update(
            {
                "sha256": lock_sha256,
                "present_and_regular": True,
                "complete_transitive_lock": False,
                "artifact_closure_verified": False,
                "all_requirements_exactly_pinned": True,
                "all_declared_requirements_sha256_hashed": True,
            }
        )
        expected["runtime_bindings"].update(
            {"source_revision": source_revision, **digests}
        )
        expected["resolution"].update(
            {
                "unresolved_paths": list(REVIEW_PENDING_UNRESOLVED_PATHS),
                "eligible_for_data_free_independent_review": True,
            }
        )
        expected = _with_predecessor_digest(expected)
    else:
        raise NativeRuntimeProfileV2Error("lifecycle_state differs")

    if value != expected:
        raise NativeRuntimeProfileV2Error(
            "record differs outside the exact V1 semantic predecessor"
        )
    return value


def _from_v1_record(record: object) -> Dict[str, object]:
    predecessor = _validate_predecessor_projection(record)
    result = deepcopy(predecessor)
    result["schema_version"] = SCHEMA_VERSION
    result["profile_id"] = PROFILE_ID
    result["target"]["operating_system_release"] = TARGET_OPERATING_SYSTEM_RELEASE
    result["record_sha256"] = "0" * 64
    return with_semantic_digest(result)


def _to_v1_record(record: object) -> Dict[str, object]:
    value = deepcopy(_exact_record(record))
    if value.get("schema_version") != SCHEMA_VERSION:
        raise NativeRuntimeProfileV2Error("schema_version differs")
    if value.get("profile_id") != PROFILE_ID:
        raise NativeRuntimeProfileV2Error("profile_id differs")
    _exact_sha256(value.get("record_sha256"), name="record.record_sha256")
    if value["record_sha256"] != semantic_sha256(value):
        raise NativeRuntimeProfileV2Error("record semantic digest differs")
    target = value.get("target")
    if (
        type(target) is not dict
        or target.get("operating_system_release")
        != TARGET_OPERATING_SYSTEM_RELEASE
    ):
        raise NativeRuntimeProfileV2Error(
            "V2 operating-system release target differs"
        )
    value["schema_version"] = PREDECESSOR_SCHEMA_VERSION
    value["profile_id"] = PREDECESSOR_PROFILE_ID
    value["target"][
        "operating_system_release"
    ] = PREDECESSOR_OPERATING_SYSTEM_RELEASE
    value["record_sha256"] = "0" * 64
    predecessor = _with_predecessor_digest(value)
    return _validate_predecessor_projection(predecessor)


def build_draft_profile() -> Dict[str, object]:
    """Build the exact unresolved Ubuntu-24.04.4 V2 declaration."""

    return _from_v1_record(deepcopy(_PREDECESSOR_DRAFT))


def validate_profile(record: object) -> Dict[str, object]:
    """Validate V2 by exact projection onto the reviewed V1 semantics."""

    value = deepcopy(_exact_record(record))
    _to_v1_record(value)
    return value


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
    """Bind V1-equivalent observation metadata without granting authority."""

    value = validate_profile(draft)
    if value["lifecycle_state"] != DRAFT_UNRESOLVED_F152_LOCK:
        raise NativeRuntimeProfileV2Error("only the exact draft can bind a capture")
    digests = {
        "source_manifest_sha256": _exact_sha256(
            source_manifest_sha256, name="source_manifest_sha256"
        ),
        "installed_distribution_metadata_observation_sha256": _exact_sha256(
            installed_distribution_metadata_observation_sha256,
            name="installed_distribution_metadata_observation_sha256",
        ),
        "module_origin_observation_sha256": _exact_sha256(
            module_origin_observation_sha256,
            name="module_origin_observation_sha256",
        ),
        "python_abi_observation_sha256": _exact_sha256(
            python_abi_observation_sha256,
            name="python_abi_observation_sha256",
        ),
        "native_runtime_capture_sha256": _exact_sha256(
            native_runtime_capture_sha256,
            name="native_runtime_capture_sha256",
        ),
    }
    lock = _exact_sha256(lock_sha256, name="lock_sha256")
    if (
        type(source_revision) is not str
        or len(source_revision) not in (40, 64)
        or any(character not in _HEX for character in source_revision)
    ):
        raise NativeRuntimeProfileV2Error(
            "source_revision must be a lowercase Git digest"
        )

    result = deepcopy(value)
    result["lifecycle_state"] = OBSERVED_REVIEW_PENDING
    result["f152_lock"].update(
        {
            "sha256": lock,
            "present_and_regular": True,
            "complete_transitive_lock": False,
            "artifact_closure_verified": False,
            "all_requirements_exactly_pinned": True,
            "all_declared_requirements_sha256_hashed": True,
        }
    )
    result["runtime_bindings"].update(
        {"source_revision": source_revision, **digests}
    )
    result["resolution"].update(
        {
            "unresolved_paths": list(REVIEW_PENDING_UNRESOLVED_PATHS),
            "eligible_for_data_free_independent_review": True,
        }
    )
    return validate_profile(with_semantic_digest(result))


__all__ = (
    "DRAFT_UNRESOLVED_F152_LOCK",
    "EXPECTED_DISTRIBUTIONS",
    "EXPECTED_MODULES",
    "F152_LOCK_PATH",
    "F153_ENVIRONMENT",
    "LIFECYCLE_STATES",
    "NativeRuntimeProfileV2Error",
    "OBSERVED_REVIEW_PENDING",
    "PREDECESSOR_INDEPENDENT_REVIEW_SHA256",
    "PREDECESSOR_PROFILE_ID",
    "PREDECESSOR_PROFILE_PATH",
    "PREDECESSOR_RECORD_DOMAIN",
    "PREDECESSOR_PROFILE_SOURCE_SHA256",
    "PREDECESSOR_SCHEMA_VERSION",
    "PREDECESSOR_TEMPLATE_FILE_SHA256",
    "PREDECESSOR_TEMPLATE_RECORD_SHA256",
    "PROFILE_ID",
    "PROFILE_PATH",
    "RECORD_DOMAIN",
    "REVIEW_PENDING_UNRESOLVED_PATHS",
    "SCHEMA_VERSION",
    "TARGET_OPERATING_SYSTEM_RELEASE",
    "UNOBSERVED_TARGET_PATHS",
    "UNRESOLVED_PATHS",
    "bind_observed_capture",
    "build_draft_profile",
    "canonical_json_bytes",
    "semantic_projection",
    "semantic_sha256",
    "validate_profile",
    "with_semantic_digest",
)
