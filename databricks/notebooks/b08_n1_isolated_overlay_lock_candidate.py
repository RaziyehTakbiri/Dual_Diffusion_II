# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # B08 N1 — isolated native overlay and F152 lock candidate
# MAGIC
# MAGIC This notebook constructs a review-pending, data-free dependency candidate
# MAGIC without changing the Databricks base Python environment. Its default mode
# MAGIC is read-only preflight. Construction is possible only after the bounded
# MAGIC widget inputs are explicit and the one-shot authorization gates are
# MAGIC deliberately enabled.
# MAGIC
# MAGIC Construction uses a temporary isolated virtual environment, accepts wheels
# MAGIC only, builds the project wheel from a copied source-only tree, installs the
# MAGIC resulting exact hash lock into a separate overlay directory, verifies the
# MAGIC wheel and installed-file closures, and publishes to one previously absent
# MAGIC durable /Volumes/... destination using no-clobber writes. Once the attempt
# MAGIC root is created, its retained device/inode identity—not its mutable path—is
# MAGIC the custody authority. External mutation of that root is outside the
# MAGIC construction protocol, and independent review must rebind the declared
# MAGIC path, retained root, and receipt before accepting the candidate. It never imports
# MAGIC project/scientific packages, calls Spark or Databricks REST APIs, reads
# MAGIC study or test data, or performs calibration, training, or inference. It
# MAGIC uses only bounded Databricks widgets to receive operator parameters
# MAGIC without editing this tracked source file.
# MAGIC
# MAGIC On an authorized run, type only the new /Volumes/... destination; choose
# MAGIC the execution mode, network/build authority, and exact acknowledgement
# MAGIC from dropdowns. The official index and accepted V2-profile bindings are
# MAGIC fixed in the reviewed notebook.
# MAGIC
# MAGIC The output is a candidate requiring independent review. It does not update
# MAGIC the repository lock, close F152/B08/Wave 2, or authorize runtime use.

# COMMAND ----------

# DBTITLE 1,Cell 3
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
import base64
import csv
import email.parser
import hashlib
import importlib.util
import io
import json
import os
import platform
import re
import shutil
import stat
import struct
import subprocess
import sys
import sysconfig
import tempfile
import venv
import zipfile


# COMMAND ----------

CONSTRUCT_MODE = "CONSTRUCT_ONE_REVIEW_PENDING_CANDIDATE"
ACKNOWLEDGEMENT_TEXT = (
    "AUTHORIZE_ONE_DATA_FREE_N1_NETWORK_BUILD_WITH_NO_BASE_INSTALL"
)
DEFERRED_GIT_REVISION_STATE = (
    "VERIFY_AFTER_DURABLE_INTENT_BEFORE_NETWORK_OR_BUILD"
)


# COMMAND ----------

# OPERATOR INPUTS
#
# Values are supplied through Databricks widgets, so this tracked notebook never
# needs to be edited and the Git checkout can remain byte-clean. Outside
# Databricks, tests may use the named environment-variable fallbacks.
_WIDGET_API = globals().get("dbutils")
_WIDGET_INPUT_ACCESSED = _WIDGET_API is not None


def operator_parameter(name, default, label, choices=None):
    environment_name = "HETERODIFF_" + name.upper()
    if _WIDGET_API is None:
        return os.environ.get(environment_name, default)
    if choices is None:
        _WIDGET_API.widgets.text(name, default, label)
    else:
        _WIDGET_API.widgets.dropdown(name, default, list(choices), label)
    return _WIDGET_API.widgets.get(name)


REPO_ROOT_OVERRIDE = (
    os.environ.get("HETERODIFF_REPO_ROOT_OVERRIDE") or None
)
DURABLE_OUTPUT_DIRECTORY = (
    operator_parameter(
        "b08_n1_durable_output_directory",
        "",
        "New durable /Volumes/... candidate directory",
    )
    or None
)

# These reviewed defaults avoid manual URL copying. A future mirror change
# requires a new source revision and review; credentials are never accepted.
PRIMARY_SIMPLE_INDEX_URL = "https://pypi.org/simple"
PYTORCH_CPU_SIMPLE_INDEX_URL = "https://download.pytorch.org/whl/cpu"

# All three gates must be changed deliberately for exactly one construction.
EXECUTION_MODE = operator_parameter(
    "b08_n1_execution_mode",
    "PREFLIGHT_ONLY",
    "Execution mode",
    ("PREFLIGHT_ONLY", CONSTRUCT_MODE),
)
_NETWORK_AUTHORIZATION_TEXT = operator_parameter(
    "b08_n1_network_build_authorized",
    "false",
    "Authorize network/build (true or false)",
    ("false", "true"),
)
NETWORK_AND_BUILD_AUTHORIZED = _NETWORK_AUTHORIZATION_TEXT == "true"
ONE_SHOT_ACKNOWLEDGEMENT = (
    operator_parameter(
        "b08_n1_one_shot_acknowledgement",
        "NOT_AUTHORIZED",
        "One-shot authorization acknowledgement",
        ("NOT_AUTHORIZED", ACKNOWLEDGEMENT_TEXT),
    )
)


# COMMAND ----------

PROFILE_RELATIVE_PATH = (
    Path("requirements")
    / "b08-databricks-aws-dbr17.3-x86_64-cpu-py312."
    "native-runtime-profile-v2.template.json"
)
CANONICAL_F152_LOCK_RELATIVE_PATH = Path(
    "requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock"
)

PROFILE_SCHEMA = "heterodiff-b08-databricks-native-runtime-profile-v2"
PROFILE_ID = (
    "b08-databricks-aws-native-dbr17.3-"
    "ubuntu24.04.4-linux-x86_64-cpu-py312-v2"
)
PROFILE_RECORD_DOMAIN = b"heterodiff/b08/databricks-native-runtime-profile/v2\0"
EXPECTED_PROFILE_FILE_SHA256 = (
    "4058d9e236733698a0a97022156cfbedd4af308b541883c2cc687d8b9a7840f6"
)
EXPECTED_PROFILE_SEMANTIC_SHA256 = (
    "d5994e8158737b2d1cbd369b347698e131256639b93e5a33ac1ba7ee49c098c3"
)
V2_REVIEW_RELATIVE_PATH = Path(
    "PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_TARGET_SUCCESSOR_V2_INDEPENDENT_REVIEW.md"
)
EXPECTED_V2_REVIEW_FILE_SHA256 = (
    "0d75872dc984fbbaf671875407b082dfb447bc007e55572158ed23383c2df450"
)
BUILDER_NOTEBOOK_RELATIVE_PATH = Path(
    "databricks/notebooks/b08_n1_isolated_overlay_lock_candidate.py"
)
NOTEBOOK_SCHEMA = "heterodiff-b08-n1-isolated-overlay-construction-v1"
MANIFEST_SCHEMA = "heterodiff-b08-n1-native-overlay-manifest-v1"
RECEIPT_SCHEMA = "heterodiff-b08-n1-native-overlay-receipt-v1"
ATTEMPT_INTENT_SCHEMA = "heterodiff-b08-n1-overlay-attempt-intent-v1"
FAILURE_RECEIPT_SCHEMA = "heterodiff-b08-n1-overlay-failure-receipt-v1"
SOURCE_MANIFEST_DOMAIN = b"heterodiff/b08/n1/project-source-manifest/v1\0"
OVERLAY_MANIFEST_DOMAIN = b"heterodiff/b08/n1/native-overlay-manifest/v1\0"
ATTEMPT_INTENT_DOMAIN = b"heterodiff/b08/n1/overlay-attempt-intent/v1\0"

EXPECTED_DISTRIBUTIONS = {
    "heterodiff": "0.1.0",
    "numpy": "2.4.6",
    "scipy": "1.17.1",
    "threadpoolctl": "3.6.0",
    "torch": "2.12.1+cpu",
}
ROOT_RUNTIME_REQUIREMENTS = (
    "numpy==2.4.6",
    "scipy==1.17.1",
    "threadpoolctl==3.6.0",
    "torch==2.12.1+cpu",
)
BUILD_TOOL_REQUIREMENTS = (
    "pip==25.0.1",
    "setuptools==74.0.0",
    "wheel==0.45.1",
)
EXPECTED_ENVIRONMENT_KEYS = (
    "BLIS_NUM_THREADS",
    "CUDA_VISIBLE_DEVICES",
    "LANG",
    "LC_ALL",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONHASHSEED",
    "PYTHONNOUSERSITE",
    "PYTHONSAFEPATH",
    "PYTHONUTF8",
    "TZ",
    "VECLIB_MAXIMUM_THREADS",
)

NORMALIZED_NAME = re.compile(r"[-_.]+")


class CandidateConstructionError(RuntimeError):
    def __init__(self, code, detail=None, telemetry=None):
        super().__init__(code if detail is None else f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.telemetry = telemetry


def canonical_json_bytes(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def normalized_name(value):
    return NORMALIZED_NAME.sub("-", value).lower()


def locate_repo_root():
    if REPO_ROOT_OVERRIDE is not None:
        candidates = [Path(REPO_ROOT_OVERRIDE).expanduser().resolve()]
    else:
        # Databricks Git-folder notebooks normally run with a repository-relative
        # working directory, but callers and test runners are free to choose a
        # different cwd. Prefer the tracked notebook's own location when Python
        # exposes __file__, then retain cwd ancestry as the runtime fallback.
        candidates = []
        source_hint = globals().get("__file__")
        if isinstance(source_hint, (str, os.PathLike)) and str(source_hint):
            source_parent = Path(source_hint).expanduser().resolve().parent
            candidates.extend([source_parent, *source_parent.parents])
        cwd = Path.cwd().resolve()
        candidates.extend([cwd, *cwd.parents])
        candidates = list(dict.fromkeys(candidates))
    for candidate in candidates:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "heterodiff").is_dir()
            and (candidate / PROFILE_RELATIVE_PATH).is_file()
            and (candidate / V2_REVIEW_RELATIVE_PATH).is_file()
        ):
            return candidate
    raise CandidateConstructionError(
        "REPOSITORY_ROOT_NOT_FOUND",
        "set REPO_ROOT_OVERRIDE to the absolute /Workspace/... repository path",
    )


def object_kind(path):
    if not os.path.lexists(path):
        return "ABSENT"
    mode = path.lstat().st_mode
    if stat.S_ISREG(mode):
        return "REGULAR_FILE"
    if stat.S_ISDIR(mode):
        return "DIRECTORY"
    if stat.S_ISLNK(mode):
        return "SYMLINK"
    return "OTHER"


def validate_profile(profile_path):
    raw = profile_path.read_bytes()
    file_sha256 = sha256_bytes(raw)
    errors = []
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return None, {
            "valid": False,
            "file_sha256": file_sha256,
            "semantic_sha256": None,
            "errors": [f"PROFILE_NOT_CANONICAL_ASCII_JSON:{type(error).__name__}"],
        }
    if raw != canonical_json_bytes(value) + b"\n":
        errors.append("PROFILE_BYTES_NOT_CANONICAL_JSON_PLUS_NEWLINE")
    if type(value) is not dict:
        errors.append("PROFILE_NOT_OBJECT")
        return None, {
            "valid": False,
            "file_sha256": file_sha256,
            "semantic_sha256": None,
            "errors": errors,
        }
    projection = dict(value)
    declared_digest = projection.pop("record_sha256", None)
    semantic_sha256 = sha256_bytes(
        PROFILE_RECORD_DOMAIN + canonical_json_bytes(projection)
    )
    if file_sha256 != EXPECTED_PROFILE_FILE_SHA256:
        errors.append("PROFILE_FILE_SHA256_DIFFERS_FROM_ACCEPTED_V2")
    if semantic_sha256 != EXPECTED_PROFILE_SEMANTIC_SHA256:
        errors.append("PROFILE_SEMANTIC_SHA256_DIFFERS_FROM_ACCEPTED_V2")
    if value.get("schema_version") != PROFILE_SCHEMA:
        errors.append("PROFILE_SCHEMA_MISMATCH")
    if value.get("profile_id") != PROFILE_ID:
        errors.append("PROFILE_ID_MISMATCH")
    if value.get("lifecycle_state") != "DRAFT_UNRESOLVED_F152_LOCK":
        errors.append("PROFILE_LIFECYCLE_STATE_MISMATCH")
    if declared_digest != semantic_sha256:
        errors.append("PROFILE_SEMANTIC_DIGEST_INVALID")
    f152 = value.get("f152_lock")
    if type(f152) is not dict:
        errors.append("PROFILE_F152_NOT_OBJECT")
    else:
        if f152.get("path") != CANONICAL_F152_LOCK_RELATIVE_PATH.as_posix():
            errors.append("PROFILE_F152_PATH_MISMATCH")
        if f152.get("expected_distributions") != EXPECTED_DISTRIBUTIONS:
            errors.append("PROFILE_EXPECTED_DISTRIBUTIONS_MISMATCH")
        if any(
            f152.get(key) is not False
            for key in (
                "present_and_regular",
                "complete_transitive_lock",
                "artifact_closure_verified",
            )
        ):
            errors.append("PROFILE_F152_DRAFT_OVERCLAIMS")
        if f152.get("sha256") is not None:
            errors.append("PROFILE_F152_DRAFT_HASH_NOT_NULL")
    environment = value.get("f153_environment")
    if (
        type(environment) is not dict
        or tuple(sorted(environment)) != tuple(sorted(EXPECTED_ENVIRONMENT_KEYS))
    ):
        errors.append("PROFILE_F153_ENVIRONMENT_SHAPE_MISMATCH")
    route = value.get("native_route")
    required_route = {
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
        route.get(key) != expected for key, expected in required_route.items()
    ):
        errors.append("PROFILE_NATIVE_ROUTE_SAFETY_MISMATCH")
    safety = value.get("safety_boundary")
    if (
        type(safety) is not dict
        or not safety
        or any(item is not False for item in safety.values())
    ):
        errors.append("PROFILE_SAFETY_BOUNDARY_NOT_ALL_FALSE")
    return value, {
        "valid": not errors,
        "file_sha256": file_sha256,
        "semantic_sha256": semantic_sha256,
        "errors": errors,
    }


def read_os_release():
    path = Path("/etc/os-release")
    if not path.is_file():
        return {}
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key] = value.strip().strip('"').strip("'")
    return result


def operating_system_release_matches(
    expected_distribution,
    expected_release,
    observed_release,
):
    if not all(
        type(value) is str and value
        for value in (
            expected_distribution,
            expected_release,
            observed_release,
        )
    ):
        return False
    return observed_release in {
        expected_release,
        f"{expected_distribution} {expected_release}",
    }


