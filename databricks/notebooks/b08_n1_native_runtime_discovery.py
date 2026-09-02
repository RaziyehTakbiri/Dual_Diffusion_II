# Databricks notebook source
# MAGIC %md
# MAGIC # B08 N1 — native Databricks runtime discovery
# MAGIC
# MAGIC Run this notebook on the intended **DBR 17.3 LTS, x86_64, CPU-only**
# MAGIC cluster after pulling the repository. It performs a bounded, read-only
# MAGIC inspection of Python, installed distribution metadata, and the 15 required
# MAGIC environment variables.
# MAGIC
# MAGIC It does **not** install or resolve packages, access the network, call Spark
# MAGIC or Databricks APIs, write files, access study/test data, or execute
# MAGIC calibration, training, or inference. Return the single JSON result for the
# MAGIC next F152 lock-construction decision.

# COMMAND ----------

from importlib import metadata
from pathlib import Path
import hashlib
import json
import os
import platform
import re
import stat
import struct
import sys
import sysconfig


# Usually no edit is needed when this notebook remains inside the checked-out
# repository. If auto-detection fails, replace None with the absolute /Workspace/...
# path to the repository root and run the notebook again.
REPO_ROOT_OVERRIDE = None

PROFILE_RELATIVE_PATH = (
    Path("requirements")
    / "b08-databricks-aws-dbr17.3-x86_64-cpu-py312.native-runtime-profile.template.json"
)
F152_LOCK_RELATIVE_PATH = Path(
    "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock"
)

# These constants bind this notebook to the independently reviewed Stage-N0
# profile. A profile change must stop this notebook until it is reviewed and the
# notebook is deliberately updated in the same source revision.
EXPECTED_PROFILE_FILE_SHA256 = (
    "2e05801bf65ede62b2c318ba82a6d4f35aa9191b64a4ac24608fda05df071a91"
)
EXPECTED_PROFILE_RECORD_SHA256 = (
    "e2bd94423e9049a612ec865087e25c71c8711dccc0cda500979b387875cc79e5"
)
EXPECTED_SCHEMA_VERSION = "heterodiff-b08-databricks-native-runtime-profile-v1"
EXPECTED_PROFILE_ID = "b08-databricks-aws-native-dbr17.3-linux-x86_64-cpu-py312"
EXPECTED_LIFECYCLE_STATE = "DRAFT_UNRESOLVED_F152_LOCK"
RECORD_DOMAIN = b"heterodiff/b08/databricks-native-runtime-profile/v1\0"
EXPECTED_TOP_LEVEL_KEYS = {
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


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256_text(value):
    if value is None:
        return None
    return sha256_bytes(value.encode("utf-8"))


def canonical_json_bytes(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def locate_repo_root():
    if REPO_ROOT_OVERRIDE is not None:
        candidates = [Path(REPO_ROOT_OVERRIDE).expanduser().resolve()]
    else:
        start = Path.cwd().resolve()
        candidates = [start, *start.parents]

    for candidate in candidates:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "heterodiff").is_dir()
            and (
                candidate / "PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_SUCCESSOR_V1.md"
            ).is_file()
            and (candidate / PROFILE_RELATIVE_PATH).is_file()
        ):
            return candidate

    raise RuntimeError(
        "Repository root was not found from the notebook's current working "
        f"directory ({Path.cwd()}). Set REPO_ROOT_OVERRIDE to the absolute "
        "/Workspace/... repository path."
    )


