"""Fresh-process runtime-attestation protocol for the A1 campaign.

This module is deliberately independent of the production-order ledger.  It
defines a narrow, canonical, source-bound supervisor/worker protocol, but does
not itself authorize a scientific transition.  The numerical worker remains
fail closed until the target-generated identity manifest and the scientific
entry point are integrated by the production-order binder.

Only Python's standard library is imported at module import time and in the
ordinary protocol tests.  In particular, importing this module never imports
NumPy, SciPy, PyTorch, or the prerequisite implementation.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import platform
import secrets
import selectors
import signal
import stat
import subprocess
import sys
import time
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

# A ``-P -S`` script starts with no project path.  The worker intentionally
# leaves it that way until the canonical request and the complete production
# source manifest have been checked using only this already source-bound file
# and the standard library.  Normal library imports use the canonical package.
if __name__ == "__main__" and (__package__ is None or __package__ == ""):
    runtime_identity = None
else:
    from heterodiff.experiments import (
        finite_association_runtime_identity as runtime_identity,
    )


REQUEST_SCHEMA = "heterodiff-a1-production-runtime-attestor-request-v2"
OBSERVATION_SCHEMA = "heterodiff-a1-production-runtime-observation-v2"
ENVELOPE_SCHEMA = "heterodiff-a1-production-attested-prerequisite-envelope-v2"
TYPED_PREREQUISITE_SCHEMA = (
    "heterodiff-a1-production-prerequisite-typed-payload-v2"
)
RUNTIME_CONTRACT_SCHEMA = "heterodiff-a1-production-runtime-contract-v2"
RUNTIME_IDENTITY_MANIFEST_SCHEMA = (
    "heterodiff-a1-production-runtime-identity-manifest-v1"
)
RUNTIME_IDENTITY_APPROVAL_SCHEMA = (
    "heterodiff-a1-production-runtime-identity-approval-v1"
)
STABLE_RUNTIME_SCHEMA = "heterodiff-a1-production-stable-runtime-v2"
HASH_PROBE_SCHEMA = "heterodiff-a1-stdlib-hash-seed-probe-v1"

ATTESTED_PREREQUISITE_OPERATION = "FROZEN_PREREQUISITE_V2"
REVALIDATE_PREREQUISITE_OPERATION = "REVALIDATE_FROZEN_PREREQUISITE_V2"
_ALLOWED_OPERATIONS = frozenset(
    (ATTESTED_PREREQUISITE_OPERATION, REVALIDATE_PREREQUISITE_OPERATION)
)
_FROZEN_PREREQUISITE_DIGESTS = (
    "69b4bbea518ab816bb1e96952c3ddda5295257f66f0f8c902ba38eec10b6c339",
    "2c9da1e2e4d98e14d91459983a3b8fcbbf4b5409574863f68cba96642a89f08b",
    "09273f6bcee7c1a09165392e6ecf0125157b747d242c1f993a982ce3b2833cc7",
    "d6326ffb38c4c3ccf5aed1002f8cbd75fe5411f60d07172d5511730a63daba45",
    "ff37337476c48fee1c01e812f78cd22c7f2ed69298329f79cd87ab2aab3de937",
)
_PREREQUISITE_RESULT_FIELD_NAMES = (
    "generator_digest", "observation_digest", "population_digest",
    "guide_digest", "split_digest", "generator_row_sum_residual",
    "association_determinant", "ambiguous_permanent",
    "clean_overflow_minimum", "clean_overflow_maximum", "density_minimum",
    "density_maximum", "terminal_guide_log_error",
    "maximum_terminal_residual", "maximum_retained_initial_residual",
    "maximum_overall_initial_residual",
    "joint_weighted_initial_absolute_residual", "initial_overflow_probability",
    "retained_weighted_residual_share", "immigrant_terminal_mean",
    "immigrant_anchor_intensity", "target_harmonicity_residual",
    "guide_rank_propagation_residual", "correction_scale_ratio",
    "pair_partition_sizes", "passed", "failures",
)

RUNTIME_IDENTITY_RELATIVE_PATH = (
    "requirements/m1-reference-macos-arm64-py311.runtime-identity.json"
)
ATTESTOR_SOURCE_RELATIVE_PATH = (
    "src/heterodiff/experiments/finite_association_runtime_attestor.py"
)
MAXIMUM_REQUEST_BYTES = 64 * 1024
MAXIMUM_RESULT_BYTES = 4 * 1024 * 1024
MAXIMUM_IDENTITY_MANIFEST_BYTES = 16 * 1024 * 1024
# Includes three complete installed-identity passes on the reference M1; it is
# a fixed wall bound, not a caller option.
ATTESTOR_TIMEOUT_SECONDS = 600.0

_THREAD_ENVIRONMENT = {
    "BLIS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
}
_STARTUP_ENVIRONMENT = {
    "CUDA_VISIBLE_DEVICES": "",
    "LANG": "C",
    "LC_ALL": "C",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONPYCACHEPREFIX": "/dev/null",
    "PYTHONSAFEPATH": "1",
    "PYTHONUTF8": "1",
    "TZ": "UTC",
}
SANITIZED_CHILD_ENVIRONMENT = dict(
    sorted({**_THREAD_ENVIRONMENT, **_STARTUP_ENVIRONMENT}.items())
)
_DARWIN_INJECTED_ENVIRONMENT_NAME = "__CF_USER_TEXT_ENCODING"
EXPECTED_BUILTIN_HASH_PROBE_SHA256 = (
    "f7b1ba1308d7559c69fc44640d0fcd07dbeae53b9024da5d862463db71e230af"
)
_TORCH_GENERATED_MODULE_NAME = "_remote_module_non_scriptable"
_TORCH_GENERATED_MODULE_ORIGIN = "torch-git"
_TORCH_GENERATED_LOADER_MODULE = "torch.distributed.nn.jit.instantiator"
_TORCH_GENERATED_LOADER_QUALNAME = "_StringLoader"
_TORCH_GENERATED_SOURCE_SIZE_BYTES = 2355
_TORCH_GENERATED_SOURCE_SHA256 = (
    "8205b16956fb264841ecd8644784a0d157f87df79b17c16825dc1163433ce5d8"
)
_TORCH_MODULE_ALIASES = {
    "torch.classes": ("torch._classes", "_Classes", "_classes.py"),
    "torch.ops": ("torch._ops", "_Ops", "_ops.py"),
}
_BANNED_EXACT_ENVIRONMENT_NAMES = frozenset(("PYTHONHOME", "PYTHONPATH"))
_BANNED_ENVIRONMENT_PREFIXES = ("DYLD_", "LD_")
_verified_bootstrap_stdlib_sys_path: Optional[Tuple[str, ...]] = None


def _validated_darwin_worker_environment(
    observed: Mapping[str, str], *, uid: int
) -> Dict[str, str]:
    """Validate macOS's UID marker and return the effective allowlist.

    Darwin adds ``__CF_USER_TEXT_ENCODING`` after ``execve`` even when the
    supervisor supplies a complete environment.  The attested child admits
    only the exact UID-derived bootstrap value and removes it before project
    or numerical imports.
    """

    if type(observed) is not dict or any(
        type(key) is not str or type(value) is not str
        for key, value in observed.items()
    ):
        raise TypeError("runtime worker environment must be an exact string map")
    if type(uid) is not int or type(uid) is bool or uid < 0:
        raise TypeError("runtime worker UID must be a nonnegative exact integer")
    normalized = dict(observed)
    injected = normalized.pop(_DARWIN_INJECTED_ENVIRONMENT_NAME, None)
    if injected != "0x%X:0x0:0x0" % uid:
        raise RuntimeError(
            "Darwin injected runtime environment identity is unexpected"
        )
    if normalized != SANITIZED_CHILD_ENVIRONMENT:
        raise RuntimeError("runtime worker environment is not the exact allowlist")
    return normalized

_REQUEST_FIELDS = {
    "schema",
    "operation",
    "plan_sha256",
    "campaign_instance_nonce_sha256",
    "source_manifest_sha256",
    "runtime_contract_sha256",
    "runtime_identity_manifest_sha256",
    "attestor_source_sha256",
    "supervisor_pid",
    "supervisor_challenge",
    "request_sha256",
}
_OBSERVATION_FIELDS = {
    "schema",
    "phase",
    "request_schema",
    "request_sha256",
    "operation",
    "plan_sha256",
    "campaign_instance_nonce_sha256",
    "source_manifest_sha256",
    "runtime_contract_sha256",
    "runtime_identity_manifest_sha256",
    "supervisor_challenge",
    "child_pid",
    "parent_pid",
    "attestor_source_sha256",
    "environment_sha256",
    "stable_runtime",
    "stable_runtime_sha256",
    "observation_sha256",
}
_ENVELOPE_FIELDS = {
    "schema",
    "request_sha256",
    "supervisor_challenge",
    "child_pid",
    "parent_pid",
    "pre_observation",
    "post_observation",
    "stable_runtime_equal",
    "typed_prerequisite_result",
    "typed_prerequisite_result_sha256",
    "fixture_sha256",
    "envelope_sha256",
}


class RuntimeAttestorError(RuntimeError):
    """A fail-closed supervisor or protocol error with a stable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _plain_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain_json_value(item) for item in value]
    return value