def observe_runtime(profile):
    target = profile["target"]
    os_release = read_os_release()
    dbr_version = os.environ.get("DATABRICKS_RUNTIME_VERSION")
    observed = {
        "databricks_runtime_version": dbr_version,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_abi": f"cp{sys.version_info.major}{sys.version_info.minor}",
        "operating_system_family": platform.system(),
        "operating_system_distribution": os_release.get("NAME"),
        "operating_system_release": os_release.get("PRETTY_NAME"),
        "architecture": platform.machine(),
        "pointer_bits": struct.calcsize("P") * 8,
        "byteorder": sys.byteorder,
        "soabi": sysconfig.get_config_var("SOABI"),
        "multiarch": sysconfig.get_config_var("MULTIARCH"),
        "extension_suffix": sysconfig.get_config_var("EXT_SUFFIX"),
        "cache_tag": sys.implementation.cache_tag,
    }
    expected = {
        "databricks_runtime_version": target["databricks_runtime_version_prefix"],
        "python_version": target["python_version"],
        "python_implementation": target["python_implementation"],
        "python_abi": target["python_abi"],
        "operating_system_family": target["operating_system_family"],
        "operating_system_distribution": target["operating_system_distribution"],
        "operating_system_release": target["operating_system_release"],
        "architecture": target["architecture"],
        "pointer_bits": target["pointer_bits"],
        "byteorder": target["byteorder"],
        "soabi": "prefix cpython-312-",
        "multiarch": "x86_64-linux-gnu",
        "extension_suffix": "contains cpython-312",
        "cache_tag": "cpython-312",
    }
    exact = {
        "databricks_runtime_version": (
            type(dbr_version) is str
            and re.fullmatch(
                re.escape(target["databricks_runtime_version_prefix"]) + r"(?:\..*)?",
                dbr_version,
            )
            is not None
        ),
        "python_version": observed["python_version"] == expected["python_version"],
        "python_implementation": (
            observed["python_implementation"] == expected["python_implementation"]
        ),
        "python_abi": observed["python_abi"] == expected["python_abi"],
        "operating_system_family": (
            observed["operating_system_family"]
            == expected["operating_system_family"]
        ),
        "operating_system_distribution": (
            observed["operating_system_distribution"]
            == expected["operating_system_distribution"]
        ),
        "operating_system_release": (
            operating_system_release_matches(
                expected["operating_system_distribution"],
                expected["operating_system_release"],
                observed["operating_system_release"],
            )
        ),
        "architecture": (
            str(observed["architecture"]).casefold()
            == str(expected["architecture"]).casefold()
        ),
        "pointer_bits": observed["pointer_bits"] == expected["pointer_bits"],
        "byteorder": observed["byteorder"] == expected["byteorder"],
        "soabi": (
            type(observed["soabi"]) is str
            and observed["soabi"].startswith("cpython-312-")
        ),
        "multiarch": observed["multiarch"] == expected["multiarch"],
        "extension_suffix": (
            type(observed["extension_suffix"]) is str
            and "cpython-312" in observed["extension_suffix"]
        ),
        "cache_tag": observed["cache_tag"] == expected["cache_tag"],
    }
    mismatches = {
        key: {"expected": expected[key], "observed": observed[key]}
        for key in exact
        if not exact[key]
    }
    return {
        "observed": observed,
        "expected": expected,
        "exact": not mismatches,
        "mismatches": mismatches,
        "cpu_count": os.cpu_count(),
    }


def observe_environment(profile):
    expected = profile["f153_environment"]
    observed = {name: os.environ.get(name) for name in expected}
    mismatches = {
        name: {"expected": expected[name], "observed": observed[name]}
        for name in expected
        if observed[name] != expected[name]
    }
    return {
        "expected": expected,
        "observed": observed,
        "exact": not mismatches,
        "mismatches": mismatches,
    }


def validate_destination(value):
    errors = []
    details = {
        "configured": value is not None,
        "path": value,
        "object_kind": None,
        "parent_exists_and_is_directory": False,
    }
    if type(value) is not str or not value:
        errors.append("DURABLE_OUTPUT_DIRECTORY_REQUIRED")
        return details, errors
    if any(ord(character) < 32 for character in value):
        errors.append("DURABLE_OUTPUT_DIRECTORY_HAS_CONTROL_CHARACTER")
        return details, errors
    pure = PurePosixPath(value)
    parts = pure.parts
    if (
        not pure.is_absolute()
        or len(parts) < 6
        or parts[0] != "/"
        or parts[1] != "Volumes"
        or any(part in ("", ".", "..") for part in parts[2:])
    ):
        errors.append(
            "DURABLE_OUTPUT_DIRECTORY_MUST_BE_NEW_CHILD_BELOW_/Volumes/catalog/schema/volume"
        )
        return details, errors
    path = Path(value)
    try:
        details["object_kind"] = object_kind(path)
        details["parent_exists_and_is_directory"] = path.parent.is_dir()
    except OSError as error:
        details["object_kind"] = "UNAVAILABLE"
        errors.append(
            "DURABLE_OUTPUT_PATH_VISIBILITY_FAILED:" + type(error).__name__
        )
        return details, errors
    if details["object_kind"] != "ABSENT":
        errors.append("DURABLE_OUTPUT_DIRECTORY_MUST_NOT_ALREADY_EXIST")
    if not details["parent_exists_and_is_directory"]:
        errors.append("DURABLE_OUTPUT_PARENT_MUST_EXIST_AND_BE_DIRECTORY")
    if not errors:
        try:
            details["ancestor_binding"] = volume_ancestor_binding(path)
        except CandidateConstructionError as error:
            errors.append(error.code)
    return details, errors


def volume_ancestor_binding(destination):
    pure = PurePosixPath(str(destination))
    if (
        not pure.is_absolute()
        or len(pure.parts) < 6
        or pure.parts[:2] != ("/", "Volumes")
    ):
        raise CandidateConstructionError("DURABLE_VOLUME_PATH_SHAPE_INVALID")
    current = Path("/")
    rows = []
    for part in pure.parts[1:-1]:
        current = current / part
        try:
            observed = current.lstat()
        except OSError as error:
            raise CandidateConstructionError(
                "DURABLE_VOLUME_ANCESTOR_UNAVAILABLE",
                type(error).__name__,
            ) from error
        if not stat.S_ISDIR(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
            raise CandidateConstructionError(
                "DURABLE_VOLUME_ANCESTOR_NOT_PHYSICAL_DIRECTORY",
                current.as_posix(),
            )
        rows.append(
            {
                "path": current.as_posix(),
                "device": observed.st_dev,
                "inode": observed.st_ino,
                "mode": observed.st_mode,
            }
        )
    return rows


def require_ancestor_binding_unchanged(destination, expected):
    observed = volume_ancestor_binding(destination)
    if observed != expected:
        raise CandidateConstructionError(
            "DURABLE_VOLUME_ANCESTOR_BINDING_CHANGED"
        )
    return observed


def validate_index_url(label, value):
    if type(value) is not str or not value:
        return None, [label + "_REQUIRED"]
    parsed = urlsplit(value)
    errors = []
    if parsed.scheme != "https":
        errors.append(label + "_MUST_USE_HTTPS")
    if not parsed.hostname:
        errors.append(label + "_MUST_HAVE_HOST")
    if parsed.username is not None or parsed.password is not None:
        errors.append(label + "_MUST_NOT_CONTAIN_CREDENTIALS")
    if parsed.query or parsed.fragment:
        errors.append(label + "_MUST_NOT_HAVE_QUERY_OR_FRAGMENT")
    if any(ord(character) < 32 for character in value):
        errors.append(label + "_HAS_CONTROL_CHARACTER")
    projection = None
    if not errors:
        projection = {
            "url": value.rstrip("/"),
            "host": parsed.hostname,
            "sha256": sha256_bytes(value.rstrip("/").encode("utf-8")),
        }
    return projection, errors


def preflight():
    repo_root = locate_repo_root()
    profile, profile_validation = validate_profile(repo_root / PROFILE_RELATIVE_PATH)
    review_binding = regular_file_binding(
        repo_root,
        V2_REVIEW_RELATIVE_PATH,
        "V2_INDEPENDENT_REVIEW",
    )
    lock_kind = object_kind(repo_root / CANONICAL_F152_LOCK_RELATIVE_PATH)
    destination, destination_errors = validate_destination(DURABLE_OUTPUT_DIRECTORY)
    primary_index, primary_errors = validate_index_url(
        "PRIMARY_SIMPLE_INDEX_URL", PRIMARY_SIMPLE_INDEX_URL
    )
    torch_index, torch_errors = validate_index_url(
        "PYTORCH_CPU_SIMPLE_INDEX_URL", PYTORCH_CPU_SIMPLE_INDEX_URL
    )

    errors = list(profile_validation["errors"])
    if review_binding["sha256"] != EXPECTED_V2_REVIEW_FILE_SHA256:
        errors.append("V2_INDEPENDENT_REVIEW_SHA256_MISMATCH")
    required_inputs = []
    if DURABLE_OUTPUT_DIRECTORY is None:
        required_inputs.append("DURABLE_OUTPUT_DIRECTORY")
    if _NETWORK_AUTHORIZATION_TEXT not in ("false", "true"):
        errors.append("NETWORK_AND_BUILD_AUTHORIZATION_TEXT_INVALID")
    if EXECUTION_MODE != CONSTRUCT_MODE:
        required_inputs.append(f"EXECUTION_MODE={CONSTRUCT_MODE}")
    if NETWORK_AND_BUILD_AUTHORIZED is not True:
        required_inputs.append("NETWORK_AND_BUILD_AUTHORIZED=True")
    if ONE_SHOT_ACKNOWLEDGEMENT != ACKNOWLEDGEMENT_TEXT:
        required_inputs.append(
            "ONE_SHOT_ACKNOWLEDGEMENT=" + ACKNOWLEDGEMENT_TEXT
        )
    errors.extend(destination_errors)
    errors.extend(primary_errors)
    errors.extend(torch_errors)
    if lock_kind != "ABSENT":
        errors.append("CANONICAL_F152_LOCK_OBJECT_ALREADY_EXISTS")

    runtime = None
    environment = None
    if profile is not None and profile_validation["valid"]:
        runtime = observe_runtime(profile)
        environment = observe_environment(profile)
        if not runtime["exact"]:
            errors.append("RUNTIME_DOES_NOT_MATCH_ACTIVE_NATIVE_PROFILE")
        if not environment["exact"]:
            errors.append("F153_ENVIRONMENT_MISMATCH")

    construction_authorized = (
        profile_validation["valid"]
        and not errors
        and not required_inputs
        and EXECUTION_MODE == CONSTRUCT_MODE
        and NETWORK_AND_BUILD_AUTHORIZED is True
        and ONE_SHOT_ACKNOWLEDGEMENT == ACKNOWLEDGEMENT_TEXT
    )
    if construction_authorized:
        decision = "PROCEED_ONE_ISOLATED_NETWORK_BUILD"
    elif runtime is not None and not runtime["exact"]:
        decision = "HOLD_RUNTIME_PROFILE_MISMATCH_REQUIRES_REVIEW"
    else:
        decision = "HOLD_PREFLIGHT_INPUTS_OR_AUTHORITY_INCOMPLETE"
    return {
        "schema_version": NOTEBOOK_SCHEMA,
        "scope": "DATA_FREE_NATIVE_OVERLAY_CANDIDATE_CONSTRUCTION_ONLY",
        "decision": decision,
        "construction_authorized": construction_authorized,
        "repo_root": repo_root,
        "profile": profile,
        "profile_validation": profile_validation,
        "v2_independent_review_binding": review_binding,
        "canonical_f152_lock_object_kind": lock_kind,
        "runtime": runtime,
        "environment": environment,
        "destination": destination,
        "destination_errors": destination_errors,
        "primary_index": primary_index,
        "torch_index": torch_index,
        "required_inputs": sorted(set(required_inputs)),
        "errors": sorted(set(errors)),
        "safety": {
            "base_runtime_install_executed": False,
            "bounded_widget_input_accessed": _WIDGET_INPUT_ACCESSED,
            "databricks_rest_api_accessed": False,
            "network_or_contact_accessed": False,
            "package_resolution_executed": False,
            "project_wheel_build_executed": False,
            "files_written": False,
            "spark_accessed": False,
            "study_or_test_data_accessed": False,
            "calibration_training_or_inference_executed": False,
        },
    }


# COMMAND ----------

# DBTITLE 1,Cell 7
def require_regular_source_file(path, root):
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise CandidateConstructionError("SOURCE_PATH_ESCAPES_ROOT") from error
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode):
        raise CandidateConstructionError(
            "SOURCE_OBJECT_NOT_REGULAR_FILE", relative.as_posix()
        )
    return relative


def project_source_manifest(repo_root):
    sources = [repo_root / "pyproject.toml", repo_root / "README.md"]
    sources.extend(sorted((repo_root / "src" / "heterodiff").rglob("*.py")))
    records = []
    for path in sources:
        relative = require_regular_source_file(path, repo_root)
        digest, size = sha256_file(path)
        observed_mode = path.lstat().st_mode & 0o777
        canonical_mode = 0o755 if observed_mode & 0o111 else 0o644
        records.append(
            {
                "relative_path": relative.as_posix(),
                "sha256": digest,
                "size_bytes": size,
                "mode_octal": format(canonical_mode, "04o"),
            }
        )
    if not records:
        raise CandidateConstructionError("SOURCE_MANIFEST_EMPTY")
    value = {
        "schema_version": "heterodiff-b08-n1-project-source-manifest-v1",
        "files": records,
    }
    value["record_sha256"] = sha256_bytes(
        SOURCE_MANIFEST_DOMAIN + canonical_json_bytes(value)
    )
    return value


def regular_file_binding(repo_root, relative_path, label):
    path = repo_root / relative_path
    if object_kind(path) != "REGULAR_FILE":
        raise CandidateConstructionError(label + "_NOT_REGULAR_FILE")
    digest, size = sha256_file(path)
    observed_mode = path.lstat().st_mode & 0o777
    canonical_mode = 0o755 if observed_mode & 0o111 else 0o644
    return {
        "relative_path": relative_path.as_posix(),
        "sha256": digest,
        "size_bytes": size,
        "mode_octal": format(canonical_mode, "04o"),
    }


def copy_source_tree(repo_root, source_manifest, destination):
    destination.mkdir(mode=0o750)
    for record in source_manifest["files"]:
        source = repo_root / record["relative_path"]
        target = destination / record["relative_path"]
        target.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
        if object_kind(target) != "ABSENT":
            raise CandidateConstructionError("STAGING_SOURCE_COLLISION")
        shutil.copyfile(source, target)
        os.chmod(target, int(record["mode_octal"], 8))
        copied_sha256, copied_size = sha256_file(target)
        if (
            copied_sha256 != record["sha256"]
            or copied_size != record["size_bytes"]
        ):
            raise CandidateConstructionError("STAGING_SOURCE_COPY_MISMATCH")
        if format(target.stat().st_mode & 0o777, "04o") != record["mode_octal"]:
            raise CandidateConstructionError("STAGING_SOURCE_MODE_MISMATCH")


def sanitized_command(argv, primary_url, torch_url):
    result = []
    for value in argv:
        if value == primary_url:
            result.append("<PRIMARY_INDEX_URL>")
        elif value == torch_url:
            result.append("<PYTORCH_CPU_INDEX_URL>")
        else:
            result.append(value)
    return result


def run_tool(
    journal,
    step,
    argv,
    cwd,
    environment,
    primary_url,
    torch_url,
    attempt_state=None,
    phase_flags=(),
    durable_attempt=None,
):
    if attempt_state is not None:
        if attempt_state.get("durable_intent_committed") is not True:
            raise CandidateConstructionError(
                "DURABLE_INTENT_REQUIRED_BEFORE_NETWORK_OR_BUILD",
                step,
                telemetry=dict(attempt_state),
            )
        if durable_attempt is None:
            raise CandidateConstructionError(
                "DURABLE_INTENT_CUSTODY_REQUIRED_BEFORE_TOOL_STEP",
                step,
                telemetry=dict(attempt_state),
            )
        try:
            verify_durable_intent_custody(
                durable_attempt,
                attempt_state["durable_intent_expected_sha256"],
                attempt_state["durable_intent_expected_size_bytes"],
            )
        except CandidateConstructionError as error:
            attempt_state["last_failed_step"] = step
            raise CandidateConstructionError(
                error.code,
                error.detail,
                telemetry=dict(attempt_state),
            ) from error
        for flag in phase_flags:
            attempt_state[flag] = True
        attempt_state["last_started_step"] = step
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            close_fds=True,
            timeout=1800,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        entry = {
            "step": step,
            "argv": sanitized_command(argv, primary_url, torch_url),
            "returncode": None,
            "execution_error": type(error).__name__,
        }
        journal.append(entry)
        if attempt_state is not None:
            attempt_state["command_journal"] = list(journal)
            attempt_state["last_failed_step"] = step
        raise CandidateConstructionError(
            "TOOL_STEP_EXECUTION_FAILED",
            f"{step}:{type(error).__name__}",
            telemetry=(None if attempt_state is None else dict(attempt_state)),
        ) from error
    entry = {
        "step": step,
        "argv": sanitized_command(argv, primary_url, torch_url),
        "returncode": completed.returncode,
        "stdout_sha256": sha256_bytes(completed.stdout),
        "stderr_sha256": sha256_bytes(completed.stderr),
    }
    journal.append(entry)
    if attempt_state is not None:
        attempt_state["command_journal"] = list(journal)
    if completed.returncode != 0:
        if attempt_state is not None:
            attempt_state["last_failed_step"] = step
        raise CandidateConstructionError(
            "TOOL_STEP_FAILED",
            f"{step}:returncode={completed.returncode}",
            telemetry=(None if attempt_state is None else dict(attempt_state)),
        )
    if attempt_state is not None:
        attempt_state["last_completed_step"] = step
    return completed.stdout