def validate_profile_bytes(profile_bytes):
    errors = []
    file_sha256 = sha256_bytes(profile_bytes)
    try:
        profile = json.loads(profile_bytes.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return None, {
            "valid": False,
            "errors": [f"PROFILE_IS_NOT_ASCII_JSON: {error}"],
            "file_sha256": file_sha256,
            "semantic_sha256": None,
        }

    try:
        canonical = canonical_json_bytes(profile)
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        return None, {
            "valid": False,
            "errors": [f"PROFILE_IS_NOT_CANONICAL_JSON_NATIVE: {error}"],
            "file_sha256": file_sha256,
            "semantic_sha256": None,
        }

    if profile_bytes != canonical + b"\n":
        errors.append("PROFILE_BYTES_ARE_NOT_EXACT_CANONICAL_JSON_PLUS_NEWLINE")
    if file_sha256 != EXPECTED_PROFILE_FILE_SHA256:
        errors.append("PROFILE_FILE_SHA256_DIFFERS_FROM_REVIEWED_N0_PROFILE")
    if type(profile) is not dict:
        errors.append("PROFILE_IS_NOT_AN_OBJECT")
        return None, {
            "valid": False,
            "errors": errors,
            "file_sha256": file_sha256,
            "semantic_sha256": None,
        }
    if set(profile) != EXPECTED_TOP_LEVEL_KEYS:
        errors.append("PROFILE_TOP_LEVEL_KEYS_DIFFER")

    semantic_sha256 = None
    if "record_sha256" in profile:
        projection = dict(profile)
        projection.pop("record_sha256")
        semantic_sha256 = sha256_bytes(RECORD_DOMAIN + canonical_json_bytes(projection))

    if profile.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        errors.append("PROFILE_SCHEMA_VERSION_DIFFERS")
    if profile.get("profile_id") != EXPECTED_PROFILE_ID:
        errors.append("PROFILE_ID_DIFFERS")
    if profile.get("lifecycle_state") != EXPECTED_LIFECYCLE_STATE:
        errors.append("PROFILE_IS_NOT_THE_UNRESOLVED_N0_DRAFT")
    if profile.get("record_sha256") != EXPECTED_PROFILE_RECORD_SHA256:
        errors.append("PROFILE_DECLARED_RECORD_SHA256_DIFFERS")
    if semantic_sha256 != profile.get("record_sha256"):
        errors.append("PROFILE_SEMANTIC_SHA256_IS_INVALID")

    route = profile.get("native_route")
    required_route_values = {
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
    }
    if type(route) is not dict or any(
        route.get(key) != value for key, value in required_route_values.items()
    ):
        errors.append("PROFILE_NATIVE_ROUTE_SAFETY_VALUES_DIFFER")

    safety_boundary = profile.get("safety_boundary")
    if (
        type(safety_boundary) is not dict
        or not safety_boundary
        or any(value is not False for value in safety_boundary.values())
    ):
        errors.append("PROFILE_SAFETY_BOUNDARY_IS_NOT_ALL_FALSE")

    f152 = profile.get("f152_lock")
    if (
        type(f152) is not dict
        or f152.get("path") != F152_LOCK_RELATIVE_PATH.as_posix()
        or f152.get("sha256") is not None
        or f152.get("present_and_regular") is not False
        or f152.get("complete_transitive_lock") is not False
        or f152.get("artifact_closure_verified") is not False
    ):
        errors.append("PROFILE_F152_DRAFT_BINDING_DIFFERS_OR_OVERCLAIMS")

    f153 = profile.get("f153_environment")
    if type(f153) is not dict or len(f153) != 15:
        errors.append("PROFILE_F153_ENVIRONMENT_IS_NOT_AN_EXACT_15_KEY_OBJECT")

    return profile, {
        "valid": not errors,
        "errors": errors,
        "file_sha256": file_sha256,
        "semantic_sha256": semantic_sha256,
    }


def path_object_observation(path):
    if not os.path.lexists(path):
        return {"object_exists": False, "object_type": None}

    mode = path.lstat().st_mode
    if stat.S_ISREG(mode):
        object_type = "REGULAR_FILE"
    elif stat.S_ISDIR(mode):
        object_type = "DIRECTORY"
    elif stat.S_ISLNK(mode):
        object_type = "SYMLINK"
    else:
        object_type = "OTHER"
    return {"object_exists": True, "object_type": object_type}


def normalized_distribution_name(value):
    return re.sub(r"[-_.]+", "-", value).lower()


def installed_distribution_index():
    index = {}
    for dist in metadata.distributions():
        name = dist.metadata.get("Name")
        if not name:
            continue
        index.setdefault(normalized_distribution_name(name), []).append(dist)
    return index


def distribution_candidate_record(dist, expected_version):
    files = tuple(dist.files or ())
    metadata_entry = next(
        (
            entry
            for entry in files
            if entry.name == "METADATA"
            and any(
                part.endswith(".dist-info") or part.endswith(".egg-info")
                for part in entry.parts
            )
        ),
        None,
    )
    metadata_path = (
        Path(dist.locate_file(metadata_entry)).resolve()
        if metadata_entry is not None
        else None
    )
    metadata_text = dist.read_text("METADATA")
    record_text = dist.read_text("RECORD")
    direct_url_text = dist.read_text("direct_url.json")
    installer_text = dist.read_text("INSTALLER")

    return {
        "name": dist.metadata.get("Name"),
        "version": dist.version,
        "matches_expected_version": (
            expected_version is None or dist.version == expected_version
        ),
        "distribution_root": str(Path(dist.locate_file("")).resolve()),
        "metadata_directory": (
            str(metadata_path.parent) if metadata_path is not None else None
        ),
        "metadata_sha256": sha256_text(metadata_text),
        "record_present": record_text is not None,
        "record_sha256": sha256_text(record_text),
        # The potentially identifying direct_url.json content is never printed.
        "direct_url_present": direct_url_text is not None,
        "direct_url_sha256": sha256_text(direct_url_text),
        "installer": installer_text.strip() if installer_text else None,
        "declared_file_count": len(files),
    }


def distribution_observation(index, name, expected_version=None):
    candidates = index.get(normalized_distribution_name(name), [])
    records = [
        distribution_candidate_record(candidate, expected_version)
        for candidate in candidates
    ]
    return {
        "expected_version": expected_version,
        "candidate_count": len(records),
        "exactly_one_candidate": len(records) == 1,
        "matches_expected_version": (
            len(records) == 1 and records[0]["matches_expected_version"]
        ),
        "candidates": records,
    }


def read_os_release():
    path = Path("/etc/os-release")
    if not path.is_file():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"').strip("'")
    return values


def observe_runtime(target):
    dbr_version = os.environ.get("DATABRICKS_RUNTIME_VERSION")
    libc_name, libc_version = platform.libc_ver()
    os_release = read_os_release()
    python_abi = f"cp{sys.version_info.major}{sys.version_info.minor}"
    pointer_bits = struct.calcsize("P") * 8
    os_pretty_name = os_release.get("PRETTY_NAME")
    soabi = sysconfig.get_config_var("SOABI")
    multiarch = sysconfig.get_config_var("MULTIARCH")
    extension_suffix = sysconfig.get_config_var("EXT_SUFFIX")
    cache_tag = sys.implementation.cache_tag
    dbr_pattern = re.compile(
        re.escape(target["databricks_runtime_version_prefix"]) + r"(?:\..*)?\Z"
    )

    checks = {
        "databricks_runtime_version_prefix": {
            "expected": target["databricks_runtime_version_prefix"],
            "observed": dbr_version,
            "exact": (
                type(dbr_version) is str
                and dbr_pattern.fullmatch(dbr_version) is not None
            ),
        },
        "python_version": {
            "expected": target["python_version"],
            "observed": platform.python_version(),
            "exact": platform.python_version() == target["python_version"],
        },
        "python_implementation": {
            "expected": target["python_implementation"],
            "observed": platform.python_implementation(),
            "exact": (
                platform.python_implementation() == target["python_implementation"]
            ),
        },
        "python_abi": {
            "expected": target["python_abi"],
            "observed": python_abi,
            "exact": python_abi == target["python_abi"],
        },
        "operating_system_family": {
            "expected": target["operating_system_family"],
            "observed": platform.system(),
            "exact": platform.system() == target["operating_system_family"],
        },
        "operating_system_distribution": {
            "expected": target["operating_system_distribution"],
            "observed": os_release.get("NAME"),
            "exact": os_release.get("NAME") == target["operating_system_distribution"],
        },
        "operating_system_release": {
            "expected": target["operating_system_release"],
            "observed": os_pretty_name,
            "exact": (
                os_pretty_name is not None
                and target["operating_system_release"] in os_pretty_name
            ),
        },
        "architecture": {
            "expected": target["architecture"],
            "observed": platform.machine(),
            "exact": (
                platform.machine().casefold() == target["architecture"].casefold()
            ),
        },
        "pointer_bits": {
            "expected": target["pointer_bits"],
            "observed": pointer_bits,
            "exact": pointer_bits == target["pointer_bits"],
        },
        "byteorder": {
            "expected": target["byteorder"],
            "observed": sys.byteorder,
            "exact": sys.byteorder == target["byteorder"],
        },
        "soabi": {
            "expected": "prefix cpython-312-",
            "observed": soabi,
            "exact": type(soabi) is str and soabi.startswith("cpython-312-"),
        },
        "multiarch": {
            "expected": "x86_64-linux-gnu",
            "observed": multiarch,
            "exact": multiarch == "x86_64-linux-gnu",
        },
        "extension_suffix": {
            "expected": "contains cpython-312",
            "observed": extension_suffix,
            "exact": (
                type(extension_suffix) is str and "cpython-312" in extension_suffix
            ),
        },
        "cache_tag": {
            "expected": "cpython-312",
            "observed": cache_tag,
            "exact": cache_tag == "cpython-312",
        },
    }
    mismatches = {
        name: {"expected": item["expected"], "observed": item["observed"]}
        for name, item in checks.items()
        if not item["exact"]
    }
    observation = {
        "checks": checks,
        "preconditions_exact": not mismatches,
        "mismatches": mismatches,
        "python_executable": sys.executable,
        "cpu_count": os.cpu_count(),
        "libc": {"name": libc_name or None, "version": libc_version or None},
        "sysconfig_platform": sysconfig.get_platform(),
    }
    return observation


def base_result(profile_validation, lock_observation):
    return {
        "schema_version": "heterodiff-b08-n1-native-runtime-discovery-v1",
        "scope": "DATA_FREE_READ_ONLY_NATIVE_RUNTIME_DISCOVERY_ONLY",
        "repo_root_detected": True,
        "profile_relative_path": PROFILE_RELATIVE_PATH.as_posix(),
        "profile_validation": profile_validation,
        "f152_lock": {
            "relative_path": F152_LOCK_RELATIVE_PATH.as_posix(),
            **lock_observation,
        },
        "safety": {
            "network_or_contact_accessed": False,
            "package_install_or_resolution_executed": False,
            "files_written": False,
            "spark_accessed": False,
            "databricks_api_accessed": False,
            "study_or_test_data_accessed": False,
            "calibration_training_or_inference_executed": False,
        },
        "not_proven_by_this_discovery": [
            "F152_COMPLETE_TRANSITIVE_HASH_LOCK",
            "F152_ARTIFACT_PAYLOAD_CLOSURE",
            "F153_EFFECTIVE_WHOLE_RUNTIME_SATISFACTION",
            "MODULE_IMPORT_ORIGIN_OWNERSHIP",
            "PRODUCTION_RUNTIME_CAPTURE",
            "UNOBSERVED_DATABRICKS_TARGET_FIELDS",
            "CAPACITY_OR_PHYSICAL_STORAGE_RESERVATION",
            "SCIENTIFIC_EXECUTION_READINESS",
            "B08_OR_WAVE2_CLOSURE",
        ],
    }


def run_discovery():
    repo_root = locate_repo_root()
    profile_path = repo_root / PROFILE_RELATIVE_PATH
    profile_bytes = profile_path.read_bytes()
    profile, profile_validation = validate_profile_bytes(profile_bytes)

    lock_path = repo_root / F152_LOCK_RELATIVE_PATH
    lock_observation = path_object_observation(lock_path)
    result = base_result(profile_validation, lock_observation)

    # A pre-existing object at the canonical lock path always stops the notebook,
    # including a directory, regular file, valid symlink, or dangling symlink.
    if lock_observation["object_exists"]:
        result["decision"] = "STOP_EXISTING_F152_LOCK_OBJECT_REQUIRES_REVIEW"
        return result

    if not profile_validation["valid"]:
        result["decision"] = "STOP_PROFILE_VALIDATION_FAILED"
        return result

    expected_versions = profile["f152_lock"]["expected_distributions"]
    expected_environment = profile["f153_environment"]
    observed_environment = {name: os.environ.get(name) for name in expected_environment}
    environment_mismatches = {
        name: {
            "expected": expected_environment[name],
            "observed": observed_environment[name],
        }
        for name in expected_environment
        if observed_environment[name] != expected_environment[name]
    }
    result["environment"] = {
        "expected": expected_environment,
        "observed": observed_environment,
        "exact": not environment_mismatches,
        "mismatches": environment_mismatches,
    }

    runtime = observe_runtime(profile["target"])
    result["runtime"] = runtime

    distribution_index = installed_distribution_index()
    distributions = {
        name: distribution_observation(distribution_index, name, version)
        for name, version in expected_versions.items()
    }
    tooling = {
        name: distribution_observation(distribution_index, name)
        for name in ("pip", "setuptools", "wheel", "build", "pip-tools")
    }
    result["distributions"] = distributions
    result["tooling"] = tooling

    external_names = ("numpy", "scipy", "threadpoolctl", "torch")
    ambiguous_external = [
        name for name in external_names if distributions[name]["candidate_count"] > 1
    ]
    missing_external = [
        name for name in external_names if distributions[name]["candidate_count"] == 0
    ]
    mismatched_external = [
        {
            "name": name,
            "expected": distributions[name]["expected_version"],
            "observed": [
                candidate["version"] for candidate in distributions[name]["candidates"]
            ],
        }
        for name in external_names
        if distributions[name]["candidate_count"] == 1
        and not distributions[name]["matches_expected_version"]
    ]
    preexisting_project_distribution = (
        distributions["heterodiff"]["candidate_count"] > 0
    )
    result["distribution_summary"] = {
        "ambiguous_external": ambiguous_external,
        "missing_external": missing_external,
        "version_mismatches": mismatched_external,
        "preexisting_heterodiff_distribution": preexisting_project_distribution,
    }

    if not runtime["preconditions_exact"]:
        decision = "STOP_RUNTIME_PROFILE_MISMATCH_REQUIRES_REVIEW"
    elif environment_mismatches:
        decision = "STOP_F153_ENVIRONMENT_MISMATCH_REQUIRES_REVIEW"
    elif ambiguous_external:
        decision = "STOP_AMBIGUOUS_EXTERNAL_DISTRIBUTIONS_REQUIRES_REVIEW"
    elif preexisting_project_distribution:
        decision = "STOP_PREEXISTING_HETERODIFF_DISTRIBUTION_REQUIRES_REVIEW"
    elif missing_external or mismatched_external:
        decision = "BUILD_ISOLATED_NATIVE_OVERLAY_LOCK_CANDIDATE"
    else:
        decision = "EXTERNAL_DISTRIBUTIONS_MATCH_BUILD_PROJECT_WHEEL_CANDIDATE"

    result["decision"] = decision
    return result


print(json.dumps(run_discovery(), indent=2, sort_keys=True))