def canonical_json_bytes(value: object) -> bytes:
    """Return the sole accepted ASCII JSON representation."""

    try:
        encoded = json.dumps(
            _plain_json_value(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ValueError("value is not finite canonical JSON") from error
    return encoded.encode("ascii")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _write_all(descriptor: int, payload: bytes) -> None:
    if type(descriptor) is not int or descriptor < 0 or type(payload) is not bytes:
        raise TypeError("bounded write requires an exact descriptor and bytes")
    offset = 0
    while offset < len(payload):
        try:
            written = os.write(descriptor, payload[offset:])
        except InterruptedError:
            continue
        if written <= 0:
            raise OSError("bounded write made no progress")
        offset += written


def _frozen_fixture_sha256() -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-a1-association-fixture-v1\0")
    for value in _FROZEN_PREREQUISITE_DIGESTS:
        digest.update(value.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _reject_duplicate_pairs(pairs: Sequence[Tuple[str, object]]) -> dict:
    value: Dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("canonical JSON contains a duplicate object key")
        value[key] = item
    return value


def _reject_nonfinite_constant(value: str) -> None:
    raise ValueError("canonical JSON contains a nonfinite value: %s" % value)


def decode_canonical_json(
    payload: bytes, *, maximum_bytes: int, description: str
) -> Dict[str, Any]:
    """Decode bounded canonical JSON, rejecting duplicates and nonfinite data."""

    if type(payload) is not bytes:
        raise TypeError("%s bytes must have exact bytes type" % description)
    if not payload or len(payload) > maximum_bytes:
        raise ValueError("%s has an invalid byte length" % description)
    try:
        text = payload.decode("ascii")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("%s is not canonical ASCII JSON" % description) from error
    if type(value) is not dict or canonical_json_bytes(value) != payload:
        raise ValueError("%s bytes are not canonical" % description)
    return value


def _is_sha256(value: object) -> bool:
    return type(value) is str and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _require_sha256(value: object, name: str) -> str:
    if not _is_sha256(value):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _require_positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or type(value) is not int or value <= 0:
        raise ValueError("%s must be a positive exact integer" % name)
    return value


def frozen_runtime_contract_v2(
    *,
    source_manifest_sha256: str,
    environment_lock_sha256: str,
    runtime_identity_manifest_sha256: str,
    minimum_macos_version: str,
) -> Dict[str, Any]:
    """Build the exact plan-specific target-runtime contract."""

    for name, value in (
        ("source_manifest_sha256", source_manifest_sha256),
        ("environment_lock_sha256", environment_lock_sha256),
        ("runtime_identity_manifest_sha256", runtime_identity_manifest_sha256),
    ):
        _require_sha256(value, name)
    if (
        type(minimum_macos_version) is not str
        or not minimum_macos_version
        or len(minimum_macos_version) > 32
        or any(part and not part.isdigit() for part in minimum_macos_version.split("."))
        or len(minimum_macos_version.split(".")) not in (2, 3)
    ):
        raise ValueError("minimum_macos_version is not canonical")
    return {
        "schema": RUNTIME_CONTRACT_SCHEMA,
        "python": {
            "implementation": "CPython",
            "version": "3.11.5",
            "abi": "cp311",
            "pointer_bits": 64,
            "byteorder": "little",
            "safe_path": True,
            "hash_seed_environment": "0",
            "builtin_hash_probe_sha256": EXPECTED_BUILTIN_HASH_PROBE_SHA256,
            "pycache_prefix": "/dev/null",
            "no_site": True,
        },
        "host": {
            "system": "Darwin",
            "machine": "arm64",
            "translated_x86": False,
            "minimum_macos_version": minimum_macos_version,
        },
        "versions": {
            "numpy": "2.4.6",
            "scipy": "1.17.1",
            "threadpoolctl": "3.6.0",
            "torch": "2.12.1",
        },
        "environment": dict(SANITIZED_CHILD_ENVIRONMENT),
        "native_pools": {
            "minimum_discovered_pool_count": 1,
            "every_discovered_pool_thread_count": 1,
        },
        "execution": {
            "device": "cpu",
            "execution_device_enforced_cpu": True,
            "deterministic_algorithms": True,
            "cuda_available": False,
            "cuda_initialized": False,
            "xpu_available": False,
            "xpu_initialized": False,
            "mps_capability_manifest_bound": True,
            "mps_operation_performed": False,
        },
        "runtime_identity_manifest_schema": RUNTIME_IDENTITY_MANIFEST_SCHEMA,
        "source_manifest_sha256": source_manifest_sha256,
        "environment_lock_sha256": environment_lock_sha256,
        "runtime_identity_manifest_sha256": runtime_identity_manifest_sha256,
    }


def frozen_runtime_contract_v2_sha256(**bindings: str) -> str:
    return sha256_json(frozen_runtime_contract_v2(**bindings))


def _validate_file_identity(value: object, *, name: str) -> Dict[str, Any]:
    if type(value) is not dict or set(value) != {"path", "size_bytes", "sha256"}:
        raise ValueError("%s file-identity schema is invalid" % name)
    path = value["path"]
    if type(path) is not str or not path or not Path(path).is_absolute():
        raise ValueError("%s path must be absolute" % name)
    size = value["size_bytes"]
    if isinstance(size, bool) or type(size) is not int or size < 0:
        raise ValueError("%s size is invalid" % name)
    _require_sha256(value["sha256"], "%s sha256" % name)
    return dict(value)


def validate_runtime_identity_manifest(value: Mapping[str, Any]) -> Dict[str, Any]:
    """Delegate the one manifest schema to the standard-library identity core."""

    return runtime_identity.validate_runtime_identity_manifest(value)


def _validate_digest_record(
    record: Mapping[str, Any], *, digest_field: str, schema_field: str, schema: str
) -> Dict[str, Any]:
    body = dict(record)
    claimed = _require_sha256(body.pop(digest_field, None), digest_field)
    if record.get(schema_field) != schema or sha256_json(body) != claimed:
        raise ValueError("%s digest/schema is invalid" % schema)
    return dict(record)


def validate_runtime_attestor_request(value: Mapping[str, Any]) -> Dict[str, Any]:
    if type(value) is not dict or set(value) != _REQUEST_FIELDS:
        raise ValueError("runtime-attestor request schema is invalid")
    record = _validate_digest_record(
        value,
        digest_field="request_sha256",
        schema_field="schema",
        schema=REQUEST_SCHEMA,
    )
    if record["operation"] not in _ALLOWED_OPERATIONS:
        raise ValueError("runtime-attestor operation is not frozen")
    for name in (
        "plan_sha256",
        "campaign_instance_nonce_sha256",
        "source_manifest_sha256",
        "runtime_contract_sha256",
        "runtime_identity_manifest_sha256",
        "attestor_source_sha256",
        "supervisor_challenge",
    ):
        _require_sha256(record[name], name)
    _require_positive_integer(record["supervisor_pid"], "supervisor_pid")
    return record


def _plan_bindings(plan: Mapping[str, Any]) -> Dict[str, str]:
    if not isinstance(plan, Mapping):
        raise TypeError("runtime attestation plan must be a mapping")
    identity_reference = plan.get("runtime_identity_manifest")
    required_reference = {
        "schema",
        "relative_path",
        "manifest_schema",
        "manifest_sha256",
        "environment_lock_sha256",
        "component_sha256",
        "runtime_projection_sha256",
        "approved",
    }
    if (
        not isinstance(identity_reference, Mapping)
        or set(identity_reference) != required_reference
        or identity_reference.get("relative_path")
        != runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH
        or identity_reference.get("manifest_schema")
        != runtime_identity.RUNTIME_IDENTITY_MANIFEST_SCHEMA
        or identity_reference.get("approved") is not True
    ):
        raise ValueError("production plan runtime identity reference is invalid")
    components = identity_reference["component_sha256"]
    expected_components = {
        "profile",
        "python_files",
        "modules",
        "distributions",
        "editable_install",
        "native_libraries",
        "native_pools",
        "accelerators",
    }
    if not isinstance(components, Mapping) or set(components) != expected_components:
        raise ValueError("production plan identity components are invalid")
    for name, value in components.items():
        _require_sha256(value, "identity component %s" % name)
    projections = identity_reference["runtime_projection_sha256"]
    if not isinstance(projections, Mapping) or set(projections) != {
        "distributions"
    }:
        raise ValueError("production plan runtime projections are invalid")
    _require_sha256(projections["distributions"], "distribution runtime projection")
    bindings = {
        "plan_sha256": plan.get("plan_sha256"),
        "campaign_instance_nonce_sha256": plan.get(
            "campaign_instance_nonce_sha256"
        ),
        "source_manifest_sha256": plan.get("source_manifest_sha256"),
        "runtime_identity_manifest_sha256": identity_reference.get(
            "manifest_sha256"
        ),
    }
    for name, value in bindings.items():
        _require_sha256(value, name)
    runtime_contract = plan.get("runtime_contract")
    if not isinstance(runtime_contract, Mapping):
        raise ValueError("production plan runtime contract v2 is absent")
    minimum_macos_version = runtime_contract.get("host", {}).get(
        "minimum_macos_version"
    )
    expected_contract = frozen_runtime_contract_v2(
        source_manifest_sha256=bindings["source_manifest_sha256"],
        environment_lock_sha256=identity_reference[
            "environment_lock_sha256"
        ],
        runtime_identity_manifest_sha256=bindings[
            "runtime_identity_manifest_sha256"
        ],
        minimum_macos_version=minimum_macos_version,
    )
    if _plain_json_value(runtime_contract) != expected_contract:
        raise ValueError("production plan runtime contract v2 is not frozen")
    bindings["runtime_contract_sha256"] = sha256_json(runtime_contract)
    return bindings


def _validate_stable_runtime(
    value: object,
    *,
    request: Mapping[str, Any],
    runtime_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    required = {
        "schema",
        "python",
        "runtime_profile",
        "versions",
        "environment",
        "effective_hash_seed",
        "host",
        "runtime_identity_component_sha256",
        "python_files",
        "module_origins",
        "distribution_metadata",
        "editable_install_identity",
        "native_libraries",
        "native_pools",
        "accelerator_identity",
        "numpy_configuration",
        "torch_device_state",
        "source_manifest_sha256",
        "runtime_contract_sha256",
        "runtime_identity_manifest_sha256",
    }
    if type(value) is not dict or set(value) != required:
        raise ValueError("stable-runtime schema is invalid")
    if value["schema"] != STABLE_RUNTIME_SCHEMA:
        raise ValueError("stable-runtime schema identifier is invalid")
    if value["source_manifest_sha256"] != request["source_manifest_sha256"]:
        raise ValueError("stable runtime has the wrong source binding")
    if value["runtime_contract_sha256"] != request["runtime_contract_sha256"]:
        raise ValueError("stable runtime has the wrong contract binding")
    if (
        value["runtime_identity_manifest_sha256"]
        != request["runtime_identity_manifest_sha256"]
    ):
        raise ValueError("stable runtime has the wrong identity binding")
    components = value["runtime_identity_component_sha256"]
    expected_components = request.get("_identity_component_sha256")
    if expected_components is not None and components != expected_components:
        raise ValueError("stable runtime identity components differ from the plan")
    if type(components) is not dict or set(components) != {
        "profile",
        "python_files",
        "modules",
        "distributions",
        "editable_install",
        "native_libraries",
        "native_pools",
        "accelerators",
    }:
        raise ValueError("stable runtime identity-component schema is invalid")
    for name, digest in components.items():
        _require_sha256(digest, "stable identity component %s" % name)
    profile = value["runtime_profile"]
    if type(profile) is not dict or sha256_json(profile) != components["profile"]:
        raise ValueError("stable runtime profile differs from approved identity")
    if (
        profile.get("python_abi") != "cp311"
        or type(profile.get("minimum_macos_version")) is not str
        or not profile["minimum_macos_version"]
    ):
        raise ValueError("stable ABI/minimum macOS profile is invalid")
    if value["versions"] != runtime_contract["versions"]:
        raise ValueError("stable numerical package versions differ from contract")
    if value["environment"] != SANITIZED_CHILD_ENVIRONMENT:
        raise ValueError("stable child environment is not the exact allowlist")
    if sha256_json(value["python_files"]) != components["python_files"]:
        raise ValueError("stable Python file identities differ from approved inventory")
    if sha256_json(value["module_origins"]) != components["modules"]:
        raise ValueError("stable module origins differ from approved inventory")
    if sha256_json(value["native_libraries"]) != components["native_libraries"]:
        raise ValueError("stable native libraries differ from approved inventory")
    if sha256_json(value["editable_install_identity"]) != components[
        "editable_install"
    ]:
        raise ValueError("stable editable-install identity differs from approved inventory")
    accelerator_identity = value["accelerator_identity"]
    if sha256_json(accelerator_identity) != components["accelerators"]:
        raise ValueError("stable accelerator identity differs from approved inventory")
    distributions = value["distribution_metadata"]
    if type(distributions) is not list or len(distributions) != len(
        runtime_identity.REQUIRED_DISTRIBUTIONS
    ):
        raise ValueError("stable distribution metadata evidence is incomplete")
    for row, expected_distribution in zip(
        distributions, runtime_identity.REQUIRED_DISTRIBUTIONS
    ):
        if type(row) is not dict or set(row) != {
            "name", "version", "origin", "metadata_files"
        }:
            raise ValueError("stable distribution metadata row is invalid")
        if any(
            type(row[name]) is not str or not row[name]
            for name in ("name", "version", "origin")
        ) or type(row["metadata_files"]) is not list:
            raise ValueError("stable distribution metadata identity is incomplete")
        if (row["name"], row["version"]) != expected_distribution:
            raise ValueError("stable distribution order/version is not frozen")
    python = value["python"]
    if type(python) is not dict or set(python) != {
        "implementation",
        "version",
        "pointer_bits",
        "byteorder",
        "safe_path",
        "soabi",
        "pycache_prefix",
        "no_site",
    }:
        raise ValueError("stable Python identity schema is invalid")
    contract = runtime_contract["python"]
    expected_python = {
        key: contract[key]
        for key in (
            "implementation",
            "version",
            "pointer_bits",
            "byteorder",
            "safe_path",
        )
    }
    expected_python["soabi"] = "cpython-311-darwin"
    expected_python["pycache_prefix"] = contract["pycache_prefix"]
    expected_python["no_site"] = contract["no_site"]
    if python != expected_python:
        raise ValueError("stable Python identity is outside the contract")
    if python["soabi"] != "cpython-311-darwin":
        raise ValueError("stable Python SOABI is not the approved cp311 ABI")
    seed = value["effective_hash_seed"]
    if type(seed) is not dict or set(seed) != {
        "environment_value",
        "hash_randomization_flag",
        "builtin_hash_probe_sha256",
    }:
        raise ValueError("effective hash-seed schema is invalid")
    if seed["environment_value"] != "0" or seed["hash_randomization_flag"] != 0:
        raise ValueError("PYTHONHASHSEED=0 was not effective at startup")
    _require_sha256(seed["builtin_hash_probe_sha256"], "hash probe")
    if seed["builtin_hash_probe_sha256"] != EXPECTED_BUILTIN_HASH_PROBE_SHA256:
        raise ValueError("built-in hash probe differs from the frozen contract")
    host = value["host"]
    if type(host) is not dict or set(host) != {
        "system", "machine", "translated_x86", "macos_version"
    } or (
        host["system"] != "Darwin"
        or host["machine"] != "arm64"
        or host["translated_x86"] is not False
        or type(host["macos_version"]) is not str
        or not host["macos_version"]
    ):
        raise ValueError("stable host identity is outside the target contract")
    try:
        observed_macos = tuple(int(part) for part in host["macos_version"].split("."))
        minimum_macos = tuple(
            int(part)
            for part in runtime_contract["host"]["minimum_macos_version"].split(".")
        )
    except (TypeError, ValueError) as error:
        raise ValueError("stable macOS version is not canonical") from error
    width = max(len(observed_macos), len(minimum_macos))
    if observed_macos + (0,) * (width - len(observed_macos)) < minimum_macos + (
        0,
    ) * (width - len(minimum_macos)):
        raise ValueError("stable macOS version is below the approved minimum")
    pools = value["native_pools"]
    if type(pools) is not list or not pools:
        raise ValueError("stable native-pool evidence is empty")
    pool_paths = []
    for row in pools:
        if type(row) is not dict or set(row) != {
            "library_path",
            "user_api",
            "internal_api",
            "prefix",
            "version",
            "num_threads",
        }:
            raise ValueError("stable native-pool row schema is invalid")
        if type(row["library_path"]) is not str or not Path(
            row["library_path"]
        ).is_absolute():
            raise ValueError("stable native-pool path is not absolute")
        if any(
            type(row[name]) is not str or not row[name]
            for name in ("user_api", "internal_api", "prefix")
        ) or (
            row["version"] is not None
            and (type(row["version"]) is not str or not row["version"])
        ):
            raise ValueError("stable native-pool identity is incomplete")
        if type(row["num_threads"]) is not int or row["num_threads"] != 1:
            raise ValueError("stable native pool is not single-threaded")
        pool_paths.append(row["library_path"])
    if pool_paths != sorted(pool_paths) or len(pool_paths) != len(set(pool_paths)):
        raise ValueError("stable native-pool paths are not unique and ordered")
    if sha256_json(pools) != components["native_pools"]:
        raise ValueError("stable native pools differ from approved inventory")
    configuration = value["numpy_configuration"]
    if type(configuration) is not dict or not configuration:
        raise ValueError("stable NumPy configuration is absent")
    canonical_json_bytes(configuration)
    torch_state = value["torch_device_state"]
    if type(torch_state) is not dict or set(torch_state) != {
        "execution_device",
        "execution_device_enforced_cpu",
        "deterministic_algorithms",
        "torch_threads",
        "torch_interop_threads",
        "cuda_available",
        "cuda_initialized",
        "cuda_device_count",
        "xpu_available",
        "xpu_initialized",
        "xpu_device_count",
        "mps_built",
        "mps_available",
        "mps_operation_performed",
    }:
        raise ValueError("stable Torch/device-state schema is invalid")
    if (
        torch_state["execution_device"] != "cpu"
        or torch_state["execution_device_enforced_cpu"] is not True
        or torch_state["deterministic_algorithms"] is not True
        or torch_state["torch_threads"] != 1
        or type(torch_state["torch_threads"]) is not int
        or torch_state["torch_interop_threads"] != 1
        or type(torch_state["torch_interop_threads"]) is not int
        or torch_state["cuda_available"] is not False
        or torch_state["cuda_initialized"] is not False
        or torch_state["cuda_device_count"] != 0
        or torch_state["xpu_available"] is not False
        or torch_state["xpu_initialized"] is not False
        or torch_state["xpu_device_count"] != 0
        or type(torch_state["mps_built"]) is not bool
        or type(torch_state["mps_available"]) is not bool
        or torch_state["mps_operation_performed"] is not False
    ):
        raise ValueError("stable Torch/device state is not CPU-enforced")
    if (
        type(accelerator_identity) is not dict
        or set(accelerator_identity) != {
            "execution_device_enforced_cpu", "cuda", "xpu", "mps"
        }
        or torch_state["execution_device_enforced_cpu"]
        != accelerator_identity["execution_device_enforced_cpu"]
        or torch_state["cuda_available"]
        != accelerator_identity["cuda"]["available"]
        or torch_state["cuda_initialized"]
        != accelerator_identity["cuda"]["initialized"]
        or torch_state["cuda_device_count"]
        != accelerator_identity["cuda"]["device_count"]
        or torch_state["xpu_available"]
        != accelerator_identity["xpu"]["available"]
        or torch_state["xpu_initialized"]
        != accelerator_identity["xpu"]["initialized"]
        or torch_state["xpu_device_count"]
        != accelerator_identity["xpu"]["device_count"]
        or torch_state["mps_built"] != accelerator_identity["mps"]["built"]
        or torch_state["mps_available"]
        != accelerator_identity["mps"]["available"]
        or torch_state["mps_operation_performed"]
        != accelerator_identity["mps"]["operation_performed"]
    ):
        raise ValueError("stable accelerator observation differs from approved identity")
    return dict(value)


def runtime_attestor_request_from_observation(
    value: Mapping[str, Any],
) -> Dict[str, Any]:
    """Reconstruct the request needed for immutable historical validation."""

    if type(value) is not dict or set(value) != _OBSERVATION_FIELDS:
        raise ValueError("runtime observation schema is invalid")
    body = {
        "schema": value["request_schema"],
        "operation": value["operation"],
        "plan_sha256": value["plan_sha256"],
        "campaign_instance_nonce_sha256": value[
            "campaign_instance_nonce_sha256"
        ],
        "source_manifest_sha256": value["source_manifest_sha256"],
        "runtime_contract_sha256": value["runtime_contract_sha256"],
        "runtime_identity_manifest_sha256": value[
            "runtime_identity_manifest_sha256"
        ],
        "attestor_source_sha256": value["attestor_source_sha256"],
        "supervisor_pid": value["parent_pid"],
        "supervisor_challenge": value["supervisor_challenge"],
    }
    request = dict(body)
    request["request_sha256"] = value["request_sha256"]
    return validate_runtime_attestor_request(request)


def validate_runtime_attestor_observation(
    value: Mapping[str, Any], *, plan: Mapping[str, Any]
) -> Dict[str, Any]:
    """Validate a durable PRE/POST observation without probing the host."""

    if type(value) is not dict or set(value) != _OBSERVATION_FIELDS:
        raise ValueError("runtime observation schema is invalid")
    record = _validate_digest_record(
        value,
        digest_field="observation_sha256",
        schema_field="schema",
        schema=OBSERVATION_SCHEMA,
    )
    if record["phase"] not in ("PRE", "POST"):
        raise ValueError("runtime observation phase is invalid")
    request = runtime_attestor_request_from_observation(record)
    bindings = _plan_bindings(plan)
    for name, expected in bindings.items():
        if request[name] != expected:
            raise ValueError("runtime observation has the wrong plan binding")
    if record["request_schema"] != REQUEST_SCHEMA:
        raise ValueError("runtime observation request schema is invalid")
    _require_positive_integer(record["child_pid"], "child_pid")
    _require_positive_integer(record["parent_pid"], "parent_pid")
    if record["environment_sha256"] != sha256_json(SANITIZED_CHILD_ENVIRONMENT):
        raise ValueError("runtime observation environment is not sanitized")
    stable = _validate_stable_runtime(
        record["stable_runtime"],
        request=request,
        runtime_contract=plan["runtime_contract"],
    )
    if (
        stable["runtime_identity_component_sha256"]
        != plan["runtime_identity_manifest"]["component_sha256"]
    ):
        raise ValueError("stable runtime components differ from the plan")
    if sha256_json(stable["distribution_metadata"]) != plan[
        "runtime_identity_manifest"
    ]["runtime_projection_sha256"]["distributions"]:
        raise ValueError("stable distribution projection differs from the plan")
    if record["stable_runtime_sha256"] != sha256_json(stable):
        raise ValueError("stable-runtime digest is invalid")
    return record


def _validate_typed_prerequisite_payload(value: object) -> Dict[str, Any]:
    if type(value) is not dict or set(value) != {
        "schema",
        "class_module",
        "class_name",
        "fields",
    }:
        raise ValueError("typed prerequisite payload schema is invalid")
    if value["schema"] != TYPED_PREREQUISITE_SCHEMA:
        raise ValueError("typed prerequisite schema identifier is invalid")
    if (
        value["class_module"]
        != "heterodiff.experiments.finite_association_guided_residual_pilot"
        or value["class_name"] != "AssociationResidualPrerequisiteResult"
    ):
        raise ValueError("typed prerequisite class identity is invalid")
    rows = value["fields"]
    if type(rows) is not list or not rows:
        raise ValueError("typed prerequisite fields are empty")
    names = []
    for row in rows:
        if type(row) is not dict or set(row) != {"name", "value"}:
            raise ValueError("typed prerequisite field row is invalid")
        if type(row["name"]) is not str or not row["name"]:
            raise ValueError("typed prerequisite field name is invalid")
        names.append(row["name"])
        encoded = row["value"]
        if type(encoded) is not dict or set(encoded) != {"kind", "value"}:
            raise ValueError("typed prerequisite field encoding is invalid")
        kind = encoded["kind"]
        item = encoded["value"]
        if kind == "scalar":
            if type(item) not in (str, bool, int) and item is not None:
                raise ValueError("typed scalar has an invalid exact type")
        elif kind == "float64-hex":
            if type(item) is not str:
                raise ValueError("typed float is not hexadecimal text")
            try:
                parsed = float.fromhex(item)
            except ValueError as error:
                raise ValueError("typed float is invalid") from error
            if not math.isfinite(parsed) or parsed.hex() != item:
                raise ValueError("typed float is nonfinite or noncanonical")
        elif kind == "string-tuple":
            if type(item) is not list or not all(
                type(part) is str and part for part in item
            ):
                raise ValueError("typed string tuple is invalid")
        elif kind == "ndarray":
            if type(item) is not dict or set(item) != {
                "dtype",
                "shape",
                "content_sha256",
            }:
                raise ValueError("typed ndarray metadata is invalid")
            if type(item["dtype"]) is not str or not item["dtype"]:
                raise ValueError("typed ndarray dtype is invalid")
            if type(item["shape"]) is not list or not all(
                type(part) is int and not isinstance(part, bool) and part >= 0
                for part in item["shape"]
            ):
                raise ValueError("typed ndarray shape is invalid")
            _require_sha256(item["content_sha256"], "typed ndarray content")
        else:
            raise ValueError("typed prerequisite field kind is invalid")
    if len(names) != len(set(names)):
        raise ValueError("typed prerequisite field names are duplicated")
    if tuple(names) != _PREREQUISITE_RESULT_FIELD_NAMES:
        raise ValueError("typed prerequisite field order is not frozen")
    by_name = {row["name"]: row["value"] for row in rows}
    for name, expected in zip(
        _PREREQUISITE_RESULT_FIELD_NAMES[:5], _FROZEN_PREREQUISITE_DIGESTS
    ):
        if by_name[name] != {"kind": "scalar", "value": expected}:
            raise ValueError("typed prerequisite digest field changed")
    if by_name["passed"] != {"kind": "scalar", "value": True}:
        raise ValueError("typed prerequisite result did not pass")
    if by_name["failures"] != {"kind": "string-tuple", "value": []}:
        raise ValueError("typed prerequisite result contains failures")
    array_names = {
        "immigrant_terminal_mean",
        "immigrant_anchor_intensity",
        "pair_partition_sizes",
    }
    for name in _PREREQUISITE_RESULT_FIELD_NAMES[5:-2]:
        expected_kind = "ndarray" if name in array_names else "float64-hex"
        if by_name[name]["kind"] != expected_kind:
            raise ValueError("typed prerequisite field kind changed")
    return dict(value)


def validate_runtime_attestor_envelope(
    value: Mapping[str, Any],
    *,
    plan: Mapping[str, Any],
    expected_child_pid: Optional[int] = None,
    expected_parent_pid: Optional[int] = None,
) -> Dict[str, Any]:
    """Validate an envelope both live and during durable receipt reload."""

    if type(value) is not dict or set(value) != _ENVELOPE_FIELDS:
        raise ValueError("runtime-attestor envelope schema is invalid")
    record = _validate_digest_record(
        value,
        digest_field="envelope_sha256",
        schema_field="schema",
        schema=ENVELOPE_SCHEMA,
    )
    pre = validate_runtime_attestor_observation(
        record["pre_observation"], plan=plan
    )
    post = validate_runtime_attestor_observation(
        record["post_observation"], plan=plan
    )
    request = runtime_attestor_request_from_observation(pre)
    if runtime_attestor_request_from_observation(post) != request:
        raise ValueError("PRE and POST observations bind different requests")
    if (
        pre["phase"] != "PRE"
        or post["phase"] != "POST"
        or pre["stable_runtime"] != post["stable_runtime"]
        or record["stable_runtime_equal"] is not True
    ):
        raise ValueError("PRE/POST stable runtime identity drifted")
    child_pid = _require_positive_integer(record["child_pid"], "child_pid")
    parent_pid = _require_positive_integer(record["parent_pid"], "parent_pid")
    if any(item["child_pid"] != child_pid for item in (pre, post)):
        raise ValueError("envelope and observation child PIDs differ")
    if any(item["parent_pid"] != parent_pid for item in (pre, post)):
        raise ValueError("envelope and observation parent PIDs differ")
    if expected_child_pid is not None and child_pid != expected_child_pid:
        raise ValueError("attestor child PID does not match the spawned process")
    if expected_parent_pid is not None and parent_pid != expected_parent_pid:
        raise ValueError("attestor PPID does not match the supervisor")
    if (
        record["request_sha256"] != request["request_sha256"]
        or record["supervisor_challenge"] != request["supervisor_challenge"]
    ):
        raise ValueError("attestor envelope challenge/request binding is invalid")
    payload = _validate_typed_prerequisite_payload(
        record["typed_prerequisite_result"]
    )
    if record["typed_prerequisite_result_sha256"] != sha256_json(payload):
        raise ValueError("typed prerequisite payload digest is invalid")
    if record["fixture_sha256"] != _frozen_fixture_sha256():
        raise ValueError("attested prerequisite fixture digest is invalid")
    return record


def _read_canonical_file(path: Path, maximum_bytes: int) -> Dict[str, Any]:
    status = path.lstat()
    if not stat.S_ISREG(status.st_mode) or status.st_size > maximum_bytes:
        raise ValueError("runtime identity path is not a bounded regular file")
    descriptor = os.open(
        os.fspath(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
        ) != (
            status.st_dev,
            status.st_ino,
            status.st_size,
            status.st_mtime_ns,
        ):
            raise RuntimeError("runtime identity changed while opening")
        payload = b""
        while len(payload) <= maximum_bytes:
            block = os.read(descriptor, min(65536, maximum_bytes + 1 - len(payload)))
            if not block:
                break
            payload += block
    finally:
        os.close(descriptor)
    return decode_canonical_json(
        payload,
        maximum_bytes=maximum_bytes,
        description="runtime identity manifest",
    )


def _hash_regular_file(path: Path, maximum_bytes: int) -> Tuple[str, int]:
    status = path.lstat()
    if not stat.S_ISREG(status.st_mode) or status.st_size > maximum_bytes:
        raise ValueError("source-bound executable path is not a bounded regular file")
    descriptor = os.open(
        os.fspath(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    )
    digest = hashlib.sha256()
    consumed = 0
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
        ) != (status.st_dev, status.st_ino):
            raise RuntimeError("source-bound file changed while opening")
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            consumed += len(block)
            if consumed > maximum_bytes:
                raise ValueError("source-bound file exceeded its byte limit")
            digest.update(block)
    finally:
        os.close(descriptor)
    after = path.lstat()
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
        status.st_dev,
        status.st_ino,
        status.st_size,
        status.st_mtime_ns,
    ):
        raise RuntimeError("source-bound file changed while hashing")
    return digest.hexdigest(), consumed


def _require_source_ancestors(workspace: Path, path: Path) -> None:
    candidate = Path(os.path.abspath(os.fspath(path)))
    root = Path(os.path.abspath(os.fspath(workspace)))
    try:
        relative = candidate.relative_to(root)
    except ValueError as error:
        raise RuntimeError("worker bootstrap source escaped the workspace") from error
    current = root
    for part in relative.parts[:-1]:
        status = current.lstat()
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise RuntimeError("worker bootstrap source ancestor is not a real directory")
        current = current / part
    status = current.lstat()
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
        raise RuntimeError("worker bootstrap source ancestor is not a real directory")


def _capture_bootstrap_stdlib_sys_path() -> Tuple[str, ...]:
    """Admit only the path shape produced by the fixed ``-P -S`` startup."""

    import sysconfig

    if not sys.path or any(
        type(value) is not str or not value or not os.path.isabs(value)
        for value in sys.path
    ):
        raise RuntimeError("worker bootstrap sys.path is not absolute and bounded")
    normalized = tuple(os.path.abspath(value) for value in sys.path)
    if tuple(sys.path) != normalized:
        raise RuntimeError("worker bootstrap sys.path is not canonical")
    if len(normalized) != len(set(normalized)):
        raise RuntimeError("worker bootstrap sys.path contains duplicates")
    configured = sysconfig.get_paths()
    stdlib_roots = {
        os.path.abspath(configured[name])
        for name in ("stdlib", "platstdlib")
        if configured.get(name)
    }
    site_roots = {
        os.path.abspath(configured[name])
        for name in ("purelib", "platlib")
        if configured.get(name)
    }
    zip_path = os.path.abspath(
        os.path.join(
            sys.base_prefix,
            "lib",
            "python%d%d.zip" % (sys.version_info.major, sys.version_info.minor),
        )
    )

    def beneath(path: str, roots: set[str]) -> bool:
        return any(
            os.path.commonpath((path, root)) == root for root in roots
        )

    for path in normalized:
        if beneath(path, site_roots):
            raise RuntimeError("worker bootstrap sys.path contains site packages")
        if path != zip_path and not beneath(path, stdlib_roots):
            raise RuntimeError("worker bootstrap sys.path escaped the standard library")
    return normalized


def _validate_worker_source_layout(
    workspace: Path, source_root: Path
) -> Tuple[str, ...]:
    """Return source files only after excluding every import shadow.

    Tagged files below ``__pycache__`` cannot be selected because the fixed
    process starts with ``PYTHONPYCACHEPREFIX=/dev/null``.  Legacy bytecode,
    extension modules, and unexpected siblings of the project package remain
    import candidates, so they are rejected before any project path is added.
    """

    import importlib.machinery
    import re

    if (
        sys.pycache_prefix != SANITIZED_CHILD_ENVIRONMENT[
            "PYTHONPYCACHEPREFIX"
        ]
        or sys.dont_write_bytecode is not True
        or not sys.flags.no_site
        or not sys.flags.safe_path
    ):
        raise RuntimeError("worker bootstrap interpreter flags are not exact")
    source_parent = workspace / "src"
    _require_source_ancestors(workspace, source_parent)
    parent_status = source_parent.lstat()
    if stat.S_ISLNK(parent_status.st_mode) or not stat.S_ISDIR(
        parent_status.st_mode
    ):
        raise RuntimeError("worker bootstrap src root is not a real directory")

    for sibling in sorted(source_parent.iterdir(), key=lambda path: path.name):
        status = sibling.lstat()
        if stat.S_ISLNK(status.st_mode):
            raise RuntimeError("worker bootstrap src sibling is a symlink")
        if sibling.name == "heterodiff":
            if sibling != source_root or not stat.S_ISDIR(status.st_mode):
                raise RuntimeError("worker bootstrap package root is invalid")
            continue
        if sibling.name == "heterodiff.egg-info":
            if not stat.S_ISDIR(status.st_mode):
                raise RuntimeError("worker bootstrap egg-info is not a directory")
            entries = sorted(sibling.iterdir(), key=lambda path: path.name)
            if len(entries) > 64:
                raise RuntimeError("worker bootstrap egg-info is unbounded")
            for entry in entries:
                entry_status = entry.lstat()
                if stat.S_ISLNK(entry_status.st_mode) or not stat.S_ISREG(
                    entry_status.st_mode
                ):
                    raise RuntimeError(
                        "worker bootstrap egg-info contains an unsafe entry"
                    )
            continue
        raise RuntimeError("worker bootstrap src contains an unexpected sibling")

    extension_suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
    discovered = []
    for path in source_root.rglob("*"):
        status = path.lstat()
        if stat.S_ISLNK(status.st_mode):
            raise RuntimeError("worker bootstrap source closure contains a symlink")
        relative = path.relative_to(source_root)
        beneath_cache = "__pycache__" in relative.parts
        if beneath_cache:
            if stat.S_ISDIR(status.st_mode):
                if path.name != "__pycache__":
                    raise RuntimeError(
                        "worker bootstrap cache contains a nested directory"
                    )
                continue
            match = re.fullmatch(
                r"([A-Za-z_][A-Za-z0-9_]*)\.cpython-[0-9]+"
                r"(?:\.opt-[0-9]+)?\.pyc",
                path.name,
            )
            if not stat.S_ISREG(status.st_mode) or match is None:
                raise RuntimeError(
                    "worker bootstrap cache contains an importable artifact"
                )
            source = path.parent.parent / (match.group(1) + ".py")
            try:
                source_status = source.lstat()
            except FileNotFoundError as error:
                raise RuntimeError(
                    "worker bootstrap cache lacks its source file"
                ) from error
            if stat.S_ISLNK(source_status.st_mode) or not stat.S_ISREG(
                source_status.st_mode
            ):
                raise RuntimeError(
                    "worker bootstrap cache lacks its regular source file"
                )
            continue
        if stat.S_ISDIR(status.st_mode):
            continue
        if not stat.S_ISREG(status.st_mode):
            raise RuntimeError("worker bootstrap source is not a regular file")
        if path.name.endswith(extension_suffixes):
            raise RuntimeError("worker bootstrap source contains an extension shadow")
        if path.suffix in (".pyc", ".pyo"):
            raise RuntimeError("worker bootstrap source contains legacy bytecode")
        if path.suffix != ".py":
            raise RuntimeError("worker bootstrap source contains an unbound file")
        discovered.append(path.relative_to(workspace).as_posix())
    return tuple(discovered)


def _bootstrap_worker_project(request: Mapping[str, Any]) -> None:
    """Verify the full source closure before executing any project import."""

    global runtime_identity, _verified_bootstrap_stdlib_sys_path
    if runtime_identity is not None:
        raise RuntimeError("worker project bootstrap may run only once")
    if _verified_bootstrap_stdlib_sys_path is not None:
        raise RuntimeError("worker bootstrap sys.path was already captured")
    _verified_bootstrap_stdlib_sys_path = _capture_bootstrap_stdlib_sys_path()
    worker = Path(os.path.abspath(__file__))
    workspace = worker.parents[3]
    source_root = workspace / "src" / "heterodiff"
    _require_source_ancestors(workspace, source_root)
    if not stat.S_ISDIR(source_root.lstat().st_mode):
        raise RuntimeError("worker bootstrap source root is not a directory")
    discovered = _validate_worker_source_layout(workspace, source_root)
    paths = tuple(
        sorted(
            set(discovered).union(
                (
                    "pyproject.toml",
                    "requirements/m1-reference-macos-arm64-py311.lock",
                    "research/62_a1_association_guided_residual_falsification_spec.md",
                )
            )
        )
    )
    identities = []
    for relative in paths:
        path = workspace / relative
        _require_source_ancestors(workspace, path)
        digest, size = _hash_regular_file(path, 32 * 1024 * 1024)
        identities.append(
            {"path": relative, "sha256": digest, "size_bytes": size}
        )
    if sha256_json(identities) != request["source_manifest_sha256"]:
        raise RuntimeError("worker bootstrap source manifest is stale")
    worker_row = next(
        row for row in identities if row["path"] == ATTESTOR_SOURCE_RELATIVE_PATH
    )
    if worker_row["sha256"] != request["attestor_source_sha256"]:
        raise RuntimeError("worker bootstrap attestor source is stale")

    import importlib.util

    identity_path = workspace / (
        "src/heterodiff/experiments/finite_association_runtime_identity.py"
    )
    module_name = "_heterodiff_attested_runtime_identity"
    specification = importlib.util.spec_from_file_location(
        module_name, os.fspath(identity_path)
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("verified runtime-identity module cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    if (
        module.RUNTIME_IDENTITY_MANIFEST_SCHEMA
        != RUNTIME_IDENTITY_MANIFEST_SCHEMA
    ):
        raise RuntimeError("verified runtime-identity module schema changed")
    runtime_identity = module
    verified_source_root = workspace / "src"
    if os.fspath(verified_source_root) not in sys.path:
        sys.path.append(os.fspath(verified_source_root))


def _verify_bound_file(identity: Mapping[str, Any], expected: Path) -> None:
    checked = _validate_file_identity(identity, name="launch identity")
    lexical = Path(checked["path"])
    if lexical != expected or lexical.is_symlink():
        raise ValueError("source-bound launch path is not the approved absolute path")
    digest, size = _hash_regular_file(lexical, 1024 * 1024 * 1024)
    if digest != checked["sha256"] or size != checked["size_bytes"]:
        raise ValueError("source-bound launch bytes differ from the manifest")


def _reject_parent_environment_leakage() -> None:
    leaked = sorted(
        key
        for key in os.environ
        if key in _BANNED_EXACT_ENVIRONMENT_NAMES
        or key.startswith(_BANNED_ENVIRONMENT_PREFIXES)
    )
    if leaked:
        raise RuntimeAttestorError(
            "ENVIRONMENT_LEAKAGE",
            "forbidden loader/startup environment is present: %s"
            % ", ".join(leaked),
        )


def _snapshot_plan(snapshot: object) -> Mapping[str, Any]:
    plan = getattr(snapshot, "plan", None)
    if not isinstance(plan, Mapping):
        raise TypeError("runtime attestor requires a canonical snapshot plan")
    if getattr(snapshot, "plan_sha256", None) != plan.get("plan_sha256"):
        raise ValueError("snapshot plan digest property is inconsistent")
    if (
        getattr(snapshot, "campaign_instance_nonce_sha256", None)
        != plan.get("campaign_instance_nonce_sha256")
    ):
        raise ValueError("snapshot campaign nonce property is inconsistent")
    _plan_bindings(plan)
    return plan


def _build_request(snapshot: object, operation: str) -> Tuple[Dict[str, Any], dict]:
    plan = _snapshot_plan(snapshot)
    if operation not in _ALLOWED_OPERATIONS:
        raise ValueError("runtime-attestor operation is not frozen")
    artifact_directory = Path(getattr(snapshot, "artifact_directory"))
    workspace = Path(os.path.abspath(os.fspath(artifact_directory))).parent.parent
    manifest_path = workspace / runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH
    loaded = runtime_identity.load_runtime_identity_manifest(
        manifest_path,
        lockfile_path=workspace / runtime_identity.LOCKFILE_RELATIVE_PATH,
    )
    if loaded.approved is not True:
        raise PermissionError("runtime identity manifest is not operator-approved")
    verified = runtime_identity.verify_runtime_identity_files(loaded)
    manifest = verified.record
    identity_reference = plan["runtime_identity_manifest"]
    if loaded.manifest_sha256 != identity_reference["manifest_sha256"]:
        raise ValueError("plan and approved runtime identity manifest differ")
    for name, expected in identity_reference["component_sha256"].items():
        if sha256_json(manifest[name]) != expected:
            raise ValueError("runtime identity component differs from the plan")
    executable_row = next(
        row for row in manifest["python_files"] if row["role"] == "executable"
    )
    interpreter_identity = {
        key: executable_row[key] for key in ("path", "size_bytes", "sha256")
    }
    worker_row = next(
        (
            row
            for row in plan.get("source_paths", ())
            if row.get("path") == ATTESTOR_SOURCE_RELATIVE_PATH
        ),
        None,
    )
    if not isinstance(worker_row, Mapping):
        raise ValueError("production source manifest omits the attestor worker")
    worker_identity = {
        "path": os.fspath(workspace / ATTESTOR_SOURCE_RELATIVE_PATH),
        "size_bytes": worker_row["size_bytes"],
        "sha256": worker_row["sha256"],
    }
    worker = Path(__file__).resolve(strict=True)
    interpreter = Path(executable_row["path"])
    _verify_bound_file(interpreter_identity, interpreter)
    _verify_bound_file(worker_identity, worker)
    if not os.access(os.fspath(interpreter), os.X_OK):
        raise PermissionError("approved Python executable is not executable")
    bindings = _plan_bindings(plan)
    body = {
        "schema": REQUEST_SCHEMA,
        "operation": operation,
        **bindings,
        "attestor_source_sha256": worker_identity["sha256"],
        "supervisor_pid": os.getpid(),
        "supervisor_challenge": hashlib.sha256(secrets.token_bytes(32)).hexdigest(),
    }
    request = dict(body)
    request["request_sha256"] = sha256_json(body)
    validate_runtime_attestor_request(request)
    launch = {
        "python_executable": interpreter_identity,
        "attestor_worker": worker_identity,
        "workspace": os.fspath(workspace),
    }
    return request, launch


def _abort_process(process: object) -> None:
    try:
        os.killpg(int(getattr(process, "pid")), signal.SIGKILL)
    except (OSError, TypeError, ValueError):
        try:
            process.kill()
        except (AttributeError, OSError):
            pass
    try:
        process.wait(timeout=2.0)
    except (AttributeError, OSError, subprocess.TimeoutExpired):
        pass


def _collect_bounded_output(process: object) -> Tuple[bytes, int]:
    stdout = getattr(process, "stdout", None)
    stderr = getattr(process, "stderr", None)
    if stdout is None or stderr is None:
        _abort_process(process)
        raise RuntimeAttestorError("SPAWN_INVALID", "child pipes are absent")
    selector = selectors.DefaultSelector()
    output = bytearray()
    deadline = time.monotonic() + ATTESTOR_TIMEOUT_SECONDS
    try:
        for stream, label in ((stdout, "stdout"), (stderr, "stderr")):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _abort_process(process)
                raise RuntimeAttestorError("TIMEOUT", "runtime attestor timed out")
            for key, _mask in selector.select(min(remaining, 0.1)):
                try:
                    block = os.read(key.fileobj.fileno(), 65536)
                except BlockingIOError:
                    continue
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                if key.data == "stderr":
                    _abort_process(process)
                    raise RuntimeAttestorError(
                        "STDERR_NONEMPTY", "runtime attestor wrote to stderr"
                    )
                output.extend(block)
                if len(output) > MAXIMUM_RESULT_BYTES:
                    _abort_process(process)
                    raise RuntimeAttestorError(
                        "OUTPUT_LIMIT", "runtime attestor stdout exceeded its bound"
                    )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _abort_process(process)
            raise RuntimeAttestorError("TIMEOUT", "runtime attestor timed out")
        returncode = process.wait(timeout=remaining)
    except subprocess.TimeoutExpired as error:
        _abort_process(process)
        raise RuntimeAttestorError("TIMEOUT", "runtime attestor timed out") from error
    finally:
        selector.close()
        for stream in (stdout, stderr):
            try:
                stream.close()
            except OSError:
                pass
    return bytes(output), int(returncode)


def _require_zero_returncode(returncode: int) -> None:
    if type(returncode) is not int:
        raise RuntimeAttestorError("CHILD_EXIT_INVALID", "child exit is not an integer")
    if returncode != 0:
        code = "CHILD_SIGNAL" if returncode < 0 else "CHILD_NONZERO"
        raise RuntimeAttestorError(code, "runtime attestor exited unsuccessfully")


def _launch_runtime_attestor(
    snapshot: object,
    operation: str,
    *,
    _process_factory: Optional[object] = None,
) -> Dict[str, Any]:
    """Launch the sole source-bound worker; the factory is a private test seam."""

    _reject_parent_environment_leakage()
    request, manifest = _build_request(snapshot, operation)
    request_bytes = canonical_json_bytes(request)
    if len(request_bytes) > MAXIMUM_REQUEST_BYTES:
        raise RuntimeAttestorError("REQUEST_LIMIT", "attestor request is too large")
    interpreter = manifest["python_executable"]["path"]
    worker = manifest["attestor_worker"]["path"]
    command = [
        interpreter,
        "-P",
        "-B",
        "-S",
        "-X",
        "utf8",
        worker,
        request_bytes.decode("ascii"),
    ]
    if any(type(part) is not str for part in command):
        raise AssertionError("attestor command contains a non-string argument")
    factory = subprocess.Popen if _process_factory is None else _process_factory
    if not callable(factory):
        raise TypeError("private process factory seam must be callable")
    try:
        process = factory(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=dict(SANITIZED_CHILD_ENVIRONMENT),
            cwd=manifest["workspace"],
            shell=False,
            close_fds=True,
            start_new_session=True,
        )
    except OSError as error:
        raise RuntimeAttestorError("SPAWN_FAILED", "runtime attestor did not spawn") from error
    stdout, returncode = _collect_bounded_output(process)
    _require_zero_returncode(returncode)
    try:
        envelope = decode_canonical_json(
            stdout,
            maximum_bytes=MAXIMUM_RESULT_BYTES,
            description="runtime-attestor envelope",
        )
        checked = validate_runtime_attestor_envelope(
            envelope,
            plan=_snapshot_plan(snapshot),
            expected_child_pid=int(process.pid),
            expected_parent_pid=os.getpid(),
        )
    except (TypeError, ValueError, PermissionError) as error:
        raise RuntimeAttestorError(
            "PROTOCOL_INVALID", "runtime-attestor envelope was rejected"
        ) from error
    request_from_child = runtime_attestor_request_from_observation(
        checked["pre_observation"]
    )
    if request_from_child != request:
        raise RuntimeAttestorError(
            "REQUEST_MISMATCH", "child envelope does not bind the launched request"
        )
    return checked


_HASH_PROBE_VALUES = (
    "heterodiff-a1",
    "dual-manifold",
    "runtime-attestor",
    "frozen-prerequisite-v2",
)


def _hash_probe_record() -> Dict[str, Any]:
    values = [hash(value) for value in _HASH_PROBE_VALUES]
    body = {
        "schema": HASH_PROBE_SCHEMA,
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "environment_value": os.environ.get("PYTHONHASHSEED"),
        "hash_randomization_flag": sys.flags.hash_randomization,
        "probe_sha256": sha256_json(values),
    }
    record = dict(body)
    record["record_sha256"] = sha256_json(body)
    return record


def _identity_component_digests(
    manifest: Mapping[str, Any],
) -> Dict[str, str]:
    names = (
        "profile",
        "python_files",
        "modules",
        "distributions",
        "editable_install",
        "native_libraries",
        "native_pools",
        "accelerators",
    )
    return {name: sha256_json(manifest[name]) for name in names}


def _worker_runtime_contract(
    request: Mapping[str, Any], manifest: Mapping[str, Any]
) -> Dict[str, Any]:
    return frozen_runtime_contract_v2(
        source_manifest_sha256=request["source_manifest_sha256"],
        environment_lock_sha256=manifest["lockfile"]["sha256"],
        runtime_identity_manifest_sha256=request[
            "runtime_identity_manifest_sha256"
        ],
        minimum_macos_version=manifest["profile"]["minimum_macos_version"],
    )


def _capture_worker_stable_runtime(
    request: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    np: object,
    scipy: object,
    threadpoolctl: object,
    torch: object,
) -> Dict[str, Any]:
    """Capture only stable fields; session PID/challenge live outside this map."""

    import importlib.metadata
    import sysconfig

    observed_environment = dict(os.environ)
    if observed_environment != SANITIZED_CHILD_ENVIRONMENT:
        raise RuntimeError("live child environment differs from the exact allowlist")
    modules_by_name = {
        "numpy": np,
        "scipy": scipy,
        "threadpoolctl": threadpoolctl,
        "torch": torch,
    }
    module_rows = [_plain_json_value(row) for row in manifest["modules"]]
    for row in module_rows:
        module = modules_by_name[row["module"]]
        origin = os.path.abspath(os.fspath(module.__file__))
        if origin != row["path"]:
            raise RuntimeError("live module origin differs from approved identity")
    distribution_evidence = []
    for row in manifest["distributions"]:
        distribution = importlib.metadata.distribution(row["name"])
        origin_value = getattr(distribution, "_path", None)
        if origin_value is None:
            raise RuntimeError("distribution metadata origin is unavailable")
        origin = os.path.abspath(os.fspath(origin_value))
        if distribution.version != row["version"]:
            raise RuntimeError("live distribution version differs from approved identity")
        metadata_files = [_plain_json_value(item) for item in row["metadata_files"]]
        if any(os.path.dirname(item["path"]) != origin for item in metadata_files):
            raise RuntimeError("distribution metadata origin differs from approved identity")
        distribution_evidence.append(
            {
                "name": row["name"],
                "version": row["version"],
                "origin": origin,
                "metadata_files": metadata_files,
            }
        )

    pool_rows = []
    for raw in threadpoolctl.threadpool_info():
        version = raw.get("version")
        row = {
            "library_path": raw.get("filepath"),
            "user_api": raw.get("user_api"),
            "internal_api": raw.get("internal_api"),
            "prefix": raw.get("prefix"),
            "version": version,
            "num_threads": raw.get("num_threads"),
        }
        pool_rows.append(row)
    pool_rows.sort(key=lambda row: str(row["library_path"]))
    expected_pools = [_plain_json_value(row) for row in manifest["native_pools"]]
    if pool_rows != expected_pools:
        raise RuntimeError("live native pools differ from the approved identity")

    numpy_configuration = np.__config__.show(mode="dicts")
    if type(numpy_configuration) is not dict or not numpy_configuration:
        raise RuntimeError("NumPy build configuration is unavailable")

    cuda_available = bool(torch.cuda.is_available())
    cuda_initialized = bool(torch.cuda.is_initialized())
    cuda_device_count = int(torch.cuda.device_count()) if cuda_available else 0
    xpu = getattr(torch, "xpu", None)
    xpu_available = bool(xpu is not None and xpu.is_available())
    xpu_initialized = bool(
        xpu is not None
        and hasattr(xpu, "is_initialized")
        and xpu.is_initialized()
    )
    xpu_device_count = int(xpu.device_count()) if xpu_available else 0
    mps_backend = torch.backends.mps
    mps_built = bool(mps_backend.is_built())
    mps_available = bool(mps_backend.is_available())
    torch_state = {
        "execution_device": "cpu",
        "execution_device_enforced_cpu": True,
        "deterministic_algorithms": bool(
            torch.are_deterministic_algorithms_enabled()
        ),
        "torch_threads": int(torch.get_num_threads()),
        "torch_interop_threads": int(torch.get_num_interop_threads()),
        "cuda_available": cuda_available,
        "cuda_initialized": cuda_initialized,
        "cuda_device_count": cuda_device_count,
        "xpu_available": xpu_available,
        "xpu_initialized": xpu_initialized,
        "xpu_device_count": xpu_device_count,
        # This is an operation claim, not an unverifiable backend-initialized
        # claim: the fixed worker has no code path that constructs an MPS tensor.
        "mps_built": mps_built,
        "mps_available": mps_available,
        "mps_operation_performed": False,
    }
    accelerators = manifest["accelerators"]
    expected_torch_capabilities = {
        "execution_device_enforced_cpu": accelerators[
            "execution_device_enforced_cpu"
        ],
        "cuda_available": accelerators["cuda"]["available"],
        "cuda_initialized": accelerators["cuda"]["initialized"],
        "cuda_device_count": accelerators["cuda"]["device_count"],
        "xpu_available": accelerators["xpu"]["available"],
        "xpu_initialized": accelerators["xpu"]["initialized"],
        "xpu_device_count": accelerators["xpu"]["device_count"],
        "mps_built": accelerators["mps"]["built"],
        "mps_available": accelerators["mps"]["available"],
    }
    if any(
        torch_state[name] != expected
        for name, expected in expected_torch_capabilities.items()
    ):
        raise RuntimeError("live accelerator state differs from approved identity")

    versions = {
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "threadpoolctl": threadpoolctl.__version__,
        "torch": torch.__version__,
    }
    stable = {
        "schema": STABLE_RUNTIME_SCHEMA,
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "pointer_bits": 8 * __import__("struct").calcsize("P"),
            "byteorder": sys.byteorder,
            "safe_path": bool(sys.flags.safe_path),
            "soabi": sysconfig.get_config_var("SOABI"),
            "pycache_prefix": sys.pycache_prefix,
            "no_site": bool(sys.flags.no_site),
        },
        "runtime_profile": _plain_json_value(manifest["profile"]),
        "versions": versions,
        "environment": observed_environment,
        "effective_hash_seed": {
            "environment_value": os.environ.get("PYTHONHASHSEED"),
            "hash_randomization_flag": sys.flags.hash_randomization,
            "builtin_hash_probe_sha256": sha256_json(
                [hash(value) for value in _HASH_PROBE_VALUES]
            ),
        },
        "host": {
            "system": platform.system(),
            "machine": platform.machine(),
            "translated_x86": platform.system() == "Darwin"
            and platform.machine() != "arm64",
            "macos_version": platform.mac_ver()[0],
        },
        "runtime_identity_component_sha256": _identity_component_digests(
            manifest
        ),
        "python_files": [_plain_json_value(row) for row in manifest["python_files"]],
        "module_origins": module_rows,
        "distribution_metadata": distribution_evidence,
        "editable_install_identity": _plain_json_value(
            manifest["editable_install"]
        ),
        "native_libraries": [
            _plain_json_value(row) for row in manifest["native_libraries"]
        ],
        "native_pools": pool_rows,
        "accelerator_identity": _plain_json_value(manifest["accelerators"]),
        "numpy_configuration": numpy_configuration,
        "torch_device_state": torch_state,
        "source_manifest_sha256": request["source_manifest_sha256"],
        "runtime_contract_sha256": request["runtime_contract_sha256"],
        "runtime_identity_manifest_sha256": request[
            "runtime_identity_manifest_sha256"
        ],
    }
    _validate_stable_runtime(
        stable,
        request=request,
        runtime_contract=_worker_runtime_contract(request, manifest),
    )
    return stable


def _worker_observation(
    request: Mapping[str, Any], phase: str, stable: Mapping[str, Any]
) -> Dict[str, Any]:
    observed_environment = dict(os.environ)
    if observed_environment != stable["environment"]:
        raise RuntimeError("child environment changed after stable capture")
    body = {
        "schema": OBSERVATION_SCHEMA,
        "phase": phase,
        "request_schema": request["schema"],
        "request_sha256": request["request_sha256"],
        "operation": request["operation"],
        "plan_sha256": request["plan_sha256"],
        "campaign_instance_nonce_sha256": request[
            "campaign_instance_nonce_sha256"
        ],
        "source_manifest_sha256": request["source_manifest_sha256"],
        "runtime_contract_sha256": request["runtime_contract_sha256"],
        "runtime_identity_manifest_sha256": request[
            "runtime_identity_manifest_sha256"
        ],
        "supervisor_challenge": request["supervisor_challenge"],
        "child_pid": os.getpid(),
        "parent_pid": os.getppid(),
        "attestor_source_sha256": request["attestor_source_sha256"],
        "environment_sha256": sha256_json(observed_environment),
        "stable_runtime": dict(stable),
        "stable_runtime_sha256": sha256_json(stable),
    }
    record = dict(body)
    record["observation_sha256"] = sha256_json(body)
    return record


def _encode_prerequisite_result(result: object, np: object) -> Dict[str, Any]:
    from dataclasses import fields

    payload = {
        "schema": TYPED_PREREQUISITE_SCHEMA,
        "class_module": type(result).__module__,
        "class_name": type(result).__name__,
        "fields": [],
    }
    for descriptor in fields(result):
        value = getattr(result, descriptor.name)
        if type(value) in (str, bool, int) or value is None:
            encoded = {"kind": "scalar", "value": value}
        elif type(value) is float:
            encoded = {"kind": "float64-hex", "value": value.hex()}
        elif type(value) is tuple:
            if not all(type(item) is str for item in value):
                raise TypeError("prerequisite tuple field is not a string tuple")
            encoded = {"kind": "string-tuple", "value": list(value)}
        elif type(value) is np.ndarray:
            array = np.ascontiguousarray(value)
            encoded = {
                "kind": "ndarray",
                "value": {
                    "dtype": array.dtype.str,
                    "shape": list(array.shape),
                    "content_sha256": hashlib.sha256(
                        array.tobytes(order="C")
                    ).hexdigest(),
                },
            }
        else:
            raise TypeError("unsupported prerequisite result field type")
        payload["fields"].append({"name": descriptor.name, "value": encoded})
    return _validate_typed_prerequisite_payload(payload)


def _verify_live_worker_source_manifest(request: Mapping[str, Any]) -> None:
    workspace = Path(__file__).resolve(strict=True).parents[3]
    _validate_worker_source_layout(
        workspace, workspace / "src" / "heterodiff"
    )
    from heterodiff.experiments import finite_association_production_order

    source_manifest = (
        finite_association_production_order.frozen_production_source_manifest(
            workspace
        )
    )
    if (
        request["source_manifest_sha256"]
        != source_manifest["source_manifest_sha256"]
    ):
        raise RuntimeError("runtime-attestor source binding is stale")
    worker_row = next(
        row
        for row in source_manifest["files"]
        if row["path"] == ATTESTOR_SOURCE_RELATIVE_PATH
    )
    if request["attestor_source_sha256"] != worker_row["sha256"]:
        raise RuntimeError("runtime-attestor worker source binding is stale")
    _validate_worker_source_layout(
        workspace, workspace / "src" / "heterodiff"
    )


def _validate_worker_request_against_custody(
    request: Mapping[str, Any], manifest: runtime_identity.RuntimeIdentityManifest
) -> Mapping[str, Any]:
    if request["supervisor_pid"] != os.getppid():
        raise RuntimeError("runtime-attestor supervisor PID is stale")
    if dict(os.environ) != SANITIZED_CHILD_ENVIRONMENT:
        raise RuntimeError("runtime-attestor child environment is not exact")
    if manifest.approved is not True or manifest.identity_files_verified is not True:
        raise RuntimeError("runtime identity was not approved and reverified")
    if request["runtime_identity_manifest_sha256"] != manifest.manifest_sha256:
        raise RuntimeError("runtime-attestor identity binding is stale")
    if request["runtime_contract_sha256"] != sha256_json(
        _worker_runtime_contract(request, manifest.record)
    ):
        raise RuntimeError("runtime-attestor contract binding is stale")
    _verify_live_worker_source_manifest(request)
    return manifest.record


def _require_verified_project_modules(module_names: Sequence[str]) -> None:
    """Prove project imports resolved to the already verified source tree."""

    workspace = Path(__file__).resolve(strict=True).parents[3]
    package_names = frozenset(("heterodiff", "heterodiff.experiments"))
    for name in module_names:
        if type(name) is not str or (
            name != "heterodiff" and not name.startswith("heterodiff.")
        ):
            raise TypeError("verified project module name is invalid")
        module = sys.modules.get(name)
        if module is None:
            raise RuntimeError("verified project module was not preloaded: " + name)
        parts = name.split(".")
        base = workspace / "src" / Path(*parts)
        expected = base / "__init__.py" if name in package_names else base.with_suffix(".py")
        origin = getattr(module, "__file__", None)
        if type(origin) is not str or os.path.abspath(origin) != os.fspath(expected):
            raise RuntimeError("project module escaped verified source: " + name)
        if name in package_names:
            package_path = getattr(module, "__path__", None)
            if package_path is None or tuple(package_path) != (
                os.fspath(expected.parent),
            ):
                raise RuntimeError("project package path escaped verified source: " + name)


def _reject_project_shadow_in_approved_root(root: Path) -> None:
    import importlib.machinery

    candidates = [
        root / "heterodiff",
        root / "heterodiff.py",
        root / "heterodiff.pyc",
        root / "heterodiff.pyo",
    ]
    candidates.extend(
        root / ("heterodiff" + suffix)
        for suffix in importlib.machinery.EXTENSION_SUFFIXES
    )
    for candidate in candidates:
        try:
            candidate.lstat()
        except FileNotFoundError:
            continue
        raise RuntimeError("approved module root contains a project-name shadow")


def _install_approved_module_roots(manifest: Mapping[str, Any]) -> None:
    """Expose only manifest-derived package roots; never execute ``.pth`` files."""

    if not sys.flags.no_site:
        raise RuntimeError("runtime-attestor worker did not start with -S")
    roots = set()
    for row in manifest["modules"]:
        origin = Path(row["path"])
        root = origin.parent.parent if origin.name == "__init__.py" else origin.parent
        if not root.is_absolute() or not root.is_dir():
            raise RuntimeError("approved module root is not an absolute directory")
        _reject_project_shadow_in_approved_root(root)
        roots.add(os.fspath(root))
    project_root = os.fspath(Path(__file__).resolve(strict=True).parents[3] / "src")
    if sys.path.count(project_root) != 1:
        raise RuntimeError("verified project source root is not uniquely installed")
    project_index = sys.path.index(project_root)
    if (
        _verified_bootstrap_stdlib_sys_path is None
        or tuple(sys.path[:project_index]) != _verified_bootstrap_stdlib_sys_path
    ):
        raise RuntimeError("worker bootstrap standard-library path precedence drifted")
    for root in sorted(roots):
        if root in sys.path:
            raise RuntimeError("approved module root was installed before admission")
        sys.path.insert(project_index, root)
        project_index += 1


def _verify_loaded_module_closure(manifest: Mapping[str, Any]) -> None:
    """Reject every loaded non-stdlib origin not covered by approved bytes."""

    import sysconfig
    from heterodiff.experiments import finite_association_production_order

    declared = set()
    for row in manifest["python_files"]:
        declared.add(row["path"])
    for row in manifest["modules"]:
        declared.add(row["path"])
    distribution_roots = set()
    for distribution in manifest["distributions"]:
        for row in distribution["metadata_files"]:
            declared.add(row["path"])
            distribution_roots.add(os.path.dirname(os.path.dirname(row["path"])))
        for row in distribution["record_payloads"]:
            declared.add(row["path"])
    declared.add(manifest["editable_install"]["direct_url_identity"]["path"])
    for row in manifest["native_libraries"]:
        declared.add(row["path"])

    workspace = Path(__file__).resolve(strict=True).parents[3]
    source_manifest = (
        finite_association_production_order.frozen_production_source_manifest(
            workspace
        )
    )
    source_paths = {
        os.fspath(workspace / row["path"]) for row in source_manifest["files"]
    }
    stdlib_roots = {
        os.path.abspath(value)
        for key, value in sysconfig.get_paths().items()
        if key in ("stdlib", "platstdlib") and value
    }

    def beneath(path: str, roots: set[str]) -> bool:
        for root in roots:
            try:
                if os.path.commonpath((path, root)) == root:
                    return True
            except ValueError:
                continue
        return False

    def exact_torch_generated_module(name: str, module: object) -> bool:
        if name != _TORCH_GENERATED_MODULE_NAME:
            return False
        spec = getattr(module, "__spec__", None)
        loader = getattr(spec, "loader", None)
        source = getattr(loader, "data", None)
        if (
            getattr(module, "__name__", None) != name
            or getattr(module, "__package__", None) != ""
            or getattr(module, "__file__", None) is not None
            or spec is None
            or getattr(spec, "name", None) != name
            or getattr(spec, "origin", None) != _TORCH_GENERATED_MODULE_ORIGIN
            or getattr(spec, "submodule_search_locations", None) is not None
            or getattr(module, "__loader__", None) is not loader
            or type(loader).__module__ != _TORCH_GENERATED_LOADER_MODULE
            or type(loader).__qualname__ != _TORCH_GENERATED_LOADER_QUALNAME
            or type(source) is not str
        ):
            return False
        try:
            encoded = source.encode("utf-8")
        except UnicodeEncodeError:
            return False
        if (
            len(encoded) != _TORCH_GENERATED_SOURCE_SIZE_BYTES
            or hashlib.sha256(encoded).hexdigest()
            != _TORCH_GENERATED_SOURCE_SHA256
        ):
            return False
        generator = sys.modules.get(_TORCH_GENERATED_LOADER_MODULE)
        generator_origin = getattr(generator, "__file__", None)
        return (
            type(generator_origin) is str
            and os.path.isabs(generator_origin)
            and os.path.abspath(generator_origin) in declared
        )

    def exact_torch_module_alias(name: str, module: object) -> bool:
        expected = _TORCH_MODULE_ALIASES.get(name)
        if expected is None:
            return False
        owner_name, type_qualname, relative_file = expected
        if (
            type(module).__module__ != owner_name
            or type(module).__qualname__ != type_qualname
            or getattr(module, "__name__", None) != name
            or getattr(module, "__package__", None) is not None
            or getattr(module, "__loader__", None) is not None
            or getattr(module, "__spec__", None) is not None
            or getattr(module, "__file__", None) != relative_file
        ):
            return False
        owner = sys.modules.get(owner_name)
        owner_origin = getattr(owner, "__file__", None)
        return (
            type(owner_origin) is str
            and os.path.isabs(owner_origin)
            and os.path.abspath(owner_origin) in declared
        )

    for name, module in tuple(sorted(sys.modules.items())):
        origin = getattr(module, "__file__", None)
        if origin is None:
            spec = getattr(module, "__spec__", None)
            origin = getattr(spec, "origin", None)
        if origin in (None, "built-in", "frozen"):
            continue
        if type(origin) is not str or not os.path.isabs(origin):
            if exact_torch_generated_module(
                name, module
            ) or exact_torch_module_alias(name, module):
                continue
            raise RuntimeError("loaded module %s has a nonabsolute origin" % name)
        path = os.path.abspath(origin)
        if path.endswith((".pyc", ".pyo")):
            raise RuntimeError("loaded module %s used forbidden bytecode" % name)
        if beneath(path, stdlib_roots):
            continue
        if path in source_paths or path in declared:
            continue
        if beneath(path, distribution_roots):
            raise RuntimeError("loaded module %s has an unapproved origin" % name)
        raise RuntimeError("loaded non-stdlib module %s is outside custody" % name)


def _execute_worker_request(request: Mapping[str, Any]) -> Dict[str, Any]:
    loaded = runtime_identity.require_approved_checked_in_runtime_identity_manifest()
    manifest = _validate_worker_request_against_custody(request, loaded)
    _require_verified_project_modules(
        (
            "heterodiff",
            "heterodiff.experiments",
            "heterodiff.experiments.finite_association_production_order",
            "heterodiff.experiments.finite_association_runtime_attestor",
            "heterodiff.experiments.finite_association_runtime_identity",
        )
    )
    _install_approved_module_roots(manifest)

    workspace = Path(__file__).resolve(strict=True).parents[3]
    _validate_worker_source_layout(
        workspace, workspace / "src" / "heterodiff"
    )
    import numpy as np
    import scipy
    import threadpoolctl
    import torch

    _validate_worker_source_layout(
        workspace, workspace / "src" / "heterodiff"
    )
    from heterodiff.experiments.finite_association_guided_residual_pilot import (
        AssociationResidualPrerequisiteResult,
        FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS,
        frozen_association_fixture_sha256,
        run_association_residual_prerequisite_gate,
    )
    from heterodiff.experiments.finite_association_residual_training_torch import (
        configure_frozen_association_training_environment,
    )
    _validate_worker_source_layout(
        workspace, workspace / "src" / "heterodiff"
    )
    _require_verified_project_modules(
        (
            "heterodiff.experiments.finite_association_guided_residual_pilot",
            "heterodiff.experiments.finite_association_residual_training_torch",
        )
    )
    _verify_loaded_module_closure(manifest)

    configure_frozen_association_training_environment()
    pre_verified = runtime_identity.verify_runtime_identity_files(loaded)
    if pre_verified.record != manifest:
        raise RuntimeError("runtime identity changed before PRE capture")
    _verify_live_worker_source_manifest(request)
    _verify_loaded_module_closure(manifest)
    pre_stable = _capture_worker_stable_runtime(
        request,
        manifest,
        np=np,
        scipy=scipy,
        threadpoolctl=threadpoolctl,
        torch=torch,
    )
    pre = _worker_observation(request, "PRE", pre_stable)
    result = run_association_residual_prerequisite_gate()
    if type(result) is not AssociationResidualPrerequisiteResult:
        raise TypeError("prerequisite returned the wrong exact result type")
    result.__post_init__()
    digests = tuple(
        getattr(result, name) for name in _PREREQUISITE_RESULT_FIELD_NAMES[:5]
    )
    if (
        digests != FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS
        or digests != _FROZEN_PREREQUISITE_DIGESTS
        or result.passed is not True
        or result.failures != ()
    ):
        raise RuntimeError("frozen prerequisite did not pass canonical admission")
    post_verified = runtime_identity.verify_runtime_identity_files(loaded)
    if post_verified.record != manifest:
        raise RuntimeError("runtime identity changed before POST capture")
    _verify_live_worker_source_manifest(request)
    _verify_loaded_module_closure(manifest)
    post_stable = _capture_worker_stable_runtime(
        request,
        manifest,
        np=np,
        scipy=scipy,
        threadpoolctl=threadpoolctl,
        torch=torch,
    )
    if pre_stable != post_stable:
        raise RuntimeError("stable runtime identity drifted during prerequisite")
    post = _worker_observation(request, "POST", post_stable)
    payload = _encode_prerequisite_result(result, np)
    fixture_sha256 = frozen_association_fixture_sha256(digests)
    if fixture_sha256 != _frozen_fixture_sha256():
        raise RuntimeError("frozen prerequisite fixture identity changed")
    body = {
        "schema": ENVELOPE_SCHEMA,
        "request_sha256": request["request_sha256"],
        "supervisor_challenge": request["supervisor_challenge"],
        "child_pid": os.getpid(),
        "parent_pid": os.getppid(),
        "pre_observation": pre,
        "post_observation": post,
        "stable_runtime_equal": True,
        "typed_prerequisite_result": payload,
        "typed_prerequisite_result_sha256": sha256_json(payload),
        "fixture_sha256": fixture_sha256,
    }
    envelope = dict(body)
    envelope["envelope_sha256"] = sha256_json(body)
    return envelope


def _worker_main(argument: str) -> int:
    """Execute only the fixed prerequisite after complete startup admission."""
    try:
        _validated_darwin_worker_environment(dict(os.environ), uid=os.getuid())
        del os.environ[_DARWIN_INJECTED_ENVIRONMENT_NAME]
        request = decode_canonical_json(
            argument.encode("ascii"),
            maximum_bytes=MAXIMUM_REQUEST_BYTES,
            description="runtime-attestor request",
        )
        validate_runtime_attestor_request(request)
        _bootstrap_worker_project(request)
        envelope = _execute_worker_request(request)
        encoded = canonical_json_bytes(envelope)
        if len(encoded) > MAXIMUM_RESULT_BYTES:
            return 70
        _write_all(1, encoded)
    except (UnicodeEncodeError, TypeError, ValueError, PermissionError, RuntimeError):
        return 64
    return 0


def _main(argv: Sequence[str]) -> int:
    if tuple(argv) == ("--stdlib-hash-seed-probe",):
        _write_all(1, canonical_json_bytes(_hash_probe_record()))
        return 0
    if len(argv) == 1:
        return _worker_main(argv[0])
    return 64


__all__ = [
    "ATTESTED_PREREQUISITE_OPERATION",
    "ENVELOPE_SCHEMA",
    "OBSERVATION_SCHEMA",
    "REVALIDATE_PREREQUISITE_OPERATION",
    "REQUEST_SCHEMA",
    "RUNTIME_CONTRACT_SCHEMA",
    "RUNTIME_IDENTITY_MANIFEST_SCHEMA",
    "RUNTIME_IDENTITY_RELATIVE_PATH",
    "RuntimeAttestorError",
    "SANITIZED_CHILD_ENVIRONMENT",
    "TYPED_PREREQUISITE_SCHEMA",
    "canonical_json_bytes",
    "decode_canonical_json",
    "frozen_runtime_contract_v2",
    "frozen_runtime_contract_v2_sha256",
    "runtime_attestor_request_from_observation",
    "sha256_json",
    "validate_runtime_attestor_envelope",
    "validate_runtime_attestor_observation",
    "validate_runtime_attestor_request",
    "validate_runtime_identity_manifest",
]


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