def isolated_environment(venv_root, source_date_epoch, deterministic_environment):
    bin_path = venv_root / "bin"
    environment = dict(deterministic_environment)
    environment.update({
        "PATH": f"{bin_path}:/usr/bin:/bin",
        "PIP_CONFIG_FILE": os.devnull,
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_CACHE_DIR": "1",
        "PIP_NO_INPUT": "1",
        "SOURCE_DATE_EPOCH": str(source_date_epoch),
    })
    return environment


def required_bootstrap_pip_version():
    pip_requirement = next(
        (req for req in BUILD_TOOL_REQUIREMENTS if req.startswith("pip==")),
        None,
    )
    if pip_requirement is None:
        raise CandidateConstructionError("BOOTSTRAP_PIP_REQUIREMENT_NOT_DECLARED")
    return pip_requirement.split("==", 1)[1]


def pip_bootstrap_plan():
    ensurepip_spec = importlib.util.find_spec("ensurepip")
    return {
        "method": "BOUND_HOST_PIP_INSTALLS_INSPECTED_PINNED_WHEEL",
        "required_pip_version": required_bootstrap_pip_version(),
        "ensurepip_observation": {
            "available": ensurepip_spec is not None,
            "origin": (
                None
                if ensurepip_spec is None
                else ensurepip_spec.origin
            ),
        },
    }


def inspect_wheel(path):
    artifact_sha256, size = sha256_file(path)
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as error:
        raise CandidateConstructionError("WHEEL_ARCHIVE_INVALID", path.name) from error
    with archive:
        infos = archive.infolist()
        names = [item.filename for item in infos if not item.is_dir()]
        if len(names) != len(set(names)):
            raise CandidateConstructionError("WHEEL_DUPLICATE_ARCHIVE_PATH", path.name)
        for name in names:
            pure = PurePosixPath(name)
            if (
                pure.is_absolute()
                or ".." in pure.parts
                or "\\" in name
                or any(part in ("", ".") for part in pure.parts)
            ):
                raise CandidateConstructionError("WHEEL_UNSAFE_ARCHIVE_PATH", path.name)
        metadata_names = [
            name
            for name in names
            if name.endswith(".dist-info/METADATA")
        ]
        record_names = [
            name for name in names if name.endswith(".dist-info/RECORD")
        ]
        wheel_names = [
            name for name in names if name.endswith(".dist-info/WHEEL")
        ]
        if (
            len(metadata_names) != 1
            or len(record_names) != 1
            or len(wheel_names) != 1
        ):
            raise CandidateConstructionError(
                "WHEEL_DIST_INFO_CARDINALITY_INVALID", path.name
            )
        message = email.parser.BytesParser().parsebytes(
            archive.read(metadata_names[0])
        )
        distribution = message.get("Name")
        version = message.get("Version")
        if not distribution or not version:
            raise CandidateConstructionError("WHEEL_METADATA_IDENTITY_MISSING", path.name)
        record_bytes = archive.read(record_names[0])
        try:
            record_text = record_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CandidateConstructionError("WHEEL_RECORD_NOT_UTF8", path.name) from error
        record_paths = set()
        for row in csv.reader(io.StringIO(record_text)):
            if len(row) != 3:
                raise CandidateConstructionError("WHEEL_RECORD_ROW_INVALID", path.name)
            record_path, hash_field, size_field = row
            if record_path in record_paths:
                raise CandidateConstructionError(
                    "WHEEL_RECORD_DUPLICATE_PATH", path.name
                )
            record_paths.add(record_path)
            if record_path not in names:
                raise CandidateConstructionError(
                    "WHEEL_RECORD_REFERENCES_MISSING_MEMBER", path.name
                )
            payload = archive.read(record_path)
            if hash_field:
                algorithm, separator, encoded = hash_field.partition("=")
                if separator != "=" or algorithm != "sha256":
                    raise CandidateConstructionError(
                        "WHEEL_RECORD_NON_SHA256_HASH", path.name
                    )
                padding = "=" * ((4 - len(encoded) % 4) % 4)
                try:
                    declared = base64.urlsafe_b64decode(encoded + padding).hex()
                except (ValueError, base64.binascii.Error) as error:
                    raise CandidateConstructionError(
                        "WHEEL_RECORD_HASH_ENCODING_INVALID", path.name
                    ) from error
                if declared != sha256_bytes(payload):
                    raise CandidateConstructionError(
                        "WHEEL_RECORD_HASH_MISMATCH", path.name
                    )
            elif record_path != record_names[0]:
                raise CandidateConstructionError(
                    "WHEEL_RECORD_UNHASHED_NON_RECORD_MEMBER", path.name
                )
            if size_field and int(size_field) != len(payload):
                raise CandidateConstructionError(
                    "WHEEL_RECORD_SIZE_MISMATCH", path.name
                )
        if record_paths != set(names):
            raise CandidateConstructionError(
                "WHEEL_RECORD_PAYLOAD_CLOSURE_INCOMPLETE", path.name
            )
        wheel_metadata = archive.read(wheel_names[0]).decode("utf-8")
        tags = sorted(
            line.split(":", 1)[1].strip()
            for line in wheel_metadata.splitlines()
            if line.startswith("Tag:")
        )
    return {
        "filename": path.name,
        "sha256": artifact_sha256,
        "size_bytes": size,
        "distribution_name": distribution,
        "normalized_name": normalized_name(distribution),
        "version": version,
        "wheel_tags": tags,
        "embedded_record_sha256": sha256_bytes(record_bytes),
        "embedded_payload_file_count": len(names),
    }


def inspect_wheel_directory(directory):
    objects = sorted(directory.iterdir(), key=lambda item: item.name)
    if not objects:
        raise CandidateConstructionError("WHEEL_DIRECTORY_EMPTY")
    if any(object_kind(path) != "REGULAR_FILE" for path in objects):
        raise CandidateConstructionError("WHEEL_DIRECTORY_HAS_NONREGULAR_OBJECT")
    if any(path.suffix != ".whl" for path in objects):
        raise CandidateConstructionError("SDIST_OR_NON_WHEEL_ARTIFACT_PRESENT")
    records = [inspect_wheel(path) for path in objects]
    names = [record["normalized_name"] for record in records]
    if len(names) != len(set(names)):
        raise CandidateConstructionError("DUPLICATE_DISTRIBUTION_WHEELS")
    return records


PIP_IDENTITY_PROBE = """
import base64
import csv
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys

spec = importlib.util.find_spec("pip")
if spec is None or not isinstance(spec.origin, str):
    raise RuntimeError("PIP_MODULE_ORIGIN_UNAVAILABLE")
distribution = importlib.metadata.distribution("pip")
record_candidates = [
    item
    for item in (distribution.files or ())
    if str(item).endswith(".dist-info/RECORD")
]
if len(record_candidates) != 1:
    raise RuntimeError("PIP_DISTRIBUTION_RECORD_UNAVAILABLE")
install_prefix = Path(sys.prefix).resolve()
module_path = Path(spec.origin).resolve()
record_path = Path(
    distribution.locate_file(record_candidates[0])
).resolve()
module_payload = module_path.read_bytes()
record_payload = record_path.read_bytes()
rows = list(csv.reader(io.StringIO(record_payload.decode("utf-8"))))
declared_paths = set()
resolved_paths = set()
payload_manifest = []
hashed_record_count = 0
unhashed_record_count = 0
for row in rows:
    if len(row) != 3:
        raise RuntimeError("PIP_RECORD_ROW_SHAPE_INVALID")
    relative, declared_digest, declared_size = row
    if (
        not relative
        or relative in declared_paths
        or "\\\\" in relative
        or Path(relative).is_absolute()
    ):
        raise RuntimeError("PIP_RECORD_PATH_INVALID")
    declared_paths.add(relative)
    located = Path(distribution.locate_file(relative))
    observed_stat = located.lstat()
    if stat.S_ISLNK(observed_stat.st_mode) or not stat.S_ISREG(
        observed_stat.st_mode
    ):
        raise RuntimeError("PIP_RECORD_OBJECT_NOT_REGULAR_FILE")
    resolved = located.resolve()
    try:
        install_relative = resolved.relative_to(install_prefix).as_posix()
    except ValueError as error:
        raise RuntimeError("PIP_RECORD_PATH_ESCAPES_INSTALL_PREFIX") from error
    if resolved in resolved_paths:
        raise RuntimeError("PIP_RECORD_RESOLVED_PATH_DUPLICATE")
    resolved_paths.add(resolved)
    payload = resolved.read_bytes()
    actual_digest = hashlib.sha256(payload).digest()
    if bool(declared_digest) != bool(declared_size):
        raise RuntimeError("PIP_RECORD_HASH_SIZE_PAIR_INCOMPLETE")
    if declared_digest:
        algorithm, separator, encoded = declared_digest.partition("=")
        if algorithm != "sha256" or separator != "=" or not encoded:
            raise RuntimeError("PIP_RECORD_DIGEST_INVALID")
        padding = "=" * (-len(encoded) % 4)
        if base64.urlsafe_b64decode(encoded + padding) != actual_digest:
            raise RuntimeError("PIP_RECORD_DIGEST_MISMATCH")
        if int(declared_size) != len(payload):
            raise RuntimeError("PIP_RECORD_SIZE_MISMATCH")
        hashed_record_count += 1
    else:
        unhashed_record_count += 1
    payload_manifest.append({
        "install_relative_path": install_relative,
        "record_declared": True,
        "sha256": actual_digest.hex(),
        "size_bytes": len(payload),
    })

module_root = module_path.parent
dist_info_root = record_path.parent
physical_payload_paths = set()
for physical_root in (module_root, dist_info_root):
    root_stat = physical_root.lstat()
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise RuntimeError("PIP_PAYLOAD_ROOT_NOT_PHYSICAL_DIRECTORY")
    pending = [physical_root]
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                if entry.is_symlink():
                    raise RuntimeError("PIP_PAYLOAD_SYMLINK_REJECTED")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    physical_payload_paths.add(Path(entry.path).resolve())
                else:
                    raise RuntimeError("PIP_PAYLOAD_OBJECT_TYPE_INVALID")

scoped_declared_paths = set()
for resolved in resolved_paths:
    for physical_root in (module_root, dist_info_root):
        try:
            resolved.relative_to(physical_root)
        except ValueError:
            continue
        scoped_declared_paths.add(resolved)
        break
missing_physical_paths = scoped_declared_paths - physical_payload_paths
if missing_physical_paths:
    raise RuntimeError("PIP_PAYLOAD_RECORD_CLOSURE_MISMATCH")
unrecorded_bytecode_paths = physical_payload_paths - scoped_declared_paths
for path in unrecorded_bytecode_paths:
    install_relative = path.relative_to(install_prefix).as_posix()
    if path.suffix != ".pyc" or "__pycache__" not in path.parts:
        raise RuntimeError("PIP_PAYLOAD_UNRECORDED_NONBYTECODE_FILE")
    payload = path.read_bytes()
    payload_manifest.append({
        "install_relative_path": install_relative,
        "record_declared": False,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
    })

payload_manifest.sort(key=lambda item: item["install_relative_path"])
payload_manifest_bytes = json.dumps(
    payload_manifest,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
print(json.dumps({
    "pip_distribution_root": str(record_path.parent.parent),
    "pip_install_prefix": str(install_prefix),
    "pip_module_file": str(module_path),
    "pip_module_file_sha256": hashlib.sha256(module_payload).hexdigest(),
    "pip_module_file_size_bytes": len(module_payload),
    "pip_payload_closure_exact": True,
    "pip_payload_file_count": len(payload_manifest),
    "pip_payload_hashed_record_count": hashed_record_count,
    "pip_payload_manifest_sha256": hashlib.sha256(
        b"heterodiff/pip-installed-payload/v1\\0" + payload_manifest_bytes
    ).hexdigest(),
    "pip_payload_unhashed_record_count": unhashed_record_count,
    "pip_payload_unrecorded_bytecode_count": len(
        unrecorded_bytecode_paths
    ),
    "pip_record_file": str(record_path),
    "pip_record_file_sha256": hashlib.sha256(record_payload).hexdigest(),
    "pip_record_file_size_bytes": len(record_payload),
    "pip_version": distribution.version,
    "python_executable": str(Path(sys.executable).resolve()),
}, sort_keys=True, separators=(",", ":")))
""".strip()


def bind_pip_identity(
    journal,
    step,
    python_executable,
    cwd,
    environment,
    primary_url,
    torch_url,
    attempt_state,
    durable_attempt,
    expected_version,
    expected_root=None,
):
    raw = run_tool(
        journal,
        step,
        [python_executable, "-I", "-B", "-c", PIP_IDENTITY_PROBE],
        cwd,
        environment,
        primary_url,
        torch_url,
        attempt_state,
        (),
        durable_attempt,
    )
    try:
        identity = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CandidateConstructionError(
            "PIP_IDENTITY_OUTPUT_INVALID",
            step,
        ) from error
    required_keys = {
        "pip_distribution_root",
        "pip_install_prefix",
        "pip_module_file",
        "pip_module_file_sha256",
        "pip_module_file_size_bytes",
        "pip_payload_closure_exact",
        "pip_payload_file_count",
        "pip_payload_hashed_record_count",
        "pip_payload_manifest_sha256",
        "pip_payload_unhashed_record_count",
        "pip_payload_unrecorded_bytecode_count",
        "pip_record_file",
        "pip_record_file_sha256",
        "pip_record_file_size_bytes",
        "pip_version",
        "python_executable",
    }
    if type(identity) is not dict or set(identity) != required_keys:
        raise CandidateConstructionError("PIP_IDENTITY_SHAPE_INVALID", step)
    if identity["pip_version"] != expected_version:
        raise CandidateConstructionError(
            "PIP_IDENTITY_VERSION_MISMATCH",
            step,
        )
    payload_counts = (
        identity["pip_payload_file_count"],
        identity["pip_payload_hashed_record_count"],
        identity["pip_payload_unhashed_record_count"],
        identity["pip_payload_unrecorded_bytecode_count"],
    )
    if (
        identity["pip_payload_closure_exact"] is not True
        or any(type(value) is not int or value < 0 for value in payload_counts)
        or payload_counts[0] <= 0
        or sum(payload_counts[1:]) != payload_counts[0]
        or type(identity["pip_payload_manifest_sha256"]) is not str
        or re.fullmatch(
            r"[0-9a-f]{64}",
            identity["pip_payload_manifest_sha256"],
        )
        is None
    ):
        raise CandidateConstructionError(
            "PIP_IDENTITY_PAYLOAD_CLOSURE_INVALID",
            step,
        )
    expected_python = str(Path(python_executable).resolve())
    if identity["python_executable"] != expected_python:
        raise CandidateConstructionError(
            "PIP_IDENTITY_PYTHON_MISMATCH",
            step,
        )
    for prefix in ("pip_install_prefix", "pip_distribution_root"):
        if (
            type(identity[prefix]) is not str
            or not Path(identity[prefix]).is_absolute()
            or object_kind(Path(identity[prefix])) != "DIRECTORY"
        ):
            raise CandidateConstructionError(
                "PIP_IDENTITY_DIRECTORY_BINDING_INVALID",
                prefix,
            )
    install_prefix = Path(identity["pip_install_prefix"])
    distribution_root = Path(identity["pip_distribution_root"])
    try:
        distribution_root.relative_to(install_prefix)
        Path(identity["python_executable"]).relative_to(install_prefix)
    except ValueError as error:
        raise CandidateConstructionError(
            "PIP_IDENTITY_ESCAPES_INSTALL_PREFIX",
            step,
        ) from error
    root = None if expected_root is None else Path(expected_root).resolve()
    if root is not None and install_prefix != root:
        raise CandidateConstructionError(
            "PIP_IDENTITY_INSTALL_PREFIX_MISMATCH",
            step,
        )
    resolved_paths = {}
    for prefix in ("pip_module_file", "pip_record_file"):
        path_value = identity[prefix]
        digest_value = identity[prefix + "_sha256"]
        size_value = identity[prefix + "_size_bytes"]
        if (
            type(path_value) is not str
            or not Path(path_value).is_absolute()
            or type(digest_value) is not str
            or re.fullmatch(r"[0-9a-f]{64}", digest_value) is None
            or type(size_value) is not int
            or size_value <= 0
        ):
            raise CandidateConstructionError(
                "PIP_IDENTITY_FILE_BINDING_INVALID",
                prefix,
            )
        path = Path(path_value)
        resolved_paths[prefix] = path
        if object_kind(path) != "REGULAR_FILE":
            raise CandidateConstructionError(
                "PIP_IDENTITY_FILE_NOT_REGULAR",
                prefix,
            )
        observed_digest, observed_size = sha256_file(path)
        if (
            observed_digest != digest_value
            or observed_size != size_value
        ):
            raise CandidateConstructionError(
                "PIP_IDENTITY_FILE_BINDING_MISMATCH",
                prefix,
            )
        if root is not None:
            try:
                path.relative_to(root)
            except ValueError as error:
                raise CandidateConstructionError(
                    "PIP_IDENTITY_ESCAPES_EXPECTED_ROOT",
                    prefix,
                ) from error
    if resolved_paths["pip_record_file"].parent.parent != distribution_root:
        raise CandidateConstructionError(
            "PIP_DISTRIBUTION_ROOT_BINDING_MISMATCH",
            step,
        )
    try:
        resolved_paths["pip_module_file"].relative_to(distribution_root)
    except ValueError as error:
        raise CandidateConstructionError(
            "PIP_MODULE_AND_DISTRIBUTION_ROOT_MISMATCH",
            step,
        ) from error
    return identity


def bootstrap_pip_into_isolated_venv(
    journal,
    staging_root,
    build_venv,
    venv_python,
    tool_wheelhouse,
    provisional_environment,
    isolated_venv_environment,
    primary_url,
    torch_url,
    attempt_state,
    durable_attempt,
):
    binding = pip_bootstrap_plan()
    required_version = binding["required_pip_version"]
    binding["host_pip_identity"] = bind_pip_identity(
        journal,
        "bind_host_pip_identity_before_bootstrap",
        sys.executable,
        staging_root,
        provisional_environment,
        primary_url,
        torch_url,
        attempt_state,
        durable_attempt,
        required_version,
    )
    attempt_state["host_pip_identity"] = binding["host_pip_identity"]
    run_tool(
        journal,
        "download_bootstrap_pip_wheel",
        [
            sys.executable,
            "-I",
            "-B",
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "download",
            "--no-input",
            "--no-deps",
            "--only-binary=:all:",
            "--index-url",
            primary_url,
            "--dest",
            str(tool_wheelhouse),
            "pip==" + required_version,
        ],
        staging_root,
        provisional_environment,
        primary_url,
        torch_url,
        attempt_state,
        ("network_contact_begun", "package_resolution_begun"),
        durable_attempt,
    )
    bootstrap_records = inspect_wheel_directory(tool_wheelhouse)
    if {
        record["normalized_name"]: record["version"]
        for record in bootstrap_records
    } != {"pip": required_version}:
        raise CandidateConstructionError(
            "BOOTSTRAP_PIP_WHEEL_IDENTITY_MISMATCH"
        )
    bootstrap_record = bootstrap_records[0]
    binding["bootstrap_wheel"] = bootstrap_record
    attempt_state["bootstrap_pip_wheel_binding"] = bootstrap_record
    bootstrap_lock_path = tool_wheelhouse.parent / "bootstrap-pip.lock"
    write_exclusive(
        bootstrap_lock_path,
        lock_candidate_bytes([bootstrap_record]),
    )
    binding["bootstrap_lock"] = {
        "filename": bootstrap_lock_path.name,
        "sha256": sha256_file(bootstrap_lock_path)[0],
    }
    attempt_state["bootstrap_pip_lock_binding"] = binding["bootstrap_lock"]
    rebound_host_identity = bind_pip_identity(
        journal,
        "rebind_host_pip_identity_before_target_install",
        sys.executable,
        staging_root,
        provisional_environment,
        primary_url,
        torch_url,
        attempt_state,
        durable_attempt,
        required_version,
    )
    if rebound_host_identity != binding["host_pip_identity"]:
        raise CandidateConstructionError(
            "HOST_PIP_IDENTITY_CHANGED_DURING_BOOTSTRAP"
        )
    binding["host_pip_identity_reverified_before_target_install"] = True
    attempt_state[
        "host_pip_identity_reverified_before_target_install"
    ] = True
    run_tool(
        journal,
        "bootstrap_pip_into_isolated_venv",
        [
            sys.executable,
            "-I",
            "-B",
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "--python",
            venv_python,
            "install",
            "--no-input",
            "--no-index",
            "--no-deps",
            "--only-binary=:all:",
            "--no-compile",
            "--require-hashes",
            "--find-links",
            str(tool_wheelhouse),
            "--requirement",
            str(bootstrap_lock_path),
        ],
        staging_root,
        provisional_environment,
        primary_url,
        torch_url,
        attempt_state,
        ("bootstrap_pip_install_begun", "build_tool_install_begun"),
        durable_attempt,
    )
    binding["isolated_venv_pip_identity"] = bind_pip_identity(
        journal,
        "bind_isolated_venv_pip_identity_after_bootstrap",
        venv_python,
        staging_root,
        isolated_venv_environment,
        primary_url,
        torch_url,
        attempt_state,
        durable_attempt,
        required_version,
        expected_root=build_venv,
    )
    attempt_state["isolated_venv_pip_identity"] = binding[
        "isolated_venv_pip_identity"
    ]
    return binding


def lock_candidate_bytes(wheel_records):
    lines = [
        "# REVIEW-PENDING F152 CANDIDATE; not an authority or runtime install instruction.",
        "# Install only after independent acceptance with --no-index --only-binary=:all: --require-hashes.",
    ]
    for record in sorted(wheel_records, key=lambda item: item["normalized_name"]):
        lines.append(
            f'{record["normalized_name"]}=={record["version"]} \\'
        )
        lines.append(f'    --hash=sha256:{record["sha256"]}')
    return ("\n".join(lines) + "\n").encode("ascii")


def write_exclusive(path, payload, mode=0o640):
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        mode,
    )
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise CandidateConstructionError("EXCLUSIVE_WRITE_DID_NOT_PROGRESS")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def sha256_descriptor(descriptor):
    os.lseek(descriptor, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
        size += len(chunk)
    return digest.hexdigest(), size


def fsync_directory(descriptor, error_code):
    observed = os.fstat(descriptor)
    if not stat.S_ISDIR(observed.st_mode):
        raise CandidateConstructionError(error_code, "NOT_DIRECTORY")
    try:
        os.fsync(descriptor)
    except OSError as error:
        raise CandidateConstructionError(
            error_code,
            type(error).__name__,
        ) from error


def write_exclusive_at(directory_descriptor, name, payload, mode=0o640):
    if (
        type(name) is not str
        or not name
        or "/" in name
        or "\\" in name
        or name in (".", "..")
    ):
        raise CandidateConstructionError("DURABLE_LEAF_NAME_INVALID")
    if (
        type(mode) is not int
        or mode < 0o400
        or mode > 0o755
        or mode & 0o022
    ):
        raise CandidateConstructionError("DURABLE_LEAF_MODE_INVALID")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = None
    created_stat = None
    leaf_created = False
    try:
        descriptor = os.open(name, flags, mode, dir_fd=directory_descriptor)
        leaf_created = True
        created_stat = os.fstat(descriptor)
        os.fchmod(descriptor, mode)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise CandidateConstructionError(
                    "DURABLE_EXCLUSIVE_WRITE_DID_NOT_PROGRESS"
                )
            view = view[written:]
        os.fsync(descriptor)
        closing_descriptor = descriptor
        descriptor = None
        os.close(closing_descriptor)
        fsync_directory(
            directory_descriptor,
            "DURABLE_PARENT_DIRECTORY_FSYNC_FAILED",
        )
        read_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        reopened = os.open(name, read_flags, dir_fd=directory_descriptor)
        try:
            observed_stat = os.fstat(reopened)
            if (
                observed_stat.st_dev,
                observed_stat.st_ino,
            ) != (
                created_stat.st_dev,
                created_stat.st_ino,
            ):
                raise CandidateConstructionError(
                    "DURABLE_EXCLUSIVE_WRITE_REOPEN_BINDING_MISMATCH"
                )
            observed_sha256, observed_size = sha256_descriptor(reopened)
        finally:
            os.close(reopened)
        if (
            observed_sha256 != sha256_bytes(payload)
            or observed_size != len(payload)
            or observed_stat.st_mode & 0o777 != mode
        ):
            raise CandidateConstructionError(
                "DURABLE_EXCLUSIVE_WRITE_REOPEN_MISMATCH"
            )
        return {
            "sha256": observed_sha256,
            "size_bytes": observed_size,
            "device": created_stat.st_dev,
            "inode": created_stat.st_ino,
            "mode_octal": format(observed_stat.st_mode & 0o777, "04o"),
        }
    except BaseException as raw_error:
        if leaf_created and created_stat is None and descriptor is not None:
            try:
                created_stat = os.fstat(descriptor)
            except BaseException as binding_error:
                # The leaf may now exist, but its binding could not be learned.
                # Do not rename or unlink through a mutable name: either action
                # could overwrite or remove an object supplied concurrently.
                closing_descriptor = descriptor
                descriptor = None
                close_error_name = None
                try:
                    os.close(closing_descriptor)
                except BaseException as close_error:
                    # Never retry close after an error: the descriptor state is
                    # unspecified and its integer may already have been reused.
                    close_error_name = type(close_error).__name__
                detail = (
                    type(raw_error).__name__
                    + ":"
                    + type(binding_error).__name__
                )
                if close_error_name is not None:
                    detail += ":close:" + close_error_name
                raise CandidateConstructionError(
                    "DURABLE_EXCLUSIVE_WRITE_FAILED_AFTER_UNBOUND_CREATE",
                    detail,
                    telemetry={
                        "durable_leaf_created": True,
                        "durable_leaf_name": name,
                        "durable_leaf_binding_unknown": True,
                        "durable_leaf_expected_sha256": sha256_bytes(payload),
                        "durable_leaf_expected_size_bytes": len(payload),
                        "durable_leaf_expected_mode_octal": format(mode, "04o"),
                    },
                ) from raw_error
        cleanup_close_error_name = None
        if descriptor is not None:
            closing_descriptor = descriptor
            descriptor = None
            try:
                os.close(closing_descriptor)
            except BaseException as close_error:
                # Do not retry an interrupted/failed close.
                cleanup_close_error_name = type(close_error).__name__
        if created_stat is None:
            if cleanup_close_error_name is not None:
                raise CandidateConstructionError(
                    "DURABLE_EXCLUSIVE_WRITE_CLEANUP_CLOSE_FAILED",
                    cleanup_close_error_name,
                ) from raw_error
            raise
        detail = (
            raw_error.code
            if isinstance(raw_error, CandidateConstructionError)
            else type(raw_error).__name__
        )
        if cleanup_close_error_name is not None:
            detail += ":close:" + cleanup_close_error_name
        raise CandidateConstructionError(
            "DURABLE_EXCLUSIVE_WRITE_FAILED_AFTER_CREATE",
            f"{name}:{detail}",
            telemetry={
                "durable_leaf_created": True,
                "durable_leaf_name": name,
                "durable_leaf_device": created_stat.st_dev,
                "durable_leaf_inode": created_stat.st_ino,
                "durable_leaf_expected_sha256": sha256_bytes(payload),
                "durable_leaf_expected_size_bytes": len(payload),
                "durable_leaf_expected_mode_octal": format(mode, "04o"),
            },
        ) from raw_error


def open_bound_directory(path, expected_device=None, expected_inode=None):
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        observed = os.fstat(descriptor)
        if not stat.S_ISDIR(observed.st_mode):
            raise CandidateConstructionError(
                "DURABLE_BOUND_OBJECT_NOT_DIRECTORY"
            )
        if (
            expected_device is not None
            and (observed.st_dev, observed.st_ino)
            != (expected_device, expected_inode)
        ):
            raise CandidateConstructionError(
                "DURABLE_DIRECTORY_BINDING_CHANGED"
            )
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor, observed


def duplicate_bound_directory(durable_attempt, error_code):
    descriptor = os.dup(durable_attempt["descriptor"])
    try:
        observed = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(observed.st_mode)
            or (observed.st_dev, observed.st_ino)
            != (durable_attempt["device"], durable_attempt["inode"])
        ):
            raise CandidateConstructionError(error_code)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor, observed


def verify_retained_durable_intent(
    durable_attempt,
    expected_intent_sha256,
    expected_intent_size,
):
    descriptor = durable_attempt.get("descriptor")
    if type(descriptor) is not int:
        raise CandidateConstructionError(
            "DURABLE_ATTEMPT_DESCRIPTOR_MISSING"
        )
    try:
        observed = os.fstat(descriptor)
    except OSError as error:
        raise CandidateConstructionError(
            "DURABLE_ATTEMPT_DESCRIPTOR_UNAVAILABLE",
            type(error).__name__,
        ) from error
    if (
        not stat.S_ISDIR(observed.st_mode)
        or (observed.st_dev, observed.st_ino)
        != (durable_attempt["device"], durable_attempt["inode"])
    ):
        raise CandidateConstructionError(
            "DURABLE_ATTEMPT_DESCRIPTOR_BINDING_CHANGED"
        )

    # The authorization record is re-opened relative to the retained inode,
    # never through a mutable pathname.
    intent_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        intent_descriptor = os.open(
            "attempt-intent.json",
            intent_flags,
            dir_fd=descriptor,
        )
    except OSError as error:
        raise CandidateConstructionError(
            "DURABLE_INTENT_REOPEN_FAILED",
            type(error).__name__,
        ) from error
    try:
        intent_stat = os.fstat(intent_descriptor)
        if not stat.S_ISREG(intent_stat.st_mode):
            raise CandidateConstructionError(
                "DURABLE_INTENT_NOT_REGULAR_FILE"
            )
        observed_sha256, observed_size = sha256_descriptor(intent_descriptor)
    finally:
        os.close(intent_descriptor)
    if (
        observed_sha256 != expected_intent_sha256
        or observed_size != expected_intent_size
        or durable_attempt["intent"]["sha256"] != expected_intent_sha256
        or durable_attempt["intent"]["size_bytes"] != expected_intent_size
    ):
        raise CandidateConstructionError(
            "DURABLE_INTENT_CUSTODY_MISMATCH"
        )

    return {
        "device": observed.st_dev,
        "inode": observed.st_ino,
        "intent_sha256": observed_sha256,
        "intent_size_bytes": observed_size,
    }


def verify_durable_intent_custody(
    durable_attempt,
    expected_intent_sha256,
    expected_intent_size,
):
    retained = verify_retained_durable_intent(
        durable_attempt,
        expected_intent_sha256,
        expected_intent_size,
    )
    # The retained descriptor preserves custody if a pathname race occurs.
    # Also require the declared destination to resolve to that same inode at
    # every normal boundary so a completed candidate cannot silently move.
    try:
        declared_descriptor, _ = open_bound_directory(
            durable_attempt["absolute_path"],
            durable_attempt["device"],
            durable_attempt["inode"],
        )
    except (CandidateConstructionError, OSError) as error:
        raise CandidateConstructionError(
            "DURABLE_DECLARED_PATH_BINDING_CHANGED",
            type(error).__name__,
        ) from error
    else:
        os.close(declared_descriptor)
    return retained


def start_durable_attempt(destination, ancestor_binding, intent_bytes):
    require_ancestor_binding_unchanged(destination, ancestor_binding)
    parent = destination.parent
    parent_binding = ancestor_binding[-1]
    parent_descriptor, before = open_bound_directory(
        parent,
        parent_binding["device"],
        parent_binding["inode"],
    )
    root_created = False
    destination_stat = None
    destination_descriptor = None
    intent_binding = None
    intent_write_begun = False

    def creation_telemetry(include_operational_binding=False):
        telemetry = {
            "durable_attempt_root_created": root_created,
            "durable_attempt_root_may_exist": root_created,
            "durable_intent_committed": type(intent_binding) is dict,
            "durable_intent_may_exist": intent_write_begun,
            "durable_intent_expected_sha256": sha256_bytes(intent_bytes),
            "durable_intent_expected_size_bytes": len(intent_bytes),
        }
        if destination_stat is not None:
            telemetry["durable_attempt_root_binding"] = {
                "device": destination_stat.st_dev,
                "inode": destination_stat.st_ino,
            }
        if (
            include_operational_binding
            and type(destination_descriptor) is int
            and destination_stat is not None
            and type(intent_binding) is dict
        ):
            # Private handoff for terminal receipt creation. The caller removes
            # this descriptor-bearing entry before serializing public telemetry.
            telemetry["_durable_attempt_operational_binding"] = {
                "absolute_path": destination.as_posix(),
                "device": destination_stat.st_dev,
                "inode": destination_stat.st_ino,
                "intent": intent_binding,
                "descriptor": destination_descriptor,
            }
        return telemetry

    try:
        try:
            os.mkdir(destination.name, mode=0o750, dir_fd=parent_descriptor)
        except FileExistsError as error:
            raise CandidateConstructionError(
                "DURABLE_ATTEMPT_ALREADY_SPENT_OR_COLLIDED"
            ) from error
        root_created = True
        fsync_directory(
            parent_descriptor,
            "DURABLE_ATTEMPT_PARENT_FSYNC_FAILED",
        )
        after = os.fstat(parent_descriptor)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise CandidateConstructionError(
                "DURABLE_PARENT_CHANGED_DURING_ATTEMPT_CREATION"
            )
        child_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        child_flags |= getattr(os, "O_NOFOLLOW", 0)
        destination_descriptor = os.open(
            destination.name,
            child_flags,
            dir_fd=parent_descriptor,
        )
        try:
            destination_stat = os.fstat(destination_descriptor)
            if not stat.S_ISDIR(destination_stat.st_mode):
                raise CandidateConstructionError(
                    "DURABLE_ATTEMPT_ROOT_NOT_DIRECTORY"
                )
            intent_write_begun = True
            intent_binding = write_exclusive_at(
                destination_descriptor,
                "attempt-intent.json",
                intent_bytes,
            )
        except BaseException:
            closing_descriptor = destination_descriptor
            destination_descriptor = None
            os.close(closing_descriptor)
            raise
    except BaseException as raw_error:
        if not root_created:
            raise
        telemetry = creation_telemetry()
        if isinstance(raw_error, CandidateConstructionError):
            detail = raw_error.code
        else:
            detail = type(raw_error).__name__
        raise CandidateConstructionError(
            "DURABLE_INTENT_COMMIT_FAILED_AFTER_ROOT_CREATION",
            detail,
            telemetry=telemetry,
        ) from raw_error
    finally:
        closing_parent_descriptor = parent_descriptor
        parent_descriptor = None
        try:
            os.close(closing_parent_descriptor)
        except BaseException as close_error:
            if root_created:
                raise CandidateConstructionError(
                    "DURABLE_ATTEMPT_PARENT_CLOSE_FAILED_AFTER_ROOT_CREATION",
                    type(close_error).__name__,
                    telemetry=creation_telemetry(
                        include_operational_binding=True,
                    ),
                ) from close_error
            raise CandidateConstructionError(
                "DURABLE_ATTEMPT_PARENT_CLOSE_FAILED_BEFORE_ROOT_CREATION",
                type(close_error).__name__,
                telemetry=creation_telemetry(),
            ) from close_error
    return {
        "absolute_path": destination.as_posix(),
        "device": destination_stat.st_dev,
        "inode": destination_stat.st_ino,
        "intent": intent_binding,
        "descriptor": destination_descriptor,
    }


def verify_installed_overlay(overlay_root, lock_records):
    overlay_root = Path(os.path.abspath(str(overlay_root)))
    actual_files = []
    for directory, subdirectories, filenames in os.walk(
        overlay_root, topdown=True, followlinks=False
    ):
        directory_path = Path(directory)
        for name in list(subdirectories):
            child = directory_path / name
            if object_kind(child) != "DIRECTORY":
                raise CandidateConstructionError("OVERLAY_HAS_NONREGULAR_DIRECTORY")
        for name in filenames:
            path = directory_path / name
            if object_kind(path) != "REGULAR_FILE":
                raise CandidateConstructionError("OVERLAY_HAS_NONREGULAR_FILE")
            actual_files.append(path.relative_to(overlay_root).as_posix())

    dist_infos = sorted(overlay_root.rglob("*.dist-info"))
    installed = {}
    declared_paths = set()
    ownership = {}
    payload_rows = []
    for dist_info in dist_infos:
        if object_kind(dist_info) != "DIRECTORY":
            raise CandidateConstructionError("OVERLAY_DIST_INFO_NOT_DIRECTORY")
        metadata_path = dist_info / "METADATA"
        record_path = dist_info / "RECORD"
        if (
            object_kind(metadata_path) != "REGULAR_FILE"
            or object_kind(record_path) != "REGULAR_FILE"
        ):
            raise CandidateConstructionError("OVERLAY_DIST_INFO_INCOMPLETE")
        message = email.parser.BytesParser().parsebytes(metadata_path.read_bytes())
        name = normalized_name(message.get("Name", ""))
        version = message.get("Version")
        if not name or not version or name in installed:
            raise CandidateConstructionError("OVERLAY_DISTRIBUTION_IDENTITY_INVALID")
        installed[name] = version
        record_base = Path(os.path.abspath(str(dist_info.parent)))
        absolute_record_path = Path(os.path.abspath(str(record_path)))
        with record_path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.reader(handle):
                if len(row) != 3:
                    raise CandidateConstructionError("OVERLAY_RECORD_ROW_INVALID")
                relative_text, hash_field, size_field = row
                pure = PurePosixPath(relative_text)
                if (
                    not relative_text
                    or pure.is_absolute()
                    or "\\" in relative_text
                    or any(ord(character) < 32 for character in relative_text)
                ):
                    raise CandidateConstructionError("OVERLAY_RECORD_PATH_UNSAFE")
                payload_path = Path(
                    os.path.abspath(
                        os.path.join(record_base, *pure.parts)
                    )
                )
                try:
                    relative = payload_path.relative_to(overlay_root).as_posix()
                except ValueError as error:
                    raise CandidateConstructionError(
                        "OVERLAY_RECORD_PATH_ESCAPES_OVERLAY"
                    ) from error
                if object_kind(payload_path) != "REGULAR_FILE":
                    raise CandidateConstructionError(
                        "OVERLAY_RECORD_REFERENCES_MISSING_FILE"
                    )
                if relative in ownership:
                    raise CandidateConstructionError(
                        "OVERLAY_DUPLICATE_INSTALLED_FILE_OWNERSHIP",
                        relative,
                    )
                ownership[relative] = name
                declared_paths.add(relative)
                digest, size = sha256_file(payload_path)
                if hash_field:
                    algorithm, separator, encoded = hash_field.partition("=")
                    if separator != "=" or algorithm != "sha256":
                        raise CandidateConstructionError(
                            "OVERLAY_RECORD_NON_SHA256_HASH"
                        )
                    padding = "=" * ((4 - len(encoded) % 4) % 4)
                    declared = base64.urlsafe_b64decode(encoded + padding).hex()
                    if declared != digest:
                        raise CandidateConstructionError(
                            "OVERLAY_RECORD_HASH_MISMATCH"
                        )
                elif payload_path != absolute_record_path:
                    raise CandidateConstructionError(
                        "OVERLAY_RECORD_UNHASHED_NON_RECORD_FILE"
                    )
                if size_field and int(size_field) != size:
                    raise CandidateConstructionError(
                        "OVERLAY_RECORD_SIZE_MISMATCH"
                    )
                payload_rows.append(
                    {
                        "relative_path": relative,
                        "sha256": digest,
                        "size_bytes": size,
                        "mode_octal": format(
                            payload_path.stat().st_mode & 0o777,
                            "04o",
                        ),
                    }
                )

    expected = {
        record["normalized_name"]: record["version"] for record in lock_records
    }
    if installed != expected:
        raise CandidateConstructionError("OVERLAY_INSTALLED_LOCK_IDENTITY_MISMATCH")
    if set(actual_files) != declared_paths:
        raise CandidateConstructionError("OVERLAY_INSTALLED_PAYLOAD_CLOSURE_INCOMPLETE")
    payload_rows.sort(key=lambda item: item["relative_path"])
    ownership_rows = [
        {"relative_path": relative, "distribution": ownership[relative]}
        for relative in sorted(ownership)
    ]
    return {
        "installed_distributions": installed,
        "regular_file_count": len(actual_files),
        "payload_manifest_sha256": sha256_bytes(
            canonical_json_bytes(payload_rows)
        ),
        "ownership_entry_count": len(ownership_rows),
        "ownership_manifest_sha256": sha256_bytes(
            canonical_json_bytes(ownership_rows)
        ),
        "duplicate_installed_file_ownership": False,
        "all_files_record_declared": True,
        "all_declared_hashes_verified": True,
    }


def is_selected_project_source_path(relative_path):
    return relative_path in ("README.md", "pyproject.toml") or (
        relative_path.startswith("src/heterodiff/")
        and relative_path.endswith(".py")
    )


def is_provenance_bound_path(relative_path):
    return (
        is_selected_project_source_path(relative_path)
        or relative_path == BUILDER_NOTEBOOK_RELATIVE_PATH.as_posix()
    )


def decode_git_nul_paths(payload, label):
    paths = []
    for raw_path in payload.split(b"\0"):
        if not raw_path:
            continue
        try:
            relative_path = raw_path.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CandidateConstructionError(
                label + "_PATH_NOT_UTF8"
            ) from error
        pure = PurePosixPath(relative_path)
        if (
            pure.is_absolute()
            or "\\" in relative_path
            or any(part in ("", ".", "..") for part in pure.parts)
            or any(ord(character) < 32 for character in relative_path)
        ):
            raise CandidateConstructionError(label + "_PATH_UNSAFE")
        if is_provenance_bound_path(relative_path):
            paths.append(relative_path)
    if len(paths) != len(set(paths)):
        raise CandidateConstructionError(label + "_DUPLICATE_PATH")
    return sorted(paths)


def parse_git_head_tree(payload):
    records = {}
    for raw_entry in payload.split(b"\0"):
        if not raw_entry:
            continue
        metadata, separator, raw_path = raw_entry.partition(b"\t")
        if separator != b"\t":
            raise CandidateConstructionError("GIT_HEAD_TREE_ENTRY_INVALID")
        fields = metadata.split(b" ")
        if len(fields) != 3:
            raise CandidateConstructionError("GIT_HEAD_TREE_METADATA_INVALID")
        try:
            mode = fields[0].decode("ascii")
            object_type = fields[1].decode("ascii")
            object_id = fields[2].decode("ascii")
            relative_path = raw_path.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CandidateConstructionError(
                "GIT_HEAD_TREE_ENTRY_ENCODING_INVALID"
            ) from error
        pure = PurePosixPath(relative_path)
        if (
            pure.is_absolute()
            or "\\" in relative_path
            or any(part in ("", ".", "..") for part in pure.parts)
            or any(ord(character) < 32 for character in relative_path)
        ):
            raise CandidateConstructionError("GIT_HEAD_TREE_PATH_UNSAFE")
        if not is_provenance_bound_path(relative_path):
            continue
        if (
            mode not in ("100644", "100755")
            or object_type != "blob"
            or re.fullmatch(r"[0-9a-f]{40}", object_id) is None
            or relative_path in records
        ):
            raise CandidateConstructionError(
                "GIT_HEAD_TREE_SOURCE_ENTRY_INVALID",
                relative_path,
            )
        records[relative_path] = {
            "relative_path": relative_path,
            "git_mode": mode,
            "git_blob_sha1": object_id,
        }
    return records


def verify_source_manifest_git_provenance(
    repo_root,
    source_manifest,
    builder_source_binding,
    index_paths_payload,
    head_tree_payload,
):
    manifest_records = source_manifest.get("files")
    if type(manifest_records) is not list or not manifest_records:
        raise CandidateConstructionError("SOURCE_MANIFEST_FILES_INVALID")
    manifest_by_path = {}
    for record in manifest_records:
        if type(record) is not dict:
            raise CandidateConstructionError("SOURCE_MANIFEST_RECORD_INVALID")
        relative_path = record.get("relative_path")
        if (
            type(relative_path) is not str
            or not is_selected_project_source_path(relative_path)
            or relative_path in manifest_by_path
        ):
            raise CandidateConstructionError("SOURCE_MANIFEST_PATH_SET_INVALID")
        manifest_by_path[relative_path] = record
    if (
        type(builder_source_binding) is not dict
        or builder_source_binding.get("relative_path")
        != BUILDER_NOTEBOOK_RELATIVE_PATH.as_posix()
        or builder_source_binding["relative_path"] in manifest_by_path
    ):
        raise CandidateConstructionError(
            "CONSTRUCTION_NOTEBOOK_BINDING_INVALID"
        )
    bound_by_path = {
        **manifest_by_path,
        builder_source_binding["relative_path"]: builder_source_binding,
    }
    manifest_paths = sorted(manifest_by_path)
    bound_paths = sorted(bound_by_path)
    index_paths = decode_git_nul_paths(
        index_paths_payload,
        "GIT_INDEX_SOURCE",
    )
    head_records = parse_git_head_tree(head_tree_payload)
    head_paths = sorted(head_records)
    if index_paths != bound_paths:
        raise CandidateConstructionError(
            "BOUND_SOURCE_DIFFERS_FROM_GIT_INDEX_PATH_SET"
        )
    if head_paths != bound_paths:
        raise CandidateConstructionError(
            "BOUND_SOURCE_DIFFERS_FROM_GIT_HEAD_PATH_SET"
        )

    verified = []
    for relative_path in bound_paths:
        record = bound_by_path[relative_path]
        path = repo_root / relative_path
        require_regular_source_file(path, repo_root)
        payload = path.read_bytes()
        current_sha256 = sha256_bytes(payload)
        current_size = len(payload)
        observed_mode = path.lstat().st_mode & 0o777
        canonical_mode = 0o755 if observed_mode & 0o111 else 0o644
        expected_git_mode = "100755" if canonical_mode == 0o755 else "100644"
        git_blob_sha1 = hashlib.sha1(
            b"blob "
            + str(current_size).encode("ascii")
            + b"\0"
            + payload
        ).hexdigest()
        head_record = head_records[relative_path]
        if (
            record.get("sha256") != current_sha256
            or record.get("size_bytes") != current_size
            or record.get("mode_octal") != format(canonical_mode, "04o")
            or head_record["git_mode"] != expected_git_mode
            or head_record["git_blob_sha1"] != git_blob_sha1
        ):
            raise CandidateConstructionError(
                "SOURCE_MANIFEST_CONTENT_OR_IDENTITY_MISMATCH",
                relative_path,
            )
        verified.append(
            {
                **head_record,
                "sha256": current_sha256,
                "size_bytes": current_size,
                "mode_octal": format(canonical_mode, "04o"),
            }
        )
    return {
        "all_manifest_paths_exactly_tracked_in_index_and_head": True,
        "all_worktree_bytes_match_head_blobs": True,
        "construction_notebook_exactly_tracked_in_index_and_head": True,
        "bound_path_count": len(bound_paths),
        "manifest_path_count": len(manifest_paths),
        "manifest_paths_sha256": sha256_bytes(
            canonical_json_bytes(manifest_paths)
        ),
        "git_index_paths_stdout_sha256": sha256_bytes(index_paths_payload),
        "git_head_tree_stdout_sha256": sha256_bytes(head_tree_payload),
        "verified_head_sources_sha256": sha256_bytes(
            canonical_json_bytes(verified)
        ),
    }


def git_identity(
    repo_root,
    journal,
    environment,
    primary_url,
    torch_url,
    attempt_state,
    durable_attempt,
    source_manifest=None,
    builder_source_binding=None,
):
    git_environment = dict(environment)
    git_environment.update(
        {
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ASKPASS": "/bin/false",
            "SSH_ASKPASS": "/bin/false",
        }
    )
    git = [
        "git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={os.devnull}",
        "-c",
        "submodule.recurse=false",
    ]
    local_config = run_tool(
        journal,
        "git_local_config_safety",
        [*git, "config", "--local", "--no-includes", "--null", "--list"],
        repo_root,
        git_environment,
        primary_url,
        torch_url,
        attempt_state,
        ("source_identity_verification_begun",),
        durable_attempt,
    )
    forbidden_config = []
    for raw_entry in local_config.split(b"\0"):
        if not raw_entry:
            continue
        raw_key = raw_entry.split(b"\n", 1)[0]
        try:
            key = raw_key.decode("utf-8").lower()
        except UnicodeDecodeError as error:
            raise CandidateConstructionError(
                "GIT_LOCAL_CONFIG_KEY_INVALID_UTF8"
            ) from error
        if (
            key in (
                "core.fsmonitor",
                "core.hookspath",
                "extensions.worktreeconfig",
            )
            or key.startswith("include.")
            or key.startswith("includeif.")
            or key.startswith("filter.")
            or (
                key.startswith("diff.")
                and key.rsplit(".", 1)[-1] in ("command", "textconv")
            )
            or (
                key.startswith("submodule.")
                and key.endswith(".update")
            )
        ):
            forbidden_config.append(key)
    if forbidden_config:
        raise CandidateConstructionError(
            "GIT_LOCAL_CONFIG_EXTERNAL_EXECUTION_SURFACE_PRESENT",
            ",".join(sorted(set(forbidden_config))),
        )
    revision = run_tool(
        journal,
        "git_revision",
        [*git, "rev-parse", "--verify", "HEAD"],
        repo_root,
        git_environment,
        primary_url,
        torch_url,
        attempt_state,
        (),
        durable_attempt,
    ).decode("ascii").strip()
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise CandidateConstructionError("SOURCE_REVISION_INVALID")
    if source_manifest is None:
        raise CandidateConstructionError(
            "SOURCE_MANIFEST_REQUIRED_FOR_GIT_IDENTITY"
        )
    if builder_source_binding is None:
        raise CandidateConstructionError(
            "CONSTRUCTION_NOTEBOOK_BINDING_REQUIRED_FOR_GIT_IDENTITY"
        )
    index_paths_payload = run_tool(
        journal,
        "git_index_source_paths",
        [
            *git,
            "ls-files",
            "--cached",
            "-z",
            "--",
            "pyproject.toml",
            "README.md",
            "src/heterodiff",
            BUILDER_NOTEBOOK_RELATIVE_PATH.as_posix(),
        ],
        repo_root,
        git_environment,
        primary_url,
        torch_url,
        attempt_state,
        (),
        durable_attempt,
    )
    head_tree_payload = run_tool(
        journal,
        "git_head_source_tree",
        [
            *git,
            "ls-tree",
            "-r",
            "-z",
            "--full-tree",
            revision,
            "--",
            "pyproject.toml",
            "README.md",
            "src/heterodiff",
            BUILDER_NOTEBOOK_RELATIVE_PATH.as_posix(),
        ],
        repo_root,
        git_environment,
        primary_url,
        torch_url,
        attempt_state,
        (),
        durable_attempt,
    )
    source_provenance = verify_source_manifest_git_provenance(
        repo_root,
        source_manifest,
        builder_source_binding,
        index_paths_payload,
        head_tree_payload,
    )
    status = run_tool(
        journal,
        "git_cleanliness",
        [
            *git,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignore-submodules=all",
        ],
        repo_root,
        git_environment,
        primary_url,
        torch_url,
        attempt_state,
        (),
        durable_attempt,
    )
    if status:
        raise CandidateConstructionError("SOURCE_WORKTREE_NOT_CLEAN")
    epoch_text = run_tool(
        journal,
        "git_commit_epoch",
        [*git, "show", "-s", "--format=%ct", "HEAD"],
        repo_root,
        git_environment,
        primary_url,
        torch_url,
        attempt_state,
        (),
        durable_attempt,
    ).decode("ascii").strip()
    if not epoch_text.isdigit():
        raise CandidateConstructionError("SOURCE_COMMIT_EPOCH_INVALID")
    return revision, int(epoch_text), source_provenance


def open_relative_directory(root_descriptor, parts):
    current = os.dup(root_descriptor)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        for part in parts:
            next_descriptor = os.open(part, flags, dir_fd=current)
            os.close(current)
            current = next_descriptor
        return current
    except BaseException:
        os.close(current)
        raise


def copy_tree_no_clobber(
    source_root,
    destination_root,
    destination_binding,
):
    directories = []
    files = []
    for directory, subdirectories, filenames in os.walk(
        source_root, topdown=True, followlinks=False
    ):
        directory_path = Path(directory)
        for name in subdirectories:
            path = directory_path / name
            if object_kind(path) != "DIRECTORY":
                raise CandidateConstructionError("STAGING_TREE_UNSAFE_DIRECTORY")
            directories.append(path.relative_to(source_root))
        for name in filenames:
            path = directory_path / name
            if object_kind(path) != "REGULAR_FILE":
                raise CandidateConstructionError("STAGING_TREE_UNSAFE_FILE")
            files.append(path.relative_to(source_root))
    ordered_files = sorted(files, key=lambda path: path.as_posix())
    del destination_root
    destination_descriptor, before = duplicate_bound_directory(
        destination_binding,
        "DURABLE_PUBLISH_DESCRIPTOR_BINDING_CHANGED",
    )
    published = []
    try:
        if sorted(os.listdir(destination_descriptor)) != ["attempt-intent.json"]:
            raise CandidateConstructionError(
                "DURABLE_ATTEMPT_ROOT_NOT_PRISTINE_FOR_PUBLISH"
            )
        for relative in sorted(
            directories,
            key=lambda path: (len(path.parts), path.as_posix()),
        ):
            parent_descriptor = open_relative_directory(
                destination_descriptor,
                relative.parts[:-1],
            )
            try:
                os.mkdir(relative.name, mode=0o750, dir_fd=parent_descriptor)
                fsync_directory(
                    parent_descriptor,
                    "DURABLE_PUBLISH_DIRECTORY_FSYNC_FAILED",
                )
            except FileExistsError as error:
                raise CandidateConstructionError(
                    "DURABLE_PUBLISH_DIRECTORY_COLLISION",
                    relative.as_posix(),
                ) from error
            finally:
                os.close(parent_descriptor)
        for relative in ordered_files:
            source = source_root / relative
            source_mode = source.lstat().st_mode & 0o777
            if (
                source_mode < 0o400
                or source_mode > 0o755
                or source_mode & 0o022
            ):
                raise CandidateConstructionError(
                    "STAGING_TREE_UNSAFE_FILE_MODE",
                    relative.as_posix(),
                )
            with source.open("rb") as handle:
                payload = handle.read()
            parent_descriptor = open_relative_directory(
                destination_descriptor,
                relative.parts[:-1],
            )
            try:
                binding = write_exclusive_at(
                    parent_descriptor,
                    relative.name,
                    payload,
                    mode=source_mode,
                )
            finally:
                os.close(parent_descriptor)
            published.append(
                {
                    "relative_path": relative.as_posix(),
                    **binding,
                }
            )
            if binding["mode_octal"] != format(source_mode, "04o"):
                raise CandidateConstructionError(
                    "DURABLE_PUBLISH_FILE_MODE_MISMATCH",
                    relative.as_posix(),
                )
        after = os.fstat(destination_descriptor)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise CandidateConstructionError(
                "DURABLE_ATTEMPT_ROOT_CHANGED_DURING_PUBLISH"
            )
    finally:
        os.close(destination_descriptor)
    return {
        "published_file_count": len(published),
        "published_files_manifest_sha256": sha256_bytes(
            canonical_json_bytes(published)
        ),
        "success_receipt_included": False,
    }


def initial_attempt_state():
    return {
        "durable_attempt_start_begun": False,
        "durable_attempt_root_created": False,
        "durable_attempt_root_may_exist": False,
        "durable_intent_committed": False,
        "durable_intent_may_exist": False,
        "durable_intent_expected_sha256": None,
        "durable_intent_expected_size_bytes": None,
        "durable_write_begun": False,
        "staging_write_begun": False,
        "source_identity_verification_begun": False,
        "network_contact_begun": False,
        "package_resolution_begun": False,
        "isolated_venv_creation_begun": False,
        "host_pip_identity": None,
        "host_pip_identity_reverified_before_target_install": False,
        "bootstrap_pip_wheel_binding": None,
        "bootstrap_pip_lock_binding": None,
        "isolated_venv_pip_identity": None,
        "bootstrap_pip_install_begun": False,
        "build_tool_install_begun": False,
        "project_wheel_build_begun": False,
        "overlay_install_begun": False,
        "durable_publish_begun": False,
        "success_receipt_publish_begun": False,
        "success_receipt_committed": False,
        "failure_receipt_commit_begun": False,
        "failure_receipt_committed": False,
        "failure_receipt_skipped_for_terminal_receipt_ambiguity": False,
        "terminal_receipt_ambiguity": False,
        "staging_cleanup_begun": False,
        "staging_cleanup_completed": False,
        "last_started_step": None,
        "last_completed_step": None,
        "last_failed_step": None,
        "command_journal": [],
    }


def suppress_failure_receipt_if_success_publication_uncertain(attempt_state):
    # Once the caller enters success-receipt publication, an asynchronous
    # exception can arrive after the helper's durable CALL returns but before
    # Python stores its binding. The caller must therefore treat the entire
    # post-call window as possibly committed and never publish a contradictory
    # failure receipt.
    if attempt_state.get("success_receipt_publish_begun") is True:
        attempt_state["terminal_receipt_ambiguity"] = True
        attempt_state["success_receipt_may_exist"] = True
    if attempt_state.get("terminal_receipt_ambiguity") is True:
        attempt_state[
            "failure_receipt_skipped_for_terminal_receipt_ambiguity"
        ] = True
        return True
    return False


def build_attempt_intent(
    profile_validation,
    review_binding,
    revision_verification_state,
    source_manifest,
    builder_binding,
    destination_root,
    destination_ancestors,
    primary_url,
    torch_url,
):
    record = {
        "schema_version": ATTEMPT_INTENT_SCHEMA,
        "record_sha256": "0" * 64,
        "state": "ATTEMPT_SPENT_BEFORE_NETWORK_OR_BUILD",
        "profile": {
            "relative_path": PROFILE_RELATIVE_PATH.as_posix(),
            "file_sha256": profile_validation["file_sha256"],
            "semantic_sha256": profile_validation["semantic_sha256"],
            "independent_review": review_binding,
        },
        "source": {
            "git_revision": None,
            "git_revision_verification_state": revision_verification_state,
            "source_manifest_sha256": source_manifest["record_sha256"],
            "construction_notebook": builder_binding,
        },
        "destination": {
            "absolute_path": destination_root.as_posix(),
            "ancestor_binding": destination_ancestors,
            "required_initial_state": "ABSENT",
        },
        "network": {
            "primary_index_url_sha256": sha256_bytes(primary_url.encode("utf-8")),
            "pytorch_cpu_index_url_sha256": sha256_bytes(torch_url.encode("utf-8")),
            "explicitly_authorized": True,
        },
        "construction": {
            "one_shot": True,
            "base_runtime_install_permitted": False,
            "wheels_only": True,
            "sdists_permitted": False,
            "complete_transitive_hash_lock_required": True,
            "study_or_test_data_permitted": False,
            "calibration_training_or_inference_permitted": False,
            "external_concurrent_attempt_root_mutation_permitted": False,
            "post_creation_root_authority": (
                "RETAINED_DIRECTORY_DEVICE_AND_INODE"
            ),
            "declared_path_rebinding_required_for_acceptance": True,
        },
    }
    projection = dict(record)
    projection.pop("record_sha256")
    record["record_sha256"] = sha256_bytes(
        ATTEMPT_INTENT_DOMAIN + canonical_json_bytes(projection)
    )
    return record, canonical_json_bytes(record) + b"\n"


def commit_failure_receipt(
    destination_root,
    destination_binding,
    attempt_intent_sha256,
    error,
    attempt_state,
):
    receipt = {
        "schema_version": FAILURE_RECEIPT_SCHEMA,
        "decision": "TERMINAL_NO_GO_PARTIAL_OR_FAILED_ATTEMPT_REVIEW_REQUIRED",
        "attempt_intent_sha256": attempt_intent_sha256,
        "error_code": error.code,
        "error_detail": error.detail,
        "attempt_state": attempt_state,
        "safety": {
            "base_runtime_install_executed": False,
            "study_or_test_data_accessed": False,
            "spark_accessed": False,
            "databricks_rest_api_accessed": False,
            "calibration_training_or_inference_executed": False,
            "canonical_repository_lock_written": False,
        },
    }
    payload = canonical_json_bytes(receipt) + b"\n"
    retained_descriptor = destination_binding.get("descriptor")
    if type(retained_descriptor) is int:
        verify_retained_durable_intent(
            destination_binding,
            attempt_intent_sha256,
            destination_binding["intent"]["size_bytes"],
        )
        descriptor, observed = duplicate_bound_directory(
            destination_binding,
            "DURABLE_FAILURE_RECEIPT_DESCRIPTOR_BINDING_CHANGED",
        )
    else:
        # This fallback is used only if root creation succeeded but the intent
        # commit itself failed, before any network/build authority existed.
        descriptor, observed = open_bound_directory(
            destination_root,
            destination_binding["device"],
            destination_binding["inode"],
        )
    binding = None
    failure_leaf_created = False
    failure_write_begun = False
    try:
        if (
            not stat.S_ISDIR(observed.st_mode)
            or (observed.st_dev, observed.st_ino)
            != (destination_binding["device"], destination_binding["inode"])
        ):
            raise CandidateConstructionError(
                "DURABLE_FAILURE_RECEIPT_DESCRIPTOR_BINDING_CHANGED"
            )
        try:
            failure_write_begun = True
            binding = write_exclusive_at(
                descriptor,
                "construction-failure-receipt.json",
                payload,
            )
            failure_leaf_created = True
        except BaseException as write_error:
            write_code = write_error.code if isinstance(
                write_error,
                CandidateConstructionError,
            ) else type(write_error).__name__
            raise CandidateConstructionError(
                "DURABLE_FAILURE_RECEIPT_COMMIT_AMBIGUOUS",
                write_code,
                telemetry={
                    "failure_receipt_may_exist": True,
                    "failure_receipt_leaf_name": (
                        "construction-failure-receipt.json"
                    ),
                    "failure_receipt_write_error": write_code,
                },
            ) from write_error
    except BaseException as commit_error:
        if binding is not None:
            detail = commit_error.code if isinstance(
                commit_error,
                CandidateConstructionError,
            ) else type(commit_error).__name__
            raise CandidateConstructionError(
                "DURABLE_FAILURE_RECEIPT_POST_CREATE_AMBIGUOUS",
                detail,
                telemetry={
                    "failure_receipt_may_exist": True,
                    "failure_receipt_leaf_name": (
                        "construction-failure-receipt.json"
                    ),
                    "failure_receipt_binding": binding,
                },
            ) from commit_error
        raise
    finally:
        closing_descriptor = descriptor
        descriptor = None
        try:
            os.close(closing_descriptor)
        except BaseException as close_error:
            if failure_leaf_created or failure_write_begun:
                raise CandidateConstructionError(
                    "DURABLE_FAILURE_RECEIPT_DESCRIPTOR_CLOSE_AMBIGUOUS",
                    type(close_error).__name__,
                    telemetry={
                        "failure_receipt_may_exist": True,
                        "failure_receipt_leaf_name": (
                            "construction-failure-receipt.json"
                        ),
                        "failure_receipt_binding": binding,
                    },
                ) from close_error
            raise
    return receipt, binding


def verify_bound_durable_leaf(
    directory_descriptor,
    name,
    expected_binding,
):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(name, flags, dir_fd=directory_descriptor)
    try:
        observed = os.fstat(descriptor)
        if not stat.S_ISREG(observed.st_mode):
            raise CandidateConstructionError(
                "DURABLE_BOUND_LEAF_NOT_REGULAR_FILE"
            )
        observed_sha256, observed_size = sha256_descriptor(descriptor)
    finally:
        os.close(descriptor)
    if (
        observed.st_dev != expected_binding["device"]
        or observed.st_ino != expected_binding["inode"]
        or observed_sha256 != expected_binding["sha256"]
        or observed_size != expected_binding["size_bytes"]
    ):
        raise CandidateConstructionError(
            "DURABLE_BOUND_LEAF_BINDING_MISMATCH",
            name,
        )
    return expected_binding


def commit_success_receipt(
    destination_binding,
    expected_intent_sha256,
    expected_intent_size,
    payload,
):
    # The retained directory inode is the post-creation custody authority.
    # A pathname can be renamed between any two userspace checks, so claiming
    # simultaneous pathname/root/leaf authority would be false. The receipt
    # binds the retained root and remains review-pending until an independent
    # reviewer rebinds the declared path to this inode.
    verify_retained_durable_intent(
        destination_binding,
        expected_intent_sha256,
        expected_intent_size,
    )
    descriptor, before = duplicate_bound_directory(
        destination_binding,
        "DURABLE_SUCCESS_RECEIPT_DESCRIPTOR_BINDING_CHANGED",
    )
    receipt_name = "construction-receipt.json"
    receipt_binding = None
    receipt_leaf_created = False
    receipt_write_begun = False
    try:
        try:
            receipt_write_begun = True
            receipt_binding = write_exclusive_at(
                descriptor,
                receipt_name,
                payload,
            )
            receipt_leaf_created = True
        except BaseException as write_error:
            write_code = write_error.code if isinstance(
                write_error,
                CandidateConstructionError,
            ) else type(write_error).__name__
            # Receipt creation is the point of no return. If any write, fsync,
            # binding, or reopen operation fails after O_EXCL created the leaf,
            # preserve every name and suppress a contradictory failure receipt.
            # Treat every exception after entering the O_EXCL operation as
            # ambiguous because an asynchronous exception can occur between the
            # kernel create and Python's local binding assignment.
            raise CandidateConstructionError(
                "DURABLE_SUCCESS_RECEIPT_COMMIT_AMBIGUOUS",
                write_code,
                telemetry={
                    "terminal_receipt_ambiguity": True,
                    "success_receipt_may_exist": True,
                    "success_receipt_leaf_name": receipt_name,
                    "success_receipt_write_error": write_code,
                },
            ) from write_error
        after = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(after.st_mode)
            or (before.st_dev, before.st_ino)
            != (after.st_dev, after.st_ino)
        ):
            raise CandidateConstructionError(
                "DURABLE_ATTEMPT_ROOT_CHANGED_DURING_SUCCESS_COMMIT"
            )
        verify_bound_durable_leaf(
            descriptor,
            receipt_name,
            receipt_binding,
        )
    except BaseException as commit_error:
        if receipt_binding is not None:
            detail = commit_error.code if isinstance(
                commit_error,
                CandidateConstructionError,
            ) else type(commit_error).__name__
            raise CandidateConstructionError(
                "DURABLE_SUCCESS_RECEIPT_POST_CREATE_AMBIGUOUS",
                detail,
                telemetry={
                    "terminal_receipt_ambiguity": True,
                    "success_receipt_may_exist": True,
                    "success_receipt_leaf_name": receipt_name,
                    "success_receipt_binding": receipt_binding,
                },
            ) from commit_error
        raise
    finally:
        closing_descriptor = descriptor
        descriptor = None
        try:
            os.close(closing_descriptor)
        except BaseException as close_error:
            if receipt_leaf_created or receipt_write_begun:
                raise CandidateConstructionError(
                    "DURABLE_SUCCESS_RECEIPT_DESCRIPTOR_CLOSE_AMBIGUOUS",
                    type(close_error).__name__,
                    telemetry={
                        "terminal_receipt_ambiguity": True,
                        "success_receipt_may_exist": True,
                        "success_receipt_leaf_name": receipt_name,
                        "success_receipt_binding": receipt_binding,
                    },
                ) from close_error
            raise
    return receipt_binding


# COMMAND ----------

# DBTITLE 1,Cell 8
def construct_candidate(preflight_result):
    journal = []
    attempt_state = initial_attempt_state()
    attempt_state["last_started_step"] = "construct_pre_intent_bindings"
    try:
        repo_root = preflight_result["repo_root"]
        profile_validation = preflight_result["profile_validation"]
        destination_root = Path(DURABLE_OUTPUT_DIRECTORY)
        primary_url = preflight_result["primary_index"]["url"]
        torch_url = preflight_result["torch_index"]["url"]
        provisional_environment = {
            "PATH": "/usr/bin:/bin",
            "LANG": "C",
            "LC_ALL": "C",
            "TZ": "UTC",
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHONSAFEPATH": "1",
            "PYTHONUTF8": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
        source_manifest = project_source_manifest(repo_root)
        builder_source_binding = regular_file_binding(
            repo_root,
            BUILDER_NOTEBOOK_RELATIVE_PATH,
            "BUILDER_NOTEBOOK",
        )
        destination_ancestors = preflight_result["destination"][
            "ancestor_binding"
        ]
        attempt_intent, attempt_intent_bytes = build_attempt_intent(
            profile_validation,
            preflight_result["v2_independent_review_binding"],
            DEFERRED_GIT_REVISION_STATE,
            source_manifest,
            builder_source_binding,
            destination_root,
            destination_ancestors,
            primary_url,
            torch_url,
        )
        attempt_intent_sha256 = sha256_bytes(attempt_intent_bytes)
        attempt_state["durable_intent_expected_sha256"] = (
            attempt_intent_sha256
        )
        attempt_state["durable_intent_expected_size_bytes"] = len(
            attempt_intent_bytes
        )
    except BaseException as raw_pre_intent_error:
        detail = raw_pre_intent_error.code if isinstance(
            raw_pre_intent_error,
            CandidateConstructionError,
        ) else type(raw_pre_intent_error).__name__
        attempt_state["last_failed_step"] = "construct_pre_intent_bindings"
        raise CandidateConstructionError(
            "PRE_INTENT_CONSTRUCTION_FAILED",
            detail,
            telemetry=dict(attempt_state),
        ) from raw_pre_intent_error
    attempt_state["last_completed_step"] = "construct_pre_intent_bindings"
    attempt_state["durable_write_begun"] = True
    attempt_state["durable_attempt_start_begun"] = True
    try:
        destination_binding = start_durable_attempt(
            destination_root,
            destination_ancestors,
            attempt_intent_bytes,
        )
    except BaseException as raw_start_error:
        if isinstance(raw_start_error, CandidateConstructionError):
            error = raw_start_error
        else:
            error = CandidateConstructionError(
                "DURABLE_ATTEMPT_START_FAILED",
                type(raw_start_error).__name__,
                telemetry={
                    "durable_attempt_root_created": False,
                    "durable_attempt_root_may_exist": True,
                    "durable_intent_committed": False,
                    "durable_intent_may_exist": True,
                },
            )
        error_telemetry = dict(error.telemetry or {})
        operational_binding = error_telemetry.pop(
            "_durable_attempt_operational_binding",
            None,
        )
        attempt_state.update(error_telemetry)
        attempt_state["last_failed_step"] = "commit_durable_attempt_intent"
        root_binding = operational_binding or attempt_state.get(
            "durable_attempt_root_binding"
        )
        try:
            if (
                attempt_state.get("durable_attempt_root_created") is True
                and type(root_binding) is dict
            ):
                attempt_state["failure_receipt_commit_begun"] = True
                try:
                    _, failure_binding = commit_failure_receipt(
                        destination_root,
                        root_binding,
                        attempt_intent_sha256,
                        error,
                        dict(attempt_state),
                    )
                except BaseException as receipt_error:
                    attempt_state["failure_receipt_may_exist"] = True
                    if (
                        isinstance(receipt_error, CandidateConstructionError)
                        and receipt_error.telemetry is not None
                    ):
                        attempt_state.update(receipt_error.telemetry)
                    attempt_state["failure_receipt_error"] = type(
                        receipt_error
                    ).__name__
                    raise CandidateConstructionError(
                        "FAILURE_RECEIPT_COMMIT_FAILED_AFTER_INTENT_ERROR",
                        error.code,
                        telemetry=dict(attempt_state),
                    ) from receipt_error
                attempt_state["failure_receipt_committed"] = True
                attempt_state["failure_receipt_binding"] = failure_binding
        finally:
            if (
                type(operational_binding) is dict
                and type(operational_binding.get("descriptor")) is int
            ):
                closing_descriptor = operational_binding["descriptor"]
                operational_binding["descriptor"] = None
                try:
                    os.close(closing_descriptor)
                except BaseException as close_error:
                    attempt_state[
                        "durable_attempt_descriptor_close_error_after_intent_failure"
                    ] = type(close_error).__name__
        raise CandidateConstructionError(
            error.code,
            error.detail,
            telemetry=dict(attempt_state),
        ) from raw_start_error
    attempt_state["durable_attempt_root_created"] = True
    attempt_state["durable_intent_committed"] = True
    attempt_state["last_completed_step"] = "commit_durable_attempt_intent"
    staging_root = None
    try:
        if destination_binding["intent"]["sha256"] != attempt_intent_sha256:
            raise CandidateConstructionError(
                "DURABLE_INTENT_BINDING_MISMATCH",
                telemetry=dict(attempt_state),
            )
        verify_durable_intent_custody(
            destination_binding,
            attempt_intent_sha256,
            len(attempt_intent_bytes),
        )
        revision, source_date_epoch, source_provenance = git_identity(
            repo_root,
            journal,
            provisional_environment,
            primary_url,
            torch_url,
            attempt_state,
            destination_binding,
            source_manifest,
            builder_source_binding,
        )
        attempt_state["command_journal"] = list(journal)
        try:
            staging_root = Path(tempfile.mkdtemp(prefix="heterodiff-b08-n1-"))
            attempt_state["staging_write_begun"] = True
        except OSError as error:
            raise CandidateConstructionError(
                "STAGING_CREATION_FAILED",
                type(error).__name__,
                telemetry=dict(attempt_state),
            ) from error
        build_venv = staging_root / "build-venv"
        candidate_root = staging_root / "candidate"
        tool_wheelhouse = candidate_root / "build-tool-wheelhouse"
        runtime_wheelhouse = candidate_root / "wheelhouse"
        overlay_root = candidate_root / "overlay"
        copied_source = staging_root / "project-source"
        tool_wheelhouse.mkdir(mode=0o750)
        runtime_wheelhouse.mkdir(mode=0o750, parents=True)
        overlay_root.mkdir(mode=0o750)

        copy_source_tree(repo_root, source_manifest, copied_source)

        verify_durable_intent_custody(
            destination_binding,
            attempt_intent_sha256,
            len(attempt_intent_bytes),
        )
        attempt_state["isolated_venv_creation_begun"] = True
        attempt_state["last_started_step"] = "create_isolated_build_venv"
        venv.EnvBuilder(
            system_site_packages=False,
            with_pip=False,
            clear=False,
            symlinks=False,
            upgrade=False,
        ).create(build_venv)
        attempt_state["last_completed_step"] = "create_isolated_build_venv"
        venv_python = str(build_venv / "bin" / "python")
        environment = isolated_environment(
            build_venv,
            source_date_epoch,
            preflight_result["environment"]["expected"],
        )

        # Seed without depending on ensurepip: bind the selected host pip,
        # retain and inspect one exact pip wheel, and use pip's supported
        # --python target mode only against the private venv and hash-locked
        # local wheelhouse. The observed ensurepip state is recorded, not
        # asserted.
        bootstrap_pip_binding = bootstrap_pip_into_isolated_venv(
            journal,
            staging_root,
            build_venv,
            venv_python,
            tool_wheelhouse,
            provisional_environment,
            environment,
            primary_url,
            torch_url,
            attempt_state,
            destination_binding,
        )

        run_tool(
            journal,
            "download_exact_build_tool_wheels",
            [
                venv_python,
                "-m",
                "pip",
                "--isolated",
                "download",
                "--no-deps",
                "--only-binary=:all:",
                "--index-url",
                primary_url,
                "--dest",
                str(tool_wheelhouse),
                *(
                    requirement
                    for requirement in BUILD_TOOL_REQUIREMENTS
                    if not requirement.startswith("pip==")
                ),
            ],
            staging_root,
            environment,
            primary_url,
            torch_url,
            attempt_state,
            ("network_contact_begun", "package_resolution_begun"),
            destination_binding,
        )
        tool_records = inspect_wheel_directory(tool_wheelhouse)
        if {
            record["normalized_name"]: record["version"] for record in tool_records
        } != {"pip": "25.0.1", "setuptools": "74.0.0", "wheel": "0.45.1"}:
            raise CandidateConstructionError("BUILD_TOOL_WHEEL_IDENTITY_MISMATCH")
        tool_lock_path = candidate_root / "build-tools.lock"
        write_exclusive(tool_lock_path, lock_candidate_bytes(tool_records))
        run_tool(
            journal,
            "install_exact_build_tools_in_isolated_venv",
            [
                venv_python,
                "-m",
                "pip",
                "--isolated",
                "install",
                "--no-index",
                "--only-binary=:all:",
                "--require-hashes",
                "--find-links",
                str(tool_wheelhouse),
                "--requirement",
                str(tool_lock_path),
            ],
            staging_root,
            environment,
            primary_url,
            torch_url,
            attempt_state,
            ("build_tool_install_begun",),
            destination_binding,
        )
        tool_versions_raw = run_tool(
            journal,
            "verify_isolated_build_tool_versions",
            [
                venv_python,
                "-c",
                (
                    "import json;"
                    "from importlib import metadata;"
                    "print(json.dumps({name:metadata.version(name) "
                    "for name in ('pip','setuptools','wheel')},sort_keys=True))"
                ),
            ],
            staging_root,
            environment,
            primary_url,
            torch_url,
            attempt_state,
            (),
            destination_binding,
        )
        try:
            installed_build_tool_versions = json.loads(
                tool_versions_raw.decode("ascii")
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CandidateConstructionError(
                "INSTALLED_BUILD_TOOL_VERSION_OUTPUT_INVALID"
            ) from error
        if installed_build_tool_versions != {
            "pip": "25.0.1",
            "setuptools": "74.0.0",
            "wheel": "0.45.1",
        }:
            raise CandidateConstructionError(
                "INSTALLED_BUILD_TOOL_VERSION_MISMATCH"
            )

        run_tool(
            journal,
            "build_project_wheel_from_source_copy",
            [
                venv_python,
                "-m",
                "pip",
                "--isolated",
                "wheel",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                str(runtime_wheelhouse),
                str(copied_source),
            ],
            staging_root,
            environment,
            primary_url,
            torch_url,
            attempt_state,
            ("project_wheel_build_begun",),
            destination_binding,
        )
        run_tool(
            journal,
            "resolve_exact_runtime_roots_to_wheels",
            [
                venv_python,
                "-m",
                "pip",
                "--isolated",
                "download",
                "--only-binary=:all:",
                "--index-url",
                primary_url,
                "--extra-index-url",
                torch_url,
                "--dest",
                str(runtime_wheelhouse),
                *ROOT_RUNTIME_REQUIREMENTS,
            ],
            staging_root,
            environment,
            primary_url,
            torch_url,
            attempt_state,
            ("network_contact_begun", "package_resolution_begun"),
            destination_binding,
        )
        runtime_records = inspect_wheel_directory(runtime_wheelhouse)
        identities = {
            record["normalized_name"]: record["version"]
            for record in runtime_records
        }
        for name, version in EXPECTED_DISTRIBUTIONS.items():
            if identities.get(name) != version:
                raise CandidateConstructionError(
                    "EXPECTED_RUNTIME_DISTRIBUTION_MISSING_OR_MISMATCHED", name
                )

        lock_bytes = lock_candidate_bytes(runtime_records)
        lock_relative = Path(
            "b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock.candidate"
        )
        lock_path = candidate_root / lock_relative
        write_exclusive(lock_path, lock_bytes)
        lock_sha256 = sha256_bytes(lock_bytes)

        run_tool(
            journal,
            "install_hash_locked_wheelhouse_to_isolated_overlay",
            [
                venv_python,
                "-m",
                "pip",
                "--isolated",
                "install",
                "--no-index",
                "--only-binary=:all:",
                "--require-hashes",
                "--ignore-installed",
                "--no-compile",
                "--find-links",
                str(runtime_wheelhouse),
                "--prefix",
                str(overlay_root),
                "--requirement",
                str(lock_path),
            ],
            staging_root,
            environment,
            primary_url,
            torch_url,
            attempt_state,
            ("overlay_install_begun",),
            destination_binding,
        )
        overlay = verify_installed_overlay(overlay_root, runtime_records)

        project_record = next(
            record
            for record in runtime_records
            if record["normalized_name"] == "heterodiff"
        )
        manifest = {
            "schema_version": MANIFEST_SCHEMA,
            "record_sha256": "0" * 64,
            "state": "CANDIDATE_REVIEW_REQUIRED_NOT_RUNTIME_AUTHORITY",
            "attempt": {
                "intent_record": attempt_intent,
                "intent_file_sha256": attempt_intent_sha256,
                "durable_root_binding": {
                    "device": destination_binding["device"],
                    "inode": destination_binding["inode"],
                },
                "custody_model": {
                    "post_creation_authority": (
                        "RETAINED_DIRECTORY_DEVICE_AND_INODE"
                    ),
                    "declared_path_is_locator_after_creation": True,
                    "external_concurrent_root_mutation_permitted": False,
                    "independent_review_must_rebind_path_root_and_receipt": True,
                },
            },
            "profile": {
                "relative_path": PROFILE_RELATIVE_PATH.as_posix(),
                "file_sha256": profile_validation["file_sha256"],
                "semantic_sha256": profile_validation["semantic_sha256"],
                "independent_review": preflight_result[
                    "v2_independent_review_binding"
                ],
            },
            "source": {
                "git_revision": revision,
                "git_clean": True,
                "source_date_epoch": source_date_epoch,
                "manifest": source_manifest,
                "git_provenance": source_provenance,
                "construction_notebook": builder_source_binding,
            },
            "network_resolution": {
                "authorized": True,
                "primary_index_url": primary_url,
                "primary_index_url_sha256": sha256_bytes(
                    primary_url.encode("utf-8")
                ),
                "pytorch_cpu_index_url": torch_url,
                "pytorch_cpu_index_url_sha256": sha256_bytes(
                    torch_url.encode("utf-8")
                ),
                "wheels_only": True,
                "sdists_accepted": False,
            },
            "build_tools": {
                "isolated_venv": True,
                "system_site_packages": False,
                "bootstrap_pip_binding": bootstrap_pip_binding,
                "installed_versions": installed_build_tool_versions,
                "wheels": tool_records,
                "lock_filename": tool_lock_path.name,
                "lock_sha256": sha256_file(tool_lock_path)[0],
            },
            "project_wheel": project_record,
            "f152_lock_candidate": {
                "canonical_target_relative_path": (
                    CANONICAL_F152_LOCK_RELATIVE_PATH.as_posix()
                ),
                "candidate_filename": lock_relative.name,
                "sha256": lock_sha256,
                "entry_count": len(runtime_records),
                "all_requirements_exactly_pinned": True,
                "hash_for_every_requirement": True,
            },
            "wheelhouse": {
                "artifact_count": len(runtime_records),
                "wheels_only": True,
                "artifacts": runtime_records,
            },
            "overlay": overlay,
            "overlay_install": {
                "prefix_isolated": True,
                "ignore_installed": True,
                "no_index": True,
                "require_hashes": True,
                "only_binary": True,
            },
            "command_journal": journal,
            "attempt_state_before_publish": dict(attempt_state),
            "safety": {
                "base_runtime_modified": False,
                "bounded_widget_input_accessed": _WIDGET_INPUT_ACCESSED,
                "databricks_rest_api_accessed": False,
                "study_or_test_data_accessed": False,
                "spark_accessed": False,
                "calibration_training_or_inference_executed": False,
                "project_or_scientific_module_imported": False,
                "canonical_repository_lock_written": False,
                "tracker_or_timetable_edited": False,
            },
            "not_proven": [
                "DECLARED_PATH_TO_RETAINED_ROOT_BINDING_AT_REVIEW_TIME",
                "F152_INDEPENDENT_ACCEPTANCE",
                "F151_PRODUCTION_RUNTIME_MANIFEST",
                "F153_EFFECTIVE_WHOLE_RUNTIME_SATISFACTION",
                "DRIVER_WORKER_EQUIVALENCE",
                "SCIENTIFIC_EXECUTION_READINESS",
                "B08_OR_WAVE2_CLOSURE",
            ],
        }
        manifest_projection = dict(manifest)
        manifest_projection.pop("record_sha256")
        manifest["record_sha256"] = sha256_bytes(
            OVERLAY_MANIFEST_DOMAIN + canonical_json_bytes(manifest_projection)
        )
        manifest_bytes = canonical_json_bytes(manifest) + b"\n"
        manifest_relative = Path(
            "b08-databricks-aws-dbr17.3-x86_64-cpu-py312."
            "overlay-manifest.candidate.json"
        )
        manifest_path = candidate_root / manifest_relative
        write_exclusive(manifest_path, manifest_bytes)
        manifest_file_sha256 = sha256_bytes(manifest_bytes)

        receipt = {
            "schema_version": RECEIPT_SCHEMA,
            "decision": "CANDIDATE_CONSTRUCTED_REVIEW_REQUIRED_DO_NOT_INSTALL",
            "scope": "DATA_FREE_ISOLATED_NATIVE_OVERLAY_CANDIDATE_ONLY",
            "durable_output_directory": DURABLE_OUTPUT_DIRECTORY,
            "attempt_intent_sha256": attempt_intent_sha256,
            "durable_attempt_root_binding": {
                "device": destination_binding["device"],
                "inode": destination_binding["inode"],
            },
            "custody_model": {
                "post_creation_authority": (
                    "RETAINED_DIRECTORY_DEVICE_AND_INODE"
                ),
                "declared_path_is_locator_after_creation": True,
                "external_concurrent_root_mutation_permitted": False,
                "independent_review_must_rebind_path_root_and_receipt": True,
            },
            "profile_file_sha256": profile_validation["file_sha256"],
            "v2_independent_review_sha256": preflight_result[
                "v2_independent_review_binding"
            ]["sha256"],
            "source_revision": revision,
            "source_manifest_sha256": source_manifest["record_sha256"],
            "source_git_provenance": source_provenance,
            "construction_notebook": builder_source_binding,
            "lock_candidate": {
                "relative_path": lock_relative.as_posix(),
                "sha256": lock_sha256,
                "entry_count": len(runtime_records),
            },
            "manifest_candidate": {
                "relative_path": manifest_relative.as_posix(),
                "file_sha256": manifest_file_sha256,
                "semantic_sha256": manifest["record_sha256"],
            },
            "project_wheel": project_record,
            "overlay_payload_manifest_sha256": overlay[
                "payload_manifest_sha256"
            ],
            "overlay_ownership_manifest_sha256": overlay[
                "ownership_manifest_sha256"
            ],
            "attempt_state_before_publish": dict(attempt_state),
            "safety": {
                "network_resolution_executed_under_explicit_gate": True,
                "base_runtime_install_executed": False,
                "bounded_widget_input_accessed": _WIDGET_INPUT_ACCESSED,
                "databricks_rest_api_accessed": False,
                "all_runtime_artifacts_are_wheels": True,
                "sdist_accepted": False,
                "durable_destination_preexisted": False,
                "durable_publish_no_clobber": True,
                "study_or_test_data_accessed": False,
                "spark_accessed": False,
                "calibration_training_or_inference_executed": False,
            },
            "not_authorized": [
                "INSTALL_OVERLAY_IN_PRODUCTION_RUNTIME",
                "WRITE_CANONICAL_F152_LOCK",
                "F152_OR_F151_CLOSURE",
                "B08_OR_WAVE2_CLOSURE",
                "SCIENTIFIC_EXECUTION",
            ],
            "not_proven": [
                "DECLARED_PATH_TO_RETAINED_ROOT_BINDING_AT_REVIEW_TIME",
            ],
        }
        attempt_state["durable_publish_begun"] = True
        attempt_state["last_started_step"] = "publish_durable_artifacts"
        verify_durable_intent_custody(
            destination_binding,
            attempt_intent_sha256,
            len(attempt_intent_bytes),
        )
        publish_binding = copy_tree_no_clobber(
            candidate_root,
            destination_root,
            destination_binding,
        )
        attempt_state["last_completed_step"] = "publish_durable_artifacts"

        # A success receipt is meaningful only after every transient object has
        # been removed.  It is therefore committed as the final durable file,
        # after artifact publication and cleanup have both succeeded.
        attempt_state["staging_cleanup_begun"] = True
        attempt_state["last_started_step"] = "cleanup_staging_before_success"
        try:
            shutil.rmtree(staging_root)
        except OSError as cleanup_error:
            attempt_state["staging_cleanup_error"] = type(
                cleanup_error
            ).__name__
            raise CandidateConstructionError(
                "STAGING_CLEANUP_FAILED_BEFORE_SUCCESS_RECEIPT",
                type(cleanup_error).__name__,
                telemetry=dict(attempt_state),
            ) from cleanup_error
        staging_root = None
        attempt_state["staging_cleanup_completed"] = True
        attempt_state["last_completed_step"] = "cleanup_staging_before_success"

        receipt["durable_publish"] = publish_binding
        attempt_state["success_receipt_publish_begun"] = True
        attempt_state["last_started_step"] = "commit_success_receipt"
        receipt["attempt_state_before_success_receipt_commit"] = dict(
            attempt_state
        )
        receipt_bytes = canonical_json_bytes(receipt) + b"\n"
        durable_receipt_binding = commit_success_receipt(
            destination_binding,
            attempt_intent_sha256,
            len(attempt_intent_bytes),
            receipt_bytes,
        )
        attempt_state["success_receipt_committed"] = True
        attempt_state["last_completed_step"] = "commit_success_receipt"
        durable_receipt_sha256 = durable_receipt_binding["sha256"]
        durable_receipt_size = durable_receipt_binding["size_bytes"]
        result = {
            **receipt,
            "attempt_state": dict(attempt_state),
            "receipt_file_sha256": durable_receipt_sha256,
            "receipt_size_bytes": durable_receipt_size,
        }
        return result
    except BaseException as raw_error:
        if isinstance(raw_error, CandidateConstructionError):
            construction_error = raw_error
            if raw_error.telemetry is not None:
                attempt_state.update(raw_error.telemetry)
        else:
            construction_error = CandidateConstructionError(
                "UNEXPECTED_CONSTRUCTION_FAILURE",
                type(raw_error).__name__,
            )
        attempt_state["command_journal"] = list(journal)
        if attempt_state["last_failed_step"] is None:
            attempt_state["last_failed_step"] = (
                attempt_state["last_started_step"] or "construction_internal"
            )
        if staging_root is not None:
            attempt_state["staging_cleanup_begun"] = True
            try:
                shutil.rmtree(staging_root)
                attempt_state["staging_cleanup_completed"] = True
            except BaseException as cleanup_error:
                attempt_state["staging_cleanup_error"] = type(
                    cleanup_error
                ).__name__
            staging_root = None
        if suppress_failure_receipt_if_success_publication_uncertain(
            attempt_state
        ):
            raise CandidateConstructionError(
                construction_error.code,
                construction_error.detail,
                telemetry=dict(attempt_state),
            ) from raw_error
        attempt_state["failure_receipt_commit_begun"] = True
        try:
            _, failure_binding = commit_failure_receipt(
                destination_root,
                destination_binding,
                attempt_intent_sha256,
                construction_error,
                dict(attempt_state),
            )
        except BaseException as receipt_error:
            attempt_state["failure_receipt_may_exist"] = True
            if (
                isinstance(receipt_error, CandidateConstructionError)
                and receipt_error.telemetry is not None
            ):
                attempt_state.update(receipt_error.telemetry)
            attempt_state["failure_receipt_error"] = type(receipt_error).__name__
            raise CandidateConstructionError(
                "FAILURE_RECEIPT_COMMIT_FAILED",
                construction_error.code,
                telemetry=dict(attempt_state),
            ) from receipt_error
        attempt_state["failure_receipt_committed"] = True
        attempt_state["failure_receipt_binding"] = failure_binding
        raise CandidateConstructionError(
            construction_error.code,
            construction_error.detail,
            telemetry=dict(attempt_state),
        ) from raw_error
    finally:
        closing_descriptor = destination_binding["descriptor"]
        destination_binding["descriptor"] = None
        try:
            os.close(closing_descriptor)
        except BaseException as close_error:
            if attempt_state.get("success_receipt_publish_begun") is True:
                suppress_failure_receipt_if_success_publication_uncertain(
                    attempt_state
                )
                attempt_state["retained_root_descriptor_close_error"] = type(
                    close_error
                ).__name__
                raise CandidateConstructionError(
                    "DURABLE_RETAINED_ROOT_CLOSE_AFTER_SUCCESS_AMBIGUOUS",
                    type(close_error).__name__,
                    telemetry=dict(attempt_state),
                ) from close_error
            attempt_state["retained_root_descriptor_close_error"] = type(
                close_error
            ).__name__
            if attempt_state.get("failure_receipt_commit_begun") is True:
                attempt_state["failure_receipt_may_exist"] = True
            raise CandidateConstructionError(
                "DURABLE_RETAINED_ROOT_DESCRIPTOR_CLOSE_FAILED",
                type(close_error).__name__,
                telemetry=dict(attempt_state),
            ) from close_error


def public_preflight_result(result):
    return {
        key: value
        for key, value in result.items()
        if key not in ("repo_root", "profile", "primary_index", "torch_index")
    } | {
        "index_configuration": {
            "primary": (
                None
                if result["primary_index"] is None
                else {
                    "host": result["primary_index"]["host"],
                    "sha256": result["primary_index"]["sha256"],
                }
            ),
            "pytorch_cpu": (
                None
                if result["torch_index"] is None
                else {
                    "host": result["torch_index"]["host"],
                    "sha256": result["torch_index"]["sha256"],
                }
            ),
        }
    }


try:
    preflight_result = preflight()
except (CandidateConstructionError, OSError) as error:
    result = {
        "schema_version": NOTEBOOK_SCHEMA,
        "decision": "HOLD_PREFLIGHT_FAILED",
        "error_code": (
            error.code
            if isinstance(error, CandidateConstructionError)
            else "PREFLIGHT_FILESYSTEM_ACCESS_FAILED"
        ),
        "error_detail": (
            error.detail
            if isinstance(error, CandidateConstructionError)
            else type(error).__name__
        ),
        "bounded_widget_input_accessed": _WIDGET_INPUT_ACCESSED,
        "safety": {
            "base_runtime_install_executed": False,
            "network_or_contact_accessed": False,
            "package_resolution_executed": False,
            "project_wheel_build_executed": False,
            "files_written": False,
            "spark_accessed": False,
            "databricks_rest_api_accessed": False,
            "study_or_test_data_accessed": False,
            "calibration_training_or_inference_executed": False,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
else:
    if not preflight_result["construction_authorized"]:
        print(
            json.dumps(
                public_preflight_result(preflight_result),
                indent=2,
                sort_keys=True,
            )
        )
    else:
        try:
            result = construct_candidate(preflight_result)
        except CandidateConstructionError as error:
            telemetry = error.telemetry or initial_attempt_state()
            try:
                durable_kind = object_kind(Path(DURABLE_OUTPUT_DIRECTORY))
            except OSError:
                durable_kind = "UNAVAILABLE"
            result = {
                "schema_version": RECEIPT_SCHEMA,
                "decision": (
                    "TERMINAL_NO_GO_SPENT_ATTEMPT_REVIEW_REQUIRED"
                    if (
                        telemetry.get("durable_attempt_root_created")
                        or telemetry.get("durable_intent_committed")
                        or telemetry.get("durable_attempt_root_may_exist")
                        or telemetry.get("durable_intent_may_exist")
                    )
                    else "NO_GO_CANDIDATE_CONSTRUCTION_FAILED_BEFORE_INTENT"
                ),
                "error_code": error.code,
                "error_detail": error.detail,
                "attempt_state": telemetry,
                "durable_output_directory": DURABLE_OUTPUT_DIRECTORY,
                "durable_output_object_kind_after_failure": durable_kind,
                "safety": {
                    "base_runtime_install_executed": False,
                    "bounded_widget_input_accessed": _WIDGET_INPUT_ACCESSED,
                    "databricks_rest_api_accessed": False,
                    "study_or_test_data_accessed": False,
                    "spark_accessed": False,
                    "calibration_training_or_inference_executed": False,
                    "canonical_repository_lock_written": False,
                },
            }
        print(json.dumps(result, indent=2, sort_keys=True))
